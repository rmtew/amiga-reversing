"""Shared KB-driven recursive constant register evaluation helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

from m68k_kb import runtime_m68k_decode

from . import value_transforms
from .instruction_decode import decode_inst_destination, decode_inst_operands
from .instruction_kb import instruction_kb
from .typing_protocols import OperandNodeLike

if TYPE_CHECKING:
    from disasm.decode import DecodedInstructionForEmit


class SizedInstructionLike(Protocol):
    @property
    def offset(self) -> int: ...

    @property
    def size(self) -> int: ...

    @property
    def raw(self) -> bytes: ...

    @property
    def kb_mnemonic(self) -> str | None: ...

    @property
    def opcode_text(self) -> str | None: ...

    @property
    def operand_size(self) -> str | None: ...

    @property
    def operand_nodes(self) -> Sequence[OperandNodeLike]: ...

    @property
    def decoded_operands(self) -> DecodedInstructionForEmit | None: ...


def _opcode_text(inst: SizedInstructionLike) -> str:
    opcode_text = inst.opcode_text
    assert opcode_text is not None, "Instruction is missing opcode_text"
    return opcode_text


def _operand_size(inst: SizedInstructionLike) -> str:
    operand_size = inst.operand_size
    assert operand_size is not None, "Instruction is missing operand_size"
    return operand_size


def resolve_constant_reg(instructions: Sequence[SizedInstructionLike], reg_mode: str, reg_num: int,
                         stop_before: int) -> int | None:
    """Resolve a concrete register value from local deterministic writes."""
    current_mode = reg_mode
    current_reg = reg_num
    offset = 0
    for inst in reversed(instructions):
        if inst.offset >= stop_before:
            continue
        mnemonic = instruction_kb(inst)
        op_type = runtime_m68k_decode.OPERATION_TYPES.get(mnemonic)
        decoded = decode_inst_operands(inst, mnemonic)
        ea_op = decoded.ea_op
        if (op_type == "clear"
                and ea_op is not None
                and ea_op.mode == current_mode
                and ea_op.reg == current_reg):
            return offset
        if (op_type in ("add", "sub")
                and decoded.imm_val is not None
                and ea_op is not None
                and ea_op.mode == current_mode
                and ea_op.reg == current_reg):
            imm = decoded.imm_val
            offset += imm if op_type == runtime_m68k_decode.OperationType.ADD else -imm
            continue
        if (op_type in ("add", "sub")
                and ea_op is not None
                and ea_op.mode in ("dn", "an")):
            dst = decode_inst_destination(inst, mnemonic)
            if dst == (current_mode, current_reg):
                if ea_op.reg is None:
                    assert ea_op.reg is not None, "Register EA missing register number"
                src_val = resolve_constant_reg(
                    instructions, ea_op.mode, ea_op.reg, inst.offset)
                if src_val is not None:
                    offset += src_val if op_type == runtime_m68k_decode.OperationType.ADD else -src_val
                    continue
        if (current_mode == "dn"
                and op_type in ("shift", "rotate")
                and decoded.reg_num == current_reg
                and decoded.imm_val is not None):
            src_val = resolve_constant_reg(
                instructions, current_mode, current_reg, inst.offset)
            if src_val is not None:
                shifted = value_transforms._apply_known_shift(
                    _opcode_text(inst), _operand_size(inst), src_val, decoded.imm_val)
                if shifted is not None:
                    return int(shifted + offset)
        if (current_mode == "dn"
                and op_type in ("shift", "rotate")
                and decoded.imm_val is None
                and len(inst.operand_nodes) == 2):
            src_node, dst_node = inst.operand_nodes
            if (src_node.kind == "register"
                    and dst_node.kind == "register"
                    and dst_node.register == f"d{current_reg}"
                    and src_node.register is not None
                    and src_node.register.startswith("d")):
                count_reg = int(src_node.register[1:])
                count_val = resolve_constant_reg(
                    instructions, "dn", count_reg, inst.offset)
                if count_val is not None and count_val >= 0:
                    src_val = resolve_constant_reg(
                    instructions, current_mode, current_reg, inst.offset)
                    if src_val is not None:
                        shifted = value_transforms._apply_known_shift(
                            _opcode_text(inst), _operand_size(inst), src_val, count_val)
                        if shifted is not None:
                            return int(shifted + offset)
        if (current_mode == "dn"
                and op_type in ("and", "or", "xor")
                and decoded.imm_val is not None
                and ea_op is not None
                and ea_op.mode == "dn"
                and ea_op.reg == current_reg):
            src_val = resolve_constant_reg(
                instructions, current_mode, current_reg, inst.offset)
            if src_val is not None:
                updated = value_transforms._apply_known_logical(
                    op_type, _operand_size(inst), src_val, decoded.imm_val)
                if updated is not None:
                    return int(updated + offset)
        if (current_mode == "dn"
                and op_type == "bit_test"
                and ea_op is not None
                and ea_op.mode == "dn"
                and ea_op.reg == current_reg
                and decoded.imm_val is not None):
            src_val = resolve_constant_reg(
                instructions, current_mode, current_reg, inst.offset)
            if src_val is not None:
                updated = value_transforms._apply_known_bitop(
                    _opcode_text(inst), src_val, decoded.imm_val)
                if updated is not None:
                    return int(updated + offset)
        if (current_mode == "dn"
                and op_type == "bit_test"
                and decoded.imm_val is None
                and len(inst.operand_nodes) == 2):
            src_node, dst_node = inst.operand_nodes
            if (src_node.kind == "register"
                    and dst_node.kind == "register"
                    and dst_node.register == f"d{current_reg}"
                    and src_node.register is not None
                    and src_node.register.startswith("d")):
                count_reg = int(src_node.register[1:])
                count_val = resolve_constant_reg(
                    instructions, "dn", count_reg, inst.offset)
                if count_val is not None:
                    src_val = resolve_constant_reg(
                        instructions, current_mode, current_reg, inst.offset)
                    if src_val is not None:
                        updated = value_transforms._apply_known_bitop(
                            _opcode_text(inst), src_val, count_val)
                        if updated is not None:
                            return int(updated + offset)
        if (current_mode == "dn"
                and op_type == "test"
                and ea_op is not None
                and ea_op.mode == "dn"
                and ea_op.reg == current_reg):
            src_val = resolve_constant_reg(
                instructions, current_mode, current_reg, inst.offset)
            if src_val is not None:
                updated = value_transforms._apply_known_test(
                    _opcode_text(inst), _operand_size(inst), src_val)
                if updated is not None:
                    return int(updated + offset)
        if (current_mode == "dn"
                and op_type in ("and", "or", "xor")
                and decoded.imm_val is None
                and ea_op is not None
                and ea_op.mode in ("dn", "an")):
            dst = decode_inst_destination(inst, mnemonic)
            if dst == (current_mode, current_reg):
                dst_val = resolve_constant_reg(
                    instructions, current_mode, current_reg, inst.offset)
                if ea_op.reg is None:
                    assert ea_op.reg is not None, "Register EA missing register number"
                src_val = resolve_constant_reg(
                    instructions, ea_op.mode, ea_op.reg, inst.offset)
                if dst_val is not None and src_val is not None:
                    updated = value_transforms._apply_known_logical(
                        op_type, _operand_size(inst), dst_val, src_val)
                    if updated is not None:
                        return int(updated + offset)
        if (current_mode == "dn"
                and op_type in ("not", "neg")
                and ea_op is not None
                and ea_op.mode == "dn"
                and ea_op.reg == current_reg):
            src_val = resolve_constant_reg(
                instructions, current_mode, current_reg, inst.offset)
            if src_val is not None:
                updated = value_transforms._apply_known_unary(
                    op_type, _operand_size(inst), src_val)
                if updated is not None:
                    return int(updated + offset)
        if (current_mode == "dn"
                and op_type == runtime_m68k_decode.OperationType.SWAP
                and len(inst.operand_nodes) == 1
                and inst.operand_nodes[0].kind == "register"
                and inst.operand_nodes[0].register == f"d{current_reg}"):
            src_val = resolve_constant_reg(
                instructions, current_mode, current_reg, inst.offset)
            if src_val is not None:
                return int(value_transforms._apply_known_swap(src_val) + offset)
        if op_type == runtime_m68k_decode.OperationType.SWAP:
            partner = value_transforms._swap_partner(inst, current_mode, current_reg)
            if partner is not None:
                src_val = resolve_constant_reg(
                    instructions, partner[0], partner[1], inst.offset)
                if src_val is not None:
                    return src_val + offset
        if (current_mode == "dn"
                and op_type == runtime_m68k_decode.OperationType.SIGN_EXTEND
                and len(inst.operand_nodes) == 1
                and inst.operand_nodes[0].kind == "register"
                and inst.operand_nodes[0].register == f"d{current_reg}"):
            src_val = resolve_constant_reg(
                instructions, current_mode, current_reg, inst.offset)
            if src_val is not None:
                updated = value_transforms._apply_known_sign_extend(_operand_size(inst), src_val)
                if updated is not None:
                    return int(updated + offset)
        if (current_mode == "dn"
                and op_type == "multiply"
                and len(inst.operand_nodes) == 2):
            src_node, dst_node = inst.operand_nodes
            if (src_node.kind in ("register", "immediate")
                    and dst_node.kind == "register"
                    and dst_node.register == f"d{current_reg}"):
                dst_val = resolve_constant_reg(
                    instructions, current_mode, current_reg, inst.offset)
                if src_node.kind == "register":
                    if src_node.register is None:
                        assert src_node.register is not None, "Register source node missing register name"
                    src_mode = "an" if src_node.register.startswith("a") else "dn"
                    src_val = resolve_constant_reg(
                        instructions, src_mode, int(src_node.register[1:]), inst.offset)
                else:
                    src_val = src_node.value
                if dst_val is not None and src_val is not None:
                    updated = value_transforms._apply_known_multiply(
                        _opcode_text(inst), _operand_size(inst), dst_val, src_val)
                    if updated is not None:
                        return int(updated + offset)
        if (current_mode == "dn"
                and op_type == "divide"
                and len(inst.operand_nodes) == 2):
            src_node, dst_node = inst.operand_nodes
            if (src_node.kind in ("register", "immediate")
                    and dst_node.kind == "register"
                    and dst_node.register == f"d{current_reg}"):
                dst_val = resolve_constant_reg(
                    instructions, current_mode, current_reg, inst.offset)
                if src_node.kind == "register":
                    if src_node.register is None:
                        assert src_node.register is not None, "Register source node missing register name"
                    src_mode = "an" if src_node.register.startswith("a") else "dn"
                    src_val = resolve_constant_reg(
                        instructions, src_mode, int(src_node.register[1:]), inst.offset)
                else:
                    src_val = src_node.value
                if dst_val is not None and src_val is not None:
                    updated = value_transforms._apply_known_divide(
                        _opcode_text(inst), _operand_size(inst), dst_val, src_val)
                    if updated is not None:
                        return int(updated + offset)
        dst = decode_inst_destination(inst, mnemonic)
        if dst != (current_mode, current_reg):
            continue
        if decoded.imm_val is not None:
            return int(decoded.imm_val + offset)
        if ea_op is not None and ea_op.mode == "imm" and ea_op.value is not None:
            return int(ea_op.value + offset)
        if op_type == runtime_m68k_decode.OperationType.MOVE and ea_op is not None and ea_op.mode in ("dn", "an"):
            if ea_op.reg is None:
                assert ea_op.reg is not None, "MOVE register EA missing register number"
            current_mode = ea_op.mode
            current_reg = ea_op.reg
            continue
        return None
    return None
