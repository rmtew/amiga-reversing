from __future__ import annotations

import argparse
import base64
import json
import logging
import threading
import time
import uuid
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import NotRequired, TypedDict, cast
from urllib.parse import parse_qs, urlparse

from amiga_disk import create_disk_project
from amiga_disk.models import DiskManifest
from disasm.annotations import AnnotationPatchInput, get_entity, patch_entity
from disasm.api import ListingWindowPayload, SerializedRow, listing_window_payload
from disasm.binary_source import write_source_descriptor
from disasm.emitter import emit_session_rows
from disasm.project_ids import derive_disk_id_from_stem, disk_project_id
from disasm.project_paths import PROJECT_ROOT
from disasm.projects import (
    ProjectRecord,
    build_project_session,
    create_project,
    dedupe_project_name,
    delete_project,
    derive_project_name,
    get_project,
    list_projects,
    mark_project_opened,
    mark_project_updated,
)
from disasm.types import ListingRow
from kb.live_os_kb import install_live_runtime_os_kb, load_live_os_reference_payload
from kb.os_reference import normalize_os_reference_corrections
from m68k.hunk_parser import HunkParseError, parse

WEB_ROOT = Path(__file__).resolve().parent.parent / "scripts" / "web"
LOGGER = logging.getLogger("disasm.server")


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


class ProjectPayload(TypedDict):
    project: dict[str, object]
    disk_manifest: NotRequired[dict[str, object]]


class ApiResponse(TypedDict):
    ok: bool
    data: object


class StaticResponse(TypedDict):
    content_type: str
    body: bytes
    headers: dict[str, str]


_MISSING = object()
_PROJECT_ROW_CACHE: dict[str, list[ListingRow]] = {}
_PROJECT_API_CALL_CACHE: dict[str, dict[int, dict[str, object]]] = {}
_ASYNC_JOBS: dict[str, AsyncJobPayload] = {}
_JOB_LOCK = threading.Lock()

_LISTING_PHASE_COUNT = 2
_PROJECT_CREATE_EXECUTABLE_PHASE_COUNT = 4
_PROJECT_CREATE_DISK_PHASE_COUNT = 5

_OS_CORRECTIONS_PATH = (
    Path(__file__).resolve().parent.parent / "knowledge" / "amiga_ndk_corrections.json"
)
install_live_runtime_os_kb()


def _os_corrections_payload() -> dict[str, object]:
    with open(_OS_CORRECTIONS_PATH, encoding="utf-8") as handle:
        return cast(dict[str, object], json.load(handle))


def _api_input_type_override_map() -> dict[tuple[str, str, str], dict[str, object]]:
    payload = _os_corrections_payload()
    meta = cast(dict[str, object], payload.get("_meta", {}))
    overrides = cast(list[dict[str, object]], meta.get("api_input_type_overrides", []))
    return {
        (
            cast(str, item["library"]),
            cast(str, item["function"]),
            cast(str, item["input"]),
        ): item
        for item in overrides
    }


def _api_input_source(library: str, function: str, input_name: str) -> str:
    overrides = _api_input_type_override_map()
    if (library, function, input_name) in overrides:
        return "global correction"
    return "parsed NDK"


def _api_input_override(
    library: str, function: str, input_name: str
) -> dict[str, object] | None:
    overrides = _api_input_type_override_map()
    return overrides.get((library, function, input_name))


def _project_api_call_rows(project_name: str) -> dict[int, dict[str, object]]:
    session = build_project_session(project_name)
    calls_by_addr: dict[int, dict[str, object]] = {}
    for hunk in session.hunk_sessions:
        for call in hunk.lib_calls:
            function = call.function
            library = call.library
            calls_by_addr[call.addr] = {
                "library": library,
                "function": function,
                "inputs": [
                    {
                        "name": inp.name,
                        "regs": list(inp.regs),
                        "type": cast(str | None, override.get("type"))
                        if override is not None
                        else inp.type,
                        "i_struct": cast(str | None, override.get("i_struct"))
                        if override is not None
                        else inp.i_struct,
                        "source": "global correction"
                        if override is not None
                        else "parsed NDK",
                    }
                    for inp in call.inputs
                    for override in [_api_input_override(library, function, inp.name)]
                ],
            }
    return calls_by_addr


