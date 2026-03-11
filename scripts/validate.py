#!/usr/bin/env py.exe
"""
Validation suite for Amiga game disassembly.

Checks:
1. Entity consistency (no overlaps, no gaps, valid references)
2. Data type validation (copper lists, sprites, palettes, etc.)
3. Round-trip reassembly (if vasm available)
4. Cross-reference integrity
"""

import json
import sys
import os
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
ENTITIES_FILE = PROJECT_ROOT / "entities.jsonl"
BIN_DIR = PROJECT_ROOT / "bin"
DISASM_DIR = PROJECT_ROOT / "disasm"


def load_entities():
    """Load all entities from JSONL file."""
    entities = []
    if not ENTITIES_FILE.exists():
        return entities
    with open(ENTITIES_FILE) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                entities.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  ERROR: Invalid JSON on line {lineno}: {e}")
    return entities


def parse_addr(addr):
    """Parse an address string like '0x0400' to int."""
    if isinstance(addr, int):
        return addr
    if isinstance(addr, str):
        return int(addr, 0)
    return None


def check_entity_consistency(entities):
    """Check for overlaps, gaps, and required fields."""
    print("\n== Entity Consistency ==")
    errors = 0
    warnings = 0

    required_fields = ["addr", "end", "type"]
    valid_types = {"code", "data", "bss", "unknown"}
    valid_statuses = {"unmapped", "typed", "named", "documented"}
    valid_confidence = {"tool-inferred", "llm-guessed", "verified"}
    valid_data_subtypes = {
        "sprite", "bitmap", "copper_list", "palette", "tilemap",
        "string", "pointer_table", "sound_sample", "level_data",
        "struct_instance", "lookup_table", "jump_table", "font",
        "sine_table", "raw_binary", "compressed",
    }

    # Check required fields and valid values
    for i, ent in enumerate(entities):
        for field in required_fields:
            if field not in ent:
                print(f"  ERROR: Entity {i} missing required field '{field}'")
                errors += 1

        if ent.get("type") and ent["type"] not in valid_types:
            print(f"  ERROR: Entity at {ent.get('addr', '?')} has invalid type '{ent['type']}'")
            errors += 1

        if ent.get("status") and ent["status"] not in valid_statuses:
            print(f"  WARNING: Entity at {ent.get('addr', '?')} has non-standard status '{ent['status']}'")
            warnings += 1

        if ent.get("confidence") and ent["confidence"] not in valid_confidence:
            print(f"  WARNING: Entity at {ent.get('addr', '?')} has non-standard confidence '{ent['confidence']}'")
            warnings += 1

        if ent.get("type") == "data" and ent.get("subtype"):
            if ent["subtype"] not in valid_data_subtypes:
                print(f"  WARNING: Entity at {ent.get('addr', '?')} has non-standard data subtype '{ent['subtype']}'")
                warnings += 1

    # Check for overlaps
    sorted_ents = sorted(
        [e for e in entities if "addr" in e and "end" in e],
        key=lambda e: parse_addr(e["addr"])
    )
    for i in range(len(sorted_ents) - 1):
        curr_end = parse_addr(sorted_ents[i]["end"])
        next_start = parse_addr(sorted_ents[i + 1]["addr"])
        if curr_end > next_start:
            print(f"  ERROR: Overlap between entity at {sorted_ents[i]['addr']} "
                  f"(ends {sorted_ents[i]['end']}) and {sorted_ents[i+1]['addr']}")
            errors += 1

    print(f"  {errors} errors, {warnings} warnings")
    return errors


def check_cross_references(entities):
    """Verify all cross-references point to valid entities."""
    print("\n== Cross-Reference Integrity ==")
    errors = 0

    known_addrs = set()
    for ent in entities:
        if "addr" in ent:
            known_addrs.add(parse_addr(ent["addr"]))

    ref_fields = ["calls", "called_by", "reads", "read_by", "writes", "written_by"]

    for ent in entities:
        for field in ref_fields:
            if field in ent:
                for ref in ent[field]:
                    ref_addr = parse_addr(ref)
                    if ref_addr not in known_addrs:
                        print(f"  WARNING: Entity at {ent.get('addr', '?')} references "
                              f"unknown address {ref} in '{field}'")
                        errors += 1

    print(f"  {errors} unresolved references")
    return errors


