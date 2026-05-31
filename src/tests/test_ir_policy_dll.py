from __future__ import annotations

import ctypes
import json
import os
import tempfile
import unittest
from functools import lru_cache
from pathlib import Path

from src.tests._build_helpers import require_built_tools
from src.tests._build_helpers import prepare_test_dll
from src.tests._platform_backend_test_utils import make_synthetic_hunkexe

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
ASM_DLL_PATH = ROOT / "src" / "build" / "m68k_assembler_lib.dll"
DISASM_DLL_PATH = ROOT / "src" / "build" / "m68k_disassembler_lib.dll"
FILE_DLL_PATH = ROOT / "src" / "build" / "platform_file_lib.dll"
AMIGA_INCLUDE_DIR = ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"
AMIGA_OS_COMPAT_VERSION_1_3 = 1
M68K_OS_COMPATIBILITY_AMIGA = 1
M68K_DIAG_SEVERITY_ERROR = 3
M68K_DIAG_MESSAGE_SIZE = 160
M68K_DIAG_LIST_CAPACITY = 8


class M68kDiag(ctypes.Structure):
    _fields_ = [
        ("severity", ctypes.c_uint32),
        ("code", ctypes.c_uint32),
        ("message", ctypes.c_char * M68K_DIAG_MESSAGE_SIZE),
    ]


class M68kDiagList(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_size_t),
        ("dropped_count", ctypes.c_size_t),
        ("items", M68kDiag * M68K_DIAG_LIST_CAPACITY),
    ]


class M68kDisasmTextResult(ctypes.Structure):
    _fields_ = [
        ("byte_count", ctypes.c_size_t),
        ("text", ctypes.c_char * 256),
        ("diagnostics", M68kDiagList),
    ]


def _diag_message(diagnostics: M68kDiagList) -> str:
    for index in range(diagnostics.count):
        if diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR:
            return diagnostics.items[index].message.decode("utf-8")
    if diagnostics.count:
        return diagnostics.items[0].message.decode("utf-8")
    return ""


def _diag_has_errors(diagnostics: M68kDiagList) -> bool:
    return any(
        diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR
        for index in range(diagnostics.count)
    )


class M68kAssemblerSyntaxPolicy(ctypes.Structure):
    _fields_ = [("syntax_mode", ctypes.c_uint8)]


class M68kPresentationPolicy(ctypes.Structure):
    _fields_ = [
        ("prefer_generated_names", ctypes.c_uint8),
        ("prefer_strings", ctypes.c_uint8),
        ("prefer_long_data", ctypes.c_uint8),
        ("code_label_prefix", ctypes.c_char * 8),
        ("call_label_prefix", ctypes.c_char * 8),
        ("data_label_prefix", ctypes.c_char * 8),
    ]


class M68kOsRenderPolicy(ctypes.Structure):
    _fields_ = [
        ("compatibility_kind", ctypes.c_uint8),
        ("compatibility_level", ctypes.c_uint16),
    ]


class M68kRenderPolicy(ctypes.Structure):
    _fields_ = [
        ("syntax", M68kAssemblerSyntaxPolicy),
        ("presentation", M68kPresentationPolicy),
        ("os", M68kOsRenderPolicy),
    ]


class M68kSourceFileIR(ctypes.Structure):
    _fields_ = [
        ("file_kind", ctypes.c_int),
        ("platform_backend_kind", ctypes.c_uint8),
        ("has_atari_st_program_flags", ctypes.c_uint8),
        ("atari_st_program_flags", ctypes.c_uint32),
        ("sections", ctypes.c_void_p),
        ("section_count", ctypes.c_size_t),
        ("section_capacity", ctypes.c_size_t),
        ("arena", ctypes.c_void_p),
    ]


class M68kSourceIrParseResult(ctypes.Structure):
    _fields_ = [
        ("source_file", M68kSourceFileIR),
        ("diagnostics", M68kDiagList),
    ]


class M68kSourceIrRenderResult(ctypes.Structure):
    _fields_ = [
        ("text", ctypes.c_void_p),
        ("diagnostics", M68kDiagList),
    ]


class PlatformFileTextResult(ctypes.Structure):
    _fields_ = [
        ("text", ctypes.c_void_p),
        ("diagnostics", M68kDiagList),
    ]


