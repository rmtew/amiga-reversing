from __future__ import annotations

import json
import os
import unittest
import ctypes
from functools import lru_cache
from pathlib import Path

from src.tests._build_helpers import prepare_test_dll
from src.tests._build_helpers import require_built_tools
from src.tests._real_fixture_helpers import analyze_real_file

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
ASM_DLL = BUILD_DIR / "m68k_assembler_lib.dll"
FILE_DLL = BUILD_DIR / "platform_file_lib.dll"


def u32(value: int) -> bytes:
    return value.to_bytes(4, "big", signed=False)


@lru_cache(maxsize=1)
def _assembler_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(ASM_DLL)))

    class M68kAsmOptions(ctypes.Structure):
        _fields_ = [("target_cpu", ctypes.c_uint8), ("input_mode", ctypes.c_uint8)]

    library._m68k_asm_options_type = M68kAsmOptions
    library.m68k_assemble.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(M68kAsmOptions),
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]
    library.m68k_assemble.restype = ctypes.c_int
    return library


@lru_cache(maxsize=1)
def _platform_file_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(FILE_DLL)))

    class M68kAnalysisPolicy(ctypes.Structure):
        _fields_ = [("max_cpu", ctypes.c_uint8)]

    library._m68k_analysis_policy_type = M68kAnalysisPolicy
    library.platform_file_analyze_buffer_json.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.POINTER(M68kAnalysisPolicy),
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]
    library.platform_file_analyze_buffer_json.restype = ctypes.c_int
    library.platform_file_free_text.argtypes = [ctypes.c_char_p]
    library.platform_file_free_text.restype = None
    return library


def _assemble_line_hex(cpu: str, text: str) -> bytes:
    cpu_codes = {"68000": 0, "68010": 1, "68020": 2, "68030": 3, "68040": 4, "68060": 5}
    library = _assembler_library()
    options = library._m68k_asm_options_type(cpu_codes[cpu], 0)
    out_buf = (ctypes.c_ubyte * 64)()
    error_buf = ctypes.create_string_buffer(256)
    byte_count = ctypes.c_size_t()
    result = library.m68k_assemble(
        text.encode("ascii"),
        ctypes.byref(options),
        out_buf,
        len(out_buf),
        ctypes.byref(byte_count),
        error_buf,
        len(error_buf),
    )
    if result != 0:
        raise AssertionError(error_buf.value.decode("utf-8"))
    return bytes(out_buf[:byte_count.value])


