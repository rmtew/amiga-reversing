from __future__ import annotations

from pathlib import Path

import pytest

from amiga_reversing import reversing_loop
from amiga_reversing.disasm.manual_actions import (
    ReviewItemKind,
    ReviewItemScope,
    ReviewItemState,
)
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord


def test_agent_reversing_loop_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "source_binary.json").write_text("{}", encoding="utf-8")
    locator = {
        "target_id": "demo",
        "projection_hash": "projection-1",
        "row_key": "row-1",
        "section_index": 0,
        "start_offset": 0,
        "end_offset": 2,
        "kind": "instruction",
    }
    item = {
        "kind": ReviewItemKind.REVIEW_NOTE,
        "scope": ReviewItemScope.RANGE,
        "state": ReviewItemState.OPEN,
        "item_id": "review-note:h0:$00000000-$00000002",
        "locator": locator,
        "ref_count": 1,
        "message": "candidate with xrefs",
        "suggested_actions": [{"action": "comment.edit"}],
    }
    monkeypatch.setattr(reversing_loop.projects, "get_project", lambda target_id, project_root: _project((item,)))
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if method == "GET":
            assert query["context"] == ["row"]
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        assert isinstance(body, dict)
        assert body["context"]["locator"]["row_key"] == "row-1"
        _write_manual_log(target_dir)
        return {
            "data": {
                "action": {"action_id": "manual-1"},
                "mutation": {
                    "durable_action_id": "manual-1",
                    "manual_action_log_count": 1,
                    "affected_locators": [locator],
                },
                "workflow_profile": {
                    "workflow_id": "manual_command_execution",
                    "spans": [{"name": "manual_action_append", "seconds": 0.01, "module": "manual_action_log"}],
                },
            }
        }

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    hygiene = reversing_loop.inspect_target_hygiene("demo", project_root=tmp_path)
    read_only = reversing_loop.inspect_target("demo", project_root=tmp_path)
    dry_run = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)
    report = reversing_loop.run_one_iteration("demo", mode="continue", project_root=tmp_path)

    assert hygiene.safe_to_continue is True
    assert read_only["candidate_work"][0]["locator"]["row_key"] == "row-1"
    assert dry_run["action_result"]["status"] == "dry_run"
    assert report["verification"]["status"] == "passed"
    assert report["workflow_profile"]["workflow_id"] == "manual_command_execution"
    assert report["next"]["recommendation"] == "continue"
    assert calls == [
        ("GET", "/api/projects/demo/commands"),
        ("POST", "/api/projects/demo/commands/execute"),
    ]
    latest_path = target_dir / "agent" / "latest-reversing-loop.json"
    assert latest_path.exists()


def _project(review_items: tuple[dict[str, object], ...]) -> ProjectRecord:
    return ProjectRecord(
        id="demo",
        name="demo",
        kind=ProjectKind.BINARY,
        target_dir="targets/demo",
        output_path=None,
        binary_path="bin/demo.bin",
        ready=True,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=None,
        disk_type=None,
        parent_project_id=None,
        target_type="program",
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        manual_action_log_path="targets/demo/manual_actions.jsonl",
        review_state=None,
        review_items=review_items,
        manual_state={"review_state": "needs_review"},
    )


def _write_manual_log(target_dir: Path) -> None:
    (target_dir / "manual_actions.jsonl").write_text(
        '{"record": "manual_action_log_header"}\n{"record": "manual_action", "action_id": "manual-1"}\n',
        encoding="utf-8",
    )
