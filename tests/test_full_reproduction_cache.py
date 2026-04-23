from __future__ import annotations

import importlib.util
import json
import os
import time
from pathlib import Path
from types import ModuleType

from amiga_reversing.disasm.profile_set_targets import (
    BUILD_RUNTIME_FILES,
    PROFILE_SET_STAMP_FILE,
    ensure_profile_set_project,
)


def _load_full_repro_module() -> ModuleType:
    path = Path(__file__).with_name("test_full_reproduction_integration.py")
    spec = importlib.util.spec_from_file_location("full_repro_helpers_for_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resource_import_cache_hit_reports_status(monkeypatch, tmp_path: Path) -> None:
    full_repro = _load_full_repro_module()
    cache_root = tmp_path / "cache"
    project_root = tmp_path / "project"
    cache_info: dict[str, object] = {}
    failures: list[str] = []
    hydrated: list[tuple[Path, Path]] = []

    monkeypatch.setattr(full_repro, "RESOURCE_IMPORT_CACHE_ROOT", cache_root)
    monkeypatch.setattr(full_repro, "_resource_import_cache_stamp", lambda: {"stamp": "current"})
    monkeypatch.setattr(
        full_repro,
        "_read_resource_import_cache_stamp",
        lambda stamp_path: {
            "stamp": {"stamp": "current"},
            "target_names": ["target_a", "target_b"],
            "import_failures": ["warn"],
        },
    )
    monkeypatch.setattr(
        full_repro,
        "_hydrate_resource_import_cache",
        lambda cache_project_root, output_project_root: hydrated.append(
            (cache_project_root, output_project_root)
        ),
    )

    targets = full_repro._import_resource_disk_targets_from_cache(
        project_root,
        import_failures=failures,
        cache_info=cache_info,
    )

    assert targets == ["target_a", "target_b"]
    assert failures == ["warn"]
    assert hydrated == [(cache_root / "project", project_root)]
    assert cache_info["status"] == "hit"
    assert cache_info["enabled"] is True
    assert cache_info["target_count"] == 2
    assert cache_info["import_failure_count"] == 1
    assert "hydrate_seconds" in cache_info


def test_resource_import_cache_rebuild_reports_reason(monkeypatch, tmp_path: Path) -> None:
    full_repro = _load_full_repro_module()
    cache_info: dict[str, object] = {}

    monkeypatch.setattr(full_repro, "RESOURCE_IMPORT_CACHE_ROOT", tmp_path / "cache")
    monkeypatch.setattr(full_repro, "_resource_import_cache_stamp", lambda: {"stamp": "new"})
    monkeypatch.setattr(
        full_repro,
        "_read_resource_import_cache_stamp",
        lambda stamp_path: {"stamp": {"stamp": "old"}},
    )
    monkeypatch.setattr(
        full_repro,
        "_build_resource_import_cache",
        lambda stamp: {"stamp": stamp, "target_names": ["rebuilt"], "import_failures": []},
    )
    monkeypatch.setattr(full_repro, "_hydrate_resource_import_cache", lambda cache_root, project_root: None)

    targets = full_repro._import_resource_disk_targets_from_cache(
        tmp_path / "project",
        import_failures=[],
        cache_info=cache_info,
    )

    assert targets == ["rebuilt"]
    assert cache_info["status"] == "rebuilt"
    assert cache_info["rebuild_reason"] == "stamp_changed"
    assert "rebuild_seconds" in cache_info


def test_resource_import_cache_fallback_reports_error(monkeypatch, tmp_path: Path) -> None:
    full_repro = _load_full_repro_module()
    cache_info: dict[str, object] = {}

    monkeypatch.setattr(full_repro, "RESOURCE_IMPORT_CACHE_ROOT", tmp_path / "cache")
    monkeypatch.setattr(full_repro, "_resource_import_cache_stamp", lambda: {"stamp": "current"})

    def fail_read(stamp_path: Path) -> dict[str, object]:
        raise RuntimeError("bad cache")

    monkeypatch.setattr(full_repro, "_read_resource_import_cache_stamp", fail_read)

    targets = full_repro._import_resource_disk_targets_from_cache(
        tmp_path / "project",
        import_failures=[],
        cache_info=cache_info,
    )

    assert targets is None
    assert cache_info["status"] == "fallback_uncached"
    assert cache_info["error_type"] == "RuntimeError"
    assert cache_info["error"] == "bad cache"


def test_resource_import_cache_stamp_tracks_disk_runtime_not_c_source_noise() -> None:
    full_repro = _load_full_repro_module()

    labels = {
        path.relative_to(full_repro.PROJECT_ROOT).as_posix()
        for path in full_repro._resource_import_tool_files()
    }

    assert "src/build/platform_disk_lib.dll" in labels
    assert "src/platform_disk_lib.c" not in labels
    assert "src/platform_file_lib.c" not in labels
    assert "src/platform_common.c" not in labels


def test_resource_import_tool_stamp_uses_content_not_mtime(tmp_path: Path) -> None:
    full_repro = _load_full_repro_module()
    tool = tmp_path / "tool.py"
    tool.write_text("same", encoding="ascii")
    first = full_repro._tool_file_stamp(tool)

    os.utime(tool, (time.time() + 20, time.time() + 20))
    second = full_repro._tool_file_stamp(tool)

    assert second == first


def test_resource_import_tool_hash_normalizes_pe_timestamps(tmp_path: Path) -> None:
    full_repro = _load_full_repro_module()
    first = tmp_path / "first.dll"
    second = tmp_path / "second.dll"
    first.write_bytes(_minimal_pe_with_timestamps(0x11111111, 0x22222222))
    second.write_bytes(_minimal_pe_with_timestamps(0x33333333, 0x44444444))

    assert full_repro._tool_file_sha256(first) == full_repro._tool_file_sha256(second)

    changed = bytearray(second.read_bytes())
    changed[-1] = 1
    second.write_bytes(changed)
    assert full_repro._tool_file_sha256(first) != full_repro._tool_file_sha256(second)


def _minimal_pe_with_timestamps(coff_timestamp: int, debug_timestamp: int) -> bytes:
    data = bytearray(0x400)
    pe_offset = 0x80
    optional_offset = pe_offset + 24
    optional_size = 0xE0
    section_table = optional_offset + optional_size
    debug_rva = 0x200
    debug_file_offset = 0x300
    data[0:2] = b"MZ"
    data[0x3C:0x40] = pe_offset.to_bytes(4, "little")
    data[pe_offset:pe_offset + 4] = b"PE\0\0"
    data[pe_offset + 4:pe_offset + 6] = (0x8664).to_bytes(2, "little")
    data[pe_offset + 6:pe_offset + 8] = (1).to_bytes(2, "little")
    data[pe_offset + 8:pe_offset + 12] = coff_timestamp.to_bytes(4, "little")
    data[pe_offset + 20:pe_offset + 22] = optional_size.to_bytes(2, "little")
    data[optional_offset:optional_offset + 2] = (0x10B).to_bytes(2, "little")
    debug_directory = optional_offset + 96 + 6 * 8
    data[debug_directory:debug_directory + 4] = debug_rva.to_bytes(4, "little")
    data[debug_directory + 4:debug_directory + 8] = (28).to_bytes(4, "little")
    data[section_table:section_table + 8] = b".rdata\0\0"
    data[section_table + 8:section_table + 12] = (0x100).to_bytes(4, "little")
    data[section_table + 12:section_table + 16] = debug_rva.to_bytes(4, "little")
    data[section_table + 16:section_table + 20] = (0x100).to_bytes(4, "little")
    data[section_table + 20:section_table + 24] = debug_file_offset.to_bytes(4, "little")
    data[debug_file_offset + 4:debug_file_offset + 8] = debug_timestamp.to_bytes(4, "little")
    return bytes(data)


def test_full_repro_setup_summary_preserves_cache_info(tmp_path: Path) -> None:
    full_repro = _load_full_repro_module()
    report_path = tmp_path / "report.json"
    started = time.perf_counter()

    summary = full_repro._write_current_repro_summary(
        [],
        limit=None,
        project_root=tmp_path,
        report_path=report_path,
        target_timeout_seconds=180,
        worker_count=1,
        batch_size=1,
        suite_started_at=started,
        overall_started_at=started,
        setup_timing={
            "resource_import_seconds": 1.25,
            "resource_import_cache": {"enabled": True, "status": "hit"},
        },
    )

    assert summary["setup_timing"]["resource_import_cache"] == {
        "enabled": True,
        "status": "hit",
    }
    assert report_path.exists()


def test_profile_set_cache_reuse_refreshes_runtime_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_root = tmp_path / "profile_project" / "project"
    source_build = repo_root / "src" / "build"
    copied_build = project_root / "src" / "build"
    source_build.mkdir(parents=True)
    copied_build.mkdir(parents=True)
    for file_name in BUILD_RUNTIME_FILES:
        (source_build / file_name).write_bytes(f"new:{file_name}".encode("ascii"))
        (copied_build / file_name).write_bytes(f"old:{file_name}".encode("ascii"))
    (project_root / PROFILE_SET_STAMP_FILE).write_text(
        json.dumps(
            {
                "project_root": str(project_root),
                "target_names": ["target_a"],
                "selected_targets": ["target_a"],
                "import_failures": [],
            }
        ),
        encoding="utf-8",
    )

    project = ensure_profile_set_project(
        project_root,
        extraction_root=tmp_path / "profile_project",
        repo_root=repo_root,
    )

    assert project.project_root == project_root
    for file_name in BUILD_RUNTIME_FILES:
        assert (copied_build / file_name).read_bytes() == f"new:{file_name}".encode("ascii")
