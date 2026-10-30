"""Original geometry, CPU register programming and polling; no DMA emulation.

Custom registers have plain byte backing. An idle/busy status is an explicit
fixture input, never an observed device completion. No blitter pixel output,
interrupt timing or normal-game caller/ownership safety is inferred.
"""
import ctypes
import itertools
import struct

import pytest

from tests.test_memory_frame_arithmetic import ConcreteState
from tests.test_starglider2_interleaved_color_kernels import kernels as original_image
from src.tests.test_m68k_simulator_abstract import _diag_has_errors, _diag_message

BASE, APP, STACK, CUSTOM, RETURN = 0x1000, 0x90000, 0xA0000, 0xDFF000, 0xFFFFFF00
RECTANGLES = [(16,303,30,128), (17,18,0,0), (15,16,199,199),
              (0,319,0,199), (319,319,1,2), (8,27,50,52)]
SIZE_WRITES = [0x2596,0x25BA,0x25DE,0x2602]


@pytest.fixture(scope='module')
def backed_memory(original_image):
    memory = (ctypes.c_uint8 * (CUSTOM+0x200))()
    raw = original_image[0]
    ctypes.memmove(ctypes.addressof(memory)+BASE, raw, len(raw))
    memory[0x68000:0x82000] = b'\xA5'*0x1A000
    return memory


def initial(memory, entry):
    memory[CUSTOM:CUSTOM+0x200] = bytes(0x200)
    memory[APP:APP+0x1000] = bytes(0x1000)
    memory[STACK-64:STACK+8] = bytes(72)
    memory[STACK:STACK+4] = struct.pack('>I', RETURN)
    state = ConcreteState()
    state.pc, state.sr, state.a[6], state.a[7] = BASE+entry, 0x2700, APP, STACK
    state.d[5], state.d[6] = 0xBEEF0000, 0xCAFE0000
    return state


def packet(memory):
    r=lambda offset: struct.unpack('>H',bytes(memory[CUSTOM+offset:CUSTOM+offset+2]))[0]
    return dict(control0=r(0x40),control1=r(0x42),first_mask=r(0x44),last_mask=r(0x46),
                destination=struct.unpack('>I',bytes(memory[CUSTOM+0x54:CUSTOM+0x58]))[0],
                size=r(0x58),modulo=r(0x66),pattern=r(0x74))


def run(image, memory, state, *, stops=(RETURN,), limit=500):
    raw, code, step, _, _ = image
    events=[]
    for _ in range(limit):
        if state.pc in stops:
            return events
        offset=state.pc-BASE
        assert 0<=offset<len(raw),hex(state.pc)
        ptr=ctypes.cast(ctypes.byref(code,offset),ctypes.POINTER(ctypes.c_uint8))
        result=step(ptr,len(raw)-offset,0,memory,len(memory),ctypes.byref(state))
        assert not _diag_has_errors(result.diagnostics),(hex(state.pc),_diag_message(result.diagnostics))
        if offset in SIZE_WRITES:
            assert raw[offset:offset+4]==bytes.fromhex('3b460058')
            events.append((offset,packet(memory)))
    return events


