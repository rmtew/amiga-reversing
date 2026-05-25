from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from amiga_reversing.tools import platform_executable_formats


def test_platform_executable_format_kb_schema_and_data_validate() -> None:
    diagnostics = platform_executable_formats.validate_kb(
        platform_executable_formats.load_kb(),
        platform_executable_formats.load_schema(),
    )

    assert diagnostics == []


def test_schema_vocabulary_covers_018_001_required_model_terms() -> None:
    kb = platform_executable_formats.load_kb()
    vocab = kb["vocabularies"]

    assert set(vocab["fact_states"]) == {"validated", "parser_asserted", "candidate", "deferred", "unsupported"}
    assert set(vocab["source_types"]) == {
        "old_out_of_print",
        "modern_compatible",
        "project_observed",
        "parser_asserted",
    }
    assert set(vocab["entrypoint_types"]) == {
        "file_entrypoint",
        "segment_entrypoint",
        "runtime_entrypoint",
        "exported_entrypoint",
        "callback_entrypoint",
        "analysis_seed_entrypoint",
    }


def test_thin_macos_proof_record_keeps_current_entry_boundary_candidate() -> None:
    kb = platform_executable_formats.load_kb()
    record = platform_executable_formats.record_by_id(kb, "macos.hfs_resource_fork.code_resources.thin_proof")
    fact = platform_executable_formats.fact_by_id(record, "macos.code_resource.movea_stack_a0.boundary.candidate")

    assert record["platform_id"] == "macos"
    assert record["format_id"] == "macos.hfs_resource_fork.code_resources"
    assert record["archetype_id"] == "macos.application_code_resources"
    assert fact["status"] == "candidate"
    assert fact["parser_use"] == "candidate_only"
    assert record["required_parser_behavior"]["accepted_output_requires_fact_states"] == [
        "validated",
        "parser_asserted",
    ]


def test_candidate_fact_cannot_authorize_accepted_parser_output() -> None:
    kb = platform_executable_formats.load_kb()
    candidate = kb["records"][0]["facts"][0]
    candidate["parser_use"] = "accepted_parser_output"

    diagnostics = platform_executable_formats.validate_kb(kb, platform_executable_formats.load_schema())

    assert any("cannot use candidate as accepted parser output" in item for item in diagnostics)


def test_parser_asserted_fact_requires_assertion_context() -> None:
    kb = platform_executable_formats.load_kb()
    fact = copy.deepcopy(kb["records"][0]["facts"][0])
    fact["id"] = "fixture.parser_asserted.without_context"
    fact["status"] = "parser_asserted"
    fact["source_type"] = "parser_asserted"
    fact["parser_use"] = "accepted_parser_output"
    kb["records"][0]["facts"].append(fact)

    diagnostics = platform_executable_formats.validate_kb(kb, platform_executable_formats.load_schema())

    assert any("parser_asserted fact lacks parser_assertion" in item for item in diagnostics)


def test_deferred_and_unsupported_items_are_not_accepted_parser_outputs() -> None:
    kb = platform_executable_formats.load_kb()
    relocation = kb["records"][0]["relocations"][0]
    unsupported = kb["records"][0]["unsupported"][0]

    assert relocation["status"] == "deferred"
    assert relocation["parser_use"] == "deferred_only"
    assert unsupported["status"] == "unsupported"
    assert unsupported["required_parser_behavior"] == "ignore_safely"


def test_018_002_macos_citation_packets_capture_validated_code_facts() -> None:
    kb = platform_executable_formats.load_kb()
    code0 = platform_executable_formats.citation_packet_by_id(kb, "macos.packet.code0.jump_table_metadata")
    code1 = platform_executable_formats.citation_packet_by_id(kb, "macos.packet.code1.main_startup")
    segment_header = platform_executable_formats.citation_packet_by_id(
        kb,
        "macos.packet.nonzero_code.segment_header",
    )

    assert code0["status"] == "validated"
    assert code0["source_type"] == "old_out_of_print"
    assert "runtime_entry_model" in code0["affects"]
    assert segment_header["status"] == "validated"
    assert "This does not define the first executable instruction" in segment_header["missing_evidence"][0]
    assert code1["status"] == "validated"
    assert "movea.l" in code1["missing_evidence"][0]


