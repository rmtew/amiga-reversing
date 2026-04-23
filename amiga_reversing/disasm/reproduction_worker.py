from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import traceback
from pathlib import Path
from typing import NoReturn

from amiga_reversing.disasm.facts_v2_source_refusal import (
    facts_v2_source_refused,
    facts_v2_source_refused_report,
)
from amiga_reversing.disasm.reproduction import (
    REPRODUCTION_SOURCE_SYNTAX,
    rebuilt_target_dir,
    reproduction_input_stamp,
    run_reproduction,
)


def main(argv: list[str] | None = None) -> NoReturn:
    parser = argparse.ArgumentParser()
    parser.add_argument("target_name", nargs="?")
    parser.add_argument("--project-root")
    parser.add_argument("--output")
    parser.add_argument("--progress")
    parser.add_argument("--batch-input")
    parser.add_argument("--batch-output")
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args(argv)

    if args.batch_input:
        raise SystemExit(_run_batch(args))
    if not args.target_name or not args.project_root or not args.output or not args.progress:
        parser.error("single-target mode requires target_name, --project-root, --output, and --progress")
    exit_code = _run_one_target(
        args.target_name,
        project_root=Path(args.project_root),
        output_path=Path(args.output),
        progress_path=Path(args.progress),
        profile=args.profile,
    )
    raise SystemExit(exit_code)


