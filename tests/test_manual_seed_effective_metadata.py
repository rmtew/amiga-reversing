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
    CustomStructFieldMetadata,
    CustomStructMetadata,
    DataBlockElementKind,
    DataBlockElementMetadata,
    DataBlockLayoutMetadata,
    ExecutionViewMetadata,
    ManualRepresentationMetadata,
    ManualRepresentationStyle,
    ManualRuntimeAddressRefMetadata,
    RssetLayoutRegionMetadata,
    RssetLayoutStorageKind,
    SeededCodeEntrypointMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    write_target_metadata,
    write_target_seeded_metadata,
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
            "c_type": None,
            "citation": "manual_action_log:text-table",
            "comment": "mode=required, data_role=string, unit=byte, encoding=ascii",
            "end": 0x320,
            "field_name": None,
            "field_type": None,
            "hunk": 1,
            "name": "manual_text",
            "pointer_struct": None,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualSeed:text-table",
            "source_path": None,
            "struct_name": None,
            "subtype": "string",
            "type": "data",
            "unit": "byte",
            "encoding": "ascii",
            "value_domain": None,
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


def test_effective_metadata_projects_target_equate_actions(tmp_path: Path) -> None:
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
                "create_manual_target_equate",
                target_equate={
                    "target_equate_id": "equate-1",
                    "name": "PLAYER_START_LIVES",
                    "value": 3,
                    "value_representation": "binary",
                },
            ),
            _action(
                "a2",
                2,
                "create_manual_representation",
                representation={
                    "representation_id": "repr-1",
                    "hunk": 0,
                    "addr": 0,
                    "end": 4,
                    "style": "symbol",
                    "element_kind": "immediate",
                    "operand_index": 0,
                    "symbol": "PLAYER_START_LIVES",
                },
            ),
            _action(
                "a3",
                3,
                "rename_manual_target_equate",
                target_equate={
                    "target_equate_id": "equate-1",
                    "previous_name": "PLAYER_START_LIVES",
                    "name": "PLAYER_INITIAL_LIVES",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["target_equates"] == [
        {
            "citation": "manual_action_log:equate-1",
            "comment": None,
            "name": "PLAYER_INITIAL_LIVES",
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "value": 3,
            "value_expression": None,
            "value_representation": "binary",
        }
    ]
    assert payload["manual_representations"][0]["symbol"] == "PLAYER_INITIAL_LIVES"


def test_effective_metadata_removes_target_equate_representations(tmp_path: Path) -> None:
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
                "create_manual_target_equate",
                target_equate={"target_equate_id": "equate-1", "name": "PLAYER_START_LIVES", "value": 3},
            ),
            _action(
                "a2",
                2,
                "create_manual_representation",
                representation={
                    "representation_id": "repr-1",
                    "hunk": 0,
                    "addr": 0,
                    "end": 4,
                    "style": "symbol",
                    "element_kind": "immediate",
                    "operand_index": 0,
                    "symbol": "PLAYER_START_LIVES",
                },
            ),
            _action(
                "a3",
                3,
                "remove_manual_target_equate",
                target_equate={"target_equate_id": "equate-1", "name": "PLAYER_START_LIVES"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["target_equates"] == []
    assert payload["manual_representations"] == []


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
                    "source_evidence_id": "prov-exec-a6",
                    "source_family": "library_base",
                    "source_evidence_status": "analysis_proven",
                    "path_lifetime_scope": {"kind": "entry", "hunk": 0, "addr": 0x120},
                    "confidence": "high",
                    "parent_evidence_ids": ["prov-entry"],
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
            "parent_evidence_ids": ["prov-entry"],
            "path_lifetime_scope": {"addr": 288, "hunk": 0, "kind": "entry"},
            "register": "A6",
            "source_evidence_id": "prov-exec-a6",
            "source_evidence_status": "analysis_proven",
            "source_family": "library_base",
            "struct_name": "LIB",
            "confidence": "high",
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


def test_effective_metadata_applies_manual_seeded_item_suppression(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=0x100,
                    end=0x104,
                    hunk=0,
                    name="auto_data",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded",
                    source_id="source",
                    source_path="source.asm",
                    source_locator="GeneratedData",
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
                "suppress_seeded_item",
                suppressed_seeded_item={"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_entities"] == []
    assert payload["suppressed_seeded_items"] == [{"addr": 0x100, "end": None, "hunk": 0, "kind": "seeded_entity"}]


def test_effective_metadata_suppresses_only_matching_seeded_entity_range(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=0x100,
                    end=0x102,
                    hunk=0,
                    name="short_data",
                    type="data",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded-short",
                    source_id="source",
                    source_path="source.asm",
                    source_locator="ShortData",
                ),
                SeededEntityMetadata(
                    addr=0x100,
                    end=0x104,
                    hunk=0,
                    name="long_data",
                    type="data",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded-long",
                    source_id="source",
                    source_path="source.asm",
                    source_locator="LongData",
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
                "suppress_seeded_item",
                suppressed_seeded_item={"kind": "seeded_entity", "hunk": 0, "addr": 0x100, "end": 0x102},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert [
        (entity["hunk"], entity["addr"], entity["end"], entity["name"])
        for entity in payload["seeded_entities"]
    ] == [(0, 0x100, 0x104, "long_data")]
    assert payload["suppressed_seeded_items"] == [{"addr": 0x100, "end": 0x102, "hunk": 0, "kind": "seeded_entity"}]


def test_effective_metadata_applies_data_symbol_rename_to_seeded_entity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=0x100,
                    end=0x104,
                    hunk=0,
                    name="auto_data",
                    comment="generated",
                    type="data",
                    subtype="pointer_table",
                    unit="long",
                    struct_name="Node",
                    field_name="LN_SUCC",
                    field_type="APTR",
                    c_type="struct Node *",
                    pointer_struct="Node",
                    value_domain="node_ref",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded",
                    source_id="source",
                    source_path="source.asm",
                    source_locator="GeneratedData",
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

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_entities"] == [
        {
            "addr": 0x100,
            "c_type": "struct Node *",
            "citation": "manual_action_log:data-symbol:h0:00000100:00000104",
            "comment": "generated",
            "encoding": None,
            "end": 0x104,
            "field_name": "LN_SUCC",
            "field_type": "APTR",
            "hunk": 0,
            "name": "player_table",
            "pointer_struct": "Node",
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualSeed:data-symbol:h0:00000100:00000104",
            "source_path": "source.asm",
            "struct_name": "Node",
            "subtype": "pointer_table",
            "type": "data",
            "unit": "long",
            "value_domain": "node_ref",
        }
    ]


def test_effective_metadata_keeps_same_address_data_symbols_with_different_ranges(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=0x100,
                    end=0x102,
                    hunk=0,
                    name="short_data",
                    type="data",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded",
                    source_id="source",
                    source_path="source.asm",
                    source_locator="ShortData",
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
                "rename_data_symbol",
                data_symbol={
                    "data_symbol_id": "data-symbol:h0:00000100:00000104",
                    "hunk": 0,
                    "addr": 0x100,
                    "end": 0x104,
                    "name": "long_data",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert [
        (entity["hunk"], entity["addr"], entity["end"], entity["type"], entity["name"])
        for entity in payload["seeded_entities"]
    ] == [
        (0, 0x100, 0x102, "data", "short_data"),
        (0, 0x100, 0x104, "data", "long_data"),
    ]


def test_effective_metadata_applies_manual_execution_view(tmp_path: Path) -> None:
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
                "create_manual_execution_view",
                execution_view={
                    "execution_view_id": "stage",
                    "source_start": 0x20,
                    "source_end": 0x80,
                    "base_addr": 0x4000,
                    "name": "stage_code",
                    "comment": "copied stage",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["execution_views"] == [
        {
            "base_addr": 0x4000,
            "citation": "manual_action_log:stage",
            "comment": "copied stage",
            "name": "stage_code",
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_end": 0x80,
            "source_start": 0x20,
        }
    ]


def test_effective_metadata_applies_manual_rsset_layout_region(tmp_path: Path) -> None:
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
                    "semantic_type": "counter",
                    "parser_role": "option_source",
                    "parser_routine": "parse_options",
                    "parse_order": 0,
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["rsset_layout_regions"] == [
        {
            "base_symbol": "__game_work_base__",
            "citation": "manual_action_log:work-counter",
            "layout_name": "work",
            "offset": 4,
            "parse_order": 0,
            "parser_role": "option_source",
            "parser_routine": "parse_options",
            "pointer_struct": None,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "semantic_type": "counter",
            "sizeof_symbol": "work_SIZEOF",
            "size": 2,
            "storage_kind": "scalar",
            "struct_name": None,
            "symbol": "work_counter",
        }
    ]


def test_effective_metadata_carries_rsset_binding_base_evidence_refs(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    base_ref = {
        "operand_index": 0,
        "base_register": "A6",
        "displacement": 0x0102,
        "source_family": "rsset_app_base",
        "status": "path_specific",
        "source_evidence_id": "prov-demo-rsset",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0xE2},
        "confidence": "medium",
        "origin_kind": "explicit_base_evidence",
        "accepted": True,
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_rsset_use_site_binding",
                rsset_use_site_binding={
                    "rsset_use_site_binding_id": "bind-selected-gap",
                    "hunk": 0,
                    "addr": 0xE2,
                    "operand_index": 0,
                    "base_register": "A6",
                    "displacement": 0x0102,
                    "layout_name": "app",
                    "base_symbol": "__amiga_app_base__",
                    "base_evidence_id": "selected-base:A6:__amiga_app_base__",
                    "source_evidence_id": "prov-demo-rsset",
                    "source_family": "rsset_app_base",
                    "source_evidence_status": "path_specific",
                    "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0xE2},
                    "confidence": "medium",
                    "base_evidence_refs": [base_ref],
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    binding = payload["rsset_use_site_bindings"][0]
    assert binding["source_evidence_id"] == "prov-demo-rsset"
    assert binding["source_family"] == "rsset_app_base"
    assert binding["source_evidence_status"] == "path_specific"
    assert binding["path_lifetime_scope"] == {"kind": "selected_use", "hunk": 0, "addr": 0xE2}
    assert binding["owner_action_id"] == "a1"
    assert binding["base_evidence_refs"] == [base_ref]


def test_effective_metadata_applies_manual_data_block_layout_with_elements(tmp_path: Path) -> None:
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
                "create_manual_data_block_layout",
                data_block_layout={
                    "layout_id": "ascii-hex",
                    "hunk": 0,
                    "source_start": 0x1442,
                    "source_end": 0x14A2,
                    "name": "ascii_hex_digit_value",
                    "role": "lookup_table",
                    "default_unit": "byte",
                    "provenance": {"xref": "loc_0_0000140E"},
                },
            ),
            _action(
                "a2",
                2,
                "set_manual_data_block_element",
                data_block_element={
                    "data_block_element_id": "ascii-hex:0",
                    "layout_id": "ascii-hex",
                    "offset": 0,
                    "width": 0x30,
                    "kind": "padding",
                    "representation": "hex",
                },
            ),
            _action(
                "a3",
                3,
                "set_manual_data_block_element",
                data_block_element={
                    "data_block_element_id": "ascii-hex:0x30",
                    "layout_id": "ascii-hex",
                    "offset": 0x30,
                    "width": 10,
                    "kind": "array",
                    "name": "digits",
                    "array_count": 10,
                    "array_stride": 1,
                },
            ),
            _action(
                "a4",
                4,
                "represent_manual_data_block_element",
                data_block_element={"layout_id": "ascii-hex", "offset": 0x30, "representation": "character"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["data_block_layouts"] == [
        {
            "citation": "manual_action_log:ascii-hex",
            "default_unit": "byte",
            "elements": [
                {
                    "array_count": None,
                    "array_stride": None,
                    "citation": "manual_action_log:ascii-hex:0",
                    "kind": "padding",
                    "layout_id": "ascii-hex",
                    "name": None,
                    "offset": 0,
                    "provenance": None,
                    "reference_interpretation": None,
                    "representation": "hex",
                    "review_status": "seeded",
                    "seed_origin": "manual_analysis",
                    "type_binding": None,
                    "width": 0x30,
                },
                {
                    "array_count": 10,
                    "array_stride": 1,
                    "citation": "manual_action_log:ascii-hex:0x30",
                    "kind": "array",
                    "layout_id": "ascii-hex",
                    "name": "digits",
                    "offset": 0x30,
                    "provenance": None,
                    "reference_interpretation": None,
                    "representation": "character",
                    "review_status": "seeded",
                    "seed_origin": "manual_analysis",
                    "type_binding": None,
                    "width": 10,
                },
            ],
            "hunk": 0,
            "layout_id": "ascii-hex",
            "name": "ascii_hex_digit_value",
            "provenance": {"xref": "loc_0_0000140E"},
            "review_status": "seeded",
            "role": "lookup_table",
            "runtime_end": None,
            "runtime_execution_view_id": None,
            "runtime_start": None,
            "seed_origin": "manual_analysis",
            "source_end": 0x14A2,
            "source_start": 0x1442,
            "version": 1,
        }
    ]
    assert payload["seeded_entities"] == [
        {
            "addr": 0x1442,
            "c_type": None,
            "citation": "manual_action_log:ascii-hex:0",
            "comment": "lookup_table",
            "encoding": None,
            "end": 0x1472,
            "field_name": None,
            "field_type": None,
            "hunk": 0,
            "name": "ascii_hex_digit_value",
            "pointer_struct": None,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": None,
            "source_locator": None,
            "source_path": None,
            "struct_name": None,
            "subtype": "lookup_table",
            "type": "data",
            "unit": "byte",
            "value_domain": None,
        },
        {
            "addr": 0x1472,
            "c_type": None,
            "citation": "manual_action_log:ascii-hex:0x30",
            "comment": "lookup_table",
            "encoding": None,
            "end": 0x147C,
            "field_name": None,
            "field_type": None,
            "hunk": 0,
            "name": "digits",
            "pointer_struct": None,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": None,
            "source_locator": None,
            "source_path": None,
            "struct_name": None,
            "subtype": "lookup_table",
            "type": "data",
            "unit": "byte",
            "value_domain": None,
        },
    ]
    assert payload["manual_representations"] == [
        {
            "addr": 0x1442,
            "citation": "manual_action_log:ascii-hex:0",
            "element_kind": "data_block_element",
            "end": 0x1472,
            "hunk": 0,
            "operand_index": None,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": None,
            "source_locator": None,
            "source_path": None,
            "style": "hex",
            "symbol": None,
        },
        {
            "addr": 0x1472,
            "citation": "manual_action_log:ascii-hex:0x30",
            "element_kind": "data_block_element",
            "end": 0x147C,
            "hunk": 0,
            "operand_index": None,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": None,
            "source_locator": None,
            "source_path": None,
            "style": "character",
            "symbol": None,
        },
    ]


def test_effective_metadata_removes_manual_data_block_layout(tmp_path: Path) -> None:
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
                "create_manual_data_block_layout",
                data_block_layout={
                    "layout_id": "ascii-hex",
                    "hunk": 0,
                    "source_start": 0x1442,
                    "source_end": 0x14A2,
                },
            ),
            _action(
                "a2",
                2,
                "remove_manual_data_block_layout",
                data_block_layout={"layout_id": "ascii-hex", "removal_state": "raw"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["data_block_layouts"] == []


def test_effective_metadata_projects_data_block_type_binding_owner_to_descendants(tmp_path: Path) -> None:
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
                "create_manual_custom_struct",
                custom_struct={
                    "name": "DataHeader",
                    "size": 6,
                    "fields": [
                        {"name": "magic", "type": "UWORD", "offset": 0, "size": 2},
                        {"name": "next_offset", "type": "APTR", "offset": 2, "size": 4},
                    ],
                },
            ),
            _action(
                "a2",
                2,
                "create_manual_data_block_layout",
                data_block_layout={
                    "layout_id": "header",
                    "hunk": 0,
                    "source_start": 0x100,
                    "source_end": 0x106,
                    "default_unit": "byte",
                },
            ),
            _action(
                "a3",
                3,
                "set_manual_data_block_element",
                data_block_element={
                    "data_block_element_id": "header:0",
                    "layout_id": "header",
                    "offset": 0,
                    "width": 6,
                    "kind": "struct",
                    "type_binding": {
                        "type_binding_id": "header:0:6:custom_struct:DataHeader",
                        "layout_id": "header",
                        "element_offset": 0,
                        "element_width": 6,
                        "binding_kind": "custom_struct",
                        "bound_type_id": "DataHeader",
                        "owner_action_id": "a3",
                        "source_evidence_id": "prov-header-base",
                        "parent_evidence_ids": ["prov-root"],
                    },
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    typed_entities = [
        entity
        for entity in payload["seeded_entities"]
        if entity["source_locator"] == "header:0:6:custom_struct:DataHeader"
    ]
    assert [(entity["field_name"], entity["owner_action_id"]) for entity in typed_entities] == [
        ("magic", "a3"),
        ("next_offset", "a3"),
    ]
    assert {entity["source_evidence_id"] for entity in typed_entities} == {"prov-header-base"}
    assert {tuple(entity["parent_evidence_ids"]) for entity in typed_entities} == {("prov-root",)}


def test_effective_metadata_projects_manual_data_block_interpreted_ref(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    interpreted_ref = {
        "data_block_ref_id": "ptr-table:0:absolute:h0:00002000",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x2000,
        "target_locator": {"hunk": 0, "offset": 0x2000},
        "source_value": 0x2000,
        "confidence": "manual",
        "xref_generation_mode": "bidirectional",
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_data_block_layout",
                data_block_layout={
                    "layout_id": "ptr-table",
                    "hunk": 0,
                    "source_start": 0x100,
                    "source_end": 0x104,
                    "default_unit": "long",
                },
            ),
            _action(
                "a2",
                2,
                "set_manual_data_block_element",
                data_block_element={
                    "data_block_element_id": "ptr-table:0",
                    "layout_id": "ptr-table",
                    "offset": 0,
                    "width": 4,
                    "kind": "scalar",
                },
            ),
            _action(
                "a3",
                3,
                "interpret_manual_data_block_element_ref",
                data_block_interpreted_ref=interpreted_ref,
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["data_block_layouts"][0]["elements"][0]["reference_interpretation"] == interpreted_ref
    assert payload["target_equates"] == [
        {
            "citation": "manual_action_log:ptr-table:0:absolute:h0:00002000",
            "comment": "data-block interpreted absolute reference",
            "name": "dblk_ref_h0_00002000",
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "value": 0x2000,
            "value_expression": None,
            "value_representation": None,
        }
    ]
    assert payload["manual_representations"] == [
        {
            "addr": 0x100,
            "citation": "manual_action_log:ptr-table:0:absolute:h0:00002000",
            "element_kind": "data_block_interpreted_ref",
            "end": 0x104,
            "hunk": 0,
            "operand_index": None,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ptr-table:0:absolute:h0:00002000",
            "source_path": None,
            "style": "symbol",
            "symbol": "dblk_ref_h0_00002000",
        }
    ]
    assert payload["manual_runtime_address_refs"] == [
        {
            "addr": 0x100,
            "citation": "manual_action_log:ptr-table:0:absolute:h0:00002000",
            "confidence": 3,
            "hunk": 0,
            "owner_element_offset": 0,
            "owner_id": "ptr-table:0:absolute:h0:00002000",
            "owner_kind": "data_block_interpreted_ref",
            "owner_layout_id": "ptr-table",
            "review_status": "seeded",
            "runtime_address": 0x2000,
            "seed_origin": "manual_analysis",
            "size": 4,
            "target_hunk": 0,
            "target_offset": 0x2000,
            "xref_generation_mode": "bidirectional",
        }
    ]


def test_effective_metadata_removes_manual_data_block_interpreted_ref(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    interpreted_ref = {
        "data_block_ref_id": "ptr-table:0:absolute:h0:00002000",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x2000,
        "target_locator": {"hunk": 0, "offset": 0x2000},
        "source_value": 0x2000,
        "confidence": "manual",
        "xref_generation_mode": "bidirectional",
    }
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_data_block_layout",
                data_block_layout={
                    "layout_id": "ptr-table",
                    "hunk": 0,
                    "source_start": 0x100,
                    "source_end": 0x104,
                    "default_unit": "long",
                },
            ),
            _action(
                "a2",
                2,
                "set_manual_data_block_element",
                data_block_element={
                    "data_block_element_id": "ptr-table:0",
                    "layout_id": "ptr-table",
                    "offset": 0,
                    "width": 4,
                    "kind": "scalar",
                },
            ),
            _action(
                "a3",
                3,
                "interpret_manual_data_block_element_ref",
                data_block_interpreted_ref=interpreted_ref,
            ),
            _action(
                "a4",
                4,
                "remove_manual_data_block_element_ref",
                data_block_interpreted_ref={
                    "data_block_ref_id": "ptr-table:0:absolute:h0:00002000",
                    "layout_id": "ptr-table",
                    "offset": 0,
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["data_block_layouts"][0]["elements"][0]["reference_interpretation"] is None
    assert payload["target_equates"] == []
    assert payload["manual_representations"] == []
    assert payload["manual_runtime_address_refs"] == []


def test_effective_metadata_clears_existing_data_block_interpreted_ref(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    existing_ref = {
        "data_block_ref_id": "ptr-table:0:absolute:h0:00002000",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x2000,
        "target_locator": {"hunk": 0, "offset": 0x2000},
        "source_value": 0x2000,
        "confidence": "manual",
        "xref_generation_mode": "bidirectional",
    }
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            manual_runtime_address_refs=(
                ManualRuntimeAddressRefMetadata(
                    addr=0x100,
                    hunk=0,
                    size=4,
                    target_hunk=0,
                    target_offset=0x2000,
                    runtime_address=0x2000,
                    confidence=3,
                    owner_kind="data_block_interpreted_ref",
                    owner_id="ptr-table:0:absolute:h0:00002000",
                    owner_layout_id="ptr-table",
                    owner_element_offset=0,
                    xref_generation_mode="bidirectional",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="manual_action_log:ptr-table:0:absolute:h0:00002000",
                ),
            ),
            data_block_layouts=(
                DataBlockLayoutMetadata(
                    layout_id="ptr-table",
                    hunk=0,
                    source_start=0x100,
                    source_end=0x104,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata",
                    elements=(
                        DataBlockElementMetadata(
                            layout_id="ptr-table",
                            offset=0,
                            width=4,
                            kind=DataBlockElementKind.SCALAR,
                            reference_interpretation=existing_ref,
                            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                            review_status=TargetMetadataReviewStatus.SEEDED,
                            citation="target_metadata",
                        ),
                    ),
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
                "remove_manual_data_block_element_ref",
                data_block_interpreted_ref={
                    "data_block_ref_id": "ptr-table:0:absolute:h0:00002000",
                    "layout_id": "ptr-table",
                    "offset": 0,
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["data_block_layouts"][0]["elements"][0]["reference_interpretation"] is None
    assert payload["manual_runtime_address_refs"] == []


def test_effective_metadata_keeps_unrelated_existing_data_block_interpreted_ref(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    existing_ref = {
        "data_block_ref_id": "ptr-table:0:absolute:h0:00002000",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x2000,
        "target_locator": {"hunk": 0, "offset": 0x2000},
        "source_value": 0x2000,
        "confidence": "manual",
        "xref_generation_mode": "bidirectional",
    }
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            data_block_layouts=(
                DataBlockLayoutMetadata(
                    layout_id="ptr-table",
                    hunk=0,
                    source_start=0x100,
                    source_end=0x104,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata",
                    elements=(
                        DataBlockElementMetadata(
                            layout_id="ptr-table",
                            offset=0,
                            width=4,
                            kind=DataBlockElementKind.SCALAR,
                            reference_interpretation=existing_ref,
                            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                            review_status=TargetMetadataReviewStatus.SEEDED,
                            citation="target_metadata",
                        ),
                    ),
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
                "remove_manual_data_block_element_ref",
                data_block_interpreted_ref={
                    "data_block_ref_id": "ptr-table:0:absolute:h0:00003000",
                    "layout_id": "ptr-table",
                    "offset": 0,
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["data_block_layouts"][0]["elements"][0]["reference_interpretation"] == existing_ref


def test_effective_metadata_removes_data_block_element_from_existing_layout(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            data_block_layouts=(
                DataBlockLayoutMetadata(
                    layout_id="ascii-hex",
                    hunk=0,
                    source_start=0x1442,
                    source_end=0x14A2,
                    name="ascii_hex_digit_value",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata",
                    elements=(
                        DataBlockElementMetadata(
                            layout_id="ascii-hex",
                            offset=0,
                            width=0x30,
                            kind=DataBlockElementKind.PADDING,
                            representation=ManualRepresentationStyle.HEX,
                            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                            review_status=TargetMetadataReviewStatus.SEEDED,
                            citation="target_metadata",
                        ),
                    ),
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
                "remove_manual_data_block_element",
                data_block_element={
                    "layout_id": "ascii-hex",
                    "offset": 0,
                    "width": 0x30,
                    "removal_state": "gap",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["data_block_layouts"][0]["elements"] == []


def test_effective_metadata_data_block_representation_overrides_standalone_representation(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            manual_representations=(
                ManualRepresentationMetadata(
                    addr=0x100,
                    end=0x104,
                    hunk=0,
                    style=ManualRepresentationStyle.BINARY,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata:standalone",
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
                "create_manual_data_block_layout",
                data_block_layout={
                    "layout_id": "values",
                    "hunk": 0,
                    "source_start": 0x100,
                    "source_end": 0x104,
                    "default_unit": "byte",
                },
            ),
            _action(
                "a2",
                2,
                "set_manual_data_block_element",
                data_block_element={
                    "data_block_element_id": "values:0",
                    "layout_id": "values",
                    "offset": 0,
                    "width": 4,
                    "kind": "array",
                    "representation": "character",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["manual_representations"] == [
        {
            "addr": 0x100,
            "citation": "manual_action_log:values:0",
            "element_kind": "data_block_element",
            "end": 0x104,
            "hunk": 0,
            "operand_index": None,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": None,
            "source_locator": None,
            "source_path": None,
            "style": "character",
            "symbol": None,
        }
    ]


def test_effective_metadata_restores_standalone_representation_after_data_block_element_removal(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            manual_representations=(
                ManualRepresentationMetadata(
                    addr=0x100,
                    end=0x104,
                    hunk=0,
                    style=ManualRepresentationStyle.BINARY,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata:standalone",
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
                "create_manual_data_block_layout",
                data_block_layout={
                    "layout_id": "values",
                    "hunk": 0,
                    "source_start": 0x100,
                    "source_end": 0x104,
                    "default_unit": "byte",
                },
            ),
            _action(
                "a2",
                2,
                "set_manual_data_block_element",
                data_block_element={
                    "data_block_element_id": "values:0",
                    "layout_id": "values",
                    "offset": 0,
                    "width": 4,
                    "kind": "array",
                    "representation": "character",
                },
            ),
            _action(
                "a3",
                3,
                "remove_manual_data_block_element",
                data_block_element={"layout_id": "values", "offset": 0, "width": 4, "removal_state": "raw"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["manual_representations"] == [
        {
            "addr": 0x100,
            "citation": "target_metadata:standalone",
            "element_kind": None,
            "end": 0x104,
            "hunk": 0,
            "operand_index": None,
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": None,
            "source_locator": None,
            "source_path": None,
            "style": "binary",
            "symbol": None,
        }
    ]


def test_effective_metadata_applies_manual_custom_struct(tmp_path: Path) -> None:
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

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["custom_structs"] == [
        {
            "available_since": "1.0",
            "base_offset": 0,
            "base_struct": None,
            "citation": "manual_action_log:InputEvent",
            "fields": [
                {
                    "available_since": "1.0",
                    "name": "ie_Class",
                    "named_base": None,
                    "offset": 4,
                    "pointer_struct": None,
                    "size": 1,
                    "struct": None,
                    "type": "UBYTE",
                }
            ],
            "name": "InputEvent",
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "size": 22,
            "source": "manual_action_log",
        }
    ]


def test_effective_metadata_removes_custom_struct_by_name(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            custom_structs=(
                CustomStructMetadata(
                    name="InputEvent",
                    size=22,
                    fields=(),
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata:test",
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
                "remove_manual_custom_struct",
                custom_struct={"name": "InputEvent"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["custom_structs"] == []


def test_effective_metadata_renames_custom_struct_by_name(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            custom_structs=(
                CustomStructMetadata(
                    name="InputEvent",
                    size=22,
                    fields=(),
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata:test",
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
                "rename_manual_custom_struct",
                custom_struct={"previous_name": "InputEvent", "name": "GameInput"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["custom_structs"][0]["name"] == "GameInput"


def test_effective_metadata_applies_manual_custom_struct_field(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            custom_structs=(
                CustomStructMetadata(
                    name="InputEvent",
                    size=22,
                    fields=(),
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata:test",
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

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["custom_structs"][0]["fields"] == [
        {
            "available_since": "1.0",
            "name": "ie_Class",
            "named_base": None,
            "offset": 4,
            "pointer_struct": None,
            "size": 1,
            "struct": None,
            "type": "UBYTE",
        }
    ]


def test_effective_metadata_removes_custom_struct_field_by_identity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            custom_structs=(
                CustomStructMetadata(
                    name="InputEvent",
                    size=22,
                    fields=(
                        CustomStructFieldMetadata(
                            name="ie_Class",
                            type="UBYTE",
                            offset=4,
                            size=1,
                        ),
                    ),
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata:test",
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
                "remove_manual_custom_struct_field",
                custom_struct_field={"struct_name": "InputEvent", "offset": 4},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["custom_structs"][0]["fields"] == []


def test_effective_metadata_renames_custom_struct_field_by_identity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            custom_structs=(
                CustomStructMetadata(
                    name="InputEvent",
                    size=22,
                    fields=(
                        CustomStructFieldMetadata(
                            name="ie_Class",
                            type="UBYTE",
                            offset=4,
                            size=1,
                        ),
                    ),
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata:test",
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
                "rename_manual_custom_struct_field",
                custom_struct_field={"struct_name": "InputEvent", "offset": 4, "name": "ie_Code"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["custom_structs"][0]["fields"][0]["name"] == "ie_Code"


def test_effective_metadata_removes_rsset_layout_region_by_identity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            rsset_layout_regions=(
                RssetLayoutRegionMetadata(
                    offset=4,
                    size=2,
                    layout_name="work",
                    base_symbol="__game_work_base__",
                    sizeof_symbol="work_SIZEOF",
                    symbol="work_counter",
                    storage_kind=RssetLayoutStorageKind.SCALAR,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata:test",
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
                "remove_manual_rsset_layout_region",
                rsset_layout_region={"offset": 4, "layout_name": "work", "base_symbol": "__game_work_base__"},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["rsset_layout_regions"] == []


def test_effective_metadata_removes_execution_view_by_identity(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            execution_views=(
                ExecutionViewMetadata(
                    source_start=0x20,
                    source_end=0x80,
                    base_addr=0x4000,
                    name="stage_code",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="target_metadata:test",
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
                "remove_manual_execution_view",
                execution_view={"source_start": 0x20, "source_end": 0x80, "base_addr": 0x4000},
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["execution_views"] == []


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
