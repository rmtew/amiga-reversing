"""Source-cursor type domains are independent of exact numeric candidates."""
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from amiga_reversing.disasm.effective_metadata import effective_metadata_file


def header_table_artifact(tmp_path, loop=True, count=2, trips=None, setup='', body='',
                          null=False, mixed=False, aliases=False, exposure=False):
    trips=count if trips is None else trips
    counter='move.w d5,d4'if trips=='unknown'else f'move.w #{trips-1},d4'
    directory=['first'if aliases else f'header_{i}'for i in range(count)]
    if null:directory[-1]='0'
    if mixed:directory[-1]='other_record'
    text=(' SECTION code,code\n ORG $1000\n'+(' lea.l again.l,a5\n'if exposure else'')+
          ' lea.l directory(pc),a3\n '+counter+'\n '+setup+'\nagain:\n '+body+
          '\n movea.l (a3)+,a0\n move.w (a0)+,d0\n move.w (a0),d1\n'+
          (' dbf d4,again\n'if loop else'')+' rts\ndirectory:\n'+''.join(' dc.l '+','.join(directory[i:i+8])+'\n'for i in range(0,count,8))+'first:\n'+
          ''.join(f'header_{i}:dc.w {i+1},{i+2}\n'for i in range(count))+
          ('other_record:dc.w 99,98\n'if mixed else''))
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
    start=len(original)-count*8-(4 if mixed else 0)
    binary=tmp_path/'input.bin';binary.write_bytes(original)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,entrypoint=0x1000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[]
    def add(command,parameters):
        kind,payload=target_catalog_manual_payload(command,parameters)
        actions.append((ManualActionKind(kind),payload));return payload
    add('target.custom_struct.add',dict(name='Header',size=4,fields=[
        dict(name='count',type='WORD',offset=0,size=2),dict(name='flags',type='WORD',offset=2,size=2)]))
    if mixed:add('target.custom_struct.add',dict(name='Other',size=4,fields=[
        dict(name='different',type='WORD',offset=0,size=2),dict(name='flags',type='WORD',offset=2,size=2)]))
    declarations=[(start,start+count*4,'directory','pointer_struct','Header',count),
                  (start+count*4,start+count*8,'headers','custom_struct','Header',count)]
    if mixed:declarations.append((start+count*8,start+count*8+4,'other','custom_struct','Other',1))
    for lo,hi,name,kind,type_name,n in declarations:
        payload=add('target.data_block.layout.create',dict(hunk=0,source_start=lo,source_end=hi,
            name=name,role='pointer_table'if kind=='pointer_struct'else'records',
            default_unit='long'if kind=='pointer_struct'else'word'))
        add('target.data_block.element.set',dict(layout_id=payload['data_block_layout']['layout_id'],
            offset=0,width=hi-lo,kind='array',name=name,array_count=n,array_stride=4,
            binding_kind=kind,type_id=type_name))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    return artifact,original


