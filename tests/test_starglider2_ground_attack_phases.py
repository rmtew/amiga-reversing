"""Original Walker/Stomper/Tank phase handoffs and shared laser construction.

Backed records and local entry contexts qualify arithmetic, gates and write order.
They do not prove normal list admission, selector bounds, peer lifetime or timing.
"""
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT
from tests.test_starglider2_control_normalization import signed
from tests.test_starglider2_scan_acquisition import project

OBJ,PLAYER,CHILD,PEER,FREE=INPUT,INPUT+0x100,INPUT+0x200,INPUT+0x300,0x85000
PROFILES={
 'walker':(0x8850,0x889E,1,600,50,0x898E,0x899A,22),
 'stomper':(0x8A74,0x8ACA,15,570,60,0x8BAA,0x8BB6,20),
 'tank':(0x9B4C,0x9B88,9,600,50,0x9C70,0x9C7C,None)}
APPS=['player_object_reference','horizontal_world_wrap_mask','ai_type12_projectile_request',
 'free_object_count','free_object_stack_cursor','model_type_target_selection_tags_prefix',
 'sine_lookup_pointer','cosine_lookup_pointer','inside_structure_flag','space_environment_flag']
LABELS=APPS+['continue_primary_object_update_loop','try_ai_projectile_attack_if_aligned','spawn_ai_projectile_continuation',
 'heading_with_player_as_reference','blend_actor_toward_opposite_player_heading','blend_actor_heading_and_clear_other_rotations',
 'object_projectile_spawn_y_offsets','sine_cosine_lookup_words','cosine_lookup_view','update_land_tank_pair_link_delay','update_nearby_type72_or_type103_projectile']
LASER,REVERSE=0x9F02,0x9248

@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
 target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
 folder=tmp_path_factory.mktemp('ground-attack');source=folder/'symbols.s';output=folder/'symbols.raw'
 source.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(LABELS)+'\n')
 r=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000','-no-opt',
  '-I'+str(target/'includes'),'-o',str(output),str(source)],cwd=target,capture_output=True,text=True)
 assert r.returncode==0,r.stdout+r.stderr
 raw=output.read_bytes();tail=4*len(LABELS);assert raw[:-tail]==original_image[0]
 return {n:v+(APP if n in APPS else 0)for n,v in zip(LABELS,struct.unpack('>'+'I'*len(LABELS),raw[-tail:]))}

def store(m,address,value,width=4):put(m,address,value&((1<<(8*width))-1),width)

def prepare(m,f,profile='walker',dirty=0):
 kind=PROFILES[profile][2]
 for address in [OBJ,PLAYER,PEER]:m[address:address+68]=bytes(68)
 m[CHILD:CHILD+68]=bytes([dirty])*68
 store(m,OBJ,kind,2);m[OBJ+28]=6;m[OBJ+30]=255;store(m,OBJ+50,10,2)
 for off,value in [(4,1000),(8,-100),(12,2000)]:store(m,OBJ+off,value)
 for off,value in [(44,3),(46,-7),(48,-3)]:store(m,OBJ+off,value,2)
 store(m,f['player_object_reference'],PLAYER);store(m,f['horizontal_world_wrap_mask'],0x1FFFF)
 store(m,f['free_object_count'],26,2);store(m,f['free_object_stack_cursor'],FREE+4);store(m,FREE,CHILD)
 store(m,f['sine_lookup_pointer'],f['sine_cosine_lookup_words']);store(m,f['cosine_lookup_pointer'],f['cosine_lookup_view'])
 m[f['ai_type12_projectile_request']]=0xA5
 return kind

def integrate(expected):
 for off,v in [(4,44),(12,48)]:store(expected,off,(get(expected,off)+signed(get(expected,v,2),16))&0x1FFFF)

@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('durability',[0,6,255])
@pytest.mark.parametrize('variant',[0,20,21,22,127,128,255])
def test_entry_damage_gates_extra_motion_and_signed_variant_wrap(original_image,memory,fields,profile,durability,variant):
 m,f=memory,fields;prepare(m,f,profile);entry,join,_,_,_,_,_,maximum=PROFILES[profile]
 if profile=='tank':join=f['update_land_tank_pair_link_delay']+4
 m[OBJ+28]=durability;m[OBJ+3]=variant;store(m,OBJ+36,0,2);store(m,OBJ+38,7,2)
 expected=bytearray(m[OBJ:OBJ+68]);store(expected,36,-1,2)
 if durability!=6:
  integrate(expected);store(expected,38,-1,2)
 if maximum is not None:
  value=(variant+1+(durability!=6))&255
  expected[3]=0 if signed(value,8)>maximum else value
 cpu=state(m,entry);cpu.a[0]=OBJ;run(original_image,m,cpu,{join},limit=40)
 assert bytes(m[OBJ:OBJ+68])==expected and cpu.a[4]==PLAYER


