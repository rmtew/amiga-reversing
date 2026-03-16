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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from m68k.hunk_parser import parse_file, HunkType
from m68k.m68k_executor import analyze, BasicBlock, _load_kb
from m68k.jump_tables import (detect_jump_tables, resolve_indirect_targets,
                               resolve_per_caller, resolve_backward_slice)
from m68k.os_calls import (load_os_kb, get_platform_config, identify_library_calls,
                            _SENTINEL_ALLOC_BASE)
from m68k.subroutine_scan import scan_and_score
from m68k.kb_util import KB
from m68k.name_entities import name_subroutines


PROJECT_ROOT = Path(__file__).parent.parent

# Relocation semantics loaded from hunk format KB.
# Maps HunkType int → {"bytes": N, "mode": "absolute"|"pc_relative"|...}
from m68k.hunk_parser import _HUNK_KB
_RELOC_INFO = {}
for _name, _sem in _HUNK_KB.get("relocation_semantics", {}).items():
    if _name in HunkType.__members__:
        _RELOC_INFO[HunkType[_name]] = {
            "bytes": _sem["bytes"],
            "mode": _sem["mode"],
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

        print(f"\nAnalyzing hunk #{hunk.index} "
              f"({code_size} bytes, {len(reloc_targets)} reloc targets)...")

        def _stats(blks):
            covered = sum(b.end - b.start for b in blks.values())
            n = sum(len(b.instructions) for b in blks.values())
            return (f"{len(blks)} blocks, {n} instructions, "
                    f"{covered}/{code_size} ({100*covered/code_size:.1f}%)")

        # ── Phase 0: Init discovery ──────────────────────────────────
        # Entry point 0 only. Discovers base register (AllocMem
        # pattern) and captures init memory (library base tags).
        base_reg_num = platform_config["_base_reg_num"]
        init_result = analyze(code, base_addr=0, entry_points=[0],
                              propagate=True, platform=platform_config)
        alloc_base = _SENTINEL_ALLOC_BASE
        alloc_limit = platform_config["_next_alloc_sentinel"]
        discovered_base = None
        best_addr = None
        best_slots = 0
        for addr, (cpu, mem) in init_result.get(
                "exit_states", {}).items():
            val = cpu.a[base_reg_num]
            if (val.is_known
                    and alloc_base <= val.concrete < alloc_limit):
                if discovered_base is None:
                    discovered_base = val.concrete
                slots = sum(1 for a in mem._bytes
                            if alloc_base <= a < alloc_limit)
                if slots > best_slots:
                    best_slots = slots
                    best_addr = addr
        if discovered_base is not None:
            print(f"  Base register A{base_reg_num} "
                  f"= ${discovered_base:08X} (from init"
                  f", {best_slots} memory bytes)")
            platform_config["initial_base_reg"] = (
                base_reg_num, discovered_base)
            if best_addr is not None:
                _, init_mem = init_result["exit_states"][best_addr]
                platform_config["_initial_mem"] = init_mem

        # ── Phase 1: Core analysis ───────────────────────────────────
        # Entry point 0 only.  Jump table and indirect targets are
        # flow-verified and feed back into the core.  Propagation
        # gives concrete state to all reachable blocks.  No reloc
        # or scan entries — those are hints (Phase 2).
        #
        # Multi-pass: after convergence, scan exit states for concrete
        # stores to app memory (function pointers, library bases set
        # after init).  Merge into init memory and re-run.  Each pass
        # discovers more stores, enabling more indirect resolution.
        core_entries = {0}
        jt_call_targets = set()
        kb = KB()

        def _resolve_and_expand():
            """Run all resolution passes, add new targets to core_entries.
            Returns number of new entries added."""
            added = 0
            for t in detect_jump_tables(
                    result["blocks"], code, base_addr=0):
                for tgt in t["targets"]:
                    if tgt not in core_entries:
                        core_entries.add(tgt)
                        added += 1
                dblk = result["blocks"].get(t["dispatch_block"])
                if dblk and dblk.instructions:
                    ft, _ = kb.flow_type(dblk.instructions[-1])
                    if ft == "call":
                        jt_call_targets.update(t["targets"])
            for r in resolve_indirect_targets(
                    result["blocks"],
                    result.get("exit_states", {}),
                    code_size):
                if r["target"] not in core_entries:
                    core_entries.add(r["target"])
                    added += 1
            for r in resolve_per_caller(
                    result["blocks"],
                    result.get("exit_states", {}),
                    code, code_size,
                    platform=platform_config):
                if r["target"] not in core_entries:
                    core_entries.add(r["target"])
                    added += 1
            for r in resolve_backward_slice(
                    result["blocks"],
                    result.get("exit_states", {}),
                    code, code_size,
                    platform=platform_config):
                if r["target"] not in core_entries:
                    core_entries.add(r["target"])
                    added += 1
            return added

        entries_converged = False
        for store_pass in range(5):
            # Inner loop: analyze + resolve until no new entries.
            # After entries converge, store passes only re-analyze
            # (for updated memory in exit states) without re-resolving.
            for _ in range(10):
                result = analyze(code, base_addr=0,
                                 entry_points=sorted(core_entries),
                                 propagate=True,
                                 platform=platform_config)
                if entries_converged:
                    break  # just re-analyzed with new memory
                if not _resolve_and_expand():
                    entries_converged = True
                    break

            # Scan exit states for concrete stores to app memory.
            # When a block's exit memory has concrete values in the
            # base-register region that the init memory lacks, those
            # are stores made during the main flow (function pointer
            # setup, library base caching).  Merge them into init
            # memory for the next pass.
            if not platform_config.get("initial_base_reg"):
                break
            breg_num, breg_val = platform_config["initial_base_reg"]
            init_mem = platform_config.get("_initial_mem")
            if init_mem is None:
                break

            new_stores = 0
            for addr, (cpu, mem) in result.get(
                    "exit_states", {}).items():
                for mem_addr, val in mem._bytes.items():
                    if not (alloc_base <= mem_addr < alloc_limit):
                        continue
                    if mem_addr in init_mem._bytes:
                        continue  # already known
                    if val.concrete is None:
                        continue
                    # Only capture values that are valid code
                    # addresses (within the hunk)
                    if not (0 <= val.concrete < code_size):
                        continue
                    init_mem._bytes[mem_addr] = val
                    new_stores += 1
                # Also merge tags
                for key, tag in mem._tags.items():
                    if key not in init_mem._tags:
                        init_mem._tags[key] = tag

            if new_stores == 0:
                break
            disp_example = ""
            for mem_addr in sorted(init_mem._bytes):
                if (alloc_base <= mem_addr < alloc_limit
                        and init_mem._bytes[mem_addr].concrete is not None
                        and 0 <= init_mem._bytes[mem_addr].concrete < code_size):
                    disp_example = f" (e.g. d({mem_addr - breg_val}))"
                    break
            print(f"  Store pass {store_pass + 1}: "
                  f"{new_stores} new memory values{disp_example}")

        blocks = result["blocks"]
        xrefs = result["xrefs"]
        call_targets = result["call_targets"] | jt_call_targets
        exit_states = result.get("exit_states", {})
        core_covered = sum(b.end - b.start for b in blocks.values())
        print(f"  Core: {_stats(blocks)}")

        # ── Phase 2: Hint discovery ──────────────────────────────────
        # Reloc targets and heuristic scan produce additional blocks.
        # These are NOT part of the core — no propagation, no state.
        # They tell us where code exists that the core can't reach.
        # Each hint is annotated with its source and why the core
        # can't reach it — these drive engine improvements.

        # Build reloc reference map: target -> [referencing offsets]
        reloc_refs: dict[int, list[int]] = {}
        for reloc in hunk.relocs:
            for offset in reloc.offsets:
                target = _resolve_reloc_target(reloc, offset, code)
                if target is not None and 0 <= target < code_size:
                    reloc_refs.setdefault(target, []).append(offset)

        # Core address set for classifying references
        core_addrs = set()
        for blk in blocks.values():
            for a in range(blk.start, blk.end):
                core_addrs.add(a)

        # Discover hint blocks from reloc targets
        hint_entries = reloc_targets - set(blocks.keys())
        hint_blocks: dict[int, BasicBlock] = {}
        hint_source: dict[int, str] = {}  # entry -> "reloc"|"scan"
        if hint_entries:
            hint_result = analyze(code, base_addr=0,
                                  entry_points=sorted(hint_entries),
                                  propagate=False)
            for a, b in hint_result["blocks"].items():
                if a not in blocks:
                    hint_blocks[a] = b
            for e in hint_entries:
                hint_source[e] = "reloc"

        # Heuristic scan on uncovered regions
        scan_candidates = scan_and_score(
            blocks, code, reloc_targets, call_targets)
        scan_entries = {c["addr"] for c in scan_candidates
                        if c["addr"] not in blocks
                        and c["addr"] not in hint_blocks}
        if scan_entries:
            scan_result = analyze(code, base_addr=0,
                                  entry_points=sorted(scan_entries),
                                  propagate=False)
            for a, b in scan_result["blocks"].items():
                if a not in blocks and a not in hint_blocks:
                    hint_blocks[a] = b
            for e in scan_entries:
                hint_source[e] = "scan"

        # Classify each hint entry: why can't the core reach it?
        # - "reloc_from_core": referenced by a reloc in core code
        #   (function pointer loaded but not called directly)
        # - "reloc_from_hint": referenced by a reloc in non-core code
        # - "scan": found by heuristic scan (no reloc reference)
        hint_reasons: dict[int, dict] = {}
        for entry in sorted(set(hint_entries) | scan_entries):
            reason = {"source": hint_source.get(entry, "scan")}
            if entry in reloc_refs:
                refs = reloc_refs[entry]
                core_refs = [r for r in refs if r in core_addrs]
                if core_refs:
                    reason["source"] = "reloc_from_core"
                    reason["referenced_from"] = core_refs
                else:
                    reason["source"] = "reloc_from_hint"
                    reason["referenced_from"] = refs
            hint_reasons[entry] = reason

        if hint_blocks:
            hint_covered = sum(b.end - b.start
                               for b in hint_blocks.values())
            # Summarize by reason
            by_reason = defaultdict(int)
            for r in hint_reasons.values():
                by_reason[r["source"]] += 1
            reason_str = ", ".join(f"{c} {s}"
                                   for s, c in sorted(by_reason.items()))
            print(f"  Hints: {_stats(hint_blocks)} "
                  f"({reason_str})")

        print(f"  {len(xrefs)} xrefs, "
              f"{len(call_targets)} call targets, "
              f"{len(result['branch_targets'])} branch targets")

        # Identify OS library calls
        os_kb = load_os_kb()
        lib_calls = identify_library_calls(
            blocks, code, os_kb, result.get("exit_states", {}),
            call_targets, platform_config)
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

        # Build library call map: subroutine addr -> list of OS calls
        lib_call_map = defaultdict(list)
        if lib_calls:
            sorted_subs = sorted(subroutines, key=lambda s: s["addr"])
            for call in lib_calls:
                for sub in sorted_subs:
                    if sub["addr"] <= call["addr"] < sub["end"]:
                        lib_call_map[sub["addr"]].append(call)
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
                calls = lib_call_map[addr]
                ent["os_calls"] = sorted(set(
                    f"{c['library']}/{c['function']}" for c in calls))
                # Collect typed register annotations from KB
                typed_calls = []
                for c in calls:
                    entry = {"call": f"{c['library']}/{c['function']}"}
                    if c.get("inputs"):
                        inputs = {}
                        for inp in c["inputs"]:
                            if inp.get("reg") and inp.get("type"):
                                info = {"type": inp["type"]}
                                if inp.get("i_struct"):
                                    info["i_struct"] = inp["i_struct"]
                                inputs[inp["reg"]] = info
                        if inputs:
                            entry["inputs"] = inputs
                    out = c.get("output")
                    if out and out.get("type"):
                        info = {"type": out["type"]}
                        if out.get("i_struct"):
                            info["i_struct"] = out["i_struct"]
                        entry["output"] = {out["reg"]: info}
                    if "inputs" in entry or "output" in entry:
                        typed_calls.append(entry)
                if typed_calls:
                    ent["os_call_types"] = typed_calls
            all_entities.append(ent)

        # ── Hint entities ────────────────────────────────────────────
        # Build hint subroutines from hint blocks, annotated with
        # source and reachability info.  These are NOT verified —
        # they drive engine improvements.
        if hint_blocks:
            # Build hint entities from contiguous block regions.
            # Each contiguous group of blocks becomes one hint entity.
            sorted_hints = sorted(hint_blocks.values(),
                                  key=lambda b: b.start)
            regions = []
            for blk in sorted_hints:
                if (regions and blk.start <= regions[-1]["end"]):
                    # Extend current region
                    r = regions[-1]
                    r["end"] = max(r["end"], blk.end)
                    r["block_count"] += 1
                    r["instr_count"] += len(blk.instructions)
                else:
                    regions.append({
                        "addr": blk.start, "end": blk.end,
                        "block_count": 1,
                        "instr_count": len(blk.instructions),
                    })
            for region in regions:
                ent = {
                    "addr": fmt_addr(region["addr"]),
                    "end": fmt_addr(region["end"]),
                    "type": "code",
                    "status": "unmapped",
                    "confidence": "hint",
                    "hunk": hunk.index,
                    "block_count": region["block_count"],
                    "instr_count": region["instr_count"],
                }
                # Find the best-matching hint reason: any hint entry
                # that falls within this region's address range.
                best_reason = None
                for entry, reason in hint_reasons.items():
                    if region["addr"] <= entry < region["end"]:
                        if (best_reason is None
                                or reason["source"] == "reloc_from_core"):
                            best_reason = reason
                if best_reason:
                    ent["hint_source"] = best_reason["source"]
                    if "referenced_from" in best_reason:
                        ent["hint_refs"] = sorted(
                            fmt_addr(r)
                            for r in best_reason["referenced_from"])
                else:
                    ent["hint_source"] = "scan"
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

        # Name subroutines from OS calls, string references, call graph
        named = name_subroutines(all_entities, blocks, code, lib_calls)
        if named:
            print(f"  Named {named} subroutines")

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
    core_ents = [e for e in all_entities
                 if e.get("confidence") not in ("hint",)]
    hint_ents = [e for e in all_entities
                 if e.get("confidence") == "hint"]
    core_code = [e for e in core_ents if e["type"] == "code"]
    hint_code = [e for e in hint_ents if e["type"] == "code"]

    print("\nSummary:")
    print(f"  Core: {len(core_code)} subroutines, "
          f"{sum(1 for e in core_code if e.get('name'))} named")
    if hint_code:
        by_src = defaultdict(int)
        for e in hint_code:
            by_src[e.get("hint_source", "?")] += 1
        src_str = ", ".join(f"{c} {s}"
                            for s, c in sorted(by_src.items()))
        print(f"  Hints: {len(hint_code)} regions ({src_str})")
    gap_count = sum(1 for e in all_entities
                    if e.get("status") == "unmapped"
                    and e.get("confidence") != "hint")
    print(f"  Gaps: {gap_count} unmapped regions")

    total_calls = sum(len(e.get("calls", [])) for e in all_entities)
    total_called_by = sum(len(e.get("called_by", [])) for e in all_entities)
    print(f"  Xrefs: {total_calls} calls")

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
