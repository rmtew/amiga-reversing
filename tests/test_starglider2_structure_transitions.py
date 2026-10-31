"""Original transition CPU paths up to world-pool handoff, plus local guards.

Supplied RAM/records are not a normal-game reachability, rebuild, DMA or lifetime
proof. No initializer/callback is replaced to manufacture a full transition.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, RETURN, STACK
from tests.test_starglider2_structure_profiles import setup, STRUCT, OBJECT
from tests.test_starglider2_scan_acquisition import signed16


def prepare(memory):
    setup(memory,kind=30);put(memory,STRUCT,48,2)
    for off,v in [(0x704,10000),(0x708,-290),(0x70C,20000)]:put(memory,APP+off,v&0xFFFFFFFF)
    put(memory,APP+0x744,201,2);put(memory,APP+0x798,3,2)
    put(memory,APP+0x6FC,0xFFFFFFFF)
    memory[APP+0x77C]=0;memory[APP+0x77E]=123;memory[APP+0xBBA]=7


@pytest.mark.parametrize('axis',[0x704,0x70C])
@pytest.mark.parametrize('rotation',[-32768,-201,-200,0,200,201,32767])
@pytest.mark.parametrize('difference',[-65536,-711,-710,-1,0,710,711,32768])
def test_entry_heading_and_cross_gate_keep_word_aliases(original_image,memory,rotation,difference,axis):
    prepare(memory);put(memory,APP+0x744,rotation&65535,2)
    put(memory,APP+axis,((10000 if axis==0x704 else 20000)-difference)&0xFFFFFFFF)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT
    run(original_image,memory,cpu,{0xBF04,0xB9A2})
    # Sign test uses LONG; NEG affects only WORD, followed by signed WORD compare.
    cross=signed16(-difference if difference<0 else difference)
    allowed=(((-rotation if rotation<0 else rotation)&65535)>200 and cross<=710)
    assert cpu.pc==(0xBF04 if allowed else 0xB9A2)


@pytest.mark.parametrize('variant',[0,1,255])
@pytest.mark.parametrize('layout',[0,15,16,31,65535])
def test_entry_pre_pool_effects_and_first_mask_selection(original_image,memory,variant,layout):
    prepare(memory);memory[STRUCT+36]=variant;put(memory,APP+0x798,layout,2)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT
    object_before=bytes(memory[OBJECT:OBJECT+68])
    run(original_image,memory,cpu,{0xBF74})
    assert [get(memory,APP+o)for o in [0x704,0x708,0x70C]]==[10000,(-1384)&0xFFFFFFFF,21600 if variant==0 else 19500]
    assert memory[APP+0x77C]==255 and memory[APP+0x77E]==0
    assert memory[APP+0xBBA]==(255 if variant==0 else 254)
    assert get(memory,APP+0x798,2)==((layout+16)&31)
    assert get(memory,APP+0x6FC)==get(memory,0x176A2)  # first mask, not layout-indexed
    assert bytes(memory[OBJECT:OBJECT+68])==object_before
    assert bytes(memory[0xE102:0xE104])==b'\x90\0'


@pytest.mark.parametrize('y',[-1000,-291])
def test_entry_low_y_return_restores_frame_then_rebinds_workspace(original_image,memory,y):
    prepare(memory);put(memory,APP+0x708,y&0xFFFFFFFF)
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT;cpu.a[6]=0x171FC
    d,a=list(cpu.d),list(cpu.a)
    run(original_image,memory,cpu,{RETURN})
    assert list(cpu.d)==d and list(cpu.a)[:6]==a[:6]
    assert cpu.a[6]==APP and cpu.a[7]==STACK+4
    assert memory[APP+0x77C]==0 and memory[APP+0x77E]==123


@pytest.mark.parametrize('orientation',[0,1])
@pytest.mark.parametrize('response',[0,255])
@pytest.mark.parametrize('difference',[-65536,-1,575,576,32767,32768,65535,65536,66112])
def test_exit_motion_and_signed_low_word_threshold(original_image,memory,orientation,response,difference):
    prepare(memory);put(memory,STRUCT+18,orientation,2);memory[APP+0x7CE]=response
    # MOVEM.W sign-extends; doubled as LONG before adding/subtracting.
    for off,v in zip([0x74A,0x74C,0x74E],[65535,32768,1]):put(memory,APP+off,v,2)
    direction=-1 if response else 1
    final_z=20000+(-difference if orientation else difference)
    put(memory,APP+0x70C,(final_z-direction*2)&0xFFFFFFFF)
    cpu=state(memory,0xBDAE);cpu.a[2]=STRUCT
    run(original_image,memory,cpu,{0xBE16,0xBAE0})
    assert get(memory,APP+0x704)==((10000-direction*2)&0xFFFFFFFF)
    assert get(memory,APP+0x708)==((-290-direction*65536)&0xFFFFFFFF)
    assert cpu.pc==(0xBE16 if signed16(difference)>575 else 0xBAE0)


@pytest.mark.parametrize('layout',[0,15,16,31,65535])
@pytest.mark.parametrize('bomb',[0,1,0x80000000])
def test_exit_pre_pool_copies_record_and_snapshots_nonnull_bomb(original_image,memory,layout,bomb):
    prepare(memory);put(memory,APP+0x798,layout,2);put(memory,APP+0xA76,bomb)
    memory[APP+0x77C]=255;cpu=state(memory,0xBE16);cpu.a[2]=STRUCT
    run(original_image,memory,cpu,{0xBE90})
    expected=[10000,(-1200)&0xFFFFFFFF,20000]
    assert [get(memory,APP+o)for o in [0x704,0x708,0x70C]]==expected
    assert [get(memory,OBJECT+o)for o in [4,8,12]]==expected
    assert get(memory,APP+0x744,2)==get(memory,OBJECT+16,2)==1023
    assert memory[APP+0x77C]==0 and memory[APP+0xBBA]==2 and memory[APP+0x786]==102
    assert get(memory,APP+0x798,2)==((layout-16)&15)
    assert get(memory,APP+0x6FC)==get(memory,0x176A2+4*((layout-16)&15))
    assert memory[0xC4CC]==(255 if bomb else 0)  # nonnull test, no dereference


@pytest.mark.parametrize('projector',[0,127,128,255])
@pytest.mark.parametrize('snapshot',[0,255])
def test_post_pool_guards_are_signed_byte_tests_in_projector_then_bomb_order(original_image,memory,projector,snapshot):
    prepare(memory);put(memory,APP+0x830,3,2)
    memory[0x37B46+3]=projector;memory[0xC4CC]=snapshot
    cpu=state(memory,0xBE94)
    run(original_image,memory,cpu,{0xBEA6,0xBEB2,RETURN})
    assert cpu.pc==(0xBEA6 if projector>=128 else 0xBEB2 if snapshot>=128 else RETURN)
