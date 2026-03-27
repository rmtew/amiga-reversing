#!/usr/bin/env py.exe
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from disasm.binary_source import resolve_target_binary_source

TARGETS_DIR = ROOT / "targets"
_RUNTIME_COVERAGE_PATH_PREFIXES = ("kb/", "m68k_kb/")
_RUNTIME_COVERAGE_PATHS = {
    "m68k/m68k_asm.py",
    "m68k/assembler_coverage_audit.py",
}


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


def _changed_files() -> set[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return set()
    changed: set[str] = set()
    for line in completed.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed.add(path.replace("\\", "/"))
    return changed


def _needs_runtime_coverage(changed_files: set[str]) -> bool:
    for path in changed_files:
        if path in _RUNTIME_COVERAGE_PATHS:
            return True
        if path.startswith(_RUNTIME_COVERAGE_PATH_PREFIXES):
            return True
    return False


def main(argv: list[str]) -> int:
    benchmark_targets = argv[1:] if len(argv) > 1 else _benchmark_targets()
    changed_files = _changed_files()

    steps: list[list[str]] = [
        ["uv", "run", "ruff", "check"],
        ["uv", "run", "mypy"],
        ["uv", "run", "python", "scripts/check_mojibake.py"],
    ]
    if _needs_runtime_coverage(changed_files):
        steps.append(["uv", "run", "pytest", "-q", "-m", "runtime_coverage"])
    steps.append(["uv", "run", "pytest", "-q"])
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
