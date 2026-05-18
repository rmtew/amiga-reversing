from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from amiga_reversing.disasm import projects, server
from amiga_reversing.disasm.manual_actions import review_item_is_open
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.reversing_workspace import (
    clean_run_target_workspace,
    inspect_target_hygiene,
)

TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "stopped"})
PARTIAL_ITERATION_STATUSES = frozenset({"started", "running", "partial"})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Operate the agentic reversing loop.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    hygiene_parser = subparsers.add_parser("hygiene", help="Classify target-local files without deleting them.")
    hygiene_parser.add_argument("--target", required=True)

    clean_parser = subparsers.add_parser("clean-run", help="Reset classified generated/local target state.")
    clean_parser.add_argument("--target", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Emit read-only target state and candidate work.")
    inspect_parser.add_argument("--target", required=True)

    run_parser = subparsers.add_parser("run-one", help="Run one safe reversing loop iteration.")
    run_parser.add_argument("--target", required=True)
    run_parser.add_argument("--mode", choices=("continue", "clean-run", "reimport"), default="continue")
    run_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "hygiene":
        report = inspect_target_hygiene(
            args.target,
            mode="inspect",
            project_root=args.project_root,
        )
        _print_json(report.to_dict())
        return 0
    if args.command == "clean-run":
        report = clean_run_target_workspace(args.target, project_root=args.project_root)
        _print_json(report.to_dict())
        return 0
    if args.command == "inspect":
        _print_json(inspect_target(args.target, project_root=args.project_root))
        return 0
    if args.command == "run-one":
        _print_json(
            run_one_iteration(
                args.target,
                mode=args.mode,
                dry_run=args.dry_run,
                project_root=args.project_root,
            )
        )
        return 0
    raise SystemExit(f"Unsupported command: {args.command}")


def inspect_target(target_id: str, *, project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    hygiene = inspect_target_hygiene(target_id, mode="inspect", project_root=project_root)
    target_dir = Path(hygiene.target_dir)
    project_payload = _project_state_payload(target_id, project_root)
    candidates = _candidate_work_items(project_payload.get("review_items"))
    return {
        "target_id": target_id,
        "mode": "inspect",
        "hygiene": hygiene.to_dict(),
        "target_state": {
            "target_dir": str(target_dir),
            "manual_action_log": _manual_action_log_state(target_dir),
            "project": project_payload,
            "projection": {
                "projection_hash": None,
                "available": False,
                "reason": "listing projection is available after listing artifact generation",
            },
            "round_trip": _round_trip_state(target_dir),
        },
        "candidate_work": candidates,
        "verification_paths": _verification_paths(target_dir),
        "safe_to_mutate": hygiene.safe_to_continue and not hygiene.unknown_files,
    }


def run_one_iteration(
    target_id: str,
    *,
    mode: str = "continue",
    dry_run: bool = False,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    run_result = start_or_resume_run(target_id, mode=mode, project_root=project_root)
    if run_result.status == "blocked":
        return run_result.to_dict()
    if run_result.run_state is None:
        raise ValueError("run state is required")
    inspect_report = inspect_target(target_id, project_root=project_root)
    iteration_id = _next_iteration_id(run_result.run_state)
    selected = _select_command_action(inspect_report)
    if selected is None:
        report = _iteration_report(
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report=inspect_report,
            selected_work_item=None,
            command=None,
            action_result={"status": "not_run"},
            workflow_profile=None,
            next_recommendation={"recommendation": "stop", "reason": "no locator-backed command candidate"},
        )
        return write_iteration_report(target_id, report, project_root=project_root)

    command = cast(dict[str, object], selected["command"])
    if dry_run:
        report = _iteration_report(
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report=inspect_report,
            selected_work_item=cast(dict[str, object], selected["work_item"]),
            command=command,
            action_result={"status": "dry_run"},
            workflow_profile=None,
            next_recommendation={"recommendation": "continue", "reason": "dry-run selected a safe command action"},
        )
        return write_iteration_report(target_id, report, project_root=project_root)

    availability = _command_availability(target_id, cast(dict[str, object], command["context"]))
    commands = availability.get("commands")
    if not isinstance(commands, list) or not any(
        isinstance(entry, dict) and entry.get("command_id") == command["command_id"] for entry in commands
    ):
        report = _iteration_report(
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report=inspect_report,
            selected_work_item=cast(dict[str, object], selected["work_item"]),
            command=command,
            action_result={"status": "blocked", "availability": availability},
            workflow_profile=None,
            next_recommendation={"recommendation": "stop", "reason": "selected command is not available"},
        )
        return write_iteration_report(target_id, report, project_root=project_root)

    execution = server.route_request(
        "POST",
        f"/api/projects/{target_id}/commands/execute",
        {},
        {
            "command_id": command["command_id"],
            "context": command["context"],
            "parameters": command["parameters"],
        },
    )
    result = cast(dict[str, object], execution["data"])
    workflow_profile = result.get("workflow_profile") if isinstance(result.get("workflow_profile"), dict) else None
    report = _iteration_report(
        run_state=run_result.run_state,
        iteration_id=iteration_id,
        inspect_report=inspect_report,
        selected_work_item=cast(dict[str, object], selected["work_item"]),
        command=command,
        action_result={
            "status": "executed",
            "durable_result": result,
        },
        workflow_profile=cast(dict[str, object] | None, workflow_profile),
        next_recommendation={"recommendation": "continue", "reason": "manual command executed"},
    )
    return write_iteration_report(target_id, report, project_root=project_root)


@dataclass(frozen=True, slots=True)
class RunStartResult:
    status: str
    run_state: dict[str, object] | None
    reason: str | None = None
    latest_report: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "run_state": self.run_state,
            "reason": self.reason,
            "latest_report": self.latest_report,
        }


def start_or_resume_run(
    target_id: str,
    *,
    mode: str,
    project_root: Path = PROJECT_ROOT,
    run_id: str | None = None,
    now: datetime | None = None,
) -> RunStartResult:
    paths = _run_report_paths(target_id, project_root)
    latest = _read_latest_report(paths["latest"])
    if mode == "continue" and latest is not None:
        if _latest_iteration_is_partial(latest):
            return RunStartResult(
                status="blocked",
                run_state=None,
                reason="latest iteration is partial; start a new clean-run or reimport run explicitly",
                latest_report=latest,
            )
        latest_state = latest.get("run_state")
        if isinstance(latest_state, dict) and latest_state.get("status") not in TERMINAL_RUN_STATUSES:
            return RunStartResult(
                status="resumed",
                run_state=dict(latest_state),
                latest_report=latest,
            )
    state = _new_run_state(
        target_id,
        mode=mode,
        paths=paths,
        run_id=run_id,
        now=now,
    )
    return RunStartResult(status="started", run_state=state)


def write_iteration_report(
    target_id: str,
    report: dict[str, object],
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    paths = _run_report_paths(target_id, project_root)
    payload = dict(report)
    run_state = payload.get("run_state")
    if not isinstance(run_state, dict):
        raise ValueError("iteration report requires run_state")
    run_state = dict(run_state)
    run_state.setdefault("report_paths", paths)
    payload["run_state"] = run_state
    paths["history"].parent.mkdir(parents=True, exist_ok=True)
    with paths["history"].open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    _atomic_write_json(paths["latest"], payload)
    return payload


def _project_state_payload(target_id: str, project_root: Path) -> dict[str, object]:
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except (FileNotFoundError, ValueError, AssertionError):
        return {"available": False, "reason": "project metadata is not available", "review_items": []}
    return {
        "available": True,
        "ready": project.ready,
        "kind": project.kind,
        "review_state": project.review_state,
        "manual_action_log_path": project.manual_action_log_path,
        "manual_state": project.manual_state,
        "review_items": [dict(item) for item in project.review_items],
    }


def _new_run_state(
    target_id: str,
    *,
    mode: str,
    paths: dict[str, Path],
    run_id: str | None,
    now: datetime | None,
) -> dict[str, object]:
    current_run_id = run_id or f"run-{uuid.uuid4().hex}"
    return {
        "run_id": current_run_id,
        "target_id": target_id,
        "mode": mode,
        "started_at": (now or datetime.now(UTC)).isoformat(),
        "last_iteration_id": None,
        "status": "running",
        "report_paths": {key: str(path) for key, path in paths.items()},
        "rollback_policy": "append corrective action or use explicit clean-run/reimport; do not delete manual history",
    }


def _run_report_paths(target_id: str, project_root: Path) -> dict[str, Path]:
    target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
    agent_dir = target_dir / "agent"
    return {
        "history": agent_dir / "reversing-loop.jsonl",
        "latest": agent_dir / "latest-reversing-loop.json",
    }


def _read_latest_report(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _latest_iteration_is_partial(report: dict[str, object]) -> bool:
    iteration = report.get("iteration")
    if not isinstance(iteration, dict):
        return False
    status = iteration.get("status")
    return isinstance(status, str) and status in PARTIAL_ITERATION_STATUSES


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def _candidate_work_items(raw_items: object) -> list[dict[str, object]]:
    if not isinstance(raw_items, list | tuple):
        return []
    candidates: list[dict[str, object]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        try:
            if not review_item_is_open(cast(dict[str, object], item)):
                continue
        except TypeError:
            continue
        item_id = item.get("item_id")
        locator = _locator_from_review_item(item)
        durable_identity = item_id if isinstance(item_id, str) and item_id else None
        if durable_identity is None and locator is None:
            continue
        candidate: dict[str, object] = {
            "id": durable_identity or _locator_candidate_id(locator),
            "kind": "manual_review_item",
            "review_item_kind": item.get("kind"),
            "durable_id": durable_identity,
            "locator": locator,
            "evidence": {
                "has_xrefs": _has_xref_evidence(item),
                "message": item.get("message"),
                "confidence": item.get("review_confidence"),
            },
            "suggested_action_kinds": _suggested_action_kinds(item),
        }
        candidates.append(candidate)
    return candidates


def _locator_from_review_item(item: dict[str, object]) -> dict[str, object] | None:
    existing = item.get("locator")
    if isinstance(existing, dict):
        return dict(cast(dict[str, object], existing))
    start = item.get("start") if isinstance(item.get("start"), int) else item.get("addr")
    hunk = item.get("hunk") if isinstance(item.get("hunk"), int) else None
    if not isinstance(start, int):
        return None
    end = item.get("end") if isinstance(item.get("end"), int) else start + 1
    return {
        "section_index": hunk,
        "start_offset": start,
        "end_offset": end,
    }


def _locator_candidate_id(locator: dict[str, object] | None) -> str:
    if locator is None:
        return "candidate:unknown"
    return "locator:{section_index}:{start_offset}:{end_offset}".format(**locator)


def _has_xref_evidence(item: dict[str, object]) -> bool:
    refs = item.get("refs")
    if isinstance(refs, list) and refs:
        return True
    ref_count = item.get("ref_count")
    return isinstance(ref_count, int) and ref_count > 0


def _suggested_action_kinds(item: dict[str, object]) -> list[str]:
    raw_actions = item.get("suggested_actions")
    if not isinstance(raw_actions, list):
        return []
    actions: list[str] = []
    for action in raw_actions:
        if not isinstance(action, dict):
            continue
        raw = action.get("action")
        if isinstance(raw, str):
            actions.append(raw)
    return actions


def _manual_action_log_state(target_dir: Path) -> dict[str, object]:
    path = target_dir / "manual_actions.jsonl"
    if not path.exists():
        return {"path": str(path), "count": 0, "head_hash": None}
    text = path.read_text(encoding="utf-8")
    return {
        "path": str(path),
        "count": sum(1 for line in text.splitlines() if '"record": "manual_action"' in line or '"record":"manual_action"' in line),
        "head_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def _round_trip_state(target_dir: Path) -> dict[str, object]:
    path = target_dir / "reproduction.json"
    if not path.exists():
        return {"available": False, "path": str(path), "status": "missing"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"available": False, "path": str(path), "status": "malformed", "error": str(exc)}
    status = payload.get("status") if isinstance(payload, dict) else None
    return {"available": True, "path": str(path), "status": status}


def _verification_paths(target_dir: Path) -> list[dict[str, object]]:
    paths: list[dict[str, object]] = [
        {"kind": "semantic_reload", "available": True},
        {"kind": "projection_check", "available": True},
        {"kind": "round_trip", "available": (target_dir / "reproduction.json").exists()},
    ]
    return paths


def _select_command_action(inspect_report: dict[str, object]) -> dict[str, object] | None:
    candidates = inspect_report.get("candidate_work")
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        locator = candidate.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        command = {
            "kind": "command",
            "command_id": "comment.edit",
            "context": {"kind": "row", "locator": locator},
            "parameters": {"text": f"agent note: {candidate.get('id') or 'candidate'}"},
            "output_affecting": False,
        }
        return {"work_item": dict(candidate), "command": command}
    return None


def _is_full_listing_locator(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return all(isinstance(value.get(key), str) and value.get(key) for key in ("target_id", "projection_hash", "row_key", "kind"))


def _command_availability(target_id: str, context: dict[str, object]) -> dict[str, object]:
    payload = server.route_request(
        "GET",
        f"/api/projects/{target_id}/commands",
        _command_query_from_context(context),
    )
    data = payload.get("data")
    return dict(data) if isinstance(data, dict) else {}


def _command_query_from_context(context: dict[str, object]) -> dict[str, list[str]]:
    kind = context.get("kind")
    if kind == "row":
        return {"context": ["row"], "locator": [json.dumps(context["locator"])]}
    if kind == "review_item":
        return {"context": ["review-item"], "item_id": [str(context["item_id"])]}
    return {"context": ["target"]}


def _next_iteration_id(run_state: dict[str, object]) -> str:
    last = run_state.get("last_iteration_id")
    if isinstance(last, str) and last.isdigit():
        return f"{int(last) + 1:06d}"
    return "000001"


def _iteration_report(
    *,
    run_state: dict[str, object],
    iteration_id: str,
    inspect_report: dict[str, object],
    selected_work_item: dict[str, object] | None,
    command: dict[str, object] | None,
    action_result: dict[str, object],
    workflow_profile: dict[str, object] | None,
    next_recommendation: dict[str, object],
) -> dict[str, object]:
    updated_run_state = dict(run_state)
    updated_run_state["last_iteration_id"] = iteration_id
    return {
        "schema_version": 1,
        "run_state": updated_run_state,
        "iteration": {
            "id": iteration_id,
            "status": "complete",
            "dry_run": action_result.get("status") == "dry_run",
        },
        "target_state": inspect_report.get("target_state"),
        "selected_work_item": selected_work_item,
        "evidence": None if selected_work_item is None else selected_work_item.get("evidence"),
        "action": command,
        "durable_result": action_result.get("durable_result"),
        "action_result": action_result,
        "verification": {"status": "not_configured", "layers": []},
        "workflow_profile": workflow_profile,
        "next": next_recommendation,
    }


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
