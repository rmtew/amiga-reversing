"""Bounded original world-service phases with explicit RAM and records.

No complete mission, valid save-state domain, object lifetime, physical cadence,
palette delivery or hardware scanout proof. Index aliases are retained, not
used to enlarge the declared tables.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, STACK
from tests.test_starglider2_message_lines import QUEUE, COUNT, TIMER, BLANK

APP_NAMES = ['professor_taymar_aboard_flag', 'current_structure_service_id',
    'model_type_population_counts', 'space_environment_flag', 'inside_structure_flag',
    'player_world_y', 'released_object_tracking_references', 'last_player_contact_type',
    'stardrive_enabled_word', 'space_station_spawn_request', 'world_object_pool',
    'free_object_count', 'free_object_stack_cursor', 'distant_object_count',
    'distant_objects_cursor', 'station_construction_steps_remaining',
    'space_station_nearby_flag', 'station_proximity_colour_ramp_step',
    'station_proximity_disc_colour_index', 'player_speed_target', 'selected_celestial_body_index',
    'shared_random_state_a', 'shared_random_state_b']
GLOBALS = ['taymar_aboard_notice_phase', 'surface_brake_hold_countdown',
    'pirate_warning_cooldown_or_negative', 'icarus_speed_colour_max_step',
    'icarus_speed_colour_step', 'icarus_speed_colour_step_direction',
    'icarus_speed_face_colour_indices', 'model_header_pointers', 'model_default_scale_shifts',
    'station_proximity_disc_colour_ramp', 'event_message_pointers',
    *['icarus_speed_animated_face_'+str(i) for i in range(4)],
    'world_low_altitude_mesh_material_indices', 'world_middle_altitude_mesh_material_indices',
    'world_high_altitude_mesh_material_indices', 'special_mesh_material_index']
OBJECT, FREE, DISTANT = 0x85000, 0x84000, 0x84100


@pytest.fixture(scope='module')
def symbols(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('world-service'); asm, out = folder/'map.s', folder/'map.raw'
    names = APP_NAMES+GLOBALS
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin',
        '-m68000', '-no-opt', '-I'+str(target/'includes'), '-o', str(out), str(asm)],
        cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    data = out.read_bytes(); tail = 4*len(names); assert data[:-tail] == original_image[0]
    return {n:v+(APP if n in APP_NAMES else 0) for n,v in
            zip(names, struct.unpack('>'+'I'*len(names), data[-tail:]))}


def word(m, address, value): put(m, address, value&65535, 2)
def negative(value, bits=16): return bool(value & (1<<(bits-1)))
def signed(value, bits=16): return (value&((1<<bits)-1))-(1<<bits) if negative(value,bits) else value&((1<<bits)-1)


@pytest.mark.parametrize('aboard,service', [(0,0), (1,0), (127,0), (128,0), (255,0), (255,1), (255,65535)])
@pytest.mark.parametrize('phase', [0, 510, 511, 32767, 65535])
@pytest.mark.parametrize('food', [0, 1, 127, 128, 129, 255])
def test_taymar_qualifying_notice_wrap_consumes_castrobars_or_requests_original_remarks(original_image, memory, symbols, aboard, service, phase, food):
    m,f = memory,symbols; cargo = f['model_type_population_counts']+100
    m[f['professor_taymar_aboard_flag']] = aboard; word(m,f['current_structure_service_id'],service)
    word(m,f['taymar_aboard_notice_phase'],phase); m[cargo] = food
    word(m,COUNT,1); word(m,TIMER,33); put(m,QUEUE-4,0x123456); put(m,QUEUE,0x765432)
    cpu = state(m,0x32E70); run(original_image,m,cpu,{0x32F12})
    gated = negative(aboard,8) and service == 0
    next_phase = (phase+1)&511 if gated else phase
    active = gated and next_phase == 0
    expected_food = food if not active or not food else food-1 if food <= 128 else 0
    assert get(m,f['taymar_aboard_notice_phase'],2) == next_phase and m[cargo] == expected_food
    if not active:
        assert get(m,COUNT,2) == 1 and get(m,TIMER,2) == 33 and get(m,QUEUE) == 0x765432
    elif food:
        assert get(m,COUNT,2) == 3 and get(m,TIMER,2) == 0
        assert [get(m,QUEUE+4*i) for i in range(3)] == [get(m,f['event_message_pointers']+4*77),BLANK,get(m,f['event_message_pointers']+4*86)]
    else:
        assert get(m,COUNT,2) == 4 and get(m,TIMER,2) == 33
        assert get(m,QUEUE+4) == get(m,f['event_message_pointers']+4*77)
        assert get(m,QUEUE+8) in [get(m,f['event_message_pointers']+4*i) for i in range(78,82)]
        assert get(m,QUEUE+12) == get(m,f['event_message_pointers']+4*35)
    assert cpu.a[7] == STACK-60  # internal phase still owns its original 15-LONG frame


@pytest.mark.parametrize('space,inside', [(0,0), (1,0), (128,0), (0,1), (0,128)])
@pytest.mark.parametrize('timer', [0, 1, 20, 32768, 32769, 65535])
@pytest.mark.parametrize('player_y', [-120, -121])
def test_surface_release_holdoff_gates_and_original_low_word_overflow(original_image,memory,symbols,space,inside,timer,player_y):
    m,f = memory,symbols; refs = f['released_object_tracking_references']
    m[f['space_environment_flag']],m[f['inside_structure_flag']] = space,inside
    put(m,f['player_world_y'],player_y&0xFFFFFFFF); word(m,f['surface_brake_hold_countdown'],timer)
    for i in range(10): put(m,refs+4*i,0)
    put(m,refs,OBJECT); put(m,OBJECT+8,(-1000)&0xFFFFFFFF); word(m,OBJECT+18,4090)
    cpu = state(m,0x32F12); run(original_image,m,cpu,{0x32F86})
    gated = space == inside == 0
    stepped = ((20 if player_y == -120 else timer)-1)&65535
    active = gated and negative(stepped)
    assert get(m,f['surface_brake_hold_countdown'],2) == (0 if active else stepped if gated else timer)
    assert get(m,OBJECT+8) == ((-970 if active else -1000)&0xFFFFFFFF)
    assert get(m,OBJECT+18,2) == ((4090+16)&4095 if active else 4090)
    assert get(m,refs) == OBJECT and cpu.a[7] == STACK


@pytest.mark.parametrize('y', [-1000, -151, -150, -120, 0, 0x7FFFFFFF, -2147483648])
def test_ten_slot_release_walk_changes_only_rotation_y_and_completed_tracking_entries(original_image,memory,symbols,y):
    m,f = memory,symbols; refs = f['released_object_tracking_references']
    m[f['space_environment_flag']] = m[f['inside_structure_flag']] = 0
    put(m,f['player_world_y'],(-121)&0xFFFFFFFF); word(m,f['surface_brake_hold_countdown'],0)
    for i in range(10):
        put(m,refs+4*i,0 if i%2 else OBJECT+68*i)
        m[OBJECT+68*i:OBJECT+68*(i+1)] = b'\x15'*68
        put(m,OBJECT+68*i+8,y&0xFFFFFFFF); word(m,OBJECT+68*i+18,4095)
    before = bytes(m[OBJECT:OBJECT+680]); expected = bytearray(before)
    advanced = (y+30)&0xFFFFFFFF; complete = not negative((advanced+120)&0xFFFFFFFF,32)
    for i in range(0,10,2):
        expected[68*i+8:68*i+12] = ((-120)&0xFFFFFFFF if complete else advanced).to_bytes(4,'big')
        expected[68*i+18:68*i+20] = (15).to_bytes(2,'big')
    cpu = state(m,0x32F12); run(original_image,m,cpu,{0x32F86})
    assert bytes(m[OBJECT:OBJECT+680]) == expected
    assert [get(m,refs+4*i) for i in range(10)] == [0 if i%2 or complete else OBJECT+68*i for i in range(10)]
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('free,distant', [(0,0), (0,1), (1,0), (1,65535), (2,0), (65535,0)])
@pytest.mark.parametrize('steps', [-1, 0, 1, 52, 53, 32767, -32768])
def test_station_request_scans_full_pool_and_preserves_fallback_allocation_and_header_mutation(original_image,memory,symbols,free,distant,steps):
    m,f = memory,symbols; pool = f['world_object_pool']; m[pool:pool+250*68] = bytes(250*68)
    m[f['space_station_spawn_request']] = 255; word(m,f['free_object_count'],free)
    put(m,f['free_object_stack_cursor'],FREE+4); put(m,FREE,OBJECT)
    word(m,f['distant_object_count'],distant); put(m,f['distant_objects_cursor'],DISTANT); put(m,DISTANT,OBJECT)
    word(m,f['station_construction_steps_remaining'],steps); m[OBJECT:OBJECT+68] = b'\x15'*68
    header = get(m,f['model_header_pointers']+4*99); header_before = bytes(m[header:header+24])
    cpu = state(m,0x330C6); run(original_image,m,cpu,{0x3318E})
    admitted = free > 1 or distant != 0
    assert m[f['space_station_spawn_request']] == (0 if admitted else 255)
    assert get(m,f['free_object_count'],2) == (free-1 if free>1 else free)
    assert get(m,f['free_object_stack_cursor']) == (FREE if free>1 else FREE+4)
    assert get(m,f['distant_objects_cursor']) == DISTANT and get(m,f['distant_object_count'],2) == distant
    if admitted:
        expected = bytearray(b'\x15'*68); expected[:2] = (99).to_bytes(2,'big'); expected[3] = 0
        expected[4:16] = struct.pack('>III',0x2255100,0xFECED300,0x1374780)
        expected[16:22] = struct.pack('>HHH',3840,0,0)
        expected[28] |= 128; expected[29] = m[f['model_default_scale_shifts']+99]; expected[30] = 255
        expected[36:38] = (200).to_bytes(2,'big')
        assert bytes(m[OBJECT:OBJECT+68]) == expected
        expected_header = bytearray(header_before); expected_header[2:4] = ((52-max(0,steps))&65535).to_bytes(2,'big')
        assert bytes(m[header:header+24]) == expected_header
    else:
        assert bytes(m[OBJECT:OBJECT+68]) == b'\x15'*68 and bytes(m[header:header+24]) == header_before
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('index', [0, 1, 249])
@pytest.mark.parametrize('phase', [0, 255])
def test_existing_station_tag_suppresses_spawn_even_when_retirement_phase_is_zero(original_image,memory,symbols,index,phase):
    m,f = memory,symbols; pool = f['world_object_pool']; m[pool:pool+250*68] = bytes(250*68)
    word(m,pool+68*index,99); m[pool+68*index+30] = phase; m[f['space_station_spawn_request']] = 128
    word(m,f['free_object_count'],10); put(m,f['free_object_stack_cursor'],FREE)
    cpu = state(m,0x330C6); run(original_image,m,cpu,{0x3318E})
    assert m[f['space_station_spawn_request']] == 0
    assert get(m,f['free_object_count'],2) == 10 and get(m,f['free_object_stack_cursor']) == FREE
    assert m[pool+68*index+30] == phase and cpu.a[7] == STACK


@pytest.mark.parametrize('speed', [0, 1, 199, 200, 399, 400, 449, 450, 32767, 32768, 65535])
@pytest.mark.parametrize('stardrive', [0, 1, 32768, 65535])
def test_speed_colour_limit_preserves_n_only_thresholds_and_zero_step_reset(original_image,memory,symbols,speed,stardrive):
    m,f = memory,symbols; word(m,f['player_speed_target'],speed); word(m,f['stardrive_enabled_word'],stardrive)
    word(m,f['icarus_speed_colour_step'],0x1234)
    cpu = state(m,0x331E4); run(original_image,m,cpu,{0x3326A})
    maximum = 0 if not speed else 2 if negative(stardrive) else 1
    if speed:
        for threshold in [200,400,450]:
            if negative((speed-threshold)&65535): break
            maximum += 1
    assert get(m,f['icarus_speed_colour_max_step'],2) == maximum
    assert get(m,f['icarus_speed_colour_step'],2) == (0x1234 if speed else 0)
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('step', [0, 1, 4, 5, 65535])
@pytest.mark.parametrize('direction', [0, 1, 65535, 32768])
@pytest.mark.parametrize('maximum', [0, 4, 5])
def test_four_face_bytes_use_old_step_before_retained_step_direction_reversal(original_image,memory,symbols,step,direction,maximum):
    m,f = memory,symbols
    word(m,f['icarus_speed_colour_step'],step); word(m,f['icarus_speed_colour_step_direction'],direction)
    word(m,f['icarus_speed_colour_max_step'],maximum)
    colour = m[f['icarus_speed_face_colour_indices']+signed(step)]
    before = [bytes(m[f['icarus_speed_animated_face_'+str(i)]:f['icarus_speed_animated_face_'+str(i)]+4]) for i in range(4)]
    cpu = state(m,0x3326A); run(original_image,m,cpu,{0x332C8})
    value = (step+direction)&65535; reverse = negative(value) or signed(value)>signed(maximum)
    assert get(m,f['icarus_speed_colour_step'],2) == (step if reverse else value)
    assert get(m,f['icarus_speed_colour_step_direction'],2) == ((-direction)&65535 if reverse else direction)
    for i in range(4):
        address = f['icarus_speed_animated_face_'+str(i)]; expected = bytearray(before[i]); expected[1] = colour
        assert bytes(m[address:address+4]) == expected
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('cooldown', [0, 1, 2, 32768, 32769, 65534, 65535])
def test_pirate_warning_word_ages_with_original_negative_sentinel_and_overflow(original_image,memory,symbols,cooldown):
    m,f = memory,symbols; word(m,f['pirate_warning_cooldown_or_negative'],cooldown)
    cpu = state(m,0x3318E); run(original_image,m,cpu,{0x3319E})
    value = (cooldown-1)&65535
    assert get(m,f['pirate_warning_cooldown_or_negative'],2) == (65535 if negative(value) else value)
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('space', [0, 1, 128])
@pytest.mark.parametrize('nearby', [0, 1, 128])
@pytest.mark.parametrize('step', [0, 1, 4, 5, 6, 32767, 32768, 65534, 65535])
def test_station_disc_colour_uses_sign_gates_and_retains_unbounded_word_aliases(original_image,memory,symbols,space,nearby,step):
    m,f = memory,symbols; m[f['space_environment_flag']],m[f['space_station_nearby_flag']] = space,nearby
    word(m,f['station_proximity_colour_ramp_step'],step)
    expected_step,colour = step,3
    if negative(space,8):
        expected_step = (step+(1 if negative(nearby,8) else -1))&65535
        if negative(nearby,8):
            if not negative((expected_step-6)&65535): expected_step = 5
        elif negative(expected_step): expected_step = 0
        colour = get(m,f['station_proximity_disc_colour_ramp']+signed(2*expected_step),2)
    cpu = state(m,0x3319E); run(original_image,m,cpu,{0x331E4})
    assert get(m,f['station_proximity_colour_ramp_step'],2) == expected_step
    assert get(m,f['station_proximity_disc_colour_index'],2) == colour and cpu.a[7] == STACK


@pytest.mark.parametrize('pending', [0, 1, 127])
def test_positive_nonzero_station_request_does_not_enter_spawn_service(original_image,memory,symbols,pending):
    m,f = memory,symbols; m[f['space_station_spawn_request']] = pending
    word(m,f['free_object_count'],10); put(m,f['free_object_stack_cursor'],FREE)
    cpu = state(m,0x330C6); run(original_image,m,cpu,{0x3318E})
    assert m[f['space_station_spawn_request']] == pending
    assert get(m,f['free_object_count'],2) == 10 and get(m,f['free_object_stack_cursor']) == FREE
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('contact', [0, 1, 65535])
@pytest.mark.parametrize('stardrive', [0, 1, 32768, 65535])
def test_nonzero_contact_clears_drive_but_only_negative_prior_word_requests_warning(original_image,memory,symbols,contact,stardrive):
    m,f = memory,symbols; word(m,f['last_player_contact_type'],contact); word(m,f['stardrive_enabled_word'],stardrive)
    word(m,COUNT,1); word(m,TIMER,33); put(m,QUEUE-4,0x123456); put(m,QUEUE,0x765432)
    cpu = state(m,0x32F9E); run(original_image,m,cpu,{0x32FE0})
    warned = contact != 0 and negative(stardrive)
    assert get(m,f['stardrive_enabled_word'],2) == (0 if contact else stardrive)
    if warned:
        assert get(m,COUNT,2) == 4 and get(m,TIMER,2) == 0
        assert [get(m,QUEUE+4*i) for i in range(4)] == [get(m,f['event_message_pointers']+4*61),BLANK,
            get(m,f['event_message_pointers']+4),get(m,f['event_message_pointers']+4*35)]
    else: assert get(m,COUNT,2) == 1 and get(m,TIMER,2) == 33 and get(m,QUEUE) == 0x765432
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('space', [0, 1, 128])
@pytest.mark.parametrize('y', [-1999, -2000, -3999, -4000, -7999, -8000, 120, -2147483648])
@pytest.mark.parametrize('body', [0, 16, 17, 65535])
def test_altitude_material_profile_retains_n_only_limits_and_unchecked_body_aliases(original_image,memory,symbols,space,y,body):
    m,f = memory,symbols; m[f['space_environment_flag']] = space
    put(m,f['player_world_y'],y&0xFFFFFFFF)
    # This app field is already present in the original layout; explicit aliases
    # outside the 17-entry prefix do not establish legitimate body selections.
    word(m,f['selected_celestial_body_index'],body); word(m,f['special_mesh_material_index'],0x7777)
    altitude = (-y)&0xFFFFFFFF; expected = 0x7777
    if not negative(space,8) and negative((altitude-8000)&0xFFFFFFFF,32):
        profile = ('world_low_altitude_mesh_material_indices' if negative((altitude-2000)&0xFFFFFFFF,32)
                   else 'world_middle_altitude_mesh_material_indices' if negative((altitude-4000)&0xFFFFFFFF,32)
                   else 'world_high_altitude_mesh_material_indices')
        expected = get(m,f[profile]+signed(2*body),2)
    cpu = state(m,0x332C8); run(original_image,m,cpu,{0x33310})
    assert get(m,f['special_mesh_material_index'],2) == expected and cpu.a[7] == STACK
