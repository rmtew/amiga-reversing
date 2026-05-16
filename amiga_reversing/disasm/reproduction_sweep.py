from __future__ import annotations

import json
import re
import time
from collections import Counter
from enum import StrEnum
from pathlib import Path
from typing import cast

JsonObject = dict[str, object]


class ReproductionSweepStatus(StrEnum):
    ACCEPTED_MISMATCH = "accepted_mismatch"
    ASSEMBLER_ERROR = "assembler_error"
    BINARY_MISMATCH = "binary_mismatch"
    CONTENT_MATCH = "content_match"
    CRASHED = "crashed"
    EXACT = "exact"
    IMPORT_FAILED = "import_failed"
    RENDER_ERROR = "render_error"
    SEMANTIC_MATCH = "semantic_match"
    TIMEOUT = "timeout"
    TOOL_ERROR = "tool_error"
    UNSUPPORTED = "unsupported"


FAILURE_STATUSES = frozenset(
    {
        ReproductionSweepStatus.ASSEMBLER_ERROR,
        ReproductionSweepStatus.BINARY_MISMATCH,
        ReproductionSweepStatus.CRASHED,
        ReproductionSweepStatus.IMPORT_FAILED,
        ReproductionSweepStatus.RENDER_ERROR,
        ReproductionSweepStatus.TIMEOUT,
        ReproductionSweepStatus.TOOL_ERROR,
    }
)

NON_EXACT_MATCH_STATUSES = frozenset(
    {
        ReproductionSweepStatus.ACCEPTED_MISMATCH,
        ReproductionSweepStatus.CONTENT_MATCH,
        ReproductionSweepStatus.SEMANTIC_MATCH,
    }
)
ACCEPTED_MISMATCH_POLICY: dict[str, str] = {
    "atari_relocation_target_out_of_range": (
        "Atari relocation payload computes a target outside the target section; facts_v2 refuses source "
        "instead of manufacturing invalid symbolic output."
    ),
    "lossy_hunk_reloc32": (
        "Amiga HUNK_RELOC32 payload is kept numerically with annotated lossy relocation semantics; "
        "payload bytes reproduce but original relocation encoding/semantics are not recreated."
    ),
}

SOURCE_RENDER_DEFAULT_GATE_COUNTERS = (
    "unaccepted_unresolved_labels",
    "unaccepted_interior_conflicts_unresolved",
    "unaccepted_relocation_failures",
    "unaccepted_relocation_anchor_instruction_bytes",
    "unaccepted_relocation_anchor_unknown_contexts",
    "unaccepted_required_instruction_failures",
    "unaccepted_asm_source_instruction_render_failures",
    "unaccepted_asm_source_instruction_byte_mismatches",
    "unaccepted_asm_source_instruction_relocation_failures",
    "unaccepted_asm_source_relocation_anchor_refusals",
)


def import_failure_record(message: str) -> JsonObject:
    return {
        "target": None,
        "status": ReproductionSweepStatus.IMPORT_FAILED,
        "exact": False,
        "backend": None,
        "error_signature": _signature(message),
        "message": message,
    }


def crash_record(target_name: str, exc: BaseException) -> JsonObject:
    message = f"{type(exc).__name__}: {exc}"
    return {
        "target": target_name,
        "status": ReproductionSweepStatus.CRASHED,
        "exact": False,
        "backend": None,
        "error_signature": _signature(message),
        "message": message,
    }


def timeout_record(
    target_name: str,
    timeout_seconds: int,
    *,
    progress: JsonObject | None = None,
    duration_seconds: float | None = None,
) -> JsonObject:
    timeout_phase = _str(progress.get("phase") if progress else None, "unknown")
    message = f"target reproduction exceeded {timeout_seconds}s in phase {timeout_phase}"
    record: JsonObject = {
        "target": target_name,
        "status": ReproductionSweepStatus.TIMEOUT,
        "exact": False,
        "backend": _str_or_none(progress.get("backend") if progress else None),
        "analysis_backend": _str_or_none(progress.get("analysis_backend") if progress else None),
        "error_signature": message,
        "message": message,
        "timeout_seconds": timeout_seconds,
        "timeout_phase": timeout_phase,
    }
    if duration_seconds is not None:
        record["duration_seconds"] = duration_seconds
    if progress:
        record["progress"] = progress
        listing_profile = _dict_or_none(progress.get("listing_profile"))
        if listing_profile is not None:
            record["listing_profile"] = listing_profile
        for key in ("row_count", "source_size", "rebuilt_size", "original_size"):
            value = progress.get(key)
            if isinstance(value, int):
                record[key] = value
        source_sha256 = _str_or_none(progress.get("source_sha256"))
        if source_sha256 is not None:
            record["source_sha256"] = source_sha256
        updated_at = _float_or_none(progress.get("updated_at"))
        if updated_at is not None:
            record["timeout_phase_elapsed_seconds"] = round(_now() - updated_at, 4)
    return record


def _parse_sweep_status(value: object) -> ReproductionSweepStatus:
    if not isinstance(value, str):
        raise TypeError("reproduction sweep status must be a string")
    try:
        return ReproductionSweepStatus(value)
    except ValueError:
        allowed = ", ".join(status.value for status in ReproductionSweepStatus)
        raise ValueError(f"invalid reproduction sweep status {value!r}; expected one of {allowed}") from None


def _record_status(record: JsonObject) -> ReproductionSweepStatus:
    value = record.get("status")
    if not isinstance(value, ReproductionSweepStatus):
        raise TypeError("reproduction sweep record status must be a ReproductionSweepStatus")
    return value


def record_from_reproduction_report(target_name: str, report: JsonObject) -> JsonObject:
    input_stamp = _dict(report.get("input_stamp"))
    reproduction_policy = _dict(input_stamp.get("reproduction_policy"))
    status = _parse_sweep_status(report.get("status"))
    issues = _dict_list(report.get("issues"))
    diagnostics = _dict_list(report.get("assembler_diagnostics"))
    diff_ranges = _dict_list(report.get("diff_ranges"))
    file_layout = _dict_list(report.get("file_layout"))
    file_shape_diagnostics = _dict_list(report.get("file_shape_diagnostics"))
    canonical_file_shape_diagnostics = _dict_list(report.get("canonical_file_shape_diagnostics"))
    comparison = _dict_or_none(report.get("comparison"))
    oracle_compatibility = _dict_list(report.get("oracle_compatibility"))
    first_diff = _dict_or_none(report.get("first_diff"))
    first_diff_offset = _int_or_none(first_diff.get("offset") if first_diff else None)
    first_diff_layout = (
        _layout_at_offset(file_layout, first_diff_offset) if first_diff_offset is not None else None
    )
    tool_error = _str_or_none(report.get("tool_error"))
    assembler_stderr = _str_or_none(report.get("assembler_stderr"))
    assembler_stdout = _str_or_none(report.get("assembler_stdout"))
    backend = _str_or_none(report.get("backend")) or _str_or_none(input_stamp.get("backend"))
    analysis_backend = _str_or_none(report.get("analysis_backend")) or _str_or_none(input_stamp.get("analysis_backend"))
    record: JsonObject = {
        "target": target_name,
        "status": status,
        "exact": bool(report.get("exact")),
        "backend": backend,
        "analysis_backend": analysis_backend,
        "assembler": _str_or_none(report.get("assembler")) or _str_or_none(input_stamp.get("assembler")),
        "reproduction_policy": reproduction_policy,
        "original_size": _int_or_none(report.get("original_size") or input_stamp.get("original_size")),
        "rebuilt_size": _int_or_none(report.get("rebuilt_size")),
        "first_diff": first_diff,
        "first_diff_layout_kind": _str_or_none(first_diff_layout.get("kind") if first_diff_layout else None),
        "first_diff_section_index": _int_or_none(
            first_diff_layout.get("section_index") if first_diff_layout else None
        ),
        "diff_range_count": len(diff_ranges),
        "diff_layout_counts": _diff_layout_counts(diff_ranges, file_layout),
        "file_shape_diagnostics": file_shape_diagnostics,
        "canonical_file_shape_diagnostics": canonical_file_shape_diagnostics,
        "comparison": comparison,
        "comparison_status": _str_or_none(comparison.get("status") if comparison else None),
        "canonical_full_file_exact": _bool_or_none(
            comparison.get("canonical_full_file_exact") if comparison else None
        ),
        "content_exact": _bool_or_none(comparison.get("content_exact") if comparison else None),
        "payload_exact": _bool_or_none(comparison.get("payload_exact") if comparison else None),
        "policy_adjusted_full_file_exact": _bool_or_none(
            (
                comparison.get("policy_adjusted_full_file_exact")
                if "policy_adjusted_full_file_exact" in comparison
                else comparison.get("full_file_exact")
            )
            if comparison
            else None
        ),
        "relocation_semantics_exact": _bool_or_none(
            comparison.get("relocation_semantics_exact") if comparison else None
        ),
        "relocation_encoding_exact": _bool_or_none(
            comparison.get("relocation_encoding_exact") if comparison else None
        ),
        "comparison_failure_kinds": _list_str(comparison.get("failure_kinds") if comparison else None),
        "oracle_compatibility": oracle_compatibility,
        "oracle_comparison_levels": _oracle_comparison_levels(oracle_compatibility),
        "issue_counts": _issue_counts(issues),
        "assembler_diagnostic_count": len(diagnostics),
        "assembler_error_signature": _assembler_signature(
            diagnostics,
            assembler_stderr=assembler_stderr,
            assembler_stdout=assembler_stdout,
        ),
        "tool_error": tool_error,
        "error_signature": _signature(tool_error or ""),
        "accepted_mismatch_kind": _str_or_none(report.get("accepted_mismatch_kind")),
        "accepted_mismatch_reason": _str_or_none(report.get("accepted_mismatch_reason")),
        "source_path": _str_or_none(report.get("source_path")),
        "rebuilt_path": _str_or_none(report.get("rebuilt_path")),
    }
    profile = _dict_or_none(report.get("profile"))
    if profile is not None:
        record["profile"] = profile
    listing_profile = _dict_or_none(report.get("listing_profile"))
    if listing_profile is not None:
        record["listing_profile"] = listing_profile
        comparison_profile = _dict_or_none(listing_profile.get("comparison"))
        if comparison_profile is not None:
            record["analysis_comparison"] = comparison_profile
    accepted_kind = _accepted_mismatch_kind(record)
    if accepted_kind is not None:
        record["status"] = ReproductionSweepStatus.ACCEPTED_MISMATCH
        record["accepted_mismatch_kind"] = accepted_kind
    return record


