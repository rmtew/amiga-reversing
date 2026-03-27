from __future__ import annotations

"""Build semantic operands from decoded instruction operands."""
from dataclasses import dataclass, replace

from disasm.decode import DecodedInstructionForEmit, decode_inst_for_emit
from disasm.hardware_symbols import (
    hardware_absolute_addr,
    hardware_register_by_addr,
    hardware_register_by_base_offset,
    render_hardware_absolute,
    render_hardware_relative,
)
from disasm.types import (
    AppStructFieldOperandMetadata,
    BitfieldOperandMetadata,
    FullIndexedOperandMetadata,
    HunkDisassemblySession,
    IndexedOperandMetadata,
    RegisterListOperandMetadata,
    RegisterPairOperandMetadata,
    SemanticOperand,
    SemanticOperandMetadata,
    StructFieldOperandMetadata,
    SymbolOperandMetadata,
)
from m68k.instruction_decode import (
    DecodedBitfield,
    decode_inst_destination,
    select_encoding_fields,
    select_operand_types_from_raw,
)
from m68k.instruction_primitives import Operand, extract_branch_target
from m68k.m68k_disasm import (
    DecodedBaseDisplacementNodeMetadata,
    DecodedBaseRegisterNodeMetadata,
    DecodedBitfieldNodeMetadata,
    DecodedFullExtensionNodeMetadata,
    DecodedIndexedNodeMetadata,
    DecodedOperandNode,
    DecodedRegisterListNodeMetadata,
    DecodedRegisterPairNodeMetadata,
    Instruction,
)
from m68k.os_structs import resolve_struct_field
from m68k_kb import runtime_m68k_analysis, runtime_m68k_decode, runtime_m68k_disasm

_FLOW_BRANCH = runtime_m68k_analysis.FlowType.BRANCH
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
@dataclass(frozen=True, slots=True)
class RegisterSpec:
    mode: str
    reg: int


@dataclass(frozen=True, slots=True)
class SpecialRegisterSpec:
    register: str


@dataclass(frozen=True, slots=True)
class RegListSpec:
    pass


@dataclass(frozen=True, slots=True)
class RegisterPairSpec:
    hi: int
    lo: int


@dataclass(frozen=True, slots=True)
class ImmediateSpec:
    value: int


@dataclass(frozen=True, slots=True)
class LabelSpec:
    pass


@dataclass(frozen=True, slots=True)
class BitfieldOperandSpec:
    operand: Operand
    bitfield: DecodedBitfield


@dataclass(frozen=True, slots=True)
class DecodedOperandSpec:
    operand: Operand


type OperandSpec = (
    RegisterSpec
    | SpecialRegisterSpec
    | RegListSpec
    | RegisterPairSpec
    | ImmediateSpec
    | LabelSpec
    | BitfieldOperandSpec
    | DecodedOperandSpec
)


def _instruction_ref(inst: Instruction) -> str:
    return f"instruction at ${inst.offset:06x}"


def _operand_types_for_inst(inst: Instruction, meta: DecodedInstructionForEmit) -> tuple[str, ...]:
    opcode = int.from_bytes(inst.raw[:2], "big")
    form_operand_types: list[tuple[str, ...]] = list(runtime_m68k_disasm.FORM_OPERAND_TYPES[meta.mnemonic])
    if form_operand_types == [("usp", "an"), ("an", "usp")]:
        return form_operand_types[0] if ((opcode >> 3) & 1) else form_operand_types[1]
    if form_operand_types == [("rn", "ea"), ("ea", "rn")]:
        if len(inst.raw) < 4:
            raise ValueError(f"MOVES extension word missing for {_instruction_ref(inst)}")
        ext = int.from_bytes(inst.raw[2:4], "big")
        return form_operand_types[0] if ((ext >> 11) & 1) != 0 else form_operand_types[1]
    operand_types = select_operand_types_from_raw(meta.mnemonic, inst.raw)
    return tuple(operand_types)


def _selected_form_register(inst: Instruction, meta: DecodedInstructionForEmit,
                            register_index: int) -> tuple[str, int] | None:
    opcode = int.from_bytes(inst.raw[:2], "big")
    fields = select_encoding_fields(meta.mnemonic, opcode)
    plain_register_fields = [
        field for field in fields
        if field[0] == "REGISTER"
    ]
    if plain_register_fields:
        register_fields = plain_register_fields
    else:
        register_fields = [
            field for field in fields
            if field[0].startswith("REGISTER ")
        ]
        register_fields.sort(key=lambda field: field[2])
    if len(register_fields) <= register_index:
        return None
    field = register_fields[register_index]
    width = field[3]
    mask = (1 << width) - 1
    reg = (opcode >> field[2]) & mask
    return ("dn", reg)


def _normalized_absolute_value(decoded_op: Operand | None) -> int | None:
    if decoded_op is None or decoded_op.value is None:
        return None
    assert isinstance(decoded_op.value, int)
    value = decoded_op.value
    if decoded_op.mode == "absw":
        return value & 0xFFFF
    if decoded_op.mode == "absl":
        return value
    return None


def _reloc_target(inst: Instruction, hunk_session: HunkDisassemblySession, value: int) -> int | None:
    for ext_off in range(inst.offset + runtime_m68k_decode.OPWORD_BYTES,
                         inst.offset + inst.size):
        target = hunk_session.reloc_map.get(ext_off)
        if target == value:
            assert isinstance(target, int)
            return target
    return None


def _absolute_label_or_text(segment_addr: int,
                            hunk_session: HunkDisassemblySession,
                            token: str,
                            inst: Instruction) -> str:
    register_def = hardware_register_by_addr(segment_addr)
    if register_def is not None:
        text = render_hardware_absolute(segment_addr)
        assert isinstance(text, str)
        return text
    label = hunk_session.absolute_labels.get(segment_addr)
    if label is not None and segment_addr in hunk_session.reserved_absolute_addrs:
        assert isinstance(label, str)
        return label
    label = hunk_session.labels.get(segment_addr)
    if label is not None:
        assert isinstance(label, str)
        return label
    label = hunk_session.absolute_labels.get(segment_addr)
    if label is not None:
        assert isinstance(label, str)
        return label
    if segment_addr in hunk_session.reserved_absolute_addrs:
        raise ValueError(
            f"Missing absolute symbol metadata for {_instruction_ref(inst)} operand {token!r} "
            f"targeting ${segment_addr:08X}")
    return token.lower()


def _hardware_base_addr(hunk_session: HunkDisassemblySession,
                        inst_offset: int,
                        base_register: str) -> int | None:
    base_regs = hunk_session.hardware_base_regs.get(inst_offset)
    if base_regs is None:
        return None
    value = base_regs.get(base_register)
    assert value is None or isinstance(value, int)
    return value


def _hardware_relative_text(hunk_session: HunkDisassemblySession,
                            inst_offset: int,
                            base_register: str,
                            displacement: int,
                            token: str,
                            decoded_op: Operand) -> tuple[str, int] | None:
    base_addr = _hardware_base_addr(hunk_session, inst_offset, base_register)
    if base_addr is None:
        return None
    register_def = hardware_register_by_base_offset(base_addr, displacement)
    if register_def is None:
        return None
    text = render_hardware_relative(base_register, base_addr, displacement)
    if decoded_op.mode == "index":
        index_reg = decoded_op.index_reg
        assert index_reg is not None, f"Indexed operand missing index register: {token!r}"
        prefix = "a" if decoded_op.index_is_addr else "d"
        index_size = decoded_op.index_size
        assert index_size, f"Indexed operand missing index size: {token!r}"
        text = f"{text[:-1]},{prefix}{index_reg}.{index_size})"
    return text, hardware_absolute_addr(base_addr, displacement)


def _register_name(mode: str, reg: int, token: str | None = None) -> str:
    if mode == "an" and reg == 7 and token is not None and token.lower() == "sp":
        return "sp"
    return f"{'a' if mode == 'an' else 'd'}{reg}"


