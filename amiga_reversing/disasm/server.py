from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import json
import logging
import queue
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import NotRequired, TypedDict, cast
from urllib.parse import parse_qs, urlparse

from amiga_reversing.amiga_disk.models import DiskManifest
from amiga_reversing.amiga_disk.project import (
    create_disk_project,
    import_disk_entry_target,
)
from amiga_reversing.disasm import corpus_usage, disk_browser
from amiga_reversing.disasm.api import (
    ListingWindowPayload,
)
from amiga_reversing.disasm.binary_source import (
    resolve_target_binary_source,
    write_source_descriptor,
)
from amiga_reversing.disasm.c_backend import (
    CListingArtifact,
    build_project_listing_artifact_profile,
    extract_disk_entry_with_c_backend,
    type_catalog_from_c_backend,
    validate_amiga_hunk_executable_with_c_backend,
    validate_api_input_struct_with_c_backend,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_hash
from amiga_reversing.disasm.manual_actions import (
    append_manual_action,
    validate_manual_action_payload,
)
from amiga_reversing.disasm.manual_review_items import analysis_review_items
from amiga_reversing.disasm.project_ids import derive_disk_id_from_stem, disk_project_id
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from amiga_reversing.disasm.projects import (
    ProjectRecord,
    create_project,
    dedupe_project_name,
    delete_project,
    derive_project_name,
    get_project,
    list_projects,
    mark_project_opened,
    mark_project_updated,
)
from amiga_reversing.disasm.reproduction import (
    issues_by_row_index,
    load_reproduction_report,
    reproduction_input_stamp,
    reproduction_navigation_entries,
    run_reproduction,
    source_renderer_tool_stamps,
)
from amiga_reversing.disasm.target_ui_edits import append_target_ui_edit

WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
LOGGER = logging.getLogger("amiga_reversing.disasm.server")


class EmptyListingPayload(TypedDict):
    anchor_addr: int | None
    start: int
    end: int
    has_more_before: bool
    has_more_after: bool
    total_rows: int
    rows: list[object]


class AsyncJobPayload(TypedDict):
    job_id: str
    job_kind: str
    project_id: str | None
    result_project_id: str | None
    status: str
    phase_id: str
    phase_index: int
    phase_count: int
    progress_mode: str
    progress_current: int
    progress_total: int
    progress_percent: int
    total_rows: int | None
    error: str | None
    created_at: float
    finished_at: float | None
    cache_key: NotRequired[str | None]
    reproduction_status: NotRequired[str | None]


class ProjectPayload(TypedDict):
    project: dict[str, object]
    disk_manifest: NotRequired[dict[str, object]]
    target_state: NotRequired[dict[str, object]]
    reproduction: NotRequired[dict[str, object]]
    review_warnings: NotRequired[list[dict[str, object]]]


class ApiResponse(TypedDict):
    ok: bool
    data: object


class StaticResponse(TypedDict):
    content_type: str
    body: bytes
    headers: dict[str, str]


_MISSING = object()
_PROJECT_C_LISTING_ARTIFACT_CACHE: dict[str, CListingArtifact] = {}
_PROJECT_LISTING_CACHE_KEY: dict[str, str] = {}
_PROJECT_ANALYSIS_REVIEW_ITEMS_CACHE: dict[str, tuple[str, int, tuple[dict[str, object], ...]]] = {}
_ASYNC_JOBS: dict[str, AsyncJobPayload] = {}
_JOB_EVENT_SUBSCRIBERS: dict[str, list[queue.Queue[dict[str, object]]]] = {}
_JOB_LOCK = threading.Lock()

_LISTING_ARTIFACT_JOB_KIND = "listing_artifact"
_LISTING_PHASE_COUNT = 2
_REPRODUCTION_PHASE_COUNT = 4
_PROJECT_CREATE_EXECUTABLE_PHASE_COUNT = 4
_PROJECT_CREATE_DISK_PHASE_COUNT = 5

_OS_CORRECTIONS_PATH = (
    Path(__file__).resolve().parents[2] / "knowledge" / "amiga_ndk_corrections.json"
)
_ALLOWED_BROWSER_ORIGIN_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _is_allowed_browser_origin(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and (
        parsed.hostname or ""
    ).lower() in _ALLOWED_BROWSER_ORIGIN_HOSTS


def _has_allowed_browser_origin(headers: Mapping[str, str]) -> bool:
    origin = headers.get("Origin")
    if origin:
        return _is_allowed_browser_origin(origin)
    referer = headers.get("Referer")
    if referer:
        return _is_allowed_browser_origin(referer)
    return True


def _os_corrections_payload() -> dict[str, object]:
    with open(_OS_CORRECTIONS_PATH, encoding="utf-8") as handle:
        return cast(dict[str, object], json.load(handle))


def _type_catalog_payload(project_name: str) -> list[dict[str, object]]:
    return type_catalog_from_c_backend(project_name)


def _valid_c_listing_artifact(project_name: str) -> CListingArtifact | None:
    artifact = _PROJECT_C_LISTING_ARTIFACT_CACHE.get(project_name)
    if project_name in _PROJECT_LISTING_CACHE_KEY:
        cache_key = _project_listing_cache_key(project_name)
        if _PROJECT_LISTING_CACHE_KEY.get(project_name) != cache_key:
            _clear_project_listing_cache(project_name)
            return None
    else:
        cache_key = None
    if (
        artifact is not None
        and cache_key is not None
        and _PROJECT_LISTING_CACHE_KEY.get(project_name) == cache_key
    ):
        return artifact
    return None


def _cached_analysis_review_items(
    project_name: str,
    listing_artifact: CListingArtifact,
) -> tuple[dict[str, object], ...]:
    cache_key = _PROJECT_LISTING_CACHE_KEY.get(project_name)
    if cache_key is None:
        return ()
    cached = _PROJECT_ANALYSIS_REVIEW_ITEMS_CACHE.get(project_name)
    artifact_id = id(listing_artifact)
    if cached is not None and cached[0] == cache_key and cached[1] == artifact_id:
        return cached[2]
    analysis_payload_fn = getattr(listing_artifact, "analysis_payload", None)
    if not callable(analysis_payload_fn):
        return ()
    analysis_payload, _ = analysis_payload_fn()
    items = tuple(analysis_review_items(analysis_payload))
    _PROJECT_ANALYSIS_REVIEW_ITEMS_CACHE[project_name] = (cache_key, artifact_id, items)
    return items


def _review_warnings_for_project_dict(project: Mapping[str, object]) -> list[dict[str, object]]:
    review_state = project.get("review_state")
    if review_state not in {"blocked", "needs_review"}:
        return []
    raw_items = project.get("review_items")
    items = [item for item in raw_items if isinstance(item, dict)] if isinstance(raw_items, list | tuple) else []
    open_items = [item for item in items if item.get("state") == "open"]
    blockers = [item for item in open_items if item.get("review_blocker") is True]
    if review_state == "blocked":
        message = f"Review is blocked by {len(blockers) or len(open_items)} live item(s); target cannot be rated clear."
        severity = "error"
    else:
        message = f"Manual review has {len(open_items)} open item(s); target cannot be rated clear yet."
        severity = "warning"
    return [
        {
            "kind": "review_state",
            "review_state": review_state,
            "severity": severity,
            "message": message,
            "open_item_count": len(open_items),
            "blocker_count": len(blockers),
            "item_ids": [
                item["item_id"]
                for item in open_items[:10]
                if isinstance(item.get("item_id"), str)
            ],
            "item_kinds": sorted({
                item["kind"]
                for item in open_items
                if isinstance(item.get("kind"), str)
            }),
        }
    ]


def _review_warnings_for_project_name(project_name: str) -> list[dict[str, object]]:
    project = get_project(project_name)
    return _review_warnings_for_project_dict(
        _project_dict_with_cached_analysis_review(project_name, project)
    )


def _project_listing_generation(project_name: str) -> str | None:
    return "full" if _valid_c_listing_artifact(project_name) is not None else None


def _c_listing_artifact_total_rows(project_name: str) -> int | None:
    artifact = _valid_c_listing_artifact(project_name)
    if artifact is None:
        return None
    try:
        summary, _ = artifact.summary_payload()
    except Exception:
        return None
    total_rows = summary.get("total_rows")
    return total_rows if isinstance(total_rows, int) else None


def _write_api_input_type_override(
    *, library: str, function: str, input_name: str, struct_name: str
) -> None:
    payload = _os_corrections_payload()
    meta = cast(dict[str, object], payload.setdefault("_meta", {}))
    overrides = cast(
        list[dict[str, object]], meta.setdefault("api_input_type_overrides", [])
    )
    replacement: dict[str, object] = {
        "library": library,
        "function": function,
        "input": input_name,
        "type": f"struct {struct_name} *",
        "i_struct": struct_name,
        "seed_origin": "manual",
        "review_status": "validated",
        "citation": "User-edited via disasm UI",
    }
    replaced = False
    for index, existing in enumerate(overrides):
        if (
            existing.get("library") == library
            and existing.get("function") == function
            and existing.get("input") == input_name
        ):
            overrides[index] = replacement
            replaced = True
            break
    if not replaced:
        overrides.append(replacement)
    overrides.sort(
        key=lambda item: (
            str(item.get("library", "")),
            str(item.get("function", "")),
            str(item.get("input", "")),
        )
    )
    _OS_CORRECTIONS_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for artifact in _PROJECT_C_LISTING_ARTIFACT_CACHE.values():
        artifact.close()
    _PROJECT_C_LISTING_ARTIFACT_CACHE.clear()
    _PROJECT_LISTING_CACHE_KEY.clear()
    _PROJECT_ANALYSIS_REVIEW_ITEMS_CACHE.clear()
    _cancel_listing_jobs()


def _validate_api_input_struct(
    project_name: str,
    library: str,
    function: str,
    input_name: str,
    struct_name: str,
) -> dict[str, object]:
    return validate_api_input_struct_with_c_backend(
        project_name, library, function, input_name, struct_name
    )


def _annotate_listing_payload(
    project_name: str, payload: ListingWindowPayload
) -> ListingWindowPayload:
    annotated_rows: list[dict[str, object]] = []
    repro_issues = _active_reproduction_issues_by_row_index(project_name)
    window_start = int(payload.get("start") or 0)
    for relative_index, row in enumerate(payload["rows"]):
        annotations: list[str] = []
        row_issues = repro_issues.get(window_start + relative_index, [])
        if row_issues:
            annotations.append("REPRO: " + str(row_issues[0].get("summary") or row_issues[0].get("message") or "issue"))
        annotated_row = dict(row)
        if annotations:
            annotated_row["view_annotations"] = annotations
        if row_issues:
            annotated_row["repro_issues"] = row_issues
        annotated_rows.append(annotated_row)
    result = {
        **payload,
        "rows": annotated_rows,
    }
    review_warnings = _review_warnings_for_project_name(project_name)
    if review_warnings:
        result["review_warnings"] = review_warnings
    return result


def _active_reproduction_report(project_name: str) -> dict[str, object] | None:
    try:
        report = load_reproduction_report(project_name, project_root=PROJECT_ROOT)
    except (FileNotFoundError, ValueError, RuntimeError):
        return None
    if report.get("stale"):
        return None
    return report


def _active_reproduction_issues_by_row_index(
    project_name: str,
) -> dict[int, list[dict[str, object]]]:
    report = _active_reproduction_report(project_name)
    if report is None:
        return {}
    return issues_by_row_index(report)


def _not_ready_reproduction_payload(
    project_name: str, error: str | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "target": project_name,
        "status": "not_ready",
        "exact": False,
        "stale": False,
        "issues": [],
        "diff_ranges": [],
        "assembler_diagnostics": [],
    }
    if error:
        payload["error"] = error
    return payload


def _active_reproduction_job(
    project_name: str, cache_key: str | None = None
) -> AsyncJobPayload | None:
    with _JOB_LOCK:
        for job in _ASYNC_JOBS.values():
            if (
                job["job_kind"] == "reproduction"
                and job["project_id"] == project_name
                and job["status"] in {"queued", "building"}
                and (cache_key is None or job.get("cache_key") == cache_key)
            ):
                return cast(AsyncJobPayload, dict(job))
    return None


def _reproduction_payload_with_job(
    report: dict[str, object], job: AsyncJobPayload | None, *, project_name: str | None = None
) -> dict[str, object]:
    payload = dict(report)
    if job is not None and job["status"] in {"queued", "building"}:
        payload["refreshing"] = True
        payload["active_job"] = dict(job)
    else:
        payload["refreshing"] = False
    if project_name is not None:
        review_warnings = _review_warnings_for_project_name(project_name)
        if review_warnings:
            payload["review_warnings"] = review_warnings
    return payload


def _current_reproduction_payload(
    project_name: str, *, auto_start: bool = False
) -> dict[str, object]:
    try:
        report = load_reproduction_report(project_name, project_root=PROJECT_ROOT)
    except Exception as exc:
        report = _not_ready_reproduction_payload(project_name, str(exc))
    cache_key = _reproduction_cache_key(project_name)
    job: AsyncJobPayload | None = None
    if "reproduction-unresolved" not in cache_key:
        job = _active_reproduction_job(project_name, cache_key)
        if (
            job is None
            and auto_start
            and (report.get("status") == "not_ready" or bool(report.get("stale")))
        ):
            job = _start_reproduction_job(project_name, force=False)
            if job["status"] == "ready":
                with contextlib.suppress(Exception):
                    report = load_reproduction_report(project_name, project_root=PROJECT_ROOT)
                job = None
    return _reproduction_payload_with_job(report, job, project_name=project_name)


def _overlay_listing_navigation_payload(
    project_name: str,
    payload: dict[str, object],
    listing_artifact: CListingArtifact | None = None,
) -> dict[str, object]:
    groups = cast(dict[str, list[dict[str, object]]], payload.setdefault("groups", {}))
    for group_name in (
        "repro-issues",
        "typed-data",
        "typed-gaps",
        "relocations",
        "api-calls",
        "app-slots",
        "app-slot-regions",
        "app-slot-gaps",
        "app-slot-field-gaps",
        "app-slot-suggestions",
        "app-slot-api-args",
        "manual-review",
        "labels",
        "equates",
        "comments",
    ):
        groups.setdefault(group_name, [])
    repro_report = _active_reproduction_report(project_name)
    if repro_report is not None:
        groups["repro-issues"] = reproduction_navigation_entries(repro_report)
    if "analysis_generation" not in payload or payload.get("analysis_generation") is None:
        payload["analysis_generation"] = _project_listing_generation(project_name)
    if "type_flow_analysis" not in payload or not isinstance(payload.get("type_flow_analysis"), dict):
        payload["type_flow_analysis"] = {}
    if listing_artifact is not None:
        groups["manual-review"] = list(
            _cached_analysis_review_items(project_name, listing_artifact)
        )
    payload["groups"] = groups
    return payload


def _clear_project_listing_cache(project_name: str) -> None:
    artifact = _PROJECT_C_LISTING_ARTIFACT_CACHE.pop(project_name, None)
    if artifact is not None:
        artifact.close()
    _PROJECT_LISTING_CACHE_KEY.pop(project_name, None)
    _PROJECT_ANALYSIS_REVIEW_ITEMS_CACHE.pop(project_name, None)


def _prewarm_analysis_review_items(project_name: str) -> None:
    artifact = _valid_c_listing_artifact(project_name)
    if artifact is not None:
        _cached_analysis_review_items(project_name, artifact)


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _log_event(message: str, **fields: object) -> None:
    suffix = " ".join(f"{key}={value}" for key, value in fields.items())
    LOGGER.info("%s%s", message, f" {suffix}" if suffix else "")


def _parse_int_arg(
    values: dict[str, list[str]], key: str, default: int | None = None
) -> int | None:
    raw_values = values.get(key)
    raw = raw_values[0] if raw_values else None
    if raw in (None, ""):
        return default
    assert raw is not None
    return int(raw, 0)


def _first_query_value(values: dict[str, list[str]], key: str) -> str | None:
    raw_values = values.get(key)
    raw = raw_values[0] if raw_values else None
    if raw in (None, ""):
        return None
    return raw


def _empty_listing_payload(addr: int | None) -> EmptyListingPayload:
    return {
        "anchor_addr": addr,
        "start": 0,
        "end": 0,
        "has_more_before": False,
        "has_more_after": False,
        "total_rows": 0,
        "rows": [],
    }


def _phase_progress(phase_index: int, phase_count: int) -> tuple[int, int, int]:
    if phase_count <= 0:
        raise ValueError(f"phase_count must be positive, got {phase_count}")
    if phase_index < 0 or phase_index > phase_count:
        raise ValueError(f"phase_index {phase_index} outside 0..{phase_count}")
    completed = 0 if phase_index == 0 else phase_index - 1
    return completed, phase_count, int((completed / phase_count) * 100)


def _job_payload(job_id: str) -> AsyncJobPayload:
    with _JOB_LOCK:
        job = dict(_ASYNC_JOBS[job_id])
    return cast(AsyncJobPayload, job)


def _job_payload_or_none(job_id: str) -> AsyncJobPayload | None:
    with _JOB_LOCK:
        if job_id not in _ASYNC_JOBS:
            return None
    return _job_payload(job_id)


def _publish_job_event_payload(job_id: str, payload: Mapping[str, object]) -> None:
    with _JOB_LOCK:
        subscribers = list(_JOB_EVENT_SUBSCRIBERS.get(job_id, []))
    for subscriber in subscribers:
        with contextlib.suppress(queue.Full):  # pragma: no cover - queues are unbounded
            subscriber.put_nowait(dict(payload))


def _publish_job_event(job_id: str) -> None:
    payload = _job_payload_or_none(job_id)
    if payload is not None:
        _publish_job_event_payload(job_id, payload)


def _publish_listing_artifact_ready_event(
    job_id: str, project_name: str, total_rows: int
) -> None:
    _publish_job_event_payload(
        job_id,
        {
            "_event_type": "listing_artifact_ready",
            "project_id": project_name,
            "total_rows": total_rows,
            "changed_ranges": [],
        },
    )


def _cancel_listing_jobs(project_name: str | None = None) -> None:
    canceled: list[tuple[str, dict[str, object]]] = []
    with _JOB_LOCK:
        stale_job_ids = [
            job_id
            for job_id, job in _ASYNC_JOBS.items()
            if job["job_kind"] == _LISTING_ARTIFACT_JOB_KIND
            and (project_name is None or job["project_id"] == project_name)
        ]
        for job_id in stale_job_ids:
            job = dict(_ASYNC_JOBS[job_id])
            job["status"] = "failed"
            job["phase_id"] = "error"
            job["error"] = "job canceled"
            job["finished_at"] = time.time()
            canceled.append((job_id, dict(job)))
            del _ASYNC_JOBS[job_id]
    for job_id, payload in canceled:
        _publish_job_event_payload(job_id, payload)


def _set_job_state(
    job_id: str,
    *,
    status: str | object = _MISSING,
    phase_id: str | object = _MISSING,
    phase_index: int | object = _MISSING,
    phase_count: int | object = _MISSING,
    progress_mode: str | object = _MISSING,
    progress_current: int | object = _MISSING,
    progress_total: int | object = _MISSING,
    progress_percent: int | object = _MISSING,
    project_id: str | None | object = _MISSING,
    result_project_id: str | None | object = _MISSING,
    total_rows: int | None | object = _MISSING,
    error: str | None | object = _MISSING,
    finished_at: float | None | object = _MISSING,
    reproduction_status: str | None | object = _MISSING,
) -> bool:
    updated = False
    with _JOB_LOCK:
        job = _ASYNC_JOBS.get(job_id)
        if job is None:
            return False
        if status is not _MISSING:
            assert isinstance(status, str)
            job["status"] = status
        if phase_id is not _MISSING:
            assert isinstance(phase_id, str)
            job["phase_id"] = phase_id
        if phase_index is not _MISSING:
            assert isinstance(phase_index, int)
            job["phase_index"] = phase_index
        if phase_count is not _MISSING:
            assert isinstance(phase_count, int)
            job["phase_count"] = phase_count
        if progress_mode is not _MISSING:
            assert isinstance(progress_mode, str)
            job["progress_mode"] = progress_mode
        if progress_current is not _MISSING:
            assert isinstance(progress_current, int)
            job["progress_current"] = progress_current
        if progress_total is not _MISSING:
            assert isinstance(progress_total, int)
            job["progress_total"] = progress_total
        if progress_percent is not _MISSING:
            assert isinstance(progress_percent, int)
            job["progress_percent"] = progress_percent
        if project_id is not _MISSING:
            assert project_id is None or isinstance(project_id, str)
            job["project_id"] = project_id
        if result_project_id is not _MISSING:
            assert result_project_id is None or isinstance(result_project_id, str)
            job["result_project_id"] = result_project_id
        if total_rows is not _MISSING:
            assert total_rows is None or isinstance(total_rows, int)
            job["total_rows"] = total_rows
        if error is not _MISSING:
            assert error is None or isinstance(error, str)
            job["error"] = error
        if finished_at is not _MISSING:
            assert finished_at is None or isinstance(finished_at, float)
            job["finished_at"] = finished_at
        if reproduction_status is not _MISSING:
            assert reproduction_status is None or isinstance(reproduction_status, str)
            job["reproduction_status"] = reproduction_status
        updated = True
    if updated:
        _publish_job_event(job_id)
    return True


def _set_job_phase(
    job_id: str, *, phase_id: str, phase_index: int, phase_count: int
) -> bool:
    progress_current, progress_total, progress_percent = _phase_progress(
        phase_index, phase_count
    )
    return _set_job_state(
        job_id,
        phase_id=phase_id,
        phase_index=phase_index,
        phase_count=phase_count,
        progress_mode="determinate",
        progress_current=progress_current,
        progress_total=progress_total,
        progress_percent=progress_percent,
    )


def _project_create_phase_count(filename: str) -> int:
    return (
        _PROJECT_CREATE_DISK_PHASE_COUNT
        if Path(filename).suffix.lower() == ".adf"
        else _PROJECT_CREATE_EXECUTABLE_PHASE_COUNT
    )


def _file_cache_stamp(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError:
        return f"{path}:missing"
    return f"{path}:{stat.st_size}:{stat.st_mtime_ns}"


def _project_listing_cache_key(project_name: str) -> str:
    try:
        paths = resolve_project_paths(project_name, project_root=PROJECT_ROOT)
    except (FileNotFoundError, ValueError):
        return f"{project_name}|unresolved"
    source = paths.binary_source
    parts = [project_name, source.kind, source.display_path]
    source_path = getattr(source, "path", None)
    if isinstance(source_path, Path):
        parts.append(_file_cache_stamp(source_path))
    adf_path = getattr(source, "adf_path", None)
    if isinstance(adf_path, Path):
        parts.append(_file_cache_stamp(adf_path))
        parts.append(str(getattr(source, "entry_path", "")))
    for attr in ("address_model", "load_address", "entrypoint", "code_start_offset"):
        if hasattr(source, attr):
            parts.append(f"{attr}={getattr(source, attr)}")
    parts.append(_file_cache_stamp(paths.target_dir / "source_binary.json"))
    parts.append(
        "source_renderer_tool_stamps="
        + json.dumps(source_renderer_tool_stamps(PROJECT_ROOT), sort_keys=True)
    )
    try:
        parts.append(f"effective_metadata={effective_metadata_hash(paths.target_dir)}")
    except ValueError as exc:
        parts.append(f"effective_metadata_error={exc}")
    return "|".join(parts)


def _cache_satisfies_listing(project_name: str, cache_key: str) -> bool:
    if project_name not in _PROJECT_LISTING_CACHE_KEY:
        return False
    if _PROJECT_LISTING_CACHE_KEY.get(project_name) != cache_key:
        return False
    return _PROJECT_C_LISTING_ARTIFACT_CACHE.get(project_name) is not None


def _build_rows_job(job_id: str, project_name: str) -> None:
    phase_count = _LISTING_PHASE_COUNT
    total_rows = 0
    listing_artifact: CListingArtifact | None = None
    try:
        cache_key = _project_listing_cache_key(project_name)
        _log_event("listing_job start", job_id=job_id, project=project_name, generation="full")
        if not _set_job_state(job_id, status="building"):
            return
        if not _set_job_phase(job_id, phase_id="build_c_artifact", phase_index=1, phase_count=phase_count):
            return
        _log_event(
            "listing_job phase",
            job_id=job_id,
            project=project_name,
            generation="full",
            phase="build_c_artifact",
        )
        total_rows, _profile, listing_artifact = build_project_listing_artifact_profile(project_name)
        if not _set_job_phase(job_id, phase_id="cache_artifact", phase_index=2, phase_count=phase_count):
            if listing_artifact is not None:
                listing_artifact.close()
            return
        if _project_listing_cache_key(project_name) != cache_key:
            if listing_artifact is not None:
                listing_artifact.close()
            _set_job_state(
                job_id,
                status="failed",
                phase_id="stale",
                error="project changed while listing job was building",
                finished_at=time.time(),
            )
            return
        with _JOB_LOCK:
            if job_id not in _ASYNC_JOBS:
                return
            job_cache_key = _ASYNC_JOBS[job_id].get("cache_key")
            if job_cache_key is not None and job_cache_key != cache_key:
                if listing_artifact is not None:
                    listing_artifact.close()
                return
            _PROJECT_LISTING_CACHE_KEY[project_name] = cache_key
            old_artifact = _PROJECT_C_LISTING_ARTIFACT_CACHE.get(project_name)
            if listing_artifact is not None:
                _PROJECT_C_LISTING_ARTIFACT_CACHE[project_name] = listing_artifact
                listing_artifact = None
            if old_artifact is not None and old_artifact is not _PROJECT_C_LISTING_ARTIFACT_CACHE.get(project_name):
                old_artifact.close()
        _prewarm_analysis_review_items(project_name)
        _log_event(
            "listing_job artifact_ready",
            job_id=job_id,
            project=project_name,
            total_rows=total_rows,
        )
        _publish_listing_artifact_ready_event(job_id, project_name, total_rows)
        if not _set_job_state(
            job_id,
            total_rows=total_rows,
        ):
            if listing_artifact is not None:
                listing_artifact.close()
            return
        _log_event(
            "listing_job done",
            job_id=job_id,
            project=project_name,
            generation="full",
            total_rows=total_rows,
        )
        _set_job_state(
            job_id,
            status="ready",
            phase_id="done",
            phase_index=phase_count,
            phase_count=phase_count,
            progress_mode="determinate",
            progress_current=phase_count,
            progress_total=phase_count,
            progress_percent=100,
            total_rows=total_rows,
            finished_at=time.time(),
        )
        _start_reproduction_job_if_needed(project_name)
    except Exception as exc:  # pragma: no cover
        if listing_artifact is not None:
            listing_artifact.close()
        _log_event(
            "listing_job failed", job_id=job_id, project=project_name, error=str(exc)
        )
        _set_job_state(
            job_id,
            status="failed",
            phase_id="error",
            error=str(exc),
            finished_at=time.time(),
        )


def _start_listing_job(project_name: str) -> AsyncJobPayload:
    cache_key = _project_listing_cache_key(project_name)
    if _cache_satisfies_listing(project_name, cache_key):
        _prewarm_analysis_review_items(project_name)
        total_rows = _c_listing_artifact_total_rows(project_name)
        job_id = f"cached-listing-artifact-{project_name}"
        payload: AsyncJobPayload = {
            "job_id": job_id,
            "job_kind": _LISTING_ARTIFACT_JOB_KIND,
            "project_id": project_name,
            "result_project_id": project_name,
            "status": "ready",
            "phase_id": "done",
            "phase_index": _LISTING_PHASE_COUNT,
            "phase_count": _LISTING_PHASE_COUNT,
            "progress_mode": "determinate",
            "progress_current": _LISTING_PHASE_COUNT,
            "progress_total": _LISTING_PHASE_COUNT,
            "progress_percent": 100,
            "total_rows": total_rows,
            "error": None,
            "created_at": time.time(),
            "finished_at": time.time(),
            "cache_key": cache_key,
        }
        with _JOB_LOCK:
            _ASYNC_JOBS[job_id] = payload
        _start_reproduction_job_if_needed(project_name)
        return payload

    with _JOB_LOCK:
        for _existing_id, job in _ASYNC_JOBS.items():
            if (
                job["job_kind"] == _LISTING_ARTIFACT_JOB_KIND
                and job["project_id"] == project_name
                and job.get("cache_key") == cache_key
                and job["status"] in {"queued", "building"}
            ):
                return cast(AsyncJobPayload, dict(job))
        job_id = str(uuid.uuid4())
        _ASYNC_JOBS[job_id] = {
            "job_id": job_id,
            "job_kind": _LISTING_ARTIFACT_JOB_KIND,
            "project_id": project_name,
            "result_project_id": project_name,
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": _LISTING_PHASE_COUNT,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": _LISTING_PHASE_COUNT,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": time.time(),
            "finished_at": None,
            "cache_key": cache_key,
        }

    worker = threading.Thread(
        target=_build_rows_job,
        args=(job_id, project_name),
        daemon=True,
    )
    worker.start()
    return _job_payload(job_id)


def _reproduction_cache_key(project_name: str) -> str:
    try:
        stamp = reproduction_input_stamp(project_name, project_root=PROJECT_ROOT)
    except Exception as exc:
        return f"{project_name}|reproduction-unresolved|{exc}"
    return json.dumps(stamp, sort_keys=True)


def _build_reproduction_job(job_id: str, project_name: str) -> None:
    phase_count = _REPRODUCTION_PHASE_COUNT
    try:
        cache_key = _reproduction_cache_key(project_name)
        pre_rendered_source_profile: dict[str, object] | None = None
        pre_rendered_source_text: str | None = None
        row_for_section_offset = None
        _log_event("reproduction_job start", job_id=job_id, project=project_name)
        if not _set_job_state(job_id, status="building"):
            return
        if not _set_job_phase(job_id, phase_id="prepare", phase_index=1, phase_count=phase_count):
            return
        listing_artifact = _valid_c_listing_artifact(project_name)
        if listing_artifact is not None:
            artifact_row_lookup = getattr(listing_artifact, "row_for_source_offset", None)
            if artifact_row_lookup is not None:
                row_for_section_offset = (
                    lambda section_index, offset: artifact_row_lookup(
                        section_index=section_index,
                        offset=offset,
                    )
                )
            try:
                pre_rendered_source_text, pre_rendered_source_profile = listing_artifact.source_text_with_profile()
            except Exception as exc:
                message = f"artifact source unavailable: {exc}"
                _log_event(
                    "reproduction_job artifact_source_unavailable",
                    job_id=job_id,
                    project=project_name,
                    error=exc,
                )
                _set_job_state(
                    job_id,
                    status="failed",
                    phase_id="error",
                    error=message,
                    finished_at=time.time(),
                )
                return
        if not _set_job_phase(job_id, phase_id="assemble", phase_index=2, phase_count=phase_count):
            return
        if pre_rendered_source_text is not None:
            if row_for_section_offset is not None:
                try:
                    report = run_reproduction(
                        project_name,
                        project_root=PROJECT_ROOT,
                        pre_rendered_source_text=pre_rendered_source_text,
                        pre_rendered_source_profile=pre_rendered_source_profile,
                        row_for_section_offset=row_for_section_offset,
                    )
                except TypeError as exc:
                    if (
                        "row_for_section_offset" in str(exc)
                        and "unexpected keyword argument" in str(exc)
                    ):
                        report = run_reproduction(
                            project_name,
                            project_root=PROJECT_ROOT,
                            pre_rendered_source_text=pre_rendered_source_text,
                            pre_rendered_source_profile=pre_rendered_source_profile,
                        )
                    else:
                        raise
            else:
                report = run_reproduction(
                    project_name,
                    project_root=PROJECT_ROOT,
                    pre_rendered_source_text=pre_rendered_source_text,
                    pre_rendered_source_profile=pre_rendered_source_profile,
                )
        else:
            report = run_reproduction(
                project_name,
                project_root=PROJECT_ROOT,
                row_for_section_offset=row_for_section_offset,
            )
        if not _set_job_phase(job_id, phase_id="diff", phase_index=3, phase_count=phase_count):
            return
        if _reproduction_cache_key(project_name) != cache_key:
            _set_job_state(
                job_id,
                status="failed",
                phase_id="stale",
                error="project changed while reproduction job was running",
                finished_at=time.time(),
            )
            return
        _set_job_state(
            job_id,
            status="ready",
            phase_id="done",
            phase_index=phase_count,
            phase_count=phase_count,
            progress_mode="determinate",
            progress_current=phase_count,
            progress_total=phase_count,
            progress_percent=100,
            finished_at=time.time(),
            reproduction_status=str(report.get("status") or ""),
        )
        _log_event(
            "reproduction_job done",
            job_id=job_id,
            project=project_name,
            status=report.get("status"),
        )
    except Exception as exc:  # pragma: no cover
        _log_event("reproduction_job failed", job_id=job_id, project=project_name, error=str(exc))
        _set_job_state(
            job_id,
            status="failed",
            phase_id="error",
            error=str(exc),
            finished_at=time.time(),
        )


def _start_reproduction_job(project_name: str, *, force: bool = True) -> AsyncJobPayload:
    cache_key = _reproduction_cache_key(project_name)
    if not force:
        try:
            report = load_reproduction_report(project_name, project_root=PROJECT_ROOT)
        except Exception:
            report = {"status": "not_ready", "stale": True}
        if report.get("status") != "not_ready" and report.get("stale") is False:
            job_id = f"cached-reproduction-{project_name}"
            payload: AsyncJobPayload = {
                "job_id": job_id,
                "job_kind": "reproduction",
                "project_id": project_name,
                "result_project_id": project_name,
                "status": "ready",
                "phase_id": "done",
                "phase_index": _REPRODUCTION_PHASE_COUNT,
                "phase_count": _REPRODUCTION_PHASE_COUNT,
                "progress_mode": "determinate",
                "progress_current": _REPRODUCTION_PHASE_COUNT,
                "progress_total": _REPRODUCTION_PHASE_COUNT,
                "progress_percent": 100,
                "total_rows": None,
                "error": None,
                "created_at": time.time(),
                "finished_at": time.time(),
                "cache_key": cache_key,
                "reproduction_status": str(report.get("status") or ""),
            }
            with _JOB_LOCK:
                _ASYNC_JOBS[job_id] = payload
            return payload
    with _JOB_LOCK:
        for _existing_id, job in _ASYNC_JOBS.items():
            if (
                job["job_kind"] == "reproduction"
                and job["project_id"] == project_name
                and job.get("cache_key") == cache_key
                and job["status"] in {"queued", "building"}
            ):
                return cast(AsyncJobPayload, dict(job))
        job_id = str(uuid.uuid4())
        _ASYNC_JOBS[job_id] = {
            "job_id": job_id,
            "job_kind": "reproduction",
            "project_id": project_name,
            "result_project_id": project_name,
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": _REPRODUCTION_PHASE_COUNT,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": _REPRODUCTION_PHASE_COUNT,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": time.time(),
            "finished_at": None,
            "cache_key": cache_key,
            "reproduction_status": None,
        }
    worker = threading.Thread(
        target=_build_reproduction_job,
        args=(job_id, project_name),
        daemon=True,
    )
    worker.start()
    return _job_payload(job_id)


def _start_reproduction_job_if_needed(project_name: str) -> AsyncJobPayload | None:
    try:
        project = get_project(project_name)
    except FileNotFoundError:
        return None
    if project.kind != "binary" or not project.ready:
        return None
    if "reproduction-unresolved" in _reproduction_cache_key(project_name):
        return None
    return _start_reproduction_job(project_name, force=False)


def _cancel_reproduction_jobs(project_name: str | None = None) -> None:
    canceled: list[tuple[str, dict[str, object]]] = []
    with _JOB_LOCK:
        stale_job_ids = [
            job_id
            for job_id, job in _ASYNC_JOBS.items()
            if job["job_kind"] == "reproduction"
            and (project_name is None or job["project_id"] == project_name)
        ]
        for job_id in stale_job_ids:
            job = dict(_ASYNC_JOBS[job_id])
            job["status"] = "failed"
            job["phase_id"] = "error"
            job["error"] = "job canceled"
            job["finished_at"] = time.time()
            canceled.append((job_id, dict(job)))
            del _ASYNC_JOBS[job_id]
    for job_id, payload in canceled:
        _publish_job_event_payload(job_id, payload)


def _build_project_create_job(job_id: str, body: dict[str, object]) -> None:
    try:
        project = _create_project_from_media(body, job_id=job_id)
        phase_count = _job_payload(job_id)["phase_count"]
        _set_job_state(
            job_id,
            status="ready",
            result_project_id=project.id,
            phase_id="done",
            phase_index=phase_count,
            phase_count=phase_count,
            progress_mode="determinate",
            progress_current=phase_count,
            progress_total=phase_count,
            progress_percent=100,
            finished_at=time.time(),
        )
    except Exception as exc:  # pragma: no cover
        _log_event("project_create failed", job_id=job_id, error=str(exc))
        _set_job_state(
            job_id,
            status="failed",
            phase_id="error",
            error=str(exc),
            finished_at=time.time(),
        )


def _start_project_create_job(body: dict[str, object]) -> AsyncJobPayload:
    filename = body.get("filename")
    if not isinstance(filename, str):
        raise ValueError("Uploaded media filename is missing")
    phase_count = _project_create_phase_count(filename)
    job_id = str(uuid.uuid4())
    with _JOB_LOCK:
        _ASYNC_JOBS[job_id] = {
            "job_id": job_id,
            "job_kind": "project_create",
            "project_id": None,
            "result_project_id": None,
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": phase_count,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": phase_count,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": time.time(),
            "finished_at": None,
        }
    worker = threading.Thread(
        target=_build_project_create_job,
        args=(job_id, dict(body)),
        daemon=True,
    )
    worker.start()
    return _job_payload(job_id)


def _failed_project_create_job(error: str) -> AsyncJobPayload:
    job_id = str(uuid.uuid4())
    now = time.time()
    with _JOB_LOCK:
        _ASYNC_JOBS[job_id] = {
            "job_id": job_id,
            "job_kind": "project_create",
            "project_id": None,
            "result_project_id": None,
            "status": "failed",
            "phase_id": "error",
            "phase_index": 0,
            "phase_count": _PROJECT_CREATE_EXECUTABLE_PHASE_COUNT,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": _PROJECT_CREATE_EXECUTABLE_PHASE_COUNT,
            "progress_percent": 0,
            "total_rows": None,
            "error": error,
            "created_at": now,
            "finished_at": now,
        }
    return _job_payload(job_id)


def _project_payload(project_name: str) -> ProjectPayload:
    project = get_project(project_name)
    project_dict = _project_dict_with_cached_analysis_review(project_name, project)
    payload: ProjectPayload = {"project": project_dict}
    review_warnings = _review_warnings_for_project_dict(project_dict)
    if review_warnings:
        payload["review_warnings"] = review_warnings
    if project.kind == "disk":
        manifest_path = project.manifest_path
        if manifest_path is None:
            raise ValueError(f"Disk project {project_name} is missing manifest_path")
        manifest = DiskManifest.load(Path(manifest_path))
        payload["disk_manifest"] = manifest.to_dict()
        target_state_path = Path(manifest_path).with_name("target_state.json")
        if target_state_path.exists():
            try:
                with open(target_state_path, encoding="utf-8") as handle:
                    payload["target_state"] = cast(dict[str, object], json.load(handle))
            except Exception:
                payload["target_state"] = {}
    elif project.kind == "binary" and project.ready:
        payload["reproduction"] = _current_reproduction_payload(project_name)
    return payload


def _project_dict_with_cached_analysis_review(project_name: str, project: ProjectRecord) -> dict[str, object]:
    project_dict = project.to_dict()
    artifact = _valid_c_listing_artifact(project_name)
    if artifact is None:
        return project_dict
    analysis_items = _cached_analysis_review_items(project_name, artifact)
    if not analysis_items:
        return project_dict
    existing_items = project_dict.get("review_items")
    review_items = [
        *(existing_items if isinstance(existing_items, list | tuple) else []),
        *analysis_items,
    ]
    project_dict["review_items"] = review_items
    if project_dict.get("review_state") != "blocked" and any(item.get("state") == "open" for item in analysis_items):
        project_dict["review_state"] = "needs_review"
    return project_dict


def _project_disk_browser_payload(project_name: str, path: str = "") -> dict[str, object]:
    project = get_project(project_name)
    if project.kind != "disk":
        raise ValueError(f"Project {project_name} is not a disk project")
    manifest_path = project.manifest_path
    if manifest_path is None:
        raise ValueError(f"Disk project {project_name} is missing manifest_path")
    manifest = DiskManifest.load(Path(manifest_path))
    manifest_dict = manifest.to_dict()
    target_index: dict[str, str] = {}
    for target in manifest_dict.get("imported_targets", []):
        if not isinstance(target, dict):
            continue
        target_name = target.get("target_name")
        entry_path = target.get("entry_path")
        if not isinstance(target_name, str) or not isinstance(entry_path, str):
            continue
        target_index[entry_path.strip().strip("/").lower()] = target_name
    return disk_browser.payload_from_project_manifest(
        manifest_dict,
        path,
        content_for_entry=lambda entry: _project_disk_entry_content_payload(manifest_dict, entry),
        target_index=target_index,
    )


def _project_disk_entry_content_payload(
    manifest: dict[str, object],
    entry: dict[str, object],
) -> dict[str, object]:
    extracted_path = entry.get("extracted_path")
    try:
        if isinstance(extracted_path, str) and extracted_path:
            path = Path(extracted_path)
            data = path.read_bytes()
        else:
            source_path = manifest.get("source_path")
            entry_path = entry.get("full_path") or entry.get("path")
            if not isinstance(source_path, str) or not isinstance(entry_path, str):
                raise RuntimeError("Disk file entry is missing source path metadata")
            data = extract_disk_entry_with_c_backend(
                Path(source_path),
                entry_path,
                project_root=PROJECT_ROOT,
            )
    except Exception as exc:
        return disk_browser.content_error_payload(str(exc), disk_browser.entry_size(entry))
    return disk_browser.content_payload_from_bytes(data)


def resolve_static_response(path: str) -> StaticResponse:
    relative = "index.html" if path in ("", "/") else path.lstrip("/")
    direct_file_path = (WEB_ROOT / relative).resolve()
    if (
        "/" not in relative
        and direct_file_path != WEB_ROOT.resolve()
        and not direct_file_path.exists()
    ):
        relative = "index.html"
    file_path = (WEB_ROOT / relative).resolve()
    if WEB_ROOT.resolve() not in file_path.parents and file_path != WEB_ROOT.resolve():
        raise FileNotFoundError(f"Unknown route: {path}")
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Unknown route: {path}")

    content_type = "text/plain; charset=utf-8"
    if file_path.suffix == ".html":
        content_type = "text/html; charset=utf-8"
    elif file_path.suffix == ".js":
        content_type = "application/javascript; charset=utf-8"
    elif file_path.suffix == ".css":
        content_type = "text/css; charset=utf-8"
    headers = {"Cache-Control": "no-store"}
    return {
        "content_type": content_type,
        "body": file_path.read_bytes(),
        "headers": headers,
    }


class DisasmApiHandler(BaseHTTPRequestHandler):
    server_version = "DisasmApi/0.1"

    def _reject_forbidden_api_origin(self, path: str) -> bool:
        if not path.startswith("/api/") or _has_allowed_browser_origin(
            cast(Mapping[str, str], self.headers)
        ):
            return False
        body = _json_bytes({"ok": False, "error": "Forbidden browser origin"})
        self.send_response(403)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True

    def _handle_request(
        self,
        method: str,
        handler: Callable[[], tuple[bytes, str, int, dict[str, str] | None]],
    ) -> None:
        started = time.time()
        status = 200
        content_type = "application/json; charset=utf-8"
        extra_headers: dict[str, str] | None = None
        try:
            body, content_type, status, extra_headers = handler()
        except FileNotFoundError as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            status = 404
        except (FileExistsError, ValueError) as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            status = 400
        except Exception as exc:  # pragma: no cover
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            status = 500
        elapsed_ms = int((time.time() - started) * 1000)
        _log_event(
            "request",
            method=method,
            path=self.path,
            status=status,
            elapsed_ms=elapsed_ms,
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if extra_headers is not None:
            for name, value in extra_headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _write_sse_event(self, event_name: str, payload: dict[str, object]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.wfile.write(f"event: {event_name}\n".encode("ascii"))
        self.wfile.write(b"data: " + data + b"\n\n")
        self.wfile.flush()

    def _write_sse_job_event(self, payload: AsyncJobPayload) -> None:
        self._write_sse_event("job", cast(dict[str, object], payload))

    def _handle_job_events(self, query: dict[str, list[str]]) -> None:
        job_values = query.get("job_id")
        job_id = job_values[0] if job_values else None
        if not job_id:
            raise ValueError("Missing job_id")
        initial_payload = _job_payload_or_none(job_id)
        if initial_payload is None:
            raise FileNotFoundError(f"Unknown job: {job_id}")

        subscriber: queue.Queue[dict[str, object]] = queue.Queue()
        with _JOB_LOCK:
            _JOB_EVENT_SUBSCRIBERS.setdefault(job_id, []).append(subscriber)

        started = time.time()
        status = 200
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self._write_sse_job_event(initial_payload)
            if initial_payload["status"] not in {"queued", "building"}:
                return
            while True:
                try:
                    payload = subscriber.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    continue
                event_name = cast(str, payload.get("_event_type", "job"))
                payload = dict(payload)
                payload.pop("_event_type", None)
                self._write_sse_event(event_name, payload)
                if event_name == "job" and payload["status"] not in {"queued", "building"}:
                    return
        except (BrokenPipeError, ConnectionResetError, OSError):
            status = 499
        finally:
            with _JOB_LOCK:
                subscribers = _JOB_EVENT_SUBSCRIBERS.get(job_id)
                if subscribers is not None:
                    with contextlib.suppress(ValueError):
                        subscribers.remove(subscriber)
                    if not subscribers:
                        del _JOB_EVENT_SUBSCRIBERS[job_id]
            elapsed_ms = int((time.time() - started) * 1000)
            _log_event(
                "request",
                method="GET",
                path=self.path,
                status=status,
                elapsed_ms=elapsed_ms,
            )

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if self._reject_forbidden_api_origin(parsed.path):
            return
        if parsed.path == "/api/jobs/events":
            try:
                self._handle_job_events(parse_qs(parsed.query))
            except FileNotFoundError as exc:
                self.send_error(404, str(exc))
            except ValueError as exc:
                self.send_error(400, str(exc))
            return

        def handler() -> tuple[bytes, str, int, dict[str, str] | None]:
            if parsed.path == "/" or not parsed.path.startswith("/api/"):
                response = resolve_static_response(parsed.path)
                return (
                    response["body"],
                    response["content_type"],
                    200,
                    response["headers"],
                )
            payload = route_request("GET", parsed.path, parse_qs(parsed.query))
            return _json_bytes(payload), "application/json; charset=utf-8", 200, None

        self._handle_request("GET", handler)

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        if self._reject_forbidden_api_origin(parsed.path):
            return

        def handler() -> tuple[bytes, str, int, dict[str, str] | None]:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            assert isinstance(payload, dict), "PATCH body must be a JSON object"
            body = _json_bytes(
                route_request(
                    "PATCH",
                    parsed.path,
                    parse_qs(parsed.query),
                    cast(dict[str, object], payload),
                )
            )
            return body, "application/json; charset=utf-8", 200, None

        self._handle_request("PATCH", handler)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if self._reject_forbidden_api_origin(parsed.path):
            return

        def handler() -> tuple[bytes, str, int, dict[str, str] | None]:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            assert isinstance(payload, dict), "POST body must be a JSON object"
            body = _json_bytes(
                route_request(
                    "POST",
                    parsed.path,
                    parse_qs(parsed.query),
                    cast(dict[str, object], payload),
                )
            )
            return body, "application/json; charset=utf-8", 200, None

        self._handle_request("POST", handler)

    def log_message(self, format: str, *args: object) -> None:
        _log_event("http", detail=format % args)


def route_request(
    method: str,
    path: str,
    query: dict[str, list[str]],
    body: dict[str, object] | None = None,
) -> ApiResponse:
    if method == "GET" and path == "/api/projects":
        return {
            "ok": True,
            "data": [
                _project_dict_with_cached_analysis_review(project.id, project)
                for project in list_projects()
            ],
        }
    if method == "POST" and path == "/api/projects":
        if "media_base64" in (body or {}):
            job = _start_project_create_job(cast(dict[str, object], body or {}))
            return {"ok": True, "data": job}
        project_id = (body or {}).get("id", "")
        if not isinstance(project_id, str):
            raise ValueError("Project id must be a string")
        return {"ok": True, "data": create_project(project_id).to_dict()}
    if method == "GET" and path == "/api/projects/create/status":
        job_values = query.get("job_id")
        job_id = job_values[0] if job_values else None
        if not job_id:
            raise ValueError("Missing job_id")
        return {"ok": True, "data": _job_payload(job_id)}

    parts = [part for part in path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "api" and parts[1] == "corpus":
        if method == "GET" and len(parts) == 3 and parts[2] == "features":
            return {"ok": True, "data": corpus_usage.feature_list()}
        if method == "GET" and len(parts) == 3 and parts[2] == "query":
            feature = _first_query_value(query, "feature")
            group = _first_query_value(query, "group")
            platform = _first_query_value(query, "platform")
            q = _first_query_value(query, "q")
            source_only = _first_query_value(query, "source_only") == "1"
            limit = _parse_int_arg(query, "limit")
            offset = _parse_int_arg(query, "offset", 0) or 0
            return {
                "ok": True,
                "data": corpus_usage.query_targets(
                    feature=feature,
                    group=group,
                    platform=platform,
                    q=q,
                    source_only=source_only,
                    limit=limit,
                    offset=offset,
                    projects=[project.to_dict() for project in list_projects()],
                ),
            }
        if method == "GET" and len(parts) == 3 and parts[2] == "variants":
            target_id = _first_query_value(query, "target_id")
            if not target_id:
                raise ValueError("Missing target_id")
            return {"ok": True, "data": corpus_usage.variants_payload(target_id)}
        if method == "GET" and len(parts) == 3 and parts[2] == "disk":
            target_id = _first_query_value(query, "target_id")
            if not target_id:
                raise ValueError("Missing target_id")
            return {
                "ok": True,
                "data": corpus_usage.disk_browser_payload(
                    target_id,
                    _first_query_value(query, "path") or "",
                    projects=[project.to_dict() for project in list_projects()],
                ),
            }
        if method == "GET" and len(parts) == 3 and parts[2] == "diff":
            left_target_id = _first_query_value(query, "left_target_id")
            right_target_id = _first_query_value(query, "right_target_id")
            if not left_target_id or not right_target_id:
                raise ValueError("Missing left_target_id/right_target_id")
            return {"ok": True, "data": corpus_usage.diff_payload(left_target_id, right_target_id)}
        if method == "GET" and len(parts) == 3 and parts[2] == "xrefs":
            target_id = _first_query_value(query, "target_id")
            feature = _first_query_value(query, "feature")
            group = _first_query_value(query, "group")
            source_only = _first_query_value(query, "source_only") == "1"
            limit = _parse_int_arg(query, "limit")
            offset = _parse_int_arg(query, "offset", 0) or 0
            return {
                "ok": True,
                "data": corpus_usage.query_xrefs(
                    target_id=target_id,
                    feature=feature,
                    group=group,
                    source_only=source_only,
                    limit=limit,
                    offset=offset,
                ),
            }
        if method == "GET" and len(parts) == 3 and parts[2] == "snippet":
            xref_id = _first_query_value(query, "xref_id")
            if not xref_id:
                raise ValueError("Missing xref_id")
            before = _parse_int_arg(query, "before", 20)
            after = _parse_int_arg(query, "after", 20)
            return {
                "ok": True,
                "data": corpus_usage.snippet_payload(
                    xref_id,
                    before=20 if before is None else before,
                    after=20 if after is None else after,
                ),
            }
        if method == "POST" and len(parts) == 3 and parts[2] == "import":
            raw_target_id = (body or {}).get("target_id")
            import_target_id: str | None = raw_target_id if isinstance(raw_target_id, str) else None
            if not isinstance(import_target_id, str) or not import_target_id:
                raise ValueError("target_id is required")
            mode = (body or {}).get("mode", "target")
            if not isinstance(mode, str):
                raise ValueError("mode must be a string")
            try:
                job = _start_project_create_job(
                    corpus_usage.corpus_import_media_body(import_target_id, mode=mode)
                )
            except Exception as exc:
                job = _failed_project_create_job(str(exc))
            return {"ok": True, "data": job}
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "projects":
        project_name = parts[2]
        if method == "GET" and len(parts) == 3:
            return {"ok": True, "data": _project_payload(project_name)}
        if method == "GET" and len(parts) == 4 and parts[3] == "disk-browser":
            return {"ok": True, "data": _project_disk_browser_payload(project_name, _first_query_value(query, "path") or "")}
        if method == "POST" and len(parts) == 4 and parts[3] == "delete":
            _cancel_listing_jobs(project_name)
            _cancel_reproduction_jobs(project_name)
            _clear_project_listing_cache(project_name)
            delete_project(project_name)
            return {"ok": True, "data": None}
        if (
            method == "POST"
            and len(parts) == 5
            and parts[3] == "disk"
            and parts[4] == "import-entry"
        ):
            raw_path = (body or {}).get("path") or (body or {}).get("entry_path")
            import_path = raw_path if isinstance(raw_path, str) else ""
            if not import_path.strip():
                raise ValueError("path is required")
            imported_target = import_disk_entry_target(
                project_name,
                entry_path=import_path,
                project_root=PROJECT_ROOT,
            )
            return {
                "ok": True,
                "data": {
                    "target_id": imported_target.target_name,
                    "target_path": imported_target.target_path,
                    "entry_path": imported_target.entry_path,
                },
            }
        if method == "POST" and len(parts) == 4 and parts[3] == "open":
            return {"ok": True, "data": mark_project_opened(project_name).to_dict()}
        if method == "GET" and len(parts) == 4 and parts[3] == "session":
            return {"ok": True, "data": None}
        if (
            method == "GET"
            and len(parts) == 5
            and parts[3] == "api"
            and parts[4] == "type-catalog"
        ):
            return {"ok": True, "data": _type_catalog_payload(project_name)}
        if method == "GET" and len(parts) == 4 and parts[3] == "reproduction":
            project = get_project(project_name)
            if project.kind != "binary":
                raise ValueError(
                    f"Project {project_name} does not expose target reproduction"
                )
            if not project.ready:
                return {
                    "ok": True,
                    "data": _not_ready_reproduction_payload(project_name),
                }
            return {
                "ok": True,
                "data": _current_reproduction_payload(
                    project_name,
                    auto_start=_project_listing_generation(project_name) == "full",
                ),
            }
        if (
            method == "POST"
            and len(parts) == 5
            and parts[3] == "reproduction"
            and parts[4] == "run"
        ):
            project = get_project(project_name)
            if project.kind != "binary" or not project.ready:
                raise ValueError(
                    f"Project {project_name} is not ready for target reproduction"
                )
            return {"ok": True, "data": _start_reproduction_job(project_name, force=True)}
        if (
            method == "GET"
            and len(parts) == 5
            and parts[3] == "reproduction"
            and parts[4] == "status"
        ):
            job_values = query.get("job_id")
            job_id = job_values[0] if job_values else None
            if not job_id:
                raise ValueError("Missing job_id")
            return {"ok": True, "data": _job_payload(job_id)}
        if method == "POST" and len(parts) == 4 and parts[3] == "target-edits":
            project = get_project(project_name)
            if project.kind != "binary" or not project.ready:
                raise ValueError(
                    f"Project {project_name} is not ready for target metadata edits"
                )
            paths = resolve_project_paths(project_name, project_root=PROJECT_ROOT)
            edit = append_target_ui_edit(paths.target_dir, cast(dict[str, object], body or {}))
            _cancel_listing_jobs(project_name)
            _cancel_reproduction_jobs(project_name)
            _clear_project_listing_cache(project_name)
            mark_project_updated(paths.target_dir)
            return {"ok": True, "data": {"edit": edit}}
        if method == "POST" and len(parts) == 4 and parts[3] == "manual-actions":
            project = get_project(project_name)
            if project.kind != "binary" or not project.ready:
                raise ValueError(
                    f"Project {project_name} is not ready for manual review actions"
                )
            action_kind = (body or {}).get("kind")
            if not isinstance(action_kind, str) or not action_kind:
                raise ValueError("Manual action kind is required")
            paths = resolve_project_paths(project_name, project_root=PROJECT_ROOT)
            binary_source = resolve_target_binary_source(paths.target_dir)
            if binary_source is None:
                raise ValueError(f"Project {project_name} has no source binary")
            action_payload = {
                key: value
                for key, value in (body or {}).items()
                if key != "kind"
            }
            validate_manual_action_payload(action_payload)
            action = append_manual_action(
                paths.target_dir,
                kind=action_kind,
                payload=action_payload,
                binary_source=binary_source,
            )
            if action_kind != "resolve_review_item":
                _cancel_listing_jobs(project_name)
                _cancel_reproduction_jobs(project_name)
                _clear_project_listing_cache(project_name)
            mark_project_updated(paths.target_dir)
            return {"ok": True, "data": {"action": action}}
        if method == "GET" and len(parts) == 4 and parts[3] == "listing":
            project = get_project(project_name)
            if project.kind != "binary":
                raise ValueError(
                    f"Project {project_name} does not expose a disassembly listing"
                )
            if not project.ready:
                return {"ok": True, "data": _empty_listing_payload(None)}
            listing_artifact = _valid_c_listing_artifact(project_name)
            if listing_artifact is None:
                raise ValueError(
                    f"C listing artifact not loaded for project: {project_name}"
                )
            start = _parse_int_arg(query, "start")
            count = _parse_int_arg(query, "count")
            anchor_code_values = query.get("anchor_code")
            anchor_code = anchor_code_values[0].strip() if anchor_code_values else ""
            if anchor_code:
                payload, _ = listing_artifact.anchor_window_payload(
                    anchor_code=anchor_code,
                    count=count or 240,
                )
            elif start is not None or count is not None:
                payload, _ = listing_artifact.window_payload(start=start or 0, count=count or 240)
            else:
                addr = _parse_int_arg(query, "addr")
                before = _parse_int_arg(query, "before", 80) or 80
                after = _parse_int_arg(query, "after", 200) or 200
                payload, _ = listing_artifact.addr_window_payload(addr=addr, before=before, after=after)
            payload = cast(
                ListingWindowPayload,
                {
                    **payload,
                    "analysis_generation": _project_listing_generation(project_name),
                },
            )
            return {
                "ok": True,
                "data": _annotate_listing_payload(project_name, payload),
            }
        if (
            method == "GET"
            and len(parts) == 5
            and parts[3] == "listing"
            and parts[4] == "navigation"
        ):
            project = get_project(project_name)
            if project.kind != "binary":
                raise ValueError(
                    f"Project {project_name} does not expose a disassembly listing"
                )
            listing_artifact = _valid_c_listing_artifact(project_name)
            if listing_artifact is not None:
                navigation_payload, _ = listing_artifact.navigation_payload()
                return {
                    "ok": True,
                    "data": _overlay_listing_navigation_payload(project_name, navigation_payload, listing_artifact),
                }
            raise ValueError(
                f"C listing artifact not loaded for project: {project_name}"
            )
        if (
            method == "POST"
            and len(parts) == 5
            and parts[3] == "listing"
            and parts[4] == "open"
        ):
            project = get_project(project_name)
            if project.kind != "binary":
                raise ValueError(
                    f"Project {project_name} does not expose a disassembly listing"
                )
            if not project.ready:
                return {
                    "ok": True,
                    "data": cast(
                        AsyncJobPayload,
                        {
                            "job_id": f"cached-empty-{project_name}",
                            "job_kind": _LISTING_ARTIFACT_JOB_KIND,
                            "project_id": project_name,
                            "result_project_id": project_name,
                            "status": "ready",
                            "phase_id": "done",
                            "phase_index": _LISTING_PHASE_COUNT,
                            "phase_count": _LISTING_PHASE_COUNT,
                            "progress_mode": "determinate",
                            "progress_current": _LISTING_PHASE_COUNT,
                            "progress_total": _LISTING_PHASE_COUNT,
                            "progress_percent": 100,
                            "total_rows": 0,
                            "error": None,
                            "created_at": time.time(),
                            "finished_at": time.time(),
                        },
                    ),
                }
            return {"ok": True, "data": _start_listing_job(project_name)}
        if (
            method == "GET"
            and len(parts) == 5
            and parts[3] == "listing"
            and parts[4] == "status"
        ):
            job_values = query.get("job_id")
            job_id = job_values[0] if job_values else None
            if not job_id:
                raise ValueError("Missing job_id")
            return {"ok": True, "data": _job_payload(job_id)}
        if (
            method == "PATCH"
            and len(parts) == 10
            and parts[3] == "api"
            and parts[4] == "functions"
            and parts[7] == "inputs"
            and parts[9] == "struct"
        ):
            library = parts[5]
            function = parts[6]
            input_name = parts[8]
            struct_name = (body or {}).get("struct_name")
            if not isinstance(struct_name, str) or not struct_name:
                raise ValueError("struct_name must be a non-empty string")
            validation = _validate_api_input_struct(
                project_name, library, function, input_name, struct_name
            )
            _write_api_input_type_override(
                library=library,
                function=function,
                input_name=input_name,
                struct_name=struct_name,
            )
            return {"ok": True, "data": validation}
    raise FileNotFoundError(f"Unknown route: {path}")


def _dedupe_upload_path(uploads_dir: Path, filename: str) -> Path:
    candidate = uploads_dir / Path(filename).name
    stem = candidate.stem
    suffix = candidate.suffix
    index = 2
    while candidate.exists():
        candidate = uploads_dir / f"{stem}-{index}{suffix}"
        index += 1
    return candidate


def _create_project_from_media(
    body: dict[str, object], *, job_id: str | None = None
) -> ProjectRecord:
    def report(phase_id: str, phase_index: int, phase_count: int) -> None:
        if job_id is None:
            return
        _set_job_state(job_id, status="building")
        _set_job_phase(
            job_id, phase_id=phase_id, phase_index=phase_index, phase_count=phase_count
        )

    filename = body.get("filename")
    media_base64 = body.get("media_base64")
    if not isinstance(filename, str):
        raise ValueError("Uploaded media filename is missing")
    if not isinstance(media_base64, str):
        raise ValueError("Uploaded media payload is missing")
    uploaded_bytes = base64.b64decode(media_base64, validate=True)
    origin_payload = body.get("project_origin")
    if origin_payload is not None and not isinstance(origin_payload, dict):
        raise ValueError("project_origin must be an object")
    media_platform = "amiga-disk" if Path(filename).suffix.lower() == ".adf" else "amiga-hunk"
    if origin_payload is None:
        project_origin: dict[str, object] = {"kind": "user_upload", "filename": filename}
    else:
        project_origin = dict(cast(dict[str, object], origin_payload))
    project_origin.setdefault("filename", filename)
    project_origin.setdefault("platform", media_platform)
    project_origin.setdefault("sha256", hashlib.sha256(uploaded_bytes).hexdigest())
    project_origin.setdefault("size", len(uploaded_bytes))
    uploads_dir = PROJECT_ROOT / "bin" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    report("write_media", 1, 4)
    media_path = _dedupe_upload_path(uploads_dir, filename)
    media_path.write_bytes(uploaded_bytes)
    if media_path.suffix.lower() == ".adf":
        base_name = dedupe_project_name(
            disk_project_id(derive_disk_id_from_stem(Path(filename).stem)),
            project_root=PROJECT_ROOT,
        )
        disk_id = base_name.removeprefix("amiga_disk_")
    else:
        base_name = dedupe_project_name(
            derive_project_name(filename), project_root=PROJECT_ROOT
        )
        disk_id = None
    _log_event(
        "media_upload saved",
        filename=filename,
        path=media_path.as_posix(),
        project_id=base_name,
    )
    if media_path.suffix.lower() == ".adf":
        if job_id is not None:
            _set_job_state(job_id, project_id=base_name)
        manifest = create_disk_project(
            media_path,
            disk_id=disk_id,
            project_root=PROJECT_ROOT,
            origin=project_origin,
            progress_fn=(
                None
                if job_id is None
                else lambda phase_id, phase_index, phase_count: report(
                    phase_id, phase_index + 1, phase_count + 1
                )
            ),
        )
        _log_event("media_upload imported", project_id=base_name, kind="disk")
        return get_project(disk_project_id(manifest.disk_id), project_root=PROJECT_ROOT)
    report("inspect_executable", 2, 4)
    try:
        validate_amiga_hunk_executable_with_c_backend(media_path, project_root=PROJECT_ROOT)
    except ValueError:
        media_path.unlink(missing_ok=True)
        raise
    report("create_target", 3, 4)
    project = create_project(base_name, project_root=PROJECT_ROOT, origin=project_origin)
    if job_id is not None:
        _set_job_state(job_id, project_id=project.id)
    write_source_descriptor(
        Path(project.target_dir),
        {
            "kind": "hunk_file",
            "path": media_path.relative_to(PROJECT_ROOT).as_posix(),
        },
    )
    mark_project_updated(Path(project.target_dir))
    report("finalize", 4, 4)
    _log_event("media_upload imported", project_id=project.id, kind="executable")
    return get_project(project.id, project_root=PROJECT_ROOT)


def serve(host: str = "127.0.0.1", port: int = 8123) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    httpd = ThreadingHTTPServer((host, port), DisasmApiHandler)
    _log_event("server_start", host=host, port=port)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve canonical disassembly API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8123)
    args = parser.parse_args()
    serve(host=args.host, port=args.port)
