"""Original heat/pressure phases and their shared mutable colour-sequence tail.

Explicit RAM/records and bounded phase stops do not prove normal-game metric
domains, valid pointers, full mission execution or hardware colour delivery.
"""
import json
import struct
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, STACK
from tests.test_starglider2_message_lines import QUEUE, COUNT, TIMER, BLANK

NOTICE = 0x39652
OBJECT, LIST = 0x85000, 0x84000
APP_NAMES = ['space_environment_flag', 'system_center_proximity_metric', 'millway_proximity_metric',
    'player_world_y', 'icarus_shield_strength', 'icarus_power_reserve',
    'type128_disc_outer_layer_index', 'nearby_object_count', 'nearby_objects_cursor']
GLOBALS = ['space_effect_base_rgb_word', 'space_effect_override_rgb_word',
    'system_center_space_colour_bytes', 'millway_space_colour_bytes',
    'type128_disc_layers_by_proximity', 'fatal_overheat_latched_flag', 'event_message_pointers',
    'energy_spheroid_primary_colour_sequence', 'energy_spheroid_secondary_colour_sequence',
    'SG2_SPACE_EFFECT_DEFAULT_OVERRIDE_RGB', 'SG2_SPACE_EFFECT_OVERRIDE_RGB_BITS']


@pytest.fixture(scope='module')
def symbols(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('space-hazards'); asm, out = folder/'map.s', folder/'map.raw'
    names = APP_NAMES+GLOBALS
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin',
        '-m68000', '-no-opt', '-I'+str(target/'includes'), '-o', str(out), str(asm)],
        cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    data = out.read_bytes(); tail = 4*len(names); assert data[:-tail] == original_image[0]
    return {n:v+(APP if n in APP_NAMES else 0) for n,v in
            zip(names, struct.unpack('>'+'I'*len(names), data[-tail:]))}


def word(m,address,value): put(m,address,value&65535,2)
def signed_word(value): return (value+32768)%65536-32768


def prepare(m,f,metric,shield,notice=0,power=0):
    m[f['space_environment_flag']] = 255
    put(m,f['system_center_proximity_metric'],metric); put(m,f['millway_proximity_metric'],metric)
    put(m,f['player_world_y'],(-20000000)&0xFFFFFFFF)
    word(m,f['icarus_shield_strength'],shield); word(m,f['icarus_power_reserve'],power)
    word(m,NOTICE,notice); m[f['fatal_overheat_latched_flag']] = 0
    word(m,f['nearby_object_count'],0)
    word(m,COUNT,1); word(m,TIMER,33); put(m,QUEUE-4,0x123456); put(m,QUEUE,0x765432)


def expected_colours(m,f,metric,star):
    index = (metric>>16)//4 if star else metric>>16
    colour = m[f['system_center_space_colour_bytes' if star else 'millway_space_colour_bytes']+signed_word(index)]<<4
    layer = get(m,f['type128_disc_layers_by_proximity']+signed_word(2*index),2)
    return index,colour,colour|f['SG2_SPACE_EFFECT_OVERRIDE_RGB_BITS'],layer


def assert_message(m,f,index):
    assert get(m,COUNT,2) == 3 and get(m,TIMER,2) == 0
    assert [get(m,QUEUE+4*i) for i in range(3)] == [get(m,f['event_message_pointers']+4*index),BLANK,
        get(m,f['event_message_pointers']+4*35)]


