from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import cast

from amiga_reversing.disasm import projects, server
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    resolve_target_binary_source,
)
from amiga_reversing.disasm.c_backend import render_project_source_with_c_backend
from amiga_reversing.disasm.callback_slot_report import callback_slot_report
from amiga_reversing.disasm.decision_journal import decision_journal_report
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_target_metadata,
)
from amiga_reversing.disasm.listing_context import listing_element_contexts
from amiga_reversing.disasm.manual_actions import review_item_is_open
from amiga_reversing.disasm.project_paths import (
    PROJECT_ROOT,
    resolve_project_dir,
    resolve_project_paths,
)
from amiga_reversing.disasm.target_metadata import SeededEntityMetadata, TargetMetadata
from amiga_reversing.reversing_workspace import (
    clean_run_target_workspace,
    inspect_target_hygiene,
)

TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "stopped"})
PARTIAL_ITERATION_STATUSES = frozenset({"started", "running", "partial"})
_LISTING_COMMENT_SEARCH_ROW_COUNT = 512
_LISTING_SOURCE_CANDIDATE_ROW_COUNT = 2048
_LISTING_SOURCE_CANDIDATE_MAX_ROWS = 16384
_MIN_IMMEDIATE_REFERENCE_VALUE = 0x1000
_AMIGA_CUSTOM_BASE_ADDRESS = 0xDFF000
_AMIGA_CUSTOM_REGISTER_MAX_OFFSET = 0x1FE
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
    "data_symbol.add": 82,
    "data_symbol.rename": 82,
    "data_symbol.edit": 83,
    "data_symbol.rename_existing": 83,
    "rsset.binding.bind": 81,
    "target.rsset_region.rename": 82,
    "target.rsset_region.add": 80,
    "target.rsset_region.edit": 80,
    "representation.choose": 75,
    "representation.hex": 75,
    "representation.binary": 75,
    "representation.character": 75,
    "immediate_ref.interpret": 84,
    "a5_hardware_ref.interpret": 83,
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
_REPORT_ONLY_COMMAND_PREFIXES: tuple[str, ...] = ()
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

_IMMEDIATE_REF_VERIFIER = "immediate_interpreted_ref_state"
_A5_HARDWARE_REF_VERIFIER = "a5_hardware_ref_state"


def _parse_int_auto(value: str) -> int:
    return int(value, 0)


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _sequence_values(value: object) -> list[object]:
    if isinstance(value, list | tuple):
        return list(value)
    return []


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

    callback_parser = subparsers.add_parser(
        "callback-report",
        help="Report app-slot code pointers consumed by indirect calls or jumps.",
    )
    callback_parser.add_argument("--target", required=True)
    callback_parser.add_argument("--slot-symbol")
    callback_parser.add_argument("--slot-offset", type=_parse_int_auto)
    callback_parser.add_argument("--listing-timeout-seconds", type=float, default=10.0)

    immediate_ref_parser = subparsers.add_parser(
        "immediate-ref-report",
        help="Report immediate constants that fall inside known source/runtime ranges.",
    )
    immediate_ref_parser.add_argument("--target", required=True)
    immediate_ref_parser.add_argument("--listing-timeout-seconds", type=float, default=10.0)

    immediate_packet_parser = subparsers.add_parser(
        "source-offset-immediate-packet",
        help="Emit one read-only source-offset immediate evidence packet.",
    )
    immediate_packet_parser.add_argument("--target", required=True)
    immediate_packet_parser.add_argument("--candidate-id", required=True)
    immediate_packet_parser.add_argument("--listing-timeout-seconds", type=float, default=10.0)

    a5_hardware_parser = subparsers.add_parser(
        "a5-hardware-report",
        help="Report read-only A5 custom-chip base listing candidates.",
    )
    a5_hardware_parser.add_argument("--target", required=True)
    a5_hardware_parser.add_argument("--listing-timeout-seconds", type=float, default=10.0)

    a5_packet_parser = subparsers.add_parser(
        "a5-path-lifetime-packet",
        help="Emit one read-only A5 path/lifetime evidence packet.",
    )
    a5_packet_parser.add_argument("--target", required=True)
    a5_packet_parser.add_argument("--selected-use-id", required=True)
    a5_packet_parser.add_argument("--listing-timeout-seconds", type=float, default=10.0)

    rsset_candidate_parser = subparsers.add_parser(
        "rsset-candidate-report",
        help="Report read-only RSSET/app-slot candidates from raw or weak A6 operands.",
    )
    rsset_candidate_parser.add_argument("--target", required=True)
    rsset_candidate_parser.add_argument("--listing-timeout-seconds", type=float, default=10.0)

    orphan_packet_parser = subparsers.add_parser(
        "orphan-code-island-packet",
        help="Emit one read-only orphan/code-island/data-range evidence packet.",
    )
    orphan_packet_parser.add_argument("--target", required=True)
    orphan_packet_parser.add_argument("--candidate-id", required=True)

    decision_journal_parser = subparsers.add_parser(
        "decision-journal-report",
        help="Report read-only Decision Journal validation state.",
    )
    decision_journal_parser.add_argument("--target", required=True)
    decision_journal_parser.add_argument("--dry-run-record", type=Path)

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
    if args.command == "callback-report":
        _print_json(
            inspect_callback_slots(
                args.target,
                slot_symbol=args.slot_symbol,
                slot_offset=args.slot_offset,
                listing_timeout_seconds=args.listing_timeout_seconds,
                project_root=args.project_root,
            )
        )
        return 0
    if args.command == "immediate-ref-report":
        _print_json(
            inspect_immediate_runtime_refs(
                args.target,
                listing_timeout_seconds=args.listing_timeout_seconds,
                project_root=args.project_root,
            )
        )
        return 0
    if args.command == "source-offset-immediate-packet":
        _print_json(
            query_source_offset_immediate_packet(
                args.target,
                candidate_id=args.candidate_id,
                listing_timeout_seconds=args.listing_timeout_seconds,
                project_root=args.project_root,
            )
        )
        return 0
    if args.command == "a5-hardware-report":
        _print_json(
            inspect_a5_hardware_lifetimes(
                args.target,
                listing_timeout_seconds=args.listing_timeout_seconds,
                project_root=args.project_root,
            )
        )
        return 0
    if args.command == "a5-path-lifetime-packet":
        _print_json(
            query_a5_path_lifetime_packet(
                args.target,
                selected_use_id=args.selected_use_id,
                listing_timeout_seconds=args.listing_timeout_seconds,
                project_root=args.project_root,
            )
        )
        return 0
    if args.command == "rsset-candidate-report":
        _print_json(
            inspect_rsset_candidates(
                args.target,
                listing_timeout_seconds=args.listing_timeout_seconds,
                project_root=args.project_root,
            )
        )
        return 0
    if args.command == "orphan-code-island-packet":
        _print_json(
            query_orphan_code_island_packet(
                args.target,
                candidate_id=args.candidate_id,
                project_root=args.project_root,
            )
        )
        return 0
    if args.command == "decision-journal-report":
        _print_json(
            inspect_decision_journal(
                args.target,
                dry_run_record_path=args.dry_run_record,
                project_root=args.project_root,
            )
        )
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


