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
from amiga_reversing.disasm.target_metadata import (
    EntryRegisterSeedKind,
    EntryRegisterSeedMetadata,
    RssetLayoutRegionMetadata,
    RssetLayoutStorageKind,
    SeededCodeLabelMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    write_target_metadata,
)


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
    assert candidate["default_verifier"] == "manual_seed_state"


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
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            _write_manual_log(tmp_path)
            return {"data": _executed_listing_comment_payload(tmp_path)}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {}}}}
        if method == "GET" and path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(comment_text="xref-backed test comment")]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert calls == [
        ("GET", "/api/projects/demo/commands"),
        ("POST", "/api/projects/demo/commands/execute"),
        ("GET", "/api/projects/demo"),
        ("GET", "/api/projects/demo/listing"),
    ]
    assert report["action_result"]["status"] == "executed"
    assert report["durable_result"]["mutation"]["durable_action_id"] == "manual-1"
    assert report["verification"]["status"] == "passed"


def test_run_one_report_includes_workflow_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _target(tmp_path)
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_locator())

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            _write_manual_log(tmp_path)
            payload = _executed_listing_comment_payload(tmp_path)
            payload["workflow_profile"] = {"workflow_id": "manual_command_execution", "spans": []}
            return {"data": payload}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {}}}}
        if method == "GET" and path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(comment_text="xref-backed test comment")]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

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
    assert report["verification"]["layers"][0]["layer"] == "manual_action_log"
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


def test_output_affecting_action_runs_round_trip_layer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_dir = _target(tmp_path)
    (target_dir / "reproduction.json").write_text('{"status": "mismatch"}', encoding="utf-8")
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    selected = {
        "work_item": inspect_report["candidate_work"][0],
        "command": {
            "kind": "command",
            "command_id": "target.equate.add",
            "context": {"kind": "target"},
            "parameters": {"name": "PLAYER_START_LIVES", "value": 3},
            "output_affecting": True,
        },
    }
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"target_equates": [{"name": "PLAYER_START_LIVES", "value": 3}]},
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET":
            return {"data": {"commands": [{"command_id": "target.equate.add"}]}}
        _write_manual_log(tmp_path)
        return {"data": _executed_target_equate_payload(tmp_path, {"name": "PLAYER_START_LIVES", "value": 3})}

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "failed"
    assert report["verification"]["layers"][-1]["layer"] == "round_trip"
    assert report["verification"]["layers"][-1]["round_trip"]["status"] == "mismatch"


