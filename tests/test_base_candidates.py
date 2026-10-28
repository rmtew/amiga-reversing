"""Undeclared fallback operands are leads, never automatic layout facts."""
from contextlib import contextmanager
import json
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource


@contextmanager
def candidate_artifact(tmp_path,code,regions=None,extra=None):
    binary=tmp_path/'input.bin'
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        ' SECTION code,code\n ORG 0\n'+code,output_path=binary)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,load_address=0,entrypoint=0,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    metadata=tmp_path/'metadata.json'
    payload=dict(target_type='program',entry_register_seeds=[],
        rsset_layout_regions=regions if regions is not None else[
            dict(layout_name='app',offset=0,size=4,symbol='known_slot',storage_kind='scalar')])
    payload.update(extra or {})
    metadata.write_text(json.dumps(payload))
    a=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:yield a,original
    finally:a.close()


def test_missing_namespace_operand_is_paged_without_admission_or_reanalysis(tmp_path,monkeypatch):
    with candidate_artifact(tmp_path,' move.l $7c(a6),d0\n lea.l $80(a6),a0\n rts\n') as (a,original):
        before=a.inline_source_text_with_profile()[0]
        a.analysis_payload=lambda:pytest.fail('whole analysis exported')
        a.navigation_payload=lambda:pytest.fail('navigation exported')
        first=a.query_payload('base_candidates',limit=1)
        second=a.query_payload('base_candidates',offset=1,limit=1)
        assert first['total']==second['total']==2
        assert first['has_more'] and not second['has_more']
        one=first['items'][0];two=second['items'][0]
        assert (one['displacement'],one['span_bytes'],one['span_known'])==(124,4,True)
        assert one['base_evidence']=='configured_fallback_unproven' and not one['admitting']
        assert one['coverage']=='undeclared' and one['provenance']=='accepted_instruction'
        assert two['address_only'] and two['span_bytes']==0
        assert a.query_payload('base_candidates',field_offset=124)['items']==[one]
        assert a.query_payload('base_candidates',source_offset=one['source_offset'])['items']==[one]
        assert a.query_payload('base_candidates',symbol='other_namespace')['total']==0
        assert a.query_payload('base_candidates',offset=2)['items']==[]
        from amiga_reversing.disasm import restoration
        monkeypatch.setattr(restoration,'_artifact',lambda _:a)
        request=dict(kind='base_candidates',limit=1)
        current=dict(revision='fixture',subject_revision='fixture-subject')
        page=restoration._query('fixture',request,current)
        assert page['items']==[one] and page['next_cursor']
        following=restoration._query('fixture',dict(request,cursor=page['next_cursor']),current)
        assert following['items']==[two] and following['next_cursor'] is None
        with pytest.raises(ValueError,match='stale_cursor'):
            restoration._query('fixture',dict(request,cursor=page['next_cursor']),
                               dict(current,revision='changed'))
        assert a.inline_source_text_with_profile()[0]==before
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',before)[0]==original


def test_footprints_endpoints_and_adjacent_coverage_are_distinct(tmp_path):
    regions=[dict(layout_name='app',offset=0,size=4,symbol='first',storage_kind='scalar'),
             dict(layout_name='app',offset=4,size=4,symbol='second',storage_kind='scalar')]
    with candidate_artifact(tmp_path,''' lea.l 8(a6),a0
 movem.l d0-d1,0(a6)
 movem.l d0-d2,0(a6)
 move.w 8(a6),d0
 bset.b #0,$82(a6)
 move.w d0,d1
 jsr 12(a6)
 rts
''',regions)as(a,_):
        rows=a.query_payload('base_candidates')['items']
        assert len(rows)==3,rows
        assert [(r['displacement'],r['span_bytes'],r['coverage'])for r in rows]==[
            (0,12,'partially_declared'),(8,2,'undeclared'),(130,1,'undeclared')]
        assert a.query_payload('base_candidates',query='partial')['items']==rows[:1]


@pytest.mark.parametrize('code',[
    ' move.w 0(a6,d0.w),d1\n rts\n',
    ' move.w (a6)+,d1\n rts\n',
    ' lea.l $DFF000.l,a6\n move.w $180(a6),d0\n rts\n',
])
def test_dynamic_updates_and_reported_hardware_do_not_become_slots(tmp_path,code):
    with candidate_artifact(tmp_path,code)as(a,_):
        assert a.query_payload('base_candidates')['total']==0


def test_unreported_absolute_base_does_not_gain_app_provenance(tmp_path):
    # The frozen catalogue does not retain this absolute base at the read.
    # The query must expose that limitation, not re-simulate preceding code
    # or present its fallback lead as a proven app access.
    with candidate_artifact(tmp_path,' lea.l $123456.l,a6\n move.w $7c(a6),d0\n rts\n')as(a,_):
        instruction=a.query_payload('instructions',source_offset=6)['items'][0]
        assert instruction['address_evidence']==[]
        assert instruction['app_slot_refs']==[]
        rows=a.query_payload('base_candidates')['items']
        assert len(rows)==1 and rows[0]['source_offset']==6
        assert rows[0]['base_evidence']=='configured_fallback_unproven'
        assert not rows[0]['admitting']


def test_existing_typed_context_is_not_reinterpreted_as_default_base(tmp_path):
    # An out-of-record typed access is already in the typed gap catalogue.
    with candidate_artifact(tmp_path,' move.w $7c(a6),d0\n rts\n',extra={
        'entry_register_seeds':[dict(entry_offset=0,hunk=0,register='A6',kind='struct_ptr',struct_name='Record',note='Record')],
        'custom_structs':[dict(name='Record',size=4,fields=[dict(name='value',type='LONG',offset=0,size=4)])],
    })as(a,_):
        assert a.query_payload('fields',struct_name='Record')['total']==1
        assert a.query_payload('base_candidates')['total']==0


@pytest.mark.parametrize('regions',[[],[dict(layout_name='other',base_symbol='other_base',
    offset=0,size=4,symbol='other_slot',storage_kind='scalar')]])
def test_only_a_registered_default_namespace_enables_the_heuristic(tmp_path,regions):
    with candidate_artifact(tmp_path,' move.l $7c(a6),d0\n rts\n',regions)as(a,_):
        assert a.query_payload('base_candidates')['total']==0


def test_striped_access_does_not_gain_a_scalar_extent(tmp_path):
    with candidate_artifact(tmp_path,' movep.w d0,$7c(a6)\n rts\n')as(a,_):
        rows=a.query_payload('base_candidates')['items'];assert len(rows)==1
        assert rows[0]['coverage']=='unknown_footprint' and not rows[0]['span_known']
        assert rows[0]['span_bytes']==0 and not rows[0]['admitting']
