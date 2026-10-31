"""Original HUD caller and writable JMP bindings, with supplied CPU/RAM inputs.

The alternate installer blocks begin after the hardware-mode test. Mode1 stops
before its trailing external register write. These are not boot, mode-switch,
cache-lifetime or hardware scanout proofs. Fetch from RAM observes the original
CPU's operand writes; there are no host patches to the dispatch instructions.
"""
import ctypes
import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, put, get, APP, STACK, RETURN
from tests.test_starglider2_heading_strip import sample_for, expected_pixels, MODES as HEADING_MODES, BEGIN, END
from src.tests.test_m68k_simulator_abstract import _diag_has_errors, _diag_message

CACHE,LOOKUP,FONT=0x499E,0x16C60,0x16DE0
ENTRIES={'amiga':0xD6DA,'mode0':0x3CF22,'mode1':0x3D57C}
ANCHORS={'amiga':[0x7007E],'mode0':[0x68298,0x70298,0x78298],
         'mode1':[0x681EC,0x701EC,0x781EC]}
BINDINGS={
    'mode0':(0x3B4C6,RETURN,[0x3B9D2,0x3B91C,0x3D0C4,0x3B590,0x3B586,
                            0x3CAF2,0x3CF22,0x3CD46,0x3B586,0x3B586]),
    'mode1':(0x3B51E,0x3B574,[0x3B7D6,0x3B77A,0x3D5BA,0x3B590,0x3B586,
                             0x3D384,0x3D57C,0x3D410,0x3B586,0x3B586]),
}


def run_ram(image,memory,cpu,stops,observe=None,limit=5000):
    raw,_,step,_,_=image
    for _ in range(limit):
        if cpu.pc in stops:return
        if observe:observe(cpu.pc)
        assert 0x1000<=cpu.pc<0x1000+len(raw),hex(cpu.pc)
        pointer=ctypes.cast(ctypes.byref(memory,cpu.pc),ctypes.POINTER(ctypes.c_uint8))
        result=step(pointer,len(memory)-cpu.pc,0,memory,len(memory),ctypes.byref(cpu))
        assert not _diag_has_errors(result.diagnostics),(hex(cpu.pc),_diag_message(result.diagnostics))
    pytest.fail('Original HUD CPU path exceeded its bounded return/handoff')


def install(image,memory,mode):
    if mode=='amiga':return
    entry,stop,targets=BINDINGS[mode];cpu=state(memory,entry);before=bytes(memory)
    run_ram(image,memory,cpu,{stop})
    expected=bytearray(before)
    for slot,target in enumerate(targets):
        address=0xC4E4+6*slot
        assert bytes(memory[address:address+2])==b'\x4E\xF9'
        expected[address+2:address+6]=target.to_bytes(4,'big')
    assert bytes(memory)==bytes(expected)
    assert cpu.a[7]==STACK+(4 if mode=='mode0' else 0)
    for address in [0xDA00,0x3CF1E]:assert bytes(memory[address:address+4])==before[address:address+4]


def coordinate_pixels(memory,mode,word,before):
    output=bytearray(before)
    for digit,shift in enumerate([12,8,4,0]):
        glyph=bytes(memory[FONT+8*((word>>shift)&15):FONT+8*(((word>>shift)&15)+1)])
        for anchor in ANCHORS[mode]:
            for row,value in enumerate(glyph):
                if mode=='amiga':
                    planes=[2,3]if digit<2 else[3]
                    for plane in planes:output[anchor-BEGIN+0x2000*plane+40*row+digit]=value
                elif mode=='mode0':
                    column=digit if digit<2 else digit+6
                    planes=[4,6]if digit<2 else[6]
                    for plane in planes:output[anchor-BEGIN+160*row+column+plane]=value
                else:
                    doubled=sum(((value>>bit)&1)*3<<(2*bit)for bit in range(8))
                    for vertical in [0,80]:
                        start=anchor-BEGIN+160*row+vertical+2*digit
                        output[start:start+2]=doubled.to_bytes(2,'big')
    return output


@pytest.mark.parametrize('mode',ENTRIES)
@pytest.mark.parametrize('word',[0,0x1234,0x9999,0xFFFF,0xABCD])
def test_original_coordinate_encodings_and_actual_saved_frames(original_image,memory,mode,word):
    memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    cpu=state(memory,ENTRIES[mode]);cpu.d[0]=0xBEEF0000|word
    old_d,old_a=list(cpu.d),list(cpu.a);expected=coordinate_pixels(memory,mode,word,memory[BEGIN:END])
    run_ram(original_image,memory,cpu,{RETURN})
    assert bytes(memory[BEGIN:END])==expected
    assert list(cpu.d)[:3]==old_d[:3] and cpu.a[7]==STACK+4
    saved=3 if mode=='amiga'else 4 if mode=='mode0'else 5
    assert list(cpu.a)[:saved]==old_a[:saved]
    if mode=='mode0':assert cpu.a[4]==0x702A2  # A4 is used, absent from original frame.


