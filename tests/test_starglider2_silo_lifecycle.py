"""Original four launcher state machines with supplied records and stationary inputs.

These CPU windows preserve partial initialization, unsigned comparisons and
null-link/stale-register behavior. They do not establish normal-play reachability,
world-list ordering, pointer lifetime, allocation capacity or elapsed frame time.
"""
import struct
import subprocess
from pathlib import Path

import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT
from tests.test_starglider2_control_normalization import signed

PARENT,CHILD,PLAYER,OTHER=INPUT+0x400,INPUT+0x500,INPUT+0x600,INPUT+0x800
FREE=0x85000
PROFILES={
 'near_air':('update_egron_silo_launch_cycle',False,False,70,300),
 'far_air':('update_distant_egron_silo_launch_cycle',False,True,40,900),
 'near_ground':('update_dome_silo_launch_cycle',True,False,70,300),
 'far_ground':('update_distant_dome_silo_launch_cycle',True,True,70,300),
}
APP_LABELS=['free_object_count','free_object_stack_cursor','player_object_reference',
 'sine_lookup_pointer','cosine_lookup_pointer','horizontal_world_wrap_mask']
LABELS=[p[0]for p in PROFILES.values()]+APP_LABELS+[
 'continue_primary_object_update_loop','continue_secondary_object_update_loop',
 'advance_shared_random_state','sine_cosine_lookup_words','cosine_lookup_view',
 'model_default_scale_shifts','model_default_durability_bytes','object_default_motion_words',
 'airborne_spawn_model_type_choices','ground_spawn_model_type_choices','update_nearby_egron_land_tank',
 'update_distant_linked_ground_actor_motion','secondary_object_update_offsets']


@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
 target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
 folder=tmp_path_factory.mktemp('silo-lifecycle');source=folder/'symbols.s';output=folder/'symbols.raw'
 source.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(LABELS)+'\n')
 r=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000','-no-opt',
  '-I'+str(target/'includes'),'-o',str(output),str(source)],cwd=target,capture_output=True,text=True)
 assert r.returncode==0,r.stdout+r.stderr
 raw=output.read_bytes();tail=4*len(LABELS);assert raw[:-tail]==original_image[0]
 return {n:v+(APP if n in APP_LABELS else 0)for n,v in zip(LABELS,struct.unpack('>'+'I'*len(LABELS),raw[-tail:]))}


def store(m,a,value,width=4):put(m,a,value&((1<<(width*8))-1),width)


def prepare(m,f,profile,dirty=0,yaw=0,choice=0,free=71):
 entry,ground,far,reserve,rearm=PROFILES[profile]
 m[PARENT:PARENT+68]=bytes(68);m[CHILD:CHILD+68]=bytes([dirty])*68;m[PLAYER:PLAYER+68]=bytes(68)
 store(m,PARENT,46 if ground else 5,2);m[PARENT+28]=6;m[PARENT+30]=255
 store(m,PARENT+4,1000);store(m,PARENT+8,-100);store(m,PARENT+12,0)
 for off,v in [(16,0x7FFF),(18,yaw),(20,0x8000),(50,1024)]:store(m,PARENT+off,v,2)
 store(m,f['player_object_reference'],PLAYER);store(m,f['horizontal_world_wrap_mask'],0x1FFFF)
 store(m,f['sine_lookup_pointer'],f['sine_cosine_lookup_words']);store(m,f['cosine_lookup_pointer'],f['cosine_lookup_view'])
 store(m,f['free_object_count'],free,2)
 for i in range(70):store(m,FREE+4*i,0x80000+68*i)
 store(m,FREE+280,CHILD);store(m,f['free_object_stack_cursor'],FREE+284)
 # An actual PRNG advance returns the desired low-three-bit choice.
 store(m,APP+0x60,0);store(m,APP+0x64,0xFFF9^choice)
 return entry,ground,far,reserve,rearm


def update(image,m,f,profile,incoming_a2=OTHER):
 entry,_,far,_,_=PROFILES[profile];cpu=state(m,f[entry]);cpu.a[0]=PARENT;cpu.a[2]=incoming_a2
 run(image,m,cpu,{f['continue_secondary_object_update_loop'if far else'continue_primary_object_update_loop']})
 return cpu


def velocity(m,f,yaw,scale):
 index=2*(yaw&4095)
 result=[]
 for table in ['sine_cosine_lookup_words','cosine_lookup_view']:
  product=(signed(scale,16)*signed(get(m,f[table]+index,2),16)*2)&0xFFFFFFFF
  result.append((product>>16)&65535)
 return (-result[0])&65535,result[1]