def _register_text(mode: str, reg: int, token: str) -> str:
    if mode == "an" and reg == 7 and token.lower() == "sp":
        return "sp"
    return token.lower()


def _address_base_name(reg: int) -> str:
    return "sp" if reg == 7 else f"a{reg}"


def _require_operand_reg(decoded_op: Operand, inst: Instruction) -> int:
    reg = decoded_op.reg
    assert reg is not None, f"Operand missing register for {_instruction_ref(inst)}"
    assert isinstance(reg, int)
    return reg


def _require_operand_value(decoded_op: Operand, inst: Instruction) -> int:
    value = decoded_op.value
    assert value is not None, f"Operand missing value for {_instruction_ref(inst)}"
    assert isinstance(value, int)
    return value


def _same_register_name(expected: str, actual: str | None) -> bool:
    if actual is None:
        return False
    if expected == actual:
        return True
    return {expected, actual} == {"a7", "sp"}


def _apply_instruction_text_substitutions(text: str, inst_offset: int,
                                          hunk_session: HunkDisassemblySession,
                                          include_arg_subs: bool) -> str:
    sub = hunk_session.lvo_substitutions.get(inst_offset)
    if sub:
        text = text.replace(sub[0], sub[1])
    if include_arg_subs:
        sub = hunk_session.arg_substitutions.get(inst_offset)
        if sub:
            text = text.replace(sub[0], sub[1])
    return text


def _struct_field_symbol(inst_offset: int, base_register: str, displacement: int,
                         hunk_session: HunkDisassemblySession,
                         used_structs: set[str] | None) -> str | None:
    metadata = _struct_field_metadata(
        inst_offset, base_register, displacement, hunk_session, used_structs)
    return None if metadata is None or metadata.field_symbol is None else metadata.field_symbol


def _struct_field_metadata(inst_offset: int, base_register: str, displacement: int,
                           hunk_session: HunkDisassemblySession,
                           used_structs: set[str] | None) -> StructFieldOperandMetadata | None:
    region_types = hunk_session.region_map.get(inst_offset)
    if not region_types or base_register not in region_types:
        return None
    reg_info = region_types[base_register]
    field_info = resolve_struct_field(
        hunk_session.os_kb.STRUCTS,
        reg_info.struct,
        reg_info.struct_offset + displacement,
    )
    if not field_info:
        return None
    if used_structs is not None:
        used_structs.add(field_info.owner_struct)
    return StructFieldOperandMetadata(
        symbol=field_info.field.name,
        owner_struct=field_info.owner_struct,
        field_symbol=field_info.field.name,
        context_name=reg_info.context_name,
    )


def _app_struct_field_metadata(base_register: str, displacement: int,
                               hunk_session: HunkDisassemblySession,
                               used_structs: set[str] | None
                               ) -> AppStructFieldOperandMetadata | None:
    base_info = hunk_session.platform.app_base
    if base_info is None:
        return None
    if base_register != f"a{base_info.reg_num}":
        return None
    for region_offset, region in hunk_session.app_struct_regions.items():
        region_end = region_offset + region.size
        if displacement < region_offset or displacement >= region_end:
            continue
        app_symbol = _app_offset_symbol(base_register, region_offset, hunk_session)
        if app_symbol is None:
            raise ValueError(
                f"Missing app symbol for struct region at offset {region_offset}")
        if displacement == region_offset:
            return AppStructFieldOperandMetadata(base_symbol=app_symbol)
        field_info = resolve_struct_field(
            hunk_session.os_kb.STRUCTS,
            region.struct,
            region.struct_offset + displacement - region_offset,
        )
        if field_info is None:
            return None
        if used_structs is not None:
            used_structs.add(field_info.owner_struct)
        return AppStructFieldOperandMetadata(
            base_symbol=app_symbol,
            field_symbol=field_info.field.name,
        )
    return None


def _app_offset_symbol(base_register: str, displacement: int,
                       hunk_session: HunkDisassemblySession) -> str | None:
    base_info = hunk_session.platform.app_base
    if not (hunk_session.app_offsets and base_info):
        return None
    if base_register != f"a{base_info.reg_num}":
        return None
    value = hunk_session.app_offsets.get(displacement)
    assert value is None or isinstance(value, str)
    return value


def _pc_relative_text(label: str | None, decoded_op: Operand, token: str) -> str:
    if label is None:
        return token
    if decoded_op.mode == "pcdisp":
        return f"{label}(pc)"
    index_reg = decoded_op.index_reg
    assert index_reg is not None, f"PC-index operand missing index register: {token!r}"
    prefix = "a" if decoded_op.index_is_addr else "d"
    index_size = decoded_op.index_size
    assert index_size, f"PC-index operand missing index size: {token!r}"
    return f"{label}(pc,{prefix}{index_reg}.{index_size})"


def _operand_symbol(metadata: SemanticOperandMetadata | None) -> str | None:
    if metadata is None:
        return None
    if isinstance(metadata, SymbolOperandMetadata):
        assert isinstance(metadata.symbol, str)
        return metadata.symbol
    if isinstance(metadata, StructFieldOperandMetadata):
        assert isinstance(metadata.symbol, str)
        return metadata.symbol
    if isinstance(metadata, AppStructFieldOperandMetadata):
        if metadata.field_symbol is None:
            assert isinstance(metadata.base_symbol, str)
            return metadata.base_symbol
        return f"{metadata.base_symbol}+{metadata.field_symbol}"
    return None


def _base_disp_text(base_register: str, displacement: int, token: str,
                    decoded_op: Operand,
                    metadata: SymbolOperandMetadata | StructFieldOperandMetadata | AppStructFieldOperandMetadata | None) -> str:
    symbol = None if metadata is None else _operand_symbol(metadata)
    if symbol is not None:
        if decoded_op.mode == "index":
            index_reg = decoded_op.index_reg
            assert index_reg is not None, f"Indexed operand missing index register: {token!r}"
            prefix = "a" if decoded_op.index_is_addr else "d"
            index_size = decoded_op.index_size
            assert index_size, f"Indexed operand missing index size: {token!r}"
            return f"{symbol}({base_register},{prefix}{index_reg}.{index_size})"
        return f"{symbol}({base_register})"
    return token


def _field_domain_constant_name(field_metadata: StructFieldOperandMetadata,
                                immediate_value: int,
                                hunk_session: HunkDisassemblySession,
                                ) -> str | None:
    field_key = f"{field_metadata.owner_struct}.{field_metadata.field_symbol}"
    domain_names: list[str] = []
    field_domains = hunk_session.os_kb.STRUCT_FIELD_VALUE_DOMAINS.get(field_key)
    if field_domains is None:
        return None
    if field_metadata.context_name is not None:
        context_domain_name = field_domains.get(field_metadata.context_name)
        if context_domain_name is not None:
            domain_names.append(context_domain_name)
    base_domain_name = field_domains.get(None)
    if base_domain_name is not None:
        domain_names.append(base_domain_name)
    for domain_name in domain_names:
        domain_constants = hunk_session.os_kb.VALUE_DOMAINS.get(domain_name)
        if domain_constants is None:
            raise KeyError(f"Missing value domain {domain_name}")
        matches: list[str] = []
        for constant_name in domain_constants:
            constant = hunk_session.os_kb.CONSTANTS.get(constant_name)
            if constant is None:
                raise KeyError(f"Missing constant {constant_name}")
            if constant.value == immediate_value:
                matches.append(constant_name)
        if not matches:
            continue
        if len(matches) != 1:
            raise ValueError(
                f"Ambiguous value-domain match for {field_key}={immediate_value}: {matches}"
            )
        return matches[0]
    if domain_names:
        raise ValueError(
            f"No KB value-domain match for {field_key}={immediate_value} "
            f"(domains: {domain_names})"
        )
    return None


