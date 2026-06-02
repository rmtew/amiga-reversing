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
TEST_WEB_E2E_CDP_PY = ROOT / "tests" / "test_web_e2e_cdp.py"
NATIVE_C_UNIT_EXE = ROOT / "src" / "build" / "m68k_c_unit_tests.exe"
CORPUS_GENERATOR_PATH = ROOT / "src" / "scripts" / "generate_c99_assembler_corpus.py"
FIND_DEAD_CODE_PATH = ROOT / "src" / "scripts" / "find_dead_code.py"

CPU_NAMES = ("68000", "68010", "68020", "68030", "68040", "68060")
DEAD_CODE_C_CHECKS = (
    "c-static-functions",
    "c-static-prototypes",
    "c-external-functions",
    "c-local-typedefs",
    "c-local-macros",
)
STYLE_MODULES = ("src.tests.test_c_style",)


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
    no_tests_ran = re.search(r"^NO TESTS RAN$", output, re.MULTILINE) is not None
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
        "no_tests_ran": no_tests_ran,
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
        "no_tests_ran": False,
        "output": result.stdout + result.stderr,
    }


def _run_dead_code_c_scan() -> dict[str, object]:
    start = time.perf_counter()
    command = [_python_exe(), str(FIND_DEAD_CODE_PATH), "--fail-on-findings"]
    for check in DEAD_CODE_C_CHECKS:
        command.extend(["--check", check])
    result = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    return {
        "name": "find_dead_code_c",
        "seconds": round(elapsed, 3),
        "ok": result.returncode == 0,
        "tests_run": 0,
        "failures": 0 if result.returncode == 0 else 1,
        "errors": 0,
        "skipped": 0,
        "expected_failures": 0,
        "unexpected_successes": 0,
        "no_tests_ran": False,
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
        "no_tests_ran": parsed["no_tests_ran"],
        "output": combined_output,
    }


def _parse_pytest_output(output: str, ok: bool) -> dict[str, object]:
    summary_match = re.search(r"=+ ([^=]*?) in [0-9.]+s =+", output)
    summary = summary_match.group(1) if summary_match else ""
    if not summary:
        fallback_match = re.search(
            r"((?:\d+ (?:passed|failed|error|errors|skipped|deselected),? ?)+)in [0-9.]+s",
            output,
        )
        summary = fallback_match.group(1).strip() if fallback_match else ""
    tests_run = 0
    skipped = 0
    failures = 0
    errors = 0
    for count_text, kind in re.findall(r"(\d+) (passed|failed|error|errors|skipped|deselected)", summary):
        count = int(count_text)
        if kind == "passed":
            tests_run += count
        elif kind == "skipped":
            skipped += count
        elif kind == "failed":
            failures += count
            tests_run += count
        elif kind in {"error", "errors"}:
            errors += count
    if not ok and failures == 0 and errors == 0:
        failures = 1
    return {
        "tests_run": tests_run,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "expected_failures": 0,
        "unexpected_successes": 0,
        "no_tests_ran": ok and tests_run == 0 and skipped == 0,
    }


def _run_pytest_file(
    name: str,
    path: Path,
    extra_env: dict[str, str] | None = None,
) -> dict[str, object]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    start = time.perf_counter()
    result = subprocess.run(
        [_python_exe(), "-m", "pytest", "-o", "addopts=", str(path), "-q"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    elapsed = time.perf_counter() - start
    combined_output = result.stdout + result.stderr
    parsed = _parse_pytest_output(combined_output, result.returncode == 0)
    return {
        "name": name,
        "seconds": round(elapsed, 3),
        "ok": result.returncode == 0,
        "tests_run": parsed["tests_run"],
        "failures": parsed["failures"],
        "errors": parsed["errors"],
        "skipped": parsed["skipped"],
        "expected_failures": parsed["expected_failures"],
        "unexpected_successes": parsed["unexpected_successes"],
        "no_tests_ran": parsed["no_tests_ran"],
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
                    "no_tests_ran": bool(run.get("no_tests_ran", False)),
                }
                for run in runs
            ]
        },
        "output": "".join(str(run["output"]) for run in runs),
    }


def _module_short_name(name: str) -> str:
    if name == "native_c":
        return name
    return name.rsplit(".", 1)[-1]


def _print_stage_summary(stage_name: str, stage: dict[str, object]) -> None:
    status = "OK" if stage["ok"] else "FAILED"
    sys.stdout.write(
        f"{stage_name}: {status}  tests={int(stage['tests_run'])}  seconds={float(stage['seconds']):.3f}\n"
    )
    for run in stage["timings"]["runs"]:
        run_status = "ok" if run["ok"] else "failed"
        if run.get("no_tests_ran", False):
            sys.stdout.write(
                f"  {_module_short_name(str(run['name']))}: filtered  seconds={float(run['seconds']):.3f}\n"
            )
        else:
            sys.stdout.write(
                f"  {_module_short_name(str(run['name']))}: {run_status}  tests={int(run['tests_run'])}  seconds={float(run['seconds']):.3f}\n"
            )


