#!/usr/bin/env py.exe
"""Build entities.jsonl from hunk binary analysis.

Parses an Amiga hunk executable, runs the symbolic executor on CODE hunks,
and generates entities with bidirectional cross-references.

Entity granularity: subroutine-level for code (not basic-block-level).
Uncovered regions between subroutines are marked as 'unknown'.

Usage:
    python build_entities.py <binary_path> [--output entities.jsonl]
    python build_entities.py resources/Amiga_Devpac_3_18/GenAm
"""

import json
import struct
import sys
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hunk_parser import parse_file, HunkType
from m68k_executor import analyze, BasicBlock, _load_kb
from jump_tables import detect_jump_tables, resolve_indirect_targets
from os_calls import load_os_kb, get_platform_config, identify_library_calls


PROJECT_ROOT = Path(__file__).parent.parent

# Relocation type metadata (from Amiga hunk format spec):
# - bytes: width of the stored value at the reloc offset
# - mode: how the stored value relates to the target address
#   "absolute"     — stored value = target offset (loader adds hunk base)
#   "pc_relative"  — stored value = target - offset (PC-relative displacement)
#   "data_relative"— stored value = target - data_section_base
_RELOC_INFO = {
    HunkType.HUNK_RELOC32:      {"bytes": 4, "mode": "absolute"},
    HunkType.HUNK_RELOC32SHORT: {"bytes": 4, "mode": "absolute"},
    HunkType.HUNK_ABSRELOC16:   {"bytes": 2, "mode": "absolute"},
    HunkType.HUNK_RELOC16:      {"bytes": 2, "mode": "pc_relative"},
    HunkType.HUNK_RELOC8:       {"bytes": 1, "mode": "pc_relative"},
    HunkType.HUNK_RELRELOC32:   {"bytes": 4, "mode": "pc_relative"},
    HunkType.HUNK_DREL32:       {"bytes": 4, "mode": "data_relative"},
    HunkType.HUNK_DREL16:       {"bytes": 2, "mode": "data_relative"},
    HunkType.HUNK_DREL8:        {"bytes": 1, "mode": "data_relative"},
}

# struct format strings by byte width (big-endian, signed for relative)
_RELOC_ABS_FMT = {4: ">I", 2: ">H"}
_RELOC_REL_FMT = {4: ">i", 2: ">h", 1: ">b"}


def _resolve_reloc_target(reloc, offset: int, data: bytes) -> int | None:
    """Resolve a relocation offset to its target address.

    Returns the absolute target offset within the hunk, or None if the
    reloc type requires context we don't have (data-relative).
    """
    info = _RELOC_INFO.get(reloc.reloc_type)
    if info is None:
        return None
    nbytes = info["bytes"]
    mode = info["mode"]
    if offset + nbytes > len(data):
        return None

    if mode == "absolute":
        fmt = _RELOC_ABS_FMT.get(nbytes)
        if fmt is None:
            return None
        return struct.unpack_from(fmt, data, offset)[0]

    if mode == "pc_relative":
        fmt = _RELOC_REL_FMT.get(nbytes)
        if fmt is None:
            return None
        disp = struct.unpack_from(fmt, data, offset)[0]
        return offset + disp

    # data_relative: would need to know data hunk base, which depends on
    # loader placement — can't resolve statically without more context
    return None


def fmt_addr(addr: int) -> str:
    return f"0x{addr:04X}"


def build_subroutine_map(blocks: dict[int, BasicBlock],
                         call_targets: set[int],
                         entry_point: int) -> list[dict]:
    """Compute subroutine boundaries from basic blocks and call targets.

    Returns list of dicts with keys: addr, end, block_count, instr_count,
    and optionally reached=False for stub entries.
    """
    _, _, meta = _load_kb()
    opword_bytes = meta["opword_bytes"]

    # All subroutine entry points
    entries = sorted({entry_point} | call_targets)

    # Map each block to its owning subroutine.
    # A block belongs to the entry it is reachable from without crossing
    # another entry point.
    block_owner: dict[int, int] = {}

    for entry in entries:
        if entry not in blocks:
            continue
        # BFS from entry, stopping at other entry points
        work = [entry]
        visited = set()
        while work:
            addr = work.pop()
            if addr in visited:
                continue
            if addr != entry and addr in call_targets:
                continue  # different subroutine
            if addr not in blocks:
                continue
            if addr in block_owner:
                continue  # already claimed
            visited.add(addr)
            block_owner[addr] = entry
            for succ in blocks[addr].successors:
                work.append(succ)

    # Group blocks by owner
    sub_blocks: dict[int, list[BasicBlock]] = defaultdict(list)
    for block_addr, owner in block_owner.items():
        sub_blocks[owner].append(blocks[block_addr])

    subroutines = []
    for entry in entries:
        if entry in sub_blocks:
            blist = sub_blocks[entry]
            sub_start = min(b.start for b in blist)
            sub_end = max(b.end for b in blist)
            instr_count = sum(len(b.instructions) for b in blist)
            subroutines.append({
                "addr": sub_start,
                "end": sub_end,
                "block_count": len(blist),
                "instr_count": instr_count,
            })
        else:
            # Call target not reached by executor — create stub entity.
            # End placeholder: minimum instruction size from KB opword_bytes.
            subroutines.append({
                "addr": entry,
                "end": entry + opword_bytes,
                "block_count": 0,
                "instr_count": 0,
                "reached": False,
            })

    # Sort by address
    subroutines.sort(key=lambda s: s["addr"])

    # Fix overlaps: truncate earlier subroutine if it overlaps the next
    for i in range(len(subroutines) - 1):
        if subroutines[i]["end"] > subroutines[i + 1]["addr"]:
            subroutines[i]["end"] = subroutines[i + 1]["addr"]

    return subroutines


