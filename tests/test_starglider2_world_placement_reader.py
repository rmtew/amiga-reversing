"""Original placement stream reader; stop before type-specific initializer calls.

Supplied records establish packing/copy/dispatch behavior, not world capacity,
selector validity, subtype initialization or lifetime for arbitrary saved state.
High stored tags retain the original default/initializer-table alias arithmetic;
stopping before the call does not certify the aliased initializer target.
"""
import struct
import subprocess
from pathlib import Path

import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, INPUT

OBJECT=INPUT+0x400
LABELS=['read_next_world_object_placement','invoke_world_placement_initializer',
        'initialize_free_stack_from_one_based_slot_index','world_object_type_initializer_pointers',
        'model_default_durability_bytes','model_default_scale_shifts']


@pytest.fixture(scope='module')
def placement_addresses(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder=tmp_path_factory.mktemp('placement-reader');source=folder/'symbols.s';output=folder/'symbols.raw'
    source.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(LABELS)+'\n')
    result=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000',
        '-no-opt','-I'+str(target/'includes'),'-o',str(output),str(source)],cwd=target,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    raw=output.read_bytes();tail=4*len(LABELS);assert raw[:-tail]==original_image[0]
    return dict(zip(LABELS,struct.unpack('>'+'I'*len(LABELS),raw[-tail:])))


@pytest.mark.parametrize('kind',[1,10,30,48,65,85,94,103,128,145])
@pytest.mark.parametrize('header',[0,1,2,128,255])
@pytest.mark.parametrize('interior',[False,True])
@pytest.mark.parametrize('dirty',[0,0xA5])
def test_original_reader_preserves_packed_header_and_phase_specific_destination_bytes(
        original_image,memory,placement_addresses,kind,header,interior,dirty):
    m,f=memory,placement_addresses
    m[OBJECT-4:OBJECT+72]=bytes([dirty])*76
    tag=kind|(header<<8);x,z=0xFEDCBA98,0x7FFFFFFF;parameters=[0x1234,0xFEDC,0x8001]
    stream=struct.pack('>HIIHHH',tag,x,z,*parameters);m[INPUT:INPUT+len(stream)]=stream
    cpu=state(m,f['read_next_world_object_placement']);cpu.a[0]=OBJECT;cpu.a[1]=INPUT
    cpu.a[3]=f['model_default_durability_bytes'];cpu.a[4]=f['model_default_scale_shifts']
    cpu.d[4]=0 if interior else 0xFFFFFFFF
    expected=bytearray(m[OBJECT:OBJECT+68]);expected[:2]=tag.to_bytes(2,'big')
    expected[4:8]=x.to_bytes(4,'big');expected[12:16]=z.to_bytes(4,'big')
    if interior:
        expected[8:12]=(0xFFFFFC18).to_bytes(4,'big')
        for offset,value in zip([36,40,18],parameters):expected[offset:offset+2]=value.to_bytes(2,'big')
        expected[2]|=128
        if header:
            expected[2]&=127;expected[38]=header;expected[0]=0
    expected[28]=m[f['model_default_durability_bytes']+kind]
    expected[29]=m[f['model_default_scale_shifts']+kind]
    expected[30]=255;expected[3]=0
    run(original_image,m,cpu,{f['invoke_world_placement_initializer']})
    assert bytes(m[OBJECT:OBJECT+68])==expected
    assert bytes(m[OBJECT-4:OBJECT])==bytes([dirty])*4
    assert bytes(m[OBJECT+68:OBJECT+72])==bytes([dirty])*4
    assert bytes(m[INPUT:INPUT+len(stream)])==stream
    assert cpu.a[0]==OBJECT and cpu.a[1]==INPUT+(16 if interior else 10)
    assert cpu.a[5]==get(m,f['world_object_type_initializer_pointers']+4*kind)
    assert cpu.d[0]&65535==4*kind


@pytest.mark.parametrize('interior',[False,True])
def test_zero_full_word_is_the_terminator_before_record_copy(original_image,memory,placement_addresses,interior):
    m,f=memory,placement_addresses;m[OBJECT:OBJECT+68]=b'\xA5'*68;put(m,INPUT,0,2)
    cpu=state(m,f['read_next_world_object_placement']);cpu.a[0]=OBJECT;cpu.a[1]=INPUT
    cpu.d[4]=0 if interior else 0xFFFFFFFF
    run(original_image,m,cpu,{f['initialize_free_stack_from_one_based_slot_index']})
    assert bytes(m[OBJECT:OBJECT+68])==b'\xA5'*68 and cpu.a[1]==INPUT+2