def _make_single_code_hunkexe(code_data: bytes, reloc_offsets: list[int]) -> bytes:
    hunk_header = 1011
    hunk_code = 1001
    hunk_reloc32 = 1004
    hunk_end = 1010
    payload = bytearray()
    payload += u32(hunk_header)
    payload += u32(0)
    payload += u32(1)
    payload += u32(0)
    payload += u32(0)
    payload += u32((len(code_data) + 3) // 4)
    payload += u32(hunk_code)
    payload += u32((len(code_data) + 3) // 4)
    payload += code_data.ljust(((len(code_data) + 3) // 4) * 4, b"\x00")
    if reloc_offsets:
        payload += u32(hunk_reloc32)
        payload += u32(len(reloc_offsets))
        payload += u32(0)
        for offset in reloc_offsets:
            payload += u32(offset)
        payload += u32(0)
    payload += u32(hunk_end)
    return bytes(payload)


class M68kSimulatorAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_built_tools()

    def _analyze_bytes(self, payload: bytes) -> dict[str, object]:
        library = _platform_file_library()
        data = (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload)
        out_json = ctypes.c_char_p()
        error_buf = ctypes.create_string_buffer(256)
        result = library.platform_file_analyze_buffer_json(
            b"amiga-hunk",
            data,
            len(payload),
            None,
            ctypes.byref(out_json),
            error_buf,
            len(error_buf),
        )
        self.assertEqual(result, 0, error_buf.value.decode("utf-8"))
        try:
            return json.loads(ctypes.string_at(out_json).decode("utf-8"))
        finally:
            library.platform_file_free_text(out_json)

    def _analyze_file(self, path: Path) -> dict[str, object]:
        return analyze_real_file("amiga-hunk", str(path))

    def test_analysis_discovers_jump_table_targets(self) -> None:
        code = (
            _assemble_line_hex("68000", "lea $0008(pc),a0")
            + _assemble_line_hex("68000", "movea.l 0(a0,d0.w),a0")
            + _assemble_line_hex("68000", "jmp (a0)")
            + u32(18)
            + u32(20)
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [10, 14])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        self.assertEqual(code_section["block_count"], 3)
        self.assertEqual(code_section["edge_count"], 4)
        self.assertEqual(code_section["blocks"][1]["start_offset"], 18)
        self.assertEqual(code_section["blocks"][2]["start_offset"], 20)

    def test_analysis_discovers_word_offset_dispatch_targets(self) -> None:
        code = (
            _assemble_line_hex("68000", "lea $000c(pc),a1")
            + _assemble_line_hex("68000", "add.w d1,d1")
            + _assemble_line_hex("68000", "move.w $0008(a1,d1.w),d1")
            + _assemble_line_hex("68000", "jsr $0(a1,d1.w)")
            + _assemble_line_hex("68000", "bra.s $000c")
            + b"\x00" * 8
            + (12).to_bytes(2, "big", signed=True)
            + _assemble_line_hex("68000", "rts")
        )
        analysis = self._analyze_bytes(_make_single_code_hunkexe(code, []))
        code_section = analysis["sections"][0]
        call_targets = {edge["target_offset"] for edge in code_section["edges"] if edge["kind"] == 3}
        self.assertIn(26, call_targets)

    def test_analysis_resolves_real_genam_word_offset_dispatch_call(self) -> None:
        analysis = self._analyze_file(ROOT / "bin" / "GenAm")
        code_section = analysis["sections"][0]
        call_targets = {
            edge["target_offset"]
            for edge in code_section["edges"]
            if edge["source_offset"] == 4156 and edge["kind"] == 3
        }
        self.assertGreaterEqual(len(call_targets), 16)
        self.assertTrue({4176, 4344, 4372, 4474, 5322}.issubset(call_targets))
        self.assertFalse({4792, 8884, 8886, 9398}.intersection(call_targets))

    def test_analysis_resolves_real_genam_entry_relative_word_dispatch_jump(self) -> None:
        analysis = self._analyze_file(ROOT / "bin" / "GenAm")
        code_section = analysis["sections"][0]
        jump_edges = [edge for edge in code_section["edges"] if edge["source_offset"] == 0x3BC8]
        jump_targets = {edge["target_offset"] for edge in jump_edges if edge["kind"] == 4}
        self.assertGreaterEqual(len(jump_targets), 20)
        self.assertTrue({0x3D00, 0x3C86, 0x3C5C, 0x3C68, 0x3E98}.issubset(jump_targets))
        self.assertFalse(any(edge["kind"] == 5 for edge in jump_edges))

    def test_analysis_tracks_pointer_copy_before_indirect_jump(self) -> None:
        code = (
            _assemble_line_hex("68000", "lea $0008(pc),a0")
            + _assemble_line_hex("68000", "movea.l (a0),a1")
            + _assemble_line_hex("68000", "movea.l a1,a0")
            + _assemble_line_hex("68000", "jmp (a0)")
            + u32(14)
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [10])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        self.assertEqual(code_section["block_count"], 2)
        self.assertEqual(code_section["edges"][0]["target_offset"], 14)

    def test_analysis_handles_interleaved_pointer_and_data_entries(self) -> None:
        code = (
            _assemble_line_hex("68000", "lea $0008(pc),a0")
            + _assemble_line_hex("68000", "movea.l 0(a0,d0.w),a0")
            + _assemble_line_hex("68000", "jmp (a0)")
            + u32(22)
            + u32(0x12345678)
            + u32(24)
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [10, 18])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        targets = {edge["target_offset"] for edge in code_section["edges"] if edge["kind"] == 4}
        self.assertEqual(targets, {22, 24})

    def test_analysis_ignores_non_fixup_in_range_longwords_in_table_summary(self) -> None:
        code = (
            _assemble_line_hex("68000", "lea $0008(pc),a0")
            + _assemble_line_hex("68000", "movea.l 0(a0,d0.w),a0")
            + _assemble_line_hex("68000", "jmp (a0)")
            + u32(22)
            + u32(12)
            + u32(24)
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [10, 18])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        targets = {edge["target_offset"] for edge in code_section["edges"] if edge["kind"] == 4}
        self.assertEqual(targets, {22, 24})

    def test_analysis_discovers_contiguous_table_entries_beyond_old_window(self) -> None:
        table_entries = b"".join(u32(78 + i * 2) for i in range(17))
        code = (
            _assemble_line_hex("68000", "lea $0008(pc),a0")
            + _assemble_line_hex("68000", "movea.l 0(a0,d0.w),a0")
            + _assemble_line_hex("68000", "jmp (a0)")
            + table_entries
            + b"".join(_assemble_line_hex("68000", "rts") for _ in range(17))
        )
        payload = _make_single_code_hunkexe(code, [10 + i * 4 for i in range(17)])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        targets = {edge["target_offset"] for edge in code_section["edges"] if edge["kind"] == 4}
        self.assertIn(110, targets)

    def test_analysis_preserves_table_region_when_joined_with_concrete_pointer(self) -> None:
        code = (
            _assemble_line_hex("68000", "bne 12")
            + _assemble_line_hex("68000", "lea $0012(pc),a0")
            + _assemble_line_hex("68000", "movea.l (a0),a0")
            + _assemble_line_hex("68000", "bra 10")
            + _assemble_line_hex("68000", "lea $0008(pc),a0")
            + _assemble_line_hex("68000", "movea.l 0(a0,d0.w),a0")
            + _assemble_line_hex("68000", "jmp (a0)")
            + u32(32)
            + u32(34)
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [24, 28])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        targets = {edge["target_offset"] for edge in code_section["edges"] if edge["kind"] == 4}
        self.assertEqual(targets, {22, 32, 34})

    def test_analysis_tracks_movem_loaded_pointer_to_indirect_jump(self) -> None:
        code = (
            _assemble_line_hex("68000", "lea $000a(pc),a0")
            + _assemble_line_hex("68000", "movem.l (a0),a1")
            + _assemble_line_hex("68000", "movea.l a1,a0")
            + _assemble_line_hex("68000", "jmp (a0)")
            + u32(16)
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [12])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        self.assertEqual(code_section["block_count"], 2)
        self.assertEqual(code_section["edges"][0]["target_offset"], 16)

    def test_analysis_tracks_movem_written_pointer_to_indirect_jump(self) -> None:
        code = (
            _assemble_line_hex("68000", "lea $000e(pc),a0")
            + _assemble_line_hex("68000", "lea $000e(pc),a1")
            + _assemble_line_hex("68000", "movem.l a1,(a0)")
            + _assemble_line_hex("68000", "movea.l (a0),a0")
            + _assemble_line_hex("68000", "jmp (a0)")
            + u32(0)
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        self.assertEqual(code_section["block_count"], 2)
        self.assertEqual(code_section["edges"][0]["target_offset"], 20)

    def test_analysis_respects_known_chk2_trap_stop(self) -> None:
        code = (
            _assemble_line_hex("68020", "moveq #9,d0")
            + _assemble_line_hex("68020", "lea $0008(pc),a0")
            + _assemble_line_hex("68020", "chk2.w (a0),d0")
            + _assemble_line_hex("68020", "rts")
            + b"\x00\x02\x00\x08"
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        self.assertEqual(code_section["block_count"], 1)
        self.assertEqual(code_section["edge_count"], 1)
        self.assertEqual(code_section["edges"][0]["target_offset"], 4294967295)

    def test_analysis_uses_cmp2_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68020", "moveq #9,d0")
            + _assemble_line_hex("68020", "lea $000c(pc),a0")
            + _assemble_line_hex("68020", "cmp2.w (a0),d0")
            + _assemble_line_hex("68020", "bcs 2")
            + _assemble_line_hex("68020", "rts")
            + _assemble_line_hex("68020", "rts")
            + b"\x00\x02\x00\x08"
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_bftst_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68020", "lea $0008(pc),a0")
            + _assemble_line_hex("68020", "bftst (a0){0:8}")
            + _assemble_line_hex("68020", "beq 2")
            + _assemble_line_hex("68020", "rts")
            + _assemble_line_hex("68020", "rts")
            + b"\x00"
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_tst_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "tst.l d0")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_cmp_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #1,d0")
            + _assemble_line_hex("68000", "cmp.l d0,d0")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_does_not_prune_branch_after_unknown_register_join(self) -> None:
        code = (
            _assemble_line_hex("68000", "beq 6")
            + _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "bra 2")
            + _assemble_line_hex("68000", "tst.b d0")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        join_branch_edges = [edge for edge in code_section["edges"] if edge["source_offset"] == 12 and edge["kind"] == 2]
        join_fallthrough_edges = [edge for edge in code_section["edges"] if edge["source_offset"] == 12 and edge["kind"] == 1]
        self.assertGreaterEqual(len(join_branch_edges), 1)
        self.assertGreaterEqual(len(join_fallthrough_edges), 1)

    def test_analysis_does_not_prune_branch_after_unknown_sr_join(self) -> None:
        code = (
            _assemble_line_hex("68000", "beq 8")
            + _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "cmp.b #0,d0")
            + _assemble_line_hex("68000", "bra 2")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        join_branch_edges = [edge for edge in code_section["edges"] if edge["source_offset"] == 14 and edge["kind"] == 2]
        join_fallthrough_edges = [edge for edge in code_section["edges"] if edge["source_offset"] == 14 and edge["kind"] == 1]
        self.assertGreaterEqual(len(join_branch_edges), 1)
        self.assertGreaterEqual(len(join_fallthrough_edges), 1)

    def test_analysis_uses_shift_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #1,d0")
            + _assemble_line_hex("68000", "lsr.l #1,d0")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_btst_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "btst #0,d0")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_logic_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "ori.l #1,d0")
            + _assemble_line_hex("68000", "bne 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_clear_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #1,d0")
            + _assemble_line_hex("68000", "clr.l d0")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_unary_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "not.l d0")
            + _assemble_line_hex("68000", "bne 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_rotate_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "ror.l #1,d0")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_tas_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "tas d0")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_bset_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "bset #0,d0")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_bfextu_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68020", "moveq #0,d0")
            + _assemble_line_hex("68020", "bfextu d0{0:8},d1")
            + _assemble_line_hex("68020", "beq 2")
            + _assemble_line_hex("68020", "rts")
            + _assemble_line_hex("68020", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_bfset_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68020", "moveq #0,d0")
            + _assemble_line_hex("68020", "bfset d0{0:8}")
            + _assemble_line_hex("68020", "beq 2")
            + _assemble_line_hex("68020", "rts")
            + _assemble_line_hex("68020", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_mulu_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68000", "moveq #0,d0")
            + _assemble_line_hex("68000", "moveq #5,d1")
            + _assemble_line_hex("68000", "mulu.w d0,d1")
            + _assemble_line_hex("68000", "beq 2")
            + _assemble_line_hex("68000", "rts")
            + _assemble_line_hex("68000", "rts")
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)

    def test_analysis_uses_cas_flags_to_prune_conditional_branch(self) -> None:
        code = (
            _assemble_line_hex("68020", "moveq #0,d0")
            + _assemble_line_hex("68020", "moveq #1,d1")
            + _assemble_line_hex("68020", "lea $000c(pc),a0")
            + _assemble_line_hex("68020", "cas.w d0,d1,(a0)")
            + _assemble_line_hex("68020", "beq 2")
            + _assemble_line_hex("68020", "rts")
            + _assemble_line_hex("68020", "rts")
            + b"\x00\x00"
        )
        payload = _make_single_code_hunkexe(code, [])
        analysis = self._analyze_bytes(payload)
        code_section = analysis["sections"][0]
        branch_edges = [edge for edge in code_section["edges"] if edge["kind"] == 2]
        fallthrough_edges = [edge for edge in code_section["edges"] if edge["kind"] == 1]
        self.assertEqual(len(branch_edges), 1)
        self.assertEqual(len(fallthrough_edges), 0)


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_HEAVY_UNIT_TESTS") == "1":
        return tests
    return unittest.TestSuite()
