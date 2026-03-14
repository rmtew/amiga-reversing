#!/usr/bin/env py.exe
"""Generate vasm-compatible .s file from entities.jsonl + binary.

Produces a reassemblable Motorola-syntax assembly file:
- Code entities: disassembled instructions with symbolic labels
- Data/unknown entities: dc.b hex dumps, dc.l at reloc offsets
- Labels at entity boundaries, branch targets, reloc targets
- Relocations converted to label references

Usage:
    python gen_disasm.py <binary> [--entities entities.jsonl] [--output disasm/out.s]
"""

import json
import re
import struct
import sys
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hunk_parser import parse_file, HunkType
from m68k_executor import analyze
from os_calls import get_platform_config, _SENTINEL_ALLOC_BASE
from build_entities import _resolve_reloc_target
from kb_util import KB, read_string_at


PROJECT_ROOT = Path(__file__).parent.parent


def load_entities(path: str) -> list[dict]:
    """Load entities from JSONL file."""
    entities = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entities.append(json.loads(line))
    return entities


def discover_pc_relative_targets(blocks: dict, code: bytes,
                                 kb: KB) -> dict[int, str]:
    """Discover PC-relative operand targets in flow-verified blocks.

    Handles both EA modes from KB ea_mode_encoding:
    - pcdisp d(PC): target = PC + opword_bytes + d (fully resolved)
    - pcindex d(PC,Xn): base = PC + opword_bytes + d (index unknown,
      but the base address IS statically known and should be labeled
      for readability — e.g. jump table base)

    Names targets based on content: string → str_XXXX, else pcref_XXXX.
    Target computation uses KB opword_bytes for PC offset.
    """
    # Match both d(pc) and d(pc,Xn) — extract displacement from either
    pc_re = re.compile(r'(-?\d+)\(pc[),]', re.IGNORECASE)

    # Build set of all instruction byte ranges to exclude targets
    # that fall inside instructions (e.g. jmp 0(pc,d0.w) where the
    # base address IS the extension word location).
    instr_ranges = set()
    for blk in blocks.values():
        for inst in blk.instructions:
            for a in range(inst.offset, inst.offset + inst.size):
                instr_ranges.add(a)

    targets = {}  # addr → name
    for blk in blocks.values():
        for inst in blk.instructions:
            text = inst.text.strip()
            parts = text.split(None, 1)
            if len(parts) < 2:
                continue
            m = pc_re.search(parts[1])
            if not m:
                continue
            disp = int(m.group(1))
            target = inst.offset + kb.opword_bytes + disp
            if target < 0 or target >= len(code) or target in targets:
                continue
            # Skip targets inside instruction bytes (encoding artifacts)
            if target in instr_ranges:
                continue
            # Name based on content at target
            s = read_string_at(code, target)
            if s and len(s) >= 3:
                targets[target] = f"str_{target:04x}"
            else:
                targets[target] = f"pcref_{target:04x}"
    return targets


def build_label_map(entities: list[dict], blocks: dict,
                    reloc_targets: set[int],
                    pc_targets: dict[int, str]) -> dict[int, str]:
    """Build addr→name label map from all sources.

    Label naming priority:
    1. Named entities: use their name
    2. Unnamed code entities: sub_XXXX
    3. Internal block targets: loc_XXXX
    4. Reloc targets: dat_XXXX
    5. PC-relative targets: str_XXXX or pcref_XXXX
    """
    labels = {}

    # Entity labels
    for ent in entities:
        addr = int(ent["addr"], 16)
        if ent.get("name"):
            labels[addr] = ent["name"]
        elif ent["type"] == "code":
            labels[addr] = f"sub_{addr:04x}"

    # Internal block targets (branch/call within subroutines)
    for addr in sorted(blocks):
        if addr not in labels:
            labels[addr] = f"loc_{addr:04x}"

    # Reloc targets that aren't already labelled
    for addr in sorted(reloc_targets):
        if addr not in labels:
            labels[addr] = f"dat_{addr:04x}"

    # PC-relative targets (strings, data tables referenced via d(PC))
    for addr, name in sorted(pc_targets.items()):
        if addr not in labels:
            labels[addr] = name

    return labels


