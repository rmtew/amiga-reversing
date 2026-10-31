"""Installed original alternate callback with a supplied 68000 exception frame.

Sparse anonymous virtual address space represents sign-extended absolute-W
ports as RAM. Only touched pages consume memory; this is not a chipset model,
interrupt delivery, vector-base setup, physical scanline timing or boot proof.
"""
import ctypes
import mmap
import pytest
from tests.test_starglider2_text_editor import original_image,state,run,put,get,APP,STACK,RETURN

FLAG,BUFFER,OTHER,PALETTE=0x3BD4A,0x3BD4C,0x5341C,0xFFFF8240
ENABLE,MASK,SERVICE,CONTROL,DATA=0xFFFFFA07,0xFFFFFA13,0xFFFFFA0F,0xFFFFFA1B,0xFFFFFA21


@pytest.fixture
def sparse_memory(original_image):
    if ctypes.sizeof(ctypes.c_void_p)<8:pytest.skip('Sparse 32-bit address-space fixture requires a 64-bit host')
    mapping=mmap.mmap(-1,1<<32)
    memory=(ctypes.c_uint8*(1<<32)).from_buffer(mapping)
    ctypes.memmove(ctypes.addressof(memory)+0x1000,original_image[0],len(original_image[0]))
    # The ctypes buffer retains the anonymous mapping until the fixture is released.
    return memory


def enter(memory):
    cpu=state(memory,0x3BCD2);cpu.sr=0x2600
    put(memory,STACK,0x2315,2);put(memory,STACK+2,RETURN)
    return cpu


@pytest.mark.parametrize('initial',[0,1,2,128,255])
def test_both_callback_phases_preserve_registers_and_return_exception_frame(original_image,sparse_memory,initial):
    m=sparse_memory;m[FLAG]=initial;m[FLAG+1]=0x7D
    m[BUFFER:BUFFER+26]=bytes(range(26));m[OTHER:OTHER+32]=bytes(range(80,112))
    m[PALETTE-2:PALETTE+34]=b'\xA5'*36
    for a in[ENABLE,MASK,SERVICE]:m[a]=0xB7
    m[CONTROL]=0xC1;m[DATA]=0x23
    cpu=enter(m);d=list(cpu.d);a=list(cpu.a);stack=bytes(m[STACK:STACK+6])
    run(original_image,m,cpu,{RETURN})
    expected=bytearray(b'\xA5'*32)
    if initial:
        expected[:]=bytes(range(80,112));assert m[FLAG]==0
        assert [m[x]for x in[ENABLE,MASK,SERVICE,CONTROL,DATA]]==[0xB6,0xB6,0xB6,0,0x23]
    else:
        for dest,source,width in[(0,0,4),(6,4,4),(10,8,4),(22,12,4),(26,16,4),(30,20,2)]:
            expected[dest:dest+width]=bytes(range(source,source+width))
        assert m[FLAG]==1
        assert [m[x]for x in[ENABLE,MASK,SERVICE,CONTROL,DATA]]==[0xB7,0xB7,0xB6,8,200]
    assert bytes(m[PALETTE:PALETTE+32])==expected
    assert bytes(m[PALETTE-2:PALETTE])==bytes(m[PALETTE+32:PALETTE+34])==b'\xA5\xA5'
    assert m[FLAG+1]==0x7D and list(cpu.d)==d and list(cpu.a[:7])==a[:7]
    assert cpu.a[7]==STACK+6 and cpu.sr==0x2315 and bytes(m[STACK:STACK+6])==stack


def test_successive_supplied_interrupt_frames_use_both_phases(original_image,sparse_memory):
    m=sparse_memory;m[FLAG]=0
    m[BUFFER:BUFFER+26]=bytes(range(26));m[OTHER:OTHER+32]=bytes(range(80,112))
    for expected in[1,0,1,0]:
        cpu=enter(m);run(original_image,m,cpu,{RETURN});assert m[FLAG]==expected
        assert get(m,PALETTE+30,2)==(0x1415 if expected else 0x6E6F)


@pytest.mark.parametrize('enabled',[0,1,128,255])
def test_installer_gates_vector_store_and_resets_phase_byte_only(original_image,sparse_memory,enabled):
    m=sparse_memory
    # Existing canonical display_and_frame_service_flags BYTE at app+$20A.
    assert original_image[0][0x3A28C:0x3A290]==bytes.fromhex('4a2e020a')
    m[APP+0x20A]=enabled;put(m,0x120,0x12345678);m[FLAG]=0xAB;m[FLAG+1]=0xCD
    m[ENABLE]=0xA0;m[MASK]=0x50;m[CONTROL]=3;m[DATA]=7
    snapshots={}
    def observe(pc):
        if pc in[0x3B29A,0x3B2A0,0x3B2A6,0x3B2AC,0x3B2B2,0x3B2B8]:
            snapshots[pc]=[m[x]for x in[DATA,CONTROL,ENABLE,MASK,FLAG]]+[get(m,0x120)]
    cpu=state(m,0x3B28C);run(original_image,m,cpu,{0x3B2C2,0x3B350},observe)
    if enabled:
        assert cpu.pc==0x3B2C2 and get(m,0x120)==0x3BCD2
        assert [m[x]for x in[ENABLE,MASK,CONTROL,DATA]]==[0xA1,0x51,8,100]
        assert m[FLAG]==0
        assert list(snapshots.values())==[
            [29,3,0xA0,0x50,0xAB,0x12345678],
            [29,8,0xA0,0x50,0xAB,0x12345678],
            [29,8,0xA1,0x50,0xAB,0x12345678],
            [29,8,0xA1,0x51,0xAB,0x12345678],
            [100,8,0xA1,0x51,0xAB,0x12345678],
            [100,8,0xA1,0x51,0,0x12345678]]
    else:
        assert not snapshots
        assert cpu.pc==0x3B350 and get(m,0x120)==0x12345678
        assert [m[x]for x in[ENABLE,MASK,CONTROL,DATA]]==[0xA0,0x50,3,7]
        assert m[FLAG]==0xAB
    assert m[FLAG+1]==0xCD
