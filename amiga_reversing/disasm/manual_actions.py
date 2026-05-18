from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
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
from amiga_reversing.disasm.target_metadata import (
    SuppressedSeededItemKind,
    TargetMetadata,
)

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
    REVIEW_NOTE = "review_note"
    LABEL_SCOPE_CONFLICT = "label_scope_conflict"
    DECOMPRESSION_BLOCKER = "decompression_blocker"


class ReviewItemScope(StrEnum):
    TARGET = "target"
    RANGE = "range"


class SuggestedReviewActionKind(StrEnum):
    ACKNOWLEDGE = "acknowledge"
    CHANGE_LABEL_SCOPE = "change_label_scope"
    CREATE_MANUAL_SEED = "create_manual_seed"
    EDIT_MANUAL_SEED = "edit_manual_seed"
    NAVIGATE = "navigate"
    OPEN_REPRODUCTION_REPORT = "open_reproduction_report"
    REMOVE_MANUAL_ANNOTATION = "remove_manual_annotation"
    REMOVE_MANUAL_LABEL = "remove_manual_label"
    RENAME_MANUAL_LABEL = "rename_manual_label"
    REPAIR_MANUAL_ACTION_LOG = "repair_manual_action_log"
    RERUN_ROUND_TRIP_VERIFICATION = "rerun_round_trip_verification"
    RESOLVE_AS_DATA_OR_PADDING = "resolve_as_data_or_padding"
    RESOLVE_AS_OPAQUE_DATA = "resolve_as_opaque_data"


class ManualSeedKind(StrEnum):
    CODE = "code"
    DATA = "data"


class ManualSeedMode(StrEnum):
    REQUIRED = "required"


class ManualLabelScope(StrEnum):
    GLOBAL = "global"
    LOCAL = "local"


def review_item_is_open(item: dict[str, object]) -> bool:
    state = item.get("state")
    if not isinstance(state, ReviewItemState):
        raise TypeError("review item state must be a ReviewItemState")
    return state is ReviewItemState.OPEN


def _manual_seed_kind_from_json(value: object) -> ManualSeedKind | None:
    if not isinstance(value, str):
        return None
    try:
        return ManualSeedKind(value)
    except ValueError:
        return None


def _manual_seed_mode_from_json(value: object) -> ManualSeedMode | None:
    if not isinstance(value, str):
        return None
    try:
        return ManualSeedMode(value)
    except ValueError:
        return None


def _manual_label_scope_from_json(value: object) -> ManualLabelScope | None:
    if not isinstance(value, str):
        return None
    try:
        return ManualLabelScope(value)
    except ValueError:
        return None


class ManualActionKind(StrEnum):
    CREATE_MANUAL_SEED = "create_manual_seed"
    REMOVE_MANUAL_SEED = "remove_manual_seed"
    RENAME_DATA_SYMBOL = "rename_data_symbol"
    CREATE_MANUAL_REGISTER_SEED = "create_manual_register_seed"
    REMOVE_MANUAL_REGISTER_SEED = "remove_manual_register_seed"
    CREATE_MANUAL_LABEL = "create_manual_label"
    REMOVE_MANUAL_LABEL = "remove_manual_label"
    RENAME_MANUAL_LABEL = "rename_manual_label"
    CHANGE_LABEL_SCOPE = "change_label_scope"
    CREATE_MANUAL_COMMENT = "create_manual_comment"
    REMOVE_MANUAL_COMMENT = "remove_manual_comment"
    CREATE_MANUAL_REPRESENTATION = "create_manual_representation"
    REMOVE_MANUAL_REPRESENTATION = "remove_manual_representation"
    CREATE_MANUAL_SEMANTIC_HINT = "create_manual_semantic_hint"
    REMOVE_MANUAL_SEMANTIC_HINT = "remove_manual_semantic_hint"
    SUPPRESS_SEEDED_ITEM = "suppress_seeded_item"
    CREATE_MANUAL_TARGET_EQUATE = "create_manual_target_equate"
    RENAME_MANUAL_TARGET_EQUATE = "rename_manual_target_equate"
    REMOVE_MANUAL_TARGET_EQUATE = "remove_manual_target_equate"
    CREATE_MANUAL_CUSTOM_STRUCT = "create_manual_custom_struct"
    RENAME_MANUAL_CUSTOM_STRUCT = "rename_manual_custom_struct"
    REMOVE_MANUAL_CUSTOM_STRUCT = "remove_manual_custom_struct"
    CREATE_MANUAL_CUSTOM_STRUCT_FIELD = "create_manual_custom_struct_field"
    RENAME_MANUAL_CUSTOM_STRUCT_FIELD = "rename_manual_custom_struct_field"
    REMOVE_MANUAL_CUSTOM_STRUCT_FIELD = "remove_manual_custom_struct_field"
    CREATE_MANUAL_RSSET_LAYOUT_REGION = "create_manual_rsset_layout_region"
    REMOVE_MANUAL_RSSET_LAYOUT_REGION = "remove_manual_rsset_layout_region"
    CREATE_MANUAL_RSSET_USE_SITE_BINDING = "create_manual_rsset_use_site_binding"
    REMOVE_MANUAL_RSSET_USE_SITE_BINDING = "remove_manual_rsset_use_site_binding"
    CREATE_MANUAL_EXECUTION_VIEW = "create_manual_execution_view"
    REMOVE_MANUAL_EXECUTION_VIEW = "remove_manual_execution_view"
    ADD_REVIEW_NOTE = "add_review_note"
    EDIT_REVIEW_NOTE = "edit_review_note"
    CLEAR_REVIEW_NOTE = "clear_review_note"
    RESOLVE_REVIEW_ITEM = "resolve_review_item"
    UNDO_ACTION = "undo_action"
    REDO_ACTION = "redo_action"


