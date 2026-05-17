from __future__ import annotations

import json
from typing import cast

from amiga_reversing.tools import tool_registry


def test_tool_registry_cli_registry_inventory_capability_and_set_path(monkeypatch, capsys) -> None:
    calls: list[tuple[str, str, dict[str, list[str]], dict[str, object] | None]] = []

    def route(method: str, path: str, query, body=None):
        calls.append((method, path, query, cast(dict[str, object] | None, body)))
        if path == "/api/tool-registry":
            return {"ok": True, "data": {"version": 2, "runtime_tools": {}, "functional_tools": {}}}
        if path == "/api/tools/runtimes":
            return {"ok": True, "data": {"runtimes": [{"runtime_tool_id": "host", "status": "available"}]}}
        if path == "/api/tools/functional":
            return {"ok": True, "data": {"tools": [{"functional_tool_id": "vasm", "status": "missing"}]}}
        if path == "/api/tools/capabilities/assemble_vasm_source":
            return {"ok": True, "data": {"capability_id": "assemble_vasm_source", "selected": {}}}
        if path == "/api/tools/path":
            return {
                "ok": True,
                "data": {"functional_tools": {cast(dict[str, object], body)["tool_id"]: {"path": cast(dict[str, object], body)["path"]}}},
            }
        raise AssertionError(path)

    monkeypatch.setattr(tool_registry.server, "route_request", route)

    assert tool_registry.main(["registry"]) == 0
    assert json.loads(capsys.readouterr().out)["version"] == 2
    assert tool_registry.main(["runtimes"]) == 0
    assert json.loads(capsys.readouterr().out)["runtimes"][0]["runtime_tool_id"] == "host"
    assert tool_registry.main(["tools"]) == 0
    assert json.loads(capsys.readouterr().out)["tools"][0]["functional_tool_id"] == "vasm"
    assert tool_registry.main(["capability", "assemble_vasm_source"]) == 0
    assert json.loads(capsys.readouterr().out)["capability_id"] == "assemble_vasm_source"
    assert tool_registry.main(["set-path", "functional", "vasm", "tools/vasm"]) == 0
    assert json.loads(capsys.readouterr().out)["functional_tools"]["vasm"]["path"] == "tools/vasm"

    assert calls == [
        ("GET", "/api/tool-registry", {}, None),
        ("GET", "/api/tools/runtimes", {}, None),
        ("GET", "/api/tools/functional", {}, None),
        ("GET", "/api/tools/capabilities/assemble_vasm_source", {}, None),
        ("POST", "/api/tools/path", {}, {"kind": "functional", "tool_id": "vasm", "path": "tools/vasm"}),
    ]


def test_tool_registry_cli_project_availability(monkeypatch, capsys) -> None:
    def route(method: str, path: str, query, body=None):
        assert method == "GET"
        assert path == "/api/projects/bloodwych/tool-availability"
        assert query == {"profile_id": ["source-devpac"]}
        return {"ok": True, "data": {"availability": [{"tool_id": "genam", "status": "missing", "missing_runtime_ids": ["vamos"]}]}}

    monkeypatch.setattr(tool_registry.server, "route_request", route)

    assert tool_registry.main(["project-availability", "bloodwych", "--profile-id", "source-devpac"]) == 0
    assert json.loads(capsys.readouterr().out)["availability"][0]["missing_runtime_ids"] == ["vamos"]
