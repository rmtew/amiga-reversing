from __future__ import annotations

import ctypes
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    DiskEntryBinarySource,
    HunkFileBinarySource,
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
    build_project_rows_generation_with_c_backend,
    build_project_rows_generation_with_c_backend_profile,
    build_project_rows_generation_with_c_backend_profile_text,
    decompress_packed_range_with_c_backend,
    decompress_packed_section_range_with_c_backend,
    extract_disk_entry_with_c_backend,
    facts_v2_asm_source_project_source_with_c_backend,
    facts_v2_asm_source_project_source_with_c_backend_profile,
    facts_v2_direct_rebuild_project_source_with_c_backend_profile,
    facts_v2_render_assemble_project_source_with_c_backend_profile,
    inspect_disk_with_c_backend,
    identify_packed_range_with_c_backend,
    render_binary_source_with_c_backend,
    render_project_source_with_c_backend,
    rows_from_c_listing_json,
    validate_amiga_hunk_executable_with_c_backend,
)
from amiga_reversing.disasm.facts_v2_source_refusal import FactsV2SourceRefused
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.listing_types import (
    AppSlotRef,
    BlockRowContext,
    CodeStartRef,
    HeaderRowContext,
    PlatformTypedAccess,
    PlatformUnresolvedTypedAccess,
    RuntimeAddressRef,
    SymbolOperandMetadata,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from src.tests._platform_backend_test_utils import (
    M68kDiagList,
    make_synthetic_atari_prg,
    make_synthetic_hunkexe,
    u32,
)


def _requires_c_backend_dlls() -> None:
    build_dir = PROJECT_ROOT / "src" / "build"
    if not (build_dir / "platform_file_lib.dll").exists() or not (build_dir / "platform_disk_lib.dll").exists():
        pytest.skip("C backend DLLs are missing; run cmd /c src\\build.bat")


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


def test_listing_analysis_json_includes_empty_decompression_fact_arrays(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary = tmp_path / "plain_hunk.bin"
    binary.write_bytes(_make_cross_section_call_hunkexe(bytes.fromhex("4e75"), 0))

    combined_text = c_backend._platform_file_text(
        "platform_file_facts_v2_listing_rows_with_analysis_path_json_alloc",
        "amiga-hunk",
        str(binary),
        "",
        "",
        project_root=PROJECT_ROOT,
    )
    combined = json.loads(combined_text)

    assert combined["analysis"]["packed_payloads"] == []
    assert combined["analysis"]["derived_target_suggestions"] == []


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
    paths = resolve_project_paths(target_name, project_root=PROJECT_ROOT, require_entities=False)
    with effective_metadata_file(paths.target_dir) as metadata_path:
        metadata_text = str(metadata_path) if metadata_path is not None else ""
        with c_backend._source_file_for_c_backend(paths.binary_source, project_root=PROJECT_ROOT) as source_file:
            include_dir = c_backend._platform_include_dir_for_listing(source_file.platform_name, PROJECT_ROOT)
            if source_file.entry_offset is None:
                combined_text = c_backend._platform_file_text(
                    "platform_file_facts_v2_listing_rows_with_analysis_path_json_alloc",
                    source_file.platform_name,
                    str(source_file.path),
                    metadata_text,
                    str(include_dir),
                    project_root=PROJECT_ROOT,
                )
            else:
                combined_text = c_backend._platform_file_text(
                    "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
                    source_file.platform_name,
                    str(source_file.path),
                    source_file.entry_offset,
                    metadata_text,
                    str(include_dir),
                    project_root=PROJECT_ROOT,
                )
    payload = json.loads(combined_text)
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
        ("label", ctypes.c_char * 64),
        ("struct_name", ctypes.c_char * 64),
        ("field_name", ctypes.c_char * 64),
        ("field_type", ctypes.c_char * 64),
        ("c_type", ctypes.c_char * 64),
        ("pointer_struct", ctypes.c_char * 64),
        ("value_domain", ctypes.c_char * 64),
        ("constant_name", ctypes.c_char * 64),
        ("semantic_role", ctypes.c_char * 64),
        ("comment", ctypes.c_char * 64),
    ]


class _M68kAnalysisNamedLabel(ctypes.Structure):
    _fields_ = [
        ("has_section_index", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
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


class _M68kAnalysisAppSlotRegion(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_uint32),
        ("size", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("symbol", ctypes.c_char * 64),
        ("struct_name", ctypes.c_char * 64),
        ("pointer_struct", ctypes.c_char * 64),
        ("storage_kind", ctypes.c_char * 32),
        ("semantic_type", ctypes.c_char * 64),
    ]


class _M68kAnalysisPolicy(ctypes.Structure):
    _fields_ = [
        ("max_cpu", ctypes.c_uint8),
        ("has_entry_offset", ctypes.c_uint8),
        ("reserved0", ctypes.c_uint8 * 2),
        ("register_seed_count", ctypes.c_uint16),
        ("entry_point_count", ctypes.c_uint16),
        ("structured_data_item_count", ctypes.c_uint16),
        ("named_label_count", ctypes.c_uint16),
        ("entry_comment_count", ctypes.c_uint16),
        ("runtime_range_count", ctypes.c_uint16),
        ("runtime_entry_point_count", ctypes.c_uint16),
        ("app_slot_region_count", ctypes.c_uint16),
        ("entry_offset", ctypes.c_uint32),
        ("register_seeds", _M68kAnalysisRegisterSeed * 64),
        ("entry_points", _M68kAnalysisEntryPoint * 64),
        ("structured_data_items", _M68kAnalysisStructuredDataItem * 256),
        ("named_labels", _M68kAnalysisNamedLabel * 128),
        ("entry_comments", _M68kAnalysisEntryComment * 128),
        ("runtime_ranges", _M68kAnalysisRuntimeRange * 64),
        ("runtime_entry_points", _M68kAnalysisRuntimeEntryPoint * 64),
        ("app_slot_regions", _M68kAnalysisAppSlotRegion * 128),
    ]


def test_rows_from_c_listing_json_uses_emitted_metadata() -> None:
    rows = rows_from_c_listing_json(
        {
            "rows": [
                {
                    "row_id": "c:0",
                    "kind": "directive",
                    "text": "    SECTION section,code\n",
                    "addr": None,
                    "label": None,
                    "opcode_or_directive": "SECTION",
                    "operand_text": "section,code",
                    "comment_text": "",
                    "source_context": {"section": "c-backend"},
                },
                {
                    "row_id": "c:1",
                    "kind": "instruction",
                    "text": "    jsr target.l\n",
                    "stable_key": "s0:00000020:instruction:1",
                    "analysis_generation": "basic",
                    "analysis_phase": "entrypoint-code",
                    "section_index": 0,
                    "start_offset": 32,
                    "end_offset": 38,
                    "addr": 32,
                    "entity_addr": 32,
                    "bytes": "4eb900000040",
                    "label": None,
                    "opcode_or_directive": "jsr",
                    "operand_text": "target.l",
                    "operand_parts": [
                        {
                            "kind": "symbol",
                            "text": "target",
                            "value": None,
                            "register": None,
                            "base_register": None,
                            "displacement": None,
                            "segment_addr": None,
                            "metadata": {"symbol": "target"},
                        }
                    ],
                    "comment_text": "",
                    "data_class": "copper_list",
                    "source_context": {"kind": "c-instruction", "hunk_index": 0},
                    "app_slot_refs": [
                        {
                            "symbol": "app_0234",
                            "displacement": 0x0234,
                            "base_register": "A6",
                            "operand_index": 0,
                            "access": "read",
                        }
                    ],
                    "runtime_address_refs": [
                        {
                            "offset": 32,
                            "operand_index": None,
                            "target_section_index": 0,
                            "target_offset": 0x40,
                            "runtime_address": 0x40040,
                            "confidence": 2,
                            "data_class": "copper_list",
                        }
                    ],
                    "code_start_refs": [
                        {
                            "offset": 32,
                            "reason": 4,
                            "reason_name": "control_target",
                            "confidence": 2,
                            "source_section_index": 0,
                            "source_offset": 16,
                            "runtime_address": None,
                            "size": 6,
                        }
                    ],
                    "typed_accesses": [
                        {
                            "operand_index": 0,
                            "base_register": "A0",
                            "displacement": 20,
                            "field_offset": 20,
                            "root_struct_name": "Library",
                            "owner_struct_name": "Library",
                            "field_name": "LIB_VERSION",
                            "field_expr": "LIB_VERSION",
                            "inherited": False,
                            "nested": False,
                        }
                    ],
                    "unresolved_typed_accesses": [
                        {
                            "operand_index": 1,
                            "base_register": "A0",
                            "displacement": 36,
                            "struct_size": 34,
                            "root_struct_name": "InputEvent",
                            "classification": "prefix_extension",
                            "container_candidate_count": 3,
                            "container_struct_name": "SyntheticEvent",
                            "container_field_expr": "se_Field",
                            "refinement_applied": True,
                            "refined_struct_name": "SyntheticEvent",
                            "type_provenance_kind": "api_output",
                            "type_provenance_section": 0,
                            "type_provenance_offset": 32,
                        }
                    ],
                    "structured_data": {
                        "struct_name": "RT",
                        "field_name": "RT_MATCHWORD",
                        "c_type": "UWORD",
                        "value_domain": "exec.resident.matchword",
                        "constant_name": "RTC_MATCHWORD",
                    },
                },
            ]
        }
    )

    assert rows[0].source_context == HeaderRowContext(section="c-backend")
    assert rows[1].addr == 32
    assert rows[1].entity_addr == 32
    assert rows[1].stable_key == "s0:00000020:instruction:1"
    assert rows[1].analysis_generation == "basic"
    assert rows[1].analysis_phase == "entrypoint-code"
    assert rows[1].section_index == 0
    assert rows[1].start_offset == 32
    assert rows[1].end_offset == 38
    assert rows[1].opcode_or_directive == "jsr"
    assert rows[1].bytes == bytes.fromhex("4eb900000040")
    assert rows[1].operand_parts[0].kind == "symbol"
    assert rows[1].operand_parts[0].text == "target"
    assert rows[1].operand_parts[0].metadata == SymbolOperandMetadata(symbol="target")
    assert rows[1].source_context == BlockRowContext(kind="c-instruction", hunk_index=0)
    assert rows[1].data_class == "copper_list"
    assert rows[1].app_slot_refs == (AppSlotRef("app_0234", 0x0234, "A6", 0, "read"),)
    assert rows[1].runtime_address_refs == (
        RuntimeAddressRef(
            offset=32,
            operand_index=None,
            target_section_index=0,
            target_offset=0x40,
            runtime_address=0x40040,
            confidence=2,
            data_class="copper_list",
        ),
    )
    assert rows[1].code_start_refs == (
        CodeStartRef(
            offset=32,
            reason=4,
            reason_name="control_target",
            confidence=2,
            source_section_index=0,
            source_offset=16,
            runtime_address=None,
            size=6,
        ),
    )
    assert rows[1].typed_accesses == (
        PlatformTypedAccess(
            operand_index=0,
            base_register="A0",
            displacement=20,
            field_offset=20,
            root_struct_name="Library",
            owner_struct_name="Library",
            field_name="LIB_VERSION",
            field_expr="LIB_VERSION",
            inherited=False,
            nested=False,
        ),
    )
    assert rows[1].unresolved_typed_accesses == (
        PlatformUnresolvedTypedAccess(
            operand_index=1,
            base_register="A0",
            displacement=36,
            struct_size=34,
            root_struct_name="InputEvent",
            classification="prefix_extension",
            container_candidate_count=3,
            container_struct_name="SyntheticEvent",
            container_field_expr="se_Field",
            refinement_applied=True,
            refined_struct_name="SyntheticEvent",
            type_provenance_kind="api_output",
            type_provenance_section=0,
            type_provenance_offset=32,
        ),
    )
    assert rows[1].structured_data == {
        "struct_name": "RT",
        "field_name": "RT_MATCHWORD",
        "c_type": "UWORD",
        "value_domain": "exec.resident.matchword",
        "constant_name": "RTC_MATCHWORD",
    }


def test_full_listing_data_rows_expose_source_bytes(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(b"\0" * 12 + b"\x4e\x75" + b"ABC\0")

    payload = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(path),
            12,
            "",
            "",
            project_root=PROJECT_ROOT,
        )
    )["listing"]
    rows = rows_from_c_listing_json(payload)
    data_rows = [row for row in rows if row.kind == "data"]

    assert any(row.addr == 0 and row.bytes == b"\0" * 12 for row in data_rows)
    assert any(row.addr == 14 and row.bytes == b"ABC\0" for row in data_rows)


def test_full_listing_rows_omit_empty_optional_c_fields(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(b"\x4e\x75")

    payload = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(path),
            0,
            "",
            "",
            project_root=PROJECT_ROOT,
        )
    )["listing"]
    raw_rows = payload["rows"]
    hydrated_rows = rows_from_c_listing_json(payload)
    label = next(row for row in raw_rows if row["kind"] == "label")
    hydrated_label = next(row for row in hydrated_rows if row.kind == "label")
    instruction = next(row for row in raw_rows if row["kind"] == "instruction")
    hydrated_instruction = next(row for row in hydrated_rows if row.kind == "instruction")

    assert label["addr"] == 0
    assert label["entity_addr"] == 0
    assert "bytes" not in label
    assert hydrated_label.addr == 0
    assert hydrated_label.entity_addr == 0
    assert hydrated_label.bytes is None
    assert "app_slot_refs" not in instruction
    assert "typed_accesses" not in instruction
    assert "unresolved_typed_accesses" not in instruction
    assert "comment_text" not in instruction
    assert hydrated_instruction.app_slot_refs == ()
    assert hydrated_instruction.typed_accesses == ()
    assert hydrated_instruction.unresolved_typed_accesses == ()
    assert hydrated_instruction.comment_text == ""


def test_full_listing_instruction_rows_expose_symbol_operand_parts(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    path = tmp_path / "raw.bin"
    path.write_bytes(bytes.fromhex("60024e754e75"))

    payload = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(path),
            0,
            "",
            "",
            project_root=PROJECT_ROOT,
        )
    )["listing"]
    rows = rows_from_c_listing_json(payload)
    branch = next(row for row in rows if row.kind == "instruction" and row.addr == 0)

    assert branch.operand_text == "loc_0_00000004"
    assert branch.operand_parts[0].kind == "symbol"
    assert branch.operand_parts[0].text == "loc_0_00000004"
    assert branch.operand_parts[0].metadata == SymbolOperandMetadata(symbol="loc_0_00000004")


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

    combined = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_and_text_raw_path_json_alloc",
            "amiga-raw",
            str(path),
            0,
            str(metadata_path),
            "",
            project_root=PROJECT_ROOT,
        )
    )
    source_text = combined["source_text"]
    assert "\tlea.l loc_0_00000020(pc),a0\n" in source_text
    assert "\tjmp $00000080.l\n" in source_text
    assert "loc_0_00000020:\n    ORG $100\nabs_0_00000100:\n" in source_text
    assert "    ORG $20\n" not in source_text
    assert "    ORG $80\n" not in source_text
    assert "src_0_" not in source_text
    assert "loc_0_00000020 EQU" not in source_text
    facts_v2 = combined["profile"]["facts_v2"]
    assert facts_v2["asm_source_numeric_runtime_refs"] == 1
    assert facts_v2["asm_source_first_numeric_runtime_ref_offset"] == 4
    assert facts_v2["asm_source_first_numeric_runtime_ref_target_offset"] == 0x10
    assert facts_v2["asm_source_first_numeric_runtime_ref_runtime_address"] == 0x80
    runtime_views = combined["analysis"]["sections"][0]["runtime_views"]
    assert runtime_views == [
        {
            "runtime_view_id": 0,
            "storage_address": 0x10,
            "storage_offset": 0x10,
            "size": 0x10,
            "runtime_address": 0x80,
            "kind": 1,
            "confidence": 3,
        },
        {
            "runtime_view_id": 1,
            "storage_address": 0x20,
            "storage_offset": 0x20,
            "size": 0x04,
            "runtime_address": 0x100,
            "kind": 1,
            "confidence": 3,
        },
    ]

    rows = rows_from_c_listing_json(combined["listing"])
    row_texts = [row.text.rstrip("\n") for row in rows]
    ref_index = next(index for index, text in enumerate(row_texts) if "lea.l loc_0_00000020(pc),a0" in text)
    storage_label_index = row_texts.index("loc_0_00000020:")
    org_index = row_texts.index("    ORG $100")
    runtime_label_index = row_texts.index("abs_0_00000100:")
    assert ref_index < storage_label_index < org_index < runtime_label_index
    storage_row = rows[storage_label_index]
    runtime_row = rows[runtime_label_index]
    assert storage_row.storage_address == 0x20
    assert storage_row.runtime_address == 0x100
    assert storage_row.runtime_view_id == 1
    assert runtime_row.storage_address == 0x20
    assert runtime_row.runtime_address == 0x100
    assert runtime_row.runtime_view_id == 1


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

    combined = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_and_text_path_json_alloc",
            "amiga-hunk",
            str(path),
            "",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            project_root=PROJECT_ROOT,
        )
    )
    source_text = combined["source_text"]
    facts_v2 = combined["profile"]["facts_v2"]
    stub_rows = [
        row
        for row in combined["listing"]["rows"]
        if row.get("kind") == "instruction" and row.get("opcode_or_directive") == "rts"
    ]

    assert facts_v2["asm_source_refused"] is False
    assert facts_v2["runtime_address_ranges"] >= 1
    assert "\tdc.b $73,$6B,$69,$70\n" in source_text
    assert "    ORG $100\nabs_0_00000100:\n\trts\n" in source_text
    assert "    ORG $18\n\tdc.b $74,$61,$69,$6C\n" in source_text
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

    combined = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_and_text_path_json_alloc",
            "amiga-hunk",
            str(path),
            "",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            project_root=PROJECT_ROOT,
        )
    )

    source_text = combined["source_text"]
    sites = combined["analysis"]["sections"][0]["recovered_indirect_sites"]
    payload_rows = [
        row
        for row in combined["listing"]["rows"]
        if row.get("section_index") == 0 and row.get("start_offset") == 0x18
    ]

    assert "\tdc.b $73,$6B,$69,$70\nloc_0_00000018:\n\tmoveq.l #2,d0\n\trts\n" in source_text
    assert not any(site["status"] == "unresolved" for site in sites)
    assert sites == [
        {
            "offset": 0x12,
            "flow": "jump",
            "shape": "ind",
            "status": "backward_slice",
            "detail": "accepted traced indirect control target",
            "target": 0x18,
            "target_count": 1,
        }
    ]
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
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_path_json_alloc",
            "amiga-hunk",
            str(path),
            str(metadata_path),
            "",
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

    source = render_binary_source_with_c_backend(path, syntax="genam")
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
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "mathtrans.analysis",
    )
    source = render_project_source_with_c_backend(binary_source, syntax="genam", metadata_path=metadata_path)
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

    source = render_binary_source_with_c_backend(path, syntax="genam")
    source_path.write_text(source, encoding="ascii")

    assert "jsr loc_1_00000004(pc)" in source
    assert "loc_1_00000004:" in source
    assert "dc.b $00,$00" in source.lower()
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

    def fake_render_project_source(source, *, syntax: str, project_root: Path) -> str:
        calls.append(
            {
                "source": source,
                "syntax": syntax,
                "project_root": project_root,
            }
        )
        return "SECTION section_0,code\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend.render_project_source_with_c_backend", fake_render_project_source)

    assert (
        render_binary_source_with_c_backend(
            binary_path,
            syntax="genam",
            project_root=tmp_path,
        )
        == "SECTION section_0,code\n"
    )
    assert calls[0]["syntax"] == "genam"
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
        kind="disk_entry",
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