def test_018_002_movea_boundary_packet_stays_candidate() -> None:
    kb = platform_executable_formats.load_kb()
    packet = platform_executable_formats.citation_packet_by_id(kb, "macos.packet.movea_stack_a0_boundary")

    assert packet["status"] == "candidate"
    assert packet["source_type"] == "project_observed"
    assert packet["parser_behavior_before_kb_migration"] == "emit_candidate"
    assert "No cited Segment Loader" in packet["missing_evidence"][0]


def test_project_observed_citation_packet_cannot_validate_general_platform_rule() -> None:
    kb = platform_executable_formats.load_kb()
    packet = kb["citation_packets"][7]
    assert packet["id"] == "macos.packet.mpw_asm_fixture_code_inventory"
    packet["status"] = "validated"

    diagnostics = platform_executable_formats.validate_kb(kb, platform_executable_formats.load_schema())

    assert any("project_observed packet must not validate a general platform rule" in item for item in diagnostics)


def test_018_003_accepted_macos_record_uses_validated_packets() -> None:
    kb = platform_executable_formats.load_kb()
    record = platform_executable_formats.record_by_id(
        kb,
        "macos.hfs_resource_fork.code_resources.mpw_application",
    )

    assert record["fact_state"] == "validated"
    assert record["required_parser_behavior"]["kb_backed"] is True
    accepted_fact = platform_executable_formats.fact_by_id(record, "macos.code_resource.0.jump_table_metadata")
    segment_header = platform_executable_formats.fact_by_id(record, "macos.code_resource.nonzero.segment_header")
    assert accepted_fact["status"] == "validated"
    assert accepted_fact["parser_use"] == "accepted_parser_output"
    assert segment_header["status"] == "validated"
    assert segment_header["parser_use"] == "accepted_parser_output"


def test_018_003_movea_migration_remains_candidate_in_accepted_record() -> None:
    kb = platform_executable_formats.load_kb()
    record = platform_executable_formats.record_by_id(
        kb,
        "macos.hfs_resource_fork.code_resources.mpw_application",
    )
    fact = platform_executable_formats.fact_by_id(record, "macos.code_resource.movea_stack_a0.boundary.candidate")
    entry = next(item for item in record["entrypoints"] if item["id"] == "macos.code_resource.movea_stack_a0.entry_candidate")

    assert fact["status"] == "candidate"
    assert fact["parser_use"] == "candidate_only"
    assert entry["status"] == "candidate"
    assert entry["parser_use"] == "candidate_only"


def test_018_004_guardrail_report_separates_kb_backed_and_report_only_records() -> None:
    kb = platform_executable_formats.load_kb()
    report = platform_executable_formats.build_guardrail_report(kb)

    assert "macos.hfs_resource_fork.code_resources.mpw_application" in report["kb_backed_records"]
    assert "macos.hfs_resource_fork.code_resources.thin_proof" in report["report_only_records"]
    mac_record = next(
        item
        for item in report["records"]
        if item["id"] == "macos.hfs_resource_fork.code_resources.mpw_application"
    )
    assert "macos.code_resource.0.jump_table_metadata" in mac_record["accepted_parser_fact_ids"]
    assert "macos.code_resource.movea_stack_a0.boundary.candidate" in mac_record["candidate_only_fact_ids"]
    assert "macos.segment_loader.relocation_fixups.deferred" in mac_record["deferred_fact_ids"]


def test_018_004_mac_movea_heuristic_guardrail_fails_candidate_promotion() -> None:
    kb = platform_executable_formats.load_kb()
    record = next(
        item
        for item in kb["records"]
        if item["id"] == "macos.hfs_resource_fork.code_resources.mpw_application"
    )
    fact = next(item for item in record["facts"] if item["id"] == "macos.code_resource.movea_stack_a0.boundary.candidate")
    fact["parser_use"] = "accepted_parser_output"

    diagnostics = platform_executable_formats.validate_kb(kb, platform_executable_formats.load_schema())

    assert any("cannot use candidate as accepted parser output" in item for item in diagnostics)


def test_018_006_031_032_first_amiga_and_atari_records_keep_current_authority_state() -> None:
    kb = platform_executable_formats.load_kb()
    amiga = platform_executable_formats.record_by_id(kb, "amiga.hunk.load_file.basic_backfill")
    atari = platform_executable_formats.record_by_id(kb, "atari_st.prg.gemdos_basic_backfill")

    assert amiga["platform_id"] == "amiga"
    assert amiga["format_id"] == "amiga.hunk"
    assert amiga["fact_state"] == "parser_asserted"
    assert amiga["required_parser_behavior"]["kb_backed"] is True
    assert atari["platform_id"] == "atari_st"
    assert atari["format_id"] == "atari_st.prg"
    assert atari["fact_state"] == "parser_asserted"
    assert atari["required_parser_behavior"]["kb_backed"] is True


