"""A manifest cannot authorize unlisted bytes or substitute a native proof."""

import json
from types import SimpleNamespace

import pytest
from test_memory_regions import region

from amiga_reversing.disasm import derived_artifact as module
from amiga_reversing.disasm.memory_regions import build_derived_artifact


def contract(tmp_path, monkeypatch):
    original = bytes.fromhex("4a390000397c4e75")
    derived = bytes.fromhex("4a3900c7f0004e75")
    monkeypatch.setattr(
        module, "resolve_project_paths", lambda _: SimpleNamespace(binary_source=None)
    )
    monkeypatch.setattr(module, "read_binary_source_bytes", lambda _: original)
    manifest = {
        "schema_version": 1,
        "kind": "fixed_width_memory_relocation",
        "target_id": "fixture",
        "original_sha256": module.sha256(original),
        "artifact_sha256": module.sha256(derived),
        "artifact_file": "payload.bin",
        "analysis_subject_revision": "a" * 64,
        "region": region(),
        "placement": {
            "runtime_address": 0xC7F000,
            "memory_class": "slow",
            "reservation": "exec_allocabs",
        },
        "native_plan_sha256": "b" * 64,
        "rewrite_ledger": [
            {
                "section_index": 0,
                "source_offset": 0,
                "operand_index": 0,
                "region_offset": 0,
                "before": original[:6].hex(),
                "after": derived[:6].hex(),
            }
        ],
    }
    path = tmp_path / "manifest.json"
    (tmp_path / "payload.bin").write_bytes(derived)
    return path, manifest


def test_exact_manifest_validates_all_changed_bytes(tmp_path, monkeypatch):
    path, manifest = contract(tmp_path, monkeypatch)
    path.write_text(json.dumps(manifest))
    assert module.validate_manifest(path, "fixture")[1] == tmp_path / "payload.bin"
    # Rehashing an extra modification still fails the exact ledger check.
    data = (tmp_path / "payload.bin").read_bytes()[:-1] + b"\x74"
    (tmp_path / "payload.bin").write_bytes(data)
    manifest["artifact_sha256"] = module.sha256(data)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="outside its exact rewrite ledger"):
        module.validate_manifest(path, "fixture")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("region", {}, "definition fields"),
        ("placement", None, "placement"),
        ("artifact_file", "../payload.bin", "sibling"),
        ("native_plan_sha256", None, "identity hash"),
        ("analysis_subject_revision", 123, "identity hash"),
        ("original_sha256", "0" * 64, "original target identity"),
        ("artifact_sha256", "0" * 64, "payload identity"),
        ("rewrite_ledger", [], "nonempty"),
    ],
)
def test_malformed_and_stale_identity_refused(
    tmp_path, monkeypatch, field, value, message
):
    path, manifest = contract(tmp_path, monkeypatch)
    manifest[field] = value
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=message):
        module.validate_manifest(path, "fixture")


def test_native_proof_is_recomputed_and_manifest_cannot_assert_closure(
    tmp_path, monkeypatch
):
    path, manifest = contract(tmp_path, monkeypatch)
    fake = SimpleNamespace(
        memory_regions_payload=lambda: {"items": [region()]},
        memory_region_plan=lambda *args: {
            "status": "refused",
            "rewrite_ledger": manifest["rewrite_ledger"],
        },
    )
    with pytest.raises(ValueError, match="closed native relocation proof"):
        module.verify_native_binding(manifest, fake)
    manifest["region"]["size"] = 256
    with pytest.raises(ValueError, match="region definition is stale"):
        module.verify_native_binding(manifest, fake)


def test_refused_plan_build_writes_nothing(tmp_path):
    with pytest.raises(ValueError, match="no artifact written"):
        build_derived_artifact(
            "invalid-target",
            None,
            {"status": "refused", "unresolved_obligations": 1},
            "a" * 64,
        )
    assert not list(tmp_path.iterdir())
