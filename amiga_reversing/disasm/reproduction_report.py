from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReportContext:
    target_name: str
    started_at: float
    input_stamp: dict[str, object]
    assembler: str
    backend: str
    source_path: Path
    rebuilt_path: Path


@dataclass(frozen=True)
class ReproductionOutcome:
    status: str
    exact: bool
    original_size: int
    rebuilt_size: int
    rebuilt_sha256: str
    canonical_rebuilt_size: int
    canonical_rebuilt_sha256: str
    canonical_rebuilt_path: Path
    first_diff: dict[str, object] | None
    diff_ranges: list[dict[str, object]]
    canonical_diff_ranges: list[dict[str, object]]
    file_layout: list[dict[str, object]]
    row_mappings: list[dict[str, object]]
    issues: list[dict[str, object]]
    assembler_diagnostics: list[dict[str, object]]
    assembler_stdout: str
    assembler_stderr: str
    file_shape_adjustments: list[dict[str, object]]
    file_shape_diagnostics: list[dict[str, object]]
    canonical_file_shape_diagnostics: list[dict[str, object]]
    comparison: dict[str, object]
    direct_source_report: dict[str, object] | None = None
    listing_profile: dict[str, object] | None = None
    profile: dict[str, object] | None = None


class RoundTripReportBuilder:
    def __init__(self, context: ReportContext) -> None:
        self.context = context

    def base(self) -> dict[str, object]:
        input_stamp = self.context.input_stamp
        return {
            "target": self.context.target_name,
            "status": "not_ready",
            "exact": False,
            "stale": False,
            "input_stamp": input_stamp,
            "started_at": self.context.started_at,
            "finished_at": None,
            "assembler": self.context.assembler,
            "assembler_cpu": input_stamp.get("assembler_cpu"),
            "backend": self.context.backend,
            "analysis_backend": input_stamp.get("analysis_backend"),
            "source_path": str(self.context.source_path),
            "rebuilt_path": str(self.context.rebuilt_path),
            "original_size": input_stamp.get("original_size"),
            "rebuilt_size": None,
            "original_sha256": input_stamp.get("original_sha256"),
            "rebuilt_sha256": None,
            "direct_source_exact": None,
            "direct_source_assembler": None,
            "direct_source_diff_range_count": None,
            "direct_source_first_diff": None,
            "first_diff": None,
            "diff_ranges": [],
            "row_mappings": [],
            "issues": [],
            "assembler_diagnostics": [],
            "assembler_stdout": "",
            "assembler_stderr": "",
            "file_shape_adjustments": [],
            "tool_error": None,
        }

    def error(
        self,
        *,
        status: str,
        issues: list[dict[str, object]],
        tool_error: str | None = None,
        assembler_diagnostics: list[dict[str, object]] | None = None,
        assembler_stdout: str = "",
        assembler_stderr: str = "",
        listing_profile: dict[str, object] | None = None,
        direct_rebuild_profile: dict[str, object] | None = None,
        profile: dict[str, object] | None = None,
        extra: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        report = {
            **self.base(),
            "status": status,
            "finished_at": time.time(),
            "issues": issues,
        }
        if tool_error is not None:
            report["tool_error"] = tool_error
        if assembler_diagnostics is not None:
            report["assembler_diagnostics"] = assembler_diagnostics
            report["assembler_stdout"] = assembler_stdout
            report["assembler_stderr"] = assembler_stderr
        if listing_profile is not None:
            report["listing_profile"] = listing_profile
        if direct_rebuild_profile is not None:
            report["direct_rebuild_profile"] = direct_rebuild_profile
        if profile is not None:
            report["profile"] = profile
        if extra is not None:
            report.update(extra)
        return report

    def completed(self, outcome: ReproductionOutcome) -> dict[str, object]:
        report = {
            **self.base(),
            "status": outcome.status,
            "exact": outcome.exact,
            "finished_at": time.time(),
            "original_size": outcome.original_size,
            "rebuilt_size": outcome.rebuilt_size,
            "rebuilt_sha256": outcome.rebuilt_sha256,
            "canonical_rebuilt_size": outcome.canonical_rebuilt_size,
            "canonical_rebuilt_sha256": outcome.canonical_rebuilt_sha256,
            "canonical_rebuilt_path": str(outcome.canonical_rebuilt_path),
            "first_diff": outcome.first_diff,
            "diff_ranges": outcome.diff_ranges,
            "canonical_diff_ranges": outcome.canonical_diff_ranges,
            "file_layout": outcome.file_layout,
            "row_mappings": outcome.row_mappings,
            "issues": outcome.issues,
            "assembler_diagnostics": outcome.assembler_diagnostics,
            "assembler_stdout": outcome.assembler_stdout,
            "assembler_stderr": outcome.assembler_stderr,
            "file_shape_adjustments": outcome.file_shape_adjustments,
            "file_shape_diagnostics": outcome.file_shape_diagnostics,
            "canonical_file_shape_diagnostics": outcome.canonical_file_shape_diagnostics,
            "comparison": outcome.comparison,
        }
        if outcome.direct_source_report is not None:
            report.update(outcome.direct_source_report)
        if outcome.listing_profile is not None:
            report["listing_profile"] = outcome.listing_profile
        if outcome.profile is not None:
            report["profile"] = outcome.profile
        return report


def profile_payload(timings: dict[str, object], started_at: float) -> dict[str, object]:
    payload: dict[str, object] = dict(timings)
    payload["total_seconds"] = round(time.perf_counter() - started_at, 4)
    return payload


def write_report(report_path: Path, report: dict[str, object]) -> dict[str, object]:
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def issue(
    kind: str,
    message: str,
    row_ref: tuple[int, Mapping[str, object]] | None,
    *,
    diff_range: dict[str, object] | None = None,
    layout_range: dict[str, object] | None = None,
    section_index: int | None = None,
    section_offset: int | None = None,
    hunk: int | None = None,
) -> dict[str, object]:
    row_index: int | None = None
    row: Mapping[str, object] | None = None
    if row_ref is not None:
        row_index, row = row_ref
    if row is not None and section_index is None:
        section_index = row_int(row, "section_index")
    if hunk is None:
        hunk = section_index
    payload: dict[str, object] = {
        "kind": kind,
        "message": message,
        "summary": message,
        "row_index": row_index,
        "addr": row_int(row, "addr") if row is not None else None,
        "section_index": section_index,
        "section_offset": section_offset,
        "hunk": hunk,
        "stable_key": row_str(row, "stable_key") if row is not None else None,
        "match_text": row_match_text(row) if row is not None else None,
    }
    if diff_range is not None:
        payload["diff_range"] = diff_range
    if layout_range is not None:
        payload["layout_range"] = layout_range
        payload["layout_kind"] = layout_range.get("kind")
    return payload


def row_match_text(row: Mapping[str, object]) -> str:
    label = row_str(row, "label")
    if label:
        return label
    opcode = row_str(row, "opcode_or_directive")
    if opcode:
        operand_text = row_str(row, "operand_text") or ""
        return " ".join(part for part in (opcode, operand_text) if part).strip()
    return str(row.get("text") or "").strip()


def row_int(row: Mapping[str, object], key: str) -> int | None:
    value = row.get(key)
    return value if isinstance(value, int) else None


def row_str(row: Mapping[str, object], key: str) -> str | None:
    value = row.get(key)
    return value if isinstance(value, str) else None


def direct_source_report_fields(original: bytes, source_bytes: bytes, *, assembler: str) -> dict[str, object]:
    diff_ranges = _direct_source_diff_ranges(original, source_bytes)
    return direct_source_report_fields_from_ranges(
        original,
        source_bytes,
        assembler=assembler,
        diff_ranges=diff_ranges,
    )


def direct_source_report_fields_from_ranges(
    original: bytes,
    source_bytes: bytes,
    *,
    assembler: str,
    diff_ranges: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "direct_source_exact": not diff_ranges,
        "direct_source_assembler": assembler,
        "direct_source_diff_range_count": len(diff_ranges),
        "direct_source_first_diff": _first_diff_from_ranges(original, source_bytes, diff_ranges),
    }


def _direct_source_diff_ranges(original: bytes, source_bytes: bytes) -> list[dict[str, object]]:
    end = max(len(original), len(source_bytes))
    ranges: list[dict[str, object]] = []
    start: int | None = None
    for offset in range(end):
        original_byte = original[offset] if offset < len(original) else None
        source_byte = source_bytes[offset] if offset < len(source_bytes) else None
        if original_byte == source_byte:
            if start is not None:
                ranges.append(_direct_source_diff_range(start, offset, original, source_bytes))
                start = None
            continue
        if start is None:
            start = offset
    if start is not None:
        ranges.append(_direct_source_diff_range(start, end, original, source_bytes))
    return ranges


def _direct_source_diff_range(start: int, end: int, original: bytes, source_bytes: bytes) -> dict[str, object]:
    return {
        "start": start,
        "end": end,
        "length": end - start,
        "original_hex": original[start:min(end, len(original))].hex(),
        "source_hex": source_bytes[start:min(end, len(source_bytes))].hex(),
    }


def _first_diff_from_ranges(
    original: bytes,
    rebuilt: bytes,
    diff_ranges: list[dict[str, object]],
) -> dict[str, object] | None:
    if not diff_ranges:
        return None
    offset_value = diff_ranges[0].get("start")
    if not isinstance(offset_value, int):
        return None
    return {
        "offset": offset_value,
        "original": original[offset_value] if offset_value < len(original) else None,
        "rebuilt": rebuilt[offset_value] if offset_value < len(rebuilt) else None,
    }
