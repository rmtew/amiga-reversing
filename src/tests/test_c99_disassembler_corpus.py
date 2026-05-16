from __future__ import annotations

import ctypes
import importlib.util
import re
import sys
import unittest
from functools import lru_cache
from pathlib import Path

from src.tests._build_helpers import prepare_test_dll
from src.tests._build_helpers import require_built_tools
from src.tests._oracle_matrix_helpers import unsupported_mmu_round_trip_mnemonics_upper

ROOT = Path(__file__).resolve().parents[2]
ASM_DLL_PATH = ROOT / "src" / "build" / "m68k_assembler_lib.dll"
DISASM_DLL_PATH = ROOT / "src" / "build" / "m68k_disassembler_lib.dll"
CORPUS_GENERATOR_PATH = ROOT / "src" / "scripts" / "generate_c99_assembler_corpus.py"
ASM_TABLES_HEADER_PATH = ROOT / "src" / "generated" / "m68k_asm_tables.h"
FORM_MODEL_HEADER_PATH = ROOT / "src" / "generated" / "m68k_form_model.h"

CPU_CODES = {
    "68000": 0,
    "68010": 1,
    "68020": 2,
    "68030": 3,
    "68040": 4,
    "68060": 5,
}
CPU_NAMES = ("68000", "68010", "68020", "68030", "68040", "68060")
TARGET_LABEL_RE = re.compile(r"\btarget\b")
UNSUPPORTED_MMU_ROUND_TRIP_MNEMONICS = unsupported_mmu_round_trip_mnemonics_upper()
UNSUPPORTED_CANONICAL_PARITY_MNEMONICS = UNSUPPORTED_MMU_ROUND_TRIP_MNEMONICS | {
    "CPRESTORE",
    "CPSAVE",
    "PFLUSH",
}
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


class M68kDisasmInfoResult(ctypes.Structure):
    _fields_ = [
        ("byte_count", ctypes.c_size_t),
        ("asm_form_index", ctypes.c_uint16),
        ("canonical_form_id", ctypes.c_uint16),
        ("mnemonic_id", ctypes.c_uint8),
        ("target_cpu", ctypes.c_uint8),
        ("mnemonic", ctypes.c_char * 32),
        ("size_suffix", ctypes.c_char),
        ("operand_count", ctypes.c_size_t),
        ("diagnostics", M68kDiagList),
    ]


class M68kAssembleResult(ctypes.Structure):
    _fields_ = [
        ("byte_count", ctypes.c_size_t),
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


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _asm_form_none() -> int:
    text = ASM_TABLES_HEADER_PATH.read_text()
    match = re.search(r"M68K_ASM_FORM_COUNT\s*=\s*(\d+)", text)
    assert match is not None
    return int(match.group(1))


@lru_cache(maxsize=None)
def _canonical_form_id_for_syntax(syntax: str) -> int:
    text = FORM_MODEL_HEADER_PATH.read_text()
    match = re.search(rf"\{{\s+(\d+)u,\s+\d+u,\s+\"[^\"]+\",\s+\"[^\"]+\",\s+\d+u,\s+\"{re.escape(syntax)}\",", text)
    assert match is not None
    return int(match.group(1))


@lru_cache(maxsize=1)
def _corpus_generator():
    return _load_module(CORPUS_GENERATOR_PATH, "src_c99_disassembler_test_corpus_generator")


@lru_cache(maxsize=None)
def _generate_cases_for_cpu(cpu_name: str):
    return tuple(_corpus_generator().generate_cases(cpu_name))


@lru_cache(maxsize=None)
def _cases_by_first_line(cpu_name: str):
    return {case.asm_lines[0]: case for case in _generate_cases_for_cpu(cpu_name)}


@lru_cache(maxsize=1)
def _disasm_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(DISASM_DLL_PATH)))
    library.m68k_disassemble_one_text_for_cpu.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.c_uint8,
    ]
    library.m68k_disassemble_one_text_for_cpu.restype = M68kDisasmTextResult
    library.m68k_disassemble_one_info_for_cpu.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.c_uint8,
    ]
    library.m68k_disassemble_one_info_for_cpu.restype = M68kDisasmInfoResult
    return library