def _oracle_comparison_levels(oracle_compatibility: list[JsonObject]) -> dict[str, str]:
    levels: dict[str, str] = {}
    for oracle in oracle_compatibility:
        oracle_id = _str_or_none(oracle.get("oracle_id"))
        comparison_level = _str_or_none(oracle.get("comparison_level"))
        if oracle_id is not None and comparison_level is not None:
            levels[oracle_id] = comparison_level
    return levels


def reproduction_sweep_summary(
    records: list[JsonObject],
    *,
    limit: int | None,
    project_root: Path,
) -> JsonObject:
    records = [_with_accepted_mismatch_status(record) for record in records]
    status_counts = Counter(_record_status(record) for record in records)
    accepted_mismatch_kinds = _accepted_mismatch_kind_counts(records)
    backend_counts = Counter(
        _str(record.get("backend"), "unknown")
        for record in records
        if record.get("backend") is not None
    )
    analysis_backend_counts = Counter(
        _str(record.get("analysis_backend"), "unknown")
        for record in records
        if record.get("analysis_backend") is not None
    )
    facts_v2_invariant_failures = _facts_v2_invariant_failures(records)
    target_records = [
        record for record in records if _record_status(record) is not ReproductionSweepStatus.IMPORT_FAILED
    ]
    supported_records = [
        record for record in target_records if _record_status(record) is not ReproductionSweepStatus.UNSUPPORTED
    ]
    exact_count = status_counts.get(ReproductionSweepStatus.EXACT, 0)
    non_exact_match_count = sum(status_counts.get(status, 0) for status in NON_EXACT_MATCH_STATUSES)
    supported_count = len(supported_records)
    total_count = len(target_records)
    failure_records = [
        record
        for record in records
        if _record_status(record) in FAILURE_STATUSES
    ]
    exactness = _reproduction_exactness_summary(supported_records, exact_count)
    direct_source_comparison = _facts_v2_direct_source_comparison_summary(records)
    return {
        "version": 1,
        "project_root": str(project_root),
        "limit": limit,
        "score": {
            "exact": exact_count,
            "non_exact_match": non_exact_match_count,
            "supported": supported_count,
            "total_targets": total_count,
            "unsupported": status_counts.get(ReproductionSweepStatus.UNSUPPORTED, 0),
            "import_failed": status_counts.get(ReproductionSweepStatus.IMPORT_FAILED, 0),
            "failed_supported": max(0, supported_count - exact_count),
            "exact_supported_percent": _percent(exact_count, supported_count),
            "exact_all_targets_percent": _percent(exact_count, total_count),
        },
        "status_counts": dict(sorted(status_counts.items())),
        "accepted_mismatch_kinds": dict(sorted(accepted_mismatch_kinds.items())),
        "reproduction_exactness": exactness,
        "backend_counts": dict(sorted(backend_counts.items())),
        "analysis_backend_counts": dict(sorted(analysis_backend_counts.items())),
        "facts_v2_invariant_failures": facts_v2_invariant_failures,
        "timing": _timing_summary(records),
        "timeout_by_phase": _timeout_by_phase(records),
        "slowest_by_phase": _slowest_by_phase(records),
        "assembler_timing": _assembler_timing_summary(records),
        "c_backend_timing": _c_backend_timing_summary(records),
        "facts_v2_timing": _facts_v2_timing_summary(records),
        "facts_v2_direct_source_comparison": direct_source_comparison,
        "facts_v2_readiness": _facts_v2_readiness_summary(
            records,
            status_counts=status_counts,
            accepted_mismatch_kinds=accepted_mismatch_kinds,
            exactness=exactness,
            direct_source_comparison=direct_source_comparison,
            facts_v2_invariant_failures=facts_v2_invariant_failures,
        ),
        "failure_group_count": len(_failure_groups(failure_records)),
        "failure_groups": _failure_groups(failure_records),
        "failures": failure_records,
        "targets": records,
    }


def _with_accepted_mismatch_status(record: JsonObject) -> JsonObject:
    accepted_kind = _accepted_mismatch_kind(record)
    if accepted_kind is None:
        return record
    if _record_status(record) is ReproductionSweepStatus.ACCEPTED_MISMATCH:
        return record
    return {
        **record,
        "status": ReproductionSweepStatus.ACCEPTED_MISMATCH,
        "accepted_mismatch_kind": accepted_kind,
    }


