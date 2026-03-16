"""Jump table detection and indirect target resolution for M68K code.

All M68K knowledge from KB. Supported patterns:

Jump tables (detect_jump_tables):
  A. Word-offset dispatch: LEA base,An; JMP/JSR disp(An,Dn.w)
  B. Self-relative dispatch: LEA d(PC,Dn),An; ADDA.W (An),An; JMP (An)
  C. PC-relative inline: JMP/JSR disp(PC,Dn.w) with BRA.S entries
  D. Indirect table read: LEA d(PC),An; MOVE.W d1(An,Dn),Dn; JSR d2(An,Dn)

Indirect resolution (resolve_indirect_targets):
  All register-indirect EA modes: (An), d(An), d(An,Xn)
  RTS return address via stack tracking

Per-caller resolution (resolve_per_caller):
  Re-analyzes shared subroutines per call site when merged state is too
  imprecise. Handles trampolines and dispatch routines.
"""

import struct
import sys

from .m68k_executor import (BasicBlock, _extract_mnemonic, _extract_branch_target,
                           _decode_ea, resolve_ea, propagate_states, _concrete,
                           _join_states)
from .m68k_disasm import _Decoder, _decode_one, DecodeError
from .kb_util import KB, xf


# ── Extension word parsing (from KB field definitions) ───────────────────

def _parse_ext_word(ext: int, raw: bytes, meta: dict) -> dict | None:
    """Parse brief or full extension word from KB fields.

    Returns dict with index_is_addr, index_reg, displacement, or None.
    """
    # Try brief first (mandatory), then full (68020+, optional)
    for key, full in [("ea_brief_ext_word", False), ("ea_full_ext_word", True)]:
        if full:
            fields_def = meta.get(key)
            if not fields_def:
                continue
        else:
            fields_def = meta[key]

        # Check discriminator bits (uncovered bits in the field definition)
        covered = set()
        for f in fields_def:
            for b in range(f["bit_lo"], f["bit_hi"] + 1):
                covered.add(b)
        disc_bits = set(range(16)) - covered
        # Brief: disc bits must be 0. Full: disc bits must be 1.
        match = all((ext & (1 << b)) == (1 << b if full else 0)
                     for b in disc_bits)
        if not match:
            continue

        # Extract fields
        fields = {}
        for f in fields_def:
            width = f["bit_hi"] - f["bit_lo"] + 1
            fields[f["name"]] = (ext >> f["bit_lo"]) & ((1 << width) - 1)

        displacement = fields.get("DISPLACEMENT", 0)  # 0 if full ext word (displacement in subsequent bytes)

        if full:
            # Full ext word: displacement from subsequent bytes.
            # BD SIZE values from KB ea_full_ext_bd_size.
            bd_size = fields.get("BD SIZE", 0)
            bd_map = meta["ea_full_ext_bd_size"]
            bd_type = bd_map.get(str(bd_size), "reserved")
            if bd_type == "reserved":
                return None
            elif bd_type == "null":
                displacement = 0
            elif bd_type == "word":
                if len(raw) < 6:
                    return None
                displacement = struct.unpack_from(">h", raw, 4)[0]
            elif bd_type == "long":
                if len(raw) < 8:
                    return None
                displacement = struct.unpack_from(">i", raw, 4)[0]
        else:
            # Brief: sign-extend displacement
            disp_f = next((f for f in fields_def
                           if f["name"] == "DISPLACEMENT"), None)
            if disp_f:
                w = disp_f["bit_hi"] - disp_f["bit_lo"] + 1
                if displacement >= (1 << (w - 1)):
                    displacement -= (1 << w)

        if "D/A" not in fields:
            raise KeyError("ea_brief/full_ext_word missing D/A field")
        if "REGISTER" not in fields:
            raise KeyError("ea_brief/full_ext_word missing REGISTER field")

        return {
            "index_is_addr": bool(fields["D/A"]),
            "index_reg": fields["REGISTER"],
            "displacement": displacement,
        }

    return None


# ── EA analysis helpers ──────────────────────────────────────────────────

def _is_indexed_ea(raw: bytes, kb: KB, inst_kb: dict) -> dict | None:
    """Check if instruction uses indexed EA (An+Xn or PC+Xn)."""
    if len(raw) < 4:
        return None

    ext_info = _parse_ext_word(
        struct.unpack_from(">H", raw, 2)[0], raw, kb.meta)
    if ext_info is None:
        return None

    ea_spec = kb.ea_field_spec(inst_kb)
    if ea_spec is None:
        return None

    opcode = struct.unpack_from(">H", raw, 0)[0]
    mode = xf(opcode, ea_spec[0])
    reg = xf(opcode, ea_spec[1])

    pcindex = kb.ea_enc["pcindex"]
    index = kb.ea_enc["index"]

    if pcindex and mode == pcindex[0] and reg == pcindex[1]:
        return {"base_mode": "pc", "base_reg": None, **ext_info}
    if index and mode == index[0]:
        return {"base_mode": "an", "base_reg": reg, **ext_info}
    return None


def _resolve_lea_pc(inst, kb: KB) -> int | None:
    """Resolve a LEA instruction's PC-relative source address.

    Handles both simple PC-displacement and PC-indexed modes.
    Returns the computed address, or None.
    """
    lea_kb = kb.find("lea")
    if lea_kb is None or len(inst.raw) < 4:
        return None

    ea_spec = kb.ea_field_spec(lea_kb)
    if ea_spec is None:
        return None

    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    mode = xf(opcode, ea_spec[0])
    reg = xf(opcode, ea_spec[1])

    # PC-indexed (pcindex): LEA d(PC,Dn),An
    pcindex = kb.ea_enc["pcindex"]
    if pcindex and mode == pcindex[0] and reg == pcindex[1]:
        ei = _is_indexed_ea(inst.raw, kb, lea_kb)
        if ei and ei["base_mode"] == "pc":
            return inst.offset + kb.opword_bytes + ei["displacement"]

    # PC-displacement (pcdisp): LEA d(PC),An
    pcdisp = kb.ea_enc["pcdisp"]
    if pcdisp and mode == pcdisp[0] and reg == pcdisp[1]:
        disp = struct.unpack_from(">h", inst.raw, kb.opword_bytes)[0]
        return inst.offset + kb.opword_bytes + disp

    return None


