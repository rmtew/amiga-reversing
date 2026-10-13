"""Explicit pointer domains retain canonical codec and conservative bounds."""
import pytest

from amiga_reversing.disasm.pointer_domains import (
    validate_pointer_domain,
    validate_runtime_address_symbol,
)
from amiga_reversing.disasm.target_metadata import (
    CustomStructFieldMetadata,
    TargetEquateMetadata,
)


def _assert_vasm_bytes(tmp_path, text, original):
    import subprocess

    from amiga_reversing.disasm.project_paths import PROJECT_ROOT

    source_path = tmp_path / 'rendered.s'
    output_path = tmp_path / 'rendered.bin'
    source_path.write_text(text)
    result = subprocess.run([str(PROJECT_ROOT / 'tools' / 'vasmm68k_mot.exe'), '-quiet', '-Fbin',
        '-o', str(output_path), str(source_path)], capture_output=True, text=True,
        timeout=10, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert output_path.read_bytes() == original


@pytest.mark.parametrize(('domain', 'group'), [('mapped_source', None), ('runtime_only', 'generated_masks')])
def test_pointer_field_codec_retains_domain(domain, group):
    payload = {'name': 'image', 'type': 'long', 'offset': 0, 'size': 4,
               'available_since': '1.0', 'struct': None, 'pointer_struct': None,
               'value_kind': 'target_pointer', 'pointer_address_domain': domain,
               'pointer_symbol_group': group}
    field = CustomStructFieldMetadata.from_dict(payload)
    assert field.pointer_address_domain == domain
    assert field.pointer_symbol_group == group


def test_struct_pointer_codec_accepts_declared_pointee():
    field = CustomStructFieldMetadata.from_dict({'name': 'next', 'type': 'long', 'offset': 0,
        'size': 4, 'available_since': '1.0', 'struct': None,
        'value_kind': 'struct_pointer', 'pointer_struct': 'Node'})
    assert field.pointer_struct == 'Node'


@pytest.mark.parametrize(('kind', 'size', 'domain', 'group'), [
    ('scalar', 4, 'mapped_source', None), ('target_pointer', 2, 'mapped_source', None),
    ('target_pointer', 4, 'runtime_only', None), ('target_pointer', 4, 'mapped_source', 'masks'),
    ('target_pointer', 4, 'other', None), ('target_pointer', 4, 'runtime_only', 'x' * 64),
])
def test_invalid_field_domain_is_rejected(kind, size, domain, group):
    with pytest.raises(ValueError, match='pointer|unsupported'):
        validate_pointer_domain(value_kind=kind, size=size, address_domain=domain, symbol_group=group)


def test_runtime_symbol_codec_preserves_unsigned_end_boundary():
    equate = TargetEquateMetadata.from_dict({'name': 'buffer', 'value': 0xFFFFFFFC,
        'group': 'masks', 'address_domain': 'runtime', 'extent_bytes': 4,
        'seed_origin': 'manual_analysis', 'review_status': 'seeded', 'citation': 'fixture'})
    assert equate.value == 0xFFFFFFFC
    assert equate.extent_bytes == 4
    assert equate.group == 'masks'


@pytest.mark.parametrize(('value', 'extent', 'group'), [(0xFFFFFFFC, 5, 'masks'), (0, 0, 'masks'),
    (-1, 1, 'masks'), (0, 1, ''), (0, 1, 'x' * 64)])
def test_invalid_runtime_namespace_bounds(value, extent, group):
    with pytest.raises(ValueError, match='runtime address symbol'):
        validate_runtime_address_symbol(value=value, extent_bytes=extent, group=group, address_domain='runtime')


def test_legacy_equate_and_pointer_remain_optional():
    validate_pointer_domain(value_kind=None, size=2, address_domain=None, symbol_group=None)
    validate_runtime_address_symbol(value=-1, group=None, address_domain=None, extent_bytes=None)


@pytest.mark.parametrize(('value', 'banks', 'reason', 'expected'), [
    (0x8004, [('mask_bank', 0x8000, 16, 'masks')], 'resolved_runtime_symbol', 'mask_bank+$4'),
    (0, [('mask_bank', 0x8000, 16, 'masks')], 'null_pointer', None),
    (0x8010, [('mask_bank', 0x8000, 16, 'masks')], 'unmapped_runtime_symbol', None),
    (0x8004, [('mask_bank', 0x8000, 16, 'other')], 'unmapped_runtime_symbol', None),
    (0x8004, [('mask_bank', 0x8000, 16, 'masks'), ('second_bank', 0x8000, 16, 'masks')],
     'ambiguous_runtime_symbol', None),
    (0x80000000, [('mask_bank', 1, 0xFFFFFFFF, 'masks')], 'resolved_runtime_symbol', 'mask_bank+$7FFFFFFF'),
    (0x80000001, [('mask_bank', 1, 0xFFFFFFFF, 'masks')], 'unsupported_addend', None),
    (0xFFFFFFFE, [('mask_bank', 0xFFFFFFFC, 4, 'masks')], 'resolved_runtime_symbol', 'mask_bank+$2'),
])
def test_native_runtime_pointer_domains(tmp_path, value, banks, reason, expected):
    import json

    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        RawAddressModel,
        RawBinarySource,
    )
    from amiga_reversing.disasm.c_backend import (
        assemble_platform_source_text_with_c_backend,
        build_listing_artifact_profile_from_binary_source,
    )
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT

    original = bytes.fromhex('6004') + value.to_bytes(4, 'big') + bytes.fromhex('4e75')
    binary = tmp_path / 'input.bin'
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    metadata = {'seeded_entities': [{'addr': 2, 'end': 6, 'hunk': 0, 'unit': 'long',
        'struct_name': 'Frame', 'field_name': 'mask', 'field_type': 'long',
        'value_kind': 'target_pointer', 'pointer_address_domain': 'runtime_only',
        'pointer_symbol_group': 'masks'}],
        'target_equates': [{'name': name, 'value': base, 'extent_bytes': extent,
            'group': group, 'address_domain': 'runtime'} for name, base, extent, group in banks]}
    path = tmp_path / 'metadata.json'
    path.write_text(json.dumps(metadata))
    _, _, artifact = build_listing_artifact_profile_from_binary_source(source, metadata_path=path,
        project_root=PROJECT_ROOT)
    try:
        row = artifact.row_for_source_offset(section_index=0, offset=2)
        assert row is not None
        resolution = row['pointer_resolution']
        assert resolution['reason'] == reason
        assert resolution['encoded_value'] == value
        assert resolution['address_domain'] == 'runtime_only'
        assert 'target_offset' not in resolution
        text, _ = artifact.inline_source_text_with_profile()
        if expected:
            assert expected in row['text']
            assert resolution['outcome'] == 'symbolic'
        else:
            assert resolution['outcome'] == ('null' if value == 0 else 'unresolved')
        rebuilt, _ = assemble_platform_source_text_with_c_backend('amiga-raw', text, project_root=PROJECT_ROOT)
        assert rebuilt == original
        _assert_vasm_bytes(tmp_path, text, original)
    finally:
        artifact.close()


