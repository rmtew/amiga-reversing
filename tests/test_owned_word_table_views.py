"""Converged scalar consumers may view a complete, clean WORD owner.

The original owner and policy survive; opaque bytes, composites and relative
control tables must not become scalar tables through this observation.
"""
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from amiga_reversing.disasm.manual_actions import append_manual_actions,ManualActionKind as Kind
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('case',[
    'word_owner','two_readers','plausible_offsets','opaque_byte','partial_owner',
    'short_owner','long_owner','interior_label','unaligned_base','unknown_upper',
    'unaligned_index','byte_reader','relative_dispatch','composite_owner',
])
def test_complete_owned_word_view_and_refusals(tmp_path,case):
    prefix='lea.l table(pc),a0\n moveq.l #0,d0\n move.b (a1)+,d0\n add.w d0,d0\n'
    after='';read='read: move.w 0(a0,d0.w),d2\n rts\n'
    values=[str((i*29+7)&65535)for i in range(256)]
    if case=='two_readers':read=read.replace(' rts',' move.w 0(a0,d0.w),d3\n rts')
    if case=='plausible_offsets':values=['512']*256
    if case=='relative_dispatch':
        values=['512']*256;read=read.replace(' rts',' jmp table(pc,d2.w)')
    if case=='unknown_upper':prefix=prefix.replace(' moveq.l #0,d0\n','')
    if case=='unaligned_index':prefix=prefix.replace(' add.w d0,d0\n','')
    if case=='byte_reader':read=read.replace('move.w','move.b')
    if case=='interior_label':prefix='lea.l table+2(pc),a3\n'+prefix
    if case=='unaligned_base':prefix=prefix.replace('table(pc)','table+1(pc)')
    data=''.join(' dc.w '+','.join(values[i:i+16])+'\n'for i in range(0,256,16))
    asm=' SECTION code,code\n ORG $1000\n'+prefix+read+'table:\n'+data+'endtable: rts\n'
    raw,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    syms=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm+' dc.l table,read\n')[0]
    assert syms[:-8]==raw
    table,reader=[int.from_bytes(syms[i:i+4],'big')-4096 for i in range(len(raw),len(raw)+8,4)]
    binary=tmp_path/'table.bin';binary.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=4096,entrypoint=4096,code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    start=table+(2 if case=='partial_owner'else 0)
    end=table+(510 if case=='short_owner'else 514 if case=='long_owner'else 512)
    if case=='composite_owner':
        from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
        actions=[]
        def add(command,**parameters):
            kind,payload=target_catalog_manual_payload(command,parameters)
            actions.append((Kind(kind),payload));return payload
        add('target.custom_struct.add',name='Pair',size=4,fields=[
            dict(name='first',type='WORD',offset=0,size=2),dict(name='second',type='WORD',offset=2,size=2)])
        layout=add('target.data_block.layout.create',hunk=0,source_start=start,source_end=end,
            name='pairs',default_unit='word')['data_block_layout']['layout_id']
        add('target.data_block.element.set',layout_id=layout,offset=0,width=end-start,kind='array',
            name='pairs',array_count=128,array_stride=4,binding_kind='custom_struct',type_id='Pair')
        append_manual_actions(tmp_path,binary_source=source,actions=actions)
    else:
        append_manual_actions(tmp_path,binary_source=source,actions=[(Kind.CREATE_MANUAL_SEED,{'seed':dict(
            seed_id='owner',kind='data',mode='required',hunk=0,addr=start,end=end,name='owned_values',
            unit='byte'if case=='opaque_byte'else'word')})])
    with effective_metadata_file(tmp_path)as metadata:
        a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        p=a.analysis_payload()[0];assert not p['incomplete_analysis'];section=p['sections'][0]
        tables=[x for x in section['table_descriptors']if x['start_offset']==table and x['table_kind']=='scalar']
        positive=case in ['word_owner','two_readers','plausible_offsets']
        if positive:
            descriptor,=tables
            assert descriptor['entry_count']==256 and descriptor['entry_size']==2
            assert descriptor['entry_count_proof']=='index_value_bits'
            assert descriptor['target_offset'] is None and descriptor['target_section_index'] is None
            uses=[x for x in section['table_consumers']if x['table_start_offset']==table]
            assert len(uses)==(2 if case=='two_readers'else 1)
            assert reader in [x['consumer_offset']for x in uses]
            owner,=[x for x in section['range_ownerships']if x['start_offset']==start and x['end_offset']==end]
            assert owner['kind_name']=='structured_data' and owner['status_name']=='accepted'
            assert not[x for x in p['analysis_policy']['structured_data_items']if x['offset']==table and
                       x.get('source_pattern')=='indexed_local_scalar_read']
        else:assert not tables
        rendered=a.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw',rendered)[0]==raw
        _assert_vasm_bytes(tmp_path,rendered,raw)
    finally:a.close()
