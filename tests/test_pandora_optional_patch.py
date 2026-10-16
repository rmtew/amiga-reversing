"""Synthetic CPU comparisons; ordinary gameplay evidence lives in runtime/observations."""
import ctypes as C
import json
from pathlib import Path
import subprocess

import pytest
from amiga_reversing.tools.optional_patch import sha256
from tests.test_pandora_state_transitions import BASE, cpu_fixture

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'patches/pandora/optional-patches.json'


def patch_record():
    return json.loads(MANIFEST.read_text())['patches'][0]


def test_guard_assembly_matches_declared_bytes(tmp_path):
    assembler=ROOT/'tools/vasmm68k_mot.exe'
    if not assembler.exists(): pytest.skip('independent vasm unavailable')
    p=patch_record(); source=MANIFEST.parent/p['assembly']
    assert sha256(source.read_bytes())==p['assembly_sha256']
    out=tmp_path/'guard.bin'
    subprocess.run([str(assembler),'-m68000','-Fbin','-o',str(out),str(source)],check=True,capture_output=True)
    assert out.read_bytes()==bytes.fromhex(p['replacement_hex'])
    assert len(out.read_bytes())==40


@pytest.mark.parametrize('null,mode,clock',[(False,0,0),(False,1,1),(False,0xa5,0xffff),(True,0xa5,0xbeef)])
def test_guard_preserves_exchange_registers_flags_and_nonnull_effects(cpu_fixture,null,mode,clock):
    cpu,memory,schemas,read,write,run=cpu_fixture
    run(0x13f4)
    obj=schemas['world_object_shared_prefix']; state=schemas['world_position_state_record']; node=schemas['WorldPositionStateNode']
    owner=cpu.a[5]; descriptor=read(owner+obj['position_descriptor_ptr'])
    active=read(descriptor); saved=read(owner+obj['saved_position_state_ptr'])
    saved_node=read(saved+state['state_node_ptr'])
    assert saved_node
    write(saved_node+node['mode_flags'],mode,1)
    write(saved_node+node['frame_index_and_phase'],clock,2)
    if null: write(saved+state['state_node_ptr'],0)
    write(0xa,0xa5,1);write(0x10,0xbeef,2)
    for i in range(8):
        cpu.d[i]=0x12340000+i
        if i!=5:cpu.a[i]=0x56780000+i
    cpu.sr=0x201f  # Exercise preserved X as well as overwritten N/Z/V/C.
    before_memory=bytes(memory); before_cpu=bytes(cpu)
    run(0x867e)
    original_memory=bytes(memory); original_cpu=bytes(cpu)
    memory[:]=before_memory;C.memmove(C.addressof(cpu),before_cpu,C.sizeof(cpu))
    replacement=bytes.fromhex(patch_record()['replacement_hex'])
    memory[BASE+0x867e:BASE+0x86a6]=replacement
    run(0x867e)
    assert bytes(cpu)==original_cpu  # Includes SR/CCR, PC and all D/A registers.
    assert read(descriptor)==saved and read(owner+obj['saved_position_state_ptr'])==active
    assert read(0xa,1)==0xa5 and read(0x10,2)==0xbeef
    if null:
        assert original_memory[0xa]==0xa4 and original_memory[0x10:0x12]==b'\0\0'
    else:
        assert read(saved_node+node['mode_flags'],1)==mode & ~1
        assert read(saved_node+node['frame_index_and_phase'],2)==0
    # The extra stack scratch is explicit in the patch precondition. Everything
    # else, including guards, must match original execution byte for byte.
    expected=bytearray(original_memory)
    expected[BASE+0x867e:BASE+0x86a6]=replacement
    expected[0x8ff4:0x8ff8]=memory[0x8ff4:0x8ff8]
    if null:
        expected[0xa]=0xa5;expected[0x10:0x12]=b'\xbe\xef'
    assert memory==expected
