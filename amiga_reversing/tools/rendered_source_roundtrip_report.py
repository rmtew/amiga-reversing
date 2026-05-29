from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from amiga_reversing.disasm.reproduction import run_reproduction
from amiga_reversing.disasm.source_rendering import (
    render_source_from_binary_source_or_raise,
)


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
        "--update-rendered-source",
        action="store_true",
        help="Rewrite each supported target .s from the current renderer before round-trip verification.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    args = parser.parse_args(argv)

    targets = _rendered_source_targets(cast(Path, args.targets_root))
    rows = [
        _run_target(target, source_path, update_rendered_source=bool(args.update_rendered_source))
        for target, source_path in targets
    ]
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


def _run_target(target: str, source_path: Path, *, update_rendered_source: bool = False) -> dict[str, Any]:
    if _target_is_macos(target, source_path):
        return {
            "target": target,
            "status": "unsupported",
            "rendered_source_full_file_exact": False,
            "rendered_source_content_exact": False,
            "failure_kinds": ["unsupported_platform_source_assembly"],
            "tool_error": None,
            "message": "Mac OS rendered-source assembly is not currently supported.",
            "source_updated": False,
        }
    rendered_source_text: str | None = None
    rendered_source_profile: dict[str, object] | None = None
    try:
        if update_rendered_source:
            rendered_source_text, rendered_source_profile = _update_rendered_source(target, source_path)
        else:
            rendered_source_text = source_path.read_text(encoding="utf-8")
        kwargs: dict[str, object] = {"assembler": "our", "profile": True, "persist_report": False}
        if rendered_source_text is not None:
            kwargs["pre_rendered_source_text"] = rendered_source_text
            if rendered_source_profile is not None:
                kwargs["pre_rendered_source_profile"] = rendered_source_profile
        result = run_reproduction(target, **kwargs)
    except Exception as exc:
        return {
            "target": target,
            "status": "exception",
            "rendered_source_full_file_exact": False,
            "rendered_source_content_exact": False,
            "failure_kinds": [],
            "tool_error": f"{type(exc).__name__}: {exc}",
            "source_updated": False,
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
        "source_updated": update_rendered_source,
    }


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
