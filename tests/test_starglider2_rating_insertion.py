"""Original ranking/copy/formatter CPU windows with explicit table inputs.

No palette, editor, disk, full-menu or normal-game execution is asserted.
Malformed supplied scores retain signed LONG comparison and nibble conversion.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,RETURN


@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names=['pilot_rating_score_slots','pilot_rating_name_slots','player_score_bcd',
        'pilot_rating_six_digit_text','pilot_rating_saved_control_settings','format_six_score_nibbles']
    folder=tmp_path_factory.mktemp('ranking');asm,out=folder/'fields.s',folder/'fields.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    r=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
    raw=out.read_bytes();assert raw[:-4*len(names)]==original_image[0]
    return dict(zip(names,struct.unpack('>'+str(len(names))+'I',raw[-4*len(names):])))


def signed(value):return value-(1<<32)if value&(1<<31)else value
SCORES=[(16-i)*0x1000 for i in range(15)]+[0xffffffff]
CANDIDATES=sorted({0,0x7fffffff,0x80000000,0x80000001,0xffff0000,0xffffffff}|
    {v+d for v in SCORES[:15]for d in [-1,0,1]})


@pytest.mark.parametrize('candidate',CANDIDATES)
@pytest.mark.parametrize('malformed',[False,True])
def test_first_strictly_greater_signed_long_wins_and_sixteenth_slot_is_not_compared(original_image,memory,fields,candidate,malformed):
    scores=SCORES if not malformed else[0,0xffffffff,0x80000000,0x7fffffff]+SCORES[4:]
    p=fields['pilot_rating_score_slots']
    for i,v in enumerate(scores):put(memory,p+4*i,v)
    before=bytes(memory[p:p+64]);cpu=state(memory,0xFDE4)
    cpu.a[3]=p;cpu.d[0]=14;cpu.d[1]=candidate
    run(original_image,memory,cpu,{0xFDEE,RETURN})
    index=next((i for i,v in enumerate(scores[:15])if signed(candidate)>signed(v)),None)
    assert cpu.pc==(0xFDEE if index is not None else RETURN)
    assert cpu.a[3]==p+4*((index+1)if index is not None else 15)
    assert cpu.d[0]==(14-index if index is not None else 65535)
    assert cpu.d[1]==candidate and bytes(memory[p:p+64])==before


@pytest.mark.parametrize('index',range(15))
@pytest.mark.parametrize('counter_high',[0,0x12340000,0xffff0000])
def test_backward_score_shift_uses_word_counter_and_reloads_live_score(original_image,memory,fields,index,counter_high):
    p=fields['pilot_rating_score_slots'];scores=[0x11220000+i for i in range(16)]
    for i,v in enumerate(scores):put(memory,p+4*i,v)
    guard=bytes(memory[p+64:p+72]);new=0x89abcdef;put(memory,APP+fields['player_score_bcd'],new)
    cpu=state(memory,0xFE08);cpu.a[1]=p+56;cpu.a[3]=p+4*(index+1)
    cpu.d[0]=counter_high|(14-index);cpu.d[2]=cpu.d[0];cpu.d[1]=0x76543210
    run(original_image,memory,cpu,{0xFE1C})
    assert [get(memory,p+4*i)for i in range(16)]==scores[:index]+[new]+scores[index:15]
    assert bytes(memory[p+64:p+72])==guard
    assert cpu.a[3]==p+4*index and cpu.a[1]==fields['pilot_rating_name_slots']+14*16
    assert cpu.d[2]==counter_high|(14-index)  # reset for the following name shift


@pytest.mark.parametrize('index',range(15))
@pytest.mark.parametrize('counter_high',[0,0x43210000])
def test_name_shift_leaves_selected_input_slot_and_controls_tail_intact(original_image,memory,fields,index,counter_high):
    p=fields['pilot_rating_name_slots'];rows=[bytes([65+i])*15+b'\0'for i in range(16)]
    memory[p:p+256]=b''.join(rows);tail=fields['pilot_rating_saved_control_settings']
    memory[tail:tail+184]=b'\xa7'*184
    cpu=state(memory,0xFE1C);cpu.a[1]=p+14*16;cpu.d[2]=counter_high|(14-index)
    run(original_image,memory,cpu,{0xFE42})
    expected=rows[:index+1]+rows[index:15]
    assert bytes(memory[p:p+256])==b''.join(expected)
    assert cpu.a[1]==p+16*index and cpu.d[2]==counter_high|65535
    assert bytes(memory[tail:tail+184])==b'\xa7'*184


FORMAT_VALUES=sorted({0,1,0x00999999,0x12345678,0x89abcdef,0xffffffff}|
    {n<<(4*position)for position in range(6)for n in range(16)}|
    {(high<<24)|0x123456 for high in range(256)})


@pytest.mark.parametrize('value',FORMAT_VALUES)
def test_formatter_skips_high_byte_converts_six_nibbles_and_retains_terminator(original_image,memory,fields,value):
    source=0x88000;p=fields['pilot_rating_six_digit_text'];put(memory,source,value)
    memory[p:p+8]=b'\xa7'*8;cpu=state(memory,fields['format_six_score_nibbles']);cpu.a[0]=source
    # The renderer is a distinct consumer; stop on entry before reading output.
    run(original_image,memory,cpu,{0xDC68})
    expected=bytes(48+((value>>shift)&15)for shift in range(20,-1,-4))
    assert bytes(memory[p:p+8])==expected+b'\xa7\xa7'
    assert cpu.a[0]==source+4 and cpu.a[1]==p
