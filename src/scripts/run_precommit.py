from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = ROOT / "src" / "benchmark.json"
BUILD_BAT = ROOT / "src" / "build.bat"
TEST_BAT = ROOT / "src" / "test.bat"
TEST_INTEGRATION_BAT = ROOT / "src" / "test_integration.bat"
TEST_EXPLICIT_BAT = ROOT / "src" / "test_explicit.bat"
NATIVE_C_UNIT_EXE = ROOT / "src" / "build" / "m68k_c_unit_tests.exe"
CORPUS_GENERATOR_PATH = ROOT / "src" / "scripts" / "generate_c99_assembler_corpus.py"

CPU_NAMES = ("68000", "68010", "68020", "68030", "68040", "68060")


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _python_exe() -> str:
    candidate = ROOT / ".venv" / "Scripts" / "python.exe"
    return str(candidate) if candidate.exists() else "python"


def _parse_variable_modules(batch_path: Path, variable_name: str) -> list[str]:
    modules: list[str] = []
    collecting = False
    for raw_line in batch_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not collecting:
            if stripped.startswith(f"set {variable_name}="):
                collecting = True
                remainder = stripped.split("=", 1)[1].strip()
                if remainder and remainder != "^":
                    modules.extend(part for part in remainder.replace("^", " ").split() if part)
                if not stripped.endswith("^"):
                    break
            continue
        content = stripped[:-1].strip() if stripped.endswith("^") else stripped
        if content:
            modules.extend(content.split())
        if not stripped.endswith("^"):
            break
    return modules


def _parse_direct_unittest_modules(batch_path: Path) -> list[str]:
    modules: list[str] = []
    collecting = False
    for raw_line in batch_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not collecting:
            if "-m unittest" in stripped:
                collecting = True
                tail = stripped.split("-m unittest", 1)[1].strip()
                if tail and tail != "^":
                    modules.extend(part for part in tail.replace("^", " ").split() if part)
                if not stripped.endswith("^"):
                    break
            continue
        content = stripped[:-1].strip() if stripped.endswith("^") else stripped
        if content:
            modules.extend(content.split())
        if not stripped.endswith("^"):
            break
    return modules


