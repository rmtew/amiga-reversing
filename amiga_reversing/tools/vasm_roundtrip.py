from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.binary_source import BinarySourceKind
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.disasm.source_rendering import (
    render_source_from_binary_source_or_raise,
)

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class VasmRoundTripResult:
    source_path: Path
    output_path: Path
    output_exists: bool
    exact_match: bool
    generated_sha256: str | None
    original_sha256: str
    first_diff_offset: int | None
    generated_size: int | None
    original_size: int
    assembler_stdout: str
    assembler_stderr: str
    assembler_returncode: int


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _first_diff_offset(lhs: bytes, rhs: bytes) -> int | None:
    limit = min(len(lhs), len(rhs))
    for index in range(limit):
        if lhs[index] != rhs[index]:
            return index
    if len(lhs) != len(rhs):
        return limit
    return None


def _vasm_executable(project_root: Path) -> Path:
    for candidate in (
        project_root / "tools" / "vasmm68k_mot.exe",
        project_root / "ext" / "vasm" / "vasmm68k_mot.exe",
    ):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("vasmm68k_mot.exe not found in tools/ or ext/vasm/")


def _vasm_format_for_source_kind(source_kind: BinarySourceKind) -> str:
    if source_kind is BinarySourceKind.HUNK_FILE:
        return "-Fhunkexe"
    if source_kind is BinarySourceKind.RAW_BINARY:
        return "-Fbin"
    raise ValueError(f"vasm round-trip target must be file-backed, got {source_kind!r}")


def _include_args(project_root: Path) -> list[str]:
    include_dir = project_root / "ext" / "amiga_includes" / "ndk_2.0" / "include"
    return [f"-I{include_dir}"] if include_dir.is_dir() else []


def roundtrip_vasm_target(target: str, *, project_root: Path = ROOT) -> VasmRoundTripResult:
    paths = resolve_project_paths(target, project_root=project_root)
    binary_source = paths.binary_source
    output_format = _vasm_format_for_source_kind(binary_source.kind)
    profile = load_assembler_profile("vasm")
    newline = "\n" if profile.render.line_ending == "lf" else "\r\n"

    with effective_metadata_file(paths.target_dir) as metadata_path:
        rendering = render_source_from_binary_source_or_raise(
            target_id=target,
            binary_source=binary_source,
            target_dir=paths.target_dir,
            metadata_path=metadata_path,
            project_root=project_root,
            workflow_id="vasm_roundtrip_source_rendering",
        )
        rendered_source = rendering.source_text

    temp_root = Path(tempfile.mkdtemp(prefix="vasm_roundtrip_"))
    try:
        source_path = temp_root / f"{target}.s"
        output_path = temp_root / Path(binary_source.display_path).name
        source_path.write_text(rendered_source, encoding="utf-8", newline=newline)
        cmd = [
            str(_vasm_executable(project_root)),
            output_format,
            "-m68000",
            "-no-opt",
            "-quiet",
            "-nosym",
            "-kick1hunks",
            *_include_args(project_root),
            "-o",
            str(output_path),
            str(source_path),
        ]
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        original_bytes = binary_source.read_bytes()
        output_exists = output_path.exists()
        generated_bytes = output_path.read_bytes() if output_exists else None
        return VasmRoundTripResult(
            source_path=source_path,
            output_path=output_path,
            output_exists=output_exists,
            exact_match=generated_bytes == original_bytes if generated_bytes is not None else False,
            generated_sha256=_sha256_bytes(generated_bytes) if generated_bytes is not None else None,
            original_sha256=_sha256_bytes(original_bytes),
            first_diff_offset=(
                _first_diff_offset(generated_bytes, original_bytes)
                if generated_bytes is not None
                else None
            ),
            generated_size=len(generated_bytes) if generated_bytes is not None else None,
            original_size=len(original_bytes),
            assembler_stdout=result.stdout,
            assembler_stderr=result.stderr,
            assembler_returncode=result.returncode,
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(description="Round-trip a target through external vasm")
    parser.add_argument("target")
    args = parser.parse_args(argv[1:])

    outcome = roundtrip_vasm_target(args.target)
    print(f"source: {outcome.source_path}")
    print(f"assembler returncode: {outcome.assembler_returncode}")
    print(f"output exists: {outcome.output_exists}")
    print(f"exact match: {outcome.exact_match}")
    print(f"original size: {outcome.original_size}")
    if outcome.generated_size is not None:
        print(f"generated size: {outcome.generated_size}")
    if outcome.first_diff_offset is not None:
        print(f"first diff offset: 0x{outcome.first_diff_offset:X}")
    if outcome.assembler_stdout.strip():
        print("assembler stdout:")
        print(outcome.assembler_stdout.strip())
    if outcome.assembler_stderr.strip():
        print("assembler stderr:")
        print(outcome.assembler_stderr.strip())
    return 0 if outcome.exact_match else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
