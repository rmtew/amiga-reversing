"""Original world-list/rotation/dispatch chain under explicit supplied states.

These execute the real caller guards. They do not establish that a normal-input
flight reaches the supplied object positions/angles, or deliver DIVS exceptions.
"""
import math
import struct
import subprocess
from pathlib import Path

import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, STACK, RETURN
from tests.test_starglider2_disc_radius_layers import word, signed

TARGET=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
NAMES=['view_rotation_matrix','view_rotation_0','view_rotation_1','view_rotation_2',
       'view_origin_x','view_origin_y','view_origin_z','sine_lookup_pointer','cosine_lookup_pointer',
       'world_object_pool','world_object_slot_count','horizontal_world_wrap_mask',
       'nearby_object_count','visible_object_count','contact_object_count','free_object_count',
       'nearby_objects_cursor','visible_objects_cursor','contact_objects_cursor',
       'visible_object_list_end_slot','contact_object_list_end_slot','nearby_object_list_end_slot',
       'SG2ObjectCore_retirement_phase_or_negative','SG2ObjectCore_flags',
       'disc_queue_attempt_count','station_proximity_disc_colour_index','solice_display_radius',
       'projection_screen_origin_x','projection_screen_origin_y','inside_structure_flag',
       'view_clip_min_x','view_clip_max_x','view_clip_min_y','view_clip_max_y']