def build_reloc_references(hunks, code_size: int,
                           subroutines: list[dict]) -> list[dict]:
    """Extract data references from relocation entries.

    Reloc offsets point to longwords in the code that contain absolute
    addresses. Targets outside known subroutines are potential data regions.
    """
    # Build address lookup for subroutines
    sub_ranges = [(s["addr"], s["end"]) for s in subroutines]

    def in_known_sub(addr):
        for start, end in sub_ranges:
            if start <= addr < end:
                return True
        return False

    data_refs = []
    for hunk in hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            continue
        for reloc in hunk.relocs:
            info = _RELOC_INFO.get(reloc.reloc_type)
            if info is None:
                continue
            for offset in reloc.offsets:
                target = _resolve_reloc_target(reloc, offset, hunk.data)
                if target is not None and 0 <= target < code_size:
                    if not in_known_sub(target):
                        data_refs.append({
                            "addr": target,
                            "offset": offset,
                            "hunk": hunk.index,
                            "ptr_size": info["bytes"],
                        })

    # Deduplicate by target address
    seen = set()
    unique = []
    for ref in data_refs:
        if ref["addr"] not in seen:
            seen.add(ref["addr"])
            unique.append(ref)
    unique.sort(key=lambda r: r["addr"])
    return unique


def fill_gaps(entities: list[dict], total_size: int, hunk_idx: int):
    """Add 'unknown' entities for unmapped regions in [0, total_size)."""
    sorted_ents = sorted(entities, key=lambda e: int(e["addr"], 16))
    gaps = []

    # Gap before first entity
    if sorted_ents:
        first_start = int(sorted_ents[0]["addr"], 16)
        if first_start > 0:
            gaps.append((0, first_start))
    else:
        gaps.append((0, total_size))

    # Gaps between entities
    for i in range(len(sorted_ents) - 1):
        curr_end = int(sorted_ents[i]["end"], 16)
        next_start = int(sorted_ents[i + 1]["addr"], 16)
        if next_start > curr_end:
            gaps.append((curr_end, next_start))

    # Gap after last entity
    if sorted_ents:
        last_end = int(sorted_ents[-1]["end"], 16)
        if last_end < total_size:
            gaps.append((last_end, total_size))

    gap_entities = []
    for start, end in gaps:
        gap_entities.append({
            "addr": fmt_addr(start),
            "end": fmt_addr(end),
            "type": "unknown",
            "status": "unmapped",
            "confidence": "tool-inferred",
            "hunk": hunk_idx,
        })
    return gap_entities


