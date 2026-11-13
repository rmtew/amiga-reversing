"""Original flying-height, angular and Horatio motion control windows.

Records, caller registers and readable trig tables are supplied inputs. These
cases do not establish normal-game reachability, complete frames or lifetimes.
"""
import struct
import subprocess
from pathlib import Path

import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, RETURN
from tests.test_starglider2_gbml_targeting import fields, prepare, OBJ
from tests.test_starglider2_homing_updates import signed32, install
from tests.test_starglider2_scan_acquisition import signed16, project


@pytest.fixture(scope='module')
def thresholds(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('flying-control'); asm, out = folder/'map.s', folder/'map.raw'
    names = ['object_ai_y_increase_thresholds', 'object_ai_y_decrease_thresholds']
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result = subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'), '-quiet', '-Fbin',
        '-m68000', '-no-opt', '-I'+str(target/'includes'), '-o', str(out), str(asm)],
        cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    raw = out.read_bytes(); assert raw[:-8] == original_image[0]
    return struct.unpack('>II', raw[-8:])


@pytest.mark.parametrize('entry,stop', [(0x90B2,0x90E6),(0x8C9C,0x8CE8)])
@pytest.mark.parametrize('roll', list(range(32))+[1008,1009,1023,1024,1025,2048,4080,4081,4082,4095,4096,65535])
def test_roll_bytecode_preserves_masked_underflow_and_raw_zero_aliases(original_image, memory, entry, stop, roll):
    put(memory, OBJ+20, roll, 2)
    masked = roll&4095
    expected = (roll+1)&65535 if not masked else (masked+(-15 if masked<1025 else 15))&4095
    if entry==0x8C9C and masked>=1025 and expected==0: expected=1
    cpu = state(memory, entry); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {stop}, limit=20)
    assert get(memory, OBJ+20, 2) == expected


@pytest.mark.parametrize('y', [-100000,-1701,-1700,-1600,-1000,-501,-500,-41,-40,-39,0,39,40,41,100000,0x7FFFFFFF])
@pytest.mark.parametrize('velocity', [-32768,-11,-10,-6,-5,-4,0,4,5,6,10,11,32767])
@pytest.mark.parametrize('countdown', [0,1,65535])
@pytest.mark.parametrize('player_y', [-2000,-100,100])
def test_flying_height_gates_use_integrated_y_and_original_velocity_limits(original_image, memory, fields, thresholds, y, velocity, countdown, player_y):
    prepare(memory, fields, 13); memory[OBJ+28] = 8
    for off,value in [(4,65530),(8,y&0xFFFFFFFF),(12,3)]: put(memory, OBJ+off, value)
    for off,value in [(16,123),(36,0),(38,countdown),(44,9),(46,velocity&65535),(48,65531)]: put(memory, OBJ+off, value, 2)
    put(memory, APP+0x6FC,65535); put(memory, fields['player_world_y'], player_y&0xFFFFFFFF)
    integrated = signed32(y+velocity)
    low, high = [signed16(get(memory,p+26,2)) for p in thresholds]
    pitch = 123
    if integrated<=low:
        next_v = signed16(velocity+1); next_v = min(next_v,10)
    elif countdown or integrated>=high:
        next_v = signed16(velocity-1); next_v = max(next_v,-10)
    elif signed32(player_y-integrated)<0 and integrated<=-40:
        next_v = signed16(velocity-1); next_v = -4 if next_v<-5 else next_v
    elif signed32(player_y-integrated)>=0 and integrated>=40:
        next_v = signed16(velocity+1); next_v = 4 if next_v>5 else next_v
    else: next_v, pitch = 0, 0
    cpu = state(memory,0x9010); cpu.a[0] = OBJ
    run(original_image,memory,cpu,{0x90B2},limit=65)
    assert [get(memory,OBJ+off) for off in [4,8,12]] == [3,integrated&0xFFFFFFFF,65534]
    assert get(memory,OBJ+46,2)==next_v&65535 and get(memory,OBJ+16,2)==pitch
    assert get(memory,OBJ+36,2)==65535 and get(memory,OBJ+38,2)==countdown


