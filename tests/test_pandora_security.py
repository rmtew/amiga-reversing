"""Original checkpoint policy and state transitions, with explicit local inputs."""
from __future__ import annotations

import ctypes as C

import pytest

from src.tests.test_m68k_simulator_arithmetic import Trace, engine

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture

APP, PLAYER = 0x39FC, BASE+0x4C322


@pytest.fixture
def security(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    m = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    slots = {r.symbol: r.offset for r in m.rsset_layout_regions if r.symbol}
    cpu.a[6], cpu.a[4] = APP, PLAYER
    return cpu, memory, schemas, read, write, run, slots


def zone(selector):
    for tier, lower, upper in [(0, 0x45, 0x51), (1, 0x9C, 0xA9),
                               (2, 0xB0, 0xB7), (3, 0x133, 0x13A)]:
        if lower <= selector < upper:
            return tier
    return 0xFF


def test_zone_lookup_covers_original_30_by_43_macrocell_map(security):
    cpu, memory, schemas, read, write, run, slots = security
    # The original 90x129 tile map stores 30x43 selectors for 3x3 tile blocks.
    selectors = [read(BASE+0x3502+2*i, 2) for i in range(1290)]
    obj = schemas['world_object_shared_prefix']
    for i, selector in enumerate(selectors):
        row, column = divmod(i, 30)
        write(PLAYER+obj['world_x'], column*48, 2)
        write(PLAYER+obj['world_y'], row*48, 2)
        run(0x875A)
        assert read(APP+slots['app_player_security_zone_tier'], 1) == zone(selector)
        assert cpu.d[1] & 0xFFFF == selector
        assert bool(cpu.sr & 8) == (zone(selector) == 0xFF)
    # This covers original cells, not arbitrary coordinates or a bounds clamp.


def test_selected_clearance_is_strict_and_admits_six_variants_only(security):
    cpu, memory, schemas, read, write, run, slots = security
    obj = schemas['world_object_shared_prefix']
    tiers = [4, 3, 1, 3, 0, 2]
    for required in [0, 1, 2, 3, 0xFF]:
        write(APP+slots['app_player_security_zone_tier'], required, 1)
        for item in range(256):
            write(PLAYER+obj['selected_item_id'], item, 1)
            cpu.sr = 0x201F
            run(0x87E2)
            admitted = 48 <= item < 54 and tiers[item-48] > required
            assert bool(cpu.sr & 1) is (not admitted), (item, required)


def test_id_possession_searches_selected_and_eight_inventory_slots(security):
    cpu, memory, schemas, read, write, run, slots = security
    obj = schemas['world_object_shared_prefix']
    locations = [PLAYER+obj['selected_item_id']]
    locations += [APP+slots['app_carried_item_ids']+i for i in range(4)]
    locations += [APP+slots['app_pocket_item_ids']+i for i in range(4)]
    for location in locations:
        for item in range(48, 56):
            for address in locations:
                write(address, 0, 1)
            write(location, item, 1)
            write(APP+0x2A6, 0xFF, 1)
            before_d, before_a = list(cpu.d), list(cpu.a[:7])
            run(0x86CA)
            assert read(APP+0x2A6, 1) == 0xEF
            assert list(cpu.d) == before_d and list(cpu.a[:7]) == before_a
            assert read(location, 1) == item
    for item in [0, 1, 47, 56, 255]:
        for address in locations:
            write(address, item, 1)
        run(0x86CA, stop=0x8700)
        assert cpu.a[4] == PLAYER  # Failure is the player, not the nearby officer.


def test_flash_continues_without_checkpoint_and_ignores_combat_gate(security):
    cpu, memory, schemas, read, write, run, slots = security
    write(PLAYER+schemas['world_object_shared_prefix']['world_object_flags'], 0, 1)
    write(APP+slots['app_nearest_object_ptr'], 0)
    write(APP+slots['app_ui_flags'], 2, 1)
    write(APP+slots['app_security_damage_flash_ticks_remaining'], 31, 1)
    write(APP+slots['app_security_damage_service_countdown'], 17, 2)
    write(APP+slots['app_security_saved_palette_color'], 0xABC, 2)
    write(PLAYER+schemas['world_object_shared_prefix']['hit_points'], 50, 2)
    for remaining in range(30, 0, -1):
        run(0x8814)
        assert read(APP+slots['app_security_damage_flash_ticks_remaining'], 1) == remaining
        assert read(APP+slots['app_security_damage_service_countdown'], 2) == 17
        assert read(BASE+0x772, 2) == read(BASE+0x8920+2*(31-remaining), 2)
    # Normal reload31 visits palette entries1..30, then restores saved color;
    # endpoints0 and31 are physical records, not normal flash outputs.
    run(0x8814)
    assert read(BASE+0x772, 2) == 0xABC
    assert read(APP+slots['app_security_damage_flash_ticks_remaining'], 1) == 0


def test_inactive_player_freezes_flash_and_damage_service(security):
    cpu, memory, schemas, read, write, run, slots = security
    write(PLAYER+schemas['world_object_shared_prefix']['world_object_flags'], 2, 1)
    write(APP+slots['app_security_damage_flash_ticks_remaining'], 9, 1)
    write(APP+slots['app_security_damage_service_countdown'], 12, 2)
    run(0x8814)
    assert read(APP+slots['app_security_damage_flash_ticks_remaining'], 1) == 9
    assert read(APP+slots['app_security_damage_service_countdown'], 2) == 12


def test_damage_updates_low_health_byte_with_signed_result_clamp(security):
    cpu, memory, schemas, read, write, run, slots = security
    hp = PLAYER+schemas['world_object_shared_prefix']['hit_points']
    for health in [0, 1, 50, 51, 52, 100, 127, 128, 178, 179, 255]:
        write(hp, 0x1200+health, 2)
        write(APP+slots['app_security_damage_service_countdown'], 1, 2)
        run(0x8864, stop=0x8880)
        difference = (health-51) & 255
        expected = 0 if difference & 128 else difference
        assert read(hp, 2) == 0x1200+expected
        assert read(APP+slots['app_security_damage_service_countdown'], 2) == 0
    # Service count zero wraps to65535 and skips damage; it is not expiry.
    write(APP+slots['app_security_damage_service_countdown'], 0, 2)
    run(0x8864, stop=0x8896)
    assert read(APP+slots['app_security_damage_service_countdown'], 2) == 0xFFFF


def test_valid_selected_card_pauses_response_without_clearing_it(security):
    cpu, memory, schemas, read, write, run, slots = security
    obj, state = schemas['world_object_shared_prefix'], schemas['world_position_state_record']
    # Explicit nearby checkpoint chain; no inference of runtime pointer immutability.
    checkpoint, descriptor, render_state = 0x80000, 0x80100, 0x80200
    write(checkpoint+obj['position_descriptor_ptr'], descriptor)
    write(descriptor, render_state)
    write(render_state+state['world_object_flags'], 0x80, 1)
    write(APP+slots['app_nearest_object_ptr'], checkpoint)
    write(PLAYER+obj['world_object_flags'], 0, 1)
    write(PLAYER+obj['selected_item_id'], 48, 1)
    write(APP+slots['app_security_damage_flash_ticks_remaining'], 0, 1)
    write(APP+slots['app_security_checkpoint_response_active'], 1, 1)
    write(APP+slots['app_security_damage_service_countdown'], 17, 2)
    write(APP+slots['app_ui_flags'], 0, 1)
    selectors = [read(BASE+0x3502+2*i, 2) for i in range(1290)]
    i = next(i for i, v in enumerate(selectors) if zone(v) == 0)
    row, column = divmod(i, 30)
    write(PLAYER+obj['world_x'], column*48, 2)
    write(PLAYER+obj['world_y'], row*48, 2)
    run(0x8814)
    assert read(APP+slots['app_security_damage_service_countdown'], 2) == 17
    assert read(APP+slots['app_security_checkpoint_response_active'], 1) == 1


def test_response_reselects_first_live_inventory_item_not_initial_inventory(security):
    cpu, memory, schemas, read, write, run, slots = security
    obj = schemas['world_object_shared_prefix']
    actor, live, initial = 0x80000, 0x80100, 0x80200
    write(actor+obj['inventory_slots_ptr'], live)
    write(actor+obj['initial_inventory_slots_ptr'], initial)
    write(live, 18, 1)
    write(initial, 19, 1)
    cpu.a[5] = actor
    run(0x8972, stop=0x897E)
    assert read(actor+obj['selected_item_id'], 1) == 18
    assert read(APP+slots['app_security_checkpoint_response_active'], 1) == 1
    assert read(live, 1) == 18 and read(initial, 1) == 19


def test_id_failure_installs_shared_thirteen_frame_defeat_state(security):
    cpu, memory, schemas, read, write, run, slots = security
    obj, state, node = [schemas[n] for n in [
        'world_object_shared_prefix', 'world_position_state_record', 'WorldPositionStateNode']]
    descriptor = read(PLAYER+obj['position_descriptor_ptr'])
    previous = read(descriptor)
    cpu.a[4] = PLAYER
    run(0x8700, stop=0x8738)
    incoming, animation, sequence = BASE+0x4C6BA, BASE+0x4C6D4, BASE+0x4C6E6
    assert read(descriptor) == incoming
    assert read(PLAYER+obj['saved_position_state_ptr']) == previous
    assert read(PLAYER+obj['world_object_flags'], 1) & 2
    assert read(PLAYER+obj['hit_points'], 2) == 0
    assert read(incoming+state['current_geometry_ptr']) == BASE+0x4C5D0
    assert read(incoming+state['state_node_ptr']) == animation
    assert read(animation+node['frame_count'], 1) == 13
    assert read(animation+node['phase_step'], 1) == 40
    assert read(animation+node['frame_sequence_ptr']) == sequence
    assert [read(sequence+4*i) for i in range(14)] == [
        BASE+0x4C6A8, *[BASE+0x4C5D0+18*i for i in range(13)]
    ]
    assert read(animation+node['frame_index_and_phase'], 2) == 0
    cpu.a[4] = incoming
    selected = {read(incoming+state['current_geometry_ptr'])}
    for _ in range(84):
        run(0x951A)
        selected.add(read(incoming+state['current_geometry_ptr']))
    assert selected == {BASE+0x4C5D0+18*i for i in range(13)}
    assert read(animation+node['mode_flags'], 1) & 1
    assert read(incoming+state['current_geometry_ptr']) == BASE+0x4C6A8
    # Direct consumer checks header/array semantics, not render reachability.


def test_static_defeat_state_null_node_retains_original_low_memory_writes(security):
    cpu, memory, schemas, read, write, run, slots = security
    obj, state = schemas['world_object_shared_prefix'], schemas['world_position_state_record']
    descriptor = read(PLAYER+obj['position_descriptor_ptr'])
    previous = read(descriptor)
    run(0x88BC, stop=0x88D2)  # Stop before outcome/message calls.
    assert read(PLAYER+obj['hit_points'], 2) == 0
    assert read(PLAYER+obj['world_object_flags'], 1) & 2
    # Explicit continuation context after the external message call; that call's
    # register effects and UI reachability are not claimed by this fixture.
    cpu.a[4] = PLAYER
    run(0x88D8, stop=0x88F8)
    incoming = BASE+0x4C5B6
    assert read(PLAYER+obj['saved_position_state_ptr']) == incoming
    assert read(incoming+state['current_geometry_ptr']) == BASE+0x4C592
    assert read(incoming+state['previous_geometry_ptr']) == BASE+0x4C592
    assert read(incoming+state['state_node_ptr']) == 0
    write(0xA, 0xA5, 1)
    write(0x10, 0xBEEF, 2)
    run(0x88FC, stop=0x8902)
    assert read(descriptor) == incoming
    assert read(PLAYER+obj['saved_position_state_ptr']) == previous
    assert read(0xA, 1) == 0xA4 and read(0x10, 2) == 0
    # No null-node guard exists in the original exchange helper. Preserve this
    # behavior rather than claiming the static pose has a valid animation node.


def test_escape_prefix_binds_second_final_pose_record_and_unbinds_animation(security):
    cpu, memory, schemas, read, write, run, slots = security
    state = schemas['world_position_state_record']
    player_state = BASE+0x4C72A
    write(player_state+state['state_node_ptr'], BASE+0x4C6D4)
    run(0x9792, stop=0x97A2)
    assert read(player_state+state['current_geometry_ptr']) == BASE+0x4C5A4
    assert read(player_state+state['state_node_ptr']) == 0
    # This is the original guarded path's MOVE/CLR continuation, not proof of
    # ordinary escape reachability or a second defeat geometry's exclusive use.


def configure_checkpoint_service(security):
    """Explicit stable-nearby fixture, not a claim about actor motion in game."""
    cpu, memory, schemas, read, write, run, slots = security
    obj = schemas['world_object_shared_prefix']
    state = schemas['world_position_state_record']
    actor, descriptor, render_state = 0x80000, 0x80100, 0x80200
    write(actor+obj['position_descriptor_ptr'], descriptor)
    write(descriptor, render_state)
    write(render_state+state['world_object_flags'], 0x80, 1)
    write(APP+slots['app_nearest_object_ptr'], actor)
    write(PLAYER+obj['world_object_flags'], 0, 1)
    write(PLAYER+obj['selected_item_id'], 18, 1)
    write(PLAYER+obj['hit_points'], 44, 2)
    write(APP+slots['app_ui_flags'], 0, 1)
    write(APP+slots['app_security_checkpoint_response_active'], 1, 1)
    write(APP+slots['app_security_damage_service_countdown'], 50, 2)
    write(APP+slots['app_security_damage_flash_ticks_remaining'], 0, 1)
    write(APP+slots['app_security_saved_palette_color'], 0xABC, 2)
    selectors = [read(BASE+0x3502+2*i, 2) for i in range(1290)]
    i = next(i for i, selector in enumerate(selectors) if zone(selector) == 0)
    row, column = divmod(i, 30)
    write(PLAYER+obj['world_x'], column*48, 2)
    write(PLAYER+obj['world_y'], row*48, 2)
    return actor, render_state, selectors


def test_second_damage_requires_flash_then_fifty_eligible_service_calls(security):
    cpu, memory, schemas, read, write, run, slots = security
    configure_checkpoint_service(security)
    write(APP+slots['app_security_damage_flash_ticks_remaining'], 31, 1)
    # The flash skips countdown work, including its final color-restore call.
    for remaining in range(30, -1, -1):
        run(0x8814)
        assert read(APP+slots['app_security_damage_flash_ticks_remaining'], 1) == remaining
        assert read(APP+slots['app_security_damage_service_countdown'], 2) == 50
    assert read(BASE+0x772, 2) == 0xABC
    for remaining in range(49, 0, -1):
        run(0x8814)
        assert read(APP+slots['app_security_damage_service_countdown'], 2) == remaining
        assert read(PLAYER+schemas['world_object_shared_prefix']['hit_points'], 2) == 44
    run(0x8814, stop=0x887C)
    assert read(APP+slots['app_security_damage_service_countdown'], 2) == 0
    assert cpu.d[0] & 255 == 0  # 44-51 clamps before the original store.
    assert read(PLAYER+schemas['world_object_shared_prefix']['hit_points'], 2) == 44
    # Stop before the health store and UI/audio calls. No gameplay reachability
    # or elapsed-time conversion follows from this fixed-nearby fixture.


@pytest.mark.parametrize('gate', ['inactive', 'combat', 'valid_card', 'unrestricted'])
def test_damage_pause_preserves_countdown_and_resumes_without_restart(security, gate):
    cpu, memory, schemas, read, write, run, slots = security
    _, _, selectors = configure_checkpoint_service(security)
    obj = schemas['world_object_shared_prefix']
    original_xy = read(PLAYER+obj['world_x'])
    if gate == 'inactive':
        write(PLAYER+obj['world_object_flags'], 2, 1)
    elif gate == 'combat':
        write(APP+slots['app_ui_flags'], 2, 1)
    elif gate == 'valid_card':
        write(PLAYER+obj['selected_item_id'], 48, 1)
    else:
        i = next(i for i, selector in enumerate(selectors) if zone(selector) == 0xFF)
        row, column = divmod(i, 30)
        write(PLAYER+obj['world_x'], column*48, 2)
        write(PLAYER+obj['world_y'], row*48, 2)
    for _ in range(3):
        run(0x8814)
        assert read(APP+slots['app_security_damage_service_countdown'], 2) == 50
        assert read(APP+slots['app_security_checkpoint_response_active'], 1) == 1
    write(PLAYER+obj['world_object_flags'], 0, 1)
    write(APP+slots['app_ui_flags'], 0, 1)
    write(PLAYER+obj['selected_item_id'], 18, 1)
    write(PLAYER+obj['world_x'], original_xy)
    run(0x8814)
    assert read(APP+slots['app_security_damage_service_countdown'], 2) == 49
    assert read(APP+slots['app_security_checkpoint_response_active'], 1) == 1


@pytest.mark.parametrize('missing', [True, False])
def test_lost_checkpoint_branches_to_response_clear_before_countdown(security, missing):
    cpu, memory, schemas, read, write, run, slots = security
    _, render_state, _ = configure_checkpoint_service(security)
    if missing:
        write(APP+slots['app_nearest_object_ptr'], 0)
    else:
        write(render_state+schemas['world_position_state_record']['world_object_flags'], 0, 1)
    run(0x8814, stop=0x8848)
    assert read(APP+slots['app_security_damage_service_countdown'], 2) == 50
    # Branch destination established; the clear helper's audio work is outside
    # this bounded CPU check and is not replaced or stubbed.


def test_static_defeat_executes_original_callees_without_reseeding_registers(security):
    cpu, memory, schemas, read, write, run, slots = security
    obj = schemas['world_object_shared_prefix']
    descriptor = read(PLAYER+obj['position_descriptor_ptr'])
    previous = read(descriptor)
    # Explicit already-busy status queue: messages are appended by the actual
    # original callees. No rendering callback or machine instruction is stubbed.
    queue = APP+slots['app_scrolling_message_queue_head']
    write(APP+slots['app_scrolling_message_queue_tail'], queue)
    write(APP+0x2A6, 1 << 5, 1)
    write(APP+slots['app_ui_flags'], 0, 1)
    write(APP+slots['app_font_glyph_bitmap_table_ptr'], BASE+0xA7E2)
    write(0xA, 0xA5, 1)
    write(0x10, 0xBEEF, 2)
    # Preserve CPU and stack continuously while retaining only 64 instructions'
    # write ranges at a time. A full text draw exceeds the trace range capacity.
    buffer = (C.c_uint8 * len(memory)).from_buffer(memory)
    cpu.a[7] = 0x9000
    write(0x9000, 0x800)
    cpu.pc = BASE+0x88BC
    steps = 0
    for _ in range(64):
        trace = Trace()
        rc = engine()(0, buffer, len(memory), C.byref(cpu), 64,
                      BASE+0x8902, BASE+0x8904, None, C.byref(trace))
        assert rc == 0 and trace.stop_reason in (1, 3)
        assert 0 < trace.steps <= 64 and not trace.overflow
        assert not any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count])
        steps += trace.steps
        if trace.stop_reason == 1:
            break
    else:
        pytest.fail('Original defeat continuation exceeded 4096 instructions')
    assert cpu.pc == BASE+0x8902 and cpu.a[7] == 0x9000
    assert steps < 4096
    assert read(PLAYER+obj['hit_points'], 2) == 0
    assert read(PLAYER+obj['world_object_flags'], 1) & 2
    assert cpu.a[5] == PLAYER
    assert read(descriptor) == BASE+0x4C5B6
    assert read(PLAYER+obj['saved_position_state_ptr']) == previous
    assert read(APP+slots['app_scrolling_message_queue_tail']) == queue+12
    assert all(read(queue+4*i) for i in range(3))
    assert read(queue+12) == 0
    assert read(0xA, 1) == 0xA4 and read(0x10, 2) == 0
    # This confirms original caller/callee continuity from the death branch in
    # an explicit local state, not that ordinary joystick play reaches it.
