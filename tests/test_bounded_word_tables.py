"""Aligned WORD prefixes reuse the shared byte-offset domain and ownership."""
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from amiga_reversing.disasm.manual_actions import append_manual_actions,ManualActionKind as Kind
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('case',['direct','scaled','call','copies','memory_destination','two_readers',
    'exact_index','unaligned','negative','long_index','unknown_call','partial_write','opaque_owner','owned'])
def test_word_geometry_uses_aligned_byte_offsets_and_conservative_owners(tmp_path,case):
    prefix=' lea.l choices(pc),a1\n andi.w #14,d0';read='read: move.w 0(a1,d0.w),d2';after=''
    if case=='scaled':prefix=' lea.l choices(pc),a1\n andi.w #7,d0\n add.w d0,d0'
    if case=='call':prefix=' lea.l choices(pc),a1\n bsr.w helper\n andi.w #14,d0'
    if case=='copies':prefix+='\n move.w d0,d4\n move.l a1,d3\n movea.l d3,a2';read='read: move.w 0(a2,d4.w),d2'
    if case=='memory_destination':read='read: move.w 0(a1,d0.w),22(a4)'
    if case=='two_readers':after=' andi.w #6,d4\n move.w 0(a1,d4.w),d3'
    if case=='exact_index':prefix=' lea.l choices(pc),a1\n moveq #6,d0'
    if case=='unaligned':prefix=prefix.replace('#14','#15')
    if case=='negative':prefix=prefix.replace('#14','#$800E')
    if case=='long_index':read=read.replace('d0.w','d0.l')
    if case=='unknown_call':prefix+='\n jsr (a3)'
    if case=='partial_write':prefix+='\n move.b d7,d0'
    asm=' SECTION code,code\n ORG $1000\n'+prefix+'\n'+read+'\n'+after+'''\n rts
helper: move.l #$12345678,d0
 rts
choices: dc.w 32,-25,15,-17,15,-30,30,-25
'''
    raw,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    symbols,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm+' dc.l choices,read\n');assert symbols[:-8]==raw
    table,reader=[int.from_bytes(symbols[i:i+4],'big')-4096 for i in range(len(raw),len(raw)+8,4)]
    path=tmp_path/'words.bin';path.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=4096,entrypoint=4096,code_start_offset=0,display_path=str(path),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    if case in('opaque_owner','owned'):
        append_manual_actions(tmp_path,binary_source=source,actions=[(Kind.CREATE_MANUAL_SEED,{'seed':dict(
            seed_id='owner',kind='data',mode='required',hunk=0,addr=table,end=table+16,name='owned_values',
            unit='word'if case=='owned'else'byte',data_role='lookup_table'if case=='owned'else'')})])
    with effective_metadata_file(tmp_path)as metadata:
        a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        p=a.analysis_payload()[0];assert not p['incomplete_analysis'];section=p['sections'][0]
        items=[i for i in p['analysis_policy']['structured_data_items']if i['offset']==table and i.get('source_pattern')=='indexed_local_scalar_read']
        positive=case in('direct','scaled','call','copies','memory_destination','two_readers','exact_index')
        if positive:
            assert len(items)==1 and items[0]['size']==(8 if case=='exact_index'else 16)
            descriptor=next(d for d in section['table_descriptors']if d['start_offset']==table)
            assert descriptor['entry_size']==2 and descriptor['entry_count']==(4 if case=='exact_index'else 8)
            assert descriptor['table_kind']=='scalar'and descriptor['entry_count_proof']=='index_value_bits'
        else:assert not items
        consumers=[c for c in section['table_consumers']if c['table_start_offset']==table]
        assert len(consumers)==(2 if case=='two_readers'else 1 if positive or case=='owned'else 0)
        text=a.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw',text)[0]==raw
        _assert_vasm_bytes(tmp_path,text,raw)
    finally:a.close()
