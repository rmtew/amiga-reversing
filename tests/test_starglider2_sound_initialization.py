"""Original sound setup and alternate output phase, with device ports as RAM.

Trace CPU store order/values only. No device, DMA, PCM, timing, complete-frame,
normal-startup caller, noise-quality, sample ownership or lifetime guarantee.
"""
import ctypes
import pytest
from tests.test_starglider2_text_editor import original_image,memory as small_memory,state,run,put,get,APP,RETURN,STACK
from tests.test_starglider2_palette_priority import rng

SEL,DATA=0xFF8800,0xFF8802
TYPE,ENABLE=0x39CE0,0x39CD5
OVOL,OPER,AMPL,PAUSE,ENV=0x4DDAC,0x4DDAE,0x4DE14,0x4DE16,0x4DE18
PVOL,PPER,STARVOL,EVENTVOL,EVENTNOISE=0x4DE20,0x4DE24,0x4DD9C,0x4DDA4,0x4DDA2
VAR,SETS,USES,RESET=0x4DE3A,0x4DE36,0x4DE3C,0x4DE39
PORT_STORES={pc:(SEL if port=='s'else DATA,1)for pc,port in[
    (0x4D9F2,'s'),(0x4DA1C,'d'),(0x4DA28,'s'),(0x4DA30,'d'),(0x4DA36,'s'),(0x4DA40,'d'),
    (0x4DA4C,'s'),(0x4DA64,'d'),(0x4DA70,'s'),(0x4DA78,'d'),(0x4DA7E,'s'),(0x4DA88,'d'),
    (0x4DACA,'s'),(0x4DAD2,'d'),(0x4DB10,'s'),(0x4DB18,'d'),
    (0x4DD4E,'s'),(0x4DD56,'d'),(0x4DD6C,'s'),(0x4DD74,'d'),(0x4DFB0,'s'),(0x4DFB8,'d')]}
PAULA_STORES={
    0x4DEE8:(0xDFF0A0,4),0x4DEEE:(0xDFF0A4,2),0x4DEF6:(0xDFF0A8,2),0x4DEFE:(0xDFF0A6,2),
    0x4DF12:(0xDFF0B0,4),0x4DF18:(0xDFF0B4,2),0x4DF20:(0xDFF0B8,2),0x4DF28:(0xDFF0B6,2),
    0x4DF3C:(0xDFF0C0,4),0x4DF42:(0xDFF0C4,2),0x4DF4A:(0xDFF0C8,2),0x4DF52:(0xDFF0C6,2),
    0x4DF60:(0xDFF0D0,4),0x4DF66:(0xDFF0D4,2),0x4DF6E:(0xDFF0D8,2),0x4DF76:(0xDFF0D6,2),
    0x4DF7E:(TYPE,2),0x4DF84:(0xDFF096,2)}


@pytest.fixture
def memory(small_memory):
    result=(ctypes.c_uint8*0x1000000)();ctypes.memmove(result,small_memory,len(small_memory))
    return result


def trace(image,memory,cpu,stops,stores=PORT_STORES):
    pending=None;events=[]
    def observe(pc):
        nonlocal pending
        if pending is not None:
            address,width=stores[pending];events.append((address,width,get(memory,address,width)))
        pending=pc if pc in stores else None
    run(image,memory,cpu,stops,observe)
    if pending is not None:
        address,width=stores[pending];events.append((address,width,get(memory,address,width)))
    return events


def prepare(memory):
    for a,v in[(TYPE,3),(OVOL,0x1234),(OPER,0xABCD),(ENV,0x5678),(PVOL,0x2345),(PPER,0x6789),
                (STARVOL,7),(EVENTVOL,13),(EVENTNOISE,0x12FF),(APP+0x9AE,32768)]:put(memory,a,v,2)
    memory[AMPL]=254;memory[PAUSE]=0;memory[VAR]=1;memory[SETS]=memory[USES]=0
    memory[APP+0x6DA]=0;memory[ENABLE]=128;memory[SEL]=0xA5;memory[DATA]=0x5A
    put(memory,APP+0x60,0x12345678);put(memory,APP+0x64,0xABCDEF01)


