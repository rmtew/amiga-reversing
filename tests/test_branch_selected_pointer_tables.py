"""Branch-selected indexed table bases reuse converged native pointer values."""
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('case',['distinct','backward','known_call','displacement','outside_base','negative_displacement','same','copies','one_bad_table','unknown_register','unknown_entry','partial_copy','unknown_call','foreign','overflow'])
def test_branch_selected_pointer_directories_and_conservative_joins(tmp_path,case):
    first='lea.l first_table(pc),a0';second='lea.l second_table(pc),a0'
    if case=='same':second=first
    if case=='known_call':
        first+='\n bsr.w preserving';second+='\n bsr.w preserving'
    if case=='displacement':
        first='lea.l first_table-4(pc),a0';second='lea.l second_table-4(pc),a0'
    if case=='outside_base':
        first='lea.l first_table-126.l,a0';second='lea.l second_table-126.l,a0'
    if case=='negative_displacement':
        first='lea.l first_table+128.l,a0';second='lea.l second_table+128.l,a0'
    if case=='copies':
        first='lea.l first_table(pc),a2\n move.l a2,d2\n movea.l d2,a0'
        second='lea.l second_table(pc),a3\n movea.l a3,a0'
    if case=='unknown_entry':second='nop'
    if case=='unknown_register':second+='\n movea.l d7,a0'
    if case=='partial_copy':second+='\n move.l a0,d2\n move.w d7,d2\n movea.l d2,a0'
    if case=='unknown_call':second+='\n jsr (a2)'
    if case=='foreign':second='lea.l $900000.l,a0'
    prefix=f''' tst.w d1
 beq.w alternate
 {first}
 bra.w shared
 alternate: {second}
'''
    if case=='overflow':
        prefix=''
        for i in range(4):prefix+=f' cmp.w #{i+1},d1\n beq.w arm{i}\n'
        prefix+=' lea.l fifth_table(pc),a0\n bra.w shared\n'
        for i,label in enumerate(['first_table','second_table','third_table','fourth_table']):
            prefix+=f' arm{i}: lea.l {label}(pc),a0\n bra.w shared\n'
    asm=' SECTION code,code\n ORG $1000\n'+prefix+''' shared: nop
 move.w d6,d7
 movea.l 0(a0,d0.w),a1
 rts
 first_table: dc.l alpha,beta,0
 second_table: dc.l gamma,delta,0
 third_table: dc.l alpha,gamma,0
 fourth_table: dc.l beta,delta,0
 fifth_table: dc.l alpha,delta,0
 alpha: dc.b "ALPHA MESSAGE",0
 beta: dc.b "BETA MESSAGE",0
 gamma: dc.b "GAMMA MESSAGE",0
 delta: dc.b "DELTA MESSAGE",0
'''
    if case=='backward':
        body=asm[asm.index(' shared:'):asm.index(' first_table:')]
        asm=asm[:asm.index(' tst.w d1')]+' bra.w choose\n'+body+' choose:\n'+prefix+' bra.w shared\n'+asm[asm.index(' first_table:'):]
    if case=='known_call':asm=asm.replace(' first_table:', ' preserving: rts\n first_table:',1)
    if case=='displacement':asm=asm.replace('movea.l 0(a0,d0.w),a1','movea.l 4(a0,d0.w),a1')
    if case=='outside_base':asm=asm.replace('movea.l 0(a0,d0.w),a1','movea.l 126(a0,d0.w),a1')
    if case=='negative_displacement':asm=asm.replace('movea.l 0(a0,d0.w),a1','movea.l -128(a0,d0.w),a1')
    if case=='one_bad_table':asm=asm.replace('second_table: dc.l gamma,delta,0','second_table: dc.l $11223344,$55667788,0')
    raw,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    with_symbols,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm+' dc.l first_table,second_table,shared\n')
    assert with_symbols[:-12]==raw
    first_offset,second_offset,shared=[int.from_bytes(with_symbols[i:i+4],'big')-4096 for i in range(len(raw),len(raw)+12,4)]
    path=tmp_path/'branch.bin';path.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=4096,entrypoint=4096,code_start_offset=0,display_path=str(path),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=tmp_path/'target_metadata.json')[2]
    try:
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        tables={i['offset'] for i in p['analysis_policy']['structured_data_items'] if i.get('source_pattern')=='indexed_local_pointer_read'}
        if case in ('distinct','backward','known_call','displacement','outside_base','negative_displacement','copies'):assert {first_offset,second_offset}<=tables
        elif case in ('same','one_bad_table'):assert first_offset in tables
        else:assert not tables
        expressions=[e for e in p['sections'][0]['address_expressions'] if e['consumer_offset']==shared+4]
        if case=='same':assert len(expressions)==1 and expressions[0]['base_offset']==first_offset
        else:assert not expressions
        observed=[c for c in p['sections'][0]['address_value_consumers']
                  if c['kind']=='indexed_base' and c['offset']==shared+4]
        assert len(observed)==1
        if case in ('unknown_register','unknown_entry','partial_copy','unknown_call','foreign'):
            assert observed[0]['address_value_id']==0
        else:
            value=next(v for v in p['sections'][0]['address_values'] if v['id']==observed[0]['address_value_id'])
            if case=='overflow':assert value['resolution']=='candidate_overflow'
            else:assert value['candidate_target_count']==(1 if case=='same' else 2)
        # Stored prefix recovery does not imply any mask/compare/loop bound.
        for c in p['sections'][0]['table_consumers']:
            if c.get('consumer_offset')==shared+4:
                assert c['index_mask_domain']is None
                assert c['index_compare_domain']is None
                assert c['index_loop_domain']is None
        text=a.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw',text)[0]==raw
        _assert_vasm_bytes(tmp_path,text,raw)
    finally:a.close()