def test_render_project_source_disk_entry_uses_atari_platform(monkeypatch, tmp_path: Path) -> None:
    source = DiskEntryBinarySource(
        kind="disk_entry",
        disk_id="demo",
        adf_path=tmp_path / "demo.st",
        entry_path="AUTO/BOOT.PRG",
        display_path="demo.st::AUTO/BOOT.PRG",
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend._platform_disk_bytes", lambda function_name, *args, project_root: b"\x60\x1a"
    )

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return "; atari\n", {"facts_v2": {"asm_source_refused": False}}

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_facts_v2_source_text_profile", fake_file_run)

    assert (
        render_project_source_with_c_backend(
            source,
            project_root=tmp_path,
        )
        == "; atari\n"
    )
    assert calls[0][0:2] == ("platform_file_facts_v2_asm_source_path_text_profile_alloc", "atari-st")


def test_render_project_source_ttp_uses_atari_platform(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "BIN_GEN.TTP"
    binary_path.write_bytes(b"\x60\x1a")
    source = HunkFileBinarySource(
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return "; atari\n", {"facts_v2": {"asm_source_refused": False}}

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_facts_v2_source_text_profile", fake_file_run)

    assert (
        render_project_source_with_c_backend(
            source,
            project_root=tmp_path,
        )
        == "; atari\n"
    )
    assert calls[0][0:2] == ("platform_file_facts_v2_asm_source_path_text_profile_alloc", "atari-st")


def test_render_project_source_uses_facts_v2(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "demo"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = HunkFileBinarySource(
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_facts_v2(*args: object, **kwargs: object) -> tuple[str, dict[str, object]]:
        calls.append((*args, kwargs))
        return "SECTION section_0,code\n", {"facts_v2": {"asm_source_refused": False}}

    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend.facts_v2_asm_source_project_source_with_c_backend_profile",
        fake_facts_v2,
    )

    assert (
        render_project_source_with_c_backend(
            source,
            project_root=tmp_path,
        )
        == "SECTION section_0,code\n"
    )
    assert calls[0][0] == source


def test_render_project_source_refuses_facts_v2_backend(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "demo"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = HunkFileBinarySource(
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend.facts_v2_asm_source_project_source_with_c_backend_profile",
        lambda *args, **kwargs: (
            "",
            {
                "facts_v2": {
                    "asm_source_refused": True,
                    "asm_source_first_failure_kind": "unresolved_label",
                    "asm_source_first_failure_section": 1,
                    "asm_source_first_failure_offset": 8,
                }
            },
        ),
    )

    with pytest.raises(FactsV2SourceRefused, match="kind=unresolved_label"):
        render_project_source_with_c_backend(
            source,
            project_root=tmp_path,
        )


def test_project_source_raw_binary_uses_raw_dll_with_local_entrypoint(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return '{"sections":[]}' if function_name == "platform_file_facts_v2_analysis_raw_path_json_alloc" else "; raw\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    assert analyze_project_source_with_c_backend(source, project_root=tmp_path) == {"sections": []}
    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend._platform_file_facts_v2_source_text_profile",
        lambda function_name, *args, project_root: ("; raw\n", {"facts_v2": {"asm_source_refused": False}}),
    )

    assert render_project_source_with_c_backend(source, project_root=tmp_path) == "; raw\n"
    assert calls == [
        ("platform_file_facts_v2_analysis_raw_path_json_alloc", "amiga-raw", str(binary_path), 12, "", ""),
    ]


def test_project_source_runtime_absolute_raw_binary_uses_local_entry_offset(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    binary_path = tmp_path / "decompressed.bin"
    binary_path.write_bytes(b"\x4e\xf9\x00\x00\x9b\x3a")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="runtime_absolute",
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
        ("platform_file_facts_v2_analysis_raw_path_json_alloc", "amiga-raw", str(binary_path), 0, "", ""),
    ]


def test_project_source_benchmark_uses_facts_v2(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    binary_path = tmp_path / "demo"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root: Path) -> tuple[str, dict[str, object]]:
        calls.append((function_name, *args))
        return "SECTION code,code\n", {
            "generation": "facts_v2_asm_source",
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
            "timing": {"total_seconds": 0.125},
        }

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_facts_v2_source_text_profile", fake_file_run)

    benchmark, text = benchmark_project_source_with_text_from_c_backend(
        source,
        syntax="genam",
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
            "total_seconds": 0.125,
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
        (
            "platform_file_facts_v2_asm_source_raw_path_text_profile_alloc",
            "amiga-raw",
            str(binary_path),
            12,
            "",
        ),
    ]


def test_project_source_facts_v2_asm_source_uses_dedicated_c_api(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return "    SECTION section,code\nloc_0_0000000C:\n\trts\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    text = facts_v2_asm_source_project_source_with_c_backend(source, project_root=tmp_path)

    assert text.startswith("    SECTION ")
    assert calls == [
        ("platform_file_facts_v2_asm_source_raw_path_text_alloc", "amiga-raw", str(binary_path), 12, ""),
    ]


def test_project_source_runtime_absolute_raw_binary_passes_local_entry_offset(
    monkeypatch, tmp_path: Path
) -> None:
    binary_path = tmp_path / "stage.bin"
    binary_path.write_bytes(b"\x4e\x75")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="runtime_absolute",
        load_address=0x400,
        entrypoint=0x400,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return "    SECTION section,code\nloc_0_00000000:\n\trts\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    facts_v2_asm_source_project_source_with_c_backend(source, project_root=tmp_path)

    assert calls == [
        ("platform_file_facts_v2_asm_source_raw_path_text_alloc", "amiga-raw", str(binary_path), 0, ""),
    ]


def test_project_source_facts_v2_asm_source_profile_uses_fast_c_api(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return "    SECTION section,code\nloc_0_0000000C:\n\trts\n", {
            "generation": "facts_v2_asm_source",
            "analysis_backend": "facts_v2",
            "facts_v2": {"asm_source_symbolic_instructions": 1},
        }

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_facts_v2_source_text_profile", fake_file_run)

    text, profile = facts_v2_asm_source_project_source_with_c_backend_profile(source, project_root=tmp_path)

    assert text.startswith("    SECTION ")
    assert profile["generation"] == "facts_v2_asm_source"
    assert profile["facts_v2"] == {"asm_source_symbolic_instructions": 1}
    assert calls == [
        ("platform_file_facts_v2_asm_source_raw_path_text_profile_alloc", "amiga-raw", str(binary_path), 12, ""),
    ]


def test_project_source_facts_v2_render_assemble_uses_combined_c_api(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "boot.bin"
    output_path = tmp_path / "rebuilt.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return (
            b"\x4e\x75",
            {"generation": "facts_v2_asm_source", "facts_v2": {"asm_source_refused": False}},
            {"assemble_c_api": True, "total_seconds": 0.01},
        )

    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend._platform_file_facts_v2_render_assemble_profile",
        fake_file_run,
    )

    rebuilt, source_profile, assembler_profile = facts_v2_render_assemble_project_source_with_c_backend_profile(
        source,
        output_path=output_path,
        include_dir=tmp_path / "include",
        project_root=tmp_path,
    )

    assert rebuilt == b"\x4e\x75"
    assert source_profile["generation"] == "facts_v2_asm_source"
    assert assembler_profile["assemble_c_api"] is True
    assert calls == [
        (
            "platform_file_facts_v2_render_assemble_raw_path_bytes_profile_alloc",
            "amiga-raw",
            str(binary_path),
            12,
            "",
            str(tmp_path / "include"),
            str(output_path),
            "any",
            0,
        ),
    ]


def test_real_dll_raw_render_assemble_returns_raw_payload(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "raw.bin"
    output_path = tmp_path / "rebuilt.bin"
    binary_path.write_bytes(b"\x4E\x75")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="runtime_absolute",
        load_address=0x4000,
        entrypoint=0x4000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rebuilt, source_profile, assembler_profile = facts_v2_render_assemble_project_source_with_c_backend_profile(
        source,
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
        kind="hunk_file",
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


def test_project_source_facts_v2_direct_rebuild_compare_uses_compare_c_api(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "sample"
    output_path = tmp_path / "rebuilt.bin"
    binary_path.write_bytes(b"\0\0\x03\xf3")
    source = HunkFileBinarySource(
        kind="hunk_file",
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
        kind="hunk_file",
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


def test_project_source_facts_v2_direct_rebuild_disk_entry_uses_buffer_c_api(
    monkeypatch, tmp_path: Path
) -> None:
    disk_path = tmp_path / "demo.adf"
    output_path = tmp_path / "rebuilt.bin"
    disk_path.write_bytes(b"disk")
    source = DiskEntryBinarySource(
        kind="disk_entry",
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
        kind="hunk_file",
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


def test_project_source_facts_v2_asm_source_profile_blanks_refused_source(
    monkeypatch, tmp_path: Path
) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    def fake_file_run(function_name: str, *args: object, project_root):
        return "    SECTION section,code\n\tbad.partial\n", {
            "generation": "facts_v2_asm_source",
            "analysis_backend": "facts_v2",
            "facts_v2": {
                "asm_source_refused": True,
                "asm_source_instruction_relocation_failures": 1,
            },
        }

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_facts_v2_source_text_profile", fake_file_run)

    text, profile = facts_v2_asm_source_project_source_with_c_backend_profile(source, project_root=tmp_path)
    facts_v2 = profile["facts_v2"]

    assert text == ""
    assert isinstance(facts_v2, dict)
    assert facts_v2["asm_source_refused"] is True


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
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "private_lvo.analysis",
    )

    text, profile = facts_v2_asm_source_project_source_with_c_backend_profile(
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
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    text, profile = facts_v2_asm_source_project_source_with_c_backend_profile(source, project_root=PROJECT_ROOT)

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
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    text, profile = facts_v2_asm_source_project_source_with_c_backend_profile(source, project_root=PROJECT_ROOT)
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
    symbol_table = bytes((index & 0xFF for index in range(300)))
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
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    text, profile = facts_v2_asm_source_project_source_with_c_backend_profile(source, project_root=PROJECT_ROOT)
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


def test_project_rows_facts_v2_uses_dedicated_listing_api(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    target_dir = tmp_path / "targets" / "raw_demo"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("", encoding="utf-8")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "path": str(binary_path),
                "address_model": "local_offset",
                "load_address": 0x70000,
                "entrypoint": 0x7000C,
                "code_start_offset": 0x0C,
            }
        ),
        encoding="utf-8",
    )
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root: Path) -> str:
        calls.append((function_name, *args))
        return json.dumps(
            {
                "listing": {"rows": []},
                "analysis": {"sections": []},
                "profile": {
                    "generation": "facts_v2_listing",
                    "analysis_backend": "facts_v2",
                    "facts_v2": {"asm_source_refused": False},
                },
            }
        )

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    rows, api_calls = build_project_rows_generation_with_c_backend(
        "raw_demo",
        generation="full",
        project_root=tmp_path,
    )

    assert rows == []
    assert api_calls == {}
    assert calls == [
        (
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            12,
            "",
            str(tmp_path / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
        )
    ]


def test_project_rows_facts_v2_profile_text_returns_source(monkeypatch, tmp_path: Path) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    target_dir = tmp_path / "targets" / "raw_demo"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("", encoding="utf-8")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "path": str(binary_path),
                "address_model": "local_offset",
                "load_address": 0x70000,
                "entrypoint": 0x7000C,
                "code_start_offset": 0x0C,
            }
        ),
        encoding="utf-8",
    )

    def fake_file_run(function_name: str, *args: object, project_root: Path) -> str:
        return json.dumps(
            {
                "listing": {"rows": [{"row_id": "r0", "kind": "directive", "text": "SECTION code,code\n"}]},
                "analysis": {"sections": []},
                "source_text": "SECTION code,code\n",
                "profile": {"generation": "facts_v2_listing", "analysis_backend": "facts_v2"},
            }
        )

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    rows, api_calls, profile, source_text = build_project_rows_generation_with_c_backend_profile_text(
        "raw_demo",
        generation="full",
        project_root=tmp_path,
    )

    assert [row.text for row in rows] == ["SECTION code,code\n"]
    assert api_calls == {}
    assert profile["analysis_backend"] == "facts_v2"
    assert source_text == "SECTION code,code\n"


def test_project_rows_basic_generation_uses_facts_v2_listing_api(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    target_dir = tmp_path / "targets" / "raw_demo"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("", encoding="utf-8")
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
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root: Path) -> str:
        calls.append((function_name, *args))
        return json.dumps(
            {
                "listing": {
                    "rows": [
                        {
                            "row_id": "f:0",
                            "kind": "directive",
                            "text": "    SECTION section,code\n",
                            "analysis_generation": "basic",
                        }
                    ]
                },
                "analysis": {},
                "source_text": "    SECTION section,code\n",
                "profile": {"generation": "facts_v2_basic_listing", "analysis_backend": "facts_v2"},
            }
        )

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    rows, api_calls, profile = build_project_rows_generation_with_c_backend_profile(
        "raw_demo",
        generation="basic",
        project_root=tmp_path,
    )

    assert [row.text for row in rows] == ["    SECTION section,code\n"]
    assert api_calls == {}
    assert profile["generation"] == "facts_v2_basic_listing"
    assert profile["analysis_backend"] == "facts_v2"
    assert calls == [
        (
            "platform_file_facts_v2_basic_listing_rows_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            "",
            str(tmp_path / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
        )
    ]


def test_project_rows_basic_generation_with_profile_text_stays_basic(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    target_dir = tmp_path / "targets" / "raw_demo"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("", encoding="utf-8")
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
    calls: list[tuple[object, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root: Path) -> str:
        calls.append((function_name, *args))
        return json.dumps(
            {
                "listing": {
                    "rows": [
                        {
                            "row_id": "f:0",
                            "kind": "directive",
                            "text": "    SECTION section,code\n",
                            "analysis_generation": "basic",
                        }
                    ]
                },
                "analysis": {},
                "profile": {"generation": "facts_v2_basic_listing", "analysis_backend": "facts_v2"},
            }
        )

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    rows, api_calls, profile, source_text = build_project_rows_generation_with_c_backend_profile_text(
        "raw_demo",
        generation="basic",
        project_root=tmp_path,
    )

    assert [row.text for row in rows] == ["    SECTION section,code\n"]
    assert api_calls == {}
    assert profile["generation"] == "facts_v2_basic_listing"
    assert source_text is None
    assert calls == [
        (
            "platform_file_facts_v2_basic_listing_rows_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            "",
            str(tmp_path / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
        )
    ]


def test_real_dll_facts_v2_listing_rows_parse_sectioned_source(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rows, api_calls, profile, source_text = c_backend._build_project_rows_generation_from_source(
        source,
        metadata_text="",
        generation="full",
        syntax="canonical",
        include_source_text=True,
        project_root=PROJECT_ROOT,
    )

    assert api_calls == {}
    assert profile["generation"] == "facts_v2_listing"
    assert profile["analysis_backend"] == "facts_v2"
    assert isinstance(source_text, str) and source_text.lstrip().startswith("SECTION ")
    assert any(row.kind == "directive" and row.text.lstrip().startswith("SECTION ") for row in rows)
    assert any(row.kind == "instruction" and row.opcode_or_directive == "rts" and row.bytes == b"\x4e\x75" for row in rows)


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
                "app_slot_regions": [],
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

    source = c_backend._platform_file_text(
        "platform_file_facts_v2_asm_source_raw_path_text_alloc",
        "amiga-raw",
        str(binary_path),
        0x410,
        str(metadata_path),
        project_root=PROJECT_ROOT,
    )

    assert "    ORG $400\nabs_0_00000400:\n\trts\n" in source
    assert "abs_0_00000410:\n\trts\n" in source
    assert "loc_0_00000010:" not in source


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
                "app_slot_regions": [],
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

    payload = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0x410,
            str(metadata_path),
            "",
            project_root=PROJECT_ROOT,
        )
    )["listing"]
    rows = rows_from_c_listing_json(payload)
    org_index = next(index for index, row in enumerate(rows) if row.text.strip() == "ORG $400")
    label_index = next(index for index, row in enumerate(rows) if row.label == "abs_0_00000400")

    assert rows[org_index].kind == "directive"
    assert rows[org_index].opcode_or_directive == "ORG"
    assert rows[org_index].operand_text == "$400"
    assert rows[org_index].addr is None
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

    payload = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            str(metadata_path),
            "",
            project_root=PROJECT_ROOT,
        )
    )["listing"]
    rows = rows_from_c_listing_json(payload)

    assert any(row.kind == "instruction" and row.start_offset == 0x3E for row in rows)
    assert any(row.kind == "instruction" and row.start_offset == 0x50 for row in rows)


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

    payload = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            str(metadata_path),
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            project_root=PROJECT_ROOT,
        )
    )["listing"]
    rows = rows_from_c_listing_json(payload)
    copper_rows = {row.addr: row for row in rows if row.kind == "data" and row.addr is not None}
    pointer_row = next(row for row in rows if row.addr == 0 and row.kind == "instruction")

    assert pointer_row.runtime_address_refs == (
        RuntimeAddressRef(
            offset=0,
            operand_index=0,
            target_section_index=0,
            target_offset=0x0C,
            runtime_address=0x0C,
            confidence=2,
            data_class="copper_list",
        ),
    )
    assert pointer_row.code_start_refs == (
            CodeStartRef(
                offset=0,
                reason=2,
                reason_name="policy_entry_offset",
            confidence=3,
            source_section_index=0,
            source_offset=0,
            runtime_address=None,
            size=10,
        ),
    )
    assert copper_rows[0x0C].data_class == "copper_list"
    assert copper_rows[0x10].data_class == "copper_list"
    assert copper_rows[0x10].structured_data is not None
    assert copper_rows[0x10].structured_data["semantic_role"] == "copper_list"
    assert (
        copper_rows[0x0C].text.strip()
        == "dc.w bplcon0,(4<<PLNCNTSHFT)|COLORON\t; display 4 bitplanes lores color"
    )
    assert copper_rows[0x10].text.strip() == "dc.w bplpt,bitmap_12345678_hi\t; bitmap pointer $12345678"
    assert copper_rows[0x14].text.strip() == "dc.w bplpt+$02,bitmap_12345678_lo"
    assert copper_rows[0x18].text.strip() == "dc.w sprpt+$1E,$0000"
    assert copper_rows[0x1C].text.strip() == "dc.w intreq,INTF_SETCLR|INTF_COPER"
    assert (
        copper_rows[0x20].text.strip()
        == "dc.w COPPER_WAIT|$2C06,$FFFE\t; copper wait v=$2C h=$06 mask $FFFE"
    )
    assert copper_rows[0x24].text.strip() == "dc.w $FFFF,$FFFE"

    analysis = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
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


def test_real_dll_facts_v2_basic_listing_rows_use_basic_api_without_source_directives(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "boot.bin"
    binary_path.write_bytes(b"\0" * 12 + b"\x4e\x75")
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rows, api_calls, profile, source_text = c_backend._build_project_rows_generation_from_source(
        source,
        metadata_text="",
        generation="basic",
        syntax="canonical",
        include_source_text=False,
        project_root=PROJECT_ROOT,
    )

    assert api_calls == {}
    assert profile["generation"] == "facts_v2_basic_listing"
    assert "source_ir_seconds" in profile["timing"]
    assert "render_seconds" not in profile["timing"]
    assert source_text is None
    assert rows
    assert all(row.analysis_generation == "basic" for row in rows)
    assert any(row.kind == "directive" and row.text.lstrip().startswith("SECTION ") for row in rows)
    assert not any(row.text.lstrip().startswith(("INCLUDE ", "COMMENT ")) for row in rows)
    assert any(row.kind == "data" and row.addr == 0 and row.bytes == b"\0" * 12 for row in rows)
    assert any(row.kind == "instruction" and row.opcode_or_directive == "rts" and row.bytes == b"\x4e\x75" for row in rows)


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
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x70000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rows, api_calls, profile, source_text = c_backend._build_project_rows_generation_from_source(
        source,
        metadata_text=str(metadata_path),
        generation="full",
        syntax="canonical",
        include_source_text=False,
        project_root=PROJECT_ROOT,
    )

    assert api_calls[(0, 6)]["function"] == "OpenLibrary"
    assert profile["generation"] == "facts_v2_listing"
    assert source_text is None
    assert rows
    first_label_index = next(index for index, row in enumerate(rows) if row.kind == "label")
    header_texts = [row.text.lstrip() for row in rows[:first_label_index]]
    section_header_index = next(index for index, text in enumerate(header_texts) if text.startswith("SECTION "))
    assert any(text.startswith("INCLUDE ") for text in header_texts[:section_header_index])
    assert rows[section_header_index - 1].kind == "blank"
    known_index = next(index for index, row in enumerate(rows) if row.text.lstrip().startswith("; KNOWN:"))
    assert known_index == first_label_index - 1
    assert all(row.addr is None for row in rows[:first_label_index])
    assert not any(row.text.lstrip().startswith("INCLUDE ") for row in rows[first_label_index:])
    assert any(row.kind == "instruction" and row.opcode_or_directive == "jsr" for row in rows)


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
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rows, api_calls, profile, source_text = c_backend._build_project_rows_generation_from_source(
        source,
        metadata_text=str(metadata_path),
        generation="full",
        syntax="canonical",
        include_source_text=True,
        project_root=PROJECT_ROOT,
    )

    assert any(row.kind == "instruction" and row.opcode_or_directive == "jsr" for row in rows)
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

    combined = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_and_text_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            12,
            str(metadata_path),
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            project_root=PROJECT_ROOT,
        )
    )
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
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )

    rows, api_calls, profile, source_text = c_backend._build_project_rows_generation_from_source(
        source,
        metadata_text=str(metadata_path),
        generation="full",
        syntax="canonical",
        include_source_text=True,
        project_root=PROJECT_ROOT,
    )

    assert profile["generation"] == "facts_v2_listing"
    assert api_calls[(0, 16)]["function"] == "FindResident"
    assert "boot_entry:" in source_text
    assert (
        "    ; KNOWN: base A6=exec.library:LIB; type A1=IOStdReq (open trackdisk.device):IO\n"
        "boot_entry:"
        in source_text
    )
    assert "\tlea.l abs_0_00070026(pc),a1\n" in source_text
    assert "\tjsr _LVOFindResident(a6)\n" in source_text
    assert "\tmovea.l RT_INIT(a0),a0\n" in source_text
    assert 'INCLUDE "exec/resident.i"' in source_text
    assert "abs_0_00070026:" in source_text
    assert '\tdc.b "dos.library",$00\n' in source_text
    assert "facts_v2 data bytes" not in source_text
    assert any(row.kind == "instruction" and "abs_0_00070026(pc)" in row.text for row in rows)
    assert any(row.kind == "label" and row.addr == 0x26 and row.text.strip() == "abs_0_00070026:" for row in rows)
    assert any(row.addr == 0 and row.data_class == "string" for row in rows)


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

    combined = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            "",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            project_root=PROJECT_ROOT,
        )
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

    combined = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            "",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            project_root=PROJECT_ROOT,
        )
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

    combined = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            "",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            project_root=PROJECT_ROOT,
        )
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

    combined = json.loads(
        c_backend._platform_file_text(
            "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            0,
            "",
            str(PROJECT_ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"),
            project_root=PROJECT_ROOT,
        )
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
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    calls: list[tuple[str, ...]] = []

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return '{"sections":[]}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)
    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend._platform_file_facts_v2_source_text_profile",
        lambda function_name, *args, project_root: (
            calls.append((function_name, *args)) or ("; raw\n", {"facts_v2": {"asm_source_refused": False}})
        ),
    )

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
            str(metadata_path),
            "",
        ),
        (
            "platform_file_facts_v2_asm_source_raw_path_text_profile_alloc",
            "amiga-raw",
            str(binary_path),
            12,
            str(metadata_path),
        ),
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
                "app_slot_regions": [
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
    assert generic_policy.app_slot_region_count == 0
    assert generic_policy.named_label_count == 1
    assert generic_policy.named_labels[0].offset == 0x24
    assert generic_policy.named_labels[0].name == b"stage_entry"

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
    assert amiga_policy.app_slot_region_count == 1
    assert amiga_policy.app_slot_regions[0].offset == 0x22C
    assert amiga_policy.app_slot_regions[0].symbol == b"app_startup_options_buffer"
    assert amiga_policy.app_slot_regions[0].storage_kind == b"pointer"
    assert amiga_policy.named_label_count > 0


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
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "biased_dispatch.analysis",
    )

    rendered, profile = facts_v2_asm_source_project_source_with_c_backend_profile(source, project_root=PROJECT_ROOT)
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