def build_reloc_map(hunks, hunk_idx: int) -> dict[int, int]:
    """Build offset→target map from absolute reloc entries for a hunk.

    Uses relocation_semantics from hunk format KB to determine which
    reloc types are absolute (need label references in disassembly).
    """
    from hunk_parser import _HUNK_KB
    reloc_sem = _HUNK_KB.get("relocation_semantics", {})
    # Build set of absolute reloc type IDs from KB
    abs_types = set()
    for name, sem in reloc_sem.items():
        if sem.get("mode") == "absolute" and name in HunkType.__members__:
            abs_types.add(HunkType[name])

    reloc_map = {}
    for hunk in hunks:
        if hunk.index != hunk_idx:
            continue
        for reloc in hunk.relocs:
            try:
                rtype = HunkType(reloc.reloc_type)
            except ValueError:
                continue
            if rtype not in abs_types:
                continue
            # Get byte width from KB — error if missing
            sem = reloc_sem.get(rtype.name)
            if sem is None:
                raise KeyError(
                    f"relocation_semantics missing for {rtype.name}")
            nbytes = sem["bytes"]
            fmt = {4: ">I", 2: ">H"}.get(nbytes)
            if fmt is None:
                raise ValueError(
                    f"Unsupported reloc byte width {nbytes} for {rtype.name}")
            for offset in reloc.offsets:
                if offset + nbytes <= len(hunk.data):
                    target = struct.unpack_from(fmt, hunk.data, offset)[0]
                    reloc_map[offset] = target
    return reloc_map


def _is_valid_68000(text: str, kb: KB) -> bool:
    """Check if a disassembled instruction is valid for 68000.

    Uses KB processor_020 flag to reject 020+ instructions that indicate
    data bytes were incorrectly decoded as code.
    """
    parts = text.split()
    if not parts:
        return True
    mn = parts[0].split('.')[0].lower()
    ikb = kb.find(mn)
    if ikb is None:
        return True
    # KB processor_020 flag: instruction requires 68020+
    if ikb.get("processor_020"):
        return False
    return True


def replace_targets_in_text(text: str, inst_offset: int, inst_size: int,
                            labels: dict[int, str], reloc_map: dict[int, int],
                            opword_bytes: int) -> str:
    """Replace hex addresses in instruction text with label names.

    Handles:
    - Branch targets: bra.s $XXXX → bra.s label
    - Absolute addresses: jsr $XXXXXXXX → jsr label
    - PC-relative: lea NNN(pc),An → lea label(pc),An
    - Relocated immediates: move.l #$XXXX,An → move.l #label,An
    """
    parts = text.split(None, 1)
    if len(parts) < 2:
        return text
    mnemonic = parts[0]
    operands = parts[1]

    # Check all extension word offsets for relocations.
    # Handles both immediates (#$XXXX) and absolute addresses ($XXXXXXXX).
    for ext_off in range(inst_offset + opword_bytes,
                         inst_offset + inst_size):
        if ext_off not in reloc_map:
            continue
        target = reloc_map[ext_off]
        if target not in labels:
            continue
        lbl = labels[target]
        # Try immediate: #$XXXX → #label
        new_ops, n = re.subn(r'#\$[0-9a-fA-F]+', f'#{lbl}',
                             operands, count=1)
        if n:
            return f"{mnemonic} {new_ops}"
        # Try absolute address: $XXXXXXXX or $XXXX → label
        hex8 = f"${target:08x}"
        hex4 = f"${target:04x}"
        if hex8 in operands.lower():
            operands = re.sub(re.escape(hex8), lbl,
                              operands, count=1, flags=re.IGNORECASE)
            return f"{mnemonic} {operands}"
        if hex4 in operands.lower():
            operands = re.sub(re.escape(hex4), lbl,
                              operands, count=1, flags=re.IGNORECASE)
            return f"{mnemonic} {operands}"

    # PC-relative: NNN(pc) → label(pc) or NNN(pc,Xn) → label(pc,Xn).
    # For both pcdisp and pcindex modes, the base address PC + d is known.
    # The index register (if present) is preserved in the output.
    pc_match = re.search(r'(-?\d+)\(pc([),])', operands, re.IGNORECASE)
    if pc_match:
        disp = int(pc_match.group(1))
        target = inst_offset + opword_bytes + disp
        if target in labels:
            delim = pc_match.group(2)  # ')' for pcdisp, ',' for pcindex
            # Replace displacement with label, keep delimiter and rest
            operands = (operands[:pc_match.start()] +
                        f"{labels[target]}(pc{delim}" +
                        operands[pc_match.end():])
            return f"{mnemonic} {operands}"

    # Branch/jump targets: $XXXX at end of operand string
    hex_match = re.search(r'\$([0-9a-fA-F]{2,8})\s*$', operands)
    if hex_match:
        target = int(hex_match.group(1), 16)
        if target in labels:
            operands = operands[:hex_match.start()] + labels[target]
            return f"{mnemonic} {operands}"

    # DBcc targets: dbf d0,$56 — target after comma
    dbcc_match = re.search(r',\s*\$([0-9a-fA-F]{2,8})\s*$', operands)
    if dbcc_match:
        target = int(dbcc_match.group(1), 16)
        if target in labels:
            operands = operands[:dbcc_match.start()] + \
                f",{labels[target]}"
            return f"{mnemonic} {operands}"

    return text


