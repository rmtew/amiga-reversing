"""Explicit tagged layouts give transient fields, never permanent subtypes."""
from copy import deepcopy

import pytest

from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_typed_pointer_domains import _assert_vasm_bytes


def schemas():
    return [dict(name='Base', size=8, fields=[dict(name='tag', type='WORD', offset=0, size=2)]),
            dict(name='Child', size=8, base_struct='Base', tag_offset=0, tag_value=12,
                 fields=[dict(name='extra', type='WORD', offset=4, size=2)])]


def seed(register='A0'):
    return dict(hunk=0, entry_offset=0, register=register, kind='struct_ptr',
                struct_name='Base', note='Abstract writable record input')


def check(tmp_path, body, *, records=None, seeds=None, entries=None):
    metadata = dict(custom_structs=records or schemas(), entry_register_seeds=seeds or [seed()])
    if entries:
        metadata['seeded_code_entrypoints'] = entries
    a, original = cursor_artifact(tmp_path, body, regions=False, metadata_extra=metadata)
    try:
        payload = a.analysis_payload()[0]
        assert not payload['incomplete_analysis']
        source_input = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=tmp_path/'input.bin',
            address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=4096, entrypoint=4096,
            code_start_offset=0, display_path='fixture', analysis_cache_path=tmp_path/'policy.analysis')
        policy = cb.effective_policy_project_source_with_c_backend(source_input,
            metadata_path=tmp_path/'metadata.json')['analysis_policy']
        for record in metadata['custom_structs']:
            if 'tag_value' in record:
                imported = next(c for c in policy['custom_structs'] if c['name'] == record['name'])
                assert (imported['tag_offset'], imported['tag_value']) == (record['tag_offset'], record['tag_value'])
        source = a.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
        _assert_vasm_bytes(tmp_path, source, original)
        return payload['sections'][0], source
    finally:
        a.close()


def extras(section):
    return [r for r in section['recovered_platform_typed_accesses'] if r['field_name'] == 'extra']


@pytest.mark.parametrize(('prefix', 'test', 'between', 'read'), [
    ('', 'cmpi.w #12,(a0)', '', '4(a0)'),
    ('move.w (a0),d0', 'cmpi.w #12,d0', '', '4(a0)'),
    ('move.w (a0),d0\n move.l d0,d1\n moveq.l #0,d0', 'cmpi.w #12,d1', '', '4(a0)'),
    ('movea.l a0,a2', 'cmpi.w #12,(a0)', '', '4(a2)'),
    ('', 'cmpi.w #12,(a0)', 'movea.l a0,a2\n moveq.l #7,d1', '4(a2)'),
    ('', 'cmpi.w #12,(a0)', 'move.l a0,d3\n movea.l d3,a2', '4(a2)'),
    ('', 'cmpi.w #12,(a0)', 'move.w #99,2(a0)', '4(a0)'),
    ('movea.l a0,a2', 'cmpi.w #12,(a0)', 'move.w #99,2(a2)', '4(a0)'),
])
def test_equal_branch_recovers_guarded_field(tmp_path, prefix, test, between, read):
    s, source = check(tmp_path, f'{prefix}\n {test}\n bne.w done\n {between}\n move.w {read},d2\ndone:')
    assert len(extras(s)) == 1
    assert extras(s)[0]['type_provenance_kind'] == 'tagged_layout_contract'
    assert 'Child_extra' in source


@pytest.mark.parametrize('between', [
    'move.w #0,(a0)', 'move.b #12,1(a0)', 'clr.b (a0)',
    'movea.l a0,a2\n clr.w (a2)', 'clr.w (a1)', 'clr.w $2000.l',
    'jsr $2000.l', 'lea.l 16(a0),a0', 'movea.w a0,a0',
    'move.l a0,-(a7)\n movea.l (a7)+,a0', 'movem.l d0-d1,-(a7)',
])
def test_mutation_alias_unknown_call_and_other_element_refuse(tmp_path, between):
    s, _ = check(tmp_path, f'cmpi.w #12,(a0)\n bne.w done\n {between}\n move.w 4(a0),d2\ndone:')
    assert not extras(s)


@pytest.mark.parametrize('body', [
    'cmpi.w #12,(a0)\n beq.w done\n move.w 4(a0),d2\ndone:',
    'cmpi.w #11,(a0)\n bne.w done\n move.w 4(a0),d2\ndone:',
    'move.w (a0),d0\n move.b #12,d0\n cmpi.w #12,d0\n bne.w done\n move.w 4(a0),d2\ndone:',
    'cmpi.w #12,(a0)\n bne.w joined\n nop\njoined: move.w 4(a0),d2',
    'cmpi.w #12,(a0)\n bne.w done\n move.w 4(a1),d2\ndone:',
])
def test_missing_predicate_conflicting_join_partial_scalar_and_other_root_refuse(tmp_path, body):
    s, _ = check(tmp_path, body, seeds=[seed(), seed('A1')])
    assert not extras(s)