@pytest.mark.parametrize('mode',ENTRIES)
@pytest.mark.parametrize('selector,space,x,z',[
    (0,0,0x1234ABCD,0x55EE6789),(15,0,0xFEDCBA98,0x11223344),
    (16,0,0x1234ABCD,0x98765432), # Next raw block BYTE is0; no universal table bound.
    (0xFFFF,0x80,0x12FE0000,0x34FF0000), # Space bypasses the body lookup.
])
def test_original_caller_uses_cpu_installed_wrappers_and_distinct_cache_gates(original_image,memory,mode,selector,space,x,z):
    install(original_image,memory,mode);memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    put(memory,APP+0x830,selector,2);memory[APP+0x77D]=space
    put(memory,APP+0x704,x);put(memory,APP+0x70C,z);put(memory,APP+0x746,0,2)
    shift=16 if space else(8 if selector<16 else 0)
    pair=memory[LOOKUP+((x>>shift)&255)]<<8|memory[LOOKUP+((z>>shift)&255)]
    before=None;visits=[]
    def observe(pc):
        nonlocal before
        visits.append(pc)
        if pc==0x4530:before=bytes(memory[BEGIN:END])  # After actual empty contact-panel call.
    for frame in range(2):
        cpu=state(memory,0x452C);visits.clear();run_ram(original_image,memory,cpu,{RETURN},observe)
        assert 0x4584 in visits and 0xC50E in visits and cpu.a[7]==STACK+4
        assert get(memory,CACHE,2)==pair
        assert (ENTRIES[mode]in visits)==(frame==0 and pair!=0)
        sample_read=0xD966 if mode=='amiga'else 0x3CDB4 if mode=='mode0'else 0x3D482
        assert (sample_read in visits)==(frame==0)
        expected=coordinate_pixels(memory,mode,pair,before)if frame==0 and pair else bytearray(before)
        heading=expected_pixels(memory,mode,sample_for(0))
        # Overlay explicit heading destinations, never infer writes from pixel values.
        for anchor in HEADING_MODES[mode][3]:
            for row in range(5):
                if mode=='amiga':
                    spans=[(anchor+0x2000*plane+40*row,4)for plane in [2,3]]
                elif mode=='mode0':
                    spans=[(anchor+160*row+plane+column,2)for plane in [4,6]for column in [0,8]]
                else:spans=[(anchor+160*row+vertical,8)for vertical in [0,80]]
                for address,width in spans:
                    start=address-BEGIN;expected[start:start+width]=heading[start:start+width]
        assert bytes(memory[BEGIN:END])==expected


def test_all_sixteen_stored_body_shifts_and_adjacent_byte_are_not_a_bound(original_image,memory):
    assert bytes(memory[0x48D8:0x48E8])==b'\x08'*16 and memory[0x48E8]==0
    for selector in range(17):
        put(memory,APP+0x830,selector,2);cpu=state(memory,0x453A)
        run_ram(original_image,memory,cpu,{0x4548})
        assert cpu.d[3]&255==(8 if selector<16 else 0)


def test_cockpit_clear_resets_coordinate_word_only_and_zero_is_a_cache_hit(original_image,memory):
    put(memory,CACHE,0xBEEF,2);put(memory,0xDA00,0x13572468);put(memory,0x3CF1E,0x12345678)
    cpu=state(memory,0x21B2);before=bytes(memory);run_ram(original_image,memory,cpu,{0x21B8})
    expected=bytearray(before);expected[CACHE:CACHE+2]=b'\0\0';assert bytes(memory)==expected
    put(memory,APP+0x704,0);put(memory,APP+0x70C,0);put(memory,APP+0x746,0,2)
    cpu=state(memory,0x4530);visits=[];run_ram(original_image,memory,cpu,{RETURN},visits.append)
    assert 0xD6DA not in visits and get(memory,CACHE,2)==0


@pytest.mark.parametrize('first,second',[('mode0','mode1'),('mode1','mode0')])
def test_cpu_rebinding_alone_does_not_invalidate_either_hud_cache(original_image,memory,first,second):
    memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    put(memory,APP+0x704,0x1234ABCD);put(memory,APP+0x70C,0x55EE6789)
    put(memory,APP+0x746,0,2);install(original_image,memory,first)
    cpu=state(memory,0x452C);run_ram(original_image,memory,cpu,{RETURN})
    pixels=bytes(memory[BEGIN:END]);cache=get(memory,CACHE,2)
    install(original_image,memory,second)
    cpu=state(memory,0x452C);visits=[];run_ram(original_image,memory,cpu,{RETURN},visits.append)
    assert bytes(memory[BEGIN:END])==pixels and get(memory,CACHE,2)==cache
    assert ENTRIES[second]not in visits
    assert HEADING_MODES[second][0]in visits and HEADING_MODES[second][2]not in visits
    # Selected install blocks plus CPU calls, not actual hardware mode switching.
