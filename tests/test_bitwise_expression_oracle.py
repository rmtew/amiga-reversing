"""Generic flag expressions checked against independent vasm output bytes."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = "FLAG_BIT equ 4\nFLAG equ 1<<FLAG_BIT\nOTHER equ 1\n"


@pytest.fixture
def assemblers():
    local_vasm = ROOT / "ext/vasm/vasmm68k_mot"
    vasm = os.environ.get("VASM") or (
        str(local_vasm) if local_vasm.is_file() else shutil.which("vasmm68k_mot")
    )
    native = Path(os.environ.get("M68K_ASSEMBLER", ROOT / "src/build/m68k_assembler_app.exe"))
    if not vasm or not native.is_file():
        pytest.skip("native assembler and vasm required; set M68K_ASSEMBLER and VASM")
    return str(native), vasm


@pytest.mark.parametrize(("statement", "expected_hex"), [
    ("dc.b (FLAG|$08)&~FLAG", "08"),
    ("dc.w (FLAG|$8008)&~FLAG", "8008"),
    ("dc.l (FLAG|$80000008)&~FLAG", "80000008"),
    ("move.b #(FLAG|$08)&~FLAG,d0", "103c0008"),
    ("move.w #(FLAG|$8008)&~FLAG,d0", "303c8008"),
    ("move.l #(FLAG|$80000008)&~FLAG,d0", "203c80000008"),
    ("dc.b OTHER|FLAG&~FLAG", "01"),
    ("dc.w 2&3<<1", "0002"),
    ("dc.l ~0", "ffffffff"),
    ("dc.l ~$80000000", "7fffffff"),
    ("dc.b ~(OTHER+2)&$ff", "fc"),
    ("dc.w (8&3)+5", "0005"),
    ("dc.l 1<<(2+1)", "00000008"),
    ("dc.l $80000000<<1", "00000000"),
    ("dc.l OTHER!FLAG&~FLAG", "00000001"),
])
def test_generic_bitwise_forms_match_vasm(assemblers, tmp_path, statement, expected_hex):
    native, vasm = assemblers
    source = tmp_path / "flags.s"
    expected = bytes.fromhex(expected_hex)
    padding = bytes((-len(expected)) % 4)
    suffix = " dc.b " + ",".join("0" for _ in padding) + "\n" if padding else ""
    source.write_text(DEFINITIONS + " section flags,code\n " + statement + "\n" + suffix,
                      encoding="ascii")
    native_output = tmp_path / "native.hunk"
    vasm_hunk_output = tmp_path / "vasm.hunk"
    vasm_output = tmp_path / "vasm.bin"
    for command in (
        [native, "assemble-platform-file", "--backend", "amiga-hunk", "--include-dir",
         str(tmp_path), str(source), str(native_output)],
        [vasm, "-quiet", "-Fhunkexe", "-kick1hunks", "-nosym", "-no-opt", "-o",
         str(vasm_hunk_output), str(source)],
        [vasm, "-quiet", "-Fbin", "-no-opt", "-o", str(vasm_output), str(source)],
    ):
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, result.stderr + result.stdout
    assert native_output.read_bytes() == vasm_hunk_output.read_bytes()
    assert vasm_output.read_bytes() == expected + padding
