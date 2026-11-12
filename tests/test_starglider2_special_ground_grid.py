"""Original 6x6 ground mesh, projection and checkerboard packet paths.

Explicit scratch/coordinate inputs do not establish arena lifetime/capacity,
normal-game reachability, clipping completeness or hardware rendering.
"""
import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, STACK, RETURN
from tests.test_starglider2_radial_callers import offsets
from tests.test_starglider2_horizon_grid_math import signed, swap

ORIGIN, XSTEP, ZSTEP, XEDGE, ZEDGE = 0x2F554, 0x2F52E, 0x2F534, 0x2F53A, 0x2F540
DIRECTORY, PROJECTED, PHASE, MATERIAL = 0x2F57C, 0x4B35E, 0x2F57A, 0x2F522
CANDIDATES, COUNT, REFS_CURSOR, PACKET_CURSOR = 0x52BE, 0x49A8, 0x3C2C, 0x3C30
PACKETS, REFS = 0x84000, 0x83000


def word(m, p, value):
    put(m, p, value & 65535, 2)


def triples(m, p, values):
    for j, v in enumerate(values):
        word(m, p + 2*j, v)


@pytest.mark.parametrize('flags',[0,2,255])
@pytest.mark.parametrize('height',[-8001,-8000,-7999,0,0x7FFFFFFF,0x80000000])
def test_grid_entry_keeps_flag_gate_and_n_only_long_subtraction(original_image,memory,flags,height):
    m=memory;raw=original_image[0]
    m[APP+get(raw,0x2F01C-4096,2)]=flags
    put(m,APP+get(raw,0x2F024-4096,2),height&0xFFFFFFFF)
    before=bytes(m[APP:APP+0x800]);word(m,CANDIDATES,0xA55A)
    admitted=bool(flags&2)and((height+8000)&0xFFFFFFFF)<0x80000000
    cpu=state(m,0x2F018)
    run(original_image,m,cpu,{RETURN,0x2F02E})
    assert cpu.pc==(0x2F02E if admitted else RETURN)
    assert bytes(m[APP:APP+0x800])==before and get(m,CANDIDATES,2)==0xA55A


@pytest.mark.parametrize('seed', [0, 0xA5, 255])
def test_quad_directory_is_25_ordered_cells_of_six_by_six_vertex_grid(original_image, memory, seed):
    m = memory
    m[DIRECTORY-2:DIRECTORY+202] = bytes([seed])*204
    cpu = state(m, 0x2F4F8)
    run(original_image, m, cpu, {RETURN})
    actual = [get(m, DIRECTORY+2*i, 2) for i in range(100)]
    expected = [8*v for row in range(5) for col in range(5)
                for v in [6*row+col, 6*row+col+1, 6*(row+1)+col+1, 6*(row+1)+col]]
    assert actual == expected and max(actual) == 35*8
    assert bytes(m[DIRECTORY-2:DIRECTORY]) == bytes([seed])*2
    assert bytes(m[DIRECTORY+200:DIRECTORY+202]) == bytes([seed])*2
    assert cpu.a[0] == DIRECTORY+200 and cpu.a[7] == STACK+4


@pytest.mark.parametrize('origin,xstep,zstep,xedge,zedge', [
    ((0,0,0), (4096,0,0), (0,0,4096), (0,0,0), (0,0,0)),
    ((32767,-32768,100), (32767,-32768,-1), (-32768,32767,2), (10,-20,30), (-40,50,-60)),
    ((-123,456,-789), (33,-57,81), (17,29,-43), (-7,8,-9), (11,-12,13)),
])
@pytest.mark.parametrize('seed', [0, 0xA5, 255])
def test_grid_writes_36_strided_xyz_records_with_outer_edge_adjustments(original_image, memory, origin, xstep, zstep, xedge, zedge, seed):
    m = memory
    # Evaluate the original LEA's canonical app displacement, not a second layout.
    raw = original_image[0]
    start = APP + signed(get(raw, 0x2F166-4096, 2))
    m[start-2:start+290] = bytes([seed])*292
    for address, values in [(ORIGIN,origin),(XSTEP,xstep),(ZSTEP,zstep),(XEDGE,xedge),(ZEDGE,zedge)]:
        triples(m,address,values)
    expected = bytearray(m[start-2:start+290])
    for row in range(6):
        for col in range(6):
            values = [origin[j] + row*zstep[j] + col*xstep[j]
                      + (zedge[j] if row == 0 else zedge[j]-zstep[j] if row == 5 else 0)
                      + (xedge[j] if col == 0 else xedge[j]-xstep[j] if col == 5 else 0)
                      for j in range(3)]
            for j,v in enumerate(values):
                at = 2+8*(6*row+col)+2*j
                expected[at:at+2] = (v&65535).to_bytes(2,'big')
    cpu = state(m,0x2F164)
    run(original_image,m,cpu,{0x2F23E})
    assert bytes(m[start-2:start+290]) == expected
    assert cpu.a[0] == start+288 and cpu.a[7] == STACK
    assert cpu.d[0]&65535 == 65535


