"""Packed scalar arrays retain a shared type without per-leaf policy symbols."""

import subprocess
from dataclasses import replace

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import (
    _data_block_compact_struct_array_entity,
    effective_metadata_file,
    effective_target_metadata,
)
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import (
    CustomStructFieldMetadata, DataBlockElementKind, ManualRepresentationMetadata,
    ManualRepresentationStyle, TargetEquateMetadata, TargetMetadata,
    TargetMetadataReviewStatus, TargetMetadataSeedOrigin, write_target_metadata,
)


def fixture(tmp_path, *, count=3, kind='array', anchor=False, symbolic_value=False,
            width=2, start=32, address_domain=None, selected=42):
    binary = tmp_path / 'cells.bin'
    load = 0x1000 if address_domain is not None else 0
    lea = 'lea.l SELECTED_CELL.l,a0' if address_domain is not None else 'lea.l SELECTED_CELL(pc),a0'
    code, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        f' SELECTED_CELL EQU {load+selected}\n SECTION code,code\n ORG ${load:X}\n {lea}\n'
        ' move.w (a0)+,d0\n move.w (a0),d1\n move.w 4(a0),d2\n rts\n')
    cell = (bytes.fromhex('0000123456789abc') if width == 2
            else b''.join((17*i).to_bytes(width, 'big') for i in range(4)))
    original = code + bytes(start-len(code)) + cell * count
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE if load else RawAddressModel.LOCAL_OFFSET,
        load_address=load, entrypoint=load,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    actions = []
    def add(command, parameters):
        action_kind, payload = target_catalog_manual_payload(command, parameters)
        actions.append((ManualActionKind(action_kind), payload))
        return payload
    unit = {1:'byte', 2:'word', 4:'long'}[width]
    add('target.custom_struct.add', dict(name='Cell', size=4*width, fields=[
        dict(name=f'{unit}_{i}', type='U'+unit.upper(), offset=width*i, size=width) for i in range(4)]))
    layout = add('target.data_block.layout.create', dict(hunk=0, source_start=start,
        source_end=len(original), name='cells', role='bitmap', default_unit=unit))
    lid = layout['data_block_layout']['layout_id']
    add('target.data_block.element.set', dict(layout_id=lid, offset=0, width=count*4*width,
        kind=kind, name='cells', array_count=count, array_stride=4*width,
        binding_kind='custom_struct', type_id='Cell', representation='hex'))
    if anchor:
        actions.append((ManualActionKind.CREATE_MANUAL_LABEL, {'label': dict(
            label_id='selected', name='selected_cell_word', scope='global',
            address_domain='source', hunk=0, addr=42)}))
    if symbolic_value:
        add('target.equate.add', dict(name='AUTHORED_VALUE', value=0x1234))
        actions.append((ManualActionKind.CREATE_MANUAL_REPRESENTATION, {'representation': dict(
            representation_id='selected-value', hunk=0, addr=34, end=36,
            element_kind='data_literal', style='symbol', width_bytes=2,
            value=0x1234, symbol='AUTHORED_VALUE')}))
    if address_domain in {'constant', 'runtime'}:
        equate = dict(name='WORKSPACE_ADDRESS', value=load+42)
        if address_domain == 'runtime':
            equate.update(address_domain='runtime', group='workspace', extent_bytes=2)
        add('target.equate.add', equate)
        actions.append((ManualActionKind.CREATE_MANUAL_REPRESENTATION, {'representation': dict(
            representation_id='address', hunk=0, addr=0, end=6, operand_index=0,
            element_kind='absolute_address', style='symbol', width_bytes=4,
            value=load+42, symbol='WORKSPACE_ADDRESS')}))
    append_manual_actions(tmp_path, binary_source=source, actions=actions)
    return source, original, effective_target_metadata(tmp_path)


def assert_package_bytes(tmp_path, text, original):
    path = tmp_path/'rendered.s';path.write_text(text)
    rebuilt, _ = c_backend.assemble_platform_source_path_with_c_backend('amiga-raw', path)
    assert rebuilt == original
    output = tmp_path/'oracle.bin'
    result = subprocess.run([str(c_backend.PROJECT_ROOT/'tools/vasmm68k_mot.exe'),
        '-quiet', '-Fbin', '-o', str(output), str(path)], cwd=tmp_path,
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert output.read_bytes() == original


def test_bulk_array_uses_one_native_range_and_label_beyond_the_old_leaf_capacity(tmp_path):
    source, original, metadata = fixture(tmp_path, count=10000)
    assert len(metadata.seeded_entities) == 1
    owner = metadata.seeded_entities[0]
    assert (owner.addr, owner.end, owner.name, owner.struct_name, owner.field_name, owner.unit) == (
        32, len(original), 'cells', 'Cell', None, 'word')
    assert (owner.source_owner_start, owner.source_owner_size) == (32, 80000)
    assert metadata.data_block_layouts[0].elements[0].array_count == 10000
    with effective_metadata_file(tmp_path) as path:
        policy = c_backend.effective_policy_project_source_with_c_backend(
            source, metadata_path=path)['analysis_policy']
    assert policy['structured_data_item_count'] == policy['named_label_count'] == 1
    assert policy['structured_data_items'][0]['struct_name'] == 'Cell'
    assert policy['structured_data_items'][0]['size'] == 80000


@pytest.mark.parametrize('width,start', [(1,32), (2,32), (4,34)])
def test_packed_array_preserves_native_unit_and_supported_alignment(tmp_path, width, start):
    source, original, metadata = fixture(tmp_path, width=width, start=start)
    assert len(metadata.seeded_entities) == 1
    assert metadata.seeded_entities[0].unit == {1:'byte', 2:'word', 4:'long'}[width]
    with effective_metadata_file(tmp_path) as path:
        text = c_backend.render_project_source_with_c_backend(source, metadata_path=path)
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)
    assert rebuilt == original


