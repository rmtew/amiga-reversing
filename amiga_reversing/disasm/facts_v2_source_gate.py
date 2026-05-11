from __future__ import annotations

import hashlib
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from amiga_reversing.disasm.c_backend import (
    listing_artifact_source_text_with_c_backend_profile,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths

type JsonDict = dict[str, object]

ASM_SOURCE_COUNTERS = (
    "asm_source_enabled",
    "asm_source_refused",
    "asm_source_symbolic_instructions",
    "asm_source_instruction_render_failures",
    "asm_source_instruction_byte_mismatches",
    "asm_source_instruction_relocation_failures",
    "asm_source_relocation_anchor_refusals",
    "asm_source_unassemblable_hunk_data_relocation_refusals",
    "asm_source_unassemblable_hunk_base_register_relocation_refusals",
    "asm_source_unresolved_labels",
    "asm_source_invalid_interior_references",
    "asm_source_lossy_numeric_hunk_relocations",
)
ASM_SOURCE_HARD_FAILURE_COUNTERS = (
    "asm_source_refused",
    "asm_source_instruction_render_failures",
    "asm_source_instruction_byte_mismatches",
    "asm_source_instruction_relocation_failures",
    "asm_source_relocation_anchor_refusals",
    "asm_source_unassemblable_hunk_data_relocation_refusals",
    "asm_source_unassemblable_hunk_base_register_relocation_refusals",
    "asm_source_unresolved_labels",
    "asm_source_invalid_interior_references",
)


def facts_v2_source_gate_report_for_target(
    target: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> JsonDict:
    started = time.perf_counter()
    source_errors: dict[str, str] = {}
    source_text = ""
    profile: Mapping[str, object] = {}
    try:
        paths = resolve_project_paths(target, project_root=project_root, require_entities=False)
        with effective_metadata_file(paths.target_dir) as metadata_path:
            source_text, raw_profile = listing_artifact_source_text_with_c_backend_profile(
                paths.binary_source,
                metadata_path=metadata_path,
                project_root=project_root,
            )
            profile = raw_profile
    except OSError as exc:
        source_errors["facts_v2_listing_artifact_source"] = str(exc)
    facts_v2 = _mapping_field(profile, "facts_v2")
    counters = _counter_values(facts_v2)
    gate_failures = _gate_failures(
        source_errors=source_errors,
        counters=counters,
    )
    return {
        "schema_version": 1,
        "target": target,
        "status": "failed" if gate_failures else "passed",
        "gate_passed": not gate_failures,
        "gate_failures": gate_failures,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "source_errors": source_errors,
        "source_fingerprint": _source_fingerprint(source_text),
        "facts_v2": {
            "asm_source_counters": counters,
            "decoded_candidates": _profile_int(facts_v2, "decoded_candidates"),
            "accepted_instructions": _profile_int(facts_v2, "accepted_instructions"),
            "data_spans": _profile_int(facts_v2, "data_spans"),
            "labels_created": _profile_int(facts_v2, "labels_created"),
            "labels_referenced": _profile_int(facts_v2, "labels_referenced"),
            "queue_iterations": _profile_int(facts_v2, "queue_iterations"),
            "decode_seconds": _profile_float(facts_v2, "decode_seconds"),
            "seed_seconds": _profile_float(facts_v2, "seed_seconds"),
            "fixed_point_seconds": _profile_float(facts_v2, "fixed_point_seconds"),
            "fixed_point_reachable_seconds": _profile_float(
                facts_v2, "fixed_point_reachable_seconds"
            ),
            "fixed_point_reachable_decode_seconds": _profile_float(
                facts_v2, "fixed_point_reachable_decode_seconds"
            ),
            "fixed_point_reachable_validate_seconds": _profile_float(
                facts_v2, "fixed_point_reachable_validate_seconds"
            ),
            "fixed_point_reachable_accept_seconds": _profile_float(
                facts_v2, "fixed_point_reachable_accept_seconds"
            ),
            "fixed_point_reachable_target_seconds": _profile_float(
                facts_v2, "fixed_point_reachable_target_seconds"
            ),
            "fixed_point_reachable_relocation_seconds": _profile_float(
                facts_v2, "fixed_point_reachable_relocation_seconds"
            ),
            "fixed_point_reachable_fallthrough_seconds": _profile_float(
                facts_v2, "fixed_point_reachable_fallthrough_seconds"
            ),
            "fixed_point_index_seconds": _profile_float(facts_v2, "fixed_point_index_seconds"),
            "fixed_point_required_label_conflict_seconds": _profile_float(
                facts_v2, "fixed_point_required_label_conflict_seconds"
            ),
            "fixed_point_opcode_relocation_conflict_seconds": _profile_float(
                facts_v2, "fixed_point_opcode_relocation_conflict_seconds"
            ),
            "fixed_point_rebuild_accepted_seconds": _profile_float(
                facts_v2, "fixed_point_rebuild_accepted_seconds"
            ),
            "fixed_point_relocation_anchor_seconds": _profile_float(
                facts_v2, "fixed_point_relocation_anchor_seconds"
            ),
            "fixed_point_materialize_labels_seconds": _profile_float(
                facts_v2, "fixed_point_materialize_labels_seconds"
            ),
            "fixed_point_data_span_seconds": _profile_float(
                facts_v2, "fixed_point_data_span_seconds"
            ),
            "fixed_point_invariant_seconds": _profile_float(
                facts_v2, "fixed_point_invariant_seconds"
            ),
            "render_ir_seconds": _profile_float(facts_v2, "render_ir_seconds"),
            "source_render_seconds": _profile_float(facts_v2, "source_render_seconds"),
        },
    }


def facts_v2_source_gate_report_for_targets(
    targets: Sequence[str],
    *,
    project_root: Path = PROJECT_ROOT,
) -> JsonDict:
    reports = [
        facts_v2_source_gate_report_for_target(target, project_root=project_root)
        for target in targets
    ]
    return {
        "schema_version": 1,
        "summary": _summary(reports),
        "targets": reports,
    }


def _summary(reports: Sequence[Mapping[str, object]]) -> JsonDict:
    return {
        "target_count": len(reports),
        "passed_count": sum(1 for report in reports if report.get("status") == "passed"),
        "failed_count": sum(1 for report in reports if report.get("status") == "failed"),
        "gate_passed": all(report.get("gate_passed") is True for report in reports),
        "gate_failed_count": sum(1 for report in reports if report.get("gate_passed") is not True),
        "first_gate_failure_target": _first_gate_failure_target(reports),
        "gate_failure_counts": _gate_failure_counts(reports),
        "asm_source_symbolic_instructions": sum(
            _nested_int(report, ("facts_v2", "asm_source_counters", "asm_source_symbolic_instructions"))
            or 0
            for report in reports
        ),
        "asm_source_lossy_numeric_hunk_relocations": sum(
            _nested_int(report, ("facts_v2", "asm_source_counters", "asm_source_lossy_numeric_hunk_relocations"))
            or 0
            for report in reports
        ),
        "elapsed_seconds": round(
            sum(
                value
                for report in reports
                if isinstance((value := report.get("elapsed_seconds")), int | float)
            ),
            3,
        ),
    }


def _gate_failures(
    *,
    source_errors: Mapping[str, str],
    counters: Mapping[str, object],
) -> list[str]:
    failures: list[str] = []
    if source_errors:
        failures.append("source_unavailable")
    if counters.get("asm_source_enabled") is False:
        failures.append("facts_v2_asm_source_disabled")
    for counter in ASM_SOURCE_HARD_FAILURE_COUNTERS:
        value = counters.get(counter)
        failed = value is True or (isinstance(value, int) and not isinstance(value, bool) and value > 0)
        if failed:
            failures.append(f"facts_v2_{counter}")
    return failures


def _gate_failure_counts(reports: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for report in reports:
        failures = report.get("gate_failures")
        if isinstance(failures, Sequence) and not isinstance(failures, str | bytes):
            for failure in failures:
                if isinstance(failure, str):
                    counts[failure] = counts.get(failure, 0) + 1
    return counts


def _first_gate_failure_target(reports: Sequence[Mapping[str, object]]) -> str | None:
    for report in reports:
        if report.get("gate_passed") is True:
            continue
        target = report.get("target")
        return target if isinstance(target, str) else None
    return None


def _counter_values(facts_v2_profile: Mapping[str, object]) -> JsonDict:
    counters: JsonDict = {}
    for key in ASM_SOURCE_COUNTERS:
        value = facts_v2_profile.get(key)
        if isinstance(value, bool | int) and not isinstance(value, float):
            counters[key] = value
    return counters


def _source_fingerprint(source_text: str) -> JsonDict:
    encoded = source_text.encode("utf-8")
    return {
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "byte_count": len(encoded),
        "line_count": len(source_text.splitlines()),
    }


def _mapping_field(payload: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = payload.get(key)
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    return {}


def _nested_int(payload: Mapping[str, object], keys: Sequence[str]) -> int | None:
    current: object = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    if isinstance(current, bool):
        return None
    if isinstance(current, int):
        return current
    if isinstance(current, float) and current.is_integer():
        return int(current)
    return None


def _profile_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return 0


def _profile_float(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    return 0.0
