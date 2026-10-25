"""Referenced control-prefixed text shares native ownership and code guards."""
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata

@pytest.mark.c_backend
@pytest.mark.parametrize('mode',['referenced','unreferenced','bad_control','unterminated','owned'])
def test_control_prefix_requires_boundary_and_clear_nul_span(tmp_path,mode):
    from amiga_reversing.disasm.manual_actions import append_manual_actions,ManualActionKind as Kind
    from amiga_reversing.disasm.effective_metadata import effective_metadata_file
    prefix=' lea.l message(pc),a1\n' if mode!='unreferenced' else ' nop\n nop\n'
    data=('$01' if mode=='bad_control' else '$0d,$0a')+',"RATING, PLEASE",'+('$01' if mode=='unterminated' else '0')
    asm=' SECTION code,code\n ORG $1000\n'+prefix+' rts\nmessage:\n dc.b '+data+'\n'
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    binary=tmp_path/'text.bin';binary.write_bytes(original)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,entrypoint=0x1000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    if mode=='owned':
        append_manual_actions(tmp_path,binary_source=source,actions=[(Kind.CREATE_MANUAL_SEED,{'seed':dict(
            seed_id='owned',kind='data',mode='required',hunk=0,addr=6,end=len(original),
            name='opaque_record',data_role='raw',unit='byte')})])
    with effective_metadata_file(tmp_path) as metadata:
        art=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
        try: analysis=art.analysis_payload()[0];text=art.source_projection_with_profile()[0]
        finally: art.close()
    controls=[i for i in analysis['analysis_policy']['structured_data_items']
              if i.get('source_pattern')=='control_string_stream']
    if mode=='referenced':
        assert len(controls)==1
        assert controls[0]['offset']==6 and controls[0]['size']==len(original)-6
    else:assert not controls
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
    assert rebuilt==original
