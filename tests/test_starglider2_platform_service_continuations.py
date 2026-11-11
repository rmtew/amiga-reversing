"""Original service continuations with supplied callee flags and RAM ports.

Enter after the named change/read/retry helpers; those helpers are not mocked
or executed here. Serial readiness is a supplied port sequence. These cases
qualify local BYTE/CCR/control flow, not disk I/O, device delivery or timing.
"""
import pytest
from tests.test_starglider2_alternate_palette_interrupt import sparse_memory
from tests.test_starglider2_text_editor import original_image,state,run,put,get,STACK,RETURN

PLATFORM,DISK_CHANGE,SERIAL=0x1002,0xBFE001,0xFFFFFC00


def storage(image,memory,remaining=0xA5,reload=0x73):
    raw=image[0];base=get(raw,0x109A6-4096);source=get(raw,0x109A2-4096)
    assert source==base+3
    memory[base:base+16]=b'\xA5'*16;memory[base]=remaining;memory[source]=reload
    return base,bytes(memory[base:base+16])


@pytest.mark.parametrize('zero',[False,True])
@pytest.mark.parametrize('reload',[0,1,127,128,255])
def test_change_status_gates_retry_reload_without_running_callees(original_image,sparse_memory,zero,reload):
    m=sparse_memory;base,before=storage(original_image,m,reload=reload)
    cpu=state(m,0x1099E);cpu.sr=0x271B|(4 if zero else 0);d=list(cpu.d);a=list(cpu.a)
    run(original_image,m,cpu,{0x109AA,RETURN})
    expected=bytearray(before)
    if zero:expected[0]=reload
    assert bytes(m[base:base+16])==expected
    assert cpu.pc==(0x109AA if zero else RETURN)
    assert cpu.d[0]==(d[0] if zero else 0xFFFFFFFF)and list(cpu.d[1:])==d[1:]
    assert list(cpu.a[:7])==a[:7]and cpu.a[7]==STACK+(0 if zero else 4)


@pytest.mark.parametrize('zero',[False,True])
def test_read_status_returns_zero_or_reaches_retry_call(original_image,sparse_memory,zero):
    m=sparse_memory;base,before=storage(original_image,m)
    cpu=state(m,0x109AE);cpu.sr=0x271B|(4 if zero else 0);d=list(cpu.d);a=list(cpu.a)
    run(original_image,m,cpu,{0x109B0,RETURN})
    assert bytes(m[base:base+16])==before
    assert cpu.pc==(RETURN if zero else 0x109B0)
    assert cpu.d[0]==(0 if zero else d[0])and list(cpu.d[1:])==d[1:]
    assert list(cpu.a[:7])==a[:7]and cpu.a[7]==STACK+(4 if zero else 0)


@pytest.mark.parametrize('platform',[0,0x7FFF,0x8000,0xFFFF])
@pytest.mark.parametrize('port',[0,4,255])
@pytest.mark.parametrize('remaining',[0,1,127,128,129,255])
def test_post_retry_port_gate_precedes_wrapping_signed_byte_budget(original_image,sparse_memory,platform,port,remaining):
    m=sparse_memory;base,before=storage(original_image,m,remaining=remaining)
    put(m,PLATFORM,platform,2);m[DISK_CHANGE]=port
    cpu=state(m,0x109B4);d=list(cpu.d);a=list(cpu.a)
    run(original_image,m,cpu,{0x109AA,RETURN})
    early=bool(platform&0x8000)and not(port&4)
    after=remaining if early else(remaining-1)&255
    retry=not early and after<128
    expected=bytearray(before);expected[0]=after
    assert bytes(m[base:base+16])==expected and m[DISK_CHANGE]==port
    assert cpu.pc==(0x109AA if retry else RETURN)
    assert cpu.d[0]==(d[0] if retry else 0xFFFFFFFF)and list(cpu.d[1:])==d[1:]
    assert list(cpu.a[:7])==a[:7]and cpu.a[7]==STACK+(0 if retry else 4)


@pytest.mark.parametrize('other_bits',[0,1,0x7D,0xFD])
@pytest.mark.parametrize('waiting_reads',[0,1,5])
def test_serial_status_poll_preserves_registers_and_only_clears_z_on_return(original_image,sparse_memory,other_bits,waiting_reads):
    m=sparse_memory;cpu=state(m,0x3B57C);cpu.sr=0x271F;d=list(cpu.d);a=list(cpu.a);reads=[]
    def port_sequence(pc):
        if pc==0x3B57C:
            reads.append(pc);m[SERIAL]=(other_bits&~2)|(2 if len(reads)>waiting_reads else 0)
    run(original_image,m,cpu,{RETURN},port_sequence)
    assert len(reads)==waiting_reads+1 and m[SERIAL]==(other_bits|2)
    assert list(cpu.d)==d and list(cpu.a[:7])==a[:7]and cpu.a[7]==STACK+4
    assert cpu.sr==0x271B
