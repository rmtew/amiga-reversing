from __future__ import annotations

import argparse
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import NotRequired, TypedDict, cast
from urllib.parse import parse_qs, urlparse

from disasm.annotations import AnnotationPatchInput, get_entity, patch_entity
from disasm.api import listing_window_payload
from disasm.emitter import emit_session_rows
from disasm.projects import (
    ProjectRecord,
    build_project_session,
    create_project,
    get_project,
    list_projects,
    mark_project_opened,
)
from disasm.types import ListingRow

WEB_ROOT = Path(__file__).resolve().parent.parent / "scripts" / "web"


class EmptyListingPayload(TypedDict):
    anchor_addr: int | None
    start: int
    end: int
    has_more_before: bool
    has_more_after: bool
    total_rows: int
    rows: list[object]


class ListingJobPayload(TypedDict):
    job_id: str | None
    project_id: str
    status: str
    phase: str
    total_rows: int | None
    error: str | None
    created_at: NotRequired[float]
    finished_at: NotRequired[float]


class ProjectPayload(TypedDict):
    project: ProjectRecord


class ApiResponse(TypedDict):
    ok: bool
    data: object


_MISSING = object()
_PROJECT_ROW_CACHE: dict[str, list[ListingRow]] = {}
_LISTING_JOBS: dict[str, ListingJobPayload] = {}
_JOB_LOCK = threading.Lock()


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _parse_int_arg(values: dict[str, list[str]], key: str,
                   default: int | None = None) -> int | None:
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


def _job_payload(job_id: str) -> ListingJobPayload:
    with _JOB_LOCK:
        job = dict(_LISTING_JOBS[job_id])
    return cast(ListingJobPayload, job)


def _set_job_state(
    job_id: str,
    *,
    status: str | object = _MISSING,
    phase: str | object = _MISSING,
    total_rows: int | None | object = _MISSING,
    error: str | None | object = _MISSING,
    finished_at: float | object = _MISSING,
) -> None:
    with _JOB_LOCK:
        job = _LISTING_JOBS[job_id]
        if status is not _MISSING:
            assert isinstance(status, str)
            job["status"] = status
        if phase is not _MISSING:
            assert isinstance(phase, str)
            job["phase"] = phase
        if total_rows is not _MISSING:
            assert total_rows is None or isinstance(total_rows, int)
            job["total_rows"] = total_rows
        if error is not _MISSING:
            assert error is None or isinstance(error, str)
            job["error"] = error
        if finished_at is not _MISSING:
            assert isinstance(finished_at, float)
            job["finished_at"] = finished_at


def _build_rows_job(job_id: str, project_name: str) -> None:
    try:
        _set_job_state(job_id, status="building", phase="session")
        session = build_project_session(project_name)
        _set_job_state(job_id, phase="rows")
        rows = emit_session_rows(session)
        _PROJECT_ROW_CACHE[project_name] = rows
        _set_job_state(
            job_id,
            status="ready",
            phase="done",
            total_rows=len(rows),
            finished_at=time.time(),
        )
    except Exception as exc:  # pragma: no cover
        _set_job_state(
            job_id,
            status="failed",
            phase="error",
            error=str(exc),
            finished_at=time.time(),
        )


def _start_listing_job(project_name: str) -> ListingJobPayload:
    cached_rows = _PROJECT_ROW_CACHE.get(project_name)
    if cached_rows is not None:
        job_id = f"cached-{project_name}"
        payload: ListingJobPayload = {
            "job_id": job_id,
            "project_id": project_name,
            "status": "ready",
            "phase": "done",
            "total_rows": len(cached_rows),
            "error": None,
        }
        with _JOB_LOCK:
            _LISTING_JOBS[job_id] = payload
        return payload

    with _JOB_LOCK:
        for existing_id, job in _LISTING_JOBS.items():
            if job["project_id"] == project_name and job["status"] in {"queued", "building", "ready"}:
                return cast(ListingJobPayload, dict(job))
        job_id = str(uuid.uuid4())
        _LISTING_JOBS[job_id] = {
            "job_id": job_id,
            "project_id": project_name,
            "status": "queued",
            "phase": "queued",
            "total_rows": None,
            "error": None,
            "created_at": time.time(),
        }

    worker = threading.Thread(
        target=_build_rows_job,
        args=(job_id, project_name),
        daemon=True,
    )
    worker.start()
    return _job_payload(job_id)


