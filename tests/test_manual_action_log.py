from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    ManualActionKind,
    append_manual_action,
    build_target_identity,
    load_manual_projection,
)
from amiga_reversing.disasm.target_metadata import (
    SeededCodeEntrypointMetadata,
    SeededCodeLabelMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
)


def _write_raw_source(target_dir: Path, binary_path: Path, payload: bytes = b"\x4e\x75") -> None:
    binary_path.write_bytes(payload)
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": str(binary_path),
                "load_address": 0x70000,
                "entrypoint": 0x70000,
                "code_start_offset": 0,
            }
        ),
        encoding="utf-8",
    )


def _append_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _action(action_id: str, sequence: int, kind: str, **fields: object) -> dict[str, object]:
    return {
        "record": "manual_action",
        "action_id": action_id,
        "sequence": sequence,
        "created_at": f"2026-05-13T00:00:0{sequence}+00:00",
        "kind": kind,
        **fields,
    }


def _assert_review_item_includes(item: dict[str, object], expected: dict[str, object]) -> None:
    for key, value in expected.items():
        assert item.get(key) == value
    assert isinstance(item.get("evidence_fingerprint"), str)
    assert len(str(item["evidence_fingerprint"])) == 64
    assert item.get("review_confidence") == "high"
    assert isinstance(item.get("suggested_actions"), list)


