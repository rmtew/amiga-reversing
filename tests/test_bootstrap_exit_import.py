"""One original JSR field may be bound by the explicit hosted bootstrap only."""
import copy
import hashlib
import subprocess
import pytest
from tests.test_bootstrap_layouts import metadata,build
from amiga_reversing.disasm.memory_regions import validate_bootstrap
from amiga_reversing.disasm.c_backend import assemble_platform_source_text_with_c_backend
from amiga_reversing.tools.direct_payload_adapter import VASM


def fixture(data=None):
    data=data or bytes.fromhex('4e71b3ca60024e754eb9000100104e754e714e75')
    data+=bytes(512-len(data));m=metadata();m['memory_regions'][0]['size']=512
    m['bootstrap_contracts'][0].update(input_sha256=hashlib.sha256(data).hexdigest(),file_size=512,copied_source_end=512,
        exit_dispatch_call_source_offset=8,exit_dispatch_target_source_offset=16)
    m['execution_views'][0]['source_end']=512
    return m,data


def test_exact_JSR_import_is_metadata_only_and_C_vasm_agree(tmp_path):
    m,data=fixture();assert validate_bootstrap(m['bootstrap_contracts'][0])==m['bootstrap_contracts'][0]
    a=build(tmp_path,m,data)
    try:
        text=a.inline_source_text_with_profile()[0]
        native,_=assemble_platform_source_text_with_c_backend('amiga-raw',text)
        source=tmp_path/'export.s';binary=tmp_path/'export.bin';source.write_text(text)
        subprocess.run([str(VASM),'-quiet','-Fbin','-m68000','-no-opt','-o',str(binary),str(source)],check=True,capture_output=True)
        assert native==binary.read_bytes() and native[8:14]==bytes.fromhex('4eb900080010')
        value=a.memory_layouts_payload()['items'][0]['bootstrap']['exit_dispatch_import']
        assert value==dict(status='requires_runtime_code_binding',role='host_mission_restart_dispatch',instruction_source_offset=8,
            source_offset=10,width=4,opcode=0x4eb9,instruction_size=6,original_target_source_offset=16,staged_value=0x80010)
        plain=copy.deepcopy(m);plain['bootstrap_contracts'][0].pop('exit_dispatch_call_source_offset');plain['bootstrap_contracts'][0].pop('exit_dispatch_target_source_offset')
        other=build(tmp_path,plain,data)
        try:assert assemble_platform_source_text_with_c_backend('amiga-raw',other.inline_source_text_with_profile()[0])[0]==native
        finally:other.close()
    finally:a.close()


@pytest.mark.parametrize('change',[{'exit_dispatch_call_source_offset':8.5},{'exit_dispatch_target_source_offset':17},
    {'exit_dispatch_call_source_offset':2},{'exit_dispatch_call_source_offset':510},{'exit_dispatch_target_source_offset':512}])
def test_authored_and_native_extent_validation_refuse(tmp_path,change):
    m,data=fixture();m['bootstrap_contracts'][0].update(change)
    with pytest.raises(ValueError):validate_bootstrap(m['bootstrap_contracts'][0])
    with pytest.raises(RuntimeError):build(tmp_path,m,data)


def test_missing_target_is_not_an_implicit_optional_contract(tmp_path):
    m,data=fixture();m['bootstrap_contracts'][0].pop('exit_dispatch_target_source_offset')
    with pytest.raises(ValueError):validate_bootstrap(m['bootstrap_contracts'][0])
    with pytest.raises(RuntimeError):build(tmp_path,m,data)


@pytest.mark.parametrize('raw',['4e71','4ef900010010','4eb900010012'])
def test_wrong_instruction_or_original_target_refuses_even_with_fresh_hash(tmp_path,raw):
    m,data=fixture();data=data[:8]+bytes.fromhex(raw)+data[8+len(bytes.fromhex(raw)):]
    m['bootstrap_contracts'][0]['input_sha256']=hashlib.sha256(data).hexdigest()
    with pytest.raises(RuntimeError):build(tmp_path,m,data)


def test_import_is_reported_with_an_atomic_owner_layout(tmp_path):
    from tests.test_memory_layouts import region,layout
    m,data=fixture();data=data[:20]+bytes.fromhex('00004000')+data[24:]
    m['bootstrap_contracts'][0]['input_sha256']=hashlib.sha256(data).hexdigest()
    m['memory_regions'].append(region('body',0x4000,32,kind='storage'))
    m['target_equates']=[dict(name='BODY',value=0x4000,extent_bytes=32,group='body',address_domain='runtime')]
    m['seeded_entities']=[dict(addr=20,end=24,hunk=0,unit='long',struct_name='Frame',field_name='ptr',field_type='long',value_kind='target_pointer',pointer_address_domain='runtime_only',pointer_symbol_group='body')]
    a=build(tmp_path,m,data)
    try:
        p=a.runtime_allocation_batch_plan('diagnostic',layout([('body',0x7000)]))
        assert p['status']=='actual_placements_valid',p
        assert p['fixup_count']==1 and p['members'][0]['fixups'][0]['source_offset']==20
        assert p['layout']['items'][0]['bootstrap']['exit_dispatch_import']['source_offset']==10
    finally:a.close()
