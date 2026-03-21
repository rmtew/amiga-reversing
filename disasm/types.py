from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

from m68k.instruction_decode import DecodedBitfield
from m68k.analysis import RelocatedSegment
from m68k.indirect_core import IndirectSite
from m68k.os_calls import (CallArgumentAnnotation, LibraryCall, OsKb,
                           PlatformState, TypedMemoryRegion)


@dataclass(frozen=True, slots=True)
class SymbolOperandMetadata:
    symbol: str


@dataclass(frozen=True, slots=True)
class AppStructFieldOperandMetadata:
    base_symbol: str
    field_symbol: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterListOperandMetadata:
    registers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RegisterPairOperandMetadata:
    registers: tuple[str, str]


@dataclass(frozen=True, slots=True)
class BitfieldOperandMetadata:
    bitfield: DecodedBitfield
    symbol: str | None = None


@dataclass(frozen=True, slots=True)
class IndexedOperandMetadata:
    index_register: str
    index_size: str
    symbol: str | None = None


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


SemanticOperandMetadata = (
    dict[str, Any]
    | SymbolOperandMetadata
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
    target_addr: int | None = None
    metadata: SemanticOperandMetadata = field(default_factory=dict)


@dataclass(frozen=True)
class ListingRow:
    row_id: str
    kind: str
    text: str
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
    source_context: "RowSourceContext | None" = None


@dataclass(frozen=True, slots=True)
class HeaderRowContext:
    section: str


@dataclass(frozen=True, slots=True)
class BlockRowContext:
    kind: str
    verified_state: str | None = None


@dataclass(frozen=True, slots=True)
class AddressRowContext:
    block: int


RowSourceContext = HeaderRowContext | BlockRowContext | AddressRowContext


@dataclass(frozen=True, slots=True)
class JumpTableEntryRef:
    entry_addr: int
    target: int


@dataclass(frozen=True, slots=True)
class JumpTableRegion:
    pattern: str
    table_end: int
    entries: tuple[JumpTableEntryRef, ...] = ()
    targets: tuple[int, ...] = ()
    base_addr: int | None = None
    base_label: str | None = None


@dataclass(frozen=True, slots=True)
class HunkMetadata:
    code_addrs: set[int]
    hint_addrs: set[int]
    reloc_map: dict[int, int]
    reloc_target_set: set[int]
    pc_targets: dict[int, str]
    string_addrs: set[int]
    core_absolute_targets: set[int]
    jump_table_regions: dict[int, JumpTableRegion]
    jump_table_target_sources: dict[int, tuple[str, ...]]
    labels: dict[int, str]


InstructionRegionMap: TypeAlias = dict[int, dict[str, TypedMemoryRegion]]
AppStructRegionMap: TypeAlias = dict[int, TypedMemoryRegion]


@dataclass
class HunkDisassemblySession:
    hunk_index: int
    code: bytes
    code_size: int
    entities: list[dict]
    blocks: dict
    hint_blocks: dict
    code_addrs: set[int]
    hint_addrs: set[int]
    reloc_map: dict[int, int]
    reloc_target_set: set[int]
    pc_targets: dict[int, str]
    string_addrs: set[int]
    core_absolute_targets: set[int]
    labels: dict[int, str]
    jump_table_regions: dict[int, JumpTableRegion]
    jump_table_target_sources: dict[int, tuple[str, ...]]
    region_map: InstructionRegionMap
    lvo_equs: dict[str, dict[int, str]]
    lvo_substitutions: dict[int, tuple[str, str]]
    arg_equs: dict[str, int]
    arg_substitutions: dict[int, tuple[str, str]]
    app_offsets: dict[int, str]
    arg_annotations: dict[int, CallArgumentAnnotation]
    data_access_sizes: dict[int, int]
    platform: PlatformState
    os_kb: OsKb
    fixed_abs_addrs: set[int]
    base_addr: int
    code_start: int
    relocated_segments: list[RelocatedSegment]
    reloc_file_offset: int
    reloc_base_addr: int
    app_struct_regions: AppStructRegionMap = field(default_factory=dict)
    unresolved_indirects: dict[int, IndirectSite] = field(default_factory=dict)


@dataclass
class DisassemblySession:
    target_name: str | None
    binary_path: Path
    entities_path: Path
    analysis_cache_path: Path
    output_path: Path | None
    entities: list[dict]
    hunk_sessions: list[HunkDisassemblySession]
    profile_stages: bool = False
