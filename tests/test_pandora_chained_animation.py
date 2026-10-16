"""Original chain-path bytes with synthetic nodes; no gameplay reachability claim."""
import ctypes as C
import hashlib

import pytest

from amiga_reversing.disasm.project_paths import resolve_project_paths
from src.tests.test_m68k_simulator_arithmetic import State, Trace, engine

TARGET = 'amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
BASE, NODE, NEXT, STATE, SEQUENCE, RETURN = 0x10000, 0x80000, 0x80100, 0x80200, 0x80300, 0x800


def put(memory, address, value, size=4):
    memory[address:address + size] = value.to_bytes(size, 'big')


def read(memory, address, size=4):
    return int.from_bytes(memory[address:address + size], 'big')


@pytest.fixture
def machine():
    data = resolve_project_paths(TARGET).binary_source.path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == '70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f'
    memory = bytearray(0x100000)
    memory[BASE:BASE + 349040] = data[:349040]
    buffer = (C.c_uint8 * len(memory)).from_buffer(memory)
    cpu = State()
    cpu.sr = 0x2000
    cpu.a[4] = STATE
    put(memory, STATE, 0x12345678)
    put(memory, STATE + 8, NODE)
    put(memory, NODE + 6, SEQUENCE)
    memory[NODE + 4:NODE + 6] = bytes((2, 1))
    memory[NODE + 10] = 8
    put(memory, NODE + 16, 0x017F, 2)
    put(memory, NODE + 18, NEXT)
    put(memory, NEXT + 16, 0x4567, 2)
    memory[NEXT + 10] = 0x0B
    put(memory, NEXT + 18, 0x80400)

    def run(start=0x951A, stop=None):
        cpu.a[7] = 0x9000
        put(memory, 0x9000, RETURN)
        cpu.pc = BASE + start
        end = RETURN if stop is None else BASE + stop
        trace = Trace()
        rc = engine()(0, buffer, len(memory), C.byref(cpu), 128, end, end + 2, None, C.byref(trace))
        assert rc == 0 and trace.stop_reason == 1 and not trace.overflow
        assert not any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count])
        return trace

    return memory, cpu, run


def test_chain_installs_one_successor_without_rendering_or_following_it(machine):
    memory, _, run = machine
    run()
    assert read(memory, STATE + 8) == NEXT
    assert read(memory, STATE) == 0x12345678
    assert read(memory, NODE + 16, 2) == 0x0100
    assert read(memory, NEXT + 16, 2) == 0
    assert memory[NEXT + 10] == 0x0A  # only hold bit cleared, including skip bit preservation
    assert read(memory, NEXT + 18) == 0x80400
    run()  # successor's skip flag prevents another transition
    assert read(memory, STATE + 8) == NEXT


def test_self_link_resets_same_node_and_returns(machine):
    memory, _, run = machine
    put(memory, NODE + 18, NODE)
    run()
    assert read(memory, STATE + 8) == NODE
    assert read(memory, NODE + 16, 2) == 0
    assert memory[NODE + 10] == 8
    assert read(memory, STATE) == 0x12345678


def test_null_successor_is_dereferenced_before_install_then_next_call_is_idle(machine):
    memory, _, run = machine
    put(memory, NODE + 18, 0)
    put(memory, 0x10, 0xABCD, 2)
    memory[0x0A] = 0xFF
    run()
    assert read(memory, 0x10, 2) == 0
    assert memory[0x0A] == 0xFE
    assert read(memory, STATE + 8) == 0
    assert read(memory, STATE) == 0x12345678
    assert run().writes == 0


@pytest.mark.parametrize('pointer', [0, NEXT, 0xFFFFFFFF])
def test_successor_load_is_full_absolute_long_with_no_sentinel_branch(machine, pointer):
    memory, cpu, run = machine
    put(memory, NODE + 18, pointer)
    cpu.a[0] = NODE
    trace = run(0x9582, 0x9586)
    assert cpu.a[0] == pointer
    assert trace.steps == 1 and trace.writes == 0


@pytest.mark.parametrize('mode,clock', [(8, 0), (9, 0x017F), (10, 0x017F), (8, 0x007F)])
def test_skip_hold_phase_and_count_gates_do_not_read_successor(machine, mode, clock):
    memory, _, run = machine
    memory[NODE + 10] = mode
    put(memory, NODE + 16, clock, 2)
    put(memory, NODE + 18, 0xFFFFFFFF)
    put(memory, SEQUENCE, 0x11111111)
    put(memory, SEQUENCE + 8, 0x22222222)
    run()
    assert read(memory, STATE + 8) == NODE
    assert read(memory, NEXT + 16, 2) == 0x4567
