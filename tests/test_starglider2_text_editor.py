"""Original editor/planar text CPU paths with explicit RAM and key stimuli.

These fixtures execute original instructions, including key translation and
font/plane writes. They do not boot the game or certify hardware scanout,
interrupt-time font sharing, arbitrary caller buffers or platform replacement.
"""
import ctypes

import pytest

from tests.test_memory_frame_arithmetic import ConcreteState
from tests.test_starglider2_interleaved_color_kernels import kernels as original_image
from src.tests.test_m68k_simulator_abstract import _diag_has_errors, _diag_message

BASE, APP, FB, INPUT, STACK, RETURN = 0x1000,0x90000,0x70000,0x88000,0xA0000,0xFFFFFF00
DEST,COL,ROW,INVERSE,LIMIT = 0xDE88,0xDE81,0xDE82,0xDE78,0xD904
FONT,COLOUR,STEP,BACKSTEP = 0x16D60,0xDF8A,0xDFB2,0xDFB6


def put(memory,address,value,width=4):
    memory[address:address+width]=value.to_bytes(width,'big')


def get(memory,address,width=4):
    return int.from_bytes(bytes(memory[address:address+width]),'big')


@pytest.fixture
def memory(original_image):
    raw=original_image[0];result=(ctypes.c_uint8*0xA1000)()
    ctypes.memmove(ctypes.addressof(result)+BASE,raw,len(raw))
    put(result,APP+4,FB)
    put(result,DEST,FB)
    put(result,0x1002,0x8000,2)  # supplied negative platform flag, not a boot-path assertion
    result[FB:FB+0x8000]=b'\xA5'*0x8000
    result[COLOUR]=6
    return result


def state(memory,entry):
    cpu=ConcreteState();cpu.pc=entry;cpu.sr=0x2700
    cpu.d[:]=[0x12340000+i for i in range(8)]
    cpu.a[:]=[INPUT,INPUT+0x80,INPUT+0x100,INPUT+0x180,INPUT+0x200,INPUT+0x280,APP,STACK]
    put(memory,STACK,RETURN)
    return cpu


def run(image,memory,cpu,stops,stimulus=None,limit=30000):
    raw,code,step,_,_=image
    for _ in range(limit):
        if cpu.pc in stops:return
        if stimulus:stimulus(cpu.pc)
        offset=cpu.pc-BASE
        assert 0<=offset<len(raw),hex(cpu.pc)
        pointer=ctypes.cast(ctypes.byref(code,offset),ctypes.POINTER(ctypes.c_uint8))
        result=step(pointer,len(raw)-offset,0,memory,len(memory),ctypes.byref(cpu))
        assert not _diag_has_errors(result.diagnostics),(hex(cpu.pc),_diag_message(result.diagnostics))
    pytest.fail('Original text phase did not reach its bounded return/handoff')


@pytest.mark.parametrize('scancodes,capacity,expected',[
    ([0x1C],8,b''), ([0x20,0x35,0x1C],8,b'AB'),
    ([0x20,0x35,0x41,0x21,0x1C],8,b'AS'),
    ([0x41,0x20,0x1C],8,b'A'),
    ([0x20,0x35,0x45],8,b''),
    ([0x20,0x35,0x21,0x1C],2,b'AB'),
    ([0x20,0x1C],0,b''),
    ([0x0E,0x42,0x20,0x1C],8,b'A'),  # translated NUL/TAB are ignored
])
def test_original_editor_uses_real_translation_and_restores_saved_registers(original_image,memory,scancodes,capacity,expected):
    memory[INPUT-4:INPUT+40]=b'\xCC'*44
    put(memory,LIMIT,capacity,2);cpu=state(memory,0xD7D8)
    before_d=list(cpu.d);before_a=list(cpu.a);font=bytes(memory[FONT:FONT+760])
    keys=iter(scancodes);events=[]
    def key(pc):
        if pc==0xD7AA:
            value=next(keys,None);assert value is not None,'unexpected additional key request'
            memory[APP+0x203]=value;events.append(value)
    run(original_image,memory,cpu,{RETURN},key)
    assert events==scancodes and list(keys)==[]
    assert bytes(memory[INPUT:INPUT+len(expected)+1])==expected+b'\0'
    assert bytes(memory[INPUT-4:INPUT])==b'\xCC'*4
    assert bytes(memory[INPUT+capacity+1:INPUT+40])==b'\xCC'*(39-capacity)
    assert list(cpu.d)==before_d and list(cpu.a)[:7]==before_a[:7] and cpu.a[7]==STACK+4
    assert bytes(memory[FONT:FONT+760])==font and memory[INVERSE]==0
    assert memory[APP+0x203]==0


@pytest.mark.parametrize('mask',range(16))
@pytest.mark.parametrize('inverse',[False,True])
def test_original_cursor_glyph_selects_four_planes_and_restores_font(original_image,memory,mask,inverse):
    text=(b'\x01' if inverse else b'\x02')+bytes([0x80|mask])+b'A\0'
    memory[INPUT:INPUT+len(text)]=text;cpu=state(memory,0xDC68);cpu.a[1]=INPUT
    font=bytes(memory[FONT:FONT+760]);before=bytes(memory[FB:FB+0x8000])
    run(original_image,memory,cpu,{RETURN})
    glyph=font[8*(ord('A')-32):8*(ord('A')-31)]
    expected=bytearray(before)
    for plane in range(4):
        for row,value in enumerate(glyph):
            expected[0x2000*plane+40*row]=(value^(255 if inverse else 0))if(mask>>plane)&1 else 0
    assert bytes(memory[FB:FB+0x8000])==expected
    assert bytes(memory[FONT:FONT+760])==font
    assert get(memory,DEST)==FB+1 and memory[COL]==1 and memory[ROW]==0
    assert get(memory,STEP)==1 and memory[INVERSE]==(255 if inverse else 0)


