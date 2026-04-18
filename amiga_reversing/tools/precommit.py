from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from amiga_reversing.disasm.binary_source import resolve_target_binary_source

TARGETS_DIR = ROOT / "targets"


def _benchmark_targets() -> list[str]:
    targets: list[str] = []
    for target_dir in TARGETS_DIR.iterdir():
        if not target_dir.is_dir() or target_dir.name.startswith("."):
            continue
        if (target_dir / "manifest.json").exists():
            targets.append(target_dir.name)
            continue
        binary_source = resolve_target_binary_source(target_dir, project_root=ROOT)
        if binary_source is None or binary_source.parent_disk_id is not None:
            continue
        targets.append(target_dir.name)
    return sorted(targets)


def _run(command: list[str]) -> int:
    print(f"\n==> {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    return int(completed.returncode)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv
    benchmark_targets = argv[1:] if len(argv) > 1 else _benchmark_targets()

    steps: list[list[str]] = [
        ["uv", "run", "ruff", "check"],
        ["uv", "run", "mypy"],
        ["uv", "run", "amiga-check-mojibake"],
    ]
    steps.append(["uv", "run", "pytest", "-q"])
    if benchmark_targets:
        steps.append(["uv", "run", "amiga-benchmark-target", *benchmark_targets])

    for command in steps:
        returncode = _run(command)
        if returncode != 0:
            return returncode

    print("\nprecommit: ok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