@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('free',[0,40,41,70,71,65535])
def test_unsigned_free_gate_precedes_real_prng_and_child_writes(original_image,memory,fields,profile,free):
 m,f=memory,fields;entry,ground,far,reserve,_=prepare(m,f,profile,dirty=0xA5,free=free)
 parent,child=bytes(m[PARENT:PARENT+68]),bytes(m[CHILD:CHILD+68]);cpu=state(m,f[entry]);cpu.a[0]=PARENT
 stop=f['continue_secondary_object_update_loop'if far else'continue_primary_object_update_loop']
 run(original_image,m,cpu,{stop,f['advance_shared_random_state']})
 assert cpu.pc==(f['advance_shared_random_state']if free>reserve else stop)
 assert get(m,f['free_object_count'],2)==free-int(free>reserve)
 assert get(m,f['free_object_stack_cursor'])==FREE+284-4*int(free>reserve)
 assert bytes(m[PARENT:PARENT+68])==parent and bytes(m[CHILD:CHILD+68])==child
 assert get(m,APP+0x60)==0 and get(m,APP+0x64)==0xFFF9


@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('count',[1,2,32767,32768,65535])
def test_nonzero_word_cooldown_decrements_and_returns_even_when_it_reaches_zero(original_image,memory,fields,profile,count):
 m,f=memory,fields;prepare(m,f,profile);store(m,PARENT+38,count,2);before=bytearray(m[PARENT:PARENT+68])
 update(original_image,m,f,profile);before[38:40]=((count-1)&65535).to_bytes(2,'big')
 assert bytes(m[PARENT:PARENT+68])==before and get(m,f['free_object_count'],2)==71


@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('phase',[1,2,7,19,128,255])
def test_closing_uses_byte_wrap_and_rearms_only_at_zero(original_image,memory,fields,profile,phase):
 m,f=memory,fields;*_,rearm=prepare(m,f,profile);m[PARENT+3]=phase;before=bytearray(m[PARENT:PARENT+68])
 update(original_image,m,f,profile);before[3]=(phase-1)&255
 if phase==1:before[38:40]=rearm.to_bytes(2,'big');before[28]|=128
 assert bytes(m[PARENT:PARENT+68])==before and get(m,f['free_object_count'],2)==71


@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('phase',[0,1,6,7,18,19,255])
@pytest.mark.parametrize('live',[False,True])
def test_attached_variant_gates_and_child_zero_do_not_clamp_dirty_phases(original_image,memory,fields,profile,phase,live):
 m,f=memory,fields;_,ground,_,_,rearm=prepare(m,f,profile)
 m[PARENT+3]=phase;m[PARENT+40]=255;store(m,PARENT+60,CHILD);store(m,CHILD,13 if live else 0,2)
 store(m,CHILD+8,-20);m[CHILD+2]=255
 parent,child=bytearray(m[PARENT:PARENT+68]),bytearray(m[CHILD:CHILD+68])
 update(original_image,m,f,profile)
 if not live:
  parent[40]=0;parent[3]=(phase-1)&255
  if phase==1:parent[38:40]=rearm.to_bytes(2,'big');parent[28]|=128
 elif phase==(7 if ground else 19):
  if ground:child[2]&=127
  else:child[8:12]=((-60)&0xFFFFFFFF).to_bytes(4,'big')
 else:parent[3]=(phase+1)&255
 assert bytes(m[PARENT:PARENT+68])==parent and bytes(m[CHILD:CHILD+68])==child


@pytest.mark.parametrize('profile',['near_air','far_air'])
@pytest.mark.parametrize('height',[-1141,-1140,-1139,-20,0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF])
def test_air_release_compares_unsigned_long_height_before_subtracting(original_image,memory,fields,profile,height):
 m,f=memory,fields;prepare(m,f,profile);m[PARENT+3]=19;m[PARENT+40]=255
 store(m,PARENT+60,CHILD);store(m,CHILD,13,2);store(m,CHILD+8,height);m[CHILD+2]=255
 update(original_image,m,f,profile);released=(height&0xFFFFFFFF)<=0xFFFFFB8C
 assert get(m,CHILD+8)==((height if released else height-40)&0xFFFFFFFF)
 assert m[CHILD+2]==(127 if released else 255)and m[PARENT+40]==(0 if released else 255)
 assert get(m,PARENT+60)==CHILD  # Release does not unlink either record.


@pytest.mark.parametrize('phase',[6,7])
@pytest.mark.parametrize('flags',[0,255])
def test_near_dome_null_link_keeps_incoming_a2_for_phase_seven_write(original_image,memory,fields,phase,flags):
 m,f=memory,fields;prepare(m,f,'near_ground');m[PARENT+3]=phase;m[PARENT+40]=255
 m[OTHER:OTHER+68]=bytes([flags])*68;before=bytearray(m[OTHER:OTHER+68])
 cpu=update(original_image,m,f,'near_ground',OTHER)
 if phase==7:before[2]&=127
 assert cpu.a[2]==OTHER and bytes(m[OTHER:OTHER+68])==before
 assert m[PARENT+3]==(7 if phase==6 else phase)and m[PARENT+40]==255


