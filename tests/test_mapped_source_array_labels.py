"""Mapped pointers reference emitted array symbols, never suppressed field labels."""
import json
import subprocess

import pytest

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    assemble_platform_source_text_with_c_backend,
    build_listing_artifact_profile_from_binary_source,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_text
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import (
    SeededEntityMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    write_target_metadata,
)


@pytest.mark.parametrize(("interior", "explicit", "span"),
                         [(0, False, "valid"), (2, False, "valid"), (0, True, "valid"), (2, True, "valid"),
                          (0, False, "missing"), (0, False, "out_of_bounds")])
def test_bound_array_pointer_uses_an_emitted_symbol_with_exact_bytes(tmp_path, interior, explicit, span):
    target = 24 + interior
    value = 0x1000 + target
    record = bytes.fromhex('0000111100002222') + bytes(10)
    assembly = ' SECTION section,code\n ORG $1000\n bra.b after\n dc.l ' + f'${value:X}\n'
    assembly += ' dc.b ' + ','.join(f'${b:02X}' for b in record * 2) + '\nafter:\n rts\n'
    binary = tmp_path / 'input.bin'
    original, _ = assemble_platform_source_text_with_c_backend('amiga-raw', assembly,
        output_path=binary, project_root=PROJECT_ROOT)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x1000, entrypoint=0x1000,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    pointer = SeededEntityMetadata(addr=2, end=6, hunk=0, unit='long', struct_name='Envelope',
        field_name='node', field_type='long', value_kind='target_pointer', pointer_address_domain='mapped_source',
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED, citation='fixture')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=(), seeded_entities=(pointer,)))
    actions = [(ManualActionKind.CREATE_MANUAL_CUSTOM_STRUCT, {'custom_struct': {'name': 'Node', 'size': 18,
        'fields': [{'name': 'position_descriptor_ptr', 'type': 'long', 'offset': 0, 'size': 4},
                   {'name': 'frame_sequence_ptr', 'type': 'long', 'offset': 4, 'size': 4},
                   {'name': 'state', 'type': 'byte', 'offset': 8, 'size': 10}]}}),
        (ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT, {'data_block_layout': {'layout_id': 'nodes',
            'hunk': 0, 'source_start': 6, 'source_end': 42, 'name': 'node_array', 'default_unit': 'byte'}}),
        (ManualActionKind.SET_MANUAL_DATA_BLOCK_ELEMENT, {'data_block_element': {'layout_id': 'nodes',
            'offset': 0, 'width': 36, 'kind': 'struct', 'array_count': 2, 'array_stride': 18,
            'type_binding': {'binding_kind': 'custom_struct', 'bound_type_id': 'Node',
                'layout_id': 'nodes', 'element_offset': 0, 'element_width': 36, 'type_binding_id': 'nodes-binding'}}})]
    if explicit:
        actions.append((ManualActionKind.CREATE_MANUAL_LABEL, {'label': {'label_id': 'anchor',
            'name': 'declared_node_anchor', 'scope': 'global', 'address_domain': 'source', 'hunk': 0, 'addr': target}}))
    append_manual_actions(tmp_path, binary_source=source, actions=actions)
    metadata_path = tmp_path / 'metadata.json'
    metadata = json.loads(effective_metadata_text(tmp_path, binary_source=source))
    first = next(e for e in metadata['seeded_entities'] if e['addr'] == 6)
    assert first['source_owner_start'] == 6 and first['source_owner_size'] == 36
    assert first['end'] == 10  # Owner proof does not change the physical leaf.
    assert sum('source_owner_start' in e for e in metadata['seeded_entities']) == 1
    if span == 'missing':
        first.pop('source_owner_start')
        first.pop('source_owner_size')
    elif span == 'out_of_bounds':
        first['source_owner_size'] = 0x100
    metadata_path.write_text(json.dumps(metadata))
    _, _, artifact = build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata_path,
        project_root=PROJECT_ROOT)
    try:
        row = artifact.row_for_source_offset(section_index=0, offset=2)
        expected = 'declared_node_anchor' if explicit and interior == 0 else 'node_array+$%X' % (target - 6)
        if span != 'valid':
            assert row['pointer_resolution']['outcome'] == 'unresolved'
            assert row['pointer_resolution']['reason'] == 'missing_source_owner'
            assert 'node_array' not in row['text']
            text, _ = artifact.inline_source_text_with_profile()
            rebuilt, _ = assemble_platform_source_text_with_c_backend('amiga-raw', text, project_root=PROJECT_ROOT)
            assert rebuilt == original
            return
        assert row['pointer_resolution']['outcome'] == 'symbolic'
        assert row['pointer_resolution']['target_offset'] == target
        assert f'dc.l {expected}' in row['text']
        text, _ = artifact.inline_source_text_with_profile()
        assert 'node_array:\n' in text
        assert 'node_array_position_descriptor_ptr_1' not in row['text']
        if explicit and interior == 0:
            assert 'declared_node_anchor:\n' in text
        else:
            assert 'declared_node_anchor:\n' not in text
            assert 'node_array_position_descriptor_ptr_1:\n' not in text
        rebuilt, _ = assemble_platform_source_text_with_c_backend('amiga-raw', text, project_root=PROJECT_ROOT)
        assert rebuilt == original
        path, output = tmp_path / 'rendered.s', tmp_path / 'oracle.bin'
        path.write_text(text)
        result = subprocess.run([str(PROJECT_ROOT / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin',
            '-o', str(output), str(path)], capture_output=True, text=True, timeout=10, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        assert output.read_bytes() == original
    finally:
        artifact.close()
