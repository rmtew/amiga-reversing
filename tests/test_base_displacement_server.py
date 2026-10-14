"""Command and verification guards for canonical stored displacements."""
import json
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import server
from amiga_reversing.disasm.manual_actions import MANUAL_ACTION_LOG_FILE_NAME
from amiga_reversing.disasm.projects import ProjectKind
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def _setup(tmp_path, monkeypatch, *, raw=0xFFFC, base=8, target=4, names=True, row_raw=None):
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    records = [{"record": "manual_action_log_header", "version": 1, "target_identity": {}}]
    for i, (kind, key, payload) in enumerate([
        ("create_manual_data_block_layout", "data_block_layout", {"layout_id": "offsets", "hunk": 0,
         "source_start": 2, "source_end": 4, "default_unit": "word"}),
        ("set_manual_data_block_element", "data_block_element", {"layout_id": "offsets", "offset": 0,
         "width": 2, "kind": "scalar"}),
    ], 1):
        records.append({"record": "manual_action", "action_id": f"a{i}", "sequence": i,
                        "created_at": "2026-10-13T00:00:00+00:00", "kind": kind, key: payload})
    (tmp_path / MANUAL_ACTION_LOG_FILE_NAME).write_text("\n".join(json.dumps(r) for r in records) + "\n")
    ref = {"layout_id": "offsets", "offset": 0, "width": 2, "reference_kind": "base_displacement",
           "data_block_ref_id": "offsets:0", "source_value": raw, "signed": True,
           "base_locator": {"hunk": 0, "offset": base}, "target_hunk": 0, "target_offset": target,
           "target_locator": {"hunk": 0, "offset": target}, "xref_generation_mode": "bidirectional"}
    def query(**params):
        return {"items": ([{"source_offset": params["source_offset"], "section_index": 0,
                            "name": "base" if params["source_offset"] == base else "target"}] if names else [])}
    artifact = SimpleNamespace(row_for_source_offset=lambda **kw: {"start_offset": 2,
                               "bytes": f"{raw if row_raw is None else row_raw:04x}"}, query_payload=query)
    monkeypatch.setattr(server, "get_project", lambda _: SimpleNamespace(kind=ProjectKind.BINARY,
                        ready=True, target_dir=str(tmp_path)))
    monkeypatch.setattr(server, "_valid_c_listing_artifact", lambda _: artifact)
    monkeypatch.setattr(server, "target_catalog_manual_payload", lambda *args:
                        ("interpret_manual_data_block_element_ref", {"data_block_interpreted_ref": ref}))
    return ref, artifact


@pytest.mark.parametrize(("raw", "base", "target"), [(4, 4, 8), (0xFFFC, 8, 4), (0, 4, 4),
                                             (0x7FFF, 0, 32767), (0x8000, 32768, 0)])
def test_command_checks_encoded_bits_and_canonical_labels_without_runtime_mapping(tmp_path, monkeypatch, raw, base, target):
    ref, artifact = _setup(tmp_path, monkeypatch, raw=raw, base=base, target=target)
    artifact.source_for_runtime_address = lambda **kw: pytest.fail("displacement is not a runtime address")
    result = server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})
    assert result[0][1]["data_block_interpreted_ref"] == ref


@pytest.mark.parametrize(("change", "error"), [
    ({"source_value": 1}, "source_value must match"),
    ({"signed": False}, "signed16"), ({"width": 1}, "source_value must match|signed16"),
    ({"scale": 2}, "signed16"), ({"runtime_address": 0xFFFC}, "signed16"),
    ({"target_offset": 5}, "target must equal"), ({"target_hunk": 1}, "same-section"),
    ({"base_locator": {"hunk": 0, "offset": 0}}, "target must equal"),
])
def test_command_rejects_inconsistent_relation_before_append(tmp_path, monkeypatch, change, error):
    ref, _ = _setup(tmp_path, monkeypatch)
    ref.update(change)
    before = (tmp_path / MANUAL_ACTION_LOG_FILE_NAME).read_bytes()
    with pytest.raises(ValueError, match=error):
        server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})
    assert (tmp_path / MANUAL_ACTION_LOG_FILE_NAME).read_bytes() == before


def test_command_requires_existing_native_labels(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, names=False)
    with pytest.raises(ValueError, match="independently renderable"):
        server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})


def test_command_rejects_another_owner_at_the_same_span(tmp_path, monkeypatch):
    ref, _ = _setup(tmp_path, monkeypatch)
    original = json.loads(server.effective_metadata_text(tmp_path))
    original["manual_data_references"] = [{"owner_id": "other", "hunk": 0, "addr": 2, "size": 2}]
    monkeypatch.setattr(server, "effective_metadata_text", lambda _: json.dumps(original))
    with pytest.raises(ValueError, match="another owner"):
        server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})
    original["manual_data_references"][0]["owner_id"] = ref["data_block_ref_id"]
    server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})


