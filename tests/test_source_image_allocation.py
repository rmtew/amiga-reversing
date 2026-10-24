"""Source image admission retains typed identities and encoded field bounds."""
import hashlib
import pytest
from tests.test_bootstrap_layouts import build,metadata


def fixture(tmp_path, *, pointer=0x10000, domain=None, extra=None, child=None, destination=0x10016):
    # NOP/CMPA retained bootstrap; SUBI.L prefix; MOVE.L immediate and
    # destination extension; RTS; one typed pointer and one equal scalar.
    data=bytes.fromhex('4e71b3ca04800001001623fc00010016000100164e75')
    data=data[:16]+destination.to_bytes(4,'big')+data[20:]
    data+=pointer.to_bytes(4,'big')+bytes.fromhex('00010000')
    m=metadata();m['memory_regions'][0]['size']=len(data)
    if child:m['memory_regions'].append(child)
    m['execution_views'][0]['source_end']=len(data)
    m['bootstrap_contracts'][0].update(file_size=len(data),copied_source_end=len(data),
        input_sha256=hashlib.sha256(data).hexdigest())
    entity=dict(addr=22,end=26,hunk=0,unit='long',name='image_pointer',struct_name='Record',
        field_name='target',field_type='long',value_kind='target_pointer')
    if domain:entity.update(pointer_address_domain=domain,pointer_symbol_group='buffers')
    m['seeded_entities']=[entity,dict(addr=26,end=30,hunk=0,unit='long',name='scalar')]
    m['manual_representations']=[dict(hunk=0,addr=4,end=10,style='symbol',operand_index=0,
        symbol='image_pointer',source_symbol=dict(section_index=0,source_offset=22,
            runtime_view=1,encoded_value=0x10016))]
    if extra:m.update(extra)
    return build(tmp_path,m,data)


def test_source_image_projects_immediate_prefix_and_destination_fields(tmp_path):
    a=fixture(tmp_path)
    try:
        inventory=a.query_payload('expressions',limit=100)['items']
        p=a.runtime_allocation_plan('image','diagnostic')
        assert p['status']=='bounded_allocation_candidate',(p,inventory)
        by_offset={f['source_offset']:f for f in p['fixups']}
        assert set(by_offset)=={6,12,16,22}
        assert [by_offset[x]['target_offset'] for x in sorted(by_offset)]==[22,22,22,0]
        assert all(f['width']==4 and f['address_domain']=='mapped_source' for f in by_offset.values())
        assert a.runtime_allocation_plan('image','diagnostic',0x90000)['status']=='actual_placement_valid'
        assert a.runtime_allocation_plan('image','diagnostic',0x20000)['status']=='refused'
    finally:a.close()


def test_source_local_numeric_coincidence_is_not_encoded_absolute_pointer(tmp_path):
    a=fixture(tmp_path,pointer=0,domain='runtime_only',extra=dict(manual_runtime_address_refs=[
        dict(hunk=0,addr=22,size=4,target_hunk=0,target_offset=0,runtime_address=0,
            owner_kind='data_block_interpreted_ref',owner_id='explicit',owner_layout_id='record',owner_element_offset=0,xref_generation_mode='bidirectional',confidence=3)]))
    try:
        p=a.runtime_allocation_plan('image','diagnostic')
        assert p['status']=='refused'
        assert p['reason']=='interpreted_image_pointer_mapping_mismatch'
    finally:a.close()


def test_explicit_interpreted_runtime_alias_keeps_source_identity(tmp_path):
    a=fixture(tmp_path,domain='runtime_only',extra=dict(manual_runtime_address_refs=[
        dict(hunk=0,addr=22,size=4,target_hunk=0,target_offset=0,runtime_address=0x10000,
            owner_kind='data_block_interpreted_ref',owner_id='explicit',owner_layout_id='record',
            owner_element_offset=0,xref_generation_mode='bidirectional',confidence=3)]))
    try:
        p=a.runtime_allocation_plan('image','diagnostic')
        assert p['status']=='bounded_allocation_candidate',p
        f=next(f for f in p['fixups'] if f['source_offset']==22)
        assert f['target_offset']==0 and f['staged_value']==0x80000
    finally:a.close()


def test_image_capacity_is_derived_from_frozen_fields_and_batch_retires_fixed_image(tmp_path):
    from tests.test_memory_layouts import layout
    count=256
    data=bytes.fromhex('4e71b3ca4e754e75')+bytes.fromhex('00010000')*count
    m=metadata();m['memory_regions'][0]['size']=len(data)
    m['execution_views'][0]['source_end']=len(data)
    m['bootstrap_contracts'][0].update(file_size=len(data),copied_source_end=len(data),
        input_sha256=hashlib.sha256(data).hexdigest())
    m['seeded_entities']=[dict(addr=8+i*4,end=12+i*4,hunk=0,unit='long',
        struct_name='Record',field_name='target',field_type='long',value_kind='target_pointer') for i in range(count)]
    a=build(tmp_path,m,data)
    try:
        p=a.runtime_allocation_plan('image','diagnostic')
        assert p['status']=='bounded_allocation_candidate' and len(p['fixups'])==count,p
        actual=a.runtime_allocation_batch_plan('diagnostic',layout([('image',0x90000)]))
        assert actual['status']=='actual_placements_valid' and actual['fixup_count']==count,actual
        assert all(f['staged_value']==0x80000 for f in actual['members'][0]['fixups'])
        assert all(c['address']!=0x80000 for c in actual['fixed_leases_requiring_OS_acquisition'])
    finally:a.close()


def test_image_read_must_fit_copied_owner(tmp_path):
    a=fixture(tmp_path,destination=0x1001c)
    try:
        p=a.runtime_allocation_plan('image','diagnostic')
        assert p['status']=='refused' and p['reason']=='partial_image_operand_access',p
        assert p['refusal_reference']['source_offset']==10
    finally:a.close()


@pytest.mark.parametrize('mapped',[True,False])
def test_image_child_retains_exact_inherited_source_mapping(tmp_path,mapped):
    from tests.test_memory_layouts import region,layout
    child=region('field',0x10016,4,parent='image')|dict(source_domain='mapped_source' if mapped else 'runtime_only')
    a=fixture(tmp_path,child=child)
    try:
        p=a.runtime_allocation_batch_plan('diagnostic',layout([('image',0x90000)]))
        if not mapped:
            assert p['status']=='refused'
            assert p['members'][0]['reason']=='image_child_source_mapping_not_inherited'
        else:
            assert p['status']=='actual_placements_valid',p
            fields=p['layout']['items'][0]['regions']
            assert next(f for f in fields if f['region_id']=='field')['runtime_address']==0x90016
    finally:a.close()
