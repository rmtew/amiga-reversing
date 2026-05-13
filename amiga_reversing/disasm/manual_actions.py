from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, cast

from amiga_reversing.disasm.binary_source import (
    BinarySource,
    DiskEntryBinarySource,
    HunkFileBinarySource,
    RawBinarySource,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata

MANUAL_ACTION_LOG_FILE_NAME = "manual_actions.jsonl"
MANUAL_ACTION_LOG_VERSION = 1

type ReviewState = Literal["clear", "needs_review", "blocked"]


@dataclass(frozen=True, slots=True)
class ManualActionLogProjection:
    review_state: ReviewState
    log_path: str
    pinned_target_identity: dict[str, object] | None
    current_target_identity: dict[str, object] | None
    seeds: tuple[dict[str, object], ...]
    labels: tuple[dict[str, object], ...]
    comments: tuple[dict[str, object], ...]
    resolutions: tuple[dict[str, object], ...]
    active_action_ids: tuple[str, ...]
    inactive_action_ids: tuple[str, ...]
    diagnostics: tuple[dict[str, object], ...]
    review_items: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        assert isinstance(result, dict)
        return result


@dataclass(frozen=True, slots=True)
class _ManualAction:
    action_id: str
    sequence: int
    created_at: str
    kind: str
    payload: dict[str, object]


def manual_action_log_path(target_dir: Path) -> Path:
    return target_dir / MANUAL_ACTION_LOG_FILE_NAME


def build_target_identity(binary_source: BinarySource) -> dict[str, object]:
    original_bytes = binary_source.read_bytes()
    identity: dict[str, object] = {
        "schema_version": 1,
        "source_kind": binary_source.kind,
        "original_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "original_size": len(original_bytes),
    }
    if isinstance(binary_source, HunkFileBinarySource):
        identity.update(
            {
                "target_format": "amiga_hunk",
                "display_path": binary_source.display_path,
                "parent_disk_id": binary_source.parent_disk_id,
            }
        )
    elif isinstance(binary_source, DiskEntryBinarySource):
        identity.update(
            {
                "target_format": "disk_entry",
                "disk_id": binary_source.disk_id,
                "entry_path": binary_source.entry_path,
                "parent_disk_id": binary_source.parent_disk_id,
            }
        )
    elif isinstance(binary_source, RawBinarySource):
        identity.update(
            {
                "target_format": "raw_binary",
                "address_model": binary_source.address_model,
                "load_address": binary_source.load_address,
                "entrypoint": binary_source.entrypoint,
                "code_start_offset": binary_source.code_start_offset,
                "parent_disk_id": binary_source.parent_disk_id,
            }
        )
    return identity


def _empty_projection(
    path: Path,
    *,
    pinned_target_identity: dict[str, object] | None = None,
    current_target_identity: dict[str, object] | None = None,
    review_state: ReviewState = "clear",
    diagnostics: tuple[dict[str, object], ...] = (),
    review_items: tuple[dict[str, object], ...] = (),
) -> ManualActionLogProjection:
    return ManualActionLogProjection(
        review_state=review_state,
        log_path=str(path),
        pinned_target_identity=pinned_target_identity,
        current_target_identity=current_target_identity,
        seeds=(),
        labels=(),
        comments=(),
        resolutions=(),
        active_action_ids=(),
        inactive_action_ids=(),
        diagnostics=diagnostics,
        review_items=review_items,
    )


def _blocked_projection(
    path: Path,
    *,
    kind: str,
    message: str,
    pinned_target_identity: dict[str, object] | None = None,
    current_target_identity: dict[str, object] | None = None,
) -> ManualActionLogProjection:
    item: dict[str, object] = {
        "kind": kind,
        "scope": "target",
        "state": "open",
        "message": message,
    }
    return _empty_projection(
        path,
        pinned_target_identity=pinned_target_identity,
        current_target_identity=current_target_identity,
        review_state="blocked",
        diagnostics=(item,),
        review_items=(item,),
    )


def _needs_review_item(kind: str, message: str) -> dict[str, object]:
    return {"kind": kind, "scope": "target", "state": "open", "message": message}


def _manual_seed_int(seed: dict[str, object], field_name: str) -> int | None:
    value = seed.get(field_name)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.replace("$", "0x"), 0)
        except ValueError:
            return None
    return None


