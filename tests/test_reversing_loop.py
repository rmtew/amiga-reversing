from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

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
        _write_manual_log(tmp_path)
        return {"data": _executed_command_payload()}

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert calls == [
        ("GET", "/api/projects/demo/commands"),
        ("POST", "/api/projects/demo/commands/execute"),
    ]
    assert report["action_result"]["status"] == "executed"
    assert report["durable_result"]["mutation"]["durable_action_id"] == "manual-1"
    assert report["verification"]["status"] == "passed"


def test_run_one_report_includes_workflow_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _target(tmp_path)
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_locator())
    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: (
            {"data": {"commands": [{"command_id": "comment.edit"}]}}
            if method == "GET"
            else (_write_manual_log(tmp_path) or {"data": _executed_command_payload(workflow_profile={"workflow_id": "manual_command_execution", "spans": []})})
        ),
    )

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["workflow_profile"] == {"workflow_id": "manual_command_execution", "spans": []}


def test_run_one_verification_failure_names_layer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _target(tmp_path)
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_locator())
    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: (
            {"data": {"commands": [{"command_id": "comment.edit"}]}}
            if method == "GET"
            else {"data": _executed_command_payload()}
        ),
    )

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "failed"
    assert report["verification"]["layers"][0]["layer"] == "semantic_reload"
    assert report["next"]["recommendation"] == "stop"


def test_output_affecting_action_requires_round_trip_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    selected = {
        "work_item": _inspect_with_locator()["candidate_work"][0],
        "command": {
            "kind": "command",
            "command_id": "row.seed.code",
            "context": {"kind": "row", "locator": _inspect_with_locator()["candidate_work"][0]["locator"]},
            "parameters": {},
            "output_affecting": True,
        },
    }
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_locator())
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["action_result"]["status"] == "blocked"
    assert report["verification"]["layers"][0]["layer"] == "round_trip"
    assert report["next"]["recommendation"] == "stop"


def test_listing_backed_comment_acquires_locator_after_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_listing_row()]}}
        if path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_comment_iteration(
        "demo",
        mode="clean-run",
        dry_run=True,
        project_root=tmp_path,
    )

    assert calls == [
        ("POST", "/api/projects/demo/listing/open"),
        ("GET", "/api/projects/demo/listing"),
        ("GET", "/api/projects/demo/commands"),
    ]
    assert report["selected_work_item"]["kind"] == "listing_row"
    assert report["selected_work_item"]["locator"]["row_key"] == "row-1"
    assert report["action"]["command_id"] == "comment.edit"


def test_listing_backed_comment_checks_availability_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    calls: list[tuple[str, str]] = []
    listing_calls = 0

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        nonlocal listing_calls
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            listing_calls += 1
            return {"data": {"rows": [_listing_row(comment_text="agent listing comment: row-1") if listing_calls > 1 else _listing_row()]}}
        if path.endswith("/commands") and method == "GET":
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        if path.endswith("/commands/execute"):
            _write_manual_log(tmp_path)
            return {"data": _executed_listing_comment_payload(tmp_path)}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {"comments": [{"text": "agent listing comment: row-1"}]}}}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_comment_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert calls[:4] == [
        ("POST", "/api/projects/demo/listing/open"),
        ("GET", "/api/projects/demo/listing"),
        ("GET", "/api/projects/demo/commands"),
        ("POST", "/api/projects/demo/commands/execute"),
    ]
    assert report["verification"]["status"] == "passed"


def test_listing_backed_comment_verifies_projected_comment_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    listing_calls = 0

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        nonlocal listing_calls
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            listing_calls += 1
            text = "custom comment" if listing_calls > 1 else None
            return {"data": {"rows": [_listing_row(comment_text=text)]}}
        if path.endswith("/commands") and method == "GET":
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        if path.endswith("/commands/execute"):
            _write_manual_log(tmp_path)
            return {"data": _executed_listing_comment_payload(tmp_path)}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {"comments": [{"text": "custom comment"}]}}}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_comment_iteration(
        "demo",
        mode="clean-run",
        comment_text="custom comment",
        project_root=tmp_path,
    )

    projection = next(layer for layer in report["verification"]["layers"] if layer["layer"] == "projection")
    assert projection["status"] == "passed"
    assert projection["actual_comment_text"] == "custom comment"


