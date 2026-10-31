"""Original modulation continuations and connected speed producers.

Device registers are RAM; these are ordered CPU writes and serial service calls,
not audio/DMA simulation, frame cadence, normal-caller or lifetime guarantees.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,state,run,put,get,APP,RETURN,STACK
from tests.test_starglider2_object_sound_handlers import memory,small_memory,ENABLE

PV,PP,DECAY=0x4D064,0x4D066,0x4D068
SV,SP,IDLE,CV,CP=0x4D06A,0x4D06C,0x4D06E,0x4D070,0x4D074
BIAS,SELECT,UP,DOWN,OUTER,INNER,STARSEL,STARUP,STARDOWN=0x4D25C,0x4D26A,0x4D26C,0x4D26E,0x4D270,0x4D272,0x4D274,0x4D276,0x4D278
STARD=APP+0x9AE
P1,V1,P0,P2=0xDFF0B6,0xDFF0B8,0xDFF0A6,0xDFF0C6
SENTINEL=0xA55A
STORES={0x4CB02:V1,0x4CB0E:V1,0x4CB28:P1,0x4CB30:P1,0x4CB86:P0,0x4CBCC:P2}


def n(v):return bool(v&32768)
def neg(v):return(-v)&65535
def decay(v,step):
    v=(v-step)&65535
    return 0 if n(v)else v


def prepare(memory):
    for a,v in[(PV,30),(PP,1300),(DECAY,1),(SV,8),(SP,124),(IDLE,1),(CV,13),(CP,500),
                (BIAS,1),(SELECT,1),(UP,0),(DOWN,0),(OUTER,1),(INNER,1),(STARSEL,1),(STARUP,0),(STARDOWN,0)]:put(memory,a,v,2)
    memory[APP+0x6DA]=0;memory[ENABLE]=128;put(memory,STARD,0,2)
    for a in[P1,V1,P0,P2]:put(memory,a,SENTINEL,2)


def service(image,memory):
    events=[];pending=None
    def observe(pc):
        nonlocal pending
        if pending is not None:events.append((STORES[pending],get(memory,STORES[pending],2)))
        pending=pc if pc in STORES else None
    cpu=state(memory,0x4CAC0);run(image,memory,cpu,{RETURN},observe)
    if pending is not None:events.append((STORES[pending],get(memory,STORES[pending],2)))
    assert cpu.a[7]==STACK+4
    return events


@pytest.mark.parametrize('phase',[0,1,32768,65535])
@pytest.mark.parametrize('volume',[0,1,2,32768,65535])
def test_not_word_phase_alternates_decay_with_original_subtraction_sign(original_image,memory,phase,volume):
    prepare(memory);put(memory,DECAY,phase,2);put(memory,PV,volume,2)
    after=phase^65535;expected=volume if n(after)else decay(volume,2)
    events=service(original_image,memory)
    assert get(memory,DECAY,2)==after and get(memory,PV,2)==expected
    assert events[0]==(V1,expected)


@pytest.mark.parametrize('period',[0,1660,1661,1700,65520])
@pytest.mark.parametrize('sign',[0,1,32768,65535])
def test_projectile_period_resets_only_on_exact_1700_and_optional_ten_bias(original_image,memory,period,sign):
    prepare(memory);put(memory,PP,period,2);put(memory,BIAS,sign,2)
    result=(period+40)&65535
    if result==1700:result=300
    new=neg(sign);events=service(original_image,memory)
    assert get(memory,PP,2)==result and get(memory,BIAS,2)==new
    assert events[1]==(P1,(result+(0 if n(new)else 10))&65535)


@pytest.mark.parametrize('outer',[0,1,32768,65535])
@pytest.mark.parametrize('inner',[0,1,32768,65535])
@pytest.mark.parametrize('select',[0,1,32768,65535])
@pytest.mark.parametrize('offsets',[(0,0),(127,128),(65535,32768)])
def test_two_neg_word_gates_mask_offsets_only_when_update_runs(original_image,memory,outer,inner,select,offsets):
    prepare(memory)
    for a,v in[(OUTER,outer),(INNER,inner),(SELECT,select),(UP,offsets[0]),(DOWN,offsets[1])]:put(memory,a,v,2)
    o=neg(outer);i=neg(inner)if n(o)else inner;update=n(o)and not n(i)
    up=(offsets[0]+1)&127 if update else offsets[0];down=(offsets[1]-1)&127 if update else offsets[1]
    chosen=down if n(neg(select))else up
    events=service(original_image,memory)
    assert [get(memory,a,2)for a in[OUTER,INNER,SELECT,UP,DOWN]]==[o,i,neg(select),up,down]
    assert events[2]==(P0,(124+chosen)&65535)


@pytest.mark.parametrize('enabled',[0,1,32768,65535])
@pytest.mark.parametrize('select',[0,1,32768,65535])
@pytest.mark.parametrize('offsets',[(0,0),(255,256),(65535,32768)])
@pytest.mark.parametrize('base',[0,65535])
def test_stardrive_nonzero_word_enables_independent_masked_eight_step(original_image,memory,enabled,select,offsets,base):
    prepare(memory)
    for a,v in[(STARD,enabled),(STARSEL,select),(STARUP,offsets[0]),(STARDOWN,offsets[1]),(CP,base)]:put(memory,a,v,2)
    events=service(original_image,memory)
    if not enabled:
        assert get(memory,P2,2)==SENTINEL and [get(memory,a,2)for a in[STARSEL,STARUP,STARDOWN]]==[select,*offsets]
    else:
        up=(offsets[0]+8)&255;down=(offsets[1]-8)&255;chosen=down if n(neg(select))else up
        assert [get(memory,a,2)for a in[STARSEL,STARUP,STARDOWN]]==[neg(select),up,down]
        assert events[-1]==(P2,(base+chosen)&65535)


@pytest.mark.parametrize('modal',[0,128])
@pytest.mark.parametrize('enabled',[0,128])
@pytest.mark.parametrize('star',[0,1])
def test_mute_does_not_suppress_state_or_period_writes_and_order_is_preserved(original_image,memory,modal,enabled,star):
    prepare(memory);memory[APP+0x6DA]=modal;memory[ENABLE]=enabled
    put(memory,STARD,star,2);put(memory,DECAY,65535,2);put(memory,PP,1660,2)
    events=service(original_image,memory)
    assert events==[(V1,0 if modal or not enabled else 28),(P1,300),(P0,124)]+([(P2,748)]if star else[])
    assert get(memory,PV,2)==28 and get(memory,PP,2)==300


@pytest.mark.parametrize('phase',[0,1,32768,65535])
@pytest.mark.parametrize('volume',[0,1,2,32768,65535])
def test_stopped_speed_volume_uses_neg_not_tail_not_phase(original_image,memory,phase,volume):
    prepare(memory);put(memory,APP+0x758,0,2);put(memory,IDLE,phase,2);put(memory,SV,volume,2)
    run(original_image,memory,state(memory,0x4BC16),{0x4BCB8})
    assert get(memory,IDLE,2)==neg(phase)
    assert get(memory,SV,2)==(volume if n(neg(phase))else decay(volume,1))


@pytest.mark.parametrize('speed',[1,479,32768,65535])
@pytest.mark.parametrize('view',[0,3,4,127,128,255])
def test_moving_speed_volume_uses_original_byte_subtraction_sign(original_image,memory,speed,view):
    prepare(memory);put(memory,APP+0x758,speed,2);memory[APP+0x7EB]=view
    run(original_image,memory,state(memory,0x4BC16),{0x4BCB8})
    assert get(memory,SV,2)==(8 if(view-4)&128 else 24)
    assert get(memory,IDLE,2)==1


@pytest.mark.parametrize('speed',[0,1,479,480,604,32768,65535])
@pytest.mark.parametrize('period',[0,123,124,603,604,605,65535])
def test_speed_period_producer_has_directional_limits_not_global_clamp(original_image,memory,speed,period):
    prepare(memory);put(memory,APP+0x758,speed,2);put(memory,SP,period,2)
    target=(604-speed)&65535;expected=period
    if target!=period:
        expected=(period-4 if n(target-period)else period+4)&65535
        if n(target-period):expected=124 if n(expected-124)else expected
        else:expected=604 if not n(expected-604)else expected
    run(original_image,memory,state(memory,0x4BC16),{0x4BCB8})
    assert get(memory,SP,2)==expected


@pytest.mark.parametrize('space',[0,1,128])
@pytest.mark.parametrize('star',[0,1,65535])
@pytest.mark.parametrize('field',[0,128])
@pytest.mark.parametrize('speed',[478,479])
@pytest.mark.parametrize('volume',[0,8,32768])
def test_stardrive_producer_guards_and_479_override_do_not_restrict_tail_consumer(original_image,memory,space,star,field,speed,volume):
    prepare(memory);memory[APP+0x77D]=space;memory[APP+0xA9D]=field
    put(memory,STARD,star,2);put(memory,APP+0x758,speed,2);put(memory,SV,volume,2)
    cvol,cperiod,svol=13,500,volume
    if space>=128 and star and field>=128:
        candidate=(volume<<2)&65535
        if not n(candidate-cvol):cvol=candidate
        cperiod=331
        if speed==479:cvol,cperiod,svol=64,300,32
    run(original_image,memory,state(memory,0x4BDCE),{0x4BE2C})
    assert [get(memory,a,2)for a in[CV,CP,SV]]==[cvol,cperiod,svol]
    events=service(original_image,memory)
    assert get(memory,P2,2)==((cperiod+248)&65535 if star else SENTINEL)


def test_initialized_serial_service_has_quarter_updates_but_no_frame_rate_claim(original_image,memory):
    prepare(memory);advance=[];periods=[]
    for call in range(1,41):
        old=get(memory,UP,2);events=service(original_image,memory)
        if get(memory,UP,2)!=old:advance.append(call)
        periods.append(get(memory,PP,2))
    assert advance==list(range(3,41,4))
    assert periods[8:11]==[1660,300,340]
    assert get(memory,UP,2)==10 and get(memory,DOWN,2)==118
