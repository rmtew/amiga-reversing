"""Indexed literal presentation preserves the dynamic EA and does not prove bounds."""
import subprocess

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import listing_catalog_manual_payload, listing_element_action_catalog
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind, append_manual_actions, manual_action_log_path
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def setup_source(tmp_path, displacement, index='d0.w', base='a1'):
    binary = tmp_path / 'input.bin'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        f' SECTION code,code\n ORG 0\n move.l {displacement}({base},{index}),d2\n rts\n',
        output_path=binary, project_root=PROJECT_ROOT)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    artifact = c_backend.build_listing_artifact_profile_from_binary_source(source)[2]
    try:
        rows = artifact.addr_window_payload(addr=0, before=0, after=8)[0]['rows']
        row = next(r for r in rows if r['kind'] == 'instruction' and r['start_offset'] == 0)
    finally:
        artifact.close()
    return source, original, row


@pytest.mark.parametrize('displacement,index', [(4, 'd0.w'), (-4, 'd0.w'), (127, 'a2.l'), (-128, 'a2.l')])
def test_native_indexed_literal_roundtrips_c_and_vasm(tmp_path, displacement, index):
    source, original, row = setup_source(tmp_path, displacement, index)
    part = next(p for p in row['operand_parts'] if p['kind'] == 'indexed_displacement')
    assert (part['value'], part['width_bytes'], part['operand_index']) == (displacement, 1, 0)
    context = {'element_kind': 'indexed_displacement', 'operand_index': 0}
    actions = listing_element_action_catalog(row, context)
    assert [a['action_id'] for a in actions if a['action_id'].startswith('representation.')] == ['representation.symbol']
    _, payload = listing_catalog_manual_payload(row, 'representation.symbol', element_context=context,
        parameters={'symbol': 'record_offset'})
    append_manual_actions(tmp_path, binary_source=source, actions=[
        (Kind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {'name': 'record_offset', 'value': displacement}}),
        (Kind.CREATE_MANUAL_REPRESENTATION, payload)])
    with effective_metadata_file(tmp_path) as metadata:
        text = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata, project_root=PROJECT_ROOT)
    assert f'move.l record_offset(a1,{index}),d2' in text
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text, project_root=PROJECT_ROOT)
    assert rebuilt == original
    path, output = tmp_path / 'rendered.s', tmp_path / 'oracle.bin'
    path.write_text(text)
    result = subprocess.run([str(PROJECT_ROOT / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-o', str(output), str(path)],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.read_bytes() == original


@pytest.mark.parametrize('value,width,symbol', [(5, 1, 'record_offset'), (4, 2, 'record_offset'), (4, 1, 'unknown')])
def test_bad_indexed_equate_rejected_before_history(tmp_path, value, width, symbol):
    source, _, _ = setup_source(tmp_path, 4)
    actions = [(Kind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {'name': 'record_offset', 'value': 4}}),
        (Kind.CREATE_MANUAL_REPRESENTATION, {'representation': {'representation_id': 'test', 'hunk': 0,
            'addr': 0, 'end': 4, 'style': 'symbol', 'element_kind': 'indexed_displacement', 'operand_index': 0,
            'value': value, 'width_bytes': width, 'symbol': symbol}})]
    with pytest.raises(ValueError, match='equal-valued canonical EQU'):
        append_manual_actions(tmp_path, binary_source=source, actions=actions)
    assert not manual_action_log_path(tmp_path).exists()


def test_indexed_context_requires_native_signed_byte():
    for value, width in [(128, 1), (-129, 1), (4, 2), (None, 1)]:
        row = {'kind': 'instruction', 'section_index': 0, 'start_offset': 0, 'end_offset': 4,
            'operand_parts': [{'kind': 'indexed_displacement', 'operand_index': 0, 'value': value, 'width_bytes': width}]}
        assert not any(a['action_id'] == 'representation.symbol' for a in
            listing_element_action_catalog(row, {'element_kind': 'indexed_displacement', 'operand_index': 0}))


def test_pc_index_is_not_exposed_as_an_address_register_displacement(tmp_path):
    _, _, row = setup_source(tmp_path, 4, base='pc')
    assert not any(p['kind'] == 'indexed_displacement' for p in row.get('operand_parts', []))


def test_native_renderer_rechecks_displacement_against_decoded_bytes(tmp_path):
    source, _, row = setup_source(tmp_path, 4)
    _, payload = listing_catalog_manual_payload(row, 'representation.symbol',
        element_context={'element_kind': 'indexed_displacement', 'operand_index': 0},
        parameters={'symbol': 'wrong_offset'})
    # A stale/forged history payload can agree with its EQU but not with the bytes.
    payload['representation']['value'] = 5
    append_manual_actions(tmp_path, binary_source=source, actions=[
        (Kind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {'name': 'wrong_offset', 'value': 5}}),
        (Kind.CREATE_MANUAL_REPRESENTATION, payload)])
    with effective_metadata_file(tmp_path) as metadata:
        with pytest.raises(RuntimeError):
            c_backend.render_project_source_with_c_backend(source, metadata_path=metadata, project_root=PROJECT_ROOT)
