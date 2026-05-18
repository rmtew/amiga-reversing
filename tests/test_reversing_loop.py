from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
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


def _project_with_manual_labels(labels: list[dict[str, object]]) -> ProjectRecord:
    return replace(_project(()), manual_state={"labels": labels})


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
    assert candidate["confidence"] == "high"
    assert candidate["default_verifier"] == "round_trip"


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
    assert report["action"]["parameters"] == {"text": "xref-backed test comment"}
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


def test_planner_ranks_source_converging_representation_before_comment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        inspect_report["candidate_work"][0],
        _representation_candidate(current_representation="hex"),
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "representation.character"
    assert report["selected_work_item"]["candidate_id"] == "repr-candidate"
    assert report["selected_work_item"]["expected_rendered_source_improvement"] == "render immediate 65 as #'A'"
    assert report["planner"]["selected_command_id"] == "representation.character"


def test_planner_skips_already_satisfied_projected_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        _representation_candidate(current_representation="character"),
        inspect_report["candidate_work"][0],
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "comment.edit"
    skipped = report["planner"]["skipped_candidates"]
    assert skipped[0]["candidate_id"] == "repr-candidate"
    assert skipped[0]["stop_reason"] == "candidate already satisfied in projected semantic state"


def test_planner_selects_data_symbol_rename_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        inspect_report["candidate_work"][0],
        _data_symbol_candidate(current_name="auto_data", new_name="player_table"),
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "data_symbol.rename"
    assert report["action"]["context"] == {"kind": "row", "locator": _listing_locator(kind="data")}
    assert report["action"]["parameters"] == {"name": "player_table"}
    assert report["planner"]["selected_command_id"] == "data_symbol.rename"


def test_planner_skips_already_satisfied_data_symbol_rename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        _data_symbol_candidate(current_name="player_table", new_name="player_table"),
        inspect_report["candidate_work"][0],
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "comment.edit"
    skipped = report["planner"]["skipped_candidates"]
    assert skipped[0]["candidate_id"] == "data-symbol-candidate"
    assert skipped[0]["stop_reason"] == "candidate already satisfied in projected semantic state"


def test_planner_selects_data_symbol_remove_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        inspect_report["candidate_work"][0],
        _data_symbol_remove_candidate(suppressed=False),
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "data_symbol.remove"
    assert report["action"]["context"] == {"kind": "row", "locator": _listing_locator(kind="data")}
    assert report["planner"]["selected_command_id"] == "data_symbol.remove"


def test_planner_selects_rsset_region_add_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        inspect_report["candidate_work"][0],
        _rsset_region_candidate(current_symbol="work_0004", new_symbol="work_flags"),
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "target.rsset_region.add"
    assert report["action"]["context"] == {"kind": "target"}
    assert report["action"]["parameters"]["symbol"] == "work_flags"
    assert report["planner"]["selected_command_id"] == "target.rsset_region.add"


def test_planner_selects_rsset_region_rename_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        inspect_report["candidate_work"][0],
        _rsset_region_candidate(
            current_symbol="work_0004",
            new_symbol="work_flags",
            action_kind="target.rsset_region.rename",
        ),
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "target.rsset_region.rename"
    assert report["action"]["context"] == {"kind": "target"}
    assert report["action"]["parameters"]["symbol"] == "work_flags"
    assert report["planner"]["selected_command_id"] == "target.rsset_region.rename"


