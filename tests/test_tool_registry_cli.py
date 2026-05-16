from __future__ import annotations

import json
from typing import cast

from amiga_reversing.tools import tool_registry


def test_tool_registry_cli_registry_availability_and_set_path(monkeypatch, capsys) -> None:
    calls: list[tuple[str, str, dict[str, list[str]], dict[str, object] | None]] = []

    def route(method: str, path: str, query, body=None):
        calls.append((method, path, query, cast(dict[str, object] | None, body)))
        if path == "/api/tool-registry":
            return {"ok": True, "data": {"version": 1, "tools": {}}}
        if path == "/api/tools/path":
            return {"ok": True, "data": {"tools": {cast(dict[str, object], body)["tool_id"]: {"path": cast(dict[str, object], body)["path"]}}}}
        return {"ok": True, "data": {"availability": [{"tool_id": "vasm", "status": "missing"}]}}

    monkeypatch.setattr(tool_registry.server, "route_request", route)

    assert tool_registry.main(["registry"]) == 0
    assert json.loads(capsys.readouterr().out)["version"] == 1
    assert tool_registry.main(["availability", "--tool-ids", "vasm", "--required-tool-ids", "vasm"]) == 0
    assert json.loads(capsys.readouterr().out)["availability"][0]["tool_id"] == "vasm"
    assert tool_registry.main(["set-path", "vasm", "tools/vasm"]) == 0
    assert json.loads(capsys.readouterr().out)["tools"]["vasm"]["path"] == "tools/vasm"

    assert calls == [
        ("GET", "/api/tool-registry", {}, None),
        ("GET", "/api/tools/availability", {"tool_ids": ["vasm"], "required_tool_ids": ["vasm"]}, None),
        ("POST", "/api/tools/path", {}, {"tool_id": "vasm", "path": "tools/vasm"}),
    ]


def test_tool_registry_cli_project_availability(monkeypatch, capsys) -> None:
    def route(method: str, path: str, query, body=None):
        assert method == "GET"
        assert path == "/api/projects/bloodwych/tool-availability"
        assert query == {"profile_id": ["source-devpac"]}
        return {"ok": True, "data": {"availability": [{"tool_id": "vamos", "status": "missing"}]}}

    monkeypatch.setattr(tool_registry.server, "route_request", route)

    assert tool_registry.main(["project-availability", "bloodwych", "--profile-id", "source-devpac"]) == 0
    assert json.loads(capsys.readouterr().out)["availability"][0]["tool_id"] == "vamos"
