"""Explicit scalar domains improve source without supplying runtime value proofs."""
from dataclasses import asdict
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.target_metadata import CustomStructFieldMetadata
from tests.test_base_candidates import candidate_artifact
from tests.test_typed_index_symbol_compensation import exact


def domain_metadata(group='modes', width=2, equates=None, inherited=False):
    records = [dict(name='Record', size=4, fields=[dict(name='mode', type='WORD',
        offset=0, size=width, equate_group=group)])]
    if inherited:
        records.append(dict(name='Child', size=8, base_struct='Record', base_offset=4,
            fields=[dict(name='tail', type='LONG', offset=4, size=4)]))
    return dict(custom_structs=records,
        entry_register_seeds=[dict(hunk=0,entry_offset=0,register='A0',kind='struct_ptr',
            struct_name='Child' if inherited else 'Record',note='Fixture input')],
        target_equates=equates if equates is not None else [dict(name='MODE_ACTIVE',value=12,group='modes')])


@pytest.mark.parametrize('code,wanted', [
    ('move.w #12,(a0)', True), ('cmpi.w #12,(a0)', True),
    ('move.w #13,(a0)', False), ('move.w #12,d0', False),
    ('move.b #12,(a0)', False), ('move.l #12,(a0)', False),
    ('addi.w #12,(a0)', False), ('andi.w #12,(a0)', False),
])
def test_whole_scalar_move_compare_only(tmp_path,code,wanted):
    with candidate_artifact(tmp_path,code+'\n rts',[],domain_metadata()) as (a,original):
        source=exact(a,original,tmp_path)
        rows=[line for line in source.splitlines() if '#' in line]
        assert any('#MODE_ACTIVE' in line for line in rows)==wanted,source
        assert not a.analysis_payload()[0]['incomplete_analysis']


@pytest.mark.parametrize('case', ['inherited','other_group','ambiguous','encoding_alias','address','expression','manual','unknown'])
def test_group_selection_and_refusals(tmp_path,case):
    eq=[dict(name='MODE_ACTIVE',value=12,group='modes')]
    if case=='other_group':eq.append(dict(name='OTHER_TWELVE',value=12,group='unrelated'))
    if case=='ambiguous':eq.append(dict(name='ALSO_ACTIVE',value=12,group='modes'))
    if case=='encoding_alias':eq=[dict(name='NEGATIVE_ONE',value=-1,group='modes'),dict(name='ALL_BITS',value=65535,group='modes')]
    if case=='address':eq[0].update(address_domain='runtime',extent_bytes=1)
    if case=='expression':eq[0].update(value_expression='6+6')
    metadata=domain_metadata(group='absent' if case=='unknown' else 'modes',equates=eq,inherited=case=='inherited')
    if case=='manual':metadata['manual_representations']=[dict(hunk=0,addr=0,end=4,style='hex',element_kind='immediate',operand_index=0,width_bytes=2)]
    value=65535 if case=='encoding_alias' else 12
    with candidate_artifact(tmp_path,f'move.w #{value},(a0)\n rts',[],metadata) as (a,original):
        source=exact(a,original,tmp_path)
        assert ('#MODE_ACTIVE' in source)==(case in ['inherited','other_group']),source
        assert '#NEGATIVE_ONE' not in source and '#ALL_BITS' not in source


@pytest.mark.parametrize('width,value',[(1,12),(2,12),(4,12),(1,-1),(2,-1)])
def test_field_width_and_signed_encodings(tmp_path,width,value):
    eq=[dict(name='MODE_VALUE',value=value,group='modes')]
    metadata=domain_metadata(width=width,equates=eq)
    size={1:'b',2:'w',4:'l'}[width]
    with candidate_artifact(tmp_path,f'move.{size} #{value},(a0)\n rts',[],metadata) as (a,original):
        source=exact(a,original,tmp_path)
        if width==1 and value<0:
            assert 'non-canonical byte-immediate encoding' in source
        else:assert '#MODE_VALUE' in source


