"""Jump table detection for M68K code.

All M68K knowledge from KB. Supported patterns:

Jump tables (detect_jump_tables):
  A. Word-offset dispatch: LEA base,An; JMP/JSR disp(An,Dn.w)
  B. Self-relative dispatch: LEA d(PC,Dn),An; ADDA.W (An),An; JMP (An)
  C. PC-relative inline: JMP/JSR disp(PC,Dn.w) with BRA.S entries
  D. Indirect table read: LEA d(PC),An; MOVE.W d1(An,Dn),Dn; JSR d2(An,Dn)

"""

import struct

from knowledge import runtime_m68k_analysis
from knowledge import runtime_m68k_decode

from .decode_errors import DecodeError
from .instruction_kb import instruction_flow, instruction_kb
from .instruction_primitives import extract_branch_target
from .m68k_executor import BasicBlock
from . import address_reconstruction
from . import indirect_core
from .m68k_disasm import _Decoder, _decode_one
from .instruction_decode import decode_inst_operands, xf
from . import table_recovery
from . import value_transforms


# Maximum RTS exits to try when forking a nested callee's per-exit
# summaries.  Each exit requires a full sub propagation, so this bounds
# the cost of per-exit resolution.  Typical M68K subroutines have 1-4
# RTS blocks; 16 covers all practical cases.
_MAX_FORK_EXITS = 16
_FLOW_BRANCH = runtime_m68k_analysis.FlowType.BRANCH
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
_FLOW_RETURN = runtime_m68k_analysis.FlowType.RETURN


# ── Extension word parsing (from KB field definitions) ───────────────────

# ── EA analysis helpers ──────────────────────────────────────────────────

def _is_indexed_ea(inst, mnemonic: str | None = None) -> dict | None:
    """Check if instruction uses indexed EA (An+Xn or PC+Xn)."""
    if len(inst.raw) < 4:
        return None
    decoded = decode_inst_operands(inst, mnemonic)
    operand = decoded.get("ea_op")
    if operand is None:
        return None
    if operand.mode == "pcindex":
        if (operand.full_extension or operand.memory_indirect
                or operand.base_suppressed or operand.index_suppressed):
            return None
        return {
            "base_mode": "pc",
            "base_reg": None,
            "index_is_addr": operand.index_is_addr,
            "index_reg": operand.index_reg,
            "displacement": operand.value - (inst.offset + runtime_m68k_decode.OPWORD_BYTES),
        }
    if operand.mode == "index":
        if (operand.full_extension or operand.memory_indirect
                or operand.base_suppressed or operand.index_suppressed):
            return None
        return {
            "base_mode": "an",
            "base_reg": operand.reg,
            "index_is_addr": operand.index_is_addr,
            "index_reg": operand.index_reg,
            "displacement": operand.value,
        }
    return None

# ── Table scanning ───────────────────────────────────────────────────────

def _scan_word_offset_table(code, table_addr, base_addr, code_size,
                            max_entries=256,
                            field_offset: int = 0, stride: int = 0,
                            call_targets: set | None = None):
    """Read word-offset table. target = base_addr + entry.

    field_offset: byte offset of the word field within each entry.
    stride: byte distance between entries (default = word size).
    call_targets: known subroutine entries -- stop before reading these.
    """
    word_size = runtime_m68k_decode.SIZE_BYTE_COUNT["w"]
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
        target = (base_addr + offset) & runtime_m68k_analysis.ADDR_MASK
        if target >= code_size or target & runtime_m68k_decode.ALIGN_MASK:
            break
        targets.append(target)
    return targets


def _scan_long_pointer_table(code, table_addr, addend, code_size,
                             max_entries=256, field_offset: int = 0,
                             stride: int = 0,
                             call_targets: set | None = None,
                             transforms=()):
    """Read long-pointer table. target = entry_long + addend."""
    long_size = runtime_m68k_decode.SIZE_BYTE_COUNT["l"]
    if stride == 0:
        stride = long_size
    targets = []
    for i in range(max_entries):
        ea = table_addr + field_offset + i * stride
        if ea + long_size > code_size:
            break
        if call_targets and ea in call_targets:
            break
        ptr = struct.unpack_from(">I", code, ea)[0]
        ptr = value_transforms._apply_pointer_transforms(ptr, transforms)
        if ptr is None:
            break
        target = (ptr + addend) & runtime_m68k_analysis.ADDR_MASK
        if target >= code_size or target & runtime_m68k_decode.ALIGN_MASK:
            break
        targets.append(target)
    return targets