def _get_lea_dst_reg(inst, kb: KB) -> int | None:
    """Get destination register number from a LEA instruction."""
    lea_kb = kb.find("lea")
    if lea_kb is None:
        return None
    dst_spec = kb.dst_reg_field(lea_kb)
    if dst_spec is None:
        return None
    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    return xf(opcode, dst_spec)


# ── Table scanning ───────────────────────────────────────────────────────

def _scan_word_offset_table(code, table_addr, base_addr, code_size,
                            kb: KB, max_entries=256,
                            field_offset: int = 0, stride: int = 0,
                            call_targets: set | None = None):
    """Read word-offset table. target = base_addr + entry.

    field_offset: byte offset of the word field within each entry.
    stride: byte distance between entries (default = word size).
    call_targets: known subroutine entries -- stop before reading these.
    """
    word_size = kb.size_bytes["w"]
    if stride == 0:
        stride = word_size
    targets = []
    for i in range(max_entries):
        ea = table_addr + field_offset + i * stride
        if ea + word_size > code_size:
            break
        # Stop if this address is a known subroutine entry
        if call_targets and ea in call_targets:
            break
        offset = struct.unpack_from(">h", code, ea)[0]
        target = (base_addr + offset) & kb.addr_mask
        if target >= code_size or target & kb.align_mask:
            break
        targets.append(target)
    return targets


def _scan_self_relative_table(code, table_addr, code_size, kb: KB,
                              max_entries=256,
                              call_targets: set | None = None):
    """Read self-relative word table. target = &entry + entry."""
    word_size = kb.size_bytes["w"]
    targets = []
    for i in range(max_entries):
        ea = table_addr + i * word_size
        if ea + word_size > code_size:
            break
        if call_targets and ea in call_targets:
            break
        offset = struct.unpack_from(">h", code, ea)[0]
        target = ea + offset
        if target < 0 or target >= code_size or target & kb.align_mask:
            break
        targets.append(target)
    return targets


def _scan_inline_dispatch(code, base_addr, code_size, kb: KB,
                          max_entries=64):
    """Decode inline BRA.S/BRA.W entries at base_addr. KB-driven.

    Returns (targets, end_pos) where end_pos is the address after
    the last decoded entry.
    """
    bra_kb = kb.by_name["BRA"]

    # Build BRA opcode pattern from KB encoding
    enc = bra_kb["encodings"][0]
    fixed = mask = 0
    for f in enc["fields"]:
        if f["name"] in ("0", "1"):
            for b in range(f["bit_lo"], f["bit_hi"] + 1):
                mask |= 1 << b
                if f["name"] == "1":
                    fixed |= 1 << b

    disp_enc = bra_kb["constraints"]["displacement_encoding"]
    disp_f = next(f for f in enc["fields"]
                  if "DISPLACEMENT" in f["name"].upper())

    w_sig = disp_enc["word_signal"]
    l_sig = disp_enc["long_signal"]
    d_width = disp_f["bit_hi"] - disp_f["bit_lo"] + 1
    d_lo = disp_f["bit_lo"]
    d_mask = ((1 << d_width) - 1) << d_lo
    ow = kb.opword_bytes

    targets = []
    pos = base_addr
    for _ in range(max_entries):
        if pos + 2 > code_size:
            break
        word = struct.unpack_from(">H", code, pos)[0]

        if (word & mask) == fixed:
            d8 = (word & d_mask) >> d_lo
            if d8 == w_sig:
                if pos + ow + 2 <= code_size:
                    d16 = struct.unpack_from(">h", code, pos + ow)[0]
                    t = pos + ow + d16
                    if 0 <= t < code_size and not (t & 1):
                        targets.append(t)
                    pos += ow + 2
                    continue
                break
            elif d8 == l_sig:
                break
            else:
                if d8 >= (1 << (d_width - 1)):
                    d8 -= 1 << d_width
                t = pos + ow + d8
                if 0 <= t < code_size and not (t & 1):
                    targets.append(t)
                pos += ow
                continue

        # Try decoding as regular instruction
        try:
            d = _Decoder(code, 0)
            d.pos = pos
            inst = _decode_one(d, None)
            if inst is None:
                break
            ft, _ = kb.flow_type(inst)
            if ft in ("jump", "branch"):
                target = _extract_branch_target(inst, inst.offset)
                if target is not None:
                    targets.append(target)
            pos += inst.size
        except (DecodeError, struct.error) as exc:
            print(f"_scan_inline_dispatch: decode error at ${pos:04x}: "
                  f"{exc} -- ending scan with {len(targets)} entries",
                  file=sys.stderr)
            break

    return targets, pos


# ── Main detection ───────────────────────────────────────────────────────