@pytest.mark.parametrize(
    ("command_id", "context", "parameters"),
    [
        (
            "target.custom_struct.add",
            {"kind": "target"},
            {"name": "InputEvent", "size": 22},
        ),
        (
            "target.custom_struct_field.add",
            {"kind": "target"},
            {"struct_name": "InputEvent", "name": "ie_Class", "type": "UBYTE", "offset": 4, "size": 1},
        ),
        (
            "typed_gap.field.add",
            {
                "kind": "element",
                "element_id": "row-1:typed_gap:0:prefix_extension",
                "element_kind": "typed_gap",
            },
            {"name": "de_Code", "type": "UWORD", "size": 2},
        ),
        (
            "typed_access.field.rename",
            {
                "kind": "element",
                "element_id": "row-1:typed_access:0:LIB_VERSION",
                "element_kind": "typed_access",
            },
            {"name": "LIB_REVISION"},
        ),
    ],
)
def test_unproven_custom_struct_and_typed_field_commands_block_without_specific_verifier(
    command_id: str,
    context: dict[str, object],
    parameters: dict[str, object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_dir = _target(tmp_path)
    (target_dir / "reproduction.json").write_text('{"status": "exact"}', encoding="utf-8")
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    selected = {
        "work_item": inspect_report["candidate_work"][0],
        "command": {
            "kind": "command",
            "command_id": command_id,
            "context": context,
            "parameters": parameters,
            "output_affecting": True,
        },
    }
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        raise AssertionError("unsupported custom struct or typed field command should not execute")

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["action_result"]["status"] == "blocked"
    assert report["verification"]["status"] == "failed"
    assert report["verification"]["layers"][0]["layer"] == "verifier"
    assert report["verification"]["layers"][0]["command_id"] == command_id


def test_run_one_manual_seed_executes_with_seed_state_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    selected = {
        "work_item": inspect_report["candidate_work"][0],
        "command": {
            "kind": "command",
            "command_id": "row.seed.data.string",
            "context": {"kind": "row", "locator": inspect_report["candidate_work"][0]["locator"]},
            "parameters": {"seed_kind": "data", "data_role": "string", "unit": "byte", "encoding": "ascii"},
            "output_affecting": True,
        },
    }
    seed = {
        "seed_id": "catalog-seed-1",
        "kind": "data",
        "mode": "required",
        "hunk": 0,
        "addr": 0,
        "end": 4,
        "data_role": "string",
        "unit": "byte",
        "encoding": "ascii",
    }
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"seeds": [seed]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "row.seed.data.string"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "row.seed.data.string"
            _write_manual_log(tmp_path)
            return {"data": _executed_manual_seed_payload(tmp_path, seed)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["verification"]["layers"][1]["matching_manual_seeds"] == [seed]
    assert report["action"]["command_id"] == "row.seed.data.string"


def test_run_one_range_seed_checks_range_catalog_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locators = [
        _listing_locator(row_key="row-1", kind="data", start_offset=0x20, end_offset=0x22),
        _listing_locator(row_key="row-2", kind="data", start_offset=0x22, end_offset=0x24),
    ]
    candidate = {
        "id": "range-string",
        "candidate_id": "range-string",
        "kind": "range_data_seed",
        "locators": locators,
        "suggested_action_kinds": ["range.seed.data.string"],
        "parameters": {"seed_kind": "data", "data_role": "string", "unit": "byte", "encoding": "ascii"},
        "confidence": "high",
        "actionable": True,
    }
    seed = {
        "seed_id": "catalog-range-seed-1",
        "kind": "data",
        "mode": "required",
        "hunk": 0,
        "addr": 0x20,
        "end": 0x24,
        "data_role": "string",
        "unit": "byte",
        "encoding": "ascii",
    }
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = [candidate]
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"seeds": [seed]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            assert query == {"context": ["range"], "locators": [json.dumps(locators)]}
            return {"data": {"commands": [{"command_id": "range.seed.data.string"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "range.seed.data.string"
            assert body["context"] == {"kind": "range", "locators": locators}
            _write_manual_log(tmp_path)
            return {"data": _executed_manual_seed_payload(tmp_path, seed)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["action"]["command_id"] == "range.seed.data.string"
    assert report["action"]["context"] == {"kind": "range", "locators": locators}


def test_run_one_rsset_region_executes_with_rsset_state_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [_rsset_region_candidate(current_symbol="work_0004", new_symbol="work_flags")]
    expected = cast(dict[str, object], inspect_report["candidate_work"][0]["parameters"])
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"rsset_layout_regions": [expected]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "target.rsset_region.add"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "target.rsset_region.add"
            _write_manual_log(tmp_path)
            return {"data": _executed_rsset_region_payload(tmp_path, expected)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["verification"]["layers"][1]["state_key"] == "rsset_layout_regions"
    assert report["action"]["command_id"] == "target.rsset_region.add"


def test_run_one_rsset_region_remove_executes_with_removed_region_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [_rsset_region_remove_candidate(removed=False)]
    expected = cast(dict[str, object], inspect_report["candidate_work"][0]["parameters"])
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"removed_rsset_layout_regions": [expected]},
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "target.rsset_region.remove"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "target.rsset_region.remove"
            _write_manual_log(tmp_path)
            return {"data": _executed_rsset_region_payload(tmp_path, expected, removed=True)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["verification"]["layers"][1]["state_key"] == "removed_rsset_layout_regions"
    assert report["action"]["command_id"] == "target.rsset_region.remove"


def test_run_one_target_equate_executes_with_equate_state_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        {
            "id": "target-equate",
            "candidate_id": "target-equate",
            "kind": "target_equate",
            "suggested_action_kinds": ["target.equate.add"],
            "parameters": {"name": "PLAYER_START_LIVES", "value": 3},
            "confidence": "high",
            "actionable": True,
        }
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"target_equates": [{"name": "PLAYER_START_LIVES", "value": 3}]},
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "target.equate.add"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "target.equate.add"
            _write_manual_log(tmp_path)
            return {"data": _executed_target_equate_payload(tmp_path, {"name": "PLAYER_START_LIVES", "value": 3})}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["verification"]["layers"][1]["state_key"] == "target_equates"
    assert report["action"]["command_id"] == "target.equate.add"


def test_run_one_target_equate_remove_executes_with_removed_equate_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        {
            "id": "target-equate-remove",
            "candidate_id": "target-equate-remove",
            "kind": "target_equate",
            "suggested_action_kinds": ["target.equate.remove"],
            "parameters": {"name": "PLAYER_START_LIVES"},
            "confidence": "high",
            "actionable": True,
        }
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"removed_target_equates": [{"name": "PLAYER_START_LIVES"}]},
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "target.equate.remove"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "target.equate.remove"
            _write_manual_log(tmp_path)
            return {
                "data": _executed_target_equate_payload(
                    tmp_path,
                    {"name": "PLAYER_START_LIVES"},
                    removed=True,
                )
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["verification"]["layers"][1]["state_key"] == "removed_target_equates"
    assert report["action"]["command_id"] == "target.equate.remove"


def test_target_equate_rename_verifier_checks_renamed_equate_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "renamed_target_equates": [
                    {"previous_name": "PLAYER_START_LIVES", "name": "PLAYER_INITIAL_LIVES"}
                ]
            },
        ),
    )

    verification = reversing_loop._verify_target_equate_mutation(
        "demo",
        "target.equate.rename",
        _executed_target_equate_payload(
            tmp_path,
            {"previous_name": "PLAYER_START_LIVES", "name": "PLAYER_INITIAL_LIVES"},
        ),
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["layers"][1]["state_key"] == "renamed_target_equates"


def test_target_equate_verifier_requires_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"target_equates": [{"name": "PLAYER_START_LIVES", "value": 3}]},
        ),
    )
    durable_result = _executed_command_payload()
    durable_result["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    durable_result["application"] = {
        "status": "applied",
        "local_effects": [{"kind": "target_equate", "target_equate": {"name": "PLAYER_START_LIVES", "value": 3}}],
    }

    verification = reversing_loop._verify_target_equate_mutation(
        "demo",
        "target.equate.add",
        durable_result,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "missing target equate payload"


def test_rsset_region_verifier_requires_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    region = {"offset": 4, "layout_name": "work", "base_symbol": "__game_work_base__", "symbol": "work_flags"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"rsset_layout_regions": [region]},
        ),
    )
    durable_result = _executed_command_payload()
    durable_result["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    durable_result["application"] = {
        "status": "applied",
        "local_effects": [{"kind": "rsset_layout_region", "rsset_layout_region": region}],
    }

    verification = reversing_loop._verify_rsset_region_mutation(
        "demo",
        "app_slot.rename",
        durable_result,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "missing RSSET layout region payload"


def test_manual_seed_verifier_requires_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    seed = {"seed_id": "catalog-seed-1", "kind": "data", "mode": "required", "hunk": 0, "addr": 0}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"seeds": [seed]}),
    )
    durable_result = _executed_command_payload()
    durable_result["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]

    verification = reversing_loop._verify_manual_seed_mutation(
        "demo",
        "row.seed.data.raw",
        durable_result,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "missing manual seed payload"


def test_manual_seed_remove_verifier_checks_removed_seed_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"seeds": []}),
    )

    verification = reversing_loop._verify_manual_seed_mutation(
        "demo",
        "review.seed.remove",
        _executed_manual_seed_remove_payload(tmp_path, "data-as-code"),
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["layers"][1]["removed_seed_ids"] == ["data-as-code"]


def test_manual_seed_verifier_rejects_mismatched_payload_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "seeds": [
                    {
                        "seed_id": "catalog-seed-1",
                        "kind": "data",
                        "mode": "required",
                        "hunk": 0,
                        "addr": 0,
                        "end": 4,
                        "row_indexes": [1, 2],
                    }
                ]
            },
        ),
    )

    verification = reversing_loop._verify_manual_seed_mutation(
        "demo",
        "range.seed.data.raw",
        _executed_manual_seed_payload(
            tmp_path,
            {
                "seed_id": "catalog-seed-1",
                "kind": "data",
                "mode": "required",
                "hunk": 0,
                "addr": 0,
                "end": 4,
                "row_indexes": [1],
            },
        ),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["matching_manual_seeds"] == []


def test_manual_label_rename_verifier_checks_label_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    label = {"label_id": "manual-label-1", "name": "renamed_label", "scope": "global"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"labels": [label]}),
    )

    verification = reversing_loop._verify_manual_label_mutation(
        "demo",
        "review.label.rename",
        _executed_manual_label_payload(tmp_path, {"label_id": "manual-label-1", "name": "renamed_label"}),
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["layers"][1]["matching_manual_labels"] == [
        {"label_id": "manual-label-1", "name": "renamed_label"}
    ]


def test_manual_label_scope_verifier_checks_owner_alias(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    label = {"label_id": "manual-label-1", "name": "local_name", "scope": "local", "owner_id": "owner-label"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"labels": [label]}),
    )

    verification = reversing_loop._verify_manual_label_mutation(
        "demo",
        "review.label.change_scope",
        _executed_manual_label_payload(
            tmp_path,
            {"label_id": "manual-label-1", "scope": "local", "owner_label_id": "owner-label"},
        ),
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"


def test_manual_label_remove_verifier_checks_label_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"labels": []}),
    )

    verification = reversing_loop._verify_manual_label_mutation(
        "demo",
        "review.label.remove",
        _executed_manual_label_payload(tmp_path, {"label_id": "manual-label-1"}),
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["layers"][1]["removed_label_ids"] == ["manual-label-1"]


def test_manual_label_verifier_requires_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"labels": [{"label_id": "manual-label-1", "name": "renamed_label"}]},
        ),
    )
    durable_result = _executed_command_payload()
    durable_result["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]

    verification = reversing_loop._verify_manual_label_mutation(
        "demo",
        "review.label.rename",
        durable_result,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "missing manual label payload"


def test_rsset_region_verifier_rejects_mismatched_payload_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "rsset_layout_regions": [
                    {
                        "rsset_layout_region_id": "catalog-rsset-region-work-0004",
                        "offset": 4,
                        "layout_name": "work",
                        "base_symbol": "__game_work_base__",
                        "symbol": "work_flags",
                    }
                ]
            },
        ),
    )

    verification = reversing_loop._verify_rsset_region_mutation(
        "demo",
        "target.rsset_region.add",
        _executed_rsset_region_payload(
            tmp_path,
            {
                "rsset_layout_region_id": "catalog-rsset-region-work-0008",
                "offset": 4,
                "layout_name": "work",
                "base_symbol": "__game_work_base__",
                "symbol": "work_flags",
            },
        ),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["matching_rsset_layout_regions"] == []


def test_target_command_verification_rejects_wrong_local_effect() -> None:
    command = {
        "kind": "command",
        "command_id": "target.equate.add",
        "context": {"kind": "target"},
        "parameters": {"name": "PLAYER_START_LIVES", "value": 3},
        "output_affecting": True,
    }
    durable_result = {
        "application": {
            "local_effects": [
                {
                    "kind": "execution_view",
                    "execution_view": {
                        "source_start": 0x20,
                        "source_end": 0x80,
                        "base_addr": 0x4000,
                        "name": "stage_code",
                    },
                }
            ]
        }
    }

    assert reversing_loop._verify_projection_metadata(command, durable_result) == {
        "layer": "projection",
        "status": "failed",
        "message": "target command local effect was not reported",
    }


def test_target_command_verification_rejects_mismatched_local_effect_payload() -> None:
    command = {
        "kind": "command",
        "command_id": "target.equate.add",
        "context": {"kind": "target"},
        "parameters": {"name": "PLAYER_START_LIVES", "value": 3},
        "output_affecting": True,
    }
    durable_result = {
        "application": {
            "local_effects": [{"kind": "target_equate", "target_equate": {"name": "PLAYER_START_LIVES", "value": 5}}]
        }
    }

    assert reversing_loop._verify_projection_metadata(command, durable_result)["status"] == "failed"


def test_target_command_verification_requires_rename_previous_name() -> None:
    command = {
        "kind": "command",
        "command_id": "target.equate.rename",
        "context": {"kind": "target"},
        "parameters": {"previous_name": "OLD_NAME", "name": "NEW_NAME"},
        "output_affecting": True,
    }
    durable_result = {
        "application": {"local_effects": [{"kind": "target_equate", "target_equate": {"name": "NEW_NAME"}}]}
    }

    assert reversing_loop._verify_projection_metadata(command, durable_result)["status"] == "failed"


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
    assert report["planner"]["selected_verifier"] == "projected_data_symbol_name"


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
    assert report["planner"]["selected_verifier"] == "suppressed_seeded_item"


def test_planner_reports_candidate_specific_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        {
            "id": "label-candidate",
            "candidate_id": "label-candidate",
            "kind": "label_name",
            "locator": _listing_locator(kind="instruction"),
            "element_id": "row-1:label:loc_10",
            "suggested_action_kinds": ["label.rename"],
            "new_label": "init_display",
            "default_verifier": "projection_metadata",
            "confidence": "high",
            "actionable": True,
        }
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    command = report["planner"]["ranked_candidates"][0]["candidate_commands"][0]
    assert command["command_id"] == "label.rename"
    assert command["verifier"] == "projection_metadata"


def test_planner_uses_next_candidate_command_when_first_option_is_unverified() -> None:
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        {
            "id": "multi-command",
            "candidate_id": "multi-command",
            "kind": "execution_view",
            "suggested_action_kinds": ["target.custom_struct.add", "target.execution_view.add"],
            "parameters": {
                "source_start": 0x20,
                "source_end": 0x80,
                "base_addr": 0x4000,
                "name": "stage_code",
            },
            "confidence": "high",
            "actionable": True,
        }
    ]

    selected = reversing_loop._select_command_action(inspect_report)

    assert selected is not None
    assert selected["command"]["command_id"] == "target.execution_view.add"
    assert inspect_report["planner"]["selected_command_id"] == "target.execution_view.add"