def _scan_self_relative_table(code, table_addr, code_size,
                              max_entries=256,
                              call_targets: set | None = None):
    """Read self-relative word table. target = &entry + entry."""
    word_size = runtime_m68k_decode.SIZE_BYTE_COUNT["w"]
    targets = []
    for i in range(max_entries):
        ea = table_addr + i * word_size
        if ea + word_size > code_size:
            break
        if call_targets and ea in call_targets:
            break
        offset = struct.unpack_from(">h", code, ea)[0]
        target = ea + offset
        if target < 0 or target >= code_size or target & runtime_m68k_decode.ALIGN_MASK:
            break
        targets.append(target)
    return targets


def _scan_inline_dispatch(code, base_addr, code_size,
                          max_entries=64):
    """Decode inline dispatch entries at base_addr.

    Returns (targets, end_pos) where end_pos is the address after
    the last decoded entry.
    """
    targets = []
    pos = base_addr
    for _ in range(max_entries):
        if pos + runtime_m68k_decode.OPWORD_BYTES > code_size:
            break
        try:
            d = _Decoder(code, 0)
            d.pos = pos
            inst = _decode_one(d, None)
            if inst is None:
                break
            ft, _ = instruction_flow(inst)
            if ft in (_FLOW_JUMP, _FLOW_BRANCH):
                target = extract_branch_target(inst, inst.offset)
                if (target is not None
                        and 0 <= target < code_size
                        and not (target & runtime_m68k_decode.ALIGN_MASK)):
                    targets.append(target)
            pos += inst.size
        except (DecodeError, struct.error):
            break

    return targets, pos


# ── Main detection ───────────────────────────────────────────────────────