@pytest.mark.parametrize("target_name", ["amiga_hunk_genam", "amiga_hunk_monam302"])
def test_project_source_facts_v2_indexed_pointer_table_comparators_stay_clean(target_name: str) -> None:
    _requires_c_backend_dlls()
    _rows, _api_calls, profile = build_project_rows_generation_with_c_backend_profile(
        target_name,
        generation="full",
        project_root=PROJECT_ROOT,
    )

    facts_v2 = profile["facts_v2"]
    assert facts_v2["asm_source_refused"] is False
    assert facts_v2["required_instruction_failures"] == 0
    assert facts_v2["unsupported_instruction_demotes"] == 0
    assert facts_v2["interior_conflicts_unresolved"] == 0
    assert facts_v2["unresolved_labels"] == 0


def test_real_dll_renders_genam() -> None:
    _requires_c_backend_dlls()
    rendered = render_binary_source_with_c_backend(PROJECT_ROOT / "bin" / "GenAm", syntax="vasm")

    assert "SECTION" in rendered
    assert "move" in rendered.lower() or "jsr" in rendered.lower()
    assert "app_0234 RS." in rendered
    assert "app_0234(a6)" in rendered

    rows, _ = build_project_rows_generation_with_c_backend(
        "amiga_hunk_genam",
        generation="full",
        project_root=PROJECT_ROOT,
    )
    refs = [ref for row in rows for ref in row.app_slot_refs]
    symbols = {ref.symbol for ref in refs}
    fallback_symbols = [
        symbol
        for symbol in symbols
        if symbol.startswith("app_")
        and len(symbol) == 8
        and all(ch in "0123456789ABCDEF" for ch in symbol[4:])
    ]
    refs_by_text = {row.text.strip(): row.app_slot_refs for row in rows if row.app_slot_refs}

    assert len(refs) > 500
    assert len(fallback_symbols) > 100
    assert refs_by_text["move.l a7,app_0234(a6)"] == (
        AppSlotRef("app_0234", 0x0234, "A6", 1, "write"),
    )
    assert refs_by_text["subq.l #4,app_0234(a6)"] == (
        AppSlotRef("app_0234", 0x0234, "A6", 1, "read-write"),
    )


