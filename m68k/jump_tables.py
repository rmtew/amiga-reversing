"""Jump table detection for M68K code.

All M68K knowledge from KB. Supported patterns:

Jump tables (detect_jump_tables):
  A. Word-offset dispatch: LEA base,An; JMP/JSR disp(An,Dn.w)
  B. Self-relative dispatch: LEA d(PC,Dn),An; ADDA.W (An),An; JMP (An)
  C. PC-relative inline: JMP/JSR disp(PC,Dn.w) with BRA.S entries
  D. Indirect table read: LEA d(PC),An; MOVE.W d1(An,Dn),Dn; JSR d2(An,Dn)

"""

import struct

from m68k_kb import runtime_m68k_analysis
from m68k_kb import runtime_m68k_decode

from .decode_errors import DecodeError
from .instruction_kb import instruction_flow, instruction_kb
from .instruction_primitives import extract_branch_target
from .m68k_executor import BasicBlock
from . import address_reconstruction
from . import indirect_core
from .m68k_disasm import _Decoder, _decode_one
from .instruction_decode import decode_inst_operands, xf
from . import table_recovery
from . import subroutine_summary
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


# -- Extension word parsing (from KB field definitions) -------------------

# -- EA analysis helpers --------------------------------------------------

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

# -- Table scanning -------------------------------------------------------

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


def _scan_sparse_word_offset_table(code, table_addr, base_addr, code_size,
                                   entry_count: int):
    """Read a bounded word-offset table where zero means no target."""
    word_size = runtime_m68k_decode.SIZE_BYTE_COUNT["w"]
    targets = []
    entries = []
    for i in range(entry_count):
        entry_addr = table_addr + i * word_size
        if entry_addr + word_size > code_size:
            break
        offset = struct.unpack_from(">h", code, entry_addr)[0]
        if offset == 0:
            continue
        target = (base_addr + offset) & runtime_m68k_analysis.ADDR_MASK
        if target >= code_size or target & runtime_m68k_decode.ALIGN_MASK:
            continue
        targets.append(target)
        entries.append({
            "offset_addr": entry_addr,
            "target": target,
        })
    return {
        "addr": table_addr,
        "entries": entries,
        "table_end": table_addr + entry_count * word_size,
        "targets": targets,
    }


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


def _scan_string_dispatch_table(code, table_addr, target_limit, code_size):
    """Decode len+key+self-relative-word string dispatch entries."""
    targets = []
    entries = []
    pos = table_addr
    limit = min(target_limit, code_size)
    scanned_end = table_addr
    while pos < limit:
        entry_len = code[pos]
        if entry_len == 0:
            scanned_end = pos + 1
            break
        next_pos = pos + entry_len + 3
        if next_pos > limit:
            break
        offset_pos = pos + entry_len + 1
        offset = struct.unpack_from(">h", code, offset_pos)[0]
        target = offset_pos + offset
        if (0 <= target < code_size
                and not (target & runtime_m68k_decode.ALIGN_MASK)):
            targets.append(target)
            entries.append({
                "addr": pos,
                "offset_addr": offset_pos,
                "target": target,
                "end": next_pos,
            })
        pos = next_pos
        scanned_end = pos
    return {
        "addr": table_addr,
        "entries": entries,
        "table_end": scanned_end,
        "targets": targets,
    }


def _find_dispatch_call_reg(last) -> int | None:
    operand, _ = indirect_core.decode_jump_ea(last)
    if operand is None or operand.mode != "ind":
        return None
    return operand.reg


def _find_dispatch_call_index_reg(last, mnemonic: str | None) -> int | None:
    ea_info = _is_indexed_ea(last, mnemonic)
    if ea_info is None:
        return None
    return ea_info["index_reg"]


def _find_preceding_direct_call(block: BasicBlock) -> int | None:
    for inst in reversed(block.instructions):
        ft, _ = instruction_flow(inst)
        if ft != _FLOW_CALL:
            continue
        target = extract_branch_target(inst, inst.offset)
        if target is not None:
            return target
    return None


