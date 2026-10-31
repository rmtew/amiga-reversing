"""Original steered-update CPU cases with supplied readable records.

No normal-game reachability, target ownership, deallocation or scanout proof.
Heading retains full DIVS numerator registers and wrapped WORD differences.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, RETURN
from tests.test_starglider2_scan_acquisition import signed16, project

OBJECT,TARGET=INPUT+0x200,INPUT+0x400
CONTINUE=0x81D2


def signed32(x):return (x+0x80000000)%0x100000000-0x80000000


def setup(memory,tracking=255,budget=20,target=TARGET,phase=255,kind=2,cadence=0):
    memory[OBJECT:OBJECT+68]=b'\xCC'*68
    for off,v in [(0,12),(36,budget),(38,cadence),(18,1234),(32,900),(44,65533),(46,4),(48,65531),(50,100),(54,200)]:put(memory,OBJECT+off,v,2)
    for off,v in [(4,0x10002),(8,(-100)&0xFFFFFFFF),(12,0x20003),(60,target)]:put(memory,OBJECT+off,v)
    memory[OBJECT+34]=tracking;memory[OBJECT+30]=255;memory[OBJECT+3]=0
    put(memory,TARGET,kind,2);memory[TARGET+30]=phase;put(memory,TARGET+8,(-400)&0xFFFFFFFF)
    put(memory,TARGET+50,0,2);put(memory,TARGET+54,0,2)
    put(memory,APP+0x6FC,0xFFFF);put(memory,APP+0x708,(-200)&0xFFFFFFFF);put(memory,APP+0x700,TARGET)


def install(image,memory):
    cpu=state(memory,0x1F0E);run(image,memory,cpu,{RETURN})


def update(image,memory,entry=0x9694,d1_upper=0):
    cpu=state(memory,entry);cpu.a[0]=OBJECT;cpu.d[1]=d1_upper
    run(image,memory,cpu,{CONTINUE});return cpu


def heading(memory,x,z,tx,tz,upper0=0,upper1=0):
    x,z,tx,tz=map(signed16,[x,z,tx,tz]);q=(2 if x>=tx else 3)if z>=tz else(1 if x>=tx else 4)
    dx,dz=map(signed16,[x-tx,z-tz]);dx=signed16(-dx)if dx<0 else dx;dz=signed16(-dz)if dz<0 else dz
    def divword(upper,low,divisor):
        numerator=signed32((upper&0xFFFF0000)|(low&65535))
        quotient=(abs(numerator)//abs(divisor))*(-1 if(numerator<0)!=(divisor<0)else 1)
        return signed16(low)if not -32768<=quotient<=32767 else quotient
    if dz==0:return 1024 if q==1 else 3072
    if dx==0:return 0 if q==1 else 2048
    if dx>dz:
        ratio=divword(upper0,dx,dz)
        if ratio>=255:return 1024 if q==1 else 3072
        a=get(memory,0x13D5C+2*(ratio&255),2)
        return [a,2048-a,2048+a,4096-a][q-1]&65535
    ratio=divword(upper1,dz,dx)
    if ratio>=255:return 0 if q==1 else 2048
    a=get(memory,0x13D5C+2*(ratio&255),2)
    return [1024-a,1024+a,3072-a,3072+a][q-1]&65535


@pytest.mark.parametrize('tracking',[0,255])
@pytest.mark.parametrize('budget',[0,1,2,32767,32768,65535])
def test_signed_and_unsigned_update_budget_tests_remain_distinct(original_image,memory,tracking,budget):
    setup(memory,tracking,budget);install(original_image,memory)
    update(original_image,memory)
    retired=(budget<=1)if tracking else signed16(budget)<=1
    assert memory[OBJECT+30]==(0 if retired else 255)
    assert get(memory,OBJECT+36,2)==(budget-1)&65535
    assert get(memory,OBJECT,2)==12 and get(memory,OBJECT+60)==TARGET


@pytest.mark.parametrize('target',[0,0x80000000,0xFFFFFFFF])
@pytest.mark.parametrize('budget',[0,1,400])
def test_null_or_negative_reference_skips_budget_after_motion(original_image,memory,target,budget):
    setup(memory,budget=budget,target=target);update(original_image,memory)
    assert get(memory,OBJECT+36,2)==budget and get(memory,OBJECT+38,2)==0
    assert memory[OBJECT+30]==255 and get(memory,OBJECT+60)==target
    assert [get(memory,OBJECT+off)for off in [4,8,12]]==[65535,(-96)&0xFFFFFFFF,65534]


@pytest.mark.parametrize('kind,phase',[(0,255),(1,0),(1,127),(65535,128),(65535,255)])
def test_target_local_checks_are_not_owner_or_type_directory_bounds(original_image,memory,kind,phase):
    setup(memory,kind=kind,phase=phase);install(original_image,memory);update(original_image,memory)
    rejected=kind==0 or phase<128
    assert memory[OBJECT+30]==(0 if rejected else 255)
    assert get(memory,OBJECT+36,2)==(20 if rejected else 19)


@pytest.mark.parametrize('tracking',[0,255])
@pytest.mark.parametrize('world_y,target_y',[(0,0),(-100,-400),(-1701,-1701),(-1700,-1700),(-9,100),(0x7FFFFFFF,-1),(-0x80000000,0x7FFFFFFF)])
def test_original_y_smoothing_and_n_only_threshold_checks(original_image,memory,tracking,world_y,target_y):
    setup(memory,tracking=tracking,cadence=0);install(original_image,memory)
    put(memory,OBJECT+8,world_y&0xFFFFFFFF);put(memory,TARGET+8,target_y&0xFFFFFFFF);put(memory,APP+0x708,target_y&0xFFFFFFFF)
    integrated=(world_y+4)&0xFFFFFFFF;shift=5 if tracking else 2
    y=(integrated+(signed32(target_y-integrated)>>shift))&0xFFFFFFFF
    retired=False
    if tracking:
        if signed32(y+10)>=0:y=(-10)&0xFFFFFFFF
    else:retired=signed32(y+1700)<0
    update(original_image,memory)
    assert get(memory,OBJECT+8)==y and memory[OBJECT+30]==(0 if retired else 255)


@pytest.mark.parametrize('cadence',[0,1,6,7,8,65535])
@pytest.mark.parametrize('upper',[0,0xFFFF0000,0x12340000])
def test_heading_cadence_and_velocity_use_stored_xz_not_world_coordinates(original_image,memory,cadence,upper):
    setup(memory,cadence=cadence);install(original_image,memory)
    x,z,tx,tz=100,200,0,0
    delta=signed32(-400-(-96))>>5
    angle=heading(memory,x,z,tx,tz,delta,upper)&4095 if((cadence+1)&7)==0 else 1234
    sine,cosine=get(memory,APP+0x44),get(memory,APP+0x48)
    expected=[(-project(900,get(memory,sine+2*angle,2)))&65535,project(900,get(memory,cosine+2*angle,2))&65535]
    update(original_image,memory,d1_upper=upper)
    assert get(memory,OBJECT+38,2)==(cadence+1)&7 and get(memory,OBJECT+18,2)==angle
    assert [get(memory,OBJECT+off,2)for off in [44,48]]==expected
    assert get(memory,OBJECT+46,2)==4


@pytest.mark.parametrize('coords',[(100,200,0,0),(-100,200,0,0),(100,-200,0,0),(-100,-200,0,0),(200,100,0,0),(0,200,0,0),(200,0,0,0),(0,0,0,0),(-32768,1,0,0)])
@pytest.mark.parametrize('upper0,upper1',[(0,0),(0xFFFF0000,0xFFFF0000),(0x12340000,0x12340000)])
def test_heading_retains_upper_word_divs_numerators(original_image,memory,coords,upper0,upper1):
    setup(memory);x,z,tx,tz=coords
    for a,off,v in [(OBJECT,50,x),(OBJECT,54,z),(TARGET,50,tx),(TARGET,54,tz)]:put(memory,a+off,v&65535,2)
    expected=heading(memory,*coords,upper0,upper1)
    cpu=state(memory,0xAF9C);cpu.a[0]=OBJECT;cpu.a[4]=TARGET;cpu.d[0]=upper0;cpu.d[1]=upper1
    run(original_image,memory,cpu,{RETURN});assert cpu.d[1]&65535==expected


@pytest.mark.parametrize('variant',[0,3,4,5,254,255])
def test_animation_resets_exactly_five_not_general_modulo_five(original_image,memory,variant):
    setup(memory,target=0);memory[OBJECT+3]=variant;update(original_image,memory,entry=0x967A)
    value=(variant+1)&255
    assert memory[OBJECT+3]==(0 if value==5 else value)
