from __future__ import annotations

import ctypes
import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend, manual_actions
from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.binary_source import BinarySourceKind, HunkFileBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind
from src.tests._platform_backend_test_utils import make_synthetic_hunkexe


@pytest.fixture
def target(tmp_path: Path):
    binary = tmp_path / "source.bin"
    binary.write_bytes(b"\x4e\x75")
    (tmp_path / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary", "address_model": "local_offset", "path": str(binary),
        "load_address": 0x70000, "entrypoint": 0x70000, "code_start_offset": 0,
    }))
    source = resolve_target_binary_source(tmp_path)
    assert source is not None
    return tmp_path, source


def _capacity(name: str) -> int:
    function = getattr(c_backend._platform_file_dll(c_backend.PROJECT_ROOT), name)
    function.argtypes = []
    function.restype = ctypes.c_size_t
    return function()


def _comment(text: str, identity: str = "c"):
    return Kind.CREATE_MANUAL_COMMENT, {"comment": {
        "comment_id": identity, "hunk": 0, "addr": 0, "text": text,
    }}


def _append(target, *actions):
    directory, source = target
    return manual_actions.append_manual_actions(directory, actions=actions, binary_source=source)


def test_native_capacity_boundary_and_lossless_escapes(target):
    capacity = _capacity("platform_file_entry_comment_text_capacity")
    _append(target, _comment("a" * capacity))
    _append(target, _comment('quoted "text" and \\path'))
    history = (target[0] / "manual_actions.jsonl").read_bytes()
    with pytest.raises(ValueError, match="capacity"):
        _append(target, _comment("a" * (capacity + 1)))
    assert (target[0] / "manual_actions.jsonl").read_bytes() == history


@pytest.mark.parametrize("text", ["café", "😀", "line\nnext", "tab\ttext", "nul\0text", "\ud800"])
def test_unsupported_codec_text_preserves_both_histories(target, text):
    _append(target, _comment("valid"))
    directory = target[0]
    journal = directory / "decision_journal.jsonl"
    journal.write_bytes(b"existing journal bytes\n")
    history = (directory / "manual_actions.jsonl").read_bytes()
    with pytest.raises(ValueError, match="codec|capacity"):
        _append(target, _comment(text))
    assert (directory / "manual_actions.jsonl").read_bytes() == history
    assert journal.read_bytes() == b"existing journal bytes\n"


def test_invalid_batch_does_not_create_history(target):
    capacity = _capacity("platform_file_entry_comment_text_capacity")
    with pytest.raises(ValueError, match="capacity"):
        _append(target, _comment("valid", "first"), _comment("a" * (capacity + 1), "second"))
    assert not (target[0] / "manual_actions.jsonl").exists()


def test_native_manual_count_boundary_is_atomic(target):
    capacity = _capacity("platform_file_entry_comment_count_capacity")
    # Distinct source offsets exercise native storage rather than deduplication.
    target[1].path.write_bytes(b"\x4e\x71" * (capacity+1) + b"\x4e\x75")
    actions = [(Kind.CREATE_MANUAL_COMMENT, {"comment": {
        "comment_id": str(index), "hunk": 0, "addr": 2*index, "text": f"Boundary {index}.",
    }}) for index in range(capacity)]
    _append(target, *actions)
    journal = target[0] / "decision_journal.jsonl"
    journal.write_bytes(b"existing journal bytes\n")
    history = (target[0] / "manual_actions.jsonl").read_bytes()
    with pytest.raises(ValueError, match="active manual comments"):
        _append(target, _comment("valid", "overflow"))
    assert (target[0] / "manual_actions.jsonl").read_bytes() == history
    assert journal.read_bytes() == b"existing journal bytes\n"


def test_invalid_legacy_comment_can_be_undone_but_not_redone(target):
    original = _append(target, _comment("valid"))[0]
    path = target[0] / "manual_actions.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    records[1]["comment"]["text"] = "line\nnext"
    path.write_text("".join(json.dumps(record) + "\n" for record in records))
    _append(target, (Kind.UNDO_ACTION, {"undoes_action_id": original["action_id"]}))
    history = path.read_bytes()
    with pytest.raises(ValueError, match="losslessly"):
        _append(target, (Kind.REDO_ACTION, {"redoes_action_id": original["action_id"]}))
    assert path.read_bytes() == history


def test_invalid_legacy_comment_can_be_replaced_or_removed(target):
    _append(target, _comment("valid"))
    path = target[0] / "manual_actions.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    records[1]["comment"]["text"] = "line\nnext"
    path.write_text("".join(json.dumps(record) + "\n" for record in records))
    _append(target, _comment("replacement"))
    _append(target, (Kind.REMOVE_MANUAL_COMMENT, {"comment_id": "c"}))


def test_supported_comment_renders_and_roundtrips(tmp_path):
    binary = tmp_path / "source.hunk"
    original = make_synthetic_hunkexe()
    binary.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE, path=binary, display_path=str(binary),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    (tmp_path / "source_binary.json").write_text(json.dumps({
        "kind": "hunk_file", "path": str(binary),
    }))
    _append((tmp_path, source), _comment("Synthetic entry returns to its caller."))
    with effective_metadata_file(tmp_path) as metadata:
        text = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
        assert "Synthetic entry returns to its caller." in text
        rebuilt, _analysis, _profile = c_backend.facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source, metadata_path=metadata, compare_original=True,
        )
    assert rebuilt == original


def test_more_than_128_distinct_comments_render_and_rebuild(tmp_path):
    directory = tmp_path
    binary = directory / 'many-comments.hunk'
    original = make_synthetic_hunkexe(code_data=b'\x4e\x71' * 129 + b'\x4e\x75')
    binary.write_bytes(original)
    source = HunkFileBinarySource(kind=BinarySourceKind.HUNK_FILE, path=binary,
        display_path=str(binary), analysis_cache_path=directory / 'binary.analysis')
    (directory / 'source_binary.json').write_text(json.dumps({'kind': 'hunk_file', 'path': str(binary)}))
    actions = [(Kind.CREATE_MANUAL_COMMENT, {'comment': {
        'comment_id': f'boundary-{index}', 'hunk': 0, 'addr': index*2,
        'text': f'Preserved source boundary {index}.',
    }}) for index in range(129)]
    _append((directory, source), *actions)
    with effective_metadata_file(directory) as metadata:
        text = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
        for index in range(129):
            assert f'Preserved source boundary {index}.' in text
        rebuilt, _analysis, _profile = c_backend.facts_v2_direct_rebuild_project_source_with_c_backend_profile(
            source, metadata_path=metadata, compare_original=True,
        )
    assert rebuilt == original


@pytest.mark.parametrize('text', [
    'range (left,right]', 'brace } and later { text',
    'quote " followed by ] and }', 'path \\ then [ and { punctuation',
])
def test_quoted_delimiters_do_not_end_metadata_arrays_or_objects(target, text):
    directory, source = target
    _append(target, _comment(text, 'first'), _comment('Following comment remains.', 'following'))
    with effective_metadata_file(directory) as metadata:
        rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
    assert text in rendered
    assert 'Following comment remains.' in rendered