def detect_jump_tables(blocks: dict[int, BasicBlock],
                       code: bytes, base_addr: int = 0) -> list[dict]:
    """Detect jump tables. Returns list of {addr, pattern, targets, dispatch_block}."""
    kb = KB()
    code_size = len(code)
    tables = []

    # Collect call targets (subroutine entries) to prevent table
    # scanners from reading into subroutine code.
    _call_targets = set()
    for blk in blocks.values():
        for xref in blk.xrefs:
            if xref.type == "call":
                _call_targets.add(xref.dst)

    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue

        last = block.instructions[-1]
        ikb = kb.find(_extract_mnemonic(last.text))
        if ikb is None:
            continue

        ft, _ = kb.flow_type(last)

        # Detect MOVE.L An,-(SP); RTS as equivalent to JMP (An).
        # The MOVE pushes a computed address, RTS pops and jumps to it.
        # For pattern detection, treat the push register as the dispatch
        # register and the combined pair as a virtual JMP (An).
        virtual_jmp_reg = None
        if ft == "return" and len(block.instructions) >= 2:
            prev = block.instructions[-2]
            prev_kb = kb.find(_extract_mnemonic(prev.text))
            if prev_kb and prev_kb.get("operation_type") == "move":
                from .kb_util import decode_instruction_operands
                decoded = decode_instruction_operands(
                    prev.raw, prev_kb, kb.meta, "l", prev.offset)
                ea_op = decoded.get("ea_op")
                dst_op = decoded.get("dst_op")
                # Source must be An, destination must be predec SP
                if (ea_op and ea_op.mode == "an"
                        and dst_op and dst_op.mode == "predec"
                        and dst_op.reg == kb.meta["_sp_reg_num"]):
                    virtual_jmp_reg = ea_op.reg

        if ft not in ("jump", "call") and virtual_jmp_reg is None:
            continue
        if ft in ("jump", "call"):
            if _extract_branch_target(last, last.offset) is not None:
                continue  # already resolved

        ea_info = _is_indexed_ea(last.raw, kb, ikb) if ft != "return" else None

        # Pattern B / E: (An) dispatch with preceding ADDA
        # For real JMP (An): extract register from EA.
        # For virtual JMP (PUSH+RTS): use the push source register.
        if ea_info is None and len(block.instructions) >= 3:
            ind_enc = kb.ea_enc["ind"]
            if virtual_jmp_reg is not None:
                jmp_reg = virtual_jmp_reg
            else:
                ea_spec = kb.ea_field_spec(ikb)
                if not (ind_enc and ea_spec and len(last.raw) >= 2):
                    jmp_reg = None
                else:
                    opcode = struct.unpack_from(">H", last.raw, 0)[0]
                    if xf(opcode, ea_spec[0]) != ind_enc[0]:
                        jmp_reg = None
                    else:
                        jmp_reg = xf(opcode, ea_spec[1])
            if jmp_reg is not None:
                    # Pattern B: self-relative ADDA (indirect source)
                    has_adda = False
                    table_base = None
                    for inst in reversed(block.instructions[:-1]):
                        if _is_adda_ind(inst, kb, jmp_reg):
                            has_adda = True
                        elif ikb_is_lea(inst, kb):
                            if _get_lea_dst_reg(inst, kb) == jmp_reg:
                                table_base = _resolve_lea_pc(inst, kb)
                            break

                    if has_adda and table_base is not None:
                        targets = _scan_self_relative_table(
                            code, table_base, code_size, kb)
                        if len(targets) >= 2:
                            tables.append({
                                "addr": table_base,
                                "pattern": "self_relative_word",
                                "targets": targets,
                                "dispatch_block": addr,
                                "base_addr": None,
                                "table_end": table_base + len(targets) * kb.size_bytes["w"],
                            })
                        continue

                    # Pattern E: ADDA.W Dn,An where Dn
                    # comes from a code-section table.
                    # LEA table,Ax; MOVE.W (Ax),Dy; LEA base,An;
                    # ADDA.W Dy,An; JMP (An)
                    adda_src = None
                    for inst in reversed(block.instructions[:-1]):
                        res = _is_adda_reg_src(inst, kb, jmp_reg)
                        if res:
                            adda_src = res
                            break
                        if ikb_is_lea(inst, kb):
                            break  # hit a LEA before finding ADDA

                    if adda_src is not None:
                        idx_mode, idx_reg = adda_src
                        # Find LEA that sets handler base (jmp_reg)
                        handler_base = None
                        for inst in reversed(block.instructions[:-1]):
                            if ikb_is_lea(inst, kb):
                                if _get_lea_dst_reg(inst, kb) == jmp_reg:
                                    handler_base = _resolve_lea_pc(inst, kb)
                                break

                        if handler_base is not None:
                            # Find where index_reg was loaded from
                            tbl_info = _find_table_source(
                                block.instructions, kb,
                                idx_mode, idx_reg,
                                block.instructions[-1].offset)

                            if tbl_info is not None:
                                targets = _scan_word_offset_table(
                                    code, tbl_info["table_addr"],
                                    handler_base, code_size, kb,
                                    field_offset=tbl_info["field_offset"],
                                    stride=tbl_info["stride"],
                                    call_targets=_call_targets)
                                if len(targets) >= 2:
                                    tables.append({
                                        "addr": tbl_info["table_addr"],
                                        "pattern": "adda_dispatch",
                                        "targets": targets,
                                        "dispatch_block": addr,
                                        "base_addr": handler_base,
                                        "table_end": (tbl_info["table_addr"]
                                            + len(targets)
                                            * tbl_info["stride"]),
                                    })
                                continue

        if ea_info is None:
            continue

        # Pattern C: PC-relative indexed
        if ea_info["base_mode"] == "pc":
            base = last.offset + kb.opword_bytes + ea_info["displacement"]
            # Scan from after the full dispatch instruction, not from
            # the PC-relative base (which may overlap the extension word)
            scan_start = last.offset + last.size
            targets, dispatch_end = _scan_inline_dispatch(
                code, scan_start, code_size, kb)
            if targets:
                tables.append({"addr": scan_start,
                               "pattern": "pc_inline_dispatch",
                               "targets": targets, "dispatch_block": addr,
                               "table_end": dispatch_end})
                continue
            targets = _scan_word_offset_table(code, base, base, code_size, kb,
                                               call_targets=_call_targets)
            if len(targets) >= 2:
                tables.append({"addr": base, "pattern": "pc_word_offset",
                               "targets": targets, "dispatch_block": addr,
                               "base_addr": base,
                               "table_end": base + len(targets) * kb.size_bytes["w"]})
            continue

        # Patterns A/D: register-indexed with LEA base
        if ea_info["base_mode"] == "an":
            base_reg = ea_info["base_reg"]
            lea_addr = None
            for inst in reversed(block.instructions[:-1]):
                if ikb_is_lea(inst, kb):
                    if _get_lea_dst_reg(inst, kb) == base_reg:
                        lea_addr = _resolve_lea_pc(inst, kb)
                    break

            if lea_addr is not None:
                # Pattern D: preceding indexed read into JSR's index reg.
                # MOVE.W d1(An,Dn),Dn reads offset from table; JSR d2(An,Dn)
                # dispatches.  table = lea + d1, target = lea + d2 + entry.
                move_disp = None
                for inst in reversed(block.instructions[:-1]):
                    if ikb_is_lea(inst, kb):
                        break
                    mi = kb.find(_extract_mnemonic(inst.text))
                    if mi is None:
                        continue
                    m_ea = _is_indexed_ea(inst.raw, kb, mi)
                    if (m_ea and m_ea["base_mode"] == "an"
                            and m_ea["base_reg"] == base_reg):
                        m_dst = kb.dst_reg_field(mi)
                        if m_dst:
                            m_op = struct.unpack_from(">H", inst.raw, 0)[0]
                            if xf(m_op, m_dst) == ea_info["index_reg"]:
                                move_disp = m_ea["displacement"]
                        break

                if move_disp is not None:
                    table_start = lea_addr + move_disp
                    target_base = lea_addr + ea_info["displacement"]
                    targets = _scan_word_offset_table(
                        code, table_start, target_base, code_size, kb,
                        call_targets=_call_targets)
                    if len(targets) >= 2:
                        tables.append({
                            "addr": table_start,
                            "pattern": "indirect_table_read",
                            "targets": targets,
                            "dispatch_block": addr,
                            "base_addr": target_base,
                            "table_end": table_start + len(targets) * kb.size_bytes["w"],
                        })
                    continue

                has_adda = any(
                    _is_adda_ind(inst, kb, base_reg)
                    for inst in block.instructions[-3:])
                if has_adda:
                    targets = _scan_self_relative_table(
                        code, lea_addr, code_size, kb,
                        call_targets=_call_targets)
                else:
                    table_start = lea_addr + ea_info["displacement"]
                    targets = _scan_word_offset_table(
                        code, table_start, lea_addr, code_size, kb,
                        call_targets=_call_targets)
                if len(targets) >= 2:
                    pattern = "self_relative_word" if has_adda else "word_offset"
                    tbl_addr = lea_addr if has_adda else table_start
                    tables.append({"addr": tbl_addr,
                                   "pattern": pattern, "targets": targets,
                                   "dispatch_block": addr,
                                   "base_addr": None if has_adda else lea_addr,
                                   "table_end": tbl_addr + len(targets) * kb.size_bytes["w"]})

    return tables


