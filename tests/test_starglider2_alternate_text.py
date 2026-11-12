"""Original alternate text paths with supplied RAM/control inputs.

No normal-input reachability, physical scanout, interrupt sharing or arbitrary
cursor/font bounds claim. Mode-specific address and byte-width quirks remain.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,FB,INPUT,RETURN,FONT,COL,ROW,DEST,INVERSE,COLOUR

CURSOR={0:0x3B9D2,1:0x3B7D6}
POSITIONED={0:0x3B91C,1:0x3B77A}


def offset(mode,column,row):
    return row*1280+(column*2 if mode else (column//2)*8+column%2)


def setup(memory,mode,column=0,row=0):
    put(memory,0x27A8,APP);put(memory,APP+4,FB);put(memory,APP,FB+0x8000)
    put(memory,4,FB+0x4000)
    memory[COL],memory[ROW],memory[INVERSE]=column,row,0
    put(memory,DEST,FB+offset(mode,column,row))


def print_text(original_image,memory,entry,text):
    memory[INPUT:INPUT+len(text)]=text
    cpu=state(memory,entry);cpu.a[1]=INPUT
    before_d=list(cpu.d);before_a=list(cpu.a)
    run(original_image,memory,cpu,{RETURN})
    return cpu,before_d,before_a


def expanded(byte):
    return sum(((byte>>bit)&1)*3<<(2*bit) for bit in range(8)).to_bytes(2,'big')


@pytest.mark.parametrize('mode',[0,1])
@pytest.mark.parametrize('mask',range(16))
@pytest.mark.parametrize('inverse',[False,True])
@pytest.mark.parametrize('character',[ord('A'),126])
def test_original_glyph_planes_colour_controls_and_inverse_restoration(original_image,memory,mode,mask,inverse,character):
    setup(memory,mode);memory[COLOUR]=6
    font=bytes(memory[FONT:FONT+768]);before=bytes(memory[FB:FB+0x8000]);expected=bytearray(before)
    text=bytes([0x80|mask,1 if inverse else 2,character,0])
    cpu,d,a=print_text(original_image,memory,CURSOR[mode],text)
    glyph=font[8*(character-32):8*(character-31)]
    for row,value in enumerate(glyph):
        if inverse:value^=255
        if mode:
            for extra in [0,80]:expected[160*row+extra:160*row+extra+2]=expanded(value)
        else:
            for plane in range(4):expected[160*row+2*plane]=value if(mask>>plane)&1 else 0
    assert bytes(memory[FB:FB+0x8000])==expected
    assert bytes(memory[FONT:FONT+768])==font
    assert memory[COLOUR]==(6 if mode else mask)
    assert memory[INVERSE]==(255 if inverse else 0)
    assert (memory[COL],memory[ROW],get(memory,DEST))==(1,0,FB+(2 if mode else 1))
    if not mode:assert list(cpu.d)==d and list(cpu.a[:7])==a[:7]
    else:assert cpu.d[0]==d[0] and cpu.a[0]==a[0] and cpu.a[2]==a[2]


@pytest.mark.parametrize('mode',[0,1])
@pytest.mark.parametrize('column,row,text,out_column,out_row',[
    (5,2,b'\r\0',0,2),(5,2,b'\n\0',5,3),(5,24,b'\n\0',0,0),
    (39,2,b'A\0',0,3),(39,24,b'A\0',0,0),(38,2,b'\t\0',44,2)])
def test_original_cursor_controls_keep_distinct_wrap_roots(original_image,memory,mode,column,row,text,out_column,out_row):
    setup(memory,mode,column,row)
    print_text(original_image,memory,CURSOR[mode],text)
    if text==b'\r\0':expected=FB+row*1280
    elif text==b'\t\0':expected=FB+offset(mode,column,row)+(12 if mode else 24)
    elif out_row==0:expected=FB+(0x4000 if mode and text==b'\n\0' else 0x8000 if mode else 0)
    elif text==b'\n\0':expected=FB+offset(mode,column,row)+1280
    else:expected=FB+out_row*1280
    assert (memory[COL],memory[ROW],get(memory,DEST))==(out_column,out_row,expected)


@pytest.mark.parametrize('mode',[0,1])
@pytest.mark.parametrize('column,row',[(40,0),(0,25),(255,255)])
def test_wrap_comparisons_do_not_normalize_arbitrary_cursor_inputs(original_image,memory,mode,column,row):
    setup(memory,mode,column,row)
    # TAB has no row/column bounds guard; byte column arithmetic wraps alone.
    initial=get(memory,DEST)
    print_text(original_image,memory,CURSOR[mode],b'\t\0')
    assert (memory[COL],memory[ROW],get(memory,DEST))==((column+6)&255,row,initial+(12 if mode else 24))


@pytest.mark.parametrize('mode',[0,1])
@pytest.mark.parametrize('mask',[0,5,15])
@pytest.mark.parametrize('separator',[b'',b'\r',b'\n'])
def test_positioned_variants_keep_separate_control_and_register_contracts(original_image,memory,mode,mask,separator):
    setup(memory,mode,11,7);memory[COLOUR]=6
    text=bytes([0x80|mask])+b'A'+separator+b'B\0'
    memory[INPUT:INPUT+len(text)]=text
    cpu=state(memory,POSITIONED[mode]);cpu.a[1]=INPUT;cpu.d[0]=3;cpu.d[1]=2
    d,a=list(cpu.d),list(cpu.a);font=bytes(memory[FONT:FONT+760])
    expected=bytearray(memory[FB:FB+0x8000]);cursor=320+(6 if mode else 9)
    for character in b'AB':
        for row,value in enumerate(font[8*(character-32):8*(character-31)]):
            if mode:
                for extra in [0,80]:expected[cursor+160*row+extra:cursor+160*row+extra+2]=expanded(value)
            else:
                for plane in range(4):expected[cursor+160*row+2*plane]=value if(mask>>plane)&1 else 0
        cursor+=2 if mode else 7 if cursor&1 else 1
        if character==ord('A')and separator==b'\n':cursor+=1280
    run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[FB:FB+0x8000])==expected
    assert bytes(memory[FONT:FONT+760])==font
    assert (memory[COL],memory[ROW],get(memory,DEST))==(11,7,FB+offset(mode,11,7))
    assert memory[COLOUR]==(6 if mode else mask)
    assert cpu.a[0]==a[0]and cpu.a[2]==a[2]
    if not mode:assert list(cpu.d)==d and list(cpu.a[:7])==a[:7]


@pytest.mark.parametrize('mode',[0,1])
@pytest.mark.parametrize('control',[3,8,9,31])
def test_positioned_unsupported_controls_keep_byte_vs_word_font_underflow(original_image,memory,mode,control):
    setup(memory,mode);memory[INPUT:INPUT+2]=bytes([control,0])
    cpu=state(memory,POSITIONED[mode]);cpu.a[1]=INPUT;cpu.d[0]=cpu.d[1]=0
    # Stop after original ADDA of the glyph offset, before drawing from it.
    run(original_image,memory,cpu,{0x3B7C2 if mode else 0x3B978})
    mask=65535 if mode else 255
    assert cpu.a[2]==FONT+((control-32)&mask)*8
    assert not FONT<=cpu.a[2]<FONT+760
