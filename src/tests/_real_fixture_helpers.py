from __future__ import annotations

import json
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
FILE_EXE = BUILD_DIR / "platform_file_cli.exe"


@lru_cache(maxsize=None)
def analyze_real_file(platform_name: str, path: str) -> dict[str, object]:
    result = subprocess.run(
        [str(FILE_EXE), "analyze-file", platform_name, path],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


@lru_cache(maxsize=None)
def disassemble_real_file(platform_name: str, path: str) -> str:
    result = subprocess.run(
        [str(FILE_EXE), "disassemble-file", platform_name, path],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout
