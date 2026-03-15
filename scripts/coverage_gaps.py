#!/usr/bin/env py.exe
"""Coverage gap analysis: diagnose why the disassembly pipeline missed code/data.

Reports gaps in analysis coverage with root causes, not guesses about
data types.  Each gap explains what evidence exists and what pipeline
improvement would resolve it.

All pattern detection driven from M68K KB (return opcodes from encodings,
alignment from opword_bytes, reloc semantics from hunk format KB).

Usage:
    python coverage_gaps.py <binary> [--entities entities.jsonl]
"""

import json
import struct
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from m68k.hunk_parser import parse_file, HunkType
from m68k.m68k_executor import analyze
from m68k.m68k_disasm import _Decoder, _decode_one, DecodeError
from m68k.os_calls import get_platform_config, _SENTINEL_ALLOC_BASE
from build_entities import _resolve_reloc_target
from m68k.kb_util import KB, read_string_at


PROJECT_ROOT = Path(__file__).parent.parent


# ── KB-derived constants ─────────────────────────────────────────────────

def _build_return_opcodes(kb_path: Path) -> set[int]:
    """Build set of return instruction opcodes from KB encoding fields."""
    with open(kb_path, encoding="utf-8") as f:
        kb_data = json.load(f)
    opcodes = set()
    for inst in kb_data["instructions"]:
        flow = inst.get("pc_effects", {}).get("flow", {})
        if flow.get("type") != "return":
            continue
        enc = inst.get("encodings", [{}])[0]
        opcode = 0
        mask = 0
        for field in enc.get("fields", []):
            if field["name"] in ("0", "1"):
                bit = field["bit_lo"]
                mask |= 1 << bit
                if field["name"] == "1":
                    opcode |= 1 << bit
        if mask == 0xFFFF:
            opcodes.add(opcode)
    return opcodes


# ── Analysis setup ───────────────────────────────────────────────────────

def _setup_analysis(hf, hunk):
    """Run the same analysis pipeline as build_entities/gen_disasm.

    Returns (blocks, verified_set, code_regions, platform).
    """
    code = hunk.data

    reloc_targets = set()
    for reloc in hunk.relocs:
        for offset in reloc.offsets:
            target = _resolve_reloc_target(reloc, offset, code)
            if target is not None and 0 <= target < len(code):
                reloc_targets.add(target)

    platform = get_platform_config()
    init = analyze(code, base_addr=0, entry_points=[0],
                   propagate=True, platform=platform)
    alloc_limit = platform.get("_next_alloc_sentinel", _SENTINEL_ALLOC_BASE)
    base_reg_num = platform.get("_base_reg_num", 6)
    for addr, (cpu, mem) in init["exit_states"].items():
        a6 = cpu.a[base_reg_num]
        if (a6.is_known
                and _SENTINEL_ALLOC_BASE <= a6.concrete < alloc_limit):
            platform["initial_base_reg"] = (base_reg_num, a6.concrete)
            break

    result = analyze(code, base_addr=0,
                     entry_points=sorted({0} | reloc_targets),
                     propagate=False, platform=platform)
    all_blocks = result["blocks"]

    # Flow-verified: reachable from 0 via successors + calls
    verified = set()
    work = [0]
    while work:
        a = work.pop()
        if a in verified or a not in all_blocks:
            continue
        verified.add(a)
        blk = all_blocks[a]
        for succ in blk.successors:
            work.append(succ)
        for xref in blk.xrefs:
            if xref.type == "call":
                work.append(xref.dst)

    code_regions = set()
    for a in verified:
        blk = all_blocks[a]
        for p in range(blk.start, blk.end):
            code_regions.add(p)

    return all_blocks, verified, code_regions, platform


# ── Gap detectors ────────────────────────────────────────────────────────

