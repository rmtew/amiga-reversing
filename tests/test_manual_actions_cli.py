from __future__ import annotations

import json
from typing import cast

import pytest

from amiga_reversing.tools import manual_actions


def test_manual_actions_cli_lists_catalog_contexts(monkeypatch, capsys) -> None:
    calls: list[tuple[str, dict[str, list[str]]]] = []
    locator_json = json.dumps(
        {"target_id": "bloodwych", "projection_hash": "cache", "row_key": "row-2", "kind": "instruction"}
    )
    locators_json = json.dumps(
        [
            {"target_id": "bloodwych", "projection_hash": "cache", "row_key": "row-2", "kind": "instruction"},
            {"target_id": "bloodwych", "projection_hash": "cache", "row_key": "row-3", "kind": "instruction"},
        ]
    )

    def route(method: str, path: str, query, body=None):
        assert method == "GET"
        assert path == "/api/projects/bloodwych/commands"
        calls.append((path, query))
        return {"ok": True, "data": {"commands": [{"action_id": "review.navigate"}]}}

    monkeypatch.setattr(manual_actions.server, "route_request", route)

    commands = [
        ["list", "bloodwych", "--context", "target"],
        ["list", "bloodwych", "--context", "review-item", "--review-index", "0"],
        ["list", "bloodwych", "--context", "row", "--locator", locator_json],
        [
            "list",
            "bloodwych",
            "--context",
            "range",
            "--locators",
            locators_json,
        ],
        [
            "list",
            "bloodwych",
            "--context",
            "element",
            "--locator",
            locator_json,
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

    assert payload["commands"] == [{"action_id": "review.navigate"}]
    assert calls == [
        ("/api/projects/bloodwych/commands", {"context": ["target"]}),
        ("/api/projects/bloodwych/commands", {"context": ["review-item"], "review_index": ["0"]}),
        ("/api/projects/bloodwych/commands", {"context": ["row"], "locator": [locator_json]}),
        (
            "/api/projects/bloodwych/commands",
            {"context": ["range"], "locators": [locators_json]},
        ),
        (
            "/api/projects/bloodwych/commands",
            {
                "context": ["element"],
                "locator": [locator_json],
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
                "commands": [
                    {"action_id": "review.navigate"},
                    {"action_id": "review.label.rename", "parameter_schema": {"required": ["name"]}},
                ]
            },
        }

    monkeypatch.setattr(manual_actions.server, "route_request", route)

    assert manual_actions.main(["list", "bloodwych", "--context", "review-item", "--review-index", "0"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["commands"][0]["action_id"] == "review.navigate"
    assert manual_actions.main(["show", "bloodwych", "--context", "review-item", "--review-index", "0", "review.label.rename"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload == {"action_id": "review.label.rename", "parameter_schema": {"required": ["name"]}}


def test_manual_actions_cli_invokes_catalog_action(monkeypatch, capsys) -> None:
    captured_body: dict[str, object] = {}

    def route(method: str, path: str, query, body=None):
        if path == "/api/projects/bloodwych/listing/open":
            assert method == "POST"
            return {"ok": True, "data": {"job_id": "listing-job", "status": "ready"}}
        assert method == "POST"
        assert path == "/api/projects/bloodwych/commands/execute"
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
        "command_id": "review.seed.data.string",
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
            "--locators",
            json.dumps([
                {
                    "target_id": "bloodwych",
                    "projection_hash": "cache",
                    "row_key": "row-2",
                    "kind": "instruction",
                },
                {
                    "target_id": "bloodwych",
                    "projection_hash": "cache",
                    "row_key": "row-3",
                    "kind": "instruction",
                },
            ]),
            "range.review_note.add",
            "--param",
            "title=\"Check range\"",
        ]
    ) == 0
    json.loads(capsys.readouterr().out)
    assert captured_body == {
        "command_id": "range.review_note.add",
        "context": {
            "kind": "range",
            "locators": [
                {
                    "target_id": "bloodwych",
                    "projection_hash": "cache",
                    "row_key": "row-2",
                    "kind": "instruction",
                },
                {
                    "target_id": "bloodwych",
                    "projection_hash": "cache",
                    "row_key": "row-3",
                    "kind": "instruction",
                },
            ],
        },
        "parameters": {"title": "Check range"},
    }


def test_manual_actions_cli_stops_when_listing_is_not_ready(monkeypatch) -> None:
    def route(method: str, path: str, query, body=None):
        assert method == "POST"
        assert path == "/api/projects/bloodwych/listing/open"
        return {"ok": True, "data": {"job_id": "listing-job", "status": "failed", "error": "bad listing"}}

    monkeypatch.setattr(manual_actions.server, "route_request", route)

    with pytest.raises(SystemExit, match="bad listing"):
        manual_actions.main(["invoke", "bloodwych", "target.code.seed"])


def test_manual_actions_cli_invokes_target_action_batch_in_one_listing_session(monkeypatch, capsys) -> None:
    calls: list[tuple[str, object]] = []

    def route(method: str, path: str, query, body=None):
        calls.append((path, body))
        if path == "/api/projects/bloodwych/listing/open":
            return {"ok": True, "data": {"job_id": "listing-job", "status": "ready"}}
        assert method == "POST"
        assert path == "/api/projects/bloodwych/commands/execute"
        return {"ok": True, "data": {"command_id": cast(dict[str, object], body)["command_id"]}}

    monkeypatch.setattr(manual_actions.server, "route_request", route)

    assert manual_actions.main(
        [
            "invoke-batch",
            "bloodwych",
            "--action",
            '{"command_id":"target.seed.remove","parameters":{"seed_id":"old"}}',
            "--action",
            '{"command_id":"target.code.seed","parameters":{"hunk":0,"addr":42,"name":"new"}}',
        ]
    ) == 0

    assert json.loads(capsys.readouterr().out) == {
        "actions": [{"command_id": "target.seed.remove"}, {"command_id": "target.code.seed"}]
    }
    assert [path for path, _body in calls] == [
        "/api/projects/bloodwych/listing/open",
        "/api/projects/bloodwych/commands/execute",
        "/api/projects/bloodwych/commands/execute",
    ]


def test_manual_actions_cli_reports_invalid_inputs(monkeypatch) -> None:
    def route(method: str, path: str, query, body=None):
        assert method == "GET"
        return {"ok": True, "data": {"commands": [{"action_id": "review.navigate"}]}}

    monkeypatch.setattr(manual_actions.server, "route_request", route)

    with pytest.raises(SystemExit) as missing_action:
        manual_actions.main(["show", "bloodwych", "missing.action"])
    assert str(missing_action.value) == "Catalog command not found: missing.action"

    with pytest.raises(SystemExit) as invalid_param:
        manual_actions.main(["invoke", "bloodwych", "review.seed.data.string", "--param", "bad"])
    assert str(invalid_param.value) == "Invalid --param value: bad"