def expected_route(f,profile,delayed,left):
 aligned=f['try_ai_projectile_attack_if_aligned'];direct=f['spawn_ai_projectile_continuation'];done=f['continue_primary_object_update_loop']
 if delayed:
  if profile=='walker':return (aligned,255)if not(left&31)else(aligned,0)if not(left&15)else(LASER,0)if not(left&7)else(done,0)
  if profile=='stomper':return (direct,255)if not(left&15)else(aligned,0)if not(left&7)else(done,0)
  return (aligned,0)if not(left&15)else(LASER,0)if not(left&7)else(done,0)
 first,second,third=(63,31,15)if profile=='walker'else(31,15,7 if profile=='tank'else None)
 if not(left&first):return REVERSE,255
 if not(left&second):return REVERSE,0
 if third is not None and not(left&third):return LASER,0
 return f['blend_actor_toward_opposite_player_heading'],0

@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('delayed',[False,True])
@pytest.mark.parametrize('left',[0,1,7,8,15,16,24,31,32,48,63,64,255,65535])
def test_decremented_phase_masks_choose_distinct_request_and_attack_handoffs(original_image,memory,fields,profile,delayed,left):
 m,f=memory,fields;prepare(m,f,profile);store(m,OBJ+36,left+1,2);store(m,OBJ+38,-1,2);m[OBJ+40]=2 if delayed else 0
 before=bytearray(m[OBJ:OBJ+68]);expected=bytearray(before);store(expected,36,left,2);integrate(expected)
 if profile!='tank':expected[3]=1
 if delayed:expected[40]=1
 route,request=expected_route(f,profile,delayed,left)
 stops={f['continue_primary_object_update_loop'],f['try_ai_projectile_attack_if_aligned'],f['spawn_ai_projectile_continuation'],
  f['blend_actor_toward_opposite_player_heading'],LASER,REVERSE}
 cpu=state(m,PROFILES[profile][0]);cpu.a[0]=OBJ;run(original_image,m,cpu,stops,limit=140)
 assert cpu.pc==route and m[f['ai_type12_projectile_request']]==request
 assert bytes(m[OBJ:OBJ+68])==expected and get(m,f['free_object_count'],2)==26

@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('count',[0,1,2,32767,32768,65535])
@pytest.mark.parametrize('x,z',[(599,2000),(601,2000),(2000,599),(2000,601),(-32768,2000),(-601,-601),(569,2000),(570,2000),(571,2000),(600,2000),(2000,570),(-600,2000),(-570,2000)])
def test_evasion_uses_signed_wrapped_axis_or_test_and_reload_only_on_expiry(original_image,memory,fields,profile,count,x,z):
 m,f=memory,fields;prepare(m,f,profile);store(m,OBJ+36,2,2);store(m,OBJ+38,count,2)
 store(m,OBJ+50,x,2);store(m,OBJ+54,z,2)
 _,_,_,window,reload,turn_return,follow_return,_=PROFILES[profile]
 next_count=count-1 if 0<count<32768 else count
 magnitude=lambda v:signed((-v if v<0 else v)&65535,16)
 turn=next_count==0 and (magnitude(x)<=window or magnitude(z)<=window)
 opposite=count>=32768 or (next_count==0 and not turn)
 cpu=state(m,PROFILES[profile][0]);cpu.a[0]=OBJ
 run(original_image,m,cpu,{f['heading_with_player_as_reference'],f['blend_actor_toward_opposite_player_heading']},limit=100)
 assert get(m,OBJ+38,2)==(reload if turn else next_count)
 if opposite:assert cpu.pc==f['blend_actor_toward_opposite_player_heading']
 else:
  assert cpu.pc==f['heading_with_player_as_reference']
  assert get(m,cpu.a[7])==(turn_return if turn else follow_return)

@pytest.mark.parametrize('kind',[1,9,15])
@pytest.mark.parametrize('tag,free',[(0,26),(1,25),(255,0),(1,26),(255,65535)])
def test_laser_gate_follows_real_heading_but_precedes_allocation(original_image,memory,fields,kind,tag,free):
 m,f=memory,fields;prepare(m,f,dirty=0xA5);store(m,OBJ,kind,2);m[f['model_type_target_selection_tags_prefix']+kind]=tag
 store(m,f['free_object_count'],free,2);parent=bytes(m[OBJ:OBJ+68]);child=bytes(m[CHILD:CHILD+68]);allowed=tag!=0 and free>25
 cpu=state(m,LASER);cpu.a[0]=OBJ
 # Stop at first child write to separate gate and constructor effects.
 run(original_image,m,cpu,{0x9F50,f['continue_primary_object_update_loop']},limit=80)
 assert cpu.pc==(0x9F50 if allowed else f['continue_primary_object_update_loop'])and cpu.a[4]==PLAYER
 assert get(m,f['free_object_count'],2)==free-int(allowed)and get(m,f['free_object_stack_cursor'])==FREE+4-4*int(allowed)
 assert bytes(m[OBJ:OBJ+68])==parent and bytes(m[CHILD:CHILD+68])==child
 assert cpu.d[1]&65535==1024

