"""Original fixed-point motion and space continuations with supplied RAM.

Lookup words/backing and entry states are explicit. No universal pointer/angle
ownership, physical velocity units or complete gameplay equivalence is claimed.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,RETURN
from tests.test_starglider2_control_normalization import signed,word,guard

SINE,COS=0x80000,0x83000
SPACE,FIELD,BONUS,STAR,SPEED,TARGET,COLLISION=0x77D,0xA9D,0xA74,0x9AE,0x75A,0x758,0x7CE
GRAY,SOUND,DIAG=0x39CDE,0xBB6,0xE103
WORLD=[0x704,0x708,0x70C];MOTION=[0x74A,0x74C,0x74E]


def doubled_product_swap(a,b):
    v=(signed(a)*signed(b)*2)&0xFFFFFFFF
    return((v&65535)<<16)|(v>>16)

def neg_word(v):return(v&0xFFFF0000)|((-v)&65535)

@pytest.fixture
def tables(memory):
    m=memory
    for i in range(4096):
        put(m,SINE+2*i,(i*109+0x1234)&65535,2)
        put(m,COS+2*i,(i*257+0x8000)&65535,2)
    put(m,APP+0x44,SINE);put(m,APP+0x48,COS)
    return m


def expected_vector(m,angles,speed):
    a0,a1,a2=[a&4095 for a in angles]
    s0,c0,s1,c1,s2=[get(m,table+2*i,2)for table,i in [(SINE,a0),(COS,a0),(SINE,a1),(COS,a1),(SINE,a2)]]
    x=neg_word(doubled_product_swap(doubled_product_swap(speed,s1),c0))
    y=neg_word(doubled_product_swap(speed,s0))
    z=doubled_product_swap(doubled_product_swap(speed,c1),c0)
    return [x,y,z],[s0,c0,s1,c1,s2]


def vector(image,m,entry,angles,speed):
    for off,v in zip([0x744,0x746,0x748],angles):word(m,off,v)
    for off,v in zip([16,18,20],angles):put(m,INPUT+off,v&65535,2)
    before=bytes(m[APP:APP+0x1000]);cpu=state(m,entry);cpu.d[3]=0xABCD0000|(speed&65535)
    regs=list(cpu.d);addresses=list(cpu.a);run(image,m,cpu,{RETURN})
    (x,y,z),(s0,c0,s1,c1,s2)=expected_vector(m,angles,speed)
    assert list(cpu.d[4:7])==[x,y,z]
    assert [get(m,APP+off,2)for off in range(0x164,0x16E,2)]==[s0,c0,s1,c1,s2]
    assert [cpu.d[i]for i in [0,1,2,3,7]]==[regs[i]for i in [0,1,2,3,7]]
    assert [cpu.a[i]for i in [0,2,4,5,6]]==[addresses[i]for i in [0,2,4,5,6]]
    assert cpu.a[1]==COS and cpu.a[3]==SINE and cpu.a[7]==addresses[7]+4
    guard(m,before,[(0x164,10)])
    return [x&65535,y&65535,z&65535]


@pytest.mark.parametrize('entry',[0x37264,0x37280])
@pytest.mark.parametrize('angle',[0,1,1023,1024,2047,2048,4095,4096,32768,65535])
@pytest.mark.parametrize('speed',[-32768,-1,0,1,32767])
def test_object_and_player_entries_share_masked_index_and_staged_products(original_image,tables,entry,angle,speed):
    vector(original_image,tables,entry,[angle,(angle*3+1024)&65535,(angle*5+1)&65535],speed)


@pytest.mark.parametrize('coefficient',[-32768,-32767,-1,0,1,32767])
@pytest.mark.parametrize('speed',[-32768,-1,0,1,32767])
def test_each_multiply_doubles_wraps_and_swaps_before_the_next_word_use(original_image,tables,coefficient,speed):
    m=tables
    for table in [SINE,COS]:put(m,table,coefficient&65535,2)
    vector(original_image,m,0x37280,[0,0,0],speed)


def test_rotation2_changes_only_its_sine_scratch_not_motion_components(original_image,tables):
    m=tables;expected=None
    for phase in [0,1,1024,2048,4095,65535]:
        result=vector(original_image,m,0x37280,[513,2047,phase],32767)
        if expected is None:expected=result
        assert result==expected


def integrate_expected(world,motion,mask,collision):
    delta=[signed(v)*2 for v in motion]
    result=[(v-d if collision&128 else v+d)&0xFFFFFFFF for v,d in zip(world,delta)]
    result[0]&=mask;result[2]&=mask
    return result


@pytest.mark.parametrize('bonus',[-32768,-1,0,299,300,15900,15999,16000,16001,32767])
@pytest.mark.parametrize('speed',[0,1,299,300,-32768])
@pytest.mark.parametrize('enabled',[0,1,65535])
@pytest.mark.parametrize('field',[0,127,128,255])
@pytest.mark.parametrize('space',[0,128])
def test_space_gate_notice_before_acceleration_and_n_only_word_limits(original_image,memory,bonus,speed,enabled,field,space):
    m=memory
    for off,value in [(BONUS,bonus),(SPEED,speed),(STAR,enabled),(TARGET,0x1234)]:word(m,off,value)
    m[APP+FIELD]=field;m[APP+SPACE]=space;m[APP+SOUND]=0x55;put(m,GRAY,0x1234,2)
    world=[0x7FFFFFFF,0xFFFFFFFF,0x80000000];motion=[-32768,-1,32767];mask=0x00FFFFFF
    for off,v in zip(WORLD,world):put(m,APP+off,v)
    for off,v in zip(MOTION,motion):word(m,off,v)
    put(m,APP+0x6FC,mask);before=bytes(m[APP:APP+0x1000])
    new_bonus=bonus&65535;new_field=field;gray=0x1234;sound=0x55
    if space&128:
        if field&128:
            if signed(bonus-16000)<0 or signed(speed-300)<0:new_field=255
            else:new_field=0;gray=15;sound=255
        if not(speed&65535) or not enabled:
            new_field=255;new_bonus=(bonus-300)&65535
            if signed(new_bonus)<0:new_bonus=0
        else:
            new_bonus=(bonus+100)&65535
            if signed(new_bonus-16000)>=0:new_bonus=16000
        world=integrate_expected(world,motion,mask,0)
    cpu=state(m,0x33FF8);run(original_image,m,cpu,{0x340AC})
    assert m[DIAG]==5 and get(m,GRAY,2)==gray and m[APP+SOUND]==sound
    assert get(m,APP+BONUS,2)==new_bonus and m[APP+FIELD]==new_field
    assert [get(m,APP+off)for off in WORLD]==world
    guard(m,before,[(BONUS,2),(FIELD,1),(SOUND,1)]+[(off,4)for off in WORLD])


@pytest.mark.parametrize('motion',[(0,0,0),(-32768,-1,32767),(32767,-32768,1),(-1,1,-1)])
@pytest.mark.parametrize('mask',[0,65535,0xFFFFFF,0xFFFFFFFF,0x80000001])
@pytest.mark.parametrize('collision',[0,1,127,128,255])
def test_movem_word_sign_extension_reverse_then_horizontal_only_wrap(original_image,memory,motion,mask,collision):
    m=memory;world=[0x7FFFFFFF,0xFFFFFFFF,0x80000000]
    for off,v in zip(WORLD,world):put(m,APP+off,v)
    for off,v in zip(MOTION,motion):word(m,off,v)
    put(m,APP+0x6FC,mask);m[APP+COLLISION]=collision
    word(m,TARGET,0x1234);word(m,SPEED,0x5678);before=bytes(m[APP:APP+0x1000])
    cpu=state(m,0x3406C);run(original_image,m,cpu,{0x340AC})
    assert [get(m,APP+off)for off in WORLD]==integrate_expected(world,motion,mask,collision)
    assert get(m,APP+TARGET,2)==(0 if collision&128 else 0x1234)
    assert get(m,APP+SPEED,2)==(0 if collision&128 else 0x5678)
    guard(m,before,[(off,4)for off in WORLD]+[(TARGET,2),(SPEED,2)])

@pytest.mark.parametrize('phase',[0,1,1024,4095,65535])
@pytest.mark.parametrize('speed,bonus',[(0,0),(1,16000),(479,16000),(32767,32767),(-32768,-1)])
@pytest.mark.parametrize('collision',[0,255])
def test_actual_caller_builds_wrapped_speed_vector_then_original_integration(original_image,tables,phase,speed,bonus,collision):
    m=tables;angles=[phase,(phase+1024)&65535,(phase+2048)&65535]
    for off,v in zip([0x744,0x746,0x748],angles):word(m,off,v)
    word(m,SPEED,speed);word(m,BONUS,bonus);word(m,TARGET,0x1234)
    expected,_=expected_vector(m,angles,(speed+bonus)&65535)
    world=[0x7FFFFFFF,0xFFFFFFFF,0x80000000];mask=0xFFFFFF
    for off,v in zip(WORLD,world):put(m,APP+off,v)
    put(m,APP+0x6FC,mask);m[APP+COLLISION]=collision
    before=bytes(m[APP:APP+0x1000]);cpu=state(m,0x2F700)
    run(original_image,m,cpu,{0x2F71C})  # actual BSR, RTS and three original WORD stores
    assert [get(m,APP+off,2)for off in MOTION]==[v&65535 for v in expected]
    guard(m,before,[(0x164,10)]+[(off,2)for off in MOTION])
    # A separate supplied consumer context; intervening game writers are not proved absent.
    cpu=state(m,0x3406C);run(original_image,m,cpu,{0x340AC})
    assert [get(m,APP+off)for off in WORLD]==integrate_expected(world,expected,mask,collision)

@pytest.mark.parametrize('collision',[128,255])
def test_collision_clears_speed_after_current_ramp_then_next_call_decays(original_image,memory,collision):
    m=memory;m[APP+SPACE]=128;m[APP+COLLISION]=collision
    word(m,STAR,1);word(m,SPEED,1);word(m,BONUS,100);word(m,TARGET,7)
    put(m,APP+0x6FC,0xFFFFFF)
    cpu=state(m,0x33FF8);run(original_image,m,cpu,{0x340AC})
    assert get(m,APP+BONUS,2)==200 and get(m,APP+SPEED,2)==get(m,APP+TARGET,2)==0
    cpu=state(m,0x33FF8);run(original_image,m,cpu,{0x340AC})
    assert get(m,APP+BONUS,2)==0 and m[APP+FIELD]==255
