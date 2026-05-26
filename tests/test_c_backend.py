from __future__ import annotations

import ctypes
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

import pytest

from amiga_reversing import reversing_loop
from amiga_reversing.disasm import c_backend, decision_journal
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    DiskEntryBinarySource,
    HunkFileBinarySource,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    FactsV2DirectRebuildRefused,
    amiga_naming_catalog_with_c_backend,
    amiga_os_metadata_catalog_with_c_backend,
    analyze_binary_source_with_c_backend,
    analyze_project_source_with_c_backend,
    api_calls_from_c_analysis,
    assemble_platform_source_path_with_c_backend,
    assemble_platform_source_text_with_c_backend,
    benchmark_project_source_with_text_from_c_backend,
    decompress_packed_range_with_c_backend,
    decompress_packed_section_range_with_c_backend,
    effective_policy_project_source_with_c_backend,
    extract_disk_entry_with_c_backend,
    facts_v2_direct_rebuild_project_source_with_c_backend_profile,
    identify_packed_range_with_c_backend,
    inspect_disk_with_c_backend,
    listing_artifact_source_text_with_c_backend_profile,
    materialize_recognized_unpacker_event_with_c_backend,
    materialize_self_decrunch_event_with_c_backend,
    render_binary_source_with_c_backend,
    render_project_source_with_c_backend,
    reproduction_compare_rebuilt_bytes_with_c_backend_profile,
    validate_amiga_hunk_executable_with_c_backend,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.facts_v2_source_refusal import FactsV2SourceRefused
from amiga_reversing.disasm.listing_context import listing_element_contexts
from amiga_reversing.disasm.manual_action_catalog import listing_element_action_catalog
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    build_target_identity,
)
from amiga_reversing.disasm.project_paths import (
    PROJECT_ROOT,
    ProjectPaths,
    resolve_project_paths,
)
from amiga_reversing.disasm.target_metadata import (
    SeededEntityMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    write_target_metadata,
    write_target_seeded_metadata,
)
from src.tests._platform_backend_test_utils import (
    M68kDiagList,
    make_synthetic_atari_prg,
    make_synthetic_hunkexe,
    u32,
)
from tests.c_backend_listing_rows import (
    analyze_project_with_c_artifact,
    analyze_source_with_c_artifact,
    build_project_listing_rows_from_source_with_c_artifact,
    build_project_listing_rows_profile_with_c_artifact,
    build_project_listing_rows_with_c_artifact,
)


def _requires_c_backend_dlls() -> None:
    build_dir = PROJECT_ROOT / "src" / "build"
    if not (build_dir / "platform_file_lib.dll").exists() or not (build_dir / "platform_disk_lib.dll").exists():
        pytest.skip("C backend DLLs are missing; run cmd /c src\\build.bat")


def _requires_project_paths(target_name: str) -> ProjectPaths:
    try:
        return resolve_project_paths(target_name, project_root=PROJECT_ROOT)
    except FileNotFoundError as exc:
        pytest.skip(f"Target fixture is not materialized by the current import policy: {target_name} ({exc})")


def test_020_006_amiga_listing_keeps_shared_data_range_out_of_instruction_rows(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "shared_ranges.hunk"
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=bytes.fromhex("4e750000"), data_data=bytes.fromhex("4e750000")))
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "shared_ranges.analysis",
    )

    rows, _api_calls, profile = build_project_listing_rows_from_source_with_c_artifact(
        source,
        metadata_text="",
        project_root=PROJECT_ROOT,
    )

    assert profile["facts_v2"]["asm_source_refused"] is False
    assert any(row.get("section_index") == 0 and row.get("kind") == "instruction" for row in rows)
    assert not any(row.get("section_index") == 1 and row.get("kind") == "instruction" for row in rows)
    assert any(row.get("section_index") == 1 and row.get("kind") == "data" for row in rows)


def test_020_006_atari_listing_keeps_shared_data_bss_ranges_out_of_instruction_rows(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "shared_ranges.prg"
    binary_path.write_bytes(
        make_synthetic_atari_prg(
            text=bytes.fromhex("4e75"),
            data=bytes.fromhex("4e75"),
            bss_size=4,
            reloc_offsets=[],
        )
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "shared_ranges_atari.analysis",
    )

    rows, _api_calls, profile = build_project_listing_rows_from_source_with_c_artifact(
        source,
        metadata_text="",
        project_root=PROJECT_ROOT,
    )

    assert profile["facts_v2"]["asm_source_refused"] is False
    assert any(row.get("section_index") == 0 and row.get("kind") == "instruction" for row in rows)
    assert not any(row.get("section_index") in {1, 2} and row.get("kind") == "instruction" for row in rows)
    assert any(row.get("section_index") == 1 and row.get("kind") == "data" for row in rows)
    assert any(row.get("section_index") == 2 and row.get("kind") == "data" for row in rows)


def test_020_007_amiga_analysis_imports_shared_executable_ranges(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "analysis_ranges.hunk"
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=bytes.fromhex("4e750000"), data_data=bytes.fromhex("4e750000")))
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "analysis_ranges.analysis",
    )

    combined = analyze_source_with_c_artifact(source, metadata_text="", project_root=PROJECT_ROOT)
    ranges = {item["role"]: item for item in combined["analysis"]["executable_ranges"]}
    ownership = {item["role"]: item for item in combined["analysis"]["source_ownership_ranges"]}

    assert combined["analysis"]["executable_model"] == "platform_executable_summary_v1"
    assert combined["analysis"]["restored_source_model"] == "restored_source_model_v1"
    assert combined["analysis"]["round_trip_required"] is True
    assert ranges["code"]["fact_id"] == "amiga.hunk.code_data_bss.sections.accepted"
    assert ranges["data"]["parser_use"] == "accepted_parser_output"
    assert ranges["data"]["stored_offset"] == 4
    assert ownership["code"]["byte_space"] == "loaded_image"
    assert ownership["data"]["start"] == ranges["data"]["load_offset"]
    assert set(ownership) == set(ranges)
    assert combined["analysis"]["executable_deferred"] == [
        {
            "kind": "runtime_entry",
            "status": "deferred",
            "fact_id": "amiga.hunk.runtime_entry.deferred",
            "fact_status": "deferred",
            "parser_use": "deferred_only",
        }
    ]


def test_020_007_atari_analysis_imports_candidate_bss_without_promotion(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "analysis_ranges.prg"
    binary_path.write_bytes(make_synthetic_atari_prg(text=bytes.fromhex("4e75"), data=b"\0\0", bss_size=4, reloc_offsets=[]))
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "analysis_ranges_atari.analysis",
    )

    combined = analyze_source_with_c_artifact(source, metadata_text="", project_root=PROJECT_ROOT)
    ranges = {item["role"]: item for item in combined["analysis"]["executable_ranges"]}
    ownership = {item["role"]: item for item in combined["analysis"]["source_ownership_ranges"]}

    assert combined["analysis"]["executable_model"] == "platform_executable_summary_v1"
    assert combined["analysis"]["restored_source_model"] == "restored_source_model_v1"
    assert combined["analysis"]["round_trip_required"] is True
    assert ranges["bss"]["stored_offset"] is None
    assert ranges["bss"]["fact_status"] == "candidate"
    assert ranges["bss"]["parser_use"] == "candidate_only"
    assert ownership["bss"]["fact_status"] == "candidate"
    assert ownership["bss"]["parser_use"] == "candidate_only"
    assert combined["analysis"]["executable_deferred"] == [
        {
            "kind": "relocation_breadth",
            "status": "deferred",
            "fact_id": "atari_st.prg.relocation_terminator_variants.deferred",
            "fact_status": "deferred",
            "parser_use": "deferred_only",
        }
    ]


def test_load_dll_resolves_relative_project_root_for_windows_dll_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    build_dir = tmp_path / "src" / "build"
    build_dir.mkdir(parents=True)
    dll_path = build_dir / "platform_file_lib.dll"
    dll_path.write_bytes(b"")
    added_dirs: list[str] = []
    loaded_paths: list[str] = []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        c_backend.os,
        "add_dll_directory",
        lambda path: added_dirs.append(path) or object(),
        raising=False,
    )
    monkeypatch.setattr(c_backend, "CDLL", lambda path: loaded_paths.append(path) or object())

    c_backend._load_dll(Path("."), dll_path.name)

    assert added_dirs == [str(build_dir.resolve())]
    assert loaded_paths == [str(dll_path.resolve())]


