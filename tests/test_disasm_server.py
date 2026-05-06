from __future__ import annotations

import json
import queue
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from amiga_reversing.disasm import server as disasm_server
from amiga_reversing.disasm.c_backend import UnsupportedCBackendProject
from amiga_reversing.disasm.listing_types import (
    AppSlotRef,
    BlockRowContext,
    ListingRow,
    PlatformTypedAccess,
    PlatformUnresolvedTypedAccess,
    SemanticOperand,
    SymbolOperandMetadata,
)
from amiga_reversing.disasm.projects import ProjectRecord


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _read_http_bytes(url: str) -> tuple[bytes, str]:
    with urllib.request.urlopen(url, timeout=2) as response:
        return response.read(), response.headers.get("Content-Type", "")


def _binary_project(project_name: str, *, ready: bool) -> ProjectRecord:
    return ProjectRecord(
        id=project_name,
        name=project_name,
        kind="binary",
        target_dir=f"targets/{project_name}",
        entities_path=f"targets/{project_name}/entities.jsonl",
        output_path=None,
        binary_path="bin/BLOODWYCH" if ready else None,
        ready=ready,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=None,
        disk_type=None,
        parent_project_id=None,
        target_type="program",
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )


def test_listing_anchor_code_start_matches_non_address_row() -> None:
    rows = [
        ListingRow(row_id="include", kind="directive", text='INCLUDE "exec/io.i"\n'),
        ListingRow(row_id="section", kind="directive", text="    SECTION section,code\n"),
        ListingRow(
            row_id="code",
            kind="instruction",
            text="bra.b h0_0036\n",
            addr=0,
            opcode_or_directive="bra.b",
            operand_text="h0_0036",
        ),
    ]

    assert disasm_server._listing_anchor_code_start(rows, "SECTION section,code") == 1


def test_route_listing_anchor_code_returns_window_at_non_address_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(row_id="include", kind="directive", text='INCLUDE "exec/io.i"\n'),
        ListingRow(row_id="section", kind="directive", text="    SECTION section,code\n"),
        ListingRow(
            row_id="code",
            kind="instruction",
            text="bra.b h0_0036\n",
            addr=0,
            opcode_or_directive="bra.b",
            operand_text="h0_0036",
        ),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"anchor_code": ["SECTION section,code"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    window_rows = cast(list[dict[str, object]], data["rows"])

    assert data["start"] == 1
    assert window_rows[0]["text"].strip() == "SECTION section,code"


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


def test_route_projects_returns_project_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [_binary_project("bloodwych", ready=True)])

    payload = disasm_server.route_request("GET", "/api/projects", {})

    assert payload["ok"] is True
    assert payload["data"] == [_binary_project("bloodwych", ready=True).to_dict()]


def test_installed_disasm_server_serves_web_static_assets() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    port = _free_tcp_port()
    process = subprocess.Popen(
        [
            "uv",
            "run",
            "amiga-disasm-server",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 8
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=1)
                raise AssertionError(f"server exited early\nstdout:\n{stdout}\nstderr:\n{stderr}")
            try:
                body, content_type = _read_http_bytes(f"{base_url}/")
                break
            except Exception as exc:
                last_error = exc
                time.sleep(0.1)
        else:
            raise AssertionError(f"server did not serve /: {last_error}")

        assert b"<html" in body.lower()
        assert content_type.startswith("text/html")

        app_js, app_content_type = _read_http_bytes(f"{base_url}/app.js")
        styles_css, styles_content_type = _read_http_bytes(f"{base_url}/styles.css")

        assert b"function" in app_js
        assert app_content_type.startswith("application/javascript")
        assert b"body {" in styles_css
        assert styles_content_type.startswith("text/css")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def test_route_create_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "create_project",
        lambda project_id: _binary_project(project_id, ready=False),
    )

    payload = disasm_server.route_request("POST", "/api/projects", {}, {"id": "demo"})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["id"] == "demo"


def test_route_project_returns_project_and_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych", {})
    data = cast(dict[str, object], payload["data"])
    project = cast(dict[str, object], data["project"])

    assert payload["ok"] is True
    assert project["name"] == "bloodwych"
    assert "session" not in data
    assert "disk_manifest" not in data


def test_route_reproduction_read_run_and_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "load_reproduction_report",
        lambda project_name, project_root=None: {"target": project_name, "status": "exact"},
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_reproduction_job",
        lambda project_name, force=True: cast(
            disasm_server.AsyncJobPayload,
            {
                "job_id": "repro-1",
                "job_kind": "reproduction",
                "project_id": project_name,
                "result_project_id": project_name,
                "status": "queued",
                "phase_id": "queued",
                "phase_index": 0,
                "phase_count": 4,
                "progress_mode": "determinate",
                "progress_current": 0,
                "progress_total": 4,
                "progress_percent": 0,
                "total_rows": None,
                "error": None,
                "created_at": 1.0,
                "finished_at": None,
            },
        ),
    )
    disasm_server._ASYNC_JOBS["repro-1"] = cast(
        disasm_server.AsyncJobPayload,
        {
            "job_id": "repro-1",
            "job_kind": "reproduction",
            "project_id": "bloodwych",
            "result_project_id": "bloodwych",
            "status": "ready",
            "phase_id": "done",
            "phase_index": 4,
            "phase_count": 4,
            "progress_mode": "determinate",
            "progress_current": 4,
            "progress_total": 4,
            "progress_percent": 100,
            "total_rows": None,
            "error": None,
            "created_at": 1.0,
            "finished_at": 2.0,
        },
    )

    read_payload = disasm_server.route_request("GET", "/api/projects/bloodwych/reproduction", {})
    run_payload = disasm_server.route_request("POST", "/api/projects/bloodwych/reproduction/run", {})
    status_payload = disasm_server.route_request(
        "GET", "/api/projects/bloodwych/reproduction/status", {"job_id": ["repro-1"]}
    )

    assert cast(dict[str, object], read_payload["data"])["status"] == "exact"
    assert cast(dict[str, object], run_payload["data"])["job_kind"] == "reproduction"
    assert cast(dict[str, object], status_payload["data"])["status"] == "ready"
    disasm_server._ASYNC_JOBS.clear()


def test_route_reproduction_stale_full_listing_exposes_background_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started: list[tuple[str, bool]] = []
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = [
        ListingRow(row_id="r0", kind="instruction", text="rts\n", addr=0)
    ]
    disasm_server._PROJECT_ROW_GENERATION_CACHE["bloodwych"] = "full"
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(disasm_server, "_reproduction_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(
        disasm_server,
        "load_reproduction_report",
        lambda project_name, project_root=None: {
            "target": project_name,
            "status": "exact",
            "stale": True,
            "issues": [],
        },
    )

    def start_reproduction(project_name: str, force: bool = True) -> disasm_server.AsyncJobPayload:
        started.append((project_name, force))
        return cast(
            disasm_server.AsyncJobPayload,
            {
                "job_id": "repro-bg",
                "job_kind": "reproduction",
                "project_id": project_name,
                "result_project_id": project_name,
                "status": "queued",
                "phase_id": "queued",
                "phase_index": 0,
                "phase_count": 4,
                "progress_mode": "determinate",
                "progress_current": 0,
                "progress_total": 4,
                "progress_percent": 0,
                "total_rows": None,
                "error": None,
                "created_at": 1.0,
                "finished_at": None,
                "cache_key": "cache",
            },
        )

    monkeypatch.setattr(disasm_server, "_start_reproduction_job", start_reproduction)

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/reproduction", {})
    data = cast(dict[str, object], payload["data"])
    active_job = cast(dict[str, object], data["active_job"])

    assert started == [("bloodwych", False)]
    assert data["stale"] is True
    assert data["refreshing"] is True
    assert active_job["job_id"] == "repro-bg"
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()


def test_route_project_returns_disk_manifest_for_disk_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_disk_manifest_payload()))

    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: ProjectRecord(
            id=project_name,
            name="demo_disk",
            kind="disk",
            target_dir=str(tmp_path),
            entities_path=None,
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path=str(manifest_path),
            target_count=0,
            source_path="bin/demo.adf",
            disk_type="DOS",
            parent_project_id=None,
            target_type=None,
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T01:00:00+00:00",
        ),
    )

    payload = disasm_server.route_request("GET", "/api/projects/amiga_disk_demo_disk", {})

    data = cast(dict[str, object], payload["data"])
    project = cast(dict[str, object], data["project"])
    disk_manifest = cast(dict[str, object], data["disk_manifest"])

    assert payload["ok"] is True
    assert project["kind"] == "disk"
    assert disk_manifest["disk_id"] == "demo_disk"


def test_route_project_disk_browser_uses_common_disk_introspection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    extracted = tmp_path / "extracted" / "s" / "startup-sequence"
    extracted.parent.mkdir(parents=True)
    extracted.write_bytes(b"Echo")
    payload = _disk_manifest_payload()
    analysis = cast(dict[str, object], payload["analysis"])
    analysis["directories"] = [
        {
            "block_num": 42,
            "name": "s",
            "full_path": "s",
            "protection": "----rwed",
            "comment": None,
            "date": "2026-01-01T00:00:00",
            "hash_chain": 0,
            "parent": 880,
            "checksum_valid": True,
        }
    ]
    analysis["files"] = [
        {
            "block_num": 43,
            "name": "startup-sequence",
            "full_path": "s/startup-sequence",
            "size": 4,
            "protection": "----rwed",
            "comment": None,
            "date": "2026-01-01T00:00:00",
            "hash_chain": 0,
            "parent": 42,
            "extension_blocks": [],
            "data_blocks": [44],
            "data_block_count": 1,
            "checksum_valid": True,
            "extracted_path": str(extracted),
            "content": {"kind": "text", "size": 4, "sha256": "text-sha"},
        }
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(payload))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: ProjectRecord(
            id=project_name,
            name="demo_disk",
            kind="disk",
            target_dir=str(tmp_path),
            entities_path=None,
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path=str(manifest_path),
            target_count=0,
            source_path="bin/demo.adf",
            disk_type="DOS",
            parent_project_id=None,
            target_type=None,
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T01:00:00+00:00",
        ),
    )

    root = disasm_server.route_request("GET", "/api/projects/amiga_disk_demo_disk/disk-browser", {})
    child = disasm_server.route_request(
        "GET",
        "/api/projects/amiga_disk_demo_disk/disk-browser",
        {"path": ["s"]},
    )
    file_payload = disasm_server.route_request(
        "GET",
        "/api/projects/amiga_disk_demo_disk/disk-browser",
        {"path": ["s/startup-sequence"]},
    )

    root_entries = cast(list[dict[str, object]], cast(dict[str, object], root["data"])["entries"])
    child_data = cast(dict[str, object], child["data"])
    child_entries = cast(list[dict[str, object]], child_data["entries"])
    assert [entry["name"] for entry in root_entries] == ["s"]
    assert root_entries[0]["type"] == "directory"
    assert child_data["parent_path"] == ""
    assert child_entries[0]["name"] == "startup-sequence"
    assert child_entries[0]["size"] == 4
    assert child_entries[0]["type"] == "text"
    selected = cast(dict[str, object], cast(dict[str, object], file_payload["data"])["selected_entry"])
    content = cast(dict[str, object], selected["content"])
    assert content["text"] == "Echo"
    assert content["bytes"] == "45 63 68 6F"


