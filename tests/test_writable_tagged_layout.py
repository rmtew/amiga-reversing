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
                assert imported.get('tag_root_struct') == record.get('tag_root_struct')
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


@pytest.mark.parametrize('body', [
    'move.w #12,(a0)\n move.w 4(a0),d2',
    'move.w #12,(a0)\n move.w #99,2(a0)\n move.w 4(a0),d2',
    'movea.l a0,a2\n move.w #12,(a0)\n move.w 4(a2),d2',
    'moveq.l #12,d0\n move.w d0,(a0)\n move.w 4(a0),d2',
    'move.w #12,d0\n move.w d0,(a0)\n move.w 4(a0),d2',
])
def test_exact_tag_store_establishes_the_same_transient_field_view(tmp_path, body):
    section, source = check(tmp_path, body)
    assert len(extras(section)) == 1
    assert extras(section)[0]['type_provenance_kind'] == 'tagged_layout_contract'
    assert 'Child_extra' in source


@pytest.mark.parametrize('between', [
    'move.w #0,(a0)', 'move.b #12,1(a0)', 'clr.w (a1)',
    'jsr $2000.l', 'lea.l 16(a0),a0',
])
def test_tag_store_still_loses_the_view_on_mutation_alias_or_unknown_call(tmp_path, between):
    section, _ = check(tmp_path, 'move.w #12,(a0)\n'+between+'\n move.w 4(a0),d2')
    assert not extras(section)


@pytest.mark.parametrize('body', [
    'move.b #12,(a0)\n move.w 4(a0),d2',
    'move.l #$C0000,(a0)\n move.w 4(a0),d2',
    'move.b #12,d0\n move.w d0,(a0)\n move.w 4(a0),d2',
    'move.w d0,(a0)\n move.w 4(a0),d2',
    'move.w #12,(a0)\n move.w 4(a1),d2',
    'tst.w d7\n beq.w other\n move.w #12,(a0)\n bra.w joined\nother: move.w #13,(a0)\njoined: move.w 4(a0),d2',
    'tst.w d7\n beq.w other\n moveq.l #12,d0\n bra.w joined\nother: moveq.l #13,d0\njoined: move.w d0,(a0)\n move.w 4(a0),d2',
    'move.w #12,(a0)\nagain: move.w 4(a0),d2\n tst.w d7\n beq.w done\n move.w #0,(a0)\n bra.w again\ndone:',
])
def test_partial_unknown_other_root_and_conflicting_store_paths_refuse(tmp_path, body):
    section, _ = check(tmp_path, body, seeds=[seed(), seed('A1')])
    assert not extras(section)


def test_each_loop_iteration_must_reestablish_the_tag_after_mutation(tmp_path):
    section, _ = check(tmp_path, '''again: move.w #12,(a0)
 move.w 4(a0),d2
 tst.w d7
 beq.w done
 move.w #0,(a0)
 bra.w again
done:''')
    assert len(extras(section))==1


@pytest.mark.parametrize('between,expected',[
    ('',1),('move.w #3,2(a0)',1),('move.w #0,(a0)',0),
    ('clr.b (a0)',0),('clr.w (a1)',0),('jsr $2000.l',0),
])
def test_empty_tagged_leaf_uses_inherited_field_without_weakening_invalidations(tmp_path,between,expected):
    records=[
        dict(name='Base',size=8,fields=[dict(name='tag',type='WORD',offset=0,size=2)]),
        dict(name='Mid',size=8,base_struct='Base',fields=[dict(name='extra',type='WORD',offset=4,size=2)]),
        dict(name='Leaf',size=8,base_struct='Mid',tag_root_struct='Base',tag_offset=0,tag_value=12,fields=[]),
    ]
    section,source=check(tmp_path,f'cmpi.w #12,(a0)\n bne.w done\n {between}\n move.w 4(a0),d2\ndone:',records=records)
    found=extras(section);assert len(found)==expected
    if found:
        assert found[0]['root_struct_name']=='Leaf'
        assert found[0]['owner_struct_name']=='Mid'
        assert found[0]['type_provenance_kind']=='tagged_layout_contract'
        assert 'Mid_extra' in source


def inherited_tag_schemas():
    return [
        dict(name='Base',size=8,fields=[dict(name='tag',type='WORD',offset=0,size=2)]),
        dict(name='Mid',size=8,base_struct='Base',fields=[]),
        dict(name='Leaf',size=8,base_struct='Mid',tag_root_struct='Base',tag_offset=0,
             tag_value=12,fields=[dict(name='extra',type='WORD',offset=4,size=2)]),
    ]


