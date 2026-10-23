"""Generated field aliases stay internal when owners repeat the field name."""

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.effective_metadata import effective_metadata_file, effective_target_metadata
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from tests.test_compact_struct_arrays import assert_package_bytes, fixture


@pytest.mark.parametrize('owner', ['word_1_bank', 'pre_word_1_bank'])
@pytest.mark.parametrize('count', [1, 2])
def test_repeated_field_name_in_owner_does_not_export_generated_alias(tmp_path, owner, count):
    _check(tmp_path, owner, count, authored=False)


@pytest.mark.parametrize('count', [1, 2])
def test_explicit_field_anchor_survives_repeated_field_name_in_owner(tmp_path, count):
    _check(tmp_path, 'word_1_bank', count, authored=True)


def _check(tmp_path, owner, count, *, authored):
    source, original, metadata = fixture(tmp_path, kind='struct', count=count, selected=32)
    layout_id = metadata.data_block_layouts[0].layout_id
    commands = [
        ('target.data_block.layout.rename', dict(layout_id=layout_id, name=owner)),
        ('target.data_block.elements.rename', dict(renames=[
            dict(layout_id=layout_id, offset=0, name=owner)])),
    ]
    if authored:
        commands.append(('target.code_label.add', dict(hunk=0, addr=34, name='keep_word_anchor')))
    actions = []
    for command, parameters in commands:
        kind, payload = target_catalog_manual_payload(command, parameters)
        actions.append((ManualActionKind(kind), payload))
    append_manual_actions(tmp_path, binary_source=source, actions=actions)
    metadata = effective_target_metadata(tmp_path)
    aliases = [item.name for item in metadata.seeded_entities if item.field_name == 'word_1']
    assert len(aliases) == count
    with effective_metadata_file(tmp_path) as path:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=path)[2]
    try:
        text = artifact.inline_source_text_with_profile()[0]
    finally:
        artifact.close()
    assert owner + ':\n' in text
    assert '; word_1' in text
    assert all(alias + ':\n' not in text for alias in aliases)
    assert ('keep_word_anchor:\n' in text) == authored
    assert_package_bytes(tmp_path, text, original)
