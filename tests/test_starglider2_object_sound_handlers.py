"""Original descriptor-gated software handlers, with device addresses as RAM.

Stop before the saved-register restore after executing original instructions. Register
writes are checked as stored values only: no DMA, PCM, timing, complete-frame,
normal-caller, selector-domain or object-lifetime claim follows from these states.
"""
import ctypes
import pytest
from tests.test_starglider2_text_editor import original_image,memory as small_memory,state,run,put,get,APP,INPUT

OBJ=INPUT+0x100
TYPE,BASE,VOL,SMOOTH,TRANS=0x39CE0,0x4D09E,0x4D09C,0x4D084,0x4D0A6
ENABLE,ENV,RAMP,PHASE=0x39CD5,0x4D0B4,0x4D12E,0x4D0B2
SPEED_PERIOD,SPEED_ENV,SNAPSHOT=0x4D0BC,0x4D0BE,0x4D0C0
PER,OUT=0xDFF0D6,0xDFF0D8
TABLES={5:(0x4D130,18),46:(0x4D130,18),17:(0x4D15C,10),19:(0x4D170,16),36:(0x4D190,24)}
SENTINEL=0xA55A


@pytest.fixture
def memory(small_memory):
    result=(ctypes.c_uint8*0xE00000)()
    ctypes.memmove(result,small_memory,len(small_memory))
    put(result,BASE,500,2);put(result,VOL,30,2);put(result,SMOOTH,25,2)
    put(result,TRANS,65535,2);put(result,ENV,20,2);put(result,RAMP,5,2)
    put(result,SPEED_ENV,5,2);put(result,SPEED_PERIOD,358,2)
    result[ENABLE]=128;result[APP+0x6DA]=0
    put(result,PER,SENTINEL,2);put(result,OUT,SENTINEL,2)
    return result


def n(v):return bool(v&32768)
def decay(v,step):
    v=(v-step)&65535
    return 0 if n(v)else v


def execute(image,memory,kind,variant=0,entry=0x4C1CA):
    put(memory,TYPE,kind,2);memory[OBJ+3]=variant
    cpu=state(memory,entry);cpu.a[2]=OBJ
    run(image,memory,cpu,{0x4C5D8})
    return cpu


def generic_period(base,kind,flags,phase):
    if kind!=16 and flags&12:base=(base-((phase if phase<128 else phase-256)<<5))&65535
    return 124 if n(base-124)else base


@pytest.mark.parametrize('kind',[1,15])
@pytest.mark.parametrize('variant',[0,8,10,18,22,128,255])
@pytest.mark.parametrize('envelope',[0,3,4,20,32768,65535])
def test_types1_15_variant_latches_then_four_unit_decay(original_image,memory,kind,variant,envelope):
    put(memory,ENV,envelope,2)
    expected=decay(30 if variant in({10,22}if kind==1 else{8,18})else envelope,4)
    execute(original_image,memory,kind,variant)
    assert get(memory,ENV,2)==get(memory,OUT,2)==expected
    assert get(memory,PER,2)==SENTINEL and get(memory,VOL,2)==30


@pytest.mark.parametrize('variant',[0,1,127,128,255])
def test_type4_signed_byte_period_formula(original_image,memory,variant):
    execute(original_image,memory,4,variant)
    expected=(728-((variant if variant<128 else variant-256)<<4))&65535
    assert get(memory,BASE,2)==expected
    assert get(memory,PER,2)==generic_period(expected,4,0,0)


@pytest.mark.parametrize('kind',[5,46])
@pytest.mark.parametrize('variant',[0,1,8,9,17,128,255])
@pytest.mark.parametrize('ramp',[0,3,30,32767,32768,65535])
def test_types5_46_signed_table_index_and_wrapped_ramp(original_image,memory,kind,variant,ramp):
    put(memory,RAMP,ramp,2);base=get(memory,BASE,2)
    if variant in[0,9]:expected=decay(ramp,4);period=SENTINEL
    else:
        expected=(ramp+1)&65535
        if not n(expected-30):expected=30
        index=variant if variant<128 else variant-256
        base=expected if index==-1 else get(memory,TABLES[kind][0]+2*index,2);period=base
    execute(original_image,memory,kind,variant)
    assert get(memory,RAMP,2)==get(memory,VOL,2)==get(memory,OUT,2)==expected
    assert get(memory,BASE,2)==base and get(memory,PER,2)==period
    # Negative indices deliberately read original preceding bytes, not an asserted valid table domain.


@pytest.mark.parametrize('kind',[56,57,58])
@pytest.mark.parametrize('speed',[0,1,295,480,654,32768,65535])
@pytest.mark.parametrize('period',[173,174,358,653,654,65535])
def test_types56_58_speed_envelope_and_conditional_period_limits(original_image,memory,kind,speed,period):
    put(memory,APP+0x758,speed,2);put(memory,SPEED_PERIOD,period,2)
    target=(654-speed)&65535;expected=period
    if target!=period:
        if n(target-period):
            expected=(period-2)&65535
            if n(expected-174):expected=174
        else:
            expected=(period+2)&65535
            if not n(expected-654):expected=654
    execute(original_image,memory,kind)
    assert get(memory,SPEED_ENV,2)==(6 if speed else 4)
    assert get(memory,SPEED_PERIOD,2)==get(memory,PER,2)==expected
    assert get(memory,OUT,2)==(6 if speed else 4)


