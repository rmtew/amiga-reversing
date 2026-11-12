"""Original column mapping; supplied CPU inputs are not a gameplay bound.

The 40 stored entries end immediately before the accepted palette interrupt.
Out-of-prefix inputs deliberately retain the original unchecked lookup.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,APP,FB

TABLE,ENTRY,AFTER=0x3BCAA,0x3B91C,0x3B94A


@pytest.mark.parametrize('column',range(40))
@pytest.mark.parametrize('row',[0,1,24,205])
def test_original_column_mapping_selects_interleaved_byte_and_wraps_row(original_image,memory,column,row):
    put(memory,0x27A8,APP)  # supplied workspace root consumed by the entry
    cpu=state(memory,ENTRY);cpu.d[0]=0x12340000|column;cpu.d[1]=row
    put(memory,APP+4,FB)
    table=bytes(memory[TABLE:TABLE+40])
    run(original_image,memory,cpu,{AFTER})
    assert cpu.a[0]==FB+((row*160)&32766)+(column//2)*8+column%2
    assert cpu.d[0]==(column//2)*8+column%2
    assert bytes(memory[TABLE:TABLE+40])==table


@pytest.mark.parametrize('index',[40,41,0xFFFF])
def test_original_lookup_does_not_bound_column_to_stored_prefix(original_image,memory,index):
    put(memory,0x27A8,APP)
    cpu=state(memory,ENTRY);cpu.d[0]=index;cpu.d[1]=0
    signed=index if index<32768 else index-65536
    expected=memory[TABLE+signed]
    run(original_image,memory,cpu,{AFTER})
    assert cpu.a[0]==FB+expected
    assert not 0<=signed<40


@pytest.fixture(scope='module')
def palette_field_offsets(tmp_path_factory,original_image):
    import struct
    import subprocess
    from pathlib import Path
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names=['SG2AlternatePalettePacket_'+s for s in [
        'colours_0_1','colours_3_4','colours_5_6','colours_11_12','colours_13_14','colour_15','SIZEOF']]
    folder=tmp_path_factory.mktemp('alternate-packet');asm,out=folder/'fields.s',folder/'fields.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result=subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    raw=out.read_bytes();assert raw[:-28]==original_image[0]
    return struct.unpack('>7I',raw[-28:])


from tests.test_starglider2_alternate_palette_interrupt import sparse_memory,enter,PALETTE,BUFFER,FLAG


def test_exported_packet_fields_match_original_sparse_hardware_copy(original_image,sparse_memory,palette_field_offsets):
    m=sparse_memory;offsets=palette_field_offsets
    pairs=[(0,1),(3,4),(5,6),(11,12),(13,14),(15,)]
    assert offsets[-1]==22
    m[FLAG]=0;m[BUFFER:BUFFER+26]=b'\xCC'*26;m[PALETTE:PALETTE+32]=b'\xA5'*32
    expected=bytearray(b'\xA5'*32)
    for offset,indices in zip(offsets,pairs):
        for n,index in enumerate(indices):
            value=(0x100+index).to_bytes(2,'big')
            m[BUFFER+offset+2*n:BUFFER+offset+2*n+2]=value
            expected[2*index:2*index+2]=value
    from tests.test_starglider2_text_editor import RETURN
    cpu=enter(m);run(original_image,m,cpu,{RETURN})
    assert bytes(m[PALETTE:PALETTE+32])==expected
    assert bytes(m[BUFFER+22:BUFFER+26])==b'\xCC'*4