@pytest.mark.parametrize('change',[dict(equate_group=''),dict(equate_group='x'*64),dict(size=3),
    dict(struct='Nested'),dict(named_base='app'),dict(value_kind='target_pointer')])
def test_invalid_scalar_group_binding(change):
    with pytest.raises(ValueError,match='equate_group'):
        CustomStructFieldMetadata(**(dict(name='mode',type='WORD',offset=0,size=2,equate_group='modes')|change))


def test_optional_codec_legacy_shape():
    from amiga_reversing.disasm.target_metadata import TargetMetadata,CustomStructMetadata,TargetMetadataSeedOrigin,TargetMetadataReviewStatus,target_metadata_json_payload
    field=CustomStructFieldMetadata(name='mode',type='WORD',offset=0,size=2)
    payload=target_metadata_json_payload(TargetMetadata(target_type="program",entry_register_seeds=(),custom_structs=(CustomStructMetadata(name='Record',size=2,fields=(field,),seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,review_status=TargetMetadataReviewStatus.SEEDED,citation='fixture'),)))
    assert 'equate_group' not in payload['custom_structs'][0]['fields'][0]
    bound=CustomStructFieldMetadata.from_dict(asdict(field)|dict(equate_group='modes'))
    assert bound.equate_group=='modes'


@pytest.mark.parametrize('ambiguous',[False,True])
@pytest.mark.parametrize('group',['modes','exec.node.type'])
@pytest.mark.parametrize('manual',[False,True])
def test_canonical_bound_scalar_arrays_use_group_without_pointer_intent(tmp_path,ambiguous,group,manual):
    from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
    from amiga_reversing.disasm.effective_metadata import effective_metadata_file
    from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
    from amiga_reversing.disasm.manual_actions import ManualActionKind,append_manual_actions
    from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
    raw=bytes.fromhex('4e75000c000d000c')
    path=tmp_path/'input.bin';path.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,
        address_model=RawAddressModel.LOCAL_OFFSET,load_address=0,entrypoint=0,code_start_offset=0,
        display_path=str(path),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[]
    def add(command,**parameters):
        kind,payload=target_catalog_manual_payload(command,parameters)
        actions.append((ManualActionKind(kind),payload));return payload
    add('target.custom_struct.add',name='Record',size=2,fields=[dict(name='mode',type='WORD',offset=0,size=2,equate_group=group)])
    add('target.equate.add',name='MODE_ACTIVE',value=12,group=group)
    if ambiguous:add('target.equate.add',name='ALSO_ACTIVE',value=12,group=group)
    layout=add('target.data_block.layout.create',hunk=0,source_start=2,source_end=8,name='modes',default_unit='word')['data_block_layout']['layout_id']
    add('target.data_block.element.set',layout_id=layout,offset=0,width=6,kind='array',name='modes',array_count=3,array_stride=2,binding_kind='custom_struct',type_id='Record')
    if manual:actions.append((ManualActionKind.CREATE_MANUAL_REPRESENTATION,{'representation':dict(representation_id='numeric-mode',hunk=0,addr=2,end=4,style='hex')}))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        text=exact(a,raw,tmp_path)
        assert text.count('dc.w MODE_ACTIVE')==(0 if ambiguous else 1 if manual else 2),text
        assert 'dc.l MODE_ACTIVE' not in text
        assert 'pointer_resolution' not in a.row_for_source_offset(section_index=0,offset=2)
    finally:a.close()


def test_negative_byte_equate_does_not_change_unused_immediate_extension(tmp_path):
    metadata=domain_metadata(width=1,equates=[dict(name='NEGATIVE_ONE',value=-1,group='modes')])
    with candidate_artifact(tmp_path,'move.b #255,(a0)\n rts',[],metadata) as (a,original):
        source=exact(a,original,tmp_path)
        assert '#NEGATIVE_ONE' not in source
