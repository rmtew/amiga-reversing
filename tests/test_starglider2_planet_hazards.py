"""Original Broadway/Dante windows in explicit disjoint RAM contexts.

No normal-play probability, pointer lifetime, valid restored-state, complete
mission, display/audio delivery or physical-cadence guarantee follows.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP
from tests.test_starglider2_message_lines import QUEUE, COUNT, TIMER, BLANK
from tests.test_starglider2_palette_priority import rng

OBJ, FREE, COUNTER = 0x85000, 0x84000, 0x37898
APP_NAMES = ['selected_celestial_body_index','inside_structure_flag','last_player_contact_type',
    'free_object_count','free_object_stack_cursor','player_world_x','player_world_y','player_world_z',
    'icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength','pending_transient_event_sound',
    'horizontal_world_wrap_mask','shared_random_state_a','shared_random_state_b']
GLOBALS = ['event_message_pointers','object_name_pointers','player_rotation2_spin_steps','SG2_ROTATION2_SPIN_START_STEPS',
    'update_nearby_falling_type47',
    'SG2ObjectCore_world_x','SG2ObjectCore_world_y','SG2ObjectCore_world_z',
    'SG2WorldObject_velocity_x','SG2WorldObject_velocity_y','SG2WorldObject_velocity_z',
    'SG2ObjectCore_retirement_phase_or_negative','SG2ObjectCore_vertex_variant_selector',
    'SG2ObjectCore_durability_or_negative','SG2ObjectCore_model_scale_shift']


@pytest.fixture(scope='module')
def fields(tmp_path_factory, original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder=tmp_path_factory.mktemp('planet-hazards');asm,out=folder/'map.s',folder/'map.raw'
    names=APP_NAMES+GLOBALS
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    r=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
    raw=out.read_bytes();tail=4*len(names);assert raw[:-tail]==original_image[0]
    result={name:value+(APP if name in APP_NAMES else 0)
        for name,value in zip(names,struct.unpack('>'+'I'*len(names),raw[-tail:]))}
    # The selection routine subtracts the established celestial type base128.
    # Keep the human names tied to original directory entries, not game lore.
    for body,text in [(1,b'Dante -'),(8,b'Broadway-')]:
        address=struct.unpack_from('>I',raw,result['object_name_pointers']-0x1000+4*(128+body))[0]
        assert raw[address-0x1000:address-0x1000+len(text)]==text
    return result


def set_rng(m,f,a,b):
    put(m,f['shared_random_state_a'],a);put(m,f['shared_random_state_b'],b)


def assert_rng(m,f,pair):
    assert tuple(get(m,f[n])for n in ['shared_random_state_a','shared_random_state_b'])==pair


@pytest.mark.parametrize('body',[0,1,8,9,65535])
@pytest.mark.parametrize('inside',[0,1,127,128,255])
@pytest.mark.parametrize('contact',[0,20,21])
@pytest.mark.parametrize('seeds',[(0,0),(0,0xFFF9)])
def test_broadway_uses_sign_gate_then_random_or_exact_contact(original_image,memory,fields,body,inside,contact,seeds):
    m,f=memory,fields
    put(m,f['selected_celestial_body_index'],body,2);m[f['inside_structure_flag']]=inside
    put(m,f['last_player_contact_type'],contact,2);set_rng(m,f,*seeds)
    m[f['pending_transient_event_sound']]=0;put(m,f['player_rotation2_spin_steps'],0x1234,2)
    put(m,COUNT,1,2);put(m,TIMER,33,2);put(m,QUEUE,0x876543)
    cpu=state(m,0x33C4C);run(original_image,m,cpu,{0x33C9A})
    gated=body==8 and inside<128
    next_rng=rng(*seeds)if gated else seeds
    active=gated and (not(next_rng[1]&2047)or contact==20)
    assert_rng(m,f,next_rng)
    assert m[f['pending_transient_event_sound']]==(255 if active else 0)
    assert get(m,f['player_rotation2_spin_steps'],2)==(f['SG2_ROTATION2_SPIN_START_STEPS']if active else 0x1234)
    if active:
        # Empty-queue insertion adds its own spacer and resets the timer;
        # the following call also enqueues the distinct message-35 pointer.
        assert get(m,COUNT,2)==3 and get(m,TIMER,2)==0
        assert [get(m,QUEUE+4*i)for i in range(3)]==[get(m,f['event_message_pointers']+56*4),
            BLANK,get(m,f['event_message_pointers']+35*4)]
    else:
        assert get(m,COUNT,2)==1 and get(m,TIMER,2)==33 and get(m,QUEUE)==0x876543


@pytest.mark.parametrize('body',[0,1,8])
@pytest.mark.parametrize('free',[0,10,11,65535])
@pytest.mark.parametrize('phase',[0,1,2,3,32768,65535])
@pytest.mark.parametrize('seeds',[(0,0),(0,0xFFF9)])
def test_dante_counter_only_advances_after_body_and_unsigned_free_gates(original_image,memory,fields,body,free,phase,seeds):
    m,f=memory,fields;put(m,f['selected_celestial_body_index'],body,2)
    put(m,f['free_object_count'],free,2);put(m,COUNTER,phase,2);set_rng(m,f,*seeds)
    cpu=state(m,0x33C9A);run(original_image,m,cpu,{0x33CCC,0x33DD0})
    gated=body==1 and free>10;next_phase=(phase+1)&3 if gated else phase
    sampled=gated and next_phase==0;next_rng=rng(*seeds)if sampled else seeds
    assert get(m,COUNTER,2)==next_phase and get(m,f['free_object_count'],2)==free
    assert_rng(m,f,next_rng)
    assert cpu.pc==(0x33CCC if sampled and not(next_rng[1]&3)else 0x33DD0)


@pytest.mark.parametrize('seeds',[(0,0),(0,0xFFF9),(0xFFFFFFFF,0x12345678),(0x95901143,0x28731549)])
@pytest.mark.parametrize('origin',[(0,0),(0x7FFFFFFF,0x80000000),(0xFFFFFFFF,12345)])
def test_dante_spawn_consumes_two_more_random_values_and_retains_velocity(original_image,memory,fields,seeds,origin):
    m,f=memory,fields;set_rng(m,f,*seeds)
    for name,value in zip(['player_world_x','player_world_z'],origin):put(m,f[name],value)
    put(m,f['free_object_count'],11,2);put(m,f['free_object_stack_cursor'],FREE+4);put(m,FREE,OBJ)
    m[OBJ:OBJ+68]=b'\x5A'*68;expected=bytearray(m[OBJ:OBJ+68])
    first=rng(*seeds);second=rng(*first)
    dx=(second[1]&8191)-4096;dz=(first[1]&8191)-4096
    expected[0:2]=(47).to_bytes(2,'big')
    for field,value in [('world_x',(origin[0]+dx)&0xFFFFFFFF),('world_y',0xFFFFFFEC),('world_z',(origin[1]+dz)&0xFFFFFFFF)]:
        off=f['SG2ObjectCore_'+field];expected[off:off+4]=value.to_bytes(4,'big')
    for field,value in [('retirement_phase_or_negative',2),('vertex_variant_selector',0),('durability_or_negative',0),('model_scale_shift',5)]:
        expected[f['SG2ObjectCore_'+field]]=value
    cpu=state(m,0x33CCC);run(original_image,m,cpu,{0x33D2C})
    assert bytes(m[OBJ:OBJ+68])==bytes(expected)
    assert_rng(m,f,second)
    assert cpu.a[4]==OBJ and get(m,f['free_object_stack_cursor'])==FREE and get(m,f['free_object_count'],2)==10


@pytest.mark.parametrize('delta',[(-4096,-4096),(-4096,4095),(-1,1),(0,0),(1,0),(4095,4095)])
@pytest.mark.parametrize('origin',[(0,0),(0x7FFFFFFF,0x80000000)])
@pytest.mark.parametrize('y',[-501,-500,-499,2147483647,-2147483648])
@pytest.mark.parametrize('reserve',[0,65530,65535])
def test_dante_recharge_uses_low_word_distance_and_independent_saturation(original_image,memory,fields,delta,origin,y,reserve):
    m,f=memory,fields
    for name,value in zip(['player_world_x','player_world_z'],origin):put(m,f[name],value)
    put(m,f['player_world_y'],y&0xFFFFFFFF)
    for field,value,d in zip(['world_x','world_z'],origin,delta):put(m,OBJ+f['SG2ObjectCore_'+field],(value+d)&0xFFFFFFFF)
    for name in ['icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength']:put(m,f[name],reserve,2)
    m[f['pending_transient_event_sound']]=0
    cpu=state(m,0x33D2C);cpu.a[4]=OBJ;run(original_image,m,cpu,{0x33DD0})
    gated=not((y+500)&0x80000000)
    x,z=map(abs,delta);distance=3*max(x,z)+min(x,z)
    reward=((8192-(distance>>1))&65535)>>5
    expected=min(65535,reserve+reward)if gated else reserve
    assert [get(m,f[n],2)for n in ['icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength']]==[expected]*3
    assert m[f['pending_transient_event_sound']]==(255 if gated and reward>=32 else 0)


@pytest.mark.parametrize('y',[-121,-120,-119,0,-2147483648,2147483647])
@pytest.mark.parametrize('velocity',[-32768,-1,0,1,32767])
def test_type47_vertical_gate_precedes_horizontal_wrap_and_gravity(original_image,memory,fields,y,velocity):
    m,f=memory,fields;m[OBJ:OBJ+68]=b'\x5A'*68
    for field,value in [('world_x',2),('world_y',y&0xFFFFFFFF),('world_z',0xFFFFFFFF)]:put(m,OBJ+f['SG2ObjectCore_'+field],value)
    for field,value in [('velocity_x',-3),('velocity_y',velocity),('velocity_z',2)]:put(m,OBJ+f['SG2WorldObject_'+field],value&65535,2)
    phase=OBJ+f['SG2ObjectCore_retirement_phase_or_negative'];m[phase]=2
    put(m,f['horizontal_world_wrap_mask'],0x1FFFF)
    cpu=state(m,f['update_nearby_falling_type47']);cpu.a[0]=OBJ;run(original_image,m,cpu,{0x39D56})
    next_y=(y+velocity)&0xFFFFFFFF;active=bool((next_y+120)&0x80000000)
    assert get(m,OBJ+f['SG2ObjectCore_world_y'])==next_y
    assert m[phase]==(2 if active else 0)
    assert get(m,OBJ+f['SG2ObjectCore_world_x'])==(0x1FFFF if active else 2)
    assert get(m,OBJ+f['SG2ObjectCore_world_z'])==(1 if active else 0xFFFFFFFF)
    assert get(m,OBJ+f['SG2WorldObject_velocity_y'],2)==((velocity+8)&65535 if active else velocity&65535)