@pytest.mark.parametrize(('value', 'views', 'reason', 'expected'), [
    (0x100C, [], 'resolved_source', 'image_bank+$4'),
    (0x800C, [], 'unmapped_source', None),
    (0x800C, [{'source_start': 8, 'source_end': 24, 'base_addr': 0x8008}], 'encoded_value_mismatch', None),
    (0x100C, [{'source_start': 8, 'source_end': 24, 'base_addr': 0x1008},
              {'source_start': 10, 'source_end': 24, 'base_addr': 0x1008}], 'ambiguous_source', None),
])
def test_native_mapped_source_pointer_uses_owner_offset(tmp_path, value, views, reason, expected):
    import json

    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        RawAddressModel,
        RawBinarySource,
    )
    from amiga_reversing.disasm.c_backend import (
        assemble_platform_source_text_with_c_backend,
        build_listing_artifact_profile_from_binary_source,
    )
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT

    original = bytes.fromhex('6004') + value.to_bytes(4, 'big') + bytes.fromhex('4e75') + bytes(range(16))
    binary = tmp_path / 'input.bin'
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x1000, entrypoint=0x1000,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    metadata = {'seeded_entities': [
        {'addr': 2, 'end': 6, 'hunk': 0, 'unit': 'long', 'struct_name': 'Frame',
         'field_name': 'pixels', 'field_type': 'long', 'value_kind': 'target_pointer',
         'pointer_address_domain': 'mapped_source'},
        {'addr': 8, 'end': 24, 'hunk': 0, 'unit': 'byte', 'name': 'image_bank'}],
        'execution_views': [{**view, 'runtime_view_use': 'pointer_target'} for view in views]}
    path = tmp_path / 'metadata.json'
    path.write_text(json.dumps(metadata))
    _, _, artifact = build_listing_artifact_profile_from_binary_source(source, metadata_path=path,
        project_root=PROJECT_ROOT)
    try:
        row = artifact.row_for_source_offset(section_index=0, offset=2)
        assert row is not None
        resolution = row['pointer_resolution']
        assert resolution['reason'] == reason
        assert resolution['encoded_value'] == value
        if expected:
            assert expected in row['text']
            assert resolution['target_offset'] == 12
        else:
            assert resolution['outcome'] == 'unresolved'
        text, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = assemble_platform_source_text_with_c_backend('amiga-raw', text, project_root=PROJECT_ROOT)
        assert rebuilt == original
        _assert_vasm_bytes(tmp_path, text, original)
    finally:
        artifact.close()


