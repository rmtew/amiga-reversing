from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import cast
from uuid import uuid4

from amiga_reversing.disasm.target_metadata import (
    AbsoluteCodeLabelMetadata,
    SeededCodeEntrypointMetadata,
    SeededCodeLabelMetadata,
    SeededEntityMetadata,
    SuppressedSeededItemKind,
    SuppressedSeededItemMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
)

TARGET_UI_EDITS_FILE_NAME = "target_ui_edits.json"


class TargetUiEditKind(StrEnum):
    CODE_RANGE = "code_range"
    DATA_RANGE = "data_range"
    POINTER_TABLE = "pointer_table"
    TEXT_RANGE = "text_range"
    JUMP_TABLE = "jump_table"
    ENTRYPOINT = "entrypoint"
    LABEL = "label"
    EXTERNAL_SYMBOL = "external_symbol"
    SUPPRESS_INFERRED_CODE = "suppress_inferred_code"
    SUPPRESS_INFERRED_POINTER = "suppress_inferred_pointer"
    REPRODUCTION = "reproduction"
    REPRODUCTION_OPTIONS = "reproduction_options"


_MATERIALIZED_ENTITY_KINDS = {
    TargetUiEditKind.CODE_RANGE: ("code", None),
    TargetUiEditKind.DATA_RANGE: ("data", None),
    TargetUiEditKind.POINTER_TABLE: ("data", "pointer_table"),
    TargetUiEditKind.TEXT_RANGE: ("data", "string"),
    TargetUiEditKind.JUMP_TABLE: ("data", "jump_table"),
}

_SUPPRESS_INFERRED_KINDS = frozenset(
    {
        TargetUiEditKind.SUPPRESS_INFERRED_CODE,
        TargetUiEditKind.SUPPRESS_INFERRED_POINTER,
    }
)

REPRODUCTION_TARGET_UI_EDIT_KINDS = frozenset(
    {
        TargetUiEditKind.REPRODUCTION,
        TargetUiEditKind.REPRODUCTION_OPTIONS,
    }
)


def target_ui_edits_path(target_dir: Path) -> Path:
    return target_dir / TARGET_UI_EDITS_FILE_NAME


def load_target_ui_edits(target_dir: Path) -> list[dict[str, object]]:
    path = target_ui_edits_path(target_dir)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Bad {path.name}")
    edits: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"Bad {path.name}")
        edit = dict(cast(dict[str, object], item))
        edit["kind"] = target_ui_edit_kind_from_json(edit.get("kind"))
        edits.append(edit)
    return edits


def target_ui_edits_stamp_text(target_dir: Path) -> str:
    edits = load_target_ui_edits(target_dir)
    if not edits:
        return ""
    return json.dumps(edits, indent=2, sort_keys=True) + "\n"


