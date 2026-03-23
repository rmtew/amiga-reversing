"""Shared M68K decode and branch-target primitives."""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass

from m68k_kb import runtime_m68k_analysis, runtime_m68k_decode, runtime_m68k_executor
from m68k_kb.runtime_types import (
    BranchExtensionDisplacement,
    BranchInlineDisplacement,
    FieldSpec,
)

from .ea_extension import parse_full_extension
from .instruction_kb import instruction_kb
from .typing_protocols import InstructionLike

_DECODED_OPS_CACHE: dict[tuple[bytes, int, str, str, int, int], DecodedOps] = {}
BRANCH_INLINE_DISPLACEMENTS: Mapping[str, BranchInlineDisplacement] = runtime_m68k_executor.BRANCH_INLINE_DISPLACEMENTS
BRANCH_EXTENSION_DISPLACEMENTS: Mapping[str, BranchExtensionDisplacement] = runtime_m68k_executor.BRANCH_EXTENSION_DISPLACEMENTS

@dataclass
class Operand:
    mode: str
    reg: int | None
    value: int | None
    index_reg: int | None = None
    index_is_addr: bool = False
    index_size: str = "w"
    size: str | None = None
    index_scale: int = 1
    full_extension: bool = False
    memory_indirect: bool = False
    postindexed: bool = False
    base_suppressed: bool = False
    index_suppressed: bool = False
    base_displacement: int | None = None
    outer_displacement: int | None = None


@dataclass
class DecodedOps:
    ea_op: Operand | None = None
    dst_op: Operand | None = None
    reg_num: int | None = None
    ea_is_source: bool | None = None
    imm_val: int | None = None
    opcode: int = 0


def xf(word: int, field_spec: FieldSpec) -> int:
    _, bit_lo, width = field_spec
    return int((word >> bit_lo) & ((1 << width) - 1))


