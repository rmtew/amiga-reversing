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


def _xf(opcode: int, field: tuple) -> int:
    """Extract a bit field from an opcode word. field = (bit_hi, bit_lo, width)."""
    return (opcode >> field[1]) & ((1 << field[2]) - 1)


def _build_ea_field_spec(inst_kb: dict) -> tuple | None:
    """Extract (mode_field, reg_field) from KB encoding for EA-using instructions.

    Returns ((hi, lo, width), (hi, lo, width)) for MODE and REGISTER fields,
    or None if the encoding doesn't have them.
    """
    encodings = inst_kb.get("encodings", [])
    if not encodings:
        return None
    fields = encodings[0].get("fields", [])
    mode_f = reg_f = None
    for f in fields:
        if f["name"] == "MODE":
            mode_f = (f["bit_hi"], f["bit_lo"], f["bit_hi"] - f["bit_lo"] + 1)
        elif f["name"] == "REGISTER" and f["bit_hi"] <= 5:
            # EA REGISTER is in the low bits (distinguish from dest REGISTER
            # in bits 11-9 for LEA)
            reg_f = (f["bit_hi"], f["bit_lo"], f["bit_hi"] - f["bit_lo"] + 1)
    if mode_f and reg_f:
        return mode_f, reg_f
    return None


def _parse_brief_ext_word(ext: int, meta: dict) -> dict | None:
    """Parse a brief extension word using KB ea_brief_ext_word fields.

    The brief/full discriminator is the one bit not covered by the KB
    field definitions (bit 8). If that bit is set, this is a full
    extension word and we return None.

    Returns dict with: index_is_addr, index_reg, displacement, or None.
    """
    bew_fields = meta.get("ea_brief_ext_word")
    if not bew_fields:
        return None

    # Find the uncovered bit (brief/full discriminator)
    covered = set()
    for f in bew_fields:
        for b in range(f["bit_lo"], f["bit_hi"] + 1):
            covered.add(b)
    brief_full_bits = set(range(16)) - covered
    # The brief/full bit must be 0 for brief format
    for bit in brief_full_bits:
        if ext & (1 << bit):
            return None  # full extension word

    # Extract fields by name from KB
    fields = {}
    for f in bew_fields:
        width = f["bit_hi"] - f["bit_lo"] + 1
        val = (ext >> f["bit_lo"]) & ((1 << width) - 1)
        fields[f["name"]] = val

    displacement = fields.get("DISPLACEMENT", 0)
    # Sign-extend displacement from its field width
    disp_field = next((f for f in bew_fields if f["name"] == "DISPLACEMENT"), None)
    if disp_field:
        disp_width = disp_field["bit_hi"] - disp_field["bit_lo"] + 1
        if displacement >= (1 << (disp_width - 1)):
            displacement -= (1 << disp_width)

    return {
        "index_is_addr": bool(fields.get("D/A", 0)),
        "index_reg": fields.get("REGISTER", 0),
        "displacement": displacement,
    }


