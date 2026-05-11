from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from amiga_reversing.disasm.target_metadata import (
    AbsoluteCodeLabelMetadata,
    SeededCodeEntrypointMetadata,
    SeededCodeLabelMetadata,
    SeededEntityMetadata,
    SuppressedSeededItemMetadata,
    TargetMetadata,
)

TARGET_UI_EDITS_FILE_NAME = "target_ui_edits.json"

_MATERIALIZED_ENTITY_KINDS = {
    "code_range": ("code", None),
    "data_range": ("data", None),
    "pointer_table": ("data", "pointer_table"),
    "text_range": ("data", "string"),
    "jump_table": ("data", "jump_table"),
}


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
        edits.append(cast(dict[str, object], item))
    return edits


def target_ui_edits_stamp_text(target_dir: Path) -> str:
    edits = load_target_ui_edits(target_dir)
    if not edits:
        return ""
    return json.dumps(edits, indent=2, sort_keys=True) + "\n"


def append_target_ui_edit(target_dir: Path, edit: dict[str, object]) -> dict[str, object]:
    kind = edit.get("kind")
    if not isinstance(kind, str) or not kind:
        raise ValueError("target edit kind must be a non-empty string")
    normalized = dict(edit)
    normalized.setdefault("id", str(uuid4()))
    normalized.setdefault("created_at", datetime.now(UTC).isoformat(timespec="seconds"))
    normalized["kind"] = kind
    _validate_target_ui_edit(normalized)
    edits = load_target_ui_edits(target_dir)
    edits.append(normalized)
    target_ui_edits_path(target_dir).write_text(
        json.dumps(edits, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return normalized


def apply_target_ui_edits(
    metadata: TargetMetadata | None,
    edits: list[dict[str, object]],
) -> TargetMetadata | None:
    current = metadata
    for edit in edits:
        current = _apply_target_ui_edit(current, edit)
    return current


def _validate_target_ui_edit(edit: dict[str, object]) -> None:
    kind = edit["kind"]
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
    if kind == "entrypoint":
        _require_int(edit, "addr")
        _optional_int(edit, "hunk")
        _optional_str(edit, "name")
        _optional_str(edit, "comment")
        return
    if kind == "label":
        _require_int(edit, "addr")
        _require_str(edit, "name")
        _optional_int(edit, "hunk")
        _optional_str(edit, "comment")
        return
    if kind == "external_symbol":
        _require_int(edit, "addr")
        _require_str(edit, "name")
        _optional_str(edit, "comment")
        return
    if kind in {"suppress_inferred_code", "suppress_inferred_pointer"}:
        _require_int(edit, "addr")
        _optional_int(edit, "hunk")
        return
    raise ValueError(f"Unsupported target edit kind: {kind}")


def _apply_target_ui_edit(
    metadata: TargetMetadata | None,
    edit: dict[str, object],
) -> TargetMetadata | None:
    kind = cast(str, edit["kind"])
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
            seed_origin="manual_analysis",
            review_status="seeded",
            citation=_edit_citation(edit),
        )
        return replace(
            current,
            seeded_entities=tuple(
                item for item in current.seeded_entities if (item.hunk, item.addr) != (entity.hunk, entity.addr)
            )
            + (entity,),
        )
    if kind == "entrypoint":
        current = _ensure_metadata(metadata)
        entrypoint = SeededCodeEntrypointMetadata(
            addr=_require_int(edit, "addr"),
            hunk=_edit_hunk(edit),
            name=_edit_str(edit, "name") or f"entry_{_require_int(edit, 'addr'):x}",
            comment=_edit_str(edit, "comment"),
            seed_origin="manual_analysis",
            review_status="seeded",
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
    if kind == "label":
        current = _ensure_metadata(metadata)
        seeded_label = SeededCodeLabelMetadata(
            addr=_require_int(edit, "addr"),
            hunk=_edit_hunk(edit),
            name=_require_str(edit, "name"),
            comment=_edit_str(edit, "comment"),
            seed_origin="manual_analysis",
            review_status="seeded",
            citation=_edit_citation(edit),
        )
        return replace(
            current,
            seeded_code_labels=tuple(
                item for item in current.seeded_code_labels if (item.hunk, item.addr) != (seeded_label.hunk, seeded_label.addr)
            )
            + (seeded_label,),
        )
    if kind == "external_symbol":
        current = _ensure_metadata(metadata)
        symbol = AbsoluteCodeLabelMetadata(
            addr=_require_int(edit, "addr"),
            name=_require_str(edit, "name"),
            comment=_edit_str(edit, "comment"),
            seed_origin="manual_analysis",
            review_status="seeded",
            citation=_edit_citation(edit),
        )
        return replace(
            current,
            absolute_code_labels=tuple(
                item for item in current.absolute_code_labels if item.addr != symbol.addr
            )
            + (symbol,),
        )
    if kind in {"suppress_inferred_code", "suppress_inferred_pointer"}:
        current = _ensure_metadata(metadata)
        suppressed = SuppressedSeededItemMetadata(
            kind="seeded_code_entrypoint" if kind == "suppress_inferred_code" else "seeded_entity",
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
