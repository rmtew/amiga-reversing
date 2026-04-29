from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _assemble_vasm_hunk(tmp_path: Path, source_text: str, name: str) -> Path:
    assembler = PROJECT_ROOT / "ext" / "vasm" / "vasmm68k_mot.exe"
    if not assembler.exists():
        pytest.skip("bundled vasm is missing")
    source_path = tmp_path / f"{name}.s"
    output_path = tmp_path / f"{name}.hunk"
    source_path.write_text(source_text, encoding="ascii", newline="\n")
    result = subprocess.run(
        [
            str(assembler),
            "-quiet",
            "-nocase",
            "-Fhunk",
            "-o",
            str(output_path),
            str(source_path),
        ],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert output_path.exists()
    return output_path


def test_vasm_mot_org_accepts_absolute_pc_block_without_padding_payload(tmp_path: Path) -> None:
    source = "    SECTION section,code\n    ORG 1024\nstart:\n    moveq #0,d0\n    rts\n"

    output_path = _assemble_vasm_hunk(tmp_path, source, "org")

    assert output_path.stat().st_size < 128


def test_vasm_mot_rorg_is_not_the_absolute_source_block_contract(tmp_path: Path) -> None:
    plain = "    SECTION section,code\nstart:\n    moveq #0,d0\n    rts\n"
    rorg = "    SECTION section,code\n    RORG 1024\nstart:\n    moveq #0,d0\n    rts\n"

    plain_path = _assemble_vasm_hunk(tmp_path, plain, "plain")
    rorg_path = _assemble_vasm_hunk(tmp_path, rorg, "rorg")

    assert rorg_path.stat().st_size > plain_path.stat().st_size + 512