def test_real_dll_genam_profile_exposes_c_app_slot_analysis() -> None:
    _requires_c_backend_dlls()
    _rows, _api_calls, profile, source_text = build_project_rows_generation_with_c_backend_profile_text(
        "amiga_hunk_genam",
        generation="full",
        syntax="vasm",
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
    assert isinstance(source_text, str)
    assert "app_slot_analysis" not in source_text


def test_real_dll_bloodwych_detects_runtime_copy_loader() -> None:
    _requires_c_backend_dlls()
    rows, _, profile = build_project_rows_generation_with_c_backend_profile(
        "amiga_hunk_bloodwych",
        generation="full",
        project_root=PROJECT_ROOT,
    )

    assert profile["analysis_backend"] == "facts_v2"
    facts_v2 = profile["facts_v2"]
    assert facts_v2["asm_source_refused"] is False
    assert facts_v2["required_instruction_failures"] == 0
    assert facts_v2["unsupported_instruction_demotes"] == 0
    assert facts_v2["interior_conflicts_unresolved"] == 0
    copied_stage_rows = [
        row for row in rows if row.section_index == 0 and row.start_offset == 0x5C
    ]
    assert any(row.kind == "label" and "abs_0_00000400:" in row.text for row in copied_stage_rows)
    assert any(row.kind == "instruction" for row in copied_stage_rows)
    assert not any(row.kind == "data" for row in copied_stage_rows)
    assert any(
        row.section_index == 0
        and row.start_offset == 0x4B2A
        and row.kind == "instruction"
        and "\tclr.b $0011(a4)" in row.text
        for row in rows
    )
    bitmap_refs = [
        ref
        for row in rows
        if row.kind == "data" and row.text.startswith("\tdc.w bplpt") and row.runtime_address_refs
        for ref in row.runtime_address_refs
    ]
    assert [(ref.runtime_address, ref.size, ref.data_class) for ref in bitmap_refs] == [
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
        require_entities=False,
    )
    source_text, source_text_profile = facts_v2_asm_source_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "loc_0_00009DA2:\n\taddq.l #1,d0\n\trts\n" in source_text
    assert "loc_0_00009DA2:\n\tdc.b $52,$80,$4E,$75" not in source_text


def test_real_dll_damocles_register_copied_target_promotes_decompressor_code() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths(
        "amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_damocles_53b24620",
        project_root=PROJECT_ROOT,
        require_entities=False,
    )
    source_text, source_text_profile = facts_v2_asm_source_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert (
        "loc_2_0000006A:\n"
        "\tmoveq.l #-83,d7\n"
        "\tlea.l $00001000.l,a0\n"
        "\tlea.l $0007FFFF.l,a2\n"
    ) in source_text
    assert "loc_2_0000006A:\n\tdc.b $7E,$AD,$41,$F9" not in source_text


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
        and row.get("text") == "\tlea.l $00077400.l,a1\n"
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
    paths = resolve_project_paths(
        target_name,
        project_root=PROJECT_ROOT,
        require_entities=False,
    )
    payloads = combined["analysis"]["packed_payloads"]
    suggestions = combined["analysis"]["derived_target_suggestions"]
    payloads_by_offset = {payload["source_section_offset"]: payload for payload in payloads}
    suggestions_by_offset = {suggestion["source_section_offset"]: suggestion for suggestion in suggestions}

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
    assert suggestions_by_offset[0x05E4]["runtime_copy_address"] == 0x77400
    assert suggestions_by_offset[0x05E4]["runtime_copy_size"] == 18016
    assert suggestions_by_offset[0x05E4]["runtime_copy_kind"] == 2
    assert suggestions_by_offset[0x05E4]["runtime_copy_conflicting"] is False
    assert suggestions_by_offset[0x05E4]["reason"] == "runtime_copy_oversize"
    assert suggestions_by_offset[0x4C40]["runtime_copy_address"] == 0x4000
    assert suggestions_by_offset[0x4C40]["runtime_copy_size"] == 168396
    assert suggestions_by_offset[0x4C40]["runtime_copy_kind"] == 3
    assert suggestions_by_offset[0x4C40]["runtime_copy_conflicting"] is True
    assert suggestions_by_offset[0x4C40]["reason"] == "initial_control_target_validated_runtime_copy"
    assert suggestions_by_offset[0x4C40]["status"] == "materializable"
    assert suggestions_by_offset[0x4C40]["load_address"] == 0x4000
    assert suggestions_by_offset[0x4C40]["entrypoint"] == 0x4000
    assert suggestions_by_offset[0x4C40]["initial_control_target"] == 0x9B3A
    assert suggestions_by_offset[0x05E4]["status"] == "needs_runtime_metadata"
    assert "load_address" not in suggestions_by_offset[0x05E4]
    assert "entrypoint" not in suggestions_by_offset[0x05E4]

    source_text, source_text_profile = facts_v2_asm_source_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )
    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
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


