"""Jump table detection and indirect target resolution for M68K code.

All M68K knowledge from KB. Supported patterns:
  A. Word-offset dispatch: LEA base,An; JMP/JSR disp(An,Dn.w)
  B. Self-relative dispatch: LEA d(PC,Dn),An; ADDA.W (An),An; JMP (An)
  C. PC-relative inline: JMP/JSR disp(PC,Dn.w) with BRA.S entries
  D. Indirect table read: LEA d(PC),An; MOVE.W d1(An,Dn),Dn; JSR d2(An,Dn)
  E. Memory dispatch: MOVEA.L d(An),Am; JMP/JSR (Am) with stored targets
"""

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m68k_executor import BasicBlock, _extract_mnemonic, _extract_branch_target
from m68k_disasm import _Decoder, _decode_one, DecodeError
from kb_util import KB, xf


# ── Extension word parsing (from KB field definitions) ───────────────────

def _parse_ext_word(ext: int, raw: bytes, meta: dict) -> dict | None:
    """Parse brief or full extension word from KB fields.

    Returns dict with index_is_addr, index_reg, displacement, or None.
    """
    # Try brief first
    for key, full in [("ea_brief_ext_word", False), ("ea_full_ext_word", True)]:
        fields_def = meta.get(key)
        if not fields_def:
            continue

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

        displacement = fields.get("DISPLACEMENT", 0)

        if full:
            # Full ext word: displacement comes from subsequent bytes
            bd_size = fields.get("BD SIZE", 0)
            if bd_size == 0:
                return None  # reserved
            elif bd_size == 1:
                displacement = 0
            elif bd_size == 2:
                if len(raw) < 6:
                    return None
                displacement = struct.unpack_from(">h", raw, 4)[0]
            elif bd_size == 3:
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

        return {
            "index_is_addr": bool(fields.get("D/A", 0)),
            "index_reg": fields.get("REGISTER", 0),
            "displacement": displacement,
        }

    return None


# ── EA analysis helpers ──────────────────────────────────────────────────

def _is_indexed_ea(raw: bytes, kb: KB, inst_kb: dict = None) -> dict | None:
    """Check if instruction uses indexed EA (An+Xn or PC+Xn)."""
    if len(raw) < 4:
        return None

    ext_info = _parse_ext_word(
        struct.unpack_from(">H", raw, 2)[0], raw, kb.meta)
    if ext_info is None:
        return None

    target_kb = inst_kb or kb.by_name.get("JMP")
    if target_kb is None:
        return None
    ea_spec = kb.ea_field_spec(target_kb)
    if ea_spec is None:
        return None

    opcode = struct.unpack_from(">H", raw, 0)[0]
    mode = xf(opcode, ea_spec[0])
    reg = xf(opcode, ea_spec[1])

    pcindex = kb.ea_enc.get("pcindex")
    index = kb.ea_enc.get("index")

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
    pcindex = kb.ea_enc.get("pcindex")
    if pcindex and mode == pcindex[0] and reg == pcindex[1]:
        ei = _is_indexed_ea(inst.raw, kb, lea_kb)
        if ei and ei["base_mode"] == "pc":
            return inst.offset + kb.opword_bytes + ei["displacement"]

    # PC-displacement (pcdisp): LEA d(PC),An
    pcdisp = kb.ea_enc.get("pcdisp")
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
                            max_entries=256):
    """Read word-offset table. target = base_addr + entry."""
    targets = []
    for i in range(max_entries):
        ea = table_addr + i * 2
        if ea + 2 > code_size:
            break
        offset = struct.unpack_from(">h", code, ea)[0]
        target = (base_addr + offset) & 0xFFFFFFFF
        if target >= code_size or target & 1:
            break
        targets.append(target)
    return targets


def _scan_self_relative_table(code, table_addr, code_size, max_entries=256):
    """Read self-relative word table. target = &entry + entry."""
    targets = []
    for i in range(max_entries):
        ea = table_addr + i * 2
        if ea + 2 > code_size:
            break
        offset = struct.unpack_from(">h", code, ea)[0]
        target = ea + offset
        if target < 0 or target >= code_size or target & 1:
            break
        targets.append(target)
    return targets