@pytest.mark.parametrize('metric', [0, 0x40000, 5999999, 0xFFFFFFFF])
@pytest.mark.parametrize('shield_case', ['borrow','exact','survive','maximum'])
@pytest.mark.parametrize('notice', [0, 1, 32768])
@pytest.mark.parametrize('power', [0, 65530])
def test_star_heat_uses_word_damage_borrow_and_power_carry_with_metric_warning_reload(original_image,memory,symbols,metric,shield_case,notice,power):
    m,f = memory,symbols; index = (metric>>16)//4
    damage,bonus = (736-32*index)&65535,(92-4*index)&65535
    shield = {'borrow':damage-1,'exact':damage,'survive':damage+1,'maximum':65535}[shield_case]
    prepare(m,f,metric,shield,notice,power)
    _,base,override,layer = expected_colours(m,f,metric,True)
    cpu = state(m,0x33310); run(original_image,m,cpu,{0x33528})
    fatal = shield<damage; expired = bool(((notice-1)&65535)&32768)
    assert get(m,f['icarus_shield_strength'],2) == (0 if fatal else shield-damage)
    assert get(m,f['icarus_power_reserve'],2) == (power if fatal else min(65535,power+bonus))
    assert get(m,NOTICE,2) == (notice if fatal else metric>>16 if expired else (notice-1)&65535)
    assert m[f['fatal_overheat_latched_flag']] == (255 if fatal else 0)
    assert [get(m,f[n],2) for n in ['space_effect_base_rgb_word','space_effect_override_rgb_word','type128_disc_outer_layer_index']] == [base,override,layer]
    if fatal or expired: assert_message(m,f,44 if fatal else 45)
    else: assert get(m,COUNT,2) == 1 and get(m,TIMER,2) == 33 and get(m,QUEUE) == 0x765432
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('metric', [0, 899999, 900000, 1199999, 0xFFFFFFFF])
@pytest.mark.parametrize('shield_case', ['borrow','exact','survive','maximum'])
@pytest.mark.parametrize('notice', [0, 1, 32768])
def test_millway_pressure_uses_two_losses_and_fixed_warning_reload_without_power_or_retirement(original_image,memory,symbols,metric,shield_case,notice):
    m,f = memory,symbols; damage = 512 if not ((metric-900000)&0x80000000) else 2048
    shield = {'borrow':damage-1,'exact':damage,'survive':damage+1,'maximum':65535}[shield_case]
    prepare(m,f,metric,shield,notice,0x1234)
    m[f['fatal_overheat_latched_flag']] = 0x55
    word(m,f['nearby_object_count'],1); put(m,f['nearby_objects_cursor'],LIST); put(m,LIST,OBJECT)
    m[OBJECT:OBJECT+68] = b'\xA5'*68
    _,base,override,layer = expected_colours(m,f,metric,False)
    cpu = state(m,0x33440); run(original_image,m,cpu,{0x33524})
    fatal = shield<damage; expired = bool(((notice-1)&65535)&32768)
    assert get(m,f['icarus_shield_strength'],2) == (0 if fatal else shield-damage)
    assert get(m,f['icarus_power_reserve'],2) == 0x1234 and m[f['fatal_overheat_latched_flag']] == 0x55
    assert bytes(m[OBJECT:OBJECT+68]) == b'\xA5'*68
    assert get(m,NOTICE,2) == (notice if fatal else 30 if expired else (notice-1)&65535)
    assert [get(m,f[n],2) for n in ['space_effect_base_rgb_word','space_effect_override_rgb_word','type128_disc_outer_layer_index']] == [base,override,layer]
    if fatal or expired: assert_message(m,f,65 if fatal else 66)
    else: assert get(m,COUNT,2) == 1 and get(m,TIMER,2) == 33
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('latch', [0, 1, 127, 128, 255])
def test_fatal_heat_always_requests_warning_but_only_nonnegative_latch_clears_nonplayer_phases(original_image,memory,symbols,latch):
    m,f = memory,symbols; prepare(m,f,0,0,7,0x1234)
    m[f['fatal_overheat_latched_flag']] = latch
    types = [0,30,1,99]; word(m,f['nearby_object_count'],len(types)); put(m,f['nearby_objects_cursor'],LIST)
    for i,kind in enumerate(types):
        put(m,LIST+4*i,OBJECT+68*i); m[OBJECT+68*i:OBJECT+68*(i+1)] = b'\xA5'*68
        word(m,OBJECT+68*i,kind)
    expected = bytearray(m[OBJECT:OBJECT+68*len(types)])
    if latch<128:
        for i,kind in enumerate(types):
            if kind == 30: continue
            expected[68*i+2] &= ~12; expected[68*i+28] = expected[68*i+30] = 0
    cpu = state(m,0x33310); run(original_image,m,cpu,{0x33528})
    assert bytes(m[OBJECT:OBJECT+68*len(types)]) == expected
    assert m[f['fatal_overheat_latched_flag']] == (255 if latch<128 else latch)
    assert get(m,NOTICE,2) == 7 and get(m,f['icarus_power_reserve'],2) == 0x1234
    assert_message(m,f,44); assert cpu.a[7] == STACK


