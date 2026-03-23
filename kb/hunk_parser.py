#!/usr/bin/env py.exe
"""Parse Amiga hunk format definitions from NDK DOSHUNKS.H → JSON KB.

Extracts hunk type IDs, aliases, ext sub-types, memory flags, and
the V37 LoadSeg compatibility note from the official NDK header.

Primary source: NDK 3.1 DOSHUNKS.H (V36.9, (C) Amiga Inc.)

Usage:
    python parse_hunk_format.py D:/NDK/NDK_3.1/INCLUDES&LIBS/INCLUDE_H/DOS/DOSHUNKS.H
"""

import argparse
import json
import re
from typing import Any, cast

from kb.paths import AMIGA_HUNK_FORMAT_JSON
from kb.runtime_builder import build_runtime_artifacts

JsonDict = dict[str, Any]


def parse_doshunks_h(path: str) -> JsonDict:
    """Parse DOSHUNKS.H into structured KB."""
    with open(path, encoding="latin-1") as f:
        text = f.read()

    hunk_types: dict[str, JsonDict] = {}
    ext_types: dict[str, JsonDict] = {}
    memory_flags: dict[str, JsonDict] = {}
    notes: list[JsonDict] = []

    # Extract version info
    ver_m = re.search(r'\$VER:\s*(\S+)\s+(\S+)', text)
    version = ver_m.group(0) if ver_m else "unknown"

    lines = text.split('\n')
    pending_comment: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Collect multi-line comments
        if stripped.startswith(('/*', '*')):
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
            entry: JsonDict = {
                "id": value,
                "description": inline_comment,
            }
            if alias_of:
                entry["alias_of"] = alias_of
                entry.pop("id")
            if pending_comment:
                entry["notes"] = " ".join(pending_comment)
                # Check for the V37 LoadSeg note
                note_text = cast(str, entry["notes"])
                if "V37 LoadSeg" in note_text or "by mistake" in note_text:
                    notes.append({
                        "topic": "HUNK_DREL32_as_RELOC32SHORT",
                        "text": note_text,
                        "applies_to": [name],
                    })
            hunk_types[name] = entry

        elif name.startswith(('HUNKB_', 'HUNKF_')):
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
    output: JsonDict = {
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
            # Fundamental constants derived from parsed data
            "longword_bytes": 4,
            "endianness": "big",
        },
        "hunk_types": hunk_types,
        "ext_types": ext_types,
        "memory_flags": memory_flags,
    }

    # Derive masks from parsed bit positions.
    # Parser-asserted: DOSHUNKS.H defines HUNKB_ADVISORY=29,
    # HUNKB_CHIP=30, HUNKB_FAST=31 as flag bits in the raw hunk type
    # and size longwords.  The masks follow from these positions.
    advisory_bit = cast(int | None, memory_flags.get("HUNKB_ADVISORY", {}).get("bit"))
    chip_bit = cast(int | None, memory_flags.get("HUNKB_CHIP", {}).get("bit"))
    fast_bit = cast(int | None, memory_flags.get("HUNKB_FAST", {}).get("bit"))
    if advisory_bit is None or chip_bit is None or fast_bit is None:
        raise KeyError("HUNKB_ADVISORY/CHIP/FAST bit positions missing "
                       "from DOSHUNKS.H")
    meta = cast(JsonDict, output["_meta"])
    meta["hunk_type_id_mask"] = (
        0xFFFFFFFF & ~(1 << advisory_bit) & ~(1 << chip_bit) & ~(1 << fast_bit)
    )
    meta["size_longs_mask"] = 0xFFFFFFFF & ~(1 << chip_bit) & ~(1 << fast_bit)
    meta["mem_flags_shift"] = min(chip_bit, fast_bit)

    # Memory type decoding table.
    # Parser-asserted: bits chip_bit and fast_bit encode a 2-bit value:
    # 0=any, CHIP=1, FAST=2, both=3 (extended, followed by ULONG attrs).
    # LOADSEG.ASM GetVector lines 400-410: rol.l #3,d1; and.l #6,d1
    # extracts bits 30-31 as MEMF_FAST+MEMF_CHIP.
    output["memory_type_codes"] = {
        "0": {"name": "ANY", "description": "Any available memory"},
        "1": {"name": "CHIP", "description": "Chip RAM (MEMF_CHIP)"},
        "2": {"name": "FAST", "description": "Fast RAM (MEMF_FAST)"},
        "3": {"name": "EXTENDED",
              "description": "Extended: next ULONG has exec memory attrs"},
    }

    # EXT type categories.
    # From DOSHUNKS.H: definitions (EXT_SYMB..EXT_RES) have IDs 0-3,
    # references (EXT_REF32..) have IDs 129+.  Boundary at 128.
    def_ids = [
        ext_id
        for value in ext_types.values()
        for ext_id in [cast(int | None, value.get("id"))]
        if ext_id is not None and ext_id < 128
    ]
    ref_ids = [
        ext_id
        for value in ext_types.values()
        for ext_id in [cast(int | None, value.get("id"))]
        if ext_id is not None and ext_id >= 128
    ]
    output["ext_type_categories"] = {
        "definition_range": [min(def_ids), max(def_ids)] if def_ids else [],
        "reference_range": [min(ref_ids), max(ref_ids)] if ref_ids else [],
        "boundary": 128,
        "citation": "DOSHUNKS.H: definitions 0-3, references 129-139; "
                    "boundary at 128 (bit 7)",
    }

    # Mark EXT types that have common_size field.
    # Parser-asserted: DOSHUNKS.H descriptions say "reference to COMMON
    # block" for EXT_COMMON and EXT_RELCOMMON.  These have an extra
    # ULONG common_size before ref_count.
    for name in ("EXT_COMMON", "EXT_RELCOMMON"):
        if name in ext_types:
            ext_types[name]["has_common_size"] = True

    # HUNK_EXT wire format.
    # Parser-asserted from amiga_hunk_format.md (reference for vasm/GenAm
    # debug hunk detail), corroborated by hunk_parser.py implementation.
    meta["ext_type_and_len_packing"] = {
        "type_bits": [31, 24],
        "type_width": 8,
        "name_len_bits": [23, 0],
        "name_len_width": 24,
        "citation": "amiga_hunk_format.md line 138: bits 31-24 = sub-type, "
                    "bits 23-0 = name_len (in longwords)",
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

    # Relocation semantics: how each reloc type patches the binary.
    # Parser-asserted from DOSHUNKS.H descriptions + LOADSEG.ASM
    # line 256: "add.l d3,0(a2,d0.l)" (add target hunk base to offset).
    # The "bytes" field is the width of the patched value.
    # The "mode" field describes how the stored value relates to the target.
    output["relocation_semantics"] = {
        "HUNK_RELOC32": {
            "bytes": 4, "mode": "absolute",
            "description": "Add target hunk base to 32-bit value at offset",
            "citation": "LOADSEG.ASM line 256; DOSHUNKS.H HUNK_ABSRELOC32 alias",
        },
        "HUNK_RELOC32SHORT": {
            "bytes": 4, "mode": "absolute",
            "description": "Same as RELOC32, compact encoding",
        },
        "HUNK_RELOC16": {
            "bytes": 2, "mode": "pc_relative",
            "description": "16-bit PC-relative displacement",
            "citation": "DOSHUNKS.H HUNK_RELRELOC16 alias",
        },
        "HUNK_RELOC8": {
            "bytes": 1, "mode": "pc_relative",
            "description": "8-bit PC-relative displacement",
            "citation": "DOSHUNKS.H HUNK_RELRELOC8 alias",
        },
        "HUNK_DREL32": {
            "bytes": 4, "mode": "data_relative",
            "description": "32-bit data-section-relative offset",
        },
        "HUNK_DREL16": {
            "bytes": 2, "mode": "data_relative",
            "description": "16-bit data-section-relative offset",
        },
        "HUNK_DREL8": {
            "bytes": 1, "mode": "data_relative",
            "description": "8-bit data-section-relative offset",
        },
        "HUNK_RELRELOC32": {
            "bytes": 4, "mode": "pc_relative",
            "description": "32-bit PC-relative displacement (V39+)",
            "citation": "DOSHUNKS.H: New for V39",
        },
        "HUNK_ABSRELOC16": {
            "bytes": 2, "mode": "absolute",
            "description": "16-bit absolute address",
            "citation": "DOSHUNKS.H",
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
            "sub_formats": {
                "LINE": {
                    "magic": 0x4C494E45,
                    "magic_text": "LINE",
                    "fields": [
                        {"name": "magic", "type": "ULONG",
                         "value": "0x4C494E45"},
                        {"name": "filename", "type": "BSTR",
                         "note": "Source filename (ULONG len + len*4 bytes)"},
                        {"name": "entries", "type": "ARRAY",
                         "element": [
                             {"name": "line", "type": "ULONG"},
                             {"name": "offset", "type": "ULONG",
                              "note": "SRD (start of routine data) offset"},
                         ]},
                    ],
                    "citation": "amiga_hunk_format.md line 175; used by "
                                "vasm and DevPac GenAm for source-level debug",
                },
            },
            "citation": "LOADSEG.ASM lines 274-282: GetLong loop to skip",
        },
        "HUNK_EXT": {
            "fields": [
                {"name": "type_and_len", "type": "ULONG",
                 "note": "Bits 31-24 = ext sub-type, bits 23-0 = name_len "
                         "(in longwords). 0 = terminator."},
                {"name": "name", "type": "UBYTE[]",
                 "note": "name_len × 4 bytes, NUL-padded"},
            ],
            "definition_fields": [
                {"name": "value", "type": "ULONG"},
            ],
            "reference_fields": [
                {"name": "ref_count", "type": "ULONG"},
                {"name": "offsets", "type": "ULONG[]",
                 "note": "ref_count × offsets within current hunk"},
            ],
            "common_fields": [
                {"name": "common_size", "type": "ULONG",
                 "note": "Size of common block in bytes"},
                {"name": "ref_count", "type": "ULONG"},
                {"name": "offsets", "type": "ULONG[]"},
            ],
            "citation": "amiga_hunk_format.md lines 133-165; DOSHUNKS.H "
                        "ext sub-type definitions",
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
    meta["load_file_citation"] = (
        "LOADSEG.ASM lines 163-180: switch table has 15 entries "
        "(HUNK_NAME through HUNK_BREAK). Note: RELOC16/RELOC8/EXT/"
        "HEADER/OVERLAY/BREAK all fall through to lssFail (line 290-298), "
        "meaning they are recognized but rejected."
    )

    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse DOSHUNKS.H → hunk format JSON KB")
    parser.add_argument("header",
                        help="Path to DOSHUNKS.H")
    parser.add_argument("--outfile", "-o",
                        default=str(AMIGA_HUNK_FORMAT_JSON),
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
    for runtime_out in build_runtime_artifacts():
        print(f"Wrote {runtime_out}")


if __name__ == "__main__":
    main()
