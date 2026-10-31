"""Original rotation/settling continuations with explicit supplied CPU contexts.

No all-runtime parity, alias exclusion, spin cadence or gameplay proof follows.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,RETURN
from tests.test_starglider2_control_normalization import signed,word,guard,YAW,PITCH,SPEED,TARGET

IMPULSE,ROT0,ROT1,ROT2,SMOOTH,FREE,POSE=0x78E,0x744,0x746,0x748,0x75A,0xBB9,0xBBA
SPIN,AFTER_SPIN,EJECT=0x39CDA,0x39CDC,0x39B78
AIMX,AIMY,SCREENX,SCREENY,NX,NY,FIXED=0x76A,0x76C,0x766,0x768,0x19C,0x19E,0x7E6


@pytest.mark.parametrize('eject',[0,127,128,255])
@pytest.mark.parametrize('free',[0,1,128,255])
@pytest.mark.parametrize('pose',[0,1,254,255])
@pytest.mark.parametrize('spin',[0,1,32767,32768,65535])
def test_mode_selection_preserves_sign_and_nonzero_gate_priority(original_image,memory,eject,free,pose,spin):
    m=memory;m[EJECT]=eject;m[APP+FREE]=free;m[APP+POSE]=pose;put(m,SPIN,spin,2)
    before=bytes(m[APP:APP+0x1000]);cpu=state(m,0x2F69C)
    stops={RETURN,0x2F8C8,0x2F920,0x2F89C,0x2F6C0}
    run(original_image,m,cpu,stops)
    expected=RETURN if eject&128 else(0x2F8C8 if not free&128 else(0x2F920 if pose else(0x2F89C if spin<32768 else 0x2F6C0)))
    assert cpu.pc==expected and bytes(m[APP:APP+0x1000])==before


@pytest.mark.parametrize('impulse',[-32768,-32767,-3,-2,-1,0,1,2,3,32766,32767])
@pytest.mark.parametrize('rotation',[0,4095,65535])
@pytest.mark.parametrize('control',[-32768,-1,0,1,32767])
@pytest.mark.parametrize('fixed',[0,255])
def test_impulse_is_added_unmasked_before_decay_and_aim_quantization(original_image,memory,impulse,rotation,control,fixed):
    m=memory
    for off,value in [(IMPULSE,impulse),(ROT2,rotation),(PITCH,control),(YAW,control),(NX,32767),(NY,-32768)]:word(m,off,value)
    m[APP+FIXED]=fixed;before=bytes(m[APP:APP+0x1000]);cpu=state(m,0x2F82E)
    run(original_image,m,cpu,{RETURN})
    assert get(m,APP+ROT2,2)==(rotation+impulse)&65535
    assert get(m,APP+IMPULSE,2)==(impulse+(2 if impulse<0 else(-2 if impulse>0 else 0)))&65535
    assert get(m,APP+ROT0,2)==(control>>1)&65535
    x=0 if fixed else control>>2
    y=0 if fixed else signed(-control)>>3
    assert [get(m,APP+o,2)for o in [AIMX,AIMY,SCREENX,SCREENY]]==[v&65535 for v in [x,y,x+32767,y-32768]]
    guard(m,before,[(IMPULSE,2),(ROT2,2),(ROT0,2),(AIMX,2),(AIMY,2),(SCREENX,2),(SCREENY,2)])


@pytest.mark.parametrize('start,stop',[(0x14A2,0x14AE),(0x14E2,0x14EE),(0x8E12,0x8E1E)])
@pytest.mark.parametrize('sample',range(64))
@pytest.mark.parametrize('old',[-32768,-1,0,1,32767])
def test_three_jitter_writers_use_even_masked_addends(original_image,memory,start,stop,sample,old):
    m=memory;word(m,IMPULSE,old);before=bytes(m[APP:APP+0x1000]);cpu=state(m,start)
    cpu.d[0]=0xA5A50000|sample;run(original_image,m,cpu,{stop})
    addend=(sample&62)-32
    assert -32<=addend<=30 and addend%2==0
    assert get(m,APP+IMPULSE,2)==(old+addend)&65535
    assert cpu.d[0]==0xA5A50000|(addend&65535)
    guard(m,before,[(IMPULSE,2)])


@pytest.mark.parametrize('initial',[-3,-2,-1,0,1,2,3])
def test_successive_impulse_calls_preserve_odd_two_cycle(original_image,memory,initial):
    m=memory;word(m,IMPULSE,initial);value=initial
    for _ in range(8):
        cpu=state(m,0x2F82E);run(original_image,m,cpu,{0x2F848})
        value=signed(value+(2 if value<0 else(-2 if value>0 else 0)))
        assert get(m,APP+IMPULSE,2)==value&65535
    assert value==0 if initial%2==0 else value in [-1,1]


@pytest.mark.parametrize('phase',range(256))
def test_contact_pose_branches_write_only_their_original_words(original_image,memory,phase):
    m=memory;m[APP+POSE]=phase
    fields=[YAW,PITCH,ROT0,ROT1,ROT2]
    for off in fields:word(m,off,0x1234)
    before=bytes(m[APP:APP+0x1000]);cpu=state(m,0x2F920);run(original_image,m,cpu,{RETURN})
    expected=[0,0,0,0,0] if phase==255 else([0,0,0,2048,0] if phase==254 else[0x1234,1020,1020,0x1234,0x1234])
    assert [get(m,APP+o,2)for o in fields]==expected
    guard(m,before,[(off,2)for off in fields])


@pytest.mark.parametrize('count',[0,1,2,63,64,32767,32768,65535])
@pytest.mark.parametrize('rotation',[0,4095,65535])
@pytest.mark.parametrize('restore',[0,4095,65535])
def test_spin_decrements_before_sign_test_and_restores_without_mask(original_image,memory,count,rotation,restore):
    m=memory;put(m,SPIN,count,2);put(m,AFTER_SPIN,restore,2);word(m,ROT2,rotation)
    before=bytes(m[APP:APP+0x1000]);cpu=state(m,0x2F89C);run(original_image,m,cpu,{RETURN})
    decremented=signed(count-1)
    assert get(m,SPIN,2)==(65535 if decremented<0 else decremented)
    assert get(m,APP+ROT2,2)==(restore if decremented<0 else(rotation+64)&4095)
    guard(m,before,[(ROT2,2)])


def test_64_spin_steps_then_separate_expiry_call(original_image,memory):
    m=memory;put(m,SPIN,64,2);put(m,AFTER_SPIN,0xFEDC,2);word(m,ROT2,123)
    for step in range(64):
        cpu=state(m,0x2F89C);run(original_image,m,cpu,{RETURN})
        assert get(m,SPIN,2)==63-step
        assert get(m,APP+ROT2,2)==(123+64*(step+1))&4095
    cpu=state(m,0x2F89C);run(original_image,m,cpu,{RETURN})
    assert get(m,SPIN,2)==65535 and get(m,APP+ROT2,2)==0xFEDC


def test_all_4096_settling_phases_and_six_arithmetic_halves(original_image,memory):
    m=memory;fields=[YAW,PITCH,0x7A6,SPEED,TARGET,SMOOTH]
    initial=[-32768,-1,1,3,-3,32767]
    for phase in range(4096):
        for off,value in zip(fields,initial):word(m,off,value)
        word(m,ROT0,phase);m[APP+FREE]=0x11;before=bytes(m[APP:APP+0x1000])
        cpu=state(m,0x2F8C8);run(original_image,m,cpu,{RETURN})
        result=(phase+6)&4095
        assert get(m,APP+ROT0,2)==result and m[APP+FREE]==(255 if result==0 else 0x11)
        assert [get(m,APP+off,2)for off in fields]==[(value>>1)&65535 for value in initial]
        guard(m,before,[(off,2)for off in fields]+[(ROT0,2),(FREE,1)])


@pytest.mark.parametrize('phase',[0,2,4090,1,4095])
def test_settling_repeated_calls_preserve_odd_phase_and_negative_one(original_image,memory,phase):
    m=memory;word(m,ROT0,phase);word(m,PITCH,-1);m[APP+FREE]=0
    expected_steps=next((n for n in range(1,2049)if(phase+6*n)&4095==0),None)
    steps=expected_steps or 2048
    for index in range(steps):
        cpu=state(m,0x2F8C8);run(original_image,m,cpu,{RETURN})
        assert get(m,APP+PITCH,2)==65535
        assert m[APP+FREE]==(255 if expected_steps and index+1==expected_steps else 0)
    assert bool(m[APP+FREE])==bool(expected_steps)
