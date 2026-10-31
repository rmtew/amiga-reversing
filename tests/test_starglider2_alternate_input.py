"""Original serial parser with RAM ports and supplied supervisor frames.

Execute the vector's actual successor for each byte. This does not model MFP/
ACIA delivery, vector-base configuration, physical timing or normal gameplay.
"""
import pytest
from tests.test_starglider2_alternate_palette_interrupt import sparse_memory
from tests.test_starglider2_text_editor import original_image,state,run,put,get,APP,STACK,RETURN

ROOT,VECTOR,DATA,ACK,GWB,KEYS,MAP,HEADER=0x3B5B2,0x118,0xFFFFFC02,0xFFFFFA11,0x27A8,0xDE8C,0x3D74A,0x3B778
PENDING,PRIMARY,SECONDARY,SCALE,YAW,PITCH,SPEED,FIRE,DIRECTIONS=0x203,0x201,0x202,0x740,0x7A2,0x7A4,0x7A8,0x1FD,0x15C


def receive(image,m,byte):
    entry=get(m,VECTOR);m[DATA]=byte;m[ACK]=0x55;put(m,GWB,APP)
    before=bytes(m[APP:APP+0x1000])
    cpu=state(m,entry);cpu.a[6]=APP+0x2000;cpu.sr=0x2600
    put(m,STACK,0x2315,2);put(m,STACK+2,RETURN)
    d=list(cpu.d);a=list(cpu.a);frame=bytes(m[STACK:STACK+6])
    run(image,m,cpu,{RETURN})
    assert list(cpu.d)==d and list(cpu.a[:7])==a[:7]
    assert cpu.a[7]==STACK+6 and cpu.sr==0x2315
    assert bytes(m[STACK:STACK+6])==frame and m[ACK]==0xBF
    assert not any(m[APP+0x2000:APP+0x3000])
    allowed={ROOT:[PENDING,PRIMARY,SECONDARY],0x3B650:[YAW,YAW+1],
             0x3B684:[PITCH,PITCH+1],0x3B6C0:[YAW,YAW+1],
             0x3B6E8:[SPEED,SPEED+1],0x3B730:[FIRE,DIRECTIONS,DIRECTIONS+1]}[entry]
    after=bytearray(m[APP:APP+0x1000])
    for offset in allowed:after[offset]=before[offset]
    assert bytes(after)==before


@pytest.mark.parametrize('byte',range(256))
def test_root_byte_domains_translation_aliases_and_exception_return(original_image,sparse_memory,byte):
    m=sparse_memory;put(m,VECTOR,ROOT);m[KEYS:KEYS+128]=b'\xA5'*128
    m[APP+PENDING]=0xA9;m[APP+PRIMARY]=0x44;m[APP+SECONDARY]=0x66;m[HEADER]=0x33
    expected=bytearray(b'\xA5'*128)
    if byte<0xF8:expected[m[MAP+(byte&127)]]=0 if byte&128 else 1
    receive(original_image,m,byte)
    assert bytes(m[KEYS:KEYS+128])==expected
    assert m[APP+PENDING]==(m[MAP+byte] if byte<128 else 0xA9)
    if byte in [0xFE,0xFF]:
        assert get(m,VECTOR)==0x3B730 and m[HEADER]==byte
        assert [m[APP+PRIMARY],m[APP+SECONDARY]]==[0x44,0x66]
    elif byte>=0xF8:
        assert get(m,VECTOR)==(0x3B6C0 if byte&1 else 0x3B650)
        assert [m[APP+PRIMARY],m[APP+SECONDARY]]==[255 if byte&2 else 0,255 if byte&1 else 0]
    else:assert get(m,VECTOR)==ROOT


@pytest.mark.parametrize('header',range(0xF8,0xFE))
@pytest.mark.parametrize('delta',[0,1,127,128,255])
@pytest.mark.parametrize('scale',[0,1,3,4,7,31,32,63,64,65535])
def test_mouse_packet_uses_actual_vector_phases_and_word_accumulators(original_image,sparse_memory,header,delta,scale):
    m=sparse_memory;put(m,VECTOR,ROOT);put(m,APP+SCALE,scale,2)
    for off in [YAW,PITCH,SPEED]:put(m,APP+off,0x7FFF,2)
    receive(original_image,m,header);receive(original_image,m,delta)
    signed=delta if delta<128 else delta-256
    expected=signed if header&1 else (signed*16)>>(scale&63)
    assert get(m,APP+YAW,2)==(0x7FFF+expected)&65535
    assert get(m,VECTOR)==(0x3B6E8 if header&1 else 0x3B684)
    receive(original_image,m,delta)
    assert get(m,VECTOR)==ROOT
    assert get(m,APP+PITCH,2)==((0x7FFF+signed)&65535 if not header&1 else 0x7FFF)
    assert get(m,APP+SPEED,2)==((0x7FFF+signed)&65535 if header&1 else 0x7FFF)


@pytest.mark.parametrize('header',[0xFE,0xFF])
@pytest.mark.parametrize('byte',range(256))
def test_joystick_header_selects_ignored_or_published_payload(original_image,sparse_memory,header,byte):
    m=sparse_memory;put(m,VECTOR,ROOT);m[APP+FIRE]=0x63;put(m,APP+DIRECTIONS,0xABCD,2)
    receive(original_image,m,header);assert get(m,VECTOR)==0x3B730
    receive(original_image,m,byte);assert get(m,VECTOR)==ROOT
    assert m[APP+FIRE]==((255 if byte&128 else 0) if header&1 else 0x63)
    assert get(m,APP+DIRECTIONS,2)==(byte&15 if header&1 else 0xABCD)


def test_installer_clears_112_key_bytes_not_whole_flag_storage(original_image,sparse_memory):
    m=sparse_memory;m[KEYS-1:KEYS+129]=b'\xA5'*130;put(m,VECTOR,0x12345678)
    cpu=state(m,0x3B3EE);run(original_image,m,cpu,{0x3B404})
    assert get(m,VECTOR)==ROOT
    assert bytes(m[KEYS:KEYS+112])==bytes(112)
    assert bytes(m[KEYS+112:KEYS+129])==b'\xA5'*17 and m[KEYS-1]==0xA5


def test_high_press_indices_alias_following_lut_but_breaks_are_headers(original_image,sparse_memory):
    m=sparse_memory
    assert bytes(m[MAP+120:MAP+128])==bytes.fromhex('00000003000c000f')
    for index in range(120,128):
        put(m,VECTOR,ROOT);receive(original_image,m,index)
        translated=m[MAP+index];assert m[KEYS+translated]==1
        receive(original_image,m,index+128)
        assert m[KEYS+translated]==1 and get(m,VECTOR)!=ROOT
