from __future__ import annotations

import ctypes
import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import DiskEntryBinarySource, HunkFileBinarySource, RawBinarySource
from amiga_reversing.disasm.c_backend import (
    amiga_naming_catalog_with_c_backend,
    amiga_os_metadata_catalog_with_c_backend,
    analyze_project_source_with_c_backend,
    api_calls_from_c_analysis,
    benchmark_project_source_with_text_from_c_backend,
    extract_disk_entry_with_c_backend,
    build_project_rows_generation_with_c_backend,
    inspect_disk_with_c_backend,
    render_binary_source_with_c_backend,
    render_project_source_with_c_backend,
    rows_from_c_listing_json,
    validate_amiga_hunk_executable_with_c_backend,
)
from amiga_reversing.disasm.listing_types import BlockRowContext, HeaderRowContext
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from src.tests._platform_backend_test_utils import make_synthetic_hunkexe
from src.tests._platform_backend_test_utils import M68kDiagList


def _requires_c_backend_dlls() -> None:
    build_dir = PROJECT_ROOT / "src" / "build"
    if not (build_dir / "platform_file_lib.dll").exists() or not (build_dir / "platform_disk_lib.dll").exists():
        pytest.skip("C backend DLLs are missing; run cmd /c src\\build.bat")


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


class _M68kAnalysisPolicy(ctypes.Structure):
    _fields_ = [
        ("max_cpu", ctypes.c_uint8),
        ("has_entry_offset", ctypes.c_uint8),
        ("skip_platform_facts", ctypes.c_uint8),
        ("reserved0", ctypes.c_uint8),
        ("register_seed_count", ctypes.c_uint16),
        ("entry_point_count", ctypes.c_uint16),
        ("structured_data_item_count", ctypes.c_uint16),
        ("named_label_count", ctypes.c_uint16),
        ("entry_comment_count", ctypes.c_uint16),
        ("reserved1", ctypes.c_uint16),
        ("entry_offset", ctypes.c_uint32),
        ("register_seeds", _M68kAnalysisRegisterSeed * 64),
        ("entry_points", _M68kAnalysisEntryPoint * 64),
        ("structured_data_items", _M68kAnalysisStructuredDataItem * 256),
        ("named_labels", _M68kAnalysisNamedLabel * 128),
        ("entry_comments", _M68kAnalysisEntryComment * 128),
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
                    "text": "    rts\n",
                    "stable_key": "s0:00000020:instruction:1",
                    "analysis_generation": "basic",
                    "addr": 32,
                    "entity_addr": 32,
                    "bytes": "4e75",
                    "label": None,
                    "opcode_or_directive": "rts",
                    "operand_text": "",
                    "comment_text": "",
                    "source_context": {"kind": "c-instruction", "hunk_index": 0},
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
    assert rows[1].opcode_or_directive == "rts"
    assert rows[1].bytes == b"\x4e\x75"
    assert rows[1].source_context == BlockRowContext(kind="c-instruction", hunk_index=0)
    assert rows[1].structured_data == {
        "struct_name": "RT",
        "field_name": "RT_MATCHWORD",
        "c_type": "UWORD",
        "value_domain": "exec.resident.matchword",
        "constant_name": "RTC_MATCHWORD",
    }


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
                        },
                    ],
                }
            ]
        }
    )

    assert api_calls[(0, 0x20)] == {
        "library": "dos.library",
        "function": "Output",
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


def test_render_binary_source_uses_c_dll(monkeypatch) -> None:
    calls: list[tuple[tuple[str, ...], object]] = []

    def fake_run(function_name: str, *args: str, project_root):
        calls.append(((function_name, *args), project_root))
        return "SECTION code,code\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_run)

    assert render_binary_source_with_c_backend("bin/GenAm", syntax="genam") == "SECTION code,code\n"
    assert calls == [
        (
            (
                "platform_file_disassemble_path_text_alloc",
                "amiga-hunk",
                "bin/GenAm",
                "genam",
                "",
            ),
            PROJECT_ROOT,
        )
    ]


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
    assert file_calls[0][0:2] == ("platform_file_analyze_path_json_alloc", "amiga-hunk")
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
        return "; atari\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    assert render_project_source_with_c_backend(source, project_root=tmp_path) == "; atari\n"
    assert calls[0][0:2] == ("platform_file_disassemble_path_text_alloc", "atari-st")


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
        return '{"sections":[]}' if function_name == "platform_file_analyze_raw_path_json_alloc" else "; raw\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    assert analyze_project_source_with_c_backend(source, project_root=tmp_path) == {"sections": []}
    assert render_project_source_with_c_backend(source, project_root=tmp_path) == "; raw\n"
    assert calls == [
        ("platform_file_analyze_raw_path_json_alloc", "amiga-raw", str(binary_path), 12, "", ""),
        ("platform_file_disassemble_raw_path_text_alloc", "amiga-raw", str(binary_path), 12, "vasm", ""),
    ]


def test_project_source_benchmark_with_text_uses_single_c_run(monkeypatch, tmp_path: Path) -> None:
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

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return '{"benchmark":{"analysis":{"violation_count":1}},"text":"SECTION code,code\\n"}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    benchmark, text = benchmark_project_source_with_text_from_c_backend(source, syntax="genam", project_root=tmp_path)

    assert benchmark == {"analysis": {"violation_count": 1}}
    assert text == "SECTION code,code\n"
    assert calls == [
        ("platform_file_benchmark_with_text_raw_path_json_alloc", "amiga-raw", str(binary_path), 12, "genam", ""),
    ]


def test_project_rows_raw_full_uses_combined_c_listing_and_analysis(monkeypatch, tmp_path: Path) -> None:
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

    def fake_file_run(function_name: str, *args: object, project_root):
        calls.append((function_name, *args))
        return '{"listing":{"rows":[]},"analysis":{"sections":[]}}'

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    rows, api_calls = build_project_rows_generation_with_c_backend(
        "raw_demo", generation="full", project_root=tmp_path
    )

    assert rows == []
    assert api_calls == {}
    assert calls == [
        (
            "platform_file_listing_rows_with_analysis_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            12,
            "",
        )
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
        return '{"sections":[]}' if function_name == "platform_file_analyze_raw_path_json_alloc" else "; raw\n"

    monkeypatch.setattr("amiga_reversing.disasm.c_backend._platform_file_text", fake_file_run)

    analyze_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=tmp_path)
    render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=tmp_path)

    assert calls == [
        (
            "platform_file_analyze_raw_path_json_alloc",
            "amiga-raw",
            str(binary_path),
            12,
            str(metadata_path),
            "",
        ),
        (
            "platform_file_disassemble_raw_path_text_alloc",
            "amiga-raw",
            str(binary_path),
            12,
            "vasm",
            str(metadata_path),
        ),
    ]


