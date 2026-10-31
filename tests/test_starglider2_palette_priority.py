"""Original palette priority/colour arithmetic and connected producer CPU paths.

Stop before the later audio continuation. Check Copper-list RAM only: not
scanout, Copper execution, DMA, timing, complete-frame or original-caller proof.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP
from tests.test_starglider2_scan_acquisition import signed16

GRAY,FADE,SPIN,FLASH,OVERRIDE=0x39CDE,0x39CD1,0x39CDA,0x39CCC,0x39CC4
BASE,OTHER,SHIFTS,RGB,SOLICE,RAMP=0x39654,0x39656,0x3996E,0x3994E,0x39746,0x4CBD4
COLOURS=[0xCF3A,0xD016,0xD0D2]
SENTINEL=0xA55A


def prepare(memory):
    for a in[GRAY,SPIN,FLASH]:put(memory,a,65535,2)
    memory[FADE]=255;memory[APP+0x77C]=memory[APP+0x77D]=0
    put(memory,OVERRIDE,0,2);put(memory,APP+0x830,0,2);put(memory,APP+0x708,0)
    put(memory,BASE,0x123,2);put(memory,OTHER,0x456,2);put(memory,SOLICE,0xABC,2)
    put(memory,APP+0x60,0x12345678);put(memory,APP+0x64,0xABCDEF01)
    for a in COLOURS:
        assert get(memory,a-2,2)==0x19E
        put(memory,a,SENTINEL,2)


def palette(image,memory):
    before={a:bytes(memory[a-4:a+6])for a in COLOURS}
    cpu=state(memory,0x4C78E);run(image,memory,cpu,{0x4CAC0})
    for a in COLOURS:
        assert bytes(memory[a-4:a])==before[a][:4] and bytes(memory[a+2:a+6])==before[a][6:]
    return cpu


def colour(memory,value):assert [get(memory,a,2)for a in COLOURS]==[value]*3


def rng(a,b):
    rotated=((a<<3)|(a>>29))&0xFFFFFFFF
    return b,(rotated&0xFFFF0000)|((((rotated&65535)-7)&65535)^(b&65535))


@pytest.mark.parametrize('route',['gray','gray_expiry','fade','fade_expiry','random','inside','flash','space','surface'])
def test_first_priority_branch_suppresses_all_lower_effects(original_image,memory,route):
    prepare(memory);put(memory,GRAY,1,2);memory[FADE]=64;put(memory,SPIN,0,2)
    memory[APP+0x77C]=1;put(memory,FLASH,501,2);memory[APP+0x77D]=1;put(memory,OVERRIDE,1,2)
    if route not in['gray','gray_expiry']:put(memory,GRAY,65535,2)
    if route=='gray_expiry':put(memory,GRAY,0,2)
    if route not in['gray','gray_expiry','fade','fade_expiry']:memory[FADE]=255
    if route=='fade_expiry':memory[FADE]=0
    if route in['inside','flash','space','surface']:put(memory,SPIN,65535,2)
    if route in['flash','space','surface']:memory[APP+0x77C]=0
    if route in['space','surface']:put(memory,FLASH,65535,2)
    if route=='surface':memory[APP+0x77D]=0
    initial=[get(memory,a,2)for a in[GRAY,SPIN,FLASH]];f=memory[FADE]
    cpu=palette(original_image,memory)
    expected={'gray':0xFFF,'gray_expiry':SENTINEL,'fade':7,'fade_expiry':SENTINEL,
              'random':rng(0x12345678,0xABCDEF01)[1]&4095,'inside':0x66A,
              'flash':0xFFF,'space':0x456,'surface':0xFFA}[route]
    colour(memory,expected)
    assert get(memory,GRAY,2)==(0 if route=='gray'else 65535 if route=='gray_expiry'else initial[0])
    assert memory[FADE]==(63 if route=='fade'else 255 if route=='fade_expiry'else f)
    assert get(memory,SPIN,2)==initial[1]
    assert get(memory,FLASH,2)==(500 if route=='flash'else initial[2])
    assert [get(memory,APP+o)for o in[0x60,0x64]]==list(rng(0x12345678,0xABCDEF01)if route=='random'else(0x12345678,0xABCDEF01))


@pytest.mark.parametrize('count',range(18))
def test_grayscale_decrements_before_unchecked_word_lookup_and_expiry_keeps_colour(original_image,memory,count):
    prepare(memory);put(memory,GRAY,count,2)
    expected=SENTINEL if count==0 else get(memory,RAMP+2*(count-1),2)
    palette(original_image,memory);colour(memory,expected)
    assert get(memory,GRAY,2)==(count-1)&65535
    # Counts17/18 deliberately read beyond the stored16-WORD prefix, not a caller bound.


@pytest.mark.parametrize('count',[0,1,7,8,63,64,126,127])
def test_byte_fade_expiry_has_no_fallback_and_other_steps_write_low_blue_bits(original_image,memory,count):
    prepare(memory);memory[FADE]=count;put(memory,FLASH,501,2)
    palette(original_image,memory);colour(memory,SENTINEL if count==0 else(count-1)>>3)
    assert memory[FADE]==(count-1)&255 and get(memory,FLASH,2)==501


@pytest.mark.parametrize('count',[0,1,2,3,479,480,481,482,499,500,501,502,32767])
@pytest.mark.parametrize('space',[0,1])
@pytest.mark.parametrize('override',[0,65535])
def test_flash_odd_steps_use_space_words_even_on_surface_and_thresholds_follow_decrement(original_image,memory,count,space,override):
    prepare(memory);put(memory,FLASH,count,2);memory[APP+0x77D]=space;put(memory,OVERRIDE,override,2)
    left=(count-1)&65535
    expected=(0x456 if override else 0x123)if left&1 else 0xFFF if left>=500 else 0xF07 if left>=480 else(left<<3)&0xF00
    palette(original_image,memory);colour(memory,expected)
    assert get(memory,FLASH,2)==left


@pytest.mark.parametrize('inside',[1,128,255])
@pytest.mark.parametrize('override',[0,1,32768,65535])
def test_any_nonzero_inside_flag_preempts_flash_and_uses_override_word_truth(original_image,memory,inside,override):
    prepare(memory);memory[APP+0x77C]=inside;put(memory,OVERRIDE,override,2);put(memory,FLASH,501,2)
    palette(original_image,memory);colour(memory,0x66A if override else 0x224)
    assert get(memory,FLASH,2)==501


def atmospheric(memory,body,y,override):
    shift=memory[SHIFTS+signed16(body)]&63
    height=((-y)&0xFFFFFFFF)>>shift
    base=get(memory,RGB+signed16(2*body),2)if override else get(memory,SOLICE,2)
    result=0
    for bit in[0,4,8]:
        v=(((base>>bit)&15)-(height&65535))&65535
        result|=(0 if v&32768 else v&15)<<bit
    return result


@pytest.mark.parametrize('body',range(16))
@pytest.mark.parametrize('override',[0,1])
@pytest.mark.parametrize('y',[0,-1,-8192,-131072,1,0x7FFFFFFF,0x80000000,0xFFFF0000])
def test_atmosphere_uses_logical_long_height_then_word_sign_clipping_and_nibble_masks(original_image,memory,body,override,y):
    prepare(memory);put(memory,APP+0x830,body,2);put(memory,APP+0x708,y&0xFFFFFFFF);put(memory,OVERRIDE,override,2)
    expected=atmospheric(memory,body,y,override)
    palette(original_image,memory);colour(memory,expected)


@pytest.mark.parametrize('body',[16,65535])
def test_table_prefix_is_not_a_universal_world_selector_domain(original_image,memory,body):
    prepare(memory);put(memory,APP+0x830,body,2);put(memory,APP+0x708,0xFFFF0000);put(memory,OVERRIDE,1,2)
    expected=atmospheric(memory,body,0xFFFF0000,1)
    palette(original_image,memory);colour(memory,expected)


@pytest.mark.parametrize('seed_a',[0,1,0x12345678,0x80000000,0xFFFFFFFF])
@pytest.mark.parametrize('seed_b',[0,1,0xFFFF0000,0xABCDEF01,0xFFFFFFFF])
def test_random_priority_executes_original_word_xor_and_preserves_d1(original_image,memory,seed_a,seed_b):
    prepare(memory);put(memory,SPIN,0,2);put(memory,APP+0x60,seed_a);put(memory,APP+0x64,seed_b)
    expected_a,expected_b=rng(seed_a,seed_b);cpu=palette(original_image,memory)
    colour(memory,expected_b&4095)
    assert get(memory,APP+0x60)==expected_a and get(memory,APP+0x64)==expected_b
    assert cpu.d[1]==0x12340001


@pytest.mark.parametrize('producer,index_base,stop',[(0x3334C,0x39658,0x3336C),(0x33468,0x39670,0x33488)])
@pytest.mark.parametrize('index',range(24))
@pytest.mark.parametrize('override',[0,1])
def test_proximity_colour_byte_producers_feed_original_space_consumer(original_image,memory,producer,index_base,stop,index,override):
    prepare(memory);value=memory[index_base+index]<<4
    cpu=state(memory,producer);cpu.d[0]=index;run(original_image,memory,cpu,{stop})
    assert get(memory,BASE,2)==value and get(memory,OTHER,2)==value|0x4C
    memory[APP+0x77D]=1;put(memory,OVERRIDE,override,2)
    palette(original_image,memory);colour(memory,value|0x4C if override else value)
    # Enter after proximity/index guards; stored24-byte prefixes do not prove those guards.


@pytest.mark.parametrize('override',[0,1])
def test_proximity_default_pair_feeds_space_consumer(original_image,memory,override):
    prepare(memory);run(original_image,memory,state(memory,0x3350C),{0x3351C})
    assert get(memory,BASE,2)==0 and get(memory,OTHER,2)==0x27
    memory[APP+0x77D]=255;put(memory,OVERRIDE,override,2)
    palette(original_image,memory);colour(memory,0x27 if override else 0)
