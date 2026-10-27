"""Common custom prefixes survive joins without keeping subtype-only fields."""
from itertools import permutations
import pytest
from tests.test_app_cursor_propagation import cursor_artifact


def metadata(left='Parent', right='Child'):
    records = [
        dict(name='Parent', size=16, fields=[dict(name='value', type='LONG', offset=12, size=4)]),
        dict(name='Child', size=20, base_struct='Parent', base_offset=16,
             fields=[dict(name='child_only', type='WORD', offset=16, size=2)]),
        dict(name='Sibling', size=24, base_struct='Parent', base_offset=16,
             fields=[dict(name='sibling_only', type='WORD', offset=20, size=2)]),
        dict(name='Grandchild', size=24, base_struct='Child', base_offset=20,
             fields=[dict(name='extra', type='WORD', offset=22, size=2)]),
        dict(name='Other', size=16, fields=[dict(name='value', type='LONG', offset=12, size=4)])]
    # Register seeds are explicit input contracts. A storage declaration alone
    # is not evidence that an arbitrary load contains a valid typed pointer.
    return dict(custom_structs=records, entry_register_seeds=[
        dict(hunk=0, entry_offset=0, register='A1', kind='struct_ptr', struct_name=left,
             note='Fixture original left input contract'),
        dict(hunk=0, entry_offset=0, register='A2', kind='struct_ptr', struct_name=right,
             note='Fixture original right input contract')])


@pytest.mark.parametrize('left,right,common', [
    ('Parent', 'Child', 'Parent'), ('Child', 'Parent', 'Parent'),
    ('Child', 'Sibling', 'Parent'), ('Sibling', 'Child', 'Parent'),
    ('Child', 'Grandchild', 'Child'), ('Grandchild', 'Parent', 'Parent')])
def test_join_keeps_only_a_real_declared_common_prefix(tmp_path, left, right, common):
    artifact, _ = cursor_artifact(tmp_path, '''tst.w d7
 beq.w right
 movea.l a1,a0
 bra.w joined
right:
 movea.l a2,a0
joined:
 move.l 12(a0),d0
 move.w 16(a0),d1''', regions=False, metadata_extra=metadata(left, right))
    try:
        analysis = artifact.analysis_payload()[0]
        assert not analysis['incomplete_analysis']
        rows = analysis['sections'][0]['recovered_platform_typed_accesses']
        assert any(r['field_expr'] == 'Parent_value' and r['root_struct_name'] == common for r in rows)
        assert any(r['field_expr'] == 'Child_child_only' for r in rows) == (common == 'Child')
    finally:
        artifact.close()


@pytest.mark.parametrize('transport', ['stack', 'call'])
def test_saved_packets_and_callee_inputs_use_the_same_prefix_join(tmp_path, transport):
    if transport == 'stack':
        body = '''tst.w d7
 beq.w right
 movea.l a1,a0
 move.l a0,-(a7)
 bra.w joined
right:
 movea.l a2,a0
 move.l a0,-(a7)
joined:
 movea.l (a7)+,a1
 move.l 12(a1),d0'''
    else:
        body = '''movea.l a1,a0
 bsr.w shared
 movea.l a2,a0
 bsr.w shared
 rts
shared:
 move.l 12(a0),d0
 rts'''
    artifact, _ = cursor_artifact(tmp_path, body, regions=False, metadata_extra=metadata())
    try:
        rows = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert any(r['field_expr'] == 'Parent_value' and r['root_struct_name'] == 'Parent' for r in rows)
    finally:
        artifact.close()


@pytest.mark.parametrize('types', list(permutations(['Parent', 'Child', 'Sibling'])))
def test_three_predecessor_order_does_not_change_the_common_prefix(tmp_path, types):
    extra = metadata(types[0], types[1])
    extra['entry_register_seeds'].append(dict(hunk=0, entry_offset=0,
        register='A3', kind='struct_ptr', struct_name=types[2], note='Fixture third input contract'))
    artifact, _ = cursor_artifact(tmp_path, '''tst.w d7
 beq.w first
 tst.w d6
 beq.w second
 movea.l a3,a0
 bra.w joined
first:
 movea.l a1,a0
 bra.w joined
second:
 movea.l a2,a0
joined:
 move.l 12(a0),d0''', regions=False, metadata_extra=extra)
    try:
        analysis = artifact.analysis_payload()[0]
        assert not analysis['incomplete_analysis']
        rows = analysis['sections'][0]['recovered_platform_typed_accesses']
        assert any(r['field_expr'] == 'Parent_value' and r['root_struct_name'] == 'Parent' for r in rows)
    finally:
        artifact.close()


@pytest.mark.parametrize('case', ['same_cursor', 'different_cursor', 'unknown', 'partial_write', 'unrelated'])
def test_ancestry_never_erases_pointer_position_or_unknown_input(tmp_path, case):
    left_adjust = right_adjust = ''
    right_load = 'movea.l a2,a0'
    extra = metadata(right='Other' if case == 'unrelated' else 'Child')
    displacement = 12
    if case in ('same_cursor', 'different_cursor'):
        right_adjust = 'addq.l #4,a0'
        if case == 'same_cursor':
            left_adjust = right_adjust
            displacement = 8
    if case == 'unknown':
        right_load = 'movea.l d6,a0'
    if case == 'partial_write':
        right_adjust = 'movea.w d6,a0'
    artifact, _ = cursor_artifact(tmp_path, f'''tst.w d7
 beq.w right
 movea.l a1,a0
 {left_adjust}
 bra.w joined
right:
 {right_load}
 {right_adjust}
joined:
 move.l {displacement}(a0),d0''', regions=False, metadata_extra=extra)
    try:
        rows = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert any(r['field_expr'] == 'Parent_value' for r in rows) == (case == 'same_cursor')
    finally:
        artifact.close()
