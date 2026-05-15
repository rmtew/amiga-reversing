from __future__ import annotations

import json
from typing import cast

import pytest

from amiga_reversing.tools import manual_actions


def test_manual_actions_cli_lists_catalog_contexts(monkeypatch, capsys) -> None:
    calls: list[tuple[str, dict[str, list[str]]]] = []

    def route(method: str, path: str, query, body=None):
        assert method == "GET"
        assert path == "/api/projects/bloodwych/manual-action-catalog"
        calls.append((path, query))
        return {"ok": True, "data": {"actions": [{"action_id": "review.navigate"}]}}

    monkeypatch.setattr(manual_actions.server, "route_request", route)

    commands = [
        ["list", "bloodwych", "--context", "target"],
        ["list", "bloodwych", "--context", "review-item", "--review-index", "0"],
        ["list", "bloodwych", "--context", "row", "--row-index", "2"],
        [
            "list",
            "bloodwych",
            "--context",
            "range",
            "--row-indexes",
            "2,3",
        ],
        [
            "list",
            "bloodwych",
            "--context",
            "element",
            "--row-index",
            "2",
            "--element-kind",
            "data_literal",
            "--element-id",
            "row-2:data_literal:2",
        ],
    ]
    payload: dict[str, object] = {}
    for command in commands:
        assert manual_actions.main(command) == 0
        payload = json.loads(capsys.readouterr().out)

    assert payload["actions"] == [{"action_id": "review.navigate"}]
    assert calls == [
        ("/api/projects/bloodwych/manual-action-catalog", {"context": ["target"]}),
        ("/api/projects/bloodwych/manual-action-catalog", {"context": ["review-item"], "review_index": ["0"]}),
        ("/api/projects/bloodwych/manual-action-catalog", {"context": ["row"], "row_index": ["2"]}),
        (
            "/api/projects/bloodwych/manual-action-catalog",
            {"context": ["range"], "row_indexes": ["2,3"]},
        ),
        (
            "/api/projects/bloodwych/manual-action-catalog",
            {
                "context": ["element"],
                "row_index": ["2"],
                "element_kind": ["data_literal"],
                "element_id": ["row-2:data_literal:2"],
            },
        ),
    ]


def test_manual_actions_cli_shows_catalog_action(monkeypatch, capsys) -> None:
    def route(method: str, path: str, query, body=None):
        assert method == "GET"
        return {
            "ok": True,
            "data": {
                "actions": [
                    {"action_id": "review.navigate"},
                    {"action_id": "review.label.rename", "parameter_schema": {"required": ["name"]}},
                ]
            },
        }

    monkeypatch.setattr(manual_actions.server, "route_request", route)

    assert manual_actions.main(["list", "bloodwych", "--context", "review-item", "--review-index", "0"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["actions"][0]["action_id"] == "review.navigate"
    assert manual_actions.main(["show", "bloodwych", "--context", "review-item", "--review-index", "0", "review.label.rename"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload == {"action_id": "review.label.rename", "parameter_schema": {"required": ["name"]}}


def test_manual_actions_cli_invokes_catalog_action(monkeypatch, capsys) -> None:
    captured_body: dict[str, object] = {}

    def route(method: str, path: str, query, body=None):
        assert method == "POST"
        assert path == "/api/projects/bloodwych/manual-action-catalog/execute"
        assert query == {}
        captured_body.update(cast(dict[str, object], body))
        return {"ok": True, "data": {"action": {"kind": "create_manual_seed"}}}

    monkeypatch.setattr(manual_actions.server, "route_request", route)

    assert manual_actions.main(
        [
            "invoke",
            "bloodwych",
            "--context",
            "review-item",
            "--review-index",
            "0",
            "review.seed.data.string",
            "--param",
            "unit=\"byte\"",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)

    assert captured_body == {
        "action_id": "review.seed.data.string",
        "context": {"kind": "review_item", "review_index": 0},
        "parameters": {"unit": "byte"},
    }
    assert payload["action"]["kind"] == "create_manual_seed"

    captured_body.clear()
    assert manual_actions.main(
        [
            "invoke",
            "bloodwych",
            "--context",
            "range",
            "--row-indexes",
            "2,3",
            "range.review_note.add",
            "--param",
            "title=\"Check range\"",
        ]
    ) == 0
    json.loads(capsys.readouterr().out)
    assert captured_body == {
        "action_id": "range.review_note.add",
        "context": {"kind": "range", "row_indexes": [2, 3]},
        "parameters": {"title": "Check range"},
    }


def test_manual_actions_cli_reports_invalid_inputs(monkeypatch) -> None:
    def route(method: str, path: str, query, body=None):
        assert method == "GET"
        return {"ok": True, "data": {"actions": [{"action_id": "review.navigate"}]}}

    monkeypatch.setattr(manual_actions.server, "route_request", route)

    with pytest.raises(SystemExit) as missing_action:
        manual_actions.main(["show", "bloodwych", "missing.action"])
    assert str(missing_action.value) == "Catalog action not found: missing.action"

    with pytest.raises(SystemExit) as invalid_param:
        manual_actions.main(["invoke", "bloodwych", "review.seed.data.string", "--param", "bad"])
    assert str(invalid_param.value) == "Invalid --param value: bad"
