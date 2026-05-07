from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.real_target_fixtures import REAL_TARGET_FIXTURES

CLI = ROOT / "src" / "build" / "platform_file_cli.exe"
BENCHMARK_SAMPLE_COUNT = 3


def run_capture(*args: str) -> str:
    result = subprocess.run(
        [str(CLI), *args],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "command failed")
    return result.stdout


def normalize_benchmark_stats(payload: dict[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    normalized.pop("timing", None)
    return normalized


def run_disassembly_with_benchmark(backend: str, cli_binary: str, benchmark_path: Path) -> tuple[str, dict[str, object]]:
    result = subprocess.run(
        [
            str(CLI),
            "disassemble-file",
            "--benchmark-json-out",
            str(benchmark_path),
            backend,
            cli_binary,
        ],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "command failed")
    payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    return result.stdout, payload


def main() -> int:
    if not CLI.exists():
        raise SystemExit(f"missing built CLI: {CLI}")

    for target in REAL_TARGET_FIXTURES:
        binary_path = Path(target["binary"])
        try:
            cli_binary = binary_path.relative_to(ROOT).as_posix()
        except ValueError:
            cli_binary = str(binary_path)
        benchmark_path = Path(target["benchmark"])
        best_payload = None
        best_time = None
        disassembly = None
        baseline_stats = None
        with tempfile.TemporaryDirectory(dir=str(ROOT / "src" / "build")) as tmp:
            temp_benchmark_path = Path(tmp) / "benchmark.json"
            for _ in range(BENCHMARK_SAMPLE_COUNT):
                current_disassembly, payload = run_disassembly_with_benchmark(
                    target["backend"], cli_binary, temp_benchmark_path
                )
                current_stats = normalize_benchmark_stats(payload)
                if baseline_stats is None:
                    baseline_stats = current_stats
                    disassembly = current_disassembly
                elif current_stats != baseline_stats:
                    raise RuntimeError(f"benchmark stats changed across samples for {target['name']}")
                current_time = float(payload["timing"]["total_seconds"])
                if best_payload is None or best_time is None or current_time < best_time:
                    best_payload = payload
                    best_time = current_time
        if disassembly is None or best_payload is None:
            raise RuntimeError(f"failed to collect fixture data for {target['name']}")
        Path(target["source"]).write_text(disassembly, encoding="utf-8")
        benchmark = best_payload
        benchmark_path.write_text(json.dumps(benchmark, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        print(f"updated {Path(target['source']).name} and {Path(target['benchmark']).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
