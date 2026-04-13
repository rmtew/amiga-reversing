from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.real_target_fixtures import REAL_TARGET_FIXTURES

CLI = ROOT / "src" / "build" / "platform_file_cli.exe"


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


def main() -> int:
    if not CLI.exists():
        raise SystemExit(f"missing built CLI: {CLI}")

    for target in REAL_TARGET_FIXTURES:
        binary_path = Path(target["binary"])
        try:
            cli_binary = binary_path.relative_to(ROOT).as_posix()
        except ValueError:
            cli_binary = str(binary_path)
        disassembly = run_capture("disassemble-file", "--syntax", "genam", target["backend"], cli_binary)
        Path(target["source"]).write_text(disassembly, encoding="utf-8")

        benchmark = json.loads(run_capture("benchmark-file", target["backend"], cli_binary))
        Path(target["benchmark"]).write_text(json.dumps(benchmark, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        print(f"updated {Path(target['source']).name} and {Path(target['benchmark']).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
