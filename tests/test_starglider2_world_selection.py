"""Original selection/surface gates and a bounded world-entry continuation.

Lists, records and selected-state backing are supplied. These are not universal
selector, pointer-lifetime, collision or full world-transition guarantees.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,RETURN
from tests.test_starglider2_control_normalization import signed,word,guard

SPACE,SNAPSHOT,COUNT,CURSOR,INDEX,REFERENCE,SHIELD=0x77D,0xAA5,0x75E,0x6C8,0x830,0x832,0x776
LIST,OLD,RECORD,PLAYER=INPUT+0x200,INPUT+0x100,INPUT+0x400,INPUT+0x700
FLAGS,DIAG=0x6C3A,0xE103


def setup(m,records,space=255,world=(0,0,0),old_index=0x1234):
    word(m,COUNT,len(records));put(m,APP+CURSOR,LIST);word(m,INDEX,old_index);put(m,APP+REFERENCE,OLD)
    m[APP+SPACE]=space;put(m,OLD,129,2)
    for off,v in zip([0x704,0x708,0x70C],world):put(m,APP+off,v&0xFFFFFFFF)
    for i,(tag,position)in enumerate(records):
        address=RECORD+68*i;put(m,LIST+4*i,address);put(m,address,tag&65535,2)
        for off,v in zip([4,8,12],position):put(m,address+off,v&0xFFFFFFFF)


def selection(records,world,old_index=0x1234):
    chosen=(old_index,OLD);best=0x7FFFFFFF
    for i,(tag,pos)in enumerate(records):
        if signed(tag-145)>=0 or signed(tag,8)>=0:continue
        delta=[signed(x-y,32)for x,y in zip(pos,world)]
        metric=sum(-x if x<0 else x for x in delta)&0xFFFFFFFF
        if signed(best-metric,32)<0:continue
        best=metric;chosen=((tag-128)&65535,RECORD+68*i)
    return chosen


@pytest.mark.parametrize('tag',[0,127,128,129,132,144,145,146,147,255,256,32767,32768,0x8080,0x8090,0x8091,0x80FF,0xFF80,65535])
@pytest.mark.parametrize('delta',[0,1,-1,-0x80000000,0x7FFFFFFF,0xFFFFFFF0])
@pytest.mark.parametrize('space',[0,1,128,255])
def test_full_word_tag_predicate_wrapped_metric_and_zero_only_space_gate(original_image,memory,tag,delta,space):
    m=memory;records=[(tag,(delta,0,0))];setup(m,records,space)
    before=bytes(m[APP:APP+0x1000]);cpu=state(m,0x338EE);run(original_image,m,cpu,{0x3396C,0x33C4C})
    expected=selection(records,(0,0,0)) if space else(0x1234,OLD)
    assert(get(m,APP+INDEX,2),get(m,APP+REFERENCE))==expected
    assert m[APP+SNAPSHOT]==space and cpu.pc==(0x3396C if space else 0x33C4C)
    guard(m,before,[(INDEX,2),(REFERENCE,4),(SNAPSHOT,1)])


@pytest.mark.parametrize('records,world',[
    ([],(0,0,0)),
    ([(1,(0,0,0)),(145,(0,0,0))],(0,0,0)),
    ([(129,(10,0,0)),(130,(0,-10,0)),(131,(0,0,10))],(0,0,0)),
    ([(129,(-0x80000000,0,0)),(130,(1,0,0)),(131,(0x7FFFFFFF,0x7FFFFFFF,0))],(0,0,0)),
    ([(129,(-0x80000000,0,0)),(130,(0x7FFFFFFF,-1,0x7FFFFFFF))],(0x7FFFFFFF,-1,-0x80000000)),
])
def test_selection_preserves_stale_state_last_ties_and_long_overflow(original_image,memory,records,world):
    m=memory;setup(m,records,world=world);cpu=state(m,0x338EE);run(original_image,m,cpu,{0x3396C})
    assert(get(m,APP+INDEX,2),get(m,APP+REFERENCE))==selection(records,world)


def surface_expected(tag,flag,depth,x,y):
    if signed(tag-144)>=0 or tag in [128,132] or flag&128:return False
    extra=(depth-305)&65535
    if signed(extra)<0:return False
    ax=(-x if signed(x)<0 else x)&65535;ay=(-y if signed(y)<0 else y)&65535
    return signed(ax-((144+extra)&65535))<0 and signed(ay-((49+extra)&65535))<0


def surface(image,m,tag,flag,depth,x,y,index=1,space=255):
    put(m,APP+REFERENCE,RECORD);put(m,RECORD,tag,2);word(m,INDEX,index)
    put(m,RECORD+38,x&65535,2);put(m,RECORD+40,y&65535,2);put(m,RECORD+42,depth&65535,2)
    m[FLAGS+tag-128]=flag;m[APP+SPACE]=space;word(m,SHIELD,0x1234)
    before=bytes(m[APP:APP+0x1000]);cpu=state(m,0x3396C);run(image,m,cpu,{0x339E4})
    accept=surface_expected(tag,flag,depth,x,y)
    assert m[APP+SPACE]==(0 if accept and index else space)
    assert get(m,APP+SHIELD,2)==(0 if accept and not index else 0x1234)
    guard(m,before,[(SPACE,1),(SHIELD,2)])


@pytest.mark.parametrize('tag',range(128,145))
@pytest.mark.parametrize('flag',[0,127,128,255])
@pytest.mark.parametrize('index',[0,1])
@pytest.mark.parametrize('space',[1,255])
def test_surface_type_and_rejection_gates_keep_index_zero_response_distinct(original_image,memory,tag,flag,index,space):
    surface(original_image,memory,tag,flag,400,0,0,index,space)


@pytest.mark.parametrize('depth',[304,305,306,32767,32768,33071,33072,33073,65535])
@pytest.mark.parametrize('dx',[-1,0,1])
@pytest.mark.parametrize('dy',[-1,0,1])
@pytest.mark.parametrize('direction',[-1,1])
def test_strict_projected_edges_use_word_abs_and_n_only_limits(original_image,memory,depth,dx,dy,direction):
    extra=(depth-305)&65535
    surface(original_image,memory,129,0,depth,direction*((144+extra+dx)&65535),direction*((49+extra+dy)&65535))


@pytest.mark.parametrize('depth',[305,32768,65535])
@pytest.mark.parametrize('x,y',[(-32768,-32768),(32767,32767),(-32768,0),(0,-32768),(-1,1)])
def test_minimum_word_absolute_values_remain_wrapped(original_image,memory,depth,x,y):
    surface(original_image,memory,129,0,depth,x,y)


def test_no_candidate_still_uses_prior_record_and_unchecked_index_pair(original_image,memory):
    m=memory;setup(m,[(1,(0,0,0))],old_index=0)
    put(m,OLD+42,400,2);put(m,OLD+38,0,2);put(m,OLD+40,0,2);m[FLAGS+1]=0;word(m,SHIELD,0x1234)
    cpu=state(m,0x338EE);run(original_image,m,cpu,{0x339E4})
    assert get(m,APP+REFERENCE)==OLD and get(m,APP+INDEX,2)==0
    assert get(m,APP+SHIELD,2)==0 and m[APP+SPACE]==255


@pytest.mark.parametrize('index',range(16))
def test_actual_empty_capture_world_entry_pose_reaches_settling_exit_after_41_calls(original_image,memory,index):
    m=memory;word(m,INDEX,index);word(m,COUNT,0);put(m,APP+0x700,PLAYER)
    m[PLAYER:PLAYER+68]=b'\xA5'*68;put(m,APP+0x704,123);put(m,APP+0x708,456);put(m,APP+0x70C,789)
    word(m,0x9AE,65535);word(m,0xA74,16000);m[APP+0xA7E]=255
    for off,v in zip([0x74A,0x74C,0x74E],[11,22,33]):word(m,off,v)
    before=bytes(m[APP:APP+0x1000]);cpu=state(m,0x33A3A)
    run(original_image,m,cpu,{0x33AF6})  # includes the actual capture helper with an empty supplied list
    mask=get(m,0x176A2+4*index);height=(get(m,0x17642+4*index)+200)&0xFFFFFFFF
    assert [get(m,APP+o)for o in [0x704,0x708,0x70C]]==[mask>>1,height,mask>>1]
    assert [get(m,PLAYER+o)for o in [4,8,12]]==[mask>>1,height,mask>>1]
    assert [get(m,APP+o,2)for o in [0x744,0x746,0x748]]==[0xF0A,0,0]
    assert [get(m,PLAYER+o,2)for o in [16,18,20]]==[0xF0A,0,0]
    assert m[APP+0xBB9]==1 and get(m,APP+0x6FC)==mask
    assert get(m,APP+0x7B0,2)==get(m,0x6BE2+2*index,2)
    assert get(m,0x2F522,2)==get(m,0x3990C+2*index,2)
    assert get(m,APP+0x798,2)==index and get(m,0x39B82,2)==65535
    assert get(m,APP+0x9AE,2)==get(m,APP+0xA74,2)==0 and m[APP+0xA7E]==0
    assert [get(m,APP+o,2)for o in [0x74A,0x74C,0x74E]]==[0,0,0]
    guard(m,before,[(0x9AE,2),(0xA74,2),(0xA7E,1),(0x74A,6),(0x7B0,2),(0x798,2),(0x6FC,4),(0x704,4),(0x708,4),(0x70C,4),(0xBB9,1),(0x744,6)])
    # The produced positive flag routes the real caller to settling. No physical cadence is assumed.
    m[0x39B78]=0
    for n in range(41):
        cpu=state(m,0x2F69C);run(original_image,m,cpu,{RETURN})
        assert get(m,APP+0x744,2)==(0xF0A+6*(n+1))&4095
        assert m[APP+0xBB9]==(255 if n==40 else 1)
