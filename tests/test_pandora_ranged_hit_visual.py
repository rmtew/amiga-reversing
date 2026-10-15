"""Original effect activation, animation and per-point scan; no full-ray closure."""
from __future__ import annotations

import pytest

from tests.test_pandora_state_transitions import cpu_fixture

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, STATE, NODE, DESCRIPTOR, TIMER = 0x39FC, 0x585B2, 0x58688, 0x5859A, 0x320


@pytest.mark.parametrize('mode', [0, 4, 5, 0xA5])
def test_activation_resets_node_returns_loaded_descriptor_and_preserves_point(cpu_fixture, mode):
    cpu, memory, schemas, read, write, run = cpu_fixture
    state, node = schemas['world_position_render_state_prefix'], schemas['WorldPositionStateNode']
    cpu.a[6] = APP
    for i in range(8):
        cpu.d[i] = 0x12340000+i
        if i < 6:
            cpu.a[i] = 0x56780000+i
    old_d, old_a = list(cpu.d), list(cpu.a)
    write(NODE+node['mode_flags'], mode, 1)
    write(NODE+node['frame_index_and_phase'], 0xABCD, 2)
    old_state, old_node = bytes(memory[STATE:STATE+26]), bytes(memory[NODE:NODE+18])
    run(0x9486)
    assert list(cpu.d) == old_d and list(cpu.a)[2:7] == old_a[2:7]
    assert cpu.a[0] == STATE and cpu.a[1] == read(STATE+state['position_descriptor_ptr']) == DESCRIPTOR
    assert cpu.a[7] == 0x9004
    expected = bytearray(old_state)
    expected[state['state_node_ptr']:state['state_node_ptr']+4] = NODE.to_bytes(4, 'big')
    assert bytes(memory[STATE:STATE+26]) == expected
    expected = bytearray(old_node)
    expected[node['mode_flags']] &= ~1
    expected[node['frame_index_and_phase']:node['frame_index_and_phase']+2] = bytes(2)
    assert bytes(memory[NODE:NODE+18]) == expected
    assert read(APP+TIMER, 2) == 25


