"""Direct-body joins are sized by reachable code and a finite must lattice."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact

@pytest.mark.parametrize('shape',['long_linear','diamonds','loop_join'])
def test_finite_direct_body_joins_do_not_enumerate_paths(tmp_path,shape):
    if shape=='long_linear':body='\n'.join(['nop']*300)+'\n rts'
    elif shape=='diamonds':
        body=''
        for i in range(7):body+=f'tst.w d0\n beq.w join_{i}\n movea.l #0,a{i}\njoin_{i}:\n'
        body+='rts'
    else:body='again:\n tst.w d0\n beq.w done\n movea.l #0,a1\n bra.w again\ndone:\n rts'
    a,_=cursor_artifact(tmp_path,'bsr.w helper\n rts\nhelper:\n '+body,regions=False)
    try:
        s=a.analysis_payload()[0]['sections'][0]
        assert len(s['function_summaries'])==1
        assert s['function_summaries'][0]['terminal_reason']=='none'
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()


def test_disagreeing_saved_frames_do_not_become_an_empty_frame(tmp_path):
    a,_=cursor_artifact(tmp_path,'bsr.w helper\n rts\nhelper:\n tst.w d0\n beq.w join\n '+
        'move.l a4,-(a7)\njoin:\n movea.l (a7)+,a4\n rts',regions=False)
    try:
        s=a.analysis_payload()[0]['sections'][0]
        assert s['function_summaries'][0]['terminal_reason']=='direct_body_unsupported'
    finally:a.close()

@pytest.mark.parametrize('body,preserved',[
    ('movem.l d0/a4-a5,-(a7)\n movea.l #0,a4\n movem.l (a7)+,d0/a4-a5',True),
    ('move.l d1,-(a7)\n moveq #0,d1\n move.l (a7)+,d1',True),
    ('movem.w a4-a5,-(a7)\n movea.l #0,a4\n movem.w (a7)+,a4-a5',False),
    ('move.l a4,-(a7)\n move.l a5,-(a7)\n movea.l (a7)+,a5\n movea.l (a7)+,a4',True),
    ('move.l a4,-(a7)\n move.l a5,-(a7)\n movea.l (a7)+,a4\n movea.l (a7)+,a5',False),
    ('move.l a4,-(a7)\n movea.l #0,a4\n move.l a4,-(a7)\n movea.l (a7)+,a4\n movea.l (a7)+,a4',True),
    ('movem.l a4-a5,-(a7)\n move.b #0,1(a7)\n movem.l (a7)+,a4-a5',False),
    ('move.l a4,-(a7)\n movea.l #0,a4\n addq.l #4,a7',False),
    ('move.l a4,-(a7)\n lea.l 4(a7),a7',True),
    ('movem.l a4-a5,-(a7)\n movem.l d0-d1,0(a7)\n movem.l (a7)+,a4-a5',False),
    ('movem.l a4-a5,-(a7)\n clr.b 0(a7,d0.w)\n movem.l (a7)+,a4-a5',False),
])
def test_body_frame_order_and_full_value_identity(tmp_path,body,preserved):
    a,_=cursor_artifact(tmp_path,'bsr.w helper\n rts\nhelper:\n '+body+'\n rts',regions=False)
    try:
        f=a.analysis_payload()[0]['sections'][0]['function_summaries'][0]
        assert f['terminal_reason']=='none'
        effects={v['location'].get('register'):v['effect']for v in f['effects']['registers']['locations']}
        assert (effects['A4']=='preserved')==preserved
        assert effects['A7']=='preserved'
    finally:a.close()


def test_scalar_and_movem_equivalent_frames_share_join_identity(tmp_path):
    a,_=cursor_artifact(tmp_path,'bsr.w helper\n rts\nhelper:\n tst.w d0\n beq.w scalar\n '+
        'movem.l a4-a5,-(a7)\n bra.w join\nscalar:\n move.l a5,-(a7)\n move.l a4,-(a7)\njoin:\n '+
        'movem.l (a7)+,a4-a5\n rts',regions=False)
    try:
        f=a.analysis_payload()[0]['sections'][0]['function_summaries'][0]
        assert f['terminal_reason']=='none'
        effects={v['location'].get('register'):v['effect']for v in f['effects']['registers']['locations']}
        assert effects['A4']==effects['A5']=='preserved'
    finally:a.close()


def test_equal_register_masks_cannot_hide_different_frame_order(tmp_path):
    a,_=cursor_artifact(tmp_path,'bsr.w helper\n rts\nhelper:\n tst.w d0\n beq.w other\n '+
        'move.l a4,-(a7)\n move.l a5,-(a7)\n bra.w join\nother:\n move.l a5,-(a7)\n move.l a4,-(a7)\njoin:\n '+
        'movem.l (a7)+,a4-a5\n rts',regions=False)
    try:
        assert a.analysis_payload()[0]['sections'][0]['function_summaries'][0]['terminal_reason']=='direct_body_unsupported'
    finally:a.close()

@pytest.mark.parametrize('body',[
    'again:\n move.l a4,-(a7)\n tst.w d0\n bne.w again\n movea.l (a7)+,a4\n rts',
    'movea.l a0,a7\n rts',
    'move.l a4,-(a7)\n movea.l a7,a0\n movea.l (a7)+,a4\n rts',
])
def test_unbalanced_backedge_pivot_and_frame_escape_refuse(tmp_path,body):
    a,_=cursor_artifact(tmp_path,'bsr.w helper\n rts\nhelper:\n '+body,regions=False)
    try:
        assert a.analysis_payload()[0]['sections'][0]['function_summaries'][0]['terminal_reason']=='direct_body_unsupported'
    finally:a.close()

@pytest.mark.parametrize('body',[
    'addq.l #4,a4\n movea.l a4,a0',
    'bsr.w inner\n movea.l a4,a0',
])
def test_written_or_callee_clobbered_entry_identity_is_not_a_result(tmp_path,body):
    a,_=cursor_artifact(tmp_path,'bsr.w outer\n rts\nouter:\n '+body+'\n rts\ninner:\n movea.l #0,a4\n rts',regions=False)
    try:
        f=a.analysis_payload()[0]['sections'][0]['function_summaries'][0]
        assert f['terminal_reason']=='none'
        assert not any(r['kind']=='identity_input' and r['location'].get('register')=='A0'for r in f['results'])
        effects={v['location'].get('register'):v['effect']for v in f['effects']['registers']['locations']}
        assert effects['A4']=='clobbered'
    finally:a.close()

@pytest.mark.parametrize('reg',[f'd{i}'for i in range(8)]+[f'a{i}'for i in range(7)])
@pytest.mark.parametrize('width',['w','l'])
def test_decoded_scalar_stack_transports_use_actual_memory_side(tmp_path,reg,width):
    dest='a1'if reg=='a0'else'a0'
    zero='movea.l'if reg.startswith('a')else'move.l'
    pop='movea'if reg.startswith('a')else'move'
    body=f'move.{width} {reg},-(a7)\n {zero} #0,{reg}\n {pop}.{width} (a7)+,{reg}\n movea.l {reg},{dest}\n rts'
    a,_=cursor_artifact(tmp_path,'bsr.w helper\n rts\nhelper:\n '+body,regions=False)
    try:
        f=a.analysis_payload()[0]['sections'][0]['function_summaries'][0]
        assert f['terminal_reason']=='none'
        results=[r for r in f['results']if r['kind']=='identity_input'and r['location'].get('register')==dest.upper()]
        assert bool(results)==(width=='l')
        if results:
            assert f['inputs'][results[0]['input_index']]['location']['register']==reg.upper()
    finally:a.close()