@lru_cache(maxsize=1)
def _asm_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(ASM_DLL_PATH)))
    library.m68k_source_ir_parse_file.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_uint8,
    ]
    library.m68k_source_ir_parse_file.restype = M68kSourceIrParseResult
    library.m68k_source_ir_render_with_policy.argtypes = [
        ctypes.POINTER(M68kSourceFileIR),
        ctypes.POINTER(M68kRenderPolicy),
    ]
    library.m68k_source_ir_render_with_policy.restype = M68kSourceIrRenderResult
    library.m68k_source_ir_free.argtypes = [ctypes.POINTER(M68kSourceFileIR)]
    library.m68k_source_ir_free.restype = None
    library.m68k_free_text.argtypes = [ctypes.c_void_p]
    library.m68k_free_text.restype = None
    return library


@lru_cache(maxsize=1)
def _file_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(FILE_DLL_PATH)))
    library.platform_file_analysis_policy_create.argtypes = [ctypes.c_uint8]
    library.platform_file_analysis_policy_create.restype = ctypes.c_void_p
    library.platform_file_analysis_policy_destroy.argtypes = [ctypes.c_void_p]
    library.platform_file_analysis_policy_destroy.restype = None
    library.platform_file_facts_v2_analysis_path_json.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_void_p,
    ]
    library.platform_file_facts_v2_analysis_path_json.restype = PlatformFileTextResult
    library.platform_file_facts_v2_analysis_buffer_json.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_void_p,
    ]
    library.platform_file_facts_v2_analysis_buffer_json.restype = PlatformFileTextResult
    library.platform_file_inspect_path_json_alloc.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_inspect_path_json_alloc.restype = ctypes.c_int
    library.platform_file_facts_v2_analysis_path_json_alloc.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_analysis_path_json_alloc.restype = ctypes.c_int
    library.platform_file_effective_policy_path_json_alloc.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_effective_policy_path_json_alloc.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_path_create.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_listing_artifact_path_create.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_raw_path_create.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_listing_artifact_raw_path_create.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_window_json_alloc.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_listing_artifact_window_json_alloc.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_addr_window_json_alloc.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_listing_artifact_addr_window_json_alloc.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_source_offset_row_json_alloc.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_listing_artifact_source_offset_row_json_alloc.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_source_text_profile_alloc.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_listing_artifact_source_text_profile_alloc.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_summary_json_alloc.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_listing_artifact_summary_json_alloc.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_analysis_json_alloc.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_listing_artifact_analysis_json_alloc.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_navigation_json_alloc.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.platform_file_facts_v2_listing_artifact_navigation_json_alloc.restype = ctypes.c_int
    library.platform_file_facts_v2_listing_artifact_destroy.argtypes = [ctypes.c_void_p]
    library.platform_file_facts_v2_listing_artifact_destroy.restype = None
    library.platform_file_free_text.argtypes = [ctypes.c_void_p]
    library.platform_file_free_text.restype = None
    library.platform_file_free_bytes.argtypes = [ctypes.c_void_p]
    library.platform_file_free_bytes.restype = None
    return library


@lru_cache(maxsize=1)
def _disasm_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(DISASM_DLL_PATH)))
    library.m68k_disassemble_one_text.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
    ]
    library.m68k_disassemble_one_text.restype = M68kDisasmTextResult
    return library


def _default_policy() -> M68kRenderPolicy:
    policy = M68kRenderPolicy()
    policy.syntax.syntax_mode = 0
    policy.presentation.prefer_generated_names = 1
    policy.presentation.prefer_strings = 1
    policy.presentation.prefer_long_data = 1
    policy.presentation.code_label_prefix = b"loc"
    policy.presentation.call_label_prefix = b"sub"
    policy.presentation.data_label_prefix = b"dat"
    return policy


def _analysis_policy(library, max_cpu: int = 5) -> ctypes.c_void_p:
    policy = library.platform_file_analysis_policy_create(max_cpu)
    if not policy:
        raise MemoryError("failed to allocate M68kAnalysisPolicy")
    return policy


def _file_alloc_text(library, function_name: str, *args: bytes) -> tuple[int, str]:
    out_text = ctypes.c_void_p()
    result = getattr(library, function_name)(*args, ctypes.byref(out_text))
    try:
        text = ctypes.string_at(out_text).decode("utf-8") if out_text.value else ""
        return result, text
    finally:
        if out_text.value:
            library.platform_file_free_text(out_text)


