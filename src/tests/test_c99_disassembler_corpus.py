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


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=None)
def _generate_cases_for_cpu(cpu_name: str):
    generator = _load_module(CORPUS_GENERATOR_PATH, f"src_c99_disassembler_test_corpus_{cpu_name}")
    return tuple(generator.generate_cases(cpu_name))


@lru_cache(maxsize=1)
def _disasm_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(DISASM_DLL_PATH)))
    library.m68k_disassemble_one_text_for_cpu.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.c_uint8,
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]
    library.m68k_disassemble_one_text_for_cpu.restype = ctypes.c_int
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
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]
    library.m68k_assemble.restype = ctypes.c_int
    return library


def _disassemble_for_cpu(data: bytes, cpu_name: str) -> tuple[str, int]:
    library = _disasm_library()
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    text_buf = ctypes.create_string_buffer(512)
    error_buf = ctypes.create_string_buffer(256)
    byte_count = ctypes.c_size_t()
    result = library.m68k_disassemble_one_text_for_cpu(
        buffer,
        len(data),
        CPU_CODES[cpu_name],
        text_buf,
        len(text_buf),
        ctypes.byref(byte_count),
        error_buf,
        len(error_buf),
    )
    if result != 0:
        raise AssertionError(error_buf.value.decode("utf-8"))
    return text_buf.value.decode("utf-8"), int(byte_count.value)


@lru_cache(maxsize=None)
def _assemble_text(text: str, cpu_name: str, input_mode: int) -> bytes:
    library = _assembler_library()
    options = library._m68k_asm_options_type(CPU_CODES[cpu_name], input_mode)
    out_buf = (ctypes.c_ubyte * 512)()
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


def _assemble_line_bytes(text: str, cpu_name: str) -> bytes:
    return _assemble_text(text, cpu_name, 0)


def _assemble_source_bytes(text: str, cpu_name: str) -> bytes:
    return _assemble_text(text, cpu_name, 1)


def _case_original_bytes(case) -> bytes:
    full = bytes.fromhex(str(case.expected_hex))
    encoded_size = int(case.size)
    return full[:encoded_size] if encoded_size != 0 else full


def _round_trip_case(case, cpu_name: str) -> None:
    if str(case.mnemonic).upper() in unsupported_mmu_round_trip_mnemonics_upper():
        raise unittest.SkipTest(f"unsupported MMU round-trip mnemonic: {case.mnemonic}")
    original = _case_original_bytes(case)
    rendered, byte_count = _disassemble_for_cpu(original, cpu_name)
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
    def test_bulk_round_trip_corpus_by_cpu(self) -> None:
        for cpu_name in CPU_NAMES:
            with self.subTest(cpu=cpu_name):
                for case in _generate_cases_for_cpu(cpu_name):
                    _round_trip_case(case, cpu_name)

    def test_pc_relative_indexed_representatives_round_trip(self) -> None:
        cases_68020 = _generate_cases_for_cpu("68020")
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
            case = next(case for case in cases_68020 if case.asm_lines[0] == source_text)
            with self.subTest(case=source_text):
                _round_trip_case(case, "68020")

    def test_pc_relative_full_extension_representatives_round_trip(self) -> None:
        cases_68020 = _generate_cases_for_cpu("68020")
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
            case = next(case for case in cases_68020 if case.asm_lines[0] == source_text)
            with self.subTest(case=source_text):
                _round_trip_case(case, "68020")

    def test_move16_round_trip_representatives(self) -> None:
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

    def test_cache_control_round_trip_representatives(self) -> None:
        cases_68040 = _generate_cases_for_cpu("68040")
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
            case = next(case for case in cases_68040 if case.asm_lines[0] == asm_text)
            with self.subTest(case=asm_text):
                _round_trip_case(case, "68040")


if __name__ == "__main__":
    unittest.main()
