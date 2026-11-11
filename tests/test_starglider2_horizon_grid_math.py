"""Original horizon/grid arithmetic with supplied vectors and canonical tables.

These cases retain signed index aliases and register high WORDs. They do not
establish a normal-game input domain, queue lifetime or display equivalence.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,STACK,RETURN
from tests.test_starglider2_radial_callers import offsets
from tests.test_starglider2_scene_packets import fields as scene_fields


def signed(v):return (v&65535)-65536 if v&32768 else v&65535

def swap(v):
    v&=0xFFFFFFFF
    return ((v<<16)|(v>>16))&0xFFFFFFFF


@pytest.mark.parametrize('angle',[0,1,1023,1024,2048,3072,4095,65535])
@pytest.mark.parametrize('xz',[(0,0),(1,-1),(-32768,32767),(32767,32767),(-32768,-32768),(1234,-5678)])
def test_grid_pair_rotation_retains_word_extraction_and_original_register_high_words(original_image,memory,offsets,angle,xz):
    m=memory;o=offsets
    put(m,APP+o['view_rotation_1'],angle,2)
    put(m,APP+o['sine_lookup_pointer'],0x13F60);put(m,APP+o['cosine_lookup_pointer'],0x14760)
    cpu=state(m,0x2F644);x,z=xz
    cpu.d[1]=0xA55A0000|(x&65535);cpu.d[3]=0xFEDC0000|(z&65535)
    d=list(cpu.d);a=list(cpu.a);app=bytes(m[APP:APP+0x800])
    phase=((-angle)&4095)*2;s=signed(get(m,0x13F60+phase,2));c=signed(get(m,0x14760+phase,2))
    first=swap(((s*z+c*x)&0xFFFFFFFF)<<2)
    second=swap(((c*z-s*x)&0xFFFFFFFF)<<2)
    run(original_image,m,cpu,{RETURN})
    expected=d[:];expected[0]=(d[0]&0xFFFF0000)|phase
    expected[1]=(d[1]&0xFFFF0000)|(first&65535)
    expected[3]=(d[3]&0xFFFF0000)|(second&65535)
    expected[4]=second;expected[5]=(s*x)&0xFFFFFFFF
    assert list(cpu.d)==expected
    assert cpu.a[0]==0x13F60 and cpu.a[1]==0x14760
    assert list(cpu.a[2:7])==a[2:7]and cpu.a[7]==STACK+4
    assert bytes(m[APP:APP+0x800])==app


@pytest.mark.parametrize('depths',[(0,1),(2,3),(0x7FFE,0x7FFF),(0x8000,0x8001),(0xFFFE,0xFFFF)])
@pytest.mark.parametrize('xy',[(1,2,3,4),(-32768,32767,32767,-32768),(0,0,0,0),(300,-400,-500,600)])
@pytest.mark.parametrize('origin',[(0,0),(159,79),(32767,65535)])
def test_horizon_projection_masks_only_depth_low_bit_and_keeps_signed_table_aliases(original_image,memory,offsets,depths,xy,origin):
    m=memory;o=offsets;raw=original_image[0]
    table=get(raw,0x2EF04-0x1000)
    put(m,APP+o['projection_screen_origin_x'],origin[0],2);put(m,APP+o['projection_screen_origin_y'],origin[1],2)
    cpu=state(m,0x2EF02)
    for reg,v in zip([1,2,4,5],xy):cpu.d[reg]=(cpu.d[reg]&0xFFFF0000)|(v&65535)
    cpu.d[3]=0xA55A0000|depths[0];cpu.d[6]=0xFEDC0000|depths[1]
    d=list(cpu.d);a=list(cpu.a);app=bytes(m[APP:APP+0x800])
    scales=[signed(get(m,table+signed(depth&65534),2))for depth in depths]
    p=[swap((signed(v)*scale)<<1)for v,scale in zip(xy,[scales[0]]*2+[scales[1]]*2)]
    expected=d[:];expected[1],expected[2]=p[:2]
    expected[3]=d[3]&0xFFFFFFFE
    for reg,hi,lo,add in [(4,p[2],p[0],origin[0]),(5,p[3],p[1],origin[1]),
                          (6,d[6],p[2],origin[0]),(7,d[7],p[3],origin[1])]:
        expected[reg]=(hi&0xFFFF0000)|((lo+add)&65535)
    run(original_image,m,cpu,{0x2F68A})
    assert list(cpu.d)==expected
    assert cpu.a[2]==table and [cpu.a[i]for i in[0,1,3,4,5,6,7]]==[a[i]for i in[0,1,3,4,5,6,7]]
    assert bytes(m[APP:APP+0x800])==app and get(m,STACK)==RETURN


@pytest.mark.parametrize('entry,mode',[(0x3A7A2,0),(0x3A868,1)])
@pytest.mark.parametrize('colour',range(16))
@pytest.mark.parametrize('top,bottom',[(0,0),(2,4),(4,3),(-1,1),(204,204),(32767,-32768),(-32768,32767)])
def test_alternate_background_rows_keep_packed_patterns_signed_address_wrap_and_inclusive_counts(original_image,memory,scene_fields,entry,mode,colour,top,bottom):
    m=memory;base=0x70000;lo,hi=base-0x9000,base+0x9000
    m[lo:hi]=b'\xA5'*(hi-lo);put(m,scene_fields['draw_buffer_base'],base)
    before=bytes(m[lo:hi]);expected=bytearray(before)
    cpu=state(m,entry);cpu.d[0]=0x12340000|colour
    cpu.d[3]=0xA55A0000|(top&65535);cpu.d[4]=0xFEDC0000|(bottom&65535)
    d=list(cpu.d);a=list(cpu.a);app=bytes(m[APP:APP+0x800])
    count=(bottom-top)&65535
    if count<32768:
        if mode==0:
            pair=((0xFFFF0000 if colour&1 else 0)|(65535 if colour&2 else 0)).to_bytes(4,'big')
            pair+=((0xFFFF0000 if colour&4 else 0)|(65535 if colour&8 else 0)).to_bytes(4,'big')
            end=base+signed(bottom*160+152)
            for row in range(count+1):
                start=end-160*row-144-lo;expected[start:start+144]=pair*18
        else:
            raw=original_image[0];body=raw[entry-4096:entry-4096+48]
            table=get(body,body.index(bytes.fromhex('41f9'))+2)
            for half in range(2):
                pattern=bytes(m[table+colour*8+half*4:table+colour*8+half*4+4])
                end=base+signed(bottom*160)+76+80*half
                for row in range(count+1):
                    start=end-160*row-72-lo;expected[start:start+72]=pattern*18
    run(original_image,m,cpu,{RETURN})
    assert bytes(m[lo:hi])==expected and bytes(m[APP:APP+0x800])==app
    assert cpu.a[6]==a[6]and cpu.a[7]==STACK+4
