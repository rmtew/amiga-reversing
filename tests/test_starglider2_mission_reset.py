"""Original mission reset and its population/proximity services.

Supplied RAM states qualify local reset footprints and arithmetic. They do not
establish complete new-game setup, save-state validity or physical distances.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, RETURN, STACK

ARRAYS = {
    'released_object_tracking_references': 40,
    'model_type_population_counts': 104,
    'taymar_delivered_model_counts_prefix': 104,
    'structure_service_entry_counts': 12,
    'structure_service_entry_latches': 12,
    'projector_part_presence_flags': 56,
}
SCALARS = {
    'station_sequence_index': (2, 0), 'station_event_tick_counter': (4, 0),
    'station_space_half_rate_toggle': (4, 0), 'projector_rebuild_cursor': (2, 55),
    'growing_projector_part_reference': (4, 0), 'growing_projector_part_type': (2, 0),
    'station_construction_steps_remaining': (2, 52), 'station_charge_steps_remaining': (2, 4),
    'station_firing_steps_remaining': (2, 2), 'station_report_primary_message': (4, 0),
    'station_report_secondary_message': (4, 0), 'pending_message_count': (2, 0),
    'message_display_countdown': (2, 1), 'carried_neutron_bomb_reference': (4, 0),
    'stardrive_speed_addend': (2, 0), 'stardrive_enabled_word': (2, 0),
    'station_mini_sentinel_count': (2, 8), 'station_cycle_enabled_flag': (1, 255),
    'neutron_bomb_order_requested_flag': (1, 0), 'professor_taymar_aboard_flag': (1, 0),
    'professor_taymar_delivered_flag': (1, 0), 'bomb_ingredient_set_complete_flag': (1, 0),
    'neutron_bomb_collection_enabled_flag': (1, 0), 'neutron_bomb_ready_flag': (1, 0),
    'neutron_bomb_spawn_request': (1, 0), 'neutron_bomb_retract_request': (1, 0),
    'projector_network_complete_flag': (1, 0), 'space_station_spawn_request': (1, 0),
}
APP_NAMES = list(dict.fromkeys([*ARRAYS, *SCALARS, 'cached_body_state_prefix', 'body_orbit_angle_words',
    'neutron_bomb_spawn_countdown', 'station_event_cadence_mask', 'player_world_x', 'player_world_z',
    'free_object_count', 'system_center_proximity_metric', 'millway_proximity_metric',
    'millway_orbit_parent_x', 'millway_orbit_parent_z', 'space_environment_flag', 'inside_structure_flag',
    'selected_celestial_body_index', 'player_speed_smoothed', 'nearby_object_count', 'nearby_objects_cursor']))
GLOBAL_NAMES = ['initialize_mission_and_flight_state', 'update_system_center_proximity_metric',
    'update_millway_proximity_metric', 'recompute_counted_model_population', 'model_header_pointers',
    'initial_cached_body_states', 'initial_body_orbit_angles', 'station_sequence_bomb_spawn_countdowns',
    'station_sequence_cadence_masks', 'counted_model_population', 'counted_model_population_times32',
    'event_message_pointers', 'object_name_pointers', 'depot_text_we_need_professor_taymar',
    'depot_text_bomb_under_construction', 'depot_text_bomb_constructed', 'clear_stardrive_below_speed_threshold',
    'enqueue_nearby_sound_analysis', 'selected_object_sound_type', 'nearby_sound_analysis_text_pointers',
    'novenia_report_repeat_delay', 'novenia_report_repeats_remaining']


@pytest.fixture(scope='module')
def fields(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('mission-reset'); asm, out = folder/'fields.s', folder/'fields.raw'
    names = APP_NAMES + GLOBAL_NAMES
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin',
        '-m68000', '-no-opt', '-I'+str(target/'includes'), '-o', str(out), str(asm)],
        cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    raw = out.read_bytes(); tail = 4*len(names); assert raw[:-tail] == original_image[0]
    f = dict(zip(names, struct.unpack('>'+'I'*len(names), raw[-tail:])))
    for name in APP_NAMES: f[name] += APP
    return f


@pytest.mark.parametrize('old_byte', [0, 0x55, 0xA5, 255])
def test_reset_rebuilds_campaign_arrays_and_station_state_but_retains_player_and_pool(original_image, memory, fields, old_byte):
    m,f = memory,fields
    m[APP:APP+0x7000] = bytes([old_byte])*0x7000
    untouched = {n:get(m,f[n],2 if n=='free_object_count' else 4)
                 for n in ('player_world_x','player_world_z','free_object_count')}
    header = get(m,f['model_header_pointers']+99*4)
    put(m,header+2,0x4567,2); old_header = bytes(m[header:header+24])
    cpu = state(m,f['initialize_mission_and_flight_state'])
    run(original_image,m,cpu,{RETURN})
    for name,size in ARRAYS.items(): assert bytes(m[f[name]:f[name]+size]) == bytes(size),name
    for name,(width,value) in SCALARS.items(): assert get(m,f[name],width)==value,name
    for name,value in untouched.items(): assert get(m,f[name],2 if name=='free_object_count' else 4)==value,name
    for dest,source,size in [('cached_body_state_prefix','initial_cached_body_states',272),
                             ('body_orbit_angle_words','initial_body_orbit_angles',34)]:
        assert bytes(m[f[dest]:f[dest]+size])==bytes(m[f[source]:f[source]+size])
    assert get(m,f['neutron_bomb_spawn_countdown'],2)==get(m,f['station_sequence_bomb_spawn_countdowns'],2)
    assert get(m,f['station_event_cadence_mask'],2)==get(m,f['station_sequence_cadence_masks'],2)
    expected = bytearray(old_header); expected[2:4] = b'\0\0'
    assert bytes(m[header:header+24])==expected
    assert cpu.a[7]==STACK+4


def u32(value): return value & 0xffffffff

def magnitude_from_n(value):
    value = u32(value)
    return u32(-value) if value & 0x80000000 else value


@pytest.mark.parametrize('millway', [False, True])
@pytest.mark.parametrize('dx', [0,1,-1,1000,-1000,0x3fffffff,0x40000000,0x7fffffff,0x80000000,0xffffffff])
@pytest.mark.parametrize('dz', [0,1,-1,2000,-2000,0x3fffffff,0x40000000,0x7fffffff,0x80000000,0xffffffff])
def test_proximity_service_keeps_result_sign_choice_and_long_wrap(original_image,memory,fields,millway,dx,dz):
    m,f = memory,fields
    cx,cz = (0xffff0000,0x12345678) if millway else (20000000,20000000)
    put(m,f['millway_orbit_parent_x'],cx); put(m,f['millway_orbit_parent_z'],cz)
    put(m,f['player_world_x'],u32(cx+dx)); put(m,f['player_world_z'],u32(cz+dz))
    x,z = magnitude_from_n(dx),magnitude_from_n(dz)
    # Original CMP/BPL selects from the subtraction result's N flag, without V.
    chosen = x if u32(z-x)&0x80000000 else z
    expected = u32(x+z+2*chosen)
    name = 'millway' if millway else 'system_center'
    cpu = state(m,f['update_'+name+'_proximity_metric']); run(original_image,m,cpu,{RETURN})
    assert get(m,f[name+'_proximity_metric'])==expected
    assert cpu.a[7]==STACK+4


@pytest.mark.parametrize('mode', ['zero','ones','high_bits','all_255','ordinal'])
def test_population_service_excludes_four_ids_and_wraps_scaled_word(original_image,memory,fields,mode):
    values = {'zero':bytes(104),'ones':bytes([1])*104,'high_bits':bytes([128])*104,
              'all_255':bytes([255])*104,'ordinal':bytes(range(104))}[mode]
    m,f = memory,fields; m[f['model_type_population_counts']:f['model_type_population_counts']+104]=values
    total = sum(v for i,v in enumerate(values) if i not in (12,91,98,84))
    cpu = state(m,f['recompute_counted_model_population']); saved=(cpu.d[0],cpu.d[1],cpu.a[1])
    run(original_image,m,cpu,{RETURN})
    assert get(m,f['counted_model_population'],2)==total
    assert get(m,f['counted_model_population_times32'],2)==(total*32)&65535
    assert (cpu.d[0],cpu.d[1],cpu.a[1])==saved and cpu.a[7]==STACK+4
    assert bytes(m[f['model_type_population_counts']:f['model_type_population_counts']+104])==values


@pytest.mark.parametrize('space', [0, 1, 128])
@pytest.mark.parametrize('inside', [0, 1, 128])
@pytest.mark.parametrize('has_report', [False, True])
@pytest.mark.parametrize('ordered,delivered,ready', [(0,0,0),(128,0,0),(128,128,0),(128,128,128)])
def test_status_report_combines_location_and_order_phase_with_distinct_flag_gates(original_image,memory,fields,space,inside,has_report,ordered,delivered,ready):
    from tests.test_starglider2_message_lines import QUEUE, COUNT, TIMER, BLANK
    m,f = memory,fields
    for name,value in [('space_environment_flag',space),('inside_structure_flag',inside),
        ('professor_taymar_aboard_flag',0),('neutron_bomb_order_requested_flag',ordered),
        ('professor_taymar_delivered_flag',delivered),('neutron_bomb_ready_flag',ready)]:m[f[name]]=value
    put(m,f['selected_celestial_body_index'],4,2)
    primary,secondary=0x88000,0x88100
    put(m,f['station_report_primary_message'],primary if has_report else 0)
    put(m,f['station_report_secondary_message'],secondary)
    put(m,QUEUE-4,0x123456);put(m,COUNT,7,2);put(m,TIMER,33,2)
    event=lambda index:get(m,f['event_message_pointers']+index*4)
    expected=[event(43),event(40)]
    expected.append(event(41) if space&128 else event(83) if inside&128 else get(m,f['object_name_pointers']+132*4))
    if inside==0:expected.append(event(15))
    if has_report:
        if inside==0:expected.extend([primary,secondary])
        if ordered&128 and inside==0:
            expected.extend([event(82),f['depot_text_we_need_professor_taymar'] if not delivered&128 else
                f['depot_text_bomb_constructed'] if ready&128 else f['depot_text_bomb_under_construction']])
    elif inside==0:expected.append(event(19))
    expected.append(event(35))
    # Shared queue inserts its empty first separator and rejects only adjacent
    # duplicates/capacity. This test checks the original caller's message order.
    queue=[]
    for pointer in expected:
        if len(queue)>=10 or queue and queue[-1]==pointer:continue
        queue.append(pointer)
        if len(queue)==1:queue.append(BLANK)
    cpu=state(m,0x36372);saved=(cpu.d[0],cpu.d[1],cpu.a[1])
    run(original_image,m,cpu,{RETURN})
    assert get(m,COUNT,2)==len(queue)
    assert [get(m,QUEUE+4*i)for i in range(len(queue))]==queue
    assert get(m,TIMER,2)==0
    assert (cpu.d[0],cpu.d[1],cpu.a[1])==saved and cpu.a[7]==STACK+4


@pytest.mark.parametrize('speed', [0,63,64,32767,32768,32831,65535])
@pytest.mark.parametrize('enabled', [0,1,32768,65535])
def test_stardrive_speed_clear_uses_n_and_only_reports_negative_enabled_state(original_image,memory,fields,speed,enabled):
    from tests.test_starglider2_message_lines import QUEUE, COUNT, TIMER, BLANK
    m,f=memory,fields;put(m,f['player_speed_smoothed'],speed,2);put(m,f['stardrive_enabled_word'],enabled,2)
    put(m,COUNT,0,2);put(m,TIMER,33,2);put(m,QUEUE-4,0x123456)
    before=bytes(m[QUEUE:QUEUE+40]);clear=bool(((speed-64)&65535)&32768)
    cpu=state(m,f['clear_stardrive_below_speed_threshold']);run(original_image,m,cpu,{RETURN})
    assert get(m,f['stardrive_enabled_word'],2)==(0 if clear else enabled)
    if clear and enabled&32768:
        assert get(m,COUNT,2)==3 and get(m,TIMER,2)==0
        assert [get(m,QUEUE+4*i)for i in range(3)]==[get(m,f['event_message_pointers']+4),BLANK,get(m,f['event_message_pointers']+35*4)]
    else:assert get(m,COUNT,2)==0 and get(m,TIMER,2)==33 and bytes(m[QUEUE:QUEUE+40])==before
    assert cpu.a[7]==STACK+4


@pytest.mark.parametrize('count', [0,1,2])
@pytest.mark.parametrize('match_at', [None,0,1])
def test_sound_analysis_resets_queue_only_after_nearby_type_match(original_image,memory,fields,count,match_at):
    from tests.test_starglider2_message_lines import QUEUE, COUNT, TIMER, BLANK
    m,f=memory,fields; cursor=0x88000;records=[0x88100,0x88200];selected=12
    put(m,f['selected_object_sound_type'],selected,2);put(m,f['nearby_object_count'],count,2)
    put(m,f['nearby_objects_cursor'],cursor)
    for i,address in enumerate(records):put(m,cursor+i*4,address);put(m,address,selected if i==match_at else 1,2)
    put(m,COUNT,3,2);put(m,TIMER,33,2);put(m,QUEUE-4,0x123456)
    before=bytes(m[QUEUE:QUEUE+40]);cpu=state(m,f['enqueue_nearby_sound_analysis']);saved=(cpu.d[0],cpu.a[4])
    run(original_image,m,cpu,{RETURN})
    if match_at is not None and match_at<count:
        expected=[get(m,f['nearby_sound_analysis_text_pointers']),BLANK,get(m,f['object_name_pointers']+selected*4),
                  get(m,f['nearby_sound_analysis_text_pointers']+4),get(m,f['event_message_pointers']+35*4)]
        assert get(m,COUNT,2)==5 and get(m,TIMER,2)==0
        assert [get(m,QUEUE+4*i)for i in range(5)]==expected
    else:assert get(m,COUNT,2)==3 and get(m,TIMER,2)==33 and bytes(m[QUEUE:QUEUE+40])==before
    assert (cpu.d[0],cpu.a[4])==saved and cpu.a[7]==STACK+4


@pytest.mark.parametrize('delay', [0,1,32767,32768,65535])
@pytest.mark.parametrize('repeats', [0,1,32768,65535])
def test_novenia_report_repeat_gate_preserves_word_wrap_and_status_pointers(original_image,memory,fields,delay,repeats):
    from tests.test_starglider2_message_lines import QUEUE, COUNT, TIMER, BLANK
    m,f=memory,fields;put(m,f['novenia_report_repeat_delay'],delay,2);put(m,f['novenia_report_repeats_remaining'],repeats,2)
    put(m,COUNT,3,2);put(m,TIMER,33,2);put(m,QUEUE-4,0x123456)
    put(m,f['station_report_primary_message'],0x123450);put(m,f['station_report_secondary_message'],0x234560)
    old=bytes(m[QUEUE:QUEUE+40]);ticks=((delay-1)&65535)&32768
    next_repeats=(repeats-1)&65535 if ticks else repeats
    report=bool(ticks) and not(next_repeats&32768)
    cpu=state(m,0x376F8);run(original_image,m,cpu,{0x37778})
    assert get(m,f['novenia_report_repeat_delay'],2)==(256 if ticks else (delay-1)&65535)
    assert get(m,f['novenia_report_repeats_remaining'],2)==(65535 if ticks and next_repeats&32768 else next_repeats)
    event=lambda index:get(m,f['event_message_pointers']+index*4)
    if report:
        assert get(m,COUNT,2)==6 and get(m,TIMER,2)==0
        assert [get(m,QUEUE+4*i)for i in range(6)]==[event(15),BLANK,event(46),event(47),event(48),event(35)]
        assert get(m,f['station_report_primary_message'])==event(46)
        assert get(m,f['station_report_secondary_message'])==event(47)
    else:
        assert get(m,COUNT,2)==3 and get(m,TIMER,2)==33 and bytes(m[QUEUE:QUEUE+40])==old
        assert get(m,f['station_report_primary_message'])==0x123450
        assert get(m,f['station_report_secondary_message'])==0x234560


@pytest.mark.parametrize('cursor', [0,1,55,56,32768,65535])
@pytest.mark.parametrize('flag', [0,1,127,128,255])
@pytest.mark.parametrize('random_result', [0,1,128,255])
def test_projector_presence_loss_masks_random_input_then_decrements_before_flag_test(original_image,memory,fields,cursor,flag,random_result):
    m,f=memory,fields;put(m,f['projector_rebuild_cursor'],cursor,2)
    selected=(cursor-1)&65535
    if selected&32768:selected=55
    address=f['projector_part_presence_flags']+selected
    assert address<len(m)
    m[address]=flag;cpu=state(m,0x3777C);cpu.d[0]=random_result
    run(original_image,m,cpu,{0x377A0})
    active=(random_result&127)==0
    assert get(m,f['projector_rebuild_cursor'],2)==(selected if active else cursor)
    assert m[address]==(0 if active and flag&128 else flag)
