"""vasm assembler interface -- assemble M68K source via vasmm68k_mot."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .hunk_parser import parse_file

VASM = Path(__file__).resolve().parent.parent / "tools" / "vasmm68k_mot.exe"


def assemble(
    source: str,
    tmpdir: str | os.PathLike[str],
    cpu_flag: str = "-m68000",
    debug: bool = False,
) -> bytes | None:
    """Assemble source with vasm, return code hunk data or None on failure.

    cpu_flag: vasm -m flag (e.g. "-m68000", "-m68851")
    """
    src_path = os.path.join(tmpdir, "test.s")
    obj_path = os.path.join(tmpdir, "test.o")

    lines = []
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped.endswith(":"):
            lines.append(stripped)
        elif stripped:
            lines.append(f"    {stripped}")
    full_source = "    section code,code\n" + "\n".join(lines) + "\n"
    with open(src_path, "w") as f:
        f.write(full_source)

    result = subprocess.run(
        [str(VASM), "-Fhunk", "-no-opt", "-quiet", "-x", cpu_flag,
         "-o", obj_path, src_path],
        capture_output=True, text=True)
    if result.returncode != 0:
        if debug:
            print(f"    [vasm src]\n{full_source}")
            print(f"    [vasm stdout] {result.stdout.strip()}")
            print(f"    [vasm stderr] {result.stderr.strip()}")
        return None

    hf = parse_file(obj_path)
    if not hf.hunks:
        return None
    return hf.hunks[0].data
