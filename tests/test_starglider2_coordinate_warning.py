"""Original coordinate warning formatter and pointer-only enqueue behavior.

Supplied prefixes/coordinates exercise local CPU behavior, not normal-game
reachability of arbitrary long prefixes or the subsequent display service.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,STACK,RETURN
from tests.test_starglider2_message_lines import QUEUE,COUNT,TIMER

BUFFER=0xB41C


def format_message(image,m,prefix,x,z):
    m[INPUT:INPUT+len(prefix)+1]=prefix+b'\0'
    put(m,INPUT+0x100+4,x);put(m,INPUT+0x100+12,z)
    cpu=state(m,0xAB94);cpu.a[0]=INPUT+0x100;cpu.a[1]=INPUT
    run(image,m,cpu,{RETURN})
    return cpu


@pytest.mark.parametrize('x,z',[(0,0),(0xFFFFFFFF,0xFFFFFFFF),(0x123480FF,0xFEDC7F00),(0x00000100,0xFFFFFEFF)])
@pytest.mark.parametrize('prefix',[b'',b' Danger! Mine Detected:',b'A'*24,b'A'*28])
def test_warning_formats_low_word_high_bytes_without_a_prefix_capacity_guard(original_image,memory,x,z,prefix):
    m=memory;m[BUFFER-2:BUFFER+38]=b'\xA5'*40;put(m,COUNT,10,2);put(m,TIMER,33,2)
    # The table address comes from the original LEA operand, not a duplicate map.
    raw=original_image[0]
    # Locate the actual encoded LEA once, retaining the original byte oracle.
    body=raw[0xAB94-0x1000:0xAC38-0x1000];lea=body.index(bytes.fromhex('43f9'))
    table=get(body,lea+2)
    def digits(value):
        b=m[table+((value>>8)&255)]
        return bytes([48+(b>>4),48+(b&15)])
    text=prefix+digits(x)+digits(z)
    expected=bytearray(b'\xA5'*40);expected[2:30]=b' '*28
    expected[2:2+len(text)]=text
    cpu=format_message(original_image,m,prefix,x,z)
    assert bytes(m[BUFFER-2:BUFFER+38])==expected
    assert cpu.a[1]==BUFFER and cpu.a[3]==BUFFER+len(text)and cpu.a[7]==STACK+4
    assert get(m,COUNT,2)==10 and get(m,TIMER,2)==33


def test_warning_rewrites_same_buffer_before_pointer_dedup_rejects_second_enqueue(original_image,memory):
    m=memory;put(m,COUNT,1,2);put(m,QUEUE,0x50000);put(m,TIMER,33,2)
    format_message(original_image,m,b' Danger! Mine Detected:',0,0)
    assert get(m,COUNT,2)==2 and get(m,QUEUE+4)==BUFFER
    before=bytes(m[BUFFER:BUFFER+30]);queue=bytes(m[QUEUE:QUEUE+40])
    format_message(original_image,m,b' Danger! Mine Detected:',0x8000,0x8000)
    assert bytes(m[BUFFER:BUFFER+30])!=before
    assert bytes(m[QUEUE:QUEUE+40])==queue and get(m,COUNT,2)==2 and get(m,TIMER,2)==33
