"""Original heading CPU paths with supplied RAM, not hardware scanout proof.

The reference treats each stored stream as a 128-bit bitstring. It does not
repeat the original split LONG/WORD extraction algorithm. Cache state persists
through the 4096-input sequence; separate fixtures retain the initial collision.
"""
import pytest

from tests.test_starglider2_text_editor import (
    original_image, memory, state, run, put, get, APP, STACK, RETURN,
)

STRIP,BEGIN,END=0xE004,0x68000,0x80000
MODES={
    'amiga':(0xD906,0xDA00,0xD966,[0x71506]),
    'mode0':(0x3CD46,0x3CF1E,0x3CDB4,[0x6D418,0x75418,0x7D418]),
    'mode1':(0x3D410,0x3CF1E,0x3D482,[0x6D3EC,0x753EC,0x7D3EC]),
}


def sample_for(angle):
    return ((((-angle)&4095)*32//365)&511)>>2


def double_nibble(value):
    return sum(((value>>bit)&1)*3<<(2*bit)for bit in range(4))


def expected_pixels(memory,mode,sample):
    streams=[int.from_bytes(bytes(memory[STRIP+16*i:STRIP+16*(i+1)]),'big')for i in range(8)]
    selected=[(value>>(96-sample))&0xFFFFFFFF for value in streams]
    rows=[(selected[0],selected[0]),(selected[1],selected[2]),(selected[3],selected[4]),
          (selected[5],selected[6]),(selected[7],selected[7])]
    output=bytearray(b'\xA5'*(END-BEGIN))
    def store(address,value,width):output[address-BEGIN:address-BEGIN+width]=value.to_bytes(width,'big')
    for anchor in MODES[mode][3]:
        for row,(plane2,plane3)in enumerate(rows):
            if mode=='amiga':
                store(anchor+0x4000+40*row,plane2,4);store(anchor+0x6000+40*row,plane3,4)
            elif mode=='mode0':
                for plane,value in enumerate([plane2,plane3]):
                    store(anchor+160*row+4+2*plane,value>>16,2)
                    store(anchor+160*row+12+2*plane,value&0xFFFF,2)
            else:
                value=plane2|plane3
                expanded=bytes(double_nibble((value>>shift)&15)for shift in range(28,-1,-4))
                for vertical in [0,80]:
                    start=anchor-BEGIN+160*row+vertical;output[start:start+8]=expanded
    return output


@pytest.mark.parametrize('mode',MODES)
def test_all_4096_heading_inputs_with_persistent_caches_and_three_output_encodings(original_image,memory,mode):
    entry,cache,read,_=MODES[mode];memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    assert get(memory,cache,2)==get(memory,cache+2,2)==0xFFFF
    strip=bytes(memory[STRIP:STRIP+128]);frames={};samples=set();repaints=[]
    for angle in range(4096):
        put(memory,APP+0x746,angle,2);sample=sample_for(angle);samples.add(sample)
        cpu=state(memory,entry);old_d,old_a=list(cpu.d),list(cpu.a)
        def observe(pc):
            if pc==read:
                coarse,shift=cpu.d[0],cpu.d[1]
                assert (cpu.a[1],coarse,shift,cpu.d[4])==(STRIP,2*(sample>>4),sample&15,16-(sample&15))
                assert 0<=coarse<=10 and all(16*r+coarse+6<=128 for r in range(8))
                repaints.append(sample)
        run(original_image,memory,cpu,{RETURN},observe)
        assert (get(memory,cache,2),get(memory,cache+2,2))==((-angle)&0xFFFF,sample)
        if sample not in frames:frames[sample]=expected_pixels(memory,mode,sample)
        assert bytes(memory[BEGIN:END])==frames[sample],(mode,angle,sample)
        assert cpu.a[7]==STACK+4
        if mode=='mode1':assert list(cpu.d)==old_d and list(cpu.a)[:7]==old_a[:7]
    assert samples==set(range(90)) and len(repaints)==91
    assert bytes(memory[STRIP:STRIP+128])==strip


@pytest.mark.parametrize('mode',MODES)
def test_initial_ffff_cache_collides_with_original_rotation_one(original_image,memory,mode):
    entry,cache,_,_=MODES[mode];memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    put(memory,APP+0x746,1,2);cpu=state(memory,entry)
    run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[BEGIN:END])==b'\xA5'*(END-BEGIN)
    assert get(memory,cache,2)==get(memory,cache+2,2)==0xFFFF
    # Supplied first-call angle, not an assertion about the actual game startup.


@pytest.mark.parametrize('mode',MODES)
def test_raw_cache_hit_does_not_repair_a_stale_second_cache(original_image,memory,mode):
    entry,cache,_,_=MODES[mode];memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    put(memory,APP+0x746,27,2);put(memory,cache,(-27)&0xFFFF,2);put(memory,cache+2,0xBEEF,2)
    cpu=state(memory,entry);run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[BEGIN:END])==b'\xA5'*(END-BEGIN) and get(memory,cache+2,2)==0xBEEF


