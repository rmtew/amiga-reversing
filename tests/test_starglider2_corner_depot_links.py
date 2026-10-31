"""Original corner/depot clamps and orientation-specific linked contact effects.

Supplied readable records, conditional profiles and flat CPU state do not prove
normal-game lifetime, arbitrary selectors, linked-chain termination or hardware.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK, RETURN
from tests.test_starglider2_scan_acquisition import signed16
from tests.test_starglider2_homing_updates import signed32
from tests.test_starglider2_structure_profiles import setup, expected as profile_expected, STRUCT, OBJECT

LINK=INPUT+0x700


def player_position(memory,position):
    for off,v in zip([0x704,0x708,0x70C],position):put(memory,APP+off,v&0xFFFFFFFF)


def object_position(memory,position):
    for off,v in zip([4,8,12],position):put(memory,OBJECT+off,v&0xFFFFFFFF)


def corner_bounds(orientation,delta,player):
    factor,base=(17,401)if player else(19,501)
    width=factor*signed16(delta)
    width=(abs(width)>>6)if player else(width>>6)
    z=20000+3120-delta if orientation else 20000-3120+delta
    return 10000-base-width,10000+base+width,z


def corner_expected(x,y,lower,upper,kind=None):
    x=signed32(x);velocity=65535;retired=False;side='none'
    if upper<x:
        x=upper+(500 if kind is None else 550);side='upper'
        if kind in [84,103]:velocity=1
    elif not lower<x:
        x=lower-500;side='lower';retired=kind==103
    low,low_out,high,high_out=(-590,-589,-410,-411)if kind is None else(-2768,-2760,0,-4)
    y=signed32(y);yclamp=False
    if y<=low:y=low_out;yclamp=True
    elif y>high:y=high_out;yclamp=True
    return x&0xFFFFFFFF,y&0xFFFFFFFF,velocity,retired,yclamp,side


@pytest.mark.parametrize('orientation',[0,1,65535])
@pytest.mark.parametrize('delta',[-65537,-1,0,1,65535,65536,65537])
@pytest.mark.parametrize('edge',range(5))
def test_player_corner_uses_absolute_17_word_slope_and_original_pushouts(original_image,memory,orientation,delta,edge):
    setup(memory);put(memory,STRUCT,92,2);put(memory,STRUCT+18,orientation,2)
    lower,upper,z=corner_bounds(orientation,delta,True);x=[lower-1,lower,lower+1,upper,upper+1][edge]
    player_position(memory,(x,-500,z));cpu=state(memory,0xBC9A);cpu.a[2]=STRUCT;run(original_image,memory,cpu,{RETURN})
    ex,ey,_,_,_,side=corner_expected(x,-500,lower,upper)
    assert(get(memory,APP+0x704),get(memory,APP+0x708),get(memory,APP+0x70C))==(ex,ey,z&0xFFFFFFFF)
    assert memory[APP+0x7E4]==(0 if side=='none'else 255)


@pytest.mark.parametrize('orientation',[0,1])
@pytest.mark.parametrize('delta',[-65536,-100,0,100,65536])
@pytest.mark.parametrize('kind',[1,84,103])
@pytest.mark.parametrize('edge',range(5))
def test_object_corner_retains_signed_19_word_slope_and_branch_specific_effects(original_image,memory,orientation,delta,kind,edge):
    setup(memory,kind=kind);put(memory,STRUCT,92,2);put(memory,STRUCT+18,orientation,2)
    lower,upper,z=corner_bounds(orientation,delta,False);x=[lower-1,lower,lower+1,upper,upper+1][edge]
    object_position(memory,(x,-1000,z));put(memory,OBJECT+44,65535,2)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;cpu.a[6]=0x171FC
    old_d,old_a=list(cpu.d),list(cpu.a);run(original_image,memory,cpu,{0xB8F8})
    ex,ey,vx,retired,_,_=corner_expected(x,-1000,lower,upper,kind)
    assert(get(memory,OBJECT+4),get(memory,OBJECT+8),get(memory,OBJECT+12))==(ex,ey,z&0xFFFFFFFF)
    assert get(memory,OBJECT+44,2)==vx and memory[OBJECT+30]==(0 if retired else 255)
    assert list(cpu.d)==old_d and list(cpu.a)==old_a


@pytest.mark.parametrize('kind',[1,84,103])
@pytest.mark.parametrize('y',[-2768,1])
@pytest.mark.parametrize('edge',['lower','upper'])
def test_corner_side_effects_precede_shared_y_clamp(original_image,memory,kind,y,edge):
    setup(memory,kind=kind);put(memory,STRUCT,92,2)
    lower,upper,z=corner_bounds(0,0,False);x=lower if edge=='lower'else upper+1
    object_position(memory,(x,y,z));put(memory,OBJECT+44,65535,2)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;run(original_image,memory,cpu,{0xB8F8})
    ex,ey,vx,retired,_,_=corner_expected(x,y,lower,upper,kind)
    assert get(memory,OBJECT+4)==ex and get(memory,OBJECT+8)==ey
    assert get(memory,OBJECT+44,2)==vx and get(memory,OBJECT+46,2)==(1 if kind in [84,103]else 65535)
    assert memory[OBJECT+30]==(0 if retired else 255)


@pytest.mark.parametrize('selector',[0,1])
@pytest.mark.parametrize('service',[0,10,255])
@pytest.mark.parametrize('delta',[574,575,576,65536+576,-65536+576,-1,32768])
def test_player_depot_uses_low_word_575_and_same_positive_snap_for_both_tests(original_image,memory,selector,service,delta):
    setup(memory,selector);put(memory,STRUCT,94,2);memory[STRUCT+38]=service
    z=20000-delta if selector else 20000+delta;player_position(memory,(10000,-500,z))
    put(memory,APP+0x6D8,0xCAFE,2);cpu=state(memory,0xBD02);cpu.a[2]=STRUCT
    run(original_image,memory,cpu,{0xBAE0})
    snap=signed16(delta)>575
    assert get(memory,APP+0x6C2,2)==service
    assert get(memory,APP+0x70C)==((20570 if snap else z)&0xFFFFFFFF)
    assert memory[APP+0x7CE]==(255 if snap else 0)and memory[APP+0x7CF]==(3 if snap else 0)
    assert get(memory,APP+0x6D8,2)==(63 if snap and not selector else 0xCAFE)


@pytest.mark.parametrize('selector',range(6))
@pytest.mark.parametrize('delta',[575,576])
def test_player_depot_continues_through_conditional_wide_profile(original_image,memory,selector,delta):
    setup(memory,selector);put(memory,STRUCT,94,2);memory[STRUCT+38]=10
    z=20000-delta if selector else 20000+delta;player_position(memory,(10000,-500,z))
    if delta>575:z=20570
    expected=profile_expected(memory,selector,0,(10000,-500,z),True)[0]
    cpu=state(memory,0xBD02);cpu.a[2]=STRUCT;run(original_image,memory,cpu,{RETURN})
    assert tuple(get(memory,APP+off)for off in [0x704,0x708,0x70C])==expected


@pytest.mark.parametrize('kind',[1,84,103])
@pytest.mark.parametrize('delta',[454,455,456,65536+456,-65536+456,-1,32768])
@pytest.mark.parametrize('velocity',[1,65535,32768])
def test_object_depot_reverses_z_word_before_profile_for_all_types(original_image,memory,kind,delta,velocity):
    setup(memory,kind=kind);put(memory,STRUCT,94,2);object_position(memory,(10000,-1000,20000+delta));put(memory,OBJECT+48,velocity,2)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;run(original_image,memory,cpu,{0xBFEC})
    snap=signed16(delta)>455
    assert get(memory,OBJECT+12)==((20450 if snap else 20000+delta)&0xFFFFFFFF)
    assert get(memory,OBJECT+48,2)==((-velocity)&65535 if snap else velocity)


@pytest.mark.parametrize('selector',range(6))
@pytest.mark.parametrize('kind',[1,84,103])
@pytest.mark.parametrize('delta',[455,456])
def test_object_depot_and_profile_velocity_reversals_remain_separate(original_image,memory,selector,kind,delta):
    setup(memory,selector,kind=kind);put(memory,STRUCT,94,2);object_position(memory,(10000,-1000,20000+delta));put(memory,OBJECT+44,100,2);put(memory,OBJECT+48,100,2)
    snap=delta>455;position=(10000,-1000,20450 if snap else 20000+delta)
    expected,axis,clamped,_=profile_expected(memory,selector,0,position,False)
    velocity=[100,65535,(-100)&65535 if snap else 100]
    if kind in [84,103]and clamped:
        i=0 if axis=='x'else 2;velocity[i]=(-velocity[i])&65535
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;run(original_image,memory,cpu,{0xB8F8})
    assert tuple(get(memory,OBJECT+off)for off in [4,8,12])==expected
    assert [get(memory,OBJECT+off,2)for off in [44,46,48]]==velocity


def linked_setup(memory,orientation,delta,link_type,actor=30):
    setup(memory,kind=actor);put(memory,STRUCT,93,2);memory[STRUCT+2]=0;memory[STRUCT+28]=128;put(memory,STRUCT+18,orientation,2)
    position=(10000+delta,-1000,20000)if orientation else(10000,-1000,20000+delta)
    object_position(memory,position);put(memory,STRUCT+56,0 if link_type is None else LINK)
    memory[LINK:LINK+68]=b'\xCC'*68
    if link_type is not None:put(memory,LINK,link_type,2)
    return bytes(memory[LINK:LINK+68])


@pytest.mark.parametrize('orientation',[0,1])
@pytest.mark.parametrize('delta',[1799,1800,1801])
@pytest.mark.parametrize('link_type',[None,0,1,90])
def test_linked_type93_orientations_keep_distinct_guards_and_mutations(original_image,memory,orientation,delta,link_type):
    before=linked_setup(memory,orientation,delta,link_type)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;cpu.a[6]=0x171FC
    old_d,old_a=list(cpu.d),list(cpu.a);run(original_image,memory,cpu,{0xB8F8})
    expected=bytearray(before)
    if delta>=1800 and link_type is not None:
        if not orientation and link_type==90:expected[3]=0;expected[34]=255;expected[40]=255
        elif orientation and link_type!=0:expected[60:64]=b'\0'*4
    assert bytes(memory[LINK:LINK+68])==expected
    assert get(memory,APP+0x6F0)==(1 if delta>=1800 else 0)
    assert list(cpu.d)==old_d and list(cpu.a)==old_a


@pytest.mark.parametrize('orientation',[0,1])
@pytest.mark.parametrize('actor',[4,90,93,96,97])
def test_linked_type93_excluded_actors_skip_mutation_and_common_hit(original_image,memory,orientation,actor):
    before=linked_setup(memory,orientation,1801,90,actor)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;run(original_image,memory,cpu,{0xB8F8})
    assert bytes(memory[LINK:LINK+68])==before and get(memory,APP+0x6F0)==0


@pytest.mark.parametrize('kind',[63,65])
@pytest.mark.parametrize('variant',[0,3,4,6,9,128,255])
@pytest.mark.parametrize('durability',[1,128])
def test_object_gate_variants_keep_signed_blast_door_and_exact_energy_gate_rules(original_image,memory,kind,variant,durability):
    setup(memory);put(memory,STRUCT,kind,2);memory[STRUCT+3]=variant;memory[STRUCT+28]=durability
    common=(variant if variant<128 else variant-256)<=3 if kind==63 else variant!=6
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;run(original_image,memory,cpu,{0xB8F8})
    assert memory[STRUCT+28]==(0 if common and durability==1 else durability)
    assert memory[STRUCT+30]==(0 if common and durability==1 else 255)
    assert memory[OBJECT+30]==(0 if common and durability==1 else 255)
