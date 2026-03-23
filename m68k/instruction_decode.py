"""Shared M68K instruction decode and operand-selection helpers."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Protocol, TypeAlias

from m68k_kb import runtime_m68k_decode
from m68k_kb.runtime_types import FieldSpec, ImmediateRange, OpmodeEntry, RawFieldSpec

from .decode_errors import DecodeError
from .instruction_primitives import decode_ea as _decode_ea, Operand, xf as _xf

OperandTypes: TypeAlias = tuple[str, ...]
BitFieldSpec: TypeAlias = FieldSpec


class InstructionDecodeLike(Protocol):
    @property
    def offset(self) -> int: ...

    @property
    def raw(self) -> bytes: ...

    @property
    def kb_mnemonic(self) -> str | None: ...

    @property
    def operand_size(self) -> str | None: ...


@dataclass(slots=True)
class DecodedOperands:
    operand_types: tuple[str, ...] = ()
    ea_op: Operand | None = None
    dst_op: Operand | None = None
    reg_num: int | None = None
    imm_val: int | None = None
    ea_is_source: bool | None = None
    compare_reg: int | None = None
    update_reg: int | None = None
    reg_mode: str | None = None
    secondary_reg: int | None = None
    control_register: str | None = None
    bitfield: DecodedBitfield | None = None


@dataclass(slots=True)
class DecodedBitfield:
    offset_is_register: bool
    offset_value: int
    width_is_register: bool
    width_value: int
    register: int | None = None


def _raw_field_spec(raw_fields: tuple[RawFieldSpec, ...], name: str) -> BitFieldSpec | None:
    for field_name, bit_hi, bit_lo, width in raw_fields:
        if field_name == name:
            return bit_hi, bit_lo, width
    return None


def _raw_fields_by_prefix(raw_fields: tuple[RawFieldSpec, ...], prefix: str) -> tuple[RawFieldSpec, ...]:
    return tuple(
        (name, bit_hi, bit_lo, width)
        for name, bit_hi, bit_lo, width in raw_fields
        if name.startswith(prefix)
    )


def _unpack_immediate_range(imm_range: ImmediateRange) -> tuple[str | None, int | None, bool, int | None, int | None, int | None]:
    return imm_range


def _runtime_opmode_entry(mnemonic: str, opcode: int,
                          fields: tuple[RawFieldSpec, ...]) -> OpmodeEntry:
    opmode_field = _raw_field_spec(fields, "OPMODE")
    if opmode_field is None:
        raise ValueError(f"{mnemonic} missing OPMODE field")
    opmode = _xf(opcode, opmode_field)
    if mnemonic not in runtime_m68k_decode.OPMODE_TABLES_BY_VALUE:
        raise KeyError(f"runtime KB missing opmode table for {mnemonic}")
    entry = runtime_m68k_decode.OPMODE_TABLES_BY_VALUE[mnemonic].get(opmode)
    if entry is None:
        raise ValueError(f"{mnemonic} missing opmode_table entry for {opmode}")
    return entry


def _runtime_control_register_name(control_value: int) -> str:
    if control_value not in runtime_m68k_decode.CONTROL_REGISTERS:
        raise ValueError(f"Unknown MOVEC control register ${control_value:03x}")
    return runtime_m68k_decode.CONTROL_REGISTERS[control_value]


def xf(opcode: int, field: BitFieldSpec) -> int:
    """Extract a bit field from an opcode. field = (bit_hi, bit_lo, width)."""
    return (opcode >> field[1]) & ((1 << field[2]) - 1)


def _encoding_literal_count(mnemonic: str, enc_idx: int, opcode: int) -> int | None:
    mask, value = runtime_m68k_decode.ENCODING_MASKS[enc_idx][mnemonic]
    if (opcode & mask) != value:
        return None
    return mask.bit_count()


def select_encoding_index(mnemonic: str, opcode: int) -> int:
    encoding_count = runtime_m68k_decode.ENCODING_COUNTS[mnemonic]
    if not encoding_count:
        raise ValueError(f"KB entry {mnemonic} has no encodings")
    form_operand_types = list(runtime_m68k_decode.FORM_OPERAND_TYPES[mnemonic])
    forms = form_operand_types
    if form_operand_types == [("dn", "dn"), ("imm", "dn"), ("ea",)]:
        return 1 if ((opcode >> 6) & 0b11) == 0b11 else 0
    primary_count = min(encoding_count, len(forms)) if forms else encoding_count
    matches = [
        index
        for index in range(primary_count)
        if _encoding_literal_count(mnemonic, index, opcode) is not None
    ]
    if not matches:
        matches = [
            index
            for index in range(primary_count, encoding_count)
            if _encoding_literal_count(mnemonic, index, opcode) is not None
        ]
    if len(matches) > 1:
        literal_counts: dict[int, int] = {
            index: literal_count
            for index in matches
            for literal_count in [_encoding_literal_count(mnemonic, index, opcode)]
            if literal_count is not None
        }
        max_literals = max(literal_counts.values())
        matches = [index for index in matches if literal_counts[index] == max_literals]
    if len(matches) != 1:
        raise ValueError(
            f"KB encoding match count {len(matches)} for opcode ${opcode:04x} "
            f"in {mnemonic}")
    return matches[0]


def select_encoding_fields(mnemonic: str, opcode: int) -> tuple[RawFieldSpec, ...]:
    return runtime_m68k_decode.RAW_FIELDS[select_encoding_index(mnemonic, opcode)][mnemonic]


def select_operand_types(mnemonic: str, opcode: int) -> OperandTypes:
    forms = runtime_m68k_decode.FORM_OPERAND_TYPES[mnemonic]
    if not forms:
        return ()
    form_operand_types = list(forms)
    if len(forms) == 1:
        return form_operand_types[0]

    encoding_index = select_encoding_index(mnemonic, opcode)
    if form_operand_types == [("dn", "dn"), ("imm", "dn"), ("ea",)]:
        if encoding_index == 0:
            return form_operand_types[0] if ((opcode >> 5) & 1) else form_operand_types[1]
        if encoding_index == 1:
            return form_operand_types[2]

    if form_operand_types == [("dn", "disp"), ("disp", "dn")]:
        enc_fields = runtime_m68k_decode.RAW_FIELDS[encoding_index][mnemonic]
        entry = _runtime_opmode_entry(mnemonic, opcode, enc_fields)
        desc = (entry.description or "").lower()
        if "register to memory" in desc:
            return form_operand_types[0]
        if "memory to register" in desc:
            return form_operand_types[1]
        raise ValueError(
            f"Unsupported MOVEP-style opmode description {entry.description!r}")

    if form_operand_types == [("reglist", "ea"), ("ea", "reglist")]:
        enc_fields = runtime_m68k_decode.RAW_FIELDS[encoding_index][mnemonic]
        dr_field = _raw_field_spec(enc_fields, "dr")
        if dr_field is None:
            raise ValueError(f"MOVEM-style form selection missing dr in {mnemonic}")
        dr = _xf(opcode, dr_field)
        return form_operand_types[1] if dr else form_operand_types[0]

    if form_operand_types == [("ctrl_reg", "rn"), ("rn", "ctrl_reg")]:
        enc_fields = runtime_m68k_decode.RAW_FIELDS[encoding_index][mnemonic]
        dr_field = _raw_field_spec(enc_fields, "dr")
        if dr_field is None:
            raise ValueError(f"MOVEC-style form selection missing dr in {mnemonic}")
        dr = _xf(opcode, dr_field)
        return form_operand_types[1] if dr else form_operand_types[0]

    operand_modes = runtime_m68k_decode.OPERAND_MODE_TABLES.get(mnemonic)
    if operand_modes:
        field_name, values = operand_modes
        enc_fields = runtime_m68k_decode.RAW_FIELDS[encoding_index][mnemonic]
        mode_field = _raw_field_spec(enc_fields, field_name)
        if mode_field is None:
            raise ValueError(f"Operand-mode selection missing {field_name!r} in {mnemonic}")
        mode_value = _xf(opcode, mode_field)
        normalized = values.get(mode_value)
        if normalized is None:
            raise ValueError(f"No operand_modes entry for value {mode_value} in {mnemonic}")
        if normalized in form_operand_types:
            return normalized
        matching_forms = [
            operand_types for operand_types in form_operand_types
            if operand_types[:len(normalized)] == normalized
        ]
        if len(matching_forms) == 1:
            return matching_forms[0]
        raise ValueError(
            f"Operand_modes resolved to unsupported form {normalized!r} in {mnemonic}")

    if encoding_index < len(form_operand_types):
        return form_operand_types[encoding_index]

    raise ValueError(
        f"Unable to resolve operand form for opcode ${opcode:04x} "
        f"in {mnemonic}")


def select_operand_types_from_raw(mnemonic: str, inst_raw: bytes) -> OperandTypes:
    if len(inst_raw) < 2:
        raise ValueError("Instruction bytes missing opcode word")
    opcode = struct.unpack_from(">H", inst_raw, 0)[0]
    operand_types = select_operand_types(mnemonic, opcode)
    encoding_index = select_encoding_index(mnemonic, opcode)
    form_operand_types = list(runtime_m68k_decode.FORM_OPERAND_TYPES[mnemonic])
    if mnemonic == "MOVE16" and encoding_index == 2:
        enc_fields = runtime_m68k_decode.RAW_FIELDS[2][mnemonic]
        entry = _runtime_opmode_entry(mnemonic, opcode, enc_fields)

        def _move16_operand_type(operand_text: str) -> str:
            normalized = operand_text.replace(" ", "")
            if normalized == "(xxx).L":
                return "absl"
            if normalized == "(Ay)+":
                return "postinc"
            if normalized == "(Ay)":
                return "ind"
            raise ValueError(f"Unsupported MOVE16 operand text {operand_text!r}")

        source = entry.source
        destination = entry.destination
        assert source is not None
        assert destination is not None
        return (
            _move16_operand_type(source),
            _move16_operand_type(destination),
        )
    if mnemonic == "PTRAPcc":
        enc_fields = runtime_m68k_decode.RAW_FIELDS[0][mnemonic]
        entry = _runtime_opmode_entry(mnemonic, opcode, enc_fields)
        return ("imm",) if entry.size in {"w", "l"} else ()
    if encoding_index != 1 or len(inst_raw) < 4:
        return operand_types

    if (mnemonic in {"MULS", "MULU"}
            and form_operand_types == [("ea", "dn"), ("ea", "dn"), ("ea", "dn_pair")]
            and runtime_m68k_decode.ENCODING_COUNTS[mnemonic] >= 3):
        ext = int(struct.unpack_from(">H", inst_raw, 2)[0])
        fields = runtime_m68k_decode.RAW_FIELDS[2][mnemonic]
        size_field = _raw_field_spec(fields, "SIZE")
        if size_field is None:
            raise ValueError(f"{mnemonic} extension SIZE field missing")
        size_bit = _xf(ext, size_field)
        return ("ea", "dn_pair") if size_bit else ("ea", "dn")

    if (mnemonic in {"DIVS, DIVSL", "DIVU, DIVUL"}
            and form_operand_types == [("ea", "dn"), ("ea", "dn"), ("ea", "dn_pair"), ("ea", "dn_pair")]
            and runtime_m68k_decode.ENCODING_COUNTS[mnemonic] >= 3):
        ext = int(struct.unpack_from(">H", inst_raw, 2)[0])
        fields = runtime_m68k_decode.RAW_FIELDS[2][mnemonic]
        size_field = _raw_field_spec(fields, "SIZE")
        dq_field = _raw_field_spec(fields, "REGISTER Dq")
        dr_field = _raw_field_spec(fields, "REGISTER Dr")
        if size_field is None or dq_field is None or dr_field is None:
            raise ValueError(f"{mnemonic} extension fields missing")
        size_bit = _xf(ext, size_field)
        dq = _xf(ext, dq_field)
        dr = _xf(ext, dr_field)
        return ("ea", "dn_pair") if (size_bit or dq != dr) else ("ea", "dn")

    return operand_types


def _decode_bitfield_extension(inst_raw: bytes, opword_bytes: int, mnemonic: str) -> DecodedBitfield:
    if runtime_m68k_decode.ENCODING_COUNTS[mnemonic] < 2:
        raise ValueError(f"KB bitfield extension encoding missing in {mnemonic}")
    if len(inst_raw) < opword_bytes + 2:
        raise ValueError("Bitfield extension word missing")
    ext = int(struct.unpack_from(">H", inst_raw, opword_bytes)[0])
    fields = runtime_m68k_decode.RAW_FIELDS[1][mnemonic]

    def _field(name: str) -> BitFieldSpec | None:
        return _raw_field_spec(fields, name)

    do_field = _field("Do")
    dw_field = _field("Dw")
    off_field = _field("OFFSET")
    width_field = _field("WIDTH")
    if do_field is None or dw_field is None or off_field is None or width_field is None:
        raise ValueError(f"KB bitfield encoding incomplete in {mnemonic}")
    offset_is_register = bool(_xf(ext, do_field))
    width_is_register = bool(_xf(ext, dw_field))
    offset_value = _xf(ext, off_field)
    width_value = _xf(ext, width_field)
    if not offset_is_register and offset_value >= 16:
        offset_value -= 32
    if not width_is_register and width_value == 0:
        width_value = 32
    reg_field = _field("REGISTER")
    register = _xf(ext, reg_field) if reg_field is not None else None
    return DecodedBitfield(
        offset_is_register=offset_is_register,
        offset_value=offset_value,
        width_is_register=width_is_register,
        width_value=width_value,
        register=register,
    )


def decode_instruction_operands(inst_raw: bytes, mnemonic: str,
                                opword_bytes: int,
                                size_byte_count: dict[str, int],
                                size: str,
                                inst_offset: int) -> DecodedOperands:
    """Decode source and destination operands from raw instruction bytes.

    Extracts structured operand info using KB encoding fields, without
    executing the instruction.  This is the same decode logic used in the
    executor's _apply_instruction, extracted for use by downstream tools.

    Returns:
        operand_types: resolved operand form from KB, or ()
        ea_op: Operand from MODE/REGISTER (bits 5-0), or None
        dst_op: Operand from upper MODE/REGISTER (MOVE only), or None
        reg_num: register number from upper REGISTER field, or None
        imm_val: decoded immediate (from DATA field or extension words), or None
        ea_is_source: bool from OPMODE (None if no OPMODE)
    """
    result = DecodedOperands()

    if len(inst_raw) < opword_bytes:
        return result

    opcode = struct.unpack_from(">H", inst_raw, 0)[0]
    encoding_index = select_encoding_index(mnemonic, opcode)
    enc_fields = runtime_m68k_decode.RAW_FIELDS[encoding_index][mnemonic]
    operand_types = select_operand_types_from_raw(mnemonic, inst_raw)
    result.operand_types = operand_types

    mode_fields = sorted(
        [(name, bit_hi, bit_lo, width) for name, bit_hi, bit_lo, width in enc_fields if name == "MODE"],
        key=lambda field: field[2])
    reg_fields = sorted(
        [(name, bit_hi, bit_lo, width) for name, bit_hi, bit_lo, width in enc_fields if name == "REGISTER"],
        key=lambda field: field[2])
    imm_range = runtime_m68k_decode.IMMEDIATE_RANGES.get(mnemonic)
    if imm_range is not None:
        data_field_name, imm_bits, imm_signed, _imm_min, _imm_max, imm_zero_means = _unpack_immediate_range(imm_range)
    else:
        data_field_name = None
        imm_bits = None
        imm_signed = False
        imm_zero_means = None
    if operand_types and operand_types[0] == "imm" and imm_range is None:
        opword_immediate_fields = {
            "DATA",
            "VECTOR",
            "BIT NUMBER",
            "8-BIT DISPLACEMENT",
            "16-BIT DISPLACEMENT",
            "Count/Register",
        }
        needs_runtime_immediate = any(
            field_name in opword_immediate_fields for field_name, _, _, _ in enc_fields
        ) or (operand_types == ("imm", "dn") and len(reg_fields) >= 2)
        if needs_runtime_immediate:
            raise KeyError(f"runtime KB missing immediate range for {mnemonic}")

    ext_pos = opword_bytes
    if (operand_types and operand_types[0] == "imm"
            and imm_range is not None
            and data_field_name is None):
        bits = imm_bits if imm_bits is not None else 16
        imm_bytes = max(2, (bits + 7) // 8)
        if len(inst_raw) < ext_pos + imm_bytes:
            raise ValueError(
                f"{mnemonic} immediate missing")
        ext_pos += imm_bytes
    if operand_types in {("reglist", "ea"), ("ea", "reglist")}:
        if len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"MOVEM register mask missing for {mnemonic}")
        ext_pos += 2
    if "bf_ea" in operand_types:
        if len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"Bitfield extension word missing for {mnemonic}")
        ext_pos += 2
    if (mnemonic in {"DIVS, DIVSL", "DIVU, DIVUL", "MULS", "MULU"}
            and encoding_index > 0):
        if len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"{mnemonic} extension word missing")
        ext_pos += 2
    if (mnemonic in {"PFLUSHR", "PScc", "PFLUSH PFLUSHA"}
            and "ea" in operand_types):
        if len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"{mnemonic} extension word missing")
        ext_pos += 2

    if "bf_ea" in operand_types:
        result.bitfield = _decode_bitfield_extension(inst_raw, opword_bytes, mnemonic)
    if mnemonic == "MOVES" and operand_types in {("rn", "ea"), ("ea", "rn")}:
        if runtime_m68k_decode.ENCODING_COUNTS[mnemonic] < 2 or len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"{mnemonic} extension word missing")
        ext = struct.unpack_from(">H", inst_raw, opword_bytes)[0]
        ext_pos = opword_bytes + 2
        fields = runtime_m68k_decode.RAW_FIELDS[1][mnemonic]
        ad_field = _raw_field_spec(fields, "A/D")
        reg_field = _raw_field_spec(fields, "REGISTER")
        dr_field = _raw_field_spec(fields, "dr")
        if ad_field is None or reg_field is None or dr_field is None:
            raise ValueError(f"{mnemonic} extension fields missing")
        result.reg_mode = "an" if _xf(ext, ad_field) else "dn"
        result.reg_num = _xf(ext, reg_field)
        dr = _xf(ext, dr_field)
        if mode_fields and reg_fields:
            mf = mode_fields[0]
            rf = reg_fields[0]
            ea_mode = _xf(opcode, (mf[1], mf[2], mf[3]))
            ea_reg = _xf(opcode, (rf[1], rf[2], rf[3]))
            ea_op, _ = _decode_ea(inst_raw, ext_pos, ea_mode, ea_reg, size, inst_offset)
            result.ea_op = ea_op
        result.ea_is_source = bool(dr)
    if mnemonic == "MOVEC" and operand_types in {("ctrl_reg", "rn"), ("rn", "ctrl_reg")}:
        if runtime_m68k_decode.ENCODING_COUNTS[mnemonic] < 2 or len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"{mnemonic} extension word missing")
        ext = struct.unpack_from(">H", inst_raw, opword_bytes)[0]
        fields = runtime_m68k_decode.RAW_FIELDS[1][mnemonic]
        ad_field = _raw_field_spec(fields, "A/D")
        reg_field = _raw_field_spec(fields, "REGISTER")
        ctrl_field = _raw_field_spec(fields, "CONTROL REGISTER")
        if ad_field is None or reg_field is None or ctrl_field is None:
            raise ValueError(f"{mnemonic} extension fields missing")
        result.reg_mode = "an" if _xf(ext, ad_field) else "dn"
        result.reg_num = _xf(ext, reg_field)
        ctrl = _xf(ext, ctrl_field)
        result.control_register = _runtime_control_register_name(ctrl)
    if mnemonic == "PTRAPcc" and operand_types == ("imm",):
        if len(inst_raw) < opword_bytes + 2:
            raise ValueError("PTRAPcc condition word missing")
        ext_pos = opword_bytes + 2
        if size == "w":
            if len(inst_raw) < ext_pos + 2:
                raise ValueError("PTRAPcc word immediate missing")
            result.imm_val = struct.unpack_from(">H", inst_raw, ext_pos)[0]
        elif size == "l":
            if len(inst_raw) < ext_pos + 4:
                raise ValueError("PTRAPcc long immediate missing")
            result.imm_val = struct.unpack_from(">I", inst_raw, ext_pos)[0]
        else:
            raise ValueError(f"Unsupported PTRAPcc operand size {size!r}")
    if mnemonic == "LINK" and operand_types == ("an", "imm"):
        reg_field = _raw_field_spec(enc_fields, "REGISTER")
        if reg_field is None:
            raise ValueError("LINK register field missing")
        result.reg_num = _xf(opcode, reg_field)
        if encoding_index == 2:
            if len(inst_raw) < opword_bytes + 4:
                raise ValueError("LINK.L displacement words missing")
            result.imm_val = struct.unpack_from(">i", inst_raw, opword_bytes)[0] & 0xFFFFFFFF
        else:
            if len(inst_raw) < opword_bytes + 2:
                raise ValueError("LINK.W displacement word missing")
            result.imm_val = struct.unpack_from(">h", inst_raw, opword_bytes)[0] & 0xFFFFFFFF
    if mnemonic == "MOVE16" and operand_types == ("postinc", "postinc"):
        if runtime_m68k_decode.ENCODING_COUNTS[mnemonic] < 2 or len(inst_raw) < opword_bytes + 2:
            raise ValueError("MOVE16 extension word missing")
        op_fields = runtime_m68k_decode.RAW_FIELDS[0][mnemonic]
        ext_fields = runtime_m68k_decode.RAW_FIELDS[1][mnemonic]
        ax_field = _raw_field_spec(op_fields, "REGISTER Ax")
        ay_field = _raw_field_spec(ext_fields, "REGISTER Ay")
        if ax_field is None or ay_field is None:
            raise ValueError("MOVE16 register fields missing")
        ext = struct.unpack_from(">H", inst_raw, opword_bytes)[0]
        ax = _xf(opcode, ax_field)
        ay = _xf(ext, ay_field)
        result.ea_op = Operand(mode="postinc", reg=ax, value=None)
        result.dst_op = Operand(mode="postinc", reg=ay, value=None)
    if mnemonic == "MOVE16" and operand_types in {
            ("absl", "postinc"), ("postinc", "absl"), ("absl", "ind"), ("ind", "absl")}:
        if runtime_m68k_decode.ENCODING_COUNTS[mnemonic] < 3 or len(inst_raw) < opword_bytes + 4:
            raise ValueError("MOVE16 absolute address words missing")
        op_fields = runtime_m68k_decode.RAW_FIELDS[2][mnemonic]
        opmode_field = _raw_field_spec(op_fields, "OPMODE")
        reg_field = _raw_field_spec(op_fields, "REGISTER Ay")
        if opmode_field is None or reg_field is None:
            raise ValueError("MOVE16 absolute form fields missing")
        opmode = _xf(opcode, opmode_field)
        opmode_table = runtime_m68k_decode.OPMODE_TABLES_BY_VALUE["MOVE16"]
        entry = opmode_table.get(opmode)
        if entry is None:
            raise ValueError(f"MOVE16 missing opmode_table entry for {opmode}")
        an = _xf(opcode, reg_field)
        addr = struct.unpack_from(">I", inst_raw, opword_bytes)[0]

        def _move16_operand(text: str) -> Operand:
            normalized = text.replace(" ", "")
            if normalized == "(xxx).L":
                return Operand(mode="absl", reg=None, value=addr)
            if normalized == "(Ay)+":
                return Operand(mode="postinc", reg=an, value=None)
            if normalized == "(Ay)":
                return Operand(mode="ind", reg=an, value=None)
            raise ValueError(f"Unsupported MOVE16 operand text {text!r}")

        source = entry.source
        destination = entry.destination
        assert source is not None
        assert destination is not None
        result.ea_op = _move16_operand(source)
        result.dst_op = _move16_operand(destination)
    if mnemonic == "CMPM" and operand_types == ("postinc", "postinc"):
        ax_field = _raw_field_spec(enc_fields, "REGISTER Ax")
        ay_field = _raw_field_spec(enc_fields, "REGISTER Ay")
        if ax_field is None or ay_field is None:
            raise ValueError("CMPM register fields missing")
        ax = _xf(opcode, ax_field)
        ay = _xf(opcode, ay_field)
        result.ea_op = Operand(mode="postinc", reg=ay, value=None)
        result.dst_op = Operand(mode="postinc", reg=ax, value=None)
    if mnemonic in {"PACK", "UNPK"} and operand_types in {
            ("dn", "dn", "imm"), ("predec", "predec", "imm")}:
        if len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"{mnemonic} adjustment word missing")
        named_reg_fields = sorted(
            _raw_fields_by_prefix(enc_fields, "REGISTER "),
            key=lambda field: field[2])
        if len(named_reg_fields) != 2:
            raise ValueError(f"{mnemonic} register fields missing")
        src_reg = _xf(opcode, named_reg_fields[0][1:])
        dst_reg = _xf(opcode, named_reg_fields[1][1:])
        imm = struct.unpack_from(">H", inst_raw, opword_bytes)[0]
        result.imm_val = imm
        if operand_types == ("dn", "dn", "imm"):
            result.ea_op = Operand(mode="dn", reg=src_reg, value=None)
            result.reg_num = src_reg
            result.secondary_reg = dst_reg
        else:
            result.ea_op = Operand(mode="predec", reg=src_reg, value=None)
            result.dst_op = Operand(mode="predec", reg=dst_reg, value=None)
    if mnemonic in {"CHK2", "CMP2"} and operand_types == ("ea", "rn"):
        if runtime_m68k_decode.ENCODING_COUNTS[mnemonic] < 2 or len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"{mnemonic} extension word missing")
        ext = struct.unpack_from(">H", inst_raw, opword_bytes)[0]
        ext_pos = opword_bytes + 2
        fields = runtime_m68k_decode.RAW_FIELDS[1][mnemonic]
        da_field = _raw_field_spec(fields, "D/A")
        reg_field = _raw_field_spec(fields, "REGISTER")
        if da_field is None or reg_field is None:
            raise ValueError(f"{mnemonic} extension fields missing")
        result.reg_mode = "an" if _xf(ext, da_field) else "dn"
        result.reg_num = _xf(ext, reg_field)
    if operand_types == ("dn", "dn", "ea"):
        if runtime_m68k_decode.ENCODING_COUNTS[mnemonic] < 2 or len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"CAS extension word missing for {mnemonic}")
        ext = struct.unpack_from(">H", inst_raw, opword_bytes)[0]
        ext_pos = opword_bytes + 2
        fields = runtime_m68k_decode.RAW_FIELDS[1][mnemonic]
        du_field = _raw_field_spec(fields, "Du")
        dc_field = _raw_field_spec(fields, "Dc")
        if du_field is None or dc_field is None:
            raise ValueError(f"CAS extension fields missing for {mnemonic}")
        result.update_reg = _xf(ext, du_field)
        result.compare_reg = _xf(ext, dc_field)
    if operand_types == ("ea", "rn"):
        if runtime_m68k_decode.ENCODING_COUNTS[mnemonic] < 2 or len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"{mnemonic} extension word missing")
        ext = struct.unpack_from(">H", inst_raw, opword_bytes)[0]
        fields = runtime_m68k_decode.RAW_FIELDS[1][mnemonic]
        da_field = _raw_field_spec(fields, "D/A")
        reg_field = _raw_field_spec(fields, "REGISTER")
        if da_field is None or reg_field is None:
            raise ValueError(f"{mnemonic} extension fields missing")
        result.reg_mode = "an" if _xf(ext, da_field) else "dn"
        result.reg_num = _xf(ext, reg_field)
    if operand_types == ("rn",):
        da_field = _raw_field_spec(enc_fields, "D/A")
        reg_field = _raw_field_spec(enc_fields, "REGISTER")
        if da_field is None or reg_field is None:
            raise ValueError(f"{mnemonic} register fields missing")
        result.reg_mode = "an" if _xf(opcode, da_field) else "dn"
        result.reg_num = _xf(opcode, reg_field)
    if operand_types == ("dn", "label"):
        reg_field = _raw_field_spec(enc_fields, "COUNT REGISTER") or _raw_field_spec(enc_fields, "REGISTER")
        if reg_field is None:
            raise ValueError(f"{mnemonic} count register field missing")
        result.reg_num = _xf(opcode, reg_field)
    if operand_types in {("usp", "an"), ("an", "usp")}:
        dr_field = _raw_field_spec(enc_fields, "dr")
        reg_field = _raw_field_spec(enc_fields, "REGISTER")
        if dr_field is None or reg_field is None:
            raise ValueError(f"{mnemonic} direction/register fields missing")
        result.reg_mode = "an"
        result.reg_num = _xf(opcode, reg_field)
        result.ea_is_source = bool(_xf(opcode, dr_field))
    if mnemonic in {"ADDX", "SUBX", "ABCD", "SBCD"}:
        named_reg_fields = sorted(
            _raw_fields_by_prefix(enc_fields, "REGISTER "),
            key=lambda field: field[2])
        if len(named_reg_fields) != 2:
            raise ValueError(f"{mnemonic} register fields missing")
        src_reg = _xf(opcode, named_reg_fields[0][1:])
        dst_reg = _xf(opcode, named_reg_fields[1][1:])
        if operand_types == ("dn", "dn"):
            result.ea_op = Operand(mode="dn", reg=src_reg, value=None)
            result.reg_num = src_reg
        elif operand_types == ("predec", "predec"):
            result.ea_op = Operand(mode="predec", reg=src_reg, value=None)
            result.dst_op = Operand(mode="predec", reg=dst_reg, value=None)
    if (operand_types in {("ea", "dn"), ("ea", "dn_pair")}
            and encoding_index > 0
            and len(inst_raw) >= opword_bytes + 2):
        if runtime_m68k_decode.ENCODING_COUNTS[mnemonic] >= 3:
            ext = struct.unpack_from(">H", inst_raw, opword_bytes)[0]
            fields = runtime_m68k_decode.RAW_FIELDS[2][mnemonic]
            ext_reg_fields = _raw_fields_by_prefix(fields, "REGISTER ")
            if ext_reg_fields:
                reg_values = {
                    name: _xf(ext, (bit_hi, bit_lo, width))
                    for name, bit_hi, bit_lo, width in ext_reg_fields
                }
                if "REGISTER Dr" in reg_values and "REGISTER Dq" in reg_values:
                    result.reg_num = reg_values["REGISTER Dr"]
                    result.secondary_reg = reg_values["REGISTER Dq"]
                elif "REGISTER Dl" in reg_values and "REGISTER Dh" in reg_values:
                    result.reg_num = reg_values["REGISTER Dl"]
                    result.secondary_reg = reg_values["REGISTER Dh"]
                elif "REGISTER Dh" in reg_values and "REGISTER DI" in reg_values:
                    result.reg_num = reg_values["REGISTER DI"]
                    result.secondary_reg = reg_values["REGISTER Dh"]

    # Decode EA from lowest MODE + lowest REGISTER
    if mode_fields and reg_fields:
        mf = mode_fields[0]
        rf = reg_fields[0]
        ea_mode = _xf(opcode, (mf[1], mf[2], mf[3]))
        ea_reg = _xf(opcode, (rf[1], rf[2], rf[3]))
        try:
            ea_op, ext_pos = _decode_ea(
                inst_raw, ext_pos,
                ea_mode, ea_reg, size, inst_offset)
            result.ea_op = ea_op
        except (ValueError, DecodeError):
            ext_pos = opword_bytes

        # Destination EA from upper MODE + upper REGISTER (MOVE)
        if len(mode_fields) >= 2 and len(reg_fields) >= 2:
            dmf = mode_fields[1]
            drf = reg_fields[1]
            d_mode = _xf(opcode, (dmf[1], dmf[2], dmf[3]))
            d_reg = _xf(opcode, (drf[1], drf[2], drf[3]))
            try:
                dst_op, _ = _decode_ea(
                    inst_raw, ext_pos,
                    d_mode, d_reg, size, inst_offset)
                result.dst_op = dst_op
            except (ValueError, DecodeError):
                pass

    if operand_types in {("dn", "disp"), ("disp", "dn")}:
        data_reg_field = _raw_field_spec(enc_fields, "DATA REGISTER")
        addr_reg_field = _raw_field_spec(enc_fields, "ADDRESS REGISTER")
        if data_reg_field is None or addr_reg_field is None:
            raise ValueError(f"MOVEP decode fields missing for {mnemonic}")
        result.reg_num = _xf(opcode, data_reg_field)
        if len(inst_raw) < opword_bytes + 2:
            raise ValueError(f"MOVEP displacement missing for opcode ${opcode:04x}")
        disp = struct.unpack_from(">H", inst_raw, opword_bytes)[0]
        if disp >= 0x8000:
            disp -= 0x10000
        addr_reg = _xf(opcode, addr_reg_field)
        result.ea_op = Operand(mode="disp", reg=addr_reg, value=disp,
                               index_reg=None, index_is_addr=False,
                               index_size="w", size=None)
    if operand_types == ("bf_ea", "dn"):
        bitfield = result.bitfield
        if bitfield is None or bitfield.register is None:
            raise ValueError(f"Bitfield destination register missing for {mnemonic}")
        result.reg_num = bitfield.register
    if operand_types == ("dn", "bf_ea"):
        bitfield = result.bitfield
        if bitfield is None or bitfield.register is None:
            raise ValueError(f"Bitfield source register missing for {mnemonic}")
        result.reg_num = bitfield.register

    # Register number from REGISTER field.
    # With 2+ REGISTER fields: upper field is the "other" register (bits 11-9).
    # With exactly 1 REGISTER and no MODE: the sole REGISTER is the
    # destination (e.g. MOVEQ where DATA has the immediate).
    if result.reg_num is None and operand_types == ("imm", "dn") and len(reg_fields) >= 2:
        rf = reg_fields[0]
        result.reg_num = _xf(opcode, (rf[1], rf[2], rf[3]))
    elif result.reg_num is None and len(reg_fields) >= 2:
        rf = reg_fields[-1]
        result.reg_num = _xf(opcode, (rf[1], rf[2], rf[3]))
    elif result.reg_num is None and len(reg_fields) == 1 and not mode_fields:
        rf = reg_fields[0]
        result.reg_num = _xf(opcode, (rf[1], rf[2], rf[3]))

    # OPMODE direction from KB opmode_table
    opmode_tables = runtime_m68k_decode.OPMODE_TABLES_BY_VALUE
    if mnemonic in opmode_tables:
        opmode_f = _raw_field_spec(enc_fields, "OPMODE")
        if opmode_f:
            opmode_val = _xf(opcode, opmode_f)
            entry = opmode_tables[mnemonic].get(opmode_val)
            if entry is None:
                raise ValueError(
                    f"{mnemonic} missing opmode_table entry for {opmode_val}")
            result.ea_is_source = entry.ea_is_source

    # Decode immediate value from opcode (KB-driven).
    # Pattern 1: DATA field in opcode (ADDQ/SUBQ/MOVEQ)
    # Pattern 2: extension word immediate (ADDI/SUBI/etc.)
    if data_field_name and imm_range is not None:
        df = _raw_field_spec(enc_fields, data_field_name)
        if df:
            raw_val = _xf(opcode, df)
            if imm_zero_means is not None and raw_val == 0:
                raw_val = imm_zero_means
            if imm_signed:
                if imm_bits is None:
                    raise KeyError(f"{mnemonic}: immediate range missing bit width")
                bits = imm_bits
                if raw_val >= (1 << (bits - 1)):
                    raw_val -= (1 << bits)
                raw_val &= 0xFFFFFFFF
            result.imm_val = raw_val
        elif operand_types == ("imm", "dn") and len(reg_fields) >= 2:
            rf = reg_fields[-1]
            raw_val = _xf(opcode, (rf[1], rf[2], rf[3]))
            if imm_zero_means is not None and raw_val == 0:
                raw_val = imm_zero_means
            if imm_signed:
                if imm_bits is None:
                    raise KeyError(f"{mnemonic}: immediate range missing bit width")
                bits = imm_bits
                if raw_val >= (1 << (bits - 1)):
                    raw_val -= (1 << bits)
                raw_val &= 0xFFFFFFFF
            result.imm_val = raw_val
        elif result.imm_val is None and "imm" in operand_types and len(inst_raw) >= opword_bytes + 2:
            bits = imm_bits if imm_bits is not None else 16
            imm_bytes = max(2, (bits + 7) // 8)
            pos = opword_bytes
            if imm_bytes <= 2:
                imm_val = struct.unpack_from(">H", inst_raw, pos)[0]
            else:
                imm_val = struct.unpack_from(">I", inst_raw, pos)[0]
            if imm_bits is not None:
                bits = imm_bits
                imm_val &= (1 << bits) - 1
            if imm_signed and imm_bits is not None:
                if imm_val >= (1 << (bits - 1)):
                    imm_val -= (1 << bits)
                imm_val &= 0xFFFFFFFF
            result.imm_val = imm_val
            if mode_fields and reg_fields:
                mf = mode_fields[0]
                rf = reg_fields[0]
                ea_m = _xf(opcode, (mf[1], mf[2], mf[3]))
                ea_r = _xf(opcode, (rf[1], rf[2], rf[3]))
                try:
                    ea_op, _ = _decode_ea(
                        inst_raw, pos + max(imm_bytes, 2),
                        ea_m, ea_r, size, inst_offset)
                    result.ea_op = ea_op
                except (ValueError, DecodeError):
                    pass

    elif (result.imm_val is None and mnemonic not in opmode_tables and not data_field_name
          and len(mode_fields) == 1 and not imm_range
          and "imm" in operand_types):
        # Pattern 2: extension word immediate (ADDI etc.)
        imm_bytes = size_byte_count.get(size, size_byte_count["w"])
        pos = opword_bytes
        if pos + imm_bytes <= len(inst_raw):
            if imm_bytes <= 2:
                imm_val = struct.unpack_from(">H", inst_raw, pos)[0]
                if size == "b":
                    imm_val &= 0xFF
            else:
                imm_val = struct.unpack_from(">I", inst_raw, pos)[0]
            result.imm_val = imm_val
            # Re-decode EA after the immediate
            if mode_fields and reg_fields:
                mf = mode_fields[0]
                rf = reg_fields[0]
                ea_m = _xf(opcode, (mf[1], mf[2], mf[3]))
                ea_r = _xf(opcode, (rf[1], rf[2], rf[3]))
                try:
                    ea_op, _ = _decode_ea(
                        inst_raw, pos + max(imm_bytes, 2),
                        ea_m, ea_r, size, inst_offset)
                    result.ea_op = ea_op
                except (ValueError, DecodeError):
                    pass

    return result


def decode_inst_operands(inst: InstructionDecodeLike, mnemonic: str | None = None) -> DecodedOperands:
    """Decode operands directly from an Instruction."""
    if mnemonic is None:
        if not inst.kb_mnemonic:
            raise ValueError(
                f"Instruction at ${inst.offset:06x} is missing kb_mnemonic")
        mnemonic = inst.kb_mnemonic
    if not inst.operand_size:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing operand_size")
    return decode_instruction_operands(
        inst.raw,
        mnemonic,
        runtime_m68k_decode.OPWORD_BYTES,
        runtime_m68k_decode.SIZE_BYTE_COUNT,
        inst.operand_size,
        inst.offset,
    )


def _decoded_register_mode(decoded: DecodedOperands, operand_types: tuple[str, ...]) -> str | None:
    for operand_type in reversed(operand_types):
        if operand_type == "an":
            return "an"
        if operand_type == "dn":
            return "dn"
        if operand_type == "rn":
            reg_mode = decoded.reg_mode
            if reg_mode in {"dn", "an"}:
                return reg_mode
            raise ValueError("operand_types include 'rn' but decoded reg_mode is missing")
    return None


def decode_destination(inst_raw: bytes, mnemonic: str,
                       opword_bytes: int,
                       size_byte_count: dict[str, int],
                       size: str,
                       inst_offset: int) -> tuple[str, int] | None:
    """Determine the destination register of an instruction.

    Returns (mode, reg_num) where mode is "dn" or "an", or None if the
    destination cannot be determined from opcode bits.

    Handles:
    - MOVE/MOVEA: dst_op from upper MODE/REGISTER fields
    - OPMODE instructions: ea_is_source=False means EA is dst, else reg_num
    - Single-EA + reg_num: destination is the upper REGISTER (e.g. LEA)
    """
    decoded = decode_instruction_operands(
        inst_raw, mnemonic, opword_bytes, size_byte_count, size, inst_offset)
    operand_types = decoded.operand_types

    # MOVE/MOVEA: has dst_op with explicit mode
    dst_op = decoded.dst_op
    if dst_op is not None:
        if dst_op.mode in ("dn", "an"):
            if dst_op.reg is None:
                raise ValueError("Destination register operand missing register number")
            return (dst_op.mode, dst_op.reg)
        return None  # destination is memory, not a register

    # OPMODE instructions (ADD, SUB, AND, OR, etc.)
    ea_is_source = decoded.ea_is_source
    ea_op = decoded.ea_op
    reg_num = decoded.reg_num
    if ea_is_source is not None:
        if ea_is_source:
            # EA is source -> destination is the upper register from KB form
            if reg_num is not None:
                reg_mode = _decoded_register_mode(decoded, operand_types)
                if reg_mode is not None:
                    return (reg_mode, reg_num)
        else:
            # EA is destination
            if ea_op and ea_op.mode in ("dn", "an"):
                if ea_op.reg is None:
                    raise ValueError("EA destination register operand missing register number")
                return (ea_op.mode, ea_op.reg)
        return None

    # Single-EA with upper register: LEA, MOVEA-like, etc.
    # Check if instruction writes to An via source_sign_extend (MOVEA pattern)
    if mnemonic in runtime_m68k_decode.SOURCE_SIGN_EXTEND and reg_num is not None:
        return ("an", reg_num)

    # Explicit register operand form from the KB (LEA, MOVEA, ADDA, etc.)
    if reg_num is not None and operand_types:
        reg_mode = _decoded_register_mode(decoded, operand_types)
        if reg_mode is not None:
            return (reg_mode, reg_num)

    # Default: reg_num is destination Dn (MOVEQ, ADDQ to Dn, etc.)
    if reg_num is not None:
        # If ea_op is a register and no OPMODE, check operation_type
        op_type = runtime_m68k_decode.OPERATION_TYPES.get(mnemonic)
        if op_type == runtime_m68k_decode.OperationType.MOVE:
            return ("dn", reg_num)
        # For ALU ops without OPMODE (ADDQ/SUBQ), EA is the destination
        if ea_op and ea_op.mode in ("dn", "an"):
            if ea_op.reg is None:
                raise ValueError("EA destination register operand missing register number")
            return (ea_op.mode, ea_op.reg)

    return None


def decode_inst_destination(inst: InstructionDecodeLike, mnemonic: str | None = None) -> tuple[str, int] | None:
    """Determine destination register directly from an Instruction."""
    if mnemonic is None:
        if not inst.kb_mnemonic:
            raise ValueError(
                f"Instruction at ${inst.offset:06x} is missing kb_mnemonic")
        mnemonic = inst.kb_mnemonic
    if not inst.operand_size:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing operand_size")
    return decode_destination(
        inst.raw,
        mnemonic,
        runtime_m68k_decode.OPWORD_BYTES,
        runtime_m68k_decode.SIZE_BYTE_COUNT,
        inst.operand_size,
        inst.offset,
    )


