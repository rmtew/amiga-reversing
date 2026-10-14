"""Bounded original CPU transitions; no full-callback or gameplay closure claim."""
from __future__ import annotations

import ctypes as C
import hashlib
from pathlib import Path

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from src.tests.test_m68k_simulator_arithmetic import State, Trace, engine

TARGET = 'amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
BASE = 0x10000
RETURN = 0x800


@pytest.fixture
def cpu_fixture():
    if not (Path(__file__).resolve().parents[1] / 'src/build/libamiga_backend.so').exists():
        pytest.skip('native backend not built')
    paths = resolve_project_paths(TARGET)
    data = paths.binary_source.path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == '70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f'
    schemas = {s.name: {f.name: f.offset for f in s.fields}
               for s in effective_target_metadata(paths.target_dir).custom_structs}
    memory = bytearray(0x100000)
    memory[BASE:BASE+349040] = data[:349040]
    buffer = (C.c_uint8 * len(memory)).from_buffer(memory)
    cpu = State()
    cpu.sr = 0x2000
    cpu.a[5] = BASE + 0x4A40A  # Original entry officer.

    def read(address, size=4):
        return int.from_bytes(memory[address:address+size], 'big')

    def write(address, value, size=4):
        memory[address:address+size] = value.to_bytes(size, 'big')

    def run(source, *, stop=None):
        cpu.a[7] = 0x9000
        write(0x9000, RETURN)
        cpu.pc = BASE + source
        stop_pc = BASE + stop if stop is not None else RETURN
        trace = Trace()
        rc = engine()(0, buffer, len(memory), C.byref(cpu), 512,
                      stop_pc, stop_pc+2, None, C.byref(trace))
        messages = [bytes(d.message).split(b'\0')[0].decode()
                    for d in trace.diagnostics.items[:trace.diagnostics.count]]
        assert rc == 0 and trace.stop_reason == 1, messages
        assert 0 < trace.steps < 512 and not trace.overflow
        assert not any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count]), messages
        return trace.steps

    return cpu, memory, schemas, read, write, run


@pytest.mark.parametrize('mode,clock', [(0, 0), (1, 0x1234), (0xA5, 0xFFFF)])
def test_state_exchange_is_reversible_and_resets_only_incoming_node(cpu_fixture, mode, clock):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj = schemas['world_object_shared_prefix']
    state = schemas['world_position_state_record']
    node = schemas['WorldPositionStateNode']
    # The original first interpreter pass supplies the active node, then waits.
    run(0x13F4)
    giver = cpu.a[5]
    descriptor = read(giver + obj['position_descriptor_ptr'])
    active = read(descriptor)
    saved = read(giver + obj['saved_position_state_ptr'])
    active_node = read(active + state['state_node_ptr'])
    saved_node = read(saved + state['state_node_ptr'])
    assert active != saved and active_node and saved_node and active_node != saved_node
    for address in (active_node, saved_node):
        write(address + node['mode_flags'], mode, 1)
        write(address + node['frame_index_and_phase'], clock, 2)
    for index in range(8):
        cpu.d[index] = 0x12340000 + index
        if index != 5:
            cpu.a[index] = 0x56780000 + index
    before_d, before_a = list(cpu.d), list(cpu.a)[:7]
    assert run(0x867E) == 11
    assert list(cpu.d) == before_d and list(cpu.a)[:7] == before_a and cpu.a[7] == 0x9004
    assert read(descriptor) == saved and read(giver + obj['saved_position_state_ptr']) == active
    assert read(saved_node + node['mode_flags'], 1) == mode & ~1
    assert read(saved_node + node['frame_index_and_phase'], 2) == 0
    assert read(active_node + node['mode_flags'], 1) == mode
    assert read(active_node + node['frame_index_and_phase'], 2) == clock
    run(0x867E)
    assert read(descriptor) == active and read(giver + obj['saved_position_state_ptr']) == saved
    assert read(active_node + node['mode_flags'], 1) == mode & ~1
    assert read(active_node + node['frame_index_and_phase'], 2) == 0


def test_handoff_prefix_inhibits_dispatch_but_delay_still_counts_down(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj = schemas['world_object_shared_prefix']
    run(0x13F4)
    giver = cpu.a[5]
    cursor = read(giver + obj['behavior_script_ptr'])
    delay = read(giver + obj['behavior_script_delay_ticks'], 2)
    assert cursor == BASE + 0x23AC and delay == 20
    slots = read(giver + obj['inventory_slots_ptr'])
    inventory_before = bytes(memory[slots:slots+8])
    item = read(giver + obj['selected_item_id'], 1)
    # This actual straight-line prefix starts after enqueue and stops before
    # state/UI/audio calls. Their effects are deliberately outside this test.
    run(0x4B12E, stop=0x4B148)
    assert read(giver + obj['selected_item_id'], 1) == 0
    assert read(BASE + 0x4C322 + obj['selected_item_id'], 1) == item == 54
    assert read(giver + obj['world_object_flags'], 1) & 2
    assert bytes(memory[slots:slots+8]) == b'\0' + inventory_before[1:]
    for remaining in range(delay-1, -1, -1):
        run(0x13F4)
        assert read(giver + obj['behavior_script_delay_ticks'], 2) == remaining
        assert read(giver + obj['behavior_script_ptr']) == cursor
    run(0x13F4)
    assert read(giver + obj['behavior_script_ptr']) == cursor
    assert read(giver + obj['behavior_script_delay_ticks'], 2) == 0
    # Execute the original restart flag-parity branch through its state exchange,
    # stopping before item-name/inventory/UI work. The suffix then restores the
    # script cursor. This is not a complete restart callback invocation.
    descriptor = read(giver + obj['position_descriptor_ptr'])
    active, saved = read(descriptor), read(giver + obj['saved_position_state_ptr'])
    run(0xA0BE, stop=0xA0E2)
    assert read(descriptor) == saved and read(giver + obj['saved_position_state_ptr']) == active
    assert read(giver + obj['world_object_flags'], 1) == read(giver + obj['initial_world_object_flags'], 1) == 0
    assert cpu.d[0] & 0xFF == 0
    run(0xA122, stop=0xA12C)
    assert read(giver + obj['behavior_script_ptr']) == read(giver + obj['initial_behavior_script_ptr']) == BASE + 0x239C
    assert read(giver + obj['behavior_script_delay_ticks'], 2) == 0
    # Re-entering the interpreter with these restored fields replays the intro
    # through its first delay. Intervening full-restart callees are not modeled.
    run(0x13F4)
    assert read(giver + obj['behavior_script_ptr']) == BASE + 0x23AC
    assert read(giver + obj['behavior_script_delay_ticks'], 2) == 20
