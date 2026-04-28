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
from amiga_reversing.disasm.listing_types import AppSlotRef, BlockRowContext, ListingRow
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

    def fake_create_project(project_id: str, project_root: Path) -> ProjectRecord:
        assert project_root == tmp_path
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "entities.jsonl").write_text("")
        (target_dir / ".project.json").write_text(json.dumps({
            "schema_version": 1,
            "created_at": "2026-03-25T00:00:00+00:00",
            "updated_at": "2026-03-25T00:00:00+00:00",
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
        lambda media_path, *, disk_id, project_root, progress_fn=None: type("Manifest", (), {"disk_id": disk_id})(),
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
    assert rows_data[0]["view_annotations"] == []
    assert rows_data[0]["structured_data"] == {
        "struct_name": "RT",
        "field_name": "RT_MATCHWORD",
        "c_type": "UWORD",
        "value_domain": "exec.resident.matchword",
        "constant_name": "RTC_MATCHWORD",
    }


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

    payload = disasm_server._listing_navigation_payload("bloodwych", rows)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])
    app_slots = groups["app-slots"]

    assert [entry["symbol"] for entry in app_slots] == ["app_DOSBase", "app_0234"]
    assert app_slots[0]["ref_count"] == 1
    assert app_slots[0]["access_counts"] == {"read": 1}
    assert app_slots[1]["ref_count"] == 2
    assert app_slots[1]["access_counts"] == {"write": 1, "address": 1}
    refs = cast(list[dict[str, object]], app_slots[1]["refs"])
    assert [(ref["row_index"], ref["access"], ref["stable_key"]) for ref in refs] == [
        (1, "write", "app-write"),
        (2, "address", "app-address"),
    ]
    assert refs[0]["summary"] == "move.l d0,app_0234(a6)"


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


def test_route_listing_keeps_view_annotations_empty_for_monam(monkeypatch: pytest.MonkeyPatch) -> None:
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
    assert rows_data[0]["view_annotations"] == []
    assert rows_data[1]["view_annotations"] == []
    assert rows_data[2]["view_annotations"] == []


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

    assert rows_data[0]["api_call"] is None
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

    assert rows_data[0]["api_call"] is None
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
        "job_kind": "listing",
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

    payload = disasm_server._start_listing_job("bloodwych", generation="full")

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
        "build_project_rows_generation_with_c_backend",
        lambda project_name, generation: build_calls.append((project_name, generation))
        or (rows, {(0, 0): {"library": "exec.library"}}),
    )

    disasm_server._build_rows_job("job-1", "bloodwych", generation="full")

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
    ) -> tuple[list[ListingRow], dict[tuple[int, int], dict[str, object]]]:
        raise UnsupportedCBackendProject("unsupported project")

    monkeypatch.setattr(disasm_server, "build_project_rows_generation_with_c_backend", fail)

    disasm_server._build_rows_job("job-1", "bloodwych", generation="full")

    assert "bloodwych" not in disasm_server._PROJECT_ROW_CACHE
    assert disasm_server._ASYNC_JOBS["job-1"]["status"] == "failed"
    assert disasm_server._ASYNC_JOBS["job-1"]["error"] == "unsupported project"


def test_build_rows_job_stops_if_job_was_cleared() -> None:
    disasm_server._ASYNC_JOBS.clear()

    assert disasm_server._set_job_state("missing", status="building") is False
    disasm_server._build_rows_job("missing", "bloodwych", generation="basic")


def test_build_rows_job_does_not_cache_after_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["job-basic"] = {
        "job_id": "job-basic",
        "job_kind": "basic_listing",
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
        "target_generation": "basic",
    }

    def canceled_build(
        project_name: str,
        generation: str,
    ) -> tuple[list[ListingRow], dict[tuple[int, int], dict[str, object]]]:
        del disasm_server._ASYNC_JOBS["job-basic"]
        return [ListingRow(row_id="stale", kind="instruction", text="nop\n")], {}

    monkeypatch.setattr(disasm_server, "build_project_rows_generation_with_c_backend", canceled_build)

    disasm_server._build_rows_job("job-basic", "bloodwych", generation="basic")

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
    ) -> tuple[list[ListingRow], dict[tuple[int, int], dict[str, object]]]:
        if generation == "basic":
            return basic_rows, {}
        return full_rows, {(0, 4): {"library": "exec.library"}}

    monkeypatch.setattr(disasm_server, "build_project_rows_generation_with_c_backend", fake_build)
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
    disasm_server._build_rows_job("job-full", "bloodwych", generation="full")

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
        "build_project_rows_generation_with_c_backend",
        lambda project_name, generation: (
            [ListingRow(row_id="r0", kind="instruction", text="rts\n", addr=0)],
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

    disasm_server._build_rows_job("job-1", "bloodwych", generation="full")

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

    payload = disasm_server._start_listing_job("bloodwych", generation="full")

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