def _print_failed_stage_details(stage_name: str, stage: dict[str, object]) -> None:
    for run in stage["timings"]["runs"]:
        if run["ok"]:
            continue
        sys.stdout.write(f"\n[{stage_name} failure] {run['name']}\n")
        for full_run in stage.get("_runs", []):
            if full_run["name"] == run["name"]:
                sys.stdout.write(str(full_run["output"]))
                break


def _run_unit_stage() -> dict[str, object]:
    runs = [_run_native_c_unit()]
    if runs[0]["ok"]:
        for module in _parse_variable_modules(TEST_BAT, "UNIT_MODULES"):
            if module in STYLE_MODULES:
                continue
            runs.append(_run_unittest_module(module))
    summary = _summarize_stage_runs(runs)
    summary["_runs"] = runs
    return summary


def _run_style_stage() -> dict[str, object]:
    runs = [_run_unittest_module(module) for module in STYLE_MODULES]
    summary = _summarize_stage_runs(runs)
    summary["_runs"] = runs
    return summary


def _run_dead_code_stage() -> dict[str, object]:
    runs = [_run_dead_code_c_scan()]
    summary = _summarize_stage_runs(runs)
    summary["_runs"] = runs
    return summary


def _run_module_stage(
    batch_path: Path,
    variable_name: str | None = None,
    extra_env: dict[str, str] | None = None,
    skip_modules: tuple[str, ...] = (),
) -> dict[str, object]:
    modules = (
        _parse_variable_modules(batch_path, variable_name)
        if variable_name is not None
        else _parse_direct_unittest_modules(batch_path)
    )
    if skip_modules:
        modules = [module for module in modules if module not in skip_modules]
    runs = [_run_unittest_module(module, extra_env) for module in modules]
    summary = _summarize_stage_runs(runs)
    summary["_runs"] = runs
    return summary


