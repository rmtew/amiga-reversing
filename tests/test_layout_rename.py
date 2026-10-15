"""Catalog rename reuses sparse layout edit without replacing owned facts."""
from __future__ import annotations

import pytest

from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.manual_action_catalog import target_action_catalog, target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_action, load_manual_projection
from tests.test_manual_action_log import _write_raw_source
from tests.test_restoration_batch import batch_target as batch_target


def test_layout_rename_catalog_preserves_identity_without_range_defaults():
    action = next(a for a in target_action_catalog() if a['action_id'] == 'target.data_block.layout.rename')
    assert action['parameter_schema']['required'] == ['layout_id', 'name']
    kind, payload = target_catalog_manual_payload('target.data_block.layout.rename', {'layout_id': ' owner ', 'name': ' actor '})
    assert kind == 'edit_manual_data_block_layout'
    assert payload == {'data_block_layout': {'layout_id': 'owner', 'name': 'actor'}}


@pytest.mark.parametrize('parameters', [{'layout_id': '', 'name': 'actor'}, {'layout_id': 'owner', 'name': ' '}])
def test_layout_rename_refuses_empty_identity_or_name(parameters):
    with pytest.raises(ValueError, match='nonempty'):
        target_catalog_manual_payload('target.data_block.layout.rename', parameters)


def test_layout_rename_replay_keeps_range_role_elements_and_reference(tmp_path):
    _write_raw_source(tmp_path, tmp_path/'binary.bin', b'\0\0\0\x08'+b'\0'*12)
    source = resolve_target_binary_source(tmp_path)
    def append(kind, payload):
        return append_manual_action(tmp_path, kind=ManualActionKind(kind), payload=payload, binary_source=source)
    layout = dict(layout_id='owner', hunk=0, source_start=0, source_end=16, name='old_actor', role='pointer_table', default_unit='long')
    append('create_manual_data_block_layout', {'data_block_layout': layout})
    append('create_manual_custom_struct', {'custom_struct': dict(name='Record', size=4, fields=[dict(name='value', type='long', offset=0, size=4, value_kind='scalar')])})
    kind, element_payload = target_catalog_manual_payload('target.data_block.element.set', dict(layout_id='owner', offset=0, width=16, kind='struct', array_count=4, array_stride=4, binding_kind='custom_struct', type_id='Record'))
    append(kind, element_payload)
    # Keep the established interpreted reference attached to the same owner.
    append('interpret_manual_data_block_element_ref', {'data_block_interpreted_ref': dict(data_block_ref_id='owner:0:absolute', layout_id='owner', offset=0, width=4, reference_kind='absolute', target_hunk=0, target_offset=8, target_locator=dict(hunk=0, offset=8), source_value=8)})
    before = load_manual_projection(tmp_path, binary_source=source)
    log = tmp_path/'manual_actions.jsonl'
    prefix = log.read_bytes()
    kind, payload = target_catalog_manual_payload('target.data_block.layout.rename', {'layout_id': 'owner', 'name': 'new_actor'})
    append(kind, payload)
    after = load_manual_projection(tmp_path, binary_source=source)
    assert after.data_block_layouts == ({**layout, 'name': 'new_actor'},)
    assert after.data_block_elements == before.data_block_elements
    assert after.data_block_interpreted_refs == before.data_block_interpreted_refs
    assert log.read_bytes().startswith(prefix)
    stable = log.read_bytes()
    kind, payload = target_catalog_manual_payload('target.data_block.layout.rename', {'layout_id': 'missing', 'name': 'new_actor'})
    with pytest.raises(ValueError):
        append(kind, payload)
    assert log.read_bytes() == stable


def test_layout_rename_runs_through_revision_checked_server_command(batch_target, monkeypatch):
    from tests.listing_types_fixtures import ListingRow
    from tests.test_disasm_server import _RowsCListingArtifact, _seed_c_listing_artifact
    from tests.test_restoration_batch import invoke
    target = batch_target
    append_manual_action(target.directory, kind=ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT,
                         payload={'data_block_layout': dict(layout_id='owner', hunk=1, source_start=0, source_end=4, name='old_actor', role='data', default_unit='long')},
                         binary_source=target.source)
    row = ListingRow(row_id='r0', kind='instruction', text='rts\n', addr=0, section_index=0,
                     start_offset=0, end_offset=2, stable_key='s0:00000000:instruction')
    _seed_c_listing_artifact(monkeypatch, 'bloodwych', _RowsCListingArtifact([row]))
    entry = dict(command_id='target.data_block.layout.rename', context={'kind': 'target'},
                 parameters={'layout_id': 'owner', 'name': 'new_actor'},
                 evidence={'reason': 'Synthetic layout rename must preserve the inspected identity.',
                           'source_evidence_refs': ['s0:00000000:instruction']})
    from amiga_reversing.disasm import restoration
    revision = restoration.revisions('bloodwych')['revision']
    result = invoke(target, entries=[entry], revision=revision)
    assert result['actions'][0]['kind'] == 'edit_manual_data_block_layout'
    assert load_manual_projection(target.directory, binary_source=target.source).data_block_layouts[0]['name'] == 'new_actor'
    prefix = (target.directory/'manual_actions.jsonl').read_bytes()
    with pytest.raises(ValueError, match='stale_revision'):
        invoke(target, entries=[entry], revision=revision)
    assert (target.directory/'manual_actions.jsonl').read_bytes() == prefix
