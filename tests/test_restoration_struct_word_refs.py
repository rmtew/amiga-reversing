"""The HTTP restoration batch validates typed relative words against native rows."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import c_backend, restoration, server
from amiga_reversing.disasm.binary_source import (
    resolve_target_binary_source,
    write_source_descriptor,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_metadata_text,
)
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_base_displacement_integration import _round_trip
from tests.test_c_backend import _requires_c_backend_dlls
from tests.test_disasm_server import _binary_project, _seed_c_listing_artifact

pytestmark = pytest.mark.c_backend


@pytest.fixture
def typed_words(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _requires_c_backend_dlls()
    original = bytes.fromhex("601a") + bytes(10)
    original += bytes.fromhex("0006fff80030fff8") * 2 + bytes.fromhex("4e75")
    binary = tmp_path / "commands.bin"
    binary.write_bytes(original)
    write_source_descriptor(tmp_path, {"kind": "raw_binary", "path": str(binary),
                                      "address_model": "local_offset", "load_address": 0,
                                      "entrypoint": 0, "code_start_offset": 0})
    source = resolve_target_binary_source(tmp_path)
    assert source is not None
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    specs = [
        ("target.custom_struct.add", {"name": "Command", "size": 8, "fields": [
            {"name": "opcode", "type": "WORD", "offset": 0, "size": 2},
            {"name": "opaque_pair", "type": "BYTE", "offset": 2, "size": 2},
            {"name": "remaining", "type": "WORD", "offset": 4, "size": 2},
            {"name": "branch", "type": "WORD", "offset": 6, "size": 2},
        ]}),
        # Real merged metadata can contain struct pointers that its native
        # wire export cannot be round-tripped through TargetMetadata.from_dict.
        ("target.custom_struct.add", {"name": "PointerHolder", "size": 4}),
        ("target.custom_struct_field.add", {"struct_name": "PointerHolder", "name": "command_ptr",
                                            "type": "LONG", "offset": 0, "size": 4,
                                            "value_kind": "struct_pointer", "pointer_struct": "Command"}),
        ("target.data_block.layout.create", {"hunk": 0, "source_start": 12, "source_end": 28,
                                              "name": "commands", "default_unit": "word"}),
        ("target.code_label.add", {"hunk": 0, "addr": 4, "name": "branch_target"}),
    ]
    actions = []
    for command, parameters in specs:
        kind, payload = target_catalog_manual_payload(command, parameters=parameters)
        actions.append((ManualActionKind(kind), payload))
    layout_id = next(payload["data_block_layout"]["layout_id"] for _, payload in actions
                     if "data_block_layout" in payload)
    kind, payload = target_catalog_manual_payload("target.data_block.element.set", parameters={
        "layout_id": layout_id, "offset": 0, "width": 16, "kind": "struct",
        "binding_kind": "custom_struct", "type_id": "Command", "array_count": 2,
        "array_stride": 8, "name": "records",
    })
    actions.append((ManualActionKind(kind), payload))
    append_manual_actions(tmp_path, actions=actions, binary_source=source)
    with effective_metadata_file(tmp_path) as metadata_path:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path,
        )
    monkeypatch.setattr(server, "resolve_project_paths", lambda *_a, **_kw: SimpleNamespace(
        target_dir=tmp_path, binary_source=source,
    ))
    monkeypatch.setattr(server, "get_project", lambda name: replace(
        _binary_project(name, ready=True), target_dir=str(tmp_path), binary_path=str(binary),
    ))
    monkeypatch.setattr(server, "mark_project_updated", lambda _name: None)
    _seed_c_listing_artifact(monkeypatch, "bloodwych", artifact)
    yield SimpleNamespace(directory=tmp_path, original=original, source=source,
                          artifact=artifact, layout_id=layout_id)
    server._LISTING_PROJECTION_SERVICE.reset()
    artifact.close()


def _entry(fixture, offset: int, base: int, target: int, *, bits: int = 0xFFF8):
    catalog = server._command_catalog_payload("bloodwych", {"context": ["target"]})
    command = next(item for item in catalog["commands"]
                   if item["command_id"] == "target.data_block.element.interpret_ref")
    row = fixture.artifact.row_for_source_offset(section_index=0, offset=12 + offset)
    return {
        "command_id": command["command_id"], "context": command["target_context"],
        "parameters": {"layout_id": fixture.layout_id, "offset": offset, "width": 2,
                       "reference_kind": "base_displacement", "signed": True, "scale": 1,
                       "base_locator": {"hunk": 0, "offset": base}, "target_hunk": 0,
                       "target_offset": target, "source_value": bits},
        "evidence": {"reason": "Inspected encoded word in the current native typed command row.",
                     "source_evidence_refs": [row["row_key"]]},
    }


def _http_batch(entries):
    return server.route_request("POST", "/api/projects/bloodwych/restoration", {}, {
        "operation": "interpret_batch", "expected_revision": restoration.revisions("bloodwych")["revision"],
        "entries": entries,
    })


def test_http_batch_accepts_actual_typed_word_rows_and_exact_source(typed_words):
    # Both synthetic record words use the same independently named table
    # anchor. The second word also exercises typed-array leaf ownership.
    result = _http_batch([_entry(typed_words, 6, 12, 4), _entry(typed_words, 14, 12, 4)])
    assert result["ok"] is True and len(result["data"]["actions"]) == 2
    metadata = json.loads(effective_metadata_text(typed_words.directory))
    assert len(metadata["manual_data_references"]) == 2
    assert not metadata["target_equates"]
    assert metadata["data_block_layouts"][0]["elements"][0]["kind"] == "struct"
    with effective_metadata_file(typed_words.directory) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(typed_words.source, metadata_path=metadata_path)
    assert "\tdc.w branch_target-commands" in rendered
    assert "dblk_ref_" not in rendered
    _round_trip(typed_words.directory, rendered, typed_words.original)


@pytest.mark.parametrize("invalid", ["byte_leaf", "source_bytes", "missing_labels"])
def test_http_batch_invalid_last_ref_preserves_both_histories(typed_words, invalid: str):
    history = typed_words.directory / "manual_actions.jsonl"
    journal = typed_words.directory / "decision_journal.jsonl"
    journal.write_bytes(b"preserve unrelated journal bytes\n")
    before = history.read_bytes()
    valid = _entry(typed_words, 6, 12, 4)
    if invalid == "byte_leaf":
        last = _entry(typed_words, 2, 12, 4)
        match = "exact declared WORD leaf"
    elif invalid == "source_bytes":
        last = _entry(typed_words, 14, 20, 13, bits=0xFFF9)
        match = "source_value must match"
    else:
        last = _entry(typed_words, 14, 21, 13)
        match = "native source labels"
    with pytest.raises(ValueError, match=match):
        _http_batch([valid, last])
    assert history.read_bytes() == before
    assert journal.read_bytes() == b"preserve unrelated journal bytes\n"


@pytest.mark.parametrize("names", [
    ("first_branch_word", "second_branch_word"),
    ("commands_branch_0", "commands_branch_1"),
])
def test_normal_source_labels_anchor_word_fields_without_changing_struct_owner(typed_words, monkeypatch, names):
    before = json.loads(effective_metadata_text(typed_words.directory))["data_block_layouts"]
    entries = []
    for offset, name in list(zip((18, 26), names, strict=True)):
        row = typed_words.artifact.row_for_source_offset(section_index=0, offset=offset)
        catalog = server._command_catalog_payload("bloodwych", {"context": ["target"]})
        command = next(item for item in catalog["commands"]
                       if item["command_id"] == "target.code_label.add")
        entries.append({"command_id": command["command_id"], "context": command["target_context"],
                        "parameters": {"hunk": 0, "addr": offset, "name": name}, "evidence": {
                            "reason": "The existing typed record declares this exact WORD field.",
                            "source_evidence_refs": [row["row_key"]],
                        }})
    result = _http_batch(entries)
    assert result["ok"] is True
    metadata = json.loads(effective_metadata_text(typed_words.directory))
    assert metadata["data_block_layouts"] == before
    labels = {(item["addr"], item["name"]) for item in metadata["seeded_code_labels"]}
    assert set(zip((18, 26), names, strict=True)) <= labels
    assert not metadata["target_equates"]
    with effective_metadata_file(typed_words.directory) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(typed_words.source, metadata_path=metadata_path)
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            typed_words.source, metadata_path=metadata_path,
        )
        try:
            for offset, name in list(zip((18, 26), names, strict=True)):
                assert name + ":" in rendered
                symbols = artifact.query_payload(kind="symbols", section_index=0, source_offset=offset,
                                                 end_offset=offset + 1, limit=100)
                assert any(item["name"] == name and item["source_offset"] == offset
                           for item in symbols["items"])
                assert any(item["name"] == name and item.get("name_is_generated") is False
                           for item in symbols["items"])
            # Native symbol queries, rather than the accepted metadata alone,
            # must authorize these exact field anchors in the normal HTTP gate.
            _seed_c_listing_artifact(monkeypatch, "bloodwych", artifact)
            typed_words.artifact = artifact
            refs = _http_batch([_entry(typed_words, 6, 26, 18), _entry(typed_words, 14, 26, 18)])
            assert refs["ok"] is True
        finally:
            artifact.close()
    with effective_metadata_file(typed_words.directory) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(typed_words.source, metadata_path=metadata_path)
    assert f"\tdc.w {names[0]}-{names[1]}" in rendered
    assert rendered.count("; branch") == 2
    assert not json.loads(effective_metadata_text(typed_words.directory))["target_equates"]
    _round_trip(typed_words.directory, rendered, typed_words.original)
