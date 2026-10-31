"""Original disc span construction in supplied scratch RAM.

Stop before the downstream planar/interleaved renderer. These cases preserve
header/coordinate arithmetic and aliases, not arbitrary radius/queue safety.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT
from tests.test_starglider2_control_normalization import signed

WORK,PACKET=0x41848,0x6524


def word(m,p,v):put(m,p,v&65535,2)
def accepted(radius,x,y):
    return signed(y+radius)>=30 and signed(y-radius)<=128 and signed(x+radius)>16 and signed(x-radius)<=303


def circle_widths(radius):
    # Integer midpoint recurrence; paired rows retain the original 2*r extent.
    widths={};x=radius;y=0;error=1-radius
    while True:
        if error<0:
            y+=1;error+=2*y+1
        else:
            widths[radius-x]=y;widths[radius+x-1]=y
            y+=1;x-=1;error+=2*(y-x)+1
        widths[radius-y]=x;widths[radius+y-1]=x
        if y>=x:break
    assert set(widths)==set(range(2*radius))
    return[widths[i]for i in range(2*radius)]


def generate(image,m,radius,x,y,colour=7):
    cpu=state(m,0x6326);cpu.d[0]=radius&65535;cpu.d[1]=colour&65535;cpu.d[2]=x&65535;cpu.d[3]=y&65535
    expected=bytearray(m)
    if not accepted(radius,x,y):
        run(image,m,cpu,{0x6324});assert bytes(m)==expected;return cpu,None
    widths=circle_widths(radius);word(expected,WORK,colour);word(expected,WORK+2,y-radius)
    for i,w in enumerate(widths):word(expected,WORK+4+4*i,max(x-w,16));word(expected,WORK+6+4*i,min(x+w,303))
    word(expected,WORK+4+8*radius,65535)
    run(image,m,cpu,{0x641E},limit=3000);assert bytes(m)==expected
    assert cpu.a[6]==WORK+4+8*radius
    return cpu,widths


@pytest.mark.parametrize('radius',range(1,17))
@pytest.mark.parametrize('x',[0,15,16,17,160,302,303,304,320])
@pytest.mark.parametrize('y',[30,79,128])
@pytest.mark.parametrize('colour',[0,0xF123])
def test_midpoint_spans_keep_symmetric_stores_x_clamps_and_exact_marker(original_image,memory,radius,x,y,colour):
    generate(original_image,memory,radius,x,y,colour)


@pytest.mark.parametrize('radius',[-32768,-1,0,1,2000,2001,4095,32767])
@pytest.mark.parametrize('x,y',[(16,30),(17,79),(303,128),(304,129),(0,0),(160,79),(32767,32767)])
def test_entry_word_wrap_rejections_and_top_header_precede_radius_cap(original_image,memory,radius,x,y):
    m=memory;cpu=state(m,0x6326)
    for i,value in enumerate([radius,0xA5F1,x,y]):cpu.d[i]=value&65535
    expected=bytearray(m)
    if accepted(radius,x,y):
        word(expected,WORK,0xA5F1);word(expected,WORK+2,y-radius)
        run(original_image,m,cpu,{0x6366});assert cpu.d[0]&65535==(2000 if signed(radius)>2000 else radius&65535)
    else:run(original_image,m,cpu,{0x6324})
    assert bytes(m)==expected


@pytest.mark.parametrize('radius',[1,2,5,12,50,64])
@pytest.mark.parametrize('y',[0,29,30,31,79,127,128,129,150])
def test_vertical_packet_header_rebase_and_terminal_marker_keep_original_offsets(original_image,memory,radius,y):
    m=memory;cpu,widths=generate(original_image,m,radius,160,y)
    if widths is None:return
    expected=bytearray(m);first=y-radius;pointer=WORK;marker=WORK+4+8*radius
    if first<30:
        pointer=WORK+4*(30-first)-4
        word(expected,pointer,7);word(expected,pointer+2,30)
        if marker<=pointer:
            run(original_image,m,cpu,{0x6324});assert bytes(m)==expected;return
    if first>128:
        run(original_image,m,cpu,{0x6324});assert bytes(m)==expected;return
    excess=first+2*radius-128
    if excess>0:marker-=4*excess;word(expected,marker,65535)
    run(original_image,m,cpu,{0x64C6});assert bytes(m)==expected
    assert cpu.a[0]==pointer and cpu.a[6]==marker


@pytest.mark.parametrize('x',[17,160,302])
def test_zero_radius_aliases_the_header_before_clipping(original_image,memory,x):
    m=memory;cpu=state(m,0x6326);cpu.d[0]=0;cpu.d[1]=7;cpu.d[2]=x;cpu.d[3]=79
    expected=bytearray(m)
    for p in [WORK,WORK+4]:word(expected,p,x+1);word(expected,p+2,x-1)
    run(original_image,m,cpu,{0x641E});assert bytes(m)==expected
    assert cpu.a[6]==WORK+4  # The marker was overwritten; no valid stream claim.


@pytest.mark.parametrize('pointer',[WORK,WORK+40,INPUT,INPUT+128])
def test_single_disc_reference_packet_updates_only_address_and_diagnostics(original_image,memory,pointer):
    m=memory;cpu=state(m,0x64C6);cpu.a[0]=pointer;expected=bytearray(m)
    put(expected,PACKET,pointer);expected[0xE102]=13;expected[0xE103]=0
    assert get(m,PACKET+4)==0xFFFFFFFF
    run(original_image,m,cpu,{0x6538});assert bytes(m)==expected
    assert cpu.a[2]==PACKET and cpu.a[0]==pointer


@pytest.mark.parametrize('x,radius',[(-5,24),(0,20),(15,2),(304,2),(310,12),(320,24)])
@pytest.mark.parametrize('colour',[0,65535])
def test_offscreen_center_trims_matching_prefix_and_suffix_rows(original_image,memory,x,radius,colour):
    m=memory;cpu,widths=generate(original_image,m,radius,x,79,colour);assert widths is not None
    first=next(i for i,w in enumerate(widths)if(x+w>=16 if x<16 else x-w<=303))
    expected=bytearray(m);pointer=WORK+4*first;marker=WORK+4+8*radius-4*first
    word(expected,pointer,colour);word(expected,pointer+2,79-radius+first);word(expected,marker,65535)
    run(original_image,m,cpu,{0x64C6},limit=3000);assert bytes(m)==expected
    assert cpu.a[0]==pointer and cpu.a[6]==marker


@pytest.mark.parametrize('depths',[[],[0],[-32768],[32767,-32768],[-1,0,1],[0,0,1],[3,2,1],[1,2,3],[2,-1,2,32767,-32768],[0,0,0,0]])
def test_disc_pointer_sort_is_descending_signed_and_retains_swap_tie_effect(original_image,memory,depths):
    from tests.test_starglider2_text_editor import STACK
    m=memory;pointers=[INPUT+0x200+16*i for i in range(len(depths))]
    for i,(p,d)in enumerate(zip(pointers,depths)):put(m,INPUT+4*i,p);m[p:p+16]=b'\xA5'*16;word(m,p,d)
    cpu=state(m,0x62C8);cpu.a[2]=INPUT;cpu.a[1]=INPUT+4*len(depths);expected=bytearray(m)
    run(original_image,m,cpu,{0x62FC if depths else 0x631E})
    actual=[get(m,INPUT+4*i)for i in range(len(depths))]
    assert sorted(actual)==sorted(pointers)
    assert[signed(get(m,p,2))for p in actual]==sorted(depths,reverse=True)
    if depths==[0,0,1]:assert actual==[pointers[2],pointers[1],pointers[0]]
    expected[INPUT:INPUT+4*len(depths)]=bytes(m[INPUT:INPUT+4*len(depths)])
    expected[STACK-60:STACK]=bytes(m[STACK-60:STACK])
    assert bytes(m)==expected


@pytest.mark.parametrize('radius',[0,1,2000,32768,65535])
@pytest.mark.parametrize('colour',[0,1,15,32768,65535])
def test_queue_record_unpack_sign_extends_words_and_masks_only_colour_low_word(original_image,memory,radius,colour):
    m=memory;record=INPUT+0x200;put(m,INPUT,record)
    for i,v in enumerate([0xA5A5,radius,colour,0x8000,0x7FFF]):word(m,record+2*i,v)
    cpu=state(m,0x6304);cpu.a[2]=INPUT;expected=bytes(m)
    run(original_image,m,cpu,{0x6314});assert bytes(m)==expected
    assert list(cpu.d[:4])==[signed(radius)&0xFFFFFFFF,(signed(colour)&0xFFFF0000)|(colour&15),0xFFFF8000,0x7FFF]
    assert cpu.a[0]==record+10 and cpu.a[2]==INPUT+4
