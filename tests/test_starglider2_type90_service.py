"""Original type90 chain/service CPU paths; supplied readable, finite links only
except one bounded cycle witness. No global termination or gameplay proof.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT
from tests.test_starglider2_structure_profiles import setup, STRUCT, OBJECT

BACK,TAIL1,TAIL2=INPUT+0x700,INPUT+0x780,INPUT+0x800


def prepare(memory,orientation=0,actor=30,x=10000,y=-1000,z=19000):
    setup(memory,kind=actor);put(memory,STRUCT,90,2);memory[STRUCT+2]=0;memory[STRUCT+28]=128
    put(memory,STRUCT+18,orientation,2)
    for off,v in zip([4,8,12],[x,y,z]):put(memory,OBJECT+off,v&0xFFFFFFFF)
    for a in [BACK,TAIL1,TAIL2]:memory[a:a+68]=b'\xCC'*68;put(memory,a,90,2);put(memory,a+60,0)
    put(memory,STRUCT+56,BACK);put(memory,STRUCT+60,TAIL1);put(memory,TAIL1+60,TAIL2)
    memory[APP+0x209]=0


def call(image,memory):
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;cpu.a[6]=0x171FC
    d,a=list(cpu.d),list(cpu.a);run(image,memory,cpu,{0xB8F8})
    assert list(cpu.d)==d and list(cpu.a)==a


@pytest.mark.parametrize('orientation',[0,1])
@pytest.mark.parametrize('cross',[-601,-600,-200,-199,0,200,201,600,601])
@pytest.mark.parametrize('y',[-1001,-1000])
def test_chain_corridor_keeps_open_lower_and_closed_upper_strip(original_image,memory,orientation,cross,y):
    prepare(memory,orientation,x=10000+(1700 if orientation else cross),y=y,z=20000+(cross if orientation else -1800))
    call(original_image,memory)
    marked=-200<cross<=200 and y>=-1000
    assert memory[BACK+3]==(0 if marked else 204)
    assert memory[BACK+34]==(255 if marked else 204)
    assert memory[TAIL1+40]==(255 if marked else 204)and memory[TAIL2+40]==(255 if marked else 204)
    assert memory[TAIL1+3]==204 and memory[TAIL1+34]==204


@pytest.mark.parametrize('back_type',[None,0,1,90])
@pytest.mark.parametrize('tail_type',[None,0,1,90])
def test_backlink_guard_and_forward_chain_have_distinct_roots(original_image,memory,back_type,tail_type):
    prepare(memory,z=18200)
    if back_type is None:put(memory,STRUCT+56,0)
    else:put(memory,BACK,back_type,2)
    if tail_type is None:put(memory,STRUCT+60,0)
    else:put(memory,TAIL1,tail_type,2)
    call(original_image,memory)
    assert memory[BACK+3]==(0 if back_type==90 else 204)
    assert memory[TAIL1+40]==(255 if back_type==90 and tail_type==90 else 204)
    assert memory[TAIL2+40]==(255 if back_type==90 and tail_type==90 else 204)


def test_valid_backed_cycle_has_no_local_visited_check(original_image,memory):
    prepare(memory,z=18200);put(memory,STRUCT+60,TAIL1);put(memory,TAIL1+60,TAIL1)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;seen=[]
    class Witness(Exception):pass
    def observe(pc):
        if pc==0xC2F2:
            seen.append(cpu.a[1])
            if len(seen)==4:raise Witness
    with pytest.raises(Witness):run(original_image,memory,cpu,{0xB8F8},observe)
    assert seen==[STRUCT,TAIL1,TAIL1,TAIL1]and memory[TAIL1+40]==255


def reference(values,increment,bonus):
    values=list(values)
    for i in range(3):
        if values[i]==65535:continue
        total=values[i]+increment;values[i]=min(total,65535)
        if total<=65535:break  # exact fill has no carry and still exits
        if i==2:bonus=(bonus+1)&0xFFFFFFFF
    return values,bonus


@pytest.mark.parametrize('speed',[0,1,32767,32768,65535])
@pytest.mark.parametrize('values',[(0,0,0),(65534,0,0),(65535,65534,0),(65535,65535,65534),(65535,65535,65535),(65533,65533,65533)])
def test_zero_orientation_service_uses_word_double_and_carry_driven_priority(original_image,memory,speed,values):
    prepare(memory,z=18201);put(memory,APP+0x75A,speed,2)
    for off,v in zip([0x774,0x776,0x794],values):put(memory,APP+off,v,2)
    put(memory,APP+0x6EC,0xFFFFFFFF)
    expected,bonus=reference(values,(2*speed)&65535,0xFFFFFFFF)
    call(original_image,memory)
    assert [get(memory,APP+off,2)for off in [0x774,0x776,0x794]]==expected
    assert get(memory,APP+0x6EC)==bonus and memory[APP+0x209]==255
    assert get(memory,APP+0x6F0)==0 and memory[BACK+3]==204


@pytest.mark.parametrize('power',[0,65135,65136,65535])
@pytest.mark.parametrize('actor',[1,30])
def test_nonzero_orientation_service_wraps_400_without_panel_request(original_image,memory,power,actor):
    prepare(memory,orientation=1,actor=actor,x=11801,z=20000)
    put(memory,APP+0x774,power,2);put(memory,APP+0x776,123,2);put(memory,APP+0x794,456,2)
    call(original_image,memory)
    assert get(memory,APP+0x774,2)==((power+400)&65535 if actor==30 else power)
    assert get(memory,APP+0x776,2)==123 and get(memory,APP+0x794,2)==456
    assert memory[APP+0x209]==0


def test_zero_orientation_nonplayer_only_requests_fast_panel(original_image,memory):
    prepare(memory,actor=1,z=18201);put(memory,APP+0x774,123,2);call(original_image,memory)
    assert memory[APP+0x209]==255 and get(memory,APP+0x774,2)==123


@pytest.mark.parametrize('orientation',[0,1])
@pytest.mark.parametrize('actor',[4,90,93,96,97])
def test_excluded_actor_types_do_not_mark_or_service(original_image,memory,orientation,actor):
    prepare(memory,orientation,actor,x=11801 if orientation else 10000,z=20000 if orientation else 18201)
    put(memory,APP+0x774,123,2);call(original_image,memory)
    assert memory[BACK+3]==204 and memory[TAIL1+40]==204
    assert memory[APP+0x209]==0 and get(memory,APP+0x774,2)==123
