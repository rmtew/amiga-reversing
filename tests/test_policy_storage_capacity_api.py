from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import c_backend, server
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_text
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
    manual_action_log_path,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_restoration_batch import batch_target as batch_target
from tests.test_restoration_batch import invoke


@pytest.fixture
def target(tmp_path, monkeypatch):
    binary = tmp_path / 'source.bin'
    binary.write_bytes(bytes.fromhex('4e75') + bytes(64))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'cache')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    monkeypatch.setattr(server, 'resolve_project_paths', lambda *a, **k: SimpleNamespace(target_dir=tmp_path))
    monkeypatch.setattr(server, 'resolve_target_binary_source', lambda directory: source)
    return tmp_path, source


def label(name, addr):
    return ManualActionKind.CREATE_MANUAL_LABEL, {'label': {
        'label_id': name, 'name': name, 'scope': 'global', 'address_domain': 'source', 'hunk': 0, 'addr': addr,
    }}


def snapshot(directory):
    return {str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob('*')
            if p.is_file() and p.name != '.target-history.lock'}


def label_codec(monkeypatch, limit=2):
    calls = []
    paths = []
    def native_policy(source, *, metadata_path, project_root):
        paths.append(metadata_path)
        payload = json.loads(metadata_path.read_text(encoding='utf-8'))
        calls.append(payload)
        if len(payload['seeded_code_labels']) > limit:
            raise RuntimeError(f'C backend DLL failed: named label capacity exceeded ({limit})')
        return {'analysis_policy': {}}
    monkeypatch.setattr(c_backend, 'effective_policy_project_source_with_c_backend', native_policy)
    return calls, paths


def test_catalog_label_overflow_is_rejected_before_history_write(target, monkeypatch):
    directory, source = target
    calls, paths = label_codec(monkeypatch)
    append_manual_actions(directory, actions=[label('ONE', 2)], binary_source=source)
    before = snapshot(directory)
    prepared = [{'context': {'kind': 'target'}, 'action_payloads': [label('TWO', 4), label('THREE', 6)]}]
    with pytest.raises(ValueError, match=r'named label capacity exceeded \(2\)'):
        server._apply_manual_action_commands('fixture', prepared)
    assert snapshot(directory) == before
    assert len(calls) == 2  # One native preflight per complete batch.
    assert {item['name'] for item in calls[-1]['seeded_code_labels']} == {'ONE', 'TWO', 'THREE'}
    assert all(not path.exists() for path in paths)


def test_duplicate_label_at_capacity_remains_valid(target, monkeypatch):
    directory, source = target
    calls, _ = label_codec(monkeypatch)
    append_manual_actions(directory, actions=[label('ONE', 2), label('TWO', 4)], binary_source=source)
    append_manual_actions(directory, actions=[label('ONE', 2)], binary_source=source)
    assert len(calls[-1]['seeded_code_labels']) == 2


def test_redo_label_overflow_does_not_append_history(target, monkeypatch):
    directory, source = target
    label_codec(monkeypatch)
    records = append_manual_actions(directory, actions=[label('ONE', 2), label('TWO', 4)], binary_source=source)
    reference = records[1]['action_id']
    append_manual_actions(directory, actions=[(ManualActionKind.UNDO_ACTION, {'undoes_action_id': reference})], binary_source=source)
    append_manual_actions(directory, actions=[label('THREE', 6)], binary_source=source)
    before = snapshot(directory)
    with pytest.raises(ValueError, match='named label capacity exceeded'):
        append_manual_actions(directory, actions=[(ManualActionKind.REDO_ACTION, {'redoes_action_id': reference})], binary_source=source)
    assert snapshot(directory) == before


