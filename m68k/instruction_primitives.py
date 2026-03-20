"""Shared M68K decode and branch-target primitives."""

import struct
from dataclasses import dataclass

from knowledge import runtime_m68k_analysis
from knowledge import runtime_m68k_executor

from .ea_extension import parse_full_extension
from .instruction_kb import instruction_kb


_EA_REVERSE = dict(runtime_m68k_analysis.EA_REVERSE)
_BRIEF_EXT_FIELDS = runtime_m68k_analysis.EA_BRIEF_FIELDS
_SIZE_BYTE_COUNT = runtime_m68k_analysis.SIZE_BYTE_COUNT
_OPWORD_BYTES = runtime_m68k_analysis.OPWORD_BYTES


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


def xf(word: int, field_spec: tuple[int, int, int]) -> int:
    _, bit_lo, width = field_spec
    return (word >> bit_lo) & ((1 << width) - 1)


def decode_ea(data: bytes, pos: int, mode: int, reg: int,
              op_size: str, pc_offset: int) -> tuple[Operand, int]:
    mode_name = _EA_REVERSE.get((mode, reg))
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
                value=info["base_displacement"],
                index_reg=info["index_reg_num"],
                index_is_addr=info["index_is_addr"],
                index_size=info["index_size"] or "w",
                index_scale=info["index_scale"] or 1,
                full_extension=True,
                memory_indirect=bool(info["memory_indirect"]),
                postindexed=bool(info["postindexed"]),
                base_suppressed=bool(info["base_suppressed"]),
                index_suppressed=bool(info["index_suppressed"]),
                base_displacement=info["base_displacement"],
                outer_displacement=info["outer_displacement"],
            ), pos
        xreg = xf(ext, _BRIEF_EXT_FIELDS["REGISTER"])
        xtype_bit = xf(ext, _BRIEF_EXT_FIELDS["D/A"])
        xsize_bit = xf(ext, _BRIEF_EXT_FIELDS["W/L"])
        disp_raw = xf(ext, _BRIEF_EXT_FIELDS["DISPLACEMENT"])
        disp_width = _BRIEF_EXT_FIELDS["DISPLACEMENT"][2]
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
        return Operand(mode="pcdisp", reg=None, value=pc_offset + _OPWORD_BYTES + disp), pos + 2
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
                value=info["base_target"],
                index_reg=info["index_reg_num"],
                index_is_addr=info["index_is_addr"],
                index_size=info["index_size"] or "w",
                index_scale=info["index_scale"] or 1,
                full_extension=True,
                memory_indirect=bool(info["memory_indirect"]),
                postindexed=bool(info["postindexed"]),
                base_suppressed=bool(info["base_suppressed"]),
                index_suppressed=bool(info["index_suppressed"]),
                base_displacement=info["base_displacement"],
                outer_displacement=info["outer_displacement"],
            ), pos
        xreg = xf(ext, _BRIEF_EXT_FIELDS["REGISTER"])
        xtype_bit = xf(ext, _BRIEF_EXT_FIELDS["D/A"])
        xsize_bit = xf(ext, _BRIEF_EXT_FIELDS["W/L"])
        disp_raw = xf(ext, _BRIEF_EXT_FIELDS["DISPLACEMENT"])
        disp_width = _BRIEF_EXT_FIELDS["DISPLACEMENT"][2]
        if disp_raw & (1 << (disp_width - 1)):
            disp_raw -= (1 << disp_width)
        return Operand(
            mode="pcindex",
            reg=None,
            value=pc_offset + _OPWORD_BYTES + disp_raw,
            index_reg=xreg,
            index_is_addr=(xtype_bit == 1),
            index_size="l" if xsize_bit == 1 else "w",
        ), pos + 2
    if mode_name == "imm":
        nbytes = _SIZE_BYTE_COUNT.get(op_size, 2)
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


def decode_instruction_ops(inst, mnemonic: str, size: str) -> DecodedOps:
    from .instruction_decode import decode_instruction_operands

    decoded_ops = DecodedOps()
    if len(inst.raw) < _OPWORD_BYTES:
        return decoded_ops
    decoded_ops.opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    decoded = decode_instruction_operands(
        inst.raw, mnemonic, _OPWORD_BYTES, _SIZE_BYTE_COUNT, size, inst.offset
    )
    decoded_ops.ea_op = decoded["ea_op"]
    decoded_ops.dst_op = decoded["dst_op"]
    decoded_ops.reg_num = decoded["reg_num"]
    decoded_ops.ea_is_source = decoded["ea_is_source"]
    decoded_ops.imm_val = decoded["imm_val"]
    return decoded_ops


def extract_branch_target(inst, pc: int) -> int | None:
    raw = inst.raw
    mnemonic = instruction_kb(inst)

    ext_branch = runtime_m68k_executor.BRANCH_EXTENSION_DISPLACEMENTS.get(mnemonic)
    if ext_branch is not None:
        disp_offset, disp_bytes = ext_branch
        if len(raw) < disp_offset + disp_bytes:
            return None
        if disp_bytes == 2:
            disp = struct.unpack_from(">h", raw, disp_offset)[0]
        elif disp_bytes == 4:
            disp = struct.unpack_from(">i", raw, disp_offset)[0]
        else:
            raise ValueError(f"{mnemonic}: unsupported displacement width {disp_bytes}")
        return pc + _OPWORD_BYTES + disp

    branch_info = runtime_m68k_executor.BRANCH_INLINE_DISPLACEMENTS.get(mnemonic)
    if branch_info is not None:
        opcode = struct.unpack_from(">H", raw, 0)[0]
        _, field, word_signal, long_signal, word_bytes, long_bytes = branch_info
        disp8 = xf(opcode, field)
        if disp8 == word_signal:
            if len(raw) < _OPWORD_BYTES + word_bytes:
                return None
            disp = struct.unpack_from(">h", raw, _OPWORD_BYTES)[0]
            return pc + _OPWORD_BYTES + disp
        if disp8 == long_signal:
            if len(raw) < _OPWORD_BYTES + long_bytes:
                return None
            disp = struct.unpack_from(">i", raw, _OPWORD_BYTES)[0]
            return pc + _OPWORD_BYTES + disp
        disp_bits = field[2]
        if disp8 >= (1 << (disp_bits - 1)):
            disp8 -= (1 << disp_bits)
        return pc + _OPWORD_BYTES + disp8

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
        if len(raw) >= _OPWORD_BYTES + 2:
            return struct.unpack_from(">h", raw, _OPWORD_BYTES)[0] & 0xFFFFFFFF
        return None
    if mode == absl_enc[0] and reg == absl_enc[1]:
        if len(raw) >= _OPWORD_BYTES + 4:
            return struct.unpack_from(">I", raw, _OPWORD_BYTES)[0]
        return None
    if mode == pcdisp_enc[0] and reg == pcdisp_enc[1]:
        if len(raw) >= _OPWORD_BYTES + 2:
            return pc + _OPWORD_BYTES + struct.unpack_from(">h", raw, _OPWORD_BYTES)[0]
        return None
    return None