def _manual_seed_range(seed: dict[str, object]) -> tuple[int, int, int] | None:
    hunk = _manual_seed_int(seed, "hunk") or 0
    addr = _manual_seed_int(seed, "addr")
    end = _manual_seed_int(seed, "end")
    if addr is not None:
        return hunk, addr, end if end is not None and end > addr else addr + 1
    raw_range = seed.get("range")
    if not isinstance(raw_range, str):
        return None
    range_text = raw_range.strip()
    if ":" in range_text:
        hunk_text, range_text = range_text.split(":", 1)
        if hunk_text.lower().startswith("h"):
            try:
                hunk = int(hunk_text[1:], 0)
            except ValueError:
                return None
    if ".." in range_text:
        start_text, end_text = range_text.split("..", 1)
        try:
            start = int(start_text.replace("$", "0x"), 0)
            parsed_end = int(end_text.replace("$", "0x"), 0)
        except ValueError:
            return None
        return hunk, start, parsed_end if parsed_end > start else start + 1
    try:
        start = int(range_text.replace("$", "0x"), 0)
    except ValueError:
        return None
    return hunk, start, start + 1


def _manual_seed_required(seed: dict[str, object]) -> bool:
    mode = seed.get("mode")
    return mode is None or mode == "required"


def _manual_seed_conflict_items(seeds: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    values = list(seeds.values())
    for left_index, left in enumerate(values):
        left_id = left.get("seed_id")
        left_kind = left.get("kind")
        left_range = _manual_seed_range(left)
        if not isinstance(left_id, str) or not isinstance(left_kind, str) or left_range is None:
            continue
        if not _manual_seed_required(left):
            continue
        for right in values[left_index + 1:]:
            right_id = right.get("seed_id")
            right_kind = right.get("kind")
            right_range = _manual_seed_range(right)
            if not isinstance(right_id, str) or not isinstance(right_kind, str) or right_range is None:
                continue
            if not _manual_seed_required(right) or right_kind == left_kind:
                continue
            if left_range[0] != right_range[0] or left_range[1] >= right_range[2] or right_range[1] >= left_range[2]:
                continue
            item_id = f"manual_seed_conflict:{min(left_id, right_id)}:{max(left_id, right_id)}"
            items.append(
                {
                    "kind": "manual_seed_conflict",
                    "item_id": item_id,
                    "scope": "range",
                    "state": "open",
                    "seed_ids": [left_id, right_id],
                    "hunk": left_range[0],
                    "start": max(left_range[1], right_range[1]),
                    "end": min(left_range[2], right_range[2]),
                    "message": f"Required manual seeds {left_id} and {right_id} conflict",
                }
            )
    return items


def _manual_seed_metadata_conflict_items(
    seeds: dict[str, dict[str, object]],
    metadata: TargetMetadata | None,
) -> list[dict[str, object]]:
    if metadata is None:
        return []
    items: list[dict[str, object]] = []
    stronger_ranges: list[tuple[str, str, int, int, int, str | None]] = []
    for entrypoint in metadata.seeded_code_entrypoints:
        stronger_id = f"seeded_code_entrypoint:h{entrypoint.hunk}:${entrypoint.addr:08x}"
        stronger_ranges.append(("code", stronger_id, entrypoint.hunk, entrypoint.addr, entrypoint.addr + 1, entrypoint.name))
    for entity in metadata.seeded_entities:
        end = entity.end if entity.end is not None and entity.end > entity.addr else entity.addr + 1
        stronger_id = f"seeded_entity:h{entity.hunk}:${entity.addr:08x}"
        stronger_ranges.append(("data", stronger_id, entity.hunk, entity.addr, end, entity.name))

    for seed in seeds.values():
        seed_id = seed.get("seed_id")
        seed_kind = seed.get("kind")
        seed_range = _manual_seed_range(seed)
        if not isinstance(seed_id, str) or not isinstance(seed_kind, str) or seed_range is None:
            continue
        if not _manual_seed_required(seed):
            continue
        seed_hunk, seed_start, seed_end = seed_range
        for stronger_kind, stronger_id, stronger_hunk, stronger_start, stronger_end, stronger_name in stronger_ranges:
            if seed_kind == stronger_kind:
                continue
            if seed_hunk != stronger_hunk or seed_start >= stronger_end or stronger_start >= seed_end:
                continue
            items.append(
                {
                    "kind": "manual_seed_conflict",
                    "item_id": f"manual_seed_conflict:{seed_id}:{stronger_id}",
                    "scope": "range",
                    "state": "open",
                    "seed_ids": [seed_id],
                    "stronger_kind": stronger_kind,
                    "stronger_source": stronger_id,
                    "stronger_name": stronger_name,
                    "hunk": seed_hunk,
                    "start": max(seed_start, stronger_start),
                    "end": min(seed_end, stronger_end),
                    "message": f"Required manual seed {seed_id} conflicts with stronger {stronger_id}",
                }
            )
    return items


def _manual_seed_binary_source_conflict_items(
    seeds: dict[str, dict[str, object]],
    binary_source: BinarySource | None,
) -> list[dict[str, object]]:
    if not isinstance(binary_source, RawBinarySource):
        return []
    entrypoint = binary_source.analysis_entrypoint
    source_id = f"source_entrypoint:h0:${entrypoint:08x}"
    items: list[dict[str, object]] = []
    for seed in seeds.values():
        seed_id = seed.get("seed_id")
        seed_kind = seed.get("kind")
        seed_range = _manual_seed_range(seed)
        if not isinstance(seed_id, str) or seed_kind != "data" or seed_range is None:
            continue
        if not _manual_seed_required(seed):
            continue
        hunk, start, end = seed_range
        if hunk != 0 or start > entrypoint or end <= entrypoint:
            continue
        items.append(
            {
                "kind": "manual_seed_conflict",
                "item_id": f"manual_seed_conflict:{seed_id}:{source_id}",
                "scope": "range",
                "state": "open",
                "seed_ids": [seed_id],
                "stronger_kind": "code",
                "stronger_source": source_id,
                "stronger_name": "entrypoint",
                "hunk": 0,
                "start": entrypoint,
                "end": entrypoint + 1,
                "message": f"Required manual seed {seed_id} conflicts with stronger {source_id}",
            }
        )
    return items


def _object(value: object, *, what: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{what} must be an object")
    return cast(dict[str, object], value)


def _str_field(raw: dict[str, object], field_name: str, *, what: str) -> str:
    value = raw.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"{what} {field_name} must be a string")
    return value


def _int_field(raw: dict[str, object], field_name: str, *, what: str) -> int:
    value = raw.get(field_name)
    if not isinstance(value, int):
        raise ValueError(f"{what} {field_name} must be an integer")
    return value


def _parse_action(raw: dict[str, object]) -> _ManualAction:
    if raw.get("record") != "manual_action":
        raise ValueError("manual action record must be manual_action")
    action_id = _str_field(raw, "action_id", what="manual action")
    sequence = _int_field(raw, "sequence", what="manual action")
    created_at = _str_field(raw, "created_at", what="manual action")
    kind = _str_field(raw, "kind", what="manual action")
    return _ManualAction(
        action_id=action_id,
        sequence=sequence,
        created_at=created_at,
        kind=kind,
        payload=dict(raw),
    )


def _action_object(action: _ManualAction, field_name: str) -> dict[str, object]:
    return _object(action.payload.get(field_name), what=f"{action.kind} {field_name}")


def _action_ref(action: _ManualAction, field_name: str) -> str:
    return _str_field(action.payload, field_name, what=action.kind)


def _put_by_id(
    target: dict[str, dict[str, object]],
    value: dict[str, object],
    id_field: str,
) -> None:
    object_id = value.get(id_field)
    if not isinstance(object_id, str):
        raise ValueError(f"{id_field} must be a string")
    target[object_id] = value


def _drop_by_id(
    target: dict[str, dict[str, object]],
    action: _ManualAction,
    id_field: str,
) -> None:
    object_id = _action_ref(action, id_field)
    target.pop(object_id, None)


def _project_actions(
    path: Path,
    *,
    pinned_target_identity: dict[str, object],
    current_target_identity: dict[str, object] | None,
    binary_source: BinarySource | None,
    stronger_metadata: TargetMetadata | None,
    actions: list[_ManualAction],
    review_items: list[dict[str, object]],
) -> ManualActionLogProjection:
    undone_action_ids: set[str] = set()
    actions_by_id: dict[str, _ManualAction] = {}
    for action in actions:
        actions_by_id[action.action_id] = action
        if action.kind == "undo_action":
            undone_action_ids.add(_action_ref(action, "undoes_action_id"))
        elif action.kind == "redo_action":
            undone_action_ids.discard(_action_ref(action, "redoes_action_id"))

    seeds: dict[str, dict[str, object]] = {}
    labels: dict[str, dict[str, object]] = {}
    comments: dict[str, dict[str, object]] = {}
    resolutions: dict[str, dict[str, object]] = {}
    active_action_ids: list[str] = []
    inactive_action_ids: list[str] = []

    for action in actions:
        if action.action_id in undone_action_ids:
            inactive_action_ids.append(action.action_id)
            continue
        active_action_ids.append(action.action_id)
        if action.kind == "create_manual_seed":
            _put_by_id(seeds, _action_object(action, "seed"), "seed_id")
        elif action.kind == "remove_manual_seed":
            _drop_by_id(seeds, action, "seed_id")
        elif action.kind == "create_manual_label":
            _put_by_id(labels, _action_object(action, "label"), "label_id")
        elif action.kind == "remove_manual_label":
            _drop_by_id(labels, action, "label_id")
        elif action.kind == "create_manual_comment":
            _put_by_id(comments, _action_object(action, "comment"), "comment_id")
        elif action.kind == "remove_manual_comment":
            _drop_by_id(comments, action, "comment_id")
        elif action.kind == "resolve_review_item":
            _put_by_id(resolutions, _action_object(action, "resolution"), "resolution_id")
        elif action.kind in {"undo_action", "redo_action"}:
            pass
        else:
            raise ValueError(f"Unsupported manual action kind: {action.kind}")

    review_items.extend(_manual_seed_conflict_items(seeds))
    review_items.extend(_manual_seed_metadata_conflict_items(seeds, stronger_metadata))
    review_items.extend(_manual_seed_binary_source_conflict_items(seeds, binary_source))
    review_state: ReviewState = "needs_review" if review_items else "clear"
    return ManualActionLogProjection(
        review_state=review_state,
        log_path=str(path),
        pinned_target_identity=pinned_target_identity,
        current_target_identity=current_target_identity,
        seeds=tuple(seeds.values()),
        labels=tuple(labels.values()),
        comments=tuple(comments.values()),
        resolutions=tuple(resolutions.values()),
        active_action_ids=tuple(active_action_ids),
        inactive_action_ids=tuple(inactive_action_ids),
        diagnostics=tuple(review_items),
        review_items=tuple(review_items),
    )


def load_manual_projection(
    target_dir: Path,
    *,
    binary_source: BinarySource | None = None,
    stronger_metadata: TargetMetadata | None = None,
) -> ManualActionLogProjection:
    path = manual_action_log_path(target_dir)
    if not path.exists():
        return _empty_projection(path)

    records: list[dict[str, object]] = []
    try:
        with open(path, encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                record = _object(json.loads(stripped), what=f"line {line_number}")
                records.append(record)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _blocked_projection(
            path,
            kind="manual_action_log_malformed",
            message=str(exc),
        )

    if not records:
        return _blocked_projection(
            path,
            kind="manual_action_log_malformed",
            message="Manual Action Log exists but has no header",
        )

    header = records[0]
    try:
        if header.get("record") != "manual_action_log_header":
            raise ValueError("first record must be manual_action_log_header")
        version = _int_field(header, "version", what="manual action log header")
        if version != MANUAL_ACTION_LOG_VERSION:
            raise ValueError(f"unsupported Manual Action Log version: {version}")
        pinned_target_identity = _object(header.get("target_identity"), what="target_identity")
    except ValueError as exc:
        return _blocked_projection(
            path,
            kind="manual_action_log_malformed",
            message=str(exc),
        )

    current_target_identity = build_target_identity(binary_source) if binary_source is not None else None
    if current_target_identity is not None and pinned_target_identity != current_target_identity:
        return _blocked_projection(
            path,
            kind="manual_action_log_target_mismatch",
            message="Manual Action Log target identity does not match current target",
            pinned_target_identity=pinned_target_identity,
            current_target_identity=current_target_identity,
        )

    review_items: list[dict[str, object]] = []
    actions: list[_ManualAction] = []
    expected_sequence = 1
    seen_action_ids: set[str] = set()
    reported_sequence_inconsistency = False
    try:
        for raw in records[1:]:
            action = _parse_action(raw)
            if action.action_id in seen_action_ids:
                raise ValueError(f"duplicate manual action id: {action.action_id}")
            seen_action_ids.add(action.action_id)
            if action.sequence != expected_sequence and not reported_sequence_inconsistency:
                review_items.append(
                    _needs_review_item(
                        "manual_action_log_inconsistency",
                        f"Action {action.action_id} has sequence {action.sequence}; expected {expected_sequence}",
                    )
                )
                reported_sequence_inconsistency = True
            expected_sequence += 1
            actions.append(action)
        return _project_actions(
            path,
            pinned_target_identity=pinned_target_identity,
            current_target_identity=current_target_identity,
            binary_source=binary_source,
            stronger_metadata=stronger_metadata,
            actions=actions,
            review_items=review_items,
        )
    except ValueError as exc:
        return _blocked_projection(
            path,
            kind="manual_action_log_malformed",
            message=str(exc),
            pinned_target_identity=pinned_target_identity,
            current_target_identity=current_target_identity,
        )