def _apply_field_value_domain_substitutions(
        operands: tuple[SemanticOperand, ...],
        hunk_session: HunkDisassemblySession,
) -> tuple[SemanticOperand, ...]:
    field_metadata = next(
        (
            operand.metadata
            for operand in operands
            if isinstance(operand.metadata, StructFieldOperandMetadata)
            and operand.metadata.field_symbol is not None
        ),
        None,
    )
    if field_metadata is None:
        return operands
    rewritten: list[SemanticOperand] = []
    for operand in operands:
        if operand.kind != "immediate" or operand.value is None:
            rewritten.append(operand)
            continue
        constant_name = _field_domain_constant_name(
            field_metadata, operand.value, hunk_session)
        if constant_name is None:
            rewritten.append(operand)
            continue
        rewritten.append(replace(operand, text=f"#{constant_name}"))
    return tuple(rewritten)


def _register_operand(token: str, mode: str, reg: int) -> SemanticOperand:
    return SemanticOperand(
        kind="register",
        text=_register_text(mode, reg, token),
        register=_register_name(mode, reg, token),
    )


def _index_metadata(decoded_op: Operand, inst: Instruction) -> IndexedOperandMetadata:
    index_reg = decoded_op.index_reg
    assert index_reg is not None, (
        f"Indexed operand missing index register for {_instruction_ref(inst)}")
    index_size = decoded_op.index_size
    assert index_size, f"Indexed operand missing index size for {_instruction_ref(inst)}"
    prefix = "a" if decoded_op.index_is_addr else "d"
    return IndexedOperandMetadata(
        index_register=f"{prefix}{index_reg}",
        index_size=index_size,
    )


def _full_index_metadata(decoded_op: Operand, inst: Instruction) -> FullIndexedOperandMetadata:
    if decoded_op.index_suppressed:
        index_register = None
        index_size = None
        index_scale = None
    else:
        indexed = _index_metadata(decoded_op, inst)
        index_register = indexed.index_register
        index_size = indexed.index_size
        index_scale = decoded_op.index_scale
    if decoded_op.base_suppressed:
        base_register = None
    elif decoded_op.mode == "pcindex":
        base_register = "pc"
    else:
        reg = decoded_op.reg
        assert reg is not None, f"Operand missing register for {_instruction_ref(inst)}"
        base_register = _address_base_name(reg)
    return FullIndexedOperandMetadata(
        base_register=base_register,
        index_register=index_register,
        index_size=index_size,
        index_scale=index_scale,
        memory_indirect=decoded_op.memory_indirect,
        postindexed=decoded_op.postindexed,
        preindexed=bool(decoded_op.memory_indirect and not decoded_op.postindexed),
        base_suppressed=decoded_op.base_suppressed,
        index_suppressed=decoded_op.index_suppressed,
        base_displacement=decoded_op.base_displacement,
        outer_displacement=decoded_op.outer_displacement,
    )


