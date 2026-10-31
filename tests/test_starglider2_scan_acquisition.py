"""Original scan selectors and aim consumers with supplied records/profile state.

These are CPU fixtures, not normal-game input/lifetime proofs. Extent/scale reads
use current RAM; no universal104-entry, positive-depth or valid-lock contract is
introduced. Projectile cases stop before allocation or the error-message body.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK, RETURN

LIST,OBJECT,OLD=INPUT,INPUT+0x200,INPUT+0x800
REF,TYPE,DEPTH,SX,SY=0x6B0,0x840,0x846,0x7D0,0x7D2
LOOKUP,HORIZONTAL,VERTICAL=0x2ADF8,0x17058,0x1712A
ENTRIES={'identity':0x73F6,'saved_frame':0x372F8}


def signed16(n):return (n+32768)%65536-32768


def project(word,factor):return signed16((signed16(word)*signed16(factor)*2)>>16)


def inside(delta,radius):
    # Original BPL tests subtraction's N, not N xor V or a mathematical abs.
    return signed16(delta-radius)<0 and signed16(signed16(-delta)-radius)<0


def record(type_=2,x=0,y=0,z=512,scale=3,flags=0,phase=255,cx=0,cy=0,radius=20):
    return dict(type=type_,x=x,y=y,z=z,scale=scale,flags=flags,phase=phase,cx=cx,cy=cy,radius=radius)


def setup(memory,records,aim=(160,80)):
    put(memory,APP+0x6CC,LIST);put(memory,APP+0x194,160,2);put(memory,APP+0x196,80,2)
    put(memory,APP+0x766,aim[0]&0xFFFF,2);put(memory,APP+0x768,aim[1]&0xFFFF,2)
    put(memory,APP+REF,OLD);put(memory,APP+TYPE,77,2);put(memory,APP+DEPTH,0x2468,2)
    put(memory,APP+SX,0x1111,2);put(memory,APP+SY,0x2222,2)
    for i,r in enumerate(records):
        a=OBJECT+96*i;put(memory,LIST+4*i,a);put(memory,a,r['type']&0xFFFF,2)
        memory[a+2]=r['flags'];memory[a+29]=r['scale'];memory[a+30]=r['phase']
        for off,k in [(22,'x'),(24,'y'),(26,'z'),(38,'cx'),(40,'cy'),(42,'radius')]:put(memory,a+off,r[k]&0xFFFF,2)


def reference(memory,variant,records,aim):
    result=[0,0,0x1111,0x2222,0x7FFF]if variant=='identity'else[77,OLD,0x1111,0x2222,0x7FFF]
    for i,r in enumerate(records):
        t=r['type']&0xFFFF;z=signed16(r['z'])
        if r['flags']&64 or not r['phase']&128:continue
        if variant=='identity':
            if t in [30,12,84,72,103,25]or z<=0:continue
        else:
            if t&128 or t in [30,84,72,103]or(t==12 and not r['flags']&128)or z==0:continue
        if z>signed16(result[4]):continue
        depth=z&0xFFFE;factor=get(memory,LOOKUP+signed16(depth),2)
        if variant=='identity'and t&128:
            x,y=signed16(r['cx']+160),signed16(r['cy']+80);rx=ry=signed16(r['radius'])
        else:
            x,y=signed16(project(r['x'],factor)+160),signed16(project(r['y'],factor)+80)
            extents=[get(memory,HORIZONTAL+signed16(2*t),2),get(memory,VERTICAL+signed16(2*t),2)]
            shift=r['scale']&63
            shifted=[signed16(v)>>shift for v in extents]if variant=='identity'else[v>>shift if shift<16 else 0 for v in extents]
            rx,ry=[project(v,factor)for v in shifted]
        if inside(signed16(aim[0]-x),rx)and inside(signed16(aim[1]-y),ry):
            result=[t,OBJECT+96*i,x&0xFFFF,y&0xFFFF,depth]
    return tuple(result)


def check(image,memory,variant,records,aim=(160,80)):
    expected=reference(memory,variant,records,aim)
    cpu=state(memory,ENTRIES[variant]);cpu.d[7]=len(records);old_a=list(cpu.a)
    run(image,memory,cpu,{RETURN})
    actual=(get(memory,APP+TYPE,2),get(memory,APP+REF),get(memory,APP+SX,2),get(memory,APP+SY,2),get(memory,APP+DEPTH,2))
    assert actual==expected and cpu.a[7]==STACK+4 and cpu.d[7]&0xFFFF==0xFFFF
    if variant=='saved_frame':assert list(cpu.a)[:6]==old_a[:6]
    return actual


@pytest.mark.parametrize('variant',ENTRIES)
@pytest.mark.parametrize('type_',[1,12,25,30,72,84,103,128])
@pytest.mark.parametrize('flags',[0,64,128])
def test_distinct_type_filters_flag_gates_and_radial_cached_geometry(original_image,memory,variant,type_,flags):
    records=[record(type_=type_,flags=flags)];setup(memory,records);check(original_image,memory,variant,records)


@pytest.mark.parametrize('variant',ENTRIES)
@pytest.mark.parametrize('phase',[0,127,128,255])
def test_retirement_sign_gate_keeps_type_and_reference_miss_distinctions(original_image,memory,variant,phase):
    records=[record(phase=phase)];setup(memory,records);check(original_image,memory,variant,records)


@pytest.mark.parametrize('variant',ENTRIES)
@pytest.mark.parametrize('axis',[0,1])
@pytest.mark.parametrize('edge',[-1,0,1,2,3,4,5])
def test_strict_extent_edges_use_stored_aim_not_renderer_clamping(original_image,memory,variant,axis,edge):
    r=record();factor=get(memory,LOOKUP+512,2);source=(HORIZONTAL if axis==0 else VERTICAL)+4
    radius=project(get(memory,source,2)>>3,factor)
    delta=[-radius-1,-radius,-radius+1,0,radius-1,radius,radius+1][edge+1]
    aim=[160,80];aim[axis]+=delta;records=[r];setup(memory,records,aim)
    actual=check(original_image,memory,variant,records,aim)
    assert (actual[1]==OBJECT)==(-radius<delta<radius)


@pytest.mark.parametrize('variant',ENTRIES)
@pytest.mark.parametrize('depths',[(200,200),(201,201),(200,201),(201,200),(512,256),(1,1)])
def test_evenized_depth_limit_preserves_ties_and_odd_depth_ordering(original_image,memory,variant,depths):
    records=[record(z=z)for z in depths];setup(memory,records)
    result=check(original_image,memory,variant,records)
    expected_index=0 if depths in [(201,201),(200,201),(1,1)]else 1
    assert result[1]==OBJECT+96*expected_index


@pytest.mark.parametrize('variant',ENTRIES)
@pytest.mark.parametrize('z',[-32768,-513,-1,0,1])
def test_depth_variants_do_not_gain_a_shared_positive_domain(original_image,memory,variant,z):
    records=[record(z=z)];setup(memory,records);check(original_image,memory,variant,records)


@pytest.mark.parametrize('variant',ENTRIES)
@pytest.mark.parametrize('shift',[0,1,15,16,31,32,63,64])
def test_extent_shift_width_and_register_count_are_not_unified(original_image,memory,variant,shift):
    records=[record(scale=shift)];setup(memory,records)
    put(memory,HORIZONTAL+4,0xFFFF,2);put(memory,VERTICAL+4,0xFFFF,2)
    check(original_image,memory,variant,records)


def test_radial_identity_uses_cached_center_and_radius_not_projected_relative_x(original_image,memory):
    records=[record(type_=128,x=20000,y=-1234,cx=0,cy=0,radius=5)];setup(memory,records)
    assert check(original_image,memory,'identity',records)[1]==OBJECT


@pytest.mark.parametrize('variant',ENTRIES)
def test_miss_resets_only_the_fields_written_by_that_selector(original_image,memory,variant):
    records=[record(flags=64)];setup(memory,records)
    assert check(original_image,memory,variant,records)==((0,0,0x1111,0x2222,0x7FFF)if variant=='identity'else(77,OLD,0x1111,0x2222,0x7FFF))


@pytest.mark.parametrize('z',[-513,-1,0,1,512])
def test_locked_pointer_projection_does_not_revalidate_type_phase_or_positive_depth(original_image,memory,z):
    r=record(type_=30,x=123,y=-456,z=z,phase=0,flags=64);setup(memory,[r]);put(memory,APP+REF,OBJECT)
    cpu=state(memory,0x76D4);run(original_image,memory,cpu,{RETURN})
    expected=(0x1111,0x2222)if z==0 else tuple((project(v,get(memory,LOOKUP+signed16(z&0xFFFE),2))+origin)&0xFFFF for v,origin in [(123,160),(-456,80)])
    assert (get(memory,APP+SX,2),get(memory,APP+SY,2))==expected
    assert get(memory,APP+TYPE,2)==77 and get(memory,APP+REF)==OBJECT and get(memory,APP+DEPTH,2)==0x2468


@pytest.mark.parametrize('type_',[84,103])
@pytest.mark.parametrize('energy',[0,1,255,256,511,512,65535])
@pytest.mark.parametrize('free',[0,2])
def test_aim_snapshot_and_energy_spending_precede_failed_slot_reserve(original_image,memory,type_,energy,free):
    # Supplied already-loaded projectile profile, no assertion about the copy/selection path.
    put(memory,0x7EC0,type_,2);put(memory,0x7ECE,14,2);put(memory,APP+0x794,energy,2)
    put(memory,APP+0x772,free,2);put(memory,APP+0x6D4,0x87654)
    put(memory,APP+0x766,0xFF80,2);put(memory,APP+0x768,0xFFFF,2)
    put(memory,APP+0x76E,0xCAFE,2);put(memory,APP+0x770,0xBEEF,2);put(memory,APP+0x6DC,0xFFFFFFFF)
    cpu=state(memory,0x7256);run(original_image,memory,cpu,{0x73DA,RETURN})
    assert get(memory,APP+0x772,2)==free and get(memory,APP+0x6D4)==0x87654
    if energy==0:
        assert cpu.pc==0x73DA and get(memory,APP+0x76E,2)==0xCAFE and get(memory,APP+0x6DC)==0xFFFFFFFF
    else:
        assert cpu.pc==RETURN and(get(memory,APP+0x76E,2),get(memory,APP+0x770,2))==(0xFF80,0xFFFF)
        assert get(memory,APP+0x794,2)==max(0,energy-(512 if type_==84 else 256))
        assert get(memory,APP+0x6DC)==0 and get(memory,APP+0x7C4,2)==14


@pytest.mark.parametrize('kind',['hit','miss','no_visible'])
def test_identification_queue_consumes_selected_type_and_keeps_no_visible_gate(original_image,memory,kind):
    records=[record(flags=64 if kind=='miss'else 0)];setup(memory,records)
    put(memory,APP+0x760,0 if kind=='no_visible'else 1,2)
    put(memory,APP+0x7AE,7,2);put(memory,APP+0x7B4,31,2)
    cpu=state(memory,0x753C);run(original_image,memory,cpu,{RETURN})
    if kind=='no_visible':
        assert get(memory,APP+0x7AE,2)==0 and get(memory,APP+0x7B4,2)==1
        assert get(memory,APP+TYPE,2)==77 and get(memory,APP+REF)==OLD
    else:
        selected=0 if kind=='miss'else 2
        pointers=[0x7F1E,0xE0B8,get(memory,0xF334+4*selected),get(memory,0x37B68+140)]
        assert get(memory,APP+0x7AE,2)==4 and get(memory,APP+0x7B4,2)==0
        assert [get(memory,0xE084+4*i)for i in range(4)]==pointers
        assert get(memory,APP+TYPE,2)==selected


@pytest.mark.parametrize('kind',['hit','miss_zero_type','miss_stale_type'])
def test_idle_scan_caller_respects_variant_state_and_only_reloads_for_nonzero_type(original_image,memory,kind):
    records=[record(flags=0 if kind=='hit'else 64)];setup(memory,records)
    put(memory,APP+0x760,1,2);put(memory,APP+0x750,0,2)
    if kind=='miss_zero_type':put(memory,APP+TYPE,0,2)
    cpu=state(memory,0x757E);run(original_image,memory,cpu,{RETURN})
    expected=2 if kind=='hit'else 0 if kind=='miss_zero_type'else 77
    assert get(memory,APP+TYPE,2)==expected
    assert get(memory,APP+0x750,2)==(56 if expected else 0)
    assert get(memory,APP+REF)==(OBJECT if kind=='hit'else OLD)and cpu.a[7]==STACK+4
    # No claim that a stale supplied lock survives the real preceding gameplay phases.
