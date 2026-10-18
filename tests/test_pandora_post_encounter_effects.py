"""Original item-state broadcasts and fixed passage writes, without DMA."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, TABLE, FIRST, SECOND = 0x70000, BASE+0x300A, 0x81000, 0x81100


def two_objects(cpu_fixture, pointers=None):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj = schemas['world_object_shared_prefix']
    cpu.a[6] = APP
    memory[FIRST:FIRST+84] = b'\xA5'*84
    memory[SECOND:SECOND+84] = b'\x5A'*84
    write(FIRST+obj['world_object_flags'], 0, 1)
    write(SECOND+obj['world_object_flags'], 2, 1)
    for index, pointer in enumerate(pointers or [FIRST, SECOND, 0]):
        write(TABLE+4*index, pointer)
    return cpu, memory, obj, read, write, run


def test_all_byte_deltas_and_states_wrap_without_saturating_or_touching_inactive(cpu_fixture):
    cpu, memory, obj, read, write, run = two_objects(cpu_fixture)
    inactive = bytes(memory[SECOND:SECOND+84])
    offset = obj['item_state']
    for delta in range(256):
        cpu.d[0] = 0xCAFE0000 | delta
        for initial in range(256):
            write(FIRST+offset, initial, 1)
            run(0x86A6, budget=64)
            assert read(FIRST+offset, 1) == (initial+delta) & 255
            assert cpu.d[0] == 0xCAFE0000 | delta
    assert bytes(memory[SECOND:SECOND+84]) == inactive
    expected = bytearray(b'\xA5'*84)
    expected[obj['world_object_flags']] = 0
    expected[offset] = 254  # Last input: 255+255 modulo 256.
    assert bytes(memory[FIRST:FIRST+84]) == expected


def test_all_flag_bytes_gate_only_on_bit_one_and_preserve_registers(cpu_fixture):
    cpu, memory, obj, read, write, run = two_objects(cpu_fixture)
    for flags in range(256):
        write(FIRST+obj['world_object_flags'], flags, 1)
        write(FIRST+obj['item_state'], 7, 1)
        for i in range(8):
            cpu.d[i] = 0xCAFE0000+i
            if i < 6:
                cpu.a[i] = 0xBEEF0000+i
        cpu.d[0] = 0x1234FFF1
        before_d, before_a = list(cpu.d), list(cpu.a[:7])
        run(0x86A6, budget=64)
        assert read(FIRST+obj['item_state'], 1) == (7 if flags & 2 else 248)
        assert read(FIRST+obj['world_object_flags'], 1) == flags
        assert list(cpu.d) == before_d and list(cpu.a[:7]) == before_a
        assert cpu.a[7] == 0x9004


@pytest.mark.parametrize('delta', [-15, 15])
def test_original_35_record_table_includes_player_and_preserves_every_other_byte(cpu_fixture, delta):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj = schemas['world_object_shared_prefix']
    objects = []
    for i in range(36):
        p = read(TABLE+4*i)
        if not p:
            break
        objects.append(p)
    assert len(objects) == 35 and BASE+0x4C322 in objects
    expected = {}
    for index, p in enumerate(objects):
        write(p+obj['item_state'], index*7 & 255, 1)
        record = bytearray(memory[p:p+84])
        if not record[obj['world_object_flags']] & 2:
            record[obj['item_state']] = (record[obj['item_state']]+delta) & 255
        expected[p] = record
    cpu.d[0] = delta & 0xFFFFFFFF
    trace = sequencer(cpu, memory, write)(0x86A6, budget=1024)
    assert trace.stop_reason == 1 and trace.steps < 1024
    assert all(memory[p:p+84] == record for p, record in expected.items())
    assert cpu.a[7] == 0x9004
    # The write summary is bounded; full guest records are checked directly.


def test_duplicate_references_apply_twice_and_first_null_ends_scan(cpu_fixture):
    cpu, memory, obj, read, write, run = two_objects(cpu_fixture, [FIRST, FIRST, 0, SECOND])
    write(FIRST+obj['item_state'], 250, 1)
    write(SECOND+obj['world_object_flags'], 0, 1)
    inactive_tail = bytes(memory[SECOND:SECOND+84])
    cpu.d[0] = 15
    run(0x86A6, budget=64)
    assert read(FIRST+obj['item_state'], 1) == 24
    assert bytes(memory[SECOND:SECOND+84]) == inactive_tail
    write(TABLE, 0)
    run(0x86A6, budget=64)
    assert read(FIRST+obj['item_state'], 1) == 24


@pytest.mark.parametrize('entry', [0x4B10A, 0x4B112])
def test_bank_manager_and_thief_completion_tail_call_same_positive_broadcast(cpu_fixture, entry):
    cpu, memory, obj, read, write, run = two_objects(cpu_fixture)
    write(FIRST+obj['item_state'], 249, 1)
    inactive = bytes(memory[SECOND:SECOND+84])
    run(entry, budget=64)
    assert cpu.d[0] == 15 and read(FIRST+obj['item_state'], 1) == 8
    assert bytes(memory[SECOND:SECOND+84]) == inactive and cpu.a[7] == 0x9004


@pytest.mark.parametrize('entry,opens_passage', [(0x4B0CE, True), (0x4B0D6, False)])
def test_priest_and_shared_negative_tail_enqueue_original_message_then_broadcast(cpu_fixture, title_slots, entry, opens_passage):
    cpu, memory, obj, read, write, run = two_objects(cpu_fixture)
    queue = APP+title_slots['app_scrolling_message_queue_head']
    tail = APP+title_slots['app_scrolling_message_queue_tail']
    write(queue, 0x83000)
    write(queue+4, 0)
    write(tail, queue+4)
    write(APP+0x2A6, 32, 1)  # Active status message: defer rendering.
    write(FIRST+obj['item_state'], 7, 1)
    write(0x64BC, 0xAABBCCDD)
    write(0x64C0, 0xDEADBEEF)
    write(0x64C4, 0x12345678)
    trace = sequencer(cpu, memory, write)(entry, budget=2048)
    assert trace.stop_reason == 1 and trace.steps < 2048
    assert read(FIRST+obj['item_state'], 1) == 248
    assert read(SECOND+obj['item_state'], 1) == 0x5A
    assert read(queue+4) == BASE+0x4D096 and read(queue+8) == 0
    assert read(tail) == queue+8
    assert read(APP+title_slots['app_status_message_service_ticks_remaining'], 2) == 90
    assert read(0x64C0) == (0x1E928 if opens_passage else 0xDEADBEEF)
    assert read(0x64BC) == 0xAABBCCDD and read(0x64C4) == 0x12345678
    assert cpu.d[0] == 0xFFFFFFF1 and cpu.a[7] == 0x9004


def test_fixed_cell_coordinates_and_tile_collision_bits_are_distinct(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    assert (0x64C0-0x4000)//4 == 26*90+12
    assert (0x1E928-(BASE+0xD0A8))//128 == 49
    assert (0x24C28-(BASE+0xD0A8))//128 == 247
    assert not read(BASE+0xA822+49//8, 1) & (0x80 >> (49 % 8))
    assert read(BASE+0xA822+247//8, 1) & (0x80 >> (247 % 8))
    macro_id = read(BASE+0x3502+244*2, 2)
    assert macro_id == 450
    assert read(BASE+0x3F16+macro_id*18+6*2, 2) == 247*128


@pytest.mark.parametrize('entry,expected', [(0x78C4, 0x1E928), (0x9F38, 0x24C28)])
def test_combat_setup_and_restart_store_only_the_fixed_pointer(cpu_fixture, entry, expected):
    cpu, memory, schemas, read, write, run = cpu_fixture
    memory[0x64BC:0x64C8] = b'\xA5'*12
    before_d, before_a = list(cpu.d), list(cpu.a[:7])
    run(entry, stop=entry+8, budget=8)
    assert read(0x64C0) == expected
    assert memory[0x64BC:0x64C0] == memory[0x64C4:0x64C8] == b'\xA5'*4
    assert list(cpu.d) == before_d and list(cpu.a[:7]) == before_a


@pytest.mark.parametrize('callback,expected,delta', [
    (0, 0x1E928, 0), (0x652FC, 0x24C28, 0),
    (0x5B0CE, 0x1E928, -15), (0x5B10A, 0x24C28, 15),
    (0x5B112, 0x24C28, 15),
])
def test_completion_prefix_resets_only_for_nonnull_callback_and_priest_reopens(cpu_fixture, title_slots, callback, expected, delta):
    cpu, memory, obj, read, write, run = two_objects(cpu_fixture)
    queue = APP+title_slots['app_scrolling_message_queue_head']
    write(queue, 0x83000)
    write(queue+4, 0)
    write(APP+title_slots['app_scrolling_message_queue_tail'], queue+4)
    write(APP+0x2A6, 32, 1)
    write(FIRST+obj['interaction_completion_callback'], callback)
    write(FIRST+obj['item_state'], 7, 1)
    write(0x64C0, 0x1E928)
    cpu.a[4], cpu.a[5] = 0xABCDEF00, FIRST
    advance = sequencer(cpu, memory, write)
    # Stop before state exchange, defeat marking and UI restore. Those are
    # separate effects, including the already documented NULL-node boundary.
    trace = advance(0x79EC, stop=0x7A06, budget=2048)
    assert trace.stop_reason == 1 and trace.steps < 2048
    assert read(0x64C0) == expected
    assert read(FIRST+obj['item_state'], 1) == (7+delta) & 255
    assert read(FIRST+obj['world_object_flags'], 1) == 0
    assert cpu.a[4] == 0xABCDEF00 and cpu.a[5] == FIRST and cpu.a[7] == 0x9000
