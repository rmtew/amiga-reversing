"""Package INCBIN path resolution and exact full-container oracle coverage."""
import shutil
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm.c_backend import (
    assemble_platform_source_path_with_c_backend,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/tests/fixtures/incbin"


def assemble(path: Path) -> bytes:
    return assemble_platform_source_path_with_c_backend("amiga-hunk", path)[0]


def test_incbin_moved_package_matches_vasm_full_container(tmp_path, monkeypatch):
    package = tmp_path / "moved package"
    shutil.copytree(FIXTURE, package)
    monkeypatch.chdir(tmp_path)
    rebuilt = assemble(package / "source.s")
    oracle = ROOT / "tools/vasmm68k_mot.exe"
    if not oracle.is_file():
        pytest.skip("vasm oracle unavailable")
    output = tmp_path / "oracle.hunk"
    subprocess.run(
        [str(oracle), "-quiet", "-Fhunkexe", "-kick1hunks", "-nosym", "-no-opt",
         "-o", str(output), "source.s"], cwd=package, check=True, capture_output=True,
    )
    assert rebuilt == output.read_bytes()
    assert len(rebuilt) == 72


@pytest.mark.parametrize("directory_link", [False, True])
def test_incbin_rejects_asset_symlinks(tmp_path, directory_link):
    package = tmp_path / "package"
    shutil.copytree(FIXTURE, package)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "first.bin").write_bytes(b"test")
    if directory_link:
        shutil.rmtree(package / "assets")
        (package / "assets").symlink_to(outside, target_is_directory=True)
    else:
        (package / "assets/first.bin").unlink()
        (package / "assets/first.bin").symlink_to(outside / "first.bin")
    with pytest.raises(RuntimeError, match="unsafe or missing INCBIN asset/root"):
        assemble(package / "source.s")


def test_incbin_range_operands_report_unsupported(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "package")
    source = tmp_path / "package/source.s"
    source.write_text(' SECTION assets,data\n INCBIN "assets/first.bin",1,2\n')
    with pytest.raises(RuntimeError, match="offset/length operands are unsupported"):
        assemble(source)


@pytest.mark.parametrize("operand", ["../outside.bin", "/tmp/outside.bin", "assets/.. /outside.bin",
                                    "assets./first.bin", "assets/first.bin "])
def test_incbin_rejects_nonportable_path_aliases(tmp_path, operand):
    shutil.copytree(FIXTURE, tmp_path / "package")
    source = tmp_path / "package/source.s"
    source.write_text(f' SECTION assets,data\n INCBIN "{operand}"\n')
    with pytest.raises(RuntimeError, match="unsafe or missing INCBIN asset/root"):
        assemble(source)


def test_incbin_raw_path_matches_text_and_vasm(tmp_path):
    source = tmp_path / "source.s"
    asset = tmp_path / "raw.bin"
    asset.write_bytes(bytes([0, 255, 39, 34, 128]))
    source.write_text(' SECTION payload,data\n INCBIN "raw.bin"\n dc.b $7f\n')
    rebuilt, profile = assemble_platform_source_path_with_c_backend("amiga-raw", source)
    assert rebuilt == asset.read_bytes() + b"\x7f"
    assert profile["source_bytes"] == source.stat().st_size
    output = tmp_path / "rebuilt.bin"
    written, _ = assemble_platform_source_path_with_c_backend("amiga-raw", source, output_path=output)
    assert written == rebuilt == output.read_bytes()
    oracle = ROOT / "tools/vasmm68k_mot.exe"
    if not oracle.is_file():
        pytest.skip("vasm oracle unavailable")
    oracle_output = tmp_path / "oracle.bin"
    subprocess.run(
        [str(oracle), "-quiet", "-Fbin", "-no-opt", "-o", str(oracle_output), "source.s"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    assert rebuilt == oracle_output.read_bytes()
