"""Numeric BYTE lookup extents come from converged index bits, not contents."""
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from amiga_reversing.disasm.manual_actions import append_manual_actions,ManualActionKind as Kind
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('case',[
    'direct','call','copies','scaled','two_readers','branch_bases','displacement',
    'unknown_index','unknown_call','unknown_base','bypassed_bound','long_index',
    'negative','partial_write','opaque_owner','partial_owner','code_overlap','join_bounds','exact_index',
])
def test_flow_bounded_byte_lookup_and_refusals(tmp_path,case):
    prefix=' lea.l choices(pc),a1\n andi.w #7,d0'
    read='read: move.b 0(a1,d0.w),d2'
    after=''
    if case=='call':prefix=' lea.l choices(pc),a1\n bsr.w helper\n andi.w #7,d0'
    if case=='copies':prefix+='\n move.l a1,d3\n movea.l d3,a2\n move.w d0,d4';read='read: move.b 0(a2,d4.w),d2'
    if case=='scaled':prefix=' lea.l choices(pc),a1\n andi.w #3,d0\n add.w d0,d0'
    if case=='two_readers':after=' andi.w #3,d4\n move.b 0(a1,d4.w),d3'
    if case=='branch_bases':prefix=' tst.w d1\n beq.w other\n lea.l choices(pc),a1\n bra.w join\nother: lea.l second(pc),a1\njoin: andi.w #7,d0'
    if case=='displacement':prefix=prefix.replace('choices(pc)','choices-2(pc)');read=read.replace('0(a1','2(a1')
    if case=='unknown_index':prefix=' lea.l choices(pc),a1'
    if case=='unknown_call':prefix+='\n jsr (a3)'
    if case=='unknown_base':prefix+='\n movea.l d7,a1'
    if case=='bypassed_bound':prefix=' lea.l choices(pc),a1\n tst.w d1\n beq.w read\n andi.w #7,d0'
    if case=='join_bounds':prefix=' lea.l choices(pc),a1\n tst.w d1\n beq.w other\n andi.w #7,d0\n bra.w read\nother: andi.w #3,d0'
    if case=='exact_index':prefix=' lea.l choices(pc),a1\n moveq #3,d0'
    if case=='long_index':read=read.replace('d0.w','d0.l')
    if case=='negative':prefix=prefix.replace('#7','#$8007')
    if case=='partial_write':prefix+='\n move.b d7,d0'
    if case=='code_overlap':after=' bsr.w choices'
    data=' dc.b 13,18,21,31,32,33,34,45'
    if case=='code_overlap':data=' rts\n dc.b 21,31,32,33,34,45'
    asm=' SECTION code,code\n ORG $1000\n'+prefix+'\n'+read+'\n'+after+'\n rts\nhelper: move.l #$12345678,d0\n rts\nchoices:'+data+'\nsecond: dc.b 1,9,15,39,13,18,21,31\n'
    raw,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    symbols,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm+' dc.l choices,second,read\n')
    assert symbols[:-12]==raw
    table,second,reader=[int.from_bytes(symbols[i:i+4],'big')-4096 for i in range(len(raw),len(raw)+12,4)]
    path=tmp_path/'byte.bin';path.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=4096,entrypoint=4096,code_start_offset=0,display_path=str(path),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    if case in('opaque_owner','partial_owner'):
        append_manual_actions(tmp_path,binary_source=source,actions=[(Kind.CREATE_MANUAL_SEED,{'seed':dict(
            seed_id='opaque',kind='data',mode='required',hunk=0,addr=table+(4 if case=='partial_owner'else 0),end=table+8,name='opaque_bytes',unit='byte')})])
    with effective_metadata_file(tmp_path)as metadata:
        a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        items=[i for i in p['analysis_policy']['structured_data_items']if i.get('source_pattern')=='indexed_local_scalar_read'and i.get('offset')in(table,second)]
        positive=case in('direct','call','copies','scaled','two_readers','branch_bases','displacement','join_bounds','exact_index')
        if positive:
            assert {i['offset']for i in items}==({table,second}if case=='branch_bases'else{table})
            for item in items:
                assert item['size']==(7 if case=='scaled'else 4 if case=='exact_index'else 8)
                descriptor=next(d for d in p['sections'][0]['table_descriptors']if d['start_offset']==item['offset'])
                assert descriptor['entry_count_proof']=='index_value_bits'
                assert descriptor['table_kind']=='scalar'
            observed=[c for c in p['sections'][0]['address_value_consumers']if c['kind']=='indexed_base'and c['offset']==reader]
            assert len(observed)==1 and observed[0]['index_word_known_bits']['mask']&0x8000
            readers=[c for c in p['sections'][0]['table_consumers']if c['table_start_offset']==table]
            assert len(readers)==(2 if case=='two_readers'else 1)
        else:assert not items
        text=a.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw',text)[0]==raw
        _assert_vasm_bytes(tmp_path,text,raw)
    finally:a.close()
