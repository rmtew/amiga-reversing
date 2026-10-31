"""Original alternate meter packets/backgrounds; RAM effects, not display proof.

Mode0 consumes two source WORDs per row, with directory-selected merges into
four adjacent destination WORDs. Mode1 consumes an AND mask and two OR LONGs,
writing LONG pairs 80 bytes apart. Neither path supplies general clipping.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,FB,INPUT,RETURN,STACK

DIRECTORY,BACKGROUNDS,MODE0,MODE1,ROW_TABLE=0x3BE80,0x3BE44,0x3BE58,0x3BE6C,0x416B8
INDEX,SKIP=0x3CAF0,0x3CAEE


def signed16(v):return v-65536 if v&32768 else v


@pytest.mark.parametrize('mode',[0,128])
def test_capture_five_backgrounds_has_56_rows_not_51(original_image,memory,mode):
    m=memory;m[APP+0x1F2]=mode
    m[0x68000:0x72000]=bytes((i*37+19)&255 for i in range(0xA000))
    expected=bytearray(m);table=MODE1 if mode else MODE0;second=80 if mode else 4
    for i in range(5):
        dest=get(m,BACKGROUNDS+4*i);source=0x68000+get(m,table+4*i)
        for row in range(56):
            for pair,offset in enumerate([0,second]):expected[dest+row*8+pair*4:dest+row*8+pair*4+4]=bytes(m[source+row*160+offset:source+row*160+offset+4])
    for address in[0x3CAE4,0x3CAE6,0x3CAE8,0x3CAEA,0x3C8EE,0x3C7B0,0x3C826,0x3C89A,0x3C990]:expected[address:address+2]=b'\0\0'
    expected[0x3CAEC:0x3CAEE]=b'\0\x0A';expected[INDEX:INDEX+2]=b'\0\x14'
    expected[STACK:STACK+4]=RETURN.to_bytes(4,'big')
    cpu=state(m,0x3BDB2);run(original_image,m,cpu,{RETURN})
    assert bytes(m)==expected


def prepare(m,mode,directory):
    m[APP+0x1F2]=mode;put(m,APP,FB);put(m,INDEX,directory*4,2)
    for i in range(5):
        source=get(m,BACKGROUNDS+4*i);m[source:source+448]=bytes((i*17+j*13)&255 for j in range(448))
    return FB+get(m,(MODE1 if mode else MODE0)+directory*4)


@pytest.mark.parametrize('mode',[0,128])
@pytest.mark.parametrize('directory',range(5))
@pytest.mark.parametrize('level',[0,7,46,47])
@pytest.mark.parametrize('rows',[1,3,6])
def test_restore_then_draw_both_row_formats(original_image,memory,mode,directory,level,rows):
    m=memory;base=prepare(m,mode,directory);m[SKIP]=0
    # Distinct supplied packet bytes; mode0 skips four control bytes only.
    m[INPUT:INPUT+100]=bytes((i*59+0x37)&255 for i in range(100))
    expected=bytearray(m);background=get(m,BACKGROUNDS+directory*4);second=80 if mode else 4
    for row in range(51):
        for pair,offset in enumerate([0,second]):expected[base+row*160+offset:base+row*160+offset+4]=bytes(m[background+row*8+pair*4:background+row*8+pair*4+4])
    index=signed16(((46-level)*2)&65535);start=base+signed16(get(m,ROW_TABLE+index,2))
    source=INPUT if mode else INPUT+4;target=get(m,DIRECTORY+directory*4)
    for row in range(rows):
        at=start+row*160
        if mode:
            keep=get(m,source+row*12);first=get(m,source+row*12+4);other=get(m,source+row*12+8)
            for offset,value in[(0,first),(80,other)]:expected[at+offset:at+offset+4]=((int.from_bytes(expected[at+offset:at+offset+4],'big')&keep)|value).to_bytes(4,'big')
        else:
            first=get(m,source+row*4,2);other=get(m,source+row*4+2,2);keep=~(first|other)&65535
            # Two actual directory routines: mixed source colours, not a guessed sprite ID.
            additions=[first&~other,0,0,first]if target==0x3CA26 else[first&other,0,first&~other,0]
            assert target in[0x3CA26,0x3CA4A]
            for plane,value in enumerate(additions):
                dest=at+2*plane;old=int.from_bytes(expected[dest:dest+2],'big');expected[dest:dest+2]=((old&keep)|(value&65535)).to_bytes(2,'big')
    expected[STACK:STACK+4]=RETURN.to_bytes(4,'big')
    cpu=state(m,0x3C9BC);cpu.a[1]=INPUT;cpu.d[0]=level;cpu.d[4]=rows-1
    run(original_image,m,cpu,{RETURN})
    # The implementation saves/restores its base at the stack slot below the return.
    expected[cpu.a[7]-8:cpu.a[7]-4]=base.to_bytes(4,'big')
    assert bytes(m)==expected
    assert cpu.a[1]==source+rows*(12 if mode else 4)


@pytest.mark.parametrize('mode',[0,128])
@pytest.mark.parametrize('skip,space,exits',[(128,128,True),(255,255,True),(128,0,False),(1,128,False),(0,128,False)])
def test_altitude_skip_clears_negative_flag_only_and_runs_after_restore(original_image,memory,mode,skip,space,exits):
    m=memory;base=prepare(m,mode,4);m[SKIP]=skip;m[APP+0x77D]=space
    cpu=state(m,0x3C9BC);cpu.a[1]=INPUT;cpu.d[0]=46;cpu.d[4]=0
    stop=0x3CAB6 if mode else 0x3CA0E
    run(original_image,m,cpu,{RETURN,stop})
    assert cpu.pc==(RETURN if exits else stop)
    assert m[SKIP]==(0 if skip&128 else skip)
    background=get(m,BACKGROUNDS+16)
    for row in range(51):
        assert bytes(m[base+row*160:base+row*160+4])==bytes(m[background+row*8:background+row*8+4])
        second=80 if mode else 4
        assert bytes(m[base+row*160+second:base+row*160+second+4])==bytes(m[background+row*8+4:background+row*8+8])


@pytest.mark.parametrize('entry,colours',[(0x3CA26,{1:0,2:9,3:8}),(0x3CA4A,{1:0,2:4,3:1})])
@pytest.mark.parametrize('rows',[1,6])
@pytest.mark.parametrize('first,other',[(0,0),(65535,0),(0,65535),(65535,65535),(0xAAAA,0x5555),(0x5555,0xAAAA),(0x1234,0x5678)])
def test_two_word_packets_have_exact_per_bit_output_indices(original_image,memory,entry,colours,rows,first,other):
    m=memory;dest=FB+0x40
    for row in range(rows):
        put(m,INPUT+row*4,first,2);put(m,INPUT+row*4+2,other,2)
    cpu=state(m,entry);cpu.a[1]=INPUT;cpu.a[2]=dest;cpu.d[4]=0xBEEF0000|(rows-1)
    expected=bytearray(m)
    for row in range(rows):
        for bit in range(16):
            selector=(((first>>bit)&1)<<1)|((other>>bit)&1)
            if not selector:continue
            for plane in range(4):
                at=dest+row*160+plane*2;value=int.from_bytes(expected[at:at+2],'big')
                value=(value&~(1<<bit))|(((colours[selector]>>plane)&1)<<bit)
                expected[at:at+2]=value.to_bytes(2,'big')
    run(original_image,m,cpu,{RETURN})
    assert bytes(m)==expected
    assert cpu.a[1]==INPUT+4*rows and cpu.a[2]==dest+160*rows
    assert cpu.d[4]==0xBEEFFFFF


def interleave(first,second):
    result=0
    for bit in range(15,-1,-1):result=(result<<2)|(((first>>bit)&1)<<1)|((second>>bit)&1)
    return result


@pytest.mark.parametrize('mode',[0,1,127,128,255])
@pytest.mark.parametrize('first,other',[(0,0),(65535,0),(0,65535),(65535,65535),(0xAAAA,0x5555),(0x5555,0xAAAA),(0x1234,0x5678)])
def test_original_row_converter_produces_the_consumed_and_or_packet(original_image,memory,mode,first,other):
    m=memory;packet=FB+0x300;put(m,INPUT,first,2);put(m,INPUT+2,other,2);m[INPUT+0x80]=mode
    m[packet-4:packet+16]=b'\xA5'*20
    cpu=state(m,0x3A4C6);cpu.a[5]=INPUT;cpu.a[1]=packet;cpu.a[4]=INPUT+0x80
    run(original_image,m,cpu,{0x3A530})
    if mode&128:words=[first&other,0,first&~other,0]
    elif mode:words=[first,other,0,0]
    else:words=[first&~other,0,0,first]
    keep=~(first|other)&65535
    expected=[interleave(keep,keep),interleave(words[0],words[1]),interleave(words[2],words[3])]
    assert [get(m,packet+i*4)for i in range(3)]==expected
    assert bytes(m[packet-4:packet])==bytes(m[packet+12:packet+16])==b'\xA5'*4
    assert cpu.a[5]==INPUT+4 and cpu.a[1]==packet+12 and cpu.a[4]==INPUT+0x80
    # Execute the actual mode1 row consumer on the actual produced bytes.
    dest=FB+0x400;put(m,dest,0x965AC33C);put(m,dest+80,0x5A963CC3)
    cpu=state(m,0x3CAC4);cpu.a[1]=packet;cpu.a[2]=dest;cpu.d[4]=0
    run(original_image,m,cpu,{RETURN})
    assert get(m,dest)==(0x965AC33C&expected[0])|expected[1]
    assert get(m,dest+80)==(0x5A963CC3&expected[0])|expected[2]
