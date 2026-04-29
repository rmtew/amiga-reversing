from __future__ import annotations

import ctypes
import json
import subprocess
from pathlib import Path

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
    analyze_project_source_with_c_backend,
    api_calls_from_c_analysis,
    assemble_platform_source_path_with_c_backend,
    assemble_platform_source_text_with_c_backend,
    benchmark_project_source_with_text_from_c_backend,
    build_project_rows_generation_with_c_backend,
    build_project_rows_generation_with_c_backend_profile,
    build_project_rows_generation_with_c_backend_profile_text,
    extract_disk_entry_with_c_backend,
    facts_v2_asm_source_project_source_with_c_backend,
    facts_v2_asm_source_project_source_with_c_backend_profile,
    facts_v2_direct_rebuild_project_source_with_c_backend_profile,
    facts_v2_render_assemble_project_source_with_c_backend_profile,
    inspect_disk_with_c_backend,
    render_binary_source_with_c_backend,
    render_project_source_with_c_backend,
    rows_from_c_listing_json,
    validate_amiga_hunk_executable_with_c_backend,
)
from amiga_reversing.disasm.facts_v2_source_refusal import FactsV2SourceRefused
from amiga_reversing.disasm.listing_types import AppSlotRef, BlockRowContext, HeaderRowContext, SymbolOperandMetadata
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
        ("reserved1", ctypes.c_uint16),
        ("entry_offset", ctypes.c_uint32),
        ("register_seeds", _M68kAnalysisRegisterSeed * 64),
        ("entry_points", _M68kAnalysisEntryPoint * 64),
        ("structured_data_items", _M68kAnalysisStructuredDataItem * 256),
        ("named_labels", _M68kAnalysisNamedLabel * 128),
        ("entry_comments", _M68kAnalysisEntryComment * 128),
        ("runtime_ranges", _M68kAnalysisRuntimeRange * 64),
        ("runtime_entry_points", _M68kAnalysisRuntimeEntryPoint * 64),
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
    assert "loc_0_00000020:\n    ORG $100\nloc_0_00000100:\n" in source_text
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
    runtime_label_index = row_texts.index("loc_0_00000100:")
    assert ref_index < storage_label_index < org_index < runtime_label_index
    storage_row = rows[storage_label_index]
    runtime_row = rows[runtime_label_index]
    assert storage_row.storage_address == 0x20
    assert storage_row.runtime_address == 0x100
    assert storage_row.runtime_view_id == 1
    assert runtime_row.storage_address == 0x20
    assert runtime_row.runtime_address == 0x100
    assert runtime_row.runtime_view_id == 1


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
    }
    assert api_calls[(0, 0x30)] == {
        "library": "unknown",
        "function": "OpenLibrary",
        "note_kind": 0,
        "call_kind": 1,
        "symbol_name": "_LVOOpenLibrary",
        "note_symbol_name": None,
        "inputs": [],
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


def test_project_source_runtime_absolute_raw_binary_passes_runtime_entrypoint(
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
        ("platform_file_facts_v2_asm_source_raw_path_text_alloc", "amiga-raw", str(binary_path), 0x400, ""),
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

    assert "    ORG $400\nloc_0_00000400:\n\trts\n" in source
    assert "loc_0_00000410:\n\trts\n" in source
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
    label_index = next(index for index, row in enumerate(rows) if row.label == "loc_0_00000400")

    assert rows[org_index].kind == "directive"
    assert rows[org_index].opcode_or_directive == "ORG"
    assert rows[org_index].operand_text == "$400"
    assert rows[org_index].addr is None
    assert org_index < label_index


def test_real_dll_facts_v2_listing_rows_auto_classifies_copper_list_from_cop_pointer(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    binary_path = tmp_path / "copper.bin"
    binary_path.write_bytes(
        bytes.fromhex(
            "23fc0000000c00dff080"
            "4e75"
            "01004200"
            "00e01234"
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
                        "source_end": 24,
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
    copper_row = next(row for row in rows if row.addr == 0x0C and row.kind == "data")

    assert copper_row.kind == "data"
    assert copper_row.data_class == "copper_list"
    assert copper_row.text.strip() == "dc.w bplcon0,$4200"


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
    assert "\tlea.l loc_0_00070026(pc),a1\n" in source_text
    assert "\tjsr _LVOFindResident(a6)\n" in source_text
    assert "\tmovea.l RT_INIT(a0),a0\n" in source_text
    assert 'INCLUDE "exec/resident.i"' in source_text
    assert "loc_0_00070026:" in source_text
    assert '\tdc.b "dos.library",$00\n' in source_text
    assert "facts_v2 data bytes" not in source_text
    assert any(row.kind == "instruction" and "loc_0_00070026(pc)" in row.text for row in rows)
    assert any(row.kind == "label" and row.addr == 0x26 and row.text.strip() == "loc_0_00070026:" for row in rows)
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
    assert any(row.kind == "label" and "loc_0_00000400:" in row.text for row in copied_stage_rows)
    assert any(row.kind == "instruction" for row in copied_stage_rows)
    assert not any(row.kind == "data" for row in copied_stage_rows)


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
    assert "loc_0_0000005C:\n    ORG $400\nloc_0_00000400:" in source_text
    assert "ORG $5C" not in source_text
    assert "loc_0_0000005C\tEQU" not in source_text
    assert "\tmove.l #loc_0_00008E10,_custom+cop1lc.l\n" in source_text
    assert "loc_0_00008E10:\n\tdc.w bplpt,$0007\n" in source_text
    assert "loc_0_00008E30:\n\tdc.w sprpt,$0000\n" in source_text
    assert "m68k_vector_level_3_interrupt_autovector\tEQU\t$6C" in source_text
    assert "\tmove.l #loc_0_00008C20,m68k_vector_level_3_interrupt_autovector.w\n" in source_text
    assert "$00DFF" not in source_text
    assert source_profile["facts_v2"]["asm_source_refused"] is False
    assert assembler_profile["rebuilt_bytes"] == len(rebuilt)
    assert rebuilt == paths.binary_source.path.read_bytes()


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


def test_real_dll_renders_mathtrans_overlap_and_fpu_restore_reassembles(tmp_path: Path) -> None:
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
    assert "fpu     5" in lowered
    assert "frestore (a4)" in lowered
    assert "fpu     1" in lowered
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
