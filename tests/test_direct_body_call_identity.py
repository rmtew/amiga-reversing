"""Callable entry identities compose through actual register contracts."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact

@pytest.mark.parametrize('inner,source,expected',[
    ('nop\n rts','d7','D7'),
    ('addq.w #1,d7\n rts','d7',None),
    ('movea.l a4,a0\n rts','a0','A4'),
    ('movea.w a4,a0\n rts','a0',None),
    ('movea.l a4,a0\n movea.l #0,a4\n rts','a0','A4'),
    ('move.l d7,-(a7)\n moveq #0,d7\n move.l (a7)+,d7\n rts','d7','D7'),
])
def test_nested_call_entry_result_is_bound_to_precall_value(tmp_path,inner,source,expected):
    a,_=cursor_artifact(tmp_path,f'bsr.w outer\n rts\nouter:\n bsr.w inner\n movea.l {source},a1\n rts\ninner:\n '+inner,regions=False)
    try:
        f=a.analysis_payload()[0]['sections'][0]['function_summaries'][0]
        assert f['terminal_reason']=='none'
        result=[r for r in f['results']if r['kind']=='identity_input'and r['location'].get('register')=='A1']
        assert bool(result)==(expected is not None)
        if result:
            assert f['inputs'][result[0]['input_index']]['location']['register']==expected
    finally:a.close()


def test_callee_clobbered_stack_pointer_cannot_reappear_at_empty_frame(tmp_path):
    summary=dict(function_summary_id='inner_stack_clobber',hunk=0,callable_kind='direct',entry_offset=14,
        inputs=[],results=[],note='Explicit adversarial A7-clobber contract.',effects=dict(schema_version=1,
            registers=dict(state='explicit',locations=[dict(location=dict(kind='register',register=f'{kind}{i}',width=4),
                effect='clobbered'if kind=='A'and i==7 else'preserved')for kind in ('D','A')for i in range(8)]),
            memory=dict(state='explicit',effects=[]),escapes=dict(state='explicit',escapes=[])))
    a,_=cursor_artifact(tmp_path,'bsr.w outer\n rts\nouter:\n bsr.w inner\n nop\n rts\ninner:\n rts',
        regions=False,metadata_extra={'function_summaries':[summary]})
    try:
        summaries=a.analysis_payload()[0]['sections'][0]['function_summaries']
        outer=next(f for f in summaries if f['entry_offset']==6)
        assert outer['terminal_reason']=='direct_body_unsupported'
    finally:a.close()