def test_missing_manual_action_log_projects_empty_state(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "clear"
    assert projection.seeds == ()
    assert projection.labels == ()
    assert projection.comments == ()
    assert projection.representations == ()
    assert projection.resolutions == ()
    assert projection.active_action_ids == ()
    assert projection.inactive_action_ids == ()


def test_header_only_manual_action_log_pins_target_identity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    identity = {"schema_version": 1, "source_kind": "raw_binary", "original_sha256": "abc"}
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [{"record": "manual_action_log_header", "version": 1, "target_identity": identity}],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "clear"
    assert projection.pinned_target_identity == identity
    assert projection.seeds == ()


def test_manual_representation_actions_project_without_manual_seed(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    log_path = target_dir / MANUAL_ACTION_LOG_FILE_NAME
    _append_jsonl(
        log_path,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_representation",
                representation={
                    "representation_id": "repr-1",
                    "hunk": 0,
                    "addr": 4,
                    "end": 5,
                    "element_kind": "literal",
                    "style": "character",
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "clear"
    assert projection.seeds == ()
    assert projection.representations == (
        {
            "representation_id": "repr-1",
            "hunk": 0,
            "addr": 4,
            "end": 5,
            "element_kind": "literal",
            "style": "character",
        },
    )


def test_review_note_actions_project_notes_and_review_items(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "add_review_note",
                note={
                    "note_id": "note-1",
                    "target_kind": "row",
                    "title": "Check branch",
                    "body": "Confirm target.",
                    "tracking": "needs_review",
                    "hunk": 0,
                    "addr": 4,
                    "end": 6,
                    "row_indexes": [2],
                },
            ),
            _action("a2", 2, "edit_review_note", note_id="note-1", title="Check branch target"),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "needs_review"
    assert projection.review_notes == (
        {
            "note_id": "note-1",
            "target_kind": "row",
            "title": "Check branch target",
            "body": "Confirm target.",
            "tracking": "needs_review",
            "hunk": 0,
            "addr": 4,
            "end": 6,
            "row_indexes": [2],
        },
    )
    review_item = projection.review_items[0]
    assert review_item["kind"] == "review_note"
    assert review_item["state"] == "open"
    assert review_item["review_blocker"] is False
    assert review_item["note_id"] == "note-1"
    assert review_item["start"] == 4
    assert review_item["end"] == 6


def test_note_only_and_cleared_review_notes_do_not_affect_review_state(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "add_review_note",
                note={"note_id": "note-1", "title": "Bookmark", "tracking": "note_only", "hunk": 0, "addr": 4},
            ),
            _action(
                "a2",
                2,
                "add_review_note",
                note={"note_id": "note-2", "title": "Review", "tracking": "needs_review", "hunk": 0, "addr": 8},
            ),
            _action("a3", 3, "clear_review_note", note_id="note-2"),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "clear"
    assert [note["note_id"] for note in projection.review_notes] == ["note-1"]
    assert projection.review_items == ()


def test_manual_action_log_replays_file_order_and_reports_sequence_inconsistency(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    log_path = target_dir / MANUAL_ACTION_LOG_FILE_NAME
    _append_jsonl(
        log_path,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 2, "create_manual_seed", seed={"seed_id": "s1", "kind": "code"}),
            _action("a2", 1, "create_manual_label", label={"label_id": "l1", "name": "start"}),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "needs_review"
    assert [seed["seed_id"] for seed in projection.seeds] == ["s1"]
    assert [label["label_id"] for label in projection.labels] == ["l1"]
    assert [item["kind"] for item in projection.review_items] == ["manual_action_log_inconsistency"]
    assert projection.active_action_ids == ("a1", "a2")


def test_manual_action_log_remove_manual_seed_projects_seed_absent(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_seed", seed={"seed_id": "data-as-code", "kind": "data", "addr": 0}),
            _action("a2", 2, "remove_manual_seed", seed_id="data-as-code"),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.seeds == ()
    assert projection.review_state == "clear"
    assert projection.active_action_ids == ("a1", "a2")


def test_manual_action_log_undo_and_redo_project_action_activity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_seed", seed={"seed_id": "s1", "kind": "code"}),
            _action("a2", 2, "undo_action", undoes_action_id="a1"),
            _action("a3", 3, "redo_action", redoes_action_id="a1"),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert [seed["seed_id"] for seed in projection.seeds] == ["s1"]
    assert projection.active_action_ids == ("a1", "a2", "a3")
    assert projection.inactive_action_ids == ()

    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_seed", seed={"seed_id": "s1", "kind": "code"}),
            _action("a2", 2, "undo_action", undoes_action_id="a1"),
        ],
    )

    undone_projection = load_manual_projection(target_dir)

    assert undone_projection.seeds == ()
    assert undone_projection.active_action_ids == ("a2",)
    assert undone_projection.inactive_action_ids == ("a1",)


def test_manual_action_log_undo_does_not_affect_future_action(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "undo_action", undoes_action_id="a2"),
            _action("a2", 2, "create_manual_seed", seed={"seed_id": "s1", "kind": "code"}),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert [seed["seed_id"] for seed in projection.seeds] == ["s1"]
    assert projection.active_action_ids == ("a1", "a2")
    assert projection.inactive_action_ids == ()


def test_manual_action_log_redo_before_undo_does_not_restore_later_undo(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_seed", seed={"seed_id": "s1", "kind": "code"}),
            _action("a2", 2, "redo_action", redoes_action_id="a1"),
            _action("a3", 3, "undo_action", undoes_action_id="a1"),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.seeds == ()
    assert projection.active_action_ids == ("a2", "a3")
    assert projection.inactive_action_ids == ("a1",)


def test_manual_action_log_projects_labels_comments_and_resolutions(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_label", label={"label_id": "l1", "name": "start"}),
            _action("a2", 2, "create_manual_comment", comment={"comment_id": "c1", "text": "entry"}),
            _action("a3", 3, "resolve_review_item", resolution={"resolution_id": "r1", "item_id": "i1"}),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.labels == ({"label_id": "l1", "name": "start"},)
    assert projection.comments == ({"comment_id": "c1", "text": "entry"},)
    assert projection.resolutions == ({"resolution_id": "r1", "item_id": "i1"},)


def test_manual_action_log_projects_label_rename_and_scope_change(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={"label_id": "l1", "name": "start", "scope": "global", "hunk": 0, "addr": 4},
            ),
            _action("a2", 2, "rename_manual_label", label_id="l1", name=".loop"),
            _action("a3", 3, "change_label_scope", label_id="l1", scope="local", owner_id="owner"),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.labels == (
        {
            "label_id": "l1",
            "name": ".loop",
            "scope": "local",
            "hunk": 0,
            "addr": 4,
            "owner_id": "owner",
        },
    )


def test_append_manual_action_creates_header_and_sequences_actions(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = target_dir / "binary.bin"
    _write_raw_source(target_dir, binary_path)
    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None

    first = append_manual_action(
        target_dir,
        kind=ManualActionKind.CREATE_MANUAL_SEED,
        payload={"seed": {"seed_id": "s1", "kind": "data", "addr": 0}},
        binary_source=binary_source,
    )
    second = append_manual_action(
        target_dir,
        kind=ManualActionKind.RESOLVE_REVIEW_ITEM,
        payload={"resolution": {"resolution_id": "r1", "item_id": "i1", "evidence_fingerprint": "abc"}},
        binary_source=binary_source,
    )

    projection = load_manual_projection(target_dir, binary_source=binary_source)

    assert first["sequence"] == 1
    assert second["sequence"] == 2
    assert projection.seeds == ({"seed_id": "s1", "kind": "data", "addr": 0},)
    assert projection.resolutions == ({"resolution_id": "r1", "item_id": "i1", "evidence_fingerprint": "abc"},)


def test_append_manual_action_rejects_reserved_payload_fields(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = target_dir / "binary.bin"
    _write_raw_source(target_dir, binary_path)
    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None

    with pytest.raises(ValueError, match="reserved field"):
        append_manual_action(
            target_dir,
            kind=ManualActionKind.CREATE_MANUAL_SEED,
            payload={
                "action_id": "manual-forged",
                "sequence": 99,
                "seed": {"seed_id": "s1", "kind": "data", "addr": 0},
            },
            binary_source=binary_source,
        )

    assert not (target_dir / MANUAL_ACTION_LOG_FILE_NAME).exists()


def test_duplicate_global_manual_labels_create_scope_conflict_review_work(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={"label_id": "l1", "name": "start", "scope": "global", "hunk": 0, "addr": 0},
            ),
            _action(
                "a2",
                2,
                "create_manual_label",
                label={"label_id": "l2", "name": "start", "scope": "global", "hunk": 0, "addr": 4},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "blocked"
    item = projection.review_items[0]
    assert item["kind"] == "label_scope_conflict"
    assert item["review_blocker"] is True
    assert item["label_ids"] == ["l1", "l2"]
    assert item["suggested_actions"] == [
        {"action": "rename_manual_label"},
        {"action": "change_label_scope"},
        {"action": "remove_manual_label"},
    ]


def test_local_manual_label_without_owner_creates_scope_conflict_review_work(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={"label_id": "l1", "name": ".loop", "scope": "local", "hunk": 0, "addr": 4},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "blocked"
    item = projection.review_items[0]
    assert item["kind"] == "label_scope_conflict"
    assert item["item_id"] == "label_scope_conflict:l1:missing-owner"
    assert item["review_blocker"] is True


def test_local_manual_label_with_owner_is_allowed_by_vasm_profile(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={
                    "label_id": "l1",
                    "name": ".loop",
                    "scope": "local",
                    "owner_id": "global:start",
                    "hunk": 0,
                    "addr": 4,
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir, assembler_profile=load_assembler_profile("vasm"))

    assert projection.review_state == "clear"
    assert projection.review_items == ()


def test_local_manual_label_rejected_when_profile_requires_unimplemented_mode_flags(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={
                    "label_id": "l1",
                    "name": ".loop",
                    "scope": "local",
                    "owner_id": "global:start",
                    "hunk": 0,
                    "addr": 4,
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir, assembler_profile=load_assembler_profile("devpac"))

    assert projection.review_state == "blocked"
    item = projection.review_items[0]
    assert item["kind"] == "label_scope_conflict"
    assert item["item_id"] == "label_scope_conflict:l1:unsupported-local-profile"
    assert item["review_blocker"] is True


def test_manual_label_colliding_with_metadata_label_creates_nonblocking_scope_conflict(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={"label_id": "l1", "name": "start", "scope": "global", "hunk": 0, "addr": 4},
            ),
        ],
    )
    metadata = TargetMetadata(
        target_type="program",
        entry_register_seeds=(),
        seeded_code_labels=(
            SeededCodeLabelMetadata(
                addr=0,
                hunk=0,
                name="start",
                seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                review_status=TargetMetadataReviewStatus.SEEDED,
                citation="test",
            ),
        ),
    )

    projection = load_manual_projection(target_dir, stronger_metadata=metadata)

    assert projection.review_state == "needs_review"
    item = projection.review_items[0]
    assert item["kind"] == "label_scope_conflict"
    assert item["item_id"] == "label_scope_conflict:l1:metadata-collision"
    assert item["review_blocker"] is False


def test_required_manual_seed_conflicts_create_review_work(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={"seed_id": "code-start", "kind": "code", "mode": "required", "hunk": 0, "addr": 4},
            ),
            _action(
                "a2",
                2,
                "create_manual_seed",
                seed={
                    "seed_id": "text-range",
                    "kind": "data",
                    "mode": "required",
                    "range": "h0:$00000002..$00000008",
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "blocked"
    assert len(projection.review_items) == 1
    _assert_review_item_includes(
        projection.review_items[0],
        {
            "kind": "manual_seed_conflict",
            "item_id": "manual_seed_conflict:code-start:text-range",
            "scope": "range",
            "state": "open",
            "seed_ids": ["code-start", "text-range"],
            "hunk": 0,
            "start": 4,
            "end": 5,
            "message": "Required manual seeds code-start and text-range conflict",
        },
    )


def test_manual_resolution_closes_nonblocking_matching_evidence_fingerprint(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    log_path = target_dir / MANUAL_ACTION_LOG_FILE_NAME
    metadata = TargetMetadata(
        target_type="program",
        entry_register_seeds=(),
        seeded_code_labels=(
            SeededCodeLabelMetadata(
                addr=0,
                hunk=0,
                name="start",
                seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                review_status=TargetMetadataReviewStatus.SEEDED,
                citation="test",
            ),
        ),
    )

    def records(label_addr: int, resolution: dict[str, object] | None = None) -> list[dict[str, object]]:
        result = [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={"label_id": "l1", "name": "start", "scope": "global", "hunk": 0, "addr": label_addr},
            ),
        ]
        if resolution is not None:
            result.append(_action("a2", 2, "resolve_review_item", resolution=resolution))
        return result

    _append_jsonl(log_path, records(4))
    open_projection = load_manual_projection(target_dir, stronger_metadata=metadata)
    item = open_projection.review_items[0]
    item_id = item["item_id"]
    evidence_fingerprint = item["evidence_fingerprint"]
    assert open_projection.review_state == "needs_review"
    assert item["review_blocker"] is False

    resolution = {
        "resolution_id": "r1",
        "item_id": item_id,
        "evidence_fingerprint": evidence_fingerprint,
        "decision": "acknowledge",
    }
    _append_jsonl(log_path, records(4, resolution))
    resolved_projection = load_manual_projection(target_dir, stronger_metadata=metadata)

    assert resolved_projection.review_state == "clear"
    assert resolved_projection.review_items[0]["state"] == "resolved"

    _append_jsonl(log_path, records(6, resolution))
    changed_projection = load_manual_projection(target_dir, stronger_metadata=metadata)

    assert changed_projection.review_state == "needs_review"
    assert changed_projection.review_items[0]["state"] == "open"
    assert changed_projection.review_items[0]["changed_since_resolution"] is True
    assert changed_projection.review_items[0]["evidence_fingerprint"] != evidence_fingerprint


def test_manual_resolution_acknowledges_but_does_not_close_live_blocker(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    log_path = target_dir / MANUAL_ACTION_LOG_FILE_NAME

    def records(code_addr: int, resolution: dict[str, object] | None = None) -> list[dict[str, object]]:
        result = [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={"seed_id": "code-start", "kind": "code", "mode": "required", "hunk": 0, "addr": code_addr},
            ),
            _action(
                "a2",
                2,
                "create_manual_seed",
                seed={
                    "seed_id": "text-range",
                    "kind": "data",
                    "mode": "required",
                    "range": "h0:$00000002..$00000008",
                },
            ),
        ]
        if resolution is not None:
            result.append(_action("a3", 3, "resolve_review_item", resolution=resolution))
        return result

    _append_jsonl(log_path, records(4))
    open_projection = load_manual_projection(target_dir)
    item = open_projection.review_items[0]
    item_id = item["item_id"]
    evidence_fingerprint = item["evidence_fingerprint"]
    assert open_projection.review_state == "blocked"
    assert item["review_blocker"] is True

    resolution = {
        "resolution_id": "r1",
        "item_id": item_id,
        "evidence_fingerprint": evidence_fingerprint,
        "decision": "acknowledge",
    }
    _append_jsonl(log_path, records(4, resolution))
    resolved_projection = load_manual_projection(target_dir)

    assert resolved_projection.review_state == "blocked"
    assert resolved_projection.review_items[0]["state"] == "open"
    assert resolved_projection.review_items[0]["acknowledged"] is True

    _append_jsonl(log_path, records(6, resolution))
    changed_projection = load_manual_projection(target_dir)

    assert changed_projection.review_state == "blocked"
    assert changed_projection.review_items[0]["state"] == "open"
    assert changed_projection.review_items[0]["changed_since_resolution"] is True
    assert changed_projection.review_items[0]["evidence_fingerprint"] != evidence_fingerprint


def test_required_manual_data_seed_conflicts_with_stronger_code_entrypoint(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={
                    "seed_id": "text-range",
                    "kind": "data",
                    "mode": "required",
                    "range": "h0:$00000002..$00000008",
                },
            ),
        ],
    )
    metadata = TargetMetadata(
        target_type="program",
        entry_register_seeds=(),
        seeded_code_entrypoints=(
            SeededCodeEntrypointMetadata(
                addr=4,
                hunk=0,
                name="entry",
                seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                review_status=TargetMetadataReviewStatus.VALIDATED,
                citation="target_metadata",
            ),
        ),
    )

    projection = load_manual_projection(target_dir, stronger_metadata=metadata)

    assert projection.review_state == "blocked"
    assert len(projection.review_items) == 1
    _assert_review_item_includes(
        projection.review_items[0],
        {
            "kind": "manual_seed_conflict",
            "item_id": "manual_seed_conflict:text-range:seeded_code_entrypoint:h0:$00000004",
            "scope": "range",
            "state": "open",
            "seed_ids": ["text-range"],
            "stronger_kind": "code",
            "stronger_source": "seeded_code_entrypoint:h0:$00000004",
            "stronger_name": "entry",
            "hunk": 0,
            "start": 4,
            "end": 5,
            "message": "Required manual seed text-range conflicts with stronger seeded_code_entrypoint:h0:$00000004",
        },
    )


def test_required_manual_code_seed_conflicts_with_stronger_seeded_entity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={"seed_id": "code-start", "kind": "code", "mode": "required", "hunk": 0, "addr": 4},
            ),
        ],
    )
    metadata = TargetMetadata(
        target_type="program",
        entry_register_seeds=(),
        seeded_entities=(
            SeededEntityMetadata(
                addr=2,
                end=8,
                hunk=0,
                name="text",
                seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                review_status=TargetMetadataReviewStatus.VALIDATED,
                citation="target_metadata",
            ),
        ),
    )

    projection = load_manual_projection(target_dir, stronger_metadata=metadata)

    assert projection.review_state == "blocked"
    assert len(projection.review_items) == 1
    _assert_review_item_includes(
        projection.review_items[0],
        {
            "kind": "manual_seed_conflict",
            "item_id": "manual_seed_conflict:code-start:seeded_entity:h0:$00000002",
            "scope": "range",
            "state": "open",
            "seed_ids": ["code-start"],
            "stronger_kind": "data",
            "stronger_source": "seeded_entity:h0:$00000002",
            "stronger_name": "text",
            "hunk": 0,
            "start": 4,
            "end": 5,
            "message": "Required manual seed code-start conflicts with stronger seeded_entity:h0:$00000002",
        },
    )


def test_manual_action_log_projects_seeded_item_suppression(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "suppress_seeded_item",
                suppressed_seeded_item={"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
            ),
            _action(
                "a2",
                2,
                "suppress_seeded_item",
                suppressed_seeded_item={"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.suppressed_seeded_items == ({"kind": "seeded_entity", "hunk": 0, "addr": 0x100},)


def test_manual_action_log_projects_execution_view(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_execution_view",
                execution_view={
                    "execution_view_id": "stage",
                    "source_start": 0x20,
                    "source_end": 0x80,
                    "base_addr": 0x4000,
                    "name": "stage_code",
                },
            ),
            _action(
                "a2",
                2,
                "create_manual_execution_view",
                execution_view={
                    "execution_view_id": "stage-revised",
                    "source_start": 0x20,
                    "source_end": 0x80,
                    "base_addr": 0x4000,
                    "name": "stage_code_revised",
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.execution_views == (
        {
            "execution_view_id": "stage-revised",
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
            "name": "stage_code_revised",
        },
    )


def test_manual_action_log_removes_execution_view_by_identity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_execution_view",
                execution_view={
                    "execution_view_id": "stage",
                    "source_start": 0x20,
                    "source_end": 0x80,
                    "base_addr": 0x4000,
                    "name": "stage_code",
                },
            ),
            _action(
                "a2",
                2,
                "remove_manual_execution_view",
                execution_view={"source_start": 0x20, "source_end": 0x80, "base_addr": 0x4000},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.execution_views == ()
    assert projection.removed_execution_views == (
        {"source_start": 0x20, "source_end": 0x80, "base_addr": 0x4000},
    )


def test_required_manual_data_seed_conflicts_with_raw_entrypoint(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "demo.bin"
    _write_raw_source(target_dir, binary_path)
    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(binary_source),
            },
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={
                    "seed_id": "entry-as-data",
                    "kind": "data",
                    "mode": "required",
                    "range": "h0:$00000000..$00000002",
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir, binary_source=binary_source)

    assert projection.review_state == "blocked"
    assert len(projection.review_items) == 1
    _assert_review_item_includes(
        projection.review_items[0],
        {
            "kind": "manual_seed_conflict",
            "item_id": "manual_seed_conflict:entry-as-data:source_entrypoint:h0:$00000000",
            "scope": "range",
            "state": "open",
            "seed_ids": ["entry-as-data"],
            "stronger_kind": "code",
            "stronger_source": "source_entrypoint:h0:$00000000",
            "stronger_name": "entrypoint",
            "hunk": 0,
            "start": 0,
            "end": 1,
            "message": "Required manual seed entry-as-data conflicts with stronger source_entrypoint:h0:$00000000",
        },
    )


def test_malformed_manual_action_log_blocks_review(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text("{not json}\n", encoding="utf-8")

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "blocked"
    assert projection.review_items[0]["kind"] == "manual_action_log_malformed"


def test_manual_action_log_invalid_seed_kind_blocks_projection(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_seed", seed={"seed_id": "s1", "kind": "bytes"}),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == "blocked"
    assert projection.seeds == ()
    assert projection.review_items[0]["kind"] == "manual_action_log_malformed"


def test_manual_action_log_target_identity_mismatch_blocks_projection(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "demo.bin"
    _write_raw_source(target_dir, binary_path)
    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None
    current_identity = build_target_identity(binary_source)
    stale_identity = {**current_identity, "original_sha256": "0" * 64}
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": stale_identity},
            _action("a1", 1, "create_manual_seed", seed={"seed_id": "s1", "kind": "code"}),
        ],
    )

    projection = load_manual_projection(target_dir, binary_source=binary_source)

    assert projection.review_state == "blocked"
    assert projection.seeds == ()
    assert projection.review_items[0]["kind"] == "manual_action_log_target_mismatch"
    assert projection.current_target_identity == current_identity


def test_append_manual_action_rejects_target_identity_mismatch(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "demo.bin"
    _write_raw_source(target_dir, binary_path)
    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None
    current_identity = build_target_identity(binary_source)
    stale_identity = {**current_identity, "original_sha256": "0" * 64}
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [{"record": "manual_action_log_header", "version": 1, "target_identity": stale_identity}],
    )

    with pytest.raises(ValueError, match="target identity does not match"):
        append_manual_action(
            target_dir,
            kind=ManualActionKind.CREATE_MANUAL_SEED,
            payload={"seed": {"seed_id": "s1", "kind": "code", "addr": 0}},
            binary_source=binary_source,
        )
