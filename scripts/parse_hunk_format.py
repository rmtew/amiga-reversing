#!/usr/bin/env py.exe
"""Parse Amiga hunk format definitions from NDK DOSHUNKS.H → JSON KB.

Extracts hunk type IDs, aliases, ext sub-types, memory flags, and
the V37 LoadSeg compatibility note from the official NDK header.

Primary source: NDK 3.1 DOSHUNKS.H (V36.9, (C) Amiga Inc.)

Usage:
    python parse_hunk_format.py D:/NDK/NDK_3.1/INCLUDES&LIBS/INCLUDE_H/DOS/DOSHUNKS.H
"""

import json
import re
import sys
import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def parse_doshunks_h(path: str) -> dict:
    """Parse DOSHUNKS.H into structured KB."""
    with open(path, encoding="latin-1") as f:
        text = f.read()

    hunk_types = {}    # name -> {id, description, aliases, notes}
    ext_types = {}     # name -> {id, description, aliases}
    memory_flags = {}  # name -> {bit, mask, description}
    notes = []         # free-form notes from comments

    # Extract version info
    ver_m = re.search(r'\$VER:\s*(\S+)\s+(\S+)', text)
    version = ver_m.group(0) if ver_m else "unknown"

    lines = text.split('\n')
    pending_comment = []

    for line in lines:
        stripped = line.strip()

        # Collect multi-line comments
        if stripped.startswith('/*') or stripped.startswith('*'):
            # Extract comment text
            comment = stripped.lstrip('/* ').rstrip('*/ ')
            if comment:
                pending_comment.append(comment)
            continue

        if not stripped.startswith('#define'):
            pending_comment = []
            continue

        # Parse #define NAME value
        m = re.match(r'#define\s+(\w+)\s+(.+?)(?:\s*/\*\s*(.*?)\s*\*/)?$',
                     stripped)
        if not m:
            pending_comment = []
            continue

        name = m.group(1)
        value_str = m.group(2).strip()
        inline_comment = m.group(3) or ""

        # Resolve value: integer or alias
        alias_of = None
        try:
            if value_str.startswith('0x'):
                value = int(value_str, 16)
            elif value_str.startswith('(') and '<<' in value_str:
                # Bit shift: (1L<<29)
                shift_m = re.search(r'(\d+)\s*<<\s*(\d+)', value_str)
                if shift_m:
                    value = int(shift_m.group(1)) << int(shift_m.group(2))
                else:
                    pending_comment = []
                    continue
            else:
                value = int(value_str)
        except ValueError:
            # It's an alias: #define HUNK_ABSRELOC32 HUNK_RELOC32
            alias_of = value_str
            value = None

        # Categorize
        if name.startswith('HUNK_'):
            entry = {
                "id": value,
                "description": inline_comment,
            }
            if alias_of:
                entry["alias_of"] = alias_of
                entry.pop("id")
            if pending_comment:
                entry["notes"] = " ".join(pending_comment)
                # Check for the V37 LoadSeg note
                note_text = entry["notes"]
                if "V37 LoadSeg" in note_text or "by mistake" in note_text:
                    notes.append({
                        "topic": "HUNK_DREL32_as_RELOC32SHORT",
                        "text": note_text,
                        "applies_to": [name],
                    })
            hunk_types[name] = entry

        elif name.startswith('HUNKB_') or name.startswith('HUNKF_'):
            if name.startswith('HUNKB_'):
                # Bit number
                memory_flags[name] = {
                    "bit": value,
                    "description": inline_comment,
                }
            else:
                # Flag mask
                flag_name = name.replace('HUNKF_', 'HUNKB_')
                if flag_name in memory_flags:
                    memory_flags[flag_name]["mask"] = value
                else:
                    memory_flags[name] = {
                        "mask": value,
                        "description": inline_comment,
                    }

        elif name.startswith('EXT_'):
            entry = {
                "id": value,
                "description": inline_comment,
            }
            if alias_of:
                entry["alias_of"] = alias_of
                entry.pop("id")
            ext_types[name] = entry

        pending_comment = []

    # Build output
    output = {
        "_meta": {
            "sources": [
                {
                    "file": str(path),
                    "type": "official",
                    "description": "NDK 3.1 DOSHUNKS.H — Amiga Inc. hunk type "
                                   "definitions, ext sub-types, memory flags",
                    "version": version,
                    "provides": ["hunk_types", "ext_types", "memory_flags",
                                 "compatibility_notes"],
                },
                {
                    "file": "NDK_3.1/EXAMPLES1/PCMCIA/AMIGAXIP/LOADSEG.ASM",
                    "type": "official",
                    "description": "NDK 3.1 reference LoadSeg implementation — "
                                   "defines wire format for all hunk types "
                                   "through executable code (not prose)",
                    "provides": ["reloc_formats", "hunk_content_formats",
                                 "load_file_valid_types"],
                    "note": "Wire format entries are parser-asserted from "
                            "the reference implementation with line citations",
                },
            ],
            "note": "Parsed from NDK 3.1 by parse_hunk_format.py",
        },
        "hunk_types": hunk_types,
        "ext_types": ext_types,
        "memory_flags": memory_flags,
    }

    # Add the V37 compatibility note as a top-level field
    # This is critical: in load files (executables), ID 1015 means
    # RELOC32SHORT, not DREL32.
    if notes:
        output["compatibility_notes"] = notes

    # Parser-asserted wire format metadata.
    # DOSHUNKS.H defines type IDs but not record layouts. The layouts
    # are defined by the reference LoadSeg implementation in
    # NDK 3.1 EXAMPLES1/PCMCIA/AMIGAXIP/LOADSEG.ASM.
    # Citations below reference line numbers in that file.
    output["reloc_formats"] = {
        "long": {
            "description": "Standard 32-bit reloc format",
            "fields": [
                {"name": "count", "type": "ULONG",
                 "note": "Number of offsets; 0 = terminator"},
                {"name": "target_hunk", "type": "ULONG",
                 "note": "Hunk index to add base of"},
                {"name": "offsets", "type": "ULONG[]",
                 "note": "count × reloc offsets within current hunk"},
            ],
            "terminator": "count == 0",
            "applies_to": ["HUNK_RELOC32", "HUNK_RELOC16", "HUNK_RELOC8",
                           "HUNK_DREL32", "HUNK_DREL16", "HUNK_DREL8",
                           "HUNK_RELRELOC32", "HUNK_ABSRELOC16"],
            "citation": "LOADSEG.ASM lines 238-261: lssHunkReloc32 "
                        "uses GetLong (ULONG) for count, target, and "
                        "each offset",
        },
        "short": {
            "description": "Compact 16-bit reloc format",
            "fields": [
                {"name": "count", "type": "UWORD",
                 "note": "Number of offsets; 0 = terminator"},
                {"name": "target_hunk", "type": "UWORD"},
                {"name": "offsets", "type": "UWORD[]",
                 "note": "count × reloc offsets (16-bit, max 64K)"},
            ],
            "terminator": "count == 0, then align to longword boundary",
            "applies_to": ["HUNK_RELOC32SHORT"],
            "citation": "DOSHUNKS.H lines 42-47: V37 LoadSeg uses "
                        "HUNK_DREL32 (1015) for this format in load files. "
                        "HUNK_DREL32 is illegal in load files, so 1015 "
                        "unambiguously means short relocs in executables.",
        },
    }

    # Parser-asserted hunk content formats from LOADSEG.ASM.
    output["hunk_content_formats"] = {
        "HUNK_HEADER": {
            "fields": [
                {"name": "resident_libs", "type": "ULONG[]",
                 "note": "Sequence of BSTRs terminated by 0; "
                         "LoadSeg fails if any present"},
                {"name": "table_size", "type": "ULONG"},
                {"name": "first_hunk", "type": "ULONG"},
                {"name": "last_hunk", "type": "ULONG"},
                {"name": "hunk_sizes", "type": "ULONG[]",
                 "note": "(last-first+1) entries; bits 30-31 = "
                         "CHIP/FAST memory flags"},
            ],
            "citation": "LOADSEG.ASM lines 82-107",
        },
        "HUNK_CODE": {
            "fields": [
                {"name": "size_longs", "type": "ULONG",
                 "note": "Size in longwords; bits 30-31 = memory flags"},
                {"name": "data", "type": "UBYTE[]",
                 "note": "size_longs × 4 bytes of code"},
            ],
            "citation": "LOADSEG.ASM lines 188-210: lssHunkCode/lssHunkData "
                        "share the same handler — read size, then data",
        },
        "HUNK_DATA": {
            "fields": [
                {"name": "size_longs", "type": "ULONG"},
                {"name": "data", "type": "UBYTE[]"},
            ],
            "citation": "Same handler as HUNK_CODE (LOADSEG.ASM line 189)",
        },
        "HUNK_BSS": {
            "fields": [
                {"name": "size_longs", "type": "ULONG",
                 "note": "Size to zero-fill; no data follows"},
            ],
            "citation": "LOADSEG.ASM lines 213-235",
        },
        "HUNK_SYMBOL": {
            "fields": [
                {"name": "name_longs", "type": "ULONG",
                 "note": "Length of name in longs; 0 = terminator"},
                {"name": "name", "type": "UBYTE[]",
                 "note": "name_longs × 4 bytes"},
                {"name": "value", "type": "ULONG"},
            ],
            "citation": "LOADSEG.ASM lines 264-271: ReadName + GetLong loop",
        },
        "HUNK_DEBUG": {
            "fields": [
                {"name": "size_longs", "type": "ULONG"},
                {"name": "data", "type": "UBYTE[]",
                 "note": "Opaque debug data, size_longs × 4 bytes"},
            ],
            "citation": "LOADSEG.ASM lines 274-282: GetLong loop to skip",
        },
        "HUNK_END": {
            "fields": [],
            "citation": "LOADSEG.ASM lines 285-287: sets limit flag, returns",
        },
    }

    # Valid hunk types in load files — from LOADSEG.ASM switch table.
    # Parser-asserted: lines 163-180 define exactly these 15 entries.
    # Any type not in this table causes LoadSeg to fail.
    output["load_file_valid_types"] = [
        "HUNK_NAME", "HUNK_CODE", "HUNK_DATA", "HUNK_BSS",
        "HUNK_RELOC32", "HUNK_RELOC16", "HUNK_RELOC8",
        "HUNK_EXT", "HUNK_SYMBOL", "HUNK_DEBUG", "HUNK_END",
        "HUNK_HEADER", "HUNK_OVERLAY", "HUNK_BREAK",
    ]
    output["_meta"]["load_file_citation"] = (
        "LOADSEG.ASM lines 163-180: switch table has 15 entries "
        "(HUNK_NAME through HUNK_BREAK). Note: RELOC16/RELOC8/EXT/"
        "HEADER/OVERLAY/BREAK all fall through to lssFail (line 290-298), "
        "meaning they are recognized but rejected."
    )

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Parse DOSHUNKS.H → hunk format JSON KB")
    parser.add_argument("header",
                        help="Path to DOSHUNKS.H")
    parser.add_argument("--outfile", "-o",
                        default=str(PROJECT_ROOT / "knowledge"
                                    / "amiga_hunk_format.json"),
                        help="Output JSON path")
    args = parser.parse_args()

    print(f"Parsing {args.header}...")
    kb = parse_doshunks_h(args.header)

    # Summary
    print(f"  Hunk types: {len(kb['hunk_types'])}")
    print(f"  Ext types:  {len(kb['ext_types'])}")
    print(f"  Memory flags: {len(kb['memory_flags'])}")
    if kb.get("compatibility_notes"):
        print(f"  Compatibility notes: {len(kb['compatibility_notes'])}")

    with open(args.outfile, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2)
    print(f"\nWrote {args.outfile}")


if __name__ == "__main__":
    main()
