"""Original-byte sequence consumers and all typed replacement commands.

The synthetic call contexts prove local semantics, not gameplay scheduling.
"""
import ctypes as C
import hashlib

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from src.tests.test_m68k_simulator_arithmetic import State, Trace, engine

TARGET = 'amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
BASE, OBJECT, DESCRIPTOR, STATE, NODE, FRAMES, XY = 0x10000, 0x80000, 0x80100, 0x80200, 0x80300, 0x80400, 0x80500


def put(memory, address, value, size=4):
    memory[address:address + size] = (value & ((1 << (size * 8)) - 1)).to_bytes(size, 'big')


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

    def run(start, stop=None):
        cpu.a[7] = 0x9000
        put(memory, 0x9000, 0x800)
        cpu.pc = BASE + start
        trace = Trace()
        end = 0x800 if stop is None else BASE + stop
        rc = engine()(0, buffer, len(memory), C.byref(cpu), 256, end, end + 2, None, C.byref(trace))
        assert rc == 0 and trace.stop_reason == 1 and not trace.overflow
        assert not any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count])
        return trace

    return memory, cpu, run


@pytest.fixture(scope='module')
def metadata():
    return effective_target_metadata(resolve_project_paths(TARGET).target_dir)


def test_every_typed_replacement_preserves_bounds_and_runs_to_held_frame(machine, metadata):
    memory, cpu, run = machine
    schemas = {s.name: {f.name: f.offset for f in s.fields} for s in metadata.custom_structs}
    commands = [l.source_start + e.offset for l in metadata.data_block_layouts for e in l.elements
                if e.type_binding and e.type_binding['bound_type_id'] == 'world_behavior_node_sequence_command']
    assert len(commands) == 26
    spans = {}
    for l in metadata.data_block_layouts:
        if l.name not in ('fixed_npc_frame_sequences_early', 'fixed_npc_frame_sequences_late'):
            continue
        elements = sorted(l.elements, key=lambda e: e.offset)
        assert len(elements) in (8, 18)
        for held, active in zip(elements[::2], elements[1::2]):
            assert held.width == 4 and active.offset == held.offset + 4
            assert active.array_count in (2, 4) and active.width == active.array_count * 4
            assert held.type_binding['bound_type_id'] == active.type_binding['bound_type_id'] == 'WorldPositionDescriptorPointer'
            spans[BASE + l.source_start + held.offset] = active.array_count
        assert elements[-1].offset + elements[-1].width == l.source_end - l.source_start
    assert len(spans) == 13
    seen = set()
    for offset in commands:
        command = BASE + offset
        assert read(memory, command, 2) == 30
        node, sequence = read(memory, command + 2), read(memory, command + 6)
        count = memory[node + 4]
        assert count == spans[sequence]
        assert memory[node + 5] == 64 and memory[node + 10] & ~1 == 4
        assert read(memory, node + 12) == 0
        seen.add(sequence)
        # Give the handler a stale clock/hold bit, leaving all other fields original.
        put(memory, node + 16, 0x0140, 2)
        memory[node + 10] |= 1
        before = bytes(memory[node:node + 18])
        put(memory, OBJECT + schemas['world_object_shared_prefix']['position_descriptor_ptr'], DESCRIPTOR)
        put(memory, DESCRIPTOR, STATE)
        memory[STATE + schemas['world_position_state_record']['world_object_flags']] = 0
        put(memory, STATE, 0x12345678)
        cpu.a[5], cpu.a[4] = OBJECT, command
        run(0x136C)
        assert cpu.a[4] == command + 10
        assert read(memory, STATE + 8) == node
        expected = bytearray(before)
        expected[6:10] = sequence.to_bytes(4, 'big')
        expected[10] &= ~1
        expected[16:18] = b'\0\0'
        assert memory[node:node + 18] == expected
        cpu.a[4] = STATE
        for index in range(1, count):
            previous = read(memory, STATE)
            run(0x951A)
            assert read(memory, STATE) == previous
            run(0x951A)
            assert read(memory, STATE) == read(memory, sequence + 4 + 4 * index)
            assert BASE <= read(memory, STATE) < BASE + 349040
        run(0x951A)
        run(0x951A)
        assert memory[node + 10] == 5
        assert read(memory, STATE) == read(memory, sequence)
        assert memory[node + 16] == count - 1
    assert len(seen) == 12


