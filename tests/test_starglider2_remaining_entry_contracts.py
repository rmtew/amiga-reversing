"""Local original entry behavior, not complete dispatch or hardware qualification."""
import ctypes
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,APP,INPUT,RETURN,STACK


@pytest.fixture(scope='module')
def labels(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names=['continue_primary_object_update_loop','integrate_and_steer_horizontal_actor',
        'continue_secondary_object_update_loop','build_and_store_view_rotation_matrix',
        'space_environment_flag','diagnostic_step_byte','_ciaa+ciaprb','_ciaa+ciaddrb']
    folder=tmp_path_factory.mktemp('remaining-entries');asm,out=folder/'labels.s',folder/'labels.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result=subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    raw=out.read_bytes();size=4*len(names);assert raw[:-size]==original_image[0]
    values=dict(zip(names,struct.unpack('>'+'I'*len(names),raw[-size:])))
    values['space_environment_flag']+=APP
    return values


@pytest.mark.parametrize('flag',[0,1,127,128,255])
@pytest.mark.parametrize('angles',[(0,0),(4090,4095),(65535,65520),(32768,32767)])
def test_junk_spin_requires_negative_byte_and_masks_both_words(original_image,memory,labels,flag,angles):
    memory[INPUT:INPUT+68]=b'\xA5'*68
    for off,value in zip([16,20],angles):put(memory,INPUT+off,value,2)
    memory[labels['space_environment_flag']]=flag
    cpu=state(memory,0x83D8);before_d,before_a=list(cpu.d),list(cpu.a);expected=bytearray(memory)
    if flag&128:
        for off,value in zip([16,20],angles):put(expected,INPUT+off,(value+16)&4095,2)
    run(original_image,memory,cpu,{labels['continue_primary_object_update_loop']},limit=8)
    assert bytes(memory)==expected and list(cpu.d)==before_d and list(cpu.a)==before_a


@pytest.mark.parametrize('variant',[0,1,18,19,20,21,127,128,254,255])
def test_columbus_resets_only_the_incremented_byte_equal_to_twenty(original_image,memory,labels,variant):
    memory[INPUT:INPUT+68]=b'\xA5'*68;memory[INPUT+3]=variant
    cpu=state(memory,0x9318);before_d,before_a=list(cpu.d),list(cpu.a);expected=bytearray(memory)
    value=(variant+1)&255;expected[INPUT+3]=0 if value==20 else value
    run(original_image,memory,cpu,{labels['integrate_and_steer_horizontal_actor']},limit=6)
    assert bytes(memory)==expected and list(cpu.d)==before_d and list(cpu.a)==before_a


@pytest.mark.parametrize('tag',[0,1,89,65535])
def test_distant_clear_tail_writes_one_word_and_diagnostic_without_pool_operations(original_image,memory,labels,tag):
    memory[INPUT:INPUT+68]=b'\xA5'*68;put(memory,INPUT,tag,2)
    cpu=state(memory,0xA8CE);before_d,before_a=list(cpu.d),list(cpu.a);expected=bytearray(memory)
    put(expected,INPUT,0,2);expected[labels['diagnostic_step_byte']]=0x4B
    run(original_image,memory,cpu,{labels['continue_secondary_object_update_loop']},limit=4)
    assert bytes(memory)==expected and list(cpu.d)==before_d and list(cpu.a)==before_a


@pytest.mark.parametrize('status',[0x2700,0x271F])
def test_ciaa_direction_setter_only_changes_emulated_ddrb_and_returns(original_image,labels,status):
    # Flat test RAM includes device addresses; this is not a CIA/port model.
    memory=(ctypes.c_uint8*0x1000000)()
    ctypes.memmove(ctypes.addressof(memory)+0x1000,original_image[0],len(original_image[0]))
    memory[labels['_ciaa+ciaprb']]=0xA5;memory[labels['_ciaa+ciaddrb']]=0x55
    cpu=state(memory,0xCB80);cpu.sr=status
    before_d,before_a=list(cpu.d),list(cpu.a);before_a[7]=STACK+4
    expected=bytearray(memory);expected[labels['_ciaa+ciaddrb']]=255
    run(original_image,memory,cpu,{RETURN},limit=3)
    assert bytes(memory)==expected and list(cpu.d)==before_d and list(cpu.a)==before_a
    assert cpu.sr==(status&~15)|8


def test_viewer_matrix_bridge_keeps_original_return_frame(original_image,memory,labels):
    cpu=state(memory,0xFD70);before=bytes(memory);before_d,before_a=list(cpu.d),list(cpu.a);sr=cpu.sr
    run(original_image,memory,cpu,{labels['build_and_store_view_rotation_matrix']},limit=2)
    assert bytes(memory)==before and list(cpu.d)==before_d and list(cpu.a)==before_a and cpu.sr==sr