@pytest.mark.parametrize('kind',[17,19,36])
@pytest.mark.parametrize('variant',[0,1,9,15,23,128,255])
def test_signed_period_prefix_reads_do_not_impose_runtime_table_bounds(original_image,memory,kind,variant):
    signed=variant if variant<128 else variant-256
    expected=get(memory,TABLES[kind][0]+2*signed,2)
    execute(original_image,memory,kind,variant)
    assert get(memory,BASE,2)==expected
    assert get(memory,PER,2)==generic_period(expected,kind,0,0)
    assert get(memory,VOL,2)==((30+9-signed)&65535 if kind==17 else 30)


@pytest.mark.parametrize('phase',[0,8,9,10,30,31,65535])
@pytest.mark.parametrize('variant',[0,1,127,128,255])
@pytest.mark.parametrize('smooth',[0,3,4,32768,65535])
def test_type10_mod32_decay_and_signed_period_bias(original_image,memory,phase,variant,smooth):
    put(memory,PHASE,phase,2);put(memory,SMOOTH,smooth,2)
    p=(phase+1)&31;v=decay(smooth,4)if p>=10 else smooth
    signed=variant if variant<128 else variant-256;base=(500+(signed<<2)-50)&65535
    execute(original_image,memory,10,variant)
    assert get(memory,PHASE,2)==p and get(memory,SMOOTH,2)==get(memory,VOL,2)==v
    assert get(memory,BASE,2)==base and get(memory,PER,2)==generic_period(base,10,0,0)


@pytest.mark.parametrize('kind',[3,11,64])
@pytest.mark.parametrize('variant',[0,1,127,128,255])
def test_snapshot_signed_volume_and_direct_period_bypass_are_distinct(original_image,memory,kind,variant):
    put(memory,OBJ+18,0xBEEF,2);put(memory,SNAPSHOT,0x1234,2)
    execute(original_image,memory,kind,variant)
    signed=variant if variant<128 else variant-256
    assert get(memory,SNAPSHOT,2)==(0xBEEF if kind==3 else 0x1234)
    assert get(memory,VOL,2)==((30+signed)&65535 if kind==11 else 30)
    assert get(memory,PER,2)==(SENTINEL if kind==3 else (500+(signed<<4))&65535 if kind==64 else 500)
    assert get(memory,OUT,2)==(SENTINEL if kind==3 else get(memory,VOL,2))


@pytest.mark.parametrize('kind',[0,16,11])
@pytest.mark.parametrize('flags',[0,4,8,12])
@pytest.mark.parametrize('phase',[0,1,127,128,255])
def test_common_period_floor_signed_phase_adjustment_and_type16_exception(original_image,memory,kind,flags,phase):
    memory[OBJ+2]=flags;memory[OBJ+30]=phase
    execute(original_image,memory,kind,entry=0x4C572)
    assert get(memory,PER,2)==generic_period(500,kind,flags,phase)


@pytest.mark.parametrize('kind',[0,1,5,56,64])
@pytest.mark.parametrize('modal',[0,128])
@pytest.mark.parametrize('enabled',[0,128])
@pytest.mark.parametrize('transition',[0,65535])
def test_output_gates_mute_or_leave_previous_register_value(original_image,memory,kind,modal,enabled,transition):
    memory[APP+0x6DA]=modal;memory[ENABLE]=enabled;put(memory,TRANS,transition,2)
    execute(original_image,memory,kind,1,entry=0x4C572 if kind==0 else 0x4C1CA)
    expected=0 if modal>=128 or enabled<128 else SENTINEL if transition<32768 else get(memory,ENV if kind==1 else SPEED_ENV if kind==56 else VOL,2)
    assert get(memory,OUT,2)==expected


@pytest.mark.parametrize('kind',[0,2,16,20,91,103])
def test_unhandled_type_in_handler_chain_does_not_imply_common_period_path(original_image,memory,kind):
    execute(original_image,memory,kind)
    assert get(memory,PER,2)==get(memory,OUT,2)==SENTINEL
    assert get(memory,BASE,2)==500 and get(memory,VOL,2)==30


@pytest.mark.parametrize('kind',[0,4,16,17,64])
@pytest.mark.parametrize('gate',[0,1,32768,65535])
def test_descriptor_word14_zero_gate_selects_common_or_specific_path(original_image,memory,kind,gate):
    put(memory,0x4CBF4+16*kind+14,gate,2)
    execute(original_image,memory,kind,entry=0x4C182)
    expected=500 if not gate else 728 if kind==4 else get(memory,TABLES[17][0],2)if kind==17 else 500 if kind==64 else SENTINEL
    assert get(memory,PER,2)==expected
    assert get(memory,OUT,2)==(34 if gate and kind==17 else SENTINEL if gate and kind in[0,16]else 25)


@pytest.mark.parametrize('period',[0,123,124,125,32767,32768,65535])
def test_common_minimum_uses_original_word_subtraction_sign(original_image,memory,period):
    put(memory,BASE,period,2)
    execute(original_image,memory,16,entry=0x4C572)
    assert get(memory,PER,2)==(124 if n(period-124)else period)