@pytest.mark.parametrize('mode',MODES)
def test_masked_alias_updates_raw_cache_but_keeps_same_sample_pixels(original_image,memory,mode):
    entry,cache,_,_=MODES[mode];memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    for angle in [0,0x1000]:
        put(memory,APP+0x746,angle,2);cpu=state(memory,entry);run(original_image,memory,cpu,{RETURN})
        assert bytes(memory[BEGIN:END])==expected_pixels(memory,mode,0)
    assert (get(memory,cache,2),get(memory,cache+2,2))==(0xF000,0)


@pytest.mark.parametrize('mode',MODES)
def test_sampling_uses_current_bitmap_ram_without_an_immutability_assumption(original_image,memory,mode):
    entry,_,_,_=MODES[mode];memory[BEGIN:END]=b'\xA5'*(END-BEGIN)
    put(memory,APP+0x746,0,2);cpu=state(memory,entry);run(original_image,memory,cpu,{RETURN})
    put(memory,STRIP+124,0x1234ABCD)
    put(memory,APP+0x746,1,2);cpu=state(memory,entry);run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[BEGIN:END])==expected_pixels(memory,mode,89)
    # The original queue's count-zero predecessor aliases this last LONG.


def test_alternate_modes_share_cache_without_a_promised_mode_change_reset(original_image,memory):
    memory[BEGIN:END]=b'\xA5'*(END-BEGIN);put(memory,APP+0x746,0,2)
    cpu=state(memory,MODES['mode0'][0]);run(original_image,memory,cpu,{RETURN})
    before=bytes(memory[BEGIN:END]);cpu=state(memory,MODES['mode1'][0])
    run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[BEGIN:END])==before
    # Direct function transition only; real mode-switch/reset paths are not qualified.


@pytest.mark.parametrize('pattern',[n*0x11111111 for n in range(16)]+[0x01234567])
def test_double_pixel_helper_nibble_order_replication_and_preserved_registers(original_image,memory,pattern):
    memory[BEGIN:END]=b'\xA5'*(END-BEGIN);anchors=MODES['mode1'][3]
    assert bytes(memory[0x3D56C:0x3D57C])==bytes(double_nibble(n)for n in range(16))
    cpu=state(memory,0x3D518);cpu.a[0],cpu.a[2],cpu.a[3]=anchors;cpu.d[2]=pattern;cpu.d[3]=0
    old=(cpu.d[0],cpu.d[4],cpu.a[1]);expected=bytearray(memory[BEGIN:END])
    expanded=bytes(double_nibble((pattern>>shift)&15)for shift in range(28,-1,-4))
    for anchor in anchors:
        for vertical in [0,80]:
            start=anchor-BEGIN+vertical;expected[start:start+8]=expanded
    run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[BEGIN:END])==expected
    assert (cpu.d[0],cpu.d[4],cpu.a[1])==old and cpu.a[7]==STACK+4
    assert (cpu.a[0],cpu.a[2],cpu.a[3])==tuple(x+160 for x in anchors)
    assert cpu.d[2]==((pattern<<4)|(pattern>>28))&0xFFFFFFFF and cpu.d[3]==0xFFFF
