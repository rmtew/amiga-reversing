"""Row renames supersede old same-address names while retaining other aliases."""
from dataclasses import replace

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.effective_metadata import _append_manual_label_declaration, effective_target_metadata
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind, append_manual_actions
from amiga_reversing.disasm.target_metadata import SeededCodeLabelMetadata, TargetMetadataSeedOrigin, TargetMetadataReviewStatus
from tests.test_canonical_source_symbol import fixture, artifact_for, representation


def test_rename_precedence_preserves_other_addresses_sections_and_aliases():
    old = SeededCodeLabelMetadata(addr=8, hunk=0, name='old', seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS, review_status=TargetMetadataReviewStatus.SEEDED, citation='test')
    alias = replace(old, name='legitimate_alias')
    other_address, other_section = replace(old, addr=12), replace(old, hunk=1)
    declarations = [old, alias, other_address, other_section]
    new = replace(old, name='new')
    _append_manual_label_declaration(declarations, new, {'previous_name': 'old'})
    assert declarations == [new, alias, other_address, other_section]


def test_legacy_manual_id_and_repeated_row_rename_reach_native_source(tmp_path):
    source, value = fixture(tmp_path)
    append_manual_actions(tmp_path, binary_source=source, actions=[
        (Kind.CREATE_MANUAL_LABEL, {'label': dict(label_id='alias', hunk=0, addr=8, name='legitimate_alias', scope='global', address_domain='source')}),
        representation(value),
    ])
    renamed = append_manual_actions(tmp_path, binary_source=source, actions=[
        (Kind.CREATE_MANUAL_LABEL, {'label': dict(label_id='row', hunk=0, addr=8, name='new_bank', previous_name='tile_bank', scope='global', address_domain='source')}),
        (Kind.CREATE_MANUAL_LABEL, {'label': dict(label_id='row', hunk=0, addr=8, name='final_bank', previous_name='new_bank', scope='global', address_domain='source')}),
    ])
    metadata = effective_target_metadata(tmp_path)
    names = [x.name for x in metadata.seeded_code_labels if x.hunk == 0 and x.addr == 8]
    assert names == ['final_bank', 'legitimate_alias']
    artifact = artifact_for(tmp_path, source)
    try:
        text = artifact.source_projection_with_profile()[0]
        assert 'subi.l #final_bank,d0' in text
        assert 'final_bank:' in text and 'tile_bank:' not in text and 'new_bank:' not in text
        assert any(x['target_offset']==8 for x in artifact.query_payload('references', symbol='final_bank')['items'])
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)
        assert rebuilt == source.path.read_bytes()
    finally:
        artifact.close()

    append_manual_actions(tmp_path, binary_source=source, actions=[(Kind.UNDO_ACTION, {'undoes_action_id': renamed[-1]['action_id']})])
    names = [x.name for x in effective_target_metadata(tmp_path).seeded_code_labels if x.hunk == 0 and x.addr == 8]
    assert names == ['new_bank', 'legitimate_alias']
    append_manual_actions(tmp_path, binary_source=source, actions=[(Kind.REDO_ACTION, {'redoes_action_id': renamed[-1]['action_id']})])
    names = [x.name for x in effective_target_metadata(tmp_path).seeded_code_labels if x.hunk == 0 and x.addr == 8]
    assert names == ['final_bank', 'legitimate_alias']