@lru_cache(maxsize=1)
def _assembler_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(ASM_DLL_PATH)))

    class M68kAsmOptions(ctypes.Structure):
        _fields_ = [("target_cpu", ctypes.c_uint8), ("input_mode", ctypes.c_uint8)]

    library._m68k_asm_options_type = M68kAsmOptions
    library.m68k_assemble.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(M68kAsmOptions),
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
    ]
    library.m68k_assemble.restype = M68kAssembleResult
    return library


def _disassemble_for_cpu(data: bytes, cpu_name: str) -> tuple[str, int]:
    library = _disasm_library()
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    result = library.m68k_disassemble_one_text_for_cpu(
        buffer,
        len(data),
        CPU_CODES[cpu_name],
    )
    if _diag_has_errors(result.diagnostics):
        raise AssertionError(_diag_message(result.diagnostics))
    return result.text.decode("utf-8"), int(result.byte_count)


def _disassemble_info_for_cpu(data: bytes, cpu_name: str) -> M68kDisasmInfoResult:
    library = _disasm_library()
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    result = library.m68k_disassemble_one_info_for_cpu(
        buffer,
        len(data),
        CPU_CODES[cpu_name],
    )
    if _diag_has_errors(result.diagnostics) or result.byte_count == 0:
        raise AssertionError(_diag_message(result.diagnostics))
    return result


@lru_cache(maxsize=None)
def _assemble_text(text: str, cpu_name: str, input_mode: int) -> bytes:
    library = _assembler_library()
    options = library._m68k_asm_options_type(CPU_CODES[cpu_name], input_mode)
    out_buf = (ctypes.c_ubyte * 512)()
    result = library.m68k_assemble(
        text.encode("ascii"),
        ctypes.byref(options),
        out_buf,
        len(out_buf),
    )
    if _diag_has_errors(result.diagnostics):
        raise AssertionError(_diag_message(result.diagnostics))
    return bytes(out_buf[:result.byte_count])


def _assemble_line_bytes(text: str, cpu_name: str) -> bytes:
    return _assemble_text(text, cpu_name, 0)


def _assemble_source_bytes(text: str, cpu_name: str) -> bytes:
    return _assemble_text(text, cpu_name, 1)


def _case_original_bytes(case) -> bytes:
    full = bytes.fromhex(str(case.expected_hex))
    encoded_size = int(case.size)
    return full[:encoded_size] if encoded_size != 0 else full


def _round_trip_case(case, cpu_name: str) -> None:
    if str(case.mnemonic).upper() in UNSUPPORTED_MMU_ROUND_TRIP_MNEMONICS:
        raise unittest.SkipTest(f"unsupported MMU round-trip mnemonic: {case.mnemonic}")
    original = _case_original_bytes(case)
    info = _disassemble_info_for_cpu(original, cpu_name)
    rendered, byte_count = _disassemble_for_cpu(original, cpu_name)
    info_mnemonic = bytes(info.mnemonic).split(b"\0", 1)[0].decode("ascii")
    if info.byte_count != byte_count:
        raise AssertionError(f"{case.case_id}: info byte_count {info.byte_count} != text byte_count {byte_count}")
    if info.mnemonic_id == 0:
        raise AssertionError(f"{case.case_id}: decoded mnemonic_id is NONE for {rendered}")
    if info.canonical_form_id == 0:
        raise AssertionError(f"{case.case_id}: decoded canonical_form_id is NONE for {rendered}")
    if str(case.mnemonic).upper() not in UNSUPPORTED_CANONICAL_PARITY_MNEMONICS and (
        info.canonical_form_id != case.canonical_form_id
    ):
        raise AssertionError(
            f"{case.case_id}: canonical form mismatch for {rendered}\n"
            f"asm={' | '.join(case.asm_lines)}\n"
            f"expected_id={case.canonical_form_id} decoded_id={info.canonical_form_id}\n"
            f"bytes={original[:byte_count].hex()}"
        )
    if not info_mnemonic:
        raise AssertionError(f"{case.case_id}: decoded mnemonic text is empty")
    if TARGET_LABEL_RE.search(rendered):
        trailing_lines = "\n".join(case.asm_lines[1:])
        rebuilt_source = rendered if not trailing_lines else rendered + "\n" + trailing_lines
        rebuilt = _assemble_source_bytes(rebuilt_source, cpu_name)
    else:
        rebuilt = _assemble_line_bytes(rendered, cpu_name)
    if byte_count <= 0 or byte_count > len(original):
        raise AssertionError(f"{case.case_id}: invalid byte_count {byte_count} for {len(original)} bytes")
    if rebuilt[:byte_count] != original[:byte_count]:
        raise AssertionError(
            f"{case.case_id}: round-trip mismatch\n"
            f"asm={' | '.join(case.asm_lines)}\n"
            f"rendered={rendered}\n"
            f"expected={original.hex()}\n"
            f"rebuilt={rebuilt[:byte_count].hex()}"
        )


