from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

from amiga_reversing.disasm import source_package_publish as publisher
from amiga_reversing.disasm.source_package import build_source_package
from amiga_reversing.disasm.source_package_publish import (
    PUBLISH_MANIFEST,
    load_published_source_package,
    publish_source_package,
)


def package(*, assets: bool = True, source_text: str | None = None):
    return build_source_package({
        "filename": "demo.s", "source_text": source_text or (
            'include "exec/types.i"\nincbin "assets/a.bin"\n' if assets else "rts\n"),
        "target": "demo", "assembler_profile": "vasm", "metadata_hash": "metadata",
        "target_identity_sha256": "binary",
    }, [{"path": "assets/a.bin", "size": 3, "data_hex": "0001ff"}] if assets else [], 3,
        includes=[{"path": "exec/types.i", "size": 4, "data_hex": b"SDK\n".hex(),
                   "kind": "include"}] if assets else [])


def inventory(directory: Path):
    return {str(p.relative_to(directory)): p.read_bytes()
            for p in directory.rglob("*") if p.is_file()}


def test_publish_in_populated_target_is_deterministic_and_cleans_only_owned_files(tmp_path: Path):
    (tmp_path / "notes.txt").write_text("keep")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/user.bin").write_bytes(b"user")
    result = publish_source_package(package(), tmp_path)
    assert result == tmp_path / "demo.s"
    before = inventory(tmp_path)
    publish_source_package(package(), tmp_path)
    assert inventory(tmp_path) == before
    manifest = json.loads((tmp_path / PUBLISH_MANIFEST).read_bytes())
    assert manifest["manifest"] == package()["manifest"]
    assert manifest["sha256"] == package()["sha256"]
    publish_source_package(package(assets=False), tmp_path)
    assert inventory(tmp_path).keys() == {"demo.s", PUBLISH_MANIFEST, "notes.txt", "assets/user.bin"}
    assert (tmp_path / "demo.s").read_text() == "rts\n"
    assert not (tmp_path / "exec").exists()


@pytest.mark.parametrize("edit_obsolete", [False, True])
def test_asset_rename_preserves_native_identity_and_removes_only_unchanged_owned_path(
    tmp_path: Path, edit_obsolete: bool,
):
    def named_package(name: str):
        return build_source_package({
            "filename": "demo.s", "source_text": f'{name}:\n    INCBIN "assets/{name}.bin"\n',
            "target": "demo", "assembler_profile": "vasm", "metadata_hash": "metadata",
            "target_identity_sha256": "binary",
        }, [{"path": f"assets/{name}.bin", "name": name, "name_is_generated": False,
             "asset_id": "section-0001-offset-00002000-size-00000003",
             "source_section_index": 1, "source_offset": 8192, "size": 3,
             "data_hex": "0001ff"}], 3)

    initial = named_package("title_sound")
    renamed = named_package("intro_sound")
    publish_source_package(initial, tmp_path)
    unrelated = tmp_path / "assets/user.bin"
    unrelated.write_bytes(b"user")
    obsolete = tmp_path / "assets/title_sound.bin"
    if edit_obsolete:
        obsolete.write_bytes(b"user edit")
        before = inventory(tmp_path)
        with pytest.raises(ValueError, match="modified"):
            publish_source_package(renamed, tmp_path)
        assert inventory(tmp_path) == before
    else:
        publish_source_package(renamed, tmp_path)
        assert not obsolete.exists()
        assert (tmp_path / "assets/intro_sound.bin").read_bytes() == b"\0\1\xff"
        assert unrelated.read_bytes() == b"user"
        assert load_published_source_package(tmp_path) == renamed
        old_asset = next(row for row in initial["manifest"]["files"] if row["kind"] == "asset")
        new_asset = next(row for row in renamed["manifest"]["files"] if row["kind"] == "asset")
        assert old_asset["asset_id"] == new_asset["asset_id"]
        assert old_asset["sha256"] == new_asset["sha256"]
        before = inventory(tmp_path)
        publish_source_package(renamed, tmp_path)
        assert inventory(tmp_path) == before


