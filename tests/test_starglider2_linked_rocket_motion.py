"""Original linked/free motion, rocket constructors and Buzz Bomb spawn windows.

Supplied backed records establish local arithmetic and write ordering, not normal
world-list admission, pointer lifetime, frame cadence or hardware equivalence.
"""
import struct
import subprocess
from pathlib import Path

import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,RETURN
from tests.test_starglider2_control_normalization import signed
from tests.test_starglider2_palette_priority import rng
from tests.test_starglider2_random_height_initializers import SEEDS

ACTOR,PEER,CHILD,FREE=INPUT+0x400,INPUT+0x500,INPUT+0x600,0x85000
APPS=['space_environment_flag','inside_structure_flag','horizontal_world_wrap_mask','free_object_count','free_object_stack_cursor']
LABELS=APPS+['update_link_following_or_free_motion_object','update_mini_rocket_delay_then_fall',
 'initialize_square_rocket_attitude_and_y_high_word','initialize_mini_rocket_delay_and_link',
 'try_buzz_bomber_type6_spawn','continue_primary_object_update_loop','continue_flying_phase_mask_tests_after_spawn_attempt']

@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
 target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
 folder=tmp_path_factory.mktemp('linked-rocket');source=folder/'symbols.s';output=folder/'symbols.raw'
 source.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(LABELS)+'\n')
 result=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000','-no-opt',
  '-I'+str(target/'includes'),'-o',str(output),str(source)],cwd=target,capture_output=True,text=True)
 assert result.returncode==0,result.stdout+result.stderr
 raw=output.read_bytes();tail=4*len(LABELS);assert raw[:-tail]==original_image[0]
 values=struct.unpack('>'+'I'*len(LABELS),raw[-tail:])
 return {n:v+(APP if n in APPS else 0)for n,v in zip(LABELS,values)}

def store(m,address,value,width=4):put(m,address,value&((1<<(8*width))-1),width)

def prepare(m,f,space=0,inside=0):
 m[ACTOR:ACTOR+68]=bytes([0xA5])*68;m[PEER:PEER+68]=bytes([0x5A])*68
 m[f['space_environment_flag']]=space;m[f['inside_structure_flag']]=inside
 store(m,f['horizontal_world_wrap_mask'],0x1FFFF)
 store(m,ACTOR+60,-1);m[ACTOR+30]=255
 for off,v in [(4,100),(8,-100),(12,200)]:store(m,ACTOR+off,v)
 for off,v in [(44,3),(46,-2),(48,-3)]:store(m,ACTOR+off,v,2)

def update(image,m,f,entry='update_link_following_or_free_motion_object'):
 cpu=state(m,f[entry]);cpu.a[0]=ACTOR
 run(image,m,cpu,{f['continue_primary_object_update_loop']})
 return cpu

def free_expected(record,space,inside):
 out=bytearray(record)
 for axis,velocity in [(4,44),(8,46),(12,48)]:
  value=(get(record,axis)+signed(get(record,velocity,2),16))&0xFFFFFFFF
  store(out,axis,value if axis==8 else value&0x1FFFF)
 if not space and not inside:
  if signed(get(out,8),32)>=-50:out[30]=0
  else:
   for off in [44,48]:store(out,off,signed(get(record,off,2),16)>>1,2)
   store(out,46,get(record,46,2)+2,2)
 return out

@pytest.mark.parametrize('link',[0,0xFFFFFFFF,0x80000000])
@pytest.mark.parametrize('space,inside',[(0,0),(1,0),(127,0),(128,0),(255,0),(0,255)])
@pytest.mark.parametrize('y,vy',[(-53,2),(-52,2),(-51,2),(0x7FFFFFFF,1),(0x80000000,-1),(-100,32767),(-100,-32768)])
def test_free_motion_sign_gates_word_wrap_and_phase_only_retirement(original_image,memory,fields,link,space,inside,y,vy):
 m,f=memory,fields;prepare(m,f,space,inside);store(m,ACTOR+60,link);store(m,ACTOR+8,y);store(m,ACTOR+46,vy,2)
 before=bytes(m[ACTOR:ACTOR+68]);update(original_image,m,f)
 assert bytes(m[ACTOR:ACTOR+68])==free_expected(before,space,inside)

