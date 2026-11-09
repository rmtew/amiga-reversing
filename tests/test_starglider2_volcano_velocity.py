"""Original eruption velocity reads and vertical PRNG path with supplied RAM.

Stop before proximity/charging continuations. No spawn eligibility, allocation
capacity, statistical independence, lifetime or normal-game reachability proof.
"""
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,STACK
from tests.test_starglider2_palette_priority import rng

CHOICES={0x3992E:[32,-25,15,-17,15,-30,30,-25],0x3993E:[-25,-35,15,12,-15,-26,18,31]}


@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder=tmp_path_factory.mktemp('volcano-fields');asm,out=folder/'symbols.s',folder/'symbols.raw'
    names=['SG2WorldObject_velocity_'+axis for axis in 'xyz']
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result=subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,text=True,capture_output=True)
    assert result.returncode==0,result.stdout+result.stderr
    data=out.read_bytes();assert data[:-12]==original_image[0]
    return dict(zip('xyz',struct.unpack('>III',data[-12:])))


@pytest.mark.parametrize('entry,table,axis',[(0x36CE8,0x3992E,'x'),(0x36CFC,0x3993E,'z')])
@pytest.mark.parametrize('index',range(8))
@pytest.mark.parametrize('upper',[0,0xFFFF0000])
def test_horizontal_choice_reads_even_word_byte_offsets_only(original_image,memory,fields,entry,table,axis,index,upper):
    field=fields[axis]
    assert int.from_bytes(original_image[0][entry-4096+4:entry-4096+6],'big')==field
    m=memory;m[INPUT:INPUT+68]=b'\xA5'*68;expected=bytearray(m[INPUT:INPUT+68])
    values=CHOICES[table];value=values[index]&65535
    assert get(m,table+2*index,2)==value
    expected[field:field+2]=value.to_bytes(2,'big')
    cpu=state(m,entry);cpu.a[1]=table;cpu.a[4]=INPUT;cpu.d[0]=upper|2*index;saved_d=list(cpu.d)
    run(original_image,m,cpu,{entry+6})
    assert bytes(m[INPUT:INPUT+68])==expected and list(cpu.d)==saved_d
    assert cpu.a[1]==table and cpu.a[4]==INPUT and cpu.a[7]==STACK


@pytest.mark.parametrize('sample',range(32))
@pytest.mark.parametrize('seed_high',[0,0xABCD0000])
def test_vertical_velocity_uses_one_additional_prng_advance(original_image,memory,fields,sample,seed_high):
    m=memory;m[INPUT:INPUT+68]=b'\xA5'*68;expected=bytearray(m[INPUT:INPUT+68])
    seed=(0,seed_high|(((-7)&65535)^sample));a,b=rng(*seed)
    assert b&31==sample
    put(m,APP+0x60,seed[0]);put(m,APP+0x64,seed[1]);expected[fields['y']:fields['y']+2]=((-100-sample)&65535).to_bytes(2,'big')
    cpu=state(m,0x36D02);cpu.a[4]=INPUT;d1=cpu.d[1]
    run(original_image,m,cpu,{0x36D14})
    assert bytes(m[INPUT:INPUT+68])==expected
    assert (get(m,APP+0x60),get(m,APP+0x64))==(a,b)
    assert cpu.d[1]==d1 and cpu.a[4]==INPUT and cpu.a[7]==STACK
