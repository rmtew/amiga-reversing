"""Name propagation preserves typed element identities and is atomic on refusal."""
from __future__ import annotations

import pytest

from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_action, load_manual_projection
from tests.test_manual_action_log import _write_raw_source
from tests.test_restoration_batch import batch_target as batch_target


@pytest.fixture
def typed_elements(tmp_path):
    _write_raw_source(tmp_path, tmp_path/'binary.bin', b'\0\0\0\x08'+b'\0'*12)
    source = resolve_target_binary_source(tmp_path)
    def append(kind, payload):
        return append_manual_action(tmp_path, kind=ManualActionKind(kind), payload=payload, binary_source=source)
    append('create_manual_data_block_layout', {'data_block_layout': dict(layout_id='owner', hunk=0, source_start=0, source_end=16, name='owner', role='data', default_unit='long')})
    append('create_manual_custom_struct', {'custom_struct': dict(name='Record', size=4, fields=[dict(name='value', type='long', offset=0, size=4, value_kind='scalar')])})
    for offset in [0, 8]:
        kind, payload = target_catalog_manual_payload('target.data_block.element.set', dict(layout_id='owner', offset=offset, width=8, kind='struct', array_count=2, array_stride=4, binding_kind='custom_struct', type_id='Record', name=f'old_{offset}'))
        append(kind, payload)
    append('interpret_manual_data_block_element_ref', {'data_block_interpreted_ref': dict(data_block_ref_id='owner:0:absolute', layout_id='owner', offset=0, width=4, reference_kind='absolute', target_hunk=0, target_offset=8, target_locator=dict(hunk=0, offset=8), source_value=8)})
    return tmp_path, source, append


def test_bulk_element_rename_preserves_bindings_references_and_undo(typed_elements):
    directory, source, append = typed_elements
    before = load_manual_projection(directory, binary_source=source)
    renames = [dict(layout_id='owner', offset=o, name=f'new_{o}') for o in [0, 8]]
    kind, payload = target_catalog_manual_payload('target.data_block.elements.rename', {'renames': renames})
    record = append(kind, payload)
    after = load_manual_projection(directory, binary_source=source)
    assert after.data_block_layouts == before.data_block_layouts
    assert after.data_block_elements == tuple({**e, 'name': f'new_{e["offset"]}'} for e in before.data_block_elements)
    assert after.data_block_interpreted_refs == before.data_block_interpreted_refs
    append('undo_action', {'undoes_action_id': record['action_id']})
    undone = load_manual_projection(directory, binary_source=source)
    assert undone.data_block_elements == before.data_block_elements
    assert undone.data_block_interpreted_refs == before.data_block_interpreted_refs
    append('redo_action', {'redoes_action_id': record['action_id']})
    assert load_manual_projection(directory, binary_source=source).data_block_elements == after.data_block_elements


def test_late_unknown_element_refuses_entire_rename_without_append(typed_elements):
    directory, source, append = typed_elements
    log = directory/'manual_actions.jsonl'
    before = log.read_bytes()
    renames = [dict(layout_id='owner', offset=0, name='new'), dict(layout_id='owner', offset=4, name='missing')]
    kind, payload = target_catalog_manual_payload('target.data_block.elements.rename', {'renames': renames})
    with pytest.raises(ValueError, match='unknown active owner/offset'):
        append(kind, payload)
    assert log.read_bytes() == before


@pytest.mark.parametrize('renames', [[], [dict(layout_id='owner', offset=0, name='')],
    [dict(layout_id='owner', offset=-1, name='new')],
    [dict(layout_id='owner', offset=True, name='new')],
    [dict(layout_id='owner', offset=0, name='new', width=16)],
    [dict(layout_id='owner', offset=0, name='new')]*2])
def test_element_rename_refuses_empty_names_shape_edits_and_duplicates(renames):
    with pytest.raises(ValueError):
        target_catalog_manual_payload('target.data_block.elements.rename', {'renames': renames})


def test_element_rename_has_a_bounded_selector_count():
    with pytest.raises(ValueError, match='1..1000'):
        target_catalog_manual_payload('target.data_block.elements.rename', {'renames': [dict(layout_id='owner', offset=i, name='new') for i in range(1001)]})


def test_element_rename_uses_shared_revision_checked_command(batch_target, monkeypatch):
    from tests.listing_types_fixtures import ListingRow
    from tests.test_disasm_server import _RowsCListingArtifact, _seed_c_listing_artifact
    from tests.test_restoration_batch import invoke
    target = batch_target
    def append(kind, payload):
        return append_manual_action(target.directory, kind=ManualActionKind(kind), payload=payload, binary_source=target.source)
    append('create_manual_data_block_layout', {'data_block_layout': dict(layout_id='owner', hunk=1, source_start=0, source_end=4, name='owner')})
    append('set_manual_data_block_element', {'data_block_element': dict(layout_id='owner', offset=0, width=4, kind='scalar', name='old')})
    row = ListingRow(row_id='r0', kind='instruction', text='rts\n', addr=0, section_index=0, start_offset=0, end_offset=2, stable_key='s0:00000000:instruction')
    _seed_c_listing_artifact(monkeypatch, 'bloodwych', _RowsCListingArtifact([row]))
    result = invoke(target, entries=[dict(command_id='target.data_block.elements.rename', context={'kind': 'target'},
                    parameters={'renames': [dict(layout_id='owner', offset=0, name='new')]},
                    evidence={'reason': 'Synthetic typed owner identity is unchanged.', 'source_evidence_refs': ['s0:00000000:instruction']})])
    assert result['actions'][0]['kind'] == 'rename_manual_data_block_elements'
    assert load_manual_projection(target.directory, binary_source=target.source).data_block_elements[0]['name'] == 'new'
