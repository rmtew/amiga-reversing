"""Original neutron-bomb CPU state transitions with supplied records and RAM.

No normal-game reachability, arbitrary pointer/lifetime safety, interrupt-time
serialization or hardware behavior is inferred from these isolated cases.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,RETURN
from tests.test_starglider2_scan_acquisition import signed16,project
from tests.test_starglider2_homing_updates import signed32

BOMB,STATION,OTHER,STACKLIST=INPUT+0x100,INPUT+0x200,INPUT+0x300,INPUT+0x500
OFFSET,INVENTORY=0x39122,APP+0xAE5+98


def negative32(v):return bool(v&0x80000000)


def prepare(memory):
    memory[BOMB:BOMB+68]=b'\x4C'*68;put(memory,BOMB,98,2)
    memory[BOMB+30]=255;memory[BOMB+31]=0
    put(memory,APP+0xA76,BOMB);put(memory,OFFSET,120)
    for off,v in [(0x704,10000),(0x708,-1000),(0x70C,20000)]:put(memory,APP+off,v&0xFFFFFFFF)
    for off,v in zip([0x744,0x746,0x748],[0,0,0]):put(memory,APP+off,v,2)
    put(memory,APP+0x75A,100,2);put(memory,APP+0x6FC,0xFFFF)
    memory[APP+0x77D]=128;memory[APP+0xA7E]=0
    memory[APP+0xAE3]=0;memory[APP+0xAE4]=0;memory[INVENTORY]=1
    put(memory,APP+0x7C4,0,2);put(memory,0xE080,0)


@pytest.mark.parametrize('space',[0,1,128])
@pytest.mark.parametrize('y',[-1000,-122,-121,-120,0,0x7FFFFFFF])
@pytest.mark.parametrize('vy',[-1,0,1])
def test_released_surface_double_y_step_and_n_only_ground_gate(original_image,memory,space,y,vy):
    prepare(memory);memory[BOMB+31]=255;memory[APP+0x77D]=space
    put(memory,BOMB+4,65535);put(memory,BOMB+8,y&0xFFFFFFFF);put(memory,BOMB+12,0)
    for off,v in zip([44,46,48],[1,vy&65535,65535]):put(memory,BOMB+off,v,2)
    for off,v in [(16,3),(18,123),(20,65535),(36,5)]:put(memory,BOMB+off,v,2)
    cpu=state(memory,0x36708);cpu.a[0]=BOMB;events=[]
    run(original_image,memory,cpu,{RETURN},lambda pc:events.append(pc)if pc==0x3683C else None)
    after_y=(y+vy*(1 if space>=128 else 2))&0xFFFFFFFF
    ground=space<128 and not negative32(after_y-0xFFFFFF88)
    assert get(memory,BOMB+8)==after_y and get(memory,BOMB+4)==0 and get(memory,BOMB+12)==65535
    assert events==([0x3683C]if ground else [])
    assert get(memory,BOMB+46,2)==((vy+1)&65535 if space<128 and not ground else vy&65535)
    assert get(memory,BOMB+36,2)==(5 if ground else 4)
    assert get(memory,BOMB+16,2)==(3 if ground else (3-8)&4095)
    assert get(memory,BOMB+20,2)==(65535 if ground else (65535-8)&4095)
    assert get(memory,BOMB+18,2)==123 and memory[BOMB+30]==(0 if ground else 255)


@pytest.mark.parametrize('near',[0,1,128])
@pytest.mark.parametrize('construction',[51,52,53])
@pytest.mark.parametrize('updates',[0,1,32768,65535])
def test_station_attraction_signed_rounding_and_wrapped_countdown(original_image,memory,near,construction,updates):
    prepare(memory);memory[BOMB+31]=255;memory[APP+0xA7E]=near
    put(memory,APP+0x868,construction,2);put(memory,APP+0x9B0,STATION)
    for off,v in zip([4,8,12],[1,-1000,65535]):put(memory,BOMB+off,v&0xFFFFFFFF)
    for off in [44,46,48]:put(memory,BOMB+off,0,2)
    for off,v in zip([4,8,12],[64,-2001,-64]):put(memory,STATION+off,v&0xFFFFFFFF)
    put(memory,BOMB+36,updates,2);cpu=state(memory,0x36708);cpu.a[0]=BOMB
    run(original_image,memory,cpu,{RETURN})
    expected=[1,-1000,65535]
    if near>=128 and construction!=52:
        expected=[(a-(signed32(a-b)>>5))&0xFFFFFFFF for a,b in zip(expected,[64,-2001,-64])]
    assert [get(memory,BOMB+o)for o in [4,8,12]]==[v&0xFFFFFFFF for v in expected]
    remaining=(updates-1)&65535
    assert get(memory,BOMB+36,2)==remaining and memory[BOMB+30]==(0 if remaining&32768 else 255)


@pytest.mark.parametrize('space',[0,1,128])
@pytest.mark.parametrize('reference',[0,BOMB,OTHER,0xFFFFFFFF])
@pytest.mark.parametrize('world_y',[-241,-240,-239,0x7FFFFFFF])
def test_carried_reference_is_nonnull_not_identity_and_ground_updates_requests(original_image,memory,space,reference,world_y):
    prepare(memory);memory[APP+0x77D]=space;put(memory,APP+0xA76,reference)
    put(memory,APP+0x708,world_y&0xFFFFFFFF)
    for off,v in zip([0x744,0x746,0x748],[65535,4097,32768]):put(memory,APP+off,v,2)
    before=bytes(memory[BOMB:BOMB+68]);cpu=state(memory,0x36708);cpu.a[0]=BOMB
    run(original_image,memory,cpu,{RETURN})
    if not reference:
        expected=bytearray(before);expected[:2]=b'\0\0'
        assert bytes(memory[BOMB:BOMB+68])==expected and get(memory,OFFSET)==20
        assert memory[INVENTORY]==1 and memory[APP+0xAE4]==0
        return
    y=(world_y+120)&0xFFFFFFFF;ground=space<128 and not negative32(y-0xFFFFFF88)
    assert [get(memory,BOMB+o)for o in [4,8,12]]==[10000,y,20000]
    assert [get(memory,BOMB+o,2)for o in [16,18,20]]==[65535,4097,32768]
    assert get(memory,APP+0xA76)==(0 if ground else reference)
    assert get(memory,OFFSET)==(20 if ground else 120)
    assert memory[INVENTORY]==(0 if ground else 1)
    assert memory[APP+0xAE4]==(255 if ground else 0)and memory[APP+0xAE3]==0
    assert get(memory,APP+0x7C4,2)==(200 if ground else 0)


@pytest.mark.parametrize('retract',[0,1,128,255])
@pytest.mark.parametrize('offset',[0,19,20,21,22,119,120,121,0x7FFFFFFF,0x80000000])
def test_service_offset_wordless_wrap_clamps_and_exact20_retraction(original_image,memory,retract,offset):
    prepare(memory);memory[APP+0xAE4]=retract;put(memory,OFFSET,offset)
    cpu=state(memory,0x32FE0);run(original_image,memory,cpu,{0x330C6})
    value=(offset+(-2 if retract>=128 else 2))&0xFFFFFFFF
    bound=20 if retract>=128 else 120
    clamp=negative32(value-bound)if retract>=128 else not negative32(value-bound)
    if clamp:value=bound
    removed=retract>=128 and value==20
    assert get(memory,OFFSET)==value and get(memory,APP+0xA76)==(0 if removed else BOMB)
    assert memory[APP+0xAE4]==(0 if removed else retract)
    assert get(memory,BOMB,2)==(0 if removed else 98)
    assert memory[BOMB+30]==255 and memory[INVENTORY]==1  # no free/recycle/count update


def install_motion(image,memory):
    cpu=state(memory,0x1F0E);run(image,memory,cpu,{RETURN})


def velocity(memory,speed):
    angles=[get(memory,APP+o,2)for o in [0x744,0x746,0x748]]
    sine,cosine=get(memory,APP+0x44),get(memory,APP+0x48)
    s0,c0,s1,c1=[get(memory,p+2*(a&4095),2)for p,a in [(sine,angles[0]),(cosine,angles[0]),(sine,angles[1]),(cosine,angles[1])]]
    scale=(speed+200)&65535
    return scale,[(-project(project(scale,s1),c0))&65535,(-project(scale,s0))&65535,project(project(scale,c1),c0)&65535]


@pytest.mark.parametrize('free',[0,1,2,65535])
@pytest.mark.parametrize('distant',[0,2])
@pytest.mark.parametrize('nearby',[0,2])
def test_spawn_unsigned_stack_gate_and_first_list_fallback_preserve_accounting(original_image,memory,free,distant,nearby):
    prepare(memory);install_motion(original_image,memory)
    put(memory,APP+0xA76,0);memory[APP+0xAE3]=255
    put(memory,APP+0x772,free,2);put(memory,APP+0x6D4,STACKLIST+4);put(memory,STACKLIST,BOMB)
    put(memory,APP+0x75C,distant,2);put(memory,APP+0x75E,nearby,2)
    put(memory,APP+0x6B8,STACKLIST+8);put(memory,APP+0x6C8,STACKLIST+16)
    for off,a in [(8,OTHER),(12,BOMB),(16,STATION),(20,BOMB)]:put(memory,STACKLIST+off,a)
    for a in [OTHER,STATION]:memory[a:a+68]=b'\x4C'*68
    selected=BOMB if free>1 else OTHER if distant else STATION if nearby else 0
    cpu=state(memory,0x3303A);run(original_image,memory,cpu,{0x330C6})
    assert memory[APP+0xAE3]==0 and get(memory,APP+0xA76)==selected
    assert get(memory,APP+0x772,2)==(free-1 if free>1 else free)
    assert get(memory,APP+0x6D4)==STACKLIST+(0 if free>1 else 4)
    assert get(memory,APP+0x75C,2)==distant and get(memory,APP+0x75E,2)==nearby
    if not selected:return
    scale,v=velocity(memory,100)
    assert get(memory,selected,2)==98 and memory[selected+31]==0
    assert [get(memory,selected+o,2)for o in [32,36,38]]==[scale,1000,0]
    assert [get(memory,selected+o,2)for o in [44,46,48]]==v
    assert [get(memory,selected+o)for o in [4,8,12]]==[(10000+signed16(v[0]))&65535,(-1000+signed16(v[1])+120)&0xFFFFFFFF,(20000+signed16(v[2]))&65535]
    assert memory[selected+2]==0x4C and bytes(memory[selected+52:selected+68])==b'\x4C'*16


@pytest.mark.parametrize('space',[0,1,128])
@pytest.mark.parametrize('inside',[0,1,128])
@pytest.mark.parametrize('projectors',[0,1,128])
@pytest.mark.parametrize('minis',[0,1,65535])
def test_launch_open_space_guard_precedence_distinguishes_sign_and_nonzero_tests(original_image,memory,space,inside,projectors,minis):
    prepare(memory);memory[APP+0x77D]=space;memory[APP+0x77C]=inside
    memory[APP+0xAA7]=projectors;put(memory,APP+0xA7A,minis,2)
    cpu=state(memory,0x79A8);run(original_image,memory,cpu,{0x79CC,0x7A3C,0x7A6A})
    guard=space>=128 and inside<128
    assert cpu.pc==(0x7A3C if guard and projectors else 0x7A6A if guard and minis else 0x79CC)
    assert memory[INVENTORY]==1 and get(memory,APP+0xA76)==BOMB


@pytest.mark.parametrize('offset',[69,70,120,0x7FFFFFFF,0x80000000,0xFFFFFFFF])
@pytest.mark.parametrize('reference',[0,BOMB])
@pytest.mark.parametrize('speed',[0,32768,65535])
@pytest.mark.parametrize('inventory',[1,255])
def test_launch_n_only_offset_gate_inventory_before_pointer_and_final_requests(original_image,memory,offset,reference,speed,inventory):
    prepare(memory);install_motion(original_image,memory)
    put(memory,OFFSET,offset);put(memory,APP+0xA76,reference);memory[INVENTORY]=inventory
    put(memory,APP+0x75A,speed,2);before=bytes(memory[BOMB:BOMB+68])
    cpu=state(memory,0x79A8);run(original_image,memory,cpu,{RETURN})
    allowed=not negative32(offset-70);launched=allowed and bool(reference)
    assert memory[INVENTORY]==(0 if allowed else inventory)
    assert get(memory,APP+0x7C4,2)==(200 if launched else 0)
    assert get(memory,OFFSET)==(20 if launched else offset)
    assert get(memory,APP+0xA76)==(0 if launched else reference)
    assert memory[APP+0xAE3]==0 and memory[APP+0xAE4]==(255 if launched else 0)
    if not launched:
        assert bytes(memory[BOMB:BOMB+68])==before
        return
    scale,v=velocity(memory,speed)
    assert get(memory,BOMB+32,2)==scale and get(memory,BOMB+36,2)==1000
    assert [get(memory,BOMB+o,2)for o in [44,46,48]]==v
    assert [get(memory,BOMB+o)for o in [4,8,12]]==[(10000+signed16(v[0]))&65535,(-1000+signed16(v[1])+offset)&0xFFFFFFFF,(20000+signed16(v[2]))&65535]
    assert memory[BOMB+31]==255 and memory[BOMB+30]==255
    assert bytes(memory[BOMB+52:BOMB+68])==before[52:68]


@pytest.mark.parametrize('spawn',[0,255])
@pytest.mark.parametrize('retract',[0,255])
def test_empty_inventory_clears_reference_and_sets_retraction_without_touching_record(original_image,memory,spawn,retract):
    prepare(memory);memory[INVENTORY]=0;memory[APP+0xAE3]=spawn;memory[APP+0xAE4]=retract
    before=bytes(memory[BOMB:BOMB+68]);cpu=state(memory,0x79A8)
    run(original_image,memory,cpu,{RETURN})
    assert get(memory,APP+0xA76)==0 and memory[APP+0xAE3]==0 and memory[APP+0xAE4]==255
    assert bytes(memory[BOMB:BOMB+68])==before and get(memory,OFFSET)==120


@pytest.mark.parametrize('spawn_request',[0,1,128,255])
@pytest.mark.parametrize('cooldown',[0,1,65535])
def test_spawn_request_sign_and_any_nonzero_cooldown_gate(original_image,memory,spawn_request,cooldown):
    prepare(memory);install_motion(original_image,memory)
    memory[APP+0xAE3]=spawn_request;put(memory,APP+0x7C4,cooldown,2);put(memory,APP+0xA76,OTHER)
    put(memory,APP+0x772,2,2);put(memory,APP+0x6D4,STACKLIST+4);put(memory,STACKLIST,BOMB)
    cpu=state(memory,0x3303A);run(original_image,memory,cpu,{0x330C6})
    created=spawn_request>=128 and cooldown==0
    assert get(memory,APP+0xA76)==(BOMB if created else OTHER)
    assert memory[APP+0xAE3]==(0 if created else spawn_request)
    assert get(memory,APP+0x772,2)==(1 if created else 2)


@pytest.mark.parametrize('phase',[0,1,2,255])
@pytest.mark.parametrize('retract',[0,128])
def test_phase_one_detonation_clears_reference_but_still_adjusts_offset(original_image,memory,phase,retract):
    prepare(memory);memory[BOMB+30]=phase;memory[APP+0xAE4]=retract
    cpu=state(memory,0x32FE0);run(original_image,memory,cpu,{0x330C6})
    assert get(memory,APP+0xA76)==(0 if phase==1 else BOMB)
    assert get(memory,OFFSET)==(118 if retract>=128 else 120)
    assert memory[INVENTORY]==1 and get(memory,BOMB,2)==98
    assert memory[APP+0xBB6]==(255 if phase==1 else 0)
