"""Generate disposable M68K ELF/DWARF symbols from canonical analysis facts.

The artifact is deliberately a debugger-side description only: it contains no
target bytes and is generated into a session state directory.  A function is
eligible only when an accepted manual name is exactly the start of one accepted
contiguous code run.  This makes its extent an analysis fact, rather than an
inference from rendered assembly or the next label.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.disasm.c_backend import build_project_listing_artifact_profile

ROOT = Path(__file__).resolve().parents[2]
M68K_AS = ROOT / "resources" / "clone_amiga" / "vscode-amiga-debug" / "bin" / "win32" / "opt" / "bin" / "m68k-amiga-elf-as.exe"
M68K_LD = ROOT / "resources" / "clone_amiga" / "vscode-amiga-debug" / "bin" / "win32" / "opt" / "bin" / "m68k-amiga-elf-ld.exe"


@dataclass(frozen=True, slots=True)
class FunctionSymbol:
    name: str
    source_start: int
    source_end: int


@dataclass(frozen=True, slots=True)
class GdbSymbolArtifact:
    elf_path: Path
    source_path: Path
    object_path: Path
    runtime_view: dict[str, int]
    functions: tuple[FunctionSymbol, ...]

    def scenario_payload(self) -> dict[str, object]:
        return {
            "elf_path": str(self.elf_path),
            "runtime_view": dict(self.runtime_view),
            "functions": [
                {"name": item.name, "source_start": item.source_start, "source_end": item.source_end}
                for item in self.functions
            ],
        }


def _single_runtime_view(artifact: object) -> dict[str, int]:
    views = getattr(artifact, "_runtime_observation_views", ())
    valid = [
        view for view in views
        if isinstance(view, dict)
        and all(isinstance(view.get(key), int) for key in ("base_addr", "source_start", "source_end"))
    ]
    if len(valid) != 1:
        raise ValueError("GDB symbols require exactly one confirmed runtime observation view.")
    return {key: int(valid[0][key]) for key in ("base_addr", "source_start", "source_end")}


def _eligible_functions(target_id: str, artifact: object) -> tuple[dict[str, int], tuple[FunctionSymbol, ...]]:
    analysis, _ = artifact.analysis_payload()
    sections = analysis.get("sections")
    if not isinstance(sections, list) or not sections or not isinstance(sections[0], dict):
        raise ValueError("Canonical analysis has no primary section for GDB symbols.")
    accepted_runs = sections[0].get("accepted_code_runs")
    if not isinstance(accepted_runs, list):
        raise ValueError("Canonical analysis has no accepted code runs for GDB symbols.")
    view = _single_runtime_view(artifact)
    runs = {
        (item.get("start_offset"), item.get("end_offset"))
        for item in accepted_runs
        if isinstance(item, dict)
        and isinstance(item.get("start_offset"), int)
        and isinstance(item.get("end_offset"), int)
        and int(item["start_offset"]) < int(item["end_offset"])
    }
    symbol_origins = sections[0].get("symbol_origins")
    if not isinstance(symbol_origins, list):
        raise ValueError("Canonical analysis has no symbol origins for GDB symbols.")
    labels = [
        {"name": item.get("symbol_name"), "source_start": item.get("offset")}
        for item in symbol_origins
        if isinstance(item, dict) and item.get("origin_kind") == "manual_label"
    ]
    name_counts: dict[str, int] = {}
    for label in labels:
        name = label.get("name")
        if isinstance(name, str):
            name_counts[name] = name_counts.get(name, 0) + 1
    functions: list[FunctionSymbol] = []
    for label in labels:
        name = label.get("name")
        source_start = label.get("source_start")
        if not isinstance(name, str) or name_counts.get(name) != 1 or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or not isinstance(source_start, int):
            continue
        matching = [end for start, end in runs if start == source_start]
        if len(matching) != 1:
            continue
        functions.append(FunctionSymbol(name, source_start, matching[0]))
    functions.sort(key=lambda item: (item.source_start, item.name))
    if not functions:
        raise ValueError("Canonical analysis has no accepted named function ranges for GDB symbols.")
    return view, tuple(functions)


def _assembly_text(functions: tuple[FunctionSymbol, ...]) -> str:
    lines = ['.file 1 "canonical-analysis"', ".text"]
    cursor = 0
    for item in functions:
        if item.source_start < cursor:
            raise ValueError(f"Overlapping accepted function range: {item.name}")
        lines.extend((
            f".org 0x{item.source_start:x}",
            f".globl {item.name}",
            f".type {item.name}, @function",
            f"{item.name}:",
            ".loc 1 1 0",
            f".space 0x{item.source_end - item.source_start:x}",
            f".size {item.name}, .-{item.name}",
        ))
        cursor = item.source_end
    return "\n".join(lines) + "\n"


def generate_gdb_symbol_artifact(target_id: str, state_directory: Path) -> GdbSymbolArtifact:
    """Build one disposable, relocatable 68K ELF/DWARF artifact for a target."""

    if not M68K_AS.is_file() or not M68K_LD.is_file():
        raise RuntimeError("The local vscode-amiga-debug M68K assembler/linker is required for GDB symbol generation.")
    _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        view, functions = _eligible_functions(target_id, artifact)
    finally:
        artifact.close()
    state_directory.mkdir(parents=True, exist_ok=True)
    source_path = state_directory / "canonical-gdb-symbols.s"
    object_path = state_directory / "canonical-gdb-symbols.o"
    elf_path = state_directory / "canonical-gdb-symbols.elf"
    source_path.write_text(_assembly_text(functions), encoding="ascii")
    subprocess.run([str(M68K_AS), "--gdwarf-2", "-m68000", "-o", str(object_path), str(source_path)], check=True, capture_output=True, text=True)
    subprocess.run([str(M68K_LD), "-m", "m68kelf", "-Ttext", "0", "-o", str(elf_path), str(object_path)], check=True, capture_output=True, text=True)
    return GdbSymbolArtifact(elf_path, source_path, object_path, view, functions)
