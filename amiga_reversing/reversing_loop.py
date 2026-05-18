from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from amiga_reversing.disasm import projects, server
from amiga_reversing.disasm.binary_source import resolve_target_binary_source
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
    run_parser.add_argument(
        "--listing-backed-comment",
        action="store_true",
        help="Acquire a listing row locator in-process and execute comment.edit.",
    )
    run_parser.add_argument("--comment-text")
    run_parser.add_argument("--listing-timeout-seconds", type=float, default=10.0)

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
        if args.listing_backed_comment:
            _print_json(
                run_listing_backed_comment_iteration(
                    args.target,
                    mode=args.mode,
                    dry_run=args.dry_run,
                    comment_text=args.comment_text,
                    listing_timeout_seconds=args.listing_timeout_seconds,
                    project_root=args.project_root,
                )
            )
            return 0
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


def run_listing_backed_comment_iteration(
    target_id: str,
    *,
    mode: str = "continue",
    dry_run: bool = False,
    comment_text: str | None = None,
    listing_timeout_seconds: float = 10.0,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    run_result = start_or_resume_run(target_id, mode=mode, project_root=project_root)
    if run_result.status == "blocked":
        return run_result.to_dict()
    if run_result.run_state is None:
        raise ValueError("run state is required")

    hygiene = inspect_target_hygiene(target_id, mode="inspect", project_root=project_root)
    inspect_report = _listing_comment_inspect_report(target_id, hygiene.to_dict(), project_root=project_root)
    iteration_id = _next_iteration_id(run_result.run_state)
    if hygiene.unknown_files or not hygiene.safe_to_continue:
        verification = {
            "status": "failed",
            "layers": [
                {
                    "layer": "hygiene",
                    "status": "failed",
                    "unknown_files": list(hygiene.unknown_files),
                }
            ],
        }
        return _write_listing_comment_report(
            target_id,
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report=inspect_report,
            selected_work_item=None,
            command=None,
            action_result={"status": "blocked"},
            verification=verification,
            workflow_profile=None,
            project_root=project_root,
        )

    listing_ready = _open_and_wait_listing(target_id, timeout_seconds=listing_timeout_seconds)
    if listing_ready.get("status") != "ready":
        verification = {"status": "failed", "layers": [{**listing_ready, "layer": "listing_readiness"}]}
        return _write_listing_comment_report(
            target_id,
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report={**inspect_report, "listing_open": listing_ready},
            selected_work_item=None,
            command=None,
            action_result={"status": "blocked", "listing_open": listing_ready},
            verification=verification,
            workflow_profile=None,
            project_root=project_root,
        )

    selection = _select_listing_comment_action(target_id, comment_text=comment_text, project_root=project_root)
    inspect_report = {**inspect_report, "candidate_work": selection.get("candidates", [])}
    if selection.get("status") != "selected":
        layer = "candidate_selection" if selection.get("status") == "no_candidate" else "command_availability"
        verification = {"status": "failed", "layers": [{**selection, "layer": layer}]}
        return _write_listing_comment_report(
            target_id,
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report={**inspect_report, "listing_open": listing_ready},
            selected_work_item=None,
            command=None,
            action_result={"status": "blocked", "listing_open": listing_ready},
            verification=verification,
            workflow_profile=None,
            next_evidence={"kind": "missing_domain_judgment", "name": selection.get("message", "no evidence-backed candidate")},
            project_root=project_root,
        )

    work_item = cast(dict[str, object], selection["work_item"])
    command = cast(dict[str, object], selection["command"])
    if dry_run:
        return _write_listing_comment_report(
            target_id,
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report={**inspect_report, "listing_open": listing_ready},
            selected_work_item=work_item,
            command=command,
            action_result={"status": "dry_run", "listing_open": listing_ready},
            verification={"status": "not_run", "layers": []},
            workflow_profile=None,
            project_root=project_root,
        )

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
    verification = _verify_listing_comment_mutation(
        target_id,
        command,
        result,
        project_root=project_root,
    )
    return _write_listing_comment_report(
        target_id,
        run_state=run_result.run_state,
        iteration_id=iteration_id,
        inspect_report={**inspect_report, "listing_open": listing_ready},
        selected_work_item=work_item,
        command=command,
        action_result={
            "status": "executed",
            "listing_open": listing_ready,
            "durable_result": result,
        },
        verification=verification,
        workflow_profile=cast(dict[str, object] | None, workflow_profile),
        project_root=project_root,
    )


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


def _listing_comment_inspect_report(
    target_id: str,
    hygiene: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
    return {
        "target_id": target_id,
        "mode": "listing-backed-comment",
        "hygiene": hygiene,
        "target_state": {
            "target_dir": str(target_dir),
            "manual_action_log": _manual_action_log_state(target_dir),
            "project": _project_state_payload(target_id, project_root),
            "round_trip": _round_trip_state(target_dir),
        },
        "candidate_work": [],
        "verification_paths": _verification_paths(target_dir),
        "safe_to_mutate": not hygiene.get("unknown_files") and hygiene.get("safe_to_continue") is True,
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
            verification={"status": "not_run", "layers": []},
            workflow_profile=None,
            next_recommendation=recommend_next_step(
                inspect_report=inspect_report,
                verification={"status": "not_run", "layers": []},
                evidence={"kind": "missing_domain_judgment", "name": "no locator-backed command candidate"},
            ),
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
            verification={"status": "not_run", "layers": []},
            workflow_profile=None,
            next_recommendation=recommend_next_step(
                inspect_report=inspect_report,
                verification={"status": "not_run", "layers": []},
            ),
        )
        return write_iteration_report(target_id, report, project_root=project_root)

    if command.get("output_affecting") is True and not _round_trip_verifier_available(inspect_report):
        verification = {
            "status": "failed",
            "layers": [
                {
                    "layer": "round_trip",
                    "status": "failed",
                    "message": "output-affecting action requires an available round-trip verifier",
                }
            ],
        }
        report = _iteration_report(
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report=inspect_report,
            selected_work_item=cast(dict[str, object], selected["work_item"]),
            command=command,
            action_result={"status": "blocked"},
            verification=verification,
            workflow_profile=None,
            next_recommendation=recommend_next_step(
                inspect_report=inspect_report,
                verification=verification,
                evidence={"kind": "unavailable_oracle", "name": "round_trip"},
            ),
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
            verification={"status": "failed", "layers": [{"layer": "command_availability", "status": "failed"}]},
            workflow_profile=None,
            next_recommendation=recommend_next_step(
                inspect_report=inspect_report,
                verification={"status": "failed", "layers": [{"layer": "command_availability", "status": "failed"}]},
                evidence={"kind": "api_gap", "name": "command_availability"},
            ),
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
    verification = _verify_manual_mutation(target_id, command, result, project_root=project_root)
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
        verification=verification,
        workflow_profile=cast(dict[str, object] | None, workflow_profile),
        next_recommendation=recommend_next_step(
            inspect_report=inspect_report,
            verification=verification,
            workflow_profile=cast(dict[str, object] | None, workflow_profile),
        ),
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


def profile_summary(workflow_profile: dict[str, object] | None) -> dict[str, object]:
    if workflow_profile is None:
        return {"available": False, "workflow_id": None, "spans": []}
    spans = workflow_profile.get("spans")
    span_payloads: list[dict[str, object]] = []
    if isinstance(spans, list):
        for span in spans:
            if not isinstance(span, dict):
                continue
            name = span.get("name")
            if not isinstance(name, str) or not name:
                continue
            seconds = span.get("seconds")
            span_payloads.append(
                {
                    "name": name,
                    "seconds": seconds if isinstance(seconds, int | float) else None,
                    "module": span.get("module") if isinstance(span.get("module"), str) else None,
                }
            )
    return {
        "available": True,
        "workflow_id": workflow_profile.get("workflow_id"),
        "spans": span_payloads,
        "top_spans": sorted(
            span_payloads,
            key=lambda span: span["seconds"] if isinstance(span.get("seconds"), int | float) else -1,
            reverse=True,
        )[:5],
    }


def recommend_next_step(
    *,
    inspect_report: dict[str, object],
    verification: dict[str, object],
    workflow_profile: dict[str, object] | None = None,
    evidence: dict[str, object] | None = None,
) -> dict[str, object]:
    hygiene = inspect_report.get("hygiene")
    if isinstance(hygiene, dict) and hygiene.get("unknown_files"):
        return {"recommendation": "stop", "reason": "unknown target-local files require review"}
    evidence_kind = evidence.get("kind") if isinstance(evidence, dict) else None
    evidence_name = evidence.get("name") if isinstance(evidence, dict) else None
    if evidence_kind in {"unavailable_oracle", "missing_domain_judgment"}:
        return {"recommendation": "stop", "reason": str(evidence_name or evidence_kind), "evidence": evidence}
    if evidence_kind == "additional_verification_required":
        return {"recommendation": "verify", "reason": str(evidence_name or evidence_kind), "evidence": evidence}
    if evidence_kind in {"profile_span", "api_gap", "state_contract", "blocking_duplication"} and evidence_name:
        return {"recommendation": "refactor", "reason": str(evidence_name), "evidence": evidence}
    if verification.get("status") == "failed":
        return {"recommendation": "stop", "reason": "verification failed", "verification": verification}
    return {
        "recommendation": "continue",
        "reason": "verification passed or no mutation was executed",
        "profile_summary": profile_summary(workflow_profile),
    }


def _open_and_wait_listing(target_id: str, *, timeout_seconds: float) -> dict[str, object]:
    try:
        opened = server.route_request("POST", f"/api/projects/{target_id}/listing/open", {}, {})
        job = opened.get("data")
        if not isinstance(job, dict):
            return {"status": "failed", "message": "listing/open returned malformed job"}
        job_id = job.get("job_id")
        if not isinstance(job_id, str) or not job_id:
            return {"status": "failed", "message": "listing/open did not return job_id", "job": job}
        deadline = time.monotonic() + max(0.0, timeout_seconds)
        current = dict(job)
        while True:
            status = current.get("status")
            if status == "ready":
                return {"status": "ready", "job": current}
            if status == "failed":
                return {"status": "failed", "message": str(current.get("error") or "listing job failed"), "job": current}
            if time.monotonic() >= deadline:
                return {"status": "failed", "message": "listing readiness timed out", "job": current}
            time.sleep(0.05)
            polled = server.route_request(
                "GET",
                f"/api/projects/{target_id}/listing/status",
                {"job_id": [job_id]},
            )
            data = polled.get("data")
            current = dict(data) if isinstance(data, dict) else {"status": "failed", "error": "malformed status"}
    except Exception as exc:
        return {"status": "failed", "message": str(exc)}


def _select_listing_comment_action(
    target_id: str,
    *,
    comment_text: str | None,
    project_root: Path,
) -> dict[str, object]:
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {"start": ["0"], "count": ["80"]},
        )
    except Exception as exc:
        return {"status": "failed", "message": str(exc)}
    data = listing.get("data")
    if not isinstance(data, dict):
        return {"status": "failed", "message": "listing returned malformed payload"}
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        return {"status": "failed", "message": "listing returned no rows"}
    candidates = _listing_comment_candidates(target_id, rows, project_root=project_root)
    if not candidates:
        return {
            "status": "no_candidate",
            "message": "no evidence-backed listing comment candidate",
            "candidates": [],
        }
    checked_candidates: list[dict[str, object]] = []
    for candidate in candidates:
        if not _candidate_is_actionable(candidate):
            checked_candidates.append(candidate)
            continue
        locator = candidate.get("locator")
        availability = _command_availability(target_id, {"kind": "row", "locator": locator})
        commands = availability.get("commands")
        if not isinstance(commands, list) or not any(
            isinstance(entry, dict) and entry.get("command_id") == "comment.edit" for entry in commands
        ):
            checked = dict(candidate)
            checked["stop_reason"] = "comment.edit unavailable"
            checked_candidates.append(checked)
            continue
        checked = dict(candidate)
        checked["evidence"] = {
            **cast(dict[str, object], checked.get("evidence", {})),
            "command_availability_checked": True,
        }
        checked_candidates.append(checked)
        text = comment_text or f"agent note: {candidate.get('candidate_id') or candidate.get('id')}"
        command = {
            "kind": "command",
            "command_id": "comment.edit",
            "context": {"kind": "row", "locator": locator},
            "parameters": {"text": text},
            "output_affecting": False,
        }
        return {
            "status": "selected",
            "work_item": checked,
            "command": command,
            "availability": availability,
            "candidates": checked_candidates,
        }
    return {
        "status": "failed",
        "message": "comment.edit was unavailable for evidence-backed candidates",
        "candidates": checked_candidates,
    }


def _listing_comment_candidates(
    target_id: str,
    rows: list[object],
    *,
    project_root: Path,
) -> list[dict[str, object]]:
    entrypoint = _source_entrypoint_evidence(target_id, project_root=project_root)
    if entrypoint is None:
        return []
    candidates: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        if not _row_covers_offset(row, cast(dict[str, object], locator), entrypoint):
            continue
        row_key = locator.get("row_key")
        candidate_id = f"source-entrypoint:{row_key}"
        candidates.append(
            {
                "id": candidate_id,
                "candidate_id": candidate_id,
                "kind": "source_entrypoint_row",
                "durable_id": f"source_entrypoint:h{locator.get('section_index')}:${entrypoint:08x}",
                "locator": dict(cast(dict[str, object], locator)),
                "evidence": {
                    "source": "source_binary.json",
                    "entrypoint": entrypoint,
                    "row_key": row_key,
                    "row_kind": row.get("kind"),
                    "row_range": {
                        "section_index": locator.get("section_index"),
                        "start_offset": locator.get("start_offset"),
                        "end_offset": locator.get("end_offset"),
                    },
                    "command_availability_checked": False,
                },
                "xref_summary": [],
                "current_metadata": {
                    "comment_text": row.get("comment_text"),
                    "row_kind": row.get("kind"),
                    "text": row.get("text"),
                },
                "suggested_action_kind": "comment.edit",
                "suggested_action_kinds": ["comment.edit"],
                "default_verifier": "projected_comment_text",
                "verifier": {"kind": "projected_comment_text", "requires_semantic_reload": True},
                "confidence": "high",
                "rationale": "source descriptor entrypoint maps to this listing row",
                "actionable": True,
                "stop_reason": None,
            }
        )
    return candidates


def _source_entrypoint_evidence(target_id: str, *, project_root: Path) -> int | None:
    try:
        target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
        source = resolve_target_binary_source(target_dir, project_root=project_root)
    except (FileNotFoundError, ValueError, KeyError, AssertionError, json.JSONDecodeError):
        return None
    entrypoint = getattr(source, "analysis_entrypoint", None)
    if isinstance(entrypoint, int) and not isinstance(entrypoint, bool):
        return entrypoint
    return None


def _row_covers_offset(row: dict[str, object], locator: dict[str, object], offset: int) -> bool:
    section = locator.get("section_index")
    if section not in (0, None):
        return False
    start = locator.get("start_offset")
    end = locator.get("end_offset")
    if isinstance(start, int) and isinstance(end, int) and start <= offset < end:
        return True
    addr = row.get("addr")
    return isinstance(addr, int) and addr == offset


def _candidate_is_actionable(candidate: dict[str, object]) -> bool:
    actions = candidate.get("suggested_action_kinds")
    return (
        candidate.get("confidence") == "high"
        and candidate.get("actionable") is True
        and candidate.get("default_verifier") is not None
        and isinstance(actions, list)
        and "comment.edit" in actions
        and _is_full_listing_locator(candidate.get("locator"))
    )


def _verify_listing_comment_mutation(
    target_id: str,
    command: dict[str, object],
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_semantic_reload(target_id),
        _verify_projected_comment_text(target_id, command),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _verify_manual_log_matches_mutation(
    target_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    mutation = durable_result.get("mutation")
    expected_count = mutation.get("manual_action_log_count") if isinstance(mutation, dict) else None
    expected_head = mutation.get("manual_action_log_head_hash") if isinstance(mutation, dict) else None
    target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
    actual = _manual_action_log_state(target_dir)
    passed = actual["count"] == expected_count and actual["head_hash"] == expected_head
    return {
        "layer": "manual_action_log",
        "status": "passed" if passed else "failed",
        "expected_manual_action_count": expected_count,
        "actual_manual_action_count": actual["count"],
        "expected_head_hash": expected_head,
        "actual_head_hash": actual["head_hash"],
    }


def _verify_project_semantic_reload(target_id: str) -> dict[str, object]:
    try:
        payload = server.route_request("GET", f"/api/projects/{target_id}", {})
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    data = payload.get("data")
    project = data.get("project") if isinstance(data, dict) else None
    if isinstance(project, dict) and isinstance(project.get("manual_state"), dict):
        return {"layer": "semantic_reload", "status": "passed"}
    return {"layer": "semantic_reload", "status": "failed", "message": "manual_state was not reloaded"}


def _verify_projected_comment_text(target_id: str, command: dict[str, object]) -> dict[str, object]:
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    parameters = command.get("parameters")
    expected = parameters.get("text") if isinstance(parameters, dict) else None
    if not isinstance(locator, dict) or not isinstance(expected, str):
        return {"layer": "projection", "status": "failed", "message": "missing locator or expected comment text"}
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {"start": ["0"], "count": ["80"]},
        )
    except Exception as exc:
        return {"layer": "projection", "status": "failed", "message": str(exc)}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {"layer": "projection", "status": "failed", "message": "listing rows missing after reload"}
    for row in rows:
        if isinstance(row, dict) and row.get("row_key") == locator.get("row_key"):
            actual = row.get("comment_text")
            return {
                "layer": "projection",
                "status": "passed" if actual == expected else "failed",
                "row_key": locator.get("row_key"),
                "expected_comment_text": expected,
                "actual_comment_text": actual,
            }
    return {"layer": "projection", "status": "failed", "message": "affected locator row missing after reload"}


def _write_listing_comment_report(
    target_id: str,
    *,
    run_state: dict[str, object],
    iteration_id: str,
    inspect_report: dict[str, object],
    selected_work_item: dict[str, object] | None,
    command: dict[str, object] | None,
    action_result: dict[str, object],
    verification: dict[str, object],
    workflow_profile: dict[str, object] | None,
    project_root: Path,
    next_evidence: dict[str, object] | None = None,
) -> dict[str, object]:
    report = _iteration_report(
        run_state=run_state,
        iteration_id=iteration_id,
        inspect_report=inspect_report,
        selected_work_item=selected_work_item,
        command=command,
        action_result=action_result,
        verification=verification,
        workflow_profile=workflow_profile,
        next_recommendation=recommend_next_step(
            inspect_report=inspect_report,
            verification=verification,
            workflow_profile=workflow_profile,
            evidence=next_evidence,
        ),
    )
    return write_iteration_report(target_id, report, project_root=project_root)


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
        has_xrefs = _has_xref_evidence(item)
        actions = _suggested_action_kinds(item)
        verifier = _default_verifier_for_actions(actions)
        confidence = "high" if locator is not None and has_xrefs and verifier is not None else "low"
        candidate: dict[str, object] = {
            "id": durable_identity or _locator_candidate_id(locator),
            "candidate_id": durable_identity or _locator_candidate_id(locator),
            "kind": "manual_review_item",
            "review_item_kind": item.get("kind"),
            "durable_id": durable_identity,
            "locator": locator,
            "evidence": {
                "has_xrefs": has_xrefs,
                "message": item.get("message"),
                "confidence": item.get("review_confidence"),
            },
            "xref_summary": item.get("refs") if isinstance(item.get("refs"), list) else [],
            "current_metadata": {
                "message": item.get("message"),
                "review_state": item.get("state"),
            },
            "suggested_action_kind": actions[0] if actions else None,
            "suggested_action_kinds": actions,
            "default_verifier": verifier,
            "verifier": {"kind": verifier, "requires_semantic_reload": True} if verifier else None,
            "confidence": confidence,
            "rationale": "open manual review item with xref evidence and locator" if confidence == "high" else None,
            "actionable": confidence == "high",
            "stop_reason": None if confidence == "high" else "candidate lacks locator, xref evidence, or verifier",
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


def _default_verifier_for_actions(actions: list[str]) -> str | None:
    if "comment.edit" in actions:
        return "projection_metadata"
    if any(action in actions for action in ("create_manual_seed", "row.seed.code", "row.seed.data")):
        return "round_trip"
    return None


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


def _verify_manual_mutation(
    target_id: str,
    command: dict[str, object],
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    layers = [
        _verify_semantic_reload(target_id, durable_result, project_root=project_root),
        _verify_projection_metadata(command, durable_result),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _verify_semantic_reload(
    target_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    mutation = durable_result.get("mutation")
    expected_count = mutation.get("manual_action_log_count") if isinstance(mutation, dict) else None
    target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
    actual = _manual_action_log_state(target_dir)
    if isinstance(expected_count, int) and actual["count"] >= expected_count:
        return {
            "layer": "semantic_reload",
            "status": "passed",
            "expected_manual_action_count": expected_count,
            "actual_manual_action_count": actual["count"],
        }
    return {
        "layer": "semantic_reload",
        "status": "failed",
        "expected_manual_action_count": expected_count,
        "actual_manual_action_count": actual["count"],
    }


def _verify_projection_metadata(command: dict[str, object], durable_result: dict[str, object]) -> dict[str, object]:
    context = command.get("context")
    expected_locator = context.get("locator") if isinstance(context, dict) else None
    mutation = durable_result.get("mutation")
    affected = mutation.get("affected_locators") if isinstance(mutation, dict) else None
    if isinstance(expected_locator, dict) and isinstance(affected, list) and any(
        isinstance(locator, dict) and locator.get("row_key") == expected_locator.get("row_key") for locator in affected
    ):
        return {"layer": "projection", "status": "passed", "row_key": expected_locator.get("row_key")}
    return {
        "layer": "projection",
        "status": "failed",
        "message": "affected locator was not reported by command execution",
    }


def _round_trip_verifier_available(inspect_report: dict[str, object]) -> bool:
    paths = inspect_report.get("verification_paths")
    if not isinstance(paths, list):
        return False
    return any(isinstance(path, dict) and path.get("kind") == "round_trip" and path.get("available") is True for path in paths)


def _select_command_action(inspect_report: dict[str, object]) -> dict[str, object] | None:
    candidates = inspect_report.get("candidate_work")
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if not _candidate_is_actionable(candidate):
            continue
        locator = candidate.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        command = {
            "kind": "command",
            "command_id": "comment.edit",
            "context": {"kind": "row", "locator": locator},
            "parameters": {"text": f"agent note: {candidate.get('candidate_id') or candidate.get('id') or 'candidate'}"},
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
    verification: dict[str, object],
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
        "candidate_work": inspect_report.get("candidate_work"),
        "selected_work_item": selected_work_item,
        "evidence": None if selected_work_item is None else selected_work_item.get("evidence"),
        "action": command,
        "durable_result": action_result.get("durable_result"),
        "action_result": action_result,
        "verification": verification,
        "workflow_profile": workflow_profile,
        "profile_summary": profile_summary(workflow_profile),
        "next": next_recommendation,
    }


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
