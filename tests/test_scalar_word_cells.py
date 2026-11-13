"""Local WORD cell definitions feed the existing finite register/index domain."""
import pytest
from tests.test_base_candidates import candidate_artifact
from amiga_reversing.disasm import c_backend


def scalar_fixture(tmp_path, before='andi.w #7,$100(a6)', middle='', load='move.w $100(a6),d0', count=32, seed_app=True,record=False):
    extra=dict(custom_structs=[dict(name='Slot',size=4,fields=[
        dict(name='value',type='LONG',offset=0,size=4)])],entry_register_seeds=[
        dict(hunk=0,entry_offset=0,register='A0',kind='struct_ptr',struct_name='Slot',array_length=count,note='Input reference array'),
        dict(hunk=0,entry_offset=0,register='A6',kind='library_base',library_name='__amiga_app_base__')])
    if not seed_app:extra['entry_register_seeds'].pop()
    if record:
        extra['custom_structs'].append(dict(name='Counter',size=48,fields=[
            dict(name='phase',type='WORD',offset=38,size=2)]))
        extra['entry_register_seeds'].append(dict(hunk=0,entry_offset=0,register='A2',
            kind='struct_ptr',struct_name='Counter',note='Counter record input'))
    return candidate_artifact(tmp_path,
        before+'\n'+middle+'\n'+load+'\n addi.w #21,d0\n lsl.w #2,d0\n move.l 0(a0,d0.w),d1\n rts\n',[],extra)


def test_masked_word_cell_supplies_a_bounded_index(tmp_path):
    with scalar_fixture(tmp_path) as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert len(refs)==1
        assert refs[0]['word_index']['byte_offsets']==list(range(84,113,4))
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


@pytest.mark.parametrize('middle,offsets',[
    ('move.w #3,$100(a6)',[96]),('clr.w $100(a6)',[84]),
    ('move.w #5,$104(a6)',list(range(84,113,4))),
    ('tst.w d7\n beq.s other\n andi.w #3,$100(a6)\n bra.s join\nother:\n andi.w #7,$100(a6)\njoin:',list(range(84,113,4))),
])
def test_scalar_cell_updates_and_must_joins(tmp_path,middle,offsets):
    with scalar_fixture(tmp_path,middle=middle)as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert len(refs)==1
        assert refs[0]['word_index']['byte_offsets']==offsets
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


