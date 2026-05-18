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
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    resolve_target_binary_source,
)
from amiga_reversing.disasm.listing_context import listing_element_contexts
from amiga_reversing.disasm.manual_actions import review_item_is_open
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.reversing_workspace import (
    clean_run_target_workspace,
    inspect_target_hygiene,
)

TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "stopped"})
PARTIAL_ITERATION_STATUSES = frozenset({"started", "running", "partial"})
_LISTING_COMMENT_SEARCH_ROW_COUNT = 512
_LISTING_SOURCE_CANDIDATE_ROW_COUNT = 2048
_COMMAND_RANK = {
    "label.rename": 100,
    "review.seed.code": 92,
    "review.seed.data.raw": 87,
    "review.seed.data.string": 87,
    "review.seed.data.scalar_table": 87,
    "review.seed.data.pointer_table": 87,
    "row.seed.code": 90,
    "row.seed.data.raw": 85,
    "row.seed.data.byte": 85,
    "row.seed.data.word": 85,
    "row.seed.data.long": 85,
    "row.seed.data.string": 85,
    "row.seed.data.scalar_table": 85,
    "row.seed.data.pointer_table": 85,
    "data_symbol.rename": 82,
    "target.rsset_region.rename": 82,
    "target.rsset_region.add": 80,
    "target.rsset_region.edit": 80,
    "representation.choose": 75,
    "representation.hex": 75,
    "representation.binary": 75,
    "representation.character": 75,
    "target.rsset_region.remove": 66,
    "data_symbol.remove": 65,
    "comment.edit": 10,
}


def _parse_int_auto(value: str) -> int:
    return int(value, 0)


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
    run_parser.add_argument(
        "--listing-backed-label-rename",
        action="store_true",
        help="Acquire a listing label locator in-process and execute label.rename.",
    )
    run_parser.add_argument("--comment-text")
    run_parser.add_argument("--label-section", type=_parse_int_auto, default=0)
    run_parser.add_argument("--label-offset", type=_parse_int_auto)
    run_parser.add_argument("--label-name")
    run_parser.add_argument("--label-rationale")
    run_parser.add_argument("--label-evidence", action="append", default=[])
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
        if args.listing_backed_label_rename:
            _print_json(
                run_listing_backed_label_rename_iteration(
                    args.target,
                    mode=args.mode,
                    dry_run=args.dry_run,
                    section_index=args.label_section,
                    source_offset=args.label_offset,
                    new_label=args.label_name,
                    rationale=args.label_rationale,
                    evidence_lines=tuple(args.label_evidence),
                    listing_timeout_seconds=args.listing_timeout_seconds,
                    project_root=args.project_root,
                )
            )
            return 0
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


