"""Equal affine path potentials support retries without iteration replay."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact,derived_refs

PREFIX='move.w #19,d7\n lea.l $BC6(a6),a4\n'

@pytest.mark.parametrize('shape',['diamond','absolute_rollback','stack_rollback','saved_call'])
@pytest.mark.parametrize('seeded',[False,True])
def test_counter_relative_positive_paths(tmp_path,shape,seeded):
    helper=''
    if shape=='diamond':
        body='tst.w d0\n beq.w right\n move.w (a4)+,d1\n bra.w done\nright:\n move.w (a4)+,d2\ndone:\n'
    elif shape=='absolute_rollback':
        body='move.l a4,$1800.l\nretry:\n move.w (a4)+,d0\n tst.w d0\n beq.w done\n movea.l $1800.l,a4\n bra.w retry\ndone:\n'
    elif shape=='stack_rollback':
        body='move.l a4,-(a7)\nretry:\n move.w (a4)+,d0\n tst.w d0\n beq.w done\n movea.l (a7),a4\n bra.w retry\ndone:\n addq.l #4,a7\n'
    else:
        body='movem.l d7/a4,-(a7)\n move.w d0,-(a7)\n addq.l #2,a7\n bsr.w helper\n movem.l (a7)+,d7/a4\n move.w (a4)+,d0\n'
        helper='\nhelper:\n moveq #0,d7\n movea.l #0,a4\n rts'
    a,original=cursor_artifact(tmp_path,PREFIX+'head:\n '+body+' dbf d7,head\n rts'+helper,seeded=seeded)
    try:
        refs=[r for r in derived_refs(a)if r.get('loop_iteration_count')and r['base_register']=='A4']
        assert len(refs)==(2 if shape=='diamond'else 1)
        assert all(r['displacement']==0xBC6 and r['loop_iteration_count']==20 and r['loop_iteration_stride']==2 for r in refs)
        assert not a.analysis_payload()[0]['incomplete_analysis']
        from amiga_reversing.disasm import c_backend
        text,_=a.inline_source_text_with_profile()
        rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
        assert rebuilt==original
    finally:a.close()

@pytest.mark.parametrize('shape',['different_stride','no_rollback','unknown_alias','partial_restore','counter_changed','unknown_call','owner_overrun','stack_pivot','callee_stack_write'])
def test_counter_relative_refusals(tmp_path,shape):
    prefix=PREFIX
    helper=''
    if shape=='different_stride':body='tst.w d0\n beq.w right\n move.w (a4)+,d1\n bra.w done\nright:\n move.l (a4)+,d2\ndone:\n'
    elif shape=='no_rollback':body='retry:\n move.w (a4)+,d0\n tst.w d0\n bne.w retry\n'
    elif shape=='unknown_alias':body='move.l a4,$1800.l\n move.b d0,(a0)\n movea.l $1800.l,a4\n move.w (a4)+,d0\n'
    elif shape=='partial_restore':body='move.l a4,-(a7)\n movea.w (a7)+,a4\n addq.l #2,a7\n move.w (a4)+,d0\n'
    elif shape=='counter_changed':body='move.w (a4)+,d0\n subq.w #1,d7\n'
    elif shape=='unknown_call':body='jsr (a0)\n move.w (a4)+,d0\n'
    elif shape=='owner_overrun':prefix=PREFIX.replace('#19','#120');body='move.w (a4)+,d0\n'
    elif shape=='callee_stack_write':
        body='movem.l d7/a4,-(a7)\n bsr.w helper\n movem.l (a7)+,d7/a4\n move.w (a4)+,d0\n'
        helper='\nhelper:\n move.l #0,4(a7)\n rts'
    else:body='movea.l a0,a7\n move.w (a4)+,d0\n'
    a,_=cursor_artifact(tmp_path,prefix+'head:\n '+body+' dbf d7,head\n rts'+helper)
    try:assert not [r for r in derived_refs(a)if r.get('loop_iteration_count')]
    finally:a.close()
