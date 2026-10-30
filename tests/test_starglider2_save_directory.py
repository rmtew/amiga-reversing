"""Original directory header/search/staging instructions, not UI or disk I/O.

Runtime buffer addresses are explicit fixture inputs. No disk format validity,
closed reader count, allocation ownership or non-local save return is inferred.
"""
import ctypes
import struct

import pytest

from tests.test_memory_frame_arithmetic import ConcreteState
from tests.test_starglider2_interleaved_color_kernels import kernels as original_image
from src.tests.test_m68k_simulator_abstract import _diag_has_errors, _diag_message

BASE, DIRECTORY, INPUT, STAGE, STACK, RETURN = 0x1000,0x7E400,0x1265A,0x41848,0xA0000,0xFFFFFF00
MAGIC = 0x47414D45


@pytest.fixture(scope='module')
def memory(original_image):
    raw=original_image[0]
    result=(ctypes.c_uint8*0xA1000)()
    ctypes.memmove(ctypes.addressof(result)+BASE,raw,len(raw))
    return result


def state(memory,entry):
    result=ConcreteState();result.pc,result.sr,result.a[7]=BASE+entry,0x2700,STACK
    memory[STACK:STACK+4]=struct.pack('>I',RETURN)
    return result


def run(image,memory,cpu,stops,limit=10000):
    raw,code,step,_,_=image
    for _ in range(limit):
        if cpu.pc in stops:return
        offset=cpu.pc-BASE
        assert 0<=offset<len(raw),hex(cpu.pc)
        pointer=ctypes.cast(ctypes.byref(code,offset),ctypes.POINTER(ctypes.c_uint8))
        result=step(pointer,len(raw)-offset,0,memory,len(memory),ctypes.byref(cpu))
        assert not _diag_has_errors(result.diagnostics),(hex(cpu.pc),_diag_message(result.diagnostics))
    pytest.fail('Provided directory phase failed to reach its bounded handoff')


@pytest.mark.parametrize('magic,count',[(0,1),(MAGIC,0),(MAGIC,1),(MAGIC,15),
                                       (MAGIC,65536),(MAGIC,65537)])
def test_original_header_checks_do_not_invent_a_fifteen_entry_reader_bound(original_image,memory,magic,count):
    memory[DIRECTORY:DIRECTORY+8]=struct.pack('>II',magic,count)
    cpu=state(memory,0xFF02)
    run(original_image,memory,cpu,{RETURN,BASE+0xFF1C})
    assert cpu.d[2]==0
    if magic!=MAGIC or not count:
        assert cpu.pc==RETURN and cpu.d[0]==0xFFFFFFFF
    else:
        # Stop before listing/UI. The LONG nonzero check precedes a WORD decrement.
        assert cpu.pc==BASE+0xFF1C and cpu.a[0]==DIRECTORY+8
        assert cpu.d[1]==(count&0xFFFF0000)|((count-1)&0xFFFF)
    assert bytes(memory[DIRECTORY:DIRECTORY+8])==struct.pack('>II',magic,count)


