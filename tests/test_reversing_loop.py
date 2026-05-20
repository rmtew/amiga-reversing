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
        (
            "row.data_block.element.bind_type",
            {"kind": "row"},
            {
                "layout_id": "ascii-hex",
                "offset": 0,
                "type_id": "InputEvent",
                "binding_kind": "custom_struct",
                "requires_source_evidence": True,
                "source_evidence_id": "prov-1",
                "source_family": "struct_pointer",
                "source_evidence_status": "reported",
            },
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


def test_typed_field_command_with_accepted_evidence_executes_and_verifies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    evidence = _accepted_struct_pointer_evidence()
    field = {
        "struct_name": "DerivedEvent",
        "offset": 36,
        "name": "de_Code",
        "type": "UWORD",
        "size": 2,
        **evidence,
    }
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    selected = {
        "work_item": inspect_report["candidate_work"][0],
        "command": {
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
            },
            "parameters": dict(field),
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
            manual_state={"custom_struct_fields": [{**field, "owner_action_id": "manual-1"}]},
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "typed_gap.field.add", "parameters": dict(field)}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            _write_manual_log(tmp_path)
            return {"data": _executed_custom_struct_field_payload(tmp_path, field)}
        if method == "GET" and path.endswith("/listing"):
            row = _listing_row(text="\tmove.w de_Code(a0),d0\n", start_offset=0, end_offset=2)
            row["typed_accesses"] = [
                {
                    "operand_index": 1,
                    "base_register": "A0",
                    "displacement": 36,
                    "field_offset": 36,
                    "root_struct_name": "InputEvent",
                    "refined_struct_name": "DerivedEvent",
                    "owner_struct_name": "DerivedEvent",
                    "field_name": "de_Code",
                    "field_expr": "de_Code",
                }
            ]
            return {"data": {"rows": [row]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["action_result"]["status"] == "executed"
    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "provenance_evidence",
        "semantic_reload",
        "rendered_source",
        "round_trip",
    ]


def test_custom_struct_field_verifier_rejects_mismatched_consumed_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    field = {
        "struct_name": "DerivedEvent",
        "offset": 36,
        "name": "de_Code",
        "type": "UWORD",
        "size": 2,
        **_accepted_struct_pointer_evidence(),
        "parent_evidence_ids": ["prov-parent-a"],
    }
    reloaded_field = {**field, "parent_evidence_ids": ["prov-parent-b"], "owner_action_id": "manual-1"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"custom_struct_fields": [reloaded_field]},
        ),
    )

    verification = reversing_loop._verify_project_custom_struct_field(
        "demo",
        "typed_gap.field.add",
        {**field, "owner_action_id": "manual-1"},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["matching_custom_struct_fields"] == []


def test_custom_struct_field_verifier_treats_parent_evidence_ids_as_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    field = {
        "struct_name": "DerivedEvent",
        "offset": 36,
        "name": "de_Code",
        "type": "UWORD",
        "size": 2,
        **_accepted_struct_pointer_evidence(),
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
        "owner_action_id": "manual-1",
    }
    reloaded_field = {**field, "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"]}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"custom_struct_fields": [reloaded_field]},
        ),
    )

    verification = reversing_loop._verify_project_custom_struct_field(
        "demo",
        "typed_gap.field.add",
        field,
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["matching_custom_struct_fields"] == [reloaded_field]


def test_custom_struct_field_verifier_requires_selected_field_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sparse_field = {"name": "de_Code", "owner_action_id": "manual-1"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"custom_struct_fields": [sparse_field]},
        ),
    )

    verification = reversing_loop._verify_project_custom_struct_field(
        "demo",
        "typed_gap.field.add",
        sparse_field,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["missing_identity_fields"] == ["struct_name", "offset"]
    assert verification["matching_custom_struct_fields"] == []


def test_custom_struct_field_remove_verifier_matches_cleanup_action_not_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    field = {
        "struct_name": "DerivedEvent",
        "offset": 36,
        "name": "de_Code",
        **_accepted_struct_pointer_evidence(),
    }
    removed_field = {
        **field,
        "owner_action_id": "manual-create",
        "cleanup_action_id": "manual-remove",
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"removed_custom_struct_fields": [removed_field]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_custom_struct_field_rendered_source",
        lambda target_id, command, command_id, expected, **kwargs: {"layer": "rendered_source", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_custom_struct_field_mutation(
        "demo",
        {"command_id": "typed_access.field.remove"},
        "typed_access.field.remove",
        {"action": {"action_id": "manual-remove", "payload": {"custom_struct_field": field}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_custom_struct_field"]["cleanup_action_id"] == "manual-remove"
    assert "owner_action_id" not in semantic_layer["expected_custom_struct_field"]


def test_custom_struct_field_rename_render_verifier_accepts_clean_selected_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {
        "command_id": "typed_access.field.rename",
        "context": {
            "locator": _listing_locator(),
            "operand_index": 0,
            "field_name": "LIB_VERSION",
        },
        "parameters": {"name": "LIB_REVISION"},
    }
    expected = {"struct_name": "Library", "offset": 20, "name": "LIB_REVISION"}
    row = _listing_row(text="\tmove.w LIB_REVISION(a0),d0\n", start_offset=0, end_offset=2)
    row["typed_accesses"] = [
        {
            "operand_index": 0,
            "displacement": 20,
            "owner_struct_name": "Library",
            "field_name": "LIB_REVISION",
            "field_expr": "LIB_REVISION",
        }
    ]

    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {"data": {"rows": [row]}},
    )

    verification = reversing_loop._verify_projected_custom_struct_field_rendered_source(
        "demo",
        command,
        "typed_access.field.rename",
        expected,
    )

    assert verification["status"] == "passed"
    assert verification["matched_tokens"] == ["LIB_REVISION"]
    assert verification["stale_typed_accesses"] == []


def test_custom_struct_field_rename_render_verifier_rejects_stale_selected_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {
        "command_id": "typed_access.field.rename",
        "context": {
            "locator": _listing_locator(),
            "operand_index": 0,
            "field_name": "LIB_VERSION",
        },
        "parameters": {"name": "LIB_REVISION"},
    }
    expected = {"struct_name": "Library", "offset": 20, "name": "LIB_REVISION"}
    row = _listing_row(text="\tmove.w LIB_REVISION(a0),d0\n", start_offset=0, end_offset=2)
    row["typed_accesses"] = [
        {
            "operand_index": 0,
            "displacement": 20,
            "owner_struct_name": "Library",
            "field_name": "LIB_REVISION",
            "field_expr": "LIB_REVISION",
        },
        {
            "operand_index": 0,
            "displacement": 20,
            "owner_struct_name": "Library",
            "field_name": "LIB_VERSION",
            "field_expr": "LIB_VERSION",
        },
    ]

    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {"data": {"rows": [row]}},
    )

    verification = reversing_loop._verify_projected_custom_struct_field_rendered_source(
        "demo",
        command,
        "typed_access.field.rename",
        expected,
    )

    assert verification["status"] == "failed"
    assert verification["matched_tokens"] == ["LIB_REVISION"]
    assert verification["stale_tokens"] == []
    assert [access["field_name"] for access in verification["stale_typed_accesses"]] == ["LIB_VERSION"]


def test_custom_struct_field_rename_render_verifier_requires_previous_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {
        "command_id": "typed_access.field.rename",
        "context": {
            "locator": _listing_locator(),
            "operand_index": 0,
        },
        "parameters": {"name": "LIB_REVISION"},
    }
    expected = {"struct_name": "Library", "offset": 20, "name": "LIB_REVISION"}
    row = _listing_row(text="\tmove.w LIB_REVISION(a0),d0\n", start_offset=0, end_offset=2)
    row["typed_accesses"] = [
        {
            "operand_index": 0,
            "displacement": 20,
            "owner_struct_name": "Library",
            "field_name": "LIB_REVISION",
            "field_expr": "LIB_REVISION",
        }
    ]

    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {"data": {"rows": [row]}},
    )

    verification = reversing_loop._verify_projected_custom_struct_field_rendered_source(
        "demo",
        command,
        "typed_access.field.rename",
        expected,
    )

    assert verification["status"] == "failed"
    assert verification["message"] == "previous custom struct field name missing for rename proof"
    assert verification["matching_typed_accesses"]


def test_custom_struct_field_remove_render_verifier_checks_affected_locators(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {
        "command_id": "typed_access.field.remove",
        "context": {
            "locator": _listing_locator(start_offset=0, end_offset=2),
            "operand_index": 0,
        },
    }
    expected = {"struct_name": "DerivedEvent", "offset": 36, "name": "de_Code"}
    selected_row = _listing_row(text="\tmove.w 36(a0),d0\n", start_offset=0, end_offset=2)
    stale_propagated_row = _listing_row(
        row_key="row-2",
        text="\tmove.w de_Code(a1),d1\n",
        start_offset=8,
        end_offset=10,
    )
    stale_propagated_row["typed_accesses"] = [
        {
            "operand_index": 1,
            "displacement": 36,
            "owner_struct_name": "DerivedEvent",
            "field_name": "de_Code",
            "field_expr": "de_Code",
        }
    ]
    durable_result = {
        "mutation": {
            "affected_locators": [
                _listing_locator(start_offset=0, end_offset=2),
                _listing_locator(row_key="row-2", start_offset=8, end_offset=10),
            ]
        }
    }

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        source_offset = int(query["source_offset"][0])
        return {"data": {"rows": [selected_row if source_offset == 0 else stale_propagated_row]}}

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    verification = reversing_loop._verify_projected_custom_struct_field_rendered_source(
        "demo",
        command,
        "typed_access.field.remove",
        expected,
        durable_result=durable_result,
    )

    assert verification["status"] == "failed"
    assert verification["checked_source_locations"] == [
        {"section_index": 0, "source_offset": 0},
        {"section_index": 0, "source_offset": 8},
    ]
    assert [access["field_name"] for access in verification["matching_typed_accesses"]] == ["de_Code"]


def test_custom_struct_field_remove_render_verifier_requires_restored_numeric_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {
        "command_id": "typed_access.field.remove",
        "context": {
            "locator": _listing_locator(start_offset=0, end_offset=2),
            "operand_index": 0,
            "base_register": "A0",
        },
    }
    expected = {"struct_name": "DerivedEvent", "offset": 36, "name": "de_Code"}
    row = _listing_row(text="\tmove.w d0,d1\n", start_offset=0, end_offset=2)

    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {"data": {"rows": [row]}},
    )

    verification = reversing_loop._verify_projected_custom_struct_field_rendered_source(
        "demo",
        command,
        "typed_access.field.remove",
        expected,
    )

    assert verification["status"] == "failed"
    assert verification["expected_restore_tokens"] == [
        "36(a0)",
        "36(A0)",
        "$24(a0)",
        "$24(A0)",
        "$0024(a0)",
        "$0024(A0)",
        "$00000024(a0)",
        "$00000024(A0)",
    ]
    assert verification["matched_restore_tokens"] == []


def test_custom_struct_field_remove_render_verifier_rejects_zero_offset_symbol_restore(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {
        "command_id": "typed_access.field.remove",
        "context": {
            "locator": _listing_locator(start_offset=0, end_offset=2),
            "operand_index": 0,
            "base_register": "A0",
        },
    }
    expected = {"struct_name": "DerivedEvent", "offset": 0, "name": "de_Header"}
    row = _listing_row(text="\tmove.w other_field(a0),d0\n", start_offset=0, end_offset=2)

    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {"data": {"rows": [row]}},
    )

    verification = reversing_loop._verify_projected_custom_struct_field_rendered_source(
        "demo",
        command,
        "typed_access.field.remove",
        expected,
    )

    assert verification["status"] == "failed"
    assert verification["expected_restore_tokens"] == ["(a0)", "(A0)"]
    assert verification["matched_restore_tokens"] == []


def test_custom_struct_field_rename_render_verifier_checks_affected_locators(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {
        "command_id": "typed_access.field.rename",
        "context": {
            "locator": _listing_locator(start_offset=0, end_offset=2),
            "operand_index": 0,
            "field_name": "de_Code",
        },
        "parameters": {"name": "de_Command"},
    }
    expected = {"struct_name": "DerivedEvent", "offset": 36, "name": "de_Command"}
    selected_row = _listing_row(text="\tmove.w de_Command(a0),d0\n", start_offset=0, end_offset=2)
    selected_row["typed_accesses"] = [
        {
            "operand_index": 0,
            "displacement": 36,
            "owner_struct_name": "DerivedEvent",
            "field_name": "de_Command",
            "field_expr": "de_Command",
        }
    ]
    stale_propagated_row = _listing_row(
        row_key="row-2",
        text="\tmove.w de_Code(a1),d1\n",
        start_offset=8,
        end_offset=10,
    )
    stale_propagated_row["typed_accesses"] = [
        {
            "operand_index": 1,
            "displacement": 36,
            "owner_struct_name": "DerivedEvent",
            "field_name": "de_Code",
            "field_expr": "de_Code",
        }
    ]
    durable_result = {
        "mutation": {
            "affected_locators": [
                _listing_locator(start_offset=0, end_offset=2),
                _listing_locator(row_key="row-2", start_offset=8, end_offset=10),
            ]
        }
    }

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        source_offset = int(query["source_offset"][0])
        return {"data": {"rows": [selected_row if source_offset == 0 else stale_propagated_row]}}

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    verification = reversing_loop._verify_projected_custom_struct_field_rendered_source(
        "demo",
        command,
        "typed_access.field.rename",
        expected,
        durable_result=durable_result,
    )

    assert verification["status"] == "failed"
    assert verification["matched_tokens"] == ["de_Command"]
    assert [access["field_name"] for access in verification["stale_typed_accesses"]] == ["de_Code"]


def test_provenance_backed_mutation_verifier_requires_accepted_evidence() -> None:
    command = {
        "command_id": "row.data_block.element.interpret_ref",
        "parameters": {"source_evidence_id": "prov-demo-unknown"},
    }
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "data_block_interpreted_ref": {
                    "source_evidence_id": "prov-demo-unknown",
                    "source_family": "unknown",
                    "source_evidence_status": "unresolved",
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    provenance_layer = report["layers"][1]
    assert report["status"] == "failed"
    assert provenance_layer["layer"] == "provenance_evidence"
    assert provenance_layer["status"] == "failed"
    assert "source_evidence_status is not accepted" in provenance_layer["failures"]
    assert "missing path_lifetime_scope" in provenance_layer["failures"]


def test_provenance_backed_mutation_verifier_accepts_scoped_evidence() -> None:
    command = {"command_id": "row.data_block.element.interpret_ref"}
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "data_block_interpreted_ref": {
                    "source_evidence_id": "prov-demo-rsset-path",
                    "source_family": "rsset_app_base",
                    "source_evidence_status": "path_specific",
                    "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x120},
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    provenance_layer = report["layers"][1]
    assert report["status"] == "passed"
    assert provenance_layer["layer"] == "provenance_evidence"
    assert provenance_layer["status"] == "passed"
    assert provenance_layer["owner_action_id"] == "action-1"


def test_provenance_backed_mutation_verifier_rejects_mismatched_command_evidence() -> None:
    command = {
        "command_id": "row.data_block.element.interpret_ref",
        "parameters": {"source_evidence_id": "prov-command"},
    }
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "data_block_interpreted_ref": {
                    "source_evidence_id": "prov-durable",
                    "source_family": "rsset_app_base",
                    "source_evidence_status": "path_specific",
                    "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x120},
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    provenance_layer = report["layers"][1]
    assert report["status"] == "failed"
    assert provenance_layer["source_evidence_id"] == "prov-durable"
    assert provenance_layer["expected_source_evidence_id"] == "prov-command"
    assert "durable source_evidence_id does not match consumed command evidence" in provenance_layer["failures"]


def test_provenance_backed_mutation_verifier_rejects_mismatched_command_scope() -> None:
    command = {
        "command_id": "row.data_block.element.bind_type",
        "parameters": {
            "source_evidence_id": "prov-command",
            "source_family": "data_block_pointer",
            "source_evidence_status": "analysis_proven",
            "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x40},
            "parent_evidence_ids": ["prov-parent-a"],
        },
    }
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "data_block_element": {
                    "type_binding": {
                        "source_evidence_id": "prov-command",
                        "source_family": "data_block_pointer",
                        "source_evidence_status": "analysis_proven",
                        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x44},
                        "parent_evidence_ids": ["prov-parent-b"],
                    }
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    provenance_layer = report["layers"][1]
    assert report["status"] == "failed"
    assert "durable path_lifetime_scope does not match consumed command evidence" in provenance_layer["failures"]
    assert "durable parent_evidence_ids does not match consumed command evidence" in provenance_layer["failures"]


def test_provenance_backed_mutation_verifier_treats_parent_evidence_ids_as_set() -> None:
    command = {
        "command_id": "row.data_block.element.bind_type",
        "parameters": {
            "source_evidence_id": "prov-command",
            "source_family": "data_block_pointer",
            "source_evidence_status": "analysis_proven",
            "path_lifetime_scope": {"kind": "global"},
            "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
        },
    }
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "data_block_element": {
                    "type_binding": {
                        "source_evidence_id": "prov-command",
                        "source_family": "data_block_pointer",
                        "source_evidence_status": "analysis_proven",
                        "path_lifetime_scope": {"kind": "global"},
                        "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"],
                    }
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    assert report["status"] == "passed"
    assert report["layers"][1]["status"] == "passed"


def test_provenance_backed_mutation_verifier_rejects_mismatched_context_evidence() -> None:
    command = {
        "command_id": "typed_gap.field.add",
        "context": {
            "source_evidence_id": "prov-context",
            "source_family": "struct_pointer",
            "source_evidence_status": "analysis_proven",
            "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x120},
            "parent_evidence_ids": ["prov-context-parent"],
        },
    }
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "custom_struct_field": {
                    "source_evidence_id": "prov-durable",
                    "source_family": "struct_pointer",
                    "source_evidence_status": "analysis_proven",
                    "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x120},
                    "parent_evidence_ids": ["prov-context-parent"],
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    provenance_layer = report["layers"][1]
    assert report["status"] == "failed"
    assert provenance_layer["source_evidence_id"] == "prov-durable"
    assert provenance_layer["expected_source_evidence_id"] == "prov-context"
    assert "durable source_evidence_id does not match consumed command evidence" in provenance_layer["failures"]


def test_provenance_backed_mutation_verifier_ignores_cleanup_scope_evidence_id_as_consumed() -> None:
    command = {
        "command_id": "typed_gap.field.add",
        "parameters": {"cleanup_scope": {"kind": "owned_descendants", "source_evidence_id": "prov-old"}},
    }
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "custom_struct_field": {
                    "source_evidence_id": "prov-new",
                    "source_family": "struct_pointer",
                    "source_evidence_status": "analysis_proven",
                    "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x120},
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    provenance_layer = report["layers"][1]
    assert report["status"] == "passed"
    assert provenance_layer["source_evidence_id"] == "prov-new"
    assert provenance_layer["expected_source_evidence_id"] is None


def test_provenance_backed_mutation_verifier_ignores_durable_cleanup_scope_as_consumed() -> None:
    command = {"command_id": "typed_access.field.remove"}
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "custom_struct_field": {
                    "struct_name": "InputEvent",
                    "offset": 0x24,
                    "cleanup_scope": {"kind": "owned_descendants", "source_evidence_id": "prov-old"},
                    "cleanup_action_id": "action-1",
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    assert report == verification


def test_provenance_backed_mutation_verifier_requires_override_cleanup_scope() -> None:
    command = {"command_id": "typed_gap.field.add"}
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "custom_struct_field": {
                    "source_evidence_id": "prov-demo-override",
                    "source_family": "struct_pointer",
                    "source_evidence_status": "manual_override",
                    "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x120},
                    "contradicted_evidence_id": "prov-old",
                    "reason": "target-specific path proof",
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    provenance_layer = report["layers"][1]
    assert report["status"] == "failed"
    assert provenance_layer["layer"] == "provenance_evidence"
    assert "manual_override missing cleanup_scope" in provenance_layer["failures"]


def test_provenance_backed_mutation_verifier_accepts_override_cleanup_scope() -> None:
    cleanup_scope = {"kind": "owned_descendants", "source_evidence_id": "prov-old"}
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "custom_struct_field": {
                    "source_evidence_id": "prov-demo-override",
                    "source_family": "struct_pointer",
                    "source_evidence_status": "manual_override",
                    "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x120},
                    "contradicted_evidence_id": "prov-old",
                    "reason": "target-specific path proof",
                    "cleanup_scope": cleanup_scope,
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(
        {"command_id": "typed_gap.field.add"},
        durable_result,
        verification,
    )

    provenance_layer = report["layers"][1]
    assert report["status"] == "passed"
    assert provenance_layer["status"] == "passed"
    assert provenance_layer["cleanup_scope"] == cleanup_scope


def test_provenance_backed_mutation_verifier_rejects_override_cleanup_scope_mismatch() -> None:
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "custom_struct_field": {
                    "source_evidence_id": "prov-demo-override",
                    "source_family": "struct_pointer",
                    "source_evidence_status": "manual_override",
                    "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x120},
                    "contradicted_evidence_id": "prov-old",
                    "reason": "target-specific path proof",
                    "cleanup_scope": {"kind": "owned_descendants", "source_evidence_id": "prov-other"},
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(
        {"command_id": "typed_gap.field.add"},
        durable_result,
        verification,
    )

    provenance_layer = report["layers"][1]
    assert report["status"] == "failed"
    assert "manual_override cleanup_scope does not match contradicted evidence" in provenance_layer["failures"]


def test_provenance_backed_mutation_verifier_rejects_command_only_evidence() -> None:
    command = {
        "command_id": "row.data_block.element.interpret_ref",
        "parameters": {"source_evidence_id": "prov-demo-rsset-path"},
    }
    durable_result = {"action": {"action_id": "action-1", "payload": {"data_block_interpreted_ref": {}}}}
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    provenance_layer = report["layers"][1]
    assert report["status"] == "failed"
    assert provenance_layer["layer"] == "provenance_evidence"
    assert "durable action payload missing consumed source_evidence_id" in provenance_layer["failures"]


def test_provenance_backed_mutation_verifier_ignores_nested_reference_evidence_as_consumed() -> None:
    command = {
        "command_id": "rsset.binding.bind",
        "parameters": {"source_evidence_id": "prov-demo-rsset-path"},
    }
    accepted_ref = {
        "source_evidence_id": "prov-demo-rsset-path",
        "source_family": "rsset_app_base",
        "status": "path_specific",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x120},
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "accepted": True,
    }
    durable_result = {
        "action": {
            "action_id": "action-1",
            "payload": {
                "rsset_use_site_binding": {
                    "base_evidence_id": "selected-base:A6:__amiga_app_base__",
                    "base_evidence_refs": [accepted_ref],
                }
            },
        }
    }
    verification = {"status": "passed", "layers": [{"layer": "manual_action_log", "status": "passed"}]}

    report = reversing_loop._verify_provenance_backed_mutation(command, durable_result, verification)

    provenance_layer = report["layers"][1]
    assert report["status"] == "failed"
    assert provenance_layer["layer"] == "provenance_evidence"
    assert "durable action payload missing consumed source_evidence_id" in provenance_layer["failures"]


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


def test_run_one_data_block_layout_executes_with_layout_state_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locators = [
        _listing_locator(row_key="row-1", kind="data", start_offset=0x20, end_offset=0x22),
        _listing_locator(row_key="row-2", kind="data", start_offset=0x22, end_offset=0x24),
    ]
    layout = {
        "layout_id": "ascii-hex",
        "hunk": 0,
        "source_start": 0x20,
        "source_end": 0x24,
        "name": "ascii_hex_digit_value",
        "role": "lookup_table",
        "default_unit": "byte",
    }
    candidate = {
        "id": "data-block-layout",
        "candidate_id": "data-block-layout",
        "kind": "data_block_layout",
        "locators": locators,
        "suggested_action_kinds": ["range.data_block.layout.create"],
        "parameters": {"name": "ascii_hex_digit_value", "role": "lookup_table", "default_unit": "byte"},
        "confidence": "high",
        "actionable": True,
    }
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = [candidate]
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    selected = {
        "work_item": candidate,
        "command": {
            "kind": "command",
            "command_id": "range.data_block.layout.create",
            "context": {"kind": "range", "locators": locators},
            "parameters": {"name": "ascii_hex_digit_value", "role": "lookup_table", "default_unit": "byte"},
            "output_affecting": True,
        },
    }
    assert reversing_loop._candidate_verifier(candidate, selected["command"]) == "data_block_layout_state"
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"data_block_layouts": [layout]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            assert query == {"context": ["range"], "locators": [json.dumps(locators)]}
            return {"data": {"commands": [{"command_id": "range.data_block.layout.create"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "range.data_block.layout.create"
            assert body["context"] == {"kind": "range", "locators": locators}
            _write_manual_log(tmp_path)
            return {"data": _executed_data_block_layout_payload(tmp_path, layout)}
        if method == "GET" and path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(
                            row_key="row-1",
                            kind="label",
                            label="ascii_hex_digit_value",
                            start_offset=0x20,
                            end_offset=0x20,
                        ),
                        _listing_row(
                            row_key="row-2",
                            kind="data",
                            text="\tdcb.b $30,$FF\t; lookup_table\n",
                            start_offset=0x20,
                            end_offset=0x24,
                        ),
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["verification"]["layers"][1]["state_key"] == "data_block_layouts"
    assert report["verification"]["layers"][2]["layer"] == "rendered_source"
    assert report["verification"]["layers"][2]["matched_tokens"] == ["ascii_hex_digit_value", "lookup_table"]
    assert report["action"]["command_id"] == "range.data_block.layout.create"


def test_data_block_layout_verifier_rejects_sparse_create_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = {
        "layout_id": "ascii-hex",
        "hunk": 0,
        "source_start": 0x20,
        "source_end": 0x24,
        "name": "ascii_hex_digit_value",
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"data_block_layouts": [layout]}),
    )

    verification = reversing_loop._verify_project_data_block_layout(
        "demo",
        "range.data_block.layout.create",
        {"layout_id": "ascii-hex"},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["message"] == "data block layout payload missing source identity"
    assert verification["missing_identity_fields"] == ["hunk", "source_start", "source_end"]


def test_run_one_data_block_element_executes_with_element_state_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locator = _listing_locator(kind="data", start_offset=0x20, end_offset=0x22)
    element = {
        "data_block_element_id": "ascii-hex:30",
        "layout_id": "ascii-hex",
        "offset": 0x30,
        "width": 2,
        "kind": "array",
        "name": "digits",
        "representation": "character",
    }
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    selected = {
        "work_item": {
            "id": "data-block-element",
            "kind": "data_block_element",
            "locator": locator,
            "suggested_action_kinds": ["row.data_block.element.set"],
            "confidence": "high",
            "actionable": True,
        },
        "command": {
            "kind": "command",
            "command_id": "row.data_block.element.set",
            "context": {"kind": "row", "locator": locator},
            "parameters": {
                "layout_id": "ascii-hex",
                "offset": 0x30,
                "width": 2,
                "kind": "array",
                "name": "digits",
                "representation": "character",
            },
            "output_affecting": True,
        },
    }
    assert reversing_loop._candidate_verifier(selected["work_item"], selected["command"]) == "data_block_element_state"
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"data_block_elements": [element]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": "row.data_block.element.set"}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "row.data_block.element.set"
            _write_manual_log(tmp_path)
            return {"data": _executed_data_block_element_payload(tmp_path, element)}
        if method == "GET" and path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(
                            kind="data",
                            text="digits:\n\tdc.b '0','1'\n",
                            start_offset=0x20,
                            end_offset=0x22,
                        )
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["verification"]["layers"][1]["state_key"] == "data_block_elements"
    assert report["verification"]["layers"][2]["layer"] == "rendered_source"
    assert report["verification"]["layers"][2]["matched_tokens"] == ["digits", "dc.b", "'"]
    assert report["action"]["command_id"] == "row.data_block.element.set"


def test_run_one_data_block_type_binding_requires_rendered_type_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locator = _listing_locator(kind="data", start_offset=0x20, end_offset=0x24)
    type_binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "source_evidence_id": "prov-1",
        "source_family": "data_block_pointer",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "global"},
        "parent_evidence_ids": ["prov-table-base"],
        "owner_action_id": "manual-1",
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": type_binding,
    }
    selected = {
        "work_item": {
            "id": "data-block-type-binding",
            "kind": "data_block_type_binding",
            "locator": locator,
            "suggested_action_kinds": ["row.data_block.element.bind_type"],
            "confidence": "high",
            "actionable": True,
        },
        "command": {
            "kind": "command",
            "command_id": "row.data_block.element.bind_type",
            "context": {"kind": "row", "locator": locator},
            "parameters": {
                "layout_id": "events",
                "offset": 0x30,
                "width": 4,
                "binding_kind": "platform_struct",
                "type_id": "Node",
                "source_evidence_id": "prov-1",
                "source_family": "data_block_pointer",
                "source_evidence_status": "analysis_proven",
                "path_lifetime_scope": {"kind": "global"},
                "parent_evidence_ids": ["prov-table-base"],
                "requires_source_evidence": True,
            },
            "output_affecting": True,
        },
    }
    assert reversing_loop._candidate_verifier(selected["work_item"], selected["command"]) == "data_block_element_state"
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"data_block_elements": [element]}),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_data_block_type_binding_descendants",
        lambda target_id, command_id, expected, project_root: {"layer": "type_binding_descendants", "status": "passed"},
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {
                "data": {
                    "commands": [
                        {
                            "command_id": "row.data_block.element.bind_type",
                            "parameters": {
                                "layout_id": "events",
                                "offset": 0x30,
                                "width": 4,
                                "source_evidence_id": "prov-1",
                                "source_family": "data_block_pointer",
                                "source_evidence_status": "analysis_proven",
                                "path_lifetime_scope": {"kind": "global"},
                                "parent_evidence_ids": ["prov-table-base"],
                            },
                        }
                    ]
                }
            }
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "row.data_block.element.bind_type"
            _write_manual_log(tmp_path)
            return {"data": _executed_data_block_element_payload(tmp_path, element)}
        if method == "GET" and path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(
                            kind="data",
                            text="event_node:\n\tNode.b $00,$00,$00,$00\n",
                            start_offset=0x20,
                            end_offset=0x24,
                        )
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed", report["verification"]
    assert report["verification"]["layers"][1]["source_evidence_id"] == "prov-1"
    assert report["verification"]["layers"][3]["matched_tokens"] == ["Node"]
    assert report["action"]["command_id"] == "row.data_block.element.bind_type"


def test_data_block_type_availability_requires_matching_element_identity() -> None:
    command = {
        "command_id": "row.data_block.element.bind_type",
        "parameters": {
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            "binding_kind": "platform_struct",
            "type_id": "Node",
        },
    }
    availability = {
        "commands": [
            {
                "command_id": "row.data_block.element.bind_type",
                "parameters": {"layout_id": "events", "offset": 0x34, "width": 4},
            }
        ]
    }

    assert reversing_loop._available_catalog_command(command, availability) is None

    command_parameters = cast(dict[str, object], command["parameters"])
    del command_parameters["width"]

    assert reversing_loop._available_catalog_command(command, availability) is None

    command_parameters["width"] = 4
    availability_parameters = cast(dict[str, object], availability["commands"][0]["parameters"])
    availability_parameters["offset"] = 0x30

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]


def test_data_block_type_availability_requires_matching_source_evidence() -> None:
    evidence = {
        "source_evidence_id": "prov-1",
        "source_family": "data_block_pointer",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "global"},
        "parent_evidence_ids": ["prov-table-base", "prov-root"],
    }
    command = {
        "command_id": "row.data_block.element.bind_type",
        "parameters": {
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            "binding_kind": "platform_struct",
            "type_id": "Node",
            **evidence,
        },
    }
    availability = {
        "commands": [
            {
                "command_id": "row.data_block.element.bind_type",
                "parameters": {"layout_id": "events", "offset": 0x30, "width": 4},
            }
        ]
    }

    assert reversing_loop._available_catalog_command(command, availability) is None

    availability_parameters = cast(dict[str, object], availability["commands"][0]["parameters"])
    availability_parameters.update({**evidence, "source_evidence_id": "prov-other"})

    assert reversing_loop._available_catalog_command(command, availability) is None

    availability_parameters["source_evidence_id"] = "prov-1"

    availability_parameters["parent_evidence_ids"] = ["prov-other-base"]
    assert reversing_loop._available_catalog_command(command, availability) is None

    availability_parameters["parent_evidence_ids"] = ["prov-root", "prov-table-base"]

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]


def test_data_block_clear_type_availability_requires_matching_binding_identity() -> None:
    evidence = {
        "source_evidence_id": "prov-1",
        "source_family": "data_block_pointer",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "global"},
        "parent_evidence_ids": ["prov-table-base"],
    }
    command = {
        "command_id": "row.data_block.element.clear_type",
        "parameters": {
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            "type_binding_id": "events:30:4:platform_struct:Node",
            "binding_kind": "platform_struct",
            "bound_type_id": "Node",
            "owner_action_id": "manual-bind",
            **evidence,
        },
    }
    availability = {
        "commands": [
            {
                "command_id": "row.data_block.element.clear_type",
                "parameters": {
                    "layout_id": "events",
                    "offset": 0x30,
                    "width": 4,
                    "type_binding_id": "events:30:4:custom_struct:InputEvent",
                    "binding_kind": "custom_struct",
                    "bound_type_id": "InputEvent",
                    "owner_action_id": "manual-other",
                    **evidence,
                },
            }
        ]
    }

    assert reversing_loop._available_catalog_command(command, availability) is None

    availability_parameters = cast(dict[str, object], availability["commands"][0]["parameters"])
    availability_parameters.update(
        {
            "type_binding_id": "events:30:4:platform_struct:Node",
            "binding_kind": "platform_struct",
            "bound_type_id": "Node",
            "owner_action_id": "manual-bind",
            "parent_evidence_ids": ["prov-other-base"],
        }
    )

    assert reversing_loop._available_catalog_command(command, availability) is None

    availability_parameters["parent_evidence_ids"] = evidence["parent_evidence_ids"]

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]


def test_data_block_type_binding_verifier_requires_binding_owner_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    type_binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "owner_action_id": "manual-1",
        "source_evidence_id": "prov-node-base",
        "parent_evidence_ids": ["prov-root"],
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": type_binding,
    }
    reloaded_element = {
        **element,
        "type_binding": {**type_binding, "owner_action_id": "manual-other"},
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"data_block_elements": [reloaded_element]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_data_block_type_binding_rendered_source",
        lambda target_id, command, command_id, expected, project_root: {"layer": "rendered_source", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_data_block_type_binding_descendants",
        lambda target_id, command_id, expected, project_root: {"layer": "type_binding_descendants", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_data_block_type_binding_mutation(
        "demo",
        {"command_id": "row.data_block.element.bind_type"},
        "row.data_block.element.bind_type",
        {"action": {"action_id": "manual-1", "payload": {"data_block_element": element}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_data_block_element"]["type_binding"]["owner_action_id"] == "manual-1"
    assert semantic_layer["matching_data_block_elements"] == []


def test_data_block_type_binding_verifier_requires_complete_binding_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sparse_binding = {"type_binding_id": "events:30:4:platform_struct:Node", "owner_action_id": "manual-1"}
    sparse_element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": sparse_binding,
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"data_block_elements": [sparse_element]},
        ),
    )

    verification = reversing_loop._verify_project_data_block_element(
        "demo",
        "row.data_block.element.bind_type",
        sparse_element,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["missing_type_binding_identity_fields"] == [
        "type_binding.layout_id",
        "type_binding.element_offset",
        "type_binding.element_width",
        "type_binding.binding_kind",
        "type_binding.bound_type_or_domain_id",
    ]
    assert verification["matching_data_block_elements"] == []


def test_data_block_type_binding_verifier_rejects_parent_evidence_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    type_binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "source_evidence_id": "prov-1",
        "source_family": "data_block_pointer",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "global"},
        "parent_evidence_ids": ["prov-parent-a"],
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": type_binding,
    }
    reloaded_element = {
        **element,
        "type_binding": {
            **type_binding,
            "parent_evidence_ids": ["prov-parent-b"],
            "owner_action_id": "manual-1",
        },
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"data_block_elements": [reloaded_element]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_data_block_type_binding_rendered_source",
        lambda target_id, command, command_id, expected, project_root: {"layer": "rendered_source", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_data_block_type_binding_descendants",
        lambda target_id, command_id, expected, project_root: {"layer": "type_binding_descendants", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_data_block_type_binding_mutation(
        "demo",
        {"command_id": "row.data_block.element.bind_type"},
        "row.data_block.element.bind_type",
        {"action": {"action_id": "manual-1", "payload": {"data_block_element": element}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["matching_data_block_elements"] == []


def test_data_block_type_binding_verifier_treats_parent_evidence_ids_as_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    type_binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "source_evidence_id": "prov-1",
        "source_family": "data_block_pointer",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "global"},
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
        "owner_action_id": "manual-1",
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": type_binding,
    }
    reloaded_element = {
        **element,
        "type_binding": {**type_binding, "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"]},
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"data_block_elements": [reloaded_element]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_data_block_type_binding_rendered_source",
        lambda target_id, command, command_id, expected, project_root: {"layer": "rendered_source", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_data_block_type_binding_descendants",
        lambda target_id, command_id, expected, project_root: {"layer": "type_binding_descendants", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_data_block_type_binding_mutation(
        "demo",
        {"command_id": "row.data_block.element.bind_type"},
        "row.data_block.element.bind_type",
        {"action": {"action_id": "manual-1", "payload": {"data_block_element": element}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["layers"][1]["matching_data_block_elements"] == [reloaded_element]


def test_data_block_clear_type_verifier_requires_previous_binding_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locator = _listing_locator(kind="data", start_offset=0x20, end_offset=0x24)
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "scalar",
    }
    command = {
        "kind": "command",
        "command_id": "row.data_block.element.clear_type",
        "context": {"kind": "row", "locator": locator},
        "parameters": dict(element),
        "output_affecting": True,
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"data_block_elements": [element]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(
                            kind="data",
                            text="\tdc.l $00000000\n",
                            start_offset=0x20,
                            end_offset=0x24,
                        )
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)
    _write_manual_log(tmp_path)

    report = reversing_loop._verify_data_block_type_binding_mutation(
        "demo",
        command,
        "row.data_block.element.clear_type",
        _executed_data_block_element_payload(tmp_path, element),
        project_root=tmp_path,
    )

    assert report["status"] == "failed"
    assert report["layers"][2]["message"] == "clear_type requires previous type-binding render token"


def test_data_block_clear_type_verifier_requires_cleanup_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    previous_type_binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "owner_action_id": "manual-bind",
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "scalar",
        "previous_type_binding": previous_type_binding,
    }
    reloaded_element = {
        **element,
        "previous_type_binding": {**previous_type_binding, "cleanup_action_id": "manual-other"},
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"data_block_elements": [reloaded_element]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_data_block_type_binding_rendered_source",
        lambda target_id, command, command_id, expected, project_root: {"layer": "rendered_source", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_projected_data_block_type_binding_descendants",
        lambda target_id, command_id, expected, project_root: {"layer": "type_binding_descendants", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_data_block_type_binding_mutation(
        "demo",
        {"command_id": "row.data_block.element.clear_type"},
        "row.data_block.element.clear_type",
        {"action": {"action_id": "manual-clear", "payload": {"data_block_element": element}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert (
        semantic_layer["expected_data_block_element"]["previous_type_binding"]["cleanup_action_id"] == "manual-clear"
    )
    assert semantic_layer["matching_data_block_elements"] == []


def test_data_block_type_binding_descendant_verifier_requires_owned_entity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": binding,
    }
    descendant = SeededEntityMetadata(
        addr=0x20,
        end=0x24,
        hunk=0,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation="manual_action_log:events:30",
        source_id="manual_action_log",
        source_locator="events:30:4:platform_struct:Node",
        owner_action_id="manual-1",
        source_evidence_id="prov-node-base",
        parent_evidence_ids=("prov-root",),
        type="data",
        struct_name="Node",
        field_name="LN_SUCC",
    )
    monkeypatch.setattr(reversing_loop.projects, "resolve_project_dir", lambda target_id, project_root: tmp_path)
    monkeypatch.setattr(
        reversing_loop,
        "effective_target_metadata",
        lambda target_dir: TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(descendant,),
        ),
    )

    verification = reversing_loop._verify_projected_data_block_type_binding_descendants(
        "demo",
        "row.data_block.element.bind_type",
        element,
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["matching_seeded_entities"][0]["field_name"] == "LN_SUCC"
    assert verification["ownership_mismatches"] == []


def test_data_block_type_binding_descendant_verifier_treats_parent_evidence_ids_as_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "owner_action_id": "manual-1",
        "source_evidence_id": "prov-node-base",
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": binding,
    }
    descendant = SeededEntityMetadata(
        addr=0x20,
        end=0x24,
        hunk=0,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation="manual_action_log:events:30",
        source_id="manual_action_log",
        source_locator="events:30:4:platform_struct:Node",
        owner_action_id="manual-1",
        source_evidence_id="prov-node-base",
        parent_evidence_ids=("prov-parent-a", "prov-parent-b"),
        type="data",
        struct_name="Node",
        field_name="LN_SUCC",
    )
    monkeypatch.setattr(reversing_loop.projects, "resolve_project_dir", lambda target_id, project_root: tmp_path)
    monkeypatch.setattr(
        reversing_loop,
        "effective_target_metadata",
        lambda target_dir: TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(descendant,),
        ),
    )

    verification = reversing_loop._verify_projected_data_block_type_binding_descendants(
        "demo",
        "row.data_block.element.bind_type",
        element,
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["ownership_mismatches"] == []


def test_data_block_type_binding_descendant_verifier_rejects_wrong_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "owner_action_id": "manual-1",
        "source_evidence_id": "prov-node-base",
        "parent_evidence_ids": ["prov-root"],
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": binding,
    }
    descendant = SeededEntityMetadata(
        addr=0x20,
        end=0x24,
        hunk=0,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation="manual_action_log:events:30",
        source_id="manual_action_log",
        source_locator="events:30:4:platform_struct:Node",
        owner_action_id="manual-other",
        source_evidence_id="prov-node-base",
        parent_evidence_ids=("prov-root",),
        type="data",
        struct_name="Node",
        field_name="LN_SUCC",
    )
    monkeypatch.setattr(reversing_loop.projects, "resolve_project_dir", lambda target_id, project_root: tmp_path)
    monkeypatch.setattr(
        reversing_loop,
        "effective_target_metadata",
        lambda target_dir: TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(descendant,),
        ),
    )

    verification = reversing_loop._verify_projected_data_block_type_binding_descendants(
        "demo",
        "row.data_block.element.bind_type",
        element,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["ownership_mismatches"][0]["owner_action_id"] == "manual-other"


def test_data_block_type_binding_descendant_verifier_rejects_missing_owned_entity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "platform_struct",
        "type_binding": binding,
    }
    monkeypatch.setattr(reversing_loop.projects, "resolve_project_dir", lambda target_id, project_root: tmp_path)
    monkeypatch.setattr(
        reversing_loop,
        "effective_target_metadata",
        lambda target_dir: TargetMetadata(target_type="program", entry_register_seeds=()),
    )

    verification = reversing_loop._verify_projected_data_block_type_binding_descendants(
        "demo",
        "row.data_block.element.bind_type",
        element,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["matching_seeded_entities"] == []


def test_data_block_clear_type_descendant_verifier_rejects_stale_owned_entity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous_binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "scalar",
        "previous_type_binding": previous_binding,
    }
    descendant = SeededEntityMetadata(
        addr=0x20,
        end=0x24,
        hunk=0,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation="manual_action_log:events:30",
        source_id="manual_action_log",
        source_locator="events:30:4:platform_struct:Node",
        type="data",
        struct_name="Node",
        field_name="LN_SUCC",
    )
    monkeypatch.setattr(reversing_loop.projects, "resolve_project_dir", lambda target_id, project_root: tmp_path)
    monkeypatch.setattr(
        reversing_loop,
        "effective_target_metadata",
        lambda target_dir: TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(descendant,),
        ),
    )

    verification = reversing_loop._verify_projected_data_block_type_binding_descendants(
        "demo",
        "row.data_block.element.clear_type",
        element,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["matching_seeded_entities"][0]["source_locator"] == "events:30:4:platform_struct:Node"


def test_data_block_clear_type_descendant_verifier_rejects_stale_owner_without_locator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous_binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "layout_id": "events",
        "element_offset": 0x30,
        "element_width": 4,
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "owner_action_id": "manual-bind",
    }
    element = {
        "data_block_element_id": "events:30",
        "layout_id": "events",
        "offset": 0x30,
        "width": 4,
        "kind": "scalar",
        "previous_type_binding": previous_binding,
    }
    descendant = SeededEntityMetadata(
        addr=0x20,
        end=0x24,
        hunk=0,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation="manual_action_log:events:30",
        source_id="manual_action_log",
        source_locator=None,
        owner_action_id="manual-bind",
        type="data",
        struct_name="Node",
        field_name="LN_SUCC",
    )
    monkeypatch.setattr(reversing_loop.projects, "resolve_project_dir", lambda target_id, project_root: tmp_path)
    monkeypatch.setattr(
        reversing_loop,
        "effective_target_metadata",
        lambda target_dir: TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(descendant,),
        ),
    )

    verification = reversing_loop._verify_projected_data_block_type_binding_descendants(
        "demo",
        "row.data_block.element.clear_type",
        element,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["matching_seeded_entities"][0]["owner_action_id"] == "manual-bind"


@pytest.mark.parametrize(
    ("command_id", "element", "state_key"),
    [
        (
            "row.data_block.element.represent",
            {"layout_id": "ascii-hex", "offset": 0x30, "representation": "hex"},
            "data_block_elements",
        ),
        (
            "row.data_block.element.remove",
            {"layout_id": "ascii-hex", "offset": 0x30, "width": 2, "removal_state": "raw"},
            "removed_data_block_elements",
        ),
    ],
)
def test_run_one_data_block_element_update_commands_verify_expected_state(
    command_id: str,
    element: dict[str, object],
    state_key: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locator = _listing_locator(kind="data", start_offset=0x20, end_offset=0x22)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    selected = {
        "work_item": {
            "id": "data-block-element-update",
            "kind": "data_block_element",
            "locator": locator,
            "suggested_action_kinds": [command_id],
            "confidence": "high",
            "actionable": True,
        },
        "command": {
            "kind": "command",
            "command_id": command_id,
            "context": {"kind": "row", "locator": locator},
            "parameters": dict(element),
            "output_affecting": True,
        },
    }
    assert reversing_loop._candidate_verifier(selected["work_item"], selected["command"]) == "data_block_element_state"
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={state_key: [element]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {"data": {"commands": [{"command_id": command_id}]}}
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == command_id
            _write_manual_log(tmp_path)
            return {"data": _executed_data_block_element_payload(tmp_path, element)}
        if method == "GET" and path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(kind="data", text="\tdc.b $30,$31\n", start_offset=0x20, end_offset=0x22),
                        _listing_row(
                            row_key="row-2",
                            kind="data",
                            text="digits:\n\tdc.b $32,$33\n",
                            start_offset=0x24,
                            end_offset=0x26,
                        ),
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert report["verification"]["layers"][1]["state_key"] == state_key
    assert report["verification"]["layers"][2]["layer"] == "rendered_source"
    assert report["action"]["command_id"] == command_id


def test_data_block_element_verifier_fails_when_rendered_source_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locator = _listing_locator(kind="data", start_offset=0x20, end_offset=0x22)
    element = {
        "data_block_element_id": "ascii-hex:30",
        "layout_id": "ascii-hex",
        "offset": 0x30,
        "width": 2,
        "kind": "array",
        "name": "digits",
    }
    selected = {
        "work_item": {
            "id": "data-block-element",
            "kind": "data_block_element",
            "locator": locator,
            "suggested_action_kinds": ["row.data_block.element.set"],
            "confidence": "high",
            "actionable": True,
        },
        "command": {
            "kind": "command",
            "command_id": "row.data_block.element.set",
            "context": {"kind": "row", "locator": locator},
            "parameters": dict(element),
            "output_affecting": True,
        },
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"data_block_elements": [element]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "POST" and path.endswith("/commands/execute"):
            _write_manual_log(tmp_path)
            return {"data": _executed_data_block_element_payload(tmp_path, element)}
        if method == "GET" and path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(kind="data", text="\tdc.b $30,$31\n", start_offset=0x20, end_offset=0x22)
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    _write_manual_log(tmp_path)
    report = reversing_loop._verify_data_block_element_mutation(
        "demo",
        cast(dict[str, object], selected["command"]),
        "row.data_block.element.set",
        _executed_data_block_element_payload(tmp_path, element),
        project_root=tmp_path,
    )

    assert report["status"] == "failed"
    assert report["layers"][2]["layer"] == "rendered_source"
    assert report["layers"][2]["expected_tokens"] == ["digits", "dc.b"]
    assert report["layers"][2]["matched_tokens"] == ["dc.b"]


def test_data_block_element_verifier_fails_on_wrong_rendered_directive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locator = _listing_locator(kind="data", start_offset=0x20, end_offset=0x22)
    element = {
        "data_block_element_id": "ascii-hex:30",
        "layout_id": "ascii-hex",
        "offset": 0x30,
        "width": 2,
        "kind": "scalar",
        "name": "word_value",
        "representation": "hex",
    }
    command = {
        "kind": "command",
        "command_id": "row.data_block.element.set",
        "context": {"kind": "row", "locator": locator},
        "parameters": dict(element),
        "output_affecting": True,
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"data_block_elements": [element]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(
                            kind="data",
                            text="word_value:\n\tdc.b $12,$34\n",
                            start_offset=0x20,
                            end_offset=0x22,
                        )
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    _write_manual_log(tmp_path)
    report = reversing_loop._verify_data_block_element_mutation(
        "demo",
        command,
        "row.data_block.element.set",
        _executed_data_block_element_payload(tmp_path, element),
        project_root=tmp_path,
    )

    assert report["status"] == "failed"
    assert report["layers"][2]["expected_tokens"] == ["word_value", "dc.w", "$"]
    assert report["layers"][2]["matched_tokens"] == ["word_value", "$"]


def test_data_block_element_remove_verifier_requires_raw_restore_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locator = _listing_locator(kind="data", start_offset=0x20, end_offset=0x22)
    element = {"layout_id": "ascii-hex", "offset": 0x30, "width": 2, "removal_state": "raw"}
    command = {
        "kind": "command",
        "command_id": "row.data_block.element.remove",
        "context": {"kind": "row", "locator": locator},
        "parameters": dict(element),
        "output_affecting": True,
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"removed_data_block_elements": [element]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(kind="data", text="unrelated_label:\n", start_offset=0x20, end_offset=0x22),
                        _listing_row(
                            row_key="row-2",
                            kind="data",
                            text="\tdc.b $30,$31\n",
                            start_offset=0x24,
                            end_offset=0x26,
                        ),
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    _write_manual_log(tmp_path)
    report = reversing_loop._verify_data_block_element_mutation(
        "demo",
        command,
        "row.data_block.element.remove",
        _executed_data_block_element_payload(tmp_path, element),
        project_root=tmp_path,
    )

    assert report["status"] == "failed"
    assert report["layers"][2]["expected_restore_tokens"] == ["dc"]
    assert report["layers"][2]["matched_restore_tokens"] == []


def test_data_block_element_remove_verifier_accepts_raw_dc_after_named_element_removal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locator = _listing_locator(kind="data", start_offset=0x20, end_offset=0x22)
    element = {
        "layout_id": "ascii-hex",
        "offset": 0x30,
        "width": 2,
        "kind": "array",
        "name": "digits",
        "removal_state": "raw",
    }
    command = {
        "kind": "command",
        "command_id": "row.data_block.element.remove",
        "context": {"kind": "row", "locator": locator},
        "parameters": {"layout_id": "ascii-hex", "offset": 0x30, "removal_state": "raw"},
        "output_affecting": True,
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"removed_data_block_elements": [element]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/listing"):
            return {
                "data": {
                    "rows": [
                        _listing_row(kind="data", text="\tdc.b $30,$31\n", start_offset=0x20, end_offset=0x22)
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    _write_manual_log(tmp_path)
    report = reversing_loop._verify_data_block_element_mutation(
        "demo",
        command,
        "row.data_block.element.remove",
        _executed_data_block_element_payload(tmp_path, element),
        project_root=tmp_path,
    )

    assert report["status"] == "passed"
    assert report["layers"][2]["stale_tokens"] == []
    assert report["layers"][2]["matched_restore_tokens"] == ["dc"]


@pytest.mark.parametrize(
    ("command_id", "state_key", "row_text", "expected_status"),
    [
        ("row.data_block.element.interpret_ref", "data_block_interpreted_refs", "\tdc.l dblk_ref_h0_00000020", "passed"),
        ("row.data_block.element.clear_ref", "removed_data_block_interpreted_refs", "\tdc.l $00000020", "passed"),
        ("row.data_block.element.interpret_ref", "data_block_interpreted_refs", "\tdc.l $00000020", "failed"),
    ],
)
def test_data_block_interpreted_ref_verifier_checks_symbolic_render(
    command_id: str,
    state_key: str,
    row_text: str,
    expected_status: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    locator = _listing_locator(kind="data", start_offset=0x20, end_offset=0x24)
    interpreted_ref = {
        "data_block_ref_id": "ptr-table:0:absolute:h0:00000020",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x20,
        "target_locator": {"hunk": 0, "offset": 0x20},
        "source_value": 0x20,
        "confidence": "manual",
        "xref_generation_mode": "bidirectional",
    }
    command = {
        "kind": "command",
        "command_id": command_id,
        "context": {"kind": "row", "locator": locator},
        "parameters": dict(interpreted_ref),
        "output_affecting": True,
    }
    project_ref = (
        {**interpreted_ref, "cleanup_action_id": "manual-1"} if command_id.endswith(".clear_ref") else interpreted_ref
    )
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={state_key: [project_ref]}),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/listing"):
            runtime_address_refs = []
            if not command_id.endswith(".clear_ref"):
                runtime_address_refs = [
                    {
                        "offset": 0x20,
                        "operand_index": None,
                        "target_section_index": 0,
                        "target_offset": 0x20,
                        "runtime_address": 0x20,
                        "size": 4,
                        "confidence": 3,
                        "owner_kind": "data_block_interpreted_ref",
                        "owner_id": "ptr-table:0:absolute:h0:00000020",
                        "owner_layout_id": "ptr-table",
                        "owner_element_offset": 0,
                        "xref_generation_mode": "bidirectional",
                    }
                ]
            return {
                "data": {
                    "rows": [
                        _listing_row(
                            row_key="data-row",
                            kind="data",
                            text=row_text,
                            start_offset=0x20,
                            end_offset=0x24,
                            runtime_address_refs=runtime_address_refs,
                        )
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    _write_manual_log(tmp_path)
    report = reversing_loop._verify_data_block_interpreted_ref_mutation(
        "demo",
        command,
        command_id,
        _executed_data_block_interpreted_ref_payload(tmp_path, interpreted_ref),
        project_root=tmp_path,
    )

    assert reversing_loop._candidate_verifier(
        {"suggested_action_kinds": [command_id], "default_verifier": "data_block_interpreted_ref_state"},
        command,
    ) == "data_block_interpreted_ref_state"
    assert report["status"] == expected_status, report
    assert report["layers"][1]["state_key"] == state_key
    assert report["layers"][2]["layer"] == "rendered_source"
    assert report["layers"][3]["layer"] == "xref_projection"


def test_data_block_interpreted_ref_verifier_rejects_sparse_interpret_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    interpreted_ref = {
        "data_block_ref_id": "ptr-table:0:absolute:h0:00000020",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x20,
        "target_locator": {"hunk": 0, "offset": 0x20},
        "source_value": 0x20,
        "confidence": "manual",
        "xref_generation_mode": "bidirectional",
    }
    sparse_ref = {
        "data_block_ref_id": "ptr-table:0:absolute:h0:00000020",
        "layout_id": "ptr-table",
        "offset": 0,
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"data_block_interpreted_refs": [interpreted_ref]},
        ),
    )

    verification = reversing_loop._verify_project_data_block_interpreted_ref(
        "demo",
        "row.data_block.element.interpret_ref",
        sparse_ref,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["message"] == "interpreted ref payload missing selected reference identity"
    assert verification["missing_identity_fields"] == [
        "width",
        "reference_kind",
        "target_hunk",
        "target_offset",
        "target_locator",
        "source_value",
    ]
    assert (
        reversing_loop._project_data_block_interpreted_ref_state_match(
            "demo",
            "row.data_block.element.interpret_ref",
            sparse_ref,
            project_root=tmp_path,
        )
        is None
    )


def test_data_block_interpreted_ref_verifier_rejects_sparse_clear_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    interpreted_ref = {
        "data_block_ref_id": "ptr-table:0:absolute:h0:00000020",
        "layout_id": "ptr-table",
        "offset": 0,
        "width": 4,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x20,
        "target_locator": {"hunk": 0, "offset": 0x20},
        "source_value": 0x20,
        "confidence": "manual",
        "xref_generation_mode": "bidirectional",
        "cleanup_action_id": "manual-1",
    }
    sparse_ref = {
        "data_block_ref_id": "ptr-table:0:absolute:h0:00000020",
        "layout_id": "ptr-table",
        "offset": 0,
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"removed_data_block_interpreted_refs": [interpreted_ref]},
        ),
    )

    verification = reversing_loop._verify_project_data_block_interpreted_ref(
        "demo",
        "row.data_block.element.clear_ref",
        sparse_ref,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["message"] == "interpreted ref payload missing selected reference identity"
    assert verification["missing_identity_fields"] == [
        "width",
        "reference_kind",
        "target_hunk",
        "target_offset",
        "target_locator",
        "source_value",
        "cleanup_action_id",
    ]
    assert (
        reversing_loop._project_data_block_interpreted_ref_state_match(
            "demo",
            "row.data_block.element.clear_ref",
            sparse_ref,
            project_root=tmp_path,
        )
        is None
    )


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


def test_target_equate_add_verifier_rejects_sparse_payload(
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
            manual_state={"target_equates": [{"name": "PLAYER_START_LIVES", "value": 5}]},
        ),
    )

    verification = reversing_loop._verify_target_equate_mutation(
        "demo",
        "target.equate.add",
        _executed_target_equate_payload(tmp_path, {"name": "PLAYER_START_LIVES"}),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "target equate payload missing mutation identity"
    assert verification["layers"][1]["missing_identity_fields"] == ["value"]


def test_target_equate_rename_verifier_rejects_sparse_payload(
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
        _executed_target_equate_payload(tmp_path, {"name": "PLAYER_INITIAL_LIVES"}),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "target equate payload missing mutation identity"
    assert verification["layers"][1]["missing_identity_fields"] == ["previous_name"]


def test_target_equate_representation_verifier_checks_rendered_definition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    equate = {
        "name": "PLAYER_START_LIVES",
        "value": 42,
        "value_representation": "symbol",
        "value_expression": "40+2",
    }
    assert (
        reversing_loop._target_equate_expected_definition_expr({"value": 32, "value_representation": "binary"})
        == "%00100000"
    )
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"target_equates": [equate]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {
            "data": {
                "groups": {
                    "equates": [
                        {
                            "symbol": "PLAYER_START_LIVES",
                            "operand": "40+2",
                            "refs": [{"access": "definition"}],
                        }
                    ]
                }
            }
        },
    )

    verification = reversing_loop._verify_target_equate_mutation(
        "demo",
        "target.equate.represent",
        _executed_target_equate_payload(tmp_path, equate),
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["layers"][2]["layer"] == "rendered_source"
    assert verification["layers"][2]["expected_operand"] == "40+2"


def test_target_equate_representation_verifier_rejects_sparse_payload(
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
            manual_state={"target_equates": [{"name": "PLAYER_START_LIVES", "value": 42}]},
        ),
    )

    verification = reversing_loop._verify_target_equate_mutation(
        "demo",
        "target.equate.represent",
        _executed_target_equate_payload(tmp_path, {"name": "PLAYER_START_LIVES", "value": 42}),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "target equate payload missing mutation identity"
    assert verification["layers"][1]["missing_identity_fields"] == ["value_representation"]


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


def test_data_symbol_remove_verifier_checks_manual_seed_removed(
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

    verification = reversing_loop._verify_manual_mutation(
        "demo",
        {"command_id": "data_symbol.remove"},
        _executed_manual_seed_remove_payload(tmp_path, "data-symbol:h0:00000100"),
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    assert verification["layers"][1]["removed_seed_ids"] == ["data-symbol:h0:00000100"]


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


def test_manual_seed_verifier_rejects_sparse_creation_payload(
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

    verification = reversing_loop._verify_manual_seed_mutation(
        "demo",
        "row.seed.data.raw",
        _executed_manual_seed_payload(tmp_path, {"seed_id": "catalog-seed-1"}),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "manual seed payload missing source identity"
    assert verification["layers"][1]["missing_identity_fields"] == [["kind", "hunk", "addr"]]


def test_range_seed_verifier_requires_range_end_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    seed = {
        "seed_id": "catalog-range-seed-1",
        "kind": "data",
        "mode": "required",
        "hunk": 0,
        "addr": 0,
        "end": 4,
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"seeds": [seed]}),
    )

    verification = reversing_loop._verify_manual_seed_mutation(
        "demo",
        "range.seed.data.raw",
        _executed_manual_seed_payload(
            tmp_path,
            {
                "seed_id": "catalog-range-seed-1",
                "kind": "data",
                "mode": "required",
                "hunk": 0,
                "addr": 0,
            },
        ),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "manual seed payload missing source identity"
    assert verification["layers"][1]["missing_identity_fields"] == [["end"]]


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


def test_manual_label_rename_verifier_rejects_sparse_payload(
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
            manual_state={"labels": [{"label_id": "manual-label-1", "name": "old_label"}]},
        ),
    )

    verification = reversing_loop._verify_manual_label_mutation(
        "demo",
        "review.label.rename",
        _executed_manual_label_payload(tmp_path, {"label_id": "manual-label-1"}),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "manual label payload missing mutation identity"
    assert verification["layers"][1]["missing_identity_fields"] == [["name"]]


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


def test_manual_label_scope_verifier_rejects_sparse_payload(
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
            manual_state={"labels": [{"label_id": "manual-label-1", "name": "local_name", "scope": "global"}]},
        ),
    )

    verification = reversing_loop._verify_manual_label_mutation(
        "demo",
        "review.label.change_scope",
        _executed_manual_label_payload(tmp_path, {"label_id": "manual-label-1"}),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "manual label payload missing mutation identity"
    assert verification["layers"][1]["missing_identity_fields"] == [["scope"]]


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


def test_rsset_region_verifier_rejects_sparse_add_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    region = {
        "offset": 4,
        "layout_name": "work",
        "base_symbol": "__game_work_base__",
        "symbol": "work_flags",
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"rsset_layout_regions": [region]}),
    )

    verification = reversing_loop._verify_rsset_region_mutation(
        "demo",
        "target.rsset_region.add",
        _executed_rsset_region_payload(tmp_path, {"offset": 4}),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "RSSET layout region payload missing mutation identity"
    assert verification["layers"][1]["missing_identity_fields"] == ["symbol"]


def test_app_slot_region_verifier_rejects_sparse_rename_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    region = {"offset": 0x102, "size": 1, "symbol": "app_input_event"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"rsset_layout_regions": [region]}),
    )

    verification = reversing_loop._verify_rsset_region_mutation(
        "demo",
        "app_slot.rename",
        _executed_rsset_region_payload(tmp_path, {"offset": 0x102, "symbol": "app_input_event"}),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][1]["message"] == "RSSET layout region payload missing mutation identity"
    assert verification["layers"][1]["missing_identity_fields"] == ["size"]


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
    assert report["action"]["parameters"] == {"name": "player_table", "hunk": 0, "addr": 0, "end": 2}
    assert report["planner"]["selected_command_id"] == "data_symbol.rename"
    assert report["planner"]["selected_verifier"] == "projected_data_symbol_name"


def test_embedded_data_symbol_rename_command_strips_provenance_parameters() -> None:
    candidate = {
        "id": "data-symbol-candidate",
        "candidate_id": "data-symbol-candidate",
        "kind": "data_symbol_name",
        "command": {
            "command_id": "data_symbol.rename_existing",
            "context": {
                "kind": "row",
                "locator": _listing_locator(kind="data"),
                "source_evidence_id": "xref-1",
                "source_family": "runtime_address_ref",
            },
            "parameters": {
                "name": "player_table",
                "previous_name": "auto_data",
                "data_class": "table",
                "source_evidence_id": "xref-1",
                "source_family": "runtime_address_ref",
                "path_lifetime_scope": {"kind": "global"},
            },
            "output_affecting": True,
        },
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["context"] == {"kind": "row", "locator": _listing_locator(kind="data")}
    assert command["parameters"] == {"name": "player_table", "hunk": 0, "addr": 0, "end": 2}
    assert reversing_loop._candidate_verifier(candidate, command) == "projected_data_symbol_name"


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


def test_data_symbol_remove_candidate_strips_provenance_parameters() -> None:
    candidate = _data_symbol_remove_candidate(suppressed=False)
    candidate["parameters"] = {
        "kind": "seeded_entity",
        "hunk": 0,
        "addr": 0x100,
        "source_evidence_id": "xref-1",
        "source_family": "runtime_address_ref",
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["parameters"] == {"kind": "seeded_entity", "hunk": 0, "addr": 0x100}


def test_data_symbol_remove_candidate_keeps_manual_seed_identity() -> None:
    candidate = _data_symbol_remove_candidate(suppressed=False)
    candidate["parameters"] = {
        "seed_id": "data-symbol:h0:00000100",
        "source_evidence_id": "xref-1",
        "source_family": "runtime_address_ref",
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["parameters"] == {"seed_id": "data-symbol:h0:00000100"}
    assert reversing_loop._candidate_verifier(candidate, command) == "manual_seed_state"
    assert reversing_loop._command_summary(command)["verifier"] == "manual_seed_state"


def test_planner_skips_already_satisfied_manual_data_symbol_remove() -> None:
    candidate = _data_symbol_remove_candidate(suppressed=False)
    candidate["parameters"] = {"seed_id": "data-symbol:h0:00000100"}
    candidate["current_metadata"] = {"removed": True, "seed_id": "data-symbol:h0:00000100"}
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )

    cast(dict[str, object], candidate["current_metadata"])["seed_id"] = "data-symbol:h0:00000200"

    assert reversing_loop._candidate_skip_reason(candidate, command) is None


def test_planner_skips_already_satisfied_generated_data_symbol_remove_by_identity() -> None:
    candidate = _data_symbol_remove_candidate(suppressed=False)
    candidate["parameters"] = {"kind": "seeded_entity", "hunk": 0, "addr": 0x100, "end": 0x104}
    candidate["current_metadata"] = {
        "suppressed": True,
        "kind": "seeded_entity",
        "hunk": 0,
        "addr": 0x100,
        "end": 0x104,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )

    cast(dict[str, object], candidate["current_metadata"])["end"] = 0x108

    assert reversing_loop._candidate_skip_reason(candidate, command) is None


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
            return {
                "data": {
                    "commands": [
                        {
                            "command_id": "data_symbol.rename",
                            "parameters": {"hunk": 0, "addr": 0, "end": 2},
                        }
                    ]
                }
            }
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
            return {"data": _executed_listing_comment_payload(tmp_path, text="Hunk file entrypoint.")}
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
        "durable_payload",
        "semantic_reload",
        "projection",
    ]
    assert report["action"]["command_id"] == "comment.edit"
    assert report["action_result"]["status"] == "executed"


def test_comment_edit_verifier_rejects_mismatched_durable_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    command = {
        "command_id": "comment.edit",
        "context": {"kind": "row", "locator": _listing_locator()},
        "parameters": {"text": "expected comment"},
    }

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {}}}}
        if method == "GET" and path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(comment_text="expected comment")]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    verification = reversing_loop._verify_manual_mutation(
        "demo",
        command,
        _executed_listing_comment_payload(tmp_path, text="wrong comment"),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    durable_layer = verification["layers"][1]
    assert durable_layer["layer"] == "durable_payload"
    assert durable_layer["expected_comment_text"] == "expected comment"
    assert durable_layer["actual_comment_text"] == "wrong comment"


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
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "seeds": [
                    {
                        "seed_id": "data_symbol:0:00000000:00000002",
                        "kind": "data",
                        "hunk": 0,
                        "addr": 0,
                        "end": 2,
                        "name": "player_table",
                    }
                ]
            },
        ),
    )

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if method == "GET" and path.endswith("/commands"):
            return {
                "data": {
                    "commands": [
                        {
                            "command_id": "data_symbol.rename",
                            "parameters": {"hunk": 0, "addr": 0, "end": 2},
                        }
                    ]
                }
            }
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "data_symbol.rename"
            _write_manual_log(tmp_path)
            return {"data": _executed_data_symbol_payload(tmp_path, {"hunk": 0, "addr": 0, "end": 2, "name": "player_table"})}
        if method == "GET" and path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(row_key="row-1", kind="data", text="player_table:\n")]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "durable_payload",
        "manual_action_log",
        "semantic_reload",
        "projection",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "data_symbol.rename"
    assert report["action_result"]["status"] == "executed"


def test_data_symbol_rename_verifier_requires_durable_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    command = {
        "command_id": "data_symbol.rename",
        "context": {"kind": "row", "locator": _listing_locator(kind="data")},
        "parameters": {"hunk": 0, "addr": 0, "end": 2, "name": "player_table"},
    }
    monkeypatch.setattr(reversing_loop, "_open_and_wait_listing", lambda target_id, timeout_seconds: {"status": "ready"})
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "seeds": [
                    {"kind": "data", "hunk": 0, "addr": 0, "end": 2, "name": "player_table"},
                ]
            },
        ),
    )
    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {"data": {"rows": [_listing_row(kind="data", text="player_table:\n")]}},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_data_symbol_rename_mutation(
        "demo",
        command,
        {"action": {"action_id": "manual-1", "payload": {"comment": {"text": "not a data symbol"}}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][0]["layer"] == "durable_payload"
    assert verification["layers"][0]["message"] == "missing data symbol payload"


def test_data_symbol_rename_verifier_rejects_mismatched_durable_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_reproduction_exact(tmp_path)
    command = {
        "command_id": "data_symbol.rename",
        "context": {"kind": "row", "locator": _listing_locator(kind="data")},
        "parameters": {"hunk": 0, "addr": 0, "end": 2, "name": "player_table"},
    }
    monkeypatch.setattr(reversing_loop, "_open_and_wait_listing", lambda target_id, timeout_seconds: {"status": "ready"})
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "seeds": [
                    {"kind": "data", "hunk": 0, "addr": 0, "end": 4, "name": "player_table"},
                ]
            },
        ),
    )
    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {"data": {"rows": [_listing_row(kind="data", text="player_table:\n")]}},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_data_symbol_rename_mutation(
        "demo",
        command,
        {
            "action": {
                "action_id": "manual-1",
                "payload": {"data_symbol": {"hunk": 0, "addr": 0, "end": 4, "name": "player_table"}},
            }
        },
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["layers"][0]["mismatched_command_fields"] == ["end"]
    assert verification["layers"][2]["matching_manual_data_symbol_seeds"] == [
        {"kind": "data", "hunk": 0, "addr": 0, "end": 4, "name": "player_table"}
    ]


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
            return {
                "data": {
                    "commands": [
                        {
                            "command_id": "data_symbol.remove",
                            "parameters": {"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
                        }
                    ]
                }
            }
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "data_symbol.remove"
            _write_manual_log(tmp_path)
            return {"data": _executed_seeded_item_suppression_payload(tmp_path)}
        if method == "GET" and path.endswith("/listing"):
            source_offset = int(query["source_offset"][0])
            return {
                "data": {
                    "rows": [
                        _listing_row(kind="data", start_offset=source_offset, end_offset=source_offset + 4),
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "rendered_source",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "data_symbol.remove"
    assert report["action_result"]["status"] == "executed"


def test_data_symbol_remove_availability_requires_matching_cleanup_identity() -> None:
    command = {
        "command_id": "data_symbol.remove",
        "parameters": {"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
    }
    availability = {
        "commands": [
            {
                "command_id": "data_symbol.remove",
                "parameters": {"kind": "seeded_entity", "hunk": 0, "addr": 0x104},
            }
        ]
    }

    assert reversing_loop._available_catalog_command(command, availability) is None

    availability_parameters = cast(dict[str, object], availability["commands"][0]["parameters"])
    availability_parameters["addr"] = 0x100

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]

    availability_parameters["end"] = 0x104

    assert reversing_loop._available_catalog_command(command, availability) is None

    ranged_command = {
        "command_id": "data_symbol.remove",
        "parameters": {"kind": "seeded_entity", "hunk": 0, "addr": 0x100, "end": 0x104},
    }

    assert reversing_loop._available_catalog_command(ranged_command, availability) == availability["commands"][0]

    manual_seed_command = {
        "command_id": "data_symbol.remove",
        "parameters": {"seed_id": "data-symbol:h0:00000100"},
    }
    availability_parameters.clear()
    availability_parameters.update({"kind": "seeded_entity", "hunk": 0, "addr": 0x100})

    assert reversing_loop._available_catalog_command(manual_seed_command, availability) is None

    availability_parameters.clear()
    availability_parameters["seed_id"] = "data-symbol:h0:00000100"

    assert reversing_loop._available_catalog_command(manual_seed_command, availability) == availability["commands"][0]


def test_data_symbol_rename_availability_requires_matching_source_identity() -> None:
    command = {
        "command_id": "data_symbol.rename",
        "parameters": {"name": "player_table", "hunk": 0, "addr": 0x100, "end": 0x108},
    }
    availability = {
        "commands": [
            {
                "command_id": "data_symbol.rename",
                "parameters": {"hunk": 0, "addr": 0x100, "end": 0x104},
            }
        ]
    }

    assert reversing_loop._available_catalog_command(command, availability) is None

    availability_parameters = cast(dict[str, object], availability["commands"][0]["parameters"])
    availability_parameters["end"] = 0x108

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]


def test_planner_command_identity_includes_data_symbol_source_identity() -> None:
    context = {"kind": "row", "locator": _listing_locator(kind="data")}
    short_range = {
        "command_id": "data_symbol.rename",
        "context": context,
        "parameters": {"name": "short_table", "hunk": 0, "addr": 0x100, "end": 0x104},
    }
    long_range = {
        "command_id": "data_symbol.rename",
        "context": context,
        "parameters": {"name": "long_table", "hunk": 0, "addr": 0x100, "end": 0x108},
    }

    assert not reversing_loop._commands_same_identity(short_range, long_range)

    long_range["parameters"] = {"name": "renamed_table", "hunk": 0, "addr": 0x100, "end": 0x104}

    assert reversing_loop._commands_same_identity(short_range, long_range)


def test_planner_command_identity_includes_union_of_provenance_keys() -> None:
    context = {"kind": "element", "locator": _listing_locator(), "element_id": "row-1:typed_gap:0"}
    unproven = {
        "command_id": "typed_gap.field.add",
        "context": context,
        "parameters": {"struct_name": "InputEvent", "offset": 4, "name": "old_flags"},
    }
    proven = {
        "command_id": "typed_gap.field.add",
        "context": context,
        "parameters": {
            "struct_name": "InputEvent",
            "offset": 4,
            "name": "flags",
            "source_evidence_id": "prov-struct-pointer",
            "source_family": "struct_pointer",
            "source_evidence_status": "analysis_proven",
        },
    }

    assert not reversing_loop._commands_same_identity(unproven, proven)


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
            return {
                "data": {
                    "commands": [
                        {
                            "command_id": "correction.suppress_seeded_item.seeded_entity",
                            "parameters": {"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
                        }
                    ]
                }
            }
        if method == "POST" and path.endswith("/commands/execute"):
            assert isinstance(body, dict)
            assert body["command_id"] == "correction.suppress_seeded_item.seeded_entity"
            _write_manual_log(tmp_path)
            return {"data": _executed_seeded_item_suppression_payload(tmp_path)}
        if method == "GET" and path.endswith("/listing"):
            source_offset = int(query["source_offset"][0])
            return {
                "data": {
                    "rows": [
                        _listing_row(kind="data", start_offset=source_offset, end_offset=source_offset + 4),
                    ]
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["verification"]["status"] == "passed"
    assert [layer["layer"] for layer in report["verification"]["layers"]] == [
        "manual_action_log",
        "semantic_reload",
        "rendered_source",
        "round_trip",
    ]
    assert report["action"]["command_id"] == "correction.suppress_seeded_item.seeded_entity"
    assert report["action_result"]["status"] == "executed"


def test_seeded_item_suppression_verifier_requires_durable_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    action_item = {"kind": "seeded_entity", "hunk": 0, "addr": 0x100}
    local_effect_item = {"kind": "seeded_entity", "hunk": 0, "addr": 0x104}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"suppressed_seeded_items": [local_effect_item]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_seeded_item_suppression_mutation(
        "demo",
        {
            "action": {"action_id": "manual-1", "payload": {"suppressed_seeded_item": action_item}},
            "application": {
                "local_effects": [
                    {"kind": "seeded_item_suppression", "suppressed_seeded_item": local_effect_item}
                ]
            },
        },
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_suppressed_seeded_item"]["addr"] == 0x100
    assert semantic_layer["matching_suppressed_seeded_items"] == []


def test_seeded_item_suppression_verifier_prefers_action_payload_over_local_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    action_item = {"kind": "seeded_entity", "hunk": 0, "addr": 0x100}
    local_effect_item = {"kind": "seeded_entity", "hunk": 0, "addr": 0x104}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"suppressed_seeded_items": [action_item]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_seeded_item_suppression_mutation(
        "demo",
        {
            "action": {"action_id": "manual-1", "payload": {"suppressed_seeded_item": action_item}},
            "application": {
                "local_effects": [
                    {"kind": "seeded_item_suppression", "suppressed_seeded_item": local_effect_item}
                ]
            },
        },
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_suppressed_seeded_item"]["addr"] == 0x100


def test_seeded_item_suppression_verifier_rejects_stale_rendered_suppressible_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    item = {"kind": "seeded_entity", "hunk": 0, "addr": 0x100}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"suppressed_seeded_items": [item]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )
    stale_row = _listing_row(kind="data", start_offset=0x100, end_offset=0x104)
    stale_row["suppressible_seeded_items"] = [item]

    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: {"data": {"rows": [stale_row]}},
    )

    verification = reversing_loop._verify_seeded_item_suppression_mutation(
        "demo",
        {
            "action": {"action_id": "manual-1", "payload": {"suppressed_seeded_item": item}},
            "mutation": {"affected_locators": [_listing_locator(kind="data", start_offset=0x100, end_offset=0x104)]},
        },
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    rendered_layer = verification["layers"][2]
    assert rendered_layer["layer"] == "rendered_source"
    assert rendered_layer["stale_suppressible_seeded_items"] == [item]


def test_seeded_item_suppression_verifier_rejects_local_effect_without_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    local_effect_item = {"kind": "seeded_entity", "hunk": 0, "addr": 0x104}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"suppressed_seeded_items": [local_effect_item]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_seeded_item_suppression_mutation(
        "demo",
        {
            "application": {
                "local_effects": [
                    {"kind": "seeded_item_suppression", "suppressed_seeded_item": local_effect_item}
                ]
            },
        },
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["message"] == "missing suppressed seeded item payload"


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
            manual_state={"execution_views": [{**_execution_view_payload(), "owner_action_id": "manual-1"}]},
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
                        "cleanup_action_id": "manual-1",
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


def test_execution_view_add_verifier_requires_owner_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"execution_views": [{**_execution_view_payload(), "owner_action_id": "manual-other"}]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_execution_view_mutation(
        "demo",
        "target.execution_view.add",
        {"action": {"action_id": "manual-1", "payload": {"execution_view": _execution_view_payload()}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_execution_view"]["owner_action_id"] == "manual-1"
    assert semantic_layer["matching_execution_views"] == []


def test_execution_view_add_verifier_requires_explicit_view_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    action_view = {**_execution_view_payload(), "execution_view_id": "stage-a"}
    reloaded_view = {**_execution_view_payload(), "execution_view_id": "stage-b", "owner_action_id": "manual-1"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"execution_views": [reloaded_view]}),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_execution_view_mutation(
        "demo",
        "target.execution_view.add",
        {"action": {"action_id": "manual-1", "payload": {"execution_view": action_view}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_execution_view"]["execution_view_id"] == "stage-a"
    assert semantic_layer["matching_execution_views"] == []


def test_execution_view_verifier_prefers_action_payload_over_local_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    action_view = {**_execution_view_payload(), "execution_view_id": "stage-a"}
    local_effect_view = {**_execution_view_payload(), "execution_view_id": "stage-b"}
    reloaded_view = {**action_view, "owner_action_id": "manual-1"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(_project(()), manual_state={"execution_views": [reloaded_view]}),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_execution_view_mutation(
        "demo",
        "target.execution_view.add",
        {
            "action": {"action_id": "manual-1", "payload": {"execution_view": action_view}},
            "application": {
                "local_effects": [{"kind": "execution_view", "execution_view": local_effect_view}],
            },
        },
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_execution_view"]["execution_view_id"] == "stage-a"


def test_execution_view_verifier_requires_durable_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    local_effect_view = {**_execution_view_payload(), "execution_view_id": "stage-b"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"execution_views": [{**local_effect_view, "owner_action_id": "manual-1"}]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_execution_view_mutation(
        "demo",
        "target.execution_view.add",
        {
            "application": {
                "local_effects": [{"kind": "execution_view", "execution_view": local_effect_view}],
            },
        },
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["message"] == "missing execution view payload"


def test_execution_view_remove_verifier_requires_cleanup_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    removed_view = {
        "source_start": 0x20,
        "source_end": 0x80,
        "base_addr": 0x4000,
        "cleanup_action_id": "manual-other",
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"removed_execution_views": [removed_view]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_execution_view_mutation(
        "demo",
        "target.execution_view.remove",
        {"action": {"action_id": "manual-1", "payload": {"execution_view": _execution_view_remove_payload()}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_execution_view"]["cleanup_action_id"] == "manual-1"
    assert semantic_layer["matching_execution_views"] == []


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


def test_register_seed_verifier_requires_matching_provenance_reload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    expected_seed = {
        "register": "A6",
        "kind": "library_base",
        "library_name": "intuition.library",
        "source_evidence_id": "prov-intuition-a6",
        "source_family": "library_base",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "entry", "hunk": 0, "addr": 0x120},
        "parent_evidence_ids": ["prov-root", "prov-call"],
    }
    command = {
        "command_id": "semantic.library_base.intuition.library",
        "context": {"kind": "element", "base_register": "A6"},
        "parameters": {},
        "output_affecting": True,
    }

    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "register_seeds": [
                    {
                        **expected_seed,
                        "parent_evidence_ids": ["prov-root"],
                    },
                ]
            },
        ),
    )

    missing_parent = reversing_loop._verify_library_base_register_seed_mutation(
        "demo",
        command,
        _executed_register_seed_payload(tmp_path, expected_seed),
        project_root=tmp_path,
    )

    assert missing_parent["status"] == "failed"
    assert missing_parent["layers"][1]["matching_register_seeds"] == []

    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={
                "register_seeds": [
                    {
                        **expected_seed,
                        "parent_evidence_ids": ["prov-call", "prov-root"],
                    },
                ]
            },
        ),
    )

    matching_parent_set = reversing_loop._verify_library_base_register_seed_mutation(
        "demo",
        command,
        _executed_register_seed_payload(tmp_path, expected_seed),
        project_root=tmp_path,
    )

    assert matching_parent_set["status"] == "passed"


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
    assert command["parameters"] == {"name": "bitmap_00040120", "hunk": 1, "addr": 0x120, "end": 0x140}


def test_listing_data_symbol_candidates_skip_runtime_address_when_class_missing() -> None:
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

    assert candidates == []


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
    assert command["parameters"] == {"name": "bitmap_h0_00000040", "hunk": 0, "addr": 0x40, "end": 0x44}


def test_listing_data_symbol_candidates_use_rename_existing_for_named_rows() -> None:
    row = _listing_row(
        row_key="table-row",
        kind="data",
        text="\tdc.b $00,$01,$02,$03\n",
        label="old_table",
        start_offset=0x40,
        end_offset=0x44,
    )
    row["data_class"] = "table"

    candidates = reversing_loop._listing_data_symbol_candidates([row])
    command = reversing_loop._candidate_command_options(candidates[0])[0]

    assert candidates[0]["suggested_action_kinds"] == ["data_symbol.rename_existing"]
    assert candidates[0]["current_metadata"] == {"name": "old_table"}
    assert command["command_id"] == "data_symbol.rename_existing"
    assert command["context"] == {"kind": "row", "locator": row["locator"]}


def test_listing_data_symbol_class_address_name_is_planner_skip() -> None:
    row = _listing_row(
        row_key="bitmap-row",
        kind="data",
        text="\tdc.b $00,$01,$02,$03\n",
        start_offset=0x40,
        end_offset=0x44,
    )
    row["data_class"] = "bitmap"
    row["runtime_address"] = 0x40120

    candidate = reversing_loop._listing_data_symbol_candidates([row])[0]
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "data symbol name is only class/address styling"
    )


def test_listing_data_symbol_rename_existing_class_address_name_is_planner_skip() -> None:
    row = _listing_row(
        row_key="table-row",
        kind="data",
        text="\tdc.b $00,$01,$02,$03\n",
        label="old_table",
        start_offset=0x40,
        end_offset=0x44,
    )
    row["data_class"] = "table"

    candidate = reversing_loop._listing_data_symbol_candidates([row])[0]
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "data symbol name is only class/address styling"
    )


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


def test_listing_data_symbol_candidates_skip_conflicting_existing_data_ref_name() -> None:
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
            "data_class": "blitter_destination",
        }
    ]

    candidates = reversing_loop._listing_data_symbol_candidates(
        [row],
        existing_data_symbols={(1, 0x120, None): "blitter_source_00040120"},
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
                    end=None,
                    name="bitmap_00040120",
                    type="data",
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


def test_listing_data_symbol_candidates_do_not_skip_different_existing_range(tmp_path: Path) -> None:
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
                    end=0x42,
                    name="bitmap_h0_00000040",
                    type="data",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.VALIDATED,
                    citation="test",
                ),
            ),
        ),
    )
    row = _listing_row(
        row_key="bitmap-row",
        kind="data",
        text="\tdc.b $00,$01,$02,$03\n",
        start_offset=0x40,
        end_offset=0x44,
    )
    row["data_class"] = "bitmap"
    inspect_report = {"target_state": {"target_dir": str(target_dir), "project": {"manual_state": {}}}}

    candidates = reversing_loop._listing_data_symbol_candidates(
        [row],
        existing_data_symbols=reversing_loop._existing_data_symbol_names(inspect_report),
    )

    assert candidates[0]["candidate_id"] == "data-class-symbol:bitmap-row:0:00000040:bitmap_h0_00000040"
    assert candidates[0]["suggested_action_kinds"] == ["data_symbol.rename"]


def test_listing_data_symbol_candidates_treat_open_ended_existing_name_as_same_start(tmp_path: Path) -> None:
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
                    end=None,
                    name="old_bitmap",
                    type="data",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.VALIDATED,
                    citation="test",
                ),
            ),
        ),
    )
    row = _listing_row(
        row_key="bitmap-row",
        kind="data",
        text="\tdc.b $00,$01,$02,$03\n",
        start_offset=0x40,
        end_offset=0x44,
    )
    row["data_class"] = "bitmap"
    row["runtime_address"] = 0x40120
    inspect_report = {"target_state": {"target_dir": str(target_dir), "project": {"manual_state": {}}}}

    candidates = reversing_loop._listing_data_symbol_candidates(
        [row],
        existing_data_symbols=reversing_loop._existing_data_symbol_names(inspect_report),
    )
    command = reversing_loop._candidate_command_options(candidates[0])[0]

    assert candidates[0]["current_metadata"] == {"name": "old_bitmap"}
    assert candidates[0]["suggested_action_kinds"] == ["data_symbol.rename_existing"]
    assert command["parameters"] == {"name": "bitmap_00040120", "hunk": 0, "addr": 0x40, "end": 0x44}


def test_listing_data_symbol_candidates_do_not_skip_existing_code_entity(tmp_path: Path) -> None:
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
                    end=0x44,
                    name="bitmap_h0_00000040",
                    type="code",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="test",
                ),
            ),
        ),
    )
    row = _listing_row(
        row_key="bitmap-row",
        kind="data",
        text="\tdc.b $00,$01,$02,$03\n",
        start_offset=0x40,
        end_offset=0x44,
    )
    row["data_class"] = "bitmap"
    inspect_report = {"target_state": {"target_dir": str(target_dir), "project": {"manual_state": {}}}}

    candidates = reversing_loop._listing_data_symbol_candidates(
        [row],
        existing_data_symbols=reversing_loop._existing_data_symbol_names(inspect_report),
    )

    assert candidates[0]["candidate_id"] == "data-class-symbol:bitmap-row:0:00000040:bitmap_h0_00000040"
    assert candidates[0]["suggested_action_kinds"] == ["data_symbol.rename"]


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
    assert reversing_loop._default_verifier_for_actions(["data_symbol.add"]) == "projected_data_symbol_name"
    assert reversing_loop._default_verifier_for_actions(["data_symbol.edit"]) == "projected_data_symbol_name"
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
        "layout_name": "app",
        "base_symbol": "__amiga_app_base__",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "rsset_binding_state"


def test_rsset_binding_skip_uses_active_binding_and_parent_evidence_set() -> None:
    base_ref = {
        "source_evidence_id": "prov-demo-rsset",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
    }
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
            "source_evidence_id": "prov-demo-rsset",
            "source_family": "rsset_app_base",
            "source_evidence_status": "analysis_proven",
            "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0xE2},
            "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
            "base_evidence_refs": [base_ref],
        },
        "current_metadata": {
            "layout_name": "app",
            "base_symbol": "__amiga_app_base__",
            "base_register": "A6",
            "base_evidence_id": "selected-base:A6:__amiga_app_base__",
            "displacement": 0x0102,
            "operand_index": 0,
            "source_evidence_id": "prov-demo-rsset",
            "source_family": "rsset_app_base",
            "source_evidence_status": "analysis_proven",
            "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0xE2},
            "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"],
            "base_evidence_refs": [{**base_ref, "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"]}],
        },
        "default_verifier": "rsset_binding_state",
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_rsset_unbind_skip_uses_removed_binding_identity_and_parent_evidence_set() -> None:
    base_ref = {
        "source_evidence_id": "prov-demo-rsset",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
    }
    parameters = {
        "layout_name": "app",
        "base_symbol": "__amiga_app_base__",
        "base_register": "A6",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "displacement": 0x0102,
        "operand_index": 0,
        "source_evidence_id": "prov-demo-rsset",
        "source_family": "rsset_app_base",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0xE2},
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
        "base_evidence_refs": [base_ref],
    }
    candidate = {
        "id": "rsset-binding-unbind",
        "candidate_id": "rsset-binding-unbind",
        "kind": "rsset_use_site_binding_remove",
        "locator": _listing_locator(),
        "element_id": "row-1:displacement:0:operand",
        "suggested_action_kinds": ["rsset.binding.unbind"],
        "parameters": parameters,
        "current_metadata": {
            "removed": True,
            "rsset_use_site_binding": {
                **parameters,
                "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"],
                "base_evidence_refs": [{**base_ref, "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"]}],
            },
        },
        "default_verifier": "rsset_binding_state",
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )

    cast(dict[str, object], candidate["current_metadata"])["rsset_use_site_binding"] = {
        **parameters,
        "base_evidence_id": "selected-base:A5:__other_base__",
    }

    assert reversing_loop._candidate_skip_reason(candidate, command) is None


def test_rsset_binding_availability_requires_matching_base_evidence() -> None:
    command = {
        "command_id": "rsset.binding.bind",
        "parameters": {
            "layout_name": "app",
            "base_symbol": "__amiga_app_base__",
            "base_register": "A6",
            "base_evidence_id": "selected-base:A6:__amiga_app_base__",
            "displacement": 0x0102,
            "operand_index": 0,
        },
    }
    availability = {
        "commands": [
            {
                "command_id": "rsset.binding.bind",
                "parameters": {
                    "layout_name": "app",
                    "base_symbol": "__amiga_app_base__",
                    "base_register": "A6",
                    "base_evidence_id": "selected-base:A5:__other_base__",
                    "displacement": 0x0102,
                    "operand_index": 0,
                },
            }
        ]
    }

    assert reversing_loop._available_catalog_command(command, availability) is None

    command_parameters = cast(dict[str, object], command["parameters"])
    del command_parameters["base_evidence_id"]

    assert reversing_loop._available_catalog_command(command, availability) is None

    command_parameters["base_evidence_id"] = "selected-base:A6:__amiga_app_base__"

    availability["commands"][0]["parameters"]["base_evidence_id"] = "selected-base:A6:__amiga_app_base__"

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]


def test_rsset_binding_availability_requires_matching_provenance_identity() -> None:
    base_ref = {
        "source_evidence_id": "prov-rsset",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
    }
    command = {
        "command_id": "rsset.binding.bind",
        "parameters": {
            "layout_name": "app",
            "base_symbol": "__amiga_app_base__",
            "base_register": "A6",
            "base_evidence_id": "selected-base:A6:__amiga_app_base__",
            "displacement": 0x0102,
            "operand_index": 0,
            "source_evidence_id": "prov-rsset",
            "source_family": "rsset_app_base",
            "source_evidence_status": "analysis_proven",
            "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0xE2},
            "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"],
            "base_evidence_refs": [base_ref],
        },
    }
    availability = {
        "commands": [
            {
                "command_id": "rsset.binding.bind",
                "parameters": {
                    **cast(dict[str, object], command["parameters"]),
                    "source_evidence_status": "manual_override",
                },
            }
        ]
    }

    assert reversing_loop._available_catalog_command(command, availability) is None

    cast(dict[str, object], availability["commands"][0]["parameters"])["source_evidence_status"] = "analysis_proven"
    cast(dict[str, object], availability["commands"][0]["parameters"])["parent_evidence_ids"] = [
        "prov-parent-b",
        "prov-parent-a",
    ]
    cast(dict[str, object], availability["commands"][0]["parameters"])["base_evidence_refs"] = [
        {**base_ref, "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"]}
    ]

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]


def test_rsset_binding_verifier_requires_owner_and_base_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    base_ref = {
        "operand_index": 0,
        "base_register": "A6",
        "displacement": 0x0102,
        "source_family": "rsset_app_base",
        "status": "path_specific",
        "source_evidence_id": "prov-demo-rsset",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0xE2},
        "cleanup_scope": {"kind": "owned_descendants", "source_evidence_id": "prov-stale-base"},
        "accepted": True,
    }
    binding = {
        "rsset_use_site_binding_id": "bind-selected-gap",
        "hunk": 0,
        "addr": 0xE2,
        "operand_index": 0,
        "base_register": "A6",
        "displacement": 0x0102,
        "layout_name": "app",
        "base_symbol": "__amiga_app_base__",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "source_evidence_id": "prov-demo-rsset",
        "source_family": "rsset_app_base",
        "source_evidence_status": "path_specific",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0xE2},
        "confidence": "medium",
        "conflicts": [],
        "cleanup_scope": {"kind": "owned_descendants", "source_evidence_id": "prov-stale-base"},
        "base_evidence_refs": [base_ref],
    }
    reloaded_binding = {**binding, "owner_action_id": "manual-other"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"rsset_use_site_bindings": [reloaded_binding]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_rsset_binding_mutation(
        "demo",
        {"context": {"kind": "target"}},
        "rsset.binding.bind",
        {"action": {"action_id": "manual-1", "payload": {"rsset_use_site_binding": binding}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_rsset_use_site_binding"]["owner_action_id"] == "manual-1"
    assert semantic_layer["expected_rsset_use_site_binding"]["base_evidence_refs"] == [base_ref]
    assert semantic_layer["matching_rsset_use_site_bindings"] == []


def test_rsset_binding_match_treats_parent_evidence_ids_as_sets() -> None:
    base_ref = {
        "source_evidence_id": "prov-demo-rsset",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
    }
    expected = {
        "rsset_use_site_binding_id": "bind-selected-gap",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "source_evidence_id": "prov-demo-rsset",
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
        "base_evidence_refs": [base_ref],
    }
    actual = {
        **expected,
        "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"],
        "base_evidence_refs": [{**base_ref, "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"]}],
    }

    assert reversing_loop._rsset_binding_matches(actual, expected)

    actual["parent_evidence_ids"] = ["prov-parent-other"]

    assert not reversing_loop._rsset_binding_matches(actual, expected)


def test_rsset_binding_semantic_verifier_requires_selected_use_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sparse_binding = {
        "rsset_use_site_binding_id": "bind-selected-gap",
        "owner_action_id": "manual-1",
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"rsset_use_site_bindings": [sparse_binding]},
        ),
    )

    verification = reversing_loop._verify_project_rsset_binding(
        "demo",
        "rsset.binding.bind",
        sparse_binding,
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    assert verification["missing_identity_fields"] == [
        "hunk",
        "addr",
        "operand_index",
        "base_register",
        "displacement",
        "layout_name",
        "base_symbol",
        "base_evidence_id",
    ]


def test_rsset_binding_render_verifier_requires_ref_only_selected_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {"context": {"kind": "element", "locator": _listing_locator(), "element_id": "row-1:displacement:0"}}
    expected = {
        "rsset_use_site_binding_id": "bind-selected-gap",
        "base_register": "A6",
        "displacement": 0x0102,
        "operand_index": 0,
        "render_state": "linked_gap_or_raw",
    }
    rows: list[dict[str, object]] = [
        {
            **_listing_locator(),
            "text": "\tmove.b d0,$0102(a6)",
            "app_slot_refs": [],
        }
    ]

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        assert method == "GET"
        assert path == "/api/projects/demo/listing"
        return {"data": {"rows": rows}}

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    verification = reversing_loop._verify_projected_rsset_binding_rendered_source(
        "demo",
        command,
        "rsset.binding.bind",
        expected,
    )

    assert verification["status"] == "failed"
    assert verification["matched_raw_tokens"] == ["$0102(a6)"]
    assert verification["matching_app_slot_refs"] == []

    rows[0]["app_slot_refs"] = [
        {
            "symbol": "app_0102",
            "base_register": "A6",
            "displacement": 0x0102,
            "operand_index": 0,
        }
    ]

    verification = reversing_loop._verify_projected_rsset_binding_rendered_source(
        "demo",
        command,
        "rsset.binding.bind",
        expected,
    )

    assert verification["status"] == "passed"


def test_rsset_binding_render_verifier_rejects_raw_render_with_metadata_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {"context": {"kind": "element", "locator": _listing_locator(), "element_id": "row-1:displacement:0"}}
    expected = {
        "rsset_use_site_binding_id": "bind-selected-field",
        "base_register": "A6",
        "displacement": 0x0102,
        "operand_index": 0,
    }
    rows: list[dict[str, object]] = [
        {
            **_listing_locator(),
            "text": "\tmove.b d0,$0102(a6)",
            "app_slot_refs": [
                {
                    "symbol": "app_0102",
                    "base_register": "A6",
                    "displacement": 0x0102,
                    "operand_index": 0,
                }
            ],
        }
    ]

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        assert method == "GET"
        assert path == "/api/projects/demo/listing"
        return {"data": {"rows": rows}}

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    verification = reversing_loop._verify_projected_rsset_binding_rendered_source(
        "demo",
        command,
        "rsset.binding.bind",
        expected,
    )

    assert verification["status"] == "failed"
    assert verification["matching_app_slot_refs"]
    assert verification["matched_raw_tokens"] == ["$0102(a6)"]
    assert verification["matched_render_tokens"] == []

    rows[0]["text"] = "\tmove.b d0,app_0102(a6)"

    verification = reversing_loop._verify_projected_rsset_binding_rendered_source(
        "demo",
        command,
        "rsset.binding.bind",
        expected,
    )

    assert verification["status"] == "passed"
    assert verification["matched_render_tokens"] == ["app_0102"]


def test_rsset_binding_render_verifier_accepts_zero_displacement_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {"context": {"kind": "element", "locator": _listing_locator(), "element_id": "row-1:displacement:0"}}
    expected = {
        "rsset_use_site_binding_id": "bind-selected-base",
        "base_register": "A6",
        "displacement": 0,
        "operand_index": 0,
    }
    rows: list[dict[str, object]] = [
        {
            **_listing_locator(),
            "text": "\tmove.b d0,app_base(a6)",
            "app_slot_refs": [
                {
                    "symbol": "app_base",
                    "base_register": "A6",
                    "displacement": 0,
                    "operand_index": 0,
                }
            ],
        }
    ]

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        assert method == "GET"
        assert path == "/api/projects/demo/listing"
        return {"data": {"rows": rows}}

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    verification = reversing_loop._verify_projected_rsset_binding_rendered_source(
        "demo",
        command,
        "rsset.binding.bind",
        expected,
    )

    assert verification["status"] == "passed"
    assert verification["matched_render_tokens"] == ["app_base"]
    assert verification["matched_raw_tokens"] == []


def test_rsset_unbind_render_verifier_requires_raw_without_linked_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = {"context": {"kind": "element", "locator": _listing_locator(), "element_id": "row-1:displacement:0"}}
    expected = {
        "rsset_use_site_binding_id": "bind-selected-gap",
        "base_register": "A6",
        "displacement": 0x0102,
        "operand_index": 0,
    }
    rows: list[dict[str, object]] = [
        {
            **_listing_locator(),
            "text": "\tmove.b d0,$0102(a6)",
            "app_slot_refs": [
                {
                    "symbol": "app_0102",
                    "base_register": "A6",
                    "displacement": 0x0102,
                    "operand_index": 0,
                }
            ],
        }
    ]

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        assert method == "GET"
        assert path == "/api/projects/demo/listing"
        return {"data": {"rows": rows}}

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    verification = reversing_loop._verify_projected_rsset_binding_rendered_source(
        "demo",
        command,
        "rsset.binding.unbind",
        expected,
    )

    assert verification["status"] == "failed"
    assert verification["matched_raw_tokens"] == ["$0102(a6)"]
    assert verification["matching_app_slot_refs"]

    rows[0]["app_slot_refs"] = []

    verification = reversing_loop._verify_projected_rsset_binding_rendered_source(
        "demo",
        command,
        "rsset.binding.unbind",
        expected,
    )

    assert verification["status"] == "passed"


def test_rsset_unbind_verifier_requires_cleanup_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    binding = {
        "rsset_use_site_binding_id": "bind-selected-gap",
        "hunk": 0,
        "addr": 0xE2,
        "operand_index": 0,
        "base_register": "A6",
        "displacement": 0x0102,
        "layout_name": "app",
        "base_symbol": "__amiga_app_base__",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
    }
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"removed_rsset_use_site_bindings": [{**binding, "cleanup_action_id": "manual-other"}]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_rsset_binding_mutation(
        "demo",
        {"context": {"kind": "target"}},
        "rsset.binding.unbind",
        {"action": {"action_id": "manual-2", "payload": {"rsset_use_site_binding": binding}}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_rsset_use_site_binding"]["cleanup_action_id"] == "manual-2"
    assert semantic_layer["matching_rsset_use_site_bindings"] == []


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


def test_semantic_hint_candidate_skips_already_projected_hint() -> None:
    candidate = {
        "id": "semantic-lvo",
        "candidate_id": "semantic-lvo",
        "kind": "api_semantic_hint",
        "locator": _listing_locator(),
        "element_id": "row-1:immediate:0:-552",
        "element_kind": "immediate",
        "operand_index": 0,
        "value": -552,
        "domain": "lvo",
        "suggested_action_kinds": ["semantic.lvo.exec.library_OpenLibrary"],
        "current_metadata": {
            "kind": "semantic_hint",
            "hunk": 0,
            "addr": 0,
            "element_kind": "immediate",
            "operand_index": 0,
            "domain": "lvo",
            "symbol": "exec.library/OpenLibrary",
            "value": -552,
        },
        "default_verifier": "semantic_hint_state",
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_semantic_hint_verifier_requires_matching_provenance() -> None:
    expected = {
        **_semantic_hint_payload(),
        "source_evidence_id": "source:api-call",
        "source_family": "constant_or_equ",
        "source_evidence_status": "manual_classified",
        "parent_evidence_ids": ["parent:b", "parent:a"],
    }
    stale = _semantic_hint_payload()
    matched = {
        **_semantic_hint_payload(),
        "source_evidence_id": "source:api-call",
        "source_family": "constant_or_equ",
        "source_evidence_status": "manual_classified",
        "parent_evidence_ids": ["parent:a", "parent:b"],
    }

    assert not reversing_loop._semantic_hint_matches(stale, expected)
    assert reversing_loop._semantic_hint_matches(matched, expected)


def test_semantic_hint_verifier_requires_durable_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    action_hint = _semantic_hint_payload()
    local_effect_hint = {**_semantic_hint_payload(), "semantic_hint_id": "hint-local", "symbol": "exec.library/CloseLibrary"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"semantic_hints": [local_effect_hint]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_semantic_hint_mutation(
        "demo",
        {
            "action": {"action_id": "manual-1", "payload": {"semantic_hint": action_hint}},
            "application": {"local_effects": [{"kind": "semantic_hint", "semantic_hint": local_effect_hint}]},
        },
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_semantic_hint"]["symbol"] == "exec.library/OpenLibrary"
    assert semantic_layer["matching_semantic_hints"] == []


def test_semantic_hint_verifier_prefers_action_payload_over_local_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    action_hint = _semantic_hint_payload()
    local_effect_hint = {**_semantic_hint_payload(), "semantic_hint_id": "hint-local", "symbol": "exec.library/CloseLibrary"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"semantic_hints": [action_hint]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_semantic_hint_mutation(
        "demo",
        {
            "action": {"action_id": "manual-1", "payload": {"semantic_hint": action_hint}},
            "application": {"local_effects": [{"kind": "semantic_hint", "semantic_hint": local_effect_hint}]},
        },
        project_root=tmp_path,
    )

    assert verification["status"] == "passed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["expected_semantic_hint"]["symbol"] == "exec.library/OpenLibrary"


def test_semantic_hint_verifier_rejects_local_effect_without_action_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    local_effect_hint = {**_semantic_hint_payload(), "semantic_hint_id": "hint-local", "symbol": "exec.library/CloseLibrary"}
    monkeypatch.setattr(
        reversing_loop.projects,
        "get_project",
        lambda target_id, project_root: replace(
            _project(()),
            manual_state={"semantic_hints": [local_effect_hint]},
        ),
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_manual_log_matches_mutation",
        lambda target_id, durable_result, project_root: {"layer": "manual_action_log", "status": "passed"},
    )
    monkeypatch.setattr(
        reversing_loop,
        "_verify_round_trip_exact",
        lambda target_id, project_root: {"layer": "round_trip", "status": "passed"},
    )

    verification = reversing_loop._verify_semantic_hint_mutation(
        "demo",
        {"application": {"local_effects": [{"kind": "semantic_hint", "semantic_hint": local_effect_hint}]}},
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    semantic_layer = verification["layers"][1]
    assert semantic_layer["message"] == "missing semantic hint payload"


def test_semantic_hint_skip_requires_matching_provenance() -> None:
    candidate = {
        "id": "semantic-lvo",
        "candidate_id": "semantic-lvo",
        "kind": "api_semantic_hint",
        "locator": _listing_locator(),
        "element_id": "row-1:immediate:0:-552",
        "element_kind": "immediate",
        "operand_index": 0,
        "value": -552,
        "domain": "lvo",
        "source_evidence_id": "source:api-call",
        "source_family": "constant_or_equ",
        "source_evidence_status": "manual_classified",
        "suggested_action_kinds": ["semantic.lvo.exec.library_OpenLibrary"],
        "current_metadata": _semantic_hint_payload(),
        "default_verifier": "semantic_hint_state",
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert reversing_loop._candidate_skip_reason(candidate, command) is None
    candidate["current_metadata"] = {
        **_semantic_hint_payload(),
        "source_evidence_id": "source:api-call",
        "source_family": "constant_or_equ",
        "source_evidence_status": "manual_classified",
        "confidence": "high",
    }
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


def test_candidate_round_trip_default_cannot_authorize_unknown_command() -> None:
    candidate = {
        "id": "unknown-source-edit",
        "candidate_id": "unknown-source-edit",
        "kind": "unknown_source_edit",
        "suggested_action_kinds": ["future.semantic.write"],
        "default_verifier": "round_trip",
        "confidence": "high",
        "actionable": True,
    }
    command = {
        "kind": "command",
        "command_id": "future.semantic.write",
        "context": {"kind": "target"},
        "parameters": {},
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
        "parameters": {
            "struct_name": "DerivedEvent",
            "offset": 36,
            "name": "de_Code",
            "type": "UWORD",
            "size": 2,
        },
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) is None
    assert reversing_loop._candidate_skip_reason(candidate, command) == "missing action-specific verifier"


def test_typed_field_command_with_accepted_evidence_gets_field_verifier() -> None:
    evidence = {**_accepted_struct_pointer_evidence(), "parent_evidence_ids": ["prov-base-a0"]}
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
        **evidence,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["parameters"] == {
        "struct_name": "DerivedEvent",
        "offset": 36,
        "name": "de_Code",
        "type": "UWORD",
        "size": 2,
        **evidence,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "custom_struct_field_state"


def test_typed_field_skip_treats_parent_evidence_ids_as_set() -> None:
    evidence = {**_accepted_struct_pointer_evidence(), "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"]}
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
        "current_metadata": {
            "struct_name": "DerivedEvent",
            "offset": 36,
            "name": "de_Code",
            "type": "UWORD",
            "size": 2,
            **evidence,
            "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"],
        },
        "confidence": "high",
        "actionable": True,
        **evidence,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_typed_field_availability_requires_matching_source_evidence() -> None:
    evidence = {**_accepted_struct_pointer_evidence(), "parent_evidence_ids": ["prov-base-a0"]}
    command = {
        "command_id": "typed_gap.field.add",
        "parameters": {
            "struct_name": "DerivedEvent",
            "offset": 36,
            "name": "de_Code",
            "type": "UWORD",
            "size": 2,
            **evidence,
        },
    }
    availability = {
        "commands": [
            {
                "command_id": "typed_gap.field.add",
                "parameters": {
                    "struct_name": "DerivedEvent",
                    "offset": 36,
                    **evidence,
                    "source_evidence_id": "prov-other",
                },
            }
        ]
    }

    assert reversing_loop._available_catalog_command(command, availability) is None

    command_parameters = cast(dict[str, object], command["parameters"])
    del command_parameters["source_evidence_id"]

    assert reversing_loop._available_catalog_command(command, availability) is None

    command_parameters["source_evidence_id"] = evidence["source_evidence_id"]
    availability_parameters = cast(dict[str, object], availability["commands"][0]["parameters"])
    availability_parameters["source_evidence_id"] = evidence["source_evidence_id"]
    availability_parameters["path_lifetime_scope"] = {"kind": "selected_use", "hunk": 0, "addr": 2, "operand_index": 1}

    assert reversing_loop._available_catalog_command(command, availability) is None

    availability_parameters["path_lifetime_scope"] = evidence["path_lifetime_scope"]

    availability_parameters["parent_evidence_ids"] = ["prov-other-base"]
    assert reversing_loop._available_catalog_command(command, availability) is None

    availability_parameters["parent_evidence_ids"] = evidence["parent_evidence_ids"]

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]


def test_typed_field_command_does_not_accept_cleanup_scope_as_consumed_evidence() -> None:
    command = {
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
        },
        "parameters": {
            "struct_name": "DerivedEvent",
            "offset": 36,
            "name": "de_Code",
            "type": "UWORD",
            "size": 2,
            "cleanup_scope": {
                "kind": "owned_descendants",
                **_accepted_struct_pointer_evidence(),
            },
        },
        "output_affecting": True,
    }

    assert reversing_loop._candidate_verifier({}, command) is None


def test_typed_field_command_rejects_selected_access_width_mismatch() -> None:
    evidence = _accepted_struct_pointer_evidence()
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
        "width_bytes": 4,
        "root_struct_name": "InputEvent",
        "refined_struct_name": "DerivedEvent",
        "classification": "prefix_extension",
        "suggested_action_kinds": ["typed_gap.field.add"],
        "parameters": {"name": "de_Code", "type": "UWORD", "size": 2},
        "confidence": "high",
        "actionable": True,
        **evidence,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["context"]["width_bytes"] == 4
    assert reversing_loop._candidate_verifier(candidate, command) is None
    assert reversing_loop._candidate_skip_reason(candidate, command) == "typed field shape mismatch"


def test_typed_field_command_rejects_selected_struct_mismatch() -> None:
    evidence = _accepted_struct_pointer_evidence()
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
        "width_bytes": 2,
        "root_struct_name": "InputEvent",
        "refined_struct_name": "DerivedEvent",
        "classification": "prefix_extension",
        "suggested_action_kinds": ["typed_gap.field.add"],
        "parameters": {"struct_name": "OtherEvent", "name": "de_Code", "type": "UWORD", "size": 2},
        "confidence": "high",
        "actionable": True,
        **evidence,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["context"]["refined_struct_name"] == "DerivedEvent"
    assert command["parameters"]["struct_name"] == "OtherEvent"
    assert reversing_loop._candidate_verifier(candidate, command) is None
    assert reversing_loop._candidate_skip_reason(candidate, command) == "typed field shape mismatch"


def test_typed_field_command_rejects_selected_struct_bounds_mismatch() -> None:
    evidence = _accepted_struct_pointer_evidence()
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
        "struct_size": 40,
        "root_struct_name": "InputEvent",
        "refined_struct_name": "DerivedEvent",
        "classification": "prefix_extension",
        "suggested_action_kinds": ["typed_gap.field.add"],
        "parameters": {"name": "de_Code", "type": "ULONG", "size": 8},
        "confidence": "high",
        "actionable": True,
        **evidence,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["context"]["struct_size"] == 40
    assert reversing_loop._candidate_verifier(candidate, command) is None
    assert reversing_loop._candidate_skip_reason(candidate, command) == "typed field shape mismatch"


def test_manual_override_typed_field_requires_cleanup_scope_before_execution() -> None:
    evidence = {
        **_accepted_struct_pointer_evidence(),
        "source_evidence_status": "manual_override",
        "conflicts": [{"source_evidence_id": "prov-old"}],
        "contradicted_evidence_id": "prov-old",
        "reason": "target-specific path proof",
    }
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
        **evidence,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert reversing_loop._candidate_verifier(candidate, command) is None
    assert reversing_loop._candidate_skip_reason(candidate, command) == "missing action-specific verifier"

    cleanup_scope = {"kind": "owned_descendants", "source_evidence_id": "prov-old"}
    candidate["cleanup_scope"] = cleanup_scope
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["parameters"]["cleanup_scope"] == cleanup_scope
    assert reversing_loop._candidate_verifier(candidate, command) == "custom_struct_field_state"


def test_manual_override_typed_field_requires_string_boundary_fields_before_execution() -> None:
    evidence = {
        **_accepted_struct_pointer_evidence(),
        "source_evidence_status": "manual_override",
        "conflicts": [{"source_evidence_id": "prov-old"}],
        "contradicted_evidence_id": True,
        "reason": ["target-specific path proof"],
        "cleanup_scope": {"kind": "owned_descendants", "source_evidence_id": "prov-old"},
    }
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
        **evidence,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert reversing_loop._candidate_verifier(candidate, command) is None
    assert reversing_loop._candidate_skip_reason(candidate, command) == "missing action-specific verifier"


def test_manual_override_typed_field_requires_cleanup_scope_to_match_contradicted_evidence() -> None:
    evidence = {
        **_accepted_struct_pointer_evidence(),
        "source_evidence_status": "manual_override",
        "conflicts": [{"source_evidence_id": "prov-old"}],
        "contradicted_evidence_id": "prov-old",
        "reason": "target-specific path proof",
        "cleanup_scope": {"kind": "owned_descendants", "source_evidence_id": "prov-other"},
    }
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
        **evidence,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert reversing_loop._candidate_verifier(candidate, command) is None
    assert reversing_loop._candidate_skip_reason(candidate, command) == "missing action-specific verifier"


def test_manual_override_data_block_type_requires_cleanup_scope_before_execution() -> None:
    evidence = {
        "source_evidence_id": "prov-demo-data-block-pointer",
        "source_family": "data_block_pointer",
        "source_evidence_status": "manual_override",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x40},
        "conflicts": [{"source_evidence_id": "prov-old"}],
        "contradicted_evidence_id": "prov-old",
        "reason": "target-specific table pointer",
    }
    candidate = {
        "id": "data-block-type",
        "candidate_id": "data-block-type",
        "kind": "data_block_type_binding",
        "confidence": "high",
        "actionable": True,
    }
    command = {
        "kind": "command",
        "command_id": "row.data_block.element.bind_type",
        "context": {"kind": "row", "locator": _listing_locator(kind="data")},
        "parameters": {
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            "binding_kind": "custom_struct",
            "type_id": "InputEvent",
            "requires_source_evidence": True,
            **evidence,
        },
        "output_affecting": True,
    }

    assert reversing_loop._candidate_verifier(candidate, command) is None

    cleanup_scope = {"kind": "owned_descendants", "source_evidence_id": "prov-old"}
    cast(dict[str, object], command["parameters"])["cleanup_scope"] = cleanup_scope

    assert command["parameters"]["cleanup_scope"] == cleanup_scope
    assert reversing_loop._candidate_verifier(candidate, command) == "data_block_element_state"


def test_data_block_type_command_does_not_accept_cleanup_scope_as_consumed_evidence() -> None:
    command = {
        "kind": "command",
        "command_id": "row.data_block.element.bind_type",
        "context": {"kind": "row", "locator": _listing_locator(kind="data")},
        "parameters": {
            "layout_id": "layout-1",
            "offset": 0,
            "binding_kind": "custom_struct",
            "type_id": "InputEvent",
            "requires_source_evidence": True,
            "cleanup_scope": {
                "kind": "owned_descendants",
                "source_evidence_id": "prov-old",
                "source_family": "data_block_pointer",
                "source_evidence_status": "analysis_proven",
                "path_lifetime_scope": {"kind": "global"},
            },
        },
        "output_affecting": True,
    }

    assert reversing_loop._candidate_verifier({}, command) is None


def test_data_block_type_skip_uses_active_binding_and_parent_evidence_set() -> None:
    evidence = {
        "source_evidence_id": "prov-demo-data-block-pointer",
        "source_family": "data_block_pointer",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "global"},
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
    }
    candidate = {
        "id": "data-block-type",
        "candidate_id": "data-block-type",
        "kind": "data_block_type_binding",
        "current_metadata": {
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            "type_binding": {
                "binding_kind": "custom_struct",
                "bound_type_id": "InputEvent",
                **evidence,
                "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"],
            },
        },
        "confidence": "high",
        "actionable": True,
    }
    command = {
        "kind": "command",
        "command_id": "row.data_block.element.bind_type",
        "context": {"kind": "row", "locator": _listing_locator(kind="data")},
        "parameters": {
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            "binding_kind": "custom_struct",
            "type_id": "InputEvent",
            "requires_source_evidence": True,
            **evidence,
        },
        "output_affecting": True,
    }

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_data_block_clear_type_skip_uses_previous_binding_and_parent_evidence_set() -> None:
    evidence = {
        "source_evidence_id": "prov-demo-data-block-pointer",
        "source_family": "data_block_pointer",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "global"},
        "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"],
    }
    previous_binding = {
        "type_binding_id": "events:30:4:platform_struct:Node",
        "binding_kind": "platform_struct",
        "bound_type_id": "Node",
        "owner_action_id": "manual-bind",
        **evidence,
    }
    candidate = {
        "id": "data-block-clear-type",
        "candidate_id": "data-block-clear-type",
        "kind": "data_block_type_binding_clear",
        "current_metadata": {
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            "kind": "scalar",
            "previous_type_binding": {
                **previous_binding,
                "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"],
                "cleanup_action_id": "manual-clear",
            },
        },
        "default_verifier": "data_block_element_state",
        "confidence": "high",
        "actionable": True,
    }
    command = {
        "kind": "command",
        "command_id": "row.data_block.element.clear_type",
        "context": {"kind": "row", "locator": _listing_locator(kind="data")},
        "parameters": {
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            **previous_binding,
        },
        "output_affecting": True,
    }

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )

    cast(dict[str, object], cast(dict[str, object], candidate["current_metadata"])["previous_type_binding"])[
        "source_evidence_id"
    ] = "prov-other-data-block-pointer"

    assert reversing_loop._candidate_skip_reason(candidate, command) is None


def test_typed_field_candidate_skips_already_projected_field() -> None:
    field = {"struct_name": "DerivedEvent", "offset": 36, "name": "de_Code", "type": "UWORD", "size": 2}
    candidate = {
        "id": "typed-gap-field",
        "candidate_id": "typed-gap-field",
        "kind": "typed_gap_field",
        "locator": _listing_locator(),
        "element_id": "row-1:typed_gap:1:A0:36",
        "element_kind": "typed_gap",
        "displacement": 36,
        "refined_struct_name": "DerivedEvent",
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


def test_typed_field_remove_skip_uses_removed_field_identity_and_parent_evidence_set() -> None:
    evidence = {**_accepted_struct_pointer_evidence(), "parent_evidence_ids": ["prov-parent-b", "prov-parent-a"]}
    field = {"struct_name": "DerivedEvent", "offset": 36, "name": "de_Code", "type": "UWORD", "size": 2}
    candidate = {
        "id": "typed-access-field-remove",
        "candidate_id": "typed-access-field-remove",
        "kind": "typed_access_field",
        "locator": _listing_locator(),
        "element_id": "row-1:typed_access:1:A0:36",
        "element_kind": "typed_access",
        "field_offset": 36,
        "owner_struct_name": "DerivedEvent",
        "field_name": "de_Code",
        "width_bytes": 2,
        "suggested_action_kinds": ["typed_access.field.remove"],
        "parameters": field,
        "current_metadata": {
            "removed": True,
            "custom_struct_field": {
                **field,
                **evidence,
                "parent_evidence_ids": ["prov-parent-a", "prov-parent-b"],
            },
        },
        "evidence": evidence,
        "default_verifier": "custom_struct_field_state",
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )

    cast(dict[str, object], cast(dict[str, object], candidate["current_metadata"])["custom_struct_field"])[
        "source_evidence_id"
    ] = "prov-other-struct-pointer"

    assert reversing_loop._candidate_skip_reason(candidate, command) is None


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


def test_target_equate_representation_candidate_strips_provenance_parameters() -> None:
    candidate = {
        "id": "target-equate-representation",
        "candidate_id": "target-equate-representation",
        "kind": "target_equate_representation",
        "suggested_action_kinds": ["target.equate.represent"],
        "parameters": {
            "name": "ASCII_SPACE",
            "value": 32,
            "value_representation": "character",
            "source_evidence_id": "prov-constant",
            "source_family": "constant_or_equ",
            "path_lifetime_scope": {"kind": "global"},
        },
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command == {
        "kind": "command",
        "command_id": "target.equate.represent",
        "context": {"kind": "target"},
        "parameters": {"name": "ASCII_SPACE", "value": 32, "value_representation": "character"},
        "output_affecting": True,
    }
    assert reversing_loop._candidate_verifier(candidate, command) == "target_equate_state"


def test_embedded_target_equate_representation_command_strips_provenance_parameters() -> None:
    candidate = {
        "id": "target-equate-representation",
        "candidate_id": "target-equate-representation",
        "kind": "target_equate_representation",
        "command": {
            "command_id": "target.equate.represent",
            "context": {
                "kind": "target",
                "source_evidence_id": "prov-constant",
                "source_family": "constant_or_equ",
            },
            "parameters": {
                "name": "ASCII_SPACE",
                "value": 32,
                "value_expression": "SPACE_CHAR",
                "source_evidence_id": "prov-constant",
                "source_family": "constant_or_equ",
            },
            "output_affecting": True,
        },
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["context"] == {"kind": "target"}
    assert command["parameters"] == {
        "name": "ASCII_SPACE",
        "value": 32,
        "value_expression": "SPACE_CHAR",
    }


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


def test_target_equate_candidate_skip_ignores_stripped_provenance_parameters() -> None:
    candidate = {
        "id": "target-equate",
        "candidate_id": "target-equate",
        "kind": "target_equate",
        "suggested_action_kinds": ["target.equate.add"],
        "parameters": {
            "name": "PLAYER_START_LIVES",
            "value": 3,
            "source_evidence_id": "constant-1",
            "source_family": "constant_or_equ",
        },
        "current_metadata": {"name": "PLAYER_START_LIVES", "value": 3},
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["parameters"] == {"name": "PLAYER_START_LIVES", "value": 3}
    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_target_equate_representation_skip_ignores_stripped_provenance_parameters() -> None:
    candidate = {
        "id": "target-equate-representation",
        "candidate_id": "target-equate-representation",
        "kind": "target_equate_representation",
        "suggested_action_kinds": ["target.equate.represent"],
        "parameters": {
            "name": "ASCII_SPACE",
            "value": 32,
            "value_representation": "character",
            "source_evidence_id": "prov-constant",
        },
        "current_metadata": {
            "name": "ASCII_SPACE",
            "value": 32,
            "value_representation": "character",
        },
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )


def test_embedded_target_equate_rename_command_strips_provenance_parameters() -> None:
    candidate = {
        "id": "target-equate-rename",
        "candidate_id": "target-equate-rename",
        "kind": "target_equate",
        "command": {
            "command_id": "target.equate.rename",
            "context": {"kind": "target"},
            "parameters": {
                "previous_name": "PLAYER_START_LIVES",
                "name": "PLAYER_INITIAL_LIVES",
                "source_evidence_id": "constant-1",
                "source_family": "constant_or_equ",
            },
            "output_affecting": True,
        },
        "confidence": "high",
        "actionable": True,
    }

    command = reversing_loop._candidate_command_options(candidate)[0]

    assert command["parameters"] == {
        "previous_name": "PLAYER_START_LIVES",
        "name": "PLAYER_INITIAL_LIVES",
    }


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


def test_correction_suppress_seeded_item_availability_requires_matching_identity() -> None:
    command = {
        "command_id": "correction.suppress_seeded_item.seeded_entity",
        "parameters": {"kind": "seeded_entity", "hunk": 0, "addr": 0x100},
    }
    availability = {
        "commands": [
            {
                "command_id": "correction.suppress_seeded_item.seeded_entity",
                "parameters": {"kind": "seeded_entity", "hunk": 0, "addr": 0x104},
            }
        ]
    }

    assert reversing_loop._available_catalog_command(command, availability) is None

    command_parameters = cast(dict[str, object], command["parameters"])
    del command_parameters["addr"]

    assert reversing_loop._available_catalog_command(command, availability) is None

    command_parameters["addr"] = 0x100
    availability_parameters = cast(dict[str, object], availability["commands"][0]["parameters"])
    availability_parameters["addr"] = 0x100

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]

    availability_parameters["end"] = 0x104

    assert reversing_loop._available_catalog_command(command, availability) is None

    command_parameters["end"] = 0x104

    assert reversing_loop._available_catalog_command(command, availability) == availability["commands"][0]


def test_correction_suppress_seeded_item_skips_already_projected_suppression() -> None:
    candidate = {
        "id": "suppress-seeded-entity",
        "candidate_id": "suppress-seeded-entity",
        "kind": "seeded_item_correction",
        "locator": _listing_locator(kind="data"),
        "suggested_action_kinds": ["correction.suppress_seeded_item.seeded_entity"],
        "parameters": {"kind": "seeded_entity", "hunk": 0, "addr": 0x100, "end": 0x104},
        "current_metadata": {"suppressed": True, "kind": "seeded_entity", "hunk": 0, "addr": 0x100, "end": 0x104},
        "confidence": "high",
        "actionable": True,
    }
    command = reversing_loop._candidate_command_options(candidate)[0]

    assert (
        reversing_loop._candidate_skip_reason(candidate, command)
        == "candidate already satisfied in projected semantic state"
    )

    cast(dict[str, object], candidate["current_metadata"])["end"] = 0x108

    assert reversing_loop._candidate_skip_reason(candidate, command) is None


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


def test_command_availability_returns_error_for_stale_locator(monkeypatch: pytest.MonkeyPatch) -> None:
    def route_request(method: str, path: str, query: dict[str, list[str]]) -> dict[str, object]:
        raise reversing_loop.server.CommandContractError("missing_locator", "locator row_key is not in current projection")

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    availability = reversing_loop._command_availability(
        "demo",
        {"kind": "row", "locator": _listing_locator()},
    )

    assert availability == {
        "error": {
            "code": "missing_locator",
            "message": "locator row_key is not in current projection",
        }
    }


def test_command_availability_query_preserves_provenance_context() -> None:
    locator = _listing_locator()
    scope = {"kind": "selected_use", "hunk": 0, "addr": 0x20}
    conflicts = [{"source_evidence_id": "prov-old"}]
    parents = ["prov-base"]
    cleanup_scope = {"kind": "owned_descendants", "source_evidence_id": "prov-old"}

    assert reversing_loop._command_query_from_context(
        {
            "kind": "row",
            "locator": locator,
            "source_evidence_id": "prov-data-block",
            "source_family": "data_block_pointer",
            "source_evidence_status": "manual_classified",
            "path_lifetime_scope": scope,
            "confidence": "medium",
            "conflicts": conflicts,
            "parent_evidence_ids": parents,
            "contradicted_evidence_id": "prov-old",
            "reason": "target-specific pointer proof",
            "cleanup_scope": cleanup_scope,
        }
    ) == {
        "context": ["row"],
        "locator": [json.dumps(locator)],
        "source_evidence_id": ["prov-data-block"],
        "source_family": ["data_block_pointer"],
        "source_evidence_status": ["manual_classified"],
        "confidence": ["medium"],
        "contradicted_evidence_id": ["prov-old"],
        "reason": ["target-specific pointer proof"],
        "path_lifetime_scope": [json.dumps(scope, sort_keys=True, separators=(",", ":"))],
        "conflicts": [json.dumps(conflicts, sort_keys=True, separators=(",", ":"))],
        "parent_evidence_ids": [json.dumps(parents, sort_keys=True, separators=(",", ":"))],
        "cleanup_scope": [json.dumps(cleanup_scope, sort_keys=True, separators=(",", ":"))],
    }


def test_element_command_availability_query_preserves_binding_and_provenance_context() -> None:
    locator = _listing_locator()
    scope = {"kind": "selected_use", "hunk": 0, "addr": 0x40, "operand_index": 0}

    assert reversing_loop._command_query_from_context(
        {
            "kind": "element",
            "locator": locator,
            "element_id": "row-1:displacement:0:operand",
            "layout_name": "app",
            "base_symbol": "__app_base__",
            "base_evidence_id": "prov-base-a6",
            "source_evidence_id": "prov-rsset",
            "source_family": "rsset_app_base",
            "source_evidence_status": "manual_override",
            "path_lifetime_scope": scope,
            "contradicted_evidence_id": "prov-old",
            "reason": "selected app base",
        }
    ) == {
        "context": ["element"],
        "locator": [json.dumps(locator)],
        "element_id": ["row-1:displacement:0:operand"],
        "layout_name": ["app"],
        "base_symbol": ["__app_base__"],
        "base_evidence_id": ["prov-base-a6"],
        "contradicted_evidence_id": ["prov-old"],
        "reason": ["selected app base"],
        "source_evidence_id": ["prov-rsset"],
        "source_family": ["rsset_app_base"],
        "source_evidence_status": ["manual_override"],
        "path_lifetime_scope": [json.dumps(scope, sort_keys=True, separators=(",", ":"))],
    }


def test_report_only_candidate_is_visible_but_not_selectable() -> None:
    candidate = {
        "id": "provenance-report",
        "candidate_id": "provenance-report",
        "kind": "provenance_report",
        "context": {
            "kind": "element",
            "locator": _listing_locator(),
            "element_id": "row-1:register:0:a6",
        },
        "suggested_action_kinds": ["provenance.definition.report"],
        "confidence": "high",
        "actionable": True,
    }
    inspect_report = _inspect_with_locator()
    inspect_report["candidate_work"] = [candidate]

    command = reversing_loop._candidate_command_options(candidate)[0]
    selected = reversing_loop._select_command_action(inspect_report)

    assert command["command_id"] == "provenance.definition.report"
    assert command["effect"] == "inspection"
    assert command["appends_to_manual_action_log"] is False
    assert reversing_loop._candidate_skip_reason(candidate, command) == "command is report-only"
    assert selected is None
    assert inspect_report["planner"]["ranked_candidates"][0]["candidate_commands"] == [
        {
            "command_id": "provenance.definition.report",
            "output_affecting": False,
            "verifier": None,
            "execution_policy": "report_only",
        }
    ]
    assert reversing_loop._command_summary(
        {
            "kind": "command",
            "command_id": "rsset.binding.report",
            "context": command["context"],
            "parameters": {},
            "effect": "inspection",
            "appends_to_manual_action_log": False,
            "output_affecting": False,
        },
        candidate,
    ) == {
        "command_id": "rsset.binding.report",
        "output_affecting": False,
        "verifier": None,
        "execution_policy": "report_only",
    }


def test_legacy_provenance_explore_command_is_not_a_planner_report_command() -> None:
    candidate = {
        "id": "legacy-provenance-report",
        "candidate_id": "legacy-provenance-report",
        "kind": "provenance_report",
        "context": {
            "kind": "element",
            "locator": _listing_locator(),
            "element_id": "row-1:register:0:a6",
        },
        "suggested_action_kinds": ["provenance.explore_definition"],
        "confidence": "high",
        "actionable": True,
    }

    assert reversing_loop._candidate_command_options(candidate) == []


def test_run_one_blocks_stale_report_only_selection_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    selected = {
        "work_item": {"kind": "provenance_report", "confidence": "high"},
        "command": {
            "kind": "command",
            "command_id": "provenance.definition.report",
            "context": {
                "kind": "element",
                "locator": _listing_locator(),
                "element_id": "row-1:register:0:a6",
            },
            "parameters": {},
            "effect": "inspection",
            "appends_to_manual_action_log": False,
            "output_affecting": False,
        },
    }
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: _inspect_with_locator())
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda inspect_report: selected)
    monkeypatch.setattr(
        reversing_loop.server,
        "route_request",
        lambda method, path, query, body=None: (_ for _ in ()).throw(AssertionError("report-only command executed")),
    )

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert report["action_result"]["status"] == "blocked"
    assert report["verification"]["layers"] == [
        {
            "layer": "command_execution_policy",
            "status": "failed",
            "message": "command is report-only",
            "command_id": "provenance.definition.report",
        }
    ]


def test_run_one_blocks_catalog_inspection_entry_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    selected = {
        "work_item": {
            "kind": "api_register_seed",
            "confidence": "high",
            "suggested_action_kinds": ["semantic.library_base.exec.library"],
        },
        "command": {
            "kind": "command",
            "command_id": "semantic.library_base.exec.library",
            "context": {
                "kind": "element",
                "locator": _listing_locator(),
                "element_id": "row-1:register:0:a6",
            },
            "parameters": {"register": "A6"},
            "output_affecting": True,
        },
    }
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(reversing_loop, "inspect_target", lambda target_id, project_root: inspect_report)
    monkeypatch.setattr(reversing_loop, "_select_command_action", lambda report: selected)

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if method == "GET" and path.endswith("/commands"):
            return {
                "data": {
                    "commands": [
                        {
                            "command_id": "semantic.library_base.exec.library",
                            "effect": "inspection",
                            "appends_to_manual_action_log": False,
                        }
                    ]
                }
            }
        raise AssertionError("catalog inspection entry executed")

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    report = reversing_loop.run_one_iteration("demo", mode="clean-run", project_root=tmp_path)

    assert calls == [("GET", "/api/projects/demo/commands")]
    assert report["action_result"]["status"] == "blocked"
    assert report["verification"]["layers"][0]["layer"] == "command_execution_policy"
    assert report["verification"]["layers"][0]["command_id"] == "semantic.library_base.exec.library"


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
        "durable_payload",
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


def test_representation_verifier_rejects_mismatched_durable_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    _write_manual_log(tmp_path)
    _write_reproduction_exact(tmp_path)
    command = _representation_command()
    wrong_representation = {**_representation_payload(), "style": "hex"}

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        if path.endswith("/listing/open"):
            return {"data": {"job_id": "job-1", "status": "ready"}}
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {"representations": [wrong_representation]}}}}
        if path.endswith("/listing"):
            return {"data": {"rows": [_listing_row(text="\tmove.b #$41,d0\n", end_offset=4)]}}
        raise AssertionError(path)

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    verification = reversing_loop._verify_manual_mutation(
        "demo",
        command,
        _executed_representation_payload(tmp_path, representation=wrong_representation),
        project_root=tmp_path,
    )

    assert verification["status"] == "failed"
    durable_layer = verification["layers"][1]
    assert durable_layer["layer"] == "durable_payload"
    assert durable_layer["mismatches"]["style"] == {"expected": "character", "actual": "hex"}


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
            return {"data": _executed_listing_comment_payload(tmp_path, text="entrypoint returns")}
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
            return {"data": _executed_listing_comment_payload(tmp_path, text="custom comment")}
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


def _executed_representation_payload(
    tmp_path: Path,
    *,
    representation: dict[str, object] | None = None,
) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    representation = dict(representation or _representation_payload())
    return {
        "action": {"action_id": "manual-1", "representation": representation},
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


def _execution_view_remove_payload() -> dict[str, object]:
    return {
        "source_start": 0x20,
        "source_end": 0x80,
        "base_addr": 0x4000,
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
    view = _execution_view_remove_payload()
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


def _executed_data_symbol_payload(tmp_path: Path, data_symbol: dict[str, object]) -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    return {
        "action": {"action_id": "manual-1", "payload": {"data_symbol": dict(data_symbol)}},
        "application": {
            "local_effects": [{"kind": "data_symbol_rename", "data_symbol": dict(data_symbol)}],
        },
        "mutation": {
            "durable_action_id": "manual-1",
            "manual_action_log_count": state["count"],
            "manual_action_log_head_hash": state["head_hash"],
            "effective_metadata_hash": "f" * 64,
            "affected_locators": [
                _listing_locator(kind="data", end_offset=cast(int, data_symbol.get("end", 2))),
            ],
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


def _executed_data_block_layout_payload(tmp_path: Path, data_block_layout: dict[str, object]) -> dict[str, object]:
    payload = _executed_command_payload()
    payload["action"] = {"action_id": "manual-1", "payload": {"data_block_layout": dict(data_block_layout)}}
    payload["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    payload["application"] = {
        "status": "applied",
        "local_effects": [{"kind": "data_block_layout", "data_block_layout": dict(data_block_layout)}],
    }
    return payload


def _executed_data_block_element_payload(tmp_path: Path, data_block_element: dict[str, object]) -> dict[str, object]:
    payload = _executed_command_payload()
    payload["action"] = {"action_id": "manual-1", "payload": {"data_block_element": dict(data_block_element)}}
    payload["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    payload["application"] = {
        "status": "applied",
        "local_effects": [{"kind": "data_block_element", "data_block_element": dict(data_block_element)}],
    }
    return payload


def _executed_data_block_interpreted_ref_payload(
    tmp_path: Path,
    data_block_interpreted_ref: dict[str, object],
) -> dict[str, object]:
    payload = _executed_command_payload()
    payload["action"] = {
        "action_id": "manual-1",
        "payload": {"data_block_interpreted_ref": dict(data_block_interpreted_ref)},
    }
    payload["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    payload["application"] = {
        "status": "applied",
        "local_effects": [
            {
                "kind": "data_block_interpreted_ref",
                "data_block_interpreted_ref": dict(data_block_interpreted_ref),
            }
        ],
    }
    return payload


def _executed_custom_struct_field_payload(tmp_path: Path, custom_struct_field: dict[str, object]) -> dict[str, object]:
    payload = _executed_command_payload()
    payload["action"] = {
        "action_id": "manual-1",
        "payload": {"custom_struct_field": dict(custom_struct_field)},
    }
    payload["mutation"]["manual_action_log_head_hash"] = reversing_loop._manual_action_log_state(
        tmp_path / "targets" / "demo"
    )["head_hash"]
    payload["application"] = {
        "status": "applied",
        "local_effects": [{"kind": "custom_struct_field", "custom_struct_field": dict(custom_struct_field)}],
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
    runtime_address_refs: list[dict[str, object]] | None = None,
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
    if runtime_address_refs is not None:
        row["runtime_address_refs"] = runtime_address_refs
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


def _accepted_struct_pointer_evidence() -> dict[str, object]:
    return {
        "source_evidence_id": "prov-demo-struct-pointer-h0-00000000-op1-A0-d0024",
        "source_family": "struct_pointer",
        "source_evidence_status": "analysis_proven",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0, "operand_index": 1},
        "confidence": "high",
        "conflicts": [],
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


def _executed_listing_comment_payload(tmp_path: Path, *, text: str = "xref-backed test comment") -> dict[str, object]:
    state = cast(dict[str, object], reversing_loop._manual_action_log_state(tmp_path / "targets" / "demo"))
    locator = _listing_locator()
    comment = {
        "comment_id": "catalog-comment-h0-00000000",
        "text": text,
        "hunk": locator["section_index"],
        "addr": locator["start_offset"],
        "end": locator["end_offset"],
    }
    return {
        "action": {"action_id": "manual-1", "payload": {"comment": comment}},
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
