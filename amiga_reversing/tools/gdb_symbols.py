"""Generate disposable M68K ELF/DWARF symbols from canonical analysis facts.

The artifact is deliberately a debugger-side description only: it contains no
target bytes and is generated into a session state directory.  A function is
eligible only when an accepted manual name is exactly the start of one accepted
contiguous code run.  This makes its extent an analysis fact, rather than an
inference from rendered assembly or the next label.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.disasm.c_backend import build_project_listing_artifact_profile
from amiga_reversing.disasm.function_facts import canonical_function_facts


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


def _eligible_functions(target_id: str, artifact: object) -> tuple[dict[str, int], tuple[FunctionSymbol, ...]]:
    analysis, _ = artifact.analysis_payload()
    sections = analysis.get("sections")
    if not isinstance(sections, list) or not sections or not isinstance(sections[0], dict):
        raise ValueError("Canonical analysis has no primary section for GDB symbols.")
    view = _single_runtime_view(artifact)
    facts = canonical_function_facts(target_id, analysis, view).get("functions")
    if not isinstance(facts, list):
        raise ValueError("Canonical analysis has no function facts for GDB symbols.")
    functions, _ = _gdb_eligible_facts(facts)
    functions.sort(key=lambda item: (item.source_start, item.name))
    if not functions:
        raise ValueError("Canonical analysis has no accepted named function ranges for GDB symbols.")
    return view, tuple(functions)


def _gdb_eligible_facts(facts: list[object]) -> tuple[list[FunctionSymbol], list[dict[str, object]]]:
    """Select fact ranges the ELF symbol table can represent exactly."""

    functions: list[FunctionSymbol] = []
    omitted: list[dict[str, object]] = []
    for item in facts:
        if not isinstance(item, dict):
            raise ValueError("Canonical function facts contain a malformed entry.")
        name = item.get("name")
        entry = item.get("entry_offset")
        if not isinstance(name, str) or not isinstance(entry, int):
            raise ValueError("Canonical function fact has no named entry offset.")
        if item.get("status") != "accepted":
            omitted.append({"name": name, "entry_offset": entry, "reason": item.get("reason")})
            continue
        ranges = item.get("ranges")
        if not isinstance(ranges, list) or len(ranges) != 1:
            omitted.append({"name": name, "entry_offset": entry, "reason": "noncontiguous_function_ranges"})
            continue
        only_range = ranges[0]
        if not isinstance(only_range, dict) or not isinstance(only_range.get("start_offset"), int) or not isinstance(only_range.get("end_offset"), int):
            raise ValueError("Accepted function fact has an invalid range.")
        start, end = int(only_range["start_offset"]), int(only_range["end_offset"])
        if start != entry:
            omitted.append({"name": name, "entry_offset": entry, "reason": "range_does_not_begin_at_entry"})
            continue
        if end <= start:
            raise ValueError("Accepted function fact has an empty range.")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            omitted.append({"name": name, "entry_offset": entry, "reason": "invalid_symbol_name"})
            continue
        functions.append(FunctionSymbol(name, start, end))
    return functions, omitted


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


def generate_gdb_symbol_artifact(
    target_id: str, state_directory: Path, *, artifact: object | None = None
) -> GdbSymbolArtifact:
    """Build one disposable, relocatable 68K ELF/DWARF artifact for a target."""

    owns_artifact = artifact is None
    if artifact is None:
        _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        view, functions = _eligible_functions(target_id, artifact)
    finally:
        if owns_artifact:
            artifact.close()
    state_directory.mkdir(parents=True, exist_ok=True)
    elf_path = state_directory / "canonical-gdb-symbols.elf"
    elf_path.write_bytes(_elf_bytes(functions))
    return GdbSymbolArtifact(elf_path, view, functions)


def symbol_coverage_report(target_id: str) -> dict[str, object]:
    """Report canonical symbol eligibility without creating an artifact."""

    _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        analysis, _ = artifact.analysis_payload()
        view = _single_runtime_view(artifact)
        facts = canonical_function_facts(target_id, analysis, view)["functions"]
    finally:
        artifact.close()
    emitted_functions, omitted = _gdb_eligible_facts(facts)
    emitted = [
        {
            "name": item.name,
            "source_start": item.source_start,
            "source_end": item.source_end,
            "range_count": 1,
        }
        for item in emitted_functions
    ]
    return {
        "target_id": target_id,
        "runtime_view": view,
        "counts": {"emitted": len(emitted), "omitted": len(omitted)},
        "emitted": emitted,
        "omitted": omitted,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(symbol_coverage_report(args.target), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
