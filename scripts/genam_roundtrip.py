from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from disasm.assembler_profiles import load_assembler_profile
from disasm.cli import gen_disasm
from disasm.project_paths import resolve_project_paths


@dataclass(frozen=True, slots=True)
class RoundTripResult:
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_diff_offset(lhs: bytes, rhs: bytes) -> int | None:
    limit = min(len(lhs), len(rhs))
    for idx in range(limit):
        if lhs[idx] != rhs[idx]:
            return idx
    if len(lhs) != len(rhs):
        return limit
    return None


def _devpac_output_args(profile_name: str, out_name: str) -> list[str]:
    profile = load_assembler_profile(profile_name)
    if profile.render.assembler_id != "devpac":
        raise ValueError(f"round-trip assembler is not DevPac: {profile_name}")
    output_file_option = profile.output_file_option
    if output_file_option == "TO <filename>":
        return ["TO", f"TMP:{out_name}"]
    if output_file_option == "-O<filename>":
        return [f"-OTMP:{out_name}"]
    raise ValueError(f"Unsupported DevPac output_file option: {output_file_option}")


def roundtrip_genam_target(target: str) -> RoundTripResult:
    paths = resolve_project_paths(target, project_root=ROOT, require_entities=False)
    target_dir = paths.target_dir
    source_path = target_dir / f"{Path(paths.binary_source.display_path).stem}.s"
    gen_disasm(
        str(paths.binary_source.path),
        str(paths.entities_path),
        str(source_path),
        assembler_profile_name="devpac",
    )

    profile = load_assembler_profile("devpac")
    include_root = profile.local_include_root
    assert include_root is not None, "DevPac profile missing local_include_root"
    include_src = (ROOT / include_root).resolve()
    assert include_src.is_dir(), f"Missing local include root: {include_src}"

    temp_root = Path(tempfile.mkdtemp(prefix="genam_roundtrip_"))
    try:
        staged_source = temp_root / source_path.name
        shutil.copyfile(source_path, staged_source)
        staged_include = temp_root / "include"
        shutil.copytree(include_src, staged_include)
        output_name = Path(paths.binary_source.path).name
        output_path = temp_root / output_name
        cmd = [
            "vamos",
            "-V",
            f"TMP:{temp_root}",
            "--",
            "bin/GenAm",
            f"TMP:{staged_source.name}",
            *_devpac_output_args("devpac", output_name),
            "QUIET",
            "INCDIR",
            "TMP:include/",
        ]
        result = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        original_path = Path(paths.binary_source.path)
        if not original_path.is_absolute():
            original_path = (ROOT / original_path).resolve()
        original_bytes = original_path.read_bytes()
        output_exists = output_path.exists()
        generated_bytes = output_path.read_bytes() if output_exists else None
        return RoundTripResult(
            source_path=source_path,
            output_path=output_path,
            output_exists=output_exists,
            exact_match=(generated_bytes == original_bytes) if generated_bytes is not None else False,
            generated_sha256=(
                hashlib.sha256(generated_bytes).hexdigest()
                if generated_bytes is not None
                else None
            ),
            original_sha256=_sha256(original_path),
            first_diff_offset=(
                _first_diff_offset(generated_bytes, original_bytes)
                if generated_bytes is not None
                else None
            ),
            generated_size=(len(generated_bytes) if generated_bytes is not None else None),
            original_size=len(original_bytes),
            assembler_stdout=result.stdout,
            assembler_stderr=result.stderr,
            assembler_returncode=result.returncode,
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Round-trip GenAm target through real DevPac under vamos")
    parser.add_argument("target", nargs="?", default="amiga_hunk_genam")
    args = parser.parse_args(argv[1:])

    outcome = roundtrip_genam_target(args.target)
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