def append_target_ui_edit(target_dir: Path, edit: dict[str, object]) -> dict[str, object]:
    payload = dict(edit)
    payload["kind"] = target_ui_edit_kind_from_json(payload.get("kind"))
    payload.setdefault("id", str(uuid4()))
    payload.setdefault("created_at", datetime.now(UTC).isoformat(timespec="seconds"))
    _validate_target_ui_edit(payload)
    edits = load_target_ui_edits(target_dir)
    edits.append(payload)
    target_ui_edits_path(target_dir).write_text(
        json.dumps(edits, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def apply_target_ui_edits(
    metadata: TargetMetadata | None,
    edits: list[dict[str, object]],
) -> TargetMetadata | None:
    current = metadata
    for edit in edits:
        current = _apply_target_ui_edit(current, edit)
    return current


def _validate_target_ui_edit(edit: dict[str, object]) -> None:
    kind = _require_parsed_target_ui_edit_kind(edit)
    if kind in _MATERIALIZED_ENTITY_KINDS:
        _require_int(edit, "addr")
        end = edit.get("end")
        if end is not None and (not isinstance(end, int) or end <= _require_int(edit, "addr")):
            raise ValueError("target edit end must be greater than addr")
        _optional_int(edit, "hunk")
        _optional_str(edit, "name")
        _optional_str(edit, "comment")
        _optional_str(edit, "subtype")
        return
    if kind is TargetUiEditKind.ENTRYPOINT:
        _require_int(edit, "addr")
        _optional_int(edit, "hunk")
        _optional_str(edit, "name")
        _optional_str(edit, "comment")
        return
    if kind is TargetUiEditKind.LABEL:
        _require_int(edit, "addr")
        _require_str(edit, "name")
        _optional_int(edit, "hunk")
        _optional_str(edit, "comment")
        return
    if kind is TargetUiEditKind.EXTERNAL_SYMBOL:
        _require_int(edit, "addr")
        _require_str(edit, "name")
        _optional_str(edit, "comment")
        return
    if kind in _SUPPRESS_INFERRED_KINDS:
        _require_int(edit, "addr")
        _optional_int(edit, "hunk")
        return
    if kind in REPRODUCTION_TARGET_UI_EDIT_KINDS:
        options = edit.get("options")
        reproduction = edit.get("reproduction")
        if not isinstance(options, dict) and not isinstance(reproduction, dict):
            raise ValueError("target reproduction edit requires options")
        _optional_str(edit, "profile_id")
        return
    raise ValueError(f"Unsupported target edit kind: {kind}")


def _apply_target_ui_edit(
    metadata: TargetMetadata | None,
    edit: dict[str, object],
) -> TargetMetadata | None:
    kind = _require_parsed_target_ui_edit_kind(edit)
    if kind in _MATERIALIZED_ENTITY_KINDS:
        current = _ensure_metadata(metadata)
        entity_type, default_subtype = _MATERIALIZED_ENTITY_KINDS[kind]
        raw_end = edit.get("end")
        end = raw_end if isinstance(raw_end, int) else None
        entity = SeededEntityMetadata(
            addr=_require_int(edit, "addr"),
            hunk=_edit_hunk(edit),
            end=end,
            name=_edit_str(edit, "name"),
            comment=_edit_str(edit, "comment"),
            type=entity_type,
            subtype=_edit_str(edit, "subtype") or default_subtype,
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.SEEDED,
            citation=_edit_citation(edit),
        )
        return replace(
            current,
            seeded_entities=tuple(
                item for item in current.seeded_entities if (item.hunk, item.addr) != (entity.hunk, entity.addr)
            )
            + (entity,),
        )
    if kind is TargetUiEditKind.ENTRYPOINT:
        current = _ensure_metadata(metadata)
        entrypoint = SeededCodeEntrypointMetadata(
            addr=_require_int(edit, "addr"),
            hunk=_edit_hunk(edit),
            name=_edit_str(edit, "name") or f"entry_{_require_int(edit, 'addr'):x}",
            comment=_edit_str(edit, "comment"),
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.SEEDED,
            citation=_edit_citation(edit),
        )
        return replace(
            current,
            seeded_code_entrypoints=tuple(
                item
                for item in current.seeded_code_entrypoints
                if (item.hunk, item.addr) != (entrypoint.hunk, entrypoint.addr)
            )
            + (entrypoint,),
        )
    if kind is TargetUiEditKind.LABEL:
        current = _ensure_metadata(metadata)
        seeded_label = SeededCodeLabelMetadata(
            addr=_require_int(edit, "addr"),
            hunk=_edit_hunk(edit),
            name=_require_str(edit, "name"),
            comment=_edit_str(edit, "comment"),
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.SEEDED,
            citation=_edit_citation(edit),
        )
        return replace(
            current,
            seeded_code_labels=tuple(
                item for item in current.seeded_code_labels if (item.hunk, item.addr) != (seeded_label.hunk, seeded_label.addr)
            )
            + (seeded_label,),
        )
    if kind is TargetUiEditKind.EXTERNAL_SYMBOL:
        current = _ensure_metadata(metadata)
        symbol = AbsoluteCodeLabelMetadata(
            addr=_require_int(edit, "addr"),
            name=_require_str(edit, "name"),
            comment=_edit_str(edit, "comment"),
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.SEEDED,
            citation=_edit_citation(edit),
        )
        return replace(
            current,
            absolute_code_labels=tuple(
                item for item in current.absolute_code_labels if item.addr != symbol.addr
            )
            + (symbol,),
        )
    if kind in _SUPPRESS_INFERRED_KINDS:
        current = _ensure_metadata(metadata)
        suppressed = SuppressedSeededItemMetadata(
            kind=SuppressedSeededItemKind.SEEDED_CODE_ENTRYPOINT
            if kind is TargetUiEditKind.SUPPRESS_INFERRED_CODE
            else SuppressedSeededItemKind.SEEDED_ENTITY,
            hunk=_edit_hunk(edit),
            addr=_require_int(edit, "addr"),
        )
        return replace(
            current,
            suppressed_seeded_items=tuple(
                item
                for item in current.suppressed_seeded_items
                if (item.kind, item.hunk, item.addr) != (suppressed.kind, suppressed.hunk, suppressed.addr)
            )
            + (suppressed,),
        )
    return metadata


def _ensure_metadata(metadata: TargetMetadata | None) -> TargetMetadata:
    if metadata is not None:
        return metadata
    return TargetMetadata(target_type="program", entry_register_seeds=())


def target_ui_edit_kind_from_json(value: object) -> TargetUiEditKind:
    if not isinstance(value, str) or not value:
        raise ValueError("target edit kind must be a non-empty string")
    try:
        return TargetUiEditKind(value)
    except ValueError as exc:
        raise ValueError(f"Unsupported target edit kind: {value}") from exc


def _require_parsed_target_ui_edit_kind(edit: dict[str, object]) -> TargetUiEditKind:
    kind = edit.get("kind")
    if not isinstance(kind, TargetUiEditKind):
        raise TypeError("target edit kind must be parsed at the JSON/API boundary")
    return kind


def _edit_hunk(edit: dict[str, object]) -> int:
    hunk = edit.get("hunk")
    return hunk if isinstance(hunk, int) else 0


def _edit_citation(edit: dict[str, object]) -> str:
    citation = edit.get("citation")
    return citation if isinstance(citation, str) and citation else "web-ui"


def _edit_str(edit: dict[str, object], key: str) -> str | None:
    value = edit.get(key)
    return value if isinstance(value, str) and value else None


def _require_int(edit: dict[str, object], key: str) -> int:
    value = edit.get(key)
    if not isinstance(value, int):
        raise ValueError(f"target edit {key} must be an integer")
    return value


def _optional_int(edit: dict[str, object], key: str) -> None:
    value = edit.get(key)
    if value is not None and not isinstance(value, int):
        raise ValueError(f"target edit {key} must be an integer")


def _require_str(edit: dict[str, object], key: str) -> str:
    value = edit.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"target edit {key} must be a non-empty string")
    return value


def _optional_str(edit: dict[str, object], key: str) -> None:
    value = edit.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"target edit {key} must be a string")
