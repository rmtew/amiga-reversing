from __future__ import annotations

import ctypes
import subprocess
import unittest
from functools import lru_cache
from pathlib import Path

from src.tests._build_helpers import prepare_test_dll
from src.tests._build_helpers import require_built_tools

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
ASM_EXE = BUILD_DIR / "m68k_assembler_app.exe"
DISASM_DLL = BUILD_DIR / "m68k_disassembler_lib.dll"
CPU_BITS = {"68000": 0, "68010": 1, "68020": 2, "68030": 3, "68040": 4}

M68K_SIM_VALUE_UNKNOWN = 0
M68K_SIM_VALUE_CONSTANT = 1
M68K_SIM_VALUE_SECTION_PTR = 2


class M68kSimTargetSet(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_size_t),
        ("targets", ctypes.c_uint32 * 32),
    ]


class M68kSimValue(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_uint8),
        ("section_index", ctypes.c_uint8),
        ("provenance", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8),
        ("value", ctypes.c_uint32),
        ("table_start", ctypes.c_uint32),
        ("table_end", ctypes.c_uint32),
        ("table_stride", ctypes.c_uint32),
        ("target_set", M68kSimTargetSet),
    ]


class M68kSimCpuState(ctypes.Structure):
    _fields_ = [
        ("d", M68kSimValue * 8),
        ("a", M68kSimValue * 8),
        ("c", M68kSimValue * 32),
        ("pc", ctypes.c_uint32),
        ("sr", ctypes.c_uint16),
    ]


class M68kSimAccess(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_uint8),
        ("width", ctypes.c_uint8),
        ("section_index", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8),
        ("offset", ctypes.c_uint32),
    ]


class M68kSimMemoryCell(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_uint8),
        ("section_index", ctypes.c_uint8),
        ("reserved0", ctypes.c_uint8),
        ("reserved1", ctypes.c_uint8),
        ("offset", ctypes.c_uint32),
        ("value", M68kSimValue),
    ]


class M68kSimStepResult(ctypes.Structure):
    _fields_ = [
        ("next_state", M68kSimCpuState),
        ("control_targets", M68kSimTargetSet),
        ("discovered_labels", M68kSimTargetSet),
        ("accesses", M68kSimAccess * 8),
        ("access_count", ctypes.c_size_t),
        ("memory_writes", M68kSimMemoryCell * 8),
        ("memory_write_count", ctypes.c_size_t),
        ("defines_condition_codes", ctypes.c_int),
        ("stops_fallthrough", ctypes.c_int),
    ]


@lru_cache(maxsize=1)
def _disasm_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(DISASM_DLL)))
    library.m68k_simulate_one_abstract_for_cpu.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_uint8,
        ctypes.POINTER(M68kSimCpuState),
        ctypes.POINTER(M68kSimStepResult),
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]
    library.m68k_simulate_one_abstract_for_cpu.restype = ctypes.c_int
    return library


