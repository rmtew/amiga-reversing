"""Shared KB-driven address/base reconstruction helpers."""

from __future__ import annotations

import struct
from collections.abc import Sequence
from typing import Protocol, cast

from m68k_kb import runtime_m68k_analysis
from m68k_kb import runtime_m68k_decode

from .constant_evaluator import SizedInstructionLike
from .instruction_kb import find_kb_entry, instruction_kb
from .instruction_decode import DecodedOperands, decode_inst_destination, decode_inst_operands, xf
from . import value_transforms as _vt


class AddressReconstructionInstructionLike(Protocol):
    @property
    def offset(self) -> int: ...

    @property
    def size(self) -> int: ...

    @property
    def raw(self) -> bytes: ...

    @property
    def kb_mnemonic(self) -> str | None: ...

    @property
    def operand_size(self) -> str | None: ...

    @property
    def operand_nodes(self) -> Sequence[object] | None: ...


def _immediate_an_adjustment(mnemonic: str, decoded: DecodedOperands,
                             current_reg: int) -> int | None:
    """Return signed immediate delta for supported An adjustment forms."""
    op_type = runtime_m68k_analysis.OPERATION_TYPES.get(mnemonic)
    ea_op = decoded.ea_op

    if (op_type in (
            runtime_m68k_analysis.OperationType.ADD,
            runtime_m68k_analysis.OperationType.SUB,
    )
            and decoded.imm_val is not None
            and ea_op is not None
            and ea_op.mode == "an"
            and ea_op.reg == current_reg):
        imm = decoded.imm_val
        assert isinstance(imm, int)
        return imm if op_type == runtime_m68k_analysis.OperationType.ADD else -imm

    if (mnemonic in runtime_m68k_analysis.SOURCE_SIGN_EXTEND
            and op_type in (
                runtime_m68k_analysis.OperationType.ADD,
                runtime_m68k_analysis.OperationType.SUB,
            )
            and decoded.reg_num == current_reg
            and ea_op is not None
            and ea_op.mode == "imm"
            and ea_op.value is not None):
        imm = ea_op.value
        assert isinstance(imm, int)
        return imm if op_type == runtime_m68k_analysis.OperationType.ADD else -imm

    return None


def _resolve_lea_pc(inst: AddressReconstructionInstructionLike) -> int | None:
    """Resolve a LEA instruction's PC-relative source address."""
    from . import static_values as _sv

    lea_kb = find_kb_entry("lea")
    if lea_kb is None:
        return None
    decoded = decode_inst_operands(inst, lea_kb)
    ea_op = decoded.ea_op
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
        index_reg = ea_op.index_reg
        if index_reg is None:
            return None
        index_val = _sv._resolve_block_constant_reg(
            cast(list[SizedInstructionLike], [inst]), index_mode, index_reg, inst.offset + inst.size)
        if index_val is None:
            return ea_op.value
        base_value = ea_op.value
        index_scale = ea_op.index_scale
        if base_value is None or index_reg is None or index_scale is None:
            return None
        if ea_op.index_size == "w":
            index_val &= 0xFFFF
            if index_val & 0x8000:
                index_val -= 0x10000
        addr_mask = runtime_m68k_analysis.ADDR_MASK
        return (base_value + index_val * index_scale) & addr_mask
    return None


def _get_lea_dst_reg(inst: AddressReconstructionInstructionLike) -> int | None:
    """Get destination register number from a LEA instruction."""
    lea_kb = find_kb_entry("lea")
    if lea_kb is None:
        return None
    dst_spec = runtime_m68k_decode.DEST_REG_FIELD.get(lea_kb)
    if dst_spec is None:
        return None
    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    return xf(opcode, dst_spec)


def is_lea(inst: AddressReconstructionInstructionLike) -> bool:
    """Check if instruction is LEA via KB operation text."""
    ikb = instruction_kb(inst)
    return (
        ikb is not None
            and runtime_m68k_analysis.OPERATION_CLASSES.get(ikb) == runtime_m68k_analysis.OperationClass.LOAD_EFFECTIVE_ADDRESS
    )