def test_planner_skips_already_satisfied_rsset_region_add(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        _rsset_region_candidate(current_symbol="work_flags", new_symbol="work_flags"),
        inspect_report["candidate_work"][0],
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "comment.edit"
    skipped = report["planner"]["skipped_candidates"]
    assert skipped[0]["candidate_id"] == "rsset-region-candidate"
    assert skipped[0]["stop_reason"] == "candidate already satisfied in projected semantic state"


def test_planner_selects_rsset_region_remove_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        inspect_report["candidate_work"][0],
        _rsset_region_remove_candidate(removed=False),
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "target.rsset_region.remove"
    assert report["action"]["context"] == {"kind": "target"}
    assert report["action"]["parameters"] == {
        "offset": 4,
        "layout_name": "work",
        "base_symbol": "__game_work_base__",
    }
    assert report["planner"]["selected_command_id"] == "target.rsset_region.remove"


def test_planner_skips_already_satisfied_rsset_region_remove(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        _rsset_region_remove_candidate(removed=True),
        inspect_report["candidate_work"][0],
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "comment.edit"
    skipped = report["planner"]["skipped_candidates"]
    assert skipped[0]["candidate_id"] == "rsset-region-remove-candidate"
    assert skipped[0]["stop_reason"] == "candidate already satisfied in projected semantic state"


def test_planner_selects_review_seed_command_from_inspect_candidate(
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

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "review.seed.code"
    assert report["action"]["context"] == {
        "kind": "review_item",
        "item_id": "orphan:h0:$00000010-$00000012",
        "review_item_kind": ReviewItemKind.ORPHAN_CODE_CANDIDATE,
    }
    assert report["selected_work_item"]["durable_id"] == "orphan:h0:$00000010-$00000012"
    assert report["planner"]["selected_command_id"] == "review.seed.code"


def test_run_one_uses_listing_printable_immediate_candidate_when_inspect_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = []
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    row = _byte_immediate_row()
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_open_and_wait_listing", lambda target_id, timeout_seconds: {"status": "ready"})
    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {"data": {"rows": [row]}},
    )

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "representation.character"
    assert report["action"]["parameters"] == {"representation": "character"}
    assert report["selected_work_item"]["expected_rendered_source_improvement"] == "render byte immediate 48 as #'0'"
    assert report["planner"]["selected_command_id"] == "representation.character"


def test_run_one_uses_listing_rsset_suggestion_when_inspect_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = []
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_open_and_wait_listing", lambda target_id, timeout_seconds: {"status": "ready"})

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if path.endswith("/listing/navigation"):
            return {"data": _rsset_suggestion_navigation_payload()}
        if path.endswith("/listing"):
            return {"data": {"rows": []}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "target.rsset_region.add"
    assert report["action"]["context"] == {"kind": "target"}
    assert report["action"]["parameters"]["symbol"] == "app_input_event"
    assert report["planner"]["selected_command_id"] == "target.rsset_region.add"


def test_listing_representation_candidates_skip_non_byte_immediates() -> None:
    byte_candidates = reversing_loop._listing_representation_candidates([_byte_immediate_row()])
    long_candidates = reversing_loop._listing_representation_candidates(
        [_byte_immediate_row(opcode="moveq.l", width_bits=32)]
    )

    assert byte_candidates[0]["element_id"] == "row-1:immediate:0:48"
    assert long_candidates == []


def test_listing_rsset_region_candidates_use_navigation_suggestions() -> None:
    candidates = reversing_loop._listing_rsset_region_candidates(_rsset_suggestion_navigation_payload())

    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "rsset-suggestion:app:__amiga_app_base__:0100:app_input_event"
    assert candidates[0]["suggested_action_kinds"] == ["target.rsset_region.add"]
    assert candidates[0]["parameters"] == {
        "offset": 0x100,
        "size": 22,
        "symbol": "app_input_event",
        "struct_name": "InputEvent",
        "storage_kind": "struct_instance",
        "parser_role": "input_event",
        "parser_routine": "parse_input_event",
        "parse_order": 1,
    }
    assert candidates[0]["default_verifier"] == "round_trip"


def test_listing_rsset_region_candidates_skip_already_projected_suggestion() -> None:
    navigation = _rsset_suggestion_navigation_payload()
    existing = {
        ("app", "__amiga_app_base__", 0x100): {
            "offset": 0x100,
            "size": 22,
            "symbol": "app_input_event",
            "struct_name": "InputEvent",
            "storage_kind": "struct_instance",
            "parser_role": "input_event",
            "parser_routine": "parse_input_event",
            "parse_order": 1,
        }
    }

    candidates = reversing_loop._listing_rsset_region_candidates(navigation, existing_regions=existing)
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = [candidates[0]]
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]

    assert candidates[0]["suggested_action_kinds"] == ["target.rsset_region.edit"]
    assert reversing_loop._select_command_action(inspect_report) is None
    assert inspect_report["planner"]["skipped_candidates"][0]["stop_reason"] == (
        "candidate already satisfied in projected semantic state"
    )


def test_representation_command_requires_round_trip_verifier_even_without_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    selected = {
        "work_item": {"kind": "literal_representation", "confidence": "high"},
        "command": _representation_command(output_affecting=False),
    }
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_representation(round_trip=False))
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["action_result"]["status"] == "blocked"
    assert report["verification"]["layers"][0]["layer"] == "round_trip"


def test_representation_command_verifies_source_projection_and_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    selected = {
        "work_item": {"kind": "literal_representation", "confidence": "high"},
        "command": _representation_command(),
    }
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/commands") and method == "GET":
            return {"data": {"commands": [{"command_id": "representation.character"}]}}
        if path.endswith("/commands/execute"):
            _write_manual_log(tmp_path)
            return {"data": _executed_representation_payload(tmp_path)}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {"representations": [_representation_payload()]}}}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(text="\tmove.b #'A',d0\n", end_offset=4)]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_representation())
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)
    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert ("POST", "/api/projects/demo/commands/execute") in calls
    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "projection",
        "round_trip",
    ]