def output(image,memory):
    events=trace(image,memory,state(memory,0x4D9BC),{0x4DB1E})
    assert len(events)%2==0
    assert all(events[i][0:2]==(SEL,1)and events[i+1][0:2]==(DATA,1)for i in range(0,len(events),2))
    return[(events[i][2],events[i+1][2])for i in range(0,len(events),2)]


@pytest.mark.parametrize('kind',[0,1,3,10,15,34,64])
@pytest.mark.parametrize('pause',[0,1,128,255])
@pytest.mark.parametrize('modal',[0,128])
@pytest.mark.parametrize('enabled',[0,128])
def test_object_volume_precedence_pause_alias_and_output_mute(original_image,memory,kind,pause,modal,enabled):
    prepare(memory);put(memory,TYPE,kind,2);memory[PAUSE]=pause;memory[APP+0x6DA]=modal;memory[ENABLE]=enabled
    expected=0x78 if kind in[1,15]else 0 if pause>=128 else 0x34
    if modal>=128 or enabled<128:expected=0
    elif kind==10:expected=254  # Later amplitude BYTE replaces preselection zero even when pause flag is negative.
    pairs=output(original_image,memory)
    assert pairs[:6]==[(10,expected),(4,0xCD),(5,0xAB),(8,0 if modal>=128 or enabled<128 else 0x45),(0,0x89),(1,0x67)]
    assert pairs[6]==(9,0 if modal>=128 or enabled<128 else 7)


@pytest.mark.parametrize('object_period',[0,1,255,256,32768,65535])
@pytest.mark.parametrize('projectile_period',[0,1,255,256,32768,65535])
def test_periods_emit_raw_low_high_bytes_without_high_nibble_normalization(original_image,memory,object_period,projectile_period):
    prepare(memory);put(memory,OPER,object_period,2);put(memory,PPER,projectile_period,2)
    pairs=output(original_image,memory)
    assert pairs[1:3]==[(4,object_period&255),(5,object_period>>8)]
    assert pairs[4:6]==[(0,projectile_period&255),(1,projectile_period>>8)]


@pytest.mark.parametrize('object_volume',[0,1,0x1234,65535])
@pytest.mark.parametrize('projectile_volume',[0,1,0x1234,65535])
def test_volume_words_emit_low_byte_without_amplitude_clamp(original_image,memory,object_volume,projectile_volume):
    prepare(memory);put(memory,OVOL,object_volume,2);put(memory,PVOL,projectile_volume,2)
    pairs=output(original_image,memory)
    assert pairs[0]==(10,object_volume&255)and pairs[3]==(8,projectile_volume&255)


@pytest.mark.parametrize('star',[0,1,32768,65535])
@pytest.mark.parametrize('envelope',[0,3,32768])
@pytest.mark.parametrize('variation',[0,1,128,255])
@pytest.mark.parametrize('event_volume',[0,1,128,255])
def test_noise_volume_selects_by_word_sign_and_zero_then_uses_old_byte_polarity(original_image,memory,star,envelope,variation,event_volume):
    prepare(memory);put(memory,APP+0x9AE,star,2);put(memory,STARVOL,envelope,2);put(memory,EVENTVOL,event_volume,2)
    memory[VAR]=variation;memory[SETS]=128
    value=envelope&255 if star&32768 or envelope else event_volume
    if not(star&32768 or envelope)and variation>=128:
        value=(value-1)&255
        if value&128:value=0
    pairs=output(original_image,memory)
    assert pairs[6]==(9,value)and len(pairs)==7
    assert memory[VAR]==variation and get(memory,STARVOL,2)==envelope and get(memory,EVENTVOL,2)==event_volume


