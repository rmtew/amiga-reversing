"""Canonical fixed layout definitions: placement is not export admission."""
import json
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm.c_backend import build_flat_m68k_bytes_listing_artifact_profile
from amiga_reversing.disasm.memory_regions import validate_layout, validate_region
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions, load_manual_projection
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload


def region(identity, address, size=16, parent='', kind='workspace'):
    return dict(region_id=identity, name=identity+'_base', runtime_address=address,
                size=size, alignment=2, source_domain='runtime_only', memory_class='cpu_ram',
                lifetime='persistent', dma_access='chip', region_kind=kind, parent_region_id=parent)


def layout(placements=(), **changes):
    return dict(schema_version=1, layout_id='diagnostic', chip_bytes=0x100000,
                placements=[dict(region_id=k, runtime_address=v) for k, v in placements]) | changes


def project(tmp_path, regions, config):
    path = tmp_path/'metadata.json'
    path.write_text(json.dumps(dict(memory_regions=regions, memory_layouts=[config])))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        bytes.fromhex('4e75'), display_path='layout-fixture', metadata_path=path)
    try:
        return artifact.memory_layouts_payload()['items'][0]
    finally:
        artifact.close()


def test_image_workspace_display_and_inherited_subregion(tmp_path):
    regions = [region('image', 0x10000, 256, kind='image'),
               region('cursor', 0x65370, 136), region('cursor1', 0x653b4, 68, parent='cursor'),
               region('display', 0x70000, 32000, kind='display')]
    result = project(tmp_path, regions, layout([('image', 0x80000), ('cursor', 0xe0000)]))
    assert result['status'] == 'placement_valid'
    assert result['export_ready'] is False
    assert result['reason'] is None
    items = {r['region_id']: r for r in result['regions']}
    assert items['image']['runtime_address'] == 0x80000
    assert items['cursor1']['runtime_address'] == 0xe0044
    assert items['cursor1']['parent_offset'] == 68
    assert items['display']['runtime_address'] == 0x70000
    assert items['display']['region_kind'] == 'display'


@pytest.mark.parametrize(('regions', 'placements', 'reason'), [
    ([region('a', 0x4000, parent='missing')], [], 'missing_parent'),
    ([region('a', 0x4000, parent='b'), region('b', 0x4000, parent='a')], [], 'parent_cycle'),
    ([region('a', 0x4000), region('b', 0x4008, 16, parent='a')], [], 'outside_original_parent'),
    ([region('a', 0x4000), region('b', 0x4008, 8, parent='a')], [('b', 0x5000)], 'independent_child_placement_unsupported'),
    ([region('a', 0x4000)], [('unknown', 0x5000)], 'unknown_placement_region'),
    ([region('a', 0x4000)], [('a', 0x100000)], 'outside_declared_chip_ram'),
    ([region('a', 0x4000)], [('a', 0x101)], 'invalid_extent_or_alignment'),
    ([region('a', 0x4000)], [('a', 0x100)], 'reserved_low_memory'),
    ([region('a', 0x4000), region('b', 0x5000)], [('b', 0x4008)], 'unrelated_region_overlap'),
])
def test_native_refusals_do_not_qualify_export(tmp_path, regions, placements, reason):
    result = project(tmp_path, regions, layout(placements))
    assert result['status'] == 'refused'
    assert result['reason'] == reason
    assert result['export_ready'] is False and result['regions'] == []


@pytest.mark.parametrize('changes', [
    {'schema_version': True}, {'schema_version': 2}, {'chip_bytes': True},
    {'chip_bytes': 0x200000}, {'layout_id': 'bad\x00id'}, {'placements': [1]},
    {'placements': [{'region_id': 'a', 'runtime_address': True}]},
    {'placements': [{'region_id': 'a', 'runtime_address': 0x1000000}]},
    {'placements': [{'region_id': 'a', 'runtime_address': 2}]*2},
    {'placements': [{'region_id': str(i), 'runtime_address': 2} for i in range(17)]},
    {'assume_safe': True},
])
def test_invalid_authored_configuration_rejected(changes):
    with pytest.raises(ValueError, match='memory_layout'):
        validate_layout(layout() | changes)


def test_identity_preserving_region_update_and_layout_replay(tmp_path):
    from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
    from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
    from amiga_reversing.disasm.effective_metadata import effective_metadata_text
    binary = tmp_path/'fixture.bin'
    binary.write_bytes(bytes.fromhex('4e75'))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    original = region('cursor', 0x65370, 136)
    updated = original | {'region_kind': 'storage'}
    actions = append_manual_actions(tmp_path, actions=[
        (ManualActionKind.CREATE_MANUAL_MEMORY_REGION, {'memory_region': original}),
        (ManualActionKind.UPDATE_MANUAL_MEMORY_REGION, {'memory_region': updated}),
        (ManualActionKind.CREATE_MANUAL_MEMORY_LAYOUT, {'memory_layout': layout([('cursor', 0xe0000)])}),
    ], binary_source=source)
    state = load_manual_projection(tmp_path)
    assert state.memory_regions == (updated,)
    assert state.memory_layouts == (layout([('cursor', 0xe0000)]),)
    assert validate_region(original) == original
    prefix = (tmp_path/'manual_actions.jsonl').read_bytes()
    append_manual_actions(tmp_path, actions=[(ManualActionKind.UNDO_ACTION,
        {'undoes_action_id': actions[1]['action_id']})], binary_source=source)
    assert load_manual_projection(tmp_path).memory_regions == (original,)
    assert (tmp_path/'manual_actions.jsonl').read_bytes().startswith(prefix)
    path = tmp_path/'effective.json'
    path.write_text(effective_metadata_text(tmp_path, binary_source=source))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        binary.read_bytes(), display_path=str(binary), metadata_path=path)
    try:
        result = artifact.memory_layouts_payload()['items'][0]
        assert result['status'] == 'placement_valid'
        assert result['regions'][0]['runtime_address'] == 0xe0000
        assert result['export_ready'] is False
    finally:
        artifact.close()