def test_array_with_authored_scalar_expression_retains_its_field_rendering(tmp_path):
    source, original, metadata = fixture(tmp_path, symbolic_value=True)
    assert metadata.data_block_layouts[0].elements[0].kind is DataBlockElementKind.ARRAY
    assert len(metadata.seeded_entities) == 12
    with effective_metadata_file(tmp_path) as path:
        text = c_backend.render_project_source_with_c_backend(source, metadata_path=path)
    assert 'dc.w AUTHORED_VALUE' in text
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)
    assert rebuilt == original


def test_grouped_asset_has_one_array_declaration_and_no_repeated_owner_comments(tmp_path):
    source, original, metadata = fixture(tmp_path, count=64, selected=32)
    with effective_metadata_file(tmp_path) as path:
        package = c_backend.listing_artifact_source_package_with_c_backend(
            source, metadata_path=path, minimum_asset_size=128)
    text = package['source_text']
    assert len(package['assets']) == 1 and text.count('INCBIN') == 1
    assert text.count('; ARRAY Cell[64]') == 1
    assert '; cells\n' not in text and len(text.splitlines()) < 45
    for asset in package['assets']:
        path = tmp_path/asset['path'];path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes.fromhex(asset['data_hex']))
    assert_package_bytes(tmp_path, text, original)


@pytest.mark.parametrize('domain', ['unannotated', 'constant', 'runtime'])
def test_runtime_only_address_does_not_inherit_overlapping_source_array_type(tmp_path, domain):
    source, original, metadata = fixture(tmp_path, address_domain=domain)
    assert len(metadata.seeded_entities) == 1
    with effective_metadata_file(tmp_path) as path:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=path)[2]
    try:
        fields = artifact.query_payload('fields', limit=20)['items']
        resolved = {f['source_offset']: f['field_name'] for f in fields if f.get('field_name')}
        assert resolved == ({} if domain == 'runtime' else {6:'word_1',8:'word_2',10:'word_0'})
        text = artifact.inline_source_text_with_profile()[0]
        if domain != 'unannotated':
            assert 'lea.l WORKSPACE_ADDRESS.l,a0' in text
    finally:
        artifact.close()
    assert_package_bytes(tmp_path, text, original)


@pytest.mark.parametrize('count', [2, 3])
@pytest.mark.parametrize('anchor', [False, True])
def test_native_interior_cursor_and_named_boundary_survive_grouping(tmp_path, count, anchor):
    source, original, metadata = fixture(tmp_path, count=count, anchor=anchor)
    with effective_metadata_file(tmp_path) as path:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=path)[2]
    try:
        fields = artifact.query_payload('fields', limit=20)['items']
        resolved = {f['source_offset']: f['field_name'] for f in fields if f.get('field_name')}
        assert resolved[4] == 'word_1' and resolved[6] == 'word_2'
        assert resolved.get(8) == ('word_0' if count == 3 else None)
        text = artifact.inline_source_text_with_profile()[0]
    finally:
        artifact.close()
    if anchor:
        assert 'selected_cell_word:' in text
    assert 'lea.l cells+10(pc),a0' in text
    assert 'cells_word_3_1:' not in text
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)
    assert rebuilt == original
    path = tmp_path/'rendered.s';path.write_text(text)
    output = tmp_path/'oracle.bin'
    result = subprocess.run([str(c_backend.PROJECT_ROOT/'tools/vasmm68k_mot.exe'),
        '-quiet', '-Fbin', '-o', str(output), str(path)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert output.read_bytes() == original


@pytest.mark.parametrize('exception', ['struct', 'mixed', 'gap', 'pointer', 'stride', 'binary', 'value', 'alias'])
def test_field_specific_or_nonuniform_presentations_keep_the_leaf_path(tmp_path, exception):
    source, original, metadata = fixture(tmp_path)
    layout = metadata.data_block_layouts[0]
    element = layout.elements[0]
    struct = metadata.custom_structs[0]
    representations, equates = [], []
    if exception == 'struct':
        element = replace(element, kind=DataBlockElementKind.STRUCT)
    elif exception == 'mixed':
        struct = replace(struct, fields=(CustomStructFieldMetadata(name='byte', type='UBYTE', offset=0, size=1), *struct.fields[1:]))
    elif exception == 'gap':
        struct = replace(struct, fields=struct.fields[1:])
    elif exception == 'pointer':
        struct = replace(struct, fields=(CustomStructFieldMetadata(name='ptr', type='LONG', offset=0, size=4,
            pointer_struct='Cell', value_kind='struct_pointer'), *struct.fields[2:]))
    elif exception == 'stride':
        element = replace(element, array_stride=10)
    elif exception == 'binary':
        element = replace(element, representation=ManualRepresentationStyle.BINARY)
    elif exception == 'value':
        representations.append(ManualRepresentationMetadata(addr=34, end=36, hunk=0,
            style=ManualRepresentationStyle.SYMBOL, symbol='AUTHORED_VALUE', element_kind='data_literal',
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.SEEDED, citation='authored value'))
    elif exception == 'alias':
        equates.append(TargetEquateMetadata(name='SELECTED_FIELD', value=42, value_expression='cells_word_1_1',
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.SEEDED, citation='authored alias'))
    assert _data_block_compact_struct_array_entity(
        layout, element, {'Cell': struct}, representations, equates) is None