def ikb_is_lea(inst, kb: KB) -> bool:
    """Check if instruction is LEA via KB operation text."""
    ikb = kb.find(_extract_mnemonic(inst.text))
    return ikb is not None and ikb.get("operation_class") == "load_effective_address"


def _find_table_source(instructions, kb: KB, index_mode: str,
                       index_reg: int, stop_before: int) -> dict | None:
    """Scan backward to find where index_reg was loaded from code-section memory.

    Looks for MOVE.W source,Dn where source is resolvable to a concrete
    code-section address (via PC-relative, or indirect/disp from an An
    set by LEA PC-relative).

    Returns {"table_addr": int, "field_offset": int, "stride": int} or None.
    field_offset: byte offset of the index field within each table entry.
    stride: entry size in bytes (detected from postincrement count).
    """
    from .kb_util import decode_instruction_operands, decode_destination

    for inst in reversed(instructions):
        if inst.offset >= stop_before:
            continue
        mi = kb.find(_extract_mnemonic(inst.text))
        if mi is None:
            continue

        # Check if this instruction writes to the index register
        dst = decode_destination(inst.raw, mi, kb.meta, "w", inst.offset)
        if not dst or dst != (index_mode, index_reg):
            continue

        # Found the write -- decode source EA
        decoded = decode_instruction_operands(
            inst.raw, mi, kb.meta, "w", inst.offset)
        ea_op = decoded.get("ea_op")
        if ea_op is None:
            return None

        word_size = kb.size_bytes["w"]

        if ea_op.mode == "pcdisp":
            return {"table_addr": ea_op.value,
                    "field_offset": 0, "stride": word_size}

        if ea_op.mode in kb.reg_indirect_modes | {"postinc"}:
            # Source is (An) or d(An) or (An)+ -- resolve An via LEA.
            # Count postincrement MOVE.W instructions from the same
            # source register to determine stride and field offset.
            src_reg = ea_op.reg
            postinc_count = 0
            field_index = -1

            if ea_op.mode == "postinc":
                # Count consecutive postinc reads from same register
                # to determine total entry size and which field we use
                for scan_inst in instructions:
                    if scan_inst.offset >= stop_before:
                        break
                    scan_mi = kb.find(_extract_mnemonic(scan_inst.text))
                    if scan_mi is None:
                        continue
                    scan_decoded = decode_instruction_operands(
                        scan_inst.raw, scan_mi, kb.meta, "w",
                        scan_inst.offset)
                    scan_ea = scan_decoded.get("ea_op")
                    if (scan_ea and scan_ea.mode == "postinc"
                            and scan_ea.reg == src_reg):
                        if scan_inst.offset == inst.offset:
                            field_index = postinc_count
                        postinc_count += 1

            # Resolve base register via LEA
            for inst2 in reversed(instructions):
                if inst2.offset >= inst.offset:
                    continue
                if ikb_is_lea(inst2, kb):
                    if _get_lea_dst_reg(inst2, kb) == src_reg:
                        lea_addr = _resolve_lea_pc(inst2, kb)
                        if lea_addr is not None:
                            disp = ea_op.value if ea_op.mode == "disp" else 0
                            stride = (postinc_count * word_size
                                      if postinc_count > 1 else word_size)
                            field_off = (field_index * word_size
                                         if field_index >= 0 else disp)
                            return {"table_addr": lea_addr,
                                    "field_offset": field_off,
                                    "stride": stride}
                    break
            return None

        return None  # unresolvable source mode

    return None


