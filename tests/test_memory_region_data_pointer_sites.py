"""Allocation preparation must see typed data pointers, not scalar lookalikes."""
import json

import pytest

from amiga_reversing.disasm.c_backend import build_flat_m68k_bytes_listing_artifact_profile
from tests.test_memory_regions import region


@pytest.mark.parametrize('typed,value,group,expected', [
    (True, 0x8004, 'buffers', 1),
    (False, 0x8004, 'buffers', 0),
    (True, 0x8010, 'buffers', 0),
    (True, 0x8004, 'other_namespace', 1),
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
        result = artifact.memory_regions_payload()['items'][0]
        assert result['typed_data_pointer_site_count'] == expected
        sites = result['typed_data_pointer_sites']
        assert len(sites) == expected
        if expected:
            symbolic = group == 'buffers'
            assert sites == [dict(source_section_index=0, source_offset=2, width=4,
                address=value, region_offset=4, kind='table_entry', symbolic=symbolic,
                reason='resolved_runtime_symbol' if symbolic else 'unmapped_runtime_symbol',
                target_symbol='BITMAP_STORAGE' if symbolic else '')]
        assert result['typed_data_pointer_scope'] == (
            'frozen_typed_expressions_only_not_all_alias_or_runtime_fixup_proof')
        # Discovery is deliberately separate from the old proof/lease adapter.
        assert result['proof_status'] == 'obligations_open'
    finally:
        artifact.close()