def find_unreachable_relocs(code: bytes, hunk, code_regions: set[int],
                            all_blocks: dict) -> list[dict]:
    """Find relocations in regions not covered by any block.

    These are instructions (JSR/JMP/MOVEA with relocated operands) that
    the executor never decoded because no control flow path reaches them.

    Root cause: subroutines callable only through indirect mechanisms
    (function pointers, computed jumps) that the pipeline cannot trace.
    """
    gaps = []
    for reloc in hunk.relocs:
        for offset in reloc.offsets:
            if offset in code_regions:
                continue
            if offset + 4 > len(code):
                continue
            target = struct.unpack_from(">I", code, offset)[0]

            # Check if this looks like an instruction operand
            # (the opword should be 2 bytes before the reloc offset)
            inst_addr = offset - 2
            in_block = any(all_blocks[a].start <= inst_addr < all_blocks[a].end
                           for a in all_blocks)

            # Try to decode the instruction at the presumed address
            decoded = None
            if inst_addr >= 0:
                d = _Decoder(code, 0)
                d.pos = inst_addr
                try:
                    inst = _decode_one(d, None)
                    if inst.offset == inst_addr:
                        decoded = inst.text.strip()
                except (DecodeError, struct.error):
                    pass

            gaps.append({
                "type": "unreachable_reloc",
                "addr": offset,
                "target": target,
                "target_in_code": target in code_regions,
                "inst_addr": inst_addr,
                "decoded": decoded,
                "in_any_block": in_block,
                "root_cause": "no_control_flow_path",
            })
    return gaps


def find_unreachable_returns(code: bytes, code_regions: set[int],
                             return_opcodes: set[int],
                             opword_bytes: int) -> list[dict]:
    """Find return opcodes in regions not covered by verified blocks.

    A return instruction in unanalyzed space indicates a complete
    subroutine that the pipeline couldn't reach.

    Root cause: the subroutine's entry point is not called from any
    reachable code (only through indirect mechanisms).
    """
    gaps = []
    for pos in range(0, len(code) - opword_bytes + 1, opword_bytes):
        if pos in code_regions:
            continue
        word = struct.unpack_from(">H", code, pos)[0]
        if word not in return_opcodes:
            continue
        # Verify it's preceded by other non-code bytes (not a known block end)
        if pos >= opword_bytes and (pos - opword_bytes) in code_regions:
            continue
        gaps.append({
            "type": "unreachable_return",
            "addr": pos,
            "opcode": f"${word:04x}",
            "root_cause": "subroutine_not_reachable",
        })
    return gaps


def find_unindexed_strings(code: bytes, verified_strings: set[int],
                           code_regions: set[int]) -> list[dict]:
    """Find string tables adjacent to verified PC-relative strings.

    These strings exist but are accessed via computed index rather than
    direct PC-relative addressing — the pipeline can't trace the
    indexing code.

    Root cause: string table accessed via base+offset pattern where
    the offset is computed at runtime (e.g., error code -> string).
    """
    gaps = []
    seen = set(verified_strings)

    for start_addr in sorted(verified_strings):
        s = read_string_at(code, start_addr, max_len=200)
        if not s:
            continue
        pos = start_addr + len(s) + 1

        while pos < len(code) and pos not in code_regions:
            while pos < len(code) and code[pos] == 0:
                pos += 1
            if pos >= len(code) or pos in code_regions:
                break
            s = read_string_at(code, pos, max_len=200)
            if not s or len(s) < 4:
                break
            alpha = sum(1 for c in s if c.isalpha())
            if alpha < len(s) * 0.5:
                break
            if pos not in seen:
                seen.add(pos)
                gaps.append({
                    "type": "unindexed_string",
                    "addr": pos,
                    "end": pos + len(s) + 1,
                    "text": s[:60],
                    "adjacent_to": start_addr,
                    "root_cause": "computed_string_index",
                })
            pos += len(s) + 1

    return gaps


def find_unverified_blocks(all_blocks: dict, verified: set[int]
                           ) -> list[dict]:
    """Find blocks discovered by the executor but not flow-verified.

    These blocks are decodable as instructions and were discovered from
    reloc-target entry points, but no control flow from entry point 0
    reaches them.

    Root cause: reloc target may be a data pointer (not a code entry)
    or the code is only reachable through indirect calls.
    """
    gaps = []
    for addr in sorted(all_blocks):
        if addr in verified:
            continue
        blk = all_blocks[addr]
        gaps.append({
            "type": "unverified_block",
            "addr": addr,
            "end": blk.end,
            "instr_count": len(blk.instructions),
            "is_entry": blk.is_entry,
            "predecessors": len(blk.predecessors),
            "root_cause": "reloc_entry_unverified"
                if blk.is_entry else "unreachable_from_entry",
        })
    return gaps


# ── Main ─────────────────────────────────────────────────────────────────

