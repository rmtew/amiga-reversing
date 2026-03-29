"""Amiga OS library call identification.

Identifies OS library calls in analyzed M68K code by matching the
ExecBase load pattern and LVO dispatch pattern against the OS runtime KB.

All identification is data-driven from:
- runtime_os.py: exec_base_addr, lvo_index, calling_convention
- runtime_m68k.py/canonical instruction KB: ea_mode_encoding for addressing mode detection

Usage:
    from os_calls import identify_library_calls
    from m68k_kb import runtime_os
    os_kb = runtime_os
    calls = identify_library_calls(blocks, code, os_kb)
"""

from __future__ import annotations

import re
import struct
from collections.abc import Callable, Mapping
from dataclasses import dataclass, is_dataclass, replace
from enum import StrEnum
from types import SimpleNamespace
from typing import TYPE_CHECKING, Protocol

from disasm.target_metadata import (
    AppSlotRegionMetadata,
    CustomStructFieldMetadata,
    CustomStructMetadata,
    TargetMetadata,
)
from m68k_kb import runtime_m68k_analysis, runtime_m68k_decode, runtime_os
from m68k_kb.runtime_os import (
    OsConstant,
    OsInput,
    OsLibrary,
    OsMeta,
    OsOutput,
    OsValueDomain,
)

from .instruction_decode import (
    DecodedOperands,
    decode_inst_destination,
    decode_inst_operands,
    instruction_immediate_value,
    xf,
)
from .instruction_kb import find_kb_entry, instruction_flow, instruction_kb
from .instruction_primitives import Operand, extract_branch_target
from .memory_provenance import (
    MemoryRegionAddressSpace,
    MemoryRegionDerivationKind,
    MemoryRegionProvenance,
    field_pointer_source,
    provenance_base_displacement,
    provenance_field_pointer,
    provenance_named_base,
    require_base_displacement,
)
from .os_structs import OsStructLike, ResolvedStructField, resolve_struct_field
from .registers import parse_reg_name
from .strings import read_c_string_span, read_string_at
from .typing_protocols import CpuStateLike, MemoryLike

if TYPE_CHECKING:
    from .m68k_disasm import Instruction
    from .m68k_executor import (
        AbstractMemory,
        BasicBlock,
        CallSummary,
        CPUState,
        InstructionTrace,
    )


def _is_named_base_seed(name: str) -> bool:
    return name.endswith((".library", ".resource"))


def _read_named_base_seed(code: bytes, addr: int) -> str | None:
    name = read_string_at(code, addr)
    if name is None or not _is_named_base_seed(name):
        return None
    assert isinstance(name, str)
    return name


type ScratchReg = tuple[str, int]


def _decode_inst(inst: Instruction) -> tuple[str, DecodedOperands]:
    mnemonic = instruction_kb(inst)
    decoded = decode_inst_operands(inst, mnemonic)
    return mnemonic, decoded


def _reg_name(mode: str, reg: int) -> str:
    prefix = {"dn": "d", "an": "a"}.get(mode)
    if prefix is None:
        raise ValueError(f"Unsupported register mode {mode!r}")
    return f"{prefix}{reg}"


def _base_disp_operand(op: Operand | None, base_reg: int) -> int | None:
    if op is None or op.mode != "disp" or op.reg != base_reg:
        return None
    assert op.value is not None, "Displacement operand missing value"
    assert isinstance(op.value, int)
    return op.value


def _decoded_source_reg(decoded: DecodedOperands) -> str | None:
    src = decoded.ea_op
    if src is None or src.mode not in {"dn", "an"}:
        return None
    assert src.reg is not None, "Source register operand missing register number"
    return _reg_name(src.mode, src.reg)


def _decoded_dest_reg(decoded: DecodedOperands) -> str | None:
    dst = decoded.dst_op
    if dst is not None and dst.mode in {"dn", "an"}:
        assert dst.reg is not None, "Destination register operand missing register number"
        return _reg_name(dst.mode, dst.reg)
    reg_mode = decoded.reg_mode
    reg_num = decoded.reg_num
    if reg_mode in {"dn", "an"} and reg_num is not None:
        return _reg_name(reg_mode, reg_num)
    return None


def _address_reg_name(reg: int) -> str:
    return "sp" if reg == 7 else f"a{reg}"


# Sentinel addresses for abstract memory regions.
# These must not overlap with real hunk addresses (code is 0..64K range).
# SP sentinel: top of a virtual stack region.
# Memory allocation sentinels: auto-incrementing base addresses.
_SENTINEL_SP = 0x7F000000
_SENTINEL_ALLOC_BASE = 0x80000000
_SENTINEL_ALLOC_STEP = 0x00100000  # 1MB per allocation
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_OPAQUE_SEGMENT_REGION_STRUCT = "__segment_data__"


class AppMemoryDirection(StrEnum):
    FORWARD = "forward"
    BACKWARD = "backward"


class AppBaseKind(StrEnum):
    DYNAMIC = "dynamic"
    ABSOLUTE = "absolute"


class OsKb(Protocol):
    @property
    def META(self) -> OsMeta: ...

    @property
    def VALUE_DOMAINS(self) -> Mapping[str, OsValueDomain]: ...

    @property
    def API_INPUT_VALUE_DOMAINS(self) -> Mapping[str, Mapping[str, Mapping[str, str]]]: ...

    @property
    def STRUCT_FIELD_VALUE_DOMAINS(self) -> Mapping[str, Mapping[str | None, str]]: ...

    @property
    def STRUCTS(self) -> Mapping[str, OsStructLike]: ...

    @property
    def CONSTANTS(self) -> Mapping[str, OsConstant]: ...

    @property
    def LIBRARIES(self) -> Mapping[str, OsLibrary]: ...


@dataclass(frozen=True, slots=True)
class LibraryBaseTag:
    library_base: str
    os_type: str | None = None
    struct_name: str | None = None


@dataclass(frozen=True, slots=True)
class OsResultTag:
    os_type: str
    os_result: str
    call: str
    library: str


@dataclass(frozen=True, slots=True)
class BaseRegisterCallEffect:
    base_reg: str
    tag: LibraryBaseTag


@dataclass(frozen=True, slots=True)
class MemoryAllocationCallEffect:
    result_reg: str
    concrete: int


@dataclass(frozen=True, slots=True)
class OutputRegisterCallEffect:
    output_reg: str
    output_type: OsResultTag


CallEffect = BaseRegisterCallEffect | MemoryAllocationCallEffect | OutputRegisterCallEffect


@dataclass(frozen=True, slots=True)
class AppMemoryType:
    name: str
    function: str
    type: str | None
    library: str | None
    direction: AppMemoryDirection


@dataclass(frozen=True, slots=True)
class AppSlotNaming:
    offset: int
    candidates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AppSlotInfo:
    offset: int
    symbol: str
    usages: tuple[AppMemoryType, ...]
    struct: str | None = None
    size: int | None = None
    pointer_struct: str | None = None
    named_base: str | None = None


@dataclass(slots=True)
class _PendingCallInput:
    input: OsInput
    arg_reg: str
    tracked_reg: str
    complete: bool = False


RUNTIME_OS_KB: OsKb = runtime_os


def _validate_custom_struct(os_kb: OsKb,
                            custom_struct: CustomStructMetadata,
                            available_structs: set[str] | None = None) -> None:
    allowed_structs = set(os_kb.STRUCTS) if available_structs is None else available_structs
    if custom_struct.size < 0:
        raise ValueError(f"Custom struct {custom_struct.name} has negative size")
    if custom_struct.base_offset < 0 or custom_struct.base_offset > custom_struct.size:
        raise ValueError(
            f"Custom struct {custom_struct.name} has invalid base_offset {custom_struct.base_offset}")
    if custom_struct.base_struct is not None:
        if custom_struct.base_struct == custom_struct.name:
            raise ValueError(f"Custom struct {custom_struct.name} cannot inherit from itself")
        if custom_struct.base_struct not in allowed_structs:
            raise KeyError(
                f"Custom struct {custom_struct.name} references unknown base struct {custom_struct.base_struct}")
    for field in custom_struct.fields:
        if field.offset < 0 or field.size < 0 or field.offset + field.size > custom_struct.size:
            raise ValueError(
                f"Custom struct field {custom_struct.name}.{field.name} lies outside struct bounds")
        if field.struct is not None and field.struct not in allowed_structs:
            raise KeyError(
                f"Custom struct field {custom_struct.name}.{field.name} references unknown struct {field.struct}")
        if field.pointer_struct is not None and field.pointer_struct not in allowed_structs:
            raise KeyError(
                f"Custom struct field {custom_struct.name}.{field.name} references unknown pointer struct {field.pointer_struct}")


def _validate_app_slot_region(slot: AppSlotRegionMetadata, os_kb: OsKb) -> None:
    declared = int(slot.struct_name is not None) + int(slot.pointer_struct is not None)
    if declared != 1:
        raise ValueError(
            f"App slot offset {slot.offset} must declare exactly one of struct_name or pointer_struct")
    if slot.struct_name is not None and slot.struct_name not in os_kb.STRUCTS:
        raise KeyError(f"Unknown custom app slot struct {slot.struct_name}")
    if slot.pointer_struct is not None and slot.pointer_struct not in os_kb.STRUCTS:
        raise KeyError(f"Unknown custom app slot pointer struct {slot.pointer_struct}")


def build_target_local_os_kb(os_kb: OsKb,
                             target_metadata: TargetMetadata | None = None,
                             *,
                             extra_custom_structs: tuple[CustomStructMetadata, ...] = (),
                             named_base_struct_overrides: Mapping[str, str] | None = None,
                             ) -> OsKb:
    if target_metadata is None and not extra_custom_structs and not named_base_struct_overrides:
        return os_kb
    merged_structs = dict(os_kb.STRUCTS)
    target_struct_names = set(merged_structs)
    custom_structs = ()
    if target_metadata is not None:
        custom_structs = target_metadata.custom_structs
    all_custom_structs = custom_structs + extra_custom_structs
    target_struct_names.update(custom_struct.name for custom_struct in all_custom_structs)
    merged_kb = SimpleNamespace(
        META=os_kb.META,
        VALUE_DOMAINS=os_kb.VALUE_DOMAINS,
        API_INPUT_VALUE_DOMAINS=os_kb.API_INPUT_VALUE_DOMAINS,
        STRUCT_FIELD_VALUE_DOMAINS=os_kb.STRUCT_FIELD_VALUE_DOMAINS,
        STRUCTS=merged_structs,
        CONSTANTS=os_kb.CONSTANTS,
        LIBRARIES=os_kb.LIBRARIES,
    )
    for custom_struct in all_custom_structs:
        _validate_custom_struct(
            SimpleNamespace(STRUCTS=merged_structs),
            custom_struct,
            available_structs=target_struct_names,
        )
        existing = merged_structs.get(custom_struct.name)
        if existing is not None:
            if existing != custom_struct:
                raise ValueError(
                    f"Target metadata custom struct conflicts with existing struct {custom_struct.name}"
                )
            continue
        merged_structs[custom_struct.name] = custom_struct
    merged_named_base_structs = dict(os_kb.META.named_base_structs)
    if named_base_struct_overrides is not None:
        for named_base, struct_name in named_base_struct_overrides.items():
            if struct_name not in merged_structs:
                raise KeyError(
                    f"Named base override {named_base} references unknown struct {struct_name}"
                )
            merged_named_base_structs[named_base] = struct_name
    if merged_named_base_structs != os_kb.META.named_base_structs:
        meta = os_kb.META
        if is_dataclass(meta):
            merged_kb.META = replace(meta, named_base_structs=merged_named_base_structs)
        elif hasattr(meta, "__dict__"):
            merged_kb.META = SimpleNamespace(**{**meta.__dict__, "named_base_structs": merged_named_base_structs})
        else:
            raise TypeError("Unsupported META container for named_base_structs override")
    if target_metadata is not None:
        for slot in target_metadata.app_slot_regions:
            _validate_app_slot_region(slot, merged_kb)
    return merged_kb


