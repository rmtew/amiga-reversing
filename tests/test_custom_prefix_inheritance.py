"""Canonical custom prefixes survive native import, field resolution and transport."""
from copy import deepcopy
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from amiga_reversing.disasm import c_backend


def schemas():
    # Forward references are intentional: import order is not ownership.
    return [dict(name='Child', size=20, base_struct='Parent', base_offset=16,
                 fields=[dict(name='own', type='WORD', offset=16, size=2)]),
            dict(name='Leaf', size=2, fields=[dict(name='value', type='WORD', offset=0, size=2)]),
            dict(name='Parent', size=16, fields=[
                dict(name='target', type='APTR', offset=4, size=4,
                     value_kind='struct_pointer', pointer_struct='Leaf', pointer_address_domain='mapped_source'),
                dict(name='world_z', type='LONG', offset=12, size=4)])]


def seed(root):
    return dict(hunk=0, entry_offset=0, register='A0', kind='struct_ptr', struct_name=root, note='Fixture original input contract')


@pytest.mark.parametrize('grandchild', [False, True])
def test_parent_owner_partial_access_pointer_load_store_and_holes(tmp_path, grandchild):
    records = schemas()
    root = 'Child'
    if grandchild:
        root = 'Grandchild'
        records.insert(0, dict(name=root, size=24, base_struct='Child', base_offset=20,
                               fields=[dict(name='extra', type='WORD', offset=22, size=2)]))
    artifact, original = cursor_artifact(tmp_path, '''move.l 12(a0),d0
 movea.l 4(a0),a1
 move.w (a1),d1
 move.w 14(a0),d2
 move.w 16(a0),d3
 move.l 14(a0),d4
 move.w 18(a0),d5
 move.l a1,4(a0)''', regions=False,
        metadata_extra=dict(custom_structs=records, entry_register_seeds=[seed(root)]))
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        typed = section['recovered_platform_typed_accesses']
        z = next(r for r in typed if r['offset'] == 0)
        assert (z['root_struct_name'], z['owner_struct_name'], z['inherited'], z['field_expr']) == (
            root, 'Parent', 1, 'Parent_world_z')
        assert any(r['offset'] == 8 and r['root_struct_name'] == 'Leaf' and r['field_name'] == 'value' for r in typed)
        assert any(r['offset'] == 10 and r['field_expr'] == 'Parent_world_z' for r in typed)
        assert any(r['offset'] == 14 and r['owner_struct_name'] == 'Child' and r['field_name'] == 'own' for r in typed)
        assert not any(r['offset'] in (18, 22) for r in typed)  # Crossing field and real gap.
        assert any(r['destination_struct_name'] == 'Parent' and r['destination_field_name'] == 'target'
                   for r in section['pointer_stores'])
        source = artifact.inline_source_text_with_profile()[0]
        assert 'Parent_world_z+2(a0)' in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source,
            include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')[0] == original
    finally:
        artifact.close()


@pytest.mark.parametrize('kind', [
    'unknown', 'self_cycle', 'long_cycle', 'short_child', 'overlap',
    'fractional_offset', 'negative_offset', 'offset_after_field', 'platform_parent',
    'scalar_schema', 'scalar_field', 'duplicate_name',
])
def test_invalid_prefix_admission_refuses_instead_of_dropping_parent(tmp_path, kind):
    records = deepcopy(schemas())
    child, _, parent = records
    if kind == 'unknown': child['base_struct'] = 'Missing'
    elif kind == 'self_cycle': child['base_struct'] = 'Child'
    elif kind == 'long_cycle': parent['base_struct'] = 'Child'; parent['size'] = 20
    elif kind == 'short_child': child['size'] = 8; child['fields'] = []; child['base_offset'] = 0
    elif kind == 'overlap': child['fields'][0]['offset'] = 12; child['base_offset'] = 0
    elif kind == 'fractional_offset': child['base_offset'] = 16.5
    elif kind == 'negative_offset': child['base_offset'] = -1
    elif kind == 'offset_after_field': child['base_offset'] = 18
    elif kind == 'platform_parent': child['base_struct'] = 'ExecBase'
    elif kind == 'scalar_schema': records.insert(0, 1)
    elif kind == 'scalar_field': child['fields'] = [1]
    elif kind == 'duplicate_name': records.append(deepcopy(child))
    with pytest.raises(RuntimeError, match='metadata|custom'):
        cursor_artifact(tmp_path, 'move.l 12(a0),d0', regions=False,
            metadata_extra=dict(custom_structs=records, entry_register_seeds=[seed('Child')]))