def decode_ea(data: bytes, pos: int, mode: int, reg: int,
              op_size: str, pc_offset: int) -> tuple[Operand, int]:
    mode_name = runtime_m68k_analysis.EA_REVERSE.get((mode, reg))
    if mode_name is None:
        raise ValueError(f"Unknown EA mode={mode} reg={reg}")

    if mode_name == "dn":
        return Operand(mode="dn", reg=reg, value=None), pos
    if mode_name == "an":
        return Operand(mode="an", reg=reg, value=None), pos
    if mode_name == "ind":
        return Operand(mode="ind", reg=reg, value=None), pos
    if mode_name == "postinc":
        return Operand(mode="postinc", reg=reg, value=None), pos
    if mode_name == "predec":
        return Operand(mode="predec", reg=reg, value=None), pos
    if mode_name == "disp":
        if pos + 2 > len(data):
            raise ValueError("Truncated displacement extension word")
        disp = struct.unpack_from(">h", data, pos)[0]
        return Operand(mode="disp", reg=reg, value=disp), pos + 2
    if mode_name == "index":
        if pos + 2 > len(data):
            raise ValueError("Truncated index extension word")
        ext = struct.unpack_from(">H", data, pos)[0]
        if ext & 0x0100:
            info, pos = parse_full_extension(
                ext, data, pos + 2, base_register=f"a{reg}", pc_offset=None
            )
            return Operand(
                mode="index",
                reg=reg,
                value=info.base_displacement,
                index_reg=info.index_reg_num,
                index_is_addr=info.index_is_addr,
                index_size=info.index_size or "w",
                index_scale=info.index_scale or 1,
                full_extension=True,
                memory_indirect=info.memory_indirect,
                postindexed=info.postindexed,
                base_suppressed=info.base_suppressed,
                index_suppressed=info.index_suppressed,
                base_displacement=info.base_displacement,
                outer_displacement=info.outer_displacement,
            ), pos
        xreg = xf(ext, runtime_m68k_analysis.EA_BRIEF_FIELDS["REGISTER"])
        xtype_bit = xf(ext, runtime_m68k_analysis.EA_BRIEF_FIELDS["D/A"])
        xsize_bit = xf(ext, runtime_m68k_analysis.EA_BRIEF_FIELDS["W/L"])
        disp_raw = xf(ext, runtime_m68k_analysis.EA_BRIEF_FIELDS["DISPLACEMENT"])
        disp_width = runtime_m68k_analysis.EA_BRIEF_FIELDS["DISPLACEMENT"][2]
        if disp_raw & (1 << (disp_width - 1)):
            disp_raw -= (1 << disp_width)
        return Operand(
            mode="index",
            reg=reg,
            value=disp_raw,
            index_reg=xreg,
            index_is_addr=(xtype_bit == 1),
            index_size="l" if xsize_bit == 1 else "w",
        ), pos + 2
    if mode_name == "absw":
        if pos + 2 > len(data):
            raise ValueError("Truncated abs.w extension word")
        addr = struct.unpack_from(">h", data, pos)[0] & 0xFFFFFFFF
        return Operand(mode="absw", reg=None, value=addr), pos + 2
    if mode_name == "absl":
        if pos + 4 > len(data):
            raise ValueError("Truncated abs.l extension words")
        addr = struct.unpack_from(">I", data, pos)[0]
        return Operand(mode="absl", reg=None, value=addr), pos + 4
    if mode_name == "pcdisp":
        if pos + 2 > len(data):
            raise ValueError("Truncated PC displacement")
        disp = struct.unpack_from(">h", data, pos)[0]
        return Operand(mode="pcdisp", reg=None, value=pc_offset + runtime_m68k_analysis.OPWORD_BYTES + disp), pos + 2
    if mode_name == "pcindex":
        if pos + 2 > len(data):
            raise ValueError("Truncated PC index extension word")
        ext = struct.unpack_from(">H", data, pos)[0]
        if ext & 0x0100:
            info, pos = parse_full_extension(
                ext, data, pos + 2, base_register="pc", pc_offset=pc_offset
            )
            return Operand(
                mode="pcindex",
                reg=None,
                value=info.base_target,
                index_reg=info.index_reg_num,
                index_is_addr=info.index_is_addr,
                index_size=info.index_size or "w",
                index_scale=info.index_scale or 1,
                full_extension=True,
                memory_indirect=info.memory_indirect,
                postindexed=info.postindexed,
                base_suppressed=info.base_suppressed,
                index_suppressed=info.index_suppressed,
                base_displacement=info.base_displacement,
                outer_displacement=info.outer_displacement,
            ), pos
        xreg = xf(ext, runtime_m68k_analysis.EA_BRIEF_FIELDS["REGISTER"])
        xtype_bit = xf(ext, runtime_m68k_analysis.EA_BRIEF_FIELDS["D/A"])
        xsize_bit = xf(ext, runtime_m68k_analysis.EA_BRIEF_FIELDS["W/L"])
        disp_raw = xf(ext, runtime_m68k_analysis.EA_BRIEF_FIELDS["DISPLACEMENT"])
        disp_width = runtime_m68k_analysis.EA_BRIEF_FIELDS["DISPLACEMENT"][2]
        if disp_raw & (1 << (disp_width - 1)):
            disp_raw -= (1 << disp_width)
        return Operand(
            mode="pcindex",
            reg=None,
            value=pc_offset + runtime_m68k_analysis.OPWORD_BYTES + disp_raw,
            index_reg=xreg,
            index_is_addr=(xtype_bit == 1),
            index_size="l" if xsize_bit == 1 else "w",
        ), pos + 2
    if mode_name == "imm":
        nbytes = runtime_m68k_analysis.SIZE_BYTE_COUNT.get(op_size, 2)
        if nbytes <= 2:
            if pos + 2 > len(data):
                raise ValueError("Truncated immediate extension word")
            imm = struct.unpack_from(">H", data, pos)[0]
            if op_size == "b":
                imm &= 0xFF
            return Operand(mode="imm", reg=None, value=imm, size=op_size), pos + 2
        if pos + 4 > len(data):
            raise ValueError("Truncated immediate long extension")
        imm = struct.unpack_from(">I", data, pos)[0]
        return Operand(mode="imm", reg=None, value=imm, size=op_size), pos + 4
    raise ValueError(f"Unhandled EA mode name '{mode_name}'")


def decode_instruction_ops(
    inst: InstructionLike,
    mnemonic: str | None,
    size: str | None,
) -> DecodedOps:
    from .instruction_decode import decode_instruction_operands

    if mnemonic is None or size is None:
        return DecodedOps()
    if (inst.decoded_operands is not None
            and inst.kb_mnemonic is not None
            and inst.kb_mnemonic.upper() == mnemonic.upper()
            and inst.operand_size == size):
        decoded_ops = DecodedOps()
        decoded_obj = inst.decoded_operands
        if decoded_obj is None:
            return decoded_ops
        decoded = decoded_obj.decoded
        decoded_ops.opcode = int(struct.unpack_from(">H", inst.raw, 0)[0]) if len(inst.raw) >= runtime_m68k_analysis.OPWORD_BYTES else 0
        decoded_ops.ea_op = decoded.ea_op
        decoded_ops.dst_op = decoded.dst_op
        decoded_ops.reg_num = decoded.reg_num
        decoded_ops.ea_is_source = decoded.ea_is_source
        decoded_ops.imm_val = decoded.imm_val
        return decoded_ops

    if len(inst.raw) < runtime_m68k_analysis.OPWORD_BYTES:
        return DecodedOps()
    cache_key = (
        inst.raw,
        inst.offset,
        mnemonic,
        size,
        id(runtime_m68k_decode.RAW_FIELDS),
        id(runtime_m68k_decode.FORM_OPERAND_TYPES),
    )
    cached = _DECODED_OPS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    decoded_ops = DecodedOps()
    decoded_ops.opcode = int(struct.unpack_from(">H", inst.raw, 0)[0])
    decoded = decode_instruction_operands(
        inst.raw, mnemonic, runtime_m68k_analysis.OPWORD_BYTES, runtime_m68k_analysis.SIZE_BYTE_COUNT, size, inst.offset
    )
    decoded_ops.ea_op = decoded.ea_op
    decoded_ops.dst_op = decoded.dst_op
    decoded_ops.reg_num = decoded.reg_num
    decoded_ops.ea_is_source = decoded.ea_is_source
    decoded_ops.imm_val = decoded.imm_val
    _DECODED_OPS_CACHE[cache_key] = decoded_ops
    return decoded_ops