def _is_adda_reg_src(inst, kb: KB, target_reg: int) -> tuple | None:
    """Check if instruction is ADDA with register source to target_reg.

    Returns (src_mode, src_reg) e.g. ("dn", 3) for ADDA.W D3,An,
    or None if not a matching ADDA.
    Uses KB source_sign_extend to identify ADDA (vs ADD).
    """
    mi = kb.find(_extract_mnemonic(inst.text))
    if mi is None:
        return None
    if mi.get("operation_type") != "add" or not mi.get("source_sign_extend"):
        return None
    ea_spec = kb.ea_field_spec(mi)
    if ea_spec is None or len(inst.raw) < 2:
        return None
    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    dst = kb.dst_reg_field(mi)
    if dst is None or xf(opcode, dst) != target_reg:
        return None
    src_mode_val = xf(opcode, ea_spec[0])
    src_reg_val = xf(opcode, ea_spec[1])
    dn_enc = kb.ea_enc["dn"]
    an_enc = kb.ea_enc["an"]
    if src_mode_val == dn_enc[0]:
        return ("dn", src_reg_val)
    if src_mode_val == an_enc[0]:
        return ("an", src_reg_val)
    return None


def _is_adda_ind(inst, kb: KB, target_reg: int) -> bool:
    """Check if instruction is ADDA with indirect (An) source to target_reg.

    Uses KB encoding fields: source EA mode == ind, source register ==
    target_reg, destination register == target_reg.
    """
    mi = kb.find(_extract_mnemonic(inst.text))
    if mi is None:
        return False
    # ADDA: operation_type == "add" with source_sign_extend (KB-driven)
    if (mi.get("operation_type") != "add"
            or not mi.get("source_sign_extend")):
        return False
    ea_spec = kb.ea_field_spec(mi)
    if ea_spec is None or len(inst.raw) < 2:
        return False
    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    if xf(opcode, ea_spec[0]) != kb.ea_enc["ind"][0]:
        return False
    if xf(opcode, ea_spec[1]) != target_reg:
        return False
    dst = kb.dst_reg_field(mi)
    if dst is None or xf(opcode, dst) != target_reg:
        return False
    return True


# ── Indirect target resolution ───────────────────────────────────────────

def _decode_jump_ea(last, kb):
    """Decode the EA operand from a JMP/JSR instruction.

    Returns (Operand, inst_kb) or (None, None) if the instruction's EA
    can't be decoded or the target is already resolved (absolute/PC-relative).
    """
    ikb = kb.find(_extract_mnemonic(last.text))
    if ikb is None:
        return None, None

    ft, _ = kb.flow_type(last)
    if ft not in ("call", "jump"):
        return None, None

    # Skip instructions whose target is already known
    if _extract_branch_target(last, last.offset) is not None:
        return None, None

    ea_spec = kb.ea_field_spec(ikb)
    if ea_spec is None or len(last.raw) < kb.opword_bytes:
        return None, None

    opcode = struct.unpack_from(">H", last.raw, 0)[0]
    mode = xf(opcode, ea_spec[0])
    reg = xf(opcode, ea_spec[1])

    # Operand size only affects immediate mode decoding (unused for
    # JMP/JSR which never use immediate EA).  Pass KB default size.
    try:
        operand, _ = _decode_ea(
            last.raw, kb.opword_bytes, mode, reg,
            kb.meta["default_operand_size"], last.offset)
    except (ValueError, struct.error):
        return None, None

    return operand, ikb


def _restore_base_reg(cpu, platform: dict | None):
    """Restore the base register from platform config if clobbered.

    The main analysis restores it on call fallthroughs, but the
    caller's exit state (pre-fallthrough) may have it unknown.
    Modifies cpu in place and returns it.
    """
    if platform:
        base_info = platform.get("initial_base_reg")
        if base_info:
            breg_num, breg_val = base_info
            if not cpu.a[breg_num].is_known:
                cpu.set_reg("an", breg_num, _concrete(breg_val))
    return cpu


def _is_valid_target(addr: int, code_size: int, align_mask: int) -> bool:
    """Check if addr is a valid code target (in range, aligned)."""
    return 0 <= addr < code_size and not (addr & align_mask)


def _read_rts_target(cpu, mem, kb: KB) -> int | None:
    """Read the return address from the stack at a RTS block's exit state.

    The exit state has the POST-increment SP. Adjusts back by the
    KB-derived RTS pop size to read from the pre-pop address.
    Returns the concrete target address, or None.
    """
    if cpu.sp.is_known:
        pre_sp = (cpu.sp.concrete - kb.rts_sp_inc) & kb.addr_mask
    elif cpu.sp.is_symbolic:
        pre_sp = cpu.sp.sym_add(-kb.rts_sp_inc)
    else:
        return None
    ret_val = mem.read(pre_sp, kb.addr_size)
    if ret_val.is_known:
        return ret_val.concrete
    return None


def _find_unresolved(blocks: dict[int, BasicBlock],
                     exit_states: dict, kb: KB,
                     code_size: int) -> list[tuple]:
    """Find blocks with unresolved indirect jumps or RTS.

    Returns list of (block_addr, "jump"|"return") for blocks where
    the merged exit state doesn't produce a concrete target.
    """
    unresolved = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue
        last = block.instructions[-1]
        ikb = kb.find(_extract_mnemonic(last.text))
        if ikb is None:
            continue
        ft, _ = kb.flow_type(last)

        if ft == "return":
            if addr in exit_states:
                cpu, mem = exit_states[addr]
                target = _read_rts_target(cpu, mem, kb)
                if target is not None:
                    continue  # already resolved
            unresolved.append((addr, "return"))
            continue

        operand, _ = _decode_jump_ea(last, kb)
        if operand is None:
            continue
        if operand.mode not in kb.reg_indirect_modes:
            continue
        if addr in exit_states:
            cpu, _ = exit_states[addr]
            ea_val = resolve_ea(operand, cpu, kb.addr_size)
            if ea_val is not None and ea_val.is_known:
                continue
        unresolved.append((addr, "jump"))

    return unresolved


