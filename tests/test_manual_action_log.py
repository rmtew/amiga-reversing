from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    ManualActionKind,
    ReviewItemKind,
    ReviewState,
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


def test_manual_action_log_projects_data_symbol_rename_as_seed_override(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "rename_data_symbol",
                data_symbol={
                    "data_symbol_id": "data-symbol:h0:00000100:00000104",
                    "hunk": 0,
                    "addr": 0x100,
                    "end": 0x104,
                    "previous_name": "auto_data",
                    "name": "player_table",
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.seeds == (
        {
            "seed_id": "data-symbol:h0:00000100:00000104",
            "kind": "data",
            "hunk": 0,
            "addr": 0x100,
            "end": 0x104,
            "name": "player_table",
        },
    )


def test_manual_action_log_keeps_same_address_data_symbol_rename_ranges(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "rename_data_symbol",
                data_symbol={
                    "hunk": 0,
                    "addr": 0x100,
                    "end": 0x104,
                    "name": "short_table",
                },
            ),
            _action(
                "a2",
                2,
                "rename_data_symbol",
                data_symbol={
                    "hunk": 0,
                    "addr": 0x100,
                    "end": 0x108,
                    "name": "long_table",
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.seeds == (
        {
            "seed_id": "data-symbol:h0:00000100:00000104",
            "kind": "data",
            "hunk": 0,
            "addr": 0x100,
            "end": 0x104,
            "name": "short_table",
        },
        {
            "seed_id": "data-symbol:h0:00000100:00000108",
            "kind": "data",
            "hunk": 0,
            "addr": 0x100,
            "end": 0x108,
            "name": "long_table",
        },
    )


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


def test_append_manual_action_rejects_duplicate_data_block_layout_range(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "target.bin"
    _write_raw_source(target_dir, binary_path, payload=b"\x00" * 16)
    binary_source = resolve_target_binary_source(target_dir)
    assert binary_source is not None
    payload = {
        "data_block_layout": {
            "layout_id": "first-layout",
            "hunk": 0,
            "source_start": 0,
            "source_end": 8,
            "default_unit": "word",
        }
    }

    append_manual_action(
        target_dir,
        kind=ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT,
        payload=payload,
        binary_source=binary_source,
    )

    with pytest.raises(ValueError, match="already covers this exact range"):
        append_manual_action(
            target_dir,
            kind=ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT,
            payload={"data_block_layout": {**payload["data_block_layout"], "layout_id": "second-layout"}},
            binary_source=binary_source,
        )


def test_append_manual_action_rejects_overlapping_data_block_layout_range(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "target.bin"
    _write_raw_source(target_dir, binary_path, payload=b"\x00" * 16)
    binary_source = resolve_target_binary_source(target_dir)
    assert binary_source is not None
    append_manual_action(
        target_dir,
        kind=ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT,
        payload={"data_block_layout": {"layout_id": "first-layout", "hunk": 0, "source_start": 0, "source_end": 8}},
        binary_source=binary_source,
    )

    with pytest.raises(ValueError, match="overlaps this source range"):
        append_manual_action(
            target_dir,
            kind=ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT,
            payload={"data_block_layout": {"layout_id": "second-layout", "hunk": 0, "source_start": 4, "source_end": 12}},
            binary_source=binary_source,
        )


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
            "owner_action_id": "a2",
        },
    )


def test_manual_action_log_projects_runtime_observation_view(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_runtime_observation_view",
                runtime_observation_view={
                    "execution_view_id": "observed-stage",
                    "source_start": 0x20,
                    "source_end": 0x80,
                    "base_addr": 0x4000,
                    "name": "observed_stage",
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.execution_views == ()
    assert projection.runtime_observation_views == (
        {
            "execution_view_id": "observed-stage",
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
            "name": "observed_stage",
            "owner_action_id": "a1",
        },
    )


def test_manual_action_log_projects_rsset_layout_region(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_rsset_layout_region",
                rsset_layout_region={
                    "rsset_layout_region_id": "work-counter",
                    "offset": 4,
                    "size": 2,
                    "layout_name": "work",
                    "base_symbol": "__game_work_base__",
                    "sizeof_symbol": "work_SIZEOF",
                    "symbol": "work_counter",
                    "storage_kind": "scalar",
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.rsset_layout_regions == (
        {
            "rsset_layout_region_id": "work-counter",
            "offset": 4,
            "size": 2,
            "layout_name": "work",
            "base_symbol": "__game_work_base__",
            "sizeof_symbol": "work_SIZEOF",
            "symbol": "work_counter",
            "storage_kind": "scalar",
        },
    )


def test_manual_action_log_projects_rsset_use_site_binding_with_owner_action(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binding = {
        "rsset_use_site_binding_id": "bind-h0-0102",
        "hunk": 0,
        "addr": 0xE2,
        "operand_index": 0,
        "base_register": "A6",
        "displacement": 0x0102,
        "layout_name": "app",
        "base_symbol": "__amiga_app_base__",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "access": "write",
        "width_bytes": 1,
        "render_state": "linked_gap_or_raw",
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_rsset_use_site_binding", rsset_use_site_binding=binding),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.rsset_use_site_bindings == ({**binding, "owner_action_id": "a1"},)
    assert projection.removed_rsset_use_site_bindings == ()


def test_manual_action_log_removes_rsset_use_site_binding(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binding_identity = {
        "rsset_use_site_binding_id": "bind-h0-0102",
        "hunk": 0,
        "addr": 0xE2,
        "operand_index": 0,
        "base_register": "A6",
        "displacement": 0x0102,
        "layout_name": "app",
        "base_symbol": "__amiga_app_base__",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_rsset_use_site_binding", rsset_use_site_binding=binding_identity),
            _action("a2", 2, "remove_manual_rsset_use_site_binding", rsset_use_site_binding=binding_identity),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.rsset_use_site_bindings == ()
    assert projection.removed_rsset_use_site_bindings == ({**binding_identity, "cleanup_action_id": "a2"},)


def test_manual_action_log_projects_data_block_layout_and_elements(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    layout = {
        "layout_id": "ascii-hex",
        "hunk": 0,
        "source_start": 0x1442,
        "source_end": 0x14A2,
        "name": "ascii_hex_digit_value",
        "role": "lookup_table",
        "default_unit": "byte",
    }
    first_element = {
        "data_block_element_id": "ascii-hex:0",
        "layout_id": "ascii-hex",
        "offset": 0,
        "width": 0x30,
        "kind": "padding",
        "representation": "hex",
    }
    second_element = {
        "data_block_element_id": "ascii-hex:0x30",
        "layout_id": "ascii-hex",
        "offset": 0x30,
        "width": 10,
        "kind": "array",
        "name": "digits",
        "array_count": 10,
        "array_stride": 1,
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_data_block_layout", data_block_layout=layout),
            _action("a2", 2, "set_manual_data_block_element", data_block_element=first_element),
            _action("a3", 3, "set_manual_data_block_element", data_block_element=second_element),
            _action(
                "a4",
                4,
                "represent_manual_data_block_element",
                data_block_element={"layout_id": "ascii-hex", "offset": 0x30, "representation": "character"},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.data_block_layouts == (layout,)
    assert projection.data_block_elements == (
        first_element,
        {**second_element, "representation": "character", "representation_action_id": "a4"},
    )
    assert projection.removed_data_block_layouts == ()
    assert projection.removed_data_block_elements == ()


def test_manual_action_log_stamps_data_block_type_binding_owner(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    layout = {"layout_id": "events", "hunk": 0, "source_start": 0x100, "source_end": 0x110}
    type_binding = {
        "type_binding_id": "events:0:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
    }
    element = {
        "data_block_element_id": "events:0",
        "layout_id": "events",
        "offset": 0,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": type_binding,
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_data_block_layout", data_block_layout=layout),
            _action("a2", 2, "set_manual_data_block_element", data_block_element=element),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.data_block_elements == (
        {**element, "type_binding": {**type_binding, "owner_action_id": "a2"}},
    )


def test_manual_action_log_stamps_data_block_type_binding_cleanup(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    layout = {"layout_id": "events", "hunk": 0, "source_start": 0x100, "source_end": 0x110}
    previous_type_binding = {
        "type_binding_id": "events:0:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "owner_action_id": "a2",
    }
    element = {
        "data_block_element_id": "events:0",
        "layout_id": "events",
        "offset": 0,
        "width": 4,
        "kind": "scalar",
        "previous_type_binding": previous_type_binding,
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_data_block_layout", data_block_layout=layout),
            _action("a3", 3, "set_manual_data_block_element", data_block_element=element),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.data_block_elements == (
        {**element, "previous_type_binding": {**previous_type_binding, "cleanup_action_id": "a3"}},
    )


def test_manual_action_log_projects_data_block_interpreted_refs(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    layout = {"layout_id": "ptr-table", "hunk": 0, "source_start": 0x100, "source_end": 0x110}
    element = {
        "data_block_element_id": "ptr-table:0",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "kind": "scalar",
    }
    interpreted_ref = {
        "data_block_ref_id": "ptr-table:0:absolute",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x200,
        "target_locator": {"hunk": 0, "offset": 0x200},
        "source_value": 0x200,
        "xref_generation_mode": "bidirectional",
        "confidence": "manual",
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_data_block_layout", data_block_layout=layout),
            _action("a2", 2, "set_manual_data_block_element", data_block_element=element),
            _action("a3", 3, "interpret_manual_data_block_element_ref", data_block_interpreted_ref=interpreted_ref),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.data_block_interpreted_refs == (interpreted_ref,)
    assert projection.removed_data_block_interpreted_refs == ()


def test_manual_action_log_removes_data_block_interpreted_ref(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    layout = {"layout_id": "ptr-table", "hunk": 0, "source_start": 0x100, "source_end": 0x110}
    element = {"data_block_element_id": "ptr-table:0", "layout_id": "ptr-table", "offset": 0, "width": 4, "kind": "scalar"}
    interpreted_ref = {
        "data_block_ref_id": "ptr-table:0:absolute",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x200,
        "target_locator": {"hunk": 0, "offset": 0x200},
        "source_value": 0x200,
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_data_block_layout", data_block_layout=layout),
            _action("a2", 2, "set_manual_data_block_element", data_block_element=element),
            _action("a3", 3, "interpret_manual_data_block_element_ref", data_block_interpreted_ref=interpreted_ref),
            _action(
                "a4",
                4,
                "remove_manual_data_block_element_ref",
                data_block_interpreted_ref={"data_block_ref_id": "ptr-table:0:absolute", "layout_id": "ptr-table", "offset": 0},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.data_block_interpreted_refs == ()
    assert projection.removed_data_block_interpreted_refs == ({**interpreted_ref, "cleanup_action_id": "a4"},)


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        ({"target_locator": {"hunk": 0, "offset": 0x201}}, "target_locator must match"),
        ({"source_value": 0x201}, "source_value must match target_offset"),
    ],
)
def test_manual_action_log_rejects_invalid_data_block_interpreted_ref_payload(
    tmp_path: Path,
    patch: dict[str, object],
    message: str,
) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    layout = {"layout_id": "ptr-table", "hunk": 0, "source_start": 0x100, "source_end": 0x104}
    element = {"data_block_element_id": "ptr-table:0", "layout_id": "ptr-table", "offset": 0, "width": 4, "kind": "scalar"}
    interpreted_ref = {
        "data_block_ref_id": "ptr-table:0:absolute",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x200,
        "target_locator": {"hunk": 0, "offset": 0x200},
        "source_value": 0x200,
        **patch,
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_data_block_layout", data_block_layout=layout),
            _action("a2", 2, "set_manual_data_block_element", data_block_element=element),
            _action("a3", 3, "interpret_manual_data_block_element_ref", data_block_interpreted_ref=interpreted_ref),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state == ReviewState.BLOCKED
    assert projection.data_block_interpreted_refs == ()
    assert any(message in str(item.get("message") or "") for item in projection.diagnostics)


def test_manual_action_log_accepts_interior_data_block_interpreted_ref(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    layout = {"layout_id": "ptr-table", "hunk": 0, "source_start": 0x100, "source_end": 0x108}
    element = {"data_block_element_id": "ptr-table:0", "layout_id": "ptr-table", "offset": 0, "width": 8, "kind": "array"}
    interpreted_ref = {
        "data_block_ref_id": "ptr-table:4:absolute",
        "layout_id": "ptr-table",
        "offset": 4,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x200,
        "target_locator": {"hunk": 0, "offset": 0x200},
        "source_value": 0x200,
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_data_block_layout", data_block_layout=layout),
            _action("a2", 2, "set_manual_data_block_element", data_block_element=element),
            _action("a3", 3, "interpret_manual_data_block_element_ref", data_block_interpreted_ref=interpreted_ref),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.data_block_interpreted_refs == (interpreted_ref,)


def test_manual_action_log_removes_data_block_layout_and_owned_elements(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    layout = {"layout_id": "ascii-hex", "hunk": 0, "source_start": 0x1442, "source_end": 0x14A2}
    element = {
        "data_block_element_id": "ascii-hex:0",
        "layout_id": "ascii-hex",
        "offset": 0,
        "width": 4,
        "kind": "scalar",
    }
    interpreted_ref = {
        "data_block_ref_id": "ascii-hex:0:absolute",
        "layout_id": "ascii-hex",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x200,
        "target_locator": {"hunk": 0, "offset": 0x200},
        "source_value": 0x200,
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_data_block_layout", data_block_layout=layout),
            _action("a2", 2, "set_manual_data_block_element", data_block_element=element),
            _action("a3", 3, "interpret_manual_data_block_element_ref", data_block_interpreted_ref=interpreted_ref),
            _action(
                "a4",
                4,
                "remove_manual_data_block_layout",
                data_block_layout={"layout_id": "ascii-hex", "removal_state": "raw"},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.data_block_layouts == ()
    assert projection.data_block_elements == ()
    assert projection.data_block_interpreted_refs == ()
    assert projection.removed_data_block_layouts == ({**layout, "cleanup_action_id": "a4"},)
    assert projection.removed_data_block_elements == (
        {**element, "cleanup_action_id": "a4", "removal_state": "raw"},
    )
    assert projection.removed_data_block_interpreted_refs == ({**interpreted_ref, "cleanup_action_id": "a4"},)


def test_manual_action_log_flags_overlapping_data_block_layout_without_replace(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_data_block_layout",
                data_block_layout={"layout_id": "first", "hunk": 0, "source_start": 0x100, "source_end": 0x120},
            ),
            _action(
                "a2",
                2,
                "create_manual_data_block_layout",
                data_block_layout={"layout_id": "second", "hunk": 0, "source_start": 0x110, "source_end": 0x130},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert [layout["layout_id"] for layout in projection.data_block_layouts] == ["first"]
    assert projection.review_items[0]["kind"] is ReviewItemKind.MANUAL_DATA_BLOCK_LAYOUT_CONFLICT
    assert projection.review_items[0]["layout_id"] == "second"
    assert projection.review_items[0]["conflicting_layout_id"] == "first"


def test_manual_action_log_removing_rejected_overlapping_layout_clears_conflict_review(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_data_block_layout",
                data_block_layout={"layout_id": "first", "hunk": 0, "source_start": 0x100, "source_end": 0x120},
            ),
            _action(
                "a2",
                2,
                "create_manual_data_block_layout",
                data_block_layout={"layout_id": "second", "hunk": 0, "source_start": 0x110, "source_end": 0x130},
            ),
            _action(
                "a3",
                3,
                "remove_manual_data_block_layout",
                data_block_layout={"layout_id": "second", "hunk": 0, "source_start": 0x110, "source_end": 0x130},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert [layout["layout_id"] for layout in projection.data_block_layouts] == ["first"]
    assert projection.review_items == ()
    assert projection.review_state is ReviewState.CLEAR


def test_manual_action_log_replaces_overlapping_data_block_layout_when_explicit(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    first = {"layout_id": "first", "hunk": 0, "source_start": 0x100, "source_end": 0x120}
    second = {
        "layout_id": "second",
        "hunk": 0,
        "source_start": 0x110,
        "source_end": 0x130,
        "replace_overlaps": True,
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action("a1", 1, "create_manual_data_block_layout", data_block_layout=first),
            _action("a2", 2, "create_manual_data_block_layout", data_block_layout=second),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.data_block_layouts == (second,)
    assert projection.removed_data_block_layouts == ({**first, "replacement_action_id": "a2"},)


def test_manual_action_log_blocks_stale_data_block_layout_edit_range(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_data_block_layout",
                data_block_layout={"layout_id": "values", "hunk": 0, "source_start": 0x100, "source_end": 0x120},
            ),
            _action(
                "a2",
                2,
                "edit_manual_data_block_layout",
                data_block_layout={"layout_id": "values", "hunk": 0, "source_start": 0x104, "source_end": 0x120},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state is ReviewState.BLOCKED
    assert projection.review_items[0]["kind"] is ReviewItemKind.MANUAL_ACTION_LOG_MALFORMED
    assert "range does not match existing layout" in str(projection.review_items[0]["message"])


def test_manual_action_log_blocks_stale_data_block_layout_remove_range(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_data_block_layout",
                data_block_layout={"layout_id": "values", "hunk": 0, "source_start": 0x100, "source_end": 0x120},
            ),
            _action(
                "a2",
                2,
                "remove_manual_data_block_layout",
                data_block_layout={"layout_id": "values", "hunk": 0, "source_start": 0x100, "source_end": 0x124},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.review_state is ReviewState.BLOCKED
    assert projection.review_items[0]["kind"] is ReviewItemKind.MANUAL_ACTION_LOG_MALFORMED
    assert "range does not match existing layout" in str(projection.review_items[0]["message"])


def test_manual_action_log_projects_custom_struct(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_custom_struct",
                custom_struct={
                    "name": "InputEvent",
                    "size": 22,
                    "fields": [
                        {
                            "name": "ie_Class",
                            "type": "UBYTE",
                            "offset": 4,
                            "size": 1,
                        }
                    ],
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.custom_structs == (
        {
            "name": "InputEvent",
            "size": 22,
            "fields": [
                {
                    "name": "ie_Class",
                    "type": "UBYTE",
                    "offset": 4,
                    "size": 1,
                }
            ],
        },
    )


def test_manual_action_log_removes_custom_struct_by_name(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_custom_struct",
                custom_struct={"name": "InputEvent", "size": 22, "fields": []},
            ),
            _action(
                "a2",
                2,
                "remove_manual_custom_struct",
                custom_struct={"name": "InputEvent"},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.custom_structs == ()
    assert projection.removed_custom_structs == ({"name": "InputEvent"},)


def test_manual_action_log_renames_custom_struct_by_name(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_custom_struct",
                custom_struct={"name": "InputEvent", "size": 22, "fields": []},
            ),
            _action(
                "a2",
                2,
                "rename_manual_custom_struct",
                custom_struct={"previous_name": "InputEvent", "name": "GameInput"},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.custom_structs == ({"name": "GameInput", "size": 22, "fields": []},)
    assert projection.renamed_custom_structs == (
        {"previous_name": "InputEvent", "name": "GameInput"},
    )


def test_manual_action_log_projects_custom_struct_field(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_custom_struct_field",
                custom_struct_field={
                    "struct_name": "InputEvent",
                    "name": "ie_Class",
                    "type": "UBYTE",
                    "offset": 4,
                    "size": 1,
                },
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.custom_struct_fields == (
        {
            "struct_name": "InputEvent",
            "name": "ie_Class",
            "type": "UBYTE",
            "offset": 4,
            "size": 1,
            "owner_action_id": "a1",
        },
    )


def test_manual_action_log_removes_custom_struct_field_by_identity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_custom_struct_field",
                custom_struct_field={
                    "struct_name": "InputEvent",
                    "name": "ie_Class",
                    "type": "UBYTE",
                    "offset": 4,
                    "size": 1,
                },
            ),
            _action(
                "a2",
                2,
                "remove_manual_custom_struct_field",
                custom_struct_field={"struct_name": "InputEvent", "offset": 4, "name": "ie_Class"},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.custom_struct_fields == ()
    assert projection.removed_custom_struct_fields == (
        {
            "struct_name": "InputEvent",
            "offset": 4,
            "name": "ie_Class",
            "owner_action_id": "a1",
            "cleanup_action_id": "a2",
        },
    )


def test_manual_action_log_renames_custom_struct_field_by_identity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_custom_struct_field",
                custom_struct_field={
                    "struct_name": "InputEvent",
                    "name": "ie_Class",
                    "type": "UBYTE",
                    "offset": 4,
                    "size": 1,
                },
            ),
            _action(
                "a2",
                2,
                "rename_manual_custom_struct_field",
                custom_struct_field={"struct_name": "InputEvent", "offset": 4, "name": "ie_Code"},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.custom_struct_fields == (
        {
            "struct_name": "InputEvent",
            "name": "ie_Code",
            "type": "UBYTE",
            "offset": 4,
            "size": 1,
            "owner_action_id": "a2",
        },
    )
    assert projection.renamed_custom_struct_fields == (
        {"struct_name": "InputEvent", "offset": 4, "name": "ie_Code", "owner_action_id": "a2"},
    )


def test_manual_action_log_removes_rsset_layout_region_by_identity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_rsset_layout_region",
                rsset_layout_region={
                    "rsset_layout_region_id": "work-counter",
                    "offset": 4,
                    "layout_name": "work",
                    "base_symbol": "__game_work_base__",
                    "symbol": "work_counter",
                },
            ),
            _action(
                "a2",
                2,
                "remove_manual_rsset_layout_region",
                rsset_layout_region={"offset": 4, "layout_name": "work", "base_symbol": "__game_work_base__"},
            ),
        ],
    )

    projection = load_manual_projection(target_dir)

    assert projection.rsset_layout_regions == ()
    assert projection.removed_rsset_layout_regions == (
        {"offset": 4, "layout_name": "work", "base_symbol": "__game_work_base__"},
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
        {
            "execution_view_id": "stage",
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
            "name": "stage_code",
            "owner_action_id": "a1",
            "cleanup_action_id": "a2",
        },
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
