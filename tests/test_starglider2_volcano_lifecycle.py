"""Original volcano producers and common retirement with explicit RAM contexts.

These are bounded CPU windows, not normal-play, unique list membership, object
lifetime, palette scanout, sound delivery or caller-capacity guarantees.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_planet_hazards import (
    APP_NAMES, GLOBALS, OBJ, FREE, COUNTER, original_image, memory, state, run,
    put, get, APP, set_rng, assert_rng,
)
from tests.test_starglider2_text_editor import RETURN
from tests.test_starglider2_palette_priority import rng

PARENT, LIST = 0x85200, 0x84100
FACES = [0x28342 + 10*i for i in range(6)]
EXTRA_APP = ['world_object_update_enabled_flag','nearby_object_count',
    'nearby_objects_cursor','distant_object_count','distant_objects_cursor',
    'panel_fast_animation_request']
EXTRA_GLOBAL = ['object_retirement_phase_limits','update_world_objects',
    'update_nearby_volcano','volcano_refill_updates_or_negative',
    'SG2Volcano_face_colour_pair_index','SG2Volcano_eruption_colour_countdown_or_negative',
    'SG2Volcano_eruption_attempt_mod4_index','world_reference_y_coordinates']


@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder=tmp_path_factory.mktemp('volcano-lifecycle');asm,out=folder/'map.s',folder/'map.raw'
    apps=APP_NAMES+EXTRA_APP;names=apps+GLOBALS+EXTRA_GLOBAL
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    r=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
    raw=out.read_bytes();tail=4*len(names);assert raw[:-tail]==original_image[0]
    return {name:value+(APP if name in apps else 0)
        for name,value in zip(names,struct.unpack('>'+'I'*len(names),raw[-tail:]))}


def object_lists(m,f,kind):
    m[f['world_object_update_enabled_flag']]=255
    for i,name in enumerate(['nearby','distant']):
        put(m,f[name+'_object_count'],int(kind==name or kind=='both'),2)
        put(m,f[name+'_objects_cursor'],LIST+4*i)
        put(m,LIST+4*i,OBJ)


@pytest.mark.parametrize('kind',['nearby','distant','both'])
@pytest.mark.parametrize('old',[0,0x5A,255])
def test_dante_positive_phase_reaches_retirement_before_motion(original_image,memory,fields,kind,old):
    m,f=memory,fields;m[OBJ:OBJ+68]=bytes([old])*68
    put(m,f['selected_celestial_body_index'],1,2);put(m,f['player_world_y'],(-1000)&0xFFFFFFFF)
    put(m,f['free_object_count'],11,2);put(m,f['free_object_stack_cursor'],FREE+4);put(m,FREE,OBJ)
    put(m,COUNTER,3,2);set_rng(m,f,0,0xFFF9)
    cpu=state(m,0x33C4C);run(original_image,m,cpu,{0x33DD0})
    phase=f['SG2ObjectCore_retirement_phase_or_negative']
    assert get(m,OBJ,2)==47 and m[OBJ+phase]==2 and get(m,f['free_object_count'],2)==10
    assert m[f['object_retirement_phase_limits']+47]==10
    before=bytes(m[OBJ:OBJ+68]);object_lists(m,f,kind)
    increments=2 if kind=='both'else 1
    for call in range(8//increments):
        seen=[];cpu=state(m,f['update_world_objects']);run(original_image,m,cpu,{RETURN},seen.append)
        expected=bytearray(before);expected[phase]=2+increments*(call+1)
        assert bytes(m[OBJ:OBJ+68])==expected
        assert f['update_nearby_falling_type47']not in seen
        assert get(m,f['free_object_count'],2)==10
    cpu=state(m,f['update_world_objects']);run(original_image,m,cpu,{RETURN})
    expected=bytearray(68)
    if kind=='nearby':expected[phase]=255
    assert bytes(m[OBJ:OBJ+68])==expected
    # Deliberate alias in both lists duplicates the free pointer; this is a
    # supplied invalid-membership counterexample, not normal-game reachability.
    released=2 if kind=='both'else 1
    assert get(m,f['free_object_count'],2)==10+released
    assert get(m,f['free_object_stack_cursor'])==FREE+4*released
    assert [get(m,FREE+4*i)for i in range(released)]==[OBJ]*released


@pytest.mark.parametrize('initial',[0,1,2,32768,65535])
@pytest.mark.parametrize('countdown',[0,1,2,127,128,129,255])
def test_six_colour_pairs_use_masked_phase_and_subtract_result_sign(original_image,memory,fields,initial,countdown):
    m,f=memory,fields;cpu=state(m,f['update_nearby_volcano']);cpu.a[0]=PARENT
    index=f['SG2Volcano_face_colour_pair_index'];timer=f['SG2Volcano_eruption_colour_countdown_or_negative']
    put(m,PARENT+index,initial,2);m[PARENT+timer]=countdown
    before=[bytes(m[face:face+10])for face in FACES]
    phase=(initial+1)&1;next_timer=(countdown-1)&255;bank=0x3998A if next_timer<128 else 0x3997E
    values=[get(m,bank+2*i+phase,1)for i in range(6)]
    run(original_image,m,cpu,{0x36BE0})
    assert get(m,PARENT+index,2)==phase and m[PARENT+timer]==(next_timer if next_timer<128 else 255)
    for face,old,colour in zip(FACES,before,values):
        expected=bytearray(old);expected[1]=colour
        assert bytes(m[face:face+10])==expected


@pytest.mark.parametrize('timer',[0,1,2,127,128,129,255])
@pytest.mark.parametrize('reserves',[(0,0,0),(65407,65471,65472),(65408,65535,65534),(65535,65535,65535)])
@pytest.mark.parametrize('y',[0,0x80000000])
def test_refill_counter_is_one_byte_and_reserves_saturate_independently(original_image,memory,fields,timer,reserves,y):
    m,f=memory,fields;address=f['volcano_refill_updates_or_negative'];m[address:address+2]=bytes([timer,0x5A])
    m[f['panel_fast_animation_request']]=0;put(m,f['player_world_y'],y)
    names=['icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength']
    for name,value in zip(names,reserves):put(m,f[name],value,2)
    cpu=state(m,0x36BE0);run(original_image,m,cpu,{0x36C54})
    remaining=(timer-1)&255;active=remaining<128
    assert bytes(m[address:address+2])==bytes([remaining if active else 255,0x5A])
    assert get(m,f['player_world_y'])==((y-5)&0xFFFFFFFF if active else y)
    assert m[f['panel_fast_animation_request']]==(255 if active else 0)
    assert [get(m,f[name],2)for name in names]==[
        min(65535,value+step)if active else value for value,step in zip(reserves,[128,64,64])]


@pytest.mark.parametrize('phase',[0,1,2,3,32768,65535])
@pytest.mark.parametrize('free',[0,10,11,65535])
@pytest.mark.parametrize('seeds',[(0,0),(0,0xFFF9)])
def test_eruption_advances_mod4_before_random_then_unsigned_free_gate(original_image,memory,fields,phase,free,seeds):
    m,f=memory,fields;cpu=state(m,0x36C54);cpu.a[0]=PARENT
    put(m,PARENT+f['SG2Volcano_eruption_attempt_mod4_index'],phase,2)
    put(m,f['free_object_count'],free,2);set_rng(m,f,*seeds)
    run(original_image,m,cpu,{0x36C78,0x36D14})
    sampled=((phase+1)&3)==0;next_rng=rng(*seeds)if sampled else seeds
    assert get(m,PARENT+f['SG2Volcano_eruption_attempt_mod4_index'],2)==(phase+1)&3
    assert_rng(m,f,next_rng)
    active=sampled and next_rng[1]&7==0 and free>10
    assert cpu.pc==(0x36C78 if active else 0x36D14)
    assert get(m,f['free_object_count'],2)==free


@pytest.mark.parametrize('scale',[0,1,15,31,32,63,64,255])
@pytest.mark.parametrize('old',[0,0x5A,255])
@pytest.mark.parametrize('kind',['nearby','distant'])
def test_complete_eruption_constructor_supplies_negative_phase_and_velocity(original_image,memory,fields,scale,old,kind):
    m,f=memory,fields;m[PARENT:PARENT+68]=b'\x33'*68;m[OBJ:OBJ+68]=bytes([old])*68
    put(m,PARENT+f['SG2Volcano_eruption_attempt_mod4_index'],3,2)
    for axis,value in [('x',0x7FFFFFFF),('z',0xFFFFFFFF)]:put(m,PARENT+f['SG2ObjectCore_world_'+axis],value)
    m[PARENT+f['SG2ObjectCore_model_scale_shift']]=scale
    put(m,f['free_object_count'],11,2);put(m,f['free_object_stack_cursor'],FREE+4);put(m,FREE,OBJ)
    set_rng(m,f,0,0xFFF9);values=[];pair=(0,0xFFF9)
    for _ in range(5):pair=rng(*pair);values.append(pair[1])
    assert values[0]&7==0
    expected=bytearray(m[OBJ:OBJ+68]);expected[:2]=(47).to_bytes(2,'big');expected[42]=88
    for axis,value in [('x',0x7FFFFFFF),('z',0xFFFFFFFF),('y',(-17000>>(scale&63))&0xFFFFFFFF)]:
        off=f['SG2ObjectCore_world_'+axis];expected[off:off+4]=value.to_bytes(4,'big')
    for field,value in [('retirement_phase_or_negative',255),('vertex_variant_selector',0),
        ('durability_or_negative',old|128),('model_scale_shift',6+(values[1]&1))]:
        expected[f['SG2ObjectCore_'+field]]=value
    for axis,value in [('x',[32,-25,15,-17,15,-30,30,-25][(values[2]&14)//2]),
        ('z',[-25,-35,15,12,-15,-26,18,31][(values[3]&14)//2]),('y',-100-(values[4]&31))]:
        off=f['SG2WorldObject_velocity_'+axis];expected[off:off+2]=(value&65535).to_bytes(2,'big')
    cpu=state(m,0x36C54);cpu.a[0]=PARENT;run(original_image,m,cpu,{0x36D14})
    assert bytes(m[OBJ:OBJ+68])==expected and m[PARENT+42]==47
    assert m[PARENT+f['SG2Volcano_eruption_colour_countdown_or_negative']]==3
    assert get(m,f['free_object_count'],2)==10 and get(m,f['free_object_stack_cursor'])==FREE
    assert_rng(m,f,pair)
    # Follow the produced record through the real common dispatcher. Flags at
    # BYTE+2 are retained by construction: they can alter/suppress its motion.
    # We supply explicit list membership, not a universal constructor contract.
    object_lists(m,f,kind);put(m,f['horizontal_world_wrap_mask'],0x1FFFF)
    y=get(m,OBJ+f['SG2ObjectCore_world_y']);flags=old
    if kind=='nearby':
        if flags&4:y=(y-18)&0xFFFFFFFF;flags=(flags&~4)|8
        elif flags&8:y=(y+18)&0xFFFFFFFF;flags&=~8
        expected[2]=flags
        if flags<128:
            vy=int.from_bytes(expected[f['SG2WorldObject_velocity_y']:f['SG2WorldObject_velocity_y']+2],'big',signed=True)
            y=(y+vy)&0xFFFFFFFF;active=bool((y+120)&0x80000000)
            if active:
                for axis in 'xz':
                    off=f['SG2ObjectCore_world_'+axis];v=f['SG2WorldObject_velocity_'+axis]
                    velocity=int.from_bytes(expected[v:v+2],'big',signed=True)
                    value=(int.from_bytes(expected[off:off+4],'big')+velocity)&0x1FFFF
                    expected[off:off+4]=value.to_bytes(4,'big')
                off=f['SG2WorldObject_velocity_y'];expected[off:off+2]=((vy+8)&65535).to_bytes(2,'big')
            else:expected[f['SG2ObjectCore_retirement_phase_or_negative']]=0
        off=f['SG2ObjectCore_world_y'];expected[off:off+4]=y.to_bytes(4,'big')
    elif flags<128:expected[f['SG2ObjectCore_retirement_phase_or_negative']]=9
    seen=[];cpu=state(m,f['update_world_objects']);run(original_image,m,cpu,{RETURN},seen.append)
    assert bytes(m[OBJ:OBJ+68])==expected
    assert (f['update_nearby_falling_type47']in seen)==(kind=='nearby'and flags<128)
    assert get(m,f['free_object_count'],2)==10
    assert_rng(m,f,pair)


@pytest.mark.parametrize('delta',[(0,0),(199,-199),(200,0),(-200,0),(0x80000000,0),(0x80000001,0)])
@pytest.mark.parametrize('y',[0,1023,1024,0x80000000,0xFFFFFFFF])
@pytest.mark.parametrize('seeds',[(0,0),(0,0xFFF9)])
def test_proximity_reloads_low_byte_from_wrapped_relative_height(original_image,memory,fields,delta,y,seeds):
    m,f=memory,fields;cpu=state(m,0x36D14);cpu.a[0]=PARENT
    for axis,value in zip('xz',delta):
        put(m,f['player_world_'+axis],value&0xFFFFFFFF);put(m,PARENT+f['SG2ObjectCore_world_'+axis],0)
    put(m,f['player_world_y'],y);m[f['pending_transient_event_sound']]=0
    address=f['volcano_refill_updates_or_negative'];m[address:address+2]=b'\x4D\x5A';set_rng(m,f,*seeds)
    magnitudes=[(-v)&0xFFFFFFFF if v&0x80000000 else v for v in delta]
    near=all((value-200)&0x80000000 for value in magnitudes)
    next_rng=rng(*seeds)if near else seeds;active=near and not(next_rng[1]&15)
    reference=get(m,f['world_reference_y_coordinates']+4)
    expected=(((y-reference)&0xFFFFFFFF)>>10)&255 if active else 0x4D
    run(original_image,m,cpu,{0x36D66})
    assert bytes(m[address:address+2])==bytes([expected,0x5A])
    assert m[f['pending_transient_event_sound']]==(255 if active else 0)
    assert_rng(m,f,next_rng)
