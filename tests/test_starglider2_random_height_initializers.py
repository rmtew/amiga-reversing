"""Original four-type placement constructors with dirty record/PRNG inputs.

The WORD mask preserves the PRNG upper WORD used by the LONG height update.
These are local CPU contracts, not spawn reachability, distributions or lifetime.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,STACK,RETURN
from tests.test_starglider2_palette_priority import rng

CONSTRUCTORS={40:0x18526,43:0x18526,41:0x1856E,73:0x1856E}
NAMES={40:b'Pirate Ship',43:b'Skim Launcher Drone',41:b'Space Ray',73:b'Asteroid'}
SEEDS=[(0,0),(1,0),(0x12345678,0x90ABCDEF),(0xFFFFFFFF,0x80000000),
       (0x80000001,7),(0x01000000,0x08000000),(0xFFFF0000,0x00010001),(0x13579BDF,0x2468ACE0)]


def test_original_directories_bind_all_four_types(original_image):
    raw=original_image[0]
    for kind,entry in CONSTRUCTORS.items():
        assert get(raw,0x17EEA-4096+4*kind)==entry
        address=get(raw,0xF334-4096+4*kind)-4096
        assert raw[address:raw.index(b'\0',address)]==NAMES[kind]


@pytest.mark.parametrize('kind',CONSTRUCTORS)
@pytest.mark.parametrize('seed',SEEDS)
@pytest.mark.parametrize('dirty',[0,0xA5])
def test_word_mask_keeps_long_height_bits_and_branch_only_field(original_image,memory,kind,seed,dirty):
    m=memory;m[INPUT-4:INPUT+72]=bytes([dirty])*76;put(m,INPUT,kind,2)
    before=bytes(m[INPUT-4:INPUT+72]);expected=bytearray(m[INPUT:INPUT+68]);a,b=seed
    values=[]
    for _ in range(3 if kind in[41,73]else 2):
        a,b=rng(a,b);values.append(b)
    height_value=values[-2]&0xFFFF03FF
    y=(-18000-height_value if height_value&1 else -18000+height_value)&0xFFFFFFFF
    expected[8:12]=y.to_bytes(4,'big')
    expected[32:34]=(0xFE0C).to_bytes(2,'big')
    expected[36:38]=(values[-1]&31).to_bytes(2,'big')
    if not(height_value&1):expected[38:40]=b'\0\1'
    if kind in[41,73]:
        expected[18:20]=(values[0]&4095).to_bytes(2,'big');expected[2]|=0x21
    put(m,APP+0x60,seed[0]);put(m,APP+0x64,seed[1])
    cpu=state(m,CONSTRUCTORS[kind]);old_d=list(cpu.d);old_a=list(cpu.a)
    run(original_image,m,cpu,{RETURN})
    assert bytes(m[INPUT:INPUT+68])==expected
    assert bytes(m[INPUT-4:INPUT])==before[:4]and bytes(m[INPUT+68:INPUT+72])==before[-4:]
    assert [get(m,APP+off)for off in[0x60,0x64]]==[a,b]
    assert cpu.d[0]==values[-1]&0xFFFF001F and list(cpu.d[1:])==old_d[1:]
    assert list(cpu.a[:7])==old_a[:7]and cpu.a[7]==STACK+4
