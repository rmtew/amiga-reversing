from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.listing_context import listing_element_contexts
from amiga_reversing.disasm.manual_actions import review_item_is_open
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata
from amiga_reversing.reversing_workspace import (
    clean_run_target_workspace,
    inspect_target_hygiene,
)

TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "stopped"})
PARTIAL_ITERATION_STATUSES = frozenset({"started", "running", "partial"})
_LISTING_COMMENT_SEARCH_ROW_COUNT = 512
_LISTING_SOURCE_CANDIDATE_ROW_COUNT = 2048
_LISTING_SOURCE_CANDIDATE_MAX_ROWS = 16384
_COMMAND_RANK = {
    "label.rename": 100,
    "review.seed.code": 92,
    "review.seed.data.raw": 87,
    "review.seed.data.string": 87,
    "review.seed.data.scalar_table": 87,
    "review.seed.data.pointer_table": 87,
    "review.label.rename": 86,
    "review.label.change_scope": 84,
    "review.label.remove": 66,
    "app_slot.rename": 82,
    "app_slot.edit": 80,
    "row.seed.code": 90,
    "row.seed.data.raw": 85,
    "row.seed.data.byte": 85,
    "row.seed.data.word": 85,
    "row.seed.data.long": 85,
    "row.seed.data.string": 85,
    "row.seed.data.scalar_table": 85,
    "row.seed.data.pointer_table": 85,
    "range.seed.code": 90,
    "data_symbol.rename": 82,
    "data_symbol.rename_existing": 83,
    "rsset.binding.bind": 81,
    "target.rsset_region.rename": 82,
    "target.rsset_region.add": 80,
    "target.rsset_region.edit": 80,
    "representation.choose": 75,
    "representation.hex": 75,
    "representation.binary": 75,
    "representation.character": 75,
    "semantic.register.struct_ptr": 73,
    "target.equate.add": 72,
    "target.equate.edit": 72,
    "target.equate.represent": 72,
    "target.equate.rename": 72,
    "target.equate.remove": 68,
    "target.custom_struct.add": 72,
    "target.custom_struct.edit": 72,
    "target.custom_struct.rename": 72,
    "target.custom_struct.remove": 68,
    "target.custom_struct_field.add": 72,
    "target.custom_struct_field.edit": 72,
    "target.custom_struct_field.rename": 72,
    "target.custom_struct_field.remove": 68,
    "target.execution_view.add": 72,
    "target.execution_view.edit": 72,
    "target.execution_view.remove": 68,
    "typed_gap.field.add": 72,
    "typed_gap.field.edit": 72,
    "typed_access.field.edit": 72,
    "typed_access.field.rename": 72,
    "typed_access.field.remove": 68,
    "app_slot.remove": 66,
    "target.rsset_region.remove": 66,
    "rsset.binding.unbind": 66,
    "review.seed.remove": 66,
    "data_symbol.remove": 65,
    "comment.edit": 10,
}
_COMMAND_PREFIX_RANK = {
    "review.seed.data.": 87,
    "range.seed.data.": 85,
    "semantic.library_base.": 74,
    "semantic.lvo.": 73,
    "semantic.struct_offset.": 73,
    "semantic.equate.": 73,
    "correction.suppress_seeded_item.": 67,
}
_SEMANTIC_COMMAND_PREFIXES = (
    "semantic.library_base.",
    "semantic.lvo.",
    "semantic.struct_offset.",
    "semantic.equate.",
)
_REPORT_ONLY_COMMAND_PREFIXES = ("provenance.explore_",)
_TARGET_LOCAL_EFFECTS: dict[str, tuple[str, str]] = {
    "target.equate.add": ("target_equate", "target_equate"),
    "target.equate.edit": ("target_equate", "target_equate"),
    "target.equate.represent": ("target_equate", "target_equate"),
    "target.equate.rename": ("target_equate", "target_equate"),
    "target.equate.remove": ("target_equate_remove", "target_equate"),
    "target.rsset_region.add": ("rsset_layout_region", "rsset_layout_region"),
    "target.rsset_region.edit": ("rsset_layout_region", "rsset_layout_region"),
    "target.rsset_region.rename": ("rsset_layout_region", "rsset_layout_region"),
    "target.rsset_region.remove": ("rsset_layout_region_remove", "rsset_layout_region"),
    "rsset.binding.bind": ("rsset_use_site_binding", "rsset_use_site_binding"),
    "rsset.binding.unbind": ("rsset_use_site_binding_remove", "rsset_use_site_binding"),
    "target.custom_struct.add": ("custom_struct", "custom_struct"),
    "target.custom_struct.edit": ("custom_struct", "custom_struct"),
    "target.custom_struct.rename": ("custom_struct", "custom_struct"),
    "target.custom_struct.remove": ("custom_struct_remove", "custom_struct"),
    "target.custom_struct_field.add": ("custom_struct_field", "custom_struct_field"),
    "target.custom_struct_field.edit": ("custom_struct_field", "custom_struct_field"),
    "target.custom_struct_field.rename": ("custom_struct_field", "custom_struct_field"),
    "target.custom_struct_field.remove": ("custom_struct_field_remove", "custom_struct_field"),
    "target.execution_view.add": ("execution_view", "execution_view"),
    "target.execution_view.edit": ("execution_view", "execution_view"),
    "target.execution_view.remove": ("execution_view_remove", "execution_view"),
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
        inspect_report = _inspect_report_with_listing_candidates(target_id, inspect_report, project_root=project_root)
    iteration_id = _next_iteration_id(run_result.run_state)
    selected = _select_command_action(inspect_report)
    if (
        (selected is None or _selected_command_id(selected) == "comment.edit")
        and bool(inspect_report.get("candidate_work"))
        and inspect_report.get("safe_to_mutate") is True
        and _round_trip_verifier_available(inspect_report)
        and not inspect_report.get("listing_open")
    ):
        inspect_report = _inspect_report_with_listing_candidates(target_id, inspect_report, project_root=project_root)
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

    command_policy = _command_execution_policy_blocker(command)
    if command_policy is not None:
        verification = {"status": "failed", "layers": [command_policy]}
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
                evidence={"kind": "api_gap", "name": "command_execution_policy"},
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

    command_verifier = _candidate_verifier(cast(dict[str, object], selected["work_item"]), command)
    if command_verifier is None:
        verification = {
            "status": "failed",
            "layers": [
                {
                    "layer": "verifier",
                    "status": "failed",
                    "message": "source-converging action requires an action-specific verifier",
                    "command_id": command.get("command_id"),
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
                evidence={"kind": "missing_verifier", "name": str(command.get("command_id") or "")},
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
    catalog_entry = _available_catalog_command(command, availability)
    if catalog_entry is None:
        alternate = _select_available_command_action(target_id, inspect_report, excluded_command=command)
        if alternate is not None:
            selected = alternate
            command = cast(dict[str, object], selected["command"])
            availability = cast(dict[str, object], selected["availability"])
            catalog_entry = _available_catalog_command(command, availability)
        else:
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

    catalog_policy = _command_execution_policy_blocker(command, catalog_entry)
    if catalog_policy is not None:
        verification = {"status": "failed", "layers": [catalog_policy]}
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
                evidence={"kind": "api_gap", "name": "command_execution_policy"},
            ),
        )
        return write_iteration_report(target_id, report, project_root=project_root)

    if _command_requires_round_trip(command) and not _round_trip_verifier_available(inspect_report):
        availability_layer = {
            "layer": "round_trip",
            "status": "failed",
            "message": "output-affecting action requires an available round-trip verifier",
        }
        verification = {"status": "failed", "layers": [availability_layer]}
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
    verification = _verify_provenance_backed_mutation(command, result, verification)
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
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    listing_ready = _open_and_wait_listing(target_id, timeout_seconds=10.0)
    if listing_ready.get("status") != "ready":
        return {**inspect_report, "listing_open": listing_ready}
    try:
        rows = _listing_source_candidate_rows(target_id)
    except Exception as exc:
        return {**inspect_report, "listing_open": {"status": "failed", "message": str(exc)}}
    existing_candidates = inspect_report.get("candidate_work")
    candidates = list(existing_candidates) if isinstance(existing_candidates, list) else []
    candidates.extend(
        _listing_entrypoint_label_candidates(
            target_id,
            rows if isinstance(rows, list) else [],
            project_root=project_root,
            existing_labels=_existing_source_label_names(inspect_report),
        )
    )
    candidates.extend(
        _listing_representation_candidates(
            rows if isinstance(rows, list) else [],
            existing_representations=_existing_representation_keys(inspect_report),
        )
    )
    candidates.extend(
        _listing_data_symbol_candidates(
            rows if isinstance(rows, list) else [],
            existing_data_symbols=_existing_data_symbol_names(inspect_report),
        )
    )
    candidates.extend(
        _listing_data_role_candidates(
            rows if isinstance(rows, list) else [],
            existing_data_roles=_existing_data_seed_roles(inspect_report),
        )
    )
    candidates.extend(
        _listing_struct_pointer_candidates(
            rows if isinstance(rows, list) else [],
            existing_register_seeds=_existing_register_seed_map(inspect_report),
        )
    )
    candidates.extend(
        _listing_library_base_candidates(
            rows if isinstance(rows, list) else [],
            existing_register_seeds=_existing_register_seed_map(inspect_report),
        )
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


def _listing_source_candidate_rows(target_id: str) -> list[object]:
    rows: list[object] = []
    start = 0
    while start < _LISTING_SOURCE_CANDIDATE_MAX_ROWS:
        count = min(_LISTING_SOURCE_CANDIDATE_ROW_COUNT, _LISTING_SOURCE_CANDIDATE_MAX_ROWS - start)
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {"start": [str(start)], "count": [str(count)]},
        )
        data = listing.get("data")
        if not isinstance(data, dict):
            break
        page_rows = data.get("rows")
        if not isinstance(page_rows, list) or not page_rows:
            break
        rows.extend(page_rows)
        if data.get("has_more_after") is not True:
            break
        raw_end = data.get("end")
        next_start = raw_end if isinstance(raw_end, int) and not isinstance(raw_end, bool) else None
        if next_start is None or next_start <= start:
            next_start = start + len(page_rows)
        start = next_start
    return rows


def _listing_entrypoint_label_candidates(
    target_id: str,
    rows: list[object],
    *,
    project_root: Path,
    existing_labels: dict[tuple[int, int], str] | None = None,
) -> list[dict[str, object]]:
    entrypoint = _source_entrypoint_evidence(target_id, project_root=project_root)
    if entrypoint is None:
        return []
    section_index = entrypoint["section_index"]
    offset = entrypoint["offset"]
    if not isinstance(section_index, int) or not isinstance(offset, int):
        return []
    new_label = "entrypoint"
    existing = existing_labels or {}
    if existing.get((section_index, offset)) == new_label:
        return []
    candidates: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        locator_payload = cast(dict[str, object], locator)
        if row.get("kind") != "label" or not _row_covers_source_location(row, locator_payload, section_index, offset):
            continue
        current_label = row.get("label")
        if not isinstance(current_label, str):
            continue
        parsed_label = _parse_generated_source_label_symbol(current_label)
        if parsed_label != (section_index, offset):
            continue
        row_key = locator_payload.get("row_key")
        element_id = f"{row_key}:label:{current_label}"
        candidate_id = f"entrypoint-label:{row_key}:{new_label}"
        candidates.append(
            {
                "id": candidate_id,
                "candidate_id": candidate_id,
                "kind": "entrypoint_label_name",
                "durable_id": f"source_entrypoint_label:h{section_index}:${offset:08x}",
                "locator": dict(locator_payload),
                "element_id": element_id,
                "evidence": {
                    "source": "source_binary.json",
                    "source_kind": entrypoint["source_kind"],
                    "evidence_kind": entrypoint["evidence_kind"],
                    "entrypoint": offset,
                    "section_index": section_index,
                    "row_key": row_key,
                    "current_label": current_label,
                    "new_label": new_label,
                },
                "current_metadata": {
                    "label": current_label,
                    "row_kind": row.get("kind"),
                    "text": row.get("text"),
                },
                "expected_rendered_source_improvement": f"name source entrypoint label {new_label}",
                "suggested_action_kind": "label.rename",
                "suggested_action_kinds": ["label.rename"],
                "new_label": new_label,
                "default_verifier": "projected_label_name",
                "verifier": {"kind": "projected_label_name", "requires_semantic_reload": True},
                "confidence": "high",
                "rationale": entrypoint["rationale"],
                "actionable": True,
                "stop_reason": None,
            }
        )
    return candidates


def _parse_generated_source_label_symbol(symbol: str) -> tuple[int, int] | None:
    parts = symbol.split("_")
    if len(parts) != 3 or parts[0] != "loc" or not parts[1].isdigit():
        return None
    hunk_text, addr_text = parts[1], parts[2]
    if len(addr_text) != 8:
        return None
    try:
        return int(hunk_text), int(addr_text, 16)
    except ValueError:
        return None


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


def _listing_data_symbol_candidates(
    rows: list[object],
    *,
    existing_data_symbols: dict[tuple[int, int], str] | None = None,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    existing = existing_data_symbols or {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        locator_dict = cast(dict[str, object], locator)
        if row.get("kind") == "data":
            hunk = locator_dict.get("section_index")
            addr = locator_dict.get("start_offset")
            data_class = row.get("data_class")
            if isinstance(hunk, int) and isinstance(addr, int) and isinstance(data_class, str) and data_class:
                name = _data_ref_symbol_name(data_class, row.get("runtime_address"), hunk, addr)
                text = row.get("text")
                existing_name = existing.get((hunk, addr))
                row_symbol = row.get("symbol") or row.get("label")
                if existing_name is None and isinstance(row_symbol, str) and row_symbol:
                    existing_name = row_symbol
                if name is not None and existing_name != name and not (isinstance(text, str) and name in text):
                    row_key = locator_dict.get("row_key")
                    candidate_id = f"data-class-symbol:{row_key}:{hunk}:{addr:08X}:{name}"
                    candidates.append(
                        {
                            "id": candidate_id,
                            "candidate_id": candidate_id,
                            "kind": "data_symbol_name",
                            "durable_id": f"data_class:h{hunk}:{addr:08X}",
                            "locator": dict(locator_dict),
                            "target_hunk": hunk,
                            "target_addr": addr,
                            "target_end": locator_dict.get("end_offset"),
                            "runtime_address": row.get("runtime_address"),
                            "data_class": data_class,
                            "evidence": {
                                "source": "listing",
                                "evidence_kind": "data_class_row",
                                "data_class": data_class,
                                "runtime_address": row.get("runtime_address"),
                                "target_hunk": hunk,
                                "target_addr": addr,
                            },
                            "current_metadata": {"name": existing_name} if isinstance(existing_name, str) else {},
                            "expected_rendered_source_improvement": f"name {data_class} data row as {name}",
                            "suggested_action_kind": "data_symbol.rename_existing"
                            if isinstance(existing_name, str)
                            else "data_symbol.rename",
                            "suggested_action_kinds": [
                                "data_symbol.rename_existing" if isinstance(existing_name, str) else "data_symbol.rename"
                            ],
                            "new_name": name,
                            "default_verifier": "projected_data_symbol_name",
                            "verifier": {"kind": "projected_data_symbol_name", "requires_semantic_reload": True},
                            "confidence": "high",
                            "rationale": "listing data class identifies named data definition candidate",
                            "actionable": True,
                            "stop_reason": None,
                        }
                    )
        element_row = dict(row)
        if not isinstance(element_row.get("stable_key"), str) and isinstance(element_row.get("row_key"), str):
            element_row["stable_key"] = element_row["row_key"]
        text = row.get("text")
        for context in listing_element_contexts(element_row):
            if context.get("element_kind") != "data_ref":
                continue
            element_id = context.get("element_id")
            target_hunk = context.get("target_hunk")
            target_addr = context.get("target_addr")
            data_class = context.get("data_class")
            if (
                not isinstance(element_id, str)
                or not isinstance(target_hunk, int)
                or not isinstance(target_addr, int)
            ):
                continue
            name = _data_ref_symbol_name(
                data_class if isinstance(data_class, str) else "",
                context.get("runtime_address"),
                target_hunk,
                target_addr,
            )
            if name is None or (isinstance(text, str) and name in text):
                continue
            context_symbol = context.get("symbol")
            existing_name = existing.get((target_hunk, target_addr))
            if existing_name is None and isinstance(context_symbol, str) and context_symbol:
                existing_name = context_symbol
            if existing_name == name:
                continue
            row_key = cast(dict[str, object], locator).get("row_key")
            operand_index = context.get("operand_index")
            candidate_id = f"data-ref-symbol:{row_key}:{operand_index}:{target_hunk}:{target_addr:08X}:{name}"
            candidates.append(
                {
                    "id": candidate_id,
                    "candidate_id": candidate_id,
                    "kind": "data_symbol_name",
                    "durable_id": f"data_ref:h{target_hunk}:{target_addr:08X}",
                    "locator": dict(cast(dict[str, object], locator)),
                    "element_id": element_id,
                    "element_kind": "data_ref",
                    "operand_index": operand_index,
                    "target_hunk": target_hunk,
                    "target_addr": target_addr,
                    "target_end": context.get("target_end"),
                    "runtime_address": context.get("runtime_address"),
                    "data_class": data_class,
                    "evidence": {
                        "source": "listing",
                        "evidence_kind": "runtime_address_ref",
                        "data_class": data_class,
                        "runtime_address": context.get("runtime_address"),
                        "target_hunk": target_hunk,
                        "target_addr": target_addr,
                    },
                    "current_metadata": {"name": existing_name} if isinstance(existing_name, str) else {},
                    "expected_rendered_source_improvement": f"name referenced {data_class} data as {name}",
                    "suggested_action_kind": "data_symbol.rename_existing"
                    if isinstance(existing_name, str)
                    else "data_symbol.rename",
                    "suggested_action_kinds": [
                        "data_symbol.rename_existing" if isinstance(existing_name, str) else "data_symbol.rename"
                    ],
                    "new_name": name,
                    "default_verifier": "projected_data_symbol_name",
                    "verifier": {"kind": "projected_data_symbol_name", "requires_semantic_reload": True},
                    "confidence": "high",
                    "rationale": "internal runtime-address reference identifies named data use-site candidate",
                    "actionable": True,
                    "stop_reason": None,
                }
            )
    return candidates


def _listing_struct_pointer_candidates(
    rows: list[object],
    *,
    existing_register_seeds: dict[tuple[str, str], dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    existing = existing_register_seeds or {}
    candidates: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        element_row = dict(row)
        if not isinstance(element_row.get("stable_key"), str) and isinstance(element_row.get("row_key"), str):
            element_row["stable_key"] = element_row["row_key"]
        contexts = listing_element_contexts(element_row)
        register_contexts = [
            context
            for context in contexts
            if isinstance(context.get("register"), str)
        ]
        for context in contexts:
            if context.get("element_kind") != "typed_gap":
                continue
            register = context.get("base_register")
            struct_name = context.get("root_struct_name") or context.get("refined_struct_name")
            operand_index = context.get("operand_index")
            if not isinstance(register, str) or not isinstance(struct_name, str) or not struct_name:
                continue
            register = register.upper()
            register_context = next(
                (
                    candidate_context
                    for candidate_context in register_contexts
                    if str(candidate_context.get("register")).upper() == register
                    and candidate_context.get("operand_index") == operand_index
                ),
                None,
            )
            if register_context is None:
                continue
            current = existing.get((register, "struct_ptr"), {})
            if current.get("struct_name") == struct_name:
                continue
            element_id = register_context.get("element_id")
            row_key = cast(dict[str, object], locator).get("row_key")
            if not isinstance(element_id, str):
                continue
            candidate_id = f"struct-ptr:{row_key}:{operand_index}:{register}:{struct_name}"
            candidates.append(
                {
                    "id": candidate_id,
                    "candidate_id": candidate_id,
                    "kind": "register_semantic",
                    "durable_id": f"register_seed:{register}:struct_ptr",
                    "locator": dict(cast(dict[str, object], locator)),
                    "element_id": element_id,
                    "element_kind": register_context.get("element_kind"),
                    "operand_index": operand_index,
                    "register": register,
                    "base_register": register,
                    "evidence": {
                        "source": "listing",
                        "evidence_kind": "unresolved_typed_access",
                        "classification": context.get("classification"),
                        "displacement": context.get("displacement"),
                        "root_struct_name": context.get("root_struct_name"),
                        "refined_struct_name": context.get("refined_struct_name"),
                    },
                    "current_metadata": dict(current),
                    "expected_rendered_source_improvement": f"treat {register} as {struct_name} struct pointer",
                    "suggested_action_kind": "semantic.register.struct_ptr",
                    "suggested_action_kinds": ["semantic.register.struct_ptr"],
                    "parameters": {"struct_name": struct_name},
                    "default_verifier": "struct_pointer_register_seed",
                    "verifier": {"kind": "struct_pointer_register_seed", "requires_semantic_reload": True},
                    "confidence": "high",
                    "rationale": "typed-access analysis found a base register with unresolved struct field usage",
                    "actionable": True,
                    "stop_reason": None,
                }
            )
    return candidates


def _listing_library_base_candidates(
    rows: list[object],
    *,
    existing_register_seeds: dict[tuple[str, str], dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    existing = existing_register_seeds or {}
    candidates: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        element_row = dict(row)
        if not isinstance(element_row.get("stable_key"), str) and isinstance(element_row.get("row_key"), str):
            element_row["stable_key"] = element_row["row_key"]
        for context in listing_element_contexts(element_row):
            if context.get("element_kind") != "symbol" or context.get("domain") != "lvo":
                continue
            library = context.get("api_library")
            function = context.get("api_function")
            register = context.get("base_register") or context.get("register")
            element_id = context.get("element_id")
            if (
                not isinstance(library, str)
                or not library
                or not isinstance(function, str)
                or not function
                or not isinstance(register, str)
                or not register
                or not isinstance(element_id, str)
            ):
                continue
            register = register.upper()
            current = existing.get((register, "library_base"), {})
            if current.get("library_name") == library:
                continue
            row_key = cast(dict[str, object], locator).get("row_key")
            operand_index = context.get("operand_index")
            symbol = context.get("symbol")
            candidate_id = f"library-base:{row_key}:{operand_index}:{register}:{library}"
            candidates.append(
                {
                    "id": candidate_id,
                    "candidate_id": candidate_id,
                    "kind": "api_register_semantic",
                    "durable_id": f"register_seed:{register}:library_base",
                    "locator": dict(cast(dict[str, object], locator)),
                    "element_id": element_id,
                    "element_kind": "symbol",
                    "operand_index": operand_index,
                    "symbol": symbol,
                    "base_register": register,
                    "api_library": library,
                    "api_function": function,
                    "domain": "lvo",
                    "evidence": {
                        "source": "listing",
                        "evidence_kind": "lvo_api_call",
                        "library": library,
                        "function": function,
                        "symbol": symbol,
                    },
                    "current_metadata": dict(current),
                    "expected_rendered_source_improvement": f"treat {register} as {library} base for {function}",
                    "suggested_action_kind": f"semantic.library_base.{library}",
                    "suggested_action_kinds": [f"semantic.library_base.{library}"],
                    "default_verifier": "library_base_register_seed",
                    "verifier": {"kind": "library_base_register_seed", "requires_semantic_reload": True},
                    "confidence": "high",
                    "rationale": "LVO API call identifies the selected library base register",
                    "actionable": True,
                    "stop_reason": None,
                }
            )
    return candidates


def _existing_register_seed_map(inspect_report: dict[str, object]) -> dict[tuple[str, str], dict[str, object]]:
    target_state = inspect_report.get("target_state")
    result: dict[tuple[str, str], dict[str, object]] = {}
    metadata = _effective_target_metadata_from_report(inspect_report)
    if metadata is not None:
        for seed in metadata.entry_register_seeds:
            result[(seed.register.upper(), seed.kind.value)] = {
                "entry_offset": seed.entry_offset,
                "register": seed.register,
                "kind": seed.kind.value,
                "note": seed.note,
                "library_name": seed.library_name,
                "struct_name": seed.struct_name,
                "context_name": seed.context_name,
            }
    project = target_state.get("project") if isinstance(target_state, dict) else None
    manual_state = project.get("manual_state") if isinstance(project, dict) else None
    register_seeds = manual_state.get("register_seeds") if isinstance(manual_state, dict) else None
    if not isinstance(register_seeds, list | tuple):
        return result
    for seed in register_seeds:
        if not isinstance(seed, dict):
            continue
        register = seed.get("register")
        kind = seed.get("kind")
        if isinstance(register, str) and isinstance(kind, str):
            result[(register.upper(), kind)] = dict(seed)
    return result


def _effective_target_metadata_from_report(inspect_report: dict[str, object]) -> TargetMetadata | None:
    target_state = inspect_report.get("target_state")
    target_dir = target_state.get("target_dir") if isinstance(target_state, dict) else None
    if not isinstance(target_dir, str):
        return None
    try:
        return effective_target_metadata(Path(target_dir))
    except (AssertionError, OSError, ValueError):
        return None


def _existing_data_symbol_names(inspect_report: dict[str, object]) -> dict[tuple[int, int], str]:
    target_state = inspect_report.get("target_state")
    names: dict[tuple[int, int], str] = {}
    metadata = _effective_target_metadata_from_report(inspect_report)
    if metadata is not None:
        for entity in metadata.seeded_entities:
            if isinstance(entity.name, str) and entity.name:
                names[(entity.hunk, entity.addr)] = entity.name
    project = target_state.get("project") if isinstance(target_state, dict) else None
    manual_state = project.get("manual_state") if isinstance(project, dict) else None
    seeds = manual_state.get("seeds") if isinstance(manual_state, dict) else None
    if not isinstance(seeds, list | tuple):
        return names
    for seed in seeds:
        if not isinstance(seed, dict) or seed.get("kind") != "data":
            continue
        hunk = seed.get("hunk")
        addr = seed.get("addr")
        name = seed.get("name")
        if isinstance(hunk, int) and isinstance(addr, int) and isinstance(name, str) and name:
            names[(hunk, addr)] = name
    return names


def _existing_source_label_names(inspect_report: dict[str, object]) -> dict[tuple[int, int], str]:
    target_state = inspect_report.get("target_state")
    names: dict[tuple[int, int], str] = {}
    metadata = _effective_target_metadata_from_report(inspect_report)
    if metadata is not None:
        for label in metadata.seeded_code_labels:
            if isinstance(label.name, str) and label.name:
                names[(label.hunk, label.addr)] = label.name
    project = target_state.get("project") if isinstance(target_state, dict) else None
    manual_state = project.get("manual_state") if isinstance(project, dict) else None
    labels = manual_state.get("labels") if isinstance(manual_state, dict) else None
    if not isinstance(labels, list | tuple):
        return names
    for label in labels:
        if not isinstance(label, dict):
            continue
        hunk = label.get("hunk", 0)
        addr = label.get("addr")
        name = label.get("name")
        address_domain = label.get("address_domain")
        if address_domain == "runtime":
            continue
        if isinstance(hunk, int) and isinstance(addr, int) and isinstance(name, str) and name:
            names[(hunk, addr)] = name
    return names


def _listing_data_role_candidates(
    rows: list[object],
    *,
    existing_data_roles: dict[tuple[int, int], str] | None = None,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    existing = existing_data_roles or {}
    for row in rows:
        if not isinstance(row, dict) or row.get("kind") != "data":
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        locator_dict = cast(dict[str, object], locator)
        hunk = locator_dict.get("section_index")
        addr = locator_dict.get("start_offset")
        if not isinstance(hunk, int) or not isinstance(addr, int):
            continue
        if existing.get((hunk, addr)) == "string" or row.get("data_class") == "string":
            continue
        text = row.get("text")
        if isinstance(text, str) and '"' in text:
            continue
        string_text = _ascii_string_from_row_bytes(row.get("bytes"))
        if string_text is None:
            continue
        row_key = locator_dict.get("row_key")
        candidate_id = f"data-role-string:{row_key}:{hunk}:{addr:08X}"
        candidates.append(
            {
                "id": candidate_id,
                "candidate_id": candidate_id,
                "kind": "data_role_seed",
                "durable_id": f"data_role:h{hunk}:{addr:08X}:string",
                "locator": dict(locator_dict),
                "evidence": {
                    "source": "listing",
                    "evidence_kind": "null_terminated_printable_ascii",
                    "preview": string_text,
                },
                "current_metadata": {"data_role": existing.get((hunk, addr))} if (hunk, addr) in existing else {},
                "expected_rendered_source_improvement": f"render printable bytes as ASCII string {string_text!r}",
                "suggested_action_kind": "row.seed.data.string",
                "suggested_action_kinds": ["row.seed.data.string"],
                "parameters": {"seed_kind": "data", "data_role": "string", "unit": "byte", "encoding": "ascii"},
                "default_verifier": "manual_seed_state",
                "verifier": {"kind": "manual_seed_state", "requires_semantic_reload": True},
                "confidence": "high",
                "rationale": "data row bytes form a null-terminated printable ASCII string",
                "actionable": True,
                "stop_reason": None,
            }
        )
    return candidates


def _existing_data_seed_roles(inspect_report: dict[str, object]) -> dict[tuple[int, int], str]:
    target_state = inspect_report.get("target_state")
    roles: dict[tuple[int, int], str] = {}
    metadata = _effective_target_metadata_from_report(inspect_report)
    if metadata is not None:
        for entity in metadata.seeded_entities:
            if entity.type == "data" and isinstance(entity.subtype, str) and entity.subtype:
                roles[(entity.hunk, entity.addr)] = entity.subtype
    project = target_state.get("project") if isinstance(target_state, dict) else None
    manual_state = project.get("manual_state") if isinstance(project, dict) else None
    seeds = manual_state.get("seeds") if isinstance(manual_state, dict) else None
    if not isinstance(seeds, list | tuple):
        return roles
    for seed in seeds:
        if not isinstance(seed, dict) or seed.get("kind") != "data":
            continue
        hunk = seed.get("hunk")
        addr = seed.get("addr")
        data_role = seed.get("data_role")
        if isinstance(hunk, int) and isinstance(addr, int) and isinstance(data_role, str) and data_role:
            roles[(hunk, addr)] = data_role
    return roles


def _ascii_string_from_row_bytes(value: object) -> str | None:
    if isinstance(value, str):
        try:
            data = bytes.fromhex(value)
        except ValueError:
            return None
    elif isinstance(value, bytes):
        data = value
    else:
        return None
    if len(data) < 3 or data[-1] != 0:
        return None
    body = data[:-1]
    if not body or any(byte < 0x20 or byte > 0x7E for byte in body):
        return None
    return body.decode("ascii")


def _data_ref_symbol_name(data_class: str, runtime_address: object, target_hunk: int, target_addr: int) -> str | None:
    prefix = _symbol_name_fragment(data_class)
    if isinstance(runtime_address, int) and not isinstance(runtime_address, bool):
        if prefix:
            return f"{prefix}_{runtime_address:08X}"
        return f"runtime_address_{runtime_address:08X}"
    if not prefix:
        return None
    return f"{prefix}_h{target_hunk}_{target_addr:08X}"


def _symbol_name_fragment(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "_" for char in value.strip()]
    return "_".join(part for part in "".join(chars).split("_") if part)


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
    regions = groups.get("app-slot-regions") if isinstance(groups, dict) else None
    existing = existing_regions or {}
    candidates: list[dict[str, object]] = []
    seen_candidate_ids: set[str] = set()

    def append_candidate(metadata: dict[str, object], evidence: dict[str, object]) -> None:
        parameters = _rsset_region_parameters_from_metadata(metadata)
        offset = parameters.get("offset")
        symbol = parameters.get("symbol")
        if not isinstance(offset, int) or not isinstance(symbol, str):
            return
        key = _rsset_region_key(parameters)
        current = existing.get(key, {})
        action_kind = "target.rsset_region.edit" if current else "target.rsset_region.add"
        layout_name, base_symbol, _ = key
        candidate_id = f"rsset-suggestion:{layout_name}:{base_symbol}:{offset:04X}:{symbol}"
        if candidate_id in seen_candidate_ids:
            return
        seen_candidate_ids.add(candidate_id)
        candidates.append(
            {
                "id": candidate_id,
                "candidate_id": candidate_id,
                "kind": "rsset_layout_region",
                "durable_id": f"rsset_region:{layout_name}:{base_symbol}:{offset:04X}",
                "evidence": evidence,
                "current_metadata": dict(current),
                "expected_rendered_source_improvement": f"add RSSET region field {symbol} at app+0x{offset:04X}",
                "suggested_action_kind": action_kind,
                "suggested_action_kinds": [action_kind],
                "parameters": parameters,
                "default_verifier": "rsset_region_state",
                "verifier": {"kind": "rsset_region_state", "requires_semantic_reload": True},
                "confidence": "high" if evidence.get("confidence") in {"high", "tool-inferred"} else "medium",
                "rationale": "app-slot analysis suggested durable RSSET layout metadata",
                "actionable": True,
                "stop_reason": None,
            }
        )
    if isinstance(suggestions, list):
        for suggestion in suggestions:
            if not isinstance(suggestion, dict) or suggestion.get("action") != "add_target_metadata":
                continue
            metadata = suggestion.get("metadata")
            if not isinstance(metadata, dict):
                continue
            append_candidate(
                metadata,
                {
                    "source": "app_slot_analysis",
                    "navigation_group": "app-slot-suggestions",
                    "summary": suggestion.get("summary"),
                    "confidence": suggestion.get("confidence"),
                    "stable_key": suggestion.get("stable_key"),
                    "row_index": suggestion.get("row_index"),
                },
            )
    if isinstance(regions, list):
        for region in regions:
            if not isinstance(region, dict) or region.get("source") != "platform_api_arg":
                continue
            append_candidate(
                region,
                {
                    "source": "app_slot_analysis",
                    "navigation_group": "app-slot-regions",
                    "summary": region.get("summary"),
                    "confidence": region.get("confidence"),
                    "row_index": region.get("row_index"),
                    "addr": region.get("addr"),
                    "hunk_index": region.get("hunk_index"),
                },
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
    result: dict[tuple[str, str, int], dict[str, object]] = {}
    metadata = _effective_target_metadata_from_report(inspect_report)
    if metadata is not None:
        for region in metadata.rsset_layout_regions:
            payload = {
                "offset": region.offset,
                "size": region.size,
                "layout_name": region.layout_name,
                "base_symbol": region.base_symbol,
                "sizeof_symbol": region.sizeof_symbol,
                "symbol": region.symbol,
                "struct_name": region.struct_name,
                "pointer_struct": region.pointer_struct,
                "storage_kind": None if region.storage_kind is None else region.storage_kind.value,
                "semantic_type": region.semantic_type,
                "parser_role": region.parser_role,
                "parser_routine": region.parser_routine,
                "parse_order": region.parse_order,
            }
            result[_rsset_region_key(payload)] = payload
    project = target_state.get("project") if isinstance(target_state, dict) else None
    manual_state = project.get("manual_state") if isinstance(project, dict) else None
    regions = manual_state.get("rsset_layout_regions") if isinstance(manual_state, dict) else None
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
    if any(action.startswith("review.label.") for action in actions):
        return "manual_label_state"
    if "comment.edit" in actions:
        return "projection_metadata"
    if "data_symbol.rename_existing" in actions or "data_symbol.rename" in actions:
        return "projected_data_symbol_name"
    if "data_symbol.remove" in actions:
        return "suppressed_seeded_item"
    if any(action.startswith("target.rsset_region.") for action in actions):
        return "rsset_region_state"
    if any(action.startswith("app_slot.") for action in actions):
        return "rsset_region_state"
    if any(action.startswith("rsset.binding.") for action in actions):
        return "rsset_binding_state"
    if any(action in {"row.data_block.layout.create", "range.data_block.layout.create"} for action in actions):
        return "data_block_layout_state"
    if any(
        action
        in {
            "row.data_block.element.set",
            "range.data_block.element.set",
            "row.data_block.element.remove",
            "range.data_block.element.remove",
            "row.data_block.element.represent",
            "range.data_block.element.represent",
            "row.data_block.element.bind_type",
            "row.data_block.element.clear_type",
        }
        for action in actions
    ):
        return "data_block_element_state"
    if any(action in {"row.data_block.element.interpret_ref", "row.data_block.element.clear_ref"} for action in actions):
        return "data_block_interpreted_ref_state"
    if any(action.startswith("target.execution_view.") for action in actions):
        return "execution_view_state"
    if any(action.startswith(("typed_gap.field.", "typed_access.field.")) for action in actions):
        return "custom_struct_field_state"
    if any(action.startswith("correction.suppress_seeded_item.") for action in actions):
        return "suppressed_seeded_item"
    if any(action.startswith("target.equate.") for action in actions):
        return "target_equate_state"
    if any(action.startswith("semantic.library_base.") for action in actions):
        return "library_base_register_seed"
    if "semantic.register.struct_ptr" in actions:
        return "struct_pointer_register_seed"
    if any(action.startswith(("semantic.lvo.", "semantic.struct_offset.", "semantic.equate.")) for action in actions):
        return "semantic_hint_state"
    if any(action == "create_manual_seed" or action.startswith(("row.seed.", "review.seed.", "range.seed.")) for action in actions):
        return "manual_seed_state"
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
    if command_id == "comment.edit":
        return _verify_listing_comment_mutation(target_id, command, durable_result, project_root=project_root)
    if command_id == "label.rename":
        location = _label_command_source_location(command)
        if location is None:
            return {
                "status": "failed",
                "layers": [
                    {
                        "layer": "projection",
                        "status": "failed",
                        "message": "label.rename verification requires a source locator",
                    }
                ],
            }
        section_index, source_offset = location
        return _verify_listing_label_rename_mutation(
            target_id,
            command,
            durable_result,
            section_index=section_index,
            source_offset=source_offset,
            project_root=project_root,
        )
    if command_id in {"data_symbol.rename", "data_symbol.rename_existing"}:
        return _verify_data_symbol_rename_mutation(target_id, command, durable_result, project_root=project_root)
    if command_id == "data_symbol.remove":
        if _manual_seed_removals_from_durable_result(durable_result):
            return _verify_manual_seed_mutation(
                target_id,
                "data_symbol.remove",
                durable_result,
                project_root=project_root,
            )
        return _verify_seeded_item_suppression_mutation(target_id, durable_result, project_root=project_root)
    if isinstance(command_id, str) and command_id.startswith("correction.suppress_seeded_item."):
        return _verify_seeded_item_suppression_mutation(target_id, durable_result, project_root=project_root)
    if isinstance(command_id, str) and command_id.startswith("review.label."):
        return _verify_manual_label_mutation(
            target_id,
            str(command_id),
            durable_result,
            project_root=project_root,
        )
    if isinstance(command_id, str) and command_id.startswith("target.equate."):
        return _verify_target_equate_mutation(
            target_id,
            str(command_id),
            durable_result,
            project_root=project_root,
        )
    if isinstance(command_id, str) and command_id.startswith(("target.rsset_region.", "app_slot.")):
        return _verify_rsset_region_mutation(
            target_id,
            str(command_id),
            durable_result,
            project_root=project_root,
        )
    if isinstance(command_id, str) and command_id.startswith("rsset.binding."):
        return _verify_rsset_binding_mutation(
            target_id,
            str(command_id),
            durable_result,
            project_root=project_root,
        )
    if command_id in {"row.data_block.layout.create", "range.data_block.layout.create"}:
        return _verify_data_block_layout_mutation(
            target_id,
            command,
            str(command_id),
            durable_result,
            project_root=project_root,
        )
    if command_id in {
        "row.data_block.element.set",
        "range.data_block.element.set",
        "row.data_block.element.remove",
        "range.data_block.element.remove",
        "row.data_block.element.represent",
        "range.data_block.element.represent",
        "row.data_block.element.bind_type",
        "row.data_block.element.clear_type",
    }:
        if command_id in {"row.data_block.element.bind_type", "row.data_block.element.clear_type"}:
            return _verify_data_block_type_binding_mutation(
                target_id,
                command,
                str(command_id),
                durable_result,
                project_root=project_root,
            )
        return _verify_data_block_element_mutation(
            target_id,
            command,
            str(command_id),
            durable_result,
            project_root=project_root,
        )
    if command_id in {"row.data_block.element.interpret_ref", "row.data_block.element.clear_ref"}:
        return _verify_data_block_interpreted_ref_mutation(
            target_id,
            command,
            str(command_id),
            durable_result,
            project_root=project_root,
        )
    if command_id in {"target.execution_view.add", "target.execution_view.edit", "target.execution_view.remove"}:
        return _verify_execution_view_mutation(
            target_id,
            str(command_id),
            durable_result,
            project_root=project_root,
        )
    if isinstance(command_id, str) and command_id.startswith(("typed_gap.field.", "typed_access.field.")):
        return _verify_custom_struct_field_mutation(
            target_id,
            command,
            command_id,
            durable_result,
            project_root=project_root,
        )
    if isinstance(command_id, str) and command_id.startswith(
        ("semantic.lvo.", "semantic.struct_offset.", "semantic.equate.")
    ):
        return _verify_semantic_hint_mutation(target_id, durable_result, project_root=project_root)
    if isinstance(command_id, str) and command_id.startswith("semantic.library_base."):
        return _verify_library_base_register_seed_mutation(
            target_id,
            command,
            durable_result,
            project_root=project_root,
        )
    if command_id == "semantic.register.struct_ptr":
        return _verify_struct_pointer_register_seed_mutation(
            target_id,
            command,
            durable_result,
            project_root=project_root,
        )
    if isinstance(command_id, str) and command_id.startswith(("row.seed.", "range.seed.", "review.seed.")):
        return _verify_manual_seed_mutation(
            target_id,
            str(command_id),
            durable_result,
            project_root=project_root,
        )
    layers = [
        _verify_semantic_reload(target_id, durable_result, project_root=project_root),
        _verify_projection_metadata(command, durable_result),
    ]
    if _command_requires_round_trip(command):
        layers.append(_verify_round_trip_exact(target_id, project_root=project_root))
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


_ACCEPTED_PROVENANCE_STATUSES = frozenset({"analysis_proven", "path_specific", "manual_classified", "manual_override"})


def _verify_provenance_backed_mutation(
    command: dict[str, object],
    durable_result: dict[str, object],
    verification: dict[str, object],
) -> dict[str, object]:
    evidence = _consumed_provenance_evidence(command, durable_result)
    if evidence is None:
        return verification
    layers = verification.get("layers")
    if not isinstance(layers, list):
        layers = []
    layer = _verify_consumed_provenance_evidence(evidence, durable_result)
    updated_layers = _insert_verification_layer_after(layers, "manual_action_log", layer)
    status = "passed" if verification.get("status") == "passed" and layer["status"] == "passed" else "failed"
    return {**verification, "status": status, "layers": updated_layers}


def _consumed_provenance_evidence(
    command: dict[str, object],
    durable_result: dict[str, object],
) -> dict[str, object] | None:
    durable_evidence = _find_source_evidence_payload(durable_result)
    command_evidence_id = _command_consumed_source_evidence_id(command)
    if durable_evidence is not None:
        evidence = dict(durable_evidence)
        if isinstance(command_evidence_id, str) and command_evidence_id:
            evidence["expected_source_evidence_id"] = command_evidence_id
        return evidence
    if command_evidence_id is None:
        return None
    return {"source_evidence_id": command_evidence_id, "missing_durable_payload": True}


def _command_consumed_source_evidence_id(command: dict[str, object]) -> str | None:
    evidence = _command_source_evidence_payload(command)
    if evidence is None:
        return None
    evidence_id = evidence.get("source_evidence_id")
    return evidence_id if isinstance(evidence_id, str) and evidence_id else None


def _command_source_evidence_payload(command: dict[str, object]) -> dict[str, object] | None:
    evidence_id = command.get("source_evidence_id")
    if isinstance(evidence_id, str) and evidence_id:
        return command
    parameters = command.get("parameters")
    if isinstance(parameters, dict):
        evidence_id = parameters.get("source_evidence_id")
        if isinstance(evidence_id, str) and evidence_id:
            return cast(dict[str, object], parameters)
    return None


def _find_source_evidence_payload(value: object) -> dict[str, object] | None:
    if isinstance(value, dict):
        evidence_id = value.get("source_evidence_id")
        if isinstance(evidence_id, str) and evidence_id:
            return cast(dict[str, object], value)
        for child in value.values():
            found = _find_source_evidence_payload(child)
            if found is not None:
                return found
    elif isinstance(value, list | tuple):
        for child in value:
            found = _find_source_evidence_payload(child)
            if found is not None:
                return found
    return None


def _verify_consumed_provenance_evidence(
    evidence: dict[str, object],
    durable_result: dict[str, object],
) -> dict[str, object]:
    evidence_id = evidence.get("source_evidence_id")
    source_family = evidence.get("source_family") or evidence.get("evidence_source_family")
    status = evidence.get("source_evidence_status") or evidence.get("evidence_status") or evidence.get("status")
    scope = evidence.get("path_lifetime_scope")
    cleanup_scope = evidence.get("cleanup_scope")
    owner_action_id = evidence.get("owner_action_id") or _durable_action_id(durable_result)
    failures: list[str] = []
    if evidence.get("missing_durable_payload") is True:
        failures.append("durable action payload missing consumed source_evidence_id")
    if not isinstance(evidence_id, str) or not evidence_id:
        failures.append("missing source_evidence_id")
    expected_evidence_id = evidence.get("expected_source_evidence_id")
    if isinstance(expected_evidence_id, str) and expected_evidence_id and evidence_id != expected_evidence_id:
        failures.append("durable source_evidence_id does not match consumed command evidence")
    if not isinstance(source_family, str) or source_family in {"", "unknown", "conflicting"}:
        failures.append("missing accepted source_family")
    if not isinstance(status, str) or status not in _ACCEPTED_PROVENANCE_STATUSES:
        failures.append("source_evidence_status is not accepted")
    if not isinstance(scope, dict) or not scope.get("kind"):
        failures.append("missing path_lifetime_scope")
    conflicts = evidence.get("conflicts")
    has_conflicts = isinstance(conflicts, list) and bool(conflicts)
    if has_conflicts and status != "manual_override":
        failures.append("conflicts require manual_override")
    if status == "manual_override":
        if not isinstance(evidence.get("contradicted_evidence_id"), str) or not evidence.get("contradicted_evidence_id"):
            failures.append("manual_override missing contradicted_evidence_id")
        if not isinstance(evidence.get("reason"), str) or not evidence.get("reason"):
            failures.append("manual_override missing reason")
        if not isinstance(cleanup_scope, dict) or not cleanup_scope.get("kind"):
            failures.append("manual_override missing cleanup_scope")
        elif not _manual_override_cleanup_scope_matches_contradicted_evidence(evidence):
            failures.append("manual_override cleanup_scope does not match contradicted evidence")
    if not isinstance(owner_action_id, str) or not owner_action_id:
        failures.append("missing owner_action_id")
    return {
        "layer": "provenance_evidence",
        "status": "failed" if failures else "passed",
        "source_evidence_id": evidence_id,
        "expected_source_evidence_id": expected_evidence_id,
        "source_family": source_family,
        "source_evidence_status": status,
        "path_lifetime_scope": scope,
        "cleanup_scope": cleanup_scope,
        "owner_action_id": owner_action_id,
        "failures": failures,
    }


def _durable_action_id(durable_result: dict[str, object]) -> str | None:
    action = durable_result.get("action")
    if isinstance(action, dict):
        action_id = action.get("action_id")
        if isinstance(action_id, str) and action_id:
            return action_id
    return None


def _insert_verification_layer_after(
    layers: list[object],
    after_layer: str,
    layer: dict[str, object],
) -> list[object]:
    updated = list(layers)
    for index, existing in enumerate(updated):
        if isinstance(existing, dict) and existing.get("layer") == after_layer:
            updated.insert(index + 1, layer)
            return updated
    return [layer, *updated]


def _verify_data_symbol_rename_mutation(
    target_id: str,
    command: dict[str, object],
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    _open_and_wait_listing(target_id, timeout_seconds=10.0)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_semantic_reload(target_id, durable_result, project_root=project_root),
        _verify_projected_data_symbol_name(target_id, command),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _verify_target_equate_mutation(
    target_id: str,
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _target_equate_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_target_equate(target_id, command_id, expected, project_root=project_root),
    ]
    if _target_equate_payload_has_definition_representation(expected):
        layers.append(_verify_target_equate_rendered_definition(target_id, expected))
    layers.append(_verify_round_trip_exact(target_id, project_root=project_root))
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _target_equate_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    equate = _target_equate_from_action(action)
    if equate is not None:
        return equate
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            equate = _target_equate_from_action(raw_action)
            if equate is not None:
                return equate
    return None


def _target_equate_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    equate = action.get("target_equate")
    if isinstance(equate, dict):
        return cast(dict[str, object], equate)
    payload = action.get("payload")
    equate = payload.get("target_equate") if isinstance(payload, dict) else None
    if isinstance(equate, dict):
        return cast(dict[str, object], equate)
    return None


def _verify_project_target_equate(
    target_id: str,
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing target equate payload"}
    key = "removed_target_equates" if command_id == "target.equate.remove" else "target_equates"
    if command_id == "target.equate.rename":
        key = "renamed_target_equates"
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    equates = manual_state.get(key) if isinstance(manual_state, dict) else None
    if not isinstance(equates, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": f"manual {key} were not reloaded"}
    matches = [equate for equate in equates if isinstance(equate, dict) and _target_equate_matches(equate, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_target_equate": expected,
        "matching_target_equates": matches,
        "state_key": key,
    }


def _target_equate_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    for key in ("previous_name", "name", "value", "comment", "value_representation", "value_expression"):
        if key in expected and actual.get(key) != expected.get(key):
            return False
    return "name" in expected


def _target_equate_payload_has_definition_representation(expected: dict[str, object] | None) -> bool:
    return isinstance(expected, dict) and "value_representation" in expected


def _target_equate_expected_definition_expr(expected: dict[str, object]) -> str | None:
    style = expected.get("value_representation")
    value = expected.get("value")
    if not isinstance(style, str) or not isinstance(value, int):
        return None
    if style == "decimal":
        return str(value)
    if style == "binary":
        value_bits = value & 0xFFFFFFFF
        high_bit = 7 if 0 <= value <= 0xFF else 15 if 0 <= value <= 0xFFFF else 31
        return "%" + "".join("1" if (value_bits & (1 << bit)) else "0" for bit in range(high_bit, -1, -1))
    if style == "character":
        if 0 <= value <= 255:
            char = chr(value)
            if " " <= char <= "~" and char not in {"'", "\\"}:
                return f"'{char}'"
        return f"${value & 0xFFFFFFFF:X}"
    if style == "symbol":
        expression = expected.get("value_expression")
        return expression if isinstance(expression, str) and expression else None
    if style == "hex":
        return f"${value & 0xFFFFFFFF:X}"
    return None


def _verify_target_equate_rendered_definition(
    target_id: str,
    expected: dict[str, object] | None,
) -> dict[str, object]:
    if not isinstance(expected, dict):
        return {"layer": "rendered_source", "status": "failed", "message": "missing target equate payload"}
    name = expected.get("name")
    expected_expr = _target_equate_expected_definition_expr(expected)
    if not isinstance(name, str) or not expected_expr:
        return {
            "layer": "rendered_source",
            "status": "failed",
            "message": "target equate payload lacks rendered definition expectation",
            "expected_target_equate": expected,
        }
    try:
        navigation = server.route_request("GET", f"/api/projects/{target_id}/listing/navigation", {}, {})
    except Exception as exc:
        return {"layer": "rendered_source", "status": "failed", "message": str(exc)}
    data = navigation.get("data")
    groups = data.get("groups") if isinstance(data, dict) else None
    equates = groups.get("equates") if isinstance(groups, dict) else None
    if not isinstance(equates, list):
        return {"layer": "rendered_source", "status": "failed", "message": "equate navigation missing after reload"}
    matches = [
        equate
        for equate in equates
        if isinstance(equate, dict)
        and equate.get("symbol") == name
        and equate.get("operand") == expected_expr
        and any(isinstance(ref, dict) and ref.get("access") == "definition" for ref in equate.get("refs", []))
    ]
    return {
        "layer": "rendered_source",
        "status": "passed" if matches else "failed",
        "expected_symbol": name,
        "expected_operand": expected_expr,
        "matching_equates": matches,
    }


def _verify_rsset_region_mutation(
    target_id: str,
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _rsset_region_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_rsset_region(target_id, command_id, expected, project_root=project_root),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _rsset_region_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    region = _rsset_region_from_action(action)
    if region is not None:
        return region
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            region = _rsset_region_from_action(raw_action)
            if region is not None:
                return region
    return None


def _rsset_region_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    region = action.get("rsset_layout_region")
    if isinstance(region, dict):
        return cast(dict[str, object], region)
    payload = action.get("payload")
    region = payload.get("rsset_layout_region") if isinstance(payload, dict) else None
    if isinstance(region, dict):
        return cast(dict[str, object], region)
    return None


def _verify_project_rsset_region(
    target_id: str,
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing RSSET layout region payload"}
    key = "removed_rsset_layout_regions" if command_id.endswith(".remove") else "rsset_layout_regions"
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    regions = manual_state.get(key) if isinstance(manual_state, dict) else None
    if not isinstance(regions, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": f"manual {key} were not reloaded"}
    matches = [region for region in regions if isinstance(region, dict) and _rsset_region_matches(region, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_rsset_layout_region": expected,
        "matching_rsset_layout_regions": matches,
        "state_key": key,
    }


def _rsset_region_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    for key in (
        "rsset_layout_region_id",
        "offset",
        "size",
        "layout_name",
        "base_symbol",
        "sizeof_symbol",
        "symbol",
        "storage_kind",
        "struct_name",
        "pointer_struct",
        "semantic_type",
        "parser_role",
        "parser_routine",
        "parse_order",
    ):
        if key in expected and actual.get(key) != expected.get(key):
            return False
    return "offset" in expected


def _verify_rsset_binding_mutation(
    target_id: str,
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _rsset_binding_from_durable_result(durable_result)
    if expected is not None:
        expected = _rsset_binding_with_expected_action_owner(
            expected,
            durable_result,
            removed=command_id.endswith(".unbind"),
        )
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_rsset_binding(target_id, command_id, expected, project_root=project_root),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _rsset_binding_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    binding = _rsset_binding_from_action(action)
    if binding is not None:
        return binding
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            binding = _rsset_binding_from_action(raw_action)
            if binding is not None:
                return binding
    return None


def _rsset_binding_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    binding = action.get("rsset_use_site_binding")
    if isinstance(binding, dict):
        return dict(cast(dict[str, object], binding))
    payload = action.get("payload")
    binding = payload.get("rsset_use_site_binding") if isinstance(payload, dict) else None
    if isinstance(binding, dict):
        return dict(cast(dict[str, object], binding))
    return None


def _rsset_binding_with_expected_action_owner(
    binding: dict[str, object],
    durable_result: dict[str, object],
    *,
    removed: bool,
) -> dict[str, object]:
    action_id = _durable_action_id(durable_result)
    if not isinstance(action_id, str) or not action_id:
        return binding
    expected = dict(binding)
    if removed:
        expected.setdefault("cleanup_action_id", action_id)
    else:
        expected.setdefault("owner_action_id", action_id)
    return expected


def _verify_project_rsset_binding(
    target_id: str,
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing RSSET use-site binding payload"}
    key = "removed_rsset_use_site_bindings" if command_id.endswith(".unbind") else "rsset_use_site_bindings"
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    bindings = manual_state.get(key) if isinstance(manual_state, dict) else None
    if not isinstance(bindings, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": f"manual {key} were not reloaded"}
    matches = [binding for binding in bindings if isinstance(binding, dict) and _rsset_binding_matches(binding, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_rsset_use_site_binding": expected,
        "matching_rsset_use_site_bindings": matches,
        "state_key": key,
    }


def _rsset_binding_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    for key in (
        "rsset_use_site_binding_id",
        "hunk",
        "addr",
        "operand_index",
        "base_register",
        "displacement",
        "layout_name",
        "base_symbol",
        "base_evidence_id",
        "owner_action_id",
        "cleanup_action_id",
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "base_evidence_refs",
    ):
        if key in expected and actual.get(key) != expected.get(key):
            return False
    return "rsset_use_site_binding_id" in expected


def _verify_data_block_layout_mutation(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _data_block_layout_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_data_block_layout(target_id, command_id, expected, project_root=project_root),
        _verify_projected_data_block_rendered_source(
            target_id,
            command,
            command_id,
            expected,
            durable_result,
            project_root=project_root,
        ),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _data_block_layout_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    layout = _data_block_layout_from_action(action)
    if layout is not None:
        return layout
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            layout = _data_block_layout_from_action(raw_action)
            if layout is not None:
                return layout
    return None


def _data_block_layout_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    layout = action.get("data_block_layout")
    if isinstance(layout, dict):
        return cast(dict[str, object], layout)
    payload = action.get("payload")
    layout = payload.get("data_block_layout") if isinstance(payload, dict) else None
    if isinstance(layout, dict):
        return cast(dict[str, object], layout)
    return None


def _verify_project_data_block_layout(
    target_id: str,
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing data block layout payload"}
    key = "removed_data_block_layouts" if command_id.endswith(".remove") else "data_block_layouts"
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    layouts = manual_state.get(key) if isinstance(manual_state, dict) else None
    if not isinstance(layouts, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": f"manual {key} were not reloaded"}
    matches = [layout for layout in layouts if isinstance(layout, dict) and _data_block_layout_matches(layout, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_data_block_layout": expected,
        "matching_data_block_layouts": matches,
        "state_key": key,
    }


def _data_block_layout_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    return isinstance(expected.get("layout_id"), str) and all(actual.get(key) == value for key, value in expected.items())


def _verify_data_block_element_mutation(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _data_block_element_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_data_block_element(target_id, command_id, expected, project_root=project_root),
        _verify_projected_data_block_rendered_source(
            target_id,
            command,
            command_id,
            expected,
            durable_result,
            project_root=project_root,
        ),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _verify_data_block_type_binding_mutation(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _data_block_element_from_durable_result(durable_result)
    if command_id == "row.data_block.element.bind_type" and expected is not None:
        expected = _data_block_element_with_expected_type_binding_owner(expected, durable_result)
    if command_id == "row.data_block.element.clear_type" and expected is not None:
        expected = _data_block_element_with_expected_type_binding_cleanup(expected, durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_data_block_element(target_id, command_id, expected, project_root=project_root),
        _verify_projected_data_block_type_binding_rendered_source(
            target_id,
            command,
            command_id,
            expected,
            project_root=project_root,
        ),
        _verify_projected_data_block_type_binding_descendants(
            target_id,
            command_id,
            expected,
            project_root=project_root,
        ),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _data_block_element_with_expected_type_binding_owner(
    element: dict[str, object],
    durable_result: dict[str, object],
) -> dict[str, object]:
    binding = element.get("type_binding")
    action_id = _durable_action_id(durable_result)
    if not isinstance(binding, dict) or not isinstance(action_id, str) or not action_id:
        return element
    result = dict(element)
    owned_binding = dict(binding)
    owned_binding.setdefault("owner_action_id", action_id)
    result["type_binding"] = owned_binding
    return result


def _data_block_element_with_expected_type_binding_cleanup(
    element: dict[str, object],
    durable_result: dict[str, object],
) -> dict[str, object]:
    previous_binding = element.get("previous_type_binding")
    action_id = _durable_action_id(durable_result)
    if not isinstance(previous_binding, dict) or not isinstance(action_id, str) or not action_id:
        return element
    result = dict(element)
    cleaned_binding = dict(previous_binding)
    cleaned_binding.setdefault("cleanup_action_id", action_id)
    result["previous_type_binding"] = cleaned_binding
    return result


def _verify_custom_struct_field_mutation(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _custom_struct_field_from_durable_result(durable_result)
    if expected is not None and expected.get("source_evidence_id") is not None:
        expected = dict(expected)
        action_id = _durable_action_id(durable_result)
        if isinstance(action_id, str) and action_id:
            if command_id.endswith(".remove"):
                expected.setdefault("cleanup_action_id", action_id)
            else:
                expected.setdefault("owner_action_id", action_id)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_custom_struct_field(target_id, command_id, expected, project_root=project_root),
        _verify_projected_custom_struct_field_rendered_source(target_id, command, command_id, expected),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _custom_struct_field_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    field = _custom_struct_field_from_action(action)
    if field is not None:
        return field
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            field = _custom_struct_field_from_action(raw_action)
            if field is not None:
                return field
    return None


def _custom_struct_field_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    field = action.get("custom_struct_field")
    if isinstance(field, dict):
        return dict(cast(dict[str, object], field))
    payload = action.get("payload")
    field = payload.get("custom_struct_field") if isinstance(payload, dict) else None
    if isinstance(field, dict):
        return dict(cast(dict[str, object], field))
    return None


def _verify_project_custom_struct_field(
    target_id: str,
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing custom struct field payload"}
    state_keys = ["custom_struct_fields"]
    if command_id.endswith(".rename"):
        state_keys = ["renamed_custom_struct_fields", "custom_struct_fields"]
    elif command_id.endswith(".remove"):
        state_keys = ["removed_custom_struct_fields"]
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    matches: list[dict[str, object]] = []
    checked_keys: list[str] = []
    if isinstance(manual_state, dict):
        for key in state_keys:
            fields = manual_state.get(key)
            checked_keys.append(key)
            if not isinstance(fields, list | tuple):
                continue
            matches.extend(
                cast(dict[str, object], field)
                for field in fields
                if isinstance(field, dict) and _custom_struct_field_matches(field, expected)
            )
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_custom_struct_field": expected,
        "matching_custom_struct_fields": matches,
        "state_keys": checked_keys,
    }


def _custom_struct_field_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    required_keys = ("struct_name", "offset")
    if not all(actual.get(key) == expected.get(key) for key in required_keys):
        return False
    for key in ("name", "type", "size"):
        if key in expected and actual.get(key) != expected.get(key):
            return False
    for key in (
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
        "owner_action_id",
        "cleanup_action_id",
    ):
        if key in expected and actual.get(key) != expected.get(key):
            return False
    return True


def _data_block_element_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    element = _data_block_element_from_action(action)
    if element is not None:
        return element
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            element = _data_block_element_from_action(raw_action)
            if element is not None:
                return element
    return None


def _data_block_element_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    element = action.get("data_block_element")
    if isinstance(element, dict):
        return dict(cast(dict[str, object], element))
    payload = action.get("payload")
    element = payload.get("data_block_element") if isinstance(payload, dict) else None
    if isinstance(element, dict):
        return dict(cast(dict[str, object], element))
    return None


def _verify_project_data_block_element(
    target_id: str,
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing data block element payload"}
    key = "removed_data_block_elements" if command_id.endswith(".remove") else "data_block_elements"
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    elements = manual_state.get(key) if isinstance(manual_state, dict) else None
    if not isinstance(elements, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": f"manual {key} were not reloaded"}
    matches = [element for element in elements if isinstance(element, dict) and _data_block_element_matches(element, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_data_block_element": expected,
        "matching_data_block_elements": matches,
        "state_key": key,
    }


def _data_block_element_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    return (
        isinstance(expected.get("layout_id"), str)
        and isinstance(expected.get("offset"), int)
        and all(actual.get(key) == value for key, value in expected.items())
    )


def _verify_data_block_interpreted_ref_mutation(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _data_block_interpreted_ref_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_data_block_interpreted_ref(target_id, command_id, expected, project_root=project_root),
        _verify_projected_data_block_interpreted_ref_rendered_source(
            target_id,
            command,
            command_id,
            expected,
            project_root=project_root,
        ),
        _verify_projected_data_block_interpreted_ref_xrefs(
            target_id,
            command,
            command_id,
            expected,
            project_root=project_root,
        ),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _data_block_interpreted_ref_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    ref = _data_block_interpreted_ref_from_action(action)
    if ref is not None:
        return ref
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            ref = _data_block_interpreted_ref_from_action(raw_action)
            if ref is not None:
                return ref
    return None


def _data_block_interpreted_ref_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    ref = action.get("data_block_interpreted_ref")
    if isinstance(ref, dict):
        return cast(dict[str, object], ref)
    payload = action.get("payload")
    ref = payload.get("data_block_interpreted_ref") if isinstance(payload, dict) else None
    if isinstance(ref, dict):
        return cast(dict[str, object], ref)
    return None


def _verify_project_data_block_interpreted_ref(
    target_id: str,
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing interpreted ref payload"}
    removed = command_id.endswith(".clear_ref")
    key = "removed_data_block_interpreted_refs" if removed else "data_block_interpreted_refs"
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    refs = manual_state.get(key) if isinstance(manual_state, dict) else None
    if not isinstance(refs, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": f"manual {key} were not reloaded"}
    matches = [ref for ref in refs if isinstance(ref, dict) and _data_block_interpreted_ref_matches(ref, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_data_block_interpreted_ref": expected,
        "matching_data_block_interpreted_refs": matches,
        "state_key": key,
    }


def _project_data_block_interpreted_ref_state_match(
    target_id: str,
    command_id: str,
    expected: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object] | None:
    key = "removed_data_block_interpreted_refs" if command_id.endswith(".clear_ref") else "data_block_interpreted_refs"
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception:
        return None
    manual_state = project.manual_state
    refs = manual_state.get(key) if isinstance(manual_state, dict) else None
    if not isinstance(refs, list | tuple):
        return None
    for ref in refs:
        if isinstance(ref, dict) and _data_block_interpreted_ref_matches(ref, expected):
            return cast(dict[str, object], ref)
    return None


def _data_block_interpreted_ref_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    expected_ref_id = expected.get("data_block_ref_id") or expected.get("interpreted_ref_id")
    actual_ref_id = actual.get("data_block_ref_id") or actual.get("interpreted_ref_id")
    return (
        isinstance(expected_ref_id, str)
        and expected_ref_id == actual_ref_id
        and isinstance(expected.get("layout_id"), str)
        and isinstance(expected.get("offset"), int)
        and all(actual.get(key) == value for key, value in expected.items())
    )


def _verify_projected_data_block_interpreted_ref_rendered_source(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "missing interpreted ref payload"}
    render_expected = (
        _project_data_block_interpreted_ref_state_match(
            target_id,
            command_id,
            expected,
            project_root=project_root,
        )
        or expected
    )
    location = _data_block_render_location(target_id, command, render_expected, project_root=project_root)
    if location is None:
        return {"layer": "rendered_source", "status": "failed", "message": "interpreted ref source location missing"}
    section_index, source_offset = location
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
        return {"layer": "rendered_source", "status": "failed", "message": str(exc)}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {"layer": "rendered_source", "status": "failed", "message": "listing rows missing after reload"}
    affected_rows = _data_block_rendered_source_rows(rows, section_index, source_offset)
    affected_rendered_text = "\n".join(_data_block_rendered_source_text(row) for row in affected_rows)
    if not affected_rows:
        return {
            "layer": "rendered_source",
            "status": "failed",
            "source_offset": source_offset,
            "message": "affected listing row missing after reload",
        }
    symbol = _data_block_interpreted_ref_symbol(render_expected)
    directive = _data_block_directive_for_width(_optional_positive_int(render_expected.get("width")))
    if symbol is None or directive is None:
        return {
            "layer": "rendered_source",
            "status": "failed",
            "source_offset": source_offset,
            "message": "interpreted ref lacks supported symbolic render payload",
            "affected_rendered_text": affected_rendered_text,
        }
    has_symbol = _rendered_source_contains_token(affected_rendered_text, symbol)
    has_directive = _rendered_source_contains_token(affected_rendered_text, directive)
    removed = command_id.endswith(".clear_ref")
    return {
        "layer": "rendered_source",
        "status": "passed" if (not has_symbol if removed else has_symbol and has_directive) else "failed",
        "source_offset": source_offset,
        "expected_symbol": symbol,
        "expected_directive": directive,
        "matched_symbol": has_symbol,
        "matched_directive": has_directive,
        "affected_rendered_text": affected_rendered_text,
    }


def _verify_projected_data_block_interpreted_ref_xrefs(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "xref_projection", "status": "failed", "message": "missing interpreted ref payload"}
    render_expected = (
        _project_data_block_interpreted_ref_state_match(
            target_id,
            command_id,
            expected,
            project_root=project_root,
        )
        or expected
    )
    mode = render_expected.get("xref_generation_mode") or "bidirectional"
    if mode == "none":
        return {"layer": "xref_projection", "status": "passed", "message": "xref generation disabled"}
    location = _data_block_render_location(target_id, command, render_expected, project_root=project_root)
    if location is None:
        return {"layer": "xref_projection", "status": "failed", "message": "interpreted ref source location missing"}
    section_index, source_offset = location
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
        return {"layer": "xref_projection", "status": "failed", "message": str(exc)}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {"layer": "xref_projection", "status": "failed", "message": "listing rows missing after reload"}
    affected_rows = _data_block_rendered_source_rows(rows, section_index, source_offset)
    refs = [
        ref
        for row in affected_rows
        for ref in _mapping_sequence(row.get("runtime_address_refs") or row.get("runtimeAddressRefs"))
    ]
    expected_ref_id = render_expected.get("data_block_ref_id") or render_expected.get("interpreted_ref_id")
    target_hunk = render_expected.get("target_hunk")
    target_offset = render_expected.get("target_offset")
    layout_id = render_expected.get("layout_id")
    element_offset = render_expected.get("offset")
    matching_refs = [
        ref
        for ref in refs
        if ref.get("owner_kind") == "data_block_interpreted_ref"
        and ref.get("owner_id") == expected_ref_id
        and ref.get("owner_layout_id") == layout_id
        and ref.get("owner_element_offset") == element_offset
        and ref.get("target_section_index") == target_hunk
        and ref.get("target_offset") == target_offset
    ]
    removed = command_id.endswith(".clear_ref")
    return {
        "layer": "xref_projection",
        "status": "passed" if (not matching_refs if removed else bool(matching_refs)) else "failed",
        "source_offset": source_offset,
        "expected_owner_id": expected_ref_id,
        "expected_target_hunk": target_hunk,
        "expected_target_offset": target_offset,
        "matching_runtime_address_refs": matching_refs,
        "runtime_address_refs": refs,
    }


def _mapping_sequence(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list | tuple):
        return []
    return [cast(dict[str, object], item) for item in value if isinstance(item, dict)]


def _data_block_interpreted_ref_symbol(expected: dict[str, object]) -> str | None:
    target_hunk = expected.get("target_hunk")
    target_offset = expected.get("target_offset")
    source_value = expected.get("source_value")
    target_locator = expected.get("target_locator")
    width = expected.get("width")
    if expected.get("reference_kind") != "absolute":
        return None
    if not isinstance(width, int) or width not in {1, 2, 4}:
        return None
    if not isinstance(target_hunk, int) or target_hunk < 0:
        return None
    if not isinstance(target_offset, int) or target_offset < 0:
        return None
    if not isinstance(source_value, int) or source_value != target_offset or source_value >= (1 << (width * 8)):
        return None
    if not isinstance(target_locator, dict):
        return None
    if target_locator.get("hunk") != target_hunk or target_locator.get("offset") != target_offset:
        return None
    return f"dblk_ref_h{target_hunk}_{target_offset:08X}"


def _verify_projected_data_block_rendered_source(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    expected: dict[str, object] | None,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "missing data block payload"}
    location = _data_block_render_location(target_id, command, expected, project_root=project_root)
    if location is None:
        metadata = _verify_projection_metadata(command, durable_result)
        metadata["layer"] = "rendered_source"
        metadata["message"] = metadata.get("message", "verified affected locator without source offset")
        return metadata
    section_index, source_offset = location
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
        return {"layer": "rendered_source", "status": "failed", "message": str(exc)}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {"layer": "rendered_source", "status": "failed", "message": "listing rows missing after reload"}
    render_expected = _project_data_block_element_state_match(
        target_id,
        command_id,
        expected,
        project_root=project_root,
    ) or expected
    expected_tokens = _data_block_expected_render_tokens(render_expected)
    rendered_text = "\n".join(
        " ".join(str(row.get(key) or "") for key in ("label", "text", "operand_text", "source_text"))
        for row in rows
        if isinstance(row, dict)
    )
    affected_rows = _data_block_rendered_source_rows(rows, section_index, source_offset)
    affected_rendered_text = "\n".join(_data_block_rendered_source_text(row) for row in affected_rows)
    if not affected_rows:
        return {
            "layer": "rendered_source",
            "status": "failed",
            "source_offset": source_offset,
            "message": "affected listing row missing after reload",
            "rendered_text": rendered_text,
        }
    if command_id.endswith(".remove"):
        stale_tokens = [
            token
            for token in _data_block_stale_removal_tokens(render_expected)
            if token and _rendered_source_contains_token(affected_rendered_text, token)
        ]
        restore_tokens = _data_block_removal_restore_tokens(render_expected)
        matched_restore_tokens = [
            token for token in restore_tokens if _rendered_source_contains_token(affected_rendered_text, token)
        ]
        status = "failed" if stale_tokens else "passed"
        if restore_tokens and len(matched_restore_tokens) != len(restore_tokens):
            status = "failed"
        if not expected_tokens and not restore_tokens:
            status = "failed"
        return {
            "layer": "rendered_source",
            "status": status,
            "source_offset": source_offset,
            "stale_tokens": stale_tokens,
            "expected_restore_tokens": restore_tokens,
            "matched_restore_tokens": matched_restore_tokens,
            "affected_rendered_text": affected_rendered_text,
            "rendered_text": rendered_text,
        }
    if not expected_tokens:
        metadata = _verify_projection_metadata(command, durable_result)
        metadata["layer"] = "rendered_source"
        metadata["source_offset"] = source_offset
        metadata["message"] = metadata.get("message", "verified affected locator; no stable rendered token in payload")
        return metadata
    matched_tokens = [token for token in expected_tokens if _rendered_source_contains_token(affected_rendered_text, token)]
    return {
        "layer": "rendered_source",
        "status": "passed" if len(matched_tokens) == len(expected_tokens) else "failed",
        "source_offset": source_offset,
        "expected_tokens": expected_tokens,
        "matched_tokens": matched_tokens,
        "affected_rendered_text": affected_rendered_text,
        "rendered_text": rendered_text,
    }


def _verify_projected_data_block_type_binding_rendered_source(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "missing data block type-binding payload"}
    render_expected = _project_data_block_element_state_match(
        target_id,
        command_id,
        expected,
        project_root=project_root,
    ) or expected
    location = _data_block_render_location(target_id, command, render_expected, project_root=project_root)
    if location is None:
        return {"layer": "rendered_source", "status": "failed", "message": "data block type-binding source location missing"}
    section_index, source_offset = location
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
        return {"layer": "rendered_source", "status": "failed", "message": str(exc)}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {"layer": "rendered_source", "status": "failed", "message": "listing rows missing after reload"}
    affected_rows = _data_block_rendered_source_rows(rows, section_index, source_offset)
    rendered_text = "\n".join(
        " ".join(str(row.get(key) or "") for key in ("label", "text", "operand_text", "source_text"))
        for row in rows
        if isinstance(row, dict)
    )
    affected_rendered_text = "\n".join(_data_block_rendered_source_text(row) for row in affected_rows)
    if not affected_rows:
        return {
            "layer": "rendered_source",
            "status": "failed",
            "source_offset": source_offset,
            "message": "affected listing row missing after reload",
            "rendered_text": rendered_text,
        }
    expected_tokens = _data_block_type_binding_tokens(render_expected)
    if command_id.endswith(".clear_type"):
        if not expected_tokens:
            return {
                "layer": "rendered_source",
                "status": "failed",
                "source_offset": source_offset,
                "message": "clear_type requires previous type-binding render token",
                "affected_rendered_text": affected_rendered_text,
                "rendered_text": rendered_text,
            }
        stale_tokens = [
            token for token in expected_tokens if _rendered_source_contains_token(affected_rendered_text, token)
        ]
        return {
            "layer": "rendered_source",
            "status": "passed" if not stale_tokens else "failed",
            "source_offset": source_offset,
            "stale_tokens": stale_tokens,
            "affected_rendered_text": affected_rendered_text,
            "rendered_text": rendered_text,
        }
    matched_tokens = [token for token in expected_tokens if _rendered_source_contains_token(affected_rendered_text, token)]
    return {
        "layer": "rendered_source",
        "status": "passed" if expected_tokens and len(matched_tokens) == len(expected_tokens) else "failed",
        "source_offset": source_offset,
        "expected_tokens": expected_tokens,
        "matched_tokens": matched_tokens,
        "affected_rendered_text": affected_rendered_text,
        "rendered_text": rendered_text,
    }


def _verify_projected_data_block_type_binding_descendants(
    target_id: str,
    command_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "type_binding_descendants", "status": "failed", "message": "missing data block type-binding payload"}
    binding = expected.get("previous_type_binding") if command_id.endswith(".clear_type") else expected.get("type_binding")
    if not isinstance(binding, dict):
        return {"layer": "type_binding_descendants", "status": "failed", "message": "missing type binding state"}
    binding_id = binding.get("type_binding_id")
    if not isinstance(binding_id, str) or not binding_id:
        return {"layer": "type_binding_descendants", "status": "failed", "message": "missing type binding id"}
    try:
        target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
        metadata = effective_target_metadata(target_dir)
    except Exception as exc:
        return {"layer": "type_binding_descendants", "status": "failed", "message": str(exc)}
    entities = metadata.seeded_entities if metadata is not None else ()
    descendants = [
        {
            "hunk": entity.hunk,
            "addr": entity.addr,
            "end": entity.end,
            "name": entity.name,
            "struct_name": entity.struct_name,
            "field_name": entity.field_name,
            "value_domain": entity.value_domain,
            "source_id": entity.source_id,
            "source_locator": entity.source_locator,
        }
        for entity in entities
        if entity.source_id == "manual_action_log" and entity.source_locator == binding_id
    ]
    cleared = command_id.endswith(".clear_type")
    return {
        "layer": "type_binding_descendants",
        "status": "passed" if (not descendants if cleared else bool(descendants)) else "failed",
        "type_binding_id": binding_id,
        "matching_seeded_entities": descendants,
    }


def _data_block_type_binding_tokens(expected: dict[str, object]) -> list[str]:
    binding = expected.get("type_binding")
    if not isinstance(binding, dict):
        binding = expected.get("previous_type_binding")
    if not isinstance(binding, dict):
        return []
    tokens = [
        value
        for value in (
            binding.get("bound_type_id"),
            binding.get("bound_domain_id"),
        )
        if isinstance(value, str) and value
    ]
    return list(dict.fromkeys(tokens))


def _verify_projected_custom_struct_field_rendered_source(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    expected: dict[str, object] | None,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "missing custom struct field payload"}
    location = _custom_struct_field_render_location(command)
    if location is None:
        return {"layer": "rendered_source", "status": "failed", "message": "custom struct field source location missing"}
    section_index, source_offset = location
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {
                "section_index": [str(section_index)],
                "source_offset": [str(source_offset)],
                "before": ["2"],
                "after": ["2"],
            },
        )
    except Exception as exc:
        return {"layer": "rendered_source", "status": "failed", "message": str(exc)}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {"layer": "rendered_source", "status": "failed", "message": "listing rows missing after reload"}
    affected_rows = _data_block_rendered_source_rows(rows, section_index, source_offset)
    rendered_text = "\n".join(
        " ".join(str(row.get(key) or "") for key in ("label", "text", "operand_text", "source_text"))
        for row in rows
        if isinstance(row, dict)
    )
    affected_rendered_text = "\n".join(_data_block_rendered_source_text(row) for row in affected_rows)
    if not affected_rows:
        return {
            "layer": "rendered_source",
            "status": "failed",
            "source_offset": source_offset,
            "message": "affected listing row missing after reload",
            "rendered_text": rendered_text,
        }
    matching_accesses = [
        access
        for row in affected_rows
        for access in _mapping_sequence(row.get("typed_accesses"))
        if _custom_struct_field_render_access_matches(access, expected, command)
    ]
    stale_name = expected.get("name") if isinstance(expected.get("name"), str) else None
    if command_id.endswith(".remove"):
        stale_tokens = (
            [stale_name]
            if stale_name and _rendered_source_contains_token(affected_rendered_text, stale_name)
            else []
        )
        return {
            "layer": "rendered_source",
            "status": "passed" if not matching_accesses and not stale_tokens else "failed",
            "source_offset": source_offset,
            "stale_tokens": stale_tokens,
            "matching_typed_accesses": matching_accesses,
            "affected_rendered_text": affected_rendered_text,
            "rendered_text": rendered_text,
        }
    if command_id.endswith(".rename"):
        previous_name = _custom_struct_field_previous_name(command, expected)
        if not previous_name:
            expected_tokens = [token for token in (stale_name,) if isinstance(token, str) and token]
            matched_tokens = [
                token for token in expected_tokens if _rendered_source_contains_token(affected_rendered_text, token)
            ]
            return {
                "layer": "rendered_source",
                "status": "failed",
                "source_offset": source_offset,
                "message": "previous custom struct field name missing for rename proof",
                "expected_tokens": expected_tokens,
                "matched_tokens": matched_tokens,
                "stale_previous_name": previous_name,
                "stale_tokens": [],
                "stale_typed_accesses": [],
                "matching_typed_accesses": matching_accesses,
                "affected_rendered_text": affected_rendered_text,
                "rendered_text": rendered_text,
            }
        previous_expected = dict(expected)
        previous_expected["name"] = previous_name
        stale_accesses = [
            access
            for row in affected_rows
            for access in _mapping_sequence(row.get("typed_accesses"))
            if _custom_struct_field_render_access_matches(access, previous_expected, command)
        ]
        stale_tokens = (
            [previous_name]
            if previous_name
            and previous_name != stale_name
            and _rendered_source_contains_token(affected_rendered_text, previous_name)
            else []
        )
        expected_tokens = [token for token in (stale_name,) if isinstance(token, str) and token]
        matched_tokens = [
            token for token in expected_tokens if _rendered_source_contains_token(affected_rendered_text, token)
        ]
        return {
            "layer": "rendered_source",
            "status": (
                "passed"
                if matching_accesses and len(matched_tokens) == len(expected_tokens) and not stale_accesses and not stale_tokens
                else "failed"
            ),
            "source_offset": source_offset,
            "expected_tokens": expected_tokens,
            "matched_tokens": matched_tokens,
            "stale_previous_name": previous_name,
            "stale_tokens": stale_tokens,
            "stale_typed_accesses": stale_accesses,
            "matching_typed_accesses": matching_accesses,
            "affected_rendered_text": affected_rendered_text,
            "rendered_text": rendered_text,
        }
    expected_tokens = [token for token in (stale_name,) if isinstance(token, str) and token]
    matched_tokens = [
        token for token in expected_tokens if _rendered_source_contains_token(affected_rendered_text, token)
    ]
    return {
        "layer": "rendered_source",
        "status": "passed" if matching_accesses and len(matched_tokens) == len(expected_tokens) else "failed",
        "source_offset": source_offset,
        "expected_tokens": expected_tokens,
        "matched_tokens": matched_tokens,
        "matching_typed_accesses": matching_accesses,
        "affected_rendered_text": affected_rendered_text,
        "rendered_text": rendered_text,
    }


def _custom_struct_field_previous_name(command: dict[str, object], expected: dict[str, object]) -> str | None:
    context = command.get("context")
    parameters = command.get("parameters")
    for source in (context, parameters):
        if not isinstance(source, dict):
            continue
        for key in ("previous_name", "field_name"):
            value = source.get(key)
            if isinstance(value, str) and value and value != expected.get("name"):
                return value
    return None


def _custom_struct_field_render_location(command: dict[str, object]) -> tuple[int, int] | None:
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    if not isinstance(locator, dict):
        return None
    section = locator.get("section_index")
    offset = locator.get("start_offset")
    if isinstance(section, int) and isinstance(offset, int):
        return section, offset
    return None


def _custom_struct_field_render_access_matches(
    access: dict[str, object],
    expected: dict[str, object],
    command: dict[str, object],
) -> bool:
    context = command.get("context")
    operand_index = context.get("operand_index") if isinstance(context, dict) else None
    if isinstance(operand_index, int) and access.get("operand_index") != operand_index:
        return False
    offset = expected.get("offset")
    if isinstance(offset, int) and access.get("field_offset") != offset and access.get("displacement") != offset:
        return False
    struct_name = expected.get("struct_name")
    if isinstance(struct_name, str) and struct_name:
        struct_names = {
            value
            for value in (
                access.get("owner_struct_name"),
                access.get("refined_struct_name"),
                access.get("root_struct_name"),
                access.get("container_struct_name"),
            )
            if isinstance(value, str)
        }
        if struct_names and struct_name not in struct_names:
            return False
    name = expected.get("name")
    if isinstance(name, str) and name:
        return name in {access.get("field_name"), access.get("field_expr")}
    return True


def _data_block_render_location(
    target_id: str,
    command: dict[str, object],
    expected: dict[str, object],
    *,
    project_root: Path,
) -> tuple[int, int] | None:
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    if not isinstance(locator, dict) and isinstance(context, dict):
        locators = context.get("locators")
        locator = locators[0] if isinstance(locators, list) and locators and isinstance(locators[0], dict) else None
    if isinstance(locator, dict):
        section = locator.get("section_index")
        offset = locator.get("start_offset")
        if isinstance(section, int) and isinstance(offset, int):
            return section, offset
    hunk = expected.get("hunk")
    source_start = expected.get("source_start")
    if isinstance(hunk, int) and isinstance(source_start, int):
        return hunk, source_start
    layout_id = expected.get("layout_id")
    element_offset = expected.get("offset")
    if isinstance(layout_id, str) and isinstance(element_offset, int):
        layout = _project_data_block_layout_by_id(target_id, layout_id, project_root=project_root)
        if layout is not None:
            hunk = layout.get("hunk")
            source_start = layout.get("source_start")
            if isinstance(hunk, int) and isinstance(source_start, int):
                return hunk, source_start + element_offset
    return None


def _project_data_block_layout_by_id(
    target_id: str,
    layout_id: str,
    *,
    project_root: Path,
) -> dict[str, object] | None:
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception:
        return None
    manual_state = project.manual_state
    layouts = manual_state.get("data_block_layouts") if isinstance(manual_state, dict) else None
    if not isinstance(layouts, list | tuple):
        return None
    for layout in layouts:
        if isinstance(layout, dict) and layout.get("layout_id") == layout_id:
            return cast(dict[str, object], layout)
    return None


def _project_data_block_element_state_match(
    target_id: str,
    command_id: str,
    expected: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object] | None:
    key = "removed_data_block_elements" if command_id.endswith(".remove") else "data_block_elements"
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception:
        return None
    manual_state = project.manual_state
    elements = manual_state.get(key) if isinstance(manual_state, dict) else None
    if not isinstance(elements, list | tuple):
        return None
    for element in elements:
        if isinstance(element, dict) and _data_block_element_matches(element, expected):
            return cast(dict[str, object], element)
    return None


def _data_block_rendered_source_rows(
    rows: list[object],
    section_index: int,
    source_offset: int,
) -> list[dict[str, object]]:
    affected: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        locator = row.get("locator")
        row_locator = locator if isinstance(locator, dict) else row
        if _row_covers_source_location(row, cast(dict[str, object], row_locator), section_index, source_offset):
            affected.append(cast(dict[str, object], row))
    return affected


def _data_block_rendered_source_text(row: dict[str, object]) -> str:
    return " ".join(str(row.get(key) or "") for key in ("label", "text", "operand_text", "source_text"))


def _data_block_expected_render_tokens(expected: dict[str, object]) -> list[str]:
    tokens: list[str] = []
    for key in ("name", "role"):
        value = expected.get(key)
        if isinstance(value, str) and value:
            tokens.append(value)
    directive = _data_block_expected_directive(expected)
    if directive is not None:
        tokens.append(directive)
    representation = expected.get("representation")
    if representation == "character":
        tokens.append("'")
    elif representation == "hex":
        tokens.append("$")
    elif representation == "binary":
        tokens.append("%")
    return list(dict.fromkeys(tokens))


def _data_block_removal_restore_tokens(expected: dict[str, object]) -> list[str]:
    tokens: list[str] = []
    removal_state = expected.get("removal_state")
    width = _optional_positive_int(expected.get("width"))
    if removal_state in {"raw", "gap"} and width is not None:
        tokens.append("dc")
    return tokens


def _data_block_stale_removal_tokens(expected: dict[str, object]) -> list[str]:
    tokens: list[str] = []
    for key in ("name", "role"):
        value = expected.get(key)
        if isinstance(value, str) and value:
            tokens.append(value)
    representation = expected.get("representation")
    if representation == "character":
        tokens.append("'")
    elif representation == "binary":
        tokens.append("%")
    return list(dict.fromkeys(tokens))


def _data_block_expected_directive(expected: dict[str, object]) -> str | None:
    kind = expected.get("kind")
    if kind == "padding":
        return "dcb.b"
    if kind == "gap":
        return "dc.b"
    if kind == "array":
        stride = _optional_positive_int(expected.get("array_stride"))
        if stride is not None:
            return _data_block_directive_for_width(stride)
        count = _optional_positive_int(expected.get("array_count"))
        width = _optional_positive_int(expected.get("width"))
        if count is not None and width is not None and width % count == 0:
            return _data_block_directive_for_width(width // count)
        return "dc.b"
    if kind == "scalar":
        return _data_block_directive_for_width(_optional_positive_int(expected.get("width")))
    return None


def _data_block_directive_for_width(width: int | None) -> str | None:
    if width == 1:
        return "dc.b"
    if width == 2:
        return "dc.w"
    if width == 4:
        return "dc.l"
    return "dc.b" if width is not None else None


def _optional_positive_int(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _rendered_source_contains_token(rendered_text: str, token: str) -> bool:
    if token == "dc":
        return re.search(r"(?<![A-Za-z0-9_.])dcb?\.[bwl](?![A-Za-z0-9_.])", rendered_text, re.IGNORECASE) is not None
    if token.startswith(("dc", "dcb")):
        return re.search(rf"(?<![A-Za-z0-9_.]){re.escape(token)}(?![A-Za-z0-9_.])", rendered_text, re.IGNORECASE) is not None
    return token in rendered_text


def _verify_seeded_item_suppression_mutation(
    target_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _suppressed_seeded_item_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_suppressed_seeded_item(target_id, expected, project_root=project_root),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _suppressed_seeded_item_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    application = durable_result.get("application")
    local_effects = application.get("local_effects") if isinstance(application, dict) else None
    if isinstance(local_effects, list):
        for effect in local_effects:
            if not isinstance(effect, dict) or effect.get("kind") != "seeded_item_suppression":
                continue
            item = effect.get("suppressed_seeded_item")
            if isinstance(item, dict):
                return cast(dict[str, object], item)
    action = durable_result.get("action")
    item = _suppressed_seeded_item_from_action(action)
    if item is not None:
        return item
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            item = _suppressed_seeded_item_from_action(raw_action)
            if item is not None:
                return item
    return None


def _suppressed_seeded_item_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    item = action.get("suppressed_seeded_item")
    if isinstance(item, dict):
        return cast(dict[str, object], item)
    payload = action.get("payload")
    item = payload.get("suppressed_seeded_item") if isinstance(payload, dict) else None
    if isinstance(item, dict):
        return cast(dict[str, object], item)
    return None


def _verify_project_suppressed_seeded_item(
    target_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing suppressed seeded item payload"}
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    suppressed = manual_state.get("suppressed_seeded_items") if isinstance(manual_state, dict) else None
    if isinstance(suppressed, dict):
        items = [item for item in suppressed.values() if isinstance(item, dict)]
    elif isinstance(suppressed, list | tuple):
        items = [item for item in suppressed if isinstance(item, dict)]
    else:
        return {"layer": "semantic_reload", "status": "failed", "message": "suppressed seeded items were not reloaded"}
    matches = [item for item in items if _suppressed_seeded_item_matches(item, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_suppressed_seeded_item": expected,
        "matching_suppressed_seeded_items": matches,
    }


def _suppressed_seeded_item_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    return all(key in expected and actual.get(key) == expected.get(key) for key in ("kind", "hunk", "addr"))


def _verify_manual_seed_mutation(
    target_id: str,
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected_seeds = _manual_seeds_from_durable_result(durable_result)
    removed_seed_ids = _manual_seed_removals_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_manual_seed_state(
            target_id,
            command_id,
            expected_seeds,
            removed_seed_ids,
            project_root=project_root,
        ),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _manual_seeds_from_durable_result(durable_result: dict[str, object]) -> list[dict[str, object]]:
    seeds: list[dict[str, object]] = []
    action = durable_result.get("action")
    seed = _manual_seed_from_action(action)
    if seed is not None:
        seeds.append(seed)
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            seed = _manual_seed_from_action(raw_action)
            if seed is not None:
                seeds.append(seed)
    return seeds


def _manual_seed_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    seed = action.get("seed")
    if isinstance(seed, dict):
        return cast(dict[str, object], seed)
    payload = action.get("payload")
    seed = payload.get("seed") if isinstance(payload, dict) else None
    if isinstance(seed, dict):
        return cast(dict[str, object], seed)
    return None


def _manual_seed_removals_from_durable_result(durable_result: dict[str, object]) -> list[str]:
    seed_ids: list[str] = []
    action = durable_result.get("action")
    seed_id = _manual_seed_removal_from_action(action)
    if seed_id is not None:
        seed_ids.append(seed_id)
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            seed_id = _manual_seed_removal_from_action(raw_action)
            if seed_id is not None:
                seed_ids.append(seed_id)
    return seed_ids


def _manual_seed_removal_from_action(action: object) -> str | None:
    if not isinstance(action, dict):
        return None
    seed_id = action.get("seed_id")
    if isinstance(seed_id, str) and seed_id:
        return seed_id
    payload = action.get("payload")
    seed_id = payload.get("seed_id") if isinstance(payload, dict) else None
    if isinstance(seed_id, str) and seed_id:
        return seed_id
    return None


def _verify_project_manual_seed_state(
    target_id: str,
    command_id: str,
    expected_seeds: list[dict[str, object]],
    removed_seed_ids: list[str],
    *,
    project_root: Path,
) -> dict[str, object]:
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    seeds = manual_state.get("seeds") if isinstance(manual_state, dict) else None
    if not isinstance(seeds, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual seeds were not reloaded"}
    seed_items = [seed for seed in seeds if isinstance(seed, dict)]
    if command_id in {"review.seed.remove", "data_symbol.remove"}:
        if not removed_seed_ids:
            return {"layer": "semantic_reload", "status": "failed", "message": "missing removed manual seed id payload"}
        remaining = [seed for seed in seed_items if seed.get("seed_id") in set(removed_seed_ids)]
        return {
            "layer": "semantic_reload",
            "status": "passed" if not remaining else "failed",
            "removed_seed_ids": removed_seed_ids,
            "remaining_manual_seeds": remaining,
        }
    if not expected_seeds:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing manual seed payload"}
    matches = [
        expected
        for expected in expected_seeds
        if any(_manual_seed_matches(actual, expected) for actual in seed_items)
    ]
    return {
        "layer": "semantic_reload",
        "status": "passed" if len(matches) == len(expected_seeds) else "failed",
        "expected_manual_seeds": expected_seeds,
        "matching_manual_seeds": matches,
    }


def _manual_seed_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    return "seed_id" in expected and all(actual.get(key) == value for key, value in expected.items())


def _verify_manual_label_mutation(
    target_id: str,
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected_labels = _manual_labels_from_durable_result(durable_result)
    removed_label_ids = _manual_label_removals_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_manual_label_state(
            target_id,
            command_id,
            expected_labels,
            removed_label_ids,
            project_root=project_root,
        ),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _manual_labels_from_durable_result(durable_result: dict[str, object]) -> list[dict[str, object]]:
    labels: list[dict[str, object]] = []
    action = durable_result.get("action")
    label = _manual_label_from_action(action)
    if label is not None:
        labels.append(label)
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            label = _manual_label_from_action(raw_action)
            if label is not None:
                labels.append(label)
    return labels


def _manual_label_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    label = action.get("label")
    if isinstance(label, dict):
        return cast(dict[str, object], label)
    payload = action.get("payload")
    if isinstance(payload, dict):
        label = payload.get("label")
        if isinstance(label, dict):
            return cast(dict[str, object], label)
        if isinstance(payload.get("label_id"), str):
            return {
                key: payload[key]
                for key in ("label_id", "name", "scope", "owner_id", "owner_label_id")
                if key in payload
            }
    if isinstance(action.get("label_id"), str):
        return {key: action[key] for key in ("label_id", "name", "scope", "owner_id", "owner_label_id") if key in action}
    return None


def _manual_label_removals_from_durable_result(durable_result: dict[str, object]) -> list[str]:
    label_ids: list[str] = []
    action = durable_result.get("action")
    label_id = _manual_label_removal_from_action(action)
    if label_id is not None:
        label_ids.append(label_id)
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            label_id = _manual_label_removal_from_action(raw_action)
            if label_id is not None:
                label_ids.append(label_id)
    return label_ids


def _manual_label_removal_from_action(action: object) -> str | None:
    if not isinstance(action, dict):
        return None
    label_id = action.get("label_id")
    if isinstance(label_id, str) and label_id:
        return label_id
    payload = action.get("payload")
    label_id = payload.get("label_id") if isinstance(payload, dict) else None
    if isinstance(label_id, str) and label_id:
        return label_id
    return None


def _verify_project_manual_label_state(
    target_id: str,
    command_id: str,
    expected_labels: list[dict[str, object]],
    removed_label_ids: list[str],
    *,
    project_root: Path,
) -> dict[str, object]:
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    labels = manual_state.get("labels") if isinstance(manual_state, dict) else None
    if not isinstance(labels, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual labels were not reloaded"}
    label_items = [label for label in labels if isinstance(label, dict)]
    if command_id == "review.label.remove":
        if not removed_label_ids:
            return {"layer": "semantic_reload", "status": "failed", "message": "missing removed manual label id payload"}
        remaining = [label for label in label_items if label.get("label_id") in set(removed_label_ids)]
        return {
            "layer": "semantic_reload",
            "status": "passed" if not remaining else "failed",
            "removed_label_ids": removed_label_ids,
            "remaining_manual_labels": remaining,
        }
    if not expected_labels:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing manual label payload"}
    matches = [
        expected
        for expected in expected_labels
        if any(_manual_label_matches(actual, expected) for actual in label_items)
    ]
    return {
        "layer": "semantic_reload",
        "status": "passed" if len(matches) == len(expected_labels) else "failed",
        "expected_manual_labels": expected_labels,
        "matching_manual_labels": matches,
    }


def _manual_label_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    if "label_id" not in expected:
        return False
    for key, value in expected.items():
        if key in {"owner_id", "owner_label_id"}:
            actual_owner = actual.get("owner_id") or actual.get("owner_label_id")
            if actual_owner != value:
                return False
            continue
        if actual.get(key) != value:
            return False
    return True


def _verify_execution_view_mutation(
    target_id: str,
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _execution_view_from_durable_result(durable_result)
    removed = command_id == "target.execution_view.remove"
    if expected is not None:
        expected = _execution_view_with_expected_action_id(expected, durable_result, removed=removed)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_execution_view(target_id, expected, removed=removed, project_root=project_root),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _execution_view_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    application = durable_result.get("application")
    local_effects = application.get("local_effects") if isinstance(application, dict) else None
    if isinstance(local_effects, list):
        for effect in local_effects:
            if not isinstance(effect, dict) or effect.get("kind") not in {"execution_view", "execution_view_remove"}:
                continue
            view = effect.get("execution_view")
            if isinstance(view, dict):
                return cast(dict[str, object], view)
    action = durable_result.get("action")
    view = _execution_view_from_action(action)
    if view is not None:
        return view
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            view = _execution_view_from_action(raw_action)
            if view is not None:
                return view
    return None


def _execution_view_with_expected_action_id(
    view: dict[str, object],
    durable_result: dict[str, object],
    *,
    removed: bool,
) -> dict[str, object]:
    action_id = _durable_action_id(durable_result)
    if not isinstance(action_id, str) or not action_id:
        return view
    result = dict(view)
    result.setdefault("cleanup_action_id" if removed else "owner_action_id", action_id)
    return result


def _execution_view_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    view = action.get("execution_view")
    if isinstance(view, dict):
        return cast(dict[str, object], view)
    payload = action.get("payload")
    view = payload.get("execution_view") if isinstance(payload, dict) else None
    if isinstance(view, dict):
        return cast(dict[str, object], view)
    return None


def _verify_project_execution_view(
    target_id: str,
    expected: dict[str, object] | None,
    *,
    removed: bool,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing execution view payload"}
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    key = "removed_execution_views" if removed else "execution_views"
    views = manual_state.get(key) if isinstance(manual_state, dict) else None
    if not isinstance(views, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": f"manual {key} were not reloaded"}
    matches = [view for view in views if isinstance(view, dict) and _execution_view_matches(view, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_execution_view": expected,
        "matching_execution_views": matches,
        "removed": removed,
    }


def _execution_view_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    for key in ("source_start", "source_end", "base_addr"):
        if key not in expected or actual.get(key) != expected.get(key):
            return False
    for key in ("name", "comment", "owner_action_id", "cleanup_action_id"):
        if key in expected and actual.get(key) != expected.get(key):
            return False
    return True


def _verify_semantic_hint_mutation(
    target_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _semantic_hint_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_semantic_hint(target_id, expected, project_root=project_root),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _semantic_hint_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    application = durable_result.get("application")
    local_effects = application.get("local_effects") if isinstance(application, dict) else None
    if isinstance(local_effects, list):
        for effect in local_effects:
            if not isinstance(effect, dict) or effect.get("kind") != "semantic_hint":
                continue
            hint = effect.get("semantic_hint")
            if isinstance(hint, dict):
                return cast(dict[str, object], hint)
    action = durable_result.get("action")
    hint = _semantic_hint_from_action(action)
    if hint is not None:
        return hint
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            hint = _semantic_hint_from_action(raw_action)
            if hint is not None:
                return hint
    return None


def _semantic_hint_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    hint = action.get("semantic_hint")
    if isinstance(hint, dict):
        return cast(dict[str, object], hint)
    payload = action.get("payload")
    hint = payload.get("semantic_hint") if isinstance(payload, dict) else None
    if isinstance(hint, dict):
        return cast(dict[str, object], hint)
    return None


def _verify_project_semantic_hint(
    target_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing semantic hint payload"}
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    semantic_hints = manual_state.get("semantic_hints") if isinstance(manual_state, dict) else None
    if not isinstance(semantic_hints, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual semantic hints were not reloaded"}
    matches = [
        hint
        for hint in semantic_hints
        if isinstance(hint, dict) and _semantic_hint_matches(hint, expected)
    ]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_semantic_hint": expected,
        "matching_semantic_hints": matches,
    }


def _semantic_hint_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    return all(
        key in expected and actual.get(key) == expected.get(key)
        for key in ("domain", "symbol", "value", "hunk", "addr", "element_kind")
    )


def _verify_projected_data_symbol_name(target_id: str, command: dict[str, object]) -> dict[str, object]:
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    parameters = command.get("parameters")
    expected = parameters.get("name") if isinstance(parameters, dict) else None
    if not isinstance(locator, dict) or not isinstance(expected, str):
        return {"layer": "projection", "status": "failed", "message": "missing locator or expected data symbol name"}
    section = locator.get("section_index")
    offset = locator.get("start_offset")
    query = (
        {"section_index": [str(section)], "source_offset": [str(offset)], "before": ["8"], "after": ["24"]}
        if isinstance(section, int) and isinstance(offset, int)
        else {"start": ["0"], "count": [str(_LISTING_COMMENT_SEARCH_ROW_COUNT)]}
    )
    try:
        listing = server.route_request("GET", f"/api/projects/{target_id}/listing", query)
    except Exception as exc:
        return {"layer": "projection", "status": "failed", "message": str(exc)}
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return {"layer": "projection", "status": "failed", "message": "listing rows missing after reload"}
    row_key = locator.get("row_key")
    section_int = section if isinstance(section, int) else None
    offset_int = offset if isinstance(offset, int) else None
    checked_rows: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_text = row.get("text")
        row_label = row.get("label")
        row_symbol = row.get("symbol")
        if row.get("row_key") == row_key or (
            section_int is not None and offset_int is not None and _row_covers_source_location(row, locator, section_int, offset_int)
        ):
            matched = row_label == expected or row_symbol == expected or (isinstance(row_text, str) and expected in row_text)
            checked_rows.append(
                {
                    "row_key": row.get("row_key"),
                    "actual_label": row_label,
                    "actual_symbol": row_symbol,
                    "actual_text": row_text,
                }
            )
            if matched:
                return {
                    "layer": "projection",
                    "status": "passed",
                    "row_key": row.get("row_key"),
                    "expected_data_symbol_name": expected,
                    "actual_label": row_label,
                    "actual_symbol": row_symbol,
                    "actual_text": row_text,
                }
    if checked_rows:
        return {
            "layer": "projection",
            "status": "failed",
            "expected_data_symbol_name": expected,
            "checked_rows": checked_rows,
        }
    return {"layer": "projection", "status": "failed", "message": "data symbol row missing after reload"}


def _verify_library_base_register_seed_mutation(
    target_id: str,
    command: dict[str, object],
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _register_seed_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_library_base_register_seed(target_id, command, expected, project_root=project_root),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _register_seed_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    seed = _register_seed_from_action(action)
    if seed is not None:
        return seed
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            seed = _register_seed_from_action(raw_action)
            if seed is not None:
                return seed
    return None


def _register_seed_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    seed = action.get("register_seed")
    if isinstance(seed, dict):
        return cast(dict[str, object], seed)
    payload = action.get("payload")
    seed = payload.get("register_seed") if isinstance(payload, dict) else None
    if isinstance(seed, dict):
        return cast(dict[str, object], seed)
    return None


def _verify_project_library_base_register_seed(
    target_id: str,
    command: dict[str, object],
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    command_id = command.get("command_id")
    if not isinstance(command_id, str) or not command_id.startswith("semantic.library_base."):
        return {"layer": "semantic_reload", "status": "failed", "message": "missing library-base command"}
    library_name = command_id.removeprefix("semantic.library_base.")
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing register seed payload"}
    register = expected.get("register")
    if (
        not isinstance(register, str)
        or not library_name
        or expected.get("kind") != "library_base"
        or expected.get("library_name") != library_name
    ):
        return {"layer": "semantic_reload", "status": "failed", "message": "unexpected library-base register seed payload"}
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    register_seeds = manual_state.get("register_seeds") if isinstance(manual_state, dict) else None
    if not isinstance(register_seeds, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual register seeds were not reloaded"}
    expected_register = register.upper()
    matches = [
        seed
        for seed in register_seeds
        if isinstance(seed, dict)
        and str(seed.get("register")).upper() == expected_register
        and seed.get("kind") == "library_base"
        and seed.get("library_name") == library_name
    ]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_register": expected_register,
        "expected_library_name": library_name,
        "expected_register_seed": expected,
        "matching_register_seeds": matches,
    }


def _verify_struct_pointer_register_seed_mutation(
    target_id: str,
    command: dict[str, object],
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _register_seed_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_semantic_register_seed(target_id, command, expected, project_root=project_root),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _verify_project_semantic_register_seed(
    target_id: str,
    command: dict[str, object],
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    parameters = command.get("parameters")
    struct_name = parameters.get("struct_name") if isinstance(parameters, dict) else None
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing register seed payload"}
    register = expected.get("register")
    if (
        not isinstance(register, str)
        or not isinstance(struct_name, str)
        or not struct_name
        or expected.get("kind") != "struct_ptr"
        or expected.get("struct_name") != struct_name
    ):
        return {"layer": "semantic_reload", "status": "failed", "message": "unexpected struct-pointer register seed payload"}
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    register_seeds = manual_state.get("register_seeds") if isinstance(manual_state, dict) else None
    if not isinstance(register_seeds, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual register seeds were not reloaded"}
    expected_register = register.upper()
    matches = [
        seed
        for seed in register_seeds
        if isinstance(seed, dict)
        and str(seed.get("register")).upper() == expected_register
        and seed.get("kind") == "struct_ptr"
        and seed.get("struct_name") == struct_name
    ]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_register": expected_register,
        "expected_struct_name": struct_name,
        "expected_register_seed": expected,
        "matching_register_seeds": matches,
    }


def _label_command_source_location(command: dict[str, object]) -> tuple[int, int] | None:
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    if not isinstance(locator, dict):
        return None
    section_index = locator.get("section_index")
    source_offset = locator.get("start_offset")
    if isinstance(section_index, int) and isinstance(source_offset, int):
        return section_index, source_offset
    return None


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
    context_kind = context.get("kind") if isinstance(context, dict) else None
    application = durable_result.get("application")
    local_effects = application.get("local_effects") if isinstance(application, dict) else None
    if context_kind == "target" and isinstance(local_effects, list):
        matched = [
            effect
            for effect in local_effects
            if isinstance(effect, dict) and _target_local_effect_matches_command(command, effect)
        ]
        if matched:
            return {
                "layer": "projection",
                "status": "passed",
                "context_kind": "target",
                "effect_kind": matched[0].get("kind"),
            }
        return {
            "layer": "projection",
            "status": "failed",
            "message": "target command local effect was not reported",
        }
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


def _target_local_effect_matches_command(command: dict[str, object], effect: dict[str, object]) -> bool:
    command_id = command.get("command_id")
    if not isinstance(command_id, str):
        return False
    effect_contract = _TARGET_LOCAL_EFFECTS.get(command_id)
    if effect_contract is None:
        return False
    effect_kind, payload_key = effect_contract
    if effect.get("kind") != effect_kind:
        return False
    payload = effect.get(payload_key)
    parameters = command.get("parameters")
    return isinstance(payload, dict) and _projection_payload_matches_parameters(
        payload,
        parameters if isinstance(parameters, dict) else {},
    )


def _projection_payload_matches_parameters(payload: dict[str, object], parameters: dict[str, object]) -> bool:
    return all(payload.get(key) == value for key, value in parameters.items())


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
    if not isinstance(command_id, str) or not isinstance(context, dict):
        return None
    if _command_rank(command_id) <= 0 and not _command_id_is_report_only(command_id):
        return None
    parameters = command.get("parameters")
    normalized = dict(command)
    normalized["kind"] = "command"
    normalized["parameters"] = _command_boundary_parameters(command_id, parameters)
    if _command_id_is_report_only(command_id):
        normalized["effect"] = str(command.get("effect") or "inspection")
        normalized["appends_to_manual_action_log"] = False
        normalized["output_affecting"] = False
    else:
        normalized["output_affecting"] = command.get("output_affecting") is True or _command_id_affects_output(command_id)
    return normalized


def _command_from_candidate_action(candidate: dict[str, object], action: str) -> dict[str, object] | None:
    if _command_id_is_report_only(action):
        context = _report_context_from_candidate(candidate)
        if context is None:
            return None
        return {
            "kind": "command",
            "command_id": action,
            "context": context,
            "parameters": dict(candidate.get("parameters")) if isinstance(candidate.get("parameters"), dict) else {},
            "output_affecting": False,
            "effect": "inspection",
            "appends_to_manual_action_log": False,
        }
    if _command_rank(action) <= 0:
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
    if action.startswith("review.label."):
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
    if action.startswith("range.seed."):
        context = _range_context_from_candidate(candidate)
        if context is None:
            return None
        return {
            "kind": "command",
            "command_id": action,
            "context": context,
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
    if action in {"data_symbol.rename", "data_symbol.rename_existing"}:
        name = parameter_payload.get("name") or candidate.get("new_name") or candidate.get("data_symbol_name")
        if not isinstance(name, str) or not name:
            return None
        element_id = candidate.get("element_id")
        context = (
            {"kind": "element", "locator": locator, "element_id": element_id}
            if isinstance(element_id, str) and element_id
            else {"kind": "row", "locator": locator}
        )
        return {
            "kind": "command",
            "command_id": action,
            "context": context,
            "parameters": {"name": name},
            "output_affecting": True,
        }
    if action == "data_symbol.remove":
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "row", "locator": locator},
            "parameters": _command_boundary_parameters(action, parameter_payload),
            "output_affecting": True,
        }
    if action.startswith("app_slot."):
        context = _app_slot_context_from_candidate(candidate)
        if context is None:
            return None
        return {
            "kind": "command",
            "command_id": action,
            "context": context,
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action.startswith("rsset.binding."):
        element_id = candidate.get("element_id")
        if not isinstance(element_id, str) or not element_id:
            return None
        context = {"kind": "element", "locator": locator, "element_id": element_id}
        for key in ("layout_name", "base_symbol", "base_evidence_id"):
            value = parameter_payload.get(key)
            if isinstance(value, str) and value:
                context[key] = value
        return {
            "kind": "command",
            "command_id": action,
            "context": context,
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action in {
        "target.rsset_region.add",
        "target.rsset_region.edit",
        "target.rsset_region.rename",
        "target.rsset_region.remove",
        "target.equate.add",
        "target.equate.edit",
        "target.equate.represent",
        "target.equate.rename",
        "target.equate.remove",
        "target.custom_struct.add",
        "target.custom_struct.edit",
        "target.custom_struct.rename",
        "target.custom_struct.remove",
        "target.custom_struct_field.add",
        "target.custom_struct_field.edit",
        "target.custom_struct_field.rename",
        "target.custom_struct_field.remove",
        "target.execution_view.add",
        "target.execution_view.edit",
        "target.execution_view.remove",
    }:
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "target"},
            "parameters": _command_boundary_parameters(action, parameter_payload),
            "output_affecting": True,
        }
    if action.startswith("correction.suppress_seeded_item."):
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "row", "locator": locator},
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action.startswith(("typed_gap.field.", "typed_access.field.")):
        context = _typed_field_context_from_candidate(candidate)
        if context is None:
            return None
        parameter_payload = _typed_field_parameters_from_candidate(candidate, parameter_payload)
        return {
            "kind": "command",
            "command_id": action,
            "context": context,
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action == "semantic.register.struct_ptr" or action.startswith(_SEMANTIC_COMMAND_PREFIXES):
        context = _semantic_context_from_candidate(candidate)
        if context is None:
            return None
        return {
            "kind": "command",
            "command_id": action,
            "context": context,
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


def _report_context_from_candidate(candidate: dict[str, object]) -> dict[str, object] | None:
    context = candidate.get("context")
    if isinstance(context, dict):
        return dict(cast(dict[str, object], context))
    locator = candidate.get("locator")
    element_id = candidate.get("element_id")
    if isinstance(element_id, str) and element_id:
        return {"kind": "element", "locator": locator, "element_id": element_id}
    if isinstance(locator, dict):
        return {"kind": "row", "locator": locator}
    return None


def _app_slot_context_from_candidate(candidate: dict[str, object]) -> dict[str, object] | None:
    locator = candidate.get("locator")
    element_id = candidate.get("element_id")
    if not isinstance(element_id, str) or not element_id:
        return None
    context: dict[str, object] = {"kind": "element", "locator": locator, "element_id": element_id}
    for key in ("element_kind", "operand_index", "symbol", "displacement", "base_register", "access"):
        if key in candidate:
            context[key] = candidate[key]
    return context


def _range_context_from_candidate(candidate: dict[str, object]) -> dict[str, object] | None:
    locators = candidate.get("locators")
    if not isinstance(locators, list) or len(locators) < 2:
        return None
    return {
        "kind": "range",
        "locators": [dict(locator) for locator in locators if isinstance(locator, dict)],
    }


def _typed_field_context_from_candidate(candidate: dict[str, object]) -> dict[str, object] | None:
    locator = candidate.get("locator")
    element_id = candidate.get("element_id")
    if not isinstance(element_id, str) or not element_id:
        return None
    context: dict[str, object] = {"kind": "element", "locator": locator, "element_id": element_id}
    for key in (
        "element_kind",
        "operand_index",
        "base_register",
        "displacement",
        "field_offset",
        "root_struct_name",
        "owner_struct_name",
        "refined_struct_name",
        "field_name",
        "field_expr",
        "classification",
        "access",
        "width_bits",
        "width_bytes",
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "conflicts",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
    ):
        if key in candidate:
            context[key] = candidate[key]
    evidence = candidate.get("evidence")
    if isinstance(evidence, dict):
        for key in (
            "source_evidence_id",
            "source_family",
            "source_evidence_status",
            "path_lifetime_scope",
            "confidence",
            "conflicts",
            "contradicted_evidence_id",
            "reason",
            "cleanup_scope",
        ):
            if key in evidence and key not in context:
                context[key] = evidence[key]
    return context


def _command_boundary_parameters(command_id: str, parameters: object) -> dict[str, object]:
    payload = dict(parameters) if isinstance(parameters, dict) else {}
    if command_id in {"data_symbol.rename", "data_symbol.rename_existing"}:
        return {key: payload[key] for key in ("name",) if key in payload}
    if command_id == "data_symbol.remove":
        return {key: payload[key] for key in ("kind", "hunk", "addr", "seed_id") if key in payload}
    if command_id in {"target.equate.add", "target.equate.edit", "target.equate.represent"}:
        return {
            key: payload[key]
            for key in ("name", "value", "comment", "value_representation", "value_expression")
            if key in payload
        }
    if command_id == "target.equate.rename":
        return {key: payload[key] for key in ("previous_name", "name") if key in payload}
    if command_id == "target.equate.remove":
        return {key: payload[key] for key in ("name",) if key in payload}
    return payload


def _typed_field_parameters_from_candidate(
    candidate: dict[str, object],
    parameters: dict[str, object],
) -> dict[str, object]:
    payload = dict(parameters)
    struct_name = (
        candidate.get("owner_struct_name")
        or candidate.get("refined_struct_name")
        or candidate.get("container_struct_name")
        or candidate.get("root_struct_name")
    )
    if isinstance(struct_name, str) and struct_name.strip() and "struct_name" not in payload:
        payload["struct_name"] = struct_name.strip()
    offset = candidate.get("field_offset")
    if not isinstance(offset, int) or isinstance(offset, bool):
        offset = candidate.get("displacement")
    if isinstance(offset, int) and not isinstance(offset, bool) and "offset" not in payload:
        payload["offset"] = offset
    if candidate.get("element_kind") == "typed_access" and "name" not in payload:
        field_name = candidate.get("field_name")
        if isinstance(field_name, str) and field_name.strip():
            payload["name"] = field_name.strip()
    _copy_source_evidence_to_payload(payload, candidate)
    evidence = candidate.get("evidence")
    if isinstance(evidence, dict):
        _copy_source_evidence_to_payload(payload, cast(dict[str, object], evidence))
    return payload


def _copy_source_evidence_to_payload(payload: dict[str, object], source: dict[str, object]) -> None:
    if not isinstance(source.get("source_evidence_id"), str):
        return
    for key in (
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
    ):
        if key in source and key not in payload:
            payload[key] = source[key]


def _semantic_context_from_candidate(candidate: dict[str, object]) -> dict[str, object] | None:
    locator = candidate.get("locator")
    element_id = candidate.get("element_id")
    if not isinstance(element_id, str) or not element_id:
        return None
    context: dict[str, object] = {"kind": "element", "locator": locator, "element_id": element_id}
    for key in (
        "element_kind",
        "operand_index",
        "register",
        "base_register",
        "symbol",
        "value",
        "signed_value",
        "width_bits",
        "width_bytes",
        "api_library",
        "api_function",
        "library_name",
        "function",
        "domain",
    ):
        if key in candidate:
            context[key] = candidate[key]
    return context


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
    policy = _command_execution_policy_blocker(command)
    if policy is not None:
        return str(policy["message"])
    if _candidate_already_satisfied(candidate, command):
        return "candidate already satisfied in projected semantic state"
    command_id = command.get("command_id")
    if isinstance(command_id, str) and _is_typed_field_command_id(command_id) and _typed_field_command_shape_mismatch(command):
        return "typed field shape mismatch"
    if _candidate_verifier(candidate, command) is None:
        return "missing action-specific verifier"
    if not _command_context_complete(command):
        return "missing durable command context"
    return None


def _candidate_verifier(candidate: dict[str, object], command: dict[str, object] | None) -> str | None:
    command_verifier: str | None = None
    command_id: str | None = None
    if command is not None:
        if _command_execution_policy_blocker(command) is not None:
            return None
        raw_command_id = command.get("command_id")
        if isinstance(raw_command_id, str):
            command_id = raw_command_id
            command_verifier = _default_verifier_for_command(command)
            if _is_typed_field_command_id(raw_command_id) and not _typed_field_command_has_accepted_source_evidence(
                command
            ):
                return None
            if raw_command_id == "row.data_block.element.bind_type" and not _data_block_type_command_has_required_evidence(
                command
            ):
                return None
    verifier = candidate.get("default_verifier")
    if isinstance(verifier, str) and verifier:
        if command_id is not None and not _candidate_advertises_command(candidate, command_id):
            return command_verifier
        if command_id == "data_symbol.remove" and command_verifier == "manual_seed_state":
            return command_verifier
        if verifier == "round_trip" and command_verifier not in {None, "round_trip"}:
            return command_verifier
        return verifier
    return command_verifier


def _default_verifier_for_command(command: dict[str, object]) -> str | None:
    command_id = command.get("command_id")
    if command_id == "data_symbol.remove":
        parameters = command.get("parameters")
        if isinstance(parameters, dict) and isinstance(parameters.get("seed_id"), str):
            return "manual_seed_state"
    return _default_verifier_for_actions([str(command_id or "")])


def _is_typed_field_command_id(command_id: str) -> bool:
    return command_id.startswith(("typed_gap.field.", "typed_access.field."))


def _typed_field_command_has_accepted_source_evidence(command: dict[str, object]) -> bool:
    evidence = _command_source_evidence_payload(command)
    if evidence is None:
        return False
    source_family = evidence.get("source_family") or evidence.get("evidence_source_family")
    status = evidence.get("source_evidence_status") or evidence.get("evidence_status") or evidence.get("status")
    scope = evidence.get("path_lifetime_scope")
    conflicts = evidence.get("conflicts")
    if source_family != "struct_pointer":
        return False
    if not isinstance(status, str) or status not in _ACCEPTED_PROVENANCE_STATUSES:
        return False
    if not isinstance(scope, dict) or not scope.get("kind"):
        return False
    if isinstance(conflicts, list) and conflicts and status != "manual_override":
        return False
    if status == "manual_override":
        return _manual_override_evidence_is_complete(evidence) and _typed_field_command_has_compatible_shape(command)
    return _typed_field_command_has_compatible_shape(command)


def _typed_field_command_has_compatible_shape(command: dict[str, object]) -> bool:
    return not _typed_field_command_shape_mismatch(command)


def _typed_field_command_shape_mismatch(command: dict[str, object]) -> bool:
    params = command.get("parameters")
    context = command.get("context")
    if not isinstance(params, dict) or not isinstance(context, dict):
        return True
    offset = params.get("offset")
    context_offset = context.get("field_offset")
    if not isinstance(context_offset, int) or isinstance(context_offset, bool):
        context_offset = context.get("displacement")
    if (
        isinstance(offset, int)
        and not isinstance(offset, bool)
        and isinstance(context_offset, int)
        and not isinstance(context_offset, bool)
        and offset != context_offset
    ):
        return True
    size = params.get("size")
    width_bytes = context.get("width_bytes")
    if isinstance(size, int) and not isinstance(size, bool) and isinstance(width_bytes, int) and not isinstance(width_bytes, bool):
        return size != width_bytes
    width_bits = context.get("width_bits")
    if isinstance(size, int) and not isinstance(size, bool) and isinstance(width_bits, int) and not isinstance(width_bits, bool):
        return size * 8 != width_bits
    return False


def _manual_override_evidence_is_complete(evidence: dict[str, object]) -> bool:
    contradicted_evidence_id = evidence.get("contradicted_evidence_id")
    reason = evidence.get("reason")
    cleanup_scope = evidence.get("cleanup_scope")
    cleanup_kind = cleanup_scope.get("kind") if isinstance(cleanup_scope, dict) else None
    return (
        isinstance(contradicted_evidence_id, str)
        and bool(contradicted_evidence_id)
        and isinstance(reason, str)
        and bool(reason)
        and isinstance(cleanup_kind, str)
        and bool(cleanup_kind)
        and _manual_override_cleanup_scope_matches_contradicted_evidence(evidence)
    )


def _manual_override_cleanup_scope_matches_contradicted_evidence(evidence: dict[str, object]) -> bool:
    contradicted_evidence_id = evidence.get("contradicted_evidence_id")
    cleanup_scope = evidence.get("cleanup_scope")
    if not isinstance(contradicted_evidence_id, str) or not isinstance(cleanup_scope, dict):
        return False
    cleanup_kind = cleanup_scope.get("kind")
    if cleanup_kind != "owned_descendants":
        return True
    cleanup_evidence_id = cleanup_scope.get("source_evidence_id")
    return isinstance(cleanup_evidence_id, str) and cleanup_evidence_id == contradicted_evidence_id


def _data_block_type_command_has_required_evidence(command: dict[str, object]) -> bool:
    params = command.get("parameters")
    requires = params.get("requires_source_evidence") if isinstance(params, dict) else None
    evidence = _command_source_evidence_payload(command)
    if requires is not True and evidence is None:
        return True
    if evidence is None:
        return False
    source_family = evidence.get("source_family") or evidence.get("evidence_source_family")
    status = evidence.get("source_evidence_status") or evidence.get("evidence_status") or evidence.get("status")
    scope = evidence.get("path_lifetime_scope")
    conflicts = evidence.get("conflicts")
    if source_family not in {"data_block_pointer", "struct_pointer", "constant_or_equ", "rsset_app_base"}:
        return False
    if not isinstance(status, str) or status not in _ACCEPTED_PROVENANCE_STATUSES:
        return False
    if not isinstance(scope, dict) or not scope.get("kind"):
        return False
    if isinstance(conflicts, list) and conflicts and status != "manual_override":
        return False
    if status == "manual_override":
        return _manual_override_evidence_is_complete(evidence)
    return True


def _candidate_advertises_command(candidate: dict[str, object], command_id: str) -> bool:
    actions = candidate.get("suggested_action_kinds")
    if isinstance(actions, list) and any(action == command_id for action in actions):
        return True
    action = candidate.get("suggested_action_kind")
    if action == command_id:
        return True
    embedded = candidate.get("command")
    return isinstance(embedded, dict) and embedded.get("command_id") == command_id


def _command_context_complete(command: dict[str, object]) -> bool:
    context = command.get("context")
    if not isinstance(context, dict):
        return False
    kind = context.get("kind")
    if kind == "row":
        return _is_full_listing_locator(context.get("locator"))
    if kind == "element":
        return _is_full_listing_locator(context.get("locator")) and isinstance(context.get("element_id"), str)
    if kind == "range":
        locators = context.get("locators")
        return (
            isinstance(locators, list)
            and len(locators) >= 2
            and all(_is_full_listing_locator(locator) for locator in locators)
        )
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
    if command_id in {"data_symbol.rename", "data_symbol.rename_existing"}:
        name = parameters.get("name")
        return isinstance(name, str) and current.get("name") == name
    if command_id == "data_symbol.remove":
        if isinstance(parameters.get("seed_id"), str):
            return current.get("removed") is True
        return current.get("suppressed") is True
    if command_id in {"app_slot.rename", "app_slot.edit"}:
        return all(current.get(key) == value for key, value in parameters.items())
    if command_id == "app_slot.remove":
        return current.get("removed") is True
    if command_id in {"target.rsset_region.add", "target.rsset_region.edit", "target.rsset_region.rename"}:
        return all(current.get(key) == value for key, value in parameters.items())
    if command_id == "target.rsset_region.remove":
        return current.get("removed") is True
    if command_id in {"target.equate.add", "target.equate.edit", "target.equate.represent"}:
        return all(current.get(key) == value for key, value in parameters.items())
    if command_id == "target.equate.rename":
        name = parameters.get("name")
        return isinstance(name, str) and current.get("name") == name
    if command_id == "target.equate.remove":
        return current.get("removed") is True
    if command_id in {"target.custom_struct.add", "target.custom_struct.edit"}:
        return all(current.get(key) == value for key, value in parameters.items())
    if command_id == "target.custom_struct.rename":
        name = parameters.get("name")
        return isinstance(name, str) and current.get("name") == name
    if command_id == "target.custom_struct.remove":
        return current.get("removed") is True
    if command_id in {
        "target.custom_struct_field.add",
        "target.custom_struct_field.edit",
        "target.custom_struct_field.rename",
        "typed_gap.field.add",
        "typed_gap.field.edit",
        "typed_access.field.edit",
        "typed_access.field.rename",
    }:
        return all(current.get(key) == value for key, value in parameters.items())
    if command_id in {"target.custom_struct_field.remove", "typed_access.field.remove"}:
        return current.get("removed") is True
    if command_id in {"target.execution_view.add", "target.execution_view.edit"}:
        return all(current.get(key) == value for key, value in parameters.items())
    if command_id == "target.execution_view.remove":
        return current.get("removed") is True
    if command_id.startswith("correction.suppress_seeded_item."):
        return current.get("suppressed") is True
    if command_id.startswith("semantic.library_base."):
        context = command.get("context")
        library_name = command_id.removeprefix("semantic.library_base.")
        return (
            isinstance(context, dict)
            and current.get("kind") == "library_base"
            and current.get("register", "A6") == "A6"
            and current.get("library_name") == library_name
        )
    if command_id == "semantic.register.struct_ptr":
        context = command.get("context")
        register = context.get("register") if isinstance(context, dict) else None
        struct_name = parameters.get("struct_name")
        return (
            isinstance(register, str)
            and isinstance(struct_name, str)
            and current.get("kind") == "struct_ptr"
            and current.get("register") == register
            and current.get("struct_name") == struct_name
        )
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
    rank = _COMMAND_RANK.get(command_id)
    if rank is not None:
        return rank
    for prefix, prefix_rank in _COMMAND_PREFIX_RANK.items():
        if command_id.startswith(prefix):
            return prefix_rank
    if _command_id_is_report_only(command_id):
        return 5
    return 0


def _command_summary(command: dict[str, object], candidate: dict[str, object] | None = None) -> dict[str, object]:
    verifier = (
        _candidate_verifier(candidate, command)
        if candidate is not None
        else _default_verifier_for_command(command)
    )
    summary = {
        "command_id": command.get("command_id"),
        "output_affecting": command.get("output_affecting") is True,
        "verifier": verifier,
    }
    if _command_execution_policy_blocker(command) is not None:
        summary["execution_policy"] = "report_only"
    return summary


def _commands_same_identity(left: dict[str, object], right: dict[str, object]) -> bool:
    return left.get("command_id") == right.get("command_id") and left.get("context") == right.get("context")


def _available_catalog_command(command: dict[str, object], availability: dict[str, object]) -> dict[str, object] | None:
    commands = availability.get("commands")
    if not isinstance(commands, list):
        return None
    for entry in commands:
        if (
            isinstance(entry, dict)
            and entry.get("command_id") == command.get("command_id")
            and _catalog_entry_matches_command_identity(command, cast(dict[str, object], entry))
        ):
            return cast(dict[str, object], entry)
    return None


def _catalog_entry_matches_command_identity(command: dict[str, object], entry: dict[str, object]) -> bool:
    command_id = command.get("command_id")
    if command_id in {"rsset.binding.bind", "rsset.binding.unbind"}:
        return _catalog_entry_parameters_match(
            command,
            entry,
            ("layout_name", "base_symbol", "base_register", "base_evidence_id", "displacement", "operand_index"),
        )
    if isinstance(command_id, str) and _is_typed_field_command_id(command_id):
        return _catalog_entry_parameters_match(
            command,
            entry,
            ("struct_name", "offset", "source_evidence_id", "source_family", "source_evidence_status"),
        )
    if command_id in {"row.data_block.element.bind_type", "row.data_block.element.clear_type"}:
        return _catalog_entry_parameters_match(command, entry, ("layout_id", "offset", "width"))
    if isinstance(command_id, str) and command_id.startswith("correction.suppress_seeded_item."):
        return _catalog_entry_parameters_match(command, entry, ("kind", "hunk", "addr"))
    return True


def _catalog_entry_parameters_match(
    command: dict[str, object],
    entry: dict[str, object],
    required_keys: tuple[str, ...],
) -> bool:
    command_parameters = command.get("parameters")
    entry_parameters = entry.get("parameters")
    if not isinstance(command_parameters, dict) or not isinstance(entry_parameters, dict):
        return False
    for key in required_keys:
        command_value = command_parameters.get(key)
        entry_value = entry_parameters.get(key)
        if entry_value is None or entry_value != command_value:
            return False
    return True


def _command_available_in_catalog(command: dict[str, object], availability: dict[str, object]) -> bool:
    return _available_catalog_command(command, availability) is not None


def _command_id_is_report_only(command_id: str) -> bool:
    return command_id.endswith(".report") or command_id.startswith(_REPORT_ONLY_COMMAND_PREFIXES)


def _command_execution_policy_blocker(
    command: dict[str, object],
    catalog_entry: dict[str, object] | None = None,
) -> dict[str, object] | None:
    command_id = command.get("command_id")
    if not isinstance(command_id, str):
        return {
            "layer": "command_execution_policy",
            "status": "failed",
            "message": "command id is missing",
            "command_id": command_id,
        }
    if _command_is_report_only(command) or (catalog_entry is not None and _command_is_report_only(catalog_entry)):
        return {
            "layer": "command_execution_policy",
            "status": "failed",
            "message": "command is report-only",
            "command_id": command_id,
        }
    return None


def _command_is_report_only(command: dict[str, object]) -> bool:
    command_id = command.get("command_id")
    if isinstance(command_id, str) and _command_id_is_report_only(command_id):
        return True
    if command.get("appends_to_manual_action_log") is False:
        return True
    effect = command.get("effect")
    return isinstance(effect, str) and effect != "manual_mutation"


def _select_available_command_action(
    target_id: str,
    inspect_report: dict[str, object],
    *,
    excluded_command: dict[str, object] | None = None,
) -> dict[str, object] | None:
    candidates = inspect_report.get("candidate_work")
    if not isinstance(candidates, list):
        return None
    eligible: list[dict[str, object]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for option in _candidate_command_options(candidate):
            if excluded_command is not None and _commands_same_identity(option, excluded_command):
                continue
            if _candidate_skip_reason(candidate, option) is not None:
                continue
            eligible.append(
                {
                    "work_item": dict(candidate),
                    "command": option,
                    "planner_score": _candidate_score(candidate, option),
                }
            )
    eligible.sort(key=lambda item: cast(int, item["planner_score"]), reverse=True)
    for item in eligible:
        command = cast(dict[str, object], item["command"])
        availability = _command_availability(target_id, cast(dict[str, object], command["context"]))
        catalog_entry = _available_catalog_command(command, availability)
        if catalog_entry is not None and _command_execution_policy_blocker(command, catalog_entry) is None:
            item["availability"] = availability
            return item
    return None


def _select_candidate_command(
    candidate: dict[str, object],
    options: list[dict[str, object]],
) -> tuple[dict[str, object] | None, str | None]:
    if not options:
        return None, _candidate_skip_reason(candidate, None)
    first_skip_reason: str | None = None
    for option in options:
        skip_reason = _candidate_skip_reason(candidate, option)
        if skip_reason is None:
            return option, None
        if first_skip_reason is None:
            first_skip_reason = skip_reason
    return options[0], first_skip_reason


def _command_id_affects_output(command_id: str) -> bool:
    return command_id != "comment.edit"


def _selected_command_id(selected: dict[str, object] | None) -> str | None:
    if selected is None:
        return None
    command = selected.get("command")
    if not isinstance(command, dict):
        return None
    command_id = command.get("command_id")
    return command_id if isinstance(command_id, str) else None


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
        command, skip_reason = _select_candidate_command(candidate, options)
        score = _candidate_score(candidate, command)
        checked = dict(candidate)
        checked["planner_score"] = score
        checked["candidate_commands"] = [_command_summary(option, candidate) for option in options]
        ranked.append(checked)
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
        "selected_verifier": _candidate_verifier(cast(dict[str, object], selected["work_item"]), command),
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
        query = {
            "context": ["element"],
            "locator": [json.dumps(context["locator"])],
            "element_id": [str(context["element_id"])],
        }
        for key in ("layout_name", "base_symbol", "base_evidence_id"):
            value = context.get(key)
            if isinstance(value, str) and value:
                query[key] = [value]
        return query
    if kind == "range":
        return {"context": ["range"], "locators": [json.dumps(context["locators"])]}
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