def test_representation_command_fails_when_rendered_text_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    selected = {
        "work_item": {"kind": "literal_representation", "confidence": "high"},
        "command": _representation_command(),
    }

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/commands") and method == "GET":
            return {"data": {"commands": [{"command_id": "representation.character"}]}}
        if path.endswith("/commands/execute"):
            _write_manual_log(tmp_path)
            return {"data": _executed_representation_payload(tmp_path)}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {"representations": [_representation_payload()]}}}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(text="\tmove.b #65,d0\n", end_offset=4)]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_representation())
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)
    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "failed"
    projection = next(layer for layer in report["verification"]["layers"] if layer["layer"] == "projection")
    assert projection["status"] == "failed"
    assert projection["expected_tokens"] == ["#'A'"]
    assert report["next"]["recommendation"] == "stop"


def test_listing_backed_comment_acquires_locator_after_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path)
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
    assert report["selected_work_item"]["kind"] == "source_entrypoint_row"
    assert report["selected_work_item"]["locator"]["row_key"] == "row-1"
    assert report["action"]["command_id"] == "comment.edit"
    assert report["action"]["parameters"] == {}
    assert report["selected_work_item"]["confidence"] == "high"
    assert report["selected_work_item"]["default_verifier"] == "projected_comment_text"


def test_listing_backed_comment_discovers_entrypoint_candidate(
    tmp_path: Path,
) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path, entrypoint=2)

    candidates = reversing_loop._listing_comment_candidates(
        "demo",
        [_listing_row(row_key="row-0", start_offset=0, end_offset=2), _listing_row(row_key="row-2", start_offset=2, end_offset=4)],
        project_root=tmp_path,
    )

    assert [candidate["candidate_id"] for candidate in candidates] == ["source-entrypoint:row-2"]
    assert candidates[0]["rationale"] == "source descriptor entrypoint maps to this listing row"
    assert candidates[0]["evidence"]["entrypoint"] == 2


def test_listing_backed_comment_discovers_hunk_file_entrypoint_candidate(
    tmp_path: Path,
) -> None:
    _target(tmp_path)
    _write_hunk_source(tmp_path)

    candidates = reversing_loop._listing_comment_candidates(
        "demo",
        [
            _listing_row(row_key="global", kind="directive", start_offset=None, end_offset=None),
            _listing_row(row_key="entry", kind="label", start_offset=0, end_offset=0),
        ],
        project_root=tmp_path,
    )

    assert [candidate["candidate_id"] for candidate in candidates] == ["source-entrypoint:entry"]
    assert candidates[0]["evidence"]["evidence_kind"] == "hunk_load_entrypoint"
    assert candidates[0]["suggested_comment_text"] == "Hunk file entrypoint."