def _scan_inline_dispatch(code, base_addr, code_size, kb: KB,
                          max_entries=64):
    """Decode inline BRA.S/BRA.W entries at base_addr. KB-driven."""
    bra_kb = kb.by_name.get("BRA")
    if not bra_kb:
        return []

    # Build BRA opcode pattern from KB encoding
    enc = bra_kb["encodings"][0]
    fixed = mask = 0
    for f in enc["fields"]:
        if f["name"] in ("0", "1"):
            for b in range(f["bit_lo"], f["bit_hi"] + 1):
                mask |= 1 << b
                if f["name"] == "1":
                    fixed |= 1 << b

    disp_enc = bra_kb.get("constraints", {}).get("displacement_encoding")
    disp_f = next((f for f in enc["fields"]
                   if "DISPLACEMENT" in f["name"].upper()), None)
    if not disp_enc or not disp_f:
        return []

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

    return targets


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
            ind_enc = kb.ea_enc.get("ind")
            ea_spec = kb.ea_field_spec(ikb)
            if ind_enc and ea_spec and len(last.raw) >= 2:
                opcode = struct.unpack_from(">H", last.raw, 0)[0]
                if xf(opcode, ea_spec[0]) == ind_enc[0]:
                    jmp_reg = xf(opcode, ea_spec[1])
                    has_adda = False
                    table_base = None
                    for inst in reversed(block.instructions[:-1]):
                        it = inst.text.strip().lower()
                        if (it.startswith("adda") and f"(a{jmp_reg})" in it
                                and f"a{jmp_reg}" in it.split(",")[-1]):
                            has_adda = True
                        elif ikb_is_lea(inst, kb):
                            if _get_lea_dst_reg(inst, kb) == jmp_reg:
                                table_base = _resolve_lea_pc(inst, kb)
                            break

                    if has_adda and table_base is not None:
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

        # Pattern C: PC-relative indexed
        if ea_info["base_mode"] == "pc":
            base = last.offset + kb.opword_bytes + ea_info["displacement"]
            targets = _scan_inline_dispatch(code, base, code_size, kb)
            if targets:
                tables.append({"addr": base, "pattern": "pc_inline_dispatch",
                               "targets": targets, "dispatch_block": addr})
                continue
            targets = _scan_word_offset_table(code, base, base, code_size)
            if len(targets) >= 2:
                tables.append({"addr": base, "pattern": "pc_word_offset",
                               "targets": targets, "dispatch_block": addr})
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
                        code, table_start, target_base, code_size)
                    if len(targets) >= 2:
                        tables.append({
                            "addr": table_start,
                            "pattern": "indirect_table_read",
                            "targets": targets,
                            "dispatch_block": addr,
                        })
                    continue

                has_adda = any(
                    inst.text.strip().lower().startswith("adda")
                    and f"(a{base_reg})" in inst.text.lower()
                    for inst in block.instructions[-3:])
                if has_adda:
                    targets = _scan_self_relative_table(
                        code, lea_addr, code_size)
                else:
                    table_start = lea_addr + ea_info["displacement"]
                    targets = _scan_word_offset_table(
                        code, table_start, lea_addr, code_size)
                if len(targets) >= 2:
                    pattern = "self_relative_word" if has_adda else "word_offset"
                    tables.append({"addr": lea_addr if has_adda else table_start,
                                   "pattern": pattern, "targets": targets,
                                   "dispatch_block": addr})

    return tables


def ikb_is_lea(inst, kb: KB) -> bool:
    """Check if instruction is LEA via KB operation text."""
    ikb = kb.find(_extract_mnemonic(inst.text))
    return ikb is not None and ikb.get("operation") == "< ea > \u2192 An"


# ── Indirect target resolution ───────────────────────────────────────────

def resolve_indirect_targets(blocks: dict[int, BasicBlock],
                             exit_states: dict, code_size: int) -> list[dict]:
    """Resolve indirect JMP/JSR (An) and RTS via propagated state.

    For JMP/JSR (An): reads the target from the propagated register value.
    For RTS: reads the return address from the stack via propagated SP + memory.
    """
    kb = KB()
    ind_enc = kb.ea_enc.get("ind")
    if ind_enc is None:
        return []
    # Instruction alignment from KB opword_bytes (2 → must be even)
    align_mask = kb.opword_bytes - 1

    def _valid_target(addr):
        return 0 <= addr < code_size and not (addr & align_mask)

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

        # RTS: read return address from stack
        if ft == "return" and addr in exit_states:
            cpu, mem = exit_states[addr]
            if cpu.sp.is_known:
                ret_val = mem.read(cpu.sp.concrete, "l")
                if ret_val.is_known and _valid_target(ret_val.concrete):
                    resolved.append({
                        "dispatch_block": addr,
                        "register": "SP",
                        "target": ret_val.concrete,
                    })
            continue

        if ft not in ("call", "jump"):
            continue
        if _extract_branch_target(last, last.offset) is not None:
            continue

        ea_spec = kb.ea_field_spec(ikb)
        if ea_spec is None or len(last.raw) < kb.opword_bytes:
            continue
        opcode = struct.unpack_from(">H", last.raw, 0)[0]
        if xf(opcode, ea_spec[0]) != ind_enc[0]:
            continue

        reg = xf(opcode, ea_spec[1])
        if addr not in exit_states:
            continue
        cpu, _ = exit_states[addr]
        val = cpu.a[reg]
        if val.is_known and _valid_target(val.concrete):
            resolved.append({"dispatch_block": addr, "register": f"A{reg}",
                             "target": val.concrete})

    return resolved


# ── Demand-driven memory dispatch resolution ─────────────────────────────

