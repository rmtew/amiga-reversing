"""Declared runtime base holders are not source-address guesses or libraries."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload


def slot(**changes):
    return dict(address=0x1800, size=4, symbol='workspace_holder', storage_kind='pointer',
                semantic_type='layout_base:__amiga_app_base__', **changes)

@pytest.mark.parametrize('instruction,expected', [
    ('movea.l $1800.l,a0', True),
    ('move.l $1800.l,d1\n movea.l d1,a0', True),
    ('movea.w $1800.l,a0', False),
    ('lea.l $1800.l,a0', False),
    ('movea.l #$1800,a0', False),
    ('movea.l $1804.l,a0', False),
    ('movea.l $1800.l,a0\n addq.l #2,a0', False),
    ('movea.l $1800.l,a0\n jsr $2000.l', False),
])
def test_declared_absolute_layout_load(tmp_path, instruction, expected):
    artifact, original = cursor_artifact(tmp_path, instruction+'\n move.w $BC6(a0),d0',
        metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        analysis,_ = artifact.analysis_payload()
        refs=[r for r in analysis['sections'][0]['app_slot_refs']
              if r['base_register']=='A0' and r['displacement']==0xBC6]
        assert bool(refs) == expected
        if refs:
            assert refs[0]['base_evidence']=='register_state'
        from amiga_reversing.disasm import c_backend
        rendered,_=artifact.inline_source_text_with_profile()
        rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',rendered,
            include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')
        assert rebuilt==original
    finally:
        artifact.close()

@pytest.mark.parametrize('changes', [
    {'size':2}, {'storage_kind':'pointer_table'}, {'pointer_struct':'SomeType'},
    {'semantic_type':'layout_base:'}, {'semantic_type':'layout_base:bad symbol'},
    {'semantic_type':'layout_base:missing_layout'},
])
def test_native_refuses_invalid_base_holder(tmp_path, changes):
    metadata=slot();metadata.update(changes)
    with pytest.raises(RuntimeError):
        cursor_artifact(tmp_path,'movea.l $1800.l,a0\n move.w $BC6(a0),d0',
            metadata_extra={'absolute_storage_slots':[metadata]})

@pytest.mark.parametrize('changes', [
    {'size':2}, {'storage_kind':'pointer_table'}, {'pointer_struct':'SomeType'},
    {'semantic_type':'layout_base:'}, {'semantic_type':'layout_base:bad symbol'},
])
def test_catalog_refuses_invalid_base_holder(changes):
    metadata=slot();metadata.update(changes)
    with pytest.raises(ValueError):
        target_catalog_manual_payload('target.absolute_storage_slot.add',metadata)


def test_opaque_pointer_storage_does_not_claim_layout(tmp_path):
    metadata=slot();metadata.pop('semantic_type')
    artifact,_=cursor_artifact(tmp_path,'movea.l $1800.l,a0\n move.w $BC6(a0),d0',
        metadata_extra={'absolute_storage_slots':[metadata]})
    try:
        assert not artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:
        artifact.close()


def test_source_backed_holder_uses_runtime_slot_identity(tmp_path):
    metadata=slot();metadata['address']=0x100C
    artifact,_=cursor_artifact(tmp_path,
        'movea.l holder.l,a0\n move.w $BC6(a0),d0\n rts\nholder:\n dc.l $3300',
        metadata_extra={'absolute_storage_slots':[metadata]})
    try:
        refs=artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert [(r['displacement'],r['base_evidence'])for r in refs]==[(0xBC6,'register_state')]
    finally:
        artifact.close()


def test_conflicting_duplicate_base_role_is_refused(tmp_path):
    conflicting=slot();conflicting.pop('semantic_type')
    with pytest.raises(RuntimeError):
        cursor_artifact(tmp_path,'movea.l $1800.l,a0',
            metadata_extra={'absolute_storage_slots':[slot(),conflicting]})


def test_catalog_preserves_explicit_base_role():
    kind,payload=target_catalog_manual_payload('target.absolute_storage_slot.add',slot())
    assert kind=='create_manual_absolute_storage_slot'
    assert payload['absolute_storage_slot']['semantic_type']=='layout_base:__amiga_app_base__'


def test_source_offset_coincidence_does_not_bind_runtime_holder(tmp_path):
    metadata=slot();metadata['address']=0xC
    artifact,_=cursor_artifact(tmp_path,
        'movea.l holder.l,a0\n move.w $BC6(a0),d0\n rts\nholder:\n dc.l $3300',
        metadata_extra={'absolute_storage_slots':[metadata]})
    try:
        assert not artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:
        artifact.close()


def test_other_named_layout_is_not_an_app_or_library(tmp_path):
    metadata=slot();metadata['semantic_type']='layout_base:other_base'
    artifact,_=cursor_artifact(tmp_path,'movea.l $1800.l,a0\n move.w $BC6(a0),d0',
        metadata_extra={'absolute_storage_slots':[metadata], 'rsset_layout_regions':[
            dict(layout_name='other',base_symbol='other_base',offset=0xBC6,size=120,
                 storage_kind='byte_array',symbol='other_points')]})
    try:
        source,_=artifact.inline_source_text_with_profile()
        assert 'other_points(a0)' in source
        assert not artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:
        artifact.close()


@pytest.mark.parametrize('clobber', [False, True])
def test_cfg_preserved_call_and_jump_keep_declared_base(tmp_path, clobber):
    # The callee changes D1 only. Preservation is an explicit existing callable
    # contract; do not mistake an unanalysed local body for an inferred ABI.
    summary=dict(function_summary_id='preserve_a0',hunk=0,callable_kind='direct',
        entry_offset=14,inputs=[],results=[],note='Normal helper returns preserve A0.',
        effects=dict(schema_version=1,registers=dict(state='explicit',locations=[
            dict(location=dict(kind='register',register=f'{kind}{i}',width=4),
                 effect='clobbered' if (kind=='D' and i==1) or (clobber and kind=='A' and i==0) else 'preserved')
            for kind in ('D','A')for i in range(8)]),memory=dict(state='unknown'),
            escapes=dict(state='unknown')))
    artifact,_=cursor_artifact(tmp_path,
        'movea.l $1800.l,a0\n bsr.w helper\n bra.w consumer\nhelper:\n '+
        ('movea.l #0,a0' if clobber else 'moveq #1,d1')+'\n rts\nconsumer:\n move.w $BC6(a0),d0',
        metadata_extra={'absolute_storage_slots':[slot()], 'function_summaries':[summary]})
    try:
        refs=artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert any(r['base_register']=='A0' and r['displacement']==0xBC6 and
                   r['base_evidence']=='register_state' for r in refs) == (not clobber)
    finally:
        artifact.close()


def test_conflicting_cfg_predecessor_does_not_become_base_from_linear_order(tmp_path):
    artifact,_=cursor_artifact(tmp_path,
        'tst.w d0\n beq.w other\n movea.l $1800.l,a0\n bra.w consumer\nother:\n movea.l #0,a0\nconsumer:\n move.w $BC6(a0),d0',
        metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        assert not artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:
        artifact.close()


def test_unproved_cfg_join_retains_only_legacy_a6_fallback(tmp_path):
    artifact,_=cursor_artifact(tmp_path,
        'tst.w d0\n beq.w other\n movea.l #0,a6\n bra.w consumer\nother:\n movea.l $1800.l,a6\nconsumer:\n move.w $7E4(a6),d0',
        metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        refs=artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert len(refs)==1
        assert refs[0]['base_evidence']=='a6_fallback'
        assert refs[0]['displacement']==0x7E4
    finally:
        artifact.close()
