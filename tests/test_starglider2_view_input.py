"""Original keyboard-to-view controls and real message/point-field helpers.

Supplied key flags and player/app state qualify local behavior, not normal-game
reachability, keyboard delivery, frame cadence or arbitrary mode/pointer safety.
"""
import struct
import subprocess
from pathlib import Path

import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,STACK,RETURN
from tests.test_starglider2_control_normalization import signed
from tests.test_starglider2_palette_priority import rng

KEYS,QUEUE,MODE_CACHE,DIRECTION_CACHE=0xDE8C,0xE084,0x2F6A,0x2F6C
DIRECTION_TABLE,MODE_TABLE=0x2DF4,0x2EB4
PRESETS={0x3E:0,0x3F:0xE00,0x2F:0xC00,0x1F:0xA00,0x1E:0x800,0x1D:0x600,0x2D:0x400,0x3D:0x200}
NAMES=['pending_key_scancode','view_mode','view_offset_distance','view_rotation_offset_0','view_rotation_offset_1',
 'inside_structure_flag','pending_message_count','message_display_countdown','shared_random_state_a','shared_random_state_b',
 'point_field_world_positions','point_field_previous_view_positions','player_world_x','player_world_y','player_world_z',
 'player_object_reference','world_object_pool','world_object_slot_count','horizontal_world_wrap_mask',
 'view_rotation_0','view_rotation_1','view_rotation_2','sine_lookup_pointer','cosine_lookup_pointer']


