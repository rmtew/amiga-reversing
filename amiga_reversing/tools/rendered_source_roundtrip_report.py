from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.c_backend import (
    analyze_project_source_with_render_evidence_from_c_backend,
    source_quality_explain_project_source_with_c_backend,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from amiga_reversing.disasm.reproduction import run_reproduction
from amiga_reversing.disasm.source_rendering import (
    render_source_from_binary_source_or_raise,
)

DEFAULT_REPORT_PATH = PROJECT_ROOT / "docs" / "validation" / "rendered-source-roundtrip-report.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run rendered-source round-trip verification for imported targets with asm.s files."
    )
    parser.add_argument(
        "--targets-root",
        type=Path,
        default=PROJECT_ROOT / "targets",
        help="Targets root to scan. Defaults to repository targets/.",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Target id to verify. May be supplied more than once. Defaults to all rendered sources.",
    )
    parser.add_argument(
        "--update-rendered-source",
        action="store_true",
        help="Rewrite each supported target .s from the current renderer before round-trip verification.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help=f"Deterministic JSON report path. Defaults to {DEFAULT_REPORT_PATH.relative_to(PROJECT_ROOT)}.",
    )
    parser.add_argument(
        "--no-write-report",
        action="store_true",
        help="Do not write the deterministic JSON report.",
    )
    parser.add_argument(
        "--analysis-export-dir",
        type=Path,
        default=None,
        help="Optional directory for per-target analysis JSON exports.",
    )
    parser.add_argument(
        "--analysis-export-scope",
        choices=("failures", "all"),
        default="failures",
        help="When --analysis-export-dir is set, export only failing rows or all rows.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    args = parser.parse_args(argv)

    targets = _filter_targets(_rendered_source_targets(cast(Path, args.targets_root)), cast(list[str], args.target))
    rows = [
        _run_target(
            target,
            source_path,
            update_rendered_source=bool(args.update_rendered_source),
            analysis_export_dir=cast(Path | None, args.analysis_export_dir),
            analysis_export_scope=str(args.analysis_export_scope),
        )
        for target, source_path in targets
    ]
    summary = _summary(rows)
    payload = _report_payload(summary, rows)
    report_path = cast(Path, args.report_path)
    report_drift = False
    if not bool(args.no_write_report):
        if not bool(args.update_rendered_source):
            report_drift = _report_has_drift(report_path, payload)
        _write_report(report_path, payload)
    if bool(args.json):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text_report(summary, rows)
        if report_drift:
            print(f"report-drift       {_display_path(report_path)}")
    return 0 if summary["failures"] == 0 and not report_drift else 1


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _report_has_drift(path: Path, payload: dict[str, Any]) -> bool:
    expected = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if not path.exists():
        return True
    return path.read_text(encoding="utf-8") != expected


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _report_payload(summary: dict[str, int], rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "summary": summary,
        "targets": [_report_row(row) for row in rows],
    }


def _report_row(row: dict[str, Any]) -> dict[str, Any]:
    report_row = {
        "target": row["target"],
        "status": row.get("status"),
        "rendered_source_full_file_exact": row["rendered_source_full_file_exact"],
        "rendered_source_content_exact": row["rendered_source_content_exact"],
        "failure_kinds": sorted(str(kind) for kind in row.get("failure_kinds") or []),
        "diff_range_count": row.get("diff_range_count"),
        "tool_error": row.get("tool_error"),
        "message": row.get("message"),
    }
    if row.get("analysis_export_path") is not None:
        report_row["analysis_export_path"] = row["analysis_export_path"]
    if row.get("analysis_export_error") is not None:
        report_row["analysis_export_error"] = row["analysis_export_error"]
    return report_row


def _rendered_source_targets(targets_root: Path) -> list[tuple[str, Path]]:
    targets: dict[str, Path] = {}
    for path in targets_root.rglob("*.s"):
        targets[_project_id_for_source(path, targets_root)] = path
    return sorted(targets.items())


def _filter_targets(targets: list[tuple[str, Path]], requested: list[str]) -> list[tuple[str, Path]]:
    if not requested:
        return targets
    target_by_id = dict(targets)
    missing = sorted(set(requested) - set(target_by_id))
    if missing:
        raise SystemExit(f"unknown rendered-source target(s): {', '.join(missing)}")
    requested_set = set(requested)
    return [(target, path) for target, path in targets if target in requested_set]


def _project_id_for_source(path: Path, targets_root: Path) -> str:
    rel = path.parent.relative_to(targets_root)
    parts = rel.parts
    if len(parts) >= 3 and parts[-2] == "targets":
        return f"{parts[0]}__{parts[-1]}"
    return parts[-1]


def _run_target(
    target: str,
    source_path: Path,
    *,
    update_rendered_source: bool = False,
    analysis_export_dir: Path | None = None,
    analysis_export_scope: str = "failures",
) -> dict[str, Any]:
    if _target_is_macos(target, source_path):
        row = {
            "target": target,
            "status": "unsupported",
            "rendered_source_full_file_exact": False,
            "rendered_source_content_exact": False,
            "failure_kinds": ["unsupported_platform_source_assembly"],
            "tool_error": None,
            "message": "Mac OS rendered-source assembly is not currently supported.",
            "source_updated": False,
        }
        _maybe_export_analysis(row, source_path, analysis_export_dir, analysis_export_scope)
        return row
    rendered_source_text: str | None = None
    rendered_source_profile: dict[str, object] | None = None
    try:
        if update_rendered_source:
            rendered_source_text, rendered_source_profile = _update_rendered_source(target, source_path)
        else:
            rendered_source_text = source_path.read_text(encoding="utf-8")
        if rendered_source_profile is None:
            result = run_reproduction(
                target,
                assembler="our",
                profile=True,
                persist_report=False,
                pre_rendered_source_text=rendered_source_text,
            )
        else:
            result = run_reproduction(
                target,
                assembler="our",
                profile=True,
                persist_report=False,
                pre_rendered_source_text=rendered_source_text,
                pre_rendered_source_profile=rendered_source_profile,
            )
    except Exception as exc:
        row = {
            "target": target,
            "status": "exception",
            "rendered_source_full_file_exact": False,
            "rendered_source_content_exact": False,
            "failure_kinds": [],
            "tool_error": f"{type(exc).__name__}: {exc}",
            "source_updated": False,
        }
        _maybe_export_analysis(row, source_path, analysis_export_dir, analysis_export_scope)
        return row
    comparison = cast(dict[str, Any], result.get("comparison") or {})
    full_file_exact = comparison.get("full_file_exact") is True
    content_exact = comparison.get("content_exact") is True or comparison.get("semantic_exact") is True
    row = {
        "target": target,
        "status": result.get("status"),
        "rendered_source_full_file_exact": full_file_exact,
        "rendered_source_content_exact": content_exact or full_file_exact,
        "failure_kinds": comparison.get("failure_kinds") or [],
        "diff_range_count": comparison.get("diff_range_count"),
        "tool_error": result.get("tool_error"),
        "message": result.get("message"),
        "source_updated": update_rendered_source,
    }
    _maybe_export_analysis(row, source_path, analysis_export_dir, analysis_export_scope)
    return row


def _maybe_export_analysis(
    row: dict[str, Any],
    source_path: Path,
    analysis_export_dir: Path | None,
    analysis_export_scope: str,
) -> None:
    if analysis_export_dir is None:
        return
    if analysis_export_scope != "all" and _row_is_success(row):
        return
    try:
        export_path = _export_target_analysis(row, source_path, analysis_export_dir)
    except Exception as exc:
        row["analysis_export_error"] = f"{type(exc).__name__}: {exc}"
    else:
        row["analysis_export_path"] = _display_path(export_path)


def _row_is_success(row: dict[str, Any]) -> bool:
    return (
        row.get("rendered_source_full_file_exact") is True
        or row.get("rendered_source_content_exact") is True
        or row.get("status") == "unsupported"
    )


def _export_target_analysis(row: dict[str, Any], source_path: Path, analysis_export_dir: Path) -> Path:
    target = str(row["target"])
    paths = resolve_project_paths(target, project_root=PROJECT_ROOT)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "target": target,
        "source_path": _display_path(source_path),
        "roundtrip_row": _report_row(row),
    }
    with effective_metadata_file(paths.target_dir) as metadata_path:
        payload["analysis"] = analyze_project_source_with_render_evidence_from_c_backend(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
        payload["source_quality_explanation"] = source_quality_explain_project_source_with_c_backend(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
    analysis_export_dir.mkdir(parents=True, exist_ok=True)
    export_path = analysis_export_dir / f"{_safe_filename(target)}.analysis.json"
    export_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return export_path


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)


def _update_rendered_source(target: str, source_path: Path) -> tuple[str, dict[str, object]]:
    paths = resolve_project_paths(target, project_root=PROJECT_ROOT)
    with effective_metadata_file(paths.target_dir) as metadata_path:
        rendering = render_source_from_binary_source_or_raise(
            target_id=target,
            binary_source=paths.binary_source,
            target_dir=paths.target_dir,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
            workflow_id="rendered_source_roundtrip_update",
        )
    newline = "\n" if load_assembler_profile("vasm").render.line_ending == "lf" else "\r\n"
    source_path.write_text(rendering.source_text, encoding="utf-8", newline=newline)
    return rendering.source_text, rendering.listing_profile


def _target_is_macos(target: str, source_path: Path) -> bool:
    return target.startswith("macos_") or any(part.startswith("macos_") for part in source_path.parts)


def _summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    full_file_exact = sum(1 for row in rows if row["rendered_source_full_file_exact"] is True)
    content_only = sum(
        1
        for row in rows
        if row["rendered_source_content_exact"] is True and row["rendered_source_full_file_exact"] is not True
    )
    unsupported = sum(1 for row in rows if row.get("status") == "unsupported")
    failures = len(rows) - full_file_exact - content_only - unsupported
    return {
        "targets": len(rows),
        "rendered_source_full_file_exact": full_file_exact,
        "rendered_source_content_exact_only": content_only,
        "unsupported": unsupported,
        "failures": failures,
    }


def _print_text_report(summary: dict[str, int], rows: list[dict[str, Any]]) -> None:
    print(
        "Rendered source round-trip: "
        f"{summary['rendered_source_full_file_exact']}/{summary['targets']} full-file exact, "
        f"{summary['rendered_source_content_exact_only']} content-exact only, "
        f"{summary['unsupported']} unsupported, "
        f"{summary['failures']} failures"
    )
    for row in rows:
        if row["rendered_source_full_file_exact"] is True:
            verdict = "full-file-exact"
        elif row["rendered_source_content_exact"] is True:
            verdict = "content-exact-only"
        elif row.get("status") == "unsupported":
            verdict = "unsupported"
        else:
            verdict = "failure"
        detail = ", ".join(str(kind) for kind in row.get("failure_kinds") or [])
        if row.get("tool_error"):
            detail = str(row["tool_error"])
        suffix = f" ({detail})" if detail else ""
        print(f"{verdict:18} {row['target']}{suffix}")


if __name__ == "__main__":
    raise SystemExit(main())