class IrPolicyDllTests(unittest.TestCase):
    def test_disassembler_dll_renders_movem_predecrement_via_ir(self) -> None:
        library = _disasm_library()
        data = (ctypes.c_uint8 * 4)(0x48, 0xE7, 0x60, 0xE0)
        result = library.m68k_disassemble_one_text(
            data,
            4,
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        self.assertEqual(result.text.decode("utf-8"), "movem.l d1-d2/a0-a2,-(a7)")

    def test_source_ir_render_preserves_mid_instruction_pc_relative_overlap_as_label_plus_offset(self) -> None:
        library = _asm_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.s"
            path.write_text(
                "SECTION code,code\n"
                "start:\n"
                "    pea.l code+2(pc)\n"
                "code:\n"
                "    lea.l $0010(a1),a0\n"
                "    rts\n",
                encoding="utf-8",
            )
            policy = _default_policy()
            parse_result = library.m68k_source_ir_parse_file(
                str(path).encode("utf-8"),
                str(AMIGA_INCLUDE_DIR).encode("utf-8"),
                0,
            )
            self.assertFalse(_diag_has_errors(parse_result.diagnostics), _diag_message(parse_result.diagnostics))
            source_file = parse_result.source_file
            try:
                render_result = library.m68k_source_ir_render_with_policy(
                    ctypes.byref(source_file),
                    ctypes.byref(policy),
                )
                self.assertFalse(_diag_has_errors(render_result.diagnostics), _diag_message(render_result.diagnostics))
                try:
                    text = ctypes.cast(render_result.text, ctypes.c_char_p).value.decode("utf-8")
                finally:
                    library.m68k_free_text(render_result.text)
            finally:
                library.m68k_source_ir_free(ctypes.byref(source_file))

        self.assertIn("pea code+2(pc)", text)
        self.assertIn("code:", text)

    def test_source_ir_render_emits_comment_head_metadata(self) -> None:
        library = _asm_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.s"
            path.write_text(
                "COMMENT HEAD=$7\n"
                "SECTION code,code\n"
                "start:\n"
                "    rts\n",
                encoding="utf-8",
            )
            policy = _default_policy()
            parse_result = library.m68k_source_ir_parse_file(
                str(path).encode("utf-8"),
                str(AMIGA_INCLUDE_DIR).encode("utf-8"),
                0,
            )
            self.assertFalse(_diag_has_errors(parse_result.diagnostics), _diag_message(parse_result.diagnostics))
            source_file = parse_result.source_file
            self.assertEqual(source_file.has_atari_st_program_flags, 1)
            self.assertEqual(source_file.atari_st_program_flags, 7)
            try:
                render_result = library.m68k_source_ir_render_with_policy(
                    ctypes.byref(source_file),
                    ctypes.byref(policy),
                )
                self.assertFalse(_diag_has_errors(render_result.diagnostics), _diag_message(render_result.diagnostics))
                try:
                    text = ctypes.cast(render_result.text, ctypes.c_char_p).value.decode("utf-8")
                finally:
                    library.m68k_free_text(render_result.text)
            finally:
                library.m68k_source_ir_free(ctypes.byref(source_file))

        self.assertIn("COMMENT HEAD=$7", text)

    def test_source_ir_parse_rs_word_and_long_align_before_assignment(self) -> None:
        library = _asm_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.s"
            path.write_text(
                "RSSET 1\n"
                "foo RS.W 1\n"
                "bar RS.L 1\n"
                "SECTION code,code\n"
                "    DC.B foo,bar,__RS\n",
                encoding="utf-8",
            )
            policy = _default_policy()
            parse_result = library.m68k_source_ir_parse_file(
                str(path).encode("utf-8"),
                str(AMIGA_INCLUDE_DIR).encode("utf-8"),
                0,
            )
            self.assertFalse(_diag_has_errors(parse_result.diagnostics), _diag_message(parse_result.diagnostics))
            source_file = parse_result.source_file
            try:
                render_result = library.m68k_source_ir_render_with_policy(
                    ctypes.byref(source_file),
                    ctypes.byref(policy),
                )
                self.assertFalse(_diag_has_errors(render_result.diagnostics), _diag_message(render_result.diagnostics))
                try:
                    text = ctypes.cast(render_result.text, ctypes.c_char_p).value.decode("utf-8")
                finally:
                    library.m68k_free_text(render_result.text)
            finally:
                library.m68k_source_ir_free(ctypes.byref(source_file))

        self.assertIn("DC.B    $02,$04,$08", text)

    def test_platform_file_analysis_reports_cfg_for_certain_code(self) -> None:
        library = _file_library()
        sample = make_synthetic_hunkexe()
        sample_buf = (ctypes.c_uint8 * len(sample)).from_buffer_copy(sample)
        policy = _analysis_policy(library)
        try:
            result = library.platform_file_facts_v2_analysis_buffer_json(
                b"amiga-hunk",
                sample_buf,
                len(sample),
                policy,
            )
            self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
            try:
                analysis = json.loads(ctypes.cast(result.text, ctypes.c_char_p).value.decode("utf-8"))
            finally:
                library.platform_file_free_text(result.text)
        finally:
            library.platform_file_analysis_policy_destroy(policy)
        self.assertEqual(analysis["section_count"], 2)
        code_section = analysis["sections"][0]
        data_section = analysis["sections"][1]
        self.assertGreaterEqual(code_section["block_count"], 1)
        self.assertGreaterEqual(code_section["edge_count"], 1)
        self.assertEqual(code_section["blocks"][0]["start_offset"], 0)
        self.assertEqual(code_section["blocks"][0]["end_offset"], 2)
        self.assertEqual(code_section["edges"][0]["source_offset"], 0)
        self.assertEqual(code_section["edges"][0]["kind"], 5)
        self.assertEqual(data_section["block_count"], 0)

    def test_platform_file_alloc_api_inspects_path(self) -> None:
        library = _file_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.hunk"
            path.write_bytes(make_synthetic_hunkexe())

            result, text = _file_alloc_text(
                library,
                "platform_file_inspect_path_json_alloc",
                b"amiga-hunk",
                str(path).encode("utf-8"),
            )

        self.assertEqual(result, 0, text)
        info = json.loads(text)
        self.assertEqual(info["platform"], "amiga-hunk")
        self.assertEqual(info["section_count"], 2)

    def test_platform_file_alloc_api_reports_error(self) -> None:
        library = _file_library()
        result, text = _file_alloc_text(
            library,
            "platform_file_inspect_path_json_alloc",
            b"missing-backend",
            b"missing.bin",
        )

        self.assertNotEqual(result, 0)
        self.assertTrue(text)

    def test_platform_file_alloc_api_uses_metadata_for_analysis_listing_and_render(self) -> None:
        library = _file_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.hunk"
            metadata_path = Path(tmp) / "target_metadata.json"
            path.write_bytes(make_synthetic_hunkexe())
            metadata_path.write_text(
                json.dumps(
                    {
                        "entry_register_seeds": [],
                        "seeded_code_entrypoints": [
                            {"addr": 0, "hunk": 0, "name": "manual_start"},
                        ],
                    },
                ),
                encoding="utf-8",
            )
            encoded_path = str(path).encode("utf-8")
            encoded_metadata_path = str(metadata_path).encode("utf-8")

            analyze_result, analyze_text = _file_alloc_text(
                library,
                "platform_file_facts_v2_analysis_path_json_alloc",
                b"amiga-hunk",
                encoded_path,
                encoded_metadata_path,
                b"",
            )
            artifact = ctypes.c_void_p()
            error = ctypes.c_void_p()
            listing_result = library.platform_file_facts_v2_listing_artifact_path_create(
                b"amiga-hunk",
                encoded_path,
                encoded_metadata_path,
                b"",
                ctypes.byref(artifact),
                ctypes.byref(error),
            )
            listing_text = ctypes.string_at(error).decode("utf-8") if error.value else ""
            if error.value:
                library.platform_file_free_text(error)
            if artifact.value:
                window = ctypes.c_void_p()
                summary = ctypes.c_void_p()
                try:
                    summary_result = library.platform_file_facts_v2_listing_artifact_summary_json_alloc(
                        artifact,
                        ctypes.byref(summary),
                    )
                    summary_text = ctypes.string_at(summary).decode("utf-8") if summary.value else ""
                    self.assertEqual(summary_result, 0, summary_text)
                    total_rows = json.loads(summary_text)["summary"]["total_rows"]
                    window_result = library.platform_file_facts_v2_listing_artifact_window_json_alloc(
                        artifact,
                        0,
                        total_rows,
                        ctypes.byref(window),
                    )
                    listing_text = ctypes.string_at(window).decode("utf-8") if window.value else ""
                    self.assertEqual(window_result, 0, listing_text)
                finally:
                    if summary.value:
                        library.platform_file_free_text(summary)
                    if window.value:
                        library.platform_file_free_text(window)
                    library.platform_file_facts_v2_listing_artifact_destroy(artifact)

        self.assertEqual(analyze_result, 0, analyze_text)
        self.assertEqual(json.loads(analyze_text)["section_count"], 2)
        self.assertEqual(listing_result, 0, listing_text)
        listing_rows = json.loads(listing_text)["listing"]["rows"]
        self.assertTrue(listing_rows)
        addressed_rows = [row for row in listing_rows if isinstance(row.get("addr"), int)]
        self.assertTrue(addressed_rows)
        self.assertEqual(addressed_rows[0]["entity_addr"], addressed_rows[0]["addr"])
        self.assertIn("SECTION", listing_text)

    def test_effective_policy_exports_rsset_storage_kind_id(self) -> None:
        library = _file_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.hunk"
            metadata_path = Path(tmp) / "target_metadata.json"
            path.write_bytes(make_synthetic_hunkexe(code_data=b"\x00" * 64))
            metadata_path.write_text(
                json.dumps(
                    {
                        "rsset_layout_regions": [
                            {
                                "offset": 0x20,
                                "flags": 1,
                                "layout_name": "state",
                                "base_symbol": "state_base",
                                "symbol": "app_Buffer",
                                "storage_kind": "pointer",
                            },
                            {
                                "offset": 0x24,
                                "layout_name": "app",
                                "base_symbol": "__amiga_app_base__",
                                "symbol": "app_NameOnly",
                                "storage_kind": "scalar",
                            },
                            {
                                "offset": 0x28,
                                "layout_name": "app",
                                "base_symbol": "__amiga_app_base__",
                                "symbol": "app_ItemIds",
                                "storage_kind": "byte_array",
                                "size": 4,
                            },
                        ],
                    },
                ),
                encoding="utf-8",
            )

            result, text = _file_alloc_text(
                library,
                "platform_file_effective_policy_path_json_alloc",
                b"amiga-hunk",
                str(path).encode("utf-8"),
                str(metadata_path).encode("utf-8"),
                b"",
            )

        self.assertEqual(result, 0, text)
        regions = json.loads(text)["analysis_policy"]["rsset_layout_regions"]
        self.assertEqual(regions[0]["storage_kind_id"], 3)
        self.assertEqual(regions[0]["storage_kind"], "pointer")
        self.assertEqual(regions[0]["flags"], 1)
        self.assertEqual(regions[1]["storage_kind_id"], 4)
        self.assertEqual(regions[1]["flags"], 2)
        self.assertEqual(regions[2]["storage_kind_id"], 5)
        self.assertEqual(regions[2]["storage_kind"], "byte_array")

    def test_effective_policy_exports_structured_data_ids(self) -> None:
        library = _file_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.hunk"
            metadata_path = Path(tmp) / "target_metadata.json"
            path.write_bytes(make_synthetic_hunkexe(code_data=b"\x00" * 64))
            metadata_path.write_text(
                json.dumps(
                    {
                        "target_type": "library",
                        "resident": {
                            "hunk": 0,
                            "offset": 0,
                            "init_offset": 0,
                            "name": "sample.library",
                            "version": 1,
                            "autoinit": {
                                "payload_offset": 0,
                                "vectors_offset": 4,
                                "init_struct_offset": 8,
                                "init_func_offset": 12,
                            },
                        },
                    },
                ),
                encoding="utf-8",
            )

            result, text = _file_alloc_text(
                library,
                "platform_file_effective_policy_path_json_alloc",
                b"amiga-hunk",
                str(path).encode("utf-8"),
                str(metadata_path).encode("utf-8"),
                b"",
            )

        self.assertEqual(result, 0, text)
        items = json.loads(text)["analysis_policy"]["structured_data_items"]
        resident_match = next(item for item in items if item["field_name"] == "RT_MATCHWORD")
        autoinit_size = next(item for item in items if item["field_name"] == "resident_base_size")
        self.assertGreater(resident_match["struct_id"], 0)
        self.assertGreater(resident_match["field_id"], 0)
        self.assertEqual(autoinit_size["platform_kind_id"], 1)
        self.assertEqual(autoinit_size["platform_field_id"], 1)

    def test_platform_file_listing_artifact_reuses_c_analysis_for_windows(self) -> None:
        library = _file_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.hunk"
            path.write_bytes(make_synthetic_hunkexe())
            encoded_path = str(path).encode("utf-8")

            artifact = ctypes.c_void_p()
            error = ctypes.c_void_p()
            create_result = library.platform_file_facts_v2_listing_artifact_path_create(
                b"amiga-hunk",
                encoded_path,
                b"",
                b"",
                ctypes.byref(artifact),
                ctypes.byref(error),
            )
            try:
                error_text = ctypes.string_at(error).decode("utf-8") if error.value else ""
                self.assertEqual(create_result, 0, error_text)
                self.assertTrue(artifact.value)
                artifact_analysis = ctypes.c_void_p()
                first_window = ctypes.c_void_p()
                second_window = ctypes.c_void_p()
                addr_window = ctypes.c_void_p()
                source_text = ctypes.c_void_p()
                source_profile = ctypes.c_void_p()
                summary = ctypes.c_void_p()
                all_window = ctypes.c_void_p()
                navigation = ctypes.c_void_p()
                try:
                    artifact_analysis_result = library.platform_file_facts_v2_listing_artifact_analysis_json_alloc(
                        artifact,
                        ctypes.byref(artifact_analysis),
                    )
                    first_result = library.platform_file_facts_v2_listing_artifact_window_json_alloc(
                        artifact,
                        1,
                        2,
                        ctypes.byref(first_window),
                    )
                    second_result = library.platform_file_facts_v2_listing_artifact_window_json_alloc(
                        artifact,
                        2,
                        2,
                        ctypes.byref(second_window),
                    )
                    addr_result = library.platform_file_facts_v2_listing_artifact_addr_window_json_alloc(
                        artifact,
                        1,
                        0,
                        0,
                        2,
                        ctypes.byref(addr_window),
                    )
                    source_result = library.platform_file_facts_v2_listing_artifact_source_text_profile_alloc(
                        artifact,
                        ctypes.byref(source_text),
                        ctypes.byref(source_profile),
                    )
                    summary_result = library.platform_file_facts_v2_listing_artifact_summary_json_alloc(
                        artifact,
                        ctypes.byref(summary),
                    )
                    navigation_result = library.platform_file_facts_v2_listing_artifact_navigation_json_alloc(
                        artifact,
                        ctypes.byref(navigation),
                    )
                    artifact_analysis_text = (
                        ctypes.string_at(artifact_analysis.value).decode("utf-8")
                        if artifact_analysis.value
                        else ""
                    )
                    first_text = ctypes.string_at(first_window).decode("utf-8") if first_window.value else ""
                    second_text = ctypes.string_at(second_window).decode("utf-8") if second_window.value else ""
                    addr_text = ctypes.string_at(addr_window).decode("utf-8") if addr_window.value else ""
                    artifact_source_text = ctypes.string_at(source_text).decode("utf-8") if source_text.value else ""
                    source_profile_text = (
                        ctypes.string_at(source_profile).decode("utf-8") if source_profile.value else ""
                    )
                    summary_text = ctypes.string_at(summary).decode("utf-8") if summary.value else ""
                    total_rows = json.loads(summary_text)["summary"]["total_rows"] if summary_text else 0
                    all_result = library.platform_file_facts_v2_listing_artifact_window_json_alloc(
                        artifact,
                        0,
                        total_rows,
                        ctypes.byref(all_window),
                    )
                    all_text = ctypes.string_at(all_window).decode("utf-8") if all_window.value else ""
                    navigation_text = ctypes.string_at(navigation).decode("utf-8") if navigation.value else ""
                    self.assertEqual(artifact_analysis_result, 0, artifact_analysis_text)
                    self.assertEqual(first_result, 0, first_text)
                    self.assertEqual(second_result, 0, second_text)
                    self.assertEqual(addr_result, 0, addr_text)
                    self.assertEqual(source_result, 0, artifact_source_text)
                    self.assertTrue(source_profile_text)
                    self.assertEqual(summary_result, 0, summary_text)
                    self.assertEqual(all_result, 0, all_text)
                    self.assertEqual(navigation_result, 0, navigation_text)
                finally:
                    if artifact_analysis.value:
                        library.platform_file_free_text(artifact_analysis)
                    if first_window.value:
                        library.platform_file_free_text(first_window)
                    if second_window.value:
                        library.platform_file_free_text(second_window)
                    if addr_window.value:
                        library.platform_file_free_text(addr_window)
                    if source_text.value:
                        library.platform_file_free_text(source_text)
                    if source_profile.value:
                        library.platform_file_free_text(source_profile)
                    if summary.value:
                        library.platform_file_free_text(summary)
                    if all_window.value:
                        library.platform_file_free_text(all_window)
                    if navigation.value:
                        library.platform_file_free_text(navigation)
            finally:
                if error.value:
                    library.platform_file_free_text(error)
                if artifact.value:
                    library.platform_file_facts_v2_listing_artifact_destroy(artifact)

        self.assertIn("SECTION", artifact_source_text)
        artifact_analysis_payload = json.loads(artifact_analysis_text)
        self.assertEqual(
            artifact_analysis_payload["profile"]["generation"],
            "facts_v2_listing_artifact_analysis",
        )
        self.assertIn("sections", artifact_analysis_payload["analysis"])
        first_rows = json.loads(first_text)["listing"]["rows"]
        second_payload = json.loads(second_text)
        second_rows = second_payload["listing"]["rows"]
        addr_payload = json.loads(addr_text)
        addr_rows = addr_payload["listing"]["rows"]
        summary_payload = json.loads(summary_text)
        source_profile_payload = json.loads(source_profile_text)
        all_rows_payload = json.loads(all_text)
        full_rows = all_rows_payload["listing"]["rows"]
        row_kind_ids = {
            "directive": 1,
            "label": 2,
            "instruction": 3,
            "data": 4,
            "blank": 5,
            "comment": 6,
        }
        self.assertTrue(full_rows)
        for row in full_rows:
            if row["kind"] in row_kind_ids:
                self.assertEqual(row["kind_id"], row_kind_ids[row["kind"]])
        addr_anchor = next(
            (index for index, row in enumerate(full_rows) if isinstance(row.get("addr"), int) and row["addr"] >= 0),
            max(0, len(full_rows) - 1),
        )
        self.assertEqual([row["row_id"] for row in first_rows], [row["row_id"] for row in full_rows[1:3]])
        self.assertEqual([row["row_id"] for row in second_rows], [row["row_id"] for row in full_rows[2:4]])
        self.assertEqual(
            [row["row_id"] for row in addr_rows],
            [row["row_id"] for row in full_rows[addr_anchor:addr_anchor + 3]],
        )
        self.assertEqual(addr_payload["profile"]["generation"], "facts_v2_listing_artifact_addr_window")
        self.assertEqual(addr_payload["profile"]["listing_total_rows"], len(full_rows))
        self.assertGreaterEqual(addr_payload["profile"]["listing_addr_block_count"], 1)
        self.assertEqual(second_payload["profile"]["generation"], "facts_v2_listing_artifact_window")
        self.assertEqual(second_payload["profile"]["listing_total_rows"], len(full_rows))
        self.assertEqual(summary_payload["profile"]["generation"], "facts_v2_listing_artifact_summary")
        self.assertEqual(summary_payload["summary"]["total_rows"], len(full_rows))
        self.assertEqual(source_profile_payload["generation"], "facts_v2_listing_artifact_source_text")
        self.assertEqual(source_profile_payload["listing_total_rows"], len(full_rows))
        self.assertIn("source_emit_seconds", source_profile_payload["timing"])
        navigation_payload = json.loads(navigation_text)
        self.assertEqual(navigation_payload["profile"]["generation"], "facts_v2_listing_artifact_navigation")
        self.assertEqual(navigation_payload["navigation"]["analysis_generation"], "full")
        self.assertIn("labels", navigation_payload["navigation"]["groups"])
        label_refs = [
            ref
            for label in navigation_payload["navigation"]["groups"]["labels"]
            for ref in label.get("refs", [])
        ]
        self.assertTrue(label_refs)
        for ref in label_refs:
            self.assertIn(ref["access_kind"], (1, 2))

    def test_platform_file_listing_artifact_maps_source_offset_to_c_row(self) -> None:
        library = _file_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.bin"
            path.write_bytes(b"\x4e\x75\x4e\x75")
            artifact = ctypes.c_void_p()
            error = ctypes.c_void_p()
            create_result = library.platform_file_facts_v2_listing_artifact_raw_path_create(
                b"amiga-raw",
                str(path).encode("utf-8"),
                0,
                0,
                0,
                b"",
                b"",
                ctypes.byref(artifact),
                ctypes.byref(error),
            )
            try:
                error_text = ctypes.string_at(error).decode("utf-8") if error.value else ""
                self.assertEqual(create_result, 0, error_text)
                self.assertTrue(artifact.value)
                row = ctypes.c_void_p()
                try:
                    row_result = library.platform_file_facts_v2_listing_artifact_source_offset_row_json_alloc(
                        artifact,
                        1,
                        0,
                        0,
                        ctypes.byref(row),
                    )
                    row_text = ctypes.string_at(row).decode("utf-8") if row.value else ""
                    self.assertEqual(row_result, 0, row_text)
                finally:
                    if row.value:
                        library.platform_file_free_text(row)
            finally:
                if error.value:
                    library.platform_file_free_text(error)
                if artifact.value:
                    library.platform_file_facts_v2_listing_artifact_destroy(artifact)

        payload = json.loads(row_text)
        self.assertTrue(payload["found"])
        self.assertIsInstance(payload["row_index"], int)
        rows = payload["listing"]["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["start_offset"], 0)
        self.assertEqual(payload["profile"]["generation"], "facts_v2_listing_artifact_source_offset_row")

    def test_platform_file_listing_artifact_supports_raw_binary_targets(self) -> None:
        library = _file_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.bin"
            path.write_bytes(b"\x4e\x75")
            artifact = ctypes.c_void_p()
            error = ctypes.c_void_p()
            create_result = library.platform_file_facts_v2_listing_artifact_raw_path_create(
                b"amiga-raw",
                str(path).encode("utf-8"),
                0,
                0,
                0,
                b"",
                b"",
                ctypes.byref(artifact),
                ctypes.byref(error),
            )
            try:
                error_text = ctypes.string_at(error).decode("utf-8") if error.value else ""
                self.assertEqual(create_result, 0, error_text)
                self.assertTrue(artifact.value)
                window = ctypes.c_void_p()
                try:
                    window_result = library.platform_file_facts_v2_listing_artifact_window_json_alloc(
                        artifact,
                        0,
                        4,
                        ctypes.byref(window),
                    )
                    window_text = ctypes.string_at(window).decode("utf-8") if window.value else ""
                    self.assertEqual(window_result, 0, window_text)
                finally:
                    if window.value:
                        library.platform_file_free_text(window)
            finally:
                if error.value:
                    library.platform_file_free_text(error)
                if artifact.value:
                    library.platform_file_facts_v2_listing_artifact_destroy(artifact)

        payload = json.loads(window_text)
        self.assertEqual(payload["profile"]["generation"], "facts_v2_listing_artifact_window")
        self.assertTrue(payload["listing"]["rows"])

    def test_platform_file_analysis_keeps_fallthrough_after_trap(self) -> None:
        library = _file_library()
        sample = make_synthetic_hunkexe(code_data=b"\x4E\x4F\x4E\x75")
        sample_buf = (ctypes.c_uint8 * len(sample)).from_buffer_copy(sample)
        policy = _analysis_policy(library)
        try:
            result = library.platform_file_facts_v2_analysis_buffer_json(
                b"amiga-hunk",
                sample_buf,
                len(sample),
                policy,
            )
            self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
            try:
                analysis = json.loads(ctypes.cast(result.text, ctypes.c_char_p).value.decode("utf-8"))
            finally:
                library.platform_file_free_text(result.text)
        finally:
            library.platform_file_analysis_policy_destroy(policy)
        code_section = analysis["sections"][0]
        self.assertEqual(code_section["block_count"], 1)
        self.assertEqual(code_section["blocks"][0]["start_offset"], 0)
        self.assertEqual(code_section["blocks"][0]["end_offset"], 4)
        self.assertEqual(code_section["edge_count"], 1)
        self.assertEqual(code_section["edges"][0]["source_offset"], 2)
        self.assertEqual(code_section["edges"][0]["kind"], 5)

    def test_assembler_source_ir_render_preserves_source_names_when_generated_names_disabled(self) -> None:
        library = _asm_library()
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.s"
            path.write_text("SECTION code,code\nstart:\n    bra.b start\n", encoding="utf-8")
            policy = _default_policy()
            policy.presentation.prefer_generated_names = 0
            parse_result = library.m68k_source_ir_parse_file(
                str(path).encode("utf-8"),
                str(AMIGA_INCLUDE_DIR).encode("utf-8"),
                0,
            )
            self.assertFalse(_diag_has_errors(parse_result.diagnostics), _diag_message(parse_result.diagnostics))
            source_file = parse_result.source_file
            try:
                render_result = library.m68k_source_ir_render_with_policy(
                    ctypes.byref(source_file),
                    ctypes.byref(policy),
                )
                self.assertFalse(_diag_has_errors(render_result.diagnostics), _diag_message(render_result.diagnostics))
                try:
                    text = ctypes.cast(render_result.text, ctypes.c_char_p).value.decode("utf-8")
                finally:
                    library.m68k_free_text(render_result.text)
            finally:
                library.m68k_source_ir_free(ctypes.byref(source_file))

        self.assertIn("start:", text)
        self.assertNotIn("L_0000:", text)


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_HEAVY_UNIT_TESTS") == "1":
        return tests
    return unittest.TestSuite()