def _static_an_source_base(mnemonic: str, decoded: DecodedOperands,
                           current_reg: int, instructions: Sequence[AddressReconstructionInstructionLike],
                           inst_offset: int) -> int | None:
    """Return concrete static source used to seed An, if any."""
    from . import static_values as _sv

    if mnemonic not in runtime_m68k_analysis.SOURCE_SIGN_EXTEND:
        return None
    if decoded.reg_num != current_reg:
        return None
    ea_op = decoded.ea_op
    if ea_op is None:
        return None
    op_type = runtime_m68k_analysis.OPERATION_TYPES.get(mnemonic)
    if (op_type == runtime_m68k_analysis.OperationType.MOVE
            and ea_op.mode == "imm"
            and ea_op.value is not None):
        return ea_op.value
    if op_type == runtime_m68k_analysis.OperationType.MOVE and ea_op.mode in ("dn", "an"):
        reg = ea_op.reg
        if reg is None:
            return None
        return _sv._resolve_block_constant_reg(cast(list[SizedInstructionLike], instructions), ea_op.mode, reg, inst_offset)
    if ea_op.mode == "pcdisp":
        return ea_op.value
    if (ea_op.mode == "pcindex"
            and not ea_op.full_extension
            and not ea_op.memory_indirect
            and not ea_op.base_suppressed
            and not ea_op.index_suppressed):
        index_mode = "an" if ea_op.index_is_addr else "dn"
        index_reg = ea_op.index_reg
        if index_reg is None:
            return None
        index_val = _sv._resolve_block_constant_reg(
            cast(list[SizedInstructionLike], instructions), index_mode, index_reg, inst_offset)
        if index_val is None:
            return None
        base_value = ea_op.value
        index_scale = ea_op.index_scale
        if base_value is None or index_scale is None:
            return None
        if ea_op.index_size == "w":
            index_val &= 0xFFFF
            if index_val & 0x8000:
                index_val -= 0x10000
        addr_mask = runtime_m68k_analysis.ADDR_MASK
        return (base_value + index_val * index_scale) & addr_mask
    return None


def resolve_block_pc_base(instructions: Sequence[AddressReconstructionInstructionLike], target_reg: int) -> int | None:
    """Resolve An back to a PC-relative LEA through simple register copies."""
    from . import static_values as _sv

    current_reg = target_reg
    offset = 0
    for inst in reversed(instructions):
        if is_lea(inst):
            if _get_lea_dst_reg(inst) == current_reg:
                base = _resolve_lea_pc(inst)
                if base is not None:
                    return base + offset
                return None
            continue

        mi = instruction_kb(inst)
        decoded = decode_inst_operands(inst, mi)
        static_base = _static_an_source_base(
            mi, decoded, current_reg, instructions, inst.offset)
        if static_base is not None:
            return static_base + offset
        delta = _immediate_an_adjustment(mi, decoded, current_reg)
        if delta is not None:
            offset += delta
            continue
        mnemonic = mi
        op_type = runtime_m68k_analysis.OPERATION_TYPES.get(mnemonic)
        ea_op = decoded.ea_op
        if (mnemonic in runtime_m68k_analysis.SOURCE_SIGN_EXTEND
                and op_type in ("add", "sub")
                and decoded.reg_num == current_reg
                and ea_op is not None
                and ea_op.mode in ("dn", "an")):
            reg = ea_op.reg
            if reg is None:
                return None
            src_val = _sv._resolve_block_constant_reg(
                cast(list[SizedInstructionLike], instructions), ea_op.mode, reg, inst.offset)
            if src_val is not None:
                offset += src_val if op_type == runtime_m68k_analysis.OperationType.ADD else -src_val
                continue
        dst = decode_inst_destination(inst, mi)
        if (dst == ("an", current_reg)
                and op_type in ("add", "sub")
                and ea_op is not None
                and ea_op.mode in ("dn", "an")):
            reg = ea_op.reg
            if reg is None:
                return None
            src_val = _sv._resolve_block_constant_reg(
                cast(list[SizedInstructionLike], instructions), ea_op.mode, reg, inst.offset)
            if src_val is not None:
                offset += src_val if op_type == runtime_m68k_analysis.OperationType.ADD else -src_val
                continue
        if op_type == runtime_m68k_analysis.OperationType.SWAP:
            partner = _vt._swap_partner(cast(_vt.ExchangeInstructionLike, inst), "an", current_reg)
            if partner is not None:
                if partner[0] != "an":
                    return None
                current_reg = partner[1]
                continue
        if dst != ("an", current_reg):
            continue
        if ea_op is None or ea_op.mode != "an":
            return None
        if ea_op.reg is None:
            return None
        current_reg = ea_op.reg
    return None
