"""Original contact eligibility and bounded common player-response CPU paths.

Records/list backing and table reads are supplied; no universal selector bounds,
complete special handlers, contact lifecycle or hardware/gameplay proof follows.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK, RETURN
from tests.test_starglider2_scan_acquisition import signed16
from tests.test_starglider2_homing_updates import signed32

OUTER,INNER,LIST=INPUT+0x200,INPUT+0x300,INPUT+0x500
H,NEG,POS=0x17058,0x1712A,0x171FC


def setup(memory,outer_type=2,inner_type=1,outer_flags=0,inner_flags=0,outer_phase=255,inner_phase=255,scale=3,x=0,z=0,y=0):
    for a,t,f,p in [(OUTER,outer_type,outer_flags,outer_phase),(INNER,inner_type,inner_flags,inner_phase)]:
        memory[a:a+68]=b'\0'*68;put(memory,a,t,2);memory[a+2]=f;memory[a+30]=p;memory[a+29]=scale
    put(memory,OUTER+50,x&65535,2);put(memory,OUTER+54,z&65535,2);put(memory,OUTER+8,y&0xFFFFFFFF)
    put(memory,LIST,OUTER);put(memory,LIST+4,INNER);put(memory,APP+0x6D0,LIST);put(memory,APP+0x762,2,2)
    put(memory,0x27A8,APP)


def geometry(memory,outer_type,inner_type,scale,x,z,y):
    shift=scale&63
    def word(table,t):return get(memory,table+signed16(2*t),2)
    def horizontal(t):return word(H,t)>>shift if shift<16 else 0
    def vertical(table,t):return(signed16(word(table,t))&0xFFFFFFFF)>>shift if shift<32 else 0
    radius=signed16(horizontal(outer_type)+horizontal(inner_type))
    def absword(v):
        v=signed16(v);return signed16(-v)if v<0 else v
    if absword(x)>radius or absword(z)>radius:return False
    dy=signed32(y)
    if dy<0:dy=signed32(-dy);height=(vertical(NEG,inner_type)+vertical(POS,outer_type))&0xFFFFFFFF
    else:height=(vertical(POS,inner_type)+vertical(NEG,outer_type))&0xFFFFFFFF
    return dy<=signed32(height)


def eligible(image,memory):
    cpu=state(memory,0xB55C);run(image,memory,cpu,{0xB670,0xB8F8,0xB8FC})
    return cpu


@pytest.mark.parametrize('axis',['x','z','y'])
@pytest.mark.parametrize('delta',[-1,0,1])
@pytest.mark.parametrize('sign',[-1,1])
def test_inclusive_extent_edges_retain_signed_y_side_selection(original_image,memory,axis,delta,sign):
    setup(memory)
    radius=(get(memory,H+4,2)>>3)+(get(memory,H+2,2)>>3)
    height=((get(memory,NEG+2,2)>>3)+(get(memory,POS+4,2)>>3))if sign<0 else((get(memory,POS+2,2)>>3)+(get(memory,NEG+4,2)>>3))
    values=dict(x=0,z=0,y=0);values[axis]=sign*((height if axis=='y'else radius)+delta)
    setup(memory,**values);expected=geometry(memory,2,1,3,**values)
    cpu=eligible(original_image,memory);assert(cpu.pc==0xB670)==expected
    assert cpu.a[6]==POS


@pytest.mark.parametrize('scale',[0,1,15,16,31,32,63,64])
@pytest.mark.parametrize('extent',[1,32767,65535])
def test_extent_word_sum_and_logical_long_shift_are_not_normalized(original_image,memory,scale,extent):
    setup(memory,scale=scale)
    for table in [H,NEG,POS]:
        for type_ in [1,2]:put(memory,table+2*type_,extent,2)
    expected=geometry(memory,2,1,scale,0,0,0)
    cpu=eligible(original_image,memory);assert(cpu.pc==0xB670)==expected


@pytest.mark.parametrize('axis',['x','z','y'])
@pytest.mark.parametrize('value',[-32768,32767,-0x80000000,0x7FFFFFFF])
def test_wrapped_absolute_separation_preserves_minimum_values(original_image,memory,axis,value):
    values=dict(x=0,z=0,y=0);values[axis]=value
    setup(memory,scale=0,**values);expected=geometry(memory,2,1,0,**values)
    cpu=eligible(original_image,memory);assert(cpu.pc==0xB670)==expected


@pytest.mark.parametrize('side',['outer','inner'])
@pytest.mark.parametrize('phase',[0,127,128,255])
@pytest.mark.parametrize('flags',[0,8])
def test_flag3_bypasses_nonnegative_phase_gate(original_image,memory,side,phase,flags):
    setup(memory,**{side+'_phase':phase,side+'_flags':flags})
    cpu=eligible(original_image,memory)
    assert(cpu.pc==0xB670)==bool(flags&8 or phase&128)


@pytest.mark.parametrize('inner_type',[95,128,145])
def test_inner_extent_read_precedes_later_tag_filter(original_image,memory,inner_type):
    setup(memory,inner_type=inner_type,scale=0)
    cpu=state(memory,0xB55C);run(original_image,memory,cpu,{0xB5DA})
    assert cpu.d[1]&65535==get(memory,H+2*inner_type,2)
    # 145 reads beyond the horizontal owner into adjacent original bytes. This
    # is access evidence, not a promoted owner/domain or safe normal-game claim.
    run(original_image,memory,cpu,{0xB8F8,0xB8FC,0xB670});assert cpu.pc!=0xB670


@pytest.mark.parametrize('count',[0,1,2,3,32768,65535])
def test_pair_count_prefix_uses_wrapped_word_n_flag(original_image,memory,count):
    setup(memory);put(memory,APP+0x762,count,2)
    put(memory,APP+0x6C2,0xABCD,2);memory[APP+0xBBA]=255;memory[APP+0x7CF]=4
    cpu=state(memory,0xB55C);run(original_image,memory,cpu,{RETURN,0xB57E})
    assert cpu.pc==(RETURN if((count-2)&65535)&32768 else 0xB57E)
    assert get(memory,APP+0x6C2,2)==0 and memory[APP+0xBBA]==0
    assert memory[APP+0x7CF]==4


def player_setup(memory,side,kind,durability=1,marker=0,inside=0,space=0,steps=0,actor=30):
    setup(memory);player,other=(OUTER,INNER)if side=='outer'else(INNER,OUTER)
    put(memory,player,actor,2);put(memory,other,kind,2)
    memory[other+28]=durability;memory[other+34]=marker;memory[other+30]=255;memory[other+2]=0x28
    memory[APP+0x77C]=inside;memory[APP+0x77D]=space;memory[APP+0x7CF]=steps
    memory[APP+0x7CE]=0;memory[APP+0x7E4]=255;put(memory,APP+0x6F0,0xFFFFFFFF);put(memory,APP+0x6D8,0x1234,2)
    return player,other


def response(image,memory,side):
    cpu=state(memory,0xB92E if side=='outer'else 0xB926);cpu.a[0]=OUTER;cpu.a[2]=INNER;cpu.a[6]=POS
    before_d,before_a=list(cpu.d),list(cpu.a)
    run(image,memory,cpu,{0xB8F8})
    assert list(cpu.d)==before_d and list(cpu.a)==before_a
    return cpu


@pytest.mark.parametrize('side',['outer','inner'])
@pytest.mark.parametrize('kind',[2,12,84,91,98,103])
@pytest.mark.parametrize('marker',[0,255])
@pytest.mark.parametrize('durability',[0,1,128,255])
def test_player_hit_or_type_marker_suppression_restores_borrowed_context(original_image,memory,side,kind,marker,durability):
    _,other=player_setup(memory,side,kind,durability,marker)
    response(original_image,memory,side)
    hit=kind!=91 and(kind==2 or not marker)
    assert get(memory,APP+0x6F0)==(0 if hit else 0xFFFFFFFF)
    assert get(memory,APP+0x6D8,2)==(kind if hit else 0x1234)
    assert memory[other+30]==(0 if hit and durability<128 else 255)
    assert memory[other+2]==(0x20 if hit and durability<128 else 0x28)
    assert memory[other+28]==durability and memory[APP+0x7E4]==0
    assert memory[APP+0x7CF]==(4 if hit and durability>=128 else 0)
    assert memory[APP+0x7CE]==(255 if hit and durability>=128 else 0)


@pytest.mark.parametrize('kind',[2,84])
@pytest.mark.parametrize('inside',[0,1])
@pytest.mark.parametrize('space',[0,1])
@pytest.mark.parametrize('steps',[0,1,255])
def test_solid_player_response_requires_surface_outside_and_idle_counter(original_image,memory,kind,inside,space,steps):
    player_setup(memory,'outer',kind,128,inside=inside,space=space,steps=steps)
    response(original_image,memory,'outer')
    hit=kind==84 or not inside
    started=hit and not inside and not space and not steps
    assert get(memory,APP+0x6F0)==(0 if hit else 0xFFFFFFFF)
    assert memory[APP+0x7CF]==(4 if started else steps)and memory[APP+0x7CE]==(255 if started else 0)


@pytest.mark.parametrize('durability',[0,1,2,127,128,255])
def test_nonplayer_common_response_retains_zero_to_ff_durability_wrap(original_image,memory,durability):
    player,other=player_setup(memory,'outer',2,durability,actor=90)
    memory[player+30]=255;response(original_image,memory,'outer')
    active=durability<128;result=(durability-1)&255
    assert memory[other+28]==(result if active else durability)
    assert memory[other+30]==(0 if active and result==0 else 255)
    assert memory[player+30]==(0 if active else 255)
    assert memory[other+2]==(0x20 if active else 0x28)


@pytest.mark.parametrize('kind,target',[(90,0xC32C),(93,0xC1DA),(65,0xBD72),(63,0xBD90),(48,0xBECC)])
def test_special_handlers_remain_explicit_unexecuted_handoffs(original_image,memory,kind,target):
    player_setup(memory,'outer',kind)
    cpu=state(memory,0xB92E);cpu.a[0]=OUTER;cpu.a[2]=INNER;cpu.a[6]=POS
    run(original_image,memory,cpu,{target})
    assert cpu.a[6]==APP and cpu.a[7]==STACK-60


@pytest.mark.parametrize('steps',[0,1,2,4,128,255])
@pytest.mark.parametrize('inside',[0,1])
def test_response_counter_ages_per_contact_pass_not_physical_frame(original_image,memory,steps,inside):
    setup(memory);memory[APP+0x7CF]=steps;memory[APP+0x7CE]=255;memory[APP+0x77C]=inside;memory[APP+0x7E4]=255
    cpu=state(memory,0xB8FC);cpu.d[7]=0;cpu.a[6]=POS
    run(original_image,memory,cpu,{RETURN,0xBA14})
    value=(steps-1)&255 if steps else 0
    assert memory[APP+0x7CF]==value and memory[APP+0x7CE]==(0 if not value or value&128 else 255)
    assert cpu.pc==(0xBA14 if inside else RETURN)
    assert memory[APP+0x7E4]==(255 if inside else 0)


def test_complete_two_record_pass_ages_new_solid_response_immediately(original_image,memory):
    player_setup(memory,'outer',2,128)
    cpu=state(memory,0xB55C);run(original_image,memory,cpu,{RETURN})
    assert memory[APP+0x7CF]==3 and memory[APP+0x7CE]==255
    assert get(memory,APP+0x6F0)==0 and get(memory,APP+0x6D8,2)==2
    assert memory[INNER+30]==255 and memory[APP+0x7E4]==0 and cpu.a[6]==APP
