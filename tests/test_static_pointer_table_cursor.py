"""Source-backed homogeneous directories survive real entry reads and loops."""
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from amiga_reversing.disasm.effective_metadata import effective_metadata_file


def header_table_artifact(tmp_path, loop, *, unknown_count=False, invalid_first=False):
    text = (' SECTION code,code\n ORG $1000\n lea.l directory(pc),a3\n moveq #1,d4\n'
        'again:\n movea.l (a3)+,a0\n move.w (a0)+,d0\n move.w (a0),d1\n'
        + (' dbf d4,again\n' if loop else '')
        + ' rts\ndirectory:\n dc.l first,second\nfirst:dc.w 1,2\nsecond:dc.w 3,4\n')
    if unknown_count:
        text=text.replace('moveq #1,d4','move.w d2,d4')
    if invalid_first:
        text=text.replace('dc.l first,second','dc.l $DEADCAFE,second')
    original, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)
    start = len(original)-16
    binary = tmp_path/'input.bin';binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,entrypoint=0x1000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions = []
    def add(command, parameters):
        kind,payload=target_catalog_manual_payload(command,parameters)
        actions.append((ManualActionKind(kind),payload));return payload
    add('target.custom_struct.add',dict(name='Header',size=4,fields=[
        dict(name='count',type='WORD',offset=0,size=2),dict(name='flags',type='WORD',offset=2,size=2)]))
    for lo,hi,name,kind in [(start,start+8,'directory','pointer_struct'),
                           (start+8,start+16,'headers','custom_struct')]:
        payload=add('target.data_block.layout.create',dict(hunk=0,source_start=lo,source_end=hi,
            name=name,role='pointer_table' if kind=='pointer_struct' else 'records',
            default_unit='long' if kind=='pointer_struct' else 'word'))
        add('target.data_block.element.set',dict(layout_id=payload['data_block_layout']['layout_id'],
            offset=0,width=hi-lo,kind='array',name=name,array_count=2,array_stride=4,
            binding_kind=kind,type_id='Header'))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    return artifact,original


def test_single_entry_load_keeps_header_type_without_inventing_inline_target_operand(tmp_path):
    artifact,original=header_table_artifact(tmp_path,False)
    try:
        analysis=artifact.analysis_payload()[0]
        accesses=analysis['sections'][0]['recovered_platform_typed_accesses']
        assert {(r['base_register'],r['field_name']) for r in accesses} == {('A0','count'),('A0','flags')}
        value, = analysis['sections'][0]['address_values']
        assert value['resolution'] == 'resolved' and value['candidate_target_count'] == 1
        assert value['target_offset'] == len(original)-8
        assert value['render_outcome'] == 'non_source' and not value['has_source_expression']
        assert value['table_origin']['entry_index'] == 0
        source=artifact.inline_source_text_with_profile()[0]
        assert '\tmovea.l (a3)+,a0' in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
        assert not analysis['incomplete_analysis']
    finally:
        artifact.close()


@pytest.mark.parametrize('invalid_first',[False,True])
def test_missing_position_or_unowned_target_cannot_gain_a_typed_singleton(tmp_path,invalid_first):
    artifact,original=header_table_artifact(tmp_path,not invalid_first,
        unknown_count=not invalid_first,invalid_first=invalid_first)
    try:
        section=artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        source=artifact.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    finally:
        artifact.close()
