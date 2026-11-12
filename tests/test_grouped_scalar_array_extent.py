"""Scalar display groups retain the canonical array range for native typing."""
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind,append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from tests.test_typed_index_symbol_compensation import exact


@pytest.mark.parametrize('width',[1,2,4])
@pytest.mark.parametrize('grouped',[False,True])
@pytest.mark.parametrize('count,mask,wanted',[(16,7,True),(16,15,True),(32,31,True),(7,7,False),(16,16,False)])
def test_array_extent_is_independent_of_scalar_group(tmp_path,width,grouped,count,mask,wanted):
    suffix={1:'b',2:'w',4:'l'}[width]
    scale='' if width==1 else 'add.w d0,d0\n'*(1 if width==2 else 2)
    code=f' SECTION code,code\n ORG 0\n lea.l cells(pc),a0\n andi.w #{mask},d0\n {scale} move.{suffix} 0(a0,d0.w),d1\n rts\ncells:\n dc.{suffix} '+','.join(['12']*count)+'\n dc.l cells\n'
    encoded=cb.assemble_platform_source_text_with_c_backend('amiga-raw',code)[0]
    raw,offset=encoded[:-4],int.from_bytes(encoded[-4:],'big')
    path=tmp_path/'input.bin';path.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,entrypoint=0,code_start_offset=0,display_path=str(path),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[]
    def add(command,**parameters):
        kind,payload=target_catalog_manual_payload(command,parameters);actions.append((ManualActionKind(kind),payload));return payload
    add('target.custom_struct.add',name='Cell',size=width,fields=[dict(name='mode',type=suffix,offset=0,size=width,**(dict(equate_group='modes')if grouped else{}))])
    add('target.equate.add',name='MODE_ACTIVE',value=12,group='modes')
    layout=add('target.data_block.layout.create',hunk=0,source_start=offset,source_end=len(raw),name='cells',default_unit={1:'byte',2:'word',4:'long'}[width])['data_block_layout']['layout_id']
    add('target.data_block.element.set',layout_id=layout,offset=0,width=len(raw)-offset,kind='array',name='cells',array_count=count,array_stride=width,binding_kind='custom_struct',type_id='Cell')
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path)as metadata:a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        section=a.analysis_payload()[0]['sections'][0]
        refs=[r for r in section['recovered_platform_typed_accesses']if r['field_name']=='mode']
        assert bool(refs)==wanted,section['recovered_platform_unresolved_typed_accesses']
        if refs:assert refs[0]['word_index']['record_count']==count
        text=exact(a,raw,tmp_path)
        if grouped:
            assert text.count(f'dc.{suffix} MODE_ACTIVE')==count,text
            assert a.source_package_payload(64)['source_text']==text
    finally:a.close()