def test_join_does_not_keep_a_subtype_after_one_arm_mutates_tag(tmp_path):
    s, _ = check(tmp_path, '''cmpi.w #12,(a0)
 bne.w done
 tst.w d7
 beq.w joined
 move.w #0,(a0)
joined: move.w 4(a0),d2
done:''')
    assert not extras(s)


def test_guarded_view_does_not_escape_through_global_pointer_storage(tmp_path):
    s, _ = check(tmp_path, '''cmpi.w #12,(a0)
 bne.w done
 move.w 4(a0),d2
 move.l a0,holder.l
 movea.l holder.l,a1
 move.w 4(a1),d3
done: rts
holder: dc.l 0''')
    assert len(extras(s)) == 1


def test_even_a_known_preserving_call_does_not_export_the_view(tmp_path):
    s, _ = check(tmp_path, '''cmpi.w #12,(a0)
 bne.w done
 move.w 4(a0),d2
 bsr.w helper
 move.w 4(a0),d3
done: rts
helper: rts''')
    assert len(extras(s)) == 1


def test_fresh_read_after_mutation_can_reestablish_view(tmp_path):
    s, _ = check(tmp_path, '''move.w #12,(a0)
 cmpi.w #12,(a0)
 bne.w done
 move.w 4(a0),d2
done:''')
    assert len(extras(s)) == 1


def test_zero_tag_contract_and_direct_test(tmp_path):
    records = schemas()
    records[1]['tag_value'] = 0
    s, _ = check(tmp_path, 'tst.w (a0)\n bne.w done\n move.w 4(a0),d2\ndone:', records=records)
    assert len(extras(s)) == 1


def test_taken_equality_edge_and_word_sign_bits(tmp_path):
    records = schemas()
    records[1]['tag_value'] = 65535
    s, _ = check(tmp_path, 'cmpi.w #-1,(a0)\n beq.w equal\n rts\nequal: move.w 4(a0),d2', records=records)
    assert len(extras(s)) == 1


@pytest.mark.parametrize('tag_type', ['WORD', 'UWORD', 'word', 'uword'])
def test_scalar_word_schema_spelling_does_not_change_tag_bits(tmp_path, tag_type):
    records = schemas()
    records[0]['fields'][0]['type'] = tag_type
    s, _ = check(tmp_path, 'cmpi.w #12,(a0)\n bne.w done\n move.w 4(a0),d2\ndone:', records=records)
    assert len(extras(s)) == 1


def test_contract_survives_manual_action_and_metadata_projection():
    from dataclasses import asdict
    import json
    from amiga_reversing.disasm.manual_action_catalog import _custom_struct_payload
    from amiga_reversing.disasm.effective_metadata import _manual_custom_struct_to_metadata
    from amiga_reversing.disasm.target_metadata import CustomStructMetadata
    action = _custom_struct_payload(schemas()[1])
    projected = _manual_custom_struct_to_metadata(action)
    assert projected is not None
    restored = CustomStructMetadata.from_dict(json.loads(json.dumps(asdict(projected))))
    assert (restored.tag_offset, restored.tag_value, restored.base_struct) == (0, 12, 'Base')


@pytest.mark.parametrize('kind', ['no_parent', 'different_size', 'partial_tag', 'not_word',
                                  'missing_tag', 'bad_value', 'outside', 'duplicate', 'other_selector'])
def test_invalid_layout_contract_refuses(tmp_path, kind):
    records = deepcopy(schemas())
    parent, child = records
    if kind == 'no_parent': child.pop('base_struct')
    elif kind == 'different_size': child['size'] = 10
    elif kind == 'partial_tag': child['tag_offset'] = 1
    elif kind == 'not_word': parent['fields'][0].update(type='LONG', size=4)
    elif kind == 'missing_tag': child.pop('tag_value')
    elif kind == 'bad_value': child['tag_value'] = 65536
    elif kind == 'outside':
        parent['fields'][0]['offset'] = child['tag_offset'] = 8
    else:
        sibling = deepcopy(child)
        sibling['name'] = 'Sibling'
        if kind == 'other_selector':
            parent['fields'].append(dict(name='other', type='WORD', offset=2, size=2))
            sibling.update(tag_offset=2, tag_value=13)
        records.append(sibling)
    with pytest.raises(RuntimeError, match='metadata|custom'):
        check(tmp_path, 'nop', records=records)
