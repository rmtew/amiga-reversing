from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import NotRequired, Protocol, TypedDict

from disasm.target_metadata import TargetMetadata
from m68k.analysis import RelocatedSegment
from m68k.indirect_core import IndirectSite
from m68k.instruction_decode import DecodedBitfield
from m68k.m68k_disasm import Instruction
from m68k.m68k_executor import XRef
from m68k.os_calls import (
    CallArgumentAnnotation,
    LibraryCall,
    OsKb,
    PlatformState,
    TypedMemoryRegion,
)


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
    bitfield: DecodedBitfield
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


class DisasmBlockLike(Protocol):
    @property
    def start(self) -> int: ...

    @property
    def end(self) -> int: ...

    @property
    def successors(self) -> Sequence[int]: ...

    @property
    def instructions(self) -> Sequence[Instruction]: ...

    @property
    def predecessors(self) -> Sequence[int]: ...

    @property
    def xrefs(self) -> Sequence[XRef]: ...

    @property
    def is_entry(self) -> bool: ...

    @property
    def is_return(self) -> bool: ...


class EntityRecord(TypedDict):
    addr: str
    type: str
    end: NotRequired[str]
    hunk: NotRequired[int]
    name: NotRequired[str]
    comment: NotRequired[str]
    subtype: NotRequired[str]
    confidence: NotRequired[str]


class EntityPatch(TypedDict, total=False):
    name: str
    comment: str
    type: str
    subtype: str
    confidence: str


class OverridesPayload(TypedDict):
    entities: dict[str, EntityPatch]


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
    hint_blocks: Mapping[int, DisasmBlockLike]
    reloc_map: dict[int, int]
    reloc_target_set: set[int]
    pc_targets: dict[int, str]
    string_addrs: set[int]
    generic_data_label_addrs: set[int]
    jump_table_regions: dict[int, JumpTableRegion]
    jump_table_target_sources: dict[int, tuple[str, ...]]
    labels: dict[int, str]
    string_ranges: dict[int, int] = field(default_factory=dict)
    absolute_labels: dict[int, str] = field(default_factory=dict)
    reserved_absolute_addrs: set[int] = field(default_factory=set)


type InstructionRegionMap = dict[int, dict[str, TypedMemoryRegion]]
type AppStructRegionMap = dict[int, TypedMemoryRegion]
type HardwareBaseRegMap = dict[int, dict[str, int]]


@dataclass
class HunkDisassemblySession:
    hunk_index: int
    code: bytes
    code_size: int
    entities: list[EntityRecord]
    blocks: Mapping[int, DisasmBlockLike]
    hint_blocks: Mapping[int, DisasmBlockLike]
    code_addrs: set[int]
    hint_addrs: set[int]
    reloc_map: dict[int, int]
    reloc_target_set: set[int]
    pc_targets: dict[int, str]
    string_addrs: set[int]
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
    base_addr: int
    code_start: int
    relocated_segments: list[RelocatedSegment]
    reloc_file_offset: int
    reloc_base_addr: int
    addr_comments: dict[int, str] = field(default_factory=dict)
    string_ranges: dict[int, int] = field(default_factory=dict)
    absolute_labels: dict[int, str] = field(default_factory=dict)
    reserved_absolute_addrs: set[int] = field(default_factory=set)
    app_struct_regions: AppStructRegionMap = field(default_factory=dict)
    hardware_base_regs: HardwareBaseRegMap = field(default_factory=dict)
    unresolved_indirects: dict[int, IndirectSite] = field(default_factory=dict)
    lib_calls: tuple[LibraryCall, ...] = field(default_factory=tuple)


@dataclass
class DisassemblySession:
    target_name: str | None
    binary_path: Path
    entities_path: Path
    analysis_cache_path: Path
    output_path: Path | None
    entities: list[EntityRecord]
    hunk_sessions: list[HunkDisassemblySession]
    target_metadata: TargetMetadata | None = None
    source_kind: str | None = None
    raw_address_model: str | None = None
    profile_stages: bool = False
