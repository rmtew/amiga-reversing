"""A source-backed BYTE pair exposes a bounded dynamic field, not a pointer promise."""
import pytest

from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('mode',['bounded','out_of_pair','partial_index','lost_pointer'])
@pytest.mark.parametrize('count',[1,6])
@pytest.mark.parametrize('transport',['register','record_cell'])
def test_byte_pair_requires_complete_index_and_base_evidence(tmp_path,mode,count,transport):
    mutation={'partial_index':' move.b d7,d0\n','lost_pointer':' movea.l a4,a3\n'}.get(mode,'')
    mask=3 if mode=='out_of_pair'else 1
    index=f' andi.w #{mask},d0\n'if transport=='register'else f' andi.w #{mask},(a0)\n move.w (a0),d0\n'
    raw,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',f'''
 SECTION code,code
 ORG $1000
{index} lea.l pair+{2*(count-1)}(pc),a3
{mutation} move.b 0(a3,d0.w),d1
 rts
pair: dc.b {','.join(['5','6']*count)}
''')
    binary=tmp_path/'input.bin';binary.write_bytes(raw);start=len(raw)-2*count
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,entrypoint=0x1000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[]
    def add(command,params):
        kind,payload=target_catalog_manual_payload(command,params)
        actions.append((ManualActionKind(kind),payload));return payload
    add('target.custom_struct.add',dict(name='ColourPair',size=2,fields=[
        dict(name='phase_colours',type='UBYTE',offset=0,size=2)]))
    if transport=='record_cell':
        add('target.custom_struct.add',dict(name='Counter',size=2,fields=[
            dict(name='phase',type='WORD',offset=0,size=2)]))
        add('target.code.register_seed.add',dict(hunk=0,addr=0,register='A0',struct_name='Counter'))
    layout=add('target.data_block.layout.create',dict(hunk=0,source_start=start,source_end=len(raw),
        name='colour_pair',role='colour choices',default_unit='byte'))['data_block_layout']['layout_id']
    add('target.data_block.element.set',dict(layout_id=layout,offset=0,width=2*count,kind='array',
        name='colour_pair',array_count=count,array_stride=2,binding_kind='custom_struct',type_id='ColourPair'))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path)as metadata:
        a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        payload=a.analysis_payload()[0];s=payload['sections'][0]
        fields=[r for r in s['recovered_platform_typed_accesses']if r['root_struct_name']=='ColourPair']
        if mode=='bounded':
            assert len(fields)==1 and fields[0]['field_name']=='phase_colours'
        else:
            assert not fields
        assert not payload['incomplete_analysis']
        text=a.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw',text)[0]==raw
        _assert_vasm_bytes(tmp_path,text,raw)
    finally:a.close()
