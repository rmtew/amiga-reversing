"""Original outcome/rank calls with controlled RAM and the real message FIFO.

Entry coordinates come from native symbol inspection. No instructions/callees
are patched; these calls do not establish ordinary gameplay reachability.
"""
import re

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_message_queue import initialize, APP, HEAD, LIMIT, TAIL, CONTEXT

OUTCOME, SELECT = 0x4C9AE, 0x4CA80
PLAYER = BASE+0x4C322
RANKS = [0x5CC87, 0x5CC99, 0x5CCA8, 0x5CCB9, 0x5CCCA, 0x5CCDE]
THRESHOLDS = [5, 10, 12, 14, 18]


def text(memory, pointer):
    return bytes(memory[pointer:memory.index(0, pointer)])


def rank_pointer(defeats):
    return RANKS[sum(defeats >= threshold for threshold in THRESHOLDS)]


@pytest.fixture
def outcome(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    slots = title_slots
    obj = schemas['world_object_shared_prefix']
    held, flags = PLAYER+obj['selected_item_id'], PLAYER+obj['world_object_flags']

    def prepare(*, event=8, destruction=0, earth=1, salvage=0, defeats=0,
                carried=(0, 0, 0, 0), holding=0, occupancy=0):
        initialize(cpu_fixture, slots, occupancy)
        write(APP+CONTEXT, 32, 1)  # Real enqueue, no immediate UI rendering.
        for index in range(occupancy):
            write(APP+HEAD+4*index, 0x80000+index*4)
        for name, value, width in [
            ('app_game_event_flags', event, 1), ('app_self_destruct_state', destruction, 1),
            ('app_earth_orbit_countdown_bcd', earth, 2), ('app_salvage_item_count', salvage, 1),
            ('app_defeated_object_count', defeats, 1)]:
            write(APP+slots[name], value, width)
        start = APP+slots['app_carried_item_ids']
        memory[start:start+4] = bytes(carried)
        write(held, holding, 1)
        write(flags, 0xA5, 1)
        return start

    def invoke():
        run(OUTCOME, budget=4096)
        assert cpu.a[7] == 0x9004
        return [read(APP+HEAD+4*i) for i in range(16) if read(APP+HEAD+4*i)]

    return cpu, memory, read, write, slots, held, flags, prepare, invoke


def test_every_unsigned_defeat_byte_selects_one_of_six_original_messages(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    for defeats in range(256):
        write(APP+title_slots['app_defeated_object_count'], defeats, 1)
        cpu.d[0] = 0xABCDEF00
        run(SELECT)
        assert cpu.a[0] == rank_pointer(defeats)
        assert cpu.d[0] == 0xABCDEF00+defeats
        assert cpu.a[7] == 0x9004
    assert [text(memory, p) for p in RANKS] == [
        b'. . DOG  MEAT . .', b'. . KILLER . .', b'. . ASSASSIN . .',
        b'. . RUTHLESS . .', b'. . MAD  PSYCHO . .', b'. . SON  OF  SATAN . .']


def test_all_self_destruct_bytes_select_by_sign_then_earth_word_zero(outcome):
    cpu, memory, read, write, slots, held, flags, prepare, invoke = outcome
    for destruction in range(256):
        for escaped, earth in [(False, 0), (True, 0), (False, 0xFFFF), (True, 0xFA09)]:
            prepare(event=8 if escaped else 0, destruction=destruction, earth=earth)
            messages = invoke()
            assert len(messages) == 3
            first = text(memory, messages[0])
            if destruction & 128:
                assert b'PANDORA  IS  DESTROYED' in first
                assert (b'EARTH  IS  SAVED' in first) == bool(earth)
            else:
                assert (b'YOU  HAVE  ESCAPED' in first) == escaped
                assert (b'FAILED  TO  SOLVE' in first) == (not escaped)
            assert text(memory, messages[1]).startswith(
                b'THE  MERCENARY' if escaped else b'YOUR  POSTHUMOUS')
            assert messages[2] == RANKS[0]


def test_latch_prevents_every_effect_for_all_previously_latched_flag_bytes(outcome):
    cpu, memory, read, write, slots, held, flags, prepare, invoke = outcome
    for event in range(256):
        if not event & 64:
            continue
        prepare(event=event, salvage=251, carried=(0x17,)*4, holding=0xA4, occupancy=14)
        before_app = bytes(memory[APP:APP+0x400])
        before_player = bytes(memory[PLAYER:PLAYER+80])
        invoke()
        assert bytes(memory[APP:APP+0x400]) == before_app
        assert bytes(memory[PLAYER:PLAYER+80]) == before_player


def test_all_salvage_bytes_wrap_and_select_science_or_mercenary_after_count(outcome):
    cpu, memory, read, write, slots, held, flags, prepare, invoke = outcome
    science = [0x5CCF5, 0x5CD0B, 0x5CD25, 0x5CD3E, 0x5CD57]
    for count in range(256):
        prepare(salvage=count, defeats=14, carried=(0x17,)*4, holding=0xB7)
        messages = invoke()
        counted = (count+4) & 255
        assert read(APP+slots['app_salvage_item_count'], 1) == counted
        assert messages[-1] == (rank_pointer(14) if counted < 6 else science[min(counted-6, 4)])
        assert (b'SCIENCE' in text(memory, messages[1])) == (counted >= 6)
        assert read(held, 1) == 0xB7 and read(flags, 1) == 0xA5
        assert read(APP+slots['app_game_event_flags'], 1) == 72


def test_only_four_carried_slots_count_and_posthumous_sets_held_item_bit_one(outcome):
    cpu, memory, read, write, slots, held, flags, prepare, invoke = outcome
    for item in range(256):
        carried = prepare(event=0, salvage=254, defeats=18, carried=(0x17, 0x1A, 0x70, 0), holding=item)
        # A qualifying item immediately after the four carried slots is excluded.
        write(carried+4, 0x17, 1)
        messages = invoke()
        assert read(APP+slots['app_salvage_item_count'], 1) == 0
        assert read(carried+4, 1) == 0x17
        assert read(held, 1) == item | 2 and read(flags, 1) == 0xA5
        assert b'POSTHUMOUS' in text(memory, messages[1]) and messages[2] == RANKS[-1]
        before = bytes(memory[APP:APP+0x400])
        assert invoke() == messages and bytes(memory[APP:APP+0x400]) == before


@pytest.mark.parametrize('occupancy', [0, 14, 15, 16])
def test_queue_capacity_does_not_rollback_latch_count_or_held_item(outcome, occupancy):
    cpu, memory, read, write, slots, held, flags, prepare, invoke = outcome
    prepare(event=0, salvage=7, defeats=14, carried=(0x17,)*4, holding=0x80, occupancy=occupancy)
    messages = invoke()
    assert len(messages) == min(occupancy+3, 16)
    assert read(APP+TAIL) == APP+HEAD+4*min(occupancy+3, 16)
    assert read(APP+LIMIT) == 0
    assert read(APP+slots['app_game_event_flags'], 1) == 64
    assert read(APP+slots['app_salvage_item_count'], 1) == 11
    assert read(held, 1) == 0x82 and read(flags, 1) == 0xA5
    final = text(memory, rank_pointer(14))
    units = len(re.findall(b' +', final))+bool(final.replace(b' ', b''))
    assert read(APP+slots['app_status_message_service_ticks_remaining'], 2) == units*10
