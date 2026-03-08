#!/usr/bin/env python3
"""
Entity management tools for the disassembly project.

Usage:
    python entity_tools.py add <addr> <end> <type> [--subtype X] [--name X] [--status X]
    python entity_tools.py update <addr> [--name X] [--status X] [--confidence X] [--subtype X]
    python entity_tools.py add-xref <from_addr> <to_addr> <ref_type>
    python entity_tools.py show <addr>
    python entity_tools.py list [--type X] [--status X] [--unnamed]
    python entity_tools.py gaps [--binary-size N]
    python entity_tools.py graph [--output dot|text]

ref_type: calls, reads, writes
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
ENTITIES_FILE = PROJECT_ROOT / "entities.jsonl"


def parse_addr(addr):
    if isinstance(addr, int):
        return addr
    return int(addr, 0)


def fmt_addr(addr):
    if isinstance(addr, str):
        return addr
    return f"0x{addr:04X}"


def load_entities():
    entities = []
    if ENTITIES_FILE.exists():
        with open(ENTITIES_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        entities.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entities


def save_entities(entities):
    with open(ENTITIES_FILE, "w") as f:
        for ent in entities:
            f.write(json.dumps(ent, separators=(",", ":")) + "\n")


def find_entity(entities, addr):
    target = parse_addr(addr)
    for i, ent in enumerate(entities):
        if parse_addr(ent.get("addr", -1)) == target:
            return i, ent
    return None, None


def cmd_add(args):
    entities = load_entities()
    addr = fmt_addr(parse_addr(args.addr))
    end = fmt_addr(parse_addr(args.end))

    # Check for overlap
    idx, existing = find_entity(entities, args.addr)
    if existing:
        print(f"Entity already exists at {addr}. Use 'update' instead.")
        return 1

    ent = {
        "addr": addr,
        "end": end,
        "type": args.type,
        "status": args.status or "unmapped",
    }
    if args.subtype:
        ent["subtype"] = args.subtype
    if args.name:
        ent["name"] = args.name
        if not args.status:
            ent["status"] = "named"
    if args.confidence:
        ent["confidence"] = args.confidence
    if args.notes:
        ent["notes"] = args.notes

    entities.append(ent)
    # Sort by address
    entities.sort(key=lambda e: parse_addr(e.get("addr", 0)))
    save_entities(entities)
    print(f"Added {args.type} entity at {addr}–{end}")
    return 0


def cmd_update(args):
    entities = load_entities()
    idx, ent = find_entity(entities, args.addr)
    if ent is None:
        print(f"No entity at {args.addr}")
        return 1

    changed = []
    for field in ["name", "status", "confidence", "subtype", "notes"]:
        val = getattr(args, field, None)
        if val is not None:
            ent[field] = val
            changed.append(f"{field}={val}")

    if not changed:
        print("Nothing to update. Specify at least one field.")
        return 1

    entities[idx] = ent
    save_entities(entities)
    print(f"Updated entity at {ent['addr']}: {', '.join(changed)}")
    return 0


def cmd_add_xref(args):
    entities = load_entities()
    from_idx, from_ent = find_entity(entities, args.from_addr)
    to_idx, to_ent = find_entity(entities, args.to_addr)

    if from_ent is None:
        print(f"No entity at {args.from_addr}")
        return 1
    if to_ent is None:
        print(f"No entity at {args.to_addr} (creating forward reference anyway)")

    # Forward reference
    ref_type = args.ref_type  # calls, reads, writes
    if ref_type not in ("calls", "reads", "writes"):
        print(f"Invalid ref_type: {ref_type}. Use: calls, reads, writes")
        return 1

    to_addr = fmt_addr(parse_addr(args.to_addr))

    if ref_type not in from_ent:
        from_ent[ref_type] = []
    if to_addr not in from_ent[ref_type]:
        from_ent[ref_type].append(to_addr)
    entities[from_idx] = from_ent

    # Reverse reference
    if to_ent is not None:
        reverse = {"calls": "called_by", "reads": "read_by", "writes": "written_by"}
        rev_type = reverse[ref_type]
        from_addr = fmt_addr(parse_addr(args.from_addr))
        if rev_type not in to_ent:
            to_ent[rev_type] = []
        if from_addr not in to_ent[rev_type]:
            to_ent[rev_type].append(from_addr)
        entities[to_idx] = to_ent

    save_entities(entities)
    print(f"Added xref: {from_ent.get('addr')} --{ref_type}--> {to_addr}")
    return 0


def cmd_show(args):
    entities = load_entities()
    idx, ent = find_entity(entities, args.addr)
    if ent is None:
        print(f"No entity at {args.addr}")
        return 1
    print(json.dumps(ent, indent=2))
    return 0


def cmd_list(args):
    entities = load_entities()
    filtered = entities

    if args.type:
        filtered = [e for e in filtered if e.get("type") == args.type]
    if args.status:
        filtered = [e for e in filtered if e.get("status") == args.status]
    if args.unnamed:
        filtered = [e for e in filtered if not e.get("name")]

    for ent in filtered:
        addr = ent.get("addr", "?")
        end = ent.get("end", "?")
        etype = ent.get("type", "?")
        name = ent.get("name", "")
        status = ent.get("status", "unmapped")
        subtype = ent.get("subtype", "")
        sub_str = f" ({subtype})" if subtype else ""
        print(f"  {addr}–{end}  {etype}{sub_str:20s}  [{status:11s}]  {name}")

    print(f"\n{len(filtered)} entities")
    return 0


def cmd_gaps(args):
    entities = load_entities()
    if not entities:
        print("No entities defined.")
        return 0

    sorted_ents = sorted(entities, key=lambda e: parse_addr(e.get("addr", 0)))
    binary_size = args.binary_size

    gaps = []
    # Gap before first entity
    first_start = parse_addr(sorted_ents[0]["addr"])
    if first_start > 0:
        gaps.append((0, first_start))

    # Gaps between entities
    for i in range(len(sorted_ents) - 1):
        curr_end = parse_addr(sorted_ents[i]["end"])
        next_start = parse_addr(sorted_ents[i + 1]["addr"])
        if next_start > curr_end:
            gaps.append((curr_end, next_start))

    # Gap after last entity
    if binary_size:
        last_end = parse_addr(sorted_ents[-1]["end"])
        if last_end < binary_size:
            gaps.append((last_end, binary_size))

    if not gaps:
        print("No gaps found!")
    else:
        total_gap = 0
        for start, end in gaps:
            size = end - start
            total_gap += size
            print(f"  {fmt_addr(start)}–{fmt_addr(end)}  ({size} bytes)")
        print(f"\n{len(gaps)} gaps, {total_gap} bytes total")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Entity management tools")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="Add a new entity")
    p_add.add_argument("addr", help="Start address (hex, e.g. 0x400)")
    p_add.add_argument("end", help="End address (hex)")
    p_add.add_argument("type", choices=["code", "data", "bss", "unknown"])
    p_add.add_argument("--subtype", help="Data subtype")
    p_add.add_argument("--name", help="Symbol name")
    p_add.add_argument("--status", help="Status (unmapped/typed/named/documented)")
    p_add.add_argument("--confidence", help="Confidence level")
    p_add.add_argument("--notes", help="Notes")

    p_upd = sub.add_parser("update", help="Update an entity")
    p_upd.add_argument("addr", help="Entity address")
    p_upd.add_argument("--name")
    p_upd.add_argument("--status")
    p_upd.add_argument("--confidence")
    p_upd.add_argument("--subtype")
    p_upd.add_argument("--notes")

    p_xref = sub.add_parser("add-xref", help="Add cross-reference")
    p_xref.add_argument("from_addr")
    p_xref.add_argument("to_addr")
    p_xref.add_argument("ref_type", choices=["calls", "reads", "writes"])

    p_show = sub.add_parser("show", help="Show entity details")
    p_show.add_argument("addr")

    p_list = sub.add_parser("list", help="List entities")
    p_list.add_argument("--type")
    p_list.add_argument("--status")
    p_list.add_argument("--unnamed", action="store_true")

    p_gaps = sub.add_parser("gaps", help="Find unmapped address gaps")
    p_gaps.add_argument("--binary-size", type=lambda x: int(x, 0))

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    cmd_map = {
        "add": cmd_add,
        "update": cmd_update,
        "add-xref": cmd_add_xref,
        "show": cmd_show,
        "list": cmd_list,
        "gaps": cmd_gaps,
    }
    return cmd_map[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