@pytest.fixture(scope='module')
def offsets(tmp_path_factory):
    # Evaluate the actual canonical RS declarations; avoid a second layout model.
    directory=tmp_path_factory.mktemp('radial-offsets');asm=directory/'offsets.s';out=directory/'offsets.bin'
    prefix=(TARGET/'starglider2_game.s').read_text().split('    SECTION code,code',1)[0]
    asm.write_text(prefix+'\n SECTION constants,data\n dc.l '+','.join(NAMES)+'\n')
    vasm=TARGET.parents[1]/'tools/vasmm68k_mot.exe'
    result=subprocess.run([str(vasm),'-quiet','-Fbin','-no-opt','-I'+str(TARGET/'includes'),'-o',str(out),str(asm)],
                          cwd=TARGET,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    values=struct.unpack('>'+len(NAMES)*'I',out.read_bytes())
    return dict(zip(NAMES,values))


def setup_world(image,m,o,kind,xyz,angles=(0,0,0),origin=(20000000,0,20000000)):
    obj=APP+o['world_object_pool'];m[obj:obj+136]=bytes(136)
    word(m,obj,kind);put(m,obj+34,100);put(m,obj+54,100)
    for off,delta,base in zip([4,8,12],xyz,origin):put(m,obj+off,(base+delta)&0xFFFFFFFF)
    for axis,base in zip('xyz',origin):put(m,APP+o['view_origin_'+axis],base)
    word(m,APP+o['world_object_slot_count'],2)
    put(m,APP+o['horizontal_world_wrap_mask'],0x0FFFFFFF)
    word(m,APP+o['station_proximity_disc_colour_index'],1)
    put(m,APP+o['solice_display_radius'],100)
    word(m,APP+o['projection_screen_origin_x'],159);word(m,APP+o['projection_screen_origin_y'],79)
    for key,value in [('view_clip_min_x',16),('view_clip_max_x',303),('view_clip_min_y',30),('view_clip_max_y',128)]:word(m,APP+o[key],value)
    put(m,APP+o['sine_lookup_pointer'],0x13F60);put(m,APP+o['cosine_lookup_pointer'],0x14760)
    for i,v in enumerate(angles):word(m,APP+o['view_rotation_'+str(i)],v)
    cpu=state(m,0x2836);run(image,m,cpu,{RETURN},limit=1000)
    assert cpu.a[7]==STACK+4
    return obj


@pytest.mark.parametrize('kind',[128,129,144,145,146,147])
@pytest.mark.parametrize('xyz',[(0,0,z)for z in [-257,-1,0,1,255,256,257,511,512,1023,1024,32767]]+[(1,0,257),(2,0,257),(-1,0,257),(0,1,257)])
def test_actual_caller_chain_to_radial_depth_or_division(original_image,memory,offsets,kind,xyz):
    m=memory;o=offsets;obj=setup_world(original_image,m,o,kind,xyz)
    matrix=[signed(get(m,APP+o['view_rotation_matrix']+2*i,2))for i in range(9)]
    assert matrix==[16382,0,-1,0,16383,0,0,0,16383]
    cpu=state(m,0x3F10);visits=[]
    run(original_image,m,cpu,{0x6958,0x6AF6},visits.append,limit=5000)
    assert all(pc in visits for pc in [0x4140,0x4320,0x489A,0x67F4])
    assert get(m,APP+o['nearby_object_count'],2)==1 and get(m,APP+o['visible_object_count'],2)==1
    assert get(m,APP+o['free_object_count'],2)==1
    relative=tuple(signed(get(m,obj+i,2))for i in [22,24,26])
    shift=max(0,max(abs(v)for v in xyz).bit_length()-10)
    scaled=[v>>shift for v in xyz]
    expected=tuple(signed((sum(matrix[3*r+c]*scaled[c]for c in range(3))&0xFFFFFFFF)>>14)for r in range(3))
    assert relative==expected and get(m,obj+44,2)==shift
    if expected[2]<=0:assert cpu.pc==0x6AF6 and 0x6B32 not in visits
    else:
        n=sum(v*v for v in expected)
        root=65536 if n==65536 else math.isqrt(n)
        assert cpu.pc==0x6958 and 0x6B32 in visits and cpu.d[0]==root
        assert get(m,APP+o['disc_queue_attempt_count'],2)==0
        if xyz==(1,0,257):assert relative==(0,0,256) and root&65535==0


@pytest.mark.parametrize('kind,limit',[(1,0x3A00),(128,0x08000000),(146,32767)])
@pytest.mark.parametrize('axis',[0,1,2])
@pytest.mark.parametrize('case',['zero','limit','over_limit','negative_limit','below_limit',
    'wrap_threshold','over_threshold','under_negative_threshold','period','negative_period','min_long'])
def test_original_partition_distance_wrap_and_partial_coordinate_stores(original_image,memory,offsets,kind,limit,axis,case):
    m=memory;o=offsets;period=0x10000000;threshold=period-limit
    delta={'zero':0,'limit':limit,'over_limit':limit+1,'negative_limit':-limit,
           'below_limit':-limit-1,'wrap_threshold':threshold,'over_threshold':threshold+1,
           'under_negative_threshold':-threshold-1,'period':period,'negative_period':-period,
           'min_long':-0x80000000}[case]
    xyz=[0,0,0];xyz[axis]=delta;obj=setup_world(original_image,m,o,kind,xyz)
    for off in [22,24,26,0x32,0x34,0x36]:word(m,obj+off,0x5A5A)
    before=bytearray(m[obj:obj+68]);expected=bytearray(before)
    accepted=True
    # The original processes X, then Z, then Y, keeping earlier stores if a
    # later component rejects. Signed MIN survives wrapped NEG as negative.
    for component,off in [(0,22),(2,26),(1,24)]:
        value=xyz[component];magnitude=signed((-value)&0xFFFFFFFF,32)if value<0 else value
        if component!=1 and magnitude>threshold:
            projected=value+period if value<0 else value-period
        else:
            if (component==1 and not -limit<=value<=limit)or(component!=1 and magnitude>limit):
                accepted=False;break
            projected=value
        expected[off:off+2]=(projected&65535).to_bytes(2,'big')
        if kind<128:
            cache={22:0x32,24:0x34,26:0x36}[off]
            expected[cache:cache+2]=(projected&65535).to_bytes(2,'big')
    cpu=state(m,0x4140);run(original_image,m,cpu,{RETURN},limit=1000)
    assert bytes(m[obj:obj+68])==expected, [(i,m[obj+i],expected[i])for i in range(68)if m[obj+i]!=expected[i]]
    assert get(m,APP+o['nearby_object_count'],2)==int(accepted)
    assert get(m,APP+o['free_object_count'],2)==1
    if accepted:assert get(m,get(m,APP+o['nearby_objects_cursor']))==obj


@pytest.mark.parametrize('count,first',[ (0,0x417C),(1,0x4292),(2,0x417C),(250,0x417C)])
def test_partition_count_gate_is_not_a_zero_count_guard(original_image,memory,offsets,count,first):
    m=memory;o=offsets;word(m,APP+o['world_object_slot_count'],count)
    cpu=state(m,0x4140);run(original_image,m,cpu,{0x417C,0x4292})
    assert cpu.pc==first and cpu.d[7]&65535==(count-1)&65535
    # Stop before the zero-count DBF traversal rather than assert its safety.


@pytest.mark.parametrize('kind',[1,128])
@pytest.mark.parametrize('flags',[0,2])
@pytest.mark.parametrize('phase',[0,128,255])
def test_contact_collection_precedes_model_flag_rejection(original_image,memory,offsets,kind,flags,phase):
    m=memory;o=offsets;obj=setup_world(original_image,m,o,kind,(0,0,1000))
    m[obj+o['SG2ObjectCore_flags']]=flags
    m[obj+o['SG2ObjectCore_retirement_phase_or_negative']]=phase
    cpu=state(m,0x4140);run(original_image,m,cpu,{RETURN},limit=1000)
    cpu=state(m,0x4320);run(original_image,m,cpu,{RETURN},limit=1000)
    contact=bool(phase&128);visible=kind>=128 or not flags&2
    assert get(m,APP+o['contact_object_count'],2)==contact
    assert get(m,APP+o['visible_object_count'],2)==visible
    if contact:assert get(m,get(m,APP+o['contact_objects_cursor']))==obj
    if visible:assert get(m,get(m,APP+o['visible_objects_cursor']))==obj