@pytest.mark.parametrize('profile,choice',[(p,i)for p,v in PROFILES.items()for i in range(4 if v[1]else 8)])
@pytest.mark.parametrize('dirty',[0,255])
@pytest.mark.parametrize('yaw',[0,65535])
def test_full_constructor_keeps_profile_and_partial_record_differences(original_image,memory,fields,profile,choice,dirty,yaw):
 m,f=memory,fields;_,ground,far,_,_=prepare(m,f,profile,dirty=dirty,yaw=yaw,choice=choice)
 table=f['ground_spawn_model_type_choices'if ground else'airborne_spawn_model_type_choices'];kind=m[table+choice]
 expected=bytearray(m[CHILD:CHILD+68]);parent=bytearray(m[PARENT:PARENT+68])
 store(expected,0,kind,2);expected[42]=46 if ground else 5;expected[3]=0
 expected[29]=3 if ground else m[f['model_default_scale_shifts']+kind]
 expected[28]=6 if ground else m[f['model_default_durability_bytes']+kind]
 store(expected,4,1000);store(expected,12,0);expected[30]=255;store(expected,60,PARENT)
 scale=get(m,f['object_default_motion_words']+2*kind,2);store(expected,32,scale,2)
 expected[43]=1;expected[41]=100
 if ground:
  store(expected,8,-5);store(expected,16,0x7FFF,2);store(expected,18,yaw+1024,2);store(expected,20,0x8000,2)
  expected[2]=(expected[2]|128)&~16;expected[40]=170
  if kind==9:
   store(expected,36,3,2);store(expected,38,100,2)
   if not far:store(expected,8,-4)
  vx,vz=velocity(m,f,(yaw+1024)&65535,scale);store(expected,44,vx,2);store(expected,48,vz,2)
  # The shared X/Z helper does not initialize vertical velocity.
 else:
  store(expected,8,-20);store(expected,18,3072,2);store(expected,20,1,2)
  store(expected,36,1022,2);store(expected,38,0,2);store(expected,46,-5,2);expected[2]|=160
  # Axis input qualifies the stored-coordinate and world-coordinate heading entries.
 parent[40]=255;parent[42]=kind;store(parent,60,CHILD)
 if ground and far:parent[41]=255
 update(original_image,m,f,profile)
 assert bytes(m[CHILD:CHILD+68])==expected and bytes(m[PARENT:PARENT+68])==parent
 assert get(m,f['free_object_count'],2)==70 and get(m,f['free_object_stack_cursor'])==FREE+280
 assert [get(m,APP+off)for off in[0x60,0x64]]==[0xFFF9^choice,choice]


@pytest.mark.parametrize('profile',['near_air','far_air'])
@pytest.mark.parametrize('dirty',[0,255])
def test_air_constructor_open_lift_release_and_close_witness_uses_original_updates(original_image,memory,fields,profile,dirty):
 m,f=memory,fields;*_,rearm=prepare(m,f,profile,dirty=dirty,choice=0)
 update(original_image,m,f,profile);assert get(m,CHILD,2)==13
 for i in range(19):
  update(original_image,m,f,profile)
  assert m[PARENT+3]==i+1 and get(m,CHILD+8)==0xFFFFFFEC and m[PARENT+40]==255
 for i in range(28):
  update(original_image,m,f,profile)
  assert get(m,CHILD+8)==((-20-40*(i+1))&0xFFFFFFFF)and m[PARENT+40]==255
 update(original_image,m,f,profile)
 assert m[PARENT+40]==0 and not(m[CHILD+2]&128)
 assert get(m,PARENT+60)==CHILD and get(m,CHILD+60)==PARENT
 for i in range(19):
  update(original_image,m,f,profile);assert m[PARENT+3]==18-i
 assert get(m,PARENT+38,2)==rearm and m[PARENT+28]==134
 assert get(m,f['free_object_count'],2)==70
 assert get(m,CHILD+36,2)==1022  # Parent-only service does not age the child's budget.


