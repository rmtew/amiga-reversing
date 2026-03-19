"""Shared KB-driven address/base reconstruction helpers."""

import struct

from .kb_util import decode_destination, decode_instruction_operands, xf
from . import value_transforms as _vt


def _immediate_an_adjustment(mi: dict, decoded: dict,
                             current_reg: int) -> int | None:
    """Return signed immediate delta for supported An adjustment forms."""
    op_type = mi.get("operation_type")
    ea_op = decoded.get("ea_op")

    if (op_type in ("add", "sub")
            and decoded.get("imm_val") is not None
            and ea_op is not None
            and ea_op.mode == "an"
            and ea_op.reg == current_reg):
        imm = decoded["imm_val"]
        return imm if op_type == "add" else -imm

    if (mi.get("source_sign_extend")
            and op_type in ("add", "sub")
            and decoded.get("reg_num") == current_reg
            and ea_op is not None
            and ea_op.mode == "imm"
            and ea_op.value is not None):
        imm = ea_op.value
        return imm if op_type == "add" else -imm

    return None


def _resolve_lea_pc(inst, kb) -> int | None:
    """Resolve a LEA instruction's PC-relative source address."""
    from . import static_values as _sv

    lea_kb = kb.find("lea")
    if lea_kb is None:
        return None
    decoded = decode_instruction_operands(
        inst.raw, lea_kb, kb.meta, inst.operand_size, inst.offset)
    ea_op = decoded.get("ea_op")
    if ea_op is None:
        return None
    if ea_op.mode == "pcdisp":
        return ea_op.value
    if (ea_op.mode == "pcindex"
            and not ea_op.full_extension
            and not ea_op.memory_indirect
            and not ea_op.base_suppressed
            and not ea_op.index_suppressed):
        index_mode = "an" if ea_op.index_is_addr else "dn"
        index_val = _sv._resolve_block_constant_reg(
            [inst], kb, index_mode, ea_op.index_reg, inst.offset + inst.size)
        if index_val is None:
            return ea_op.value
        if ea_op.index_size == "w":
            index_val &= 0xFFFF
            if index_val & 0x8000:
                index_val -= 0x10000
        return (ea_op.value + index_val * ea_op.index_scale) & kb.addr_mask
    return None


def _get_lea_dst_reg(inst, kb) -> int | None:
    """Get destination register number from a LEA instruction."""
    lea_kb = kb.find("lea")
    if lea_kb is None:
        return None
    dst_spec = kb.dst_reg_field(lea_kb)
    if dst_spec is None:
        return None
    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    return xf(opcode, dst_spec)


def is_lea(inst, kb) -> bool:
    """Check if instruction is LEA via KB operation text."""
    ikb = kb.instruction_kb(inst)
    return ikb is not None and ikb.get("operation_class") == "load_effective_address"


def _static_an_source_base(mi: dict, decoded: dict,
                           current_reg: int, instructions,
                           kb, inst_offset: int) -> int | None:
    """Return concrete static source used to seed An, if any."""
    from . import static_values as _sv

    if not mi.get("source_sign_extend"):
        return None
    if decoded.get("reg_num") != current_reg:
        return None
    ea_op = decoded.get("ea_op")
    if ea_op is None:
        return None
    if (mi.get("operation_type") == "move"
            and ea_op.mode == "imm"
            and ea_op.value is not None):
        return ea_op.value
    if mi.get("operation_type") == "move" and ea_op.mode in ("dn", "an"):
        return _sv._resolve_block_constant_reg(
            instructions, kb, ea_op.mode, ea_op.reg, inst_offset)
    if ea_op.mode == "pcdisp":
        return ea_op.value
    if (ea_op.mode == "pcindex"
            and not ea_op.full_extension
            and not ea_op.memory_indirect
            and not ea_op.base_suppressed
            and not ea_op.index_suppressed):
        index_mode = "an" if ea_op.index_is_addr else "dn"
        index_val = _sv._resolve_block_constant_reg(
            instructions, kb, index_mode, ea_op.index_reg, inst_offset)
        if index_val is None:
            return None
        if ea_op.index_size == "w":
            index_val &= 0xFFFF
            if index_val & 0x8000:
                index_val -= 0x10000
        return (ea_op.value + index_val * ea_op.index_scale) & kb.addr_mask
    return None


def resolve_block_pc_base(instructions, kb, target_reg: int) -> int | None:
    """Resolve An back to a PC-relative LEA through simple register copies."""
    from . import static_values as _sv

    current_reg = target_reg
    offset = 0
    for inst in reversed(instructions):
        if is_lea(inst, kb):
            if _get_lea_dst_reg(inst, kb) == current_reg:
                base = _resolve_lea_pc(inst, kb)
                if base is not None:
                    return base + offset
                return None
            continue

        mi = kb.instruction_kb(inst)
        decoded = decode_instruction_operands(
            inst.raw, mi, kb.meta, inst.operand_size, inst.offset)
        static_base = _static_an_source_base(
            mi, decoded, current_reg, instructions, kb, inst.offset)
        if static_base is not None:
            return static_base + offset
        delta = _immediate_an_adjustment(mi, decoded, current_reg)
        if delta is not None:
            offset += delta
            continue
        ea_op = decoded.get("ea_op")
        if (mi.get("source_sign_extend")
                and mi.get("operation_type") in ("add", "sub")
                and decoded.get("reg_num") == current_reg
                and ea_op is not None
                and ea_op.mode in ("dn", "an")):
            src_val = _sv._resolve_block_constant_reg(
                instructions, kb, ea_op.mode, ea_op.reg, inst.offset)
            if src_val is not None:
                offset += src_val if mi.get("operation_type") == "add" else -src_val
                continue
        dst = decode_destination(inst.raw, mi, kb.meta, inst.operand_size, inst.offset)
        if (dst == ("an", current_reg)
                and mi.get("operation_type") in ("add", "sub")
                and ea_op is not None
                and ea_op.mode in ("dn", "an")):
            src_val = _sv._resolve_block_constant_reg(
                instructions, kb, ea_op.mode, ea_op.reg, inst.offset)
            if src_val is not None:
                offset += src_val if mi.get("operation_type") == "add" else -src_val
                continue
        if mi.get("operation_type") == "swap":
            partner = _vt._swap_partner(inst, "an", current_reg)
            if partner is not None:
                if partner[0] != "an":
                    return None
                current_reg = partner[1]
                continue
        if dst != ("an", current_reg):
            continue
        if ea_op is None or ea_op.mode != "an":
            return None
        current_reg = ea_op.reg
    return None
