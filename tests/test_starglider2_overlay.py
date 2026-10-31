"""Original overlay blits and caller prefixes; no sprite DMA or scanout claim.

Supplied draw-bank RAM retains the shipped 160-byte row table. Amiga angle
fixtures start after the hardware pointer write and stop before sprite control
writes. Alternate callers stop before message/meter service.
"""
import json
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, FB, INPUT, STACK, RETURN
from tests.test_starglider2_heading_strip import BEGIN, END

TARGET=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
SPRITES={x['name']:x['source_offset']+0x1000 for x in json.loads((TARGET/'rendered-manifest.json').read_text())['assets']
         if x['name']in ['hud_default_reticle_sprite','hud_scan_reticle_sprite']or x['name'].startswith('object_scan_sprite_frame_')}
DEFAULT,SCAN=SPRITES['hud_default_reticle_sprite'],SPRITES['hud_scan_reticle_sprite']


def signed16(n):return (n+32768)%65536-32768


def draw_reference(memory,before,source,x,y,mode):
    left=min(288,max(16,signed16(x-8)));top=min(112,max(30,signed16(y-8)))
    out=bytearray(before)
    for row in range(16):
        a,b=get(memory,source+4*row,2),get(memory,source+4*row+2,2)
        for col in range(16):
            first,second=(a>>(15-col))&1,(b>>(15-col))&1
            if mode&128:
                for which,value in enumerate([first,second]):
                    if not value:continue
                    px=2*(left+col)+which
                    for vertical in [0,1]:
                        address=FB-BEGIN+80*(2*(top+row)+vertical)+px//8
                        out[address]|=0x80>>(px%8)
            elif first or second:
                px=left+col
                for plane in range(4):
                    address=FB-BEGIN+160*(top+row)+8*(px//16)+2*plane+(px%16)//8
                    bit=0x80>>(px%8);value=first if plane==2 else second if plane==0 else 0
                    out[address]=(out[address]&~bit)|(bit if value else 0)
    return out


def setup(memory,mode):
    put(memory,APP,FB);memory[APP+0x1F2]=mode;memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    for row in range(16):
        put(memory,INPUT+4*row,((0x8421<<row%4)^0x3333*row)&0xFFFF,2)
        put(memory,INPUT+4*row+2,((0x1248>>row%4)^0x5555*row)&0xFFFF,2)
    assert all(get(memory,0x416B8+2*y,2)==160*y for y in range(128))


@pytest.mark.parametrize('mode',[0,2,128,255])
@pytest.mark.parametrize('shift',range(16))
def test_all_alignments_sign_selected_blits_and_transparent_or_replace_pixels(original_image,memory,mode,shift):
    setup(memory,mode);cpu=state(memory,0x3A542);cpu.a[0]=INPUT
    cpu.d[1]=0xBEEF0000|(24+shift);cpu.d[2]=0xCAFE0032
    expected=draw_reference(memory,memory[BEGIN:END],INPUT,24+shift,50,mode)
    run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[BEGIN:END])==expected and cpu.a[0]==INPUT+64 and cpu.a[7]==STACK+4
    assert cpu.d[6]&0xFFFF==0xFFFF


@pytest.mark.parametrize('mode',[0,255])
@pytest.mark.parametrize('x,y',[(-32768,-32768),(-1,-1),(0,0),(23,37),(24,38),(295,119),
                                  (296,120),(297,121),(32767,32767)])
def test_word_subtraction_wrap_and_fixed_clamps_are_retained(original_image,memory,mode,x,y):
    setup(memory,mode);cpu=state(memory,0x3A542);cpu.a[0]=INPUT;cpu.d[1]=x&0xFFFF;cpu.d[2]=y&0xFFFF
    expected=draw_reference(memory,memory[BEGIN:END],INPUT,x,y,mode)
    run(original_image,memory,cpu,{RETURN});assert bytes(memory[BEGIN:END])==expected