def test_real_dll_carrier_decompressed_child_raw_reproduction() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths(
        "amiga_disk_carrier-command-1994-kixx-budget__amiga_raw_carrier_rnc_00004c60",
        project_root=PROJECT_ROOT,
        require_entities=False,
    )

    rebuilt, source_profile, _assembler_profile = facts_v2_render_assemble_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert len(rebuilt) == 359600
    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert rebuilt == paths.binary_source.read_bytes()


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

    assert len(payloads) == 1
    assert payloads[0]["provider_id"] == "ancient-cli"
    assert payloads[0]["codec_id"] == "rnc1"
    assert payloads[0]["source_section"] == 1
    assert payloads[0]["source_section_offset"] == 8
    assert payloads[0]["packed_size"] == 11406
    assert payloads[0]["decompressed_size"] == 84980
    assert len(suggestions) == 1
    assert suggestions[0]["status"] == "needs_runtime_metadata"
    assert suggestions[0]["source_section"] == 1
    assert suggestions[0]["source_section_offset"] == 8


def test_real_dll_conqueror_file_handle_slots_do_not_alias_dosbase() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths(
        "amiga_disk_conqueror-1990-rainbow-arts-de-en__amiga_hunk_conqueror_cf971606",
        project_root=PROJECT_ROOT,
        require_entities=False,
    )
    source_text, source_text_profile = facts_v2_asm_source_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "\tmovea.l loc_0_00000004.l,a6\n" not in source_text
    assert source_text.count("\tmovea.l $00000004.l,a6\n") == 2
    assert "\tlea.l loc_0_00000148.l,a0\n" in source_text
    assert "\tlea.l abs_0_00000004.l,a0\n" not in source_text
    assert "\tlea.l $00000004.l,a1\n" in source_text
    assert "\tjmp $00000004.l\n" in source_text
    assert "    ORG $4\n" not in source_text
    assert "\tclr.l spr1+sd_dataa(a6)\n" in source_text
    assert "\tclr.l app_014C(a6)\n" not in source_text
    assert "app_014C" not in source_text.split("    SECTION section_0,code\n", 1)[0]
    assert "\tmove.l d0,loc_0_0000004E.l\n" in source_text
    assert "\tmove.l d0,loc_0_00000052.l\n" in source_text
    assert "\tmove.l loc_0_0000004E.l,d1\n" in source_text
    assert source_text.count("h0dl_DOSBase:") == 1