def _assemble_line_hex(cpu: str, text: str) -> bytes:
    result = subprocess.run(
        [str(ASM_EXE), "assemble-line", "--cpu", cpu, text],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return bytes.fromhex(result.stdout.strip())


def _const(value: int) -> M68kSimValue:
    result = M68kSimValue()
    result.kind = M68K_SIM_VALUE_CONSTANT
    result.value = value
    return result


def _section_ptr(offset: int) -> M68kSimValue:
    result = M68kSimValue()
    result.kind = M68K_SIM_VALUE_SECTION_PTR
    result.section_index = 0
    result.value = offset
    return result


class M68kSimulatorAbstractTests(unittest.TestCase):
    def _simulate_bytes(self, code: bytes, state: M68kSimCpuState, cpu: str = "68000") -> M68kSimStepResult:
        buf = (ctypes.c_uint8 * len(code)).from_buffer_copy(code)
        error = ctypes.create_string_buffer(256)
        result = M68kSimStepResult()
        rc = _disasm_library().m68k_simulate_one_abstract_for_cpu(
            buf, len(code), CPU_BITS[cpu], ctypes.byref(state), ctypes.byref(result), error, len(error)
        )
        self.assertEqual(rc, 0, error.value.decode("utf-8"))
        return result

    def _simulate(self, asm_text: str, state: M68kSimCpuState) -> M68kSimStepResult:
        code = _assemble_line_hex("68000", asm_text)
        return self._simulate_bytes(code, state)

    def test_abstract_dbf_decrements_counter_and_emits_target(self) -> None:
        state = M68kSimCpuState()
        state.d[0] = _const(2)
        result = self._simulate("dbf d0,4", state)
        self.assertEqual(result.next_state.d[0].kind, M68K_SIM_VALUE_CONSTANT)
        self.assertEqual(result.next_state.d[0].value, 1)
        self.assertEqual(result.control_targets.count, 1)
        self.assertEqual(result.control_targets.targets[0], 6)

    def test_abstract_sf_updates_low_byte_of_register(self) -> None:
        state = M68kSimCpuState()
        state.d[0] = _const(0x12345678)
        result = self._simulate("sf d0", state)
        self.assertEqual(result.next_state.d[0].kind, M68K_SIM_VALUE_CONSTANT)
        self.assertEqual(result.next_state.d[0].value, 0x12345600)

    def test_abstract_sf_memory_write_records_access_and_label(self) -> None:
        state = M68kSimCpuState()
        state.a[0] = _section_ptr(0)
        result = self._simulate("sf (a0)", state)
        self.assertEqual(result.access_count, 1)
        self.assertEqual(result.accesses[0].offset, 0)
        self.assertEqual(result.discovered_labels.count, 1)
        self.assertEqual(result.discovered_labels.targets[0], 0)

    def test_abstract_movem_predecrement_records_pointer_write(self) -> None:
        state = M68kSimCpuState()
        state.a[7] = _section_ptr(0x04)
        state.a[1] = _section_ptr(0x40)
        result = self._simulate("movem.l a1,-(a7)", state)
        self.assertEqual(result.next_state.a[7].kind, M68K_SIM_VALUE_SECTION_PTR)
        self.assertEqual(result.next_state.a[7].value, 0x00)
        self.assertEqual(result.memory_write_count, 1)
        self.assertEqual(result.memory_writes[0].offset, 0x00)
        self.assertEqual(result.memory_writes[0].value.kind, M68K_SIM_VALUE_SECTION_PTR)
        self.assertEqual(result.memory_writes[0].value.value, 0x40)

    def test_abstract_asl_immediate_updates_constant_register(self) -> None:
        state = M68kSimCpuState()
        state.d[0] = _const(3)
        result = self._simulate("asl.l #1,d0", state)
        self.assertEqual(result.next_state.d[0].kind, M68K_SIM_VALUE_CONSTANT)
        self.assertEqual(result.next_state.d[0].value, 6)

    def test_abstract_cmp2_updates_carry_for_out_of_range_value(self) -> None:
        state = M68kSimCpuState()
        code = _assemble_line_hex("68020", "cmp2.w (a0),d0") + b"\x00\x02\x00\x08"
        state.a[0] = _section_ptr(len(_assemble_line_hex("68020", "cmp2.w (a0),d0")))
        state.d[0] = _const(9)
        result = self._simulate_bytes(code, state, "68020")
        self.assertEqual(result.next_state.sr & 0x0001, 0x0001)
        self.assertGreaterEqual(result.access_count, 2)

    def test_abstract_bfins_memory_records_byte_write(self) -> None:
        state = M68kSimCpuState()
        code = _assemble_line_hex("68020", "bfins d1,(a0){0:8}") + b"\x12"
        state.a[0] = _section_ptr(len(_assemble_line_hex("68020", "bfins d1,(a0){0:8}")))
        state.d[1] = _const(0xAA)
        result = self._simulate_bytes(code, state, "68020")
        self.assertEqual(result.memory_write_count, 1)
        self.assertEqual(result.memory_writes[0].offset, len(code) - 1)
        self.assertEqual(result.memory_writes[0].value.kind, M68K_SIM_VALUE_CONSTANT)
        self.assertEqual(result.memory_writes[0].value.value, 0xAA)

    def test_abstract_bfffo_memory_produces_absolute_bit_offset(self) -> None:
        state = M68kSimCpuState()
        code = _assemble_line_hex("68020", "bfffo (a0){12:8},d1") + bytes.fromhex("12345678")
        state.a[0] = _section_ptr(len(_assemble_line_hex("68020", "bfffo (a0){12:8},d1")))
        result = self._simulate_bytes(code, state, "68020")
        self.assertEqual(result.next_state.d[1].kind, M68K_SIM_VALUE_CONSTANT)
        self.assertEqual(result.next_state.d[1].value, 13)

    def test_abstract_chk2_known_failure_stops_fallthrough(self) -> None:
        state = M68kSimCpuState()
        code = _assemble_line_hex("68020", "chk2.w (a0),d0") + b"\x00\x02\x00\x08"
        state.a[0] = _section_ptr(len(_assemble_line_hex("68020", "chk2.w (a0),d0")))
        state.d[0] = _const(9)
        result = self._simulate_bytes(code, state, "68020")
        self.assertEqual(result.next_state.sr & 0x0001, 0x0001)
        self.assertEqual(result.stops_fallthrough, 1)

    def test_abstract_bftst_memory_sets_zero_flag(self) -> None:
        state = M68kSimCpuState()
        code = _assemble_line_hex("68020", "bftst (a0){0:8}") + b"\x00"
        state.a[0] = _section_ptr(len(_assemble_line_hex("68020", "bftst (a0){0:8}")))
        result = self._simulate_bytes(code, state, "68020")
        self.assertEqual(result.next_state.sr & 0x0004, 0x0004)


if __name__ == "__main__":
    unittest.main()
