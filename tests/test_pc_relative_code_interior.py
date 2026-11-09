"""PC addresses into accepted instructions need a shared-assembler expression."""
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('load',[0,0x1000])
@pytest.mark.parametrize('addend',[2,3,4,5])
def test_pc_address_into_extension_uses_enclosing_instruction_symbol(tmp_path,load,addend):
    asm=f''' SECTION code,code
 ORG ${load:x}
 bsr.w body
 lea.l body+{addend}(pc),a0
 rts
 body: move.l #$11223344,d0
 rts
'''
    raw,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    path=tmp_path/'interior.bin';path.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=load,entrypoint=load,code_start_offset=0,display_path=str(path),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=tmp_path/'target_metadata.json')[2]
    try:
        text=a.inline_source_text_with_profile()[0]
        assert f'+{addend}(pc)' in text
        assert '\tmove.l #$11223344,d0\n' in text
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw',text)[0]==raw
        _assert_vasm_bytes(tmp_path,text,raw)
    finally:a.close()