def assign_xrefs(subroutines: list[dict], xrefs: list,
                 ) -> tuple[dict, dict]:
    """Map instruction-level xrefs to subroutine-level entity xrefs.

    Returns (forward_map, reverse_map) where each maps entity addr to
    {field: set(target_addrs)}.
    Prints count of xrefs dropped due to unmapped src/dst addresses.
    """
    # For fast range lookup, build sorted list
    sorted_subs = sorted(subroutines, key=lambda s: s["addr"])

    def find_sub(addr):
        """Find which subroutine contains the given address."""
        # Binary search
        lo, hi = 0, len(sorted_subs) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            s = sorted_subs[mid]
            if addr < s["addr"]:
                hi = mid - 1
            elif addr >= s["end"]:
                lo = mid + 1
            else:
                return s["addr"]
        return None

    forward: dict[int, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    reverse: dict[int, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    dropped = 0

    for xref in xrefs:
        if xref.type == "fallthrough":
            continue  # internal control flow

        src_sub = find_sub(xref.src)
        dst_sub = find_sub(xref.dst)

        if src_sub is None or dst_sub is None:
            dropped += 1
            continue
        if src_sub == dst_sub:
            continue  # intra-subroutine

        if xref.type == "call":
            forward[src_sub]["calls"].add(dst_sub)
            reverse[dst_sub]["called_by"].add(src_sub)
        elif xref.type in ("branch", "jump"):
            # Inter-subroutine branches/jumps are treated as calls
            forward[src_sub]["calls"].add(dst_sub)
            reverse[dst_sub]["called_by"].add(src_sub)

    if dropped:
        print(f"  {dropped} xrefs dropped (src or dst outside known subroutines)")
    return forward, reverse


def build_entities(binary_path: str, output_path: str = None):
    """Main pipeline: parse binary, run executor, generate entities."""
    if output_path is None:
        output_path = str(PROJECT_ROOT / "entities.jsonl")

    print(f"Parsing {binary_path}...")
    hf = parse_file(binary_path)

    if not hf.is_executable:
        print("ERROR: not an executable hunk file")
        return 1

    print(f"  {len(hf.hunks)} hunks")
    for h in hf.hunks:
        print(f"    #{h.index}: {h.type_name} {len(h.data)} bytes, "
              f"{len(h.relocs)} reloc groups, {len(h.symbols)} symbols")

    all_entities = []

    for hunk in hf.hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            # DATA/BSS hunks become entities directly
            etype = "data" if hunk.hunk_type == HunkType.HUNK_DATA else "bss"
            all_entities.append({
                "addr": fmt_addr(0),
                "end": fmt_addr(hunk.alloc_size),
                "type": etype,
                "status": "unmapped",
                "confidence": "tool-inferred",
                "hunk": hunk.index,
            })
            continue

        code = hunk.data
        code_size = len(code)

        # Collect extra entry points from relocations
        reloc_targets = set()
        for reloc in hunk.relocs:
            for offset in reloc.offsets:
                target = _resolve_reloc_target(reloc, offset, code)
                if target is not None and 0 <= target < code_size:
                    reloc_targets.add(target)

        # Load platform config from OS KB for calling convention
        platform_config = get_platform_config()

        print(f"\nRunning executor on hunk #{hunk.index} "
              f"({code_size} bytes, {len(reloc_targets)} reloc targets)...")

        # Iterative analysis: discover blocks, detect jump tables,
        # resolve indirect targets via propagation, repeat until stable.
        all_entry_points = {0} | reloc_targets
        max_passes = 8
        for pass_num in range(1, max_passes + 1):
            use_propagate = pass_num >= 2  # propagation from pass 2 onward
            result = analyze(code, base_addr=0,
                             entry_points=sorted(all_entry_points),
                             propagate=use_propagate,
                             platform=platform_config if use_propagate else None)
            blocks = result["blocks"]

            # Jump table detection
            tables = detect_jump_tables(blocks, code, base_addr=0)
            new_targets = set()
            for t in tables:
                new_targets.update(t["targets"])

            # Indirect target resolution via propagated state
            resolved = []
            if use_propagate and result.get("exit_states"):
                resolved = resolve_indirect_targets(
                    blocks, result["exit_states"], code_size)
                for r in resolved:
                    new_targets.add(r["target"])

            new_targets -= set(blocks.keys())
            new_targets -= all_entry_points

            if pass_num == 1 or new_targets:
                covered = sum(b.end - b.start for b in blocks.values())
                total_instr = sum(len(b.instructions)
                                  for b in blocks.values())
                extras = []
                if tables:
                    extras.append(f"{len(tables)} jump tables")
                if resolved:
                    extras.append(f"{len(resolved)} indirect resolved")
                extra_msg = ", " + ", ".join(extras) if extras else ""
                print(f"  Pass {pass_num}: {len(blocks)} blocks, "
                      f"{total_instr} instructions, "
                      f"{covered}/{code_size} bytes "
                      f"({100 * covered / code_size:.1f}%)"
                      f"{extra_msg}")

            if not new_targets:
                break
            all_entry_points |= new_targets

        xrefs = result["xrefs"]
        call_targets = result["call_targets"]
        print(f"  {len(xrefs)} xrefs, "
              f"{len(call_targets)} call targets, "
              f"{len(result['branch_targets'])} branch targets")

        # Identify OS library calls
        os_kb = load_os_kb()
        lib_calls = identify_library_calls(
            blocks, code, os_kb, result.get("exit_states"))
        if lib_calls:
            identified = sum(1 for c in lib_calls
                             if c.get("library") != "unknown")
            libs_seen = set(c["library"] for c in lib_calls
                            if c.get("library") != "unknown")
            print(f"  {len(lib_calls)} library calls identified "
                  f"({identified} resolved, "
                  f"libraries: {', '.join(sorted(libs_seen))})")

        # Build subroutine map
        subroutines = build_subroutine_map(blocks, call_targets, 0)
        stubs = sum(1 for s in subroutines if not s.get("reached", True))
        print(f"  {len(subroutines)} subroutines ({stubs} stubs — unreached)")

        # Assign cross-references (reports dropped xrefs)
        fwd_xrefs, rev_xrefs = assign_xrefs(subroutines, xrefs)

        # Build library call map: subroutine addr -> list of OS calls made
        lib_call_map = defaultdict(list)
        if lib_calls:
            sorted_subs = sorted(subroutines, key=lambda s: s["addr"])
            for call in lib_calls:
                # Find containing subroutine
                for sub in sorted_subs:
                    if sub["addr"] <= call["addr"] < sub["end"]:
                        lib_call_map[sub["addr"]].append(
                            f"{call['library']}/{call['function']}")
                        break

        # Build subroutine entities
        stub_count = 0
        for sub in subroutines:
            ent = {
                "addr": fmt_addr(sub["addr"]),
                "end": fmt_addr(sub["end"]),
                "type": "code",
                "status": "typed",
                "confidence": "tool-inferred",
                "hunk": hunk.index,
                "block_count": sub["block_count"],
                "instr_count": sub["instr_count"],
            }
            if not sub.get("reached", True):
                ent["stub"] = True
                stub_count += 1
            addr = sub["addr"]
            # Add forward xrefs
            if addr in fwd_xrefs:
                for field, targets in fwd_xrefs[addr].items():
                    ent[field] = sorted(fmt_addr(t) for t in targets)
            # Add reverse xrefs
            if addr in rev_xrefs:
                for field, sources in rev_xrefs[addr].items():
                    ent[field] = sorted(fmt_addr(s) for s in sources)
            # Add OS library calls made by this subroutine
            if addr in lib_call_map:
                ent["os_calls"] = sorted(set(lib_call_map[addr]))
            all_entities.append(ent)

        # Build reloc-derived data references for uncovered regions
        data_refs = build_reloc_references(
            [hunk], code_size, subroutines)
        for ref in data_refs:
            ref_end = ref["addr"] + ref["ptr_size"]
            all_entities.append({
                "addr": fmt_addr(ref["addr"]),
                "end": fmt_addr(ref_end),
                "type": "unknown",
                "status": "unmapped",
                "confidence": "tool-inferred",
                "hunk": hunk.index,
                "source": "reloc32",
            })

        # Remove reloc entities that overlap with subroutines or each other
        all_entities = _remove_overlapping(all_entities)

        # Fill gaps to cover entire hunk
        gap_ents = fill_gaps(
            [e for e in all_entities
             if e.get("hunk") == hunk.index],
            code_size, hunk.index)
        all_entities.extend(gap_ents)

    # Sort by address
    def _addr_int(e):
        a = e["addr"]
        return int(a, 16) if isinstance(a, str) else a
    all_entities.sort(key=_addr_int)

    # Write output
    with open(output_path, "w") as f:
        for ent in all_entities:
            f.write(json.dumps(ent, separators=(",", ":")) + "\n")

    print(f"\nWrote {len(all_entities)} entities to {output_path}")

    # Summary
    type_counts = defaultdict(int)
    status_counts = defaultdict(int)
    for ent in all_entities:
        type_counts[ent["type"]] += 1
        status_counts[ent.get("status", "unmapped")] += 1

    print("\nSummary:")
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    print()
    for s, c in sorted(status_counts.items()):
        print(f"  {s}: {c}")

    # Count xrefs
    total_calls = sum(len(e.get("calls", [])) for e in all_entities)
    total_called_by = sum(len(e.get("called_by", [])) for e in all_entities)
    print(f"\n  call xrefs: {total_calls} forward, {total_called_by} reverse")

    return 0


def _remove_overlapping(entities: list[dict]) -> list[dict]:
    """Remove entities that overlap with earlier ones (sorted by addr)."""
    entities.sort(key=lambda e: int(e["addr"], 16))
    result = []
    for ent in entities:
        addr = int(ent["addr"], 16)
        end = int(ent["end"], 16)
        # Check against all existing
        overlap = False
        for existing in result:
            ex_addr = int(existing["addr"], 16)
            ex_end = int(existing["end"], 16)
            if addr < ex_end and end > ex_addr:
                overlap = True
                break
        if not overlap:
            result.append(ent)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Build entities.jsonl from hunk binary analysis")
    parser.add_argument("binary", help="Path to Amiga hunk executable")
    parser.add_argument("--output", "-o",
                        help="Output path (default: entities.jsonl)")
    args = parser.parse_args()

    return build_entities(args.binary, args.output)


if __name__ == "__main__":
    sys.exit(main())