def test_018_006_backfill_records_do_not_authorize_accepted_parser_output() -> None:
    kb = platform_executable_formats.load_kb()
    amiga = platform_executable_formats.record_by_id(kb, "amiga.hunk.load_file.basic_backfill")
    atari = platform_executable_formats.record_by_id(kb, "atari_st.prg.gemdos_basic_backfill")

    assert all(item["parser_use"] != "accepted_parser_output" for item in amiga["facts"])
    assert all(item["parser_use"] != "accepted_parser_output" for item in atari["facts"])
    assert amiga["runtime_model"][0]["status"] == "deferred"
    assert atari["runtime_model"][0]["status"] == "deferred"


def test_018_031_amiga_hunk_reference_slice_is_parser_asserted_and_kb_backed() -> None:
    kb = platform_executable_formats.load_kb()
    record = platform_executable_formats.record_by_id(kb, "amiga.hunk.load_file.basic_backfill")
    accepted = platform_executable_formats.record_item_by_id(record, "amiga.hunk.code_data_bss.sections.accepted")
    candidate = platform_executable_formats.record_item_by_id(record, "amiga.hunk.code_data_bss.sections.candidate")
    runtime = platform_executable_formats.record_item_by_id(record, "amiga.hunk.runtime_entry.deferred")

    assert record["fact_state"] == "parser_asserted"
    assert record["required_parser_behavior"]["kb_backed"] is True
    assert record["required_parser_behavior"]["missing_fact_behavior"] == "fail_closed"
    assert accepted["status"] == "parser_asserted"
    assert accepted["parser_use"] == "accepted_parser_output"
    assert accepted["details"]["parser_assertion"]["standard_interpretation"]
    assert candidate["status"] == "candidate"
    assert candidate["parser_use"] == "candidate_only"
    assert runtime["status"] == "deferred"
    assert runtime["parser_use"] == "deferred_only"


def test_018_032_atari_prg_reference_slice_is_parser_asserted_and_kb_backed() -> None:
    kb = platform_executable_formats.load_kb()
    record = platform_executable_formats.record_by_id(kb, "atari_st.prg.gemdos_basic_backfill")
    accepted = platform_executable_formats.record_item_by_id(record, "atari_st.prg.container_sequence.accepted")
    deferred = platform_executable_formats.record_item_by_id(record, "atari_st.prg.relocation_terminator_variants.deferred")

    assert record["fact_state"] == "parser_asserted"
    assert record["required_parser_behavior"]["kb_backed"] is True
    assert record["required_parser_behavior"]["missing_fact_behavior"] == "fail_closed"
    assert accepted["status"] == "parser_asserted"
    assert accepted["parser_use"] == "accepted_parser_output"
    assert accepted["details"]["parser_assertion"]["reason"]
    assert deferred["status"] == "deferred"


def test_018_037_macos_blockers_are_formally_deferred_or_unsupported() -> None:
    kb = platform_executable_formats.load_kb()
    record = platform_executable_formats.record_by_id(kb, "macos.hfs_resource_fork.code_resources.mpw_application")
    byte_entry = platform_executable_formats.record_item_by_id(record, "macos.code_resource.byte_entry_rule.unknown")
    relocation = platform_executable_formats.record_item_by_id(record, "macos.segment_loader.relocation_fixups.deferred")
    source_map = platform_executable_formats.record_item_by_id(record, "macos.source_to_code.fixture_product.deferred")
    curs_payload = platform_executable_formats.record_item_by_id(record, "macos.resource_fork.curs.payload_decode.unsupported")
    movea = platform_executable_formats.record_item_by_id(record, "macos.code_resource.movea_stack_a0.boundary.candidate")

    assert byte_entry["status"] == "deferred"
    assert byte_entry["required_parser_behavior"] == "block_closeout"
    assert byte_entry["details"]["final_resolution"] == "formal_deferred"
    assert byte_entry["details"]["candidate_fact_id"] == movea["id"]
    assert relocation["status"] == "deferred"
    assert relocation["parser_use"] == "deferred_only"
    assert relocation["details"]["final_resolution"] == "formal_deferred"
    assert "classic_CODE_fixup_record_location" in relocation["details"]["missing_evidence"]
    assert source_map["status"] == "deferred"
    assert source_map["required_parser_behavior"] == "block_closeout"
    assert source_map["details"]["must_not_map_to_observed_product"] == "MPW/Tools/Asm"
    assert curs_payload["status"] == "unsupported"
    assert curs_payload["required_parser_behavior"] == "ignore_safely"
    assert curs_payload["details"]["accepted_type_level_fact_id"] == "macos.resource_fork.curs.layout.accepted"
    assert movea["status"] == "candidate"
    assert movea["parser_use"] == "candidate_only"


