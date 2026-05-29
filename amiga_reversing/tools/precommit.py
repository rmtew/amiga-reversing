from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = ROOT

from amiga_reversing.amiga_disk.models import DiskManifest
from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.project_ids import target_output_stem

TARGETS_DIR = ROOT / "targets"
FACTS_V2_GATE_ENV = "AMIGA_REVERSING_PRECOMMIT_FACTS_V2_GATE"
FULL_REPRO_INTEGRATION_ENV = "AMIGA_REVERSING_FULL_REPRO_INTEGRATION"
FULL_REPRO_PROFILE_ENV = "AMIGA_REVERSING_FULL_REPRO_PROFILE"
FULL_REPRO_REPORT_ENV = "AMIGA_REVERSING_FULL_REPRO_REPORT"
FULL_REPRO_FACTS_V2_SOURCE_GATE_ENV = "AMIGA_REVERSING_FULL_REPRO_FACTS_V2_SOURCE_GATE"
FULL_REPRO_FACTS_V2_STRUCTURAL_GATE_ENV = "AMIGA_REVERSING_FULL_REPRO_FACTS_V2_STRUCTURAL_GATE"
FULL_REPRO_FACTS_V2_REPRODUCTION_GATE_ENV = "AMIGA_REVERSING_FULL_REPRO_FACTS_V2_REPRODUCTION_GATE"
REQUIRED_SUBTARGET_STATES = {"added"}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _benchmark_targets() -> list[str]:
    targets: list[str] = []
    for target_dir in TARGETS_DIR.iterdir():
        if not target_dir.is_dir() or target_dir.name.startswith("."):
            continue
        if (target_dir / "manifest.json").exists():
            targets.append(target_dir.name)
            continue
        binary_source = resolve_target_binary_source(target_dir, project_root=ROOT)
        if binary_source is None or getattr(binary_source, "parent_disk_id", None) is not None:
            continue
        targets.append(target_dir.name)
    return sorted(targets)


def _expected_s_path(target_dir: Path) -> Path:
    return target_dir / f"{target_output_stem(target_dir.name)}.s"


def _child_target_state_paths(
    disk_target: Path,
) -> tuple[list[tuple[Path, list[str]]], list[str]]:
    manifest_path = disk_target / "manifest.json"
    state_path = disk_target / "target_state.json"
    try:
        manifest = DiskManifest.load(manifest_path)
    except Exception:
        return [], []
    state = _read_json(state_path)
    entries = state.get("subtargets")
    target_paths: list[tuple[Path, list[str]]] = []
    missing: list[str] = []
    if isinstance(entries, list) and entries:
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("state") not in REQUIRED_SUBTARGET_STATES:
                continue
            target_id = entry.get("id")
            if not isinstance(target_id, str) or not target_id:
                continue
            path_value = entry.get("path")
            target_dir: Path | None = None
            if isinstance(path_value, str) and path_value.strip():
                path_obj = Path(path_value)
                if not path_obj.is_absolute():
                    target_dir = PROJECT_ROOT / path_obj
            if target_dir is None:
                target_dir = disk_target / "targets" / target_id
            target_paths.append((target_dir, [target_id]))
    else:
        for imported in manifest.imported_targets:
            target_paths.append((PROJECT_ROOT / imported.target_path, [imported.target_name]))
    observed: list[tuple[Path, list[str]]] = []
    for path, target_ids in target_paths:
        if not path.exists():
            missing.append(", ".join(sorted(target_ids)))
            continue
        observed.append((path, target_ids))
    return observed, missing


def _collect_required_artifact_targets(scope_targets: list[str]) -> tuple[set[Path], list[str]]:
    required: set[Path] = set()
    missing: list[str] = []
    for target in scope_targets:
        target_dir = TARGETS_DIR / target
        if not target_dir.exists():
            missing.append(target)
            continue
        manifest_path = target_dir / "manifest.json"
        if manifest_path.exists():
            state_targets, state_missing = _child_target_state_paths(target_dir)
            for missing_target_id in state_missing:
                missing.append(missing_target_id)
            for path, _ in state_targets:
                required.add(path)
            continue
        required.add(target_dir)
    return required, missing


def _verify_target_artifacts(target_dir: Path) -> list[str]:
    missing: list[str] = []
    s_path = _expected_s_path(target_dir)
    if not s_path.exists():
        missing.append(f"{s_path}: expected source artifact missing")
    benchmark_path = target_dir / "benchmark.json"
    if not benchmark_path.exists():
        missing.append(f"{benchmark_path}: benchmark artifact missing")
    return missing


def _artifact_summary(scope_targets: list[str]) -> tuple[bool, list[str]]:
    required_targets, missing_dirs = _collect_required_artifact_targets(scope_targets)
    errors = []
    for missing_dir in missing_dirs:
        errors.append(f"missing target directory for required artifact scope: {missing_dir}")
    for target_dir in sorted(required_targets, key=lambda item: str(item).lower()):
        errors.extend(_verify_target_artifacts(target_dir))
    if not errors:
        return True, []
    return False, errors


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

    artifact_ok, artifact_errors = _artifact_summary(benchmark_targets)
    required_target_dirs, missing_scope = _collect_required_artifact_targets(benchmark_targets)
    print(f"\nprecommit: artifact scope requires {len(required_target_dirs)} target directories")
    for target_dir in sorted(required_target_dirs, key=lambda item: str(item).lower()):
        print(f"  {target_dir}")
    for missing_dir in sorted(set(missing_scope)):
        print(f"  !! missing scope directory: {missing_dir}")
    if not artifact_ok:
        print("\nprecommit: artifact check failed before commit checks")
        for error in artifact_errors:
            print(f"  {error}")
        return 1

    for command, env in steps:
        returncode = _run(command) if env is None else _run(command, env=env)
        if returncode != 0:
            return returncode

    print("\nprecommit: ok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
