"""Run an isolated candidate/oracle corpus build pair and compare normal artifacts.

The candidate and oracle may use different code roots, but always read the
same repository data root.  This is the migration gate runner for Proposal
041: it never deletes or reuses an output directory, and it compares only the
published semantic artifacts after both builds succeed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from src.scripts.compare_corpus_artifacts import compare_normal_artifacts


ARTIFACT_ARGUMENTS = (
    ("--output", "target_usage_manifest.jsonl"),
    ("--xrefs-output", "target_usage_xrefs.jsonl"),
    ("--snippet-rows-output", "target_usage_snippet_rows"),
    ("--variants-output", "target_variant_index.jsonl"),
    ("--type-flow-report-output", "target_type_flow_report.jsonl"),
    ("--unresolved-typed-fields-output", "target_unresolved_typed_fields.jsonl"),
    ("--coverage-report-output", "target_usage_coverage.json"),
    ("--profile-output", "target_usage_build_profile.json"),
    ("--progress-output", "progress"),
)


def _require_fresh_directory(path: Path) -> None:
    """Create a gate output directory only if it has never been used."""
    if path.exists():
        raise ValueError(f"refusing to reuse or delete existing output directory: {path}")
    path.mkdir(parents=True)


def _build_command(
    *,
    python_executable: str,
    code_root: Path,
    data_root: Path,
    output_dir: Path,
    workers: int,
) -> list[str]:
    """Build an explicit child command without letting its cwd choose code."""
    build_arguments = ["build", "--workers", str(workers)]
    for option, relative_path in ARTIFACT_ARGUMENTS:
        build_arguments.extend((option, str(output_dir / relative_path)))
    child = (
        "import os, sys; from pathlib import Path; "
        f"code_root = Path({str(code_root)!r}); data_root = Path({str(data_root)!r}); "
        "sys.path.insert(0, str(code_root)); "
        "import src.scripts.platform_manifest_io as platform_manifest_io; "
        "platform_manifest_io.ROOT = data_root; "
        "import src.scripts.target_usage_manifest as target_usage_manifest; "
        "os.chdir(data_root); "
        f"raise SystemExit(target_usage_manifest.main({build_arguments!r}))"
    )
    return [python_executable, "-c", child]


def run_build(
    *,
    label: str,
    python_executable: str,
    code_root: Path,
    data_root: Path,
    output_dir: Path,
    workers: int,
) -> None:
    _require_fresh_directory(output_dir)
    command = _build_command(
        python_executable=python_executable,
        code_root=code_root,
        data_root=data_root,
        output_dir=output_dir,
        workers=workers,
    )
    print(f"Running {label} build: {code_root}")
    subprocess.run(command, cwd=data_root, check=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-code-root", type=Path, required=True)
    parser.add_argument("--candidate-code-root", type=Path, default=Path.cwd())
    parser.add_argument("--data-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-parent", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=(1, 8), required=True)
    parser.add_argument("--python-executable", default=sys.executable)
    args = parser.parse_args(argv)
    if args.workers < 1:
        raise ValueError("workers must be positive")
    for name, path in (("oracle code root", args.oracle_code_root), ("candidate code root", args.candidate_code_root),
                       ("data root", args.data_root)):
        if not path.is_dir():
            raise ValueError(f"{name} is not a directory: {path}")
    _require_fresh_directory(args.output_parent)
    oracle_output = args.output_parent / "oracle"
    candidate_output = args.output_parent / "candidate"
    run_build(label="oracle", python_executable=args.python_executable, code_root=args.oracle_code_root,
              data_root=args.data_root, output_dir=oracle_output, workers=args.workers)
    run_build(label="candidate", python_executable=args.python_executable, code_root=args.candidate_code_root,
              data_root=args.data_root, output_dir=candidate_output, workers=args.workers)
    comparisons = compare_normal_artifacts(oracle_output, candidate_output)
    for comparison in comparisons:
        print(f"{comparison.name}: {comparison.status}")
    return 0 if all(item.status == "identical" for item in comparisons) else 1


if __name__ == "__main__":
    raise SystemExit(main())