def test_listing_backed_comment_stops_on_listing_readiness_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "queued"}}
        if path.endswith("/listing/status"):
            return {"data": {"job_id": "job-1", "status": "building"}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_comment_iteration(
        "demo",
        mode="clean-run",
        listing_timeout_seconds=0,
        project_root=tmp_path,
    )

    assert report["verification"]["status"] == "failed"
    assert report["verification"]["layers"][0]["layer"] == "listing_readiness"
    assert report["next"]["recommendation"] == "stop"
    assert calls == [("POST", "/api/projects/demo/listing/open")]


def test_listing_backed_comment_blocks_when_comment_edit_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_listing_row()]}}
        if path.endswith("/commands"):
            return {"data": {"commands": []}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_comment_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "failed"
    assert report["verification"]["layers"][0]["layer"] == "command_availability"
    assert not any(path.endswith("/commands/execute") for _, path in calls)


def test_continue_recommendation_when_verification_passes() -> None:
    recommendation = reversing_loop.recommend_next_step(
        inspect_report={"hygiene": {"unknown_files": []}},
        verification={"status": "passed", "layers": []},
        workflow_profile={"workflow_id": "manual_command_execution", "spans": []},
    )

    assert recommendation["recommendation"] == "continue"


def test_refactor_recommendation_requires_evidence() -> None:
    without_evidence = reversing_loop.recommend_next_step(
        inspect_report={"hygiene": {"unknown_files": []}},
        verification={"status": "passed", "layers": []},
    )
    with_evidence = reversing_loop.recommend_next_step(
        inspect_report={"hygiene": {"unknown_files": []}},
        verification={"status": "passed", "layers": []},
        evidence={"kind": "profile_span", "name": "locator_resolution"},
    )

    assert without_evidence["recommendation"] != "refactor"
    assert with_evidence["recommendation"] == "refactor"


def test_stop_recommendation_for_unknown_target_files() -> None:
    recommendation = reversing_loop.recommend_next_step(
        inspect_report={"hygiene": {"unknown_files": ["notes.json"]}},
        verification={"status": "passed", "layers": []},
    )

    assert recommendation["recommendation"] == "stop"


def test_profile_summary_shape() -> None:
    summary = reversing_loop.profile_summary(
        {
            "workflow_id": "manual_command_execution",
            "spans": [
                {"name": "small", "seconds": 0.1, "module": "server"},
                {"name": "large", "seconds": 1.2, "module": "listing_projection"},
            ],
        }
    )

    assert summary["workflow_id"] == "manual_command_execution"
    assert summary["top_spans"][0]["name"] == "large"


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
        "verification_paths": [{"kind": "round_trip", "available": False}],
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


def _write_manual_log(tmp_path: Path) -> None:
    path = tmp_path / "targets" / "demo" / "manual_actions.jsonl"
    path.write_text(
        '{"record": "manual_action_log_header"}\n{"record": "manual_action", "action_id": "manual-1"}\n',
        encoding="utf-8",
    )


def _executed_command_payload(workflow_profile: dict[str, object] | None = None) -> dict[str, object]:
    locator = _inspect_with_locator()["candidate_work"][0]["locator"]
    return {
        "action": {"action_id": "manual-1"},
        "mutation": {
            "durable_action_id": "manual-1",
            "manual_action_log_count": 1,
            "affected_locators": [locator],
        },
        "workflow_profile": workflow_profile
        or {"workflow_id": "manual_command_execution", "spans": [{"name": "manual_action_append"}]},
    }


def _listing_row(comment_text: str | None = None) -> dict[str, object]:
    row = {
        "row_key": "row-1",
        "kind": "instruction",
        "locator": _listing_locator(),
    }
    if comment_text is not None:
        row["comment_text"] = comment_text
    return row


def _listing_locator() -> dict[str, object]:
    return {
        "target_id": "demo",
        "projection_hash": "projection-1",
        "row_key": "row-1",
        "section_index": 0,
        "start_offset": 0,
        "end_offset": 2,
        "kind": "instruction",
    }


def _executed_listing_comment_payload(tmp_path: Path) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    return {
        "action": {"action_id": "manual-1"},
        "mutation": {
            "durable_action_id": "manual-1",
            "manual_action_log_count": state["count"],
            "manual_action_log_head_hash": state["head_hash"],
            "effective_metadata_hash": "f" * 64,
            "affected_locators": [_listing_locator()],
            "projection_hash": "projection-1",
        },
        "workflow_profile": {
            "workflow_id": "manual_command_execution",
            "spans": [{"name": "locator_resolution", "seconds": 0.01, "module": "listing_projection"}],
        },
    }
