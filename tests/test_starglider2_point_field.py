"""Original point-field arithmetic, RAM plotting and scene packet writes.

Explicit matrices, backing and cached points are fixture inputs. Alternate
profiles retain shipped X tables; these are not complete installed pixel
encodings, clipping-caller closure, DMA/scanout or retry-termination proofs.
"""
import struct
import subprocess
from pathlib import Path

import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,FB,INPUT,STACK,RETURN
from tests.test_starglider2_control_normalization import signed
from tests.test_starglider2_palette_priority import rng
from tests.test_starglider2_contact_plot import initialize,ROW_TABLE,X_OFFSETS,X_MASKS

CURSOR,REF_CURSOR,POLY_CURSOR,COUNT=0x4E5C0,0x3C2C,0x3C30,0x49A8
STYLES={'other':0x4E56C,'body5':0x4E588,'le1':0x4E5A4}
REFERENCE,PACKET=INPUT+0x400,INPUT+0x1000
PROFILES=['amiga','mode0','mode1']
FIELDS=['point_field_world_positions','point_field_previous_view_positions','point_field_plane_byte_stride',
 'player_world_x','player_world_y','player_world_z','view_rotation_matrix','stardrive_speed_addend',
 'selected_celestial_body_index','projection_screen_origin_x','projection_screen_origin_y',
 'view_clip_min_x','view_clip_max_x','view_clip_min_y','view_clip_max_y',
 'player_rotation_1','sine_lookup_pointer','cosine_lookup_pointer','shared_random_state_a','shared_random_state_b']