def _amiga_hunk_section_hexes(path: Path) -> list[str]:
    inspector = PROJECT_ROOT / "src" / "build" / "platform_file_cli.exe"
    result = subprocess.run(
        [str(inspector), "inspect-file", "amiga-hunk", str(path)],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return [section["data_hex"] for section in json.loads(result.stdout)["sections"]]


def test_decompression_c_backend_reports_unknown_payload(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    payload = tmp_path / "unknown.bin"
    output = tmp_path / "unknown.out"
    payload.write_bytes(b"not packed")

    identified = identify_packed_range_with_c_backend(payload, 0, payload.stat().st_size)
    assert identified["status"] == "ok"
    packed_payload = identified["packed_payloads"][0]
    assert packed_payload["found"] is False
    assert len(packed_payload["provider_sha256"]) == 64
    assert len(packed_payload["source_sha256"]) == 64

    decompressed = decompress_packed_range_with_c_backend(payload, 0, payload.stat().st_size, output)
    assert decompressed["status"] == "ok"
    assert decompressed["packed_payloads"][0]["found"] is False
    assert not output.exists()


def test_analysis_json_includes_empty_decompression_fact_arrays(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "plain_hunk.bin"
    binary.write_bytes(_make_cross_section_call_hunkexe(bytes.fromhex("4e75"), 0))

    analysis = analyze_binary_source_with_c_backend(binary)

    assert analysis["packed_payloads"] == []
    assert analysis["derived_target_suggestions"] == []
    assert analysis["decompression_events"] == []


def test_listing_analysis_json_includes_empty_decompression_fact_arrays(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "plain_hunk.bin"
    binary.write_bytes(_make_cross_section_call_hunkexe(bytes.fromhex("4e75"), 0))

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )

    assert combined["analysis"]["packed_payloads"] == []
    assert combined["analysis"]["derived_target_suggestions"] == []
    assert combined["analysis"]["decompression_events"] == []


def test_listing_analysis_reports_unsupported_self_decruncher_without_materialising_payload(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "self_decrunch_hunk.bin"
    source = """    SECTION section,code
    lea.l $4000.l,a0
    move.b #$4E,(a0)+
    move.b #$75,(a0)+
    jmp $4000.l
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )

    assert combined["analysis"]["packed_payloads"] == []
    assert combined["analysis"]["derived_target_suggestions"] == []
    events = combined["analysis"]["decompression_events"]
    assert len(events) == 1
    event = events[0]
    assert event["source_kind"] == "self_decruncher"
    assert event["provider_id"] == "m68k-sim-decrunch"
    assert event["codec_support"] == "simulator_required"
    assert event["status"] == "simulated_output_observed"
    assert event["reason"] == "simulated_pc_range_stop"
    assert event["payload_role"] == "unknown_runtime_payload"
    assert event["payload_role_confidence"] == "observed_output_only"
    assert event["decompressor_code_section"] == 0
    assert event["decompressor_entry_offset"] == 0
    assert event["transfer_offset"] == 14
    assert event["load_address"] == 0x4000
    assert event["entrypoint"] == 0x4000
    assert event["observed_write_start"] == 0x4000
    assert event["observed_write_end"] == 0x4002
    assert event["observed_write_count"] == 2
    assert event["simulated_stop_reason"] == 1
    assert event["simulated_write_count"] == 2
    assert event["simulated_output_start"] == 0x4000
    assert event["simulated_output_end"] == 0x4002
    assert event["simulated_output_size"] == 2
    assert event["simulated_output_sha256"] == hashlib.sha256(bytes.fromhex("4e75")).hexdigest()


def test_c_backend_materializes_simulated_self_decrunch_event_output(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "materialize_self_decrunch_hunk.bin"
    output_path = tmp_path / "materialized.bin"
    source = """    SECTION section,code
    lea.l $4000.l,a0
    move.b #$4E,(a0)+
    move.b #$75,(a0)+
    jmp $4000.l
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )

    analysis = analyze_binary_source_with_c_backend(binary, project_root=PROJECT_ROOT)
    event = analysis["decompression_events"][0]
    result = materialize_self_decrunch_event_with_c_backend(
        "amiga-hunk",
        binary,
        event["event_id"],
        output_path,
        project_root=PROJECT_ROOT,
    )

    assert result["status"] == "ok"
    assert output_path.read_bytes() == bytes.fromhex("4e75")
    assert result["decompressed"]["sha256"] == hashlib.sha256(bytes.fromhex("4e75")).hexdigest()
    materialized_event = result["decompression_events"][0]
    assert materialized_event["event_id"] == event["event_id"]
    assert materialized_event["status"] == "simulated_output_observed"
    assert materialized_event["payload_role"] == "unknown_runtime_payload"


def test_listing_analysis_identifies_tetragon_unpacker_markers_in_multiple_sections(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "tetragon_markers_hunk.bin"
    marker = "$20,$54,$45,$54,$52,$41,$47,$4F,$4E,$20"
    source = f"""    SECTION entry,code
    jsr first_start.l
    jsr second_start.l
    rts
    dc.w 0
    SECTION first,code
    bra.b first_start
    dc.b {marker}
first_start:
    moveq.l #$11,d7
    lea.l $40000.l,a0
    lea.l $50000.l,a2
    lea.l $4F92B.l,a1
    jmp $40000.l
first_payload:
    dc.w 0
    dc.w 0
    dc.w 0
    dc.w 0
    dc.w 0
    SECTION second,code
    bra.b second_start
    dc.b {marker}
second_start:
    moveq.l #-83,d7
    lea.l $1000.l,a0
    lea.l $7FFFF.l,a2
    lea.l $130B6.l,a1
    jmp $59484.l
second_payload:
    dc.w 0
    dc.w 0
    dc.w 0
    dc.w 0
    dc.w 0
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )

    analysis = analyze_binary_source_with_c_backend(binary, project_root=PROJECT_ROOT)
    events = [event for event in analysis["decompression_events"] if event.get("codec_id") == "tetragon"]

    assert len(events) == 2
    by_section = {event["source_section"]: event for event in events}
    assert by_section[1]["source_kind"] == "recognized_unpacker"
    assert by_section[1]["provider_id"] == "c-tetragon-signature"
    assert by_section[1]["status"] == "identified"
    assert by_section[1]["source_section_offset"] > by_section[1]["unpacker_marker_offset"]
    assert by_section[1]["compressed_source_section_offset"] == by_section[1]["source_section_offset"]
    assert by_section[1]["compressed_source_section_end_offset"] > by_section[1]["compressed_source_section_offset"]
    assert by_section[1]["target_start_address"] == 0x40000
    assert by_section[1]["postpass_source_start_address"] > by_section[1]["target_start_address"]
    assert by_section[1]["postpass_source_end_address"] == 0x50000
    assert by_section[1]["postpass_escape_byte"] == 0x11
    assert by_section[1]["entrypoint"] == 0x40000
    assert by_section[2]["source_section_offset"] > by_section[2]["unpacker_marker_offset"]
    assert by_section[2]["compressed_source_section_offset"] == by_section[2]["source_section_offset"]
    assert by_section[2]["compressed_source_section_end_offset"] > by_section[2]["compressed_source_section_offset"]
    assert by_section[2]["target_start_address"] == 0x1000
    assert by_section[2]["postpass_source_start_address"] > by_section[2]["target_start_address"]
    assert by_section[2]["postpass_source_end_address"] == 0x7FFFF
    assert by_section[2]["postpass_escape_byte"] == 0xAD
    assert by_section[2]["entrypoint"] == 0x59484


def test_listing_analysis_bounds_simulated_self_decruncher_output_to_transfer_range(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "scratch_write_self_decrunch_hunk.bin"
    source = """    SECTION section,code
    move.w #$FFFF,$3000.l
    lea.l $4000.l,a0
    move.b #$4E,(a0)+
    move.b #$75,(a0)+
    jmp $4000.l
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    events = combined["analysis"]["decompression_events"]

    assert len(events) == 1
    event = events[0]
    assert event["status"] == "simulated_output_observed"
    assert event["simulated_write_count"] == 3
    assert event["simulated_output_start"] == 0x4000
    assert event["simulated_output_end"] == 0x4002
    assert event["simulated_output_size"] == 2
    assert event["simulated_output_sha256"] == hashlib.sha256(bytes.fromhex("4e75")).hexdigest()


def test_listing_analysis_simulates_self_decruncher_across_amiga_hardware_write(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "hardware_write_self_decrunch_hunk.bin"
    source = """    SECTION section,code
    moveq.l #0,d0
    lea.l $4000.l,a0
    move.w d0,($DFF180).l
    move.b #$4E,(a0)+
    move.b #$75,(a0)+
    jmp $4000.l
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    events = combined["analysis"]["decompression_events"]

    assert len(events) == 1
    event = events[0]
    assert event["status"] == "simulated_output_observed"
    assert event["simulated_write_count"] == 2
    assert event["simulated_output_start"] == 0x4000
    assert event["simulated_output_end"] == 0x4002
    assert event["simulated_output_sha256"] == hashlib.sha256(bytes.fromhex("4e75")).hexdigest()


def test_listing_analysis_simulates_self_decruncher_after_branch_over_embedded_data(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "bridged_self_decrunch_hunk.bin"
    source = """    SECTION section,code
    lea.l payload(pc),a1
    bra.b stage
    dc.b $54,$45,$53,$54
stage:
    lea.l $4000.l,a0
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    jmp $4000.l
payload:
    dc.b $4E,$75
    dc.w 0
    dc.w 0
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    events = [
        event
        for event in combined["analysis"]["decompression_events"]
        if event.get("source_kind") == "self_decruncher"
    ]

    assert len(events) == 1
    event = events[0]
    assert event["status"] == "simulated_output_observed"
    assert event["decompressor_entry_offset"] == 0
    assert event["simulated_output_start"] == 0x4000
    assert event["simulated_output_end"] == 0x4002
    assert event["simulated_output_sha256"] == hashlib.sha256(bytes.fromhex("4e75")).hexdigest()


def test_listing_analysis_simulates_self_decruncher_from_reachable_section_root(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "rooted_self_decrunch_hunk.bin"
    metadata_path = tmp_path / "target_metadata.json"
    source = """    SECTION section,code
    bra.b stage
helper:
    rts
    dc.b $54,$45,$53,$54
stage:
    lea.l payload(pc),a1
    lea.l $4000.l,a0
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    jmp $4000.l
payload:
    dc.b $4E,$75
    dc.w 0
    dc.w 0
    dc.w 0
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )
    metadata_path.write_text(
        json.dumps({"seeded_code_entrypoints": [{"hunk": 0, "addr": 2}]}),
        encoding="utf-8",
    )

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )
    events = [
        event
        for event in combined["analysis"]["decompression_events"]
        if event.get("source_kind") == "self_decruncher"
    ]

    assert len(events) == 1
    event = events[0]
    assert event["status"] == "simulated_output_observed"
    assert event["decompressor_entry_offset"] == 0
    assert event["transfer_offset"] > event["decompressor_entry_offset"]
    assert event["simulated_output_start"] == 0x4000
    assert event["simulated_output_end"] == 0x4002
    assert event["simulated_output_sha256"] == hashlib.sha256(bytes.fromhex("4e75")).hexdigest()


def test_listing_analysis_simulates_self_decruncher_when_written_bytes_match_existing_memory(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "same_bytes_self_decrunch_hunk.bin"
    source = """    SECTION section,code
    lea.l $4000.l,a0
    move.b #0,(a0)+
    move.b #0,(a0)+
    jmp $4000.l
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    events = combined["analysis"]["decompression_events"]

    assert len(events) == 1
    event = events[0]
    assert event["status"] == "simulated_output_observed"
    assert event["simulated_write_count"] == 2
    assert event["simulated_output_start"] == 0x4000
    assert event["simulated_output_end"] == 0x4002
    assert event["simulated_output_sha256"] == hashlib.sha256(bytes(2)).hexdigest()


def test_listing_analysis_simulates_self_decruncher_with_runtime_mapped_source(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "mapped_source_self_decrunch_hunk.bin"
    metadata_path = tmp_path / "target_metadata.json"
    source = """    SECTION section,code
    moveq.l #0,d0
    lea.l $50000.l,a1
    lea.l $40000.l,a0
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    jmp $40000.l
payload:
    dc.b $12,$34
    dc.w 0
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )
    metadata_path.write_text(
        json.dumps({"execution_views": [{"source_start": 0x18, "source_end": 0x1A, "base_addr": 0x50000}]}),
        encoding="utf-8",
    )

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )
    events = [
        event
        for event in combined["analysis"]["decompression_events"]
        if event.get("source_kind") == "self_decruncher"
    ]

    assert len(events) == 1
    event = events[0]
    assert event["status"] == "simulated_output_observed"
    assert event["reason"] == "simulated_pc_range_stop"
    assert event["decompressor_code_section"] == 0
    assert event["decompressor_entry_offset"] == 0
    assert event["load_address"] == 0x40000
    assert event["entrypoint"] == 0x40000
    assert event["simulated_output_start"] == 0x40000
    assert event["simulated_output_end"] == 0x40002
    assert event["simulated_output_size"] == 2
    assert event["simulated_write_count"] == 2
    assert event["simulated_output_sha256"] == hashlib.sha256(bytes.fromhex("1234")).hexdigest()


def test_listing_analysis_simulates_self_decruncher_with_absolute_source_mirror(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "absolute_source_mirror_self_decrunch_hunk.bin"
    source = """    SECTION section,code
    lea.l $00040016.l,a1
    lea.l $00040000.l,a0
    move.b (a1)+,(a0)+
    move.b (a1)+,(a0)+
    jmp $40000.l
payload:
    dc.b $12,$34
    dc.w 0
    dc.w 0
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    events = [
        event
        for event in combined["analysis"]["decompression_events"]
        if event.get("source_kind") == "self_decruncher"
    ]

    assert len(events) == 1
    event = events[0]
    assert event["status"] == "simulated_output_observed"
    assert event["reason"] == "simulated_pc_range_stop"
    assert event["decompressor_entry_offset"] == 0
    assert event["load_address"] == 0x40000
    assert event["entrypoint"] == 0x40000
    assert event["simulated_output_start"] == 0x40000
    assert event["simulated_output_end"] == 0x40002
    assert event["simulated_output_sha256"] == hashlib.sha256(bytes.fromhex("1234")).hexdigest()


def test_analysis_decompression_skips_candidate_overlapping_accepted_code(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "overlap_hunk.bin"
    code = bytearray(b"\x4e\x71")
    code += b"RNC\x01"
    code += b"\x00" * 14
    binary.write_bytes(make_synthetic_hunkexe(code_data=bytes(code)))

    analysis = analyze_binary_source_with_c_backend(binary)

    assert analysis["sections"][0]["blocks"][0]["start_offset"] == 0
    assert analysis["sections"][0]["blocks"][0]["end_offset"] == 4
    assert analysis["packed_payloads"] == []
    assert analysis["derived_target_suggestions"] == []
    assert analysis["decompression_events"] == []


def test_decompression_c_backend_section_range_reports_unknown_payload(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "plain_hunk.bin"
    output = tmp_path / "plain.out"
    binary.write_bytes(_make_cross_section_call_hunkexe(bytes.fromhex("4e75"), 0))

    decompressed = decompress_packed_section_range_with_c_backend("amiga-hunk", binary, 0, 0, 8, output)

    assert decompressed["status"] == "ok"
    assert decompressed["packed_payloads"][0]["found"] is False
    assert decompressed["packed_payloads"][0]["source_section"] == 0
    assert decompressed["packed_payloads"][0]["source_section_offset"] == 0
    assert not output.exists()


def _facts_v2_listing_analysis_for_project(target_name: str) -> dict[str, object]:
    _requires_project_paths(target_name)
    payload = analyze_project_with_c_artifact(target_name, project_root=PROJECT_ROOT)
    assert isinstance(payload, dict)
    return payload


def _make_cross_section_call_hunkexe(second_code: bytes, target_offset: int) -> bytes:
    hunk_header = 1011
    hunk_code = 1001
    hunk_reloc32 = 1004
    hunk_end = 1010
    first_code = bytes.fromhex("4eb9") + u32(target_offset) + bytes.fromhex("4e75")
    payload = bytearray()
    payload += u32(hunk_header)
    payload += u32(0)
    payload += u32(2)
    payload += u32(0)
    payload += u32(1)
    payload += u32((len(first_code) + 3) // 4)
    payload += u32((len(second_code) + 3) // 4)
    payload += u32(hunk_code)
    payload += u32((len(first_code) + 3) // 4)
    payload += first_code.ljust(((len(first_code) + 3) // 4) * 4, b"\x00")
    payload += u32(hunk_reloc32)
    payload += u32(1)
    payload += u32(1)
    payload += u32(2)
    payload += u32(0)
    payload += u32(hunk_end)
    payload += u32(hunk_code)
    payload += u32((len(second_code) + 3) // 4)
    payload += second_code.ljust(((len(second_code) + 3) // 4) * 4, b"\x00")
    payload += u32(hunk_end)
    return bytes(payload)


def _make_cross_section_pc_relative_call_hunkexe(second_code: bytes, target_offset: int) -> bytes:
    hunk_header = 1011
    hunk_code = 1001
    hunk_reloc16 = 1005
    hunk_end = 1010
    first_code = bytes.fromhex("4eba") + ((target_offset - 2) & 0xFFFF).to_bytes(2, "big") + bytes.fromhex("4e75")
    payload = bytearray()
    payload += u32(hunk_header)
    payload += u32(0)
    payload += u32(2)
    payload += u32(0)
    payload += u32(1)
    payload += u32((len(first_code) + 3) // 4)
    payload += u32((len(second_code) + 3) // 4)
    payload += u32(hunk_code)
    payload += u32((len(first_code) + 3) // 4)
    payload += first_code.ljust(((len(first_code) + 3) // 4) * 4, b"\x00")
    payload += u32(hunk_reloc16)
    payload += u32(1)
    payload += u32(1)
    payload += u32(2)
    payload += u32(0)
    payload += u32(hunk_end)
    payload += u32(hunk_code)
    payload += u32((len(second_code) + 3) // 4)
    payload += second_code.ljust(((len(second_code) + 3) // 4) * 4, b"\x00")
    payload += u32(hunk_end)
    return bytes(payload)


def _make_cross_section_jump_template_table_hunkexe() -> bytes:
    hunk_header = 1011
    hunk_code = 1001
    hunk_data = 1002
    hunk_reloc32 = 1004
    hunk_end = 1010
    code_data = bytes.fromhex("4e754e75")
    data_data = bytes.fromhex("4ef9000000004ef900000002")
    payload = bytearray()
    payload += u32(hunk_header)
    payload += u32(0)
    payload += u32(2)
    payload += u32(0)
    payload += u32(1)
    payload += u32((len(code_data) + 3) // 4)
    payload += u32((len(data_data) + 3) // 4)
    payload += u32(hunk_code)
    payload += u32((len(code_data) + 3) // 4)
    payload += code_data.ljust(((len(code_data) + 3) // 4) * 4, b"\x00")
    payload += u32(hunk_end)
    payload += u32(hunk_data)
    payload += u32((len(data_data) + 3) // 4)
    payload += data_data.ljust(((len(data_data) + 3) // 4) * 4, b"\x00")
    payload += u32(hunk_reloc32)
    payload += u32(2)
    payload += u32(0)
    payload += u32(2)
    payload += u32(8)
    payload += u32(0)
    payload += u32(hunk_end)
    return bytes(payload)


class _M68kDiagSink(ctypes.Structure):
    _fields_ = [("list", ctypes.POINTER(M68kDiagList))]


class _M68kAnalysisRegisterSeed(ctypes.Structure):
    _fields_ = [
        ("platform_kind", ctypes.c_uint8),
        ("kind", ctypes.c_uint8),
        ("reg_kind", ctypes.c_uint8),
        ("reg_index", ctypes.c_uint8),
        ("has_entry_offset", ctypes.c_uint8),
        ("has_section_index", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 2),
        ("entry_offset", ctypes.c_uint32),
        ("section_index", ctypes.c_uint32),
        ("name", ctypes.c_char * 64),
        ("type_name", ctypes.c_char * 64),
        ("context_name", ctypes.c_char * 64),
    ]


class _M68kAnalysisEntryPoint(ctypes.Structure):
    _fields_ = [
        ("has_section_index", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("section_index", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
    ]


class _M68kAnalysisStructuredDataItem(ctypes.Structure):
    _fields_ = [
        ("has_section_index", ctypes.c_uint8),
        ("kind", ctypes.c_uint8),
        ("is_pointer", ctypes.c_uint8),
        ("has_target", ctypes.c_uint8),
        ("section_index", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("target_section", ctypes.c_uint32),
        ("target_offset", ctypes.c_uint32),
        ("has_constant_value", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("constant_value", ctypes.c_int32),
        ("has_consumer", ctypes.c_uint8),
        ("source_pattern_id", ctypes.c_uint8),
        ("table_kind_id", ctypes.c_uint8),
        ("table_base_expression_id", ctypes.c_uint8),
        ("table_conflicted", ctypes.c_uint8),
        ("table_conflict_state", ctypes.c_uint8),
        ("platform_kind_id", ctypes.c_uint16),
        ("platform_field_id", ctypes.c_uint16),
        ("struct_id", ctypes.c_uint16),
        ("field_id", ctypes.c_uint16),
        ("pointer_struct_id", ctypes.c_uint16),
        ("consumer_section", ctypes.c_uint32),
        ("consumer_offset", ctypes.c_uint32),
        ("semantic_role_flags", ctypes.c_uint32),
        ("label", ctypes.c_char * 64),
        ("struct_name", ctypes.c_char * 64),
        ("field_name", ctypes.c_char * 64),
        ("field_type", ctypes.c_char * 64),
        ("c_type", ctypes.c_char * 64),
        ("pointer_struct", ctypes.c_char * 64),
        ("value_domain", ctypes.c_char * 64),
        ("constant_name", ctypes.c_char * 64),
        ("semantic_role", ctypes.c_char * 64),
        ("source_pattern", ctypes.c_char * 64),
        ("comment", ctypes.c_char * 96),
    ]


class _M68kAnalysisNamedLabel(ctypes.Structure):
    _fields_ = [
        ("has_section_index", ctypes.c_uint8),
        ("domain", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 2),
        ("section_index", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("name", ctypes.c_char * 64),
    ]


class _M68kAnalysisEntryComment(ctypes.Structure):
    _fields_ = [
        ("has_section_index", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("section_index", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("comment", ctypes.c_char * 192),
    ]


class _M68kAnalysisRuntimeRange(ctypes.Structure):
    _fields_ = [
        ("has_section_index", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("section_index", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("runtime_address", ctypes.c_uint32),
        ("name", ctypes.c_char * 64),
    ]


class _M68kAnalysisRuntimeEntryPoint(ctypes.Structure):
    _fields_ = [
        ("has_section_index", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("section_index", ctypes.c_uint32),
        ("runtime_address", ctypes.c_uint32),
    ]


class _M68kAnalysisRssetLayoutRegion(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_uint32),
        ("size", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
        ("storage_kind_id", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 1),
        ("layout_name", ctypes.c_char * 32),
        ("base_symbol", ctypes.c_char * 64),
        ("sizeof_symbol", ctypes.c_char * 64),
        ("symbol", ctypes.c_char * 64),
        ("struct_name", ctypes.c_char * 64),
        ("pointer_struct", ctypes.c_char * 64),
        ("storage_kind", ctypes.c_char * 32),
        ("semantic_type", ctypes.c_char * 64),
    ]


class _M68kAnalysisRssetUseSiteBinding(ctypes.Structure):
    _fields_ = [
        ("section_index", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("displacement", ctypes.c_uint32),
        ("operand_index", ctypes.c_uint8),
        ("base_reg", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 2),
        ("layout_name", ctypes.c_char * 32),
        ("base_symbol", ctypes.c_char * 64),
        ("base_evidence_id", ctypes.c_char * 96),
        ("binding_id", ctypes.c_char * 256),
        ("owner_action_id", ctypes.c_char * 96),
    ]


class _M68kAnalysisManualRepresentation(ctypes.Structure):
    _fields_ = [
        ("has_section_index", ctypes.c_uint8),
        ("style_id", ctypes.c_uint8),
        ("has_operand_index", ctypes.c_uint8),
        ("operand_index", ctypes.c_uint8),
        ("symbol_id", ctypes.c_uint16),
        ("target_equate_index", ctypes.c_uint16),
        ("section_index", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
    ]


class _M68kAnalysisTargetEquate(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 64),
        ("value", ctypes.c_int32),
        ("value_style_id", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("value_expr", ctypes.c_char * 64),
    ]


class _M68kAnalysisManualRuntimeAddressRef(ctypes.Structure):
    _fields_ = [
        ("has_section_index", ctypes.c_uint8),
        ("has_target", ctypes.c_uint8),
        ("has_runtime_address", ctypes.c_uint8),
        ("confidence", ctypes.c_uint8),
        ("section_index", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("target_section_index", ctypes.c_uint32),
        ("target_offset", ctypes.c_uint32),
        ("runtime_address", ctypes.c_uint32),
        ("owner_element_offset", ctypes.c_uint32),
        ("owner_kind", ctypes.c_char * 32),
        ("owner_id", ctypes.c_char * 96),
        ("owner_layout_id", ctypes.c_char * 64),
        ("xref_generation_mode", ctypes.c_char * 32),
    ]


class _M68kAnalysisCustomStructField(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 64),
        ("type_name", ctypes.c_char * 64),
        ("offset", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("struct_name", ctypes.c_char * 64),
        ("pointer_struct", ctypes.c_char * 64),
        ("named_base", ctypes.c_char * 64),
    ]


class _M68kAnalysisCustomStruct(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 64),
        ("size", ctypes.c_uint32),
        ("field_count", ctypes.c_uint16),
        ("reserved", ctypes.c_uint16),
        ("fields", _M68kAnalysisCustomStructField * 32),
    ]


class _M68kAnalysisPolicy(ctypes.Structure):
    _fields_ = [
        ("max_cpu", ctypes.c_uint8),
        ("has_entry_offset", ctypes.c_uint8),
        ("disable_implicit_entry_points", ctypes.c_uint8),
        ("reserved0", ctypes.c_uint8 * 1),
        ("register_seed_count", ctypes.c_uint16),
        ("entry_point_count", ctypes.c_uint16),
        ("structured_data_item_count", ctypes.c_uint16),
        ("named_label_count", ctypes.c_uint16),
        ("entry_comment_count", ctypes.c_uint16),
        ("runtime_range_count", ctypes.c_uint16),
        ("runtime_entry_point_count", ctypes.c_uint16),
        ("rsset_layout_region_count", ctypes.c_uint16),
        ("rsset_use_site_binding_count", ctypes.c_uint16),
        ("manual_representation_count", ctypes.c_uint16),
        ("target_equate_count", ctypes.c_uint16),
        ("manual_runtime_address_ref_count", ctypes.c_uint16),
        ("custom_struct_count", ctypes.c_uint16),
        ("custom_struct_capacity", ctypes.c_uint16),
        ("custom_struct_owner", ctypes.c_uint8),
        ("reserved1", ctypes.c_uint8 * 1),
        ("entry_offset", ctypes.c_uint32),
        ("register_seeds", _M68kAnalysisRegisterSeed * 64),
        ("entry_points", _M68kAnalysisEntryPoint * 64),
        ("structured_data_items", _M68kAnalysisStructuredDataItem * 256),
        ("named_labels", _M68kAnalysisNamedLabel * 128),
        ("entry_comments", _M68kAnalysisEntryComment * 128),
        ("runtime_ranges", _M68kAnalysisRuntimeRange * 64),
        ("runtime_entry_points", _M68kAnalysisRuntimeEntryPoint * 64),
        ("rsset_layout_regions", _M68kAnalysisRssetLayoutRegion * 128),
        ("rsset_use_site_bindings", _M68kAnalysisRssetUseSiteBinding * 128),
        ("manual_representations", _M68kAnalysisManualRepresentation * 128),
        ("target_equates", _M68kAnalysisTargetEquate * 128),
        ("manual_runtime_address_refs", _M68kAnalysisManualRuntimeAddressRef * 128),
        ("custom_structs", ctypes.POINTER(_M68kAnalysisCustomStruct)),
    ]


def test_full_listing_data_rows_expose_source_bytes(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(b"\0" * 12 + b"\x4e\x75" + b"ABC\0")

    rows, _, _ = build_project_listing_rows_from_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=12,
            code_start_offset=12,
            display_path=str(path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    data_rows = [row for row in rows if row["kind"] == "data"]

    assert any(row["addr"] == 0 and row["bytes"] == "000000000000000000000000" for row in data_rows)
    assert any(row["addr"] == 14 and row["bytes"] == "41424300" for row in data_rows)


def test_full_listing_rows_omit_empty_optional_c_fields(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(b"\x4e\x75")

    raw_rows, _, _ = build_project_listing_rows_from_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    label = next(row for row in raw_rows if row["kind"] == "label")
    instruction = next(row for row in raw_rows if row["kind"] == "instruction")

    assert label["addr"] == 0
    assert label["entity_addr"] == 0
    assert label.get("bytes") is None
    assert instruction.get("app_slot_refs", []) == []
    assert instruction.get("typed_accesses", []) == []
    assert instruction.get("unresolved_typed_accesses", []) == []
    assert instruction.get("comment_text", "") == ""


def test_full_listing_instruction_rows_expose_symbol_operand_parts(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(bytes.fromhex("60024e754e75"))

    rows, _, _ = build_project_listing_rows_from_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    branch = next(row for row in rows if row["kind"] == "instruction" and row["addr"] == 0)

    assert branch["operand_text"] == "loc_0_00000004"
    assert branch["flow_kind"] == 2
    assert branch["flow"] == "branch"
    assert branch["control_flow_boundary"] is True
    assert branch["operand_parts"][0]["kind"] == "symbol"
    assert branch["operand_parts"][0]["text"] == "loc_0_00000004"
    assert branch["operand_parts"][0]["metadata"] == {"symbol": "loc_0_00000004"}


def test_full_listing_bit_ops_use_generated_sequential_flow_metadata(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    source_text = (
        "    SECTION section,code\n"
        "    btst #0,d0\n"
        "    bset #1,d0\n"
        "    bclr #2,d0\n"
        "    bchg #3,d0\n"
        "    rts\n"
        "    nop\n"
    )
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        project_root=PROJECT_ROOT,
    )
    path = tmp_path / "bit_ops.hunk"
    path.write_bytes(rebuilt)

    rows, _, _ = build_project_listing_rows_from_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=path,
            display_path=str(path),
            analysis_cache_path=tmp_path / "bit_ops.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    by_opcode = {
        str(row.get("opcode_or_directive", "")).split(".", 1)[0]: row
        for row in rows
        if row.get("kind") == "instruction"
    }

    for opcode in ("btst", "bset", "bclr", "bchg"):
        assert by_opcode[opcode]["flow_kind"] == 1
        assert by_opcode[opcode]["flow"] == "sequential"
        assert by_opcode[opcode]["control_flow_boundary"] is False


def test_real_dll_genam_lvo_symbol_operand_parts_expose_base_register() -> None:
    _requires_c_backend_dlls()
    rows, _api_calls, profile = build_project_listing_rows_with_c_artifact(
        "amiga_hunk_genam",
        project_root=PROJECT_ROOT,
    )
    lvo_row = next(
        row
        for row in rows
        if isinstance(row.get("api_call"), dict)
        and row["api_call"].get("library") == "exec.library"
        and row["api_call"].get("function") == "AllocMem"
        and row.get("operand_text") == "_LVOAllocMem(a6)"
    )
    operand_part = lvo_row["operand_parts"][0]

    assert operand_part["kind"] == "symbol"
    assert operand_part["text"] == "_LVOAllocMem"
    assert operand_part["base_register"] == "A6"
    assert operand_part["metadata"] == {"symbol": "_LVOAllocMem"}


def test_full_listing_instruction_rows_expose_immediate_operand_parts(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(bytes.fromhex("70054e75"))

    rows, _, _ = build_project_listing_rows_from_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    moveq = next(row for row in rows if row["kind"] == "instruction" and row["addr"] == 0)

    assert moveq["operand_parts"][0]["kind"] == "immediate"
    assert moveq["operand_parts"][0]["operand_index"] == 0
    assert moveq["operand_parts"][0]["value"] == 5
    assert moveq["operand_parts"][0]["signed_value"] == 5


def test_full_listing_runtime_copy_storage_alias_precedes_runtime_org(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    metadata_path = tmp_path / "target_metadata.json"
    path.write_bytes(
        bytes.fromhex(
            "41fa001e"
            "4ef900000080"
            "000000000000"
            "4ef900000100"
            "4e75"
            "0000000000000000"
            "4e714e75"
        )
    )
    metadata_path.write_text(
        json.dumps(
            {
                "execution_views": [
                    {"source_start": 0x10, "source_end": 0x20, "base_addr": 0x80},
                    {"source_start": 0x20, "source_end": 0x24, "base_addr": 0x100},
                ]
            }
        ),
        encoding="utf-8",
    )

    binary_source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    combined = analyze_source_with_c_artifact(binary_source, metadata_text=str(metadata_path), project_root=PROJECT_ROOT)
    assert "\tlea.l loc_0_00000020-(*+2)(pc),a0\n" in source_text
    assert "\tjmp $00000080.l\n" in source_text
    assert "loc_0_00000020:\n    ORG $100\nabs_0_00000100:\n" in source_text
    assert "    ORG $20\n" not in source_text
    assert "    ORG $80\n" not in source_text
    assert "src_0_" not in source_text
    assert "loc_0_00000020 EQU" not in source_text
    facts_v2 = source_profile["facts_v2"]
    assert facts_v2["asm_source_numeric_runtime_refs"] == 1
    assert facts_v2["asm_source_first_numeric_runtime_ref_offset"] == 4
    assert facts_v2["asm_source_first_numeric_runtime_ref_target_offset"] == 0x10
    assert facts_v2["asm_source_first_numeric_runtime_ref_runtime_address"] == 0x80
    runtime_views = combined["analysis"]["sections"][0]["runtime_views"]
    runtime_view_0_expected = {
        "runtime_view_id": 0,
        "storage_address": 0x10,
        "storage_offset": 0x10,
        "size": 0x10,
        "runtime_address": 0x80,
        "kind": 1,
        "confidence": 3,
        "materialized": False,
        "materialization_reason": 102,
        "materialization_reason_name": "crossed_by_storage_xref",
    }
    runtime_view_1_expected = {
        "runtime_view_id": 1,
        "storage_address": 0x20,
        "storage_offset": 0x20,
        "size": 0x04,
        "runtime_address": 0x100,
        "kind": 1,
        "confidence": 3,
        "materialized": True,
        "materialization_reason": 3,
        "materialization_reason_name": "runtime_ref_target",
    }
    for key, value in runtime_view_0_expected.items():
        assert runtime_views[0][key] == value
    for key, value in runtime_view_1_expected.items():
        assert runtime_views[1][key] == value

    rows = combined["listing"]["rows"]
    row_texts = [str(row["text"]).rstrip("\n") for row in rows]
    ref_index = next(index for index, text in enumerate(row_texts) if "lea.l loc_0_00000020-(*+2)(pc),a0" in text)
    storage_label_index = row_texts.index("loc_0_00000020:")
    org_index = row_texts.index("    ORG $100")
    runtime_label_index = row_texts.index("abs_0_00000100:")
    assert ref_index < storage_label_index < org_index < runtime_label_index
    storage_row = rows[storage_label_index]
    runtime_row = rows[runtime_label_index]
    assert storage_row["storage_address"] == 0x20
    assert storage_row["runtime_address"] == 0x100
    assert storage_row["runtime_view_id"] == 1
    assert runtime_row["storage_address"] == 0x20
    assert runtime_row["runtime_address"] == 0x100
    assert runtime_row["runtime_view_id"] == 1


def test_full_listing_contained_runtime_view_does_not_emit_second_org(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    metadata_path = tmp_path / "target_metadata.json"
    path.write_bytes(bytes.fromhex("4ef9000000804ef900000084000000004e714e754e714e75"))
    metadata_path.write_text(
        json.dumps(
            {
                "seeded_code_entrypoints": [
                    {
                        "hunk": 0,
                        "addr": 6,
                        "name": "second_runtime_ref",
                        "source_id": "test",
                        "source_path": "test",
                        "source_locator": "test",
                    }
                ],
                "execution_views": [
                    {"source_start": 0x10, "source_end": 0x18, "base_addr": 0x80},
                    {"source_start": 0x14, "source_end": 0x18, "base_addr": 0x84},
                ],
            }
        ),
        encoding="utf-8",
    )

    binary_source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )

    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert source_text.count("    ORG $80\n") == 1
    assert "    ORG $84\n" not in source_text
    assert "    ORG $14\n" not in source_text
    assert "\tjmp abs_0_00000080.l\n" in source_text
    assert "\tjmp abs_0_00000084.l\n" in source_text
    assert "abs_0_00000084:\n\tnop\n\trts\n" in source_text


def test_facts_v2_adjacent_control_stub_table_promotes_sibling_entry(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(bytes.fromhex("6000000A000000006000000A6000000A4E714E754E714E754E714E75"))

    binary_source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        metadata_path=None,
        project_root=PROJECT_ROOT,
    )

    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert "\nloc_0_00000008:\n\tbra.w loc_0_00000014\n" in source_text
    assert "\nloc_0_00000014:\n\tnop\n\trts\n" in source_text
    assert "\tdc.b $00,$00,$00,$00,$60,$00,$00,$0A\n" not in source_text


def test_facts_v2_indexed_control_stub_table_promotes_entries(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(
        bytes.fromhex(
            "7000"
            "4EBB0010"
            "4E75"
            "000000000000000000000000"
            "6008600A600C60026004"
            "4E754E714E754E714E75"
        )
    )

    binary_source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        metadata_path=None,
        project_root=PROJECT_ROOT,
    )

    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert "\tjsr loc_0_00000014(pc,d0.w)\n" in source_text
    assert "loc_0_00000014:\n\tbra.b loc_0_0000001E\n" in source_text
    assert "loc_0_00000018:\n\tbra.b loc_0_00000026\n" in source_text
    assert "loc_0_00000026:\n\trts\n" in source_text
    assert "\tdc.b $60,$08,$60,$0A,$60,$0C" not in source_text


def test_facts_v2_indexed_indirect_target_rejects_zero_padding(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(
        bytes.fromhex(
            "7000"
            "41F90000000E"
            "20700000"
            "4ED0"
            "4E75"
            "00000020"
            "00000024"
        )
        + (b"\x00" * 64)
    )

    binary_source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        metadata_path=None,
        project_root=PROJECT_ROOT,
    )
    combined = analyze_source_with_c_artifact(binary_source, metadata_text="", project_root=PROJECT_ROOT)
    section = combined["analysis"]["sections"][0]

    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert "\tjmp (a0)\n" in source_text
    assert "loc_0_00000020:\n\tori.b #0,d0\n" not in source_text
    assert not any(ref.get("offset") in {0x20, 0x24} for ref in section["code_start_refs"])


def test_facts_v2_adjacent_absolute_jmp_stub_does_not_promote_data_target(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(
        bytes.fromhex(
            "6000000A"
            "0000000000000000"
            "4EF900000024"
            "4EF900000030"
            "000000000000000000000000"
            "4E75"
            "00000000000000000000"
            "202020204A455A2053414E20202000"
        )
    )

    binary_source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        metadata_path=None,
        project_root=PROJECT_ROOT,
    )

    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert "\nloc_0_0000000C:\n\tjmp $00000024.l\n" in source_text
    assert "\nloc_0_00000012:\n\tjmp loc_0_00000030.l\n" not in source_text
    assert "\nloc_0_00000030:\n\tmove.l -(a0),d0\n" not in source_text


def test_facts_v2_traces_reglist_copied_runtime_stub(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    source = (
        "    SECTION section,code\n"
        "    lea.l stub(pc),a0\n"
        "    movem.w (a0),d0\n"
        "    lea.l $100.w,a1\n"
        "    movem.w d0,(a1)\n"
        "    jmp (a1)\n"
        "    dc.b \"skip\"\n"
        "stub:\n"
        "    rts\n"
        "    dc.b \"tail\"\n"
    )
    rebuilt, _ = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        project_root=PROJECT_ROOT,
    )
    path = tmp_path / "reglist_stub.hunk"
    path.write_bytes(rebuilt)

    binary_source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=path,
        display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        project_root=PROJECT_ROOT,
    )
    combined = analyze_source_with_c_artifact(binary_source, metadata_text="", project_root=PROJECT_ROOT)
    facts_v2 = source_profile["facts_v2"]
    stub_rows = [
        row
        for row in combined["listing"]["rows"]
        if row.get("kind") == "instruction" and row.get("opcode_or_directive") == "rts"
    ]

    assert facts_v2["asm_source_refused"] is False
    assert facts_v2["runtime_address_ranges"] >= 1
    assert "\tdc.b $73,$6B,$69,$70\n" in source_text
    assert "runtime_code_00000100\tEQU\t$100\n" in source_text
    assert "    ORG $100\n" not in source_text
    assert "    ORG $18\n" not in source_text
    assert "loc_0_00000016:\n\trts\n\tdc.b $74,$61,$69,$6C\n" in source_text
    assert any(
        ref.get("reason_name") == "control_target" and ref.get("runtime_address") == 0x100
        for row in stub_rows
        for ref in row.get("code_start_refs", [])
    )


def test_facts_v2_traces_predecrement_copied_entry_source(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    source = (
        "    SECTION section,code\n"
        "    lea.l payload_end(pc),a0\n"
        "    lea.l -$80(a7),a1\n"
        "    move.w #3,d0\n"
        "copy_loop:\n"
        "    move.b -(a0),-(a1)\n"
        "    dbf.w d0,copy_loop\n"
        "    jmp (a1)\n"
        "    dc.b \"skip\"\n"
        "payload:\n"
        "    moveq.l #2,d0\n"
        "    rts\n"
        "payload_end:\n"
    )
    rebuilt, _ = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        project_root=PROJECT_ROOT,
    )
    path = tmp_path / "predecrement_stub.hunk"
    path.write_bytes(rebuilt)

    binary_source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=path,
        display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    source_text, _source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        project_root=PROJECT_ROOT,
    )
    combined = analyze_source_with_c_artifact(binary_source, metadata_text="", project_root=PROJECT_ROOT)

    sites = combined["analysis"]["sections"][0]["recovered_indirect_sites"]
    payload_rows = [
        row
        for row in combined["listing"]["rows"]
        if row.get("section_index") == 0 and row.get("start_offset") == 0x18
    ]

    assert "\tdc.b $73,$6B,$69,$70\nloc_0_00000018:\n\tmoveq.l #2,d0\n\trts\n" in source_text
    assert not any(site["status"] == "unresolved" for site in sites)
    assert len(sites) == 1
    expected_site = {
        "offset": 0x12,
        "flow": "jump",
        "shape": "ind",
        "status": "backward_slice",
        "detail": "accepted traced indirect control target",
        "target": 0x18,
        "target_count": 1,
    }
    assert expected_site.items() <= sites[0].items()
    assert sites[0]["source_offset"] == 0x12
    assert sites[0]["source_size"] == 2
    assert sites[0]["operand_index"] == 0
    assert sites[0]["table_bounds_status"] == "none"
    assert any(
        ref.get("reason_name") == "control_target" and ref.get("source_offset") == 0x12
        for row in payload_rows
        for ref in row.get("code_start_refs", [])
    )


def test_facts_v2_listing_rejects_invalid_platform_metadata(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "sample.exe"
    metadata_path = tmp_path / "target_metadata.json"
    path.write_bytes(make_synthetic_hunkexe(code_data=bytes.fromhex("4e750000")))
    metadata_path.write_text(
        json.dumps({"target_type": "library", "resident": {"hunk": 0, "offset": 9999}}),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="target metadata range is out of range"):
        analyze_source_with_c_artifact(
            HunkFileBinarySource(
                kind=BinarySourceKind.HUNK_FILE,
                path=path,
                display_path=str(path),
                analysis_cache_path=tmp_path / "binary.analysis",
            ),
            metadata_text=str(metadata_path),
            project_root=PROJECT_ROOT,
        )


def test_relocation_backed_entry_splits_speculative_decode(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    if not assembler.exists():
        pytest.skip("m68k assembler app is missing; run cmd /c src\\build.bat")
    path = tmp_path / "cross_entry.exe"
    source_path = tmp_path / "cross_entry.s"
    rebuilt_path = tmp_path / "cross_entry.rebuilt"
    path.write_bytes(
        _make_cross_section_call_hunkexe(
            second_code=bytes.fromhex("4e7100004e754e75"),
            target_offset=4,
        )
    )

    source = render_binary_source_with_c_backend(path)
    source_path.write_text(source, encoding="ascii")

    assert "jsr loc_1_00000004.l" in source
    assert "loc_1_00000004:" in source
    assert "dc.b $4e,$71,$00,$00" in source.lower()
    assert "ori.b #$75,d0" not in source.lower()

    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "amiga-hunk",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert rebuilt_path.exists()


def test_stale_resident_vector_metadata_repaired_to_hunk_entries(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    inspector = PROJECT_ROOT / "src" / "build" / "platform_file_cli.exe"
    disk_path = PROJECT_ROOT / "resources" / "platform_amiga" / "ArgAsm1.06.adf"
    if not assembler.exists() or not inspector.exists():
        pytest.skip("C backend tools are missing; run cmd /c src\\build.bat")
    if not disk_path.exists():
        pytest.skip("ArgAsm fixture disk is missing")

    binary_path = tmp_path / "mathtrans.library"
    binary_path.write_bytes(extract_disk_entry_with_c_backend(disk_path, "libs/mathtrans.library"))
    inspect_result = subprocess.run(
        [str(inspector), "inspect-file", "amiga-hunk", str(binary_path)],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert inspect_result.returncode == 0, inspect_result.stderr
    metadata = json.loads(inspect_result.stdout)
    metadata["resident"]["autoinit"].pop("vector_entries", None)
    metadata_path = tmp_path / "stale_target_metadata.json"
    source_path = tmp_path / "mathtrans.s"
    rebuilt_path = tmp_path / "mathtrans.rebuilt"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    binary_source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "mathtrans.analysis",
    )
    source = render_project_source_with_c_backend(binary_source, metadata_path=metadata_path)
    source_path.write_text(source, encoding="utf-8")

    assert "dc.l s_p_atan" in source.lower()
    assert "\ns_p_atan:\n" in source
    assert "\ns_p_sin:\n" in source
    assert "\nh1_008E:\n" not in source

    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "amiga-hunk",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_pc_relative_relocation_backed_entry_splits_speculative_decode(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    if not assembler.exists():
        pytest.skip("m68k assembler app is missing; run cmd /c src\\build.bat")
    path = tmp_path / "pc_cross_entry.exe"
    source_path = tmp_path / "pc_cross_entry.s"
    rebuilt_path = tmp_path / "pc_cross_entry.rebuilt"
    path.write_bytes(
        _make_cross_section_pc_relative_call_hunkexe(
            second_code=bytes.fromhex("4e7100004e754e75"),
            target_offset=4,
        )
    )

    source = render_binary_source_with_c_backend(path)
    source_path.write_text(source, encoding="ascii")

    assert "jsr loc_1_00000004(pc)" in source
    assert "loc_1_00000004:" in source
    assert "dc.w $0000" in source.lower()
    assert "ori.b #$75,d0" not in source.lower()

    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "amiga-hunk",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert rebuilt_path.exists()


def test_relocation_backed_jump_template_table_is_discovered_from_data_section(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    if not assembler.exists():
        pytest.skip("m68k assembler app is missing; run cmd /c src\\build.bat")
    path = tmp_path / "jmp_template_table.exe"
    source_path = tmp_path / "jmp_template_table.s"
    rebuilt_path = tmp_path / "jmp_template_table.rebuilt"
    path.write_bytes(_make_cross_section_jump_template_table_hunkexe())

    source = render_binary_source_with_c_backend(path)
    source_path.write_text(source, encoding="ascii")

    assert "\tjmp loc_0_00000000.l\nloc_1_00000006:\n\tjmp loc_0_00000002.l\n" in source
    assert "loc_0_00000002:\n\trts\n" in source
    assert "dc.b $4e,$f9" not in source.lower()

    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "amiga-hunk",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert rebuilt_path.exists()


def test_api_calls_from_c_analysis_uses_recovered_symbols() -> None:
    api_calls = api_calls_from_c_analysis(
        {
            "sections": [
                {
                    "section_index": 0,
                    "recovered_platform_calls": [
                        {
                            "offset": 0x20,
                            "symbol_name": None,
                            "note_symbol_name": "_LVOOutput",
                            "note_base_name": "DOSBase",
                            "library_name": "dos.library",
                            "function_name": "Output",
                            "note_kind": 3,
                            "kind": 1,
                            "inputs": [
                                {
                                    "name": "file",
                                    "regs": ["D1"],
                                    "type": "BPTR",
                                    "i_struct": None,
                                    "semantic_kind": None,
                                    "value_domain": None,
                                    "source": "parsed NDK",
                                }
                            ],
                            "outputs": [
                                {
                                    "name": "handle",
                                    "regs": ["D0"],
                                    "type": "BPTR",
                                    "o_struct": None,
                                    "semantic_kind": None,
                                    "value_domain": None,
                                    "source": "parsed NDK",
                                }
                            ],
                        },
                        {
                            "offset": 0x30,
                            "symbol_name": "_LVOOpenLibrary",
                            "note_symbol_name": None,
                            "note_base_name": None,
                            "note_kind": 0,
                            "kind": 1,
                        },
                    ],
                }
            ]
        }
    )

    assert api_calls[(0, 0x20)] == {
        "library": "dos.library",
        "function": "Output",
        "note_kind": 3,
        "call_kind": 1,
        "symbol_name": None,
        "note_symbol_name": "_LVOOutput",
        "inputs": [
            {
                "name": "file",
                "regs": ["D1"],
                "type": "BPTR",
                "i_struct": None,
                "source": "parsed NDK",
                "semantic_kind": None,
                "value_domain": None,
            }
        ],
        "outputs": [
            {
                "name": "handle",
                "regs": ["D0"],
                "type": "BPTR",
                "o_struct": None,
                "source": "parsed NDK",
                "semantic_kind": None,
                "value_domain": None,
            }
        ],
    }
    assert api_calls[(0, 0x30)] == {
        "library": "unknown",
        "function": "OpenLibrary",
        "note_kind": 0,
        "call_kind": 1,
        "symbol_name": "_LVOOpenLibrary",
        "note_symbol_name": None,
        "inputs": [],
        "outputs": [],
    }


def test_api_calls_from_c_analysis_uses_c_emitted_input_metadata() -> None:
    api_calls = api_calls_from_c_analysis(
        {
            "sections": [
                {
                    "section_index": 0,
                    "recovered_platform_calls": [
                        {
                            "offset": 0x40,
                            "library_name": "intuition.library",
                            "function_name": "SetPointer",
                            "inputs": [
                                {
                                    "name": "pointer",
                                    "regs": ["A0"],
                                    "type": "struct SimpleSprite *",
                                    "i_struct": "SimpleSprite",
                                    "source": "global correction",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    )

    assert api_calls[(0, 0x40)]["inputs"] == [
        {
            "name": "pointer",
            "regs": ["A0"],
            "type": "struct SimpleSprite *",
            "i_struct": "SimpleSprite",
            "source": "global correction",
            "semantic_kind": None,
            "value_domain": None,
        }
    ]


def test_api_calls_from_c_analysis_uses_c_emitted_output_metadata() -> None:
    api_calls = api_calls_from_c_analysis(
        {
            "sections": [
                {
                    "section_index": 0,
                    "recovered_platform_calls": [
                        {
                            "offset": 0x44,
                            "library_name": "exec.library",
                            "function_name": "CreateMsgPort",
                            "outputs": [
                                {
                                    "name": "port",
                                    "regs": ["D0"],
                                    "type": "struct MsgPort *",
                                    "o_struct": "MsgPort",
                                    "value_domain": "exec.msgport",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    )

    assert api_calls[(0, 0x44)]["outputs"] == [
        {
            "name": "port",
            "regs": ["D0"],
            "type": "struct MsgPort *",
            "o_struct": "MsgPort",
            "source": "parsed NDK",
            "semantic_kind": None,
            "value_domain": "exec.msgport",
        }
    ]


def test_render_binary_source_uses_facts_v2_source(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []
    binary_path = tmp_path / "demo"

    def fake_render_project_source(source, *, project_root: Path) -> str:
        calls.append(
            {
                "source": source,
                "project_root": project_root,
            }
        )
        return "SECTION section_0,code\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend.render_project_source_with_c_backend", fake_render_project_source)

    assert (
        render_binary_source_with_c_backend(
            binary_path,
            project_root=tmp_path,
        )
        == "SECTION section_0,code\n"
    )
    assert calls[0]["project_root"] == tmp_path
    assert calls[0]["source"].path == binary_path


def test_validate_amiga_hunk_executable_uses_c_inspect(monkeypatch) -> None:
    calls: list[tuple[tuple[str, ...], object]] = []

    def fake_run(function_name: str, *args: str, project_root):
        calls.append(((function_name, *args), project_root))
        return '{"file_kind":"executable"}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_run)

    validate_amiga_hunk_executable_with_c_backend("bin/GenAm")

    assert calls == [
        (
            (
                "platform_file_inspect_path_json_alloc",
                "amiga-hunk",
                "bin/GenAm",
            ),
            PROJECT_ROOT,
        )
    ]


def test_validate_amiga_hunk_executable_rejects_non_executable(monkeypatch) -> None:
    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend._platform_file_text",
        lambda function_name, *args, project_root: '{"file_kind":"object"}',
    )

    with pytest.raises(ValueError, match="Uploaded media is not an Amiga executable") as exc_info:
        validate_amiga_hunk_executable_with_c_backend("bin/object.o")
    assert str(exc_info.value) == "Uploaded media is not an Amiga executable"


def test_amiga_naming_catalog_uses_c_dll(monkeypatch) -> None:
    calls: list[tuple[tuple[str, ...], object]] = []

    def fake_run(function_name: str, *args: str, project_root):
        calls.append((args, project_root))
        return '{"patterns":[],"trivial_functions":[],"generic_prefix":"call_","libraries":["dos.library"]}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_run)

    assert amiga_naming_catalog_with_c_backend() == {
        "patterns": [],
        "trivial_functions": [],
        "generic_prefix": "call_",
        "libraries": ["dos.library"],
    }
    assert calls == [(("amiga-hunk",), PROJECT_ROOT)]


def test_amiga_os_metadata_catalog_uses_c_dll(monkeypatch) -> None:
    calls: list[tuple[tuple[str, ...], object]] = []

    def fake_run(function_name: str, *args: str, project_root):
        calls.append((args, project_root))
        return '{"exec_base_library":"exec.library","lvo_slot_size":6,"libraries":[]}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_run)

    assert amiga_os_metadata_catalog_with_c_backend() == {
        "exec_base_library": "exec.library",
        "lvo_slot_size": 6,
        "libraries": [],
    }
    assert calls == [(("amiga-hunk",), PROJECT_ROOT)]


def test_real_dll_amiga_os_metadata_catalog_exposes_generated_struct_fields() -> None:
    _requires_c_backend_dlls()

    catalog = amiga_os_metadata_catalog_with_c_backend()
    structs = {
        struct["name"]: struct
        for struct in catalog.get("structs", [])
        if isinstance(struct, dict) and isinstance(struct.get("name"), str)
    }
    input_event_fields = {
        field["name"]: field
        for field in structs["InputEvent"]["fields"]
        if isinstance(field, dict) and isinstance(field.get("name"), str)
    }
    io_fields = {
        field["name"]: field
        for field in structs["IO"]["fields"]
        if isinstance(field, dict) and isinstance(field.get("name"), str)
    }
    input_event_resolved = {
        field["query_start"]: field
        for field in structs["InputEvent"]["resolved_fields"]
        if isinstance(field, dict) and isinstance(field.get("query_start"), int)
    }
    input_event_gap_resolved = {
        field["query_start"]: field
        for field in structs["InputEvent"]["resolved_gap_fields"]
        if isinstance(field, dict) and isinstance(field.get("query_start"), int)
    }
    io_resolved = {
        field["query_start"]: field
        for field in structs["IO"]["resolved_fields"]
        if isinstance(field, dict) and isinstance(field.get("query_start"), int)
    }
    io_gap_resolved = {
        field["query_start"]: field
        for field in structs["IO"]["resolved_gap_fields"]
        if isinstance(field, dict) and isinstance(field.get("query_start"), int)
    }

    assert structs["InputEvent"]["size"] == 22
    assert input_event_fields["ie_Code"]["offset"] == 6
    assert input_event_fields["ie_Code"]["size"] == 2
    assert input_event_fields["ie_TimeStamp"]["nested_type"] == "TIMEVAL"
    assert input_event_resolved[18]["name"] == "TV_MICRO"
    assert input_event_resolved[18]["offset"] == 18
    assert input_event_resolved[18]["owner_struct"] == "TIMEVAL"
    assert input_event_resolved[18]["nested"] is True
    assert input_event_resolved[18]["path"] == ["ie_TimeStamp", "TV_MICRO"]
    assert input_event_gap_resolved[14]["name"] == "TV_SECS"
    assert input_event_gap_resolved[14]["query_end"] == 18
    assert structs["IO"]["size"] == 48
    assert structs["IO"]["base"] == {"struct": "MN", "size_symbol": "MN_SIZE", "size": 20}
    assert io_fields["IO_DEVICE"]["offset"] == 20
    assert io_fields["IO_DEVICE"]["pointer_struct"] == "DD"
    assert io_fields["IO_ACTUAL"]["offset"] == 32
    assert io_fields["IO_SIZE"]["offset"] == 32
    assert io_resolved[14]["name"] == "MN_REPLYPORT"
    assert io_resolved[14]["owner_struct"] == "MN"
    assert io_resolved[14]["inherited"] is True
    assert io_gap_resolved[14]["name"] == "MN_REPLYPORT"
    assert io_gap_resolved[14]["nested"] is False


def test_inspect_disk_uses_c_disk_backend(monkeypatch, tmp_path: Path) -> None:
    disk_path = tmp_path / "demo.adf"
    disk_path.write_bytes(b"\0")
    calls: list[tuple[object, ...]] = []

    def fake_run(function_name: str, *args: str, project_root):
        calls.append((function_name, *args))
        return '{"platform":"amiga-disk","boot_block":{"magic_bytes":[68,79,83]}}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_disk_text", fake_run)

    assert inspect_disk_with_c_backend(disk_path, project_root=tmp_path) == {
        "platform": "amiga-disk",
        "boot_block": {"magic_bytes": [68, 79, 83]},
    }
    assert calls == [("platform_disk_inspect_path_json_alloc", "amiga-disk", str(disk_path))]


def test_extract_disk_entry_uses_c_disk_backend(monkeypatch, tmp_path: Path) -> None:
    disk_path = tmp_path / "demo.adf"
    disk_path.write_bytes(b"\0")
    calls: list[tuple[object, ...]] = []

    def fake_run(function_name: str, *args: str, project_root):
        calls.append((function_name, *args))
        return b"payload"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_disk_bytes", fake_run)

    assert extract_disk_entry_with_c_backend(disk_path, "C/Run", project_root=tmp_path) == b"payload"
    assert calls == [("platform_disk_extract_entry_path_bytes_alloc", "amiga-disk", str(disk_path), "C/Run")]


def test_project_source_disk_entry_extracts_with_c_disk_backend(monkeypatch, tmp_path: Path) -> None:
    source = DiskEntryBinarySource(
        kind=BinarySourceKind.DISK_ENTRY,
        disk_id="demo",
        adf_path=tmp_path / "demo.adf",
        entry_path="c/Run",
        display_path="demo.adf::c/Run",
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    file_calls: list[tuple[object, ...]] = []
    disk_calls: list[tuple[object, ...]] = []

    def fake_disk_run(function_name: str, *args: str, project_root):
        disk_calls.append((function_name, *args))
        return b"\x00\x00\x03\xf3"

    def fake_file_run(function_name: str, *args: object, project_root):
        file_calls.append((function_name, *args))
        assert Path(str(args[1])).read_bytes() == b"\x00\x00\x03\xf3"
        return '{"sections":[]}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_disk_bytes", fake_disk_run)
    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    assert analyze_project_source_with_c_backend(source, project_root=tmp_path) == {"sections": []}
    assert disk_calls == [("platform_disk_extract_entry_path_bytes_alloc", "amiga-disk", str(source.adf_path), "c/Run")]
    assert file_calls[0][0:2] == ("platform_file_facts_v2_analysis_path_json_alloc", "amiga-hunk")
    assert not Path(str(file_calls[0][2])).exists()


class _FakeSourceArtifact:
    def __init__(self, source_text: str, profile: dict[str, object]) -> None:
        self.source_text_value = source_text
        self.profile = profile
        self.closed = False

    def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        return {"total_rows": 1}, self.profile

    def source_text_with_profile(self) -> tuple[str, dict[str, object]]:
        return self.source_text_value, self.profile

    def close(self) -> None:
        self.closed = True


def _patch_render_source_artifact(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[dict[str, object]],
    artifact: _FakeSourceArtifact,
) -> None:
    def fake_create(cls, source_file, *, metadata_text: str, include_dir: str, project_root: Path):
        calls.append(
            {
                "platform_name": source_file.platform_name,
                "path": source_file.path,
                "entry_offset": source_file.entry_offset,
                "runtime_load_address": source_file.runtime_load_address,
                "metadata_text": metadata_text,
                "include_dir": include_dir,
                "project_root": project_root,
            }
        )
        return artifact

    monkeypatch.setattr(c_backend.CListingArtifact, "create", classmethod(fake_create))


def test_render_project_source_disk_entry_uses_atari_platform(monkeypatch, tmp_path: Path) -> None:
    source = DiskEntryBinarySource(
        kind=BinarySourceKind.DISK_ENTRY,
        disk_id="demo",
        adf_path=tmp_path / "demo.st",
        entry_path="AUTO/BOOT.PRG",
        display_path="demo.st::AUTO/BOOT.PRG",
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[dict[str, object]] = []
    artifact = _FakeSourceArtifact("; atari\n", {"facts_v2": {"asm_source_refused": False}})

    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend._platform_disk_bytes", lambda function_name, *args, project_root: b"\x60\x1a"
    )
    _patch_render_source_artifact(monkeypatch, calls, artifact)

    assert (
        render_project_source_with_c_backend(
            source,
            project_root=tmp_path,
        )
        == "; atari\n"
    )
    assert calls[0]["platform_name"] == "atari-st"
    assert artifact.closed is True


def test_render_project_source_ttp_uses_atari_platform(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "BIN_GEN.TTP"
    binary_path.write_bytes(b"\x60\x1a")
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[dict[str, object]] = []
    artifact = _FakeSourceArtifact("; atari\n", {"facts_v2": {"asm_source_refused": False}})
    _patch_render_source_artifact(monkeypatch, calls, artifact)

    assert (
        render_project_source_with_c_backend(
            source,
            project_root=tmp_path,
        )
        == "; atari\n"
    )
    assert calls[0]["platform_name"] == "atari-st"
    assert artifact.closed is True


def test_render_project_source_uses_listing_artifact(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "demo"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[dict[str, object]] = []
    artifact = _FakeSourceArtifact("SECTION section_0,code\n", {"facts_v2": {"asm_source_refused": False}})
    _patch_render_source_artifact(monkeypatch, calls, artifact)

    assert (
        render_project_source_with_c_backend(
            source,
            project_root=tmp_path,
        )
        == "SECTION section_0,code\n"
    )
    assert calls[0]["path"] == binary_path
    assert calls[0]["platform_name"] == "amiga-hunk"
    assert artifact.closed is True


def test_render_project_source_refuses_artifact_source(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "demo"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[dict[str, object]] = []
    artifact = _FakeSourceArtifact(
        "",
        {
            "facts_v2": {
                "asm_source_refused": True,
                "asm_source_first_failure_kind": "unresolved_label",
                "asm_source_first_failure_section": 1,
                "asm_source_first_failure_offset": 8,
            }
        },
    )
    _patch_render_source_artifact(monkeypatch, calls, artifact)

    with pytest.raises(FactsV2SourceRefused, match="kind=unresolved_label"):
        render_project_source_with_c_backend(
            source,
            project_root=tmp_path,
        )
    assert artifact.closed is True


def test_project_source_raw_binary_uses_raw_dll_with_local_entrypoint(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []
    artifact_calls: list[dict[str, object]] = []
    artifact = _FakeSourceArtifact("; raw\n", {"facts_v2": {"asm_source_refused": False}})

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return '{"sections":[]}' if function_name == "platform_file_facts_v2_analysis_raw_path_json_alloc" else "; raw\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)
    _patch_render_source_artifact(monkeypatch, artifact_calls, artifact)

    assert analyze_project_source_with_c_backend(source, project_root=tmp_path) == {"sections": []}

    assert render_project_source_with_c_backend(source, project_root=tmp_path) == "; raw\n"
    assert calls == [
        ("platform_file_facts_v2_analysis_raw_path_json_alloc", "amiga-raw", str(binary_path), 12, 0, 0, "", ""),
    ]
    assert artifact_calls[0]["platform_name"] == "amiga-raw"
    assert artifact_calls[0]["entry_offset"] == 12
    assert artifact_calls[0]["runtime_load_address"] is None


def test_project_source_runtime_absolute_raw_binary_passes_runtime_load_model(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    binary_path = tmp_path / "decompressed.bin"
    binary_path.write_bytes(b"\x4e\xf9\x00\x00\x9b\x3a")
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=0x4000,
        entrypoint=0x4000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root: Path) -> str:
        calls.append((function_name, *args))
        return '{"sections":[]}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    assert analyze_project_source_with_c_backend(source, project_root=tmp_path) == {"sections": []}
    assert calls == [
        ("platform_file_facts_v2_analysis_raw_path_json_alloc", "amiga-raw", str(binary_path), 0x4000, 1, 0x4000, "", ""),
    ]


def test_real_dll_runtime_absolute_raw_binary_materializes_runtime_load_range(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    original = bytes.fromhex("4e754e75")
    binary_path = tmp_path / "decompressed.bin"
    binary_path.write_bytes(original)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=0x4000,
        entrypoint=0x4000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    policy = effective_policy_project_source_with_c_backend(source, project_root=PROJECT_ROOT)["analysis_policy"]
    assert policy["runtime_ranges"] == [
        {"section_index": 0, "offset": 0, "size": len(original), "runtime_address": 0x4000, "name": "raw_load"}
    ]
    assert policy["runtime_entry_points"] == [{"section_index": 0, "runtime_address": 0x4000}]
    analysis = analyze_project_source_with_c_backend(source, project_root=PROJECT_ROOT)
    assert any(
        record.get("record_kind") == "runtime_view"
        and record.get("source_offset") == 0
        and record.get("source_size") == len(original)
        and record.get("runtime_address") == 0x4000
        and record.get("entry_runtime_address") == 0x4000
        and record.get("entry_reason_name") == "policy_entry_point"
        for record in analysis["memory_layout_records"]
    )

    rendered = render_project_source_with_c_backend(source, project_root=PROJECT_ROOT)
    assert "ORG $4000" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_local_offset_raw_binary_does_not_invent_runtime_load_range(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "local.bin"
    binary_path.write_bytes(bytes.fromhex("4e754e75"))
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0x4000,
        entrypoint=0x4000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    policy = effective_policy_project_source_with_c_backend(source, project_root=PROJECT_ROOT)["analysis_policy"]
    assert policy["runtime_ranges"] == []
    assert policy["runtime_entry_points"] == []


def test_real_dll_seeded_entities_become_structured_data_policy_items(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "seeded-data.bin"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(bytes.fromhex("4e75414243004e75"))
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "entry_register_seeds": [],
                "seeded_entities": [
                    {
                        "addr": 2,
                        "end": 6,
                        "hunk": 0,
                        "name": "manual_text",
                        "comment": "Manual string seed with enough detail to exceed the old parser scratch buffer",
                        "type": "data",
                        "subtype": "string",
                        "unit": "byte",
                        "encoding": "ascii",
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "manual_action_log:text-table",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    policy = effective_policy_project_source_with_c_backend(
        source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )["analysis_policy"]

    assert len(policy["structured_data_items"]) == 1
    item = policy["structured_data_items"][0]
    assert item["section_index"] == 0
    assert item["offset"] == 2
    assert item["size"] == 4
    assert item["kind"] == "string"
    assert str(item["comment"]).startswith("Manual string seed with enough detail")
    assert item["label"] == "manual_text"
    assert item["field_type"] == "byte"
    assert item["value_domain"] == "ascii"
    assert item["semantic_role"] == "string"
    assert item["semantic_role_flags"] == 128


def test_real_dll_seeded_entity_metadata_classifies_pointer_table_once(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "seeded-pointer-table.bin"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(bytes.fromhex("4e750000000000000000"))
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "entry_register_seeds": [],
                "seeded_entities": [
                    {
                        "addr": 2,
                        "end": 10,
                        "hunk": 0,
                        "name": "manual_jump_table",
                        "type": "data",
                        "subtype": "pointer_table",
                        "unit": "pointer",
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    },
                    {
                        "addr": 0,
                        "end": 2,
                        "hunk": 0,
                        "name": "ignored_code_seed",
                        "type": "code",
                        "subtype": "pointer_table",
                        "unit": "pointer",
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    policy = effective_policy_project_source_with_c_backend(
        source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )["analysis_policy"]

    assert len(policy["structured_data_items"]) == 1
    item = policy["structured_data_items"][0]
    assert item["section_index"] == 0
    assert item["offset"] == 2
    assert item["size"] == 8
    assert item["kind"] == "longs"
    assert item["label"] == "manual_jump_table"
    assert item["field_type"] == "pointer"
    assert item["semantic_role"] == "pointer_table"
    assert item["semantic_role_flags"] == 4


def test_real_dll_required_manual_code_seed_drives_c_analysis_without_implicit_scan(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-code-seed.bin"
    source_text = """    SECTION section,code
    dc.b $41,$42,$43,$44
manual_start:
    bsr.b helper
    rts
helper:
    rts
    dc.w 0
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="data", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_seed",
                "seed": {
                    "seed_id": "manual-start",
                    "kind": "code",
                    "mode": "required",
                    "hunk": 0,
                    "addr": 4,
                    "name": "manual_start",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        analysis = analyze_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert policy["implicit_entry_points"] is False
    assert policy["entrypoints"] == [{"section_index": 0, "offset": 4}]
    block_starts = {block["start_offset"] for block in analysis["sections"][0]["blocks"]}
    assert 0 not in block_starts
    assert {4, 8}.issubset(block_starts)


def test_real_dll_required_manual_data_seed_splits_rendered_subrange(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-seed.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b "TEXT",$00,$00
after_data:
    rts
    dc.w 0
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_seed",
                "seed": {
                    "seed_id": "manual-text",
                    "kind": "data",
                    "mode": "required",
                    "hunk": 0,
                    "addr": 2,
                    "end": 7,
                    "data_role": "string",
                    "unit": "byte",
                    "encoding": "ascii",
                    "name": "manual_text",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert "loc_0_00000000:\n\tbra.b loc_0_00000008\n" in rendered
    assert (
        'manual_text:\n\tdc.b "TEXT",$00\t; mode=required, data_role=string, unit=byte, encoding=ascii\n'
        in rendered
    )
    assert "\tdc.b $00\nloc_0_00000008:\n\trts\n" in rendered


def test_real_dll_manual_data_symbol_rename_updates_rendered_seeded_entity(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-symbol-rename.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b "TEXT",$00,$00
after_data:
    rts
    dc.w 0
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=2,
                    end=7,
                    hunk=0,
                    name="seeded_text",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="test seeded data label",
                    source_id="fixture",
                    source_path="tests/test_c_backend.py",
                    source_locator="test_real_dll_manual_data_symbol_rename_updates_rendered_seeded_entity",
                    type="data",
                    subtype="string",
                    unit="byte",
                    encoding="ascii",
                ),
            ),
        ),
    )
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-18T00:00:01+00:00",
                "kind": "rename_data_symbol",
                "data_symbol": {
                    "data_symbol_id": "data-symbol:h0:00000002:00000007",
                    "hunk": 0,
                    "addr": 2,
                    "end": 7,
                    "name": "renamed_text",
                    "previous_name": "seeded_text",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert 'renamed_text:\n\tdc.b "TEXT",$00\t; string\n' in rendered
    assert "seeded_text:" not in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_refused"] is False
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_manual_data_symbol_remove_suppresses_rendered_seeded_entity(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-symbol-remove.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b "TEXT",$00,$00
after_data:
    rts
    dc.w 0
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=2,
                    end=7,
                    hunk=0,
                    name="seeded_text",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="test seeded data label",
                    source_id="fixture",
                    source_path="tests/test_c_backend.py",
                    source_locator="test_real_dll_manual_data_symbol_remove_suppresses_rendered_seeded_entity",
                    type="data",
                    subtype="string",
                    unit="byte",
                    encoding="ascii",
                ),
            ),
        ),
    )
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-18T00:00:01+00:00",
                "kind": "suppress_seeded_item",
                "suppressed_seeded_item": {"kind": "seeded_entity", "hunk": 0, "addr": 2},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "seeded_text:" not in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_refused"] is False
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_manual_data_symbol_rename_renders_ordinary_data_row(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-symbol-row-rename.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b "TEXT",$00,$00
after_data:
    rts
    dc.w 0
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-18T00:00:01+00:00",
                "kind": "rename_data_symbol",
                "data_symbol": {
                    "data_symbol_id": "data-symbol:h0:00000002:00000007",
                    "hunk": 0,
                    "addr": 2,
                    "end": 7,
                    "name": "renamed_text",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "renamed_text:\n\tdc.b $54,$45,$58,$54,$00\n" in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_refused"] is False
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_manual_data_symbol_rename_updates_rendered_use_site(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-symbol-use-site.bin"
    source_text = """    SECTION section,code
start:
    lea data_label(pc),a0
    rts
data_label:
    dc.b "DATA",$00,$00
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-18T00:00:01+00:00",
                "kind": "rename_data_symbol",
                "data_symbol": {
                    "data_symbol_id": "data-symbol:h0:00000006:0000000C",
                    "hunk": 0,
                    "addr": 6,
                    "end": 12,
                    "name": "renamed_data",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "\tlea.l renamed_data(pc),a0\n" in rendered
    assert "renamed_data:\n\tdc.b $44,$41,$54,$41,$00,$00\n" in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_refused"] is False
    assert direct_profile["direct_rebuild_exact"] is True


@pytest.mark.parametrize(
    ("data_role", "unit", "encoding"),
    [
        ("copper_list", "word", None),
        ("palette", "word", None),
        ("pointer_table", "pointer", None),
        ("lookup_table", "word", None),
        ("scalar_table", "word", None),
        ("length_prefixed_string", "byte", "ascii"),
        ("bitmap", "byte", None),
        ("sound_sample", "byte", None),
        ("string", "byte", "ascii"),
        ("audio_table", "pointer", None),
        ("sprite", "byte", None),
        ("string_control_stream", "byte", None),
    ],
)
def test_real_dll_required_manual_data_roles_render_source(
    tmp_path: Path,
    data_role: str,
    unit: str,
    encoding: str | None,
) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / f"manual-{data_role}.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b $03,$41,$42,$43,$00,$00,$00,$00
after_data:
    rts
    dc.b $00,$00,$00,$00
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    seed = {
        "seed_id": f"manual-{data_role}",
        "kind": "data",
        "mode": "required",
        "hunk": 0,
        "addr": 2,
        "end": 10,
        "data_role": data_role,
        "unit": unit,
    }
    if encoding is not None:
        seed["encoding"] = encoding
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-18T00:00:01+00:00",
                "kind": "create_manual_seed",
                "seed": seed,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert f"data_role={data_role}" in rendered
    assert f"unit={unit}" in rendered
    if encoding is not None:
        assert f"encoding={encoding}" in rendered
    assert "\trts\n" in rendered
    assert rebuilt == binary_path.read_bytes()
    assert direct_profile["direct_rebuild_refused"] is False
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_manual_representation_styles_classified_bytes_without_classifying(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-representation.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b $41,$42,$43,$44
after_data:
    rts
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_representation",
                "representation": {
                    "representation_id": "repr-data",
                    "hunk": 0,
                    "addr": 2,
                    "end": 6,
                    "style": "character",
                    "element_kind": "operand",
                },
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a2",
                "sequence": 2,
                "created_at": "2026-05-13T00:00:02+00:00",
                "kind": "create_manual_seed",
                "seed": {
                    "seed_id": "manual-bytes",
                    "kind": "data",
                    "mode": "required",
                    "hunk": 0,
                    "addr": 2,
                    "end": 6,
                    "unit": "byte",
                    "name": "manual_bytes",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert policy["manual_representations"] == [
        {"section_index": 0, "offset": 2, "size": 4, "style": "character"}
    ]
    assert "manual_bytes:\n\tdc.b 'A','B','C','D'\t; mode=required, unit=byte\n" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_data_block_layout_element_renders_source_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-block-layout.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b $41,$42,$43,$44
after_data:
    rts
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-18T00:00:01+00:00",
                "kind": "create_manual_data_block_layout",
                "data_block_layout": {
                    "layout_id": "ascii-hex",
                    "hunk": 0,
                    "source_start": 2,
                    "source_end": 6,
                    "name": "ascii_hex_digit_value",
                    "role": "lookup_table",
                    "default_unit": "byte",
                },
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a2",
                "sequence": 2,
                "created_at": "2026-05-18T00:00:02+00:00",
                "kind": "set_manual_data_block_element",
                "data_block_element": {
                    "data_block_element_id": "ascii-hex:0",
                    "layout_id": "ascii-hex",
                    "offset": 0,
                    "width": 4,
                    "kind": "array",
                    "representation": "character",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert "ascii_hex_digit_value:\n\tdc.b 'A','B','C','D'\t; lookup_table\n" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_data_block_custom_struct_binding_expands_fields_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-block-custom-struct.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.w $4AFC
    dc.l $00000008
after_data:
    rts
    nop
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    records = [
        {
            "record": "manual_action_log_header",
            "version": 1,
            "target_identity": build_target_identity(source),
        },
        {
            "record": "manual_action",
            "action_id": "a1",
            "sequence": 1,
            "created_at": "2026-05-18T00:00:01+00:00",
            "kind": "create_manual_custom_struct",
            "custom_struct": {
                "custom_struct_id": "DataHeader",
                "name": "DataHeader",
                "size": 6,
                "fields": [
                    {"name": "magic", "type": "UWORD", "offset": 0, "size": 2},
                    {"name": "next_offset", "type": "APTR", "offset": 2, "size": 4},
                ],
            },
        },
        {
            "record": "manual_action",
            "action_id": "a2",
            "sequence": 2,
            "created_at": "2026-05-18T00:00:02+00:00",
            "kind": "create_manual_data_block_layout",
            "data_block_layout": {
                "layout_id": "header",
                "hunk": 0,
                "source_start": 2,
                "source_end": 8,
                "name": "data_header",
                "default_unit": "byte",
            },
        },
        {
            "record": "manual_action",
            "action_id": "a3",
            "sequence": 3,
            "created_at": "2026-05-18T00:00:03+00:00",
            "kind": "set_manual_data_block_element",
            "data_block_element": {
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
                },
            },
        },
    ]
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    typed_items = [
        item for item in policy["structured_data_items"] if item.get("struct_name") == "DataHeader"
    ]
    assert [(item["offset"], item["size"], item["field_name"], item["field_type"]) for item in typed_items] == [
        (2, 2, "magic", "UWORD"),
        (4, 4, "next_offset", "APTR"),
    ]
    assert "UWORD magic" in rendered
    assert "APTR next_offset" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_data_block_platform_struct_binding_expands_fields_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-block-platform-struct.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dcb.b 34,$00
after_data:
    rts
    nop
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    records = [
        {
            "record": "manual_action_log_header",
            "version": 1,
            "target_identity": build_target_identity(source),
        },
        {
            "record": "manual_action",
            "action_id": "a1",
            "sequence": 1,
            "created_at": "2026-05-18T00:00:01+00:00",
            "kind": "create_manual_data_block_layout",
            "data_block_layout": {
                "layout_id": "node",
                "hunk": 0,
                "source_start": 2,
                "source_end": 36,
                "name": "msg_port",
                "default_unit": "byte",
            },
        },
        {
            "record": "manual_action",
            "action_id": "a2",
            "sequence": 2,
            "created_at": "2026-05-18T00:00:02+00:00",
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "node:0",
                "layout_id": "node",
                "offset": 0,
                "width": 34,
                "kind": "platform_struct",
                "type_binding": {
                    "type_binding_id": "node:0:22:platform_struct:MsgPort",
                    "layout_id": "node",
                    "element_offset": 0,
                    "element_width": 34,
                    "binding_kind": "platform_struct",
                    "bound_type_id": "MsgPort",
                    "owner_action_id": "a2",
                },
            },
        },
    ]
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    typed_items = [item for item in policy["structured_data_items"] if item.get("struct_name") == "MP"]
    assert [(item["offset"], item["size"], item["field_name"], item["field_type"]) for item in typed_items] == [
        (2, 4, "LN_SUCC", "APTR"),
        (6, 4, "LN_PRED", "APTR"),
        (10, 1, "LN_TYPE", "UBYTE"),
        (11, 1, "LN_PRI", "BYTE"),
        (12, 4, "LN_NAME", "APTR"),
        (16, 1, "MP_FLAGS", "UBYTE"),
        (17, 1, "MP_SIGBIT", "UBYTE"),
        (18, 4, "MP_SIGTASK", "APTR"),
        (22, 4, "MP_MSGLIST.LH_HEAD", "APTR"),
        (26, 4, "MP_MSGLIST.LH_TAIL", "APTR"),
        (30, 4, "MP_MSGLIST.LH_TAILPRED", "APTR"),
        (34, 1, "MP_MSGLIST.LH_TYPE", "UBYTE"),
        (35, 1, "MP_MSGLIST.LH_pad", "UBYTE"),
    ]
    assert "APTR LN_SUCC" in rendered
    assert "UBYTE MP_MSGLIST.LH_TYPE" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_data_block_domain_binding_renders_symbolic_value_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-block-domain.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b $09
    dc.b $00
after_data:
    rts
    nop
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    records = [
        {
            "record": "manual_action_log_header",
            "version": 1,
            "target_identity": build_target_identity(source),
        },
        {
            "record": "manual_action",
            "action_id": "a1",
            "sequence": 1,
            "created_at": "2026-05-18T00:00:01+00:00",
            "kind": "create_manual_data_block_layout",
            "data_block_layout": {
                "layout_id": "node-type",
                "hunk": 0,
                "source_start": 2,
                "source_end": 3,
                "name": "node_type",
                "default_unit": "byte",
            },
        },
        {
            "record": "manual_action",
            "action_id": "a2",
            "sequence": 2,
            "created_at": "2026-05-18T00:00:02+00:00",
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "node-type:0",
                "layout_id": "node-type",
                "offset": 0,
                "width": 1,
                "kind": "scalar",
                "type_binding": {
                    "type_binding_id": "node-type:0:1:enum_domain:exec.node.type",
                    "layout_id": "node-type",
                    "element_offset": 0,
                    "element_width": 1,
                    "binding_kind": "enum_domain",
                    "bound_domain_id": "exec.node.type",
                    "owner_action_id": "a2",
                },
            },
        },
    ]
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    domain_items = [item for item in policy["structured_data_items"] if item.get("value_domain") == "exec.node.type"]
    assert [(item["offset"], item["size"], item["value_domain"]) for item in domain_items] == [
        (2, 1, "exec.node.type")
    ]
    assert "\tdc.b NT_LIBRARY\n" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_data_block_interpreted_ref_renders_symbol_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-block-ref.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.l $00000006
after_data:
    rts
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    actions = [
        {
            "record": "manual_action_log_header",
            "version": 1,
            "target_identity": build_target_identity(source),
        },
        {
            "record": "manual_action",
            "action_id": "a1",
            "sequence": 1,
            "created_at": "2026-05-18T00:00:01+00:00",
            "kind": "create_manual_data_block_layout",
            "data_block_layout": {
                "layout_id": "jump-target",
                "hunk": 0,
                "source_start": 2,
                "source_end": 6,
                "default_unit": "long",
            },
        },
        {
            "record": "manual_action",
            "action_id": "a2",
            "sequence": 2,
            "created_at": "2026-05-18T00:00:02+00:00",
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "jump-target:0",
                "layout_id": "jump-target",
                "offset": 0,
                "width": 4,
                "kind": "scalar",
            },
        },
        {
            "record": "manual_action",
            "action_id": "a3",
            "sequence": 3,
            "created_at": "2026-05-18T00:00:03+00:00",
            "kind": "interpret_manual_data_block_element_ref",
            "data_block_interpreted_ref": {
                "data_block_ref_id": "jump-target:0:absolute:h0:00000006",
                "layout_id": "jump-target",
                "offset": 0,
                "width": 4,
                "reference_kind": "absolute",
                "target_hunk": 0,
                "target_offset": 0x06,
                "target_locator": {"hunk": 0, "offset": 0x06},
                "source_value": 0x06,
                "confidence": "manual",
                "xref_generation_mode": "bidirectional",
            },
        },
    ]
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "\n".join(json.dumps(action, sort_keys=True) for action in actions) + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rows, _api_calls, _profile = build_project_listing_rows_from_source_with_c_artifact(
            source,
            metadata_text=str(metadata_path),
            project_root=PROJECT_ROOT,
        )

    assert "dblk_ref_h0_00000006\tEQU\t$6" in rendered
    assert "\tdc.l dblk_ref_h0_00000006\n" in rendered
    data_row = next(row for row in rows if row.get("kind") == "data" and row.get("start_offset") == 2)
    assert data_row["runtime_address_refs"] == [
        {
            "confidence": 3,
            "data_class": None,
            "offset": 2,
            "operand_index": None,
            "owner_element_offset": 0,
            "owner_id": "jump-target:0:absolute:h0:00000006",
            "owner_kind": "data_block_interpreted_ref",
            "owner_layout_id": "jump-target",
            "runtime_address": 0x06,
            "size": 4,
            "sink_address": None,
            "target_offset": 0x06,
            "target_section_index": 0,
            "xref_generation_mode": "bidirectional",
        }
    ]
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_data_block_interpreted_refs_scale_past_target_equate_edit_cap(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-block-ref-table.bin"
    source_offsets = [2 + index * 4 for index in range(20)]
    source_text = "\n".join(
        [
            "    SECTION section,code",
            "start:",
            "    bra.b after_data",
            *[f"    dc.l ${offset:08X}" for offset in source_offsets],
            "after_data:",
            "    rts",
            "",
        ]
    )
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    actions = [
        {
            "record": "manual_action_log_header",
            "version": 1,
            "target_identity": build_target_identity(source),
        },
        {
            "record": "manual_action",
            "action_id": "layout",
            "sequence": 1,
            "created_at": "2026-05-18T00:00:01+00:00",
            "kind": "create_manual_data_block_layout",
            "data_block_layout": {
                "layout_id": "ref-table",
                "hunk": 0,
                "source_start": source_offsets[0],
                "source_end": source_offsets[-1] + 4,
                "default_unit": "long",
            },
        },
    ]
    for index, source_offset in enumerate(source_offsets):
        element_offset = index * 4
        actions.append(
            {
                "record": "manual_action",
                "action_id": f"element-{index}",
                "sequence": 2 + index * 2,
                "created_at": "2026-05-18T00:00:02+00:00",
                "kind": "set_manual_data_block_element",
                "data_block_element": {
                    "data_block_element_id": f"ref-table:{element_offset}",
                    "layout_id": "ref-table",
                    "offset": element_offset,
                    "width": 4,
                    "kind": "scalar",
                },
            }
        )
        actions.append(
            {
                "record": "manual_action",
                "action_id": f"ref-{index}",
                "sequence": 3 + index * 2,
                "created_at": "2026-05-18T00:00:03+00:00",
                "kind": "interpret_manual_data_block_element_ref",
                "data_block_interpreted_ref": {
                    "data_block_ref_id": f"ref-table:{element_offset}:absolute:h0:{source_offset:08X}",
                    "layout_id": "ref-table",
                    "offset": element_offset,
                    "width": 4,
                    "reference_kind": "absolute",
                    "target_hunk": 0,
                    "target_offset": source_offset,
                    "target_locator": {"hunk": 0, "offset": source_offset},
                    "source_value": source_offset,
                    "confidence": "manual",
                    "xref_generation_mode": "bidirectional",
                },
            }
        )
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "\n".join(json.dumps(action, sort_keys=True) for action in actions) + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rows, _api_calls, _profile = build_project_listing_rows_from_source_with_c_artifact(
            source,
            metadata_text=str(metadata_path),
            project_root=PROJECT_ROOT,
        )

    assert rendered.count("\tEQU\t$") >= len(source_offsets)
    for source_offset in source_offsets:
        symbol = f"dblk_ref_h0_{source_offset:08X}"
        assert f"{symbol}\tEQU\t${source_offset:X}" in rendered
        assert f"\tdc.l {symbol}\n" in rendered
    owned_refs = [
        ref
        for row in rows
        for ref in row.get("runtime_address_refs", [])
        if isinstance(ref, dict) and ref.get("owner_kind") == "data_block_interpreted_ref"
    ]
    assert len(owned_refs) == len(source_offsets)
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_data_block_layout_scalar_matrix_renders_source_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-block-layout-matrix.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b $12,$00
    dc.w $3456
    dc.l $789ABCDE
    dc.b $41,$42,$43,$44
    dcb.b 8,$00
after_data:
    rts
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    actions = [
        {
            "kind": "create_manual_data_block_layout",
            "data_block_layout": {
                "layout_id": "matrix",
                "hunk": 0,
                "source_start": 2,
                "source_end": 22,
                "role": "lookup_table",
                "default_unit": "byte",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "matrix:0",
                "layout_id": "matrix",
                "offset": 0,
                "width": 1,
                "kind": "scalar",
                "name": "byte_value",
                "representation": "hex",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "matrix:1",
                "layout_id": "matrix",
                "offset": 1,
                "width": 1,
                "kind": "gap",
                "name": "gap_byte",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "matrix:2",
                "layout_id": "matrix",
                "offset": 2,
                "width": 2,
                "kind": "scalar",
                "name": "word_value",
                "representation": "hex",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "matrix:4",
                "layout_id": "matrix",
                "offset": 4,
                "width": 4,
                "kind": "scalar",
                "name": "long_value",
                "representation": "hex",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "matrix:8",
                "layout_id": "matrix",
                "offset": 8,
                "width": 4,
                "kind": "array",
                "name": "letters",
                "array_count": 4,
                "array_stride": 1,
                "representation": "character",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "matrix:C",
                "layout_id": "matrix",
                "offset": 12,
                "width": 8,
                "kind": "padding",
                "name": "zero_pad",
            },
        },
    ]
    lines = [
        json.dumps(
            {"record": "manual_action_log_header", "version": 1, "target_identity": build_target_identity(source)},
            sort_keys=True,
        )
    ]
    for sequence, action in enumerate(actions, start=1):
        lines.append(
            json.dumps(
                {
                    "record": "manual_action",
                    "action_id": f"a{sequence}",
                    "sequence": sequence,
                    "created_at": f"2026-05-18T00:00:{sequence:02d}+00:00",
                    **action,
                },
                sort_keys=True,
            )
        )
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
    )

    assert "byte_value:\n\tdc.b $12\t; lookup_table\n" in rendered
    assert "gap_byte:\n\tdc.b $00\t; lookup_table\n" in rendered
    assert "word_value:\n\tdc.w $3456\t; lookup_table\n" in rendered
    assert "long_value:\n\tdc.l $789ABCDE\t; lookup_table\n" in rendered
    assert "letters:\n\tdc.b 'A','B','C','D'\t; lookup_table\n" in rendered
    assert "zero_pad:\n\tdcb.b $8,$00\t; lookup_table\n" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_genam_ascii_hex_table_data_block_layout_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    paths = _requires_project_paths("amiga_hunk_genam")
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    actions = [
        {
            "kind": "create_manual_data_block_layout",
            "data_block_layout": {
                "layout_id": "genam-ascii-hex",
                "hunk": 0,
                "source_start": 0x1442,
                "source_end": 0x14C2,
                "name": "ascii_hex_digit_value",
                "role": "lookup_table",
                "default_unit": "byte",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "genam-ascii-hex:0",
                "layout_id": "genam-ascii-hex",
                "offset": 0,
                "width": 0x30,
                "kind": "padding",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "genam-ascii-hex:30",
                "layout_id": "genam-ascii-hex",
                "offset": 0x30,
                "width": 10,
                "kind": "array",
                "name": "ascii_hex_digit_values",
                "array_count": 10,
                "array_stride": 1,
                "representation": "hex",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "genam-ascii-hex:3A",
                "layout_id": "genam-ascii-hex",
                "offset": 0x3A,
                "width": 7,
                "kind": "padding",
                "name": "ascii_hex_digit_separator",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "genam-ascii-hex:41",
                "layout_id": "genam-ascii-hex",
                "offset": 0x41,
                "width": 6,
                "kind": "array",
                "name": "ascii_hex_upper_values",
                "array_count": 6,
                "array_stride": 1,
                "representation": "hex",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "genam-ascii-hex:47",
                "layout_id": "genam-ascii-hex",
                "offset": 0x47,
                "width": 0x1A,
                "kind": "padding",
                "name": "ascii_hex_case_gap",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "genam-ascii-hex:61",
                "layout_id": "genam-ascii-hex",
                "offset": 0x61,
                "width": 6,
                "kind": "array",
                "name": "ascii_hex_lower_values",
                "array_count": 6,
                "array_stride": 1,
                "representation": "hex",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "genam-ascii-hex:67",
                "layout_id": "genam-ascii-hex",
                "offset": 0x67,
                "width": 0x19,
                "kind": "padding",
                "name": "ascii_hex_tail",
            },
        },
    ]
    lines = [
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(paths.binary_source),
            },
            sort_keys=True,
        )
    ]
    for sequence, action in enumerate(actions, start=1):
        lines.append(
            json.dumps(
                {
                    "record": "manual_action",
                    "action_id": f"a{sequence}",
                    "sequence": sequence,
                    "created_at": f"2026-05-18T00:00:{sequence:02d}+00:00",
                    **action,
                },
                sort_keys=True,
            )
        )
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    original = paths.binary_source.path.read_bytes()
    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            paths.binary_source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "ascii_hex_digit_value:\n\tdcb.b $30,$FF\t; lookup_table\n" in rendered
    assert "ascii_hex_digit_values:\n\tdc.b $00,$01,$02,$03,$04,$05,$06,$07,$08,$09\t; lookup_table\n" in rendered
    assert "ascii_hex_upper_values:\n\tdc.b $0A,$0B,$0C,$0D,$0E,$0F\t; lookup_table\n" in rendered
    assert "ascii_hex_lower_values:\n\tdc.b $0A,$0B,$0C,$0D,$0E,$0F\t; lookup_table\n" in rendered
    assert "ascii_hex_tail:\n\tdcb.b $19,$FF\t; lookup_table\n" in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_data_block_layout_removal_returns_raw_source_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-block-layout-removal.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b $41,$42,$43,$44
after_data:
    rts
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    actions = [
        {
            "kind": "create_manual_data_block_layout",
            "data_block_layout": {
                "layout_id": "ascii-hex",
                "hunk": 0,
                "source_start": 2,
                "source_end": 6,
                "name": "ascii_hex_digit_value",
                "role": "lookup_table",
                "default_unit": "byte",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "ascii-hex:0",
                "layout_id": "ascii-hex",
                "offset": 0,
                "width": 4,
                "kind": "array",
                "representation": "character",
            },
        },
        {
            "kind": "remove_manual_data_block_layout",
            "data_block_layout": {"layout_id": "ascii-hex", "removal_state": "raw"},
        },
    ]
    lines = [
        json.dumps(
            {"record": "manual_action_log_header", "version": 1, "target_identity": build_target_identity(source)},
            sort_keys=True,
        )
    ]
    for sequence, action in enumerate(actions, start=1):
        lines.append(
            json.dumps(
                {
                    "record": "manual_action",
                    "action_id": f"a{sequence}",
                    "sequence": sequence,
                    "created_at": f"2026-05-18T00:00:{sequence:02d}+00:00",
                    **action,
                },
                sort_keys=True,
            )
        )
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert "ascii_hex_digit_value" not in rendered
    assert "\tdc.b $41,$42,$43,$44\n" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_data_block_element_removal_returns_raw_source_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-data-block-element-removal.bin"
    source_text = """    SECTION section,code
start:
    bra.b after_data
    dc.b $41,$42,$43,$44
after_data:
    rts
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    actions = [
        {
            "kind": "create_manual_data_block_layout",
            "data_block_layout": {
                "layout_id": "ascii-hex",
                "hunk": 0,
                "source_start": 2,
                "source_end": 6,
                "name": "ascii_hex_digit_value",
                "role": "lookup_table",
                "default_unit": "byte",
            },
        },
        {
            "kind": "set_manual_data_block_element",
            "data_block_element": {
                "data_block_element_id": "ascii-hex:0",
                "layout_id": "ascii-hex",
                "offset": 0,
                "width": 4,
                "kind": "array",
                "name": "digit_chars",
                "representation": "character",
            },
        },
        {
            "kind": "remove_manual_data_block_element",
            "data_block_element": {"layout_id": "ascii-hex", "offset": 0, "removal_state": "raw"},
        },
    ]
    lines = [
        json.dumps(
            {"record": "manual_action_log_header", "version": 1, "target_identity": build_target_identity(source)},
            sort_keys=True,
        )
    ]
    for sequence, action in enumerate(actions, start=1):
        lines.append(
            json.dumps(
                {
                    "record": "manual_action",
                    "action_id": f"a{sequence}",
                    "sequence": sequence,
                    "created_at": f"2026-05-18T00:00:{sequence:02d}+00:00",
                    **action,
                },
                sort_keys=True,
            )
        )
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert "digit_chars" not in rendered
    assert "\tdc.b $41,$42,$43,$44\n" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_manual_representation_styles_instruction_immediates(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-immediate-representation.bin"
    source_text = """    SECTION section,code
start:
    move.b #65,d0
    move.w #5,d1
    rts
    dc.w 0
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_representation",
                "representation": {
                    "representation_id": "repr-char",
                    "hunk": 0,
                    "addr": 0,
                    "end": 4,
                    "style": "character",
                    "element_kind": "immediate",
                    "operand_index": 0,
                },
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a2",
                "sequence": 2,
                "created_at": "2026-05-13T00:00:02+00:00",
                "kind": "create_manual_representation",
                "representation": {
                    "representation_id": "repr-binary",
                    "hunk": 0,
                    "addr": 4,
                    "end": 8,
                    "style": "binary",
                    "element_kind": "immediate",
                    "operand_index": 0,
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert policy["manual_representations"] == [
        {"section_index": 0, "offset": 0, "size": 4, "style": "character", "operand_index": 0},
        {"section_index": 0, "offset": 4, "size": 4, "style": "binary", "operand_index": 0},
    ]
    assert "\tmove.b #'A',d0\n" in rendered
    assert "\tmove.w #%0000000000000101,d1\n" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_real_dll_equate_semantic_hint_renders_symbolic_immediate(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-equate-hint.bin"
    source_text = """    SECTION section,code
start:
    move.l #$10000,d0
    rts
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-18T00:00:01+00:00",
                "kind": "create_manual_semantic_hint",
                "semantic_hint": {
                    "semantic_hint_id": "hint-1",
                    "hunk": 0,
                    "addr": 0,
                    "element_kind": "immediate",
                    "operand_index": 0,
                    "domain": "equate",
                    "symbol": "MEMF_CLEAR",
                    "value": 0x10000,
                    "namespace": "exec/memory.i",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert policy["manual_representations"] == [
        {"section_index": 0, "offset": 0, "size": 1, "style": "symbol", "operand_index": 0, "symbol": "MEMF_CLEAR"}
    ]
    assert '    INCLUDE "exec/memory.i"\n' in rendered
    assert "\tmove.l #MEMF_CLEAR,d0\n" in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


def _append_a5_decision(
    target_dir: Path,
    *,
    action: str = "accept_fact",
    decision_id: str = "decision-a5-render",
    ref_override: dict[str, object] | None = None,
) -> dict[str, object]:
    ref = {
        "a5_hardware_ref_id": "a5-hw:fixture",
        "target_id": "demo",
        "row_key": "s0:00000000:instruction:1",
        "selected_use_id": "s0:00000000:op0",
        "parent_evidence_id": "a5-custom-cfg:fixture",
        "parent_evidence_ids": ["a5-custom-cfg:fixture"],
        "source_family": "amiga_custom_base",
        "source_evidence_status": "accepted",
        "source_evidence_id": "a5-custom-cfg:fixture",
        "path_lifetime_scope": {
            "accepted_hardware_base_evidence": True,
            "kind": "straight_line_cfg_between_definition_and_use",
        },
        "base_register": "A5",
        "register": "A5",
        "operand_index": 1,
        "displacement": 0x96,
        "custom_base_offset": 0,
        "custom_base_address": 0xDFF000,
        "hardware_register_offset": 0x96,
        "hardware_register_address": 0xDFF096,
        "reference_kind": "hardware_register",
        "symbol": "dmacon",
        "render_mode": "symbol_operand",
        "conflicts": [],
        "hunk": 0,
        "addr": 0,
        "end": 4,
    }
    if ref_override:
        ref.update(ref_override)
    selected_identity = {
        "target_id": "demo",
        "segment_id": "s0",
        "hunk": 0,
        "addr": 0,
        "end": 4,
        "row_key": "s0:00000000:instruction:1",
        "operand_index": 1,
        "base_register": "A5",
        "displacement": 0x96,
        "hardware_register_offset": 0x96,
        "parent_evidence_id": "a5-custom-cfg:fixture",
    }
    record = {
        "schema": decision_journal.DECISION_JOURNAL_SCHEMA,
        "decision_id": decision_id,
        "prev": None,
        "created_at": "2026-05-26T00:00:00+00:00",
        "actor": {"kind": "llm", "name": "codex"},
        "action": action,
        "packet_id": "a5-path-lifetime-packet:s0:00000000:op1",
        "candidate_id": "a5-custom-cfg:fixture",
        "selected_identity": selected_identity,
        "evidence_refs": ["a5-path-lifetime-packet:s0:00000000:op1", "a5-custom-cfg:fixture"],
        "conflicts": [],
        "reason": action,
    }
    if action == "accept_fact":
        record["fact_type"] = "a5_hardware_ref"
        record["scope"] = {"kind": "selected_a5_hardware_ref", "hunk": 0, "addr": 0, "end": 4, "operand_index": 1}
        record["a5_hardware_ref"] = ref
    elif action == "defer_fact":
        record["defer_reason"] = "deferred fixture"
    elif action == "reject_fact":
        record["reject_reason"] = "rejected fixture"
    else:
        raise AssertionError(action)
    decision_journal.append_decision_record(target_dir, record)
    return ref


def _a5_decision_render_fixture(tmp_path: Path, source_text: str) -> tuple[HunkFileBinarySource, Path, bytes]:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "a5-render.bin"
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    return source, target_dir, original


def test_real_dll_accepted_a5_decision_renders_through_effective_metadata(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    source, target_dir, original = _a5_decision_render_fixture(
        tmp_path,
        """    SECTION section,code
start:
    move.w d0,$0096(a5)
    rts
    dc.w 0
""",
    )
    _append_a5_decision(target_dir)

    with effective_metadata_file(target_dir, include_decision_journal=False) as baseline_path:
        baseline = render_project_source_with_c_backend(source, metadata_path=baseline_path, project_root=PROJECT_ROOT)
    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "\tmove.w d0,$0096(a5)\n" in baseline
    assert policy["manual_representations"] == [
        {"section_index": 0, "offset": 0, "size": 4, "style": "symbol", "operand_index": 1, "symbol": "dmacon"}
    ]
    assert "\tmove.w d0,dmacon(a5)\n" in rendered
    assert "\tmove.w d0,$0096(a5)\n" not in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


@pytest.mark.parametrize("action", ["defer_fact", "reject_fact"])
def test_real_dll_nonaccepted_a5_decision_does_not_render(tmp_path: Path, action: str) -> None:
    _requires_c_backend_dlls()
    source, target_dir, original = _a5_decision_render_fixture(
        tmp_path,
        """    SECTION section,code
start:
    move.w d0,$0096(a5)
    rts
    dc.w 0
""",
    )
    _append_a5_decision(target_dir, action=action, decision_id=f"decision-a5-{action}")

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert policy["manual_representations"] == []
    assert "\tmove.w d0,$0096(a5)\n" in rendered
    assert "dmacon(a5)" not in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_stale_a5_decision_identity_does_not_render(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    source, target_dir, original = _a5_decision_render_fixture(
        tmp_path,
        """    SECTION section,code
start:
    move.w d0,$0096(a5)
    rts
    dc.w 0
""",
    )
    _append_a5_decision(target_dir, ref_override={"row_key": "s0:00000002:instruction:stale"})

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert policy["manual_representations"] == []
    assert "\tmove.w d0,$0096(a5)\n" in rendered
    assert "dmacon(a5)" not in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


def _target_equate_manual_action_log_text(source: HunkFileBinarySource, actions: list[dict[str, object]]) -> str:
    records = [
        {
            "record": "manual_action_log_header",
            "version": 1,
            "target_identity": build_target_identity(source),
        }
    ]
    records.extend(actions)
    return "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n"


def _target_equate_action(sequence: int, kind: str, payload: dict[str, object]) -> dict[str, object]:
    return {
        "record": "manual_action",
        "action_id": f"a{sequence}",
        "sequence": sequence,
        "created_at": f"2026-05-18T00:00:{sequence:02d}+00:00",
        "kind": kind,
        **payload,
    }


def test_real_dll_target_equate_renders_definition_and_symbolic_immediate(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-target-equate.bin"
    source_text = """    SECTION section,code
start:
    move.w #42,d0
    rts
    dc.w 0
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        _target_equate_manual_action_log_text(
            source,
            [
                _target_equate_action(
                    1,
                    "create_manual_target_equate",
                    {
                        "target_equate": {
                            "target_equate_id": "equate-1",
                            "name": "PLAYER_START_LIVES",
                            "value": 42,
                        }
                    },
                ),
                _target_equate_action(
                    2,
                    "create_manual_representation",
                    {
                        "representation": {
                            "representation_id": "repr-1",
                            "hunk": 0,
                            "addr": 0,
                            "end": 4,
                            "style": "symbol",
                            "element_kind": "immediate",
                            "operand_index": 0,
                            "symbol": "PLAYER_START_LIVES",
                        }
                    },
                ),
            ],
        ),
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        artifact = c_backend.CListingArtifact.create(
            c_backend._CBackendSourceFile(binary_path, "amiga-hunk"),
            metadata_text=str(metadata_path),
            include_dir=str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            project_root=PROJECT_ROOT,
        )
        try:
            navigation, _profile = artifact.navigation_payload()
        finally:
            artifact.close()
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert policy["target_equates"] == [{"name": "PLAYER_START_LIVES", "value": 42}]
    assert policy["manual_representations"] == [
        {
            "section_index": 0,
            "offset": 0,
            "size": 4,
            "style": "symbol",
            "operand_index": 0,
            "symbol": "PLAYER_START_LIVES",
        }
    ]
    assert "PLAYER_START_LIVES\tEQU\t$2A\n" in rendered
    assert "\tmove.w #PLAYER_START_LIVES,d0\n" in rendered
    equates = navigation["groups"]["equates"]
    assert len(equates) == 1
    assert equates[0]["symbol"] == "PLAYER_START_LIVES"
    assert equates[0]["operand"] == "$2A"
    assert equates[0]["ref_count"] == 2
    assert [ref["access"] for ref in equates[0]["refs"]] == ["definition", "reference"]
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_target_equate_value_representation_renders_definition_text(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-target-equate-repr.bin"
    source_text = """    SECTION section,code
start:
    move.w #42,d0
    rts
    dc.w 0
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        _target_equate_manual_action_log_text(
            source,
            [
                _target_equate_action(
                    1,
                    "create_manual_target_equate",
                    {
                        "target_equate": {
                            "target_equate_id": "equate-1",
                            "name": "PLAYER_START_LIVES",
                            "value": 42,
                            "value_representation": "symbol",
                            "value_expression": "40+2",
                        }
                    },
                ),
                _target_equate_action(
                    2,
                    "create_manual_target_equate",
                    {
                        "target_equate": {
                            "target_equate_id": "equate-2",
                            "name": "ASCII_SPACE",
                            "value": 32,
                            "value_representation": "character",
                        }
                    },
                ),
                _target_equate_action(
                    3,
                    "create_manual_target_equate",
                    {
                        "target_equate": {
                            "target_equate_id": "equate-3",
                            "name": "SPACE_BITS",
                            "value": 32,
                            "value_representation": "binary",
                        }
                    },
                ),
            ],
        ),
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert policy["target_equates"] == [
        {
            "name": "PLAYER_START_LIVES",
            "value": 42,
            "value_expression": "40+2",
            "value_representation": "symbol",
        },
        {
            "name": "ASCII_SPACE",
            "value": 32,
            "value_representation": "character",
        },
        {
            "name": "SPACE_BITS",
            "value": 32,
            "value_representation": "binary",
        },
    ]
    assert "ASCII_SPACE\tEQU\t' '\n" in rendered
    assert "PLAYER_START_LIVES\tEQU\t40+2\n" in rendered
    assert "SPACE_BITS\tEQU\t%00100000\n" in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_target_equate_rename_and_remove_update_rendered_source(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-target-equate-rename.bin"
    source_text = """    SECTION section,code
start:
    move.w #42,d0
    rts
    dc.w 0
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    base_actions = [
        _target_equate_action(
            1,
            "create_manual_target_equate",
            {
                "target_equate": {
                    "target_equate_id": "equate-1",
                    "name": "PLAYER_START_LIVES",
                    "value": 42,
                },
            },
        ),
        _target_equate_action(
            2,
            "create_manual_representation",
            {
                "representation": {
                    "representation_id": "repr-1",
                    "hunk": 0,
                    "addr": 0,
                    "end": 4,
                    "style": "symbol",
                    "element_kind": "immediate",
                    "operand_index": 0,
                    "symbol": "PLAYER_START_LIVES",
                },
            },
        ),
    ]
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        _target_equate_manual_action_log_text(
            source,
            [
                *base_actions,
                _target_equate_action(
                    3,
                    "rename_manual_target_equate",
                    {
                        "target_equate": {
                            "target_equate_id": "equate-1",
                            "previous_name": "PLAYER_START_LIVES",
                            "name": "PLAYER_INITIAL_LIVES",
                        }
                    },
                ),
            ],
        ),
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert "PLAYER_INITIAL_LIVES\tEQU\t$2A\n" in rendered
    assert "\tmove.w #PLAYER_INITIAL_LIVES,d0\n" in rendered
    assert "PLAYER_START_LIVES" not in rendered

    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        _target_equate_manual_action_log_text(
            source,
            [
                *base_actions,
                _target_equate_action(
                    3,
                    "remove_manual_target_equate",
                    {"target_equate": {"target_equate_id": "equate-1", "name": "PLAYER_START_LIVES"}},
                ),
            ],
        ),
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "EQU" not in rendered
    assert "\tmove.w #$2A,d0\n" in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_lvo_semantic_hint_renders_symbolic_immediate(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-lvo-hint.bin"
    source_text = """    SECTION section,code
start:
    move.l #-552,d0
    rts
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-18T00:00:01+00:00",
                "kind": "create_manual_semantic_hint",
                "semantic_hint": {
                    "semantic_hint_id": "hint-1",
                    "hunk": 0,
                    "addr": 0,
                    "element_kind": "immediate",
                    "operand_index": 0,
                    "domain": "lvo",
                    "symbol": "exec.library/OpenLibrary",
                    "value": -552,
                    "namespace": "exec.library",
                    "function": "OpenLibrary",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert policy["manual_representations"] == [
        {"section_index": 0, "offset": 0, "size": 1, "style": "symbol", "operand_index": 0, "symbol": "_LVOOpenLibrary"}
    ]
    assert '    INCLUDE "exec/exec_lib.i"\n' in rendered
    assert "\tmove.l #_LVOOpenLibrary,d0\n" in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_struct_offset_semantic_hint_renders_symbolic_immediate(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-struct-offset-hint.bin"
    source_text = """    SECTION section,code
start:
    move.l #0,d0
    rts
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-18T00:00:01+00:00",
                "kind": "create_manual_semantic_hint",
                "semantic_hint": {
                    "semantic_hint_id": "hint-1",
                    "hunk": 0,
                    "addr": 0,
                    "element_kind": "immediate",
                    "operand_index": 0,
                    "domain": "struct_offset",
                    "symbol": "LN.ln_Succ",
                    "value": 0,
                    "namespace": "LN",
                    "field": "ln_Succ",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        policy = effective_policy_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert policy["manual_representations"] == [
        {"section_index": 0, "offset": 0, "size": 1, "style": "symbol", "operand_index": 0, "symbol": "LN_SUCC"}
    ]
    assert '    INCLUDE "exec/nodes.i"\n' in rendered
    assert "\tmove.l #LN_SUCC,d0\n" in rendered
    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_manual_register_seed_projects_library_base_into_rendering(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-register-seed.bin"
    source_text = """    SECTION section,code
start:
    jsr -552(a6)
    rts
    dc.w 0
"""
    original, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {
                "record": "manual_action_log_header",
                "version": 1,
                "target_identity": build_target_identity(source),
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_register_seed",
                "register_seed": {
                    "register_seed_id": "exec-base",
                    "entry_offset": 0,
                    "register": "A6",
                    "kind": "library_base",
                    "library_name": "exec.library",
                    "struct_name": "LIB",
                    "context_name": "exec.library",
                    "note": "Manual semantic helper",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert '    INCLUDE "exec/exec_lib.i"\n' in rendered
    assert "\tjsr _LVOOpenLibrary(a6)\n" in rendered
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        rendered,
        include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
        project_root=PROJECT_ROOT,
    )
    assert rebuilt == original


def test_project_source_benchmark_uses_facts_v2(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    binary_path = tmp_path / "demo"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[dict[str, object]] = []

    class FakeArtifact:
        def __init__(self) -> None:
            self.closed = False

        def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return {"total_rows": 1}, self._source_profile()

        def _source_profile(self) -> dict[str, object]:
            return {
                "generation": "facts_v2_listing_artifact_source_text",
                "backend": "amiga-raw",
                "analysis_backend": "facts_v2",
                "path": "demo",
                "facts_v2": {
                    "platform_base_slot_count": 1,
                    "platform_call_count": 2,
                    "platform_effect_count": 3,
                    "asm_source_symbolic_instructions": 4,
                    "decode_seconds": 0.01,
                    "seed_seconds": 0.02,
                    "fixed_point_seconds": 0.03,
                    "render_ir_seconds": 0.04,
                    "source_render_seconds": 0.05,
                    "render_ir_statements": 6,
                    "render_ir_labels": 7,
                    "render_ir_instructions": 8,
                    "render_ir_data_spans": 9,
                    "asm_source_bytes": 10,
                },
                "timing": {"source_seconds": 0.125, "source_emit_seconds": 0.025, "total_seconds": 0.15},
            }

        def source_text_with_profile(self) -> tuple[str, dict[str, object]]:
            return "SECTION code,code\n", self._source_profile()

        def close(self) -> None:
            self.closed = True

    artifact = FakeArtifact()

    def fake_create(cls, source_file, *, metadata_text: str, include_dir: str, project_root: Path):
        calls.append(
            {
                "platform_name": source_file.platform_name,
                "path": source_file.path,
                "entry_offset": source_file.entry_offset,
                "metadata_text": metadata_text,
                "include_dir": include_dir,
                "project_root": project_root,
            }
        )
        return artifact

    monkeypatch.setattr(c_backend.CListingArtifact, "create", classmethod(fake_create))

    benchmark, text = benchmark_project_source_with_text_from_c_backend(
        source,
        project_root=tmp_path,
    )

    assert benchmark == {
        "benchmark_version": 1,
        "platform": "amiga-raw",
        "path": "demo",
        "analysis_backend": "facts_v2",
        "facts_v2": {
            "platform_base_slot_count": 1,
            "platform_call_count": 2,
            "platform_effect_count": 3,
            "asm_source_symbolic_instructions": 4,
            "decode_seconds": 0.01,
            "seed_seconds": 0.02,
            "fixed_point_seconds": 0.03,
            "render_ir_seconds": 0.04,
            "source_render_seconds": 0.05,
            "render_ir_statements": 6,
            "render_ir_labels": 7,
            "render_ir_instructions": 8,
            "render_ir_data_spans": 9,
            "asm_source_bytes": 10,
        },
        "analysis": {
            "recovered_platform_base_slot_count": 1,
            "recovered_platform_call_count": 2,
            "recovered_platform_effect_count": 3,
        },
        "render": {
            "symbol_ref_count": 0,
            "symbol_ref_abs_count": 0,
            "symbol_ref_pc_relative_count": 0,
            "symbol_ref_section_relative_count": 0,
            "statement_count": 6,
            "label_statement_count": 7,
            "instruction_statement_count": 8,
            "data_statement_count": 9,
            "symbolic_instruction_count": 4,
            "text_bytes": 10,
        },
        "timing": {
            "source_seconds": 0.125,
            "source_emit_seconds": 0.025,
            "total_seconds": 0.15,
            "decode_seconds": 0.01,
            "seed_seconds": 0.02,
            "fixed_point_seconds": 0.03,
            "render_ir_seconds": 0.04,
            "source_render_seconds": 0.05,
            "analysis_seconds": 0.06,
            "ir_build_seconds": 0.04,
            "render_seconds": 0.05,
        },
    }
    assert text == "SECTION code,code\n"
    assert calls == [
        {
            "platform_name": "amiga-raw",
            "path": binary_path,
            "entry_offset": 12,
            "metadata_text": "",
            "include_dir": str(tmp_path / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            "project_root": tmp_path,
        }
    ]
    assert artifact.closed is True


def test_platform_file_cli_disassemble_uses_artifact_options(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    cli = PROJECT_ROOT / "src" / "build" / "platform_file_cli.exe"
    binary_path = tmp_path / "sample.hunk"
    benchmark_path = tmp_path / "benchmark.json"
    source_path = tmp_path / "sample.s"
    binary_path.write_bytes(make_synthetic_hunkexe())

    result = subprocess.run(
        [
            str(cli),
            "disassemble-file",
            "--benchmark-json-out",
            str(benchmark_path),
            "--output",
            str(source_path),
            "amiga-hunk",
            str(binary_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "SECTION" in source_path.read_text(encoding="utf-8")
    profile = json.loads(benchmark_path.read_text(encoding="utf-8"))
    assert profile["generation"] == "facts_v2_listing_artifact_source_text"
    assert "source_emit_seconds" in profile["timing"]
    assert profile["timing"]["total_seconds"] >= profile["timing"]["source_seconds"]

    rejected = subprocess.run(
        [str(cli), "disassemble-file", "--syntax", "genam", "amiga-hunk", str(binary_path)],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert rejected.returncode == 2
    assert "unexpected argument: --syntax" in rejected.stderr


def test_real_dll_raw_listing_source_assembles_to_raw_payload(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "raw.bin"
    output_path = tmp_path / "rebuilt.bin"
    binary_path.write_bytes(b"\x4E\x75")
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=0x4000,
        entrypoint=0x4000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        source,
        project_root=PROJECT_ROOT,
    )
    rebuilt, assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        source_text,
        output_path=output_path,
        project_root=PROJECT_ROOT,
    )

    assert rebuilt == b"\x4E\x75"
    assert output_path.read_bytes() == b"\x4E\x75"
    assert source_profile["backend"] == "amiga-raw"
    assert assembler_profile["rebuilt_bytes"] == 2


def test_project_source_facts_v2_direct_rebuild_uses_direct_c_api(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "sample"
    output_path = tmp_path / "rebuilt.bin"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return (
            b"\0\0\x03\xf3",
            {"generation": "facts_v2_asm_source", "facts_v2": {"asm_source_refused": False}},
            {"facts_v2_direct_rebuild": True, "direct_rebuild_refused": False},
        )

    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend._platform_file_facts_v2_direct_rebuild_profile",
        fake_file_run,
    )

    rebuilt, source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        source,
        output_path=output_path,
        project_root=tmp_path,
    )

    assert rebuilt == b"\0\0\x03\xf3"
    assert source_profile["generation"] == "facts_v2_asm_source"
    assert direct_profile["facts_v2_direct_rebuild"] is True
    assert calls == [
        (
            "platform_file_facts_v2_direct_rebuild_path_bytes_profile_alloc",
            "amiga-hunk",
            str(binary_path),
            "",
            str(output_path),
        ),
    ]


def test_c_profiled_operation_frees_bytes_profiles_and_error_buffers() -> None:
    buffers: list[ctypes.Array[ctypes.c_char]] = []

    class FakeDll:
        def __init__(self) -> None:
            self.freed_text: list[int] = []
            self.freed_bytes: list[int] = []

        def platform_file_free_text(self, value: ctypes.c_void_p) -> None:
            self.freed_text.append(int(value.value or 0))

        def platform_file_free_bytes(self, value: ctypes.c_void_p) -> None:
            self.freed_bytes.append(int(value.value or 0))

    dll = FakeDll()

    def keep(data: bytes) -> int:
        buffer = ctypes.create_string_buffer(data)
        buffers.append(buffer)
        return ctypes.addressof(buffer)

    def fake_function(*args: object) -> int:
        out_data, out_size, out_profile_a, out_profile_b, out_error = args[-5:]
        out_data._obj.value = keep(b"rebuilt")  # type: ignore[attr-defined]
        out_size._obj.value = 7  # type: ignore[attr-defined]
        out_profile_a._obj.value = keep(b'{"source": true}')  # type: ignore[attr-defined]
        out_profile_b._obj.value = keep(b'{"direct": true}')  # type: ignore[attr-defined]
        out_error._obj.value = keep(b"boom")  # type: ignore[attr-defined]
        return 0

    result = c_backend.CProfiledOperation(dll).call_bytes_with_profiles(  # type: ignore[arg-type]
        fake_function,
        profile_count=2,
    )

    assert result.data == b"rebuilt"
    assert result.profiles == ({"source": True}, {"direct": True})
    assert result.error_text == "boom"
    assert len(dll.freed_text) == 3
    assert len(dll.freed_bytes) == 1


def test_c_profiled_operation_frees_profile_and_error_on_failure_status() -> None:
    buffers: list[ctypes.Array[ctypes.c_char]] = []

    class FakeDll:
        def __init__(self) -> None:
            self.freed_text: list[int] = []

        def platform_file_free_text(self, value: ctypes.c_void_p) -> None:
            self.freed_text.append(int(value.value or 0))

    dll = FakeDll()

    def keep(data: bytes) -> int:
        buffer = ctypes.create_string_buffer(data)
        buffers.append(buffer)
        return ctypes.addressof(buffer)

    def fake_function(*args: object) -> int:
        out_profile, out_error = args[-2:]
        out_profile._obj.value = keep(b'{"compare": true}')  # type: ignore[attr-defined]
        out_error._obj.value = keep(b"failed")  # type: ignore[attr-defined]
        return 23

    result = c_backend.CProfiledOperation(dll).call_profile(fake_function)  # type: ignore[arg-type]

    assert result.status == 23
    assert result.profile == {"compare": True}
    assert result.error_text == "failed"
    assert len(dll.freed_text) == 2


def test_c_profiled_operation_frees_single_profile_bytes_shape() -> None:
    buffers: list[ctypes.Array[ctypes.c_char]] = []

    class FakeDll:
        def __init__(self) -> None:
            self.freed_text: list[int] = []
            self.freed_bytes: list[int] = []

        def platform_file_free_text(self, value: ctypes.c_void_p) -> None:
            self.freed_text.append(int(value.value or 0))

        def platform_file_free_bytes(self, value: ctypes.c_void_p) -> None:
            self.freed_bytes.append(int(value.value or 0))

    dll = FakeDll()

    def keep(data: bytes) -> int:
        buffer = ctypes.create_string_buffer(data)
        buffers.append(buffer)
        return ctypes.addressof(buffer)

    def fake_function(*args: object) -> int:
        out_data, out_size, out_profile, out_error = args[-4:]
        out_data._obj.value = keep(b"assembled")  # type: ignore[attr-defined]
        out_size._obj.value = 9  # type: ignore[attr-defined]
        out_profile._obj.value = keep(b'{"assemble": true}')  # type: ignore[attr-defined]
        out_error._obj.value = keep(b"note")
        return 0

    result = c_backend.CProfiledOperation(dll).call_bytes_with_profile(fake_function)  # type: ignore[arg-type]

    assert result.status == 0
    assert result.data == b"assembled"
    assert result.profile == {"assemble": True}
    assert result.error_text == "note"
    assert len(dll.freed_text) == 2
    assert len(dll.freed_bytes) == 1


def test_c_profiled_operation_frees_text_profile_shape_on_failure_status() -> None:
    buffers: list[ctypes.Array[ctypes.c_char]] = []

    class FakeDll:
        def __init__(self) -> None:
            self.freed_text: list[int] = []

        def platform_file_free_text(self, value: ctypes.c_void_p) -> None:
            self.freed_text.append(int(value.value or 0))

    dll = FakeDll()

    def keep(data: bytes) -> int:
        buffer = ctypes.create_string_buffer(data)
        buffers.append(buffer)
        return ctypes.addressof(buffer)

    def fake_function(*args: object) -> int:
        out_text, out_profile = args[-2:]
        out_text._obj.value = keep(b"render failed")  # type: ignore[attr-defined]
        out_profile._obj.value = keep(b'{"source": true}')  # type: ignore[attr-defined]
        return 7

    result = c_backend.CProfiledOperation(dll).call_text_with_profile(fake_function)  # type: ignore[arg-type]

    assert result.status == 7
    assert result.text == "render failed"
    assert result.profile == {"source": True}
    assert len(dll.freed_text) == 2


def test_project_source_facts_v2_direct_rebuild_compare_uses_compare_c_api(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "sample"
    output_path = tmp_path / "rebuilt.bin"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return (
            b"\0\0\x03\xf3",
            {"generation": "facts_v2_asm_source", "facts_v2": {"asm_source_refused": False}},
            {"facts_v2_direct_rebuild": True, "direct_rebuild_compared": True, "direct_rebuild_exact": True},
        )

    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend._platform_file_facts_v2_direct_rebuild_profile",
        fake_file_run,
    )

    rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        source,
        output_path=output_path,
        compare_original=True,
        project_root=tmp_path,
    )

    assert rebuilt == b"\0\0\x03\xf3"
    assert direct_profile["direct_rebuild_exact"] is True
    assert calls == [
        (
            "platform_file_facts_v2_direct_rebuild_compare_path_bytes_profile_alloc",
            "amiga-hunk",
            str(binary_path),
            "",
            str(output_path),
        ),
    ]


def test_project_source_facts_v2_direct_compare_classifies_hunk_container_oddity(
    tmp_path: Path,
) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "odd_container.exe"
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=b"\x4e\x75\x00\x00") + u32(1010))
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="odd_container.exe",
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        source,
        compare_original=True,
        project_root=PROJECT_ROOT,
    )

    assert rebuilt != binary_path.read_bytes()
    assert direct_profile["direct_rebuild_exact"] is False
    assert direct_profile["direct_compare_semantic_exact"] is True
    assert direct_profile["direct_compare_payload_exact"] is True
    assert direct_profile["direct_compare_relocation_semantics_exact"] is True
    assert direct_profile["direct_compare_container_oddity"] is True
    assert direct_profile["direct_compare_status"] == "semantic_container_oddity"
    assert direct_profile["direct_compare_status_id"] == 2
    assert direct_profile["direct_compare_exactness_id"] == 2
    assert direct_profile["direct_compare_issue_group_flags"] & 0x4 == 0x4
    assert direct_profile["direct_compare_range_count"] >= 1
    assert any(item["kind"] == "section_payload" for item in direct_profile["direct_compare_file_layout"])
    payload_layout = next(item for item in direct_profile["direct_compare_file_layout"] if item["kind"] == "section_payload")
    assert payload_layout["section_index"] == 0
    assert payload_layout["section_offset_start"] == 0
    assert direct_profile["direct_compare_source_hint_count"] == 0
    assert direct_profile["direct_compare_source_hints"] == []
    assert direct_profile["assembler_policy_kind"] == 2
    assert direct_profile["assembler_policy_flags"] & 0x3 == 0x3


def test_project_source_facts_v2_direct_rebuild_preserves_hunk_reloc32short_encoding(
    tmp_path: Path,
) -> None:
    _requires_c_backend_dlls()
    original = bytes.fromhex(
        "000003f3"
        "00000000"
        "00000001"
        "00000000"
        "00000000"
        "00000002"
        "000003e9"
        "00000002"
        "00000000"
        "00000004"
        "000003fc"
        "00010000"
        "0000"
        "00010000"
        "0004"
        "0000"
        "0000"
        "000003f2"
    )
    binary_path = tmp_path / "reloc32short.exe"
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="reloc32short.exe",
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        source,
        compare_original=True,
        project_root=PROJECT_ROOT,
    )

    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True
    assert direct_profile["direct_compare_status_id"] == 1
    assert direct_profile["direct_compare_exactness_id"] == 1
    assert direct_profile["direct_compare_issue_group_flags"] == 0
    assert direct_profile["assembler_policy_kind"] == 2
    assert direct_profile["assembler_policy_hunk_relocation_record_count"] == 1


def test_project_source_facts_v2_direct_rebuild_disk_entry_uses_buffer_c_api(
    monkeypatch, tmp_path: Path
) -> None:
    disk_path = tmp_path / "demo.adf"
    output_path = tmp_path / "rebuilt.bin"
    disk_path.write_bytes(b"disk")
    source = DiskEntryBinarySource(
        kind=BinarySourceKind.DISK_ENTRY,
        disk_id="demo",
        adf_path=disk_path,
        entry_path="c/Run",
        display_path="demo.adf::c/Run",
        analysis_cache_path=tmp_path / "binary.analysis",
        project_root=tmp_path,
    )
    calls: list[tuple[object, ...]] = []

    def fake_extract(path: Path, entry_path: str, *, project_root: Path) -> bytes:
        assert path == disk_path
        assert entry_path == "c/Run"
        assert project_root == tmp_path
        return b"\0\0\x03\xf3"

    def fake_buffer_run(
        function_name: str,
        platform_name: str,
        data: bytes,
        metadata_text: str,
        display_path: str,
        output_text: str,
        *,
        project_root: Path,
    ) -> tuple[bytes, dict[str, object], dict[str, object]]:
        calls.append((function_name, platform_name, data, metadata_text, display_path, output_text, project_root))
        return (
            data,
            {"generation": "facts_v2_asm_source", "facts_v2": {"asm_source_refused": False}},
            {"facts_v2_direct_rebuild": True, "direct_rebuild_refused": False},
        )

    monkeypatch.setattr(c_backend, "extract_disk_entry_with_c_backend", fake_extract)
    monkeypatch.setattr(c_backend, "_platform_file_facts_v2_direct_rebuild_buffer_profile", fake_buffer_run)
    monkeypatch.setattr(
        c_backend,
        "_platform_file_facts_v2_direct_rebuild_profile",
        lambda *args, **kwargs: pytest.fail("disk-entry direct rebuild should use buffer API"),
    )

    rebuilt, source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        source,
        output_path=output_path,
        project_root=tmp_path,
    )

    assert rebuilt == b"\0\0\x03\xf3"
    assert source_profile["generation"] == "facts_v2_asm_source"
    assert direct_profile["facts_v2_direct_rebuild"] is True
    assert calls == [
        (
            "platform_file_facts_v2_direct_rebuild_buffer_bytes_profile_alloc",
            "amiga-hunk",
            b"\0\0\x03\xf3",
            "",
            "demo.adf::c/Run",
            str(output_path),
            tmp_path,
        ),
    ]


def test_project_source_facts_v2_direct_rebuild_surfaces_refusal(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "sample"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    source_profile = {"facts_v2": {"asm_source_refused": False}}
    direct_profile = {
        "facts_v2_direct_rebuild": True,
        "direct_rebuild_refused": True,
        "direct_rebuild_refusal_reason": "lossy_numeric_hunk_relocations",
    }

    def fake_file_run(function_name: str, *args: object, project_root):
        raise FactsV2DirectRebuildRefused(source_profile, direct_profile)

    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend._platform_file_facts_v2_direct_rebuild_profile",
        fake_file_run,
    )

    with pytest.raises(FactsV2DirectRebuildRefused) as exc_info:
        facts_v2_direct_rebuild_project_source_with_c_backend_profile(source, project_root=tmp_path)

    assert exc_info.value.source_profile == source_profile
    assert exc_info.value.direct_profile == direct_profile


def test_project_source_facts_v2_defines_private_exec_lvo_symbol(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "private_lvo.exe"
    metadata_path = tmp_path / "target_metadata.json"
    output_path = tmp_path / "private_lvo.rebuilt"
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=bytes.fromhex("4eaeffdc4e75")))
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "program",
                "entry_register_seeds": [
                    {
                        "entry_offset": 0,
                        "hunk": 0,
                        "register": "A6",
                        "kind": "library_base",
                        "library_name": "exec.library",
                        "struct_name": "LIB",
                        "context_name": None,
                    }
                ],
                "seeded_code_entrypoints": [{"hunk": 0, "addr": 0}],
            }
        ),
        encoding="utf-8",
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "private_lvo.analysis",
    )

    text, profile = listing_artifact_source_text_with_c_backend_profile(
        source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    rebuilt, assemble_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        text,
        include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
        output_path=output_path,
        target_cpu="any",
        project_root=PROJECT_ROOT,
    )

    assert "_LVOexecPrivate1\tEQU\t-36\n" in text
    assert "\tjsr _LVOexecPrivate1(a6)\n" in text
    assert profile["facts_v2"]["asm_source_refused"] is False
    assert profile["facts_v2"]["asm_source_instruction_render_failures"] == 0
    assert output_path.read_bytes() == rebuilt
    assert assemble_profile["assemble_c_api"] is True


def test_project_source_facts_v2_atari_empty_relocation_stream_roundtrips(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    if not assembler.exists():
        pytest.skip("m68k assembler app is missing; run cmd /c src\\build.bat")
    binary_path = tmp_path / "empty_reloc.prg"
    source_path = tmp_path / "empty_reloc.s"
    rebuilt_path = tmp_path / "empty_reloc.rebuilt.prg"
    original = make_synthetic_atari_prg(
        b"\x4E\x75", b"", 0, program_flags=7, relocation_flag=0xFFFF
    ) + u32(0)
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    text, profile = listing_artifact_source_text_with_c_backend_profile(source, project_root=PROJECT_ROOT)

    assert profile["analysis_backend"] == "facts_v2"
    assert text.startswith(
        "    COMMENT HEAD=$7\n"
        "    COMMENT ATARI_RELOC_FLAG=$FFFF\n"
        "    COMMENT ATARI_RELOC=$00000000\n"
        "    SECTION TEXT,code"
    )
    source_path.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "atari-st",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "atarist_includes" / "devpac_3_10" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert rebuilt_path.read_bytes() == original


def test_project_source_facts_v2_direct_rebuild_preserves_atari_eof_relocation_terminator(
    tmp_path: Path,
) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "eof_reloc.prg"
    original = make_synthetic_atari_prg(
        b"\0\0\0\0\0\0\0\0",
        b"",
        0,
        symbol_table_type=7,
        program_flags=0x1234,
        relocation_flag=0xFFFF,
    ) + u32(4)
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        source,
        compare_original=True,
        project_root=PROJECT_ROOT,
    )

    assert rebuilt == original
    assert direct_profile["direct_rebuild_exact"] is True
    assert direct_profile["assembler_policy_flags"] & 0x20 == 0x20


def test_project_source_reproduction_compare_atari_uses_object_semantics(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "atari_content_exact.prg"
    original = make_synthetic_atari_prg(
        b"\x4e\x75",
        b"",
        0,
        symbol_table_type=7,
        program_flags=0x1234,
        relocation_flag=0xFFFF,
    ) + u32(0)
    rebuilt = make_synthetic_atari_prg(
        b"\x4e\x75",
        b"",
        0,
        symbol_table_type=0,
        program_flags=0,
        relocation_flag=0xFFFF,
    ) + u32(0)
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    compare_profile = reproduction_compare_rebuilt_bytes_with_c_backend_profile(
        source,
        rebuilt,
        project_root=PROJECT_ROOT,
    )

    assert compare_profile["facts_v2_reproduction_compare"] is True
    assert compare_profile["reproduction_compare_full_file_exact"] is False
    assert compare_profile["reproduction_compare_payload_exact"] is True
    assert compare_profile["reproduction_compare_content_exact"] is True
    assert compare_profile["reproduction_compare_status_id"] == 2
    assert compare_profile["reproduction_compare_exactness_id"] == 2
    assert compare_profile["reproduction_compare_issue_group_flags"] & 0x4 == 0x4
    assert compare_profile["reproduction_compare_issue_group_flags"] & 0x100 == 0x100
    assert compare_profile["reproduction_compare_file_layout"][:2] == [
        {"kind": "header", "file_start": 0, "file_end": 28, "length": 28},
        {
            "kind": "section_payload",
            "file_start": 28,
            "file_end": 30,
            "length": 2,
            "section_index": 0,
            "hunk": 0,
            "section_offset_start": 0,
        },
    ]
    assert {
        "kind": "atari_header_field_mismatch",
        "field": "symbol_table_type",
        "original": 7,
        "rebuilt": 0,
    } in compare_profile["reproduction_compare_file_shape_diagnostics"]
    assert {
        "kind": "atari_header_field_mismatch",
        "field": "flags",
        "original": 0x1234,
        "rebuilt": 0,
    } in compare_profile["reproduction_compare_file_shape_diagnostics"]


def test_project_source_facts_v2_atari_large_relocation_stream_is_chunked(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    if not assembler.exists():
        pytest.skip("m68k assembler app is missing; run cmd /c src\\build.bat")
    binary_path = tmp_path / "large_reloc.prg"
    source_path = tmp_path / "large_reloc.s"
    rebuilt_path = tmp_path / "large_reloc.rebuilt.prg"
    relocation_stream = u32(0) + (b"\0" * 320)
    original = make_synthetic_atari_prg(
        b"\x4E\x75", b"", 0, program_flags=7, relocation_flag=0xFFFF
    ) + relocation_stream
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    text, profile = listing_artifact_source_text_with_c_backend_profile(source, project_root=PROJECT_ROOT)
    reloc_lines = [line for line in text.splitlines() if "ATARI_RELOC" in line]

    assert profile["analysis_backend"] == "facts_v2"
    assert any(line.startswith("    COMMENT ATARI_RELOC=$") for line in reloc_lines)
    assert any(line.startswith("    COMMENT ATARI_RELOC+=$") for line in reloc_lines)
    assert all(len(line) < 256 for line in reloc_lines)
    source_path.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "atari-st",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "atarist_includes" / "devpac_3_10" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert rebuilt_path.read_bytes() == original


def test_project_source_facts_v2_atari_symbol_table_roundtrips(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    if not assembler.exists():
        pytest.skip("m68k assembler app is missing; run cmd /c src\\build.bat")
    binary_path = tmp_path / "symbols.prg"
    source_path = tmp_path / "symbols.s"
    rebuilt_path = tmp_path / "symbols.rebuilt.prg"
    symbol_table = bytes(index & 0xFF for index in range(300))
    original = make_synthetic_atari_prg(
        b"\x4E\x75",
        b"",
        0,
        symbol_table=symbol_table,
        symbol_table_type=0x1234,
        program_flags=7,
        relocation_flag=0xFFFF,
    ) + u32(0)
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    text, profile = listing_artifact_source_text_with_c_backend_profile(source, project_root=PROJECT_ROOT)
    symbol_lines = [line for line in text.splitlines() if "ATARI_SYMBOL" in line]

    assert profile["analysis_backend"] == "facts_v2"
    assert "    COMMENT ATARI_SYMBOL_TYPE=$1234\n" in text
    assert any(line.startswith("    COMMENT ATARI_SYMBOLS=$") for line in symbol_lines)
    assert any(line.startswith("    COMMENT ATARI_SYMBOLS+=$") for line in symbol_lines)
    assert all(len(line) < 256 for line in symbol_lines)
    source_path.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "atari-st",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "atarist_includes" / "devpac_3_10" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert rebuilt_path.read_bytes() == original


def test_atari_symbolic_relocation_materializes_image_relative_payload(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    if not assembler.exists():
        pytest.skip("m68k assembler app is missing; run cmd /c src\\build.bat")
    source_path = tmp_path / "symbolic_reloc.s"
    rebuilt_path = tmp_path / "symbolic_reloc.prg"
    source_path.write_text(
        "\n".join(
            [
                "    COMMENT ATARI_RELOC_FLAG=$0",
                "    SECTION TEXT,code",
                "    dc.l $12345678",
                "    dc.l bss_target",
                "    rts",
                "    SECTION DATA,data",
                "    dc.l bss_target",
                "    SECTION BSS,bss,$8",
                "    DS.B $4",
                "bss_target:",
                "    DS.B $4",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "atari-st",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "atarist_includes" / "devpac_3_10" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rebuilt = rebuilt_path.read_bytes()
    assert rebuilt[2:6] == u32(10)
    assert rebuilt[6:10] == u32(4)
    assert rebuilt[10:14] == u32(8)
    assert rebuilt[28 + 4 : 28 + 8] == u32(18)
    assert rebuilt[28 + 10 : 28 + 14] == u32(18)
    assert rebuilt[28 + 14 : 28 + 20] == u32(4) + b"\x06\0"


def test_project_listing_artifact_skips_analysis_json_when_no_platform_calls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\x4e\x75")
    target_dir = tmp_path / "targets" / "raw_demo"
    target_dir.mkdir(parents=True)
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "path": str(binary_path),
                "address_model": "local_offset",
                "load_address": 0,
                "entrypoint": 0,
                "code_start_offset": 0,
            }
        ),
        encoding="utf-8",
    )

    class FakeArtifact:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

        def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return (
                {"total_rows": 1},
                {
                    "generation": "facts_v2_listing_artifact_summary",
                    "facts_v2": {"platform_call_count": 0},
                },
            )

        def navigation_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            raise AssertionError("navigation JSON should not be requested while building the artifact cache")

        def analysis_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            raise AssertionError("analysis JSON should not be requested when the C profile has no platform calls")

    artifact = FakeArtifact()
    monkeypatch.setattr(
        c_backend.CListingArtifact,
        "create",
        classmethod(lambda cls, source_file, *, metadata_text, include_dir, project_root: artifact),
    )

    total_rows, profile, returned_artifact = c_backend.build_project_listing_artifact_profile(
        "raw_demo",
        project_root=tmp_path,
    )

    assert total_rows == 1
    assert profile["facts_v2"] == {"platform_call_count": 0}
    assert returned_artifact is artifact
    assert artifact.closed is False


def test_project_listing_artifact_build_uses_summary_only_with_platform_calls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\x4e\x75")
    target_dir = tmp_path / "targets" / "raw_demo"
    target_dir.mkdir(parents=True)
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "path": str(binary_path),
                "address_model": "local_offset",
                "load_address": 0,
                "entrypoint": 0,
                "code_start_offset": 0,
            }
        ),
        encoding="utf-8",
    )

    class FakeArtifact:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

        def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return (
                {"total_rows": 1},
                {
                    "generation": "facts_v2_listing_artifact_summary",
                    "facts_v2": {"platform_call_count": 1},
                },
            )

        def navigation_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            raise AssertionError("navigation JSON should not be requested while building the artifact cache")

        def analysis_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            raise AssertionError("full analysis JSON should not be requested for API calls")

    artifact = FakeArtifact()
    monkeypatch.setattr(
        c_backend.CListingArtifact,
        "create",
        classmethod(lambda cls, source_file, *, metadata_text, include_dir, project_root: artifact),
    )

    total_rows, profile, returned_artifact = c_backend.build_project_listing_artifact_profile(
        "raw_demo",
        project_root=tmp_path,
    )

    assert total_rows == 1
    assert profile["generation"] == "facts_v2_listing_artifact_summary"
    assert returned_artifact is artifact
    assert artifact.closed is False


def test_real_dll_listing_artifact_address_helpers_pass_typed_integer_args() -> None:
    _requires_c_backend_dlls()
    total_rows, _profile, artifact = c_backend.build_project_listing_artifact_profile("amiga_hunk_genam")
    try:
        assert total_rows > 0
        source_row = artifact.row_for_source_offset(section_index=0, offset=0)
        assert source_row is not None
        assert source_row.get("start_offset") == 0
        addr_window, _addr_profile = artifact.addr_window_payload(addr=0, before=0, after=3)
        assert addr_window["rows"]
        assert addr_window["rows"][0].get("start_offset") == 0
    finally:
        artifact.close()


def test_real_dll_facts_v2_listing_rows_use_plan_metadata_without_source_model(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rows, api_calls, profile = build_project_listing_rows_from_source_with_c_artifact(
        source,
        metadata_text="",
        project_root=PROJECT_ROOT,
    )

    assert api_calls == {}
    assert "source_model_seconds" not in profile["timing"]
    assert any(row["kind"] == "directive" and str(row["text"]).lstrip().startswith("SECTION ") for row in rows)
    assert any(
        row["kind"] == "instruction" and row["opcode_or_directive"] == "rts" and row["bytes"] == "4e75"
        for row in rows
    )


def test_real_dll_raw_runtime_absolute_entry_uses_execution_view(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "stage.bin"
    binary_path.write_bytes(b"\x4e\x75" + (b"\0" * 14) + b"\x4e\x75")
    metadata_path = tmp_path / "target_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [],
                "execution_views": [
                    {
                        "source_start": 0,
                        "source_end": 18,
                        "base_addr": 0x400,
                        "name": "loaded_stage",
                    }
                ],
                "absolute_code_labels": [],
            }
        ),
        encoding="utf-8",
    )

    artifact = c_backend.CListingArtifact.create(
        c_backend._CBackendSourceFile(binary_path, "amiga-raw", 0x410),
        metadata_text=str(metadata_path),
        include_dir="",
        project_root=PROJECT_ROOT,
    )
    try:
        source, _profile = artifact.source_text_with_profile()
    finally:
        artifact.close()

    assert "    ORG $400\n\tdc.b $4E,$75\n\tdcb.b $E,$00\nabs_0_00000410:\n\trts\n" in source
    assert "abs_0_00000410:\n\trts\n" in source
    assert "loc_0_00000010:" not in source


def test_real_dll_epic_runtime_absolute_raw_source_keeps_single_load_org() -> None:
    _requires_c_backend_dlls()
    paths = resolve_project_paths(
        "amiga_disk_epic-1992-ocean-disk-1__amiga_raw_bootloader_stage_1",
        project_root=PROJECT_ROOT,
    )

    with effective_metadata_file(paths.target_dir) as metadata_path:
        source, _profile = listing_artifact_source_text_with_c_backend_profile(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert source.count("    ORG $40000\n") == 1
    assert "loc_0_00000000:\n    ORG $40000\nabs_0_00040000:\n" in source
    assert "    ORG $0\n" not in source


def test_real_dll_epic_bootblock_does_not_materialize_load_address_org() -> None:
    _requires_c_backend_dlls()
    paths = resolve_project_paths(
        "amiga_disk_epic-1992-ocean-disk-1__amiga_raw_bootblock",
        project_root=PROJECT_ROOT,
    )

    with effective_metadata_file(paths.target_dir) as metadata_path:
        policy = effective_policy_project_source_with_c_backend(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )["analysis_policy"]
        source, _profile = listing_artifact_source_text_with_c_backend_profile(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        analysis = analyze_project_source_with_c_backend(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert not any(item.get("name") == "bootblock" for item in policy["runtime_ranges"])
    assert {"section_index": 0, "runtime_address": 0x7000C} not in policy["runtime_entry_points"]
    assert "    ORG $70000\n" not in source
    assert "boot_entry:\n" in source
    assert 'dc.b "DOS",$00\t; NOTE: boot magic\n' in source
    assert "runtime_code_00000400\tEQU\t$400\n" in source
    assert "\tlea.l runtime_code_00000400.l,a1\n" in source
    assert "abs_0_0007008C-" not in source
    assert analysis["sections"][0]["recovered_platform_runtime_copies"] == [
        {
            "offset": 0x8C,
            "source_addr": 0x20000,
            "destination_addr": 0x864,
            "byte_length": 0x3000,
            "handoff_addr": 0x86C,
            "source_kind": "post_read_runtime_copy",
        }
    ]


def test_real_dll_bootblock_policy_io_seed_symbolizes_saved_request_setup(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    original_source = (
        "    SECTION section,code\n"
        '    dc.b "DOS",$00\n'
        "    dc.l 0\n"
        "    dc.l 0\n"
        "boot_entry:\n"
        "    lea.l saved_io(pc),a2\n"
        "    move.l a1,(a2)\n"
        "    bsr.w helper\n"
        "    lea.l saved_io(pc),a5\n"
        "    movea.l (a5),a1\n"
        "    move.l #$400,$002C(a1)\n"
        "    move.l #$4E00,$0024(a1)\n"
        "    move.l #$1E200,$0028(a1)\n"
        "    move.w #$2,$001C(a1)\n"
        "    movea.l $0004.w,a6\n"
        "    jsr -456(a6)\n"
        "    move.w #$3,d0\n"
        "    lea.l $0001E202.l,a0\n"
        "    lea.l $00000864.l,a1\n"
        "copy_loop:\n"
        "    move.b (a0)+,(a1)+\n"
        "    dbf.w d0,copy_loop\n"
        "    bsr.w helper\n"
        "    jsr $00000866.l\n"
        "    rts\n"
        "helper:\n"
        "    rts\n"
        "saved_io:\n"
        "    dc.l 0\n"
    )
    include_dir = PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"
    original, _ = assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        original_source,
        include_dir=include_dir,
        project_root=PROJECT_ROOT,
    )
    binary_path = tmp_path / "bootblock_io_seed.bin"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(original)
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "bootblock",
                "entry_register_seeds": [
                    {
                        "entry_offset": None,
                        "hunk": 0,
                        "register": "A6",
                        "kind": "library_base",
                        "library_name": "exec.library",
                        "struct_name": "LIB",
                        "context_name": None,
                    },
                    {
                        "entry_offset": None,
                        "hunk": 0,
                        "register": "A1",
                        "kind": "struct_ptr",
                        "note": "IOStdReq",
                        "struct_name": "IO",
                        "context_name": "trackdisk.device",
                    },
                ],
                "bootblock": {
                    "entrypoint": 0x7000C,
                    "load_address": 0x70000,
                    "bootcode_offset": 0x0C,
                },
            }
        ),
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "bootblock_io_seed.analysis",
    )

    rendered, _profile = listing_artifact_source_text_with_c_backend_profile(
        source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    analysis = analyze_project_source_with_c_backend(
        source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    rebuilt, _ = assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        rendered,
        include_dir=include_dir,
        project_root=PROJECT_ROOT,
    )

    typed_accesses = analysis["sections"][0]["recovered_platform_typed_accesses"]
    disk_reads = analysis["sections"][0]["recovered_platform_disk_reads"]
    runtime_copies = analysis["sections"][0]["recovered_platform_runtime_copies"]
    assert "\tmove.l #$400,IO_OFFSET(a1)\n" in rendered
    assert "\tmove.l #$4E00,IO_LENGTH(a1)\n" in rendered
    assert "\tmove.l #$1E200,IO_DATA(a1)\n" in rendered
    assert "\tmove.w #$2,IO_COMMAND(a1)\n" in rendered
    assert {access["field_name"] for access in typed_accesses} == {
        "IO_OFFSET",
        "IO_LENGTH",
        "IO_DATA",
        "IO_COMMAND",
    }
    assert {access["type_provenance_kind"] for access in typed_accesses} == {"policy_seed"}
    assert disk_reads == [
        {
            "offset": 62,
            "command_value": 2,
            "command_name": "CMD_READ",
            "disk_offset": 0x400,
            "byte_length": 0x4E00,
            "destination_addr": 0x1E200,
            "source_kind": "logical_disk_offset",
        }
    ]
    assert runtime_copies == [
        {
            "offset": 66,
            "source_addr": 0x1E202,
            "destination_addr": 0x864,
            "byte_length": 4,
            "handoff_addr": 0x866,
            "source_kind": "post_read_runtime_copy",
        }
    ]
    assert rebuilt == original

    overwritten_source = original_source.replace(
        "    bsr.w helper\n",
        "    clr.l (a2)\n"
        "    bsr.w helper\n",
    )
    overwritten, _ = assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        overwritten_source,
        include_dir=include_dir,
        project_root=PROJECT_ROOT,
    )
    overwritten_binary_path = tmp_path / "bootblock_io_seed_overwritten.bin"
    overwritten_binary_path.write_bytes(overwritten)
    overwritten_rendered, _profile = listing_artifact_source_text_with_c_backend_profile(
        overwritten_binary_source := RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=overwritten_binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0x70000,
            entrypoint=0x7000C,
            code_start_offset=0x0C,
            display_path=str(overwritten_binary_path),
            analysis_cache_path=tmp_path / "bootblock_io_seed_overwritten.analysis",
        ),
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    overwritten_analysis = analyze_project_source_with_c_backend(
        overwritten_binary_source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )

    assert "_LVODoIO(a6)" in overwritten_rendered
    assert "IO_COMMAND(a1)" not in overwritten_rendered
    assert "\tmove.w #$2,$001C(a1)\n" in overwritten_rendered
    assert overwritten_analysis["sections"][0]["recovered_platform_disk_reads"] == []
    assert overwritten_analysis["sections"][0]["recovered_platform_runtime_copies"] == []


def test_real_dll_ice_bootloader_stage_recovers_copied_runtime_payload_without_bad_addend() -> None:
    _requires_c_backend_dlls()
    paths = resolve_project_paths(
        "amiga_disk_ice-1991-06-28-the-silents__amiga_raw_bootloader_stage_1",
        project_root=PROJECT_ROOT,
    )

    with effective_metadata_file(paths.target_dir) as metadata_path:
        source, _profile = listing_artifact_source_text_with_c_backend_profile(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )

    assert source.count("    ORG $40000\n") == 1
    assert "runtime_code_00006000\tEQU\t$6000\n" in source
    assert "\tlea.l runtime_code_00006000.l,a1\n" in source
    assert "\tjmp runtime_code_00006000.l\n" in source
    assert "abs_0_00040046:\n\tlea.l abs_0_000449C2(pc),a0\n" in source
    assert "dat_0046:" not in source
    assert "abs_0_00040046-" not in source


def test_real_dll_runtime_ref_to_copied_range_start_seeds_org_entry_code(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "runtime_ref_copied_entry.bin"
    code = bytes.fromhex(
        "41fa000e"      # lea.l payload(pc),a0
        "43f900000400"  # lea.l $400.l,a1
        "7000"          # moveq.l #0,d0
        "32d8"          # move.w (a0)+,(a1)+
        "4e75"          # rts
        "4e75"          # payload: rts
        "0000"
    )
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=code))
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "runtime_ref_copied_entry.analysis",
    )

    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        source,
        metadata_path=None,
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "loc_0_00000010:\n\trts\n" in source_text
    assert any(
        ref.get("reason_name") == "runtime_view_entry" and ref.get("offset") == 0x10
        for ref in analyze_project_source_with_c_backend(
            source,
            metadata_path=None,
            project_root=PROJECT_ROOT,
        )["sections"][0]["code_start_refs"]
    )
    assert "\tdc.b $4E,$75" not in source_text


def test_real_dll_bootstrap_copied_image_jump_target_decodes_without_compression(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    source = (
        "    SECTION section,code\n"
        "start:\n"
        "    lea.l stage2(pc),a0\n"
        "    lea.l start(pc),a1\n"
        "    lea.l $300.w,a2\n"
        "    moveq.l #47,d0\n"
        "copy_stage2:\n"
        "    move.b (a0)+,(a2)+\n"
        "    dbf.w d0,copy_stage2\n"
        "    jmp $300.w\n"
        "stage2:\n"
        "    lea.l $10000.l,a2\n"
        "    lea.l $10050.l,a3\n"
        "    move.l #$53,d0\n"
        "    cmpa.l a2,a1\n"
        "    bcs.b copy_forward\n"
        "    adda.l d0,a1\n"
        "    adda.l d0,a2\n"
        "copy_back_loop:\n"
        "    move.b -(a1),-(a2)\n"
        "    subq.l #1,d0\n"
        "    bne.b copy_back_loop\n"
        "    jmp (a3)\n"
        "copy_forward:\n"
        "    move.b (a1)+,(a2)+\n"
        "    subq.l #1,d0\n"
        "    bne.b copy_forward\n"
        "    jmp (a3)\n"
        "stage2_end:\n"
        "    dcb.b 14,0\n"
        "runtime_entry:\n"
        "    moveq.l #7,d0\n"
        "    rts\n"
        "image_end:\n"
        "    dcb.b 44,0\n"
    )
    binary_path = tmp_path / "bootstrap_copied_image.hunk"
    metadata_path = tmp_path / "target_metadata.json"
    rebuilt, _ = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary_path,
        project_root=PROJECT_ROOT,
    )
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "seeded_code_entrypoints": [
                    {
                        "addr": 0,
                        "hunk": 0,
                        "name": "start",
                        "seed_origin": "manual",
                        "review_status": "accepted",
                        "citation": "test fixture entrypoint",
                    }
                ],
                "execution_views": [
                    {
                        "source_start": 0,
                        "source_end": 0x80,
                        "base_addr": 0x20000,
                        "name": "loaded_wrapper_payload",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    binary_source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "bootstrap_copied_image.analysis",
    )

    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    analysis = analyze_project_source_with_c_backend(
        binary_source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    section = analysis["sections"][0]
    views_by_runtime = {view["runtime_address"]: view for view in section["runtime_views"]}
    rebuilt_from_rendered, _ = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        project_root=PROJECT_ROOT,
    )

    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert views_by_runtime[0x20000]["materialization_reason_name"] == "overlaid_by_runtime_copy"
    assert views_by_runtime[0x300]["materialization_reason_name"] == "exit_to_larger_runtime_range"
    assert views_by_runtime[0x10000]["materialization_reason_name"] == "discovered_copy_entry"
    assert any(
        ref.get("reason_name") == "control_target"
        and ref.get("runtime_address") == 0x10050
        and ref.get("offset") == 0x50
        for ref in section["code_start_refs"]
    )
    assert "    ORG $10000\nabs_0_00010000:\n" in source_text
    assert "abs_0_00010050:\n\tmoveq.l #7,d0\n\trts\n" in source_text
    assert "runtime_code_00010050\tEQU\t$10050\n" not in source_text
    assert "\tdc.b $70,$07,$4E,$75" not in source_text
    assert "    ORG $20000\n" not in source_text
    assert "    ORG $300\n" not in source_text
    assert rebuilt_from_rendered == rebuilt


def test_real_dll_pandora_bootstrap_does_not_promote_zero_padding_as_code() -> None:
    _requires_c_backend_dlls()
    target_name = "amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8"
    paths = resolve_project_paths(target_name, project_root=PROJECT_ROOT)
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )
    combined = _facts_v2_listing_analysis_for_project(target_name)
    section = combined["analysis"]["sections"][0]

    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert "    ORG $10000\nabs_0_00010000:\n" in source_text
    assert "\tlea.l abs_0_00010000.l,a2\n" in source_text
    assert "\tlea.l abs_0_0001046A.l,a3\n" in source_text
    assert "abs_0_0001046A:\n\tlea.l $000039FC.l,a0\n" in source_text
    assert "runtime_code_0001046A\tEQU\t$1046A\n" not in source_text
    assert "\tmove.l #abs_0_0005D5DE,bltapt(a5)" in source_text
    assert "\tmovea.l #abs_0_0001C3A8,a0\n" in source_text
    assert "    ORG $55370\n" not in source_text
    assert "    ORG $5548F\n" not in source_text
    assert "loc_0_00057800:\n" not in source_text
    assert "loc_0_00057D00:\n" not in source_text
    assert "loc_0_00000078:\n\tori.b #0,d0\n" not in source_text
    assert not any(ref.get("offset") == 0x78 for ref in section["code_start_refs"])
    assert not any(site.get("target") == 0x78 for site in section["recovered_indirect_sites"])
    assert any(
        record.get("record_kind") == "runtime_view"
        and record.get("source_offset") == 0
        and record.get("runtime_address") == 0x20000
        and record.get("entry_runtime_address") == 0x20000
        and record.get("entry_reason_name") == "policy_entry_point"
        for record in combined["analysis"]["memory_layout_records"]
    )
    assert any(
        record.get("record_kind") == "runtime_view"
        and record.get("source_offset") == 0
        and record.get("runtime_address") == 0x10000
        and record.get("entry_point_count", 0) == 0
        for record in combined["analysis"]["memory_layout_records"]
    )


def test_real_dll_starglider_replays_common_indirect_stub_trace_variants() -> None:
    _requires_c_backend_dlls()
    target_name = "amiga_disk_starglider-1987-rainbird__amiga_hunk_libs__mathieeedoubbas.library_3d4e4903"
    paths = _requires_project_paths(target_name)
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )
    combined = _facts_v2_listing_analysis_for_project(target_name)
    section = combined["analysis"]["sections"][0]

    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert "DPTst:\n\tmove.l d0,d1\n\tclr.l d0\n\tjsr fptrap.l" in source_text
    assert "dtst_1:\n\tsubq.l #1,d0\n\trts\n" in source_text
    assert "dtst_2:\n\taddq.l #1,d0\n\trts\n" in source_text
    assert "\tdc.b $22,$00,$42,$80,$4E,$B9" not in source_text
    assert any(
        ref.get("offset") == 0x236
        and ref.get("reason_name") == "control_target"
        and ref.get("source_offset") == 0x2D0
        for ref in section["code_start_refs"]
    )
    assert not any(0x230 <= signal.get("offset", 0) <= 0x250 for signal in section["orphan_code_signals"])


def test_real_dll_monam_callback_field_targets_decode_from_indirect_call() -> None:
    _requires_c_backend_dlls()
    paths = resolve_project_paths("amiga_hunk_monam302", project_root=PROJECT_ROOT)
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )
    combined = _facts_v2_listing_analysis_for_project("amiga_hunk_monam302")
    section = combined["analysis"]["sections"][0]

    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert "\tmovea.l $003E(a3),a0\n\tjsr $0000(a0)\n" in source_text
    assert "loc_0_00005F32:\n\tbra.w loc_0_00005F44\n" in source_text
    assert "loc_0_00005F32:\n\tdc.b $60,$00,$00,$10" not in source_text
    for offset in (0x5F32, 0x5FE2, 0x66F6, 0x6782, 0x682E):
        assert any(
            ref.get("offset") == offset
            and ref.get("reason_name") == "control_target"
            and ref.get("source_offset") == 0x5F2A
            for ref in section["code_start_refs"]
        )


def test_real_dll_magicland_org_bootstrap_decodes_copied_runtime_entry() -> None:
    _requires_c_backend_dlls()
    paths = resolve_project_paths("amiga_hunk_magicland_dizzy_md", project_root=PROJECT_ROOT)

    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "abs_0_0005BFF0:\n\tlea.l abs_0_0005C004(pc),a0\n" in source_text
    assert "\tdc.b $41,$FA,$00,$12,$21,$C8,$00,$80,$4E,$40" not in source_text
    _rebuilt, _direct_source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        compare_original=True,
        project_root=PROJECT_ROOT,
    )
    assert direct_profile["direct_compare_payload_exact"] is True
    assert direct_profile["direct_compare_relocation_semantics_exact"] is True
    assert direct_profile["direct_compare_semantic_exact"] is True


def test_real_dll_runtime_org_is_visible_in_listing_rows(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "stage.bin"
    binary_path.write_bytes(b"\x4e\x75" + (b"\0" * 14) + b"\x4e\x75")
    metadata_path = tmp_path / "target_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [],
                "execution_views": [
                    {
                        "source_start": 0,
                        "source_end": 18,
                        "base_addr": 0x400,
                        "name": "loaded_stage",
                    }
                ],
                "absolute_code_labels": [],
            }
        ),
        encoding="utf-8",
    )

    rows, _, _ = build_project_listing_rows_from_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0x410,
            code_start_offset=0x410,
            display_path=str(binary_path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )
    org_index = next(index for index, row in enumerate(rows) if str(row["text"]).strip() == "ORG $400")
    label_index = next(index for index, row in enumerate(rows) if row.get("label") == "abs_0_00000410")

    assert rows[org_index]["kind"] == "directive"
    assert rows[org_index]["opcode_or_directive"] == "ORG"
    assert rows[org_index]["operand_text"] == "$400"
    assert rows[org_index]["addr"] is None
    assert org_index < label_index


def test_real_dll_runtime_absolute_target_decode_does_not_invalidate_source_candidate(
    tmp_path: Path,
) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "runtime-target.bin"
    # The 32nd decoded candidate is an absolute control transfer into the same
    # runtime view. Decoding that target grows the candidate array.
    binary_path.write_bytes(
        (b"\x4e\x71" * 31)
        + bytes.fromhex("4eb900004050")
        + (b"\x4e\x71" * ((0x50 - 0x44) // 2))
        + b"\x4e\x75"
    )
    metadata_path = tmp_path / "target_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "execution_views": [
                    {
                        "source_start": 0,
                        "source_end": binary_path.stat().st_size,
                        "base_addr": 0x4000,
                        "name": "loaded_stage",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rows, _, _ = build_project_listing_rows_from_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(binary_path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )

    assert any(row["kind"] == "instruction" and row["start_offset"] == 0x3E for row in rows)
    assert any(row["kind"] == "instruction" and row["start_offset"] == 0x50 for row in rows)


def test_real_dll_analysis_api_exposes_source_free_render_index_profile(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "analysis-index.bin"
    binary_path.write_bytes(bytes.fromhex("4eb9000000084e714e75"))

    analysis = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            0,
            0,
            "",
            "",
            project_root=PROJECT_ROOT,
        )
    )

    facts_v2 = analysis["profile"]["facts_v2"]
    assert analysis["profile"]["generation"] == "facts_v2_analysis"
    assert facts_v2["asm_source_enabled"] is False
    assert facts_v2["asm_source_bytes"] == 0
    assert facts_v2["render_ir_statements"] >= 3
    assert facts_v2["accepted_instructions"] >= 2


def test_real_dll_facts_v2_listing_rows_auto_classifies_copper_list_from_cop_pointer(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "copper.bin"
    binary_path.write_bytes(
        bytes.fromhex(
            "23fc0000000c00dff080"
            "4e75"
            "01004200"
            "00e01234"
            "00e25678"
            "013e0000"
            "009c8010"
            "2c07fffe"
            "fffffffe"
        )
    )
    metadata_path = tmp_path / "target_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "execution_views": [
                    {
                        "source_start": 0,
                        "source_end": 40,
                        "base_addr": 0,
                        "name": "loaded_stage",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    combined = analyze_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(binary_path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )
    rows = combined["listing"]["rows"]
    copper_rows = [row for row in rows if row["kind"] == "data" and row.get("data_class") == "copper_list"]
    copper_layout_rows = [
        row for row in rows
        if row["kind"] == "data" and row.get("structured_data", {}).get("semantic_role") == "copper_list"
    ]
    pointer_row = next(row for row in rows if row["addr"] == 0 and row["kind"] == "instruction")

    assert pointer_row["runtime_address_refs"] == [
        {
            "offset": 0,
            "operand_index": 0,
            "target_section_index": 0,
            "target_offset": 0x0C,
            "sink_address": 0xDFF080,
            "runtime_address": 0x0C,
            "confidence": 2,
            "data_class": "copper_list",
            "data_class_flags": 1,
        }
    ]
    assert pointer_row["code_start_refs"] == [
        {
            "offset": 0,
            "reason": 2,
            "reason_name": "policy_entry_offset",
            "confidence": 3,
            "source_section_index": 0,
            "source_offset": 0,
            "runtime_address": None,
            "size": 10,
        }
    ]
    assert all(row["addr"] == 0x0C for row in copper_rows)
    assert all(row["addr"] == 0x0C for row in copper_layout_rows)
    assert [str(row["text"]).strip() for row in copper_layout_rows] == [
        "; display layout 1 bitmap plane $12345678",
        "dc.w bplcon0,(4<<PLNCNTSHFT)|COLORON\t; display 4 bitplanes lores color",
        "dc.w bplpt,bitmap_12345678_hi\t; bitmap pointer $12345678",
        "dc.w bplpt+$02,bitmap_12345678_lo",
        "dc.w sprpt+$1E,$0000",
        "dc.w intreq,INTF_SETCLR|INTF_COPER",
        "dc.w COPPER_WAIT|$2C06,$FFFE\t; copper wait v=$2C h=$06 mask $FFFE",
        "dc.w $FFFF,$FFFE",
    ]
    bitmap_pointer_row = next(row for row in copper_rows if str(row["text"]).strip().startswith("dc.w bplpt,"))
    assert bitmap_pointer_row["runtime_address_refs"] == [
        {
            "offset": 0x10,
            "operand_index": None,
            "target_section_index": None,
            "target_offset": None,
            "sink_address": None,
            "runtime_address": 0x12345678,
            "confidence": 2,
            "data_class": "bitmap",
            "data_class_flags": 32,
        }
    ]
    assert all(not row.get("runtime_address_refs") for row in copper_rows[3:])

    analysis = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            0,
            0,
            str(metadata_path),
            "",
            project_root=PROJECT_ROOT,
        )
    )
    structured_items = analysis["analysis_policy"]["structured_data_items"]
    assert any(
        item["section_index"] == 0
        and item["offset"] == 0x0C
        and item["size"] == 28
        and item["semantic_role"] == "copper_list"
        for item in structured_items
    )


def test_real_dll_facts_v2_listing_rows_exclude_source_only_directives_without_source_text(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "boot.bin"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(bytes.fromhex("223c000030004eaefdd84e75"))
    metadata_path.write_text(
        json.dumps(
            {
                "entry_register_seeds": [
                    {
                        "entry_offset": 0,
                        "hunk": 0,
                        "register": "A6",
                        "kind": "library_base",
                        "library_name": "exec.library",
                        "struct_name": "LIB",
                        "context_name": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0x70000,
        entrypoint=0x70000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rows, api_calls, profile = build_project_listing_rows_from_source_with_c_artifact(
        source,
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )

    assert api_calls[(0, 6)]["function"] == "OpenLibrary"
    assert rows
    first_label_index = next(index for index, row in enumerate(rows) if row["kind"] == "label")
    header_texts = [str(row["text"]).lstrip() for row in rows[:first_label_index]]
    section_header_index = next(index for index, text in enumerate(header_texts) if text.startswith("SECTION "))
    assert any(text.startswith("INCLUDE ") for text in header_texts[:section_header_index])
    assert rows[section_header_index - 1]["kind"] == "blank"
    known_index = next(index for index, row in enumerate(rows) if str(row["text"]).lstrip().startswith("; KNOWN:"))
    assert known_index == first_label_index - 1
    assert all(row["addr"] is None for row in rows[:first_label_index])
    assert not any(str(row["text"]).lstrip().startswith("INCLUDE ") for row in rows[first_label_index:])
    assert any(row["kind"] == "instruction" and row["opcode_or_directive"] == "jsr" for row in rows)


def test_real_dll_facts_v2_listing_rows_emit_api_calls(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "boot.bin"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(b"\0" * 12 + bytes.fromhex("4eaefdd84e75"))
    metadata_path.write_text(
        json.dumps(
            {
                "entry_register_seeds": [
                    {
                        "entry_offset": 12,
                        "hunk": 0,
                        "register": "A6",
                        "kind": "library_base",
                        "library_name": "exec.library",
                        "struct_name": "LIB",
                        "context_name": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    source_text, _source_profile = listing_artifact_source_text_with_c_backend_profile(
        source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    rows, api_calls, profile = build_project_listing_rows_from_source_with_c_artifact(
        source,
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )

    assert any(row["kind"] == "instruction" and row["opcode_or_directive"] == "jsr" for row in rows)
    assert "_LVOOpenLibrary" in source_text
    assert profile["facts_v2"]["platform_call_count"] == 1
    assert api_calls[(0, 12)]["library"] == "exec.library"
    assert api_calls[(0, 12)]["function"] == "OpenLibrary"
    assert {item["name"] for item in api_calls[(0, 12)]["inputs"]} == {"libName", "version"}
    assert api_calls[(0, 12)]["outputs"] == [
        {
            "name": "library",
            "regs": ["D0"],
            "type": "struct Library *",
            "o_struct": "LIB",
            "source": "parsed NDK",
            "semantic_kind": None,
            "value_domain": None,
        }
    ]
    call_row = next(row for row in rows if row["kind"] == "instruction" and row["addr"] == 12)
    assert "platform_call" not in call_row
    assert call_row["api_call"]["library"] == "exec.library"
    assert call_row["api_call"]["function"] == "OpenLibrary"
    assert {item["name"] for item in call_row["api_call"]["inputs"]} == {"libName", "version"}
    assert call_row["api_call"]["outputs"] == api_calls[(0, 12)]["outputs"]

    combined = analyze_source_with_c_artifact(source, metadata_text=str(metadata_path), project_root=PROJECT_ROOT)
    effects = combined["analysis"]["sections"][0]["recovered_platform_effects"]
    assert effects == [
        {
            "offset": 12,
            "kind": 4,
            "reg_kind": 1,
            "reg_index": 0,
            "displacement": -32768,
            "field_disp": -32768,
            "base_name": None,
            "symbol_name": "library",
            "type_name": "LIB",
            "semantic_kind": None,
            "value_domain_name": None,
            "has_constant_value": 0,
            "constant_value": 0,
            "target_section_index": 4294967295,
            "target_offset": 4294967295,
        }
    ]


def test_real_dll_facts_v2_bootblock_metadata_recovers_entry_context_and_pc_data_label(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "bootblock.bin"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(
        bytes.fromhex(
            "444f5300"
            "c0200f19"
            "00000370"
            "43fa0018"
            "4eaeffa0"
            "4a80"
            "670a"
            "2040"
            "20680016"
            "7000"
            "4e75"
            "70ff"
            "60fa"
            "646f732e6c69627261727900"
        )
        + (b"\0" * 16)
    )
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "bootblock",
                "entry_register_seeds": [
                    {
                        "entry_offset": None,
                        "hunk": 0,
                        "register": "A6",
                        "kind": "library_base",
                        "library_name": "exec.library",
                        "struct_name": "LIB",
                        "context_name": None,
                    },
                    {
                        "entry_offset": None,
                        "hunk": 0,
                        "register": "A1",
                        "kind": "struct_ptr",
                        "note": "IOStdReq (open trackdisk.device)",
                        "struct_name": "IO",
                        "context_name": "trackdisk.device",
                    },
                ],
                "bootblock": {
                    "entrypoint": 0x7000C,
                    "load_address": 0x70000,
                    "bootcode_offset": 0x0C,
                },
            }
        ),
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    policy = effective_policy_project_source_with_c_backend(
        source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )["analysis_policy"]
    source_text, _source_profile = listing_artifact_source_text_with_c_backend_profile(
        source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    rows, api_calls, profile = build_project_listing_rows_from_source_with_c_artifact(
        source,
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )

    assert policy["runtime_ranges"] == []
    assert policy["runtime_entry_points"] == []
    assert "    ORG $70000\n" not in source_text
    assert api_calls[(0, 16)]["function"] == "FindResident"
    assert "boot_entry:" in source_text
    assert (
        "    ; KNOWN: base A6=exec.library:LIB; type A1=IOStdReq (open trackdisk.device):IO\n"
        "boot_entry:"
        in source_text
    )
    assert "\tlea.l loc_0_00000026(pc),a1\n" in source_text
    assert "\tjsr _LVOFindResident(a6)\n" in source_text
    assert "\tmovea.l RT_INIT(a0),a0\n" in source_text
    assert 'INCLUDE "exec/resident.i"' in source_text
    assert "loc_0_00000026:" in source_text
    assert '\tdc.b "dos.library",$00\t; string\n' in source_text
    assert "facts_v2 data bytes" not in source_text
    assert any(row["kind"] == "instruction" and "loc_0_00000026(pc)" in str(row["text"]) for row in rows)
    assert any(
        row["kind"] == "label" and row["addr"] == 0x26 and str(row["text"]).strip() == "loc_0_00000026:"
        for row in rows
    )
    assert any(row["addr"] == 0 and row["data_class"] == "string" for row in rows)


def test_real_dll_facts_v2_listing_rows_emit_base_slot_effects(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "open_library_slot.bin"
    binary_path.write_bytes(
        bytes.fromhex(
            "2c780004"
            "4eaeff3a"
            "2c40"
            "43f90000002c"
            "2f0e"
            "2c780004"
            "4eaefdd8"
            "2c5f"
            "2d4000be"
            "2c6e00be"
            "4eaefef2"
            "4e75"
            "0000"
            "696e74756974696f6e2e6c69627261727900"
        )
    )

    combined = analyze_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(binary_path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    facts = combined["profile"]["facts_v2"]
    effects = combined["analysis"]["sections"][0]["recovered_platform_effects"]

    assert facts["platform_base_slot_count"] == 1
    assert {
        "offset": 28,
        "kind": 2,
        "displacement": 190,
        "base_name": "IntuitionBase",
    } in [
        {
            "offset": effect["offset"],
            "kind": effect["kind"],
            "displacement": effect["displacement"],
            "base_name": effect["base_name"],
        }
        for effect in effects
    ]


def test_real_dll_facts_v2_listing_rows_emit_wrapper_function_args(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "wrapper_args.bin"
    binary_path.write_bytes(
        bytes.fromhex(
            "222f0008"
            "2f3c00010000"
            "48780060"
            "61000008"
            "2d400120"
            "4e75"
            "2f0e"
            "2c780004"
            "4cef00030008"
            "4eaeff3a"
            "2c5f"
            "4e75"
        )
    )

    combined = analyze_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(binary_path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    args = combined["analysis"]["sections"][0]["recovered_function_args"]
    summaries = combined["analysis"]["sections"][0]["recovered_local_call_summaries"]
    effects = combined["analysis"]["sections"][0]["recovered_platform_effects"]

    assert {
        "function_offset": 24,
        "stack_offset": 4,
        "reg_kind": 1,
        "reg_index": 0,
        "symbol_name": "byteSize",
        "type_name": "unsigned long",
        "semantic_kind": None,
        "value_domain_name": None,
    } in [
        {
            "function_offset": arg["function_offset"],
            "stack_offset": arg["stack_offset"],
            "reg_kind": arg["reg_kind"],
            "reg_index": arg["reg_index"],
            "symbol_name": arg["symbol_name"],
            "type_name": arg["type_name"],
            "semantic_kind": arg["semantic_kind"],
            "value_domain_name": arg["value_domain_name"],
        }
        for arg in args
    ]
    assert {
        "function_offset": 24,
        "stack_offset": 8,
        "reg_kind": 1,
        "reg_index": 1,
        "symbol_name": "attributes",
        "type_name": "ULONG",
        "value_domain_name": "exec.allocmem.attributes",
    } in [
        {
            "function_offset": arg["function_offset"],
            "stack_offset": arg["stack_offset"],
            "reg_kind": arg["reg_kind"],
            "reg_index": arg["reg_index"],
            "symbol_name": arg["symbol_name"],
            "type_name": arg["type_name"],
            "value_domain_name": arg["value_domain_name"],
        }
        for arg in args
    ]
    assert summaries == [
        {
            "target_offset": 24,
            "effect_kind": 4,
            "reg_kind": 1,
            "reg_index": 0,
            "success_reg_kind": 0,
            "success_reg_index": 0,
            "success_value_known": 0,
            "success_reg_value": 0,
            "base_name": None,
            "symbol_name": "memoryBlock",
            "type_name": "void *",
            "semantic_kind": None,
            "value_domain_name": None,
            "has_constant_value": 0,
            "constant_value": 0,
        }
    ]
    assert {
        "offset": 18,
        "kind": 5,
        "displacement": 288,
        "symbol_name": "memoryBlock",
        "type_name": "void *",
    } in [
        {
            "offset": effect["offset"],
            "kind": effect["kind"],
            "displacement": effect["displacement"],
            "symbol_name": effect["symbol_name"],
            "type_name": effect["type_name"],
        }
        for effect in effects
    ]


def test_real_dll_facts_v2_propagates_opendevice_instance_to_io_calls(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "device_calls.bin"
    binary_path.write_bytes(
        bytes.fromhex(
            "41f900000032"
            "43ee0040"
            "337c0009001c"
            "2c780004"
            "4eaefe44"
            "2c780004"
            "43ee0040"
            "4eaefe38"
            "2c780004"
            "43ee0040"
            "4eaefe3e"
            "4e75"
        )
        + b"input.device\0"
    )

    combined = analyze_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(binary_path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    calls = combined["analysis"]["sections"][0]["recovered_platform_calls"]
    by_function = {call["function_name"]: call for call in calls if call.get("function_name")}
    typed_accesses = combined["analysis"]["sections"][0]["recovered_platform_typed_accesses"]
    listing_rows = combined["listing"]["rows"]

    assert by_function["OpenDevice"]["device_name"] == "input.device"
    assert by_function["DoIO"]["device_name"] == "input.device"
    assert by_function["CloseDevice"]["device_name"] == "input.device"
    assert any(access["field_name"] == "IO_COMMAND" and access["offset"] == 10 for access in typed_accesses)
    assert any("IO_COMMAND(a1)" in row["text"] for row in listing_rows)
    assert any(
        access["field_name"] == "IO_COMMAND"
        for row in listing_rows
        for access in row.get("typed_accesses", [])
    )


def test_real_dll_facts_v2_propagates_typed_base_through_stack_storage(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "typed_stack.bin"
    binary_path.write_bytes(
        bytes.fromhex(
            "41f90000002a"
            "43ee0040"
            "2f0e"
            "2c780004"
            "4eaefe44"
            "2c5f"
            "206e0054"
            "2f480100"
            "206f0100"
            "0c6800240014"
            "4e75"
        )
        + b"timer.device\0"
    )

    combined = analyze_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(binary_path),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    typed_accesses = combined["analysis"]["sections"][0]["recovered_platform_typed_accesses"]
    listing_rows = combined["listing"]["rows"]

    assert any(access["field_name"] == "LIB_VERSION" and access["offset"] == 34 for access in typed_accesses)
    assert any("LIB_VERSION(a0)" in row["text"] for row in listing_rows)
    assert any(
        access["field_name"] == "LIB_VERSION"
        for row in listing_rows
        for access in row.get("typed_accesses", [])
    )


def test_project_source_raw_binary_passes_metadata_register_seeds(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "boot.bin"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    metadata_path.write_text(
        """{
  "entry_register_seeds": [
    {"entry_offset": null, "register": "A6", "kind": "library_base", "library_name": "exec.library", "struct_name": "LIB", "context_name": null},
    {"entry_offset": null, "register": "A1", "kind": "struct_ptr", "note": "IOStdReq", "struct_name": "IO", "context_name": "trackdisk.device"}
  ],
  "seeded_code_entrypoints": [
    {"addr": 20, "hunk": 0, "name": "extra_entry"}
  ]
}
""",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[str, ...]] = []
    artifact_calls: list[dict[str, object]] = []
    artifact = _FakeSourceArtifact("; raw\n", {"facts_v2": {"asm_source_refused": False}})

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return '{"sections":[]}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)
    _patch_render_source_artifact(monkeypatch, artifact_calls, artifact)

    analyze_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=tmp_path)
    render_project_source_with_c_backend(
        source,
        metadata_path=metadata_path,
        project_root=tmp_path,
    )

    assert calls == [
        (
            "platform_file_facts_v2_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            12,
            0,
            0,
            str(metadata_path),
            "",
        ),
    ]
    assert artifact_calls == [
        {
            "platform_name": "amiga-raw",
            "path": binary_path,
            "entry_offset": 12,
            "runtime_load_address": None,
            "metadata_text": str(metadata_path),
            "include_dir": str(tmp_path / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            "project_root": tmp_path,
        }
    ]


def test_generic_metadata_loader_omits_platform_specific_data(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    dll = ctypes.CDLL(str(PROJECT_ROOT / "src" / "build" / "platform_file_lib.dll"))
    dll.platform_file_analysis_policy_load_target_metadata.argtypes = [
        ctypes.POINTER(_M68kAnalysisPolicy),
        ctypes.c_char_p,
        _M68kDiagSink,
    ]
    dll.platform_file_analysis_policy_load_target_metadata.restype = ctypes.c_int
    dll.platform_file_analysis_policy_load_target_metadata_for_platform.argtypes = [
        ctypes.POINTER(_M68kAnalysisPolicy),
        ctypes.c_char_p,
        ctypes.c_char_p,
        _M68kDiagSink,
    ]
    dll.platform_file_analysis_policy_load_target_metadata_for_platform.restype = ctypes.c_int

    metadata_path = tmp_path / "target_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "library",
                "entry_register_seeds": [
                    {
                        "entry_offset": 0,
                        "register": "A6",
                        "kind": "library_base",
                        "library_name": "exec.library",
                        "struct_name": "LIB",
                    }
                ],
                "execution_views": [
                    {
                        "source_start": 0x20,
                        "source_end": 0x30,
                        "base_addr": 0x400,
                        "name": "loaded_stage",
                    }
                ],
                "absolute_code_labels": [
                    {
                        "addr": 0x404,
                        "name": "stage_entry",
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    }
                ],
                "seeded_code_labels": [
                    {
                        "addr": 0x28,
                        "hunk": 0,
                        "name": "manual_loop",
                        "comment": "loop head",
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    }
                ],
                "entry_comments": [
                    {
                        "addr": 0x2A,
                        "hunk": 0,
                        "comment": "manual note",
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    }
                ],
                "rsset_layout_regions": [
                    {
                        "offset": 0x22C,
                        "symbol": "app_startup_options_buffer",
                        "struct_name": None,
                        "pointer_struct": None,
                        "storage_kind": "pointer",
                        "semantic_type": "source_text_buffer",
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    },
                    {
                        "offset": 0x04,
                        "size": 2,
                        "layout_name": "work",
                        "base_symbol": "__game_work_base__",
                        "sizeof_symbol": "work_SIZEOF",
                        "symbol": "work_counter",
                        "struct_name": None,
                        "pointer_struct": None,
                        "storage_kind": "scalar",
                        "semantic_type": "counter",
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    }
                ],
                "custom_structs": [
                    {
                        "name": "Player",
                        "size": 16,
                        "fields": [
                            {
                                "name": "player_score",
                                "type": "long",
                                "offset": 8,
                                "size": 4,
                                "struct": None,
                                "pointer_struct": None,
                                "named_base": None,
                            }
                        ],
                    }
                ],
                "resident": {"name": "icon.library", "version": 40, "offset": 0, "hunk": 0},
            }
        ),
        encoding="utf-8",
    )

    generic_policy = _M68kAnalysisPolicy()
    generic_diagnostics = M68kDiagList()
    assert dll.platform_file_analysis_policy_load_target_metadata(
        ctypes.byref(generic_policy),
        str(metadata_path).encode("utf-8"),
        _M68kDiagSink(ctypes.pointer(generic_diagnostics)),
    ) == 0
    assert generic_policy.register_seed_count == 1
    assert generic_policy.runtime_range_count == 1
    assert generic_policy.runtime_ranges[0].offset == 0x20
    assert generic_policy.runtime_ranges[0].size == 0x10
    assert generic_policy.runtime_ranges[0].runtime_address == 0x400
    assert generic_policy.structured_data_item_count == 0
    assert generic_policy.rsset_layout_region_count == 0
    assert generic_policy.named_label_count == 2
    assert generic_policy.named_labels[0].offset == 0x28
    assert generic_policy.named_labels[0].name == b"manual_loop"
    assert generic_policy.named_labels[1].domain == 1
    assert generic_policy.named_labels[1].offset == 0x404
    assert generic_policy.named_labels[1].name == b"stage_entry"
    assert generic_policy.entry_comment_count == 2
    assert generic_policy.entry_comments[0].offset == 0x28
    assert generic_policy.entry_comments[0].comment == b"loop head"
    assert generic_policy.entry_comments[1].offset == 0x2A
    assert generic_policy.entry_comments[1].comment == b"manual note"
    assert generic_policy.custom_struct_count == 1
    assert generic_policy.custom_structs[0].name == b"Player"
    assert generic_policy.custom_structs[0].size == 16
    assert generic_policy.custom_structs[0].field_count == 1
    assert generic_policy.custom_structs[0].fields[0].name == b"player_score"
    assert generic_policy.custom_structs[0].fields[0].type_name == b"long"
    assert generic_policy.custom_structs[0].fields[0].offset == 8
    assert generic_policy.custom_structs[0].fields[0].size == 4

    amiga_policy = _M68kAnalysisPolicy()
    amiga_diagnostics = M68kDiagList()
    assert dll.platform_file_analysis_policy_load_target_metadata_for_platform(
        ctypes.byref(amiga_policy),
        str(metadata_path).encode("utf-8"),
        b"amiga-hunk",
        _M68kDiagSink(ctypes.pointer(amiga_diagnostics)),
    ) == 0
    assert amiga_policy.register_seed_count == 1
    assert amiga_policy.structured_data_item_count > 0
    assert amiga_policy.rsset_layout_region_count == 2
    assert amiga_policy.rsset_layout_regions[0].offset == 0x22C
    assert amiga_policy.rsset_layout_regions[0].layout_name == b"app"
    assert amiga_policy.rsset_layout_regions[0].base_symbol == b"__amiga_app_base__"
    assert amiga_policy.rsset_layout_regions[0].symbol == b"app_startup_options_buffer"
    assert amiga_policy.rsset_layout_regions[0].storage_kind == b"pointer"
    assert amiga_policy.rsset_layout_regions[1].offset == 0x04
    assert amiga_policy.rsset_layout_regions[1].size == 2
    assert amiga_policy.rsset_layout_regions[1].layout_name == b"work"
    assert amiga_policy.rsset_layout_regions[1].base_symbol == b"__game_work_base__"
    assert amiga_policy.rsset_layout_regions[1].sizeof_symbol == b"work_SIZEOF"
    assert amiga_policy.rsset_layout_regions[1].symbol == b"work_counter"
    assert amiga_policy.custom_struct_count == 1
    assert amiga_policy.custom_structs[0].fields[0].name == b"player_score"
    assert amiga_policy.named_label_count > 0


def test_real_dll_custom_struct_seed_renders_typed_field(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "custom_struct.bin"
    binary_path.write_bytes(bytes.fromhex("202800084e75"))
    metadata_path = tmp_path / "target_metadata.json"
    metadata = {
        "target_type": "raw_binary",
        "entry_register_seeds": [
            {
                "entry_offset": None,
                "hunk": 0,
                "register": "A0",
                "kind": "struct_ptr",
                "note": "GamePlayer",
                "struct_name": "GamePlayer",
                "context_name": None,
            }
        ],
        "custom_structs": [
            {
                "name": "GamePlayer",
                "size": 16,
                "fields": [
                    {
                        "name": "player_score",
                        "type": "long",
                        "offset": 8,
                        "size": 4,
                        "struct": None,
                        "pointer_struct": None,
                        "named_base": None,
                    }
                ],
            }
        ],
    }
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    combined = analyze_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(binary_path),
            analysis_cache_path=tmp_path / "custom_struct.analysis",
        ),
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )

    typed_accesses = combined["analysis"]["sections"][0]["recovered_platform_typed_accesses"]
    assert typed_accesses == [
        {
            "offset": 0,
            "operand_index": 0,
            "base_register": "A0",
            "displacement": 8,
            "field_offset": 8,
            "struct_size": 16,
            "field_size": 4,
            "root_struct_name": "GamePlayer",
            "owner_struct_name": "GamePlayer",
            "field_name": "player_score",
            "field_expr": "player_score",
            "inherited": 0,
            "nested": 0,
            "type_provenance_kind_id": 11,
            "type_provenance_kind": "policy_seed",
            "type_provenance_section": 0,
            "type_provenance_offset": 0,
        }
    ]
    assert any("player_score(a0)" in row["text"] for row in combined["listing"]["rows"])
    assert any(
        access["field_name"] == "player_score"
        for row in combined["listing"]["rows"]
        for access in row.get("typed_accesses", [])
    )


def test_real_dll_custom_struct_seed_shadows_platform_struct_name(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "custom_input_event.bin"
    binary_path.write_bytes(bytes.fromhex("202800084e75"))
    metadata_path = tmp_path / "target_metadata.json"
    metadata = {
        "target_type": "raw_binary",
        "entry_register_seeds": [
            {
                "entry_offset": None,
                "hunk": 0,
                "register": "A0",
                "kind": "struct_ptr",
                "note": "target-local InputEvent",
                "struct_name": "InputEvent",
                "context_name": None,
            }
        ],
        "custom_structs": [
            {
                "name": "InputEvent",
                "size": 16,
                "fields": [
                    {
                        "name": "game_event_score",
                        "type": "long",
                        "offset": 8,
                        "size": 4,
                        "struct": None,
                        "pointer_struct": None,
                        "named_base": None,
                    }
                ],
            }
        ],
    }
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    combined = analyze_source_with_c_artifact(
        RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=binary_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(binary_path),
            analysis_cache_path=tmp_path / "custom_input_event.analysis",
        ),
        metadata_text=str(metadata_path),
        project_root=PROJECT_ROOT,
    )

    typed_accesses = combined["analysis"]["sections"][0]["recovered_platform_typed_accesses"]
    assert typed_accesses[0]["root_struct_name"] == "InputEvent"
    assert typed_accesses[0]["owner_struct_name"] == "InputEvent"
    assert typed_accesses[0]["field_name"] == "game_event_score"
    assert any("game_event_score(a0)" in row["text"] for row in combined["listing"]["rows"])


def test_real_dll_metadata_named_rsset_layout_preserves_explicit_size(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "stage.bin"
    binary_path.write_bytes(b"\x4e\x75")
    metadata_path = tmp_path / "target_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [
                    {
                        "offset": 2,
                        "size": 2,
                        "layout_name": "work",
                        "base_symbol": "__game_work_base__",
                        "sizeof_symbol": "work_SIZEOF",
                        "symbol": "work_flags",
                        "struct_name": None,
                        "pointer_struct": None,
                        "storage_kind": "scalar",
                        "semantic_type": None,
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    }
                ],
                "execution_views": [],
                "absolute_code_labels": [],
            }
        ),
        encoding="utf-8",
    )

    artifact = c_backend.CListingArtifact.create(
        c_backend._CBackendSourceFile(binary_path, "amiga-raw", 0),
        metadata_text=str(metadata_path),
        include_dir="",
        project_root=PROJECT_ROOT,
    )
    try:
        rendered, _profile = artifact.source_text_with_profile()
    finally:
        artifact.close()

    assert "work_flags RS.W 1\n" in rendered
    assert "work_flags RS.L 1\n" not in rendered
    assert "work_SIZEOF EQU __RS\n" in rendered


def test_real_dll_metadata_named_rsset_layout_renders_byte_array_kind(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "stage.bin"
    binary_path.write_bytes(b"\x4e\x75")
    metadata_path = tmp_path / "target_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [
                    {
                        "offset": 4,
                        "size": 4,
                        "layout_name": "work",
                        "base_symbol": "__game_work_base__",
                        "sizeof_symbol": "work_SIZEOF",
                        "symbol": "work_item_ids",
                        "struct_name": None,
                        "pointer_struct": None,
                        "storage_kind": "byte_array",
                        "semantic_type": "item_ids",
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    }
                ],
                "execution_views": [],
                "absolute_code_labels": [],
            }
        ),
        encoding="utf-8",
    )

    artifact = c_backend.CListingArtifact.create(
        c_backend._CBackendSourceFile(binary_path, "amiga-raw", 0),
        metadata_text=str(metadata_path),
        include_dir="",
        project_root=PROJECT_ROOT,
    )
    try:
        rendered, _profile = artifact.source_text_with_profile()
    finally:
        artifact.close()

    assert "work_item_ids RS.B 4\n" in rendered
    assert "work_item_ids RS.L 1\n" not in rendered
    assert "work_SIZEOF EQU __RS\n" in rendered


def test_real_dll_metadata_named_rsset_layout_symbols_seeded_base_access(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "stage.bin"
    binary_path.write_bytes(bytes.fromhex("354000044e75"))
    metadata_path = tmp_path / "target_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "entry_register_seeds": [
                    {
                        "entry_offset": 0,
                        "hunk": 0,
                        "register": "A2",
                        "kind": "struct_ptr",
                        "note": "__game_work_base__",
                        "library_name": None,
                        "struct_name": "",
                        "context_name": None,
                    }
                ],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [
                    {
                        "offset": 4,
                        "size": 2,
                        "layout_name": "work",
                        "base_symbol": "__game_work_base__",
                        "sizeof_symbol": "work_SIZEOF",
                        "symbol": "work_flags",
                        "struct_name": None,
                        "pointer_struct": None,
                        "storage_kind": "scalar",
                        "semantic_type": None,
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "test",
                    }
                ],
                "execution_views": [],
                "absolute_code_labels": [],
            }
        ),
        encoding="utf-8",
    )

    artifact = c_backend.CListingArtifact.create(
        c_backend._CBackendSourceFile(binary_path, "amiga-raw", 0),
        metadata_text=str(metadata_path),
        include_dir="",
        project_root=PROJECT_ROOT,
    )
    try:
        rendered, _profile = artifact.source_text_with_profile()
    finally:
        artifact.close()

    assert "work_flags RS.W 1\n" in rendered
    assert "\tmove.w d0,work_flags(a2)\n" in rendered
    assert "\tmove.w d0,$0004(a2)\n" not in rendered


def test_real_dll_manual_rsset_layout_region_renders_source_and_rebuilds(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-rsset.hunk"
    source_text = "    SECTION section_0,code\nstart:\n    move.w d0,$0004(a2)\n    rts\n    dc.w $0000\n"
    binary_path.write_bytes(
        assemble_platform_source_text_with_c_backend(
            "amiga-hunk",
            source_text,
            include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
            target_cpu="any",
            project_root=PROJECT_ROOT,
        )[0]
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {"record": "manual_action_log_header", "version": 1, "target_identity": build_target_identity(source)},
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_register_seed",
                "register_seed": {
                    "register_seed_id": "a2-work-base",
                    "entry_offset": 0,
                    "register": "A2",
                    "kind": "struct_ptr",
                    "note": "__game_work_base__",
                },
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a2",
                "sequence": 2,
                "created_at": "2026-05-13T00:00:02+00:00",
                "kind": "create_manual_rsset_layout_region",
                "rsset_layout_region": {
                    "rsset_layout_region_id": "work-flags",
                    "offset": 4,
                    "size": 2,
                    "layout_name": "work",
                    "base_symbol": "__game_work_base__",
                    "sizeof_symbol": "work_SIZEOF",
                    "symbol": "work_flags",
                    "storage_kind": "scalar",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "work_flags RS.W 1\n" in rendered
    assert "\tmove.w d0,work_flags(a2)\n" in rendered
    assert rebuilt == binary_path.read_bytes()
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_manual_rsset_layout_region_remove_restores_raw_reference(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-rsset-remove.hunk"
    source_text = "    SECTION section_0,code\nstart:\n    move.w d0,$0004(a2)\n    rts\n    dc.w $0000\n"
    binary_path.write_bytes(
        assemble_platform_source_text_with_c_backend(
            "amiga-hunk",
            source_text,
            include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
            target_cpu="any",
            project_root=PROJECT_ROOT,
        )[0]
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(
            {
                "target_type": "program",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [
                    {
                        "offset": 4,
                        "size": 2,
                        "layout_name": "work",
                        "base_symbol": "__game_work_base__",
                        "sizeof_symbol": "work_SIZEOF",
                        "symbol": "work_flags",
                        "struct_name": None,
                        "pointer_struct": None,
                        "storage_kind": "scalar",
                        "semantic_type": None,
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "target_metadata:test",
                    }
                ],
                "execution_views": [],
                "absolute_code_labels": [],
            }
        ),
        encoding="utf-8",
    )
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {"record": "manual_action_log_header", "version": 1, "target_identity": build_target_identity(source)},
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_register_seed",
                "register_seed": {
                    "register_seed_id": "a2-work-base",
                    "entry_offset": 0,
                    "register": "A2",
                    "kind": "struct_ptr",
                    "note": "__game_work_base__",
                },
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a2",
                "sequence": 2,
                "created_at": "2026-05-13T00:00:02+00:00",
                "kind": "remove_manual_rsset_layout_region",
                "rsset_layout_region": {"offset": 4, "layout_name": "work", "base_symbol": "__game_work_base__"},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "work_flags RS.W 1\n" not in rendered
    assert "\tmove.w d0,$0004(a2)\n" in rendered
    assert rebuilt == binary_path.read_bytes()
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_manual_rsset_use_site_binding_renders_selected_existing_field_only(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-rsset-binding.hunk"
    source_text = (
        "    SECTION section_0,code\n"
        "start:\n"
        "    move.w d0,$0004(a2)\n"
        "    move.w d1,$0004(a2)\n"
        "    rts\n"
        "    dc.w $0000\n"
    )
    binary_path.write_bytes(
        assemble_platform_source_text_with_c_backend(
            "amiga-hunk",
            source_text,
            include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
            target_cpu="any",
            project_root=PROJECT_ROOT,
        )[0]
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {"record": "manual_action_log_header", "version": 1, "target_identity": build_target_identity(source)},
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_rsset_layout_region",
                "rsset_layout_region": {
                    "rsset_layout_region_id": "work-flags",
                    "offset": 4,
                    "size": 2,
                    "layout_name": "work",
                    "base_symbol": "__game_work_base__",
                    "sizeof_symbol": "work_SIZEOF",
                    "symbol": "work_flags",
                    "storage_kind": "scalar",
                },
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a2",
                "sequence": 2,
                "created_at": "2026-05-13T00:00:02+00:00",
                "kind": "create_manual_rsset_use_site_binding",
                "rsset_use_site_binding": {
                    "rsset_use_site_binding_id": "bind-work-flags-first-use",
                    "hunk": 0,
                    "addr": 0,
                    "operand_index": 1,
                    "base_register": "A2",
                    "displacement": 4,
                    "layout_name": "work",
                    "base_symbol": "__game_work_base__",
                    "base_evidence_id": "selected-base:A2:__game_work_base__",
                    "access": "write",
                    "width_bytes": 2,
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "work_flags RS.W 1\n" in rendered
    assert "\tmove.w d0,work_flags(a2)\n" in rendered
    assert "\tmove.w d1,$0004(a2)\n" in rendered
    assert rebuilt == binary_path.read_bytes()
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_manual_rsset_use_site_binding_renders_selected_region_suboffset(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-rsset-binding-suboffset.hunk"
    source_text = (
        "    SECTION section_0,code\n"
        "start:\n"
        "    move.b $0007(a2),d0\n"
        "    move.b $0007(a2),d1\n"
        "    rts\n"
        "    dc.w $0000\n"
    )
    binary_path.write_bytes(
        assemble_platform_source_text_with_c_backend(
            "amiga-hunk",
            source_text,
            include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
            target_cpu="any",
            project_root=PROJECT_ROOT,
        )[0]
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {"record": "manual_action_log_header", "version": 1, "target_identity": build_target_identity(source)},
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_rsset_layout_region",
                "rsset_layout_region": {
                    "rsset_layout_region_id": "work-counter",
                    "offset": 4,
                    "size": 4,
                    "layout_name": "work",
                    "base_symbol": "__game_work_base__",
                    "sizeof_symbol": "work_SIZEOF",
                    "symbol": "work_counter",
                    "storage_kind": "scalar",
                },
            },
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a2",
                "sequence": 2,
                "created_at": "2026-05-13T00:00:02+00:00",
                "kind": "create_manual_rsset_use_site_binding",
                "rsset_use_site_binding": {
                    "rsset_use_site_binding_id": (
                        "rsset-binding-h0-00000000-op0-A2-0007-work-__game_work_base__-"
                        "selected-base_A2___game_work_base__"
                    ),
                    "hunk": 0,
                    "addr": 0,
                    "operand_index": 0,
                    "base_register": "A2",
                    "displacement": 7,
                    "layout_name": "work",
                    "base_symbol": "__game_work_base__",
                    "base_evidence_id": "selected-base:A2:__game_work_base__",
                    "access": "read",
                    "width_bytes": 1,
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )

    assert "work_counter RS.L 1\n" in rendered
    assert "\tmove.b work_counter+3(a2),d0\n" in rendered
    assert "\tmove.b $0007(a2),d1\n" in rendered
    assert "work_0007" not in rendered
    assert rebuilt == binary_path.read_bytes()
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_manual_rsset_use_site_binding_projects_missing_field_as_ref_only(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = tmp_path / "manual-rsset-binding-gap.hunk"
    source_text = (
        "    SECTION section_0,code\n"
        "start:\n"
        "    move.w d0,$0004(a2)\n"
        "    move.w d1,$0004(a2)\n"
        "    rts\n"
        "    dc.w $0000\n"
    )
    binary_path.write_bytes(
        assemble_platform_source_text_with_c_backend(
            "amiga-hunk",
            source_text,
            include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
            target_cpu="any",
            project_root=PROJECT_ROOT,
        )[0]
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
        encoding="utf-8",
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        json.dumps(
            {"record": "manual_action_log_header", "version": 1, "target_identity": build_target_identity(source)},
            sort_keys=True,
        )
        + "\n"
        + json.dumps(
            {
                "record": "manual_action",
                "action_id": "a1",
                "sequence": 1,
                "created_at": "2026-05-13T00:00:01+00:00",
                "kind": "create_manual_rsset_use_site_binding",
                "rsset_use_site_binding": {
                    "rsset_use_site_binding_id": "bind-work-gap-first-use",
                    "hunk": 0,
                    "addr": 0,
                    "operand_index": 1,
                    "base_register": "A2",
                    "displacement": 4,
                    "layout_name": "work",
                    "base_symbol": "__game_work_base__",
                    "base_evidence_id": "selected-base:A2:__game_work_base__",
                    "access": "write",
                    "width_bytes": 2,
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with effective_metadata_file(target_dir) as metadata_path:
        assert metadata_path is not None
        metadata_text = c_backend._metadata_path_text(metadata_path)
        rendered = render_project_source_with_c_backend(
            source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source,
            metadata_path=metadata_path,
            compare_original=True,
            project_root=PROJECT_ROOT,
        )
        rows, _api_calls, profile = build_project_listing_rows_from_source_with_c_artifact(
            source,
            metadata_text=metadata_text,
            project_root=PROJECT_ROOT,
        )

    assert "\tmove.w d0,$0004(a2)\n" in rendered
    assert "\tmove.w d1,$0004(a2)\n" in rendered
    assert "app_0004 RS" not in rendered
    assert rebuilt == binary_path.read_bytes()
    assert direct_profile["direct_rebuild_exact"] is True

    refs_by_text = {str(row["text"]).strip(): row["app_slot_refs"] for row in rows if row.get("app_slot_refs")}
    assert refs_by_text == {
        "move.w d0,$0004(a2)": [
            {"symbol": "app_0004", "displacement": 4, "base_register": "A2", "operand_index": 1, "access": "write"}
        ]
    }
    app_slot_analysis = profile["app_slot_analysis"]
    assert isinstance(app_slot_analysis, dict)
    assert [
        (slot["symbol"], slot["displacement"], slot["base_registers"], slot["ref_count"])
        for slot in app_slot_analysis["slots"]
    ] == [("app_0004", 4, ["A2"], 1)]


def test_real_dll_assembles_source_path_with_profile(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    source_path = tmp_path / "minimal.s"
    output_path = tmp_path / "minimal.hunk"
    source_path.write_text("    SECTION section_0,code\n    rts\n    dc.w $0000\n", encoding="ascii")

    rebuilt, profile = assemble_platform_source_path_with_c_backend(
        "amiga-hunk",
        source_path,
        include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
        output_path=output_path,
        target_cpu="any",
        project_root=PROJECT_ROOT,
    )

    assert output_path.read_bytes() == rebuilt
    assert rebuilt.startswith(b"\x00\x00\x03\xf3")
    assert profile["assemble_c_api"] is True
    assert profile["source_bytes"] == source_path.stat().st_size
    assert profile["rebuilt_bytes"] == len(rebuilt)
    assert profile["total_seconds"] >= 0


def test_real_dll_assembles_source_text_with_profile(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    source_text = "    SECTION section_0,code\n    rts\n    dc.w $0000\n"
    output_path = tmp_path / "minimal_text.hunk"

    rebuilt, profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
        output_path=output_path,
        target_cpu="any",
        project_root=PROJECT_ROOT,
    )

    assert output_path.read_bytes() == rebuilt
    assert rebuilt.startswith(b"\x00\x00\x03\xf3")
    assert profile["assemble_c_api"] is True
    assert profile["source_bytes"] == len(source_text.encode("utf-8"))
    assert profile["rebuilt_bytes"] == len(rebuilt)
    assert profile["total_seconds"] >= 0


def test_project_source_facts_v2_biased_absolute_long_dispatch_table_roundtrips(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "biased_dispatch.hunk"
    code = bytearray()
    code += bytes.fromhex("302d000c")
    code += bytes.fromhex("672a")
    code += bytes.fromhex("e540")
    code += bytes.fromhex("41f900000010")
    code += bytes.fromhex("20700000")
    code += bytes.fromhex("4ed0")
    assert len(code) == 0x14
    code += u32(0x30)
    code += u32(0x36)
    code += b"\x00" * (0x30 - len(code))
    code += bytes.fromhex("4e75")
    code += b"\x00" * (0x36 - len(code))
    code += bytes.fromhex("4e75")
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=bytes(code)))
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "biased_dispatch.analysis",
    )

    rendered, profile = listing_artifact_source_text_with_c_backend_profile(source, project_root=PROJECT_ROOT)
    rebuilt, source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        source,
        project_root=PROJECT_ROOT,
    )

    assert "\tlea.l $00000010.l,a0\n\tmovea.l $0(a0,d0.w),a0\n\tjmp (a0)\n" in rendered
    assert "\tdc.l loc_0_00000030\t; pointer_table\n\tdc.l loc_0_00000036\n" in rendered
    assert "loc_0_00000010:\n" not in rendered
    assert "dc.b $00,$00,$00,$30,$00,$00,$00,$36" not in rendered
    assert profile["facts_v2"]["asm_source_refused"] is False
    assert profile["facts_v2"]["code_start_control_targets"] >= 2
    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert direct_profile["direct_rebuild_refused"] is False
    assert rebuilt == binary_path.read_bytes()


def test_project_source_facts_v2_pc_indexed_absolute_long_dispatch_table_roundtrips(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "pc_indexed_long_dispatch.hunk"
    code = bytes.fromhex("7800227B40044ED100000010000000124E754E75")
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=code))
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "pc_indexed_long_dispatch.analysis",
    )

    rendered, profile = listing_artifact_source_text_with_c_backend_profile(source, project_root=PROJECT_ROOT)
    rebuilt, source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        source,
        project_root=PROJECT_ROOT,
    )

    assert "\tmovea.l loc_0_00000008(pc,d4.w),a1\n\tjmp (a1)\n" in rendered
    assert "\tdc.l loc_0_00000010,loc_0_00000012\t; lookup_table\n" in rendered
    assert "loc_0_00000010:\n\trts\nloc_0_00000012:\n\trts\n" in rendered
    assert "dc.b $00,$00,$00,$10,$00,$00,$00,$12" not in rendered
    assert profile["facts_v2"]["asm_source_refused"] is False
    assert profile["facts_v2"]["code_start_control_targets"] >= 2
    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert direct_profile["direct_rebuild_refused"] is False
    assert rebuilt == binary_path.read_bytes()


@pytest.mark.parametrize("target_name", ["amiga_hunk_genam", "amiga_hunk_monam302"])
def test_project_source_facts_v2_indexed_pointer_table_comparators_stay_clean(target_name: str) -> None:
    _requires_c_backend_dlls()
    _rows, _api_calls, profile = build_project_listing_rows_profile_with_c_artifact(
        target_name,
        project_root=PROJECT_ROOT,
    )
    paths = resolve_project_paths(target_name, project_root=PROJECT_ROOT)
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    facts_v2 = profile["facts_v2"]
    assert facts_v2["asm_source_refused"] is False
    assert facts_v2["required_instruction_failures"] == 0
    assert facts_v2["unsupported_instruction_demotes"] == 0
    assert facts_v2["interior_conflicts_unresolved"] == 0
    assert facts_v2["unresolved_labels"] == 0
    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert "    ORG $4\n" not in source_text
    if target_name == "amiga_hunk_monam302":
        assert "\tdc.l loc_0_0000850A\t; pointer_table\n" in source_text
    else:
        assert "pointer_table" not in source_text


@pytest.mark.parametrize("target_name", ["amiga_hunk_genam", "amiga_hunk_monam302"])
def test_project_source_facts_v2_wide_word_dispatch_comparators_stay_clean(target_name: str) -> None:
    _requires_c_backend_dlls()
    paths = resolve_project_paths(target_name, project_root=PROJECT_ROOT)
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    facts_v2 = source_profile["facts_v2"]
    assert facts_v2["asm_source_refused"] is False
    assert facts_v2["required_instruction_failures"] == 0
    assert facts_v2["unsupported_instruction_demotes"] == 0
    assert facts_v2["interior_conflicts_unresolved"] == 0
    assert facts_v2["unresolved_labels"] == 0
    assert "    ORG $4\n" not in source_text


def test_project_source_facts_v2_inline_tail_dispatch_voodoo_and_comparators_stay_clean() -> None:
    _requires_c_backend_dlls()
    paths = resolve_project_paths(
        "amiga_disk_voodoo-nightmare-1990-palace-cr-angels-defjam-genesis__amiga_hunk_run_df6ad190",
        project_root=PROJECT_ROOT,
    )
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )
    facts_v2 = source_profile["facts_v2"]
    assert facts_v2["asm_source_refused"] is False
    assert facts_v2["required_instruction_failures"] == 0
    assert facts_v2["unsupported_instruction_demotes"] == 0
    assert facts_v2["interior_conflicts_unresolved"] == 0
    assert facts_v2["unresolved_labels"] == 0
    assert "\tjmp abs_6_00078DD0(pc,d1.w)\n" in source_text
    assert "abs_6_00078DC0:\n\tmove.b (a1)+,(a0)+\n" in source_text
    assert "abs_6_00078DD0:\n\tdbf.w d0,abs_6_00078DC0\n" in source_text
    assert "\tjmp abs_6_000791A4(pc,d1.w)\n" in source_text
    assert "abs_6_00079194:\n\tmove.b (a1)+,(a0)+\n" in source_text
    assert "abs_6_000791A4:\n\tdbf.w d0,abs_6_00079194\n" in source_text

    for target_name in ["amiga_hunk_genam", "amiga_hunk_monam302"]:
        paths = resolve_project_paths(target_name, project_root=PROJECT_ROOT)
        rebuilt, direct_source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            paths.binary_source,
            metadata_path=paths.target_dir / "target_metadata.json",
            project_root=PROJECT_ROOT,
        )
        assert direct_source_profile["facts_v2"]["asm_source_refused"] is False
        assert direct_profile["direct_rebuild_refused"] is False
        assert rebuilt == paths.binary_source.path.read_bytes()


def test_real_dll_renders_genam() -> None:
    _requires_c_backend_dlls()
    rendered = render_binary_source_with_c_backend(PROJECT_ROOT / "bin" / "GenAm")

    assert "SECTION" in rendered
    assert "move" in rendered.lower() or "jsr" in rendered.lower()
    assert "app_0234 RS." in rendered
    assert "app_0234(a6)" in rendered
    assert "$0098(a1)" in rendered
    assert "m68k_vector_trap_6_instruction_vector(a1)" not in rendered

    rows, _api_calls, _profile = build_project_listing_rows_with_c_artifact(
        "amiga_hunk_genam",
        project_root=PROJECT_ROOT,
    )
    refs = [ref for row in rows for ref in row.get("app_slot_refs", [])]
    symbols = {ref["symbol"] for ref in refs}
    fallback_symbols = [
        symbol
        for symbol in symbols
        if symbol.startswith("app_")
        and len(symbol) == 8
        and all(ch in "0123456789ABCDEF" for ch in symbol[4:])
    ]
    refs_by_text = {str(row["text"]).strip(): row["app_slot_refs"] for row in rows if row.get("app_slot_refs")}

    assert len(refs) > 500
    assert len(fallback_symbols) > 100
    assert refs_by_text["move.l a7,app_0234(a6)"] == [
        {"symbol": "app_0234", "displacement": 0x0234, "base_register": "A6", "operand_index": 1, "access": "write"}
    ]
    assert refs_by_text["subq.l #4,app_0234(a6)"] == [
        {
            "symbol": "app_0234",
            "displacement": 0x0234,
            "base_register": "A6",
            "operand_index": 1,
            "access": "read-write",
        }
    ]


def test_real_dll_genam_raw_0102_a6_exposes_rsset_binding_report() -> None:
    _requires_c_backend_dlls()
    rows, _api_calls, profile = build_project_listing_rows_with_c_artifact(
        "amiga_hunk_genam",
        project_root=PROJECT_ROOT,
    )
    row = next(row for row in rows if str(row.get("text", "")).strip() == "sf.b $0102(a6)")
    assert row.get("app_slot_refs", []) == []
    assert row["operand_parts"] == [
        {
            "kind": "displacement",
            "operand_index": 0,
            "text": None,
            "value": None,
            "register": None,
            "base_register": "A6",
            "displacement": 0x0102,
            "segment_addr": None,
            "metadata": {},
        }
    ]

    contexts = listing_element_contexts(row)
    matching_contexts = [
        context
        for context in contexts
        if context.get("base_register") == "A6" and context.get("displacement") == 0x0102
    ]
    assert matching_contexts, f"operand_parts={row.get('operand_parts')!r}; contexts={contexts!r}"
    context = matching_contexts[0]
    assert context["operand_index"] == 0

    row_with_analysis = dict(row)
    row_with_analysis["app_slot_analysis"] = profile["app_slot_analysis"]
    actions = listing_element_action_catalog(row_with_analysis, {"element_id": context["element_id"]})
    report_action = next(action for action in actions if action["action_id"] == "rsset.binding.report")
    assert not any(action["action_id"] == "rsset.binding.bind" for action in actions)

    assert report_action["report"]["candidate"] == {
        "layout_name": "app",
        "base_symbol": "__amiga_app_base__",
        "base_register": "A6",
        "base_evidence_id": None,
        "displacement": 0x0102,
    }
    assert report_action["report"]["operand_facts"]["width_bytes"] == 1
    assert report_action["report"]["base_evidence"]["blockers"] == ["missing_base_evidence"]
    assert report_action["report"]["candidate_layouts"][0]["gap_covering_displacement"]["start"] <= 0x0102
    assert report_action["report"]["candidate_layouts"][0]["gap_covering_displacement"]["end"] > 0x0102
    assert report_action["report"]["type_compatibility"]["width_fits_gap"] is True
    assert report_action["report"]["render"]["state"] == "linked_gap_or_raw"


@pytest.mark.parametrize("binary_name", ["GenAm", "MonAm302"])
def test_real_dll_runtime_memory_immediates_need_proven_external_role(binary_name: str) -> None:
    _requires_c_backend_dlls()
    rendered = render_binary_source_with_c_backend(PROJECT_ROOT / "bin" / binary_name)

    assert "#bitmap_" not in rendered
    assert "#disk_buffer_" not in rendered


def test_real_dll_genam_profile_exposes_c_app_slot_analysis() -> None:
    _requires_c_backend_dlls()
    _rows, _api_calls, profile = build_project_listing_rows_profile_with_c_artifact(
        "amiga_hunk_genam",
        project_root=PROJECT_ROOT,
    )

    analysis = profile["app_slot_analysis"]
    assert isinstance(analysis, dict)
    regions = [
        region
        for region in analysis["regions"]
        if isinstance(region, dict) and region.get("source") == "platform_api_arg"
    ]
    struct_names = {region.get("struct_name") for region in regions}
    field_names = {
        field_ref.get("field_name")
        for region in regions
        for field_ref in region.get("field_refs", [])
        if isinstance(field_ref, dict)
    }
    field_gap_coverages = {
        gap.get("coverage")
        for gap in analysis["field_gaps"]
        if isinstance(gap, dict)
    }

    assert analysis["typed_region_count"] >= 3
    assert analysis["gap_count"] >= 1
    assert analysis["field_gap_count"] >= 1
    assert {"TIMEVAL", "IO"} <= struct_names
    assert {"TV_SECS", "TV_MICRO", "IO_DEVICE", "IO_ERROR", "IO_DATA"} <= field_names
    assert field_gap_coverages == {"known_struct_field"}
    assert profile["timing"]["total_seconds"] < 30.0
    assert profile["facts_v2"]["queue_iterations"] < 10000


def test_real_dll_bloodwych_detects_runtime_copy_loader() -> None:
    _requires_c_backend_dlls()
    rows, _, profile = build_project_listing_rows_profile_with_c_artifact(
        "amiga_hunk_bloodwych",
        project_root=PROJECT_ROOT,
    )

    facts_v2 = profile["facts_v2"]
    assert facts_v2["asm_source_refused"] is False
    assert facts_v2["required_instruction_failures"] == 0
    assert facts_v2["unsupported_instruction_demotes"] == 0
    assert facts_v2["interior_conflicts_unresolved"] == 0
    copied_stage_rows = [
        row for row in rows if row["section_index"] == 0 and row["start_offset"] == 0x5C
    ]
    assert any(row["kind"] == "label" and "abs_0_00000400:" in str(row["text"]) for row in copied_stage_rows)
    assert any(row["kind"] == "instruction" for row in copied_stage_rows)
    assert not any(row["kind"] == "data" for row in copied_stage_rows)
    assert any(
        row["section_index"] == 0
        and row["start_offset"] == 0x4B2A
        and row["kind"] == "instruction"
        and "\tclr.b $0011(a4)" in str(row["text"])
        for row in rows
    )
    bitmap_refs = [
        ref
        for row in rows
        if row["kind"] == "data" and str(row["text"]).startswith("\tdc.w bplpt") and row.get("runtime_address_refs")
        for ref in row["runtime_address_refs"]
    ]
    assert [(ref["runtime_address"], ref["size"], ref["data_class"]) for ref in bitmap_refs] == [
        (0x70000, 0x2000, "bitmap"),
        (0x72000, 0x2000, "bitmap"),
        (0x74000, 0x2000, "bitmap"),
        (0x76000, 0x2000, "bitmap"),
    ]
    combined = _facts_v2_listing_analysis_for_project("amiga_hunk_bloodwych")
    section = combined["analysis"]["sections"][0]
    sites_by_offset = {site["offset"]: site for site in section["recovered_indirect_sites"]}
    assert sites_by_offset[0x79D8]["status"] == "jump_table"
    assert sites_by_offset[0x79D8]["target_count"] == 9
    assert sites_by_offset[0xA394]["status"] == "jump_table"
    assert sites_by_offset[0xA394]["target_count"] == 5
    refs_by_source = [
        ref
        for ref in section["code_start_refs"]
        if ref["source_offset"] in {0x79D8, 0xA394}
    ]
    assert len(refs_by_source) == 14


def test_real_dll_bloodwych_listing_rows_use_per_entry_table_ranges() -> None:
    _requires_c_backend_dlls()
    rows, _, _ = build_project_listing_rows_profile_with_c_artifact(
        "amiga_hunk_bloodwych",
        project_root=PROJECT_ROOT,
    )
    data_rows = {str(row["text"]).strip(): row for row in rows if row["kind"] == "data"}

    first_pointer = data_rows["dc.l abs_0_00008E84\t; pointer_table"]
    second_pointer = data_rows["dc.l abs_0_00008F14"]
    first_word = data_rows["dc.w abs_0_000058F4-abs_0_000058F4\t; lookup_table"]
    second_word = data_rows["dc.w abs_0_0000590C-abs_0_000058F4"]

    assert (first_pointer["start_offset"], first_pointer["end_offset"], first_pointer["bytes"]) == (
        0x20E,
        0x212,
        "00008e84",
    )
    assert (second_pointer["start_offset"], second_pointer["end_offset"], second_pointer["bytes"]) == (
        0x212,
        0x216,
        "00008f14",
    )
    assert (first_word["start_offset"], first_word["end_offset"], first_word["bytes"]) == (
        0x5548,
        0x554A,
        "0000",
    )
    assert (second_word["start_offset"], second_word["end_offset"], second_word["bytes"]) == (
        0x554A,
        0x554C,
        "0018",
    )


def test_real_dll_render_plan_data_classes_reach_listing_rows() -> None:
    _requires_c_backend_dlls()

    expectations = {
        "amiga_hunk_bloodwych": {
            "lookup_table": 230,
            "pointer_table": 4,
            "string": 72,
        },
        "amiga_hunk_genam": {
            "lookup_table": 6,
            "string": 145,
        },
        "amiga_hunk_monam302": {
            "lookup_table": 18,
            "pointer_table": 1,
            "string": 128,
        },
    }
    for target_name, expected_counts in expectations.items():
        rows, _, profile = build_project_listing_rows_profile_with_c_artifact(
            target_name,
            project_root=PROJECT_ROOT,
        )
        assert profile["facts_v2"]["asm_source_refused"] is False
        assert not [
            row
            for row in rows
            if str(row.get("text", "")).strip().endswith(":") and row.get("kind") not in {"label", "directive", "comment"}
        ]
        assert not [row for row in rows if row.get("data_class") and row.get("kind") != "data"]
        assert not [
            row
            for row in rows
            if row.get("data_class") and str(row.get("text", "")).strip().endswith(":")
        ]
        for data_class, expected_count in expected_counts.items():
            assert sum(1 for row in rows if row.get("data_class") == data_class) >= expected_count


def test_real_dll_genam_data_class_rows_feed_data_symbol_candidates() -> None:
    _requires_c_backend_dlls()

    rows, _, profile = build_project_listing_rows_profile_with_c_artifact(
        "amiga_hunk_genam",
        project_root=PROJECT_ROOT,
    )
    assert profile["facts_v2"]["asm_source_refused"] is False
    candidate_rows = []
    for row in rows:
        if row.get("kind") != "data" or not row.get("data_class"):
            continue
        row_with_locator = dict(row)
        row_with_locator["locator"] = {
            "target_id": "amiga_hunk_genam",
            "projection_hash": "genam-data-symbol-smoke",
            "kind": "row",
            "row_key": row["row_key"],
            "section_index": row["section_index"],
            "start_offset": row["start_offset"],
            "end_offset": row.get("end_offset"),
        }
        candidate_rows.append(row_with_locator)

    candidates = reversing_loop._listing_data_symbol_candidates(candidate_rows)
    data_class_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("evidence", {}).get("evidence_kind") == "data_class_row"
    ]

    assert data_class_candidates
    assert any(candidate["new_name"].startswith("string_h0_") for candidate in data_class_candidates)
    assert all(candidate["kind"] == "data_symbol_name" for candidate in data_class_candidates)
    assert all(candidate["suggested_action_kinds"] == ["data_symbol.rename"] for candidate in data_class_candidates)
    assert all(candidate["verifier"]["kind"] == "projected_data_symbol_name" for candidate in data_class_candidates)


def test_real_dll_render_plan_data_classes_reach_navigation() -> None:
    _requires_c_backend_dlls()

    for target_name in ("amiga_hunk_bloodwych", "amiga_hunk_genam"):
        rows, _, profile = build_project_listing_rows_profile_with_c_artifact(
            target_name,
            project_root=PROJECT_ROOT,
        )
        assert profile["facts_v2"]["asm_source_refused"] is False
        expected = []
        seen = set()
        for row in rows:
            key = (row.get("section_index"), row.get("addr"), row.get("data_class"))
            if row.get("data_class") and row.get("kind") not in {"instruction", "label"} and key not in seen:
                seen.add(key)
                expected.append(
                    (
                        row.get("section_index"),
                        row.get("addr"),
                        row.get("comment_text") or row["data_class"],
                    )
                )
        duplicate_keys = [
            key
            for key, count in Counter(
                (row.get("section_index"), row.get("addr"), row.get("data_class"))
                for row in rows
                if row.get("data_class")
            ).items()
            if count > 1
        ]
        assert duplicate_keys
        assert expected

        navigation = profile["navigation"]
        assert isinstance(navigation, dict)
        groups = navigation["groups"]
        assert isinstance(groups, dict)
        typed_data = groups["typed-data"]
        assert isinstance(typed_data, list)

        keys = [
            (entry.get("hunk_index"), entry.get("addr"), entry.get("summary"))
            for entry in typed_data
            if isinstance(entry, dict)
        ]
        assert len(keys) == len(set(keys))
        entries = set(keys)
        for key in expected:
            assert key in entries


def test_real_dll_platform_calls_are_not_unresolved_indirect_sites() -> None:
    _requires_c_backend_dlls()

    for target_name in ["amiga_hunk_genam", "amiga_hunk_monam302"]:
        combined = _facts_v2_listing_analysis_for_project(target_name)
        for section in combined["analysis"]["sections"]:
            platform_call_offsets = {
                call["offset"] for call in section["recovered_platform_calls"]
            }
            unresolved_indirect_offsets = {
                site["offset"]
                for site in section["recovered_indirect_sites"]
                if site["status"] == "unresolved"
            }
            assert unresolved_indirect_offsets.isdisjoint(platform_call_offsets)


def test_real_dll_genam_register_copied_code_target_promotes_code() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths(
        "amiga_hunk_genam",
        project_root=PROJECT_ROOT,
    )
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "loc_0_00009DA2:\n\taddq.l #1,d0\n\trts\n" in source_text
    assert "loc_0_00009DA2:\n\tdc.b $52,$80,$4E,$75" not in source_text


def test_real_dll_damocles_register_copied_target_promotes_decompressor_code(tmp_path: Path) -> None:
    _requires_c_backend_dlls()

    paths = _requires_project_paths(
        "amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_damocles_53b24620",
    )
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "stack_top_00000800\tEQU\t$800\n" in source_text
    assert "\tlea.l stack_top_00000800.l,a7\n" in source_text
    assert "\tmovea.l loc_1_000000D0+2(pc),a4\n" in source_text
    assert "\tadda.l loc_1_00000012+2(pc),a0\n" in source_text
    assert "\tmovea.l $C4(pc),a4\n" not in source_text
    assert "\tadda.l -$C(pc),a0\n" not in source_text
    assert "runtime_address_0004F92B\tEQU\t$4F92B\n" in source_text
    assert "\tlea.l runtime_address_0004F92B.l,a1\n" in source_text
    assert "\tlea.l $0004F92B.l,a1\n" not in source_text
    assert "runtime_address_00040000\tEQU\t$40000\n" in source_text
    assert "runtime_address_00050000\tEQU\t$50000\n" in source_text
    assert "\tlea.l runtime_address_00040000.l,a0\n" in source_text
    assert "\tlea.l runtime_address_00050000.l,a2\n" in source_text
    assert "\tlea.l $00040000.l,a0\n" not in source_text
    assert "\tlea.l $00050000.l,a2\n" not in source_text
    assert "\tlea.l abs_2_00000100.l,a1\n" in source_text
    assert (
        "loc_2_0000006A:\n"
        "    ORG $100\n"
        "abs_2_00000100:\n"
        "\tmoveq.l #-83,d7\n"
        "\tlea.l $00001000.l,a0\n"
        "\tlea.l runtime_address_0007FFFF.l,a2\n"
    ) in source_text
    assert "loc_2_0000006A:\n\tdc.b $7E,$AD,$41,$F9" not in source_text
    assert (
        "abs_2_00000140:\n"
        "\tadda.l #$47368,a0\n"
        "\tlea.l runtime_address_000130B6.l,a1\n"
    ) in source_text
    assert "\tlea.l loc_2_0000014C-(*+2)(pc),a0\n" in source_text
    assert "\tlea.l loc_2_0000014C(pc),a0\n" not in source_text
    assert "\tdc.b $3D,$7C,$7F,$FF,$00,$9A,$4E,$73,$D1,$FC,$00,$04,$73,$68,$43,$F9\n" not in source_text

    vasm = PROJECT_ROOT / "tools" / "vasmm68k_mot.exe"
    if not vasm.exists():
        pytest.skip("vasm is missing")
    source_path = tmp_path / "damocles.s"
    output_path = tmp_path / "damocles.hunk"
    source_path.write_text(source_text, encoding="utf-8", newline="\n")
    result = subprocess.run(
        [
            str(vasm),
            "-Fhunkexe",
            "-m68000",
            "-no-opt",
            "-quiet",
            "-nosym",
            "-kick1hunks",
            "-I" + str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            "-o",
            str(output_path),
            str(source_path),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert output_path.read_bytes() == paths.binary_source.read_bytes()


def test_listing_analysis_reports_extracted_damocles_style_self_decruncher(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "damocles_style_self_decrunch_hunk.bin"
    source = """    SECTION section,code
    moveq.l #17,d7
    lea.l payload(pc),a1
    lea.l $40000.l,a0
    lea.l $50000.l,a2
loop:
    move.b (a1)+,d0
    cmp.b d7,d0
    bne.b literal
    moveq.l #0,d1
    move.b (a1)+,d1
    beq.b literal
    move.b (a1)+,d0
    addq.w #1,d1
repeat:
    move.b d0,(a0)+
    dbf.w d1,repeat
literal:
    move.w d0,($DFF180).l
    move.b d0,(a0)+
    cmpa.l a2,a1
    blt.b loop
    jmp $40000.l
payload:
    dc.b $12,$E7,$FF,$7F,$C4,$9C,$AD,$19,$7D,$FF,$7F,$92,$D8,$60,$38,$88
    dc.w 0
"""
    assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source,
        output_path=binary,
        project_root=PROJECT_ROOT,
    )

    combined = analyze_source_with_c_artifact(
        HunkFileBinarySource(
            kind=BinarySourceKind.HUNK_FILE,
            path=binary,
            display_path=str(binary),
            analysis_cache_path=tmp_path / "binary.analysis",
        ),
        metadata_text="",
        project_root=PROJECT_ROOT,
    )
    events = [
        event
        for event in combined["analysis"]["decompression_events"]
        if event.get("source_kind") == "self_decruncher"
    ]

    assert len(events) == 1
    event = events[0]
    assert event["status"] == "needs_simulated_decrunch"
    assert event["reason"].startswith("simulated_")
    assert event["provider_id"] == "m68k-sim-decrunch"
    assert event["codec_support"] == "simulator_required"
    assert event["decompressor_code_section"] == 0
    assert event["decompressor_entry_offset"] == 0
    assert event["simulated_start_pc"] == 0
    assert event["simulated_stop_pc"] >= event["simulated_start_pc"]
    assert event["simulated_step_count"] > 0
    assert isinstance(event["simulated_stop_reason_name"], str)
    assert event["load_address"] == 0x40000
    assert event["entrypoint"] == 0x40000
    assert event["observed_write_start"] <= 0x40000
    assert event["observed_write_end"] > 0x40000


def test_real_dll_carrier_predecrement_copied_entry_promotes_loader_code() -> None:
    _requires_c_backend_dlls()

    combined = _facts_v2_listing_analysis_for_project(
        "amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_carrier_91b0ba24"
    )
    section = combined["analysis"]["sections"][0]
    sites_by_offset = {site["offset"]: site for site in section["recovered_indirect_sites"]}
    rows = combined["listing"]["rows"]

    assert sites_by_offset[0x360]["status"] == "backward_slice"
    assert sites_by_offset[0x360]["target"] == 0x362
    assert any(
        row.get("kind") == "instruction"
        and row.get("start_offset") == 0x362
        and row.get("text") == "\tlea.l runtime_code_00077400.l,a1\n"
        for row in rows
    )
    assert not any(
        row.get("kind") == "data" and row.get("start_offset") == 0x362
        for row in rows
    )


def test_real_dll_carrier_decompression_suggestions_require_runtime_metadata() -> None:
    _requires_c_backend_dlls()

    target_name = "amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_carrier_91b0ba24"
    combined = _facts_v2_listing_analysis_for_project(target_name)
    paths = _requires_project_paths(target_name)
    payloads = combined["analysis"]["packed_payloads"]
    suggestions = combined["analysis"]["derived_target_suggestions"]
    events = combined["analysis"]["decompression_events"]
    payloads_by_offset = {payload["source_section_offset"]: payload for payload in payloads}
    suggestions_by_offset = {suggestion["source_section_offset"]: suggestion for suggestion in suggestions}
    events_by_offset = {event["source_section_offset"]: event for event in events}

    assert set(payloads_by_offset) == {0x05E4, 0x4C40}
    assert payloads_by_offset[0x05E4]["provider_id"] == "ancient-cli"
    assert payloads_by_offset[0x05E4]["codec_id"] == "rnc1-old"
    assert payloads_by_offset[0x05E4]["source_section"] == 0
    assert payloads_by_offset[0x05E4]["decompressed_size"] == 32032
    assert payloads_by_offset[0x4C40]["provider_id"] == "ancient-cli"
    assert payloads_by_offset[0x4C40]["codec_id"] == "rnc1-old"
    assert payloads_by_offset[0x4C40]["source_section"] == 0
    assert payloads_by_offset[0x4C40]["decompressed_size"] == 359600
    assert set(suggestions_by_offset) == {0x05E4, 0x4C40}
    assert set(events_by_offset) == {0x05E4, 0x4C40}
    assert suggestions_by_offset[0x05E4]["runtime_copy_address"] == 0x77400
    assert suggestions_by_offset[0x05E4]["runtime_copy_size"] == 18012
    assert suggestions_by_offset[0x05E4]["runtime_copy_kind"] == 2
    assert suggestions_by_offset[0x05E4]["runtime_copy_conflicting"] is False
    assert suggestions_by_offset[0x05E4]["reason"] == "missing_decompressed_load_entry"
    assert suggestions_by_offset[0x05E4]["payload_role"] == "unknown_runtime_payload"
    assert suggestions_by_offset[0x05E4]["status"] == "needs_runtime_metadata"
    assert suggestions_by_offset[0x4C40]["runtime_copy_address"] == 0x4000
    assert suggestions_by_offset[0x4C40]["runtime_copy_size"] == 168392
    assert suggestions_by_offset[0x4C40]["runtime_copy_kind"] == 3
    assert suggestions_by_offset[0x4C40]["runtime_copy_conflicting"] is True
    assert suggestions_by_offset[0x4C40]["reason"] == "initial_control_target_validated_runtime_copy"
    assert suggestions_by_offset[0x4C40]["event_kind"] == "decompression"
    assert suggestions_by_offset[0x4C40]["event_id"] == "decompression:section:0:00004C40:rnc1-old"
    assert suggestions_by_offset[0x4C40]["payload_role"] == "primary_program"
    assert suggestions_by_offset[0x4C40]["payload_role_confidence"] == "tool_inferred"
    assert suggestions_by_offset[0x4C40]["parent_remains_active"] == "unknown"
    assert suggestions_by_offset[0x4C40]["status"] == "materializable"
    assert suggestions_by_offset[0x4C40]["load_address"] == 0x4000
    assert suggestions_by_offset[0x4C40]["entrypoint"] == 0x4000
    assert suggestions_by_offset[0x4C40]["initial_control_target"] == 0x9B3A
    assert events_by_offset[0x4C40]["event_kind"] == "decompression"
    assert events_by_offset[0x4C40]["event_id"] == "decompression:section:0:00004C40:rnc1-old"
    assert events_by_offset[0x4C40]["status"] == "materializable"
    assert events_by_offset[0x4C40]["payload_role"] == "primary_program"
    assert events_by_offset[0x4C40]["provider_id"] == "ancient-cli"
    assert events_by_offset[0x4C40]["codec_support"] == "external_provider"
    assert events_by_offset[0x4C40]["load_address"] == 0x4000
    assert events_by_offset[0x05E4]["status"] == "needs_runtime_metadata"
    assert events_by_offset[0x05E4]["reason"] == "missing_decompressed_load_entry"
    assert events_by_offset[0x05E4]["payload_role"] == "unknown_runtime_payload"

    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )
    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "    ORG $5000\n" not in source_text
    assert "    ORG $328\n" not in source_text
    assert "runtime_code_00005000\tEQU\t$5000\n" in source_text
    assert "\tjmp runtime_code_00005000.w\n" in source_text
    assert "loc_0_00000324:\n\tmove #$2700,sr\n\tmove.w #DMAF_CLRALL,_custom+dmacon.l\n" in source_text
    assert "\tjmp $00004000.l\n" in source_text
    assert "loc_0_00004000:" not in source_text
    assert "loc_0_00004004:" not in source_text

    rebuilt, direct_source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        compare_original=True,
        project_root=PROJECT_ROOT,
    )
    assert len(rebuilt) == 188240
    assert direct_source_profile["facts_v2"]["asm_source_refused"] is False
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_pandora_bk_provider_wrapper_promotes_absolute_payload() -> None:
    _requires_c_backend_dlls()

    fixture = PROJECT_ROOT / "tests" / "fixtures" / "hunk" / "pandora_bk_wrapper.bin"
    analysis = analyze_binary_source_with_c_backend(fixture, project_root=PROJECT_ROOT)
    payloads = analysis["packed_payloads"]
    suggestions = analysis["derived_target_suggestions"]
    events = analysis["decompression_events"]

    assert len(payloads) == 1
    assert len(suggestions) == 1
    assert len(events) == 1
    assert payloads[0]["provider_id"] == "ancient-cli"
    assert payloads[0]["codec_id"] == "bk"
    assert payloads[0]["source_section"] == 0
    assert payloads[0]["source_section_offset"] == 0xE8
    assert payloads[0]["packed_size"] == 189000
    assert payloads[0]["decompressed_size"] == 0x5C000
    assert payloads[0]["decompressed_sha256"] == (
        "70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f"
    )
    assert suggestions[0]["status"] == "materializable"
    assert suggestions[0]["reason"] == "initial_control_target_validated_provider_wrapper"
    assert suggestions[0]["payload_role"] == "primary_program"
    assert suggestions[0]["parent_remains_active"] == "false"
    assert suggestions[0]["load_address"] == 0x20000
    assert suggestions[0]["entrypoint"] == 0x20000
    assert suggestions[0]["initial_control_target"] == 0x20000
    assert events[0]["status"] == "materializable"
    assert events[0]["reason"] == "initial_control_target_validated_provider_wrapper"
    assert events[0]["parent_remains_active"] == "false"
    assert events[0]["load_address"] == 0x20000
    assert events[0]["entrypoint"] == 0x20000


def test_real_dll_carrier_decompressed_child_raw_reproduction() -> None:
    _requires_c_backend_dlls()

    paths = _requires_project_paths(
        "amiga_disk_carrier-command-1994-kixx-budget__amiga_raw_carrier_91b0ba24_rnc1_old_00_00004c40",
    )

    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        source_text,
        include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
        project_root=PROJECT_ROOT,
    )

    assert len(rebuilt) == 359600
    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert rebuilt == paths.binary_source.read_bytes()


def test_real_dll_damocles_tetragon_unpacker_candidates() -> None:
    _requires_c_backend_dlls()

    fixture = PROJECT_ROOT / "tests" / "fixtures" / "hunk" / "damocles_tetragon_53b24620.bin"
    analysis = analyze_binary_source_with_c_backend(fixture, project_root=PROJECT_ROOT)
    tetragon_events = [event for event in analysis["decompression_events"] if event.get("codec_id") == "tetragon"]
    self_decrunch_events = [
        event for event in analysis["decompression_events"] if event.get("source_kind") == "self_decruncher"
    ]

    assert len(tetragon_events) == 2
    assert self_decrunch_events == []
    by_section = {event["source_section"]: event for event in tetragon_events}
    assert by_section[1]["source_section_offset"] == 0x100
    assert by_section[1]["compressed_source_section_offset"] == 0x100
    assert by_section[1]["compressed_source_section_end_offset"] == 0x428
    assert by_section[1]["postpass_source_start_address"] == 0x4F92B
    assert by_section[1]["postpass_source_end_address"] == 0x50000
    assert by_section[1]["postpass_escape_byte"] == 0x11
    assert by_section[1]["target_start_address"] == 0x40000
    assert by_section[1]["target_end_address"] == 0x50000
    assert by_section[1]["compressed_source_consumed_section_offset"] == 0x100
    assert by_section[1]["postpass_source_consumed_address"] == 0x50000
    assert by_section[1]["decompressed_size"] == 0x10000
    assert by_section[1]["decompressed_sha256"] == (
        "6fa11625a70f82fc4df5f318ccb149ceeb2687f4af36643c5089090d37a2c0b9"
    )
    assert by_section[1]["entrypoint"] == 0x40000
    assert by_section[1]["status"] == "materializable"
    assert by_section[1]["payload_role"] == "primary_program"
    assert by_section[1]["entry_validation_valid"] is True
    assert by_section[1]["entry_validation_unsupported_instruction_demotes"] == 0
    assert by_section[2]["source_section_offset"] == 0x14C
    assert by_section[2]["compressed_source_section_offset"] == 0x14C
    assert by_section[2]["compressed_source_section_end_offset"] == 0x474B4
    assert by_section[2]["postpass_source_start_address"] == 0x130B6
    assert by_section[2]["postpass_source_end_address"] == 0x7FFFF
    assert by_section[2]["postpass_escape_byte"] == 0xAD
    assert by_section[2]["target_start_address"] == 0x1000
    assert by_section[2]["target_end_address"] == 0x789C9
    assert by_section[2]["compressed_source_consumed_section_offset"] == 0x13D40
    assert by_section[2]["postpass_source_consumed_address"] == 0x7FFFF
    assert by_section[2]["decompressed_size"] == 0x779C9
    assert by_section[2]["decompressed_sha256"] == (
        "3c8656ece7d5b1c8d56cd51a8399cf9b6c22775d1a7c3e67517fae9bb5876b65"
    )
    assert by_section[2]["entrypoint"] == 0x59484
    assert by_section[2]["status"] == "needs_review_blocker"
    assert by_section[2]["reason"] == "invalid_decompressed_entrypoint"
    assert by_section[2]["payload_role"] == "unknown_runtime_payload"
    assert by_section[2]["entry_validation_valid"] is False
    assert by_section[2]["entry_validation_accepted_instructions"] == 7
    assert by_section[2]["entry_validation_unsupported_instruction_demotes"] == 1
    assert by_section[2]["copied_stub_storage_offset"] == 0x6A
    assert by_section[2]["copied_stub_runtime_address"] == 0x100
    assert by_section[2]["copied_stub_transfer_offset"] == 0x40


def test_real_dll_damocles_tetragon_native_materialization(tmp_path: Path) -> None:
    _requires_c_backend_dlls()

    parent_path = PROJECT_ROOT / "tests" / "fixtures" / "hunk" / "damocles_tetragon_53b24620.bin"
    analysis = analyze_binary_source_with_c_backend(parent_path, project_root=PROJECT_ROOT)
    event = next(
        item
        for item in analysis["decompression_events"]
        if item.get("codec_id") == "tetragon" and item.get("source_section") == 1
    )
    output_path = tmp_path / "damocles_hunk1_tetragon.bin"

    result = materialize_recognized_unpacker_event_with_c_backend(
        "amiga-hunk",
        parent_path,
        event["event_id"],
        output_path,
        project_root=PROJECT_ROOT,
    )

    output = output_path.read_bytes()
    assert result["status"] == "ok"
    assert result["provider_id"] == "c-tetragon-native"
    assert len(output) == 0x10000
    assert hashlib.sha256(output).hexdigest() == event["decompressed_sha256"]
    assert result["decompressed"]["load_address"] == 0x40000
    assert result["decompressed"]["entrypoint"] == 0x40000
    binary_source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=output_path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=0x40000,
        entrypoint=0x40000,
        code_start_offset=0,
        display_path=str(output_path),
        analysis_cache_path=output_path.with_suffix(output_path.suffix + ".analysis"),
    )
    source_text, source_profile = listing_artifact_source_text_with_c_backend_profile(
        binary_source,
        project_root=PROJECT_ROOT,
    )
    rebuilt, _assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        source_text,
        include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
        project_root=PROJECT_ROOT,
    )
    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert rebuilt == output


def test_real_dll_damocles_tetragon_rejects_invalid_entry_materialization(tmp_path: Path) -> None:
    _requires_c_backend_dlls()

    parent_path = PROJECT_ROOT / "tests" / "fixtures" / "hunk" / "damocles_tetragon_53b24620.bin"
    analysis = analyze_binary_source_with_c_backend(parent_path, project_root=PROJECT_ROOT)
    event = next(
        item
        for item in analysis["decompression_events"]
        if item.get("codec_id") == "tetragon" and item.get("source_section") == 2
    )
    output_path = tmp_path / "damocles_hunk2_tetragon.bin"

    assert event["status"] == "needs_review_blocker"
    assert event["entry_validation_valid"] is False
    with pytest.raises(RuntimeError, match="recognized unpacker event has no materializable native output"):
        materialize_recognized_unpacker_event_with_c_backend(
            "amiga-hunk",
            parent_path,
            event["event_id"],
            output_path,
            project_root=PROJECT_ROOT,
        )
    assert not output_path.exists()


def test_real_dll_voodoo_tetragon_unpacker_comparator(tmp_path: Path) -> None:
    _requires_c_backend_dlls()

    fixture = PROJECT_ROOT / "tests" / "fixtures" / "hunk" / "voodoo_ake_tetragon.bin"
    analysis = analyze_binary_source_with_c_backend(fixture, project_root=PROJECT_ROOT)
    event = next(event for event in analysis["decompression_events"] if event.get("codec_id") == "tetragon")
    self_decrunch_events = [
        item for item in analysis["decompression_events"] if item.get("source_kind") == "self_decruncher"
    ]
    output_path = tmp_path / "voodoo_ake_tetragon.bin"

    result = materialize_recognized_unpacker_event_with_c_backend(
        "amiga-hunk",
        fixture,
        event["event_id"],
        output_path,
        project_root=PROJECT_ROOT,
    )

    output = output_path.read_bytes()
    assert event["status"] == "materializable"
    assert event["payload_role"] == "primary_program"
    assert event["source_section_offset"] == 0xE8
    assert event["compressed_source_section_end_offset"] == 0x62F0
    assert event["postpass_source_start_address"] == 0x5F68D
    assert event["postpass_source_end_address"] == 0x67000
    assert event["postpass_escape_byte"] == 0x9B
    assert event["target_start_address"] == 0x5C000
    assert event["target_end_address"] == 0x65BA7
    assert event["entrypoint"] == 0x5C000
    assert self_decrunch_events == []
    assert result["status"] == "ok"
    assert len(output) == 39847
    assert hashlib.sha256(output).hexdigest() == "7ec283de794a7ddc64d8f2c3a4aa8545aee9e782476ebe75e48da8a117dd404e"


def test_real_dll_magicland_self_decrunch_materialization(tmp_path: Path) -> None:
    _requires_c_backend_dlls()

    fixture = PROJECT_ROOT / "tests" / "fixtures" / "hunk" / "magicland_trsi_trainer_self_decrunch.bin"
    analysis = analyze_binary_source_with_c_backend(fixture, project_root=PROJECT_ROOT)
    event = next(event for event in analysis["decompression_events"] if event.get("source_kind") == "self_decruncher")
    output_path = tmp_path / "magicland_trsi_trainer_self_decrunch.bin"

    result = materialize_self_decrunch_event_with_c_backend(
        "amiga-hunk",
        fixture,
        event["event_id"],
        output_path,
        project_root=PROJECT_ROOT,
    )

    output = output_path.read_bytes()
    assert event["status"] == "simulated_output_observed"
    assert event["reason"] == "simulated_pc_range_stop"
    assert event["simulated_step_count"] > 262144
    assert event["simulated_output_size"] == 43695
    assert event["load_address"] == 0x20000
    assert event["entrypoint"] == 0x20000
    assert event["simulated_output_sha256"] == "f867bec7c8a062b9d086ea170cd297d620c0a5e32fd90caf14a979f4fe13fce4"
    assert result["status"] == "ok"
    assert len(output) == 43695
    assert hashlib.sha256(output).hexdigest() == event["simulated_output_sha256"]


def test_real_dll_voodoo_trainer_decompression_comparator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _requires_c_backend_dlls()
    monkeypatch.chdir(tmp_path)

    archive = PROJECT_ROOT / "resources" / "platform_amiga" / (
        "Voodoo Nightmare (1990)(Palace)[cr CLS][t +13 Flashtro].zip"
    )
    member = "Voodoo Nightmare (1990)(Palace)[cr CLS][t +13 Flashtro].adf"
    if not archive.exists():
        pytest.skip("Voodoo Nightmare comparator archive is missing")

    adf_path = tmp_path / "voodoo.adf"
    with ZipFile(archive) as zip_file:
        adf_path.write_bytes(zip_file.read(member))
    trainer_path = tmp_path / "trainer"
    trainer_path.write_bytes(extract_disk_entry_with_c_backend(adf_path, "Trainer", project_root=PROJECT_ROOT))

    analysis = analyze_binary_source_with_c_backend(trainer_path, project_root=PROJECT_ROOT)
    payloads = analysis["packed_payloads"]
    suggestions = analysis["derived_target_suggestions"]
    events = analysis["decompression_events"]

    assert len(payloads) == 1
    assert payloads[0]["provider_id"] == "ancient-cli"
    assert payloads[0]["codec_id"] == "rnc1"
    assert payloads[0]["codec_support"] == "external_provider"
    assert payloads[0]["source_section"] == 1
    assert payloads[0]["source_section_offset"] == 8
    assert payloads[0]["packed_size"] == 11406
    assert payloads[0]["decompressed_size"] == 84980
    assert len(suggestions) == 1
    assert len(events) == 1
    assert suggestions[0]["status"] == "needs_runtime_metadata"
    assert events[0]["status"] == "needs_runtime_metadata"
    assert suggestions[0]["event_kind"] == "decompression"
    assert suggestions[0]["codec_support"] == "external_provider"
    assert suggestions[0]["payload_role"] == "unknown_runtime_payload"
    assert suggestions[0]["source_section"] == 1
    assert suggestions[0]["source_section_offset"] == 8


@pytest.mark.parametrize(
    "target_name",
    [
        "amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_devs__serial.device_ddfdac2b",
        "amiga_disk_starglider-1987-rainbird__amiga_hunk_devs__serial.device_ddfdac2b",
    ],
)
def test_real_dll_serial_device_app_slot_widths_stay_evidence_backed(target_name: str) -> None:
    _requires_c_backend_dlls()

    paths = _requires_project_paths(target_name)
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "app_01D9 RS.B 1\n" in source_text
    assert "app_01DB RS.B 1\n" in source_text
    assert "app_01DC RS.L 1\n" not in source_text


def test_real_dll_voodoo_absolute_four_stays_numeric_not_initial_pc_vector() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths(
        "amiga_disk_voodoo-nightmare-1990-palace-cr-angels-defjam-genesis__amiga_hunk_run_df6ad190",
        project_root=PROJECT_ROOT,
    )
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "m68k_vector_initial_pc\tEQU\t$4\n" not in source_text
    assert "\tmove.l #$1,$0004.w\n" in source_text
    assert "\tmove.l #$1,m68k_vector_initial_pc.w\n" not in source_text


def test_real_dll_voodoo_adjacent_branch_stub_table_recovers_handlers() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths(
        "amiga_disk_voodoo-nightmare-1990-palace-cr-angels-defjam-genesis__amiga_hunk_run_df6ad190",
        project_root=PROJECT_ROOT,
    )
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert source_text_profile["facts_v2"]["code_start_platform_loadseg_entries"] == 1
    assert "loc_3_00000000:\n\tmoveq.l #0,d5\n\taddq.w #1,d6\n" in source_text
    assert "    SECTION section_3,code\n\tdc.b $7A,$00,$52,$46" not in source_text
    assert (
        "loc_6_0000016A:\n"
        "    ORG $78000\n"
        "abs_6_00078000:\n"
        "\tbra.w abs_6_000780B4\n"
        "abs_6_00078004:\n"
        "\tbra.w abs_6_000780EA\n"
    ) in source_text
    assert "abs_6_000780B4:\n\tmovem.l d1-d7/a0-a6,-(a7)\n" in source_text
    assert "\tdc.b $60,$00,$00,$B2\nloc_6_0000016E:" not in source_text


def test_real_dll_carrier_clipboard_relocation_backed_jump_templates_are_code() -> None:
    _requires_c_backend_dlls()

    target_name = "amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_devs__clipboard.device_2e6f0d10"
    paths = _requires_project_paths(target_name)
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert (
        "resident_vectors:\n"
        "\tjmp clipboard_device_lib_open.l\n"
        "loc_2_0000006E:\n"
        "\tjmp clipboard_device_lib_close.l\n"
    ) in source_text
    assert "clipboard_device_dev_abortio:\n\tmovem.l d0/a1,-(a7)\n" in source_text
    assert "clipboard_device_dev_beginio:\n\tmove.l a1,-(a7)\n" in source_text
    assert "\tdc.b $4E,$F9\n\tdc.l loc_0_00000088\n" not in source_text


def test_real_dll_carrier_serial_device_renders_non_autoinit_vectors() -> None:
    _requires_c_backend_dlls()

    target_name = "amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_devs__serial.device_ddfdac2b"
    paths = _requires_project_paths(target_name)
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "resident_vectors:\n\tdc.b $FF,$FF\n" in source_text
    assert "serial_device_lib_open:\n\tclr.b $001F(a1)\n" in source_text
    assert "serial_device_dev_beginio:" in source_text
    assert "    ; KNOWN: base A6=serial.device:LIB\nserial_device_lib_open:" in source_text


def test_real_dll_carrier_ramdrive_relocation_backed_template_seeds_target_code() -> None:
    _requires_c_backend_dlls()

    target_name = "amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_devs__ramdrive.device_2c146d8c"
    paths = _requires_project_paths(target_name)
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert source_text_profile["facts_v2"]["asm_source_lossy_numeric_hunk_relocations"] == 0
    assert "\tdc.l __section_0_base-$00000004\t; facts_v2 HUNK_RELOC32 anchor: base(hunk 0)-$00000004\n" in source_text
    assert "HUNK_RELOC32 numeric: source hunk 0 offset $0000002E" not in source_text
    assert "loc_0_00000000-$00000004" not in source_text
    assert source_text_profile["facts_v2"]["accepted_instructions"] >= 436
    assert "loc_0_0000062C:\n\tbra.b loc_0_0000064C\n" in source_text
    assert "loc_0_0000068A:\n\tbtst.b #0,$001B(a1)\n" in source_text
    assert "\tdc.b $60,$1E,$60,$1C,$60,$36,$60,$56\n" not in source_text
    assert "loc_0_00000718:\n\tmovea.l $0004.w,a0\n" in source_text
    assert "\tdc.b $20,$78,$00,$04,$52,$28,$01,$27\n" not in source_text
    assert "    ORG $4\n" not in source_text
    rebuilt, direct_source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        compare_original=True,
        project_root=PROJECT_ROOT,
    )
    assert len(rebuilt) == len(paths.binary_source.read_bytes())
    assert direct_source_profile["facts_v2"]["asm_source_refused"] is False
    assert direct_source_profile["facts_v2"]["unassemblable_hunk_data_relocations"] == 1
    assert direct_source_profile["facts_v2"]["asm_source_lossy_numeric_hunk_relocations"] == 0
    assert direct_profile["direct_rebuild_refused"] is False
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_monam_keeps_unrelocated_jump_bytes_as_data() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths("amiga_hunk_monam302", project_root=PROJECT_ROOT)
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "dc.b $4E,$F9" in source_text
    assert "resident_vectors" not in source_text
    assert "    ORG $4\n" not in source_text


def test_real_dll_conqueror_file_handle_slots_do_not_alias_dosbase() -> None:
    _requires_c_backend_dlls()

    target_name = "amiga_disk_conqueror-1990-rainbow-arts-de-en__amiga_hunk_conqueror_cf971606"
    paths = resolve_project_paths(
        target_name,
        project_root=PROJECT_ROOT,
    )
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "\tmovea.l loc_0_00000004.l,a6\n" not in source_text
    assert source_text.count("\tmovea.l $00000004.l,a6\n") == 2
    assert "\tlea.l loc_0_00000148.l,a0\n" in source_text
    assert "\tlea.l abs_0_00000004.l,a0\n" not in source_text
    assert "runtime_code_00000004\tEQU\t$4\n" in source_text
    assert "\tlea.l runtime_code_00000004.l,a1\n" in source_text
    assert "\tjmp runtime_code_00000004.l\n" in source_text
    assert "    ORG $4\n" not in source_text
    assert source_text.count("    ORG $40\n") == 1
    assert "loc_0_00000004:" not in source_text
    assert "abs_0_00000004:" not in source_text
    assert "loc_0_00000154:\n    ORG $40\nabs_0_00000040:\n" in source_text
    assert "abs_0_00000040:\n\tori.b" not in source_text
    assert "abs_0_00000040:\n\tdc.b $00,$00,$03,$F3" in source_text
    assert "abs_0_00000064:\n\tlea.l abs_0_0000014C(pc),a0\n" in source_text
    assert "\tclr.l spr1+sd_dataa(a6)\n" in source_text
    assert "\tclr.l app_014C(a6)\n" not in source_text
    assert "app_014C" not in source_text.split("    SECTION section_0,code\n", 1)[0]
    assert "\tmove.l d0,loc_0_0000004E.l\n" in source_text
    assert "\tmove.l d0,loc_0_00000052.l\n" in source_text
    assert "\tmove.l loc_0_0000004E.l,d1\n" in source_text
    assert source_text.count("h0dl_DOSBase:") == 1
    rows, _, listing_profile = build_project_listing_rows_profile_with_c_artifact(
        target_name,
        project_root=PROJECT_ROOT,
    )
    assert listing_profile["facts_v2"]["asm_source_refused"] is False
    row_texts = [str(row["text"]).rstrip("\n") for row in rows]
    assert row_texts.count("    ORG $4") == 0
    assert row_texts.count("    ORG $40") == 1
    assert "loc_0_00000004:" not in row_texts
    assert "abs_0_00000004:" not in row_texts
    assert "runtime_code_00000004\tEQU\t$4" in row_texts
    storage_label_row = next(row for row in rows if row.get("label") == "loc_0_00000154")
    runtime_label_row = next(row for row in rows if row.get("label") == "abs_0_00000040")
    assert storage_label_row["runtime_address"] == 0x40
    assert runtime_label_row["runtime_address"] == 0x40
    assert row_texts.index("loc_0_00000154:") < row_texts.index("    ORG $40")
    assert row_texts.index("    ORG $40") < row_texts.index("abs_0_00000040:")
    rebuilt, direct_source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        compare_original=True,
        project_root=PROJECT_ROOT,
    )
    assert len(rebuilt) == len(paths.binary_source.read_bytes())
    assert direct_source_profile["facts_v2"]["asm_source_refused"] is False
    assert direct_profile["direct_rebuild_exact"] is True


def test_real_dll_starglider_loader_file_handle_slot_stays_untyped() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths(
        "amiga_disk_starglider-1987-rainbird__amiga_hunk_sgload_ee6b361e",
        project_root=PROJECT_ROOT,
    )
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "\tmove.l d0,loc_0_00000304.l\n" in source_text
    assert "\tmove.l loc_0_00000304.l,d1\n" in source_text
    assert source_text.count("\tmove.l d0,h0dl_DOSBase.l\n") == 1


def test_real_dll_starglider_main_app_slot_widths_stay_evidence_backed() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths(
        "amiga_disk_starglider-1987-rainbird__amiga_hunk_sg_9832b282",
        project_root=PROJECT_ROOT,
    )
    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "app_0050 RS.L 1\n" not in source_text
    assert "app_005D RS.B 1\n" in source_text
    assert "app_005F RS.B 1\n" in source_text
    assert "app_016A RS.L 1\n" not in source_text


def test_real_dll_starglider_mathtrans_linkage_api_labels_promote_wrappers() -> None:
    _requires_c_backend_dlls()

    combined = _facts_v2_listing_analysis_for_project(
        "amiga_disk_starglider-1987-rainbird__amiga_hunk_libs__mathtrans.library_30d0f132"
    )
    section = combined["analysis"]["sections"][15]
    linkage_refs = {
        ref["offset"]
        for ref in section["code_start_refs"]
        if ref.get("reason_name") == "linkage_api_entry"
    }
    rows_by_offset = {
        row["start_offset"]: row
        for row in combined["listing"]["rows"]
        if row.get("section_index") == 15 and row.get("kind") == "instruction"
    }
    api_orphans = [
        signal
        for signal in section["orphan_code_signals"]
        if signal.get("missing_inbound") == "api"
    ]

    assert linkage_refs == {0x14}
    assert rows_by_offset[0x14]["text"] == "\tmove.l a6,-(a7)\n"
    assert rows_by_offset[0x1C]["text"] == "\tjsr -$0210(a6)\n"
    assert not api_orphans


def test_real_dll_openlibrary_d0_to_a6_resolves_followup_calls() -> None:
    _requires_c_backend_dlls()

    cases = {
        "amiga_disk_conqueror-1990-rainbow-arts-de-en__amiga_hunk_conqueror_cf971606": {
            0x16: "_LVOOutput",
            0x20: "_LVOInput",
        },
        "amiga_disk_starglider-1987-rainbird__amiga_hunk_sgload_ee6b361e": {
            0x24: "_LVOOpen",
            0x42: "_LVOWrite",
        },
    }
    for target_name, expected_calls in cases.items():
        combined = _facts_v2_listing_analysis_for_project(target_name)
        calls_by_offset = {
            call["offset"]: call["symbol_name"]
            for section in combined["analysis"]["sections"]
            for call in section["recovered_platform_calls"]
        }
        unresolved_offsets = {
            site["offset"]
            for section in combined["analysis"]["sections"]
            for site in section["recovered_indirect_sites"]
            if site["status"] == "unresolved"
        }
        for offset, symbol_name in expected_calls.items():
            assert calls_by_offset[offset] == symbol_name
            assert offset not in unresolved_offsets


def test_real_dll_cross_section_openlibrary_name_resolves_followup_calls() -> None:
    _requires_c_backend_dlls()

    combined = _facts_v2_listing_analysis_for_project(
        "amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_trio_6d66c94c"
    )
    calls_by_offset = {
        call["offset"]: call["symbol_name"]
        for section in combined["analysis"]["sections"]
        for call in section["recovered_platform_calls"]
    }
    unresolved_offsets = {
        site["offset"]
        for section in combined["analysis"]["sections"]
        for site in section["recovered_indirect_sites"]
        if site["status"] == "unresolved"
    }
    assert calls_by_offset[0x76] == "_LVOOpen"
    assert calls_by_offset[0x94] == "_LVORead"
    assert calls_by_offset[0xF6] == "_LVOClose"
    assert calls_by_offset[0xA2E] == "_LVOExecute"
    assert not unresolved_offsets


def test_real_dll_monam_openlibrary_app_slot_resolves_dos_calls() -> None:
    _requires_c_backend_dlls()

    combined = _facts_v2_listing_analysis_for_project("amiga_hunk_monam302")
    calls_by_offset = {
        call["offset"]: call["symbol_name"]
        for section in combined["analysis"]["sections"]
        for call in section["recovered_platform_calls"]
    }
    unresolved_offsets = {
        site["offset"]
        for section in combined["analysis"]["sections"]
        for site in section["recovered_indirect_sites"]
        if site["status"] == "unresolved"
    }
    expected_calls = {
        0x1AFE: "_LVOIoErr",
        0x448E: "_LVOUnLoadSeg",
        0x555E: "_LVOLoadSeg",
        0x5646: "_LVOCreateProc",
        0x73C4: "_LVOOpen",
        0x7438: "_LVORead",
        0x7450: "_LVOWrite",
        0x747C: "_LVOClose",
    }
    for offset, symbol_name in expected_calls.items():
        assert calls_by_offset[offset] == symbol_name
        assert offset not in unresolved_offsets


def test_real_dll_bloodwych_generated_source_assembles_exact(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    paths = resolve_project_paths(
        "amiga_hunk_bloodwych",
        project_root=PROJECT_ROOT,
    )

    source_text, source_text_profile = listing_artifact_source_text_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )
    rebuilt, assembler_profile = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        source_text,
        include_dir=PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
        output_path=tmp_path / "bloodwych_generated_source.hunk",
        target_cpu="any",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    section_pos = source_text.index("    SECTION section,code_c\n")
    assert source_text.index("    RSSET 0\n") < section_pos
    assert source_text.index('    INCLUDE "hardware/custom.i"\n') < section_pos
    assert source_text.index('    INCLUDE "graphics/display.i"\n') < section_pos
    assert source_text.index("INTF_CLRALL\tEQU\t$7FFF\n") < section_pos
    assert "\nloc_0_00000000:\nINTF_CLRALL\tEQU" not in source_text
    assert "loc_0_0000005C:\n    ORG $400\nabs_0_00000400:" in source_text
    assert "ORG $5C" not in source_text
    assert "loc_0_0000005C\tEQU" not in source_text
    assert "\tmove.w #$400,(a0)\n" in source_text
    assert "\tmove.w #abs_0_00000400,(a0)\n" not in source_text
    assert "\tmove.l #abs_0_00008E10,_custom+cop1lc.l\t; copper_list pointer\n" in source_text
    assert (
        "\tmove.l a0,_custom+aud0+ac_ptr.l\t"
        "; source loc_0_00054452 + dynamic offset from loc_0_00008938 | sound_sample pointer\n"
    ) in source_text
    assert (
        "\tmove.w d1,_custom+aud0+ac_len.l\t"
        "; audio sample length derived from -$0002(a0) header word\n"
    ) in source_text
    assert "\tmove.w #$40,_custom+aud0+ac_vol.l\t; audio volume 64\n" in source_text
    assert "\tadda.w abs_0_00008938(pc,d0.w),a0\n" in source_text
    assert "\tmove.w abs_0_0000893A(pc,d0.w),d0\n" in source_text
    assert "\tmove.l a1,_custom+dskpt.l\t; disk_buffer pointer $00067D00\n" in source_text
    assert "disk_buffer_00067D00\tEQU\t$67D00\n" in source_text
    assert "\tmove.l #disk_buffer_00067D00,abs_0_00008D36.l\n" in source_text
    assert "bitmap_00060000\tEQU\t$60000\n" in source_text
    assert "\tmove.l #bitmap_00060000,d0\n" in source_text
    assert (
        "\tmove.w #(4<<PLNCNTSHFT)|COLORON,_custom+bplcon0.l\t"
        "; display 4 bitplanes lores color\n"
    ) in source_text
    assert "\tmove.w #$0,_custom+bplcon1.l\t; display scroll pf1=0 pf2=0\n" in source_text
    assert "\tmove.w #BPLCON2_PF2P2|BPLCON2_PF1P2,_custom+bplcon2.l\n" in source_text
    assert "\tmove.w #$3781,_custom+diwstrt.l\t; display window start v=$37 h=$81\n" in source_text
    assert "\tmove.w #$38,_custom+ddfstrt.l\t; display fetch start $38\n" in source_text
    assert "\tmove.w #$0,_custom+bpl1mod.l\t; bitplane modulo 0 bytes\n" in source_text
    assert "\tmove.w #$4489,_custom+dsksync.l\t; disk sync word $4489\n" in source_text
    assert "\tmove.w #$9F40,_custom+dsklen.l\t; disk DMA read 16000 bytes\n" in source_text
    assert (
        "\tmove.w d0,_custom+aud0+ac_per.l\t"
        "; period from loc_0_0000893A transformed | audio period\n"
    ) in source_text
    assert "\tmove.w (a0),_custom+aud0+ac_dat.l\t; audio data word\n" in source_text
    assert "abs_0_0000C484:\n\tdc.l abs_0_0000C938\t; pointer_table\n" in source_text
    assert "\tdc.l abs_0_0000C852\n\tdc.l abs_0_0000CB28\n" in source_text
    assert "abs_0_00008938:\n\tdc.w $0000\t; lookup_table\n" in source_text
    assert (
        "abs_0_0000893A:\n"
        "\tdc.w $0028,$0000,$009B,$0084,$005D,$0646,$0028,$1ECE\t; lookup_table\n"
    ) in source_text
    assert "\tdc.w $0049,$3684,$0049\t; lookup_table\nabs_0_00008950:\n" in source_text
    assert (
        "abs_0_000015AE:\n"
        "\tdc.w abs_0_0000166A-abs_0_0000166A\t; lookup_table\n"
        "\tdc.w abs_0_000015D6-abs_0_0000166A\n"
        "\tdc.w abs_0_0000175A-abs_0_0000166A\n"
        "\tdc.w abs_0_000015B8-abs_0_0000166A\n"
        "\tdc.w abs_0_00001664-abs_0_0000166A\n"
    ) in source_text
    assert (
        "abs_0_0000A73A:\n"
        "\tdc.w abs_0_0000A50A-abs_0_0000A73A\t; lookup_table\n"
        "\tdc.w abs_0_00009EFA-abs_0_0000A73A\n"
        "\tdc.w abs_0_0000A34C-abs_0_0000A73A\n"
        "\tdc.w abs_0_0000A330-abs_0_0000A73A\n"
        "\tdc.w abs_0_0000A53C-abs_0_0000A73A\n"
    ) in source_text
    assert (
        "abs_0_00002E4A:\n"
        "\tdc.w abs_0_00002E5C-abs_0_00002E5C\t; lookup_table\n"
        "\tdc.w abs_0_00002E82-abs_0_00002E5C\n"
        "\tdc.w abs_0_00002EE4-abs_0_00002E5C\n"
        "\tdc.w abs_0_00002E5C-abs_0_00002E5C\n"
    ) in source_text
    assert (
        "abs_0_00003526:\n"
        "\tdc.w abs_0_0000355C-abs_0_0000355C\t; lookup_table\n"
        "\tdc.w abs_0_0000356A-abs_0_0000355C\n"
        "\tdc.w abs_0_00003572-abs_0_0000355C\n"
        "\tdc.w abs_0_0000357A-abs_0_0000355C\n"
    ) in source_text
    assert "\tdc.w $0000,$000E,$0016,$001E\t; lookup_table\n" not in source_text
    assert (
        "abs_0_00005B68:\n"
        "\tdc.w abs_0_00005B66-abs_0_00005B66\t; lookup_table\n"
        "\tdc.w abs_0_00005D12-abs_0_00005B66\n"
        "\tdc.w abs_0_00005CFC-abs_0_00005B66\n"
        "\tdc.w abs_0_00007746-abs_0_00005B66\n"
        "\tdc.w abs_0_000076B4-abs_0_00005B66\n"
        "\tdc.w abs_0_0000776C-abs_0_00005B66\n"
        "\tdc.w abs_0_00007768-abs_0_00005B66\n"
        "\tdc.w abs_0_00007758-abs_0_00005B66\n"
    ) in source_text
    assert "\tdc.w $1B4E,$1C06,$1C02,$1BF2\t; lookup_table\n" not in source_text
    assert (
        "abs_0_00007018:\n"
        "\tdc.w abs_0_00007016-abs_0_00007016\t; lookup_table\n"
        "\tdc.w abs_0_00007712-abs_0_00007016\n"
        "\tdc.w abs_0_0000771A-abs_0_00007016\n"
        "\tdc.w abs_0_00007746-abs_0_00007016\n"
    ) in source_text
    assert "\tdc.w $0000,$06FC,$0704,$0730\t; lookup_table\n" not in source_text
    assert "abs_0_00005C6E:\n" not in source_text
    assert "abs_0_00007216:\n" not in source_text
    assert "\tsubi.w #20,d1\n\tbcs.b abs_0_00002E76\n" in source_text
    assert (
        "abs_0_000033A0:\n"
        "\tdc.w abs_0_000033B2-abs_0_000033B2\t; lookup_table\n"
        "\tdc.w abs_0_000033EE-abs_0_000033B2\n"
        "\tdc.w abs_0_00004150-abs_0_000033B2\n"
        "\tdc.w abs_0_000040E4-abs_0_000033B2\n"
        "\tdc.w abs_0_00003F60-abs_0_000033B2\n"
        "\tdc.w abs_0_00004144-abs_0_000033B2\n"
        "\tdc.w abs_0_00003F5C-abs_0_000033B2\n"
        "\tdc.w abs_0_00003E9C-abs_0_000033B2\n"
        "\tdc.w abs_0_000034CC-abs_0_000033B2\n"
    ) in source_text
    assert (
        "\tlea.l abs_0_0000C266-4.l,a0\n"
        "\tmovea.l $0(a0,d0.w),a0\n"
        "\tjmp (a0)\n"
        "abs_0_0000C266:\n"
        "\tdc.l abs_0_0000C53C\t; pointer_table\n"
        "\tdc.l abs_0_0000C436\n"
        "\tdc.l abs_0_0000C490\n"
        "\tdc.l abs_0_0000C516\n"
        "\tdc.l abs_0_0000C286\n"
        "\tdc.l abs_0_0000C2EA\n"
        "\tdc.l abs_0_0000C1F4\n"
        "\tdc.l abs_0_0000C2EA\n"
        "abs_0_0000C286:\n"
    ) in source_text
    assert "\tjsr abs_0_000008F2.w\n" in source_text
    assert source_text.count("\tjsr abs_0_000041FA.w\n") == 2
    assert "\tjsr $08F2.w\n" not in source_text
    assert "\tjsr $41FA.w\n" not in source_text
    assert "\tmove.b d0,abs_0_000005C9.w\n" in source_text
    assert (
        "abs_0_00007D44:\n"
        "\tdc.l abs_0_00007CA0,abs_0_00007CA6,$00000000,abs_0_00007CD6\t; lookup_table\n"
        "\tdc.l abs_0_00007D20,abs_0_00007D26,abs_0_00007D2C,abs_0_00007D32\t; lookup_table\n"
        "\tdc.l abs_0_00007D38,abs_0_00007D3E\t; lookup_table\n"
    ) in source_text
    display_summary = (
        "    ; display layout 4 bitmap planes $00070000..$00076000 step $2000 | "
        "display setup 4 bitplanes lores color window v=$37..$FF h=$81..$C1 rows 200 "
        "fetch $38..$D0 row 40 bytes/plane mod 0/0 span $1F40/plane\n"
    )
    assert display_summary in source_text
    assert "bitmap_00070000\tEQU\t$70000\n" in source_text
    assert "bitmap_00070000_hi\tEQU\tbitmap_00070000/$10000\n" in source_text
    assert "bitmap_00070000_lo\tEQU\tbitmap_00070000-(bitmap_00070000_hi*$10000)\n" in source_text
    assert (
        "abs_0_00008E10:\n"
        f"{display_summary}"
        "\tdc.w bplpt,bitmap_00070000_hi\t; bitmap pointer $00070000\n"
    ) in source_text
    assert "\tdc.w bplpt+$02,bitmap_00070000_lo\n" in source_text
    assert "\tdc.w bplpt+$04,bitmap_00072000_hi\t; bitmap pointer $00072000\n" in source_text
    assert "\tdc.w bplpt+$06,bitmap_00072000_lo\n" in source_text
    assert "\tdc.w bplpt+$08,bitmap_00074000_hi\t; bitmap pointer $00074000\n" in source_text
    assert "\tdc.w bplpt+$0A,bitmap_00074000_lo\n" in source_text
    assert "\tdc.w bplpt+$0C,bitmap_00076000_hi\t; bitmap pointer $00076000\n" in source_text
    assert "\tdc.w bplpt+$0E,bitmap_00076000_lo\n" in source_text
    assert "abs_0_00008E30:\n\tdc.w sprpt,$0000\t; sprite pointer 0 disabled\n" in source_text
    assert "\tdc.w sprpt+$1E,$0000\n" in source_text
    assert "\tdc.w COPPER_WAIT|$9800,$FF00\t; copper wait v=$98 h=$00 mask $FF00\n" in source_text
    assert "\tdc.w COPPER_WAIT|$FF00,$FF00\t; copper wait v=$FF h=$00 mask $FF00\n" in source_text
    assert "\tdc.w intreq,INTF_SETCLR|INTF_COPER\n" in source_text
    assert "m68k_vector_level_3_interrupt_autovector\tEQU\t$6C" in source_text
    assert "\tmove.l #abs_0_00008C20,m68k_vector_level_3_interrupt_autovector.w\n" in source_text
    assert "$00DFF" not in source_text
    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert assembler_profile["rebuilt_bytes"] == len(rebuilt)
    assert _amiga_hunk_section_hexes(tmp_path / "bloodwych_generated_source.hunk") == _amiga_hunk_section_hexes(
        paths.binary_source.path
    )
    assert source_text_profile["facts_v2"]["asm_source_instruction_byte_mismatches"] == 0


def test_real_dll_inspects_and_extracts_dos_disk_entry() -> None:
    _requires_c_backend_dlls()
    disk_path = PROJECT_ROOT / "bin" / "Search for the King, The (1991)(Accolade)(Disk 1 of 5).adf"

    analysis = inspect_disk_with_c_backend(disk_path)
    entries = analysis.get("entries")
    assert isinstance(entries, list)
    icon_entry = next(
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("path") == "libs/icon.library" and entry.get("byte_size", 0) > 0
    )

    payload = extract_disk_entry_with_c_backend(disk_path, "libs/icon.library")
    assert len(payload) == icon_entry["byte_size"]
    assert payload[:4] == b"\x00\x00\x03\xf3"


def test_real_dll_renders_icon_library_resident_structure() -> None:
    _requires_c_backend_dlls()
    target_name = (
        "amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5__"
        "amiga_hunk_libs__icon.library_8bc90c0c"
    )
    paths = _requires_project_paths(target_name)

    rendered = render_project_source_with_c_backend(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert "    RSSET LIB_SIZE\napp_ExecBase RS.L 1\napp_DOSBase RS.L 1\napp_SegList RS.L 1\napp_SIZEOF EQU __RS" in rendered
    assert rendered.index("    RSSET LIB_SIZE\n") < rendered.index("    SECTION section_0,code\n")
    assert "app_ExecBase EQU 34" not in rendered
    assert "app_DOSBase EQU 38" not in rendered
    assert "app_SegList EQU 42" not in rendered
    assert "resident:\t; STRUCT RT" in rendered
    assert "\tdc.w RTC_MATCHWORD\t; UWORD RT_MATCHWORD" in rendered
    assert "\tdc.l resident\t; APTR RT_MATCHTAG" in rendered
    assert "\tdc.l loc_0_00000280\t; APTR RT_ENDSKIP" in rendered
    assert "\tdc.b RTF_AUTOINIT\t; UBYTE RT_FLAGS" in rendered
    assert "\tdc.b NT_LIBRARY\t; UBYTE RT_TYPE" in rendered
    assert "\tdc.l resident_autoinit\t; APTR RT_INIT" in rendered
    assert "\tdc.b $22\t; UBYTE RT_VERSION" in rendered
    assert "\tdc.b $46\t; BYTE RT_PRI" in rendered
    assert "\tdc.l resident_name\t; APTR RT_NAME" in rendered
    assert "\tdc.l resident_idstring\t; APTR RT_IDSTRING" in rendered
    assert 'resident_name:\n\tdc.b "icon.library",$00' in rendered
    assert 'resident_idstring:\n\tdc.b "icon 34.2 (22 Jun 1988)",$0D,$0A,$00' in rendered
    assert "resident_autoinit:\t; STRUCT resident_autoinit" in rendered
    assert "\tdc.l app_SIZEOF\t; ULONG resident_base_size" in rendered
    assert "DC.L    LIB_SIZE+12                 ; ULONG resident_base_size" not in rendered
    assert "\tdc.l resident_vectors\t; APTR resident_vectors" in rendered
    assert "\tdc.l resident_init_struct\t; APTR resident_init_struct" in rendered
    assert "\tdc.l resident_init\t; APTR resident_init_function" in rendered
    assert "resident_vectors:" in rendered
    assert "\tdc.l icon_lib_open" in rendered
    assert "resident_init_struct:" in rendered
    assert "\tdc.b $E0,$00,$00,$08,$09,$00,$C0,$00,$00,$0A" in rendered
    assert "\tdc.l resident_name" in rendered
    assert "res_MatchWord:" not in rendered
    assert "res_Flags:" not in rendered
    assert "DC.W    $4afc ; NOTE: resident matchword" not in rendered
    assert "\tdc.l icon_lib_open\n" in rendered
    assert "\tdc.l get_disk_object\n" in rendered
    assert "icon_lib_open:\nloc_00DC:" not in rendered
    assert "resident_init:\n\tmove.l a2,-(a7)" in rendered
    assert "loc_0148:" not in rendered
    assert "move.l a0,app_SegList(a2)" in rendered
    assert "move.l a6,app_ExecBase(a2)" in rendered
    assert "move.l d0,app_DOSBase(a2)" in rendered
    assert "movea.l $0004.w,a6" in rendered
    assert "resident.w,a6" not in rendered
    assert "base A6=exec.library:LIB" in rendered
    assert "KNOWN: base A6=icon.library" in rendered
    assert rendered.index('    INCLUDE "exec/libraries.i"\n') < rendered.index("    SECTION section_0,code\n")
    assert "icon_lib_open:\n\taddq.w #1,LIB_OPENCNT(a6)" in rendered
    assert "icon_lib_open:\n\taddq.w #1,$0020(a6)" not in rendered
    assert "icon_lib_extfunc:\n\tmoveq.l #0,d0" in rendered
    assert "dat_00A4+44" not in rendered
    assert "VIOLATION: pc-relative" not in rendered
    assert "lea.l loc_0_000000D0(pc),a1" in rendered
    assert "lea.l -$86(pc),a1" not in rendered
    assert "move.l app_ExecBase(a2),h0dl_ExecBase.l" in rendered
    assert "move.l app_DOSBase(a2),h0dl_DOSBase.l" in rendered
    assert "absolute in-section address $0192 has no relocation" not in rendered
    assert "absolute in-section address $0196 has no relocation" not in rendered
    assert "move.l app_SegList(a6),-(a7)" in rendered
    assert "movea.l (a1),a0" in rendered
    assert "movea.l $0004(a1),a1" in rendered
    assert "move.l a0,(a1)" in rendered
    assert "move.l a1,$0004(a0)" in rendered
    assert "move.l #AN_IconLib|AG_OpenLib|AO_DOSLib,d7" in rendered
    assert "movea.l app_ExecBase(a6),a6" in rendered
    assert "movea.l LIB_SIZE(a6),a6" not in rendered
    assert "h0dl_ExecBase:\n\tdc.b $00,$00,$00,$00" in rendered
    assert "h0dl_DOSBase:\n\tdc.b $00,$00,$00,$00" in rendered
    assert "dat_0192:" not in rendered
    assert "dat_0196:" not in rendered
    assert "$00000192.l" not in rendered
    assert "$00000196.l" not in rendered
    assert "jsr loc_3_00000000.l" in rendered
    assert "jsr $000000BC.l" not in rendered
    assert "hunk1_0000 EQU" not in rendered
    assert "hunk1_0092 EQU" not in rendered
    assert "hunk1_00BC EQU" not in rendered

    rows, _api_calls, _profile = build_project_listing_rows_with_c_artifact(target_name, project_root=PROJECT_ROOT)
    refs_by_text = {str(row["text"]).strip(): row["app_slot_refs"] for row in rows if row.get("app_slot_refs")}
    assert refs_by_text["move.l a6,app_ExecBase(a2)"] == [
        {"symbol": "app_ExecBase", "displacement": 34, "base_register": "A2", "operand_index": 1, "access": "write"}
    ]
    assert refs_by_text["move.l app_DOSBase(a2),h0dl_DOSBase.l"] == [
        {"symbol": "app_DOSBase", "displacement": 38, "base_register": "A2", "operand_index": 0, "access": "read"}
    ]
    assert "get_disk_object:" in rendered
    assert "\tlink a6,#-80" in rendered
    assert "jsr hunk3_0768.l ; CANDIDATE: indirect_call" not in rendered
    assert "jsr hunk3_0818.l ; CANDIDATE: indirect_call" not in rendered
    assert "sub_00A8:" not in rendered
    assert "loc_0_000000A8:" not in rendered
    assert "facts_v2 relocation" not in rendered
    assert "facts_v2 structured data" not in rendered
    assert "invalid overlap: decoded code at $00A8" not in rendered
    assert "ori.w #29999,a6" not in rendered
    assert "; NOTE: resident vector\n" not in rendered
    assert "@abs:" not in rendered[:1500]


def test_real_dll_listing_rows_keep_icon_lvo_comments_on_entrypoints() -> None:
    _requires_c_backend_dlls()
    project_name = (
        "amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5__"
        "amiga_hunk_libs__icon.library_8bc90c0c"
    )
    _requires_project_paths(project_name)

    rows, _, _ = build_project_listing_rows_profile_with_c_artifact(
        project_name,
        project_root=PROJECT_ROOT,
    )

    vector_index = next(index for index, row in enumerate(rows) if str(row["text"]).strip() == "resident_vectors:")
    dos_index = next(index for index, row in enumerate(rows) if str(row["text"]).strip() == 'dc.b "dos.library",$00')
    open_index = next(index for index, row in enumerate(rows) if str(row["text"]).strip() == "icon_lib_open:")

    assert rows[vector_index]["addr"] == 0x58
    assert rows[dos_index]["addr"] == 0xD0
    assert rows[open_index]["addr"] == 0xDC
    assert rows[open_index - 1]["kind"] == "comment"
    assert "KNOWN: base A6=icon.library:LIB" in str(rows[open_index - 1]["text"])
    assert not any(row["kind"] == "comment" for row in rows[vector_index:dos_index])


def test_real_dll_renders_mathtrans_overlap_as_data_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    if not assembler.exists():
        pytest.skip("m68k assembler app is missing; run cmd /c src\\build.bat")
    disk_path = PROJECT_ROOT / "resources" / "platform_amiga" / "ArgAsm1.06.adf"
    if not disk_path.exists():
        pytest.skip("ArgAsm1.06.adf fixture is missing")

    disk = inspect_disk_with_c_backend(disk_path, project_root=PROJECT_ROOT)
    entry = next(item for item in disk["entries"] if item.get("path") == "libs/mathtrans.library")
    metadata = entry["content"]["import_target"]["target_metadata"]
    vector_entries = metadata["resident"]["autoinit"]["vector_entries"]
    assert any(item["hunk"] != 0 for item in vector_entries)
    metadata_path = tmp_path / "target_metadata.json"
    source_path = tmp_path / "mathtrans.s"
    rebuilt_path = tmp_path / "mathtrans.bin"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    source = DiskEntryBinarySource(
        kind=BinarySourceKind.DISK_ENTRY,
        disk_id="resource_amiga_disk_argasm1.06",
        adf_path=disk_path,
        entry_path="libs/mathtrans.library",
        display_path="ArgAsm1.06.adf::libs/mathtrans.library",
        analysis_cache_path=tmp_path / "binary.analysis",
        project_root=PROJECT_ROOT,
    )

    rendered = render_project_source_with_c_backend(
        source,
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    source_path.write_text(rendered, encoding="ascii")

    assert "resident_vectors:" in rendered
    assert "dc.l s_p_atan" in rendered.lower()
    assert "ori.b #142,d0" not in rendered
    lowered = rendered.lower()
    assert "dc.b $19,$21,$fb,$54" in lowered
    assert "fpu     5" not in lowered
    assert "frestore" not in lowered
    assert "cprestore" not in lowered
    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "amiga-hunk",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert rebuilt_path.exists()


def test_real_dll_renders_pmove_form_specific_control_register_and_reassembles(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    if not assembler.exists():
        pytest.skip("m68k assembler app is missing; run cmd /c src\\build.bat")
    disk_path = PROJECT_ROOT / "resources" / "platform_atari_st" / "Devpac v3.10 (1992)(HiSoft).st"
    if not disk_path.exists():
        pytest.skip("Devpac Atari fixture is missing")

    source_path = tmp_path / "amon030.s"
    rebuilt_path = tmp_path / "amon030.prg"
    source = DiskEntryBinarySource(
        kind=BinarySourceKind.DISK_ENTRY,
        disk_id="resource_atari_devpac_3.10",
        adf_path=disk_path,
        entry_path="AMON/AMON030.PRG",
        display_path="Devpac v3.10 (1992)(HiSoft).st::AMON/AMON030.PRG",
        analysis_cache_path=tmp_path / "binary.analysis",
        project_root=PROJECT_ROOT,
    )

    rendered = render_project_source_with_c_backend(
        source,
        project_root=PROJECT_ROOT,
    )
    source_path.write_text(rendered, encoding="ascii")

    assert "pmove psr,(a7)" in rendered
    assert "pmove sfc,(a7)" not in rendered
    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "atari-st",
            "--include-dir",
            str(PROJECT_ROOT / "ext" / "atarist_includes" / "devpac_3_10" / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert rebuilt_path.exists()


def test_structural_label_at_zero_does_not_rewrite_absolute_short(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    resident = (
        bytes([0x4A, 0xFC])
        + (0).to_bytes(4, "big")
        + (0x20).to_bytes(4, "big")
        + bytes([0x80, 1, 0, 0])
        + (0).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
    )
    code_offset = len(resident) + 2
    code = resident + b"\x00\x00" + bytes.fromhex("2c7800044e75")
    binary_path = tmp_path / "resident_abs_short.exe"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=code))
    metadata_path.write_text(
        json.dumps(
            {
                "resident": {"hunk": 0, "offset": 0, "version": 1},
                "seeded_code_entrypoints": [{"hunk": 0, "addr": code_offset}],
            }
        ),
        encoding="utf-8",
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "analysis.json",
    )

    rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)

    assert "resident:" in rendered
    assert "movea.l $0004.w,a6" in rendered
    assert "resident.w,a6" not in rendered


def test_non_autoinit_resident_init_offset_seeds_entrypoint(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    resident = (
        bytes([0x4A, 0xFC])
        + (0).to_bytes(4, "big")
        + (0x22).to_bytes(4, "big")
        + bytes([0x00, 1, 3, 0])
        + (0).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + (0x1C).to_bytes(4, "big")
    )
    code = resident + b"\x00\x00" + bytes.fromhex("2c7800044e75")
    binary_path = tmp_path / "resident_non_autoinit_init.exe"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=code))
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "device",
                "resident": {
                    "name": "test.device",
                    "version": 1,
                    "offset": 0,
                    "hunk": 0,
                    "init_offset": 0x1C,
                    "autoinit": None,
                },
            }
        ),
        encoding="utf-8",
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "analysis.json",
    )

    rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)

    assert "resident:\t; STRUCT RT" in rendered
    assert "\tdc.l $0000001C\t; APTR RT_INIT" in rendered
    assert "resident_init:\n\tmovea.l $0004.w,a6\n\trts" in rendered
    assert "\tdc.b $2C,$78,$00,$04,$4E,$75" not in rendered


def test_non_autoinit_resident_make_library_vectors_seed_device_entrypoints(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    resident = (
        bytes([0x4A, 0xFC])
        + (0).to_bytes(4, "big")
        + (0x68).to_bytes(4, "big")
        + bytes([0x00, 1, 3, 0])
        + (0x5C).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + (0x40).to_bytes(4, "big")
    )
    code = bytearray(resident)
    code += b"\x00" * (0x30 - len(code))
    code += bytes.fromhex("ffff00200022002400260028002affff")
    code += bytes.fromhex("41faffee2c7800044eaeffac4e75")
    code += b"\x00" * (0x50 - len(code))
    code += bytes.fromhex("4e754e754e754e754e754e75")
    code += b"test.device\x00"
    binary_path = tmp_path / "resident_non_autoinit_vectors.exe"
    metadata_path = tmp_path / "target_metadata.json"
    binary_path.write_bytes(make_synthetic_hunkexe(code_data=bytes(code)))
    metadata_path.write_text(
        json.dumps(
            {
                "target_type": "device",
                "resident": {
                    "name": "test.device",
                    "version": 1,
                    "offset": 0,
                    "hunk": 0,
                    "init_offset": 0x40,
                    "autoinit": None,
                },
            }
        ),
        encoding="utf-8",
    )
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "analysis.json",
    )

    rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)

    assert "resident_vectors:\n\tdc.b $FF,$FF\n\tdc.w $0020" in rendered
    assert "test_device_lib_open:\n\trts" in rendered
    assert "test_device_lib_close:\n\trts" in rendered
    assert "test_device_lib_expunge:\n\trts" in rendered
    assert "test_device_lib_extfunc:\n\trts" in rendered
    assert "test_device_dev_beginio:\n\trts" in rendered
    assert "test_device_dev_abortio:\n\trts" in rendered
    assert "\tdc.b $4E,$75,$4E,$75,$4E,$75" not in rendered
    assert "    ORG $" not in rendered


@pytest.mark.parametrize(
    ("target_name", "prefix"),
    [
        (
            "amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_devs__parallel.device_0b71ffaa",
            "parallel_device",
        ),
        (
            "amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_devs__printer.device_1aada1d4",
            "printer_device",
        ),
        (
            "amiga_disk_starglider-1987-rainbird__amiga_hunk_devs__serial.device_ddfdac2b",
            "serial_device",
        ),
    ],
)
def test_real_dll_non_autoinit_resident_vectors_seed_device_entrypoints(target_name: str, prefix: str) -> None:
    _requires_c_backend_dlls()
    paths = _requires_project_paths(target_name)

    rendered = render_project_source_with_c_backend(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert "resident_vectors:" in rendered
    assert f"{prefix}_lib_open:" in rendered
    assert f"{prefix}_lib_close:" in rendered
    assert f"{prefix}_lib_expunge:" in rendered
    assert f"{prefix}_lib_extfunc:" in rendered
    assert f"{prefix}_dev_beginio:" in rendered
    assert f"{prefix}_dev_abortio:" in rendered
    assert "    ORG $4\n" not in rendered


def test_symbolic_zero_address_displacement_preserves_instruction_width(tmp_path: Path) -> None:
    assembler = PROJECT_ROOT / "src" / "build" / "m68k_assembler_app.exe"
    inspector = PROJECT_ROOT / "src" / "build" / "platform_file_cli.exe"
    if not assembler.exists() or not inspector.exists():
        pytest.skip("C backend tools are missing; run cmd /c src\\build.bat")
    source_path = tmp_path / "symbolic_zero_displacement.s"
    rebuilt_path = tmp_path / "symbolic_zero_displacement.hunk"
    source_path.write_text(
        "\n".join(
            [
                "    SECTION section_0,code",
                "app_0000 EQU 0",
                "loc_0_00000000:",
                "    dc.w $0000",
                "    move.l loc_0_00000000(a0),d0",
                "    move.w app_0000(a6),d5",
                "    dc.w $0000",
                "",
            ]
        ),
        encoding="ascii",
    )

    result = subprocess.run(
        [
            str(assembler),
            "assemble-platform-file",
            "--cpu",
            "any",
            "--backend",
            "amiga-hunk",
            "--include-dir",
            str(PROJECT_ROOT / "include"),
            str(source_path),
            str(rebuilt_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    inspect_result = subprocess.run(
        [str(inspector), "inspect-file", "amiga-hunk", str(rebuilt_path)],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert inspect_result.returncode == 0, inspect_result.stderr
    section = json.loads(inspect_result.stdout)["sections"][0]
    assert section["data_size"] == 12
    assert section["data_hex"] == "0000202800003a2e00000000"


def test_real_dll_extract_disk_entry_reports_c_error() -> None:
    _requires_c_backend_dlls()
    disk_path = PROJECT_ROOT / "bin" / "Search for the King, The (1991)(Accolade)(Disk 1 of 5).adf"

    with pytest.raises(RuntimeError, match="C disk backend DLL failed:"):
        extract_disk_entry_with_c_backend(disk_path, "missing/file")