@pytest.mark.parametrize('mode',[0,255])
@pytest.mark.parametrize('sprite',sorted(SPRITES))
def test_all_nine_shipped_overlay_payloads_fit_the_fixed_sixteen_row_reader(original_image,memory,mode,sprite):
    setup(memory,mode);source=SPRITES[sprite]+4;cpu=state(memory,0x3A542);cpu.a[0]=source
    cpu.d[1],cpu.d[2]=167,81;expected=draw_reference(memory,memory[BEGIN:END],source,167,81,mode)
    before=bytes(memory[source-4:source+68]);run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[BEGIN:END])==expected and cpu.a[0]==source+64
    assert bytes(memory[source-4:source+68])==before


def test_rotated_split_masks_have_sixteen_original_low_and_high_words(original_image,memory):
    for shift in range(16):
        low=0xFFFF>>shift
        assert get(memory,0x3A648+2*shift,2)==low
        assert get(memory,0x3A668+2*shift,2)==0xFFFF^low


def x_offset(angle):
    value=(-angle)&4095
    if 1024<=value<3072:value=(2048-value)&4095
    folded=(-value)&4095
    return ((folded+2048)%4096-2048)//8


def angle_call(image,memory,amiga,x,y,fixed=0):
    put(memory,APP+0x7A2,x&0xFFFF,2);put(memory,APP+0x7A4,y&0xFFFF,2)
    memory[APP+0x7E6]=fixed;put(memory,APP+0x19C,160,2);put(memory,APP+0x19E,80,2)
    cpu=state(memory,0xD360 if amiga else 0x3AC72);cpu.a[0]=DEFAULT
    run(image,memory,cpu,{0xD3E2 if amiga else 0x3ACF0})
    dx=0 if fixed else x_offset(x)
    dy=0 if fixed else -(signed16(y)//16)if amiga else signed16(-y)//16
    assert (get(memory,APP+0x76A,2),get(memory,APP+0x76C,2))==(dx&0xFFFF,dy&0xFFFF)
    assert (get(memory,APP+0x766,2),get(memory,APP+0x768,2))==((160+dx)&0xFFFF,(80+dy)&0xFFFF)
    assert cpu.a[7]==STACK


@pytest.mark.parametrize('amiga',[False,True])
def test_all_4096_horizontal_control_phases_preserve_original_fold_and_quantization(original_image,memory,amiga):
    for x in range(4096):angle_call(original_image,memory,amiga,x,0)


@pytest.mark.parametrize('amiga',[False,True])
@pytest.mark.parametrize('y',[-32768,-32767,-17,-16,-15,-1,0,1,15,16,17,32767])
def test_vertical_profiles_keep_negation_shift_order_and_word_wrap(original_image,memory,amiga,y):
    angle_call(original_image,memory,amiga,123,y)


@pytest.mark.parametrize('amiga',[False,True])
@pytest.mark.parametrize('fixed',[1,255])
def test_fixed_sight_ignores_angles_and_stores_neutral_positions(original_image,memory,amiga,fixed):
    angle_call(original_image,memory,amiga,32767,-32768,fixed)


@pytest.mark.parametrize('mode',[0,255])
@pytest.mark.parametrize('count',[0,1,2,8,9,16,17,48,49,56])
def test_alternate_scan_countdown_selects_frames_then_draws_scan_reticle(original_image,memory,mode,count):
    setup(memory,mode);memory[APP+0x20A]=1;memory[APP+0x7EA]=8;memory[APP+0x7E6]=1
    put(memory,APP+0x19C,160,2);put(memory,APP+0x19E,80,2);put(memory,APP+0x750,count,2)
    for off,value in [(0xE4,16),(0xE6,304),(0xE8,30),(0xEA,128),(0x7D0,160),(0x7D2,80)]:put(memory,APP+off,value,2)
    before=memory[BEGIN:END];expected=bytearray(before)
    if count>1:
        frame=(count-1)//8;expected=draw_reference(memory,expected,SPRITES[f'object_scan_sprite_frame_{frame}']+4,160,80,mode)
    expected=draw_reference(memory,expected,SCAN+4,160,80,mode)
    cpu=state(memory,0x3ABF0);run(original_image,memory,cpu,{0x3ACFC})
    assert bytes(memory[BEGIN:END])==expected and get(memory,APP+0x750,2)==max(0,count-1)
    assert memory[APP+0x7EA]==8 and cpu.a[7]==STACK


@pytest.mark.parametrize('count',[57,0x100,0xFFFF])
def test_outside_the_producer_domain_is_not_admitted_as_an_eighth_frame(original_image,memory,count):
    setup(memory,0);memory[APP+0x20A]=1;memory[APP+0x7EA]=8;put(memory,APP+0x750,count,2)
    cpu=state(memory,0x3ABF0);run(original_image,memory,cpu,{0x3AC1C})
    assert cpu.d[0]&0xFFFF==28 and get(memory,APP+0x750,2)==(count&0xFF00)|((count-1)&255)
    # Stop before the out-of-directory dereference; no guessed pointer or guest patch.


@pytest.mark.parametrize('mode',[0,255])
@pytest.mark.parametrize('x,y,accepted',[(22,70,False),(23,70,True),(295,70,True),(296,70,False),
                                         (100,37,False),(100,38,True),(100,120,True),(100,121,False)])
def test_caller_rejects_scan_at_exclusive_edges_without_suppressing_reticle(original_image,memory,mode,x,y,accepted):
    setup(memory,mode);memory[APP+0x20A]=1;memory[APP+0x7EA]=8;memory[APP+0x7E6]=1
    put(memory,APP+0x19C,160,2);put(memory,APP+0x19E,80,2);put(memory,APP+0x750,56,2)
    for off,value in [(0xE4,16),(0xE6,304),(0xE8,30),(0xEA,128),(0x7D0,x),(0x7D2,y)]:put(memory,APP+off,value,2)
    expected=bytearray(memory[BEGIN:END])
    if accepted:expected=draw_reference(memory,expected,SPRITES['object_scan_sprite_frame_6']+4,x,y,mode)
    expected=draw_reference(memory,expected,SCAN+4,160,80,mode)
    cpu=state(memory,0x3ABF0);run(original_image,memory,cpu,{0x3ACFC})
    assert bytes(memory[BEGIN:END])==expected and get(memory,APP+0x750,2)==(55 if accepted else 0)


@pytest.mark.parametrize('flags',[0,2,128])
def test_disabled_overlay_bit_leaves_aim_and_scan_state_untouched(original_image,memory,flags):
    setup(memory,255);memory[APP+0x20A]=flags;memory[APP+0x7EA]=8;put(memory,APP+0x750,56,2)
    memory[APP+0x766:APP+0x76E]=b'\xBE\xEF'*4;before=bytes(memory[APP:APP+0x900])
    cpu=state(memory,0x3ABF0);run(original_image,memory,cpu,{0x3ACFC})
    assert bytes(memory[APP:APP+0x900])==before and bytes(memory[BEGIN:END])==b'\xA5'*(END-BEGIN)


@pytest.mark.parametrize('mode',[0,255])
@pytest.mark.parametrize('weapon',[0,9,255])
def test_default_weapon_path_keeps_unclipped_aim_fields_but_clamps_drawing(original_image,memory,mode,weapon):
    setup(memory,mode);memory[APP+0x20A]=1;memory[APP+0x7EA]=weapon
    put(memory,APP+0x750,56,2);put(memory,APP+0x7A2,1024,2);put(memory,APP+0x7A4,15,2)
    put(memory,APP+0x19C,0,2);put(memory,APP+0x19E,0,2)
    dx,dy=x_offset(1024),-1;expected=draw_reference(memory,memory[BEGIN:END],DEFAULT+4,dx,dy,mode)
    cpu=state(memory,0x3ABF0);run(original_image,memory,cpu,{0x3ACFC})
    assert bytes(memory[BEGIN:END])==expected and get(memory,APP+0x750,2)==56
    assert (get(memory,APP+0x766,2),get(memory,APP+0x768,2))==(dx&0xFFFF,dy&0xFFFF)
    assert memory[APP+0x7EA]==weapon
