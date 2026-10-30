"""Declared layout roles survive generated callable results and closed callers."""
import pytest
from tests.test_base_candidates import candidate_artifact
from tests.test_absolute_layout_base import slot
from amiga_reversing.disasm import c_backend


def named_call(tmp_path, helper='movea.l $1800.l,a6', *, nested=False, expose=False, direct=False, caller_edit=''):
    metadata=dict(absolute_storage_slots=[slot()], custom_structs=[dict(name='Slot',size=4,
        fields=[dict(name='value',type='LONG',offset=0,size=4)])],entry_register_seeds=[
        dict(hunk=0,entry_offset=0,register='A0',kind='struct_ptr',struct_name='Slot',array_length=32,note='Input reference array')])
    prefix=('lea.l worker(pc),a2\n' if expose else '')+('movea.l $1800.l,a6\n' if direct else 'bsr.w acquire\n')
    code=(prefix+caller_edit+'bsr.w worker\n rts\nworker:\n andi.w #7,$100(a6)\n move.w $100(a6),d0\n'
          ' addi.w #21,d0\n lsl.w #2,d0\n move.l 0(a0,d0.w),d1\n rts\nacquire:\n'+
          ('bsr.w inner\n rts\ninner:\n' if nested else '')+helper+'\n rts\n')
    return candidate_artifact(tmp_path,code,[dict(layout_name='app',offset=0x100,size=2,symbol='cycle',storage_kind='scalar')],metadata)


@pytest.mark.parametrize('nested,direct',[(False,False),(True,False),(False,True)])
def test_named_base_producer_to_closed_callee_index_consumer(tmp_path,nested,direct):
    with named_call(tmp_path,nested=nested,direct=direct)as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert len(refs)==1
        assert refs[0]['word_index']['byte_offsets']==list(range(84,113,4))
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


@pytest.mark.parametrize('helper,expose',[
    ('movea.w $1800.l,a6',False),('lea.l $1800.l,a6',False),
    ('movea.l $1800.l,a6\n addq.l #2,a6',False),
    ('movea.l $1800.l,a6\n jsr (a2)',False),
    ('tst.w d7\n beq.s unchanged\n movea.l $1800.l,a6\nunchanged:',False),
    ('movea.l $1800.l,a6',True),
])
def test_unproved_results_and_independent_callers_refuse(tmp_path,helper,expose):
    with named_call(tmp_path,helper,expose=expose)as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        assert not[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original

@pytest.mark.parametrize('helper',[
    'move.l $1800.l,d2\n movea.l d2,a6',
    'movea.l $1800.l,a4\n movea.l a4,a6',
    'tst.w d7\n beq.s other\n movea.l $1800.l,a6\n bra.s done\nother:\n movea.l $1800.l,a6\ndone:',
])
def test_layout_results_are_nominal_and_copied_by_shared_transfer(tmp_path,helper):
    with named_call(tmp_path,helper)as(a,_):
        p=a.analysis_payload()[0]
        summaries=p['sections'][0]['function_summaries']
        roles=[r for s in summaries for r in s['results'] if r.get('kind')=='base_register']
        assert roles and all(r['base_name']=='__amiga_app_base__'for r in roles)
        assert [r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']

@pytest.mark.parametrize('helper',[
    'movea.l $1800.l,a6\n move.w d7,a6',
    'move.l $1800.l,d2\n move.b d7,d2\n movea.l d2,a6',
    'movea.l $1800.l,a6\n jmp (a2)',
])
def test_partial_or_unclosed_results_do_not_acquire_a_layout(tmp_path,helper):
    with named_call(tmp_path,helper)as(a,_):
        p=a.analysis_payload()[0]
        assert not[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']

@pytest.mark.parametrize('caller_edit',[
    'move.w d7,a6\n',
    'tst.w d7\n beq.s retain\n movea.l d7,a6\nretain:\n',
    'bsr.w worker\n movea.l d7,a6\n',
    'jsr (a2)\n',
])
def test_call_entry_roles_require_all_known_callers(tmp_path,caller_edit):
    with named_call(tmp_path,caller_edit=caller_edit)as(a,_):
        p=a.analysis_payload()[0]
        assert not[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']

@pytest.mark.parametrize('conflicting',[False,True])
def test_non_app_layout_results_keep_namespace_identity(tmp_path,conflicting):
    other=dict(slot(),address=0x1804,symbol='other_holder',semantic_type='layout_base:other_base')
    regions=[dict(layout_name='app',offset=0xBC6,size=2,symbol='app_item',storage_kind='scalar'),
             dict(layout_name='other',base_symbol='other_base',offset=0xBC6,size=2,
                  symbol='other_item',storage_kind='scalar')]
    helper=('tst.w d7\n beq.s other\n movea.l $1800.l,a4\n bra.s done\nother:\n '
            if conflicting else '')+'movea.l $1804.l,a4\ndone:\n rts'
    with candidate_artifact(tmp_path,'bsr.w acquire\n move.w $bc6(a4),d0\n rts\nacquire:\n'+helper,
            regions,dict(absolute_storage_slots=[slot(),other]))as(a,original):
        p=a.analysis_payload()[0]
        source=a.inline_source_text_with_profile()[0]
        assert ('other_item(a4)'in source)==(not conflicting)
        assert not p['sections'][0]['app_slot_refs']
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