def test_catalog_mal_projection_and_whole_candidate_native_preflight(tmp_path):
    import json

    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        RawAddressModel,
        RawBinarySource,
    )
    from amiga_reversing.disasm.c_backend import validate_policy_storage_with_c_backend
    from amiga_reversing.disasm.effective_metadata import (
        effective_metadata_text,
        effective_target_metadata,
    )
    from amiga_reversing.disasm.manual_action_catalog import (
        target_catalog_manual_payload,
    )
    from amiga_reversing.disasm.manual_actions import build_target_identity
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT
    from amiga_reversing.disasm.target_metadata import (
        TargetMetadata,
        write_target_metadata,
    )

    binary = tmp_path / 'input.bin'
    binary.write_bytes(bytes.fromhex('6004000080044e75'))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    (tmp_path / 'source_binary.json').write_text(json.dumps({'kind': 'raw_binary', 'path': str(binary),
        'address_model': 'local_offset', 'load_address': 0, 'entrypoint': 0, 'code_start_offset': 0}))
    factory = [target_catalog_manual_payload('target.custom_struct.add', {'name': 'Frame', 'size': 4,
        'fields': [{'name': 'mask', 'type': 'long', 'offset': 0, 'size': 4,
            'value_kind': 'target_pointer', 'pointer_address_domain': 'runtime_only',
            'pointer_symbol_group': 'masks'}]}),
        target_catalog_manual_payload('target.equate.add', {'name': 'mask_bank', 'value': 0x8000,
            'address_domain': 'runtime', 'group': 'masks', 'extent_bytes': 16})]
    actions = factory + [
        ('create_manual_data_block_layout', {'data_block_layout': {'layout_id': 'frame', 'hunk': 0,
            'source_start': 2, 'source_end': 6, 'name': 'frame', 'default_unit': 'byte'}}),
        ('set_manual_data_block_element', {'data_block_element': {'data_block_element_id': 'frame:0',
            'layout_id': 'frame', 'offset': 0, 'width': 4, 'kind': 'struct',
            'type_binding': {'type_binding_id': 'binding', 'layout_id': 'frame', 'element_offset': 0,
                'element_width': 4, 'binding_kind': 'custom_struct', 'bound_type_id': 'Frame',
                'owner_action_id': 'a4'}}})]
    records = [{'record': 'manual_action_log_header', 'version': 1, 'target_identity': build_target_identity(source)}]
    records += [{'record': 'manual_action', 'action_id': f'a{i}', 'sequence': i,
        'created_at': '2026-10-13T00:00:00+00:00', 'kind': kind, **payload}
        for i, (kind, payload) in enumerate(actions, 1)]
    (tmp_path / 'manual_actions.jsonl').write_text(''.join(json.dumps(record) + '\n' for record in records))
    canonical = effective_target_metadata(tmp_path)
    field = next(entity for entity in canonical.seeded_entities if entity.field_name == 'mask')
    assert field.pointer_address_domain == 'runtime_only'
    assert field.pointer_symbol_group == 'masks'
    bank = next(equate for equate in canonical.target_equates if equate.name == 'mask_bank')
    assert (bank.address_domain, bank.group, bank.extent_bytes) == ('runtime', 'masks', 16)
    validate_policy_storage_with_c_backend(source, metadata_text=effective_metadata_text(tmp_path),
        project_root=PROJECT_ROOT)


def test_runtime_namespace_rejects_competing_expression_without_changing_legacy():
    from amiga_reversing.disasm.manual_action_catalog import (
        target_catalog_manual_payload,
    )

    params = {'name': 'buffer', 'value': 0x8000, 'group': 'masks', 'address_domain': 'runtime',
              'extent_bytes': 16, 'value_expression': 'other_buffer+$4'}
    with pytest.raises(ValueError, match='cannot declare value_expression'):
        target_catalog_manual_payload('target.equate.add', params)
    with pytest.raises(ValueError, match='cannot declare value_expression'):
        TargetEquateMetadata.from_dict({**params, 'seed_origin': 'manual_analysis',
            'review_status': 'seeded', 'citation': 'fixture'})
    _, payload = target_catalog_manual_payload('target.equate.add',
        {'name': 'legacy_alias', 'value': 0x8000, 'value_expression': 'other_buffer+$4'})
    assert payload['target_equate']['value_expression'] == 'other_buffer+$4'


def test_native_runtime_namespace_rejects_competing_expression(tmp_path):
    import json

    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        RawAddressModel,
        RawBinarySource,
    )
    from amiga_reversing.disasm.c_backend import validate_policy_storage_with_c_backend
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT

    binary = tmp_path / 'input.bin'
    binary.write_bytes(bytes.fromhex('4e75'))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    metadata = {'target_equates': [{'name': 'mask_bank', 'value': 0x8000, 'group': 'masks',
        'address_domain': 'runtime', 'extent_bytes': 16, 'value_expression': 'other_buffer+$4'}]}
    with pytest.raises(RuntimeError, match='failed parsing target metadata target equate'):
        validate_policy_storage_with_c_backend(source, metadata_text=json.dumps(metadata),
            project_root=PROJECT_ROOT)