def _run_build() -> dict[str, object]:
    start = time.perf_counter()
    result = subprocess.run(
        ["cmd", "/c", str(BUILD_BAT)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    return {
        "seconds": round(elapsed, 3),
        "returncode": int(result.returncode),
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _parse_unittest_output(output: str, ok: bool) -> dict[str, object]:
    ran_match = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", output)
    status_match = re.search(r"^(OK|FAILED)(?: \(([^)]*)\))?$", output, re.MULTILINE)
    tests_run = int(ran_match.group(1)) if ran_match else 0
    skipped = 0
    failures = 0
    errors = 0
    expected_failures = 0
    unexpected_successes = 0
    if status_match and status_match.group(2):
        for part in status_match.group(2).split(","):
            key, _, value = part.strip().partition("=")
            if not value:
                continue
            count = int(value)
            if key == "skipped":
                skipped = count
            elif key == "failures":
                failures = count
            elif key == "errors":
                errors = count
            elif key == "expected failures":
                expected_failures = count
            elif key == "unexpected successes":
                unexpected_successes = count
    if not ok and status_match is None:
        failures = 1
    return {
        "tests_run": tests_run,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "expected_failures": expected_failures,
        "unexpected_successes": unexpected_successes,
    }


def _run_native_c_unit() -> dict[str, object]:
    start = time.perf_counter()
    result = subprocess.run(
        [str(NATIVE_C_UNIT_EXE)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    return {
        "name": "native_c",
        "seconds": round(elapsed, 3),
        "ok": result.returncode == 0,
        "tests_run": 0,
        "failures": 0 if result.returncode == 0 else 1,
        "errors": 0,
        "skipped": 0,
        "expected_failures": 0,
        "unexpected_successes": 0,
        "output": result.stdout + result.stderr,
    }


def _run_unittest_module(module_name: str, extra_env: dict[str, str] | None = None) -> dict[str, object]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    start = time.perf_counter()
    result = subprocess.run(
        [_python_exe(), "-m", "unittest", module_name],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    elapsed = time.perf_counter() - start
    combined_output = result.stdout + result.stderr
    parsed = _parse_unittest_output(combined_output, result.returncode == 0)
    return {
        "name": module_name,
        "seconds": round(elapsed, 3),
        "ok": result.returncode == 0,
        "tests_run": parsed["tests_run"],
        "failures": parsed["failures"],
        "errors": parsed["errors"],
        "skipped": parsed["skipped"],
        "expected_failures": parsed["expected_failures"],
        "unexpected_successes": parsed["unexpected_successes"],
        "output": combined_output,
    }


def _summarize_stage_runs(runs: list[dict[str, object]]) -> dict[str, object]:
    return {
        "seconds": round(sum(float(run["seconds"]) for run in runs), 3),
        "ok": all(bool(run["ok"]) for run in runs),
        "tests_run": sum(int(run["tests_run"]) for run in runs),
        "failures": sum(int(run["failures"]) for run in runs),
        "errors": sum(int(run["errors"]) for run in runs),
        "skipped": sum(int(run["skipped"]) for run in runs),
        "expected_failures": sum(int(run["expected_failures"]) for run in runs),
        "unexpected_successes": sum(int(run["unexpected_successes"]) for run in runs),
        "timings": {
            "runs": [
                {
                    "name": str(run["name"]),
                    "seconds": float(run["seconds"]),
                    "ok": bool(run["ok"]),
                    "tests_run": int(run["tests_run"]),
                }
                for run in runs
            ]
        },
        "output": "".join(str(run["output"]) for run in runs),
    }


def _run_unit_stage() -> dict[str, object]:
    runs = [_run_native_c_unit()]
    if runs[0]["ok"]:
        for module in _parse_variable_modules(TEST_BAT, "UNIT_MODULES"):
            runs.append(_run_unittest_module(module))
    return _summarize_stage_runs(runs)


def _run_module_stage(
    batch_path: Path,
    variable_name: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> dict[str, object]:
    modules = (
        _parse_variable_modules(batch_path, variable_name)
        if variable_name is not None
        else _parse_direct_unittest_modules(batch_path)
    )
    runs = [_run_unittest_module(module, extra_env) for module in modules]
    return _summarize_stage_runs(runs)


def _collect_corpus_stats() -> dict[str, object]:
    start = time.perf_counter()
    generator = _load_module(CORPUS_GENERATOR_PATH, "src_precommit_corpus_generator")
    by_cpu: dict[str, dict[str, int]] = {}
    unique_case_ids: set[str] = set()
    total_cases = 0
    for cpu_name in CPU_NAMES:
        cases = tuple(generator.generate_cases(cpu_name))
        by_cpu[cpu_name] = {
            "cases": len(cases),
            "mnemonics": len({str(case.mnemonic) for case in cases}),
        }
        total_cases += len(cases)
        unique_case_ids.update(str(case.case_id) for case in cases)
    return {
        "seconds": round(time.perf_counter() - start, 3),
        "by_cpu": by_cpu,
        "total_cpu_qualified_cases": total_cases,
        "unique_case_ids": len(unique_case_ids),
    }


def _write_benchmark(data: dict[str, object]) -> None:
    BENCHMARK_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    build = _run_build()
    benchmark: dict[str, object] = {
        "benchmark_version": 2,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "build": {key: value for key, value in build.items() if key not in {"stdout", "stderr"}},
        "corpus": _collect_corpus_stats(),
    }
    if not build["ok"]:
        benchmark["unit"] = {"ok": False, "timings": {"runs": []}}
        benchmark["integration"] = {"ok": False, "timings": {"runs": []}}
        benchmark["explicit"] = {"ok": False, "timings": {"runs": []}}
        benchmark["total_seconds"] = round(float(build["seconds"]) + float(benchmark["corpus"]["seconds"]), 3)
        benchmark["status"] = "build_failed"
        _write_benchmark(benchmark)
        sys.stdout.write(build["stdout"])
        sys.stderr.write(build["stderr"])
        return int(build["returncode"])

    unit = _run_unit_stage()
    if unit["ok"]:
        integration = _run_module_stage(TEST_INTEGRATION_BAT, "INTEGRATION_MODULES")
    else:
        integration = {
            "seconds": 0.0,
            "ok": False,
            "tests_run": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expected_failures": 0,
            "unexpected_successes": 0,
            "timings": {"runs": []},
            "output": "skipped because unit suite failed\n",
        }
    if unit["ok"] and integration["ok"]:
        explicit = _run_module_stage(TEST_EXPLICIT_BAT, None, {"AMIGA_INCLUDE_EXPLICIT_TESTS": "1"})
    else:
        explicit = {
            "seconds": 0.0,
            "ok": False,
            "tests_run": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expected_failures": 0,
            "unexpected_successes": 0,
            "timings": {"runs": []},
            "output": "skipped because earlier suite failed\n",
        }

    benchmark["unit"] = {key: value for key, value in unit.items() if key != "output"}
    benchmark["integration"] = {key: value for key, value in integration.items() if key != "output"}
    benchmark["explicit"] = {key: value for key, value in explicit.items() if key != "output"}
    benchmark["total_seconds"] = round(
        float(build["seconds"])
        + float(benchmark["corpus"]["seconds"])
        + float(unit["seconds"])
        + float(integration["seconds"])
        + float(explicit["seconds"]),
        3,
    )
    benchmark["status"] = "ok" if unit["ok"] and integration["ok"] and explicit["ok"] else "test_failed"
    _write_benchmark(benchmark)

    sys.stdout.write(build["stdout"])
    sys.stderr.write(build["stderr"])
    sys.stdout.write(unit["output"])
    sys.stdout.write(integration["output"])
    sys.stdout.write(explicit["output"])
    return 0 if unit["ok"] and integration["ok"] and explicit["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
