from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from amiga_reversing.disasm.facts_v2_source_gate import facts_v2_source_gate_report_for_targets
from amiga_reversing.disasm.profile_set_targets import ensure_profile_set_project, select_profile_targets

SOURCE_GATE_PROFILE_TARGET_CATEGORIES = (
    ("genam", ("genam",)),
    ("bloodwych", ("bloodwych",)),
    ("icon.library", ("icon.library",)),
    ("fastfilesystem", ("fastfilesystem",)),
    ("3dedit", ("3dedit",)),
    ("atari_3d", ("resource-atari", "3d-construction-kit")),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gate facts_v2 assembler source readiness.",
    )
    parser.add_argument("targets", nargs="*", help="Target names. Defaults to the profile set with --profile-set.")
    parser.add_argument(
        "--profile-set",
        action="store_true",
        help="Build/use the representative imported profile-set project and gate its selected targets.",
    )
    parser.add_argument(
        "--profile-project-root",
        type=Path,
        default=ROOT / "bin" / "rebuilt" / "facts_v2_source_gate_profile_project" / "project",
        help="Generated profile-set project root used with --profile-set.",
    )
    parser.add_argument(
        "--refresh-profile-project",
        action="store_true",
        help="Rebuild the generated profile-set project before gating.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "bin" / "rebuilt" / "facts_v2_source_gate_report.json",
        help="JSON report path.",
    )
    parser.add_argument("--fail-on-gate", action="store_true", help="Return non-zero if any gate blocker exists.")
    args = parser.parse_args(argv)

    project_root = ROOT
    profile_project = None
    if args.profile_set:
        profile_project_root = args.profile_project_root
        if not profile_project_root.is_absolute():
            profile_project_root = ROOT / profile_project_root
        profile_project = ensure_profile_set_project(
            profile_project_root,
            extraction_root=profile_project_root.parent,
            refresh=args.refresh_profile_project,
            repo_root=ROOT,
        )
        project_root = profile_project.project_root
        profile_targets = select_profile_targets(
            profile_project.target_names,
            categories=SOURCE_GATE_PROFILE_TARGET_CATEGORIES,
        )
        if not profile_targets:
            profile_targets = profile_project.selected_targets
        targets = tuple(args.targets) if args.targets else tuple(profile_targets)
    else:
        targets = tuple(args.targets)
    if not targets:
        parser.error("targets are required unless --profile-set selects targets")

    report = facts_v2_source_gate_report_for_targets(targets, project_root=project_root)
    if profile_project is not None:
        report["profile_set_project"] = profile_project.to_dict()

    output = args.output
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")

    summary = report.get("summary") if isinstance(report, dict) else None
    if not isinstance(summary, dict):
        raise RuntimeError("facts_v2 source gate report returned malformed summary")
    print(
        f"targets={_summary_int(summary, 'target_count')} "
        f"passed={_summary_int(summary, 'passed_count')} "
        f"failed={_summary_int(summary, 'failed_count')} "
        f"gate_failed={_summary_int(summary, 'gate_failed_count')} "
        f"symbolic={_summary_int(summary, 'asm_source_symbolic_instructions')}"
    )
    if profile_project is not None:
        print(
            f"profile_project={profile_project.project_root} "
            f"selected={len(targets)} "
            f"imports_failed={len(profile_project.import_failures)}"
        )
    print(f"wrote {output}")

    if args.profile_set and profile_project is not None and profile_project.import_failures and args.fail_on_gate:
        return 1
    if args.fail_on_gate and _summary_int(summary, "gate_failed_count") > 0:
        return 1
    return 0


def _summary_int(summary: dict[object, object], key: str) -> int:
    value = summary.get(key)
    if isinstance(value, bool):
        return 0
    return value if isinstance(value, int) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