@pytest.mark.parametrize('delta',[-2147483648,-17,-16,-15,-1,0,1,15,16,17,2147483647])
@pytest.mark.parametrize('tag,phase',[(0,128),(13,255)])
def test_positive_link_follows_phase_sign_even_without_live_tag(original_image,memory,fields,delta,tag,phase):
 m,f=memory,fields;prepare(m,f,255,255);store(m,ACTOR+60,PEER);store(m,PEER,tag,2);m[PEER+30]=phase
 for off,base in [(4,10),(8,0x80000000),(12,0xFFFFFFFF)]:
  store(m,PEER+off,base);store(m,ACTOR+off,base+delta)
 before=bytearray(m[ACTOR:ACTOR+68]);peer=bytes(m[PEER:PEER+68]);expected=bytearray(before)
 for off in [4,8,12]:store(expected,off,get(before,off)-(delta>>4))
 for off in [16,20]:store(expected,off,(get(before,off,2)+32)&4095,2)
 update(original_image,m,f)
 assert bytes(m[ACTOR:ACTOR+68])==expected and bytes(m[PEER:PEER+68])==peer

@pytest.mark.parametrize('phase',[0,1,127])
@pytest.mark.parametrize('space',[0,1,128])
def test_inactive_peer_detaches_and_zeroes_velocity_before_same_call_integration(original_image,memory,fields,phase,space):
 m,f=memory,fields;prepare(m,f,space);store(m,ACTOR+60,PEER);m[PEER+30]=phase
 before=bytearray(m[ACTOR:ACTOR+68]);peer=bytes(m[PEER:PEER+68]);store(before,60,-1)
 for off in [44,46,48]:store(before,off,0,2)
 update(original_image,m,f)
 assert bytes(m[ACTOR:ACTOR+68])==free_expected(before,space,0)and bytes(m[PEER:PEER+68])==peer

@pytest.mark.parametrize('delay',[0,1,2,31,32768,65535])
@pytest.mark.parametrize('space',[0,1,127,128,255])
@pytest.mark.parametrize('yaw,vy',[(4090,0),(65530,-32768)])
def test_mini_delay_fall_and_negative_space_delegation(original_image,memory,fields,delay,space,yaw,vy):
 m,f=memory,fields;prepare(m,f,space,255);store(m,ACTOR+36,delay,2);store(m,ACTOR+18,yaw,2);store(m,ACTOR+46,vy,2)
 before=bytearray(m[ACTOR:ACTOR+68]);expected=bytearray(before)
 if space&128:expected=free_expected(before,space,255)
 elif delay:store(expected,36,delay-1,2);store(expected,46,0,2)
 else:
  store(expected,18,yaw+16,2);store(expected,46,vy-2,2)
  store(expected,8,get(before,8)+signed((vy-2)&65535,16))
 update(original_image,m,f,'update_mini_rocket_delay_then_fall')
 assert bytes(m[ACTOR:ACTOR+68])==expected

@pytest.mark.parametrize('old_y',[0,0x12345678,0xFFFFFFFF])
@pytest.mark.parametrize('durability',[0,127,128,255])
def test_square_constructor_preserves_y_low_word_and_other_record_bytes(original_image,memory,fields,old_y,durability):
 m,f=memory,fields;prepare(m,f);m[ACTOR+28]=durability;store(m,ACTOR+8,old_y);expected=bytearray(m[ACTOR:ACTOR+68])
 store(expected,16,1024,2);store(expected,8,0xFF380000|(old_y&65535));expected[28]|=128
 cpu=state(m,f['initialize_square_rocket_attitude_and_y_high_word']);cpu.a[0]=ACTOR;run(original_image,m,cpu,{RETURN})
 assert bytes(m[ACTOR:ACTOR+68])==expected

@pytest.mark.parametrize('seed',SEEDS)
def test_mini_constructor_uses_one_real_rng_advance_and_preserves_dirty_fields(original_image,memory,fields,seed):
 m,f=memory,fields;prepare(m,f);store(m,APP+0x60,seed[0]);store(m,APP+0x64,seed[1])
 a,b=rng(*seed);value=b;expected=bytearray(m[ACTOR:ACTOR+68]);store(expected,36,value&31,2);store(expected,60,-1)
 cpu=state(m,f['initialize_mini_rocket_delay_and_link']);cpu.a[0]=ACTOR;run(original_image,m,cpu,{RETURN})
 assert bytes(m[ACTOR:ACTOR+68])==expected and (get(m,APP+0x60),get(m,APP+0x64))==(a,b)

