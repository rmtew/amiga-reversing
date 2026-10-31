"""Original structure selection, six-way profiles and two variant-gated contacts.

Supplied records/backing and conditional selectors 0..5 are not global lifetime,
constructor-bound, arbitrary-input or hardware/gameplay guarantees.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK, RETURN
from tests.test_starglider2_scan_acquisition import signed16
from tests.test_starglider2_homing_updates import signed32
from tests.test_starglider2_contact_eligibility import player_setup, response

STRUCT,OBJECT,LIST=INPUT+0x500,INPUT+0x200,INPUT+0x900
TABLES=[(0xC43C,0xC454),(0xC46C,0xC484)]


def setup(memory,selector=0,family=0,kind=1):
    for a,t in [(STRUCT,66 if family==0 else 67),(OBJECT,kind)]:
        memory[a:a+68]=b'\0'*68;put(memory,a,t,2);memory[a+30]=255
    memory[STRUCT+2]=64;put(memory,STRUCT+40,selector,2)
    put(memory,STRUCT+4,10000);put(memory,STRUCT+12,20000)
    put(memory,0x27A8,APP);put(memory,APP+0x700,OBJECT);put(memory,APP+0x6FC,0xFFFF)
    memory[APP+0x7E4]=0
    for off,v in [(44,32768),(46,65535),(48,1)]:put(memory,OBJECT+off,v,2)


def centre(memory,selector,family,cross):
    tx,tz=TABLES[family];x=signed32(10000+get(memory,tx+4*selector));z=signed32(20000+get(memory,tz+4*selector))
    if selector<=2:
        correction=0 if selector==0 else signed32(cross-z)
        if selector==2:correction=signed32(-correction)
        if selector:correction=signed16(correction>>1)
        return signed32(x+correction),'x'
    correction=0 if selector==4 else signed32(cross-x)
    if selector!=3 and selector!=4:correction=signed32(-correction)
    if selector!=4:correction>>=1
    return signed32(z+correction),'z'


def expected(memory,selector,family,position,player):
    x,y,z=map(signed32,position);target,axis=centre(memory,selector,family,z if selector<=2 else x)
    difference=signed32(target-(x if axis=='x'else z));radius=500 if player else 550
    clamped=False
    if difference>=radius+1 or difference<=-radius-1:
        value=signed32(target+radius if difference<0 else target-radius)
        if axis=='x':x=value
        else:z=value
        clamped=True
    low,low_out,high,high_out=(-590,-589,-410,-411)if player else(-2768,-2760,0,-4)
    yclamped=False
    if y<=low:y=low_out;yclamped=True
    elif y>high:y=high_out;yclamped=True
    return tuple(v&0xFFFFFFFF for v in [x,y,z]),axis,clamped,yclamped


def position_at(memory,selector,family,difference,y=-500,cross=0):
    target,axis=centre(memory,selector,family,cross)
    return(target-difference,y,cross)if axis=='x'else(cross,y,target-difference)


def player_call(image,memory,selector,family,position):
    for off,v in zip([0x704,0x708,0x70C],position):put(memory,APP+off,v&0xFFFFFFFF)
    cpu=state(memory,0xBB4A);cpu.a[2]=STRUCT;cpu.a[1],cpu.a[3]=TABLES[family]
    run(image,memory,cpu,{RETURN})
    return tuple(get(memory,APP+off)for off in [0x704,0x708,0x70C])


@pytest.mark.parametrize('family',range(2))
@pytest.mark.parametrize('selector',range(6))
@pytest.mark.parametrize('difference',[-501,-500,0,500,501])
def test_player_profile_keeps_500_units_with_inclusive_thresholds(original_image,memory,family,selector,difference):
    setup(memory,selector,family);position=position_at(memory,selector,family,difference)
    result,_,clamped,yclamped=expected(memory,selector,family,position,True)
    assert player_call(original_image,memory,selector,family,position)==result
    assert memory[APP+0x7E4]==(255 if clamped or yclamped else 0)


@pytest.mark.parametrize('family',range(2))
@pytest.mark.parametrize('selector',[1,2,3,5])
@pytest.mark.parametrize('cross',[-65537,-65536,-1,0,1,65535,65536,65537])
def test_only_x_oriented_slope_truncates_shifted_correction_to_word(original_image,memory,family,selector,cross):
    setup(memory,selector,family);position=position_at(memory,selector,family,1000,cross=cross)
    assert player_call(original_image,memory,selector,family,position)==expected(memory,selector,family,position,True)[0]


@pytest.mark.parametrize('y',[-0x80000000,-591,-590,-589,-411,-410,-409,0x7FFFFFFF])
def test_player_y_thresholds_keep_original_asymmetric_clamp_values(original_image,memory,y):
    setup(memory);position=position_at(memory,0,0,0,y=y)
    result,_,_,clamped=expected(memory,0,0,position,True)
    assert player_call(original_image,memory,0,0,position)==result
    assert memory[APP+0x7E4]==(255 if clamped else 0)


@pytest.mark.parametrize('family',range(2))
@pytest.mark.parametrize('selector',range(6))
@pytest.mark.parametrize('kind',[1,84,103])
@pytest.mark.parametrize('difference',[-551,-550,0,550,551])
def test_object_profile_uses_550_and_only_two_types_reverse_velocity(original_image,memory,family,selector,kind,difference):
    setup(memory,selector,family,kind);position=position_at(memory,selector,family,difference,y=-1000)
    result,axis,clamped,yclamped=expected(memory,selector,family,position,False)
    for off,v in zip([4,8,12],position):put(memory,OBJECT+off,v&0xFFFFFFFF)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;cpu.a[6]=0x171FC
    before_d,before_a=list(cpu.d),list(cpu.a);run(original_image,memory,cpu,{0xB8F8})
    assert tuple(get(memory,OBJECT+off)for off in [4,8,12])==result
    velocity=[32768,65535,1]
    if kind in [84,103]and clamped:
        i=0 if axis=='x'else 2;velocity[i]=(-velocity[i])&65535
    assert [get(memory,OBJECT+off,2)for off in [44,46,48]]==velocity
    assert memory[OBJECT+30]==255 and list(cpu.d)==before_d and list(cpu.a)==before_a


@pytest.mark.parametrize('kind',[1,84,103])
@pytest.mark.parametrize('y',[-0x80000000,-2769,-2768,-2760,0,1,0x7FFFFFFF])
def test_object_y_clamp_reverses_y_velocity_only_on_84_or_103(original_image,memory,kind,y):
    setup(memory,kind=kind);position=position_at(memory,0,0,0,y=y)
    for off,v in zip([4,8,12],position):put(memory,OBJECT+off,v&0xFFFFFFFF)
    expected_position,_,_,clamped=expected(memory,0,0,position,False)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;run(original_image,memory,cpu,{0xB8F8})
    assert tuple(get(memory,OBJECT+off)for off in [4,8,12])==expected_position
    assert get(memory,OBJECT+46,2)==(1 if kind in [84,103]and clamped else 65535)


@pytest.mark.parametrize('response_flag',[0,255])
@pytest.mark.parametrize('motion',[(1,2,3),(-1,-2,-3),(32767,-32768,-1)])
def test_player_prefix_doubles_sign_extended_motion_as_longs(original_image,memory,response_flag,motion):
    setup(memory);memory[APP+0x7CE]=response_flag
    start=[65535,0x7FFFFFFF,1]
    for off,v in zip([0x704,0x708,0x70C],start):put(memory,APP+off,v)
    for off,v in zip([0x74A,0x74C,0x74E],motion):put(memory,APP+off,v&65535,2)
    cpu=state(memory,0xBAFA);cpu.a[2]=STRUCT;cpu.a[1],cpu.a[3]=TABLES[0]
    run(original_image,memory,cpu,{0xBB4A})
    sign=-1 if response_flag else 1
    result=[(v+sign*2*m)&0xFFFFFFFF for v,m in zip(start,motion)];result[0]&=65535;result[2]&=65535
    assert [get(memory,APP+off)for off in [0x704,0x708,0x70C]]==result


def select(image,memory,records,fallback=OBJECT):
    put(memory,APP+0x762,len(records),2);put(memory,APP+0x6D0,LIST);put(memory,APP+0x700,OBJECT)
    put(memory,0x39CC6,123,2)  # original BA9A clears this absolute WORD latch
    for i,(type_,xyz,tag)in enumerate(records):
        a=STRUCT+96*i;put(memory,LIST+4*i,a);put(memory,a,type_,2);memory[a+37]=tag
        for off,v in zip([22,24,26],xyz):put(memory,a+off,v&65535,2)
    cpu=state(memory,0xBA14);cpu.a[2]=fallback;run(image,memory,cpu,{0xBAA0,RETURN})
    assert get(memory,0x39CC6,2)==(0 if records else 123)
    return cpu


@pytest.mark.parametrize('type_',[48,66,67,68,69,70,85,92,94])
def test_selector_recognizes_nine_original_types_and_copies_band_byte(original_image,memory,type_):
    setup(memory);cpu=select(original_image,memory,[(type_,(1,2,3),254)])
    assert cpu.a[2]==STRUCT and cpu.a[0]==OBJECT and memory[APP+0x77E]==254


@pytest.mark.parametrize('records,selected',[
    ([(66,(1,2,3),1),(67,(2,2,2),2)],1),
    ([(66,(1,1,1),1),(67,(2,2,2),2)],0),
    ([(2,(0,0,0),0),(66,(20,0,0),1)],1),
    ([(66,(1,1,1),1),(67,(-32768,0,0),2)],1),
])
def test_selector_keeps_last_tie_and_word_neg_minimum_score(original_image,memory,records,selected):
    setup(memory);cpu=select(original_image,memory,records)
    assert cpu.a[2]==STRUCT+96*selected


def test_selector_no_eligible_record_keeps_incoming_a2_and_empty_list_returns(original_image,memory):
    setup(memory);put(memory,OBJECT,99,2);memory[OBJECT+37]=7
    cpu=select(original_image,memory,[(2,(0,0,0),1)])
    assert cpu.a[2]==OBJECT and memory[APP+0x77E]==7
    cpu=select(original_image,memory,[]);assert cpu.pc==RETURN and cpu.a[2]==OBJECT


@pytest.mark.parametrize('kind,excluded',[(65,6),(63,9)])
@pytest.mark.parametrize('variant',[0,5,6,7,8,9,10,255])
@pytest.mark.parametrize('durability',[1,128])
def test_energy_gate_and_blast_door_player_contacts_only_skip_exact_variants(original_image,memory,kind,excluded,variant,durability):
    _,other=player_setup(memory,'outer',kind,durability);memory[other+3]=variant
    response(original_image,memory,'outer')
    skipped=variant==excluded
    assert get(memory,APP+0x6F0)==(0xFFFFFFFF if skipped else 0)
    assert memory[APP+0x7CF]==(0 if skipped else 3)and memory[APP+0x7CE]==(0 if skipped else 255)
    assert memory[other+30]==(0 if not skipped and durability<128 else 255)
