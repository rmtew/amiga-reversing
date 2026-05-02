from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SymbolOperandMetadata:
    symbol: str


@dataclass(frozen=True, slots=True)
class StructFieldOperandMetadata:
    symbol: str
    owner_struct: str
    field_symbol: str | None = None
    context_name: str | None = None


@dataclass(frozen=True, slots=True)
class AppStructFieldOperandMetadata:
    base_symbol: str
    field_symbol: str | None = None
    owner_struct: str | None = None
    context_name: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterListOperandMetadata:
    registers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RegisterPairOperandMetadata:
    registers: tuple[str, str]


@dataclass(frozen=True, slots=True)
class BitfieldOperandMetadata:
    bitfield: object
    symbol: str | None = None


@dataclass(frozen=True, slots=True)
class IndexedOperandMetadata:
    index_register: str
    index_size: str
    symbol: str | None = None
    owner_struct: str | None = None
    field_symbol: str | None = None
    context_name: str | None = None


@dataclass(frozen=True, slots=True)
class FullIndexedOperandMetadata:
    base_register: str | None
    index_register: str | None
    index_size: str | None
    index_scale: int | None
    memory_indirect: bool
    postindexed: bool
    preindexed: bool
    base_suppressed: bool
    index_suppressed: bool
    base_displacement: int | None
    outer_displacement: int | None
    symbol: str | None = None
    owner_struct: str | None = None
    field_symbol: str | None = None
    context_name: str | None = None


@dataclass(frozen=True, slots=True)
class TypedDataFieldInfo:
    owner_struct: str
    field_symbol: str
    context_name: str | None = None


SemanticOperandMetadata = (
    SymbolOperandMetadata
    | StructFieldOperandMetadata
    | AppStructFieldOperandMetadata
    | RegisterListOperandMetadata
    | RegisterPairOperandMetadata
    | BitfieldOperandMetadata
    | IndexedOperandMetadata
    | FullIndexedOperandMetadata
)


@dataclass(frozen=True)
class SemanticOperand:
    kind: str
    text: str
    value: int | None = None
    register: str | None = None
    base_register: str | None = None
    displacement: int | None = None
    segment_addr: int | None = None
    metadata: SemanticOperandMetadata | None = None


@dataclass(frozen=True, slots=True)
class AppSlotRef:
    symbol: str
    displacement: int
    base_register: str
    operand_index: int
    access: str


@dataclass(frozen=True, slots=True)
class PlatformTypedAccess:
    operand_index: int
    base_register: str
    displacement: int
    field_offset: int
    root_struct_name: str | None
    owner_struct_name: str | None
    field_name: str | None
    field_expr: str
    inherited: bool = False
    nested: bool = False


@dataclass(frozen=True, slots=True)
class PlatformUnresolvedTypedAccess:
    operand_index: int
    base_register: str
    displacement: int
    struct_size: int | None
    root_struct_name: str | None
    classification: str | None = None
    container_candidate_count: int | None = None
    container_struct_name: str | None = None
    container_field_expr: str | None = None
    refinement_applied: bool = False
    refined_struct_name: str | None = None
    type_provenance_kind: str | None = None
    type_provenance_section: int | None = None
    type_provenance_offset: int | None = None


@dataclass(frozen=True)
class ListingRow:
    row_id: str
    kind: str
    text: str
    stable_key: str | None = None
    analysis_generation: str = "full"
    analysis_phase: str | None = None
    section_index: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    storage_address: int | None = None
    runtime_address: int | None = None
    runtime_view_id: int | None = None
    addr: int | None = None
    entity_addr: int | None = None
    verified_state: str | None = None
    bytes: bytes | None = None
    label: str | None = None
    opcode_or_directive: str | None = None
    operation_type: str | None = None
    operand_parts: tuple[SemanticOperand, ...] = ()
    operand_accesses: tuple[str, ...] = ()
    operand_registers: tuple[str | None, ...] = ()
    app_slot_refs: tuple[AppSlotRef, ...] = ()
    typed_accesses: tuple[PlatformTypedAccess, ...] = ()
    unresolved_typed_accesses: tuple[PlatformUnresolvedTypedAccess, ...] = ()
    operand_text: str = ""
    comment_parts: tuple[str, ...] = ()
    comment_text: str = ""
    source_context: RowSourceContext | None = None
    data_class: str | None = None
    structured_data: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class HeaderRowContext:
    section: str


@dataclass(frozen=True, slots=True)
class BlockRowContext:
    kind: str
    hunk_index: int
    verified_state: str | None = None


@dataclass(frozen=True, slots=True)
class AddressRowContext:
    block: int


RowSourceContext = HeaderRowContext | BlockRowContext | AddressRowContext
