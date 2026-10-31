"""Original alternate palette RAM preparation; not interrupt/device/scanout proof."""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP
from tests.test_starglider2_palette_priority import prepare,atmospheric,rng,GRAY,FADE,SPIN,FLASH,BASE,OTHER,COLOURS

OUTPUT,OVERRIDE,RAMP=0x3BD60,0x4DDA0,0x4DD7C
SENTINEL=0xA55A


def setup(memory):
    prepare(memory);put(memory,OVERRIDE,0,2);put(memory,OUTPUT,SENTINEL,2)


def palette(image,memory):
    neighbours=bytes(memory[OUTPUT-8:OUTPUT])+bytes(memory[OUTPUT+2:OUTPUT+10])
    cpu=state(memory,0x4DB1E);run(image,memory,cpu,{0x4DD3A})
    assert bytes(memory[OUTPUT-8:OUTPUT])+bytes(memory[OUTPUT+2:OUTPUT+10])==neighbours
    assert [get(memory,a,2)for a in COLOURS]==[SENTINEL]*3
    return get(memory,OUTPUT,2)


def converted(value):return(value>>1)&0x777


@pytest.mark.parametrize('count',range(18))
def test_gray_decrement_prefix_and_unchecked_following_words(original_image,memory,count):
    setup(memory);put(memory,GRAY,count,2)
    expected=SENTINEL if count==0 else converted(get(memory,RAMP+2*(count-1),2))
    assert palette(original_image,memory)==expected
    assert get(memory,GRAY,2)==((count-1)&65535)


@pytest.mark.parametrize('fade',[0,1,7,8,15,16,63,64,127])
@pytest.mark.parametrize('gray',[0xFFFF,0xFFFE,0x8001,0x8000])
def test_fade_falls_through_gray_but_expiry_does_not(original_image,memory,fade,gray):
    setup(memory);memory[FADE]=fade;put(memory,GRAY,gray,2)
    expected=SENTINEL if fade==0 else converted((fade-1)>>3)
    next_gray=gray
    if fade:
        next_gray=(gray-1)&65535
        if next_gray&0x8000:next_gray=65535
        else:
            offset=(next_gray*2)&65535
            if offset&0x8000:offset-=65536
            expected=converted(get(memory,RAMP+offset,2))
    assert palette(original_image,memory)==expected
    assert memory[FADE]==((fade-1)&255)
    assert get(memory,GRAY,2)==next_gray


@pytest.mark.parametrize('inside,space,override',[(i,s,o)for i in[0,1]for s in[0,1]for o in[0,1]])
def test_separate_override_and_inside_converted_constants(original_image,memory,inside,space,override):
    setup(memory);memory[APP+0x77C]=inside;memory[APP+0x77D]=space;put(memory,OVERRIDE,override,2)
    expected=(0x335 if override else 0x112)if inside else converted(0x456 if override else 0x123)if space else converted(atmospheric(memory,0,0,override))
    assert palette(original_image,memory)==expected


@pytest.mark.parametrize('body',[0,1,3,8,15,16,65535])
@pytest.mark.parametrize('height',[0,1,0xFFFF,0x10000,0x7FFFFFFF,0x80000000,0xFFFFFFFF])
@pytest.mark.parametrize('override',[0,1])
def test_world_and_surface_signed_word_component_wrap(original_image,memory,body,height,override):
    setup(memory);put(memory,APP+0x830,body,2);put(memory,APP+0x708,height);put(memory,OVERRIDE,override,2)
    assert palette(original_image,memory)==converted(atmospheric(memory,body,height,override))


@pytest.mark.parametrize('count',[0,1,2,3,479,480,481,499,500,501,502,32767])
@pytest.mark.parametrize('override',[0,1])
def test_flash_odd_routes_to_space_even_when_not_in_space(original_image,memory,count,override):
    setup(memory);put(memory,FLASH,count,2);put(memory,OVERRIDE,override,2)
    n=(count-1)&65535
    value=(0x456 if override else 0x123)if n&1 else 0xFFF if n>=500 else 0xF07 if n>=480 else(n<<3)&0xF00
    assert palette(original_image,memory)==converted(value)
    assert get(memory,FLASH,2)==n


@pytest.mark.parametrize('a,b',[(0,0),(0x12345678,0xABCDEF01),(0xFFFFFFFF,0x80000000)])
def test_random_uses_shared_rng_then_colour_conversion(original_image,memory,a,b):
    setup(memory);put(memory,SPIN,0,2);put(memory,APP+0x60,a);put(memory,APP+0x64,b)
    aa,bb=rng(a,b)
    assert palette(original_image,memory)==converted(bb&4095)
    assert [get(memory,APP+o)for o in[0x60,0x64]]==[aa,bb]
    assert get(memory,SPIN,2)==0


@pytest.mark.parametrize('selected',['gray','fade','random','inside','flash','space','surface'])
def test_priority_suppresses_lower_branches_without_updating_their_state(original_image,memory,selected):
    setup(memory);put(memory,GRAY,1,2);memory[FADE]=64;put(memory,SPIN,0,2)
    memory[APP+0x77C]=memory[APP+0x77D]=1;put(memory,FLASH,501,2);put(memory,OVERRIDE,1,2)
    if selected!='gray':put(memory,GRAY,65535,2)
    if selected not in['gray','fade']:memory[FADE]=255
    if selected not in['gray','fade','random']:put(memory,SPIN,65535,2)
    if selected in['flash','space','surface']:memory[APP+0x77C]=0
    if selected in['space','surface']:put(memory,FLASH,65535,2)
    if selected=='surface':memory[APP+0x77D]=0
    before=[get(memory,a,2)for a in[SPIN,FLASH]]
    expected={'gray':0x777,'fade':converted(63>>3),'random':converted(rng(0x12345678,0xABCDEF01)[1]&4095),'inside':0x335,'flash':0x777,'space':converted(0x456),'surface':converted(atmospheric(memory,0,0,1))}[selected]
    assert palette(original_image,memory)==expected
    assert get(memory,GRAY,2)==(0 if selected=='gray'else 65535)
    assert memory[FADE]==(63 if selected=='fade'else 64 if selected=='gray'else 255)
    assert get(memory,SPIN,2)==before[0]
    assert get(memory,FLASH,2)==(500 if selected=='flash'else before[1])
    assert [get(memory,APP+o)for o in[0x60,0x64]]==list(rng(0x12345678,0xABCDEF01)if selected=='random'else(0x12345678,0xABCDEF01))
