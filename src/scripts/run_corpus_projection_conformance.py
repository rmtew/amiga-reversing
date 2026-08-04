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
    ("--unresolved-typed-field-report-output", "target_unresolved_typed_fields.jsonl"),
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
    """Build against shared data while binding ctypes to the selected DLL root."""
    build_arguments = ["build", "--workers", str(workers)]
    for option, relative_path in ARTIFACT_ARGUMENTS:
        build_arguments.extend((option, str(output_dir / relative_path)))
    child = (
        "import hashlib, os, sys; from pathlib import Path; "
        f"code_root = Path({str(code_root)!r}); data_root = Path({str(data_root)!r}); "
        "manifest_paths = ('corpus/platform_disk_manifest.jsonl', 'corpus/platform_file_manifest.jsonl'); "
        "assert all((code_root / path).is_file() and (data_root / path).is_file() and "
        "hashlib.sha256((code_root / path).read_bytes()).digest() == "
        "hashlib.sha256((data_root / path).read_bytes()).digest() for path in manifest_paths), "
        "'code and data roots do not share the declared corpus manifests'; "
        "sys.path.insert(0, str(code_root)); "
        "os.environ['AMIGA_C_BACKEND_DLL_ROOT'] = str(code_root); "
        "import src.scripts.platform_manifest_io as platform_manifest_io; "
        "platform_manifest_io.ROOT = data_root; "
        "import amiga_reversing.disasm.c_backend as c_backend; "
        "c_backend._load_dll = lambda project_root, name: ("
        "c_backend._dll_directory_handles.append(os.add_dll_directory(str(code_root / 'src' / 'build'))) "
        "if hasattr(os, 'add_dll_directory') else None, "
        "c_backend.CDLL(str(code_root / 'src' / 'build' / name)))[1]; "
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