def test_route_listing_rejects_disk_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_disk_manifest_payload()))
    disk_project = ProjectRecord(
        id="amiga_disk_demo_disk",
        name="demo_disk",
        kind="disk",
        target_dir=str(tmp_path),
        entities_path=None,
        output_path=None,
        binary_path=None,
        ready=False,
        last_opened=None,
        manifest_path=str(manifest_path),
        target_count=0,
        source_path="bin/demo.adf",
        disk_type="DOS",
        parent_project_id=None,
        target_type=None,
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: disk_project)

    with pytest.raises(ValueError, match="does not expose a disassembly listing"):
        disasm_server.route_request("GET", "/api/projects/amiga_disk_demo_disk/listing", {})


def test_route_listing_open_rejects_disk_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_disk_manifest_payload()))
    disk_project = ProjectRecord(
        id="amiga_disk_demo_disk",
        name="demo_disk",
        kind="disk",
        target_dir=str(tmp_path),
        entities_path=None,
        output_path=None,
        binary_path=None,
        ready=False,
        last_opened=None,
        manifest_path=str(manifest_path),
        target_count=0,
        source_path="bin/demo.adf",
        disk_type="DOS",
        parent_project_id=None,
        target_type=None,
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: disk_project)

    with pytest.raises(ValueError, match="does not expose a disassembly listing"):
        disasm_server.route_request("POST", "/api/projects/amiga_disk_demo_disk/listing/open", {}, {})


def test_route_create_project_from_adf_media(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_start_project_create_job",
        lambda body: {"job_id": "job-adf", "job_kind": "project_create", "status": "queued"},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects",
        {},
        {"filename": "demo.adf", "media_base64": "ZGVtbw=="},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-adf"
    assert data["job_kind"] == "project_create"


def test_route_create_project_from_executable_media(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_start_project_create_job",
        lambda body: {"job_id": "job-exe", "job_kind": "project_create", "status": "queued"},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects",
        {},
        {"filename": "bloodwych", "media_base64": "ZGVtbw=="},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-exe"
    assert data["job_kind"] == "project_create"


def test_route_corpus_features_query_xrefs_and_snippet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [])
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "feature_list",
        lambda: [{"feature": "hardware:custom", "target_count": 1, "occurrence_count": 2, "source_example_count": 1}],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "query_targets",
        lambda *, feature=None, group=None, platform=None, q=None, source_only=False, limit=None, offset=0, projects=None: [
            {
                "id": "platform_file_manifest:amiga-hunk/demo",
                "platform": platform,
                "count": 2,
                "source_example_count": 1,
                "feature": feature,
                "group": group,
                "q": q,
                "source_only": source_only,
                "limit": limit,
                "offset": offset,
            }
        ],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "query_xrefs",
        lambda *, target_id=None, feature=None, group=None, source_only=False, limit=None, offset=0: [
            {"id": "xref-1", "target_id": target_id, "feature": feature, "group": group, "row_index": 4, "limit": limit, "offset": offset}
        ],
    )
    snippet_args: list[tuple[str, int, int]] = []

    def fake_snippet_payload(xref_id: str, before: int = 20, after: int = 20) -> dict[str, object]:
        snippet_args.append((xref_id, before, after))
        return {
            "xref": {"id": xref_id},
            "start": 3,
            "end": 6,
            "highlighted_row_index": 4,
            "rows": [{"row_index": 4, "row_id": "r4", "text": "move.w _custom+intena,d0\n"}],
        }

    monkeypatch.setattr(disasm_server.corpus_usage, "snippet_payload", fake_snippet_payload)

    features = disasm_server.route_request("GET", "/api/corpus/features", {})
    query = disasm_server.route_request(
        "GET",
        "/api/corpus/query",
        {"feature": ["hardware:custom"], "group": ["hardware"], "platform": ["amiga-hunk"], "q": ["intena"], "source_only": ["1"], "limit": ["41"], "offset": ["40"]},
    )
    xrefs = disasm_server.route_request(
        "GET",
        "/api/corpus/xrefs",
        {"target_id": ["platform_file_manifest:amiga-hunk/demo"], "feature": ["hardware:custom"], "group": ["hardware"], "source_only": ["1"], "limit": ["121"], "offset": ["120"]},
    )
    snippet = disasm_server.route_request(
        "GET",
        "/api/corpus/snippet",
        {"xref_id": ["xref-1"], "before": ["0"], "after": ["0"]},
    )

    assert cast(list[dict[str, object]], features["data"])[0]["feature"] == "hardware:custom"
    assert cast(list[dict[str, object]], features["data"])[0]["source_example_count"] == 1
    assert cast(list[dict[str, object]], query["data"])[0]["platform"] == "amiga-hunk"
    assert cast(list[dict[str, object]], query["data"])[0]["source_example_count"] == 1
    assert cast(list[dict[str, object]], query["data"])[0]["group"] == "hardware"
    assert cast(list[dict[str, object]], query["data"])[0]["source_only"] is True
    assert cast(list[dict[str, object]], query["data"])[0]["limit"] == 41
    assert cast(list[dict[str, object]], query["data"])[0]["offset"] == 40
    assert cast(list[dict[str, object]], xrefs["data"])[0]["row_index"] == 4
    assert cast(list[dict[str, object]], xrefs["data"])[0]["limit"] == 121
    assert cast(list[dict[str, object]], xrefs["data"])[0]["offset"] == 120
    assert cast(dict[str, object], snippet["data"])["highlighted_row_index"] == 4
    assert snippet_args == [("xref-1", 0, 0)]
    assert cast(list[dict[str, object]], cast(dict[str, object], snippet["data"])["rows"])[0]["row_index"] == 4


def test_corpus_snippet_payload_preserves_explicit_row_indexes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_xrefs",
        lambda: [{"id": "xref-1", "target_id": "target-1", "row_index": 10}],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_manifest",
        lambda: [{"id": "target-1", "platform": "amiga-hunk", "origin": {"display_name": "demo"}}],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_snippet_rows",
        lambda: [
            {"target_id": "target-1", "row_index": 9, "row": {"text": "before"}},
            {"target_id": "target-1", "row_index": 10, "row": {"text": "hit"}},
            {"target_id": "target-1", "row_index": 12, "row": {"text": "sparse"}},
        ],
    )

    payload = disasm_server.corpus_usage.snippet_payload("xref-1", before=1, after=2)

    rows = cast(list[dict[str, object]], payload["rows"])
    assert [row["row_index"] for row in rows] == [9, 10, 12]
    assert payload["highlighted_row_index"] == 10


def test_route_corpus_variants_and_diff(monkeypatch: pytest.MonkeyPatch) -> None:
    left = {
        "id": "left-target",
        "platform": "amiga-hunk",
        "source_id": "left-source",
        "sha256": "left-sha",
        "size": 4,
        "origin": {"display_name": "Bloodwych [b2].zip", "in_image_path": "C/BLOODWYCH"},
        "feature_counts": {"hardware:custom": 1, "data:copper_list": 1},
    }
    right = {
        "id": "right-target",
        "platform": "amiga-hunk",
        "source_id": "right-source",
        "sha256": "right-sha",
        "size": 4,
        "origin": {"display_name": "Bloodwych [cr].zip", "in_image_path": "C/BLOODWYCH"},
        "feature_counts": {"hardware:custom": 2, "runtime:copied_code": 1},
    }
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: [left, right])
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_variants",
        lambda: [
            {
                "id": "variant-1",
                "platform": "amiga-hunk",
                "title_family": "bloodwych",
                "display_path": "C/BLOODWYCH",
                "target_count": 2,
                "unique_hash_count": 2,
                "targets": [
                    {"target_id": "left-target", "sha256": "left-sha", "origin": left["origin"]},
                    {"target_id": "right-target", "sha256": "right-sha", "origin": right["origin"]},
                ],
            }
        ],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "_target_media_bytes",
        lambda target: b"abcX" if target["id"] == "left-target" else b"abcY",
    )
    snippet_rows = [
        {"target_id": "left-target", "row_index": 0, "row": {"section_index": 0, "start_offset": 0, "text": "same_label:"}},
        {"target_id": "left-target", "row_index": 1, "row": {"section_index": 0, "start_offset": 3, "end_offset": 4, "text": "moveq #1,d0"}},
        {"target_id": "right-target", "row_index": 0, "row": {"section_index": 0, "start_offset": 0, "text": "same_label:"}},
        {"target_id": "right-target", "row_index": 1, "row": {"section_index": 0, "start_offset": 3, "end_offset": 4, "text": "moveq #2,d0"}},
    ]
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_snippet_rows_for_target",
        lambda target_id: [row for row in snippet_rows if row["target_id"] == target_id],
    )

    variants = disasm_server.route_request("GET", "/api/corpus/variants", {"target_id": ["left-target"]})
    diff = disasm_server.route_request(
        "GET",
        "/api/corpus/diff",
        {"left_target_id": ["left-target"], "right_target_id": ["right-target"]},
    )

    variant_data = cast(dict[str, object], variants["data"])
    diff_data = cast(dict[str, object], diff["data"])
    byte_diff = cast(dict[str, object], diff_data["byte_diff"])
    assert cast(dict[str, object], variant_data["group"])["id"] == "variant-1"
    assert cast(dict[str, object], diff_data["variant_group"])["id"] == "variant-1"
    assert [item["selected"] for item in cast(list[dict[str, object]], variant_data["variants"])] == [True, False]
    assert byte_diff["first_diff"] == 3
    assert byte_diff["region_count"] == 1
    regions = cast(list[dict[str, object]], byte_diff["regions"])
    assert regions[0]["left_start"] == 3
    assert regions[0]["right_start"] == 3
    assert regions[0]["skipped_left"] == 3
    assert regions[0]["skipped_right"] == 3
    assert "moveq #1,d0" in [row["text"] for row in cast(list[dict[str, object]], regions[0]["left_context"])]
    assert "moveq #2,d0" in [row["text"] for row in cast(list[dict[str, object]], regions[0]["right_context"])]