@pytest.mark.parametrize('mode,index,expected_record', [(1, 0, 0), (0, 0, 2), (0, 1, 1)])
def test_xy_pair_stride_and_held_prefix(machine, mode, index, expected_record):
    memory, cpu, run = machine
    cpu.a[4] = STATE
    put(memory, STATE + 8, NODE)
    put(memory, NODE + 6, FRAMES)
    put(memory, NODE + 12, XY)
    memory[NODE + 4:NODE + 6] = bytes((2, 64))
    memory[NODE + 10] = mode
    put(memory, NODE + 16, (index << 8) | 64, 2)
    pairs = [(0xFFFF, 0x8000), (11, 22), (33, 44)]
    for i, (x, y) in enumerate(pairs):
        put(memory, FRAMES + 4 * i, 0x20000 + 0x100 * i)
        put(memory, XY + 4 * i, x, 2)
        put(memory, XY + 4 * i + 2, y, 2)
    run(0x951A)
    assert read(memory, STATE) == read(memory, FRAMES + 4 * expected_record)
    assert (read(memory, STATE + 12, 2), read(memory, STATE + 14, 2)) == pairs[expected_record]
    # Wrap reads pair zero and then active pair zero in the same call.
    assert memory[NODE + 16] == (index if mode else (index + 1) % 2)


@pytest.mark.parametrize('handler,wanted,walks', [(0x1306, 0, False), (0x1334, 8, True), (0x136C, 0, True)])
def test_replacement_selectors_and_ten_byte_command_stride(machine, metadata, handler, wanted, walks):
    memory, cpu, run = machine
    schemas = {s.name: {f.name: f.offset for f in s.fields} for s in metadata.custom_structs}
    flags = schemas['world_position_state_record']['world_object_flags']
    attachment = schemas['world_position_state_record']['attachment_state_ptr']
    second, command = STATE + 0x40, 0x80600
    put(memory, OBJECT + schemas['world_object_shared_prefix']['position_descriptor_ptr'], DESCRIPTOR)
    put(memory, DESCRIPTOR, STATE)
    put(memory, command + 2, NODE)
    put(memory, command + 6, FRAMES)
    for head_matches, second_matches in ((True, False), (False, True), (False, False)):
        put(memory, STATE + attachment, second)
        put(memory, second + attachment, 0)
        memory[STATE + flags] = wanted if head_matches else wanted ^ 8
        memory[second + flags] = wanted if second_matches else wanted ^ 8
        put(memory, STATE + 8, 0)
        put(memory, second + 8, 0)
        memory[NODE:NODE + 18] = bytes(range(18))
        before = bytes(memory[NODE:NODE + 18])
        cpu.a[5], cpu.a[4] = OBJECT, command
        run(handler)
        assert cpu.a[4] == command + 10
        matched = STATE if head_matches else second if walks and second_matches else None
        if matched is not None:
            expected = bytearray(before)
            expected[6:10] = FRAMES.to_bytes(4, 'big')
            expected[10] &= ~1
            expected[16:18] = b'\0\0'
            assert read(memory, matched + 8) == NODE
            assert read(memory, (second if matched == STATE else STATE) + 8) == 0
            assert memory[NODE:NODE + 18] == expected
        else:
            assert read(memory, STATE + 8) == read(memory, second + 8) == 0
            assert memory[NODE:NODE + 18] == before


def test_hold_at_end_defers_xy_header_until_next_held_visit(machine):
    memory, cpu, run = machine
    cpu.a[4] = STATE
    put(memory, STATE + 8, NODE)
    put(memory, NODE + 6, FRAMES)
    put(memory, NODE + 12, XY)
    memory[NODE + 4:NODE + 6] = bytes((2, 64))
    memory[NODE + 10] = 4
    put(memory, NODE + 16, 0x0140, 2)
    put(memory, FRAMES, 0x20000)
    put(memory, XY, 0xFFFF8000)
    put(memory, STATE + 12, 0x00010002)
    run(0x951A)
    assert read(memory, STATE) == 0x20000 and memory[NODE + 10] == 5
    assert read(memory, STATE + 12) == 0x00010002
    run(0x951A)
    assert read(memory, STATE + 12) == 0xFFFF8000