def inspect_decision_journal(
    target_id: str,
    *,
    dry_run_record_path: Path | None = None,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    target_dir = resolve_project_dir(target_id, project_root=project_root)
    dry_run_record = _load_decision_dry_run_record(dry_run_record_path) if dry_run_record_path is not None else None
    report = decision_journal_report(target_dir, dry_run_record=dry_run_record)
    result = {"target_id": target_id, **report}
    result = _decision_journal_report_with_current_source_audit(
        target_id,
        result,
        project_root=project_root,
    )
    if dry_run_record_path is not None:
        dry_run = result.get("dry_run_record")
        if isinstance(dry_run, dict):
            dry_run["path"] = str(dry_run_record_path)
    return result


def _load_decision_dry_run_record(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"__load_error__": str(exc)}


def _decision_journal_report_with_current_source_audit(
    target_id: str,
    report: dict[str, object],
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    audit = report.get("audit")
    records = audit.get("records") if isinstance(audit, Mapping) else None
    if not isinstance(records, Sequence) or isinstance(records, str):
        return report
    rsset_report: dict[str, object] | None = None
    updated_records: list[object] = []
    for raw_record in records:
        if not isinstance(raw_record, Mapping):
            updated_records.append(raw_record)
            continue
        record = dict(raw_record)
        if (
            record.get("state") == "active"
            and record.get("action") == "accept_fact"
            and record.get("fact_type") == "rsset_app_base"
        ):
            if rsset_report is None:
                rsset_report = inspect_rsset_candidates(target_id, project_root=project_root)
            record = _rsset_source_effect_audit_record(record, rsset_report)
        updated_records.append(record)
    updated_audit = dict(audit)
    updated_audit["records"] = updated_records
    return {**report, "audit": updated_audit}


def _rsset_source_effect_audit_record(
    audit_record: dict[str, object],
    rsset_report: Mapping[str, object],
) -> dict[str, object]:
    candidate_id = audit_record.get("candidate_id")
    if not isinstance(candidate_id, str):
        return _audit_record_with_blocker(audit_record, "missing_candidate_id")
    candidate_report = rsset_report.get("rsset_candidate_report")
    candidate = _rsset_candidate_report_find_candidate(
        candidate_report if isinstance(candidate_report, Mapping) else {},
        candidate_id,
    )
    if candidate is None:
        return _audit_record_with_blocker(audit_record, "current_rsset_candidate_not_found")
    decision_id = audit_record.get("decision_id")
    matched_decision = _rsset_candidate_has_matching_journal_decision(candidate, decision_id)
    if not matched_decision:
        return _audit_record_with_blocker(audit_record, "current_journal_evidence_not_matched")
    bind = (candidate.get("command_support") or {}).get("bind") if isinstance(candidate.get("command_support"), Mapping) else None
    existing = bind.get("existing_manual_state") if isinstance(bind, Mapping) else None
    if (
        isinstance(bind, Mapping)
        and bind.get("state") == "already_satisfied"
        and isinstance(existing, Mapping)
        and existing.get("source_evidence_id") == decision_id
    ):
        updated = dict(audit_record)
        updated["replay"] = {"status": "source_effective", "semantic_reload": "current_rsset_report_matched"}
        updated["rendered_source_effect"] = {
            "status": "source_effective",
            "effect": "selected RSSET binding exists in current manual state",
            "render_intent": "enables_render",
            "source": "rsset-candidate-report",
            "owner_action_id": existing.get("owner_action_id"),
        }
        updated["verifier_layers"] = [
            {"layer": "decision_journal", "status": "passed"},
            {"layer": "semantic_reload", "status": "passed", "source": "rsset-candidate-report"},
            {"layer": "generated_source", "status": "passed_or_previously_verified", "source": "existing_manual_state"},
            {"layer": "exact_round_trip", "status": "passed_or_previously_verified", "source": "existing_manual_state"},
        ]
        updated["blockers"] = [
            blocker for blocker in _string_sequence(audit_record.get("blockers")) if blocker != "source_effect_not_verified"
        ]
        return updated
    updated = dict(audit_record)
    updated["replay"] = {"status": "matched_current_packet", "semantic_reload": "current_rsset_report_matched"}
    return _audit_record_with_blocker(updated, "missing_current_rendered_source_effect")


def _rsset_candidate_has_matching_journal_decision(candidate: Mapping[str, object], decision_id: object) -> bool:
    if not isinstance(decision_id, str):
        return False
    lane = candidate.get("journal_decision_evidence")
    accepted = lane.get("accepted") if isinstance(lane, Mapping) else None
    if not isinstance(accepted, Sequence) or isinstance(accepted, str):
        return False
    return any(isinstance(item, Mapping) and item.get("decision_id") == decision_id for item in accepted)


def _audit_record_with_blocker(record: dict[str, object], blocker: str) -> dict[str, object]:
    blockers = _string_sequence(record.get("blockers"))
    if blocker not in blockers:
        blockers.append(blocker)
    return {**record, "blockers": blockers}


def inspect_callback_slots(
    target_id: str,
    *,
    slot_symbol: str | None = None,
    slot_offset: int | None = None,
    listing_timeout_seconds: float = 10.0,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    hygiene = inspect_target_hygiene(target_id, mode="inspect", project_root=project_root)
    report: dict[str, object] = {
        "target_id": target_id,
        "hygiene": hygiene.to_dict(),
        "safe_to_mutate": hygiene.safe_to_continue and not hygiene.unknown_files,
    }
    listing_ready = _open_and_wait_listing(target_id, timeout_seconds=listing_timeout_seconds)
    report["listing_open"] = listing_ready
    if listing_ready.get("status") != "ready":
        return report
    rows = _listing_all_rows(target_id)
    project_response = server.route_request("GET", f"/api/projects/{target_id}", {})
    project_data = project_response.get("data")
    project_payload = project_data.get("project") if isinstance(project_data, dict) else {}
    review_items = project_payload.get("review_items") if isinstance(project_payload, dict) else None
    report["callback_slots"] = callback_slot_report(
        [row for row in rows if isinstance(row, Mapping)],
        [item for item in review_items if isinstance(item, Mapping)] if isinstance(review_items, list) else (),
        slot_symbol=slot_symbol,
        slot_offset=slot_offset,
    )
    return report


def inspect_immediate_runtime_refs(
    target_id: str,
    *,
    listing_timeout_seconds: float = 10.0,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    hygiene = inspect_target_hygiene(target_id, mode="inspect", project_root=project_root)
    hygiene_safe = hygiene.safe_to_continue and not hygiene.unknown_files
    report: dict[str, object] = {
        "target_id": target_id,
        "hygiene": hygiene.to_dict(),
        "safe_to_mutate": False,
        "interpretation_policy": _immediate_reference_interpretation_policy(),
    }
    listing_ready = _open_and_wait_listing(target_id, timeout_seconds=listing_timeout_seconds)
    report["listing_open"] = listing_ready
    if listing_ready.get("status") != "ready":
        report["immediate_reference_candidates"] = []
        report["mutation_gate"] = _immediate_reference_mutation_gate([])
        return report
    rows = _listing_all_rows(target_id)
    candidates = _listing_immediate_runtime_reference_report(rows)
    mutation_gate = _immediate_reference_mutation_gate(candidates)
    report["immediate_reference_candidates"] = candidates
    report["mutation_gate"] = mutation_gate
    report["safe_to_mutate"] = hygiene_safe and mutation_gate["safe_to_mutate"] is True
    return report


def inspect_a5_hardware_lifetimes(
    target_id: str,
    *,
    listing_timeout_seconds: float = 10.0,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    hygiene = inspect_target_hygiene(target_id, mode="inspect", project_root=project_root)
    report: dict[str, object] = {
        "target_id": target_id,
        "hygiene": hygiene.to_dict(),
        "safe_to_mutate": False,
        "verifier_gate": _a5_hardware_verifier_gate(),
    }
    listing_ready = _open_and_wait_listing(target_id, timeout_seconds=listing_timeout_seconds)
    report["listing_open"] = listing_ready
    if listing_ready.get("status") != "ready":
        report["a5_hardware_lifetimes"] = _empty_a5_hardware_lifetime_report()
        return report
    rows = _listing_all_rows(target_id)
    lifetime_report = _listing_a5_hardware_lifetime_report(rows)
    lifetime_report = _a5_hardware_lifetime_report_with_existing_refs(
        lifetime_report,
        _existing_a5_hardware_ref_index(target_id, project_root=project_root),
    )
    report["a5_hardware_lifetimes"] = lifetime_report
    cfg_report = lifetime_report.get("cfg_path_lifetime_report")
    if isinstance(cfg_report, dict):
        report["safe_to_mutate"] = cfg_report.get("safe_to_mutate") is True
    return report


def inspect_rsset_candidates(
    target_id: str,
    *,
    listing_timeout_seconds: float = 10.0,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    hygiene = inspect_target_hygiene(target_id, mode="inspect", project_root=project_root)
    target_dir = resolve_project_dir(target_id, project_root=project_root)
    journal_report = decision_journal_report(target_dir)
    journal_projection = journal_report.get("projection") if isinstance(journal_report, Mapping) else None
    project_payload = _project_state_payload(target_id, project_root)
    manual_state = project_payload.get("manual_state") if isinstance(project_payload, Mapping) else None
    report: dict[str, object] = {
        "target_id": target_id,
        "hygiene": hygiene.to_dict(),
        "safe_to_mutate": False,
        "mutation_policy": "report_only",
    }
    listing_ready = _open_and_wait_listing(target_id, timeout_seconds=listing_timeout_seconds)
    report["listing_open"] = listing_ready
    if listing_ready.get("status") != "ready":
        report["rsset_candidate_report"] = _empty_rsset_candidate_report()
        return report
    rows = _listing_all_rows(target_id)
    report["rsset_candidate_report"] = _listing_rsset_candidate_report(
        rows,
        target_id=target_id,
        manual_state=manual_state if isinstance(manual_state, Mapping) else None,
        journal_projection=journal_projection if isinstance(journal_projection, Mapping) else None,
        exact_round_trip_available=(target_dir / "reproduction.json").exists(),
    )
    return report


def query_rsset_evidence_packet(
    target_id: str,
    *,
    candidate_id: str,
    selected_use_id: str | None = None,
    listing_timeout_seconds: float = 10.0,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    report = inspect_rsset_candidates(
        target_id,
        listing_timeout_seconds=listing_timeout_seconds,
        project_root=project_root,
    )
    candidate_report = report.get("rsset_candidate_report")
    if not isinstance(candidate_report, Mapping):
        candidate_report = _empty_rsset_candidate_report()
    return _rsset_evidence_packet_from_candidate_report(
        target_id,
        candidate_report,
        candidate_id=candidate_id,
        selected_use_id=selected_use_id,
    )


def query_source_offset_immediate_packet(
    target_id: str,
    *,
    candidate_id: str,
    listing_timeout_seconds: float = 10.0,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    report = inspect_immediate_runtime_refs(
        target_id,
        listing_timeout_seconds=listing_timeout_seconds,
        project_root=project_root,
    )
    candidates = report.get("immediate_reference_candidates")
    if not isinstance(candidates, Sequence) or isinstance(candidates, str):
        candidates = []
    return _source_offset_immediate_packet_from_candidates(
        target_id,
        [candidate for candidate in candidates if isinstance(candidate, Mapping)],
        candidate_id=candidate_id,
    )


def query_a5_path_lifetime_packet(
    target_id: str,
    *,
    selected_use_id: str,
    listing_timeout_seconds: float = 10.0,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    report = inspect_a5_hardware_lifetimes(
        target_id,
        listing_timeout_seconds=listing_timeout_seconds,
        project_root=project_root,
    )
    lifetime_report = report.get("a5_hardware_lifetimes")
    if not isinstance(lifetime_report, Mapping):
        lifetime_report = _empty_a5_hardware_lifetime_report()
    return _a5_path_lifetime_packet_from_report(
        target_id,
        lifetime_report,
        selected_use_id=selected_use_id,
    )


def query_orphan_code_island_packet(
    target_id: str,
    *,
    candidate_id: str,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    report = _inspect_report_with_listing_candidates(
        target_id,
        inspect_target(target_id, project_root=project_root),
        project_root=project_root,
    )
    candidates = report.get("candidate_work")
    if not isinstance(candidates, Sequence) or isinstance(candidates, str):
        candidates = []
    return _orphan_code_island_packet_from_candidates(
        target_id,
        [candidate for candidate in candidates if isinstance(candidate, Mapping)],
        candidate_id=candidate_id,
    )


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
    _record_planner_availability_check(inspect_report, selected, command, availability, catalog_entry)
    if catalog_entry is None:
        alternate = _select_available_command_action(target_id, inspect_report, excluded_command=command)
        if alternate is not None:
            _record_planner_selection_drift(
                inspect_report,
                before=selected,
                after=alternate,
                reason="selected command unavailable; used next available catalog command",
            )
            selected = alternate
            command = cast(dict[str, object], selected["command"])
            availability = cast(dict[str, object], selected["availability"])
            catalog_entry = _available_catalog_command(command, availability)
        else:
            _record_planner_selection_drift(
                inspect_report,
                before=selected,
                after=None,
                reason="selected command unavailable and no alternate command was available",
            )
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
    else:
        _record_planner_selection_drift(inspect_report, before=selected, after=selected, reason=None)

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
            action_result={"status": "blocked", "availability": availability},
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
            action_result={"status": "blocked", "availability": availability},
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

    if dry_run:
        report = _iteration_report(
            run_state=run_result.run_state,
            iteration_id=iteration_id,
            inspect_report=inspect_report,
            selected_work_item=cast(dict[str, object], selected["work_item"]),
            command=command,
            action_result={"status": "dry_run", "availability": availability},
            verification={"status": "not_run", "layers": []},
            workflow_profile=None,
            next_recommendation=recommend_next_step(
                inspect_report=inspect_report,
                verification={"status": "not_run", "layers": []},
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
    target_dir = projects.resolve_project_dir(target_id, project_root=project_root)
    journal_report = decision_journal_report(target_dir)
    journal_projection = journal_report.get("projection") if isinstance(journal_report, Mapping) else None
    project_payload = inspect_report.get("target_state")
    project_payload = project_payload.get("project") if isinstance(project_payload, Mapping) else None
    if not isinstance(project_payload, Mapping):
        project_payload = _project_state_payload(target_id, project_root)
    manual_state = project_payload.get("manual_state") if isinstance(project_payload, Mapping) else None
    rsset_report = _listing_rsset_candidate_report(
        rows if isinstance(rows, list) else [],
        target_id=target_id,
        manual_state=manual_state if isinstance(manual_state, Mapping) else None,
        journal_projection=journal_projection if isinstance(journal_projection, Mapping) else None,
        exact_round_trip_available=(target_dir / "reproduction.json").exists(),
    )
    candidates.extend(_listing_rsset_journal_binding_candidates(rsset_report))
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


def _listing_all_rows(target_id: str) -> list[object]:
    rows: list[object] = []
    start = 0
    while True:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {"start": [str(start)], "count": [str(_LISTING_SOURCE_CANDIDATE_ROW_COUNT)]},
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
        if _opcode_uses_immediate_as_bit_mask(opcode):
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
                    "autonomous_progress_value": "low",
                    "actionable": True,
                    "stop_reason": None,
                }
            )
    return candidates


def _listing_immediate_runtime_reference_report(rows: list[object]) -> list[dict[str, object]]:
    mapping_rows = [row for row in rows if isinstance(row, Mapping)]
    known_ranges = _known_listing_address_ranges(mapping_rows)
    candidates: list[dict[str, object]] = []
    for row in mapping_rows:
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        element_row = dict(row)
        if not isinstance(element_row.get("stable_key"), str) and isinstance(element_row.get("row_key"), str):
            element_row["stable_key"] = element_row["row_key"]
        for context in listing_element_contexts(element_row):
            if context.get("element_kind") != "immediate":
                continue
            value = context.get("value")
            if not isinstance(value, int):
                continue
            if value < _MIN_IMMEDIATE_REFERENCE_VALUE:
                continue
            matches = _matching_known_address_ranges(value, known_ranges)
            if not matches:
                continue
            row_key = cast(dict[str, object], locator).get("row_key")
            operand_index = context.get("operand_index")
            candidate_id = f"immediate-runtime-ref:{row_key}:{operand_index}:{value:08X}"
            candidates.append(
                _immediate_reference_candidate_payload(
                    candidate_id=candidate_id,
                    row=row,
                    locator=cast(dict[str, object], locator),
                    row_key=row_key,
                    context=context,
                    value=value,
                    matches=matches,
                )
            )
    return sorted(
        candidates,
        key=lambda candidate: (
            str(candidate.get("status")),
            str(candidate.get("candidate_id")),
        ),
    )


def _immediate_reference_candidate_payload(
    *,
    candidate_id: str,
    row: Mapping[str, object],
    locator: dict[str, object],
    row_key: object,
    context: Mapping[str, object],
    value: int,
    matches: list[dict[str, object]],
) -> dict[str, object]:
    accepted = len(matches) == 1
    target = matches[0]["target"] if accepted else None
    source_family = matches[0]["source_family"] if accepted else "ambiguous"
    candidate: dict[str, object] = {
        "id": candidate_id,
        "candidate_id": candidate_id,
        "kind": "immediate_runtime_reference",
        "status": "accepted" if accepted else "conflicting",
        "source_family": source_family,
        "target": target,
        "source_range": matches[0] if accepted else None,
        "conflicts": [] if accepted else matches,
        "instruction_context": {
            "locator": dict(locator),
            "row_key": row_key,
            "opcode": row.get("opcode_or_directive"),
            "operand_text": row.get("operand_text"),
            "element_id": context.get("element_id"),
            "operand_index": context.get("operand_index"),
            "value": value,
            "width_bits": context.get("width_bits"),
            "width_bytes": context.get("width_bytes"),
        },
        "current_render_state": {
            "row_kind": row.get("kind"),
            "text": row.get("text"),
            "operand_text": row.get("operand_text"),
        },
        "write_policy": _immediate_reference_report_only_policy(
            _immediate_reference_report_only_reason(
                accepted=accepted,
                source_family=source_family,
                context=context,
                target=target,
                value=value,
            )
        ),
    }
    if accepted and isinstance(target, dict):
        target_hunk = _int_or_none(target.get("section_index"))
        target_offset = _int_or_none(target.get("source_offset"))
        width = _int_or_none(context.get("width_bytes"))
        if (
            target_hunk is not None
            and target_offset is not None
            and width in {1, 2, 4}
            and 0 <= value < (1 << (width * 8))
            and source_family in {"runtime_address", "runtime_address_ref"}
        ):
            symbol = _immediate_reference_symbol(target_hunk, target_offset, _int_or_none(target.get("runtime_address")))
            parameters: dict[str, object] = {
                "immediate_ref_id": candidate_id.removeprefix("immediate-runtime-ref:"),
                "source_family": source_family,
                "source_evidence_status": "accepted",
                "source_evidence_id": candidate_id,
                "source_value": value,
                "width": width,
                "target_hunk": target_hunk,
                "target_offset": target_offset,
                "symbol": symbol,
                "source_range": matches[0],
                "conflicts": [],
            }
            runtime_address = _int_or_none(target.get("runtime_address"))
            if runtime_address is not None:
                parameters["runtime_address"] = runtime_address
            candidate.update(
                {
                    "safe_to_mutate": True,
                    "locator": dict(locator),
                    "element_id": context.get("element_id"),
                    "operand_index": context.get("operand_index"),
                    "write_policy": _immediate_reference_interpretation_policy(),
                    "suggested_action_kinds": ["immediate_ref.interpret"],
                    "default_verifier": _IMMEDIATE_REF_VERIFIER,
                    "parameters": parameters,
                }
            )
    return candidate


def _immediate_reference_symbol(target_hunk: int, target_offset: int, runtime_address: int | None) -> str:
    if runtime_address is not None:
        return f"imm_ref_h{target_hunk}_{target_offset:08X}_rt_{runtime_address:08X}"
    return f"imm_ref_h{target_hunk}_{target_offset:08X}"


def _known_listing_address_ranges(rows: list[Mapping[str, object]]) -> list[dict[str, object]]:
    ranges: list[dict[str, object]] = []
    for row in rows:
        locator = row.get("locator")
        locator_payload = locator if isinstance(locator, Mapping) else row
        section_index = _int_or_none(locator_payload.get("section_index"))
        start = _int_or_none(locator_payload.get("start_offset"))
        end = _int_or_none(locator_payload.get("end_offset"))
        if section_index is not None and start is not None and end is not None and end > start:
            ranges.append(
                {
                    "source_family": "source_offset",
                    "section_index": section_index,
                    "start": start,
                    "end": end,
                    "target": {"section_index": section_index, "source_offset": start},
                }
            )
            runtime_address = _int_or_none(row.get("runtime_address"))
            if runtime_address is not None:
                ranges.append(
                    {
                        "source_family": "runtime_address",
                        "section_index": section_index,
                        "source_start": start,
                        "source_end": end,
                        "runtime_start": runtime_address,
                        "runtime_end": runtime_address + (end - start),
                        "target": {
                            "section_index": section_index,
                            "source_offset": start,
                            "runtime_address": runtime_address,
                        },
                    }
                )
        for ref in _mapping_sequence(row.get("runtime_address_refs") or row.get("runtimeAddressRefs")):
            ref_section = _int_or_none(ref.get("target_section_index") or ref.get("targetSectionIndex"))
            ref_offset = _int_or_none(ref.get("target_offset") or ref.get("targetOffset"))
            ref_runtime = _int_or_none(ref.get("runtime_address") or ref.get("runtimeAddress"))
            ref_size = _int_or_none(ref.get("size")) or 1
            if ref_section is None or ref_offset is None or ref_runtime is None or ref_size <= 0:
                continue
            ranges.append(
                {
                    "source_family": "runtime_address_ref",
                    "section_index": ref_section,
                    "source_start": ref_offset,
                    "source_end": ref_offset + ref_size,
                    "runtime_start": ref_runtime,
                    "runtime_end": ref_runtime + ref_size,
                    "data_class": ref.get("data_class") or ref.get("dataClass"),
                    "target": {
                        "section_index": ref_section,
                        "source_offset": ref_offset,
                        "runtime_address": ref_runtime,
                    },
                }
            )
    return ranges


def _matching_known_address_ranges(value: int, known_ranges: list[dict[str, object]]) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    for address_range in known_ranges:
        source_family = address_range.get("source_family")
        if source_family == "source_offset":
            start = _int_or_none(address_range.get("start"))
            end = _int_or_none(address_range.get("end"))
            if start is None or end is None or not start <= value < end:
                continue
            matched = dict(address_range)
            matched["target"] = {
                "section_index": address_range.get("section_index"),
                "source_offset": value,
            }
            matches.append(matched)
            continue
        runtime_start = _int_or_none(address_range.get("runtime_start"))
        runtime_end = _int_or_none(address_range.get("runtime_end"))
        source_start = _int_or_none(address_range.get("source_start"))
        if runtime_start is None or runtime_end is None or source_start is None or not runtime_start <= value < runtime_end:
            continue
        matched = dict(address_range)
        matched["target"] = {
            "section_index": address_range.get("section_index"),
            "source_offset": source_start + (value - runtime_start),
            "runtime_address": value,
        }
        matches.append(matched)
    return matches


def _immediate_reference_interpretation_policy() -> dict[str, object]:
    return {
        "status": "supported",
        "symbolic_reference_allowed": True,
        "rendering_allowed": True,
        "command_support": {
            "status": "available",
            "command_id": "immediate_ref.interpret",
        },
        "verifier_support": {
            "status": "available",
            "verifier": _IMMEDIATE_REF_VERIFIER,
        },
        "reason": "accepted conflict-free immediate references can be promoted through command and verifier gates",
    }


def _immediate_reference_report_only_policy(reason: str) -> dict[str, object]:
    return {
        "status": "report_only",
        "symbolic_reference_allowed": False,
        "rendering_allowed": False,
        "command_support": {
            "status": "unavailable",
            "command_id": "immediate_ref.interpret",
        },
        "verifier_support": {
            "status": "unavailable",
            "verifier": _IMMEDIATE_REF_VERIFIER,
        },
        "reason": reason,
    }


def _immediate_reference_report_only_reason(
    *,
    accepted: bool,
    source_family: object,
    context: Mapping[str, object],
    target: object,
    value: int,
) -> str:
    if not accepted:
        return "conflicting immediate reference ranges require disambiguation before mutation"
    if source_family not in {"runtime_address", "runtime_address_ref"}:
        return "source-offset immediate matches are report-only until accepted runtime-address provenance exists"
    if not isinstance(target, Mapping):
        return "matched immediate reference range lacks a concrete target"
    target_hunk = _int_or_none(target.get("section_index"))
    target_offset = _int_or_none(target.get("source_offset"))
    if target_hunk is None or target_offset is None:
        return "matched immediate reference range lacks target hunk or offset"
    width = _int_or_none(context.get("width_bytes"))
    if width not in {1, 2, 4}:
        return "immediate operand width is unsupported for interpreted-reference mutation"
    if not 0 <= value < (1 << (width * 8)):
        return "immediate value does not fit the operand width for rendered symbolic replacement"
    return "immediate reference lacks command-backed runtime-address evidence"


def _immediate_reference_mutation_gate(candidates: Sequence[Mapping[str, object]]) -> dict[str, object]:
    command_candidate_count = sum(
        1 for candidate in candidates if _immediate_reference_candidate_is_command_backed(candidate)
    )
    report_only_candidate_count = len(candidates) - command_candidate_count
    if command_candidate_count:
        status = "available"
        reason = "command-backed immediate reference candidates are available"
    elif report_only_candidate_count:
        status = "blocked"
        reason = "remaining immediate reference candidates are report-only"
    else:
        status = "blocked"
        reason = "no immediate reference candidates are available"
    return {
        "status": status,
        "safe_to_mutate": command_candidate_count > 0,
        "command_id": "immediate_ref.interpret",
        "command_candidate_count": command_candidate_count,
        "report_only_candidate_count": report_only_candidate_count,
        "reason": reason,
    }


def _immediate_reference_candidate_is_command_backed(candidate: Mapping[str, object]) -> bool:
    actions = candidate.get("suggested_action_kinds")
    parameters = candidate.get("parameters")
    return (
        isinstance(actions, Sequence)
        and not isinstance(actions, str)
        and "immediate_ref.interpret" in actions
        and isinstance(parameters, Mapping)
    )


def _source_offset_immediate_packet_from_candidates(
    target_id: str,
    candidates: Sequence[Mapping[str, object]],
    *,
    candidate_id: str,
) -> dict[str, object]:
    for candidate in candidates:
        if candidate.get("candidate_id") == candidate_id:
            return _source_offset_immediate_packet_from_candidate(target_id, candidate)
    return {
        "packet_kind": "source_offset_immediate_evidence_packet",
        "schema_version": 1,
        "target_id": target_id,
        "candidate_id": candidate_id,
        "status": "not_found",
        "safe_to_mutate": False,
        "mutation_policy": "read_only",
    }


def _source_offset_immediate_packet_from_candidate(
    target_id: str,
    candidate: Mapping[str, object],
) -> dict[str, object]:
    instruction = candidate.get("instruction_context")
    instruction = instruction if isinstance(instruction, Mapping) else {}
    locator = instruction.get("locator")
    locator = locator if isinstance(locator, Mapping) else {}
    candidate_id = str(candidate.get("candidate_id") or candidate.get("id") or "")
    identity = _immediate_packet_selected_identity(target_id, candidate_id, instruction, locator)
    interpretations = _immediate_packet_interpretations(candidate)
    command_backed = _immediate_reference_candidate_is_command_backed(candidate)
    blockers = _source_offset_immediate_packet_blockers(candidate, command_backed)
    status = "blocked" if blockers else "accepted"
    return {
        "packet_kind": "source_offset_immediate_evidence_packet",
        "schema_version": 1,
        "packet_id": f"source-offset-immediate-packet:{candidate_id}",
        "target_id": target_id,
        "candidate_id": candidate_id,
        "candidate_family": "source_offset_immediate",
        "status": status,
        "selected_identity": identity,
        "literal": {
            "value": instruction.get("value"),
            "value_hex": f"{instruction['value']:X}" if isinstance(instruction.get("value"), int) else None,
            "width_bits": instruction.get("width_bits"),
            "width_bytes": instruction.get("width_bytes"),
            "signedness": "unknown",
            "syntax": instruction.get("operand_text"),
        },
        "evidence_lanes": {
            "instruction": dict(instruction),
            "possible_interpretations": interpretations,
            "landing_range": _source_offset_immediate_landing_range(candidate, interpretations),
            "local_dataflow": _source_offset_immediate_dataflow(candidate),
            "downstream_dataflow": {"status": "unavailable", "blocker": "downstream dataflow query is not available"},
            "same_literal_context": {
                "status": "report_only",
                "reason": "same literal matches do not prove source-offset provenance",
            },
        },
        "conflicts": _source_offset_immediate_conflict_state(candidate),
        "blockers": blockers,
        "render_intent": {
            "intent": "renders" if command_backed else "analysis_only",
            "status": "blocked" if blockers else "ready",
            "render_effect": "none",
            "future_render_effect": "selected_operand_only",
        },
        "command_gate": {
            "command_id": "immediate_ref.interpret",
            "candidate_command_available": command_backed,
            "enabled": False,
            "safe_to_mutate": False,
            "missing_gates": ["packet_read_only_no_writes", *blockers],
        },
        "decision": {
            "writes_enabled": False,
            "available_actions": ["accept_fact", "defer_fact", "reject_fact"],
            "state": "read_only_metadata",
        },
        "safe_to_mutate": False,
        "mutation_policy": "read_only",
    }


def _immediate_packet_selected_identity(
    target_id: str,
    candidate_id: str,
    instruction: Mapping[str, object],
    locator: Mapping[str, object],
) -> dict[str, object]:
    hunk = _int_or_none(locator.get("section_index")) or 0
    addr = _int_or_none(locator.get("start_offset"))
    operand_index = _int_or_none(instruction.get("operand_index"))
    identity: dict[str, object] = {
        "target_id": target_id,
        "segment_id": f"s{hunk}",
        "hunk": hunk,
        "candidate_id": candidate_id,
    }
    if addr is not None:
        identity["addr"] = addr
        identity["address_hex"] = f"{addr:08X}"
        identity["selected_use_id"] = f"s{hunk}:{addr:08X}:op{operand_index}" if operand_index is not None else f"s{hunk}:{addr:08X}"
    if operand_index is not None:
        identity["operand_index"] = operand_index
    for key in ("row_key", "element_id", "width_bytes", "width_bits", "opcode"):
        value = instruction.get(key)
        if value is not None:
            identity[key] = value
    return identity


def _immediate_packet_interpretations(candidate: Mapping[str, object]) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    conflicts = candidate.get("conflicts")
    if isinstance(conflicts, Sequence) and not isinstance(conflicts, str) and conflicts:
        matches.extend(dict(item) for item in conflicts if isinstance(item, Mapping))
    source_range = candidate.get("source_range")
    if not matches and isinstance(source_range, Mapping):
        matches.append(dict(source_range))
    interpretations: list[dict[str, object]] = []
    for match in matches:
        target = match.get("target")
        target = target if isinstance(target, Mapping) else {}
        interpretations.append(
            {
                "kind": match.get("source_family"),
                "source_offset": target.get("source_offset"),
                "runtime_address": target.get("runtime_address"),
                "source_range": match,
                "provenance": "range_match_only",
                "durable": False,
            }
        )
    return interpretations


def _source_offset_immediate_landing_range(
    candidate: Mapping[str, object],
    interpretations: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    target = candidate.get("target")
    target = target if isinstance(target, Mapping) else {}
    source_range = candidate.get("source_range")
    source_range = source_range if isinstance(source_range, Mapping) else {}
    return {
        "target": dict(target),
        "classification": source_range.get("classification") or source_range.get("row_kind") or "unknown",
        "inside_loaded_binary": bool(interpretations),
        "source_range": dict(source_range),
    }


def _source_offset_immediate_dataflow(candidate: Mapping[str, object]) -> dict[str, object]:
    render_state = candidate.get("current_render_state")
    render_state = render_state if isinstance(render_state, Mapping) else {}
    return {
        "status": "listing_instruction_only",
        "opcode": (candidate.get("instruction_context") or {}).get("opcode")
        if isinstance(candidate.get("instruction_context"), Mapping)
        else None,
        "operand_text": render_state.get("operand_text"),
        "row_text": render_state.get("text"),
    }


def _source_offset_immediate_conflict_state(candidate: Mapping[str, object]) -> dict[str, object]:
    conflicts = candidate.get("conflicts")
    if isinstance(conflicts, Sequence) and not isinstance(conflicts, str) and conflicts:
        return {"status": "conflicting", "explicit_empty": False, "items": list(conflicts)}
    if candidate.get("source_family") == "source_offset":
        return {"status": "none_reported", "explicit_empty": True, "items": []}
    return {"status": "unknown", "explicit_empty": False, "items": []}


def _source_offset_immediate_packet_blockers(
    candidate: Mapping[str, object],
    command_backed: bool,
) -> list[str]:
    blockers: list[str] = []
    source_family = candidate.get("source_family")
    if source_family == "source_offset":
        blockers.extend(
            [
                "same_literal_only_not_durable_provenance",
                "missing_accepted_runtime_address_provenance",
                "missing_source_offset_decision_replay_support",
                "missing_source_offset_render_verifier_gate",
            ]
        )
    elif source_family == "ambiguous" or candidate.get("status") == "conflicting":
        blockers.extend(["conflicting_immediate_interpretations", "missing_selected_interpretation_decision"])
    elif not command_backed:
        policy = candidate.get("write_policy")
        reason = policy.get("reason") if isinstance(policy, Mapping) else None
        blockers.append(str(reason or "missing_immediate_reference_command_gate"))
    return blockers


def _listing_a5_hardware_lifetime_report(rows: list[object]) -> dict[str, object]:
    definitions: list[dict[str, object]] = []
    uses: list[dict[str, object]] = []
    clobbers: list[dict[str, object]] = []
    boundaries: list[dict[str, object]] = []
    active_definition: dict[str, object] | None = None
    lifetime_index = 0
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        locator = row.get("locator")
        if not _is_full_listing_locator(locator):
            continue
        if boundary := _a5_save_restore_boundary(row):
            boundaries.append({**boundary, "locator": dict(cast(dict[str, object], locator))})
        definition = _a5_definition(row)
        if definition is not None:
            definition["locator"] = dict(cast(dict[str, object], locator))
            definitions.append(definition)
            if definition["status"] == "custom_base":
                lifetime_index += 1
                definition["linear_lifetime_id"] = f"a5-linear-lifetime-{lifetime_index}"
                active_definition = definition
            else:
                clobbers.append(definition)
                active_definition = None
        for use in _a5_displacement_uses(row):
            use["locator"] = dict(cast(dict[str, object], locator))
            use["lifetime_status"] = _a5_use_lifetime_status(active_definition, use)
            uses.append(use)
    return {
        "register": "A5",
        "custom_base_address": _AMIGA_CUSTOM_BASE_ADDRESS,
        "evidence_scope": "linear_listing_state",
        "durable_accepted_hardware_base_evidence": False,
        "definitions": definitions,
        "uses": uses,
        "clobbers": clobbers,
        "save_restore_boundaries": boundaries,
        "lifetimes": _a5_lifetime_summaries(definitions, uses),
        "cfg_path_lifetime_report": _listing_a5_cfg_path_lifetime_report(rows, definitions, uses),
        "verifier_gate": _a5_hardware_verifier_gate(),
    }


def _empty_a5_hardware_lifetime_report() -> dict[str, object]:
    return {
        "register": "A5",
        "custom_base_address": _AMIGA_CUSTOM_BASE_ADDRESS,
        "evidence_scope": "linear_listing_state",
        "durable_accepted_hardware_base_evidence": False,
        "definitions": [],
        "uses": [],
        "clobbers": [],
        "save_restore_boundaries": [],
        "lifetimes": [],
        "cfg_path_lifetime_report": _empty_a5_cfg_path_lifetime_report(),
        "verifier_gate": _a5_hardware_verifier_gate(),
    }


def _empty_a5_cfg_path_lifetime_report() -> dict[str, object]:
    return {
        "kind": "a5_cfg_path_lifetime_report",
        "path_model": "conservative_straight_line_cfg",
        "accepted_custom_base_evidence_count": 0,
        "use_count": 0,
        "uses": [],
        "safe_to_mutate": False,
        "mutation_policy": "report_only_requires_render_command_and_verifier",
        "rendering_allowed": False,
        "rendering_gate": _a5_hardware_rendering_gate(0, 0),
    }


def _listing_a5_cfg_path_lifetime_report(
    rows: list[object],
    definitions: list[dict[str, object]],
    uses: list[dict[str, object]],
) -> dict[str, object]:
    mapping_rows = [row for row in rows if isinstance(row, Mapping) and _is_full_listing_locator(row.get("locator"))]
    row_positions = {
        cast(dict[str, object], row["locator"]).get("row_key"): index
        for index, row in enumerate(mapping_rows)
        if isinstance(cast(dict[str, object], row["locator"]).get("row_key"), str)
    }
    custom_definitions = [definition for definition in definitions if definition.get("status") == "custom_base"]
    statuses = [
        _a5_cfg_use_status(use, mapping_rows, row_positions, custom_definitions)
        for use in uses
    ]
    accepted_count = sum(1 for status in statuses if status.get("status") == "accepted_custom_base")
    command_count = sum(1 for status in statuses if _a5_hardware_candidate_is_command_backed(status))
    return {
        "kind": "a5_cfg_path_lifetime_report",
        "path_model": "conservative_straight_line_cfg",
        "accepted_custom_base_evidence_count": accepted_count,
        "use_count": len(statuses),
        "uses": statuses,
        "safe_to_mutate": command_count > 0,
        "mutation_policy": "requires_accepted_path_lifetime_command_verifier_and_exact_round_trip",
        "rendering_allowed": command_count > 0,
        "rendering_gate": _a5_hardware_rendering_gate(accepted_count, command_count),
    }


def _a5_cfg_use_status(
    use: dict[str, object],
    rows: list[Mapping[str, object]],
    row_positions: dict[object, int],
    custom_definitions: list[dict[str, object]],
) -> dict[str, object]:
    use_locator = use.get("locator")
    use_key = use_locator.get("row_key") if isinstance(use_locator, dict) else None
    use_index = row_positions.get(use_key)
    if use_index is None:
        return _a5_cfg_unknown_status(use, None, ["use row is not present in CFG row index"])
    definition = _nearest_prior_a5_custom_definition(use, custom_definitions, row_positions, use_index)
    if definition is None:
        return _a5_cfg_unknown_status(use, None, ["no prior A5 _custom definition reaches selected use"])
    definition_locator = definition.get("locator")
    definition_key = definition_locator.get("row_key") if isinstance(definition_locator, dict) else None
    definition_index = row_positions.get(definition_key)
    if definition_index is None:
        return _a5_cfg_unknown_status(use, definition, ["definition row is not present in CFG row index"])
    blockers = _a5_cfg_slice_blockers(rows[definition_index + 1 : use_index])
    if not _a5_effective_hardware_register_candidate(definition, use):
        return _a5_cfg_conflicting_status(use, definition, ["A5 displacement is outside custom register range"])
    if blockers:
        return _a5_cfg_unknown_status(use, definition, blockers)
    return _a5_cfg_accepted_status(use, definition)


def _nearest_prior_a5_custom_definition(
    use: dict[str, object],
    definitions: list[dict[str, object]],
    row_positions: dict[object, int],
    use_index: int,
) -> dict[str, object] | None:
    use_locator = use.get("locator")
    use_hunk = use_locator.get("section_index") if isinstance(use_locator, dict) else None
    candidates: list[tuple[int, dict[str, object]]] = []
    for definition in definitions:
        locator = definition.get("locator")
        if not isinstance(locator, dict):
            continue
        if use_hunk is not None and locator.get("section_index") != use_hunk:
            continue
        position = row_positions.get(locator.get("row_key"))
        if position is not None and position < use_index:
            candidates.append((position, definition))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _a5_cfg_slice_blockers(rows: list[Mapping[str, object]]) -> list[str]:
    blockers: list[str] = []
    for row in rows:
        if _a5_save_restore_boundary(row) is not None:
            blockers.append("A5 save/restore boundary requires interprocedural lifetime proof")
        definition = _a5_definition(row)
        if definition is not None:
            blockers.append("A5 is redefined before selected use")
        opcode = _row_opcode_base(row)
        if opcode in {"jsr", "bsr"}:
            blockers.append("call before selected use may clobber A5")
        elif opcode in {"jmp", "bra"} or _is_conditional_branch_opcode(opcode):
            blockers.append("branch before selected use requires full CFG path proof")
        elif opcode in {"rts", "rte", "rtr"}:
            blockers.append("return before selected use breaks local path proof")
    return sorted(set(blockers))


def _a5_cfg_unknown_status(
    use: dict[str, object],
    definition: dict[str, object] | None,
    blockers: list[str],
) -> dict[str, object]:
    return _a5_cfg_status_payload(use, definition, "unknown", blockers, accepted=False)


def _a5_cfg_conflicting_status(
    use: dict[str, object],
    definition: dict[str, object] | None,
    blockers: list[str],
) -> dict[str, object]:
    return _a5_cfg_status_payload(use, definition, "conflicting", blockers, accepted=False)


def _a5_cfg_accepted_status(use: dict[str, object], definition: dict[str, object]) -> dict[str, object]:
    payload = _a5_cfg_status_payload(use, definition, "accepted_custom_base", [], accepted=True)
    symbol_operand_blocker = _a5_hardware_ref_symbol_operand_blocker(payload)
    if symbol_operand_blocker is not None:
        payload["symbol_operand_blocked_reason"] = symbol_operand_blocker
        payload["render_mode"] = "entry_comment"
    else:
        payload["render_mode"] = "symbol_operand"
    parameters = _a5_hardware_ref_parameters(payload)
    if parameters is not None:
        payload["suggested_action_kinds"] = ["a5_hardware_ref.interpret"]
        payload["default_verifier"] = _A5_HARDWARE_REF_VERIFIER
        payload["parameters"] = parameters
    return payload


def _a5_cfg_status_payload(
    use: dict[str, object],
    definition: dict[str, object] | None,
    status: str,
    blockers: list[str],
    *,
    accepted: bool,
) -> dict[str, object]:
    scope = _a5_cfg_path_lifetime_scope(use, definition, accepted=accepted)
    custom_base_offset = _a5_definition_custom_base_offset(definition)
    hardware_register_offset = _a5_effective_hardware_register_offset(definition, use)
    payload = {
        "status": status,
        "accepted_hardware_base_evidence": accepted,
        "source_family": "amiga_custom_base" if accepted else "candidate_amiga_custom_base",
        "source_evidence_id": scope.get("source_evidence_id"),
        "path_lifetime_scope": scope,
        "definition_locator": definition.get("locator") if isinstance(definition, dict) else None,
        "use_locator": use.get("locator"),
        "operand_index": use.get("operand_index"),
        "displacement": use.get("displacement"),
        "custom_base_offset": custom_base_offset,
        "hardware_register_offset": hardware_register_offset,
        "hardware_register_candidate": _a5_effective_hardware_register_candidate(definition, use),
        "blockers": blockers,
    }
    return {key: value for key, value in payload.items() if value not in (None, [])}


def _a5_hardware_candidate_is_command_backed(candidate: Mapping[str, object]) -> bool:
    actions = candidate.get("suggested_action_kinds")
    parameters = candidate.get("parameters")
    return (
        isinstance(actions, Sequence)
        and not isinstance(actions, str)
        and "a5_hardware_ref.interpret" in actions
        and isinstance(parameters, Mapping)
    )


def _existing_a5_hardware_ref_index(
    target_id: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, dict[str, object]]:
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception:
        return {}
    manual_state = project.manual_state
    refs = manual_state.get("a5_hardware_refs") if isinstance(manual_state, Mapping) else None
    if not isinstance(refs, Sequence) or isinstance(refs, str):
        return {}
    result: dict[str, dict[str, object]] = {}
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        status = ref.get("source_evidence_status")
        if isinstance(status, str) and status not in _ACCEPTED_PROVENANCE_STATUSES:
            continue
        for key in ("source_evidence_id", "a5_hardware_ref_id"):
            value = ref.get(key)
            if isinstance(value, str) and value:
                result[value] = ref
    return result


def _a5_hardware_lifetime_report_with_existing_refs(
    report: dict[str, object],
    existing_refs: Mapping[str, dict[str, object]],
) -> dict[str, object]:
    if not existing_refs:
        return report
    cfg_report = report.get("cfg_path_lifetime_report")
    if not isinstance(cfg_report, dict):
        return report
    uses = cfg_report.get("uses")
    if not isinstance(uses, Sequence) or isinstance(uses, str):
        return report
    updated_uses: list[object] = []
    for use in uses:
        if not isinstance(use, dict):
            updated_uses.append(use)
            continue
        updated = dict(use)
        existing = _existing_a5_hardware_ref_for_candidate(updated, existing_refs)
        if existing is not None:
            updated.pop("suggested_action_kinds", None)
            updated.pop("default_verifier", None)
            updated.pop("parameters", None)
            updated["existing_manual_state"] = {
                key: existing[key]
                for key in ("a5_hardware_ref_id", "source_evidence_id", "owner_action_id")
                if isinstance(existing.get(key), str)
            }
        updated_uses.append(updated)
    accepted_count = sum(
        1 for use in updated_uses if isinstance(use, Mapping) and use.get("status") == "accepted_custom_base"
    )
    command_count = sum(
        1 for use in updated_uses if isinstance(use, Mapping) and _a5_hardware_candidate_is_command_backed(use)
    )
    updated_cfg = dict(cfg_report)
    updated_cfg["uses"] = updated_uses
    updated_cfg["accepted_custom_base_evidence_count"] = accepted_count
    updated_cfg["safe_to_mutate"] = command_count > 0
    updated_cfg["rendering_allowed"] = command_count > 0
    updated_cfg["rendering_gate"] = _a5_hardware_rendering_gate(accepted_count, command_count)
    updated_report = dict(report)
    updated_report["cfg_path_lifetime_report"] = updated_cfg
    return updated_report


def _existing_a5_hardware_ref_for_candidate(
    candidate: Mapping[str, object],
    existing_refs: Mapping[str, dict[str, object]],
) -> dict[str, object] | None:
    parameters = candidate.get("parameters")
    for value in (
        candidate.get("source_evidence_id"),
        parameters.get("source_evidence_id") if isinstance(parameters, Mapping) else None,
        parameters.get("a5_hardware_ref_id") if isinstance(parameters, Mapping) else None,
    ):
        if isinstance(value, str) and value in existing_refs:
            return existing_refs[value]
    return None


def _a5_path_lifetime_packet_from_report(
    target_id: str,
    lifetime_report: Mapping[str, object],
    *,
    selected_use_id: str,
) -> dict[str, object]:
    cfg_report = lifetime_report.get("cfg_path_lifetime_report")
    uses = cfg_report.get("uses") if isinstance(cfg_report, Mapping) else None
    if not isinstance(uses, Sequence) or isinstance(uses, str):
        uses = []
    selected = _a5_path_lifetime_packet_selected_use(uses, selected_use_id)
    if selected is None:
        return {
            "packet_kind": "a5_path_lifetime_evidence_packet",
            "schema_version": 1,
            "target_id": target_id,
            "selected_use_query": selected_use_id,
            "status": "selected_use_not_found",
            "safe_to_mutate": False,
            "mutation_policy": "read_only",
        }
    return _a5_path_lifetime_packet_from_use(target_id, selected)


def _a5_path_lifetime_packet_selected_use(
    uses: Sequence[object],
    selected_use_id: str,
) -> dict[str, object] | None:
    query = _parse_rsset_selected_use_id(selected_use_id)
    for raw_use in uses:
        if not isinstance(raw_use, Mapping):
            continue
        use = dict(raw_use)
        identity = _a5_path_lifetime_selected_identity("", use)
        if _rsset_selected_identity_matches_query(identity, query) or identity.get("selected_use_id") == selected_use_id:
            return use
    return None


def _a5_path_lifetime_packet_from_use(
    target_id: str,
    use: Mapping[str, object],
) -> dict[str, object]:
    identity = _a5_path_lifetime_selected_identity(target_id, use)
    blockers = _a5_path_lifetime_packet_blockers(use)
    command_backed = _a5_hardware_candidate_is_command_backed(use)
    existing_manual = use.get("existing_manual_state")
    accepted = use.get("status") == "accepted_custom_base"
    status = "accepted" if accepted and not blockers else "blocked"
    if isinstance(existing_manual, Mapping) and accepted:
        status = "accepted_existing_manual_state"
    return {
        "packet_kind": "a5_path_lifetime_evidence_packet",
        "schema_version": 1,
        "packet_id": f"a5-path-lifetime-packet:{identity.get('selected_use_id', 'unknown')}",
        "target_id": target_id,
        "candidate_family": "a5_hardware_base",
        "status": status,
        "selected_identity": identity,
        "evidence_lanes": {
            "base_setup": {
                "base_register": "A5",
                "definition_locator": use.get("definition_locator"),
                "computed_base_expression": _a5_computed_base_expression(use),
                "custom_base_offset": use.get("custom_base_offset", 0),
            },
            "path_lifetime": {
                "scope": use.get("path_lifetime_scope"),
                "cfg_reachability": "straight_line_cfg" if accepted else "unproven",
                "a5_clobber_before_use": False if accepted else "unknown",
                "lifetime_end": "selected_use",
                "blockers": use.get("blockers", []),
            },
            "custom_delta": {
                "displacement": use.get("displacement"),
                "hardware_register_offset": use.get("hardware_register_offset"),
                "symbol": (use.get("parameters") or {}).get("symbol") if isinstance(use.get("parameters"), Mapping) else None,
            },
            "existing_manual_state": dict(existing_manual) if isinstance(existing_manual, Mapping) else None,
        },
        "conflicts": {"status": "none", "explicit_empty": True, "items": []}
        if accepted
        else {"status": "unknown", "explicit_empty": False, "items": []},
        "blockers": blockers,
        "render_intent": {
            "intent": "renders",
            "status": "ready" if command_backed else "blocked",
            "render_mode": use.get("render_mode"),
            "unsafe_forms": _a5_path_lifetime_unsafe_forms(use),
            "future_render_effect": "selected_operand_or_entry_comment",
        },
        "verifier_plan": {
            "generated_source": {"status": "available" if command_backed else "blocked"},
            "exact_round_trip": {"status": "required_for_output_affecting_mutation"},
            "verifier": _A5_HARDWARE_REF_VERIFIER,
        },
        "command_gate": {
            "command_id": "a5_hardware_ref.interpret",
            "candidate_command_available": command_backed,
            "enabled": False,
            "safe_to_mutate": False,
            "missing_gates": ["packet_read_only_no_writes", *blockers],
        },
        "decision": {
            "writes_enabled": False,
            "available_actions": ["accept_fact", "defer_fact", "reject_fact"],
            "state": "read_only_metadata",
        },
        "safe_to_mutate": False,
        "mutation_policy": "read_only",
    }


def _a5_path_lifetime_selected_identity(target_id: str, use: Mapping[str, object]) -> dict[str, object]:
    locator = use.get("use_locator")
    locator = locator if isinstance(locator, Mapping) else {}
    hunk = _int_or_none(locator.get("section_index")) or 0
    addr = _int_or_none(locator.get("start_offset"))
    operand_index = _int_or_none(use.get("operand_index"))
    identity: dict[str, object] = {
        "target_id": target_id,
        "segment_id": f"s{hunk}",
        "hunk": hunk,
        "base_register": "A5",
    }
    if addr is not None:
        identity["addr"] = addr
        identity["address_hex"] = f"{addr:08X}"
        identity["selected_use_id"] = f"s{hunk}:{addr:08X}:op{operand_index}" if operand_index is not None else f"s{hunk}:{addr:08X}"
    if operand_index is not None:
        identity["operand_index"] = operand_index
    for key in ("displacement", "custom_base_offset", "hardware_register_offset", "source_evidence_id"):
        value = use.get(key)
        if value is not None:
            identity[key] = value
    return identity


def _a5_computed_base_expression(use: Mapping[str, object]) -> str:
    offset = _int_or_none(use.get("custom_base_offset")) or 0
    return "_custom" if offset == 0 else f"_custom+${offset:04X}"


def _a5_path_lifetime_unsafe_forms(use: Mapping[str, object]) -> list[str]:
    blocker = use.get("symbol_operand_blocked_reason")
    if isinstance(blocker, str) and blocker:
        return ["address_mode_changing_symbol_operand"]
    return []


def _a5_path_lifetime_packet_blockers(use: Mapping[str, object]) -> list[str]:
    blockers = list(_string_sequence(use.get("blockers")))
    if use.get("status") != "accepted_custom_base":
        blockers.append("missing_accepted_path_lifetime_scope")
    if isinstance(use.get("existing_manual_state"), Mapping):
        blockers.append("already_recorded_in_manual_state")
    if not _a5_hardware_candidate_is_command_backed(use):
        blockers.append("missing_command_candidate")
    return sorted(set(blockers))


def _a5_hardware_ref_parameters(candidate: Mapping[str, object]) -> dict[str, object] | None:
    path_lifetime_scope = candidate.get("path_lifetime_scope")
    use_locator = candidate.get("use_locator")
    displacement = _int_or_none(candidate.get("displacement"))
    custom_base_offset = _int_or_none(candidate.get("custom_base_offset"))
    hardware_register_offset = _int_or_none(candidate.get("hardware_register_offset"))
    operand_index = _int_or_none(candidate.get("operand_index"))
    source_evidence_id = candidate.get("source_evidence_id")
    if (
        not isinstance(path_lifetime_scope, Mapping)
        or path_lifetime_scope.get("accepted_hardware_base_evidence") is not True
        or not isinstance(use_locator, Mapping)
        or displacement is None
        or operand_index is None
        or not isinstance(source_evidence_id, str)
        or not source_evidence_id
    ):
        return None
    custom_base_offset = custom_base_offset or 0
    hardware_register_offset = hardware_register_offset if hardware_register_offset is not None else custom_base_offset + displacement
    if hardware_register_offset != custom_base_offset + displacement:
        return None
    symbol = _amiga_custom_register_symbol(hardware_register_offset)
    if symbol is None:
        return None
    addr = _int_or_none(use_locator.get("start_offset"))
    if addr is None:
        return None
    hunk = _int_or_none(use_locator.get("section_index")) or 0
    return {
        "a5_hardware_ref_id": f"a5-hw:{source_evidence_id}",
        "source_family": "amiga_custom_base",
        "source_evidence_status": "accepted",
        "source_evidence_id": source_evidence_id,
        "path_lifetime_scope": dict(path_lifetime_scope),
        "operand_index": operand_index,
        "displacement": displacement,
        "custom_base_offset": custom_base_offset,
        "hardware_register_offset": hardware_register_offset,
        "symbol": symbol,
        "render_mode": _a5_hardware_ref_render_mode(
            {
                "displacement": displacement,
                "custom_base_offset": custom_base_offset,
            }
        ),
        **_a5_hardware_ref_symbol_operand_blocker_payload(
            {
                "displacement": displacement,
                "custom_base_offset": custom_base_offset,
            }
        ),
        "hardware_register_address": _AMIGA_CUSTOM_BASE_ADDRESS + hardware_register_offset,
        "definition_locator": candidate.get("definition_locator"),
        "use_locator": dict(use_locator),
        "conflicts": [],
        "hunk": hunk,
        "addr": addr,
    }


def _a5_hardware_ref_render_mode(candidate: Mapping[str, object]) -> str:
    return "entry_comment" if _a5_hardware_ref_symbol_operand_blocker(candidate) is not None else "symbol_operand"


def _a5_hardware_ref_symbol_operand_blocker_payload(candidate: Mapping[str, object]) -> dict[str, object]:
    blocker = _a5_hardware_ref_symbol_operand_blocker(candidate)
    return {} if blocker is None else {"symbol_operand_blocked_reason": blocker}


def _a5_hardware_ref_symbol_operand_blocker(candidate: Mapping[str, object]) -> str | None:
    displacement = _int_or_none(candidate.get("displacement"))
    custom_base_offset = _int_or_none(candidate.get("custom_base_offset")) or 0
    if displacement == 0:
        return "zero_displacement_a5_operand_requires_address_mode_preserving_rendering"
    if custom_base_offset != 0:
        return "nonzero_a5_custom_base_offset_requires_symbol_delta_rendering"
    return None


@lru_cache(maxsize=1)
def _amiga_custom_register_symbols_by_offset() -> dict[int, str]:
    symbols_path = PROJECT_ROOT / "knowledge" / "amiga_hw_symbols.json"
    payload = json.loads(symbols_path.read_text(encoding="utf-8"))
    rows = payload.get("registers")
    result: dict[int, str] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, Mapping) or row.get("base_symbol") != "_custom":
            continue
        raw_offset = row.get("offset")
        if isinstance(raw_offset, str):
            try:
                offset = int(raw_offset, 0)
            except ValueError:
                offset = None
        else:
            offset = _int_or_none(raw_offset)
        symbols = row.get("symbols")
        if offset is None or not isinstance(symbols, list) or not symbols:
            continue
        first_symbol = symbols[0]
        if isinstance(first_symbol, str) and first_symbol:
            result[offset] = first_symbol
    return result


def _amiga_custom_register_symbol(displacement: int) -> str | None:
    return _amiga_custom_register_symbols_by_offset().get(displacement)


@lru_cache(maxsize=1)
def _amiga_custom_register_offsets_by_symbol() -> dict[str, int]:
    return {
        symbol.lower(): offset
        for offset, symbol in _amiga_custom_register_symbols_by_offset().items()
    }


def _a5_cfg_path_lifetime_scope(
    use: dict[str, object],
    definition: dict[str, object] | None,
    *,
    accepted: bool,
) -> dict[str, object]:
    use_locator = use.get("locator") if isinstance(use.get("locator"), dict) else {}
    definition_locator = definition.get("locator") if isinstance(definition, dict) and isinstance(definition.get("locator"), dict) else {}
    hunk = use_locator.get("section_index")
    definition_addr = definition_locator.get("start_offset")
    use_addr = use_locator.get("start_offset")
    operand_index = use.get("operand_index")
    displacement = use.get("displacement")
    custom_base_offset = _a5_definition_custom_base_offset(definition)
    displacement_id = None
    if isinstance(displacement, int):
        displacement_id = _a5_displacement_id(displacement)
        if custom_base_offset not in (None, 0):
            displacement_id = f"b{custom_base_offset:04X}+{displacement_id}"
    source_evidence_id = (
        f"a5-custom-cfg:h{hunk}:{int(definition_addr):08X}->{int(use_addr):08X}:"
        f"op{int(operand_index)}:{displacement_id}"
        if isinstance(hunk, int)
        and isinstance(definition_addr, int)
        and isinstance(use_addr, int)
        and isinstance(operand_index, int)
        and isinstance(displacement, int)
        and displacement_id is not None
        else "a5-custom-cfg:unknown"
    )
    return {
        "id": source_evidence_id,
        "source_evidence_id": source_evidence_id,
        "kind": "straight_line_cfg_between_definition_and_use",
        "hunk": hunk,
        "definition_locator": definition_locator or None,
        "use_locator": use_locator or None,
        "custom_base_offset": custom_base_offset,
        "hardware_register_offset": _a5_effective_hardware_register_offset(definition, use),
        "accepted_hardware_base_evidence": accepted,
        "path_model": "conservative_straight_line_cfg",
    }


def _row_opcode_base(row: Mapping[str, object]) -> str:
    opcode = str(row.get("opcode_or_directive") or row.get("opcode") or "").strip().lower()
    return opcode.split(".", 1)[0]


def _is_conditional_branch_opcode(opcode: str) -> bool:
    return opcode in {
        "bcc",
        "bcs",
        "beq",
        "bge",
        "bgt",
        "bhs",
        "bhi",
        "ble",
        "blo",
        "bls",
        "blt",
        "bmi",
        "bne",
        "bpl",
        "bvc",
        "bvs",
    }


def _a5_definition(row: Mapping[str, object]) -> dict[str, object] | None:
    if not _row_writes_register(row, "A5"):
        return None
    custom_base_offset = _row_custom_base_offset(row)
    status = "custom_base" if custom_base_offset is not None else "non_custom_or_unknown"
    return {
        "kind": "definition",
        "status": status,
        "opcode": row.get("opcode_or_directive"),
        "text": row.get("text"),
        "custom_base_offset": custom_base_offset,
        "hardware_register_address": _AMIGA_CUSTOM_BASE_ADDRESS + custom_base_offset if custom_base_offset is not None else None,
        "reason": (
            "A5 loaded with an address inside the Amiga custom-chip register block"
            if status == "custom_base"
            else "A5 write is not accepted custom-base evidence"
        ),
    }


def _row_writes_register(row: Mapping[str, object], register: str) -> bool:
    registers = _sequence_values(row.get("operand_registers") or row.get("operandRegisters"))
    accesses = _sequence_values(row.get("operand_accesses") or row.get("operandAccesses"))
    for index, raw_register in enumerate(registers):
        if not isinstance(raw_register, str) or raw_register.upper() != register:
            continue
        access = accesses[index] if index < len(accesses) else None
        if access == "register_write":
            return True
    text = str(row.get("text") or "").lower().replace(" ", "")
    return text.endswith(f",{register.lower()}") or f",{register.lower()}\n" in text


def _row_custom_base_offset(row: Mapping[str, object]) -> int | None:
    text = str(row.get("text") or "").lower()
    text_offset = _custom_base_expression_offset(text)
    if text_offset is not None:
        return text_offset
    operand_parts = row.get("operand_parts") or row.get("operandParts")
    if not isinstance(operand_parts, list | tuple):
        return None
    for part in operand_parts:
        if not isinstance(part, Mapping):
            continue
        symbol = _operand_part_symbol(part)
        if symbol is not None:
            symbol_offset = _custom_base_expression_offset(symbol.lower())
            if symbol_offset is not None:
                return symbol_offset
        value = _int_or_none(part.get("value"))
        if value is not None and _AMIGA_CUSTOM_BASE_ADDRESS <= value <= _AMIGA_CUSTOM_BASE_ADDRESS + _AMIGA_CUSTOM_REGISTER_MAX_OFFSET:
            return value - _AMIGA_CUSTOM_BASE_ADDRESS
    return None


def _a5_displacement_id(displacement: int) -> str:
    if displacement < 0:
        return f"d-{abs(displacement):04X}"
    return f"d{displacement:04X}"


def _operand_part_symbol(part: Mapping[str, object]) -> str | None:
    symbol = part.get("symbol")
    if isinstance(symbol, str) and symbol:
        return symbol
    metadata = part.get("metadata")
    if isinstance(metadata, Mapping):
        symbol = metadata.get("symbol")
        if isinstance(symbol, str) and symbol:
            return symbol
    return None


def _custom_base_expression_offset(expression: str) -> int | None:
    for match in re.finditer(r"\$dff([0-9a-f]{3})|0xdff([0-9a-f]{3})", expression, flags=re.IGNORECASE):
        raw_offset = match.group(1) or match.group(2)
        offset = int(raw_offset, 16)
        if 0 <= offset <= _AMIGA_CUSTOM_REGISTER_MAX_OFFSET:
            return offset
    match = re.search(r"_custom(?:\s*\+\s*([a-z_][\w.]*))?", expression, flags=re.IGNORECASE)
    if match is None:
        return None
    symbol = match.group(1)
    if symbol is None:
        return 0
    symbol = re.sub(r"\.[bwl]$", "", symbol.lower())
    return _amiga_custom_register_offsets_by_symbol().get(symbol)


def _a5_definition_custom_base_offset(definition: dict[str, object] | None) -> int | None:
    if not isinstance(definition, dict):
        return None
    offset = _int_or_none(definition.get("custom_base_offset"))
    return offset if offset is not None else 0


def _a5_effective_hardware_register_offset(
    definition: dict[str, object] | None,
    use: Mapping[str, object],
) -> int | None:
    custom_base_offset = _a5_definition_custom_base_offset(definition)
    displacement = _int_or_none(use.get("displacement"))
    if custom_base_offset is None or displacement is None:
        return None
    return custom_base_offset + displacement


def _a5_effective_hardware_register_candidate(
    definition: dict[str, object] | None,
    use: Mapping[str, object],
) -> bool:
    offset = _a5_effective_hardware_register_offset(definition, use)
    return offset is not None and 0 <= offset <= _AMIGA_CUSTOM_REGISTER_MAX_OFFSET


def _a5_displacement_uses(row: Mapping[str, object]) -> list[dict[str, object]]:
    uses: list[dict[str, object]] = []
    operand_parts = row.get("operand_parts") or row.get("operandParts")
    if not isinstance(operand_parts, list | tuple):
        return uses
    for index, part in enumerate(operand_parts):
        if not isinstance(part, Mapping):
            continue
        base_register = part.get("base_register") or part.get("baseRegister")
        if not isinstance(base_register, str) or base_register.upper() != "A5":
            continue
        displacement = _int_or_none(part.get("displacement"))
        if displacement is None:
            continue
        uses.append(
            {
                "kind": "use",
                "opcode": row.get("opcode_or_directive"),
                "text": row.get("text"),
                "operand_index": _int_or_none(part.get("operand_index") or part.get("operandIndex")) or index,
                "displacement": displacement,
                "hardware_register_candidate": 0 <= displacement <= _AMIGA_CUSTOM_REGISTER_MAX_OFFSET,
            }
        )
    return uses


def _a5_use_lifetime_status(
    active_definition: dict[str, object] | None,
    use: dict[str, object],
) -> dict[str, object]:
    if active_definition is None:
        return {
            "status": "unknown",
            "accepted_hardware_base_evidence": False,
            "evidence_scope": "linear_listing_state",
            "path_lifetime_status": "unknown",
            "reason": "no active _custom base candidate reaches this A5-relative use",
        }
    if not _a5_effective_hardware_register_candidate(active_definition, use):
        return {
            "status": "conflicting",
            "accepted_hardware_base_evidence": False,
            "evidence_scope": "linear_listing_state",
            "path_lifetime_status": "conflicting",
            "reason": "A5 displacement is outside the Amiga custom register offset range",
            "definition": active_definition,
            "hardware_register_offset": _a5_effective_hardware_register_offset(active_definition, use),
        }
    hardware_register_offset = _a5_effective_hardware_register_offset(active_definition, use)
    return {
        "status": "probable_custom_candidate",
        "accepted_hardware_base_evidence": False,
        "evidence_scope": "linear_listing_state",
        "path_lifetime_status": "unknown",
        "custom_base_offset": _a5_definition_custom_base_offset(active_definition),
        "hardware_register_offset": hardware_register_offset,
        "path_lifetime_scope": {
            "id": active_definition.get("linear_lifetime_id"),
            "kind": "linear_listing_between_a5_writes",
            "definition_locator": active_definition.get("locator"),
            "use_locator": use.get("locator"),
            "custom_base_offset": _a5_definition_custom_base_offset(active_definition),
            "hardware_register_offset": hardware_register_offset,
            "accepted_hardware_base_evidence": False,
            "missing_verifier": "control-flow path/lifetime proof that A5 remains _custom on every path to this use",
        },
        "reason": "linear listing state suggests an active A5 _custom base and in-range custom register displacement",
        "definition": active_definition,
    }


def _a5_save_restore_boundary(row: Mapping[str, object]) -> dict[str, object] | None:
    text = str(row.get("text") or "").lower().replace(" ", "")
    if "a5,-(a7)" in text or "a5,-(sp)" in text:
        return {"kind": "save", "text": row.get("text")}
    if "(a7)+,a5" in text or "(sp)+,a5" in text:
        return {"kind": "restore", "text": row.get("text")}
    return None


def _a5_lifetime_summaries(
    definitions: list[dict[str, object]],
    uses: list[dict[str, object]],
) -> list[dict[str, object]]:
    if not definitions and not uses:
        return []
    statuses = {cast(dict[str, object], use.get("lifetime_status")).get("status") for use in uses if isinstance(use.get("lifetime_status"), dict)}
    if "conflicting" in statuses:
        status = "conflicting"
    elif "unknown" in statuses:
        status = "unknown"
    elif "probable_custom_candidate" in statuses:
        status = "probable_custom_candidate"
    else:
        status = "unknown"
    return [{"status": status, "definition_count": len(definitions), "use_count": len(uses)}]


def _a5_hardware_verifier_gate() -> dict[str, object]:
    return {
        "status": "blocked",
        "hardware_register_rendering_allowed": False,
        "requires_accepted_path_lifetime_scope": True,
        "requires_command_support": True,
        "requires_verifier_support": True,
        "reason": "raw A5 displacements remain report-only until path/lifetime scope is accepted and verified",
        "knowledge_source": "knowledge/amiga_hw_reference.md base $DFF000",
    }


def _a5_hardware_rendering_gate(accepted_evidence_count: int, command_candidate_count: int) -> dict[str, object]:
    available = accepted_evidence_count > 0 and command_candidate_count > 0
    missing_gates = []
    if accepted_evidence_count == 0:
        missing_gates.append("accepted_path_lifetime_evidence")
    if command_candidate_count == 0:
        missing_gates.append("command_candidate")
    return {
        "status": "available" if available else "blocked",
        "accepted_path_lifetime_evidence_available": accepted_evidence_count > 0,
        "accepted_path_lifetime_evidence_count": accepted_evidence_count,
        "command_support": {
            "command_id": "a5_hardware_ref.interpret",
            "status": "available",
            "command_candidate_count": command_candidate_count,
        },
        "verifier_support": {
            "verifier": _A5_HARDWARE_REF_VERIFIER,
            "status": "available",
        },
        "exact_round_trip": "required_for_output_affecting_mutation",
        "missing_gates": missing_gates,
    }


def _opcode_uses_immediate_as_bit_mask(opcode: str) -> bool:
    return opcode.lower() in {"andi.b", "eori.b", "ori.b"}


def _listing_data_symbol_candidates(
    rows: list[object],
    *,
    existing_data_symbols: dict[tuple[int, int, int | None], str] | None = None,
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
                target_end = locator_dict.get("end_offset")
                name = _data_ref_symbol_name(data_class, row.get("runtime_address"), hunk, addr)
                text = row.get("text")
                existing_name = _existing_data_symbol_name(existing, hunk, addr, target_end)
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
                            "target_end": target_end,
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
            target_end = context.get("target_end")
            existing_name = _existing_data_symbol_name(existing, target_hunk, target_addr, target_end)
            if existing_name is None and isinstance(context_symbol, str) and context_symbol:
                existing_name = context_symbol
            if existing_name == name:
                continue
            if isinstance(existing_name, str):
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
                    "target_end": target_end,
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


def _data_symbol_identity_key(hunk: int, addr: int, end: object) -> tuple[int, int, int | None]:
    return (hunk, addr, end if isinstance(end, int) else None)


def _existing_data_symbol_name(
    existing: dict[tuple[int, int, int | None], str], hunk: int, addr: int, end: object
) -> str | None:
    exact = existing.get(_data_symbol_identity_key(hunk, addr, end))
    if exact is not None:
        return exact
    return existing.get(_data_symbol_identity_key(hunk, addr, None))


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


def _existing_data_symbol_names(inspect_report: dict[str, object]) -> dict[tuple[int, int, int | None], str]:
    target_state = inspect_report.get("target_state")
    names: dict[tuple[int, int, int | None], str] = {}
    metadata = _effective_target_metadata_from_report(inspect_report)
    if metadata is not None:
        for entity in metadata.seeded_entities:
            if entity.type == "data" and isinstance(entity.name, str) and entity.name:
                names[_data_symbol_identity_key(entity.hunk, entity.addr, entity.end)] = entity.name
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
        end = seed.get("end")
        name = seed.get("name")
        if isinstance(hunk, int) and isinstance(addr, int) and isinstance(name, str) and name:
            names[_data_symbol_identity_key(hunk, addr, end)] = name
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
        return None
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


def _empty_rsset_candidate_report() -> dict[str, object]:
    return {
        "kind": "rsset_candidate_report",
        "candidate_count": 0,
        "use_count": 0,
        "candidates": [],
    }


def _rsset_evidence_packet_from_candidate_report(
    target_id: str,
    candidate_report: Mapping[str, object],
    *,
    candidate_id: str,
    selected_use_id: str | None = None,
) -> dict[str, object]:
    candidate = _rsset_candidate_report_find_candidate(candidate_report, candidate_id)
    if candidate is None:
        return {
            "packet_kind": "rsset_selected_use_evidence_packet",
            "schema_version": 1,
            "target_id": target_id,
            "candidate_id": candidate_id,
            "status": "not_found",
            "safe_to_mutate": False,
            "mutation_policy": "read_only",
        }
    selected_use = _rsset_candidate_packet_selected_use(candidate, selected_use_id)
    if selected_use is None:
        return {
            "packet_kind": "rsset_selected_use_evidence_packet",
            "schema_version": 1,
            "target_id": target_id,
            "candidate_id": candidate_id,
            "selected_use_query": selected_use_id,
            "status": "selected_use_not_found",
            "safe_to_mutate": False,
            "mutation_policy": "read_only",
        }
    return _rsset_evidence_packet_from_candidate(target_id, candidate, selected_use)


def _rsset_candidate_report_find_candidate(
    candidate_report: Mapping[str, object],
    candidate_id: str,
) -> dict[str, object] | None:
    candidates = candidate_report.get("candidates")
    if not isinstance(candidates, Sequence) or isinstance(candidates, str):
        return None
    for candidate in candidates:
        if isinstance(candidate, Mapping) and candidate.get("candidate_id") == candidate_id:
            return dict(candidate)
    return None


def _rsset_candidate_packet_selected_use(
    candidate: Mapping[str, object],
    selected_use_id: str | None,
) -> dict[str, object] | None:
    uses: list[Mapping[str, object]] = []
    selected_use = candidate.get("selected_use")
    if isinstance(selected_use, Mapping):
        uses.append(selected_use)
    same_displacement_uses = candidate.get("same_displacement_uses")
    if isinstance(same_displacement_uses, Sequence) and not isinstance(same_displacement_uses, str):
        uses.extend(use for use in same_displacement_uses if isinstance(use, Mapping))
    if not uses:
        return None
    if selected_use_id is None:
        return dict(uses[0])
    query = _parse_rsset_selected_use_id(selected_use_id)
    for use in uses:
        identity = _rsset_evidence_packet_selected_identity("", use)
        if _rsset_selected_identity_matches_query(identity, query):
            return dict(use)
    return None


def _parse_rsset_selected_use_id(selected_use_id: str) -> dict[str, object]:
    match = re.fullmatch(r"s(?P<hunk>\d+):(?P<addr>[0-9A-Fa-f]{1,8})(?::op(?P<op>\d+))?", selected_use_id)
    if match is None:
        return {"raw": selected_use_id}
    query: dict[str, object] = {
        "hunk": int(match.group("hunk")),
        "addr": int(match.group("addr"), 16),
    }
    operand_index = match.group("op")
    if operand_index is not None:
        query["operand_index"] = int(operand_index)
    return query


def _rsset_selected_identity_matches_query(
    identity: Mapping[str, object],
    query: Mapping[str, object],
) -> bool:
    if "raw" in query:
        return identity.get("selected_use_id") == query.get("raw")
    for key in ("hunk", "addr", "operand_index"):
        if key in query and identity.get(key) != query.get(key):
            return False
    return True


def _rsset_evidence_packet_from_candidate(
    target_id: str,
    candidate: Mapping[str, object],
    selected_use: Mapping[str, object],
) -> dict[str, object]:
    candidate_id = str(candidate.get("candidate_id") or "")
    identity = _rsset_evidence_packet_selected_identity(target_id, selected_use)
    evidence_search = candidate.get("evidence_search") if isinstance(candidate.get("evidence_search"), Mapping) else {}
    blockers = _rsset_evidence_packet_blockers(candidate, evidence_search)
    conflict_state = _rsset_evidence_packet_conflict_state(evidence_search)
    command_gate = _rsset_evidence_packet_command_gate(candidate, blockers)
    status = "blocked" if blockers else str(candidate.get("status") or "unknown")
    selected_use_id = str(identity.get("selected_use_id") or "")
    return {
        "packet_kind": "rsset_selected_use_evidence_packet",
        "schema_version": 1,
        "packet_id": f"rsset-packet:{candidate_id}:{selected_use_id}",
        "target_id": target_id,
        "candidate_id": candidate_id,
        "candidate_family": "rsset_app_base",
        "status": status,
        "selected_identity": identity,
        "evidence_lanes": _rsset_evidence_packet_lanes(candidate, selected_use, evidence_search),
        "blockers": blockers,
        "conflicts": conflict_state,
        "render_intent": {
            "intent": "enables_render",
            "status": "blocked" if blockers else "ready",
            "render_effect": "none",
            "future_render_effect": "selected_operand_only",
        },
        "journal_mutation_gate": candidate.get("journal_mutation_gate")
        or _rsset_journal_mutation_gate(
            target_id=target_id,
            candidate_id=candidate_id,
            selected_use=selected_use,
            layout_context=candidate.get("field_or_app_slot_context")
            if isinstance(candidate.get("field_or_app_slot_context"), Mapping)
            else None,
            journal_decision_evidence=candidate.get("journal_decision_evidence")
            if isinstance(candidate.get("journal_decision_evidence"), Mapping)
            else None,
            exact_round_trip_available=False,
        ),
        "command_gate": command_gate,
        "decision": {
            "writes_enabled": False,
            "available_actions": ["accept_fact", "defer_fact", "reject_fact"],
            "state": "read_only_metadata",
        },
        "safe_to_mutate": False,
        "mutation_policy": "read_only",
    }


def _rsset_evidence_packet_selected_identity(
    target_id: str,
    selected_use: Mapping[str, object],
) -> dict[str, object]:
    hunk = _int_or_none(selected_use.get("hunk")) or 0
    addr = _int_or_none(selected_use.get("addr"))
    operand_index = _int_or_none(selected_use.get("operand_index"))
    displacement = _int_or_none(selected_use.get("displacement"))
    identity: dict[str, object] = {
        "target_id": target_id,
        "segment_id": f"s{hunk}",
        "hunk": hunk,
    }
    if addr is not None:
        identity["addr"] = addr
        identity["address_hex"] = f"{addr:08X}"
    if operand_index is not None:
        identity["operand_index"] = operand_index
    if isinstance(selected_use.get("base_register"), str):
        identity["base_register"] = selected_use["base_register"]
    if displacement is not None:
        identity["displacement"] = displacement
        identity["displacement_hex"] = f"{displacement:04X}"
    for key in ("element_id", "element_kind", "stable_key", "width_bytes", "access"):
        value = selected_use.get(key)
        if value is not None:
            identity[key] = value
    if addr is not None:
        identity["selected_use_id"] = (
            f"s{hunk}:{addr:08X}:op{operand_index}" if operand_index is not None else f"s{hunk}:{addr:08X}"
        )
    return identity


def _rsset_evidence_packet_lanes(
    candidate: Mapping[str, object],
    selected_use: Mapping[str, object],
    evidence_search: Mapping[str, object],
) -> dict[str, object]:
    return {
        "selected_use": dict(selected_use),
        "same_displacement_context": {
            "use_count": candidate.get("same_displacement_use_count", 0),
            "raw_or_weak_use_count": candidate.get("raw_or_weak_use_count", 0),
            "access_counts": candidate.get("access_counts", {}),
            "width_counts": candidate.get("width_counts", {}),
        },
        "field_or_app_slot_context": candidate.get("field_or_app_slot_context"),
        "accepted_base_evidence": {
            "status": evidence_search.get("status", "unknown"),
            "accepted_count": evidence_search.get("accepted_base_evidence_count", 0),
            "accepted": evidence_search.get("accepted_base_evidence", []),
            "rejected_count": evidence_search.get("rejected_evidence_count", 0),
            "rejected": evidence_search.get("rejected_evidence", []),
            "missing_proof": evidence_search.get("missing_proof", []),
        },
        "journal_decision_evidence": candidate.get("journal_decision_evidence")
        or evidence_search.get("journal_decision_evidence")
        or _unavailable_rsset_journal_decision_evidence(),
        "journal_mutation_gate": candidate.get("journal_mutation_gate"),
    }


def _rsset_evidence_packet_blockers(
    candidate: Mapping[str, object],
    evidence_search: Mapping[str, object],
) -> list[str]:
    blockers = list(_string_sequence(candidate.get("missing_gates")))
    journal_gate = candidate.get("journal_mutation_gate")
    if isinstance(journal_gate, Mapping) and journal_gate.get("ready_for_039") is True:
        return blockers
    accepted_count = _int_or_none(evidence_search.get("accepted_base_evidence_count")) or 0
    if accepted_count == 0:
        for blocker in (
            "missing_accepted_base_evidence",
            "missing_selected_a6_base_identity",
            "missing_selected_use_path_lifetime_scope",
            "missing_explicit_empty_conflicts",
        ):
            if blocker not in blockers:
                blockers.append(blocker)
    elif not _rsset_evidence_search_has_explicit_empty_conflicts(evidence_search):
        blockers.append("missing_explicit_empty_conflicts")
    return blockers


def _rsset_evidence_packet_conflict_state(evidence_search: Mapping[str, object]) -> dict[str, object]:
    if _rsset_evidence_search_has_explicit_empty_conflicts(evidence_search):
        return {"status": "explicit_empty", "explicit_empty": True, "items": []}
    rejected = evidence_search.get("rejected_evidence")
    conflict_reasons = [
        ref.get("reason")
        for ref in rejected
        if isinstance(ref, Mapping)
        and isinstance(ref.get("reason"), str)
        and "conflict" in cast(str, ref.get("reason"))
    ] if isinstance(rejected, Sequence) and not isinstance(rejected, str) else []
    return {
        "status": "blocked" if conflict_reasons else "unknown",
        "explicit_empty": False,
        "items": [],
        "blockers": conflict_reasons,
    }


def _rsset_evidence_search_has_explicit_empty_conflicts(evidence_search: Mapping[str, object]) -> bool:
    accepted = evidence_search.get("accepted_base_evidence")
    if not isinstance(accepted, Sequence) or isinstance(accepted, str):
        return False
    return any(isinstance(ref, Mapping) and ref.get("conflicts") == [] for ref in accepted)


def _rsset_evidence_packet_command_gate(
    candidate: Mapping[str, object],
    blockers: list[str],
) -> dict[str, object]:
    support = candidate.get("command_support")
    bind = support.get("bind") if isinstance(support, Mapping) else None
    bind_support = dict(bind) if isinstance(bind, Mapping) else {"command_id": "rsset.binding.bind", "state": "unknown"}
    state = "blocked" if blockers else str(bind_support.get("state") or "unknown")
    enabled = not blockers and state == "available"
    return {
        "command_id": "rsset.binding.bind",
        "state": state,
        "enabled": enabled,
        "safe_to_mutate": enabled,
        "missing_gates": blockers,
        "writes": list(bind_support.get("writes") or []) if enabled else [],
        "source": bind_support,
    }


def _string_sequence(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [item for item in value if isinstance(item, str)]


def _listing_rsset_candidate_report(
    rows: list[object],
    *,
    target_id: str = "",
    manual_state: Mapping[str, object] | None = None,
    journal_projection: Mapping[str, object] | None = None,
    exact_round_trip_available: bool = False,
) -> dict[str, object]:
    mapping_rows = [row for row in rows if isinstance(row, Mapping)]
    uses: list[dict[str, object]] = []
    for row in mapping_rows:
        for context in listing_element_contexts(row):
            use = _rsset_candidate_use_from_context(row, context)
            if use is not None:
                uses.append(use)

    grouped: dict[tuple[str, int], list[dict[str, object]]] = {}
    for use in uses:
        base_register = use.get("base_register")
        displacement = use.get("displacement")
        if isinstance(base_register, str) and isinstance(displacement, int):
            grouped.setdefault((base_register, displacement), []).append(use)

    candidates = [
        _rsset_candidate_group_summary(
            base_register=base_register,
            displacement=displacement,
            uses=group_uses,
            target_id=target_id,
            manual_state=manual_state,
            journal_projection=journal_projection,
            exact_round_trip_available=exact_round_trip_available,
        )
        for (base_register, displacement), group_uses in grouped.items()
    ]
    candidates.sort(
        key=lambda candidate: (
            0 if candidate.get("status") == "actionable" else 1,
            1 if candidate.get("status") == "already_recorded" else 0,
            -cast(int, candidate.get("same_displacement_use_count") or 0),
            str(candidate.get("candidate_id")),
        )
    )
    return {
        "kind": "rsset_candidate_report",
        "candidate_count": len(candidates),
        "use_count": len(uses),
        "candidates": candidates,
    }


def _rsset_candidate_use_from_context(
    row: Mapping[str, object],
    context: dict[str, object],
) -> dict[str, object] | None:
    base_register = context.get("base_register")
    displacement = _int_or_none(context.get("displacement"))
    if not isinstance(base_register, str) or base_register.upper() != "A6":
        return None
    if displacement is None or displacement < 0 or displacement > 0x7FFF:
        return None
    operand_index = _int_or_none(context.get("operand_index"))
    element_kind = context.get("element_kind")
    if not isinstance(element_kind, str) or not element_kind:
        return None
    use: dict[str, object] = {
        "hunk": _int_or_none(context.get("hunk")),
        "addr": _int_or_none(context.get("addr") or context.get("start_offset")),
        "stable_key": context.get("stable_key") or row.get("row_key") or row.get("stable_key"),
        "row_text": str(row.get("text") or "").strip(),
        "element_id": context.get("element_id"),
        "element_kind": element_kind,
        "base_register": base_register.upper(),
        "displacement": displacement,
        "signed_displacement": _signed_16(displacement),
        "access": context.get("access") or "reference",
        "width_bytes": _rsset_candidate_width_bytes(context, row),
    }
    if operand_index is not None:
        use["operand_index"] = operand_index
    for key in ("symbol", "source_kind", "field_name", "classification"):
        value = context.get(key)
        if isinstance(value, str) and value:
            use[key] = value
    for key in ("source_evidence_id", "source_family", "source_evidence_status", "path_lifetime_scope"):
        value = context.get(key)
        if value is not None:
            use[key] = value
    locator = row.get("locator")
    if isinstance(locator, Mapping):
        use["locator"] = dict(locator)
    return {key: value for key, value in use.items() if value is not None}


def _rsset_candidate_width_bytes(context: Mapping[str, object], row: Mapping[str, object]) -> int | None:
    width_bytes = _int_or_none(context.get("width_bytes"))
    if width_bytes is not None:
        return width_bytes
    opcode = str(row.get("opcode_or_directive") or row.get("opcode") or "")
    if opcode.endswith(".b"):
        return 1
    if opcode.endswith(".w"):
        return 2
    if opcode.endswith(".l"):
        return 4
    return None


def _signed_16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def _rsset_candidate_group_summary(
    *,
    base_register: str,
    displacement: int,
    uses: list[dict[str, object]],
    target_id: str = "",
    manual_state: Mapping[str, object] | None = None,
    journal_projection: Mapping[str, object] | None = None,
    exact_round_trip_available: bool = False,
) -> dict[str, object]:
    selected_use = _rsset_candidate_selected_use(uses)
    layout_context = _rsset_candidate_layout_context(uses, displacement)
    candidate_id = f"rsset-raw-a6:{displacement:04X}"
    journal_decision_evidence = _rsset_journal_decision_evidence(
        target_id=target_id,
        candidate_id=candidate_id,
        selected_use=selected_use,
        field_available=layout_context is not None,
        journal_projection=journal_projection,
    )
    evidence_search = _rsset_candidate_evidence_search(
        selected_use=selected_use,
        layout_context=layout_context,
        uses=uses,
        manual_state=manual_state,
        journal_decision_evidence=journal_decision_evidence,
    )
    journal_mutation_gate = _rsset_journal_mutation_gate(
        target_id=target_id,
        candidate_id=candidate_id,
        selected_use=selected_use,
        layout_context=layout_context,
        journal_decision_evidence=journal_decision_evidence,
        exact_round_trip_available=exact_round_trip_available,
    )
    has_base_evidence = bool(evidence_search["accepted_base_evidence"])
    already_recorded = _rsset_candidate_evidence_search_already_recorded(evidence_search)
    field_available = layout_context is not None
    journal_ready = journal_mutation_gate.get("ready_for_039") is True
    duplicate_authority = has_base_evidence and journal_ready and not already_recorded
    missing_gates: list[str] = []
    if not has_base_evidence and not journal_ready:
        missing_gates.append("missing_accepted_base_evidence")
    if not field_available:
        missing_gates.append("missing_field_or_layout_refinement")
    if duplicate_authority:
        missing_gates.append("duplicate_legacy_v2_authority")
    if already_recorded:
        status = "already_recorded"
    elif duplicate_authority:
        status = "blocked"
    else:
        status = "actionable" if (has_base_evidence or journal_ready) and field_available else "blocked"
    bind_support: dict[str, object]
    if already_recorded:
        bind_support = {
            "command_id": "rsset.binding.bind",
            "state": "already_satisfied",
            "existing_manual_state": evidence_search["accepted_base_evidence"][0],
        }
    elif duplicate_authority:
        bind_support = {
            "command_id": "rsset.binding.bind",
            "state": "blocked",
            "missing_gates": ["duplicate_legacy_v2_authority"],
        }
    elif journal_ready:
        bind_support = _rsset_journal_bind_support(
            candidate_id,
            selected_use,
            layout_context,
            journal_decision_evidence,
            journal_mutation_gate,
        )
    elif has_base_evidence:
        bind_support = {"command_id": "rsset.binding.bind", "state": "available"}
    else:
        bind_support = {
            "command_id": "rsset.binding.bind",
            "state": "blocked",
            "missing_gates": ["missing_accepted_base_evidence"],
        }
        if layout_context is not None and layout_context.get("element_kind") == "app_slot":
            bind_support["catalog_state"] = "report_only_same_displacement_app_slot_not_base_evidence"
    return {
        "candidate_id": candidate_id,
        "kind": "rsset_app_slot_candidate",
        "status": status,
        "base_register": base_register,
        "displacement": displacement,
        "signed_displacement": _signed_16(displacement),
        "same_displacement_use_count": len(uses),
        "raw_or_weak_use_count": sum(1 for use in uses if use.get("element_kind") != "app_slot"),
        "access_counts": _rsset_candidate_value_counts(uses, "access"),
        "width_counts": _rsset_candidate_value_counts(uses, "width_bytes"),
        "selected_use": selected_use,
        "same_displacement_uses": uses[:10],
        "field_or_app_slot_context": layout_context,
        "evidence_search": evidence_search,
        "journal_decision_evidence": journal_decision_evidence,
        "journal_mutation_gate": journal_mutation_gate,
        "command_support": {
            "report": {"command_id": "rsset.binding.report", "state": "available"},
            "bind": bind_support,
        },
        "verifier_support": {
            "binding_state": "available",
            "selected_use_render": "ready_if_existing_field" if field_available else "blocked_until_field_refinement",
            "exact_round_trip": "required_for_output_affecting_mutation",
        },
        "missing_gates": missing_gates,
        "safe_to_mutate": status == "actionable" and bind_support.get("state") == "available",
        "mutation_policy": "journal_gate_requires_verified_command" if journal_ready else "report_only_requires_separate_verified_command",
        "rationale": "A6 displacement use requires accepted app-base evidence and field/layout context before mutation",
    }


def _rsset_journal_bind_support(
    candidate_id: str,
    selected_use: Mapping[str, object],
    layout_context: Mapping[str, object] | None,
    journal_decision_evidence: Mapping[str, object],
    journal_mutation_gate: Mapping[str, object],
) -> dict[str, object]:
    candidate = _rsset_journal_binding_candidate(
        {
            "candidate_id": candidate_id,
            "selected_use": dict(selected_use),
            "field_or_app_slot_context": dict(layout_context) if isinstance(layout_context, Mapping) else None,
            "journal_decision_evidence": dict(journal_decision_evidence),
            "journal_mutation_gate": dict(journal_mutation_gate),
        }
    )
    writes = []
    if candidate is not None:
        writes.append({"kind": "rsset_use_site_binding", "parameters": candidate["parameters"]})
    accepted = _mapping_sequence(journal_decision_evidence.get("accepted"))
    source_decision_id = accepted[0].get("decision_id") if accepted and isinstance(accepted[0], Mapping) else None
    return {
        "command_id": "rsset.binding.bind",
        "state": "available",
        "authority": "decision_journal",
        "source_decision_id": source_decision_id,
        "writes": writes,
    }


def _listing_rsset_journal_binding_candidates(rsset_report: Mapping[str, object]) -> list[dict[str, object]]:
    candidates = rsset_report.get("candidates")
    if not isinstance(candidates, Sequence) or isinstance(candidates, str):
        return []
    result: list[dict[str, object]] = []
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            bind_candidate = _rsset_journal_binding_candidate(candidate)
            if bind_candidate is not None:
                result.append(bind_candidate)
    return result


def _rsset_journal_binding_candidate(candidate: Mapping[str, object]) -> dict[str, object] | None:
    if candidate.get("candidate_id") != "rsset-raw-a6:022E":
        return None
    gate = candidate.get("journal_mutation_gate")
    if not isinstance(gate, Mapping) or gate.get("ready_for_039") is not True:
        return None
    evidence_search = candidate.get("evidence_search")
    if isinstance(evidence_search, Mapping) and _int_or_none(evidence_search.get("accepted_base_evidence_count")):
        return None
    selected_use = candidate.get("selected_use")
    layout_context = candidate.get("field_or_app_slot_context")
    journal_lane = candidate.get("journal_decision_evidence")
    if not isinstance(selected_use, Mapping) or not isinstance(layout_context, Mapping) or not isinstance(journal_lane, Mapping):
        return None
    accepted = _mapping_sequence(journal_lane.get("accepted"))
    if len(accepted) != 1:
        return None
    record = accepted[0]
    locator = selected_use.get("locator") or layout_context.get("locator")
    element_id = selected_use.get("element_id") or layout_context.get("element_id")
    if not isinstance(locator, Mapping) or not isinstance(element_id, str) or not element_id:
        return None
    addr = _int_or_none(selected_use.get("addr"))
    operand_index = _int_or_none(selected_use.get("operand_index"))
    displacement = _int_or_none(selected_use.get("displacement"))
    if addr is None or operand_index is None or displacement is None:
        return None
    scope = record.get("scope")
    if not isinstance(scope, Mapping):
        return None
    decision_id = record.get("decision_id")
    reason = record.get("reason")
    parameters: dict[str, object] = {
        "layout_name": str(layout_context.get("layout_name") or "app"),
        "base_symbol": str(layout_context.get("base_symbol") or "__amiga_app_base__"),
        "base_register": str(selected_use.get("base_register") or "A6"),
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "displacement": displacement,
        "operand_index": operand_index,
        "source_evidence_id": decision_id,
        "source_family": "rsset_app_base",
        "source_evidence_status": "accepted",
        "path_lifetime_scope": dict(scope),
        "conflicts": list(record.get("conflicts") or []),
        "parent_evidence_ids": list(record.get("evidence_refs") or []),
        "reason": reason,
    }
    if not isinstance(decision_id, str) or not decision_id or not isinstance(reason, str) or not reason:
        return None
    selected_use_id = f"s{_int_or_none(selected_use.get('hunk')) or 0}:{addr:08X}:op{operand_index}"
    return {
        "id": f"rsset-journal-bind:{candidate.get('candidate_id')}:{selected_use_id}",
        "candidate_id": f"rsset-journal-bind:{candidate.get('candidate_id')}:{selected_use_id}",
        "kind": "rsset_use_site_binding",
        "locator": dict(locator),
        "element_id": element_id,
        "selected_use": dict(selected_use),
        "parameters": parameters,
        "suggested_action_kinds": ["rsset.binding.bind"],
        "default_verifier": "rsset_binding_state",
        "confidence": "high",
        "actionable": True,
        "evidence": {
            "decision_id": decision_id,
            "candidate_id": candidate.get("candidate_id"),
            "selected_use_id": selected_use_id,
        },
    }


def _rsset_candidate_selected_use(uses: list[dict[str, object]]) -> dict[str, object]:
    return dict(
        sorted(
            uses,
            key=lambda use: (
                0 if use.get("element_kind") != "app_slot" else 1,
                int(use.get("addr") or 0),
                int(use.get("operand_index") or 0),
            ),
        )[0]
    )


def _rsset_candidate_layout_context(uses: list[dict[str, object]], displacement: int) -> dict[str, object] | None:
    app_slot_uses = [use for use in uses if use.get("element_kind") == "app_slot"]
    if app_slot_uses:
        return dict(app_slot_uses[0])
    nearby = [
        use
        for use in uses
        if use.get("symbol") and abs(cast(int, use.get("displacement", displacement)) - displacement) <= 8
    ]
    return dict(nearby[0]) if nearby else None


def _rsset_candidate_evidence_search(
    *,
    selected_use: dict[str, object],
    layout_context: dict[str, object] | None,
    uses: list[dict[str, object]],
    manual_state: Mapping[str, object] | None,
    journal_decision_evidence: Mapping[str, object] | None = None,
) -> dict[str, object]:
    accepted_refs: list[dict[str, object]] = []
    rejected_refs: list[dict[str, object]] = []
    for source, evidence in _rsset_candidate_search_sources(
        selected_use=selected_use,
        layout_context=layout_context,
        manual_state=manual_state,
    ):
        ref = _rsset_candidate_accepted_base_evidence_ref(evidence)
        if ref is not None and _rsset_candidate_evidence_matches_selected_use(ref, selected_use):
            accepted_refs.append({"search_source": source, **ref})
            continue
        rejected_refs.append(_rsset_candidate_rejected_evidence_ref(source, evidence, selected_use))
    return {
        "status": "accepted" if accepted_refs else "missing_accepted_base_evidence",
        "searched": [
            "selected_use_source_evidence",
            "same_displacement_app_slot_context",
            "manual_rsset_use_site_bindings",
        ],
        "selected_use_identity": _rsset_candidate_selected_use_identity(selected_use),
        "accepted_base_evidence": accepted_refs,
        "accepted_base_evidence_count": len(accepted_refs),
        "rejected_evidence": rejected_refs[:8],
        "rejected_evidence_count": len(rejected_refs),
        "journal_decision_evidence": dict(journal_decision_evidence)
        if isinstance(journal_decision_evidence, Mapping)
        else _unavailable_rsset_journal_decision_evidence(),
        "same_displacement_use_count": len(uses),
        "missing_proof": [] if accepted_refs else _rsset_candidate_missing_base_proof(),
        "ownership_requirement": "binding action owner required before generated descendants or cleanup",
    }


def _rsset_journal_decision_evidence(
    *,
    target_id: str,
    candidate_id: str,
    selected_use: Mapping[str, object],
    field_available: bool,
    journal_projection: Mapping[str, object] | None,
) -> dict[str, object]:
    if not isinstance(journal_projection, Mapping):
        return _unavailable_rsset_journal_decision_evidence()
    if journal_projection.get("valid") is not True:
        return _unavailable_rsset_journal_decision_evidence(diagnostics=journal_projection.get("diagnostics"))

    accepted: list[dict[str, object]] = []
    deferred: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    mismatched: list[dict[str, object]] = []
    for bucket_name, output in (
        ("accepted_facts", accepted),
        ("deferred_facts", deferred),
        ("rejected_facts", rejected),
    ):
        for record in _mapping_sequence(journal_projection.get(bucket_name)):
            reasons = _rsset_journal_decision_mismatch_reasons(
                record,
                target_id=target_id,
                candidate_id=candidate_id,
                selected_use=selected_use,
            )
            if not reasons:
                output.append(record)
            elif _rsset_journal_decision_is_relevant(record, target_id=target_id, candidate_id=candidate_id, selected_use=selected_use):
                mismatched.append(_rsset_journal_decision_mismatch(record, reasons))

    missing_gates = _rsset_journal_decision_missing_gates(bool(accepted), field_available=field_available)
    status = _rsset_journal_decision_status(accepted=accepted, deferred=deferred, rejected=rejected, mismatched=mismatched)
    return {
        "status": status,
        "accepted_count": len(accepted),
        "accepted": accepted,
        "deferred_count": len(deferred),
        "deferred": deferred,
        "rejected_count": len(rejected),
        "rejected": rejected,
        "mismatched_count": len(mismatched),
        "mismatched": mismatched,
        "missing_gates": missing_gates,
        "mutation_enabled": False,
    }


def _unavailable_rsset_journal_decision_evidence(diagnostics: object = None) -> dict[str, object]:
    return {
        "status": "unavailable",
        "accepted_count": 0,
        "accepted": [],
        "deferred_count": 0,
        "deferred": [],
        "rejected_count": 0,
        "rejected": [],
        "mismatched_count": 0,
        "mismatched": [],
        "missing_gates": ["missing_accepted_base_evidence"],
        "mutation_enabled": False,
        "diagnostics": _mapping_sequence(diagnostics),
    }


def _rsset_journal_decision_status(
    *,
    accepted: Sequence[Mapping[str, object]],
    deferred: Sequence[Mapping[str, object]],
    rejected: Sequence[Mapping[str, object]],
    mismatched: Sequence[Mapping[str, object]],
) -> str:
    if accepted:
        return "accepted"
    if rejected:
        return "rejected"
    if deferred or mismatched:
        return "blocked"
    return "unavailable"


def _rsset_journal_decision_missing_gates(has_accepted: bool, *, field_available: bool) -> list[str]:
    if not has_accepted:
        return ["missing_accepted_base_evidence"]
    gates: list[str] = []
    if not field_available:
        gates.append("missing_field_or_layout_refinement")
    gates.extend(["missing_render_gate", "missing_verifier_gate", "mutation_disabled_in_017_037"])
    return gates


_RSSET_JOURNAL_MUTATION_GATE_IDS = (
    "journal_accept",
    "candidate_identity",
    "selected_identity",
    "fact_type",
    "selected_use_scope",
    "empty_conflicts",
    "field_or_layout_refinement",
    "render_support",
    "generated_source_verifier",
    "exact_round_trip",
)


def _rsset_journal_mutation_gate(
    *,
    target_id: str,
    candidate_id: str,
    selected_use: Mapping[str, object],
    layout_context: Mapping[str, object] | None,
    journal_decision_evidence: Mapping[str, object] | None,
    exact_round_trip_available: bool,
) -> dict[str, object]:
    lane = (
        dict(journal_decision_evidence)
        if isinstance(journal_decision_evidence, Mapping)
        else _unavailable_rsset_journal_decision_evidence()
    )
    accepted = _mapping_sequence(lane.get("accepted"))
    accepted_record = accepted[0] if len(accepted) == 1 else None
    mismatch_reasons = _rsset_journal_gate_mismatch_reasons(lane)
    gate_state = {
        "journal_accept": len(accepted) == 1,
        "candidate_identity": candidate_id == "rsset-raw-a6:022E"
        and not (accepted_record is None and "wrong_candidate" in mismatch_reasons),
        "selected_identity": accepted_record is not None
        or ("wrong_selected_identity" not in mismatch_reasons and len(accepted) == 1),
        "fact_type": accepted_record is not None or ("wrong_fact_type" not in mismatch_reasons and len(accepted) == 1),
        "selected_use_scope": accepted_record is not None
        or (not {"missing_selected_use_scope", "scope_mismatch"} & mismatch_reasons and len(accepted) == 1),
        "empty_conflicts": accepted_record is not None
        or ("non_empty_conflicts" not in mismatch_reasons and len(accepted) == 1),
        "field_or_layout_refinement": layout_context is not None,
        "exact_round_trip": exact_round_trip_available,
    }
    render_readiness = _rsset_journal_render_readiness(
        target_id=target_id,
        candidate_id=candidate_id,
        selected_use=selected_use,
        layout_context=layout_context,
        accepted_record=accepted_record,
    )
    gate_state["render_support"] = render_readiness["status"] == "ready"
    gate_state["generated_source_verifier"] = render_readiness["status"] == "ready"
    satisfied_gates = [gate for gate in _RSSET_JOURNAL_MUTATION_GATE_IDS if gate_state.get(gate) is True]
    missing_gates = [gate for gate in _RSSET_JOURNAL_MUTATION_GATE_IDS if gate not in satisfied_gates]
    return {
        "command_id": "rsset.binding.bind",
        "mutation_enabled": False,
        "ready_for_039": not missing_gates,
        "status": "ready_for_mutation_issue" if not missing_gates else "blocked",
        "satisfied_gates": satisfied_gates,
        "missing_gates": missing_gates,
        "journal_evidence": {
            "status": lane.get("status", "unavailable"),
            "accepted_count": len(accepted),
            "accepted_decision_ids": [
                record["decision_id"] for record in accepted if isinstance(record.get("decision_id"), str)
            ],
            "mismatched_count": lane.get("mismatched_count", 0),
            "mismatch_reasons": sorted(mismatch_reasons),
        },
        "render_intent": render_readiness["render_intent"],
        "verifier_plan": {
            "generated_source": render_readiness["generated_source_verifier"],
            "exact_round_trip": {
                "status": "ready" if exact_round_trip_available else "blocked",
                "available": exact_round_trip_available,
                "verifier": "_verify_round_trip_exact",
                "gate": "exact_round_trip",
            },
        },
        "render_verifier_readiness": render_readiness["status"],
    }


def _rsset_journal_gate_mismatch_reasons(lane: Mapping[str, object]) -> set[str]:
    reasons: set[str] = set()
    for item in _mapping_sequence(lane.get("mismatched")):
        for reason in _string_sequence(item.get("reason_codes")):
            reasons.add(reason)
    return reasons


def _rsset_journal_render_readiness(
    *,
    target_id: str,
    candidate_id: str,
    selected_use: Mapping[str, object],
    layout_context: Mapping[str, object] | None,
    accepted_record: Mapping[str, object] | None,
) -> dict[str, object]:
    render_intent = _rsset_journal_render_intent(
        target_id=target_id,
        candidate_id=candidate_id,
        selected_use=selected_use,
        layout_context=layout_context,
    )
    if accepted_record is None or layout_context is None:
        return {
            "status": "not_applicable_yet",
            "render_intent": render_intent,
            "generated_source_verifier": {
                "status": "not_applicable_yet",
                "verifier": "_verify_projected_rsset_binding_rendered_source",
                "gate": "generated_source_verifier",
                "reason": "requires one exact journal accept and field/layout context",
            },
        }
    blockers = _rsset_journal_render_intent_blockers(render_intent)
    if blockers:
        return {
            "status": "blocked",
            "render_intent": render_intent,
            "generated_source_verifier": {
                "status": "blocked",
                "verifier": "_verify_projected_rsset_binding_rendered_source",
                "gate": "generated_source_verifier",
                "missing": blockers,
            },
        }
    return {
        "status": "ready",
        "render_intent": render_intent,
        "generated_source_verifier": {
            "status": "ready",
            "verifier": "_verify_projected_rsset_binding_rendered_source",
            "gate": "generated_source_verifier",
            "proves": [
                "selected operand/use changed as expected",
                "unrelated RSSET uses did not change",
                "no unsafe symbolic operand emitted",
            ],
        },
    }


def _rsset_journal_render_intent(
    *,
    target_id: str,
    candidate_id: str,
    selected_use: Mapping[str, object],
    layout_context: Mapping[str, object] | None,
) -> dict[str, object]:
    hunk = _int_or_none(selected_use.get("hunk")) or 0
    addr = _int_or_none(selected_use.get("addr"))
    operand_index = _int_or_none(selected_use.get("operand_index"))
    displacement = _int_or_none(selected_use.get("displacement"))
    base_register = selected_use.get("base_register")
    symbol = layout_context.get("symbol") if isinstance(layout_context, Mapping) else None
    expected_operand = None
    if isinstance(symbol, str) and symbol and isinstance(base_register, str) and base_register:
        expected_operand = f"{symbol}({base_register.lower()})"
    intent: dict[str, object] = {
        "target_id": target_id,
        "candidate_id": candidate_id,
        "effect": "selected_operand_only",
        "render_effect": "none_in_017_038",
        "later_mutation_effect": "bind one selected RSSET use-site to the existing app-slot symbol",
        "selected_identity": {
            "segment_id": f"s{hunk}",
            "hunk": hunk,
        },
        "expected_operand": expected_operand,
    }
    if addr is not None:
        cast(dict[str, object], intent["selected_identity"])["addr"] = addr
        cast(dict[str, object], intent["selected_identity"])["address_hex"] = f"{addr:08X}"
        intent["source_offset"] = addr
    if operand_index is not None:
        cast(dict[str, object], intent["selected_identity"])["operand_index"] = operand_index
    if isinstance(base_register, str):
        cast(dict[str, object], intent["selected_identity"])["base_register"] = base_register
    if displacement is not None:
        cast(dict[str, object], intent["selected_identity"])["displacement"] = displacement
        cast(dict[str, object], intent["selected_identity"])["displacement_hex"] = f"{displacement:04X}"
        intent["raw_operand_tokens"] = _rsset_binding_raw_displacement_tokens(
            {"displacement": displacement, "base_register": base_register}
        )
    if isinstance(symbol, str):
        intent["field_symbol"] = symbol
    for key in ("section_index", "source_offset", "element_id", "stable_key"):
        value = selected_use.get(key)
        if value is not None:
            intent[key] = value
    return intent


def _rsset_journal_render_intent_blockers(render_intent: Mapping[str, object]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(render_intent.get("expected_operand"), str):
        blockers.append("missing_expected_operand_symbol")
    identity = render_intent.get("selected_identity")
    if not isinstance(identity, Mapping) or not all(key in identity for key in ("addr", "operand_index", "base_register", "displacement")):
        blockers.append("missing_selected_operand_identity")
    return blockers


def _rsset_journal_decision_mismatch(
    record: Mapping[str, object],
    reasons: Sequence[str],
) -> dict[str, object]:
    result = {
        "decision_id": record.get("decision_id"),
        "action": record.get("action"),
        "candidate_id": record.get("candidate_id"),
        "selected_identity": record.get("selected_identity"),
        "reason_codes": list(reasons),
    }
    return {key: value for key, value in result.items() if value is not None}


def _rsset_journal_decision_mismatch_reasons(
    record: Mapping[str, object],
    *,
    target_id: str,
    candidate_id: str,
    selected_use: Mapping[str, object],
) -> list[str]:
    reasons: list[str] = []
    if record.get("candidate_id") != candidate_id:
        reasons.append("wrong_candidate")
    if not _rsset_journal_decision_selected_identity_matches(
        record.get("selected_identity"),
        target_id=target_id,
        selected_use=selected_use,
    ):
        reasons.append("wrong_selected_identity")
    if record.get("action") == "accept_fact":
        if record.get("fact_type") != "rsset_app_base":
            reasons.append("wrong_fact_type")
        scope = record.get("scope")
        if not isinstance(scope, Mapping) or scope.get("kind") != "selected_use":
            reasons.append("missing_selected_use_scope")
        elif not _rsset_journal_decision_scope_matches(scope, selected_use):
            reasons.append("scope_mismatch")
        if record.get("conflicts") != []:
            reasons.append("non_empty_conflicts")
    return reasons


def _rsset_journal_decision_is_relevant(
    record: Mapping[str, object],
    *,
    target_id: str,
    candidate_id: str,
    selected_use: Mapping[str, object],
) -> bool:
    if record.get("candidate_id") == candidate_id:
        return True
    identity = record.get("selected_identity")
    if not isinstance(identity, Mapping):
        return False
    if target_id and identity.get("target_id") != target_id:
        return False
    expected_segment = f"s{_int_or_none(selected_use.get('hunk')) or 0}"
    if identity.get("segment_id") != expected_segment:
        return False
    addr = _int_or_none(identity.get("addr"))
    selected_addr = _int_or_none(selected_use.get("addr"))
    return addr is not None and selected_addr is not None and abs(addr - selected_addr) <= 8


def _rsset_journal_decision_selected_identity_matches(
    value: object,
    *,
    target_id: str,
    selected_use: Mapping[str, object],
) -> bool:
    if not isinstance(value, Mapping):
        return False
    hunk = _int_or_none(selected_use.get("hunk")) or 0
    addr = _int_or_none(selected_use.get("addr"))
    operand_index = _int_or_none(selected_use.get("operand_index"))
    expected_selected_use_id = f"s{hunk}:{addr:08X}:op{operand_index}" if addr is not None and operand_index is not None else None
    if target_id and value.get("target_id") != target_id:
        return False
    if value.get("segment_id") != f"s{hunk}":
        return False
    if value.get("addr") != addr or value.get("operand_index") != operand_index:
        return False
    selected_use_id = value.get("selected_use_id")
    return not isinstance(selected_use_id, str) or selected_use_id == expected_selected_use_id


def _rsset_journal_decision_scope_matches(
    scope: Mapping[str, object],
    selected_use: Mapping[str, object],
) -> bool:
    selected_hunk = _int_or_none(selected_use.get("hunk")) or 0
    return (
        scope.get("hunk") == selected_hunk
        and scope.get("addr") == selected_use.get("addr")
        and scope.get("operand_index") == selected_use.get("operand_index")
    )


def _rsset_candidate_evidence_search_already_recorded(evidence_search: Mapping[str, object]) -> bool:
    refs = evidence_search.get("accepted_base_evidence")
    if not isinstance(refs, Sequence) or isinstance(refs, str):
        return False
    return any(isinstance(ref, Mapping) and isinstance(ref.get("owner_action_id"), str) for ref in refs)


def _rsset_candidate_search_sources(
    *,
    selected_use: Mapping[str, object],
    layout_context: Mapping[str, object] | None,
    manual_state: Mapping[str, object] | None,
) -> list[tuple[str, Mapping[str, object]]]:
    sources: list[tuple[str, Mapping[str, object]]] = [("selected_use", selected_use)]
    if layout_context is not None and layout_context is not selected_use:
        sources.append(("same_displacement_app_slot_context", layout_context))
    if isinstance(manual_state, Mapping):
        bindings = manual_state.get("rsset_use_site_bindings")
        if isinstance(bindings, Sequence) and not isinstance(bindings, str):
            for binding in bindings:
                if isinstance(binding, Mapping):
                    sources.append(("manual_rsset_use_site_binding", binding))
    return sources


def _rsset_candidate_accepted_base_evidence_ref(evidence: Mapping[str, object]) -> dict[str, object] | None:
    source_evidence_id = evidence.get("source_evidence_id")
    source_family = evidence.get("source_family")
    status = evidence.get("source_evidence_status") or evidence.get("status")
    scope = evidence.get("path_lifetime_scope")
    base_evidence_id = evidence.get("base_evidence_id")
    if not isinstance(source_evidence_id, str) or not source_evidence_id:
        return None
    if source_family != "rsset_app_base":
        return None
    if not isinstance(status, str) or status not in _ACCEPTED_PROVENANCE_STATUSES:
        return None
    if not isinstance(scope, Mapping) or not scope.get("kind"):
        return None
    conflict_reason = _rsset_candidate_conflicts_rejection_reason(evidence)
    if conflict_reason is not None:
        return None
    if not isinstance(base_evidence_id, str) or not base_evidence_id:
        return None
    conflicts = evidence["conflicts"]
    ref = {
        "source_evidence_id": source_evidence_id,
        "source_family": source_family,
        "source_evidence_status": status,
        "path_lifetime_scope": dict(scope),
        "base_evidence_id": base_evidence_id,
        "base_register": evidence.get("base_register"),
        "displacement": evidence.get("displacement"),
        "hunk": evidence.get("hunk"),
        "addr": evidence.get("addr"),
        "operand_index": evidence.get("operand_index"),
        "conflicts": list(conflicts),
    }
    for key in ("owner_action_id", "cleanup_action_id", "parent_evidence_ids", "base_evidence_refs"):
        value = evidence.get(key)
        if value is not None:
            ref[key] = value
    return {key: value for key, value in ref.items() if value is not None}


def _rsset_candidate_evidence_matches_selected_use(
    evidence: Mapping[str, object],
    selected_use: Mapping[str, object],
) -> bool:
    for key in ("addr", "operand_index", "base_register", "displacement"):
        if key not in evidence or key not in selected_use:
            return False
        if evidence.get(key) != selected_use.get(key):
            return False
    if "hunk" in selected_use and evidence.get("hunk") != selected_use.get("hunk"):
        return False
    scope = evidence.get("path_lifetime_scope")
    if not isinstance(scope, Mapping) or scope.get("kind") != "selected_use":
        return False
    for key in ("addr", "operand_index"):
        if scope.get(key) != selected_use.get(key):
            return False
    return not ("hunk" in selected_use and scope.get("hunk") != selected_use.get("hunk"))


def _rsset_candidate_rejected_evidence_ref(
    source: str,
    evidence: Mapping[str, object],
    selected_use: Mapping[str, object],
) -> dict[str, object]:
    ref = {
        "search_source": source,
        "reason": _rsset_candidate_rejected_evidence_reason(evidence, selected_use),
    }
    for key in (
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "status",
        "base_evidence_id",
        "base_register",
        "displacement",
        "hunk",
        "addr",
        "operand_index",
        "symbol",
        "element_kind",
    ):
        value = evidence.get(key)
        if value is not None:
            ref[key] = value
    return ref


def _rsset_candidate_rejected_evidence_reason(
    evidence: Mapping[str, object],
    selected_use: Mapping[str, object],
) -> str:
    accepted = _rsset_candidate_accepted_base_evidence_ref(evidence)
    if accepted is None:
        conflict_reason = _rsset_candidate_conflicts_rejection_reason(evidence)
        if conflict_reason is not None:
            return conflict_reason
        if evidence.get("element_kind") == "app_slot":
            return "same-displacement app-slot context is not accepted base/path evidence"
        return "missing accepted rsset_app_base evidence fields"
    for key in ("addr", "operand_index", "base_register", "displacement"):
        if key not in accepted:
            return "accepted evidence lacks selected-use identity"
    if "hunk" in selected_use and "hunk" not in accepted:
        return "accepted evidence lacks selected-use identity"
    scope = accepted.get("path_lifetime_scope")
    if not isinstance(scope, Mapping) or scope.get("kind") != "selected_use":
        return "accepted evidence path/lifetime scope is not selected-use scoped"
    for key in ("addr", "operand_index"):
        if scope.get(key) != selected_use.get(key):
            return "accepted evidence path/lifetime scope does not cover selected use"
    if "hunk" in selected_use and scope.get("hunk") != selected_use.get("hunk"):
        return "accepted evidence path/lifetime scope does not cover selected use"
    if not _rsset_candidate_evidence_matches_selected_use(accepted, selected_use):
        return "accepted evidence is scoped to a different selected use"
    return "accepted evidence rejected"


def _rsset_candidate_conflicts_rejection_reason(evidence: Mapping[str, object]) -> str | None:
    status = evidence.get("source_evidence_status") or evidence.get("status")
    if evidence.get("source_family") != "rsset_app_base":
        return None
    if not isinstance(evidence.get("source_evidence_id"), str) or not evidence.get("source_evidence_id"):
        return None
    if not isinstance(status, str) or status not in _ACCEPTED_PROVENANCE_STATUSES:
        return None
    if "conflicts" not in evidence:
        return "accepted rsset_app_base evidence missing explicit conflicts sequence"
    conflicts = evidence.get("conflicts")
    if isinstance(conflicts, str) or not isinstance(conflicts, Sequence):
        return "accepted rsset_app_base evidence conflicts must be an explicit sequence"
    if conflicts:
        return "accepted rsset_app_base evidence conflicts must be empty"
    return None


def _rsset_candidate_selected_use_identity(selected_use: Mapping[str, object]) -> dict[str, object]:
    return {
        key: selected_use[key]
        for key in ("hunk", "addr", "operand_index", "base_register", "displacement", "element_id", "stable_key")
        if key in selected_use
    }


def _rsset_candidate_missing_base_proof() -> list[str]:
    return [
        "source_evidence_id with source_family=rsset_app_base",
        "accepted source_evidence_status",
        "path_lifetime_scope covering the selected use",
        "empty conflicts",
        "base_evidence_id for the selected A6 app base",
    ]


def _rsset_candidate_value_counts(uses: list[dict[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for use in uses:
        value = use.get(key)
        if value is None:
            continue
        token = str(value)
        counts[token] = counts.get(token, 0) + 1
    return counts


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
        _verify_comment_payload_matches_command(command, durable_result),
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


def _verify_comment_payload_matches_command(
    command: dict[str, object],
    durable_result: dict[str, object],
) -> dict[str, object]:
    expected = _comment_expected_from_command(command)
    actual = _manual_comment_from_durable_result(durable_result)
    if actual is None:
        return {"layer": "durable_payload", "status": "failed", "message": "missing manual comment payload"}
    if expected is None:
        return {"layer": "durable_payload", "status": "failed", "message": "missing command comment identity"}
    mismatches = {
        key: {"expected": value, "actual": actual.get(key)}
        for key, value in expected.items()
        if actual.get(key) != value
    }
    return {
        "layer": "durable_payload",
        "status": "passed" if not mismatches else "failed",
        "expected_comment": expected,
        "actual_comment": actual,
        "mismatches": mismatches,
        "expected_comment_text": expected.get("text"),
        "actual_comment_text": actual.get("text"),
    }


def _comment_expected_from_command(command: dict[str, object]) -> dict[str, object] | None:
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    parameters = command.get("parameters")
    text = parameters.get("text") if isinstance(parameters, dict) else None
    if not isinstance(locator, dict) or not isinstance(text, str):
        return None
    expected: dict[str, object] = {"text": text}
    for source_key, target_key in (("section_index", "hunk"), ("start_offset", "addr"), ("end_offset", "end")):
        value = locator.get(source_key)
        if isinstance(value, int):
            expected[target_key] = value
    return expected


def _manual_comment_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    comment = _manual_comment_from_action(action)
    if comment is not None:
        return comment
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            comment = _manual_comment_from_action(raw_action)
            if comment is not None:
                return comment
    return None


def _manual_comment_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    comment = action.get("comment")
    if isinstance(comment, dict):
        return cast(dict[str, object], comment)
    payload = action.get("payload")
    comment = payload.get("comment") if isinstance(payload, dict) else None
    if isinstance(comment, dict):
        return cast(dict[str, object], comment)
    return None


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
        orphan_code_blocker = _orphan_code_action_blocker(item)
        confidence = "high" if locator is not None and has_xrefs and verifier is not None and orphan_code_blocker is None else "low"
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
                "orphan_code_score": item.get("orphan_code_score"),
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
            "stop_reason": None
            if confidence == "high"
            else orphan_code_blocker or "candidate lacks locator, xref evidence, or verifier",
        }
        if suggested_comment_text is not None:
            candidate["suggested_comment_text"] = suggested_comment_text
        candidates.append(candidate)
    return candidates


def _orphan_code_island_packet_from_candidates(
    target_id: str,
    candidates: Sequence[Mapping[str, object]],
    *,
    candidate_id: str,
) -> dict[str, object]:
    for candidate in candidates:
        if candidate.get("candidate_id") == candidate_id or candidate.get("durable_id") == candidate_id:
            return _orphan_code_island_packet_from_candidate(target_id, candidate)
    return {
        "packet_kind": "orphan_code_island_evidence_packet",
        "schema_version": 1,
        "target_id": target_id,
        "candidate_id": candidate_id,
        "status": "not_found",
        "safe_to_mutate": False,
        "mutation_policy": "read_only",
    }


def _orphan_code_island_packet_from_candidate(
    target_id: str,
    candidate: Mapping[str, object],
) -> dict[str, object]:
    locator = candidate.get("locator")
    locator = locator if isinstance(locator, Mapping) else {}
    evidence = candidate.get("evidence")
    evidence = evidence if isinstance(evidence, Mapping) else {}
    blockers = _orphan_code_island_packet_blockers(candidate)
    status = "action_ready" if candidate.get("actionable") is True and not blockers else "blocked"
    candidate_id = str(candidate.get("candidate_id") or candidate.get("durable_id") or "")
    candidate_family = "ambiguous_data_range" if candidate.get("kind") == "data_symbol_name" else "orphan_code_island"
    return {
        "packet_kind": "orphan_code_island_evidence_packet",
        "schema_version": 1,
        "packet_id": f"orphan-code-island-packet:{candidate_id}",
        "target_id": target_id,
        "candidate_id": candidate_id,
        "candidate_family": candidate_family,
        "status": status,
        "selected_range": {
            "target_id": target_id,
            "hunk": locator.get("section_index"),
            "segment_id": f"s{locator.get('section_index') or 0}",
            "start": locator.get("start_offset"),
            "end": locator.get("end_offset"),
            "current_classification": candidate.get("data_class") or candidate.get("review_item_kind") or candidate.get("kind"),
            "durable_id": candidate.get("durable_id"),
        },
        "evidence_lanes": {
            "direct_xrefs": candidate.get("xref_summary", []),
            "potential_incoming_control_flow": {
                "status": "present" if evidence.get("has_xrefs") else "unknown",
                "source": "manual_review_item",
            },
            "overlap": {
                "status": "unknown",
                "known_overlaps": [],
                "blocker": "range overlap query is not available on this packet surface",
            },
            "range_bytes": {
                "status": "unavailable",
                "blocker": "review item candidate does not carry range bytes",
            },
            "decoded_candidates": evidence.get("orphan_code_score") or evidence,
        },
        "conflicts": {"status": "unknown", "explicit_empty": False, "items": []},
        "blockers": blockers,
        "render_effects": _orphan_code_island_render_effects(candidate),
        "decision": {
            "writes_enabled": False,
            "available_actions": ["accept_fact", "defer_fact", "reject_fact"],
            "state": "read_only_metadata",
        },
        "safe_next_actions": _orphan_code_island_safe_actions(candidate, blockers),
        "safe_to_mutate": False,
        "mutation_policy": "read_only",
    }


def _orphan_code_island_packet_blockers(candidate: Mapping[str, object]) -> list[str]:
    blockers: list[str] = []
    stop_reason = candidate.get("stop_reason")
    if isinstance(stop_reason, str) and stop_reason:
        blockers.append(stop_reason)
    if candidate.get("locator") is None:
        blockers.append("missing_range_locator")
    evidence = candidate.get("evidence")
    if not isinstance(evidence, Mapping) or evidence.get("has_xrefs") is not True:
        blockers.append("missing_direct_xref_evidence")
    if candidate.get("default_verifier") is None:
        blockers.append("missing_manual_seed_verifier")
    blockers.append("missing_exact_round_trip_gate")
    return sorted(set(blockers))


def _orphan_code_island_render_effects(candidate: Mapping[str, object]) -> list[dict[str, object]]:
    actions = candidate.get("suggested_action_kinds")
    if not isinstance(actions, Sequence) or isinstance(actions, str):
        return []
    effects: list[dict[str, object]] = []
    for action in actions:
        if isinstance(action, str) and action:
            effects.append({"action": action, "effect": "manual_seed_projection", "status": "blocked_until_command_verifier"})
    return effects


def _orphan_code_island_safe_actions(
    candidate: Mapping[str, object],
    blockers: Sequence[str],
) -> list[dict[str, object]]:
    actions = candidate.get("suggested_action_kinds")
    if not isinstance(actions, Sequence) or isinstance(actions, str):
        return []
    return [
        {"action": action, "status": "blocked" if blockers else "candidate", "blockers": list(blockers)}
        for action in actions
        if isinstance(action, str) and action
    ]


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
    if item.get("kind") == "orphan_code_candidate":
        score = item.get("orphan_code_score")
        if isinstance(score, dict):
            evidence = score.get("durable_evidence")
            return isinstance(evidence, list) and bool(evidence)
    refs = item.get("refs")
    if isinstance(refs, list) and refs:
        return True
    ref_count = item.get("ref_count")
    return isinstance(ref_count, int) and ref_count > 0


def _orphan_code_action_blocker(item: dict[str, object]) -> str | None:
    if item.get("kind") != "orphan_code_candidate":
        return None
    score = item.get("orphan_code_score")
    if not isinstance(score, dict):
        return "orphan code candidate lacks durable evidence score"
    if score.get("category") != "evidence_led":
        return "orphan code candidate is report-only without durable control/data-flow evidence"
    checks = score.get("false_positive_checks")
    if isinstance(checks, list) and any(isinstance(check, dict) and check.get("status") == "risk" for check in checks):
        return "orphan code candidate has false-positive risk"
    return None


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
    if any(
        action in {"data_symbol.add", "data_symbol.edit", "data_symbol.rename_existing", "data_symbol.rename"}
        for action in actions
    ):
        return "projected_data_symbol_name"
    if "data_symbol.remove" in actions:
        return "suppressed_seeded_item"
    if any(action.startswith("target.rsset_region.") for action in actions):
        return "rsset_region_state"
    if any(action.startswith("app_slot.") for action in actions):
        return "rsset_region_state"
    if any(action.startswith("rsset.binding.") for action in actions):
        return "rsset_binding_state"
    if "immediate_ref.interpret" in actions:
        return _IMMEDIATE_REF_VERIFIER
    if "a5_hardware_ref.interpret" in actions:
        return _A5_HARDWARE_REF_VERIFIER
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
    if command_id in {
        "data_symbol.add",
        "data_symbol.edit",
        "data_symbol.rename",
        "data_symbol.rename_existing",
    }:
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
            command,
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
    if command_id == "immediate_ref.interpret":
        return _verify_immediate_interpreted_ref_mutation(
            target_id,
            command,
            durable_result,
            project_root=project_root,
        )
    if command_id == "a5_hardware_ref.interpret":
        return _verify_a5_hardware_ref_mutation(
            target_id,
            command,
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


_ACCEPTED_PROVENANCE_STATUSES = frozenset(
    {"accepted", "analysis_proven", "path_specific", "manual_classified", "manual_override"}
)
_PROVENANCE_COMMAND_IDENTITY_KEYS = (
    "source_evidence_id",
    "source_family",
    "source_evidence_status",
    "path_lifetime_scope",
    "conflicts",
    "parent_evidence_ids",
    "contradicted_evidence_id",
    "reason",
    "cleanup_scope",
)
_PROVENANCE_REFERENCE_CONTAINER_KEYS = frozenset({"base_evidence_refs", "cleanup_scope", "conflicts"})


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
    command_evidence = _command_source_evidence_payload(command)
    command_evidence_id = _source_evidence_id(command_evidence) if command_evidence is not None else None
    if durable_evidence is not None:
        evidence = dict(durable_evidence)
        if command_evidence is not None:
            for key in _PROVENANCE_COMMAND_IDENTITY_KEYS:
                if key in command_evidence:
                    evidence[f"expected_{key}"] = command_evidence[key]
        return evidence
    if command_evidence_id is None:
        return None
    return {"source_evidence_id": command_evidence_id, "missing_durable_payload": True}


def _source_evidence_id(evidence: dict[str, object] | None) -> str | None:
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
    context = command.get("context")
    if isinstance(context, dict):
        evidence_id = context.get("source_evidence_id")
        if isinstance(evidence_id, str) and evidence_id:
            return cast(dict[str, object], context)
    return None


def _find_source_evidence_payload(value: object) -> dict[str, object] | None:
    if isinstance(value, dict):
        evidence_id = value.get("source_evidence_id")
        if isinstance(evidence_id, str) and evidence_id:
            return cast(dict[str, object], value)
        for key, child in value.items():
            if key in _PROVENANCE_REFERENCE_CONTAINER_KEYS:
                continue
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
    for key in _PROVENANCE_COMMAND_IDENTITY_KEYS:
        if key == "source_evidence_id":
            continue
        expected_key = f"expected_{key}"
        if expected_key in evidence and not _provenance_identity_values_match(
            key,
            evidence.get(key),
            evidence.get(expected_key),
        ):
            failures.append(f"durable {key} does not match consumed command evidence")
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
        "expected_provenance": {
            key.removeprefix("expected_"): value for key, value in evidence.items() if key.startswith("expected_")
        },
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
    expected = _data_symbol_from_durable_result(durable_result)
    layers = [
        _verify_data_symbol_durable_payload(command, expected),
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_data_symbol_seed(target_id, expected, project_root=project_root),
        _verify_projected_data_symbol_name(target_id, command),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _data_symbol_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    symbol = _data_symbol_from_action(action)
    if symbol is not None:
        return symbol
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            symbol = _data_symbol_from_action(raw_action)
            if symbol is not None:
                return symbol
    return None


def _data_symbol_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    symbol = action.get("data_symbol")
    if isinstance(symbol, dict):
        return cast(dict[str, object], symbol)
    payload = action.get("payload")
    symbol = payload.get("data_symbol") if isinstance(payload, dict) else None
    if isinstance(symbol, dict):
        return cast(dict[str, object], symbol)
    return None


def _verify_data_symbol_durable_payload(
    command: dict[str, object],
    expected: dict[str, object] | None,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "durable_payload", "status": "failed", "message": "missing data symbol payload"}
    missing = [key for key in ("name", "hunk", "addr") if key not in expected]
    mismatches: list[str] = []
    parameters = command.get("parameters")
    if isinstance(parameters, dict):
        for key in ("name", "hunk", "addr", "end", "previous_name"):
            if key in parameters and expected.get(key) != parameters.get(key):
                mismatches.append(key)
    return {
        "layer": "durable_payload",
        "status": "failed" if missing or mismatches else "passed",
        "expected_data_symbol": expected,
        "missing_identity_fields": missing,
        "mismatched_command_fields": mismatches,
    }


def _verify_project_data_symbol_seed(
    target_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing data symbol payload"}
    if any(key not in expected for key in ("name", "hunk", "addr")):
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "data symbol payload missing source identity",
            "expected_data_symbol": expected,
        }
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    seeds = manual_state.get("seeds") if isinstance(manual_state, dict) else None
    if not isinstance(seeds, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual seeds were not reloaded"}
    matches = [
        seed
        for seed in seeds
        if isinstance(seed, dict) and _data_symbol_seed_matches(seed, expected)
    ]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_data_symbol": expected,
        "matching_manual_data_symbol_seeds": matches,
    }


def _data_symbol_seed_matches(seed: dict[str, object], expected: dict[str, object]) -> bool:
    if str(seed.get("kind")) != "data":
        return False
    for key in ("name", "hunk", "addr"):
        if seed.get(key) != expected.get(key):
            return False
    return "end" not in expected or seed.get("end") == expected.get("end")


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
    missing_identity_fields = _target_equate_missing_required_payload_fields(command_id, expected)
    if missing_identity_fields:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "target equate payload missing mutation identity",
            "missing_identity_fields": missing_identity_fields,
            "expected_target_equate": expected,
        }
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


def _target_equate_missing_required_payload_fields(command_id: str, expected: dict[str, object]) -> list[str]:
    if command_id in {"target.equate.add", "target.equate.edit"}:
        fields = ["name", "value"]
    elif command_id == "target.equate.represent":
        fields = ["name", "value", "value_representation"]
        if expected.get("value_representation") == "symbol":
            fields.append("value_expression")
    elif command_id == "target.equate.rename":
        fields = ["previous_name", "name"]
    elif command_id == "target.equate.remove":
        fields = ["name"]
    else:
        fields = ["name"]
    return [field for field in fields if field not in expected]


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
    missing_identity_fields = _rsset_region_missing_required_payload_fields(command_id, expected)
    if missing_identity_fields:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "RSSET layout region payload missing mutation identity",
            "missing_identity_fields": missing_identity_fields,
            "expected_rsset_layout_region": expected,
        }
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


def _rsset_region_missing_required_payload_fields(command_id: str, expected: dict[str, object]) -> list[str]:
    if command_id in {"app_slot.rename", "app_slot.edit"}:
        fields = ["offset", "size", "symbol"]
    elif command_id.endswith(".remove"):
        fields = ["offset"]
    else:
        fields = ["offset", "symbol"]
    return [field for field in fields if field not in expected]


def _verify_rsset_binding_mutation(
    target_id: str,
    command: dict[str, object],
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
        _verify_projected_rsset_binding_rendered_source(target_id, command, command_id, expected),
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
    missing_identity = _rsset_binding_missing_required_identity_fields(command_id, expected)
    if missing_identity:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "RSSET use-site binding payload missing selected-use identity",
            "expected_rsset_use_site_binding": expected,
            "missing_identity_fields": missing_identity,
            "state_key": "removed_rsset_use_site_bindings" if command_id.endswith(".unbind") else "rsset_use_site_bindings",
        }
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


def _rsset_binding_missing_required_identity_fields(command_id: str, expected: dict[str, object]) -> list[str]:
    required = [
        "rsset_use_site_binding_id",
        "hunk",
        "addr",
        "operand_index",
        "base_register",
        "displacement",
        "layout_name",
        "base_symbol",
        "base_evidence_id",
        "cleanup_action_id" if command_id.endswith(".unbind") else "owner_action_id",
    ]
    return [key for key in required if key not in expected]


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
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
        "base_evidence_refs",
    ):
        if key in expected and not _rsset_binding_identity_value_matches(key, actual.get(key), expected.get(key)):
            return False
    return "rsset_use_site_binding_id" in expected


def _rsset_binding_identity_value_matches(key: str, actual: object, expected: object) -> bool:
    if key == "parent_evidence_ids":
        return _provenance_identity_values_match(key, actual, expected)
    if key == "base_evidence_refs":
        return _provenance_reference_values_match(actual, expected)
    return actual == expected


def _verify_projected_rsset_binding_rendered_source(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    expected: dict[str, object] | None,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "missing RSSET use-site binding payload"}
    location = _custom_struct_field_render_location(command)
    if location is None:
        return {"layer": "rendered_source", "status": "failed", "message": "RSSET binding source location missing"}
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
    affected_rendered_text = "\n".join(_data_block_rendered_source_text(row) for row in affected_rows)
    if not affected_rows:
        return {
            "layer": "rendered_source",
            "status": "failed",
            "source_offset": source_offset,
            "message": "affected listing row missing after reload",
        }
    matching_refs = [
        ref
        for row in affected_rows
        for ref in _mapping_sequence(row.get("app_slot_refs"))
        if _rsset_binding_app_slot_ref_matches(ref, expected)
    ]
    raw_tokens = _rsset_binding_raw_displacement_tokens(expected)
    matched_raw_tokens = [
        token for token in raw_tokens if _rendered_source_contains_raw_operand_token(affected_rendered_text, token)
    ]
    render_tokens = _rsset_binding_render_tokens(matching_refs)
    matched_render_tokens = [
        token for token in render_tokens if _rendered_source_contains_token(affected_rendered_text, token)
    ]
    removed = command_id.endswith(".unbind")
    ref_only = expected.get("render_state") == "linked_gap_or_raw"
    if removed:
        status = "passed" if not matching_refs and matched_raw_tokens else "failed"
    elif ref_only:
        status = "passed" if matching_refs and matched_raw_tokens else "failed"
    else:
        status = "passed" if matching_refs and matched_render_tokens and not matched_raw_tokens else "failed"
    return {
        "layer": "rendered_source",
        "status": status,
        "source_offset": source_offset,
        "matching_app_slot_refs": matching_refs,
        "expected_raw_tokens": raw_tokens,
        "matched_raw_tokens": matched_raw_tokens,
        "expected_render_tokens": render_tokens,
        "matched_render_tokens": matched_render_tokens,
        "affected_rendered_text": affected_rendered_text,
    }


def _rsset_binding_app_slot_ref_matches(ref: dict[str, object], expected: dict[str, object]) -> bool:
    for key in ("base_register", "displacement", "operand_index"):
        if key in expected and ref.get(key) != expected.get(key):
            return False
    base_symbol = expected.get("base_symbol")
    return not (isinstance(base_symbol, str) and ref.get("base_symbol") not in {None, base_symbol})


def _rsset_binding_raw_displacement_tokens(expected: dict[str, object]) -> list[str]:
    displacement = expected.get("displacement")
    base_register = expected.get("base_register")
    if not isinstance(displacement, int) or not isinstance(base_register, str) or not base_register:
        return []
    registers = [base_register.lower(), base_register.upper()]
    tokens: list[str] = []
    if displacement == 0:
        tokens.extend(f"({register})" for register in registers)
    else:
        tokens.extend(f"{displacement}({register})" for register in registers)
        for width in (0, 2, 4, 8):
            tokens.extend(f"${displacement:0{width}X}({register})" for register in registers)
    return list(dict.fromkeys(tokens))


def _rsset_binding_render_tokens(matching_refs: list[dict[str, object]]) -> list[str]:
    tokens: list[str] = []
    for ref in matching_refs:
        symbol = ref.get("symbol")
        if isinstance(symbol, str) and symbol:
            tokens.append(symbol)
    return list(dict.fromkeys(tokens))


def _rendered_source_contains_raw_operand_token(rendered_text: str, token: str) -> bool:
    if token.startswith("("):
        return re.search(rf"(?<![A-Za-z0-9_.$]){re.escape(token)}", rendered_text) is not None
    return _rendered_source_contains_token(rendered_text, token)


def _provenance_reference_values_match(actual: object, expected: object) -> bool:
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual) != set(expected):
            return False
        return all(
            _provenance_identity_values_match(key, actual.get(key), expected.get(key))
            if key == "parent_evidence_ids"
            else actual.get(key) == expected.get(key)
            for key in actual
        )
    if isinstance(actual, list | tuple) and isinstance(expected, list | tuple):
        if len(actual) != len(expected):
            return False
        return all(
            _provenance_reference_values_match(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected, strict=True)
        )
    return actual == expected


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
    missing_identity_fields = _data_block_layout_missing_required_identity_fields(command_id, expected)
    if missing_identity_fields:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "data block layout payload missing source identity",
            "missing_identity_fields": missing_identity_fields,
            "expected_data_block_layout": expected,
        }
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


def _data_block_layout_missing_required_identity_fields(command_id: str, expected: dict[str, object]) -> list[str]:
    fields = ["layout_id"]
    if command_id.endswith(".create"):
        fields.extend(["hunk", "source_start", "source_end"])
    return [field for field in fields if field not in expected]


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
        _verify_projected_custom_struct_field_rendered_source(
            target_id,
            command,
            command_id,
            expected,
            durable_result=durable_result,
        ),
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
    missing_identity = _custom_struct_field_missing_required_identity_fields(command_id, expected)
    if missing_identity:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "custom struct field payload missing selected field identity",
            "expected_custom_struct_field": expected,
            "matching_custom_struct_fields": [],
            "missing_identity_fields": missing_identity,
        }
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


def _custom_struct_field_missing_required_identity_fields(command_id: str, expected: dict[str, object]) -> list[str]:
    required = ["struct_name", "offset"]
    if not command_id.endswith(".remove"):
        required.append("name")
    if expected.get("source_evidence_id") is not None:
        required.append("cleanup_action_id" if command_id.endswith(".remove") else "owner_action_id")
    return [key for key in required if key not in expected]


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
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
        "owner_action_id",
        "cleanup_action_id",
    ):
        if key in expected and not _custom_struct_field_identity_value_matches(key, actual.get(key), expected.get(key)):
            return False
    return True


def _custom_struct_field_identity_value_matches(key: str, actual: object, expected: object) -> bool:
    if key == "parent_evidence_ids":
        return _provenance_identity_values_match(key, actual, expected)
    return actual == expected


def _custom_struct_field_remove_already_satisfied(
    current: dict[str, object],
    parameters: dict[str, object],
) -> bool:
    removed = current.get("removed") is True
    field = current.get("custom_struct_field")
    if isinstance(field, dict):
        removed = removed or field.get("removed") is True
        current = {**current, **field}
    if not removed:
        return False
    required_keys = ("struct_name", "offset")
    if any(key not in parameters for key in required_keys):
        return False
    for key in (
        *required_keys,
        "name",
        "type",
        "size",
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
    ):
        if key in parameters and not _custom_struct_field_identity_value_matches(key, current.get(key), parameters.get(key)):
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
    missing_binding_identity = _data_block_element_missing_required_type_binding_fields(command_id, expected)
    if missing_binding_identity:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "data block type-binding payload missing selected binding identity",
            "expected_data_block_element": expected,
            "matching_data_block_elements": [],
            "missing_type_binding_identity_fields": missing_binding_identity,
            "state_key": "removed_data_block_elements" if command_id.endswith(".remove") else "data_block_elements",
        }
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


def _data_block_element_missing_required_type_binding_fields(
    command_id: str,
    expected: dict[str, object],
) -> list[str]:
    if command_id == "row.data_block.element.bind_type":
        binding_key = "type_binding"
        action_key = "owner_action_id"
    elif command_id == "row.data_block.element.clear_type":
        binding_key = "previous_type_binding"
        action_key = "cleanup_action_id"
    else:
        return []
    binding = expected.get(binding_key)
    if not isinstance(binding, dict):
        return [binding_key]
    missing = [
        f"{binding_key}.{key}"
        for key in ("type_binding_id", "layout_id", "element_offset", "element_width", "binding_kind", action_key)
        if key not in binding
    ]
    if "bound_type_id" not in binding and "bound_domain_id" not in binding:
        missing.append(f"{binding_key}.bound_type_or_domain_id")
    return missing


def _data_block_element_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    return (
        isinstance(expected.get("layout_id"), str)
        and isinstance(expected.get("offset"), int)
        and all(_data_block_element_value_matches(key, actual.get(key), value) for key, value in expected.items())
    )


def _data_block_element_value_matches(key: str, actual: object, expected: object) -> bool:
    if key in {"type_binding", "previous_type_binding"}:
        return _provenance_reference_values_match(actual, expected)
    if key == "parent_evidence_ids":
        return _provenance_identity_values_match(key, actual, expected)
    return actual == expected


def _verify_data_block_interpreted_ref_mutation(
    target_id: str,
    command: dict[str, object],
    command_id: str,
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _data_block_interpreted_ref_from_durable_result(durable_result)
    if expected is not None and command_id.endswith(".clear_ref"):
        expected = _data_block_interpreted_ref_with_expected_cleanup_action_id(expected, durable_result)
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


def _data_block_interpreted_ref_with_expected_cleanup_action_id(
    ref: dict[str, object],
    durable_result: dict[str, object],
) -> dict[str, object]:
    action_id = _durable_action_id(durable_result)
    if not isinstance(action_id, str) or not action_id:
        return ref
    expected = dict(ref)
    expected.setdefault("cleanup_action_id", action_id)
    return expected


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
    missing_identity_fields = _data_block_interpreted_ref_missing_required_identity_fields(command_id, expected)
    if missing_identity_fields:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "interpreted ref payload missing selected reference identity",
            "missing_identity_fields": missing_identity_fields,
            "expected_data_block_interpreted_ref": expected,
        }
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
    if _data_block_interpreted_ref_missing_required_identity_fields(command_id, expected):
        return None
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


def _data_block_interpreted_ref_missing_required_identity_fields(
    command_id: str,
    expected: dict[str, object],
) -> list[str]:
    fields = [
        "data_block_ref_id",
        "layout_id",
        "offset",
        "width",
        "reference_kind",
        "target_hunk",
        "target_offset",
        "target_locator",
        "source_value",
    ]
    if command_id.endswith(".clear_ref"):
        fields.append("cleanup_action_id")
    return [
        field
        for field in fields
        if field not in expected and not (field == "data_block_ref_id" and "interpreted_ref_id" in expected)
    ]


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


def _verify_immediate_interpreted_ref_mutation(
    target_id: str,
    command: dict[str, object],
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _immediate_interpreted_ref_from_durable_result(durable_result)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_immediate_interpreted_ref(target_id, expected, project_root=project_root),
        _verify_projected_immediate_interpreted_ref_rendered_source(
            target_id,
            command,
            expected,
            project_root=project_root,
        ),
        _verify_projected_immediate_interpreted_ref_xrefs(
            target_id,
            command,
            expected,
            project_root=project_root,
        ),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _immediate_interpreted_ref_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    ref = _immediate_interpreted_ref_from_action(action)
    if ref is not None:
        return ref
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            ref = _immediate_interpreted_ref_from_action(raw_action)
            if ref is not None:
                return ref
    return None


def _immediate_interpreted_ref_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    ref = action.get("immediate_interpreted_ref")
    if isinstance(ref, dict):
        return cast(dict[str, object], ref)
    payload = action.get("payload")
    ref = payload.get("immediate_interpreted_ref") if isinstance(payload, dict) else None
    if isinstance(ref, dict):
        return cast(dict[str, object], ref)
    return None


def _verify_project_immediate_interpreted_ref(
    target_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing immediate interpreted ref payload"}
    missing_identity_fields = _immediate_interpreted_ref_missing_required_identity_fields(expected)
    if missing_identity_fields:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "immediate interpreted ref payload missing selected operand identity",
            "missing_identity_fields": missing_identity_fields,
            "expected_immediate_interpreted_ref": expected,
        }
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    refs = manual_state.get("immediate_interpreted_refs") if isinstance(manual_state, dict) else None
    if not isinstance(refs, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual immediate refs were not reloaded"}
    matches = [ref for ref in refs if isinstance(ref, dict) and _immediate_interpreted_ref_matches(ref, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_immediate_interpreted_ref": expected,
        "matching_immediate_interpreted_refs": matches,
        "state_key": "immediate_interpreted_refs",
    }


def _project_immediate_interpreted_ref_state_match(
    target_id: str,
    expected: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object] | None:
    if _immediate_interpreted_ref_missing_required_identity_fields(expected):
        return None
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception:
        return None
    manual_state = project.manual_state
    refs = manual_state.get("immediate_interpreted_refs") if isinstance(manual_state, dict) else None
    if not isinstance(refs, list | tuple):
        return None
    for ref in refs:
        if isinstance(ref, dict) and _immediate_interpreted_ref_matches(ref, expected):
            return cast(dict[str, object], ref)
    return None


def _immediate_interpreted_ref_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    expected_ref_id = expected.get("immediate_ref_id")
    return isinstance(expected_ref_id, str) and actual.get("immediate_ref_id") == expected_ref_id and all(
        actual.get(key) == value for key, value in expected.items()
    )


def _immediate_interpreted_ref_missing_required_identity_fields(expected: dict[str, object]) -> list[str]:
    fields = [
        "immediate_ref_id",
        "hunk",
        "addr",
        "end",
        "operand_index",
        "width",
        "reference_kind",
        "source_family",
        "source_evidence_status",
        "target_hunk",
        "target_offset",
        "target_locator",
        "source_value",
    ]
    return [field for field in fields if field not in expected]


def _verify_projected_immediate_interpreted_ref_rendered_source(
    target_id: str,
    command: dict[str, object],
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "missing immediate interpreted ref payload"}
    render_expected = _project_immediate_interpreted_ref_state_match(
        target_id,
        expected,
        project_root=project_root,
    ) or expected
    location = _immediate_interpreted_ref_location(command, render_expected)
    if location is None:
        return {"layer": "rendered_source", "status": "failed", "message": "immediate ref source location missing"}
    section_index, source_offset = location
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {"section_index": [str(section_index)], "source_offset": [str(source_offset)], "before": ["1"], "after": ["2"]},
        )
    except Exception as exc:
        return {"layer": "rendered_source", "status": "failed", "message": str(exc)}
    rows = _listing_rows_from_response(listing)
    affected = _listing_row_at_source(rows, section_index, source_offset)
    if affected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "affected listing row missing after reload"}
    symbol = _immediate_interpreted_ref_symbol(render_expected)
    operand_index = render_expected.get("operand_index")
    selected_operands = [
        part
        for part in _mapping_sequence(affected.get("operand_parts") or affected.get("operandParts"))
        if part.get("operand_index") == operand_index
    ]
    has_symbol_operand = any(
        part.get("symbol") == symbol
        or (isinstance(part.get("metadata"), dict) and part["metadata"].get("symbol") == symbol)
        for part in selected_operands
    )
    rendered_text = str(affected.get("text") or "")
    has_symbol_text = symbol is not None and _rendered_source_contains_token(rendered_text, symbol)
    return {
        "layer": "rendered_source",
        "status": "passed" if symbol is not None and has_symbol_operand and has_symbol_text else "failed",
        "source_offset": source_offset,
        "expected_symbol": symbol,
        "operand_index": operand_index,
        "matched_symbol_operand": has_symbol_operand,
        "matched_symbol_text": has_symbol_text,
        "affected_rendered_text": rendered_text,
        "selected_operands": selected_operands,
    }


def _verify_projected_immediate_interpreted_ref_xrefs(
    target_id: str,
    command: dict[str, object],
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "xref_projection", "status": "failed", "message": "missing immediate interpreted ref payload"}
    render_expected = _project_immediate_interpreted_ref_state_match(
        target_id,
        expected,
        project_root=project_root,
    ) or expected
    location = _immediate_interpreted_ref_location(command, render_expected)
    if location is None:
        return {"layer": "xref_projection", "status": "failed", "message": "immediate ref source location missing"}
    section_index, source_offset = location
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {"section_index": [str(section_index)], "source_offset": [str(source_offset)], "before": ["1"], "after": ["2"]},
        )
    except Exception as exc:
        return {"layer": "xref_projection", "status": "failed", "message": str(exc)}
    rows = _listing_rows_from_response(listing)
    affected = _listing_row_at_source(rows, section_index, source_offset)
    refs = _mapping_sequence(affected.get("runtime_address_refs") or affected.get("runtimeAddressRefs")) if affected else []
    expected_ref_id = render_expected.get("immediate_ref_id")
    target_hunk = render_expected.get("target_hunk")
    target_offset = render_expected.get("target_offset")
    operand_index = render_expected.get("operand_index")
    matching_refs = [
        ref
        for ref in refs
        if ref.get("owner_kind") == "immediate_interpreted_ref"
        and ref.get("owner_id") == expected_ref_id
        and ref.get("owner_element_offset") == operand_index
        and ref.get("target_section_index") == target_hunk
        and ref.get("target_offset") == target_offset
    ]
    return {
        "layer": "xref_projection",
        "status": "passed" if matching_refs else "failed",
        "source_offset": source_offset,
        "expected_owner_id": expected_ref_id,
        "expected_target_hunk": target_hunk,
        "expected_target_offset": target_offset,
        "matching_runtime_address_refs": matching_refs,
        "runtime_address_refs": refs,
    }


def _immediate_interpreted_ref_location(
    command: dict[str, object],
    expected: dict[str, object],
) -> tuple[int, int] | None:
    hunk = expected.get("hunk")
    addr = expected.get("addr")
    if isinstance(hunk, int) and isinstance(addr, int):
        return hunk, addr
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    if isinstance(locator, dict):
        hunk = _int_or_none(locator.get("section_index"))
        addr = _int_or_none(locator.get("start_offset"))
        if hunk is not None and addr is not None:
            return hunk, addr
    return None


def _immediate_interpreted_ref_symbol(expected: dict[str, object]) -> str | None:
    symbol = expected.get("symbol")
    if isinstance(symbol, str) and symbol:
        return symbol
    target_hunk = expected.get("target_hunk")
    target_offset = expected.get("target_offset")
    runtime_address = expected.get("runtime_address")
    if isinstance(target_hunk, int) and isinstance(target_offset, int):
        if isinstance(runtime_address, int):
            return _immediate_reference_symbol(target_hunk, target_offset, runtime_address)
        return _immediate_reference_symbol(target_hunk, target_offset, None)
    return None


def _verify_a5_hardware_ref_mutation(
    target_id: str,
    command: dict[str, object],
    durable_result: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    expected = _a5_hardware_ref_from_durable_result(durable_result)
    _open_and_wait_listing(target_id, timeout_seconds=10.0)
    layers = [
        _verify_manual_log_matches_mutation(target_id, durable_result, project_root=project_root),
        _verify_project_a5_hardware_ref(target_id, expected, project_root=project_root),
        _verify_projected_a5_hardware_ref_rendered_source(
            target_id,
            command,
            expected,
            project_root=project_root,
        ),
        _verify_round_trip_exact(target_id, project_root=project_root),
    ]
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _a5_hardware_ref_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
    action = durable_result.get("action")
    ref = _a5_hardware_ref_from_action(action)
    if ref is not None:
        return ref
    actions = durable_result.get("actions")
    if isinstance(actions, list):
        for raw_action in actions:
            ref = _a5_hardware_ref_from_action(raw_action)
            if ref is not None:
                return ref
    return None


def _a5_hardware_ref_from_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    ref = action.get("a5_hardware_ref")
    if isinstance(ref, dict):
        return _normalized_a5_hardware_ref(cast(dict[str, object], ref))
    payload = action.get("payload")
    ref = payload.get("a5_hardware_ref") if isinstance(payload, dict) else None
    if isinstance(ref, dict):
        return _normalized_a5_hardware_ref(cast(dict[str, object], ref))
    return None


def _normalized_a5_hardware_ref(ref: dict[str, object]) -> dict[str, object]:
    result = dict(ref)
    displacement = _int_or_none(result.get("displacement"))
    custom_base_offset = _int_or_none(result.get("custom_base_offset"))
    hardware_register_offset = _int_or_none(result.get("hardware_register_offset"))
    if custom_base_offset is None:
        custom_base_offset = 0
    if hardware_register_offset is None and displacement is not None:
        hardware_register_offset = custom_base_offset + displacement
    result["custom_base_offset"] = custom_base_offset
    if hardware_register_offset is not None:
        result["hardware_register_offset"] = hardware_register_offset
    return result


def _verify_project_a5_hardware_ref(
    target_id: str,
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "semantic_reload", "status": "failed", "message": "missing A5 hardware ref payload"}
    missing_identity_fields = _a5_hardware_ref_missing_required_identity_fields(expected)
    if missing_identity_fields:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "A5 hardware ref payload missing accepted path/lifetime identity",
            "missing_identity_fields": missing_identity_fields,
            "expected_a5_hardware_ref": expected,
        }
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception as exc:
        return {"layer": "semantic_reload", "status": "failed", "message": str(exc)}
    manual_state = project.manual_state
    refs = manual_state.get("a5_hardware_refs") if isinstance(manual_state, dict) else None
    if not isinstance(refs, list | tuple):
        return {"layer": "semantic_reload", "status": "failed", "message": "manual A5 hardware refs were not reloaded"}
    matches = [ref for ref in refs if isinstance(ref, dict) and _a5_hardware_ref_matches(ref, expected)]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_a5_hardware_ref": expected,
        "matching_a5_hardware_refs": matches,
        "state_key": "a5_hardware_refs",
    }


def _project_a5_hardware_ref_state_match(
    target_id: str,
    expected: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object] | None:
    if _a5_hardware_ref_missing_required_identity_fields(expected):
        return None
    try:
        project = projects.get_project(target_id, project_root=project_root)
    except Exception:
        return None
    manual_state = project.manual_state
    refs = manual_state.get("a5_hardware_refs") if isinstance(manual_state, dict) else None
    if not isinstance(refs, list | tuple):
        return None
    for ref in refs:
        if isinstance(ref, dict) and _a5_hardware_ref_matches(ref, expected):
            return cast(dict[str, object], ref)
    return None


def _a5_hardware_ref_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    expected_ref_id = expected.get("a5_hardware_ref_id")
    return isinstance(expected_ref_id, str) and actual.get("a5_hardware_ref_id") == expected_ref_id and all(
        actual.get(key) == value for key, value in expected.items()
    )


def _a5_hardware_ref_missing_required_identity_fields(expected: dict[str, object]) -> list[str]:
    fields = [
        "a5_hardware_ref_id",
        "hunk",
        "addr",
        "end",
        "operand_index",
        "base_register",
        "displacement",
        "custom_base_offset",
        "hardware_register_offset",
        "custom_base_address",
        "hardware_register_address",
        "reference_kind",
        "source_family",
        "source_evidence_status",
        "source_evidence_id",
        "path_lifetime_scope",
        "symbol",
    ]
    missing = [field for field in fields if field not in expected]
    scope = expected.get("path_lifetime_scope")
    if not isinstance(scope, dict) or scope.get("accepted_hardware_base_evidence") is not True:
        missing.append("path_lifetime_scope.accepted_hardware_base_evidence")
    return missing


def _verify_projected_a5_hardware_ref_rendered_source(
    target_id: str,
    command: dict[str, object],
    expected: dict[str, object] | None,
    *,
    project_root: Path,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "missing A5 hardware ref payload"}
    render_expected = _project_a5_hardware_ref_state_match(target_id, expected, project_root=project_root) or expected
    location = _a5_hardware_ref_location(command, render_expected)
    if location is None:
        return {"layer": "rendered_source", "status": "failed", "message": "A5 hardware ref source location missing"}
    section_index, source_offset = location
    try:
        listing = server.route_request(
            "GET",
            f"/api/projects/{target_id}/listing",
            {"section_index": [str(section_index)], "source_offset": [str(source_offset)], "before": ["1"], "after": ["2"]},
        )
    except Exception as exc:
        return {"layer": "rendered_source", "status": "failed", "message": str(exc)}
    rows = _listing_rows_from_response(listing)
    affected = _listing_row_at_source(rows, section_index, source_offset)
    if affected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "affected listing row missing after reload"}
    symbol_operand_blocker = _a5_hardware_ref_symbol_operand_blocker(render_expected)
    if symbol_operand_blocker is not None:
        return _verify_projected_a5_hardware_ref_entry_comment(
            target_id,
            affected,
            render_expected,
            symbol_operand_blocker,
            source_offset,
            project_root=project_root,
        )
    symbol = expected.get("symbol")
    operand_index = expected.get("operand_index")
    selected_operands = [
        part
        for part in _mapping_sequence(affected.get("operand_parts") or affected.get("operandParts"))
        if part.get("operand_index") == operand_index
    ]
    has_a5_operand = any(
        str(part.get("base_register") or part.get("baseRegister") or part.get("register") or "").upper() == "A5"
        for part in selected_operands
    )
    has_symbol_operand = any(
        part.get("symbol") == symbol
        or (isinstance(part.get("metadata"), dict) and part["metadata"].get("symbol") == symbol)
        for part in selected_operands
    )
    rendered_text = str(affected.get("text") or "")
    has_symbol_text = isinstance(symbol, str) and _rendered_source_contains_token(rendered_text, symbol)
    return {
        "layer": "rendered_source",
        "status": "passed" if has_a5_operand and has_symbol_operand and has_symbol_text else "failed",
        "source_offset": source_offset,
        "expected_symbol": symbol,
        "operand_index": operand_index,
        "matched_a5_operand": has_a5_operand,
        "matched_symbol_operand": has_symbol_operand,
        "matched_symbol_text": has_symbol_text,
        "affected_rendered_text": rendered_text,
        "selected_operands": selected_operands,
    }


def _verify_projected_a5_hardware_ref_entry_comment(
    target_id: str,
    affected: Mapping[str, object],
    expected: dict[str, object],
    symbol_operand_blocker: str,
    source_offset: int,
    *,
    project_root: Path,
) -> dict[str, object]:
    expected_comment = _a5_hardware_ref_entry_comment_text(expected)
    rendered_text = str(affected.get("text") or "")
    symbol = expected.get("symbol")
    selected_operands = [
        part
        for part in _mapping_sequence(affected.get("operand_parts") or affected.get("operandParts"))
        if part.get("operand_index") == expected.get("operand_index")
    ]
    has_symbol_operand = any(
        part.get("symbol") == symbol
        or (isinstance(part.get("metadata"), dict) and part["metadata"].get("symbol") == symbol)
        for part in selected_operands
    )
    has_symbol_text = isinstance(symbol, str) and _rendered_source_contains_token(rendered_text, symbol)
    source_text = ""
    source_error: str | None = None
    try:
        paths = resolve_project_paths(target_id, project_root=project_root)
        with effective_metadata_file(paths.target_dir) as metadata_path:
            source_text = render_project_source_with_c_backend(
                paths.binary_source,
                metadata_path=metadata_path,
                project_root=project_root,
            )
    except Exception as exc:
        source_error = str(exc)
    source_contains_expected_comment = bool(expected_comment and expected_comment in source_text)
    actual_comment_text = expected_comment if source_contains_expected_comment else None
    symbol_operand_text = f"{symbol}(a5)" if isinstance(symbol, str) else None
    has_unsafe_symbol_operand_text = bool(symbol_operand_text and symbol_operand_text in source_text)
    return {
        "layer": "rendered_source",
        "status": "passed"
        if expected_comment
        and source_error is None
        and actual_comment_text == expected_comment
        and not has_symbol_operand
        and not has_symbol_text
        and not has_unsafe_symbol_operand_text
        else "failed",
        "source_offset": source_offset,
        "render_mode": "entry_comment",
        "symbol_operand_blocked_reason": symbol_operand_blocker,
        "expected_comment_text": expected_comment,
        "actual_comment_text": actual_comment_text,
        "source_contains_expected_comment": source_contains_expected_comment,
        "expected_symbol": symbol,
        "matched_symbol_operand": has_symbol_operand,
        "matched_symbol_text": has_symbol_text,
        "matched_unsafe_symbol_operand_text": has_unsafe_symbol_operand_text,
        "source_render_error": source_error,
        "affected_rendered_text": rendered_text,
        "selected_operands": selected_operands,
    }


def _a5_hardware_ref_entry_comment_text(ref: Mapping[str, object]) -> str | None:
    symbol = ref.get("symbol")
    hardware_register_offset = _int_or_none(ref.get("hardware_register_offset"))
    displacement = _int_or_none(ref.get("displacement"))
    if not isinstance(symbol, str) or hardware_register_offset is None or displacement is None:
        return None
    return (
        f"A5 hardware ref: {symbol} at _custom+${hardware_register_offset:04X}; "
        f"operand kept as {_a5_displacement_operand_text(displacement)}"
    )


def _a5_displacement_operand_text(displacement: int) -> str:
    if displacement == 0:
        return "(a5)"
    sign = "-" if displacement < 0 else ""
    return f"{sign}${abs(displacement):04X}(a5)"


def _a5_hardware_ref_location(
    command: dict[str, object],
    expected: dict[str, object],
) -> tuple[int, int] | None:
    hunk = expected.get("hunk")
    addr = expected.get("addr")
    if isinstance(hunk, int) and isinstance(addr, int):
        return hunk, addr
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    if isinstance(locator, dict):
        hunk = _int_or_none(locator.get("section_index"))
        addr = _int_or_none(locator.get("start_offset"))
        if hunk is not None and addr is not None:
            return hunk, addr
    return None


def _listing_rows_from_response(listing: dict[str, object]) -> list[dict[str, object]]:
    data = listing.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []
    return [cast(dict[str, object], row) for row in rows if isinstance(row, dict)]


def _listing_row_at_source(
    rows: list[dict[str, object]],
    section_index: int,
    source_offset: int,
) -> dict[str, object] | None:
    for row in rows:
        locator = row.get("locator")
        locator_payload = locator if isinstance(locator, dict) else row
        hunk = _int_or_none(locator_payload.get("section_index"))
        start = _int_or_none(locator_payload.get("start_offset"))
        end = _int_or_none(locator_payload.get("end_offset"))
        if hunk == section_index and start is not None and end is not None and start <= source_offset < end:
            return row
    return None


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
    cleared = command_id.endswith(".clear_type")
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
            "owner_action_id": entity.owner_action_id,
            "source_evidence_id": entity.source_evidence_id,
            "parent_evidence_ids": list(entity.parent_evidence_ids),
        }
        for entity in entities
        if _data_block_type_binding_descendant_matches(entity, binding, binding_id, cleared=cleared)
    ]
    ownership_mismatches: list[dict[str, object]] = []
    if not cleared:
        expected_owner_action_id = binding.get("owner_action_id")
        expected_source_evidence_id = binding.get("source_evidence_id")
        expected_parent_evidence_ids = binding.get("parent_evidence_ids")
        for descendant in descendants:
            mismatch: dict[str, object] = {}
            if (
                isinstance(expected_owner_action_id, str)
                and descendant.get("owner_action_id") != expected_owner_action_id
            ):
                mismatch["owner_action_id"] = descendant.get("owner_action_id")
            if (
                isinstance(expected_source_evidence_id, str)
                and descendant.get("source_evidence_id") != expected_source_evidence_id
            ):
                mismatch["source_evidence_id"] = descendant.get("source_evidence_id")
            if (
                isinstance(expected_parent_evidence_ids, list | tuple)
                and not _provenance_identity_values_match(
                    "parent_evidence_ids",
                    descendant.get("parent_evidence_ids"),
                    expected_parent_evidence_ids,
                )
            ):
                mismatch["parent_evidence_ids"] = descendant.get("parent_evidence_ids")
            if mismatch:
                mismatch["descendant"] = descendant
                ownership_mismatches.append(mismatch)
    return {
        "layer": "type_binding_descendants",
        "status": "passed"
        if (not descendants if cleared else bool(descendants) and not ownership_mismatches)
        else "failed",
        "type_binding_id": binding_id,
        "matching_seeded_entities": descendants,
        "ownership_mismatches": ownership_mismatches,
    }


def _data_block_type_binding_descendant_matches(
    entity: SeededEntityMetadata,
    binding: Mapping[str, object],
    binding_id: str,
    *,
    cleared: bool,
) -> bool:
    if entity.source_id != "manual_action_log":
        return False
    if entity.source_locator == binding_id:
        return True
    if not cleared:
        return False
    owner_action_id = binding.get("owner_action_id")
    return isinstance(owner_action_id, str) and bool(owner_action_id) and entity.owner_action_id == owner_action_id


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
    *,
    durable_result: dict[str, object] | None = None,
) -> dict[str, object]:
    if expected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "missing custom struct field payload"}
    locations = _custom_struct_field_render_locations(command, durable_result)
    if not locations:
        return {"layer": "rendered_source", "status": "failed", "message": "custom struct field source location missing"}
    section_index, source_offset = locations[0]
    rows: list[object] = []
    affected_rows: list[dict[str, object]] = []
    for check_section, check_offset in locations:
        try:
            listing = server.route_request(
                "GET",
                f"/api/projects/{target_id}/listing",
                {
                    "section_index": [str(check_section)],
                    "source_offset": [str(check_offset)],
                    "before": ["2"],
                    "after": ["2"],
                },
            )
        except Exception as exc:
            return {"layer": "rendered_source", "status": "failed", "message": str(exc)}
        data = listing.get("data")
        check_rows = data.get("rows") if isinstance(data, dict) else None
        if not isinstance(check_rows, list):
            return {"layer": "rendered_source", "status": "failed", "message": "listing rows missing after reload"}
        rows.extend(check_rows)
        affected_rows.extend(_data_block_rendered_source_rows(check_rows, check_section, check_offset))
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
        restore_tokens = _custom_struct_field_remove_restore_tokens(command, expected)
        matched_restore_tokens = [
            token for token in restore_tokens if _rendered_source_contains_raw_operand_token(affected_rendered_text, token)
        ]
        stale_accesses = [
            access
            for row in affected_rows
            for access in _mapping_sequence(row.get("typed_accesses"))
            if _custom_struct_field_render_access_matches(access, expected, command, match_operand_index=False)
        ]
        status = "failed" if stale_accesses or stale_tokens else "passed"
        if restore_tokens and not matched_restore_tokens:
            status = "failed"
        return {
            "layer": "rendered_source",
            "status": status,
            "source_offset": source_offset,
            "checked_source_locations": [
                {"section_index": check_section, "source_offset": check_offset}
                for check_section, check_offset in locations
            ],
            "stale_tokens": stale_tokens,
            "expected_restore_tokens": restore_tokens,
            "matched_restore_tokens": matched_restore_tokens,
            "matching_typed_accesses": stale_accesses,
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
            if _custom_struct_field_render_access_matches(access, previous_expected, command, match_operand_index=False)
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
            "checked_source_locations": [
                {"section_index": check_section, "source_offset": check_offset}
                for check_section, check_offset in locations
            ],
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
        "checked_source_locations": [
            {"section_index": check_section, "source_offset": check_offset}
            for check_section, check_offset in locations
        ],
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


def _custom_struct_field_remove_restore_tokens(command: dict[str, object], expected: dict[str, object]) -> list[str]:
    offset = expected.get("offset")
    if not isinstance(offset, int):
        return []
    context = command.get("context")
    base_register = context.get("base_register") if isinstance(context, dict) else None
    registers = []
    if isinstance(base_register, str) and base_register:
        registers = [base_register.lower(), base_register.upper()]
    tokens: list[str] = []
    if registers:
        if offset == 0:
            tokens.extend(f"({register})" for register in registers)
        else:
            tokens.extend(f"{offset}({register})" for register in registers)
            for width in (0, 2, 4, 8):
                tokens.extend(f"${offset:0{width}X}({register})" for register in registers)
    elif offset != 0:
        tokens.append(f"{offset}(")
        tokens.extend(f"${offset:0{width}X}(" for width in (0, 2, 4, 8))
    return list(dict.fromkeys(tokens))


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


def _custom_struct_field_render_locations(
    command: dict[str, object],
    durable_result: dict[str, object] | None,
) -> list[tuple[int, int]]:
    locations: list[tuple[int, int]] = []
    selected = _custom_struct_field_render_location(command)
    if selected is not None:
        locations.append(selected)
    mutation = durable_result.get("mutation") if isinstance(durable_result, dict) else None
    affected = mutation.get("affected_locators") if isinstance(mutation, dict) else None
    if isinstance(affected, list):
        for locator in affected:
            if not isinstance(locator, dict):
                continue
            section = locator.get("section_index")
            offset = locator.get("start_offset")
            if isinstance(section, int) and isinstance(offset, int):
                locations.append((section, offset))
    return list(dict.fromkeys(locations))


def _custom_struct_field_render_access_matches(
    access: dict[str, object],
    expected: dict[str, object],
    command: dict[str, object],
    *,
    match_operand_index: bool = True,
) -> bool:
    context = command.get("context")
    operand_index = context.get("operand_index") if isinstance(context, dict) else None
    if match_operand_index and isinstance(operand_index, int) and access.get("operand_index") != operand_index:
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
    ]
    rendered_source = _verify_projected_suppressed_seeded_item_rendered_source(target_id, expected, durable_result)
    if rendered_source is not None:
        layers.append(rendered_source)
    layers.append(_verify_round_trip_exact(target_id, project_root=project_root))
    status = "passed" if all(layer["status"] == "passed" for layer in layers) else "failed"
    return {"status": status, "layers": layers}


def _suppressed_seeded_item_from_durable_result(durable_result: dict[str, object]) -> dict[str, object] | None:
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


def _verify_projected_suppressed_seeded_item_rendered_source(
    target_id: str,
    expected: dict[str, object] | None,
    durable_result: dict[str, object],
) -> dict[str, object] | None:
    if expected is None:
        return {"layer": "rendered_source", "status": "failed", "message": "missing suppressed seeded item payload"}
    locations = _durable_result_affected_source_locations(durable_result)
    if not locations:
        return None
    affected_rows: list[dict[str, object]] = []
    for section_index, source_offset in locations:
        try:
            listing = server.route_request(
                "GET",
                f"/api/projects/{target_id}/listing",
                {
                    "section_index": [str(section_index)],
                    "source_offset": [str(source_offset)],
                    "before": ["0"],
                    "after": ["0"],
                },
            )
        except Exception as exc:
            return {"layer": "rendered_source", "status": "failed", "message": str(exc)}
        data = listing.get("data")
        rows = data.get("rows") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            return {"layer": "rendered_source", "status": "failed", "message": "listing rows missing after reload"}
        affected_rows.extend(_data_block_rendered_source_rows(rows, section_index, source_offset))
    if not affected_rows:
        return {
            "layer": "rendered_source",
            "status": "failed",
            "message": "affected listing row missing after reload",
            "checked_source_locations": [
                {"section_index": section_index, "source_offset": source_offset}
                for section_index, source_offset in locations
            ],
        }
    stale_items = [
        item
        for row in affected_rows
        for item in _mapping_sequence(row.get("suppressible_seeded_items"))
        if _suppressed_seeded_item_matches(item, expected)
    ]
    return {
        "layer": "rendered_source",
        "status": "failed" if stale_items else "passed",
        "checked_source_locations": [
            {"section_index": section_index, "source_offset": source_offset}
            for section_index, source_offset in locations
        ],
        "expected_suppressed_seeded_item": expected,
        "stale_suppressible_seeded_items": stale_items,
    }


def _durable_result_affected_source_locations(durable_result: dict[str, object]) -> list[tuple[int, int]]:
    mutation = durable_result.get("mutation")
    affected = mutation.get("affected_locators") if isinstance(mutation, dict) else None
    locations: list[tuple[int, int]] = []
    if isinstance(affected, list):
        for locator in affected:
            if not isinstance(locator, dict):
                continue
            section = locator.get("section_index")
            offset = locator.get("start_offset")
            if isinstance(section, int) and isinstance(offset, int):
                locations.append((section, offset))
    return list(dict.fromkeys(locations))


def _suppressed_seeded_item_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    if not all(key in expected and actual.get(key) == expected.get(key) for key in ("kind", "hunk", "addr")):
        return False
    return "end" not in expected or actual.get("end") == expected.get("end")


def _suppressed_seeded_item_already_satisfied(current: dict[str, object], parameters: dict[str, object]) -> bool:
    if current.get("suppressed") is not True:
        return False
    if not all(key in parameters for key in ("kind", "hunk", "addr")):
        return False
    if "end" in current and "end" not in parameters:
        return False
    expected = {key: parameters[key] for key in ("kind", "hunk", "addr", "end") if key in parameters}
    return _suppressed_seeded_item_matches(current, expected)


def _data_symbol_remove_already_satisfied(current: dict[str, object], parameters: dict[str, object]) -> bool:
    seed_id = parameters.get("seed_id")
    if isinstance(seed_id, str):
        return current.get("removed") is True and current.get("seed_id") == seed_id
    return _suppressed_seeded_item_already_satisfied(current, parameters)


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
    return _dedupe_manual_seed_payloads(seeds)


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
    return list(dict.fromkeys(seed_ids))


def _dedupe_manual_seed_payloads(seeds: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: list[dict[str, object]] = []
    seen: set[str] = set()
    for seed in seeds:
        identity = json.dumps(seed, sort_keys=True, separators=(",", ":"), default=str)
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(seed)
    return deduped


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
    missing_identity = [
        missing for expected in expected_seeds if (missing := _manual_seed_missing_required_identity_fields(command_id, expected))
    ]
    if missing_identity:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "manual seed payload missing source identity",
            "missing_identity_fields": missing_identity,
            "expected_manual_seeds": expected_seeds,
        }
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


def _manual_seed_missing_required_identity_fields(command_id: str, expected: dict[str, object]) -> list[str]:
    fields = ["seed_id", "kind", "hunk", "addr"]
    if command_id.startswith("range.seed."):
        fields.append("end")
    return [field for field in fields if field not in expected]


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
    missing_identity_fields = [
        fields for expected in expected_labels if (fields := _manual_label_missing_required_payload_fields(command_id, expected))
    ]
    if missing_identity_fields:
        return {
            "layer": "semantic_reload",
            "status": "failed",
            "message": "manual label payload missing mutation identity",
            "missing_identity_fields": missing_identity_fields,
            "expected_manual_labels": expected_labels,
        }
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


def _manual_label_missing_required_payload_fields(command_id: str, expected: dict[str, object]) -> list[str]:
    fields = ["label_id"]
    if command_id in {"review.label.rename", "label.rename"}:
        fields.append("name")
    elif command_id == "review.label.change_scope":
        fields.append("scope")
    return [field for field in fields if field not in expected]


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
    for key in ("execution_view_id", "name", "comment", "owner_action_id", "cleanup_action_id"):
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
    if not all(
        key in expected and actual.get(key) == expected.get(key)
        for key in ("domain", "symbol", "value", "hunk", "addr", "element_kind")
    ):
        return False
    return _provenance_payload_matches(actual, expected)


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
        and _register_seed_provenance_matches(seed, expected)
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
        and _register_seed_provenance_matches(seed, expected)
    ]
    return {
        "layer": "semantic_reload",
        "status": "passed" if matches else "failed",
        "expected_register": expected_register,
        "expected_struct_name": struct_name,
        "expected_register_seed": expected,
        "matching_register_seeds": matches,
    }


def _register_seed_provenance_matches(seed: dict[str, object], expected: dict[str, object]) -> bool:
    return _provenance_payload_matches(seed, expected)


def _provenance_payload_matches(actual: dict[str, object], expected: dict[str, object]) -> bool:
    for key in _PROVENANCE_COMMAND_IDENTITY_KEYS:
        expected_value = expected.get(key)
        if expected_value is None:
            continue
        if key not in actual:
            return False
        if not _provenance_identity_values_match(key, actual.get(key), expected_value):
            return False
    return True


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
        _verify_representation_payload_matches_command(command, representation),
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
        payload = action.get("payload")
        representation = payload.get("representation") if isinstance(payload, dict) else None
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
            payload = raw_action.get("payload")
            representation = payload.get("representation") if isinstance(payload, dict) else None
            if isinstance(representation, dict):
                return cast(dict[str, object], representation)
    return None


def _verify_representation_payload_matches_command(
    command: dict[str, object],
    representation: dict[str, object] | None,
) -> dict[str, object]:
    if representation is None:
        return {"layer": "durable_payload", "status": "failed", "message": "missing durable representation payload"}
    expected = _representation_expected_from_command(command)
    if expected is None:
        return {"layer": "durable_payload", "status": "failed", "message": "missing command representation identity"}
    mismatches = {
        key: {"expected": value, "actual": representation.get(key)}
        for key, value in expected.items()
        if representation.get(key) != value
    }
    return {
        "layer": "durable_payload",
        "status": "passed" if not mismatches else "failed",
        "expected_representation": expected,
        "actual_representation": representation,
        "mismatches": mismatches,
    }


def _representation_expected_from_command(command: dict[str, object]) -> dict[str, object] | None:
    context = command.get("context")
    locator = context.get("locator") if isinstance(context, dict) else None
    parameters = command.get("parameters")
    style = parameters.get("representation") if isinstance(parameters, dict) else None
    if not isinstance(context, dict) or not isinstance(locator, dict) or not isinstance(style, str):
        return None
    expected: dict[str, object] = {"style": style}
    for source_key, target_key in (("section_index", "hunk"), ("start_offset", "addr"), ("end_offset", "end")):
        value = locator.get(source_key)
        if isinstance(value, int):
            expected[target_key] = value
    for key in ("element_kind", "operand_index"):
        value = context.get(key)
        if isinstance(value, str | int):
            expected[key] = value
    return expected


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
    bounded_context = _command_boundary_context(command_id, context)
    bounded_parameters = _command_boundary_parameters(command_id, parameters)
    if command_id in {"data_symbol.add", "data_symbol.edit", "data_symbol.rename", "data_symbol.rename_existing"}:
        name = bounded_parameters.get("name")
        if isinstance(name, str) and name:
            bounded_parameters = _data_symbol_command_parameters(
                {"locator": bounded_context.get("locator")},
                bounded_parameters,
                name,
            )
    normalized["context"] = bounded_context
    normalized["parameters"] = bounded_parameters
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
    if action in {"data_symbol.add", "data_symbol.edit", "data_symbol.rename", "data_symbol.rename_existing"}:
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
            "parameters": _data_symbol_command_parameters(candidate, parameter_payload, name),
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
        for key in (
            "source_evidence_id",
            "source_family",
            "source_evidence_status",
            "path_lifetime_scope",
            "confidence",
            "conflicts",
            "parent_evidence_ids",
            "contradicted_evidence_id",
            "reason",
            "cleanup_scope",
        ):
            if key in parameter_payload:
                context[key] = parameter_payload[key]
        return {
            "kind": "command",
            "command_id": action,
            "context": context,
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action == "immediate_ref.interpret":
        element_id = candidate.get("element_id")
        if not isinstance(element_id, str) or not element_id:
            return None
        return {
            "kind": "command",
            "command_id": action,
            "context": {"kind": "element", "locator": locator, "element_id": element_id},
            "parameters": parameter_payload,
            "output_affecting": True,
        }
    if action == "a5_hardware_ref.interpret":
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
        "struct_size",
        "width_bits",
        "width_bytes",
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "conflicts",
        "parent_evidence_ids",
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
            "parent_evidence_ids",
            "contradicted_evidence_id",
            "reason",
            "cleanup_scope",
        ):
            if key in evidence and key not in context:
                context[key] = evidence[key]
    return context


def _command_boundary_parameters(command_id: str, parameters: object) -> dict[str, object]:
    payload = dict(parameters) if isinstance(parameters, dict) else {}
    if command_id in {"data_symbol.add", "data_symbol.edit", "data_symbol.rename", "data_symbol.rename_existing"}:
        return {key: payload[key] for key in ("name", "hunk", "addr", "end") if key in payload}
    if command_id == "data_symbol.remove":
        return {key: payload[key] for key in ("kind", "hunk", "addr", "end", "seed_id") if key in payload}
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


def _data_symbol_command_parameters(
    candidate: dict[str, object],
    parameter_payload: dict[str, object],
    name: str,
) -> dict[str, object]:
    parameters = _command_boundary_parameters("data_symbol.rename", {**parameter_payload, "name": name})
    if "hunk" not in parameters:
        hunk = candidate.get("target_hunk")
        if not isinstance(hunk, int):
            locator = candidate.get("locator")
            hunk = locator.get("section_index") if isinstance(locator, dict) else None
        if isinstance(hunk, int):
            parameters["hunk"] = hunk
    if "addr" not in parameters:
        addr = candidate.get("target_addr")
        if not isinstance(addr, int):
            locator = candidate.get("locator")
            addr = locator.get("start_offset") if isinstance(locator, dict) else None
        if isinstance(addr, int):
            parameters["addr"] = addr
    if "end" not in parameters:
        end = candidate.get("target_end")
        if not isinstance(end, int):
            locator = candidate.get("locator")
            end = locator.get("end_offset") if isinstance(locator, dict) else None
        addr = parameters.get("addr")
        if isinstance(end, int) and (not isinstance(addr, int) or end > addr):
            parameters["end"] = end
    return parameters


def _command_boundary_context(command_id: str, context: dict[str, object]) -> dict[str, object]:
    if command_id in {
        "data_symbol.add",
        "data_symbol.edit",
        "data_symbol.rename",
        "data_symbol.rename_existing",
        "data_symbol.remove",
    }:
        return {key: context[key] for key in ("kind", "locator", "element_id") if key in context}
    if command_id == "target.equate.represent":
        return {key: context[key] for key in ("kind",) if key in context}
    return dict(context)


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
        "parent_evidence_ids",
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
    _copy_source_evidence_to_payload(context, candidate)
    evidence = candidate.get("evidence")
    if isinstance(evidence, dict):
        _copy_source_evidence_to_payload(context, cast(dict[str, object], evidence))
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
    if _data_symbol_candidate_is_class_address_only(candidate, command):
        return "data symbol name is only class/address styling"
    if _candidate_already_satisfied(candidate, command):
        return "candidate already satisfied in projected semantic state"
    if _literal_representation_candidate_is_syntax_only(candidate, command):
        return "literal representation is syntax-only and low semantic value"
    command_id = command.get("command_id")
    if isinstance(command_id, str) and _is_typed_field_command_id(command_id) and _typed_field_command_shape_mismatch(command):
        return "typed field shape mismatch"
    if _candidate_verifier(candidate, command) is None:
        return "missing action-specific verifier"
    if not _command_context_complete(command):
        return "missing durable command context"
    return None


def _literal_representation_candidate_is_syntax_only(
    candidate: dict[str, object],
    command: dict[str, object],
) -> bool:
    command_id = command.get("command_id")
    if not isinstance(command_id, str) or not command_id.startswith("representation."):
        return False
    if candidate.get("kind") != "literal_representation":
        return False
    if candidate.get("autonomous_progress_value") == "semantic":
        return False
    evidence_id = candidate.get("source_evidence_id")
    evidence_status = candidate.get("source_evidence_status")
    source_family = candidate.get("source_family")
    path_scope = candidate.get("path_lifetime_scope")
    if (
        isinstance(evidence_id, str)
        and evidence_id
        and isinstance(source_family, str)
        and source_family
        and isinstance(evidence_status, str)
        and evidence_status in _ACCEPTED_PROVENANCE_STATUSES
        and (path_scope is None or isinstance(path_scope, dict))
    ):
        return False
    evidence = candidate.get("evidence")
    evidence_kind = evidence.get("evidence_kind") if isinstance(evidence, dict) else None
    if evidence_kind == "byte_printable_immediate":
        return True
    return candidate.get("autonomous_progress_value") == "low"


def _data_symbol_candidate_is_class_address_only(
    candidate: dict[str, object],
    command: dict[str, object],
) -> bool:
    command_id = command.get("command_id")
    if command_id not in {"data_symbol.rename", "data_symbol.rename_existing"}:
        return False
    if candidate.get("kind") != "data_symbol_name":
        return False
    data_class = candidate.get("data_class")
    target_hunk = candidate.get("target_hunk")
    target_addr = candidate.get("target_addr")
    if not isinstance(data_class, str) or not isinstance(target_hunk, int) or not isinstance(target_addr, int):
        return False
    expected = _data_ref_symbol_name(data_class, candidate.get("runtime_address"), target_hunk, target_addr)
    if expected is None:
        return False
    parameters = command.get("parameters")
    name = parameters.get("name") if isinstance(parameters, dict) else candidate.get("new_name")
    return name == expected


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
        if command_id is not None and command_verifier is None:
            return None
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
    struct_name = params.get("struct_name")
    context_struct_name = (
        context.get("owner_struct_name")
        or context.get("refined_struct_name")
        or context.get("container_struct_name")
        or context.get("root_struct_name")
    )
    if (
        isinstance(struct_name, str)
        and struct_name.strip()
        and isinstance(context_struct_name, str)
        and context_struct_name.strip()
        and struct_name.strip() != context_struct_name.strip()
    ):
        return True
    size = params.get("size")
    width_bytes = context.get("width_bytes")
    if isinstance(size, int) and not isinstance(size, bool) and isinstance(width_bytes, int) and not isinstance(width_bytes, bool):
        return size != width_bytes
    width_bits = context.get("width_bits")
    if isinstance(size, int) and not isinstance(size, bool) and isinstance(width_bits, int) and not isinstance(width_bits, bool):
        return size * 8 != width_bits
    selected_offset = offset if isinstance(offset, int) and not isinstance(offset, bool) else context_offset
    struct_size = context.get("struct_size")
    return (
        isinstance(selected_offset, int)
        and not isinstance(selected_offset, bool)
        and isinstance(size, int)
        and not isinstance(size, bool)
        and isinstance(struct_size, int)
        and not isinstance(struct_size, bool)
        and selected_offset + size > struct_size
    )


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
    if command_id in {"data_symbol.add", "data_symbol.edit", "data_symbol.rename", "data_symbol.rename_existing"}:
        name = parameters.get("name")
        return isinstance(name, str) and current.get("name") == name
    if command_id == "data_symbol.remove":
        return _data_symbol_remove_already_satisfied(current, parameters)
    if command_id in {"app_slot.rename", "app_slot.edit"}:
        return all(current.get(key) == value for key, value in parameters.items())
    if command_id == "app_slot.remove":
        return current.get("removed") is True
    if command_id == "rsset.binding.bind":
        return _rsset_binding_already_satisfied(current, parameters)
    if command_id == "rsset.binding.unbind":
        return _rsset_binding_unbind_already_satisfied(current, parameters)
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
        return all(_custom_struct_field_identity_value_matches(key, current.get(key), value) for key, value in parameters.items())
    if command_id in {"target.custom_struct_field.remove", "typed_access.field.remove"}:
        return _custom_struct_field_remove_already_satisfied(current, parameters)
    if command_id == "row.data_block.element.bind_type":
        return _data_block_type_binding_already_satisfied(current, parameters)
    if command_id == "row.data_block.element.clear_type":
        return _data_block_type_clear_already_satisfied(current, parameters)
    if command_id in {"target.execution_view.add", "target.execution_view.edit"}:
        return all(current.get(key) == value for key, value in parameters.items())
    if command_id == "target.execution_view.remove":
        return current.get("removed") is True
    if command_id.startswith("correction.suppress_seeded_item."):
        suppression_parameters = dict(parameters)
        suppression_parameters.setdefault("kind", command_id.removeprefix("correction.suppress_seeded_item."))
        return _suppressed_seeded_item_already_satisfied(current, suppression_parameters)
    if command_id.startswith(("semantic.lvo.", "semantic.struct_offset.", "semantic.equate.")):
        return _semantic_hint_already_satisfied(current, command)
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


def _rsset_binding_already_satisfied(current: dict[str, object], parameters: dict[str, object]) -> bool:
    binding = current.get("rsset_use_site_binding")
    if isinstance(binding, dict):
        current = binding
    if current.get("removed") is True:
        return False
    for key in (
        "layout_name",
        "base_symbol",
        "base_register",
        "base_evidence_id",
        "displacement",
        "operand_index",
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
        "base_evidence_refs",
    ):
        if key in parameters and not _rsset_binding_identity_value_matches(key, current.get(key), parameters.get(key)):
            return False
    return True


def _rsset_binding_unbind_already_satisfied(current: dict[str, object], parameters: dict[str, object]) -> bool:
    removed = current.get("removed") is True
    binding = current.get("rsset_use_site_binding")
    if isinstance(binding, dict):
        removed = removed or binding.get("removed") is True
        current = {**current, **binding}
    if not removed:
        return False
    required_keys = (
        "layout_name",
        "base_symbol",
        "base_register",
        "base_evidence_id",
        "displacement",
        "operand_index",
    )
    if any(key not in parameters for key in required_keys):
        return False
    for key in (
        *required_keys,
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
        "base_evidence_refs",
    ):
        if key in parameters and not _rsset_binding_identity_value_matches(key, current.get(key), parameters.get(key)):
            return False
    return True


def _data_block_type_binding_already_satisfied(current: dict[str, object], parameters: dict[str, object]) -> bool:
    for key in ("layout_id", "offset", "width"):
        if key in parameters and current.get(key) != parameters.get(key):
            return False
    binding = current.get("type_binding")
    if not isinstance(binding, dict):
        return False
    bound_type_id = parameters.get("bound_type_id") or parameters.get("type_id")
    if isinstance(bound_type_id, str) and binding.get("bound_type_id") != bound_type_id:
        return False
    bound_domain_id = parameters.get("bound_domain_id") or parameters.get("domain_id")
    if isinstance(bound_domain_id, str) and binding.get("bound_domain_id") != bound_domain_id:
        return False
    for key in (
        "binding_kind",
        "array_count",
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
    ):
        if key in parameters and not _data_block_element_value_matches(key, binding.get(key), parameters.get(key)):
            return False
    return True


def _data_block_type_clear_already_satisfied(current: dict[str, object], parameters: dict[str, object]) -> bool:
    required_element_keys = ("layout_id", "offset", "width")
    if any(key not in parameters for key in required_element_keys):
        return False
    for key in required_element_keys:
        if current.get(key) != parameters.get(key):
            return False
    if isinstance(current.get("type_binding"), dict):
        return False
    previous_binding = current.get("previous_type_binding")
    if not isinstance(previous_binding, dict):
        return False
    if not isinstance(parameters.get("type_binding_id"), str):
        return False
    for key in (
        "type_binding_id",
        "binding_kind",
        "bound_type_id",
        "bound_domain_id",
        "owner_action_id",
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
    ):
        if key in parameters and not _data_block_element_value_matches(key, previous_binding.get(key), parameters.get(key)):
            return False
    return True


def _semantic_hint_already_satisfied(current: dict[str, object], command: dict[str, object]) -> bool:
    command_id = command.get("command_id")
    domain = current.get("domain")
    symbol = current.get("symbol")
    if not isinstance(command_id, str) or not isinstance(domain, str) or not isinstance(symbol, str):
        return False
    if command_id != f"semantic.{domain}.{_semantic_action_token(symbol)}":
        return False
    context = command.get("context")
    parameters = command.get("parameters")
    context = context if isinstance(context, dict) else {}
    parameters = parameters if isinstance(parameters, dict) else {}
    for key in ("value", "element_kind", "operand_index"):
        expected = parameters.get(key, context.get(key))
        if expected is not None and current.get(key) != expected:
            return False
    locator = context.get("locator")
    if isinstance(locator, dict):
        hunk = locator.get("section_index")
        if hunk is not None and current.get("hunk") != hunk:
            return False
        addr = locator.get("start_offset")
        if addr is not None and current.get("addr") != addr:
            return False
    expected_provenance = {
        key: parameters[key] if key in parameters else context.get(key)
        for key in _PROVENANCE_COMMAND_IDENTITY_KEYS
        if key in parameters or key in context
    }
    return not expected_provenance or _provenance_payload_matches(current, expected_provenance)


def _semantic_action_token(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")[:80] or "candidate"


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
    if left.get("command_id") != right.get("command_id") or left.get("context") != right.get("context"):
        return False
    keys = _command_identity_parameter_keys(left, right)
    if not keys:
        return True
    return _catalog_entry_parameters_match(left, right, keys)


def _command_identity_parameter_keys(left: dict[str, object], right: dict[str, object]) -> tuple[str, ...]:
    command_id = left.get("command_id")
    if command_id in {"rsset.binding.bind", "rsset.binding.unbind"}:
        return _rsset_binding_catalog_identity_keys(left, right)
    if isinstance(command_id, str) and _is_typed_field_command_id(command_id):
        return _command_provenance_identity_keys(
            left,
            right,
            ("struct_name", "offset", "source_evidence_id", "source_family", "source_evidence_status"),
        )
    if command_id == "row.data_block.element.bind_type":
        return _command_provenance_identity_keys(left, right, ("layout_id", "offset", "width"))
    if command_id == "row.data_block.element.clear_type":
        return _data_block_type_clear_identity_keys(left, right)
    if isinstance(command_id, str) and command_id.startswith("correction.suppress_seeded_item."):
        return _suppressed_seeded_item_identity_keys(left, right)
    if command_id in {"data_symbol.add", "data_symbol.edit", "data_symbol.rename", "data_symbol.rename_existing"}:
        return _data_symbol_identity_keys(left, right)
    if command_id == "data_symbol.remove":
        parameters = left.get("parameters")
        if isinstance(parameters, dict) and isinstance(parameters.get("seed_id"), str):
            return ("seed_id",)
        return _suppressed_seeded_item_identity_keys(left, right)
    return ()


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
        return _catalog_entry_parameters_match(command, entry, _rsset_binding_catalog_identity_keys(command, entry))
    if isinstance(command_id, str) and _is_typed_field_command_id(command_id):
        return _catalog_entry_parameters_match(
            command,
            entry,
            _catalog_entry_provenance_identity_keys(
                command,
                ("struct_name", "offset", "source_evidence_id", "source_family", "source_evidence_status"),
            ),
        )
    if command_id == "row.data_block.element.bind_type":
        return _catalog_entry_parameters_match(
            command,
            entry,
            _catalog_entry_provenance_identity_keys(command, ("layout_id", "offset", "width")),
        )
    if command_id == "row.data_block.element.clear_type":
        return _catalog_entry_parameters_match(command, entry, _data_block_type_clear_identity_keys(command))
    if isinstance(command_id, str) and command_id.startswith("correction.suppress_seeded_item."):
        return _catalog_entry_parameters_match(command, entry, _suppressed_seeded_item_identity_keys(command, entry))
    if command_id in {"data_symbol.add", "data_symbol.edit", "data_symbol.rename", "data_symbol.rename_existing"}:
        return _catalog_entry_parameters_match(command, entry, _data_symbol_identity_keys(command, entry))
    if command_id == "data_symbol.remove":
        parameters = command.get("parameters")
        keys = (
            ("seed_id",)
            if isinstance(parameters, dict) and isinstance(parameters.get("seed_id"), str)
            else _suppressed_seeded_item_identity_keys(command, entry)
        )
        return _catalog_entry_parameters_match(command, entry, keys)
    return True


def _data_symbol_identity_keys(command: dict[str, object], entry: dict[str, object]) -> tuple[str, ...]:
    command_parameters = command.get("parameters")
    entry_parameters = entry.get("parameters")
    if not isinstance(command_parameters, dict) or not isinstance(entry_parameters, dict):
        return ("hunk", "addr")
    if "end" in command_parameters or "end" in entry_parameters:
        return ("hunk", "addr", "end")
    return ("hunk", "addr")


def _suppressed_seeded_item_identity_keys(command: dict[str, object], entry: dict[str, object]) -> tuple[str, ...]:
    command_parameters = command.get("parameters")
    entry_parameters = entry.get("parameters")
    if (isinstance(command_parameters, dict) and "end" in command_parameters) or (
        isinstance(entry_parameters, dict) and "end" in entry_parameters
    ):
        return ("kind", "hunk", "addr", "end")
    return ("kind", "hunk", "addr")


def _rsset_binding_catalog_identity_keys(
    command: dict[str, object],
    entry: dict[str, object] | None = None,
) -> tuple[str, ...]:
    keys = list(
        _command_provenance_identity_keys(
            command,
            entry or {},
            ("layout_name", "base_symbol", "base_register", "base_evidence_id", "displacement", "operand_index"),
        )
    )
    for payload in (
        command.get("parameters"),
        entry.get("parameters") if isinstance(entry, dict) else None,
    ):
        if isinstance(payload, dict) and "base_evidence_refs" in payload and "base_evidence_refs" not in keys:
            keys.append("base_evidence_refs")
    return tuple(keys)


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
        if entry_value is None or not _provenance_identity_values_match(key, entry_value, command_value):
            return False
    return True


def _provenance_identity_values_match(key: str, left: object, right: object) -> bool:
    if key == "parent_evidence_ids":
        left_ids = _normalise_parent_evidence_ids(left)
        right_ids = _normalise_parent_evidence_ids(right)
        return left_ids is not None and right_ids is not None and left_ids == right_ids
    if key == "base_evidence_refs":
        return _provenance_reference_values_match(left, right)
    return left == right


def _normalise_parent_evidence_ids(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list | tuple):
        return None
    ids = {item for item in value if isinstance(item, str) and item}
    return tuple(sorted(ids))


def _catalog_entry_provenance_identity_keys(command: dict[str, object], base_keys: tuple[str, ...]) -> tuple[str, ...]:
    parameters = command.get("parameters")
    if not isinstance(parameters, dict):
        return base_keys
    provenance_keys = tuple(key for key in _PROVENANCE_COMMAND_IDENTITY_KEYS if key in parameters and key not in base_keys)
    return (*base_keys, *provenance_keys)


def _command_provenance_identity_keys(
    left: dict[str, object],
    right: dict[str, object],
    base_keys: tuple[str, ...],
) -> tuple[str, ...]:
    keys = list(_catalog_entry_provenance_identity_keys(left, base_keys))
    right_parameters = right.get("parameters")
    if isinstance(right_parameters, dict):
        keys.extend(key for key in _PROVENANCE_COMMAND_IDENTITY_KEYS if key in right_parameters and key not in keys)
    return tuple(keys)


def _data_block_type_clear_identity_keys(
    command: dict[str, object],
    other: dict[str, object] | None = None,
) -> tuple[str, ...]:
    parameters = command.get("parameters")
    base_keys = ("layout_id", "offset", "width")
    if not isinstance(parameters, dict):
        return base_keys
    binding_keys = tuple(
        key
        for key in ("type_binding_id", "binding_kind", "bound_type_id", "bound_domain_id", "owner_action_id")
        if key in parameters
    )
    keys = _catalog_entry_provenance_identity_keys(command, (*base_keys, *binding_keys))
    other_parameters = other.get("parameters") if other is not None else None
    if isinstance(other_parameters, dict):
        extra_binding_keys = (
            "type_binding_id",
            "binding_kind",
            "bound_type_id",
            "bound_domain_id",
            "owner_action_id",
        )
        keys = (
            *keys,
            *(key for key in extra_binding_keys if key in other_parameters and key not in keys),
        )
        keys = (
            *keys,
            *(key for key in _PROVENANCE_COMMAND_IDENTITY_KEYS if key in other_parameters and key not in keys),
        )
    return keys


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
    eligible.sort(key=_planner_sort_key)
    for item in eligible:
        command = cast(dict[str, object], item["command"])
        availability = _command_availability(target_id, cast(dict[str, object], command["context"]))
        catalog_entry = _available_catalog_command(command, availability)
        _record_planner_availability_check(inspect_report, item, command, availability, catalog_entry)
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
    eligible.sort(key=_planner_sort_key)
    ranked.sort(key=lambda item: (-cast(int, item["planner_score"]), str(_candidate_id(item))))
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
        "skipped_candidate_ids": [
            {"candidate_id": _candidate_id(candidate), "reason": candidate.get("stop_reason")} for candidate in skipped
        ],
        "selected_candidate_id": cast(dict[str, object], selected["work_item"]).get("candidate_id")
        or cast(dict[str, object], selected["work_item"]).get("id"),
        "selected_command_id": command.get("command_id"),
        "selected_before_availability": _selected_action_summary(selected),
        "selected_verifier": _candidate_verifier(cast(dict[str, object], selected["work_item"]), command),
        "selection_reason": "highest-ranked supported source-converging command",
    }
    return {
        "work_item": cast(dict[str, object], selected["work_item"]),
        "command": command,
        "planner_score": selected["planner_score"],
    }


def _planner_sort_key(item: dict[str, object]) -> tuple[int, str, str]:
    command = item.get("command")
    return (
        -cast(int, item["planner_score"]),
        str(_candidate_id(cast(dict[str, object], item.get("work_item") or item))),
        str(command.get("command_id") if isinstance(command, dict) else ""),
    )


def _candidate_id(candidate: dict[str, object]) -> object:
    return candidate.get("candidate_id") or candidate.get("durable_id") or candidate.get("id")


def _selected_action_summary(selected: dict[str, object] | None) -> dict[str, object] | None:
    if selected is None:
        return None
    work_item = selected.get("work_item")
    command = selected.get("command")
    return {
        "candidate_id": _candidate_id(cast(dict[str, object], work_item)) if isinstance(work_item, dict) else None,
        "command_id": command.get("command_id") if isinstance(command, dict) else None,
        "planner_score": selected.get("planner_score"),
    }


def _record_planner_availability_check(
    inspect_report: dict[str, object],
    selected: dict[str, object],
    command: dict[str, object],
    availability: dict[str, object],
    catalog_entry: dict[str, object] | None,
) -> None:
    planner = inspect_report.setdefault("planner", {})
    if not isinstance(planner, dict):
        return
    checks = planner.setdefault("availability_checks", [])
    if not isinstance(checks, list):
        return
    status = "available" if catalog_entry is not None else "unavailable"
    check: dict[str, object] = {
        **(cast(dict[str, object], _selected_action_summary(selected)) or {}),
        "status": status,
    }
    error = availability.get("error")
    if isinstance(error, dict):
        check["error"] = dict(error)
        check["reason"] = "command availability query failed"
    elif catalog_entry is None:
        check["reason"] = "command not present in catalog for selected context"
    else:
        policy = _command_execution_policy_blocker(command, catalog_entry)
        if policy is not None:
            check["status"] = "unavailable"
            check["reason"] = policy.get("message")
            check["error"] = policy
    checks.append(check)


def _record_planner_selection_drift(
    inspect_report: dict[str, object],
    *,
    before: dict[str, object],
    after: dict[str, object] | None,
    reason: str | None,
) -> None:
    planner = inspect_report.setdefault("planner", {})
    if not isinstance(planner, dict):
        return
    before_summary = _selected_action_summary(before)
    after_summary = _selected_action_summary(after)
    changed = before_summary != after_summary
    planner["selected_after_availability"] = after_summary
    if after_summary is not None:
        planner["selected_candidate_id"] = after_summary.get("candidate_id")
        planner["selected_command_id"] = after_summary.get("command_id")
    planner["selection_drift"] = {
        "status": "changed" if changed else "stable",
        "before": before_summary,
        "after": after_summary,
        "reason": reason,
    }


def _is_full_listing_locator(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return all(isinstance(value.get(key), str) and value.get(key) for key in ("target_id", "projection_hash", "row_key", "kind"))


def _command_availability(target_id: str, context: dict[str, object]) -> dict[str, object]:
    try:
        payload = server.route_request(
            "GET",
            f"/api/projects/{target_id}/commands",
            _command_query_from_context(context),
        )
    except server.CommandContractError as exc:
        return {"error": {"code": exc.code, "message": str(exc)}}
    data = payload.get("data")
    return dict(data) if isinstance(data, dict) else {}


def _command_query_from_context(context: dict[str, object]) -> dict[str, list[str]]:
    kind = context.get("kind")
    if kind == "row":
        query = {"context": ["row"], "locator": [json.dumps(context["locator"])]}
        _copy_provenance_context_to_query(query, context)
        return query
    if kind == "element":
        query = {
            "context": ["element"],
            "locator": [json.dumps(context["locator"])],
            "element_id": [str(context["element_id"])],
        }
        for key in ("layout_name", "base_symbol", "base_evidence_id", "contradicted_evidence_id", "reason"):
            value = context.get(key)
            if isinstance(value, str) and value:
                query[key] = [value]
        _copy_provenance_context_to_query(query, context)
        return query
    if kind == "range":
        return {"context": ["range"], "locators": [json.dumps(context["locators"])]}
    if kind == "review_item":
        return {"context": ["review-item"], "item_id": [str(context["item_id"])]}
    return {"context": ["target"]}


def _copy_provenance_context_to_query(query: dict[str, list[str]], context: dict[str, object]) -> None:
    for key in (
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "confidence",
        "contradicted_evidence_id",
        "reason",
    ):
        value = context.get(key)
        if isinstance(value, str) and value:
            query[key] = [value]
    for key in ("path_lifetime_scope", "conflicts", "parent_evidence_ids", "cleanup_scope"):
        value = context.get(key)
        if isinstance(value, dict | list):
            query[key] = [json.dumps(value, sort_keys=True, separators=(",", ":"))]


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