def _run_batch(args: argparse.Namespace) -> int:
    batch_input = Path(args.batch_input)
    batch_output = Path(args.batch_output) if args.batch_output else batch_input.with_suffix(".out.json")
    payload = json.loads(batch_input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("batch input must be a JSON object")
    project_root = Path(str(payload.get("project_root") or args.project_root or ""))
    if not str(project_root):
        raise ValueError("batch input requires project_root")
    profile = bool(payload.get("profile")) or bool(args.profile)
    targets = payload.get("targets")
    if not isinstance(targets, list):
        raise ValueError("batch input requires targets")
    results: list[dict[str, object]] = []
    for item in targets:
        if not isinstance(item, dict):
            continue
        target_name = item.get("target")
        output = item.get("output")
        progress = item.get("progress")
        if not isinstance(target_name, str) or not isinstance(output, str) or not isinstance(progress, str):
            continue
        exit_code = _run_one_target(
            target_name,
            project_root=project_root,
            output_path=Path(output),
            progress_path=Path(progress),
            profile=profile,
        )
        results.append({"target": target_name, "output": output, "progress": progress, "exit_code": exit_code})
    _write_json(batch_output, {"status": "ok", "targets": results})
    return 0


def _run_one_target(
    target_name: str,
    *,
    project_root: Path,
    output_path: Path,
    progress_path: Path,
    profile: bool,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        started_at = time.perf_counter()
        started_wall_at = time.time()
        _write_progress(
            progress_path,
            {
                "target": target_name,
                "phase": "prepare",
                "updated_at": time.time(),
                "elapsed_seconds": 0.0,
            },
        )
        input_stamp = reproduction_input_stamp(target_name, project_root=project_root)
        _write_progress(
            progress_path,
            {
                "target": target_name,
                "phase": "analysis",
                "updated_at": time.time(),
                "elapsed_seconds": 0.0,
                "backend": input_stamp.get("backend"),
                "analysis_backend": input_stamp.get("analysis_backend"),
                "original_size": input_stamp.get("original_size"),
                "assembler_cpu": input_stamp.get("assembler_cpu"),
            },
        )
        source_syntax = input_stamp.get("source_syntax")
        if not isinstance(source_syntax, str) or not source_syntax:
            source_syntax = REPRODUCTION_SOURCE_SYNTAX
        rows = []
        source_text: str | None = None
        listing_profile: dict[str, object] = {}
        source_refused = False
        source_sha256: str | None = None
        facts_v2_defer_source_to_reproduction = True
        if listing_profile:
            source_refused = facts_v2_source_refused(listing_profile)
            source_sha256 = (
                _sha256_text(source_text)
                if source_text is not None and not source_refused
                else None
            )
            comparison_profile = _comparison_profile(listing_profile, source_sha256)
            if comparison_profile:
                listing_profile = {**listing_profile, "comparison": comparison_profile}
        analyzed_at = time.perf_counter()
        _write_progress(
            progress_path,
            {
                "target": target_name,
                "phase": "reproduction_prepare",
                "updated_at": time.time(),
                "elapsed_seconds": round(analyzed_at - started_at, 4),
                "row_count": len(rows),
                "listing_profile": listing_profile,
                "analysis_backend": input_stamp.get("analysis_backend"),
                "source_size": len(source_text.encode("utf-8")) if source_text is not None else None,
                "source_sha256": source_sha256,
            },
        )
        if source_refused:
            out_dir = rebuilt_target_dir(target_name, project_root=project_root)
            report = facts_v2_source_refused_report(
                target_name,
                input_stamp=input_stamp,
                listing_profile=listing_profile,
                source_path=out_dir / "source.s",
                rebuilt_path=out_dir / "rebuilt.bin",
                started_at=started_wall_at,
            )
        else:
            report = run_reproduction(
                target_name,
                rows=rows,
                project_root=project_root,
                pre_rendered_source_text=source_text,
                progress_callback=lambda event: _write_progress(
                    progress_path,
                    {
                        **event,
                        "row_count": len(rows),
                        "listing_profile": listing_profile,
                        "analysis_backend": input_stamp.get("analysis_backend"),
                        "source_sha256": source_sha256,
                    },
                ),
                profile=profile,
            )
            report_listing_profile = report.get("listing_profile")
            if isinstance(report_listing_profile, dict):
                comparison_profile = _comparison_profile(report_listing_profile, None)
                listing_profile = (
                    {**report_listing_profile, "comparison": comparison_profile}
                    if comparison_profile
                    else report_listing_profile
                )
                source_refused = facts_v2_source_refused(listing_profile)
        finished_at = time.perf_counter()
        total_seconds = round(finished_at - started_at, 4)
        _write_json(
            output_path,
            {
                "status": "ok",
                "report": report,
                "row_count": len(rows),
                "duration_seconds": total_seconds,
                "timings": {
                    "analysis_seconds": round(analyzed_at - started_at, 4),
                    "reproduction_seconds": round(finished_at - analyzed_at, 4),
                    "total_seconds": total_seconds,
                },
                "listing_profile": listing_profile,
                "source_sha256": source_sha256,
            },
        )
        _write_progress(
            progress_path,
            {
                "target": target_name,
                "phase": "done",
                "updated_at": time.time(),
                "elapsed_seconds": total_seconds,
                "row_count": len(rows),
                "status": report.get("status"),
                "analysis_backend": input_stamp.get("analysis_backend"),
            },
        )
        return 0
    except Exception as exc:
        _write_progress(
            progress_path,
            {
                "target": target_name,
                "phase": "crashed",
                "updated_at": time.time(),
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        _write_json(
            output_path,
            {
                "status": "crashed",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(limit=20),
            },
        )
        return 1


def _write_json(path: Path, payload: dict[str, object]) -> None:
    _write_json_atomic(path, payload)


def _write_progress(path: Path, payload: dict[str, object]) -> None:
    _write_json_atomic(path, payload)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _comparison_profile(listing_profile: dict[str, object], source_sha256: str | None) -> dict[str, object]:
    facts_v2 = listing_profile.get("facts_v2")
    if not isinstance(facts_v2, dict):
        return {}
    result: dict[str, object] = {
        "rendered_source_sha256": source_sha256,
        "facts_v2_render_ir_hash": facts_v2.get("render_ir_hash"),
        "facts_v2_preview_source_hash": facts_v2.get("preview_source_hash"),
        "facts_v2_preview_source_enabled": facts_v2.get("preview_source_enabled"),
        "facts_v2_asm_source_hash": facts_v2.get("asm_source_hash"),
        "facts_v2_asm_source_enabled": facts_v2.get("asm_source_enabled"),
        "facts_v2_asm_source_refused": facts_v2.get("asm_source_refused"),
        "facts_v2_asm_source_bytes": facts_v2.get("asm_source_bytes"),
        "facts_v2_asm_source_relocation_exprs": facts_v2.get("asm_source_relocation_exprs"),
        "facts_v2_asm_source_symbolic_instructions": facts_v2.get(
            "asm_source_symbolic_instructions"
        ),
        "facts_v2_asm_source_lossy_numeric_hunk_relocations": facts_v2.get(
            "asm_source_lossy_numeric_hunk_relocations"
        ),
        "facts_v2_asm_source_instruction_render_failures": facts_v2.get(
            "asm_source_instruction_render_failures"
        ),
        "facts_v2_asm_source_instruction_byte_mismatches": facts_v2.get(
            "asm_source_instruction_byte_mismatches"
        ),
        "facts_v2_asm_source_instruction_relocation_failures": facts_v2.get(
            "asm_source_instruction_relocation_failures"
        ),
        "facts_v2_asm_source_relocation_anchor_refusals": facts_v2.get(
            "asm_source_relocation_anchor_refusals"
        ),
        "facts_v2_asm_source_unassemblable_hunk_data_relocation_refusals": facts_v2.get(
            "asm_source_unassemblable_hunk_data_relocation_refusals"
        ),
        "facts_v2_asm_source_unassemblable_hunk_base_register_relocation_refusals": facts_v2.get(
            "asm_source_unassemblable_hunk_base_register_relocation_refusals"
        ),
        "facts_v2_asm_source_first_failure_kind": facts_v2.get("asm_source_first_failure_kind"),
        "facts_v2_asm_source_first_failure_section": facts_v2.get("asm_source_first_failure_section"),
        "facts_v2_asm_source_first_failure_offset": facts_v2.get("asm_source_first_failure_offset"),
        "facts_v2_asm_source_first_failure_aux_offset": facts_v2.get(
            "asm_source_first_failure_aux_offset"
        ),
        "facts_v2_unresolved_labels": facts_v2.get("unresolved_labels"),
        "facts_v2_interior_conflicts": facts_v2.get("interior_conflicts"),
        "facts_v2_interior_conflicts_resolved_by_demote": facts_v2.get(
            "interior_conflicts_resolved_by_demote"
        ),
        "facts_v2_interior_conflicts_unresolved": facts_v2.get("interior_conflicts_unresolved"),
        "facts_v2_relocation_failures": facts_v2.get("relocation_failures"),
        "facts_v2_relocation_anchors": facts_v2.get("relocation_anchors"),
        "facts_v2_first_relocation_anchor_kind": facts_v2.get(
            "first_relocation_anchor_kind"
        ),
        "facts_v2_first_relocation_anchor_section": facts_v2.get(
            "first_relocation_anchor_section"
        ),
        "facts_v2_first_relocation_anchor_offset": facts_v2.get(
            "first_relocation_anchor_offset"
        ),
        "facts_v2_first_relocation_anchor_target_section": facts_v2.get(
            "first_relocation_anchor_target_section"
        ),
        "facts_v2_first_relocation_anchor_width": facts_v2.get(
            "first_relocation_anchor_width"
        ),
        "facts_v2_first_relocation_anchor_platform_record_kind": facts_v2.get(
            "first_relocation_anchor_platform_record_kind"
        ),
        "facts_v2_first_relocation_anchor_raw_value": facts_v2.get(
            "first_relocation_anchor_raw_value"
        ),
        "facts_v2_first_relocation_anchor_addend": facts_v2.get(
            "first_relocation_anchor_addend"
        ),
        "facts_v2_relocation_anchor_instruction_bytes": facts_v2.get(
            "relocation_anchor_instruction_bytes"
        ),
        "facts_v2_relocation_anchor_data_payloads": facts_v2.get(
            "relocation_anchor_data_payloads"
        ),
        "facts_v2_relocation_anchor_unknown_contexts": facts_v2.get(
            "relocation_anchor_unknown_contexts"
        ),
        "facts_v2_unassemblable_hunk_data_relocations": facts_v2.get(
            "unassemblable_hunk_data_relocations"
        ),
        "facts_v2_unassemblable_hunk_base_register_relocations": facts_v2.get(
            "unassemblable_hunk_base_register_relocations"
        ),
        "facts_v2_first_relocation_anchor_context": facts_v2.get(
            "first_relocation_anchor_context"
        ),
        "facts_v2_first_relocation_anchor_instruction_offset": facts_v2.get(
            "first_relocation_anchor_instruction_offset"
        ),
        "facts_v2_first_relocation_failure_reason": facts_v2.get(
            "first_relocation_failure_reason"
        ),
        "facts_v2_first_relocation_failure_section": facts_v2.get(
            "first_relocation_failure_section"
        ),
        "facts_v2_first_relocation_failure_offset": facts_v2.get(
            "first_relocation_failure_offset"
        ),
        "facts_v2_first_relocation_failure_target_section": facts_v2.get(
            "first_relocation_failure_target_section"
        ),
        "facts_v2_first_relocation_failure_width": facts_v2.get(
            "first_relocation_failure_width"
        ),
        "facts_v2_first_relocation_failure_raw_value": facts_v2.get(
            "first_relocation_failure_raw_value"
        ),
        "facts_v2_first_relocation_failure_computed_target": facts_v2.get(
            "first_relocation_failure_computed_target"
        ),
        "facts_v2_code_start_facts": facts_v2.get("code_start_facts"),
        "facts_v2_code_start_section_entries": facts_v2.get("code_start_section_entries"),
        "facts_v2_code_start_policy_entry_offsets": facts_v2.get(
            "code_start_policy_entry_offsets"
        ),
        "facts_v2_code_start_policy_entry_points": facts_v2.get(
            "code_start_policy_entry_points"
        ),
        "facts_v2_code_start_control_targets": facts_v2.get("code_start_control_targets"),
        "facts_v2_code_start_fallthroughs": facts_v2.get("code_start_fallthroughs"),
        "facts_v2_code_start_inline_resumes": facts_v2.get("code_start_inline_resumes"),
        "facts_v2_required_instruction_failures": facts_v2.get("required_instruction_failures"),
        "facts_v2_unsupported_instruction_demotes": facts_v2.get(
            "unsupported_instruction_demotes"
        ),
        "facts_v2_first_required_instruction_failure_section": facts_v2.get(
            "first_required_instruction_failure_section"
        ),
        "facts_v2_first_required_instruction_failure_offset": facts_v2.get(
            "first_required_instruction_failure_offset"
        ),
        "facts_v2_first_required_instruction_failure_reason": facts_v2.get(
            "first_required_instruction_failure_reason"
        ),
        "facts_v2_first_required_instruction_failure_source_section": facts_v2.get(
            "first_required_instruction_failure_source_section"
        ),
        "facts_v2_first_required_instruction_failure_source_offset": facts_v2.get(
            "first_required_instruction_failure_source_offset"
        ),
        "facts_v2_first_unsupported_instruction_demote_section": facts_v2.get(
            "first_unsupported_instruction_demote_section"
        ),
        "facts_v2_first_unsupported_instruction_demote_offset": facts_v2.get(
            "first_unsupported_instruction_demote_offset"
        ),
        "facts_v2_first_unsupported_instruction_demote_reason": facts_v2.get(
            "first_unsupported_instruction_demote_reason"
        ),
        "facts_v2_first_unsupported_instruction_demote_source_section": facts_v2.get(
            "first_unsupported_instruction_demote_source_section"
        ),
        "facts_v2_first_unsupported_instruction_demote_source_offset": facts_v2.get(
            "first_unsupported_instruction_demote_source_offset"
        ),
        "facts_v2_opcode_relocation_conflicts_resolved_by_demote": facts_v2.get(
            "opcode_relocation_conflicts_resolved_by_demote"
        ),
        "facts_v2_first_opcode_relocation_conflict_section": facts_v2.get(
            "first_opcode_relocation_conflict_section"
        ),
        "facts_v2_first_opcode_relocation_conflict_offset": facts_v2.get(
            "first_opcode_relocation_conflict_offset"
        ),
        "facts_v2_first_opcode_relocation_conflict_aux_offset": facts_v2.get(
            "first_opcode_relocation_conflict_aux_offset"
        ),
        "facts_v2_render_ir_statements": facts_v2.get("render_ir_statements"),
    }
    failures = []
    if int(facts_v2.get("unresolved_labels") or 0) != 0:
        failures.append("facts_v2_unresolved_labels")
    if int(facts_v2.get("interior_conflicts_unresolved") or 0) != 0:
        failures.append("facts_v2_interior_conflicts_unresolved")
    if int(facts_v2.get("relocation_failures") or 0) != 0:
        failures.append("facts_v2_relocation_failures")
    if int(facts_v2.get("relocation_anchor_instruction_bytes") or 0) != 0:
        failures.append("facts_v2_relocation_anchor_instruction_bytes")
    if int(facts_v2.get("relocation_anchor_unknown_contexts") or 0) != 0:
        failures.append("facts_v2_relocation_anchor_unknown_contexts")
    if int(facts_v2.get("required_instruction_failures") or 0) != 0:
        failures.append("facts_v2_required_instruction_failures")
    result["structural_invariant_failures"] = failures
    source_failures = []
    if int(facts_v2.get("asm_source_instruction_render_failures") or 0) != 0:
        source_failures.append("facts_v2_asm_source_instruction_render_failures")
    if int(facts_v2.get("asm_source_instruction_byte_mismatches") or 0) != 0:
        source_failures.append("facts_v2_asm_source_instruction_byte_mismatches")
    if int(facts_v2.get("asm_source_instruction_relocation_failures") or 0) != 0:
        source_failures.append("facts_v2_asm_source_instruction_relocation_failures")
    if int(facts_v2.get("asm_source_relocation_anchor_refusals") or 0) != 0:
        source_failures.append("facts_v2_asm_source_relocation_anchor_refusals")
    if facts_v2.get("asm_source_refused") is True and not source_failures and not failures:
        source_failures.append("facts_v2_asm_source_refused")
    result["source_invariant_failures"] = source_failures
    return result


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


if __name__ == "__main__":
    main()