def _find_sparse_pc_indirect_table(pred: BasicBlock, call_inst, code: bytes,
                                   code_size: int, target_reg: int,
                                   blocks: dict[int, BasicBlock] | None = None) -> dict | None:
    call_kb = instruction_kb(call_inst)
    call_ea = _is_indexed_ea(call_inst, call_kb)
    if call_ea is None or call_ea["base_mode"] != "pc" or call_ea["index_reg"] != target_reg:
        return None

    table_addr = call_inst.offset + runtime_m68k_decode.OPWORD_BYTES + call_ea["displacement"]
    entry_count = None
    saw_zero_branch = False
    saw_load = False

    search_blocks = [pred]
    if blocks is not None:
        seen = {pred.start}
        frontier = [pred]
        for _ in range(2):
            next_frontier = []
            for block in frontier:
                for pred_addr in block.predecessors:
                    pred2 = blocks.get(pred_addr)
                    if pred2 is None or pred2.start in seen:
                        continue
                    seen.add(pred2.start)
                    search_blocks.append(pred2)
                    next_frontier.append(pred2)
            frontier = next_frontier
    search_blocks.sort(key=lambda block: block.start)

    for block in search_blocks:
        for idx, inst in enumerate(block.instructions):
            mnemonic = instruction_kb(inst)
            decoded = decode_inst_operands(inst, mnemonic)
            ea_info = _is_indexed_ea(inst, mnemonic)

            if ea_info is not None and ea_info["base_mode"] == "pc":
                dst_field = runtime_m68k_decode.DEST_REG_FIELD.get(mnemonic)
                if dst_field and len(inst.raw) >= runtime_m68k_decode.OPWORD_BYTES:
                    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
                    dst_reg = xf(opcode, dst_field)
                    load_base = inst.offset + runtime_m68k_decode.OPWORD_BYTES + ea_info["displacement"]
                    if dst_reg == target_reg and load_base == table_addr:
                        saw_load = True
                        continue

            if (runtime_m68k_analysis.OPERATION_TYPES.get(mnemonic)
                    == runtime_m68k_analysis.OperationType.COMPARE):
                compared_reg = decoded.get("reg_num")
                if compared_reg is None and decoded.get("ea_op") is not None:
                    ea_op = decoded["ea_op"]
                    if ea_op.mode == "dn":
                        compared_reg = ea_op.reg
                imm_val = decoded.get("imm_val")
                if imm_val is None and decoded.get("ea_op") is not None:
                    ea_op = decoded["ea_op"]
                    if ea_op.mode == "imm":
                        imm_val = ea_op.value
                next_inst = block.instructions[idx + 1] if idx + 1 < len(block.instructions) else None
                if (next_inst is not None
                        and instruction_flow(next_inst)[0] == _FLOW_BRANCH
                        and compared_reg is not None
                        and imm_val is not None):
                    entry_count = imm_val
                    continue

            if (block is pred
                    and inst is pred.instructions[-1]
                    and instruction_flow(inst)[0] == _FLOW_BRANCH
                    and instruction_flow(inst)[1]):
                saw_zero_branch = True

    if not saw_load or not saw_zero_branch or entry_count is None or entry_count < 2:
        return None
    return _scan_sparse_word_offset_table(code, table_addr, table_addr, code_size, entry_count)


def _find_dispatch_decoder_entry(blocks: dict[int, BasicBlock], pred: BasicBlock) -> int | None:
    seen = set()
    work = [pred]
    while work:
        block = work.pop(0)
        if block.start in seen:
            continue
        seen.add(block.start)
        sub_entry = _find_preceding_direct_call(block)
        if sub_entry is not None:
            return sub_entry
        for pred_addr in block.predecessors:
            pred2 = blocks.get(pred_addr)
            if pred2 is None:
                continue
            if pred2.start not in seen:
                work.append(pred2)
    return None


