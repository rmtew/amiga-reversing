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
