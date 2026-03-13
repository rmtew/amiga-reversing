"""Jump table detection for M68K code.

Scans basic blocks for common jump table dispatch patterns and extracts
target addresses from the tables. All M68K instruction knowledge comes
from the KB via the executor/disassembler — the patterns detected here
are structural (addressing mode combinations), not mnemonic-specific.

Supported patterns:
  A. Word-offset dispatch: LEA base,An; JMP/JSR disp(An,Dn.w)
     Table of word offsets relative to An. target = An + table[i]
  B. Self-relative dispatch: LEA base(pc,Dn.w),An; ADDA.W (An),An; JMP (An)
     Table of self-relative word offsets. target = &entry + entry_value
  C. PC-relative inline: JMP/JSR disp(PC,Dn.w)
     Inline code at base address. Try decoding instructions from base.

Usage:
    from jump_tables import detect_jump_tables
    new_entries = detect_jump_tables(blocks, code, base_addr=0)
"""

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m68k_executor import (BasicBlock, _extract_mnemonic, _load_kb,
                            _find_kb_entry, _extract_branch_target)
from m68k_disasm import _Decoder, _decode_one, DecodeError


def _get_flow_type(inst_text: str) -> str | None:
    """Get flow type from KB for an instruction's mnemonic."""
    kb_by_name, _, meta = _load_kb()
    cc_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})
    mn = _extract_mnemonic(inst_text)
    kb = _find_kb_entry(kb_by_name, mn, cc_defs, cc_aliases)
    if kb is None:
        return None
    return kb.get("pc_effects", {}).get("flow", {}).get("type")


def _is_indexed_ea(raw: bytes) -> dict | None:
    """Check if instruction uses indexed EA (mode 110+Xn or PC-relative+Xn).

    Returns dict with base_mode ('an' or 'pc'), base_reg, index_reg,
    index_is_data, displacement, or None.
    """
    if len(raw) < 4:
        return None

    _, _, meta = _load_kb()
    ea_enc = meta["ea_mode_encoding"]

    opcode = struct.unpack_from(">H", raw, 0)[0]
    ext = struct.unpack_from(">H", raw, 2)[0]

    # Brief extension word format (bit 8 = 0):
    # bits 15: D/A (0=Dn, 1=An)
    # bits 14-12: index register number
    # bit 11: W/L (0=sign-extended word, 1=long)
    # bit 8: 0 for brief
    # bits 7-0: signed displacement
    if ext & 0x0100:
        return None  # full extension word — not handled yet

    index_is_addr = bool(ext & 0x8000)
    index_reg = (ext >> 12) & 7
    displacement = ext & 0xFF
    if displacement >= 0x80:
        displacement -= 0x100  # sign extend

    # Find the EA mode/reg fields — check common positions.
    # For JMP/JSR: bits 5-3 = mode, bits 2-0 = reg
    # For LEA: bits 5-3 = mode, bits 2-0 = reg (source EA)
    mode = (opcode >> 3) & 7
    reg = opcode & 7

    # Check against KB ea_mode_encoding.
    # KB keys: "pcindex" for PC-relative indexed, "index" for An-indexed.
    pcindex_enc = ea_enc.get("pcindex")  # [7, 3]
    index_enc = ea_enc.get("index")      # [6, None]

    if pcindex_enc and mode == pcindex_enc[0] and reg == pcindex_enc[1]:
        return {
            "base_mode": "pc",
            "base_reg": None,
            "index_reg": index_reg,
            "index_is_data": not index_is_addr,
            "displacement": displacement,
        }
    if index_enc and mode == index_enc[0]:
        return {
            "base_mode": "an",
            "base_reg": reg,
            "index_reg": index_reg,
            "index_is_data": not index_is_addr,
            "displacement": displacement,
        }
    return None


def _scan_word_offset_table(code: bytes, table_addr: int, base_addr: int,
                            code_size: int, max_entries: int = 256
                            ) -> list[int]:
    """Read word-offset table entries and compute targets.

    Each entry is a signed 16-bit offset. target = base_addr + offset.
    Stops when target falls outside code range or entry looks invalid.
    """
    targets = []
    for i in range(max_entries):
        entry_addr = table_addr + i * 2
        if entry_addr + 2 > code_size:
            break
        offset = struct.unpack_from(">h", code, entry_addr)[0]
        target = (base_addr + offset) & 0xFFFFFFFF
        if target >= code_size or target & 1:
            break  # out of range or odd address
        targets.append(target)
    return targets


def _scan_self_relative_table(code: bytes, table_addr: int,
                              code_size: int, max_entries: int = 256
                              ) -> list[int]:
    """Read self-relative word-offset table entries.

    Each entry at addr: target = addr + signed_word_at(addr).
    Stops when target falls outside code range.
    """
    targets = []
    for i in range(max_entries):
        entry_addr = table_addr + i * 2
        if entry_addr + 2 > code_size:
            break
        offset = struct.unpack_from(">h", code, entry_addr)[0]
        target = entry_addr + offset
        if target < 0 or target >= code_size or target & 1:
            break
        targets.append(target)
    return targets


