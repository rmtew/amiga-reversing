from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import cast

from amiga_reversing.disasm.assembler_profiles import VASM_PROFILE, AssemblerProfile
from amiga_reversing.disasm.binary_source import (
    BinarySource,
    DiskEntryBinarySource,
    HunkFileBinarySource,
    RawBinarySource,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata

MANUAL_ACTION_LOG_FILE_NAME = "manual_actions.jsonl"
MANUAL_ACTION_LOG_VERSION = 1
RESERVED_MANUAL_ACTION_FIELDS = frozenset(
    {"record", "action_id", "sequence", "created_at", "kind"}
)

class ReviewState(StrEnum):
    CLEAR = "clear"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


class ReviewItemState(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"


class ReviewConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewItemKind(StrEnum):
    MANUAL_SEED_CONFLICT = "manual_seed_conflict"
    MANUAL_ACTION_LOG_INCONSISTENCY = "manual_action_log_inconsistency"
    MANUAL_ACTION_LOG_MALFORMED = "manual_action_log_malformed"
    MANUAL_ACTION_LOG_TARGET_MISMATCH = "manual_action_log_target_mismatch"
    REPRODUCTION_MISMATCH = "reproduction_mismatch"
    UNSUPPORTED_CONTAINER_SHAPE = "unsupported_container_shape"
    ORPHAN_CODE_CANDIDATE = "orphan_code_candidate"
    UNRECONCILED_DATA_RANGE = "unreconciled_data_range"
    SUSPICIOUS_INSTRUCTION_DECODE = "suspicious_instruction_decode"
    MANUAL_LABEL_UNRECONCILED = "manual_label_unreconciled"
    MANUAL_COMMENT_UNRECONCILED = "manual_comment_unreconciled"
    LABEL_SCOPE_CONFLICT = "label_scope_conflict"
    DECOMPRESSION_BLOCKER = "decompression_blocker"


def review_item_state(value: object) -> ReviewItemState | None:
    if isinstance(value, ReviewItemState):
        return value
    if not isinstance(value, str):
        return None
    try:
        return ReviewItemState(value)
    except ValueError:
        return None


def review_item_is_open(item: dict[str, object]) -> bool:
    return review_item_state(item.get("state")) is ReviewItemState.OPEN


def review_item_kind(value: object) -> ReviewItemKind | None:
    if isinstance(value, ReviewItemKind):
        return value
    if not isinstance(value, str):
        return None
    try:
        return ReviewItemKind(value)
    except ValueError:
        return None


class ManualActionKind(StrEnum):
    CREATE_MANUAL_SEED = "create_manual_seed"
    REMOVE_MANUAL_SEED = "remove_manual_seed"
    CREATE_MANUAL_LABEL = "create_manual_label"
    REMOVE_MANUAL_LABEL = "remove_manual_label"
    CREATE_MANUAL_COMMENT = "create_manual_comment"
    REMOVE_MANUAL_COMMENT = "remove_manual_comment"
    RESOLVE_REVIEW_ITEM = "resolve_review_item"
    UNDO_ACTION = "undo_action"
    REDO_ACTION = "redo_action"


def _manual_action_kind_id(kind: ManualActionKind | str) -> ManualActionKind:
    if isinstance(kind, ManualActionKind):
        return kind
    try:
        return ManualActionKind(kind)
    except ValueError:
        raise ValueError(f"Unsupported manual action kind: {kind}") from None


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
    kind: ManualActionKind
    payload: dict[str, object]


def manual_action_log_path(target_dir: Path) -> Path:
    return target_dir / MANUAL_ACTION_LOG_FILE_NAME


def append_manual_action(
    target_dir: Path,
    *,
    kind: ManualActionKind | str,
    payload: dict[str, object],
    binary_source: BinarySource,
) -> dict[str, object]:
    kind_id = _manual_action_kind_id(kind)
    validate_manual_action_payload(payload)
    path = manual_action_log_path(target_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                raw = json.loads(line)
                records.append(_object(raw, what="manual action log record"))
    else:
        records.append(
            {
                "record": "manual_action_log_header",
                "version": MANUAL_ACTION_LOG_VERSION,
                "target_identity": build_target_identity(binary_source),
            }
        )
    if not records or records[0].get("record") != "manual_action_log_header":
        raise ValueError("first record must be manual_action_log_header")
    pinned_target_identity = _object(records[0].get("target_identity"), what="target_identity")
    current_target_identity = build_target_identity(binary_source)
    if pinned_target_identity != current_target_identity:
        raise ValueError("Manual Action Log target identity does not match current target")
    max_sequence = 0
    for raw in records[1:]:
        if raw.get("record") != "manual_action":
            continue
        sequence = raw.get("sequence")
        if isinstance(sequence, int):
            max_sequence = max(max_sequence, sequence)
    action = {
        "record": "manual_action",
        "action_id": f"manual-{uuid.uuid4().hex}",
        "sequence": max_sequence + 1,
        "created_at": datetime.now(UTC).isoformat(),
        "kind": kind_id,
        **payload,
    }
    records.append(action)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return action


def validate_manual_action_payload(payload: dict[str, object]) -> None:
    reserved_fields = sorted(RESERVED_MANUAL_ACTION_FIELDS.intersection(payload))
    if reserved_fields:
        joined = ", ".join(reserved_fields)
        raise ValueError(f"Manual action payload contains reserved field(s): {joined}")


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
    review_state: ReviewState = ReviewState.CLEAR,
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


def _review_item_id(item: dict[str, object]) -> str:
    existing = item.get("item_id")
    if isinstance(existing, str) and existing:
        return existing
    kind = item.get("kind")
    scope = item.get("scope")
    if scope == "range":
        hunk = item.get("hunk")
        start = item.get("start")
        end = item.get("end")
        hunk_int = hunk if isinstance(hunk, int) else 0
        start_int = start if isinstance(start, int) else 0
        end_int = end if isinstance(end, int) else 0
        return f"{kind}:h{hunk_int}:${start_int:08x}-${end_int:08x}"
    return f"{kind}:target"


def _review_item_fingerprint(item: dict[str, object]) -> str:
    evidence = {
        key: value
        for key, value in item.items()
        if key not in {"state", "evidence_fingerprint", "review_confidence", "suggested_actions"}
    }
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _suggested_review_actions(item: dict[str, object]) -> list[dict[str, object]]:
    kind = review_item_kind(item.get("kind"))
    if kind is ReviewItemKind.MANUAL_SEED_CONFLICT:
        return [
            {"action": "navigate", "scope": item.get("scope"), "hunk": item.get("hunk"), "addr": item.get("start")},
            {"action": "edit_manual_seed", "seed_ids": item.get("seed_ids")},
        ]
    if kind in {
        ReviewItemKind.MANUAL_ACTION_LOG_INCONSISTENCY,
        ReviewItemKind.MANUAL_ACTION_LOG_MALFORMED,
        ReviewItemKind.MANUAL_ACTION_LOG_TARGET_MISMATCH,
    }:
        return [{"action": "repair_manual_action_log"}]
    if kind in {ReviewItemKind.REPRODUCTION_MISMATCH, ReviewItemKind.UNSUPPORTED_CONTAINER_SHAPE}:
        return [{"action": "open_reproduction_report"}, {"action": "rerun_round_trip_verification"}]
    if kind is ReviewItemKind.ORPHAN_CODE_CANDIDATE:
        return [
            {"action": "navigate", "scope": item.get("scope"), "hunk": item.get("hunk"), "addr": item.get("start")},
            {"action": "create_manual_seed", "seed_kind": "code", "mode": "required"},
            {"action": "resolve_as_data_or_padding"},
        ]
    if kind is ReviewItemKind.UNRECONCILED_DATA_RANGE:
        return [
            {"action": "navigate", "scope": item.get("scope"), "hunk": item.get("hunk"), "addr": item.get("start")},
            {"action": "create_manual_seed", "seed_kind": "data", "mode": "required"},
            {"action": "resolve_as_opaque_data"},
        ]
    if kind is ReviewItemKind.SUSPICIOUS_INSTRUCTION_DECODE:
        return [
            {"action": "navigate", "scope": item.get("scope"), "hunk": item.get("hunk"), "addr": item.get("start")},
            {"action": "create_manual_seed", "seed_kind": "data", "mode": "required"},
            {"action": "acknowledge"},
        ]
    if kind in {ReviewItemKind.MANUAL_LABEL_UNRECONCILED, ReviewItemKind.MANUAL_COMMENT_UNRECONCILED}:
        return [
            {"action": "navigate", "scope": item.get("scope"), "hunk": item.get("hunk"), "addr": item.get("start")},
            {"action": "create_manual_seed", "mode": "required"},
            {"action": "remove_manual_annotation"},
            {"action": "acknowledge"},
        ]
    if kind is ReviewItemKind.LABEL_SCOPE_CONFLICT:
        return [{"action": "rename_manual_label"}, {"action": "change_label_scope"}, {"action": "remove_manual_label"}]
    return []


def _finalize_review_items(
    items: list[dict[str, object]],
    resolutions: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    resolved_fingerprints: set[tuple[str, str]] = set()
    resolved_item_ids: set[str] = set()
    for resolution in resolutions:
        item_id = resolution.get("item_id")
        evidence_fingerprint = resolution.get("evidence_fingerprint")
        if isinstance(item_id, str) and isinstance(evidence_fingerprint, str):
            resolved_fingerprints.add((item_id, evidence_fingerprint))
            resolved_item_ids.add(item_id)

    finalized: list[dict[str, object]] = []
    for item in items:
        item = dict(item)
        item["item_id"] = _review_item_id(item)
        item["evidence_fingerprint"] = _review_item_fingerprint(item)
        item.setdefault("review_confidence", ReviewConfidence.HIGH)
        item.setdefault("suggested_actions", _suggested_review_actions(item))
        if (str(item["item_id"]), str(item["evidence_fingerprint"])) in resolved_fingerprints:
            if item.get("review_blocker") is True:
                item["acknowledged"] = True
            else:
                item["state"] = ReviewItemState.RESOLVED
        elif str(item["item_id"]) in resolved_item_ids:
            item["changed_since_resolution"] = True
        finalized.append(item)
    return tuple(finalized)


def _review_state_for_items(review_items: tuple[dict[str, object], ...]) -> ReviewState:
    open_review_items = tuple(item for item in review_items if review_item_is_open(item))
    if any(item.get("review_blocker") is True for item in open_review_items):
        return ReviewState.BLOCKED
    if open_review_items:
        return ReviewState.NEEDS_REVIEW
    return ReviewState.CLEAR


def finalize_review_items(
    items: tuple[dict[str, object], ...],
    resolutions: tuple[dict[str, object], ...] = (),
) -> tuple[dict[str, object], ...]:
    return _finalize_review_items(list(items), resolutions)


def _blocked_projection(
    path: Path,
    *,
    kind: ReviewItemKind,
    message: str,
    pinned_target_identity: dict[str, object] | None = None,
    current_target_identity: dict[str, object] | None = None,
) -> ManualActionLogProjection:
    item: dict[str, object] = {
        "kind": kind,
        "scope": "target",
        "state": ReviewItemState.OPEN,
        "message": message,
    }
    review_items = _finalize_review_items([item], ())
    return _empty_projection(
        path,
        pinned_target_identity=pinned_target_identity,
        current_target_identity=current_target_identity,
        review_state=ReviewState.BLOCKED,
        diagnostics=review_items,
        review_items=review_items,
    )


def _needs_review_item(kind: ReviewItemKind, message: str) -> dict[str, object]:
    return {"kind": kind, "scope": "target", "state": ReviewItemState.OPEN, "message": message}


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


def _metadata_global_label_names(metadata: TargetMetadata | None) -> set[str]:
    if metadata is None:
        return set()
    names: set[str] = set()
    for label in (*metadata.seeded_code_labels, *metadata.absolute_code_labels):
        names.add(label.name)
    for entity in metadata.seeded_entities:
        if entity.name is not None:
            names.add(entity.name)
    return names


def _manual_label_conflict_items(
    labels: dict[str, dict[str, object]],
    *,
    stronger_metadata: TargetMetadata | None,
    assembler_profile: AssemblerProfile,
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    global_labels: dict[str, dict[str, object]] = {}
    metadata_names = _metadata_global_label_names(stronger_metadata)
    local_profile = assembler_profile.render.local_labels
    reserved_local_names = set(local_profile.reserved_names)
    for label in labels.values():
        label_id = label.get("label_id")
        name = label.get("name")
        scope = label.get("scope") or "global"
        if not isinstance(label_id, str) or not isinstance(name, str):
            continue
        label_range = _manual_seed_range(label)
        if scope == "local":
            owner_id = label.get("owner_id") or label.get("owner_label_id")
            hunk, start, end = label_range or (0, 0, 1)
            if not isinstance(owner_id, str) or not owner_id:
                items.append(
                    {
                        "kind": ReviewItemKind.LABEL_SCOPE_CONFLICT,
                        "item_id": f"label_scope_conflict:{label_id}:missing-owner",
                        "scope": "range",
                        "state": ReviewItemState.OPEN,
                        "review_blocker": True,
                        "label_ids": [label_id],
                        "hunk": hunk,
                        "start": start,
                        "end": end,
                        "message": f"Local manual label {label_id} has no explicit owner id",
                    }
                )
                continue
            if (
                not local_profile.supported
                or local_profile.prefix is None
                or not name.startswith(local_profile.prefix)
                or local_profile.required_mode_flags
            ):
                items.append(
                    {
                        "kind": ReviewItemKind.LABEL_SCOPE_CONFLICT,
                        "item_id": f"label_scope_conflict:{label_id}:unsupported-local-profile",
                        "scope": "range",
                        "state": ReviewItemState.OPEN,
                        "review_blocker": True,
                        "label_ids": [label_id],
                        "hunk": hunk,
                        "start": start,
                        "end": end,
                        "message": (
                            f"Local manual label {label_id} cannot be emitted by assembler profile "
                            f"{assembler_profile.assembler_id!r}"
                        ),
                    }
                )
                continue
            if name in reserved_local_names:
                items.append(
                    {
                        "kind": ReviewItemKind.LABEL_SCOPE_CONFLICT,
                        "item_id": f"label_scope_conflict:{label_id}:reserved-local-name",
                        "scope": "range",
                        "state": ReviewItemState.OPEN,
                        "review_blocker": True,
                        "label_ids": [label_id],
                        "hunk": hunk,
                        "start": start,
                        "end": end,
                        "message": f"Local manual label {label_id} uses reserved local name {name!r}",
                    }
                )
            continue
        if scope != "global":
            continue
        if name in metadata_names:
            hunk, start, end = label_range or (0, 0, 1)
            items.append(
                {
                    "kind": ReviewItemKind.LABEL_SCOPE_CONFLICT,
                    "item_id": f"label_scope_conflict:{label_id}:metadata-collision",
                    "scope": "range",
                    "state": ReviewItemState.OPEN,
                    "review_blocker": False,
                    "label_ids": [label_id],
                    "hunk": hunk,
                    "start": start,
                    "end": end,
                    "message": f"Global manual label name {name!r} collides with existing metadata label",
                }
            )
        previous = global_labels.get(name)
        if previous is None:
            global_labels[name] = label
            continue
        previous_id = previous.get("label_id")
        if not isinstance(previous_id, str):
            continue
        left_range = _manual_seed_range(previous)
        right_range = label_range
        hunk, start, end = right_range or left_range or (0, 0, 1)
        items.append(
            {
                "kind": ReviewItemKind.LABEL_SCOPE_CONFLICT,
                "item_id": f"label_scope_conflict:{min(previous_id, label_id)}:{max(previous_id, label_id)}",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "label_ids": [previous_id, label_id],
                "hunk": hunk,
                "start": start,
                "end": end,
                "message": f"Global manual label name {name!r} is not unique",
            }
        )
    return items


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
                    "kind": ReviewItemKind.MANUAL_SEED_CONFLICT,
                    "item_id": item_id,
                    "scope": "range",
                    "state": ReviewItemState.OPEN,
                    "review_blocker": True,
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
                    "kind": ReviewItemKind.MANUAL_SEED_CONFLICT,
                    "item_id": f"manual_seed_conflict:{seed_id}:{stronger_id}",
                    "scope": "range",
                    "state": ReviewItemState.OPEN,
                    "review_blocker": True,
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
                "kind": ReviewItemKind.MANUAL_SEED_CONFLICT,
                "item_id": f"manual_seed_conflict:{seed_id}:{source_id}",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
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
    kind = _manual_action_kind_id(_str_field(raw, "kind", what="manual action"))
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
    return _str_field(action.payload, field_name, what=str(action.kind))


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
    assembler_profile: AssemblerProfile,
    actions: list[_ManualAction],
    review_items: list[dict[str, object]],
) -> ManualActionLogProjection:
    undone_action_ids: set[str] = set()
    seen_action_ids: set[str] = set()
    for action in actions:
        if action.kind is ManualActionKind.UNDO_ACTION:
            action_id = _action_ref(action, "undoes_action_id")
            if action_id in seen_action_ids:
                undone_action_ids.add(action_id)
        elif action.kind is ManualActionKind.REDO_ACTION:
            action_id = _action_ref(action, "redoes_action_id")
            if action_id in seen_action_ids:
                undone_action_ids.discard(action_id)
        seen_action_ids.add(action.action_id)

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
        if action.kind is ManualActionKind.CREATE_MANUAL_SEED:
            _put_by_id(seeds, _action_object(action, "seed"), "seed_id")
        elif action.kind is ManualActionKind.REMOVE_MANUAL_SEED:
            _drop_by_id(seeds, action, "seed_id")
        elif action.kind is ManualActionKind.CREATE_MANUAL_LABEL:
            _put_by_id(labels, _action_object(action, "label"), "label_id")
        elif action.kind is ManualActionKind.REMOVE_MANUAL_LABEL:
            _drop_by_id(labels, action, "label_id")
        elif action.kind is ManualActionKind.CREATE_MANUAL_COMMENT:
            _put_by_id(comments, _action_object(action, "comment"), "comment_id")
        elif action.kind is ManualActionKind.REMOVE_MANUAL_COMMENT:
            _drop_by_id(comments, action, "comment_id")
        elif action.kind is ManualActionKind.RESOLVE_REVIEW_ITEM:
            _put_by_id(resolutions, _action_object(action, "resolution"), "resolution_id")
        elif action.kind in {ManualActionKind.UNDO_ACTION, ManualActionKind.REDO_ACTION}:
            pass
        else:
            raise ValueError(f"Unsupported manual action kind: {action.kind}")

    review_items.extend(_manual_seed_conflict_items(seeds))
    review_items.extend(_manual_seed_metadata_conflict_items(seeds, stronger_metadata))
    review_items.extend(_manual_seed_binary_source_conflict_items(seeds, binary_source))
    review_items.extend(
        _manual_label_conflict_items(
            labels,
            stronger_metadata=stronger_metadata,
            assembler_profile=assembler_profile,
        )
    )
    finalized_review_items = _finalize_review_items(review_items, tuple(resolutions.values()))
    review_state = _review_state_for_items(finalized_review_items)
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
        diagnostics=finalized_review_items,
        review_items=finalized_review_items,
    )


def load_manual_projection(
    target_dir: Path,
    *,
    binary_source: BinarySource | None = None,
    stronger_metadata: TargetMetadata | None = None,
    assembler_profile: AssemblerProfile = VASM_PROFILE,
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
            kind=ReviewItemKind.MANUAL_ACTION_LOG_MALFORMED,
            message=str(exc),
        )

    if not records:
        return _blocked_projection(
            path,
            kind=ReviewItemKind.MANUAL_ACTION_LOG_MALFORMED,
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
            kind=ReviewItemKind.MANUAL_ACTION_LOG_MALFORMED,
            message=str(exc),
        )

    current_target_identity = build_target_identity(binary_source) if binary_source is not None else None
    if current_target_identity is not None and pinned_target_identity != current_target_identity:
        return _blocked_projection(
            path,
            kind=ReviewItemKind.MANUAL_ACTION_LOG_TARGET_MISMATCH,
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
                        ReviewItemKind.MANUAL_ACTION_LOG_INCONSISTENCY,
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
            assembler_profile=assembler_profile,
            actions=actions,
            review_items=review_items,
        )
    except ValueError as exc:
        return _blocked_projection(
            path,
            kind=ReviewItemKind.MANUAL_ACTION_LOG_MALFORMED,
            message=str(exc),
            pinned_target_identity=pinned_target_identity,
            current_target_identity=current_target_identity,
        )
