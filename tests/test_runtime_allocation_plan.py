"""Native typed fixups and actual-return geometry remain separate obligations."""
import hashlib

import pytest

from tests.test_bootstrap_layouts import build,metadata
from tests.test_memory_layouts import region


def fixture(tmp_path, unresolved_value=None, extra_runtime_extent=None, **owner_changes):
    data=bytes.fromhex('4e71b3ca4e754e75000007f0')
    if unresolved_value is not None:data+=unresolved_value.to_bytes(4,'big')
    data+=bytes(512-len(data))
    m=metadata()
    m['memory_regions'][0]['size']=len(data)
    m['memory_regions'] += [region('body',0x7f0,0x900,**owner_changes),region('grid',0x4000,0xb568)]
    m['bootstrap_contracts'][0].update(file_size=len(data),copied_source_end=len(data),
        input_sha256=hashlib.sha256(data).hexdigest())
    m['execution_views'][0]['source_end']=len(data)
    m['seeded_entities']=[dict(addr=8,end=12,hunk=0,unit='long',struct_name='Frame',
        field_name='bitmap',field_type='long',value_kind='target_pointer',
        pointer_address_domain='runtime_only',pointer_symbol_group='buffers')]
    m['target_equates']=[dict(name='BODY_STORAGE',value=0x7f0,extent_bytes=0x900,
        group='buffers',address_domain='runtime')]
    if unresolved_value is not None:
        m['seeded_entities'].append(dict(addr=12,end=16,hunk=0,unit='long',struct_name='Frame',
            field_name='other',field_type='long',value_kind='target_pointer',
            pointer_address_domain='runtime_only',pointer_symbol_group='missing'))
    if extra_runtime_extent is not None:
        address,size=extra_runtime_extent
        m['target_equates'].append(dict(name='OTHER_RUNTIME_STORAGE',value=address,
            extent_bytes=size,group='other',address_domain='runtime'))
    return build(tmp_path,m,data)


def test_typed_LONG_candidate_and_actual_base_are_native_and_repeatable(tmp_path):
    a=fixture(tmp_path)
    try:
        initial=a.runtime_allocation_plan('body','diagnostic')
        assert initial['status']=='bounded_allocation_candidate'
        assert initial['fixups']==[dict(source_section_index=0,source_offset=8,width=4,
            encoding='absolute_long_data',address_domain='runtime_only',region_offset=0,staged_value=0x7f0)]
        actual=a.runtime_allocation_plan('body','diagnostic',0xf568)
        assert actual['status']=='actual_placement_valid'
        owner=next(r for r in actual['layout']['items'][0]['regions'] if r['region_id']=='body')
        assert owner['runtime_address']==0xf568
        assert a.runtime_allocation_plan('body','diagnostic')==initial
    finally:a.close()


@pytest.mark.parametrize('address,reason',[(0x59e8,'unrelated_region_overlap'),
    (0x20000,'allocator_result_overlaps_live_input'),(0xf569,'invalid_extent_or_alignment'),
    (0x100000,'outside_declared_chip_ram')])
def test_actual_allocations_refuse_collisions_and_invalid_extents(tmp_path,address,reason):
    a=fixture(tmp_path)
    try:
        result=a.runtime_allocation_plan('body','diagnostic',address)
        assert result==dict(status='refused',reason=reason)
    finally:a.close()


@pytest.mark.parametrize('value,expected',[(0x90000,'bounded_allocation_candidate'),
    (0x800,'refused')])
def test_unresolved_runtime_domains_are_scoped_not_silently_owned(tmp_path,value,expected):
    a=fixture(tmp_path,unresolved_value=value)
    try:
        result=a.runtime_allocation_plan('body','diagnostic')
        assert result['status']==expected
        assert a.memory_regions_payload()['unresolved_typed_data_pointer_site_count']>=1
        if expected=='refused':assert result['reason']=='unresolved_runtime_pointer_site'
        else:assert len(result['fixups'])==1
    finally:a.close()


def test_protected_equate_without_a_region_still_blocks_actual_base(tmp_path):
    a=fixture(tmp_path,extra_runtime_extent=(0xf600,0x100))
    try:
        assert a.runtime_allocation_plan('body','diagnostic')['status']=='bounded_allocation_candidate'
        result=a.runtime_allocation_plan('body','diagnostic',0xf568)
        assert result==dict(status='refused',reason='allocator_result_overlaps_protected_runtime_extent')
    finally:a.close()


def test_another_old_owner_alias_is_not_inferred_as_a_fixup(tmp_path):
    a=fixture(tmp_path,extra_runtime_extent=(0x7f0,0x900))
    try:
        assert a.runtime_allocation_plan('body','diagnostic')==dict(
            status='refused',reason='unbound_runtime_alias_of_allocation_owner')
    finally:a.close()


@pytest.mark.parametrize('base,expected',[(0xf568,'refused'),(0xf5a8,'refused'),(0xf5b0,'actual_placement_valid')])
def test_grid_end_probe_byte_must_not_alias_an_independent_body_lease(tmp_path,base,expected):
    # Existing stale-A4 inventory path reads grid_end + $46. A BYTE footprint
    # excludes both historical body bases without extending the grid itself.
    artifact=fixture(tmp_path,extra_runtime_extent=(0xf568+0x46,1))
    try:
        result=artifact.runtime_allocation_plan('body','diagnostic',base)
        assert result['status']==expected
        if expected=='refused':assert result['reason']=='allocator_result_overlaps_protected_runtime_extent'
    finally:artifact.close()