def _scan_inline_dispatch(code: bytes, base_addr: int,
                          code_size: int, max_entries: int = 64
                          ) -> list[int]:
    """Try decoding instructions at base_addr to find inline dispatch targets.

    For JMP disp(PC,Dn.w) tables, the entries at base+0, base+2, base+4...
    are typically short branch instructions (BRA.S) to actual handlers.
    Also handles direct code (non-branch entries stop the scan).
    """
    targets = []
    pos = base_addr
    for _ in range(max_entries):
        if pos + 2 > code_size:
            break
        word = struct.unpack_from(">H", code, pos)[0]

        # BRA.S: $60xx where xx != 0x00 and xx != 0xFF
        if (word >> 8) == 0x60 and (word & 0xFF) not in (0x00, 0xFF):
            disp8 = word & 0xFF
            if disp8 >= 0x80:
                disp8 -= 256
            target = pos + 2 + disp8
            if 0 <= target < code_size and not (target & 1):
                targets.append(target)
            pos += 2
            continue

        # BRA.W: $6000 + 16-bit displacement
        if word == 0x6000 and pos + 4 <= code_size:
            disp16 = struct.unpack_from(">h", code, pos + 2)[0]
            target = pos + 2 + disp16
            if 0 <= target < code_size and not (target & 1):
                targets.append(target)
            pos += 4
            continue

        # Try decoding as a regular instruction
        try:
            d = _Decoder(code, 0)
            d.pos = pos
            inst = _decode_one(d, None)
            if inst is None:
                break
            # If it's a flow instruction, extract its target
            ft = _get_flow_type(inst.text)
            if ft in ("jump", "branch"):
                target = _extract_branch_target(inst, inst.offset)
                if target is not None:
                    targets.append(target)
            pos += inst.size
        except (DecodeError, struct.error):
            break

    return targets


