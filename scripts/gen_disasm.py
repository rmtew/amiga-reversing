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
from os_calls import (get_platform_config, _SENTINEL_ALLOC_BASE,
                      load_os_kb, identify_library_calls,
                      propagate_input_types)
from build_entities import _resolve_reloc_target
from m68k_executor import (_extract_branch_target, _extract_mnemonic,
                          _extract_size)
from kb_util import (KB, read_string_at, find_containing_sub,
                     decode_instruction_operands, decode_destination,
                     parse_reg_name)
from jump_tables import detect_jump_tables, resolve_indirect_targets, resolve_per_caller


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

    Decodes each instruction's EA from raw opcode bytes using KB encoding
    fields.  If the EA mode is pcdisp or pcindex, the Operand.value is
    the statically-known target address (PC + opword_bytes + displacement).

    Names targets based on content: string -> str_XXXX, else pcref_XXXX.
    """
    # Build set of all instruction byte ranges to exclude targets
    # that fall inside instructions (e.g. jmp 0(pc,d0.w) where the
    # base address IS the extension word location).
    instr_ranges = set()
    for blk in blocks.values():
        for inst in blk.instructions:
            for a in range(inst.offset, inst.offset + inst.size):
                instr_ranges.add(a)

    targets = {}  # addr -> name
    for blk in blocks.values():
        for inst in blk.instructions:
            mn = _extract_mnemonic(inst.text)
            inst_kb = kb.find(mn)
            if inst_kb is None:
                continue
            sz = _extract_size(inst.text)
            decoded = decode_instruction_operands(
                inst.raw, inst_kb, kb.meta, sz, inst.offset)
            # Check both ea_op and dst_op for PC-relative modes
            for op in (decoded["ea_op"], decoded["dst_op"]):
                if op is None:
                    continue
                if op.mode not in ("pcdisp", "pcindex"):
                    continue
                target = op.value
                if target is None:
                    continue
                if target < 0 or target >= len(code) or target in targets:
                    continue
                if target in instr_ranges:
                    continue
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


def _is_valid_encoding(text: str, raw: bytes, offset: int, kb: KB) -> bool:
    """Check if instruction's EA mode and size are valid per KB constraints.

    Validates:
    - EA mode is in the instruction's allowed ea_modes (ea/src/dst)
    - An with an_sizes constraint rejects invalid sizes
    - An as source rejects byte size (architectural: no byte ops on An)

    KB ea_modes has three possible keys:
    - "ea": single EA operand (JSR, LEA, CLR, etc.)
    - "src"/"dst": separate source and destination modes (MOVE)
    """
    mn = _extract_mnemonic(text)
    if not mn:
        return True
    ikb = kb.find(mn)
    if ikb is None:
        return True
    ea_modes = ikb.get("ea_modes", {})
    if not ea_modes:
        return True
    sz = _extract_size(text)
    decoded = decode_instruction_operands(raw, ikb, kb.meta, sz, offset)
    ea_op = decoded["ea_op"]
    dst_op = decoded["dst_op"]

    # Check ea_op against allowed modes
    if ea_op and ea_op.mode:
        if "ea" in ea_modes:
            if ea_op.mode not in ea_modes["ea"]:
                return False
        elif "src" in ea_modes:
            if ea_op.mode not in ea_modes["src"]:
                return False
        elif "dst" in ea_modes:
            if ea_op.mode not in ea_modes["dst"]:
                return False

    # Check dst_op against allowed dst modes
    if dst_op and dst_op.mode and "dst" in ea_modes:
        if dst_op.mode not in ea_modes["dst"]:
            return False

    # An size restriction from KB constraint (ADDQ/SUBQ: no byte to An)
    an_sizes = ikb.get("constraints", {}).get("an_sizes")
    if an_sizes and sz:
        for op in (ea_op, dst_op):
            if op and op.mode == "an" and sz not in an_sizes:
                return False

    # Architectural: no byte-size operations on address registers.
    # From KB ea_mode_sizes: An only supports word and long.
    if sz == "b":
        ea_mode_sizes = kb.meta.get("ea_mode_sizes", {})
        an_valid = ea_mode_sizes.get("an", ["w", "l"])
        for op in (ea_op, dst_op):
            if op and op.mode == "an" and "b" not in an_valid:
                return False

    return True


def _has_valid_branch_target(inst, kb: KB) -> bool:
    """Check if branch/jump target is word-aligned.

    Odd branch targets indicate data bytes mis-decoded as branch
    instructions. Alignment requirement from KB opword_bytes.
    Only checks instructions whose KB flow type is branch, jump, or
    call — other instructions are not branches and always pass.
    """
    mn = _extract_mnemonic(inst.text)
    if mn:
        ikb = kb.find(mn)
        if ikb:
            flow = ikb.get("pc_effects", {}).get("flow", {})
            ftype = flow.get("type")
            if ftype not in ("branch", "jump", "call"):
                return True  # not a branch instruction
    try:
        target = _extract_branch_target(inst, inst.offset)
    except (struct.error, IndexError):
        return False  # can't decode = invalid
    if target is None:
        return True  # indirect target, can't validate statically
    return target % kb.opword_bytes == 0


def _get_processor_min(text: str, kb: KB) -> str:
    """Get minimum processor for instruction from KB.

    Returns "68000" for base 68000 instructions, or the minimum
    processor (e.g. "68010", "68020", "68040") for later architectures.

    Uses two KB fields:
    - processor_min (instruction level): for entirely non-68000 instructions
    - processor_020 (variant level): for mixed instructions where only some
      variants (e.g. DIVSL, EXTB) require 68020+
    """
    mn = _extract_mnemonic(text)
    if not mn:
        return "68000"
    ikb = kb.find(mn)
    if ikb is None:
        return "68000"
    # Instruction-level processor_min (e.g. BFINS -> 68020)
    pmin = ikb.get("processor_min", "68000")
    if pmin != "68000":
        return pmin
    # Variant-level processor_020 (e.g. DIVSL is 020+ but parent DIVS is 68000)
    mn_upper = mn.upper()
    for v in ikb.get("variants", []):
        if v["mnemonic"].upper() == mn_upper and v.get("processor_020"):
            return "68020"
    return "68000"


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


def replace_struct_fields(text: str, inst_offset: int,
                          struct_map: dict[int, dict],
                          used_structs: set[str]) -> str:
    """Replace d(An) displacements with struct field names.

    When a register at this instruction offset is known to hold a struct
    pointer, numeric displacements that match field offsets are replaced
    with the field name: 18(a1) -> IS_CODE(a1).

    Adds used struct names to used_structs for INCLUDE generation.

    struct_map: {inst_offset: {reg: {"struct": name, "fields": {off: name}}}}
    """
    if inst_offset not in struct_map:
        return text
    reg_types = struct_map[inst_offset]

    def _replace_disp(m):
        disp = int(m.group(1))
        reg = m.group(2).lower()
        rest = m.group(3)  # ')' or ',Xn...'
        if reg in reg_types:
            field_name = reg_types[reg]["fields"].get(disp)
            if field_name:
                used_structs.add(reg_types[reg]["struct"])
                return f"{field_name}({m.group(2)}{rest}"
        return m.group(0)

    parts = text.split(None, 1)
    if len(parts) < 2:
        return text
    new_ops = re.sub(r'(-?\d+)\((a\d)([),])', _replace_disp, parts[1])
    if new_ops != parts[1]:
        return f"{parts[0]} {new_ops}"
    return text


def _is_printable_ascii(b: int) -> bool:
    """Check if a byte is printable ASCII (space through tilde)."""
    return 0x20 <= b <= 0x7E


def _try_read_string(code: bytes, pos: int, end: int) -> str | None:
    """Try to read a null-terminated ASCII string at pos.

    Returns the string if valid (>=4 printable chars + null terminator),
    or None.  Allows tab ($09) and newline ($0A) within strings.
    """
    chars = []
    i = pos
    while i < end:
        b = code[i]
        if b == 0:
            # Null terminator — valid string if long enough
            if len(chars) >= 4:
                return "".join(chars)
            return None
        if _is_printable_ascii(b) or b in (0x09, 0x0A):
            chars.append(chr(b))
        else:
            return None
        i += 1
    return None


def _emit_string(f, s: str, indent: str):
    """Emit a null-terminated string as dc.b with vasm quoting."""
    # vasm Motorola syntax: dc.b "text",0
    # Escape special chars: split on non-printable, emit as mixed
    parts = []
    current = []
    for ch in s:
        if _is_printable_ascii(ord(ch)) and ch != '"':
            current.append(ch)
        else:
            if current:
                parts.append('"' + "".join(current) + '"')
                current = []
            parts.append(f"${ord(ch):02x}")
    if current:
        parts.append('"' + "".join(current) + '"')
    parts.append("0")  # null terminator
    f.write(f"{indent}dc.b    {','.join(parts)}\n")


def emit_data_region(f, code: bytes, start: int, end: int,
                     labels: dict[int, str], reloc_map: dict[int, int],
                     string_addrs: set[int], indent: str = "    "):
    """Emit a data/unknown region as structured directives.

    Classification priority at each position:
    1. Relocated longword → dc.l label
    2. Verified string (at a labeled PC-relative target) → dc.b "text",0
    3. Zero padding (4+ consecutive zero bytes) → dcb.b N,0
    4. Raw bytes → dc.b hex dump
    """
    pos = start
    while pos < end:
        # Emit label
        if pos != start and pos in labels:
            f.write(f"{labels[pos]}:\n")

        # 1. Relocated longword
        if pos in reloc_map and pos + 4 <= end:
            target = reloc_map[pos]
            if target in labels:
                f.write(f"{indent}dc.l    {labels[target]}\n")
            else:
                val = struct.unpack_from(">I", code, pos)[0]
                f.write(f"{indent}dc.l    ${val:08x}\n")
            pos += 4
            continue

        # 2. Verified string at a known PC-relative target
        if pos in string_addrs:
            s = _try_read_string(code, pos, end)
            if s:
                _emit_string(f, s, indent)
                pos += len(s) + 1  # string + null
                continue

        # 3. Zero padding (4+ consecutive zero bytes)
        if code[pos] == 0:
            zero_end = pos + 1
            while zero_end < end and code[zero_end] == 0:
                # Stop at labels and relocs
                if zero_end in labels or zero_end in reloc_map:
                    break
                zero_end += 1
            count = zero_end - pos
            if count >= 4:
                f.write(f"{indent}dcb.b   {count},0\n")
                pos = zero_end
                continue

        # 4. Raw bytes until next boundary
        chunk_end = pos + 1
        while chunk_end < end:
            if (chunk_end in labels or chunk_end in reloc_map
                    or chunk_end in string_addrs):
                break
            # Stop before zero runs of 4+
            if (code[chunk_end] == 0 and chunk_end + 3 < end
                    and all(code[chunk_end + i] == 0 for i in range(4))):
                break
            chunk_end += 1

        chunk = code[pos:chunk_end]
        for i in range(0, len(chunk), 16):
            row = chunk[i:i + 16]
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
        # Discover base register + init memory from init pass
        init_result = analyze(code, base_addr=0, entry_points=[0],
                              propagate=True, platform=platform)
        alloc_limit = platform["_next_alloc_sentinel"]
        base_reg_num = platform["_base_reg_num"]
        best_addr = None
        best_slots = 0
        for addr, (cpu, mem) in init_result["exit_states"].items():
            val = cpu.a[base_reg_num]
            if (val.is_known
                    and _SENTINEL_ALLOC_BASE <= val.concrete < alloc_limit):
                if best_addr is None:
                    platform["initial_base_reg"] = (
                        base_reg_num, val.concrete)
                slots = sum(1 for a in mem._bytes
                            if _SENTINEL_ALLOC_BASE <= a < alloc_limit)
                if slots > best_slots:
                    best_slots = slots
                    best_addr = addr
        if best_addr is not None:
            _, init_mem = init_result["exit_states"][best_addr]
            platform["_initial_mem"] = init_mem

        # Core analysis with jump table discovery loop.
        # Iteratively adds jump table targets and indirect targets
        # as entry points until no new targets are found.
        core_entries = {0}
        jt_list = []
        for _ in range(10):
            result = analyze(code, base_addr=0,
                             entry_points=sorted(core_entries),
                             propagate=True, platform=platform)
            added = 0
            jt_list = detect_jump_tables(result["blocks"], code,
                                         base_addr=0)
            for t in jt_list:
                for tgt in t["targets"]:
                    if tgt not in core_entries:
                        core_entries.add(tgt)
                        added += 1
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
                    code, code_size, platform=platform):
                if r["target"] not in core_entries:
                    core_entries.add(r["target"])
                    added += 1
            if not added:
                break
        blocks = result["blocks"]
        code_addrs = set()
        for blk in blocks.values():
            for a in range(blk.start, blk.end):
                code_addrs.add(a)
        print(f"  {len(blocks)} core blocks, "
              f"{len(code_addrs)}/{code_size} code bytes")

        # Hint blocks: reloc targets + scan, separate discovery.
        # Emitted as unverified disassembly (readable but not trusted).
        from subroutine_scan import scan_and_score
        hint_entries = reloc_targets - set(blocks.keys())
        hint_blocks: dict = {}
        if hint_entries:
            hint_r = analyze(code, base_addr=0,
                             entry_points=sorted(hint_entries),
                             propagate=False)
            hint_blocks = {a: b for a, b in hint_r["blocks"].items()
                           if a not in blocks and a not in code_addrs}
        scan_cands = scan_and_score(
            blocks, code, reloc_targets,
            result.get("call_targets", set()))
        scan_entries = {c["addr"] for c in scan_cands
                        if c["addr"] not in blocks
                        and c["addr"] not in hint_blocks}
        if scan_entries:
            scan_r = analyze(code, base_addr=0,
                             entry_points=sorted(scan_entries),
                             propagate=False)
            for a, b in scan_r["blocks"].items():
                if (a not in blocks and a not in code_addrs
                        and a not in hint_blocks):
                    hint_blocks[a] = b

        hint_addrs = set()
        for blk in hint_blocks.values():
            for a in range(blk.start, blk.end):
                hint_addrs.add(a)
        if hint_blocks:
            print(f"  {len(hint_blocks)} hint blocks, "
                  f"{len(hint_addrs)} hint bytes")

        # Build reloc map
        reloc_map = build_reloc_map(hf.hunks, hunk.index)
        reloc_target_set = set(reloc_map.values())
        print(f"  {len(reloc_map)} relocations")

        # Discover internal branch targets from blocks.
        # A label is needed only at addresses that are branched or
        # jumped to — not at block splits caused by fallthrough.
        # Collect all non-fallthrough successors (branch targets),
        # then label block starts only if something branches to them.
        branch_targets = set()
        for blk in blocks.values():
            for succ in blk.successors:
                if succ != blk.end:
                    branch_targets.add(succ)
        internal_targets = branch_targets | core_entries

        # Discover PC-relative targets (strings, data tables)
        pc_targets = discover_pc_relative_targets(blocks, code, kb)
        # Also discover from hint blocks so their d(PC) references
        # get labels and assemble without absolute displacement warnings.
        hint_pc = discover_pc_relative_targets(hint_blocks, code, kb)
        for addr, name in hint_pc.items():
            if addr not in pc_targets:
                pc_targets[addr] = name
        # String addresses: only PC-relative-verified targets
        string_addrs = {addr for addr, name in pc_targets.items()
                        if name.startswith("str_")}
        print(f"  {len(pc_targets)} PC-relative targets "
              f"({len(string_addrs)} verified strings)")

        # Build jump table metadata for structured emission.
        # Uses jt_list captured from the discovery loop (final
        # iteration's tables match the final blocks).
        jt_regions = {}  # table_addr -> {base_addr, entries, pattern}
        jt_target_sources = defaultdict(list)  # target -> [base_label]
        for t in jt_list:
            tbl_addr = t["addr"]
            if t["pattern"] == "pc_inline_dispatch":
                # BRA instruction entries — emitted as disassembled code.
                # The dispatch block ends after the JMP instruction;
                # use that as the region start so the walk loop finds it.
                dispatch_blk = blocks.get(t["dispatch_block"])
                if dispatch_blk is None:
                    continue
                region_start = dispatch_blk.end
                jt_regions[region_start] = {
                    "pattern": "pc_inline_dispatch",
                    "table_end": t["table_end"],
                    "targets": t["targets"],
                }
            else:
                jt_regions[tbl_addr] = {
                    "base_addr": t["base_addr"],
                    "entries": [(tbl_addr + i * 2, tgt)
                                for i, tgt in enumerate(t["targets"])],
                    "pattern": t["pattern"],
                    "table_end": t["table_end"],
                }
        if jt_regions:
            print(f"  {len(jt_regions)} jump tables for structured emission")

        # Build label map
        labels = build_label_map(
            hunk_entities,
            {t: None for t in internal_targets},
            reloc_target_set,
            pc_targets)
        # Ensure jump table targets and base addresses have labels
        for tbl_addr, jt in jt_regions.items():
            if jt["pattern"] == "pc_inline_dispatch":
                # Inline BRA targets just need target labels
                for tgt in jt["targets"]:
                    if tgt not in labels:
                        labels[tgt] = f"loc_{tgt:04x}"
                continue
            if tbl_addr not in labels:
                labels[tbl_addr] = f"jt_{tbl_addr:04x}"
            base = jt["base_addr"]
            if base is not None and base not in labels:
                labels[base] = f"loc_{base:04x}"
            for _entry_addr, tgt in jt["entries"]:
                if tgt not in labels:
                    labels[tgt] = f"loc_{tgt:04x}"
        # Populate jt_target_sources now that labels exist
        for tbl_addr, jt in jt_regions.items():
            if jt["pattern"] == "pc_inline_dispatch":
                continue
            base = jt["base_addr"]
            base_label = labels[base] if base is not None else None
            jt["base_label"] = base_label
            source = base_label or labels[tbl_addr]
            for _entry_addr, tgt in jt["entries"]:
                if source not in jt_target_sources[tgt]:
                    jt_target_sources[tgt].append(source)

        # Add hint block labels (don't override existing labels)
        for addr in sorted(hint_blocks):
            if addr not in labels:
                labels[addr] = f"hint_{addr:04x}"
            # Also add labels for hint block successors
            blk = hint_blocks[addr]
            for succ in blk.successors:
                if succ == blk.end:
                    continue  # fallthrough, no label needed
                if succ not in labels:
                    if succ in hint_blocks:
                        labels[succ] = f"hint_{succ:04x}"
                    elif succ in code_addrs:
                        labels[succ] = f"loc_{succ:04x}"
        print(f"  {len(labels)} labels")

        # Build struct type map for displacement substitution.
        # Run library call identification on verified blocks, then
        # backward-propagate struct types from call inputs.
        os_kb = load_os_kb()
        lib_calls = identify_library_calls(
            blocks, code, os_kb, result.get("exit_states", {}),
            result.get("call_targets", set()), platform)
        struct_map = propagate_input_types(blocks, lib_calls, os_kb)
        if struct_map:
            print(f"  {len(struct_map)} instructions with struct type info")

        # Build LVO symbol substitutions from resolved library calls.
        # Two patterns:
        # 1. Direct: jsr -60(a6) -> jsr _LVOOpenLibrary(a6)
        # 2. Dispatch: moveq #-60,d0 -> moveq #_LVOOutput,d0
        # Collect all _LVO EQUs needed, grouped by library.
        lvo_equs: dict[str, dict[int, str]] = {}  # lib -> {lvo: symbol}
        # Map instruction offset -> (old_text_fragment, new_text_fragment)
        lvo_substitutions: dict[int, tuple[str, str]] = {}

        sorted_code_ents = sorted(
            [{"addr": int(e["addr"], 16), "end": int(e["end"], 16)}
             for e in hunk_entities if e["type"] == "code"],
            key=lambda s: s["addr"])

        for call in lib_calls:
            lib = call.get("library")
            func = call.get("function")
            lvo = call.get("lvo")
            if not lib or not func or lvo is None or lib == "unknown":
                continue
            if func.startswith("LVO_"):
                continue  # unresolved

            sym = f"_LVO{func}"
            lvo_equs.setdefault(lib, {})[lvo] = sym

            if "dispatch" in call:
                # Dispatch call: find the moveq/move that sets D0
                # in the caller block before the BSR to the dispatcher.
                caller_blk = blocks.get(call["addr"])
                if not caller_blk:
                    continue
                disp_sub = find_containing_sub(
                    call["dispatch"], sorted_code_ents)
                if disp_sub is None:
                    continue
                # Find BSR/JSR to dispatch sub, then scan backward
                # for the instruction that sets D0 to the LVO value.
                for i, inst in enumerate(caller_blk.instructions):
                    target = _extract_branch_target(inst, inst.offset)
                    if target != disp_sub:
                        continue
                    # Scan backward for moveq/move #lvo,d0
                    for j in range(i - 1, -1, -1):
                        prev = caller_blk.instructions[j]
                        prev_mn = _extract_mnemonic(prev.text)
                        prev_kb = kb.find(prev_mn)
                        if prev_kb is None:
                            continue
                        prev_sz = _extract_size(prev.text)
                        prev_dec = decode_instruction_operands(
                            prev.raw, prev_kb, kb.meta,
                            prev_sz, prev.offset)
                        if prev_dec["imm_val"] is None:
                            continue
                        # Check if the immediate matches the LVO
                        # (compare as signed 32-bit)
                        pv = prev_dec["imm_val"]
                        if pv >= 0x80000000:
                            pv_signed = pv - 0x100000000
                        else:
                            pv_signed = pv
                        if pv_signed == lvo:
                            # Extract literal #value text for
                            # replacement. Detection was KB-driven.
                            imm_m = re.search(r'#(\$?-?[0-9a-fA-F]+)',
                                              prev.text)
                            if imm_m:
                                lvo_substitutions[prev.offset] = (
                                    f"#{imm_m.group(1)}", f"#{sym}")
                            break
                    break
            else:
                # Direct call: jsr lvo(a6)
                lvo_substitutions[call["addr"]] = (
                    f"{lvo}(", f"{sym}(")

        lvo_count = sum(len(v) for v in lvo_equs.values())
        if lvo_count:
            print(f"  {lvo_count} LVO symbols "
                  f"({', '.join(sorted(lvo_equs))})")

        # Build argument constant substitutions from OS KB
        # constant_domains.  For each resolved call, find instructions
        # that set input registers to immediate values matching known
        # constants for that function.
        arg_equs: dict[str, int] = {}  # constant_name -> value
        arg_substitutions: dict[int, tuple[str, str]] = {}
        const_domains = os_kb["_meta"]["constant_domains"]
        all_consts = os_kb.get("constants", {})
        # Build per-function value->name map from domains
        func_const_map: dict[str, dict[int, str]] = {}
        for func_name, const_names in const_domains.items():
            vmap = {}
            for cn in const_names:
                cv = all_consts.get(cn, {}).get("value")
                if cv is not None:
                    vmap[cv] = cn
            if vmap:
                func_const_map[func_name] = vmap

        for call in lib_calls:
            func_name = call.get("function")
            if not func_name or func_name.startswith("LVO_"):
                continue
            vmap = func_const_map.get(func_name)
            if not vmap:
                continue
            lib = call["library"]
            func = os_kb["libraries"].get(lib, {}).get(
                "functions", {}).get(func_name, {})
            inputs = func.get("inputs", [])
            if not inputs:
                continue

            # Find the block containing the call
            blk_addr = call["block"]
            blk = blocks.get(blk_addr)
            if not blk:
                continue

            # Find the call instruction index
            call_idx = None
            call_addr = call["addr"]
            # For dispatch calls, find the BSR to the dispatcher
            if "dispatch" in call:
                disp_sub = find_containing_sub(
                    call["dispatch"], sorted_code_ents)
                for ci, inst in enumerate(blk.instructions):
                    if _extract_branch_target(inst, inst.offset) == disp_sub:
                        call_idx = ci
                        break
            else:
                for ci, inst in enumerate(blk.instructions):
                    if inst.offset == call_addr:
                        call_idx = ci
                        break
            if call_idx is None:
                continue

            # For each input register, scan backward for immediate set
            for inp in inputs:
                reg = inp["reg"].lower()
                reg_mode, reg_n = parse_reg_name(reg)
                # Scan backward from call for #imm,reg
                for j in range(call_idx - 1, -1, -1):
                    prev = blk.instructions[j]
                    prev_mn = _extract_mnemonic(prev.text)
                    prev_kb = kb.find(prev_mn)
                    if prev_kb is None:
                        continue
                    prev_sz = _extract_size(prev.text)
                    prev_dec = decode_instruction_operands(
                        prev.raw, prev_kb, kb.meta,
                        prev_sz, prev.offset)
                    if prev_dec["imm_val"] is None:
                        continue
                    # Determine destination register from decoded operands
                    dst = decode_destination(
                        prev.raw, prev_kb, kb.meta,
                        prev_sz, prev.offset)
                    if dst is None:
                        continue
                    dst_mode, dst_num = dst
                    if dst_mode != reg_mode or dst_num != reg_n:
                        continue
                    imm_val = prev_dec["imm_val"]
                    # Try both unsigned and signed forms for lookup,
                    # since KB constants may use signed values (-2)
                    # while decoded immediates are unsigned 32-bit.
                    const_name = vmap.get(imm_val)
                    if const_name is None and imm_val >= 0x80000000:
                        const_name = vmap.get(
                            imm_val - 0x100000000)
                    if const_name:
                        # Store signed value for EQU output
                        equ_val = imm_val
                        if equ_val >= 0x80000000:
                            equ_val = imm_val - 0x100000000
                        arg_equs[const_name] = equ_val
                        # Extract the literal #value text from the
                        # instruction for text replacement.  The
                        # detection was KB-driven; this extracts the
                        # display form for substitution only.
                        imm_m = re.search(r'#(\$?-?[0-9a-fA-F]+)',
                                          prev.text)
                        if imm_m:
                            arg_substitutions[prev.offset] = (
                                f"#{imm_m.group(1)}",
                                f"#{const_name}")
                    break  # stop scanning for this register

        if arg_substitutions:
            print(f"  {len(arg_substitutions)} argument constant "
                  f"substitutions")

        # Build app memory offset EQUs from init memory tags.
        app_offsets: dict[int, str] = {}
        base_info = platform.get("initial_base_reg")
        init_mem = platform.get("_initial_mem")
        if base_info and init_mem:
            base_concrete = base_info[1]
            base_reg_num = base_info[0]
            for (addr, _nbytes), tag in init_mem._tags.items():
                if not tag or "library_base" not in tag:
                    continue
                offset = addr - base_concrete
                lib_name = tag["library_base"]
                base_name = lib_name.rsplit(".", 1)[0]
                sym = re.sub(r'[^a-z0-9]+', '_', base_name.lower())
                app_offsets[offset] = f"app_{sym}_base"
        if app_offsets:
            print(f"  {len(app_offsets)} app memory offset symbols")

        # Generate output
        print(f"Writing {output_path}...")
        used_structs = set()  # struct names used in field substitutions
        with open(output_path, "w") as f:
            # Header
            f.write("; Generated disassembly -- vasm Motorola syntax\n")
            f.write("; Source: " + str(binary_path) + "\n")
            f.write(f"; {code_size} bytes, "
                    f"{len(hunk_entities)} entities, "
                    f"{len(blocks)} blocks\n")
            f.write("\n")

            # LVO EQUs grouped by library
            for lib_name in sorted(lvo_equs):
                f.write(f"; LVO offsets: {lib_name}\n")
                by_lvo = lvo_equs[lib_name]
                for lvo_val in sorted(by_lvo):
                    f.write(f"{by_lvo[lvo_val]}\tEQU\t{lvo_val}\n")
                f.write("\n")

            # Argument constant EQUs
            if arg_equs:
                f.write("; OS function argument constants\n")
                for name in sorted(arg_equs):
                    f.write(f"{name}\tEQU\t{arg_equs[name]}\n")
                f.write("\n")

            # App memory offset EQUs
            if app_offsets:
                f.write("; App memory offsets (base register "
                        f"A{base_info[0]})\n")
                for off in sorted(app_offsets):
                    f.write(f"{app_offsets[off]}\tEQU\t{off}\n")
                f.write("\n")

            f.write("    section code,code\n\n")

            instr_count = 0
            data_bytes = 0

            def _emit_label(addr):
                """Emit a label, with jt comment if it's a jump table target."""
                lbl = labels[addr]
                sources = jt_target_sources.get(addr)
                if sources:
                    comment = ", ".join(sources)
                    f.write(f"{lbl}: ; jt: {comment}\n")
                else:
                    f.write(f"{lbl}:\n")

            # Walk ALL bytes in order, emitting code or data
            pos = 0
            while pos < code_size:
                # Emit label if present
                if pos in labels:
                    _emit_label(pos)

                if pos in blocks:
                    # This is a basic block — disassemble instructions
                    blk = blocks[pos]
                    for inst in blk.instructions:
                        # Internal label
                        if inst.offset != pos and inst.offset in labels:
                            _emit_label(inst.offset)
                        if (not _is_valid_encoding(inst.text, inst.raw,
                                                   inst.offset, kb)
                                or not _has_valid_branch_target(inst, kb)):
                            emit_data_region(f, code, inst.offset,
                                             inst.offset + inst.size,
                                             labels, reloc_map,
                                             string_addrs)
                            data_bytes += inst.size
                            continue
                        text = replace_targets_in_text(
                                inst.text, inst.offset, inst.size,
                                labels, reloc_map, kb.opword_bytes)
                        text = replace_struct_fields(
                                text, inst.offset, struct_map,
                                used_structs)
                        # Substitute app memory offsets
                        if app_offsets and base_info:
                            brn = base_info[0]
                            for off, sym in app_offsets.items():
                                text = text.replace(
                                    f"{off}(a{brn})",
                                    f"{sym}(a{brn})")
                        # Substitute LVO constants
                        sub = lvo_substitutions.get(inst.offset)
                        if sub:
                            text = text.replace(sub[0], sub[1])
                        # Substitute argument constants
                        sub = arg_substitutions.get(inst.offset)
                        if sub:
                            text = text.replace(sub[0], sub[1])
                        pmin = _get_processor_min(inst.text, kb)
                        if pmin != "68000":
                            f.write(f"    {text} ; {pmin}+\n")
                        else:
                            f.write(f"    {text}\n")
                        instr_count += 1
                    pos = blk.end
                elif pos in code_addrs:
                    # Inside a block but not at the start — skip
                    pos += 1
                elif pos in hint_blocks:
                    # Hint block: emit as unverified disassembly only if
                    # ALL validation checks pass.  Unlike core blocks
                    # (which have verified control flow), hint blocks
                    # have no trust — one bad instruction rejects the
                    # entire block as data.
                    #
                    # Checks (all KB-driven):
                    # 1. Last instruction is flow-terminating
                    # 2. No zero opwords ($0000 = null bytes as code)
                    # 3. All instructions have valid EA modes/sizes
                    # 4. All branch targets are word-aligned
                    # 5. No 68020+ instructions (unverified mixed-arch
                    #    blocks are almost certainly false decodes)
                    blk = hint_blocks[pos]
                    valid_hint = False
                    if blk.instructions:
                        last = blk.instructions[-1]
                        last_kb = kb.find(
                            _extract_mnemonic(last.text))
                        if last_kb:
                            flow = last_kb.get("pc_effects", {}).get(
                                "flow", {})
                            ftype = flow.get("type")
                            if ftype in ("return", "jump", "branch"):
                                valid_hint = True
                            elif (ftype == "call"
                                  and not flow.get("conditional")):
                                valid_hint = True  # tail call
                    if valid_hint:
                        for inst in blk.instructions:
                            # Zero opword
                            if (len(inst.raw) >= kb.opword_bytes
                                    and struct.unpack_from(">H",
                                        inst.raw, 0)[0] == 0):
                                valid_hint = False
                                break
                            # Invalid EA mode/size
                            if not _is_valid_encoding(inst.text,
                                    inst.raw, inst.offset, kb):
                                valid_hint = False
                                break
                            # Odd branch target
                            if not _has_valid_branch_target(inst, kb):
                                valid_hint = False
                                break
                            # 68020+ in unverified block
                            if _get_processor_min(inst.text, kb) != "68000":
                                valid_hint = False
                                break
                    if not valid_hint:
                        # Not valid code — emit as data
                        emit_data_region(f, code, pos, blk.end,
                                         labels, reloc_map,
                                         string_addrs)
                        data_bytes += blk.end - pos
                        pos = blk.end
                        continue
                    f.write("; --- unverified ---\n")
                    hint_instr = 0
                    for inst in blk.instructions:
                        if inst.offset != pos and inst.offset in labels:
                            _emit_label(inst.offset)
                        text = replace_targets_in_text(
                                inst.text, inst.offset, inst.size,
                                labels, reloc_map, kb.opword_bytes)
                        if app_offsets and base_info:
                            brn = base_info[0]
                            for off, sym in app_offsets.items():
                                text = text.replace(
                                    f"{off}(a{brn})",
                                    f"{sym}(a{brn})")
                        sub = lvo_substitutions.get(inst.offset)
                        if sub:
                            text = text.replace(sub[0], sub[1])
                        pmin = _get_processor_min(inst.text, kb)
                        if pmin != "68000":
                            f.write(f"    {text} ; {pmin}+\n")
                        else:
                            f.write(f"    {text}\n")
                        hint_instr += 1
                    instr_count += hint_instr
                    pos = blk.end
                elif pos in hint_addrs:
                    # Inside a hint block but not at start — skip
                    pos += 1
                elif pos in jt_regions:
                    jt = jt_regions[pos]
                    if jt["pattern"] == "pc_inline_dispatch":
                        # Decode and emit BRA instructions inline
                        from m68k_disasm import _Decoder, _decode_one
                        dec = _Decoder(code, 0)
                        dec.pos = pos
                        while dec.pos < jt["table_end"]:
                            if dec.pos in labels and dec.pos != pos:
                                _emit_label(dec.pos)
                            inst = _decode_one(dec, None)
                            if inst is None:
                                break
                            text = replace_targets_in_text(
                                inst.text, inst.offset, inst.size,
                                labels, reloc_map, kb.opword_bytes)
                            f.write(f"    {text}\n")
                            instr_count += 1
                        pos = jt["table_end"]
                    else:
                        # Data tables — emit structured dc.w entries
                        for entry_addr, tgt in jt["entries"]:
                            if entry_addr in labels and entry_addr != pos:
                                _emit_label(entry_addr)
                            tgt_label = labels[tgt]
                            if jt["base_addr"] is None:
                                f.write(
                                    f"    dc.w    {tgt_label}-*\n")
                            else:
                                f.write(
                                    f"    dc.w    "
                                    f"{tgt_label}-{jt['base_label']}\n")
                        data_bytes += jt["table_end"] - pos
                        pos = jt["table_end"]
                else:
                    # Not in any block — emit as data
                    data_end = pos + 1
                    while (data_end < code_size
                           and data_end not in blocks
                           and data_end not in hint_blocks
                           and data_end not in labels):
                        data_end += 1
                    emit_data_region(f, code, pos, data_end,
                                     labels, reloc_map, string_addrs)
                    data_bytes += data_end - pos
                    pos = data_end

            print(f"  {instr_count} instructions, "
                  f"{data_bytes} data bytes emitted")

        # Insert INCLUDE directives for used struct definitions.
        # The .I files define the field offset constants (e.g., IS_CODE EQU 18)
        # that the struct field substitution uses.
        if used_structs:
            # Look up source .i files from KB struct definitions
            includes = set()
            for struct_name in sorted(used_structs):
                struct_def = os_kb["structs"][struct_name]
                inc_path = struct_def["source"].lower()
                includes.add(inc_path)

            if includes:
                with open(output_path, "r") as f:
                    content = f.read()
                # Insert after the header comments, before section directive
                insert_point = content.index("    section code,code")
                include_block = ""
                for inc in sorted(includes):
                    include_block += f'    INCLUDE "{inc}"\n'
                include_block += "\n"
                content = (content[:insert_point] + include_block
                           + content[insert_point:])
                with open(output_path, "w") as f:
                    f.write(content)
                print(f"  {len(includes)} INCLUDE directives for "
                      f"{len(used_structs)} struct types")

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
