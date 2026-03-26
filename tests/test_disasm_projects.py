from __future__ import annotations

import json
from pathlib import Path

import pytest

from disasm.binary_source import resolve_target_binary_source
from disasm.project_paths import resolve_project_paths
from disasm.projects import (
    build_project_session,
    create_project,
    dedupe_project_name,
    delete_project,
    derive_project_name,
    get_project,
    list_projects,
    mark_project_opened,
)


def _disk_manifest_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "disk_id": "demo_disk",
        "source_path": "bin/demo.adf",
        "source_sha256": "deadbeef",
        "bootblock_target_name": "amiga_disk_demo_disk__amiga_raw_bootblock",
        "bootblock_target_path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock",
        "analysis": {
            "disk_info": {
                "path": "demo.adf",
                "size": 901120,
                "variant": "DD",
                "total_sectors": 1760,
                "sectors_per_track": 11,
                "is_dos": True,
            },
            "boot_block": {
                "magic_ascii": "DOS",
                "is_dos": True,
                "flags_byte": 1,
                "fs_type": "FFS",
                "fs_description": "DOS\\1 - Fast File System",
                "checksum": "0x00000000",
                "checksum_valid": True,
                "rootblock_ptr": 880,
                "bootcode_size": 1012,
                "bootcode_has_code": False,
                "bootcode_entropy": 0.0,
            },
            "filesystem": {
                "type": "FFS",
                "volume_name": "Demo",
                "directories": 1,
                "files": 1,
                "total_file_size": 1234,
            },
        },
        "imported_targets": [
            {
                "target_name": "amiga_disk_demo_disk__amiga_hunk_run_12345678",
                "target_path": "targets/amiga_disk_demo_disk/targets/amiga_hunk_run_12345678",
                "entry_path": "c/Run",
                "binary_path": "bin/demo.adf::c/Run",
                "target_type": "program",
            }
        ],
    }


def _dos_magic_non_dos_manifest_payload() -> dict[str, object]:
    payload = _disk_manifest_payload()
    analysis = payload["analysis"]
    assert isinstance(analysis, dict)
    analysis.pop("filesystem", None)
    analysis["non_dos"] = {
        "description": "Custom format disk (non-AmigaDOS)",
        "bootcode_present": True,
        "dos_magic_without_filesystem": True,
        "filesystem_parse_error": "Unexpected root hash table size",
    }
    return payload


def test_resolve_project_paths_uses_recorded_binary_path(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("")
    binary_path = bin_dir / "DemoGame"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "hunk_file",
        "path": str(binary_path),
    }))
    (target_dir / "DemoGame.s").write_text("; output\n")

    resolved = resolve_project_paths("demo", project_root=project_root)

    assert resolved.binary_source.kind == "hunk_file"
    assert resolved.binary_source.path == binary_path
    assert resolved.binary_source.display_path == str(binary_path)
    assert resolved.output_path == target_dir / "DemoGame.s"
    assert resolved.kind == "binary"


def test_resolve_project_paths_supports_disk_entry_binary_source(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_hunk_run_12345678"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("")
    adf_path = bin_dir / "demo.adf"
    adf_path.write_bytes(b"demo")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "disk_entry",
        "disk_id": "demo_disk",
        "disk_path": "bin/demo.adf",
        "entry_path": "c/Run",
        "parent_disk_id": "demo_disk",
    }))

    resolved = resolve_project_paths("amiga_disk_demo_disk__amiga_hunk_run_12345678", project_root=project_root)

    assert resolved.binary_source.kind == "disk_entry"
    assert resolved.binary_source.adf_path == adf_path
    assert resolved.binary_source.entry_path == "c/Run"
    assert resolved.binary_source.analysis_cache_path == target_dir / "binary.analysis"


