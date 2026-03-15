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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m68k_executor import (BasicBlock, _extract_mnemonic, _extract_branch_target,
                          _decode_ea, resolve_ea, propagate_states, _concrete)
from m68k_disasm import _Decoder, _decode_one, DecodeError
from kb_util import KB, xf


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
                            kb: KB, max_entries=256):
    """Read word-offset table. target = base_addr + entry."""
    word_size = kb.size_bytes["w"]
    targets = []
    for i in range(max_entries):
        ea = table_addr + i * word_size
        if ea + word_size > code_size:
            break
        offset = struct.unpack_from(">h", code, ea)[0]
        target = (base_addr + offset) & 0xFFFFFFFF
        if target >= code_size or target & kb.align_mask:
            break
        targets.append(target)
    return targets


def _scan_self_relative_table(code, table_addr, code_size, kb: KB,
                              max_entries=256):
    """Read self-relative word table. target = &entry + entry."""
    word_size = kb.size_bytes["w"]
    targets = []
    for i in range(max_entries):
        ea = table_addr + i * word_size
        if ea + word_size > code_size:
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
        except (DecodeError, struct.error):
            break

    return targets, pos


# ── Main detection ───────────────────────────────────────────────────────

def detect_jump_tables(blocks: dict[int, BasicBlock],
                       code: bytes, base_addr: int = 0) -> list[dict]:
    """Detect jump tables. Returns list of {addr, pattern, targets, dispatch_block}."""
    kb = KB()
    code_size = len(code)
    tables = []

    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue

        last = block.instructions[-1]
        ikb = kb.find(_extract_mnemonic(last.text))
        if ikb is None:
            continue

        ft, _ = kb.flow_type(last)
        if ft not in ("jump", "call"):
            continue
        if _extract_branch_target(last, last.offset) is not None:
            continue  # already resolved

        ea_info = _is_indexed_ea(last.raw, kb, ikb)

        # Pattern B: JMP (An) with preceding LEA+ADDA self-relative
        if ea_info is None and len(block.instructions) >= 3:
            ind_enc = kb.ea_enc["ind"]
            ea_spec = kb.ea_field_spec(ikb)
            if ind_enc and ea_spec and len(last.raw) >= 2:
                opcode = struct.unpack_from(">H", last.raw, 0)[0]
                if xf(opcode, ea_spec[0]) == ind_enc[0]:
                    jmp_reg = xf(opcode, ea_spec[1])
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
            targets = _scan_word_offset_table(code, base, base, code_size, kb)
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
                        code, table_start, target_base, code_size, kb)
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
                        code, lea_addr, code_size, kb)
                else:
                    table_start = lea_addr + ea_info["displacement"]
                    targets = _scan_word_offset_table(
                        code, table_start, lea_addr, code_size, kb)
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


def resolve_indirect_targets(blocks: dict[int, BasicBlock],
                             exit_states: dict, code_size: int) -> list[dict]:
    """Resolve indirect JMP/JSR and RTS via propagated state.

    Uses KB-driven EA decoding to handle all addressing modes uniformly:
    ind (An), disp d(An), and index d(An,Xn). The decoded operand is
    resolved against the propagated register state to compute the target.

    For RTS: reads the return address from the stack.
    """
    kb = KB()
    # Address size for stack reads: derived from RTS sp_effects bytes.
    # JMP/JSR EA resolution size doesn't affect address computation
    # (resolve_ea computes addresses from register values, not from
    # size-dependent memory reads), so we pass the address size for
    # consistency but it only matters for the immediate mode (unused here).
    rts_kb = kb.find("RTS")
    if rts_kb is None:
        raise KeyError("KB missing RTS instruction")
    rts_sp_inc = sum(e["bytes"] for e in rts_kb.get("sp_effects", [])
                     if e.get("action") == "increment")
    if not rts_sp_inc:
        raise ValueError("KB RTS has no sp_effects increment")
    # Map sp_effects bytes to size key for mem.read
    addr_size = next(
        (k for k, v in kb.size_bytes.items() if v == rts_sp_inc), None)
    if addr_size is None:
        raise ValueError(
            f"KB size_byte_count has no entry for {rts_sp_inc} bytes")

    def _valid_target(addr):
        return 0 <= addr < code_size and not (addr & kb.align_mask)

    resolved = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue

        last = block.instructions[-1]
        ikb = kb.find(_extract_mnemonic(last.text))
        if ikb is None:
            continue

        ft, _ = kb.flow_type(last)

        # RTS: read return address from stack.
        # The exit state has the POST-increment SP (RTS pops then jumps).
        # Adjust back by the KB-defined sp_effects to read from the
        # pre-pop address where the return address was stored.
        if ft == "return" and addr in exit_states:
            cpu, mem = exit_states[addr]
            if cpu.sp.is_known:
                pre_sp = (cpu.sp.concrete - rts_sp_inc) & 0xFFFFFFFF
            elif cpu.sp.is_symbolic:
                pre_sp = cpu.sp.sym_add(-rts_sp_inc)
            else:
                continue
            ret_val = mem.read(pre_sp, addr_size)
            if ret_val.is_known and _valid_target(ret_val.concrete):
                resolved.append({"target": ret_val.concrete})
            continue

        # Decode the EA from the JMP/JSR instruction
        operand, _ = _decode_jump_ea(last, kb)
        if operand is None:
            continue

        if addr not in exit_states:
            continue
        cpu, _ = exit_states[addr]

        # resolve_ea computes the effective address for all modes:
        # ind -> An, disp -> An+d, index -> An+Xn+d
        ea_val = resolve_ea(operand, cpu, addr_size)
        if ea_val is not None and ea_val.is_known:
            if _valid_target(ea_val.concrete):
                resolved.append({"target": ea_val.concrete})

    return resolved


