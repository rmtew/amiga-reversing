import json

from disasm import server as disasm_server
from disasm.types import ListingRow


def test_route_projects_returns_project_list(monkeypatch):
    monkeypatch.setattr(disasm_server, "list_projects",
                        lambda: [{"id": "bloodwych", "name": "bloodwych"}])

    payload = disasm_server.route_request("GET", "/api/projects", {})

    assert payload["ok"] is True
    assert payload["data"] == [{"id": "bloodwych", "name": "bloodwych"}]


def test_route_create_project(monkeypatch):
    monkeypatch.setattr(
        disasm_server,
        "create_project",
        lambda project_id: {"id": project_id, "name": project_id, "ready": False},
    )

    payload = disasm_server.route_request("POST", "/api/projects", {}, {"id": "demo"})

    assert payload["ok"] is True
    assert payload["data"]["id"] == "demo"


def test_route_project_returns_project_and_session(monkeypatch):
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: {"id": project_name, "name": project_name, "ready": True},
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych", {})

    assert payload["ok"] is True
    assert payload["data"]["project"]["name"] == "bloodwych"
    assert "session" not in payload["data"]


def test_route_listing_returns_empty_payload_for_unready_project(monkeypatch):
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

    assert payload["ok"] is True
    assert payload["data"]["rows"] == []


def test_route_listing_raises_if_rows_not_loaded(monkeypatch):
    disasm_server._PROJECT_ROW_CACHE.clear()
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: {"id": project_name, "name": project_name, "ready": True},
    )
    try:
        disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    except ValueError as exc:
        assert "Canonical rows not loaded" in str(exc)
    else:
        raise AssertionError("expected unloaded canonical rows failure")


def test_route_listing_returns_cached_window(monkeypatch):
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

    assert payload["ok"] is True
    assert payload["data"]["anchor_addr"] == 0x10
    assert payload["data"]["rows"][0]["row_id"] == "r0"


def test_route_listing_open_starts_job(monkeypatch):
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

    assert payload["ok"] is True
    assert payload["data"]["job_id"] == "job-1"


def test_route_listing_status_returns_job(monkeypatch):
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

    assert payload["ok"] is True
    assert payload["data"]["status"] == "building"


def test_json_bytes_returns_valid_json():
    body = disasm_server._json_bytes({"ok": True, "data": {"x": 1}})

    assert json.loads(body.decode("utf-8")) == {"ok": True, "data": {"x": 1}}


def test_resolve_static_response_serves_index():
    content_type, body = disasm_server.resolve_static_response("/")

    assert content_type == "text/html; charset=utf-8"
    assert b"Disassembly Projects" in body


def test_resolve_static_response_serves_project_route():
    content_type, body = disasm_server.resolve_static_response("/bloodwych")

    assert content_type == "text/html; charset=utf-8"
    assert b"Disassembly Projects" in body


def test_resolve_static_response_rejects_missing_file():
    try:
        disasm_server.resolve_static_response("/missing.txt")
    except FileNotFoundError as exc:
        assert "Unknown route" in str(exc)
    else:
        raise AssertionError("expected missing static file error")


def test_route_get_entity_returns_annotation_view(monkeypatch):
    monkeypatch.setattr(disasm_server, "get_entity",
                        lambda project_name, addr: {"addr": addr, "name": "main"})

    payload = disasm_server.route_request(
        "GET", "/api/projects/bloodwych/entities/0x0000", {})

    assert payload["ok"] is True
    assert payload["data"]["name"] == "main"


def test_route_patch_entity_updates_annotations(monkeypatch):
    monkeypatch.setattr(
        disasm_server, "patch_entity",
        lambda project_name, addr, body: {"addr": addr, "name": body["name"]},
    )

    payload = disasm_server.route_request(
        "PATCH", "/api/projects/bloodwych/entities/0x0000", {},
        {"name": "main"})

    assert payload["ok"] is True
    assert payload["data"]["name"] == "main"