def test_listing_backed_comment_does_not_use_first_commentable_row_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path, entrypoint=2)
    queried_rows: list[str] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(row_key="row-0", start_offset=0, end_offset=2),
                        _listing_row(row_key="row-2", start_offset=2, end_offset=4),
                    ]
                }
            }
        if path.endswith("/commands"):
            locator = json.loads(query["locator"][0])
            queried_rows.append(locator["row_key"])
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_comment_iteration(
        "demo",
        mode="clean-run",
        dry_run=True,
        project_root=tmp_path,
    )

    assert queried_rows == ["row-2"]
    assert report["selected_work_item"]["locator"]["row_key"] == "row-2"


def test_listing_backed_comment_selects_hunk_entrypoint_beyond_header_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_hunk_source(tmp_path)
    listing_queries: list[dict[str, list[str]]] = []
    rows = [
        _listing_row(row_key=f"global-{index}", kind="directive", start_offset=None, end_offset=None)
        for index in range(120)
    ]
    rows.append(_listing_row(row_key="entry", kind="label", start_offset=0, end_offset=0))

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            listing_queries.append(query)
            return {"data": {"rows": rows}}
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

    assert listing_queries == [{"start": ["0"], "count": [str(reversing_loop._LISTING_COMMENT_SEARCH_ROW_COUNT)]}]
    assert report["selected_work_item"]["locator"]["row_key"] == "entry"
    assert report["action"]["parameters"] == {"text": "Hunk file entrypoint."}


def test_listing_backed_comment_stops_when_no_evidence_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path, entrypoint=8)
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(row_key="row-0", start_offset=0, end_offset=2)]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_comment_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["layers"][0]["layer"] == "candidate_selection"
    assert report["next"]["recommendation"] == "stop"
    assert report["candidate_work"] == []
    assert not any(path.endswith("/commands/execute") for _, path in calls)


def test_listing_backed_comment_checks_availability_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path)
    calls: list[tuple[str, str]] = []
    listing_calls = 0

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        nonlocal listing_calls
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            listing_calls += 1
            return {"data": {"rows": [_listing_row(comment_text="entrypoint returns") if listing_calls > 1 else _listing_row()]}}
        if path.endswith("/commands") and method == "GET":
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        if path.endswith("/commands/execute"):
            _write_manual_log(tmp_path)
            return {"data": _executed_listing_comment_payload(tmp_path)}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {"comments": [{"text": "entrypoint returns"}]}}}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_comment_iteration(
        "demo",
        mode="clean-run",
        comment_text="entrypoint returns",
        project_root=tmp_path,
    )

    assert calls[:4] == [
        ("POST", "/api/projects/demo/listing/open"),
        ("GET", "/api/projects/demo/listing"),
        ("GET", "/api/projects/demo/commands"),
        ("POST", "/api/projects/demo/commands/execute"),
    ]
    assert report["verification"]["status"] == "passed"


def test_listing_backed_comment_blocks_execution_without_comment_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path)
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_listing_row()]}}
        if path.endswith("/commands") and method == "GET":
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_comment_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["action_result"]["status"] == "blocked"
    assert report["verification"]["layers"][0]["layer"] == "comment_text"
    assert report["next"]["recommendation"] == "stop"
    assert not any(path.endswith("/commands/execute") for _, path in calls)


def test_listing_backed_comment_verifies_projected_comment_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path)
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
    _write_raw_source(tmp_path)
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
    _write_raw_source(tmp_path)
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