def test_run_one_uses_available_alternate_command_when_selected_catalog_action_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        {
            "id": "multi-command",
            "candidate_id": "multi-command",
            "kind": "data_symbol_name",
            "locator": _listing_locator(kind="data"),
            "suggested_action_kinds": ["row.seed.code", "data_symbol.rename"],
            "new_name": "player_table",
            "default_verifier": "round_trip",
            "confidence": "high",
            "actionable": True,
        }
    ]
    executed: list[str] = []
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_mutation",
        lambda target_id, command, result, project_root: {"status": "passed", "layers": []},
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "data_symbol.rename"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            executed.append(str(body["command_id"]))
            return {"data": _executed_command_payload()}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert executed == ["data_symbol.rename"]
    assert report["action"]["command_id"] == "data_symbol.rename"
    assert report["action_result"]["status"] == "executed"


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


def test_run_one_uses_listing_entrypoint_label_candidate_when_inspect_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path, entrypoint=2)
    inspect_report = {
        "target_id": "demo",
        "safe_to_mutate": True,
        "candidate_work": [],
        "verification_paths": [{"kind": "round_trip", "available": True}],
    }
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing") and not path.endswith("/listing/navigation"):
            return {
                "data": {
                    "rows": [
                        _listing_row(
                            row_key="entry-label",
                            kind="label",
                            label="loc_0_00000002",
                            start_offset=2,
                            end_offset=2,
                        )
                    ]
                }
            }
        if path.endswith("/listing/navigation"):
            return {"data": {}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "label.rename"
    assert report["action"]["parameters"] == {"name": "entrypoint"}
    assert report["selected_work_item"]["candidate_id"] == "entrypoint-label:entry-label:entrypoint"


def test_run_one_entrypoint_label_rename_executes_with_label_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path, entrypoint=2)
    _write_reproduction_exact(tmp_path)
    inspect_report = {
        "target_id": "demo",
        "safe_to_mutate": True,
        "candidate_work": [],
        "verification_paths": [{"kind": "round_trip", "available": True}],
    }
    listing_calls = 0
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: _project_with_manual_labels([{"name": "entrypoint", "addr": 2}]),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        nonlocal listing_calls
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if path.endswith("/listing") and not path.endswith("/listing/navigation"):
            listing_calls += 1
            label = "entrypoint" if listing_calls > 1 else "loc_0_00000002"
            return {
                "data": {
                    "rows": [
                        _listing_row(
                            row_key="entry-label",
                            kind="label",
                            label=label,
                            start_offset=2,
                            end_offset=2,
                        )
                    ]
                }
            }
        if path.endswith("/listing/navigation"):
            return {"data": {}}
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "label.rename"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "label.rename"
            _write_manual_log(tmp_path)
            return {"data": _executed_listing_label_payload(tmp_path)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "projection",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "label.rename"
    assert report["action_result"]["status"] == "executed"


def test_run_one_comment_edit_executes_with_projected_comment_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = [
        {
            "id": "comment-candidate",
            "candidate_id": "comment-candidate",
            "kind": "source_entrypoint_row",
            "locator": _listing_locator(),
            "suggested_comment_text": "Hunk file entrypoint.",
            "suggested_action_kinds": ["comment.edit"],
            "default_verifier": "projected_comment_text",
            "confidence": "high",
            "actionable": True,
        }
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "comment.edit"
            _write_manual_log(tmp_path)
            return {"data": _executed_listing_comment_payload(tmp_path)}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {}}}}
        if method == "GET" and path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(comment_text="Hunk file entrypoint.")]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "projection",
    ]
    assert report["action"]["command_id"] == "comment.edit"
    assert report["action_result"]["status"] == "executed"


def test_run_one_data_symbol_rename_executes_with_projected_name_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [_data_symbol_candidate(current_name="auto_data", new_name="player_table")]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_open_and_wait_listing", lambda target_id, timeout_seconds: {"status": "ready"})

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "data_symbol.rename"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "data_symbol.rename"
            _write_manual_log(tmp_path)
            return {"data": _executed_listing_comment_payload(tmp_path)}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {}}}}
        if method == "GET" and path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(row_key="row-1", kind="data", text="player_table:\n")]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "projection",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "data_symbol.rename"
    assert report["action_result"]["status"] == "executed"


def test_run_one_data_symbol_remove_executes_with_suppression_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    candidate = _data_symbol_remove_candidate(suppressed=False)
    candidate["parameters"] = {"kind": "seeded_entity", "hunk": 0, "addr": 0x100}
    inspect_report["candidate_work"] = [candidate]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "suppressed_seeded_items": [
                    {"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
                ]
            },
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "data_symbol.remove"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "data_symbol.remove"
            _write_manual_log(tmp_path)
            return {"data": _executed_seeded_item_suppression_payload(tmp_path)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "data_symbol.remove"
    assert report["action_result"]["status"] == "executed"


def test_run_one_seeded_item_correction_executes_with_suppression_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    candidate = {
        "id": "suppress-seeded-entity",
        "candidate_id": "suppress-seeded-entity",
        "kind": "seeded_item_correction",
        "locator": _listing_locator(kind="data"),
        "suggested_action_kinds": ["correction.suppress_seeded_item.seeded_entity"],
        "parameters": {"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
        "confidence": "high",
        "actionable": True,
    }
    inspect_report["candidate_work"] = [candidate]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "suppressed_seeded_items": [
                    {"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
                ]
            },
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "correction.suppress_seeded_item.seeded_entity"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "correction.suppress_seeded_item.seeded_entity"
            _write_manual_log(tmp_path)
            return {"data": _executed_seeded_item_suppression_payload(tmp_path)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "correction.suppress_seeded_item.seeded_entity"
    assert report["action_result"]["status"] == "executed"


def test_run_one_execution_view_executes_with_view_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    candidate = {
        "id": "execution-view",
        "candidate_id": "execution-view",
        "kind": "execution_view",
        "suggested_action_kinds": ["target.execution_view.add"],
        "parameters": _execution_view_payload(),
        "confidence": "high",
        "actionable": True,
    }
    inspect_report["candidate_work"] = [candidate]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"execution_views": [_execution_view_payload()]},
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "target.execution_view.add"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "target.execution_view.add"
            _write_manual_log(tmp_path)
            return {"data": _executed_execution_view_payload(tmp_path)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "target.execution_view.add"
    assert report["action_result"]["status"] == "executed"


def test_run_one_execution_view_remove_executes_with_removed_view_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    candidate = {
        "id": "execution-view-remove",
        "candidate_id": "execution-view-remove",
        "kind": "execution_view",
        "suggested_action_kinds": ["target.execution_view.remove"],
        "parameters": {
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
        },
        "confidence": "high",
        "actionable": True,
    }
    inspect_report["candidate_work"] = [candidate]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "removed_execution_views": [
                    {
                        "source_start": 0x20,
                        "source_end": 0x80,
                        "base_addr": 0x4000,
                    }
                ]
            },
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "target.execution_view.remove"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "target.execution_view.remove"
            _write_manual_log(tmp_path)
            return {"data": _executed_execution_view_remove_payload(tmp_path)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["verification"]["layers"][1]["removed"] is True
    assert report["action"]["command_id"] == "target.execution_view.remove"
    assert report["action_result"]["status"] == "executed"


def test_run_one_semantic_hint_executes_with_hint_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        {
            "id": "semantic-lvo",
            "candidate_id": "semantic-lvo",
            "kind": "api_semantic_hint",
            "locator": _listing_locator(),
            "element_id": "row-1:immediate:0:-552",
            "element_kind": "immediate",
            "operand_index": 0,
            "value": -552,
            "suggested_action_kinds": ["semantic.lvo.exec.library_OpenLibrary"],
            "default_verifier": "round_trip",
            "confidence": "high",
            "actionable": True,
        }
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"semantic_hints": [_semantic_hint_payload()]},
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "semantic.lvo.exec.library_OpenLibrary"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "semantic.lvo.exec.library_OpenLibrary"
            _write_manual_log(tmp_path)
            return {"data": _executed_semantic_hint_payload(tmp_path)}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "semantic.lvo.exec.library_OpenLibrary"
    assert report["action_result"]["status"] == "executed"


def test_run_one_library_base_executes_with_register_seed_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        {
            "id": "semantic-library-base",
            "candidate_id": "semantic-library-base",
            "kind": "api_register_semantic",
            "locator": _listing_locator(),
            "element_id": "row-1:symbol:0:_LVOSetPointer",
            "element_kind": "symbol",
            "operand_index": 0,
            "symbol": "_LVOSetPointer",
            "base_register": "A6",
            "api_library": "intuition.library",
            "api_function": "SetPointer",
            "suggested_action_kinds": ["semantic.library_base.intuition.library"],
            "default_verifier": "round_trip",
            "confidence": "high",
            "actionable": True,
        }
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "register_seeds": [
                    {"register": "A6", "kind": "library_base", "library_name": "intuition.library"},
                ]
            },
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "semantic.library_base.intuition.library"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "semantic.library_base.intuition.library"
            _write_manual_log(tmp_path)
            return {
                "data": _executed_register_seed_payload(
                    tmp_path,
                    {"register": "A6", "kind": "library_base", "library_name": "intuition.library"},
                )
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "semantic.library_base.intuition.library"
    assert report["action_result"]["status"] == "executed"


def test_library_base_register_seed_verifier_requires_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "register_seeds": [
                    {"register": "A6", "kind": "library_base", "library_name": "intuition.library"},
                ]
            },
        ),
    )
    command = {
        "command_id": "semantic.library_base.intuition.library",
        "context": {"kind": "element", "base_register": "A6"},
        "parameters": {},
        "output_affecting": True,
    }

    verification = reversing_loop._verify_library_base_register_seed_mutation(
        "demo",
        command,
        _executed_listing_comment_payload(tmp_path),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "missing register seed payload"


def test_run_one_struct_pointer_seed_executes_with_register_seed_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = [
        {
            "id": "semantic-struct-pointer",
            "candidate_id": "semantic-struct-pointer",
            "kind": "register_semantic",
            "locator": _listing_locator(),
            "element_id": "row-1:register:0:A1",
            "element_kind": "register",
            "register": "A1",
            "suggested_action_kinds": ["semantic.register.struct_ptr"],
            "parameters": {"struct_name": "IOStdReq"},
            "default_verifier": "round_trip",
            "confidence": "high",
            "actionable": True,
        }
    ]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "register_seeds": [
                    {"register": "A1", "kind": "struct_ptr", "struct_name": "IOStdReq"},
                ]
            },
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "semantic.register.struct_ptr"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "semantic.register.struct_ptr"
            _write_manual_log(tmp_path)
            return {
                "data": _executed_register_seed_payload(
                    tmp_path,
                    {"register": "A1", "kind": "struct_ptr", "struct_name": "IOStdReq"},
                )
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "semantic.register.struct_ptr"
    assert report["action_result"]["status"] == "executed"


def test_projected_data_symbol_verifier_checks_all_matching_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    command = {
        "command_id": "data_symbol.rename",
        "context": {"kind": "row", "locator": _listing_locator(kind="data")},
        "parameters": {"name": "player_table"},
    }
    calls = 0

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {
            "data": {
                "rows": [
                    _listing_row(row_key="row-1", kind="data", text="\tdc.b $00\n"),
                    _listing_row(row_key="data-label", kind="label", label="player_table", start_offset=0, end_offset=0),
                ]
            }
        }

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)
    layer = reversing_loop._verify_projected_data_symbol_name("demo", command)

    assert calls == 1
    assert layer["status"] == "passed"
    assert layer["row_key"] == "data-label"


