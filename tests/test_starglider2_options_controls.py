"""Original options-state windows with supplied RAM, not UI/device delivery.

Start after drawing/palette calls and stop at the original menu continuation.
No original instruction is patched. Settings retain arbitrary loaded BYTEs;
these tests do not impose a global boolean or autocentre-domain invariant.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image,memory,state,run,put,APP,RETURN


@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names=['crosshair_autocentre_mode','fixed_sight_mode_flag','one_hand_control_flag',
        'joystick_control_enabled_flag','pilot_rating_saved_control_settings',
        'options_joystick_status_text','options_one_hand_status_text',
        'options_fixed_sight_status_text','options_autocentre_status_text']
    folder=tmp_path_factory.mktemp('options');asm,out=folder/'fields.s',folder/'fields.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    r=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
    raw=out.read_bytes();assert raw[:-4*len(names)]==original_image[0]
    return dict(zip(names,struct.unpack('>'+str(len(names))+'I',raw[-4*len(names):])))


def app(fields,name):return APP+fields[name]
def text(m,address):return bytes(m[address:address+3])


@pytest.mark.parametrize('mode',range(256))
@pytest.mark.parametrize('enabled',[False,True])
def test_loaded_settings_render_nonzero_flags_and_all_autocentre_bytes(original_image,memory,fields,mode,enabled):
    flags=['joystick_control_enabled_flag','one_hand_control_flag','fixed_sight_mode_flag']
    values=[2,128,255]if enabled else[0,0,0]
    for name,value in zip(flags,values):memory[app(fields,name)]=value
    memory[app(fields,'crosshair_autocentre_mode')]=mode
    cpu=state(memory,0xE152);run(original_image,memory,cpu,{0xE256})
    for field in ['options_joystick_status_text','options_one_hand_status_text','options_fixed_sight_status_text']:
        p=fields[field];assert text(memory,p)==(b'ON 'if enabled else b'OFF')
        assert memory[p-1]==(0x89 if enabled else 0x8c)
    p=fields['options_autocentre_status_text']
    assert text(memory,p)==(b'OFF'if mode==0 else b'X  'if mode==1 else b'Y  'if mode==2 else b'X,Y')
    assert memory[p-1]==(0x8c if mode==0 else 0x89)
    assert [memory[app(fields,n)]for n in flags]==values
    assert memory[app(fields,'crosshair_autocentre_mode')]==mode


@pytest.mark.parametrize('mode',range(256))
def test_autocentre_cycle_preserves_the_original_partial_text_updates(original_image,memory,fields,mode):
    p=fields['options_autocentre_status_text'];memory[p-1:p+3]=b'\x55abc'
    memory[app(fields,'crosshair_autocentre_mode')]=mode
    cpu=state(memory,0xE616);run(original_image,memory,cpu,{0xE276})
    expected=(b'\x89X  ',1)if mode==0 else(b'\x55Ybc',2)if mode==1 else(b'\x55X,Y',3)if mode==2 else(b'\x8cOFF',0)
    assert bytes(memory[p-1:p+3])==expected[0]
    assert memory[app(fields,'crosshair_autocentre_mode')]==expected[1]


@pytest.mark.parametrize('value',[0,1,2,127,128,255])
@pytest.mark.parametrize('entry,flag,status,true_value',[
    (0xE55E,'one_hand_control_flag','options_one_hand_status_text',1),
    (0xE5BA,'fixed_sight_mode_flag','options_fixed_sight_status_text',255),
])
def test_menu_toggles_use_nonzero_tests_and_distinct_true_encodings(original_image,memory,fields,value,entry,flag,status,true_value):
    p=fields[status];memory[p-1:p+3]=b'\x55abc';memory[app(fields,flag)]=value
    cpu=state(memory,entry);run(original_image,memory,cpu,{0xE276})
    assert bytes(memory[p-1:p+3])==(b'\x89aN 'if value==0 else b'\x8caFF')
    assert memory[app(fields,flag)]==(true_value if value==0 else 0)


@pytest.mark.parametrize('value',[0,1,2,128,255])
@pytest.mark.parametrize('one_hand',[0,1,255])
def test_joystick_off_also_disables_one_hand_without_normalizing_unrelated_flags(original_image,memory,fields,value,one_hand):
    jp=fields['options_joystick_status_text'];hp=fields['options_one_hand_status_text']
    memory[jp-1:jp+3]=b'\x55abc';memory[hp-1:hp+3]=b'\x66def'
    memory[app(fields,'joystick_control_enabled_flag')]=value
    memory[app(fields,'one_hand_control_flag')]=one_hand
    memory[app(fields,'fixed_sight_mode_flag')]=0x80
    cpu=state(memory,0xE4EE);run(original_image,memory,cpu,{0xE276})
    assert bytes(memory[jp-1:jp+3])==(b'\x89aN 'if value==0 else b'\x8caFF')
    assert memory[app(fields,'joystick_control_enabled_flag')]==(1 if value==0 else 0)
    assert memory[app(fields,'one_hand_control_flag')]==(one_hand if value==0 else 0)
    assert bytes(memory[hp-1:hp+3])==(b'\x66def'if value==0 else b'\x8cdFF')
    assert memory[app(fields,'fixed_sight_mode_flag')]==0x80


@pytest.mark.parametrize('values',[(0,0,0,0),(1,255,1,1),(255,2,128,127),(3,128,255,2)])
def test_four_saved_bytes_roundtrip_without_touching_the_opaque_tail(original_image,memory,fields,values):
    names=['crosshair_autocentre_mode','fixed_sight_mode_flag','one_hand_control_flag','joystick_control_enabled_flag']
    p=fields['pilot_rating_saved_control_settings'];memory[p:p+184]=bytes(values)+b'\xa7'*180
    cpu=state(memory,0xE130);run(original_image,memory,cpu,{0xE146})
    assert [memory[app(fields,n)]for n in names]==list(values)
    new=tuple(v^0xff for v in values)
    for n,v in zip(names,new):memory[app(fields,n)]=v
    cpu=state(memory,0xE6CA);run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[p:p+184])==bytes(new)+b'\xa7'*180
