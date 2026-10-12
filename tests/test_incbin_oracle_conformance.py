"""Black-box dialect checks; no licensed assembler binaries are downloaded."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def vasm() -> str:
    configured = os.environ.get("VASM")
    local = Path(__file__).resolve().parents[1] / "ext/vasm/vasmm68k_mot"
    executable = configured or (str(local) if local.is_file() else shutil.which("vasmm68k_mot"))
    if not executable:
        pytest.skip("real vasm unavailable; set VASM to a native Motorola-syntax executable")
    return executable


def assemble(vasm: str, root: Path, source: str, *flags: str):
    (root / "main.s").write_text(source, encoding="ascii")
    output = root / "out.bin"
    output.unlink(missing_ok=True)
    result = subprocess.run(
        [vasm, "-quiet", "-Fbin", *flags, "-o", str(output), "main.s"],
        cwd=root, capture_output=True, text=True, timeout=10,
    )
    return result, output.read_bytes() if output.exists() else None


@pytest.mark.parametrize("flags", [(), ("-devpac",)])
@pytest.mark.parametrize("quote", ['"', "'"])
def test_whole_file_quotes_case_odd_length_and_empty(vasm, tmp_path, flags, quote):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/a, b.bin").write_bytes(b"ABC")
    (tmp_path / "assets/empty.bin").write_bytes(b"")
    source = (f" dc.b $aa\n InCbIn {quote}assets/a, b.bin{quote}\n"
              ' incbin "assets/empty.bin"\n dc.b $bb\n')
    result, data = assemble(vasm, tmp_path, source, *flags)
    assert result.returncode == 0, result.stderr
    assert data == b"\xaaABC\xbb"  # No implicit INCBIN alignment, even with -devpac.


@pytest.mark.parametrize(("operands", "expected"), [
    ('"blob.bin",2', bytes([2, 3, 4])),
    ('"blob.bin",1,2', bytes([1, 2])),
    ('"blob.bin",3,9', bytes([3, 4])),
    ('"blob.bin",5', b""),
    ('"blob.bin",0,0', bytes(range(5))),
    ('"blob.bin",1,-1', bytes([1, 2, 3, 4])),
    ('"blob.bin",1,2,3', bytes([1, 2])),  # Oracle ignores the extra operand.
])
def test_vasm_ranges_and_devpac_mode_rejection(vasm, tmp_path, operands, expected):
    (tmp_path / "blob.bin").write_bytes(bytes(range(5)))
    source = f" dc.b $aa\n incbin {operands}\n dc.b $bb\n"
    result, data = assemble(vasm, tmp_path, source)
    assert result.returncode == 0, result.stderr
    assert data == b"\xaa" + expected + b"\xbb"
    result, _ = assemble(vasm, tmp_path, source, "-devpac")
    assert result.returncode != 0
    assert "syntax error" in result.stderr


@pytest.mark.parametrize(("operands", "error"), [
    ('"blob.bin",-1', "bad file-offset"),
    ('"blob.bin",6', "bad file-offset"),
    ('"missing.bin"', "could not open"),
])
def test_invalid_incbin(vasm, tmp_path, operands, error):
    (tmp_path / "blob.bin").write_bytes(bytes(range(5)))
    result, _ = assemble(vasm, tmp_path, f" incbin {operands}\n")
    assert result.returncode != 0
    assert error in result.stderr


def test_nested_include_uses_working_directory_not_include_parent(vasm, tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "blob.bin").write_bytes(b"ROOT")
    (tmp_path / "sub/blob.bin").write_bytes(b"SUB!")
    (tmp_path / "sub/part.s").write_text(' incbin "blob.bin"\n', encoding="ascii")
    result, data = assemble(vasm, tmp_path, ' include "sub/part.s"\n', f"-I{tmp_path / 'sub'}")
    assert result.returncode == 0, result.stderr
    assert data == b"ROOT"


@pytest.mark.parametrize(("flags", "statement", "expected"), [
    ((), " dc.w $1234", b"ABC\x12\x34"),
    (("-devpac",), " dc.w $1234", b"ABC\0\x12\x34"),
    ((), " even\n dc.w $1234", b"ABC\0\x12\x34"),
    (("-devpac",), " even\n dc.w $1234", b"ABC\0\x12\x34"),
    ((), " ds.b 1\n dc.w $1234", b"ABC\0\x12\x34"),
])
def test_explicit_layout_and_profile_alignment(vasm, tmp_path, flags, statement, expected):
    (tmp_path / "blob.bin").write_bytes(b"ABC")
    result, data = assemble(vasm, tmp_path, ' incbin "blob.bin"\n' + statement + "\n", *flags)
    assert result.returncode == 0, result.stderr
    assert data == expected


@pytest.mark.parametrize("flags", [(), ("-devpac",)])
def test_assets_labels_addresses_sections_full_hunk(vasm, tmp_path, flags):
    """Compare complete original-assembler artifacts, including relocations."""
    (tmp_path / "one.bin").write_bytes(bytes([1, 2]))
    (tmp_path / "two.bin").write_bytes(bytes([3, 4]))
    prefix = " section code,code\nstart:\n dc.l second\n section data,data\nfirst:\n"
    suffix = "\n dc.w second-first\n section workspace,bss\n ds.b 8\n"
    inline = prefix + " dc.b 1,2\nsecond:\n dc.b 3,4" + suffix
    external = prefix + ' incbin "one.bin"\nsecond:\n incbin "two.bin"' + suffix
    result, expected = assemble(vasm, tmp_path, inline, *flags, "-Fhunkexe", "-nosym")
    assert result.returncode == 0, result.stderr
    result, actual = assemble(vasm, tmp_path, external, *flags, "-Fhunkexe", "-nosym")
    assert result.returncode == 0, result.stderr
    assert actual == expected