def test_listing_backed_label_rename_dry_run_selects_label_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(row_key="label-row", kind="label", label="loc_0_00001000", start_offset=0x1000, end_offset=0x1000)]}}
        if path.endswith("/commands"):
            assert query["context"] == ["element"]
            return {"data": {"commands": [{"command_id": "label.rename"}]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_label_rename_iteration(
        "demo",
        mode="clean-run",
        dry_run=True,
        source_offset=0x1000,
        new_label="open_output_file",
        rationale="sets MODE_NEWFILE and stores the returned handle",
        evidence_lines=("calls DOS Open",),
        project_root=tmp_path,
    )

    assert calls == [
        ("POST", "/api/projects/demo/listing/open"),
        ("GET", "/api/projects/demo/listing"),
        ("GET", "/api/projects/demo/commands"),
    ]
    assert report["selected_work_item"]["kind"] == "listing_label_rename"
    assert report["action"]["command_id"] == "label.rename"
    assert report["action"]["context"]["kind"] == "element"
    assert report["action"]["parameters"] == {"name": "open_output_file"}
    assert report["action_result"]["status"] == "dry_run"


def test_listing_backed_label_rename_executes_and_verifies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    calls: list[tuple[str, str]] = []
    listing_calls = 0
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: _project_with_manual_labels([{"name": "open_output_file", "addr": 0x1000}]),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        nonlocal listing_calls
        calls.append((method, path))
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing"):
            listing_calls += 1
            label = "open_output_file" if listing_calls > 1 else "loc_0_00001000"
            return {"data": {"rows": [_listing_row(row_key="label-row", kind="label", label=label, start_offset=0x1000, end_offset=0x1000)]}}
        if path.endswith("/commands") and method == "GET":
            return {"data": {"commands": [{"command_id": "label.rename"}]}}
        if path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "label.rename"
            _write_manual_log(tmp_path)
            return {"data": _executed_listing_label_payload(tmp_path)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_listing_backed_label_rename_iteration(
        "demo",
        mode="clean-run",
        source_offset=0x1000,
        new_label="open_output_file",
        rationale="sets MODE_NEWFILE and stores the returned handle",
        evidence_lines=("calls DOS Open",),
        project_root=tmp_path,
    )

    assert ("POST", "/api/projects/demo/commands/execute") in calls
    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "projection",
        "round_trip",
    ]
    assert report["next"]["recommendation"] == "continue"


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
                "confidence": "high",
                "actionable": True,
                "default_verifier": "projection_metadata",
                "verifier": {"kind": "projection_metadata", "requires_semantic_reload": True},
                "rationale": "test xref-backed candidate",
                "suggested_action_kinds": ["comment.edit"],
                "suggested_comment_text": "xref-backed test comment",
            }
        ],
        "safe_to_mutate": True,
    }


def _inspect_with_representation(*, round_trip: bool = True) -> dict[str, object]:
    report = _inspect_with_locator()
    report["verification_paths"] = [{"kind": "round_trip", "available": round_trip}]
    report["candidate_work"] = [{"kind": "literal_representation", "confidence": "high"}]
    return report


def _representation_command(*, output_affecting: bool = True) -> dict[str, object]:
    command = {
        "kind": "command",
        "command_id": "representation.character",
        "context": {
            "kind": "element",
            "locator": _listing_locator(end_offset=4),
            "element_id": "row-1:immediate:0:65",
            "element_kind": "immediate",
            "operand_index": 0,
            "value": 65,
            "width_bits": 8,
            "width_bytes": 1,
        },
        "parameters": {"representation": "character"},
    }
    if output_affecting:
        command["output_affecting"] = True
    return command


def _representation_candidate(*, current_representation: str) -> dict[str, object]:
    return {
        "id": "repr-candidate",
        "candidate_id": "repr-candidate",
        "kind": "literal_representation",
        "locator": _listing_locator(end_offset=4),
        "element_id": "row-1:immediate:0:65",
        "element_kind": "immediate",
        "operand_index": 0,
        "value": 65,
        "width_bits": 8,
        "width_bytes": 1,
        "evidence": {"source": "listing", "value": 65},
        "current_metadata": {"representation": current_representation},
        "expected_rendered_source_improvement": "render immediate 65 as #'A'",
        "suggested_action_kinds": ["representation.character"],
        "default_verifier": "projected_representation_text",
        "verifier": {"kind": "projected_representation_text", "requires_semantic_reload": True},
        "confidence": "high",
        "actionable": True,
    }


def _data_symbol_candidate(*, current_name: str, new_name: str) -> dict[str, object]:
    return {
        "id": "data-symbol-candidate",
        "candidate_id": "data-symbol-candidate",
        "kind": "data_symbol_name",
        "locator": _listing_locator(kind="data"),
        "evidence": {"source": "listing", "previous_name": current_name},
        "current_metadata": {"name": current_name},
        "expected_rendered_source_improvement": f"rename data symbol {current_name} to {new_name}",
        "suggested_action_kinds": ["data_symbol.rename"],
        "new_name": new_name,
        "default_verifier": "round_trip",
        "verifier": {"kind": "round_trip", "requires_semantic_reload": True},
        "confidence": "high",
        "actionable": True,
    }