def _sanitize_app_name(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', name.lower())


def _named_base_inferred_struct_name(named_base: str) -> str:
    stem = "".join(part.capitalize() for part in _sanitize_app_name(named_base).split("_") if part)
    return f"Inferred{stem}Base"


def _named_base_field_name_from_region(region: TypedMemoryRegion | None, fallback_offset: int) -> str:
    if region is not None:
        derivation = region.provenance.derivation
        if derivation is not None and derivation.kind is MemoryRegionDerivationKind.NAMED_BASE:
            named_base = derivation.named_base
            if named_base is not None:
                return f"{_sanitize_app_name(named_base)}_base"
        stem = _sanitize_app_name(region.struct)
        if stem:
            suffix = "base" if stem.endswith(("library", "device", "resource")) else "ptr"
            return f"{stem}_{suffix}"
    return f"field_{fallback_offset:04x}"


def _fixed_base_operand(op: Operand | None) -> tuple[str, int] | None:
    if op is None:
        return None
    if op.mode == "ind":
        assert op.reg is not None, "Indirect operand missing base register"
        return _address_reg_name(op.reg), 0
    if op.mode == "disp":
        assert op.reg is not None and op.value is not None, (
            "Displacement operand missing register or value")
        return _address_reg_name(op.reg), op.value
    if (
        op.mode == "index"
        and not op.memory_indirect
        and not op.base_suppressed
        and op.index_suppressed
    ):
        assert op.reg is not None, "Indexed operand missing base register"
        return _address_reg_name(op.reg), 0 if op.base_displacement is None else op.base_displacement
    return None


@dataclass(slots=True)
class _InferredNamedBaseField:
    offset: int
    size: int
    field_type: str
    name: str
    pointer_struct: str | None = None
    named_base: str | None = None


def _merge_inferred_named_base_field(
    existing: _InferredNamedBaseField | None,
    candidate: _InferredNamedBaseField,
) -> _InferredNamedBaseField:
    if existing is None:
        return candidate
    size = max(existing.size, candidate.size)
    pointer_struct = existing.pointer_struct or candidate.pointer_struct
    if (
        existing.pointer_struct is not None
        and candidate.pointer_struct is not None
        and existing.pointer_struct != candidate.pointer_struct
    ):
        pointer_struct = None
    named_base = existing.named_base or candidate.named_base
    if (
        existing.named_base is not None
        and candidate.named_base is not None
        and existing.named_base != candidate.named_base
    ):
        named_base = None
    field_type = existing.field_type if existing.size >= candidate.size else candidate.field_type
    if pointer_struct is not None:
        field_type = "APTR"
    name = existing.name
    if name.startswith("field_") and not candidate.name.startswith("field_"):
        name = candidate.name
    return _InferredNamedBaseField(
        offset=existing.offset,
        size=size,
        field_type=field_type,
        name=name,
        pointer_struct=pointer_struct,
        named_base=named_base,
    )


def infer_named_base_extension_structs(
    blocks: dict[int, BasicBlock],
    facts_by_inst: dict[int, dict[str, TypedMemoryRegion]],
    os_kb: OsKb,
) -> tuple[tuple[CustomStructMetadata, ...], dict[str, str]]:
    size_map = {"b": 1, "w": 2, "l": 4}
    inferred_fields: dict[str, dict[int, _InferredNamedBaseField]] = {}
    base_structs: dict[str, str] = {}
    for block in blocks.values():
        for inst in block.instructions:
            facts = facts_by_inst.get(inst.offset)
            if not facts:
                continue
            ikb, decoded = _decode_inst(inst)
            operand_size = inst.operand_size
            if operand_size is None:
                continue
            byte_size = size_map.get(operand_size)
            if byte_size is None:
                continue
            src_name = _decoded_source_reg(decoded)
            src_region = None if src_name is None else facts.get(src_name)
            for op, is_store in ((decoded.ea_op, False), (decoded.dst_op, True)):
                access = _fixed_base_operand(op)
                if access is None:
                    continue
                base_register, displacement = access
                base_region = facts.get(base_register)
                if base_region is None or _is_opaque_segment_region(base_region):
                    continue
                derivation = base_region.provenance.derivation
                if derivation is None or derivation.kind is not MemoryRegionDerivationKind.NAMED_BASE:
                    continue
                named_base = derivation.named_base
                if named_base is None:
                    continue
                field_offset = base_region.struct_offset + displacement
                if field_offset < 0:
                    continue
                known_field = resolve_struct_field(os_kb.STRUCTS, base_region.struct, field_offset)
                if known_field is not None:
                    continue
                base_structs.setdefault(named_base, base_region.struct)
                field_type = {1: "UBYTE", 2: "UWORD", 4: "ULONG"}[byte_size]
                pointer_struct = None
                pointer_named_base = None
                field_name = f"field_{field_offset:04x}"
                if is_store and byte_size == 4 and src_region is not None:
                    pointer_struct = src_region.struct
                    src_derivation = src_region.provenance.derivation
                    if (
                        src_derivation is not None
                        and src_derivation.kind is MemoryRegionDerivationKind.NAMED_BASE
                    ):
                        pointer_named_base = src_derivation.named_base
                    field_type = "APTR"
                    field_name = _named_base_field_name_from_region(src_region, field_offset)
                fields_for_base = inferred_fields.setdefault(named_base, {})
                candidate = _InferredNamedBaseField(
                    offset=field_offset,
                    size=byte_size,
                    field_type=field_type,
                    name=field_name,
                    pointer_struct=pointer_struct,
                    named_base=pointer_named_base,
                )
                fields_for_base[field_offset] = _merge_inferred_named_base_field(
                    fields_for_base.get(field_offset),
                    candidate,
                )
    custom_structs: list[CustomStructMetadata] = []
    named_base_overrides: dict[str, str] = {}
    for named_base, fields_by_offset in sorted(inferred_fields.items()):
        if not fields_by_offset:
            continue
        base_struct = base_structs[named_base]
        base_struct_def = os_kb.STRUCTS[base_struct]
        seen_names: set[str] = set()
        rendered_fields: list[CustomStructFieldMetadata] = []
        for offset, field in sorted(fields_by_offset.items()):
            field_name = field.name
            if field_name in seen_names:
                field_name = f"{field_name}_{offset:04x}"
            seen_names.add(field_name)
            rendered_fields.append(
                    CustomStructFieldMetadata(
                        name=field_name,
                        type=field.field_type,
                        offset=offset,
                        size=field.size,
                        pointer_struct=field.pointer_struct,
                        named_base=field.named_base,
                    )
                )
        struct_size = max(
            base_struct_def.size,
            max(field.offset + field.size for field in rendered_fields),
        )
        struct_name = _named_base_inferred_struct_name(named_base)
        custom_structs.append(
            CustomStructMetadata(
                name=struct_name,
                size=struct_size,
                fields=tuple(rendered_fields),
                seed_origin="manual_analysis",
                review_status="seeded",
                citation=f"Inferred from typed named-base accesses for {named_base}",
                source="target_metadata",
                base_offset=base_struct_def.size,
                base_struct=base_struct,
            )
        )
        named_base_overrides[named_base] = struct_name
    return tuple(custom_structs), named_base_overrides


def _refined_named_base_struct(os_kb: OsKb,
                               named_base: str | None,
                               generic_struct: str | None) -> str | None:
    if named_base is None or generic_struct is None:
        return generic_struct
    specific_struct = os_kb.META.named_base_structs.get(named_base)
    if specific_struct is None:
        raise KeyError(
            f"Named base {named_base} is missing a KB struct mapping "
            f"(generic struct was {generic_struct})")
    assert isinstance(specific_struct, str)
    if specific_struct not in os_kb.STRUCTS:
        raise KeyError(
            f"Named base {named_base} maps to unknown struct {specific_struct}")
    return specific_struct


def app_memory_type_priority(info: AppMemoryType) -> int:
    return 0 if info.direction is AppMemoryDirection.BACKWARD else 1


def select_primary_app_memory_type(usages: tuple[AppMemoryType, ...]) -> AppMemoryType:
    if not usages:
        assert usages, "App memory type usages cannot be empty"
    ranked = sorted(enumerate(usages), key=lambda item: (app_memory_type_priority(item[1]), item[0]))
    return ranked[0][1]


def _app_slot_usage_symbol(info: AppMemoryType) -> str:
    return _sanitize_app_name(f"app_{info.function}_{info.name}")


def _app_slot_usage_suffix(infos: tuple[AppMemoryType, ...]) -> str | None:
    ranked = sorted(enumerate(infos), key=lambda item: (app_memory_type_priority(item[1]), item[0]))
    names: list[str] = []
    for _, info in ranked:
        suffix = _sanitize_app_name(info.name)
        if suffix not in names:
            names.append(suffix)
    if len(names) != 1:
        return None
    if names[0] in {"library", "resource", "device", "base"}:
        return "base"
    return names[0]


def _ordered_app_slot_symbols(infos: tuple[AppMemoryType, ...]) -> tuple[str, ...]:
    ranked = sorted(enumerate(infos), key=lambda item: (app_memory_type_priority(item[1]), item[0]))
    ordered: list[str] = []
    for _, info in ranked:
        sym = _app_slot_usage_symbol(info)
        if sym not in ordered:
            ordered.append(sym)
    if not ordered:
        assert ordered, "App slot usage candidates cannot be empty"
    return tuple(ordered)


def _app_slot_naming(*, offset: int, infos: tuple[AppMemoryType, ...], named_base: str | None) -> AppSlotNaming:
    if named_base is not None:
        base_sym = _sanitize_app_name(named_base)
        suffix = _app_slot_usage_suffix(infos)
        if suffix is None:
            return AppSlotNaming(offset=offset, candidates=(f"app_{base_sym}_base",))
        return AppSlotNaming(offset=offset, candidates=(f"app_{base_sym}_{suffix}",))
    return AppSlotNaming(offset=offset, candidates=_ordered_app_slot_symbols(infos))


def _choose_app_slot_symbol(naming: AppSlotNaming, grouped_candidates: dict[str, list[int]]) -> str:
    for sym in naming.candidates:
        if len(grouped_candidates[sym]) == 1:
            return sym
    return naming.candidates[0]


def _segment_label_disambiguator(address: int) -> str:
    return f"{address:04X}" if address <= 0xFFFF else f"{address:08X}"


def _segment_seed_addr(op: Operand | None, code_size: int, base_addr: int = 0) -> int | None:
    if op is None or op.value is None:
        return None
    target: int
    if op.mode == "pcdisp":
        target = op.value
    elif op.mode == "absw":
        target = op.value & 0xFFFF
    elif op.mode == "absl":
        target = op.value
    elif op.mode == "imm":
        target = op.value & 0xFFFFFFFF
    else:
        return None
    if base_addr <= target < base_addr + code_size:
        return target
    return None


def _call_input_symbol(call: LibraryCall, inp: OsInput) -> str:
    return f"{_sanitize_app_name(call.function)}_{_sanitize_app_name(inp.name)}"


def _finalize_segment_symbols(symbol_candidates: dict[int, set[str]]) -> dict[int, str]:
    resolved: dict[int, str] = {}
    grouped_symbols: dict[str, list[int]] = {}
    for address, symbols in symbol_candidates.items():
        if len(symbols) != 1:
            raise ValueError(
                f"Conflicting typed segment names for ${address:08X}: {sorted(symbols)}")
        symbol = next(iter(symbols))
        grouped_symbols.setdefault(symbol, []).append(address)
    for symbol, addrs in grouped_symbols.items():
        if len(addrs) == 1:
            resolved[addrs[0]] = symbol
            continue
        for address in sorted(addrs):
            resolved[address] = f"{symbol}_{_segment_label_disambiguator(address)}"
    return resolved


def _trace_segment_seed(block: BasicBlock,
                        call_addr: int,
                        reg_name: str,
                        code: bytes,
                        *,
                        base_addr: int = 0) -> tuple[int, int] | None:
    call_idx = None
    for i, inst in enumerate(block.instructions):
        if inst.offset == call_addr:
            call_idx = i
            break
    if call_idx is None:
        return None
    tracked_reg = reg_name
    for i in range(call_idx - 1, -1, -1):
        inst = block.instructions[i]
        ikb, decoded = _decode_inst(inst)
        dst = decode_inst_destination(inst, ikb)
        dst_name = None if dst is None else _reg_name(dst[0], dst[1])
        if dst_name != tracked_reg:
            continue
        op_type = None if ikb is None else runtime_m68k_analysis.OPERATION_TYPES.get(ikb)
        if op_type == runtime_m68k_analysis.OperationType.MOVE or ikb == "MOVEA":
            src_name = _decoded_source_reg(decoded)
            if src_name is not None:
                tracked_reg = src_name
                continue
            address = _segment_seed_addr(decoded.ea_op, len(code), base_addr=base_addr)
            if address is not None:
                return inst.offset, address
        return None
    return None


@dataclass(frozen=True, slots=True)
class LeadingWordPointerWrapper:
    source_reg: str
    payload_reg: str
    payload_offset: int
    consumed_word_args: tuple[str, ...]


def _parse_movem_registers(text: str) -> tuple[str, ...]:
    regs: list[str] = []
    for part in text.lower().split("/"):
        item = part.strip()
        if not item:
            continue
        match = re.fullmatch(r"([da])([0-7])-([da])([0-7])", item)
        if match:
            start_kind, start_idx, end_kind, end_idx = match.groups()
            if start_kind != end_kind:
                raise ValueError(f"Mixed MOVEM register range {text!r}")
            start = int(start_idx)
            end = int(end_idx)
            step = 1 if start <= end else -1
            for reg in range(start, end + step, step):
                regs.append(f"{start_kind}{reg}")
            continue
        match = re.fullmatch(r"([da])([0-7])", item)
        if match:
            kind, idx = match.groups()
            regs.append(f"{kind}{idx}")
    return tuple(regs)


def _leading_word_pointer_wrapper(call: LibraryCall,
                                  block: BasicBlock,
                                  call_addr: int) -> LeadingWordPointerWrapper | None:
    call_idx = None
    for i, inst in enumerate(block.instructions):
        if inst.offset == call_addr:
            call_idx = i
            break
    if call_idx is None:
        return None
    reg_to_input = {
        reg.lower(): inp
        for inp in call.inputs
        for reg in _input_regs(inp)
    }
    movem_regs: tuple[str, ...] | None = None
    source_reg: str | None = None
    reg_sources: dict[str, int] = {}
    payload_reg: str | None = None
    for inst in block.instructions[:call_idx]:
        ikb, decoded = _decode_inst(inst)
        if ikb == "MOVEM" and inst.operand_size == "w":
            op = decoded.ea_op
            if op is None or op.mode != "postinc" or op.reg is None:
                continue
            operand_texts = inst.operand_texts or ()
            parsed_regs: tuple[str, ...] = ()
            for text in operand_texts:
                regs = _parse_movem_registers(text)
                if regs:
                    parsed_regs = regs
                    break
            if not parsed_regs or any(not reg.startswith("d") for reg in parsed_regs):
                continue
            source_reg = _address_reg_name(op.reg)
            movem_regs = parsed_regs
            reg_sources = {reg: index for index, reg in enumerate(parsed_regs)}
            continue
        if movem_regs is None:
            continue
        if ikb == "EXG":
            operand_texts = inst.operand_texts or ()
            src_name = operand_texts[0].lower() if len(operand_texts) >= 1 else None
            dst_name = operand_texts[1].lower() if len(operand_texts) >= 2 else None
            if src_name in reg_sources and dst_name in reg_sources:
                reg_sources[src_name], reg_sources[dst_name] = reg_sources[dst_name], reg_sources[src_name]
            continue
        if ikb == "MOVEA":
            src_name = _decoded_source_reg(decoded)
            dst = decode_inst_destination(inst, ikb)
            dst_name = None if dst is None else _reg_name(dst[0], dst[1])
            if src_name == source_reg and dst_name is not None:
                payload_reg = dst_name
    if source_reg is None or movem_regs is None or payload_reg is None:
        return None
    assert movem_regs is not None
    payload_input = reg_to_input.get(payload_reg)
    if payload_input is None:
        return None
    consumed_word_args = [""] * len(movem_regs)
    for reg_name, source_index in reg_sources.items():
        inp = reg_to_input.get(reg_name)
        if inp is None:
            continue
        consumed_word_args[source_index] = f"{call.function}.{inp.name}"
    return LeadingWordPointerWrapper(
        source_reg=source_reg,
        payload_reg=payload_reg,
        payload_offset=len(movem_regs) * 2,
        consumed_word_args=tuple(consumed_word_args),
    )


def _apply_leading_word_wrapper_segment_seeds(blocks: dict[int, BasicBlock],
                                              lib_calls: list[LibraryCall],
                                              code: bytes,
                                              *,
                                              base_addr: int = 0,
                                              arg_annotations: dict[int, CallArgumentAnnotation],
                                              segment_data_name_candidates: dict[int, set[str]],
                                              segment_struct_candidates: dict[int, set[str]],
                                              typed_data_sizes: dict[int, int],
                                              typed_data_comments: dict[int, str],
                                              typed_data_fields: dict[int, tuple[str, str, str | None]],
                                              os_kb: OsKb) -> None:
    code_ranges = tuple(
        (inst.offset, inst.offset + inst.size)
        for block in blocks.values()
        for inst in block.instructions
    )

    def overlaps_code(addr: int, size: int) -> bool:
        return any(addr < stop and start < addr + size for start, stop in code_ranges)

    for call in lib_calls:
        wrapper_block = blocks.get(call.block)
        if wrapper_block is None:
            continue
        wrapper_entry = call.block
        wrapper = _leading_word_pointer_wrapper(call, wrapper_block, call.addr)
        if wrapper is None:
            continue
        payload_input = next(
            (inp for inp in call.inputs if wrapper.payload_reg in tuple(reg.lower() for reg in _input_regs(inp))),
            None,
        )
        for block in blocks.values():
            for xref in block.xrefs:
                if xref.type != "call" or xref.dst != wrapper_entry:
                    continue
                traced = _trace_segment_seed(block, xref.src, wrapper.source_reg, code, base_addr=base_addr)
                if traced is None:
                    continue
                seed_offset, source_addr = traced
                if payload_input is not None:
                    arg_annotations[seed_offset] = CallArgumentAnnotation(
                        arg_name=payload_input.name,
                        arg_reg=wrapper.source_reg.upper(),
                        function=call.function,
                        library=call.library,
                    )
                for index, comment in enumerate(wrapper.consumed_word_args):
                    if not comment:
                        continue
                    addr = source_addr + (index * 2)
                    if overlaps_code(addr, 2):
                        continue
                    typed_data_sizes[addr] = 2
                    typed_data_comments[addr] = comment
                if payload_input is not None and payload_input.i_struct is not None:
                    payload_addr = source_addr + wrapper.payload_offset
                    if not overlaps_code(payload_addr, 4):
                        segment_struct_candidates.setdefault(payload_addr, set()).add(payload_input.i_struct)
                        _apply_segment_struct_typed_overlay(
                            address=payload_addr,
                            struct_name=payload_input.i_struct,
                            os_kb=os_kb,
                            typed_data_sizes=typed_data_sizes,
                            typed_data_comments=typed_data_comments,
                            typed_data_fields=typed_data_fields,
                        )


def _leading_word_wrapper_seed_regions(blocks: dict[int, BasicBlock],
                                       lib_calls: list[LibraryCall],
                                       code: bytes,
                                       *,
                                       base_addr: int = 0) -> dict[int, dict[str, RegisterFact]]:
    seed_regions: dict[int, dict[str, RegisterFact]] = {}
    code_size = len(code)
    for call in lib_calls:
        wrapper_block = blocks.get(call.block)
        if wrapper_block is None:
            continue
        wrapper = _leading_word_pointer_wrapper(call, wrapper_block, call.addr)
        if wrapper is None:
            continue
        wrapper_entry = call.block
        for block in blocks.values():
            for xref in block.xrefs:
                if xref.type != "call" or xref.dst != wrapper_entry:
                    continue
                traced = _trace_segment_seed(block, xref.src, wrapper.source_reg, code, base_addr=base_addr)
                if traced is None:
                    continue
                _seed_offset, source_addr = traced
                seed_regions.setdefault(xref.src, {})[wrapper.source_reg] = RegisterFact(
                    region=_segment_data_region(source_addr, code_size),
                )
    return seed_regions


def _augment_region_summaries_with_leading_word_wrapper(
        blocks: dict[int, BasicBlock],
        lib_calls: list[LibraryCall],
        summaries: dict[int, RegionSummary],
) -> dict[int, RegionSummary]:
    result = dict(summaries)
    for call in lib_calls:
        block = blocks.get(call.block)
        if block is None:
            continue
        wrapper = _leading_word_pointer_wrapper(call, block, call.addr)
        if wrapper is None:
            continue
        summary = result.get(call.block, RegionSummary())
        produced = tuple(
            (reg_name, region)
            for reg_name, region in summary.produced
            if reg_name != wrapper.payload_reg
        )
        transfers = list(summary.region_offset_transfers)
        transfer = RegionOffsetTransfer(
            dst_reg=wrapper.payload_reg,
            src_reg=wrapper.source_reg,
            offset=wrapper.payload_offset,
        )
        if transfer not in transfers:
            transfers.append(transfer)
        result[call.block] = RegionSummary(
            produced=produced,
            field_pointer_transfers=summary.field_pointer_transfers,
            region_offset_transfers=tuple(transfers),
        )
    return result


def _apply_segment_struct_typed_overlay(*,
                                        address: int,
                                        struct_name: str,
                                        os_kb: OsKb,
                                        typed_data_sizes: dict[int, int],
                                        typed_data_comments: dict[int, str],
                                        typed_data_fields: dict[int, tuple[str, str, str | None]],
                                        context_name: str | None = None) -> None:
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        struct_def = os_kb.STRUCTS.get(name)
        if struct_def is None:
            return
        if struct_def.base_struct is not None:
            visit(struct_def.base_struct)
        for field in struct_def.fields:
            if field.size <= 0:
                continue
            field_addr = address + field.offset
            typed_data_sizes.setdefault(field_addr, field.size)
            typed_data_comments.setdefault(field_addr, f"{name}.{field.name}")
            typed_data_fields.setdefault(field_addr, (name, field.name, context_name))

    visit(struct_name)


def _absolute_app_slot_addr(base_info: AppBaseInfo, offset: int) -> int:
    assert base_info.kind == AppBaseKind.ABSOLUTE, (
        "Absolute app slot address requires absolute app base")
    return (base_info.concrete + offset) & 0xFFFFFFFF


def _app_slot_offset_from_absolute_addr(base_info: AppBaseInfo, addr: int) -> int | None:
    offset = addr - base_info.concrete
    if base_info.kind == AppBaseKind.DYNAMIC:
        base_is_sentinel = base_info.concrete >= _SENTINEL_ALLOC_BASE
        addr_is_sentinel = addr >= _SENTINEL_ALLOC_BASE
        if base_is_sentinel != addr_is_sentinel:
            return None
        if offset < 0 or offset > 0xFFFF:
            return None
        return offset
    if base_info.kind == AppBaseKind.ABSOLUTE:
        if offset < -0x8000 or offset > 0x7FFF:
            return None
        return offset
    raise ValueError(f"Unsupported app base kind {base_info.kind!r}")


def _app_slot_disambiguator(base_info: AppBaseInfo | None, offset: int) -> str:
    if base_info is not None and base_info.kind == AppBaseKind.ABSOLUTE:
        addr = _absolute_app_slot_addr(base_info, offset)
        width = 4 if addr <= 0xFFFF else 8
        return f"{addr:0{width}X}"
    return f"{offset:04X}"


@dataclass(frozen=True, slots=True)
class CallArgumentAnnotation:
    arg_name: str
    arg_reg: str
    function: str
    library: str | None


@dataclass(frozen=True, slots=True)
class CallSetupAnalysis:
    arg_annotations: dict[int, CallArgumentAnnotation]
    segment_data_symbols: dict[int, str]
    segment_struct_regions: dict[int, str]
    typed_data_sizes: dict[int, int]
    typed_data_comments: dict[int, str]
    typed_data_fields: dict[int, tuple[str, str, str | None]]
    segment_code_symbols: dict[int, str]
    code_entry_points: tuple[int, ...]
    string_ranges: dict[int, int]


@dataclass(frozen=True, slots=True)
class TypedMemoryRegion:
    struct: str
    size: int
    provenance: MemoryRegionProvenance
    struct_offset: int = 0
    context_name: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterFact:
    region: TypedMemoryRegion | None = None
    concrete: int | None = None


@dataclass(frozen=True, slots=True)
class AppBaseInfo:
    kind: AppBaseKind
    reg_num: int
    concrete: int


@dataclass(frozen=True, slots=True)
class FieldPointerTransfer:
    dst_reg: str
    src_reg: str
    displacement: int


@dataclass(frozen=True, slots=True)
class RegionOffsetTransfer:
    dst_reg: str
    src_reg: str
    offset: int


@dataclass(frozen=True, slots=True)
class RegionSummary:
    produced: tuple[tuple[str, TypedMemoryRegion], ...] = ()
    field_pointer_transfers: tuple[FieldPointerTransfer, ...] = ()
    region_offset_transfers: tuple[RegionOffsetTransfer, ...] = ()


@dataclass(slots=True)
class PlatformState:
    scratch_regs: tuple[ScratchReg, ...]
    exec_base_addr: int
    exec_base_library: str
    exec_base_tag: LibraryBaseTag
    base_reg: str
    return_reg: str
    initial_sp: int
    base_reg_num: int
    next_alloc_sentinel: int
    os_call_resolver: Callable[..., CallEffect | None] | None
    app_base: AppBaseInfo | None = None
    initial_register_regions: dict[str, TypedMemoryRegion] | None = None
    initial_register_tags: dict[str, object] | None = None
    entry_register_regions: dict[int, dict[str, TypedMemoryRegion]] | None = None
    initial_mem: AbstractMemory | None = None
    pending_call_effect: CallEffect | None = None
    summary_cache: dict[int, CallSummary | None] | None = None

    def app_base_register_name(self) -> str | None:
        if self.app_base is None:
            return None
        return _address_reg_name(self.app_base.reg_num)


@dataclass(frozen=True, slots=True)
class LibraryCall:
    addr: int
    block: int
    library: str
    function: str
    lvo: int
    owner_sub: int = -1
    inputs: tuple[OsInput, ...] = ()
    output: OsOutput | None = None
    no_return: bool = False
    dispatch: int | None = None
    os_since: str | None = None
    fd_version: str | None = None


def get_platform_config() -> PlatformState:
    """Build executor platform state from the OS KB."""
    meta = RUNTIME_OS_KB.META
    cc = meta.calling_convention

    scratch = tuple(parse_reg_name(r) for r in cc.scratch_regs)

    base_reg_name = cc.base_reg.upper()
    if not base_reg_name.startswith("A"):
        raise ValueError(f"calling_convention.base_reg must be An, got {base_reg_name}")
    base_reg_num = int(base_reg_name[1])
    exec_lib = meta.exec_base_addr.library

    return PlatformState(
        scratch_regs=scratch,
        exec_base_addr=meta.exec_base_addr.address,
        exec_base_library=exec_lib,
        exec_base_tag=LibraryBaseTag(library_base=exec_lib),
        base_reg=cc.base_reg,
        return_reg=cc.return_reg,
        initial_sp=_SENTINEL_SP,
        base_reg_num=base_reg_num,
        next_alloc_sentinel=_SENTINEL_ALLOC_BASE,
        os_call_resolver=lambda offset, lvo, lib, cpu, code, platform=None:
            resolve_call_effects(offset, lvo, lib, cpu, code, platform=platform),
    )


def resolve_call_effects(inst_offset: int, lvo: int, a6_lib: str | None,
                         cpu_state: CpuStateLike, code: bytes,
                         os_kb: OsKb | None = None,
                         platform: PlatformState | None = None) -> CallEffect | None:
    """Determine the effects of a library call on register state.

    Handles three KB fields, in priority order:
    - `returns_base` (OpenLibrary etc.): tags result register as library base
    - `returns_memory` (AllocMem etc.): assigns sentinel concrete value to
      result register, enabling base-relative memory tracking
    - `output` (all typed functions): tags result register with OS type

    Returns dict with one of:
        {"base_reg": "D0", "tag": {"library_base": "dos.library"}}
        {"result_reg": "D0", "concrete": 0x80000000}
        {"output_reg": "D0", "output_type": {"os_type": "void *", ...}}
    or None if no effect can be determined.
    """
    if os_kb is None:
        os_kb = RUNTIME_OS_KB

    if a6_lib is None:
        return None

    lib_data = os_kb.LIBRARIES.get(a6_lib)
    if lib_data is None:
        return None

    lvo_index = lib_data.lvo_index
    func_name = lvo_index.get(str(lvo))
    if func_name is None:
        return None

    func = lib_data.functions[func_name]

    # Check returns_base first (OpenLibrary, OpenResource)
    rb = func.returns_base
    if rb is not None:
        mode, num = parse_reg_name(rb.name_reg)
        reg_val = cpu_state.get_reg(mode, num)
        if reg_val.is_known:
            lib_name = _read_named_base_seed(code, reg_val.concrete)
            if lib_name:
                output = func.output
                return BaseRegisterCallEffect(
                    base_reg=rb.base_reg,
                    tag=LibraryBaseTag(
                        library_base=lib_name,
                        os_type=None if output is None else output.type,
                        struct_name=None if output is None else output.i_struct,
                    ),
                )

    # Check returns_memory (AllocMem, AllocVec, etc.)
    rm = func.returns_memory
    if rm is not None and platform is not None:
        sentinel = platform.next_alloc_sentinel
        platform.next_alloc_sentinel = sentinel + _SENTINEL_ALLOC_STEP
        return MemoryAllocationCallEffect(
            result_reg=rm.result_reg,
            concrete=sentinel,
        )

    # Generic output type tag from KB
    output = func.output
    if output is not None and output.reg and output.type:
        return OutputRegisterCallEffect(
            output_reg=output.reg,
            output_type=OsResultTag(
                os_type=output.type,
                os_result=output.name,
                call=func_name,
                library=a6_lib,
            ),
        )

    return None


# -- Return value store tracing ---------------------------------------

def trace_return_stores(blocks: dict[int, BasicBlock],
                        lib_calls: list[LibraryCall],
                        base_reg: int) -> dict[int, AppMemoryType]:
    """Trace return value stores to app memory after library calls.

    For each lib_call with an output field, scans the fallthrough block
    for stores of the return register to d(base_reg).  Returns a map
    of app memory offsets to the function/field that produced the value.

    Returns: {offset: {"function": "Output", "name": "file", ...}}
    """
    result = {}

    for call in lib_calls:
        output = call.output
        if output is None or output.reg is None:
            continue

        ret_reg = output.reg.lower()
        call_addr = call.addr

        # Find the block containing the call
        block = blocks.get(call.block)
        if not block:
            continue

        # Scan for store of ret_reg to d(base_reg) in instructions
        # after the call.  The call may end the block, so also check
        # the fallthrough block.
        ret_key = ("dn" if ret_reg[0] == "d" else "an", int(ret_reg[1]))
        store_info = AppMemoryType(
            function=call.function,
            name=output.name,
            type=output.type,
            library=call.library,
            direction=AppMemoryDirection.FORWARD,
        )

        def _scan_for_store(
            instructions: list[Instruction],
            *,
            _ret_reg: str = ret_reg,
            _ret_key: tuple[str, int] = ret_key,
        ) -> int | None:
            """Scan instructions for ret_reg -> d(base_reg). Returns offset or None."""
            for inst in instructions:
                ikb, decoded = _decode_inst(inst)
                if (
                    ikb
                    and runtime_m68k_analysis.OPERATION_TYPES.get(ikb) == runtime_m68k_analysis.OperationType.MOVE
                    and _decoded_source_reg(decoded) == _ret_reg
                    and (offset := _base_disp_operand(decoded.dst_op, base_reg)) is not None
                ):
                    return offset
                # Stop if ret_reg is overwritten
                dst = decode_inst_destination(inst, ikb)
                if dst == _ret_key:
                    return None
            return None

        # Instructions after the call in the same block
        past_call = False
        after_call: list[Instruction] = []
        for inst in block.instructions:
            if past_call:
                after_call.append(inst)
            if inst.offset == call_addr:
                past_call = True

        offset = _scan_for_store(after_call)
        if offset is None:
            # Check fallthrough block
            for xref in block.xrefs:
                if xref.type == "fallthrough":
                    ft_block = blocks.get(xref.dst)
                    if ft_block:
                        offset = _scan_for_store(ft_block.instructions)
                    break

        if offset is not None:
            result[offset] = store_info

    return result


def collect_app_memory_type_usages(blocks: dict[int, BasicBlock],
                                   lib_calls: list[LibraryCall],
                                   base_reg: int) -> dict[int, tuple[AppMemoryType, ...]]:
    """Collect all typed app memory slot usages from library call data flow.

    Combines forward propagation (return values -> register copies -> 
    app memory stores) with backward propagation (call inputs <- app
    memory loads).  Handles cross-subroutine flow: sub A stores Output()
    result to d(A6), sub B loads it for Write(file=D1).

    Returns: {app_offset: (AppMemoryType, ...)}
    """
    result: dict[int, list[AppMemoryType]] = {}

    def _record(offset: int, info: AppMemoryType) -> None:
        entries = result.setdefault(offset, [])
        if info not in entries:
            entries.append(info)

    def _trace_reg_forward(instructions: list[Instruction], src_reg: str, info: AppMemoryType) -> None:
        """Trace src_reg through copies and stores to d(base_reg).

        Follows move/movea chains: if src_reg is copied to another
        register, continues tracing the copy.  Stops when src_reg
        (or its copy) is stored to d(base_reg) or overwritten.
        """
        tracked: set[str] = {src_reg}  # set of registers carrying the value
        for inst in instructions:
            copied_to = None  # register added by copy in this instruction
            ikb, decoded = _decode_inst(inst)

            # Check for store to d(base_reg) from any tracked register
            if ikb and runtime_m68k_analysis.OPERATION_TYPES.get(ikb) == runtime_m68k_analysis.OperationType.MOVE:
                src_name = _decoded_source_reg(decoded)
                if src_name in tracked:
                    offset = _base_disp_operand(decoded.dst_op, base_reg)
                    if offset is not None:
                        _record(offset, info)
                        return

                    copied_to = _decoded_dest_reg(decoded)
                    if copied_to is not None:
                        tracked.add(copied_to)

            # Check if any tracked register is overwritten
            # (skip the register we just added via copy)
            dst = decode_inst_destination(inst, ikb)
            if dst:
                dst_name = _reg_name(dst[0], dst[1])
                if dst_name in tracked and dst_name != copied_to:
                    tracked.discard(dst_name)
                    if not tracked:
                        return

    # Forward: trace return values to app memory stores
    for call in lib_calls:
        output = call.output
        if output is None or output.reg is None:
            continue
        ret_reg = output.reg.lower()
        call_addr = call.addr
        info = AppMemoryType(
            function=call.function,
            name=output.name,
            type=output.type,
            library=call.library,
            direction=AppMemoryDirection.FORWARD,
        )

        block = blocks.get(call.block)
        if not block:
            continue

        # Collect instructions after the call
        past_call = False
        after_call = []
        for inst in block.instructions:
            if past_call:
                after_call.append(inst)
            if inst.offset == call_addr:
                past_call = True

        # Trace in same block
        _trace_reg_forward(after_call, ret_reg, info)

        # Trace in fallthrough block
        for xref in block.xrefs:
            if xref.type == "fallthrough":
                ft_block = blocks.get(xref.dst)
                if ft_block:
                    _trace_reg_forward(ft_block.instructions, ret_reg, info)
                    # Also follow fallthrough's fallthrough (conditional blocks)
                    for xref2 in ft_block.xrefs:
                        if xref2.type in ("fallthrough", "branch"):
                            ft2 = blocks.get(xref2.dst)
                            if ft2:
                                _trace_reg_forward(
                                    ft2.instructions, ret_reg, info)
                break

    # Backward: trace call inputs to app memory loads
    for call in lib_calls:
        inputs = call.inputs
        if not inputs:
            continue

        block = blocks.get(call.block)
        if not block or not block.instructions:
            continue

        call_idx = None
        for i, inst in enumerate(block.instructions):
            if inst.offset == call.addr:
                call_idx = i
                break
        if call_idx is None:
            continue

        for inp in inputs:
            for reg in _input_regs(inp):
                reg_name = reg.lower()
                # Walk backward to find where this register was loaded
                for i in range(call_idx - 1, -1, -1):
                    inst = block.instructions[i]
                    ikb, decoded = _decode_inst(inst)

                    # Check if this instruction writes to the arg register
                    dst = decode_inst_destination(inst, ikb)
                    if not dst:
                        continue
                    mode_str = "dn" if reg_name[0] == "d" else "an"
                    reg_num = int(reg_name[1])
                    if dst != (mode_str, reg_num):
                        continue

                    # Found the setter. Check if source is d(base_reg)
                    offset = _base_disp_operand(decoded.ea_op, base_reg)
                    if offset is not None:
                        _record(offset, AppMemoryType(
                            name=inp.name,
                            function=call.function,
                            type=inp.type,
                            library=call.library,
                            direction=AppMemoryDirection.BACKWARD,
                        ))
                    break
    return {offset: tuple(entries) for offset, entries in result.items()}


# -- Unified app memory type map ---------------------------------------

def build_app_memory_types(blocks: dict[int, BasicBlock],
                           lib_calls: list[LibraryCall],
                           base_reg: int) -> dict[int, AppMemoryType]:
    """Build a primary type map for app memory slots from library call data flow."""
    usages = collect_app_memory_type_usages(blocks, lib_calls, base_reg)
    return {
        offset: select_primary_app_memory_type(entries)
        for offset, entries in usages.items()
    }


# -- Call argument annotation -----------------------------------------

def analyze_call_setups(blocks: dict[int, BasicBlock],
                        lib_calls: list[LibraryCall],
                        os_kb: OsKb,
                        code: bytes,
                        platform: PlatformState | None = None,
                        base_addr: int = 0,
                        include_data_labels: bool = True) -> CallSetupAnalysis:
    """Analyze library call setup instructions once for comments and typed labels."""
    arg_annotations: dict[int, CallArgumentAnnotation] = {}
    segment_data_name_candidates: dict[int, set[str]] = {}
    segment_struct_candidates: dict[int, set[str]] = {}
    typed_data_sizes: dict[int, int] = {}
    typed_data_comments: dict[int, str] = {}
    typed_data_fields: dict[int, tuple[str, str, str | None]] = {}
    segment_code_name_candidates: dict[int, set[str]] = {}
    string_ranges: dict[int, int] = {}
    code_addrs = {
        addr
        for block in blocks.values()
        for inst in block.instructions
        for addr in range(inst.offset, inst.offset + inst.size)
    }

    for call in lib_calls:
        if not call.inputs:
            continue
        block = blocks.get(call.block)
        if not block or not block.instructions:
            continue

        call_idx = None
        for i, inst in enumerate(block.instructions):
            if inst.offset == call.addr:
                call_idx = i
                break
        if call_idx is None:
            continue

        pending: list[_PendingCallInput] = []
        for inp in call.inputs:
            for reg_name in (reg.lower() for reg in _input_regs(inp)):
                pending.append(
                    _PendingCallInput(
                        input=inp,
                        arg_reg=_input_reg_display(inp),
                        tracked_reg=reg_name,
                    )
                )

        for i in range(call_idx - 1, -1, -1):
            if all(state.complete for state in pending):
                break
            inst = block.instructions[i]
            ikb, decoded = _decode_inst(inst)
            dst = decode_inst_destination(inst, ikb)
            dst_name = None if dst is None else _reg_name(dst[0], dst[1])
            if dst_name is None:
                continue

            for state in pending:
                if state.complete:
                    continue
                tracked_reg = state.tracked_reg
                if dst_name != tracked_reg:
                    continue
                inp = state.input
                arg_annotations[inst.offset] = CallArgumentAnnotation(
                    arg_name=inp.name,
                    arg_reg=_input_reg_display(inp),
                    function=call.function,
                    library=call.library,
                )
                op_type = None if ikb is None else runtime_m68k_analysis.OPERATION_TYPES.get(ikb)
                if op_type == runtime_m68k_analysis.OperationType.MOVE:
                    src_name = _decoded_source_reg(decoded)
                    if src_name is not None:
                        state.tracked_reg = src_name
                        continue
                if ikb == "MOVEA":
                    src_name = _decoded_source_reg(decoded)
                    if src_name is not None:
                        state.tracked_reg = src_name
                        continue
                symbol = _call_input_symbol(call, inp)
                address = _segment_seed_addr(decoded.ea_op, len(code), base_addr=base_addr)
                if inp.semantic_kind == "code_ptr":
                    if address is None:
                        state.complete = True
                        continue
                    segment_code_name_candidates.setdefault(address, set()).add(symbol)
                elif include_data_labels and (inp.type == "STRPTR" or inp.semantic_kind == "string_ptr"):
                    if address is None:
                        state.complete = True
                        continue
                    string_span = read_c_string_span(code, address)
                    if string_span is None:
                        state.complete = True
                        continue
                    _text, end = string_span
                    if any(addr in code_addrs for addr in range(address, end)):
                        state.complete = True
                        continue
                    existing_end = string_ranges.get(address)
                    if existing_end is not None and existing_end != end:
                        raise ValueError(
                            f"Conflicting typed string ranges for ${address:08X}: "
                            f"{existing_end:08X} vs {end:08X}")
                    string_ranges[address] = end
                    segment_data_name_candidates.setdefault(address, set()).add(symbol)
                elif include_data_labels and ikb == "LEA" and inp.i_struct is not None:
                    region = _region_from_lea(inst, decoded, inp.i_struct, os_kb, platform)
                    if region is not None and region.provenance.address_space == MemoryRegionAddressSpace.SEGMENT:
                        address = region.provenance.segment_addr
                        if address is None:
                            raise ValueError(
                            f"Segment provenance missing address for {call.function}:{inp.name}")
                        segment_data_name_candidates.setdefault(address, set()).add(symbol)
                        segment_struct_candidates.setdefault(address, set()).add(inp.i_struct)
                        _apply_segment_struct_typed_overlay(
                            address=address,
                            struct_name=inp.i_struct,
                            os_kb=os_kb,
                            typed_data_sizes=typed_data_sizes,
                            typed_data_comments=typed_data_comments,
                            typed_data_fields=typed_data_fields,
                        )
                state.complete = True

    _apply_leading_word_wrapper_segment_seeds(
        blocks,
        lib_calls,
        code,
        base_addr=base_addr,
        arg_annotations=arg_annotations,
        segment_data_name_candidates=segment_data_name_candidates,
        segment_struct_candidates=segment_struct_candidates,
        typed_data_sizes=typed_data_sizes,
        typed_data_comments=typed_data_comments,
        typed_data_fields=typed_data_fields,
        os_kb=os_kb,
    )

    segment_data_symbols = _finalize_segment_symbols(segment_data_name_candidates)
    segment_struct_regions = _finalize_segment_symbols(segment_struct_candidates)
    segment_code_symbols = _finalize_segment_symbols(segment_code_name_candidates)

    return CallSetupAnalysis(
        arg_annotations=arg_annotations,
        segment_data_symbols=segment_data_symbols,
        segment_struct_regions=segment_struct_regions,
        typed_data_sizes=typed_data_sizes,
        typed_data_comments=typed_data_comments,
        typed_data_fields=typed_data_fields,
        segment_code_symbols=segment_code_symbols,
        code_entry_points=tuple(sorted(segment_code_symbols)),
        string_ranges=string_ranges,
    )


# -- Typed memory regions ----------------------------------------------


def _region_from_lea(inst: Instruction, decoded: DecodedOperands, struct_name: str,
                     os_kb: OsKb, platform: PlatformState | None) -> TypedMemoryRegion | None:
    op = decoded.ea_op
    if op is None:
        return None
    struct_def = os_kb.STRUCTS[struct_name]
    if op.mode == "disp":
        assert op.reg is not None, "Displacement operand missing base register"
        assert op.value is not None, "Displacement operand missing value"
        base_register = _address_reg_name(op.reg)
        displacement = op.value
        kind = MemoryRegionAddressSpace.REGISTER
        if platform is not None and platform.app_base is not None:
            base_reg_num = platform.app_base.reg_num
            if op.reg == base_reg_num:
                kind = MemoryRegionAddressSpace.APP
        return TypedMemoryRegion(
            struct=struct_name,
            size=struct_def.size,
            provenance=provenance_base_displacement(kind, base_register, displacement),
        )
    if op.mode == "pcdisp":
        return TypedMemoryRegion(
            struct=struct_name,
            size=struct_def.size,
            provenance=MemoryRegionProvenance(
                address_space=MemoryRegionAddressSpace.SEGMENT,
                segment_addr=op.value,
            ),
        )
    if op.mode == "absw":
        assert op.value is not None, "abs.w operand missing value"
        value = op.value
        return TypedMemoryRegion(
            struct=struct_name,
            size=struct_def.size,
            provenance=MemoryRegionProvenance(
                address_space=MemoryRegionAddressSpace.ABSOLUTE,
                absolute_addr=value & 0xFFFF,
            ),
        )
    if op.mode == "absl":
        assert op.value is not None, "abs.l operand missing value"
        value = op.value
        return TypedMemoryRegion(
            struct=struct_name,
            size=struct_def.size,
            provenance=MemoryRegionProvenance(
                address_space=MemoryRegionAddressSpace.ABSOLUTE,
                absolute_addr=value,
            ),
        )
    return None


def _find_region_seed(block: BasicBlock, call_addr: int, reg_name: str, struct_name: str,
                      os_kb: OsKb, platform: PlatformState | None
                      ) -> tuple[int, str, TypedMemoryRegion] | None:
    call_idx = None
    for i, inst in enumerate(block.instructions):
        if inst.offset == call_addr:
            call_idx = i
            break
    if call_idx is None:
        return None

    tracked = reg_name
    for j in range(call_idx - 1, -1, -1):
        inst = block.instructions[j]
        ikb, decoded = _decode_inst(inst)
        dst = decode_inst_destination(inst, ikb)
        dst_name = None if dst is None else _reg_name(dst[0], dst[1])
        if dst_name != tracked:
            continue

        op_type = None if ikb is None else runtime_m68k_analysis.OPERATION_TYPES.get(ikb)
        if op_type == runtime_m68k_analysis.OperationType.MOVE:
            src_name = _decoded_source_reg(decoded)
            if src_name is not None:
                tracked = src_name
                continue

        if ikb is not None and ikb.upper() == "LEA":
            region = _region_from_lea(inst, decoded, struct_name, os_kb, platform)
            if region is None:
                return None
            return inst.offset, tracked, region
        return None
    return None


def _region_facts(facts: dict[str, RegisterFact]) -> dict[str, TypedMemoryRegion]:
    return {
        reg: fact.region
        for reg, fact in facts.items()
        if fact.region is not None
    }


def _concrete_facts(facts: dict[str, RegisterFact]) -> dict[str, int]:
    return {
        reg: fact.concrete
        for reg, fact in facts.items()
        if fact.concrete is not None
    }


def _merge_register_facts(existing: dict[str, RegisterFact] | None,
                          incoming: dict[str, RegisterFact],
                          os_kb: OsKb,
                          ) -> tuple[dict[str, RegisterFact], bool]:
    if existing is None:
        return dict(incoming), True
    merged: dict[str, RegisterFact] = {}
    for reg, fact in existing.items():
        incoming_fact = incoming.get(reg)
        if incoming_fact is None:
            continue
        merged_fact = _merge_register_fact(fact, incoming_fact, os_kb)
        if merged_fact is not None:
            merged[reg] = merged_fact
    return merged, merged != existing


def _struct_lineage(os_kb: OsKb, struct_name: str) -> tuple[str, ...]:
    lineage: list[str] = []
    seen: set[str] = set()
    current: str | None = struct_name
    while current is not None:
        if current in seen:
            raise ValueError(f"Cyclic struct inheritance detected for {struct_name}")
        seen.add(current)
        lineage.append(current)
        current = os_kb.STRUCTS[current].base_struct
    return tuple(lineage)


def _common_region_struct(os_kb: OsKb,
                          left: TypedMemoryRegion,
                          right: TypedMemoryRegion) -> str | None:
    if left.context_name != right.context_name or left.struct_offset != right.struct_offset:
        return None
    if _is_opaque_segment_region(left) or _is_opaque_segment_region(right):
        if left == right:
            return left.struct
        return None
    right_lineage = set(_struct_lineage(os_kb, right.struct))
    for candidate in _struct_lineage(os_kb, left.struct):
        if candidate not in right_lineage:
            continue
        struct_def = os_kb.STRUCTS[candidate]
        if left.struct_offset < struct_def.size:
            return candidate
    return None


def _merged_region_fact(left: RegisterFact,
                        right: RegisterFact,
                        os_kb: OsKb) -> TypedMemoryRegion | None:
    left_region = left.region
    right_region = right.region
    if left_region is None or right_region is None:
        return None
    common_struct = _common_region_struct(os_kb, left_region, right_region)
    if common_struct is None:
        return None
    size = left_region.size if _is_opaque_segment_region(left_region) else os_kb.STRUCTS[common_struct].size
    provenance = left_region.provenance
    if left_region != right_region:
        provenance = MemoryRegionProvenance(address_space=MemoryRegionAddressSpace.REGISTER)
    return TypedMemoryRegion(
        struct=common_struct,
        size=size,
        provenance=provenance,
        struct_offset=left_region.struct_offset,
        context_name=left_region.context_name,
    )


def _merge_register_fact(existing: RegisterFact,
                         incoming: RegisterFact,
                         os_kb: OsKb) -> RegisterFact | None:
    if existing == incoming:
        return existing
    region = _merged_region_fact(existing, incoming, os_kb)
    concrete = existing.concrete if existing.concrete == incoming.concrete else None
    if region is None and concrete is None:
        return None
    return RegisterFact(region=region, concrete=concrete)


def _summary_register_facts(current: dict[str, RegisterFact],
                            summary: CallSummary | None,
                            os_kb: OsKb,
                            ) -> dict[str, RegisterFact]:
    if summary is None:
        return dict(current)
    result: dict[str, RegisterFact] = {}
    produced_d_tags = dict(summary.produced_d_tags)
    produced_a_tags = dict(summary.produced_a_tags)
    for reg_num in summary.preserved_d:
        reg_name = _reg_name("dn", reg_num)
        fact = current.get(reg_name)
        if fact is not None:
            result[reg_name] = fact
    for reg_num in summary.preserved_a:
        reg_name = _reg_name("an", reg_num)
        fact = current.get(reg_name)
        if fact is not None:
            result[reg_name] = fact
    for reg_num, concrete in summary.produced_d:
        reg_name = _reg_name("dn", reg_num)
        tag = produced_d_tags.get(reg_num)
        region = (_region_from_library_base_tag(tag, os_kb)
                  if isinstance(tag, LibraryBaseTag) else None)
        result[reg_name] = RegisterFact(region=region, concrete=concrete)
    for reg_num, tag in summary.produced_d_tags:
        reg_name = _reg_name("dn", reg_num)
        if reg_name in result:
            continue
        region = (_region_from_library_base_tag(tag, os_kb)
                  if isinstance(tag, LibraryBaseTag) else None)
        result[reg_name] = RegisterFact(region=region)
    for reg_num, concrete in summary.produced_a:
        reg_name = _reg_name("an", reg_num)
        tag = produced_a_tags.get(reg_num)
        region = (_region_from_library_base_tag(tag, os_kb)
                  if isinstance(tag, LibraryBaseTag) else None)
        result[reg_name] = RegisterFact(region=region, concrete=concrete)
    for reg_num, tag in summary.produced_a_tags:
        reg_name = _reg_name("an", reg_num)
        if reg_name in result:
            continue
        region = (_region_from_library_base_tag(tag, os_kb)
                  if isinstance(tag, LibraryBaseTag) else None)
        result[reg_name] = RegisterFact(region=region)
    return result


def _restore_platform_register_facts(result: dict[str, RegisterFact],
                                     platform: PlatformState | None,
                                     ) -> None:
    if platform is not None and platform.app_base is not None:
        reg_num = platform.app_base.reg_num
        concrete_val = platform.app_base.concrete
        reg_name = _address_reg_name(reg_num)
        result.setdefault(reg_name, RegisterFact(concrete=concrete_val))
    if platform is not None and platform.initial_register_regions is not None:
        for reg_name, region in platform.initial_register_regions.items():
            result.setdefault(reg_name, RegisterFact(region=region))


def _apply_region_fact_summary(current: dict[str, RegisterFact],
                               result: dict[str, RegisterFact],
                               region_summary: RegionSummary | None,
                               os_kb: OsKb,
                               ) -> None:
    if region_summary is None:
        return
    for transfer in region_summary.region_offset_transfers:
        src_fact = current.get(transfer.src_reg)
        if src_fact is None or src_fact.region is None:
            continue
        offset_region = _offset_region(src_fact.region, transfer.offset)
        if offset_region is None:
            continue
        existing = result.get(transfer.dst_reg)
        result[transfer.dst_reg] = RegisterFact(
            region=offset_region,
            concrete=None if existing is None else existing.concrete,
        )
    for field_transfer in region_summary.field_pointer_transfers:
        src_fact = current.get(field_transfer.src_reg)
        if src_fact is None or src_fact.region is None:
            continue
        field_info = _resolve_region_field(
            os_kb, src_fact.region, field_transfer.displacement)
        if field_info is None:
            continue
        region = _region_from_pointer_field(
            field_info=field_info,
            os_kb=os_kb,
            base_register=field_transfer.src_reg,
            displacement=field_transfer.displacement,
        )
        if region is None:
            raise ValueError(
                f"Region transfer {field_transfer.src_reg}+{field_transfer.displacement} missing pointer struct")
        result[field_transfer.dst_reg] = RegisterFact(
            region=region,
        )
    for reg_name, region in region_summary.produced:
        existing = result.get(reg_name)
        result[reg_name] = RegisterFact(
            region=region,
            concrete=None if existing is None else existing.concrete,
        )


def _same_region_shape(left: TypedMemoryRegion, right: TypedMemoryRegion) -> bool:
    return (
        left.struct == right.struct
        and left.size == right.size
        and left.struct_offset == right.struct_offset
        and left.context_name == right.context_name
    )


def _output_struct_region_facts(
    lib_calls: list[LibraryCall],
    os_kb: OsKb,
) -> dict[int, dict[str, RegisterFact]]:
    facts_by_call: dict[int, dict[str, RegisterFact]] = {}
    for call in lib_calls:
        output = call.output
        if output is None or output.i_struct is None or output.reg is None:
            continue
        if call.library != "unknown":
            library = os_kb.LIBRARIES.get(call.library)
            if library is None:
                raise KeyError(f"Unknown library {call.library}")
            func = library.functions.get(call.function)
            if func is None:
                raise KeyError(f"Unknown function {call.library}:{call.function}")
            if func.returns_base is not None:
                continue
        struct_name = output.i_struct
        if struct_name not in os_kb.STRUCTS:
            raise KeyError(f"Unknown output struct {struct_name}")
        struct_def = os_kb.STRUCTS[struct_name]
        reg_name = output.reg.lower()
        region = TypedMemoryRegion(
            struct=struct_name,
            size=struct_def.size,
            provenance=MemoryRegionProvenance(address_space=MemoryRegionAddressSpace.REGISTER),
        )
        output_facts = facts_by_call.setdefault(call.addr, {})
        existing = output_facts.get(reg_name)
        if existing is not None:
            if existing.region is None or not _same_region_shape(existing.region, region):
                raise ValueError(
                    f"Conflicting output struct facts for call ${call.addr:06X} {reg_name}: "
                    f"{existing.region} vs {region}"
                )
            continue
        output_facts[reg_name] = RegisterFact(region=region)
    return facts_by_call


def _apply_output_struct_region_facts(
    result: dict[str, RegisterFact],
    output_facts: dict[str, RegisterFact] | None,
) -> None:
    if output_facts is None:
        return
    for reg_name, fact in output_facts.items():
        if fact.region is None:
            raise ValueError(f"Output struct fact for {reg_name} is missing region")
        existing = result.get(reg_name)
        result[reg_name] = RegisterFact(
            region=fact.region,
            concrete=None if existing is None else existing.concrete,
        )


def _apply_register_fact_summary(current: dict[str, RegisterFact],
                                 summary: CallSummary | None,
                                 region_summary: RegionSummary | None,
                                 os_kb: OsKb,
                                 platform: PlatformState | None,
                                 ) -> dict[str, RegisterFact]:
    result = _summary_register_facts(current, summary, os_kb)
    _restore_platform_register_facts(result, platform)
    _apply_region_fact_summary(current, result, region_summary, os_kb)
    return result


def _signed_16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def _input_regs(inp: runtime_os.OsInput) -> tuple[str, ...]:
    regs = inp.regs
    assert isinstance(regs, tuple), "OS input regs must be a tuple"
    return regs


def _input_reg_display(inp: runtime_os.OsInput) -> str:
    return "/".join(_input_regs(inp))


def _signed_index_value(op: Operand, concrete_regs: dict[str, int]) -> int | None:
    if op.index_suppressed:
        return 0
    index_reg = op.index_reg
    assert index_reg is not None, "Indexed operand missing index register"
    index_mode = "an" if op.index_is_addr else "dn"
    index_name = _reg_name(index_mode, index_reg)
    index_value = concrete_regs.get(index_name)
    if index_value is None:
        return None
    if op.index_size == "w":
        index_value = _signed_16(index_value)
    elif op.index_size != "l":
        raise ValueError(f"Unsupported index size {op.index_size!r}")
    return index_value * int(op.index_scale)


def _effective_index_offset(op: Operand | None, concrete_regs: dict[str, int]) -> tuple[str, int] | None:
    if op is None or op.mode != "index" or op.memory_indirect or op.base_suppressed:
        return None
    assert op.reg is not None, "Indexed operand missing base register"
    base_register = _address_reg_name(op.reg)
    base_displacement = op.value if op.value is not None else op.base_displacement
    if base_displacement is None:
        base_displacement = 0
    index_value = _signed_index_value(op, concrete_regs)
    if index_value is None:
        return None
    return base_register, base_displacement + index_value


def _resolve_region_field(os_kb: OsKb, region: TypedMemoryRegion,
                          displacement: int) -> ResolvedStructField | None:
    if _is_opaque_segment_region(region):
        return None
    field_offset = region.struct_offset + displacement
    if field_offset < 0:
        return None
    return resolve_struct_field(
        os_kb.STRUCTS,
        region.struct,
        field_offset,
    )


def _resolve_app_struct_field(app_struct_regions: dict[int, TypedMemoryRegion],
                              displacement: int,
                              os_kb: OsKb
                              ) -> tuple[int, TypedMemoryRegion, int, ResolvedStructField] | None:
    for region_offset, region in app_struct_regions.items():
        region_end = region_offset + region.size
        if displacement < region_offset or displacement >= region_end:
            continue
        field_displacement = displacement - region_offset
        field_info = _resolve_region_field(os_kb, region, field_displacement)
        if field_info is None:
            return None
        return region_offset, region, field_displacement, field_info
    return None


def _resolve_app_pointer_region(app_pointer_regions: dict[int, TypedMemoryRegion],
                                displacement: int) -> TypedMemoryRegion | None:
    return app_pointer_regions.get(displacement)


def _region_from_library_base_tag(tag: LibraryBaseTag,
                                  os_kb: OsKb) -> TypedMemoryRegion | None:
    if tag.struct_name is None:
        return None
    struct_name = _refined_named_base_struct(
        os_kb, tag.library_base, tag.struct_name)
    if struct_name is None:
        raise ValueError(f"Named base {tag.library_base} resolved to no struct")
    struct_def = os_kb.STRUCTS[struct_name]
    return TypedMemoryRegion(
        struct=struct_name,
        size=struct_def.size,
        provenance=provenance_named_base(tag.library_base),
    )


def _region_from_pointer_field(
    *,
    field_info: ResolvedStructField,
    os_kb: OsKb,
    base_register: str,
    displacement: int,
    source_is_app: bool = False,
    pointee_offset: int = 0,
) -> TypedMemoryRegion | None:
    pointer_struct = field_info.field.pointer_struct
    if pointer_struct is None:
        return None
    named_base = field_info.field.named_base
    struct_name = pointer_struct
    if named_base is not None:
        specific_struct = os_kb.META.named_base_structs.get(named_base)
        if specific_struct is not None:
            if specific_struct not in os_kb.STRUCTS:
                raise KeyError(
                    f"Named base {named_base} maps to unknown struct {specific_struct}"
                )
            struct_name = specific_struct
    if struct_name is None:
        return None
    struct_def = os_kb.STRUCTS[struct_name]
    if pointee_offset < 0 or pointee_offset >= struct_def.size:
        return None
    if named_base is not None:
        provenance = provenance_named_base(named_base)
    elif source_is_app:
        provenance = provenance_base_displacement(
            MemoryRegionAddressSpace.APP, base_register, displacement
        )
    else:
        provenance = provenance_field_pointer(base_register, displacement)
    return TypedMemoryRegion(
        struct=struct_name,
        size=struct_def.size,
        provenance=provenance,
        struct_offset=pointee_offset,
    )


def _region_from_typed_address(current: dict[str, RegisterFact],
                               op: Operand | None,
                               os_kb: OsKb,
                               app_struct_regions: dict[int, TypedMemoryRegion],
                               platform: PlatformState | None) -> TypedMemoryRegion | None:
    if op is None:
        return None
    if op.mode == "ind":
        assert op.reg is not None, "Indirect operand missing base register"
        base_fact = current.get(_address_reg_name(op.reg))
        if base_fact is None or base_fact.region is None:
            return None
        return base_fact.region
    if op.mode == "disp":
        assert op.reg is not None and op.value is not None, (
            "Displacement operand missing register or value")
        reg = op.reg
        displacement = op.value
        if (platform is not None
                and platform.app_base is not None
                and reg == platform.app_base.reg_num):
            resolved = _resolve_app_struct_field(app_struct_regions, displacement, os_kb)
            if resolved is not None:
                _region_offset, region, field_displacement, _field_info = resolved
                return TypedMemoryRegion(
                    struct=region.struct,
                    size=region.size,
                    provenance=region.provenance,
                    struct_offset=region.struct_offset + field_displacement,
                )
        base_fact = current.get(_address_reg_name(reg))
        if base_fact is None or base_fact.region is None:
            return None
        next_offset = base_fact.region.struct_offset + displacement
        if next_offset < 0 or next_offset >= base_fact.region.size:
            return None
        return TypedMemoryRegion(
            struct=base_fact.region.struct,
            size=base_fact.region.size,
            provenance=base_fact.region.provenance,
            struct_offset=next_offset,
        )
    if op.mode != "index" or op.base_suppressed:
        return None
    assert op.reg is not None, "Indexed operand missing base register"
    reg = op.reg
    base_fact = current.get(_address_reg_name(reg))
    if base_fact is None or base_fact.region is None:
        return None
    concrete_regs = _concrete_facts(current)
    if not op.memory_indirect:
        offset_info = _effective_index_offset(op, concrete_regs)
        if offset_info is None:
            return None
        _base_register, displacement = offset_info
        next_offset = base_fact.region.struct_offset + displacement
        if next_offset < 0 or next_offset >= base_fact.region.size:
            return None
        return TypedMemoryRegion(
            struct=base_fact.region.struct,
            size=base_fact.region.size,
            provenance=base_fact.region.provenance,
            struct_offset=next_offset,
        )
    base_displacement = 0 if op.base_displacement is None else op.base_displacement
    index_value = _signed_index_value(op, concrete_regs)
    if index_value is None:
        return None
    pointer_field_offset = base_displacement
    pointee_offset = 0 if op.outer_displacement is None else op.outer_displacement
    if op.postindexed:
        pointee_offset += index_value
    else:
        pointer_field_offset += index_value
    field_info = _resolve_region_field(os_kb, base_fact.region, pointer_field_offset)
    if field_info is None:
        return None
    return _region_from_pointer_field(
        field_info=field_info,
        os_kb=os_kb,
        base_register=_address_reg_name(reg),
        displacement=pointer_field_offset,
        pointee_offset=pointee_offset,
    )


def _field_offset_from_source_operand(op: Operand | None) -> tuple[str, int] | None:
    if op is None:
        return None
    if op.mode == "ind":
        assert op.reg is not None, "Indirect operand missing base register"
        return _address_reg_name(op.reg), 0
    if op.mode == "disp":
        assert op.reg is not None and op.value is not None, (
            "Displacement operand missing register or value")
        return (_address_reg_name(op.reg), op.value)
    if (op.mode == "index"
            and op.full_extension
            and not op.memory_indirect
            and not op.base_suppressed
            and op.index_suppressed):
        assert op.reg is not None, "Indexed operand missing base register"
        return (_address_reg_name(op.reg), 0 if op.base_displacement is None else op.base_displacement)
    return None


def _pointee_region_from_load(current: dict[str, RegisterFact],
                              inst: Instruction,
                              hunk_index: int,
                              decoded: DecodedOperands,
                              os_kb: OsKb,
                              app_struct_regions: dict[int, TypedMemoryRegion],
                              app_pointer_regions: dict[int, TypedMemoryRegion],
                              absolute_pointer_regions: dict[tuple[int, int], TypedMemoryRegion],
                              reloc_target_hunks: dict[int, int] | None,
                              platform: PlatformState | None) -> TypedMemoryRegion | None:
    source_op = decoded.ea_op
    if source_op is not None and source_op.mode in {"absw", "absl"} and source_op.value is not None:
        absolute_addr = (source_op.value & 0xFFFF) if source_op.mode == "absw" else source_op.value
        target_hunk = hunk_index
        if reloc_target_hunks is not None:
            for ext_off in range(
                inst.offset + runtime_m68k_analysis.OPWORD_BYTES,
                inst.offset + inst.size,
            ):
                resolved_hunk = reloc_target_hunks.get(ext_off)
                if resolved_hunk is not None:
                    target_hunk = resolved_hunk
                    break
        absolute_region = absolute_pointer_regions.get((target_hunk, absolute_addr))
        if absolute_region is not None:
            return absolute_region
    src_info = _field_offset_from_source_operand(decoded.ea_op)
    if src_info is None:
        src_info = _effective_index_offset(decoded.ea_op, _concrete_facts(current))
    if src_info is None:
        return None
    base_register, displacement = src_info
    field_info = None
    source_is_app = False
    if (platform is not None
            and platform.app_base is not None
            and base_register == _address_reg_name(platform.app_base.reg_num)):
        resolved = _resolve_app_struct_field(app_struct_regions, displacement, os_kb)
        if resolved is not None:
            _region_offset, _region, _field_displacement, field_info = resolved
            source_is_app = True
        else:
            pointer_region = _resolve_app_pointer_region(app_pointer_regions, displacement)
            if pointer_region is not None:
                return pointer_region
    if field_info is None:
        base_fact = current.get(base_register)
        if base_fact is None or base_fact.region is None:
            return None
        field_info = _resolve_region_field(os_kb, base_fact.region, displacement)
        if field_info is None:
            return None
    return _region_from_pointer_field(
        field_info=field_info,
        os_kb=os_kb,
        base_register=base_register,
        displacement=displacement,
        source_is_app=source_is_app,
    )


def _immediate_constant(decoded: DecodedOperands) -> int | None:
    return None if decoded.imm_val is None else int(decoded.imm_val)


def _updated_concrete_value(current: dict[str, RegisterFact], ikb: str | None,
                            decoded: DecodedOperands, dst_name: str) -> int | None:
    op_type = None if ikb is None else runtime_m68k_analysis.OPERATION_TYPES.get(ikb)
    if op_type == runtime_m68k_analysis.OperationType.MOVE:
        src_name = _decoded_source_reg(decoded)
        if src_name is not None:
            src_fact = current.get(src_name)
            if src_fact is not None and src_fact.concrete is not None:
                return src_fact.concrete
        imm_val = _immediate_constant(decoded)
        if imm_val is not None:
            return imm_val
    if op_type == runtime_m68k_analysis.OperationType.CLEAR:
        return 0
    if op_type in {
        runtime_m68k_analysis.OperationType.ADD,
        runtime_m68k_analysis.OperationType.SUB,
    } and ikb in {"ADDQ", "SUBQ"}:
        imm_val = _immediate_constant(decoded)
        assert imm_val is not None, f"{ikb} missing decoded immediate"
        prior_fact = current.get(dst_name)
        if prior_fact is None or prior_fact.concrete is None:
            return None
        delta = imm_val if ikb == "ADDQ" else -imm_val
        return (prior_fact.concrete + delta) & 0xFFFFFFFF
    return None


def _set_register_fact(current: dict[str, RegisterFact], reg_name: str,
                       *, region: TypedMemoryRegion | None,
                       concrete: int | None) -> None:
    if region is None and concrete is None:
        current.pop(reg_name, None)
        return
    current[reg_name] = RegisterFact(region=region, concrete=concrete)


def _is_opaque_segment_region(region: TypedMemoryRegion) -> bool:
    return region.struct == _OPAQUE_SEGMENT_REGION_STRUCT


def _segment_data_region(address: int, code_size: int) -> TypedMemoryRegion:
    return TypedMemoryRegion(
        struct=_OPAQUE_SEGMENT_REGION_STRUCT,
        size=code_size - address,
        provenance=MemoryRegionProvenance(
            address_space=MemoryRegionAddressSpace.SEGMENT,
            segment_addr=address,
        ),
    )


def _offset_region(region: TypedMemoryRegion, offset: int) -> TypedMemoryRegion | None:
    if offset < 0:
        return None
    if _is_opaque_segment_region(region):
        segment_addr = region.provenance.segment_addr
        if segment_addr is None or offset > region.size:
            return None
        return TypedMemoryRegion(
            struct=region.struct,
            size=region.size - offset,
            provenance=MemoryRegionProvenance(
                address_space=MemoryRegionAddressSpace.SEGMENT,
                segment_addr=segment_addr + offset,
            ),
            context_name=region.context_name,
        )
    if offset > region.size:
        return None
    return TypedMemoryRegion(
        struct=region.struct,
        size=region.size,
        provenance=region.provenance,
        struct_offset=region.struct_offset + offset,
        context_name=region.context_name,
    )


def _apply_register_update(current: dict[str, RegisterFact],
                           inst: Instruction,
                           hunk_index: int,
                           ikb: str | None,
                           decoded: DecodedOperands,
                           dst_name: str,
                           os_kb: OsKb,
                           app_struct_regions: dict[int, TypedMemoryRegion],
                           app_pointer_regions: dict[int, TypedMemoryRegion],
                           absolute_pointer_regions: dict[tuple[int, int], TypedMemoryRegion],
                           reloc_target_hunks: dict[int, int] | None,
                           platform: PlatformState | None) -> None:
    op_type = None if ikb is None else runtime_m68k_analysis.OPERATION_TYPES.get(ikb)
    concrete = _updated_concrete_value(current, ikb, decoded, dst_name)
    if ikb == "LEA":
        region = _region_from_typed_address(
            current, decoded.ea_op, os_kb, app_struct_regions, platform)
        _set_register_fact(current, dst_name, region=region, concrete=concrete)
        return
    if op_type == runtime_m68k_analysis.OperationType.MOVE or ikb == "MOVEA":
        pointee_region = _pointee_region_from_load(
            current,
            inst,
            hunk_index,
            decoded,
            os_kb,
            app_struct_regions,
            app_pointer_regions,
            absolute_pointer_regions,
            reloc_target_hunks,
            platform,
        )
        if pointee_region is not None:
            _set_register_fact(current, dst_name, region=pointee_region, concrete=concrete)
            return
        src_name = _decoded_source_reg(decoded)
        if src_name is not None:
            src_fact = current.get(src_name)
            if src_fact is not None and src_fact.region is not None:
                _set_register_fact(current, dst_name, region=src_fact.region, concrete=concrete)
                return
    _set_register_fact(current, dst_name, region=None, concrete=concrete)


def build_app_struct_regions(blocks: dict[int, BasicBlock],
                             lib_calls: list[LibraryCall],
                             os_kb: OsKb,
                             platform: PlatformState | None = None,
                             target_metadata: TargetMetadata | None = None,
                             ) -> dict[int, TypedMemoryRegion]:
    """Build persistent app-relative typed regions from OS call inputs."""
    if platform is None or platform.app_base is None:
        return {}
    os_kb = build_target_local_os_kb(os_kb, target_metadata)
    base_reg_num = platform.app_base.reg_num
    base_reg_name = _address_reg_name(base_reg_num)
    result: dict[int, TypedMemoryRegion] = {}
    for call in lib_calls:
        block = blocks.get(call.block)
        if block is None:
            continue
        for inp in call.inputs:
            if inp.i_struct is None:
                continue
            for reg in _input_regs(inp):
                seed = _find_region_seed(
                    block, call.addr, reg.lower(), inp.i_struct, os_kb, platform)
                if seed is None:
                    continue
                _seed_offset, _seed_reg, region = seed
                provenance = region.provenance
                if provenance.address_space != MemoryRegionAddressSpace.APP:
                    continue
                prov_base_register, displacement = require_base_displacement(
                    provenance, expected_space=MemoryRegionAddressSpace.APP)
                if prov_base_register != base_reg_name:
                    raise ValueError(
                        f"App-relative region base mismatch: expected {base_reg_name}, "
                        f"got {prov_base_register}")
                existing = result.get(displacement)
                if existing is not None and existing != region:
                    raise ValueError(
                        f"Conflicting app struct regions at offset {displacement}: "
                        f"{existing} vs {region}")
                result[displacement] = region
    if target_metadata is not None:
        for slot in target_metadata.app_slot_regions:
            if slot.struct_name is None:
                continue
            struct_def = os_kb.STRUCTS.get(slot.struct_name)
            if struct_def is None:
                raise KeyError(f"Unknown custom app slot struct {slot.struct_name}")
            region = TypedMemoryRegion(
                struct=slot.struct_name,
                size=struct_def.size,
                provenance=provenance_base_displacement(
                    MemoryRegionAddressSpace.APP, base_reg_name, slot.offset),
            )
            existing = result.get(slot.offset)
            if existing is not None and existing != region:
                raise ValueError(
                    f"Conflicting app struct regions at offset {slot.offset}: "
                    f"{existing} vs {region}")
            result[slot.offset] = region
    return result


def build_app_slot_symbols(blocks: dict[int, BasicBlock],
                           lib_calls: list[LibraryCall],
                           code: bytes,
                           os_kb: OsKb,
                           platform: PlatformState,
                           target_metadata: TargetMetadata | None = None) -> dict[int, str]:
    raw_app_offsets: dict[int, str] = {}
    base_info = platform.app_base
    init_mem = platform.initial_mem
    if base_info and init_mem:
        for (addr, _nbytes), tag in init_mem.iter_tags():
            if not isinstance(tag, LibraryBaseTag):
                continue
            offset = _app_slot_offset_from_absolute_addr(base_info, addr)
            if offset is None:
                continue
            lib_name = tag.library_base
            base_name = lib_name.rsplit(".", 1)[0]
            sym = _sanitize_app_name(base_name)
            raw_app_offsets[offset] = f"app_{sym}_base"
    if base_info and lib_calls:
        named_bases = build_app_named_bases(blocks, lib_calls, code, os_kb, platform)
        slot_usages = collect_app_memory_type_usages(blocks, lib_calls, base_reg=base_info.reg_num)
        naming_by_offset: dict[int, AppSlotNaming] = {}
        for offset, infos in slot_usages.items():
            if offset not in raw_app_offsets:
                naming_by_offset[offset] = _app_slot_naming(
                    offset=offset,
                    infos=infos,
                    named_base=named_bases.get(offset),
                )
        grouped_candidates: dict[str, list[int]] = {}
        for naming in naming_by_offset.values():
            for sym in naming.candidates:
                grouped_candidates.setdefault(sym, []).append(naming.offset)
        for offset, naming in naming_by_offset.items():
            raw_app_offsets[offset] = _choose_app_slot_symbol(naming, grouped_candidates)
    if target_metadata is not None:
        for slot in target_metadata.app_slot_regions:
            if slot.symbol is None:
                continue
            raw_app_offsets[slot.offset] = slot.symbol

    grouped: dict[str, list[int]] = {}
    for offset, symbol in raw_app_offsets.items():
        grouped.setdefault(symbol, []).append(offset)

    app_offsets: dict[int, str] = {}
    for symbol, offsets in grouped.items():
        if len(offsets) == 1:
            app_offsets[offsets[0]] = symbol
            continue
        for offset in sorted(offsets):
            app_offsets[offset] = f"{symbol}_{_app_slot_disambiguator(base_info, offset)}"
    return app_offsets


def build_app_slot_infos(blocks: dict[int, BasicBlock],
                         lib_calls: list[LibraryCall],
                         code: bytes,
                         os_kb: OsKb,
                         platform: PlatformState,
                         target_metadata: TargetMetadata | None = None) -> tuple[AppSlotInfo, ...]:
    base_info = platform.app_base
    if base_info is None:
        return ()
    os_kb = build_target_local_os_kb(os_kb, target_metadata)
    symbols = build_app_slot_symbols(blocks, lib_calls, code, os_kb, platform, target_metadata)
    usages = collect_app_memory_type_usages(blocks, lib_calls, base_reg=base_info.reg_num)
    regions = build_app_struct_regions(blocks, lib_calls, os_kb, platform, target_metadata)
    pointer_regions = build_app_pointer_regions(blocks, lib_calls, code, os_kb, platform, target_metadata)
    named_bases = build_app_named_bases(blocks, lib_calls, code, os_kb, platform)
    infos: list[AppSlotInfo] = []
    for offset, symbol in sorted(symbols.items()):
        region = regions.get(offset)
        named_base = named_bases.get(offset)
        pointer_region = pointer_regions.get(offset)
        infos.append(AppSlotInfo(
            offset=offset,
            symbol=symbol,
            usages=usages.get(offset, ()),
            struct=None if region is None else region.struct,
            size=None if region is None else region.size,
            pointer_struct=None if pointer_region is None else pointer_region.struct,
            named_base=named_base,
        ))
    return tuple(infos)


def build_app_slot_pointer_structs(blocks: dict[int, BasicBlock],
                                   lib_calls: list[LibraryCall],
                                   os_kb: OsKb,
                                   platform: PlatformState | None = None
                                   ) -> dict[int, str]:
    result: dict[int, str] = {}
    if platform is None or platform.app_base is None:
        return result
    base_reg = platform.app_base.reg_num
    for call in lib_calls:
        if call.library == "unknown":
            continue
        library = os_kb.LIBRARIES.get(call.library)
        if library is None:
            raise KeyError(f"Unknown library {call.library}")
        func = library.functions.get(call.function)
        if func is None:
            raise KeyError(f"Unknown function {call.library}:{call.function}")
        output = func.output
        if output is None or output.i_struct is None or output.reg is None:
            continue
        if output.i_struct not in os_kb.STRUCTS:
            raise KeyError(f"Unknown output struct {output.i_struct}")
        store_offsets = _trace_app_return_store_offsets(
            blocks, call, output.reg.lower(), base_reg)
        for offset in store_offsets:
            existing = result.get(offset)
            if existing is not None and existing != output.i_struct:
                raise ValueError(
                    f"Conflicting pointer struct types for app slot {offset}: "
                    f"{existing} vs {output.i_struct}")
            result[offset] = output.i_struct
    return result


def build_app_pointer_regions(blocks: dict[int, BasicBlock],
                              lib_calls: list[LibraryCall],
                              code: bytes,
                              os_kb: OsKb,
                              platform: PlatformState | None = None,
                              target_metadata: TargetMetadata | None = None,
                              ) -> dict[int, TypedMemoryRegion]:
    if platform is None or platform.app_base is None:
        return {}
    os_kb = build_target_local_os_kb(os_kb, target_metadata)
    base_reg_name = _address_reg_name(platform.app_base.reg_num)
    named_bases = build_app_named_bases(blocks, lib_calls, code, os_kb, platform)
    pointer_structs = build_app_slot_pointer_structs(blocks, lib_calls, os_kb, platform)
    result: dict[int, TypedMemoryRegion] = {}
    for offset, generic_struct in pointer_structs.items():
        named_base = named_bases.get(offset)
        struct_name = _refined_named_base_struct(os_kb, named_base, generic_struct)
        if struct_name is None:
            raise ValueError(f"App pointer slot {offset} resolved to no struct")
        struct_def = os_kb.STRUCTS[struct_name]
        region = TypedMemoryRegion(
            struct=struct_name,
            size=struct_def.size,
            provenance=provenance_base_displacement(
                MemoryRegionAddressSpace.APP, base_reg_name, offset),
        )
        existing = result.get(offset)
        if existing is not None and existing != region:
            raise ValueError(
                f"Conflicting app pointer regions at offset {offset}: "
                f"{existing} vs {region}")
        result[offset] = region
    if target_metadata is not None:
        for slot in target_metadata.app_slot_regions:
            if slot.pointer_struct is None:
                continue
            custom_struct_def = os_kb.STRUCTS.get(slot.pointer_struct)
            if custom_struct_def is None:
                raise KeyError(f"Unknown custom app pointer struct {slot.pointer_struct}")
            region = TypedMemoryRegion(
                struct=slot.pointer_struct,
                size=custom_struct_def.size,
                provenance=provenance_base_displacement(
                    MemoryRegionAddressSpace.APP, base_reg_name, slot.offset),
            )
            existing = result.get(slot.offset)
            if existing is not None and existing != region:
                raise ValueError(
                    f"Conflicting app pointer regions at offset {slot.offset}: "
                    f"{existing} vs {region}")
            result[slot.offset] = region
    return result


def _typed_app_pointer_region(base_register: str,
                              displacement: int,
                              region: TypedMemoryRegion) -> TypedMemoryRegion:
    return TypedMemoryRegion(
        struct=region.struct,
        size=region.size,
        provenance=provenance_base_displacement(
            MemoryRegionAddressSpace.APP, base_register, displacement),
        struct_offset=region.struct_offset,
        context_name=region.context_name,
    )


def _merge_app_pointer_regions(existing: dict[int, TypedMemoryRegion],
                               incoming: dict[int, TypedMemoryRegion]) -> dict[int, TypedMemoryRegion]:
    merged = dict(existing)
    for offset, region in incoming.items():
        prior = merged.get(offset)
        if prior is not None and prior != region:
            raise ValueError(
                f"Conflicting app pointer regions at offset {offset}: "
                f"{prior} vs {region}")
        merged[offset] = region
    return merged


def _collect_app_pointer_regions_from_store_facts(
        blocks: dict[int, BasicBlock],
        facts_by_inst: dict[int, dict[str, TypedMemoryRegion]],
        platform: PlatformState | None,
) -> dict[int, TypedMemoryRegion]:
    if platform is None or platform.app_base is None:
        return {}
    base_reg = platform.app_base.reg_num
    base_register = _address_reg_name(base_reg)
    result: dict[int, TypedMemoryRegion] = {}
    for block in blocks.values():
        for inst in block.instructions:
            facts = facts_by_inst.get(inst.offset)
            if not facts:
                continue
            ikb, decoded = _decode_inst(inst)
            if runtime_m68k_analysis.OPERATION_TYPES.get(ikb) != runtime_m68k_analysis.OperationType.MOVE:
                continue
            src_name = _decoded_source_reg(decoded)
            if src_name is None:
                continue
            src_region = facts.get(src_name)
            if src_region is None:
                continue
            displacement = _base_disp_operand(decoded.dst_op, base_reg)
            if displacement is None:
                continue
            region = _typed_app_pointer_region(base_register, displacement, src_region)
            existing = result.get(displacement)
            if existing is not None and existing != region:
                raise ValueError(
                    f"Conflicting app pointer regions at offset {displacement}: "
                    f"{existing} vs {region}")
            result[displacement] = region
    return result


def _call_targets(blocks: dict[int, BasicBlock]) -> set[int]:
    targets: set[int] = set()
    for block in blocks.values():
        for xref in block.xrefs:
            if xref.type == "call":
                targets.add(xref.dst)
    return targets


def _compute_region_summaries(blocks: dict[int, BasicBlock],
                              facts_by_inst: dict[int, dict[str, TypedMemoryRegion]],
                              exec_summaries: dict[int, CallSummary | None] | None,
                              ) -> dict[int, RegionSummary]:
    from . import subroutine_summary

    call_targets = _call_targets(blocks)
    summaries: dict[int, RegionSummary] = {}
    for entry in sorted(call_targets):
        owned = subroutine_summary.find_sub_blocks(entry, blocks, call_targets)
        return_facts: list[dict[str, TypedMemoryRegion]] = []
        for addr in owned:
            block = blocks.get(addr)
            if block is None or not block.instructions:
                continue
            last = block.instructions[-1]
            if instruction_flow(last)[0] != runtime_m68k_analysis.FlowType.RETURN:
                continue
            return_facts.append(facts_by_inst.get(last.offset, {}))
        if not return_facts:
            continue
        common_regs = set(return_facts[0])
        for facts in return_facts[1:]:
            common_regs &= set(facts)
        produced: list[tuple[str, TypedMemoryRegion]] = []
        transfers: list[FieldPointerTransfer] = []
        exec_summary = None if exec_summaries is None else exec_summaries.get(entry)
        preserved_regs: set[str] = set()
        if exec_summary is not None:
            preserved_regs |= {_reg_name("dn", num) for num in exec_summary.preserved_d}
            preserved_regs |= {_reg_name("an", num) for num in exec_summary.preserved_a}
        for reg_name in sorted(common_regs):
            if reg_name in preserved_regs:
                continue
            region = return_facts[0][reg_name]
            if all(facts[reg_name] == region for facts in return_facts[1:]):
                provenance = region.provenance
                field_pointer = field_pointer_source(provenance)
                if field_pointer is not None:
                    transfers.append(FieldPointerTransfer(
                        dst_reg=reg_name,
                        src_reg=field_pointer[0],
                        displacement=field_pointer[1],
                    ))
                else:
                    produced.append((reg_name, region))
        if produced or transfers:
            summaries[entry] = RegionSummary(
                produced=tuple(produced),
                field_pointer_transfers=tuple(transfers),
            )
    return summaries


def _find_string_seed(block: BasicBlock, call_addr: int, reg_name: str, code: bytes) -> str | None:
    call_idx = None
    for i, inst in enumerate(block.instructions):
        if inst.offset == call_addr:
            call_idx = i
            break
    if call_idx is None:
        raise ValueError(f"Call ${call_addr:06x} not found in block ${block.start:06x}")
    for i in range(call_idx - 1, -1, -1):
        inst = block.instructions[i]
        ikb, decoded = _decode_inst(inst)
        dst = decode_inst_destination(inst, ikb)
        if dst is None or _reg_name(dst[0], dst[1]) != reg_name:
            continue
        op_type = None if ikb is None else runtime_m68k_analysis.OPERATION_TYPES.get(ikb)
        if ikb == "LEA" and decoded.ea_op is not None and decoded.ea_op.mode == "pcdisp":
            assert decoded.ea_op.value is not None, "pcdisp LEA operand missing value"
            assert isinstance(decoded.ea_op.value, int)
            value = read_string_at(code, decoded.ea_op.value)
            assert value is None or isinstance(value, str)
            return value
        if op_type == runtime_m68k_analysis.OperationType.MOVE and decoded.ea_op is not None:
            op = decoded.ea_op
            if op.mode in {"absw", "absl"} and op.value is not None:
                assert isinstance(op.value, int)
                value = read_string_at(code, op.value & 0xFFFFFFFF)
                assert value is None or isinstance(value, str)
                return value
        return None
    return None


def _find_local_immediate_seed(
    block: BasicBlock,
    call_addr: int,
    reg_mode: str,
    reg_num: int,
) -> int | None:
    call_idx = None
    for i, inst in enumerate(block.instructions):
        if inst.offset == call_addr:
            call_idx = i
            break
    if call_idx is None:
        raise ValueError(f"Call ${call_addr:06x} not found in block ${block.start:06x}")
    for i in range(call_idx - 1, -1, -1):
        inst = block.instructions[i]
        ikb = instruction_kb(inst)
        dst = decode_inst_destination(inst, ikb)
        if dst != (reg_mode, reg_num):
            continue
        return instruction_immediate_value(inst, ikb)
    return None


def _find_named_base_seed(block: BasicBlock, call_addr: int, reg_name: str, code: bytes) -> str | None:
    name = _find_string_seed(block, call_addr, reg_name, code)
    if name is None or not _is_named_base_seed(name):
        return None
    return name


def _trace_app_return_store_offsets(blocks: dict[int, BasicBlock],
                                    call: LibraryCall,
                                    result_reg: str,
                                    base_reg: int) -> tuple[int, ...]:
    offsets: list[int] = []

    def _record(offset: int) -> None:
        if offset not in offsets:
            offsets.append(offset)

    def _scan(instructions: list[Instruction]) -> None:
        tracked: set[str] = {result_reg}
        for inst in instructions:
            copied_to = None
            ikb, decoded = _decode_inst(inst)
            if ikb and runtime_m68k_analysis.OPERATION_TYPES.get(ikb) == runtime_m68k_analysis.OperationType.MOVE:
                src_name = _decoded_source_reg(decoded)
                if src_name in tracked:
                    offset = _base_disp_operand(decoded.dst_op, base_reg)
                    if offset is not None:
                        _record(offset)
                    copied_to = _decoded_dest_reg(decoded)
                    if copied_to is not None:
                        tracked.add(copied_to)
            dst = decode_inst_destination(inst, ikb)
            if dst is None:
                continue
            dst_name = _reg_name(dst[0], dst[1])
            if dst_name in tracked and dst_name != copied_to:
                tracked.discard(dst_name)
                if not tracked:
                    return

    block = blocks.get(call.block)
    if block is None:
        return ()
    after_call: list[Instruction] = []
    past_call = False
    for inst in block.instructions:
        if past_call:
            after_call.append(inst)
        if inst.offset == call.addr:
            past_call = True
    _scan(after_call)
    for xref in block.xrefs:
        if xref.type != "fallthrough":
            continue
        ft_block = blocks.get(xref.dst)
        if ft_block is None:
            break
        _scan(ft_block.instructions)
        for xref2 in ft_block.xrefs:
            if xref2.type not in ("fallthrough", "branch"):
                continue
            ft2 = blocks.get(xref2.dst)
            if ft2 is not None:
                _scan(ft2.instructions)
        break
    return tuple(offsets)


def build_app_named_bases(blocks: dict[int, BasicBlock],
                          lib_calls: list[LibraryCall],
                          code: bytes,
                          os_kb: OsKb,
                          platform: PlatformState | None = None
                          ) -> dict[int, str]:
    """Map app-relative slots/regions to named opened bases."""
    result: dict[int, str] = {}
    for call in lib_calls:
        block = blocks.get(call.block)
        if block is None:
            continue
        if call.library == "exec.library" and call.function == "OpenDevice":
            io_seed = _find_region_seed(block, call.addr, "a1", "IO", os_kb, platform)
            if io_seed is None:
                continue
            _seed_offset, _seed_reg, region = io_seed
            if region.provenance.address_space != MemoryRegionAddressSpace.APP:
                continue
            _base_register, displacement = require_base_displacement(
                region.provenance, expected_space=MemoryRegionAddressSpace.APP)
            dev_name = _find_string_seed(block, call.addr, "a0", code)
            if dev_name is None:
                continue
            existing = result.get(displacement)
            if existing is not None and existing != dev_name:
                raise ValueError(
                    f"Conflicting device names for IO region {displacement}: "
                    f"{existing!r} vs {dev_name!r}")
            result[displacement] = dev_name
            continue
        if call.library == "unknown":
            continue

        library = os_kb.LIBRARIES.get(call.library)
        if library is None:
            raise KeyError(f"Unknown library {call.library}")
        func = library.functions.get(call.function)
        if func is None:
            raise KeyError(f"Unknown function {call.library}:{call.function}")
        returns_base = func.returns_base
        if returns_base is None or platform is None or platform.app_base is None:
            continue
        base_name = _find_named_base_seed(
            block, call.addr, returns_base.name_reg.lower(), code)
        if base_name is None:
            continue
        store_offsets = _trace_app_return_store_offsets(
            blocks, call, returns_base.base_reg.lower(), platform.app_base.reg_num)
        for offset in store_offsets:
            existing = result.get(offset)
            if existing is not None and existing != base_name:
                raise ValueError(
                    f"Conflicting base names for app slot {offset}: "
                    f"{existing!r} vs {base_name!r}")
            result[offset] = base_name
    return result


def _find_app_slot_seed(block: BasicBlock, call_addr: int, reg_name: str, base_reg: int) -> int | None:
    call_idx = None
    for i, inst in enumerate(block.instructions):
        if inst.offset == call_addr:
            call_idx = i
            break
    if call_idx is None:
        raise ValueError(f"Call ${call_addr:06x} not found in block ${block.start:06x}")
    tracked = reg_name
    for j in range(call_idx - 1, -1, -1):
        inst = block.instructions[j]
        ikb, decoded = _decode_inst(inst)
        dst = decode_inst_destination(inst, ikb)
        dst_name = None if dst is None else _reg_name(dst[0], dst[1])
        if dst_name != tracked:
            continue
        op_type = None if ikb is None else runtime_m68k_analysis.OPERATION_TYPES.get(ikb)
        if op_type == runtime_m68k_analysis.OperationType.MOVE or ikb == "MOVEA":
            offset = _base_disp_operand(decoded.ea_op, base_reg)
            if offset is not None:
                return offset
            src_name = _decoded_source_reg(decoded)
            if src_name is not None:
                tracked = src_name
                continue
        return None
    return None


def _block_containing_instruction(blocks: dict[int, BasicBlock], addr: int) -> BasicBlock | None:
    direct = blocks.get(addr)
    if direct is not None:
        return direct
    for block in blocks.values():
        for inst in block.instructions:
            if inst.offset == addr:
                return block
    return None


def refine_library_calls(blocks: dict[int, BasicBlock],
                         lib_calls: list[LibraryCall],
                         code: bytes,
                         os_kb: OsKb,
                         platform: PlatformState | None = None,
                         target_metadata: TargetMetadata | None = None,
                         region_map: dict[int, dict[str, TypedMemoryRegion]] | None = None) -> list[LibraryCall]:
    """Resolve unknown LVO calls from propagated named-base and app-slot facts."""
    os_kb = build_target_local_os_kb(os_kb, target_metadata)
    lvo_lookup = _build_lvo_lookup(os_kb)
    app_struct_regions: dict[int, TypedMemoryRegion] = {}
    named_bases: dict[int, str] = {}
    base_reg_name: str | None = None
    if platform is not None and platform.app_base is not None:
        app_struct_regions = build_app_struct_regions(blocks, lib_calls, os_kb, platform, target_metadata)
        named_bases = build_app_named_bases(blocks, lib_calls, code, os_kb, platform)
        base_reg_name = _address_reg_name(platform.app_base.reg_num)
    if region_map is None:
        region_map = propagate_typed_memory_regions(
            blocks, lib_calls, code, os_kb, platform, target_metadata
        )
    refined: list[LibraryCall] = []
    for call in lib_calls:
        if call.library != "unknown" or call.lvo is None:
            refined.append(call)
            continue
        resolved_call = None
        region = region_map.get(call.addr, {}).get("a6")
        if region is not None:
            derivation = region.provenance.derivation
            if (
                derivation is not None
                and derivation.kind is MemoryRegionDerivationKind.NAMED_BASE
                and derivation.named_base is not None
            ):
                resolved_call = _resolve_lvo(call.lvo, derivation.named_base, lvo_lookup)
            elif (
                base_reg_name is not None
                and region.struct == "DD"
                and region.provenance.address_space == MemoryRegionAddressSpace.APP
            ):
                base_disp = require_base_displacement(
                    region.provenance, expected_space=MemoryRegionAddressSpace.APP
                )
                if base_disp[0] == base_reg_name:
                    resolved = _resolve_app_struct_field(app_struct_regions, base_disp[1], os_kb)
                    if resolved is not None:
                        region_offset, _parent_region, _field_displacement, field_info = resolved
                        if field_info.field.name == "IO_DEVICE":
                            device_name = named_bases.get(region_offset)
                            if device_name is not None:
                                resolved_call = _resolve_lvo(call.lvo, device_name, lvo_lookup)
        if resolved_call is None and base_reg_name is not None:
            block = _block_containing_instruction(blocks, call.addr)
            if block is None:
                refined.append(call)
                continue
            assert platform is not None and platform.app_base is not None
            slot_offset = _find_app_slot_seed(block, call.addr, "a6", platform.app_base.reg_num)
            if slot_offset is None:
                refined.append(call)
                continue
            base_name = named_bases.get(slot_offset)
            if base_name is None:
                refined.append(call)
                continue
            resolved_call = _resolve_lvo(call.lvo, base_name, lvo_lookup)
        if resolved_call is None:
            refined.append(call)
            continue
        refined.append(LibraryCall(
            addr=call.addr,
            block=call.block,
            owner_sub=call.owner_sub,
            library=resolved_call.library,
            function=resolved_call.function,
            lvo=resolved_call.lvo,
            inputs=resolved_call.inputs,
            output=resolved_call.output,
            no_return=resolved_call.no_return,
            dispatch=call.dispatch,
            os_since=resolved_call.os_since,
            fd_version=resolved_call.fd_version,
        ))
    return refined


def propagate_typed_memory_regions(blocks: dict[int, BasicBlock],
                                   lib_calls: list[LibraryCall],
                                   code: bytes,
                                   os_kb: OsKb,
                                   platform: PlatformState | None = None,
                                   target_metadata: TargetMetadata | None = None,
                                   absolute_pointer_regions: dict[tuple[int, int], TypedMemoryRegion] | None = None,
                                   hunk_index: int = 0,
                                   reloc_target_hunks: dict[int, int] | None = None,
                                   ) -> dict[int, dict[str, TypedMemoryRegion]]:
    """Propagate KB-typed memory regions through register values.

    Seeds regions from struct-typed OS call inputs whose base address can be
    derived from the setup code, then propagates those facts forward through
    the CFG via register copies and overwrites.

    Returns: {inst_offset: {reg_name: TypedMemoryRegion}}
    """
    seed_regions: dict[int, dict[str, RegisterFact]] = {}
    os_kb = build_target_local_os_kb(os_kb, target_metadata)
    output_region_facts = _output_struct_region_facts(lib_calls, os_kb)
    for call in lib_calls:
        block = blocks.get(call.block)
        if not block:
            continue
        for inp in call.inputs:
            if inp.i_struct is None:
                continue
            struct_name = inp.i_struct
            if struct_name not in os_kb.STRUCTS:
                raise KeyError(f"Unknown struct {struct_name}")
            for reg in _input_regs(inp):
                seed = _find_region_seed(
                    block, call.addr, reg.lower(), struct_name, os_kb, platform)
                if seed is None:
                    continue
                seed_offset, seed_reg, region = seed
                seed_regions.setdefault(seed_offset, {})[seed_reg] = RegisterFact(region=region)
    wrapper_seed_regions = _leading_word_wrapper_seed_regions(
        blocks,
        lib_calls,
        code,
    )
    if absolute_pointer_regions is None:
        absolute_pointer_regions = {}
    for seed_offset, seeds in wrapper_seed_regions.items():
        seed_regions.setdefault(seed_offset, {}).update(seeds)
    app_struct_regions = build_app_struct_regions(blocks, lib_calls, os_kb, platform, target_metadata)
    base_app_pointer_regions = build_app_pointer_regions(blocks, lib_calls, code, os_kb, platform, target_metadata)
    app_pointer_regions = dict(base_app_pointer_regions)

    exec_summaries = None if platform is None else platform.summary_cache
    region_summaries: dict[int, RegionSummary] = {}

    max_iterations = max(2, (len(blocks) + len(_call_targets(blocks))) * 2)
    iterations = 0
    while True:
        iterations += 1
        if iterations > max_iterations:
            raise RuntimeError(
                f"Typed memory region propagation did not converge after {max_iterations} iterations")
        block_in: dict[int, dict[str, RegisterFact] | None] = dict.fromkeys(blocks)
        init_fact: dict[str, RegisterFact] = {}
        if platform is not None:
            if platform.app_base is not None:
                reg_num = platform.app_base.reg_num
                concrete_val = platform.app_base.concrete
                init_fact[_address_reg_name(reg_num)] = RegisterFact(concrete=concrete_val)
            if platform.initial_register_regions is not None:
                for reg_name, region in platform.initial_register_regions.items():
                    init_fact.setdefault(reg_name, RegisterFact(region=region))
        worklist: list[int] = []
        for addr, block in blocks.items():
            if block.predecessors:
                continue
            seeded_fact = dict(init_fact)
            if platform is not None and platform.entry_register_regions is not None:
                for reg_name, region in platform.entry_register_regions.get(addr, {}).items():
                    seeded_fact[reg_name] = RegisterFact(region=region)
            if seeded_fact:
                block_in[addr] = seeded_fact
            worklist.append(addr)
        if not worklist:
            worklist = list(blocks)
        facts_by_inst: dict[int, dict[str, TypedMemoryRegion]] = {}

        while worklist:
            block_addr = worklist.pop()
            block = blocks[block_addr]
            current = dict(block_in[block_addr] or {})
            for inst in block.instructions:
                facts_by_inst[inst.offset] = _region_facts(current)

                seeded = seed_regions.get(inst.offset)
                if seeded:
                    current.update(seeded)

                ikb, decoded = _decode_inst(inst)
                dst = decode_inst_destination(inst, ikb)
                dst_name = None if dst is None else _reg_name(dst[0], dst[1])
                if dst_name is not None and not (seeded and dst_name in seeded):
                    _apply_register_update(
                        current,
                        inst,
                        hunk_index,
                        ikb,
                        decoded,
                        dst_name,
                        os_kb,
                        app_struct_regions,
                        app_pointer_regions,
                        absolute_pointer_regions,
                        reloc_target_hunks,
                        platform,
                    )
                _apply_output_struct_region_facts(current, output_region_facts.get(inst.offset))

            call_dst = None
            ft_dst = None
            other_succs: list[int] = []
            for xref in block.xrefs:
                if xref.type == "call":
                    call_dst = xref.dst
                elif xref.type == "fallthrough":
                    ft_dst = xref.dst
                else:
                    other_succs.append(xref.dst)

            if call_dst is not None and call_dst in blocks:
                merged, changed = _merge_register_facts(block_in[call_dst], current, os_kb)
                if changed:
                    block_in[call_dst] = merged
                    worklist.append(call_dst)

            if ft_dst is not None and ft_dst in blocks:
                summary = None
                if exec_summaries is not None and call_dst is not None:
                    summary = exec_summaries.get(call_dst)
                region_summary = None if call_dst is None else region_summaries.get(call_dst)
                fallthrough = _apply_register_fact_summary(
                    current, summary, region_summary, os_kb, platform)
                merged, changed = _merge_register_facts(block_in[ft_dst], fallthrough, os_kb)
                if changed:
                    block_in[ft_dst] = merged
                    worklist.append(ft_dst)

            for succ in other_succs:
                if succ not in blocks:
                    continue
                merged, changed = _merge_register_facts(block_in[succ], current, os_kb)
                if changed:
                    block_in[succ] = merged
                    worklist.append(succ)

        new_region_summaries = _compute_region_summaries(
            blocks, facts_by_inst, exec_summaries)
        new_region_summaries = _augment_region_summaries_with_leading_word_wrapper(
            blocks, lib_calls, new_region_summaries)
        learned_app_pointer_regions = _collect_app_pointer_regions_from_store_facts(
            blocks, facts_by_inst, platform)
        next_app_pointer_regions = _merge_app_pointer_regions(
            base_app_pointer_regions, learned_app_pointer_regions)
        if new_region_summaries == region_summaries and next_app_pointer_regions == app_pointer_regions:
            return facts_by_inst
        region_summaries = new_region_summaries
        app_pointer_regions = next_app_pointer_regions


@dataclass(frozen=True, slots=True)
class ResolvedLibraryCall:
    library: str
    function: str
    lvo: int
    inputs: tuple[OsInput, ...]
    output: OsOutput | None
    no_return: bool
    os_since: str | None
    fd_version: str | None


@dataclass(frozen=True, slots=True)
class LvoLookup:
    by_lib_lvo: dict[tuple[str, int], ResolvedLibraryCall]
    by_lvo: dict[int, tuple[ResolvedLibraryCall, ...]]


def _library_base_from_tag(tag: object) -> str | None:
    return tag.library_base if isinstance(tag, LibraryBaseTag) else None


def _build_lvo_lookup(os_kb: OsKb) -> LvoLookup:
    """Build combined LVO lookup: {(library_name, lvo_offset_int): function_dict}.

    Also builds reverse: {lvo_offset_int: [(library_name, func_name, func_dict)]}
    for when we don't know which library base is in A6.
    """
    by_lib_lvo: dict[tuple[str, int], ResolvedLibraryCall] = {}
    by_lvo: dict[int, list[ResolvedLibraryCall]] = {}
    for lib_name, lib_data in os_kb.LIBRARIES.items():
        for lvo_str, func_name in lib_data.lvo_index.items():
            lvo = int(lvo_str)
            func = lib_data.functions[func_name]
            call = ResolvedLibraryCall(
                library=lib_name,
                function=func_name,
                lvo=lvo,
                inputs=func.inputs,
                output=func.output,
                no_return=func.no_return,
                os_since=func.os_since,
                fd_version=func.fd_version,
            )
            by_lib_lvo[lib_name, lvo] = call
            by_lvo.setdefault(lvo, []).append(call)
    return LvoLookup(
        by_lib_lvo=by_lib_lvo,
        by_lvo={lvo: tuple(calls) for lvo, calls in by_lvo.items()},
    )


def _resolve_lvo(lvo: int, library: str, lvo_lookup: LvoLookup) -> LibraryCall:
    """Resolve an LVO offset to a function in a known library."""
    key = (library, lvo)
    match = lvo_lookup.by_lib_lvo.get(key)
    if match:
        return LibraryCall(
            addr=0,
            block=0,
            library=match.library,
            function=match.function,
            lvo=lvo,
            inputs=match.inputs,
            output=match.output,
            no_return=match.no_return,
            os_since=match.os_since,
            fd_version=match.fd_version,
        )
    raise KeyError(f"Missing KB LVO mapping for {library}:{lvo}")


def _find_sub_entry(block_addr: int, blocks: Mapping[int, BasicBlock],
                    call_targets: set[int]) -> int | None:
    """Walk predecessors to find the containing subroutine entry."""
    visited: set[int] = set()
    work: list[int] = [block_addr]
    while work:
        addr = work.pop()
        if addr in visited:
            continue
        visited.add(addr)
        if addr in call_targets:
            return addr
        blk = blocks.get(addr)
        if blk:
            work.extend(blk.predecessors)
    return None


def identify_library_calls(blocks: Mapping[int, BasicBlock],
                           code: bytes,
                           os_kb: OsKb,
                           exit_states: Mapping[int, tuple[CpuStateLike, MemoryLike]],
                           call_targets: set[int],
                           platform: PlatformState,
                           initial_state: CPUState | None = None,
                           entry_initial_states: Mapping[int, CPUState] | None = None,
                           base_addr: int = 0,
                           ) -> list[LibraryCall]:
    """Identify OS library calls in analyzed code.

    Detects two patterns through the library base register (OS KB):
    1. Displacement EA: JSR d(A6) -- LVO is the displacement
    2. Indexed EA: JSR 0(A6,Dn.w) -- LVO is in the index register,
       resolved per-caller from exit states

    Library identity comes from:
    - Propagated library_base tags on A6 (from exit states)
    - Intra-block ExecBase load detection (MOVEA.L ($N).W,A6)

    EA field positions from M68K KB encodings.  ExecBase address and
    library base register from OS KB.

    Returns typed LibraryCall records.
    """
    os_meta = os_kb.META
    exec_base_addr = os_meta.exec_base_addr.address
    exec_lib_name = os_meta.exec_base_addr.library
    base_mode, base_reg_num = parse_reg_name(
        os_meta.calling_convention.base_reg)
    if base_mode != "an":
        raise ValueError(
            f"calling_convention.base_reg must be An, got {base_mode}")

    lvo_lookup = _build_lvo_lookup(os_kb)

    # App base register concrete value (from init discovery)
    base_info = platform.app_base
    app_base = base_info.concrete if base_info else None

    absw_enc: list[int | None] = runtime_m68k_decode.EA_MODE_ENCODING["absw"]
    disp_enc: list[int | None] = runtime_m68k_decode.EA_MODE_ENCODING["disp"]
    index_enc: list[int | None] = runtime_m68k_decode.EA_MODE_ENCODING["index"]
    addr_mask = runtime_m68k_analysis.ADDR_MASK
    brief_ext: dict[str, tuple[int, int, int]] = runtime_m68k_decode.EA_BRIEF_FIELDS

    movea_kb = find_kb_entry("movea")
    jsr_kb = find_kb_entry("jsr")
    if movea_kb is None:
        raise KeyError("MOVEA not found in M68K KB")
    if jsr_kb is None:
        raise KeyError("JSR not found in M68K KB")

    movea_ea_spec: tuple[tuple[int, int, int], tuple[int, int, int]] | None = runtime_m68k_decode.EA_FIELD_SPECS.get(movea_kb)
    movea_dst_spec: tuple[int, int, int] | None = runtime_m68k_decode.DEST_REG_FIELD.get(movea_kb)
    jsr_ea_spec: tuple[tuple[int, int, int], tuple[int, int, int]] | None = runtime_m68k_decode.EA_FIELD_SPECS.get(jsr_kb)
    if movea_ea_spec is None:
        raise KeyError("MOVEA encoding lacks MODE/REGISTER EA fields")
    if movea_dst_spec is None:
        raise KeyError("MOVEA encoding lacks destination REGISTER field")
    if jsr_ea_spec is None:
        raise KeyError("JSR encoding lacks MODE/REGISTER EA fields")

    movea_mode_f, movea_reg_f = movea_ea_spec
    jsr_mode_f, jsr_reg_f = jsr_ea_spec

    # Build caller map: subroutine_entry -> [(caller_block_addr, caller_inst_addr)]
    caller_map: dict[int, list[tuple[int, int]]] = {}
    for addr, blk in blocks.items():
        for x in blk.xrefs:
            if x.type == "call" and x.dst in call_targets:
                caller_map.setdefault(x.dst, []).append((addr, x.src))

    results = []
    trace_watch_offsets: set[int] = set()
    for block_addr, block in blocks.items():
        if block_addr not in exit_states and not block.is_entry:
            trace_watch_offsets.update(inst.offset for inst in block.instructions)
    traces_by_offset: dict[int, list[InstructionTrace]] | None = None

    def get_traces_by_offset() -> dict[int, list[InstructionTrace]]:
        nonlocal traces_by_offset
        if traces_by_offset is not None:
            return traces_by_offset
        from .m68k_executor import collect_instruction_traces
        traces = collect_instruction_traces(
            dict(blocks),
            code,
            base_addr=base_addr,
            initial_state=initial_state,
            entry_initial_states=entry_initial_states,
            platform=platform,
            summaries=platform.summary_cache,
            watch_offsets=trace_watch_offsets,
        )
        traces_by_offset = {}
        for instruction_trace in traces:
            traces_by_offset.setdefault(
                instruction_trace.instruction.offset, []).append(instruction_trace)
        return traces_by_offset

    def select_trace(inst_offset: int) -> InstructionTrace | None:
        candidates_by_offset = get_traces_by_offset()
        candidates = candidates_by_offset.get(inst_offset)
        if not candidates:
            return None
        known_pre_libs = {
            lib_name
            for trace in candidates
            for lib_name in [_library_base_from_tag(trace.pre_cpu.a[base_reg_num].tag)]
            if lib_name is not None
        }
        if len(known_pre_libs) > 1:
            raise ValueError(
                f"Conflicting A6 library ownership at 0x{inst_offset:X}: {sorted(known_pre_libs)}"
            )
        if known_pre_libs:
            selected_lib = next(iter(known_pre_libs))
            for candidate in candidates:
                if _library_base_from_tag(candidate.pre_cpu.a[base_reg_num].tag) == selected_lib:
                    return candidate
        return candidates[0]

    def uniform_indexed_lvo(
        inst_offset: int,
        idx_mode: str,
        idx_reg: int,
        idx_wl: int,
        base_disp: int,
    ) -> int | None:
        candidates = get_traces_by_offset().get(inst_offset)
        if not candidates:
            return None
        lvos: set[int] = set()
        for candidate in candidates:
            idx_val = candidate.pre_cpu.get_reg(idx_mode, idx_reg)
            if not idx_val.is_known:
                return None
            v = idx_val.concrete
            idx_size = "l" if idx_wl == 1 else "w"
            nbits = runtime_m68k_decode.SIZE_BYTE_COUNT[idx_size] * 8
            mask = (1 << nbits) - 1
            v = v & mask
            if v >= (1 << (nbits - 1)):
                v -= (1 << nbits)
            lvos.add(base_disp + v)
        if len(lvos) != 1:
            return None
        return next(iter(lvos))

    def local_indexed_lvo(
        caller_block_addr: int,
        caller_inst_addr: int,
        idx_mode: str,
        idx_reg: int,
        idx_wl: int,
        base_disp: int,
    ) -> int | None:
        caller_block = blocks.get(caller_block_addr)
        if caller_block is None:
            return None
        imm_val = _find_local_immediate_seed(
            caller_block, caller_inst_addr, idx_mode, idx_reg)
        if imm_val is None:
            return None
        idx_size = "l" if idx_wl == 1 else "w"
        nbits = runtime_m68k_decode.SIZE_BYTE_COUNT[idx_size] * 8
        mask = (1 << nbits) - 1
        v = imm_val & mask
        if v >= (1 << (nbits - 1)):
            v -= (1 << nbits)
        return base_disp + v

    def uniform_pre_library(inst_offset: int) -> str | None:
        candidates = get_traces_by_offset().get(inst_offset)
        if not candidates:
            return None
        libs = {
            lib_name
            for candidate in candidates
            for lib_name in [_library_base_from_tag(candidate.pre_cpu.a[base_reg_num].tag)]
            if lib_name is not None
        }
        if len(libs) > 1:
            raise ValueError(
                f"Conflicting caller A6 library ownership at 0x{inst_offset:X}: {sorted(libs)}"
            )
        if not libs:
            return None
        return next(iter(libs))

    def entry_seed_library(block_addr: int) -> str | None:
        if entry_initial_states is not None:
            entry_state = entry_initial_states.get(block_addr)
            if entry_state is not None:
                return _library_base_from_tag(entry_state.a[base_reg_num].tag)
        if initial_state is not None and block_addr == base_addr:
            return _library_base_from_tag(initial_state.a[base_reg_num].tag)
        return None
    # Deferred: indexed EA calls needing per-caller resolution.
    # List of (block_addr, inst_offset, library, index_reg_mode,
    #          index_reg_num, base_displacement)
    deferred_indexed = []
    deferred_direct = []

    for block_addr in sorted(blocks):
        block = blocks[block_addr]
        if not block.instructions:
            continue
        block_owner_sub = _find_sub_entry(block_addr, blocks, call_targets)
        if block_owner_sub is None:
            block_owner_sub = block_addr

        carried_a6_lib: str | None = entry_seed_library(block_addr)
        base_reg_locally_modified = False

        for inst in block.instructions:
            selected_trace: InstructionTrace | None = None
            inst_offset = inst.offset

            def get_selected_trace(offset: int = inst_offset) -> InstructionTrace | None:
                nonlocal selected_trace
                if selected_trace is None:
                    selected_trace = select_trace(offset)
                return selected_trace

            has_local_state = block_addr in exit_states or block.is_entry
            a6_lib = carried_a6_lib
            if selected_trace is not None:
                traced_a6_lib = _library_base_from_tag(selected_trace.pre_cpu.a[base_reg_num].tag)
                if traced_a6_lib is not None:
                    a6_lib = traced_a6_lib
            ikb = instruction_kb(inst)
            flow_type, _ = instruction_flow(inst)
            if decode_inst_destination(inst, ikb) == ("an", base_reg_num):
                base_reg_locally_modified = True

            # Detect library base load into the base register.
            # 1. MOVEA.L ($N).W,A6 - ExecBase from absolute address
            # 2. MOVEA.L d(An),A6 - library base from tagged memory
            if (runtime_m68k_analysis.OPERATION_TYPES.get(ikb) == runtime_m68k_analysis.OperationType.MOVE
                    and ikb in runtime_m68k_analysis.SOURCE_SIGN_EXTEND
                    and len(inst.raw) >= runtime_m68k_decode.OPWORD_BYTES + 2):
                opcode = struct.unpack_from(">H", inst.raw, 0)[0]
                src_mode = xf(opcode, movea_mode_f)
                src_reg = xf(opcode, movea_reg_f)
                dst_reg = xf(opcode, movea_dst_spec)

                if dst_reg == base_reg_num:
                    carried_a6_lib = None
                    traced = get_selected_trace() if not has_local_state else None
                    if traced is not None:
                        carried_a6_lib = _library_base_from_tag(
                            traced.post_cpu.a[base_reg_num].tag)
                    if (src_mode == absw_enc[0]
                            and src_reg == absw_enc[1]):
                        addr_val = struct.unpack_from(
                            ">h", inst.raw, runtime_m68k_decode.OPWORD_BYTES)[0]
                        addr_val &= addr_mask
                        if addr_val == exec_base_addr:
                            carried_a6_lib = exec_lib_name
                    elif (src_mode == disp_enc[0]
                            and block_addr in exit_states
                            and app_base is not None):
                        disp_val = struct.unpack_from(
                            ">h", inst.raw, runtime_m68k_decode.OPWORD_BYTES)[0]
                        _, blk_mem = exit_states[block_addr]
                        mem_addr = (app_base + disp_val) & addr_mask
                        tag_val = blk_mem.read(mem_addr, "l")
                        carried_a6_lib = _library_base_from_tag(tag_val.tag)

            # Detect library call: JSR through base_reg
            if flow_type != _FLOW_CALL:
                continue
            target = extract_branch_target(inst, inst.offset)
            if target is not None:
                continue  # resolved - not a library call
            if len(inst.raw) < runtime_m68k_decode.OPWORD_BYTES + 2:
                continue

            opcode = struct.unpack_from(">H", inst.raw, 0)[0]
            ea_mode = xf(opcode, jsr_mode_f)
            ea_reg = xf(opcode, jsr_reg_f)
            if not has_local_state:
                traced = get_selected_trace()
                if traced is None:
                    continue
                traced_a6_lib = _library_base_from_tag(
                    traced.pre_cpu.a[base_reg_num].tag)
                if traced_a6_lib is not None:
                    a6_lib = traced_a6_lib

            # Pattern 1: JSR d(A6) - displacement EA, LVO is disp
            if ea_mode == disp_enc[0] and ea_reg == base_reg_num:
                disp = struct.unpack_from(
                    ">h", inst.raw, runtime_m68k_decode.OPWORD_BYTES)[0]
                sub_entry = _find_sub_entry(block_addr, blocks, call_targets)
                callers = () if sub_entry is None else caller_map.get(sub_entry, ())
                if callers and not base_reg_locally_modified:
                    deferred_direct.append((block_addr, inst.offset, disp))
                elif a6_lib:
                    resolved = _resolve_lvo(disp, a6_lib, lvo_lookup)
                    results.append(LibraryCall(
                        addr=inst.offset,
                        block=block_addr,
                        owner_sub=block_owner_sub,
                        library=resolved.library,
                        function=resolved.function,
                        lvo=resolved.lvo,
                        inputs=resolved.inputs,
                        output=resolved.output,
                        no_return=resolved.no_return,
                        dispatch=resolved.dispatch,
                        os_since=resolved.os_since,
                        fd_version=resolved.fd_version,
                    ))
                else:
                    results.append(LibraryCall(
                        addr=inst.offset,
                        block=block_addr,
                        owner_sub=block_owner_sub,
                        library="unknown",
                        function=f"LVO_{-disp}",
                        lvo=disp,
                    ))
                continue

            # Pattern 2: JSR 0(A6,Dn.w) - indexed EA, LVO in index reg
            if ea_mode == index_enc[0] and ea_reg == base_reg_num:
                ext = struct.unpack_from(
                    ">H", inst.raw, runtime_m68k_decode.OPWORD_BYTES)[0]
                idx_da = xf(ext, brief_ext["D/A"])
                idx_reg = xf(ext, brief_ext["REGISTER"])
                idx_wl = xf(ext, brief_ext["W/L"])
                disp_raw = xf(ext, brief_ext["DISPLACEMENT"])
                disp_w = brief_ext["DISPLACEMENT"][2]
                if disp_raw & (1 << (disp_w - 1)):
                    disp_raw -= (1 << disp_w)

                idx_mode = "an" if idx_da == 1 else "dn"

                # Prefer a local immediate seed before paying for trace-based
                # reconstruction.
                lvo = local_indexed_lvo(
                    block_addr, inst.offset, idx_mode, idx_reg, idx_wl, disp_raw)
                if lvo is None:
                    lvo = uniform_indexed_lvo(
                        inst.offset, idx_mode, idx_reg, idx_wl, disp_raw)
                if lvo is not None:
                    if a6_lib:
                        resolved = _resolve_lvo(lvo, a6_lib, lvo_lookup)
                        results.append(LibraryCall(
                            addr=inst.offset,
                            block=block_addr,
                            owner_sub=block_owner_sub,
                            library=resolved.library,
                            function=resolved.function,
                            lvo=resolved.lvo,
                            inputs=resolved.inputs,
                            output=resolved.output,
                            no_return=resolved.no_return,
                            dispatch=resolved.dispatch,
                            os_since=resolved.os_since,
                            fd_version=resolved.fd_version,
                        ))
                    else:
                        resolved = LibraryCall(
                            addr=0,
                            block=0,
                            owner_sub=block_owner_sub,
                            library="unknown",
                            function=f"LVO_{-lvo}",
                            lvo=lvo,
                        )
                        results.append(LibraryCall(
                            addr=inst.offset,
                            block=block_addr,
                            owner_sub=block_owner_sub,
                            library=resolved.library,
                            function=resolved.function,
                            lvo=resolved.lvo,
                            inputs=resolved.inputs,
                            output=resolved.output,
                            no_return=resolved.no_return,
                            dispatch=resolved.dispatch,
                            os_since=resolved.os_since,
                            fd_version=resolved.fd_version,
                        ))
                    continue

                # Defer for per-caller resolution
                deferred_indexed.append((block_addr, inst.offset, a6_lib,
                                         idx_mode, idx_reg, idx_wl, disp_raw))
                continue

    # Per-caller resolution for deferred direct A6 displacement calls.
    for blk_addr, inst_addr, disp in deferred_direct:
        sub_entry = _find_sub_entry(blk_addr, blocks, call_targets)
        if sub_entry is None:
            results.append(LibraryCall(
                addr=inst_addr,
                block=blk_addr,
                owner_sub=blk_addr,
                library="unknown",
                function=f"LVO_{-disp}",
                lvo=disp,
            ))
            continue
        callers = caller_map.get(sub_entry, [])
        resolved_any = False
        for caller_block_addr, caller_inst_addr in callers:
            trace_watch_offsets.add(caller_inst_addr)
            caller_owner_sub = _find_sub_entry(caller_block_addr, blocks, call_targets)
            if caller_owner_sub is None:
                caller_owner_sub = caller_block_addr
            call_lib = uniform_pre_library(caller_inst_addr)
            if call_lib is None:
                continue
            resolved = _resolve_lvo(disp, call_lib, lvo_lookup)
            results.append(LibraryCall(
                addr=caller_inst_addr,
                block=caller_block_addr,
                owner_sub=caller_owner_sub,
                library=resolved.library,
                function=resolved.function,
                lvo=resolved.lvo,
                inputs=resolved.inputs,
                output=resolved.output,
                no_return=resolved.no_return,
                dispatch=inst_addr,
                os_since=resolved.os_since,
                fd_version=resolved.fd_version,
            ))
            resolved_any = True
        if not resolved_any:
            results.append(LibraryCall(
                addr=inst_addr,
                block=blk_addr,
                owner_sub=blk_addr,
                library="unknown",
                function=f"LVO_{-disp}",
                lvo=disp,
            ))

    # Per-caller resolution for deferred indexed-EA calls.
    # The callee block's index register is unknown (joined from
    # multiple callers), but each caller's exit state has the
    # concrete value.
    for (blk_addr, inst_addr, lib, idx_mode, idx_reg,
         idx_wl, base_disp) in deferred_indexed:
        sub_entry = _find_sub_entry(blk_addr, blocks, call_targets)
        if sub_entry is None:
            continue
        callers = caller_map.get(sub_entry, [])
        for caller_block_addr, caller_inst_addr in callers:
            trace_watch_offsets.add(caller_inst_addr)
            caller_owner_sub = _find_sub_entry(caller_block_addr, blocks, call_targets)
            if caller_owner_sub is None:
                caller_owner_sub = caller_block_addr
            lvo = local_indexed_lvo(
                caller_block_addr, caller_inst_addr, idx_mode, idx_reg, idx_wl, base_disp)
            if lvo is None:
                lvo = uniform_indexed_lvo(
                    caller_inst_addr, idx_mode, idx_reg, idx_wl, base_disp)
            if lvo is None:
                continue

            # Resolve library from caller's A6 if callee didn't have it
            call_lib = lib
            if call_lib is None:
                call_lib = uniform_pre_library(caller_inst_addr)
            if call_lib is None:
                continue

            resolved = _resolve_lvo(lvo, call_lib, lvo_lookup)
            results.append(LibraryCall(
                addr=caller_inst_addr,
                block=caller_block_addr,
                owner_sub=caller_owner_sub,
                library=resolved.library,
                function=resolved.function,
                lvo=resolved.lvo,
                inputs=resolved.inputs,
                output=resolved.output,
                no_return=resolved.no_return,
                dispatch=inst_addr,
                os_since=resolved.os_since,
                fd_version=resolved.fd_version,
            ))

    return results


def collect_library_call_site_addrs(blocks: Mapping[int, BasicBlock],
                                    os_kb: OsKb) -> frozenset[int]:
    """Collect unresolved JSR sites that use the OS library base register.

    This is a cheap syntactic filter for per-caller indirect resolution. It
    does not classify libraries or functions; it only identifies call sites
    that are OS-call-shaped and should be excluded from generic indirect-call
    target recovery.
    """
    os_meta = os_kb.META
    base_mode, base_reg_num = parse_reg_name(os_meta.calling_convention.base_reg)
    if base_mode != "an":
        raise ValueError(
            f"calling_convention.base_reg must be An, got {base_mode}")

    jsr_kb = find_kb_entry("jsr")
    if jsr_kb is None:
        raise KeyError("JSR not found in M68K KB")
    jsr_ea_spec: tuple[tuple[int, int, int], tuple[int, int, int]] | None = (
        runtime_m68k_decode.EA_FIELD_SPECS.get(jsr_kb))
    if jsr_ea_spec is None:
        raise KeyError("JSR encoding lacks MODE/REGISTER EA fields")
    jsr_mode_f, jsr_reg_f = jsr_ea_spec
    disp_enc: list[int | None] = runtime_m68k_decode.EA_MODE_ENCODING["disp"]
    index_enc: list[int | None] = runtime_m68k_decode.EA_MODE_ENCODING["index"]

    call_sites: set[int] = set()
    for block in blocks.values():
        for inst in block.instructions:
            flow_type, _ = instruction_flow(inst)
            if flow_type != _FLOW_CALL:
                continue
            if extract_branch_target(inst, inst.offset) is not None:
                continue
            if len(inst.raw) < runtime_m68k_decode.OPWORD_BYTES + 2:
                continue
            opcode = struct.unpack_from(">H", inst.raw, 0)[0]
            ea_mode = xf(opcode, jsr_mode_f)
            ea_reg = xf(opcode, jsr_reg_f)
            if (
                (ea_mode == disp_enc[0] and ea_reg == base_reg_num)
                or (ea_mode == index_enc[0] and ea_reg == base_reg_num)
            ):
                call_sites.add(inst.offset)
    return frozenset(call_sites)

