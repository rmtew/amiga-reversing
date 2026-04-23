from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from amiga_reversing.disasm.binary_source import resolve_target_binary_source
TARGETS_DIR = ROOT / "targets"
FACTS_V2_GATE_ENV = "AMIGA_REVERSING_PRECOMMIT_FACTS_V2_GATE"
FULL_REPRO_INTEGRATION_ENV = "AMIGA_REVERSING_FULL_REPRO_INTEGRATION"
FULL_REPRO_PROFILE_ENV = "AMIGA_REVERSING_FULL_REPRO_PROFILE"
FULL_REPRO_REPORT_ENV = "AMIGA_REVERSING_FULL_REPRO_REPORT"
FULL_REPRO_FACTS_V2_SOURCE_GATE_ENV = "AMIGA_REVERSING_FULL_REPRO_FACTS_V2_SOURCE_GATE"
FULL_REPRO_FACTS_V2_STRUCTURAL_GATE_ENV = "AMIGA_REVERSING_FULL_REPRO_FACTS_V2_STRUCTURAL_GATE"
FULL_REPRO_FACTS_V2_REPRODUCTION_GATE_ENV = "AMIGA_REVERSING_FULL_REPRO_FACTS_V2_REPRODUCTION_GATE"


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


def _run(command: list[str], *, env: dict[str, str] | None = None) -> int:
    print(f"\n==> {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False, env=env)
    return int(completed.returncode)


def _facts_v2_gate_enabled() -> bool:
    value = os.environ.get(FACTS_V2_GATE_ENV)
    return value is None or value.lower() not in {"0", "false", "no", "off"}


def _full_repro_gate_env(report_path: Path, *, source_gate: bool) -> dict[str, str]:
    env = os.environ.copy()
    env[FULL_REPRO_INTEGRATION_ENV] = "1"
    env[FULL_REPRO_PROFILE_ENV] = "1"
    env[FULL_REPRO_REPORT_ENV] = str(report_path)
    for key in (
        FULL_REPRO_FACTS_V2_SOURCE_GATE_ENV,
        FULL_REPRO_FACTS_V2_STRUCTURAL_GATE_ENV,
        FULL_REPRO_FACTS_V2_REPRODUCTION_GATE_ENV,
    ):
        env.pop(key, None)
    if source_gate:
        env[FULL_REPRO_FACTS_V2_SOURCE_GATE_ENV] = "1"
    return env


def _facts_v2_gate_steps() -> list[tuple[list[str], dict[str, str] | None]]:
    default_report = ROOT / "bin" / "rebuilt" / "precommit_full_reproduction_default_facts_v2.json"
    source_gate_report = ROOT / "bin" / "rebuilt" / "precommit_full_reproduction_facts_v2_source_gate.json"
    return [
        (
            [sys.executable, "-m", "pytest", "tests/test_full_reproduction_integration.py", "-q"],
            _full_repro_gate_env(default_report, source_gate=False),
        ),
        (
            [sys.executable, "-m", "pytest", "tests/test_full_reproduction_integration.py", "-q"],
            _full_repro_gate_env(source_gate_report, source_gate=True),
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv
    benchmark_targets = argv[1:] if len(argv) > 1 else _benchmark_targets()

    steps: list[tuple[list[str], dict[str, str] | None]] = [
        (["uv", "run", "ruff", "check"], None),
        (["uv", "run", "mypy"], None),
        (["uv", "run", "amiga-check-mojibake"], None),
    ]
    steps.append((["uv", "run", "pytest", "-q"], None))
    if benchmark_targets:
        steps.append(
            (
                [
                    "uv",
                    "run",
                    "amiga-benchmark-target",
                    *benchmark_targets,
                ],
                None,
            )
        )
    if _facts_v2_gate_enabled():
        steps.extend(_facts_v2_gate_steps())

    for command, env in steps:
        returncode = _run(command) if env is None else _run(command, env=env)
        if returncode != 0:
            return returncode

    print("\nprecommit: ok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