def run_listing_backed_label_rename_iteration(
    target_id: str,
    *,
    mode: str = "continue",
    dry_run: bool = False,
    section_index: int = 0,
    source_offset: int | None = None,
    new_label: str | None = None,
    rationale: str | None = None,
    evidence_lines: tuple[str, ...] = (),
    listing_timeout_seconds: float = 10.0,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    run_result = start_or_resume_run(target_id, mode=mode, project_root=project_root)
    if run_result.status == "blocked":
        return run_result.to_dict()
    if run_result.run_state is None:
        raise ValueError("run state is required")

    hygiene = inspect_target_hygiene(target_id, mode="inspect", project_root=project_root)
    inspect_report = _listing_command_inspect_report(
        target_id,
        hygiene.to_dict(),
        mode="listing-backed-label-rename",
        project_root=project_root,
    )
    iteration_id = _next_iteration_id(run_result.run_state)
    if hygiene.unknown_files or not hygiene.safe_to_continue:
        verification = {
            "status": "failed",
            "layers": [{"layer": "hygiene", "status": "failed", "unknown_files": list(hygiene.unknown_files)}],
        }
        return _write_listing_command_report(
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

    missing: list[str] = []
    if source_offset is None:
        missing.append("label_offset")
    label_name = _clean_label_name(new_label)
    if label_name is None:
        missing.append("label_name")
    if missing:
        verification = {"status": "failed", "layers": [{"layer": "parameters", "status": "failed", "missing": missing}]}
        return _write_listing_command_report(
            target_id,
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report=inspect_report,
            selected_work_item=None,
            command=None,
            action_result={"status": "blocked"},
            verification=verification,
            workflow_profile=None,
            next_evidence={"kind": "missing_domain_judgment", "name": ",".join(missing)},
            project_root=project_root,
        )
    assert source_offset is not None
    assert label_name is not None

    listing_ready = _open_and_wait_listing(target_id, timeout_seconds=listing_timeout_seconds)
    if listing_ready.get("status") != "ready":
        verification = {"status": "failed", "layers": [{**listing_ready, "layer": "listing_readiness"}]}
        return _write_listing_command_report(
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

    selection = _select_listing_label_rename_action(
        target_id,
        section_index=section_index,
        source_offset=source_offset,
        new_label=label_name,
        rationale=rationale,
        evidence_lines=evidence_lines,
    )
    inspect_report = {**inspect_report, "candidate_work": selection.get("candidates", [])}
    if selection.get("status") != "selected":
        layer = "candidate_selection" if selection.get("status") == "no_candidate" else "command_availability"
        verification = {"status": "failed", "layers": [{**selection, "layer": layer}]}
        return _write_listing_command_report(
            target_id,
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report={**inspect_report, "listing_open": listing_ready},
            selected_work_item=None,
            command=None,
            action_result={"status": "blocked", "listing_open": listing_ready},
            verification=verification,
            workflow_profile=None,
            next_evidence={"kind": "missing_domain_judgment", "name": str(selection.get("message") or "label rename candidate")},
            project_root=project_root,
        )

    work_item = cast(dict[str, object], selection["work_item"])
    command = cast(dict[str, object], selection["command"])
    if not _round_trip_verifier_available(inspect_report):
        verification = {
            "status": "failed",
            "layers": [{"layer": "round_trip", "status": "failed", "message": "label rename requires an available round-trip verifier"}],
        }
        return _write_listing_command_report(
            target_id,
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report={**inspect_report, "listing_open": listing_ready},
            selected_work_item=work_item,
            command=command,
            action_result={"status": "blocked", "listing_open": listing_ready},
            verification=verification,
            workflow_profile=None,
            next_evidence={"kind": "unavailable_oracle", "name": "round_trip"},
            project_root=project_root,
        )
    if dry_run:
        return _write_listing_command_report(
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
        {"command_id": command["command_id"], "context": command["context"], "parameters": command["parameters"]},
    )
    result = cast(dict[str, object], execution["data"])
    workflow_profile = result.get("workflow_profile") if isinstance(result.get("workflow_profile"), dict) else None
    verification = _verify_listing_label_rename_mutation(
        target_id,
        command,
        result,
        section_index=section_index,
        source_offset=source_offset,
        project_root=project_root,
    )
    return _write_listing_command_report(
        target_id,
        run_state=run_result.run_state,
        iteration_id=iteration_id,
        inspect_report={**inspect_report, "listing_open": listing_ready},
        selected_work_item=work_item,
        command=command,
        action_result={"status": "executed", "listing_open": listing_ready, "durable_result": result},
        verification=verification,
        workflow_profile=cast(dict[str, object] | None, workflow_profile),
        project_root=project_root,
    )


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

    if _comment_text_missing(command):
        verification = {
            "status": "failed",
            "layers": [
                {
                    "layer": "comment_text",
                    "status": "failed",
                    "message": "comment.edit requires explicit evidence-backed comment text",
                }
            ],
        }
        return _write_listing_comment_report(
            target_id,
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report={**inspect_report, "listing_open": listing_ready},
            selected_work_item=work_item,
            command=command,
            action_result={"status": "blocked", "listing_open": listing_ready},
            verification=verification,
            workflow_profile=None,
            next_evidence={"kind": "missing_domain_judgment", "name": "comment_text"},
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
    return _listing_command_inspect_report(
        target_id,
        hygiene,
        mode="listing-backed-comment",
        project_root=project_root,
    )


def _listing_command_inspect_report(
    target_id: str,
    hygiene: dict[str, object],
    *,
    mode: str,
    project_root: Path,
) -> dict[str, object]:
    target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
    return {
        "target_id": target_id,
        "mode": mode,
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
    if not inspect_report.get("candidate_work") and inspect_report.get("safe_to_mutate") is True:
        inspect_report = _inspect_report_with_listing_candidates(target_id, inspect_report)
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

    if _comment_text_missing(command):
        verification = {
            "status": "failed",
            "layers": [
                {
                    "layer": "comment_text",
                    "status": "failed",
                    "message": "comment.edit requires explicit evidence-backed comment text",
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
                evidence={"kind": "missing_domain_judgment", "name": "comment_text"},
            ),
        )
        return write_iteration_report(target_id, report, project_root=project_root)

    if _command_requires_round_trip(command) and not _round_trip_verifier_available(inspect_report):
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
        availability_layer = {
            "layer": "command_availability",
            "status": "failed",
            "message": "selected source-converging command is unavailable in the command catalog",
            "command_id": command.get("command_id"),
            "context_kind": cast(dict[str, object], command.get("context")).get("kind")
            if isinstance(command.get("context"), dict)
            else None,
        }
        verification = {"status": "failed", "layers": [availability_layer]}
        report = _iteration_report(
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report=inspect_report,
            selected_work_item=cast(dict[str, object], selected["work_item"]),
            command=command,
            action_result={"status": "blocked", "availability": availability},
            verification=verification,
            workflow_profile=None,
            next_recommendation=recommend_next_step(
                inspect_report=inspect_report,
                verification=verification,
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


def _inspect_report_with_listing_candidates(
    target_id: str,
    inspect_report: dict[str, object],
) -> dict[str, object]:
    listing_ready = _open_and_wait_listing(target_id, timeout_seconds=10.0)
    if listing_ready.get("status") != "ready":
        return {**inspect_report, "listing_open": listing_ready}
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {"start": ["0"], "count": [str(_LISTING_SOURCE_CANDIDATE_ROW_COUNT)]},
        )
    except Exception as exc:
        return {**inspect_report, "listing_open": {"status": "failed", "message": str(exc)}}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    candidates = _listing_representation_candidates(
        rows if isinstance(rows, list) else [],
        existing_representations=_existing_representation_keys(inspect_report),
    )
    try:
        navigation = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing/navigation",
            {},
        )
    except Exception:
        navigation = {}
    navigation_data = navigation.get("data") if isinstance(navigation, dict) else None
    candidates.extend(
        _listing_rsset_region_candidates(
            navigation_data if isinstance(navigation_data, dict) else {},
            existing_regions=_existing_rsset_region_map(inspect_report),
        )
    )
    return {**inspect_report, "listing_open": listing_ready, "candidate_work": candidates}


def _listing_representation_candidates(
    rows: list[object],
    *,
    existing_representations: set[tuple[int, int, int | None, int | None, str]] | None = None,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    existing = existing_representations or set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        text = row.get("text")
        opcode = row.get("opcode_or_directive")
        if not isinstance(opcode, str) or not opcode.endswith(".b"):
            continue
        element_row = dict(row)
        if not isinstance(element_row.get("stable_key"), str) and isinstance(element_row.get("row_key"), str):
            element_row["stable_key"] = element_row["row_key"]
        for context in listing_element_contexts(element_row):
            if context.get("element_kind") != "immediate":
                continue
            value = context.get("value")
            width_bits = context.get("width_bits")
            if not isinstance(value, int) or not isinstance(width_bits, int):
                continue
            if width_bits != 8 or not _printable_character_representation_value(value):
                continue
            char = chr(value)
            if isinstance(text, str) and f"#'{char}'" in text:
                continue
            element_id = context.get("element_id")
            if not isinstance(element_id, str) or not element_id:
                continue
            row_key = cast(dict[str, object], locator).get("row_key")
            operand_index = context.get("operand_index")
            hunk = context.get("hunk")
            addr = context.get("addr")
            end = context.get("end_offset")
            if (
                isinstance(hunk, int)
                and isinstance(addr, int)
                and (hunk, addr, end if isinstance(end, int) else None, operand_index if isinstance(operand_index, int) else None, "character")
                in existing
            ):
                continue
            candidate_id = f"representation:{row_key}:{operand_index}:{value}:character"
            candidates.append(
                {
                    "id": candidate_id,
                    "candidate_id": candidate_id,
                    "kind": "literal_representation",
                    "durable_id": f"source_immediate:{row_key}:{operand_index}:{value}",
                    "locator": dict(cast(dict[str, object], locator)),
                    "element_id": element_id,
                    "element_kind": "immediate",
                    "operand_index": operand_index,
                    "value": value,
                    "width_bits": width_bits,
                    "width_bytes": context.get("width_bytes"),
                    "evidence": {
                        "source": "listing",
                        "evidence_kind": "byte_printable_immediate",
                        "opcode": opcode,
                        "text": text,
                        "value": value,
                        "character": char,
                    },
                    "current_metadata": {"representation": "decimal"},
                    "expected_rendered_source_improvement": f"render byte immediate {value} as #'{char}'",
                    "suggested_action_kind": "representation.character",
                    "suggested_action_kinds": ["representation.character"],
                    "default_verifier": "projected_representation_text",
                    "verifier": {"kind": "projected_representation_text", "requires_semantic_reload": True},
                    "confidence": "high",
                    "rationale": "byte instruction uses a printable immediate value",
                    "actionable": True,
                    "stop_reason": None,
                }
            )
    return candidates


def _existing_representation_keys(inspect_report: dict[str, object]) -> set[tuple[int, int, int | None, int | None, str]]:
    target_state = inspect_report.get("target_state")
    project = target_state.get("project") if isinstance(target_state, dict) else None
    manual_state = project.get("manual_state") if isinstance(project, dict) else None
    representations = manual_state.get("representations") if isinstance(manual_state, dict) else None
    keys: set[tuple[int, int, int | None, int | None, str]] = set()
    if not isinstance(representations, list):
        return keys
    for representation in representations:
        if not isinstance(representation, dict):
            continue
        hunk = representation.get("hunk")
        addr = representation.get("addr")
        style = representation.get("style")
        if not isinstance(hunk, int) or not isinstance(addr, int) or not isinstance(style, str):
            continue
        end = representation.get("end")
        operand_index = representation.get("operand_index")
        keys.add(
            (
                hunk,
                addr,
                end if isinstance(end, int) else None,
                operand_index if isinstance(operand_index, int) else None,
                style,
            )
        )
    return keys


def _printable_character_representation_value(value: int) -> bool:
    return 32 <= value <= 126 and value not in {ord("'"), ord("\\")}


def _listing_rsset_region_candidates(
    navigation_payload: dict[str, object],
    *,
    existing_regions: dict[tuple[str, str, int], dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    groups = navigation_payload.get("groups")
    suggestions = groups.get("app-slot-suggestions") if isinstance(groups, dict) else None
    if not isinstance(suggestions, list):
        return []
    existing = existing_regions or {}
    candidates: list[dict[str, object]] = []
    for suggestion in suggestions:
        if not isinstance(suggestion, dict) or suggestion.get("action") != "add_target_metadata":
            continue
        metadata = suggestion.get("metadata")
        if not isinstance(metadata, dict):
            continue
        parameters = _rsset_region_parameters_from_metadata(metadata)
        offset = parameters.get("offset")
        symbol = parameters.get("symbol")
        if not isinstance(offset, int) or not isinstance(symbol, str):
            continue
        key = _rsset_region_key(parameters)
        current = existing.get(key, {})
        action_kind = "target.rsset_region.edit" if current else "target.rsset_region.add"
        layout_name, base_symbol, _ = key
        candidate_id = f"rsset-suggestion:{layout_name}:{base_symbol}:{offset:04X}:{symbol}"
        candidates.append(
            {
                "id": candidate_id,
                "candidate_id": candidate_id,
                "kind": "rsset_layout_region",
                "durable_id": f"rsset_region:{layout_name}:{base_symbol}:{offset:04X}",
                "evidence": {
                    "source": "app_slot_analysis",
                    "navigation_group": "app-slot-suggestions",
                    "summary": suggestion.get("summary"),
                    "confidence": suggestion.get("confidence"),
                    "stable_key": suggestion.get("stable_key"),
                    "row_index": suggestion.get("row_index"),
                },
                "current_metadata": dict(current),
                "expected_rendered_source_improvement": f"add RSSET region field {symbol} at app+0x{offset:04X}",
                "suggested_action_kind": action_kind,
                "suggested_action_kinds": [action_kind],
                "parameters": parameters,
                "default_verifier": "round_trip",
                "verifier": {"kind": "round_trip", "requires_semantic_reload": True},
                "confidence": "high" if suggestion.get("confidence") in {"high", "tool-inferred"} else "medium",
                "rationale": "app-slot analysis suggested durable RSSET layout metadata",
                "actionable": True,
                "stop_reason": None,
            }
        )
    return candidates


def _rsset_region_parameters_from_metadata(metadata: dict[str, object]) -> dict[str, object]:
    parameters: dict[str, object] = {}
    for field_name in ("offset", "size"):
        value = metadata.get(field_name)
        if isinstance(value, int) and not isinstance(value, bool):
            parameters[field_name] = value
    for field_name in (
        "symbol",
        "layout_name",
        "base_symbol",
        "sizeof_symbol",
        "struct_name",
        "pointer_struct",
        "storage_kind",
        "semantic_type",
        "parser_role",
        "parser_routine",
    ):
        value = metadata.get(field_name)
        if isinstance(value, str) and value.strip():
            parameters[field_name] = value.strip()
    parse_order = metadata.get("parse_order")
    if isinstance(parse_order, int) and not isinstance(parse_order, bool):
        parameters["parse_order"] = parse_order
    return parameters


def _rsset_region_key(region: dict[str, object]) -> tuple[str, str, int]:
    offset = region.get("offset")
    return (
        str(region.get("layout_name") or "app"),
        str(region.get("base_symbol") or "__amiga_app_base__"),
        offset if isinstance(offset, int) and not isinstance(offset, bool) else -1,
    )


def _existing_rsset_region_map(inspect_report: dict[str, object]) -> dict[tuple[str, str, int], dict[str, object]]:
    target_state = inspect_report.get("target_state")
    project = target_state.get("project") if isinstance(target_state, dict) else None
    manual_state = project.get("manual_state") if isinstance(project, dict) else None
    regions = manual_state.get("rsset_layout_regions") if isinstance(manual_state, dict) else None
    result: dict[tuple[str, str, int], dict[str, object]] = {}
    if not isinstance(regions, list | tuple):
        return result
    for region in regions:
        if not isinstance(region, dict):
            continue
        key = _rsset_region_key(region)
        if key[2] >= 0:
            result[key] = dict(region)
    return result


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
            {"start": ["0"], "count": [str(_LISTING_COMMENT_SEARCH_ROW_COUNT)]},
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
        text = _clean_comment_text(comment_text) or _comment_text_from_candidate(checked)
        command = {
            "kind": "command",
            "command_id": "comment.edit",
            "context": {"kind": "row", "locator": locator},
            "parameters": {"text": text} if text is not None else {},
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


def _select_listing_label_rename_action(
    target_id: str,
    *,
    section_index: int,
    source_offset: int,
    new_label: str,
    rationale: str | None,
    evidence_lines: tuple[str, ...],
) -> dict[str, object]:
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {
                "section_index": [str(section_index)],
                "source_offset": [str(source_offset)],
                "before": ["16"],
                "after": ["48"],
            },
        )
    except Exception as exc:
        return {"status": "failed", "message": str(exc), "candidates": []}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        return {"status": "no_candidate", "message": "listing returned no rows", "candidates": []}
    candidates = _listing_label_rename_candidates(
        target_id,
        rows,
        section_index=section_index,
        source_offset=source_offset,
        new_label=new_label,
        rationale=rationale,
        evidence_lines=evidence_lines,
    )
    if not candidates:
        return {"status": "no_candidate", "message": "no label row at requested source location", "candidates": []}
    checked_candidates: list[dict[str, object]] = []
    for candidate in candidates:
        if candidate.get("actionable") is not True:
            checked_candidates.append(candidate)
            continue
        locator = candidate.get("locator")
        element_id = candidate.get("element_id")
        context = {"kind": "element", "locator": locator, "element_id": element_id}
        availability = _command_availability(target_id, context)
        commands = availability.get("commands")
        if not isinstance(commands, list) or not any(
            isinstance(entry, dict) and entry.get("command_id") == "label.rename" for entry in commands
        ):
            checked = dict(candidate)
            checked["stop_reason"] = "label.rename unavailable"
            checked_candidates.append(checked)
            continue
        checked = dict(candidate)
        checked["evidence"] = {
            **cast(dict[str, object], checked.get("evidence", {})),
            "command_availability_checked": True,
        }
        checked_candidates.append(checked)
        command = {
            "kind": "command",
            "command_id": "label.rename",
            "context": context,
            "parameters": {"name": new_label},
            "output_affecting": True,
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
        "message": "label.rename was unavailable for label candidates",
        "candidates": checked_candidates,
    }


def _listing_label_rename_candidates(
    target_id: str,
    rows: list[object],
    *,
    section_index: int,
    source_offset: int,
    new_label: str,
    rationale: str | None,
    evidence_lines: tuple[str, ...],
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        locator_payload = cast(dict[str, object], locator)
        if row.get("kind") != "label" or not _row_covers_source_location(row, locator_payload, section_index, source_offset):
            continue
        current_label = row.get("label")
        if not isinstance(current_label, str) or not current_label:
            continue
        row_key = locator_payload.get("row_key")
        element_id = f"{row_key}:label:{current_label}"
        already_named = current_label == new_label
        candidate_id = f"label-rename:{row_key}:{new_label}"
        candidates.append(
            {
                "id": candidate_id,
                "candidate_id": candidate_id,
                "kind": "listing_label_rename",
                "durable_id": f"source_label:h{section_index}:${source_offset:08x}",
                "locator": dict(locator_payload),
                "element_id": element_id,
                "evidence": {
                    "source": "listing",
                    "evidence_kind": "operator_supplied_label_semantics",
                    "section_index": section_index,
                    "source_offset": source_offset,
                    "row_key": row_key,
                    "current_label": current_label,
                    "new_label": new_label,
                    "rationale": _clean_comment_text(rationale),
                    "evidence_lines": list(evidence_lines),
                    "command_availability_checked": False,
                },
                "xref_summary": list(evidence_lines),
                "current_metadata": {
                    "label": current_label,
                    "row_kind": row.get("kind"),
                    "text": row.get("text"),
                },
                "suggested_action_kind": "label.rename",
                "suggested_action_kinds": ["label.rename"],
                "default_verifier": "projected_label_name",
                "verifier": {"kind": "projected_label_name", "requires_semantic_reload": True},
                "confidence": "high" if not already_named else "low",
                "rationale": _clean_comment_text(rationale),
                "actionable": not already_named,
                "stop_reason": "label already has requested name" if already_named else None,
            }
        )
    return candidates


def _listing_comment_candidates(
    target_id: str,
    rows: list[object],
    *,
    project_root: Path,
) -> list[dict[str, object]]:
    entrypoint = _source_entrypoint_evidence(target_id, project_root=project_root)
    if entrypoint is None:
        return []
    section_index = entrypoint["section_index"]
    offset = entrypoint["offset"]
    assert isinstance(section_index, int)
    assert isinstance(offset, int)
    candidates: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        if not _row_covers_source_location(row, cast(dict[str, object], locator), section_index, offset):
            continue
        row_key = locator.get("row_key")
        candidate_id = f"source-entrypoint:{row_key}"
        candidate = {
            "id": candidate_id,
            "candidate_id": candidate_id,
            "kind": "source_entrypoint_row",
            "durable_id": f"source_entrypoint:h{section_index}:${offset:08x}",
            "locator": dict(cast(dict[str, object], locator)),
            "evidence": {
                "source": "source_binary.json",
                "source_kind": entrypoint["source_kind"],
                "evidence_kind": entrypoint["evidence_kind"],
                "entrypoint": offset,
                "section_index": section_index,
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
            "rationale": entrypoint["rationale"],
            "actionable": True,
            "stop_reason": None,
        }
        suggested_comment_text = entrypoint.get("suggested_comment_text")
        if isinstance(suggested_comment_text, str) and suggested_comment_text:
            candidate["suggested_comment_text"] = suggested_comment_text
        candidates.append(candidate)
    return candidates


def _source_entrypoint_evidence(target_id: str, *, project_root: Path) -> dict[str, object] | None:
    try:
        target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
        source = resolve_target_binary_source(target_dir, project_root=project_root)
    except (FileNotFoundError, ValueError, KeyError, AssertionError, json.JSONDecodeError):
        return None
    entrypoint = getattr(source, "analysis_entrypoint", None)
    if isinstance(entrypoint, int) and not isinstance(entrypoint, bool):
        return {
            "source_kind": str(getattr(source, "kind", "")),
            "evidence_kind": "source_descriptor_entrypoint",
            "section_index": 0,
            "offset": entrypoint,
            "rationale": "source descriptor entrypoint maps to this listing row",
        }
    if getattr(source, "kind", None) is BinarySourceKind.HUNK_FILE:
        return {
            "source_kind": BinarySourceKind.HUNK_FILE.value,
            "evidence_kind": "hunk_load_entrypoint",
            "section_index": 0,
            "offset": 0,
            "rationale": "hunk load file starts execution at section 0 offset 0",
            "suggested_comment_text": "Hunk file entrypoint.",
        }
    return None


def _row_covers_source_location(
    row: dict[str, object],
    locator: dict[str, object],
    section_index: int,
    offset: int,
) -> bool:
    section = locator.get("section_index")
    if section != section_index:
        return False
    start = locator.get("start_offset")
    end = locator.get("end_offset")
    if isinstance(start, int) and isinstance(end, int) and (start <= offset < end or start == offset == end):
        return True
    addr = row.get("addr")
    return isinstance(addr, int) and addr == offset


def _candidate_is_actionable(candidate: dict[str, object]) -> bool:
    options = _candidate_command_options(candidate)
    return bool(
        candidate.get("confidence") == "high"
        and candidate.get("actionable") is True
        and _candidate_verifier(candidate, options[0] if options else None) is not None
        and options
        and _command_context_complete(options[0])
        and not _candidate_already_satisfied(candidate, options[0])
    )


def _clean_comment_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _clean_label_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _comment_text_missing(command: dict[str, object]) -> bool:
    if command.get("command_id") != "comment.edit":
        return False
    parameters = command.get("parameters")
    text = parameters.get("text") if isinstance(parameters, dict) else None
    return _clean_comment_text(text) is None


def _comment_text_from_candidate(candidate: dict[str, object]) -> str | None:
    return _clean_comment_text(candidate.get("comment_text")) or _clean_comment_text(candidate.get("suggested_comment_text"))


def _comment_parameters_from_candidate(candidate: dict[str, object]) -> dict[str, object]:
    text = _comment_text_from_candidate(candidate)
    return {"text": text} if text is not None else {}


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


def _verify_listing_label_rename_mutation(
    target_id: str,
    command: dict[str, object],
    durable_result: dict[str, object],
    *,
    section_index: int,
    source_offset: int,
    project_root: Path,
) -> dict[str, object]:
    _open_and_wait_listing(target_id, timeout_seconds=10.0)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_semantic_label(target_id, command, project_root=project_root),
        _verify_projected_label_name(target_id, command, section_index=section_index, source_offset=source_offset),
        _verify_round_trip_exact(target_id, project_root=project_root),
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
            {"start": ["0"], "count": [str(_LISTING_COMMENT_SEARCH_ROW_COUNT)]},
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


def _verify_project_semantic_label(
    target_id: str,
    command: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    parameters = command.get("parameters")
    expected = parameters.get("name") if isinstance(parameters, dict) else None
    if not isinstance(expected, str):
        return {"layer": "semantic_reload", "status": "failed", "message": "missing expected label name"}
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    labels = manual_state.get("labels") if isinstance(manual_state, dict) else None
    if not isinstance(labels, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual labels were not reloaded"}
    matches = [label for label in labels if isinstance(label, dict) and label.get("name") == expected]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_label_name": expected,
        "matching_labels": matches,
    }


def _verify_projected_label_name(
    target_id: str,
    command: dict[str, object],
    *,
    section_index: int,
    source_offset: int,
) -> dict[str, object]:
    parameters = command.get("parameters")
    expected = parameters.get("name") if isinstance(parameters, dict) else None
    if not isinstance(expected, str):
        return {"layer": "projection", "status": "failed", "message": "missing expected label name"}
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {
                "section_index": [str(section_index)],
                "source_offset": [str(source_offset)],
                "before": ["8"],
                "after": ["16"],
            },
        )
    except Exception as exc:
        return {"layer": "projection", "status": "failed", "message": str(exc)}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {"layer": "projection", "status": "failed", "message": "listing rows missing after reload"}
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        if not isinstance(locator, dict):
            continue
        if row.get("kind") == "label" and _row_covers_source_location(row, locator, section_index, source_offset):
            actual = row.get("label")
            return {
                "layer": "projection",
                "status": "passed" if actual == expected else "failed",
                "expected_label_name": expected,
                "actual_label_name": actual,
                "row_key": row.get("row_key"),
            }
    return {"layer": "projection", "status": "failed", "message": "label row missing after reload"}


def _verify_round_trip_exact(target_id: str, *, project_root: Path) -> dict[str, object]:
    target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
    round_trip = _round_trip_state(target_dir)
    return {
        "layer": "round_trip",
        "status": "passed" if round_trip.get("status") == "exact" else "failed",
        "round_trip": round_trip,
    }


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
    return _write_listing_command_report(
        target_id,
        run_state=run_state,
        iteration_id=iteration_id,
        inspect_report=inspect_report,
        selected_work_item=selected_work_item,
        command=command,
        action_result=action_result,
        verification=verification,
        workflow_profile=workflow_profile,
        project_root=project_root,
        next_evidence=next_evidence,
    )


def _write_listing_command_report(
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
        suggested_comment_text = _clean_comment_text(item.get("suggested_comment_text"))
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
        if suggested_comment_text is not None:
            candidate["suggested_comment_text"] = suggested_comment_text
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
    if any(action.startswith("representation.") for action in actions):
        return "projected_representation_text"
    if "label.rename" in actions:
        return "projected_label_name"
    if "comment.edit" in actions:
        return "projection_metadata"
    if any(action.startswith("data_symbol.") for action in actions):
        return "round_trip"
    if any(action.startswith("target.rsset_region.") for action in actions):
        return "round_trip"
    if any(action == "create_manual_seed" or action.startswith(("row.seed.", "review.seed.")) for action in actions):
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
    command_id = command.get("command_id")
    if isinstance(command_id, str) and command_id.startswith("representation."):
        return _verify_representation_mutation(target_id, command, durable_result, project_root=project_root)
    layers = [
        _verify_semantic_reload(target_id, durable_result, project_root=project_root),
        _verify_projection_metadata(command, durable_result),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _verify_representation_mutation(
    target_id: str,
    command: dict[str, object],
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    representation = _representation_from_durable_result(durable_result)
    _open_and_wait_listing(target_id, timeout_seconds=10.0)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_semantic_representation(target_id, representation),
        _verify_projected_representation_text(target_id, command, representation),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _representation_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    if isinstance(action, dict):
        representation = action.get("representation")
        if isinstance(representation, dict):
            return cast(dict[str, object], representation)
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            if not isinstance(raw_action, dict):
                continue
            representation = raw_action.get("representation")
            if isinstance(representation, dict):
                return cast(dict[str, object], representation)
    return None


def _verify_project_semantic_representation(
    target_id: str,
    expected: dict[str, object] | None,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing durable representation payload"}
    try:
        payload = server.route_request("GET", f"/api/projects/{target_id}", {})
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    data = payload.get("data")
    project = data.get("project") if isinstance(data, dict) else None
    manual_state = project.get("manual_state") if isinstance(project, dict) else None
    representations = manual_state.get("representations") if isinstance(manual_state, dict) else None
    if not isinstance(representations, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual representations were not reloaded"}
    matches = [
        representation
        for representation in representations
        if isinstance(representation, dict) and _representation_matches(representation, expected)
    ]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_representation": expected,
        "matching_representations": matches,
    }


def _representation_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    for key in ("style", "element_kind", "hunk", "addr", "end", "operand_index"):
        if key in expected and actual.get(key) != expected.get(key):
            return False
    return True


def _verify_projected_representation_text(
    target_id: str,
    command: dict[str, object],
    representation: dict[str, object] | None,
) -> dict[str, object]:
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    if not isinstance(locator, dict) or representation is None:
        return {"layer": "projection", "status": "failed", "message": "missing locator or representation payload"}
    expected_tokens = _expected_representation_tokens(command, representation)
    if not expected_tokens:
        return {"layer": "projection", "status": "failed", "message": "missing expected representation token"}
    section_index = locator.get("section_index")
    source_offset = locator.get("start_offset")
    if not isinstance(section_index, int) or not isinstance(source_offset, int):
        return {"layer": "projection", "status": "failed", "message": "locator lacks section/source offset"}
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {
                "section_index": [str(section_index)],
                "source_offset": [str(source_offset)],
                "before": ["2"],
                "after": ["8"],
            },
        )
    except Exception as exc:
        return {"layer": "projection", "status": "failed", "message": str(exc)}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {"layer": "projection", "status": "failed", "message": "listing rows missing after reload"}
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_locator = row.get("locator")
        same_row_key = row.get("row_key") == locator.get("row_key")
        same_location = isinstance(row_locator, dict) and _row_covers_source_location(
            row, row_locator, section_index, source_offset
        )
        if not same_row_key and not same_location:
            continue
        rendered_text = " ".join(str(row.get(key) or "") for key in ("text", "operand_text", "source_text"))
        matched = [token for token in expected_tokens if token in rendered_text]
        return {
            "layer": "projection",
            "status": "passed" if matched else "failed",
            "expected_tokens": expected_tokens,
            "matched_tokens": matched,
            "rendered_text": rendered_text,
            "row_key": row.get("row_key"),
        }
    return {"layer": "projection", "status": "failed", "message": "affected locator row missing after reload"}


def _expected_representation_tokens(command: dict[str, object], representation: dict[str, object]) -> list[str]:
    context = command.get("context")
    value = context.get("value") if isinstance(context, dict) else None
    if not isinstance(value, int):
        value = representation.get("value")
    if not isinstance(value, int):
        return []
    width_bits = context.get("width_bits") if isinstance(context, dict) else None
    width_bytes = context.get("width_bytes") if isinstance(context, dict) else None
    if not isinstance(width_bits, int) and isinstance(width_bytes, int):
        width_bits = width_bytes * 8
    style = representation.get("style")
    element_kind = representation.get("element_kind")
    prefix = "#" if element_kind == "immediate" else ""
    masked = _mask_representation_value(value, width_bits if isinstance(width_bits, int) else None)
    if style == "binary":
        digits = f"{masked:b}"
        if isinstance(width_bits, int) and width_bits > 0:
            digits = digits.zfill(width_bits)
        return [f"{prefix}%{digits}"]
    if style == "character" and 32 <= masked <= 126 and masked not in {ord("'"), ord("\\")}:
        return [f"{prefix}'{chr(masked)}'"]
    if style in {"hex", "character"}:
        return [f"{prefix}${masked:X}"]
    return []


def _mask_representation_value(value: int, width_bits: int | None) -> int:
    if width_bits == 8:
        return value & 0xFF
    if width_bits == 16:
        return value & 0xFFFF
    if width_bits == 32:
        return value & 0xFFFFFFFF
    return value


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


def _command_requires_round_trip(command: dict[str, object]) -> bool:
    command_id = command.get("command_id")
    return command.get("output_affecting") is True or (
        isinstance(command_id, str) and command_id.startswith("representation.")
    )


def _candidate_command_options(candidate: dict[str, object]) -> list[dict[str, object]]:
    embedded = candidate.get("command")
    if isinstance(embedded, dict):
        normalized = _normalize_candidate_command(cast(dict[str, object], embedded))
        return [normalized] if normalized is not None else []
    actions = candidate.get("suggested_action_kinds")
    if not isinstance(actions, list):
        return []
    options: list[dict[str, object]] = []
    for raw_action in actions:
        if not isinstance(raw_action, str):
            continue
        for action in _planner_command_ids_for_action(candidate, raw_action):
            command = _command_from_candidate_action(candidate, action)
            if command is not None:
                options.append(command)
    return sorted(options, key=lambda command: _command_rank(str(command.get("command_id") or "")), reverse=True)


def _planner_command_ids_for_action(candidate: dict[str, object], action: str) -> list[str]:
    if action != "create_manual_seed":
        return [action]
    review_kind = candidate.get("review_item_kind")
    if review_kind == "orphan_code_candidate":
        return ["review.seed.code"]
    if review_kind == "unreconciled_data_range":
        return ["review.seed.data.raw"]
    if review_kind == "suspicious_instruction_decode":
        return ["review.seed.data.raw"]
    return []


def _normalize_candidate_command(command: dict[str, object]) -> dict[str, object] | None:
    command_id = command.get("command_id")
    context = command.get("context")
    if not isinstance(command_id, str) or command_id not in _COMMAND_RANK or not isinstance(context, dict):
        return None
    parameters = command.get("parameters")
    normalized = dict(command)
    normalized["kind"] = "command"
    normalized["parameters"] = dict(parameters) if isinstance(parameters, dict) else {}
    normalized["output_affecting"] = command.get("output_affecting") is True or _command_id_affects_output(command_id)
    return normalized


def _command_from_candidate_action(candidate: dict[str, object], action: str) -> dict[str, object] | None:
    if action not in _COMMAND_RANK:
        return None
    locator = candidate.get("locator")
    parameters = candidate.get("parameters")
    parameter_payload = dict(parameters) if isinstance(parameters, dict) else {}
    if action.startswith("review.seed."):
        item_id = candidate.get("durable_id") or candidate.get("candidate_id") or candidate.get("id")
        return {
            "kind": "command",
            "command_id": action,
            "context": {
                "kind": "review_item",
                "item_id": item_id,
                "review_item_kind": candidate.get("review_item_kind"),
            },
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action == "comment.edit":
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "row", "locator": locator},
            "parameters": parameter_payload or _comment_parameters_from_candidate(candidate),
            "output_affecting": False,
        }
    if action.startswith("row.seed."):
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "row", "locator": locator},
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action == "label.rename":
        element_id = candidate.get("element_id")
        name = parameter_payload.get("name") or candidate.get("new_label")
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "element", "locator": locator, "element_id": element_id},
            "parameters": {"name": name} if isinstance(name, str) and name else parameter_payload,
            "output_affecting": True,
        }
    if action == "data_symbol.rename":
        name = parameter_payload.get("name") or candidate.get("new_name") or candidate.get("data_symbol_name")
        if not isinstance(name, str) or not name:
            return None
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "row", "locator": locator},
            "parameters": {"name": name},
            "output_affecting": True,
        }
    if action == "data_symbol.remove":
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "row", "locator": locator},
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action in {
        "target.rsset_region.add",
        "target.rsset_region.edit",
        "target.rsset_region.rename",
        "target.rsset_region.remove",
    }:
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "target"},
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action.startswith("representation."):
        context = _representation_context_from_candidate(candidate)
        representation = parameter_payload.get("representation") or action.removeprefix("representation.")
        if representation == "choose":
            return None
        return {
            "kind": "command",
            "command_id": action,
            "context": context,
            "parameters": {"representation": representation},
            "output_affecting": True,
        }
    return None


def _representation_context_from_candidate(candidate: dict[str, object]) -> dict[str, object]:
    context = candidate.get("context")
    if isinstance(context, dict):
        payload = dict(context)
    else:
        payload = {
            "kind": "element",
            "locator": candidate.get("locator"),
            "element_id": candidate.get("element_id"),
        }
    for key in ("element_kind", "operand_index", "value", "width_bits", "width_bytes"):
        if key in candidate and key not in payload:
            payload[key] = candidate[key]
    payload["kind"] = "element"
    return payload


def _candidate_skip_reason(candidate: dict[str, object], command: dict[str, object] | None) -> str | None:
    if candidate.get("confidence") != "high":
        return "candidate confidence is not high"
    if candidate.get("actionable") is not True:
        existing = candidate.get("stop_reason")
        return str(existing) if isinstance(existing, str) and existing else "candidate is not actionable"
    if command is None:
        return "no supported source-converging command"
    if _candidate_verifier(candidate, command) is None:
        return "missing action-specific verifier"
    if not _command_context_complete(command):
        return "missing durable command context"
    if _candidate_already_satisfied(candidate, command):
        return "candidate already satisfied in projected semantic state"
    return None


def _candidate_verifier(candidate: dict[str, object], command: dict[str, object] | None) -> str | None:
    verifier = candidate.get("default_verifier")
    if isinstance(verifier, str) and verifier:
        return verifier
    if command is None:
        return None
    command_id = command.get("command_id")
    if isinstance(command_id, str):
        return _default_verifier_for_actions([command_id])
    return None


def _command_context_complete(command: dict[str, object]) -> bool:
    context = command.get("context")
    if not isinstance(context, dict):
        return False
    kind = context.get("kind")
    if kind == "row":
        return _is_full_listing_locator(context.get("locator"))
    if kind == "element":
        return _is_full_listing_locator(context.get("locator")) and isinstance(context.get("element_id"), str)
    if kind == "review_item":
        return isinstance(context.get("item_id"), str) and bool(context.get("item_id"))
    return kind == "target"


def _candidate_already_satisfied(candidate: dict[str, object], command: dict[str, object]) -> bool:
    if candidate.get("satisfied") is True:
        return True
    current = candidate.get("current_metadata")
    if not isinstance(current, dict):
        return False
    parameters = command.get("parameters")
    command_id = command.get("command_id")
    if not isinstance(parameters, dict) or not isinstance(command_id, str):
        return False
    if command_id == "comment.edit":
        text = parameters.get("text")
        return isinstance(text, str) and current.get("comment_text") == text
    if command_id == "label.rename":
        name = parameters.get("name")
        return isinstance(name, str) and current.get("label") == name
    if command_id == "data_symbol.rename":
        name = parameters.get("name")
        return isinstance(name, str) and current.get("name") == name
    if command_id == "data_symbol.remove":
        return current.get("suppressed") is True
    if command_id in {"target.rsset_region.add", "target.rsset_region.edit", "target.rsset_region.rename"}:
        return all(current.get(key) == value for key, value in parameters.items())
    if command_id == "target.rsset_region.remove":
        return current.get("removed") is True
    if command_id.startswith("representation."):
        style = parameters.get("representation")
        return isinstance(style, str) and current.get("representation") == style
    return False


def _candidate_score(candidate: dict[str, object], command: dict[str, object] | None) -> int:
    command_id = command.get("command_id") if isinstance(command, dict) else None
    score = _command_rank(str(command_id or ""))
    if candidate.get("confidence") == "high":
        score += 20
    evidence = candidate.get("evidence")
    if isinstance(evidence, dict) and evidence:
        score += 5
    return score


def _command_rank(command_id: str) -> int:
    return _COMMAND_RANK.get(command_id, 0)


def _command_summary(command: dict[str, object]) -> dict[str, object]:
    return {
        "command_id": command.get("command_id"),
        "output_affecting": command.get("output_affecting") is True,
        "verifier": _default_verifier_for_actions([str(command.get("command_id") or "")]),
    }


def _command_id_affects_output(command_id: str) -> bool:
    return command_id != "comment.edit"


def _select_command_action(inspect_report: dict[str, object]) -> dict[str, object] | None:
    candidates = inspect_report.get("candidate_work")
    if not isinstance(candidates, list):
        inspect_report["planner"] = {"status": "no_candidate", "ranked_candidates": [], "skipped_candidates": []}
        return None
    ranked: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    eligible: list[dict[str, object]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        options = _candidate_command_options(candidate)
        command = options[0] if options else None
        score = _candidate_score(candidate, command)
        checked = dict(candidate)
        checked["planner_score"] = score
        checked["candidate_commands"] = [_command_summary(option) for option in options]
        ranked.append(checked)
        skip_reason = _candidate_skip_reason(candidate, command)
        if skip_reason is not None:
            checked["stop_reason"] = skip_reason
            skipped.append(checked)
            continue
        selected = dict(candidate)
        selected["planner_score"] = score
        eligible.append({"work_item": selected, "command": command, "planner_score": score})
    eligible.sort(key=lambda item: cast(int, item["planner_score"]), reverse=True)
    ranked.sort(key=lambda item: cast(int, item["planner_score"]), reverse=True)
    if not eligible:
        inspect_report["planner"] = {
            "status": "no_candidate",
            "ranked_candidates": ranked,
            "skipped_candidates": skipped,
            "message": "no supported source-converging command candidate",
        }
        return None
    selected = eligible[0]
    command = cast(dict[str, object], selected["command"])
    inspect_report["planner"] = {
        "status": "selected",
        "ranked_candidates": ranked,
        "skipped_candidates": skipped,
        "selected_candidate_id": cast(dict[str, object], selected["work_item"]).get("candidate_id")
        or cast(dict[str, object], selected["work_item"]).get("id"),
        "selected_command_id": command.get("command_id"),
        "selection_reason": "highest-ranked supported source-converging command",
    }
    return {"work_item": cast(dict[str, object], selected["work_item"]), "command": command}


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
    if kind == "element":
        return {
            "context": ["element"],
            "locator": [json.dumps(context["locator"])],
            "element_id": [str(context["element_id"])],
        }
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
        "planner": inspect_report.get("planner"),
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