def _accepted_mismatch_kind_counts(records: list[JsonObject]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        if _record_status(record) is not ReproductionSweepStatus.ACCEPTED_MISMATCH:
            continue
        kind = _accepted_mismatch_kind(record) or _str_or_none(record.get("accepted_mismatch_kind")) or "unknown"
        counts[kind] += 1
    return counts


def write_reproduction_sweep_report(path: Path, summary: JsonObject) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def format_reproduction_sweep_score(summary: JsonObject) -> str:
    score = _dict(summary.get("score"))
    statuses = _dict(summary.get("status_counts"))
    exact = _int_value(score.get("exact"))
    supported = _int_value(score.get("supported"))
    percent = _float_value(score.get("exact_supported_percent"))
    unsupported = _int_value(score.get("unsupported"))
    import_failed = _int_value(score.get("import_failed"))
    status_text = ", ".join(f"{key}={value}" for key, value in statuses.items())
    result = (
        f"Full reproduction score: {exact}/{supported} supported exact "
        f"({percent:.1f}%), unsupported={unsupported}, import_failed={import_failed}. "
        f"Statuses: {status_text}"
    )
    exactness = _dict(summary.get("reproduction_exactness"))
    comparison_targets = _int_value(exactness.get("comparison_targets"))
    if comparison_targets:
        accepted = _int_value(exactness.get("accepted_mismatch"))
        result += (
            f" Canonical/content/adjusted: "
            f"{_int_value(exactness.get('canonical_full_file_exact'))}/"
            f"{_int_value(exactness.get('content_exact'))}/"
            f"{_int_value(exactness.get('policy_adjusted_full_file_exact'))}"
            f" of {comparison_targets}."
        )
        if accepted:
            result += f" Accepted mismatches: {accepted}."
    return result


def _reproduction_exactness_summary(records: list[JsonObject], status_exact_count: int) -> JsonObject:
    comparison_records = [
        record for record in records if _dict_or_none(record.get("comparison")) is not None
    ]
    accepted_records = [record for record in records if _accepted_mismatch_kind(record) is not None]
    accepted_no_comparison = [
        record for record in accepted_records if _dict_or_none(record.get("comparison")) is None
    ]
    canonical = 0
    content = 0
    payload = 0
    adjusted = 0
    relocation_semantics = 0
    relocation_encoding = 0
    relocation_semantics_applicable = 0
    relocation_encoding_applicable = 0
    adjusted_only = 0
    content_only = 0
    accepted_mismatch = len(accepted_no_comparison)
    accepted_content = 0
    accepted_adjusted = 0
    canonical_mismatch_targets: list[str] = []
    content_mismatch_targets: list[str] = []
    adjusted_mismatch_targets: list[str] = []
    accepted_mismatch_targets: list[str] = []
    for record in accepted_no_comparison:
        target = _str_or_none(record.get("target"))
        if len(accepted_mismatch_targets) < 20 and target:
            accepted_mismatch_targets.append(target)
    for record in comparison_records:
        accepted = _accepted_mismatch_kind(record) is not None
        canonical_exact = record.get("canonical_full_file_exact") is True
        content_is_exact = record.get("content_exact") is True
        payload_is_exact = record.get("payload_exact") is True
        adjusted_exact = record.get("policy_adjusted_full_file_exact") is True
        relocation_semantics_value = record.get("relocation_semantics_exact")
        relocation_encoding_value = record.get("relocation_encoding_exact")
        relocation_semantics_exact = relocation_semantics_value is True
        relocation_encoding_exact = relocation_encoding_value is True
        if canonical_exact:
            canonical += 1
        if content_is_exact:
            content += 1
        if payload_is_exact:
            payload += 1
        if adjusted_exact:
            adjusted += 1
        if isinstance(relocation_semantics_value, bool):
            relocation_semantics_applicable += 1
            if relocation_semantics_exact:
                relocation_semantics += 1
        if isinstance(relocation_encoding_value, bool):
            relocation_encoding_applicable += 1
            if relocation_encoding_exact:
                relocation_encoding += 1
        if adjusted_exact and not canonical_exact:
            adjusted_only += 1
        if content_is_exact and not canonical_exact:
            content_only += 1
        target = _str_or_none(record.get("target"))
        if accepted:
            accepted_mismatch += 1
            if len(accepted_mismatch_targets) < 20 and target:
                accepted_mismatch_targets.append(target)
        if content_is_exact or accepted:
            accepted_content += 1
        if adjusted_exact or accepted:
            accepted_adjusted += 1
        if target and not canonical_exact and len(canonical_mismatch_targets) < 20:
            canonical_mismatch_targets.append(target)
        if target and not content_is_exact and not accepted and len(content_mismatch_targets) < 20:
            content_mismatch_targets.append(target)
        if target and not adjusted_exact and not accepted and len(adjusted_mismatch_targets) < 20:
            adjusted_mismatch_targets.append(target)
    comparison_count = len(comparison_records)
    return {
        "supported_targets": len(records),
        "comparison_targets": comparison_count,
        "missing_comparison_targets": len(records) - comparison_count - len(accepted_no_comparison),
        "status_exact": status_exact_count,
        "canonical_full_file_exact": canonical,
        "content_exact": content,
        "payload_exact": payload,
        "policy_adjusted_full_file_exact": adjusted,
        "accepted_mismatch": accepted_mismatch,
        "accepted_no_comparison": len(accepted_no_comparison),
        "accepted_content_or_lossy": accepted_content,
        "accepted_adjusted_or_lossy": accepted_adjusted,
        "relocation_semantics_exact": relocation_semantics,
        "relocation_encoding_exact": relocation_encoding,
        "relocation_semantics_applicable_targets": relocation_semantics_applicable,
        "relocation_encoding_applicable_targets": relocation_encoding_applicable,
        "policy_adjusted_only_exact": adjusted_only,
        "content_only_exact": content_only,
        "canonical_full_file_exact_percent": _percent(canonical, comparison_count),
        "content_exact_percent": _percent(content, comparison_count),
        "policy_adjusted_full_file_exact_percent": _percent(adjusted, comparison_count),
        "relocation_semantics_exact_percent": _percent(relocation_semantics, relocation_semantics_applicable),
        "relocation_encoding_exact_percent": _percent(relocation_encoding, relocation_encoding_applicable),
        "canonical_mismatch_targets": canonical_mismatch_targets,
        "content_mismatch_targets": content_mismatch_targets,
        "policy_adjusted_mismatch_targets": adjusted_mismatch_targets,
        "accepted_mismatch_targets": accepted_mismatch_targets,
    }


def _failure_groups(records: list[JsonObject]) -> list[JsonObject]:
    grouped: dict[str, JsonObject] = {}
    for record in records:
        status = _record_status(record)
        backend = _str(record.get("backend"), "unknown")
        kind, signature = _failure_kind_and_signature(record)
        key = f"{status}|{backend}|{kind}|{signature}"
        bucket = grouped.setdefault(
            key,
            {
                "key": key,
                "status": status,
                "backend": backend,
                "kind": kind,
                "signature": signature,
                "count": 0,
                "sample_targets": [],
            },
        )
        bucket["count"] = _int_value(bucket.get("count")) + 1
        samples = cast(list[str], bucket["sample_targets"])
        target = _str_or_none(record.get("target"))
        if target and len(samples) < 8:
            samples.append(target)
    return sorted(
        grouped.values(),
        key=lambda item: (-_int_value(item.get("count")), str(item["key"])),
    )


def _facts_v2_invariant_failures(records: list[JsonObject]) -> JsonObject:
    profiled_targets = 0
    unresolved = 0
    interior = 0
    interior_resolved = 0
    interior_unresolved = 0
    relocation = 0
    relocation_anchor = 0
    relocation_anchor_instruction_bytes = 0
    relocation_anchor_data_payloads = 0
    relocation_anchor_unknown_contexts = 0
    unassemblable_hunk_data_relocations = 0
    unassemblable_hunk_base_register_relocations = 0
    code_start_facts = 0
    code_start_section_entries = 0
    code_start_policy_entry_offsets = 0
    code_start_policy_entry_points = 0
    code_start_control_targets = 0
    code_start_fallthroughs = 0
    code_start_inline_resumes = 0
    required_instruction = 0
    unsupported_demotes = 0
    opcode_relocation_demotes = 0
    unaccepted_unresolved = 0
    unaccepted_interior_unresolved = 0
    unaccepted_relocation = 0
    unaccepted_relocation_anchor_instruction_bytes = 0
    unaccepted_relocation_anchor_unknown_contexts = 0
    unaccepted_required_instruction = 0
    source_render = 0
    source_mismatch = 0
    source_relocation = 0
    source_anchor = 0
    unaccepted_source_render = 0
    unaccepted_source_mismatch = 0
    unaccepted_source_relocation = 0
    unaccepted_source_anchor = 0
    source_unassemblable_hunk_data_relocation = 0
    source_unassemblable_hunk_base_register_relocation = 0
    asm_source_enabled_targets = 0
    asm_source_refused_targets = 0
    symbolic_instructions = 0
    lossy_numeric_hunk_relocations = 0
    affected_targets: list[str] = []
    unaccepted_affected_targets: list[str] = []
    accepted_invariant_targets: list[JsonObject] = []
    first_relocation_failures: list[JsonObject] = []
    first_relocation_anchors: list[JsonObject] = []
    source_affected_targets: list[str] = []
    unaccepted_source_affected_targets: list[str] = []
    first_source_failures: list[JsonObject] = []
    source_failure_signature_map: dict[tuple[object, ...], JsonObject] = {}
    for record in records:
        listing_profile = _dict_or_none(record.get("listing_profile"))
        comparison = _dict_or_none(record.get("analysis_comparison"))
        facts_v2 = _dict_or_none(listing_profile.get("facts_v2")) if listing_profile is not None else None
        if comparison is not None or facts_v2 is not None:
            profiled_targets += 1
        unresolved_count = _int_value(
            (comparison or {}).get("facts_v2_unresolved_labels")
            if comparison is not None
            else (facts_v2 or {}).get("unresolved_labels")
        )
        interior_count = _int_value(
            (comparison or {}).get("facts_v2_interior_conflicts")
            if comparison is not None
            else (facts_v2 or {}).get("interior_conflicts")
        )
        interior_resolved_count = _int_value(
            (comparison or {}).get("facts_v2_interior_conflicts_resolved_by_demote")
            if comparison is not None
            else (facts_v2 or {}).get("interior_conflicts_resolved_by_demote")
        )
        interior_unresolved_count = _int_value(
            (comparison or {}).get("facts_v2_interior_conflicts_unresolved")
            if comparison is not None
            else (facts_v2 or {}).get("interior_conflicts_unresolved")
        )
        relocation_count = _int_value(
            (comparison or {}).get("facts_v2_relocation_failures")
            if comparison is not None
            else (facts_v2 or {}).get("relocation_failures")
        )
        relocation_anchor_count = _int_value(
            (comparison or {}).get("facts_v2_relocation_anchors")
            if comparison is not None
            else (facts_v2 or {}).get("relocation_anchors")
        )
        relocation_anchor_instruction_bytes_count = _int_value(
            (comparison or {}).get("facts_v2_relocation_anchor_instruction_bytes")
            if comparison is not None
            else (facts_v2 or {}).get("relocation_anchor_instruction_bytes")
        )
        relocation_anchor_data_payloads_count = _int_value(
            (comparison or {}).get("facts_v2_relocation_anchor_data_payloads")
            if comparison is not None
            else (facts_v2 or {}).get("relocation_anchor_data_payloads")
        )
        relocation_anchor_unknown_contexts_count = _int_value(
            (comparison or {}).get("facts_v2_relocation_anchor_unknown_contexts")
            if comparison is not None
            else (facts_v2 or {}).get("relocation_anchor_unknown_contexts")
        )
        unassemblable_hunk_data_relocation_count = _int_value(
            (comparison or {}).get("facts_v2_unassemblable_hunk_data_relocations")
            if comparison is not None
            else (facts_v2 or {}).get("unassemblable_hunk_data_relocations")
        )
        unassemblable_hunk_base_register_relocation_count = _int_value(
            (comparison or {}).get("facts_v2_unassemblable_hunk_base_register_relocations")
            if comparison is not None
            else (facts_v2 or {}).get("unassemblable_hunk_base_register_relocations")
        )
        code_start_fact_count = _int_value(
            (comparison or {}).get("facts_v2_code_start_facts")
            if comparison is not None
            else (facts_v2 or {}).get("code_start_facts")
        )
        code_start_section_entry_count = _int_value(
            (comparison or {}).get("facts_v2_code_start_section_entries")
            if comparison is not None
            else (facts_v2 or {}).get("code_start_section_entries")
        )
        code_start_policy_entry_offset_count = _int_value(
            (comparison or {}).get("facts_v2_code_start_policy_entry_offsets")
            if comparison is not None
            else (facts_v2 or {}).get("code_start_policy_entry_offsets")
        )
        code_start_policy_entry_point_count = _int_value(
            (comparison or {}).get("facts_v2_code_start_policy_entry_points")
            if comparison is not None
            else (facts_v2 or {}).get("code_start_policy_entry_points")
        )
        code_start_control_target_count = _int_value(
            (comparison or {}).get("facts_v2_code_start_control_targets")
            if comparison is not None
            else (facts_v2 or {}).get("code_start_control_targets")
        )
        code_start_fallthrough_count = _int_value(
            (comparison or {}).get("facts_v2_code_start_fallthroughs")
            if comparison is not None
            else (facts_v2 or {}).get("code_start_fallthroughs")
        )
        code_start_inline_resume_count = _int_value(
            (comparison or {}).get("facts_v2_code_start_inline_resumes")
            if comparison is not None
            else (facts_v2 or {}).get("code_start_inline_resumes")
        )
        required_instruction_count = _int_value(
            (comparison or {}).get("facts_v2_required_instruction_failures")
            if comparison is not None
            else (facts_v2 or {}).get("required_instruction_failures")
        )
        unsupported_demote_count = _int_value(
            (comparison or {}).get("facts_v2_unsupported_instruction_demotes")
            if comparison is not None
            else (facts_v2 or {}).get("unsupported_instruction_demotes")
        )
        opcode_relocation_demote_count = _int_value(
            (comparison or {}).get("facts_v2_opcode_relocation_conflicts_resolved_by_demote")
            if comparison is not None
            else (facts_v2 or {}).get("opcode_relocation_conflicts_resolved_by_demote")
        )
        source_render_count = _int_value(
            (comparison or {}).get("facts_v2_asm_source_instruction_render_failures")
            if comparison is not None
            else (facts_v2 or {}).get("asm_source_instruction_render_failures")
        )
        source_mismatch_count = _int_value(
            (comparison or {}).get("facts_v2_asm_source_instruction_byte_mismatches")
            if comparison is not None
            else (facts_v2 or {}).get("asm_source_instruction_byte_mismatches")
        )
        source_relocation_count = _int_value(
            (comparison or {}).get("facts_v2_asm_source_instruction_relocation_failures")
            if comparison is not None
            else (facts_v2 or {}).get("asm_source_instruction_relocation_failures")
        )
        source_anchor_count = _int_value(
            (comparison or {}).get("facts_v2_asm_source_relocation_anchor_refusals")
            if comparison is not None
            else (facts_v2 or {}).get("asm_source_relocation_anchor_refusals")
        )
        source_unassemblable_hunk_data_relocation_count = _int_value(
            (comparison or {}).get(
                "facts_v2_asm_source_unassemblable_hunk_data_relocation_refusals"
            )
            if comparison is not None
            else (facts_v2 or {}).get("asm_source_unassemblable_hunk_data_relocation_refusals")
        )
        source_unassemblable_hunk_base_register_relocation_count = _int_value(
            (comparison or {}).get(
                "facts_v2_asm_source_unassemblable_hunk_base_register_relocation_refusals"
            )
            if comparison is not None
            else (facts_v2 or {}).get(
                "asm_source_unassemblable_hunk_base_register_relocation_refusals"
            )
        )
        symbolic_instruction_count = _int_value(
            (comparison or {}).get("facts_v2_asm_source_symbolic_instructions")
            if comparison is not None
            else (facts_v2 or {}).get("asm_source_symbolic_instructions")
        )
        lossy_numeric_hunk_relocation_count = _int_value(
            (comparison or {}).get("facts_v2_asm_source_lossy_numeric_hunk_relocations")
            if comparison is not None
            else (facts_v2 or {}).get("asm_source_lossy_numeric_hunk_relocations")
        )
        asm_source_enabled = (
            (comparison or {}).get("facts_v2_asm_source_enabled")
            if comparison is not None
            else (facts_v2 or {}).get("asm_source_enabled")
        ) is True
        asm_source_refused = (
            (comparison or {}).get("facts_v2_asm_source_refused")
            if comparison is not None
            else (facts_v2 or {}).get("asm_source_refused")
        ) is True
        if asm_source_enabled:
            asm_source_enabled_targets += 1
        if asm_source_refused:
            asm_source_refused_targets += 1
        unresolved += unresolved_count
        interior += interior_count
        interior_resolved += interior_resolved_count
        interior_unresolved += interior_unresolved_count
        relocation += relocation_count
        relocation_anchor += relocation_anchor_count
        relocation_anchor_instruction_bytes += relocation_anchor_instruction_bytes_count
        relocation_anchor_data_payloads += relocation_anchor_data_payloads_count
        relocation_anchor_unknown_contexts += relocation_anchor_unknown_contexts_count
        unassemblable_hunk_data_relocations += unassemblable_hunk_data_relocation_count
        unassemblable_hunk_base_register_relocations += (
            unassemblable_hunk_base_register_relocation_count
        )
        code_start_facts += code_start_fact_count
        code_start_section_entries += code_start_section_entry_count
        code_start_policy_entry_offsets += code_start_policy_entry_offset_count
        code_start_policy_entry_points += code_start_policy_entry_point_count
        code_start_control_targets += code_start_control_target_count
        code_start_fallthroughs += code_start_fallthrough_count
        code_start_inline_resumes += code_start_inline_resume_count
        required_instruction += required_instruction_count
        unsupported_demotes += unsupported_demote_count
        opcode_relocation_demotes += opcode_relocation_demote_count
        source_render += source_render_count
        source_mismatch += source_mismatch_count
        source_relocation += source_relocation_count
        source_anchor += source_anchor_count
        source_unassemblable_hunk_data_relocation += source_unassemblable_hunk_data_relocation_count
        source_unassemblable_hunk_base_register_relocation += (
            source_unassemblable_hunk_base_register_relocation_count
        )
        symbolic_instructions += symbolic_instruction_count
        lossy_numeric_hunk_relocations += lossy_numeric_hunk_relocation_count
        source_hard_failure_count = (
            source_render_count
            + source_mismatch_count
            + source_relocation_count
            + source_anchor_count
        )
        target_hard_failure_count = (
            unresolved_count
            + interior_unresolved_count
            + relocation_count
            + required_instruction_count
            + relocation_anchor_instruction_bytes_count
            + relocation_anchor_unknown_contexts_count
        )
        target = _str_or_none(record.get("target"))
        accepted_kind = _accepted_mismatch_kind(record)
        if accepted_kind is None:
            unaccepted_unresolved += unresolved_count
            unaccepted_interior_unresolved += interior_unresolved_count
            unaccepted_relocation += relocation_count
            unaccepted_required_instruction += required_instruction_count
            unaccepted_relocation_anchor_instruction_bytes += (
                relocation_anchor_instruction_bytes_count
            )
            unaccepted_relocation_anchor_unknown_contexts += (
                relocation_anchor_unknown_contexts_count
            )
            unaccepted_source_render += source_render_count
            unaccepted_source_mismatch += source_mismatch_count
            unaccepted_source_relocation += source_relocation_count
            unaccepted_source_anchor += source_anchor_count
        elif target and (target_hard_failure_count != 0 or source_hard_failure_count != 0):
            if len(accepted_invariant_targets) < 20:
                accepted_invariant_targets.append(
                    {
                        "target": target,
                        "accepted_mismatch_kind": accepted_kind,
                        "hard_failure_count": target_hard_failure_count,
                        "source_failure_count": source_hard_failure_count,
                    }
                )
        if target and (
            unresolved_count != 0 or interior_unresolved_count != 0 or relocation_count != 0
            or relocation_anchor_instruction_bytes_count != 0
            or relocation_anchor_unknown_contexts_count != 0
            or required_instruction_count != 0
        ) and len(affected_targets) < 20:
            affected_targets.append(target)
        if (
            accepted_kind is None
            and target
            and target_hard_failure_count != 0
            and len(unaccepted_affected_targets) < 20
        ):
            unaccepted_affected_targets.append(target)
        if target and relocation_count != 0 and len(first_relocation_failures) < 20:
            source = comparison if comparison is not None else facts_v2
            source = source or {}
            prefix = "facts_v2_" if comparison is not None else ""
            first_relocation_failures.append(
                {
                    "target": target,
                    "reason": source.get(f"{prefix}first_relocation_failure_reason"),
                    "section": source.get(f"{prefix}first_relocation_failure_section"),
                    "offset": source.get(f"{prefix}first_relocation_failure_offset"),
                    "target_section": source.get(
                        f"{prefix}first_relocation_failure_target_section"
                    ),
                    "raw_value": source.get(f"{prefix}first_relocation_failure_raw_value"),
                    "computed_target": source.get(
                        f"{prefix}first_relocation_failure_computed_target"
                    ),
                }
            )
        if target and relocation_anchor_count != 0 and len(first_relocation_anchors) < 20:
            source = comparison if comparison is not None else facts_v2
            source = source or {}
            prefix = "facts_v2_" if comparison is not None else ""
            first_relocation_anchors.append(
                {
                    "target": target,
                    "kind": source.get(f"{prefix}first_relocation_anchor_kind"),
                    "section": source.get(f"{prefix}first_relocation_anchor_section"),
                    "offset": source.get(f"{prefix}first_relocation_anchor_offset"),
                    "target_section": source.get(
                        f"{prefix}first_relocation_anchor_target_section"
                    ),
                    "record_kind": source.get(
                        f"{prefix}first_relocation_anchor_platform_record_kind"
                    ),
                    "raw_value": source.get(f"{prefix}first_relocation_anchor_raw_value"),
                    "addend": source.get(f"{prefix}first_relocation_anchor_addend"),
                    "context": source.get(f"{prefix}first_relocation_anchor_context"),
                    "instruction_offset": source.get(
                        f"{prefix}first_relocation_anchor_instruction_offset"
                    ),
                }
            )
        if target and (
            source_render_count != 0
            or source_mismatch_count != 0
            or source_relocation_count != 0
            or source_anchor_count != 0
        ):
            if len(source_affected_targets) < 20:
                source_affected_targets.append(target)
            if accepted_kind is None and len(unaccepted_source_affected_targets) < 20:
                unaccepted_source_affected_targets.append(target)
            if len(first_source_failures) < 20:
                source = comparison if comparison is not None else facts_v2
                source = source or {}
                prefix = "facts_v2_" if comparison is not None else ""
                first_source_failures.append(
                    {
                        "target": target,
                        "kind": source.get(f"{prefix}asm_source_first_failure_kind"),
                        "section": source.get(f"{prefix}asm_source_first_failure_section"),
                        "offset": source.get(f"{prefix}asm_source_first_failure_offset"),
                        "aux_offset": source.get(f"{prefix}asm_source_first_failure_aux_offset"),
                    }
                )
            source = comparison if comparison is not None else facts_v2
            source = source or {}
            prefix = "facts_v2_" if comparison is not None else ""
            failure_count = source_hard_failure_count
            signature_key = (
                source.get(f"{prefix}asm_source_first_failure_kind"),
                source.get(f"{prefix}first_relocation_anchor_kind"),
                source.get(f"{prefix}first_relocation_anchor_context"),
                source.get(f"{prefix}first_relocation_anchor_target_section"),
                source.get(f"{prefix}first_relocation_anchor_platform_record_kind"),
                source.get(f"{prefix}first_relocation_anchor_width"),
                source.get(f"{prefix}first_relocation_anchor_raw_value"),
                source.get(f"{prefix}first_relocation_anchor_addend"),
            )
            signature = source_failure_signature_map.get(signature_key)
            if signature is None:
                signature = {
                    "count": 0,
                    "target_count": 0,
                    "kind": signature_key[0],
                    "anchor_kind": signature_key[1],
                    "anchor_context": signature_key[2],
                    "target_section": signature_key[3],
                    "record_kind": signature_key[4],
                    "width": signature_key[5],
                    "raw_value": signature_key[6],
                    "addend": signature_key[7],
                    "first_target": target,
                    "first_section": source.get(f"{prefix}asm_source_first_failure_section"),
                    "first_offset": source.get(f"{prefix}asm_source_first_failure_offset"),
                    "first_aux_offset": source.get(f"{prefix}asm_source_first_failure_aux_offset"),
                }
                source_failure_signature_map[signature_key] = signature
            signature["count"] = _int_value(signature.get("count")) + failure_count
            signature["target_count"] = _int_value(signature.get("target_count")) + 1
    hard_failure_count = (
        unresolved + interior_unresolved + relocation + required_instruction +
        relocation_anchor_instruction_bytes + relocation_anchor_unknown_contexts
    )
    unaccepted_hard_failure_count = (
        unaccepted_unresolved
        + unaccepted_interior_unresolved
        + unaccepted_relocation
        + unaccepted_required_instruction
        + unaccepted_relocation_anchor_instruction_bytes
        + unaccepted_relocation_anchor_unknown_contexts
    )
    source_failure_count = source_render + source_mismatch + source_relocation + source_anchor
    unaccepted_source_failure_count = (
        unaccepted_source_render
        + unaccepted_source_mismatch
        + unaccepted_source_relocation
        + unaccepted_source_anchor
    )
    return {
        "profiled_targets": profiled_targets,
        "hard_failure_count": hard_failure_count,
        "unaccepted_hard_failure_count": unaccepted_hard_failure_count,
        "unresolved_labels": unresolved,
        "unaccepted_unresolved_labels": unaccepted_unresolved,
        "interior_conflicts": interior,
        "interior_conflicts_resolved_by_demote": interior_resolved,
        "interior_conflicts_unresolved": interior_unresolved,
        "unaccepted_interior_conflicts_unresolved": unaccepted_interior_unresolved,
        "relocation_failures": relocation,
        "unaccepted_relocation_failures": unaccepted_relocation,
        "relocation_anchors": relocation_anchor,
        "relocation_anchor_instruction_bytes": relocation_anchor_instruction_bytes,
        "unaccepted_relocation_anchor_instruction_bytes": (
            unaccepted_relocation_anchor_instruction_bytes
        ),
        "relocation_anchor_data_payloads": relocation_anchor_data_payloads,
        "relocation_anchor_unknown_contexts": relocation_anchor_unknown_contexts,
        "unaccepted_relocation_anchor_unknown_contexts": (
            unaccepted_relocation_anchor_unknown_contexts
        ),
        "unassemblable_hunk_data_relocations": unassemblable_hunk_data_relocations,
        "unassemblable_hunk_base_register_relocations": unassemblable_hunk_base_register_relocations,
        "code_start_facts": code_start_facts,
        "code_start_section_entries": code_start_section_entries,
        "code_start_policy_entry_offsets": code_start_policy_entry_offsets,
        "code_start_policy_entry_points": code_start_policy_entry_points,
        "code_start_control_targets": code_start_control_targets,
        "code_start_fallthroughs": code_start_fallthroughs,
        "code_start_inline_resumes": code_start_inline_resumes,
        "required_instruction_failures": required_instruction,
        "unaccepted_required_instruction_failures": unaccepted_required_instruction,
        "unsupported_instruction_demotes": unsupported_demotes,
        "opcode_relocation_conflicts_resolved_by_demote": opcode_relocation_demotes,
        "affected_targets": affected_targets,
        "unaccepted_affected_targets": unaccepted_affected_targets,
        "accepted_invariant_targets": accepted_invariant_targets,
        "first_relocation_failures": first_relocation_failures,
        "first_relocation_anchors": first_relocation_anchors,
        "source_failure_count": source_failure_count,
        "unaccepted_source_failure_count": unaccepted_source_failure_count,
        "asm_source_enabled_targets": asm_source_enabled_targets,
        "asm_source_refused_targets": asm_source_refused_targets,
        "asm_source_symbolic_instructions": symbolic_instructions,
        "asm_source_lossy_numeric_hunk_relocations": lossy_numeric_hunk_relocations,
        "asm_source_instruction_render_failures": source_render,
        "unaccepted_asm_source_instruction_render_failures": unaccepted_source_render,
        "asm_source_instruction_byte_mismatches": source_mismatch,
        "unaccepted_asm_source_instruction_byte_mismatches": unaccepted_source_mismatch,
        "asm_source_instruction_relocation_failures": source_relocation,
        "unaccepted_asm_source_instruction_relocation_failures": unaccepted_source_relocation,
        "asm_source_relocation_anchor_refusals": source_anchor,
        "unaccepted_asm_source_relocation_anchor_refusals": unaccepted_source_anchor,
        "asm_source_unassemblable_hunk_data_relocation_refusals": source_unassemblable_hunk_data_relocation,
        "asm_source_unassemblable_hunk_base_register_relocation_refusals": (
            source_unassemblable_hunk_base_register_relocation
        ),
        "source_affected_targets": source_affected_targets,
        "unaccepted_source_affected_targets": unaccepted_source_affected_targets,
        "first_source_failures": first_source_failures,
        "source_failure_signatures": sorted(
            source_failure_signature_map.values(),
            key=lambda item: (-_int_value(item.get("count")), str(item.get("kind")), str(item.get("first_target"))),
        )[:20],
    }


def _timing_summary(records: list[JsonObject]) -> JsonObject:
    timed_records = [
        record for record in records if _float_or_none(record.get("duration_seconds")) is not None
    ]
    durations = [
        cast(float, _float_or_none(record.get("duration_seconds")))
        for record in timed_records
    ]
    slowest = sorted(
        timed_records,
        key=lambda record: _float_value(record.get("duration_seconds")),
        reverse=True,
    )[:20]
    return {
        "timed_targets": len(timed_records),
        "total_seconds": round(sum(durations), 4),
        "max_seconds": round(max(durations), 4) if durations else 0.0,
        "average_seconds": round(sum(durations) / len(durations), 4) if durations else 0.0,
        "slowest_targets": [
            {
                "target": record.get("target"),
                "status": record.get("status"),
                "duration_seconds": record.get("duration_seconds"),
                "analysis_seconds": _phase_timing(record, "analysis_seconds"),
                "reproduction_seconds": _phase_timing(record, "reproduction_seconds"),
                "timeout_phase": record.get("timeout_phase"),
                "row_count": record.get("row_count"),
            }
            for record in slowest
        ],
    }


def _timeout_by_phase(records: list[JsonObject]) -> dict[str, int]:
    counts = Counter(
        _str(record.get("timeout_phase"), "unknown")
        for record in records
        if _record_status(record) is ReproductionSweepStatus.TIMEOUT
    )
    return dict(sorted(counts.items()))


def _slowest_by_phase(records: list[JsonObject]) -> dict[str, list[JsonObject]]:
    result: dict[str, list[JsonObject]] = {}
    for record in records:
        timeout_phase = _str(record.get("timeout_phase"), "")
        if timeout_phase and _float_or_none(record.get("duration_seconds")) is not None:
            result.setdefault(timeout_phase, []).append(
                _phase_slow_target(record, _float_value(record.get("duration_seconds")))
            )
        timings = _dict(record.get("worker_timings"))
        for timing_key, phase in (
            ("analysis_seconds", "analysis"),
            ("reproduction_seconds", "reproduction"),
        ):
            seconds = _float_or_none(timings.get(timing_key))
            if seconds is None:
                continue
            result.setdefault(phase, []).append(_phase_slow_target(record, seconds))
    for phase, items in result.items():
        result[phase] = sorted(
            items,
            key=lambda item: _float_value(item.get("phase_seconds")),
            reverse=True,
        )[:10]
    return dict(sorted(result.items()))


def _assembler_timing_summary(records: list[JsonObject]) -> JsonObject:
    phase_keys = (
        "assemble_seconds",
        "assembler_total_seconds",
        "assembler_parse_layout_seconds",
        "assembler_emit_object_seconds",
        "assembler_platform_finalize_seconds",
        "assembler_write_buffer_seconds",
        "assembler_write_file_seconds",
        "assembler_read_output_seconds",
    )
    count_keys = ("assembler_source_bytes", "assembler_rebuilt_bytes")
    profiled_targets = 0
    phase_totals: dict[str, float] = {}
    count_totals: Counter[str] = Counter()
    slowest_by_phase: dict[str, list[JsonObject]] = {}
    for record in records:
        profile = _dict(record.get("profile"))
        has_profile = False
        for key in phase_keys:
            seconds = _float_or_none(profile.get(key))
            if seconds is None:
                continue
            has_profile = True
            _add_float_total(phase_totals, key, seconds)
            if seconds > 0.0:
                slowest_by_phase.setdefault(key, []).append(
                    _c_backend_target_timing(record, key, seconds)
                )
        for key in count_keys:
            value = profile.get(key)
            if isinstance(value, int):
                has_profile = True
                count_totals[key] += value
        if has_profile:
            profiled_targets += 1
    return {
        "profiled_targets": profiled_targets,
        "phase_totals": _rounded_float_totals(phase_totals),
        "count_totals": dict(sorted(count_totals.items())),
        "slowest_by_phase": {
            key: sorted(
                items,
                key=lambda item: _float_value(item.get("phase_seconds")),
                reverse=True,
            )[:10]
            for key, items in sorted(slowest_by_phase.items())
        },
    }


def _c_backend_timing_summary(records: list[JsonObject]) -> JsonObject:
    profiled_targets = 0
    top_level_totals: dict[str, float] = {}
    section_phase_totals: dict[str, float] = {}
    amiga_fact_totals: Counter[str] = Counter()
    top_level_slowest: dict[str, list[JsonObject]] = {}
    section_hotspots: list[JsonObject] = []
    for record in records:
        listing_profile = _dict_or_none(record.get("listing_profile"))
        if listing_profile is None:
            continue
        timing = _dict(listing_profile.get("timing"))
        sections = _dict_list(listing_profile.get("sections"))
        if not timing and not sections:
            continue
        profiled_targets += 1
        for key, value in timing.items():
            seconds = _float_or_none(value)
            if seconds is None:
                continue
            _add_float_total(top_level_totals, key, seconds)
            top_level_slowest.setdefault(key, []).append(
                _c_backend_target_timing(record, key, seconds)
            )
        for section_position, section in enumerate(sections):
            section_timing = _section_timing(section)
            for key, value in section_timing.items():
                seconds = _float_or_none(value)
                if seconds is None or seconds <= 0.0:
                    continue
                _add_float_total(section_phase_totals, key, seconds)
                section_hotspots.append(
                    _c_backend_section_timing(record, section, section_position, key, seconds)
                )
            amiga_facts = _dict(section.get("amiga_facts"))
            for key, value in amiga_facts.items():
                if isinstance(value, int):
                    amiga_fact_totals[key] += value
    return {
        "profiled_targets": profiled_targets,
        "top_level_totals": _rounded_float_totals(top_level_totals),
        "section_phase_totals": _rounded_float_totals(section_phase_totals),
        "amiga_fact_totals": dict(sorted(amiga_fact_totals.items())),
        "slowest_top_level": {
            key: sorted(
                items,
                key=lambda item: _float_value(item.get("phase_seconds")),
                reverse=True,
            )[:10]
            for key, items in sorted(top_level_slowest.items())
        },
        "slowest_sections": sorted(
            section_hotspots,
            key=lambda item: _float_value(item.get("phase_seconds")),
            reverse=True,
        )[:25],
    }


def _facts_v2_timing_summary(records: list[JsonObject]) -> JsonObject:
    phase_keys = (
        "decode_seconds",
        "seed_seconds",
        "fixed_point_seconds",
        "fixed_point_reachable_seconds",
        "fixed_point_reachable_decode_seconds",
        "fixed_point_reachable_validate_seconds",
        "fixed_point_reachable_accept_seconds",
        "fixed_point_reachable_target_seconds",
        "fixed_point_reachable_relocation_seconds",
        "fixed_point_reachable_fallthrough_seconds",
        "fixed_point_index_seconds",
        "fixed_point_required_label_conflict_seconds",
        "fixed_point_opcode_relocation_conflict_seconds",
        "fixed_point_rebuild_accepted_seconds",
        "fixed_point_relocation_anchor_seconds",
        "fixed_point_materialize_labels_seconds",
        "fixed_point_data_span_seconds",
        "fixed_point_invariant_seconds",
        "render_ir_seconds",
        "source_render_seconds",
    )
    count_keys = (
        "decoded_candidates",
        "accepted_instructions",
        "data_spans",
        "labels_created",
        "labels_referenced",
        "queue_iterations",
        "render_ir_statements",
        "render_ir_instructions",
        "render_ir_data_spans",
        "render_ir_labels",
        "asm_source_symbolic_instructions",
        "asm_source_relocation_exprs",
        "asm_source_lines",
        "asm_source_bytes",
    )
    profiled_targets = 0
    phase_totals: dict[str, float] = {}
    count_totals: Counter[str] = Counter()
    slowest_by_phase: dict[str, list[JsonObject]] = {}
    for record in records:
        facts_v2 = _facts_v2_profile(record)
        if not facts_v2:
            continue
        has_profile = False
        for key in phase_keys:
            seconds = _float_or_none(facts_v2.get(key))
            if seconds is None:
                continue
            has_profile = True
            if seconds <= 0.0:
                continue
            _add_float_total(phase_totals, key, seconds)
            slowest_by_phase.setdefault(key, []).append(
                _facts_v2_phase_target(record, facts_v2, key, seconds)
            )
        for key in count_keys:
            value = facts_v2.get(key)
            if isinstance(value, int):
                has_profile = True
                count_totals[key] += value
        if has_profile:
            profiled_targets += 1
    return {
        "profiled_targets": profiled_targets,
        "phase_totals": _rounded_float_totals(phase_totals),
        "count_totals": dict(sorted(count_totals.items())),
        "slowest_by_phase": {
            key: sorted(
                items,
                key=lambda item: _float_value(item.get("phase_seconds")),
                reverse=True,
            )[:10]
            for key, items in sorted(slowest_by_phase.items())
        },
    }


def _facts_v2_direct_source_comparison_summary(records: list[JsonObject]) -> JsonObject:
    compared = 0
    matched = 0
    mismatched = 0
    overrode_direct = 0
    source_full_file_exact = 0
    source_content_compared = 0
    source_content_exact = 0
    source_payload_exact = 0
    source_relocation_semantics_applicable = 0
    source_relocation_semantics_exact = 0
    source_relocation_encoding_applicable = 0
    source_relocation_encoding_exact = 0
    mismatch_targets: list[JsonObject] = []
    source_content_mismatch_targets: list[JsonObject] = []
    for record in records:
        profile = _dict(record.get("profile"))
        if profile.get("facts_v2_direct_source_compare") != 1.0:
            continue
        compared += 1
        if profile.get("facts_v2_direct_source_match") == 1.0:
            matched += 1
        else:
            mismatched += 1
            if len(mismatch_targets) < 20:
                mismatch_targets.append(
                    {
                        "target": record.get("target"),
                        "status": record.get("status"),
                        "backend": record.get("backend"),
                        "direct_sha256": profile.get("facts_v2_direct_rebuilt_sha256"),
                        "source_sha256": profile.get("facts_v2_source_assembled_sha256"),
                    }
                )
        if (
            profile.get("facts_v2_direct_source_compare_overrode_direct") == 1.0
            or profile.get("facts_v2_direct_source_compare_fell_back") == 1.0
        ):
            overrode_direct += 1
        if profile.get("facts_v2_source_full_file_exact") == 1.0:
            source_full_file_exact += 1
        source_content_value = _profile_flag(profile.get("facts_v2_source_content_exact"))
        if source_content_value is not None:
            source_content_compared += 1
            if source_content_value:
                source_content_exact += 1
            elif len(source_content_mismatch_targets) < 20:
                source_content_mismatch_targets.append(
                    {
                        "target": record.get("target"),
                        "status": record.get("status"),
                        "backend": record.get("backend"),
                        "direct_sha256": profile.get("facts_v2_direct_rebuilt_sha256"),
                        "source_sha256": profile.get("facts_v2_source_assembled_sha256"),
                        "source_payload_exact": _profile_flag(
                            profile.get("facts_v2_source_payload_exact")
                        ),
                        "source_relocation_semantics_exact": _profile_flag(
                            profile.get("facts_v2_source_relocation_semantics_exact")
                        ),
                    }
                )
        if profile.get("facts_v2_source_payload_exact") == 1.0:
            source_payload_exact += 1
        source_relocation_semantics_value = _profile_flag(
            profile.get("facts_v2_source_relocation_semantics_exact")
        )
        if source_relocation_semantics_value is not None:
            source_relocation_semantics_applicable += 1
            if source_relocation_semantics_value:
                source_relocation_semantics_exact += 1
        source_relocation_encoding_value = _profile_flag(
            profile.get("facts_v2_source_relocation_encoding_exact")
        )
        if source_relocation_encoding_value is not None:
            source_relocation_encoding_applicable += 1
            if source_relocation_encoding_value:
                source_relocation_encoding_exact += 1
    return {
        "compared_targets": compared,
        "matched_targets": matched,
        "mismatched_targets": mismatched,
        "overrode_direct_targets": overrode_direct,
        "fell_back_targets": overrode_direct,
        "source_full_file_exact_targets": source_full_file_exact,
        "source_content_compared_targets": source_content_compared,
        "source_content_exact_targets": source_content_exact,
        "source_payload_exact_targets": source_payload_exact,
        "source_relocation_semantics_applicable_targets": source_relocation_semantics_applicable,
        "source_relocation_semantics_exact_targets": source_relocation_semantics_exact,
        "source_relocation_encoding_applicable_targets": source_relocation_encoding_applicable,
        "source_relocation_encoding_exact_targets": source_relocation_encoding_exact,
        "first_mismatch": mismatch_targets[0] if mismatch_targets else None,
        "mismatch_targets": mismatch_targets,
        "first_source_content_mismatch": (
            source_content_mismatch_targets[0] if source_content_mismatch_targets else None
        ),
        "source_content_mismatch_targets": source_content_mismatch_targets,
    }


def _facts_v2_readiness_summary(
    records: list[JsonObject],
    *,
    status_counts: Counter[ReproductionSweepStatus],
    accepted_mismatch_kinds: Counter[str],
    exactness: JsonObject,
    direct_source_comparison: JsonObject,
    facts_v2_invariant_failures: JsonObject,
) -> JsonObject:
    blockers: list[str] = []
    direct_rebuild_blockers: list[str] = []
    analysis_counts = Counter(
        _str(record.get("analysis_backend"), "unknown")
        for record in records
        if record.get("analysis_backend") is not None
    )
    facts_v2_analysis_records = analysis_counts.get("facts_v2", 0)
    non_facts_v2_analysis_records = sum(
        count for analysis_stamp, count in analysis_counts.items() if analysis_stamp != "facts_v2"
    )
    if facts_v2_analysis_records == 0:
        blockers.append("facts_v2_not_used")
    if non_facts_v2_analysis_records:
        blockers.append("non_facts_v2_analysis_records_present")
    hard_failure_count = sum(status_counts.get(status, 0) for status in FAILURE_STATUSES)
    if hard_failure_count:
        blockers.append("hard_reproduction_failures")
    unexpected_accepted_mismatch_kinds = sorted(
        kind for kind in accepted_mismatch_kinds if kind not in ACCEPTED_MISMATCH_POLICY
    )
    if unexpected_accepted_mismatch_kinds:
        blockers.append("unexpected_accepted_mismatch_policy")
    compared = _int_value(direct_source_comparison.get("compared_targets"))
    mismatched = _int_value(direct_source_comparison.get("mismatched_targets"))
    direct_rebuild_records = sum(
        1 for record in records if _dict(record.get("profile")).get("facts_v2_direct_rebuild_c_api") == 1.0
    )
    missing_comparison = _int_value(exactness.get("missing_comparison_targets"))
    if missing_comparison:
        blockers.append("missing_reproduction_comparison_records")
    comparison_targets = _int_value(exactness.get("comparison_targets"))
    accepted_content = _int_value(
        exactness.get("accepted_content_or_lossy", exactness.get("content_exact"))
    )
    accepted_adjusted = _int_value(
        exactness.get("accepted_adjusted_or_lossy", exactness.get("policy_adjusted_full_file_exact"))
    )
    if direct_rebuild_records == 0:
        direct_rebuild_blockers.append("direct_rebuild_not_run")
    elif facts_v2_analysis_records and direct_rebuild_records < facts_v2_analysis_records:
        direct_rebuild_blockers.append("direct_rebuild_not_run_for_all_facts_v2")
    if hard_failure_count:
        direct_rebuild_blockers.append("hard_reproduction_failures")
    if unexpected_accepted_mismatch_kinds:
        direct_rebuild_blockers.append("unexpected_accepted_mismatch_policy")
    if missing_comparison:
        direct_rebuild_blockers.append("missing_reproduction_comparison_records")
    if comparison_targets == 0:
        direct_rebuild_blockers.append("direct_rebuild_no_comparison_records")
    elif accepted_content != comparison_targets:
        direct_rebuild_blockers.append("direct_rebuild_content_mismatches")
    elif accepted_adjusted != comparison_targets:
        direct_rebuild_blockers.append("direct_rebuild_policy_adjusted_mismatches")
    accepted_mismatch_policy = {
        "ready": not unexpected_accepted_mismatch_kinds,
        "known_kinds": sorted(ACCEPTED_MISMATCH_POLICY),
        "unexpected_kinds": unexpected_accepted_mismatch_kinds,
        "kinds": [
            {
                "kind": kind,
                "count": accepted_mismatch_kinds[kind],
                "policy": ACCEPTED_MISMATCH_POLICY.get(kind, "No policy recorded."),
            }
            for kind in sorted(accepted_mismatch_kinds)
        ],
    }
    source_render_blockers = _source_render_default_blockers(
        facts_v2_invariant_failures,
        direct_source_comparison,
    )
    source_render_default_ready = not source_render_blockers
    return {
        "analysis_path": "facts_v2",
        "non_facts_v2_analysis_records": non_facts_v2_analysis_records,
        "facts_v2_analysis_records": facts_v2_analysis_records,
        "hard_reproduction_failures": hard_failure_count,
        "accepted_mismatch_kinds": dict(sorted(accepted_mismatch_kinds.items())),
        "accepted_mismatch_count": sum(accepted_mismatch_kinds.values()),
        "accepted_mismatch_policy_ready": not unexpected_accepted_mismatch_kinds,
        "accepted_mismatch_policy": accepted_mismatch_policy,
        "direct_rebuild_records": direct_rebuild_records,
        "direct_rebuild_source_compared_targets": compared,
        "direct_rebuild_source_mismatched_targets": mismatched,
        "direct_rebuild_default_ready": not direct_rebuild_blockers,
        "direct_rebuild_blockers": direct_rebuild_blockers,
        "source_render_default_ready": source_render_default_ready,
        "source_render_default_blocker": (
            source_render_blockers[0] if source_render_blockers else None
        ),
        "source_render_default_blockers": source_render_blockers,
        "facts_v2_reproduction_default_ready": not blockers,
        "blockers": blockers,
    }


def _source_render_default_blockers(
    facts_v2_invariant_failures: JsonObject,
    direct_source_comparison: JsonObject,
) -> list[str]:
    blockers: list[str] = []
    profiled_targets = _int_value(facts_v2_invariant_failures.get("profiled_targets"))
    enabled_targets = _int_value(facts_v2_invariant_failures.get("asm_source_enabled_targets"))
    if profiled_targets == 0:
        blockers.append("facts_v2_profiles_missing")
    elif enabled_targets != profiled_targets:
        blockers.append(f"asm_source_enabled_targets={enabled_targets}/{profiled_targets}")
    if _int_value(facts_v2_invariant_failures.get("asm_source_symbolic_instructions")) == 0:
        blockers.append("facts_v2_symbolic_source_not_rendered")
    for counter in SOURCE_RENDER_DEFAULT_GATE_COUNTERS:
        value = _int_value(facts_v2_invariant_failures.get(counter))
        if value:
            blockers.append(f"{counter}={value}")
    if _list_length(facts_v2_invariant_failures.get("unaccepted_affected_targets")):
        blockers.append("unaccepted_affected_targets_present")
    if _list_length(facts_v2_invariant_failures.get("unaccepted_source_affected_targets")):
        blockers.append("unaccepted_source_affected_targets_present")
    compared_targets = _int_value(direct_source_comparison.get("compared_targets"))
    source_content_compared = _int_value(direct_source_comparison.get("source_content_compared_targets"))
    source_content_exact = _int_value(direct_source_comparison.get("source_content_exact_targets"))
    if compared_targets == 0:
        blockers.append("direct_source_comparison_not_run")
    elif source_content_compared != compared_targets:
        blockers.append(f"source_content_compared_targets={source_content_compared}/{compared_targets}")
    elif source_content_exact != compared_targets:
        blockers.append(f"source_content_exact_targets={source_content_exact}/{compared_targets}")
    return blockers


def _facts_v2_profile(record: JsonObject) -> JsonObject:
    listing_profile = _dict(record.get("listing_profile"))
    return _dict(listing_profile.get("facts_v2"))


def _facts_v2_phase_target(
    record: JsonObject,
    facts_v2: JsonObject,
    phase: str,
    seconds: float,
) -> JsonObject:
    return {
        "target": record.get("target"),
        "status": record.get("status"),
        "backend": record.get("backend"),
        "phase": phase,
        "phase_seconds": round(seconds, 4),
        "duration_seconds": record.get("duration_seconds"),
        "original_size": record.get("original_size"),
        "decoded_candidates": facts_v2.get("decoded_candidates"),
        "accepted_instructions": facts_v2.get("accepted_instructions"),
        "queue_iterations": facts_v2.get("queue_iterations"),
        "render_ir_statements": facts_v2.get("render_ir_statements"),
        "asm_source_bytes": facts_v2.get("asm_source_bytes"),
    }


def _c_backend_target_timing(record: JsonObject, phase: str, seconds: float) -> JsonObject:
    return {
        "target": record.get("target"),
        "status": record.get("status"),
        "backend": record.get("backend"),
        "phase": phase,
        "phase_seconds": round(seconds, 4),
        "duration_seconds": record.get("duration_seconds"),
        "row_count": record.get("row_count"),
        "original_size": record.get("original_size"),
    }


def _c_backend_section_timing(
    record: JsonObject,
    section: JsonObject,
    section_position: int,
    phase: str,
    seconds: float,
) -> JsonObject:
    section_index = _int_or_none(section.get("section_index"))
    if section_index is None:
        section_index = section_position
    return {
        "target": record.get("target"),
        "status": record.get("status"),
        "backend": record.get("backend"),
        "section_index": section_index,
        "section_name": section.get("name"),
        "section_size": section.get("size"),
        "phase": phase,
        "phase_seconds": round(seconds, 4),
        "duration_seconds": record.get("duration_seconds"),
        "row_count": record.get("row_count"),
    }


def _section_timing(section: JsonObject) -> JsonObject:
    nested = _dict(section.get("timing"))
    if nested:
        return nested
    return {
        key: value
        for key, value in section.items()
        if key.endswith("_seconds")
    }


def _phase_slow_target(record: JsonObject, phase_seconds: float) -> JsonObject:
    return {
        "target": record.get("target"),
        "status": record.get("status"),
        "phase_seconds": round(phase_seconds, 4),
        "duration_seconds": record.get("duration_seconds"),
        "row_count": record.get("row_count"),
    }


def _phase_timing(record: JsonObject, key: str) -> float | None:
    timings = _dict(record.get("worker_timings"))
    return _float_or_none(timings.get(key))


def _failure_kind_and_signature(record: JsonObject) -> tuple[str, str]:
    status = _record_status(record)
    if status is ReproductionSweepStatus.BINARY_MISMATCH:
        diagnostics = _dict_list(record.get("file_shape_diagnostics"))
        if not diagnostics:
            diagnostics = _dict_list(record.get("canonical_file_shape_diagnostics"))
        if diagnostics:
            first = diagnostics[0]
            return _str(first.get("kind"), "file_shape"), _shape_signature(first)
        failure_kinds = _list_str(record.get("comparison_failure_kinds"))
        if failure_kinds:
            return failure_kinds[0], ""
        kind = _str(record.get("first_diff_layout_kind"), "unknown_diff")
        section_index = _int_or_none(record.get("first_diff_section_index"))
        section = "?" if section_index is None else str(section_index)
        return kind, f"section={section}"
    if status is ReproductionSweepStatus.ASSEMBLER_ERROR:
        return "assembler", _str(record.get("assembler_error_signature"), "")
    if status is ReproductionSweepStatus.TIMEOUT:
        return "timeout", _str(record.get("timeout_phase"), "unknown")
    if status in {
        ReproductionSweepStatus.TOOL_ERROR,
        ReproductionSweepStatus.RENDER_ERROR,
        ReproductionSweepStatus.CRASHED,
        ReproductionSweepStatus.IMPORT_FAILED,
    }:
        return status.value, _str(record.get("error_signature"), "")
    return status.value, ""


def _accepted_mismatch_kind(record: JsonObject) -> str | None:
    existing = _str_or_none(record.get("accepted_mismatch_kind"))
    if existing in ACCEPTED_MISMATCH_POLICY:
        return existing
    if _accepted_lossy_hunk_reloc32_mismatch(record):
        return "lossy_hunk_reloc32"
    if _accepted_atari_target_out_of_range_source_refusal(record):
        return "atari_relocation_target_out_of_range"
    return None


def _accepted_lossy_hunk_reloc32_mismatch(record: JsonObject) -> bool:
    if _str(record.get("backend"), "") != "amiga-hunk":
        return False
    comparison = _dict(record.get("comparison"))
    if not comparison or comparison.get("payload_exact") is not True:
        return False
    if comparison.get("full_file_exact") is True:
        return False
    if comparison.get("relocation_semantics_exact") is not False:
        return False
    if _facts_v2_lossy_hunk_reloc32_count(record) <= 0:
        return False
    diagnostics = _dict_list(comparison.get("semantic_diagnostics"))
    if not diagnostics:
        diagnostics = _dict_list(record.get("canonical_file_shape_diagnostics"))
    if not diagnostics:
        return False
    return all(_is_lossy_hunk_reloc32_diagnostic(item) for item in diagnostics)


def _accepted_atari_target_out_of_range_source_refusal(record: JsonObject) -> bool:
    if _str(record.get("backend"), "") != "atari-st":
        return False
    if _str(record.get("analysis_backend"), "") != "facts_v2":
        return False
    status = _record_status(record)
    if status not in {ReproductionSweepStatus.RENDER_ERROR, ReproductionSweepStatus.ACCEPTED_MISMATCH}:
        return False
    facts_v2 = _dict(_dict(record.get("listing_profile")).get("facts_v2"))
    comparison = _dict(record.get("analysis_comparison"))
    source_refused = (
        facts_v2.get("asm_source_refused") is True
        or comparison.get("facts_v2_asm_source_refused") is True
    )
    reason = _str(
        facts_v2.get("first_relocation_failure_reason")
        or comparison.get("facts_v2_first_relocation_failure_reason"),
        "",
    )
    failures = max(
        _int_value(facts_v2.get("relocation_failures")),
        _int_value(comparison.get("facts_v2_relocation_failures")),
    )
    if source_refused and reason == "target_out_of_range" and failures > 0:
        return True
    tool_error = _str(record.get("tool_error") or record.get("error_signature"), "")
    return (
        "facts_v2 asm source refused" in tool_error
        and "relocation_reason=target_out_of_range" in tool_error
    )


def _facts_v2_lossy_hunk_reloc32_count(record: JsonObject) -> int:
    listing_profile = _dict(record.get("listing_profile"))
    facts_v2 = _dict(listing_profile.get("facts_v2"))
    value = _int_value(facts_v2.get("asm_source_lossy_numeric_hunk_relocations"))
    if value:
        return value
    comparison = _dict(record.get("analysis_comparison"))
    return _int_value(comparison.get("facts_v2_asm_source_lossy_numeric_hunk_relocations"))


def _is_lossy_hunk_reloc32_diagnostic(diagnostic: JsonObject) -> bool:
    if _str(diagnostic.get("kind"), "") not in {
        "extra_relocation_group",
        "missing_relocation_group",
        "offset_order_mismatch",
        "target_section_mismatch",
    }:
        return False
    sides = [_dict(diagnostic.get("original")), _dict(diagnostic.get("rebuilt"))]
    present_sides = [side for side in sides if side]
    if not present_sides:
        return False
    return all(side.get("record_id") == 1004 for side in present_sides)


def _diff_layout_counts(
    diff_ranges: list[JsonObject],
    file_layout: list[JsonObject],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for diff_range in diff_ranges:
        start = _int_or_none(diff_range.get("start"))
        if start is None:
            continue
        layout = _layout_at_offset(file_layout, start)
        counts[_str(layout.get("kind") if layout else None, "unknown")] += 1
    return dict(sorted(counts.items()))


def _issue_counts(issues: list[JsonObject]) -> dict[str, int]:
    counts = Counter(_str(issue.get("kind"), "unknown") for issue in issues)
    return dict(sorted(counts.items()))


def _assembler_signature(
    diagnostics: list[JsonObject],
    *,
    assembler_stderr: str | None,
    assembler_stdout: str | None,
) -> str:
    for diagnostic in diagnostics:
        message = _str_or_none(diagnostic.get("message"))
        if message:
            return _signature(message)
    return _signature(assembler_stderr or assembler_stdout or "")


def _shape_signature(diagnostic: JsonObject) -> str:
    parts: list[str] = []
    for key in ("field", "section_index"):
        value = diagnostic.get(key)
        if value is not None:
            parts.append(f"{key}={value}")
    original = _dict(diagnostic.get("original"))
    rebuilt = _dict(diagnostic.get("rebuilt"))
    for side_name, side in (("original", original), ("rebuilt", rebuilt)):
        if side:
            record_id = side.get("record_id")
            target_section = side.get("target_section")
            count = side.get("count")
            parts.append(
                f"{side_name}=record:{record_id}:target:{target_section}:count:{count}"
            )
    if not parts:
        return _signature(json.dumps(diagnostic, sort_keys=True))
    return " ".join(parts)


def _layout_at_offset(file_layout: list[JsonObject], offset: int) -> JsonObject | None:
    for item in file_layout:
        start = _int_or_none(item.get("file_start"))
        end = _int_or_none(item.get("file_end"))
        if start is not None and end is not None and start <= offset < end:
            return item
    return None


def _signature(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized[:240]


def _percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _dict(value: object) -> JsonObject:
    return cast(JsonObject, value) if isinstance(value, dict) else {}


def _dict_or_none(value: object) -> JsonObject | None:
    return cast(JsonObject, value) if isinstance(value, dict) else None


def _dict_list(value: object) -> list[JsonObject]:
    if not isinstance(value, list):
        return []
    return [cast(JsonObject, item) for item in value if isinstance(item, dict)]


def _list_str(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _add_float_total(totals: dict[str, float], key: str, value: float) -> None:
    totals[key] = totals.get(key, 0.0) + value


def _rounded_float_totals(totals: dict[str, float]) -> dict[str, float]:
    return {
        key: round(value, 4)
        for key, value in sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    }


def _str(value: object, default: str) -> str:
    return value if isinstance(value, str) and value else default


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _int_value(value: object) -> int:
    return value if isinstance(value, int) else 0


def _list_length(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _bool_or_none(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _profile_flag(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        if value == 1:
            return True
        if value == 0:
            return False
    return None


def _float_value(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _float_or_none(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _now() -> float:
    return time.time()
