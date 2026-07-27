from __future__ import annotations

import pytest

from src.scripts.platform_manifest_io import iter_jsonl_manifest, read_jsonl_manifest, write_jsonl_manifest


def test_write_jsonl_manifest_streams_and_atomically_replaces_output(tmp_path) -> None:
    output = tmp_path / "manifest.jsonl"
    output.write_text('{"old":true}\n', encoding="utf-8")

    write_jsonl_manifest(output, [{"id": 1}, {"id": 2, "name": "entry"}])

    assert read_jsonl_manifest(output) == [{"id": 1}, {"id": 2, "name": "entry"}]
    assert list(iter_jsonl_manifest(output)) == [{"id": 1}, {"id": 2, "name": "entry"}]
    assert not (tmp_path / ".manifest.jsonl.tmp").exists()


def test_write_jsonl_manifest_keeps_previous_output_when_serialization_fails(tmp_path) -> None:
    output = tmp_path / "manifest.jsonl"
    output.write_text('{"old":true}\n', encoding="utf-8")

    with pytest.raises(TypeError):
        write_jsonl_manifest(output, [{"id": 1}, {"not_json": {1}}])

    assert read_jsonl_manifest(output) == [{"old": True}]
    assert not (tmp_path / ".manifest.jsonl.tmp").exists()
