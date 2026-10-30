"""Source-cursor type domains are independent of exact numeric candidates."""
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from amiga_reversing.disasm.effective_metadata import effective_metadata_file


def header_table_artifact(tmp_path, loop=True, count=2, trips=None, setup='', body='',
                          null=False, mixed=False, aliases=False, exposure=False,
                          indexed=False, index_code=None, index_register='d2',
                          reference_records=False, derived=False, index_displacement=0, after_count='',
                          zero_counts=False, null_prefix=False, code_tail='', target_type='program',
                          record_access=None, extra_actions=(), load_via_data=False):
    trips=count if trips is None else trips
    counter='move.w d5,d4'if trips=='unknown'else f'move.w #{trips-1},d4'
    directory=['first'if aliases else f'header_{i}'for i in range(count)]
    if null:directory[-1]='0'
    if mixed:directory[-1]='other_record'
    if derived:directory[-1]='derived_record'
    if null_prefix:directory[0]='0'
    text=(' SECTION code,code\n ORG $1000\n'+(' lea.l again.l,a5\n'if exposure else'')+
          ' lea.l directory(pc),a3\n '+counter+'\n '+setup+'\nagain:\n '+body+
          ('\n '+(index_code or'move.w d4,d2\n lsl.w #2,d2')+
           f'\n movea.l {index_displacement}(a3,{index_register}.w),a0\n'if indexed
           else('\n move.l (a3)+,d2\n movea.l d2,a0\n'if load_via_data else'\n movea.l (a3)+,a0\n'))+
          (record_access if record_access is not None else ' move.w (a0)+,d0\n'+after_count+' move.w (a0),d1\n')+
          (' dbf d4,again\n'if loop else'')+' rts\n'+code_tail+'directory:\n'+''.join(' dc.l '+','.join(directory[i:i+8])+'\n'for i in range(0,count,8))+'first:\n'+
          ''.join(f'header_{i}:dc.w {0 if zero_counts else i+1},{i+2}\n'for i in range(count))+
          ('other_record:dc.w 99,98\n'if mixed else'')+
          ('derived_record:dc.w 99,98\n dc.l 123\n'if derived else''))
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
    start=len(original)-count*8-(4 if mixed else 0)-(8 if derived else 0)
    binary=tmp_path/'input.bin';binary.write_bytes(original)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,entrypoint=0x1000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type=target_type,entry_register_seeds=()))
    actions=[]
    def add(command,parameters):
        kind,payload=target_catalog_manual_payload(command,parameters)
        actions.append((ManualActionKind(kind),payload));return payload
    add('target.custom_struct.add',dict(name='Header',size=4,fields=[
        dict(name='count',type='WORD',offset=0,size=2),dict(name='flags',type='WORD',offset=2,size=2)]))
    if reference_records:
        add('target.custom_struct.add',dict(name='Reference',size=4,fields=[
            dict(name='entry',type='APTR',offset=0,size=4)]))
    if mixed:add('target.custom_struct.add',dict(name='Other',size=4,fields=[
        dict(name='different',type='WORD',offset=0,size=2),dict(name='flags',type='WORD',offset=2,size=2)]))
    if derived:add('target.custom_struct.add',dict(name='ExtendedHeader',size=8,
        base_struct='Header',base_offset=4,fields=[
            dict(name='extra',type='LONG',offset=4,size=4)]))
    declarations=[(start,start+count*4,'directory','custom_struct'if reference_records else'pointer_struct',
                   'Reference'if reference_records else'Header',count),
                  (start+count*4,start+count*8,'headers','custom_struct','Header',count)]
    if mixed:declarations.append((start+count*8,start+count*8+4,'other','custom_struct','Other',1))
    if derived:declarations.append((start+count*8,start+count*8+8,'extended','custom_struct','ExtendedHeader',1))
    for lo,hi,name,kind,type_name,n in declarations:
        payload=add('target.data_block.layout.create',dict(hunk=0,source_start=lo,source_end=hi,
            name=name,role='pointer_table'if kind=='pointer_struct'else'records',
            default_unit='long'if kind=='pointer_struct'else'word'))
        add('target.data_block.element.set',dict(layout_id=payload['data_block_layout']['layout_id'],
            offset=0,width=hi-lo,kind='array',name=name,array_count=n,
            array_stride=8 if type_name=='ExtendedHeader'else 4,
            binding_kind=kind,type_id=type_name))
    for command, parameters in (extra_actions(start) if callable(extra_actions) else extra_actions):
        add(command, parameters)
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    return artifact,original


