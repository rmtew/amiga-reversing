"""Allocation preparation must see typed data pointers, not scalar lookalikes."""
import json

import pytest

from amiga_reversing.disasm.c_backend import build_flat_m68k_bytes_listing_artifact_profile
from tests.test_memory_regions import region


@pytest.mark.parametrize('typed,value,group,expected', [
    (True, 0x8004, 'buffers', 1),
    (False, 0x8004, 'buffers', 0),
    (True, 0x8010, 'buffers', 0),
    (True, 0x8004, 'other_namespace', 0),
])
def test_native_region_exposes_frozen_pointer_coordinates(tmp_path, typed, value, group, expected):
    data = bytes.fromhex('6004') + value.to_bytes(4, 'big') + bytes.fromhex('4e75')
    item = dict(addr=2, end=6, hunk=0, unit='long')
    if typed:
        item.update(struct_name='Frame', field_name='bitmap', field_type='long',
                    value_kind='target_pointer', pointer_address_domain='runtime_only',
                    pointer_symbol_group=group)
    metadata = dict(memory_regions=[region(region_id='bitmap', name='bitmap',
        runtime_address=0x8000, size=16, dma_access='chip')], seeded_entities=[item],
        target_equates=[dict(name='BITMAP_STORAGE', value=0x8000, extent_bytes=16,
                            group='buffers', address_domain='runtime')])
    path = tmp_path / 'metadata.json'
    path.write_text(json.dumps(metadata))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        data, display_path='typed-pointer-sites', metadata_path=path)
    try:
        payload = artifact.memory_regions_payload()
        result = payload['items'][0]
        assert result['typed_data_pointer_site_count'] == expected
        sites = result['typed_data_pointer_sites']
        assert len(sites) == expected
        if expected:
            symbolic = group == 'buffers'
            assert sites == [dict(source_section_index=0, source_offset=2, width=4,
                address=value, region_offset=4, kind='table_entry', symbolic=symbolic,
                reason='resolved_runtime_symbol', target_symbol='BITMAP_STORAGE',
                encoded_value=value, address_domain='runtime_only', has_target=False,
                target_section_index=None, target_offset=None)]
        if typed and group != 'buffers':
            assert payload['unresolved_typed_data_pointer_site_count'] == 1
            assert payload['unresolved_typed_data_pointer_sites'][0]['reason'] == 'unmapped_runtime_symbol'
        assert result['typed_data_pointer_scope'] == (
            'frozen_typed_expressions_only_not_all_alias_or_runtime_fixup_proof')
        # Discovery is deliberately separate from the old proof/lease adapter.
        assert result['proof_status'] == 'obligations_open'
    finally:
        artifact.close()


def test_local_source_offset_is_not_a_coincident_runtime_workspace(tmp_path):
    from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
    from amiga_reversing.disasm.c_backend import build_listing_artifact_profile_from_binary_source
    value = 0x7f0
    data = bytes.fromhex('6004') + value.to_bytes(4, 'big') + bytes.fromhex('4e75')
    data += bytes(value-len(data)) + bytes.fromhex('12345678')
    binary = tmp_path/'source.bin'
    binary.write_bytes(data)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x10000,
        entrypoint=0x10000, code_start_offset=0, display_path=str(binary),
        analysis_cache_path=tmp_path/'analysis')
    metadata = dict(memory_regions=[
        region(region_id='body', name='body', runtime_address=0x7f0, size=0x900),
        region(region_id='source_image', name='source_image', runtime_address=0x10000,
               size=len(data), source_domain='mapped_source')],
        seeded_entities=[dict(addr=2, end=6, hunk=0, unit='long', struct_name='Frame',
                              field_name='source', field_type='long', value_kind='target_pointer'),
                         dict(addr=value, end=value+4, hunk=0, unit='byte', name='source_data')])
    path=tmp_path/'metadata.json'
    path.write_text(json.dumps(metadata))
    _,_,artifact=build_listing_artifact_profile_from_binary_source(source, metadata_path=path)
    try:
        result=artifact.memory_regions_payload()
        row=artifact.row_for_source_offset(section_index=0, offset=2)
        assert row['pointer_resolution']['outcome']=='symbolic'
        assert row['pointer_resolution']['target_offset']==value
        by_id={r['region_id']:r for r in result['items']}
        assert by_id['body']['typed_data_pointer_sites']==[]
        site=by_id['source_image']['typed_data_pointer_sites'][0]
        assert site['has_target'] is True
        assert site['target_section_index']==0 and site['target_offset']==value
        assert site['encoded_value']==0x7f0 and site['address']==0x107f0
        assert site['address_domain']=='legacy'
    finally:
        artifact.close()
