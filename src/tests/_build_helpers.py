from __future__ import annotations

import os
import shutil
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
TEST_DLL_DIR = BUILD_DIR / "test_dll" / str(os.getpid())
REQUIRED_OUTPUTS = (
    BUILD_DIR / "m68k_assembler_app.exe",
    BUILD_DIR / "m68k_assembler_lib.dll",
    BUILD_DIR / "m68k_disassembler_lib.dll",
    BUILD_DIR / "platform_disk_cli.exe",
    BUILD_DIR / "platform_disk_lib.dll",
    BUILD_DIR / "platform_file_cli.exe",
    BUILD_DIR / "platform_file_lib.dll",
)


def require_built_tools() -> Path:
    missing = [str(path) for path in REQUIRED_OUTPUTS if not path.exists()]
    if missing:
        raise AssertionError("Missing built tool outputs:\n" + "\n".join(missing))
    return BUILD_DIR


@lru_cache(maxsize=None)
def prepare_test_dll(source_path: Path) -> Path:
    require_built_tools()
    if not source_path.exists():
        raise AssertionError(f"Missing DLL source: {source_path}")
    TEST_DLL_DIR.mkdir(parents=True, exist_ok=True)
    copied_path = TEST_DLL_DIR / source_path.name
    shutil.copy2(source_path, copied_path)
    if not copied_path.exists():
        raise AssertionError(f"Failed to copy DLL: {copied_path}")
    return copied_path
