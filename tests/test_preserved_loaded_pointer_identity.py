"""Explicit identity results distinguish saved register values from mutable storage."""
import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


@pytest.mark.parametrize('identity', [False, True])
@pytest.mark.parametrize('tuple_location', [0, 2, 4])
def test_saved_loaded_pointer_requires_explicit_identity_result(tmp_path, identity, tuple_location):
    binary = tmp_path / 'source.bin'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        ' SECTION code,code\n ORG 0\n move.l a5,$70000.l\n movea.l $70000.l,a5\n'
        ' bsr.w helper\n clr.w 16(a5)\n rts\nhelper:\n rts\n', output_path=binary)
    assert len(original) == 24
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    summary = {'hunk': 0, 'callable_kind': 'direct', 'entry_offset': 22,
        'inputs': [{'location': {'kind': 'register', 'register': 'A5', 'width': 4}, 'value_kind': 'abi_pointer'}],
        'results': [{'kind': 'identity_input', 'location': {'kind': 'register', 'register': 'A5', 'width': 4}, 'input_index': 0}] if identity else [],
        'effects': {'schema_version': 1, 'registers': {'state': 'explicit', 'locations': [
            {'location': {'kind': 'register', 'register': f'{kind}{i}', 'width': 4},
             'effect': 'preserved' if kind == 'A' and i in (5, 7) else 'clobbered'}
            for kind in ('D', 'A') for i in range(8)]},
            'memory': {'state': 'unknown'}, 'escapes': {'state': 'unknown'}}}
    if tuple_location:
        location = {'kind': 'register_tuple', 'registers': [f'A{i}' for i in range(6 - tuple_location, 6)], 'width': 4 * tuple_location}
        summary['inputs'][0]['location'] = location
        if identity:
            summary['results'][0]['location'] = location
    actions = [target_catalog_manual_payload(command, parameters) for command, parameters in [
        ('target.custom_struct.add', {'name': 'Node', 'size': 18, 'fields': [{'name': 'clock', 'type': 'WORD', 'offset': 16, 'size': 2}]}),
        ('target.code.register_seed.add', {'hunk': 0, 'addr': 0, 'register': 'A5', 'struct_name': 'Node'}),
        ('target.function_summary.add', summary)]]
    append_manual_actions(tmp_path, binary_source=source, actions=[(Kind(kind), payload) for kind, payload in actions])
    with effective_metadata_file(tmp_path) as metadata:
        rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
    assert ('clr.w Node_clock(a5)' in rendered) == identity
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered)
    assert rebuilt == original


@pytest.mark.parametrize('location,extra', [
    ({'kind': 'register', 'register': 'A5', 'width': 4}, {'struct_name': 'Node'}),
    ({'kind': 'register', 'register': 'A5', 'width': 8}, {}),
    ({'kind': 'register_tuple', 'registers': ['A5', 'A5'], 'width': 8}, {}),
    ({'kind': 'register_tuple', 'registers': ['A4', 'A5'], 'width': 4}, {}),
    ({'kind': 'memory', 'register': 'A5', 'width': 4}, {}),
])
def test_type_neutral_catalog_rejects_bad_locations_or_pointee_claims(location, extra):
    with pytest.raises(ValueError):
        target_catalog_manual_payload('target.function_summary.add', {
            'hunk': 0, 'callable_kind': 'direct', 'entry_offset': 0,
            'inputs': [{'location': location, 'value_kind': 'abi_pointer', **extra}]})


def test_native_tuple_reader_rejects_a_final_nonstring_member(tmp_path):
    import json
    binary = tmp_path / 'input.bin'
    binary.write_bytes(bytes.fromhex('4e754e75'))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    _, payload = target_catalog_manual_payload('target.function_summary.add', {
        'hunk': 0, 'callable_kind': 'direct', 'entry_offset': 2,
        'inputs': [{'location': {'kind': 'register_tuple', 'registers': ['A4', 'A5'], 'width': 8},
                    'value_kind': 'abi_pointer'}]})
    payload['function_summary']['inputs'][0]['location']['registers'].append(17)
    metadata = tmp_path / 'bad.json'
    metadata.write_text(json.dumps({'target_type': 'program', 'function_summaries': [payload['function_summary']]}, indent=2))
    with pytest.raises(RuntimeError, match='failed parsing target metadata function summary'):
        c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
