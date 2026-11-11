"""Original startup/clock routines with explicit CCR, tick and RAM-port inputs.

These cases do not deliver interrupts or prove elapsed time, RNG distributions,
auxiliary-state consumers, normal startup or physical CIA behavior.
"""
import pytest
from tests.test_starglider2_alternate_palette_interrupt import sparse_memory
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,STACK,RETURN

CLOCK,SAMPLE,PLATFORM=0x27AC,0x27BA,0x1002
TOD_HI,TOD_MID,TOD_LOW=0xBFDA00,0xBFD900,0xBFD800


@pytest.mark.parametrize('seed',[0,0x1357,0xFF00,0x80FF,0xFFFF,0x0100])
@pytest.mark.parametrize('extend',[0,1])
def test_initializer_has_fixed_active_states_but_carry_dependent_auxiliary_bytes(original_image,memory,seed,extend):
    m=memory;m[APP:APP+0x200]=b'\xA5'*0x200;put(m,APP+0x1B0,seed,2)
    expected=bytearray(m[APP:APP+0x200]);hi,lo=seed>>8,seed&255
    combined=(hi+lo+extend)&255;shifted=(combined<<1)&255
    secondary=(shifted+lo+(combined>>7))&255
    expected[0x34:0x3A]=bytes([hi,combined,lo,shifted,secondary,secondary>>1])
    expected[0x3C:0x40]=(0x314159).to_bytes(4,'big')
    expected[0x60:0x68]=bytes.fromhex('9590114328731549')
    cpu=state(m,0x261A);cpu.sr=0x270F|(extend<<4);d=list(cpu.d);a=list(cpu.a)
    run(original_image,m,cpu,{RETURN})
    assert bytes(m[APP:APP+0x200])==expected
    assert cpu.d[0]==(d[0]&0xFFFFFF00)|(secondary>>1)
    assert cpu.d[1]==(d[1]&0xFFFFFF00)|lo and list(cpu.d[2:])==d[2:]
    assert list(cpu.a[:7])==a[:7]and cpu.a[7]==STACK+4
    assert cpu.sr==0x2700|((secondary&1)<<4)


@pytest.mark.parametrize('entry,stop,subtract',[(0x1324,0x1356,True),(0x135E,0x138C,False),
                                               (0xEAD2,0xEB04,True),(0xEB08,0xEB36,False)])
@pytest.mark.parametrize('platform',[0,0x7FFF,0x8000,0xFFFF])
@pytest.mark.parametrize('port_sample',[0,1,0x7FFF,0xFFFF])
@pytest.mark.parametrize('previous',[0,0xFFFF])
def test_shared_clock_word_aliases_delta_and_sample_by_phase(original_image,sparse_memory,entry,stop,subtract,platform,port_sample,previous):
    m=sparse_memory;m[CLOCK-2:CLOCK+18]=b'\xA5'*20;put(m,SAMPLE,previous,2)
    before=bytes(m[CLOCK-2:CLOCK+18]);put(m,PLATFORM,platform,2)
    m[TOD_HI]=0xA7;m[TOD_MID]=port_sample>>8;m[TOD_LOW]=port_sample&255
    inherited=port_sample^0xA55A
    cpu=state(m,entry);cpu.d[0]=(cpu.d[0]&0xFFFF0000)|inherited;d=list(cpu.d);a=list(cpu.a)
    sample=port_sample if platform&0x8000 else inherited
    expected=bytearray(before);expected[16:18]=((sample-previous if subtract else sample)&65535).to_bytes(2,'big')
    run(original_image,m,cpu,{stop})
    assert bytes(m[CLOCK-2:CLOCK+18])==expected
    assert list(cpu.d)==d and list(cpu.a)==a
    assert [m[x]for x in[TOD_HI,TOD_MID,TOD_LOW]]==[0xA7,port_sample>>8,port_sample&255]


@pytest.mark.parametrize('initial',[0,0xFFFE,0xFFFF])
@pytest.mark.parametrize('sequence',['immediate','successive','skipped_then_equal'])
@pytest.mark.parametrize('mouse',[(0,0),(1,2),(255,255),(128,127)])
@pytest.mark.parametrize('seeds',[(0,0),(0xFFFFFFFF,0xFFFFFFFE)])
def test_tick_target_is_exact_word_equality_and_each_poll_mixes_mouse_bytes(original_image,memory,initial,sequence,mouse,seeds):
    m=memory;m[APP:APP+0x210]=b'\xA5'*0x210;mx,my=mouse
    put(m,APP+0x17C,initial,2);m[APP+0x1FF]=mx;m[APP+0x200]=my
    put(m,APP+0x60,seeds[0]);put(m,APP+0x64,seeds[1])
    expected=bytearray(m[APP:APP+0x210]);target=(initial+2)&65535
    samples=[target]if sequence=='immediate'else[initial,(initial+(1 if sequence=='successive'else 3))&65535,target]
    a,b=seeds
    for _ in samples:
        a=(a&0xFFFF00FF)|(((((a>>8)&255)+mx)&255)<<8)
        b=(b&0xFFFFFF00)|(((b&255)+my)&255)
        a=(a-7)&0xFFFFFFFF;b=(b+5)&0xFFFFFFFF
    expected[0x60:0x68]=a.to_bytes(4,'big')+b.to_bytes(4,'big')
    expected[0x17C:0x17E]=target.to_bytes(2,'big')
    cpu=state(m,0x38C8);d=list(cpu.d);regs=list(cpu.a);seen=[]
    def tick(pc):
        if pc==0x38CE:
            assert len(seen)<len(samples),'Unexpected extra poll after target sample'
            put(m,APP+0x17C,samples[len(seen)],2);seen.append(pc)
    run(original_image,m,cpu,{RETURN},tick)
    assert len(seen)==len(samples)and bytes(m[APP:APP+0x210])==expected
    assert cpu.d[0]==(d[0]&0xFFFF0000)|target
    assert cpu.d[1]==(d[1]&0xFFFFFF00)|my and list(cpu.d[2:])==d[2:]
    assert list(cpu.a[:7])==regs[:7]and cpu.a[7]==STACK+4


def test_version_banner_entry_resets_queue_then_tail_calls_its_normal_enqueue_bridge(original_image,memory):
    m=memory;put(m,APP+0x7AE,5,2);put(m,APP+0x7B4,0x5678,2)
    cpu=state(m,0x1E76);d=list(cpu.d);a=list(cpu.a)
    run(original_image,m,cpu,{0x49DA})
    assert get(m,APP+0x7AE,2)==0 and get(m,APP+0x7B4,2)==1
    version=b'SG2 - Version 1.03 USA.'
    assert cpu.a[1]==0x278C and bytes(m[0x278C:0x278C+len(version)])==version
    assert m[0x278C+len(version)]==0 and list(cpu.d)==d
    assert [cpu.a[i]for i in[0,2,3,4,5,6,7]]==[a[i]for i in[0,2,3,4,5,6,7]]
