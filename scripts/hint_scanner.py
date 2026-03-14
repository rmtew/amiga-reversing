#!/usr/bin/env py.exe
"""Hint scanner: discovers unverified patterns that suggest data/code types.

Scans binary regions NOT covered by flow-verified blocks and produces
scored hints for further analysis.  Hints are NOT classifications —
they are evidence that the analysis pipeline can use to extend coverage.

All patterns derived from KB data (M68K instructions, hunk format).

Hint types:
- string_table: consecutive null-terminated strings near a verified string
- orphan_reloc: reloc offset in a data region, not referenced by code
- trailing_return: return instruction at end of an unclassified region
- post_return_entry: word-aligned address after a return instruction

Usage:
    python hint_scanner.py <binary> [--entities entities.jsonl]
"""

import json
import struct
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hunk_parser import parse_file, HunkType
from kb_util import KB, read_string_at
from build_entities import _resolve_reloc_target


PROJECT_ROOT = Path(__file__).parent.parent


# ── KB-derived patterns ──────────────────────────────────────────────────

def _build_return_opcodes(kb_instructions: list) -> set[int]:
    """Build set of return instruction opcodes from KB.

    Scans all instructions for pc_effects.flow.type == "return" and
    constructs the fixed opcode from encoding bit fields.
    Only includes fully fixed opcodes (no variable fields).
    """
    opcodes = set()
    for inst in kb_instructions:
        flow = inst.get("pc_effects", {}).get("flow", {})
        if flow.get("type") != "return":
            continue
        enc = inst.get("encodings", [{}])[0]
        opcode = 0
        mask = 0
        for f in enc.get("fields", []):
            if f["name"] in ("0", "1"):
                bit = f["bit_lo"]
                mask |= 1 << bit
                if f["name"] == "1":
                    opcode |= 1 << bit
        if mask == 0xFFFF:  # all 16 bits fixed
            opcodes.add(opcode)
    return opcodes


def _build_unconditional_jump_opcodes(kb_instructions: list) -> set[int]:
    """Build set of unconditional non-return flow opcodes from KB.

    These are JMP/BRA-like instructions that end a block but aren't returns.
    Only includes opcodes where the upper bits are fixed (lower bits may
    contain EA or displacement fields).
    """
    patterns = []  # (opcode, mask) pairs
    for inst in kb_instructions:
        flow = inst.get("pc_effects", {}).get("flow", {})
        if flow.get("type") not in ("jump", "branch"):
            continue
        if flow.get("conditional"):
            continue
        enc = inst.get("encodings", [{}])[0]
        opcode = 0
        mask = 0
        for f in enc.get("fields", []):
            if f["name"] in ("0", "1"):
                bit = f["bit_lo"]
                mask |= 1 << bit
                if f["name"] == "1":
                    opcode |= 1 << bit
        if mask:
            patterns.append((opcode, mask))
    return patterns


# ── Hint types ───────────────────────────────────────────────────────────

def scan_string_tables(code: bytes, verified_strings: set[int],
                       code_regions: set[int]) -> list[dict]:
    """Find consecutive strings adjacent to verified string targets.

    Scans forward and backward from each verified string looking for
    adjacent null-terminated printable strings.  Only scans in data
    regions (not code).
    """
    hints = []
    seen = set(verified_strings)

    for start_addr in sorted(verified_strings):
        # Scan forward from end of verified string
        s = read_string_at(code, start_addr, max_len=200)
        if not s:
            continue
        pos = start_addr + len(s) + 1  # skip string + null

        while pos < len(code) and pos not in code_regions:
            # Skip alignment padding
            while pos < len(code) and code[pos] == 0:
                pos += 1
            if pos >= len(code) or pos in code_regions:
                break
            s = read_string_at(code, pos, max_len=200)
            if not s or len(s) < 4:
                break
            # Reject strings that are mostly non-alphabetic
            # (data bytes that happen to be in printable range)
            alpha = sum(1 for c in s if c.isalpha())
            if alpha < len(s) * 0.5:
                break
            if pos not in seen:
                seen.add(pos)
                hints.append({
                    "addr": pos,
                    "end": pos + len(s) + 1,
                    "type": "string_table",
                    "confidence": 0.7,
                    "text": s[:60],
                    "adjacent_to": start_addr,
                })
            pos += len(s) + 1

    return hints


