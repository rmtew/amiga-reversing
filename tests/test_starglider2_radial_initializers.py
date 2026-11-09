"""Original radial initializers with supplied types, PRNG state and lookup RAM.

Check original arithmetic, partial field writes and register restoration. These
are not proofs of caller type bounds, normal-game state, uniform distributions,
physical units, complete startup or rendered-star/hardware equivalence.
"""
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT,STACK,RETURN
from tests.test_starglider2_motion_integration import tables,expected_vector
from tests.test_starglider2_palette_priority import rng

NAMES=['initialize_star_radius_position_and_colour','initialize_celestial_body_radius_and_y',
 'initialize_shared_radial_object','nonmodel_object_base_radii','SG2RadialObject_base_radius',
 'SG2RadialObject_radius_work_value','SG2StarObject_primary_colour_index','SG2ObjectCore_durability_or_negative']


@pytest.fixture(scope='module')
def symbols(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder=tmp_path_factory.mktemp('radial-initializers');asm,out=folder/'symbols.s',folder/'symbols.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(NAMES)+'\n')
    r=subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,text=True,capture_output=True)
    assert r.returncode==0,r.stdout+r.stderr
    data=out.read_bytes();size=4*len(NAMES);assert data[:-size]==original_image[0]
    return dict(zip(NAMES,struct.unpack('>'+'I'*len(NAMES),data[-size:])))


def set_field(expected,offset,value,width=4):expected[offset:offset+width]=(value&((1<<(8*width))-1)).to_bytes(width,'big')


@pytest.mark.parametrize('incoming_d3',[0,1,4095,4096,65535,0x12345678])
@pytest.mark.parametrize('seed',[(0,0),(0x12345678,0x90ABCDEF),(0xFFFFFFFF,0x80000000),(0x80000001,7)])
def test_star_uses_inherited_magnitude_and_four_prng_advances(original_image,tables,symbols,incoming_d3,seed):
    m=tables;f=symbols;m[INPUT:INPUT+68]=b'\xCC'*68;put(m,INPUT,147,2)
    m[INPUT+f['SG2ObjectCore_durability_or_negative']]=0x35
    expected=bytearray(m[INPUT:INPUT+68]);a,b=seed
    put(m,APP+0x60,a);put(m,APP+0x64,b)
    values=[]
    for _ in range(4):a,b=rng(a,b);values.append(b)
    angles=[((values[0]&511)-256)&4095,values[1]&4095,0]
    magnitude=(incoming_d3&4095)+20480
    vector,_=expected_vector(m,angles,magnitude)
    coordinates=[(((v&65535)if not(v&32768)else(v&65535)-65536)*8192+origin)&0xFFFFFFFF
                 for v,origin in zip(vector,[20000000,-20000000,20000000])]
    radius=get(m,f['nonmodel_object_base_radii']+4*(147-128))
    for key in ['SG2RadialObject_base_radius','SG2RadialObject_radius_work_value']:set_field(expected,f[key],radius)
    for off,value in zip([4,8,12],coordinates):set_field(expected,off,value)
    palette=[0,3,0,3,0,1,0,1];set_field(expected,f['SG2StarObject_primary_colour_index'],palette[values[3]&7],2)
    expected[f['SG2ObjectCore_durability_or_negative']]|=128
    cpu=state(m,f['initialize_star_radius_position_and_colour']);cpu.a[0]=INPUT;cpu.d[3]=incoming_d3
    saved_d=list(cpu.d);saved_a=list(cpu.a)
    run(original_image,m,cpu,{RETURN})
    assert bytes(m[INPUT:INPUT+68])==expected
    assert (get(m,APP+0x60),get(m,APP+0x64))==(a,b)
    assert list(cpu.d[3:7])==saved_d[3:7]
    assert [cpu.a[i]for i in [0,1,2,3,4,5,6]]==saved_a[:7] and cpu.a[7]==STACK+4


@pytest.mark.parametrize('kind',range(128,145))
def test_celestial_radius_and_y_leave_unassigned_bytes_and_registers(original_image,memory,symbols,kind):
    m=memory;f=symbols;m[INPUT:INPUT+68]=b'\x35'*68;put(m,INPUT,kind,2)
    expected=bytearray(m[INPUT:INPUT+68]);radius=get(m,f['nonmodel_object_base_radii']+4*(kind-128))
    for key in ['SG2RadialObject_base_radius','SG2RadialObject_radius_work_value']:set_field(expected,f[key],radius)
    set_field(expected,8,-20000000);expected[f['SG2ObjectCore_durability_or_negative']]|=128
    cpu=state(m,f['initialize_celestial_body_radius_and_y']);cpu.a[0]=INPUT;saved=list(cpu.a)
    run(original_image,m,cpu,{RETURN})
    assert bytes(m[INPUT:INPUT+68])==expected
    assert list(cpu.a[:7])==saved[:7] and cpu.a[7]==STACK+4


@pytest.mark.parametrize('kind',[145,146])
def test_shared_radial_initializer_preserves_other_overlay_bytes(original_image,memory,symbols,kind):
    m=memory;f=symbols;m[INPUT:INPUT+68]=b'\x35'*68;put(m,INPUT,kind,2)
    expected=bytearray(m[INPUT:INPUT+68]);radius=get(m,f['nonmodel_object_base_radii']+4*(kind-128))
    for key in ['SG2RadialObject_base_radius','SG2RadialObject_radius_work_value']:set_field(expected,f[key],radius)
    set_field(expected,8,-100000);expected[f['SG2ObjectCore_durability_or_negative']]|=128;expected[2]|=16
    cpu=state(m,f['initialize_shared_radial_object']);cpu.a[0]=INPUT;saved=list(cpu.a)
    run(original_image,m,cpu,{RETURN})
    assert bytes(m[INPUT:INPUT+68])==expected
    assert list(cpu.a[:7])==saved[:7] and cpu.a[7]==STACK+4