def detect_jump_tables(blocks: dict[int, BasicBlock],
                       code: bytes, base_addr: int = 0,
                       ) -> list[dict]:
    """Detect jump tables in analyzed code and extract their targets.

    Returns list of dicts:
        {"addr": table_address, "pattern": str, "targets": [int, ...],
         "dispatch_block": int}
    """
    _, _, meta = _load_kb()
    opword_bytes = meta["opword_bytes"]
    code_size = len(code)
    tables = []

    kb_by_name, _, meta = _load_kb()
    cc_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})

    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue

        last = block.instructions[-1]
        mn = _extract_mnemonic(last.text)
        kb = _find_kb_entry(kb_by_name, mn, cc_defs, cc_aliases)
        if kb is None:
            continue

        flow = kb.get("pc_effects", {}).get("flow", {})
        flow_type = flow.get("type", "sequential")

        if flow_type not in ("jump", "call"):
            continue

        # Only interested in unresolved targets
        target = _extract_branch_target(last, last.offset)
        if target is not None:
            continue  # already resolved

        ea_info = _is_indexed_ea(last.raw)

        # Pattern B: JMP/JSR (An) with preceding LEA disp(PC,Dn),An + ADDA.W (An),An
        # The JMP itself uses simple indirect (mode 2), not indexed.
        # The indexed access is in the LEA that sets up the register.
        if ea_info is None and len(block.instructions) >= 3:
            ea_enc = meta["ea_mode_encoding"]
            ind_enc = ea_enc.get("ind")  # [2, None] for (An)
            if ind_enc:
                opcode = struct.unpack_from(">H", last.raw, 0)[0]
                jmp_mode = (opcode >> 3) & 7
                jmp_reg = opcode & 7
                if jmp_mode == ind_enc[0]:
                    # JMP (An) — look for ADDA.W (An),An + LEA indexed(PC,Dn),An
                    has_adda = False
                    lea_info = None
                    for inst in reversed(block.instructions[:-1]):
                        it = inst.text.strip().lower()
                        if it.startswith("adda") and f"(a{jmp_reg})" in it \
                                and f"a{jmp_reg}" in it.split(",")[-1]:
                            has_adda = True
                        elif _extract_mnemonic(inst.text).lower() == "lea":
                            parts = inst.text.strip().split(None, 1)
                            if len(parts) >= 2:
                                dst = parts[1].split(",")[-1].strip().lower()
                                if dst == f"a{jmp_reg}":
                                    lea_info = _is_indexed_ea(inst.raw)
                                    if lea_info and lea_info["base_mode"] == "pc":
                                        pc_val = inst.offset + opword_bytes
                                        table_base = pc_val + lea_info["displacement"]
                            break

                    if has_adda and lea_info and table_base is not None:
                        targets = _scan_self_relative_table(
                            code, table_base, code_size)
                        if len(targets) >= 2:
                            tables.append({
                                "addr": table_base,
                                "pattern": "self_relative_word",
                                "targets": targets,
                                "dispatch_block": addr,
                            })
                        continue

        if ea_info is None:
            continue

        # Pattern C: PC-relative indexed (JMP/JSR disp(PC,Dn.w))
        if ea_info["base_mode"] == "pc":
            pc_val = last.offset + opword_bytes
            table_base = pc_val + ea_info["displacement"]

            # Try inline dispatch (BRA.S entries)
            targets = _scan_inline_dispatch(code, table_base, code_size)
            if targets:
                tables.append({
                    "addr": table_base,
                    "pattern": "pc_inline_dispatch",
                    "targets": targets,
                    "dispatch_block": addr,
                })
                continue

            # Try word-offset table
            targets = _scan_word_offset_table(
                code, table_base, table_base, code_size)
            if len(targets) >= 2:
                tables.append({
                    "addr": table_base,
                    "pattern": "pc_word_offset",
                    "targets": targets,
                    "dispatch_block": addr,
                })
            continue

        # Pattern A/B: register-indexed (JMP/JSR disp(An,Dn.w))
        if ea_info["base_mode"] == "an":
            # Look backward in the block for LEA that sets up the base reg
            base_reg = ea_info["base_reg"]
            lea_addr = None

            for inst in reversed(block.instructions[:-1]):
                inst_mn = _extract_mnemonic(inst.text).lower()
                if inst_mn == "lea":
                    # Check if destination is the base register
                    text = inst.text.strip()
                    parts = text.split(None, 1)
                    if len(parts) >= 2:
                        operands = parts[1]
                        # Find destination (after last comma outside parens)
                        depth = 0
                        last_comma = -1
                        for ci, ch in enumerate(operands):
                            if ch == '(':
                                depth += 1
                            elif ch == ')':
                                depth -= 1
                            elif ch == ',' and depth == 0:
                                last_comma = ci
                        if last_comma >= 0:
                            dst = operands[last_comma + 1:].strip().lower()
                            if dst == f"a{base_reg}":
                                # Found the LEA — extract its EA
                                lea_ea = _is_indexed_ea(inst.raw)
                                if lea_ea and lea_ea["base_mode"] == "pc":
                                    # LEA disp(PC,Dn.w),An — self-relative
                                    pc_val = inst.offset + opword_bytes
                                    lea_base = pc_val + lea_ea["displacement"]
                                    lea_addr = lea_base
                                elif inst.text.strip().lower().find("(pc)") >= 0 or \
                                     "pc" in inst.text.lower():
                                    # LEA disp(PC),An — simple PC-relative
                                    # Parse displacement from extension word
                                    if len(inst.raw) >= 4:
                                        disp = struct.unpack_from(
                                            ">h", inst.raw, 2)[0]
                                        pc_val = inst.offset + opword_bytes
                                        lea_addr = pc_val + disp
                                break

            if lea_addr is not None:
                # Check for self-relative pattern:
                # LEA disp(PC,Dn.w),An; ADDA.W (An),An; JMP (An)
                has_adda = False
                for inst in block.instructions[-3:]:
                    it = inst.text.strip().lower()
                    if it.startswith("adda") and f"(a{base_reg})" in it:
                        has_adda = True

                if has_adda:
                    # Self-relative word table
                    targets = _scan_self_relative_table(
                        code, lea_addr, code_size)
                    if len(targets) >= 2:
                        tables.append({
                            "addr": lea_addr,
                            "pattern": "self_relative_word",
                            "targets": targets,
                            "dispatch_block": addr,
                        })
                else:
                    # Word-offset table: entries are offsets from lea_addr
                    jmp_disp = ea_info["displacement"]
                    table_start = lea_addr + jmp_disp
                    targets = _scan_word_offset_table(
                        code, table_start, lea_addr, code_size)
                    if len(targets) >= 2:
                        tables.append({
                            "addr": table_start,
                            "pattern": "word_offset",
                            "targets": targets,
                            "dispatch_block": addr,
                        })

    return tables


def detect_and_report(blocks: dict[int, BasicBlock],
                      code: bytes, base_addr: int = 0) -> set[int]:
    """Detect jump tables and print a report. Returns set of new entry points."""
    tables = detect_jump_tables(blocks, code, base_addr)

    if not tables:
        print("  No jump tables detected")
        return set()

    new_entries = set()
    for t in tables:
        targets = t["targets"]
        new_entries.update(targets)
        print(f"  ${t['dispatch_block']:06X}: {t['pattern']} "
              f"table at ${t['addr']:06X}, {len(targets)} entries")

    # Remove entries that are already known blocks
    known = set(blocks.keys())
    new_entries -= known
    print(f"  Total new entry points from tables: {len(new_entries)}")
    return new_entries