def test_real_dll_starglider_loader_file_handle_slot_stays_untyped() -> None:
    _requires_c_backend_dlls()

    paths = resolve_project_paths(
        "amiga_disk_starglider-1987-rainbird__amiga_hunk_sgload_ee6b361e",
        project_root=PROJECT_ROOT,
        require_entities=False,
    )
    source_text, source_text_profile = facts_v2_asm_source_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )

    assert source_text_profile["facts_v2"]["asm_source_refused"] is False
    assert "\tmove.l d0,loc_0_00000304.l\n" in source_text
    assert "\tmove.l loc_0_00000304.l,d1\n" in source_text
    assert source_text.count("\tmove.l d0,h0dl_DOSBase.l\n") == 1


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
        require_entities=False,
    )

    source_text, source_text_profile = facts_v2_asm_source_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
        project_root=PROJECT_ROOT,
    )
    rebuilt, source_profile, assembler_profile = facts_v2_render_assemble_project_source_with_c_backend_profile(
        paths.binary_source,
        metadata_path=paths.target_dir / "target_metadata.json",
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
        "\tdc.w abs_0_0000166A-abs_0_0000166A,abs_0_000015D6-abs_0_0000166A,"
        "abs_0_0000175A-abs_0_0000166A,abs_0_000015B8-abs_0_0000166A\t; lookup_table\n"
        "\tdc.w abs_0_00001664-abs_0_0000166A\t; lookup_table\n"
    ) in source_text
    assert (
        "abs_0_0000A73A:\n"
        "\tdc.w abs_0_0000A50A-abs_0_0000A73A,abs_0_00009EFA-abs_0_0000A73A,"
        "abs_0_0000A34C-abs_0_0000A73A,abs_0_0000A330-abs_0_0000A73A\t; lookup_table\n"
        "\tdc.w abs_0_0000A53C-abs_0_0000A73A\t; lookup_table\n"
    ) in source_text
    assert (
        "abs_0_00002E4A:\n"
        "\tdc.w abs_0_00002E5C-abs_0_00002E5C,abs_0_00002E82-abs_0_00002E5C,"
        "abs_0_00002EE4-abs_0_00002E5C,abs_0_00002E5C-abs_0_00002E5C\t; lookup_table\n"
    ) in source_text
    assert (
        "abs_0_000033A0:\n"
        "\tdc.w abs_0_000033B2-abs_0_000033B2,abs_0_000033EE-abs_0_000033B2,"
        "abs_0_00004150-abs_0_000033B2,abs_0_000040E4-abs_0_000033B2\t; lookup_table\n"
        "\tdc.w abs_0_00003F60-abs_0_000033B2,abs_0_00004144-abs_0_000033B2,"
        "abs_0_00003F5C-abs_0_000033B2,abs_0_00003E9C-abs_0_000033B2\t; lookup_table\n"
        "\tdc.w abs_0_000034CC-abs_0_000033B2\t; lookup_table\n"
    ) in source_text
    assert (
        "\tlea.l $0000C262.l,a0\n"
        "\tmovea.l $0(a0,d0.w),a0\n"
        "\tjmp (a0)\n"
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
    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert assembler_profile["rebuilt_bytes"] == len(rebuilt)
    assert _amiga_hunk_section_hexes(tmp_path / "bloodwych_generated_source.hunk") == _amiga_hunk_section_hexes(
        paths.binary_source.path
    )
    assert source_profile["facts_v2"]["asm_source_instruction_byte_mismatches"] == 0


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
    paths = resolve_project_paths(
        "amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5__amiga_hunk_libs__icon.library_8bc90c0c",
        project_root=PROJECT_ROOT,
        require_entities=False,
    )

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
    assert "resident_vectors:\n\tdc.l icon_lib_open" in rendered
    assert "resident_init_struct:\n\tdc.b $E0,$00,$00,$08,$09,$00,$C0,$00,$00,$0A\n\tdc.l resident_name" in rendered
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
    assert "KNOWN: base A6=exec.library" in rendered
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

    rows, _ = build_project_rows_generation_with_c_backend(
        "amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5__amiga_hunk_libs__icon.library_8bc90c0c",
        generation="full",
        project_root=PROJECT_ROOT,
    )
    refs_by_text = {row.text.strip(): row.app_slot_refs for row in rows if row.app_slot_refs}
    assert refs_by_text["move.l a6,app_ExecBase(a2)"] == (
        AppSlotRef("app_ExecBase", 34, "A2", 1, "write"),
    )
    assert refs_by_text["move.l app_DOSBase(a2),h0dl_DOSBase.l"] == (
        AppSlotRef("app_DOSBase", 38, "A2", 0, "read"),
    )
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

    rows, _, _ = build_project_rows_generation_with_c_backend_profile(
        project_name,
        generation="full",
        project_root=PROJECT_ROOT,
    )

    vector_index = next(index for index, row in enumerate(rows) if row.text.strip() == "resident_vectors:")
    dos_index = next(index for index, row in enumerate(rows) if row.text.strip() == 'dc.b "dos.library",$00')
    open_index = next(index for index, row in enumerate(rows) if row.text.strip() == "icon_lib_open:")

    assert rows[vector_index].addr == 0x58
    assert rows[dos_index].addr == 0xD0
    assert rows[open_index].addr == 0xDC
    assert rows[open_index - 1].kind == "comment"
    assert "KNOWN: base A6=icon.library:LIB" in rows[open_index - 1].text
    assert not any(row.kind == "comment" for row in rows[vector_index:dos_index])


def test_real_dll_listing_rows_load_king_nondefault_fpu_save() -> None:
    _requires_c_backend_dlls()
    project_name = "amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5__amiga_hunk_king_481902ec"

    rows, _, _ = build_project_rows_generation_with_c_backend_profile(
        project_name,
        generation="full",
        project_root=PROJECT_ROOT,
    )

    fsave_rows = [
        row
        for row in rows
        if row.kind == "instruction" and row.text.strip() == "fsave app_7000(a6)"
    ]
    assert len(fsave_rows) == 1
    assert fsave_rows[0].app_slot_refs == (
        AppSlotRef("app_7000", 0x7000, "A6", 0, "read-write"),
    )


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
        kind="disk_entry",
        disk_id="resource_amiga_disk_argasm1.06",
        adf_path=disk_path,
        entry_path="libs/mathtrans.library",
        display_path="ArgAsm1.06.adf::libs/mathtrans.library",
        analysis_cache_path=tmp_path / "binary.analysis",
        project_root=PROJECT_ROOT,
    )

    rendered = render_project_source_with_c_backend(
        source,
        syntax="genam",
        metadata_path=metadata_path,
        project_root=PROJECT_ROOT,
    )
    source_path.write_text(rendered, encoding="ascii")

    assert "resident_vectors:" in rendered
    assert "dc.l s_p_atan" in rendered.lower()
    assert "ori.b #142,d0" not in rendered
    assert "invalid overlap: decoded code" in rendered
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
        kind="disk_entry",
        disk_id="resource_atari_devpac_3.10",
        adf_path=disk_path,
        entry_path="AMON/AMON030.PRG",
        display_path="Devpac v3.10 (1992)(HiSoft).st::AMON/AMON030.PRG",
        analysis_cache_path=tmp_path / "binary.analysis",
        project_root=PROJECT_ROOT,
    )

    rendered = render_project_source_with_c_backend(
        source,
        syntax="genam",
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
        kind="hunk_file",
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
        + bytes([0x00, 1, 0, 0])
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
        kind="hunk_file",
        path=binary_path,
        display_path=str(binary_path),
        analysis_cache_path=tmp_path / "analysis.json",
    )

    rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)

    assert "resident:\t; STRUCT RT" in rendered
    assert "\tdc.l $0000001C\t; APTR RT_INIT" in rendered
    assert "resident_init:\n\tmovea.l $0004.w,a6\n\trts" in rendered
    assert "\tdc.b $2C,$78,$00,$04,$4E,$75" not in rendered


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