@pytest.mark.parametrize('indexed', [False, True])
def test_directory_pointee_contract_accepts_validated_prefix_subtype(tmp_path,indexed):
    a,original=header_table_artifact(tmp_path,count=104,indexed=indexed,derived=True)
    try:
        assert typed_fields(a)=={('A0','count'),('A0','flags')}
        section=a.analysis_payload()[0]['sections'][0]
        assert any(v['resolution']=='type_domain'for v in section['address_values'])
        source=a.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    finally:a.close()


@pytest.mark.parametrize('changes', [
    {'body':'move.b #0,(a2)'}, {'body':'move.l #0,directory.l'},
    {'exposure':True}, {'trips':105},
])
def test_prefix_subtype_does_not_override_loop_stability_or_extent(tmp_path,changes):
    a,_=header_table_artifact(tmp_path,count=104,indexed=True,derived=True,**changes)
    try:
        assert not typed_fields(a)
        assert not any(v['resolution']=='type_domain'for v in
                       a.analysis_payload()[0]['sections'][0]['address_values'])
    finally:a.close()


def typed_fields(artifact):
    return {(r['base_register'],r['field_name'])for r in
            artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']}


@pytest.mark.parametrize('index_code,index_register,displacement,expected', [
    ('move.w #99,d2\n asl.w #2,d2', 'd2', 0, 99),
    ('move.w #102,d2\n lsl.w #2,d2', 'd2', 4, 103),
    ('movea.l #396,a5', 'a5', 0, 99),
])
def test_closed_singleton_index_uses_existing_word_value_in_owned_directory(
        tmp_path,index_code,index_register,displacement,expected):
    a,original=header_table_artifact(tmp_path,loop=False,count=104,indexed=True,
        index_code=index_code,index_register=index_register,index_displacement=displacement)
    try:
        assert typed_fields(a)=={('A0','count'),('A0','flags')}
        values=a.analysis_payload()[0]['sections'][0]['address_values']
        singleton=[v for v in values if v['table_origin']['has_origin']]
        assert len(singleton)==1
        assert singleton[0]['resolution']=='resolved'
        assert singleton[0]['table_origin']['entry_index']==expected
        assert singleton[0]['candidate_target_count']==1
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
    finally:a.close()


@pytest.mark.parametrize('index_code,displacement,body', [
    ('move.w #104,d2\n asl.w #2,d2',0,''),
    ('move.w #-4,d2',0,''),
    ('move.w #2,d2',0,''),
    ('move.w #103,d2\n asl.w #2,d2',4,''),
    ('move.w #99,d2\n asl.w #2,d2\n move.w d7,d2',0,''),
    ('move.w #99,d2\n asl.w #2,d2',0,'move.l #0,directory+396.l'),
    ('move.w #99,d2\n asl.w #2,d2',0,'move.b #0,(a2)'),
])
def test_singleton_index_does_not_admit_outside_partial_or_clobbered_eas(
        tmp_path,index_code,displacement,body):
    a,_=header_table_artifact(tmp_path,loop=False,count=104,indexed=True,
        index_code=index_code,index_displacement=displacement,body=body)
    try:
        assert not typed_fields(a)
        assert not any(v['resolution']=='resolved' for v in
                       a.analysis_payload()[0]['sections'][0]['address_values'])
    finally:a.close()


def test_single_selection_does_not_require_or_claim_a_loop_domain(tmp_path):
    a,original=header_table_artifact(tmp_path,loop=False,count=2,indexed=True)
    try:
        assert typed_fields(a)=={('A0','count'),('A0','flags')}
        values=a.analysis_payload()[0]['sections'][0]['address_values']
        assert len(values)==1 and values[0]['resolution']=='resolved'
        assert values[0]['table_origin']['entry_index']==1
        assert not any(v['resolution']=='type_domain' for v in values)
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
    finally:a.close()


def test_incomplete_scalar_proof_does_not_publish_singleton_hint(tmp_path,monkeypatch):
    monkeypatch.setenv('AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS','6')
    a,_=header_table_artifact(tmp_path,loop=False,count=104,indexed=True,
        index_code='move.w #99,d2\n asl.w #2,d2')
    try:
        analysis=a.analysis_payload()[0]
        assert analysis['incomplete_analysis']
        # An exhausted typed pass may retain local discovery/type facts; it
        # must not certify a source selection from a partial scalar solve.
        assert any(w['source_kind_name']=='typed_flow_worklist'and w['capacity']==6
                   for w in analysis['incomplete_analysis'])
        assert not any(v['resolution']=='resolved'for v in analysis['sections'][0]['address_values'])
    finally:a.close()


@pytest.mark.parametrize('count,index_code,index_register', [
    (2, None, 'd2'), (104, None, 'd2'),
    (104, 'move.w d4,d2\n add.w d2,d2\n add.w d2,d2', 'd2'),
    (104, 'move.w d4,d2\n asl.w #2,d2\n movea.w d2,a5', 'a5'),
    (104, 'tst.w d6\n beq.w other\n move.w d4,d2\n lsl.w #2,d2\n bra.w ready\n'
          'other:\n move.w d4,d2\n add.w d2,d2\n add.w d2,d2\nready:', 'd2'),
])
def test_counter_indexed_directory_uses_shared_induction(tmp_path,count,index_code,index_register):
    a,original=header_table_artifact(tmp_path,count=count,indexed=True,
                                   index_code=index_code,index_register=index_register)
    try:
        assert typed_fields(a)=={('A0','count'),('A0','flags')}
        domains=[x for x in a.analysis_payload()[0]['sections'][0]['address_values']
                 if x['resolution']=='type_domain']
        assert len(domains)==1
        assert domains[0]['table_origin']['index_min']==0
        assert domains[0]['table_origin']['index_max']==(count-1)*4
        assert not domains[0]['has_source_expression'] and not domains[0]['candidate_target_count']
        source=a.inline_source_text_with_profile()[0]
        assert f'0(a3,{index_register}.w)' in source or f'$0(a3,{index_register}.w)' in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    finally:a.close()


@pytest.mark.parametrize('changes', [
    {'loop':False,'index_code':'move.w d5,d2\n lsl.w #2,d2'},
    {'trips':3}, {'trips':'unknown'}, {'null':True}, {'mixed':True},
    {'exposure':True}, {'body':'move.w d5,d4'}, {'body':'move.l #0,directory.l'},
    {'body':'move.b #0,(a2)'},
    {'index_code':'move.w d4,d2\n lsl.w #2,d2\n move.w d5,d2'},
    {'index_code':'move.w d4,d2\n lsl.w #15,d2'},
    {'loop':False, 'setup':'lea.l directory+4(pc),a3',
     'index_code':'move.w d5,d2\n andi.w #4,d2'},
    {'index_code':'tst.w d6\n beq.w other\n move.w d4,d2\n lsl.w #2,d2\n bra.w ready\n'
                  'other:\n move.w d4,d2\n lsl.w #3,d2\nready:'},
])
def test_counter_indexed_directory_keeps_refusal_boundaries(tmp_path,changes):
    a,_=header_table_artifact(tmp_path,count=2,indexed=True,**changes)
    try:
        assert not typed_fields(a)
        assert not [x for x in a.analysis_payload()[0]['sections'][0]['address_values']
                    if x['resolution']=='type_domain']
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()


@pytest.mark.parametrize('body', [
    '', 'move.l #0,directory.l',
    'tst.w d6\n beq.w unchanged\n addq.l #4,a2\nunchanged:',
])
@pytest.mark.parametrize('count', [104,148])
def test_indexed_record_fields_are_not_loaded_pointer_values(tmp_path,body,count):
    a,original=header_table_artifact(tmp_path,count=count,trips=104,indexed=True,reference_records=True,
                                   setup='lea.l $200(a6),a2',body=body)
    try:
        assert typed_fields(a)=={('A3','entry')}
        analysis=a.analysis_payload()[0];section=analysis['sections'][0]
        row=next(x for x in section['recovered_platform_typed_accesses']if x['field_name']=='entry')
        domain=row['word_index']
        assert domain['evidence']=='bounded_counter_index'
        assert domain['record_count']==count
        assert 'byte_offsets' not in domain
        assert domain['loop_domain']['iteration_count']==104
        assert domain['loop_domain']['index_first']==412 and domain['loop_domain']['index_stride']==-4
        assert not [x for x in section['address_values']if x['resolution']=='type_domain']
        assert not [x for x in section['recovered_platform_unresolved_typed_accesses']
                    if x['root_struct_name']=='Reference']
        footprint=next(x for x in analysis['memory_layout_records']
                       if x.get('record_kind')=='platform_typed_access'and x.get('field_name')=='entry')
        assert footprint['owner_range_size']==count*4
        assert footprint['indexed_access_envelope']['strided_possible_accesses'] is True
        assert footprint['indexed_access_envelope']['range_size']==104*4
        source=a.inline_source_text_with_profile()[0]
        assert 'Reference_entry(a3,d2.w)' in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    finally:a.close()


@pytest.mark.parametrize('changes', [
    {'trips':105}, {'trips':'unknown'}, {'body':'move.w d5,d4'},
    {'index_code':'move.w d4,d2\n lsl.w #2,d2\n move.w d5,d2'},
    {'index_code':'move.w d4,d2\n lsl.w #1,d2'},
    {'index_code':'move.w d4,d2\n lsl.w #2,d2\n addq.w #1,d2'},
])
def test_record_field_domain_is_not_assumed_from_its_array_extent(tmp_path,changes):
    a,_=header_table_artifact(tmp_path,count=104,indexed=True,reference_records=True,**changes)
    try:
        assert not typed_fields(a)
    finally:a.close()


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


@pytest.mark.parametrize('reference_records', [False,True])
def test_counter_word_sign_extension_keeps_interior_base_offset(tmp_path,reference_records):
    a,original=header_table_artifact(tmp_path,count=104,indexed=True,reference_records=reference_records,
        setup='lea.l directory+412(pc),a3',
        index_code='move.w d4,d2\n lsl.w #2,d2\n subi.w #412,d2')
    try:
        assert typed_fields(a)==({('A3','entry')}if reference_records else{('A0','count'),('A0','flags')})
        if reference_records:
            row=next(r for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
                     if r['field_name']=='entry')
            assert row['word_index']['base_record_index']==103
            assert row['word_index']['loop_domain']['index_first']==0
            assert row['word_index']['loop_domain']['index_stride']==-4
        source=a.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    finally:a.close()


@pytest.mark.parametrize('changes,expected', [({}, True), ({'derived':True}, True),
    ({'null':True}, False), ({'mixed':True}, False),
    ({'body':'move.b #0,(a2)'}, False), ({'exposure':True}, False)])
def test_data_register_table_load_has_canonical_producer_not_orphan_type(tmp_path,changes,expected):
    a,original=header_table_artifact(tmp_path,count=104,load_via_data=True,**changes)
    try:
        payload=a.analysis_payload()[0];section=payload['sections'][0]
        assert bool(typed_fields(a))==expected
        assert not payload['incomplete_analysis']
        if expected:
            assert section['address_values']
            assert any(v['resolution']=='type_domain' for v in section['address_values'])
            assert c_backend.assemble_platform_source_text_with_c_backend(
                'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
    finally:a.close()