@pytest.mark.parametrize("proof", ["text", "hash"])
def test_initial_canonical_takeover_requires_exact_expected_bytes(tmp_path: Path, proof: str):
    source = tmp_path / "demo.s"
    source.write_text("rts\n")
    before = inventory(tmp_path)
    with pytest.raises(ValueError, match="expected source"):
        publish_source_package(package(), tmp_path)
    with pytest.raises(ValueError, match="differs"):
        publish_source_package(package(), tmp_path, expected_source_text="edited\n")
    assert inventory(tmp_path) == before
    options = {"expected_source_text": "rts\n"} if proof == "text" else {
        "expected_source_sha256": hashlib.sha256(b"rts\n").hexdigest()}
    publish_source_package(package(), tmp_path, **options)
    assert b"incbin" in source.read_bytes()


@pytest.mark.parametrize("edited", ["demo.s", "assets/a.bin", "exec/types.i", PUBLISH_MANIFEST])
def test_all_owned_edits_prevent_any_mutation_even_during_inline_cleanup(tmp_path: Path, edited: str):
    publish_source_package(package(), tmp_path)
    (tmp_path / edited).write_bytes(b"edited")
    before = inventory(tmp_path)
    with pytest.raises(ValueError, match="modified"):
        publish_source_package(package(assets=False), tmp_path, expected_source_text="edited")
    assert inventory(tmp_path) == before


def test_missing_obsolete_owned_file_is_refused(tmp_path: Path):
    publish_source_package(package(), tmp_path)
    (tmp_path / "exec/types.i").unlink()
    before = inventory(tmp_path)
    with pytest.raises(ValueError, match="modified"):
        publish_source_package(package(assets=False), tmp_path)
    assert inventory(tmp_path) == before


@pytest.mark.parametrize("collision", ["assets/a.bin", "ASSETS", "assets/A.BIN", "exec", PUBLISH_MANIFEST])
def test_unowned_file_and_case_collisions_are_preserved(tmp_path: Path, collision: str):
    path = tmp_path / collision
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"user")
    before = inventory(tmp_path)
    with pytest.raises(ValueError, match="collision|modified"):
        publish_source_package(package(), tmp_path)
    assert inventory(tmp_path) == before


@pytest.mark.parametrize("linked", ["demo.s", "assets", "assets/a.bin", "exec/types.i", PUBLISH_MANIFEST])
def test_destination_symlinks_are_refused(tmp_path: Path, linked: str):
    target = tmp_path / "target"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"user")
    path = target / linked
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink|modified"):
        publish_source_package(package(), target, expected_source_text="user")
    assert path.is_symlink()
    assert outside.read_bytes() == b"user"
    assert not (target / "demo.s").exists() or linked == "demo.s"