def manual_action_kind(value: str) -> ManualActionKind:
    try:
        return ManualActionKind(value)
    except ValueError:
        raise ValueError(f"Unsupported manual action kind: {value}") from None


@dataclass(frozen=True, slots=True)
class ManualActionLogProjection:
    review_state: ReviewState
    log_path: str
    pinned_target_identity: dict[str, object] | None
    current_target_identity: dict[str, object] | None
    seeds: tuple[dict[str, object], ...]
    register_seeds: tuple[dict[str, object], ...]
    labels: tuple[dict[str, object], ...]
    comments: tuple[dict[str, object], ...]
    representations: tuple[dict[str, object], ...]
    semantic_hints: tuple[dict[str, object], ...]
    suppressed_seeded_items: tuple[dict[str, object], ...]
    target_equates: tuple[dict[str, object], ...]
    renamed_target_equates: tuple[dict[str, object], ...]
    removed_target_equates: tuple[dict[str, object], ...]
    custom_structs: tuple[dict[str, object], ...]
    renamed_custom_structs: tuple[dict[str, object], ...]
    removed_custom_structs: tuple[dict[str, object], ...]
    custom_struct_fields: tuple[dict[str, object], ...]
    renamed_custom_struct_fields: tuple[dict[str, object], ...]
    removed_custom_struct_fields: tuple[dict[str, object], ...]
    rsset_layout_regions: tuple[dict[str, object], ...]
    removed_rsset_layout_regions: tuple[dict[str, object], ...]
    rsset_use_site_bindings: tuple[dict[str, object], ...]
    removed_rsset_use_site_bindings: tuple[dict[str, object], ...]
    execution_views: tuple[dict[str, object], ...]
    removed_execution_views: tuple[dict[str, object], ...]
    review_notes: tuple[dict[str, object], ...]
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
    kind: ManualActionKind,
    payload: dict[str, object],
    binary_source: BinarySource,
) -> dict[str, object]:
    if not isinstance(kind, ManualActionKind):
        raise TypeError("kind must be a ManualActionKind")
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
        "kind": kind,
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
        register_seeds=(),
        labels=(),
        comments=(),
        representations=(),
        semantic_hints=(),
        suppressed_seeded_items=(),
        target_equates=(),
        renamed_target_equates=(),
        removed_target_equates=(),
        custom_structs=(),
        renamed_custom_structs=(),
        removed_custom_structs=(),
        custom_struct_fields=(),
        renamed_custom_struct_fields=(),
        removed_custom_struct_fields=(),
        rsset_layout_regions=(),
        removed_rsset_layout_regions=(),
        rsset_use_site_bindings=(),
        removed_rsset_use_site_bindings=(),
        execution_views=(),
        removed_execution_views=(),
        review_notes=(),
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
    if scope == ReviewItemScope.RANGE:
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
    kind = item.get("kind")
    if not isinstance(kind, ReviewItemKind):
        raise TypeError("review item kind must be a ReviewItemKind")
    if kind is ReviewItemKind.MANUAL_SEED_CONFLICT:
        return [
            {
                "action": SuggestedReviewActionKind.NAVIGATE,
                "scope": item.get("scope"),
                "hunk": item.get("hunk"),
                "addr": item.get("start"),
            },
            {"action": SuggestedReviewActionKind.EDIT_MANUAL_SEED, "seed_ids": item.get("seed_ids")},
        ]
    if kind in {
        ReviewItemKind.MANUAL_ACTION_LOG_INCONSISTENCY,
        ReviewItemKind.MANUAL_ACTION_LOG_MALFORMED,
        ReviewItemKind.MANUAL_ACTION_LOG_TARGET_MISMATCH,
    }:
        return [{"action": SuggestedReviewActionKind.REPAIR_MANUAL_ACTION_LOG}]
    if kind in {ReviewItemKind.REPRODUCTION_MISMATCH, ReviewItemKind.UNSUPPORTED_CONTAINER_SHAPE}:
        return [
            {"action": SuggestedReviewActionKind.OPEN_REPRODUCTION_REPORT},
            {"action": SuggestedReviewActionKind.RERUN_ROUND_TRIP_VERIFICATION},
        ]
    if kind is ReviewItemKind.ORPHAN_CODE_CANDIDATE:
        return [
            {
                "action": SuggestedReviewActionKind.NAVIGATE,
                "scope": item.get("scope"),
                "hunk": item.get("hunk"),
                "addr": item.get("start"),
            },
            {
                "action": SuggestedReviewActionKind.CREATE_MANUAL_SEED,
                "seed_kind": ManualSeedKind.CODE,
                "mode": ManualSeedMode.REQUIRED,
            },
            {"action": SuggestedReviewActionKind.RESOLVE_AS_DATA_OR_PADDING},
        ]
    if kind is ReviewItemKind.UNRECONCILED_DATA_RANGE:
        return [
            {
                "action": SuggestedReviewActionKind.NAVIGATE,
                "scope": item.get("scope"),
                "hunk": item.get("hunk"),
                "addr": item.get("start"),
            },
            {
                "action": SuggestedReviewActionKind.CREATE_MANUAL_SEED,
                "seed_kind": ManualSeedKind.DATA,
                "mode": ManualSeedMode.REQUIRED,
            },
            {"action": SuggestedReviewActionKind.RESOLVE_AS_OPAQUE_DATA},
        ]
    if kind is ReviewItemKind.SUSPICIOUS_INSTRUCTION_DECODE:
        return [
            {
                "action": SuggestedReviewActionKind.NAVIGATE,
                "scope": item.get("scope"),
                "hunk": item.get("hunk"),
                "addr": item.get("start"),
            },
            {
                "action": SuggestedReviewActionKind.CREATE_MANUAL_SEED,
                "seed_kind": ManualSeedKind.DATA,
                "mode": ManualSeedMode.REQUIRED,
            },
            {"action": SuggestedReviewActionKind.ACKNOWLEDGE},
        ]
    if kind in {ReviewItemKind.MANUAL_LABEL_UNRECONCILED, ReviewItemKind.MANUAL_COMMENT_UNRECONCILED}:
        return [
            {
                "action": SuggestedReviewActionKind.NAVIGATE,
                "scope": item.get("scope"),
                "hunk": item.get("hunk"),
                "addr": item.get("start"),
            },
            {"action": SuggestedReviewActionKind.CREATE_MANUAL_SEED, "mode": ManualSeedMode.REQUIRED},
            {"action": SuggestedReviewActionKind.REMOVE_MANUAL_ANNOTATION},
            {"action": SuggestedReviewActionKind.ACKNOWLEDGE},
        ]
    if kind is ReviewItemKind.REVIEW_NOTE:
        return [
            {
                "action": SuggestedReviewActionKind.NAVIGATE,
                "scope": item.get("scope"),
                "hunk": item.get("hunk"),
                "addr": item.get("start"),
            },
            {"action": SuggestedReviewActionKind.ACKNOWLEDGE},
        ]
    if kind is ReviewItemKind.LABEL_SCOPE_CONFLICT:
        return [
            {"action": SuggestedReviewActionKind.RENAME_MANUAL_LABEL},
            {"action": SuggestedReviewActionKind.CHANGE_LABEL_SCOPE},
            {"action": SuggestedReviewActionKind.REMOVE_MANUAL_LABEL},
        ]
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
        "scope": ReviewItemScope.TARGET,
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
    return {
        "kind": kind,
        "scope": ReviewItemScope.TARGET,
        "state": ReviewItemState.OPEN,
        "message": message,
    }


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
    if mode is None:
        return True
    if not isinstance(mode, ManualSeedMode):
        raise TypeError("manual seed mode must be a ManualSeedMode")
    return mode is ManualSeedMode.REQUIRED


