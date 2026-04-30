from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest

from amiga_reversing.amiga_disk.models import DiskManifest
from amiga_reversing.amiga_disk.project import create_disk_project
from amiga_reversing.disasm.binary_source import write_source_descriptor
from amiga_reversing.disasm.c_backend import inspect_disk_with_c_backend
from amiga_reversing.disasm.project_ids import (
    ensure_safe_project_id,
    normalize_filename_stem,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import create_project_at_path
from amiga_reversing.disasm.reproduction_sweep import (
    crash_record,
    format_reproduction_sweep_score,
    import_failure_record,
    record_from_reproduction_report,
    reproduction_sweep_summary,
    timeout_record,
    write_reproduction_sweep_report,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata

RUN_FULL_REPRO = os.environ.get("AMIGA_REVERSING_FULL_REPRO_INTEGRATION") == "1"
FULL_REPRO_REPORT_ENV = "AMIGA_REVERSING_FULL_REPRO_REPORT"
FULL_REPRO_TARGET_TIMEOUT_ENV = "AMIGA_REVERSING_FULL_REPRO_TARGET_TIMEOUT"
FULL_REPRO_PROFILE_ENV = "AMIGA_REVERSING_FULL_REPRO_PROFILE"
FULL_REPRO_PROFILE_SET_ENV = "AMIGA_REVERSING_FULL_REPRO_PROFILE_SET"
FULL_REPRO_FACTS_V2_STRUCTURAL_GATE_ENV = "AMIGA_REVERSING_FULL_REPRO_FACTS_V2_STRUCTURAL_GATE"
FULL_REPRO_FACTS_V2_SOURCE_GATE_ENV = "AMIGA_REVERSING_FULL_REPRO_FACTS_V2_SOURCE_GATE"
FULL_REPRO_FACTS_V2_REPRODUCTION_GATE_ENV = "AMIGA_REVERSING_FULL_REPRO_FACTS_V2_REPRODUCTION_GATE"
FULL_REPRO_WORKERS_ENV = "AMIGA_REVERSING_FULL_REPRO_WORKERS"
FULL_REPRO_BATCH_SIZE_ENV = "AMIGA_REVERSING_FULL_REPRO_BATCH_SIZE"
FULL_REPRO_IMPORT_WORKERS_ENV = "AMIGA_REVERSING_FULL_REPRO_IMPORT_WORKERS"
FULL_REPRO_RESOURCE_CACHE_ENV = "AMIGA_REVERSING_FULL_REPRO_RESOURCE_CACHE"
REPRO_SOURCE_ARTIFACT_ENV = "AMIGA_REVERSING_REPRO_SOURCE_ARTIFACT"
FACTS_V2_DIRECT_SOURCE_COMPARE_ENV = "AMIGA_REVERSING_FACTS_V2_DIRECT_SOURCE_COMPARE"
DEFAULT_FULL_REPRO_TARGET_TIMEOUT_SECONDS = 180
DEFAULT_FULL_REPRO_MAX_WORKERS = 12
DEFAULT_FULL_REPRO_BATCH_SIZE = 16
DEFAULT_FULL_REPRO_IMPORT_WORKERS = 1
DEFAULT_PROGRESS_WRITES_PER_WORKER = 4
DONE_PROGRESS_GRACE_SECONDS = 5
FACTS_V2_ACCEPTED_MISMATCH_KINDS = {
    "atari_relocation_target_out_of_range",
    "lossy_hunk_reloc32",
}
REQUIRED_EXACT_FULL_REPRO_TARGET_PREFIXES = (
    "existing_amiga_hunk_bloodwych",
)
RESOURCE_IMPORT_CACHE_ROOT = PROJECT_ROOT / "bin" / "rebuilt" / "_full_repro_resource_import_cache"
RESOURCE_DIRS = (
    PROJECT_ROOT / "resources" / "platform_amiga",
    PROJECT_ROOT / "resources" / "platform_atari_st",
)
RESOURCE_IMPORT_CACHE_TOOL_PATHS = (
    PROJECT_ROOT / "amiga_reversing" / "amiga_disk" / "adf.py",
    PROJECT_ROOT / "amiga_reversing" / "amiga_disk" / "models.py",
    PROJECT_ROOT / "amiga_reversing" / "amiga_disk" / "project.py",
    PROJECT_ROOT / "amiga_reversing" / "disasm" / "binary_source.py",
    PROJECT_ROOT / "amiga_reversing" / "disasm" / "c_backend.py",
    PROJECT_ROOT / "amiga_reversing" / "disasm" / "project_ids.py",
    PROJECT_ROOT / "amiga_reversing" / "disasm" / "target_metadata.py",
    PROJECT_ROOT / "src" / "build" / "platform_disk_lib.dll",
)
PROFILE_RESOURCE_DISK_PATTERNS = (
    "3d construction kit",
    "argasm",
    "bloodwych",
    "search for the king",
    "workbench",
)
PROFILE_TARGET_CATEGORIES = (
    ("king", ("king",)),
    ("bloodwych", ("bloodwych",)),
    ("icon.library", ("icon.library",)),
    ("3dedit", ("3dedit",)),
    ("fastfilesystem", ("fastfilesystem",)),
    ("atari_3d", ("resource-atari", "3d-construction-kit")),
)
BUILD_RUNTIME_FILES = (
    "platform_file_lib.dll",
    "platform_disk_lib.dll",
    "m68k_disassembler_lib.dll",
    "m68k_assembler_lib.dll",
    "m68k_assembler_app.exe",
)
INCLUDE_DIRS = (
    Path("ext") / "amiga_includes" / "ndk_2.0" / "include",
    Path("ext") / "atarist_includes" / "devpac_3_10" / "include",
)


pytestmark = pytest.mark.skipif(
    not RUN_FULL_REPRO,
    reason="Set AMIGA_REVERSING_FULL_REPRO_INTEGRATION=1 for the full reproduction sweep.",
)


def test_all_importable_targets_reproduce(tmp_path: Path) -> None:
    overall_started_at = time.perf_counter()
    setup_timing: dict[str, object] = {}
    phase_started_at = time.perf_counter()
    project_root = _prepare_project_root(tmp_path)
    setup_timing["prepare_project_root_seconds"] = round(time.perf_counter() - phase_started_at, 4)

    phase_started_at = time.perf_counter()
    limit = _target_limit()
    target_timeout_seconds = _target_timeout_seconds()
    profile_enabled = _profile_enabled()
    profile_set_enabled = _profile_set_enabled()
    setup_timing["config_seconds"] = round(time.perf_counter() - phase_started_at, 4)

    import_failures: list[str] = []
    discovery_limit = None if profile_set_enabled else limit
    phase_started_at = time.perf_counter()
    target_names = _copy_existing_binary_targets(project_root, limit=discovery_limit)
    setup_timing["copy_existing_targets_seconds"] = round(time.perf_counter() - phase_started_at, 4)
    remaining = _remaining_target_limit(discovery_limit, len(target_names))
    resource_import_cache: dict[str, object] = {}
    phase_started_at = time.perf_counter()
    if remaining is None or remaining > 0:
        target_names.extend(
            _import_resource_disk_targets(
                project_root,
                tmp_path,
                limit=remaining,
                import_failures=import_failures,
                profile_set=profile_set_enabled,
                cache_info=resource_import_cache,
            )
        )
    setup_timing["resource_import_seconds"] = round(time.perf_counter() - phase_started_at, 4)
    if resource_import_cache:
        setup_timing["resource_import_cache"] = resource_import_cache

    phase_started_at = time.perf_counter()
    if profile_set_enabled:
        target_names = _select_profile_targets(target_names)
        if limit is not None:
            target_names = target_names[:limit]
    setup_timing["profile_select_seconds"] = round(time.perf_counter() - phase_started_at, 4)

    assert target_names or import_failures, "No reproduction targets discovered."

    report_path = _full_repro_report_path()
    worker_count = _target_worker_count(len(target_names))
    batch_size = _target_batch_size(len(target_names))
    suite_started_at = time.perf_counter()
    target_failures: dict[int, str] = {}
    unsupported_indices: set[int] = set()
    records = [import_failure_record(message) for message in import_failures]
    target_record_start = len(records)
    records.extend(
        {"target": target_name, "status": "in_progress", "exact": False}
        for target_name in target_names
    )
    summary = _write_current_repro_summary(
        records,
        limit=limit,
        project_root=project_root,
        report_path=report_path,
        target_timeout_seconds=target_timeout_seconds,
        worker_count=worker_count,
        batch_size=batch_size,
        suite_started_at=suite_started_at,
        overall_started_at=overall_started_at,
        setup_timing=setup_timing,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_target = {
            executor.submit(
                _run_target_reproduction_batch_worker,
                batch,
                project_root=project_root,
                timeout_seconds=target_timeout_seconds,
                profile=profile_enabled,
            ): batch
            for batch in _target_batches(target_names, batch_size=batch_size)
        }
        completed_targets = 0
        progress_write_interval = _progress_write_interval(worker_count)
        for future in concurrent.futures.as_completed(future_to_target):
            batch = future_to_target[future]
            try:
                batch_results = future.result()
            except Exception as exc:
                batch_results = [
                    (target_index, target_name, crash_record(target_name, exc), None)
                    for target_index, target_name in batch
                ]
            for target_index, target_name, record, report in batch_results:
                record_index = target_record_start + target_index
                record = _with_effective_record_status(record, target_name, project_root=project_root)
                records[record_index] = record
                completed_targets += 1
                status = str(record.get("status"))
                if status == "unsupported":
                    unsupported_indices.add(target_index)
                    continue
                if status in {"exact", "accepted_mismatch"}:
                    continue
                target_failures[target_index] = (
                    _format_repro_failure(target_name, report)
                    if report is not None
                    else _format_repro_record_failure(target_name, record)
                )
            if completed_targets % progress_write_interval == 0:
                summary = _write_current_repro_summary(
                    records,
                    limit=limit,
                    project_root=project_root,
                    report_path=report_path,
                    target_timeout_seconds=target_timeout_seconds,
                    worker_count=worker_count,
                    batch_size=batch_size,
                    suite_started_at=suite_started_at,
                    overall_started_at=overall_started_at,
                    setup_timing=setup_timing,
                )
    summary = _write_current_repro_summary(
        records,
        limit=limit,
        project_root=project_root,
        report_path=report_path,
        target_timeout_seconds=target_timeout_seconds,
        worker_count=worker_count,
        batch_size=batch_size,
        suite_started_at=suite_started_at,
        overall_started_at=overall_started_at,
        setup_timing=setup_timing,
    )

    required_failures = _required_exact_full_repro_target_failures(summary, limit=limit)
    if required_failures:
        failure_text = "\n".join(required_failures)
        pytest.fail(f"required exact reproduction target failed:\nReport: {report_path}\n{failure_text}")

    if _facts_v2_structural_gate_enabled():
        gate_failures = _facts_v2_structural_gate_failures(summary)
        if gate_failures:
            failure_text = "\n".join(gate_failures)
            pytest.fail(f"facts_v2 structural gate failed:\nReport: {report_path}\n{failure_text}")
        return

    if _facts_v2_source_gate_enabled():
        gate_failures = _facts_v2_source_gate_failures(summary)
        if gate_failures:
            failure_text = "\n".join(gate_failures)
            pytest.fail(f"facts_v2 source gate failed:\nReport: {report_path}\n{failure_text}")
        return

    if _facts_v2_reproduction_gate_enabled():
        gate_failures = _facts_v2_reproduction_gate_failures(summary)
        if gate_failures:
            failure_text = "\n".join(gate_failures)
            pytest.fail(f"facts_v2 reproduction gate failed:\nReport: {report_path}\n{failure_text}")
        return

    failures = list(import_failures)
    failures.extend(target_failures[index] for index in sorted(target_failures))
    if failures:
        unsupported = [target_names[index] for index in sorted(unsupported_indices)]
        score_text = format_reproduction_sweep_score(summary)
        failure_text = "\n".join(failures[:80])
        if len(failures) > 80:
            failure_text += f"\n... {len(failures) - 80} more failures"
        pytest.fail(
            f"{len(failures)} target(s) failed exact reproduction "
            f"({len(unsupported)} unsupported skipped):\n"
            f"{score_text}\nReport: {report_path}\n{failure_text}"
        )


def _prepare_project_root(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    build_dir = project_root / "src" / "build"
    build_dir.mkdir(parents=True)
    for file_name in BUILD_RUNTIME_FILES:
        shutil.copy2(PROJECT_ROOT / "src" / "build" / file_name, build_dir / file_name)
    for include_dir in INCLUDE_DIRS:
        source_dir = PROJECT_ROOT / include_dir
        if source_dir.exists():
            shutil.copytree(source_dir, project_root / include_dir, dirs_exist_ok=True)
    (project_root / "targets").mkdir()
    return project_root


def _summary_target_status(summary: dict[str, object], target_name: str, *, fallback: str) -> str:
    targets = summary.get("targets")
    if isinstance(targets, list):
        for item in reversed(targets):
            if isinstance(item, dict) and item.get("target") == target_name:
                status = item.get("status")
                if isinstance(status, str) and status:
                    return status
    return fallback


def _with_effective_record_status(
    record: dict[str, object],
    target_name: str,
    *,
    project_root: Path,
) -> dict[str, object]:
    status = str(record.get("status"))
    if status in {"exact", "accepted_mismatch", "unsupported"}:
        return record
    summary = reproduction_sweep_summary([record], limit=1, project_root=project_root)
    targets = summary.get("targets")
    if isinstance(targets, list) and targets and isinstance(targets[0], dict):
        effective_record = cast(dict[str, object], targets[0])
        effective_status = _summary_target_status(summary, target_name, fallback=status)
        if effective_status != status:
            return effective_record
    return record


def _copy_existing_binary_targets(project_root: Path, *, limit: int | None) -> list[str]:
    target_names: list[str] = []
    source_paths = sorted((PROJECT_ROOT / "targets").rglob("source_binary.json"))
    for index, source_path in enumerate(source_paths):
        if limit is not None and len(target_names) >= limit:
            break
        source_payload = cast(dict[str, object], json.loads(source_path.read_text(encoding="utf-8")))
        if source_payload.get("kind") == "raw_binary":
            continue
        source_payload = _absolute_source_payload(source_payload)
        target_name = _integration_target_name("existing", f"{index}-{source_path.parent}")
        target_dir = project_root / "targets" / target_name
        create_project_at_path(f"targets/{target_name}", project_root=project_root)
        write_source_descriptor(target_dir, source_payload)
        for metadata_name in (
            "target_metadata.json",
            "target_seeded_metadata.json",
            "target_corrections.json",
            "target_ui_edits.json",
        ):
            metadata_path = source_path.parent / metadata_name
            if metadata_path.exists():
                shutil.copy2(metadata_path, target_dir / metadata_name)
        target_names.append(target_name)
    return target_names

def _absolute_source_payload(payload: dict[str, object]) -> dict[str, object]:
    result = dict(payload)
    for key in ("path", "disk_path"):
        value = result.get(key)
        if isinstance(value, str):
            result[key] = str(_resolve_repo_path(value))
    result.pop("parent_disk_id", None)
    return result


def _resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path.resolve()
    return (PROJECT_ROOT / value).resolve()


def _import_resource_disk_targets(
    project_root: Path,
    tmp_path: Path,
    *,
    limit: int | None,
    import_failures: list[str],
    profile_set: bool,
    cache_info: dict[str, object] | None = None,
) -> list[str]:
    if profile_set:
        _set_resource_import_cache_info(cache_info, enabled=False, status="disabled", reason="profile_set")
    elif limit is not None:
        _set_resource_import_cache_info(cache_info, enabled=False, status="disabled", reason="target_limit")
    elif not _resource_import_cache_enabled():
        _set_resource_import_cache_info(cache_info, enabled=False, status="disabled", reason="env_disabled")
    else:
        cached = _import_resource_disk_targets_from_cache(
            project_root,
            import_failures=import_failures,
            cache_info=cache_info,
        )
        if cached is not None:
            return cached
    return _import_resource_disk_targets_uncached(
        project_root,
        tmp_path,
        limit=limit,
        import_failures=import_failures,
        profile_set=profile_set,
    )


def _import_resource_disk_targets_uncached(
    project_root: Path,
    tmp_path: Path,
    *,
    limit: int | None,
    import_failures: list[str],
    profile_set: bool,
) -> list[str]:
    disk_paths = list(_resource_disk_images(tmp_path, profile_set=profile_set))
    if limit is not None or profile_set:
        return _import_resource_disk_targets_sequential(
            project_root,
            disk_paths,
            limit=limit,
            import_failures=import_failures,
        )

    worker_count = _resource_import_worker_count(len(disk_paths))
    if worker_count <= 1:
        return _import_resource_disk_targets_sequential(
            project_root,
            disk_paths,
            limit=None,
            import_failures=import_failures,
        )

    results: dict[int, tuple[list[str], list[str]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_disk = {
            executor.submit(_import_resource_disk_path_targets, project_root, disk_path): (index, disk_path)
            for index, disk_path in enumerate(disk_paths)
        }
        for future in concurrent.futures.as_completed(future_to_disk):
            index, disk_path = future_to_disk[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                results[index] = (
                    [],
                    [f"{disk_path}: disk import failed: {type(exc).__name__}: {exc}"],
                )

    target_names: list[str] = []
    for index in range(len(disk_paths)):
        imported_targets, failures = results.get(index, ([], []))
        target_names.extend(imported_targets)
        import_failures.extend(failures)
    return target_names


def _import_resource_disk_targets_sequential(
    project_root: Path,
    disk_paths: list[Path],
    *,
    limit: int | None,
    import_failures: list[str],
) -> list[str]:
    target_names: list[str] = []
    for disk_path in disk_paths:
        if limit is not None and len(target_names) >= limit:
            break
        imported_targets, failures = _import_resource_disk_path_targets(project_root, disk_path)
        target_names.extend(imported_targets)
        import_failures.extend(failures)
    return target_names if limit is None else target_names[:limit]


def _import_resource_disk_path_targets(project_root: Path, disk_path: Path) -> tuple[list[str], list[str]]:
    import_failures: list[str] = []
    suffix = disk_path.suffix.lower()
    if suffix == ".adf":
        return _import_amiga_disk_targets(project_root, disk_path, import_failures), import_failures
    if suffix in {".st", ".msa"}:
        return _import_atari_disk_targets(project_root, disk_path, import_failures), import_failures
    return [], import_failures


def _resource_import_cache_enabled() -> bool:
    return os.environ.get(FULL_REPRO_RESOURCE_CACHE_ENV, "1") != "0"


def _import_resource_disk_targets_from_cache(
    project_root: Path,
    *,
    import_failures: list[str],
    cache_info: dict[str, object] | None = None,
) -> list[str] | None:
    _set_resource_import_cache_info(
        cache_info,
        enabled=True,
        status="checking",
        cache_root=str(RESOURCE_IMPORT_CACHE_ROOT),
    )
    try:
        stamp = _resource_import_cache_stamp()
        stamp_path = RESOURCE_IMPORT_CACHE_ROOT / "stamp.json"
        cache_project_root = RESOURCE_IMPORT_CACHE_ROOT / "project"
        cached = _read_resource_import_cache_stamp(stamp_path)
        rebuild_reason: str | None = None
        if cached is None:
            rebuild_reason = "missing_or_unreadable_stamp"
        elif cached.get("stamp") != stamp:
            rebuild_reason = "stamp_changed"
        if rebuild_reason is not None:
            rebuild_started_at = time.perf_counter()
            cached = _build_resource_import_cache(stamp)
            _set_resource_import_cache_info(
                cache_info,
                enabled=True,
                status="rebuilt",
                rebuild_reason=rebuild_reason,
                rebuild_seconds=round(time.perf_counter() - rebuild_started_at, 4),
            )
        else:
            _set_resource_import_cache_info(cache_info, enabled=True, status="hit")
        target_names = cached.get("target_names")
        cached_failures = cached.get("import_failures")
        if not isinstance(target_names, list) or not all(isinstance(item, str) for item in target_names):
            _set_resource_import_cache_info(
                cache_info,
                enabled=True,
                status="fallback_uncached",
                error="cached target_names missing or malformed",
            )
            return None
        if isinstance(cached_failures, list):
            import_failures.extend(str(item) for item in cached_failures)
        hydrate_started_at = time.perf_counter()
        _hydrate_resource_import_cache(cache_project_root, project_root)
        _set_resource_import_cache_info(
            cache_info,
            enabled=True,
            target_count=len(target_names),
            import_failure_count=len(cached_failures) if isinstance(cached_failures, list) else 0,
            hydrate_seconds=round(time.perf_counter() - hydrate_started_at, 4),
        )
        return list(target_names)
    except Exception as exc:
        _set_resource_import_cache_info(
            cache_info,
            enabled=True,
            status="fallback_uncached",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return None


def _set_resource_import_cache_info(
    cache_info: dict[str, object] | None,
    **values: object,
) -> None:
    if cache_info is None:
        return
    cache_info.update(values)


def _read_resource_import_cache_stamp(stamp_path: Path) -> dict[str, object] | None:
    if not stamp_path.exists():
        return None
    payload = json.loads(stamp_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _build_resource_import_cache(stamp: dict[str, object]) -> dict[str, object]:
    if RESOURCE_IMPORT_CACHE_ROOT.exists():
        shutil.rmtree(RESOURCE_IMPORT_CACHE_ROOT)
    cache_project_root = _prepare_project_root(RESOURCE_IMPORT_CACHE_ROOT)
    import_failures: list[str] = []
    target_names = _import_resource_disk_targets_uncached(
        cache_project_root,
        RESOURCE_IMPORT_CACHE_ROOT,
        limit=None,
        import_failures=import_failures,
        profile_set=False,
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "stamp": stamp,
        "target_names": target_names,
        "import_failures": import_failures,
    }
    RESOURCE_IMPORT_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    (RESOURCE_IMPORT_CACHE_ROOT / "stamp.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def _hydrate_resource_import_cache(cache_project_root: Path, project_root: Path) -> None:
    source_targets = cache_project_root / "targets"
    target_root = project_root / "targets"
    if not source_targets.exists():
        raise FileNotFoundError(source_targets)
    for source_child in source_targets.iterdir():
        if source_child.is_dir():
            shutil.copytree(source_child, target_root / source_child.name, dirs_exist_ok=True)


def _resource_import_cache_stamp() -> dict[str, object]:
    return {
        "resources": [_file_stamp(path) for path in _resource_input_files(profile_set=False)],
        "tools": [_tool_file_stamp(path) for path in _resource_import_tool_files()],
    }


def _resource_import_tool_files() -> Iterator[Path]:
    seen: set[Path] = set()
    for path in RESOURCE_IMPORT_CACHE_TOOL_PATHS:
        if path.exists():
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield path


def _file_stamp(path: Path) -> dict[str, object]:
    stat = path.stat()
    try:
        label = path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        label = path.as_posix()
    return {
        "path": label,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _tool_file_stamp(path: Path) -> dict[str, object]:
    stat = path.stat()
    try:
        label = path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        label = path.as_posix()
    return {
        "path": label,
        "size": stat.st_size,
        "sha256": _tool_file_sha256(path),
    }


def _tool_file_sha256(path: Path) -> str:
    data = bytearray(path.read_bytes())
    if path.suffix.lower() in {".dll", ".exe"}:
        _zero_pe_reproducible_timestamps(data)
    return hashlib.sha256(data).hexdigest()


def _zero_pe_reproducible_timestamps(data: bytearray) -> None:
    if len(data) < 0x40 or data[0:2] != b"MZ":
        return
    pe_offset = int.from_bytes(data[0x3C:0x40], "little")
    if pe_offset < 0 or pe_offset + 24 > len(data) or data[pe_offset:pe_offset + 4] != b"PE\0\0":
        return
    _zero_range(data, pe_offset + 8, 4)
    section_count = int.from_bytes(data[pe_offset + 6:pe_offset + 8], "little")
    optional_size = int.from_bytes(data[pe_offset + 20:pe_offset + 22], "little")
    optional_offset = pe_offset + 24
    section_table = optional_offset + optional_size
    if optional_offset + optional_size > len(data) or section_table + section_count * 40 > len(data):
        return
    magic = int.from_bytes(data[optional_offset:optional_offset + 2], "little")
    data_directory_offset = optional_offset + (112 if magic == 0x20B else 96 if magic == 0x10B else 0)
    if data_directory_offset == optional_offset or data_directory_offset + 7 * 8 > len(data):
        return
    debug_rva = int.from_bytes(data[data_directory_offset + 6 * 8:data_directory_offset + 6 * 8 + 4], "little")
    debug_size = int.from_bytes(data[data_directory_offset + 6 * 8 + 4:data_directory_offset + 6 * 8 + 8], "little")
    debug_offset = _pe_rva_to_file_offset(data, section_table, section_count, debug_rva)
    if debug_offset is None or debug_size == 0 or debug_offset + debug_size > len(data):
        return
    for entry_offset in range(debug_offset, debug_offset + debug_size, 28):
        if entry_offset + 28 > len(data):
            break
        _zero_range(data, entry_offset + 4, 4)


def _zero_range(data: bytearray, offset: int, size: int) -> None:
    if offset < 0 or offset + size > len(data):
        return
    data[offset:offset + size] = b"\0" * size


def _pe_rva_to_file_offset(
    data: bytearray,
    section_table: int,
    section_count: int,
    rva: int,
) -> int | None:
    for index in range(section_count):
        offset = section_table + index * 40
        virtual_size = int.from_bytes(data[offset + 8:offset + 12], "little")
        virtual_address = int.from_bytes(data[offset + 12:offset + 16], "little")
        raw_size = int.from_bytes(data[offset + 16:offset + 20], "little")
        raw_pointer = int.from_bytes(data[offset + 20:offset + 24], "little")
        span = max(virtual_size, raw_size)
        if span != 0 and virtual_address <= rva < virtual_address + span:
            file_offset = raw_pointer + (rva - virtual_address)
            return file_offset if 0 <= file_offset < len(data) else None
    return rva if 0 <= rva < len(data) else None


def _resource_input_files(*, profile_set: bool = False) -> Iterator[Path]:
    for resource_dir in RESOURCE_DIRS:
        if not resource_dir.exists():
            continue
        for path in sorted(resource_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".adf", ".st", ".msa", ".zip"}:
                continue
            if profile_set and not _is_profile_resource_path(path):
                continue
            yield path


def _resource_disk_images(tmp_path: Path, *, profile_set: bool = False) -> Iterator[Path]:
    extraction_dir = tmp_path / "resource_disks"
    for path in _resource_input_files(profile_set=profile_set):
        suffix = path.suffix.lower()
        if suffix in {".adf", ".st", ".msa"}:
            yield path
            continue
        yield from _extract_zipped_disk_images(path, extraction_dir)


def _extract_zipped_disk_images(zip_path: Path, extraction_dir: Path) -> Iterator[Path]:
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                member_suffix = Path(member.filename).suffix.lower()
                if member_suffix not in {".adf", ".st", ".msa"}:
                    continue
                digest = hashlib.sha1(f"{zip_path}|{member.filename}".encode()).hexdigest()[:12]
                out_path = extraction_dir / f"{digest}_{Path(member.filename).name}"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, out_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
                yield out_path
    except zipfile.BadZipFile:
        return


def _import_amiga_disk_targets(
    project_root: Path,
    disk_path: Path,
    import_failures: list[str],
) -> list[str]:
    disk_id = _integration_target_name("resource_amiga_disk", str(disk_path))
    try:
        manifest = create_disk_project(disk_path, disk_id=disk_id, project_root=project_root)
    except Exception as exc:
        import_failures.append(f"{disk_path}: Amiga disk import failed: {type(exc).__name__}: {exc}")
        return []
    target_names: list[str] = []
    if manifest.bootblock_target_name:
        target_names.append(manifest.bootblock_target_name)
    target_names.extend(target.target_name for target in manifest.imported_targets)
    return [
        target_name
        for target_name in target_names
        if _target_source_kind(project_root, target_name) != "raw_binary"
    ]


def _import_atari_disk_targets(
    project_root: Path,
    disk_path: Path,
    import_failures: list[str],
) -> list[str]:
    try:
        inspection = inspect_disk_with_c_backend(disk_path, project_root=project_root)
    except Exception as exc:
        import_failures.append(f"{disk_path}: Atari disk import failed: {type(exc).__name__}: {exc}")
        return []

    target_names: list[str] = []
    disk_id = _integration_target_name("resource_atari_disk", str(disk_path))
    entries = inspection.get("entries")
    if not isinstance(entries, list):
        return target_names
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if not entry.get("is_executable_candidate"):
            continue
        entry_path = entry.get("path")
        if not isinstance(entry_path, str):
            continue
        if Path(entry_path).suffix.lower() not in {".prg", ".tos", ".ttp"}:
            continue
        target_name = _integration_target_name("resource_atari", f"{disk_path}::{entry_path}")
        target_dir = project_root / "targets" / target_name
        create_project_at_path(f"targets/{target_name}", project_root=project_root)
        write_source_descriptor(
            target_dir,
            {
                "kind": "disk_entry",
                "disk_id": disk_id,
                "disk_path": str(disk_path.resolve()),
                "entry_path": entry_path,
            },
        )
        write_target_metadata(target_dir, TargetMetadata.from_dict(_empty_metadata()))
        target_names.append(target_name)
    return target_names


def _target_source_kind(project_root: Path, target_name: str) -> str | None:
    source_path = project_root / "targets" / target_name / "source_binary.json"
    if not source_path.exists():
        for manifest_path in (project_root / "targets").glob("*/manifest.json"):
            manifest = DiskManifest.load(manifest_path)
            if manifest.bootblock_target_name == target_name:
                source_path = project_root / manifest.bootblock_target_path / "source_binary.json"
                break
            for imported_target in manifest.imported_targets:
                if imported_target.target_name == target_name:
                    source_path = project_root / imported_target.target_path / "source_binary.json"
                    break
    if not source_path.exists():
        return None
    payload = cast(dict[str, object], json.loads(source_path.read_text(encoding="utf-8")))
    kind = payload.get("kind")
    return kind if isinstance(kind, str) else None


def _integration_target_name(prefix: str, label: str) -> str:
    stem = normalize_filename_stem(Path(label).stem)[:36]
    digest = hashlib.sha1(label.encode("utf-8")).hexdigest()[:10]
    return ensure_safe_project_id(f"{prefix}_{stem}_{digest}")


def _target_limit() -> int | None:
    limit_text = os.environ.get("AMIGA_REVERSING_FULL_REPRO_LIMIT")
    if not limit_text:
        return None
    try:
        limit = int(limit_text)
    except ValueError:
        return None
    if limit <= 0:
        return None
    return limit


def _target_timeout_seconds() -> int:
    timeout_text = os.environ.get(FULL_REPRO_TARGET_TIMEOUT_ENV)
    if not timeout_text:
        return DEFAULT_FULL_REPRO_TARGET_TIMEOUT_SECONDS
    try:
        timeout = int(timeout_text)
    except ValueError:
        return DEFAULT_FULL_REPRO_TARGET_TIMEOUT_SECONDS
    if timeout <= 0:
        return DEFAULT_FULL_REPRO_TARGET_TIMEOUT_SECONDS
    return timeout


def _target_worker_count(target_count: int) -> int:
    if target_count <= 1:
        return 1
    default_workers = min(DEFAULT_FULL_REPRO_MAX_WORKERS, os.cpu_count() or 1, target_count)
    workers_text = os.environ.get(FULL_REPRO_WORKERS_ENV)
    if not workers_text:
        return max(1, default_workers)
    try:
        workers = int(workers_text)
    except ValueError:
        return max(1, default_workers)
    if workers <= 0:
        return max(1, default_workers)
    return min(workers, target_count)


def _target_batch_size(target_count: int) -> int:
    if target_count <= 1:
        return 1
    batch_size_text = os.environ.get(FULL_REPRO_BATCH_SIZE_ENV)
    if not batch_size_text:
        return min(DEFAULT_FULL_REPRO_BATCH_SIZE, target_count)
    try:
        batch_size = int(batch_size_text)
    except ValueError:
        return min(DEFAULT_FULL_REPRO_BATCH_SIZE, target_count)
    if batch_size <= 0:
        return min(DEFAULT_FULL_REPRO_BATCH_SIZE, target_count)
    return min(batch_size, target_count)


def _resource_import_worker_count(disk_count: int) -> int:
    if disk_count <= 1:
        return 1
    default_workers = min(DEFAULT_FULL_REPRO_IMPORT_WORKERS, os.cpu_count() or 1, disk_count)
    workers_text = os.environ.get(FULL_REPRO_IMPORT_WORKERS_ENV)
    if not workers_text:
        return max(1, default_workers)
    try:
        workers = int(workers_text)
    except ValueError:
        return max(1, default_workers)
    if workers <= 0:
        return max(1, default_workers)
    return min(workers, disk_count)


def _target_batches(
    target_names: list[str],
    *,
    batch_size: int,
) -> Iterator[list[tuple[int, str]]]:
    effective_batch_size = max(1, batch_size)
    for start in range(0, len(target_names), effective_batch_size):
        yield list(enumerate(target_names[start : start + effective_batch_size], start=start))


def _progress_write_interval(worker_count: int) -> int:
    return max(1, worker_count * DEFAULT_PROGRESS_WRITES_PER_WORKER)


def _profile_enabled() -> bool:
    return os.environ.get(FULL_REPRO_PROFILE_ENV) == "1" or _profile_set_enabled()


def _profile_set_enabled() -> bool:
    return os.environ.get(FULL_REPRO_PROFILE_SET_ENV) == "1"


def _facts_v2_structural_gate_enabled() -> bool:
    return os.environ.get(FULL_REPRO_FACTS_V2_STRUCTURAL_GATE_ENV) == "1"


def _facts_v2_source_gate_enabled() -> bool:
    return os.environ.get(FULL_REPRO_FACTS_V2_SOURCE_GATE_ENV) == "1"


def _facts_v2_reproduction_gate_enabled() -> bool:
    return os.environ.get(FULL_REPRO_FACTS_V2_REPRODUCTION_GATE_ENV) == "1"


def _required_exact_full_repro_target_failures(summary: dict[str, object], *, limit: int | None) -> list[str]:
    if limit is not None:
        return []
    targets = summary.get("targets")
    if not isinstance(targets, list):
        return ["missing reproduction target summary"]
    failures: list[str] = []
    for prefix in REQUIRED_EXACT_FULL_REPRO_TARGET_PREFIXES:
        matches = [
            target for target in targets
            if isinstance(target, dict) and str(target.get("target", "")).startswith(prefix)
        ]
        if not matches:
            failures.append(f"{prefix}: target did not run")
            continue
        exact_matches = [
            target for target in matches
            if target.get("status") == "exact"
            and target.get("exact") is True
            and target.get("comparison_status") == "exact_file"
            and target.get("content_exact") is True
            and target.get("canonical_full_file_exact") is True
        ]
        if exact_matches:
            continue
        statuses = ", ".join(
            f"{target.get('target')}={target.get('status')}/{target.get('comparison_status')}"
            for target in matches
        )
        failures.append(f"{prefix}: expected exact full-file reproduction, got {statuses}")
    return failures


def _facts_v2_structural_gate_failures(summary: dict[str, object]) -> list[str]:
    failures: list[str] = []
    analysis_backend_counts = summary.get("analysis_backend_counts")
    if not isinstance(analysis_backend_counts, dict) or analysis_backend_counts.get("facts_v2", 0) == 0:
        failures.append("no facts_v2 targets were run")
    facts_v2 = summary.get("facts_v2_invariant_failures")
    if not isinstance(facts_v2, dict):
        failures.append("missing facts_v2 invariant summary")
        return failures
    profiled_targets = facts_v2.get("profiled_targets")
    if not isinstance(profiled_targets, int) or profiled_targets == 0:
        failures.append("no facts_v2 profiles were produced")
    for key, fallback_key in (
        ("unaccepted_unresolved_labels", "unresolved_labels"),
        ("unaccepted_interior_conflicts_unresolved", "interior_conflicts_unresolved"),
        ("unaccepted_relocation_failures", "relocation_failures"),
        ("unaccepted_relocation_anchor_instruction_bytes", "relocation_anchor_instruction_bytes"),
        ("unaccepted_relocation_anchor_unknown_contexts", "relocation_anchor_unknown_contexts"),
        ("unaccepted_required_instruction_failures", "required_instruction_failures"),
    ):
        value = facts_v2.get(key, facts_v2.get(fallback_key))
        if isinstance(value, int) and value != 0:
            failures.append(f"{key}={value}")
    affected_targets = facts_v2.get("unaccepted_affected_targets", facts_v2.get("affected_targets"))
    if isinstance(affected_targets, list) and affected_targets:
        failures.append("affected_targets=" + ", ".join(str(item) for item in affected_targets[:20]))
    return failures


def _facts_v2_source_gate_failures(summary: dict[str, object]) -> list[str]:
    failures = _facts_v2_structural_gate_failures(summary)
    facts_v2 = summary.get("facts_v2_invariant_failures")
    if not isinstance(facts_v2, dict):
        return failures
    profiled_targets = facts_v2.get("profiled_targets")
    enabled_targets = facts_v2.get("asm_source_enabled_targets")
    if isinstance(profiled_targets, int) and profiled_targets != 0 and enabled_targets != profiled_targets:
        failures.append(f"asm_source_enabled_targets={enabled_targets}/{profiled_targets}")
    symbolic = facts_v2.get("asm_source_symbolic_instructions")
    if not isinstance(symbolic, int) or symbolic == 0:
        failures.append("no facts_v2 symbolic instructions were rendered")
    for key, fallback_key in (
        ("unaccepted_asm_source_instruction_render_failures", "asm_source_instruction_render_failures"),
        ("unaccepted_asm_source_instruction_byte_mismatches", "asm_source_instruction_byte_mismatches"),
        (
            "unaccepted_asm_source_instruction_relocation_failures",
            "asm_source_instruction_relocation_failures",
        ),
        ("unaccepted_asm_source_relocation_anchor_refusals", "asm_source_relocation_anchor_refusals"),
    ):
        value = facts_v2.get(key, facts_v2.get(fallback_key))
        if isinstance(value, int) and value != 0:
            failures.append(f"{key}={value}")
    affected_targets = facts_v2.get(
        "unaccepted_source_affected_targets", facts_v2.get("source_affected_targets")
    )
    if isinstance(affected_targets, list) and affected_targets:
        failures.append("source_affected_targets=" + ", ".join(str(item) for item in affected_targets[:20]))
    source_comparison = summary.get("facts_v2_direct_source_comparison")
    if not isinstance(source_comparison, dict):
        failures.append("missing direct source comparison summary")
        return failures
    compared = source_comparison.get("compared_targets")
    if not isinstance(compared, int) or compared == 0:
        failures.append("no direct source comparisons were run")
        return failures
    content_compared = source_comparison.get("source_content_compared_targets")
    if content_compared != compared:
        failures.append(f"source_content_compared_targets={content_compared}/{compared}")
    content_exact = source_comparison.get("source_content_exact_targets")
    if content_exact != compared:
        failures.append(f"source_content_exact_targets={content_exact}/{compared}")
        mismatch_targets = source_comparison.get("source_content_mismatch_targets")
        if isinstance(mismatch_targets, list) and mismatch_targets:
            failures.append(
                "source_content_mismatch_targets="
                + ", ".join(str(item.get("target")) for item in mismatch_targets[:20] if isinstance(item, dict))
            )
    return failures


def _facts_v2_reproduction_gate_failures(summary: dict[str, object]) -> list[str]:
    failures: list[str] = []
    analysis_backend_counts = summary.get("analysis_backend_counts")
    if not isinstance(analysis_backend_counts, dict) or analysis_backend_counts.get("facts_v2", 0) == 0:
        failures.append("no facts_v2 targets were run")
    exactness = summary.get("reproduction_exactness")
    if not isinstance(exactness, dict):
        failures.append("missing reproduction exactness summary")
        return failures
    accepted_kind_counts = summary.get("accepted_mismatch_kinds")
    if not isinstance(accepted_kind_counts, dict):
        failures.append("missing accepted_mismatch_kinds summary")
    else:
        unexpected = sorted(str(kind) for kind in accepted_kind_counts if kind not in FACTS_V2_ACCEPTED_MISMATCH_KINDS)
        if unexpected:
            failures.append("unexpected_accepted_mismatch_kinds=" + ", ".join(unexpected))
        accepted_total = sum(value for value in accepted_kind_counts.values() if isinstance(value, int))
        accepted_exactness = exactness.get("accepted_mismatch")
        if isinstance(accepted_exactness, int) and accepted_total != accepted_exactness:
            failures.append(f"accepted_mismatch_kind_total={accepted_total}/{accepted_exactness}")
    comparison_targets = exactness.get("comparison_targets")
    if not isinstance(comparison_targets, int) or comparison_targets == 0:
        failures.append("no reproduction comparison records were produced")
        return failures
    missing_comparison = exactness.get("missing_comparison_targets")
    if isinstance(missing_comparison, int) and missing_comparison != 0:
        failures.append(f"missing_comparison_targets={missing_comparison}")
    content_exact = exactness.get("accepted_content_or_lossy", exactness.get("content_exact"))
    if not isinstance(content_exact, int) or content_exact != comparison_targets:
        failures.append(f"accepted_content_or_lossy={content_exact}/{comparison_targets}")
        targets = exactness.get("content_mismatch_targets")
        if isinstance(targets, list) and targets:
            failures.append("content_mismatch_targets=" + ", ".join(str(item) for item in targets[:20]))
    adjusted_exact = exactness.get(
        "accepted_adjusted_or_lossy", exactness.get("policy_adjusted_full_file_exact")
    )
    if not isinstance(adjusted_exact, int) or adjusted_exact != comparison_targets:
        failures.append(f"accepted_adjusted_or_lossy={adjusted_exact}/{comparison_targets}")
        targets = exactness.get("policy_adjusted_mismatch_targets")
        if isinstance(targets, list) and targets:
            failures.append("policy_adjusted_mismatch_targets=" + ", ".join(str(item) for item in targets[:20]))
    return failures


def _is_profile_resource_path(path: Path) -> bool:
    normalized = path.name.lower().replace("_", " ").replace("-", " ")
    return any(pattern in normalized for pattern in PROFILE_RESOURCE_DISK_PATTERNS)


def _select_profile_targets(target_names: list[str]) -> list[str]:
    selected: list[str] = []
    seen_categories: set[str] = set()
    for target_name in target_names:
        category = _profile_target_category(target_name)
        if category is None or category in seen_categories:
            continue
        selected.append(target_name)
        seen_categories.add(category)
    return selected


def _profile_target_category(target_name: str) -> str | None:
    normalized = target_name.lower().replace("_", "-")
    for category, required_tokens in PROFILE_TARGET_CATEGORIES:
        if all(token in normalized for token in required_tokens):
            return category
    return None


def _full_repro_report_path() -> Path:
    report_text = os.environ.get(FULL_REPRO_REPORT_ENV)
    if report_text:
        return Path(report_text)
    return PROJECT_ROOT / "bin" / "rebuilt" / "full_reproduction_report.json"


def _write_current_repro_summary(
    records: list[dict[str, object]],
    *,
    limit: int | None,
    project_root: Path,
    report_path: Path,
    target_timeout_seconds: int,
    worker_count: int,
    batch_size: int,
    suite_started_at: float,
    overall_started_at: float,
    setup_timing: dict[str, object],
) -> dict[str, object]:
    summary = reproduction_sweep_summary(
        records,
        limit=limit,
        project_root=project_root,
    )
    summary["target_timeout_seconds"] = target_timeout_seconds
    summary["worker_count"] = worker_count
    summary["batch_size"] = batch_size
    summary["wall_seconds"] = round(time.perf_counter() - suite_started_at, 4)
    summary["overall_wall_seconds"] = round(time.perf_counter() - overall_started_at, 4)
    setup_summary = dict(setup_timing)
    setup_summary["total_seconds"] = round(suite_started_at - overall_started_at, 4)
    summary["setup_timing"] = setup_summary
    write_reproduction_sweep_report(report_path, summary)
    return summary


def _run_target_reproduction_batch_worker(
    batch: list[tuple[int, str]],
    *,
    project_root: Path,
    timeout_seconds: int,
    profile: bool,
) -> list[tuple[int, str, dict[str, object], dict[str, object] | None]]:
    batch_input_path = _batch_input_path(project_root, batch)
    batch_output_path = _batch_output_path(project_root, batch)
    batch_started_at = time.perf_counter()
    batch_timeout = max(timeout_seconds, timeout_seconds * max(1, len(batch)))
    if batch_input_path.exists():
        batch_input_path.unlink()
    if batch_output_path.exists():
        batch_output_path.unlink()
    batch_payload = {
        "project_root": str(project_root),
        "profile": profile,
        "targets": [
            {
                "target": target_name,
                "output": str(_worker_output_path(project_root, target_name)),
                "progress": str(_worker_progress_path(project_root, target_name)),
            }
            for _, target_name in batch
        ],
    }
    _write_worker_payload(batch_input_path, batch_payload)
    command = [
        sys.executable,
        "-m",
        "amiga_reversing.disasm.reproduction_worker",
        "--batch-input",
        str(batch_input_path),
        "--batch-output",
        str(batch_output_path),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    if profile:
        env.setdefault(REPRO_SOURCE_ARTIFACT_ENV, "on_failure")
    if _facts_v2_source_gate_enabled():
        env["AMIGA_REVERSING_FACTS_V2_ASM_SOURCE"] = "1"
        env[FACTS_V2_DIRECT_SOURCE_COMPARE_ENV] = "1"
    process = subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0,
        start_new_session=os.name != "nt",
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=batch_timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process_tree(process)
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        stdout = ""
        stderr = ""
    results: list[tuple[int, str, dict[str, object], dict[str, object] | None]] = []
    for target_index, target_name in batch:
        payload = _read_worker_payload(_worker_output_path(project_root, target_name))
        completed = _worker_result_from_payload(
            target_name,
            payload,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr,
            started_at=batch_started_at,
        )
        if completed is not None:
            record, report = completed
        else:
            progress = _read_worker_payload(_worker_progress_path(project_root, target_name))
            if timed_out:
                duration_seconds = round(time.perf_counter() - batch_started_at, 4)
                record = timeout_record(
                    target_name,
                    timeout_seconds,
                    progress=progress,
                    duration_seconds=duration_seconds,
                )
            else:
                record = crash_record(
                    target_name,
                    RuntimeError(f"batch worker exited {process.returncode}: {stderr or stdout}".strip()[:1000]),
                )
                record["duration_seconds"] = round(time.perf_counter() - batch_started_at, 4)
            report = None
        results.append((target_index, target_name, record, report))
    return results


def _worker_result_from_payload(
    target_name: str,
    payload: dict[str, object],
    *,
    returncode: int | None,
    stdout: str,
    stderr: str,
    started_at: float,
) -> tuple[dict[str, object], dict[str, object] | None] | None:
    if isinstance(payload.get("report"), dict):
        report = cast(dict[str, object], payload["report"])
        record = record_from_reproduction_report(target_name, report)
        _attach_worker_metrics(record, payload, started_at=started_at)
        return record, report
    if payload.get("status") == "crashed":
        message = f"{payload.get('error_type')}: {payload.get('error')}"
        record = crash_record(target_name, RuntimeError(message))
        if isinstance(payload.get("traceback"), str):
            record["worker_traceback"] = payload["traceback"]
        _attach_worker_metrics(record, payload, started_at=started_at)
        return record, None
    if returncode is None:
        return None
    if returncode != 0:
        message = f"worker exited {returncode}: {stderr or stdout}".strip()
        record = crash_record(target_name, RuntimeError(message[:1000]))
        record["duration_seconds"] = round(time.perf_counter() - started_at, 4)
        return record, None
    return None


def _attach_worker_metrics(
    record: dict[str, object],
    payload: dict[str, object],
    *,
    started_at: float,
) -> None:
    duration_seconds = _float_or_none(payload.get("duration_seconds"))
    record["duration_seconds"] = (
        round(duration_seconds, 4)
        if duration_seconds is not None
        else round(time.perf_counter() - started_at, 4)
    )
    timings = payload.get("timings")
    if isinstance(timings, dict):
        record["worker_timings"] = timings
    listing_profile = payload.get("listing_profile")
    if isinstance(listing_profile, dict):
        record["listing_profile"] = listing_profile
    row_count = payload.get("row_count")
    if isinstance(row_count, int):
        record["row_count"] = row_count


def _worker_output_path(project_root: Path, target_name: str) -> Path:
    digest = hashlib.sha1(target_name.encode()).hexdigest()[:16]
    return project_root / "bin" / "rebuilt" / "_full_repro_workers" / f"{digest}.json"


def _worker_progress_path(project_root: Path, target_name: str) -> Path:
    digest = hashlib.sha1(target_name.encode()).hexdigest()[:16]
    return project_root / "bin" / "rebuilt" / "_full_repro_workers" / f"{digest}.progress.json"


def _batch_input_path(project_root: Path, batch: list[tuple[int, str]]) -> Path:
    return _batch_path(project_root, batch, suffix=".input.json")


def _batch_output_path(project_root: Path, batch: list[tuple[int, str]]) -> Path:
    return _batch_path(project_root, batch, suffix=".output.json")


def _batch_path(project_root: Path, batch: list[tuple[int, str]], *, suffix: str) -> Path:
    key = "|".join(f"{index}:{target_name}" for index, target_name in batch)
    digest = hashlib.sha1(key.encode()).hexdigest()[:16]
    return project_root / "bin" / "rebuilt" / "_full_repro_workers" / f"batch_{digest}{suffix}"


def _read_worker_payload(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return cast(dict[str, object], payload) if isinstance(payload, dict) else {}


def _write_worker_payload(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def _kill_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                check=False,
            )
            return
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
            return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except OSError:
        process.kill()


def _remaining_target_limit(limit: int | None, current_count: int) -> int | None:
    if limit is None:
        return None
    return max(0, limit - current_count)


def _format_repro_failure(target_name: str, report: dict[str, object]) -> str:
    parts = [f"{target_name}: {report.get('status')}"]
    first_diff = report.get("first_diff")
    if first_diff:
        parts.append(f"first_diff={first_diff}")
    tool_error = report.get("tool_error")
    if tool_error:
        parts.append(f"tool_error={tool_error}")
    stderr = str(report.get("assembler_stderr") or "").strip()
    if stderr:
        parts.append(f"stderr={stderr[:500]}")
    return " ".join(parts)


def _format_repro_record_failure(target_name: str, record: dict[str, object]) -> str:
    parts = [f"{target_name}: {record.get('status')}"]
    message = record.get("message") or record.get("error_signature")
    if message:
        parts.append(str(message)[:500])
    return " ".join(parts)


def _empty_metadata() -> dict[str, object]:
    return {
        "target_type": "program",
        "entry_register_seeds": [],
        "bootblock": None,
        "resident": None,
        "library": None,
        "custom_structs": [],
        "app_slot_regions": [],
        "seeded_entities": [],
        "seeded_code_labels": [],
        "seeded_code_entrypoints": [],
        "absolute_code_labels": [],
        "execution_views": [],
        "suppressed_seeded_items": [],
    }


def _float_or_none(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) else None
