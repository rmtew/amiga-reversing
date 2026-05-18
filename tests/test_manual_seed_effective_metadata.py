from __future__ import annotations

import json
from pathlib import Path

from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.effective_metadata import effective_metadata_text
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    build_target_identity,
)
from amiga_reversing.disasm.target_metadata import (
    SeededCodeEntrypointMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    write_target_metadata,
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


def test_effective_metadata_includes_required_manual_code_and_data_seeds(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={
                    "seed_id": "code-start",
                    "kind": "code",
                    "mode": "required",
                    "range": "h0:$00000200..$00000208",
                    "name": "manual_start",
                    "role": "extra entrypoint",
                },
            ),
            _action(
                "a2",
                2,
                "create_manual_seed",
                seed={
                    "seed_id": "text-table",
                    "kind": "data",
                    "mode": "required",
                    "hunk": 1,
                    "addr": 0x300,
                    "end": 0x320,
                    "data_role": "string",
                    "unit": "byte",
                    "encoding": "ascii",
                    "name": "manual_text",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_entrypoints"] == [
        {
            "addr": 0x200,
            "citation": "manual_action_log:code-start",
            "comment": "mode=required",
            "hunk": 0,
            "name": "manual_start",
            "review_status": "seeded",
            "role": "extra entrypoint",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualSeed:code-start",
            "source_path": None,
        }
    ]
    assert payload["seeded_entities"] == [
        {
            "addr": 0x300,
            "citation": "manual_action_log:text-table",
            "comment": "mode=required, data_role=string, unit=byte, encoding=ascii",
            "end": 0x320,
            "hunk": 1,
            "name": "manual_text",
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualSeed:text-table",
            "source_path": None,
            "subtype": "string",
            "type": "data",
            "unit": "byte",
            "encoding": "ascii",
        }
    ]


def test_effective_metadata_includes_manual_representation_without_classifying_data(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_representation",
                representation={
                    "representation_id": "repr-1",
                    "hunk": 0,
                    "addr": 0x300,
                    "end": 0x304,
                    "style": "character",
                    "element_kind": "operand",
                    "operand_index": 1,
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_entities"] == []
    assert payload["manual_representations"] == [
        {
            "addr": 0x300,
            "citation": "manual_action_log:repr-1",
            "element_kind": "operand",
            "end": 0x304,
            "hunk": 0,
            "review_status": "seeded",
            "operand_index": 1,
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualRepresentation:repr-1",
            "source_path": None,
            "style": "character",
            "symbol": None,
        }
    ]


def test_effective_metadata_projects_equate_semantic_hint_to_symbol_representation(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_semantic_hint",
                semantic_hint={
                    "semantic_hint_id": "hint-1",
                    "hunk": 0,
                    "addr": 0x300,
                    "element_kind": "operand",
                    "operand_index": 0,
                    "domain": "equate",
                    "symbol": "MEMF_CLEAR",
                    "value": 0x10000,
                    "namespace": "exec/memory.i",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["manual_representations"] == [
        {
            "addr": 0x300,
            "citation": "manual_action_log:hint-1",
            "element_kind": "operand",
            "end": None,
            "hunk": 0,
            "operand_index": 0,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualSemanticHint:hint-1",
            "source_path": None,
            "style": "symbol",
            "symbol": "MEMF_CLEAR",
        }
    ]


def test_effective_metadata_projects_lvo_semantic_hint_to_symbol_representation(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_semantic_hint",
                semantic_hint={
                    "semantic_hint_id": "hint-1",
                    "hunk": 0,
                    "addr": 0x300,
                    "element_kind": "operand",
                    "operand_index": 0,
                    "domain": "lvo",
                    "symbol": "exec.library/OpenLibrary",
                    "value": -552,
                    "namespace": "exec.library",
                    "function": "OpenLibrary",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["manual_representations"] == [
        {
            "addr": 0x300,
            "citation": "manual_action_log:hint-1",
            "element_kind": "operand",
            "end": None,
            "hunk": 0,
            "operand_index": 0,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualSemanticHint:hint-1",
            "source_path": None,
            "style": "symbol",
            "symbol": "_LVOOpenLibrary",
        }
    ]


def test_effective_metadata_projects_struct_offset_semantic_hint_to_symbol_representation(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_semantic_hint",
                semantic_hint={
                    "semantic_hint_id": "hint-1",
                    "hunk": 0,
                    "addr": 0x300,
                    "element_kind": "operand",
                    "operand_index": 0,
                    "domain": "struct_offset",
                    "symbol": "LN.ln_Succ",
                    "value": 0,
                    "namespace": "LN",
                    "field": "ln_Succ",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["manual_representations"] == [
        {
            "addr": 0x300,
            "citation": "manual_action_log:hint-1",
            "element_kind": "operand",
            "end": None,
            "hunk": 0,
            "operand_index": 0,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualSemanticHint:hint-1",
            "source_path": None,
            "style": "symbol",
            "symbol": "LN_SUCC",
        }
    ]


def test_effective_metadata_includes_manual_register_seed_for_semantic_helper(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_register_seed",
                register_seed={
                    "register_seed_id": "reg-1",
                    "entry_offset": 0x120,
                    "register": "A6",
                    "kind": "library_base",
                    "library_name": "exec.library",
                    "struct_name": "LIB",
                    "context_name": "exec.library",
                    "note": "Manual semantic helper",
                },
            ),
            _action(
                "a2",
                2,
                "create_manual_register_seed",
                register_seed={
                    "register_seed_id": "reg-2",
                    "entry_offset": 0x140,
                    "register": "A1",
                    "kind": "struct_ptr",
                    "library_name": None,
                    "struct_name": "IOStdReq",
                    "context_name": "trackdisk.device",
                    "note": "Manual semantic helper",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["entry_register_seeds"] == [
        {
            "context_name": "exec.library",
            "entry_offset": 0x120,
            "kind": "library_base",
            "library_name": "exec.library",
            "note": "Manual semantic helper",
            "register": "A6",
            "struct_name": "LIB",
        },
        {
            "context_name": "trackdisk.device",
            "entry_offset": 0x140,
            "kind": "struct_ptr",
            "library_name": None,
            "note": "Manual semantic helper",
            "register": "A1",
            "struct_name": "IOStdReq",
        },
    ]


def test_effective_metadata_ignores_suggested_manual_seeds_until_accepted(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={
                    "seed_id": "maybe-code",
                    "kind": "code",
                    "mode": "suggested",
                    "addr": 0x200,
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_entrypoints"] == []
    assert payload["seeded_entities"] == []


def test_effective_metadata_projects_manual_labels_and_comments_without_seeding_code_or_data(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={
                    "label_id": "loop-label",
                    "scope": "global",
                    "hunk": 0,
                    "addr": 0x20,
                    "name": "main_loop",
                    "comment": "loop head",
                },
            ),
            _action(
                "a2",
                2,
                "create_manual_comment",
                comment={"comment_id": "loop-note", "range": "h0:$00000024", "text": "poll joystick"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_entrypoints"] == []
    assert payload["seeded_entities"] == []
    assert payload["seeded_code_labels"] == [
        {
            "addr": 0x20,
            "citation": "manual_action_log:loop-label",
            "comment": "loop head",
            "hunk": 0,
            "name": "main_loop",
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualLabel:loop-label",
            "source_path": None,
        }
    ]
    assert payload["entry_comments"] == [
        {
            "addr": 0x24,
            "citation": "manual_action_log:loop-note",
            "comment": "poll joystick",
            "hunk": 0,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualComment:loop-note",
            "source_path": None,
        }
    ]


def test_effective_metadata_projects_runtime_manual_labels_to_absolute_labels(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={
                    "label_id": "runtime-entry",
                    "scope": "global",
                    "address_domain": "runtime",
                    "hunk": 0,
                    "addr": 0x10000,
                    "name": "ENTRYPOINT0000",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_labels"] == []
    assert payload["absolute_code_labels"] == [
        {
            "addr": 0x10000,
            "citation": "manual_action_log:runtime-entry",
            "comment": None,
            "name": "ENTRYPOINT0000",
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
        }
    ]


def test_effective_metadata_ignores_manual_labels_with_scope_conflicts(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_label",
                label={"label_id": "l1", "scope": "global", "hunk": 0, "addr": 0x20, "name": "dup"},
            ),
            _action(
                "a2",
                2,
                "create_manual_label",
                label={"label_id": "l2", "scope": "global", "hunk": 0, "addr": 0x24, "name": "dup"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_labels"] == []


def test_effective_metadata_ignores_required_manual_seeds_with_projection_conflicts(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
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
                    "data_role": "string",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_entrypoints"] == []
    assert payload["seeded_entities"] == []


def test_effective_metadata_preserves_stronger_code_entrypoint_over_conflicting_manual_data_seed(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_code_entrypoints=(
                SeededCodeEntrypointMetadata(
                    addr=4,
                    hunk=0,
                    name="existing_entry",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.VALIDATED,
                    citation="target_metadata",
                ),
            ),
        ),
    )
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
                    "data_role": "string",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_entrypoints"] == [
        {
            "addr": 4,
            "citation": "target_metadata",
            "comment": None,
            "hunk": 0,
            "name": "existing_entry",
            "review_status": "validated",
            "role": None,
            "seed_origin": "manual_analysis",
            "source_id": None,
            "source_locator": None,
            "source_path": None,
        }
    ]
    assert payload["seeded_entities"] == []


def test_effective_metadata_ignores_manual_data_seed_conflicting_with_raw_entrypoint(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x4e\x75")
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
    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
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
                    "data_role": "string",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_entities"] == []


def test_effective_metadata_ignores_manual_seeds_when_log_target_identity_mismatches(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x4e\x75")
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
    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None
    stale_identity = {**build_target_identity(binary_source), "original_sha256": "0" * 64}
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": stale_identity},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={
                    "seed_id": "stale-code",
                    "kind": "code",
                    "mode": "required",
                    "addr": 0x200,
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_entrypoints"] == []