@pytest.mark.parametrize('changes',[
    dict(middle='move.b d7,$100(a6)'),dict(middle='move.b d7,$101(a6)'),
    dict(middle='move.w d7,$100(a6)'),dict(middle='addq.w #1,$100(a6)'),
    dict(middle='move.w d7,(a2)'),dict(middle='move.w #3,$200.l'),
    dict(middle='jsr (a2)'),dict(middle='movea.l #0,a6'),
    dict(load='move.b $100(a6),d0'),dict(load='move.l $100(a6),d0'),
    dict(before='andi.w #15,$100(a6)'),dict(count=28),
    dict(before='tst.w d7\n beq.s no_definition\n andi.w #7,$100(a6)\nno_definition:'),
    dict(middle='tst.w d7\n beq.s no_overwrite\n move.w d7,$100(a6)\nno_overwrite:'),
])
def test_missing_partial_unknown_alias_and_extent_cases_refuse(tmp_path,changes):
    with scalar_fixture(tmp_path,**changes)as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        assert not[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


def test_scalar_word_register_copy_reuses_shared_transfer(tmp_path):
    with scalar_fixture(tmp_path,load='move.w $100(a6),d2\n move.w d2,d0')as(a,_):
        refs=a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert len([r for r in refs if r['field_name']=='value'])==1


@pytest.mark.parametrize('alias_write',[False,True])
def test_absolute_word_storage_uses_bus_alias_invalidation(tmp_path,alias_write):
    with scalar_fixture(tmp_path,before='andi.w #7,$200.l',load='move.w $200.l,d0',
            middle='move.b d7,$1000200.l' if alias_write else '')as(a,original):
        refs=a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert bool([r for r in refs if r['field_name']=='value'])== (not alias_write)
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


def test_fallback_app_view_cannot_supply_a_scalar_numeric_invariant(tmp_path):
    with scalar_fixture(tmp_path,seed_app=False)as(a,_):
        assert not[r for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
                   if r['field_name']=='value']


def test_closed_scalar_cell_loop_converges_without_restoring_original_bytes(tmp_path):
    before='andi.w #7,$100(a6)\n moveq.l #3,d3\nagain:\n andi.w #3,$100(a6)\n dbf.w d3,again'
    with scalar_fixture(tmp_path,before=before)as(a,_):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert len(refs)==1
        assert refs[0]['word_index']['byte_offsets']==[84,88,92,96]

@pytest.mark.parametrize('load',[
    'move.w $100(a6),d0\n andi.w #7,d0',
    'move.w $100(a6),d2\n move.w d2,d0\n andi.w #7,d0',
])
def test_compact_cell_domain_can_be_narrowed_after_reload(tmp_path,load):
    with scalar_fixture(tmp_path,before='andi.w #15,$100(a6)',load=load)as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert len(refs)==1
        assert refs[0]['word_index']['byte_offsets']==list(range(84,113,4))
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


@pytest.mark.parametrize('middle,wanted',[
    ('',True),('move.w #3,38(a2)',True),('clr.w 38(a2)',True),
    ('move.b d7,37(a2)',True),('move.b d7,40(a2)',True),
    ('movem.l d4-d5,40(a2)',True),
    ('move.b d7,38(a2)',False),('move.b d7,39(a2)',False),
    ('move.l d7,36(a2)',False),('movem.l d4-d5,32(a2)',False),
    ('move.w d7,38(a2)',False),('addq.w #1,38(a2)',False),
    ('move.w d7,38(a3)',False),('movea.l a2,a3\n move.w d7,38(a3)',False),
    ('move.w d7,$200.l',False),('move.w d7,$DFF180.l',False),
    ('jsr (a3)',False),('trap #1',False),
    ('movea.l a3,a2',False),('lea.l 2(a2),a2',False),
    ('move.w (a2)+,d4',False),('exg a2,a3',False),
    ('movem.l (a3),a2-a3',False),
    ('tst.w d7\n beq.s join\n movea.l a3,a2\njoin:',False),
    ('tst.w d7\n beq.s other\n andi.w #3,38(a2)\n bra.s join\nother:\n andi.w #7,38(a2)\njoin:',True),
])
def test_register_relative_scalar_cells_keep_only_local_must_values(tmp_path,middle,wanted):
    # A2 has a record input contract, not a numeric address, disjointness,
    # stored-value or index contract. The WORD is relative to its current An.
    with scalar_fixture(tmp_path,before='andi.w #7,38(a2)',
            load='move.w 38(a2),d0',middle=middle,record=True)as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert bool(refs)==wanted
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0],
            include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')[0]==original


def test_relative_word_cell_join_does_not_restore_a_missing_definition(tmp_path):
    before='tst.w d7\n beq.s join\n andi.w #7,38(a2)\njoin:'
    with scalar_fixture(tmp_path,before=before,load='move.w 38(a2),d0',record=True)as(a,_):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        assert not[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']


def test_relative_word_cell_closed_loop_uses_the_same_sparse_join(tmp_path):
    before='andi.w #7,38(a2)\n moveq.l #3,d3\nagain:\n andi.w #3,38(a2)\n dbf.w d3,again'
    with scalar_fixture(tmp_path,before=before,load='move.w 38(a2),d0',record=True)as(a,_):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert len(refs)==1 and refs[0]['word_index']['byte_offsets']==[84,88,92,96]


def test_unknown_record_base_cannot_supply_a_relative_word_cell(tmp_path):
    with scalar_fixture(tmp_path,before='andi.w #7,38(a2)',load='move.w 38(a2),d0')as(a,_):
        assert not[r for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
                   if r['field_name']=='value']
