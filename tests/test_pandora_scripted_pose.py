"""Bounded cold-image script semantics; no normal-gameplay reachability claim."""
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


def test_diabetic_script_selects_active_and_header_poses_with_100_6_delays():
    paths = resolve_project_paths(TARGET)
    if not (Path(__file__).resolve().parents[1] / 'src/build/libamiga_backend.so').exists():
        pytest.skip('native backend not built')
    data = paths.binary_source.path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == '70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f'
    metadata = effective_target_metadata(paths.target_dir)
    schemas = {s.name: {f.name: f.offset for f in s.fields} for s in metadata.custom_structs}
    obj = schemas['world_object_shared_prefix']
    state_fields = schemas['world_position_state_record']
    node_fields = schemas['WorldPositionStateNode']
    memory = bytearray(0x100000)
    memory[BASE:BASE+349040] = data[:349040]
    buffer = (C.c_uint8 * len(memory)).from_buffer(memory)
    cpu = State()
    cpu.sr = 0x2000
    cpu.a[5] = BASE + 0x4B728

    def read(address, size=4):
        return int.from_bytes(memory[address:address+size], 'big')

    def call(source_offset):
        # Synthetic call/return context exists only in this local CPU fixture.
        cpu.a[7] = 0x9000
        memory[0x9000:0x9004] = RETURN.to_bytes(4, 'big')
        cpu.pc = BASE + source_offset
        trace = Trace()
        rc = engine()(0, buffer, len(memory), C.byref(cpu), 256, RETURN, RETURN+2, None, C.byref(trace))
        messages = [bytes(d.message).split(b'\0')[0].decode() for d in trace.diagnostics.items[:trace.diagnostics.count]]
        assert rc == 0 and trace.stop_reason == 1, messages
        assert 0 < trace.steps < 256 and not trace.overflow
        assert not any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count]), messages
        assert cpu.a[5] == BASE + 0x4B728

    giver = cpu.a[5]
    assert not read(giver + obj['world_object_flags'], 1) & 2
    assert read(giver + obj['behavior_script_ptr']) == BASE + 0x21CC
    descriptor = read(giver + obj['position_descriptor_ptr'])
    primary = read(descriptor)
    attachment = read(primary + state_fields['attachment_state_ptr'])
    assert attachment == BASE + 0x4B7C6
    assert read(attachment + state_fields['state_node_ptr']) == 0
    primary_before = bytes(memory[primary:primary+26])
    # Execute the actual variable-format interpreter and both callback bodies.
    call(0x13F4)
    node = read(attachment + state_fields['state_node_ptr'])
    assert node == BASE + 0x4B814
    assert read(giver + obj['behavior_script_delay_ticks'], 2) == 100
    assert read(giver + obj['behavior_script_ptr']) == BASE + 0x21DC
    assert bytes(memory[primary:primary+26]) == primary_before
    sequence = read(node + node_fields['frame_sequence_ptr'])
    held, active = read(sequence), read(sequence+4)
    assert (held, active) == (BASE+0x4B78E, BASE+0x4B77C)
    assert read(node + node_fields['frame_count'], 1) == 1
    assert read(node + node_fields['mode_flags'], 1) == 0
    cpu.a[4] = attachment
    call(0x951A)
    assert read(attachment + state_fields['current_geometry_ptr']) == active

    for remaining in range(99, -1, -1):
        call(0x13F4)
        assert read(giver + obj['behavior_script_delay_ticks'], 2) == (remaining or 6)
    assert read(giver + obj['behavior_script_ptr']) == BASE + 0x21E6
    assert read(node + node_fields['mode_flags'], 1) == 1
    cpu.a[4] = attachment
    call(0x951A)
    assert read(attachment + state_fields['current_geometry_ptr']) == held

    for remaining in range(5, -1, -1):
        call(0x13F4)
        assert read(giver + obj['behavior_script_delay_ticks'], 2) == (remaining or 100)
    assert read(giver + obj['behavior_script_ptr']) == BASE + 0x21DC
    assert read(node + node_fields['mode_flags'], 1) == 0
    cpu.a[4] = attachment
    call(0x951A)
    assert read(attachment + state_fields['current_geometry_ptr']) == active
