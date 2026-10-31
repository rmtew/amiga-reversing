"""Original radial-disc arithmetic with explicit objects, queues and tables.

The root helper is not replaced by math.isqrt: its $10000 boundary and WORD
register restores remain observable. Supplied entry states do not establish
normal-game reachability, overflow-defined flags or universal queue lifetimes.
"""
import math
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,STACK,RETURN
from tests.test_starglider2_control_normalization import signed

OBJECT,RECORD,LIST=INPUT+0x400,INPUT+0x1000,INPUT+0x100
PRIMARY,SECONDARY,LAYER,FLAGS,DIRECTION=0x6BE2,0x6C0A,0x6C32,0x6C3A,0x7198
ROOTS=list(range(512))+[1023,1024,32767,32768,65535]
NORMS=sorted({r*r+d for r in ROOTS for d in [-1,0,1]if 0<=r*r+d<=0xFFFFFFFF}|{1572,1573,1574,65535,65536,65537,0x7FFFFFFF,0x80000000,0xC0000000,0xFFFFFFFF})


def word(m,p,v):put(m,p,v&65535,2)
def appword(m,p,v):word(m,APP+p,v)
def quotient(n,d):return(-1 if(n<0)!=(d<0)else 1)*(abs(n)//abs(d))
def s32(v):return signed(v,32)


@pytest.mark.parametrize('n',NORMS)
def test_original_root_boundaries_and_path_specific_register_restore(original_image,memory,n):
    m=memory;cpu=state(m,0x6B32);cpu.d[0]=n
    cpu.d[1:5]=[0x12348000,0xFEDC7FFF,0xA5A5FFFF,0x01010001]
    regs=list(cpu.d);addresses=list(cpu.a);expected=bytearray(m)
    run(original_image,m,cpu,{RETURN},limit=1000)
    expected_d0=65536 if n==65536 else math.isqrt(n)
    assert cpu.d[0]==expected_d0
    restored=[signed(v)&0xFFFFFFFF for v in regs[1:5]]if 1573<n<65536 else regs[1:5]
    assert list(cpu.d[1:5])==restored and list(cpu.d[5:])==regs[5:]
    assert list(cpu.a)[:7]==addresses[:7]and cpu.a[7]==STACK+4
    expected[STACK-16:STACK]=bytes(m[STACK-16:STACK]);assert bytes(m)==expected


@pytest.mark.parametrize('xyz',[(0,0,-32768),(1,-1,-1),(0,0,0),(0,0,1),(15,-15,16),(0,0,255),(0,0,256),(0,0,257),(-255,255,1024),(255,-255,32767)])
@pytest.mark.parametrize('shift',[0,1,14,16,31,32,63,65535])
def test_projection_prefix_preserves_word_wrap_and_supplies_squared_norm(original_image,memory,xyz,shift):
    m=memory;x,y,z=xyz
    for off,value in zip([22,24,26],xyz):word(m,OBJECT+off,value)
    word(m,OBJECT+44,shift);appword(m,0x194,32760);appword(m,0x196,-32760)
    m[RECORD:RECORD+10]=b'\xA5'*10
    cpu=state(m,0x68E2);cpu.a[4]=OBJECT;cpu.a[1]=RECORD;expected=bytearray(m)
    if z<=0:
        run(original_image,m,cpu,{0x6AF6});assert bytes(m)==expected;return
    px,py=quotient(x*128,z),quotient(y*128,z)
    depth=s32((z<<(shift&63))&0xFFFFFFFF)>>14
    word(expected,RECORD,depth);word(expected,RECORD+6,px+32760);word(expected,RECORD+8,py-32760)
    word(expected,OBJECT+38,px);word(expected,OBJECT+40,py)
    run(original_image,m,cpu,{0x694C});assert bytes(m)==expected
    assert cpu.d[0]==x*x+y*y+z*z


RADIUS_CASES=[(base,root,kind)for base in [0,1,100,2000,32767,0x10001,0xFFFF,0x80000000]for root in [1,2,16,39,256,32767,32768,65535]for kind in [128,146,147]if -32768<=quotient(signed(base)*144,signed(root))<=32767]
@pytest.mark.parametrize('base,root,kind',RADIUS_CASES)
def test_primary_radius_uses_signed_low_base_word_and_distinct_zero_rules(original_image,memory,base,root,kind):
    m=memory;put(m,OBJECT+34,base);word(m,OBJECT,kind)
    m[RECORD:RECORD+10]=b'\xA5'*10;word(m,OBJECT+42,0x5A5A)
    cpu=state(m,0x6950);cpu.a[4]=OBJECT;cpu.a[1]=RECORD;cpu.d[0]=root;expected=bytearray(m)
    q=quotient(signed(base)*144,signed(root))
    if q<0 or q==0 and kind==146:
        run(original_image,m,cpu,{0x6AF6});assert bytes(m)==expected;return
    radius=q or 1
    word(expected,OBJECT+42,radius);word(expected,RECORD+2,min(radius,1999));expected[0xE103]=0x68
    run(original_image,m,cpu,{0x6994});assert bytes(m)==expected
    assert cpu.d[4]&65535==radius


FAMILIES=[(128,0x80,i,0,3,0,0,14)for i in [-1,0,1,3,4]]+[(129,0x80,0,0,3,0,0,14),(144,0x80,0,0,3,0,0,14),(144,0x80,0,0,0,0,0,14),(145,0,0,0,3,0,0,14),(145,0,0,0,3,0,0,15),(145,0,0,0,3,1,0,14),(145,0,0,0,3,0,0x80,14),(145,0x80,0,0,3,0,0,14),(146,0x80,0,0,3,0,0,14),(146,0x80,0,0x80,3,0,0,14),(147,0x80,0,0,3,0,0,14)]


def emit(expected,cursor,ref,count,record):
    for i,value in enumerate(record):word(expected,cursor+2*i,value)
    count=(count+1)&65535
    if signed(count-94)<0:
        put(expected,ref,cursor);cursor+=10;ref+=4
    return cursor,ref,count


@pytest.mark.parametrize('family',FAMILIES)
@pytest.mark.parametrize('count',[0,92,93,94,65535])
def test_full_radial_producer_layers_and_failed_link_scratch_order(original_image,memory,family,count):
    kind,space,layer,expansion,station,ramp,atmosphere,shift=family;m=memory
    m[OBJECT:OBJECT+68]=b'\0'*68;word(m,OBJECT,kind)
    put(m,OBJECT+4,20000000);put(m,OBJECT+12,20000000);put(m,OBJECT+34,100)
    x,y,z=64,-32,640
    for off,value in zip([22,24,26],[x,y,z]):word(m,OBJECT+off,value)
    word(m,OBJECT+44,shift)
    if kind==146:m[OBJECT+20]=0xA4;m[OBJECT+21]=0xB5;m[OBJECT+31]=expansion
    if kind==147:word(m,OBJECT+16,0x7F1C)
    appword(m,0x194,159);appword(m,0x196,79);appword(m,0x7F8,count)
    appword(m,0x9CC,layer);appword(m,0x9C8,station);appword(m,0x9CA,ramp)
    m[APP+0x77D]=space;m[APP+0xBB7]=atmosphere;m[DIRECTION]=0x80
    put(m,APP+0x74,RECORD);put(m,APP+0x78,LIST);put(m,APP+0x9B4,0)
    m[RECORD:RECORD+100]=b'\xA5'*100;m[LIST:LIST+64]=b'\xCC'*64;m[FLAGS:FLAGS+20]=b'\xA5'*20
    cpu=state(m,0x67F4);cpu.a[4]=OBJECT;regs=list(cpu.d);addresses=list(cpu.a);expected=bytearray(m)
    put(expected,APP+0x7FA,PRIMARY);put(expected,APP+0x7FE,PRIMARY if kind==128 else SECONDARY)
    if kind!=128:expected[DIRECTION]=0
    expected[0xE103]=0x98
    if kind==144 and station==0:
        expected[FLAGS+kind-128]=255
    else:
        colour=get(m,PRIMARY+2*(kind-128),2)
        if kind==144:colour=station
        if kind==146 and expansion&128:colour=0xA4
        if kind==147:colour=0x7F1C
        px,py=quotient(x*128,z),quotient(y*128,z);norm=math.isqrt(x*x+y*y+z*z);radius=14400//norm;depth=(z<<shift)>>14
        for off,value in [(38,px),(40,py),(42,radius)]:word(expected,OBJECT+off,value)
        expected[0xE103]=0x68
        records=[(depth,min(radius,1999),colour,px+159,py+79)]
        if kind==128:
            if layer>=0:
                for i in range(layer,-1,-1):records.append((32767 if i>1 else depth+1+i,radius+i+1,get(m,LAYER+2*i,2),px+159,py+79))
        elif kind==145 and not space&128:
            if ramp==0 and not atmosphere&128:
                for i in [1,0]:records.append((norm+i+1,radius+i+1,get(m,LAYER+2*i,2),px+159,py+79))
        elif kind==146:records.append((depth+1,radius*2,0xB5 if expansion&128 else 11,px+159,py+79))
        elif kind!=147:
            dx=-((radius>>3)*px>>7);dy=-((radius>>3)*py>>7)
            records.append((depth+1,radius,get(m,SECONDARY+2*(kind-128),2),px+159+dx,py+79+dy))
        cursor,ref,n=RECORD,LIST,count
        for record in records:cursor,ref,n=emit(expected,cursor,ref,n,record)
        put(expected,APP+0x74,cursor);put(expected,APP+0x78,ref);appword(expected,0x7F8,n);expected[FLAGS+kind-128]=0
    run(original_image,m,cpu,{RETURN},limit=15000)
    expected[STACK-96:STACK+4]=bytes(m[STACK-96:STACK+4]);assert bytes(m)==expected
    assert list(cpu.d)==regs and list(cpu.a)[:7]==addresses[:7]and cpu.a[7]==STACK+4


@pytest.mark.parametrize('radius',[1,7,8,15,16,17,32767,32768,65535])
@pytest.mark.parametrize('direction',[0,127,128,255])
def test_secondary_disc_offsets_keep_word_shift_long_floor_and_direction_sign(original_image,memory,radius,direction):
    m=memory;word(m,OBJECT,129);word(m,OBJECT+42,radius);word(m,OBJECT+38,13);word(m,OBJECT+40,-15)
    appword(m,0x194,159);appword(m,0x196,79);appword(m,0x7F8,0);put(m,APP+0x74,RECORD+10);put(m,APP+0x78,LIST);put(m,APP+0x7FE,SECONDARY)
    word(m,RECORD,65535);m[DIRECTION]=direction
    cpu=state(m,0x6A30);cpu.a[4]=OBJECT;cpu.a[1]=RECORD;expected=bytearray(m)
    step=signed(radius)>>3;dx=(step*13)>>7;dy=(step*-15)>>7
    if not direction&128:dx=-dx;dy=-dy
    cursor,ref,count=emit(expected,RECORD+10,LIST,0,(0,radius,get(m,SECONDARY+2,2),13+159+dx,-15+79+dy))
    put(expected,APP+0x74,cursor);put(expected,APP+0x78,ref);appword(expected,0x7F8,count)
    run(original_image,m,cpu,{0x6AE0});expected[STACK-4:STACK]=bytes(m[STACK-4:STACK]);assert bytes(m)==expected


@pytest.mark.parametrize('kind',[128,129])
@pytest.mark.parametrize('delta_x,delta_z',[(0,0),(1,-1),(30000000,-50000000),(0x7FFFFFFF,0x80000000),(-20000000,20000000)])
@pytest.mark.parametrize('metric',[0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF])
@pytest.mark.parametrize('work_radius',[0,1,0x40000000])
def test_colour_order_metric_keeps_n_only_long_wrap_and_retained_direction(original_image,memory,kind,delta_x,delta_z,metric,work_radius):
    m=memory;word(m,OBJECT,kind);put(m,OBJECT+4,(20000000+delta_x)&0xFFFFFFFF);put(m,OBJECT+12,(20000000+delta_z)&0xFFFFFFFF)
    put(m,OBJECT+54,work_radius);put(m,APP+0x9B4,metric);m[DIRECTION]=0x80
    cpu=state(m,0x67F4);cpu.a[4]=OBJECT;expected=bytearray(m);expected[0xE103]=0x98
    first,second=PRIMARY,PRIMARY
    if kind!=128:
        dx=delta_x&0xFFFFFFFF;dz=delta_z&0xFFFFFFFF
        if s32(dx)<0:dx=(-dx)&0xFFFFFFFF
        if s32(dz)<0:dz=(-dz)&0xFFFFFFFF
        selected=dz if s32(dz-dx)>=0 else dx;value=(dx+dz+2*selected)&0xFFFFFFFF
        difference=(metric-value)&0xFFFFFFFF
        if s32(difference)<0:difference=(-difference)&0xFFFFFFFF
        if s32(difference-2*work_radius)>=0:
            if s32(metric-value)>=0:first,second=PRIMARY,SECONDARY;expected[DIRECTION]=0
            else:first,second=SECONDARY,PRIMARY;expected[DIRECTION]=255
    put(expected,APP+0x7FA,first);put(expected,APP+0x7FE,second)
    run(original_image,m,cpu,{0x6890});expected[STACK-60:STACK]=bytes(m[STACK-60:STACK]);assert bytes(m)==expected


def test_supplied_radial_entry_reaches_zero_divisor_at_norm_boundary(original_image,memory):
    m=memory;m[OBJECT:OBJECT+68]=b'\0'*68;word(m,OBJECT,128);word(m,OBJECT+26,256);word(m,OBJECT+44,14);put(m,OBJECT+34,100)
    put(m,APP+0x74,RECORD);put(m,APP+0x78,LIST);appword(m,0x194,159);appword(m,0x196,79)
    cpu=state(m,0x67F4);cpu.a[4]=OBJECT
    run(original_image,m,cpu,{0x6958},limit=1000)
    assert cpu.d[0]==65536 and cpu.d[0]&65535==0 and cpu.d[4]==14400
    assert original_image[0][0x5958:0x595A]==bytes.fromhex('89c0')  # DIVS.W D0,D4, not executed by this fixture.
    assert get(m,RECORD,2)==256 and get(m,APP+0x7F8,2)==0


@pytest.mark.parametrize('radius',[1,16383,16384,32767,32768,65535])
@pytest.mark.parametrize('expansion',[0,127,128])
def test_spheroid_outer_word_doubling_keeps_conditional_zero_alias(original_image,memory,radius,expansion):
    m=memory;word(m,OBJECT,146);m[OBJECT+31]=expansion;m[OBJECT+21]=0xB5
    word(m,OBJECT+38,13);word(m,OBJECT+40,-15)
    appword(m,0x194,159);appword(m,0x196,79);appword(m,0x7F8,0);put(m,APP+0x74,RECORD);put(m,APP+0x78,LIST)
    cpu=state(m,0x6AA4);cpu.a[4]=OBJECT;cpu.a[1]=RECORD;cpu.d[3]=radius;expected=bytearray(m)
    word(expected,RECORD+2,radius*2);word(expected,RECORD+4,0xB5 if expansion&128 else 11)
    word(expected,RECORD+6,172);word(expected,RECORD+8,64)
    put(expected,LIST,RECORD);put(expected,APP+0x74,RECORD+10);put(expected,APP+0x78,LIST+4);appword(expected,0x7F8,1)
    run(original_image,m,cpu,{0x6AE0});expected[STACK-4:STACK]=bytes(m[STACK-4:STACK]);assert bytes(m)==expected
    if radius==32768:assert get(m,RECORD+2,2)==0  # Direct-stage input; primary in-range division rejects this signed value.
