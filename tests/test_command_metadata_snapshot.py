"""Only current, locked command preparation shares metadata projections."""

from copy import deepcopy

import pytest

from amiga_reversing.disasm import effective_metadata, server
from tests.test_restoration_batch import batch_target as batch_target
from tests.test_restoration_batch import invoke


def counted_metadata(monkeypatch):
    calls = {"wire": [], "typed": []}
    original_typed = effective_metadata.effective_target_metadata
    def typed(path, **kwargs):
        if kwargs:
            return original_typed(path, **kwargs)
        calls["typed"].append(path)
        return object()
    monkeypatch.setattr(server, "effective_metadata_text",
                        lambda path: calls["wire"].append(path) or '{"version": 1}')
    monkeypatch.setattr(effective_metadata, "effective_target_metadata", typed)
    return calls


def test_prepare_reuses_pair_and_resets_before_append(batch_target, monkeypatch):
    calls = counted_metadata(monkeypatch)
    directory = batch_target.directory
    original_prepare = server._prepare_catalog_command
    def prepare(*args):
        assert server._command_preparation_metadata(directory) is server._command_preparation_metadata(directory)
        assert server._command_preparation_metadata(directory, typed=True) is server._command_preparation_metadata(directory, typed=True)
        return original_prepare(*args)
    monkeypatch.setattr(server, "_prepare_catalog_command", prepare)
    original_append = server._apply_manual_action_commands
    def append(*args, **kwargs):
        assert server._COMMAND_METADATA_SNAPSHOTS.get() is None
        return original_append(*args, **kwargs)
    monkeypatch.setattr(server, "_apply_manual_action_commands", append)
    invoke(batch_target)
    assert calls == {"wire": [directory], "typed": [directory]}
    assert server._COMMAND_METADATA_SNAPSHOTS.get() is None
    # Direct reads and subsequent preparation never retain a prior projection.
    server._command_preparation_metadata(directory)
    server._command_preparation_metadata(directory)
    assert calls["wire"] == [directory] * 3


def test_invalid_middle_cleans_snapshot_and_preserves_histories(batch_target, monkeypatch):
    calls = counted_metadata(monkeypatch)
    original_prepare = server._prepare_catalog_command
    def prepare(*args):
        server._command_preparation_metadata(batch_target.directory)
        server._command_preparation_metadata(batch_target.directory, typed=True)
        return original_prepare(*args)
    monkeypatch.setattr(server, "_prepare_catalog_command", prepare)
    entries = deepcopy(batch_target.entries)
    entries.insert(1, {**entries[0], "command_id": "unavailable.command"})
    journal = batch_target.directory / "decision_journal.jsonl"
    journal.write_bytes(b"preserve exactly\n")
    with pytest.raises(ValueError, match="Command is not available"):
        invoke(batch_target, entries=entries)
    assert server._COMMAND_METADATA_SNAPSHOTS.get() is None
    assert len(calls["wire"]) == len(calls["typed"]) == 1
    assert not (batch_target.directory / "manual_actions.jsonl").exists()
    assert journal.read_bytes() == b"preserve exactly\n"


def test_loader_exception_is_not_cached_and_direct_typed_reads_are_fresh(tmp_path, monkeypatch):
    calls = counted_metadata(monkeypatch)
    token = server._COMMAND_METADATA_SNAPSHOTS.set({})
    try:
        monkeypatch.setattr(server, "effective_metadata_text", lambda _: '{invalid')
        with pytest.raises(ValueError, match="property name"):
            server._command_preparation_metadata(tmp_path)
        assert server._COMMAND_METADATA_SNAPSHOTS.get()[tmp_path] == {}
    finally:
        server._COMMAND_METADATA_SNAPSHOTS.reset(token)
    assert server._command_preparation_metadata(tmp_path, typed=True) is not server._command_preparation_metadata(tmp_path, typed=True)
    assert calls["typed"] == [tmp_path, tmp_path]
