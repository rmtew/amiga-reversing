"""Original tractor continuations with explicit records, arrays and RAM state.

These do not establish normal-game selector domains, pointer lifetime, queue
capacity or physics units. Internal phases stop before their saved-frame or
object-loop handoff; direct toggle entry exercises its real register frame.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, STACK, RETURN
from tests.test_starglider2_scan_acquisition import setup, record, OBJECT, OLD

FIELDS=['tractor_target_reference','previous_tractor_target_reference','scan_target_type',
        'tractor_target_rotation_step','tractor_velocity_decay_phase','tractor_attraction_shift',
        'tractor_input_override_flag','player_world_x','player_world_y','player_world_z',
        'nearby_object_count','visible_object_count','tractor_command_toggle_word',
        'free_object_count','free_object_stack_cursor','reuse_tractor_markers_flag',
        'tractor_markers_shrinking_flag','tractor_marker_shrink_countdown',
        'tractor_marker_lower_y_offset','released_object_tracking_references',
        'space_environment_flag','icarus_power_reserve','weapon_energy_reserve',
        'icarus_shield_strength','panel_fast_animation_request',
        'model_type_population_counts','taymar_delivered_model_counts_prefix',
        'inside_structure_flag','neutron_bomb_collection_enabled_flag',
        'neutron_bomb_ready_flag','neutron_bomb_order_requested_flag',
        'bomb_ingredient_set_complete_flag','weapon_selection_and_status',
        'neutron_bomb_spawn_request','neutron_bomb_retract_request',
        'professor_taymar_aboard_flag']
POOL,FREE=0x85000,0x84000


def signed(v,bits=32):
    v&=(1<<bits)-1
    return v-(1<<bits)if v&(1<<(bits-1))else v


def write(m,p,v,width=4):put(m,p,v&((1<<(8*width))-1),width)


@pytest.fixture(scope='module')
def fields(tmp_path_factory):
    root=Path(__file__).resolve().parents[1];target=root/'targets/amiga_raw_starglider2_game'
    folder=tmp_path_factory.mktemp('tractor-fields');asm=folder/'map.s';out=folder/'map.raw'
    asm.write_text((target/'starglider2_game.s').read_text().split('    SECTION code,code',1)[0]
                   +'\n SECTION constants,data\n dc.l '+','.join(FIELDS)+'\n')
    result=subprocess.run([str(root/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-no-opt',
                           '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    return dict(zip(FIELDS,[APP+v for v in struct.unpack('>'+len(FIELDS)*'I',out.read_bytes())]))


@pytest.mark.parametrize('step',[-5,-4,-1,0,1,4,5])
@pytest.mark.parametrize('phase',[0,15])
@pytest.mark.parametrize('shift',[0,4,10,32,63,64])
@pytest.mark.parametrize('kind',[1,3])
def test_attraction_direction_damping_and_signed_velocity_halving_keep_original_order(original_image,memory,fields,step,phase,shift,kind):
    m=memory;f=fields;obj=POOL
    m[obj:obj+68]=b'\xA5'*68;write(m,obj,kind,2)
    player=[1000,-2000,3000];position=[900,-2100,2800]
    for j,(p,v)in enumerate(zip(player,position)):
        write(m,f[['player_world_x','player_world_y','player_world_z'][j]],p)
        write(m,obj+4+4*j,v)
    write(m,obj+18,4094,2)
    velocities=[-32768,-3,32767,5]
    for off,v in zip([44,46,48,32],velocities):write(m,obj+off,v,2)
    write(m,f['tractor_target_rotation_step'],step,2);write(m,f['tractor_velocity_decay_phase'],phase,2)
    write(m,f['tractor_attraction_shift'],shift,2);m[f['tractor_input_override_flag']]=0
    before=bytearray(m[obj:obj+68]);expected=bytearray(before)
    expected[18:20]=((4094+step)&4095).to_bytes(2,'big')
    deltas=[signed(p-v)>>(shift&63)for p,v in zip(player,position)]
    anchored=bool(m[0x39536+kind]&128)
    if anchored:
        player=[(v-d)&0xFFFFFFFF for v,d in zip(player,deltas)]
        next_step,next_phase=step&65535,phase
    else:
        position=[(v+d)&0xFFFFFFFF for v,d in zip(position,deltas)]
        next_step=(step+(4 if step<0 else-4))&65535
        next_phase=phase if step<0 else(phase+1)&15
        if step>=0 and next_phase==0:
            for off,v in zip([44,46,48,32],velocities):expected[off:off+2]=((v>>1)&65535).to_bytes(2,'big')
        if ((position[1]+120)&0xFFFFFFFF)<0x80000000:position[1]=(-120)&0xFFFFFFFF
        for j,v in enumerate(position):expected[4+4*j:8+4*j]=(v&0xFFFFFFFF).to_bytes(4,'big')
    cpu=state(m,0x3539C);cpu.a[0]=obj
    run(original_image,m,cpu,{0x354D4})
    assert bytes(m[obj:obj+68])==expected
    assert [get(m,f[n])for n in ['player_world_x','player_world_y','player_world_z']]==[v&0xFFFFFFFF for v in player]
    assert get(m,f['tractor_target_rotation_step'],2)==next_step
    assert get(m,f['tractor_velocity_decay_phase'],2)==next_phase
    assert m[f['tractor_input_override_flag']]==255 and cpu.a[7]==STACK


@pytest.mark.parametrize('axis',range(3))
@pytest.mark.parametrize('distance',[9999,10000,-10000,-9999,-2147483648])
def test_per_axis_distance_failure_clears_lock_but_does_not_clear_override(original_image,memory,fields,axis,distance):
    m=memory;f=fields;obj=POOL
    write(m,obj,1,2);write(m,f['tractor_target_reference'],obj);write(m,f['scan_target_type'],1,2)
    m[f['tractor_input_override_flag']]=0x5A
    for j,n in enumerate(['player_world_x','player_world_y','player_world_z']):
        write(m,f[n],0);write(m,obj+4+4*j,distance if axis==j else 0)
    write(m,f['tractor_attraction_shift'],10,2)
    cpu=state(m,0x3539C);cpu.a[0]=obj
    run(original_image,m,cpu,{0x354D4})
    rejected=distance in [10000,-10000,-2147483648]
    assert get(m,f['tractor_target_reference'])==(0 if rejected else obj)
    assert get(m,f['scan_target_type'],2)==(0 if rejected else 1)
    assert m[f['tractor_input_override_flag']]==(0x5A if rejected else 255)


def test_nonnull_toggle_releases_lock_without_overwriting_previous_reference_snapshot(original_image,memory,fields):
    m=memory;f=fields
    write(m,f['tractor_target_reference'],POOL);write(m,f['previous_tractor_target_reference'],0x12345678)
    write(m,f['scan_target_type'],1,2);write(m,f['tractor_target_rotation_step'],99,2)
    m[f['tractor_input_override_flag']]=255
    cpu=state(m,0x357AA);d,a=list(cpu.d),list(cpu.a)
    run(original_image,m,cpu,{RETURN})
    assert get(m,f['tractor_target_reference'])==get(m,f['scan_target_type'],2)==get(m,f['tractor_target_rotation_step'],2)==0
    assert get(m,f['previous_tractor_target_reference'])==0x12345678
    assert m[f['tractor_input_override_flag']]==0
    assert list(cpu.d)==d and list(cpu.a)[:7]==a[:7]and cpu.a[7]==STACK+4


@pytest.mark.parametrize('kind,miss',[(1,False),(2,False),(12,True),(30,True),
                                     (72,True),(84,True),(103,True),(128,True)])
@pytest.mark.parametrize('free',[0,10,11,65535])
def test_null_toggle_uses_real_scan_then_retains_partial_lock_or_builds_two_markers(original_image,memory,fields,kind,miss,free):
    m=memory;f=fields
    setup(m,[record(type_=kind)])
    write(m,f['visible_object_count'],1,2);write(m,f['nearby_object_count'],0,2)
    write(m,f['tractor_target_reference'],0);write(m,f['previous_tractor_target_reference'],0x12345678)
    write(m,f['tractor_command_toggle_word'],-1,2);write(m,f['free_object_count'],free,2)
    m[f['reuse_tractor_markers_flag']]=0x5A
    write(m,f['free_object_stack_cursor'],FREE+44)
    for i in range(11):write(m,FREE+4*i,POOL+68*i)
    m[POOL:POOL+11*68]=b'\xA5'*(11*68)
    write(m,f['player_world_x'],100);write(m,f['player_world_y'],-1000);write(m,f['player_world_z'],200)
    for off,v in [(4,100),(8,-1000),(12,200)]:write(m,OBJECT+off,v)
    # Ten tracking slots have no zero match: the original null search must not
    # remove any nonzero reference. It then snapshots the null target itself.
    tracking=f['released_object_tracking_references']
    for i in range(10):write(m,tracking+4*i,0x10000+68*i)
    before=bytes(m[tracking:tracking+40])
    cpu=state(m,0x357AA);d,a=list(cpu.d),list(cpu.a)
    run(original_image,m,cpu,{RETURN})
    # This caller uses the saved-frame scan variant. A miss keeps its old REF;
    # the caller copies that REF before testing the separately cleared type.
    assert get(m,f['tractor_target_reference'])==(OLD if miss else OBJECT)
    assert get(m,f['scan_target_type'],2)==(0 if miss else kind)
    assert get(m,f['previous_tractor_target_reference'])==0
    assert m[f['reuse_tractor_markers_flag']]==(0x5A if miss else 0)
    assert bytes(m[tracking:tracking+40])==before
    allocated=not miss and free>10
    assert get(m,f['free_object_count'],2)==free-(2 if allocated else 0)
    assert get(m,f['free_object_stack_cursor'])==FREE+44-(8 if allocated else 0)
    if allocated:
        first,second=POOL+10*68,POOL+9*68
        assert get(m,first,2)==get(m,second,2)==95
        # Only marker one clears BYTE22; marker two retains its supplied seed.
        assert m[first+34]==0 and m[second+34]==0xA5
        assert get(m,first+18,2)==0 and get(m,second+18,2)==1024
        assert bytes(m[POOL:POOL+9*68])==b'\xA5'*(9*68)
    else:assert bytes(m[POOL:POOL+11*68])==b'\xA5'*(11*68)
    assert list(cpu.d)==d and list(cpu.a)[:7]==a[:7]and cpu.a[7]==STACK+4


@pytest.mark.parametrize('space',[0,1,127,128,255])
@pytest.mark.parametrize('present',[False,True])
def test_marker_follows_target_with_sign_gated_y_offset_and_unmasked_word_angles(original_image,memory,fields,space,present):
    m=memory;f=fields;obj=POOL;target=POOL+68
    m[obj:obj+68]=b'\xA5'*68;write(m,obj,95,2)
    origin=[0x7FFFFFFF,1000,-200];position=[-2147483648,-400,400]
    for i,(v,t)in enumerate(zip(origin,position)):
        write(m,obj+4+4*i,v);write(m,target+4+4*i,t)
    angles=[65530,4090,0xFF80]
    for off,v in zip([16,18,20],angles):write(m,obj+off,v,2)
    m[obj+29]=255;m[obj+3]=15
    write(m,f['tractor_target_reference'],target if present else 0)
    m[f['tractor_markers_shrinking_flag']]=0;m[f['space_environment_flag']]=space
    write(m,f['tractor_marker_lower_y_offset'],128)
    expected=bytearray(m[obj:obj+68])
    if present:
        position[1]-=128 if space<128 else 0
        for i,(v,t)in enumerate(zip(origin,position)):
            value=(v+(signed(t-v)>>3))&0xFFFFFFFF
            expected[4+4*i:8+4*i]=value.to_bytes(4,'big')
        for off,v,delta in zip([16,18,20],angles,[128,2048,128]):expected[off:off+2]=((v+delta)&65535).to_bytes(2,'big')
        expected[3]=0
    else:expected[:2]=b'\x00\x00'
    cpu=state(m,0x35AE6);cpu.a[0]=obj
    run(original_image,m,cpu,{0x39D56})
    assert bytes(m[obj:obj+68])==expected and cpu.a[7]==STACK


@pytest.mark.parametrize('count',[0,1,2,127,128,255])
def test_two_marker_bodies_share_byte_countdown_and_preserve_wrapping_shrink_steps(original_image,memory,fields,count):
    m=memory;f=fields;m[f['tractor_markers_shrinking_flag']]=1
    m[f['tractor_marker_shrink_countdown']]=count
    for i in range(2):
        obj=POOL+68*i;m[obj:obj+68]=b'\xA5'*68;write(m,obj,95,2)
        m[obj+29]=255;m[obj+3]=15
        expected=bytearray(m[obj:obj+68]);count=(count-1)&255
        if count>=128:expected[:2]=b'\0\0'
        else:
            expected[29]=expected[3]=0
            for off,delta in [(16,128),(18,2048),(20,128)]:
                expected[off:off+2]=((get(m,obj+off,2)+delta)&65535).to_bytes(2,'big')
        cpu=state(m,0x35AE6);cpu.a[0]=obj
        run(original_image,m,cpu,{0x39D56})
        assert bytes(m[obj:obj+68])==expected
        assert m[f['tractor_marker_shrink_countdown']]==count and cpu.a[7]==STACK


@pytest.mark.parametrize('present',[False,True])
@pytest.mark.parametrize('zero',[False,True])
def test_key_entry_branch_uses_incoming_z_not_the_pointer_loaded_by_movea(original_image,memory,fields,present,zero):
    m=memory;f=fields;pointer=POOL if present else 0
    write(m,f['tractor_target_reference'],pointer)
    cpu=state(m,0x354E2);cpu.d[0]=0xABCD0058;old_d7=cpu.d[7]
    cpu.sr=(cpu.sr|4)if zero else(cpu.sr&~4)
    run(original_image,m,cpu,{0x354EC,0x35782})
    assert cpu.pc==(0x35782 if zero else 0x354EC)
    assert cpu.a[0]==pointer and cpu.a[7]==STACK
    assert cpu.d[7]==(old_d7 if zero else(old_d7&0xFFFF0000)|0x58)


@pytest.mark.parametrize('present',[False,True])
@pytest.mark.parametrize('override',[0,1,127,128,255])
def test_real_frame_command_caller_enters_key_reader_on_flag_sign_without_a_pointer_guard(original_image,memory,fields,present,override):
    """Original post-key-input prefix; stop before any target dereference."""
    m=memory;f=fields;pointer=POOL if present else 0
    write(m,f['tractor_target_reference'],pointer);m[f['tractor_input_override_flag']]=override
    cpu=state(m,0x1992);cpu.d[0]=0x12340058
    run(original_image,m,cpu,{0x354EC,0x19A4})
    if override>=128:
        assert cpu.pc==0x354EC and cpu.a[0]==pointer and cpu.a[7]==STACK-64
        assert get(m,STACK-64)==0x19A0
    else:assert cpu.pc==0x19A4 and cpu.a[7]==STACK


@pytest.mark.parametrize('spin',[0,1,0x3FFF,0x4000,0x8000,0xFFFF])
@pytest.mark.parametrize('reserves',[(0,0,0),(65535,65535,65535),(65534,32767,1),(0x1234,0xABCD,0x8000)])
def test_asteroid_pulse_uses_wrapping_word_times_four_then_unsigned_add_carry(original_image,memory,fields,spin,reserves):
    """Nonzero-low7 RNG continuation; this does not test the random selection."""
    m=memory;f=fields;write(m,POOL+36,spin,2)
    names=['icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength']
    for name,v in zip(names,reserves):write(m,f[name],v,2)
    cpu=state(m,0x35522);cpu.a[0]=POOL
    run(original_image,m,cpu,{0x3557C})
    increment=(spin*4)&65535
    assert [get(m,f[n],2)for n in names]==[min(65535,v+increment)for v in reserves]
    assert m[f['panel_fast_animation_request']]==255 and get(m,POOL+36,2)==spin


@pytest.mark.parametrize('kind',[1,3])
@pytest.mark.parametrize('key',[0x2E,0x2C,0x4D,0x9E,0x58])
@pytest.mark.parametrize('shift',[-32768,-2,-1,0,1,9,10,32767])
def test_rotation_keys_and_n_only_attraction_controls_keep_invalid_word_edges(original_image,memory,fields,kind,key,shift):
    m=memory;f=fields;write(m,POOL,kind,2)
    write(m,f['tractor_target_rotation_step'],32760,2);write(m,f['tractor_attraction_shift'],shift,2)
    expected_step=32760
    if not m[0x39536+kind]&128:
        expected_step=(expected_step+(16 if key==0x2E else-16 if key==0x2C else 0))&65535
    expected_shift=shift&65535
    if key==0x4D:
        expected_shift=(expected_shift-1)&65535
        if expected_shift&32768:expected_shift=0
    elif key==0x9E:
        expected_shift=(expected_shift+1)&65535
        if not((expected_shift-10)&32768):expected_shift=10
    cpu=state(m,0x3557C);cpu.a[0]=POOL;cpu.d[7]=key
    run(original_image,m,cpu,{0x35782})
    assert get(m,f['tractor_target_rotation_step'],2)==expected_step
    assert get(m,f['tractor_attraction_shift'],2)==expected_shift


@pytest.mark.parametrize('axis',range(3))
@pytest.mark.parametrize('distance',[2999,3000,-2999,-3000,-2147483648])
def test_collect_key_has_its_own_3000_axis_gate_before_type_and_count_tests(original_image,memory,fields,axis,distance):
    m=memory;f=fields;write(m,f['tractor_target_reference'],POOL)
    for i,n in enumerate(['player_world_x','player_world_y','player_world_z']):
        write(m,f[n],0);write(m,POOL+4+4*i,distance if i==axis else 0)
    cpu=state(m,0x355D2);cpu.d[0]=ord('C')
    run(original_image,m,cpu,{0x3562C,0x3564E})
    assert cpu.pc==(0x3562C if distance in [3000,-3000,-2147483648]else 0x3564E)


@pytest.mark.parametrize('kind',[12,91])
@pytest.mark.parametrize('count',[3,4,127,128,255])
def test_projectile_collection_count_is_a_signed_byte_comparison_not_a_global_cap(original_image,memory,fields,kind,count):
    m=memory;f=fields;write(m,POOL,kind,2)
    entry=0x3570C if kind==12 else 0x3572C
    call=0x35720 if kind==12 else 0x35740
    next_count=(count+1)&255;accepted=signed(next_count,8)<=4
    m[f['model_type_population_counts']+kind]=count
    cpu=state(m,entry);cpu.a[0]=POOL;cpu.a[1]=f['model_type_population_counts'];cpu.d[0]=kind
    run(original_image,m,cpu,{call,0x3576E})
    assert cpu.pc==(call if accepted else 0x3576E)
    assert m[f['model_type_population_counts']+kind]==(next_count if accepted else count)
    assert get(m,POOL,2)==kind  # Stop before the HUD helper and common retirement.


@pytest.mark.parametrize('inside',[0,1,128,255])
@pytest.mark.parametrize('enabled',[0,128])
@pytest.mark.parametrize('population',[0,1])
def test_type98_collection_preserves_phase_dependent_a1_write_destination(original_image,memory,fields,inside,enabled,population):
    """Supplied collection-prefix inputs; no normal-game reachability claim."""
    m=memory;f=fields;write(m,POOL,98,2)
    # The actual initial collect byte is nonnegative; keep that source input.
    assert m[0x39536+98]<128
    m[f['inside_structure_flag']]=inside;m[f['neutron_bomb_collection_enabled_flag']]=enabled
    m[f['model_type_population_counts']+98]=population
    delivered=f['taymar_delivered_model_counts_prefix']
    m[delivered:delivered+104]=b'\xA5'*104
    for n in ['neutron_bomb_ready_flag','neutron_bomb_order_requested_flag',
              'bomb_ingredient_set_complete_flag']:m[f[n]]=255
    m[f['weapon_selection_and_status']]=16
    m[f['neutron_bomb_spawn_request']]=0;m[f['neutron_bomb_retract_request']]=255
    is_inside=inside>=128;accepted=not is_inside or(population==0 and enabled>=128)
    destination=(delivered+104 if is_inside else 0x39536)+98
    before_destination=m[destination]
    cpu=state(m,0x3567A);cpu.a[0]=POOL
    run(original_image,m,cpu,{0x356DE,0x3576E})
    assert cpu.pc==(0x356DE if accepted else 0x3576E)
    assert m[destination]==(1 if accepted else before_destination)
    assert m[f['model_type_population_counts']+98]==population
    assert bytes(m[delivered:delivered+104])==(bytes(104)if accepted and is_inside else b'\xA5'*104)
    assert [m[f[n]]for n in ['neutron_bomb_ready_flag','neutron_bomb_order_requested_flag',
                            'bomb_ingredient_set_complete_flag']]==([0]*3 if accepted and is_inside else[255]*3)
    assert m[f['neutron_bomb_spawn_request']]==(255 if accepted else 0)
    assert m[f['neutron_bomb_retract_request']]==(0 if accepted else 255)
    # Do not relabel A1+$62 as a population field: neither admitted path has
    # that base. One writes source collect flags; the other a later app byte.
