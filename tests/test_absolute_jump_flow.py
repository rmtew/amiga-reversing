"""Typed CFG/body walkers consume existing absolute executable mappings."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_absolute_layout_base import slot

@pytest.mark.parametrize('jump',['bra.w target','jmp target.l','jmp target.w'])
def test_known_absolute_jump_carries_the_same_base_as_relative_branch(tmp_path,jump):
    a,_=cursor_artifact(tmp_path,'movea.l $1800.l,a0\n '+jump+'\ntarget:\n move.w $BC6(a0),d0',
        metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        refs=a.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert len(refs)==1 and refs[0]['base_evidence']=='register_state'
    finally:a.close()


def test_direct_body_absolute_tail_jump_uses_existing_runtime_mapping(tmp_path):
    a,_=cursor_artifact(tmp_path,'movea.l $1800.l,a0\n bsr.w helper\n move.w $BC6(a0),d0\n rts\nhelper:\n jmp tail.l\ntail:\n rts',
        metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        s=a.analysis_payload()[0]['sections'][0]
        assert len(s['app_slot_refs'])==1 and s['app_slot_refs'][0]['base_evidence']=='register_state'
        assert all(f['terminal_reason']=='none'for f in s['function_summaries'])
    finally:a.close()

@pytest.mark.parametrize('unknown',['jmp (a0)','jmp $2000.l'])
def test_one_return_does_not_hide_an_unresolved_tail_path(tmp_path,unknown):
    a,_=cursor_artifact(tmp_path,'bsr.w helper\n rts\nhelper:\n tst.w d0\n beq.w unknown\n rts\nunknown:\n '+unknown)
    try:
        s=a.analysis_payload()[0]['sections'][0]
        assert s['function_summaries']
        assert all(f['terminal_reason']=='direct_body_unsupported'for f in s['function_summaries'])
    finally:a.close()


def test_pointer_only_observation_does_not_create_executable_jump_entry(tmp_path):
    a,_=cursor_artifact(tmp_path,'movea.l $1800.l,a0\n jmp $4000.l\n move.w $BC6(a0),d0',
        metadata_extra={'absolute_storage_slots':[slot()],
            'execution_views':[dict(source_start=12,source_end=18,base_addr=0x4000,
                runtime_view_use='pointer_target')]})
    try:
        assert not a.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:a.close()


def test_unmapped_conditional_branch_cannot_be_ignored_by_body_proof(tmp_path):
    a,_=cursor_artifact(tmp_path,'bsr.w helper\n rts\nhelper:\n tst.w d0\n beq.w $2000\n rts')
    try:
        s=a.analysis_payload()[0]['sections'][0]
        assert s['function_summaries']
        assert all(f['terminal_reason']=='direct_body_unsupported'for f in s['function_summaries'])
    finally:a.close()