@pytest.mark.parametrize('star',[0,1,32768,65535])
@pytest.mark.parametrize('sets_noise',[0,1,128,255])
@pytest.mark.parametrize('uses_object',[0,1,128,255])
@pytest.mark.parametrize('variation',[0,1,128,255])
def test_noise_period_writer_guards_polarity_order_and_conditional_rng(original_image,memory,star,sets_noise,uses_object,variation):
    prepare(memory);put(memory,APP+0x9AE,star,2);put(memory,STARVOL,0,2)
    memory[SETS]=sets_noise;memory[USES]=uses_object;memory[VAR]=variation
    skip=bool(star&32768)or sets_noise>=128
    fallback=not skip and uses_object<128
    new=(-variation)&255 if fallback else variation
    pairs=output(original_image,memory)
    old_volume=0 if star&32768 else 12 if variation>=128 else 13
    assert pairs[6]==(9,old_volume)
    if skip:assert len(pairs)==7
    elif uses_object>=128:assert pairs[7:]==[(6,0xCD)]
    else:
        jitter=rng(0x12345678,0xABCDEF01)[1]&3
        assert pairs[7:]==[(6,(255+(1 if new>=128 else 0)+jitter)&255)]
    assert memory[VAR]==new
    assert [get(memory,APP+o)for o in[0x60,0x64]]==list(rng(0x12345678,0xABCDEF01)if fallback else(0x12345678,0xABCDEF01))
    assert get(memory,OPER,2)==0xABCD and get(memory,EVENTNOISE,2)==0x12FF


@pytest.mark.parametrize('entry,value',[(0x4DD40,0x28),(0x4DD5E,8)])
@pytest.mark.parametrize('d0',[0,0xFFFFFFFF])
def test_control_helpers_construct_fixed_byte_and_clobber_d0_only(original_image,memory,entry,value,d0):
    prepare(memory);cpu=state(memory,entry);cpu.d[0]=d0;before_d=list(cpu.d);before_a=list(cpu.a)
    events=trace(original_image,memory,cpu,{RETURN})
    assert events==[(SEL,1,7),(DATA,1,value)]and cpu.d[0]==value
    assert list(cpu.d)[1:]==before_d[1:]and list(cpu.a)[:7]==before_a[:7]and cpu.a[7]==STACK+4


@pytest.mark.parametrize('kind',[1,15])
@pytest.mark.parametrize('phase',[0,6,7,255])
@pytest.mark.parametrize('envelope',[0,1,32768,65535])
def test_control08_caller_sets_object_noise_source_and_mod8_envelope_decay(original_image,memory,kind,phase,envelope):
    prepare(memory);put(memory,TYPE,kind,2);put(memory,APP+0x9AE,0,2);put(memory,ENV,envelope,2)
    memory[0x4DE1E]=phase;memory[0x4DE1F]=0xA5
    left=(phase+1)&7;value=envelope
    if not left:
        value=(value-1)&65535
        if value&32768:value=0
    events=trace(original_image,memory,state(memory,0x4D97C),{0x4DB1E})
    assert events[:2]==[(SEL,1,7),(DATA,1,8)]
    assert events[2:4]==[(SEL,1,10),(DATA,1,value&255)]
    assert events[-2:]==[(SEL,1,6),(DATA,1,0xCD)]
    assert memory[USES]==255 and memory[SETS]==0 and memory[VAR]==1
    assert memory[0x4DE1E]==left and memory[0x4DE1F]==0xA5 and get(memory,ENV,2)==value
    assert [get(memory,APP+o)for o in[0x60,0x64]]==[0x12345678,0xABCDEF01]


