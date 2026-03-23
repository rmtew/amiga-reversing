#!/usr/bin/env py.exe
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS_DIR = ROOT / "targets"


def _benchmark_targets() -> list[str]:
    return sorted(
        target_dir.name
        for target_dir in TARGETS_DIR.iterdir()
        if target_dir.is_dir() and (target_dir / "binary_path.txt").exists()
    )


def _run(command: list[str]) -> int:
    print(f"\n==> {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    return int(completed.returncode)


def main(argv: list[str]) -> int:
    benchmark_targets = argv[1:] if len(argv) > 1 else _benchmark_targets()

    steps: list[list[str]] = [
        ["uv", "run", "ruff", "check"],
        ["uv", "run", "mypy"],
        ["uv", "run", "pytest", "-q"],
    ]
    if benchmark_targets:
        steps.append(["uv", "run", "scripts/benchmark_target.py", *benchmark_targets])

    for command in steps:
        returncode = _run(command)
        if returncode != 0:
            return returncode

    print("\nprecommit: ok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
