from __future__ import annotations

import copy

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


def test_018_006_first_amiga_and_atari_records_are_schema_valid_report_only() -> None:
    kb = platform_executable_formats.load_kb()
    amiga = platform_executable_formats.record_by_id(kb, "amiga.hunk.load_file.basic_backfill")
    atari = platform_executable_formats.record_by_id(kb, "atari_st.prg.gemdos_basic_backfill")

    assert amiga["platform_id"] == "amiga"
    assert amiga["format_id"] == "amiga.hunk"
    assert amiga["required_parser_behavior"]["kb_backed"] is False
    assert atari["platform_id"] == "atari_st"
    assert atari["format_id"] == "atari_st.prg"
    assert atari["required_parser_behavior"]["kb_backed"] is False


def test_018_006_backfill_records_do_not_authorize_accepted_parser_output() -> None:
    kb = platform_executable_formats.load_kb()
    amiga = platform_executable_formats.record_by_id(kb, "amiga.hunk.load_file.basic_backfill")
    atari = platform_executable_formats.record_by_id(kb, "atari_st.prg.gemdos_basic_backfill")

    assert all(item["parser_use"] != "accepted_parser_output" for item in amiga["facts"])
    assert all(item["parser_use"] != "accepted_parser_output" for item in atari["facts"])
    assert amiga["runtime_model"][0]["status"] == "deferred"
    assert atari["runtime_model"][0]["status"] == "deferred"