def _annotate_api_calls(
    project_name: str, payload: ListingWindowPayload
) -> ListingWindowPayload:
    call_rows = _PROJECT_API_CALL_CACHE.get(project_name, {})
    rows: list[SerializedRow] = []
    for row in payload["rows"]:
        addr = row["addr"]
        if isinstance(addr, int) and addr in call_rows:
            rows.append(cast(SerializedRow, {**row, "api_call": call_rows[addr]}))
        else:
            rows.append(row)
    return {**payload, "rows": rows}


def _type_catalog_payload() -> list[dict[str, object]]:
    payload = load_live_os_reference_payload()
    return [
        {
            "name": name,
            "source": struct_def["source"],
            "size": struct_def["size"],
        }
        for name, struct_def in sorted(payload["structs"].items())
    ]


def _pointer_depth(type_text: str | None) -> int:
    if type_text is None:
        return 0
    return type_text.count("*")


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
    normalized = normalize_os_reference_corrections(payload)
    _OS_CORRECTIONS_PATH.write_text(
        json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    install_live_runtime_os_kb()
    _PROJECT_ROW_CACHE.clear()
    _PROJECT_API_CALL_CACHE.clear()
    with _JOB_LOCK:
        stale_job_ids = [
            job_id
            for job_id, job in _ASYNC_JOBS.items()
            if job["job_kind"] == "listing"
        ]
        for job_id in stale_job_ids:
            del _ASYNC_JOBS[job_id]


def _annotate_listing_payload(
    project_name: str, payload: ListingWindowPayload
) -> ListingWindowPayload:
    annotated_rows: list[SerializedRow] = []
    for row in payload["rows"]:
        annotated_rows.append(row)
    payload = {
        **payload,
        "rows": annotated_rows,
    }
    return _annotate_api_calls(project_name, payload)


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
) -> None:
    with _JOB_LOCK:
        job = _ASYNC_JOBS[job_id]
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


