"""Analyze why the executor only reaches ~25.7% of GenAm's code.

Identifies:
1. Blocks ending with unresolved indirect jumps/calls (jump table dispatch)
2. Their last few instructions (looking for LEA + indexed JMP patterns)
3. Potential subroutines in uncovered regions (RTS/RTE scanning)
"""

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from m68k.hunk_parser import parse_file, HunkType as HT
from m68k.m68k_executor import analyze, _extract_mnemonic, _load_kb


def main():
    binary_path = Path(__file__).resolve().parent.parent / "resources" / "Amiga_Devpac_3_18" / "GenAm"
    hf = parse_file(binary_path)

    # Find the code hunk
    code_hunk = None
    for hunk in hf.hunks:
        if hunk.hunk_type == HT.HUNK_CODE:
            code_hunk = hunk
            break

    if code_hunk is None:
        print("ERROR: No code hunk found")
        sys.exit(1)

    code = code_hunk.data
    code_len = len(code)
    print(f"=== GenAm Code Analysis ===")
    print(f"Code hunk size: {code_len} bytes ({code_len:#x})")
    print()

    # Run the executor
    print("Running executor (analyze)...")
    result = analyze(code, base_addr=0)
    blocks = result["blocks"]

    # Calculate coverage
    covered_bytes = set()
    for block in blocks.values():
        for inst in block.instructions:
            for b in range(inst.offset, inst.offset + inst.size):
                covered_bytes.add(b)

    coverage_pct = len(covered_bytes) / code_len * 100
    print(f"Blocks discovered: {len(blocks)}")
    print(f"Call targets: {len(result['call_targets'])}")
    print(f"Branch targets: {len(result['branch_targets'])}")
    print(f"Covered bytes: {len(covered_bytes)} / {code_len} ({coverage_pct:.1f}%)")
    print()

    # ── 1. Find blocks ending with unresolved indirect jumps/calls ──
    kb_by_name, _, meta = _load_kb()
    cc_test_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})

    from m68k.m68k_executor import _find_kb_entry, _extract_branch_target

    indirect_blocks = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue
        last = block.instructions[-1]
        mn = _extract_mnemonic(last.text)
        kb_entry = _find_kb_entry(kb_by_name, mn, cc_test_defs, cc_aliases)
        if kb_entry is None:
            continue
        flow = kb_entry.get("pc_effects", {}).get("flow", {})
        flow_type = flow.get("type", "sequential")

        if flow_type in ("jump", "call"):
            target = _extract_branch_target(last, last.offset)
            if target is None:
                # Unresolved indirect jump/call
                indirect_blocks.append((addr, block, flow_type))

    print(f"{'='*60}")
    print(f"BLOCKS ENDING WITH UNRESOLVED INDIRECT JUMPS/CALLS: {len(indirect_blocks)}")
    print(f"{'='*60}")
    print()

    for addr, block, ftype in indirect_blocks:
        pred_str = ", ".join(f"${p:06x}" for p in block.predecessors) or "none"
        succ_str = ", ".join(f"${s:06x}" for s in block.successors) or "none"
        print(f"--- Block ${addr:06x} ({ftype}) pred=[{pred_str}] succ=[{succ_str}] ---")
        # Print last few instructions (up to 6)
        show_instrs = block.instructions[-6:]
        for inst in show_instrs:
            hex_bytes = " ".join(f"{b:02x}" for b in inst.raw[:10])
            print(f"  {inst.offset:06x}: {hex_bytes:30s} {inst.text}")
        print()

    # ── Categorize indirect jump patterns ──
    print(f"{'='*60}")
    print("INDIRECT JUMP PATTERN ANALYSIS")
    print(f"{'='*60}")
    print()

    pattern_counts = {}
    for addr, block, ftype in indirect_blocks:
        last = block.instructions[-1]
        text = last.text.strip().lower()
        # Classify the pattern
        if "(" in text:
            # Extract the addressing mode part
            parts = text.split(None, 1)
            if len(parts) > 1:
                operand = parts[1]
            else:
                operand = text
            pattern_counts.setdefault(operand, []).append(addr)
        else:
            pattern_counts.setdefault(text, []).append(addr)

    for pattern, addrs in sorted(pattern_counts.items(), key=lambda x: -len(x[1])):
        print(f"  {pattern}: {len(addrs)} occurrences")
        if len(addrs) <= 5:
            for a in addrs:
                print(f"    at ${a:06x}")
        else:
            for a in addrs[:3]:
                print(f"    at ${a:06x}")
            print(f"    ... and {len(addrs)-3} more")
    print()

    # ── Look for LEA + JMP patterns (jump tables) ──
    print(f"{'='*60}")
    print("DETAILED JUMP TABLE CANDIDATES (LEA + indexed JMP)")
    print(f"{'='*60}")
    print()

    jt_count = 0
    for addr, block, ftype in indirect_blocks:
        last = block.instructions[-1]
        text = last.text.strip().lower()
        # Look for patterns suggesting jump tables:
        # - JMP with PC-relative index: jmp (pc,dn) or similar
        # - LEA before JMP (An)
        has_lea = False
        lea_text = ""
        for inst in block.instructions[-4:]:
            if inst.text.strip().lower().startswith("lea"):
                has_lea = True
                lea_text = inst.text.strip()

        is_pcindex = "pc" in text and ("d" in text or "a" in text)
        is_indexed = any(f"d{i}" in text for i in range(8)) or any(f"a{i}" in text for i in range(8))

        if has_lea or is_pcindex or ("index" in text):
            jt_count += 1
            print(f"  Block ${addr:06x}:")
            for inst in block.instructions[-6:]:
                hex_bytes = " ".join(f"{b:02x}" for b in inst.raw[:10])
                print(f"    {inst.offset:06x}: {hex_bytes:30s} {inst.text}")
            if has_lea:
                print(f"    >> LEA found: {lea_text}")
            print()

    if jt_count == 0:
        print("  (No obvious LEA + JMP jump table patterns found)")
        print()

    # ── 2. Scan uncovered regions for subroutine boundaries ──
    print(f"{'='*60}")
    print("SCANNING UNCOVERED REGIONS")
    print(f"{'='*60}")
    print()

    # Build sorted list of covered ranges
    uncovered_ranges = []
    in_uncovered = False
    start = 0
    for i in range(code_len):
        if i not in covered_bytes:
            if not in_uncovered:
                start = i
                in_uncovered = True
        else:
            if in_uncovered:
                uncovered_ranges.append((start, i))
                in_uncovered = False
    if in_uncovered:
        uncovered_ranges.append((start, code_len))

    total_uncovered = sum(e - s for s, e in uncovered_ranges)
    print(f"Uncovered ranges: {len(uncovered_ranges)}")
    print(f"Total uncovered bytes: {total_uncovered}")
    print()

    # Show largest uncovered regions
    uncovered_ranges.sort(key=lambda x: -(x[1] - x[0]))
    print("Largest uncovered regions:")
    for s, e in uncovered_ranges[:15]:
        size = e - s
        print(f"  ${s:06x}-${e:06x}: {size} bytes ({size:#x})")
    print()

    # Scan for RTS ($4E75), RTE ($4E73) in uncovered regions
    rts_pattern = b'\x4e\x75'
    rte_pattern = b'\x4e\x73'
    rts_locs = []
    rte_locs = []

    for i in range(0, code_len - 1, 2):  # word-aligned
        if i in covered_bytes:
            continue
        word = code[i:i+2]
        if word == rts_pattern:
            rts_locs.append(i)
        elif word == rte_pattern:
            rte_locs.append(i)

    print(f"RTS ($4E75) in uncovered regions: {len(rts_locs)}")
    print(f"RTE ($4E73) in uncovered regions: {len(rte_locs)}")
    print()

    # Estimate subroutine count by looking for RTS boundaries
    # Each RTS likely ends a subroutine
    # Also scan for other common patterns
    bsr_count = 0
    jsr_count = 0
    movem_count = 0
    link_count = 0

    for i in range(0, code_len - 1, 2):
        if i in covered_bytes:
            continue
        word = struct.unpack_from(">H", code, i)[0]
        # BSR.W = $6100, BSR.B = $61xx (xx != 00, ff)
        if (word >> 8) == 0x61:
            bsr_count += 1
        # JSR = $4E80-$4EBF (mode 4, EA in bits 5-0)
        elif (word & 0xFFC0) == 0x4E80:
            jsr_count += 1
        # MOVEM = $48xx (register to memory) or $4Cxx (memory to register)
        elif (word & 0xFB80) == 0x4880:
            movem_count += 1
        # LINK = $4E50-$4E57
        elif (word & 0xFFF8) == 0x4E50:
            link_count += 1

    print("Common M68K patterns in uncovered regions:")
    print(f"  BSR (subroutine calls):  {bsr_count}")
    print(f"  JSR (subroutine calls):  {jsr_count}")
    print(f"  MOVEM (reg save/restore): {movem_count}")
    print(f"  LINK (frame setup):       {link_count}")
    print()

    # ── 3. Try to find subroutine entry points ──
    # Look backward from each RTS to find potential subroutine starts
    # A subroutine typically starts after a previous RTS or at an even address
    # after data
    print(f"{'='*60}")
    print("ESTIMATED UNREACHED SUBROUTINES")
    print(f"{'='*60}")
    print()

    # For each uncovered region, try to find word-aligned positions that
    # look like valid instruction starts (not data-like)
    potential_entries = []
    for rng_start, rng_end in uncovered_ranges:
        # Align to word boundary
        s = (rng_start + 1) & ~1
        # Try decoding from the start of each uncovered range
        # If it decodes successfully for a few instructions, it's likely code
        from m68k.m68k_disasm import _Decoder, _decode_one, DecodeError
        pos = s
        streak = 0
        entry = pos
        while pos < rng_end - 1:
            d = _Decoder(code, 0)
            d.pos = pos
            try:
                inst = _decode_one(d, None)
                if inst is None:
                    streak = 0
                    pos += 2
                    entry = pos
                    continue
                streak += 1
                if streak == 3:  # 3 valid instructions = likely code
                    potential_entries.append(entry)
                # Check if this is an RTS - start new potential entry
                if inst.raw[:2] == rts_pattern:
                    streak = 0
                    pos += inst.size
                    entry = pos
                    continue
                pos += inst.size
            except (DecodeError, struct.error, Exception):
                streak = 0
                pos += 2
                entry = pos

    print(f"Potential subroutine entry points in uncovered regions: {len(potential_entries)}")
    print()

    # Now re-run the executor with these additional entry points to see
    # how much more we'd cover
    if potential_entries:
        print("Re-running executor with additional entry points...")
        all_entries = [0] + potential_entries
        result2 = analyze(code, base_addr=0, entry_points=all_entries)
        blocks2 = result2["blocks"]

        covered2 = set()
        for block in blocks2.values():
            for inst in block.instructions:
                for b in range(inst.offset, inst.offset + inst.size):
                    covered2.add(b)

        coverage2_pct = len(covered2) / code_len * 100
        new_bytes = len(covered2) - len(covered_bytes)
        print(f"Blocks with extra entries: {len(blocks2)} (was {len(blocks)})")
        print(f"Coverage with extra entries: {len(covered2)} / {code_len} ({coverage2_pct:.1f}%)")
        print(f"New bytes covered: {new_bytes}")
        print()

        # Check how many of these new blocks end in indirect jumps
        indirect2 = 0
        for a in sorted(blocks2):
            block = blocks2[a]
            if not block.instructions:
                continue
            last = block.instructions[-1]
            mn = _extract_mnemonic(last.text)
            kb_entry = _find_kb_entry(kb_by_name, mn, cc_test_defs, cc_aliases)
            if kb_entry is None:
                continue
            flow = kb_entry.get("pc_effects", {}).get("flow", {})
            ft = flow.get("type", "sequential")
            if ft in ("jump", "call"):
                target = _extract_branch_target(last, last.offset)
                if target is None:
                    indirect2 += 1
        print(f"Indirect jumps/calls in expanded analysis: {indirect2}")
        print()

    # ── Summary ──
    print(f"{'='*60}")
    print("SUMMARY: WHY COVERAGE IS LOW")
    print(f"{'='*60}")
    print()
    print(f"1. The executor starts from offset 0 and follows control flow.")
    print(f"   It discovers {len(blocks)} blocks covering {coverage_pct:.1f}% of code.")
    print()
    print(f"2. {len(indirect_blocks)} blocks end with unresolved indirect jumps/calls.")
    print(f"   These are likely jump tables or vtable dispatches that the")
    print(f"   executor cannot follow because it doesn't know the register values.")
    print()
    print(f"3. In uncovered regions:")
    print(f"   - {len(rts_locs)} RTS instructions (subroutine boundaries)")
    print(f"   - {len(rte_locs)} RTE instructions (interrupt handlers)")
    print(f"   - {bsr_count} BSR, {jsr_count} JSR calls (nested subroutines)")
    print(f"   - {link_count} LINK instructions (function prologues)")
    print()
    print(f"4. ~{len(potential_entries)} potential subroutine entries found by")
    print(f"   scanning for valid instruction sequences in uncovered regions.")
    if potential_entries:
        print(f"   Adding them as entry points raises coverage to {coverage2_pct:.1f}%.")


if __name__ == "__main__":
    main()
