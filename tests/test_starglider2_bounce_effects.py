"""Original bounce and software sound-continuation CPU behavior.

Sound cases stop before device-writing phases. Supplied RAM/list states are not
normal-game reachability, ownership, concurrency, scanout or PCM guarantees.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,RETURN
from tests.test_starglider2_scan_acquisition import signed16,project

BOMB,LIST=INPUT+0x100,INPUT+0x500
PV,PP,PA=0x4D070,0x4D074,0x39CC4
AV,AP,AD,AA=0x4DDA4,0x4DDA2,0x4DDA6,0x4DDA0
PENDING,GENERIC,ARG=APP+0xAE1,APP+0xBB6,APP+0x860


def n16(v):return bool(v&0x8000)
def n32(v):return bool(v&0x80000000)


def prepare(memory):
    memory[BOMB:BOMB+68]=b'\0'*68;put(memory,BOMB,91,2)
    memory[BOMB+30]=255
    for o,v in [(4,65535),(8,-30),(12,0)]:put(memory,BOMB+o,v&0xFFFFFFFF)
    for o,v in [(16,3),(18,1024),(20,65535),(32,21),(36,5),(38,0),(44,3),(46,1),(48,65531),(26,0xF123)]:put(memory,BOMB+o,v,2)
    put(memory,APP+0x6FC,65535);memory[APP+0x77D]=0
    memory[PENDING]=0;memory[GENERIC]=0;put(memory,ARG,0x1111,2)


def install_motion(image,memory):
    run(image,memory,state(memory,0x1F0E),{RETURN})


def motion_xz(memory,angles,scale):
    sine,cosine=get(memory,APP+0x44),get(memory,APP+0x48)
    s1=get(memory,sine+2*(angles[1]&4095),2);c1=get(memory,cosine+2*(angles[1]&4095),2)
    c0=get(memory,cosine+2*(angles[0]&4095),2)
    return [(-project(project(scale,s1),c0))&65535,project(project(scale,c1),c0)&65535]


@pytest.mark.parametrize('space',[0,1,128])
@pytest.mark.parametrize('y',[-1000,-30,-25,-20,0x7FFFFFFF])
@pytest.mark.parametrize('vy',[-32768,-1,0,10,32764])
@pytest.mark.parametrize('scale',[0,19,20,21,32768,65535])
def test_bounce_word_restitution_zero_scale_sound_and_unconditional_tail(original_image,memory,space,y,vy,scale):
    prepare(memory);install_motion(original_image,memory)
    memory[APP+0x77D]=space;put(memory,BOMB+8,y&0xFFFFFFFF)
    put(memory,BOMB+46,vy&65535,2);put(memory,BOMB+32,scale,2)
    angles=[3,1024,65535];vx,vz=3,65531;mask=0;pending=False;hit=False
    if space<128:
        angles[0]=(signed16(angles[0])>>1)&65535;angles[2]=(signed16(angles[2])>>1)&65535
        vy=signed16(vy+4);y=(y+vy)&0xFFFFFFFF
        hit=not n32(y-0xFFFFFFE7)
        if hit:
            mask=3;vy=signed16(10-vy);y=(y+vy)&0xFFFFFFFF
            scale=(scale-20)&65535
            if n16(scale):scale=0;vx=vz=0
            else:vx,vz=motion_xz(memory,angles,scale);pending=True
    else:y&=0xFFFFFFFF
    resting=scale==0 and not n32(y-0xFFFFFFE7)
    expected_y=0xFFFFFFE7 if resting else y
    cpu=state(memory,0x368AE);cpu.a[0]=BOMB;run(original_image,memory,cpu,{RETURN})
    assert [get(memory,BOMB+o)for o in [4,8,12]]==[(65535+signed16(vx))&65535,expected_y,signed16(vz)&65535]
    assert [get(memory,BOMB+o,2)for o in [16,18,20]]==angles
    assert [get(memory,BOMB+o,2)for o in [32,38,44,46,48]]==[scale,mask,vx,vy&65535,vz]
    assert get(memory,BOMB+36,2)==(5 if resting else 4)
    assert memory[BOMB+30]==(0 if resting else 255)
    assert memory[PENDING]==(255 if pending else 0)and get(memory,ARG,2)==(0xF123 if pending else 0x1111)
    assert get(memory,BOMB+34,2)==(0 if resting else 1&mask)
    assert memory[BOMB+3]==(11 if not resting and (1&mask)==0 else 0)


@pytest.mark.parametrize('remaining',[0,1,32768,65535])
@pytest.mark.parametrize('mask',[0,1,3,65535])
@pytest.mark.parametrize('phase',[0,1,65535])
@pytest.mark.parametrize('variant',[0,1,13,128,255])
def test_wrapped_countdown_and_masked_vertex_cycle_are_not_universal_mod12(original_image,memory,remaining,mask,phase,variant):
    prepare(memory);memory[APP+0x77D]=128;put(memory,BOMB+32,5,2)
    for off,v in [(36,remaining),(38,mask),(34,phase)]:put(memory,BOMB+off,v,2)
    memory[BOMB+3]=variant;cpu=state(memory,0x368AE);cpu.a[0]=BOMB
    run(original_image,memory,cpu,{RETURN})
    left=(remaining-1)&65535;expired=n16(left)
    result_phase=phase if expired else ((phase+1)&mask)
    result_variant=variant
    if not expired and result_phase==0:
        result_variant=(variant-1)&255
        if result_variant&128:result_variant=11
    assert get(memory,BOMB+36,2)==left and memory[BOMB+30]==(0 if expired else 255)
    assert get(memory,BOMB+34,2)==result_phase and memory[BOMB+3]==result_variant


def sound_setup(memory,count=1,kind=91,phase=0,depth=123):
    put(memory,APP+0x75E,count,2);put(memory,APP+0x6C8,LIST);put(memory,LIST,BOMB)
    put(memory,BOMB,kind,2);memory[BOMB+30]=phase;put(memory,BOMB+26,depth,2)
    put(memory,PV,0,2);put(memory,PP,200,2)
    put(memory,AV,0,2);put(memory,AP,0,2);put(memory,AD,0,2)


def paula_reference(count,bounce,generic,argument,vol=0,period=200):
    active=bool(count and (bounce>=128 or generic>=128))
    if count and bounce>=128:bounce=0;period=358
    if count and generic>=128:generic=0;argument=1;period=358
    if active:
        magnitude=(-argument)&65535 if n16(argument)else argument
        candidate=(64-(magnitude>>7))&65535
        if not n16(candidate-vol):vol=candidate
        result=(period-((magnitude>>4)+124))&65535
        period=124 if n16(result-124)else result
    vol=(vol-1)&65535
    if n16(vol):vol=0
    period=(period+30)&65535
    if not n16(period-1000):period=1000
    return bounce,generic,vol,period,int(active)


def alternate_reference(count,bounce,generic,argument,vol=0,period=0,decay=0):
    active=bool(count and (bounce>=128 or generic>=128))
    if count and bounce>=128:bounce=0
    elif count and generic>=128:generic=0;argument=500
    if active:
        candidate=15-(argument>>12)
        if not n16(candidate-vol):vol=candidate
        period=15
    decay=(decay+1)&3
    if decay==0:
        vol=(vol-1)&65535
        if n16(vol):vol=0
    period=(period+1)&65535
    if not n16(period-31):period=31
    return bounce,generic,vol,period,decay,int(active)


@pytest.mark.parametrize('backend',['paula','alternate'])
@pytest.mark.parametrize('count',[0,1])
@pytest.mark.parametrize('bounce',[0,1,128])
@pytest.mark.parametrize('generic',[0,1,128])
@pytest.mark.parametrize('argument',[0,1,8192,32767,32768,65535])
def test_software_sound_consumers_keep_priority_sign_and_empty_list_gates(original_image,memory,backend,count,bounce,generic,argument):
    prepare(memory);sound_setup(memory,count);memory[PENDING]=bounce;memory[GENERIC]=generic;put(memory,ARG,argument,2)
    entry,stop=(0x4BCB8,0x4BDCE)if backend=='paula'else(0x4D36C,0x4D452)
    run(original_image,memory,state(memory,entry),{stop})
    if backend=='paula':
        assert [memory[PENDING],memory[GENERIC],get(memory,PV,2),get(memory,PP,2),get(memory,PA,2)]==list(paula_reference(count,bounce,generic,argument))
    else:
        assert [memory[PENDING],memory[GENERIC],get(memory,AV,2),get(memory,AP,2),get(memory,AD,2),get(memory,AA,2)]==list(alternate_reference(count,bounce,generic,argument))


@pytest.mark.parametrize('kind',[75,76,82,83])
@pytest.mark.parametrize('bounce',[0,128])
@pytest.mark.parametrize('generic',[0,128])
def test_paula_projector_override_retains_pending_requests(original_image,memory,kind,bounce,generic):
    prepare(memory);sound_setup(memory,1,kind,1);memory[PENDING]=bounce;memory[GENERIC]=generic;put(memory,ARG,1,2)
    run(original_image,memory,state(memory,0x4BCB8),{0x4BDCE})
    if 76<=kind<=82:
        assert [memory[PENDING],memory[GENERIC],get(memory,PV,2),get(memory,PP,2)]==[bounce,generic,63,420]
    else:assert [memory[PENDING],memory[GENERIC]]==[0,0]


@pytest.mark.parametrize('backend',['paula','alternate'])
@pytest.mark.parametrize('argument',[1,32768,65535])
@pytest.mark.parametrize('generic',[0,128])
def test_original_bounce_producers_overwrite_pending_argument_before_consumption(original_image,memory,backend,argument,generic):
    prepare(memory);install_motion(original_image,memory)
    put(memory,BOMB+8,0xFFFFFFE7);put(memory,BOMB+32,20,2)
    second=BOMB+0x100;memory[second:second+68]=bytes(memory[BOMB:BOMB+68]);put(memory,second+26,argument,2)
    for record in [BOMB,second]:
        cpu=state(memory,0x368AE);cpu.a[0]=record;run(original_image,memory,cpu,{RETURN})
        assert memory[PENDING]==255 and memory[record+30]==0
    assert get(memory,ARG,2)==argument  # one latch; last original producer wins
    sound_setup(memory);memory[GENERIC]=generic
    entry,stop=(0x4BCB8,0x4BDCE)if backend=='paula'else(0x4D36C,0x4D452)
    run(original_image,memory,state(memory,entry),{stop})
    if backend=='paula':
        assert [memory[PENDING],memory[GENERIC],get(memory,PV,2),get(memory,PP,2),get(memory,PA,2)]==list(paula_reference(1,255,generic,argument))
    else:
        assert [memory[PENDING],memory[GENERIC],get(memory,AV,2),get(memory,AP,2),get(memory,AD,2),get(memory,AA,2)]==list(alternate_reference(1,255,generic,argument))


@pytest.mark.parametrize('backend,volume,period,decay',[
    ('paula',0,999,0),('paula',1,65535,0),('paula',32768,0,0),('paula',65535,32768,0),
    ('alternate',0,31,3),('alternate',1,65535,3),('alternate',32768,0,3),('alternate',65535,32768,0),
])
def test_software_envelope_decay_keeps_original_word_wrap_and_n_only_caps(original_image,memory,backend,volume,period,decay):
    prepare(memory);sound_setup(memory,0)
    if backend=='paula':
        put(memory,PV,volume,2);put(memory,PP,period,2)
        run(original_image,memory,state(memory,0x4BCB8),{0x4BDCE})
        assert [memory[PENDING],memory[GENERIC],get(memory,PV,2),get(memory,PP,2),get(memory,PA,2)]==list(paula_reference(0,0,0,0,volume,period))
    else:
        put(memory,AV,volume,2);put(memory,AP,period,2);put(memory,AD,decay,2)
        run(original_image,memory,state(memory,0x4D36C),{0x4D452})
        assert [memory[PENDING],memory[GENERIC],get(memory,AV,2),get(memory,AP,2),get(memory,AD,2),get(memory,AA,2)]==list(alternate_reference(0,0,0,0,volume,period,decay))