def _try_resolve_block(unres_addr: int, unres_type: str,
                       blocks: dict, cpu, mem,
                       kb: KB, code_size: int) -> int | None:
    """Try to resolve an indirect target from a specific CPU/memory state.

    Returns the concrete target address, or None.
    """
    if unres_type == "return":
        target = _read_rts_target(cpu, mem, kb)
        if target is not None and _is_valid_target(
                target, code_size, kb.align_mask):
            return target
        return None

    last = blocks[unres_addr].instructions[-1]
    operand, _ = _decode_jump_ea(last, kb)
    if operand is None:
        return None
    ea_val = resolve_ea(operand, cpu, kb.addr_size)
    if ea_val is not None and ea_val.is_known:
        if _is_valid_target(ea_val.concrete, code_size, kb.align_mask):
            return ea_val.concrete
    return None


def resolve_indirect_targets(blocks: dict[int, BasicBlock],
                             exit_states: dict, code_size: int) -> list[dict]:
    """Resolve indirect JMP/JSR and RTS via propagated state.

    Uses KB-driven EA decoding to handle all addressing modes uniformly:
    ind (An), disp d(An), and index d(An,Xn). The decoded operand is
    resolved against the propagated register state to compute the target.

    For RTS: reads the return address from the stack.
    """
    kb = KB()
    resolved = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions or addr not in exit_states:
            continue
        last = block.instructions[-1]
        ikb = kb.find(_extract_mnemonic(last.text))
        if ikb is None:
            continue
        ft, _ = kb.flow_type(last)

        # Determine unresolved type
        if ft == "return":
            unres_type = "return"
        elif ft in ("call", "jump"):
            if _extract_branch_target(last, last.offset) is not None:
                continue
            unres_type = "jump"
        else:
            continue

        cpu, mem = exit_states[addr]
        target = _try_resolve_block(
            addr, unres_type, blocks, cpu, mem, kb, code_size)
        if target is not None:
            resolved.append({"target": target})

    return resolved


def _needed_registers(operand, unres_type: str) -> list[tuple[str, int]]:
    """Identify which registers an EA operand depends on.

    Returns list of (mode, reg_num) pairs, e.g. [("an", 6), ("dn", 0)]
    for jsr 0(a6,d0.w).  For RTS, returns empty (depends on stack, not
    registers).
    """
    if unres_type == "return" or operand is None:
        return []
    regs = []
    if operand.mode in ("ind", "disp", "index", "postinc", "predec"):
        regs.append(("an", operand.reg))
    if operand.mode == "index":
        idx_mode = "an" if operand.index_is_addr else "dn"
        regs.append((idx_mode, operand.index_reg))
    return regs


def _reg_modified_in_sub(blocks: dict, sub_entry: int,
                         dispatch_addr: int,
                         reg_mode: str, reg_num: int,
                         kb: KB,
                         platform_ref: dict | None = None) -> bool:
    """Check if a register is modified on any path from sub entry to dispatch.

    Walks forward from sub_entry through the block graph.  For each
    instruction, checks if it writes to the given register.  Returns True
    if any path modifies it before reaching the dispatch block.

    Uses KB operation_type/compute_formula to identify writes without
    executing instructions.
    """
    from .kb_util import decode_destination
    visited = set()
    work = [sub_entry]

    while work:
        addr = work.pop()
        if addr in visited or addr not in blocks:
            continue
        visited.add(addr)
        block = blocks[addr]

        for inst in block.instructions:
            # Don't check instructions AT the dispatch block -- they're
            # the consumers, not modifiers.
            if inst.offset >= dispatch_addr:
                break

            mn = _extract_mnemonic(inst.text)
            ikb = kb.find(mn)
            if ikb is None:
                continue

            # Check if this instruction could write to the register.
            # KB-driven: check destination operand and operation type.
            ft = ikb.get("pc_effects", {}).get("flow", {}).get("type")
            if ft in ("jump", "return", "branch"):
                continue  # flow instructions don't write to data/addr regs
            if ft == "call":
                # A call to a nested callee may modify registers.
                # Check the callee's summary: if the register is NOT
                # preserved (and not produced as the same value),
                # the call effectively modifies it.
                call_target = _extract_branch_target(inst, inst.offset)
                if call_target is not None:
                    global_sums = (platform_ref.get("_summary_cache")
                                   if platform_ref else None)
                    callee_sum = (global_sums.get(call_target)
                                 if global_sums else None)
                    if callee_sum is not None:
                        pkey = ("preserved_d" if reg_mode == "dn"
                                else "preserved_a")
                        if reg_num not in callee_sum.get(pkey, set()):
                            return True
                # No summary or no target — skip (old behavior)
                continue

            # Check explicit destination via KB encoding
            from .m68k_executor import _extract_size
            size = _extract_size(inst.text)
            dst = decode_destination(inst.raw, ikb, kb.meta, size,
                                     inst.offset)
            if dst and dst == (reg_mode, reg_num):
                return True

            # SWAP/EXG modify registers without a conventional destination.
            # SWAP modifies the Dn from its REGISTER field.
            # EXG modifies both Rx and Ry from its encoding.
            # Conservative: if the instruction is a swap type, assume it
            # could modify our register.
            if ikb.get("operation_type") == "swap":
                return True

            # MOVEM can write to any register in the mask
            if ikb.get("operation_class") == "multi_register_transfer":
                return True  # conservative: assume it could write our reg

        # Continue to successors within the sub
        for succ in block.successors:
            if succ in blocks and succ != dispatch_addr:
                work.append(succ)

    return False


