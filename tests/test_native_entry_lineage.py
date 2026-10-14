"""Native refusal of premature unphased absolute control promotion."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_entry_lineage_refusal_and_exact_bytes(tmp_path):
    compiler = shutil.which("cc")
    backend = Path(os.environ.get("AMIGA_TEST_BACKEND", ROOT / "src/build/libamiga_backend.so"))
    if compiler is None or not backend.exists():
        pytest.skip("built native backend and host compiler required")
    driver = tmp_path / "runtime-context"
    built = subprocess.run(
        [compiler, "-Isrc", "-D_POSIX_C_SOURCE=200809L", "-std=c11", "-O0", "-g",
         str(ROOT / "tests/native/runtime_entry_lineage_fixture.c"), str(backend),
         f"-Wl,-rpath,{backend.parent}", "-o", str(driver)],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    assert built.returncode == 0, built.stderr
    result = subprocess.run([str(driver), str(tmp_path)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "entry lineage fixtures passed" in result.stdout
    vasm = ROOT / "ext/vasm/vasmm68k_mot"
    if not vasm.exists():
        pytest.skip("vasm required for independent exact rebuild")
    for explicit in (0, 1, 2, 3, 4, 5, 7, 8, 10):
        output = tmp_path / f"rebuilt-{explicit}.bin"
        assembled = subprocess.run(
            [str(vasm), "-quiet", "-Fbin", "-m68000", "-no-opt", "-o", str(output),
             str(tmp_path / f"entry-{explicit}.s")],
            capture_output=True, text=True, timeout=30,
        )
        assert assembled.returncode == 0, assembled.stderr
        assert output.read_bytes() == (tmp_path / f"entry-{explicit}.bin").read_bytes()
