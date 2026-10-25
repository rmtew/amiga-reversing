"""Indexed MOVEA discovers text pointers without scanning unrelated LONG data."""
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata

@pytest.mark.c_backend
@pytest.mark.parametrize('load',[0,0x1000])
@pytest.mark.parametrize('destination',['a1','d1'])
def test_indexed_text_directory_requires_address_consumer(tmp_path,load,destination):
    asm=f''' SECTION code,code
 ORG ${load:x}
 lea.l directory(pc),a0
 movea.l $0(a0,d0.w),a1
 rts
 directory:
 dc.l first,second,first
 first:
 dc.b $0d,$0a,"FIRST MESSAGE",0
 second:
 dc.b "SECOND MESSAGE",0
'''
    if destination=='d1':asm=asm.replace('movea.l $0(a0,d0.w),a1','move.l $0(a0,d0.w),d1')
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    binary=tmp_path/'source.bin';binary.write_bytes(original)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=load,entrypoint=load,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,
        metadata_path=tmp_path/'target_metadata.json')[2]
    try:
        text=artifact.source_projection_with_profile()[0]
        analysis=artifact.analysis_payload()[0]
    finally:artifact.close()
    items=analysis['analysis_policy']['structured_data_items']
    tables=[i for i in items if i.get('source_pattern')=='indexed_local_pointer_read']
    if destination=='a1':
        assert len(tables)==1, items
        assert tables[0]['size']==12
        assert 'dc.l $' not in text
        assert 'FIRST MESSAGE' in text
    else:assert not tables
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
    assert rebuilt==original

@pytest.mark.c_backend
@pytest.mark.parametrize('fault',['repeated_only','foreign','source_offset','nontext','owned_target'])
def test_text_pointer_scan_refuses_weak_or_conflicting_targets(tmp_path,fault):
    from amiga_reversing.disasm.manual_actions import append_manual_actions,ManualActionKind as Kind
    from amiga_reversing.disasm.effective_metadata import effective_metadata_file
    asm=''' SECTION code,code
 ORG $1000
 lea.l directory(pc),a0
 movea.l $0(a0,d0.w),a1
 rts
 directory:
 dc.l first,second,first
 first:
 dc.b "FIRST MESSAGE",0
 second:
 dc.b "SECOND MESSAGE",0
'''
    raw,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    raw=bytearray(raw);first=int.from_bytes(raw[10:14],'big');second=int.from_bytes(raw[14:18],'big')
    if fault=='repeated_only':raw[14:18]=first.to_bytes(4,'big')
    if fault=='foreign':raw[14:18]=(0xf00000).to_bytes(4,'big')
    if fault=='source_offset':
        for pos in (10,14,18):raw[pos:pos+4]=(int.from_bytes(raw[pos:pos+4],'big')-0x1000).to_bytes(4,'big')
    if fault=='nontext':raw[second-0x1000]=1
    binary=tmp_path/'text.bin';binary.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,entrypoint=0x1000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    if fault=='owned_target':
        append_manual_actions(tmp_path,binary_source=source,actions=[(Kind.CREATE_MANUAL_SEED,{'seed':dict(
            seed_id='opaque',kind='data',mode='required',hunk=0,addr=second-0x1000,end=len(raw),
            name='opaque_record',unit='byte',data_role='raw')})])
    with effective_metadata_file(tmp_path) as metadata:
        art=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
        try:analysis=art.analysis_payload()[0];text=art.source_projection_with_profile()[0]
        finally:art.close()
    assert not [i for i in analysis['analysis_policy']['structured_data_items']
                if i.get('source_pattern')=='indexed_local_pointer_read']
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
    assert rebuilt==raw
