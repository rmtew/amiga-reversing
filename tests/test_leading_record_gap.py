"""An opaque leading gap retains its declared record identity, not field meaning."""
from contextlib import closing

import pytest
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.effective_metadata import effective_metadata_file,effective_target_metadata
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind,append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata


def projected(tmp_path,access=14,target=32,conflict=False,count=1,tail=None):
    # LEA record(PC),A0; MOVE.W displacement(A0),D0; RTS.
    binary=tmp_path/'input.bin'
    code=bytes.fromhex('41fa')+(target-2).to_bytes(2,'big')
    code+=bytes.fromhex(tail)if tail else bytes.fromhex('3028')+access.to_bytes(2,'big')+bytes.fromhex('4e75')
    binary.write_bytes(code+bytes(32+16*count-len(code)))
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,address_model=RawAddressModel.LOCAL_OFFSET,load_address=0,entrypoint=0,code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[]
    def add(command,parameters):
        kind,payload=target_catalog_manual_payload(command,parameters);actions.append((ManualActionKind(kind),payload));return payload
    add('target.custom_struct.add',dict(name='Frame',size=16,fields=[dict(name='sample',type='WORD',offset=14,size=2)]))
    owner=add('target.data_block.layout.create',dict(hunk=0,source_start=32,source_end=32+16*count,name='frame',role='data'))['data_block_layout']
    add('target.data_block.element.set',dict(layout_id=owner['layout_id'],offset=0,width=16*count,kind='struct',array_count=count,array_stride=16,binding_kind='custom_struct',type_id='Frame'))
    if conflict:
        add('target.custom_struct.add',dict(name='Other',size=16,fields=[dict(name='different',type='WORD',offset=14,size=2)]))
        other=add('target.data_block.layout.create',dict(hunk=0,source_start=32,source_end=48,name='other',role='data'))['data_block_layout']
        add('target.data_block.element.set',dict(layout_id=other['layout_id'],offset=0,width=16,kind='struct',binding_kind='custom_struct',type_id='Other'))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    metadata=effective_target_metadata(tmp_path)
    with effective_metadata_file(tmp_path)as path:
        artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=path)[2]
    with closing(artifact):
        return metadata,artifact.query_payload('fields',limit=20)['items'],artifact.source_text_with_profile()[0],binary.read_bytes()


@pytest.mark.parametrize('target,access',[(32,14),(34,12),(45,1)])
def test_leading_gap_address_recovers_declared_field_without_naming_opaque_bytes(tmp_path,target,access):
    metadata,fields,text,original=projected(tmp_path,target=target,access=access)
    assert any(f.get('field_name')=='sample'and f.get('field_offset')==14 for f in fields)
    gap=next(e for e in metadata.seeded_entities if e.addr==32)
    assert gap.struct_name=='Frame'and not gap.field_name and gap.end==46
    if target==32:assert '\tdcb.b $E,$00' in text
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
    assert rebuilt==original


@pytest.mark.parametrize('target,access',[(32,0),(32,13),(32,16),(48,0)])
def test_unknown_prefix_crossing_field_and_one_past_do_not_invent_fields(tmp_path,target,access):
    _,fields,_,_=projected(tmp_path,target=target,access=access)
    assert not any(f.get('field_name')=='sample'for f in fields)


def test_conflicting_exact_owner_declaration_is_rejected_before_projection(tmp_path):
    with pytest.raises(ValueError,match='already covers this exact range'):
        projected(tmp_path,conflict=True)


def test_later_declared_record_prefix_has_its_own_zero_cursor(tmp_path):
    metadata,fields,text,original=projected(tmp_path,target=48,count=2)
    assert any(f.get('field_name')=='sample'and f.get('field_offset')==14 for f in fields)
    gap=next(e for e in metadata.seeded_entities if e.addr==48)
    assert gap.struct_name=='Frame'and gap.end==62 and not gap.field_name
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
    assert rebuilt==original


@pytest.mark.parametrize('clobber',['2041','3041','d0c1','4e91'])
def test_opaque_prefix_identity_does_not_survive_unknown_base_write_or_call(tmp_path,clobber):
    # MOVEA.L D1,A0; MOVEA.W D1,A0; ADDA.W D1,A0; JSR(A1).
    _,fields,_,_=projected(tmp_path,tail=clobber+'3028000e4e75')
    assert not any(f.get('field_name')=='sample'for f in fields)
