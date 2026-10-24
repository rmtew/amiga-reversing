"""Canonical, identity-bound same-size address-frame variants through native export."""
import copy
import hashlib
import subprocess

import pytest

from tests.test_bootstrap_layouts import metadata,build
from tests.test_memory_layouts import region
from amiga_reversing.disasm.memory_regions import validate_region
from amiga_reversing.disasm.c_backend import assemble_platform_source_text_with_c_backend
from amiga_reversing.tools.direct_payload_adapter import VASM


def model(stage=0x6080):
    data=bytes.fromhex('4e71b3ca60024e754df9000039fc21fc0001e92864c04e75')
    data+=bytes(512-len(data));m=metadata();m['memory_regions'][0]['size']=512
    owner=region('cpu',0x39fc,0xbbb3)|dict(dma_access='none',address_frame=dict(
        schema_version=1,kind='same_size_move_long_immediate_store',register='a6',contract_sha256='a'*64,input_sha256=hashlib.sha256(data).hexdigest(),
        sites=[dict(section_index=0,source_offset=14,operand_index=1,expected_hex=data[14:22].hex())]))
    m['memory_regions'] += [owner,region('grid',0x4000,0xb568,parent='cpu')|dict(dma_access='none')]
    m['memory_layouts'][0]['placements'].append(dict(region_id='cpu',runtime_address=stage))
    m['bootstrap_contracts'][0].update(input_sha256=hashlib.sha256(data).hexdigest(),file_size=512,copied_source_end=512)
    m['execution_views'][0]['source_end']=512
    m['target_equates']=[dict(name='APP',value=0x39fc,group='cpu',address_domain='runtime',extent_bytes=4),dict(name='CELL',value=0x64c0,group='cpu',address_domain='runtime',extent_bytes=4)]
    m['manual_representations']=[dict(hunk=0,addr=8,end=14,element_kind='absolute_address',operand_index=0,style='symbol',symbol='APP',value=0x39fc,width_bytes=4),dict(hunk=0,addr=14,end=22,element_kind='absolute_address',operand_index=1,style='symbol',symbol='CELL',value=0x64c0,width_bytes=2)]
    return m,data


@pytest.mark.parametrize('stage',[0x39fc,0x6080,0x7080])
def test_original_and_restored_native_frame_export(tmp_path,stage):
    m,data=model(stage);assert validate_region(m['memory_regions'][1])==m['memory_regions'][1]
    a=build(tmp_path,m,data)
    try:
        text=a.inline_source_text_with_profile()[0]
        if stage==0x39fc:
            assert 'restored-only address frame' not in text
            assert 'CELL.w' in text
        else:
            assert 'restored-only address frame a6' in text
            assert 'CELL-cpu_base(a6)' in text
        native,_=assemble_platform_source_text_with_c_backend('amiga-raw',text)
        s=tmp_path/'out.s';b=tmp_path/'out.bin';s.write_text(text)
        r=subprocess.run([str(VASM),'-quiet','-Fbin','-m68000','-no-opt','-o',str(b),str(s)],capture_output=True,text=True)
        assert r.returncode==0,r.stderr
        assert native==b.read_bytes() and len(native)==512
        assert native[14:22]==(data[14:22] if stage==0x39fc else bytes.fromhex('2d7c0001e9282ac4'))
        if stage!=0x39fc:
            p=a.runtime_allocation_plan('cpu','diagnostic',0x7080)
            assert p['status']=='actual_placement_valid',p
            assert len(p['fixups'])==1 and p['fixups'][0]['source_offset']==10
            assert p['address_frame_guards']==[dict(instruction_source_offset=14,opcode=0x2d7c,displacement_source_offset=20,displacement=0x2ac4,base_register=6,instruction_size=8)]
            assert p['address_frame_contract_sha256']=='a'*64
        changed=copy.deepcopy(m);changed['memory_layouts'][0]['placements'][-1]['runtime_address']=0x39fc if stage!=0x39fc else 0x6080
        projected=a.layout_projection_payload(dict(memory_layouts=changed['memory_layouts'],selected_memory_layout_id='diagnostic'))
        assert projected['status']=='rebuild_required' and projected['reason']=='address_frame_activation_requires_new_plan'
    finally:a.close()


@pytest.mark.parametrize('change', ['scalar','fraction','duplicate','stale','unaccepted','register','kind','contract','input','sibling_modified','wrong_form'])
def test_frame_admission_refuses_malformed_or_unbound_sites(tmp_path,change):
    m,data=model();owner=m['memory_regions'][1];frame=owner['address_frame'];site=frame['sites'][0]
    if change=='scalar':frame['sites']=[1]
    elif change=='fraction':site['source_offset']=14.5
    elif change=='duplicate':frame['sites']*=2
    elif change=='stale':site['expected_hex']='00'*8
    elif change=='unaccepted':site['source_offset']=100
    elif change=='register':frame['register']='a7'
    elif change=='kind':frame['kind']='arbitrary_rewrite'
    elif change=='contract':frame['contract_sha256']='z'*64
    elif change=='input':frame['input_sha256']='z'*64
    elif change=='sibling_modified':
        data=data[:100]+b'\x01'+data[101:]
        m['bootstrap_contracts'][0]['input_sha256']=hashlib.sha256(data).hexdigest()
    elif change=='wrong_form':
        data=data[:14]+bytes.fromhex('00800001e9284e71')+data[22:]
        site['expected_hex']=data[14:22].hex()
        frame['input_sha256']=m['bootstrap_contracts'][0]['input_sha256']=hashlib.sha256(data).hexdigest()
    if change not in ['stale','unaccepted','sibling_modified','wrong_form']:
        with pytest.raises(ValueError,match='address_frame'):validate_region(owner)
    with pytest.raises(RuntimeError,match='memory region|address_frame'):
        a=build(tmp_path,m,data);a.close()