@pytest.mark.parametrize('rect',RECTANGLES)
def test_original_word_aligned_geometry(original_image,backed_memory,rect):
    x0,x1,y0,y1=rect
    memory=backed_memory;state=initial(memory,0x2608)
    state.a[0]=0x70000
    for i,value in enumerate([0xA5A51234,x0,x1,y0,y1]):
        state.d[i]=value if i==0 else 0x12340000|value
    saved=list(state.d[:5])
    assert not run(original_image,memory,state)
    words=x1//16-x0//16+1
    assert state.pc==RETURN and state.a[7]==STACK+4
    assert list(state.d[:5])==saved
    assert state.a[0]==0x70000+y0*40+2*(x0//16)
    assert state.d[5]==0xBEEF0000|(40-2*words)
    assert state.d[6]==0xCAFE0000|((y1-y0+1)*64+words)


@pytest.mark.parametrize('rect,expected',[
    ((65535,0,65535,0),(8150,36,130)),
    ((0,319,65535,65535),(65496,0,84)),
    ((0,65535,0,0),(0,40,64)),
    ((319,0,200,199),(8038,76,4078)),
])
def test_geometry_retains_word_wrap_without_invented_validation(original_image,backed_memory,rect,expected):
    memory=backed_memory;state=initial(memory,0x2608);state.a[0]=0x70000
    state.d[1],state.d[2],state.d[3],state.d[4]=rect
    run(original_image,memory,state)
    offset,modulo,size=expected
    assert state.pc==RETURN
    assert state.a[0]==0x70000+offset
    assert state.d[5]&0xFFFF==modulo and state.d[6]&0xFFFF==size


@pytest.mark.parametrize('colour',range(16))
def test_four_plane_register_programming(original_image,backed_memory,colour):
    memory=backed_memory
    for rect,draw in itertools.product(RECTANGLES,[0x70000,0x78B50]):
        x0,x1,y0,y1=rect
        state=initial(memory,0x253A)
        memory[APP:APP+4]=struct.pack('>I',draw)
        memory[APP+0xE4:APP+0xE8]=struct.pack('>HH',x0,x1)
        state.d[0],state.d[3],state.d[4]=0xA5A50000|colour,y0,y1
        app=bytes(memory[APP:APP+0x1000])
        events=run(original_image,memory,state)
        assert state.pc==RETURN and state.a[7]==STACK+4
        assert [offset for offset,_ in events]==SIZE_WRITES
        words=x1//16-x0//16+1
        for plane,(_,event)in enumerate(events):
            assert event==dict(control0=0x1F0,control1=0,first_mask=0xFFFF,last_mask=0xFFFF,
                destination=draw+plane*8192+y0*40+2*(x0//16),
                size=(y1-y0+1)*64+words,modulo=40-2*words,
                pattern=0xFFFF if colour&(1<<plane)else 0)
        assert bytes(memory[APP:APP+0x1000])==app
        assert bytes(memory[0x68000:0x82000])==b'\xA5'*0x1A000  # No DMA is simulated.


@pytest.mark.parametrize('entry,wait',[(0x255A,0x256A),(0x259C,0x25AA),
                                      (0x25C0,0x25CE),(0x25E4,0x25F2)])
def test_busy_status_prevents_device_programming(original_image,backed_memory,entry,wait):
    memory=backed_memory;state=initial(memory,entry)
    memory[CUSTOM+2]=0x40  # Original BTST.B #6 on the high DMACONR byte.
    before=bytes(memory[CUSTOM:CUSTOM+0x200])
    state.a[0],state.a[5],state.d[0]=0x70000,CUSTOM,15
    assert not run(original_image,memory,state,limit=100)
    assert state.pc in [BASE+wait,BASE+wait+6]
    assert bytes(memory[CUSTOM:CUSTOM+0x200])==before


def test_horizon_row_selection_keeps_original_guards(original_image,backed_memory):
    memory=backed_memory
    for lower,space,split in itertools.product([False,True],[False,True],[-1,0,30,31,128,129,150]):
        state=initial(memory,0x24F8)
        state.d[0]=0xAABB0000|int(lower)
        memory[APP+0xE8:APP+0xEC]=struct.pack('>HH',30,128)
        memory[APP+0x77D]=0xFF if space else 0
        memory[0x2F010:0x2F012]=struct.pack('>h',split)
        memory[0x2F014:0x2F018]=struct.pack('>HH',5,10)
        events=run(original_image,memory,state,stops=(RETURN,BASE+0x253A))
        assert not events  # Stop before any programming when a band is selected.
        if space and lower or not space and (lower and split<0 or not lower and 0<=split<=30):
            assert state.pc==RETURN
        else:
            assert state.pc==BASE+0x253A
            expected=(30,128)if space or split<0 else (split,128)if lower else (30,split-1)
            assert (state.d[3]&0xFFFF,state.d[4]&0xFFFF)==expected
            assert state.d[0]&0xFFFF==(0xFFFF if space else 10 if lower else 5)