@pytest.mark.parametrize('xyz', [(0,0,-32768),(3,-4,-1),(1,2,0),(11,22,128),
                                (100,-200,129),(32767,-32768,256),(91,-37,8223),
                                (91,-37,8224),(32767,-32768,32767)])
@pytest.mark.parametrize('seed', [0,0xA5])
def test_projection_keeps_near_stale_coordinates_padding_and_far_division_path(original_image,memory,offsets,xyz,seed):
    m = memory;raw = original_image[0];o = offsets
    source = APP+signed(get(raw,0x2F244-4096,2))
    table = get(raw,0x2F24E-4096)
    for i in range(36):triples(m,source+8*i,xyz)
    m[PROJECTED-2:PROJECTED+290] = bytes([seed])*292
    expected = bytearray(m[PROJECTED-2:PROJECTED+290])
    for name,v in [('projection_screen_origin_x',159),('projection_screen_origin_y',79),
                   ('view_clip_min_x',16),('view_clip_max_x',303),
                   ('view_clip_min_y',30),('view_clip_max_y',128)]:word(m,APP+o[name],v)
    x,y,z=xyz
    if z>128:
        if z<8224:
            scale=signed(get(m,table+(z&65534),2))
            px,py=[signed(swap(v*scale*2))for v in [x,y]]
            depth=z&65534
        else:
            px,py=[(abs(v*128)//z)*(-1 if v<0 else 1)for v in [x,y]]
            depth=z
        px,py=signed(px+159),signed(py+79)
        clip=(px<16)+2*(px>303)+4*(py<30)+8*(py>128)
    else:clip=128
    for i in range(36):
        at=2+8*i
        if z>128:
            expected[at:at+6]=b''.join((v&65535).to_bytes(2,'big')for v in [px,py,depth])
        expected[at+6]=clip
    cpu=state(m,0x2F23E)
    run(original_image,m,cpu,{0x2F2D8})
    assert bytes(m[PROJECTED-2:PROJECTED+290])==expected
    assert cpu.a[3]==source+288 and cpu.a[4]==PROJECTED+288 and cpu.a[7]==STACK


def setup_packets(image,m,phase):
    cpu=state(m,0x2F4F8);run(image,m,cpu,{RETURN})
    for i in range(36):
        triples(m,PROJECTED+8*i,(10+i,20+i,1000+i))
        word(m,PROJECTED+8*i+6,0)
    m[PACKETS-4:PACKETS+600]=b'\xCC'*604
    m[REFS-4:REFS+120]=b'\xA5'*124
    put(m,PACKET_CURSOR,PACKETS);put(m,REFS_CURSOR,REFS)
    word(m,PHASE,phase);word(m,MATERIAL,9);word(m,CANDIDATES,25);word(m,COUNT,7)
    return state(m,0x2F2D8)


@pytest.mark.parametrize('phase',[0,65535])
def test_checkerboard_fast_path_emits_alternating_quads_and_preserves_skip_header_write(original_image,memory,phase):
    m=memory;cpu=setup_packets(original_image,m,phase)
    expected=bytearray(m[PACKETS-4:PACKETS+600]);refs=[];cursor=PACKETS
    for i in range(25):
        phase=(~phase)&65535
        at=cursor-PACKETS+4
        expected[at:at+2]=bytes.fromhex('7ff0')
        if phase:
            vertices=[get(m,DIRECTORY+8*i+2*j,2)for j in range(4)]
            packet=bytes.fromhex('7ff00009')+b''.join(bytes(m[PROJECTED+v:PROJECTED+v+4])for v in vertices)+b'\xFF\xFF'
            expected[at:at+len(packet)]=packet
            refs.append(cursor);cursor+=len(packet)
    run(original_image,m,cpu,{RETURN})
    assert bytes(m[PACKETS-4:PACKETS+600])==expected
    assert [get(m,REFS+4*i)for i in range(len(refs))]==refs
    assert bytes(m[REFS-4:REFS])==b'\xA5'*4
    assert bytes(m[REFS+4*len(refs):REFS+120])==b'\xA5'*(120-4*len(refs))
    assert get(m,PACKET_CURSOR)==cursor and get(m,REFS_CURSOR)==REFS+4*len(refs)
    assert get(m,COUNT,2)==7+len(refs) and get(m,CANDIDATES,2)==0
    assert cpu.a[7]==STACK+4


@pytest.mark.parametrize('corner,forces_fallback',[(0,True),(1,True),(2,False),(3,False)])
def test_first_two_fast_clip_tests_read_padding_byte_but_last_two_do_not(original_image,memory,corner,forces_fallback):
    m=memory;cpu=setup_packets(original_image,m,0)
    vertex=get(m,DIRECTORY+2*corner,2)
    m[PROJECTED+vertex+7]=1
    run(original_image,m,cpu,{0x2F370,0x2F4D4})
    assert cpu.pc==(0x2F370 if forces_fallback else 0x2F4D4)
    assert get(m,COUNT,2)==(7 if forces_fallback else 8)


@pytest.mark.parametrize('clip',[1,2,4,8])
def test_shared_side_outcode_rejects_quad_before_clipper_without_publishing_reference(original_image,memory,clip):
    m=memory;cpu=setup_packets(original_image,m,0)
    for i in range(36):m[PROJECTED+8*i+6]=clip
    refs=bytes(m[REFS-4:REFS+120])
    run(original_image,m,cpu,{0x2F4D4})
    assert get(m,COUNT,2)==7 and cpu.a[3]==REFS and cpu.a[4]==PACKETS
    assert bytes(m[REFS-4:REFS+120])==refs
    # The speculative header/material stores are not rolled back.
    assert bytes(m[PACKETS:PACKETS+4])==bytes.fromhex('7ff00009')
    assert cpu.a[7]==STACK


def test_near_flag_builds_four_xyz_inputs_then_calls_real_clipping_bridge(original_image,memory):
    m=memory;cpu=setup_packets(original_image,m,0);raw=original_image[0]
    source=APP+signed(get(raw,0x2F244-4096,2))
    for i in range(36):triples(m,source+8*i,(10+i,20+i,100+i))
    vertices=[get(m,DIRECTORY+2*j,2)for j in range(4)]
    for v in vertices:m[PROJECTED+v+6]=128
    expected=b'\x00\x09'+b''.join(bytes(m[source+v:source+v+6])for v in vertices)
    bridge=0x2F430+signed(get(raw,0x2F430-4096,2))
    run(original_image,m,cpu,{bridge})
    assert bytes(m[0x52C0:0x52C0+26])==expected
    assert cpu.a[2]==0x52C2 and cpu.d[7]==4 and get(m,COUNT,2)==7
    assert cpu.a[3]==REFS and cpu.a[4]==PACKETS
    assert get(m,STACK-16)==0x2F432  # Original return after the clipper bridge.


@pytest.mark.parametrize('depth',[0,1,100,16383,16384,32767,32768,40000,65535])
@pytest.mark.parametrize('failed_vertex',[0,2])
def test_clipped_projection_keeps_add_overflow_branch_and_partial_rollback(original_image,memory,offsets,depth,failed_vertex):
    m=memory;cpu=setup_packets(original_image,m,0);o=offsets
    source=0x88000
    vertices=[(10,20,100)]*4
    vertices[failed_vertex]=(-20,-10,depth)
    for i,xyz in enumerate(vertices):triples(m,source+6*i,xyz)
    word(m,0x52C0,9);word(m,CANDIDATES,1)
    for name,v in [('projection_screen_origin_x',159),('projection_screen_origin_y',79),
                   ('view_clip_min_x',16),('view_clip_max_x',303),
                   ('view_clip_min_y',30),('view_clip_max_y',128)]:word(m,APP+o[name],v)
    expected=bytearray(m[PACKETS-4:PACKETS+600]);packet=bytearray.fromhex('7ff00009')
    rejected=False
    for x,y,z in vertices:
        divisor=signed(2*z)
        # BLE consumes ADD.W's V as well as N/Z, not a fresh TST of its result.
        if signed(z)<=0:
            rejected=True
            break
        px,py=[(abs(v*scale)//abs(divisor))*(-1 if (v<0)!=(divisor<0) else 1)for v,scale in [(x,288),(y,98)]]
        px,py=signed(px+159),signed(py+79)
        px,py=max(16,min(303,px)),max(30,min(128,py))
        packet+=b''.join(v.to_bytes(2,'big')for v in [px,py])
    if not rejected:packet+=b'\xFF\xFF'
    expected[4:4+len(packet)]=packet
    cpu.pc=0x2F462;cpu.a[2]=source;cpu.a[3]=REFS;cpu.a[4]=PACKETS;cpu.d[7]=4
    run(original_image,m,cpu,{RETURN})
    assert bytes(m[PACKETS-4:PACKETS+600])==expected
    # The reference slot is written before projection, even on later rollback.
    assert get(m,REFS)==PACKETS and get(m,REFS_CURSOR)==REFS+(0 if rejected else 4)
    assert get(m,PACKET_CURSOR)==PACKETS+(0 if rejected else len(packet))
    assert get(m,COUNT,2)==7+(not rejected) and cpu.a[7]==STACK+4