def test_018_008_parser_fact_reference_validator_rejects_citation_packet_candidate_ids() -> None:
    kb = platform_executable_formats.load_kb()
    payload = {
        "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
        "fact_id": "macos.segment_loader.code_resources",
        "fact_status": "validated",
        "parser_use": "accepted_parser_output",
    }

    diagnostics = platform_executable_formats.validate_parser_fact_references(payload, kb)

    assert any("citation packet fact_candidate_id" in item for item in diagnostics)


def test_018_008_parser_fact_reference_validator_rejects_status_and_parser_use_drift() -> None:
    kb = platform_executable_formats.load_kb()
    payload = {
        "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
        "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
        "fact_status": "validated",
        "parser_use": "accepted_parser_output",
    }

    diagnostics = platform_executable_formats.validate_parser_fact_references(payload, kb)

    assert any("does not match KB status 'candidate'" in item for item in diagnostics)
    assert any("does not match KB parser_use 'candidate_only'" in item for item in diagnostics)


def test_018_034_parser_fact_coverage_report_classifies_current_mac_output() -> None:
    payload = {
        "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
        "code": {
            "fact_id": "macos.code_resource.0.jump_table_metadata",
            "fact_status": "validated",
            "parser_use": "accepted_parser_output",
            "layout_ranges": [
                {
                    "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                    "fact_status": "candidate",
                    "parser_use": "candidate_only",
                },
                {
                    "fact_id": "macos.segment_loader.relocation_fixups.deferred",
                    "fact_status": "deferred",
                    "parser_use": "deferred_only",
                },
            ],
        },
    }

    report = platform_executable_formats.build_parser_fact_coverage_report([payload], labels=["mac_fixture"])

    assert report["summary"] == {
        "parser_outputs": 1,
        "emitted_fact_refs": 3,
        "accepted": 1,
        "candidate": 1,
        "deferred": 1,
        "unsupported": 0,
        "invalid": 0,
    }
    assert report["invalid_fact_refs"] == []
    assert {"amiga", "atari_st"} <= set(report["unreported_platforms"])
    assert report["generated_fact_table"]["source"] == "knowledge/platform_executable_formats.json"


def test_018_034_parser_fact_coverage_fails_closed_on_invalid_accepted_claims() -> None:
    payload = {
        "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
        "claims": [
            {
                "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                "fact_status": "candidate",
                "parser_use": "accepted_parser_output",
            },
            {
                "fact_id": "macos.missing.accepted",
                "fact_status": "validated",
                "parser_use": "accepted_parser_output",
            },
        ],
    }

    report = platform_executable_formats.build_parser_fact_coverage_report([payload])

    reasons = {item["reason"] for item in report["invalid_fact_refs"]}
    assert report["summary"]["invalid"] == 2
    assert "parser_use_mismatch" in reasons
    assert "unknown_fact_id" in reasons


