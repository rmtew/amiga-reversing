from __future__ import annotations

from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import c_backend, server
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
    manual_action_log_path,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


@pytest.fixture
def target(tmp_path, monkeypatch):
    binary = tmp_path / "source.bin"
    binary.write_bytes(bytes(0x108))
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / "cache",
    )
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    # Exercise the native accessor wrapper without making API tests depend on
    # rebuilding the shared library; native boundary tests cover its real limit.
    def capacity():
        return 2
    monkeypatch.setattr(c_backend, "_platform_file_dll", lambda root: SimpleNamespace(
        platform_file_target_equate_count_capacity=capacity,
    ))
    monkeypatch.setattr(server, "resolve_project_paths", lambda *args, **kwargs: SimpleNamespace(target_dir=tmp_path))
    monkeypatch.setattr(server, "resolve_target_binary_source", lambda directory: source)
    return tmp_path, source


def equate(name, value=1):
    return ManualActionKind.CREATE_MANUAL_TARGET_EQUATE, {
        "target_equate": {"target_equate_id": f"equate-{name}", "name": name, "value": value},
    }


def snapshot(directory):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in directory.rglob("*") if path.is_file() and path.name != ".target-history.lock"}


def test_catalog_batch_overflow_changes_no_target_files(target):
    directory, source = target
    append_manual_actions(directory, actions=[equate("ONE")], binary_source=source)
    before = snapshot(directory)
    prepared = [{"context": {"kind": "target"}, "action_payloads": [equate("TWO"), equate("THREE")]}]
    with pytest.raises(ValueError, match="at most 2 target equates.*candidate contains 3"):
        server._apply_manual_action_commands("fixture", prepared)
    assert snapshot(directory) == before


def test_new_log_overflow_creates_no_history(target):
    directory, source = target
    before = snapshot(directory)
    with pytest.raises(ValueError, match="candidate contains 3"):
        append_manual_actions(directory, actions=[equate("ONE"), equate("TWO"), equate("THREE")], binary_source=source)
    assert not manual_action_log_path(directory).exists()
    assert snapshot(directory) == before


def test_duplicate_and_update_at_capacity_are_allowed(target):
    directory, source = target
    append_manual_actions(directory, actions=[equate("ONE"), equate("TWO")], binary_source=source)
    append_manual_actions(directory, actions=[equate("ONE"), equate("TWO", 9)], binary_source=source)
    metadata = effective_target_metadata(directory, binary_source=source)
    assert {item.name: item.value for item in metadata.target_equates} == {"ONE": 1, "TWO": 9}


def test_generated_reference_proxy_counts_toward_capacity(target):
    directory, source = target
    append_manual_actions(directory, actions=[equate("ONE"), equate("TWO")], binary_source=source)
    before = snapshot(directory)
    layout = (ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT, {"data_block_layout": {
        "layout_id": "pointers", "hunk": 0, "source_start": 0x100, "source_end": 0x104, "default_unit": "long",
    }})
    element = (ManualActionKind.SET_MANUAL_DATA_BLOCK_ELEMENT, {"data_block_element": {
        "data_block_element_id": "pointers:0", "layout_id": "pointers", "offset": 0, "width": 4, "kind": "scalar",
    }})
    reference = (ManualActionKind.INTERPRET_MANUAL_DATA_BLOCK_ELEMENT_REF, {"data_block_interpreted_ref": {
        "data_block_ref_id": "pointers:0:absolute:h0:00002000", "layout_id": "pointers", "offset": 0,
        "width": 4, "reference_kind": "absolute", "target_hunk": 0, "target_offset": 0x2000,
        "target_locator": {"hunk": 0, "offset": 0x2000}, "source_value": 0x2000,
        "confidence": "manual", "xref_generation_mode": "bidirectional",
    }})
    with pytest.raises(ValueError, match="candidate contains 3.*generated"):
        append_manual_actions(directory, actions=[layout, element, reference], binary_source=source)
    assert snapshot(directory) == before


def test_redo_overflow_leaves_history_unchanged(target):
    directory, source = target
    actions = append_manual_actions(directory, actions=[equate("ONE"), equate("TWO")], binary_source=source)
    undone = actions[1]["action_id"]
    append_manual_actions(directory, actions=[(ManualActionKind.UNDO_ACTION, {"undoes_action_id": undone})], binary_source=source)
    append_manual_actions(directory, actions=[equate("THREE")], binary_source=source)
    before = snapshot(directory)
    with pytest.raises(ValueError, match="candidate contains 3"):
        append_manual_actions(directory, actions=[(ManualActionKind.REDO_ACTION, {"redoes_action_id": undone})], binary_source=source)
    assert snapshot(directory) == before