def emit_data_region(f, code: bytes, start: int, end: int,
                     labels: dict[int, str], reloc_map: dict[int, int],
                     indent: str = "    "):
    """Emit a data/unknown region as dc.b/dc.l directives.

    At reloc offsets, emits dc.l with label reference.
    Otherwise emits dc.b with hex bytes (16 per line).
    """
    pos = start
    while pos < end:
        # Check for label at this position
        if pos != start and pos in labels:
            f.write(f"{labels[pos]}:\n")

        # Check for reloc at this position
        if pos in reloc_map and pos + 4 <= end:
            target = reloc_map[pos]
            if target in labels:
                f.write(f"{indent}dc.l    {labels[target]}\n")
            else:
                val = struct.unpack_from(">I", code, pos)[0]
                f.write(f"{indent}dc.l    ${val:08x}\n")
            pos += 4
            continue

        # Find how many bytes until next label or reloc or end
        chunk_end = end
        for a in range(pos + 1, end):
            if a in labels or a in reloc_map:
                chunk_end = a
                break

        # Emit dc.b in rows of 16
        chunk = code[pos:chunk_end]
        for i in range(0, len(chunk), 16):
            row = chunk[i:i+16]
            hex_vals = ",".join(f"${b:02x}" for b in row)
            f.write(f"{indent}dc.b    {hex_vals}\n")
        pos = chunk_end