def test_corpus_diff_uses_listing_byte_space_not_raw_file_offsets(monkeypatch: pytest.MonkeyPatch) -> None:
    left = {"id": "left-target", "platform": "amiga-hunk", "origin": {"display_name": "left"}, "feature_counts": {}}
    right = {"id": "right-target", "platform": "amiga-hunk", "origin": {"display_name": "right"}, "feature_counts": {}}
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: [left, right])
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_variants",
        lambda: [
            {
                "id": "variant-1",
                "platform": "amiga-hunk",
                "title_family": "demo",
                "display_path": "C/DEMO",
                "targets": [{"target_id": "left-target"}, {"target_id": "right-target"}],
            }
        ],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "_target_media_bytes",
        lambda target: (b"raw-left-header" if target["id"] == "left-target" else b"different-raw-header") + b"\xaa\xef\xbb",
    )
    snippet_rows = [
        {
            "target_id": "left-target",
            "row_index": 0,
            "row": {
                "section_index": 0,
                "start_offset": 0,
                "end_offset": 3,
                "bytes": "aaefbb",
                "text": "\tdc.b $AA,$EF,$BB\n",
            },
        },
        {
            "target_id": "right-target",
            "row_index": 0,
            "row": {
                "section_index": 0,
                "start_offset": 0,
                "end_offset": 3,
                "bytes": "aaeebb",
                "text": "\tdc.b $AA,$EE,$BB\n",
            },
        },
    ]
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_snippet_rows_for_target",
        lambda target_id: [row for row in snippet_rows if row["target_id"] == target_id],
    )

    diff = disasm_server.corpus_usage.diff_payload("left-target", "right-target")

    byte_diff = cast(dict[str, object], diff["byte_diff"])
    regions = cast(list[dict[str, object]], byte_diff["regions"])
    assert byte_diff["left_space"] == "listing"
    assert byte_diff["right_space"] == "listing"
    assert byte_diff["left_size"] == 3
    assert byte_diff["right_size"] == 3
    assert byte_diff["first_diff"] == 1
    assert regions[0]["left_start"] == 1
    assert regions[0]["right_start"] == 1
    left_context = cast(list[dict[str, object]], regions[0]["left_context"])[0]
    assert left_context["diff_start_offset"] == 0
    assert left_context["diff_end_offset"] == 3


def test_corpus_listing_diff_space_expands_dcb_directives() -> None:
    rows = [
        {
            "section_index": 0,
            "row_index": 0,
            "start_offset": 0,
            "end_offset": 4,
            "bytes": "efef",
            "opcode_or_directive": "dcb.b",
            "operand_text": "4,$EF",
            "text": "\tdcb.b 4,$EF\n",
        }
    ]

    space = disasm_server.corpus_usage._listing_diff_space(rows)

    assert space is not None
    assert space["bytes"] == b"\xef\xef\xef\xef"
    mapped_rows = cast(list[dict[str, object]], space["rows"])
    assert mapped_rows[0]["diff_start_offset"] == 0
    assert mapped_rows[0]["diff_end_offset"] == 4


def test_corpus_diff_context_includes_preceding_rows_for_nearby_semantics() -> None:
    rows = [
        {"row_index": 0, "section_index": 0, "start_offset": 0, "end_offset": 4, "bytes": "11111111", "text": "\tmoveq #1,d0\n"},
        {"row_index": 1, "section_index": 0, "start_offset": 4, "end_offset": 8, "bytes": "22222222", "text": "\tmoveq #2,d0\n"},
        {"row_index": 2, "section_index": 0, "start_offset": 8, "end_offset": 12, "bytes": "33333333", "text": "\tmoveq #3,d0\n"},
        {"row_index": 3, "section_index": 0, "start_offset": 12, "end_offset": 16, "bytes": "44444444", "text": "\tmoveq #4,d0\n"},
    ]

    context = disasm_server.corpus_usage._source_rows_for_range(rows, 14, 15, limit=4, before=2)

    assert [row["row_index"] for row in context] == [1, 2, 3]


def test_corpus_byte_diff_merges_small_equal_runs_and_reports_skips() -> None:
    left = b"A" * 80 + b"abcd" + b"=" * 8 + b"wxyz" + b"B" * 80
    right = b"A" * 80 + b"ABCD" + b"=" * 8 + b"WXYZ" + b"B" * 80

    diff = disasm_server.corpus_usage._byte_diff_summary(left, right, merge_equal_gap=16)

    regions = cast(list[dict[str, object]], diff["regions"])
    assert diff["region_count"] == 1
    assert regions[0]["left_start"] == 80
    assert regions[0]["right_start"] == 80
    assert regions[0]["left_length"] == 16
    assert regions[0]["right_length"] == 16
    assert regions[0]["skipped_left"] == 80
    assert regions[0]["skipped_right"] == 80
    assert diff["trailing_skipped_left"] == 80
    assert diff["trailing_skipped_right"] == 80


def test_corpus_context_pairs_align_same_code_at_different_offsets() -> None:
    pairs = disasm_server.corpus_usage._paired_context_rows(
        [
            {"start_offset": 0x280, "end_offset": 0x284, "text": "\tmove.b ciaicr(a0),d0\n"},
            {"start_offset": 0x284, "end_offset": 0x286, "text": "\tandi.b #$7f,d0\n"},
        ],
        [
            {"start_offset": 0x25C, "end_offset": 0x260, "text": "\tmove.b ciaicr(a0),d0\n"},
            {"start_offset": 0x260, "end_offset": 0x266, "text": "\tandi.b #$7f,d0\n"},
        ],
    )

    assert len(pairs) == 2
    assert pairs[0]["same_text"] is True
    assert pairs[0]["same_offset"] is False
    assert cast(dict[str, object], pairs[0]["left"])["start_offset"] == 0x280
    assert cast(dict[str, object], pairs[0]["right"])["start_offset"] == 0x25C


def test_corpus_context_pairs_deemphasise_consistent_address_shift() -> None:
    pairs = disasm_server.corpus_usage._paired_context_rows(
        [
            {"start_offset": 0x1146, "end_offset": 0x114A, "opcode_or_directive": "bsr.w", "operand_text": "loc_0_00008576", "text": "\tbsr.w loc_0_00008576\n"},
            {"start_offset": 0x114A, "end_offset": 0x114E, "opcode_or_directive": "bsr.w", "operand_text": "loc_0_00008538", "text": "\tbsr.w loc_0_00008538\n"},
        ],
        [
            {"start_offset": 0x110A, "end_offset": 0x110E, "opcode_or_directive": "bsr.w", "operand_text": "loc_0_000084DA", "text": "\tbsr.w loc_0_000084DA\n"},
            {"start_offset": 0x110E, "end_offset": 0x1112, "opcode_or_directive": "bsr.w", "operand_text": "loc_0_0000849C", "text": "\tbsr.w loc_0_0000849C\n"},
        ],
    )

    assert [pair["diff_class"] for pair in pairs] == ["shifted_address", "shifted_address"]
    assert pairs[0]["dominant_delta"] == 0x9C
    assert "shifted address" in cast(str, pairs[0]["diff_label"])


def test_corpus_context_pairs_classify_immediate_and_addressing_mode_changes() -> None:
    pairs = disasm_server.corpus_usage._paired_context_rows(
        [
            {"start_offset": 0xACF, "end_offset": 0xAD4, "opcode_or_directive": "subi.l", "operand_text": "#60368,d0", "text": "\tsubi.l #60368,d0\n"},
            {"start_offset": 0x1A8, "end_offset": 0x1AE, "opcode_or_directive": "lea.l", "operand_text": "$00000060.l,a0", "text": "\tlea.l $00000060.l,a0\n"},
        ],
        [
            {"start_offset": 0xA92, "end_offset": 0xA98, "opcode_or_directive": "subi.l", "operand_text": "#60202,d0", "text": "\tsubi.l #60202,d0\n"},
            {"start_offset": 0x18E, "end_offset": 0x192, "opcode_or_directive": "lea.l", "operand_text": "$0060.w,a0", "text": "\tlea.l $0060.w,a0\n"},
        ],
    )

    assert pairs[0]["diff_class"] == "immediate_semantic"
    assert pairs[1]["diff_class"] == "addressing_mode"


def test_route_corpus_diff_rejects_unrelated_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_manifest",
        lambda: [
            {"id": "left-target", "platform": "amiga-hunk", "origin": {"display_name": "left"}},
            {"id": "right-target", "platform": "amiga-hunk", "origin": {"display_name": "right"}},
        ],
    )
    monkeypatch.setattr(disasm_server.corpus_usage, "read_variants", lambda: [])

    with pytest.raises(ValueError, match="not variants"):
        disasm_server.route_request(
            "GET",
            "/api/corpus/diff",
            {"left_target_id": ["left-target"], "right_target_id": ["right-target"]},
        )


def test_corpus_query_marks_existing_file_and_disk_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_rows = [
        {
            "id": "file-target",
            "platform": "amiga-hunk",
            "source_id": "file-row",
            "sha256": "file-sha",
            "size": 12,
            "feature_counts": {"hardware:custom": 1},
            "tags": ["hardware:custom"],
            "origin": {"in_image_path": "C/Run"},
        },
        {
            "id": "disk-target",
            "platform": "amiga-disk",
            "source_id": "disk-row",
            "sha256": "disk-sha",
            "size": 901120,
            "feature_counts": {"format:disk_image": 1},
            "tags": ["format:disk_image"],
            "origin": {"member_name": "Demo.adf"},
        },
    ]
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: manifest_rows)
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_xrefs",
        lambda: [{"id": "xref", "target_id": "file-target", "feature": "hardware:custom", "row_index": 3}],
    )

    def fake_read_jsonl(path: Path) -> list[dict[str, object]]:
        if path == disasm_server.corpus_usage.FILE_MANIFEST_PATH:
            return [{"id": "file-row", "disk_sha256": "disk-sha"}]
        return []

    monkeypatch.setattr(disasm_server.corpus_usage, "_read_jsonl_cached", fake_read_jsonl)

    rows = disasm_server.corpus_usage.query_targets(
        feature="hardware:custom",
        projects=[
            {"id": "project-file", "origin": {"kind": "user_upload", "platform": "amiga-hunk", "sha256": "file-sha", "size": 12}},
            {"id": "project-disk", "origin": {"kind": "user_upload", "platform": "amiga-disk", "sha256": "disk-sha", "size": 901120}},
        ],
    )

    assert len(rows) == 1
    coverage = cast(dict[str, object], rows[0]["project_coverage"])
    assert coverage["target_project_id"] == "project-file"
    assert coverage["disk_project_id"] == "project-disk"
    assert coverage["parent_disk_target_id"] == "disk-target"
    assert rows[0]["source_context"] == {
        "target_name": "C/Run",
        "disk_name": "Demo.adf",
        "disk_target_id": "disk-target",
    }