@pytest.mark.parametrize('input_type,expected',[('Base',1),('Mid',1),('Sibling',0)])
def test_explicit_tag_root_accepts_only_compatible_prefix_inputs(tmp_path,input_type,expected):
    records=inherited_tag_schemas()
    records.append(dict(name='Sibling',size=8,base_struct='Base',fields=[]))
    entry=seed();entry['struct_name']=input_type
    s,_=check(tmp_path,'cmpi.w #12,(a0)\n bne.w done\n move.w 4(a0),d2\ndone:',
              records=records,seeds=[entry])
    assert len(extras(s))==expected


def test_omitted_root_preserves_legacy_immediate_parent_namespace(tmp_path):
    records=inherited_tag_schemas();records[-1].pop('tag_root_struct')
    s,_=check(tmp_path,'cmpi.w #12,(a0)\n bne.w done\n move.w 4(a0),d2\ndone:',records=records)
    assert not extras(s)


def test_overlapping_explicit_and_legacy_tag_namespaces_refuse(tmp_path):
    records=inherited_tag_schemas()
    records.append(dict(name='Other',size=8,base_struct='Mid',tag_offset=0,tag_value=12,
                        fields=[dict(name='other',type='WORD',offset=4,size=2)]))
    entry=seed();entry['struct_name']='Mid'
    s,_=check(tmp_path,'cmpi.w #12,(a0)\n bne.w done\n move.w 4(a0),d2\ndone:',
              records=records,seeds=[entry])
    assert not extras(s)
    assert not [r for r in s['recovered_platform_typed_accesses'] if r['field_name']=='other']


@pytest.mark.parametrize('kind',['missing','unrelated','self','different_size','not_word',
                                 'without_guard','empty','too_long','duplicate','different_selector'])
def test_invalid_explicit_tag_root_refuses_at_native_admission(tmp_path,kind):
    records=inherited_tag_schemas();base,mid,leaf=records
    if kind=='missing':leaf['tag_root_struct']='Missing'
    elif kind=='unrelated':
        records.append(dict(name='Other',size=8,fields=[]));leaf['tag_root_struct']='Other'
    elif kind=='self':leaf['tag_root_struct']='Leaf'
    elif kind=='different_size':base['size']=6
    elif kind=='not_word':base['fields'][0].update(type='LONG',size=4)
    elif kind=='without_guard':leaf.pop('tag_value');leaf.pop('tag_offset')
    elif kind=='empty':leaf['tag_root_struct']=''
    elif kind=='too_long':leaf['tag_root_struct']='X'*64
    else:
        sibling=deepcopy(leaf);sibling['name']='Other'
        if kind=='different_selector':
            base['fields'].append(dict(name='other_tag',type='WORD',offset=2,size=2))
            sibling.update(tag_offset=2,tag_value=13)
        records.append(sibling)
    with pytest.raises(RuntimeError,match='metadata|custom'):
        check(tmp_path,'nop',records=records)


def test_explicit_tag_root_survives_canonical_action_projection():
    from dataclasses import asdict
    from amiga_reversing.disasm.manual_action_catalog import _custom_struct_payload
    from amiga_reversing.disasm.effective_metadata import _manual_custom_struct_to_metadata
    from amiga_reversing.disasm.target_metadata import CustomStructMetadata
    action=_custom_struct_payload(inherited_tag_schemas()[-1])
    metadata=_manual_custom_struct_to_metadata(action)
    assert metadata is not None
    import json
    restored=CustomStructMetadata.from_dict(json.loads(json.dumps(asdict(metadata))))
    assert restored.tag_root_struct=='Base'


def test_explicit_tag_root_native_policy_name_capacity_is_exact(tmp_path):
    # Policy name capacity is independent of longer generated field symbols.
    import json
    records=inherited_tag_schemas();name='R'*63
    records[0]['name']=records[1]['base_struct']=records[2]['tag_root_struct']=name
    binary=tmp_path/'input.bin';binary.write_bytes(bytes.fromhex('4e75'))
    metadata=tmp_path/'metadata.json';metadata.write_text(json.dumps(dict(custom_structs=records)))
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=4096,entrypoint=4096,
        code_start_offset=0,display_path='fixture',analysis_cache_path=tmp_path/'policy.analysis')
    policy=cb.effective_policy_project_source_with_c_backend(source,metadata_path=metadata)['analysis_policy']
    assert next(r for r in policy['custom_structs'] if r['name']=='Leaf')['tag_root_struct']==name
