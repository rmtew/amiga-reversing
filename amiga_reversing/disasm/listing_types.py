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


@dataclass(frozen=True)
class ListingRow:
    row_id: str
    kind: str
    text: str
    stable_key: str | None = None
    analysis_generation: str = "full"
    addr: int | None = None
    entity_addr: int | None = None
    verified_state: str | None = None
    bytes: bytes | None = None
    label: str | None = None
    opcode_or_directive: str | None = None
    operand_parts: tuple[SemanticOperand, ...] = ()
    operand_text: str = ""
    comment_parts: tuple[str, ...] = ()
    comment_text: str = ""
    source_context: RowSourceContext | None = None
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
