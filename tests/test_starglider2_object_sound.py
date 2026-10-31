"""Original nearby-object software selectors and Paula descriptor consumers.

Fixtures enter after preceding device writes and stop before downstream device
phases/frame restoration. Original tables and supplied RAM do not prove global
index/ownership, PCM, concurrency or normal-game reachability contracts.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT
from tests.test_starglider2_scan_acquisition import signed16

RECORDS=[INPUT+0x100+128*i for i in range(5)];LIST,OLD=INPUT+0x600,INPUT+0x900
DESC,PFILTER,AFILTER=0x4CBF4,0x4D1C0,0x4DE3E
PREF,PFOUND,PSPECIAL=0x4D088,0x4D094,0x4D256
AREF,AFOUND,ATYPE,AVOL=0x4DDA8,0x4DE3B,0x39CE0,0x4DDAC
PBASE,PCUR,PBASEVOL,PTARGET,PSMOOTH,POUT=0x4D09E,0x4D096,0x4D0A2,0x4D086,0x4D084,0x4D09C
PREVIOUS=(0x4D08E,0x4D090,0x4D092)
LIMITS={91:1200,12:1100,8:1000,5:500,46:350}


def n16(v):return bool(v&32768)
def magnitude(v):return (-v)&65535 if n16(v)else v

def metric(coords,shift):return (sum(magnitude(v&65535)for v in coords)&65535)>>shift


def record(memory,index,kind=1,phase=128,flags=0,coords=(4000,0,0),word20=0):
    a=RECORDS[index];memory[a:a+68]=b'\0'*68;put(memory,a,kind,2)
    memory[a+2]=flags;memory[a+30]=phase
    for o,v in zip([22,24,26],coords):put(memory,a+o,v&65535,2)
    put(memory,a+32,word20,2)
    return dict(address=a,kind=kind,phase=phase,flags=flags,coords=coords)


def setup(memory,rows):
    put(memory,APP+0x75E,len(rows),2);put(memory,APP+0x6C8,LIST)
    for i,r in enumerate(rows):put(memory,LIST+4*i,r['address'])
    put(memory,PREF,OLD);put(memory,PFOUND,0x7777,2);put(memory,PSPECIAL,0x5555,2)
    put(memory,AREF,OLD);memory[AFOUND]=255;put(memory,ATYPE,77,2)
    for a,v in [(PTARGET,999),(PSMOOTH,4),(POUT,888),(PBASE,500),(PCUR,400),(PBASEVOL,24),(AVOL,4),(0x4DE18,32768)]:put(memory,a,v,2)
    memory[0x4DE14]=128
    put(memory,0x4D0AA,0x11223344);put(memory,0x4D0AE,0);put(memory,0x4D0A8,0,2);put(memory,0x4D0A6,65535,2)
    put(memory,APP+0x758,0,2)
    for a in PREVIOUS:put(memory,a,0,2)


def selection(memory,rows,backend):
    best=32767;selected=None;special=False;found=False
    for r in rows:
        kind=r['kind'];f=r['flags'];phase=r['phase']
        eligible=(f&12 or phase>=128 or(backend=='paula'and kind==16))and memory[(PFILTER if backend=='paula'else AFILTER)+kind]<128
        if not eligible:continue
        d=metric(r['coords'],2);special=False
        if backend=='paula'and kind in LIMITS and d<LIMITS[kind]:return r,d,True,found
        if d<=best:selected=r;best=d;found=True
    return selected,best,special,found


def select_cpu(image,memory,backend):
    cpu=state(memory,0x4BE58 if backend=='paula'else 0x4D452);cpu.a[2]=OLD
    run(image,memory,cpu,{0x4BF46,0x4C1A4}if backend=='paula'else{0x4D53A})
    return cpu


@pytest.mark.parametrize('backend',['paula','alternate'])
@pytest.mark.parametrize('kind',[0,1,2,5,8,12,16,46,64,91,103])
@pytest.mark.parametrize('phase',[0,1,128,255])
@pytest.mark.parametrize('flags',[0,4,8])
def test_original_type_tables_and_profile_specific_phase_gates(original_image,memory,backend,kind,phase,flags):
    r=record(memory,0,kind,phase,flags);setup(memory,[r]);expected,d,special,found=selection(memory,[r],backend)
    cpu=select_cpu(original_image,memory,backend)
    if backend=='paula':
        assert cpu.pc==(0x4BF46 if expected else 0x4C1A4)
        assert get(memory,PREF)==(r['address']if expected else OLD)
        assert get(memory,PFOUND,2)==(65535 if found else 0)
        if expected:assert get(memory,PSPECIAL,2)==(65535 if special else 0)
    else:
        assert get(memory,AREF)==(r['address']if expected else 0)
        assert memory[AFOUND]==(255 if expected else 0)
        assert get(memory,ATYPE,2)==(kind if expected else 0)
        assert get(memory,AVOL,2)==(max(0,memory[AFILTER+kind]-(d>>11))if expected else 3)


@pytest.mark.parametrize('backend',['paula','alternate'])
@pytest.mark.parametrize('coords',[(-32768,-32768,0),(-32768,0,0),(32767,32767,32767),(-1,-1,-1),(0,0,0)])
@pytest.mark.parametrize('reverse',[False,True])
def test_wrapped_word_magnitude_sum_and_last_equal_metric_win(original_image,memory,backend,coords,reverse):
    rows=[record(memory,0,1,coords=coords),record(memory,1,3,coords=(400,0,0))]
    if reverse:rows.reverse()
    setup(memory,rows);expected,_,_,_=selection(memory,rows,backend);select_cpu(original_image,memory,backend)
    assert get(memory,PREF if backend=='paula'else AREF)==expected['address']


@pytest.mark.parametrize('backend',['paula','alternate'])
@pytest.mark.parametrize('reverse',[False,True])
def test_equal_metric_selects_last_eligible_record(original_image,memory,backend,reverse):
    rows=[record(memory,0,1),record(memory,1,3)]
    if reverse:rows.reverse()
    setup(memory,rows);select_cpu(original_image,memory,backend)
    assert get(memory,PREF if backend=='paula'else AREF)==rows[-1]['address']


@pytest.mark.parametrize('backend',['paula','alternate'])
@pytest.mark.parametrize('kind',list(LIMITS))
@pytest.mark.parametrize('edge',[-1,0,1])
@pytest.mark.parametrize('special_first',[False,True])
def test_paula_first_special_metric_preempts_nearest_and_stops_scan(original_image,memory,backend,kind,edge,special_first):
    ordinary=record(memory,0,1,coords=(4,0,0));special=record(memory,1,kind,coords=(4*(LIMITS[kind]+edge),0,0));last=record(memory,2,3,coords=(0,0,0))
    rows=[special,ordinary,last]if special_first else[ordinary,special,last]
    setup(memory,rows);expected,_,priority,found=selection(memory,rows,backend);select_cpu(original_image,memory,backend)
    assert get(memory,PREF if backend=='paula'else AREF)==expected['address']
    if backend=='paula':assert get(memory,PFOUND,2)==(65535 if found else 0)
    if kind==91:assert memory[PFILTER+91]>=128  # original-table refusal, no forced activation
    assert priority==(backend=='paula'and kind!=91 and edge<0)


@pytest.mark.parametrize('backend',['paula','alternate'])
@pytest.mark.parametrize('count',[0,1])
@pytest.mark.parametrize('volume',[0,1,32768,65535])
def test_no_selection_retains_or_clears_exact_original_state(original_image,memory,backend,count,volume):
    rows=[record(memory,0,1,phase=0)]if count else[];setup(memory,rows)
    put(memory,PSMOOTH,volume,2);put(memory,AVOL,volume,2)
    cpu=state(memory,0x4BE58 if backend=='paula'else 0x4D452)
    run(original_image,memory,cpu,{0x4C5AC}if backend=='paula'else{0x4D53A})
    if backend=='paula':
        v=(volume-2)&65535;v=0 if n16(v)else v
        assert get(memory,PREF)==OLD and get(memory,ATYPE,2)==77
        assert get(memory,PFOUND,2)==(0 if count else 0x7777)
        assert get(memory,PSMOOTH,2)==get(memory,POUT,2)==v and get(memory,PTARGET,2)==0
    else:
        v=(volume-1)&65535;v=0 if n16(v)else v
        assert get(memory,AREF)==(0 if count else OLD)and memory[AFOUND]==(0 if count else 255)
        assert get(memory,ATYPE,2)==0 and get(memory,AVOL,2)==v
        assert memory[0x4DE14]==127 and get(memory,0x4DE18,2)==32767


def full_paula(image,memory):
    cpu=state(memory,0x4BE58);run(image,memory,cpu,{0x4C1CA,0x4C572,0x4C5AC});return cpu


def expected_period_volume(memory,r,oldcoords,current,basevol,smooth,prefix):
    old_metric=metric(oldcoords,1);d=metric(r['coords'],1)
    object_bias=(-get(memory,r['address']+32,2))&65535
    player_bias=(signed16(-get(memory,APP+0x758,2))>>2)&65535
    if n16(d-old_metric):object_bias=(-object_bias)&65535;player_bias=(-player_bias)&65535
    target=(get(memory,DESC+16*r['kind']+6,2)+object_bias+player_bias)&65535
    period=current if current==target else(current-4 if not n16(current-target)else current+4)&65535
    distance=1 if n16(d-1)else d
    volume=(basevol-(distance>>7))&65535
    if n16(volume):volume=0
    volume=(volume+prefix)&65535
    if not n16(volume-64):volume=64
    if smooth!=volume:
        if n16(volume-smooth):
            smooth=(smooth-2)&65535
            if not n16(volume-smooth):smooth=volume
        else:
            smooth=(smooth+2)&65535
            if n16(volume-smooth):smooth=volume
    return period,volume,smooth,object_bias,player_bias


@pytest.mark.parametrize('kind',[1,3,8])
@pytest.mark.parametrize('changed',[False,True])
@pytest.mark.parametrize('sample_matches',[False,True])
@pytest.mark.parametrize('restart',[0,65535])
@pytest.mark.parametrize('transition',[0,65535])
def test_descriptor_transition_preserves_stale_base_state_until_later_service(original_image,memory,kind,changed,sample_matches,restart,transition):
    r=record(memory,0,kind);setup(memory,[r]);put(memory,ATYPE,0 if changed else kind,2)
    sample=get(memory,DESC+16*kind);put(memory,0x4D0AE,sample if sample_matches else sample^1)
    put(memory,0x4D0A8,restart,2);put(memory,0x4D0A6,transition,2)
    copied=changed and sample_matches
    current=get(memory,DESC+16*kind+6,2)if copied else 400
    base=get(memory,DESC+16*kind+8,2)if copied else 24
    expected=expected_period_volume(memory,r,(0,0,0),current,base,4,0)
    full_paula(original_image,memory)
    requested=sample if changed else 0x11223344
    expected_restart=65535 if changed and not sample_matches else restart
    activated=(changed and not sample_matches)or(not changed and restart>=32768)
    expected_transition=11 if activated and transition>=32768 else transition
    assert get(memory,0x4D0AA)==requested and get(memory,0x4D0A8,2)==expected_restart
    assert get(memory,0x4D0A6,2)==expected_transition and get(memory,PBASEVOL,2)==base
    assert [get(memory,a,2)for a in [PCUR,PBASE,PTARGET,PSMOOTH,POUT,0x4D0C4,0x4D0C2]]==[expected[0],expected[0],expected[1],expected[2],expected[2],expected[3],expected[4]]
    assert [get(memory,a,2)for a in PREVIOUS]==list(r['coords'])
    assert get(memory,ATYPE,2)==kind


@pytest.mark.parametrize('phase',[0,128])
@pytest.mark.parametrize('order',[(0,1,3),(1,0,3),(1,2,0,3),(2,1,0),(1,3,0)])
def test_same_type_sum_is_only_prefix_and_does_not_repeat_eligibility_filter(original_image,memory,phase,order):
    objects=[record(memory,0,1,coords=(400,0,0)),record(memory,1,1,phase=phase,coords=(1000,0,0)),record(memory,2,3,phase=phase,coords=(5000,0,0)),record(memory,3,1,phase=phase,coords=(2000,0,0))]
    rows=[objects[i]for i in order];setup(memory,rows)
    put(memory,ATYPE,1,2);total=0;base=get(memory,DESC+16+8,2)
    for r in rows:
        if r['kind']!=1 or r['address']==objects[0]['address']:break
        distance=metric(r['coords'],1);distance=1 if n16(distance-1)else distance
        value=(base-(distance>>7))&65535
        if n16(value):value=0
        total=(total+value)&65535
    full_paula(original_image,memory)
    assert get(memory,PREF)==objects[0]['address']
    assert get(memory,0x4D08C,2)==total
    assert get(memory,PTARGET,2)==min(64,23+total)


@pytest.mark.parametrize('old_x',[0,4000,32768,65535])
@pytest.mark.parametrize('new_x',[400,32768])
@pytest.mark.parametrize('word20',[0,200,32768,65535])
@pytest.mark.parametrize('speed',[0,1,32768,65535])
@pytest.mark.parametrize('period',[0,32767,32768,65535])
def test_relative_snapshot_period_bias_and_word_step_preserve_overflow(original_image,memory,old_x,new_x,word20,speed,period):
    r=record(memory,0,1,coords=(new_x,0,0),word20=word20);setup(memory,[r])
    put(memory,ATYPE,1,2);put(memory,PREVIOUS[0],old_x,2);put(memory,APP+0x758,speed,2);put(memory,PCUR,period,2)
    expected=expected_period_volume(memory,r,(old_x,0,0),period,24,4,0)
    full_paula(original_image,memory)
    assert [get(memory,a,2)for a in [PCUR,PBASE,PTARGET,PSMOOTH,POUT,0x4D0C4,0x4D0C2]]==[expected[0],expected[0],expected[1],expected[2],expected[2],expected[3],expected[4]]
    assert [get(memory,a,2)for a in PREVIOUS]==[new_x,0,0]


@pytest.mark.parametrize('difference',[-3,-1,0,1,3])
def test_period_four_step_can_overshoot_and_return_without_target_clamp(original_image,memory,difference):
    r=record(memory,0,1,coords=(400,0,0));setup(memory,[r]);put(memory,ATYPE,1,2)
    put(memory,PREVIOUS[0],400,2);target=get(memory,DESC+16+6,2);initial=target+difference;put(memory,PCUR,initial,2)
    full_paula(original_image,memory);first=get(memory,PCUR,2)
    full_paula(original_image,memory);second=get(memory,PCUR,2)
    assert first==(initial if difference==0 else initial+4 if difference<0 else initial-4)
    assert second==initial  # serial continuation only, not an audible oscillation claim