def test_corpus_disk_browser_lists_directories_first_and_file_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    disk_target = {
        "id": "disk-target",
        "platform": "amiga-disk",
        "source_id": "disk-row",
        "sha256": "disk-sha",
        "size": 901120,
        "origin": {"member_name": "Demo.adf"},
    }
    file_target = {
        "id": "file-run-target",
        "platform": "amiga-hunk",
        "source_id": "file-run-row",
        "sha256": "run-sha",
        "size": 12148,
        "origin": {"in_image_path": "run"},
    }
    disk_row = {
        "id": "disk-row",
        "platform": "amiga-disk",
        "origin": {"source_relpath": "resources/demo.adf"},
        "expect": {
            "inspect": {
                "entries": [
                    {"path": "Demo", "name": "Demo", "kind_name": "volume", "kind": 3},
                    {"path": "run", "name": "run", "kind_name": "file", "kind": 1, "byte_size": 12148, "content": {"kind": "amiga_hunk_executable", "target_type": "program", "size": 12148}},
                    {"path": "s", "name": "s", "kind_name": "directory", "kind": 2},
                    {"path": "s/startup-sequence", "name": "startup-sequence", "kind_name": "file", "kind": 1, "byte_size": 4, "extents": [{"image_offset": 0, "byte_size": 4}], "content": {"kind": "text", "size": 4}},
                ]
            }
        },
    }
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: [disk_target, file_target])
    monkeypatch.setattr(disasm_server.corpus_usage, "load_disk_image_bytes", lambda origin: b"Echo")
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [])

    def fake_read_jsonl(path: Path) -> list[dict[str, object]]:
        if path == disasm_server.corpus_usage.DISK_MANIFEST_PATH:
            return [disk_row]
        if path == disasm_server.corpus_usage.FILE_MANIFEST_PATH:
            return [{"id": "file-run-row", "disk_sha256": "disk-sha", "origin": {"in_image_path": "run"}}]
        return []

    monkeypatch.setattr(disasm_server.corpus_usage, "_read_jsonl_cached", fake_read_jsonl)

    root = disasm_server.route_request("GET", "/api/corpus/disk", {"target_id": ["disk-target"]})
    root_data = cast(dict[str, object], root["data"])
    root_entries = cast(list[dict[str, object]], root_data["entries"])
    child = disasm_server.route_request("GET", "/api/corpus/disk", {"target_id": ["file-run-target"], "path": ["s"]})
    child_data = cast(dict[str, object], child["data"])
    child_entries = cast(list[dict[str, object]], child_data["entries"])
    selected = disasm_server.corpus_usage.disk_browser_payload("disk-target", "s/startup-sequence")

    assert root_data["path"] == ""
    disk = cast(dict[str, object], root_data["disk"])
    coverage = cast(dict[str, object], disk["project_coverage"])
    modes = cast(list[dict[str, object]], coverage["import_modes"])
    assert modes == [
        {
            "mode": "disk",
            "label": "Promote disk",
            "available": True,
            "covered_project_id": None,
            "corpus_target_id": "disk-target",
        }
    ]
    assert [entry["name"] for entry in root_entries] == ["s", "run"]
    assert root_entries[0]["is_directory"] is True
    assert root_entries[1]["size"] == 12148
    assert root_entries[1]["type"] == "Amiga HUNK program"
    assert root_entries[1]["target_id"] == "file-run-target"
    assert child_data["parent_path"] == ""
    assert [entry["name"] for entry in child_entries] == ["startup-sequence"]
    assert cast(dict[str, object], selected["selected_entry"])["name"] == "startup-sequence"
    assert selected["entries"] == []
    content = cast(dict[str, object], cast(dict[str, object], selected["selected_entry"])["content"])
    assert content["text"] == "Echo"
    assert content["bytes"] == "45 63 68 6F"


def test_corpus_import_disk_mode_for_file_imports_parent_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    file_target = {
        "id": "file-target",
        "platform": "amiga-hunk",
        "source_id": "file-row",
        "origin": {"in_image_path": "C/Run"},
    }
    disk_target = {
        "id": "disk-target",
        "platform": "amiga-disk",
        "source_id": "disk-row",
        "source_manifest": "platform_disk_manifest",
        "sha256": "disk-sha",
        "size": 901120,
        "origin": {"member_name": "Demo.adf", "source_relpath": "resources/Demo.zip"},
    }
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: [file_target, disk_target])

    def fake_read_jsonl(path: Path) -> list[dict[str, object]]:
        if path == disasm_server.corpus_usage.FILE_MANIFEST_PATH:
            return [{"id": "file-row", "disk_sha256": "disk-sha"}]
        if path == disasm_server.corpus_usage.DISK_MANIFEST_PATH:
            return [{"id": "disk-row", "origin": {"member_name": "Demo.adf"}}]
        return []

    monkeypatch.setattr(disasm_server.corpus_usage, "_read_jsonl_cached", fake_read_jsonl)
    monkeypatch.setattr(disasm_server.corpus_usage, "load_disk_image_bytes", lambda origin: b"disk-bytes")

    body = disasm_server.corpus_usage.corpus_import_media_body("file-target", mode="disk")

    assert body["filename"] == "Demo.adf"
    assert body["media_base64"] == "ZGlzay1ieXRlcw=="
    origin = cast(dict[str, object], body["project_origin"])
    assert origin["kind"] == "corpus_disk"
    assert origin["corpus_target_id"] == "disk-target"
    assert origin["requested_corpus_target_id"] == "file-target"


def test_route_corpus_import_uses_project_create_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "corpus_import_media_body",
        lambda target_id, mode="target": {"filename": f"{target_id}-{mode}.hunk", "media_base64": "ZGVtbw=="},
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_project_create_job",
        lambda body: {"job_id": "job-corpus", "job_kind": "project_create", "status": "queued", "filename": body["filename"]},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/corpus/import",
        {},
        {"target_id": "demo", "mode": "disk"},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-corpus"
    assert data["filename"] == "demo-disk.hunk"


