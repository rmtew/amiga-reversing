from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from amiga_reversing import reversing_loop
from amiga_reversing.disasm.manual_actions import (
    ReviewItemKind,
    ReviewItemScope,
    ReviewItemState,
)
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord


def _target(tmp_path: Path, name: str = "demo") -> Path:
    target_dir = tmp_path / "targets" / name
    target_dir.mkdir(parents=True)
    return target_dir


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


def test_inspect_report_generation_does_not_mutate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_dir = _target(tmp_path)
    (target_dir / "source_binary.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(reversing_loop.projects, "get_project", lambda target_id, project_root: _project(()))

    report = reversing_loop.inspect_target("demo", project_root=tmp_path)

    assert report["target_id"] == "demo"
    assert report["safe_to_mutate"] is True
    assert sorted(path.name for path in target_dir.iterdir()) == ["source_binary.json"]


def test_inspect_candidates_include_durable_identity_or_locator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    item = {
        "kind": ReviewItemKind.ORPHAN_CODE_CANDIDATE,
        "scope": ReviewItemScope.RANGE,
        "state": ReviewItemState.OPEN,
        "item_id": "orphan:h0:$00000010-$00000012",
        "hunk": 0,
        "start": 0x10,
        "end": 0x12,
        "ref_count": 2,
        "message": "orphan code",
        "suggested_actions": [{"action": "create_manual_seed"}],
    }
    monkeypatch.setattr(reversing_loop.projects, "get_project", lambda target_id, project_root: _project((item,)))

    report = reversing_loop.inspect_target("demo", project_root=tmp_path)
    candidate = report["candidate_work"][0]

    assert candidate["durable_id"] == "orphan:h0:$00000010-$00000012"
    assert candidate["locator"] == {"section_index": 0, "start_offset": 0x10, "end_offset": 0x12}
    assert candidate["evidence"]["has_xrefs"] is True


def test_inspect_unsafe_hygiene_blocks_mutation_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_dir = _target(tmp_path)
    (target_dir / "unknown.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(reversing_loop.projects, "get_project", lambda target_id, project_root: _project(()))

    report = reversing_loop.inspect_target("demo", project_root=tmp_path)

    assert report["safe_to_mutate"] is False
    assert report["hygiene"]["unknown_files"] == ["unknown.txt"]


def test_inspect_cli_reports_json(tmp_path: Path) -> None:
    _target(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "amiga_reversing.reversing_loop",
            "--project-root",
            str(tmp_path),
            "inspect",
            "--target",
            "demo",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert payload["target_id"] == "demo"
    assert payload["candidate_work"] == []
    assert payload["target_state"]["manual_action_log"]["count"] == 0


def test_run_identity_creation_includes_report_paths(tmp_path: Path) -> None:
    _target(tmp_path)

    result = reversing_loop.start_or_resume_run(
        "demo",
        mode="clean-run",
        project_root=tmp_path,
        run_id="run-test",
        now=datetime(2026, 5, 18, tzinfo=UTC),
    )

    assert result.status == "started"
    assert result.run_state is not None
    assert result.run_state["run_id"] == "run-test"
    assert result.run_state["target_id"] == "demo"
    assert result.run_state["mode"] == "clean-run"
    assert result.run_state["last_iteration_id"] is None
    assert result.run_state["report_paths"]["history"].endswith("reversing-loop.jsonl")


def test_iteration_history_is_append_only(tmp_path: Path) -> None:
    _target(tmp_path)
    state = reversing_loop.start_or_resume_run("demo", mode="clean-run", project_root=tmp_path, run_id="run-test").run_state
    assert state is not None

    reversing_loop.write_iteration_report("demo", {"run_state": state, "iteration": {"id": "001", "status": "complete"}}, project_root=tmp_path)
    reversing_loop.write_iteration_report("demo", {"run_state": state, "iteration": {"id": "002", "status": "complete"}}, project_root=tmp_path)

    history_path = Path(state["report_paths"]["history"])
    assert len(history_path.read_text(encoding="utf-8").splitlines()) == 2
    latest = json.loads(Path(state["report_paths"]["latest"]).read_text(encoding="utf-8"))
    assert latest["iteration"]["id"] == "002"


def test_latest_report_write_is_atomic(tmp_path: Path) -> None:
    _target(tmp_path)
    state = reversing_loop.start_or_resume_run("demo", mode="clean-run", project_root=tmp_path, run_id="run-test").run_state
    assert state is not None

    reversing_loop.write_iteration_report("demo", {"run_state": state, "iteration": {"id": "001", "status": "complete"}}, project_root=tmp_path)

    latest_path = Path(state["report_paths"]["latest"])
    assert latest_path.exists()
    assert not latest_path.with_name(f".{latest_path.name}.tmp").exists()


def test_continue_resumes_complete_non_terminal_run(tmp_path: Path) -> None:
    _target(tmp_path)
    state = reversing_loop.start_or_resume_run("demo", mode="clean-run", project_root=tmp_path, run_id="run-test").run_state
    assert state is not None
    reversing_loop.write_iteration_report("demo", {"run_state": state, "iteration": {"id": "001", "status": "complete"}}, project_root=tmp_path)

    result = reversing_loop.start_or_resume_run("demo", mode="continue", project_root=tmp_path)

    assert result.status == "resumed"
    assert result.run_state is not None
    assert result.run_state["run_id"] == "run-test"


def test_continue_rejects_partial_iteration_state(tmp_path: Path) -> None:
    _target(tmp_path)
    state = reversing_loop.start_or_resume_run("demo", mode="clean-run", project_root=tmp_path, run_id="run-test").run_state
    assert state is not None
    reversing_loop.write_iteration_report("demo", {"run_state": state, "iteration": {"id": "001", "status": "partial"}}, project_root=tmp_path)

    result = reversing_loop.start_or_resume_run("demo", mode="continue", project_root=tmp_path)

    assert result.status == "blocked"
    assert result.run_state is None
    assert result.reason == "latest iteration is partial; start a new clean-run or reimport run explicitly"


def test_run_one_dry_run_selects_command_without_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_locator())
    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: calls.append(method) or {"data": {}},
    )

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert calls == []
    assert report["action"]["command_id"] == "comment.edit"
    assert report["action_result"]["status"] == "dry_run"
    assert not (tmp_path / "targets" / "demo" / "manual_actions.jsonl").exists()


def test_run_one_executes_existing_command_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _target(tmp_path)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_locator())

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if method == "GET":
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        return {
            "data": {
                "action": {"action_id": "manual-1"},
                "mutation": {"durable_action_id": "manual-1"},
                "workflow_profile": {"workflow_id": "manual_command_execution", "spans": [{"name": "manual_action_append"}]},
            }
        }

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert calls == [
        ("GET", "/api/projects/demo/commands"),
        ("POST", "/api/projects/demo/commands/execute"),
    ]
    assert report["action_result"]["status"] == "executed"
    assert report["durable_result"]["mutation"]["durable_action_id"] == "manual-1"


def test_run_one_report_includes_workflow_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _target(tmp_path)
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_locator())
    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: (
            {"data": {"commands": [{"command_id": "comment.edit"}]}}
            if method == "GET"
            else {"data": {"workflow_profile": {"workflow_id": "manual_command_execution", "spans": []}}}
        ),
    )

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["workflow_profile"] == {"workflow_id": "manual_command_execution", "spans": []}


def _inspect_with_locator() -> dict[str, object]:
    locator = {
        "target_id": "demo",
        "projection_hash": "projection-1",
        "row_key": "row-1",
        "section_index": 0,
        "start_offset": 0,
        "end_offset": 2,
        "kind": "instruction",
    }
    return {
        "target_id": "demo",
        "target_state": {},
        "candidate_work": [
            {
                "id": "candidate-1",
                "kind": "manual_review_item",
                "locator": locator,
                "evidence": {"has_xrefs": True},
                "suggested_action_kinds": ["comment.edit"],
            }
        ],
        "safe_to_mutate": True,
    }
