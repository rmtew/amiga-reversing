"""Original self-destruct console protocol with controlled RAM and real callees.

Entry/source stops are native listing coordinates. Full accepted submissions use
original audio dispatch, name resolution, UI update and compact text rendering.
BLIT-ready MMIO is a RAM shadow; no DMA or hardware scheduling is claimed.
Corrupt counters are bounded prefixes, not gameplay admission claims.
"""
import itertools

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_framebuffer_lifetime import APP, fill_rows
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
INPUT, VALIDATE, RENDER = 0x9CBE, 0x9DAA, 0x9DC2
PLAYER, FRONT = BASE+0x4C322, 0x78000
CARDS, QUALIFYING = range(0x20, 0x26), {0x21, 0x23, 0x24}


@pytest.fixture
def console(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    fill_rows(cpu, memory, run)
    slots = title_slots
    held = PLAYER+schemas['world_object_shared_prefix']['selected_item_id']
    cpu.d[0] = 0
    assert sequencer(cpu, memory, write)(0x4D7DE, budget=4096).stop_reason == 1
    cpu.a[6] = APP
    for name, value in [('app_front_bitplane_base', FRONT),
                        ('app_font_glyph_bitmap_table_ptr', BASE+0xA7E2),
                        ('app_font_glyph_layout_table_ptr', BASE+0xAAFE)]:
        write(APP+slots[name], value)
    write(APP+0x1E0, 0x70000)
    write(0xDFF01E, 0x40, 2)  # BLIT-ready shadow, no DMA execution.
    memory[BASE+0xA862:BASE+0xA862+128] = bytes(128)

    def prepare(*, state=1, item=0, cached=0x80, fire=255, ui=0, qualifying=0, submitted=0):
        cpu.a[6], cpu.sr = APP, 0x2000
        for name, value in [('app_self_destruct_state', state),
                            ('app_modal_last_selected_item_id', cached),
                            ('app_input_fire_pressed_ff', fire), ('app_ui_flags', ui),
                            ('app_self_destruct_qualifying_card_count', qualifying),
                            ('app_self_destruct_submitted_card_count', submitted),
                            ('app_context_flags', 0x15)]:
            write(APP+slots[name], value, 1)
        write(held, item, 1)
        names = APP+slots['app_self_destruct_submitted_name_ptrs']
        memory[names:names+12] = bytes(12)
        return names

    def submit(item):
        write(held, item, 1)
        trace = sequencer(cpu, memory, write)(INPUT, budget=100000)
        assert trace.stop_reason == 1 and 0 < trace.steps < 100000
        # Rendering exceeds the bounded range-summary capacity. Check guest
        # memory/return state directly, without claiming a complete write trace.
        assert cpu.a[7] == 0x9004

    return cpu, memory, read, write, run, slots, held, prepare, submit


def test_all_ui_fire_and_unchanged_item_bytes_gate_before_cache_update(console):
    cpu, memory, read, write, run, slots, held, prepare, submit = console
    cache = APP+slots['app_modal_last_selected_item_id']
    for value in range(256):
        prepare(ui=value, item=0, cached=0x80)
        submit(0)
        assert read(cache, 1) == (0x80 if value & 4 else 0)
        prepare(fire=value, item=0, cached=0x80)
        submit(0)
        assert read(cache, 1) == (0 if value else 0x80)
        prepare(item=value, cached=value)
        before = bytes(memory[APP:APP+0x400])
        submit(value)
        assert bytes(memory[APP:APP+0x400]) == before and read(held, 1) == value


def test_every_state_byte_caches_changed_selection_before_ignoring_invalid_item(console):
    cpu, memory, read, write, run, slots, held, prepare, submit = console
    for state in range(256):
        prepare(state=state, qualifying=9, submitted=2)
        submit(0)
        assert read(APP+slots['app_modal_last_selected_item_id'], 1) == 0
        assert read(APP+slots['app_self_destruct_state'], 1) == state
        assert read(APP+slots['app_self_destruct_qualifying_card_count'], 1) == 9
        assert read(APP+slots['app_self_destruct_submitted_card_count'], 1) == 2


def test_disk_state_accepts_only_sdi_id_across_all_item_bytes(console):
    cpu, memory, read, write, run, slots, held, prepare, submit = console
    for item in range(256):
        prepare(state=0, item=item)
        submit(item)
        accepted = item == 0x26
        assert read(APP+slots['app_self_destruct_state'], 1) == int(accepted)
        assert read(held, 1) == (0 if accepted else item)
        assert read(APP+slots['app_context_flags'], 1) == (0x55 if accepted else 0x15)
        assert read(APP+slots['app_self_destruct_submitted_card_count'], 1) == 0


def test_card_state_admits_exactly_six_ids_and_counts_only_three_colors(console):
    cpu, memory, read, write, run, slots, held, prepare, submit = console
    for item in range(256):
        names = prepare(item=item)
        submit(item)
        accepted = item in CARDS
        assert read(APP+slots['app_self_destruct_state'], 1) == 1
        assert read(APP+slots['app_self_destruct_submitted_card_count'], 1) == int(accepted)
        assert read(APP+slots['app_self_destruct_qualifying_card_count'], 1) == int(item in QUALIFYING)
        assert read(held, 1) == (0 if accepted else item)
        assert bool(read(names)) == accepted
        if accepted:
            pointer = read(names)
            assert bytes(memory[pointer:memory.index(0, pointer)]) == [
                b'Code WHITE', b'Code BLUE', b'Code GREY', b'Code SCARLET',
                b'Code OCHRE', b'Code BLACK'][item-0x20]
            assert read(APP+slots['app_modal_last_selected_item_id'], 1) == 0


SEQUENCES = list(itertools.permutations(sorted(QUALIFYING)))+[(x,)*3 for x in sorted(QUALIFYING)]+[
    (0x20, 0x21, 0x23), (0x21, 0x22, 0x24), (0x21, 0x23, 0x25)]


@pytest.mark.parametrize('cards', SEQUENCES)
def test_complete_three_card_calls_accept_any_qualifying_order_and_duplicates(console, cards):
    cpu, memory, read, write, run, slots, held, prepare, submit = console
    names = prepare()
    pointers = []
    for count, item in enumerate(cards, 1):
        submit(item)
        pointers.append(read(names+4*(count-1)))
        assert pointers[-1] and read(held, 1) == 0
        assert read(APP+slots['app_self_destruct_submitted_card_count'], 1) == count
        assert read(APP+slots['app_self_destruct_qualifying_card_count'], 1) == sum(x in QUALIFYING for x in cards[:count])
        expected = (255 if all(x in QUALIFYING for x in cards) else 2) if count == 3 else 1
        assert read(APP+slots['app_self_destruct_state'], 1) == expected
    assert (len(set(pointers)) == 1) == (len(set(cards)) == 1)
    before = bytes(memory[names:names+12])
    submit(0x21)
    assert bytes(memory[names:names+12]) == before
    assert read(APP+slots['app_self_destruct_submitted_card_count'], 1) == 3
    assert read(held, 1) == 0x21


def test_qualifying_counter_wrap_and_all_validator_bytes_are_original_byte_math(console):
    cpu, memory, read, write, run, slots, held, prepare, submit = console
    q, state = APP+slots['app_self_destruct_qualifying_card_count'], APP+slots['app_self_destruct_state']
    for count in range(256):
        prepare(item=0x21, qualifying=count)
        run(INPUT, stop=0x9D22)
        assert read(q, 1) == (count+1) & 255
        assert read(held, 1) == 0x21
        write(q, count, 1)
        run(VALIDATE, stop=0x9E18 if count == 3 else 0x9DA4)
        assert read(state, 1) == (255 if count == 3 else 2)


def test_submission_prefix_indexes_all_counter_bytes_without_a_three_slot_guard(console):
    cpu, memory, read, write, run, slots, held, prepare, submit = console
    for count in range(256):
        names = prepare(item=0x20, submitted=count)
        destination = names+4*count
        memory[destination:destination+4] = b'GUAR'
        cpu.d[0] = 0x20
        run(0x9D30, stop=0x9D4A)
        assert read(destination) == cpu.a[0] and read(destination) != int.from_bytes(b'GUAR', 'big')
        assert cpu.d[2] & 65535 == count+1
        assert read(held, 1) == 0x20
    # Three declared name slots remain the source/storage prefix. This bounded
    # original prefix proves no general admission check on a corrupt count.


def test_console_clear_writes_384_thirty_byte_rows_at_forty_byte_stride(console):
    cpu, memory, read, write, run, slots, held, prepare, submit = console
    prepare()
    start = FRONT+2+16*160
    memory[start-4:start+384*40+4] = b'\xA5'*(384*40+8)
    trace = sequencer(cpu, memory, write)(RENDER, stop=0x9DEA, budget=8192)
    assert trace.stop_reason == 1 and trace.steps < 8192
    for row in range(384):
        assert memory[start+40*row:start+40*row+30] == bytes(30)
        assert memory[start+40*row+30:start+40*row+40] == b'\xA5'*10
    assert memory[start-4:start] == b'\xA5'*4
    assert memory[start+384*40:start+384*40+4] == b'\xA5'*4
    assert cpu.a[0] == start+384*40 and cpu.d[7] & 65535 == 65535


def test_disk_then_three_blue_cards_arms_without_reloading_inherited_countdown(console):
    cpu, memory, read, write, run, slots, held, prepare, submit = console
    prepare(state=0)
    timer = APP+slots['app_self_destruct_service_ticks_remaining']
    write(timer, 0xBEEF, 2)
    submit(0x26)
    assert read(APP+slots['app_self_destruct_state'], 1) == 1
    for _ in range(3):
        submit(0x21)
        assert read(timer, 2) == 0xBEEF
    assert read(APP+slots['app_self_destruct_state'], 1) == 255
    assert read(APP+slots['app_self_destruct_qualifying_card_count'], 1) == 3
    assert read(APP+slots['app_self_destruct_submitted_card_count'], 1) == 3
    assert read(APP+slots['app_context_flags'], 1) == 0x55
