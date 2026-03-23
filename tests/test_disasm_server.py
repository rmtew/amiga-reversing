from __future__ import annotations

import json
from typing import cast

import pytest

from disasm import server as disasm_server
from disasm.types import ListingRow


def test_route_projects_returns_project_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "list_projects",
                        lambda: [{"id": "bloodwych", "name": "bloodwych"}])

    payload = disasm_server.route_request("GET", "/api/projects", {})

    assert payload["ok"] is True
    assert payload["data"] == [{"id": "bloodwych", "name": "bloodwych"}]


def test_route_create_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "create_project",
        lambda project_id: {"id": project_id, "name": project_id, "ready": False},
    )

    payload = disasm_server.route_request("POST", "/api/projects", {}, {"id": "demo"})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["id"] == "demo"


def test_route_project_returns_project_and_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: {"id": project_name, "name": project_name, "ready": True},
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych", {})
    data = cast(dict[str, object], payload["data"])
    project = cast(dict[str, object], data["project"])

    assert payload["ok"] is True
    assert project["name"] == "bloodwych"
    assert "session" not in data


def test_route_listing_returns_empty_payload_for_unready_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: {"id": project_name, "name": project_name, "ready": False},
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
        lambda project_name: {"id": project_name, "name": project_name, "ready": True},
    )
    with pytest.raises(ValueError, match="Canonical rows not loaded"):
        disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})


def test_route_listing_returns_cached_window(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [ListingRow(row_id="r0", kind="instruction", text="moveq #0,d0\n", addr=0x10)]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: {"id": project_name, "name": project_name, "ready": True},
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


def test_route_listing_open_starts_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: {"id": project_name, "name": project_name, "ready": True},
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_listing_job",
        lambda project_name: {"job_id": "job-1", "project_id": project_name, "status": "queued"},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/listing/open",
        {},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-1"


def test_route_listing_status_returns_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_job_payload",
        lambda job_id: {"job_id": job_id, "status": "building", "phase": "rows"},
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing/status",
        {"job_id": ["job-1"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["status"] == "building"


def test_json_bytes_returns_valid_json() -> None:
    body = disasm_server._json_bytes({"ok": True, "data": {"x": 1}})

    assert json.loads(body.decode("utf-8")) == {"ok": True, "data": {"x": 1}}


def test_resolve_static_response_serves_index() -> None:
    content_type, body = disasm_server.resolve_static_response("/")

    assert content_type == "text/html; charset=utf-8"
    assert b"Disassembly Projects" in body


def test_resolve_static_response_serves_project_route() -> None:
    content_type, body = disasm_server.resolve_static_response("/bloodwych")

    assert content_type == "text/html; charset=utf-8"
    assert b"Disassembly Projects" in body


def test_resolve_static_response_rejects_missing_file() -> None:
    with pytest.raises(FileNotFoundError, match="Unknown route"):
        disasm_server.resolve_static_response("/missing.txt")


def test_route_get_entity_returns_annotation_view(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "get_entity",
                        lambda project_name, addr: {"addr": addr, "name": "main"})

    payload = disasm_server.route_request(
        "GET", "/api/projects/bloodwych/entities/0x0000", {})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["name"] == "main"


def test_route_patch_entity_updates_annotations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server, "patch_entity",
        lambda project_name, addr, body: {"addr": addr, "name": body["name"]},
    )

    payload = disasm_server.route_request(
        "PATCH", "/api/projects/bloodwych/entities/0x0000", {},
        {"name": "main"})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["name"] == "main"