def test_owned_symlink_and_target_directory_symlink_are_refused(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    publish_source_package(package(), target)
    asset = target / "assets/a.bin"
    outside = tmp_path / "outside"
    outside.write_bytes(asset.read_bytes())
    asset.unlink()
    asset.symlink_to(outside)
    with pytest.raises(ValueError, match="modified"):
        publish_source_package(package(assets=False), target)
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        publish_source_package(package(), link)


def test_invalid_new_package_is_rejected_before_target_mutation(tmp_path: Path):
    publish_source_package(package(), tmp_path)
    invalid = copy.deepcopy(package())
    invalid["files"][0]["data_base64"] = "AAAA"
    before = inventory(tmp_path)
    with pytest.raises(ValueError, match="integrity"):
        publish_source_package(invalid, tmp_path)
    assert inventory(tmp_path) == before


@pytest.mark.parametrize("failure_at", [2, 3, 4])
def test_failed_install_rolls_back_all_owned_bytes_and_new_directories(
    tmp_path: Path, monkeypatch, failure_at: int,
):
    (tmp_path / "demo.s").write_text("rts\n")
    (tmp_path / "notes.txt").write_text("keep")
    before = inventory(tmp_path)
    original_replace = os.replace
    calls = 0

    def fail_once(source, destination):
        nonlocal calls
        calls += 1
        if calls == failure_at:
            raise OSError("injected install failure")
        original_replace(source, destination)

    monkeypatch.setattr(publisher.os, "replace", fail_once)
    with pytest.raises(OSError, match="injected"):
        publish_source_package(package(), tmp_path, expected_source_text="rts\n")
    assert inventory(tmp_path) == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["demo.s", "notes.txt"]


def test_manifest_commit_failure_restores_obsolete_owned_companions(tmp_path: Path, monkeypatch):
    publish_source_package(package(), tmp_path)
    before = inventory(tmp_path)
    original_replace = os.replace
    failed = False

    def fail_manifest_once(source, destination):
        nonlocal failed
        if Path(destination).name == PUBLISH_MANIFEST and not failed:
            failed = True
            raise OSError("injected manifest failure")
        original_replace(source, destination)

    monkeypatch.setattr(publisher.os, "replace", fail_manifest_once)
    with pytest.raises(OSError, match="injected"):
        publish_source_package(package(assets=False), tmp_path)
    assert inventory(tmp_path) == before


def test_package_cannot_claim_publisher_manifest(tmp_path: Path):
    value = build_source_package({
        "filename": PUBLISH_MANIFEST, "source_text": "rts\n", "target": "demo",
        "assembler_profile": "vasm", "metadata_hash": "metadata",
        "target_identity_sha256": "binary",
    }, [], 3)
    with pytest.raises(ValueError, match="Reserved"):
        publish_source_package(value, tmp_path)
    assert not list(tmp_path.iterdir())


def test_loader_returns_exact_package_and_rejects_modified_owned_bytes(tmp_path: Path):
    with pytest.raises(ValueError, match="missing"):
        load_published_source_package(tmp_path)
    value = package()
    publish_source_package(value, tmp_path)
    (tmp_path / "notes.txt").write_text("keep")
    assert load_published_source_package(tmp_path) == value
    (tmp_path / "assets/a.bin").write_bytes(b"modified")
    with pytest.raises(ValueError, match="modified"):
        load_published_source_package(tmp_path)


@pytest.mark.parametrize("protected", [
    "target_metadata.json", "binary.bin", "manual_actions.jsonl", "decision_journal.jsonl",
    "target_state.json", "decision_verifier_artifacts.json", "TARGET_METADATA.JSON/asset.bin",
])
def test_package_cannot_claim_protected_target_state(tmp_path: Path, protected: str):
    value = build_source_package({
        "filename": "demo.s", "source_text": "rts\n", "target": "demo",
        "assembler_profile": "vasm", "metadata_hash": "metadata",
        "target_identity_sha256": "binary",
    }, [{"path": protected, "data_hex": "01", "size": 1}], 3)
    with pytest.raises(ValueError, match="Reserved"):
        publish_source_package(value, tmp_path)
    assert not list(tmp_path.iterdir())


def test_loader_rejects_even_hash_valid_protected_target_ownership(tmp_path: Path):
    value = package()
    publish_source_package(value, tmp_path)
    for record in value["manifest"]["files"]:
        if record["path"] == "assets/a.bin":
            record["path"] = "target_metadata.json"
    (tmp_path / "target_metadata.json").write_bytes(b"\0\1\xff")
    value["sha256"] = hashlib.sha256(
        (json.dumps(value["manifest"], sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()
    ).hexdigest()
    (tmp_path / PUBLISH_MANIFEST).write_text(json.dumps({
        "manifest": value["manifest"], "sha256": value["sha256"],
    }))
    before = inventory(tmp_path)
    with pytest.raises(ValueError, match="modified"):
        publish_source_package(package(assets=False), tmp_path)
    assert inventory(tmp_path) == before
