import json
from pathlib import Path

from disasm import server as disasm_server
from disasm.types import DisassemblySession, ListingRow


def test_route_projects_returns_project_list(monkeypatch):
    monkeypatch.setattr(disasm_server, "list_projects",
                        lambda: [{"name": "bloodwych"}])

    payload = disasm_server.route_request("GET", "/api/projects", {})

    assert payload["ok"] is True
    assert payload["data"] == [{"name": "bloodwych"}]


def test_route_project_returns_paths_and_session(monkeypatch, tmp_path):
    class FakePaths:
        name = "bloodwych"
        target_dir = tmp_path / "targets" / "bloodwych"
        entities_path = target_dir / "entities.jsonl"
        output_path = target_dir / "Bloodwych439.s"
        binary_path = tmp_path / "bin" / "Bloodwych439"
        analysis_cache_path = tmp_path / "bin" / "Bloodwych439.analysis"
        provenance = "output-stem"

    session = DisassemblySession(
        target_name="bloodwych",
        binary_path=Path("bin/Bloodwych439"),
        entities_path=Path("targets/bloodwych/entities.jsonl"),
        analysis_cache_path=Path("bin/Bloodwych439.analysis"),
        output_path=Path("targets/bloodwych/Bloodwych439.s"),
        entities=[],
        hunk_sessions=[],
    )

    monkeypatch.setattr(disasm_server, "resolve_project_paths",
                        lambda project_name: FakePaths())
    monkeypatch.setattr(disasm_server, "build_project_session",
                        lambda project_name: session)
    monkeypatch.setattr(disasm_server, "session_metadata",
                        lambda seen_session: {"target_name": seen_session.target_name})

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych", {})

    assert payload["ok"] is True
    assert payload["data"]["project"]["name"] == "bloodwych"
    assert payload["data"]["project"]["provenance"] == "output-stem"
    assert payload["data"]["session"]["target_name"] == "bloodwych"


def test_route_listing_returns_window_payload(monkeypatch):
    session = DisassemblySession(
        target_name="bloodwych",
        binary_path=Path("bin/Bloodwych439"),
        entities_path=Path("targets/bloodwych/entities.jsonl"),
        analysis_cache_path=Path("bin/Bloodwych439.analysis"),
        output_path=Path("targets/bloodwych/Bloodwych439.s"),
        entities=[],
        hunk_sessions=[],
    )
    rows = [ListingRow(row_id="r0", kind="instruction", text="moveq #0,d0\n", addr=0x10)]

    monkeypatch.setattr(disasm_server, "build_project_session",
                        lambda project_name: session)
    monkeypatch.setattr(disasm_server, "emit_session_rows",
                        lambda seen_session: rows)
    monkeypatch.setattr(
        disasm_server, "listing_window_payload",
        lambda seen_rows, addr, before=80, after=160: {
            "anchor_addr": addr,
            "before": before,
            "after": after,
            "rows": [{"row_id": seen_rows[0].row_id}],
        })

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"addr": ["0x10"], "before": ["5"], "after": ["7"]},
    )

    assert payload["ok"] is True
    assert payload["data"]["anchor_addr"] == 0x10
    assert payload["data"]["before"] == 5
    assert payload["data"]["after"] == 7
    assert payload["data"]["rows"] == [{"row_id": "r0"}]


def test_json_bytes_returns_valid_json():
    body = disasm_server._json_bytes({"ok": True, "data": {"x": 1}})

    assert json.loads(body.decode("utf-8")) == {"ok": True, "data": {"x": 1}}


def test_resolve_static_response_serves_index():
    content_type, body = disasm_server.resolve_static_response("/")

    assert content_type == "text/html; charset=utf-8"
    assert b"Disassembly Browser" in body


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