def _is_indexed_ea(raw: bytes, inst_kb: dict = None) -> dict | None:
    """Check if instruction uses indexed EA (An+Xn or PC+Xn).

    EA mode/reg extracted from KB encoding fields (not hardcoded bit positions).
    Brief extension word parsed from KB ea_brief_ext_word fields.

    Returns dict with base_mode ('an' or 'pc'), base_reg, index_reg,
    index_is_data, displacement, or None.
    """
    if len(raw) < 4:
        return None

    kb_by_name, _, meta = _load_kb()
    ea_enc = meta["ea_mode_encoding"]

    opcode = struct.unpack_from(">H", raw, 0)[0]
    ext = struct.unpack_from(">H", raw, 2)[0]

    # Parse brief extension word from KB fields
    bew = _parse_brief_ext_word(ext, meta)
    if bew is None:
        return None  # full extension word — not handled

    # Extract EA mode/reg from KB encoding fields if inst_kb provided,
    # otherwise fall back to the standard EA position (bits 5-3, 2-0)
    # which is where MODE/REGISTER appear in JMP, JSR, LEA encodings.
    if inst_kb:
        ea_spec = _build_ea_field_spec(inst_kb)
        if ea_spec:
            mode_f, reg_f = ea_spec
            mode = _xf(opcode, mode_f)
            reg = _xf(opcode, reg_f)
        else:
            return None
    else:
        # No inst_kb — use standard EA field position from JMP/JSR/LEA.
        # These all have MODE at bits 5-3 and REGISTER at bits 2-0.
        jmp_kb = kb_by_name.get("JMP")
        if jmp_kb:
            ea_spec = _build_ea_field_spec(jmp_kb)
            if ea_spec:
                mode_f, reg_f = ea_spec
                mode = _xf(opcode, mode_f)
                reg = _xf(opcode, reg_f)
            else:
                return None
        else:
            return None

    # Check against KB ea_mode_encoding
    pcindex_enc = ea_enc.get("pcindex")
    index_enc = ea_enc.get("index")

    if pcindex_enc and mode == pcindex_enc[0] and reg == pcindex_enc[1]:
        return {
            "base_mode": "pc",
            "base_reg": None,
            "index_reg": bew["index_reg"],
            "index_is_data": not bew["index_is_addr"],
            "displacement": bew["displacement"],
        }
    if index_enc and mode == index_enc[0]:
        return {
            "base_mode": "an",
            "base_reg": reg,
            "index_reg": bew["index_reg"],
            "index_is_data": not bew["index_is_addr"],
            "displacement": bew["displacement"],
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

    BRA opcode pattern and displacement encoding derived from KB.
    """
    kb_by_name, _, meta = _load_kb()
    opword_bytes = meta["opword_bytes"]
    cc_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})

    # Build BRA opcode pattern from KB encoding
    bra_kb = kb_by_name.get("BRA")
    if not bra_kb:
        return []
    bra_enc = bra_kb["encodings"][0]
    bra_fixed = 0
    bra_mask = 0
    for f in bra_enc["fields"]:
        if f["name"] in ("0", "1"):
            for b in range(f["bit_lo"], f["bit_hi"] + 1):
                bra_mask |= (1 << b)
                if f["name"] == "1":
                    bra_fixed |= (1 << b)

    # Displacement field and encoding from KB
    disp_enc = bra_kb.get("constraints", {}).get("displacement_encoding")
    disp_field = None
    for f in bra_enc["fields"]:
        if "DISPLACEMENT" in f["name"].upper():
            disp_field = f
            break
    if not disp_enc or not disp_field:
        return []

    word_signal = disp_enc["word_signal"]
    long_signal = disp_enc["long_signal"]
    disp_width = disp_field["bit_hi"] - disp_field["bit_lo"] + 1
    disp_lo = disp_field["bit_lo"]
    disp_mask = ((1 << disp_width) - 1) << disp_lo

    targets = []
    pos = base_addr
    for _ in range(max_entries):
        if pos + 2 > code_size:
            break
        word = struct.unpack_from(">H", code, pos)[0]

        # Check if this word matches BRA opcode pattern
        if (word & bra_mask) == bra_fixed:
            disp8 = (word & disp_mask) >> disp_lo
            if disp8 == word_signal:
                # BRA.W: word displacement in extension
                if pos + opword_bytes + 2 <= code_size:
                    disp16 = struct.unpack_from(
                        ">h", code, pos + opword_bytes)[0]
                    target = pos + opword_bytes + disp16
                    if 0 <= target < code_size and not (target & 1):
                        targets.append(target)
                    pos += opword_bytes + 2
                    continue
                break
            elif disp8 == long_signal:
                # BRA.L (020+): skip
                break
            else:
                # BRA.S: 8-bit displacement
                if disp8 >= (1 << (disp_width - 1)):
                    disp8 -= (1 << disp_width)
                target = pos + opword_bytes + disp8
                if 0 <= target < code_size and not (target & 1):
                    targets.append(target)
                pos += opword_bytes
                continue

        # Try decoding as a regular instruction
        try:
            d = _Decoder(code, 0)
            d.pos = pos
            inst = _decode_one(d, None)
            if inst is None:
                break
            # If it's a flow instruction, extract its target
            mn = _extract_mnemonic(inst.text)
            kb = _find_kb_entry(kb_by_name, mn, cc_defs, cc_aliases)
            if kb:
                ft = kb.get("pc_effects", {}).get("flow", {}).get("type")
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
    kb_by_name, _, meta = _load_kb()
    opword_bytes = meta["opword_bytes"]
    ea_enc = meta["ea_mode_encoding"]
    code_size = len(code)
    tables = []

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

        ea_info = _is_indexed_ea(last.raw, kb)

        # Pattern B: JMP/JSR (An) with preceding LEA disp(PC,Dn),An + ADDA.W (An),An
        # The JMP itself uses simple indirect (mode 2), not indexed.
        # The indexed access is in the LEA that sets up the register.
        if ea_info is None and len(block.instructions) >= 3:
            ind_enc = ea_enc.get("ind")
            ea_spec = _build_ea_field_spec(kb)
            if ind_enc and ea_spec and len(last.raw) >= 2:
                mode_f, reg_f = ea_spec
                opcode = struct.unpack_from(">H", last.raw, 0)[0]
                jmp_mode = _xf(opcode, mode_f)
                jmp_reg = _xf(opcode, reg_f)
                if jmp_mode == ind_enc[0]:
                    # JMP (An) — look for ADDA.W (An),An + LEA indexed(PC,Dn),An
                    has_adda = False
                    lea_info = None
                    table_base = None
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
                                    lea_kb = _find_kb_entry(
                                        kb_by_name, "lea", cc_defs, cc_aliases)
                                    lea_info = _is_indexed_ea(
                                        inst.raw, lea_kb)
                                    if lea_info and lea_info["base_mode"] == "pc":
                                        pc_val = inst.offset + opword_bytes
                                        table_base = pc_val + lea_info["displacement"]
                                    else:
                                        # Check for simple PC-relative LEA
                                        # via KB EA mode encoding (pcdisp)
                                        pcdisp_enc = ea_enc.get("pcdisp")
                                        if pcdisp_enc and lea_kb and len(inst.raw) >= 4:
                                            lea_spec = _build_ea_field_spec(lea_kb)
                                            if lea_spec:
                                                lop = struct.unpack_from(">H", inst.raw, 0)[0]
                                                lm = _xf(lop, lea_spec[0])
                                                lr = _xf(lop, lea_spec[1])
                                                if lm == pcdisp_enc[0] and lr == pcdisp_enc[1]:
                                                    disp = struct.unpack_from(
                                                        ">h", inst.raw, 2)[0]
                                                    pc_val = inst.offset + opword_bytes
                                                    table_base = pc_val + disp
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
                                lea_kb = _find_kb_entry(
                                    kb_by_name, "lea", cc_defs, cc_aliases)
                                lea_ea = _is_indexed_ea(inst.raw, lea_kb)
                                if lea_ea and lea_ea["base_mode"] == "pc":
                                    # LEA disp(PC,Dn.w),An
                                    pc_val = inst.offset + opword_bytes
                                    lea_addr = pc_val + lea_ea["displacement"]
                                else:
                                    # Check for LEA disp(PC),An via KB pcdisp
                                    pcdisp_enc = ea_enc.get("pcdisp")
                                    if pcdisp_enc and lea_kb and len(inst.raw) >= 4:
                                        lea_spec = _build_ea_field_spec(lea_kb)
                                        if lea_spec:
                                            lop = struct.unpack_from(">H", inst.raw, 0)[0]
                                            lm = _xf(lop, lea_spec[0])
                                            lr = _xf(lop, lea_spec[1])
                                            if lm == pcdisp_enc[0] and lr == pcdisp_enc[1]:
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


def resolve_indirect_targets(blocks: dict[int, BasicBlock],
                             exit_states: dict, code_size: int,
                             ) -> list[dict]:
    """Resolve indirect JMP/JSR (An) targets using propagated register values.

    For each block ending with an unresolved indirect call/jump via (An),
    checks if An has a concrete value in the exit state. If so, and the
    value is a valid code address, returns it as a resolved target.

    EA mode/reg extracted from KB encoding fields (not hardcoded bit positions).

    Returns list of dicts:
        {"dispatch_block": int, "register": str, "target": int}
    """
    kb_by_name, _, meta = _load_kb()
    ea_enc = meta["ea_mode_encoding"]
    ind_enc = ea_enc.get("ind")  # [mode, None] for (An)
    cc_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})

    resolved = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue

        last = block.instructions[-1]
        mn = _extract_mnemonic(last.text)
        kb = _find_kb_entry(kb_by_name, mn, cc_defs, cc_aliases)
        if not kb:
            continue

        flow = kb.get("pc_effects", {}).get("flow", {})
        if flow.get("type") not in ("call", "jump"):
            continue

        # Only interested in unresolved targets
        target = _extract_branch_target(last, last.offset)
        if target is not None:
            continue

        # Extract EA mode/reg from KB encoding fields
        ea_spec = _build_ea_field_spec(kb)
        if ea_spec is None or ind_enc is None or len(last.raw) < 2:
            continue
        mode_f, reg_f = ea_spec
        opcode = struct.unpack_from(">H", last.raw, 0)[0]
        mode = _xf(opcode, mode_f)
        reg = _xf(opcode, reg_f)
        if mode != ind_enc[0]:
            continue  # not register indirect

        # Check propagated state
        if addr not in exit_states:
            continue
        cpu, _mem = exit_states[addr]
        reg_val = cpu.a[reg]
        if reg_val.is_known and 0 <= reg_val.concrete < code_size:
            if not (reg_val.concrete & 1):  # must be word-aligned
                resolved.append({
                    "dispatch_block": addr,
                    "register": f"A{reg}",
                    "target": reg_val.concrete,
                })

    return resolved


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