def resolve_per_caller(blocks: dict[int, BasicBlock],
                       exit_states: dict, code: bytes,
                       code_size: int,
                       platform: dict | None = None) -> list[dict]:
    """Resolve indirect targets that require per-caller analysis.

    When a subroutine's indirect jump can't be resolved because the
    merged state lost caller-specific information, re-analyze the
    subroutine with each caller's state independently.

    This handles patterns where:
    - A trampoline pops the caller's return address and jumps through it
    - A dispatch sub uses a register (e.g. D0) set by each caller
    """
    kb = KB()
    # Derive address size from KB (same as resolve_indirect_targets)
    rts_kb = kb.find("RTS")
    if rts_kb is None:
        raise KeyError("KB missing RTS instruction")
    rts_sp_inc = sum(e["bytes"] for e in rts_kb.get("sp_effects", [])
                     if e.get("action") == "increment")
    addr_size = next(
        (k for k, v in kb.size_bytes.items() if v == rts_sp_inc), None)
    if addr_size is None:
        raise ValueError(
            f"KB size_byte_count has no entry for {rts_sp_inc} bytes")

    def _valid_target(addr):
        return 0 <= addr < code_size and not (addr & kb.align_mask)

    # Find blocks ending with unresolved indirect jumps
    unresolved = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue
        last = block.instructions[-1]
        operand, _ = _decode_jump_ea(last, kb)
        if operand is None:
            continue
        if operand.mode not in kb.reg_indirect_modes:
            continue
        # Only consider blocks where the merged state failed to resolve
        if addr in exit_states:
            cpu, _ = exit_states[addr]
            ea_val = resolve_ea(operand, cpu, addr_size)
            if ea_val is not None and ea_val.is_known:
                continue  # already resolved by main pass
        unresolved.append((addr, operand))

    if not unresolved:
        return []

    # Find call-site predecessors for each unresolved block's subroutine.
    # Walk backward from the unresolved block to find the subroutine entry
    # (a block that has a call-site predecessor).
    call_targets = set()
    for block in blocks.values():
        for xref in block.xrefs:
            if xref.type == "call":
                call_targets.add(xref.dst)

    # Map subroutine entries to their blocks
    sub_blocks = {}
    for entry in call_targets:
        if entry not in blocks:
            continue
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
        sub_blocks[entry] = owned

    # Find which subroutine each unresolved block belongs to
    resolved = []
    for unres_addr, operand in unresolved:
        # Find the containing subroutine
        sub_entry = None
        for entry, owned in sub_blocks.items():
            if unres_addr in owned:
                sub_entry = entry
                break
        if sub_entry is None:
            continue

        # Find all callers of this subroutine
        callers = blocks[sub_entry].predecessors if sub_entry in blocks else []
        if not callers:
            continue

        # For each caller, re-propagate through the subroutine with
        # the caller's specific exit state
        sub_block_dict = {a: blocks[a] for a in sub_blocks[sub_entry]
                          if a in blocks}

        for caller_addr in callers:
            if caller_addr not in exit_states:
                continue
            caller_cpu, caller_mem = exit_states[caller_addr]
            init_cpu = caller_cpu.copy()

            # Restore the base register from platform config if it was
            # clobbered in the caller's state.  The main analysis restores
            # it on call fallthroughs, but the caller's exit state (which
            # is the pre-fallthrough state) may have it unknown.
            if platform:
                base_info = platform.get("initial_base_reg")
                if base_info:
                    breg_num, breg_val = base_info
                    if not init_cpu.a[breg_num].is_known:
                        init_cpu.set_reg("an", breg_num,
                                         _concrete(breg_val))

            per_caller_exits = propagate_states(
                sub_block_dict, code, sub_entry,
                initial_state=init_cpu,
                initial_mem=caller_mem.copy(),
                platform=platform)

            if unres_addr not in per_caller_exits:
                continue

            cpu, _ = per_caller_exits[unres_addr]
            ea_val = resolve_ea(operand, cpu, addr_size)
            if ea_val is not None and ea_val.is_known:
                if _valid_target(ea_val.concrete):
                    resolved.append({"target": ea_val.concrete})

    return resolved