def scan_orphan_relocs(reloc_offsets: set[int], code_regions: set[int],
                       code: bytes) -> list[dict]:
    """Find reloc offsets in data regions not covered by code blocks.

    These are pointer values embedded in data — likely pointer tables,
    vtable entries, or struct fields containing addresses.
    """
    hints = []
    for offset in sorted(reloc_offsets):
        if offset in code_regions:
            continue
        if offset + 4 > len(code):
            continue
        target = struct.unpack_from(">I", code, offset)[0]
        hints.append({
            "addr": offset,
            "end": offset + 4,
            "type": "orphan_reloc",
            "confidence": 0.9,
            "target": target,
        })
    return hints


def scan_trailing_returns(code: bytes, code_regions: set[int],
                          return_opcodes: set[int],
                          opword_bytes: int) -> list[dict]:
    """Find return instruction opcodes at end of unclassified regions.

    A return opcode in a data region followed by different data suggests
    a subroutine boundary.  The return opcode is from KB, not hardcoded.
    """
    hints = []
    for pos in range(0, len(code) - opword_bytes + 1, opword_bytes):
        if pos in code_regions:
            continue
        word = struct.unpack_from(">H", code, pos)[0]
        if word not in return_opcodes:
            continue
        # Check that preceding bytes are also in data region
        # (if the preceding byte is in code, this is just the end of
        # a known block, not a hint)
        if pos >= opword_bytes and (pos - opword_bytes) in code_regions:
            continue
        hints.append({
            "addr": pos,
            "end": pos + opword_bytes,
            "type": "trailing_return",
            "confidence": 0.5,
            "opcode": f"${word:04x}",
        })
    return hints


def scan_post_return_entries(code: bytes, code_regions: set[int],
                             return_opcodes: set[int],
                             opword_bytes: int) -> list[dict]:
    """Find word-aligned addresses immediately after return instructions.

    If a return opcode appears at address N, address N+opword_bytes
    is likely the start of the next subroutine — IF it's not already
    in a known code region.
    """
    hints = []
    for pos in range(0, len(code) - opword_bytes * 2 + 1, opword_bytes):
        word = struct.unpack_from(">H", code, pos)[0]
        if word not in return_opcodes:
            continue
        entry = pos + opword_bytes
        if entry in code_regions:
            continue
        if entry >= len(code):
            continue
        # The entry point should be decodable as an instruction
        # (we don't decode here — that's verification, not hinting)
        hints.append({
            "addr": entry,
            "end": entry,  # unknown extent
            "type": "post_return_entry",
            "confidence": 0.4,
            "after_return_at": pos,
        })
    return hints


# ── Main ─────────────────────────────────────────────────────────────────