def resolve_memory_dispatches(blocks: dict[int, BasicBlock],
                              code: bytes, code_size: int) -> list[dict]:
    """Resolve indirect JMP/JSR (An) fed by MOVEA.L d(An),Am memory loads.

    Demand-driven: scans raw binary for both dispatch sites and store
    sites.  When a slot has both a MOVEA.L load + JMP/JSR dispatch AND
    stores with statically-known values, the stored targets are resolved.

    Each caller context contributes its own targets — the dispatch site
    accumulates all of them rather than joining to unknown.
    """
    kb = KB()
    ind_enc = kb.ea_enc.get("ind")
    disp_enc = kb.ea_enc.get("disp")
    if ind_enc is None or disp_enc is None:
        return []
    align_mask = kb.opword_bytes - 1
    ow = kb.opword_bytes

    def _valid_target(addr):
        return 0 <= addr < code_size and not (addr & align_mask)

    # Decode all instructions from raw binary.
    d = _Decoder(code, 0)
    all_instrs = []
    while d.pos < code_size:
        pos = d.pos
        try:
            inst = _decode_one(d, None)
            if inst is None:
                break
            all_instrs.append(inst)
        except (DecodeError, struct.error):
            d.pos = pos + 2

    # Step 1: find MOVEA.L d(An),Am + JMP/JSR (Am) pairs in raw binary.
    dispatches = {}  # (slot, base_reg) -> list of (dispatch_addr, flow_type)
    for i, inst in enumerate(all_instrs):
        ikb = kb.find(_extract_mnemonic(inst.text))
        if ikb is None:
            continue
        ft, _ = kb.flow_type(inst)
        if ft not in ("call", "jump"):
            continue
        ea_spec = kb.ea_field_spec(ikb)
        if ea_spec is None or len(inst.raw) < ow:
            continue
        opcode = struct.unpack_from(">H", inst.raw, 0)[0]
        if xf(opcode, ea_spec[0]) != ind_enc[0]:
            continue
        dispatch_reg = xf(opcode, ea_spec[1])

        # Look backwards for MOVEA.L d(An),Am
        for j in range(max(0, i - 5), i):
            prev = all_instrs[j]
            mi = kb.find(_extract_mnemonic(prev.text))
            if mi is None or len(prev.raw) < 4:
                continue
            mi_ea = kb.ea_field_spec(mi)
            if mi_ea is None:
                continue
            mi_op = struct.unpack_from(">H", prev.raw, 0)[0]
            if xf(mi_op, mi_ea[0]) != disp_enc[0]:
                continue
            mi_dst = kb.dst_reg_field(mi)
            if mi_dst is None or xf(mi_op, mi_dst) != dispatch_reg:
                continue
            base_reg = xf(mi_op, mi_ea[1])
            slot = struct.unpack_from(">h", prev.raw, ow)[0]
            dispatches.setdefault((slot, base_reg), []).append(
                (inst.offset, ft))
            break

    if not dispatches:
        return []

    # Step 2: scan for stores to those slots with known values.
    slot_targets = {}  # (slot, base_reg) -> set of target addresses

    for i, inst in enumerate(all_instrs):
        text_lower = inst.text.strip().lower()
        if not text_lower.startswith("move.l"):
            continue
        for slot, base_reg in dispatches:
            pat = f"{slot}(a{base_reg})"
            if pat not in text_lower:
                continue
            parts = text_lower.split(",")
            if len(parts) != 2 or parts[1].strip() != pat:
                continue
            src = parts[0].replace("move.l", "").strip()

            # Source is An -> look back for LEA d(PC),An
            if len(src) == 2 and src[0] == "a" and src[1].isdigit():
                an = int(src[1])
                for j in range(max(0, i - 4), i):
                    ptxt = all_instrs[j].text.strip().lower()
                    if (ptxt.startswith("lea") and "(pc)" in ptxt
                            and f"a{an}" in ptxt
                            and len(all_instrs[j].raw) >= 4):
                        disp = struct.unpack_from(
                            ">h", all_instrs[j].raw, ow)[0]
                        target = all_instrs[j].offset + ow + disp
                        if _valid_target(target):
                            slot_targets.setdefault(
                                (slot, base_reg), set()).add(target)

            # Source is #immediate
            elif src.startswith("#"):
                try:
                    val = int(src[1:].replace("$", "0x"), 0)
                except ValueError:
                    continue
                if _valid_target(val):
                    slot_targets.setdefault(
                        (slot, base_reg), set()).add(val)

    # Step 3: cross-reference dispatches with stored targets.
    resolved = []
    for key, dispatch_list in dispatches.items():
        targets = slot_targets.get(key, set())
        if not targets:
            continue
        slot, base_reg = key
        for dispatch_addr, ft in dispatch_list:
            for target in targets:
                resolved.append({
                    "dispatch_block": dispatch_addr,
                    "slot": f"d({slot})(A{base_reg})",
                    "target": target,
                    "pattern": "memory_dispatch",
                    "flow_type": ft,
                })

    return resolved
