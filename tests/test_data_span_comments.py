"""A range annotation belongs to its first directive, not every wrapped line."""
from pathlib import Path
import subprocess
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from amiga_reversing.disasm.project_paths import PROJECT_ROOT

@pytest.mark.c_backend
@pytest.mark.parametrize('unit', ['byte', 'word', 'long'])
@pytest.mark.parametrize('tail', [0, 1])
def test_wrapped_data_retains_distinct_notes_once(tmp_path, unit, tail):
    original = bytes.fromhex('4e75') + bytes(range(1, 98 + tail)) + bytes(range(101, 150))
    binary = tmp_path/'span.bin'; binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    split=99+tail
    actions=[]
    for start,end,name,note in [(2,split,'first_span','First independent span.'),
                                (split,len(original),'second_span','Second independent span.')]:
        actions.append((Kind.CREATE_MANUAL_SEED, {'seed': dict(seed_id=name,kind='data',
            mode='required',hunk=0,addr=start,end=end,name=name,data_role='raw',unit=unit,comment=note)}))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,
            metadata_path=metadata,project_root=PROJECT_ROOT)[2]
        try: text=artifact.source_projection_with_profile()[0]
        finally: artifact.close()
    assert text.count('First independent span.')==1, text
    assert text.count('Second independent span.')==1, text
    includes=PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include'
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text,include_dir=includes)
    assert rebuilt==original
    asm=tmp_path/'out.s'; asm.write_text(text); output=tmp_path/'out.bin'
    subprocess.run([str(PROJECT_ROOT/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000',
        '-no-opt','-I'+str(includes)+'/', '-o',str(output),str(asm)],capture_output=True,check=True)
    assert output.read_bytes()==original