@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('shift',[0,1,31,32,64,255])
@pytest.mark.parametrize('dirty',[0,255])
@pytest.mark.parametrize('parent_y',[-100,0x7FFFFFF0])
def test_full_laser_constructor_retains_flags_links_and_scale_count_aliases(original_image,memory,fields,profile,shift,dirty,parent_y):
 m,f=memory,fields;kind=prepare(m,f,profile,dirty);m[OBJ+29]=shift;store(m,OBJ+8,parent_y)
 m[f['model_type_target_selection_tags_prefix']+kind]=1;m[f['inside_structure_flag']]=255
 parent=bytearray(m[OBJ:OBJ+68]);expected=bytearray(m[CHILD:CHILD+68])
 height=signed(get(m,f['object_projectile_spawn_y_offsets']+2*kind,2),16)>>(shift&63)
 for off in [4,12]:expected[off:off+4]=parent[off:off+4]
 store(expected,8,parent_y+height);store(expected,0,72,2);expected[3]=0;expected[28]=1;expected[29]=4;expected[30]=255;expected[34]=0;expected[42]=kind
 for off,value in [(16,0),(18,1024),(20,0),(32,-100),(36,100),(46,0)]:store(expected,off,value,2)
 sine=get(m,f['sine_cosine_lookup_words']+2048,2);cosine=get(m,f['cosine_lookup_view']+2048,2)
 store(expected,44,-project((-100)&65535,sine),2);store(expected,48,project((-100)&65535,cosine),2);parent[42]=72
 cpu=state(m,LASER);cpu.a[0]=OBJ;run(original_image,m,cpu,{f['continue_primary_object_update_loop']},limit=120)
 assert bytes(m[CHILD:CHILD+68])==expected and bytes(m[OBJ:OBJ+68])==parent
 assert get(m,f['free_object_count'],2)==25 and get(m,f['free_object_stack_cursor'])==FREE


def test_original_update_directory_binds_all_three_ground_actors(original_image,fields):
 raw=original_image[0]
 for entry,_,kind,*_ in PROFILES.values():assert 0x802A+signed(get(raw,0x802A-4096+2*kind,2),16)==entry
 assert 0x802A+signed(get(raw,0x802A-4096+2*72,2),16)==fields['update_nearby_type72_or_type103_projectile']

@pytest.mark.parametrize('profile,left',[('walker',16),('tank',8)])
def test_ground_phase_to_laser_then_one_hundred_local_projectile_updates(original_image,memory,fields,profile,left):
 m,f=memory,fields;kind=prepare(m,f,profile);store(m,OBJ+36,left+1,2);store(m,OBJ+8,-100000)
 store(m,OBJ+18,0,2);m[f['model_type_target_selection_tags_prefix']+kind]=1
 m[f['space_environment_flag']]=0
 cpu=state(m,PROFILES[profile][0]);cpu.a[0]=OBJ
 run(original_image,m,cpu,{f['continue_primary_object_update_loop']},limit=180)
 assert get(m,CHILD,2)==72 and get(m,CHILD+18,2)==1024 and get(m,CHILD+36,2)==100
 assert get(m,OBJ+36,2)==left and m[OBJ+42]==72 and m[CHILD+34]==0
 assert (get(m,CHILD+4),get(m,CHILD+12))==(1003,1997)
 x,z=get(m,CHILD+4),get(m,CHILD+12);y=get(m,CHILD+8)
 vx,vz=signed(get(m,CHILD+44,2),16),signed(get(m,CHILD+48,2),16)
 for n in range(1,101):
  cpu=state(m,f['update_nearby_type72_or_type103_projectile']);cpu.a[0]=CHILD
  run(original_image,m,cpu,{f['continue_primary_object_update_loop']},limit=60)
  x,z=(x+vx)&0x1FFFF,(z+vz)&0x1FFFF
  assert (get(m,CHILD+4),get(m,CHILD+8),get(m,CHILD+12))==(x,y,z)
  assert get(m,CHILD+36,2)==100-n and m[CHILD+30]==(0 if n==100 else 255)
 assert get(m,CHILD,2)==72 and get(m,f['free_object_count'],2)==25

@pytest.mark.parametrize('yaw',[0,4095,65535])
@pytest.mark.parametrize('target',[0,44,45,46,65535,65492,65491,32767,32768,32769])
def test_alignment_gate_uses_wrapped_negation_and_subtraction_n_flag(original_image,memory,fields,yaw,target):
 m,f=memory,fields;prepare(m,f);store(m,OBJ+18,yaw,2)
 difference=(target-(yaw&4095))&65535;magnitude=(-difference)&65535 if difference&32768 else difference
 accepted=bool(((magnitude-45)&65535)&32768)
 cpu=state(m,f['try_ai_projectile_attack_if_aligned']);cpu.a[0]=OBJ;cpu.d[1]=0xA5A50000|target
 run(original_image,m,cpu,{f['spawn_ai_projectile_continuation'],f['continue_primary_object_update_loop']},limit=20)
 assert cpu.pc==(f['spawn_ai_projectile_continuation']if accepted else f['continue_primary_object_update_loop'])
 assert get(m,f['free_object_count'],2)==26 and bytes(m[CHILD:CHILD+68])==bytes(68)