def _metadata_global_label_names(metadata: TargetMetadata | None) -> set[str]:
    if metadata is None:
        return set()
    names: set[str] = set()
    for code_label in metadata.seeded_code_labels:
        names.add(code_label.name)
    for absolute_label in metadata.absolute_code_labels:
        names.add(absolute_label.name)
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
        raw_scope = label.get("scope")
        if raw_scope is not None and not isinstance(raw_scope, ManualLabelScope):
            raise TypeError("manual label scope must be a ManualLabelScope")
        scope = raw_scope if raw_scope is not None else ManualLabelScope.GLOBAL
        if not isinstance(label_id, str) or not isinstance(name, str):
            continue
        label_range = _manual_seed_range(label)
        if scope is ManualLabelScope.LOCAL:
            owner_id = label.get("owner_id") or label.get("owner_label_id")
            hunk, start, end = label_range or (0, 0, 1)
            if not isinstance(owner_id, str) or not owner_id:
                items.append(
                    {
                        "kind": ReviewItemKind.LABEL_SCOPE_CONFLICT,
                        "item_id": f"label_scope_conflict:{label_id}:missing-owner",
                        "scope": ReviewItemScope.RANGE,
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
                        "scope": ReviewItemScope.RANGE,
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
                        "scope": ReviewItemScope.RANGE,
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
        if scope is not ManualLabelScope.GLOBAL:
            continue
        if name in metadata_names:
            hunk, start, end = label_range or (0, 0, 1)
            items.append(
                {
                    "kind": ReviewItemKind.LABEL_SCOPE_CONFLICT,
                    "item_id": f"label_scope_conflict:{label_id}:metadata-collision",
                    "scope": ReviewItemScope.RANGE,
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
                "scope": ReviewItemScope.RANGE,
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
        if not isinstance(left_id, str) or not isinstance(left_kind, ManualSeedKind) or left_range is None:
            continue
        if not _manual_seed_required(left):
            continue
        for right in values[left_index + 1:]:
            right_id = right.get("seed_id")
            right_kind = right.get("kind")
            right_range = _manual_seed_range(right)
            if not isinstance(right_id, str) or not isinstance(right_kind, ManualSeedKind) or right_range is None:
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
                    "scope": ReviewItemScope.RANGE,
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
    stronger_ranges: list[tuple[ManualSeedKind, str, int, int, int, str | None]] = []
    for entrypoint in metadata.seeded_code_entrypoints:
        stronger_id = f"seeded_code_entrypoint:h{entrypoint.hunk}:${entrypoint.addr:08x}"
        stronger_ranges.append((
            ManualSeedKind.CODE,
            stronger_id,
            entrypoint.hunk,
            entrypoint.addr,
            entrypoint.addr + 1,
            entrypoint.name,
        ))
    for entity in metadata.seeded_entities:
        end = entity.end if entity.end is not None and entity.end > entity.addr else entity.addr + 1
        stronger_id = f"seeded_entity:h{entity.hunk}:${entity.addr:08x}"
        stronger_ranges.append((ManualSeedKind.DATA, stronger_id, entity.hunk, entity.addr, end, entity.name))

    for seed in seeds.values():
        seed_id = seed.get("seed_id")
        seed_kind = seed.get("kind")
        seed_range = _manual_seed_range(seed)
        if not isinstance(seed_id, str) or not isinstance(seed_kind, ManualSeedKind) or seed_range is None:
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
                    "scope": ReviewItemScope.RANGE,
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
        if not isinstance(seed_id, str) or seed_kind is not ManualSeedKind.DATA or seed_range is None:
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
                "scope": ReviewItemScope.RANGE,
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "seed_ids": [seed_id],
                "stronger_kind": ManualSeedKind.CODE,
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
    kind = manual_action_kind(_str_field(raw, "kind", what="manual action"))
    return _ManualAction(
        action_id=action_id,
        sequence=sequence,
        created_at=created_at,
        kind=kind,
        payload=dict(raw),
    )


def _action_object(action: _ManualAction, field_name: str) -> dict[str, object]:
    return _object(action.payload.get(field_name), what=f"{action.kind} {field_name}")


def _suppressed_seeded_item_key(item: dict[str, object]) -> tuple[str, int, int]:
    kind = item.get("kind")
    hunk = _manual_seed_int(item, "hunk")
    addr = _manual_seed_int(item, "addr")
    if not isinstance(kind, str) or hunk is None or addr is None:
        raise ValueError("suppressed_seeded_item requires kind, hunk, and addr")
    try:
        SuppressedSeededItemKind(kind)
    except ValueError:
        raise ValueError(f"unsupported suppressed seeded item kind: {kind}") from None
    return kind, hunk, addr


def _execution_view_key(view: dict[str, object]) -> tuple[int, int, int]:
    source_start = _manual_seed_int(view, "source_start")
    source_end = _manual_seed_int(view, "source_end")
    base_addr = _manual_seed_int(view, "base_addr")
    if source_start is None or source_end is None or base_addr is None:
        raise ValueError("execution_view requires source_start, source_end, and base_addr")
    if source_start < 0 or source_end <= source_start or base_addr < 0:
        raise ValueError("execution_view has invalid source/runtime range")
    return source_start, source_end, base_addr


def _rsset_layout_region_key(region: dict[str, object]) -> tuple[str, str, int]:
    offset = _manual_seed_int(region, "offset")
    if offset is None or offset < 0:
        raise ValueError("rsset_layout_region requires offset")
    layout_name = region.get("layout_name")
    base_symbol = region.get("base_symbol")
    return (
        layout_name if isinstance(layout_name, str) and layout_name else "app",
        base_symbol if isinstance(base_symbol, str) and base_symbol else "__amiga_app_base__",
        offset,
    )


def _rsset_use_site_binding_key(binding: dict[str, object]) -> str:
    binding_id = binding.get("rsset_use_site_binding_id")
    if isinstance(binding_id, str) and binding_id:
        return binding_id
    hunk = _manual_seed_int(binding, "hunk")
    addr = _manual_seed_int(binding, "addr")
    operand_index = _manual_seed_int(binding, "operand_index")
    displacement = _manual_seed_int(binding, "displacement")
    base_register = binding.get("base_register")
    layout_name = binding.get("layout_name")
    base_symbol = binding.get("base_symbol")
    base_evidence_id = binding.get("base_evidence_id")
    if (
        hunk is None
        or addr is None
        or operand_index is None
        or displacement is None
        or not isinstance(base_register, str)
        or not base_register
    ):
        raise ValueError("rsset_use_site_binding requires binding id or hunk, addr, operand_index, base_register, and displacement")
    layout = layout_name if isinstance(layout_name, str) and layout_name else "app"
    base = base_symbol if isinstance(base_symbol, str) and base_symbol else "__amiga_app_base__"
    evidence = base_evidence_id if isinstance(base_evidence_id, str) and base_evidence_id else f"selected-base:{base_register.upper()}:{base}"
    return f"h{hunk}:{addr:08X}:op{operand_index}:{base_register.upper()}:{displacement:04X}:{layout}:{base}:{evidence}"


def _custom_struct_field_key(field: dict[str, object]) -> tuple[str, int]:
    struct_name = field.get("struct_name")
    offset = _manual_seed_int(field, "offset")
    if not isinstance(struct_name, str) or not struct_name:
        raise ValueError("custom_struct_field requires struct_name")
    if offset is None or offset < 0:
        raise ValueError("custom_struct_field requires offset")
    return struct_name, offset


def _custom_struct_rename_names(custom_struct: dict[str, object]) -> tuple[str, str]:
    previous_name = custom_struct.get("previous_name")
    name = custom_struct.get("name")
    if not isinstance(previous_name, str) or not previous_name:
        raise ValueError("custom_struct rename requires previous_name")
    if not isinstance(name, str) or not name:
        raise ValueError("custom_struct rename requires name")
    return previous_name, name


def _target_equate_rename_names(equate: dict[str, object]) -> tuple[str, str]:
    previous_name = equate.get("previous_name")
    name = equate.get("name")
    if not isinstance(previous_name, str) or not previous_name:
        raise ValueError("target_equate rename requires previous_name")
    if not isinstance(name, str) or not name:
        raise ValueError("target_equate rename requires name")
    return previous_name, name


def _data_symbol_seed_id(symbol: Mapping[str, object]) -> str:
    hunk = _manual_seed_int(symbol, "hunk")
    addr = _manual_seed_int(symbol, "addr")
    if hunk is None or addr is None:
        raise ValueError("data_symbol requires hunk and addr")
    return f"data-symbol:h{hunk}:{addr:08X}"


def _projected_data_symbol_seed(action: _ManualAction) -> dict[str, object]:
    symbol = dict(_action_object(action, "data_symbol"))
    hunk = _manual_seed_int(symbol, "hunk")
    addr = _manual_seed_int(symbol, "addr")
    end = _manual_seed_int(symbol, "end")
    name = symbol.get("name")
    if hunk is None or addr is None:
        raise ValueError("data_symbol requires hunk and addr")
    if end is not None and end <= addr:
        raise ValueError("data_symbol end must be greater than addr")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("data_symbol requires name")
    seed: dict[str, object] = {
        "seed_id": str(symbol.get("data_symbol_id") or _data_symbol_seed_id(symbol)),
        "kind": ManualSeedKind.DATA,
        "hunk": hunk,
        "addr": addr,
        "name": name.strip(),
    }
    if end is not None:
        seed["end"] = end
    return seed


def _projected_manual_seed(action: _ManualAction) -> dict[str, object]:
    seed = dict(_action_object(action, "seed"))
    seed_kind = _manual_seed_kind_from_json(seed.get("kind"))
    if seed_kind is None:
        raise ValueError(f"{action.kind} seed kind must be code or data")
    seed["kind"] = seed_kind
    raw_mode = seed.get("mode")
    if raw_mode is not None:
        seed_mode = _manual_seed_mode_from_json(raw_mode)
        if seed_mode is None:
            raise ValueError(f"{action.kind} seed mode must be required")
        seed["mode"] = seed_mode
    return seed


def _projected_manual_label(action: _ManualAction) -> dict[str, object]:
    label = dict(_action_object(action, "label"))
    raw_scope = label.get("scope")
    if raw_scope is not None:
        scope = _manual_label_scope_from_json(raw_scope)
        if scope is None:
            raise ValueError(f"{action.kind} label scope must be global or local")
        label["scope"] = scope
    return label


def _rename_manual_label(labels: dict[str, dict[str, object]], action: _ManualAction) -> None:
    label_id = _action_ref(action, "label_id")
    name = _action_ref(action, "name")
    label = labels.get(label_id)
    if label is None:
        return
    updated = dict(label)
    updated["name"] = name
    labels[label_id] = updated


def _change_manual_label_scope(labels: dict[str, dict[str, object]], action: _ManualAction) -> None:
    label_id = _action_ref(action, "label_id")
    raw_scope = action.payload.get("scope")
    scope = _manual_label_scope_from_json(raw_scope)
    if scope is None:
        raise ValueError(f"{action.kind} scope must be global or local")
    label = labels.get(label_id)
    if label is None:
        return
    updated = dict(label)
    updated["scope"] = scope
    if scope is ManualLabelScope.GLOBAL:
        updated.pop("owner_id", None)
        updated.pop("owner_label_id", None)
    else:
        owner_id = action.payload.get("owner_id") or action.payload.get("owner_label_id")
        if isinstance(owner_id, str) and owner_id:
            updated["owner_id"] = owner_id
    labels[label_id] = updated


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


def _review_note_from_action(action: _ManualAction) -> dict[str, object]:
    note = _action_object(action, "note")
    tracking = note.get("tracking")
    if tracking not in {"note_only", "needs_review"}:
        note["tracking"] = "note_only"
    if "title" not in note:
        note["title"] = ""
    if "body" not in note:
        note["body"] = ""
    return note


def _edit_review_note(notes: dict[str, dict[str, object]], action: _ManualAction) -> None:
    note_id = _action_ref(action, "note_id")
    existing = notes.get(note_id)
    if existing is None:
        return
    updated = dict(existing)
    for field_name in ("title", "body", "tracking"):
        if field_name in action.payload:
            updated[field_name] = action.payload[field_name]
    if updated.get("tracking") not in {"note_only", "needs_review"}:
        updated["tracking"] = "note_only"
    notes[note_id] = updated


def _review_note_item(note: dict[str, object]) -> dict[str, object] | None:
    if note.get("tracking") != "needs_review":
        return None
    note_id = note.get("note_id")
    if not isinstance(note_id, str) or not note_id:
        return None
    addr = _manual_seed_int(note, "addr")
    end = _manual_seed_int(note, "end")
    title = str(note.get("title") or "").strip()
    body = str(note.get("body") or "").strip()
    message = title or body or "Review note"
    item: dict[str, object] = {
        "kind": ReviewItemKind.REVIEW_NOTE,
        "scope": ReviewItemScope.RANGE if addr is not None else ReviewItemScope.TARGET,
        "state": ReviewItemState.OPEN,
        "review_blocker": False,
        "source": "review_note",
        "note_id": note_id,
        "title": title,
        "body": body,
        "message": message,
    }
    hunk = _manual_seed_int(note, "hunk")
    if hunk is not None:
        item["hunk"] = hunk
    if addr is not None:
        item["start"] = addr
        item["addr"] = addr
        item["end"] = end if end is not None and end > addr else addr + 1
    else:
        item["stale_location_reason"] = "unresolved_location"
    row_indexes = note.get("row_indexes")
    if isinstance(row_indexes, list):
        item["row_indexes"] = [value for value in row_indexes if isinstance(value, int) and not isinstance(value, bool)]
    return item


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
    register_seeds: dict[str, dict[str, object]] = {}
    labels: dict[str, dict[str, object]] = {}
    comments: dict[str, dict[str, object]] = {}
    representations: dict[str, dict[str, object]] = {}
    semantic_hints: dict[str, dict[str, object]] = {}
    suppressed_seeded_items: dict[tuple[str, int, int], dict[str, object]] = {}
    target_equates: dict[str, dict[str, object]] = {}
    renamed_target_equates: dict[str, dict[str, object]] = {}
    removed_target_equates: dict[str, dict[str, object]] = {}
    custom_structs: dict[str, dict[str, object]] = {}
    renamed_custom_structs: dict[str, dict[str, object]] = {}
    removed_custom_structs: dict[str, dict[str, object]] = {}
    custom_struct_fields: dict[tuple[str, int], dict[str, object]] = {}
    renamed_custom_struct_fields: dict[tuple[str, int], dict[str, object]] = {}
    removed_custom_struct_fields: dict[tuple[str, int], dict[str, object]] = {}
    rsset_layout_regions: dict[tuple[str, str, int], dict[str, object]] = {}
    removed_rsset_layout_regions: dict[tuple[str, str, int], dict[str, object]] = {}
    rsset_use_site_bindings: dict[str, dict[str, object]] = {}
    removed_rsset_use_site_bindings: dict[str, dict[str, object]] = {}
    execution_views: dict[tuple[int, int, int], dict[str, object]] = {}
    removed_execution_views: dict[tuple[int, int, int], dict[str, object]] = {}
    review_notes: dict[str, dict[str, object]] = {}
    resolutions: dict[str, dict[str, object]] = {}
    active_action_ids: list[str] = []
    inactive_action_ids: list[str] = []

    for action in actions:
        if action.action_id in undone_action_ids:
            inactive_action_ids.append(action.action_id)
            continue
        active_action_ids.append(action.action_id)
        if action.kind is ManualActionKind.CREATE_MANUAL_SEED:
            _put_by_id(seeds, _projected_manual_seed(action), "seed_id")
        elif action.kind is ManualActionKind.REMOVE_MANUAL_SEED:
            _drop_by_id(seeds, action, "seed_id")
        elif action.kind is ManualActionKind.RENAME_DATA_SYMBOL:
            _put_by_id(seeds, _projected_data_symbol_seed(action), "seed_id")
        elif action.kind is ManualActionKind.CREATE_MANUAL_REGISTER_SEED:
            _put_by_id(register_seeds, _action_object(action, "register_seed"), "register_seed_id")
        elif action.kind is ManualActionKind.REMOVE_MANUAL_REGISTER_SEED:
            _drop_by_id(register_seeds, action, "register_seed_id")
        elif action.kind is ManualActionKind.CREATE_MANUAL_LABEL:
            _put_by_id(labels, _projected_manual_label(action), "label_id")
        elif action.kind is ManualActionKind.REMOVE_MANUAL_LABEL:
            _drop_by_id(labels, action, "label_id")
        elif action.kind is ManualActionKind.RENAME_MANUAL_LABEL:
            _rename_manual_label(labels, action)
        elif action.kind is ManualActionKind.CHANGE_LABEL_SCOPE:
            _change_manual_label_scope(labels, action)
        elif action.kind is ManualActionKind.CREATE_MANUAL_COMMENT:
            _put_by_id(comments, _action_object(action, "comment"), "comment_id")
        elif action.kind is ManualActionKind.REMOVE_MANUAL_COMMENT:
            _drop_by_id(comments, action, "comment_id")
        elif action.kind is ManualActionKind.CREATE_MANUAL_REPRESENTATION:
            _put_by_id(representations, _action_object(action, "representation"), "representation_id")
        elif action.kind is ManualActionKind.REMOVE_MANUAL_REPRESENTATION:
            _drop_by_id(representations, action, "representation_id")
        elif action.kind is ManualActionKind.CREATE_MANUAL_SEMANTIC_HINT:
            _put_by_id(semantic_hints, _action_object(action, "semantic_hint"), "semantic_hint_id")
        elif action.kind is ManualActionKind.REMOVE_MANUAL_SEMANTIC_HINT:
            _drop_by_id(semantic_hints, action, "semantic_hint_id")
        elif action.kind is ManualActionKind.SUPPRESS_SEEDED_ITEM:
            item = _action_object(action, "suppressed_seeded_item")
            suppressed_seeded_items[_suppressed_seeded_item_key(item)] = item
        elif action.kind is ManualActionKind.CREATE_MANUAL_TARGET_EQUATE:
            equate = _action_object(action, "target_equate")
            _put_by_id(target_equates, equate, "name")
            removed_target_equates.pop(str(equate["name"]), None)
        elif action.kind is ManualActionKind.RENAME_MANUAL_TARGET_EQUATE:
            equate = _action_object(action, "target_equate")
            previous_name, name = _target_equate_rename_names(equate)
            existing = target_equates.pop(previous_name, None)
            if existing is not None:
                updated = dict(existing)
                updated["name"] = name
                target_equates[name] = updated
            renamed_target_equates[previous_name] = equate
        elif action.kind is ManualActionKind.REMOVE_MANUAL_TARGET_EQUATE:
            equate = _action_object(action, "target_equate")
            name = equate.get("name")
            if not isinstance(name, str):
                raise ValueError("target_equate requires name")
            target_equates.pop(name, None)
            removed_target_equates[name] = equate
        elif action.kind is ManualActionKind.CREATE_MANUAL_CUSTOM_STRUCT:
            custom_struct = _action_object(action, "custom_struct")
            _put_by_id(custom_structs, custom_struct, "name")
            removed_custom_structs.pop(str(custom_struct["name"]), None)
        elif action.kind is ManualActionKind.RENAME_MANUAL_CUSTOM_STRUCT:
            custom_struct = _action_object(action, "custom_struct")
            previous_name, name = _custom_struct_rename_names(custom_struct)
            existing = custom_structs.pop(previous_name, None)
            if existing is not None:
                updated = dict(existing)
                updated["name"] = name
                custom_structs[name] = updated
            renamed_custom_structs[previous_name] = custom_struct
        elif action.kind is ManualActionKind.REMOVE_MANUAL_CUSTOM_STRUCT:
            custom_struct = _action_object(action, "custom_struct")
            struct_name = custom_struct.get("name")
            if not isinstance(struct_name, str):
                raise ValueError("custom_struct requires name")
            custom_structs.pop(struct_name, None)
            removed_custom_structs[struct_name] = custom_struct
        elif action.kind is ManualActionKind.CREATE_MANUAL_CUSTOM_STRUCT_FIELD:
            field = _action_object(action, "custom_struct_field")
            key = _custom_struct_field_key(field)
            removed_custom_struct_fields.pop(key, None)
            custom_struct_fields[key] = field
        elif action.kind is ManualActionKind.RENAME_MANUAL_CUSTOM_STRUCT_FIELD:
            field = _action_object(action, "custom_struct_field")
            key = _custom_struct_field_key(field)
            name = field.get("name")
            if not isinstance(name, str) or not name:
                raise ValueError("custom_struct_field rename requires name")
            existing = custom_struct_fields.get(key)
            if existing is not None:
                updated = dict(existing)
                updated["name"] = name
                custom_struct_fields[key] = updated
            renamed_custom_struct_fields[key] = field
        elif action.kind is ManualActionKind.REMOVE_MANUAL_CUSTOM_STRUCT_FIELD:
            field = _action_object(action, "custom_struct_field")
            key = _custom_struct_field_key(field)
            custom_struct_fields.pop(key, None)
            removed_custom_struct_fields[key] = field
        elif action.kind is ManualActionKind.CREATE_MANUAL_RSSET_LAYOUT_REGION:
            region = _action_object(action, "rsset_layout_region")
            key = _rsset_layout_region_key(region)
            removed_rsset_layout_regions.pop(key, None)
            rsset_layout_regions[key] = region
        elif action.kind is ManualActionKind.REMOVE_MANUAL_RSSET_LAYOUT_REGION:
            region = _action_object(action, "rsset_layout_region")
            key = _rsset_layout_region_key(region)
            rsset_layout_regions.pop(key, None)
            removed_rsset_layout_regions[key] = region
        elif action.kind is ManualActionKind.CREATE_MANUAL_RSSET_USE_SITE_BINDING:
            binding = _action_object(action, "rsset_use_site_binding")
            key = _rsset_use_site_binding_key(binding)
            binding = dict(binding)
            binding.setdefault("rsset_use_site_binding_id", key)
            binding["owner_action_id"] = action.action_id
            removed_rsset_use_site_bindings.pop(key, None)
            rsset_use_site_bindings[key] = binding
        elif action.kind is ManualActionKind.REMOVE_MANUAL_RSSET_USE_SITE_BINDING:
            binding = _action_object(action, "rsset_use_site_binding")
            key = _rsset_use_site_binding_key(binding)
            binding = dict(binding)
            binding.setdefault("rsset_use_site_binding_id", key)
            binding["cleanup_action_id"] = action.action_id
            rsset_use_site_bindings.pop(key, None)
            removed_rsset_use_site_bindings[key] = binding
        elif action.kind is ManualActionKind.CREATE_MANUAL_EXECUTION_VIEW:
            view = _action_object(action, "execution_view")
            key = _execution_view_key(view)
            removed_execution_views.pop(key, None)
            execution_views[key] = view
        elif action.kind is ManualActionKind.REMOVE_MANUAL_EXECUTION_VIEW:
            view = _action_object(action, "execution_view")
            key = _execution_view_key(view)
            execution_views.pop(key, None)
            removed_execution_views[key] = view
        elif action.kind is ManualActionKind.ADD_REVIEW_NOTE:
            _put_by_id(review_notes, _review_note_from_action(action), "note_id")
        elif action.kind is ManualActionKind.EDIT_REVIEW_NOTE:
            _edit_review_note(review_notes, action)
        elif action.kind is ManualActionKind.CLEAR_REVIEW_NOTE:
            _drop_by_id(review_notes, action, "note_id")
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
    review_items.extend(
        item for note in review_notes.values() if (item := _review_note_item(note)) is not None
    )
    finalized_review_items = _finalize_review_items(review_items, tuple(resolutions.values()))
    review_state = _review_state_for_items(finalized_review_items)
    return ManualActionLogProjection(
        review_state=review_state,
        log_path=str(path),
        pinned_target_identity=pinned_target_identity,
        current_target_identity=current_target_identity,
        seeds=tuple(seeds.values()),
        register_seeds=tuple(register_seeds.values()),
        labels=tuple(labels.values()),
        comments=tuple(comments.values()),
        representations=tuple(representations.values()),
        semantic_hints=tuple(semantic_hints.values()),
        suppressed_seeded_items=tuple(suppressed_seeded_items.values()),
        target_equates=tuple(target_equates.values()),
        renamed_target_equates=tuple(renamed_target_equates.values()),
        removed_target_equates=tuple(removed_target_equates.values()),
        custom_structs=tuple(custom_structs.values()),
        renamed_custom_structs=tuple(renamed_custom_structs.values()),
        removed_custom_structs=tuple(removed_custom_structs.values()),
        custom_struct_fields=tuple(custom_struct_fields.values()),
        renamed_custom_struct_fields=tuple(renamed_custom_struct_fields.values()),
        removed_custom_struct_fields=tuple(removed_custom_struct_fields.values()),
        rsset_layout_regions=tuple(rsset_layout_regions.values()),
        removed_rsset_layout_regions=tuple(removed_rsset_layout_regions.values()),
        rsset_use_site_bindings=tuple(rsset_use_site_bindings.values()),
        removed_rsset_use_site_bindings=tuple(removed_rsset_use_site_bindings.values()),
        execution_views=tuple(execution_views.values()),
        removed_execution_views=tuple(removed_execution_views.values()),
        review_notes=tuple(review_notes.values()),
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