def test_run_one_retries_listing_candidates_when_inspect_candidates_all_skip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = [_representation_candidate(current_representation="character")]
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
    assert report["selected_work_item"]["candidate_id"] == "representation:row-1:0:48:character"
    skipped = report["planner"]["skipped_candidates"]
    assert skipped[0]["candidate_id"] == "repr-candidate"
    assert skipped[0]["stop_reason"] == "candidate already satisfied in projected semantic state"


def test_run_one_tries_listing_candidates_before_accepting_comment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
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
    assert report["selected_work_item"]["candidate_id"] == "representation:row-1:0:48:character"
    ranked_ids = [
        candidate.get("candidate_id") or candidate.get("id") for candidate in report["planner"]["ranked_candidates"]
    ]
    assert ranked_ids[:2] == ["representation:row-1:0:48:character", "candidate-1"]


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


def test_listing_entrypoint_label_candidates_skip_human_label(tmp_path: Path) -> None:
    _target(tmp_path)
    _write_raw_source(tmp_path, entrypoint=2)
    row = _listing_row(
        row_key="entry-label",
        kind="label",
        label="already_named_entry",
        start_offset=2,
        end_offset=2,
    )

    candidates = reversing_loop._listing_entrypoint_label_candidates("demo", [row], project_root=tmp_path)

    assert candidates == []


def test_listing_entrypoint_label_candidates_skip_existing_effective_label(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _write_raw_source(tmp_path, entrypoint=2)
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_code_labels=(
                SeededCodeLabelMetadata(
                    hunk=0,
                    addr=2,
                    name="entrypoint",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.VALIDATED,
                    citation="test",
                ),
            ),
        ),
    )
    row = _listing_row(
        row_key="entry-label",
        kind="label",
        label="loc_0_00000002",
        start_offset=2,
        end_offset=2,
    )
    inspect_report = {"target_state": {"target_dir": str(target_dir), "project": {"manual_state": {}}}}

    candidates = reversing_loop._listing_entrypoint_label_candidates(
        "demo",
        [row],
        project_root=tmp_path,
        existing_labels=reversing_loop._existing_source_label_names(inspect_report),
    )

    assert candidates == []


def test_listing_data_symbol_candidates_use_runtime_ref_identity() -> None:
    row = _listing_row(
        row_key="code-row",
        text="\tlea $120(pc),a0\n",
        start_offset=0x20,
        end_offset=0x24,
    )
    row["runtime_address_refs"] = [
        {
            "offset": 0x20,
            "operand_index": 0,
            "target_section_index": 1,
            "target_offset": 0x120,
            "runtime_address": 0x40120,
            "data_class": "bitmap",
            "size": 0x20,
        }
    ]

    candidates = reversing_loop._listing_data_symbol_candidates([row])
    command = reversing_loop._candidate_command_options(candidates[0])[0]

    assert candidates[0]["candidate_id"] == "data-ref-symbol:code-row:0:1:00000120:bitmap_00040120"
    assert candidates[0]["durable_id"] == "data_ref:h1:00000120"
    assert candidates[0]["new_name"] == "bitmap_00040120"
    assert candidates[0]["element_id"] == "code-row:data_ref:0:1:00000120"
    assert command["command_id"] == "data_symbol.rename"
    assert command["context"] == {
        "kind": "element",
        "locator": row["locator"],
        "element_id": "code-row:data_ref:0:1:00000120",
    }
    assert command["parameters"] == {"name": "bitmap_00040120"}


def test_listing_data_symbol_candidates_use_runtime_address_when_class_missing() -> None:
    row = _listing_row(
        row_key="code-row",
        text="\tlea $120(pc),a0\n",
        start_offset=0x20,
        end_offset=0x24,
    )
    row["runtime_address_refs"] = [
        {
            "offset": 0x20,
            "operand_index": 0,
            "target_section_index": 1,
            "target_offset": 0x120,
            "runtime_address": 0x4F92B,
            "size": 4,
        }
    ]

    candidates = reversing_loop._listing_data_symbol_candidates([row])
    command = reversing_loop._candidate_command_options(candidates[0])[0]

    assert candidates[0]["candidate_id"] == "data-ref-symbol:code-row:0:1:00000120:runtime_address_0004F92B"
    assert candidates[0]["durable_id"] == "data_ref:h1:00000120"
    assert candidates[0]["new_name"] == "runtime_address_0004F92B"
    assert candidates[0]["evidence"]["runtime_address"] == 0x4F92B
    assert command["command_id"] == "data_symbol.rename"
    assert command["parameters"] == {"name": "runtime_address_0004F92B"}


def test_listing_data_symbol_candidates_use_data_class_row_identity() -> None:
    row = _listing_row(
        row_key="bitmap-row",
        kind="data",
        text="\tdc.b $00,$01,$02,$03\n",
        start_offset=0x40,
        end_offset=0x44,
    )
    row["data_class"] = "bitmap"

    candidates = reversing_loop._listing_data_symbol_candidates([row])
    command = reversing_loop._candidate_command_options(candidates[0])[0]

    assert candidates[0]["candidate_id"] == "data-class-symbol:bitmap-row:0:00000040:bitmap_h0_00000040"
    assert candidates[0]["durable_id"] == "data_class:h0:00000040"
    assert candidates[0]["new_name"] == "bitmap_h0_00000040"
    assert command["command_id"] == "data_symbol.rename"
    assert command["context"] == {"kind": "row", "locator": row["locator"]}
    assert command["parameters"] == {"name": "bitmap_h0_00000040"}


def test_listing_data_symbol_candidates_skip_existing_manual_name() -> None:
    row = _listing_row(
        row_key="code-row",
        text="\tlea $120(pc),a0\n",
        start_offset=0x20,
        end_offset=0x24,
    )
    row["runtime_address_refs"] = [
        {
            "offset": 0x20,
            "operand_index": 0,
            "target_section_index": 1,
            "target_offset": 0x120,
            "runtime_address": 0x40120,
            "data_class": "bitmap",
        }
    ]
    inspect_report = {
        "target_state": {
            "project": {
                "manual_state": {
                    "seeds": [
                        {
                            "kind": "data",
                            "hunk": 1,
                            "addr": 0x120,
                            "name": "bitmap_00040120",
                        }
                    ]
                }
            }
        }
    }

    candidates = reversing_loop._listing_data_symbol_candidates(
        [row],
        existing_data_symbols=reversing_loop._existing_data_symbol_names(inspect_report),
    )

    assert candidates == []