def _set_job_phase(
    job_id: str, *, phase_id: str, phase_index: int, phase_count: int
) -> None:
    progress_current, progress_total, progress_percent = _phase_progress(
        phase_index, phase_count
    )
    _set_job_state(
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


def _build_rows_job(job_id: str, project_name: str) -> None:
    phase_count = _LISTING_PHASE_COUNT
    try:
        _log_event("listing_job start", job_id=job_id, project=project_name)
        _set_job_state(job_id, status="building")
        _set_job_phase(
            job_id, phase_id="build_session", phase_index=1, phase_count=phase_count
        )
        install_live_runtime_os_kb()
        session = build_project_session(project_name)
        _log_event(
            "listing_job phase", job_id=job_id, project=project_name, phase="emit_rows"
        )
        _set_job_phase(
            job_id, phase_id="emit_rows", phase_index=2, phase_count=phase_count
        )
        rows = emit_session_rows(session)
        _PROJECT_ROW_CACHE[project_name] = rows
        _PROJECT_API_CALL_CACHE[project_name] = _project_api_call_rows(project_name)
        _log_event(
            "listing_job done",
            job_id=job_id,
            project=project_name,
            total_rows=len(rows),
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
            total_rows=len(rows),
            finished_at=time.time(),
        )
    except Exception as exc:  # pragma: no cover
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
    cached_rows = _PROJECT_ROW_CACHE.get(project_name)
    if cached_rows is not None:
        job_id = f"cached-{project_name}"
        payload: AsyncJobPayload = {
            "job_id": job_id,
            "job_kind": "listing",
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
            "total_rows": len(cached_rows),
            "error": None,
            "created_at": time.time(),
            "finished_at": time.time(),
        }
        with _JOB_LOCK:
            _ASYNC_JOBS[job_id] = payload
        return payload

    with _JOB_LOCK:
        for _existing_id, job in _ASYNC_JOBS.items():
            if (
                job["job_kind"] == "listing"
                and job["project_id"] == project_name
                and job["status"] in {"queued", "building"}
            ):
                return cast(AsyncJobPayload, dict(job))
        job_id = str(uuid.uuid4())
        _ASYNC_JOBS[job_id] = {
            "job_id": job_id,
            "job_kind": "listing",
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
        }

    worker = threading.Thread(
        target=_build_rows_job,
        args=(job_id, project_name),
        daemon=True,
    )
    worker.start()
    return _job_payload(job_id)


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


def _project_payload(project_name: str) -> ProjectPayload:
    project = get_project(project_name)
    payload: ProjectPayload = {"project": project.to_dict()}
    if project.kind == "disk":
        manifest_path = project.manifest_path
        if manifest_path is None:
            raise ValueError(f"Disk project {project_name} is missing manifest_path")
        manifest = DiskManifest.load(Path(manifest_path))
        payload["disk_manifest"] = manifest.to_dict()
    return payload


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

    def do_GET(self) -> None:
        def handler() -> tuple[bytes, str, int, dict[str, str] | None]:
            parsed = urlparse(self.path)
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
        def handler() -> tuple[bytes, str, int, dict[str, str] | None]:
            parsed = urlparse(self.path)
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
        def handler() -> tuple[bytes, str, int, dict[str, str] | None]:
            parsed = urlparse(self.path)
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
        return {"ok": True, "data": [project.to_dict() for project in list_projects()]}
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
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "projects":
        project_name = parts[2]
        if method == "GET" and len(parts) == 3:
            return {"ok": True, "data": _project_payload(project_name)}
        if method == "POST" and len(parts) == 4 and parts[3] == "delete":
            delete_project(project_name)
            return {"ok": True, "data": None}
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
            return {"ok": True, "data": _type_catalog_payload()}
        if method == "GET" and len(parts) == 4 and parts[3] == "listing":
            project = get_project(project_name)
            if project.kind != "binary":
                raise ValueError(
                    f"Project {project_name} does not expose a disassembly listing"
                )
            if not project.ready:
                return {"ok": True, "data": _empty_listing_payload(None)}
            rows = _PROJECT_ROW_CACHE.get(project_name)
            if rows is None:
                raise ValueError(
                    f"Canonical rows not loaded for project: {project_name}"
                )
            addr = _parse_int_arg(query, "addr")
            before = _parse_int_arg(query, "before", 80) or 80
            after = _parse_int_arg(query, "after", 200) or 200
            payload = listing_window_payload(rows, addr, before, after)
            return {
                "ok": True,
                "data": _annotate_listing_payload(project_name, payload),
            }
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
                            "job_kind": "listing",
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
        if method == "GET" and len(parts) == 5 and parts[3] == "entities":
            return {"ok": True, "data": get_entity(project_name, parts[4])}
        if method == "PATCH" and len(parts) == 5 and parts[3] == "entities":
            return {
                "ok": True,
                "data": patch_entity(
                    project_name,
                    parts[4],
                    cast(AnnotationPatchInput, body or {}),
                ),
            }
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
            payload = load_live_os_reference_payload()
            struct_def = payload["structs"].get(struct_name)
            if struct_def is None:
                raise ValueError(f"Unknown struct {struct_name}")
            library_def = payload["libraries"].get(library)
            function_def = (
                None if library_def is None else library_def["functions"].get(function)
            )
            if function_def is None:
                raise ValueError(f"Unknown API function {library}/{function}")
            inputs = function_def.get("inputs", [])
            match = next(
                (item for item in inputs if item.get("name") == input_name), None
            )
            if match is None:
                raise ValueError(f"Unknown API input {library}/{function}.{input_name}")
            if _pointer_depth(cast(str | None, match.get("type"))) != 1:
                raise ValueError(
                    f"API input {library}/{function}.{input_name} is not a supported single-pointer argument"
                )
            _write_api_input_type_override(
                library=library,
                function=function,
                input_name=input_name,
                struct_name=struct_name,
            )
            return {
                "ok": True,
                "data": {
                    "library": library,
                    "function": function,
                    "input": input_name,
                    "type": f"struct {struct_name} *",
                    "i_struct": struct_name,
                    "source": "global correction",
                    "struct_source": struct_def["source"],
                },
            }
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
    report("parse_executable", 2, 4)
    try:
        hunk_file = parse(uploaded_bytes)
    except HunkParseError as exc:
        media_path.unlink(missing_ok=True)
        raise ValueError(f"Uploaded media is not an Amiga executable: {exc}") from exc
    if not hunk_file.is_executable:
        media_path.unlink(missing_ok=True)
        raise ValueError("Uploaded media is not an Amiga executable")
    report("create_target", 3, 4)
    project = create_project(base_name, project_root=PROJECT_ROOT)
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