def test_resolve_project_paths_supports_raw_binary_source(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("")
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x00" * 0x0C + b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000C,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))

    resolved = resolve_project_paths("amiga_disk_demo_disk__amiga_raw_bootblock", project_root=project_root)

    assert resolved.binary_source.kind == "raw_binary"
    assert resolved.binary_source.path == binary_path
    assert resolved.binary_source.load_address == 0x70000
    assert resolved.binary_source.entrypoint == 0x7000C
    assert resolved.binary_source.code_start_offset == 0x0C


def test_resolve_target_binary_source_rejects_non_object_descriptor(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "source_binary.json").write_text("null", encoding="utf-8")

    with pytest.raises(TypeError, match="Expected JSON object"):
        resolve_target_binary_source(target_dir)


def test_resolve_target_binary_source_rejects_raw_code_start_outside_file(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": str(binary_path),
                "load_address": 0x70000,
                "entrypoint": 0x70000,
                "code_start_offset": 2,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="code_start_offset 0x2 lies outside file of 2 bytes"):
        resolve_target_binary_source(target_dir)


def test_resolve_target_binary_source_rejects_raw_entrypoint_outside_code_range(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x00" * 0x0C + b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": str(binary_path),
                "load_address": 0x70000,
                "entrypoint": 0x7000E,
                "code_start_offset": 0x0C,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"entrypoint 0x7000E lies outside code range 0x7000C\.\.0x7000D"):
        resolve_target_binary_source(target_dir)


def test_resolve_project_paths_allows_missing_entities_when_requested(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x00" * 0x0C + b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000C,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))

    resolved = resolve_project_paths("amiga_disk_demo_disk__amiga_raw_bootblock", project_root=project_root, require_entities=False)

    assert resolved.entities_path == target_dir / "entities.jsonl"
    assert resolved.binary_source.kind == "raw_binary"


def test_resolve_project_paths_rejects_disk_project_name(tmp_path: Path) -> None:
    disk_dir = tmp_path / "targets" / "amiga_disk_demo"
    disk_dir.mkdir(parents=True)
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))

    with pytest.raises(ValueError, match="Disk project"):
        resolve_project_paths("amiga_disk_demo", project_root=tmp_path)


def test_list_projects_includes_unready_binary_project(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("")
    (target_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))

    projects = list_projects(project_root=project_root)

    assert len(projects) == 1
    assert projects[0].id == "demo"
    assert projects[0].kind == "binary"
    assert projects[0].ready is False
    assert projects[0].binary_path is None
    assert projects[0].parent_project_id is None
    assert projects[0].created_at
    assert projects[0].updated_at


def test_list_projects_includes_disk_project(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))

    projects = list_projects(project_root=project_root)

    assert len(projects) == 1
    assert projects[0].id == "amiga_disk_demo_disk"
    assert projects[0].kind == "disk"
    assert projects[0].manifest_path == str(disk_dir / "manifest.json")
    assert projects[0].target_count == 2
    assert projects[0].ready is False
    assert projects[0].disk_type == "DOS"


def test_list_projects_hides_imported_disk_child_targets(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))
    child_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_hunk_run_12345678"
    child_dir.mkdir(parents=True)
    (child_dir / "entities.jsonl").write_text("")
    (child_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    bootblock_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    bootblock_dir.mkdir(parents=True)
    (bootblock_dir / "entities.jsonl").write_text("")
    (bootblock_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    (bootblock_dir / "binary.bin").write_bytes(b"\x4e\x75")
    (bootblock_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000C,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))
    (child_dir / "source_binary.json").write_text(json.dumps({
        "kind": "disk_entry",
        "disk_id": "demo_disk",
        "disk_path": "bin/demo.adf",
        "entry_path": "c/Run",
        "parent_disk_id": "demo_disk",
    }))

    projects = list_projects(project_root=project_root)

    assert [project.id for project in projects] == ["amiga_disk_demo_disk"]


def test_list_projects_requires_disk_manifest(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_broken_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "created_at": "2026-03-25T00:00:00+00:00",
                "updated_at": "2026-03-25T00:00:00+00:00",
            }
        )
    )

    with pytest.raises(FileNotFoundError, match="Missing manifest.json for disk project: amiga_disk_broken_disk"):
        list_projects(project_root=project_root)


def test_get_project_reads_disk_project(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))

    project = get_project("amiga_disk_demo_disk", project_root=project_root)

    assert project.name == "demo_disk"
    assert project.kind == "disk"
    assert project.source_path == "bin/demo.adf"
    assert project.disk_type == "DOS"
    assert project.parent_project_id is None


