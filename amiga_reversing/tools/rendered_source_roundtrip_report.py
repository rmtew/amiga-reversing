from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.reproduction import run_reproduction


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
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    args = parser.parse_args(argv)

    targets = _rendered_source_targets(cast(Path, args.targets_root))
    rows = [_run_target(target, source_path) for target, source_path in targets]
    summary = _summary(rows)
    payload = {"summary": summary, "targets": rows}
    if bool(args.json):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text_report(summary, rows)
    return 0 if summary["failures"] == 0 else 1


def _rendered_source_targets(targets_root: Path) -> list[tuple[str, Path]]:
    targets: dict[str, Path] = {}
    for path in targets_root.rglob("*.s"):
        targets[_project_id_for_source(path, targets_root)] = path
    return sorted(targets.items())


def _project_id_for_source(path: Path, targets_root: Path) -> str:
    rel = path.parent.relative_to(targets_root)
    parts = rel.parts
    if len(parts) >= 3 and parts[-2] == "targets":
        return f"{parts[0]}__{parts[-1]}"
    return parts[-1]


def _run_target(target: str, source_path: Path) -> dict[str, Any]:
    if _target_is_macos(target, source_path):
        return {
            "target": target,
            "status": "unsupported",
            "rendered_source_full_file_exact": False,
            "rendered_source_content_exact": False,
            "failure_kinds": ["unsupported_platform_source_assembly"],
            "tool_error": None,
            "message": "Mac OS rendered-source assembly is not currently supported.",
        }
    try:
        result = run_reproduction(target, assembler="our", profile=True, persist_report=False)
    except Exception as exc:
        return {
            "target": target,
            "status": "exception",
            "rendered_source_full_file_exact": False,
            "rendered_source_content_exact": False,
            "failure_kinds": [],
            "tool_error": f"{type(exc).__name__}: {exc}",
        }
    comparison = cast(dict[str, Any], result.get("comparison") or {})
    full_file_exact = comparison.get("full_file_exact") is True
    content_exact = comparison.get("content_exact") is True or comparison.get("semantic_exact") is True
    return {
        "target": target,
        "status": result.get("status"),
        "rendered_source_full_file_exact": full_file_exact,
        "rendered_source_content_exact": content_exact or full_file_exact,
        "failure_kinds": comparison.get("failure_kinds") or [],
        "diff_range_count": comparison.get("diff_range_count"),
        "tool_error": result.get("tool_error"),
        "message": result.get("message"),
    }


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
