"""Interior table annotations must survive specialized pointer serialization."""
import subprocess
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind,append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from amiga_reversing.disasm.project_paths import PROJECT_ROOT

@pytest.mark.c_backend
@pytest.mark.parametrize('explicit',[False,True])
def test_pointer_table_interior_comments_render_once_in_order(tmp_path,explicit):
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
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    binary=tmp_path/'table.bin';binary.write_bytes(original)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,entrypoint=0x1000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[]
    if explicit:actions.append((Kind.CREATE_MANUAL_SEED,{'seed':dict(seed_id='table',kind='data',
        mode='required',hunk=0,addr=10,end=22,name='text_directory',unit='long',data_role='pointer_table')}))
    for i in range(3):actions.append((Kind.CREATE_MANUAL_COMMENT,{'comment':dict(
        comment_id=f'entry-{i}',hunk=0,addr=10+4*i,text=f'Independent directory entry {i}.')}))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path)as metadata:
        art=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
        try:text=art.source_projection_with_profile()[0]
        finally:art.close()
    positions=[]
    for i in range(3):
        note=f'Independent directory entry {i}.'
        assert text.count(note)==1,text
        positions.append(text.index(note))
    assert positions==sorted(positions)
    for i in range(2):assert '\tdc.l 'in text[positions[i]:positions[i+1]]
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
    assert rebuilt==original
    path=tmp_path/'rendered.s';path.write_text(text);output=tmp_path/'rebuilt.bin'
    subprocess.run([str(PROJECT_ROOT/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000',
        '-no-opt','-o',str(output),str(path)],capture_output=True,check=True)
    assert output.read_bytes()==original
