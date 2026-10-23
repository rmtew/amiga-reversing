"""Explicit value EQUs take precedence over generated immediate addresses."""
import subprocess

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.listing_context import listing_element_contexts
from amiga_reversing.disasm.manual_action_catalog import listing_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions, manual_action_log_path
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


@pytest.mark.parametrize('destination', ['$64C0.w', 'a0\n move.l a0,$64C0.w'])
@pytest.mark.parametrize('matches', [True, False])
@pytest.mark.parametrize('base', [0, 0x10000])
def test_generated_immediate_pointer_accepts_equal_equate_and_keeps_exact_bytes(tmp_path, destination, matches, base):
    binary = tmp_path/'input.bin'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend(
        'amiga-raw', f' SECTION code,code\n ORG {base}\n move.l #${base+20:X},{destination}\n rts\n dcb.b 64,0\n',
        output_path=binary)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE if base else RawAddressModel.LOCAL_OFFSET, load_address=base, entrypoint=base,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    with effective_metadata_file(tmp_path) as metadata:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)
    try:
        row = artifact.row_for_source_offset(section_index=0, offset=0)
        element = next(e for e in listing_element_contexts(row) if e['element_kind']=='immediate')
        kind, payload = listing_catalog_manual_payload(row, 'representation.symbol',
            element_context=element, parameters={'symbol':'PIXEL_SOURCE_VALUE'})
    finally:
        artifact.close()
    append_manual_actions(tmp_path, binary_source=source, actions=[
        (ManualActionKind.CREATE_MANUAL_ABSOLUTE_STORAGE_SLOT, {'absolute_storage_slot': {
            'absolute_storage_slot_id':'fixture-pointer', 'address':0x64C0, 'size':4,
            'symbol':'fixture_pointer', 'storage_kind':'pointer'}}),
        (ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT, {'data_block_layout': {
            'layout_id':'pixels', 'hunk':0, 'source_start':16, 'source_end':48,
            'name':'pixel_bytes', 'role':'bitmap', 'default_unit':'byte'}}),
        (ManualActionKind.SET_MANUAL_DATA_BLOCK_ELEMENT, {'data_block_element': {
            'data_block_element_id':'pixels:0', 'layout_id':'pixels', 'offset':0, 'width':32,
            'kind':'raw', 'name':'pixel_bytes', 'representation':'hex'}})])
    before_history = manual_action_log_path(tmp_path).read_bytes()
    with effective_metadata_file(tmp_path) as metadata:
        baseline = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
    assert ('#abs_0_00010014' if base else '#loc_0_00000014') in baseline  # Typed destination generated a source address.
    actions = [(ManualActionKind.CREATE_MANUAL_TARGET_EQUATE,
                {'target_equate':{'name':'PIXEL_SOURCE_VALUE','value':base+20 if matches else base+21}}),
               (ManualActionKind(kind), payload)]
    if not matches:
        with pytest.raises(ValueError, match='EQU value must match'):
            append_manual_actions(tmp_path, binary_source=source, actions=actions)
        assert manual_action_log_path(tmp_path).read_bytes() == before_history
        return
    append_manual_actions(tmp_path, binary_source=source, actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)
        rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
    try:
        assert '#PIXEL_SOURCE_VALUE' in artifact.row_for_source_offset(section_index=0, offset=0)['text']
        values = artifact.analysis_payload()[0]['sections'][0]['address_values']
        assert any(v['source_value']==base+20 and v['target_offset']==20 and
                   v['resolution']=='resolved' for v in values)
        assert not any(label['source_offset']==20 for label in artifact.source_plan_payload()['labels'])
        package = artifact.source_package_payload(16)
        assert any(a['source_offset']==16 and a['size']==32 for a in package['assets'])
        refs = artifact.query_payload('references', symbol='PIXEL_SOURCE_VALUE')['items']
        assert len(refs)==1 and refs[0].get('target_offset') is None
    finally:
        artifact.close()
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered)
    assert rebuilt == original
    assembly, output = tmp_path/'rendered.s', tmp_path/'oracle.bin'
    assembly.write_text(rendered)
    result = subprocess.run([str(PROJECT_ROOT/'tools/vasmm68k_mot.exe'), '-quiet', '-no-opt', '-Fbin',
        '-o', str(output), str(assembly)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout+result.stderr
    assert output.read_bytes() == original


@pytest.mark.parametrize('mnemonic', ['btst.b', 'bset.b', 'bclr.b'])
@pytest.mark.parametrize('matches', [True, False])
def test_bit_number_equate_without_byte_width_accepts_only_equal_value(tmp_path, mnemonic, matches):
    binary = tmp_path/'input.bin'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend(
        'amiga-raw', f' SECTION code,code\n {mnemonic} #3,72(a5)\n rts\n', output_path=binary)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    with effective_metadata_file(tmp_path) as metadata:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)
    try:
        row = artifact.row_for_source_offset(section_index=0, offset=0)
        element = next(e for e in listing_element_contexts(row) if e['element_kind']=='immediate')
        kind, payload = listing_catalog_manual_payload(row, 'representation.symbol',
            element_context=element, parameters={'symbol':'READY_BIT'})
    finally:
        artifact.close()
    assert payload['representation'].get('width_bytes') is None
    before = {p.name:p.read_bytes() for p in tmp_path.iterdir() if p.is_file() and p.name!='.target-history.lock'}
    actions = [(ManualActionKind.CREATE_MANUAL_TARGET_EQUATE,
                {'target_equate':{'name':'READY_BIT','value':3 if matches else 4}}),
               (ManualActionKind(kind), payload)]
    if not matches:
        with pytest.raises(ValueError, match='EQU value must match'):
            append_manual_actions(tmp_path, binary_source=source, actions=actions)
        assert {p.name:p.read_bytes() for p in tmp_path.iterdir() if p.is_file() and p.name!='.target-history.lock'} == before
        return
    append_manual_actions(tmp_path, binary_source=source, actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
    assert '#READY_BIT' in rendered
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered)
    assert rebuilt == original
    assembly, output = tmp_path/'rendered.s', tmp_path/'oracle.bin'
    assembly.write_text(rendered)
    result = subprocess.run([str(PROJECT_ROOT/'tools/vasmm68k_mot.exe'), '-quiet', '-no-opt', '-Fbin',
        '-o', str(output), str(assembly)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout+result.stderr
    assert output.read_bytes() == original
