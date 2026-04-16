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


class M68kAnalysisPolicy(ctypes.Structure):
    _fields_ = [
        ("max_cpu", ctypes.c_uint8),
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


class PlatformFileSourceIrResult(ctypes.Structure):
    _fields_ = [
        ("source_file", M68kSourceFileIR),
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
        ctypes.c_int,
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
    library.platform_file_to_ir_with_policy.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(M68kRenderPolicy),
        ctypes.POINTER(M68kAnalysisPolicy),
    ]
    library.platform_file_to_ir_with_policy.restype = PlatformFileSourceIrResult
    library.platform_file_to_ir_buffer_with_policy.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(M68kRenderPolicy),
        ctypes.POINTER(M68kAnalysisPolicy),
    ]
    library.platform_file_to_ir_buffer_with_policy.restype = PlatformFileSourceIrResult
    library.platform_file_render_ir_with_policy.argtypes = [
        ctypes.POINTER(M68kSourceFileIR),
        ctypes.POINTER(M68kRenderPolicy),
    ]
    library.platform_file_render_ir_with_policy.restype = PlatformFileTextResult
    library.platform_file_analyze_path_json.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(M68kAnalysisPolicy),
    ]
    library.platform_file_analyze_path_json.restype = PlatformFileTextResult
    library.platform_file_analyze_buffer_json.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(M68kAnalysisPolicy),
    ]
    library.platform_file_analyze_buffer_json.restype = PlatformFileTextResult
    library.platform_file_source_ir_free.argtypes = [ctypes.POINTER(M68kSourceFileIR)]
    library.platform_file_source_ir_free.restype = None
    library.platform_file_free_text.argtypes = [ctypes.c_void_p]
    library.platform_file_free_text.restype = None
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


def _analysis_policy(max_cpu: int = 5) -> M68kAnalysisPolicy:
    policy = M68kAnalysisPolicy()
    policy.max_cpu = max_cpu
    return policy


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

    def test_platform_file_analysis_reports_cfg_for_certain_code(self) -> None:
        library = _file_library()
        sample = make_synthetic_hunkexe()
        sample_buf = (ctypes.c_uint8 * len(sample)).from_buffer_copy(sample)
        result = library.platform_file_analyze_buffer_json(
            b"amiga-hunk",
            sample_buf,
            len(sample),
            ctypes.byref(_analysis_policy()),
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        try:
            analysis = json.loads(ctypes.cast(result.text, ctypes.c_char_p).value.decode("utf-8"))
        finally:
            library.platform_file_free_text(result.text)
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

    def test_platform_file_analysis_keeps_fallthrough_after_trap(self) -> None:
        library = _file_library()
        sample = make_synthetic_hunkexe(code_data=b"\x4E\x4F\x4E\x75")
        sample_buf = (ctypes.c_uint8 * len(sample)).from_buffer_copy(sample)
        result = library.platform_file_analyze_buffer_json(
            b"amiga-hunk",
            sample_buf,
            len(sample),
            ctypes.byref(_analysis_policy()),
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        try:
            analysis = json.loads(ctypes.cast(result.text, ctypes.c_char_p).value.decode("utf-8"))
        finally:
            library.platform_file_free_text(result.text)
        code_section = analysis["sections"][0]
        self.assertEqual(code_section["block_count"], 1)
        self.assertEqual(code_section["blocks"][0]["start_offset"], 0)
        self.assertEqual(code_section["blocks"][0]["end_offset"], 4)
        self.assertEqual(code_section["edge_count"], 1)
        self.assertEqual(code_section["edges"][0]["source_offset"], 2)
        self.assertEqual(code_section["edges"][0]["kind"], 5)

    def test_platform_file_ir_render_respects_generated_name_policy(self) -> None:
        library = _file_library()
        sample = make_synthetic_hunkexe()
        sample_buf = (ctypes.c_uint8 * len(sample)).from_buffer_copy(sample)
        default_policy = _default_policy()
        result = library.platform_file_to_ir_buffer_with_policy(
            b"amiga-hunk",
            sample_buf,
            len(sample),
            ctypes.byref(default_policy),
            ctypes.byref(_analysis_policy()),
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        source_file = result.source_file
        try:
            render_result = library.platform_file_render_ir_with_policy(
                ctypes.byref(source_file),
                ctypes.byref(default_policy),
            )
            self.assertFalse(_diag_has_errors(render_result.diagnostics), _diag_message(render_result.diagnostics))
            try:
                default_text = ctypes.cast(render_result.text, ctypes.c_char_p).value.decode("utf-8")
            finally:
                library.platform_file_free_text(render_result.text)
        finally:
            library.platform_file_source_ir_free(ctypes.byref(source_file))

        self.assertIn("loc_0000:", default_text)

        fallback_policy = _default_policy()
        fallback_policy.presentation.prefer_generated_names = 0
        result = library.platform_file_to_ir_buffer_with_policy(
            b"amiga-hunk",
            sample_buf,
            len(sample),
            ctypes.byref(fallback_policy),
            ctypes.byref(_analysis_policy()),
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        source_file = result.source_file
        try:
            render_result = library.platform_file_render_ir_with_policy(
                ctypes.byref(source_file),
                ctypes.byref(fallback_policy),
            )
            self.assertFalse(_diag_has_errors(render_result.diagnostics), _diag_message(render_result.diagnostics))
            try:
                fallback_text = ctypes.cast(render_result.text, ctypes.c_char_p).value.decode("utf-8")
            finally:
                library.platform_file_free_text(render_result.text)
        finally:
            library.platform_file_source_ir_free(ctypes.byref(source_file))

        self.assertIn("L_0000:", fallback_text)
        self.assertNotIn("loc_0000:", fallback_text)

    def test_platform_file_ir_render_emits_minimum_os_version_comment(self) -> None:
        library = _file_library()
        sample = make_synthetic_hunkexe()
        sample_buf = (ctypes.c_uint8 * len(sample)).from_buffer_copy(sample)
        policy = _default_policy()
        policy.os.compatibility_kind = M68K_OS_COMPATIBILITY_AMIGA
        policy.os.compatibility_level = AMIGA_OS_COMPAT_VERSION_1_3
        result = library.platform_file_to_ir_buffer_with_policy(
            b"amiga-hunk",
            sample_buf,
            len(sample),
            ctypes.byref(policy),
            ctypes.byref(_analysis_policy()),
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        source_file = result.source_file
        try:
            render_result = library.platform_file_render_ir_with_policy(
                ctypes.byref(source_file),
                ctypes.byref(policy),
            )
            self.assertFalse(_diag_has_errors(render_result.diagnostics), _diag_message(render_result.diagnostics))
            try:
                text = ctypes.cast(render_result.text, ctypes.c_char_p).value.decode("utf-8")
            finally:
                library.platform_file_free_text(render_result.text)
        finally:
            library.platform_file_source_ir_free(ctypes.byref(source_file))

        self.assertTrue(text.startswith("; Minimum OS version: 1.3\n"), text)

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
