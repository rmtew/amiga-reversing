"""Canonical presentation edits replace the same operand while history survives."""
import subprocess

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file, effective_target_metadata
from amiga_reversing.disasm.manual_action_catalog import listing_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind as Kind, append_manual_action, append_manual_actions,
    load_manual_projection, manual_action_log_path, manual_representation_owner_key,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import (
    TargetMetadata, ManualRepresentationMetadata, ManualRepresentationStyle,
    TargetMetadataSeedOrigin, TargetMetadataReviewStatus, write_target_metadata,
)


def fixture(tmp_path, legacy=False):
    binary = tmp_path/'input.bin'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        ' SECTION code,code\n ORG 0\n move.w #32,4(a1)\n rts\n', output_path=binary, project_root=PROJECT_ROOT)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    old = {'representation_id': 'old', 'hunk': 0, 'addr': 0, 'end': 6,
           'style': 'character', 'element_kind': 'immediate', 'operand_index': 0}
    seeded = ManualRepresentationMetadata(addr=0, end=6, hunk=0, operand_index=0,
        element_kind='immediate', style=ManualRepresentationStyle.CHARACTER,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS, review_status=TargetMetadataReviewStatus.SEEDED,
        citation='fixture')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=(),
        manual_representations=(seeded,) if legacy else ()))
    if not legacy:append_manual_action(tmp_path, kind=Kind.CREATE_MANUAL_REPRESENTATION,
        payload={'representation': old}, binary_source=source)
    artifact = c_backend.build_listing_artifact_profile_from_binary_source(source)[2]
    try:row = next(r for r in artifact.addr_window_payload(addr=0, before=0, after=8)[0]['rows']
                  if r.get('kind')=='instruction' and r['start_offset']==0)
    finally:artifact.close()
    _, new = listing_catalog_manual_payload(row, 'representation.symbol',
        element_context={'element_kind': 'immediate', 'operand_index': 0}, parameters={'symbol': 'ASCII_SPACE'})
    return source, original, old, new


def render(tmp_path, source):
    with effective_metadata_file(tmp_path) as metadata:
        return c_backend.render_project_source_with_c_backend(source, metadata_path=metadata, project_root=PROJECT_ROOT)


@pytest.mark.parametrize('legacy', [False, True])
def test_edit_replaces_character_with_symbol_and_undo_redo_keep_append_only_history(tmp_path, legacy):
    source, original, old, new = fixture(tmp_path, legacy)
    log = manual_action_log_path(tmp_path)
    prefix = log.read_bytes() if log.exists() else b''
    actions = append_manual_actions(tmp_path, binary_source=source, actions=[
        (Kind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {'name': 'ASCII_SPACE', 'value': 32}}),
        (Kind.CREATE_MANUAL_REPRESENTATION, new)])
    metadata = effective_target_metadata(tmp_path)
    assert len(metadata.manual_representations)==1
    assert metadata.manual_representations[0].symbol=='ASCII_SPACE'
    text = render(tmp_path, source)
    assert 'move.w #ASCII_SPACE,$0004(a1)' in text
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text, project_root=PROJECT_ROOT)
    assert rebuilt == original
    path, output = tmp_path/'source.s', tmp_path/'vasm.bin'
    path.write_text(text)
    result = subprocess.run([str(PROJECT_ROOT/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-o', str(output), str(path)],
        capture_output=True, text=True, timeout=10)
    assert result.returncode==0, result.stdout+result.stderr
    assert output.read_bytes()==original
    append_manual_action(tmp_path, binary_source=source, kind=Kind.UNDO_ACTION,
        payload={'undoes_action_id': actions[-1]['action_id']})
    assert "move.w #' ',$0004(a1)" in render(tmp_path, source)
    append_manual_action(tmp_path, binary_source=source, kind=Kind.REDO_ACTION,
        payload={'redoes_action_id': actions[-1]['action_id']})
    assert 'move.w #ASCII_SPACE,$0004(a1)' in render(tmp_path, source)
    assert log.read_bytes().startswith(prefix)


def test_other_operand_and_revised_existing_id_keep_native_owner_identity(tmp_path):
    source, _, old, new = fixture(tmp_path)
    other = {**old, 'representation_id': 'destination', 'element_kind': 'displacement',
             'operand_index': 1, 'value': 4, 'width_bytes': 2, 'symbol': 'column', 'style': 'symbol'}
    append_manual_actions(tmp_path, binary_source=source, actions=[
        (Kind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {'name': 'column', 'value': 4}}),
        (Kind.CREATE_MANUAL_REPRESENTATION, {'representation': other}),
        (Kind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {'name': 'ASCII_SPACE', 'value': 32}}),
        (Kind.CREATE_MANUAL_REPRESENTATION, new),
        (Kind.CREATE_MANUAL_REPRESENTATION, {'representation': {**old, 'style': 'hex'}})])
    projected = load_manual_projection(tmp_path, binary_source=source).representations
    assert {(r['representation_id'], r['operand_index']) for r in projected} == {('old', 0), ('destination', 1)}
    text = render(tmp_path, source)
    assert 'move.w #$20,column(a1)' in text
    prefix = manual_action_log_path(tmp_path).read_bytes()
    with pytest.raises(ValueError, match='equal-valued canonical EQU'):
        append_manual_action(tmp_path, binary_source=source, kind=Kind.CREATE_MANUAL_REPRESENTATION,
            payload={'representation': {**other, 'symbol': 'missing'}})
    assert manual_action_log_path(tmp_path).read_bytes()==prefix


def test_presentation_owner_requires_same_section_extent_and_operand():
    owners = [manual_representation_owner_key(*args) for args in [
        (0, 2, 6, 0), (1, 2, 6, 0), (0, 2, 8, 0), (0, 2, 6, 1), (0, 2, 6, None)]]
    assert len(set(owners))==5
    assert manual_representation_owner_key(None, 2, None, None)==(0, 2, 1, None)


def test_revised_id_moving_to_another_operand_clears_old_owner_index(tmp_path):
    source, _, old, new = fixture(tmp_path)
    moved = {**old, 'style': 'hex', 'element_kind': 'displacement', 'operand_index': 1}
    append_manual_actions(tmp_path, binary_source=source, actions=[
        (Kind.CREATE_MANUAL_REPRESENTATION, {'representation': moved}),
        (Kind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {'name': 'ASCII_SPACE', 'value': 32}}),
        (Kind.CREATE_MANUAL_REPRESENTATION, new)])
    projected = load_manual_projection(tmp_path, binary_source=source).representations
    assert {(r['representation_id'], r['operand_index']) for r in projected} == {
        ('old', 1), (new['representation']['representation_id'], 0)}
    append_manual_action(tmp_path, binary_source=source, kind=Kind.REMOVE_MANUAL_REPRESENTATION,
        payload={'representation_id': 'old'})
    projected = load_manual_projection(tmp_path, binary_source=source).representations
    assert len(projected)==1 and projected[0]['operand_index']==0