def test_get_project_marks_dos_magic_without_filesystem_as_non_dos(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    (disk_dir / "manifest.json").write_text(json.dumps(_dos_magic_non_dos_manifest_payload()))

    project = get_project("amiga_disk_demo_disk", project_root=project_root)

    assert project.disk_type == "non-DOS"


def test_get_project_sets_parent_project_for_disk_entry_target(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_hunk_run_12345678"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir()
    (target_dir / "entities.jsonl").write_text("")
    (target_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    (target_dir / "binary.analysis").write_text("")
    adf_path = bin_dir / "demo.adf"
    adf_path.write_bytes(b"demo")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "disk_entry",
        "disk_id": "demo_disk",
        "disk_path": "bin/demo.adf",
        "entry_path": "c/Run",
        "parent_disk_id": "demo_disk",
    }))

    project = get_project("amiga_disk_demo_disk__amiga_hunk_run_12345678", project_root=project_root)

    assert project.parent_project_id == "amiga_disk_demo_disk"


def test_build_project_session_supports_raw_binary_target(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("")
    (target_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    binary_path = target_dir / "binary.bin"
    binary = bytearray(24)
    binary[12:24] = bytes.fromhex("337c0002001c4eaefe384e75")
    binary_path.write_bytes(binary)
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000C,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))
    (target_dir / "target_metadata.json").write_text(json.dumps({
        "target_type": "bootblock",
        "entry_register_seeds": [
            {
                "register": "A6",
                "kind": "library_base",
                "note": "ExecBase",
                "library_name": "exec.library",
                "struct_name": "LIB",
                "context_name": None,
            },
            {
                "register": "A1",
                "kind": "struct_ptr",
                "note": "IOStdReq",
                "library_name": None,
                "struct_name": "IO",
                "context_name": "trackdisk.device",
            },
        ],
        "bootblock": {
            "magic_ascii": "DOS",
            "flags_byte": 0,
            "fs_description": "DOS\\0 - OFS",
            "checksum": "0x00000000",
            "checksum_valid": True,
            "rootblock_ptr": 880,
            "bootcode_offset": 0x0C,
            "bootcode_size": 1012,
            "load_address": 0x70000,
            "entrypoint": 0x7000C,
        },
        "resident": None,
        "library": None,
    }))

    session = build_project_session("amiga_disk_demo_disk__amiga_raw_bootblock", project_root=project_root)

    assert len(session.hunk_sessions) == 1
    assert session.hunk_sessions[0].base_addr == 0x0C
    assert session.hunk_sessions[0].code_start == 0x0C
    assert session.hunk_sessions[0].labels[0x0C] == "boot_entry"


def test_build_project_session_requires_metadata_for_raw_binary_target(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("")
    (target_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    binary_path = target_dir / "binary.bin"
    binary = bytearray(16)
    binary[12:14] = bytes.fromhex("4e75")
    binary_path.write_bytes(binary)
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000E,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))

    with pytest.raises(ValueError, match="Missing target_metadata.json"):
        build_project_session("amiga_disk_demo_disk__amiga_raw_bootblock", project_root=project_root)


def test_create_project_creates_entities_file(tmp_path: Path) -> None:
    project = create_project("demo", project_root=tmp_path)

    assert project.id == "demo"
    assert project.kind == "binary"
    assert (tmp_path / "targets" / "demo" / "entities.jsonl").exists()
    metadata = json.loads((tmp_path / "targets" / "demo" / ".project.json").read_text())
    assert metadata["schema_version"] == 1
    assert metadata["created_at"] == project.created_at
    assert metadata["updated_at"] == project.updated_at


def test_derive_project_name_uses_filename_stem() -> None:
    assert derive_project_name("Bloodwych (1990).adf") == "amiga_hunk_bloodwych-1990"


def test_dedupe_project_name_suffixes_existing_binary_and_disk_projects(tmp_path: Path) -> None:
    create_project("demo", project_root=tmp_path)
    disk_dir = tmp_path / "targets" / "demo-2"
    disk_dir.mkdir(parents=True)
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))

    assert dedupe_project_name("demo", project_root=tmp_path) == "demo-3"


