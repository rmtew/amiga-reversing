"""Original world rebuild/projector/detonation CPU paths with supplied RAM.

Original streams and bounded body indices are fixture inputs, not universal
selector, arbitrary-pointer, gameplay, hardware or lifetime guarantees.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,RETURN
from tests.test_starglider2_scan_acquisition import signed16

POOL,FREE=APP+0x2330,APP+0xEA4


@pytest.mark.parametrize('layout',range(32))
def test_original_placement_streams_rebuild_player_and_free_suffix(original_image,memory,layout):
    put(memory,0x27A8,APP);put(memory,APP+0x798,layout,2)
    for off,v in [(0x704,12345),(0x708,0xFFFFFA98),(0x70C,54321)]:put(memory,APP+off,v)
    for off,v in zip([0x744,0x746,0x748],[1023,2047,4095]):put(memory,APP+off,v,2)
    # Read the original, already classified stream. Surface stride10/interior16.
    cursor=get(memory,0x2F9FC+4*layout);placed=0
    while get(memory,cursor,2):
        placed+=1;cursor+=10 if layout<16 else 16
        assert placed<250
    memory[POOL-4:POOL+17004]=b'\xCC'*17008
    cpu=state(memory,0x17D90);run(original_image,memory,cpu,{RETURN},limit=150000)
    assert get(memory,APP+0x700)==POOL and get(memory,POOL,2)==30
    assert [get(memory,POOL+o)for o in [4,8,12]]==[0,0,0]
    assert [get(memory,APP+o)for o in [0x704,0x708,0x70C]]==[12345,0xFFFFFA98,54321]
    assert [get(memory,POOL+o,2)for o in [16,18,20]]==[1023,2047,4095]
    assert memory[POOL+2]==0x12 and memory[POOL+28]==memory[POOL+30]==255
    count=249-placed;assert get(memory,APP+0x772,2)==count
    assert get(memory,APP+0x6D4)==FREE+4*count and get(memory,APP+0x172,2)==250
    assert [get(memory,FREE+4*i)for i in range(count)]==[POOL+68*(placed+1+i)for i in range(count)]
    assert bytes(memory[POOL+68*(placed+1):POOL+17000])==b'\0'*(68*count)
    assert bytes(memory[POOL-4:POOL])==bytes(memory[POOL+17000:POOL+17004])==b'\xCC'*4


@pytest.mark.parametrize('body',[8,14])
@pytest.mark.parametrize('free',[0,1,2,5,9,65535])
@pytest.mark.parametrize('presence',[0,1,8,255])
@pytest.mark.parametrize('complete',[0,128])
def test_projector_templates_use_sign_flags_lifo_and_partial_initialization(original_image,memory,body,free,presence,complete):
    stack=INPUT;records=[INPUT+0x100+68*i for i in range(9)]
    for i,a in enumerate(records):put(memory,stack+4*i,a);memory[a:a+68]=b'\xCC'*68
    put(memory,APP+0x830,body,2);put(memory,APP+0x772,free,2)
    # Negative signed counts refuse before reading the cursor; no huge backing invented.
    cursor=stack+4*free if free<=9 else stack+36
    put(memory,APP+0x6D4,cursor);memory[APP+0xAA7]=complete
    base=APP+0xAA9+8*(14-body)
    for i in range(8):memory[base+i]=255 if presence>>i&1 else 0
    put(memory,APP+0x872,0xDEADBEEF);put(memory,APP+0x876,0xDEADBEEF)
    cpu=state(memory,0x3662E);run(original_image,memory,cpu,{RETURN})
    selected=[i for i in range(8)if presence>>i&1][:max(0,signed16(free)-1)]
    assert get(memory,APP+0x772,2)==free-len(selected)
    assert get(memory,APP+0x6D4)==cursor-4*len(selected)
    for j,i in enumerate(selected):
        a=records[free-1-j];kind=75+i;template=0x37AF6+10*i
        expected=bytearray(b'\xCC'*68)
        expected[:2]=kind.to_bytes(2,'big');expected[3]=0
        expected[4:8]=bytes(memory[template+2:template+6]);expected[8:12]=b'\0'*4
        expected[12:16]=bytes(memory[template+6:template+10]);expected[16:22]=b'\0'*6
        expected[28]|=128;expected[29]=memory[0x172CE+kind];expected[30]=255
        expected[31]=1 if complete&128 else 0
        assert bytes(memory[a:a+68])==expected  # unassigned bytes stay stale
    for a in records[:free-len(selected)]if free<=9 else records:
        assert bytes(memory[a:a+68])==b'\xCC'*68
    turret=[get(memory,APP+o)for o in [0x872,0x876]]
    assert turret==([0x7000,0x7000]if 3 in selected else [0xDEADBEEF]*2)


@pytest.mark.parametrize('previous_matches',[False,True])
@pytest.mark.parametrize('shield',[0,1,65535])
def test_detonation_requests_deduplicated_messages_and_clears_all_nonplayer_phases(original_image,memory,previous_matches,shield):
    message=get(memory,0x37B68+0x154);put(memory,0xE080,message if previous_matches else 0)
    memory[0xE084:0xE0AC]=b'\xCC'*40
    for i in range(250):
        a=POOL+68*i;memory[a:a+68]=b'\xCC'*68
        put(memory,a,[0,30,75,147][i%4],2);memory[a+30]=i&255
    before=bytes(memory[POOL:POOL+17000]);put(memory,APP+0x776,shield,2)
    put(memory,APP+0x774,123,2);put(memory,APP+0x794,456,2)
    cpu=state(memory,0x3683C);run(original_image,memory,cpu,{RETURN})
    expected=bytearray(before)
    for i in range(250):
        if i%4!=1:expected[68*i+30]=0
    assert bytes(memory[POOL:POOL+17000])==expected
    assert get(memory,APP+0x776,2)==0 and memory[APP+0xBB6]==255
    assert get(memory,APP+0x774,2)==123 and get(memory,APP+0x794,2)==456
    assert get(memory,APP+0x7AE,2)==(0 if previous_matches else 3)
    assert get(memory,APP+0x7B4,2)==(1 if previous_matches else 0)
    if not previous_matches:assert [get(memory,0xE084+4*i)for i in range(3)]==[message,0xE0B8,message]


@pytest.mark.parametrize('layout',[0,3,7,15])
@pytest.mark.parametrize('variant',[0,1])
def test_entry_runs_original_pool_to_return_and_recreates_zero_position_player(original_image,memory,layout,variant):
    from tests.test_starglider2_structure_transitions import prepare
    from tests.test_starglider2_structure_profiles import STRUCT,OBJECT
    prepare(memory);put(memory,APP+0x798,layout,2);memory[STRUCT+36]=variant
    cpu=state(memory,0xB92E);cpu.a[0]=OBJECT;cpu.a[2]=STRUCT
    before_d,before_a=list(cpu.d),list(cpu.a)
    run(original_image,memory,cpu,{RETURN},limit=150000)
    assert list(cpu.d)==before_d and list(cpu.a)[:7]==before_a[:7]
    assert get(memory,APP+0x798,2)==layout+16 and get(memory,APP+0x700)==POOL
    assert [get(memory,POOL+o)for o in [4,8,12]]==[0,0,0]
    assert [get(memory,APP+o)for o in [0x704,0x708,0x70C]]==[10000,0xFFFFFA98,19500 if variant else 21600]


@pytest.mark.parametrize('presence',[0,255])
@pytest.mark.parametrize('bomb',[0,1])
def test_surface_return_runs_pool_projector_and_optional_detonation_original_calls(original_image,memory,presence,bomb):
    from tests.test_starglider2_structure_transitions import prepare
    from tests.test_starglider2_structure_profiles import STRUCT
    prepare(memory);put(memory,APP+0x798,24,2);put(memory,APP+0x830,8,2)
    put(memory,APP+0xA76,bomb);memory[APP+0xAA9+48:APP+0xAA9+56]=bytes([presence])*8
    for off in [0x74A,0x74C,0x74E]:put(memory,APP+off,0,2)
    put(memory,APP+0x70C,20576);put(memory,0xE080,0)
    cpu=state(memory,0xBDAE);cpu.a[2]=STRUCT
    calls=[]
    def observe(pc):
        if pc in [0x17D90,0x3662E,0x3683C]:calls.append(pc)
    run(original_image,memory,cpu,{RETURN},observe,limit=150000)
    assert calls==[0x17D90,0x3662E]+([0x3683C]if bomb else [])
    assert get(memory,APP+0x798,2)==8 and get(memory,APP+0x700)==POOL
    assert [get(memory,POOL+o)for o in [4,8,12]]==[0,0,0]
    assert [get(memory,APP+o)for o in [0x704,0x708,0x70C]]==[10000,0xFFFFFB50,20000]
    assert memory[0xC4CC]==(255 if bomb else 0)
    if bomb:assert all(memory[POOL+68*i+30]==0 for i in range(1,250))