def detect_jump_tables(blocks: dict[int, BasicBlock],
                       code: bytes, base_addr: int = 0) -> list[dict]:
    """Detect jump tables. Returns list of {addr, pattern, targets, dispatch_block}."""
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
        ikb = instruction_kb(last)

        ft, _ = instruction_flow(last)

        # Detect MOVE.L An,-(SP); RTS as equivalent to JMP (An).
        # The MOVE pushes a computed address, RTS pops and jumps to it.
        # For pattern detection, treat the push register as the dispatch
        # register and the combined pair as a virtual JMP (An).
        virtual_jmp_reg = None
        if ft == _FLOW_RETURN and len(block.instructions) >= 2:
            prev = block.instructions[-2]
            prev_kb = instruction_kb(prev)
            if prev_kb and runtime_m68k_analysis.OPERATION_TYPES.get(prev_kb) == runtime_m68k_analysis.OperationType.MOVE:
                decoded = decode_inst_operands(prev, prev_kb)
                ea_op = decoded.get("ea_op")
                dst_op = decoded.get("dst_op")
                # Source must be An, destination must be predec SP
                if (ea_op and ea_op.mode == "an"
                        and dst_op and dst_op.mode == "predec"
                        and dst_op.reg == runtime_m68k_decode.SP_REG_NUM):
                    virtual_jmp_reg = ea_op.reg

        if ft not in (_FLOW_JUMP, _FLOW_CALL) and virtual_jmp_reg is None:
            continue
        if ft in (_FLOW_JUMP, _FLOW_CALL):
            if extract_branch_target(last, last.offset) is not None:
                continue  # already resolved

        jump_operand, _ = indirect_core.decode_jump_ea(last) if ft != _FLOW_RETURN else (None, None)
        ea_info = _is_indexed_ea(last, ikb) if ft != _FLOW_RETURN else None

        full_ext_info = table_recovery._find_full_extension_long_pointer_dispatch(
            jump_operand, block.instructions[:-1], code, code_size)
        if full_ext_info is not None:
            targets = _scan_long_pointer_table(
                code, full_ext_info["table_addr"], full_ext_info["addend"],
                code_size, call_targets=_call_targets)
            if len(targets) >= 2:
                tables.append({
                    "addr": full_ext_info["table_addr"],
                    "pattern": full_ext_info["pattern"],
                    "targets": targets,
                    "dispatch_block": addr,
                    "base_addr": None,
                    "table_end": (full_ext_info["table_addr"]
                                  + len(targets) * runtime_m68k_decode.SIZE_BYTE_COUNT["l"]),
                })
                continue

        # Pattern B / E: (An) dispatch with preceding ADDA
        # For real JMP (An): extract register from EA.
        # For virtual JMP (PUSH+RTS): use the push source register.
        if ea_info is None and len(block.instructions) >= 3:
            ind_enc = runtime_m68k_decode.EA_MODE_ENCODING["ind"]
            if virtual_jmp_reg is not None:
                jmp_reg = virtual_jmp_reg
            else:
                ea_spec = runtime_m68k_decode.EA_FIELD_SPECS.get(ikb)
                if not (ind_enc and ea_spec and len(last.raw) >= 2):
                    jmp_reg = None
                else:
                    opcode = struct.unpack_from(">H", last.raw, 0)[0]
                    if xf(opcode, ea_spec[0]) != ind_enc[0]:
                        jmp_reg = None
                    else:
                        jmp_reg = xf(opcode, ea_spec[1])
            if jmp_reg is not None:
                ptr_info = table_recovery.find_pointer_table_load(
                    block.instructions[:-1], jmp_reg, last.offset, code, code_size)
                if ptr_info is not None:
                    targets = _scan_long_pointer_table(
                        code, ptr_info["table_addr"],
                        ptr_info["addend"], code_size,
                        stride=ptr_info["stride"], call_targets=_call_targets,
                        transforms=ptr_info.get("transforms", ()))
                    if len(targets) >= 2:
                        tables.append({
                            "addr": ptr_info["table_addr"],
                            "pattern": "indirect_pointer_read",
                            "targets": targets,
                            "dispatch_block": addr,
                            "base_addr": None,
                            "table_end": (ptr_info["table_addr"]
                                + len(targets) * ptr_info["stride"]),
                        })
                        continue

                # Pattern B: self-relative ADDA (indirect source)
                has_adda = False
                table_base = None
                for inst in reversed(block.instructions[:-1]):
                    if table_recovery._is_adda_ind(inst, jmp_reg):
                        has_adda = True
                    elif address_reconstruction.is_lea(inst):
                        if address_reconstruction._get_lea_dst_reg(inst) == jmp_reg:
                            table_base = address_reconstruction._resolve_lea_pc(inst)
                        break

                if has_adda and table_base is not None:
                    targets = _scan_self_relative_table(code, table_base, code_size)
                    if len(targets) >= 2:
                        tables.append({
                            "addr": table_base,
                            "pattern": "self_relative_word",
                            "targets": targets,
                            "dispatch_block": addr,
                            "base_addr": None,
                            "table_end": table_base + len(targets) * runtime_m68k_decode.SIZE_BYTE_COUNT["w"],
                        })
                    continue

                # Pattern E: ADDA.W Dn,An where Dn
                # comes from a code-section table.
                # LEA table,Ax; MOVE.W (Ax),Dy; LEA base,An;
                # ADDA.W Dy,An; JMP (An)
                adda_src = None
                for inst in reversed(block.instructions[:-1]):
                    res = table_recovery._is_adda_reg_src(inst, jmp_reg)
                    if res:
                        adda_src = res
                        break
                    if address_reconstruction.is_lea(inst):
                        break  # hit a LEA before finding ADDA

                if adda_src is not None:
                    idx_mode, idx_reg = adda_src
                    # Find LEA that sets handler base (jmp_reg)
                    handler_base = None
                    for inst in reversed(block.instructions[:-1]):
                        if address_reconstruction.is_lea(inst):
                            if address_reconstruction._get_lea_dst_reg(inst) == jmp_reg:
                                handler_base = address_reconstruction._resolve_lea_pc(inst)
                            break

                    if handler_base is not None:
                        # Find where index_reg was loaded from
                        tbl_info = table_recovery.find_table_source(
                            block.instructions, idx_mode, idx_reg, block.instructions[-1].offset)

                        if tbl_info is not None:
                            targets = _scan_word_offset_table(
                                code, tbl_info["table_addr"],
                                handler_base, code_size,
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
            base = last.offset + runtime_m68k_decode.OPWORD_BYTES + ea_info["displacement"]
            # Scan from after the full dispatch instruction, not from
            # the PC-relative base (which may overlap the extension word)
            scan_start = last.offset + last.size
            targets, dispatch_end = _scan_inline_dispatch(code, scan_start, code_size)
            if targets:
                tables.append({"addr": scan_start,
                               "pattern": "pc_inline_dispatch",
                               "targets": targets, "dispatch_block": addr,
                               "table_end": dispatch_end})
                continue
            targets = _scan_word_offset_table(
                code, base, base, code_size, call_targets=_call_targets)
            if len(targets) >= 2:
                tables.append({"addr": base, "pattern": "pc_word_offset",
                               "targets": targets, "dispatch_block": addr,
                               "base_addr": base,
                               "table_end": base + len(targets) * runtime_m68k_decode.SIZE_BYTE_COUNT["w"]})
            continue

        # Patterns A/D: register-indexed with LEA base
        if ea_info["base_mode"] == "an":
            base_reg = ea_info["base_reg"]
            lea_addr = address_reconstruction.resolve_block_pc_base(block.instructions[:-1], base_reg)

            if lea_addr is not None:
                # Pattern D: preceding indexed read into JSR's index reg.
                # MOVE.W d1(An,Dn),Dn reads offset from table; JSR d2(An,Dn)
                # dispatches.  table = lea + d1, target = lea + d2 + entry.
                move_disp = None
                for inst in reversed(block.instructions[:-1]):
                    if address_reconstruction.is_lea(inst):
                        break
                    mi = instruction_kb(inst)
                    m_ea = _is_indexed_ea(inst, mi)
                    if (m_ea and m_ea["base_mode"] == "an"
                            and m_ea["base_reg"] == base_reg):
                        m_dst = runtime_m68k_decode.DEST_REG_FIELD.get(mi)
                        if m_dst:
                            m_op = struct.unpack_from(">H", inst.raw, 0)[0]
                            if xf(m_op, m_dst) == ea_info["index_reg"]:
                                move_disp = m_ea["displacement"]
                        break

                if move_disp is not None:
                    table_start = lea_addr + move_disp
                    target_base = lea_addr + ea_info["displacement"]
                    targets = _scan_word_offset_table(
                        code, table_start, target_base, code_size,
                        call_targets=_call_targets)
                    if len(targets) >= 2:
                        tables.append({
                            "addr": table_start,
                            "pattern": "indirect_table_read",
                            "targets": targets,
                            "dispatch_block": addr,
                            "base_addr": target_base,
                            "table_end": table_start + len(targets) * runtime_m68k_decode.SIZE_BYTE_COUNT["w"],
                        })
                    continue

                has_adda = any(
                    table_recovery._is_adda_ind(inst, base_reg)
                    for inst in block.instructions[-3:])
                if has_adda:
                    targets = _scan_self_relative_table(code, lea_addr, code_size, call_targets=_call_targets)
                else:
                    table_start = lea_addr + ea_info["displacement"]
                    targets = _scan_word_offset_table(
                        code, table_start, lea_addr, code_size,
                        call_targets=_call_targets)
                if len(targets) >= 2:
                    pattern = "self_relative_word" if has_adda else "word_offset"
                    tbl_addr = lea_addr if has_adda else table_start
                    tables.append({"addr": tbl_addr,
                                   "pattern": pattern, "targets": targets,
                                   "dispatch_block": addr,
                                   "base_addr": None if has_adda else lea_addr,
                                   "table_end": tbl_addr + len(targets) * runtime_m68k_decode.SIZE_BYTE_COUNT["w"]})

    return tables

# ── Indirect target resolution ───────────────────────────────────────────