def _inline_summary(callee_entry: int, blocks: dict,
                    call_targets: set, exit_states: dict,
                    kb: KB) -> dict | None:
    """Compute a summary from a callee's actual execution exit states.

    Unlike _compute_summary (which uses symbolic inputs), this builds
    a summary from concrete exit states produced by running the callee
    with specific inputs.  All concrete registers at RTS become produced
    values in the summary.
    """
    owned = _find_sub_blocks(callee_entry, blocks, call_targets)

    rts_states = []
    for addr in owned:
        blk = blocks.get(addr)
        if not blk or not blk.instructions:
            continue
        last = blk.instructions[-1]
        mn = _extract_mnemonic(last.text)
        ikb = kb.find(mn)
        if ikb is None:
            continue
        ft, _ = kb.flow_type(last)
        if ft == "return" and addr in exit_states:
            rts_states.append(exit_states[addr])

    if not rts_states:
        return None

    rts_cpu, _ = _join_states(rts_states)

    produced_d = {}
    for i in range(len(rts_cpu.d)):
        if rts_cpu.d[i].is_known:
            produced_d[i] = rts_cpu.d[i].concrete
    produced_a = {}
    for i in range(len(rts_cpu.a)):
        if rts_cpu.a[i].is_known:
            produced_a[i] = rts_cpu.a[i].concrete
    sp_delta = 0
    if rts_cpu.sp.is_symbolic and rts_cpu.sp.sym_base == "SP_entry":
        sp_delta = rts_cpu.sp.sym_offset

    return {"preserved_d": set(), "preserved_a": set(),
            "produced_d": produced_d, "produced_a": produced_a,
            "sp_delta": sp_delta}


def _find_sub_blocks(entry: int, blocks: dict,
                     call_targets: set) -> set[int]:
    """Find all blocks owned by a subroutine starting at entry."""
    owned = set()
    work = [entry]
    while work:
        a = work.pop()
        if a in owned or a not in blocks:
            continue
        if a != entry and a in call_targets:
            continue
        owned.add(a)
        for s in blocks[a].successors:
            work.append(s)
    return owned


def resolve_per_caller(blocks: dict[int, BasicBlock],
                       exit_states: dict, code: bytes,
                       code_size: int,
                       platform: dict | None = None) -> list[dict]:
    """Resolve indirect targets that require per-caller analysis.

    Uses targeted register substitution when possible: if the dispatch
    depends on registers that pass through the subroutine unmodified,
    substitute each caller's values directly (O(1) per caller).

    Falls back to full per-caller propagation only when the subroutine
    modifies the needed registers.
    """
    kb = KB()
    unresolved = _find_unresolved(blocks, exit_states, kb, code_size)
    if not unresolved:
        return []

    call_targets = set()
    for block in blocks.values():
        for xref in block.xrefs:
            if xref.type == "call":
                call_targets.add(xref.dst)

    # Map subroutine entries to their blocks (cached)
    sub_blocks_cache = {}

    resolved = []
    for unres_addr, unres_type in unresolved:
        # Find the containing subroutine
        sub_entry = None
        for entry in call_targets:
            if entry not in sub_blocks_cache:
                sub_blocks_cache[entry] = _find_sub_blocks(
                    entry, blocks, call_targets)
            if unres_addr in sub_blocks_cache[entry]:
                sub_entry = entry
                break
        if sub_entry is None:
            continue

        callers = blocks[sub_entry].predecessors if sub_entry in blocks else []
        if not callers:
            continue

        # Decode the dispatch EA to find needed registers
        operand = None
        if unres_type == "jump":
            last = blocks[unres_addr].instructions[-1]
            operand, _ = _decode_jump_ea(last, kb)
        needed_regs = _needed_registers(operand, unres_type)

        sub_dict = {a: blocks[a] for a in sub_blocks_cache[sub_entry]
                    if a in blocks}

        # Identify which needed registers are unknown in the merged
        # exit state -- those are the caller-varying ones we need to
        # substitute.  Registers that are concrete in the merged state
        # (even if modified in the sub) are already resolved.
        merged_cpu, merged_mem = exit_states.get(
            unres_addr, (None, None))
        unknown_regs = []
        if needed_regs and unres_type == "jump" and merged_cpu is not None:
            for mode, num in needed_regs:
                val = merged_cpu.get_reg(mode, num)
                if not val.is_known:
                    unknown_regs.append((mode, num))

        # Fast path only works when: (a) there ARE unknown registers in
        # the merged state, (b) those registers flow through from the
        # sub entry unmodified, and (c) the dispatch isn't at the sub
        # entry itself (single-block subs need full propagation because
        # the register is computed within the block, e.g. trampolines).
        use_fast_path = (
            unknown_regs
            and merged_cpu is not None
            and unres_addr != sub_entry
            and all(not _reg_modified_in_sub(sub_dict, sub_entry,
                                             unres_addr, mode, num, kb,
                                             platform_ref=platform)
                    for mode, num in unknown_regs))

        if use_fast_path:
            # Fast path: substitute caller-varying register values
            # into the merged exit state. Registers that the sub
            # computes to concrete values are already correct in the
            # merged state.
            for caller_addr in callers:
                if caller_addr not in exit_states:
                    continue
                caller_cpu, _ = exit_states[caller_addr]
                test_cpu = merged_cpu.copy()
                for mode, num in unknown_regs:
                    val = caller_cpu.get_reg(mode, num)
                    test_cpu.set_reg(mode, num, val)
                _restore_base_reg(test_cpu, platform)

                target = _try_resolve_block(
                    unres_addr, unres_type, blocks,
                    test_cpu, merged_mem, kb, code_size)
                if target is not None:
                    resolved.append({"target": target})
        else:
            # Slow path: full propagation per caller (trampolines, etc.)
            # Two-pass approach for nested callees:
            #   Pass 1: execute sub + nested callees with caller's state
            #   Pass 2: compute inline summaries from callee's actual
            #           execution, re-propagate sub with those summaries.
            # This resolves registers set by nested callees (e.g. A0 from
            # a utility sub that computes a function pointer from input).

            # Collect nested callee entries and their blocks
            nested_callees = set()
            for addr in sub_blocks_cache[sub_entry]:
                blk = blocks.get(addr)
                if not blk:
                    continue
                for xref in blk.xrefs:
                    if (xref.type == "call"
                            and xref.dst in call_targets
                            and xref.dst != sub_entry):
                        nested_callees.add(xref.dst)

            # Expand block set with nested callee blocks
            expanded = dict(sub_dict)
            for callee_entry in nested_callees:
                for na in _find_sub_blocks(
                        callee_entry, blocks, call_targets):
                    if na in blocks and na not in expanded:
                        expanded[na] = blocks[na]

            # Per-caller platform: no scratch invalidation for pass 1
            pc_platform = dict(platform) if platform else {}
            pc_platform["scratch_regs"] = []

            for caller_addr in callers:
                if caller_addr not in exit_states:
                    continue
                caller_cpu, caller_mem = exit_states[caller_addr]
                init_cpu = _restore_base_reg(
                    caller_cpu.copy(), platform)

                # Pass 1: execute everything (callee gets real inputs)
                pass1_exits = propagate_states(
                    expanded, code, sub_entry,
                    initial_state=init_cpu,
                    initial_mem=caller_mem.copy(),
                    platform=pc_platform)

                # Compute inline summaries from nested callees' exits
                inline_sums = {}
                for callee_entry in nested_callees:
                    isum = _inline_summary(
                        callee_entry, blocks, call_targets,
                        pass1_exits, kb)
                    if isum is not None:
                        inline_sums[callee_entry] = isum

                # Pass 2: re-propagate sub with inline summaries
                if inline_sums:
                    per_caller_exits = propagate_states(
                        sub_dict, code, sub_entry,
                        initial_state=init_cpu,
                        initial_mem=caller_mem.copy(),
                        platform=pc_platform,
                        summaries=inline_sums)
                else:
                    per_caller_exits = pass1_exits

                if unres_addr not in per_caller_exits:
                    continue
                cpu, mem = per_caller_exits[unres_addr]
                target = _try_resolve_block(
                    unres_addr, unres_type, blocks,
                    cpu, mem, kb, code_size)
                if target is not None:
                    resolved.append({"target": target})

    return resolved


