"""Canonical bound owner spans survive leaf projection without widening leaves."""
from dataclasses import replace

import pytest

from amiga_reversing.disasm.effective_metadata import _data_block_bound_struct_entities
from amiga_reversing.disasm.target_metadata import (
    CustomStructFieldMetadata,
    CustomStructMetadata,
    DataBlockElementKind,
    DataBlockElementMetadata,
    DataBlockLayoutMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    target_metadata_json_payload,
)

REVIEW = {'seed_origin': TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
          'review_status': TargetMetadataReviewStatus.SEEDED, 'citation': 'fixture'}


def test_named_bound_array_retains_exact_owner_only_on_first_leaf():
    struct = CustomStructMetadata(name='Node', size=18, fields=(
        CustomStructFieldMetadata(name='first', type='long', offset=0, size=4,
            available_since='1.0', struct=None, pointer_struct=None),
        CustomStructFieldMetadata(name='rest', type='byte', offset=4, size=14,
            available_since='1.0', struct=None, pointer_struct=None)), **REVIEW)
    element = DataBlockElementMetadata(layout_id='nodes', offset=8, width=36,
        kind=DataBlockElementKind.STRUCT, name='node_array', array_count=2, array_stride=18,
        type_binding={'binding_kind': 'custom_struct', 'bound_type_id': 'Node'}, **REVIEW)
    layout = DataBlockLayoutMetadata(layout_id='nodes', hunk=0, source_start=100, source_end=144,
        name='scene', elements=(element,), **REVIEW)
    leaves = _data_block_bound_struct_entities(layout, element, {'Node': struct})
    assert [leaf.addr for leaf in leaves] == [108, 112, 126, 130]
    assert [leaf.end - leaf.addr for leaf in leaves] == [4, 14, 4, 14]
    assert leaves[0].name == 'node_array'
    assert (leaves[0].source_owner_start, leaves[0].source_owner_size) == (108, 36)
    assert all(leaf.source_owner_size is None for leaf in leaves[1:])
    payload = target_metadata_json_payload(TargetMetadata(target_type='program',
        entry_register_seeds=(), seeded_entities=leaves))
    assert payload['seeded_entities'][0]['source_owner_size'] == 36
    assert all('source_owner_size' not in entity for entity in payload['seeded_entities'][1:])
    assert SeededEntityMetadata.from_dict(payload['seeded_entities'][0]) == leaves[0]
    unnamed = _data_block_bound_struct_entities(replace(layout, name=None),
        replace(element, name=None), {'Node': struct})
    assert all(leaf.source_owner_size is None for leaf in unnamed)


@pytest.mark.parametrize(('start', 'size', 'name'), [
    (None, 36, 'nodes'), (108, None, 'nodes'), (107, 36, 'nodes'),
    (108, 0, 'nodes'), (108, 3, 'nodes'), (108, 0xFFFFFFFF, 'nodes'),
    (True, 36, 'nodes'), (108, 36, None),
])
def test_owner_span_rejects_unpaired_nonfirst_or_unbounded_leaf(start, size, name):
    with pytest.raises(ValueError, match='source owner span'):
        SeededEntityMetadata(addr=108, end=112, name=name, source_owner_start=start,
            source_owner_size=size, **REVIEW)


@pytest.mark.parametrize('span', [
    {'source_owner_size': 4}, {'source_owner_start': 2},
    {'source_owner_start': 1, 'source_owner_size': 4},
    {'source_owner_start': 2, 'source_owner_size': 3},
    {'source_owner_start': 2, 'source_owner_size': 0},
    {'source_owner_start': 2, 'source_owner_size': 0xFFFFFFFF},
    {'end': 2, 'source_owner_start': 2, 'source_owner_size': 4},
    {'end': 1, 'source_owner_start': 2, 'source_owner_size': 4},
])
def test_native_codec_rejects_malformed_owner_span(tmp_path, span):
    import json

    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        RawAddressModel,
        RawBinarySource,
    )
    from amiga_reversing.disasm.c_backend import validate_policy_storage_with_c_backend
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT

    binary = tmp_path / 'input.bin'
    binary.write_bytes(bytes.fromhex('6004000000004e75'))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    metadata = {'seeded_entities': [{'addr': 2, 'end': 6, 'hunk': 0, 'unit': 'long', 'name': 'nodes', **span}]}
    with pytest.raises(RuntimeError, match='failed parsing target metadata seeded entity'):
        validate_policy_storage_with_c_backend(source, metadata_text=json.dumps(metadata),
            project_root=PROJECT_ROOT)


def test_native_policy_exports_owner_extent_without_widening_leaf(tmp_path):
    import json

    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        RawAddressModel,
        RawBinarySource,
    )
    from amiga_reversing.disasm.c_backend import (
        effective_policy_project_source_with_c_backend,
    )
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT

    binary = tmp_path / 'input.bin'
    binary.write_bytes(bytes.fromhex('600800000000000000004e75'))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    entity = SeededEntityMetadata(addr=2, end=6, unit='long', name='nodes',
        source_owner_start=2, source_owner_size=8, **REVIEW)
    metadata = target_metadata_json_payload(TargetMetadata(target_type='program',
        entry_register_seeds=(), seeded_entities=(entity,)))
    path = tmp_path / 'metadata.json'
    path.write_text(json.dumps(metadata))
    payload = effective_policy_project_source_with_c_backend(source, metadata_path=path,
        project_root=PROJECT_ROOT)
    policy = payload['analysis_policy']
    native = next(item for item in policy['structured_data_items'] if item['label'] == 'nodes')
    assert native['offset'] == 2 and native['size'] == 4
    assert native['source_owner_start'] == 2 and native['source_owner_size'] == 8


@pytest.mark.parametrize('end', [108, 107])
def test_owner_span_requires_a_positive_leaf(end):
    with pytest.raises(ValueError, match='source owner span'):
        SeededEntityMetadata(addr=108, end=end, name='nodes', source_owner_start=108,
            source_owner_size=36, **REVIEW)
