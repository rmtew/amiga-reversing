"""Actual compare edges bound WORD indexes without asserted input ranges."""
import pytest
from amiga_reversing.disasm import c_backend
from tests.test_base_candidates import candidate_artifact


@pytest.mark.parametrize('before,compare,between,branch,after,width,count,expected', [
    ('', 'cmp.w #5,d0', '', 'bls', '', 'w', 6, True),
    ('', 'cmpi.w #5,d0', '', 'bls', '', 'w', 6, True),
    ('', 'cmp.w #6,d0', '', 'bcs', '', 'w', 6, True),
    ('', 'cmp.w #2,d0', '', 'beq', '', 'w', 6, True),
    ('', 'cmp.w #5,d0', '', 'bls', '', 'w', 5, False),
    ('', 'cmp.w #5,d0', '', 'bls', '', 'l', 6, False),
    ('', 'cmp.b #5,d0', '', 'bls', '', 'w', 6, False),
    ('', 'cmp.l #5,d0', '', 'bls', '', 'w', 6, False),
    ('', 'cmp.w #5,d0', '', 'ble', '', 'w', 6, False),
    ('', 'cmp.w #5,d0', 'tst.w d1', 'bls', '', 'w', 6, False),
    ('', 'cmp.w #5,d0', '', 'bls', 'move.b d1,d0', 'w', 6, False),
    ('', 'cmp.w #5,d0', '', 'bls', 'muls.w d1,d0', 'w', 6, False),
    ('', 'cmp.w #5,d0', '', 'bls', 'divu.w #2,d0', 'w', 6, False),
    ('', 'cmp.w #5,d0', '', 'bls', 'swap.w d0', 'w', 6, False),
    ('tst.w d1\n beq.s within', 'cmp.w #5,d0', '', 'bls', '', 'w', 6, False),
    ('lea.l condition(pc),a2', 'cmp.w #5,d0', '', 'bls', '', 'w', 6, False),
])
def test_compare_guarded_array(tmp_path,before,compare,between,branch,after,width,count,expected):
    extra=dict(custom_structs=[dict(name='Slot',size=4,fields=[
        dict(name='value',type='LONG',offset=0,size=4)])],entry_register_seeds=[
        dict(hunk=0,entry_offset=0,register='A0',kind='struct_ptr',struct_name='Slot',
             array_length=count,note='Input array, index initially unknown')])
    code=f'{before}\n {compare}\n {between}\ncondition:\n {branch}.s within\n rts\nwithin:\n {after}\n add.w d0,d0\n add.w d0,d0\n move.l 0(a0,d0.{width}),d2\n rts\n'
    with candidate_artifact(tmp_path,code,[],extra)as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[x for x in p['sections'][0]['recovered_platform_typed_accesses']if x['field_name']=='value']
        assert bool(refs)==expected
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


def test_decrement_condition_branch_is_not_a_compare_only_predicate(tmp_path):
    extra=dict(custom_structs=[dict(name='Slot',size=4,fields=[
        dict(name='value',type='LONG',offset=0,size=4)])],entry_register_seeds=[
        dict(hunk=0,entry_offset=0,register='A0',kind='struct_ptr',struct_name='Slot',
             array_length=6,note='Array input')])
    code='cmp.w #5,d0\n dbeq.w d1,within\n rts\nwithin:\n add.w d0,d0\n add.w d0,d0\n move.l 0(a0,d0.w),d2\n rts\n'
    with candidate_artifact(tmp_path,code,[],extra)as(a,original):
        assert not a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


@pytest.mark.parametrize('compare,exit_branch', [('cmp.w #5,d0','bhi'),('cmp.w #0,d0','bne')])
def test_guard_on_fallthrough_edge(tmp_path,compare,exit_branch):
    extra=dict(custom_structs=[dict(name='Slot',size=4,fields=[
        dict(name='value',type='LONG',offset=0,size=4)])],entry_register_seeds=[
        dict(hunk=0,entry_offset=0,register='A0',kind='struct_ptr',struct_name='Slot',
             array_length=6,note='Array input')])
    code=f'{compare}\n {exit_branch}.s outside\n add.w d0,d0\n add.w d0,d0\n move.l 0(a0,d0.w),d2\n rts\noutside:\n rts\n'
    with candidate_artifact(tmp_path,code,[],extra)as(a,original):
        assert len(a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses'])==1
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
