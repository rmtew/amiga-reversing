"""Original terminal scan contracts; initialized records are not a scan bound."""
from __future__ import annotations

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
TABLE, END, PLAYER = 0x8CA0, 0x8CC8, 0x5C322


def initial_records(memory):
    records = []
    for i in range(10):
        address = int.from_bytes(memory[BASE+TABLE+4*i:BASE+TABLE+4*i+4], 'big')
        records.append((address, int.from_bytes(memory[address:address+2], 'big'),
                        int.from_bytes(memory[address+2:address+4], 'big')))
    return records


@pytest.mark.parametrize('index', range(10))
def test_each_initialized_location_selects_its_inline_text(cpu_fixture, index):
    cpu, memory, schemas, read, write, run = cpu_fixture
    record, x, y = initial_records(memory)[index]
    write(PLAYER+schemas['world_object_shared_prefix']['world_x'], x, 2)
    write(PLAYER+schemas['world_object_shared_prefix']['world_y'], y, 2)
    run(0x9140, stop=0x917A, budget=1024)
    assert cpu.a[2] == record+4 and cpu.d[4] & 0xFFFF == 0
    assert cpu.a[0] == BASE+END+4
    assert memory[record+4:record+8] != bytes(4)


def test_equal_distance_retains_first_record(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    write(PLAYER+0x30, 336, 2)
    write(PLAYER+0x32, 208, 2)
    run(0x9140, stop=0x917A, budget=1024)
    assert cpu.a[2] == initial_records(memory)[0][0]+4
    assert cpu.d[4] & 0xFFFF == 96


def test_word_distance_sum_can_wrap_to_zero(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    record, x, y = initial_records(memory)[0]
    write(PLAYER+0x30, (x+0x8000) & 0xFFFF, 2)
    write(PLAYER+0x32, (y+0x8000) & 0xFFFF, 2)
    run(0x9140, stop=0x917A, budget=1024)
    assert cpu.a[2] == record+4 and cpu.d[4] & 0xFFFF == 0
    # This is original WORD arithmetic, not a general mathematical L1 guarantee.


def test_scan_accepts_an_eleventh_record_when_initial_null_is_replaced(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    record, x, y = 0x90000, 100, 100
    write(BASE+END, record)
    write(BASE+END+4, 0)
    write(record, x, 2)
    write(record+2, y, 2)
    memory[record+4:record+10] = b'EXTRA\0'
    write(PLAYER+0x30, x, 2)
    write(PLAYER+0x32, y, 2)
    run(0x9140, stop=0x917A, budget=1024)
    assert cpu.a[2] == record+4 and cpu.d[4] & 0xFFFF == 0
    assert cpu.a[0] == BASE+END+8
    # Explicit changed-data model; stop before display. The ten-entry physical
    # prefix is not a runtime admission check and original file bytes stay intact.


def test_card_display_accepts_exactly_eight_byte_ids(cpu_fixture):
    from tests.test_pandora_render_order import sequencer
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = 0x39FC
    advance = sequencer(cpu, memory, write)
    for item in range(256):
        write(PLAYER+schemas['world_object_shared_prefix']['selected_item_id'], item, 1)
        trace = advance(0x90F0, budget=6)
        assert trace.stop_reason == 3
        assert cpu.pc == BASE+(0x9108 if 48 <= item < 56 else 0x91EC), item
        assert cpu.d[0] == (item-48) & 255
        assert cpu.a[7] == 0x9000  # Stop before the accepted-selector push.


def test_eight_display_selectors_resolve_five_clearance_labels(cpu_fixture):
    from tests.test_pandora_render_order import sequencer
    cpu, memory, schemas, read, write, run = cpu_fixture
    advance = sequencer(cpu, memory, write)
    expected = ['Omega', 'Pi   ', 'Alpha', 'Pi   ', 'None ', 'Delta', 'None ', 'None ']
    for selector, text in enumerate(expected):
        cpu.d[0] = selector
        assert advance(0x9190, budget=2).stop_reason == 3
        address = cpu.a[3]
        end = memory.index(0, address)
        assert bytes(memory[address:end]).decode('ascii') == text
        assert cpu.pc == BASE+0x9196
    # This is the eight-entry display domain, not a proof that the distinct
    # six-entry security-tier table accepts every displayed card ID.
