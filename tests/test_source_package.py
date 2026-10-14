from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from amiga_reversing.disasm.source_package import (
    build_source_package,
    collect_package_includes,
    materialize_source_package,
    source_package_zip,
    validate_source_package,
    write_source_package,
)


def test_collect_includes_follows_mixed_literal_quotes_and_cycles(tmp_path: Path):
    sdk = tmp_path / "sdk"
    (sdk / "graphics").mkdir(parents=True)
    (sdk / "exec").mkdir()
    copper = b"    include 'exec/types.i' ; SDK dependency\n"
    types = b'    INCLUDE "graphics/copper.i"\n'
    (sdk / "graphics/copper.i").write_bytes(copper)
    (sdk / "exec/types.i").write_bytes(types)

    includes = collect_package_includes('INCLUDE "graphics/copper.i"\n', sdk)
    assert [(entry["path"], bytes.fromhex(entry["data_hex"])) for entry in includes] == [
        ("exec/types.i", types), ("graphics/copper.i", copper),
    ]


@pytest.mark.parametrize("operand", [
    "'exec/types.i\"", '"exec/types.i\'', "exec/types.i", "'exec/types.i' extra",
    "'../outside.i'", "'/outside.i'", "'exec/../outside.i'", "'exec/\\1.i'",
])
def test_collect_includes_refuses_ambiguous_or_unsafe_literals(tmp_path: Path, operand: str):
    with pytest.raises(ValueError, match="literal quoted INCLUDE paths|package relative path"):
        collect_package_includes(f"include {operand}\n", tmp_path)


def test_single_quoted_include_cannot_follow_sdk_symlink_outside_root(tmp_path: Path):
    sdk = tmp_path / "sdk"
    sdk.mkdir()
    outside = tmp_path / "outside.i"
    outside.write_text("private bytes")
    (sdk / "outside.i").symlink_to(outside)
    with pytest.raises(ValueError, match="escapes"):
        collect_package_includes("include 'outside.i'\n", sdk)


def package(*, assets=True):
    return build_source_package({
        "filename": "demo.s", "source_text": '\tincbin "assets/a.bin"\n' if assets else "\trts\n",
        "target": "demo", "assembler_profile": "vasm", "metadata_hash": "metadata",
        "target_identity_sha256": "original",
    }, [{"path": "assets/a.bin", "data_hex": "0001ff", "size": 3,
         "source_section_index": 0, "source_offset": 4, "classification": "bitmap"}] if assets else [], 3)


def test_repeatable_archive_and_manifest_bind_all_bytes(tmp_path: Path):
    value = package()
    blob = source_package_zip(value)
    assert blob == source_package_zip(package())
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        assert archive.namelist() == ["assets/a.bin", "demo.s", "manifest.json"]
        assert archive.read("assets/a.bin") == b"\0\1\xff"
        assert json.loads(archive.read("manifest.json")) == value["manifest"]
    entry = materialize_source_package(value, tmp_path / "fresh")
    assert entry.read_bytes() == validate_source_package(value)["demo.s"]
    changed = copy.deepcopy(value)
    changed["files"][0]["data_base64"] = base64.b64encode(b"modified").decode()
    with pytest.raises(ValueError, match="integrity"):
        materialize_source_package(changed, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


@pytest.mark.parametrize("path", ["../outside", "/absolute", "a/../b", "a\\b", "a//b", "CON.bin", "a/aux", "a."])
def test_package_rejects_nonportable_paths(path):
    value = package()
    value["files"][0]["path"] = path
    with pytest.raises(ValueError, match="path"):
        validate_source_package(value)


def test_regeneration_replaces_archive_without_stale_assets(tmp_path: Path):
    output = tmp_path / "export.zip"
    write_source_package(package(), output)
    previous = output.read_bytes()
    write_source_package(package(), output)
    assert output.read_bytes() == previous
    write_source_package(package(assets=False), output)
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == ["demo.s", "manifest.json"]


def test_modified_or_unowned_archive_is_preserved(tmp_path: Path):
    output = tmp_path / "export.zip"
    write_source_package(package(), output)
    with zipfile.ZipFile(output, "a") as archive:
        archive.writestr("user-notes.txt", "keep me")
    original = output.read_bytes()
    with pytest.raises(ValueError, match="modified"):
        write_source_package(package(assets=False), output)
    assert output.read_bytes() == original


def test_materialization_preserves_existing_artifacts_and_symlinks(tmp_path: Path):
    directory = tmp_path / "existing"
    directory.mkdir()
    (directory / "notes").write_text("keep")
    with pytest.raises(ValueError, match="empty"):
        materialize_source_package(package(), directory)
    link = tmp_path / "link"
    link.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match="empty"):
        materialize_source_package(package(), link)
    assert (directory / "notes").read_text() == "keep"


@pytest.mark.parametrize(("source", "asset"), [
    ("assets", "assets/a.bin"),
    ("ASSETS", "assets/a.bin"),
    ("demo.s", "manifest.json/asset.bin"),
    ("demo.s", "MANIFEST.JSON/asset.bin"),
])
@pytest.mark.parametrize("reverse_order", [False, True])
def test_file_directory_collisions_are_rejected_before_materialization(
    tmp_path: Path, source: str, asset: str, reverse_order: bool,
):
    value = package()
    remap = {"demo.s": source, "assets/a.bin": asset}
    for entry in value["files"] + value["manifest"]["files"]:
        entry["path"] = remap[entry["path"]]
    value["manifest"]["source"] = source
    value["sha256"] = hashlib.sha256(
        (json.dumps(value["manifest"], sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()
    ).hexdigest()
    if reverse_order:
        value["files"].reverse()
    destination = tmp_path / "invalid"
    with pytest.raises(ValueError, match="collision"):
        materialize_source_package(value, destination)
    assert not destination.exists()


def test_modified_manifest_is_preserved(tmp_path: Path):
    output = tmp_path / "export.zip"
    write_source_package(package(), output)
    with zipfile.ZipFile(output) as archive:
        entries = {p: archive.read(p) for p in archive.namelist()}
        comment = archive.comment
    manifest = json.loads(entries["manifest.json"])
    manifest["target"] = "user-edited"
    entries["manifest.json"] = json.dumps(manifest).encode()
    with zipfile.ZipFile(output, "w") as archive:
        archive.comment = comment
        for path, data in entries.items():
            archive.writestr(path, data)
    previous = output.read_bytes()
    with pytest.raises(ValueError, match="modified"):
        write_source_package(package(assets=False), output)
    assert output.read_bytes() == previous