def resolve_backward_slice(blocks: dict[int, BasicBlock],
                           exit_states: dict, code: bytes,
                           code_size: int,
                           platform: dict | None = None,
                           max_depth: int = 8) -> list[dict]:
    """Resolve indirect targets by backward-slicing through predecessor chains.

    When a block's merged exit state loses a register value needed for
    an indirect dispatch, walk backward through predecessor chains to
    find paths where the value was concrete. For each such path,
    propagate the predecessor's state forward to the dispatch block
    and try to resolve.

    This generalises resolve_per_caller (which only handles subroutine
    entries) to work across any block boundary, following predecessor
    chains up to max_depth levels.
    """
    kb = KB()
    unresolved = _find_unresolved(blocks, exit_states, kb, code_size)
    if not unresolved:
        return []

    resolved = []
    seen_targets = set()

    # Identify blocks ending with call instructions (BSR/JSR).
    # Call predecessors are handled by resolve_per_caller, not backward
    # slice.  Using a call block's exit state would propagate the pushed
    # return address, causing false positive RTS resolutions.
    call_blocks = set()
    for addr, block in blocks.items():
        if block.instructions:
            ft, _ = kb.flow_type(block.instructions[-1])
            if ft == "call":
                call_blocks.add(addr)

    for unres_addr, unres_type in unresolved:
        # Walk predecessor chains backward, collecting paths.
        # At each level, try to propagate.  If the predecessor's exit
        # state resolves the target, we're done.  Otherwise, go deeper.
        # Work queue: (predecessor_addr, path_from_pred_to_unres)
        # Skip call predecessors -- their exit states have SP decremented
        # and return addresses on the stack that cause false positives.
        work = []
        for pred in blocks[unres_addr].predecessors:
            if pred in exit_states and pred not in call_blocks:
                work.append((pred, [pred, unres_addr]))

        visited = {unres_addr}
        for _ in range(max_depth):
            next_work = []
            for pred_addr, path in work:
                if pred_addr in visited:
                    continue
                visited.add(pred_addr)

                if pred_addr not in exit_states:
                    continue
                pred_cpu, pred_mem = exit_states[pred_addr]
                init_cpu = _restore_base_reg(pred_cpu.copy(), platform)

                # Propagate through path blocks to unresolved block
                path_blocks = {a: blocks[a] for a in path
                               if a in blocks}
                if not path_blocks or pred_addr not in path_blocks:
                    continue
                per_path_exits = propagate_states(
                    path_blocks, code, pred_addr,
                    initial_state=init_cpu,
                    initial_mem=pred_mem.copy(),
                    platform=platform)
                if unres_addr not in per_path_exits:
                    continue
                p_cpu, p_mem = per_path_exits[unres_addr]
                target = _try_resolve_block(
                    unres_addr, unres_type, blocks,
                    p_cpu, p_mem, kb, code_size)
                if target is not None and target not in seen_targets:
                    resolved.append({"target": target})
                    seen_targets.add(target)
                else:
                    # Go one level deeper: add pred's predecessors
                    # (skip call blocks to avoid false positives)
                    if pred_addr in blocks:
                        for pp in blocks[pred_addr].predecessors:
                            if (pp not in visited and pp in exit_states
                                    and pp not in call_blocks):
                                next_work.append(
                                    (pp, [pp] + path))
            work = next_work
            if not work:
                break

    return resolved
