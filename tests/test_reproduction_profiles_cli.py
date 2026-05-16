from __future__ import annotations

import json
from typing import cast

from amiga_reversing.tools import reproduction_profiles


def test_reproduction_profiles_cli_list_show_set(monkeypatch, capsys) -> None:
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def route(method: str, path: str, query, body=None):
        calls.append((method, path, cast(dict[str, object] | None, body)))
        if path.endswith("/profiles"):
            return {"ok": True, "data": {"profiles": [{"profile_id": "exact-framework"}]}}
        if method == "GET":
            return {"ok": True, "data": {"profile_id": "source-vasm"}}
        return {"ok": True, "data": {"active": {"profile_id": cast(dict[str, object], body)["profile_id"]}}}

    monkeypatch.setattr(reproduction_profiles.server, "route_request", route)

    assert reproduction_profiles.main(["list", "bloodwych"]) == 0
    assert json.loads(capsys.readouterr().out)["profiles"][0]["profile_id"] == "exact-framework"
    assert reproduction_profiles.main(["show", "bloodwych"]) == 0
    assert json.loads(capsys.readouterr().out)["profile_id"] == "source-vasm"
    assert reproduction_profiles.main(["set", "bloodwych", "content-semantic"]) == 0
    assert json.loads(capsys.readouterr().out)["active"]["profile_id"] == "content-semantic"
    assert calls == [
        ("GET", "/api/projects/bloodwych/reproduction/profiles", None),
        ("GET", "/api/projects/bloodwych/reproduction/profile", None),
        ("POST", "/api/projects/bloodwych/reproduction/profile", {"profile_id": "content-semantic"}),
    ]