def gen_disasm(binary_path: str, entities_path: str, output_path: str):
    """Main: generate vasm-compatible .s file from binary + entities.

    Uses the executor to get basic block boundaries (not linear disassembly)
    so embedded data within code entities is emitted as dc.b, not decoded
    as instructions.
    """
    print(f"Parsing {binary_path}...")
    hf = parse_file(binary_path)

    print(f"Loading entities from {entities_path}...")
    entities = load_entities(entities_path)

    kb = KB()

    for hunk in hf.hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            continue

        code = hunk.data
        code_size = len(code)
        hunk_entities = [e for e in entities if e.get("hunk") == hunk.index]
        hunk_entities.sort(key=lambda e: int(e["addr"], 16))

        print(f"Hunk #{hunk.index}: {code_size} bytes, "
              f"{len(hunk_entities)} entities")

        # Run executor to get basic blocks (code vs data boundaries)
        reloc_targets = set()
        for reloc in hunk.relocs:
            for offset in reloc.offsets:
                target = _resolve_reloc_target(reloc, offset, code)
                if target is not None and 0 <= target < code_size:
                    reloc_targets.add(target)

        platform = get_platform_config()
        # Discover base register from init pass (same as build_entities)
        init_result = analyze(code, base_addr=0, entry_points=[0],
                              propagate=True, platform=platform)
        alloc_limit = platform.get("_next_alloc_sentinel",
                                   _SENTINEL_ALLOC_BASE)
        base_reg_num = platform.get("_base_reg_num", 6)
        for addr, (cpu, mem) in init_result["exit_states"].items():
            val = cpu.a[base_reg_num]
            if (val.is_known
                    and _SENTINEL_ALLOC_BASE <= val.concrete < alloc_limit):
                platform["initial_base_reg"] = (base_reg_num, val.concrete)
                break

        all_ep = sorted({0} | reloc_targets)
        result = analyze(code, base_addr=0, entry_points=all_ep,
                         propagate=False, platform=platform)
        all_blocks = result["blocks"]

        # Filter to flow-verified blocks: reachable from address 0
        # through control flow edges (successors) AND call xrefs.
        # Reloc-target entry blocks with no predecessors may be data
        # pointers, not code — they're excluded unless reachable.
        verified = set()
        work = [0]
        while work:
            addr = work.pop()
            if addr in verified or addr not in all_blocks:
                continue
            verified.add(addr)
            blk = all_blocks[addr]
            for succ in blk.successors:
                work.append(succ)
            for xref in blk.xrefs:
                if xref.type == "call":
                    work.append(xref.dst)

        blocks = {a: all_blocks[a] for a in verified}
        code_addrs = set()
        for blk in blocks.values():
            for a in range(blk.start, blk.end):
                code_addrs.add(a)
        print(f"  {len(blocks)}/{len(all_blocks)} flow-verified blocks, "
              f"{len(code_addrs)}/{code_size} code bytes")

        # Build reloc map
        reloc_map = build_reloc_map(hf.hunks, hunk.index)
        reloc_target_set = set(reloc_map.values())
        print(f"  {len(reloc_map)} relocations")

        # Discover internal targets from blocks
        internal_targets = set()
        for blk in blocks.values():
            internal_targets.add(blk.start)
            for succ in blk.successors:
                internal_targets.add(succ)

        # Discover PC-relative targets (strings, data tables)
        pc_targets = discover_pc_relative_targets(blocks, code, kb)
        print(f"  {len(pc_targets)} PC-relative targets")

        # Build label map
        labels = build_label_map(
            hunk_entities,
            {t: None for t in internal_targets},
            reloc_target_set,
            pc_targets)
        print(f"  {len(labels)} labels")

        # Generate output
        print(f"Writing {output_path}...")
        with open(output_path, "w") as f:
            f.write("; Generated disassembly — vasm Motorola syntax\n")
            f.write("; Source: " + str(binary_path) + "\n")
            f.write(f"; {code_size} bytes, "
                    f"{len(hunk_entities)} entities, "
                    f"{len(blocks)} blocks\n")
            f.write("\n")
            f.write("    section code,code\n\n")

            instr_count = 0
            data_bytes = 0

            # Walk ALL bytes in order, emitting code or data
            pos = 0
            while pos < code_size:
                # Emit label if present
                if pos in labels:
                    f.write(f"{labels[pos]}:\n")

                if pos in blocks:
                    # This is a basic block — disassemble instructions
                    blk = blocks[pos]
                    for inst in blk.instructions:
                        # Internal label
                        if inst.offset != pos and inst.offset in labels:
                            f.write(f"{labels[inst.offset]}:\n")
                        if not _is_valid_68000(inst.text, kb):
                            # Invalid decode — emit as raw bytes
                            emit_data_region(f, code, inst.offset,
                                             inst.offset + inst.size,
                                             labels, reloc_map)
                            data_bytes += inst.size
                        else:
                            text = replace_targets_in_text(
                                inst.text, inst.offset, inst.size,
                                labels, reloc_map, kb.opword_bytes)
                            f.write(f"    {text}\n")
                            instr_count += 1
                    pos = blk.end
                elif pos in code_addrs:
                    # Inside a block but not at the start — shouldn't
                    # happen since we walk in order, skip
                    pos += 1
                else:
                    # Not in a block — emit as data until next block/label
                    data_end = pos + 1
                    while (data_end < code_size
                           and data_end not in blocks
                           and data_end not in labels):
                        data_end += 1
                    emit_data_region(f, code, pos, data_end,
                                     labels, reloc_map)
                    data_bytes += data_end - pos
                    pos = data_end

            print(f"  {instr_count} instructions, "
                  f"{data_bytes} data bytes emitted")

    print(f"\nDone: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate vasm-compatible .s file from binary + entities")
    parser.add_argument("binary", help="Path to Amiga hunk executable")
    parser.add_argument("--entities", "-e",
                        default=str(PROJECT_ROOT / "entities.jsonl"),
                        help="Path to entities.jsonl")
    parser.add_argument("--output", "-o",
                        default=str(PROJECT_ROOT / "disasm" / "genam.s"),
                        help="Output .s file path")
    args = parser.parse_args()

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    return gen_disasm(args.binary, args.entities, args.output)


if __name__ == "__main__":
    sys.exit(main() or 0)