def test_legacy_metadata_loader_is_generic_only(tmp_path: Path) -> None:
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
                "resident": {"name": "icon.library", "version": 40, "offset": 0, "hunk": 0},
            }
        ),
        encoding="utf-8",
    )

    legacy_policy = _M68kAnalysisPolicy()
    legacy_diagnostics = M68kDiagList()
    assert dll.platform_file_analysis_policy_load_target_metadata(
        ctypes.byref(legacy_policy),
        str(metadata_path).encode("utf-8"),
        _M68kDiagSink(ctypes.pointer(legacy_diagnostics)),
    ) == 0
    assert legacy_policy.register_seed_count == 1
    assert legacy_policy.structured_data_item_count == 0
    assert legacy_policy.named_label_count == 0

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


def test_real_dll_renders_genam() -> None:
    _requires_c_backend_dlls()
    rendered = render_binary_source_with_c_backend(PROJECT_ROOT / "bin" / "GenAm", syntax="vasm")

    assert "SECTION" in rendered
    assert "move" in rendered.lower() or "jsr" in rendered.lower()


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

    assert "RSSET LIB_SIZE\napp_ExecBase RS.L 1\napp_DOSBase RS.L 1\napp_SegList RS.L 1\napp_SIZEOF EQU __RS" in rendered
    assert "app_ExecBase EQU 34" not in rendered
    assert "app_DOSBase EQU 38" not in rendered
    assert "app_SegList EQU 42" not in rendered
    assert "resident:                               ; STRUCT RT" in rendered
    assert "DC.W    RTC_MATCHWORD               ; UWORD RT_MATCHWORD" in rendered
    assert "DC.L    resident                    ; APTR RT_MATCHTAG" in rendered
    assert "DC.L    dat_0280                    ; APTR RT_ENDSKIP" in rendered
    assert "DC.B    RTF_AUTOINIT                ; UBYTE RT_FLAGS" in rendered
    assert "DC.B    NT_LIBRARY                  ; UBYTE RT_TYPE" in rendered
    assert "DC.L    resident_autoinit           ; APTR RT_INIT" in rendered
    assert "DC.B    34                          ; UBYTE RT_VERSION" in rendered
    assert "DC.B    70                          ; BYTE RT_PRI" in rendered
    assert "DC.L    resident_name               ; APTR RT_NAME" in rendered
    assert "DC.L    resident_idstring           ; APTR RT_IDSTRING" in rendered
    assert 'resident_name:\n    DC.B    "icon.library",0' in rendered
    assert 'resident_idstring:\n    DC.B    "icon 34.2 (22 Jun 1988)\\x0d\\x0a",0' in rendered
    assert "resident_autoinit:                      ; STRUCT resident_autoinit" in rendered
    assert "DC.L    app_SIZEOF                  ; ULONG resident_base_size" in rendered
    assert "DC.L    LIB_SIZE+12                 ; ULONG resident_base_size" not in rendered
    assert "DC.L    resident_vectors            ; APTR resident_vectors" in rendered
    assert "DC.L    resident_init_struct        ; APTR resident_init_struct" in rendered
    assert "DC.L    resident_init               ; APTR resident_init_function" in rendered
    assert "resident_vectors:\n    DC.L    lib_open" in rendered
    assert "resident_init_struct:\n    DC.L" in rendered
    assert "res_MatchWord:" not in rendered
    assert "res_Flags:" not in rendered
    assert "DC.W    $4afc ; NOTE: resident matchword" not in rendered
    assert "DC.L    lib_open\n" in rendered
    assert "DC.L    get_disk_object\n" in rendered
    assert "lib_open:\nloc_00DC:" not in rendered
    assert "resident_init:\n    move.l a2,-(a7)" in rendered
    assert "loc_0148:" not in rendered
    assert "move.l a0,app_SegList(a2)" in rendered
    assert "move.l a6,app_ExecBase(a2)" in rendered
    assert "move.l d0,app_DOSBase(a2)" in rendered
    assert "movea.l $0004.w,a6" in rendered
    assert "resident.w,a6" not in rendered
    assert "KNOWN: base A6=exec.library" in rendered
    assert "KNOWN: base A6=icon.library" in rendered
    assert "lib_open:\n    addq.w #1,LIB_OPENCNT(a6)" in rendered
    assert "lib_extfunc:\n    moveq.l #0,d0" in rendered
    assert "dat_00D0:\n    DC.B" in rendered
    assert "lea.l dat_00D0(pc),a1" in rendered
    assert "dat_00A4+44" not in rendered
    assert "VIOLATION: pc-relative" not in rendered
    assert "lea.l -$86(pc),a1" not in rendered
    assert "move.l app_ExecBase(a2),h0dl_ExecBase.l" in rendered
    assert "move.l app_DOSBase(a2),h0dl_DOSBase.l" in rendered
    assert "move.l app_SegList(a6),-(a7)" in rendered
    assert "movea.l LN_SUCC(a1),a0" in rendered
    assert "movea.l LN_PRED(a1),a1" in rendered
    assert "move.l a0,LN_SUCC(a1)" in rendered
    assert "move.l a1,LN_PRED(a0)" in rendered
    assert "move.l #AN_IconLib|AG_OpenLib|AO_DOSLib,d7" in rendered
    assert "movea.l app_ExecBase(a6),a6" in rendered
    assert "movea.l LIB_SIZE(a6),a6" not in rendered
    assert "h0dl_ExecBase:\n    DC.L    $00000000" in rendered
    assert "h0dl_DOSBase:\n    DC.L    $00000000" in rendered
    assert "dat_0192:" not in rendered
    assert "dat_0196:" not in rendered
    assert "$00000192.l" not in rendered
    assert "$00000196.l" not in rendered
    assert "h1_00BC:" in rendered
    assert "jsr h1_00BC.l" in rendered
    assert "jsr $000000BC.l" not in rendered
    assert "hunk1_0000 EQU" not in rendered
    assert "hunk1_0092 EQU" not in rendered
    assert "hunk1_00BC EQU" not in rendered
    assert "jsr h3_00A8.l" in rendered
    assert "h3_00A8:\n    link a6,#-80" in rendered
    assert "h3_00A8:\n    DC.L" not in rendered
    assert "jsr h8_DOSOpen.l" in rendered
    assert "h8_DOSOpen:\n    movem.l d2/a6,-(a7)" in rendered
    assert "jsr hunk3_0768.l ; CANDIDATE: indirect_call" not in rendered
    assert "jsr hunk3_0818.l ; CANDIDATE: indirect_call" not in rendered
    assert "get_disk_object:" in rendered
    assert "sub_00A8:" not in rendered
    assert "ori.w #29999,a6" not in rendered
    assert "; NOTE: resident vector\n" not in rendered
    assert "@abs:" not in rendered[:1500]


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


def test_real_dll_extract_disk_entry_reports_c_error() -> None:
    _requires_c_backend_dlls()
    disk_path = PROJECT_ROOT / "bin" / "Search for the King, The (1991)(Accolade)(Disk 1 of 5).adf"

    with pytest.raises(RuntimeError, match="C disk backend DLL failed:"):
        extract_disk_entry_with_c_backend(disk_path, "missing/file")
