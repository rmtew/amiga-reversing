"""Original HUD projection and CPU plane writes with explicit table backing.

These are bounded continuation cases, not scanout/timing or arbitrary polygon
safety proofs. Raw alternative kernels without an incoming edge stay raw.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,STACK
from tests.test_starglider2_control_normalization import signed,word

SINE,COS=0x13F60,0x14760
VECTORS,CORNERS,CYCLE=0x3A0B8,0x3A0D6,0x3A134
WORK,LEFT,RIGHT=0x41848,0x3A24C,0x3A1CC
MODE,ROLL=0x3A2CE,0x3A2D0
PLANE1,PLANE2=0x716E6,0x736E6


def write(m,address,value,width=4):put(m,address,value&((1<<(8*width))-1),width)
def product(a,b):return signed((signed(a)*signed(b)*4)>>16)
def quotient(n,d):return(-1 if(n<0) != (d<0)else 1)*(abs(n)//abs(d))


def projected(m,pitch,view_roll,amiga):
    s0,c0=[get(m,p+2*(pitch&4095),2)for p in [SINE,COS]]
    s2,c2=[get(m,p+2*((-view_roll)&4095),2)for p in [SINE,COS]]
    out=[]
    for i in range(4):
        x,y,z=[get(m,VECTORS+6*i+2*j,2)for j in range(3)]
        yy=signed(product(y,c0)+product(z,s0));zz=signed(product(z,c0)-product(y,s0))
        xx=signed(product(x,c2)+product(yy,s2));yy=signed(product(yy,c2)-product(x,s2))
        depth=zz+45
        px=quotient(signed(xx+19)*25,signed(depth))if depth else xx+19
        py=quotient(signed(yy+70)*25,signed(depth))if depth else yy+70
        out.append(((px+(4 if amiga else 180))&65535,(py+(-25 if amiga else 121))&65535))
    return out,[s0,c0,s2,c2]


@pytest.mark.parametrize('pitch',[0,1,511,1024,2047,2048,3072,65535])
@pytest.mark.parametrize('view_roll',range(0,4096,128))
@pytest.mark.parametrize('amiga',[False,True])
def test_four_original_vectors_use_view_angles_and_platform_translation(original_image,memory,pitch,view_roll,amiga):
    m=memory;put(m,APP+0x44,SINE);put(m,APP+0x48,COS)
    word(m,0x7B6,pitch);word(m,0x7BA,view_roll);word(m,0x748,view_roll^0x5A5A)
    put(m,0x1002,0x8000 if amiga else 0,2)
    points,scratch=projected(m,pitch,view_roll,amiga)
    cpu=state(m,0x39D70);expected=bytearray(m)
    put(expected,ROLL,(view_roll^0x5A5A)&4095,2)
    for i,(x,y)in enumerate(points):put(expected,CORNERS+4*i,x,2);put(expected,CORNERS+4*i+2,y,2)
    put(expected,CORNERS+16,65535,2)
    for off,value in zip([0x164,0x166,0x16C,0x16E],scratch):put(expected,APP+off,value,2)
    run(original_image,m,cpu,{0x39E2C if amiga else 0x3A0B2})
    # Original MOVEM and real calls leave saved registers/return words on stack.
    expected[STACK-96:STACK+4]=bytes(m[STACK-96:STACK+4])
    assert bytes(m)==expected
    assert cpu.a[7]==STACK-60 and cpu.d[7]&65535==65535


@pytest.mark.parametrize('roll',[0,831,832,2880,2881,4095,65535])
@pytest.mark.parametrize('old_mode',[0,1,2])
@pytest.mark.parametrize('first_row',[-1,0,1,31,32,33,34])
@pytest.mark.parametrize('spans',[[(0,31)],[(1,15),(15,30)],[(31,32)]])
def test_plane_switch_clear_span_masks_and_unclipped_leading_rows(original_image,memory,roll,old_mode,first_row,spans):
    m=memory;put(m,ROLL,roll,2);put(m,MODE,old_mode,2)
    for i,(left,right)in enumerate(spans):put(m,WORK+4*i,left,2);put(m,WORK+4*i+2,right,2)
    cpu=state(m,0x39FE4);cpu.a[6]=WORK+4*len(spans);cpu.d[7]=first_row&65535
    expected=bytearray(m);put(expected,WORK+4*len(spans),65535,2)
    mode=2 if 832<roll<=2880 else 1
    active,opposite=(PLANE1,PLANE2)if mode==1 else(PLANE2,PLANE1)
    if old_mode!=mode:
        for row in range(33):put(expected,opposite+40*row,0)
        put(expected,MODE,mode,2)
    # The preclear precedes the end-pointer test; rows33/34 retain overshoot.
    leading=max(first_row,0)
    for row in range(leading):put(expected,active+40*row,0)
    for row in range(leading,33):
        i=row-leading;value=0
        if i<len(spans):
            left,right=spans[i]
            # Index31 in the 31-LONG left prefix aliases the edge scratch pair.
            value=get(m,LEFT+4*left)&get(m,RIGHT+4*right)
        put(expected,active+40*row,value)
    run(original_image,m,cpu,{0x3A0B2});assert bytes(m)==expected


@pytest.mark.parametrize('shift',range(4))
@pytest.mark.parametrize('left,right',[(0,31),(4,20),(15,15),(15,16),(30,31)])
@pytest.mark.parametrize('top,bottom',[(0,1),(2,7),(31,32)])
def test_rectangle_cycle_retains_first_minimum_and_inclusive_span_rows(original_image,memory,shift,left,right,top,bottom):
    m=memory;points=[(left,top),(right,top),(right,bottom),(left,bottom)]
    points=points[shift:]+points[:shift]
    for i,(x,y)in enumerate(points):put(m,CORNERS+4*i,x,2);put(m,CORNERS+4*i+2,y,2)
    put(m,CORNERS+16,65535,2);put(m,CORNERS+18,0x5678,2)
    cpu=state(m,0x39E2C);expected=bytearray(m)
    first=min(range(4),key=lambda i:points[i][1]);ordered=points[first:]+points[:first]
    for i,(x,y)in enumerate(ordered):put(expected,CYCLE+4*i,x,2);put(expected,CYCLE+4*i+2,y,2)
    put(expected,CYCLE+16,0)
    for row in range(bottom-top+1):put(expected,WORK+4*row,left+int(left==right),2);put(expected,WORK+4*row+2,right,2)
    put(expected,0x3A2C8,left,2);put(expected,0x3A2CA,left,2)
    run(original_image,m,cpu,{0x39FE4},limit=1000)
    assert bytes(m)==expected
    assert cpu.a[6]==WORK+4*(bottom-top+1) and cpu.d[7]&65535==top


@pytest.mark.parametrize('xs',[(2,25,20,5),(5,20,25,2),(0,31,31,1),(3,21,30,12)])
@pytest.mark.parametrize('height',[1,2,5,17,31])
def test_sloped_edges_use_reciprocal_of_inclusive_height_and_staged_fixed_point(original_image,memory,xs,height):
    m=memory;left0,right0,right1,left1=xs;top=2
    points=[(left0,top),(right0,top),(right1,top+height),(left1,top+height)]
    for i,(x,y)in enumerate(points):put(m,CORNERS+4*i,x,2);put(m,CORNERS+4*i+2,y,2)
    put(m,CORNERS+16,65535,2)
    cpu=state(m,0x39E2C);scale=signed(get(m,0x4B99E+2*(height+1),2))
    step_left=(left1-left0)*scale*2;step_right=(right1-right0)*scale*2
    run(original_image,m,cpu,{0x39FE4},limit=2000)
    expected=[]
    for j in range(1,height+2):
        endpoints=[((left0*65536+j*step_left)>>16)&65535,((right0*65536+j*step_right)>>16)&65535]
        expected.append(tuple(sorted(endpoints)))
    actual=[(get(m,WORK+4*i,2),get(m,WORK+4*i+2,2))for i in range(height+1)]
    assert actual==expected and cpu.a[6]==WORK+4*(height+1)


@pytest.mark.parametrize('shift',range(4))
@pytest.mark.parametrize('y',[0,31,4094])
def test_flat_row_uses_unsigned_x_extrema_and_bypasses_plane_address_setup(original_image,memory,shift,y):
    m=memory;xs=[0,31,3,17];xs=xs[shift:]+xs[:shift]
    for i,x in enumerate(xs):put(m,CORNERS+4*i,x,2);put(m,CORNERS+4*i+2,y,2)
    put(m,CORNERS+16,65535,2)
    cpu=state(m,0x39E2C);expected=bytearray(m)
    for i,x in enumerate(xs):put(expected,CYCLE+4*i,x,2);put(expected,CYCLE+4*i+2,y,2)
    put(expected,CYCLE+16,0);put(expected,WORK,0,2);put(expected,WORK+2,31,2);put(expected,WORK+4,65535,2)
    run(original_image,m,cpu,{0x3A062},limit=1000);assert bytes(m)==expected
    assert cpu.a[0]==CYCLE+16 and cpu.a[4]==0x4B99E
    assert cpu.d[7]&65535==y


@pytest.mark.parametrize('roll',[0,833,2880])
@pytest.mark.parametrize('old_mode',[0,1,2])
def test_original_entry_connects_projection_spans_plane_and_saved_return(original_image,memory,roll,old_mode):
    m=memory;put(m,APP+0x44,SINE);put(m,APP+0x48,COS)
    word(m,0x7B6,0);word(m,0x7BA,0);word(m,0x748,roll);put(m,MODE,old_mode,2)
    points,scratch=projected(m,0,0,True)
    top=min(y for x,y in points);bottom=max(y for x,y in points)
    left0,right0=sorted(x for x,y in points if y==top);left1,right1=sorted(x for x,y in points if y==bottom)
    scale=signed(get(m,0x4B99E+2*(bottom-top+1),2))
    spans=[(left0+((j*(left1-left0)*scale*2)>>16),right0+((j*(right1-right0)*scale*2)>>16))for j in range(1,bottom-top+2)]
    cpu=state(m,0x39D70);regs=list(cpu.d);addresses=list(cpu.a);expected=bytearray(m)
    put(expected,ROLL,roll,2)
    for i,(x,y)in enumerate(points):put(expected,CORNERS+4*i,x,2);put(expected,CORNERS+4*i+2,y,2)
    put(expected,CORNERS+16,65535,2)
    for off,value in zip([0x164,0x166,0x16C,0x16E],scratch):put(expected,APP+off,value,2)
    for i,(x,y)in enumerate(points):put(expected,CYCLE+4*i,x,2);put(expected,CYCLE+4*i+2,y,2)
    put(expected,CYCLE+16,0)
    for i,(left,right)in enumerate(spans):put(expected,WORK+4*i,left,2);put(expected,WORK+4*i+2,right,2)
    put(expected,WORK+4*len(spans),65535,2);put(expected,0x3A2C8,left1,2);put(expected,0x3A2CA,left1,2)
    mode=1 if roll==0 else 2;active,opposite=(PLANE1,PLANE2)if mode==1 else(PLANE2,PLANE1)
    if mode!=old_mode:
        for row in range(33):put(expected,opposite+40*row,0)
        put(expected,MODE,mode,2)
    for row in range(33):
        i=row-top;value=0
        if 0<=i<len(spans):
            left,right=spans[i];value=get(expected,LEFT+4*left)&get(expected,RIGHT+4*right)
        put(expected,active+40*row,value)
    from tests.test_starglider2_text_editor import RETURN
    run(original_image,m,cpu,{RETURN},limit=5000)
    expected[STACK-96:STACK+4]=bytes(m[STACK-96:STACK+4])
    assert bytes(m)==expected
    assert list(cpu.d)==regs and list(cpu.a)[:7]==addresses[:7]and cpu.a[7]==STACK+4


@pytest.mark.parametrize('dx',[-7,-1,0,1,7])
@pytest.mark.parametrize('height',[1,5,17])
def test_matching_edges_retain_directional_tail_bounds(original_image,memory,dx,height):
    m=memory;x0=15;x1=x0+dx;top=2
    for i,(x,y)in enumerate([(x0,top),(x0,top),(x1,top+height),(x1,top+height)]):
        put(m,CORNERS+4*i,x,2);put(m,CORNERS+4*i+2,y,2)
    put(m,CORNERS+16,65535,2)
    cpu=state(m,0x39E2C);step=dx*signed(get(m,0x4B99E+2*(height+1),2))*2
    expected=[]
    for j in range(1,height+2):
        old=((x0*65536+(j-1)*step)>>16)&65535;new=((x0*65536+j*step)>>16)&65535
        expected.append((new,(old-1)&65535)if step<0 else((old+1)&65535,new))
    run(original_image,m,cpu,{0x39FE4},limit=2000)
    assert[(get(m,WORK+4*i,2),get(m,WORK+4*i+2,2))for i in range(height+1)]==expected
    assert cpu.a[6]==WORK+4*(height+1)
