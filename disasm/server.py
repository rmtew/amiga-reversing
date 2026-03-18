from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from disasm.annotations import get_entity, patch_entity
from disasm.api import listing_window_payload, session_metadata
from disasm.project_paths import resolve_project_paths
from disasm.projects import build_project_session, list_projects
from disasm.emitter import emit_session_rows

WEB_ROOT = Path(__file__).resolve().parent.parent / "scripts" / "web"


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _parse_int_arg(values: dict[str, list[str]], key: str,
                   default: int | None = None) -> int | None:
    raw = values.get(key, [None])[0]
    if raw in (None, ""):
        return default
    return int(raw, 0)


def _project_payload(project_name: str) -> dict:
    paths = resolve_project_paths(project_name)
    session = build_project_session(project_name)
    return {
        "project": {
            "name": paths.name,
            "target_dir": str(paths.target_dir),
            "entities_path": str(paths.entities_path),
            "output_path": str(paths.output_path) if paths.output_path else None,
            "binary_path": str(paths.binary_path),
            "analysis_cache_path": str(paths.analysis_cache_path),
            "provenance": paths.provenance,
        },
        "session": session_metadata(session),
    }


def resolve_static_response(path: str) -> tuple[str, bytes]:
    relative = "index.html" if path in ("", "/") else path.lstrip("/")
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

    def do_GET(self):
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

    def do_PATCH(self):
        parsed = urlparse(self.path)
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            body = _json_bytes(route_request(
                "PATCH", parsed.path, parse_qs(parsed.query), payload))
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

    def log_message(self, format: str, *args):  # noqa: A003
        return


def route_request(method: str, path: str, query: dict[str, list[str]],
                  body: dict | None = None) -> dict:
    if method == "GET" and path == "/api/projects":
        return {"ok": True, "data": list_projects()}

    parts = [part for part in path.split("/") if part]
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "projects":
        project_name = parts[2]
        if method == "GET" and len(parts) == 3:
            return {"ok": True, "data": _project_payload(project_name)}
        if method == "GET" and len(parts) == 4 and parts[3] == "session":
            session = build_project_session(project_name)
            return {"ok": True, "data": session_metadata(session)}
        if method == "GET" and len(parts) == 4 and parts[3] == "listing":
            session = build_project_session(project_name)
            rows = emit_session_rows(session)
            addr = _parse_int_arg(query, "addr")
            before = _parse_int_arg(query, "before", 80)
            after = _parse_int_arg(query, "after", 160)
            return {
                "ok": True,
                "data": listing_window_payload(rows, addr, before=before, after=after),
            }
        if method == "GET" and len(parts) == 5 and parts[3] == "entities":
            return {"ok": True, "data": get_entity(project_name, parts[4])}
        if method == "PATCH" and len(parts) == 5 and parts[3] == "entities":
            return {"ok": True, "data": patch_entity(project_name, parts[4], body or {})}

    raise FileNotFoundError(f"Unknown route: {path}")


def serve(host: str = "127.0.0.1", port: int = 8123):
    httpd = ThreadingHTTPServer((host, port), DisasmApiHandler)
    print(f"Serving disassembly API on http://{host}:{port}")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="Serve canonical disassembly API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8123)
    args = parser.parse_args()
    serve(host=args.host, port=args.port)