def test_route_corpus_import_failure_returns_failed_project_job(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "corpus_import_media_body",
        lambda target_id, mode="target": (_ for _ in ()).throw(ValueError("cannot reconstruct")),
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/corpus/import",
        {},
        {"target_id": "missing"},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_kind"] == "project_create"
    assert data["status"] == "failed"
    assert data["error"] == "cannot reconstruct"
    disasm_server._ASYNC_JOBS.clear()


def test_route_project_create_status_returns_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_job_payload",
        lambda job_id: {"job_id": job_id, "status": "building", "phase_id": "analyze_disk"},
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/create/status",
        {"job_id": ["job-1"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["phase_id"] == "analyze_disk"


def test_route_delete_project(monkeypatch: pytest.MonkeyPatch) -> None:
    removed_projects: list[str] = []
    monkeypatch.setattr(disasm_server, "delete_project", lambda project_id: removed_projects.append(project_id))

    payload = disasm_server.route_request("POST", "/api/projects/demo/delete", {})

    assert payload["ok"] is True
    assert removed_projects == ["demo"]


def test_create_project_from_media_creates_executable_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "amiga_hunk_bloodwych"

    def fake_create_project(
        project_id: str,
        project_root: Path,
        *,
        origin: dict[str, object] | None = None,
    ) -> ProjectRecord:
        assert project_root == tmp_path
        assert origin is not None
        assert origin["kind"] == "user_upload"
        assert origin["filename"] == "Bloodwych"
        assert origin["platform"] == "amiga-hunk"
        assert origin["size"] == 4
        assert isinstance(origin["sha256"], str)
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "entities.jsonl").write_text("")
        (target_dir / ".project.json").write_text(json.dumps({
            "schema_version": 2,
            "created_at": "2026-03-25T00:00:00+00:00",
            "updated_at": "2026-03-25T00:00:00+00:00",
            "origin": origin,
        }))
        return ProjectRecord(
            id=project_id,
            name=project_id,
            kind="binary",
            target_dir=str(target_dir),
            entities_path=str(target_dir / "entities.jsonl"),
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path=None,
            target_count=None,
            source_path=None,
            disk_type=None,
            parent_project_id=None,
            target_type="program",
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T00:00:00+00:00",
        )

    monkeypatch.setattr(disasm_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        disasm_server,
        "validate_amiga_hunk_executable_with_c_backend",
        lambda path, project_root: None,
    )
    monkeypatch.setattr(disasm_server, "create_project", fake_create_project)
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name, project_root: _binary_project(project_name, ready=True),
    )

    project = disasm_server._create_project_from_media({
        "filename": "Bloodwych",
        "media_base64": "ZGVtbw==",
    })

    assert project.id == "amiga_hunk_bloodwych"
    assert (tmp_path / "bin" / "uploads" / "Bloodwych").read_bytes() == b"demo"
    payload = json.loads((target_dir / "source_binary.json").read_text())
    assert payload == {
        "kind": "hunk_file",
        "path": "bin/uploads/Bloodwych",
    }


def test_create_project_from_media_rejects_invalid_executable_with_c_backend(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(disasm_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        disasm_server,
        "validate_amiga_hunk_executable_with_c_backend",
        lambda path, project_root: (_ for _ in ()).throw(
            ValueError("Uploaded media is not an Amiga executable")
        ),
    )

    with pytest.raises(ValueError, match="Uploaded media is not an Amiga executable"):
        disasm_server._create_project_from_media({
            "filename": "Bloodwych",
            "media_base64": "ZGVtbw==",
        })

    assert not (tmp_path / "bin" / "uploads" / "Bloodwych").exists()


def test_create_project_from_media_creates_disk_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(disasm_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        disasm_server,
        "create_disk_project",
        lambda media_path, *, disk_id, project_root, progress_fn=None, origin=None: type("Manifest", (), {"disk_id": disk_id})(),
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name, project_root: ProjectRecord(
            id=project_name,
            name="bloodwych",
            kind="disk",
            target_dir="targets/amiga_disk_bloodwych",
            entities_path=None,
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path="targets/amiga_disk_bloodwych/manifest.json",
            target_count=0,
            source_path="bin/uploads/Bloodwych.adf",
            disk_type="DOS",
            parent_project_id=None,
            target_type=None,
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T01:00:00+00:00",
        ),
    )

    project = disasm_server._create_project_from_media({
        "filename": "Bloodwych.adf",
        "media_base64": "ZGVtbw==",
    })

    assert project.id == "amiga_disk_bloodwych"
    assert (tmp_path / "bin" / "uploads" / "Bloodwych.adf").read_bytes() == b"demo"


def test_route_listing_returns_empty_payload_for_unready_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=False),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/demo/listing",
        {"addr": ["0x10"], "before": ["5"], "after": ["7"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["rows"] == []


def test_route_listing_raises_if_rows_not_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._PROJECT_ROW_CACHE.clear()
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    with pytest.raises(ValueError, match="Canonical rows not loaded"):
        disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})


def test_route_listing_returns_cached_window(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="moveq #0,d0\n",
            addr=0x10,
            structured_data={
                "struct_name": "RT",
                "field_name": "RT_MATCHWORD",
                "c_type": "UWORD",
                "value_domain": "exec.resident.matchword",
                "constant_name": "RTC_MATCHWORD",
            },
        )
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"addr": ["0x10"], "before": ["5"], "after": ["7"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert data["anchor_addr"] == 0x10
    assert rows_data[0]["row_id"] == "r0"
    assert "view_annotations" not in rows_data[0]
    assert rows_data[0]["structured_data"] == {
        "struct_name": "RT",
        "field_name": "RT_MATCHWORD",
        "c_type": "UWORD",
        "value_domain": "exec.resident.matchword",
        "constant_name": "RTC_MATCHWORD",
    }


def test_route_listing_addr_window_uses_serialized_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id=f"r{index}", kind="instruction", text=f"moveq #{index},d0\n", addr=index * 4)
        for index in range(5)
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_SERIALIZED_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setitem(
        disasm_server._PROJECT_SERIALIZED_ROW_CACHE,
        "bloodwych",
        [disasm_server.serialize_row(row) for row in rows],
    )
    monkeypatch.setitem(disasm_server._PROJECT_ROW_CACHE_KEY, "bloodwych", "cache")
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(
        disasm_server,
        "listing_window_payload",
        lambda rows, addr, before, after: pytest.fail("dataclass address window path should not be used"),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"addr": ["8"], "before": ["1"], "after": ["1"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert data["anchor_addr"] == 8
    assert data["start"] == 1
    assert data["end"] == 4
    assert [row["row_id"] for row in rows_data] == ["r1", "r2", "r3"]


def test_route_listing_returns_index_window(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id=f"r{index}", kind="instruction", text=f"moveq #{index},d0\n", addr=index * 2)
        for index in range(5)
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"start": ["2"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert data["start"] == 2
    assert data["end"] == 4
    assert data["total_rows"] == 5
    assert data["has_more_before"] is True
    assert data["has_more_after"] is True
    assert [row["row_id"] for row in rows_data] == ["r2", "r3"]


def test_route_listing_index_window_uses_serialized_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id=f"r{index}", kind="instruction", text=f"moveq #{index},d0\n", addr=index * 2)
        for index in range(5)
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_SERIALIZED_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setitem(
        disasm_server._PROJECT_SERIALIZED_ROW_CACHE,
        "bloodwych",
        [disasm_server.serialize_row(row) for row in rows],
    )
    monkeypatch.setitem(disasm_server._PROJECT_ROW_CACHE_KEY, "bloodwych", "cache")
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(
        disasm_server,
        "listing_index_window_payload",
        lambda rows, start, count: pytest.fail("dataclass window path should not be used"),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"start": ["2"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert data["start"] == 2
    assert data["end"] == 4
    assert [row["row_id"] for row in rows_data] == ["r2", "r3"]


def test_route_listing_window_clamps_past_end(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id=f"r{index}", kind="instruction", text=f"moveq #{index},d0\n", addr=index * 2)
        for index in range(5)
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"start": ["999"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert data["start"] == 3
    assert data["end"] == 5
    assert data["total_rows"] == 5
    assert [row["row_id"] for row in rows_data] == ["r3", "r4"]


def test_route_listing_navigation_uses_all_cached_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0, label="start:"),
        ListingRow(row_id="r1", kind="instruction", text="rts\n", addr=2),
        ListingRow(row_id="r2", kind="label", text="far_target:\n", addr=2000, label="far_target:"),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    disasm_server._PROJECT_ROW_GENERATION_CACHE["bloodwych"] = "basic"
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing/navigation",
        {},
    )
    data = cast(dict[str, object], payload["data"])
    groups = cast(dict[str, list[dict[str, object]]], data["groups"])

    assert payload["ok"] is True
    assert data["analysis_generation"] == "basic"
    assert data["total_rows"] == 3
    assert [entry["summary"] for entry in groups["labels"]] == ["start:", "far_target:"]
    assert groups["labels"][1]["addr"] == 2000


def test_listing_navigation_indexes_instruction_typed_accesses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    monkeypatch.setattr(disasm_server, "get_entities_by_int_addr", lambda project_name, project_root=None: {})
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="cmpi.w #36,LIB_VERSION(a0)\n",
            stable_key="typed-row",
            addr=0x30,
            typed_accesses=(
                PlatformTypedAccess(
                    operand_index=1,
                    base_register="A0",
                    displacement=20,
                    field_offset=20,
                    root_struct_name="Library",
                    owner_struct_name="Library",
                    field_name="LIB_VERSION",
                    field_expr="LIB_VERSION",
                ),
            ),
        )
    ]

    payload = disasm_server._listing_navigation_payload("bloodwych", rows)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

    assert groups["typed-data"] == [
        {
            "addr": 0x30,
            "row_index": 0,
            "summary": "Library.LIB_VERSION",
            "match_text": "cmpi.w #36,LIB_VERSION(a0)",
            "stable_key": "typed-row",
        }
    ]


def test_listing_navigation_indexes_unresolved_typed_accesses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    monkeypatch.setattr(disasm_server, "get_entities_by_int_addr", lambda project_name, project_root=None: {})
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="cmpi.w #36,$0024(a0)\n",
            stable_key="gap-row",
            addr=0x34,
            unresolved_typed_accesses=(
                PlatformUnresolvedTypedAccess(
                    operand_index=1,
                    base_register="A0",
                    displacement=36,
                    struct_size=34,
                    root_struct_name="InputEvent",
                    classification="prefix_extension",
                    container_candidate_count=1,
                    container_struct_name="DerivedEvent",
                    container_field_expr="de_Field",
                    refinement_applied=True,
                    refined_struct_name="DerivedEvent",
                    type_provenance_kind="prefix_refinement",
                    type_provenance_section=0,
                    type_provenance_offset=0x34,
                ),
            ),
        )
    ]

    payload = disasm_server._listing_navigation_payload("bloodwych", rows)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

    assert groups["typed-gaps"] == [
        {
            "addr": 0x34,
            "row_index": 0,
            "summary": "InputEvent+$0024 refines to DerivedEvent",
            "match_text": "cmpi.w #36,$0024(a0)",
            "stable_key": "gap-row",
            "root_struct_name": "InputEvent",
            "base_register": "A0",
            "operand_index": 1,
            "displacement": 36,
            "struct_size": 34,
            "classification": "prefix_extension",
            "container_candidate_count": 1,
            "container_struct_name": "DerivedEvent",
            "container_field_expr": "de_Field",
            "refinement_applied": True,
            "refined_struct_name": "DerivedEvent",
            "type_provenance_kind": "prefix_refinement",
            "type_provenance_section": 0,
            "type_provenance_offset": 0x34,
        }
    ]


def test_route_listing_navigation_indexes_label_definition_and_refs(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0, label="start"),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="bra.w target\n",
            addr=2,
            opcode_or_directive="bra.w",
            operand_text="target",
            operand_parts=(SemanticOperand(kind="symbol", text="target", metadata=SymbolOperandMetadata("target")),),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="move.l #target,d0\n",
            addr=6,
            opcode_or_directive="move.l",
            operand_text="#target,d0",
        ),
        ListingRow(
            row_id="r3",
            kind="instruction",
            text="move.l #target,d1\n",
            addr=8,
            opcode_or_directive="move.l",
            operand_text="#target,d1",
            operand_parts=(SemanticOperand(kind="symbol", text="target"),),
        ),
        ListingRow(row_id="r4", kind="label", text="target:\n", addr=10, label="target"),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing/navigation",
        {},
    )
    data = cast(dict[str, object], payload["data"])
    groups = cast(dict[str, list[dict[str, object]]], data["groups"])
    target = groups["labels"][1]
    refs = cast(list[dict[str, object]], target["refs"])

    assert target["symbol"] == "target"
    assert target["ref_count"] == 2
    assert target["access_counts"] == {"definition": 1, "reference": 1}
    assert [(ref["access"], ref["row_index"]) for ref in refs] == [("reference", 1), ("definition", 4)]


def test_route_listing_navigation_includes_entity_annotations(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="loc_0010:\n",
            addr=0x10,
            entity_addr=0x10,
        )
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "get_entities_by_int_addr",
        lambda project_name, project_root=None: {
            0x10: {
                "addr": "0x0010",
                "type": "code",
                "name": "main_entry",
                "comment": "validated entry",
                "confidence": "verified",
            }
        },
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing/navigation",
        {},
    )
    groups = cast(dict[str, list[dict[str, object]]], cast(dict[str, object], payload["data"])["groups"])

    assert [entry["summary"] for entry in groups["comments"]] == [
        "main_entry; validated entry; code; verified"
    ]


def test_listing_navigation_api_calls_use_instruction_row_and_hunk_context() -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="moveq #0,d0\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
        ListingRow(
            row_id="r1",
            kind="label",
            text="loc_0010:\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="jsr loc_0100(pc)\t; KNOWN: local helper uses IntuitionBase _LVOSetPointer\n",
            addr=0x10,
            opcode_or_directive="jsr",
            operand_text="loc_0100(pc)",
            comment_text="KNOWN: local helper uses IntuitionBase _LVOSetPointer",
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r3",
            kind="instruction",
            text="moveq.l #_LVOSetPointer,d0\n",
            addr=0x12,
            opcode_or_directive="moveq.l",
            operand_text="#_LVOSetPointer,d0",
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r4",
            kind="instruction",
            text="bsr.w loc_dispatch\n",
            addr=0x14,
            opcode_or_directive="bsr.w",
            operand_text="loc_dispatch",
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
    ]
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE["bloodwych"] = {
        (1, 0x10): {
            "library": "intuition.library",
            "function": "SetPointer",
            "note_kind": 3,
            "call_kind": 1,
            "inputs": [],
        },
        (1, 0x12): {
            "library": "intuition.library",
            "function": "SetPointer",
            "note_kind": 0,
            "call_kind": 1,
            "inputs": [],
        },
        (1, 0x14): {
            "library": "intuition.library",
            "function": "SetPointer",
            "note_kind": 1,
            "call_kind": 2,
            "inputs": [],
        },
    }

    try:
        payload = disasm_server._listing_navigation_payload("bloodwych", rows)
        groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

        assert groups["api-calls"] == [
            {
                "addr": 0x12,
                "row_index": 3,
                "summary": "SetPointer (intuition.library)",
                "match_text": "moveq.l #_LVOSetPointer,d0",
                "stable_key": None,
                "hunk_index": 1,
            }
        ]
    finally:
        disasm_server._PROJECT_API_CALL_CACHE.clear()


