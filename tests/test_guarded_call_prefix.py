"""Caller-local predicates select a proved suffix without weakening the callable."""
import pytest
from tests.test_source_pointer_loop_domain import header_table_artifact, typed_fields
from amiga_reversing.disasm import c_backend


def guarded_artifact(tmp_path, *, flags='$8001',before='',predicate='',suffix='',helpers=''):
    return header_table_artifact(tmp_path,count=104,target_type='raw_binary',
        # The real SGII reader owns its directory counter after the call.
        setup='lea.l $60000.l,a6\nmove.l a6,saved_frame.l\n'+before+
              '\nbsr platform_init\nlea.l directory(pc),a3\nmove.w #103,d4\n',
        record_access='move.w (a0)+,d0\nmove.w (a0),d1\nmove.w d0,$40(a6)\n',
        code_tail=('unknown:move.b #0,(a2)\nrts\nplatform_init:\n'
                   'move.w platform_flags.l,d0\n'+predicate+'\nbpl alternate\n'
                   'btst #0,d0\nbeq alternate\nmovea.l saved_frame.l,a6\n'+suffix+
                   '\nnop\nrts\nalternate:trap #1\nrts\nplatform_flags:dc.w '+flags+
                   '\ndc.w 0\nsaved_frame:dc.l 0\n'+helpers),)


@pytest.mark.parametrize('changes', [{},
    {'flags':'$0001','before':'move.l #$80010000,platform_flags.l'},
    {'flags':'$0001','predicate':'move.w #$8001,d0'}])
def test_caller_predicate_and_reloaded_base_reach_reader(tmp_path,changes):
    a,original=guarded_artifact(tmp_path,**changes)
    try:
        payload=a.analysis_payload()[0]
        assert typed_fields(a)=={('A0','count'),('A0','flags')}
        assert not payload['incomplete_analysis']
        assert any(s.get('terminal_reason')=='direct_body_unsupported'for s in payload['sections'][0]['function_summaries'])
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
    finally:a.close()


@pytest.mark.parametrize('changes', [
    {'flags':'$0001'}, {'flags':'$8000'},
    {'before':'move.w #1,platform_flags.l'},
    {'before':'move.l #$00010000,platform_flags.l'},
    {'before':'move.b #0,(a2)'}, {'before':'jsr unknown'},
    {'before':'tst.w d7\nbeq join\nmove.w #1,platform_flags.l\njoin:'},
    {'predicate':'moveq #0,d0'},
    {'before':'moveq #1,d7\nchanging:tst.w platform_flags.l\nbpl stopped\nmove.l #0,platform_flags.l\ndbf d7,changing\nstopped:'},
    {'suffix':'jsr (a2)'},
    {'suffix':'movea.l sp,a6'},
    {'suffix':'movea.l (sp)+,a6'},
    {'before':'lea.l call_again.l,a4\ncall_again:'},
])
def test_unproved_mutated_conflicting_or_unknown_context_refuses(tmp_path,changes):
    a,_=guarded_artifact(tmp_path,**changes)
    try: assert not typed_fields(a)
    finally:a.close()


def test_caller_memory_predicate_selects_frame_writer_before_scoped_call(tmp_path):
    before=('move.l #directory-$40,saved_frame.l\n'
            'btst #0,platform_flags+1.l\nbeq keep_old\n'
            'lea.l $68000.l,a6\nmove.l a6,saved_frame.l\nkeep_old:')
    a,original=guarded_artifact(tmp_path,before=before)
    try:
        assert typed_fields(a)=={('A0','count'),('A0','flags')}
        assert not a.analysis_payload()[0]['incomplete_analysis']
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
    finally:a.close()


def test_bus_alias_mutation_cannot_preserve_original_predicate(tmp_path):
    a,_=guarded_artifact(tmp_path,before='move.w #1,platform_flags+$1000000.l')
    try:assert not typed_fields(a)
    finally:a.close()

@pytest.mark.parametrize('boundary',['bsr empty','move.w $dff006.l,d0'])
def test_initial_edge_refinement_does_not_become_later_phase_closure(tmp_path,boundary):
    before=(boundary+'\nmove.l #directory-$40,saved_frame.l\n'
            'btst #0,platform_flags+1.l\nbeq keep_old\n'
            'lea.l $68000.l,a6\nmove.l a6,saved_frame.l\nkeep_old:')
    a,_=guarded_artifact(tmp_path,before=before,helpers='empty:rts\n')
    try:
        assert not typed_fields(a)
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()