def _project_payload(project_name: str) -> ProjectPayload:
    project = get_project(project_name)
    return {"project": project}


def resolve_static_response(path: str) -> tuple[str, bytes]:
    relative = "index.html" if path in ("", "/") else path.lstrip("/")
    if relative and "." not in Path(relative).name:
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
    return content_type, file_path.read_bytes()


class DisasmApiHandler(BaseHTTPRequestHandler):
    server_version = "DisasmApi/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/" or not parsed.path.startswith("/api/"):
                content_type, body = resolve_static_response(parsed.path)
                self.send_response(200)
            else:
                payload = route_request("GET", parsed.path, parse_qs(parsed.query))
                body = _json_bytes(payload)
                content_type = "application/json; charset=utf-8"
                self.send_response(200)
        except FileNotFoundError as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            self.send_response(404)
        except ValueError as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            self.send_response(400)
        except Exception as exc:  # pragma: no cover
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            self.send_response(500)

        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            assert isinstance(payload, dict), "PATCH body must be a JSON object"
            body = _json_bytes(route_request(
                "PATCH", parsed.path, parse_qs(parsed.query), cast(dict[str, object], payload)))
            content_type = "application/json; charset=utf-8"
            self.send_response(200)
        except FileNotFoundError as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            self.send_response(404)
        except ValueError as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            self.send_response(400)
        except Exception as exc:  # pragma: no cover
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            self.send_response(500)

        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            assert isinstance(payload, dict), "POST body must be a JSON object"
            body = _json_bytes(route_request(
                "POST", parsed.path, parse_qs(parsed.query), cast(dict[str, object], payload)))
            content_type = "application/json; charset=utf-8"
            self.send_response(200)
        except FileNotFoundError as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            self.send_response(404)
        except (FileExistsError, ValueError) as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            self.send_response(400)
        except Exception as exc:  # pragma: no cover
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            self.send_response(500)

        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def route_request(method: str, path: str, query: dict[str, list[str]],
                  body: dict[str, object] | None = None) -> ApiResponse:
    if method == "GET" and path == "/api/projects":
        return {"ok": True, "data": list_projects()}
    if method == "POST" and path == "/api/projects":
        project_id = (body or {}).get("id", "")
        if not isinstance(project_id, str):
            raise ValueError("Project id must be a string")
        return {"ok": True, "data": create_project(project_id)}

    parts = [part for part in path.split("/") if part]
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "projects":
        project_name = parts[2]
        if method == "GET" and len(parts) == 3:
            return {"ok": True, "data": _project_payload(project_name)}
        if method == "POST" and len(parts) == 4 and parts[3] == "open":
            return {"ok": True, "data": mark_project_opened(project_name)}
        if method == "GET" and len(parts) == 4 and parts[3] == "session":
            return {"ok": True, "data": None}
        if method == "GET" and len(parts) == 4 and parts[3] == "listing":
            project = get_project(project_name)
            if not project.get("ready"):
                return {"ok": True, "data": _empty_listing_payload(None)}
            rows = _PROJECT_ROW_CACHE.get(project_name)
            if rows is None:
                raise ValueError(f"Canonical rows not loaded for project: {project_name}")
            addr = _parse_int_arg(query, "addr")
            before = _parse_int_arg(query, "before", 80) or 80
            after = _parse_int_arg(query, "after", 200) or 200
            return {"ok": True, "data": listing_window_payload(rows, addr, before, after)}
        if method == "POST" and len(parts) == 5 and parts[3] == "listing" and parts[4] == "open":
            project = get_project(project_name)
            if not project.get("ready"):
                return {"ok": True, "data": cast(ListingJobPayload, {
                    "job_id": None,
                    "project_id": project_name,
                    "status": "ready",
                    "phase": "done",
                    "total_rows": 0,
                    "error": None,
                })}
            return {"ok": True, "data": _start_listing_job(project_name)}
        if method == "GET" and len(parts) == 5 and parts[3] == "listing" and parts[4] == "status":
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

    raise FileNotFoundError(f"Unknown route: {path}")


def serve(host: str = "127.0.0.1", port: int = 8123) -> None:
    httpd = ThreadingHTTPServer((host, port), DisasmApiHandler)
    print(f"Serving disassembly API on http://{host}:{port}")
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