def test_commands_share_normal_catalog_validation():
    kind, payload = target_catalog_manual_payload('target.memory_layout.add', parameters=layout())
    assert kind == 'create_manual_memory_layout' and payload['memory_layout'] == layout()
    kind, payload = target_catalog_manual_payload('target.memory_region.update', parameters=region('r', 0x4000))
    assert kind == 'update_manual_memory_region' and payload['memory_region']['region_id'] == 'r'


def test_malformed_native_placement_array_refused(tmp_path):
    path = tmp_path/'bad.json'
    path.write_text(json.dumps({'memory_layouts': [layout() | {'placements': [1]}]}))
    with pytest.raises(RuntimeError, match='parsing target metadata memory layout'):
        build_flat_m68k_bytes_listing_artifact_profile(bytes.fromhex('4e75'),
            display_path='invalid-layout', metadata_path=path)


@pytest.mark.parametrize('value', [[1], [1, layout()], [layout(), 1], [None], 'not-an-array', {}])
def test_native_layout_import_refuses_scalar_and_mixed_entries(tmp_path, value):
    path = tmp_path/'bad.json'
    path.write_text(json.dumps({'memory_layouts': value}))
    with pytest.raises(RuntimeError, match='memory layout'):
        build_flat_m68k_bytes_listing_artifact_profile(bytes.fromhex('4e75'),
            display_path='invalid-layout-array', metadata_path=path)


@pytest.mark.parametrize(('field', 'value'), [('schema_version', 1.5), ('schema_version', 1.0),
    ('schema_version', True), ('chip_bytes', 1048576.5), ('runtime_address', 16384.5),
    ('runtime_address', 1e10), ('runtime_address', -1), ('runtime_address', 0x100000000)])
def test_native_layout_numeric_fields_match_authored_integer_rules(tmp_path, field, value):
    config = layout([('a', 0x4000)])
    if field == 'runtime_address':
        config['placements'][0][field] = value
    else:
        config[field] = value
    path = tmp_path/'fraction.json'
    path.write_text(json.dumps({'memory_layouts': [config]}))
    with pytest.raises(RuntimeError, match='memory layout'):
        build_flat_m68k_bytes_listing_artifact_profile(bytes.fromhex('4e75'),
            display_path='invalid-layout-number', metadata_path=path)


@pytest.mark.parametrize('token', ['1e0', '1E+0', '01', '+1', '1junk'])
def test_layout_boundary_rejects_non_integer_tokens(tmp_path, token):
    path = tmp_path/'token.json'
    # Valid JSON exponents reach native validation; malformed JSON may be
    # refused earlier by the transport's JSON reader.
    text = json.dumps({'memory_layouts': [layout()]})
    path.write_text(text.replace('"schema_version": 1', '"schema_version": '+token))
    with pytest.raises((RuntimeError, json.JSONDecodeError)):
        build_flat_m68k_bytes_listing_artifact_profile(bytes.fromhex('4e75'),
            display_path='invalid-number-token', metadata_path=path)


@pytest.mark.parametrize('moved', [False, True])
def test_native_layout_render_and_independent_assembly(tmp_path, moved):
    config = layout([('image', 0x80000), ('cursor', 0xe0000)] if moved else [])
    meta = dict(memory_regions=[region('image', 0x10000, 8, kind='image'),
        region('cursor', 0x65370, 136), region('cursor1', 0x653b4, 68, parent='cursor'),
        region('display', 0x70000, 32000, kind='display')], memory_layouts=[config],
        selected_memory_layout_id='diagnostic',
        execution_views=[dict(source_start=0, source_end=8, base_addr=0x10000)],
        target_equates=[dict(name='CURSOR', value=0x65370, value_representation='hex',
            address_domain='runtime', extent_bytes=68, group='cursor'),
            dict(name='SCALAR', value=0x65370, value_representation='hex')])
    path = tmp_path/'meta.json'
    path.write_text(json.dumps(meta))
    original = bytes.fromhex('41f9000653704e75')
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(original,
        display_path='layout-render-fixture', metadata_path=path)
    try:
        text = artifact.inline_source_text_with_profile()[0]
        assert 'cursor1_base\tEQU\tcursor_base+$44' in text
        assert 'CURSOR\tEQU\tcursor_base' in text
        assert 'absolute_slot_00065370\tEQU\tcursor_base' in text
        assert 'SCALAR\tEQU\t$65370' in text
        assert 'display_base\tEQU\t$70000' in text
        assert 'ORG image_base' in text
        source, output = tmp_path/'layout.s', tmp_path/'layout.bin'
        source.write_text(text)
        vasm = Path(__file__).resolve().parents[1]/'tools/vasmm68k_mot.exe'
        subprocess.run([str(vasm), '-Fbin', '-m68000', '-no-opt', '-o', str(output), str(source)],
                       check=True, capture_output=True)
        assert output.read_bytes() == (bytes.fromhex('41f9000e00004e75') if moved else original)
    finally:
        artifact.close()


def test_unknown_selected_layout_refused(tmp_path):
    path = tmp_path/'meta.json'
    path.write_text(json.dumps(dict(selected_memory_layout_id='missing')))
    with pytest.raises(RuntimeError):
        build_flat_m68k_bytes_listing_artifact_profile(bytes.fromhex('4e75'),
            display_path='missing-selection', metadata_path=path)
