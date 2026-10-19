"""Original record-index arithmetic retains alignment without proving bounds."""

import pytest

from tests.test_pandora_inventory_cursor import APP
from tests.test_pandora_inventory_cursor import cursor as cursor
from tests.test_pandora_state_transitions import cpu_fixture as cpu_fixture
from tests.test_pandora_title_data import title_slots as title_slots

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)


@pytest.mark.parametrize('row', [0, 1, 2, 3, 128, 0x1FE0])
def test_body_inventory_index_preserves_high_byte_and_can_leave_four_record_prefix(cursor, row):
    cpu, memory, read, write, names, slots, obj, constants, player, palette, app, value, call, reset = cursor
    npc, inventory = 0x82000, 0x83000
    memory[npc:npc+84] = bytes(84)
    write(npc+obj['inventory_slots_ptr'], inventory)
    cpu.a[4], cpu.a[5], cpu.a[6] = player, npc, APP
    app('inventory_cursor_x', constants['INVENTORY_CURSOR_BODY_COLUMN_X'])
    app('inventory_cursor_y', (constants['INVENTORY_CURSOR_FIRST_ROW_Y']+8*row) & 0xFFFF)
    write(player+obj['selected_item_id'], 54, 1)
    # Original WORD subtraction/shift, followed by BYTE AND #6 on D1.
    raw = ((8*row) & 0xFFFF) >> 2
    displacement = (raw & 0xFF00) | (raw & 6)
    memory[inventory+displacement:inventory+displacement+2] = bytes([18, 0xA5])
    before = bytes(memory[inventory-2:inventory+0x4008])
    call(0x2A48, stop=0x2A7C, budget=32)
    assert cpu.d[1] & 0xFFFF == displacement and displacement % 2 == 0
    assert cpu.d[2] & 255 == 18
    expected = bytearray(before)
    expected[2+displacement] = 54
    assert bytes(memory[inventory-2:inventory+0x4008]) == expected
    assert read(inventory+displacement+1, 1) == 0xA5
    assert (displacement >= 8) == (row >= 128)
    # Stop before the separate packed display-ID access, whose index is also
    # unchecked. No instruction, helper or original data table is patched.