def test_expanded_array_candidate_reaches_native_codec_before_persistence(target, monkeypatch):
    directory, source = target
    paths = []
    def native_policy(binary, *, metadata_path, project_root):
        paths.append(metadata_path)
        payload = json.loads(metadata_path.read_text())
        assert payload['custom_structs'][-1]['name'] == 'Pair'
        element = payload['data_block_layouts'][0]['elements'][0]
        assert element['array_count'] == 3 and element['array_stride'] == 2
        assert element['type_binding']['bound_type_id'] == 'Pair'
        raise RuntimeError('C backend DLL failed: structured data item capacity exceeded (2)')
    monkeypatch.setattr(c_backend, 'effective_policy_project_source_with_c_backend', native_policy)
    actions = [
        (ManualActionKind.CREATE_MANUAL_CUSTOM_STRUCT, {'custom_struct': {'name': 'Pair', 'size': 2,
            'fields': [{'name': 'value', 'type': 'word', 'offset': 0, 'size': 2}]}}),
        (ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT, {'data_block_layout': {'layout_id': 'pairs',
            'hunk': 0, 'source_start': 2, 'source_end': 8, 'default_unit': 'byte'}}),
        (ManualActionKind.SET_MANUAL_DATA_BLOCK_ELEMENT, {'data_block_element': {'data_block_element_id': 'pairs:0',
            'layout_id': 'pairs', 'offset': 0, 'width': 6, 'kind': 'struct', 'array_count': 3, 'array_stride': 2,
            'type_binding': {'type_binding_id': 'pairs-type', 'layout_id': 'pairs', 'element_offset': 0,
                'element_width': 6, 'binding_kind': 'custom_struct', 'bound_type_id': 'Pair'}}}),
    ]
    before = snapshot(directory)
    with pytest.raises(ValueError, match='structured data item capacity exceeded'):
        append_manual_actions(directory, actions=actions, binary_source=source)
    assert not manual_action_log_path(directory).exists()
    assert snapshot(directory) == before
    assert all(not path.exists() for path in paths)


def test_unrelated_native_failure_is_not_relabelled_as_capacity(target, monkeypatch):
    directory, source = target
    paths = []
    def native_policy(*args, metadata_path, **kwargs):
        paths.append(metadata_path)
        raise RuntimeError('C backend DLL failed: unsupported fixture')
    monkeypatch.setattr(c_backend, 'effective_policy_project_source_with_c_backend', native_policy)
    before = snapshot(directory)
    with pytest.raises(RuntimeError, match='unsupported fixture'):
        append_manual_actions(directory, actions=[label('ONE', 2)], binary_source=source)
    assert snapshot(directory) == before
    assert all(not path.exists() for path in paths)


def test_candidate_serialization_preserves_pending_runtime_ranges(target):
    directory, source = target
    action = {'record': 'manual_action', 'action_id': 'candidate-range', 'sequence': 1,
        'created_at': '2026-10-13T00:00:00+00:00', 'kind': ManualActionKind.CREATE_MANUAL_RUNTIME_DATA_RANGE,
        'runtime_data_range': {'runtime_data_range_id': 'scratch', 'runtime_address': 0x400, 'size': 4, 'name': 'scratch'}}
    payload = json.loads(effective_metadata_text(directory, pending_actions=[action], binary_source=source))
    assert payload['runtime_data_ranges'][0]['runtime_address'] == 0x400
    assert not manual_action_log_path(directory).exists()


def test_restoration_capacity_rejection_preserves_manual_and_decision_histories(batch_target, monkeypatch):
    invoke(batch_target, entries=[batch_target.entries[0]])
    journal = batch_target.directory / "decision_journal.jsonl"
    journal.write_bytes(b"preserve unrelated journal bytes\n")
    before = snapshot(batch_target.directory)
    def native_policy(*args, **kwargs):
        raise RuntimeError("C backend DLL failed: named label capacity exceeded (8192)")
    monkeypatch.setattr(c_backend, "effective_policy_project_source_with_c_backend", native_policy)
    with pytest.raises(ValueError, match=r"named label capacity exceeded \(8192\)"):
        invoke(batch_target)
    assert snapshot(batch_target.directory) == before


def test_manual_reference_capacity_is_clear_value_error_and_disposable(target, monkeypatch):
    _, source = target
    paths = []
    def native_policy(*args, metadata_path, **kwargs):
        paths.append(metadata_path)
        raise RuntimeError("C backend DLL failed: manual data reference capacity exceeded (512)")
    monkeypatch.setattr(c_backend, "effective_policy_project_source_with_c_backend", native_policy)
    with pytest.raises(ValueError, match=r"manual data reference capacity exceeded \(512\)"):
        c_backend.validate_policy_storage_with_c_backend(source, metadata_text="{}")
    assert all(not path.exists() for path in paths)