def _find_string_dispatch_targets(blocks: dict[int, BasicBlock], code: bytes,
                                  code_size: int, call_targets: set[int],
                                  sub_entry: int, target_reg: int) -> dict | None:
    owned = subroutine_summary.find_sub_blocks(sub_entry, blocks, call_targets)
    instructions = []
    for addr in sorted(owned):
        instructions.extend(blocks[addr].instructions)
    if not instructions:
        return None

    table_base = None
    table_end = None
    saw_skip = False
    saw_target_calc = False
    pc_lea_targets = {}

    for inst in instructions:
        ikb = instruction_kb(inst)
        if address_reconstruction.is_lea(inst):
            dst = address_reconstruction._get_lea_dst_reg(inst)
            decoded = decode_inst_operands(inst, ikb)
            ea_op = decoded.get("ea_op")
            if ea_op is None:
                continue
            if ea_op.mode == "pcdisp":
                resolved = address_reconstruction._resolve_lea_pc(inst)
                if resolved is not None and dst is not None:
                    pc_lea_targets[dst] = resolved
                    if dst == target_reg and table_base is None:
                        table_base = resolved
                continue
            if ea_op.mode != "index" or dst != target_reg or ea_op.index_is_addr:
                continue
            if ea_op.reg == target_reg and ea_op.value == 2:
                saw_skip = True
            elif ea_op.value == -2:
                saw_target_calc = True
            continue

        if ikb != "CMPA":
            continue
        decoded = decode_inst_operands(inst, ikb)
        ea_op = decoded.get("ea_op")
        if decoded.get("reg_num") != target_reg or ea_op is None or ea_op.mode != "an":
            continue
        table_end = pc_lea_targets.get(ea_op.reg)

    if table_base is None or table_end is None or not saw_skip or not saw_target_calc:
        return None
    return _scan_string_dispatch_table(code, table_base, table_end, code_size)


# -- Main detection -------------------------------------------------------

def detect_jump_tables(blocks: dict[int, BasicBlock],
                       code: bytes, base_addr: int = 0) -> list[dict]:
    """Detect jump tables with explicit dispatch sites."""
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

        if ft == _FLOW_CALL:
            dispatch_reg = _find_dispatch_call_reg(last)
            if dispatch_reg is None:
                dispatch_reg = _find_dispatch_call_index_reg(last, ikb)
            if dispatch_reg is not None:
                call_pc_sparse = None
                for pred_addr in block.predecessors:
                    pred = blocks.get(pred_addr)
                    if pred is None or not pred.instructions:
                        continue
                    call_pc_sparse = _find_sparse_pc_indirect_table(
                        pred, last, code, code_size, dispatch_reg, blocks)
                    if call_pc_sparse is not None and len(call_pc_sparse["targets"]) >= 2:
                        tables.append({
                            "addr": call_pc_sparse["addr"],
                            "entries": call_pc_sparse["entries"],
                            "pattern": "pc_sparse_word_offset",
                            "targets": call_pc_sparse["targets"],
                            "dispatch_sites": [addr],
                            "dispatch_block": addr,
                            "base_addr": call_pc_sparse["addr"],
                            "table_end": call_pc_sparse["table_end"],
                        })
                        break
                    pred_ft, pred_conditional = instruction_flow(pred.instructions[-1])
                    if pred_ft != _FLOW_BRANCH or not pred_conditional:
                        continue
                    sub_entry = _find_dispatch_decoder_entry(blocks, pred)
                    if sub_entry is None:
                        continue
                    table_info = _find_string_dispatch_targets(
                        blocks, code, code_size, _call_targets, sub_entry, dispatch_reg)
                    if table_info is not None and len(table_info["targets"]) >= 2:
                        tables.append({
                            "addr": table_info["addr"],
                            "entries": table_info["entries"],
                            "pattern": "string_dispatch_self_relative",
                            "targets": table_info["targets"],
                            "dispatch_sites": [addr],
                            "dispatch_block": addr,
                            "base_addr": None,
                            "decoder_entry": sub_entry,
                            "table_end": table_info["table_end"],
                        })
                        break
                if tables and tables[-1]["dispatch_block"] == addr:
                    continue

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
                    "dispatch_sites": [addr],
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
                            "dispatch_sites": [addr],
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
                            "dispatch_sites": [addr],
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
                                    "dispatch_sites": [addr],
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
                               "targets": targets, "dispatch_sites": [addr], "dispatch_block": addr,
                               "table_end": dispatch_end})
                continue
            targets = _scan_word_offset_table(
                code, base, base, code_size, call_targets=_call_targets)
            if len(targets) >= 2:
                tables.append({"addr": base, "pattern": "pc_word_offset",
                               "targets": targets, "dispatch_sites": [addr], "dispatch_block": addr,
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
                            "dispatch_sites": [addr],
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
                                   "dispatch_sites": [addr],
                                   "dispatch_block": addr,
                                   "base_addr": None if has_adda else lea_addr,
                                   "table_end": tbl_addr + len(targets) * runtime_m68k_decode.SIZE_BYTE_COUNT["w"]})

    return tables

# -- Indirect target resolution -------------------------------------------