@pytest.mark.parametrize('entry', [0xACB0,0xAD00])
@pytest.mark.parametrize('yaw', [0,1,2047,2048,2049,4095,65535])
@pytest.mark.parametrize('target', [0,1,2047,2048,2049,4095,65535])
@pytest.mark.parametrize('roll', [0,1,4095,65535])
def test_heading_blend_stores_unmasked_yaw_and_recomputes_original_velocity(original_image,memory,fields,entry,yaw,target,roll):
    prepare(memory,fields,17);install(original_image,memory)
    for off,value in [(16,123),(18,yaw),(20,roll),(32,65186),(46,65530)]:put(memory,OBJ+off,value,2)
    current, goal = yaw&4095,target&4095
    step = signed16(goal-current)>>5
    delta = -step if abs(current-goal)>2048 else step
    next_yaw = (current+delta)&65535
    next_roll = 0 if entry==0xACB0 else ((roll+delta)&4095 or 1)
    sine,cosine=[get(memory,fields[n])for n in ['sine_lookup_pointer','cosine_lookup_pointer']]
    angle=next_yaw&4095
    velocities=[(-project(-350,get(memory,sine+2*angle,2)))&65535,project(-350,get(memory,cosine+2*angle,2))&65535]
    cpu=state(memory,entry);cpu.a[0]=OBJ;cpu.d[1]=0xABCD0000|target
    run(original_image,memory,cpu,{fields['continue_primary_object_update_loop']},limit=70)
    assert get(memory,OBJ+18,2)==next_yaw and get(memory,OBJ+20,2)==next_roll
    assert get(memory,OBJ+16,2)==(0 if entry==0xACB0 else 123)
    assert [get(memory,OBJ+off,2)for off in [44,48]]==velocities and get(memory,OBJ+46,2)==65530


@pytest.mark.parametrize('variant', range(256))
@pytest.mark.parametrize('caller_heading', [0,3000])
def test_horatio_reset_uses_caller_d1_while_other_variants_halve_velocity(original_image,memory,fields,variant,caller_heading):
    prepare(memory,fields,17);install(original_image,memory)
    memory[OBJ+3]=variant
    for off,value in [(18,4090),(32,65186),(44,65533),(48,32767)]:put(memory,OBJ+off,value,2)
    next_variant=(variant+1)&255;next_yaw=4090
    if next_variant in [9,10]:
        next_variant=0;next_yaw=(4090+((caller_heading-4090)&4095)//16)&65535
        sine,cosine=[get(memory,fields[n])for n in ['sine_lookup_pointer','cosine_lookup_pointer']]
        v=[(-project(-350,get(memory,sine+2*(next_yaw&4095),2)))&65535,project(-350,get(memory,cosine+2*(next_yaw&4095),2))&65535]
    else:v=[65534,16383]
    cpu=state(memory,0x92CC);cpu.a[0]=OBJ;cpu.d[1]=0xABCD0000|caller_heading
    run(original_image,memory,cpu,{0x9500},limit=80)
    assert memory[OBJ+3]==next_variant and get(memory,OBJ+18,2)==next_yaw
    assert [get(memory,OBJ+off,2)for off in [44,48]]==v


@pytest.mark.parametrize('entry', [0x9260,0x927A,0x9296,0x92B0])
@pytest.mark.parametrize('velocity', [-32768,-11,-10,-6,-5,-4,0,4,5,6,10,11,32767])
def test_vertical_adjustment_tails_preserve_word_wrap_and_five_to_four_cycle(original_image,memory,entry,velocity):
    put(memory,OBJ+46,velocity&65535,2)
    increasing=entry in [0x9260,0x9296]
    expected=signed16(velocity+(1 if increasing else -1))
    if entry==0x9260: expected=min(expected,10)
    elif entry==0x927A: expected=max(expected,-10)
    elif entry==0x9296: expected=4 if expected>5 else expected
    else: expected=-4 if expected<-5 else expected
    cpu=state(memory,entry);cpu.a[0]=OBJ
    run(original_image,memory,cpu,{0x90B2},limit=8)
    assert get(memory,OBJ+46,2)==expected&65535


@pytest.mark.parametrize('variant', [8,9,255])
@pytest.mark.parametrize('yaw', [0,4095])
def test_horatio_normal_dispatch_carries_relative_routine_offset_into_reset_helper(original_image,memory,fields,variant,yaw):
    prepare(memory,fields,17);install(original_image,memory)
    memory[OBJ+2]=0;memory[OBJ+28]=8;memory[OBJ+3]=variant
    for off,value in [(18,yaw),(32,65186),(44,65533),(48,32767)]:put(memory,OBJ+off,value,2)
    dispatch_delta=get(memory,0x802A+2*17,2)
    assert 0x802A+signed16(dispatch_delta)==0x92CC
    cpu=state(memory,0x800A);cpu.a[0]=OBJ
    run(original_image,memory,cpu,{0x9500},limit=90)
    reset=(variant+1)&255 in [9,10]
    expected=(yaw+((dispatch_delta-yaw)&4095)//16)&65535 if reset else yaw
    assert get(memory,OBJ+18,2)==expected
    assert memory[OBJ+3]==(0 if reset else (variant+1)&255)