def extract_branch_target(inst: InstructionLike, pc: int) -> int | None:
    raw = inst.raw
    mnemonic = instruction_kb(inst)

    ext_branch = BRANCH_EXTENSION_DISPLACEMENTS.get(mnemonic)
    if ext_branch is not None:
        disp_offset, disp_bytes = ext_branch
        if len(raw) < disp_offset + disp_bytes:
            return None
        if disp_bytes == 2:
            disp = int(struct.unpack_from(">h", raw, disp_offset)[0])
        elif disp_bytes == 4:
            disp = int(struct.unpack_from(">i", raw, disp_offset)[0])
        else:
            raise ValueError(f"{mnemonic}: unsupported displacement width {disp_bytes}")
        return pc + runtime_m68k_analysis.OPWORD_BYTES + disp

    branch_info = BRANCH_INLINE_DISPLACEMENTS.get(mnemonic)
    if branch_info is not None:
        opcode = struct.unpack_from(">H", raw, 0)[0]
        _, field, word_signal, long_signal, word_bytes, long_bytes = branch_info
        disp8 = xf(opcode, field)
        if disp8 == word_signal:
            if len(raw) < runtime_m68k_analysis.OPWORD_BYTES + word_bytes:
                return None
            disp = int(struct.unpack_from(">h", raw, runtime_m68k_analysis.OPWORD_BYTES)[0])
            return pc + runtime_m68k_analysis.OPWORD_BYTES + disp
        if disp8 == long_signal:
            if len(raw) < runtime_m68k_analysis.OPWORD_BYTES + long_bytes:
                return None
            disp = int(struct.unpack_from(">i", raw, runtime_m68k_analysis.OPWORD_BYTES)[0])
            return pc + runtime_m68k_analysis.OPWORD_BYTES + disp
        disp_bits = field[2]
        if disp8 >= (1 << (disp_bits - 1)):
            disp8 -= (1 << disp_bits)
        return pc + runtime_m68k_analysis.OPWORD_BYTES + disp8

    flow_type = runtime_m68k_analysis.FLOW_TYPES[mnemonic]
    if flow_type not in (
            runtime_m68k_analysis.FlowType.JUMP,
            runtime_m68k_analysis.FlowType.CALL):
        return None

    opword_fields = runtime_m68k_executor.FIELD_MAPS[0][mnemonic]
    opcode = struct.unpack_from(">H", raw, 0)[0]
    mode = xf(opcode, opword_fields["MODE"])
    reg = xf(opcode, opword_fields["REGISTER"])

    absw_enc = runtime_m68k_analysis.EA_MODE_ENCODING["absw"]
    absl_enc = runtime_m68k_analysis.EA_MODE_ENCODING["absl"]
    pcdisp_enc = runtime_m68k_analysis.EA_MODE_ENCODING["pcdisp"]

    if mode == absw_enc[0] and reg == absw_enc[1]:
        if len(raw) >= runtime_m68k_analysis.OPWORD_BYTES + 2:
            return int(struct.unpack_from(">h", raw, runtime_m68k_analysis.OPWORD_BYTES)[0]) & 0xFFFFFFFF
        return None
    if mode == absl_enc[0] and reg == absl_enc[1]:
        if len(raw) >= runtime_m68k_analysis.OPWORD_BYTES + 4:
            return int(struct.unpack_from(">I", raw, runtime_m68k_analysis.OPWORD_BYTES)[0])
        return None
    if mode == pcdisp_enc[0] and reg == pcdisp_enc[1]:
        if len(raw) >= runtime_m68k_analysis.OPWORD_BYTES + 2:
            return pc + runtime_m68k_analysis.OPWORD_BYTES + int(struct.unpack_from(">h", raw, runtime_m68k_analysis.OPWORD_BYTES)[0])
        return None
    return None