def _data_symbol_remove_candidate(*, suppressed: bool) -> dict[str, object]:
    return {
        "id": "data-symbol-remove-candidate",
        "candidate_id": "data-symbol-remove-candidate",
        "kind": "data_symbol_remove",
        "locator": _listing_locator(kind="data"),
        "evidence": {"source": "listing", "name": "wrong_data"},
        "current_metadata": {"name": "wrong_data", "suppressed": suppressed},
        "expected_rendered_source_improvement": "remove wrong seeded data symbol wrong_data",
        "suggested_action_kinds": ["data_symbol.remove"],
        "default_verifier": "round_trip",
        "verifier": {"kind": "round_trip", "requires_semantic_reload": True},
        "confidence": "high",
        "actionable": True,
    }


def _rsset_region_candidate(
    *,
    current_symbol: str,
    new_symbol: str,
    action_kind: str = "target.rsset_region.add",
) -> dict[str, object]:
    parameters = {
        "offset": 4,
        "size": 2,
        "layout_name": "work",
        "base_symbol": "__game_work_base__",
        "sizeof_symbol": "work_SIZEOF",
        "symbol": new_symbol,
        "storage_kind": "scalar",
    }
    return {
        "id": "rsset-region-candidate",
        "candidate_id": "rsset-region-candidate",
        "kind": "rsset_layout_region",
        "evidence": {"source": "app_slot_analysis", "previous_symbol": current_symbol},
        "current_metadata": {**parameters, "symbol": current_symbol},
        "expected_rendered_source_improvement": f"rename RSSET region field {current_symbol} to {new_symbol}",
        "suggested_action_kinds": [action_kind],
        "parameters": parameters,
        "default_verifier": "round_trip",
        "verifier": {"kind": "round_trip", "requires_semantic_reload": True},
        "confidence": "high",
        "actionable": True,
    }


def _rsset_region_remove_candidate(*, removed: bool) -> dict[str, object]:
    return {
        "id": "rsset-region-remove-candidate",
        "candidate_id": "rsset-region-remove-candidate",
        "kind": "rsset_layout_region_remove",
        "evidence": {"source": "app_slot_analysis", "symbol": "wrong_flags"},
        "current_metadata": {"symbol": "wrong_flags", "removed": removed},
        "expected_rendered_source_improvement": "remove wrong RSSET region field wrong_flags",
        "suggested_action_kinds": ["target.rsset_region.remove"],
        "parameters": {"offset": 4, "layout_name": "work", "base_symbol": "__game_work_base__"},
        "default_verifier": "round_trip",
        "verifier": {"kind": "round_trip", "requires_semantic_reload": True},
        "confidence": "high",
        "actionable": True,
    }


def _write_manual_log(tmp_path: Path) -> None:
    path = tmp_path / "targets" / "demo" / "manual_actions.jsonl"
    path.write_text(
        '{"record": "manual_action_log_header"}\n{"record": "manual_action", "action_id": "manual-1"}\n',
        encoding="utf-8",
    )


def _representation_payload() -> dict[str, object]:
    return {
        "representation_id": "repr-1",
        "hunk": 0,
        "addr": 0,
        "end": 4,
        "style": "character",
        "element_kind": "immediate",
        "operand_index": 0,
    }


def _executed_representation_payload(tmp_path: Path) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    return {
        "action": {"action_id": "manual-1", "representation": _representation_payload()},
        "mutation": {
            "durable_action_id": "manual-1",
            "manual_action_log_count": state["count"],
            "manual_action_log_head_hash": state["head_hash"],
            "effective_metadata_hash": "f" * 64,
            "affected_locators": [_listing_locator(end_offset=4)],
            "projection_hash": "projection-1",
        },
        "workflow_profile": {"workflow_id": "manual_command_execution", "spans": []},
    }


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


