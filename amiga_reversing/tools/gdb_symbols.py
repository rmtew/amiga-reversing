"""Generate disposable M68K ELF/DWARF symbols from canonical analysis facts.

The artifact is deliberately a debugger-side description only: it contains no
target bytes and is generated into a session state directory.  A function is
eligible only when an accepted manual name is exactly the start of one accepted
contiguous code run.  This makes its extent an analysis fact, rather than an
inference from rendered assembly or the next label.
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.disasm.c_backend import build_project_listing_artifact_profile
from amiga_reversing.disasm.manual_actions import load_manual_projection
from amiga_reversing.disasm.project_paths import resolve_project_paths

@dataclass(frozen=True, slots=True)
class FunctionSymbol:
    name: str
    source_start: int
    source_end: int


@dataclass(frozen=True, slots=True)
class GdbSymbolArtifact:
    elf_path: Path
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


def _canonical_labels(target_id: str, view: dict[str, int]) -> list[dict[str, object]]:
    projection = load_manual_projection(resolve_project_paths(target_id).target_dir)
    return [
        {
            "name": item.get("name"),
            "source_start": (
                int(item["addr"]) - view["base_addr"] + view["source_start"]
                if item.get("address_domain") == "runtime" and isinstance(item.get("addr"), int)
                else None
            ),
        }
        for item in projection.labels
    ]


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
    labels = _canonical_labels(target_id, view)
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


def _uleb128(value: int) -> bytes:
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        result.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(result)


def _string_table(strings: list[str]) -> tuple[bytes, dict[str, int]]:
    data = bytearray(b"\0")
    offsets: dict[str, int] = {}
    for value in strings:
        offsets[value] = len(data)
        data.extend(value.encode("ascii") + b"\0")
    return bytes(data), offsets


def _dwarf_sections(functions: tuple[FunctionSymbol, ...]) -> tuple[bytes, bytes, bytes]:
    """Return DWARF v2 abbrev, info, and string sections for the symbols."""

    strings, offsets = _string_table(["canonical-analysis", *[item.name for item in functions]])
    # CU(name, language, low_pc, high_pc), then subprogram(name, low_pc, high_pc).
    abbrev = bytes((
        1, 0x11, 1, 0x03, 0x0E, 0x13, 0x05, 0x11, 0x01, 0x12, 0x01, 0, 0,
        2, 0x2E, 0, 0x03, 0x0E, 0x11, 0x01, 0x12, 0x01, 0, 0, 0,
    ))
    highest = max(item.source_end for item in functions)
    dies = bytearray(_uleb128(1))
    dies.extend(struct.pack(">I", offsets["canonical-analysis"]))
    dies.extend(struct.pack(">HII", 0x8001, 0, highest))  # DW_LANG_Mips_Assembler, address range.
    for item in functions:
        dies.extend(_uleb128(2))
        dies.extend(struct.pack(">III", offsets[item.name], item.source_start, item.source_end))
    dies.append(0)
    info_body = struct.pack(">H I B", 2, 0, 4) + dies
    return abbrev, struct.pack(">I", len(info_body)) + info_body, strings


def _align(data: bytearray, alignment: int) -> None:
    data.extend(b"\0" * ((-len(data)) % alignment))


def _elf_bytes(functions: tuple[FunctionSymbol, ...]) -> bytes:
    """Build a self-contained ELF32 big-endian MC68000 symbol object.

    Synthetic zero-filled .text reserves addresses for debugger relocation; it
    is metadata only and is never written to the target.
    """

    text_size = max(item.source_end for item in functions)
    symbol_strings, symbol_offsets = _string_table([item.name for item in functions])
    symbols = bytearray(16)
    for item in functions:
        symbols.extend(struct.pack(">IIIBBH", symbol_offsets[item.name], item.source_start, item.source_end - item.source_start, 0x12, 0, 1))
    abbrev, info, debug_strings = _dwarf_sections(functions)
    names = [".text", ".symtab", ".strtab", ".debug_abbrev", ".debug_info", ".debug_str", ".shstrtab"]
    shstr, shname = _string_table(names)
    sections = [
        (".text", 1, 0x6, 0, b"\0" * text_size, 4, 0, 0),
        (".symtab", 2, 0, 0, bytes(symbols), 4, 3, 16),
        (".strtab", 3, 0, 0, symbol_strings, 1, 0, 0),
        (".debug_abbrev", 1, 0, 0, abbrev, 1, 0, 0),
        (".debug_info", 1, 0, 0, info, 1, 0, 0),
        (".debug_str", 1, 0, 0, debug_strings, 1, 0, 0),
        (".shstrtab", 3, 0, 0, shstr, 1, 0, 0),
    ]
    data = bytearray(52)
    headers = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)]
    for name, kind, flags, address, contents, alignment, link, entry_size in sections:
        _align(data, alignment)
        offset = len(data)
        data.extend(contents)
        headers.append((shname[name], kind, flags, address, offset, len(contents), link, 0, alignment, entry_size))
    _align(data, 4)
    section_header_offset = len(data)
    for header in headers:
        data.extend(struct.pack(">IIIIIIIIII", *header))
    data[:52] = struct.pack(">16sHHIIIIIHHHHHH", b"\x7fELF\x01\x02\x01" + b"\0" * 9, 2, 4, 1, 0, 0, section_header_offset, 0, 52, 0, 0, 40, len(headers), 7)
    return bytes(data)


def generate_gdb_symbol_artifact(target_id: str, state_directory: Path) -> GdbSymbolArtifact:
    """Build one disposable, relocatable 68K ELF/DWARF artifact for a target."""

    _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        view, functions = _eligible_functions(target_id, artifact)
    finally:
        artifact.close()
    state_directory.mkdir(parents=True, exist_ok=True)
    elf_path = state_directory / "canonical-gdb-symbols.elf"
    elf_path.write_bytes(_elf_bytes(functions))
    return GdbSymbolArtifact(elf_path, view, functions)