def test_typed_grid_pointer_MOVE_immediate_is_an_encoder_bound_field(tmp_path):
    m,data=model()
    data=data[:22]+bytes.fromhex('2d7c0000400001be4e75')+data[32:]
    m['bootstrap_contracts'][0]['input_sha256']=m['memory_regions'][1]['address_frame']['input_sha256']=hashlib.sha256(data).hexdigest()
    m['target_equates'].append(dict(name='GRID',value=0x4000,group='cpu',address_domain='runtime',extent_bytes=4))
    m['manual_representations'].append(dict(hunk=0,addr=22,end=30,element_kind='immediate',operand_index=0,style='symbol',symbol='GRID',value=0x4000,width_bytes=4))
    a=build(tmp_path,m,data)
    try:
        p=a.runtime_allocation_plan('cpu','diagnostic',0x7080)
        assert p['status']=='actual_placement_valid',p
        assert p['fixups'][1]==dict(source_section_index=0,source_offset=24,width=4,
            encoding='absolute_long_immediate',address_domain='runtime_only',region_offset=0x604,staged_value=0x6684,
            instruction_source_offset=22,operand_index=0,opcode=0x2d7c,symbol='GRID')
        text=a.inline_source_text_with_profile()[0]
        code,_=assemble_platform_source_text_with_c_backend('amiga-raw',text)
        assert code[24:28]==bytes.fromhex('00006684')
    finally:a.close()


def image_source_frame_model(*,foreign=False):
    from tests.test_memory_layouts import region
    m,data=model();value=0x2000 if foreign else 0x10040
    data=data[:14]+bytes.fromhex('21fc')+value.to_bytes(4,'big')+bytes.fromhex('64c0')+data[22:]
    digest=hashlib.sha256(data).hexdigest();m['bootstrap_contracts'][0]['input_sha256']=digest
    frame=m['memory_regions'][1]['address_frame'];frame['input_sha256']=digest;frame['sites'][0]['expected_hex']=data[14:22].hex()
    m['target_equates'].append(dict(name='PIXEL',value=value,group='assets',address_domain='runtime',extent_bytes=4))
    m['manual_representations'].append(dict(hunk=0,addr=14,end=22,element_kind='immediate',operand_index=0,
        style='symbol',symbol='PIXEL',value=value,width_bytes=4))
    if foreign:
        m['memory_regions'].append(region('foreign',0x2000,128)|dict(dma_access='none'))
        m['memory_layouts'][0]['placements'].append(dict(region_id='foreign',runtime_address=0x3000))
    return m,data


def test_image_LONG_source_and_reviewed_frame_destination_compose_byte_exactly(tmp_path):
    from tests.test_memory_layouts import layout
    m,data=image_source_frame_model();a=build(tmp_path,m,data)
    try:
        batch=a.runtime_allocation_batch_plan('diagnostic',layout([('image',0x90000),('cpu',0x7080)]))
        assert batch['status']=='actual_placements_valid',batch
        staged,_=assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])
        patched=bytearray(staged);actual={'image':0x90000,'cpu':0x7080}
        for member in batch['members']:
            for f in member['fixups']:
                value=actual[member['region_id']]+f['region_offset']
                patched[f['source_offset']:f['source_offset']+f['width']]=value.to_bytes(f['width'],'big')
        assert staged[14:16]==patched[14:16] and staged[20:22]==patched[20:22]
        assert int.from_bytes(patched[16:20],'big')==0x90040
        reference=copy.deepcopy(m)
        reference['memory_layouts'][0]['placements']=[dict(region_id=n,runtime_address=v) for n,v in actual.items()]
        directory=tmp_path/'reference';directory.mkdir();b=build(directory,reference,data)
        try:
            source=b.inline_source_text_with_profile()[0]
            expected,_=assemble_platform_source_text_with_c_backend('amiga-raw',source)
            asm=directory/'reference.s';binary=directory/'reference.bin';asm.write_text(source)
            subprocess.run([str(VASM),'-quiet','-Fbin','-m68000','-no-opt','-o',str(binary),str(asm)],check=True,capture_output=True)
            assert bytes(patched)==expected==binary.read_bytes()
        finally:b.close()
    finally:a.close()


def test_other_owner_field_does_not_silently_widen_frame_composition(tmp_path):
    from tests.test_memory_layouts import layout
    m,data=image_source_frame_model(foreign=True);a=build(tmp_path,m,data)
    try:
        batch=a.runtime_allocation_batch_plan('diagnostic',layout([('foreign',0x3000),('cpu',0x7080)]))
        assert batch['status']=='refused' and batch['reason']=='batch_fixup_overlaps_frame_contract',batch
    finally:a.close()
