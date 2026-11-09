"""Code-pointer directory discovery must respect the encoded address domain."""
import json
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('mode', ['runtime', 'zero_origin', 'large', 'local_numbers', 'ambiguous', 'duplicate', 'odd', 'unaccepted'])
def test_indexed_code_directory_does_not_treat_small_numbers_as_source_offsets(tmp_path, mode):
    asm = ''' SECTION code,code
 ORG $1000
 lea.l table(pc),a0
 movea.l 0(a0,d0.w),a1
 bsr.w first
 bsr.w second
 rts
 table: dc.l first,second,0
 first: rts
 second: rts
'''
    load=0 if mode=='zero_origin' else 0x1000
    raw, _ = cb.assemble_platform_source_text_with_c_backend('amiga-raw', asm.replace('ORG $1000',f'ORG ${load:x}'))
    assert [int.from_bytes(raw[i:i+4], 'big') for i in (18,22)] == [load+30,load+32]
    if mode == 'local_numbers':
        changed = bytearray(raw)
        for i in (18,22):changed[i:i+4]=(int.from_bytes(raw[i:i+4],'big')-0x1000).to_bytes(4,'big')
        raw=bytes(changed)
    if mode in ('large', 'ambiguous', 'duplicate'):raw += bytes(0x1200)
    if mode in ('odd', 'unaccepted'):
        changed=bytearray(raw);changed[22:26]=(0x101F if mode=='odd' else 0x101A).to_bytes(4,'big');raw=bytes(changed)
    binary=tmp_path/'code.bin';binary.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=load,
        entrypoint=load,code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    metadata=tmp_path/'target_metadata.json'
    if mode in ('ambiguous','duplicate'):
        policy=json.loads(metadata.read_text())
        policy['execution_views']=[dict(source_start=start,source_end=len(raw),base_addr=0x1000,
            runtime_view_use='pointer_target')for start in [0,2 if mode=='ambiguous' else 0]]
        metadata=tmp_path/'pointer-mappings.json';metadata.write_text(json.dumps(policy))
    artifact=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        payload=artifact.analysis_payload()[0]
        assert not payload['incomplete_analysis']
        tables=[i for i in payload['analysis_policy']['structured_data_items'] if i.get('source_pattern')=='indexed_local_pointer_read']
        if mode in ('runtime','zero_origin','large','duplicate'):assert any(i['offset']==18 and i['size']==8 for i in tables)
        else:assert not tables
        text=artifact.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw',text)[0]==raw
        _assert_vasm_bytes(tmp_path,text,raw)
    finally:artifact.close()
