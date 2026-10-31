"""Original encounter data consumers with supplied records, not spawn lifetime proof.

The 18 stored pointers bound the recovered directory prefix, not every possible
caller selector. Retirement cursor masking occurs after its current table read.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT
from tests.test_starglider2_control_normalization import signed,word

RECORD=INPUT+0x400
DIRECTORY,CYCLE=0x399A0,0x39AA8


def write(m,address,value,width=4):put(m,address,value&((1<<(8*width))-1),width)


def table_for(m,metric,index):
    # Original CMP.L/BPL tests N alone, including wrapped differences.
    for threshold,table in [(300000000,0x39B28),(150000000,0x39B08),(90000000,0x39AE8)]:
        if signed(metric-threshold,32)>=0:return table
    return get(m,DIRECTORY+4*index)


def choose(image,m,metric,index,draw):
    put(m,APP+0x9B4,metric);word(m,0x830,index)
    m[RECORD:RECORD+68]=b'\xA5'*68;m[RECORD+2]=0x25
    cpu=state(m,0x337E0);cpu.a[4]=RECORD;cpu.d[0]=draw
    expected=bytearray(m);typ=get(m,table_for(m,metric,index)+2*(draw&15),2)
    write(expected,RECORD,typ,2)
    expected[RECORD+29]=m[0x172CE+typ];expected[RECORD+28]=m[0x17D0C+typ]
    expected[RECORD+30]=255;expected[RECORD+3]=0;expected[RECORD+31]=1
    write(expected,RECORD+32,signed(get(m,0x17C30+2*typ,2))>>1,2)
    write(expected,RECORD+44,0,2);write(expected,RECORD+16,1,2)
    if typ==91:expected[RECORD+2]|=128
    if typ==10:write(expected,RECORD+36,1000,2)
    run(image,m,cpu,{0x33896});assert bytes(m)==expected
    assert cpu.d[0]&65535==2*typ


@pytest.mark.parametrize('index',range(18))
@pytest.mark.parametrize('draw',range(16))
def test_all_stored_directory_choices_and_partial_constructor(original_image,memory,index,draw):
    choose(original_image,memory,0,index,0xFEDC0000|draw)


@pytest.mark.parametrize('metric',[89999999,90000000,149999999,150000000,299999999,300000000,0x7FFFFFFF,0x80000000,0xFFFFFFFF])
@pytest.mark.parametrize('draw',range(16))
def test_metric_n_only_selection_keeps_wrapped_extremes(original_image,memory,metric,draw):
    choose(original_image,memory,metric,0,0x1234FFF0|draw)


@pytest.mark.parametrize('cursor',range(33))
@pytest.mark.parametrize('tick',[0,254,255,65535])
@pytest.mark.parametrize('count',[0,4])
def test_retirement_tick_type_only_clear_and_post_read_cursor_mask(original_image,memory,cursor,tick,count):
    m=memory;word(m,0x75C,count);put(m,APP+0x6B8,INPUT)
    put(m,0x39998,tick,2);put(m,0x3999A,cursor,2)
    wanted=get(m,CYCLE+2*cursor,2)
    types=[wanted,wanted^1,wanted,wanted+1]
    for i,typ in enumerate(types):
        p=RECORD+68*i;put(m,INPUT+4*i,p);m[p:p+68]=b'\xA5'*68;put(m,p,typ,2)
    cpu=state(m,0x3367A);expected=bytearray(m);next_tick=(tick+1)&255
    put(expected,0x39998,next_tick,2)
    if next_tick==0 and count:
        for i,typ in enumerate(types):
            if typ==wanted:put(expected,RECORD+68*i,0,2)
        put(expected,0x3999A,(cursor+1)&31,2)
    run(original_image,m,cpu,{0x336C4});assert bytes(m)==expected
