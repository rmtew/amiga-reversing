"""MOVEQ's signed DATA byte, long result and NZVC/X contract (PRM p238)."""
import ctypes as C
import pytest

from src.tests.test_m68k_simulator_arithmetic import State, Trace, engine
from src.tests import test_m68k_simulator_abstract as abstract


def concrete(reg, byte, old_ccr):
    memory = bytearray([0x70 | (reg << 1), byte, 0xA5, 0x5A])
    original = bytes(memory)
    state = State()
    state.d[:] = [0xA5A50000+i for i in range(8)]
    state.a[:] = [0x12340000+i for i in range(8)]
    state.sr = 0xA700 | old_ccr
    before_d, before_a = list(state.d), list(state.a)
    buf = (C.c_uint8*len(memory)).from_buffer(memory)
    trace = Trace()
    assert engine()(0, buf, len(memory), C.byref(state), 1, 0, 0, None, C.byref(trace)) == 0
    assert trace.steps == 1 and not trace.writes and bytes(memory) == original
    assert not any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count])
    expected = byte if byte < 128 else byte | 0xFFFFFF00
    before_d[reg] = expected
    assert list(state.d) == before_d and list(state.a) == before_a, (reg, byte)
    assert state.pc == 2
    assert state.sr == 0xA700 | (old_ccr & 16) | (8 if byte & 128 else 4 if not byte else 0), (reg, byte, hex(state.sr))


def test_negative_witness():
    concrete(5, 0xFF, 31)


@pytest.mark.parametrize('reg', range(8))
def test_all_encoded_bytes_neighbours_and_extend_bit(reg):
    for byte in range(256):
        for ccr in (0, 31):
            concrete(reg, byte, ccr)


@pytest.mark.parametrize('byte', [0, 1, 127, 128, 255])
def test_abstract_and_concrete_agree_on_signed_long_and_flags(byte):
    state = abstract.M68kSimCpuState()
    state.sr = 0x201F
    code = (C.c_uint8*2)(0x70, byte)
    result = abstract._disasm_library().m68k_simulate_one_abstract_for_cpu(code, 2, 0, C.byref(state))
    assert not abstract._diag_has_errors(result.diagnostics)
    value = result.step.next_state.d[0]
    assert value.kind == abstract.M68K_SIM_VALUE_CONSTANT
    assert value.value == (byte if byte < 128 else byte | 0xFFFFFF00)
    assert result.step.next_state.sr == 0x2010 | (8 if byte & 128 else 4 if not byte else 0)