@pytest.fixture(scope='module')
def fields(tmp_path_factory):
    root=Path(__file__).resolve().parents[1];target=root/'targets/amiga_raw_starglider2_game'
    temp=tmp_path_factory.mktemp('view-input-fields');asm=temp/'fields.s';output=temp/'fields.bin'
    prefix=(target/'starglider2_game.s').read_text().split('    SECTION code,code',1)[0]
    asm.write_text(prefix+'\n SECTION constants,data\n dc.l '+','.join(NAMES)+'\n')
    r=subprocess.run([str(root/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-no-opt','-I'+str(target/'includes'),
                      '-o',str(output),str(asm)],cwd=target,capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
    return {key:APP+v for key,v in zip(NAMES,struct.unpack('>'+len(NAMES)*'I',output.read_bytes()))}


def word(m,p,v):put(m,p,v&65535,2)
def sector(v):return(((v+256)&65535)>>9)&7

def prepare(m,f,key=0,mode=0,distance=800,pitch=0,yaw=0,inside=0):
    m[KEYS:KEYS+128]=bytes(128);m[f['pending_key_scancode']]=key;m[f['view_mode']]=mode;m[f['inside_structure_flag']]=inside
    for name,value in [('view_offset_distance',distance),('view_rotation_offset_0',pitch),('view_rotation_offset_1',yaw),
                       ('pending_message_count',3),('message_display_countdown',9)]:word(m,f[name],value)
    word(m,MODE_CACHE,0xFFFF);word(m,DIRECTION_CACHE,0x5A5A);put(m,QUEUE-4,0)
    put(m,f['shared_random_state_a'],0x12345678);put(m,f['shared_random_state_b'],0x90ABCDEF)
    for axis,value in zip('xyz',[0x12340010,0xFFF01234,0x56789ABC]):put(m,f['player_world_'+axis],value)
    m[f['point_field_world_positions']:f['point_field_world_positions']+120]=b'\xA5'*120
    m[f['point_field_previous_view_positions']:f['point_field_previous_view_positions']+120]=b'\x5A'*120


def check_reinitialized_points(m,f,changed):
    a,b=0x12345678,0x90ABCDEF;expected=bytearray()
    if changed:
        for _ in range(20):
            for axis in 'xyz':
                a,b=rng(a,b);value=(b&16383)-8192+get(m,f['player_world_'+axis])
                expected+=(value&65535).to_bytes(2,'big')
        assert bytes(m[f['point_field_world_positions']:f['point_field_world_positions']+120])==expected
        assert bytes(m[f['point_field_previous_view_positions']:f['point_field_previous_view_positions']+120])==bytes(120)
    else:
        assert bytes(m[f['point_field_world_positions']:f['point_field_world_positions']+120])==b'\xA5'*120
    assert get(m,f['shared_random_state_a'])==a and get(m,f['shared_random_state_b'])==b


def message_pointer(image,base,index):return base+signed(int.from_bytes(image[0][base-4096+2*index:base-4096+2*index+2],'big'))
def check_message(m,f,pointer):
    assert get(m,f['pending_message_count'],2)==2 and get(m,f['message_display_countdown'],2)==0
    assert get(m,QUEUE)==pointer and get(m,QUEUE+4)==0xE0B8


@pytest.mark.parametrize('key',range(1,9))
@pytest.mark.parametrize('old_mode',[0,5])
def test_number_keys_bypass_held_controls_and_use_real_point_reset(original_image,memory,fields,key,old_mode):
    m=memory;f=fields;prepare(m,f,key,old_mode,distance=100,pitch=0x1234,yaw=0x5678)
    for code in [0x0F,0x5E,0x4A,0x4F,0x4E,0x4C,0x4D]:m[KEYS+code]=255
    cpu=state(m,0x2C20);run(original_image,m,cpu,{RETURN},limit=5000)
    assert m[f['view_mode']]==key-1 and get(m,f['view_offset_distance'],2)==800
    assert get(m,f['view_rotation_offset_0'],2)==0x1234 and get(m,f['view_rotation_offset_1'],2)==0x5678
    check_reinitialized_points(m,f,key-1!=old_mode);check_message(m,f,message_pointer(original_image,MODE_TABLE,key-1))
    assert cpu.a[6]==APP and cpu.a[7]==STACK+4


@pytest.mark.parametrize('distance',[-32768,-1,0,736,799,800,801,863,9936,9999,10000,10001,32767])
@pytest.mark.parametrize('decrease,increase',[(False,False),(True,False),(False,True),(True,True)])
def test_held_distance_keys_keep_order_and_soft_limits(original_image,memory,fields,distance,decrease,increase):
    m=memory;f=fields;prepare(m,f,distance=distance)
    m[KEYS+0x0F]=int(decrease);m[KEYS+0x4A]=int(increase)
    expected=distance
    if decrease and expected>800:expected=signed(expected-64)
    if increase and expected<=10000:expected=signed(expected+64)
    cpu=state(m,0x2C20);run(original_image,m,cpu,{RETURN})
    assert signed(get(m,f['view_offset_distance'],2))==expected
    assert get(m,f['pending_message_count'],2)==3 and get(m,f['message_display_countdown'],2)==9
    check_reinitialized_points(m,f,False)


@pytest.mark.parametrize('key,yaw',list(PRESETS.items()))
@pytest.mark.parametrize('old_pitch,old_yaw',[(0,0),(1,0),(0,2048),(65535,65535)])
def test_direction_presets_rebuild_only_on_actual_offset_change(original_image,memory,fields,key,yaw,old_pitch,old_yaw):
    m=memory;f=fields;prepare(m,f,key,pitch=old_pitch,yaw=old_yaw)
    cpu=state(m,0x2C20);run(original_image,m,cpu,{RETURN},limit=5000)
    changed=old_pitch!=0 or old_yaw!=yaw
    assert get(m,f['view_rotation_offset_0'],2)==0 and get(m,f['view_rotation_offset_1'],2)==yaw
    check_reinitialized_points(m,f,changed)
    if changed and sector(yaw)!=yaw:check_message(m,f,message_pointer(original_image,DIRECTION_TABLE,sector(yaw)))
    else:assert get(m,f['pending_message_count'],2)==3


@pytest.mark.parametrize('yaw',[0,1,255,256,511,512,2048,4095,65535])
@pytest.mark.parametrize('left,right',[(False,False),(True,False),(False,True),(True,True)])
def test_held_yaw_updates_keep_word_wrap_and_raw_angle_comparison(original_image,memory,fields,yaw,left,right):
    m=memory;f=fields;prepare(m,f,yaw=yaw)
    m[KEYS+0x4F]=int(left);m[KEYS+0x4E]=int(right);expected=yaw;last=None
    for pressed,change in [(left,-32),(right,32)]:
        if pressed:
            expected=(expected+change)&65535
            if sector(expected)!=expected:last=sector(expected)
    cpu=state(m,0x2C20);run(original_image,m,cpu,{RETURN})
    assert get(m,f['view_rotation_offset_1'],2)==expected
    if last is None:assert get(m,f['pending_message_count'],2)==3 and get(m,DIRECTION_CACHE,2)==0x5A5A
    else:
        check_message(m,f,message_pointer(original_image,DIRECTION_TABLE,last));assert get(m,DIRECTION_CACHE,2)==last
    check_reinitialized_points(m,f,False)


@pytest.mark.parametrize('yaw',[0,1,255,256,511,512,2048,4095,65535])
@pytest.mark.parametrize('inside',[0,1,128,255])
@pytest.mark.parametrize('mode',[0,4,7,128,255])
def test_direction_message_suppression_is_signed_and_keeps_raw_compare(original_image,memory,fields,yaw,inside,mode):
    m=memory;f=fields;prepare(m,f,mode=mode,yaw=yaw,inside=inside)
    cpu=state(m,0x2DA4);run(original_image,m,cpu,{RETURN})
    index=sector(yaw);changed=index!=yaw
    allowed=inside<128 or signed(mode,8)<4 or index in[0,4]
    assert get(m,DIRECTION_CACHE,2)==(index if changed else 0x5A5A)
    if changed and allowed:check_message(m,f,message_pointer(original_image,DIRECTION_TABLE,index))
    else:assert get(m,f['pending_message_count'],2)==3 and get(m,f['message_display_countdown'],2)==9


@pytest.mark.parametrize('mode',[0,4,255])
@pytest.mark.parametrize('distance',[-32768,0,799,800,801,10000])
def test_toggle_selects_outside_only_from_zero_and_retains_soft_minimum(original_image,memory,fields,mode,distance):
    m=memory;f=fields;prepare(m,f,key=0x43,mode=mode,distance=distance)
    cpu=state(m,0x2C20);run(original_image,m,cpu,{RETURN})
    selected=4 if mode==0 else 0
    assert m[f['view_mode']]==selected and get(m,f['view_offset_distance'],2)==max(800,distance)
    check_message(m,f,message_pointer(original_image,MODE_TABLE,selected));check_reinitialized_points(m,f,False)


@pytest.mark.parametrize('pitch',[0,0xFC00])
@pytest.mark.parametrize('yaw',[0,2048])
@pytest.mark.parametrize('inside,mode',[(0,0),(0,4),(128,4)])
def test_below_preset_uses_ninth_message_and_keeps_same_pitch_early_return(original_image,memory,fields,pitch,yaw,inside,mode):
    m=memory;f=fields;prepare(m,f,key=0x2E,mode=mode,pitch=pitch,yaw=yaw,inside=inside)
    cpu=state(m,0x2C20);run(original_image,m,cpu,{RETURN},limit=5000)
    changed=pitch!=0xFC00
    assert get(m,f['view_rotation_offset_0'],2)==0xFC00
    assert get(m,f['view_rotation_offset_1'],2)==(0 if changed else yaw)
    check_reinitialized_points(m,f,changed)
    assert get(m,DIRECTION_CACHE,2)==0x5A5A
    if changed and not(inside>=128 and mode>=4):check_message(m,f,message_pointer(original_image,DIRECTION_TABLE,8))
    else:assert get(m,f['pending_message_count'],2)==3


@pytest.mark.parametrize('mode',range(8))
@pytest.mark.parametrize('distance',[-1,799,800,801])
@pytest.mark.parametrize('same',[False,True])
def test_mode_message_same_cache_returns_before_distance_or_queue_changes(original_image,memory,fields,mode,distance,same):
    m=memory;f=fields;prepare(m,f,distance=distance);word(m,MODE_CACHE,mode if same else 65535)
    cpu=state(m,0x2E7C);cpu.d[0]=mode;run(original_image,m,cpu,{RETURN})
    assert signed(get(m,f['view_offset_distance'],2))==(distance if same else max(distance,800))
    if same:assert get(m,f['pending_message_count'],2)==3 and get(m,f['message_display_countdown'],2)==9
    else:check_message(m,f,message_pointer(original_image,MODE_TABLE,mode))


@pytest.mark.parametrize('pitch',[0,1,32767,65535])
@pytest.mark.parametrize('decrease,increase',[(False,False),(True,False),(False,True),(True,True)])
def test_held_pitch_keys_do_not_announce_or_rebuild_points(original_image,memory,fields,pitch,decrease,increase):
    m=memory;f=fields;prepare(m,f,pitch=pitch)
    m[KEYS+0x4C]=int(decrease);m[KEYS+0x4D]=int(increase)
    cpu=state(m,0x2C20);run(original_image,m,cpu,{RETURN})
    assert get(m,f['view_rotation_offset_0'],2)==(pitch-32*decrease+32*increase)&65535
    assert get(m,f['pending_message_count'],2)==3 and get(m,f['message_display_countdown'],2)==9
    check_reinitialized_points(m,f,False)


def test_front_key_and_real_camera_producers_do_not_exclude_supplied_root_boundary(original_image,memory,fields):
    m=memory;f=fields;prepare(m,f,key=0x3E,pitch=1024,yaw=2048)
    player=0x88400;m[player:player+68]=bytes(68);word(m,player,1);put(m,f['player_object_reference'],player)
    for off,axis,value in zip([4,8,12],'xyz',[20000000,-120,20000000]):
        put(m,player+off,value&0xFFFFFFFF);put(m,f['player_world_'+axis],value&0xFFFFFFFF)
    put(m,f['sine_lookup_pointer'],0x13F60);put(m,f['cosine_lookup_pointer'],0x14760)
    run(original_image,m,state(m,0x2C20),{RETURN},limit=5000)
    run(original_image,m,state(m,0x3C40),{RETURN},limit=1000)
    assert [get(m,f['view_rotation_'+str(i)],2)for i in range(3)]==[0,0,0]
    run(original_image,m,state(m,0x2836),{RETURN},limit=1000)
    obj=f['world_object_pool'];m[obj:obj+136]=bytes(136);word(m,obj,128)
    for off,value in zip([4,8,12],[20000001,-120,20000257]):put(m,obj+off,value&0xFFFFFFFF)
    put(m,obj+54,100);word(m,f['world_object_slot_count'],2);put(m,f['horizontal_world_wrap_mask'],0x0FFFFFFF)
    cpu=state(m,0x3F10);run(original_image,m,cpu,{0x6958},limit=5000)
    assert [get(m,obj+o,2)for o in [22,24,26]]==[0,0,256]
    assert cpu.d[0]==65536 and cpu.d[0]&65535==0  # Stop before original DIVS; no exception claim.