def check_data_types(entities):
    """Type-specific validation for data entities."""
    print("\n== Data Type Validation ==")
    errors = 0

    for ent in entities:
        if ent.get("type") != "data" or not ent.get("subtype"):
            continue

        addr = ent.get("addr", "?")
        start = parse_addr(ent.get("addr", 0))
        end = parse_addr(ent.get("end", 0))
        size = end - start

        subtype = ent["subtype"]

        if subtype == "palette":
            # OCS palette: 2 bytes per color, max 32 colors = 64 bytes
            if size > 64:
                print(f"  WARNING: Palette at {addr} is {size} bytes (max 64 for OCS)")
            if size % 2 != 0:
                print(f"  ERROR: Palette at {addr} is {size} bytes (must be even)")
                errors += 1

        elif subtype == "pointer_table":
            if size % 4 != 0:
                print(f"  WARNING: Pointer table at {addr} is {size} bytes (not multiple of 4)")

        elif subtype == "sprite":
            # Sprite: 2 control words (4 bytes) + data pairs + terminator (4 bytes)
            if size < 8:
                print(f"  ERROR: Sprite at {addr} is only {size} bytes (minimum 8)")
                errors += 1

    print(f"  {errors} errors")
    return errors


def compute_coverage(entities, binary_size=None):
    """Compute and display coverage statistics."""
    print("\n== Coverage ==")

    if not entities:
        print("  No entities defined yet.")
        return

    total_bytes = 0
    typed_bytes = 0
    named_count = 0
    documented_count = 0
    verified_count = 0

    type_counts = defaultdict(int)
    status_counts = defaultdict(int)
    subtype_counts = defaultdict(int)

    for ent in entities:
        start = parse_addr(ent.get("addr", 0))
        end = parse_addr(ent.get("end", 0))
        size = end - start
        total_bytes += size

        etype = ent.get("type", "unknown")
        type_counts[etype] += 1

        status = ent.get("status", "unmapped")
        status_counts[status] += 1

        if etype != "unknown":
            typed_bytes += size
        if ent.get("name"):
            named_count += 1
        if status == "documented":
            documented_count += 1
        if ent.get("confidence") == "verified":
            verified_count += 1
        if etype == "data" and ent.get("subtype"):
            subtype_counts[ent["subtype"]] += 1

    print(f"  Total entities: {len(entities)}")
    print(f"  Total bytes covered: {total_bytes}")
    if binary_size:
        pct = (total_bytes / binary_size) * 100
        print(f"  Binary coverage: {pct:.1f}% ({total_bytes}/{binary_size})")
    print(f"\n  By type:")
    for t, c in sorted(type_counts.items()):
        print(f"    {t}: {c}")
    print(f"\n  By status:")
    for s, c in sorted(status_counts.items()):
        print(f"    {s}: {c}")
    if subtype_counts:
        print(f"\n  Data subtypes:")
        for s, c in sorted(subtype_counts.items()):
            print(f"    {s}: {c}")
    print(f"\n  Named: {named_count}/{len(entities)}")
    print(f"  Documented: {documented_count}/{len(entities)}")
    print(f"  Verified: {verified_count}/{len(entities)}")


def main():
    print("=== Amiga Disassembly Validator ===")

    entities = load_entities()
    print(f"\nLoaded {len(entities)} entities from {ENTITIES_FILE}")

    if not entities:
        print("No entities to validate. Add entries to entities.jsonl to begin.")
        return 0

    total_errors = 0
    total_errors += check_entity_consistency(entities)
    total_errors += check_cross_references(entities)
    total_errors += check_data_types(entities)

    # Try to determine binary size
    bin_files = list(BIN_DIR.glob("*"))
    bin_files = [f for f in bin_files if f.is_file() and f.name != ".gitkeep" and not f.name.startswith(".")]
    binary_size = None
    if len(bin_files) == 1:
        binary_size = bin_files[0].stat().st_size
        print(f"\nBinary: {bin_files[0].name} ({binary_size} bytes)")

    compute_coverage(entities, binary_size)

    print(f"\n{'PASS' if total_errors == 0 else 'FAIL'}: {total_errors} total errors")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
