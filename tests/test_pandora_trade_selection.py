"""Original trade policy and ordered exchange writes in initialized flat RAM."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer
from tests.test_pandora_framebuffer_lifetime import APP, fill_rows

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
NPC, PLAYER, INVENTORY, OFFERS = 0x82000, BASE+0x4C322, 0x83000, 0x83100
TABLE = BASE+0x300A


@pytest.fixture
def trade(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    fill_rows(cpu, memory, run)
    obj = schemas['world_object_shared_prefix']
    memory[NPC:NPC+84] = bytes(84)
    write(NPC+obj['inventory_slots_ptr'], INVENTORY)
    write(NPC+obj['trade_offer_table_ptr'], OFFERS)
    write(NPC+obj['selected_item_id'], 3, 1)
    write(NPC+obj['item_definition_id'], 2, 1)
    write(PLAYER+obj['selected_item_id'], 2, 1)
    write(PLAYER+obj['world_object_flags'], 0, 1)
    for pointer in [NPC, PLAYER]:
        write(pointer+obj['world_x'], 400, 2)
        write(pointer+obj['world_y'], 400, 2)
    memory[INVENTORY:INVENTORY+12] = bytes([0,0]*6)
    memory[OFFERS:OFFERS+12] = bytes([40,10,41,20,42,30,43,40,0xF0,0xB0,0xA5,0x5A])
    write(APP+title_slots['app_nearest_object_ptr'], NPC)
    write(APP+title_slots['app_ui_flags'], 4, 1)  # Holding-name refresh returns directly.
    write(APP+title_slots['app_input_fire_pressed_ff'], 0, 1)
    write(APP+0x1E0, 0x70000)
    write(APP+0x1D4, 0x78000)
    write(0xDFF01E, 0x40, 2)
    queue = APP+title_slots['app_scrolling_message_queue_head']
    write(queue, 0x84000)
    write(queue+4, 0)
    write(APP+title_slots['app_scrolling_message_queue_tail'], queue+4)
    write(APP+0x2A6, 32, 1)  # Preexisting status message avoids immediate status drawing.
    cpu.a[4], cpu.a[5], cpu.a[6] = PLAYER, NPC, APP
    return cpu, memory, obj, read, write, run, title_slots, queue


def test_every_item_byte_and_high_register_bits_preserve_exact_combat_range(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for high in [0, 0x12345600, 0xFFFFFF00]:
        for item in range(256):
            cpu.d[0] = high | item
            run(0x7CE4)
            assert cpu.d[0] == high | ((item-7) & 255)
            assert bool(cpu.sr & 1) == (7 <= item <= 21)


def test_all_matched_threshold_state_pairs_use_strict_unsigned_less_than(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    cpu.a[2] = OFFERS
    for threshold in range(256):
        write(OFFERS+1, threshold, 1)
        for state in range(256):
            write(NPC+obj['item_state'], state, 1)
            run(0x7C36, stop=0x7C40 if threshold < state else 0x7C46, budget=8)


def test_counteroffer_all_threshold_value_pairs_keep_only_positive_gaps_below_128(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    memory[INVENTORY:INVENTORY+8] = bytes([2,0,0,0,1,255,0,0])
    before = bytes(memory[INVENTORY:INVENTORY+8])
    for threshold in range(256):
        for value in range(256):
            write(INVENTORY+1, value, 1)
            cpu.d[0], cpu.a[1] = threshold, 0x87654321
            write(NPC+obj['selected_item_id'], 6, 1)
            write(NPC+obj['world_object_flags'], 0xA0, 1)
            accepted = 1 <= threshold-value <= 127
            run(0x7C8E, stop=0x7CCE if accepted else None, budget=128)
            assert read(NPC+obj['selected_item_id'], 1) == (2 if accepted else 6)
            assert read(NPC+obj['world_object_flags'], 1) == (0xA8 if accepted else 0xA0)
            assert cpu.a[0] == INVENTORY+8
            if accepted:
                assert cpu.a[1] == INVENTORY and cpu.d[3] & 255 == threshold-value
            else:
                assert cpu.sr & 1
    assert bytes(memory[INVENTORY:INVENTORY+8]) == before[:1]+b'\xFF'+before[2:]


@pytest.mark.parametrize('items,values,threshold,winner', [
    ([2,3,4,5], [40,40,10,20], 50, 0),
    ([2,3,4,5], [1,40,49,30], 50, 2),
    ([0,1,4,5], [49,49,40,40], 50, 2),
    ([2,3,4,5], [50,51,255,0], 50, 3),
    ([2,3,4,5], [0,1,2,3], 200, None),
])
def test_counteroffer_first_ties_skips_reserved_ids_and_does_not_consume_slots(trade, items, values, threshold, winner):
    cpu, memory, obj, read, write, run, slots, queue = trade
    memory[INVENTORY:INVENTORY+8] = bytes(v for pair in zip(items, values) for v in pair)
    original = bytes(memory[INVENTORY:INVENTORY+8])
    cpu.d[0] = threshold
    run(0x7C8E, stop=0x7CCE if winner is not None else None, budget=128)
    assert read(NPC+obj['selected_item_id'], 1) == (items[winner] if winner is not None else 3)
    if winner is not None:
        assert cpu.a[1] == INVENTORY+2*winner
    assert bytes(memory[INVENTORY:INVENTORY+8]) == original


def test_full_counteroffer_queues_message_draws_name_and_returns_clear_carry(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    memory[INVENTORY:INVENTORY+8] = bytes([2,40,3,40,4,10,5,20])
    cpu.d[0] = 50
    trace = sequencer(cpu, memory, write)(0x7C8E, budget=20000)
    assert trace.stop_reason == 1 and trace.steps < 20000
    assert read(NPC+obj['selected_item_id'], 1) == 2
    assert read(NPC+obj['world_object_flags'], 1) == 8
    assert memory[INVENTORY:INVENTORY+8] == bytes([2,40,3,40,4,10,5,20])
    assert read(queue+4) == BASE+0x7C65 and read(queue+8) == 0
    assert read(APP+slots['app_status_message_service_ticks_remaining'], 2) == 80
    assert not cpu.sr & 1 and cpu.a[5] == NPC and cpu.a[7] == 0x9004


def test_full_predicate_accepted_offer_suppresses_combat_even_after_success_clear_carry(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    write(NPC+obj['item_state'], 51, 1)
    memory[INVENTORY:INVENTORY+8] = bytes([2,40,3,40,4,10,5,20])
    memory[OFFERS:OFFERS+8] = bytes([2,50,6,1,6,2,6,3])
    trace = sequencer(cpu, memory, write)(0x7BBA, budget=20000)
    assert trace.stop_reason == 1 and trace.steps < 20000
    assert read(NPC+obj['world_object_flags'], 1) == 8 and cpu.sr & 1
    assert read(queue+4) == BASE+0x7C65


def test_predicate_disabled_flag_and_no_matching_offer_return_set_carry_without_writes(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    for flags in [0, 1, 2, 4, 8, 16, 128, 255]:
        write(NPC+obj['world_object_flags'], flags, 1)
        before = bytes(memory[NPC:NPC+84])
        run(0x7BBA, budget=128)
        assert cpu.sr & 1 and bytes(memory[NPC:NPC+84]) == before
        assert read(queue+4) == 0


def test_predicate_combat_item_and_empty_fallback_return_clear_carry(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    for item in range(7,22):
        write(NPC+obj['selected_item_id'], item, 1)
        run(0x7BBA, budget=128)
        assert not cpu.sr & 1 and read(NPC+obj['selected_item_id'], 1) == item
    for npc, player in [(0,0), (0,1), (1,0), (1,1), (2,7)]:
        write(NPC+obj['selected_item_id'], npc, 1)
        write(PLAYER+obj['selected_item_id'], player, 1)
        run(0x7BBA, budget=128)
        assert not cpu.sr & 1 and read(NPC+obj['selected_item_id'], 1) == npc


@pytest.mark.parametrize('route', ['player_combat_item', 'rejected_offer'])
@pytest.mark.parametrize('first_slot', [0, 1, 3])
def test_first_combat_inventory_item_is_selected_without_consumption(trade, route, first_slot):
    cpu, memory, obj, read, write, run, slots, queue = trade
    inventory = bytearray([2,10,3,20,4,30,5,40])
    inventory[2*first_slot] = 7+first_slot
    if first_slot < 3:
        inventory[6] = 7  # A later lower ID must not replace the first match.
    memory[INVENTORY:INVENTORY+8] = inventory
    write(PLAYER+obj['selected_item_id'], 7 if route=='player_combat_item' else 2, 1)
    write(NPC+obj['item_state'], 50, 1)
    memory[OFFERS:OFFERS+8] = bytes([2,50,3,10,4,20,5,30])
    trace = sequencer(cpu, memory, write)(0x7BBA, budget=20000)
    assert trace.stop_reason == 1 and trace.steps < 20000 and not cpu.sr & 1
    assert read(NPC+obj['selected_item_id'], 1) == 7+first_slot
    assert memory[INVENTORY:INVENTORY+8] == inventory
    assert read(NPC+obj['world_object_flags'], 1) == 0
    assert read(queue+4) == (BASE+0x7C50 if route=='rejected_offer' else 0)
    if route == 'rejected_offer':
        assert read(APP+slots['app_status_message_service_ticks_remaining'], 2) == 50


def test_global_selection_clear_visits_all_35_objects_including_inactive(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    offset = schemas['world_object_shared_prefix']['world_object_flags']
    pointers = [read(TABLE+4*i) for i in range(35)]
    assert read(TABLE+35*4) == 0
    snapshots = {}
    for p in pointers:
        write(p+offset, 255, 1)
        snapshots[p] = bytearray(memory[p:p+84])
        snapshots[p][offset] = 247
    trace = sequencer(cpu, memory, write)(0x7BA6, budget=512)
    assert trace.stop_reason == 1 and all(memory[p:p+84]==data for p,data in snapshots.items())
    assert cpu.a[0] == TABLE+36*4 and cpu.d[0] == 0


def test_exchange_all_first_match_and_one_past_combinations_preserve_outer_fences(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    for inv_index in range(5):
        for offer_index in range(5):
            inv = bytearray([40,10,41,20,42,30,43,40,0xF0,0xB0])
            offers = bytearray([50,11,51,21,52,31,53,41,0xF1,0xB1])
            if inv_index < 4:inv[2*inv_index]=5
            if offer_index < 4:offers[2*offer_index]=6
            memory[INVENTORY-1:INVENTORY+11] = b'\xA5'+inv+b'\x5A'
            memory[OFFERS-1:OFFERS+11] = b'\xC7'+offers+b'\x3C'
            write(PLAYER+obj['selected_item_id'], 6, 1)
            write(NPC+obj['selected_item_id'], 5, 1)
            write(NPC+obj['world_object_flags'], 0xA8, 1)
            write(APP+slots['app_input_fire_pressed_ff'], 255, 1)
            run(0x2F56, stop=0x2F9C, budget=128)
            inv[2*inv_index]=6
            inv[2*inv_index+1]=offers[2*offer_index+1]
            offers[2*offer_index]=0
            assert memory[INVENTORY-1:INVENTORY+11] == b'\xA5'+inv+b'\x5A'
            assert memory[OFFERS-1:OFFERS+11] == b'\xC7'+offers+b'\x3C'
            assert read(PLAYER+obj['selected_item_id'], 1) == 5
            assert read(NPC+obj['world_object_flags'], 1) == 0xA0


def test_exchange_aliases_observe_the_earlier_inventory_store(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    write(NPC+obj['trade_offer_table_ptr'], INVENTORY)
    memory[INVENTORY:INVENTORY+10] = bytes([5,37,2,4,3,5,4,6,0xF0,0xB0])
    write(PLAYER+obj['selected_item_id'], 6, 1)
    write(NPC+obj['selected_item_id'], 5, 1)
    write(APP+slots['app_input_fire_pressed_ff'], 255, 1)
    run(0x2F56, stop=0x2F9C, budget=128)
    assert memory[INVENTORY:INVENTORY+10] == bytes([0,37,2,4,3,5,4,6,0xF0,0xB0])
    assert read(PLAYER+obj['selected_item_id'], 1) == 5


def test_full_exchange_updates_both_selected_items_and_returns_after_real_audio(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    cpu.d[0] = 0
    trace = sequencer(cpu, memory, write)(0x4D7DE, budget=4096)
    assert trace.stop_reason == 1
    cpu.a[4], cpu.a[5], cpu.a[6] = PLAYER, NPC, APP
    memory[INVENTORY:INVENTORY+8] = bytes([5,10,2,20,3,30,4,40])
    memory[OFFERS:OFFERS+8] = bytes([6,37,3,21,4,31,5,41])
    write(PLAYER+obj['selected_item_id'], 6, 1)
    write(NPC+obj['selected_item_id'], 5, 1)
    write(NPC+obj['world_object_flags'], 8, 1)
    write(APP+slots['app_input_fire_pressed_ff'], 255, 1)
    write(TABLE, NPC)
    write(TABLE+4, PLAYER)
    write(TABLE+8, 0)
    trace = sequencer(cpu, memory, write)(0x2F56, budget=30000)
    assert trace.stop_reason == 1 and trace.steps < 30000
    assert read(PLAYER+obj['selected_item_id'], 1) == 5
    assert read(NPC+obj['selected_item_id'], 1) == 6
    assert memory[INVENTORY:INVENTORY+8] == bytes([6,37,2,20,3,30,4,40])
    assert memory[OFFERS:OFFERS+8] == bytes([0,37,3,21,4,31,5,41])
    assert not read(NPC+obj['world_object_flags'], 1) & 8 and cpu.a[7] == 0x9004
    assert read(queue+4) == BASE+0x7D00


def test_nearby_fire_zero_preserves_every_npc_flag_byte_and_item_tables(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    for flags in range(256):
        write(NPC+obj['world_object_flags'], flags, 1)
        before = bytes(memory[NPC:NPC+84])
        run(0x2EE6, budget=256)
        assert bytes(memory[NPC:NPC+84]) == before
    assert read(PLAYER+obj['selected_item_id'], 1) == 2 and read(queue+4) == 0


def test_thief_automatic_loss_handles_all_normal_item_bytes_without_fire(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    write(NPC+obj['item_definition_id'], 68, 1)
    before = bytes(memory[NPC:NPC+84])
    for item in range(2,256):
        write(PLAYER+obj['selected_item_id'], item, 1)
        write(APP+slots['app_scrolling_message_queue_tail'], queue+4)
        write(queue+4, 0)
        write(NPC+obj['interaction_message_ptr'], BASE+0x7C50)
        trace = sequencer(cpu, memory, write)(0x2EE6, budget=2048)
        assert trace.stop_reason == 1 and trace.steps < 2048
        assert read(PLAYER+obj['selected_item_id'], 1) == 0
        assert read(queue+4) == BASE+0x7C50
    expected = bytearray(before)
    expected[obj['interaction_message_ptr']:obj['interaction_message_ptr']+4] = (BASE+0x7C50).to_bytes(4,'big')
    assert memory[NPC:NPC+84] == expected


def test_trade_announcement_literal_ends_at_the_next_opcode_zero(trade):
    cpu, memory, obj, read, write, run, slots, queue = trade
    text = bytes(memory[BASE+0x7D00:BASE+0x7D24])
    assert text == b'..... YOU HAVE TRADED OBJECTS .....\0'
    cpu.a[0] = BASE+0x7D00
    run(0x99DE, budget=1024)
    assert read(APP+slots['app_status_message_service_ticks_remaining'],2) == 60