class C99DisassemblerCorpusTests(unittest.TestCase):
    def _bulk_round_trip_corpus_by_cpu(self) -> None:
        for cpu_name in CPU_NAMES:
            with self.subTest(cpu=cpu_name):
                for case in _generate_cases_for_cpu(cpu_name):
                    with self.subTest(cpu=cpu_name, case=str(case.case_id)):
                        if str(case.mnemonic).upper() in UNSUPPORTED_MMU_ROUND_TRIP_MNEMONICS:
                            continue
                        _round_trip_case(case, cpu_name)

    def _pc_relative_indexed_representatives_round_trip(self) -> None:
        cases_68020 = _cases_by_first_line("68020")
        samples = (
            "lea target(pc,d1.w),a0",
            "pea target(pc,a3.l)",
            "jmp target(pc,d1.w)",
            "jsr target(pc,a3.l)",
            "add.w target(pc,d1.w),d0",
            "chk2.b target(pc,a3.l),d7",
            "cmp2.b target(pc,d1.w),a0",
            "callm #1,target(pc,a3.l)",
            "movem.l target(pc,d1.w),d0/d7/a0/a7",
        )
        for source_text in samples:
            case = cases_68020[source_text]
            with self.subTest(case=source_text):
                _round_trip_case(case, "68020")

    def _pc_relative_full_extension_representatives_round_trip(self) -> None:
        cases_68020 = _cases_by_first_line("68020")
        samples = (
            "move.b target(pc,d1.w),$10(a0,d1.w){full}",
            "move.b target(pc,d1.w),$10(a0,d1.w){full,bs}",
            "move.b target(pc,d1.w),$10(a0,d1.w){full,is}",
            "move.b target(pc,d1.w),$10(a0,d1.w){full,bdw=$1234,odw=$5678,iis=3}",
            "move.b target(pc,a3.l),$20(a7,a3.l){full}",
            "move.w target(pc,d1.w),$10(a0,d1.w){full}",
            "move.l target(pc,a3.l),$20(a7,a3.l){full}",
        )
        for source_text in samples:
            case = cases_68020[source_text]
            with self.subTest(case=source_text):
                _round_trip_case(case, "68020")

    def _move16_round_trip_representatives(self) -> None:
        syntax_prefixes = (
            "move16 (a0)+,(",
            "move16 $00123456.l,(",
            "move16 $00123456.l,(a0)+",
            "move16 (a0),$",
            "move16 (a0)+,$",
        )
        cases = _generate_cases_for_cpu("68040")
        for prefix in syntax_prefixes:
            case = next(case for case in cases if case.asm_lines[0].startswith(prefix))
            with self.subTest(line=case.asm_lines[0]):
                _round_trip_case(case, "68040")

    def _cache_control_round_trip_representatives(self) -> None:
        cases_68040 = _cases_by_first_line("68040")
        samples = (
            "cinvl dc,(a0)",
            "cinvp ic,(a7)",
            "cinva bc",
            "cpushl dc,(a0)",
            "cpushp ic,(a7)",
            "cpusha bc",
            "cinva nc",
            "cpusha nc",
        )
        for asm_text in samples:
            case = cases_68040[asm_text]
            with self.subTest(case=asm_text):
                _round_trip_case(case, "68040")

    def test_negative_indexed_displacements_render_signed(self) -> None:
        samples = (
            ("68000", "move.w -$8(a1,d1.w),d1"),
            ("68000", "jsr -$8(a1,d1.w)"),
            ("68000", "move.w -$0008(a1),d1"),
            ("68020", "move.w -$8(pc,d1.w),d1"),
        )
        for cpu_name, asm_text in samples:
            with self.subTest(cpu=cpu_name, asm=asm_text):
                original = _assemble_line_bytes(asm_text, cpu_name)
                rendered, byte_count = _disassemble_for_cpu(original, cpu_name)
                self.assertEqual(byte_count, len(original))
                self.assertEqual(rendered, asm_text)

    def test_link_long_round_trip_keeps_long_suffix(self) -> None:
        original = bytes.fromhex("480800008000")
        rendered, byte_count = _disassemble_for_cpu(original, "68010")
        self.assertEqual(byte_count, len(original))
        self.assertEqual(rendered, "link.l a0,#32768")
        self.assertEqual(_assemble_line_bytes(rendered, "68010"), original)

    def test_pvalid_absolute_word_prefers_full_length_match(self) -> None:
        original = bytes.fromhex("f03828001234")
        rendered, byte_count = _disassemble_for_cpu(original, "68030")
        self.assertEqual(byte_count, len(original))
        self.assertEqual(rendered, "pvalid val,$1234.w")
        self.assertEqual(_assemble_line_bytes(rendered, "68030"), original)

    def test_disassemble_info_sets_mnemonic_id_for_disassembler_only_form(self) -> None:
        original = bytes.fromhex("f050000f")
        result = _disassemble_info_for_cpu(original, "68030")
        self.assertEqual(result.byte_count, len(original))
        self.assertEqual(result.asm_form_index, _asm_form_none())
        self.assertNotEqual(result.canonical_form_id, 0)
        self.assertNotEqual(result.mnemonic_id, 0)
        self.assertEqual(bytes(result.mnemonic).split(b"\0", 1)[0].decode("ascii"), "pscc")

    def test_decode_info_returns_canonical_form_id(self) -> None:
        result = _disassemble_info_for_cpu(bytes.fromhex("4e71"), "68000")
        self.assertEqual(result.byte_count, 2)
        self.assertEqual(result.canonical_form_id, _canonical_form_id_for_syntax("NOP"))

    def test_conditional_family_case_preserves_canonical_form_id(self) -> None:
        case = _cases_by_first_line("68000")["bhi.b target"]
        result = _disassemble_info_for_cpu(_case_original_bytes(case), "68000")
        self.assertEqual(result.canonical_form_id, case.canonical_form_id)

    def test_signed_displacement_families_render_signed(self) -> None:
        samples = (
            ("68000", "move.w -$0008(a1),d1"),
            ("68000", "move.w -$10(pc),d1"),
            ("68000", "lea.l -$192(pc),a1"),
            ("68020", "move.w -$8(a1,d1.w),d1"),
            ("68020", "move.w -$8(pc,d1.w),d1"),
            ("68020", "lea.l $0(a0,d1.w){full,bdl=-$00000010,odl=-$00000004,iis=3},a0"),
            ("68000", "link a6,#-268"),
            ("68010", "rtd #-268"),
            ("68020", "link.l a6,#-32768"),
        )
        for cpu_name, asm_text in samples:
            with self.subTest(cpu=cpu_name, asm=asm_text):
                original = _assemble_line_bytes(asm_text, cpu_name)
                rendered, byte_count = _disassemble_for_cpu(original, cpu_name)
                self.assertEqual(byte_count, len(original))
                self.assertEqual(rendered, asm_text)

    def test_full_extension_word_displacements_render_signed(self) -> None:
        original = _assemble_line_bytes("lea.l $10(a0,d1.w){full,bdw=$1234,odw=$5678,iis=3},a0", "68020")
        patched = bytearray(original)
        patched[-4:] = bytes.fromhex("fff0fffc")
        rendered, byte_count = _disassemble_for_cpu(bytes(patched), "68020")
        self.assertEqual(byte_count, len(patched))
        self.assertEqual(rendered, "lea.l $0(a0,d1.w){full,bdw=-$0010,odw=-$0004,iis=3},a0")


if __name__ == "__main__":
    unittest.main()