def _listing_row(
    comment_text: str | None = None,
    *,
    row_key: str = "row-1",
    kind: str = "instruction",
    label: str | None = None,
    text: str | None = None,
    start_offset: int | None = 0,
    end_offset: int | None = 2,
) -> dict[str, object]:
    row = {
        "row_key": row_key,
        "kind": kind,
        "addr": start_offset,
        "locator": _listing_locator(row_key=row_key, kind=kind, start_offset=start_offset, end_offset=end_offset),
    }
    if label is not None:
        row["label"] = label
        row["text"] = f"{label}:\n"
    if text is not None:
        row["text"] = text
    if comment_text is not None:
        row["comment_text"] = comment_text
    return row


def _byte_immediate_row(*, opcode: str = "subi.b", width_bits: int = 8) -> dict[str, object]:
    row = _listing_row(text=f"\t{opcode} #48,d1\n", end_offset=2)
    row.update(
        {
            "opcode_or_directive": opcode,
            "operand_text": "#48,d1",
            "operand_parts": [
                {
                    "kind": "immediate",
                    "operand_index": 0,
                    "value": 48,
                    "signed_value": 48,
                    "width_bits": width_bits,
                    "width_bytes": width_bits // 8,
                    "metadata": {},
                }
            ],
            "operand_accesses": ["immediate", "register_write"],
            "operand_registers": [None, "D1"],
        }
    )
    return row


def _rsset_suggestion_navigation_payload() -> dict[str, object]:
    return {
        "groups": {
            "app-slot-suggestions": [
                {
                    "summary": "app_input_event at app+0x100 matches InputEvent from platform API usage",
                    "action": "add_target_metadata",
                    "confidence": "tool-inferred",
                    "symbol": "app_input_event",
                    "offset": 0x100,
                    "row_index": 1,
                    "stable_key": "call-row",
                    "metadata": {
                        "symbol": "app_input_event",
                        "offset": 0x100,
                        "size": 22,
                        "struct_name": "InputEvent",
                        "storage_kind": "struct_instance",
                        "parser_role": "input_event",
                        "parser_routine": "parse_input_event",
                        "parse_order": 1,
                    },
                }
            ]
        }
    }


def _listing_locator(
    *,
    row_key: str = "row-1",
    kind: str = "instruction",
    start_offset: int | None = 0,
    end_offset: int | None = 2,
) -> dict[str, object]:
    return {
        "target_id": "demo",
        "projection_hash": "projection-1",
        "row_key": row_key,
        "section_index": 0,
        "start_offset": start_offset,
        "end_offset": end_offset,
        "kind": kind,
    }


def _write_raw_source(tmp_path: Path, *, entrypoint: int = 0) -> None:
    binary_path = tmp_path / "bin" / "demo.bin"
    binary_path.parent.mkdir(exist_ok=True)
    binary_path.write_bytes(b"\x4e\x75\x4e\x75\x4e\x75\x4e\x75\x4e\x75")
    (tmp_path / "targets" / "demo" / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "path": str(binary_path),
                "address_model": "local_offset",
                "load_address": 0,
                "entrypoint": entrypoint,
                "code_start_offset": 0,
            }
        ),
        encoding="utf-8",
    )


def _write_hunk_source(tmp_path: Path) -> None:
    binary_path = tmp_path / "bin" / "demo"
    binary_path.parent.mkdir(exist_ok=True)
    binary_path.write_bytes(b"\x00\x00\x03\xf3")
    (tmp_path / "targets" / "demo" / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "hunk_file",
                "path": str(binary_path),
            }
        ),
        encoding="utf-8",
    )


def _write_reproduction_exact(tmp_path: Path) -> None:
    (tmp_path / "targets" / "demo" / "reproduction.json").write_text(
        json.dumps({"status": "exact"}),
        encoding="utf-8",
    )


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


def _executed_listing_label_payload(tmp_path: Path) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    return {
        "action": {"action_id": "manual-1"},
        "mutation": {
            "durable_action_id": "manual-1",
            "manual_action_log_count": state["count"],
            "manual_action_log_head_hash": state["head_hash"],
            "effective_metadata_hash": "f" * 64,
            "affected_locators": [_listing_locator(row_key="label-row", kind="label", start_offset=0x1000, end_offset=0x1000)],
            "projection_hash": "projection-1",
        },
        "workflow_profile": {
            "workflow_id": "manual_command_execution",
            "spans": [{"name": "locator_resolution", "seconds": 0.01, "module": "listing_projection"}],
        },
    }