@pytest.mark.parametrize('entry',[0x4D9A6,0x4D9AC])
@pytest.mark.parametrize('pause',[0,255])
def test_control28_caller_clears_noise_flags_but_pause_clear_depends_on_entry(original_image,memory,entry,pause):
    prepare(memory);memory[USES]=memory[SETS]=255;memory[PAUSE]=pause
    events=trace(original_image,memory,state(memory,entry),{0x4DB1E})
    expected_pause=0 if entry==0x4D9A6 else pause
    assert events[:2]==[(SEL,1,7),(DATA,1,0x28)]
    assert events[2:4]==[(SEL,1,10),(DATA,1,0 if expected_pause>=128 else 0x34)]
    assert memory[USES]==memory[SETS]==0 and memory[PAUSE]==expected_pause


@pytest.mark.parametrize('d0',[0,1,0xFFFFFFFF])
@pytest.mark.parametrize('kind',[0,65535])
@pytest.mark.parametrize('reset_request',[0,255])
def test_alternate_init_resets_exact_fields_and_restores_d0_without_full_register_reset(original_image,memory,d0,kind,reset_request):
    prepare(memory);put(memory,TYPE,kind,2);memory[RESET-1]=0x11;memory[RESET]=reset_request;memory[RESET+1]=0x22
    cpu=state(memory,0x4DF8E);cpu.d[0]=d0;before_d=list(cpu.d);before_a=list(cpu.a)
    events=trace(original_image,memory,cpu,{RETURN})
    assert events==[(SEL,1,7),(DATA,1,0x28)]
    assert [get(memory,a,2)for a in[TYPE,OVOL,OPER]]==[0,0,0]
    assert bytes(memory[RESET-1:RESET+2])==b'\x11\0\x22'
    assert [get(memory,a,2)for a in[PVOL,PPER,ENV,STARVOL,EVENTVOL]]==[0x2345,0x6789,0x5678,7,13]
    assert list(cpu.d)==before_d and list(cpu.a)[:7]==before_a[:7]and cpu.a[7]==STACK+4


@pytest.mark.parametrize('d0',[0,1,0xFFFFFFFF])
@pytest.mark.parametrize('kind',[0,65535])
def test_paula_init_register_order_distinct_sample_skips_and_retained_software_state(original_image,memory,d0,kind):
    prepare(memory);put(memory,TYPE,kind,2)
    for a,v in[(0x4D0A6,42),(0x4D0A8,65535)]:put(memory,a,v,2)
    put(memory,0x4D0AA,0x11223344);put(memory,0x4D0AE,0x55667788)
    cpu=state(memory,0x4DEDC);cpu.d[0]=d0;before_d=list(cpu.d);before_a=list(cpu.a)
    events=trace(original_image,memory,cpu,{RETURN},PAULA_STORES)
    expected=[]
    for base,pointer,length,volume,period in[(0xDFF0A0,0x59F34,0x2168,24,358),
        (0xDFF0B0,0x5E220,0x1DA,0,1500),(0xDFF0C0,0x5E5F0,0x1212,0,658),(0xDFF0D0,0x4D0CA,20,0,5124)]:
        expected +=[(base,4,pointer),(base+4,2,length),(base+8,2,volume),(base+6,2,period)]
    assert events==expected+[(TYPE,2,0),(0xDFF096,2,0x820F)]
    assert get(memory,0x4D0A6,2)==42 and get(memory,0x4D0A8,2)==65535
    assert get(memory,0x4D0AA)==0x11223344 and get(memory,0x4D0AE)==0x55667788
    assert list(cpu.d)==before_d and list(cpu.a)[1:7]==before_a[1:7]and cpu.a[0]==0x4D0CA and cpu.a[7]==STACK+4


def test_alternate_initializer_is_not_a_full_software_amplitude_clear(original_image,memory):
    prepare(memory);put(memory,APP+0x9AE,0,2);memory[SETS]=128;put(memory,PVOL,0x22,2);put(memory,EVENTVOL,0x33,2)
    trace(original_image,memory,state(memory,0x4DF8E),{RETURN})
    pairs=output(original_image,memory)
    assert pairs[0]==(10,0)and pairs[3]==(8,0x22)and pairs[6]==(9,7)
    # Supplied pre-existing state, not an assertion about a normal startup or audible output.