def test_018_039_coverage_cli_rejects_empty_closeout_input(capsys) -> None:
    exit_code = platform_executable_formats.main(["coverage"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "coverage requires --parser-output, --current-macos-c-backend" in captured.err
    assert "--current-amiga-hunk" in captured.err
    assert "--current-atari-prg" in captured.err
    assert captured.out == ""


def test_018_039_coverage_cli_allows_explicit_empty_inventory(capsys) -> None:
    exit_code = platform_executable_formats.main(["coverage", "--allow-empty"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["summary"]["parser_outputs"] == 0
    assert output["unreported_platforms"] == ["amiga", "atari_st", "macos"]


def test_018_039_coverage_cli_can_include_current_macos_backend(monkeypatch, capsys) -> None:
    def fake_current_macos_output(image_path: Path, hfs_path: str) -> dict[str, object]:
        assert image_path.name == "MPW-GM.img.bin"
        assert hfs_path == "MPW-GM/MPW/Tools/Asm"
        return {
            "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        }

    monkeypatch.setattr(platform_executable_formats, "_load_current_macos_c_backend_output", fake_current_macos_output)

    exit_code = platform_executable_formats.main(["coverage", "--current-macos-c-backend"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["summary"]["parser_outputs"] == 1
    assert output["summary"]["candidate"] == 1
    assert output["summary"]["invalid"] == 0


def test_019_001_current_amiga_hunk_output_runs_real_parser_path() -> None:
    payload = platform_executable_formats._load_current_amiga_hunk_output()
    report = platform_executable_formats.build_parser_fact_coverage_report([payload], labels=["current-amiga-hunk"])

    assert payload["kb_record_id"] == "amiga.hunk.load_file.basic_backfill"
    assert payload["parser"] == "platform_file_inspect_path_json_alloc"
    assert {section["kind"] for section in payload["sections"]} == {"code", "data", "bss"}
    assert payload["fact_refs"]
    assert report["summary"]["invalid"] == 0
    assert report["summary"]["accepted"] >= 3
    assert report["summary"]["deferred"] >= 1
    assert "amiga" not in report["unreported_platforms"]


def test_019_004_raw_amiga_hunk_parser_summary_emits_kb_refs_before_coverage() -> None:
    payload = platform_executable_formats._inspect_platform_fixture(
        "amiga-hunk",
        platform_executable_formats._synthetic_amiga_hunk_fixture(),
        ".hunk",
    )
    refs = payload["fact_refs"]

    assert payload["kb_record_id"] == "amiga.hunk.load_file.basic_backfill"
    assert payload["parser"] == "platform_file_inspect_path_json_alloc"
    assert {
        (ref["fact_id"], ref["fact_status"], ref["parser_use"])
        for ref in refs
    } >= {
        ("amiga.hunk.header.identifies_load_file.accepted", "parser_asserted", "accepted_parser_output"),
        ("amiga.hunk.code_data_bss.sections.accepted", "parser_asserted", "accepted_parser_output"),
        ("amiga.hunk.runtime_entry.deferred", "deferred", "deferred_only"),
    }
    assert platform_executable_formats.validate_parser_fact_references(payload) == []


def test_020_002_raw_amiga_hunk_parser_summary_exposes_shared_ranges() -> None:
    payload = platform_executable_formats._inspect_platform_fixture(
        "amiga-hunk",
        platform_executable_formats._synthetic_amiga_hunk_fixture(),
        ".hunk",
    )
    ranges = {item["role"]: item for item in payload["executable_ranges"]}
    deferred = {item["kind"]: item for item in payload["executable_deferred"]}

    assert payload["executable_model"] == "platform_executable_summary_v1"
    assert set(ranges) == {"code", "data", "bss"}
    assert ranges["code"] == {
        "role": "code",
        "source_offset": 0,
        "size": 4,
        "stored_size": 4,
        "status": "parser_asserted",
        "fact_id": "amiga.hunk.code_data_bss.sections.accepted",
        "fact_status": "parser_asserted",
        "parser_use": "accepted_parser_output",
    }
    assert ranges["data"] == {
        "role": "data",
        "source_offset": 4,
        "size": 4,
        "stored_size": 4,
        "status": "parser_asserted",
        "fact_id": "amiga.hunk.code_data_bss.sections.accepted",
        "fact_status": "parser_asserted",
        "parser_use": "accepted_parser_output",
    }
    assert ranges["bss"] == {
        "role": "bss",
        "source_offset": 8,
        "size": 8,
        "stored_size": 0,
        "status": "parser_asserted",
        "fact_id": "amiga.hunk.bss.size_only.accepted",
        "fact_status": "parser_asserted",
        "parser_use": "accepted_parser_output",
    }
    assert deferred["runtime_entry"] == {
        "kind": "runtime_entry",
        "status": "deferred",
        "fact_id": "amiga.hunk.runtime_entry.deferred",
        "fact_status": "deferred",
        "parser_use": "deferred_only",
    }
    assert payload["sections"]
    assert payload["fact_refs"]
    assert platform_executable_formats.validate_parser_fact_references(payload) == []


def test_019_002_current_atari_prg_output_runs_real_parser_path() -> None:
    payload = platform_executable_formats._load_current_atari_prg_output()
    report = platform_executable_formats.build_parser_fact_coverage_report([payload], labels=["current-atari-prg"])

    assert payload["kb_record_id"] == "atari_st.prg.gemdos_basic_backfill"
    assert payload["parser"] == "platform_file_inspect_path_json_alloc"
    assert {section["kind"] for section in payload["sections"]} == {"code", "data", "bss"}
    assert payload["fact_refs"]
    assert report["summary"]["invalid"] == 0
    assert report["summary"]["accepted"] >= 3
    assert report["summary"]["candidate"] >= 1
    assert report["summary"]["deferred"] >= 1
    assert "atari_st" not in report["unreported_platforms"]


def test_019_004_raw_atari_prg_parser_summary_emits_kb_refs_before_coverage() -> None:
    payload = platform_executable_formats._inspect_platform_fixture(
        "atari-st",
        platform_executable_formats._synthetic_atari_prg_fixture(),
        ".prg",
    )
    refs = payload["fact_refs"]

    assert payload["kb_record_id"] == "atari_st.prg.gemdos_basic_backfill"
    assert payload["parser"] == "platform_file_inspect_path_json_alloc"
    assert {
        (ref["fact_id"], ref["fact_status"], ref["parser_use"])
        for ref in refs
    } >= {
        ("atari_st.prg.magic_601a.accepted", "parser_asserted", "accepted_parser_output"),
        ("atari_st.prg.text_data_bss_regions.accepted", "parser_asserted", "accepted_parser_output"),
        ("atari_st.prg.bss.header_only.candidate", "candidate", "candidate_only"),
        ("atari_st.prg.relocation_terminator_variants.deferred", "deferred", "deferred_only"),
    }
    assert platform_executable_formats.validate_parser_fact_references(payload) == []


def test_019_004_current_amiga_hunk_coverage_refuses_summary_without_parser_refs(monkeypatch) -> None:
    monkeypatch.setattr(
        platform_executable_formats,
        "_inspect_platform_fixture",
        lambda backend, fixture_bytes, suffix: {
            "platform": backend,
            "file_kind": "executable",
            "sections": [{"kind": "code"}],
        },
    )

    with pytest.raises(ValueError, match="parser summary did not emit kb_record_id"):
        platform_executable_formats._load_current_amiga_hunk_output()


def test_019_004_current_atari_prg_coverage_refuses_summary_without_parser_refs(monkeypatch) -> None:
    monkeypatch.setattr(
        platform_executable_formats,
        "_inspect_platform_fixture",
        lambda backend, fixture_bytes, suffix: {
            "platform": backend,
            "file_kind": "executable",
            "sections": [{"kind": "code"}],
        },
    )

    with pytest.raises(ValueError, match="parser summary did not emit kb_record_id"):
        platform_executable_formats._load_current_atari_prg_output()


def test_019_003_combined_current_coverage_requires_amiga_and_atari_refs(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        platform_executable_formats,
        "_load_current_macos_c_backend_output",
        lambda image_path, hfs_path: {
            "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
            "fact_id": "macos.code_resource.0.jump_table_metadata",
            "fact_status": "validated",
            "parser_use": "accepted_parser_output",
        },
    )

    exit_code = platform_executable_formats.main(
        ["coverage", "--current-macos-c-backend", "--current-amiga-hunk", "--current-atari-prg"]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["summary"]["parser_outputs"] == 3
    assert output["summary"]["invalid"] == 0
    assert output["summary"]["accepted"] >= 8
    assert output["summary"]["candidate"] >= 1
    assert output["summary"]["deferred"] >= 2
    assert output["unreported_platforms"] == []
    sources = {item["source"] for item in output["emitted_fact_refs"]}
    assert "current-amiga-hunk:synthetic-parser-fixture" in sources
    assert "current-atari-prg:synthetic-parser-fixture" in sources


def test_018_034_coverage_cli_reports_json_and_returns_failure_for_invalid(tmp_path: Path, capsys) -> None:
    payload_path = tmp_path / "parser-output.json"
    payload_path.write_text(
        json.dumps(
            {
                "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                "fact_status": "candidate",
                "parser_use": "accepted_parser_output",
            }
        ),
        encoding="utf-8",
    )

    exit_code = platform_executable_formats.main(["coverage", "--parser-output", str(payload_path)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["summary"]["invalid"] == 1
    assert output["invalid_fact_refs"][0]["reason"] == "parser_use_mismatch"


def test_018_008_c_macos_fact_constants_resolve_to_kb_record_items() -> None:
    kb = platform_executable_formats.load_kb()
    record = platform_executable_formats.record_by_id(kb, "macos.hfs_resource_fork.code_resources.mpw_application")
    repo_root = Path(__file__).resolve().parents[1]
    c_paths = [
        repo_root / "src/platform_file_lib.c",
        repo_root / "src/platform_macos_resource.c",
    ]
    constants: set[str] = set()
    for path in c_paths:
        text = path.read_text(encoding="utf-8")
        constants.update(re.findall(r'"(?P<id>macos\.[A-Za-z0-9_.-]+)"', text))

    assert "macos.segment_loader.code_resources" not in constants
    assert constants
    for constant in constants:
        if constant == record["id"]:
            continue
        platform_executable_formats.record_item_by_id(record, constant)


def test_018_013_generated_platform_executable_fact_table_is_fresh(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "src" / "scripts" / "generate_platform_format_runtime.py"
    subprocess.run(
        [sys.executable, str(script), "--output-dir", str(tmp_path)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    for name in ("platform_executable_formats.c", "platform_executable_formats.h"):
        assert (tmp_path / name).read_text(encoding="utf-8") == (
            repo_root / "src" / "generated" / name
        ).read_text(encoding="utf-8")


def test_018_013_generated_fact_table_excludes_citation_packet_candidate_ids() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    header = (repo_root / "src" / "generated" / "platform_executable_formats.h").read_text(encoding="utf-8")
    source = (repo_root / "src" / "generated" / "platform_executable_formats.c").read_text(encoding="utf-8")

    assert "PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_RESOURCE_FORK_CODE_RESOURCES_ACCEPTED" in header
    assert '"macos.segment_loader.code_resources"' not in source


def test_018_033_generated_fact_table_preserves_ownership_and_consumer_constants() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    header = (repo_root / "src" / "generated" / "platform_executable_formats.h").read_text(encoding="utf-8")
    source = (repo_root / "src" / "generated" / "platform_executable_formats.c").read_text(encoding="utf-8")
    mac_resource = (repo_root / "src" / "platform_macos_resource.c").read_text(encoding="utf-8")

    assert "const char *platform_id;" in header
    assert "const char *archetype_id;" in header
    assert re.search(
        r'\{\s*"macos\.hfs_resource_fork\.code_resources\.mpw_application",\s*"macos",\s*'
        r'"macos\.application_code_resources",\s*"macos\.code_resource\.0\.jump_table_metadata"',
        source,
    )
    assert "PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_CODE_RESOURCE_0_JUMP_TABLE_METADATA" in mac_resource
    assert "PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_CODE_RESOURCE_BYTE_ENTRY_RULE_UNKNOWN" in mac_resource
    assert '"macos.code_resource.0.jump_table_metadata"' not in mac_resource
    assert '"macos.code_resource.byte_entry_rule.unknown"' not in mac_resource


def test_018_014_015_016_research_packets_and_audit_state() -> None:
    kb = platform_executable_formats.load_kb()
    mac_record = platform_executable_formats.record_by_id(kb, "macos.hfs_resource_fork.code_resources.mpw_application")
    non_code = platform_executable_formats.record_item_by_id(
        mac_record,
        "macos.resource_fork.non_code_metadata.inventory.candidate",
    )
    renderer = platform_executable_formats.record_item_by_id(
        mac_record,
        "macos.renderer.accepted_vs_candidate_labeling.accepted",
    )
    object_packet = platform_executable_formats.citation_packet_by_id(kb, "macos.packet.mpw.object_modules")
    library_packet = platform_executable_formats.citation_packet_by_id(kb, "macos.packet.mpw.object_libraries")
    format_packet = platform_executable_formats.citation_packet_by_id(
        kb,
        "macos.packet.mpw.object_library_format.deferred",
    )

    assert non_code["status"] == "candidate"
    assert non_code["parser_use"] == "candidate_only"
    assert renderer["status"] == "parser_asserted"
    assert renderer["source_type"] == "parser_asserted"
    assert object_packet["status"] == "validated"
    assert library_packet["status"] == "validated"
    assert format_packet["status"] == "deferred"