def scan_hints(binary_path: str, entities_path: str) -> list[dict]:
    """Run all hint scanners on a binary + entities."""
    hf = parse_file(binary_path)
    with open(entities_path) as f:
        entities = [json.loads(line) for line in f if line.strip()]

    # Load KB data
    kb = KB()
    _, kb_instructions, meta = kb.by_name, None, kb.meta
    # Load full instruction list for opcode scanning
    kb_path = Path(__file__).resolve().parent.parent / "knowledge" / "m68k_instructions.json"
    with open(kb_path, encoding="utf-8") as f:
        kb_data = json.load(f)
    kb_instructions = kb_data["instructions"]

    return_opcodes = _build_return_opcodes(kb_instructions)
    opword_bytes = meta["opword_bytes"]

    all_hints = []

    for hunk in hf.hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            continue
        code = hunk.data

        # Build code region set from entities
        code_regions = set()
        verified_strings = set()
        for ent in entities:
            if ent.get("hunk") != hunk.index:
                continue
            addr = int(ent["addr"], 16)
            end = int(ent["end"], 16)
            if ent["type"] == "code":
                for a in range(addr, end):
                    code_regions.add(a)

        # Get verified strings from PC-relative targets in gen_disasm
        # For now, find strings referenced by labels in entities
        from m68k_executor import analyze
        from os_calls import get_platform_config, _SENTINEL_ALLOC_BASE

        platform = get_platform_config()
        init = analyze(code, base_addr=0, entry_points=[0],
                       propagate=True, platform=platform)
        alloc_limit = platform.get("_next_alloc_sentinel",
                                   _SENTINEL_ALLOC_BASE)
        for addr, (cpu, mem) in init["exit_states"].items():
            a6 = cpu.a[platform.get("_base_reg_num", 6)]
            if (a6.is_known
                    and _SENTINEL_ALLOC_BASE <= a6.concrete < alloc_limit):
                platform["initial_base_reg"] = (
                    platform.get("_base_reg_num", 6), a6.concrete)
                break

        reloc_targets = set()
        for reloc in hunk.relocs:
            for offset in reloc.offsets:
                target = _resolve_reloc_target(reloc, offset, code)
                if target is not None and 0 <= target < len(code):
                    reloc_targets.add(target)

        result = analyze(code, base_addr=0,
                         entry_points=sorted({0} | reloc_targets),
                         propagate=False, platform=platform)

        # Flow-verified blocks
        verified = set()
        work = [0]
        while work:
            a = work.pop()
            if a in verified or a not in result["blocks"]:
                continue
            verified.add(a)
            blk = result["blocks"][a]
            for succ in blk.successors:
                work.append(succ)
            for xref in blk.xrefs:
                if xref.type == "call":
                    work.append(xref.dst)

        # Build code_regions from flow-verified blocks
        code_regions = set()
        for a in verified:
            blk = result["blocks"][a]
            for p in range(blk.start, blk.end):
                code_regions.add(p)

        # Get PC-relative verified strings
        from gen_disasm import discover_pc_relative_targets
        pc_targets = discover_pc_relative_targets(
            {a: result["blocks"][a] for a in verified}, code, kb)
        verified_strings = {addr for addr, name in pc_targets.items()
                            if name.startswith("str_")}

        # Reloc offsets
        reloc_offsets = set()
        for reloc in hunk.relocs:
            for offset in reloc.offsets:
                reloc_offsets.add(offset)

        # Run scanners
        all_hints.extend(scan_string_tables(
            code, verified_strings, code_regions))
        all_hints.extend(scan_orphan_relocs(
            reloc_offsets, code_regions, code))
        all_hints.extend(scan_trailing_returns(
            code, code_regions, return_opcodes, opword_bytes))
        all_hints.extend(scan_post_return_entries(
            code, code_regions, return_opcodes, opword_bytes))

    # Sort by confidence (descending), then address
    all_hints.sort(key=lambda h: (-h["confidence"], h["addr"]))
    return all_hints


def main():
    parser = argparse.ArgumentParser(
        description="Scan binary for unverified hints")
    parser.add_argument("binary", help="Path to Amiga hunk executable")
    parser.add_argument("--entities", "-e",
                        default=str(PROJECT_ROOT / "entities.jsonl"),
                        help="Path to entities.jsonl")
    args = parser.parse_args()

    hints = scan_hints(args.binary, args.entities)

    # Summary
    by_type = {}
    for h in hints:
        by_type.setdefault(h["type"], []).append(h)

    print(f"{len(hints)} hints found:\n")
    for htype, hlist in sorted(by_type.items()):
        avg_conf = sum(h["confidence"] for h in hlist) / len(hlist)
        print(f"  {htype}: {len(hlist)} "
              f"(avg confidence {avg_conf:.2f})")

    # Show top hints
    print(f"\nTop hints:")
    for h in hints[:20]:
        extra = ""
        if "text" in h:
            extra = f' "{h["text"][:40]}"'
        elif "target" in h:
            extra = f" -> ${h['target']:04x}"
        elif "opcode" in h:
            extra = f" {h['opcode']}"
        print(f"  ${h['addr']:04x}: {h['type']} "
              f"(conf={h['confidence']:.1f}){extra}")


if __name__ == "__main__":
    main()
