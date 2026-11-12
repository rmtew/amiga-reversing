"""Original queued-object motion gates shared by the two frame-service paths.

Supplied list/records and bounded intra-handler entries do not prove interrupt
arrival, frame timing, list lifetime or coverage of every partition caller.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,STACK

PARTITION,LIST,OBJECT = 0x49AA,0x84000,0x85000
NAMES = ['modal_command_input_flag','integrating_object_count','integrating_objects_cursor',
         'horizontal_world_wrap_mask']


@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('interrupt-motion');asm,out = folder/'fields.s',folder/'fields.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(NAMES)+'\n')
    result = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-m68000',
        '-no-opt','-Fbin','-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,
        capture_output=True,text=True)
    assert result.returncode == 0,result.stdout+result.stderr
    raw = out.read_bytes();assert raw[:-4*len(NAMES)] == original_image[0]
    return {n:APP+v for n,v in zip(NAMES,struct.unpack('>'+'I'*len(NAMES),raw[-4*len(NAMES):]))}


@pytest.mark.parametrize('entry,stop',[(0xC82C,0xC876),(0x3B2C2,0x3B30C)])
@pytest.mark.parametrize('modal',[0,1,128,255])
@pytest.mark.parametrize('partition',[0,1,128,255])
@pytest.mark.parametrize('count',[0,2])
def test_any_nonzero_gate_skips_object_motion_and_zero_allows_signed_velocity_then_xz_wrap(
        original_image,memory,fields,entry,stop,modal,partition,count):
    m,f = memory,fields;m[PARTITION] = partition;m[f['modal_command_input_flag']] = modal
    put(m,f['integrating_object_count'],count,2);put(m,f['integrating_objects_cursor'],LIST)
    put(m,f['horizontal_world_wrap_mask'],0xFFFFFF)
    worlds = [(0x7FFFFFFF,0xFFFFFFFF,0x80000000),(0xFFFFFFFE,0x80000000,0x12345678)]
    velocities = [(-32768,1,32767),(32767,-32768,-1)]
    for i,(xyz,delta) in enumerate(zip(worlds,velocities)):
        p = OBJECT+68*i;put(m,LIST+4*i,p);m[p:p+68] = b'\xA5'*68
        for off,value in zip([4,8,12],xyz):put(m,p+off,value)
        for off,value in zip([44,46,48],delta):put(m,p+off,value&65535,2)
    cpu = state(m,entry)
    expected = bytearray(m);active = not modal and not partition and count
    if active:
        for i,(xyz,delta) in enumerate(zip(worlds,velocities)):
            for axis,(value,velocity) in enumerate(zip(xyz,delta)):
                value = (value+velocity)&0xFFFFFFFF
                if axis!=1:value &= 0xFFFFFF
                p = OBJECT+68*i+4+4*axis;expected[p:p+4] = value.to_bytes(4,'big')
    run(original_image,m,cpu,{stop})
    assert bytes(m) == expected and cpu.a[7] == STACK
    assert m[PARTITION] == partition
    if active:assert cpu.a[1] == LIST+4*count
