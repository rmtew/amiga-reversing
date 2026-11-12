"""Original bomb-service and ingredient phases with supplied RAM.

Stop at the next phase or display handoff. These are not disk/save acceptance,
normal-game reachability, object lifetime or complete mission/UI tests.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, STACK

APP_NAMES = [
    'professor_taymar_delivered_flag', 'neutron_bomb_ready_flag',
    'neutron_bomb_spawn_countdown', 'inside_structure_flag',
    'selected_celestial_body_index', 'free_object_count', 'free_object_stack_cursor',
    'distant_object_count', 'distant_objects_cursor', 'station_sequence_index',
    'model_type_population_counts', 'taymar_delivered_model_counts_prefix',
    'bomb_ingredient_set_complete_flag', 'shared_inventory_depot_message_pointers',
    'current_structure_service_id', 'neutron_bomb_order_requested_flag',
    'professor_taymar_aboard_flag',
]
GLOBAL_NAMES = [
    'neutron_bomb_ingredient_model_types', 'neutron_bomb_ingredient_name_pointers',
    'depot_text_we_still_require_these', 'station_sequence_bomb_spawn_countdowns',
    'depot_dialogue_tick', 'taymar_dialogue_state',
    'taymar_intro_message_index', 'taymar_intro_message_index_mask',
    'depot_dialogue_pause_countdown', 'display_event_message_line', 'event_message_pointers',
]
OBJECT, FREE, DISTANT = 0x85000, 0x84000, 0x84100


@pytest.fixture(scope='module')
def symbols(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('taymar-delivery'); asm, out = folder/'map.s', folder/'map.raw'
    names = APP_NAMES + GLOBAL_NAMES
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin',
        '-m68000', '-no-opt', '-I'+str(target/'includes'), '-o', str(out), str(asm)],
        cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    data = out.read_bytes(); tail = 4*len(names)
    assert data[:-tail] == original_image[0]
    values = struct.unpack('>'+'I'*len(names), data[-tail:])
    return {n: v+(APP if n in APP_NAMES else 0) for n,v in zip(names, values)}


@pytest.mark.parametrize('mask', range(256))
def test_all_ingredient_subsets_build_reverse_order_missing_list_without_consuming_counts(original_image, memory, symbols, mask):
    m, f = memory, symbols
    types = list(m[f['neutron_bomb_ingredient_model_types']:f['neutron_bomb_ingredient_model_types']+8])
    counts, dest = f['taymar_delivered_model_counts_prefix'], f['shared_inventory_depot_message_pointers']
    m[counts:counts+104] = bytes(104)
    for i,t in enumerate(types): m[counts+t] = (1 if i%2 else 255) if mask & (1<<i) else 0
    before = bytes(m[counts:counts+104]); m[dest-4:dest+44] = b'\xCC'*48
    m[f['professor_taymar_delivered_flag']] = 255
    m[f['bomb_ingredient_set_complete_flag']] = 0x55
    cpu = state(m, 0x34380); run(original_image, m, cpu, {0x343FC})
    expected = [f['depot_text_we_still_require_these']]
    expected += [get(m, f['neutron_bomb_ingredient_name_pointers']+4*i)
                 for i in reversed(range(8)) if not mask & (1<<i)]
    expected += [0xFFFFFFFF]
    assert [get(m, dest+4*i) for i in range(len(expected))] == expected
    assert bytes(m[dest-4:dest]) == b'\xCC'*4
    assert bytes(m[dest+4*len(expected):dest+44]) == b'\xCC'*(44-4*len(expected))
    assert bytes(m[counts:counts+104]) == before
    assert m[f['bomb_ingredient_set_complete_flag']] == (255 if mask == 255 else 0)
    assert cpu.d[1] & 65535 == mask.bit_count() and cpu.a[7] == STACK


@pytest.mark.parametrize('owned', [0, 1, 127, 128, 129, 255])
@pytest.mark.parametrize('delivered', [0, 126, 127, 128, 255])
def test_depot_entry_transfers_one_of_each_available_type_with_original_signed_byte_clamps(original_image, memory, symbols, owned, delivered):
    m, f = memory, symbols
    types = list(m[f['neutron_bomb_ingredient_model_types']:f['neutron_bomb_ingredient_model_types']+8])
    source, dest = f['model_type_population_counts'], f['taymar_delivered_model_counts_prefix']
    m[source:source+104] = bytes(104); m[dest:dest+104] = bytes(104)
    for t in types: m[source+t], m[dest+t] = owned, delivered
    cpu = state(m, 0x341EC); cpu.a[0], cpu.a[1], cpu.a[2] = source, dest, f['neutron_bomb_ingredient_model_types']; cpu.d[0] = 7
    run(original_image, m, cpu, {0x34358})
    remaining = owned if not owned else max(0, owned-1) if owned <= 128 else 0
    advanced = delivered if not owned else ((delivered+1)&255)
    if owned and advanced >= 128: advanced = 127
    assert bytes(m[source:source+104]) == bytes(remaining if i in types else 0 for i in range(104))
    assert bytes(m[dest:dest+104]) == bytes(advanced if i in types else 0 for i in range(104))
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('countdown', [0, 1, 2, 32768, 32769, 65535])
@pytest.mark.parametrize('inside,body', [(0,3), (1,3), (128,2), (128,3)])
def test_ready_timer_resets_before_location_gate_and_can_mark_ready_without_spawning(original_image, memory, symbols, countdown, inside, body):
    m, f = memory, symbols
    m[f['professor_taymar_delivered_flag']] = 255; m[f['neutron_bomb_ready_flag']] = 0
    m[f['inside_structure_flag']] = inside; put(m, f['selected_celestial_body_index'], body, 2)
    put(m, f['neutron_bomb_spawn_countdown'], countdown, 2); put(m, f['station_sequence_index'], 0, 2)
    put(m, f['free_object_count'], 2, 2); put(m, f['free_object_stack_cursor'], FREE+4); put(m, FREE, OBJECT)
    m[OBJECT:OBJECT+68] = b'\xA5'*68
    cpu = state(m, 0x340AC); run(original_image, m, cpu, {0x34172})
    elapsed = bool(((countdown-1)&65535)&32768)
    spawned = elapsed and bool(inside&128) and body == 3
    assert get(m, f['neutron_bomb_spawn_countdown'], 2) == (get(m, f['station_sequence_bomb_spawn_countdowns'], 2) if elapsed else (countdown-1)&65535)
    assert m[f['neutron_bomb_ready_flag']] == (255 if elapsed else 0)
    assert get(m, f['free_object_count'], 2) == (1 if spawned else 2)
    assert get(m, f['free_object_stack_cursor']) == FREE+(0 if spawned else 4)
    if spawned:
        assert get(m, OBJECT, 2) == 98
        assert [get(m, OBJECT+i) for i in (4,8,12)] == [0xA71E, 0xFFFFFEA2, 0x14D12]
        assert bytes(m[OBJECT+16:OBJECT+22]) == bytes(6)
        assert bytes(m[OBJECT+22:OBJECT+26]) == b'\xA5'*4  # no full-record initialization
    else: assert bytes(m[OBJECT:OBJECT+68]) == b'\xA5'*68
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('distant_count', [0, 1, 65535])
def test_exhausted_free_stack_borrows_first_distant_pointer_without_popping_or_advancing_it(original_image, memory, symbols, distant_count):
    m, f = memory, symbols
    m[f['professor_taymar_delivered_flag']] = 255; m[f['neutron_bomb_ready_flag']] = 0; m[f['inside_structure_flag']] = 255
    put(m, f['selected_celestial_body_index'], 3, 2); put(m, f['station_sequence_index'], 0, 2)
    put(m, f['neutron_bomb_spawn_countdown'], 0, 2); put(m, f['free_object_count'], 1, 2)
    put(m, f['free_object_stack_cursor'], FREE); put(m, f['distant_object_count'], distant_count, 2)
    put(m, f['distant_objects_cursor'], DISTANT); put(m, DISTANT, OBJECT); m[OBJECT:OBJECT+68] = b'\xA5'*68
    cpu = state(m, 0x340AC); run(original_image, m, cpu, {0x34172})
    assert m[f['neutron_bomb_ready_flag']] == (255 if distant_count else 0)
    assert get(m, OBJECT, 2) == (98 if distant_count else 0xA5A5)
    assert get(m, f['distant_object_count'], 2) == distant_count
    assert get(m, f['distant_objects_cursor']) == DISTANT
    assert get(m, f['free_object_count'], 2) == 1 and get(m, f['free_object_stack_cursor']) == FREE
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('complete', [False, True])
@pytest.mark.parametrize('aboard', [0, 255])
@pytest.mark.parametrize('delivered', [0, 127, 128, 255])
@pytest.mark.parametrize('tick', [0, 31])
def test_delivery_flags_and_ingredient_completion_choose_four_dialogue_states_only_on_tick_wrap(original_image, memory, symbols, complete, aboard, delivered, tick):
    m, f = memory, symbols
    types = list(m[f['neutron_bomb_ingredient_model_types']:f['neutron_bomb_ingredient_model_types']+8])
    counts = f['taymar_delivered_model_counts_prefix']; m[counts:counts+104] = bytes(104)
    for t in types if complete else types[:1]: m[counts+t] = 255
    m[f['professor_taymar_aboard_flag']] = aboard; m[f['professor_taymar_delivered_flag']] = delivered
    m[f['neutron_bomb_order_requested_flag']] = 255
    put(m, f['current_structure_service_id'], 1, 2); put(m, f['depot_dialogue_tick'], tick, 2)
    put(m, f['taymar_dialogue_state'], 0x7777, 2)
    handlers = [0x3446A, 0x344E0, 0x3450E, 0x3458C]
    cpu = state(m, 0x34358); run(original_image, m, cpu, set(handlers+[0x34A62]))
    accepted_delivery = bool(aboard&128 or delivered&128)
    selection = 2*accepted_delivery+complete
    assert m[f['professor_taymar_aboard_flag']] == 0
    assert m[f['professor_taymar_delivered_flag']] == (255 if aboard&128 else delivered)
    assert m[f['bomb_ingredient_set_complete_flag']] == (255 if complete else 0)
    assert get(m, f['depot_dialogue_tick'], 2) == (tick+1)&31
    assert get(m, f['taymar_dialogue_state'], 2) == (selection if tick == 31 else 0x7777)
    assert cpu.pc == (handlers[selection] if tick == 31 else 0x34A62) and cpu.a[7] == STACK


@pytest.mark.parametrize('delivered', [0, 1, 127, 128, 255])
def test_zero_ingredients_returns_to_offer_unless_delivery_flag_is_negative(original_image, memory, symbols, delivered):
    m, f = memory, symbols; counts = f['taymar_delivered_model_counts_prefix']
    m[counts:counts+104] = bytes(104); m[f['professor_taymar_delivered_flag']] = delivered
    m[f['bomb_ingredient_set_complete_flag']] = 255
    cpu = state(m, 0x34380); run(original_image, m, cpu, {0x343FC, 0x345F2})
    assert cpu.pc == (0x343FC if delivered&128 else 0x345F2)
    assert m[f['bomb_ingredient_set_complete_flag']] == 0 and cpu.a[7] == STACK


@pytest.mark.parametrize('token', [0, 0x59, 0x4E, 0xA0, 0x12340059, 0xFFFF004E])
def test_offer_command_uses_low_byte_and_only_yes_or_no_reset_intro_state(original_image, memory, symbols, token):
    m, f = memory, symbols
    for n in ['taymar_intro_message_index', 'taymar_intro_message_index_mask',
              'depot_dialogue_pause_countdown', 'depot_dialogue_tick']:
        put(m, f[n], 0x7777, 2)
    m[f['neutron_bomb_order_requested_flag']] = 0x55
    cpu = state(m, 0x3460E); cpu.d[0] = token
    run(original_image, m, cpu, {0x354DA, 0x3466C, f['display_event_message_line']})
    byte = token&255; choice = byte in (0x59,0x4E)
    assert cpu.pc == (0x354DA if byte == 0xA0 else f['display_event_message_line'] if choice else 0x3466C)
    for n,value in [('taymar_intro_message_index',0), ('taymar_intro_message_index_mask',31 if byte == 0x59 else 15),
                    ('depot_dialogue_pause_countdown',2), ('depot_dialogue_tick',0)]:
        assert get(m, f[n], 2) == (value if choice else 0x7777)
    assert m[f['neutron_bomb_order_requested_flag']] == (255 if byte == 0x59 else 0 if byte == 0x4E else 0x55)
    assert cpu.a[7] == STACK-(4 if choice else 0)
    if choice: assert cpu.a[1] == get(m, f['event_message_pointers']+4*(33 if byte == 0x59 else 34))