def test_feedback_wrapper_preserves_context_across_register_clobbering_audio_callee(machine):
    memory, cpu, run = machine
    for i in range(8):
        cpu.d[i] = 0xD0000000 + i
        cpu.a[i] = 0xA0000000 + i
    cpu.a[6] = 0x90000
    before_d, before_a = list(cpu.d), list(cpu.a)
    # The original wrapper's JSR target is read from its original instruction.
    assert memory[BASE + 0x4D33A:BASE + 0x4D33C] == bytes.fromhex('4eb9')
    callee = read(memory, BASE + 0x4D33C)
    run(0x4D330, stop=callee - BASE)
    # Stub only the nested audio implementation. The wrapper and its stack
    # save/restore remain original bytes; deliberately clobber all other regs.
    put(memory, callee, 0x4E75, 2)
    for i in range(8):
        cpu.d[i] = 0x12340000 + i
        if i < 7:
            cpu.a[i] = 0x56780000 + i
    buffer = (C.c_uint8 * len(memory)).from_buffer(memory)
    trace = Trace()
    assert engine()(0, buffer, len(memory), C.byref(cpu), 32, 0x800, 0x802, None, C.byref(trace)) == 0
    assert trace.stop_reason == 1 and not trace.overflow
    assert not any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count])
    assert list(cpu.d)[1:] == before_d[1:]
    assert list(cpu.a)[1:7] == before_a[1:7]
    assert cpu.a[7] == 0x9004
    assert cpu.d[0] == 0x12340000 and cpu.a[0] == 0x56780000


@pytest.mark.parametrize('near,variant,sequence', [
    (True, 0, 0x49134), (True, 1, 0x4916C),
    (False, 0, 0x49150), (False, 1, 0x49188),
])
def test_proximity_sequence_selection_preserves_count_and_updates_mode(machine, near, variant, sequence):
    memory, cpu, run = machine
    cpu.a[2], cpu.a[4], cpu.a[6] = STATE, OBJECT, 0x90000
    cpu.d[0], cpu.d[1] = (0 if near else 44), 0  # Manhattan comparison at $7E74
    put(memory, STATE + 8, NODE)
    memory[STATE + 25] = variant << 5
    memory[NODE + 4:NODE + 6] = bytes((6, 64))
    put(memory, NODE + 6, FRAMES)
    memory[NODE + 10] = 1
    put(memory, NODE + 16, 0x0340, 2)
    # Isolate the documented audio side effect; its wrapper contract has its
    # own original-byte save/restore test above.
    put(memory, BASE + 0x4D330, 0x4E75, 2)
    before = bytes(memory[NODE:NODE + 18])
    run(0x7E74, stop=0x7F02)
    expected = bytearray(before)
    expected[6:10] = (BASE + sequence).to_bytes(4, 'big')
    expected[10] = 4
    expected[16:18] = b'\0\0'
    assert memory[NODE:NODE + 18] == expected
    assert read(memory, STATE + 8) == NODE


def test_all_recovered_node_and_replacement_sequences_have_exact_typed_bounds(machine, metadata):
    memory, _, _ = machine
    sequences = {}
    nodes = [e.addr - 6 for e in metadata.seeded_entities
             if e.struct_name == 'WorldPositionStateNode' and e.field_name == 'frame_sequence_ptr']
    assert len(nodes) == len(set(nodes)) == 89

    def require(sequence, count):
        assert sequence not in sequences or sequences[sequence] == count
        sequences[sequence] = count

    for offset in nodes:
        node = BASE + offset
        require(read(memory, node + 6) - BASE, memory[node + 4])
        assert read(memory, node + 12) == 0
        assert not memory[node + 10] & 8
    for layout in metadata.data_block_layouts:
        for element in layout.elements:
            if element.type_binding and element.type_binding['bound_type_id'] == 'world_behavior_node_sequence_command':
                command = BASE + layout.source_start + element.offset
                node = read(memory, command + 2)
                require(read(memory, command + 6) - BASE, memory[node + 4])
    # Two near variants are selected by the four-way proximity routine, not
    # initial node pointers; every eligible initialized state has count six.
    eligible = []
    for field in metadata.seeded_entities:
        if field.struct_name == 'world_position_render_state_prefix' and field.field_name == 'state_node_ptr':
            state = BASE + field.addr - 8
            if memory[state + 25] & 0x15 == 1 and not memory[state + 24] & 1:
                eligible.append(state)
                assert memory[read(memory, state + 8) + 4] == 6
    assert len(eligible) == 18
    require(0x49134, 6)
    require(0x4916C, 6)
    assert len(sequences) == 63
    elements = {l.source_start + e.offset: e for l in metadata.data_block_layouts for e in l.elements}
    for start, count in sequences.items():
        held, active = elements[start], elements[start + 4]
        assert held.name.endswith('_held') and active.name.endswith('_active')
        assert held.width == 4 and held.array_count == 1
        assert active.width == 4 * count and active.array_count == count
        assert held.array_stride == active.array_stride == 4
        assert held.type_binding['bound_type_id'] == active.type_binding['bound_type_id'] == 'WorldPositionDescriptorPointer'
    assert sum(n + 1 for n in sequences.values()) == 416
    tail = elements[0x491A4]
    assert tail.name == 'world_position_unassigned_frame_entries' and tail.width == 56 and tail.array_count == 14
