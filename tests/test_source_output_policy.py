"""Persistent presentation policy uses ordinary actions and native projection."""
import json
from ctypes import c_void_p
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import restoration, source_rendering
from amiga_reversing.disasm.c_backend import CListingArtifact, _source_output_policy_from_metadata_path
from amiga_reversing.disasm.effective_metadata import effective_metadata_hash, effective_target_metadata
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_action, load_manual_projection
from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.target_metadata import SourceOutputPolicyMetadata, TargetMetadata, target_metadata_json_payload, write_target_metadata


@pytest.fixture
def policy_target(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    binary = tmp_path / "original.bin"
    binary.write_bytes(b"\x4e\x75")
    (target / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary", "address_model": "local_offset", "path": str(binary),
        "load_address": 0, "entrypoint": 0, "code_start_offset": 0,
    }))
    write_target_metadata(target, TargetMetadata(target_type="program", entry_register_seeds=()))
    return target, resolve_target_binary_source(target)


def configure(target, binary, **policy):
    kind, payload = target_catalog_manual_payload("target.source_output.configure", policy)
    return append_manual_action(target, kind=ManualActionKind(kind), payload=payload, binary_source=binary)


def test_artifact_policy_reads_backend_metadata_file_contract(tmp_path):
    path = tmp_path / "effective.json"
    path.write_text(json.dumps({"source_output_policy": {"mode": "binary_assets", "minimum_asset_size": 512}}))
    assert _source_output_policy_from_metadata_path(str(path)) == SourceOutputPolicyMetadata("binary_assets", 512)
    assert _source_output_policy_from_metadata_path("") == SourceOutputPolicyMetadata()


def test_default_policy_preserves_metadata_and_undo_restores_previous_effective_hash(policy_target):
    target, binary = policy_target
    before = effective_metadata_hash(target)
    assert "source_output_policy" not in target_metadata_json_payload(effective_target_metadata(target))
    first = configure(target, binary, mode="binary_assets", minimum_asset_size=256)
    assets_hash = effective_metadata_hash(target)
    assert assets_hash != before
    assert effective_target_metadata(target).source_output_policy == SourceOutputPolicyMetadata("binary_assets", 256)
    second = configure(target, binary, mode="inline")
    assert effective_metadata_hash(target) == before
    append_manual_action(target, kind=ManualActionKind.UNDO_ACTION,
                         payload={"undoes_action_id": second["action_id"]}, binary_source=binary)
    assert effective_metadata_hash(target) == assets_hash
    append_manual_action(target, kind=ManualActionKind.UNDO_ACTION,
                         payload={"undoes_action_id": first["action_id"]}, binary_source=binary)
    assert effective_metadata_hash(target) == before
    assert load_manual_projection(target).seeds == ()


@pytest.mark.parametrize("policy", [{"mode": "force"}, {"mode": "binary_assets", "minimum_asset_size": True},
                                    {"mode": "binary_assets", "minimum_asset_size": 0},
                                    {"mode": "binary_assets", "force": True}])
def test_invalid_presentation_policy_cannot_append(policy_target, policy):
    target, binary = policy_target
    with pytest.raises(ValueError, match="mode|minimum_asset_size|unsupported"):
        configure(target, binary, **policy)
    assert not (target / "manual_actions.jsonl").exists()


def test_normal_full_source_projection_uses_same_native_planner_and_explicit_inline_gate():
    artifact = CListingArtifact(None, c_void_p(), source_output_policy=SourceOutputPolicyMetadata("binary_assets", 512))
    calls = []
    artifact.inline_source_text_with_profile = lambda: ("dc.b $ff\n", {"backend": "amiga-raw"})
    def native(minimum):
        calls.append(minimum)
        return {"source_text": 'INCBIN "assets/a.bin"\n', "assets": [{"path": "assets/a.bin"}]}
    artifact.source_package_payload = native
    text, profile, package = artifact.source_projection_with_profile()
    assert text == 'INCBIN "assets/a.bin"\n'
    assert package["canonical_source_text"] == "dc.b $ff\n"
    assert artifact.source_text_with_profile() == (text, profile)
    assert calls == [512, 512]
    assert artifact.source_projection_with_profile(use_persisted_policy=False) == ("dc.b $ff\n", profile, None)
    assert calls == [512, 512]


def test_policy_command_requires_current_revision_before_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(restoration, "_paths", lambda _: SimpleNamespace(target_dir=tmp_path))
    monkeypatch.setattr(restoration, "revisions", lambda _: {"revision": "current", "subject_revision": "subject"})
    calls = []
    monkeypatch.setattr(restoration, "_server", lambda: SimpleNamespace(
        _execute_command_unchecked=lambda *args: calls.append(args)))
    with pytest.raises(ValueError, match="stale_revision"):
        restoration.execute("target", {"operation": "command", "command_id": "target.source_output.configure",
            "context": {"kind": "target"}, "parameters": {"mode": "binary_assets"}, "expected_revision": "old"})
    assert calls == []


def test_source_rendering_carries_companions_without_export_header(tmp_path, monkeypatch):
    (tmp_path / "canonical.s").write_text("dc.b $ff\n")
    native = {"canonical_source_text": "dc.b $ff\n", "source_text": 'INCBIN "assets/a.bin"\n',
              "minimum_asset_size": 256, "assets": [{"path": "assets/a.bin", "size": 1, "data_hex": "ff"}]}
    monkeypatch.setattr(source_rendering, "listing_artifact_source_projection_with_c_backend_profile",
        lambda *a, **kw: (native["source_text"], {"backend": "amiga-raw"}, native))
    monkeypatch.setattr(source_rendering, "effective_metadata_hash", lambda _: "metadata")
    result = source_rendering.render_source_from_binary_source(target_id="target", target_dir=tmp_path,
        binary_source=SimpleNamespace(read_bytes=lambda: b"\xff"), metadata_path=None, project_root=tmp_path)
    assert result.source_package["manifest"]["source"] == "canonical.s"
    assert result.source_package["manifest"]["files"][0]["kind"] == "asset"
    assert result.inline_source_text == "dc.b $ff\n"
    assert result.source_text == native["source_text"]
