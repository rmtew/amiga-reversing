"""Whole named runtime bases cross full-value transports, not partial writes."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_absolute_layout_base import slot


def fixture(tmp_path, transport, *, named=False, middle='', after=''):
    metadata=slot()
    extra={'absolute_storage_slots':[metadata]}
    if named:
        metadata['semantic_type']='layout_base:other_base'
        extra['rsset_layout_regions']=[dict(layout_name='other',base_symbol='other_base',
            offset=0xBC6,size=120,storage_kind='byte_array',symbol='other_points')]
    push,pop=transport
    body=f'movea.l $1800.l,a0\n {push}\n movea.l #0,a0\n {middle}\n {pop}\n {after}\n move.w $BC6(a0),d1'
    return cursor_artifact(tmp_path,body,metadata_extra=extra)

@pytest.mark.parametrize('named',[False,True])
@pytest.mark.parametrize('transport',[
    ('movem.l a0,-(a7)','movem.l (a7)+,a0'),
    ('move.l a0,-(a7)','movea.l (a7)+,a0'),
    ('move.l a0,d0\n movem.l d0/a1,-(a7)',
     'movem.l (a7)+,d0/a1\n movea.l d0,a0'),
])
def test_whole_layout_base_value_roundtrip(tmp_path,transport,named):
    a,original=fixture(tmp_path,transport,named=named)
    try:
        source,_=a.inline_source_text_with_profile()
        if named:
            assert 'other_points(a0)'in source
            assert not a.analysis_payload()[0]['sections'][0]['app_slot_refs']
            refs=a.query_payload('references',symbol='other_points',limit=20)['items']
            assert any(r['provenance']=='typed_operand' and not r['comment_only'] for r in refs)
        else:
            refs=a.analysis_payload()[0]['sections'][0]['app_slot_refs']
            assert any(r['base_register']=='A0' and r['displacement']==0xBC6 and
                       r['base_evidence']=='register_state'for r in refs)
        from amiga_reversing.disasm import c_backend
        rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source,
            include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')
        assert rebuilt==original
    finally:a.close()

@pytest.mark.parametrize('named',[False,True])
@pytest.mark.parametrize('transport,middle',[
    (('movem.w a0,-(a7)','movem.w (a7)+,a0'),''),
    (('movem.l a0,-(a7)','movem.l (a7)+,a0'),'move.b #0,1(a7)'),
    (('movem.l a0,-(a7)','movem.l (a7)+,a0'),'adda.l d0,a7'),
])
def test_partial_or_unknown_saved_base_is_not_promoted(tmp_path,transport,middle,named):
    a,_=fixture(tmp_path,transport,named=named,middle=middle)
    try:
        source,_=a.inline_source_text_with_profile()
        assert 'other_points(a0)'not in source
        assert not a.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:a.close()


@pytest.mark.parametrize('named',[False,True])
@pytest.mark.parametrize('after',['addq.l #2,a0','adda.l d0,a0','movea.w a0,a0','move.w (a0)+,d0'])
def test_restored_root_changes_do_not_retain_unchanged_base_identity(tmp_path,named,after):
    a,_=fixture(tmp_path,('movem.l a0,-(a7)','movem.l (a7)+,a0'),named=named,after=after)
    try:
        source,_=a.inline_source_text_with_profile()
        assert 'other_points(a0)'not in source
        assert not a.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:a.close()


def test_distinct_root_namespaces_survive_same_frame_without_conflation(tmp_path):
    regions=[dict(layout_name='app',offset=0xBC6,size=120,storage_kind='byte_array',symbol='world_points'),
             dict(layout_name='other',base_symbol='other_base',offset=0xBC6,size=120,
                  storage_kind='byte_array',symbol='other_points')]
    other=dict(slot(),address=0x1804,symbol='other_holder',semantic_type='layout_base:other_base')
    a,_=cursor_artifact(tmp_path,
        'movea.l $1800.l,a0\n movea.l $1804.l,a1\n movem.l a0-a1,-(a7)\n movea.l #0,a0\n movea.l #0,a1\n movem.l (a7)+,a0-a1\n move.w $BC6(a0),d0\n move.w $BC6(a1),d1',
        metadata_extra={'absolute_storage_slots':[slot(),other],'rsset_layout_regions':regions})
    try:
        source,_=a.inline_source_text_with_profile()
        assert 'world_points(a0)'in source and 'other_points(a1)'in source
        refs=a.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert len(refs)==1 and refs[0]['base_register']=='A0'
    finally:a.close()


def test_conflicting_saved_namespaces_merge_to_unknown(tmp_path):
    regions=[dict(layout_name='app',offset=0xBC6,size=120,storage_kind='byte_array',symbol='world_points'),
             dict(layout_name='other',base_symbol='other_base',offset=0xBC6,size=120,
                  storage_kind='byte_array',symbol='other_points')]
    other=dict(slot(),address=0x1804,symbol='other_holder',semantic_type='layout_base:other_base')
    a,_=cursor_artifact(tmp_path,
        'tst.w d0\n beq.w alternate\n movea.l $1800.l,a0\n bra.w save\nalternate:\n movea.l $1804.l,a0\nsave:\n movem.l a0,-(a7)\n movea.l #0,a0\n movem.l (a7)+,a0\n move.w $BC6(a0),d1',
        metadata_extra={'absolute_storage_slots':[slot(),other],'rsset_layout_regions':regions})
    try:
        source,_=a.inline_source_text_with_profile()
        assert 'other_points(a0)'not in source and 'world_points(a0)'not in source
        assert not a.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:a.close()


@pytest.mark.parametrize('effect',['preserved','clobbered','inferred','unknown'])
def test_named_base_obeys_existing_callable_effects(tmp_path,effect):
    summary=dict(function_summary_id='helper_effects',hunk=0,callable_kind='direct',entry_offset=16,
        inputs=[],results=[],note='Normal helper return register effects.',effects=dict(schema_version=1,
        registers=dict(state='explicit',locations=[dict(location=dict(kind='register',register=f'{k}{i}',width=4),
            effect='clobbered' if effect=='clobbered' and k=='A' and i==0 else 'preserved')
            for k in ('D','A')for i in range(8)]),memory=dict(state='unknown'),escapes=dict(state='unknown')))
    metadata=dict(slot(),semantic_type='layout_base:other_base')
    extra={'absolute_storage_slots':[metadata],'rsset_layout_regions':[dict(layout_name='other',base_symbol='other_base',
        offset=0xBC6,size=120,storage_kind='byte_array',symbol='other_points')]}
    if effect in ('preserved','clobbered'):extra['function_summaries']=[summary]
    call='jsr $2000.l' if effect=='unknown' else 'bsr.w helper'
    a,_=cursor_artifact(tmp_path,'movea.l $1800.l,a0\n '+call+'\n move.w $BC6(a0),d1\n rts\nhelper:\n '+
        ('movea.l #0,a0\n'if effect=='clobbered'else'')+' rts',metadata_extra=extra)
    try:
        source,_=a.inline_source_text_with_profile()
        assert ('other_points(a0)'in source)==(effect in ('preserved','inferred'))
        assert not a.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:a.close()


def test_valid_ambiguous_layout_alias_does_not_choose_a_symbol(tmp_path):
    metadata=dict(slot(),semantic_type='layout_base:other_base')
    regions=[dict(layout_name='other',base_symbol='other_base',offset=0xBC6,size=120,
                  storage_kind='byte_array',symbol='other_points'),
             dict(layout_name='other_phase',base_symbol='other_base',offset=0xBC6,size=120,
                  storage_kind='byte_array',symbol='other_alias')]
    a,_=cursor_artifact(tmp_path,'movea.l $1800.l,a0\n movem.l a0,-(a7)\n movea.l #0,a0\n movem.l (a7)+,a0\n move.w $BC6(a0),d1',
        metadata_extra={'absolute_storage_slots':[metadata],'rsset_layout_regions':regions})
    try:
        source,_=a.inline_source_text_with_profile()
        assert 'other_points(a0)'not in source and 'other_alias(a0)'not in source
        assert not a.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:a.close()


def test_incomplete_cfg_does_not_publish_new_layout_binding(tmp_path,monkeypatch):
    monkeypatch.setenv('AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS','16')
    body='tst.w d0\n bne.w delayed\n movea.l $1800.l,a0\n movem.l a0,-(a7)\n movea.l #0,a0\n movem.l (a7)+,a0\n bra.w consumer\ndelayed:\n '+\
        '\n '.join(['nop']*20)+'\n movea.l #0,a0\nconsumer:\n move.w $BC6(a0),d1'
    metadata=dict(slot(),semantic_type='layout_base:other_base')
    a,_=cursor_artifact(tmp_path,body,metadata_extra={'absolute_storage_slots':[metadata],
        'rsset_layout_regions':[dict(layout_name='other',base_symbol='other_base',offset=0xBC6,size=120,
             storage_kind='byte_array',symbol='other_points')]})
    try:
        assert a.analysis_payload()[0]['incomplete_analysis']
        assert not a.query_payload('references',symbol='other_points',limit=20)['items']
    finally:a.close()

@pytest.mark.parametrize('callee,preserved',[
    ('rts',True),('movea.l #0,a0\n rts',True),('move.l #0,4(a7)\n rts',False),
])
def test_known_register_partition_preserves_private_saves_unless_stack_written(tmp_path,callee,preserved):
    a,_=cursor_artifact(tmp_path,'lea.l $C3E(a6),a0\n movem.l a0,-(a7)\n '+
        'move.w d1,-(a7)\n addq.l #2,a7\n bsr.w helper\n movem.l (a7)+,a0\n '+
        'move.w (a0),d0\n rts\nhelper:\n '+callee)
    try:
        refs=a.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert bool([r for r in refs if r['base_register']=='A0'and r['access']=='read'])==preserved
    finally:a.close()
