"""Original alternate-profile table/code/data transformations in supplied RAM.

Entry follows the external mode-register read. No hardware mode switch,
interrupt delivery, normal boot or converted-sprite lifetime is inferred.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,RETURN

XOFF,MASK,BCD=0x16760,0x169E0,0x16C60
STUBS,COCKPIT,SPLASH=0x34A4,0x5341C,0x56554
ANIMATION,END=0x4EA7A,0x5341A
OFFSETS=[2,8,14,20,26,32,44,50]
MODE0=[0x3A950,0x3A9C0,0x3A760,0x3A756,0x3A8F0,0x3AA02,0x4D360,0x4DF8E]
MODE1=[0x3A540,0x3A540,0x3A82A,0x3A820,0x3A8F0,0x3AA02,0x4D360,0x4DF8E]


def interleave(a,b):
    return sum(((a>>k)&1)<<(2*k+1)|((b>>k)&1)<<(2*k)for k in range(16))


@pytest.mark.parametrize('mode_byte',range(256))
def test_input_bit1_selects_x_offsets_and_conditional_reverse_mask_rewrite(original_image,memory,mode_byte):
    m=memory;cpu=state(m,0x3A2F8);cpu.d[0]=0xA5A50000|mode_byte;expected=bytearray(m)
    expected[APP+0x1F2]=mode_byte
    paired=bool(mode_byte&2)
    for x in range(320):
        put(expected,XOFF+2*x,(x//8)*2 if paired else(x//16)*8,2)
        if paired:put(expected,MASK+2*x,0x8000>>(2*(x&7)),2)
    put(expected,0x7920,0x68000+(0x6FEC if paired else 0x6F58))
    put(expected,0x7924,0x68000+(0x6FE8 if paired else 0x6F50))
    run(original_image,m,cpu,{0x3A37E},limit=3000);assert bytes(m)==expected
    assert bytes(m[BCD:BCD+256])==expected[BCD:BCD+256]


@pytest.mark.parametrize('pattern',[None,0,65535,0xA55A,0x0123,0xF888,0x0777,0xFEDC])
@pytest.mark.parametrize('mode_byte',[0,1,0x80,0xFD])
def test_mode0_callback_patching_and_palette_conversion_reentry(original_image,memory,pattern,mode_byte):
    m=memory
    if pattern is not None:
        for i in range(16):put(m,COCKPIT+2*i,(pattern+i)&65535,2);put(m,SPLASH+2*i,(pattern-i)&65535,2)
    for repeat in range(2):
        m[APP+0x1F2]=mode_byte;cpu=state(m,0x3A37E);expected=bytearray(m)
        expected[APP+0x1F2]=0
        for off,target in zip(OFFSETS,MODE0):put(expected,STUBS+off,target)
        for p in [COCKPIT,SPLASH]:
            for i in range(16):put(expected,p+2*i,(get(m,p+2*i,2)>>1)&0x777,2)
        put(expected,COCKPIT,1,2)
        run(original_image,m,cpu,{RETURN});assert bytes(m)==expected


@pytest.mark.parametrize('mode_byte',[2,3,0x7E,0xFF])
def test_mode1_disables_two_fades_and_patches_profile_specific_targets(original_image,memory,mode_byte):
    m=memory;m[APP+0x1F2]=mode_byte;cpu=state(m,0x3A37E);expected=bytearray(m)
    expected[APP+0x1F2]=255
    for off,target in zip(OFFSETS,MODE1):put(expected,STUBS+off,target)
    run(original_image,m,cpu,{0x3A450});assert bytes(m)==expected


@pytest.mark.parametrize('a',[0,1,0x8000,0x7FFF,0xFFFF,0x5555,0xAAAA,0xA55A])
@pytest.mark.parametrize('b',[0,1,0x8000,0x7FFF,0xFFFF,0x5555,0xAAAA,0x5AA5])
def test_panel_word_pairs_pack_bits_in_order_and_replace_in_place(original_image,memory,a,b):
    m=memory;cpu=state(m,0x3A466);cpu.a[0]=cpu.a[1]=INPUT;cpu.d[5]=0
    for i,v in enumerate([a,b,b,a]):put(m,INPUT+2*i,v,2)
    expected=bytearray(m);put(expected,INPUT,interleave(a,b));put(expected,INPUT+4,interleave(b,a))
    run(original_image,m,cpu,{0x3A4A2});assert bytes(m)==expected
    assert cpu.a[0]==cpu.a[1]==INPUT+8 and cpu.d[5]&65535==65535


def test_complete_original_animation_extent_and_reentry_keep_exact_boundaries(original_image,memory):
    m=memory;assert END-ANIMATION==18848 and(END-ANIMATION)%8==0
    for repeat in range(2):
        cpu=state(m,0x3A450);expected=bytearray(m)
        for p in range(ANIMATION,END,4):put(expected,p,interleave(get(m,p,2),get(m,p+2,2)))
        run(original_image,m,cpu,{0x3A4A2},limit=600000)
        assert bytes(m)==expected and cpu.a[0]==cpu.a[1]==END
        assert cpu.d[5]&65535==65535