@pytest.mark.parametrize('column,row,text,offset,out_column,out_row',[
    (5,2,b'\r\0',640,0,2), (5,2,b'\n\0',965,5,3),
    (5,24,b'\n\0',0,0,0), (39,2,b'A\0',960,0,3),
    (39,24,b'A\0',0,0,0), (38,2,b'\t\0',684,44,2),
])
def test_original_cursor_controls_preserve_distinct_wrap_rules(original_image,memory,column,row,text,offset,out_column,out_row):
    memory[COL],memory[ROW]=column,row;put(memory,DEST,FB+row*320+column)
    memory[INPUT:INPUT+len(text)]=text;cpu=state(memory,0xDC68);cpu.a[1]=INPUT
    run(original_image,memory,cpu,{RETURN})
    assert (get(memory,DEST),memory[COL],memory[ROW])==(FB+offset,out_column,out_row)


@pytest.mark.parametrize('step,flags,next_step',[(1,0x8000,1),(1,0,7),(7,0,1),(7,0x8000,1),(2,0,2)])
def test_delete_continuation_keeps_original_platform_step_rule(original_image,memory,step,flags,next_step):
    put(memory,0xDE74,INPUT);put(memory,BACKSTEP,step);put(memory,0x1002,flags,2)
    put(memory,DEST,FB+100);memory[COL]=5
    cpu=state(memory,0xD870);cpu.a[0]=INPUT+2;cpu.d[1]=6
    run(original_image,memory,cpu,{0xD7E8})
    assert cpu.a[0]==INPUT+1 and cpu.d[1]==7
    assert get(memory,DEST)==FB+101-2*step and memory[COL]==4
    assert get(memory,BACKSTEP)==next_step


def test_delete_previous_row_retains_unusual_original_subtraction(original_image,memory):
    put(memory,0xDE74,INPUT);put(memory,BACKSTEP,1);put(memory,DEST,FB+320)
    memory[COL],memory[ROW]=0,1
    cpu=state(memory,0xD870);cpu.a[0]=INPUT+1;cpu.d[0]=8;cpu.d[1]=7
    run(original_image,memory,cpu,{0xD7E8})
    assert cpu.a[0]==INPUT and cpu.d[1]==8
    assert (memory[COL],memory[ROW],get(memory,DEST))==(39,0,FB-1)
    # This supplied boundary state is not a normal-input reachability proof.


@pytest.mark.parametrize('text,positions,shared_cursor',[
    (b'A\rB\0',[0,1],False), (b'A\nB\0',[0,321],False),
    (b'\x01A\0',[0],True),
])
def test_positioned_text_cr_lf_and_shared_inverse_continuation(original_image,memory,text,positions,shared_cursor):
    put(memory,0x27A8,APP);memory[COL],memory[ROW]=11,7
    memory[INPUT:INPUT+len(text)]=text;cpu=state(memory,0xDBB8)
    cpu.a[1]=INPUT;cpu.d[0],cpu.d[1]=5,8
    font=bytes(memory[FONT:FONT+760]);before=bytes(memory[FB:FB+0x8000]);expected=bytearray(before)
    run(original_image,memory,cpu,{RETURN})
    for character,position in zip(b'AB',positions):
        glyph=font[8*(character-32):8*(character-31)]
        for plane in range(4):
            for row,value in enumerate(glyph):
                expected[325+position+0x2000*plane+40*row]=(value^(255 if shared_cursor else 0))if(6>>plane)&1 else 0
    assert bytes(memory[FB:FB+0x8000])==expected
    assert bytes(memory[FONT:FONT+760])==font
    assert (memory[COL],memory[ROW])==((12,7)if shared_cursor else(11,7))
    assert get(memory,DEST)==(FB+326 if shared_cursor else FB)


@pytest.mark.parametrize('mouse,fire',[(1,0),(0,1),(1,1)])
def test_key_wait_mouse_or_fire_returns_zero_without_consuming_pending_key(original_image,memory,mouse,fire):
    memory[APP+0x201],memory[APP+0x1FD],memory[APP+0x203]=mouse,fire,0x20
    cpu=state(memory,0xD7AA);old_a0=cpu.a[0]
    run(original_image,memory,cpu,{RETURN})
    assert cpu.d[0]==0 and cpu.a[0]==old_a0 and cpu.a[7]==STACK+4
    assert memory[APP+0x203]==0x20


def test_editor_marker_at_last_column_preserves_original_row_and_column_drift(original_image,memory):
    memory[COL]=39;put(memory,DEST,FB+39);put(memory,LIMIT,8,2)
    cpu=state(memory,0xD7D8);events=[]
    def key(pc):
        if pc==0xD7AA:
            assert not events
            memory[APP+0x203]=0x1C;events.append(0x1C)
    run(original_image,memory,cpu,{RETURN},key)
    assert events==[0x1C] and memory[INPUT]==0
    assert (get(memory,DEST),memory[COL],memory[ROW])==(FB+39,255,1)
    # Explicit caller cursor state, not evidence that a real game prompt reaches it.
