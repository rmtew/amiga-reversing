from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, NamedTuple, TypedDict, TypeAlias


FieldSpec: TypeAlias = tuple[int, int, int]
RawFieldSpec: TypeAlias = tuple[str, int, int, int]
FieldMap: TypeAlias = dict[str, FieldSpec]
EncodingMask: TypeAlias = tuple[int, int]
FieldMaps: TypeAlias = tuple[dict[str, FieldMap], ...]
RawFieldMaps: TypeAlias = tuple[dict[str, tuple[RawFieldSpec, ...]], ...]
BitField: TypeAlias = FieldSpec
AsmSizeEncoding: TypeAlias = tuple[int | None, int | None, int | None]
DisasmSizeEncoding: TypeAlias = tuple[int | None, int | None, int | None, int | None]
ShiftFieldInfo: TypeAlias = tuple[FieldSpec, tuple[str | None, ...], int | None]
RmFieldInfo: TypeAlias = tuple[int, tuple[str | None, ...]]
BranchInlineDisplacement: TypeAlias = tuple[str, FieldSpec, int, int, int, int]
BranchExtensionDisplacement: TypeAlias = tuple[int, int]
ConditionFamily: TypeAlias = tuple[str, str, tuple[str, ...], bool, tuple[str, ...]]
DirectionVariant: TypeAlias = tuple[FieldSpec, str, tuple[str, ...], dict[int, str]]
ImmediateRange: TypeAlias = tuple[str | None, int | None, bool, int | None, int | None, int | None]
BitModulus: TypeAlias = tuple[int, bool]
EaModeTable: TypeAlias = tuple[str, dict[int, tuple[str, ...]]]
OperandModeTable: TypeAlias = tuple[str, dict[int, tuple[str, ...]]]
ComputeFormula: TypeAlias = tuple[str, tuple[str | int, ...], tuple[int, int] | None, tuple[int, int] | None, tuple[tuple[str, int], ...], str | None]
SpEffect: TypeAlias = tuple[str, int | None, str | None]
BoundsCheck: TypeAlias = tuple[str, int, int, str | None, bool, bool] | None
MoveFields: TypeAlias = tuple[FieldSpec, FieldSpec, FieldSpec, FieldSpec]
DirectionFormValue: TypeAlias = tuple[str, tuple[int, ...]]


class AsmCcParam(TypedDict, total=False):
    prefix: str
    field_bits: int
    excluded: list[str]


class AsmOpmodeEntry(TypedDict, total=False):
    opmode: int
    size: str | None
    operation: str
    description: str
    ea_is_source: bool | None
    source: str | None
    destination: str | None
    rx_mode: str | None
    ry_mode: str | None


class RuntimeCcFlagSpec(TypedDict, total=False):
    rule: str
    zero_count: str
    bit: int


class OpmodeEntry(NamedTuple):
    size: str | None
    description: str | None
    ea_is_source: bool | None
    source: str | None
    destination: str | None
    rx_mode: str | None
    ry_mode: str | None

CcLookupFamily: TypeAlias = tuple[str, tuple[str, ...], bool]
PrimaryDataSize: TypeAlias = tuple[str, int, int, int]
ShiftVariantBehavior: TypeAlias = tuple[str, str, str, bool]
CcrValue: TypeAlias = int | None
CcrState: TypeAlias = Mapping[str, CcrValue]
KnownCcrState: TypeAlias = Mapping[str, int]
PredictedCcrState: TypeAlias = dict[str, CcrValue]
RuntimeCcSemantics: TypeAlias = Mapping[str, RuntimeCcFlagSpec]


class MnemonicInstructionRecord(TypedDict):
    mnemonic: str


class ComputeInstructionRecord(MnemonicInstructionRecord, total=False):
    cc_semantics: RuntimeCcSemantics
    overflow_undefined_flags: list[str]


class CpuHierarchy(TypedDict):
    order: list[str]
    aliases: dict[str, str]


class HunkExtTypeAndLenPacking(TypedDict):
    type_bits: list[int]
    type_width: int
    name_len_bits: list[int]
    name_len_width: int
    citation: str


class HunkMeta(TypedDict, total=False):
    sources: list[dict[str, object]]
    note: str
    longword_bytes: int
    endianness: str
    hunk_type_id_mask: int
    size_longs_mask: int
    mem_flags_shift: int
    ext_type_and_len_packing: HunkExtTypeAndLenPacking
    load_file_citation: str


class HunkTypeDef(TypedDict, total=False):
    id: int
    description: str
    notes: str
    alias_of: str


class MemoryFlagDef(TypedDict):
    bit: int
    description: str


class MemoryTypeCodeDef(TypedDict):
    name: str
    description: str


class ExtTypeCategoryDef(TypedDict, total=False):
    definition_range: list[int]
    reference_range: list[int]
    boundary: int
    citation: str


class CompatibilityNote(TypedDict):
    topic: str
    text: str
    applies_to: list[str]


class RelocFieldDef(TypedDict, total=False):
    name: str
    type: str
    note: str
    repeat_until_zero: bool
    repeat_per_count: bool


class RelocFormatDef(TypedDict):
    description: str
    fields: list[RelocFieldDef]


class HunkContentFormatDef(TypedDict):
    description: str
    citation: str


class HardwareRegisterDef(TypedDict):
    symbol: str
    aliases: tuple[str, ...]
    family: str
    include: str | None
    base_symbol: str | None
    offset: int