def test_listing_data_symbol_candidates_skip_existing_effective_name(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    hunk=1,
                    addr=0x120,
                    name="bitmap_00040120",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.VALIDATED,
                    citation="test",
                ),
            ),
        ),
    )
    row = _listing_row(
        row_key="code-row",
        text="\tlea $120(pc),a0\n",
        start_offset=0x20,
        end_offset=0x24,
    )
    row["runtime_address_refs"] = [
        {
            "offset": 0x20,
            "operand_index": 0,
            "target_section_index": 1,
            "target_offset": 0x120,
            "runtime_address": 0x40120,
            "data_class": "bitmap",
        }
    ]
    inspect_report = {"target_state": {"target_dir": str(target_dir), "project": {"manual_state": {}}}}

    candidates = reversing_loop._listing_data_symbol_candidates(
        [row],
        existing_data_symbols=reversing_loop._existing_data_symbol_names(inspect_report),
    )

    assert candidates == []


def test_listing_data_symbol_candidates_skip_existing_context_symbol() -> None:
    row = _listing_row(
        row_key="code-row",
        text="\tlea $120(pc),a0\n",
        start_offset=0x20,
        end_offset=0x24,
    )
    row["runtime_address_refs"] = [
        {
            "offset": 0x20,
            "operand_index": 0,
            "target_section_index": 1,
            "target_offset": 0x120,
            "runtime_address": 0x40120,
            "data_class": "bitmap",
            "symbol": "bitmap_00040120",
        }
    ]

    assert reversing_loop._listing_data_symbol_candidates([row]) == []


def test_listing_data_role_candidates_mine_ascii_string_rows() -> None:
    row = _listing_row(
        row_key="data-row",
        kind="data",
        text="\tdc.b $48,$45,$4C,$4C,$4F,$00\n",
        start_offset=0x40,
        end_offset=0x46,
    )
    row["bytes"] = "48454c4c4f00"

    candidates = reversing_loop._listing_data_role_candidates([row])
    command = reversing_loop._candidate_command_options(candidates[0])[0]

    assert candidates[0]["candidate_id"] == "data-role-string:data-row:0:00000040"
    assert candidates[0]["durable_id"] == "data_role:h0:00000040:string"
    assert candidates[0]["evidence"]["preview"] == "HELLO"
    assert candidates[0]["default_verifier"] == "manual_seed_state"
    assert command["command_id"] == "row.seed.data.string"
    assert command["context"] == {"kind": "row", "locator": row["locator"]}
    assert command["parameters"] == {
        "seed_kind": "data",
        "data_role": "string",
        "unit": "byte",
        "encoding": "ascii",
    }


def test_listing_data_role_candidates_skip_existing_string_seed() -> None:
    row = _listing_row(
        row_key="data-row",
        kind="data",
        text="\tdc.b $48,$49,$00\n",
        start_offset=0x40,
        end_offset=0x43,
    )
    row["bytes"] = "484900"
    inspect_report = {
        "target_state": {
            "project": {
                "manual_state": {
                    "seeds": [
                        {
                            "kind": "data",
                            "hunk": 0,
                            "addr": 0x40,
                            "data_role": "string",
                        }
                    ]
                }
            }
        }
    }

    candidates = reversing_loop._listing_data_role_candidates(
        [row],
        existing_data_roles=reversing_loop._existing_data_seed_roles(inspect_report),
    )

    assert candidates == []


def test_listing_data_role_candidates_skip_existing_effective_role(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    hunk=0,
                    addr=0x40,
                    end=0x46,
                    type="data",
                    subtype="string",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.VALIDATED,
                    citation="test",
                ),
            ),
        ),
    )
    row = _listing_row(
        row_key="data-row",
        kind="data",
        text="\tdc.b $48,$45,$4c,$4c,$4f,$00\n",
        start_offset=0x40,
        end_offset=0x46,
    )
    row["bytes"] = "48454c4c4f00"
    inspect_report = {"target_state": {"target_dir": str(target_dir), "project": {"manual_state": {}}}}

    candidates = reversing_loop._listing_data_role_candidates(
        [row],
        existing_data_roles=reversing_loop._existing_data_seed_roles(inspect_report),
    )

    assert candidates == []


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
    assert candidates[0]["default_verifier"] == "rsset_region_state"


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


def test_existing_rsset_region_map_reads_effective_target_metadata(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            rsset_layout_regions=(
                RssetLayoutRegionMetadata(
                    offset=0x100,
                    size=22,
                    layout_name="app",
                    base_symbol="__amiga_app_base__",
                    symbol="app_input_event",
                    struct_name="InputEvent",
                    storage_kind=RssetLayoutStorageKind.STRUCT_INSTANCE,
                    parser_role="input_event",
                    parser_routine="parse_input_event",
                    parse_order=1,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.VALIDATED,
                    citation="test",
                ),
            ),
        ),
    )
    inspect_report = {"target_state": {"target_dir": str(target_dir), "project": {"manual_state": {}}}}

    existing = reversing_loop._existing_rsset_region_map(inspect_report)
    candidates = reversing_loop._listing_rsset_region_candidates(
        _rsset_suggestion_navigation_payload(),
        existing_regions=existing,
    )

    assert existing[("app", "__amiga_app_base__", 0x100)]["symbol"] == "app_input_event"
    assert candidates[0]["suggested_action_kinds"] == ["target.rsset_region.edit"]
    command = reversing_loop._candidate_command_options(candidates[0])[0]
    assert reversing_loop._candidate_already_satisfied(candidates[0], command)


def test_listing_rsset_region_candidates_use_platform_api_regions_without_suggestions() -> None:
    candidates = reversing_loop._listing_rsset_region_candidates(_rsset_region_navigation_payload())

    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "rsset-suggestion:app:__amiga_app_base__:0100:app_input_event"
    assert candidates[0]["suggested_action_kinds"] == ["target.rsset_region.add"]
    assert candidates[0]["evidence"]["navigation_group"] == "app-slot-regions"
    assert candidates[0]["parameters"] == {
        "offset": 0x100,
        "size": 22,
        "symbol": "app_input_event",
        "struct_name": "InputEvent",
    }


def test_listing_rsset_region_candidates_dedupe_region_when_suggestion_exists() -> None:
    payload = _rsset_suggestion_navigation_payload()
    groups = cast(dict[str, object], payload["groups"])
    groups["app-slot-regions"] = cast(dict[str, object], _rsset_region_navigation_payload()["groups"])[
        "app-slot-regions"
    ]

    candidates = reversing_loop._listing_rsset_region_candidates(payload)

    assert len(candidates) == 1
    assert candidates[0]["evidence"]["navigation_group"] == "app-slot-suggestions"


def test_semantic_dynamic_command_candidate_uses_element_context_and_specific_verifier() -> None:
    candidate = {
        "id": "semantic-library-base",
        "candidate_id": "semantic-library-base",
        "kind": "api_register_semantic",
        "locator": _listing_locator(),
        "element_id": "row-1:symbol:0:_LVOSetPointer",
        "element_kind": "symbol",
        "operand_index": 0,
        "symbol": "_LVOSetPointer",
        "base_register": "A6",
        "api_library": "intuition.library",
        "api_function": "SetPointer",
        "suggested_action_kinds": ["semantic.library_base.intuition.library"],
        "default_verifier": "round_trip",
        "confidence": "high",
        "actionable": True,
    }
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = [candidate]
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]

    command = reversing_loop._candidate_command_options(candidate)[0]
    selected = reversing_loop._select_command_action(inspect_report)

    assert command["command_id"] == "semantic.library_base.intuition.library"
    assert command["context"] == {
        "kind": "element",
        "locator": _listing_locator(),
        "element_id": "row-1:symbol:0:_LVOSetPointer",
        "element_kind": "symbol",
        "operand_index": 0,
        "symbol": "_LVOSetPointer",
        "base_register": "A6",
        "api_library": "intuition.library",
        "api_function": "SetPointer",
    }
    assert command["output_affecting"] is True
    assert reversing_loop._candidate_verifier(candidate, command) == "library_base_register_seed"
    assert selected is not None
    assert selected["command"]["command_id"] == "semantic.library_base.intuition.library"


def test_unknown_source_command_prefixes_do_not_get_round_trip_fallback() -> None:
    assert reversing_loop._default_verifier_for_actions(["data_symbol.create"]) is None
    assert reversing_loop._default_verifier_for_actions(["semantic.api_arg.foo"]) is None