def analyze_gaps(binary_path: str, entities_path: str) -> list[dict]:
    """Run all gap detectors and return structured diagnostics."""
    hf = parse_file(binary_path)

    with open(entities_path) as f:
        entities = [json.loads(line) for line in f if line.strip()]

    kb = KB()
    kb_path = (Path(__file__).resolve().parent.parent
               / "knowledge" / "m68k_instructions.json")
    return_opcodes = _build_return_opcodes(kb_path)
    opword_bytes = kb.meta["opword_bytes"]

    all_gaps = []

    for hunk in hf.hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            continue
        code = hunk.data
        all_blocks, verified, code_regions, platform = \
            _setup_analysis(hf, hunk)

        # Get verified strings for adjacency check
        from gen_disasm import discover_pc_relative_targets
        pc_targets = discover_pc_relative_targets(
            {a: all_blocks[a] for a in verified}, code, kb)
        verified_strings = {addr for addr, name in pc_targets.items()
                            if name.startswith("str_")}

        all_gaps.extend(find_unreachable_relocs(
            code, hunk, code_regions, all_blocks))
        all_gaps.extend(find_unreachable_returns(
            code, code_regions, return_opcodes, opword_bytes))
        all_gaps.extend(find_unindexed_strings(
            code, verified_strings, code_regions))
        all_gaps.extend(find_unverified_blocks(
            all_blocks, verified))

    return all_gaps


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose coverage gaps in disassembly analysis")
    parser.add_argument("binary", help="Path to Amiga hunk executable")
    parser.add_argument("--entities", "-e",
                        default=str(PROJECT_ROOT / "entities.jsonl"),
                        help="Path to entities.jsonl")
    args = parser.parse_args()

    gaps = analyze_gaps(args.binary, args.entities)

    # Group by root cause
    by_cause = {}
    for g in gaps:
        cause = g["root_cause"]
        by_cause.setdefault(cause, []).append(g)

    print(f"{len(gaps)} coverage gaps found\n")
    print("By root cause:")
    for cause, glist in sorted(by_cause.items(),
                                key=lambda x: -len(x[1])):
        types = {}
        for g in glist:
            types[g["type"]] = types.get(g["type"], 0) + 1
        type_str = ", ".join(f"{v} {k}" for k, v in types.items())
        print(f"  {cause}: {len(glist)} gaps ({type_str})")

    # Detail each category
    for cause in sorted(by_cause):
        glist = by_cause[cause]
        print(f"\n{'='*60}")
        print(f"ROOT CAUSE: {cause}")
        print(f"{'='*60}")

        if cause == "no_control_flow_path":
            print("Relocations in undecoded regions containing valid")
            print("instructions. The subroutines are callable only through")
            print("indirect mechanisms the pipeline cannot trace.")
            print(f"\n{len(glist)} instances:")
            for g in glist[:10]:
                decoded = g.get("decoded", "?")
                tgt = f"${g['target']:04x}"
                tgt_status = "IN CODE" if g["target_in_code"] else "ALSO UNREACHABLE"
                print(f"  ${g['addr']:04x}: {decoded}")
                print(f"    target {tgt} ({tgt_status})")

        elif cause == "subroutine_not_reachable":
            print("Return opcodes (from KB) in unanalyzed regions.")
            print("Each likely ends a subroutine with no known caller.")
            print(f"\n{len(glist)} instances (showing first 10):")
            for g in glist[:10]:
                print(f"  ${g['addr']:04x}: {g['opcode']}")

        elif cause == "computed_string_index":
            print("Strings adjacent to verified PC-relative targets.")
            print("Accessed via computed index (error code -> offset),")
            print("not direct PC-relative addressing.")
            print(f"\n{len(glist)} strings (showing first 10):")
            for g in glist[:10]:
                print(f'  ${g["addr"]:04x}: "{g["text"]}"')

        elif cause == "reloc_entry_unverified":
            print("Blocks at reloc-target addresses that decoded as")
            print("valid instructions but aren't reachable from entry 0.")
            print("May be data pointers misidentified as code entries.")
            print(f"\n{len(glist)} blocks:")
            for g in glist[:10]:
                print(f"  ${g['addr']:04x}-${g['end']:04x}: "
                      f"{g['instr_count']} instructions")

        elif cause == "unreachable_from_entry":
            print("Blocks discovered from non-entry predecessors that")
            print("aren't in the verified set.")
            print(f"\n{len(glist)} blocks")


if __name__ == "__main__":
    main()