def test_listing_navigation_groups_app_slot_refs_by_symbol(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    monkeypatch.setattr(disasm_server, "get_entities_by_int_addr", lambda project_name, project_root=None: {})
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="move.l app_DOSBase(a6),d0\n",
            stable_key="app-read",
            addr=0x20,
            opcode_or_directive="move.l",
            operand_text="app_DOSBase(a6),d0",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_DOSBase", 0x26, "A6", 0, "read"),),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="move.l d0,app_0234(a6)\n",
            stable_key="app-write",
            addr=0x30,
            opcode_or_directive="move.l",
            operand_text="d0,app_0234(a6)",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_0234", 0x0234, "A6", 1, "write"),),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="lea.l app_0234(a6),a0\n",
            stable_key="app-address",
            addr=0x40,
            opcode_or_directive="lea.l",
            operand_text="app_0234(a6),a0",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_0234", 0x0234, "A6", 0, "address"),),
        ),
    ]

    disasm_server._PROJECT_APP_SLOT_ANALYSIS_CACHE["bloodwych"] = {
        "gap_count": 1,
        "slots": [
            {
                "symbol": "app_DOSBase",
                "base_registers": ["A6"],
                "width_counts": {"long": 1},
                "observed_size": 4,
                "observed_end": 0x2A,
                "first_row_index": 0,
                "last_row_index": 0,
                "first_addr": 0x20,
                "last_addr": 0x20,
            },
            {
                "symbol": "app_0234",
                "base_registers": ["A6"],
                "width_counts": {"long": 1},
                "observed_size": 4,
                "observed_end": 0x238,
                "first_row_index": 1,
                "last_row_index": 2,
                "first_addr": 0x30,
                "last_addr": 0x40,
            },
        ],
        "regions": [],
        "gaps": [],
        "field_gaps": [],
        "suggestions": [],
    }
    try:
        payload = disasm_server._listing_navigation_payload("bloodwych", rows)
        groups = cast(dict[str, list[dict[str, object]]], payload["groups"])
        app_slots = groups["app-slots"]
        app_slot_analysis = cast(dict[str, object], payload["app_slot_analysis"])

        assert [entry["symbol"] for entry in app_slots] == ["app_DOSBase", "app_0234"]
        assert app_slots[0]["ref_count"] == 1
        assert app_slots[0]["access_counts"] == {"read": 1}
        assert app_slots[0]["width_counts"] == {"long": 1}
        assert app_slots[0]["observed_end"] == 0x2A
        assert app_slots[1]["ref_count"] == 2
        assert app_slots[1]["access_counts"] == {"write": 1, "address": 1}
        assert app_slots[1]["width_counts"] == {"long": 1}
        assert app_slots[1]["first_row_index"] == 1
        assert app_slots[1]["last_row_index"] == 2
        assert app_slot_analysis["gap_count"] == 1
        refs = cast(list[dict[str, object]], app_slots[1]["refs"])
        assert [(ref["row_index"], ref["access"], ref["stable_key"]) for ref in refs] == [
            (1, "write", "app-write"),
            (2, "address", "app-address"),
        ]
        assert refs[0]["summary"] == "move.l d0,app_0234(a6)"
    finally:
        disasm_server._PROJECT_APP_SLOT_ANALYSIS_CACHE.clear()


def test_listing_navigation_exposes_type_flow_analysis_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    monkeypatch.setattr(disasm_server, "get_entities_by_int_addr", lambda project_name, project_root=None: {})
    disasm_server._PROJECT_TYPE_FLOW_ANALYSIS_CACHE["bloodwych"] = {
        "schema_version": 1,
        "target_id": "project_target:bloodwych",
        "pointer_chain_root_counts": {"app_slot": 2},
        "chains": [{"kind": "register_to_app_slot_reload", "count": 2}],
    }
    try:
        payload = disasm_server._listing_navigation_payload("bloodwych", [])

        assert payload["type_flow_analysis"] == {
            "schema_version": 1,
            "target_id": "project_target:bloodwych",
            "pointer_chain_root_counts": {"app_slot": 2},
            "chains": [{"kind": "register_to_app_slot_reload", "count": 2}],
        }
    finally:
        disasm_server._PROJECT_TYPE_FLOW_ANALYSIS_CACHE.clear()


def test_listing_navigation_exposes_app_slot_regions_and_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    monkeypatch.setattr(disasm_server, "get_entities_by_int_addr", lambda project_name, project_root=None: {})
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="lea.l app_input_event(a6),a1\n",
            stable_key="input-event-address",
            addr=0x10,
            opcode_or_directive="lea.l",
            operand_text="app_input_event(a6),a1",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_input_event", 0x100, "A6", 0, "address"),),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr _LVORawKeyConvert(a6)\n",
            stable_key="rawkeyconvert",
            addr=0x14,
            opcode_or_directive="jsr",
            operand_text="_LVORawKeyConvert(a6)",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="move.b app_after_event(a6),d0\n",
            stable_key="after-event",
            addr=0x18,
            opcode_or_directive="move.b",
            operand_text="app_after_event(a6),d0",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_after_event", 0x120, "A6", 0, "read"),),
        ),
    ]
    disasm_server._PROJECT_APP_SLOT_ANALYSIS_CACHE["input-demo"] = {
        "regions": [
            {
                "source": "platform_api_arg",
                "symbol": "app_input_event",
                "offset": 0x100,
                "end": 0x116,
                "size": 22,
                "confidence": "tool-inferred",
                "struct_name": "InputEvent",
                "field_refs": [{"field_path": ["ie_Code"]}],
                "evidence": [{"row_index": 1, "addr": 0x14, "hunk_index": 0}],
            }
        ],
        "gaps": [
            {
                "start": 0x116,
                "end": 0x120,
                "size": 10,
                "after": "app_slot_region_0100_InputEvent",
                "before": "app_slot_observed_app_after_event",
                "coverage": "unknown_app_slot_space",
            }
        ],
        "field_gaps": [
            {
                "start": 0x108,
                "end": 0x10A,
                "size": 2,
                "coverage": "known_struct_field",
                "field_path": ["ie_Qualifier"],
                "region_id": "app_slot_region_0100_InputEvent",
                "symbol": "app_input_event",
                "struct_name": "InputEvent",
            }
        ],
        "suggestions": [
            {
                "summary": "app_input_event at app+0x100 matches InputEvent from platform API usage",
                "action": "add_target_metadata",
                "confidence": "tool-inferred",
                "metadata": {
                    "symbol": "app_input_event",
                    "offset": 0x100,
                    "size": 22,
                    "struct_name": "InputEvent",
                    "storage_kind": "struct_instance",
                },
                "evidence": [{"row_index": 1, "addr": 0x14, "hunk_index": 0}],
            }
        ],
        "untyped_api_args": [
            {
                "symbol": "app_key_buffer",
                "displacement": 0x140,
                "function": "RawKeyConvert",
                "input_name": "buffer",
                "register": "A1",
                "type_name": "STRPTR",
                "reason": "missing_struct_metadata",
                "row_index": 1,
                "addr": 0x14,
                "hunk_index": 0,
                "stable_key": "call-row",
                "source_stable_key": "lea-row",
            }
        ],
    }

    try:
        payload = disasm_server._listing_navigation_payload("input-demo", rows)
        groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

        assert groups["app-slot-regions"] == [
            {
                "summary": "app_input_event: InputEvent $0100-$0116",
                "match_text": "app_input_event",
                "symbol": "app_input_event",
                "offset": 0x100,
                "end": 0x116,
                "size": 22,
                "source": "platform_api_arg",
                "confidence": "tool-inferred",
                "struct_name": "InputEvent",
                "field_ref_count": 1,
                "field_paths": ["InputEvent.ie_Code"],
                "row_index": 1,
                "addr": 0x14,
                "hunk_index": 0,
            }
        ]
        assert groups["app-slot-gaps"] == [
            {
                "summary": "Gap $0116-$0120 (10 bytes)",
                "match_text": "",
                "navigable": False,
                "start": 0x116,
                "end": 0x120,
                "size": 10,
                "after": "app_slot_region_0100_InputEvent",
                "before": "app_slot_observed_app_after_event",
                "coverage": "unknown_app_slot_space",
            }
        ]
        assert groups["app-slot-field-gaps"] == [
            {
                "summary": "Field gap $0108-$010A (2 bytes) InputEvent.ie_Qualifier",
                "match_text": "InputEvent.ie_Qualifier",
                "navigable": False,
                "start": 0x108,
                "end": 0x10A,
                "size": 2,
                "coverage": "known_struct_field",
                "field_path": ["ie_Qualifier"],
                "region_id": "app_slot_region_0100_InputEvent",
                "symbol": "app_input_event",
                "struct_name": "InputEvent",
            }
        ]
        suggestions = groups["app-slot-suggestions"]
        assert len(suggestions) == 1
        assert suggestions[0]["action"] == "add_target_metadata"
        assert suggestions[0]["symbol"] == "app_input_event"
        assert suggestions[0]["offset"] == 0x100
        assert suggestions[0]["struct_name"] == "InputEvent"
        assert suggestions[0]["row_index"] == 1
        assert cast(dict[str, object], suggestions[0]["metadata"])["storage_kind"] == "struct_instance"
        api_args = groups["app-slot-api-args"]
        assert len(api_args) == 1
        assert api_args[0]["summary"] == "app_key_buffer -> RawKeyConvert buffer A1 (missing_struct_metadata)"
        assert api_args[0]["symbol"] == "app_key_buffer"
        assert api_args[0]["register"] == "A1"
        assert api_args[0]["type_name"] == "STRPTR"
        assert api_args[0]["row_index"] == 1
        assert api_args[0]["stable_key"] == "call-row"
        assert api_args[0]["source_stable_key"] == "lea-row"
    finally:
        disasm_server._PROJECT_APP_SLOT_ANALYSIS_CACHE.clear()


def test_route_listing_navigation_rejects_stale_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = [
        ListingRow(row_id="r0", kind="label", text="stale:\n", addr=0, label="stale:")
    ]
    disasm_server._PROJECT_ROW_GENERATION_CACHE["bloodwych"] = "basic"
    disasm_server._PROJECT_ROW_CACHE_KEY["bloodwych"] = "old-cache"
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "_project_listing_cache_key",
        lambda project_name: "new-cache",
    )

    with pytest.raises(ValueError, match="Canonical rows not loaded"):
        disasm_server.route_request(
            "GET",
            "/api/projects/bloodwych/listing/navigation",
            {},
        )

    assert "bloodwych" not in disasm_server._PROJECT_ROW_CACHE
    assert "bloodwych" not in disasm_server._PROJECT_ROW_GENERATION_CACHE
    assert "bloodwych" not in disasm_server._PROJECT_ROW_CACHE_KEY