def test_initialized_phase_advances_before_selection_and_then_holds(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    state, node = schemas['world_position_render_state_prefix'], schemas['WorldPositionStateNode']
    cpu.a[6] = APP
    assert read(NODE+node['frame_count'], 1) == 7
    assert read(NODE+node['phase_step'], 1) == 0x80
    assert read(NODE+node['mode_flags'], 1) == 4
    run(0x9486)
    sequence = read(NODE+node['frame_sequence_ptr'])
    frames = [read(sequence+4*i) for i in range(8)]
    cpu.a[4] = STATE
    # Reset index=0 is incremented before lookup. No claim that slot 1 is shown.
    for expected in frames[2:]+[frames[0], frames[0]]:
        run(0x951A)
        assert read(STATE+state['current_geometry_ptr']) == expected
    assert read(NODE+node['frame_index_and_phase'], 2) == 0x0600
    assert read(NODE+node['mode_flags'], 1) == 5
    assert read(APP+TIMER, 2) == 25  # Animation service does not consume this timer.


@pytest.mark.parametrize('remaining', [0, 1, 2])
def test_visual_timer_only_unbinds_node_on_transition_to_zero(cpu_fixture, remaining):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    obj, state = schemas['world_object_shared_prefix'], schemas['world_position_render_state_prefix']
    write(0x5C322+obj['world_object_flags'], 0, 1)
    write(STATE+state['state_node_ptr'], NODE)
    write(STATE+state['current_geometry_ptr'], 0x58676)
    write(APP+TIMER, remaining, 2)
    run(0x9250, stop=0x926E, budget=32)
    assert read(APP+TIMER, 2) == max(0, remaining-1)
    assert read(STATE+state['state_node_ptr']) == (0 if remaining == 1 else NODE)
    assert read(STATE+state['current_geometry_ptr']) == 0x58676


def point_scene(fixture, x, y, flags=0, child=False):
    cpu, memory, schemas, read, write, run = fixture
    cpu.a[6], cpu.d[0], cpu.d[1] = APP, x, y
    table, descriptor, primary, attached, geometry = 0x80000, 0x81000, 0x82000, 0x82100, 0x83000
    state, desc, bounds = schemas['world_position_state_record'], schemas['world_position_descriptor_prefix'], schemas['world_position_collision_bounds']
    write(APP+0x2A8, table)
    write(APP+0x2AC, 0, 2)  # This scan uses NULL, not active_world_object_count.
    player_desc = read(0x5C322+schemas['world_object_shared_prefix']['position_descriptor_ptr'])
    for i, pointer in enumerate([DESCRIPTOR, player_desc, descriptor, 0]):
        write(table+4*i, pointer)
    write(descriptor+desc['position_state_ptr'], primary)
    write(descriptor+desc['world_x'], 100, 2)
    write(descriptor+desc['world_y'], 200, 2)
    for address in [primary, attached]:
        write(address+state['current_geometry_ptr'], geometry)
        write(address+state['world_x_offset'], 3, 2)
        write(address+state['world_y_offset'], 0xFFFE, 2)
    write(primary+state['world_object_flags'], flags, 1)
    write(primary+state['attachment_state_ptr'], attached if child else 0)
    write(geometry+bounds['world_x_origin_offset'], 7, 2)
    write(geometry+bounds['world_y_origin_offset'], 5, 2)
    write(geometry+bounds['world_x_extent'], 20, 2)
    write(geometry+bounds['world_y_extent'], 10, 2)
    return descriptor, primary, attached


@pytest.mark.parametrize('x,y,hit', [(110, 203, True), (129, 212, True), (109, 203, False),
                                   (130, 203, False), (110, 202, False), (110, 213, False)])
def test_per_point_scan_uses_half_open_composed_bounds(cpu_fixture, x, y, hit):
    cpu, memory, schemas, read, write, run = cpu_fixture
    descriptor, primary, _ = point_scene(cpu_fixture, x, y)
    run(0x931C, stop=0x9380 if hit else 0x92DE, budget=256)
    if hit:
        assert cpu.a[1] == descriptor and cpu.a[2] == primary


@pytest.mark.parametrize('flags,hit_child', [(8, True), (64, False)])
def test_state_skip_and_whole_descriptor_skip_have_different_scope(cpu_fixture, flags, hit_child):
    cpu, memory, schemas, read, write, run = cpu_fixture
    descriptor, _, attached = point_scene(cpu_fixture, 110, 203, flags=flags, child=True)
    run(0x931C, stop=0x9380 if hit_child else 0x92DE, budget=256)
    if hit_child:
        assert cpu.a[1] == descriptor and cpu.a[2] == attached


@pytest.mark.parametrize('reverse', [False, True])
def test_first_matching_descriptor_wins_in_table_order(cpu_fixture, reverse):
    cpu, memory, schemas, read, write, run = cpu_fixture
    descriptor, primary, _ = point_scene(cpu_fixture, 110, 203)
    second = descriptor+0x100
    memory[second:second+12] = memory[descriptor:descriptor+12]
    order = [second, descriptor] if reverse else [descriptor, second]
    for i, pointer in enumerate(order+[0]):
        write(0x80000+4*i, pointer)
    run(0x931C, stop=0x9380, budget=256)
    assert cpu.a[1] == order[0] and cpu.a[2] == primary


@pytest.mark.parametrize('call,registers', [(0x93A0, (0, 1)), (0x9410, (5, 6)), (0x942A, (0, 1))])
def test_three_callers_store_point_into_returned_visual_descriptor(cpu_fixture, call, registers):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6], cpu.a[1] = APP, 0x80000
    write(0x80004, 0xBEEFBEEF)
    cpu.d[registers[0]], cpu.d[registers[1]] = 0x123, 0x456
    run(call, stop=call+12, budget=64)
    assert cpu.a[1] == DESCRIPTOR
    assert read(DESCRIPTOR+4, 2) == 0x123 and read(DESCRIPTOR+6, 2) == 0x456
    assert read(0x80004) == 0xBEEFBEEF


def test_inactive_player_skips_visual_timer_service(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    write(0x5C322+schemas['world_object_shared_prefix']['world_object_flags'], 2, 1)
    write(APP+TIMER, 1, 2)
    write(STATE+schemas['world_position_render_state_prefix']['state_node_ptr'], NODE)
    run(0x9250, budget=16)
    assert read(APP+TIMER, 2) == 1
    assert read(STATE+schemas['world_position_render_state_prefix']['state_node_ptr']) == NODE


@pytest.mark.parametrize('entry,stop', [(0x9394, 0x93AC), (0x941E, 0x9436)])
def test_interaction_flag_bypasses_activation_and_keeps_hit_descriptor(cpu_fixture, entry, stop):
    cpu, memory, schemas, read, write, run = cpu_fixture
    descriptor, state = 0x80000, 0x81000
    cpu.a[6], cpu.a[1] = APP, descriptor
    cpu.d[0], cpu.d[1] = 0x123, 0x456
    write(descriptor, state)
    write(state+schemas['world_position_state_record']['interaction_flags'], 1, 1)
    visual_before = bytes(memory[DESCRIPTOR:DESCRIPTOR+12])
    write(APP+TIMER, 9, 2)
    run(entry, stop=stop, budget=32)
    assert cpu.a[1] == descriptor
    assert read(descriptor+4, 2) == 0x123 and read(descriptor+6, 2) == 0x456
    assert bytes(memory[DESCRIPTOR:DESCRIPTOR+12]) == visual_before
    assert read(APP+TIMER, 2) == 9


def test_activation_returns_mutated_descriptor_field_without_assuming_original_address(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    write(STATE+schemas['world_position_render_state_prefix']['position_descriptor_ptr'], 0x80000)
    run(0x9486)
    assert cpu.a[1] == 0x80000
