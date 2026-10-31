"""Original cache/exit continuations with supplied backing, not lifetime proof.

Whole RAM expectations retain accesses outside the 17-slot seed. No larger
owner, universal tag domain or complete transition safety is inferred.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT
from tests.test_starglider2_control_normalization import signed,word,guard

CACHE=APP+0x87C;POOL=APP+0x2330;LIST=INPUT+0x100;SOURCE=INPUT+0x400
INDEX,SPACE,SPEED,POINT=0x830,0x77D,0x75A,0xA9D
REFY,RADII,YTHRESH=0x17642,0x175F2,0x395CA
TAGS=[0,127,128,129,144,145,146,147,148,255,0x8080,0xFF80]


def cache_address(tag):return CACHE+signed((tag-128)<<4)
def accepted(tag):return signed(tag,8)<0 and(tag&65535)!=147

def write(m,address,value,width=4):put(m,address,value&((1<<(width*8))-1),width)


def capture(image,m,records):
    word(m,0x75E,len(records));put(m,APP+0x6C8,LIST)
    for i,(tag,coords,tail)in enumerate(records):
        p=SOURCE+68*i;put(m,LIST+4*i,p);write(m,p,tag,2)
        for offset,value in zip([4,8,12],coords):write(m,p+offset,value)
        write(m,p+32,tail,2)
    cpu=state(m,0x33AF6);expected=bytearray(m)
    for tag,coords,tail in records:
        if accepted(tag):
            address=cache_address(tag)
            for offset,value in zip([0,4,8,12],list(coords)+[signed(tail)]):write(expected,address+offset,value)
    run(image,m,cpu,{0x33B3A});assert bytes(m)==expected


@pytest.mark.parametrize('tag',TAGS)
@pytest.mark.parametrize('tail',[-32768,-1,0,1,32767])
def test_capture_retains_signed_stride_aliases_and_word20_extension(original_image,memory,tag,tail):
    capture(original_image,memory,[(tag,[0x80000000,0x7FFFFFFF,0xFEDCBA98],tail)])


@pytest.mark.parametrize('records',[
    [],[(147,[1,2,3],4)],
    [(128,[1,2,3],-1),(129,[4,5,6],32767),(128,[7,8,9],-32768)],
    [(128,[1,2,3],1),(0x8080,[4,5,6],-1),(145,[7,8,9],-32768)],
])
def test_capture_zero_count_skip_and_ordered_duplicate_slots(original_image,memory,records):
    capture(original_image,memory,records)


def restore(image,m,tag,metadata,index):
    word(m,INDEX,index)
    m[POOL:POOL+23*68]=b'\xA5'*(23*68)
    for i in range(23):put(m,POOL+68*i,0,2)
    # Slot0 and slot22 are valid but outside the actual 21-record walk.
    put(m,POOL,128,2);put(m,POOL+22*68,128,2);write(m,POOL+68,tag,2)
    values=[0x80000000,0x12345678,0xFEDCBA98,metadata]
    for offset,value in zip([0,4,8,12],values):write(m,cache_address(tag)+offset,value)
    cpu=state(m,0x33F02);expected=bytearray(m)
    if accepted(tag):
        for offset,value in zip([4,8,12],values):write(expected,POOL+68+offset,value)
        write(expected,POOL+68+32,metadata,2)
        if(index&65535)==(tag-128)&65535:
            for offset,value in zip([0x704,0x708,0x70C],values):write(expected,APP+offset,value)
    run(image,m,cpu,{0x33F66});assert bytes(m)==expected


@pytest.mark.parametrize('tag',TAGS)
@pytest.mark.parametrize('metadata',[0,65535,0xA5A58000,0x7FFFFFFF])
@pytest.mark.parametrize('index',[0,1,16,17,20,127,0xFF00])
def test_restore_exact_21_records_full_xyz_low_word20_and_selected_match(original_image,memory,tag,metadata,index):
    restore(original_image,memory,tag,metadata,index)


@pytest.mark.parametrize('index',range(16))
@pytest.mark.parametrize('old_y',[-0x80000000,-1,0,1,0x7FFFFFFF])
@pytest.mark.parametrize('radius',[None,-1,-0x80000000,0x7FFFFFFF])
def test_post_restore_y_uses_saved_selector_double_reference_and_arithmetic_radius_half(original_image,memory,index,old_y,radius):
    m=memory;write(m,APP+0x708,old_y);word(m,INDEX,index^7)
    if radius is not None:write(m,RADII+4*index,radius)
    ref=get(m,REFY+4*index);r=signed(get(m,RADII+4*index),32)
    expected=(old_y+2*ref-(r>>1)-200)&0xFFFFFFFF
    cpu=state(m,0x33F66);cpu.d[7]=0xBEEF0000|index;before=bytes(m)
    expected_memory=bytearray(before);write(expected_memory,APP+0x708,expected);expected_memory[0xE103]=0x89
    run(original_image,m,cpu,{0x33F9A});assert bytes(m)==expected_memory


def fold_angle(yaw):
    if signed(yaw-2048)<0:return yaw&65535
    return(-yaw)&2047


@pytest.mark.parametrize('index',[0,15])
@pytest.mark.parametrize('position',[0,1,2,3,4,5,6,7])
@pytest.mark.parametrize('yaw',[0,2047,2048,4095,32768,65535])
@pytest.mark.parametrize('delta',[-1,0,1])
@pytest.mark.parametrize('speed',[459,460,32768,65535])
def test_surface_exit_height_angle_and_speed_use_original_n_predicates(original_image,memory,index,position,yaw,delta,speed):
    m=memory;word(m,INDEX,index);ref=get(m,REFY+4*index);threshold=get(m,YTHRESH+4*index)
    y=[ref-1,ref,ref+1,threshold-1,threshold,threshold+1,-0x80000000,0x7FFFFFFF][position]&0xFFFFFFFF
    folded=fold_angle(yaw);pitch=(239+folded+delta)&65535
    write(m,APP+0x708,y);word(m,0x744,pitch);word(m,0x748,yaw);word(m,SPEED,speed);m[APP+SPACE]=0
    expected_field=0 if signed(threshold-y,32)<0 else 255
    leaves=(signed(ref-y,32)>=0 and signed(pitch-((239+folded)&65535))>=0 and signed(speed-460)>=0)
    before=bytes(m[APP:APP+0x1000]);cpu=state(m,0x33DD0);run(original_image,m,cpu,{0x33E52})
    assert m[APP+POINT]==expected_field and m[APP+SPACE]==(255 if leaves else 0)
    guard(m,before,[(POINT,1),(SPACE,1)])

@pytest.mark.parametrize('tag',[128,145,0xFF80])
@pytest.mark.parametrize('tail',[-32768,-1,1])
def test_actual_capture_then_restore_uses_the_same_logical_slot_format(original_image,memory,tag,tail):
    m=memory;coords=[0x80000000,0xFEDCBA98,0x12345678]
    capture(original_image,m,[(tag,coords,tail)])
    m[POOL:POOL+23*68]=bytes(23*68);put(m,POOL+68,tag,2);word(m,INDEX,(tag-128)&65535)
    cpu=state(m,0x33F02);expected=bytearray(m)
    for off,value in zip([4,8,12],coords):write(expected,POOL+68+off,value)
    write(expected,POOL+68+32,tail,2)
    for off,value in zip([0x704,0x708,0x70C],coords):write(expected,APP+off,value)
    run(original_image,m,cpu,{0x33F66});assert bytes(m)==expected
