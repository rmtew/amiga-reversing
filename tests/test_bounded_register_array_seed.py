"""A bounded record prefix is carried through the normal catalog to native typing."""

import json
from dataclasses import replace

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_target_metadata,
)
from amiga_reversing.disasm.manual_action_catalog import (
    listing_catalog_manual_payload,
    target_catalog_manual_payload,
)
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind
from amiga_reversing.disasm.manual_actions import append_manual_actions
from amiga_reversing.disasm.target_metadata import (
    EntryRegisterSeedKind,
    EntryRegisterSeedMetadata,
    TargetMetadata,
    target_metadata_json_payload,
    write_target_metadata,
)


def seed(length=None, **changes):
    p = {'hunk': 0, 'addr': 0, 'register': 'A0', 'struct_name': 'Slot'} | changes
    if length is not None:
        p['array_length'] = length
    return target_catalog_manual_payload('target.code.register_seed.add', p)


@pytest.mark.parametrize('value', [0, -1, 65536, True, False, 4.0, '4', None])
def test_catalog_rejects_invalid_array_contract(value):
    with pytest.raises(ValueError, match='array_length'):
        target_catalog_manual_payload('target.code.register_seed.add', {
            'hunk': 0, 'addr': 0, 'register': 'A0', 'struct_name': 'Slot', 'array_length': value})


def test_optional_length_keeps_legacy_wire_shape_and_validates_metadata():
    s = EntryRegisterSeedMetadata(entry_offset=0, register='A0', kind=EntryRegisterSeedKind.STRUCT_PTR,
                                  note='base', struct_name='Slot')
    m = TargetMetadata(target_type='program', entry_register_seeds=(s,))
    assert 'array_length' not in target_metadata_json_payload(m)['entry_register_seeds'][0]
    for length in [1, 4, 65535]:
        with_array = replace(m, entry_register_seeds=(replace(s, array_length=length),))
        assert target_metadata_json_payload(with_array)['entry_register_seeds'][0]['array_length'] == length
    with pytest.raises(ValueError, match='array_length'):
        replace(s, array_length=4, kind=EntryRegisterSeedKind.LIBRARY_BASE)


@pytest.mark.parametrize('length', [None, 4, 65535])
def test_catalog_replay_native_prefix_fields_and_conservative_edges(tmp_path, length):
    text = (' SECTION code,code\n ORG 0\n move.b (a0),d0\n move.b 2(a0),d1\n'
            ' move.b 4(a0),d2\n move.b 6(a0),d3\n move.b 8(a0),d4\n'
            ' move.b 0(a0,d6.w),d5\n move.b 2(a1),d0\n rts\n')
    binary = tmp_path / 'source.bin'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text, output_path=binary)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    actions = [target_catalog_manual_payload('target.custom_struct.add', {
        'name': 'Slot', 'size': 2, 'fields': [
            {'name': 'id', 'type': 'UBYTE', 'offset': 0, 'size': 1},
            {'name': 'value', 'type': 'UBYTE', 'offset': 1, 'size': 1}]}),
        seed(length), seed(register='A1')]
    if length == 4:
        actions += [target_catalog_manual_payload('target.equate.add', {
            'name': 'SECOND_SLOT_ID', 'value': 2, 'value_expression': 'Slot_SIZEOF+Slot_id'}),
            listing_catalog_manual_payload({'kind': 'instruction', 'section_index': 0,
                'start_offset': 2, 'end_offset': 6, 'operand_parts': [
                    {'kind': 'displacement', 'operand_index': 0, 'value': 2, 'width_bytes': 2}]},
                'representation.symbol', element_context={'element_kind': 'displacement', 'operand_index': 0},
                parameters={'symbol': 'SECOND_SLOT_ID'})]
    records = append_manual_actions(tmp_path, binary_source=source,
        actions=[(Kind(k), p) for k, p in actions])
    m = effective_target_metadata(tmp_path)
    assert [(s.register, s.array_length) for s in m.entry_register_seeds] == [('A0', length), ('A1', None)]
    if length is not None:
        assert m.entry_register_seeds[0].hunk == 0
        append_manual_actions(tmp_path, binary_source=source,
            actions=[(Kind.UNDO_ACTION, {'undoes_action_id': records[1]['action_id']})])
        assert [s.register for s in effective_target_metadata(tmp_path).entry_register_seeds] == ['A1']
        append_manual_actions(tmp_path, binary_source=source,
            actions=[(Kind.REDO_ACTION, {'redoes_action_id': records[1]['action_id']})])
    with effective_metadata_file(tmp_path) as metadata:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)[2]
    try:
        a = artifact.analysis_payload()[0]['sections'][0]
        unresolved = a['recovered_platform_unresolved_typed_accesses']
        assert len(unresolved) == {None: 6, 4: 3, 65535: 2}[length]
        assert [u['classification'] for u in unresolved].count('indexed_dynamic') == 1
        assert any(u['base_register'] == 'A1' and u['displacement'] == 2 for u in unresolved)
        assert any(u['base_register'] == 'A0' and u['displacement'] == 8 for u in unresolved) == (length != 65535)
        typed = a['recovered_platform_typed_accesses']
        assert len([r for r in typed if r['base_register'] == 'A0']) == {None: 1, 4: 4, 65535: 5}[length]
        rendered = artifact.source_text_with_profile()[0]
        if length == 4:
            assert 'move.b SECOND_SLOT_ID(a0),d1' in rendered
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered)
        assert rebuilt == original
    finally:
        artifact.close()


@pytest.mark.parametrize('value', [0, -1, 65536, True, 4.5, '4'])
def test_native_import_refuses_invalid_length_instead_of_truncating(tmp_path, value):
    binary = tmp_path / 'source.bin'
    binary.write_bytes(bytes.fromhex('4e75'))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    metadata = tmp_path / 'bad.json'
    metadata.write_text(json.dumps({'target_type': 'program', 'entry_register_seeds': [{
        'entry_offset': 0, 'register': 'A0', 'kind': 'struct_ptr', 'note': 'base',
        'struct_name': 'Slot', 'array_length': value}]}))
    with pytest.raises(RuntimeError, match='register seed'):
        c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)


def test_row_and_target_array_contracts_preserve_section_identity():
    from amiga_reversing.disasm.manual_action_catalog import _register_seed_payload

    row_seed = _register_seed_payload({'section_index': 3, 'start_offset': 16}, {
        'kind': 'struct_ptr', 'register': 'A0', 'struct_name': 'Slot', 'array_length': 4})
    assert row_seed['hunk'] == 3 and row_seed['array_length'] == 4
    _, target_seed = seed(4, hunk=3)
    assert target_seed['register_seed']['hunk'] == 3
    with pytest.raises(ValueError, match='struct pointer'):
        _register_seed_payload({'section_index': 3, 'start_offset': 16}, {
            'kind': 'library_base', 'register': 'A0', 'array_length': 4})