@pytest.mark.parametrize('profile',['near_ground','far_ground'])
def test_dome_spawned_tank_releases_parent_after_170_nearby_child_updates(original_image,memory,fields,profile):
 m,f=memory,fields;prepare(m,f,profile,choice=1)
 update(original_image,m,f,profile);assert get(m,CHILD,2)==9
 initial_y=get(m,CHILD+8);assert initial_y==(0xFFFFFFFC if profile=='near_ground'else 0xFFFFFFFB)
 for _ in range(8):update(original_image,m,f,profile)
 assert m[PARENT+3]==7 and m[PARENT+40]==255 and not(m[CHILD+2]&128)
 for i in range(170):
  cpu=state(m,f['update_nearby_egron_land_tank']);cpu.a[0]=CHILD
  run(original_image,m,cpu,{f['continue_primary_object_update_loop']})
  assert m[CHILD+40]==169-i and m[PARENT+40]==(255 if i<169 else 0)
 assert get(m,CHILD+60)==0 and get(m,PARENT+60)==CHILD
 assert get(m,CHILD+8)==initial_y
 for _ in range(7):update(original_image,m,f,profile)
 assert m[PARENT+3]==0 and get(m,PARENT+38,2)==300


def test_original_secondary_directory_shares_link_counter_body(original_image,memory,fields):
 base=fields['secondary_object_update_offsets']
 for kind in [1,9,39]:
  assert base+signed(get(memory,base+2*kind,2),16)==fields['update_distant_linked_ground_actor_motion']


@pytest.mark.parametrize('count',[0,1,2,127,128,255])
@pytest.mark.parametrize('linked',[False,True])
@pytest.mark.parametrize('speeds',[(0,0),(7,-9),(-32768,32767)])
@pytest.mark.parametrize('positions',[(0,0),(0xFFFFFFFF,0x80000000)])
@pytest.mark.parametrize('mask',[0x1FFFF,0x5555])
def test_distant_ground_counter_tests_before_decrement_and_repeats_horizontal_motion(
        original_image,memory,fields,count,linked,speeds,positions,mask):
 m,f=memory,fields;prepare(m,f,'far_ground');m[PARENT+40]=255
 store(m,CHILD,9,2);store(m,CHILD+60,PARENT if linked else 0);m[CHILD+40]=count
 for off,value in zip([4,12],positions):store(m,CHILD+off,value)
 for off,value in zip([44,48],speeds):store(m,CHILD+off,value,2)
 store(m,f['horizontal_world_wrap_mask'],mask)
 child,parent=bytearray(m[CHILD:CHILD+68]),bytearray(m[PARENT:PARENT+68])
 releases=linked and count==0;steps=1 if releases else 2
 for off,value,velocity_ in zip([4,12],positions,speeds):
  for _ in range(steps):value=((value+velocity_)&0xFFFFFFFF)&mask
  store(child,off,value)
 if releases:store(child,60,0);parent[40]=0
 else:child[40]=(count-1)&255
 cpu=state(m,f['update_distant_linked_ground_actor_motion']);cpu.a[0]=CHILD
 run(original_image,m,cpu,{f['continue_secondary_object_update_loop']})
 assert bytes(m[CHILD:CHILD+68])==child and bytes(m[PARENT:PARENT+68])==parent


@pytest.mark.parametrize('near_calls_at_zero',[0,2])
def test_distant_zero_can_cross_into_nearby_service_without_releasing_parent(
        original_image,memory,fields,near_calls_at_zero):
 m,f=memory,fields;prepare(m,f,'far_ground',choice=1)
 update(original_image,m,f,'far_ground')
 for _ in range(8):update(original_image,m,f,'far_ground')
 assert get(m,CHILD,2)==9 and not(m[CHILD+2]&128)
 for i in range(170):
  cpu=state(m,f['update_distant_linked_ground_actor_motion']);cpu.a[0]=CHILD
  run(original_image,m,cpu,{f['continue_secondary_object_update_loop']})
  assert m[CHILD+40]==169-i and m[PARENT+40]==255
 assert get(m,CHILD+60)==PARENT
 for _ in range(near_calls_at_zero):
  cpu=state(m,f['update_nearby_egron_land_tank']);cpu.a[0]=CHILD
  run(original_image,m,cpu,{f['continue_primary_object_update_loop']})
  assert m[CHILD+40]==0 and m[PARENT+40]==255 and get(m,CHILD+60)==PARENT
 # The next distant service releases before decrementing. A following unlinked
 # service wraps zero to 255 and resumes the double-motion branch.
 cpu=state(m,f['update_distant_linked_ground_actor_motion']);cpu.a[0]=CHILD
 run(original_image,m,cpu,{f['continue_secondary_object_update_loop']})
 assert m[CHILD+40]==0 and m[PARENT+40]==0 and get(m,CHILD+60)==0
 cpu=state(m,f['update_distant_linked_ground_actor_motion']);cpu.a[0]=CHILD
 run(original_image,m,cpu,{f['continue_secondary_object_update_loop']})
 assert m[CHILD+40]==255 and m[PARENT+40]==0
 assert get(m,f['free_object_count'],2)==70