def _decoded_operand_specs(inst: Instruction, hunk_session: HunkDisassemblySession,
                           meta: DecodedInstructionForEmit) -> list[OperandSpec]:
    decoded = meta.decoded
    operand_types = _operand_types_for_inst(inst, meta)
    if operand_types == ():
        return []
    ea_op = decoded.ea_op
    dst_op = decoded.dst_op
    reg_num = decoded.reg_num
    reg_mode = decoded.reg_mode
    secondary_reg = decoded.secondary_reg
    imm_val = decoded.imm_val
    bitfield = decoded.bitfield
    compare_reg = decoded.compare_reg
    update_reg = decoded.update_reg
    control_register = decoded.control_register
    ea_is_source = decoded.ea_is_source

    if operand_types == ("label",):
        return [LabelSpec()]
    if ea_op is None and dst_op is None and reg_num is None and imm_val is None:
        return []
    if operand_types == ("imm", "ea"):
        assert imm_val is not None and ea_op is not None, (
            f"Decoded immediate/ea shape incomplete for {_instruction_ref(inst)}")
        return [ImmediateSpec(imm_val), DecodedOperandSpec(ea_op)]
    if operand_types == ("bf_ea",):
        assert ea_op is not None and bitfield is not None, (
            f"Decoded bitfield ea shape incomplete for {_instruction_ref(inst)}")
        return [BitfieldOperandSpec(ea_op, bitfield)]
    if operand_types == ("bf_ea", "dn"):
        assert ea_op is not None and bitfield is not None and reg_num is not None, (
            f"Decoded bitfield ea/register shape incomplete for {_instruction_ref(inst)}")
        return [BitfieldOperandSpec(ea_op, bitfield), RegisterSpec("dn", reg_num)]
    if operand_types == ("dn", "bf_ea"):
        assert ea_op is not None and bitfield is not None and reg_num is not None, (
            f"Decoded register/bitfield-ea shape incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec("dn", reg_num), BitfieldOperandSpec(ea_op, bitfield)]
    if operand_types == ("dn", "dn", "ea"):
        assert compare_reg is not None and update_reg is not None and ea_op is not None, (
            f"Decoded CAS shape incomplete for {_instruction_ref(inst)}")
        return [
            RegisterSpec("dn", compare_reg),
            RegisterSpec("dn", update_reg),
            DecodedOperandSpec(ea_op),
        ]
    if operand_types == ("ea", "rn"):
        assert ea_op is not None and reg_num is not None and reg_mode is not None, (
            f"Decoded ea/rn shape incomplete for {_instruction_ref(inst)}")
        return [DecodedOperandSpec(ea_op), RegisterSpec(reg_mode, reg_num)]
    if operand_types == ("usp", "an"):
        assert reg_num is not None, (
            f"Decoded usp/address-register shape incomplete for {_instruction_ref(inst)}")
        return [SpecialRegisterSpec("usp"), RegisterSpec("an", reg_num)]
    if operand_types == ("an", "usp"):
        assert reg_num is not None, (
            f"Decoded address-register/usp shape incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec("an", reg_num), SpecialRegisterSpec("usp")]
    if operand_types == ("ctrl_reg", "rn"):
        assert control_register is not None and reg_num is not None and reg_mode is not None, (
            f"Decoded control-register/rn shape incomplete for {_instruction_ref(inst)}")
        return [SpecialRegisterSpec(control_register), RegisterSpec(reg_mode, reg_num)]
    if operand_types == ("rn", "ctrl_reg"):
        assert control_register is not None and reg_num is not None and reg_mode is not None, (
            f"Decoded rn/control-register shape incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec(reg_mode, reg_num), SpecialRegisterSpec(control_register)]
    if operand_types == ("an", "imm"):
        assert reg_num is not None and imm_val is not None, (
            f"Decoded address-register/immediate shape incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec("an", reg_num), ImmediateSpec(imm_val)]
    if operand_types == ("imm", "dn"):
        assert imm_val is not None and reg_num is not None, (
            f"Decoded immediate/register shape incomplete for {_instruction_ref(inst)}")
        return [ImmediateSpec(imm_val), RegisterSpec("dn", reg_num)]
    if operand_types == ("dn",):
        assert reg_num is not None, f"Decoded single-register shape incomplete for {_instruction_ref(inst)}"
        return [RegisterSpec("dn", reg_num)]
    if operand_types == ("rn",):
        assert reg_num is not None and reg_mode is not None, (
            f"Decoded rn shape incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec(reg_mode, reg_num)]
    if operand_types == ("an",):
        assert reg_num is not None, (
            f"Decoded single-address-register shape incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec("an", reg_num)]
    if operand_types == ("dn", "dn"):
        assert reg_num is not None, (
            f"Decoded register/register shape incomplete for {_instruction_ref(inst)}")
        dest = _selected_form_register(inst, meta, 1)
        if dest is None:
            dest = decode_inst_destination(inst, meta.mnemonic)
        assert dest is not None, (
            f"Unable to resolve destination operand from decode for {_instruction_ref(inst)}")
        return [RegisterSpec("dn", reg_num), RegisterSpec(dest[0], dest[1])]
    if operand_types == ("dn", "dn", "imm"):
        assert reg_num is not None and secondary_reg is not None and imm_val is not None, (
            f"Decoded PACK/UNPK register form incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec("dn", reg_num), RegisterSpec("dn", secondary_reg), ImmediateSpec(imm_val)]
    if operand_types == ("dn", "ea"):
        assert reg_num is not None and ea_op is not None, (
            f"Decoded register/ea shape incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec("dn", reg_num), DecodedOperandSpec(ea_op)]
    if operand_types == ("dn", "disp"):
        assert reg_num is not None and ea_op is not None, (
            f"Decoded register/displacement shape incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec("dn", reg_num), DecodedOperandSpec(ea_op)]
    if operand_types == ("ea", "ccr"):
        assert ea_op is not None, f"Decoded ea/ccr shape incomplete for {_instruction_ref(inst)}"
        return [DecodedOperandSpec(ea_op), SpecialRegisterSpec("ccr")]
    if operand_types == ("ea", "sr"):
        assert ea_op is not None, f"Decoded ea/sr shape incomplete for {_instruction_ref(inst)}"
        return [DecodedOperandSpec(ea_op), SpecialRegisterSpec("sr")]
    if operand_types == ("sr", "ea"):
        assert ea_op is not None, f"Decoded sr/ea shape incomplete for {_instruction_ref(inst)}"
        return [SpecialRegisterSpec("sr"), DecodedOperandSpec(ea_op)]
    if operand_types == ("ccr", "ea"):
        assert ea_op is not None, f"Decoded ccr/ea shape incomplete for {_instruction_ref(inst)}"
        return [SpecialRegisterSpec("ccr"), DecodedOperandSpec(ea_op)]
    if operand_types == ("ea", "dn"):
        assert ea_op is not None and reg_num is not None, (
            f"Decoded ea/register shape incomplete for {_instruction_ref(inst)}")
        if secondary_reg is not None and secondary_reg != reg_num:
            return [DecodedOperandSpec(ea_op), RegisterPairSpec(secondary_reg, reg_num)]
        return [DecodedOperandSpec(ea_op), RegisterSpec("dn", reg_num)]
    if operand_types == ("ea", "dn_pair"):
        assert ea_op is not None and reg_num is not None and secondary_reg is not None, (
            f"Decoded ea/register-pair shape incomplete for {_instruction_ref(inst)}")
        return [DecodedOperandSpec(ea_op), RegisterPairSpec(secondary_reg, reg_num)]
    if operand_types == ("disp", "dn"):
        assert ea_op is not None and reg_num is not None, (
            f"Decoded displacement/register shape incomplete for {_instruction_ref(inst)}")
        return [DecodedOperandSpec(ea_op), RegisterSpec("dn", reg_num)]
    if operand_types == ("ea", "an"):
        assert ea_op is not None and reg_num is not None, (
            f"Decoded ea/address-register shape incomplete for {_instruction_ref(inst)}")
        return [DecodedOperandSpec(ea_op), RegisterSpec("an", reg_num)]
    if operand_types == ("predec", "predec"):
        assert ea_op is not None and dst_op is not None, (
            f"Decoded predecrement/predecrement shape incomplete for {_instruction_ref(inst)}")
        return [DecodedOperandSpec(ea_op), DecodedOperandSpec(dst_op)]
    if operand_types == ("predec", "predec", "imm"):
        assert ea_op is not None and dst_op is not None and imm_val is not None, (
            f"Decoded PACK/UNPK predecrement form incomplete for {_instruction_ref(inst)}")
        return [DecodedOperandSpec(ea_op), DecodedOperandSpec(dst_op), ImmediateSpec(imm_val)]
    if operand_types == ("postinc", "postinc"):
        assert ea_op is not None and dst_op is not None, (
            f"Decoded postincrement/postincrement shape incomplete for {_instruction_ref(inst)}")
        return [DecodedOperandSpec(ea_op), DecodedOperandSpec(dst_op)]
    if operand_types in {("absl", "postinc"), ("postinc", "absl"), ("absl", "ind"), ("ind", "absl")}:
        assert ea_op is not None and dst_op is not None, (
            f"Decoded MOVE16 mixed addressing shape incomplete for {_instruction_ref(inst)}")
        return [DecodedOperandSpec(ea_op), DecodedOperandSpec(dst_op)]
    if dst_op is None and reg_num is None:
        if operand_types == ("reglist", "ea"):
            assert ea_op is not None, f"Decoded ea operand missing for {_instruction_ref(inst)}"
            return [RegListSpec(), DecodedOperandSpec(ea_op)]
        if operand_types == ("ea", "reglist"):
            assert ea_op is not None, f"Decoded ea operand missing for {_instruction_ref(inst)}"
            return [DecodedOperandSpec(ea_op), RegListSpec()]
        if operand_types == ("ea",):
            assert ea_op is not None, f"Decoded ea operand missing for {_instruction_ref(inst)}"
            return [DecodedOperandSpec(ea_op)]
        if operand_types == ("imm",):
            assert imm_val is not None, f"Decoded immediate operand missing for {_instruction_ref(inst)}"
            return [ImmediateSpec(imm_val)]
        if ea_op is not None and imm_val is not None:
            return [ImmediateSpec(imm_val), DecodedOperandSpec(ea_op)]
        if ea_op is not None:
            return [DecodedOperandSpec(ea_op)]
        if imm_val is not None:
            return [ImmediateSpec(imm_val)]
        raise ValueError(
            f"Unsupported single-operand instruction shape for {_instruction_ref(inst)}")
    if operand_types == ("dn", "label"):
        assert reg_num is not None, (
            f"Decoded register/label shape incomplete for {_instruction_ref(inst)}")
        return [RegisterSpec("dn", reg_num), LabelSpec()]
    if operand_types == ("rn", "ea"):
        assert ea_op is not None and reg_num is not None and reg_mode is not None and ea_is_source is not None, (
            f"Decoded rn/ea shape incomplete for {_instruction_ref(inst)}")
        reg_spec = RegisterSpec(reg_mode, reg_num)
        return [reg_spec, DecodedOperandSpec(ea_op)] if ea_is_source else [DecodedOperandSpec(ea_op), reg_spec]
    if ea_is_source is not None and ea_op is not None and reg_num is not None:
        reg_spec = RegisterSpec("dn", reg_num)
        return [DecodedOperandSpec(ea_op), reg_spec] if ea_is_source else [reg_spec, DecodedOperandSpec(ea_op)]

    if ea_op is not None:
        first: OperandSpec = DecodedOperandSpec(ea_op)
    elif imm_val is not None:
        first = ImmediateSpec(imm_val)
    else:
        raise AssertionError(
            f"Unable to resolve first operand from decode for {_instruction_ref(inst)}"
        )

    if dst_op is not None:
        second: OperandSpec = DecodedOperandSpec(dst_op)
    else:
        dest = decode_inst_destination(inst, meta.mnemonic)
        assert dest is not None, (
            f"Unable to resolve destination operand from decode for {_instruction_ref(inst)}")
        second = RegisterSpec(dest[0], dest[1])
    return [first, second]


def _operand_text_slots(inst: Instruction, operand_count: int) -> list[str]:
    if operand_count == 0:
        return []
    if inst.operand_texts is None:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing operand_texts")
    tokens = [token for token in inst.operand_texts if token]
    if len(tokens) != operand_count:
        raise ValueError(
            f"Operand text count mismatch for {_instruction_ref(inst)}: "
            f"decoded {operand_count}, text {len(tokens)}")
    return tokens


def _simple_semantic_from_node(inst: Instruction, node: DecodedOperandNode, spec: OperandSpec,
                               operand_index: int,
                               hunk_session: HunkDisassemblySession,
                               meta: DecodedInstructionForEmit,
                               used_structs: set[str] | None,
                               include_arg_subs: bool) -> SemanticOperand | None:
    flow_type = runtime_m68k_analysis.FLOW_TYPES[meta.mnemonic]
    labels = hunk_session.labels

    if isinstance(spec, RegisterSpec) and node.kind == "register":
        mode, reg = spec.mode, spec.reg
        expected = f"{'a' if mode == 'an' else 'd'}{reg}"
        if not _same_register_name(expected, node.register):
            raise ValueError(
                f"Typed register mismatch for {_instruction_ref(inst)}: "
                f"decoded {expected}, node {node.register}")
        return SemanticOperand(kind="register", text=node.text.lower(), register=node.register)

    if isinstance(spec, SpecialRegisterSpec) and node.kind == "special_register":
        if spec.register != node.register:
            raise ValueError(
                f"Typed special-register mismatch for {_instruction_ref(inst)}: "
                f"decoded {spec.register}, node {node.register}")
        return SemanticOperand(kind="register", text=node.text.lower(), register=node.register)

    if isinstance(spec, RegListSpec) and node.kind == "register_list":
        assert isinstance(node.metadata, DecodedRegisterListNodeMetadata), (
            f"Typed register list metadata missing for {_instruction_ref(inst)}")
        return SemanticOperand(
            kind="register_list",
            text=node.text,
            metadata=RegisterListOperandMetadata(registers=node.metadata.registers),
        )

    if isinstance(spec, RegisterPairSpec) and node.kind == "register_pair":
        hi, lo = spec.hi, spec.lo
        expected_pair_registers = (f"d{hi}", f"d{lo}")
        assert isinstance(node.metadata, DecodedRegisterPairNodeMetadata), (
            f"Typed register pair metadata missing for {_instruction_ref(inst)}")
        actual_pair_registers = node.metadata.registers
        if actual_pair_registers != expected_pair_registers:
            raise ValueError(
                f"Typed register-pair mismatch for {_instruction_ref(inst)}: "
                f"decoded {expected_pair_registers}, node {actual_pair_registers}")
        return SemanticOperand(
            kind="register_pair",
            text=node.text.lower(),
            metadata=RegisterPairOperandMetadata(registers=expected_pair_registers),
        )

    if isinstance(spec, ImmediateSpec) and node.kind == "immediate":
        value = spec.value
        same_encoded_value = False
        if node.value is not None and value is not None:
            for bits in (8, 16, 32):
                mask = (1 << bits) - 1
                if (node.value & mask) == value:
                    same_encoded_value = True
                    break
        if node.value != value and not same_encoded_value:
            raise ValueError(
                f"Typed immediate mismatch for {_instruction_ref(inst)}: "
                f"decoded {value}, node {node.value}")
        target = _reloc_target(inst, hunk_session, value)
        label = labels.get(target) if target is not None else None
        text = f"#{label}" if label is not None else node.text
        text = _apply_instruction_text_substitutions(
            text, inst.offset, hunk_session, include_arg_subs)
        return SemanticOperand(
            kind="immediate_symbol" if label is not None else "immediate",
            text=text,
            value=value,
            segment_addr=target,
            metadata=SymbolOperandMetadata(symbol=label) if label is not None else None,
        )

    if (isinstance(spec, ImmediateSpec)
            and node.kind == "branch_target"
            and flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL)):
        segment_addr = node.target
        assert segment_addr is not None, f"Typed branch target missing for {_instruction_ref(inst)}"
        label = labels.get(segment_addr)
        text = label if label is not None else node.text
        return SemanticOperand(
            kind="call_target" if flow_type == _FLOW_CALL else "branch_target",
            text=text,
            value=segment_addr,
            segment_addr=segment_addr,
            metadata=SymbolOperandMetadata(symbol=label) if label is not None else None,
        )

    if isinstance(spec, LabelSpec) and node.kind == "branch_target":
        segment_addr = node.target
        assert segment_addr is not None, f"Typed branch target missing for {_instruction_ref(inst)}"
        label = labels.get(segment_addr)
        text = label if label is not None else node.text
        return SemanticOperand(
            kind="call_target" if flow_type == _FLOW_CALL else "branch_target",
            text=text,
            value=segment_addr,
            segment_addr=segment_addr,
            metadata=SymbolOperandMetadata(symbol=label) if label is not None else None,
        )

    if isinstance(spec, BitfieldOperandSpec) and node.kind == "bitfield_ea":
        decoded_op, bitfield = spec.operand, spec.bitfield
        metadata = node.metadata
        assert isinstance(metadata, DecodedBitfieldNodeMetadata), (
            f"Typed bitfield operand missing base node for {_instruction_ref(inst)}")
        base = _simple_semantic_from_node(
            inst, metadata.base_node, DecodedOperandSpec(decoded_op), operand_index,
            hunk_session, meta, used_structs, include_arg_subs)
        assert base is not None, f"Typed bitfield base node did not decode for {_instruction_ref(inst)}"
        for key, node_value, decoded_value in (
            ("offset_is_register", metadata.offset_is_register, bitfield.offset_is_register),
            ("offset_value", metadata.offset_value, bitfield.offset_value),
            ("width_is_register", metadata.width_is_register, bitfield.width_is_register),
            ("width_value", metadata.width_value, bitfield.width_value),
        ):
            if node_value != decoded_value:
                raise ValueError(
                    f"Typed bitfield operand mismatch for {_instruction_ref(inst)}: "
                    f"{key} decoded {decoded_value}, node {node_value}")
        symbol = _operand_symbol(base.metadata)
        bitfield_metadata = BitfieldOperandMetadata(bitfield=bitfield, symbol=symbol)
        return SemanticOperand(
            kind="bitfield_ea",
            text=node.text,
            value=base.value,
            register=base.register,
            base_register=base.base_register,
            displacement=base.displacement,
            segment_addr=base.segment_addr,
            metadata=bitfield_metadata,
        )

    if isinstance(spec, DecodedOperandSpec):
        decoded_operand = spec.operand
        op_mode = decoded_operand.mode
        op_value = decoded_operand.value
        semantic_metadata: SemanticOperandMetadata | None = None
        kind = "text"
        operand_value: int | None = None
        register = None
        base_register = None
        displacement = None
        segment_addr = None
        text = node.text

        if op_mode in ("dn", "dreg") and node.kind == "register":
            expected = f"d{_require_operand_reg(decoded_operand, inst)}"
            if node.register != expected:
                raise ValueError(
                    f"Typed register mismatch for {_instruction_ref(inst)}: "
                    f"decoded {expected}, node {node.register}")
            kind = "register"
            register = node.register
            text = node.text.lower()
        elif op_mode in ("an", "areg") and node.kind == "register":
            expected = f"a{_require_operand_reg(decoded_operand, inst)}"
            if not _same_register_name(expected, node.register):
                raise ValueError(
                    f"Typed register mismatch for {_instruction_ref(inst)}: "
                    f"decoded {expected}, node {node.register}")
            kind = "register"
            register = node.register
            text = node.text.lower()
        elif op_mode == "imm" and node.kind == "immediate":
            operand_value = op_value
            same_encoded_value = False
            if node.value is not None and operand_value is not None:
                for bits in (8, 16, 32):
                    mask = (1 << bits) - 1
                    if (node.value & mask) == operand_value:
                        same_encoded_value = True
                        break
            if node.value != operand_value and not same_encoded_value:
                raise ValueError(
                    f"Typed immediate mismatch for {_instruction_ref(inst)}: "
                    f"decoded {operand_value}, node {node.value}")
            target = _reloc_target(
                inst, hunk_session, operand_value) if operand_value is not None else None
            label = labels.get(target) if target is not None else None
            if label is not None:
                kind = "immediate_symbol"
                segment_addr = target
                semantic_metadata = SymbolOperandMetadata(symbol=label)
                text = f"#{label}"
            else:
                kind = "immediate"
        elif op_mode == "ind" and node.kind == "indirect":
            base_register = _address_base_name(_require_operand_reg(decoded_operand, inst))
            assert isinstance(node.metadata, DecodedBaseRegisterNodeMetadata), (
                f"Typed indirect metadata missing for {_instruction_ref(inst)}")
            if node.metadata.base_register != base_register:
                raise ValueError(
                    f"Typed indirect mismatch for {_instruction_ref(inst)}: "
                    f"decoded {base_register}, node {node.metadata.base_register}")
            kind = "indirect"
            custom = _hardware_relative_text(
                hunk_session, inst.offset, base_register, 0, node.text, decoded_operand)
            if custom is not None:
                text, segment_addr = custom
        elif op_mode == "postinc" and node.kind == "postincrement":
            base_register = _address_base_name(_require_operand_reg(decoded_operand, inst))
            assert isinstance(node.metadata, DecodedBaseRegisterNodeMetadata), (
                f"Typed postincrement metadata missing for {_instruction_ref(inst)}")
            if node.metadata.base_register != base_register:
                raise ValueError(
                    f"Typed postincrement mismatch for {_instruction_ref(inst)}: "
                    f"decoded {base_register}, node {node.metadata.base_register}")
            kind = "postincrement"
        elif op_mode == "predec" and node.kind == "predecrement":
            base_register = _address_base_name(_require_operand_reg(decoded_operand, inst))
            assert isinstance(node.metadata, DecodedBaseRegisterNodeMetadata), (
                f"Typed predecrement metadata missing for {_instruction_ref(inst)}")
            if node.metadata.base_register != base_register:
                raise ValueError(
                    f"Typed predecrement mismatch for {_instruction_ref(inst)}: "
                    f"decoded {base_register}, node {node.metadata.base_register}")
            kind = "predecrement"
        elif op_mode == "disp" and node.kind == "base_displacement":
            base_register = _address_base_name(_require_operand_reg(decoded_operand, inst))
            displacement = _require_operand_value(decoded_operand, inst)
            assert isinstance(node.metadata, DecodedBaseDisplacementNodeMetadata), (
                f"Typed base displacement metadata missing for {_instruction_ref(inst)}")
            if node.metadata.base_register != base_register:
                raise ValueError(
                    f"Typed base displacement mismatch for {_instruction_ref(inst)}: "
                    f"decoded {base_register}, node {node.metadata.base_register}")
            if node.metadata.displacement != displacement:
                raise ValueError(
                    f"Typed base displacement mismatch for {_instruction_ref(inst)}: "
                    f"decoded {displacement}, node {node.metadata.displacement}")
            operand_value = displacement
            field_metadata = _struct_field_metadata(
                inst.offset, base_register, displacement, hunk_session, used_structs)
            app_region_metadata = _app_struct_field_metadata(
                base_register, displacement, hunk_session, used_structs)
            if field_metadata is not None:
                kind = "base_displacement_symbol"
                semantic_metadata = field_metadata
            elif app_region_metadata is not None:
                kind = "base_displacement_symbol"
                semantic_metadata = app_region_metadata
            else:
                app_symbol = _app_offset_symbol(base_register, displacement, hunk_session)
                if app_symbol is not None:
                    kind = "base_displacement_symbol"
                    semantic_metadata = SymbolOperandMetadata(symbol=app_symbol)
                else:
                    kind = "base_displacement"
            custom = _hardware_relative_text(
                hunk_session, inst.offset, base_register, displacement, node.text, decoded_operand)
            if custom is not None:
                text, segment_addr = custom
                kind = "base_displacement_symbol"
                semantic_metadata = SymbolOperandMetadata(symbol=text.split("(", 1)[0])
            else:
                symbol_metadata = (
                    semantic_metadata
                    if isinstance(semantic_metadata, (SymbolOperandMetadata, StructFieldOperandMetadata, AppStructFieldOperandMetadata))
                    else None
                )
                text = _base_disp_text(
                    base_register, displacement, node.text, decoded_operand, symbol_metadata)
        elif op_mode in ("absw", "absl") and node.kind == "absolute_target":
            operand_value = _normalized_absolute_value(decoded_operand)
            segment_addr = operand_value
            if node.target != segment_addr:
                raise ValueError(
                    f"Typed absolute target mismatch for {_instruction_ref(inst)}: "
                    f"decoded {segment_addr}, node {node.target}")
            assert segment_addr is not None, (
                f"Typed absolute target missing value for {_instruction_ref(inst)}")
            label = _absolute_label_or_text(segment_addr, hunk_session, node.text, inst)
            text = label
            if flow_type == _FLOW_CALL and operand_index == 0:
                kind = "call_target"
            elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP) and operand_index == 0:
                kind = "branch_target"
            else:
                kind = "absolute_target"
        elif op_mode == "pcdisp" and node.kind == "pc_relative_target":
            segment_addr = _require_operand_value(decoded_operand, inst)
            operand_value = segment_addr
            if node.target != segment_addr:
                raise ValueError(
                    f"Typed PC-relative target mismatch for {_instruction_ref(inst)}: "
                    f"decoded {segment_addr}, node {node.target}")
            label = labels.get(segment_addr)
            text = _pc_relative_text(label, decoded_operand, node.text)
            if flow_type == _FLOW_CALL and operand_index == 0:
                kind = "call_target"
            elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP) and operand_index == 0:
                kind = "branch_target"
            else:
                kind = "pc_relative_target"
        elif op_mode == "index" and node.kind == "indexed":
            base_register = _address_base_name(_require_operand_reg(decoded_operand, inst))
            displacement = _require_operand_value(decoded_operand, inst)
            if isinstance(node.metadata, DecodedIndexedNodeMetadata):
                if node.metadata.base_register != base_register:
                    raise ValueError(
                        f"Typed indexed operand mismatch for {_instruction_ref(inst)}: "
                        f"decoded {base_register}, node {node.metadata.base_register}")
                if node.metadata.displacement != displacement:
                    raise ValueError(
                        f"Typed indexed operand mismatch for {_instruction_ref(inst)}: "
                        f"decoded {displacement}, node {node.metadata.displacement}")
                semantic_metadata = _index_metadata(decoded_operand, inst)
                indexed_metadata = semantic_metadata
                if node.metadata.index_register != indexed_metadata.index_register:
                    raise ValueError(
                        f"Typed indexed operand mismatch for {_instruction_ref(inst)}: "
                        f"decoded {indexed_metadata.index_register}, node {node.metadata.index_register}")
                if node.metadata.index_size != indexed_metadata.index_size:
                    raise ValueError(
                        f"Typed indexed operand mismatch for {_instruction_ref(inst)}: "
                        f"decoded {indexed_metadata.index_size}, node {node.metadata.index_size}")
            elif isinstance(node.metadata, DecodedFullExtensionNodeMetadata):
                semantic_metadata = _full_index_metadata(decoded_operand, inst)
                expected_metadata = FullIndexedOperandMetadata(
                    base_register=node.metadata.base_register,
                    index_register=node.metadata.index_register,
                    index_size=node.metadata.index_size,
                    index_scale=node.metadata.index_scale,
                    memory_indirect=node.metadata.memory_indirect,
                    postindexed=node.metadata.postindexed,
                    preindexed=node.metadata.preindexed,
                    base_suppressed=node.metadata.base_suppressed,
                    index_suppressed=node.metadata.index_suppressed,
                    base_displacement=node.metadata.base_displacement,
                    outer_displacement=node.metadata.outer_displacement,
                )
                if expected_metadata != semantic_metadata:
                    raise ValueError(
                        f"Typed full indexed operand mismatch for {_instruction_ref(inst)}: "
                        f"decoded {semantic_metadata}, node {expected_metadata}")
            else:
                raise AssertionError(
                    f"Typed indexed metadata missing for {_instruction_ref(inst)}"
                )
            operand_value = displacement
            symbol = None
            if decoded_operand.index_suppressed:
                symbol = _struct_field_symbol(inst.offset, base_register, displacement,
                                              hunk_session, used_structs)
                if symbol is None:
                    app_field_metadata = _app_struct_field_metadata(
                        base_register, displacement, hunk_session, used_structs)
                    symbol = _operand_symbol(app_field_metadata)
                if symbol is None:
                    symbol = _app_offset_symbol(base_register, displacement, hunk_session)
            kind = "base_displacement_symbol" if symbol is not None else "indexed"
            if symbol is not None:
                semantic_metadata = replace(
                    semantic_metadata,
                    symbol=symbol,
                )
            custom = _hardware_relative_text(
                hunk_session, inst.offset, base_register, displacement, node.text, decoded_operand)
            if custom is not None:
                text, segment_addr = custom
                kind = "base_displacement_symbol"
                semantic_metadata = replace(
                    semantic_metadata,
                    symbol=text.split("(", 1)[0],
                )
            else:
                text = _base_disp_text(
                    base_register,
                    displacement,
                    node.text,
                    decoded_operand,
                    SymbolOperandMetadata(symbol=symbol) if symbol is not None else None,
                )
        elif op_mode == "index" and node.kind == "memory_indirect_indexed":
            base_register = _address_base_name(_require_operand_reg(decoded_operand, inst))
            semantic_metadata = _full_index_metadata(decoded_operand, inst)
            assert isinstance(node.metadata, DecodedFullExtensionNodeMetadata), (
                f"Typed full indexed metadata missing for {_instruction_ref(inst)}")
            expected_metadata = FullIndexedOperandMetadata(
                base_register=node.metadata.base_register,
                index_register=node.metadata.index_register,
                index_size=node.metadata.index_size,
                index_scale=node.metadata.index_scale,
                memory_indirect=node.metadata.memory_indirect,
                postindexed=node.metadata.postindexed,
                preindexed=node.metadata.preindexed,
                base_suppressed=node.metadata.base_suppressed,
                index_suppressed=node.metadata.index_suppressed,
                base_displacement=node.metadata.base_displacement,
                outer_displacement=node.metadata.outer_displacement,
            )
            if expected_metadata != semantic_metadata:
                raise ValueError(
                    f"Typed full indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {semantic_metadata}, node {expected_metadata}")
            full_index_metadata = semantic_metadata
            displacement = full_index_metadata.base_displacement
            operand_value = displacement
            kind = "memory_indirect_indexed"
            text = node.text
        elif op_mode == "pcindex" and node.kind == "pc_relative_indexed":
            segment_addr = node.target
            expected_target = _require_operand_value(decoded_operand, inst)
            if node.target != expected_target:
                raise ValueError(
                    f"Typed PC-indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {expected_target}, node {node.target}")
            assert isinstance(node.metadata, DecodedIndexedNodeMetadata), (
                f"Typed PC-indexed metadata missing for {_instruction_ref(inst)}")
            semantic_metadata = _index_metadata(decoded_operand, inst)
            indexed_metadata = semantic_metadata
            if node.metadata.index_register != indexed_metadata.index_register:
                raise ValueError(
                    f"Typed PC-indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {indexed_metadata.index_register}, node {node.metadata.index_register}")
            if node.metadata.index_size != indexed_metadata.index_size:
                raise ValueError(
                    f"Typed PC-indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {indexed_metadata.index_size}, node {node.metadata.index_size}")
            operand_value = op_value
            label = labels.get(segment_addr) if segment_addr is not None else None
            text = _pc_relative_text(label, decoded_operand, node.text)
            kind = "pc_relative_indexed"
        elif op_mode == "pcindex" and node.kind == "pc_memory_indirect_indexed":
            segment_addr = node.target
            expected_target = _require_operand_value(decoded_operand, inst)
            if node.target != expected_target:
                raise ValueError(
                    f"Typed PC full indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {expected_target}, node {node.target}")
            semantic_metadata = _full_index_metadata(decoded_operand, inst)
            assert isinstance(node.metadata, DecodedFullExtensionNodeMetadata), (
                f"Typed PC full indexed metadata missing for {_instruction_ref(inst)}")
            expected_metadata = FullIndexedOperandMetadata(
                base_register=node.metadata.base_register,
                index_register=node.metadata.index_register,
                index_size=node.metadata.index_size,
                index_scale=node.metadata.index_scale,
                memory_indirect=node.metadata.memory_indirect,
                postindexed=node.metadata.postindexed,
                preindexed=node.metadata.preindexed,
                base_suppressed=node.metadata.base_suppressed,
                index_suppressed=node.metadata.index_suppressed,
                base_displacement=node.metadata.base_displacement,
                outer_displacement=node.metadata.outer_displacement,
            )
            if expected_metadata != semantic_metadata:
                raise ValueError(
                    f"Typed PC full indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {semantic_metadata}, node {expected_metadata}")
            operand_value = op_value
            kind = "pc_memory_indirect_indexed"
            text = node.text
        else:
            return None

        text = _apply_instruction_text_substitutions(
            text, inst.offset, hunk_session, include_arg_subs)
        return SemanticOperand(
            kind=kind,
            text=text,
            value=operand_value,
            register=register,
            base_register=base_register,
            displacement=displacement,
            segment_addr=segment_addr,
            metadata=semantic_metadata,
        )

    return None


def _build_decoded_semantic_operand(inst: Instruction, token: str, spec: OperandSpec,
                                    operand_index: int,
                                    hunk_session: HunkDisassemblySession,
                                    meta: DecodedInstructionForEmit,
                                    used_structs: set[str] | None,
                                    include_arg_subs: bool) -> SemanticOperand:
    flow_type = runtime_m68k_analysis.FLOW_TYPES[meta.mnemonic]
    branch_target = None
    if flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL):
        branch_target = extract_branch_target(inst, inst.offset)
    labels = hunk_session.labels

    if isinstance(spec, RegisterSpec):
        return _register_operand(token, spec.mode, spec.reg)

    if isinstance(spec, BitfieldOperandSpec):
        decoded_operand, bitfield = spec.operand, spec.bitfield
        base = _build_decoded_semantic_operand(
            inst, token, DecodedOperandSpec(decoded_operand), operand_index,
            hunk_session, meta, used_structs, include_arg_subs)
        return SemanticOperand(
            kind="bitfield_ea",
            text=base.text,
            value=base.value,
            register=base.register,
            base_register=base.base_register,
            displacement=base.displacement,
            segment_addr=base.segment_addr,
            metadata=BitfieldOperandMetadata(
                bitfield=bitfield,
                symbol=_operand_symbol(base.metadata),
            ),
        )

    if isinstance(spec, SpecialRegisterSpec):
        return SemanticOperand(
            kind="register",
            text=token.lower(),
            register=spec.register,
        )

    if isinstance(spec, RegisterPairSpec):
        hi, lo = spec.hi, spec.lo
        return SemanticOperand(
            kind="register_pair",
            text=token.lower(),
            metadata=RegisterPairOperandMetadata(registers=(f"d{hi}", f"d{lo}")),
        )

    if isinstance(spec, RegListSpec):
        return SemanticOperand(kind="register_list", text=token)

    if isinstance(spec, LabelSpec):
        if branch_target is None:
            raise ValueError(
                f"Decoded label operand missing branch target for {_instruction_ref(inst)}")
        label = labels.get(branch_target)
        text = label if label is not None else token
        return SemanticOperand(
            kind="call_target" if flow_type == _FLOW_CALL else "branch_target",
            text=text,
            value=branch_target,
            segment_addr=branch_target,
            metadata=SymbolOperandMetadata(symbol=label) if label is not None else None,
        )

    if isinstance(spec, ImmediateSpec):
        value = spec.value
        target = branch_target if flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL) else _reloc_target(
            inst, hunk_session, value)
        label = labels.get(target) if target is not None else None
        if flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL) and label is not None:
            text = label
            kind = "call_target" if flow_type == _FLOW_CALL else "branch_target"
        else:
            text = f"#{label}" if label is not None else token
            kind = "immediate_symbol" if label is not None else "immediate"
        text = _apply_instruction_text_substitutions(
            text, inst.offset, hunk_session, include_arg_subs)
        return SemanticOperand(
            kind=kind,
            text=text,
            value=value,
            segment_addr=target,
            metadata=SymbolOperandMetadata(symbol=label) if label is not None else None,
        )

    assert isinstance(spec, DecodedOperandSpec), (
        f"Unexpected operand spec for {_instruction_ref(inst)}")
    decoded_operand = spec.operand
    op_mode = decoded_operand.mode
    op_value = decoded_operand.value
    metadata: SemanticOperandMetadata | None = None
    kind = "text"
    operand_value: int | None = None
    register = None
    base_register = None
    displacement = None
    segment_addr = None
    text = token

    if op_mode in ("dn", "dreg"):
        register = _register_name("dn", _require_operand_reg(decoded_operand, inst), token)
        kind = "register"
        text = _register_text("dn", _require_operand_reg(decoded_operand, inst), token)
    elif op_mode in ("an", "areg"):
        register = _register_name("an", _require_operand_reg(decoded_operand, inst), token)
        kind = "register"
        text = _register_text("an", _require_operand_reg(decoded_operand, inst), token)
    elif op_mode == "imm":
        operand_value = op_value
        target = _reloc_target(
            inst, hunk_session, operand_value) if operand_value is not None else None
        label = labels.get(target) if target is not None else None
        if label is not None:
            kind = "immediate_symbol"
            segment_addr = target
            metadata = SymbolOperandMetadata(symbol=label)
            text = f"#{label}"
        else:
            kind = "immediate"
    elif op_mode in ("absw", "absl"):
        operand_value = _normalized_absolute_value(decoded_operand)
        segment_addr = operand_value
        if segment_addr is None:
            raise ValueError(f"Decoded absolute operand missing value for {_instruction_ref(inst)}")
        label = _absolute_label_or_text(segment_addr, hunk_session, token, inst)
        text = label
        if flow_type == _FLOW_CALL and operand_index == 0:
            kind = "call_target"
        elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP) and operand_index == 0:
            kind = "branch_target"
        else:
            kind = "absolute_target"
    elif op_mode == "pcdisp":
        segment_addr = _require_operand_value(decoded_operand, inst)
        operand_value = segment_addr
        label = labels.get(segment_addr)
        text = _pc_relative_text(label, decoded_operand, token)
        if flow_type == _FLOW_CALL and operand_index == 0:
            kind = "call_target"
        elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP) and operand_index == 0:
            kind = "branch_target"
        else:
            kind = "pc_relative_target"
    elif op_mode == "pcindex":
        segment_addr = op_value
        operand_value = op_value
        label = labels.get(segment_addr) if segment_addr is not None else None
        text = _pc_relative_text(label, decoded_operand, token)
        if flow_type == _FLOW_CALL and operand_index == 0:
            kind = "call_target"
        elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP) and operand_index == 0:
            kind = "branch_target"
        elif decoded_operand.memory_indirect:
            metadata = _full_index_metadata(decoded_operand, inst)
            kind = "pc_memory_indirect_indexed"
        else:
            metadata = _index_metadata(decoded_operand, inst)
            kind = "pc_relative_indexed"
    elif op_mode == "disp":
        base_register = f"a{_require_operand_reg(decoded_operand, inst)}"
        displacement = _require_operand_value(decoded_operand, inst)
        operand_value = displacement
        field_metadata = _struct_field_metadata(
            inst.offset, base_register, displacement, hunk_session, used_structs)
        app_region_metadata = _app_struct_field_metadata(
            base_register, displacement, hunk_session, used_structs)
        if field_metadata is not None:
            kind = "base_displacement_symbol"
            metadata = field_metadata
        elif app_region_metadata is not None:
            kind = "base_displacement_symbol"
            metadata = app_region_metadata
        else:
            app_symbol = _app_offset_symbol(base_register, displacement, hunk_session)
            if app_symbol is not None:
                kind = "base_displacement_symbol"
                metadata = SymbolOperandMetadata(symbol=app_symbol)
            else:
                kind = "base_displacement"
        custom = _hardware_relative_text(
            hunk_session, inst.offset, base_register, displacement, token, decoded_operand)
        if custom is not None:
            text, segment_addr = custom
            kind = "base_displacement_symbol"
            metadata = SymbolOperandMetadata(symbol=text.split("(", 1)[0])
        else:
            symbol_metadata = (
                metadata
                if isinstance(metadata, (SymbolOperandMetadata, StructFieldOperandMetadata, AppStructFieldOperandMetadata))
                else None
            )
            text = _base_disp_text(
                base_register, displacement, token, decoded_operand, symbol_metadata)
    elif op_mode == "ind":
        base_register = f"a{_require_operand_reg(decoded_operand, inst)}"
        kind = "indirect"
        custom = _hardware_relative_text(
            hunk_session, inst.offset, base_register, 0, token, decoded_operand)
        if custom is not None:
            text, segment_addr = custom
    elif op_mode == "postinc":
        base_register = f"a{_require_operand_reg(decoded_operand, inst)}"
        kind = "postincrement"
    elif op_mode == "predec":
        base_register = f"a{_require_operand_reg(decoded_operand, inst)}"
        kind = "predecrement"
    elif op_mode == "index":
        base_register = f"a{_require_operand_reg(decoded_operand, inst)}"
        displacement = _require_operand_value(decoded_operand, inst)
        operand_value = displacement
        if decoded_operand.memory_indirect:
            metadata = _full_index_metadata(decoded_operand, inst)
            kind = "memory_indirect_indexed"
        else:
            metadata = _index_metadata(decoded_operand, inst)
            kind = "indexed"
            custom = _hardware_relative_text(
                hunk_session, inst.offset, base_register, displacement, token, decoded_operand)
            if custom is not None:
                text, segment_addr = custom
                kind = "base_displacement_symbol"
                metadata = SymbolOperandMetadata(symbol=text.split("(", 1)[0])
    else:
        raise ValueError(
            f"Unsupported decoded operand mode {op_mode!r} in {_instruction_ref(inst)}")

    if (flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL)
            and operand_index == 0
            and branch_target is not None):
        segment_addr = branch_target
        operand_value = branch_target if operand_value is None else operand_value
        label = labels.get(branch_target)
        if label is not None and op_mode not in ("pcdisp", "pcindex"):
            text = label
        kind = "call_target" if flow_type == _FLOW_CALL else "branch_target"

    text = _apply_instruction_text_substitutions(
        text, inst.offset, hunk_session, include_arg_subs)
    return SemanticOperand(
        kind=kind,
        text=text,
            value=operand_value,
        register=register,
        base_register=base_register,
        displacement=displacement,
        segment_addr=segment_addr,
        metadata=metadata,
    )


def build_instruction_semantic_operands(
        inst: Instruction, hunk_session: HunkDisassemblySession,
        used_structs: set[str] | None = None,
        include_arg_subs: bool = True
) -> tuple[SemanticOperand, ...]:
    meta = decode_inst_for_emit(inst)
    specs = _decoded_operand_specs(inst, hunk_session, meta)
    nodes = list(inst.operand_nodes or ())
    tokens = _operand_text_slots(inst, len(specs))

    operands = tuple(
        (_simple_semantic_from_node(
            inst, nodes[idx], spec, idx,
            hunk_session, meta, used_structs, include_arg_subs,
        ) if idx < len(nodes) else None)
        or _build_decoded_semantic_operand(
            inst,
            token,
            spec,
            idx,
            hunk_session,
            meta,
            used_structs,
            include_arg_subs,
        )
        for idx, (token, spec) in enumerate(zip(tokens, specs, strict=True))
    )
    return _apply_field_value_domain_substitutions(operands, hunk_session)

