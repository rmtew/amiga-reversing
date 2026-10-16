"""Bounded original-byte execution of player node installation and phase changes.

These fixtures establish local record use, not arbitrary gameplay reachability.
"""
import ctypes as C
import hashlib

import pytest

from amiga_reversing.disasm.project_paths import resolve_project_paths
from src.tests.test_m68k_simulator_arithmetic import State, Trace, engine

TARGET = 'amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
BASE = 0x10000
PLAYER_STATE = BASE + 0x4C72A
POSITIVE_X = BASE + 0x4C744
SEQUENCE = BASE + 0x4C756
RETURN = 0x800


@pytest.fixture
def machine():
    data = resolve_project_paths(TARGET).binary_source.path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == '70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f'
    memory = bytearray(0x100000)
    memory[BASE:BASE + 349040] = data[:349040]
    buffer = (C.c_uint8 * len(memory)).from_buffer(memory)
    cpu = State()
    cpu.sr = 0x2000
    cpu.a[6] = 0x90000

    def run(start, stop=None):
        cpu.a[7] = 0x9000
        memory[0x9000:0x9004] = RETURN.to_bytes(4, 'big')
        cpu.pc = BASE + start
        end = RETURN if stop is None else BASE + stop
        trace = Trace()
        result = engine()(0, buffer, len(memory), C.byref(cpu), 256, end, end + 2, None, C.byref(trace))
        assert result == 0 and trace.stop_reason == 1 and not trace.overflow
        assert not any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count])

    return memory, cpu, run


def read(memory, addr, size=4):
    return int.from_bytes(memory[addr:addr + size], 'big')


@pytest.mark.parametrize('x,y,node,flag', [
    (1, 0, 0x4C744, 8), (-1, 0, 0x4C776, 4),
    (0, 1, 0x4C7A8, 2), (0, -1, 0x4C7D6, 1),
])
def test_direction_selection_reuses_node_and_resets_only_on_change(machine, x, y, node, flag):
    memory, cpu, run = machine
    node += BASE
    descriptor = bytes(memory[POSITIVE_X:POSITIVE_X + 4])
    cpu.a[4] = 0x80000  # synthetic object; this prefix only touches direction flags
    cpu.d[0], cpu.d[1] = x & 0xFFFFFFFF, y & 0xFFFFFFFF
    memory[node + 16:node + 18] = b'\x03\x40'
    memory[node + 10] = 3
    run(0x9844, 0x98AE)
    assert read(memory, PLAYER_STATE + 8) == node
    assert memory[0x80000 + 75] == flag
    assert read(memory, node + 16, 2) == 0
    assert memory[node + 10] == 0
    memory[node + 16:node + 18] = b'\x03\x40'
    run(0x9844, 0x98AE)
    assert read(memory, node + 16, 2) == 0x0340
    assert bytes(memory[POSITIVE_X:POSITIVE_X + 4]) == descriptor


def test_positive_x_install_cycle_hold_and_resume_keep_adjacent_descriptor(machine):
    memory, cpu, run = machine
    assert POSITIVE_X == PLAYER_STATE + 26
    header = bytes(memory[POSITIVE_X:POSITIVE_X + 16])
    assert read(memory, POSITIVE_X) == BASE + 0x4C71E
    assert read(memory, POSITIVE_X + 6) == SEQUENCE
    assert memory[POSITIVE_X + 4:POSITIVE_X + 6] == b'\x07\x40'
    run(0x4AFFA, 0x4B008)
    assert read(memory, PLAYER_STATE + 8) == POSITIVE_X
    frames = []
    for visit in range(14):
        cpu.a[4] = PLAYER_STATE
        run(0x951A)
        if visit % 2:
            frames.append(read(memory, PLAYER_STATE))
    assert frames == [read(memory, SEQUENCE + 4 + index * 4) for index in (1, 2, 3, 4, 5, 6, 0)]
    assert read(memory, POSITIVE_X + 16, 2) == 0
    run(0x9984)
    assert memory[POSITIVE_X + 10] == 1
    cpu.a[4] = PLAYER_STATE
    run(0x951A)
    assert read(memory, PLAYER_STATE) == read(memory, SEQUENCE)
    assert read(memory, POSITIVE_X + 16, 2) == 0
    cpu.a[4] = 0x80000
    cpu.d[0], cpu.d[1] = 1, 0
    run(0x9844, 0x98AE)
    assert bytes(memory[POSITIVE_X:POSITIVE_X + 16]) == header
    assert read(memory, PLAYER_STATE + 8) == POSITIVE_X


def test_initialized_player_flags_skip_receptacle_tail_dispatch(machine):
    memory, cpu, run = machine
    assert memory[PLAYER_STATE + 25] == 2
    memory[0x81000:0x81004] = (BASE + 0x4C71E).to_bytes(4, 'big')
    cpu.a[0] = 0x81000
    cpu.d[7] = 0  # one descriptor in the bounded interaction scan
    before = bytes(memory[PLAYER_STATE:SEQUENCE + 32])
    run(0x7E04)
    assert bytes(memory[PLAYER_STATE:SEQUENCE + 32]) == before
    assert cpu.a[0] == 0x81004
