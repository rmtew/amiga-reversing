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


def _run_test_batch(batch_path: Path) -> dict[str, object]:
    start = time.perf_counter()
    result = subprocess.run(
        ["cmd", "/c", str(batch_path), "--no-build"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    combined_output = result.stdout + result.stderr
    parsed = _parse_unittest_output(combined_output, result.returncode == 0)
    return {
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


def _collect_corpus_stats() -> dict[str, object]:
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
        "benchmark_version": 1,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "build": {key: value for key, value in build.items() if key not in {"stdout", "stderr"}},
        "corpus": _collect_corpus_stats(),
    }
    if not build["ok"]:
        benchmark["unit"] = {"ok": False}
        benchmark["integration"] = {"ok": False}
        benchmark["total_seconds"] = round(float(build["seconds"]), 3)
        benchmark["status"] = "build_failed"
        _write_benchmark(benchmark)
        sys.stdout.write(build["stdout"])
        sys.stderr.write(build["stderr"])
        return int(build["returncode"])

    unit = _run_test_batch(TEST_BAT)
    integration = _run_test_batch(TEST_INTEGRATION_BAT) if unit["ok"] else {
        "seconds": 0.0,
        "ok": False,
        "tests_run": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "expected_failures": 0,
        "unexpected_successes": 0,
        "output": "skipped because unit suite failed\n",
    }
    benchmark["unit"] = {key: value for key, value in unit.items() if key != "output"}
    benchmark["integration"] = {key: value for key, value in integration.items() if key != "output"}
    benchmark["total_seconds"] = round(float(build["seconds"]) + float(unit["seconds"]) + float(integration["seconds"]), 3)
    benchmark["status"] = "ok" if unit["ok"] and integration["ok"] else "test_failed"
    _write_benchmark(benchmark)

    sys.stdout.write(build["stdout"])
    sys.stderr.write(build["stderr"])
    sys.stdout.write(unit["output"])
    sys.stdout.write(integration["output"])
    return 0 if unit["ok"] and integration["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
