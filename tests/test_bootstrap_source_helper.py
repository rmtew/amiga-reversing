"""Same-size, identity-bound helper entry; original fixed-helper lane remains."""
import hashlib
import json
import subprocess
from pathlib import Path
import pytest
from amiga_reversing.disasm.memory_regions import validate_bootstrap
from amiga_reversing.disasm.c_backend import assemble_platform_source_text_with_c_backend
from tests.test_bootstrap_layouts import build,contract
from tests.test_memory_layouts import region,layout

# LEA helper.W,A2; JMP helper.W; CMPA.L A2,A1; RTS. Independent vasm
# reassembly below checks the generated PC-relative forms and all extents.
ORIGINAL=bytes.fromhex('45f803004ef80300b3ca4e75')
ROOT=Path(__file__).resolve().parents[1]


def metadata(data=ORIGINAL,variant='forward_disjoint_source_helper',**changes):
    c=contract(input_sha256=hashlib.sha256(data).hexdigest(),file_size=len(data),copied_source_end=len(data),
        helper_source_start=8,helper_source_end=12,continuation_source_offset=10,comparison_source_offset=8,
        helper_destination_source_offset=0,helper_jump_source_offset=4)
    return dict(memory_regions=[region('image',0x10000,len(data),kind='image')|{'source_domain':'mapped_source'}],
        memory_layouts=[layout([('image',0x80000)],bootstrap_contract_id='boot',bootstrap_variant=variant)],
        bootstrap_contracts=[c],selected_memory_layout_id='diagnostic',
        execution_views=[dict(source_start=0,source_end=len(data),base_addr=0x10000),
            dict(source_start=8,source_end=12,base_addr=0x300)])|changes


@pytest.mark.parametrize('variant',['forward_disjoint','forward_disjoint_source_helper'])
def test_helper_native_C_and_independent_vasm_agree(tmp_path,variant):
    a=build(tmp_path,metadata(variant=variant),ORIGINAL)
    try:
        plan=a.memory_layouts_payload()['items'][0];text=a.inline_source_text_with_profile()[0]
        encoded,_=assemble_platform_source_text_with_c_backend('amiga-raw',text)
        source=tmp_path/'source.s';source.write_text(text);output=tmp_path/'vasm.bin'
        subprocess.run([str(ROOT/'tools/vasmm68k_mot.exe'),'-Fbin','-m68000','-no-opt','-I'+str(ROOT/'ext/amiga_includes/ndk_2.0/include'),'-o',str(output),str(source)],check=True,capture_output=True)
        assert encoded==output.read_bytes() and len(encoded)==len(ORIGINAL)
        if variant=='forward_disjoint':
            assert encoded[:8]==ORIGINAL[:8] and plan['bootstrap']['helper_runtime_address']==0x300
        else:
            assert encoded[:4]!=ORIGINAL[:4] and encoded[4:8]!=ORIGINAL[4:8]
            assert '(pc)' in text and plan['bootstrap']['helper_runtime_address']==0x20008
            assert plan['bootstrap']['original_helper_runtime_address']==0x300
    finally:a.close()


@pytest.mark.parametrize('change',[
    {'helper_destination_source_offset':0.5},{'helper_jump_source_offset':None},
    {'helper_jump_source_offset':0},{'helper_jump_source_offset':6},{'helper_jump_source_offset':8}])
def test_source_sites_authored_and_native_malformed_refuse(tmp_path,change):
    m=metadata();m['bootstrap_contracts'][0].update(change)
    with pytest.raises(ValueError):validate_bootstrap(m['bootstrap_contracts'][0])
    with pytest.raises(RuntimeError):build(tmp_path,m,ORIGINAL)


@pytest.mark.parametrize('data',[
    bytes.fromhex('47f803004ef80300b3ca4e75'), # LEA destination A3, not reviewed A2.
    bytes.fromhex('45f803004ef80304b3ca4e75'), # JMP names a different helper.
])
def test_identity_alone_does_not_admit_wrong_entry_semantics(tmp_path,data):
    with pytest.raises(RuntimeError):build(tmp_path,metadata(data),data)


def test_missing_source_entry_sites_refused(tmp_path):
    m=metadata();del m['bootstrap_contracts'][0]['helper_jump_source_offset'];del m['bootstrap_contracts'][0]['helper_destination_source_offset']
    with pytest.raises(RuntimeError):build(tmp_path,m,ORIGINAL)


def test_helper_entry_state_and_oracle_cycles(tmp_path):
    import machine68k
    a=build(tmp_path,metadata(),ORIGINAL)
    try:changed,_=assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])
    finally:a.close()
    for ccr in range(32):
        timings=[]
        for code,target in ((ORIGINAL,0x300),(changed,0x20008)):
            m=machine68k.Machine(machine68k.CPUType.M68000,256)
            m.mem.w_block(0x20000,code);m.mem.w_block(0x300,b'\x4e\x71'*4)
            for i in range(8):
                m.cpu.w_reg(getattr(machine68k.Register,f'D{i}'),0x12340000+i)
                m.cpu.w_reg(getattr(machine68k.Register,f'A{i}'),0x9000+i*4)
            m.cpu.w_sr(0x2700|ccr);m.cpu.w_pc(0x20000)
            cycles=[m.cpu.execute(1).cycles,m.cpu.execute(1).cycles]
            assert m.cpu.r_pc()==target and m.cpu.r_sr()==0x2700|ccr
            assert [m.cpu.r_reg(getattr(machine68k.Register,f'D{i}')) for i in range(8)]==[0x12340000+i for i in range(8)]
            assert [m.cpu.r_reg(getattr(machine68k.Register,f'A{i}')) for i in range(8)]==[target if i==2 else 0x9000+i*4 for i in range(8)]
            timings.append(cycles)
        assert timings==[[8,10],[8,10]]


def test_helper_activation_requires_new_frozen_plan(tmp_path):
    m=metadata(variant='forward_disjoint');a=build(tmp_path,m,ORIGINAL)
    try:
        changed=dict(m['memory_layouts'][0],bootstrap_variant='forward_disjoint_source_helper')
        result=a.layout_projection_payload(dict(memory_layouts=[changed],selected_memory_layout_id='diagnostic'))
        assert result['status']=='rebuild_required' and result['reason']=='bootstrap_or_profile_change_requires_new_plan'
    finally:a.close()
