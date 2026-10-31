"""Original contact plotting prefixes with supplied records and framebuffer RAM.

Amiga fixtures execute the original row-table initialization prefix. Alternate
fixtures retain the shipped 160-byte row table and stop before scan/aim/message
service. These tests do not establish boot, record lifetime, palette RGB or scanout.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, FB, INPUT, STACK, RETURN
from tests.test_starglider2_heading_strip import BEGIN, END

MASKS,ROW_TABLE,X_OFFSETS,X_MASKS=0x48E8,0x416B8,0x16760,0x169E0
OBJECT=INPUT+0x200
MODES=['amiga','mode0','mode1']


def initialize(image,memory,mode):
    put(memory,APP,FB);memory[APP+0x1F2]=2 if mode=='mode1'else 0
    if mode=='amiga':
        cpu=state(memory,0x3E96E);run(image,memory,cpu,{0x3E98E})
    stride=40 if mode=='amiga'else 160
    assert all(get(memory,ROW_TABLE+2*y,2)==stride*y for y in range(200))
    assert all(get(memory,X_OFFSETS+2*x,2)==2*(x//16) for x in range(128,160))
    assert all(get(memory,X_MASKS+2*x,2)==0x8000>>(x%16) for x in range(128,160))


def configure(memory,records,count=None):
    memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    put(memory,APP+0x6D0,INPUT);put(memory,APP+0x762,len(records)if count is None else count,2)
    for i,record in enumerate(records):
        type_,x,y,z,flags=record;address=OBJECT+64*i
        put(memory,INPUT+4*i,address);put(memory,address,type_&0xFFFF,2);memory[address+2]=flags
        for off,value in [(22,x),(24,y),(26,z)]:put(memory,address+off,value&0xFFFF,2)
    put(memory,INPUT+4*len(records),0)


def expected_canvas(memory,mode,records):
    out=bytearray(b'\xA5'*(END-BEGIN))
    def write(address,data):out[address-BEGIN:address-BEGIN+len(data)]=data
    if mode=='amiga':
        for plane in range(4):
            for row in range(35):write(FB+plane*0x2000+40*(144+row)+16,b'\0'*4)
            write(FB+plane*0x2000+40*161+16,b'\0\0\x80\0')
    elif mode=='mode0':
        for row in range(34):write(FB+160*(144+row)+64,b'\0'*16)
        write(FB+160*159+64,b'\0'*8+b'\x80\0'*4)
    else:
        for row in range(68):write(FB+80*(288+row)+32,b'\0'*8)
        for row in [319,320]:write(FB+80*row+32,b'\0\0\0\1\x80\0\0\0')
    for type_,x,y,z,flags in records:
        if flags&16 or not(-8192<x<8192 and -8192<z<8192):continue
        px,py=144+x//512,160+(-z)//512
        signed_type=(type_+32768)%65536-32768
        colour=memory[MASKS+signed_type]&15 if mode!='mode1'else 1
        if mode=='amiga':
            for plane in range(4):
                if colour>>plane&1:out[FB-BEGIN+0x2000*plane+40*py+px//8]|=0x80>>(px%8)
        elif mode=='mode0':
            for plane in range(4):
                if colour>>plane&1:
                    address=FB-BEGIN+160*py+8*(px//16)+2*plane
                    word=int.from_bytes(out[address:address+2],'big')|0x8000>>(px%16)
                    out[address:address+2]=word.to_bytes(2,'big')
        else:
            # Retain both encoded terms. This is not a uniform x*2 mapping.
            address=FB-BEGIN+160*py+((px//4)&~1);mask=0xC000>>(px&14)
            for vertical in [0,80]:
                a=address+vertical;word=int.from_bytes(out[a:a+2],'big')|mask
                out[a:a+2]=word.to_bytes(2,'big')
    return out


def check_plot(image,memory,mode,records):
    cpu=state(memory,0x4584 if mode=='amiga'else 0x3AA02);visits=[]
    run(image,memory,cpu,{RETURN if mode=='amiga'else 0x3ABF0},visits.append)
    assert cpu.a[7]==STACK+(4 if mode=='amiga'else 0)
    assert bytes(memory[BEGIN:END])==expected_canvas(memory,mode,records)
    return cpu,visits


@pytest.mark.parametrize('mode',MODES)
@pytest.mark.parametrize('type_',range(182))
def test_stored_mask_region_bytes_and_mono_ignored_colour_setup(original_image,memory,mode,type_):
    initialize(original_image,memory,mode);records=[(type_,0,32767,0,0)];configure(memory,records)
    _,visits=check_plot(original_image,memory,mode,records)
    assert (0x4864 in visits)==(mode=='amiga') and (0x3AACE in visits)==(mode=='mode0')
    # Stored extent is not a claim that all182 object types are live/valid.


@pytest.mark.parametrize('mode',MODES)
def test_all_1024_quantized_pixel_bins_and_original_clear_marker_geometry(original_image,memory,mode):
    initialize(original_image,memory,mode)
    for bx in range(-16,16):
        for bz in range(-16,16):
            x=max(-8191,512*bx);z=min(8191,-512*bz)
            records=[(9,x,0,z,0)];configure(memory,records)
            check_plot(original_image,memory,mode,records)


@pytest.mark.parametrize('mode',MODES)
@pytest.mark.parametrize('x,z',[(-32768,0),(-8192,0),(-8191,0),(-1,0),(1,0),(8191,0),
                                  (8192,0),(32767,0),(0,-8192),(0,8192)])
def test_strict_signed_word_clipping_boundaries(original_image,memory,mode,x,z):
    initialize(original_image,memory,mode);records=[(9,x,0,z,0)];configure(memory,records)
    check_plot(original_image,memory,mode,records)


@pytest.mark.parametrize('mode',MODES)
def test_y_is_loaded_but_does_not_move_contact_pixels(original_image,memory,mode):
    initialize(original_image,memory,mode);frames=[]
    for y in [-32768,0,32767]:
        records=[(9,700,y,-800,0)];configure(memory,records);check_plot(original_image,memory,mode,records)
        frames.append(bytes(memory[BEGIN:END]))
    assert frames[0]==frames[1]==frames[2]


@pytest.mark.parametrize('mode',MODES)
def test_skip_flag_restores_saved_table_register_and_coincident_masks_or(original_image,memory,mode):
    initialize(original_image,memory,mode)
    records=[(9,0,0,0,16),(1,1000,0,1000,8),(2,1000,0,1000,128)]
    configure(memory,records);check_plot(original_image,memory,mode,records)


@pytest.mark.parametrize('mode',MODES)
@pytest.mark.parametrize('ending',['null','odd','zero_count','null_cursor','negative_count_null'])
def test_early_termination_is_not_an_entry_skip_or_count_bound(original_image,memory,mode,ending):
    initialize(original_image,memory,mode);records=[(9,0,0,0,0),(9,500,0,500,0)]
    configure(memory,records)
    if ending in ['null','odd']:put(memory,INPUT,0 if ending=='null'else OBJECT|1)
    elif ending=='zero_count':put(memory,APP+0x762,0,2)
    elif ending=='null_cursor':put(memory,APP+0x6D0,0)
    else:put(memory,APP+0x762,0xFFFF,2);put(memory,INPUT,0)
    check_plot(original_image,memory,mode,[])


@pytest.mark.parametrize('mode',MODES)
@pytest.mark.parametrize('type_',[-1,182])
def test_no_type_bound_is_invented_at_either_side_of_source_region(original_image,memory,mode,type_):
    initialize(original_image,memory,mode);put(memory,0x499E,0xA500,2)
    records=[(type_,0,0,0,0)];configure(memory,records);check_plot(original_image,memory,mode,records)


@pytest.mark.parametrize('mode',MODES)
def test_plane_mask_reader_uses_current_ram_low_bits_not_immutable_initial_colour(original_image,memory,mode):
    initialize(original_image,memory,mode);memory[MASKS+9]=0xE3
    records=[(9,0,0,0,0)];configure(memory,records);check_plot(original_image,memory,mode,records)


@pytest.mark.parametrize('value',[0,1,1023,1024,1025,2047,2048,4095,4096,524287,524288,2147483647,-2147483648])
@pytest.mark.parametrize('axis',range(3))
def test_radial_shift_thresholds_wrapped_abs_and_original_register_frame(original_image,memory,value,axis):
    values=[-1,-2,-3];values[axis]=value;cpu=state(memory,0x489A)
    for i,v in enumerate(values,1):cpu.d[i]=v&0xFFFFFFFF
    old_d,old_a=list(cpu.d),list(cpu.a)
    scale=radial_reference(values)
    run(original_image,memory,cpu,{RETURN})
    assert list(cpu.d)[1:4]==old_d[1:4] and list(cpu.a)[:7]==old_a[:7] and cpu.a[7]==STACK+4
    assert cpu.d[6]==(old_d[6]&0xFFFF0000)|scale and cpu.d[4]==512<<scale


def test_all_int_min_deltas_retain_word_counter_high_bits_and_take_wrapped_sign_branch(original_image,memory):
    cpu=state(memory,0x489A);cpu.d[1]=cpu.d[2]=cpu.d[3]=0x80000000;upper=cpu.d[6]&0xFFFF0000
    run(original_image,memory,cpu,{RETURN})
    assert list(cpu.d)[1:4]==[0x80000000]*3 and cpu.d[6]==upper|10 and cpu.d[4]==524288


def radial_reference(values):
    # NEG wraps; subsequent BMI/BPL inspect subtraction's sign bit, ignoring V.
    magnitudes=[(-v if v<0 else v)&0xFFFFFFFF for v in values]
    selected=magnitudes[0]
    for candidate in magnitudes[1:]:
        if (candidate-selected)&0x80000000==0:selected=candidate
    if selected==0x80000000:return 10  # Subtracting the positive threshold wraps.
    return max(0,min(10,selected.bit_length()-10))


@pytest.mark.parametrize('values',[
    (-2147483648,0,0),(0,-2147483648,0),(0,0,-2147483648),
    (-2147483648,0,1),(1,-2147483648,0),(-2147483648,1,2147483647),
    (-2147483647,-2147483648,0),
])
def test_radial_wrapped_sign_comparisons_keep_zero_and_min_order_effects(original_image,memory,values):
    cpu=state(memory,0x489A)
    for i,value in enumerate(values,1):cpu.d[i]=value&0xFFFFFFFF
    upper=cpu.d[6]&0xFFFF0000;scale=radial_reference(values)
    run(original_image,memory,cpu,{RETURN})
    assert cpu.d[6]==upper|scale and cpu.d[4]==512<<scale


@pytest.mark.parametrize('entry,rows,stride,width',[(0x3AD12,68,80,8),(0x3AF30,34,160,16)])
@pytest.mark.parametrize('pattern',[0,0xFFFFFFFF,0xA55A5AA5])
def test_unrolled_fill_helpers_keep_pattern_geometry_and_exact_final_cursor(original_image,memory,entry,rows,stride,width,pattern):
    memory[BEGIN:END]=b'\xA5'*(END-BEGIN);start=BEGIN+0x100
    cpu=state(memory,entry);cpu.a[0]=start;cpu.d[0]=pattern;old_a=list(cpu.a)
    expected=bytearray(memory[BEGIN:END])
    for row in range(rows):
        offset=start-BEGIN+row*stride;expected[offset:offset+width]=pattern.to_bytes(4,'big')*(width//4)
    run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[BEGIN:END])==expected and cpu.d[0]==pattern
    assert cpu.a[0]==start+(rows-1)*stride+width and cpu.a[7]==STACK+4
    assert list(cpu.a)[1:7]==old_a[1:7]
