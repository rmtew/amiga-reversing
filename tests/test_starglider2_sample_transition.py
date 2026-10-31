"""Original sample-transition/type-3 service, device registers represented as RAM.

Trace CPU store order and values, stopping before palette service. No Paula,
DMA, PCM, timing, complete-frame, caller-domain or sample-lifetime simulation.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,state,run,put,get,APP
from tests.test_starglider2_object_sound_handlers import memory,small_memory,execute,OBJ,TYPE,BASE,VOL,SMOOTH,TRANS,ENABLE,PER,OUT,SENTINEL
from tests.test_starglider2_scan_acquisition import signed16

RESTART,REQUESTED,PREVIOUS=0x4D0A8,0x4D0AA,0x4D0AE
CURRENT,BASEVOL=0x4D096,0x4D0A2
SIGN,UP,DOWN,STEP=0x4D264,0x4D266,0x4D268,0x4D0C0
DESC,SHIFTS,PTR,LENGTH,DMA=0x4CBF4,0x4D320,0xDFF0D0,0xDFF0D4,0xDFF096
# Original instruction identities: capture stores even when the stored value is unchanged.
STORES={0x4C686:(OUT,2),0x4C690:(OUT,2),0x4C6A8:(DMA,2),
        0x4C6D2:(PTR,4),0x4C6E8:(LENGTH,2),0x4C70C:(DMA,2),
        0x4C764:(PER,2),0x4C77A:(OUT,2),0x4C784:(OUT,2)}


def service(image,memory):
    pending=None;events=[]
    def observe(pc):
        nonlocal pending
        if pending is not None:
            address,width=STORES[pending];events.append((pending,address,width,get(memory,address,width)))
        pending=pc if pc in STORES else None
    run(image,memory,state(memory,0x4C62C),{0x4C78E},observe)
    if pending is not None:
        address,width=STORES[pending];events.append((pending,address,width,get(memory,address,width)))
    return events


def prepare(memory,kind=1,phase=11,restart=65535):
    put(memory,TYPE,kind,2);put(memory,TRANS,phase,2);put(memory,RESTART,restart,2)
    put(memory,REQUESTED,0x11223344);put(memory,PREVIOUS,0x55667788)
    put(memory,CURRENT,1234,2);put(memory,BASEVOL,23,2)
    put(memory,SIGN,1,2);put(memory,UP,17,2);put(memory,DOWN,239,2);put(memory,STEP,2,2)
    put(memory,PTR,0xA55AA55A);put(memory,LENGTH,SENTINEL,2);put(memory,DMA,SENTINEL,2)


def outputs(events):return[(address,width,value)for _,address,width,value in events]


@pytest.mark.parametrize('phase',[0,1,6,7,8,11,12,32767,32768,65535])
@pytest.mark.parametrize('restart',[0,1,32768,65535])
def test_transition_entry_signs_decrement_before_shift_and_preserve_restart_rules(original_image,memory,phase,restart):
    prepare(memory,phase=phase,restart=restart)
    skip=bool(phase&32768)and not(restart&32768)
    p=phase if skip else(phase-1)&65535
    active=not skip and not(p&32768)
    count=get(memory,SHIFTS+signed16(2*p),2)&63 if active else 0
    expected_volume=30>>count if count<16 else 0
    events=service(original_image,memory)
    assert get(memory,TRANS,2)==(p if skip or active else 65535)
    assert get(memory,RESTART,2)==(0 if phase&32768 and restart&32768 else restart)
    if active:
        assert outputs(events)[0]==(OUT,2,expected_volume)
        if p==7:assert outputs(events)[1:]==[(DMA,2,8)]
        elif p==6:
            assert [address for _,address,_,_ in events]==[OUT,PTR,LENGTH,DMA]
        else:assert len(events)==1
    else:assert events==[]
    # Out-of-prefix cases preserve original WORD indexing; table length is no runtime bound.


@pytest.mark.parametrize('kind',range(71))
def test_phase6_copies_stored_descriptor_prefix_and_snapshots_old_request(original_image,memory,kind):
    prepare(memory,kind,phase=7)
    sample=get(memory,DESC+16*kind);length=get(memory,DESC+16*kind+4,2)
    period=get(memory,DESC+16*kind+6,2);volume=get(memory,DESC+16*kind+8,2)
    events=service(original_image,memory);o=outputs(events)
    assert o[:4]==[(OUT,2,30>>5),(PTR,4,(sample+6)&0xFFFFFFFF),(LENGTH,2,length),(DMA,2,0x8208)]
    assert get(memory,PREVIOUS)==0x11223344 and get(memory,REQUESTED)==(sample+6)&0xFFFFFFFF
    assert get(memory,BASE,2)==get(memory,CURRENT,2)==period and get(memory,BASEVOL,2)==volume
    assert get(memory,SMOOTH,2)==0 and get(memory,RESTART,2)==65535
    if kind!=3:assert len(events)==4
    else:
        assert o[4:]==[(PER,2,(period+236)&65535),(OUT,2,30)]
        assert get(memory,CURRENT,2)==period  # Later modulation changes output only.


@pytest.mark.parametrize('pointer',[0,0xFFFFFFFC,0xFFFFFFFF])
@pytest.mark.parametrize('length',[0,1,65535])
def test_phase6_pointer_add_wrap_and_word_length_are_not_dma_safety_proofs(original_image,memory,pointer,length):
    prepare(memory,phase=7);put(memory,DESC+16,pointer);put(memory,DESC+20,length,2)
    events=service(original_image,memory)
    assert outputs(events)[1:]==[(PTR,4,(pointer+6)&0xFFFFFFFF),(LENGTH,2,length),(DMA,2,0x8208)]


@pytest.mark.parametrize('phase',[0,1,6,7,8,11,65535])
@pytest.mark.parametrize('step',[0,1,2,255,32768,65535])
@pytest.mark.parametrize('sign',[0,1,32768,65535])
def test_type3_odd_step_masked_offsets_sign_negation_and_expiry_skip(original_image,memory,phase,step,sign):
    prepare(memory,3,phase,restart=0);put(memory,STEP,step,2);put(memory,SIGN,sign,2)
    put(memory,BASE,65535,2)
    events=service(original_image,memory)
    if phase==0:
        assert events==[] and get(memory,UP,2)==17 and get(memory,DOWN,2)==239 and get(memory,SIGN,2)==sign
        return
    odd=step|1;up=(17+odd)&255;down=(239-odd)&255;new_sign=(-sign)&65535
    period=get(memory,BASE,2)
    assert get(memory,UP,2)==up and get(memory,DOWN,2)==down and get(memory,SIGN,2)==new_sign
    offset=down if new_sign&32768 else up
    assert outputs(events)[-2:]==[(PER,2,(period+offset)&65535),(OUT,2,30)]
    assert get(memory,STEP,2)==step
    assert get(memory,CURRENT,2)==(period if phase==7 else 1234)
    # Zero and $8000 signs do not alternate under NEG.W. No common-period floor here.


@pytest.mark.parametrize('kind',[1,3])
@pytest.mark.parametrize('phase',[1,7,8,65535])
@pytest.mark.parametrize('modal',[0,128])
@pytest.mark.parametrize('enabled',[0,128])
def test_output_gates_and_later_type3_write_order(original_image,memory,kind,phase,modal,enabled):
    prepare(memory,kind,phase,restart=0);memory[APP+0x6DA]=modal;memory[ENABLE]=enabled
    events=service(original_image,memory);values=[value for _,address,_,value in events if address==OUT]
    muted=modal>=128 or enabled<128
    expected=[]
    if phase!=65535:expected.append(0 if muted else 30>>(get(memory,SHIFTS+2*(phase-1),2)&63))
    if kind==3:expected.append(0 if muted else 30)
    assert values==expected
    assert [value for _,address,_,value in events if address==DMA]==([0x8208]if phase==7 else[8]if phase==8 else[])


@pytest.mark.parametrize('restart',[0,65535])
def test_serial_restart_runs_original_shift_order_dma_commands_then_idle_type3_service(original_image,memory,restart):
    prepare(memory,3,restart=restart);trace=[];observed=[]
    for _ in range(14):
        events=service(original_image,memory);trace.extend(events)
        observed.append(get(memory,TRANS,2))
    assert observed==[10,9,8,7,6,5,4,3,2,1,0,65535,65535,65535]
    assert [(pc,value)for pc,address,_,value in trace if address==DMA]==[(0x4C6A8,8),(0x4C70C,0x8208)]
    assert len([1 for _,address,_,_ in trace if address==PTR])==1
    assert len([1 for _,address,_,_ in trace if address==PER])==(12 if restart else 13)
    # Expiry always skips type3; a pending-flag clear on the next call also skips it.
    assert get(memory,RESTART,2)==0  # Cleared on the later idle entry, not at positive phase11.


@pytest.mark.parametrize('step',[0,1,2,255,32768,65535])
def test_original_selected_object_snapshot_feeds_later_type3_service(original_image,memory,step):
    prepare(memory,3,phase=65535,restart=0)
    put(memory,OBJ+18,step,2)
    execute(original_image,memory,3)
    assert get(memory,STEP,2)==step
    events=service(original_image,memory)
    assert get(memory,DOWN,2)==(239-(step|1))&255
    assert outputs(events)[-2:]==[(PER,2,(500+((239-(step|1))&255))&65535),(OUT,2,30)]


@pytest.mark.parametrize('count',[0,1,15,16,31,32,63,64,65,65535])
@pytest.mark.parametrize('volume',[0,1,32768,65535])
def test_shift_word_uses_register_count_low6_bits_and_unsigned_volume(original_image,memory,count,volume):
    prepare(memory,phase=1);put(memory,SHIFTS,count,2);put(memory,VOL,volume,2)
    events=service(original_image,memory)
    shift=count&63
    assert outputs(events)==[(OUT,2,volume>>shift if shift<16 else 0)]
    # Supplied shift-table state, not evidence that the original writer produces these counts.