@pytest.fixture(scope='module')
def fields(tmp_path_factory):
    root=Path(__file__).resolve().parents[1];target=root/'targets/amiga_raw_starglider2_game'
    temp=tmp_path_factory.mktemp('point-fields');asm=temp/'fields.s';out=temp/'fields.bin'
    asm.write_text((target/'starglider2_game.s').read_text().split('    SECTION code,code',1)[0]+
                   '\n SECTION constants,data\n dc.l '+','.join(FIELDS)+'\n')
    result=subprocess.run([str(root/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-no-opt','-I'+str(target/'includes'),
                           '-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    return {name:APP+value for name,value in zip(FIELDS,struct.unpack('>'+len(FIELDS)*'I',out.read_bytes()))}


def word(m,p,v):put(m,p,v&65535,2)
def divide(n,d):return (-1 if (n<0)!=(d<0)else 1)*(abs(n)//abs(d))
def shifted_product(a,b):return signed(((signed(a)*signed(b))&0xFFFFFFFF)>>14)
def fast(speed):return signed((speed-500)&65535)>=0


def prepare(image,m,f,profile='amiga',speed=0):
    initialize(image,m,profile);word(m,0x1002,0x8000 if profile=='amiga'else 0)
    word(m,f['stardrive_speed_addend'],speed)
    for key,value in [('projection_screen_origin_x',159),('projection_screen_origin_y',79),
                      ('view_clip_min_x',16),('view_clip_max_x',303),('view_clip_min_y',30),('view_clip_max_y',128)]:word(m,f[key],value)
    for axis in 'xyz':put(m,f['player_world_'+axis],0)
    for i,v in enumerate([16384,0,0,0,16384,0,0,0,16384]):word(m,f['view_rotation_matrix']+2*i,v)
    m[f['point_field_previous_view_positions']:f['point_field_previous_view_positions']+120]=bytes(120)
    m[FB:FB+0x8000]=b'\xA5'*0x8000


@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('xyz',[(1,1,1),(-1,32767,-32768),(100,-300,2000),(65535,0,0)])
@pytest.mark.parametrize('matrix',[[16384,0,0,0,16384,0,0,0,16384],[8192]*9,[32767,-32768,12345,-8192,4096,30000,17,-20,16383]])
def test_per_product_rounding_and_cache_store_precede_trail_decision(original_image,memory,fields,profile,xyz,matrix):
    m=memory;f=fields;prepare(original_image,m,f,profile)
    for i,v in enumerate(matrix):word(m,f['view_rotation_matrix']+2*i,v)
    for axis,value in zip('xyz',[0x12340000,0xFFFF0000,0]):put(m,f['player_world_'+axis],value)
    for i,v in enumerate(xyz):word(m,f['point_field_world_positions']+2*i,v)
    previous=[-1,123,456]
    for i,v in enumerate(previous):word(m,f['point_field_previous_view_positions']+2*i,v)
    put(m,APP+0x54,0xCAFEBABE)
    cpu=state(m,0x4E04A);run(original_image,m,cpu,{0x4E178})
    delta=[signed(v)for v in xyz]
    result=[signed(sum(shifted_product(matrix[3*r+c],delta[c])for c in range(3)))for r in range(3)]
    assert list(cpu.d[1:4])==[v&0xFFFFFFFF for v in result]
    assert list(cpu.d[4:7])==[v&0xFFFFFFFF for v in previous]
    assert [signed(get(m,f['point_field_previous_view_positions']+2*i,2))for i in range(3)]==result
    assert get(m,CURSOR)==f['point_field_previous_view_positions']+6
    assert cpu.a[4]==f['point_field_world_positions']+6 and get(m,APP+0x56,2)==0xBABE
    assert get(m,f['point_field_plane_byte_stride'],2)=={'amiga':8192,'mode0':2,'mode1':0}[profile]
    if xyz==(1,1,1)and matrix==[8192]*9:assert result==[0,0,0]  # Sum-first extraction would give one.


DEPTHS=sorted({0,32767,32768,65535}|{v+d for v in range(0,32768,2048)for d in [-1,0,1]if 0<=v+d<=65535})
@pytest.mark.parametrize('depth',DEPTHS)
@pytest.mark.parametrize('body',[-32768,-1,0,1,2,5,6,32767])
@pytest.mark.parametrize('count',[0,65535])
def test_depth_style_prefix_and_exact_fourteen_byte_scene_packet(original_image,memory,fields,depth,body,count):
    m=memory;f=fields;prepare(original_image,m,f)
    word(m,f['selected_celestial_body_index'],body);word(m,COUNT,count)
    put(m,REF_CURSOR,REFERENCE);put(m,POLY_CURSOR,PACKET)
    m[REFERENCE-4:REFERENCE+8]=b'\x5A'*12;m[PACKET-4:PACKET+18]=b'\xA5'*22
    expected=bytearray(m);table=STYLES['le1'if body<=1 else'body5'if body==5 else'other']
    index=0 if depth&32768 else(depth>>11)&14
    style=get(m,table+index,2);coords=[16,30,303,128]
    put(expected,REFERENCE,PACKET);put(expected,REF_CURSOR,REFERENCE+4);put(expected,POLY_CURSOR,PACKET+14)
    word(expected,COUNT,count+1)
    expected[PACKET:PACKET+14]=struct.pack('>7H',depth,style,*coords,65535)
    cpu=state(m,0x4E22E);cpu.d[1],cpu.d[2],cpu.d[4],cpu.d[5],cpu.d[6],cpu.d[7]=*coords,depth,0
    run(original_image,m,cpu,{RETURN})
    assert bytes(m)==expected and cpu.a[7]==STACK+4
    assert 0<=index<=14 and index%2==0


@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('speed',[0,499,500,32768,65535])
@pytest.mark.parametrize('xyz',[(-10,0,129),(0,0,128),(10,-10,256),(100,100,512),(2000,0,256)])
def test_simple_point_projection_and_plane_alias_writes(original_image,memory,fields,profile,speed,xyz):
    m=memory;f=fields;prepare(original_image,m,f,profile,speed)
    stride={'amiga':8192,'mode0':2,'mode1':0}[profile];word(m,f['point_field_plane_byte_stride'],stride)
    x,y,z=xyz;expected=bytearray(m[FB:FB+0x8000])
    sx=159+divide(x*128,z&65534);sy=79+divide(y*128,z&65534)
    accepted=z>128 and 16<=sx<=303 and 30<=sy<=128
    if accepted and not fast(speed):
        address=FB+get(m,ROW_TABLE+2*sy,2)+get(m,X_OFFSETS+2*sx,2);mask=get(m,X_MASKS+2*sx,2)
        for plane in [0,2,3]:
            pos=address+plane*stride-FB;value=int.from_bytes(expected[pos:pos+2],'big')&(~mask&65535)
            expected[pos:pos+2]=value.to_bytes(2,'big')
        pos=address+stride-FB;value=int.from_bytes(expected[pos:pos+2],'big')|mask;expected[pos:pos+2]=value.to_bytes(2,'big')
    cpu=state(m,0x4E298);cpu.d[1],cpu.d[2],cpu.d[3],cpu.d[7]=x&0xFFFFFFFF,y&0xFFFFFFFF,z,0
    cpu.a[1],cpu.a[3],cpu.a[5]=ROW_TABLE,X_OFFSETS,X_MASKS
    run(original_image,m,cpu,{RETURN,0x4E350})
    assert (cpu.pc==RETURN)==accepted and bytes(m[FB:FB+0x8000])==expected


@pytest.mark.parametrize('profile',PROFILES)
@pytest.mark.parametrize('speed',[0,500])
def test_full_twenty_point_pass_with_empty_previous_x_sentinels(original_image,memory,fields,profile,speed):
    m=memory;f=fields;prepare(original_image,m,f,profile,speed)
    vectors=[(16*(i-10),0,1024)for i in range(20)]
    for i,xyz in enumerate(vectors):
        for component,value in enumerate(xyz):word(m,f['point_field_world_positions']+6*i+2*component,value)
    put(m,REF_CURSOR,REFERENCE);put(m,POLY_CURSOR,PACKET);word(m,COUNT,0x1234)
    expected=bytearray(m[FB:FB+0x8000]);stride={'amiga':8192,'mode0':2,'mode1':0}[profile]
    if not fast(speed):
        for x,y,z in vectors:
            sx,sy=159+divide(x*128,z),79+divide(y*128,z)
            address=get(m,ROW_TABLE+2*sy,2)+get(m,X_OFFSETS+2*sx,2);mask=get(m,X_MASKS+2*sx,2)
            for plane in [0,2,3]:
                pos=address+plane*stride;value=int.from_bytes(expected[pos:pos+2],'big')&(~mask&65535)
                expected[pos:pos+2]=value.to_bytes(2,'big')
            pos=address+stride;value=int.from_bytes(expected[pos:pos+2],'big')|mask;expected[pos:pos+2]=value.to_bytes(2,'big')
    cpu=state(m,0x4E04A);run(original_image,m,cpu,{RETURN},limit=10000)
    assert bytes(m[FB:FB+0x8000])==expected
    assert bytes(m[f['point_field_previous_view_positions']:f['point_field_previous_view_positions']+120])==b''.join(struct.pack('>hhh',*v)for v in vectors)
    assert get(m,CURSOR)==f['point_field_previous_view_positions']+120
    assert get(m,REF_CURSOR)==REFERENCE and get(m,POLY_CURSOR)==PACKET and get(m,COUNT,2)==0x1234
    assert cpu.a[6]==APP and cpu.a[7]==STACK+4


@pytest.mark.parametrize('yaw',[0,1,512,1024,2048,4095])
@pytest.mark.parametrize('origin',[(0,0,0),(0x7FFFFFFF,0x80000000,0xFFFF0001)])
@pytest.mark.parametrize('seed',[(0,0),(0x12345678,0x90ABCDEF)])
def test_recycle_rewinds_same_point_and_clears_its_previous_view_only(original_image,memory,fields,yaw,origin,seed):
    m=memory;f=fields;prepare(original_image,m,f)
    world=f['point_field_world_positions'];previous=f['point_field_previous_view_positions']
    m[world:world+12]=b'\xA5'*12;m[previous:previous+12]=b'\x5A'*12
    for axis,value in zip('xyz',origin):put(m,f['player_world_'+axis],value)
    word(m,f['player_rotation_1'],yaw)
    put(m,f['sine_lookup_pointer'],0x13F60);put(m,f['cosine_lookup_pointer'],0x14760)
    put(m,f['shared_random_state_a'],seed[0]);put(m,f['shared_random_state_b'],seed[1])
    put(m,CURSOR,previous+6);put(m,APP+0x54,0xCAFEBABE)
    a,b=seed;values=[]
    for _ in range(3):a,b=rng(a,b);values.append((b&32767)-16384)
    y,z,x=values;sine=signed(get(m,0x13F60+2*yaw,2));cosine=signed(get(m,0x14760+2*yaw,2))
    x=shifted_product(x,cosine)+shifted_product(z,sine)
    # The Z calculation uses the original third random WORD, not the new X.
    z=shifted_product(z,cosine)-shifted_product(values[2],sine)
    expected=[(value+base)&65535 for value,base in zip([x,y,z],origin)]
    cpu=state(m,0x4E350);cpu.a[4]=world+6;cpu.d[7]=0
    run(original_image,m,cpu,{0x4E0AC},limit=1000)
    assert [get(m,world+2*i,2)for i in range(3)]==expected
    assert bytes(m[world+6:world+12])==b'\xA5'*6
    assert bytes(m[previous:previous+6])==bytes(6) and bytes(m[previous+6:previous+12])==b'\x5A'*6
    assert get(m,CURSOR)==previous and cpu.a[4]==world and cpu.d[7]==0
    assert get(m,f['shared_random_state_a'])==a and get(m,f['shared_random_state_b'])==b
    assert get(m,APP+0x54,2)==expected[1] and get(m,APP+0x56,2)==0xBABE