def _run_web_e2e_stage() -> dict[str, object]:
    if os.environ.get("M68K_SKIP_BRAVE_CDP") == "1":
        runs = [
            {
                "name": "tests.test_web_e2e_cdp",
                "seconds": 0.0,
                "ok": True,
                "tests_run": 0,
                "failures": 0,
                "errors": 0,
                "skipped": 1,
                "expected_failures": 0,
                "unexpected_successes": 0,
                "no_tests_ran": False,
                "output": "skipped because M68K_SKIP_BRAVE_CDP=1\n",
            }
        ]
    else:
        runs = [
            _run_pytest_file(
                "tests.test_web_e2e_cdp",
                TEST_WEB_E2E_CDP_PY,
                {"M68K_RUN_BRAVE_CDP": "1"},
            )
        ]
    summary = _summarize_stage_runs(runs)
    summary["_runs"] = runs
    return summary


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
    style = _run_style_stage()
    if not style["ok"]:
        benchmark: dict[str, object] = {
            "benchmark_version": 2,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "style": {key: value for key, value in style.items() if key != "output"},
            "build": {"ok": False, "returncode": 0, "seconds": 0.0},
            "corpus": {"seconds": 0.0},
            "dead_code": {"ok": False, "timings": {"runs": []}},
            "unit": {"ok": False, "timings": {"runs": []}},
            "integration": {"ok": False, "timings": {"runs": []}},
            "explicit": {"ok": False, "timings": {"runs": []}},
            "web_e2e": {"ok": False, "timings": {"runs": []}},
            "total_seconds": float(style["seconds"]),
            "status": "style_failed",
        }
        _write_benchmark(benchmark)
        _print_stage_summary("style", style)
        _print_failed_stage_details("style", style)
        sys.stdout.write("build: skipped because style checks failed\n")
        sys.stdout.write("dead_code: skipped because style checks failed\n")
        sys.stdout.write("unit: skipped because style checks failed\n")
        sys.stdout.write("integration: skipped because style checks failed\n")
        sys.stdout.write("explicit: skipped because style checks failed\n")
        sys.stdout.write("web_e2e: skipped because style checks failed\n")
        return 1
    build = _run_build()
    benchmark = {
        "benchmark_version": 2,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "style": {key: value for key, value in style.items() if key != "output"},
        "build": {key: value for key, value in build.items() if key not in {"stdout", "stderr"}},
        "corpus": _collect_corpus_stats(),
    }
    if not build["ok"]:
        benchmark["dead_code"] = {"ok": False, "timings": {"runs": []}}
        benchmark["unit"] = {"ok": False, "timings": {"runs": []}}
        benchmark["integration"] = {"ok": False, "timings": {"runs": []}}
        benchmark["explicit"] = {"ok": False, "timings": {"runs": []}}
        benchmark["web_e2e"] = {"ok": False, "timings": {"runs": []}}
        benchmark["total_seconds"] = round(
            float(style["seconds"]) + float(build["seconds"]) + float(benchmark["corpus"]["seconds"]),
            3,
        )
        benchmark["status"] = "build_failed"
        _write_benchmark(benchmark)
        _print_stage_summary("style", style)
        sys.stdout.write(build["stdout"])
        sys.stderr.write(build["stderr"])
        return int(build["returncode"])

    dead_code = _run_dead_code_stage()
    if dead_code["ok"]:
        unit = _run_unit_stage()
    else:
        unit = {
            "seconds": 0.0,
            "ok": False,
            "tests_run": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expected_failures": 0,
            "unexpected_successes": 0,
            "timings": {"runs": []},
            "output": "skipped because dead-code scan failed\n",
            "_runs": [],
        }
    if dead_code["ok"] and unit["ok"]:
        integration = _run_module_stage(
            TEST_INTEGRATION_BAT,
            "INTEGRATION_MODULES",
            {"AMIGA_INCLUDE_HEAVY_UNIT_TESTS": "1"},
        )
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
            "_runs": [],
        }
    if dead_code["ok"] and unit["ok"] and integration["ok"]:
        explicit = _run_module_stage(
            TEST_EXPLICIT_BAT,
            None,
            {"AMIGA_INCLUDE_EXPLICIT_TESTS": "1"},
            skip_modules=STYLE_MODULES,
        )
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
            "_runs": [],
        }
    if dead_code["ok"] and unit["ok"] and integration["ok"] and explicit["ok"]:
        web_e2e = _run_web_e2e_stage()
    else:
        web_e2e = {
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
            "_runs": [],
        }

    benchmark["dead_code"] = {key: value for key, value in dead_code.items() if key != "output"}
    benchmark["unit"] = {key: value for key, value in unit.items() if key != "output"}
    benchmark["integration"] = {key: value for key, value in integration.items() if key != "output"}
    benchmark["explicit"] = {key: value for key, value in explicit.items() if key != "output"}
    benchmark["web_e2e"] = {key: value for key, value in web_e2e.items() if key != "output"}
    benchmark["total_seconds"] = round(
        float(style["seconds"])
        + float(build["seconds"])
        + float(benchmark["corpus"]["seconds"])
        + float(dead_code["seconds"])
        + float(unit["seconds"])
        + float(integration["seconds"])
        + float(explicit["seconds"])
        + float(web_e2e["seconds"]),
        3,
    )
    benchmark["status"] = (
        "ok"
        if dead_code["ok"] and unit["ok"] and integration["ok"] and explicit["ok"] and web_e2e["ok"]
        else "dead_code_failed"
        if not dead_code["ok"]
        else "test_failed"
    )
    _write_benchmark(benchmark)

    sys.stdout.write(build["stdout"])
    sys.stderr.write(build["stderr"])
    _print_stage_summary("style", style)
    _print_stage_summary("dead_code", dead_code)
    if dead_code["ok"]:
        _print_stage_summary("unit", unit)
    else:
        sys.stdout.write("unit: skipped because dead-code scan failed\n")
    if dead_code["ok"] and unit["ok"]:
        _print_stage_summary("integration", integration)
    else:
        sys.stdout.write("integration: skipped because earlier suite failed\n")
    if dead_code["ok"] and unit["ok"] and integration["ok"]:
        _print_stage_summary("explicit", explicit)
    else:
        sys.stdout.write("explicit: skipped because earlier suite failed\n")
    if dead_code["ok"] and unit["ok"] and integration["ok"] and explicit["ok"]:
        _print_stage_summary("web_e2e", web_e2e)
    else:
        sys.stdout.write("web_e2e: skipped because earlier suite failed\n")
    if not dead_code["ok"]:
        _print_failed_stage_details("dead_code", dead_code)
    if not unit["ok"] and dead_code["ok"]:
        _print_failed_stage_details("unit", unit)
    if not integration["ok"] and dead_code["ok"] and unit["ok"]:
        _print_failed_stage_details("integration", integration)
    if not explicit["ok"] and dead_code["ok"] and unit["ok"] and integration["ok"]:
        _print_failed_stage_details("explicit", explicit)
    if not web_e2e["ok"] and dead_code["ok"] and unit["ok"] and integration["ok"] and explicit["ok"]:
        _print_failed_stage_details("web_e2e", web_e2e)
    return 0 if dead_code["ok"] and unit["ok"] and integration["ok"] and explicit["ok"] and web_e2e["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
