"""A relative WORD dispatch may reach already accepted code beyond a local heuristic window."""
import subprocess
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import append_manual_actions,ManualActionKind as Kind

@pytest.mark.c_backend
@pytest.mark.parametrize('backwards',[False,True])
@pytest.mark.parametrize('far_evidence',['code','none','data','interior'])
def test_far_word_targets_require_existing_code_evidence(tmp_path,backwards,far_evidence):
    body=' move.l #0,d0\n rts\n' if far_evidence=='interior' else ' rts\n'
    prefix=' bra.w dispatch\nback:\n'+body+' dcb.b $2200,0\n' if backwards else ''
    suffix='' if backwards else ' dcb.b $2200,0\nfar:\n'+body
    target='back' if backwards else 'far'
    if far_evidence=='interior':target+=' + 2'
    asm=' SECTION code,code\n ORG $1000\n'+prefix+f'''dispatch:
 move.w offsets(pc,d1.w),d1
 jmp offsets(pc,d1.w)
offsets:
 dc.w near-offsets,{target}-offsets
near:
 rts
'''+suffix
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    dispatch=(0x220C if far_evidence=='interior' else 0x2206) if backwards else 0
    table=dispatch+8;near=table+4;code_start=4 if backwards else len(original)-(8 if far_evidence=='interior' else 2)
    far=code_start+(2 if far_evidence=='interior' else 0)
    assert abs(far-table)>0x2000
    binary=tmp_path/'dispatch.bin';binary.write_bytes(original)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,
        entrypoint=0x1000,code_start_offset=0,
        display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[(Kind.CREATE_MANUAL_SEED,{'seed':dict(seed_id='near',kind='code',mode='required',hunk=0,addr=near)})]
    if far_evidence!='none':actions.append((Kind.CREATE_MANUAL_SEED,{'seed':dict(
        seed_id='far',kind='code' if far_evidence in ['code','interior'] else 'data',mode='required',
        hunk=0,addr=code_start,**({}if far_evidence in ['code','interior'] else dict(end=far+2,unit='word',data_role='raw')))}))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path)as metadata:
        art=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
        try:analysis=art.analysis_payload()[0];text=art.source_projection_with_profile()[0]
        finally:art.close()
    sites=[s for s in analysis['sections'][0]['recovered_indirect_sites']if s['offset']==dispatch+4]
    assert len(sites)==1
    if far_evidence=='code':
        assert sites[0]['status']=='jump_table',sites
        assert sites[0]['target_count']==2,sites
    else:
        assert sites[0]['status']!='jump_table',sites
        if far_evidence=='interior':
            assert not any(r['offset']==far for r in analysis['sections'][0]['code_start_refs'])
        else:
            assert not any(r['start_offset']<=far<r['end_offset'] for r in analysis['sections'][0]['accepted_code_runs'])
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
    assert rebuilt==original
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT
    path=tmp_path/'rendered.s';path.write_text(text);output=tmp_path/'vasm.bin'
    subprocess.run([str(PROJECT_ROOT/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000',
        '-no-opt','-o',str(output),str(path)],capture_output=True,check=True)
    assert output.read_bytes()==original