@pytest.mark.parametrize("mode", ["bidirectional", "source_only", "none"])
@pytest.mark.parametrize("removed", [False, True])
def test_verifier_checks_relation_expression_and_owner_scoped_navigation(tmp_path, monkeypatch, mode, removed):
    from amiga_reversing import reversing_loop as loop
    ref, artifact = _setup(tmp_path, monkeypatch)
    ref["xref_generation_mode"] = mode
    native = {"owner_kind": "data_block_interpreted_ref", "owner_id": ref["data_block_ref_id"],
              "owner_layout_id": "offsets", "owner_element_offset": 0, "reference_role": "target",
              "target_section_index": 0, "target_offset": 4, "base_section_index": 0, "base_offset": 8,
              "source_value": 0xFFFC, "signed": True, "width": 2, "reference_kind": "base_displacement"}
    def query(**params):
        if params["kind"] == "symbols":
            return {"items": [{"name": "base" if params["source_offset"] == 8 else "target",
                               "source_offset": params["source_offset"], "section_index": 0}]}
        visible = not removed and mode != "none" and (params["direction"] != "incoming" or mode == "bidirectional")
        base_ref = {**native, "reference_role": "base", "target_offset": 8}
        refs = [native, base_ref] if params["direction"] == "outgoing" else [base_ref if params["source_offset"] == 8 else native]
        return {"items": refs if visible else []}
    artifact.query_payload = query
    artifact.row_for_source_offset = lambda **kw: {"text": "dc.w $FFFC" if removed else "dc.w target-base"}
    monkeypatch.setattr(loop, "_data_block_render_location", lambda *args, **kw: (0, 2))
    for layer in ("rendered_source", "xref_projection"):
        result = loop._verify_base_displacement_reference("synthetic", {}, "data.clear_ref" if removed else "data.ref",
                  ref, project_root=tmp_path, layer=layer)
        assert result["status"] == "passed", result
    if not removed and mode != "none":
        native["base_offset"] = 10
        result = loop._verify_base_displacement_reference("synthetic", {}, "data.ref", ref,
                                                          project_root=tmp_path, layer="xref_projection")
        assert result["status"] == "failed"


def test_verifier_rejects_numeric_or_wrong_base_output(tmp_path, monkeypatch):
    from amiga_reversing import reversing_loop as loop
    ref, artifact = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(loop, "_data_block_render_location", lambda *args, **kw: (0, 2))
    for text in ("dc.w $FFFC", "dc.w base-target", "dc.w target-other"):
        artifact.row_for_source_offset = lambda _text=text, **kw: {"text": _text}
        result = loop._verify_base_displacement_reference("synthetic", {}, "data.ref", ref,
                                                          project_root=tmp_path, layer="rendered_source")
        assert result["status"] == "failed"


def test_verifier_detects_missing_base_role_and_stale_incoming_after_clear(tmp_path, monkeypatch):
    from amiga_reversing import reversing_loop as loop
    ref, artifact = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(loop, "_data_block_render_location", lambda *args, **kw: (0, 2))
    native = {"owner_kind": "data_block_interpreted_ref", "owner_id": ref["data_block_ref_id"],
              "owner_layout_id": "offsets", "owner_element_offset": 0, "reference_role": "target",
              "target_section_index": 0, "target_offset": 4, "base_section_index": 0, "base_offset": 8,
              "source_value": 0xFFFC, "signed": True, "width": 2, "reference_kind": "base_displacement"}
    artifact.query_payload = lambda **kw: {"items": [native] if kw["source_offset"] != 8 else []}
    result = loop._verify_base_displacement_reference("synthetic", {}, "data.ref", ref,
                                                      project_root=tmp_path, layer="xref_projection")
    assert result["status"] == "failed"
    artifact.query_payload = lambda **kw: {"items": [native] if kw["direction"] == "incoming" else []}
    result = loop._verify_base_displacement_reference("synthetic", {}, "data.clear_ref", ref,
                                                      project_root=tmp_path, layer="xref_projection")
    assert result["status"] == "failed"


@pytest.mark.parametrize(("new_kind", "old_kind"), [("base_displacement", "absolute"), ("absolute", "base_displacement")])
def test_command_rejects_cross_kind_owner_collision_even_when_xrefs_disabled(tmp_path, monkeypatch, new_kind, old_kind):
    ref, _ = _setup(tmp_path, monkeypatch, raw=4, base=8, target=12)
    ref["reference_kind"] = new_kind
    other = {**ref, "reference_kind": old_kind, "data_block_ref_id": "other", "xref_generation_mode": "none"}
    state = {"data_block_layouts": [{"layout_id": "offsets", "hunk": 0, "source_start": 2}],
             "data_block_interpreted_refs": [other]}
    project = SimpleNamespace(kind=ProjectKind.BINARY, ready=True, target_dir=str(tmp_path), manual_state=state)
    monkeypatch.setattr(server, "get_project", lambda _: project)
    with pytest.raises(ValueError, match="another interpretation owner"):
        server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})
    other["data_block_ref_id"] = ref["data_block_ref_id"]
    server._validate_data_block_reference_owners(project, ref)