def typed_fields(artifact):
    return {(r['base_register'],r['field_name'])for r in
            artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']}


@pytest.mark.parametrize('loop,count',[(False,2),(True,2),(True,104)])
def test_entry_load_keeps_header_type_without_inventing_numeric_targets(tmp_path,loop,count):
    a,original=header_table_artifact(tmp_path,loop=loop,count=count)
    try:
        analysis=a.analysis_payload()[0];section=analysis['sections'][0]
        assert typed_fields(a)=={('A0','count'),('A0','flags')}
        values=section['address_values']
        if loop:
            domains=[v for v in values if v['resolution']=='type_domain']
            assert len(domains)==1
            value=domains[0]
            assert value['table_origin']['selection_kind']=='bounded_source_cursor'
            assert value['table_origin']['index_min']==0 and value['table_origin']['index_max']==(count-1)*4
            assert value['candidate_target_count']==0 and not value['has_source_expression']
            assert value['render_outcome']=='non_source'and value['terminal_state']=='type_domain'
        source=a.inline_source_text_with_profile()[0]
        assert '\tmovea.l (a3)+,a0'in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
        assert not analysis['incomplete_analysis']
    finally:a.close()


@pytest.mark.parametrize('options',[
    dict(trips=3),dict(trips='unknown'),dict(body='addq.l #2,a3'),
    dict(body='move.b #0,(a5)'),dict(body='clr.l directory.l'),
    dict(body='jsr $2000.l'),dict(null=True),dict(mixed=True),dict(exposure=True),
    dict(body='tst.w d7\n beq.w keep\n addq.l #4,a3\nkeep:'),
])
def test_unproved_or_incompatible_source_domains_do_not_promote_types(tmp_path,options):
    a,_=header_table_artifact(tmp_path,**options)
    try:
        assert not typed_fields(a)
        section=a.analysis_payload()[0]['sections'][0]
        assert not[v for v in section['address_values']if v['resolution']=='type_domain']
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()


def test_duplicate_pointer_entries_are_valid_aliases(tmp_path):
    a,_=header_table_artifact(tmp_path,aliases=True)
    try:assert typed_fields(a)=={('A0','count'),('A0','flags')}
    finally:a.close()


@pytest.mark.parametrize('setup,body',[
    ('','move.w #0,header_0.l'),
    ('lea.l header_0(pc),a2','move.w #0,(a2)'),
    ('lea.l header_0(pc),a2','move.w #0,(a2)+'),
    ('lea.l $70000.l,a6','move.w #0,$100(a6)'),
    ('','moveq #1,d6\ninner:\n nop\n dbf d6,inner'),
    ('lea.l header_0(pc),a0',''),
    ('','tst.w d7\n beq.w unchanged\n addq.l #4,a3\n subq.l #4,a3\nunchanged:'),
])
def test_disjoint_cpu_writes_and_nested_retry_preserve_the_domain(tmp_path,setup,body):
    a,original=header_table_artifact(tmp_path,setup=setup,body=body)
    try:
        expected={('A0','count'),('A0','flags')}
        # A fixed A2 additionally has one valid named store. The advancing
        # writer crosses count/flags, so it cannot claim one fixed field.
        if setup=='lea.l header_0(pc),a2'and body=='move.w #0,(a2)':expected.add(('A2','count'))
        assert typed_fields(a)==expected
        source=a.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()


@pytest.mark.parametrize('setup,body',[
    ('lea.l directory(pc),a2','move.w #0,(a2)'),
    ('lea.l header_0(pc),a2','movea.l (a3),a2\n move.w #0,(a2)'),
    ('lea.l directory-2(pc),a2','move.w #0,(a2)+'),
    # LEA(4)+MOVE.W immediate(4): the loop starts at runtime $1008.
    ('','clr.l $FF001008.l'),
    ('','clr.w again.l'),
    ('','moveq #1,d6\ninner:\n addq.l #4,a3\n dbf d6,inner'),
    ('','dbf d4,again'),
    ('','movea.l d4,a2\n adda.l #$1000,a2\n move.w #0,(a2)'),
])
def test_write_aliases_code_changes_and_unproved_loop_dependencies_refuse(tmp_path,setup,body):
    a,_=header_table_artifact(tmp_path,setup=setup,body=body)
    try:
        assert not typed_fields(a)
        assert not[v for v in a.analysis_payload()[0]['sections'][0]['address_values']if v['resolution']=='type_domain']
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()


@pytest.mark.parametrize('known_frame',[False,True])
def test_source_loop_requires_a_disjoint_physical_write_frame(tmp_path,known_frame):
    a,_=header_table_artifact(tmp_path,count=104,
        setup='lea.l $70000.l,a6'if known_frame else'',body='move.w #0,$174(a6)')
    try:
        assert typed_fields(a)==({('A0','count'),('A0','flags')}if known_frame else set())
        domains=[v for v in a.analysis_payload()[0]['sections'][0]['address_values']
                 if v['resolution']=='type_domain']
        assert bool(domains)==known_frame
    finally:a.close()
