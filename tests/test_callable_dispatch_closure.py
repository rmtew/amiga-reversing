"""Callable effects require complete indexed control, not plausible targets."""
import pytest
from tests.test_base_candidates import candidate_artifact
from tests.test_absolute_layout_base import slot
from amiga_reversing.disasm import c_backend


def dispatch(tmp_path, *, count=4, guard=True, mutation='', between='', case='', expose=False, guard_gap='', guard_branch='bhi', annotated=True, main_loop=False):
    entries=','.join(f'case{i}-offsets'for i in range(count))
    cases='\n'.join(f'case{i}:\n '+(case if i==count-1 and case else f'moveq #{i},d1')+'\n rts'for i in range(count))
    code=(f'lea.l {expose if isinstance(expose,str)else "transfer"}(pc),a2\n'if expose else '')+'''movea.l $1800.l,a6
 bsr.w select
 move.w $bc6(a6),d0
 rts
select:
'''+(f' cmpi.w #{count-1},d0\n '+guard_gap+f' {guard_branch}.w default\n'if guard else '')+mutation+'''
 add.w d0,d0
beforeload:
 move.w offsets(pc,d0.w),d0
'''+between+'''
transfer:
 jmp offsets(pc,d0.w)
offsets:
 dc.w '''+entries+'\n'+cases+'''
default:
 rts
helper:
 moveq #3,d2
 rts
'''
    if main_loop:code=code.replace(' bsr.w select', ' moveq #1,d6\nagain:\n move.w $bc6(a6),d7\n dbf.w d6,again\n bsr.w select',1)
    return candidate_artifact(tmp_path,code,[dict(layout_name='app',offset=0xbc6,size=2,
        symbol='field',storage_kind='scalar')]if annotated else [],
        dict(absolute_storage_slots=[slot()])if annotated else {})


def check(a,original,expected,expected_refs=1):
    p=a.analysis_payload()[0];assert not p['incomplete_analysis']
    refs=[r for r in p['sections'][0]['app_slot_refs']if r['displacement']==0xbc6]
    assert len(refs)==expected_refs
    assert all((r['base_evidence']=='register_state')==expected for r in refs)
    source=a.inline_source_text_with_profile()[0]
    assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    return p


@pytest.mark.parametrize('changes',[{},dict(count=8),dict(between='moveq #1,d3\n'),
    dict(count=8,case='bsr.w helper'),dict(main_loop=True)])
def test_guarded_targets_close_callable_effects(tmp_path,changes):
    with dispatch(tmp_path,**changes)as(a,original):
        p=check(a,original,True,2 if changes.get('main_loop')else 1)
        assert all(s['terminal_reason']=='none'for s in p['sections'][0]['function_summaries'])


@pytest.mark.parametrize('changes',[
    dict(guard=False),dict(mutation='addq.w #1,d0\n'),dict(count=16),
    dict(guard_branch='bgt'),dict(guard_gap='tst.w d7\n'),dict(expose='beforeload'),
    dict(between='move.b d7,d0\n'),dict(between='jsr (a3)\n'),
    dict(expose=True),dict(case='jmp (a3)'),
    dict(mutation='move.w #0,offsets.l\n'),
])
def test_incomplete_or_changed_control_refuses(tmp_path,changes):
    with dispatch(tmp_path,**changes)as(a,original):check(a,original,False)


@pytest.mark.parametrize('case',['movea.l d7,a6','movea.l $1804.l,a6'])
def test_clobbering_or_conflicting_returns_are_not_preservation(tmp_path,case):
    with dispatch(tmp_path,case=case)as(a,original):
        p=check(a,original,False)
        assert all(s['terminal_reason']=='none'for s in p['sections'][0]['function_summaries'])


def test_callable_bounds_do_not_require_app_or_type_annotations(tmp_path):
    with dispatch(tmp_path,annotated=False)as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        f=p['sections'][0]['function_summaries'][0]
        assert f['terminal_reason']=='none'
        effects={r['location'].get('register'):r['effect']for r in f['effects']['registers']['locations']}
        assert effects['A6']==effects['A7']=='preserved'
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


def test_late_callable_refinement_refreshes_rendered_app_accesses(tmp_path):
    # A6 has an early fallback row. Closing the callee later adds an A5 row,
    # exercising both growth and the renderer's qualified-evidence projection.
    code='''move.w $bc6(a6),d7
 movea.l $1800.l,a5
 bsr.w select
 move.w $bc6(a5),d0
 rts
select:
 cmpi.w #1,d0
 bhi.s default
 add.w d0,d0
 move.w offsets(pc,d0.w),d0
 jmp offsets(pc,d0.w)
offsets:
 dc.w one-offsets,two-offsets
one:
 moveq #1,d1
 rts
two:
 moveq #2,d1
 rts
default:
 rts
'''
    with candidate_artifact(tmp_path,code,[dict(layout_name='app',offset=0xbc6,size=2,
            symbol='field',storage_kind='scalar')],dict(absolute_storage_slots=[slot()]))as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=p['sections'][0]['app_slot_refs'];assert len(refs)==2
        assert any(r['base_register']=='A5'and r['base_evidence']=='register_state'for r in refs)
        rendered=a.inline_source_text_with_profile()[0]
        assert 'field(a5)'in rendered
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',rendered)[0]==original
