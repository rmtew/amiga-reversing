"""Original rating arithmetic with explicit local caller/register inputs.

The rank kernel starts with a zero high WORD in D0, as in the normalized
accuracy path. It does not establish arbitrary entry safety or final-screen
hardware delivery. Physical pointer-table extent remains sixteen entries.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP

TABLE=0xB3CC


@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names=['pilot_hit_accuracy_word','weapon_energy_overflow_bonus_count','icarus_hits_received']
    folder=tmp_path_factory.mktemp('rating');asm,out=folder/'fields.s',folder/'fields.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result=subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    raw=out.read_bytes();assert raw[:-12]==original_image[0]
    return {n:APP+v for n,v in zip(names,struct.unpack('>III',raw[-12:]))}


def signed_word(value):
    value&=65535
    return value-65536 if value&32768 else value


@pytest.mark.parametrize('hits',[0,1,10,100,32767,32768,65535,0x12340009])
@pytest.mark.parametrize('shots',[0,1,65535,100,32767,32768,65536,65537,0xffff0000])
def test_accuracy_uses_signed_low_words_and_masks_division_result(original_image,memory,fields,hits,shots):
    put(memory,fields['pilot_hit_accuracy_word'],0xbeef,2)
    cpu=state(memory,0xB10A);cpu.d[0],cpu.d[1]=hits,shots
    run(original_image,memory,cpu,{0xB112,0xB12A})
    divisor=signed_word(shots)
    if divisor==0:
        assert cpu.pc==0xB112 and get(memory,fields['pilot_hit_accuracy_word'],2)==0xbeef
    else:
        dividend=signed_word(hits)*100
        quotient=abs(dividend)//abs(divisor)
        if (dividend<0)!=(divisor<0):quotient=-quotient
        # DIVS overflow leaves D0 unchanged; the following ANDI still masks it.
        expected=(quotient if -32768<=quotient<=32767 else dividend)&255
        assert cpu.pc==0xB12A and cpu.d[0]==expected
        assert get(memory,fields['pilot_hit_accuracy_word'],2)==expected


def check_rank(image,memory,fields,accuracy,bonus,damage):
    put(memory,fields['pilot_hit_accuracy_word'],accuracy,2)
    put(memory,fields['weapon_energy_overflow_bonus_count'],bonus)
    put(memory,fields['icarus_hits_received'],damage)
    cpu=state(memory,0xB13A);cpu.d[0]=0
    run(image,memory,cpu,{0xB1CA})
    base=accuracy//10 if accuracy<70 else 8
    bonus_steps=4 if bonus==0x80000000 else 0 if bonus==0xffffffff else sum(bonus>=t for t in (1,2,7,17))
    penalties=3 if damage==0x80000000 else 0 if damage==0xffffffff else sum(damage>=t for t in (600,1400,2400))
    expected=max(0,min(10,base+bonus_steps-penalties))
    assert cpu.d[0]&65535==expected*4
    assert cpu.a[0]==TABLE and cpu.a[1]==get(memory,TABLE+expected*4)
    assert 0<=expected<=10


@pytest.mark.parametrize('accuracy',range(256))
def test_every_normalized_accuracy_has_the_original_base_bucket(original_image,memory,fields,accuracy):
    check_rank(original_image,memory,fields,accuracy,0,0)


@pytest.mark.parametrize('accuracy',[0,1,9,10,59,60,69,70,79,99,100,255])
@pytest.mark.parametrize('bonus',[0,1,2,6,7,16,17,0x80000000,0xffffffff])
@pytest.mark.parametrize('damage',[0,599,600,1399,1400,2399,2400,0x80000000,0xffffffff])
def test_rank_tiers_and_n_only_overflow_cases_preserve_final_clamp(original_image,memory,fields,accuracy,bonus,damage):
    check_rank(original_image,memory,fields,accuracy,bonus,damage)


def test_sixteen_pointer_slots_retain_eleven_distinct_verdicts(original_image,memory):
    pointers=[get(memory,TABLE+4*i)for i in range(16)]
    assert len(set(pointers))==11 and len(set(pointers[10:]))==1


@pytest.mark.parametrize('rank',[0,1,10,11,32767,32768,32778,32779,65535])
def test_final_clamp_bounds_even_subtraction_overflow_aliases(original_image,memory,rank):
    cpu=state(memory,0xB1AC);cpu.d[0]=0x12340000|rank
    run(original_image,memory,cpu,{0xB1CA})
    expected=rank if rank<=10 else 10 if rank<=32778 else 0
    assert cpu.d[0]&65535==expected*4
    assert cpu.a[1]==get(memory,TABLE+expected*4)