def test_mark_project_opened_records_recent_timestamp_for_binary_and_disk(tmp_path: Path) -> None:
    create_project("demo", project_root=tmp_path)
    disk_dir = tmp_path / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))

    binary_project = mark_project_opened("demo", project_root=tmp_path)
    disk_project = mark_project_opened("amiga_disk_demo_disk", project_root=tmp_path)
    state = json.loads((tmp_path / "targets" / ".browser_state.json").read_text())

    assert binary_project.last_opened == state["recent_projects"]["demo"]
    assert disk_project.last_opened == state["recent_projects"]["amiga_disk_demo_disk"]


def test_list_projects_orders_by_most_recently_opened(tmp_path: Path) -> None:
    create_project("older", project_root=tmp_path)
    create_project("newer", project_root=tmp_path)
    mark_project_opened("older", project_root=tmp_path)
    mark_project_opened("newer", project_root=tmp_path)

    projects = list_projects(project_root=tmp_path)

    assert [project.id for project in projects] == ["newer", "older"]


def test_delete_binary_project_removes_target_dir_and_state(tmp_path: Path) -> None:
    create_project("demo", project_root=tmp_path)
    mark_project_opened("demo", project_root=tmp_path)

    delete_project("demo", project_root=tmp_path)

    assert not (tmp_path / "targets" / "demo").exists()
    state = json.loads((tmp_path / "targets" / ".browser_state.json").read_text())
    assert "demo" not in state["recent_projects"]


def test_delete_disk_project_removes_manifest_targets_and_source(tmp_path: Path) -> None:
    targets_dir = tmp_path / "targets"
    bin_dir = tmp_path / "bin" / "uploads"
    targets_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    source_path = bin_dir / "demo.adf"
    source_path.write_bytes(b"demo")
    disk_dir = targets_dir / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    imported_dir = targets_dir / "amiga_disk_demo_disk" / "targets" / "amiga_hunk_run_12345678"
    imported_dir.mkdir(parents=True)
    (imported_dir / "entities.jsonl").write_text("")
    (imported_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    (imported_dir / "source_binary.json").write_text(json.dumps({
        "kind": "disk_entry",
        "disk_id": "demo_disk",
        "disk_path": "bin/uploads/demo.adf",
        "entry_path": "c/Run",
        "parent_disk_id": "demo_disk",
    }))
    bootblock_dir = targets_dir / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    bootblock_dir.mkdir(parents=True)
    (bootblock_dir / "entities.jsonl").write_text("")
    (bootblock_dir / ".project.json").write_text(json.dumps({
        "schema_version": 1,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
    }))
    (bootblock_dir / "binary.bin").write_bytes(b"\x00" * 0x0C + b"\x4e\x75")
    (bootblock_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000C,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))
    payload = _disk_manifest_payload()
    payload["source_path"] = "bin/uploads/demo.adf"
    (disk_dir / "manifest.json").write_text(json.dumps(payload))
    mark_project_opened("amiga_disk_demo_disk", project_root=tmp_path)
    mark_project_opened("amiga_disk_demo_disk__amiga_hunk_run_12345678", project_root=tmp_path)
    mark_project_opened("amiga_disk_demo_disk__amiga_raw_bootblock", project_root=tmp_path)

    delete_project("amiga_disk_demo_disk", project_root=tmp_path)

    assert not disk_dir.exists()
    assert not imported_dir.exists()
    assert not bootblock_dir.exists()
    assert not source_path.exists()
    state = json.loads((targets_dir / ".browser_state.json").read_text())
    assert "amiga_disk_demo_disk" not in state["recent_projects"]
    assert "amiga_disk_demo_disk__amiga_hunk_run_12345678" not in state["recent_projects"]
    assert "amiga_disk_demo_disk__amiga_raw_bootblock" not in state["recent_projects"]


def test_get_project_requires_project_metadata(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("")

    with pytest.raises(FileNotFoundError, match=r"Missing \.project\.json for project: demo"):
        get_project("demo", project_root=tmp_path)


def test_list_projects_requires_project_metadata(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("")

    with pytest.raises(FileNotFoundError, match=r"Missing \.project\.json for project: demo"):
        list_projects(project_root=tmp_path)
