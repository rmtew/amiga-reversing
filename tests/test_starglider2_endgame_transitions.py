"""Original main-tail and game-over windows in explicit RAM contexts.

These are local CPU cases, not normal-game reachability, valid loaded-player,
allocation separation, UI, audio or hardware-cadence guarantees.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP

from tests.test_starglider2_palette_priority import rng

OBJ,FREE,STACK_CURSOR=0x85000,0x85100,0x84004
APP_FIELDS=['icarus_game_over_reason','novella_answer_tail_latch','novella_expected_char_latch',
    'icarus_shield_strength','icarus_power_reserve','weapon_energy_reserve','frame_handoff_counter',
    'player_speed_target','stardrive_enabled_word','inside_structure_flag','debug_features_enabled_flag',
    'player_world_x','player_world_y','player_world_z','player_rotation_0','player_rotation_1','player_rotation_2',
    'view_mode','view_offset_distance','view_rotation_offset_0','view_rotation_offset_1',
    'free_object_count','free_object_stack_cursor','player_motion_x','player_motion_y','player_motion_z',
    'shared_random_state_a','shared_random_state_b','pending_transient_event_sound','docking_service_phase','last_player_contact_type']
GLOBAL_FIELDS=['fatal_overheat_latched_flag','begin_postgame_screen_smear','gameplay_frame_loop',
    'game_over_sequence_countdown','player_ejection_active_flag']
CONSTANTS=['SG2_OBJECT_TYPE_ICARUS','SG2_OBJECT_TYPE_ICARUS_PILOT_COUCH',
    'SG2ObjectCore_durability_or_negative','SG2ObjectCore_vertex_variant_selector',
    'SG2ObjectCore_retirement_phase_or_negative','SG2ObjectCore_model_scale_shift',
    'SG2TargetingObject_collision_ignored_object_type','SG2WorldObject_velocity_y']


@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names=APP_FIELDS+GLOBAL_FIELDS+CONSTANTS
    folder=tmp_path_factory.mktemp('endgame');asm,out=folder/'map.s',folder/'map.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    r=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
    raw=out.read_bytes();assert raw[:-4*len(names)]==original_image[0]
    return {n:v+(APP if n in APP_FIELDS else 0)for n,v in zip(names,struct.unpack('>'+str(len(names))+'I',raw[-4*len(names):]))}


@pytest.mark.parametrize('gate',range(256))
@pytest.mark.parametrize('fatal',[0,0x80])
def test_fatal_sign_precedes_pool_rebuild_and_game_over_checks(original_image,memory,fields,gate,fatal):
    memory[APP+0x7ee]=gate;memory[fields['fatal_overheat_latched_flag']]=fatal
    put(memory,fields['icarus_game_over_reason'],1,2)
    cpu=state(memory,0x13D0)
    run(original_image,memory,cpu,{fields['begin_postgame_screen_smear'],0x123E,0x1560})
    assert cpu.pc==(fields['begin_postgame_screen_smear']if fatal&128 else 0x123E if gate else 0x1560)
    assert memory[APP+0x7ee]==gate


@pytest.mark.parametrize('fatal',[0,1,127])
@pytest.mark.parametrize('reason,tail,expected',[(0,0,0x140C),(1,0,0x1560),(65535,0,0x1560),(0,1,0x1560),(0,255,0x1560)])
def test_nonnegative_fatal_bytes_and_zero_pool_gate_retain_later_guards(original_image,memory,fields,fatal,reason,tail,expected):
    memory[fields['fatal_overheat_latched_flag']]=fatal;memory[APP+0x7ee]=0
    put(memory,fields['icarus_game_over_reason'],reason,2);memory[fields['novella_answer_tail_latch']]=tail
    put(memory,fields['icarus_shield_strength'],12000,2)
    cpu=state(memory,0x13D0);run(original_image,memory,cpu,{0x123E,0x1560,0x140C})
    assert cpu.pc==expected


@pytest.mark.parametrize('power',[0,1,2,100,1000,65535])
@pytest.mark.parametrize('speed',[0,63,64,65,32768,65535])
@pytest.mark.parametrize('boost',[0,1,0x8000,65535])
def test_power_debit_uses_unsigned_words_and_threefold_boost_cost(original_image,memory,fields,power,speed,boost):
    put(memory,fields['icarus_power_reserve'],power,2);put(memory,fields['player_speed_target'],speed,2)
    put(memory,fields['stardrive_enabled_word'],boost,2);memory[fields['inside_structure_flag']]=1
    put(memory,fields['icarus_game_over_reason'],0x55,2)
    cpu=state(memory,0x144C);run(original_image,memory,cpu,{fields['gameplay_frame_loop']})
    debit=(speed>>6)*(3 if boost else 1)
    assert get(memory,fields['icarus_power_reserve'],2)==max(0,power-debit)
    assert get(memory,fields['icarus_game_over_reason'],2)==(1 if power<debit else 0x55)


def setup_pose(memory,fields,countdown):
    memory[OBJ:OBJ+68]=b'\x35'*68
    put(memory,fields['game_over_sequence_countdown'],countdown,2)
    memory[fields['player_ejection_active_flag']]=0
    for n,v in [('view_offset_distance',0xfff0),('view_rotation_offset_0',0x1234),('view_rotation_offset_1',0xff8),
                ('player_rotation_0',0x123),('player_rotation_1',0xff0),('player_rotation_2',0xabc)]:put(memory,fields[n],v,2)
    for i,n in enumerate(['player_world_x','player_world_y','player_world_z']):put(memory,fields[n],1000+i*1000)
    put(memory,fields['shared_random_state_a'],0);put(memory,fields['shared_random_state_b'],0)
    put(memory,fields['free_object_count'],0,2)
    cpu=state(memory,0x157A);cpu.a[0]=OBJ
    return cpu


@pytest.mark.parametrize('mode',[0,3,4,7,127,131,132,255])
def test_countdown200_view_test_keeps_subtraction_sign_overflow_aliases(original_image,memory,fields,mode):
    cpu=setup_pose(memory,fields,200);memory[fields['view_mode']]=mode
    run(original_image,memory,cpu,{fields['gameplay_frame_loop'],0x16B0})
    captured=bool((mode-4)&0x80)
    assert memory[fields['view_mode']]==(7 if captured else mode)
    assert get(memory,fields['view_offset_distance'],2)==(530 if captured else 14)
    assert get(memory,fields['view_rotation_offset_0'],2)==(0 if captured else 0x1234)
    assert get(memory,fields['view_rotation_offset_1'],2)==(((rng(0,0)[1]+32)&4095)if captured else 24)
    assert get(memory,fields['game_over_sequence_countdown'],2)==199


@pytest.mark.parametrize('countdown',[0,1,2,179,181,199,201,32768,32769,65535])
def test_orbit_pose_copy_and_countdown_keep_word_wrap(original_image,memory,fields,countdown):
    cpu=setup_pose(memory,fields,countdown);memory[fields['view_mode']]=5
    run(original_image,memory,cpu,{fields['gameplay_frame_loop'],0x16B0})
    after=(countdown-1)&65535
    assert cpu.pc==(0x16B0 if after&32768 else fields['gameplay_frame_loop'])
    assert get(memory,fields['game_over_sequence_countdown'],2)==after
    assert [get(memory,OBJ+o)for o in [4,8,12]]==[1000,2000,3000]
    assert [get(memory,OBJ+o,2)for o in [16,18,20]]==[0x123,0xff0,0xabc]
    assert get(memory,fields['view_rotation_offset_1'],2)==24
    assert get(memory,fields['view_offset_distance'],2)==14


@pytest.mark.parametrize('count',[0,1,2,3,65535])
@pytest.mark.parametrize('alias',[False,True])
def test_countdown180_partial_couch_initialization_and_unchecked_alias(original_image,memory,fields,count,alias):
    cpu=setup_pose(memory,fields,180);new=OBJ if alias else FREE
    if not alias:memory[new:new+68]=b'\x35'*68
    for i,o in enumerate([4,8,12]):put(memory,OBJ+o,100+i*100)
    put(memory,fields['free_object_count'],count,2);put(memory,fields['free_object_stack_cursor'],STACK_CURSOR)
    put(memory,STACK_CURSOR-4,new)
    for n in ['player_speed_target','player_motion_x','player_motion_y','player_motion_z']:put(memory,fields[n],0x1234,2)
    before=bytes(memory[new:new+68]);run(original_image,memory,cpu,{fields['gameplay_frame_loop']})
    assert memory[fields['player_ejection_active_flag']]==255
    assert all(get(memory,fields[n],2)==0 for n in ['player_speed_target','player_motion_x','player_motion_y','player_motion_z'])
    assert get(memory,fields['free_object_count'],2)==(count-1 if count>1 else count)
    assert get(memory,fields['free_object_stack_cursor'])==(STACK_CURSOR-4 if count>1 else STACK_CURSOR)
    if count<=1:
        if not alias:assert bytes(memory[new:new+68])==before
        assert memory[OBJ+0x2a]==0x35
    else:
        expected=bytearray(before)
        def write(offset,value,width=1):expected[offset:offset+width]=value.to_bytes(width,'big')
        write(0,fields['SG2_OBJECT_TYPE_ICARUS_PILOT_COUCH'],2)
        for i,o in enumerate([4,8,12]):write(o,(1000+i*1000)if alias else(100+i*100),4)
        write(fields['SG2WorldObject_velocity_y'],0,2)
        write(fields['SG2ObjectCore_retirement_phase_or_negative'],255)
        write(fields['SG2ObjectCore_durability_or_negative'],0x80 if alias else 0xb5)
        write(fields['SG2ObjectCore_vertex_variant_selector'],0)
        write(fields['SG2ObjectCore_model_scale_shift'],6)
        write(fields['SG2TargetingObject_collision_ignored_object_type'],0x47 if alias else fields['SG2_OBJECT_TYPE_ICARUS'])
        for o,v in zip([16,18,20],[0x123,0xff0,0xabc]if alias else[0,0x7f0,0]):write(o,v,2)
        if alias:write(2,0x31)
        assert bytes(memory[new:new+68])==bytes(expected)
        assert memory[OBJ+0x2a]==0x47
    assert [get(memory,OBJ+o)for o in [4,8,12]]==[1000,2000,3000]


@pytest.mark.parametrize('shield',[0,1])
@pytest.mark.parametrize('phase',[0,1])
@pytest.mark.parametrize('contact',[0,2])
@pytest.mark.parametrize('debug',[0,1,255])
def test_debug_refill_follows_zero_shield_and_contact_gates(original_image,memory,fields,shield,phase,contact,debug):
    put(memory,fields['icarus_shield_strength'],shield,2);put(memory,fields['docking_service_phase'],phase,2)
    put(memory,fields['last_player_contact_type'],contact,2);memory[fields['debug_features_enabled_flag']]=debug
    put(memory,fields['icarus_power_reserve'],100,2);put(memory,fields['weapon_energy_reserve'],300,2)
    cpu=state(memory,0x141E);run(original_image,memory,cpu,{0x1502,0x14B6,0x144C})
    expected=0x1502 if not shield else 0x14B6 if not phase and contact else 0x144C
    assert cpu.pc==expected
    refill=expected==0x144C and debug
    assert [get(memory,fields[n],2)for n in ['icarus_power_reserve','icarus_shield_strength','weapon_energy_reserve']]==([22000,40000,30000]if refill else[100,shield,300])