@pytest.mark.parametrize('space,star,pressure,y,route,index', [
    (0,0,0,-20000000,'skip',None), (1,0,0,-20000000,'skip',None),
    (128,0,0,-20000000,'star',0), (255,5999999,0,-18000001,'star',22),
    (255,6000000,0,-20000000,'pressure',0), (255,6000000,1199999,-19600001,'pressure',18),
    (255,6000000,1200000,-20000000,'default',None),
    (255,0,1200000,-18000000,'default',None), (255,0,1200000,-22000000,'default',None),
    (255,6000000,0,-19600000,'default',None), (255,6000000,0,-20400000,'default',None),
    (255,0x80000000,0,-20000000,'pressure',0), (255,0x80600000,0,-20000000,'star',8216),
    (255,0xFFFFFFFF,0,-20000000,'star',16383), (255,6000000,0xFFFFFFFF,-20000000,'pressure',65535),
    (255,0,0,-2147483648,'default',None), (255,0,1200000,-21999999,'star',0),
])
def test_proximity_and_height_routes_preserve_priority_n_only_aliases_and_default_distinction(original_image,memory,symbols,space,star,pressure,y,route,index):
    m,f = memory,symbols; prepare(m,f,0,0x7777,0x1234,0x5678)
    m[f['space_environment_flag']] = space; put(m,f['system_center_proximity_metric'],star)
    put(m,f['millway_proximity_metric'],pressure); put(m,f['player_world_y'],y&0xFFFFFFFF)
    for n,value in [('space_effect_base_rgb_word',0xABCD),('space_effect_override_rgb_word',0x2468),('type128_disc_outer_layer_index',0x1357)]: word(m,f[n],value)
    cpu = state(m,0x33310); run(original_image,m,cpu,{0x3334C,0x33468,0x33528})
    assert cpu.pc == (0x3334C if route=='star' else 0x33468 if route=='pressure' else 0x33528)
    if index is not None: assert cpu.d[0]&65535 == index
    expected = [0,f['SG2_SPACE_EFFECT_DEFAULT_OVERRIDE_RGB'],3] if route=='default' else [0xABCD,0x2468,0x1357]
    assert [get(m,f[n],2) for n in ['space_effect_base_rgb_word','space_effect_override_rgb_word','type128_disc_outer_layer_index']] == expected
    assert get(m,f['icarus_shield_strength'],2) == 0x7777 and get(m,f['icarus_power_reserve'],2) == 0x5678
    assert get(m,NOTICE,2) == 0x1234 and cpu.a[7] == STACK


@pytest.mark.parametrize('producer', ['star_reset', 'pressure_reset', 'word_overflow'])
@pytest.mark.parametrize('index', [30, 31])
def test_warning_reload_is_read_as_mutable_tail_bytes_by_original_spheroid_phase(original_image,memory,symbols,producer,index):
    m,f = memory,symbols
    # A star reset supplies metric highWORD80; pressure supplies30. Neither is
    # the zeroWORD present in the initial image, and no guest patch is made
    # between these two original phase executions.
    star = producer != 'pressure_reset'
    prepare(m,f,0x500000 if star else 0,65535,32768 if producer=='word_overflow' else 0,0)
    m[OBJECT:OBJECT+68] = bytes(68); word(m,OBJECT,146); word(m,OBJECT+16,index)
    word(m,OBJECT+18,0); m[OBJECT+31] = 255; word(m,OBJECT+60,1); put(m,OBJECT+54,1000)
    cpu = state(m,0x33310 if star else 0x33440); run(original_image,m,cpu,{0x33528,0x33524})
    reset = 32767 if producer=='word_overflow' else 80 if star else 30
    assert get(m,NOTICE,2) == reset
    secondary = f['energy_spheroid_secondary_colour_sequence']
    assert NOTICE-secondary == 30
    assert secondary-f['energy_spheroid_primary_colour_sequence'] == 30
    cpu = state(m,0x362F4); cpu.a[0] = OBJECT
    expected_primary = m[f['energy_spheroid_primary_colour_sequence']+index]
    expected_secondary = m[secondary+index]
    run(original_image,m,cpu,{0x3635A})
    assert get(m,OBJECT+16,2) == (index+1)&31
    assert m[OBJECT+20] == expected_primary and m[OBJECT+21] == expected_secondary
    assert expected_secondary == (reset>>8 if index==30 else reset&255)
    assert get(m,NOTICE,2) == reset and cpu.a[7] == STACK


def test_secondary_colour_owner_retains_shared_countdown_tail():
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    with effective_metadata_file(target) as path: md = json.loads(path.read_text())
    owner = next(r for r in md['seeded_entities'] if r['name']=='energy_spheroid_secondary_colour_sequence')
    assert owner['end']-owner['addr'] == 32 and owner['unit']=='byte'
    assert owner['addr']+0x1000+30 == NOTICE