@pytest.mark.parametrize('delay',[0,1,15,31])
def test_constructor_to_delay_and_two_fall_calls(original_image,memory,fields,delay):
 m,f=memory,fields;prepare(m,f);store(m,APP+0x60,0);store(m,APP+0x64,0xFFF9^delay)
 cpu=state(m,f['initialize_mini_rocket_delay_and_link']);cpu.a[0]=ACTOR;run(original_image,m,cpu,{RETURN})
 assert get(m,ACTOR+36,2)==delay
 y=get(m,ACTOR+8);yaw=get(m,ACTOR+18,2);initial_vy=get(m,ACTOR+46,2)
 for remaining in range(delay,0,-1):
  update(original_image,m,f,'update_mini_rocket_delay_then_fall')
  assert get(m,ACTOR+36,2)==remaining-1 and get(m,ACTOR+8)==y and get(m,ACTOR+46,2)==0
 for n in [1,2]:
  update(original_image,m,f,'update_mini_rocket_delay_then_fall')
  vy=((0 if delay else initial_vy)-2*n)&65535;y=(y+signed(vy,16))&0xFFFFFFFF
  assert (get(m,ACTOR+8),get(m,ACTOR+46,2),get(m,ACTOR+18,2))==(y,vy,(yaw+16*n)&65535)

@pytest.mark.parametrize('space,kind,free',[(0,33,50),(0,33,51),(0,33,65535),(1,33,51),(128,33,51),(0,13,51)])
@pytest.mark.parametrize('dirty',[0,255])
@pytest.mark.parametrize('parent_y',[-100,0x7FFFFFF0,0xFFFFFFF8])
def test_buzz_spawn_gates_and_partial_record_copy(original_image,memory,fields,space,kind,free,dirty,parent_y):
 m,f=memory,fields;prepare(m,f,space);store(m,ACTOR+8,parent_y);store(m,ACTOR,kind,2);m[CHILD:CHILD+68]=bytes([dirty])*68
 store(m,f['free_object_count'],free,2);store(m,f['free_object_stack_cursor'],FREE+4);store(m,FREE,CHILD)
 parent=bytearray(m[ACTOR:ACTOR+68]);expected=bytearray(m[CHILD:CHILD+68]);allowed=space==0 and kind==33 and free>50
 # Rejected attempts continue phase tests, before their next possible action.
 join=f['continue_flying_phase_mask_tests_after_spawn_attempt']
 cpu=state(m,f['try_buzz_bomber_type6_spawn']);cpu.a[0]=ACTOR;run(original_image,m,cpu,{join,f['continue_primary_object_update_loop']})
 if allowed:
  expected[44:50]=parent[44:50];expected[4:16]=parent[4:16];store(expected,8,get(parent,8)+20)
  store(expected,0,6,2);expected[28]=2;expected[29]=6;expected[30]=255;expected[42]=33;store(expected,60,-1);parent[42]=6
 assert cpu.pc==(f['continue_primary_object_update_loop']if allowed else join)
 assert bytes(m[CHILD:CHILD+68])==expected and bytes(m[ACTOR:ACTOR+68])==parent
 assert get(m,f['free_object_count'],2)==free-int(allowed)and get(m,f['free_object_stack_cursor'])==FREE+4-4*int(allowed)


def test_spawn_then_free_body_marks_phase_without_releasing_slot(original_image,memory,fields):
 m,f=memory,fields;prepare(m,f);store(m,ACTOR,33,2);store(m,ACTOR+46,10,2)
 store(m,f['free_object_count'],51,2);store(m,f['free_object_stack_cursor'],FREE+4);store(m,FREE,CHILD)
 m[CHILD:CHILD+68]=bytes(68);cpu=state(m,f['try_buzz_bomber_type6_spawn']);cpu.a[0]=ACTOR
 run(original_image,m,cpu,{f['continue_primary_object_update_loop']});assert get(m,CHILD+8)==0xFFFFFFB0
 for y,vy,phase in [(-70,12,255),(-58,14,255),(-44,14,0)]:
  cpu=state(m,f['update_link_following_or_free_motion_object']);cpu.a[0]=CHILD;run(original_image,m,cpu,{f['continue_primary_object_update_loop']})
  assert (signed(get(m,CHILD+8),32),get(m,CHILD+46,2),m[CHILD+30])==(y,vy,phase)
 assert get(m,CHILD,2)==6 and get(m,f['free_object_count'],2)==50 and get(m,f['free_object_stack_cursor'])==FREE


def test_original_tables_connect_buzz_bomb_and_both_rocket_initializers(original_image,fields):
 raw=original_image[0];f=fields
 for kind,label in [(28,'initialize_square_rocket_attitude_and_y_high_word'),(29,'initialize_mini_rocket_delay_and_link')]:
  assert get(raw,0x17EEA-4096+4*kind)==f[label]
 for kind,label in [(6,'update_link_following_or_free_motion_object'),(29,'update_mini_rocket_delay_then_fall')]:
  assert 0x802A+signed(get(raw,0x802A-4096+2*kind,2),16)==f[label]