def test_project_listing_cache_key_includes_renderer_tool_stamps(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x4e\x75")
    source = SimpleNamespace(
        kind="hunk_file",
        display_path="demo.bin",
        path=binary_path,
    )
    stamp = {"value": "a"}
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root, require_entities=False: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    monkeypatch.setattr(disasm_server, "effective_metadata_hash", lambda target_dir: "metadata")
    monkeypatch.setattr(disasm_server, "source_renderer_tool_stamps", lambda project_root: {"renderer": stamp["value"]})

    first = disasm_server._project_listing_cache_key("demo")
    stamp["value"] = "b"
    second = disasm_server._project_listing_cache_key("demo")

    assert first != second


def test_route_listing_omits_empty_view_annotations_for_monam(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id="r0", kind="label", text="setpointer_pointer:\n", addr=0x0008),
        ListingRow(row_id="r1", kind="instruction", text="movea.l #memtask,a0\n", addr=0x0298),
        ListingRow(row_id="r2", kind="label", text="call_setpointer:\n", addr=0x8146),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["amiga_hunk_monam302"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/amiga_hunk_monam302/listing",
        {"before": ["5"], "after": ["7"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert "view_annotations" not in rows_data[0]
    assert "view_annotations" not in rows_data[1]
    assert "view_annotations" not in rows_data[2]


def test_route_listing_hydrates_entity_annotations(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="loc_0010:\n",
            addr=0x10,
            entity_addr=0x10,
        )
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "get_entities_by_int_addr",
        lambda project_name, project_root=None: {
            0x10: {
                "addr": "0x0010",
                "type": "code",
                "name": "main_entry",
                "comment": "validated entry",
                "confidence": "verified",
            }
        },
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"before": ["0"], "after": ["1"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert rows_data[0]["view_annotations"] == [
        "main_entry",
        "validated entry",
        "code",
        "verified",
    ]
    assert rows_data[0]["entity"] == {
        "addr": "0x0010",
        "type": "code",
        "name": "main_entry",
        "comment": "validated entry",
        "confidence": "verified",
    }


def test_route_listing_adds_api_call_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            addr=0x814E,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        )
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    disasm_server._PROJECT_API_CALL_CACHE["bloodwych"] = {
        (0, 0x814E): {
            "library": "intuition.library",
            "function": "SetPointer",
            "inputs": [
                {
                    "name": "pointer",
                    "regs": ["A1"],
                    "type": "UWORD *",
                    "i_struct": None,
                    "source": "parsed NDK",
                }
            ],
        }
    }
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert rows_data[0]["api_call"] == {
        "library": "intuition.library",
        "function": "SetPointer",
        "inputs": [
            {
                "name": "pointer",
                "regs": ["A1"],
                "type": "UWORD *",
                "i_struct": None,
                "source": "parsed NDK",
            }
        ],
    }


def test_route_listing_does_not_attach_api_call_metadata_to_label_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="loc_0010:\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    disasm_server._PROJECT_API_CALL_CACHE["bloodwych"] = {
        (0, 0x10): {
            "library": "intuition.library",
            "function": "SetPointer",
            "inputs": [],
        }
    }
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert "api_call" not in rows_data[0]
    assert rows_data[1]["api_call"] == {
        "library": "intuition.library",
        "function": "SetPointer",
        "inputs": [],
    }


def test_route_listing_does_not_cross_apply_api_call_metadata_between_hunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="moveq #1,d0\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr _LVOOpenLibrary(a6)\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=3),
        ),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    disasm_server._PROJECT_API_CALL_CACHE["bloodwych"] = {
        (3, 0x10): {
            "library": "exec.library",
            "function": "OpenLibrary",
            "inputs": [],
        }
    }
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert "api_call" not in rows_data[0]
    assert rows_data[1]["api_call"] == {
        "library": "exec.library",
        "function": "OpenLibrary",
        "inputs": [],
    }


def test_route_type_catalog_returns_known_structs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "type_catalog_from_c_backend",
        lambda project_name: [
            {"name": "SimpleSprite", "source": "graphics/sprite.i", "size": 12},
            {"name": "Window", "source": "intuition/intuition.i", "size": 34},
        ],
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/api/type-catalog", {})
    data = cast(list[dict[str, object]], payload["data"])

    assert payload["ok"] is True
    assert data[0]["name"] == "SimpleSprite"
    assert data[0]["source"] == "graphics/sprite.i"


def test_route_patch_api_input_struct_writes_global_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    corrections_path = tmp_path / "amiga_ndk_corrections.json"
    corrections_path.write_text(json.dumps({
        "_meta": {
            "absolute_symbols": [],
            "api_input_semantic_assertions": [],
            "api_input_type_overrides": [],
            "api_input_value_bindings": [],
            "struct_field_value_bindings": [],
            "value_domains": {},
        },
        "libraries": {},
        "structs": {},
        "constants": {},
    }))
    monkeypatch.setattr(disasm_server, "_OS_CORRECTIONS_PATH", corrections_path)
    monkeypatch.setattr(
        disasm_server,
        "validate_api_input_struct_with_c_backend",
        lambda project_name, library, function, input_name, struct_name: {
            "library": library,
            "function": function,
            "input": input_name,
            "type": f"struct {struct_name} *",
            "i_struct": struct_name,
            "source": "global correction",
            "struct_source": "graphics/sprite.i",
        },
    )

    payload = disasm_server.route_request(
        "PATCH",
        "/api/projects/bloodwych/api/functions/intuition.library/SetPointer/inputs/pointer/struct",
        {},
        {"struct_name": "SimpleSprite"},
    )
    data = cast(dict[str, object], payload["data"])
    persisted = json.loads(corrections_path.read_text())

    assert payload["ok"] is True
    assert data["type"] == "struct SimpleSprite *"
    assert data["struct_source"] == "graphics/sprite.i"
    overrides = persisted["_meta"]["api_input_type_overrides"]
    assert overrides == [{
        "citation": "User-edited via disasm UI",
        "function": "SetPointer",
        "i_struct": "SimpleSprite",
        "input": "pointer",
        "library": "intuition.library",
        "review_status": "validated",
        "seed_origin": "manual",
        "type": "struct SimpleSprite *",
    }]


def test_route_listing_open_starts_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_progressive_listing_jobs",
        lambda project_name: {
            "job_id": "job-full",
            "project_id": project_name,
            "status": "queued",
            "target_generation": "full",
        },
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/listing/open",
        {},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-full"
    assert data["target_generation"] == "full"


def test_start_listing_job_ignores_stale_ready_job_without_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeThread:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def start(self) -> None:
            pass

    monkeypatch.setattr(disasm_server.threading, "Thread", FakeThread)
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["stale-job"] = {
        "job_id": "stale-job",
        "job_kind": "full_listing",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "ready",
        "phase_id": "done",
        "phase_index": 2,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 2,
        "progress_total": 2,
        "progress_percent": 100,
        "total_rows": 10,
        "error": None,
        "created_at": 1.0,
        "finished_at": 1.0,
    }

    payload = disasm_server._start_listing_job("bloodwych")

    assert payload["job_id"] != "stale-job"
    assert payload["status"] in {"queued", "building"}


def test_build_rows_job_can_use_c_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [ListingRow(row_id="c:0", kind="instruction", text="nop\n", addr=0)]
    build_calls: list[tuple[str, str, str | None]] = []
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["job-1"] = {
        "job_id": "job-1",
        "job_kind": "full_listing",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }
    monkeypatch.setattr(
        disasm_server,
        "build_project_rows_generation_with_c_backend_profile",
        lambda project_name, generation: build_calls.append((project_name, generation))
        or (rows, {(0, 0): {"library": "exec.library"}}, {}),
    )

    disasm_server._build_rows_job("job-1", "bloodwych")

    assert disasm_server._PROJECT_ROW_CACHE["bloodwych"] == rows
    assert disasm_server._PROJECT_ROW_GENERATION_CACHE["bloodwych"] == "full"
    assert disasm_server._PROJECT_API_CALL_CACHE["bloodwych"] == {
        (0, 0): {"library": "exec.library"}
    }
    assert build_calls == [("bloodwych", "basic"), ("bloodwych", "full")]
    assert disasm_server._ASYNC_JOBS["job-1"]["status"] == "ready"


def test_build_rows_job_reports_unsupported_c_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["job-1"] = {
        "job_id": "job-1",
        "job_kind": "full_listing",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }

    def fail(
        project_name: str,
        generation: str,
    ) -> tuple[list[ListingRow], dict[tuple[int, int], dict[str, object]], dict[str, object]]:
        raise UnsupportedCBackendProject("unsupported project")

    monkeypatch.setattr(disasm_server, "build_project_rows_generation_with_c_backend_profile", fail)

    disasm_server._build_rows_job("job-1", "bloodwych")

    assert "bloodwych" not in disasm_server._PROJECT_ROW_CACHE
    assert disasm_server._ASYNC_JOBS["job-1"]["status"] == "failed"
    assert disasm_server._ASYNC_JOBS["job-1"]["error"] == "unsupported project"


def test_build_rows_job_stops_if_job_was_cleared() -> None:
    disasm_server._ASYNC_JOBS.clear()

    assert disasm_server._set_job_state("missing", status="building") is False
    disasm_server._build_rows_job("missing", "bloodwych")


def test_build_rows_job_does_not_cache_after_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["job-full"] = {
        "job_id": "job-full",
        "job_kind": "full_listing",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
        "target_generation": "full",
    }

    def canceled_build(
        project_name: str,
        generation: str,
    ) -> tuple[list[ListingRow], dict[tuple[int, int], dict[str, object]], dict[str, object]]:
        del disasm_server._ASYNC_JOBS["job-full"]
        return [ListingRow(row_id="stale", kind="instruction", text="nop\n")], {}, {}

    monkeypatch.setattr(disasm_server, "build_project_rows_generation_with_c_backend_profile", canceled_build)

    disasm_server._build_rows_job("job-full", "bloodwych")

    assert "bloodwych" not in disasm_server._PROJECT_ROW_CACHE
    assert "bloodwych" not in disasm_server._PROJECT_ROW_GENERATION_CACHE


def test_full_listing_replaces_basic_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    basic_rows = [ListingRow(row_id="basic", kind="instruction", text="nop\n", analysis_generation="basic")]
    full_rows = [
        ListingRow(
            row_id="full",
            kind="instruction",
            text="rts\n",
            analysis_generation="full",
            section_index=0,
            start_offset=4,
            end_offset=6,
            addr=4,
        )
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    subscriber: queue.Queue[dict[str, object]] = queue.Queue()
    disasm_server._JOB_EVENT_SUBSCRIBERS["job-full"] = [subscriber]

    def fake_build(
        project_name: str,
        generation: str,
    ) -> tuple[list[ListingRow], dict[tuple[int, int], dict[str, object]], dict[str, object]]:
        if generation == "basic":
            return basic_rows, {}, {}
        return full_rows, {(0, 4): {"library": "exec.library"}}, {}

    monkeypatch.setattr(disasm_server, "build_project_rows_generation_with_c_backend_profile", fake_build)
    disasm_server._ASYNC_JOBS["job-full"] = {
        "job_id": "job-full",
        "job_kind": "full_listing",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 4,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 4,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
        "target_generation": "full",
    }
    disasm_server._build_rows_job("job-full", "bloodwych")

    assert disasm_server._PROJECT_ROW_CACHE["bloodwych"] == full_rows
    assert disasm_server._PROJECT_ROW_GENERATION_CACHE["bloodwych"] == "full"
    assert disasm_server._PROJECT_API_CALL_CACHE["bloodwych"] == {
        (0, 4): {"library": "exec.library"}
    }
    events: list[dict[str, object]] = []
    while not subscriber.empty():
        events.append(subscriber.get_nowait())
    generation_events = [event for event in events if event.get("_event_type") == "listing_generation_ready"]
    assert generation_events == [
        {
            "_event_type": "listing_generation_ready",
            "project_id": "bloodwych",
            "generation": "basic",
            "total_rows": 1,
            "changed_ranges": [],
        },
        {
            "_event_type": "listing_generation_ready",
            "project_id": "bloodwych",
            "generation": "full",
            "total_rows": 1,
            "changed_ranges": [{"section_index": 0, "start_offset": 4, "end_offset": 6}],
        }
    ]


def test_route_listing_status_returns_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_job_payload",
        lambda job_id: {"job_id": job_id, "status": "building", "phase_id": "emit_rows"},
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing/status",
        {"job_id": ["job-1"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["status"] == "building"
    assert data["phase_id"] == "emit_rows"


def test_job_state_update_publishes_event() -> None:
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    subscriber: queue.Queue[disasm_server.AsyncJobPayload] = queue.Queue()
    disasm_server._ASYNC_JOBS["job-1"] = {
        "job_id": "job-1",
        "job_kind": "full_listing",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }
    disasm_server._JOB_EVENT_SUBSCRIBERS["job-1"] = [subscriber]

    assert disasm_server._set_job_state(
        "job-1",
        status="ready",
        phase_id="done",
        finished_at=2.0,
    )

    payload = subscriber.get_nowait()
    assert payload["job_id"] == "job-1"
    assert payload["status"] == "ready"
    assert payload["phase_id"] == "done"
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    disasm_server._ASYNC_JOBS.clear()


def test_cancel_listing_job_publishes_failed_event() -> None:
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    subscriber: queue.Queue[disasm_server.AsyncJobPayload] = queue.Queue()
    disasm_server._ASYNC_JOBS["job-1"] = {
        "job_id": "job-1",
        "job_kind": "full_listing",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "building",
        "phase_id": "build_c_rows",
        "phase_index": 1,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }
    disasm_server._JOB_EVENT_SUBSCRIBERS["job-1"] = [subscriber]

    disasm_server._cancel_listing_jobs("bloodwych")

    payload = subscriber.get_nowait()
    assert payload["job_id"] == "job-1"
    assert payload["status"] == "failed"
    assert payload["error"] == "job canceled"
    assert "job-1" not in disasm_server._ASYNC_JOBS
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()


def test_json_bytes_returns_valid_json() -> None:
    body = disasm_server._json_bytes({"ok": True, "data": {"x": 1}})

    assert json.loads(body.decode("utf-8")) == {"ok": True, "data": {"x": 1}}


def test_resolve_static_response_serves_index() -> None:
    response = disasm_server.resolve_static_response("/")

    assert response["content_type"] == "text/html; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"Disassembly Projects" in response["body"]


def test_resolve_static_response_serves_project_route() -> None:
    response = disasm_server.resolve_static_response("/bloodwych")

    assert response["content_type"] == "text/html; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"Disassembly Projects" in response["body"]


def test_resolve_static_response_serves_dotted_project_route() -> None:
    response = disasm_server.resolve_static_response("/amiga_disk_search-for-the-king")

    assert response["content_type"] == "text/html; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"Disassembly Projects" in response["body"]


def test_resolve_static_response_serves_app_js_with_no_store() -> None:
    response = disasm_server.resolve_static_response("/app.js")

    assert response["content_type"] == "application/javascript; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"function renderDiskTargets(manifest)" in response["body"]


def test_resolve_static_response_rejects_missing_file() -> None:
    with pytest.raises(FileNotFoundError, match="Unknown route"):
        disasm_server.resolve_static_response("/assets/missing.txt")


def test_route_get_entity_returns_annotation_view(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "get_entity",
                        lambda project_name, addr, project_root=None: {"addr": addr, "name": "main"})

    payload = disasm_server.route_request(
        "GET", "/api/projects/bloodwych/entities/0x0000", {})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["name"] == "main"


def test_route_patch_entity_updates_annotations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server, "patch_entity",
        lambda project_name, addr, body, project_root=None: {"addr": addr, "name": body["name"]},
    )

    payload = disasm_server.route_request(
        "PATCH", "/api/projects/bloodwych/entities/0x0000", {},
        {"name": "main"})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["name"] == "main"


def test_full_listing_job_queues_reproduction(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[str] = []
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(
        disasm_server,
        "build_project_rows_generation_with_c_backend_profile",
        lambda project_name, generation: (
            [ListingRow(row_id="r0", kind="instruction", text="rts\n", addr=0)],
            {},
            {},
        ),
    )
    monkeypatch.setattr(disasm_server, "_start_reproduction_job_if_needed", lambda project_name: queued.append(project_name))
    disasm_server._ASYNC_JOBS["job-1"] = cast(
        disasm_server.AsyncJobPayload,
        {
            "job_id": "job-1",
            "job_kind": "full_listing",
            "project_id": "bloodwych",
            "result_project_id": "bloodwych",
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": 2,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": 2,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": 1.0,
            "finished_at": None,
            "cache_key": "cache",
        },
    )

    disasm_server._build_rows_job("job-1", "bloodwych")

    assert queued == ["bloodwych"]
    assert disasm_server._PROJECT_ROW_GENERATION_CACHE["bloodwych"] == "full"
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()


def test_cached_full_listing_job_queues_reproduction(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[str] = []
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = [
        ListingRow(row_id="r0", kind="instruction", text="rts\n", addr=0)
    ]
    disasm_server._PROJECT_ROW_GENERATION_CACHE["bloodwych"] = "full"
    disasm_server._PROJECT_ROW_CACHE_KEY["bloodwych"] = "cache"
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(
        disasm_server,
        "_start_reproduction_job_if_needed",
        lambda project_name: queued.append(project_name),
    )

    payload = disasm_server._start_listing_job("bloodwych")

    assert payload["status"] == "ready"
    assert queued == ["bloodwych"]
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()


def test_reproduction_job_does_not_use_stale_cached_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_rows: list[list[ListingRow] | None] = []
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = [
        ListingRow(row_id="stale", kind="instruction", text="nop\n", addr=0)
    ]
    disasm_server._PROJECT_ROW_GENERATION_CACHE["bloodwych"] = "full"
    disasm_server._PROJECT_ROW_CACHE_KEY["bloodwych"] = "old-cache"
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "fresh-cache")
    monkeypatch.setattr(disasm_server, "_reproduction_cache_key", lambda project_name: "repro-cache")
    monkeypatch.setattr(
        disasm_server,
        "run_reproduction",
        lambda project_name, rows, project_root: captured_rows.append(rows) or {"status": "exact"},
    )
    disasm_server._ASYNC_JOBS["repro-job"] = cast(
        disasm_server.AsyncJobPayload,
        {
            "job_id": "repro-job",
            "job_kind": "reproduction",
            "project_id": "bloodwych",
            "result_project_id": "bloodwych",
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": 4,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": 4,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": 1.0,
            "finished_at": None,
            "cache_key": "repro-cache",
        },
    )

    disasm_server._build_reproduction_job("repro-job", "bloodwych")

    assert captured_rows == [None]
    assert "bloodwych" not in disasm_server._PROJECT_ROW_CACHE
    assert disasm_server._ASYNC_JOBS["repro-job"]["status"] == "ready"
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()


def test_metadata_edit_route_invalidates_listing_and_reproduction(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    canceled: list[str] = []
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = []
    disasm_server._PROJECT_ROW_GENERATION_CACHE["bloodwych"] = "full"
    disasm_server._PROJECT_ROW_CACHE_KEY["bloodwych"] = "cache"
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root, require_entities=False: SimpleNamespace(target_dir=target_dir),
    )
    monkeypatch.setattr(disasm_server, "append_target_ui_edit", lambda target_dir, body: {"kind": body["kind"], "addr": body["addr"]})
    monkeypatch.setattr(disasm_server, "_cancel_listing_jobs", lambda project_name: canceled.append(f"listing:{project_name}"))
    monkeypatch.setattr(disasm_server, "_cancel_reproduction_jobs", lambda project_name: canceled.append(f"repro:{project_name}"))
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/target-edits",
        {},
        {"kind": "entrypoint", "addr": 0x20},
    )

    assert cast(dict[str, object], cast(dict[str, object], payload["data"])["edit"])["kind"] == "entrypoint"
    assert "bloodwych" not in disasm_server._PROJECT_ROW_CACHE
    assert canceled == ["listing:bloodwych", "repro:bloodwych"]


def test_listing_navigation_includes_repro_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [ListingRow(row_id="r0", kind="instruction", text="rts\n", addr=0x20)]
    monkeypatch.setattr(
        disasm_server,
        "_active_reproduction_report",
        lambda project_name: {
            "issues": [
                {
                    "kind": "diff",
                    "summary": "Diff at file offset 0x20",
                    "row_index": 0,
                    "addr": 0x20,
                    "match_text": "rts",
                }
            ]
        },
    )
    monkeypatch.setattr(disasm_server, "get_entities_by_int_addr", lambda project_name, project_root=None: {})

    payload = disasm_server._listing_navigation_payload("bloodwych", rows)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

    assert groups["repro-issues"][0]["summary"] == "Diff at file offset 0x20"