def test_rsset_binding_candidate_uses_element_context_and_binding_verifier() -> None:
    candidate = {
        "id": "rsset-binding",
        "candidate_id": "rsset-binding",
        "kind": "rsset_use_site_binding",
        "locator": _listing_locator(),
        "element_id": "row-1:displacement:0:operand",
        "suggested_action_kinds": ["rsset.binding.bind"],
        "parameters": {
            "layout_name": "app",
            "base_symbol": "__amiga_app_base__",
            "base_register": "A6",
            "base_evidence_id": "selected-base:A6:__amiga_app_base__",
            "displacement": 0x0102,
            "operand_index": 0,
        },
        "default_verifier": "rsset_binding_state",
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["command_id"] == "rsset.binding.bind"
    assert command["context"] == {
        "kind": "element",
        "locator": _listing_locator(),
        "element_id": "row-1:displacement:0:operand",
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "rsset_binding_state"


def test_listing_library_base_candidates_use_lvo_api_call() -> None:
    candidates = reversing_loop._listing_library_base_candidates([_library_base_row()])
    command = reversing_loop._candidate_command_options(candidates[0])[0]

    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "library-base:row-1:0:A6:intuition.library"
    assert candidates[0]["element_id"] == "row-1:symbol:0:_LVOSetPointer"
    assert candidates[0]["suggested_action_kinds"] == ["semantic.library_base.intuition.library"]
    assert candidates[0]["api_function"] == "SetPointer"
    assert candidates[0]["default_verifier"] == "library_base_register_seed"
    assert command["command_id"] == "semantic.library_base.intuition.library"
    assert command["context"]["api_library"] == "intuition.library"
    assert reversing_loop._candidate_verifier(candidates[0], command) == "library_base_register_seed"


def test_listing_library_base_candidates_skip_already_projected_seed() -> None:
    existing = {("A6", "library_base"): {"kind": "library_base", "register": "A6", "library_name": "intuition.library"}}

    candidates = reversing_loop._listing_library_base_candidates(
        [_library_base_row()],
        existing_register_seeds=existing,
    )

    assert candidates == []


def test_listing_struct_pointer_candidates_use_unresolved_typed_access_register() -> None:
    candidates = reversing_loop._listing_struct_pointer_candidates([_struct_pointer_row()])
    command = reversing_loop._candidate_command_options(candidates[0])[0]

    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "struct-ptr:row-1:0:A0:InputEvent"
    assert candidates[0]["element_id"] == "row-1:register:0:operand"
    assert candidates[0]["suggested_action_kinds"] == ["semantic.register.struct_ptr"]
    assert candidates[0]["parameters"] == {"struct_name": "InputEvent"}
    assert candidates[0]["evidence"]["classification"] == "prefix_extension"
    assert candidates[0]["default_verifier"] == "struct_pointer_register_seed"
    assert reversing_loop._candidate_verifier(candidates[0], command) == "struct_pointer_register_seed"


def test_listing_struct_pointer_candidates_use_memory_operand_register() -> None:
    row = _struct_pointer_row()
    row["operand_parts"] = [
        {"kind": "memory", "operand_index": 0, "metadata": {}},
        {"kind": "register", "operand_index": 1, "register": "D0", "metadata": {}},
    ]

    candidates = reversing_loop._listing_struct_pointer_candidates([row])

    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "struct-ptr:row-1:0:A0:InputEvent"
    assert candidates[0]["element_id"] == "row-1:memory:0:operand"
    assert candidates[0]["element_kind"] == "memory"
    assert candidates[0]["parameters"] == {"struct_name": "InputEvent"}


def test_listing_struct_pointer_candidates_skip_already_projected_seed() -> None:
    existing = {("A0", "struct_ptr"): {"kind": "struct_ptr", "register": "A0", "struct_name": "InputEvent"}}

    candidates = reversing_loop._listing_struct_pointer_candidates(
        [_struct_pointer_row()],
        existing_register_seeds=existing,
    )

    assert candidates == []


def test_existing_register_seed_map_reads_effective_target_metadata(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(
                EntryRegisterSeedMetadata(
                    entry_offset=None,
                    register="a0",
                    kind=EntryRegisterSeedKind.STRUCT_PTR,
                    note="seeded by target metadata",
                    struct_name="InputEvent",
                ),
            ),
        ),
    )
    inspect_report = {"target_state": {"target_dir": str(target_dir), "project": {"manual_state": {}}}}

    existing = reversing_loop._existing_register_seed_map(inspect_report)
    candidates = reversing_loop._listing_struct_pointer_candidates(
        [_struct_pointer_row()],
        existing_register_seeds=existing,
    )

    assert existing[("A0", "struct_ptr")]["struct_name"] == "InputEvent"
    assert candidates == []


def test_run_one_uses_listing_struct_pointer_candidate_when_inspect_empty(
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
            return {"data": {"groups": {}}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_struct_pointer_row()]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "semantic.register.struct_ptr"
    assert report["action"]["context"]["element_id"] == "row-1:register:0:operand"
    assert report["action"]["parameters"] == {"struct_name": "InputEvent"}


def test_run_one_uses_listing_library_base_candidate_when_inspect_empty(
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
            return {"data": {"groups": {}}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_library_base_row()]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)

    assert report["action"]["command_id"] == "semantic.library_base.intuition.library"
    assert report["selected_work_item"]["candidate_id"] == "library-base:row-1:0:A6:intuition.library"


def test_semantic_library_base_candidate_skips_already_projected_seed() -> None:
    candidate = {
        "id": "semantic-library-base",
        "candidate_id": "semantic-library-base",
        "kind": "api_register_semantic",
        "locator": _listing_locator(),
        "element_id": "row-1:symbol:0:_LVOSetPointer",
        "element_kind": "symbol",
        "symbol": "_LVOSetPointer",
        "base_register": "A6",
        "api_library": "intuition.library",
        "api_function": "SetPointer",
        "suggested_action_kinds": ["semantic.library_base.intuition.library"],
        "current_metadata": {
            "kind": "library_base",
            "register": "A6",
            "library_name": "intuition.library",
        },
        "default_verifier": "round_trip",
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_semantic_struct_pointer_candidate_skips_already_projected_seed() -> None:
    candidate = {
        "id": "semantic-struct-pointer",
        "candidate_id": "semantic-struct-pointer",
        "kind": "register_semantic",
        "locator": _listing_locator(),
        "element_id": "row-1:register:0:A1",
        "element_kind": "register",
        "register": "A1",
        "suggested_action_kinds": ["semantic.register.struct_ptr"],
        "parameters": {"struct_name": "IOStdReq"},
        "current_metadata": {
            "kind": "struct_ptr",
            "register": "A1",
            "struct_name": "IOStdReq",
        },
        "default_verifier": "round_trip",
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_embedded_semantic_hint_command_normalizes_with_prefix_rank() -> None:
    candidate = {
        "command": {
            "command_id": "semantic.struct_offset.Node.ln_Succ",
            "context": {
                "kind": "element",
                "locator": _listing_locator(),
                "element_id": "row-1:immediate:0:0",
            },
            "parameters": {"domain": "struct_offset", "symbol": "Node.ln_Succ", "value": 0},
        }
    }

    options = reversing_loop._candidate_command_options(candidate)

    assert options == [
        {
            "kind": "command",
            "command_id": "semantic.struct_offset.Node.ln_Succ",
            "context": {
                "kind": "element",
                "locator": _listing_locator(),
                "element_id": "row-1:immediate:0:0",
            },
            "parameters": {"domain": "struct_offset", "symbol": "Node.ln_Succ", "value": 0},
            "output_affecting": True,
        }
    ]
    assert reversing_loop._candidate_verifier(candidate, options[0]) == "semantic_hint_state"


def test_target_custom_struct_command_candidate_uses_target_context_and_requires_verifier() -> None:
    candidate = {
        "id": "custom-struct-field",
        "candidate_id": "custom-struct-field",
        "kind": "custom_struct_field",
        "suggested_action_kinds": ["target.custom_struct_field.add"],
        "parameters": {
            "struct_name": "InputEvent",
            "name": "ie_Code",
            "type": "UWORD",
            "offset": 6,
            "size": 2,
        },
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "target.custom_struct_field.add",
        "context": {"kind": "target"},
        "parameters": {
            "struct_name": "InputEvent",
            "name": "ie_Code",
            "type": "UWORD",
            "offset": 6,
            "size": 2,
        },
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) is None
    assert reversing_loop._candidate_skip_reason(candidate, command) == "missing action-specific verifier"


def test_target_custom_struct_candidate_skips_already_projected_field() -> None:
    field = {
        "struct_name": "InputEvent",
        "name": "ie_Code",
        "type": "UWORD",
        "offset": 6,
        "size": 2,
    }
    candidate = {
        "id": "custom-struct-field",
        "candidate_id": "custom-struct-field",
        "kind": "custom_struct_field",
        "suggested_action_kinds": ["target.custom_struct_field.add"],
        "parameters": field,
        "current_metadata": field,
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_target_custom_struct_rename_skips_projected_new_name() -> None:
    candidate = {
        "id": "custom-struct-rename",
        "candidate_id": "custom-struct-rename",
        "kind": "custom_struct",
        "suggested_action_kinds": ["target.custom_struct.rename"],
        "parameters": {"previous_name": "InputEvent", "name": "GameInput"},
        "current_metadata": {"name": "GameInput"},
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_typed_field_command_candidate_uses_selected_element_context() -> None:
    candidate = {
        "id": "typed-gap-field",
        "candidate_id": "typed-gap-field",
        "kind": "typed_gap_field",
        "locator": _listing_locator(),
        "element_id": "row-1:typed_gap:1:A0:36",
        "element_kind": "typed_gap",
        "operand_index": 1,
        "base_register": "A0",
        "displacement": 36,
        "root_struct_name": "InputEvent",
        "refined_struct_name": "DerivedEvent",
        "classification": "prefix_extension",
        "suggested_action_kinds": ["typed_gap.field.add"],
        "parameters": {"name": "de_Code", "type": "UWORD", "size": 2},
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "typed_gap.field.add",
        "context": {
            "kind": "element",
            "locator": _listing_locator(),
            "element_id": "row-1:typed_gap:1:A0:36",
            "element_kind": "typed_gap",
            "operand_index": 1,
            "base_register": "A0",
            "displacement": 36,
            "root_struct_name": "InputEvent",
            "refined_struct_name": "DerivedEvent",
            "classification": "prefix_extension",
        },
        "parameters": {"name": "de_Code", "type": "UWORD", "size": 2},
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) is None
    assert reversing_loop._candidate_skip_reason(candidate, command) == "missing action-specific verifier"


def test_typed_field_candidate_skips_already_projected_field() -> None:
    field = {"name": "de_Code", "type": "UWORD", "size": 2}
    candidate = {
        "id": "typed-gap-field",
        "candidate_id": "typed-gap-field",
        "kind": "typed_gap_field",
        "locator": _listing_locator(),
        "element_id": "row-1:typed_gap:1:A0:36",
        "element_kind": "typed_gap",
        "suggested_action_kinds": ["typed_gap.field.add"],
        "parameters": field,
        "current_metadata": field,
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_target_execution_view_command_candidate_uses_target_context() -> None:
    candidate = {
        "id": "execution-view",
        "candidate_id": "execution-view",
        "kind": "execution_view",
        "suggested_action_kinds": ["target.execution_view.add"],
        "parameters": {
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
            "name": "stage_code",
        },
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "target.execution_view.add",
        "context": {"kind": "target"},
        "parameters": {
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
            "name": "stage_code",
        },
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "execution_view_state"


def test_target_execution_view_candidate_skips_already_projected_view() -> None:
    candidate = {
        "id": "execution-view",
        "candidate_id": "execution-view",
        "kind": "execution_view",
        "suggested_action_kinds": ["target.execution_view.add"],
        "parameters": {
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
            "name": "stage_code",
        },
        "current_metadata": {
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
            "name": "stage_code",
        },
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_target_equate_command_candidate_uses_target_context() -> None:
    candidate = {
        "id": "target-equate",
        "candidate_id": "target-equate",
        "kind": "target_equate",
        "suggested_action_kinds": ["target.equate.add"],
        "parameters": {"name": "PLAYER_START_LIVES", "value": 3},
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "target.equate.add",
        "context": {"kind": "target"},
        "parameters": {"name": "PLAYER_START_LIVES", "value": 3},
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "target_equate_state"


def test_target_equate_candidate_skips_already_projected_equate() -> None:
    candidate = {
        "id": "target-equate",
        "candidate_id": "target-equate",
        "kind": "target_equate",
        "suggested_action_kinds": ["target.equate.add"],
        "parameters": {"name": "PLAYER_START_LIVES", "value": 3},
        "current_metadata": {"name": "PLAYER_START_LIVES", "value": 3},
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_target_equate_rename_skips_projected_new_name() -> None:
    candidate = {
        "id": "target-equate-rename",
        "candidate_id": "target-equate-rename",
        "kind": "target_equate",
        "suggested_action_kinds": ["target.equate.rename"],
        "parameters": {"previous_name": "PLAYER_START_LIVES", "name": "PLAYER_INITIAL_LIVES"},
        "current_metadata": {"name": "PLAYER_INITIAL_LIVES"},
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_correction_suppress_seeded_item_candidate_uses_row_context_with_prefix_rank() -> None:
    candidate = {
        "id": "suppress-seeded-entity",
        "candidate_id": "suppress-seeded-entity",
        "kind": "seeded_item_correction",
        "locator": _listing_locator(kind="data"),
        "suggested_action_kinds": ["correction.suppress_seeded_item.seeded_entity"],
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "correction.suppress_seeded_item.seeded_entity",
        "context": {"kind": "row", "locator": _listing_locator(kind="data")},
        "parameters": {},
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "suppressed_seeded_item"


def test_correction_suppress_seeded_item_skips_already_projected_suppression() -> None:
    candidate = {
        "id": "suppress-seeded-entity",
        "candidate_id": "suppress-seeded-entity",
        "kind": "seeded_item_correction",
        "locator": _listing_locator(kind="data"),
        "suggested_action_kinds": ["correction.suppress_seeded_item.seeded_entity"],
        "current_metadata": {"suppressed": True},
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_app_slot_command_candidate_uses_selected_element_context() -> None:
    candidate = {
        "id": "app-slot-rename",
        "candidate_id": "app-slot-rename",
        "kind": "app_slot_region",
        "locator": _listing_locator(),
        "element_id": "row-1:app_slot:1:0234",
        "element_kind": "app_slot",
        "operand_index": 1,
        "symbol": "app_0234",
        "displacement": 0x234,
        "base_register": "A6",
        "access": "write",
        "suggested_action_kinds": ["app_slot.rename"],
        "parameters": {"symbol": "app_player_state", "size": 4, "storage_kind": "pointer"},
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "app_slot.rename",
        "context": {
            "kind": "element",
            "locator": _listing_locator(),
            "element_id": "row-1:app_slot:1:0234",
            "element_kind": "app_slot",
            "operand_index": 1,
            "symbol": "app_0234",
            "displacement": 0x234,
            "base_register": "A6",
            "access": "write",
        },
        "parameters": {"symbol": "app_player_state", "size": 4, "storage_kind": "pointer"},
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "rsset_region_state"


def test_app_slot_candidate_skips_already_projected_region() -> None:
    parameters = {"symbol": "app_player_state", "size": 4, "storage_kind": "pointer"}
    candidate = {
        "id": "app-slot-rename",
        "candidate_id": "app-slot-rename",
        "kind": "app_slot_region",
        "locator": _listing_locator(),
        "element_id": "row-1:app_slot:1:0234",
        "element_kind": "app_slot",
        "operand_index": 1,
        "symbol": "app_0234",
        "displacement": 0x234,
        "base_register": "A6",
        "access": "write",
        "suggested_action_kinds": ["app_slot.rename"],
        "parameters": parameters,
        "current_metadata": parameters,
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_range_seed_command_candidate_uses_range_context_and_verifier() -> None:
    locators = [
        _listing_locator(row_key="row-1", kind="data", start_offset=0x20, end_offset=0x22),
        _listing_locator(row_key="row-2", kind="data", start_offset=0x22, end_offset=0x24),
    ]
    candidate = {
        "id": "range-string",
        "candidate_id": "range-string",
        "kind": "range_data_seed",
        "locators": locators,
        "suggested_action_kinds": ["range.seed.data.string"],
        "parameters": {"seed_kind": "data", "data_role": "string", "unit": "byte", "encoding": "ascii"},
        "confidence": "high",
        "actionable": True,
    }
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = [candidate]
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]

    command = reversing_loop._candidate_command_options(candidate)[0]
    selected = reversing_loop._select_command_action(inspect_report)

    assert command == {
        "kind": "command",
        "command_id": "range.seed.data.string",
        "context": {"kind": "range", "locators": locators},
        "parameters": {"seed_kind": "data", "data_role": "string", "unit": "byte", "encoding": "ascii"},
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "manual_seed_state"
    assert selected is not None
    assert selected["command"]["command_id"] == "range.seed.data.string"


def test_range_command_availability_query_uses_range_context() -> None:
    locators = [
        _listing_locator(row_key="row-1", kind="data", start_offset=0x20, end_offset=0x22),
        _listing_locator(row_key="row-2", kind="data", start_offset=0x22, end_offset=0x24),
    ]

    assert reversing_loop._command_query_from_context({"kind": "range", "locators": locators}) == {
        "context": ["range"],
        "locators": [json.dumps(locators)],
    }


def test_review_data_role_seed_candidate_uses_review_item_context() -> None:
    candidate = {
        "id": "review-data-named",
        "candidate_id": "review-data-named",
        "kind": "manual_review_item",
        "review_item_kind": "unreconciled_data_range",
        "durable_id": "unreconciled:h0:00000004-00000008",
        "suggested_action_kinds": ["review.seed.data.named"],
        "parameters": {"name": "manual_gap"},
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "review.seed.data.named",
        "context": {
            "kind": "review_item",
            "item_id": "unreconciled:h0:00000004-00000008",
            "review_item_kind": "unreconciled_data_range",
        },
        "parameters": {"name": "manual_gap"},
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "manual_seed_state"


def test_review_label_candidate_uses_review_item_context_and_manual_label_verifier() -> None:
    candidate = {
        "id": "review-label-rename",
        "candidate_id": "review-label-rename",
        "kind": "manual_review_item",
        "review_item_kind": "label_scope_conflict",
        "durable_id": "label_scope_conflict:l1:missing-owner",
        "suggested_action_kinds": ["review.label.rename"],
        "parameters": {"name": "renamed_label"},
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "review.label.rename",
        "context": {
            "kind": "review_item",
            "item_id": "label_scope_conflict:l1:missing-owner",
            "review_item_kind": "label_scope_conflict",
        },
        "parameters": {"name": "renamed_label"},
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "manual_label_state"


def test_review_seed_remove_candidate_uses_review_item_context() -> None:
    candidate = {
        "id": "review-seed-remove",
        "candidate_id": "review-seed-remove",
        "kind": "manual_review_item",
        "review_item_kind": "manual_seed_conflict",
        "durable_id": "manual_seed_conflict:data-as-code:entry",
        "suggested_action_kinds": ["review.seed.remove"],
        "parameters": {"seed_id": "data-as-code"},
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "review.seed.remove",
        "context": {
            "kind": "review_item",
            "item_id": "manual_seed_conflict:data-as-code:entry",
            "review_item_kind": "manual_seed_conflict",
        },
        "parameters": {"seed_id": "data-as-code"},
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "manual_seed_state"


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
        "default_verifier": "projected_data_symbol_name",
        "verifier": {"kind": "projected_data_symbol_name", "requires_semantic_reload": True},
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
        "default_verifier": "suppressed_seeded_item",
        "verifier": {"kind": "suppressed_seeded_item", "requires_semantic_reload": True},
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
        "default_verifier": "rsset_region_state",
        "verifier": {"kind": "rsset_region_state", "requires_semantic_reload": True},
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
        "default_verifier": "rsset_region_state",
        "verifier": {"kind": "rsset_region_state", "requires_semantic_reload": True},
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


def _semantic_hint_payload() -> dict[str, object]:
    return {
        "semantic_hint_id": "hint-1",
        "hunk": 0,
        "addr": 0,
        "element_kind": "immediate",
        "domain": "lvo",
        "symbol": "exec.library/OpenLibrary",
        "value": -552,
        "namespace": "exec.library",
        "function": "OpenLibrary",
        "element_id": "row-1:immediate:0:-552",
        "operand_index": 0,
    }


def _execution_view_payload() -> dict[str, object]:
    return {
        "source_start": 0x20,
        "source_end": 0x80,
        "base_addr": 0x4000,
        "name": "stage_code",
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


def _executed_execution_view_payload(tmp_path: Path) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    return {
        "action": {"action_id": "manual-1", "payload": {"execution_view": _execution_view_payload()}},
        "application": {
            "local_effects": [{"kind": "execution_view", "execution_view": _execution_view_payload()}],
        },
        "mutation": {
            "durable_action_id": "manual-1",
            "manual_action_log_count": state["count"],
            "manual_action_log_head_hash": state["head_hash"],
            "effective_metadata_hash": "f" * 64,
            "affected_locators": [],
            "projection_hash": "projection-1",
        },
        "workflow_profile": {"workflow_id": "manual_command_execution", "spans": []},
    }


def _executed_execution_view_remove_payload(tmp_path: Path) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    view = {
        "source_start": 0x20,
        "source_end": 0x80,
        "base_addr": 0x4000,
    }
    return {
        "action": {"action_id": "manual-1", "payload": {"execution_view": view}},
        "application": {
            "local_effects": [{"kind": "execution_view_remove", "execution_view": view}],
        },
        "mutation": {
            "durable_action_id": "manual-1",
            "manual_action_log_count": state["count"],
            "manual_action_log_head_hash": state["head_hash"],
            "effective_metadata_hash": "f" * 64,
            "affected_locators": [],
            "projection_hash": "projection-1",
        },
        "workflow_profile": {"workflow_id": "manual_command_execution", "spans": []},
    }


def _executed_semantic_hint_payload(tmp_path: Path) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    return {
        "action": {"action_id": "manual-1", "payload": {"semantic_hint": _semantic_hint_payload()}},
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


def _executed_register_seed_payload(tmp_path: Path, register_seed: dict[str, object]) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    return {
        "action": {"action_id": "manual-1", "register_seed": dict(register_seed)},
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


def _executed_target_equate_payload(
    tmp_path: Path,
    target_equate: dict[str, object],
    *,
    removed: bool = False,
) -> dict[str, object]:
    payload = _executed_command_payload()
    payload["action"] = {"action_id": "manual-1", "payload": {"target_equate": dict(target_equate)}}
    payload["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    payload["application"] = {
        "status": "applied",
        "local_effects": [
            {
                "kind": "target_equate_remove" if removed else "target_equate",
                "target_equate": dict(target_equate),
            }
        ],
    }
    return payload


def _executed_rsset_region_payload(
    tmp_path: Path,
    rsset_layout_region: dict[str, object],
    *,
    removed: bool = False,
) -> dict[str, object]:
    payload = _executed_command_payload()
    payload["action"] = {"action_id": "manual-1", "payload": {"rsset_layout_region": dict(rsset_layout_region)}}
    payload["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    payload["application"] = {
        "status": "applied",
        "local_effects": [
            {
                "kind": "rsset_layout_region_remove" if removed else "rsset_layout_region",
                "rsset_layout_region": dict(rsset_layout_region),
            }
        ],
    }
    return payload


def _executed_manual_seed_payload(tmp_path: Path, seed: dict[str, object]) -> dict[str, object]:
    payload = _executed_command_payload()
    payload["action"] = {"action_id": "manual-1", "payload": {"seed": dict(seed)}}
    payload["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    payload["application"] = {"status": "applied", "refresh": {"mode": "project"}}
    return payload


def _executed_manual_seed_remove_payload(tmp_path: Path, seed_id: str) -> dict[str, object]:
    payload = _executed_command_payload()
    payload["action"] = {"action_id": "manual-1", "payload": {"seed_id": seed_id}}
    payload["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    payload["application"] = {"status": "applied", "refresh": {"mode": "project"}}
    return payload


def _executed_manual_label_payload(tmp_path: Path, label_payload: dict[str, object]) -> dict[str, object]:
    payload = _executed_command_payload()
    payload["action"] = {"action_id": "manual-1", "payload": dict(label_payload)}
    payload["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    payload["application"] = {"status": "applied", "refresh": {"mode": "project"}}
    return payload


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


def _struct_pointer_row() -> dict[str, object]:
    row = _listing_row(text="\tmove.w 36(a0),d0\n", end_offset=2)
    row.update(
        {
            "opcode_or_directive": "move.w",
            "operand_text": "36(a0),d0",
            "operand_parts": [
                {"kind": "register", "operand_index": 0, "register": "A0", "metadata": {}},
                {"kind": "register", "operand_index": 1, "register": "D0", "metadata": {}},
            ],
            "operand_accesses": ["memory_read", "register_write"],
            "operand_registers": ["A0", "D0"],
            "unresolved_typed_accesses": [
                {
                    "operand_index": 0,
                    "base_register": "A0",
                    "displacement": 36,
                    "struct_size": 22,
                    "root_struct_name": "InputEvent",
                    "refined_struct_name": "DerivedEvent",
                    "classification": "prefix_extension",
                }
            ],
        }
    )
    return row


def _library_base_row() -> dict[str, object]:
    row = _listing_row(text="\tjsr _LVOSetPointer(a6)\n", end_offset=4)
    row.update(
        {
            "opcode_or_directive": "jsr",
            "operand_text": "_LVOSetPointer(a6)",
            "operand_parts": [
                {
                    "kind": "symbol",
                    "operand_index": 0,
                    "symbol": "_LVOSetPointer",
                    "base_register": "A6",
                    "metadata": {"symbol": "_LVOSetPointer"},
                }
            ],
            "operand_accesses": ["call"],
            "operand_registers": ["A6"],
            "api_call": {"library": "intuition.library", "function": "SetPointer"},
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


def _rsset_region_navigation_payload() -> dict[str, object]:
    return {
        "groups": {
            "app-slot-regions": [
                {
                    "summary": "app_input_event: InputEvent $0100-$0116",
                    "match_text": "app_input_event",
                    "symbol": "app_input_event",
                    "offset": 0x100,
                    "size": 22,
                    "source": "platform_api_arg",
                    "confidence": "tool-inferred",
                    "struct_name": "InputEvent",
                    "row_index": 1,
                    "addr": 0x14,
                    "hunk_index": 0,
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


def _executed_seeded_item_suppression_payload(tmp_path: Path) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    suppressed_item = {"kind": "seeded_entity", "hunk": 0, "addr": 0x100}
    return {
        "action": {"action_id": "manual-1", "payload": {"suppressed_seeded_item": suppressed_item}},
        "application": {
            "local_effects": [
                {"kind": "seeded_item_suppression", "suppressed_seeded_item": suppressed_item},
            ]
        },
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