@pytest.mark.parametrize('names,count,entered,result,index',[
    (['ALPHA','ALPINE','BETA'],3,'',-2,None),
    (['ALPHA','ALPINE','BETA'],3,'AL',0,0),
    (['ALPHA','ALPINE','BETA'],3,'ALPHA',0,0),
    (['ALPHA','ALPINE','BETA'],3,'ALPINE',0,1),
    (['ALPHA','ALPINE','BETA'],3,'BET',0,2),
    (['ALPHA','ALPINE','BETA'],3,'ALPHAX',-1,3),
    (['ALPHA','ALPINE','BETA'],3,'beta',-1,3),
    (['A','AB'],2,'A',0,0),
    (['A','AB'],2,'AB',0,1),
    (['A','B','C'],2,'C',-1,2),
    (['A','','C','D'],4,'C',-1,1),
    (['','C'],2,'C',0,1),
    (['X'*30],1,'X'*30,0,0),
])
def test_original_name_lookup_is_first_bytewise_input_prefix(original_image,memory,names,count,entered,result,index):
    memory[DIRECTORY:DIRECTORY+1024]=bytes(1024)
    memory[DIRECTORY:DIRECTORY+8]=struct.pack('>II',MAGIC,count)
    for n,name in enumerate(names):
        data=name.encode('ascii')+b'\0'
        memory[DIRECTORY+8+32*n:DIRECTORY+8+32*(n+1)]=data+b'\xCC'*(32-len(data))
    text=entered.encode('ascii')+b'\0'
    memory[INPUT:INPUT+36]=text+b'\xA5'*(36-len(text))
    before_directory=bytes(memory[DIRECTORY:DIRECTORY+1024]);before_input=bytes(memory[INPUT:INPUT+36])
    cpu=state(memory,0xFF5A)
    run(original_image,memory,cpu,{RETURN})
    assert cpu.pc==RETURN and cpu.a[7]==STACK+4
    assert cpu.d[0]==result&0xFFFFFFFF
    if index is not None:
        assert cpu.d[2]==index and cpu.a[2]==DIRECTORY+8+32*index
    assert bytes(memory[DIRECTORY:DIRECTORY+1024])==before_directory
    assert bytes(memory[INPUT:INPUT+36])==before_input


@pytest.mark.parametrize('index',[0,1,14,15])
def test_name_copy_precedes_capacity_guard_and_only_valid_indices_stage(original_image,memory,index):
    directory=bytearray(b'\xA5'*520)
    struct.pack_into('>II',directory,0,MAGIC,15)
    incoming=b'NEW\0'+bytes(range(32))  # 36 backing bytes; only the first 32 are copied.
    memory[DIRECTORY:DIRECTORY+520]=directory
    memory[INPUT:INPUT+36]=incoming
    memory[STAGE:STAGE+512]=b'\xEE'*512
    cpu=state(memory,0xF054);cpu.d[2]=index;cpu.a[2]=DIRECTORY+8+32*index
    run(original_image,memory,cpu,{BASE+0xF08E,BASE+0xF156})
    expected=bytearray(directory);begin=8+32*index;expected[begin:begin+32]=incoming[:32]
    if index<15:
        struct.pack_into('>II',expected,0,MAGIC,index+1)
        assert cpu.pc==BASE+0xF08E and cpu.d[2]==index
        assert bytes(memory[STAGE:STAGE+512])==bytes(expected[:512])
    else:
        assert cpu.pc==BASE+0xF156 and cpu.d[2]==15
        assert bytes(memory[STAGE:STAGE+512])==b'\xEE'*512
        # Eight copied bytes lie beyond the 512-byte directory image, still in
        # the supplied track backing. This is not a disk-write or allocator proof.
        assert bytes(memory[DIRECTORY+512:DIRECTORY+520])==incoming[24:32]
    assert cpu.a[7]==STACK
    assert bytes(memory[DIRECTORY:DIRECTORY+520])==bytes(expected)
    assert bytes(memory[INPUT:INPUT+36])==incoming


def test_staged_directory_restore_copies_only_512_bytes(original_image,memory):
    incoming=bytes((i*37+11)&255 for i in range(512))
    memory[STAGE:STAGE+512]=incoming
    memory[DIRECTORY:DIRECTORY+520]=b'\xCC'*520
    cpu=state(memory,0xF0F6)
    run(original_image,memory,cpu,{BASE+0xF10A})
    assert cpu.pc==BASE+0xF10A and cpu.a[7]==STACK
    assert bytes(memory[DIRECTORY:DIRECTORY+512])==incoming
    assert bytes(memory[DIRECTORY+512:DIRECTORY+520])==b'\xCC'*8
    assert bytes(memory[STAGE:STAGE+512])==incoming
