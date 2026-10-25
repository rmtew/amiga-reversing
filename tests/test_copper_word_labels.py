"""Copper value labels must not suppress later command expressions."""
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind, append_manual_actions
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


@pytest.mark.c_backend
@pytest.mark.parametrize('value_label', [False, True])
@pytest.mark.parametrize('early_stop', [False, True])
def test_copper_value_word_label_resumes_at_next_command(tmp_path, value_label, early_stop):
    head = 12
    original = bytes.fromhex('23fc0000000c00dff0804e75' '01004200')
    if early_stop:
        original += bytes.fromhex('fffffffe')
    original += bytes.fromhex('00e0000700e28000fffffffe')
    binary = tmp_path / 'copper.bin'
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    actions = [(Kind.CREATE_MANUAL_SEED, {'seed': dict(seed_id='physical_list', kind='data',
        mode='required', hunk=0, addr=head, end=len(original), name='physical_copper_list',
        data_role='copper_list', unit='word')})]
    if value_label:
        actions.append((Kind.CREATE_MANUAL_LABEL, {'label': dict(label_id='value', hunk=0,
            addr=14, name='display_control_value', scope='global', address_domain='source')}))
    append_manual_actions(tmp_path, binary_source=source, actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(source,
            metadata_path=metadata, project_root=PROJECT_ROOT)[2]
        try:
            text = artifact.source_projection_with_profile()[0]
            analysis, _ = artifact.analysis_payload()
            assert analysis['source_quality_diagnostic_count'] == 0
        finally:
            artifact.close()
    assert 'dc.w bplpt,' in text and 'dc.w bplpt+$02,' in text
    if not value_label:
        assert 'dc.w bplpt,bitmap_00078000_hi' in text
        assert 'dc.w bplpt+$02,bitmap_00078000_lo' in text
    if value_label:
        assert 'display_control_value:' in text
    includes = PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include'
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text, include_dir=includes)
    assert rebuilt == original
    asm, output = tmp_path/'rendered.s', tmp_path/'vasm.bin'
    asm.write_text(text)
    subprocess.run([str(PROJECT_ROOT/'ext/vasm/vasmm68k_mot'), '-quiet', '-Fbin', '-m68000',
        '-no-opt', '-I'+str(includes)+'/', '-o', str(output), str(asm)], capture_output=True, check=True)
    assert output.read_bytes() == original


@pytest.mark.c_backend
def test_writable_copper_gate_does_not_hide_following_commands(tmp_path):
    head, gate = 22, 26
    original = (bytes.fromhex('23fc4a01ff00') + gate.to_bytes(4, 'big') +
        bytes.fromhex('23fc') + head.to_bytes(4, 'big') + bytes.fromhex('00dff0804e75') +
        bytes.fromhex('01004200fffffffe00e0000700e28000fffffffe'))
    binary = tmp_path/'writable.bin'
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    actions = [(Kind.CREATE_MANUAL_SEED, {'seed': dict(seed_id=name, kind='data', mode='required',
        hunk=0, addr=start, end=end, name=name, data_role=role, unit='word')})
        for start,end,name,role in [(head,len(original),'physical_backing','raw'),
            (head,gate,'first_commands','copper_list'),
            (gate,len(original),'writable_continuation','copper_list')]]
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,
            metadata_path=metadata,project_root=PROJECT_ROOT)[2]
        try:
            text=artifact.source_projection_with_profile()[0]
        finally:
            artifact.close()
    assert 'dc.w bplpt,bitmap_00078000_hi' in text
    includes=PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include'
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text,include_dir=includes)
    assert rebuilt==original
    asm,output=tmp_path/'writable.s',tmp_path/'vasm.bin'
    asm.write_text(text)
    subprocess.run([str(PROJECT_ROOT/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000',
        '-no-opt','-I'+str(includes)+'/', '-o',str(output),str(asm)],capture_output=True,check=True)
    assert output.read_bytes()==original
