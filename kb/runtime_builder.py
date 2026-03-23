"""Build runtime-oriented knowledge artifacts from canonical JSON KB files."""

from __future__ import annotations

import argparse
import json
import pprint
import re
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Literal, TypedDict, TypeAlias, cast

from m68k_kb.runtime_types import (
    BitModulus,
    BoundsCheck,
    BranchExtensionDisplacement,
    BranchInlineDisplacement,
    CompatibilityNote,
    ComputeFormula,
    ConditionFamily,
    CpuHierarchy,
    DirectionFormValue,
    DirectionVariant,
    EncodingMask,
    ExtTypeCategoryDef,
    FieldMap,
    FieldSpec,
    HunkContentFormatDef,
    HunkMeta,
    HunkTypeDef,
    ImmediateRange,
    MemoryFlagDef,
    MemoryTypeCodeDef,
    MoveFields,
    OperandModeTable,
    OpmodeEntry,
    PrimaryDataSize,
    RawFieldSpec,
    RelocFormatDef,
    ShiftVariantBehavior,
    SpEffect,
)
from kb.schemas import (
    M68kCcParameterized,
    M68kCcTestDefinition,
    M68kConditionFamilyEntry,
    M68kConstraints,
    M68kEncoding,
    HardwareSymbolsPayload,
    HunkFormatPayload,
    M68kField,
    M68kInstruction,
    M68kInstructionsPayload,
    M68kMeta,
    M68kOpmodeEntry,
    NamingPattern,
    NamingRulesMeta,
    NamingRulesPayload,
    OsConstant,
    OsFunction,
    OsInput,
    OsMeta,
    OsOutput,
    OsReferencePayload,
    OsStructDef,
    OsStructField,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
RUNTIME_PY_DIR = PROJECT_ROOT / "m68k_kb"


JsonObject: TypeAlias = dict[str, object]
RawFieldMap: TypeAlias = dict[str, tuple[RawFieldSpec, ...]]
CcFamilyRuntime: TypeAlias = tuple[str, M68kCcParameterized]
DerivedCcFamilyRuntime: TypeAlias = tuple[str, tuple[str, ...], bool]


class ShiftFieldsData(TypedDict):
    dr_field: FieldSpec
    dr_values: dict[int, str]
    zero_means: int | None


class RuntimeM68kMeta(TypedDict):
    asm_syntax_index: dict[str, str]
    cc_aliases: dict[str, str]
    cc_test_definitions: dict[str, M68kCcTestDefinition]
    ccr_bit_positions: dict[str, int]
    condition_codes: list[str]
    condition_families: list[M68kConditionFamilyEntry]
    cpu_hierarchy: CpuHierarchy
    default_operand_size: str
    ea_brief_ext_word: list[M68kField]
    ea_full_ext_bd_size: dict[str, str]
    ea_full_ext_word: list[M68kField]
    ea_mode_encoding: dict[str, list[int]]
    ea_mode_sizes: dict[str, list[str]]
    immediate_routing: dict[str, str]
    movem_reg_masks: dict[str, dict[str, int]]
    opword_bytes: int
    pmmu_condition_codes: list[str]
    register_aliases: dict[str, str]
    size_byte_count: dict[str, int]
    _cc_families: dict[str, DerivedCcFamilyRuntime]
    _asm_mnemonic_index: dict[str, str]
    _num_data_regs: int
    _num_addr_regs: int
    _sp_reg_num: int


class RuntimeM68kTables(TypedDict):
    mnemonic_index: dict[str, tuple[str, ...]]
    encoding_counts: dict[str, int]
    encoding_masks: tuple[dict[str, EncodingMask], ...]
    fixed_opcodes: dict[int, str]
    ext_field_names: dict[str, tuple[str, ...]]
    field_maps: tuple[dict[str, FieldMap], ...]
    raw_fields: tuple[RawFieldMap, ...]
    ea_brief_fields: dict[str, FieldSpec]
    size_encodings_asm: dict[str, dict[str, int]]
    size_encodings_disasm: dict[str, dict[int, int]]
    cc_families: dict[str, CcFamilyRuntime]
    immediate_ranges: dict[str, ImmediateRange]
    compute_formulas: dict[str, ComputeFormula]
    bounds_checks: dict[str, BoundsCheck]
    sp_effects: dict[str, tuple[SpEffect, ...]]
    sp_effects_complete: tuple[str, ...]
    implicit_operands: dict[str, str]
    bit_moduli: dict[str, BitModulus]
    rotate_extra_bits: dict[str, int]
    signed_results: dict[str, bool]
    instruction_sizes: dict[str, tuple[str, ...]]
    operation_types: dict[str, str | None]
    operation_classes: dict[str, str | None]
    source_sign_extend: tuple[str, ...]
    shift_count_moduli: dict[str, int]
    opmode_tables_list: dict[str, list[M68kOpmodeEntry]]
    opmode_tables_by_value: dict[str, dict[int, OpmodeEntry]]
    form_operand_types: dict[str, tuple[tuple[str, ...], ...]]
    form_flags_020: dict[str, tuple[bool, ...]]
    primary_data_sizes: dict[str, PrimaryDataSize]
    ea_mode_tables: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]]
    an_sizes: dict[str, tuple[str, ...]]
    operand_mode_tables: dict[str, OperandModeTable]
    direction_variants: dict[str, DirectionVariant]
    register_fields: dict[str, tuple[FieldSpec, ...]]
    dest_reg_field: dict[str, FieldSpec]
    bf_mnemonics: tuple[str, ...]
    bitop_names: tuple[dict[int, str], FieldSpec]
    imm_names: tuple[dict[int, str], FieldSpec]
    shift_names: dict[int, str]
    shift_type_fields: tuple[FieldSpec, FieldSpec]
    shift_fields: ShiftFieldsData
    rm_field: dict[str, tuple[int, dict[int, str]]]
    addq_zero_means: int | None
    control_registers: dict[int, str]
    processor_mins: dict[str, str]
    flow_types: dict[str, str]
    flow_conditional: dict[str, bool]
    condition_families: tuple[ConditionFamily, ...]
    branch_inline_displacements: dict[str, BranchInlineDisplacement]
    branch_extension_displacements: dict[str, BranchExtensionDisplacement]
    move_fields: MoveFields
    movem_fields: dict[str, FieldSpec]
    cpid_field: tuple[int, int]
    asm_syntax_index: dict[tuple[str, tuple[str, ...]], str]
    special_operand_types: tuple[str, ...]
    uses_labels: dict[str, bool]
    direction_form_values: dict[str, DirectionFormValue]
    shift_variant_behaviors: dict[str, tuple[ShiftVariantBehavior, ...]]
    processor_020_variants: dict[str, frozenset[str]]


class RuntimeInstruction(TypedDict):
    mnemonic: str


class RuntimeM68kPayload(TypedDict):
    instructions: list[RuntimeInstruction]
    meta: RuntimeM68kMeta
    tables: RuntimeM68kTables


class M68kDecodeRuntimePayload(TypedDict):
    OPWORD_BYTES: int
    ALIGN_MASK: int
    DEFAULT_OPERAND_SIZE: str
    SIZE_BYTE_COUNT: dict[str, int]
    EA_MODE_ENCODING: dict[str, list[int]]
    REG_INDIRECT_MODES: tuple[str, ...]
    MOVEM_REG_MASKS: dict[str, dict[str, int]]
    SP_REG_NUM: int
    NUM_DATA_REGS: int
    NUM_ADDR_REGS: int
    EA_BRIEF_FIELDS: dict[str, FieldSpec]
    EA_FULL_FIELDS: dict[str, FieldSpec]
    EA_FULL_BD_SIZE: dict[str, str]
    ENCODING_COUNTS: dict[str, int]
    ENCODING_MASKS: tuple[dict[str, EncodingMask], ...]
    FIELD_MAPS: tuple[dict[str, FieldMap], ...]
    RAW_FIELDS: tuple[RawFieldMap, ...]
    EA_FIELD_SPECS: dict[str, tuple[FieldSpec, FieldSpec]]
    EXT_FIELD_NAMES: dict[str, tuple[str, ...]]
    FORM_OPERAND_TYPES: dict[str, tuple[tuple[str, ...], ...]]
    OPERATION_TYPES: dict[str, str | None]
    SOURCE_SIGN_EXTEND: tuple[str, ...]
    OPMODE_TABLES_BY_VALUE: dict[str, dict[int, OpmodeEntry]]
    OPERAND_MODE_TABLES: dict[str, OperandModeTable]
    EA_MODE_TABLES: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]]
    AN_SIZES: dict[str, tuple[str, ...]]
    IMMEDIATE_RANGES: dict[str, ImmediateRange]
    REGISTER_FIELDS: dict[str, tuple[FieldSpec, ...]]
    DEST_REG_FIELD: dict[str, FieldSpec]
    DIRECTION_VARIANTS: dict[str, DirectionVariant]
    SHIFT_FIELDS: ShiftFieldsData
    RM_FIELD: dict[str, tuple[int, dict[int, str]]]
    CONTROL_REGISTERS: dict[int, str]
    MOVE_FIELDS: MoveFields
    MOVEM_FIELDS: dict[str, FieldSpec]
    CPID_FIELD: tuple[int, int]


class M68kDisasmRuntimePayload(TypedDict):
    MNEMONIC_INDEX: dict[str, tuple[str, ...]]
    ENCODING_COUNTS: dict[str, int]
    ENCODING_MASKS: tuple[dict[str, EncodingMask], ...]
    FIXED_OPCODES: dict[int, str]
    EXT_FIELD_NAMES: dict[str, tuple[str, ...]]
    FIELD_MAPS: tuple[dict[str, FieldMap], ...]
    RAW_FIELDS: tuple[RawFieldMap, ...]
    FORM_OPERAND_TYPES: dict[str, tuple[tuple[str, ...], ...]]
    EA_BRIEF_FIELDS: dict[str, FieldSpec]
    MOVEM_REG_MASKS: dict[str, dict[str, int]]
    DEST_REG_FIELD: dict[str, FieldSpec]
    BF_MNEMONICS: tuple[str, ...]
    BITOP_NAMES: tuple[dict[int, str], FieldSpec]
    IMM_NAMES: tuple[dict[int, str], FieldSpec]
    SHIFT_NAMES: dict[int, str]
    SHIFT_TYPE_FIELDS: tuple[FieldSpec, FieldSpec]
    SHIFT_FIELDS: ShiftFieldsData
    RM_FIELD: dict[str, tuple[int, dict[int, str]]]
    ADDQ_ZERO_MEANS: int | None
    CONTROL_REGISTERS: dict[int, str]
    SIZE_ENCODINGS_DISASM: dict[str, dict[int, int]]
    INSTRUCTION_SIZES: dict[str, tuple[str, ...]]
    OPERATION_TYPES: dict[str, str | None]
    OPERATION_CLASSES: dict[str, str | None]
    SOURCE_SIGN_EXTEND: tuple[str, ...]
    SHIFT_COUNT_MODULI: dict[str, int]
    PROCESSOR_MINS: dict[str, str]
    OPMODE_TABLES_BY_VALUE: dict[str, dict[int, OpmodeEntry]]
    CONDITION_FAMILIES: tuple[ConditionFamily, ...]
    CONDITION_CODES: tuple[str, ...]
    CPU_HIERARCHY: CpuHierarchy
    PMMU_CONDITION_CODES: tuple[str, ...]
    DEFAULT_OPERAND_SIZE: str
    MOVE_FIELDS: MoveFields
    CPID_FIELD: tuple[int, int]


class M68kAsmRuntimePayload(TypedDict):
    ENCODING_COUNTS: dict[str, int]
    ENCODING_MASKS: tuple[dict[str, EncodingMask], ...]
    FIELD_MAPS: tuple[dict[str, FieldMap], ...]
    RAW_FIELDS: tuple[RawFieldMap, ...]
    LOOKUP_UPPER: dict[str, str]
    EA_MODE_ENCODING: dict[str, list[int]]
    EA_BRIEF_FIELDS: dict[str, FieldSpec]
    SIZE_BYTE_COUNT: dict[str, int]
    CONDITION_CODES: tuple[str, ...]
    CC_ALIASES: dict[str, str]
    MOVEM_REG_MASKS: dict[str, dict[str, int]]
    IMMEDIATE_ROUTING: dict[str, str]
    SIZE_ENCODINGS_ASM: dict[str, dict[str, int]]
    INSTRUCTION_SIZES: dict[str, tuple[str, ...]]
    OPERATION_TYPES: dict[str, str | None]
    SOURCE_SIGN_EXTEND: tuple[str, ...]
    OPMODE_TABLES_LIST: dict[str, list[M68kOpmodeEntry]]
    FORM_OPERAND_TYPES: dict[str, tuple[tuple[str, ...], ...]]
    FORM_FLAGS_020: dict[str, tuple[bool, ...]]
    EA_MODE_TABLES: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]]
    CC_FAMILIES: dict[str, CcFamilyRuntime]
    IMMEDIATE_RANGES: dict[str, ImmediateRange]
    DIRECTION_VARIANTS: dict[str, DirectionVariant]
    BRANCH_INLINE_DISPLACEMENTS: dict[str, BranchInlineDisplacement]
    AN_SIZES: dict[str, tuple[str, ...]]
    USES_LABELS: dict[str, bool]
    DIRECTION_FORM_VALUES: dict[str, DirectionFormValue]
    SPECIAL_OPERAND_TYPES: tuple[str, ...]
    ASM_SYNTAX_INDEX: dict[tuple[str, tuple[str, ...]], str]


class M68kAnalysisRuntimePayload(TypedDict):
    OPWORD_BYTES: int
    DEFAULT_OPERAND_SIZE: str
    SIZE_BYTE_COUNT: dict[str, int]
    EA_MODE_ENCODING: dict[str, list[int]]
    EA_REVERSE: dict[tuple[int, int], str]
    EA_BRIEF_FIELDS: dict[str, FieldSpec]
    EA_MODE_SIZES: dict[str, list[str]]
    MOVEM_REG_MASKS: dict[str, dict[str, int]]
    CC_TEST_DEFINITIONS: dict[str, tuple[int, str]]
    CC_ALIASES: dict[str, str]
    REGISTER_ALIASES: dict[str, str]
    NUM_DATA_REGS: int
    NUM_ADDR_REGS: int
    SP_REG_NUM: int
    RTS_SP_INC: int
    ADDR_SIZE: str
    ADDR_MASK: int
    CCR_FLAG_NAMES: tuple[str, ...]
    OPERATION_TYPES: dict[str, str | None]
    OPERATION_CLASSES: dict[str, str | None]
    SOURCE_SIGN_EXTEND: tuple[str, ...]
    FLOW_TYPES: dict[str, str]
    FLOW_CONDITIONAL: dict[str, bool]
    BOUNDS_CHECKS: dict[str, BoundsCheck]
    COMPUTE_FORMULAS: dict[str, ComputeFormula]
    SP_EFFECTS: dict[str, tuple[SpEffect, ...]]
    SP_EFFECTS_COMPLETE: tuple[str, ...]
    EA_MODE_TABLES: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]]
    AN_SIZES: dict[str, tuple[str, ...]]
    PROCESSOR_MINS: dict[str, str]
    PROCESSOR_020_VARIANTS: dict[str, frozenset[str]]
    LOOKUP_UPPER: dict[str, str]
    LOOKUP_CANONICAL: dict[str, str]
    LOOKUP_NUMERIC_CC_PREFIXES: dict[str, str]
    LOOKUP_CC_FAMILIES: dict[str, tuple[str, tuple[str, ...], bool]]
    LOOKUP_ASM_MNEMONIC_INDEX: dict[str, str]


class M68kComputeRuntimePayload(TypedDict):
    OPERATION_TYPES: dict[str, str | None]
    COMPUTE_FORMULAS: dict[str, ComputeFormula]
    IMPLICIT_OPERANDS: dict[str, str]
    SP_EFFECTS: dict[str, tuple[SpEffect, ...]]
    PRIMARY_DATA_SIZES: dict[str, PrimaryDataSize]


class M68kExecutorRuntimePayload(TypedDict):
    FIELD_MAPS: tuple[dict[str, FieldMap], ...]
    RAW_FIELDS: tuple[RawFieldMap, ...]
    OPERAND_MODE_TABLES: dict[str, OperandModeTable]
    REGISTER_FIELDS: dict[str, tuple[FieldSpec, ...]]
    RM_FIELD: dict[str, tuple[int, dict[int, str]]]
    IMPLICIT_OPERANDS: dict[str, str]
    OPMODE_TABLES_BY_VALUE: dict[str, dict[int, OpmodeEntry]]
    MOVEM_FIELDS: dict[str, FieldSpec]
    IMMEDIATE_RANGES: dict[str, ImmediateRange]
    DEST_REG_FIELD: dict[str, FieldSpec]
    OPERATION_TYPES: dict[str, str | None]
    OPERATION_CLASSES: dict[str, str | None]
    SOURCE_SIGN_EXTEND: tuple[str, ...]
    BOUNDS_CHECKS: dict[str, BoundsCheck]
    BIT_MODULI: dict[str, BitModulus]
    SHIFT_COUNT_MODULI: dict[str, int]
    ROTATE_EXTRA_BITS: dict[str, int]
    DIRECTION_VARIANTS: dict[str, DirectionVariant]
    SHIFT_FIELDS: tuple[FieldSpec, tuple[str | None, ...], int | None]
    SHIFT_VARIANT_BEHAVIORS: dict[str, tuple[ShiftVariantBehavior, ...]]
    PRIMARY_DATA_SIZES: dict[str, PrimaryDataSize]
    SIGNED_RESULTS: dict[str, bool]
    BRANCH_INLINE_DISPLACEMENTS: dict[str, BranchInlineDisplacement]
    BRANCH_EXTENSION_DISPLACEMENTS: dict[str, BranchExtensionDisplacement]


class NamingRuntimePayload(TypedDict):
    META: NamingRulesMeta
    PATTERNS: list[NamingPattern]
    TRIVIAL_FUNCTIONS: list[str]
    GENERIC_PREFIX: str


class BranchInlineDisplacementInfo(TypedDict):
    kind: Literal["inline_or_extension"]
    field_name: str
    field: FieldSpec
    word_signal: int
    long_signal: int
    word_bytes: int
    long_bytes: int


class BranchExtensionDisplacementInfo(TypedDict):
    kind: Literal["extension_only"]
    offset_bytes: int
    bytes: int


BranchDisplacementInfo: TypeAlias = BranchInlineDisplacementInfo | BranchExtensionDisplacementInfo


class HunkRuntimePayload(TypedDict):
    META: HunkMeta
    HUNK_TYPES: dict[str, HunkTypeDef]
    EXT_TYPES: dict[str, HunkTypeDef]
    MEMORY_FLAGS: dict[str, MemoryFlagDef]
    MEMORY_TYPE_CODES: dict[str, MemoryTypeCodeDef]
    EXT_TYPE_CATEGORIES: ExtTypeCategoryDef
    COMPATIBILITY_NOTES: list[CompatibilityNote]
    RELOC_FORMATS: dict[str, RelocFormatDef]
    RELOCATION_SEMANTICS: dict[str, tuple[int, str]]
    HUNK_CONTENT_FORMATS: dict[str, HunkContentFormatDef]


class OsRuntimeLibrary(TypedDict):
    lvo_index: dict[str, str]
    functions: dict[str, OsFunction]


class OsRuntimePayload(TypedDict):
    META: OsMeta
    STRUCTS: dict[str, OsStructDef]
    CONSTANTS: dict[str, OsConstant]
    LIBRARIES: dict[str, OsRuntimeLibrary]


class HardwareRuntimeRegisterDef(TypedDict):
    symbol: str
    aliases: tuple[str, ...]
    family: str
    include: str
    base_symbol: str
    offset: int


class HardwareRuntimePayload(TypedDict):
    META: dict[str, object]
    REGISTER_DEFS: dict[int, HardwareRuntimeRegisterDef]


def _load_json(name: str) -> JsonObject:
    with open(KNOWLEDGE_DIR / name, encoding="utf-8") as handle:
        return cast(JsonObject, json.load(handle))


def _load_m68k_instructions_payload() -> M68kInstructionsPayload:
    return cast(M68kInstructionsPayload, _load_json("m68k_instructions.json"))


def _load_os_reference_payload() -> OsReferencePayload:
    return cast(OsReferencePayload, _load_json("amiga_os_reference.json"))


def _load_hunk_format_payload() -> HunkFormatPayload:
    return cast(HunkFormatPayload, _load_json("amiga_hunk_format.json"))


def _load_hardware_symbols_payload() -> HardwareSymbolsPayload:
    return cast(HardwareSymbolsPayload, _load_json("amiga_hw_symbols.json"))


def _load_naming_rules_payload() -> NamingRulesPayload:
    return cast(NamingRulesPayload, _load_json("naming_rules.json"))


def _write_python(path: Path, variable: str, payload: object, *, header: str) -> None:
    rendered = pprint.pformat(payload, width=100, sort_dicts=False)
    text = (
        '"""' + header + '"""\n\n'
        f"{variable} = {rendered}\n"
    )
    path.write_text(text, encoding="utf-8")


def _render_py(payload: object) -> str:
    return pprint.pformat(payload, width=100, sort_dicts=False)


def _render_typed_assignment(name: str, value: object, annotation: str) -> str:
    return f"{name}: {annotation} = {_render_py(value)}"


def _render_frozenset(values: frozenset[str]) -> str:
    rendered = ", ".join(repr(value) for value in sorted(values))
    if len(values) == 1:
        rendered += ","
    return f"frozenset(({rendered}))"


def _render_processor_020_variants(table: dict[str, frozenset[str]]) -> str:
    rendered = ",\n ".join(
        f"{mnemonic!r}: {_render_frozenset(variants)}"
        for mnemonic, variants in sorted(table.items())
    )
    return "{%s}" % rendered


def _render_opmode_tables_by_value(table: dict[str, dict[int, OpmodeEntry]]) -> str:
    rendered_entries: list[str] = []
    for mnemonic, entries in table.items():
        rendered_inner = ",\n  ".join(
            f"{opmode!r}: {entry!r}"
            for opmode, entry in entries.items()
        )
        rendered_entries.append(f"{mnemonic!r}: {{{rendered_inner}}}")
    return "{%s}" % (",\n ".join(rendered_entries))


def _write_runtime_constants_python(path: Path, payload: Mapping[str, object], *, header: str) -> None:
    lines = ['"""' + header + '"""', "", "from __future__ import annotations", ""]
    if "REGISTER_DEFS" in payload:
        lines.extend([
            "from .runtime_types import HardwareRegisterDef",
            "",
        ])
    runtime_type_imports: list[str] = []
    if "OPMODE_TABLES_BY_VALUE" in payload:
        runtime_type_imports.append("OpmodeEntry")
    if "LOOKUP_CC_FAMILIES" in payload:
        runtime_type_imports.append("CcLookupFamily")
    if "SIZE_ENCODINGS_ASM" in payload:
        runtime_type_imports.append("AsmSizeEncoding")
    if "SIZE_ENCODINGS_DISASM" in payload:
        runtime_type_imports.append("DisasmSizeEncoding")
    if "PRIMARY_DATA_SIZES" in payload:
        runtime_type_imports.append("PrimaryDataSize")
    if "COMPUTE_FORMULAS" in payload:
        runtime_type_imports.append("ComputeFormula")
    if "SP_EFFECTS" in payload:
        runtime_type_imports.append("SpEffect")
    if "DIRECTION_FORM_VALUES" in payload:
        runtime_type_imports.append("DirectionFormValue")
    if "SHIFT_VARIANT_BEHAVIORS" in payload:
        runtime_type_imports.append("ShiftVariantBehavior")
    if "FIELD_MAPS" in payload:
        runtime_type_imports.append("FieldMaps")
    if "EA_BRIEF_FIELDS" in payload:
        runtime_type_imports.append("FieldSpec")
    if "RAW_FIELDS" in payload:
        runtime_type_imports.append("RawFieldMaps")
    if "BRANCH_INLINE_DISPLACEMENTS" in payload:
        runtime_type_imports.append("BranchInlineDisplacement")
    if "BRANCH_EXTENSION_DISPLACEMENTS" in payload:
        runtime_type_imports.append("BranchExtensionDisplacement")
    if runtime_type_imports:
        lines.extend([
            f"from .runtime_types import {', '.join(runtime_type_imports)}",
            "",
        ])
    if (
        "OPERATION_TYPES" in payload
        or "OPERATION_CLASSES" in payload
        or "COMPUTE_FORMULAS" in payload
        or "SP_EFFECTS" in payload
        or "PRIMARY_DATA_SIZES" in payload
        or "SHIFT_VARIANT_BEHAVIORS" in payload
    ):
        lines.extend(["from enum import StrEnum", ""])
    if (
        "OPMODE_TABLES_BY_VALUE" in payload
        or "LOOKUP_CC_FAMILIES" in payload
        or "CC_TEST_DEFINITIONS" in payload
        or "SIZE_ENCODINGS_ASM" in payload
        or "SIZE_ENCODINGS_DISASM" in payload
        or "COMPUTE_FORMULAS" in payload
        or "PRIMARY_DATA_SIZES" in payload
        or "SP_EFFECTS" in payload
        or "SHIFT_VARIANT_BEHAVIORS" in payload
    ):
        lines.extend(["from typing import TypeAlias", ""])
    if "CC_TEST_DEFINITIONS" in payload:
        lines.append("CcTestDefinition: TypeAlias = tuple[int, str]")
    if "COMPUTE_FORMULAS" in payload:
        lines.extend([
            "class ComputeOp(StrEnum):",
            "    ADD = 'add'",
            "    ADD_DECIMAL = 'add_decimal'",
            "    ASSIGN = 'assign'",
            "    BIT_CHANGE = 'bit_change'",
            "    BIT_CLEAR = 'bit_clear'",
            "    BIT_SET = 'bit_set'",
            "    BIT_TEST = 'bit_test'",
            "    BITWISE_AND = 'bitwise_and'",
            "    BITWISE_COMPLEMENT = 'bitwise_complement'",
            "    BITWISE_OR = 'bitwise_or'",
            "    BITWISE_XOR = 'bitwise_xor'",
            "    DIVIDE = 'divide'",
            "    EXCHANGE = 'exchange'",
            "    MULTIPLY = 'multiply'",
            "    ROTATE = 'rotate'",
            "    ROTATE_EXTEND = 'rotate_extend'",
            "    SHIFT = 'shift'",
            "    SIGN_EXTEND = 'sign_extend'",
            "    SUBTRACT = 'subtract'",
            "    SUBTRACT_DECIMAL = 'subtract_decimal'",
            "    TEST = 'test'",
            "",
            "class FormulaTerm(StrEnum):",
            "    SOURCE = 'source'",
            "    DESTINATION = 'destination'",
            "    EXTEND = 'X'",
            "    IMPLICIT = 'implicit'",
            "",
            "class TruncationMode(StrEnum):",
            "    TOWARD_ZERO = 'toward_zero'",
        ])
    if "PRIMARY_DATA_SIZES" in payload:
        lines.extend([
            "class PrimaryDataSizeKind(StrEnum):",
            "    MULTIPLY = 'multiply'",
            "    DIVIDE = 'divide'",
        ])
    if "OPERATION_TYPES" in payload:
        lines.extend([
            "class OperationType(StrEnum):",
            "    ADD = 'add'",
            "    ADD_DECIMAL = 'add_decimal'",
            "    ADDX = 'addx'",
            "    AND = 'and'",
            "    BIT_TEST = 'bit_test'",
            "    BITFIELD = 'bitfield'",
            "    BOUNDS_CHECK = 'bounds_check'",
            "    CCR_OP = 'ccr_op'",
            "    CLEAR = 'clear'",
            "    COMPARE = 'compare'",
            "    COMPARE_SWAP = 'compare_swap'",
            "    DIVIDE = 'divide'",
            "    MOVE = 'move'",
            "    MULTIPLY = 'multiply'",
            "    NEG = 'neg'",
            "    NEGX = 'negx'",
            "    NOT = 'not'",
            "    OR = 'or'",
            "    ROTATE = 'rotate'",
            "    ROTATE_EXTEND = 'rotate_extend'",
            "    SHIFT = 'shift'",
            "    SIGN_EXTEND = 'sign_extend'",
            "    SR_OP = 'sr_op'",
            "    SUB = 'sub'",
            "    SUB_DECIMAL = 'sub_decimal'",
            "    SUBX = 'subx'",
            "    SWAP = 'swap'",
            "    TEST = 'test'",
            "    XOR = 'xor'",
        ])
    if "OPERATION_CLASSES" in payload:
        lines.extend([
            "class OperationClass(StrEnum):",
            "    LOAD_EFFECTIVE_ADDRESS = 'load_effective_address'",
            "    MULTI_REGISTER_TRANSFER = 'multi_register_transfer'",
        ])
    if "SP_EFFECTS" in payload:
        lines.extend([
            "class SpEffectAction(StrEnum):",
            "    DECREMENT = 'decrement'",
            "    INCREMENT = 'increment'",
            "    ADJUST = 'adjust'",
            "    STORE_REG_TO_STACK = 'store_reg_to_stack'",
            "    SAVE_TO_REG = 'save_to_reg'",
            "    LOAD_FROM_REG = 'load_from_reg'",
            "    LOAD_FROM_STACK_TO_REG = 'load_from_stack_to_reg'",
        ])
    if "SHIFT_VARIANT_BEHAVIORS" in payload:
        lines.extend([
            "class ShiftDirection(StrEnum):",
            "    LEFT = 'left'",
            "    RIGHT = 'right'",
            "",
            "class ShiftFill(StrEnum):",
            "    ZERO = 'zero'",
            "    SIGN = 'sign'",
            "    ROTATE = 'rotate'",
        ])
    if (
        "OPMODE_TABLES_BY_VALUE" in payload
        or "LOOKUP_CC_FAMILIES" in payload
        or "CC_TEST_DEFINITIONS" in payload
        or "SIZE_ENCODINGS_ASM" in payload
        or "SIZE_ENCODINGS_DISASM" in payload
        or "COMPUTE_FORMULAS" in payload
        or "PRIMARY_DATA_SIZES" in payload
        or "SP_EFFECTS" in payload
        or "SHIFT_VARIANT_BEHAVIORS" in payload
    ):
        lines.append("")
    for name, value in payload.items():
        if name == "REGISTER_DEFS":
            lines.append(f"{name}: dict[int, HardwareRegisterDef] = {_render_py(value)}")
        elif name == "OPMODE_TABLES_BY_VALUE":
            lines.append(
                f"{name}: dict[str, dict[int, OpmodeEntry]] = "
                f"{_render_opmode_tables_by_value(cast(dict[str, dict[int, OpmodeEntry]], value))}"
            )
        elif name == "LOOKUP_CC_FAMILIES":
            lines.append(_render_typed_assignment(name, value, "dict[str, CcLookupFamily]"))
        elif name == "SIZE_ENCODINGS_ASM":
            lines.append(_render_typed_assignment(name, value, "dict[str, AsmSizeEncoding]"))
        elif name == "SIZE_ENCODINGS_DISASM":
            lines.append(_render_typed_assignment(name, value, "dict[str, DisasmSizeEncoding]"))
        elif name == "FIELD_MAPS":
            lines.append(f"{name}: FieldMaps = {_render_py(value)}")
        elif name == "EA_BRIEF_FIELDS":
            lines.append(f"{name}: dict[str, FieldSpec] = {_render_py(value)}")
        elif name == "RAW_FIELDS":
            lines.append(f"{name}: RawFieldMaps = {_render_py(value)}")
        elif name == "BRANCH_INLINE_DISPLACEMENTS":
            lines.append(f"{name}: dict[str, BranchInlineDisplacement] = {_render_py(value)}")
        elif name == "BRANCH_EXTENSION_DISPLACEMENTS":
            lines.append(f"{name}: dict[str, BranchExtensionDisplacement] = {_render_py(value)}")
        elif name == "CC_TEST_DEFINITIONS":
            lines.append(f"{name} = {_render_cc_test_definitions(cast(dict[str, dict[str, int | str]], value))}")
        elif name == "OPERATION_TYPES":
            lines.append(f"{name} = {_render_operation_type_table(cast(dict[str, str | None], value))}")
        elif name == "OPERATION_CLASSES":
            lines.append(f"{name} = {_render_operation_class_table(cast(dict[str, str | None], value))}")
        elif name == "COMPUTE_FORMULAS":
            lines.append(f"{name} = {_render_compute_formulas(cast(dict[str, ComputeFormula], value))}")
        elif name == "SP_EFFECTS":
            lines.append(f"{name} = {_render_sp_effects(cast(dict[str, tuple[SpEffect, ...]], value))}")
        elif name == "PRIMARY_DATA_SIZES":
            lines.append(f"{name} = {_render_primary_data_sizes(cast(dict[str, PrimaryDataSize], value))}")
        elif name == "SHIFT_VARIANT_BEHAVIORS":
            lines.append(
                f"{name} = "
                f"{_render_shift_variant_behaviors(cast(dict[str, tuple[tuple[str, str, str, bool], ...]], value))}"
            )
        else:
            lines.append(f"{name} = {_render_py(value)}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _enum_member(enum_name: str, raw_value: str) -> str:
    members = {
        "Processor": {
            "68000": "M68000",
            "68008": "M68008",
            "68010": "M68010",
            "68020": "M68020",
            "68030": "M68030",
            "68040": "M68040",
            "CPU32": "CPU32",
            "68851": "MC68851",
        },
        "FlowType": {
            "sequential": "SEQUENTIAL",
            "branch": "BRANCH",
            "jump": "JUMP",
            "call": "CALL",
            "return": "RETURN",
            "trap": "TRAP",
        },
        "ComputeOp": {
            "add": "ADD",
            "add_decimal": "ADD_DECIMAL",
            "assign": "ASSIGN",
            "bit_change": "BIT_CHANGE",
            "bit_clear": "BIT_CLEAR",
            "bit_set": "BIT_SET",
            "bit_test": "BIT_TEST",
            "bitwise_and": "BITWISE_AND",
            "bitwise_complement": "BITWISE_COMPLEMENT",
            "bitwise_or": "BITWISE_OR",
            "bitwise_xor": "BITWISE_XOR",
            "divide": "DIVIDE",
            "exchange": "EXCHANGE",
            "multiply": "MULTIPLY",
            "rotate": "ROTATE",
            "rotate_extend": "ROTATE_EXTEND",
            "shift": "SHIFT",
            "sign_extend": "SIGN_EXTEND",
            "subtract": "SUBTRACT",
            "subtract_decimal": "SUBTRACT_DECIMAL",
            "test": "TEST",
        },
        "FormulaTerm": {
            "source": "SOURCE",
            "destination": "DESTINATION",
            "X": "EXTEND",
            "implicit": "IMPLICIT",
        },
        "TruncationMode": {
            "toward_zero": "TOWARD_ZERO",
        },
        "PrimaryDataSizeKind": {
            "multiply": "MULTIPLY",
            "divide": "DIVIDE",
        },
        "OperationType": {
            "add": "ADD",
            "add_decimal": "ADD_DECIMAL",
            "addx": "ADDX",
            "and": "AND",
            "bit_test": "BIT_TEST",
            "bitfield": "BITFIELD",
            "bounds_check": "BOUNDS_CHECK",
            "ccr_op": "CCR_OP",
            "clear": "CLEAR",
            "compare": "COMPARE",
            "compare_swap": "COMPARE_SWAP",
            "divide": "DIVIDE",
            "move": "MOVE",
            "multiply": "MULTIPLY",
            "neg": "NEG",
            "negx": "NEGX",
            "not": "NOT",
            "or": "OR",
            "rotate": "ROTATE",
            "rotate_extend": "ROTATE_EXTEND",
            "shift": "SHIFT",
            "sign_extend": "SIGN_EXTEND",
            "sr_op": "SR_OP",
            "sub": "SUB",
            "sub_decimal": "SUB_DECIMAL",
            "subx": "SUBX",
            "swap": "SWAP",
            "test": "TEST",
            "xor": "XOR",
        },
        "OperationClass": {
            "load_effective_address": "LOAD_EFFECTIVE_ADDRESS",
            "multi_register_transfer": "MULTI_REGISTER_TRANSFER",
        },
        "SpEffectAction": {
            "decrement": "DECREMENT",
            "increment": "INCREMENT",
            "adjust": "ADJUST",
            "store_reg_to_stack": "STORE_REG_TO_STACK",
            "save_to_reg": "SAVE_TO_REG",
            "load_from_reg": "LOAD_FROM_REG",
            "load_from_stack_to_reg": "LOAD_FROM_STACK_TO_REG",
        },
        "ShiftDirection": {
            "left": "LEFT",
            "right": "RIGHT",
        },
        "ShiftFill": {
            "zero": "ZERO",
            "sign": "SIGN",
            "rotate": "ROTATE",
        },
        "RelocMode": {
            "absolute": "ABSOLUTE",
            "pc_relative": "PC_RELATIVE",
            "data_relative": "DATA_RELATIVE",
        },
    }
    return f"{enum_name}.{members[enum_name][raw_value]}"


def _render_processor_table(table: dict[str, str]) -> str:
    rendered = ",\n ".join(
        f"{key!r}: {_enum_member('Processor', value)}"
        for key, value in table.items()
    )
    return "{%s}" % rendered


def _render_flow_table(table: dict[str, str]) -> str:
    rendered = ",\n ".join(
        f"{key!r}: {_enum_member('FlowType', value)}"
        for key, value in table.items()
    )
    return "{%s}" % rendered


def _render_operation_type_table(table: dict[str, str | None]) -> str:
    rendered = ",\n ".join(
        f"{key!r}: {(_enum_member('OperationType', value) if value is not None else 'None')}"
        for key, value in table.items()
    )
    return "{%s}" % rendered


def _render_operation_class_table(table: dict[str, str | None]) -> str:
    rendered = ",\n ".join(
        f"{key!r}: {(_enum_member('OperationClass', value) if value is not None else 'None')}"
        for key, value in table.items()
    )
    return "{%s}" % rendered


def _render_hunk_relocation_semantics(table: dict[str, tuple[int, str]]) -> str:
    rendered = ",\n ".join(
        f"{key!r}: ({nbytes!r}, {_enum_member('RelocMode', mode)})"
        for key, (nbytes, mode) in table.items()
    )
    return "{%s}" % rendered


def _render_primary_data_sizes(table: dict[str, tuple[str, int, int, int]]) -> str:
    rendered = ",\n ".join(
        f"{key!r}: ({_enum_member('PrimaryDataSizeKind', kind)}, {src_bits!r}, {dst_bits!r}, {result_bits!r})"
        for key, (kind, src_bits, dst_bits, result_bits) in table.items()
    )
    return "{%s}" % rendered


def _render_cc_test_definitions(table: dict[str, dict[str, int | str]]) -> str:
    rendered = ",\n ".join(
        f"{key!r}: ({value['encoding']!r}, {value['test']!r})"
        for key, value in table.items()
    )
    return "{%s}" % rendered


def _render_size_encodings(table: Mapping[str, Mapping[str | int, int]]) -> str:
    def _entry(mapping: Mapping[str | int, int], *keys: str | int) -> str:
        return "(" + ", ".join(repr(mapping.get(key)) for key in keys) + ")"

    rendered = ",\n ".join(
        f"{key!r}: {_entry(value, 'b', 'w', 'l') if 'b' in value or 'w' in value or 'l' in value else _entry(value, 0, 1, 2, 3)}"
        for key, value in table.items()
    )
    return "{%s}" % rendered


def _render_rm_fields(table: dict[str, tuple[int, dict[int, str]]]) -> str:
    rendered = ",\n ".join(
        f"{key!r}: ({bit_lo!r}, ({', '.join(repr(values.get(idx)) for idx in range(max(values) + 1))}))"
        for key, (bit_lo, values) in table.items()
    )
    return "{%s}" % rendered


def _render_shift_fields(value: ShiftFieldsData) -> str:
    dr_values = value["dr_values"]
    max_idx = max(dr_values)
    rendered_values = ", ".join(repr(dr_values.get(idx)) for idx in range(max_idx + 1))
    return f"({value['dr_field']!r}, ({rendered_values}), {value['zero_means']!r})"


def _render_compute_formulas(table: dict[str, ComputeFormula]) -> str:
    def _render_formula_term(term: str | int) -> str:
        if isinstance(term, int):
            return repr(term)
        return _enum_member("FormulaTerm", term)

    def _render_source_bits(entries: tuple[tuple[str, int], ...]) -> str:
        rendered_entries = ", ".join(f"({size!r}, {bits!r})" for size, bits in entries)
        if len(entries) == 1:
            rendered_entries += ","
        return f"({rendered_entries})"

    rendered = ",\n ".join(
        f"{key!r}: ("
        f"{_enum_member('ComputeOp', value[0])}, "
        f"({', '.join(_render_formula_term(term) for term in value[1])}{',' if len(value[1]) == 1 else ''}), "
        f"{value[2]!r}, "
        f"{value[3]!r}, "
        f"{_render_source_bits(value[4])}, "
        f"{_enum_member('TruncationMode', value[5]) if value[5] is not None else 'None'})"
        for key, value in sorted(table.items())
    )
    return "{%s}" % rendered


def _render_sp_effects(table: dict[str, tuple[tuple[str, int | None, str | None], ...]]) -> str:
    entries = []
    for key, value in table.items():
        rendered_value = ", ".join(
            f"({_enum_member('SpEffectAction', action)}, {nbytes!r}, {aux!r})"
            for action, nbytes, aux in value
        )
        entries.append(f"{key!r}: ({rendered_value},)")
    rendered = ",\n ".join(entries)
    return "{%s}" % rendered


def _render_shift_variant_behaviors(table: dict[str, tuple[tuple[str, str, str, bool], ...]]) -> str:
    entries = []
    for key, value in table.items():
        rendered_value = ", ".join(
            f"({variant!r}, {_enum_member('ShiftDirection', direction)}, {_enum_member('ShiftFill', fill)}, {arithmetic!r})"
            for variant, direction, fill, arithmetic in value
        )
        entries.append(f"{key!r}: ({rendered_value},)")
    rendered = ",\n ".join(entries)
    return "{%s}" % rendered


def _write_m68k_runtime_python(path: Path, payload: RuntimeM68kPayload, *, header: str) -> None:
    meta = payload["meta"]
    tables = payload["tables"]
    text = "\n".join(
        [
            '"""' + header + '"""',
            "",
            "from __future__ import annotations",
            "",
            "from enum import IntEnum, StrEnum",
            "from typing import TypeAlias",
            "from .runtime_types import AsmSizeEncoding, BitField, BitModulus, BranchExtensionDisplacement, BranchInlineDisplacement, CcLookupFamily, ComputeFormula, ConditionFamily, DirectionFormValue, DirectionVariant, DisasmSizeEncoding, EaModeTable, FieldMaps, FieldSpec, ImmediateRange, OperandModeTable, OpmodeEntry, PrimaryDataSize, RawFieldMaps, RmFieldInfo, ShiftFieldInfo, ShiftVariantBehavior, SpEffect",
            "",
            "class SizeCode(IntEnum):",
            "    BYTE = 0",
            "    WORD = 1",
            "    LONG = 2",
            "",
            "class Processor(StrEnum):",
            "    M68000 = '68000'",
            "    M68008 = '68008'",
            "    M68010 = '68010'",
            "    M68020 = '68020'",
            "    M68030 = '68030'",
            "    M68040 = '68040'",
            "    CPU32 = 'CPU32'",
            "    MC68851 = '68851'",
            "",
            "class FlowType(StrEnum):",
            "    SEQUENTIAL = 'sequential'",
            "    BRANCH = 'branch'",
            "    JUMP = 'jump'",
            "    CALL = 'call'",
            "    RETURN = 'return'",
            "    TRAP = 'trap'",
            "",
            "class ComputeOp(StrEnum):",
            "    ADD = 'add'",
            "    ADD_DECIMAL = 'add_decimal'",
            "    ASSIGN = 'assign'",
            "    BIT_CHANGE = 'bit_change'",
            "    BIT_CLEAR = 'bit_clear'",
            "    BIT_SET = 'bit_set'",
            "    BIT_TEST = 'bit_test'",
            "    BITWISE_AND = 'bitwise_and'",
            "    BITWISE_COMPLEMENT = 'bitwise_complement'",
            "    BITWISE_OR = 'bitwise_or'",
            "    BITWISE_XOR = 'bitwise_xor'",
            "    DIVIDE = 'divide'",
            "    EXCHANGE = 'exchange'",
            "    MULTIPLY = 'multiply'",
            "    ROTATE = 'rotate'",
            "    ROTATE_EXTEND = 'rotate_extend'",
            "    SHIFT = 'shift'",
            "    SIGN_EXTEND = 'sign_extend'",
            "    SUBTRACT = 'subtract'",
            "    SUBTRACT_DECIMAL = 'subtract_decimal'",
            "    TEST = 'test'",
            "",
            "class FormulaTerm(StrEnum):",
            "    SOURCE = 'source'",
            "    DESTINATION = 'destination'",
            "    EXTEND = 'X'",
            "    IMPLICIT = 'implicit'",
            "",
            "class TruncationMode(StrEnum):",
            "    TOWARD_ZERO = 'toward_zero'",
            "",
            "class PrimaryDataSizeKind(StrEnum):",
            "    MULTIPLY = 'multiply'",
            "    DIVIDE = 'divide'",
            "",
            "class OperationType(StrEnum):",
            "    ADD = 'add'",
            "    ADD_DECIMAL = 'add_decimal'",
            "    ADDX = 'addx'",
            "    AND = 'and'",
            "    BIT_TEST = 'bit_test'",
            "    BITFIELD = 'bitfield'",
            "    BOUNDS_CHECK = 'bounds_check'",
            "    CCR_OP = 'ccr_op'",
            "    CLEAR = 'clear'",
            "    COMPARE = 'compare'",
            "    COMPARE_SWAP = 'compare_swap'",
            "    DIVIDE = 'divide'",
            "    MOVE = 'move'",
            "    MULTIPLY = 'multiply'",
            "    NEG = 'neg'",
            "    NEGX = 'negx'",
            "    NOT = 'not'",
            "    OR = 'or'",
            "    ROTATE = 'rotate'",
            "    ROTATE_EXTEND = 'rotate_extend'",
            "    SHIFT = 'shift'",
            "    SIGN_EXTEND = 'sign_extend'",
            "    SR_OP = 'sr_op'",
            "    SUB = 'sub'",
            "    SUB_DECIMAL = 'sub_decimal'",
            "    SUBX = 'subx'",
            "    SWAP = 'swap'",
            "    TEST = 'test'",
            "    XOR = 'xor'",
            "",
            "class OperationClass(StrEnum):",
            "    LOAD_EFFECTIVE_ADDRESS = 'load_effective_address'",
            "    MULTI_REGISTER_TRANSFER = 'multi_register_transfer'",
            "",
            "class SpEffectAction(StrEnum):",
            "    DECREMENT = 'decrement'",
            "    INCREMENT = 'increment'",
            "    ADJUST = 'adjust'",
            "    STORE_REG_TO_STACK = 'store_reg_to_stack'",
            "    SAVE_TO_REG = 'save_to_reg'",
            "    LOAD_FROM_REG = 'load_from_reg'",
            "    LOAD_FROM_STACK_TO_REG = 'load_from_stack_to_reg'",
            "",
            "class ShiftDirection(StrEnum):",
            "    LEFT = 'left'",
            "    RIGHT = 'right'",
            "",
            "class ShiftFill(StrEnum):",
            "    ZERO = 'zero'",
            "    SIGN = 'sign'",
            "    ROTATE = 'rotate'",
            "",
            f"META = {_render_py(meta)}",
            "",
            f"MNEMONIC_INDEX = {_render_py(tables['mnemonic_index'])}",
            f"ENCODING_COUNTS = {_render_py(tables['encoding_counts'])}",
            f"ENCODING_MASKS = {_render_py(tables['encoding_masks'])}",
            f"FIXED_OPCODES = {_render_py(tables['fixed_opcodes'])}",
            f"EXT_FIELD_NAMES = {_render_py(tables['ext_field_names'])}",
            f"FIELD_MAPS = {_render_py(tables['field_maps'])}",
            f"RAW_FIELDS = {_render_py(tables['raw_fields'])}",
            f"EA_BRIEF_FIELDS = {_render_py(tables['ea_brief_fields'])}",
            f"SIZE_ENCODINGS_ASM = {_render_size_encodings(cast(Mapping[str, Mapping[str | int, int]], tables['size_encodings_asm']))}",
            f"SIZE_ENCODINGS_DISASM = {_render_size_encodings(cast(Mapping[str, Mapping[str | int, int]], tables['size_encodings_disasm']))}",
            f"CC_FAMILIES = {_render_py(tables['cc_families'])}",
            f"IMMEDIATE_RANGES = {_render_py(tables['immediate_ranges'])}",
            f"COMPUTE_FORMULAS = {_render_compute_formulas(tables['compute_formulas'])}",
            f"SP_EFFECTS = {_render_sp_effects(tables['sp_effects'])}",
            f"IMPLICIT_OPERANDS = {_render_py(tables['implicit_operands'])}",
            f"BIT_MODULI = {_render_py(tables['bit_moduli'])}",
            f"ROTATE_EXTRA_BITS = {_render_py(tables['rotate_extra_bits'])}",
            f"SIGNED_RESULTS = {_render_py(tables['signed_results'])}",
            f"INSTRUCTION_SIZES = {_render_py(tables['instruction_sizes'])}",
            f"OPERATION_TYPES = {_render_operation_type_table(tables['operation_types'])}",
            f"OPERATION_CLASSES = {_render_operation_class_table(tables['operation_classes'])}",
            f"SOURCE_SIGN_EXTEND = {_render_py(tables['source_sign_extend'])}",
            f"BOUNDS_CHECKS = {_render_py(tables['bounds_checks'])}",
            f"SHIFT_COUNT_MODULI = {_render_py(tables['shift_count_moduli'])}",
            f"OPMODE_TABLES_LIST = {_render_py(tables['opmode_tables_list'])}",
            f"OPMODE_TABLES_BY_VALUE: dict[str, dict[int, OpmodeEntry]] = {_render_opmode_tables_by_value(tables['opmode_tables_by_value'])}",
            f"FORM_OPERAND_TYPES = {_render_py(tables['form_operand_types'])}",
            f"FORM_FLAGS_020 = {_render_py(tables['form_flags_020'])}",
            f"PRIMARY_DATA_SIZES = {_render_primary_data_sizes(tables['primary_data_sizes'])}",
            f"EA_MODE_TABLES = {_render_py(tables['ea_mode_tables'])}",
            f"AN_SIZES = {_render_py(tables['an_sizes'])}",
            f"OPERAND_MODE_TABLES = {_render_py(tables['operand_mode_tables'])}",
            f"DIRECTION_VARIANTS = {_render_py(tables['direction_variants'])}",
            f"REGISTER_FIELDS = {_render_py(tables['register_fields'])}",
            f"DEST_REG_FIELD = {_render_py(tables['dest_reg_field'])}",
            f"BF_MNEMONICS = {_render_py(tables['bf_mnemonics'])}",
            f"BITOP_NAMES = {_render_py(tables['bitop_names'])}",
            f"IMM_NAMES = {_render_py(tables['imm_names'])}",
            f"SHIFT_NAMES = {_render_py(tables['shift_names'])}",
            f"SHIFT_TYPE_FIELDS = {_render_py(tables['shift_type_fields'])}",
            f"SHIFT_FIELDS = {_render_shift_fields(tables['shift_fields'])}",
            f"RM_FIELD = {_render_rm_fields(tables['rm_field'])}",
            f"ADDQ_ZERO_MEANS = {_render_py(tables['addq_zero_means'])}",
            f"CONTROL_REGISTERS = {_render_py(tables['control_registers'])}",
            f"PROCESSOR_MINS = {_render_processor_table(tables['processor_mins'])}",
            f"FLOW_TYPES = {_render_flow_table(tables['flow_types'])}",
            f"FLOW_CONDITIONAL = {_render_py(tables['flow_conditional'])}",
            f"CONDITION_FAMILIES = {_render_py(tables['condition_families'])}",
            f"BRANCH_INLINE_DISPLACEMENTS = {_render_py(tables['branch_inline_displacements'])}",
            f"BRANCH_EXTENSION_DISPLACEMENTS = {_render_py(tables['branch_extension_displacements'])}",
            f"MOVE_FIELDS = {_render_py(tables['move_fields'])}",
            f"MOVEM_FIELDS = {_render_py(tables['movem_fields'])}",
            f"CPID_FIELD = {_render_py(tables['cpid_field'])}",
            f"ASM_SYNTAX_INDEX = {_render_py(tables['asm_syntax_index'])}",
            f"SPECIAL_OPERAND_TYPES = {_render_py(tables['special_operand_types'])}",
            f"USES_LABELS = {_render_py(tables['uses_labels'])}",
            f"DIRECTION_FORM_VALUES = {_render_py(tables['direction_form_values'])}",
            f"SHIFT_VARIANT_BEHAVIORS = {_render_shift_variant_behaviors(tables['shift_variant_behaviors'])}",
            f"PROCESSOR_020_VARIANTS = {_render_processor_020_variants(tables['processor_020_variants'])}",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def _write_m68k_decode_runtime_python(path: Path, payload: M68kDecodeRuntimePayload, *, header: str) -> None:
    typed_assignments = {
        "SIZE_BYTE_COUNT": "dict[str, int]",
        "EA_MODE_ENCODING": "dict[str, list[int | None]]",
        "EA_BRIEF_FIELDS": "dict[str, tuple[int, int, int]]",
        "ENCODING_COUNTS": "dict[str, int]",
        "ENCODING_MASKS": "tuple[dict[str, tuple[int, int]], ...]",
        "RAW_FIELDS": "tuple[dict[str, tuple[tuple[str, int, int, int], ...]], ...]",
        "FORM_OPERAND_TYPES": "dict[str, tuple[tuple[str, ...], ...]]",
        "OPERATION_TYPES": "dict[str, OperationType]",
        "SOURCE_SIGN_EXTEND": "tuple[str, ...]",
        "OPMODE_TABLES_BY_VALUE": "dict[str, dict[int, OpmodeEntry]]",
        "OPERAND_MODE_TABLES": "dict[str, tuple[str, dict[int, tuple[str, ...]]]]",
        "CONTROL_REGISTERS": "dict[int, str]",
    }
    lines = [
        '"""' + header + '"""',
        "",
        "from __future__ import annotations",
        "",
        "from enum import StrEnum",
        "",
        "from .runtime_types import BitField, OpmodeEntry",
        "",
        "class OperationType(StrEnum):",
        "    ADD = 'add'",
        "    ADD_DECIMAL = 'add_decimal'",
        "    ADDX = 'addx'",
        "    AND = 'and'",
        "    BIT_TEST = 'bit_test'",
        "    BITFIELD = 'bitfield'",
        "    BOUNDS_CHECK = 'bounds_check'",
        "    CCR_OP = 'ccr_op'",
        "    CLEAR = 'clear'",
        "    COMPARE = 'compare'",
        "    COMPARE_SWAP = 'compare_swap'",
        "    DIVIDE = 'divide'",
        "    MOVE = 'move'",
        "    MULTIPLY = 'multiply'",
        "    NEG = 'neg'",
        "    NEGX = 'negx'",
        "    NOT = 'not'",
        "    OR = 'or'",
        "    ROTATE = 'rotate'",
        "    ROTATE_EXTEND = 'rotate_extend'",
        "    SHIFT = 'shift'",
        "    SIGN_EXTEND = 'sign_extend'",
        "    SR_OP = 'sr_op'",
        "    SUB = 'sub'",
        "    SUB_DECIMAL = 'sub_decimal'",
        "    SUBX = 'subx'",
        "    SWAP = 'swap'",
        "    TEST = 'test'",
        "    XOR = 'xor'",
        "",
    ]
    for name, value in payload.items():
        if name == "OPERATION_TYPES":
            lines.append(f"{name} = {_render_operation_type_table(cast(dict[str, str | None], value))}")
        elif name == "OPMODE_TABLES_BY_VALUE":
            lines.append(
                f"{name}: dict[str, dict[int, OpmodeEntry]] = "
                f"{_render_opmode_tables_by_value(cast(dict[str, dict[int, OpmodeEntry]], value))}"
            )
        elif name in typed_assignments:
            lines.append(_render_typed_assignment(name, value, typed_assignments[name]))
        else:
            lines.append(f"{name} = {_render_py(value)}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_m68k_disasm_runtime_python(path: Path, payload: M68kDisasmRuntimePayload, *, header: str) -> None:
    lines = [
        '"""' + header + '"""',
        "",
        "from __future__ import annotations",
        "",
        "from enum import StrEnum",
        "",
        "from typing import TypeAlias",
        "from .runtime_types import ConditionFamily, CpuHierarchy, DisasmSizeEncoding, OpmodeEntry, RmFieldInfo, ShiftFieldInfo",
        "",
        "class OperationType(StrEnum):",
        "    ADD = 'add'",
        "    ADD_DECIMAL = 'add_decimal'",
        "    ADDX = 'addx'",
        "    AND = 'and'",
        "    BIT_TEST = 'bit_test'",
        "    BITFIELD = 'bitfield'",
        "    BOUNDS_CHECK = 'bounds_check'",
        "    CCR_OP = 'ccr_op'",
        "    CLEAR = 'clear'",
        "    COMPARE = 'compare'",
        "    COMPARE_SWAP = 'compare_swap'",
        "    DIVIDE = 'divide'",
        "    MOVE = 'move'",
        "    MULTIPLY = 'multiply'",
        "    NEG = 'neg'",
        "    NEGX = 'negx'",
        "    NOT = 'not'",
        "    OR = 'or'",
        "    ROTATE = 'rotate'",
        "    ROTATE_EXTEND = 'rotate_extend'",
        "    SHIFT = 'shift'",
        "    SIGN_EXTEND = 'sign_extend'",
        "    SR_OP = 'sr_op'",
        "    SUB = 'sub'",
        "    SUB_DECIMAL = 'sub_decimal'",
        "    SUBX = 'subx'",
        "    SWAP = 'swap'",
        "    TEST = 'test'",
        "    XOR = 'xor'",
        "class OperationClass(StrEnum):",
        "    LOAD_EFFECTIVE_ADDRESS = 'load_effective_address'",
        "    MULTI_REGISTER_TRANSFER = 'multi_register_transfer'",
        "",
    ]
    for name, value in payload.items():
        if name == "SIZE_ENCODINGS_DISASM":
            lines.append(f"{name} = {_render_size_encodings(cast(Mapping[str, Mapping[str | int, int]], value))}")
        elif name == "SHIFT_FIELDS":
            lines.append(f"{name} = {_render_shift_fields(cast(ShiftFieldsData, value))}")
        elif name == "RM_FIELD":
            lines.append(f"{name} = {_render_rm_fields(cast(dict[str, tuple[int, dict[int, str]]], value))}")
        elif name == "OPERATION_TYPES":
            lines.append(f"{name} = {_render_operation_type_table(cast(dict[str, str | None], value))}")
        elif name == "OPERATION_CLASSES":
            lines.append(f"{name} = {_render_operation_class_table(cast(dict[str, str | None], value))}")
        elif name == "CONDITION_FAMILIES":
            lines.append(f"{name}: tuple[ConditionFamily, ...] = {_render_py(value)}")
        elif name == "CPU_HIERARCHY":
            lines.append(f"{name}: CpuHierarchy = {_render_py(value)}")
        elif name == "PROCESSOR_MINS":
            lines.append(f"{name}: dict[str, str] = {_render_py(value)}")
        elif name == "OPMODE_TABLES_BY_VALUE":
            lines.append(
                f"{name}: dict[str, dict[int, OpmodeEntry]] = "
                f"{_render_opmode_tables_by_value(cast(dict[str, dict[int, OpmodeEntry]], value))}"
            )
        elif name == "FORM_OPERAND_TYPES":
            lines.append(f"{name}: dict[str, tuple[tuple[str, ...], ...]] = {_render_py(value)}")
        elif name == "EXT_FIELD_NAMES":
            lines.append(f"{name}: dict[str, tuple[str, ...]] = {_render_py(value)}")
        elif name == "PMMU_CONDITION_CODES":
            lines.append(f"{name}: tuple[str, ...] = {_render_py(value)}")
        elif name == "CONDITION_CODES":
            lines.append(f"{name}: tuple[str, ...] = {_render_py(value)}")
        elif name == "DEFAULT_OPERAND_SIZE":
            lines.append(f"{name}: str | None = {_render_py(value)}")
        else:
            lines.append(f"{name} = {_render_py(value)}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_m68k_asm_runtime_python(path: Path, payload: M68kAsmRuntimePayload, *, header: str) -> None:
    lines = [
        '"""' + header + '"""',
        "",
        "from __future__ import annotations",
        "",
        "from enum import StrEnum",
        "",
        "from .runtime_types import AsmSizeEncoding",
        "",
        "class OperationType(StrEnum):",
        "    ADD = 'add'",
        "    ADD_DECIMAL = 'add_decimal'",
        "    ADDX = 'addx'",
        "    AND = 'and'",
        "    BIT_TEST = 'bit_test'",
        "    BITFIELD = 'bitfield'",
        "    BOUNDS_CHECK = 'bounds_check'",
        "    CCR_OP = 'ccr_op'",
        "    CLEAR = 'clear'",
        "    COMPARE = 'compare'",
        "    COMPARE_SWAP = 'compare_swap'",
        "    DIVIDE = 'divide'",
        "    MOVE = 'move'",
        "    MULTIPLY = 'multiply'",
        "    NEG = 'neg'",
        "    NEGX = 'negx'",
        "    NOT = 'not'",
        "    OR = 'or'",
        "    ROTATE = 'rotate'",
        "    ROTATE_EXTEND = 'rotate_extend'",
        "    SHIFT = 'shift'",
        "    SIGN_EXTEND = 'sign_extend'",
        "    SR_OP = 'sr_op'",
        "    SUB = 'sub'",
        "    SUB_DECIMAL = 'sub_decimal'",
        "    SUBX = 'subx'",
        "    SWAP = 'swap'",
        "    TEST = 'test'",
        "    XOR = 'xor'",
        "",
    ]
    for name, value in payload.items():
        if name == "SIZE_ENCODINGS_ASM":
            lines.append(f"{name} = {_render_size_encodings(cast(Mapping[str, Mapping[str | int, int]], value))}")
        elif name == "OPERATION_TYPES":
            lines.append(f"{name} = {_render_operation_type_table(cast(dict[str, str | None], value))}")
        else:
            lines.append(f"{name} = {_render_py(value)}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_m68k_analysis_runtime_python(path: Path, payload: M68kAnalysisRuntimePayload, *, header: str) -> None:
    typed_assignments = {
        "OPWORD_BYTES": "int",
        "SIZE_BYTE_COUNT": "dict[str, int]",
        "EA_MODE_ENCODING": "dict[str, list[int | None]]",
        "EA_REVERSE": "dict[tuple[int, int], str]",
        "EA_BRIEF_FIELDS": "dict[str, tuple[int, int, int]]",
        "OPERATION_TYPES": "dict[str, OperationType]",
        "FLOW_TYPES": "dict[str, FlowType]",
        "FLOW_CONDITIONAL": "dict[str, bool]",
        "LOOKUP_CANONICAL": "dict[str, str]",
        "LOOKUP_NUMERIC_CC_PREFIXES": "dict[str, str]",
    }
    lines = [
        '"""' + header + '"""',
        "",
        "from __future__ import annotations",
        "",
        "from enum import StrEnum",
        "",
        "class Processor(StrEnum):",
        "    M68000 = '68000'",
        "    M68008 = '68008'",
        "    M68010 = '68010'",
        "    M68020 = '68020'",
        "    M68030 = '68030'",
        "    M68040 = '68040'",
        "    CPU32 = 'CPU32'",
        "    MC68851 = '68851'",
        "",
        "class FlowType(StrEnum):",
        "    SEQUENTIAL = 'sequential'",
        "    BRANCH = 'branch'",
        "    JUMP = 'jump'",
        "    CALL = 'call'",
        "    RETURN = 'return'",
        "    TRAP = 'trap'",
        "",
        "class OperationType(StrEnum):",
        "    ADD = 'add'",
        "    ADD_DECIMAL = 'add_decimal'",
        "    ADDX = 'addx'",
        "    AND = 'and'",
        "    BIT_TEST = 'bit_test'",
        "    BITFIELD = 'bitfield'",
        "    BOUNDS_CHECK = 'bounds_check'",
        "    CCR_OP = 'ccr_op'",
        "    CLEAR = 'clear'",
        "    COMPARE = 'compare'",
        "    COMPARE_SWAP = 'compare_swap'",
        "    DIVIDE = 'divide'",
        "    MOVE = 'move'",
        "    MULTIPLY = 'multiply'",
        "    NEG = 'neg'",
        "    NEGX = 'negx'",
        "    NOT = 'not'",
        "    OR = 'or'",
        "    ROTATE = 'rotate'",
        "    ROTATE_EXTEND = 'rotate_extend'",
        "    SHIFT = 'shift'",
        "    SIGN_EXTEND = 'sign_extend'",
        "    SR_OP = 'sr_op'",
        "    SUB = 'sub'",
        "    SUB_DECIMAL = 'sub_decimal'",
        "    SUBX = 'subx'",
        "    SWAP = 'swap'",
        "    TEST = 'test'",
        "    XOR = 'xor'",
        "",
        "class OperationClass(StrEnum):",
        "    LOAD_EFFECTIVE_ADDRESS = 'load_effective_address'",
        "    MULTI_REGISTER_TRANSFER = 'multi_register_transfer'",
        "",
        "class ComputeOp(StrEnum):",
        "    ADD = 'add'",
        "    ADD_DECIMAL = 'add_decimal'",
        "    ASSIGN = 'assign'",
        "    BIT_CHANGE = 'bit_change'",
        "    BIT_CLEAR = 'bit_clear'",
        "    BIT_SET = 'bit_set'",
        "    BIT_TEST = 'bit_test'",
        "    BITWISE_AND = 'bitwise_and'",
        "    BITWISE_COMPLEMENT = 'bitwise_complement'",
        "    BITWISE_OR = 'bitwise_or'",
        "    BITWISE_XOR = 'bitwise_xor'",
        "    DIVIDE = 'divide'",
        "    EXCHANGE = 'exchange'",
        "    MULTIPLY = 'multiply'",
        "    ROTATE = 'rotate'",
        "    ROTATE_EXTEND = 'rotate_extend'",
        "    SHIFT = 'shift'",
        "    SIGN_EXTEND = 'sign_extend'",
        "    SUBTRACT = 'subtract'",
        "    SUBTRACT_DECIMAL = 'subtract_decimal'",
        "    TEST = 'test'",
        "",
        "class FormulaTerm(StrEnum):",
        "    SOURCE = 'source'",
        "    DESTINATION = 'destination'",
        "    EXTEND = 'X'",
        "    IMPLICIT = 'implicit'",
        "",
        "class TruncationMode(StrEnum):",
        "    TOWARD_ZERO = 'toward_zero'",
        "",
        "class SpEffectAction(StrEnum):",
        "    DECREMENT = 'decrement'",
        "    INCREMENT = 'increment'",
        "    ADJUST = 'adjust'",
        "    STORE_REG_TO_STACK = 'store_reg_to_stack'",
        "    SAVE_TO_REG = 'save_to_reg'",
        "    LOAD_FROM_REG = 'load_from_reg'",
        "    LOAD_FROM_STACK_TO_REG = 'load_from_stack_to_reg'",
        "",
    ]
    for name, value in payload.items():
        if name == "PROCESSOR_MINS":
            lines.append(f"{name} = {_render_processor_table(cast(dict[str, str], value))}")
        elif name == "FLOW_TYPES":
            lines.append(f"{name} = {_render_flow_table(cast(dict[str, str], value))}")
        elif name == "OPERATION_TYPES":
            lines.append(f"{name} = {_render_operation_type_table(cast(dict[str, str | None], value))}")
        elif name == "OPERATION_CLASSES":
            lines.append(f"{name} = {_render_operation_class_table(cast(dict[str, str | None], value))}")
        elif name == "COMPUTE_FORMULAS":
            lines.append(f"{name} = {_render_compute_formulas(cast(dict[str, ComputeFormula], value))}")
        elif name == "SP_EFFECTS":
            lines.append(f"{name} = {_render_sp_effects(cast(dict[str, tuple[SpEffect, ...]], value))}")
        elif name == "PROCESSOR_020_VARIANTS":
            lines.append(
                f"{name} = {_render_processor_020_variants(cast(dict[str, frozenset[str]], value))}"
            )
        elif name in typed_assignments:
            lines.append(_render_typed_assignment(name, value, typed_assignments[name]))
        else:
            lines.append(f"{name} = {_render_py(value)}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_hunk_runtime_python(path: Path, payload: HunkRuntimePayload, *, header: str) -> None:
    lines = [
        '"""' + header + '"""',
        "",
        "from __future__ import annotations",
        "",
        "from enum import StrEnum",
        "",
        "class RelocMode(StrEnum):",
        "    ABSOLUTE = 'absolute'",
        "    PC_RELATIVE = 'pc_relative'",
        "    DATA_RELATIVE = 'data_relative'",
        "",
        f"META = {_render_py(payload['META'])}",
        f"HUNK_TYPES = {_render_py(payload['HUNK_TYPES'])}",
        f"EXT_TYPES = {_render_py(payload['EXT_TYPES'])}",
        f"MEMORY_FLAGS = {_render_py(payload['MEMORY_FLAGS'])}",
        f"MEMORY_TYPE_CODES = {_render_py(payload['MEMORY_TYPE_CODES'])}",
        f"EXT_TYPE_CATEGORIES = {_render_py(payload['EXT_TYPE_CATEGORIES'])}",
        f"COMPATIBILITY_NOTES = {_render_py(payload['COMPATIBILITY_NOTES'])}",
        f"RELOC_FORMATS = {_render_py(payload['RELOC_FORMATS'])}",
        f"RELOCATION_SEMANTICS = {_render_hunk_relocation_semantics(payload['RELOCATION_SEMANTICS'])}",
        f"HUNK_CONTENT_FORMATS = {_render_py(payload['HUNK_CONTENT_FORMATS'])}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _render_os_struct_field(field: OsStructField) -> str:
    parts = [
        f"name={field['name']!r}",
        f"type={field['type']!r}",
        f"offset={field['offset']!r}",
        f"size={field['size']!r}",
    ]
    if "size_symbol" in field:
        parts.append(f"size_symbol={field['size_symbol']!r}")
    if "struct" in field:
        parts.append(f"struct={field['struct']!r}")
    if "c_type" in field:
        parts.append(f"c_type={field['c_type']!r}")
    if "pointer_struct" in field:
        parts.append(f"pointer_struct={field['pointer_struct']!r}")
    return f"OsStructField({', '.join(parts)})"


def _render_os_struct(struct_def: OsStructDef) -> str:
    fields = ", ".join(_render_os_struct_field(field) for field in struct_def["fields"])
    if len(struct_def["fields"]) == 1:
        fields += ","
    parts = [
        f"source={struct_def['source']!r}",
        f"base_offset={struct_def['base_offset']!r}",
        f"base_offset_symbol={struct_def['base_offset_symbol']!r}",
        f"size={struct_def['size']!r}",
        f"fields=({fields})",
    ]
    if "base_struct" in struct_def:
        parts.append(f"base_struct={struct_def['base_struct']!r}")
    return f"OsStruct({', '.join(parts)})"


def _render_os_constant(constant: OsConstant) -> str:
    return f"OsConstant(raw={constant['raw']!r}, value={constant['value']!r})"


def _render_os_input(arg: OsInput) -> str:
    return (
        "OsInput("
        f"name={arg['name']!r}, "
        f"reg={arg['reg']!r}, "
        f"type={arg.get('type')!r}, "
        f"i_struct={arg.get('i_struct')!r}, "
        f"semantic_kind={arg.get('semantic_kind')!r}, "
        f"semantic_note={arg.get('semantic_note')!r}"
        ")"
    )


def _render_os_output(arg: OsOutput) -> str:
    return (
        "OsOutput("
        f"name={arg['name']!r}, "
        f"reg={arg['reg']!r}, "
        f"type={arg.get('type')!r}, "
        f"i_struct={arg.get('i_struct')!r}"
        ")"
    )


def _render_os_function(func: OsFunction) -> str:
    inputs = ", ".join(_render_os_input(arg) for arg in func.get("inputs", ()))
    if func.get("inputs"):
        if len(func["inputs"]) == 1:
            inputs += ","
        inputs_repr = f"({inputs})"
    else:
        inputs_repr = "()"
    parts = [
        f"lvo={func['lvo']!r}",
        f"inputs={inputs_repr}",
        f"output={_render_os_output(func['output']) if 'output' in func else 'None'}",
        (
            "returns_base="
            f"{'OsReturnsBase(name_reg=%r, base_reg=%r)' % (func['returns_base']['name_reg'], func['returns_base']['base_reg'])}"
            if "returns_base" in func else "returns_base=None"
        ),
        (
            "returns_memory="
            f"{'OsReturnsMemory(result_reg=%r, size_reg=%r)' % (func['returns_memory']['result_reg'], func['returns_memory'].get('size_reg'))}"
            if "returns_memory" in func else "returns_memory=None"
        ),
        f"no_return={func.get('no_return', False)!r}",
        f"os_since={func.get('os_since')!r}",
        f"fd_version={func.get('fd_version')!r}",
        f"private={func.get('private', False)!r}",
    ]
    return f"OsFunction({', '.join(parts)})"


def _write_os_runtime_python(path: Path, payload: OsRuntimePayload, *, header: str) -> None:
    meta = payload["META"]
    structs = payload["STRUCTS"]
    constants = payload["CONSTANTS"]
    libraries = payload["LIBRARIES"]
    lines = [
        '"""' + header + '"""',
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class CallingConvention:",
        "    scratch_regs: tuple[str, ...]",
        "    preserved_regs: tuple[str, ...]",
        "    base_reg: str",
        "    return_reg: str",
        "    note: str",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class ExecBaseAddress:",
        "    address: int",
        "    library: str",
        "    note: str",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class AbsoluteSymbol:",
        "    address: int",
        "    name: str",
        "    note: str",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsMeta:",
        "    calling_convention: CallingConvention",
        "    exec_base_addr: ExecBaseAddress",
        "    absolute_symbols: tuple[AbsoluteSymbol, ...]",
        "    lvo_slot_size: int",
        "    named_base_structs: dict[str, str]",
        "    constant_domains: dict[str, tuple[str, ...]]",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsStructField:",
        "    name: str",
        "    type: str",
        "    offset: int",
        "    size: int",
        "    size_symbol: str | None = None",
        "    struct: str | None = None",
        "    c_type: str | None = None",
        "    pointer_struct: str | None = None",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsStruct:",
        "    source: str",
        "    base_offset: int",
        "    base_offset_symbol: str | None",
        "    size: int",
        "    fields: tuple[OsStructField, ...]",
        "    base_struct: str | None = None",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsConstant:",
        "    raw: str",
        "    value: int | None",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsInput:",
        "    name: str",
        "    reg: str",
        "    type: str | None = None",
        "    i_struct: str | None = None",
        "    semantic_kind: str | None = None",
        "    semantic_note: str | None = None",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsOutput:",
        "    name: str",
        "    reg: str | None",
        "    type: str | None = None",
        "    i_struct: str | None = None",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsReturnsBase:",
        "    name_reg: str",
        "    base_reg: str",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsReturnsMemory:",
        "    result_reg: str",
        "    size_reg: str | None = None",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsFunction:",
        "    lvo: int | None",
        "    inputs: tuple[OsInput, ...] = ()",
        "    output: OsOutput | None = None",
        "    returns_base: OsReturnsBase | None = None",
        "    returns_memory: OsReturnsMemory | None = None",
        "    no_return: bool = False",
        "    os_since: str | None = None",
        "    fd_version: str | None = None",
        "    private: bool = False",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class OsLibrary:",
        "    lvo_index: dict[str, str]",
        "    functions: dict[str, OsFunction]",
        "",
        "META = OsMeta(",
        f"    calling_convention=CallingConvention(scratch_regs={tuple(meta['calling_convention']['scratch_regs'])!r}, preserved_regs={tuple(meta['calling_convention']['preserved_regs'])!r}, base_reg={meta['calling_convention']['base_reg']!r}, return_reg={meta['calling_convention']['return_reg']!r}, note={meta['calling_convention']['note']!r}),",
        f"    exec_base_addr=ExecBaseAddress(address={meta['exec_base_addr']['address']!r}, library={meta['exec_base_addr']['library']!r}, note={meta['exec_base_addr']['note']!r}),",
        "    absolute_symbols=(",
    ]
    for symbol in meta["absolute_symbols"]:
        lines.append(
            f"        AbsoluteSymbol(address={symbol['address']!r}, name={symbol['name']!r}, note={symbol['note']!r}),"
        )
    lines.extend([
        "    ),",
        f"    lvo_slot_size={meta['lvo_slot_size']!r},",
        f"    named_base_structs={_render_py(dict(sorted(meta['named_base_structs'].items())))} ,",
        f"    constant_domains={{{', '.join(f'{name!r}: {tuple(values)!r}' for name, values in sorted(meta['constant_domains'].items()))}}},",
        ")",
        "",
        "STRUCTS = {",
    ])
    for name, struct_def in sorted(structs.items()):
        lines.append(f"    {name!r}: {_render_os_struct(struct_def)},")
    lines.extend([
        "}",
        "",
        "CONSTANTS = {",
    ])
    for name, constant in sorted(constants.items()):
        lines.append(f"    {name!r}: {_render_os_constant(constant)},")
    lines.extend([
        "}",
        "",
        "LIBRARIES = {",
    ])
    for name, library in sorted(libraries.items()):
        lines.append(f"    {name!r}: OsLibrary(")
        lines.append(f"        lvo_index={_render_py(library['lvo_index'])},")
        lines.append("        functions={")
        for func_name, func in sorted(library["functions"].items()):
            lines.append(f"            {func_name!r}: {_render_os_function(func)},")
        lines.append("        },")
        lines.append("    ),")
    lines.extend([
        "}",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _iter_mnemonic_tokens(text: str) -> Iterator[str]:
    start = None
    for i, ch in enumerate(text):
        if ch.isspace() or ch == ",":
            if start is not None:
                yield text[start:i]
                start = None
            continue
        if start is None:
            start = i
    if start is not None:
        yield text[start:]


def _derive_varying_bits(mask_val_pairs: list[tuple[int, int]]) -> tuple[int, int]:
    if len(mask_val_pairs) < 2:
        raise RuntimeError("need at least 2 mask/val pairs to derive varying bits")
    varying = 0
    base_val = mask_val_pairs[0][1]
    for _, val in mask_val_pairs[1:]:
        varying |= base_val ^ val
    for i in range(len(mask_val_pairs)):
        for j in range(i + 1, len(mask_val_pairs)):
            varying |= mask_val_pairs[i][1] ^ mask_val_pairs[j][1]
    if varying == 0:
        raise RuntimeError("all vals are identical")
    bit_lo = (varying & -varying).bit_length() - 1
    bit_hi = varying.bit_length() - 1
    return bit_hi, bit_lo


def _runtime_size_encodings(inst: M68kInstruction) -> tuple[dict[str, int], dict[int, int]]:
    size_desc = inst.get("field_descriptions", {}).get("Size", "")
    requires_size_encoding = bool(
        re.search(r"\bByte\b|\bWord\b|\bLong\b", size_desc)
    ) or inst["mnemonic"] in {"DIVS, DIVSL", "DIVU, DIVUL", "MULS", "MULU"}

    if "size_encoding" not in inst:
        if requires_size_encoding:
            raise KeyError(f"{inst['mnemonic']}: missing required size_encoding")
        return {}, {}

    size_encoding = inst["size_encoding"]
    if size_encoding["field"] != "SIZE":
        raise ValueError(
            f"{inst['mnemonic']}: size_encoding.field must be 'SIZE', got {size_encoding['field']!r}"
        )

    size_name_to_const = {"b": 0, "w": 1, "l": 2}
    asm_map = {}
    disasm_map = {}
    for entry in size_encoding["values"]:
        size = entry["size"]
        bits = entry["bits"]
        if size in asm_map:
            raise ValueError(f"{inst['mnemonic']}: duplicate size {size!r} in size_encoding")
        if bits in disasm_map:
            raise ValueError(f"{inst['mnemonic']}: duplicate SIZE bits {bits!r} in size_encoding")
        asm_map[size] = bits
        disasm_map[bits] = size_name_to_const[size]
    if not asm_map:
        raise ValueError(f"{inst['mnemonic']}: size_encoding.values must not be empty")
    return asm_map, disasm_map


def _runtime_branch_displacement(inst: M68kInstruction,
                                 field_maps_by_idx: list[dict[str, FieldMap]],
                                 raw_fields_by_idx: list[RawFieldMap]
                                 ) -> BranchDisplacementInfo | None:
    flow = inst.get("pc_effects", {}).get("flow", {})
    if flow.get("type") not in {"branch", "call"}:
        return None

    displacement_encoding = inst.get("constraints", {}).get("displacement_encoding")
    if displacement_encoding:
        field_name = displacement_encoding["field"]
        field_map = field_maps_by_idx[0].get(inst["mnemonic"], {})
        if field_name not in field_map:
            raise KeyError(f"{inst['mnemonic']}: missing displacement field {field_name!r}")
        return {
            "kind": "inline_or_extension",
            "field_name": field_name,
            "field": field_map[field_name],
            "word_signal": displacement_encoding["word_signal"],
            "long_signal": displacement_encoding["long_signal"],
            "word_bytes": displacement_encoding["word_bits"] // 8,
            "long_bytes": displacement_encoding["long_bits"] // 8,
        }

    forms = [
        tuple(operand["type"] for operand in form.get("operands", []))
        for form in inst.get("forms", [])
    ]
    if ("dn", "label") not in forms:
        return None
    encodings = inst.get("encodings", [])
    if len(encodings) <= 1:
        raise KeyError(f"{inst['mnemonic']}: branch form missing extension displacement encoding")
    return {
        "kind": "extension_only",
        "offset_bytes": (len(encodings) - 1) * 2,
        "bytes": 2,
    }

def _project_instruction_runtime(inst: M68kInstruction) -> RuntimeInstruction:
    return {
        "mnemonic": inst["mnemonic"],
    }


def _build_m68k_runtime() -> RuntimeM68kPayload:
    payload = _load_m68k_instructions_payload()
    instructions = payload["instructions"]
    meta = payload["_meta"]
    by_name = {inst["mnemonic"]: inst for inst in instructions}

    mnemonic_index: dict[str, list[str]] = {}
    encoding_counts = {
        inst["mnemonic"]: len(inst.get("encodings", []))
        for inst in instructions
    }
    for inst in instructions:
        lowered = inst["mnemonic"].lower()
        keys = {lowered, lowered.partition(" ")[0]}
        keys.update(_iter_mnemonic_tokens(lowered))
        for key in sorted(keys):
            mnemonic_index.setdefault(key, [])
            mnemonic_index[key].append(inst["mnemonic"])

    max_encoding_count = max(len(inst.get("encodings", ())) for inst in instructions)
    encoding_masks_by_idx: list[dict[str, tuple[int, int]]] = []
    field_maps_by_idx: list[dict[str, dict[str, tuple[int, int, int]]]] = []
    raw_fields_by_idx: list[dict[str, tuple[tuple[str, int, int, int], ...]]] = []
    for enc_idx in range(max_encoding_count):
        masks: dict[str, tuple[int, int]] = {}
        field_maps: dict[str, dict[str, tuple[int, int, int]]] = {}
        raw_fields: dict[str, tuple[tuple[str, int, int, int], ...]] = {}
        for inst in instructions:
            encodings = inst.get("encodings", [])
            if len(encodings) <= enc_idx:
                continue
            mask = val = 0
            fields_map: dict[str, tuple[int, int, int]] = {}
            raw_fields_list = []
            for field in encodings[enc_idx]["fields"]:
                name = field["name"]
                if name in ("0", "1"):
                    bit = 1 if name == "1" else 0
                    for bit_index in range(field["bit_lo"], field["bit_hi"] + 1):
                        mask |= (1 << bit_index)
                        val |= (bit << bit_index)
                    continue
                spec = (field["bit_hi"], field["bit_lo"], field["width"])
                fields_map[name] = spec
                raw_fields_list.append((name, field["bit_hi"], field["bit_lo"], field["width"]))
            masks[inst["mnemonic"]] = (mask, val)
            field_maps[inst["mnemonic"]] = fields_map
            raw_fields[inst["mnemonic"]] = tuple(raw_fields_list)
        encoding_masks_by_idx.append(dict(sorted(masks.items())))
        field_maps_by_idx.append(dict(sorted(field_maps.items())))
        raw_fields_by_idx.append(dict(sorted(raw_fields.items())))

    fixed_opcodes = {
        val: mnemonic
        for mnemonic, (mask, val) in encoding_masks_by_idx[0].items()
        if mask == 0xFFFF
    }

    ext_field_names = {
        mnemonic: tuple(sorted(field_map))
        for mnemonic, field_map in field_maps_by_idx[1].items()
    }

    ea_brief_fields = {
        field["name"]: (field["bit_hi"], field["bit_lo"], field["bit_hi"] - field["bit_lo"] + 1)
        for field in meta["ea_brief_ext_word"]
    }

    size_encodings_asm = {}
    size_encodings_disasm = {}
    for inst in instructions:
        asm_map, disasm_map = _runtime_size_encodings(inst)
        if asm_map:
            size_encodings_asm[inst["mnemonic"]] = asm_map
            size_encodings_disasm[inst["mnemonic"]] = disasm_map

    cc_families: dict[str, tuple[str, M68kCcParameterized]] = {}
    for inst in instructions:
        cc_param = inst.get("constraints", {}).get("cc_parameterized")
        if cc_param:
            cc_families[cc_param["prefix"]] = (inst["mnemonic"], cc_param)

    immediate_ranges = {
        inst["mnemonic"]: (
            inst["constraints"]["immediate_range"].get("field"),
            inst["constraints"]["immediate_range"].get("bits"),
            bool(inst["constraints"]["immediate_range"].get("signed", False)),
            inst["constraints"]["immediate_range"].get("min"),
            inst["constraints"]["immediate_range"].get("max"),
            inst["constraints"]["immediate_range"].get("zero_means"),
        )
        for inst in instructions
        if inst.get("constraints", {}).get("immediate_range")
    }
    compute_formulas: dict[str, ComputeFormula] = {}
    bounds_checks: dict[str, BoundsCheck] = {}
    sp_effects: dict[str, tuple[SpEffect, ...]] = {}
    sp_effects_complete: set[str] = set()
    implicit_operands = {}
    bit_moduli = {}
    rotate_extra_bits = {}
    signed_results = {}
    instruction_sizes = {}
    operation_types = {}
    operation_classes = {}
    source_sign_extend = set()
    shift_count_moduli: dict[str, int] = {}
    shift_variant_behaviors: dict[str, tuple[ShiftVariantBehavior, ...]] = {}
    processor_020_variants: dict[str, frozenset[str]] = {}
    for inst in instructions:
        mnemonic = inst["mnemonic"]
        instruction_sizes[mnemonic] = tuple(inst.get("sizes", ()))
        operation_types[mnemonic] = inst.get("operation_type")
        operation_classes[mnemonic] = inst.get("operation_class")
        if inst.get("source_sign_extend"):
            source_sign_extend.add(mnemonic)
        if "shift_count_modulus" in inst:
            shift_count_moduli[mnemonic] = inst["shift_count_modulus"]
        formula = inst.get("compute_formula")
        if formula:
            source_bits_by_size = formula.get("source_bits_by_size")
            compute_formulas[mnemonic] = (
                formula["op"],
                tuple(formula.get("terms", ())),
                cast(tuple[int, int], tuple(formula["range_a"])) if "range_a" in formula else None,
                cast(tuple[int, int], tuple(formula["range_b"])) if "range_b" in formula else None,
                tuple((size, bits) for size, bits in source_bits_by_size.items()) if source_bits_by_size else (),
                formula.get("truncation"),
            )
        raw_bounds_check = inst.get("bounds_check")
        bounds_checks[mnemonic] = None if raw_bounds_check is None else (
            raw_bounds_check["register_operand"],
            raw_bounds_check["lower_bound"],
            raw_bounds_check["upper_bound"],
            raw_bounds_check.get("comparison"),
            bool(raw_bounds_check.get("sign_extend_bounds_for_address_register", False)),
            bool(raw_bounds_check.get("trap_on_out_of_bounds", False)),
        )
        raw_sp_effects = inst.get("sp_effects")
        if raw_sp_effects:
            sp_effects[mnemonic] = tuple(
                (effect["action"], effect.get("bytes"), effect.get("reg", effect.get("operand")))
                for effect in raw_sp_effects
            )
            if inst.get("sp_effects_complete"):
                sp_effects_complete.add(mnemonic)
        if "implicit_operand" in inst:
            implicit_operands[mnemonic] = inst["implicit_operand"]
        if "bit_modulus" in inst:
            bit_mod = inst["bit_modulus"]
            bit_moduli[mnemonic] = (bit_mod["register"], bit_mod["memory"])
        if "rotate_extra_bits" in inst:
            rotate_extra_bits[mnemonic] = inst["rotate_extra_bits"]
        if "signed" in inst:
            signed_results[mnemonic] = bool(inst["signed"])
        raw_variants = inst.get("variants", ())
        shift_behaviors = tuple(
            (
                variant["mnemonic"],
                variant["direction"],
                variant["fill"],
                bool(variant.get("arithmetic", False)),
            )
            for variant in raw_variants
            if "direction" in variant and "fill" in variant
        )
        if shift_behaviors:
            shift_variant_behaviors[mnemonic] = shift_behaviors
        variant_020 = frozenset(
            variant["mnemonic"]
            for variant in raw_variants
            if variant.get("processor_020")
        )
        if variant_020:
            processor_020_variants[mnemonic] = variant_020

    form_operand_types = {}
    form_flags_020 = {}
    primary_data_sizes = {}
    ea_mode_tables = {}
    an_sizes = {}
    operand_mode_tables: dict[str, OperandModeTable] = {}
    uses_labels = {}
    direction_form_values: dict[str, DirectionFormValue] = {}
    flow_conditional = {}
    for inst in instructions:
        mnemonic = inst["mnemonic"]
        forms = inst.get("forms", [])
        form_operand_types[mnemonic] = tuple(
            tuple(operand["type"] for operand in form.get("operands", []))
            for form in forms
        )
        form_flags_020[mnemonic] = tuple(bool(form.get("processor_020")) for form in forms)
        for form in forms:
            data_sizes = form.get("data_sizes")
            if data_sizes and not form.get("processor_020") and mnemonic not in primary_data_sizes:
                kind = data_sizes["type"]
                if kind == "multiply":
                    primary_data_sizes[mnemonic] = (
                        kind,
                        data_sizes["src_bits"],
                        data_sizes["dst_bits"],
                        data_sizes["result_bits"],
                    )
                elif kind == "divide":
                    primary_data_sizes[mnemonic] = (
                        kind,
                        data_sizes["divisor_bits"],
                        data_sizes["dividend_bits"],
                        data_sizes["quotient_bits"],
                    )
                else:
                    raise KeyError(f"unsupported primary data size kind {kind!r} for {mnemonic}")
        ea_modes = inst.get("ea_modes") or {}
        ea_mode_tables[mnemonic] = (
            tuple(ea_modes.get("src", ())),
            tuple(ea_modes.get("dst", ())),
            tuple(ea_modes.get("ea", ())),
        )
        raw_constraints = inst.get("constraints", {})
        an_sizes[mnemonic] = tuple(raw_constraints.get("an_sizes", ()))
        operand_modes = raw_constraints.get("operand_modes")
        if operand_modes:
            operand_mode_tables[mnemonic] = (
                operand_modes["field"],
                {
                    int(key): tuple(value.split(","))
                    for key, value in operand_modes["values"].items()
                },
            )
        uses_labels[mnemonic] = bool(inst.get("uses_label"))
        if "direction_field_values" in inst:
            field_name = inst["direction_field_values"]["field"]
            form_field_value = inst["direction_field_values"]["form_field_value"]
            max_form_idx = max(int(key) for key in form_field_value)
            direction_form_values[mnemonic] = (
                field_name,
                tuple(form_field_value[str(idx)] for idx in range(max_form_idx + 1)),
            )
        flow_conditional[mnemonic] = bool(inst["pc_effects"]["flow"]["conditional"])

    opmode_tables_list = {
        inst["mnemonic"]: inst["constraints"]["opmode_table"]
        for inst in instructions
        if inst.get("constraints", {}).get("opmode_table")
    }
    opmode_tables_by_value: dict[str, dict[int, OpmodeEntry]] = {
        mnemonic: {
            entry["opmode"]: OpmodeEntry(
                entry.get("size"),
                entry.get("description") or entry.get("operation"),
                entry.get("ea_is_source"),
                entry.get("source"),
                entry.get("destination"),
                entry.get("rx_mode"),
                entry.get("ry_mode"),
            )
            for entry in table
        }
        for mnemonic, table in opmode_tables_list.items()
    }

    pmmu_codes = tuple(code.lower() for code in meta["pmmu_condition_codes"])
    cpu_codes = set(meta["cc_test_definitions"])
    cpu_codes.update(meta["cc_aliases"])
    derived_cc_families = {}
    for inst in instructions:
        cc_param = inst.get("constraints", {}).get("cc_parameterized")
        is_pmmu = "68851" in inst.get("processors", "")
        codes = pmmu_codes if is_pmmu else tuple(sorted(cpu_codes))
        if cc_param:
            derived_cc_families[cc_param["prefix"].lower()] = (
                inst["mnemonic"],
                tuple(codes),
                is_pmmu,
            )
            continue
        for raw_name in inst["mnemonic"].split(","):
            name = raw_name.strip()
            if not name.endswith("cc"):
                continue
            prefix = name[:-2].lower()
            if not prefix or prefix in derived_cc_families:
                continue
            derived_cc_families[prefix] = (name, tuple(codes), is_pmmu)

    asm_mnemonic_index: dict[str, str] = {}
    for syntax_key, kb_mnemonic in meta["asm_syntax_index"].items():
        asm_mnemonic, _, raw_operand_types = syntax_key.partition(":")
        if raw_operand_types:
            continue
        existing = asm_mnemonic_index.get(asm_mnemonic)
        if existing is not None and existing != kb_mnemonic:
            raise ValueError(f"duplicate bare mnemonic mapping for {asm_mnemonic!r}")
        if kb_mnemonic not in by_name:
            raise ValueError(f"asm_syntax_index maps {asm_mnemonic!r} to missing {kb_mnemonic!r}")
        asm_mnemonic_index[asm_mnemonic] = kb_mnemonic

    reg_masks = meta["movem_reg_masks"]["normal"]
    data_regs = [reg for reg in reg_masks if reg.startswith("d")]
    addr_regs = [reg for reg in reg_masks if reg.startswith("a")]
    if not addr_regs:
        raise KeyError("KB movem_reg_masks has no address registers")
    derived_meta = {
        "_cc_families": dict(sorted(derived_cc_families.items())),
        "_asm_mnemonic_index": dict(sorted(asm_mnemonic_index.items())),
        "_num_data_regs": len(data_regs),
        "_num_addr_regs": len(addr_regs),
        "_sp_reg_num": int(addr_regs[-1][1:]),
    }

    register_fields = {}
    dest_reg_field = {}
    for mnemonic, fields in raw_fields_by_idx[0].items():
        reg_fields = sorted(
            [
                (hi, lo, width)
                for name, hi, lo, width in fields
                if name.startswith("REGISTER")
            ],
            reverse=True,
        )
        if reg_fields:
            register_fields[mnemonic] = tuple(reg_fields)
            if len(reg_fields) >= 2:
                dest_reg_field[mnemonic] = reg_fields[0]
            elif reg_fields[0][0] >= 9:
                dest_reg_field[mnemonic] = reg_fields[0]

    bf_mnemonics = tuple(sorted(mn for mn in encoding_masks_by_idx[0] if mn.startswith("BF")))

    def _derive_name_table(
        mnemonics: tuple[str, ...],
        names: tuple[str, ...],
        enc_idx: int = 0,
    ) -> tuple[dict[int, str], FieldSpec]:
        pairs = [encoding_masks_by_idx[enc_idx][mn] for mn in mnemonics]
        hi, lo = _derive_varying_bits(pairs)
        width = hi - lo + 1
        table: dict[int, str] = {}
        for mnemonic, label in zip(mnemonics, names):
            _, val = encoding_masks_by_idx[enc_idx][mnemonic]
            table[(val >> lo) & ((1 << width) - 1)] = label
        return table, (hi, lo, width)

    bitop_names, bitop_field = _derive_name_table(
        ("BTST", "BCHG", "BCLR", "BSET"),
        ("btst", "bchg", "bclr", "bset"),
    )
    imm_names, imm_field = _derive_name_table(
        ("ORI", "ANDI", "SUBI", "ADDI", "EORI", "CMPI"),
        ("ori", "andi", "subi", "addi", "eori", "cmpi"),
    )
    shift_names, _ = _derive_name_table(
        ("ASL, ASR", "LSL, LSR", "ROXL, ROXR", "ROL, ROR"),
        ("as", "ls", "rox", "ro"),
    )
    reg_shift_field = _derive_varying_bits([encoding_masks_by_idx[0][mn] for mn in ("ASL, ASR", "LSL, LSR", "ROXL, ROXR", "ROL, ROR")])
    mem_shift_field = _derive_varying_bits([encoding_masks_by_idx[1][mn] for mn in ("ASL, ASR", "LSL, LSR", "ROXL, ROXR", "ROL, ROR")])
    shift_type_fields = (
        (reg_shift_field[0], reg_shift_field[1], reg_shift_field[0] - reg_shift_field[1] + 1),
        (mem_shift_field[0], mem_shift_field[1], mem_shift_field[0] - mem_shift_field[1] + 1),
    )

    shift_fields: ShiftFieldsData | None = None
    direction_variants: dict[str, DirectionVariant] = {}
    for inst in instructions:
        dv = inst.get("constraints", {}).get("direction_variants")
        if dv:
            field_map = field_maps_by_idx[0].get(inst["mnemonic"], {})
            direction_variants[inst["mnemonic"]] = (
                field_map[dv["field"]],
                dv["base"],
                tuple(dv["variants"]),
                {int(key): value for key, value in dv["values"].items()},
            )
        if shift_fields is None and inst["mnemonic"].startswith("ASL"):
            shift_fields = {
                "dr_field": direction_variants[inst["mnemonic"]][0],
                "dr_values": direction_variants[inst["mnemonic"]][3],
                "zero_means": inst["constraints"]["immediate_range"]["zero_means"],
            }
    if shift_fields is None:
        raise RuntimeError("KB missing ASL/ASR")

    rm_field = {}
    for inst in instructions:
        operand_modes = inst.get("constraints", {}).get("operand_modes")
        if not operand_modes or operand_modes.get("field") != "R/M":
            continue
        rm_bits = field_maps_by_idx[0].get(inst["mnemonic"], {}).get("R/M")
        if rm_bits:
            rm_field[inst["mnemonic"]] = (rm_bits[0], {int(key): value for key, value in operand_modes["values"].items()})

    addq_zero_means = immediate_ranges["ADDQ"][5]
    control_registers: dict[int, str] = {}
    for control in by_name["MOVEC"]["constraints"]["control_registers"]:
        hex_value = int(control["hex"], 16)
        control_registers.setdefault(hex_value, control["abbrev"])

    processor_mins = {}
    for inst in instructions:
        min_cpu = inst["processor_min"]
        for part in inst["mnemonic"].split(","):
            tokens = part.strip().split()
            for token in tokens:
                processor_mins[token.lower()] = min_cpu[2:] if min_cpu.startswith("-m") else min_cpu

    condition_families = tuple(
        (
            entry["prefix"],
            entry["canonical"],
            tuple(entry["codes"]),
            entry["match_numeric_suffix"],
            tuple(entry["exclude_from_family"]),
        )
        for entry in meta["condition_families"]
    )

    branch_inline_displacements: dict[str, BranchInlineDisplacement] = {}
    branch_extension_displacements: dict[str, BranchExtensionDisplacement] = {}
    for inst in instructions:
        branch_info = _runtime_branch_displacement(inst, field_maps_by_idx, raw_fields_by_idx)
        if branch_info is not None:
            if branch_info["kind"] == "inline_or_extension":
                branch_inline_displacements[inst["mnemonic"]] = (
                    branch_info["field_name"],
                    branch_info["field"],
                    branch_info["word_signal"],
                    branch_info["long_signal"],
                    branch_info["word_bytes"],
                    branch_info["long_bytes"],
                )
            elif branch_info["kind"] == "extension_only":
                branch_extension_displacements[inst["mnemonic"]] = (
                    branch_info["offset_bytes"],
                    branch_info["bytes"],
                )
            else:
                raise ValueError(f"{inst['mnemonic']}: unknown branch displacement kind {branch_info['kind']!r}")

    move_raw = raw_fields_by_idx[0]["MOVE"]
    move_modes = sorted([(hi, lo, width) for name, hi, lo, width in move_raw if name == "MODE"], reverse=True)
    move_regs = sorted([(hi, lo, width) for name, hi, lo, width in move_raw if name == "REGISTER"], reverse=True)
    move_fields = (move_regs[0], move_modes[0], move_modes[1], move_regs[1])

    movem_field_map = field_maps_by_idx[0].get("MOVEM")
    if movem_field_map is None:
        raise KeyError("MOVEM: missing opword field map")
    movem_fields = {
        "dr": movem_field_map["dr"],
        "size": movem_field_map["SIZE"],
        "mode": movem_field_map["MODE"],
        "register": movem_field_map["REGISTER"],
    }

    frestore = by_name["FRESTORE"]
    id_field = next(field for field in frestore["encodings"][0]["fields"] if field["name"] == "ID")
    cpid_field = (id_field["bit_lo"], id_field["width"])

    ea_mode_names: set[str] = set(meta["ea_mode_encoding"].keys())
    generic_types: set[str] = ea_mode_names | {"ea", "imm", "label", "reglist", "ctrl_reg",
                                               "rn", "bf_ea", "unknown", "dn_pair",
                                               "disp", "postinc", "predec"}
    asm_syntax_index: dict[tuple[str, tuple[str, ...]], str] = {}
    all_types: set[str] = set()
    for key, kb_mnemonic in sorted(meta["asm_syntax_index"].items()):
        mnemonic, _, raw_operand_types = key.partition(":")
        operand_types: tuple[str, ...] = tuple(raw_operand_types.split(",")) if raw_operand_types else ()
        asm_syntax_index[(mnemonic, operand_types)] = kb_mnemonic
        all_types.update(operand_types)
    special_operand_types = tuple(sorted(all_types - generic_types))
    flow_types = {
        inst["mnemonic"]: inst["pc_effects"]["flow"]["type"]
        for inst in instructions
    }

    runtime_instructions = [_project_instruction_runtime(inst) for inst in instructions]
    mnemonic_index_out = {
        key: tuple(values)
        for key, values in sorted(mnemonic_index.items())
    }
    runtime_meta = cast(RuntimeM68kMeta, {**meta, **derived_meta})

    return {
        "instructions": runtime_instructions,
        "meta": runtime_meta,
        "tables": {
            "mnemonic_index": mnemonic_index_out,
            "encoding_counts": dict(sorted(encoding_counts.items())),
            "encoding_masks": tuple(encoding_masks_by_idx),
            "fixed_opcodes": dict(sorted(fixed_opcodes.items())),
            "ext_field_names": dict(sorted(ext_field_names.items())),
            "field_maps": tuple(field_maps_by_idx),
            "raw_fields": tuple(raw_fields_by_idx),
            "ea_brief_fields": ea_brief_fields,
            "size_encodings_asm": dict(sorted(size_encodings_asm.items())),
            "size_encodings_disasm": dict(sorted(size_encodings_disasm.items())),
            "cc_families": dict(sorted(cc_families.items())),
              "immediate_ranges": dict(sorted(immediate_ranges.items())),
              "compute_formulas": dict(sorted(compute_formulas.items())),
              "bounds_checks": dict(sorted(bounds_checks.items())),
              "sp_effects": dict(sorted(sp_effects.items())),
              "sp_effects_complete": tuple(sorted(sp_effects_complete)),
              "implicit_operands": dict(sorted(implicit_operands.items())),
              "bit_moduli": dict(sorted(bit_moduli.items())),
              "rotate_extra_bits": dict(sorted(rotate_extra_bits.items())),
              "signed_results": dict(sorted(signed_results.items())),
              "instruction_sizes": dict(sorted(instruction_sizes.items())),
              "operation_types": dict(sorted(operation_types.items())),
              "operation_classes": dict(sorted(operation_classes.items())),
              "source_sign_extend": tuple(sorted(source_sign_extend)),
              "shift_count_moduli": dict(sorted(shift_count_moduli.items())),
              "opmode_tables_list": dict(sorted(opmode_tables_list.items())),
            "opmode_tables_by_value": dict(sorted(opmode_tables_by_value.items())),
            "form_operand_types": dict(sorted(form_operand_types.items())),
            "form_flags_020": dict(sorted(form_flags_020.items())),
            "primary_data_sizes": dict(sorted(primary_data_sizes.items())),
            "ea_mode_tables": dict(sorted(ea_mode_tables.items())),
            "an_sizes": dict(sorted(an_sizes.items())),
            "operand_mode_tables": dict(sorted(operand_mode_tables.items())),
            "direction_variants": dict(sorted(direction_variants.items())),
            "register_fields": dict(sorted(register_fields.items())),
            "dest_reg_field": dict(sorted(dest_reg_field.items())),
            "bf_mnemonics": bf_mnemonics,
            "bitop_names": (dict(sorted(bitop_names.items())), bitop_field),
            "imm_names": (dict(sorted(imm_names.items())), imm_field),
            "shift_names": dict(sorted(shift_names.items())),
            "shift_type_fields": shift_type_fields,
            "shift_fields": shift_fields,
            "rm_field": dict(sorted(rm_field.items())),
            "addq_zero_means": addq_zero_means,
            "control_registers": dict(sorted(control_registers.items())),
            "processor_mins": dict(sorted(processor_mins.items())),
            "flow_types": dict(sorted(flow_types.items())),
            "flow_conditional": dict(sorted(flow_conditional.items())),
            "condition_families": tuple(condition_families),
            "branch_inline_displacements": dict(sorted(branch_inline_displacements.items())),
            "branch_extension_displacements": dict(sorted(branch_extension_displacements.items())),
            "move_fields": move_fields,
            "movem_fields": movem_fields,
            "cpid_field": cpid_field,
            "asm_syntax_index": asm_syntax_index,
            "special_operand_types": special_operand_types,
            "uses_labels": dict(sorted(uses_labels.items())),
            "direction_form_values": dict(sorted(direction_form_values.items())),
            "shift_variant_behaviors": dict(sorted(shift_variant_behaviors.items())),
            "processor_020_variants": dict(sorted(processor_020_variants.items())),
        },
    }


def _build_os_runtime() -> OsRuntimePayload:
    canonical = _load_os_reference_payload()
    libraries: dict[str, OsRuntimeLibrary] = {}
    for library_name, library_data in sorted(canonical["libraries"].items()):
        funcs: dict[str, OsFunction] = {}
        for func_name, func_data in sorted(library_data["functions"].items()):
            compact: OsFunction = {"lvo": func_data["lvo"]}
            for key in (
                "returns_base",
                "returns_memory",
                "output",
                "no_return",
                "inputs",
                "os_since",
                "fd_version",
                "private",
            ):
                if key in func_data:
                    compact[key] = func_data[key]
            funcs[func_name] = compact
        libraries[library_name] = {
            "lvo_index": library_data["lvo_index"],
            "functions": funcs,
        }
    return {
        "META": {
            "calling_convention": canonical["_meta"]["calling_convention"],
            "exec_base_addr": canonical["_meta"]["exec_base_addr"],
            "absolute_symbols": canonical["_meta"]["absolute_symbols"],
            "lvo_slot_size": canonical["_meta"]["lvo_slot_size"],
            "named_base_structs": canonical["_meta"]["named_base_structs"],
            "constant_domains": canonical["_meta"]["constant_domains"],
        },
        "STRUCTS": canonical["structs"],
        "CONSTANTS": canonical["constants"],
        "LIBRARIES": libraries,
    }


def _build_m68k_decode_runtime(runtime_payload: RuntimeM68kPayload) -> M68kDecodeRuntimePayload:
    meta = runtime_payload["meta"]
    tables = runtime_payload["tables"]
    ea_field_specs = {}
    for mnemonic, fields in tables["raw_fields"][0].items():
        mode_field = None
        reg_field = None
        for name, bit_hi, bit_lo, width in fields:
            if name == "MODE":
                mode_field = (bit_hi, bit_lo, width)
            elif name == "REGISTER" and bit_hi <= 5:
                reg_field = (bit_hi, bit_lo, width)
        if mode_field is not None and reg_field is not None:
            ea_field_specs[mnemonic] = (mode_field, reg_field)
    direct_modes = {"dn", "an"}
    auto_modify_modes = {"postinc", "predec"}
    return {
        "OPWORD_BYTES": meta["opword_bytes"],
        "ALIGN_MASK": meta["opword_bytes"] - 1,
        "DEFAULT_OPERAND_SIZE": meta["default_operand_size"],
        "SIZE_BYTE_COUNT": meta["size_byte_count"],
        "EA_MODE_ENCODING": meta["ea_mode_encoding"],
        "REG_INDIRECT_MODES": tuple(sorted(
            name
            for name, (_mode_val, reg_val) in meta["ea_mode_encoding"].items()
            if reg_val is None
            and name not in direct_modes
            and name not in auto_modify_modes
        )),
        "MOVEM_REG_MASKS": meta["movem_reg_masks"],
        "SP_REG_NUM": meta["_sp_reg_num"],
        "NUM_DATA_REGS": meta["_num_data_regs"],
        "NUM_ADDR_REGS": meta["_num_addr_regs"],
        "EA_BRIEF_FIELDS": tables["ea_brief_fields"],
        "EA_FULL_FIELDS": {
            field["name"]: (
                field["bit_hi"],
                field["bit_lo"],
                field["bit_hi"] - field["bit_lo"] + 1,
            )
            for field in meta["ea_full_ext_word"]
        },
        "EA_FULL_BD_SIZE": meta["ea_full_ext_bd_size"],
        "ENCODING_COUNTS": tables["encoding_counts"],
        "ENCODING_MASKS": tables["encoding_masks"],
        "FIELD_MAPS": tables["field_maps"],
        "RAW_FIELDS": tables["raw_fields"],
        "EA_FIELD_SPECS": ea_field_specs,
        "EXT_FIELD_NAMES": tables["ext_field_names"],
        "FORM_OPERAND_TYPES": tables["form_operand_types"],
        "OPERATION_TYPES": tables["operation_types"],
        "SOURCE_SIGN_EXTEND": tables["source_sign_extend"],
        "OPMODE_TABLES_BY_VALUE": tables["opmode_tables_by_value"],
        "OPERAND_MODE_TABLES": tables["operand_mode_tables"],
        "EA_MODE_TABLES": tables["ea_mode_tables"],
        "AN_SIZES": tables["an_sizes"],
        "IMMEDIATE_RANGES": tables["immediate_ranges"],
        "REGISTER_FIELDS": tables["register_fields"],
        "DEST_REG_FIELD": tables["dest_reg_field"],
        "DIRECTION_VARIANTS": tables["direction_variants"],
        "SHIFT_FIELDS": tables["shift_fields"],
        "RM_FIELD": tables["rm_field"],
        "CONTROL_REGISTERS": tables["control_registers"],
        "MOVE_FIELDS": tables["move_fields"],
        "MOVEM_FIELDS": tables["movem_fields"],
        "CPID_FIELD": tables["cpid_field"],
    }


def _build_m68k_disasm_runtime(runtime_payload: RuntimeM68kPayload) -> M68kDisasmRuntimePayload:
    meta = runtime_payload["meta"]
    tables = runtime_payload["tables"]
    return {
        "MNEMONIC_INDEX": tables["mnemonic_index"],
        "ENCODING_COUNTS": tables["encoding_counts"],
        "ENCODING_MASKS": tables["encoding_masks"],
        "FIXED_OPCODES": tables["fixed_opcodes"],
        "EXT_FIELD_NAMES": tables["ext_field_names"],
        "FIELD_MAPS": tables["field_maps"],
        "RAW_FIELDS": tables["raw_fields"],
        "FORM_OPERAND_TYPES": tables["form_operand_types"],
        "EA_BRIEF_FIELDS": tables["ea_brief_fields"],
        "MOVEM_REG_MASKS": meta["movem_reg_masks"],
        "DEST_REG_FIELD": tables["dest_reg_field"],
        "BF_MNEMONICS": tables["bf_mnemonics"],
        "BITOP_NAMES": tables["bitop_names"],
        "IMM_NAMES": tables["imm_names"],
        "SHIFT_NAMES": tables["shift_names"],
        "SHIFT_TYPE_FIELDS": tables["shift_type_fields"],
        "SHIFT_FIELDS": tables["shift_fields"],
        "RM_FIELD": tables["rm_field"],
        "ADDQ_ZERO_MEANS": tables["addq_zero_means"],
        "CONTROL_REGISTERS": tables["control_registers"],
        "SIZE_ENCODINGS_DISASM": tables["size_encodings_disasm"],
        "INSTRUCTION_SIZES": tables["instruction_sizes"],
        "OPERATION_TYPES": tables["operation_types"],
        "OPERATION_CLASSES": tables["operation_classes"],
        "SOURCE_SIGN_EXTEND": tables["source_sign_extend"],
        "SHIFT_COUNT_MODULI": tables["shift_count_moduli"],
        "PROCESSOR_MINS": tables["processor_mins"],
        "OPMODE_TABLES_BY_VALUE": tables["opmode_tables_by_value"],
        "CONDITION_FAMILIES": tables["condition_families"],
        "CONDITION_CODES": tuple(meta["condition_codes"]),
        "CPU_HIERARCHY": meta["cpu_hierarchy"],
        "PMMU_CONDITION_CODES": tuple(meta["pmmu_condition_codes"]),
        "DEFAULT_OPERAND_SIZE": meta["default_operand_size"],
        "MOVE_FIELDS": tables["move_fields"],
        "CPID_FIELD": tables["cpid_field"],
    }


def _build_m68k_asm_runtime(runtime_payload: RuntimeM68kPayload) -> M68kAsmRuntimePayload:
    meta = runtime_payload["meta"]
    tables = runtime_payload["tables"]
    lookup_upper = {
        inst["mnemonic"].upper(): inst["mnemonic"]
        for inst in runtime_payload["instructions"]
    }
    for inst in runtime_payload["instructions"]:
        mnemonic = inst["mnemonic"]
        if "," in mnemonic:
            for part in mnemonic.split(","):
                lookup_upper[part.strip().upper()] = mnemonic
    for mnemonic, kb_name in meta["_asm_mnemonic_index"].items():
        lookup_upper[mnemonic.upper()] = kb_name
    return {
        "ENCODING_COUNTS": tables["encoding_counts"],
        "ENCODING_MASKS": tables["encoding_masks"],
        "FIELD_MAPS": tables["field_maps"],
        "RAW_FIELDS": tables["raw_fields"],
        "LOOKUP_UPPER": dict(sorted(lookup_upper.items())),
        "EA_MODE_ENCODING": meta["ea_mode_encoding"],
        "EA_BRIEF_FIELDS": tables["ea_brief_fields"],
        "SIZE_BYTE_COUNT": meta["size_byte_count"],
        "CONDITION_CODES": tuple(meta["condition_codes"]),
        "CC_ALIASES": meta["cc_aliases"],
        "MOVEM_REG_MASKS": meta["movem_reg_masks"],
        "IMMEDIATE_ROUTING": meta["immediate_routing"],
        "SIZE_ENCODINGS_ASM": tables["size_encodings_asm"],
        "INSTRUCTION_SIZES": tables["instruction_sizes"],
        "OPERATION_TYPES": tables["operation_types"],
        "SOURCE_SIGN_EXTEND": tables["source_sign_extend"],
        "OPMODE_TABLES_LIST": tables["opmode_tables_list"],
        "FORM_OPERAND_TYPES": tables["form_operand_types"],
        "FORM_FLAGS_020": tables["form_flags_020"],
        "EA_MODE_TABLES": tables["ea_mode_tables"],
        "CC_FAMILIES": tables["cc_families"],
        "IMMEDIATE_RANGES": tables["immediate_ranges"],
        "DIRECTION_VARIANTS": tables["direction_variants"],
        "BRANCH_INLINE_DISPLACEMENTS": tables["branch_inline_displacements"],
        "AN_SIZES": tables["an_sizes"],
        "USES_LABELS": tables["uses_labels"],
        "DIRECTION_FORM_VALUES": tables["direction_form_values"],
        "SPECIAL_OPERAND_TYPES": tables["special_operand_types"],
        "ASM_SYNTAX_INDEX": tables["asm_syntax_index"],
    }


def _build_m68k_analysis_runtime(runtime_payload: RuntimeM68kPayload) -> M68kAnalysisRuntimePayload:
    meta = runtime_payload["meta"]
    instructions = runtime_payload["instructions"]
    tables = runtime_payload["tables"]
    rts_sp_inc = sum(
        nbytes or 0
        for action, nbytes, _ in tables["sp_effects"]["RTS"]
        if action == "increment"
    )
    if not rts_sp_inc:
        raise ValueError("RTS has no increment SP effect")
    addr_size = next(
        (size for size, nbytes in meta["size_byte_count"].items() if nbytes == rts_sp_inc),
        None,
    )
    if addr_size is None:
        raise ValueError(
            f"size_byte_count has no entry for {rts_sp_inc} bytes (RTS pop size)"
        )
    ea_reverse = {}
    for name, (mode, reg) in meta["ea_mode_encoding"].items():
        if reg is not None:
            ea_reverse[(mode, reg)] = name
            continue
        for index in range(8):
            ea_reverse.setdefault((mode, index), name)
    lookup_cc_families = {}
    for prefix, family in meta["_cc_families"].items():
        lookup_cc_families[prefix] = (
            family[0],
            tuple(family[1]),
            family[2],
        )
    lookup_canonical = {}
    lookup_upper = {
        name.upper(): name
        for name in {inst["mnemonic"] for inst in instructions}
    }
    for mnemonic, kb_name in meta["_asm_mnemonic_index"].items():
        lookup_upper[mnemonic.upper()] = kb_name
    for inst in instructions:
        mnemonic = inst["mnemonic"]
        if "," in mnemonic:
            for part in mnemonic.split(","):
                lookup_upper[part.strip().upper()] = mnemonic
    for upper_name, kb_name in lookup_upper.items():
        lookup_canonical[upper_name] = kb_name
    numeric_cc_prefixes = {}
    for prefix, (kb_name, codes, match_numeric_suffix) in lookup_cc_families.items():
        prefix_upper = prefix.upper()
        if match_numeric_suffix:
            numeric_cc_prefixes[prefix_upper] = kb_name
        for code in codes:
            lookup_canonical[f"{prefix_upper}{code.upper()}"] = kb_name
    cc_test_definitions = {
        name: (entry["encoding"], entry["test"])
        for name, entry in meta["cc_test_definitions"].items()
    }
    return {
        "OPWORD_BYTES": meta["opword_bytes"],
        "DEFAULT_OPERAND_SIZE": meta["default_operand_size"],
        "SIZE_BYTE_COUNT": meta["size_byte_count"],
        "EA_MODE_ENCODING": meta["ea_mode_encoding"],
        "EA_REVERSE": ea_reverse,
        "EA_BRIEF_FIELDS": tables["ea_brief_fields"],
        "EA_MODE_SIZES": meta["ea_mode_sizes"],
        "MOVEM_REG_MASKS": meta["movem_reg_masks"],
        "CC_TEST_DEFINITIONS": cc_test_definitions,
        "CC_ALIASES": meta["cc_aliases"],
        "REGISTER_ALIASES": meta["register_aliases"],
        "NUM_DATA_REGS": meta["_num_data_regs"],
        "NUM_ADDR_REGS": meta["_num_addr_regs"],
        "SP_REG_NUM": meta["_sp_reg_num"],
        "RTS_SP_INC": rts_sp_inc,
        "ADDR_SIZE": addr_size,
        "ADDR_MASK": (1 << (rts_sp_inc * 8)) - 1,
        "CCR_FLAG_NAMES": tuple(meta["ccr_bit_positions"]),
        "OPERATION_TYPES": tables["operation_types"],
        "OPERATION_CLASSES": tables["operation_classes"],
        "SOURCE_SIGN_EXTEND": tables["source_sign_extend"],
        "FLOW_TYPES": tables["flow_types"],
        "FLOW_CONDITIONAL": tables["flow_conditional"],
        "BOUNDS_CHECKS": tables["bounds_checks"],
        "COMPUTE_FORMULAS": tables["compute_formulas"],
        "SP_EFFECTS": tables["sp_effects"],
        "SP_EFFECTS_COMPLETE": tables["sp_effects_complete"],
        "EA_MODE_TABLES": tables["ea_mode_tables"],
        "AN_SIZES": tables["an_sizes"],
        "PROCESSOR_MINS": tables["processor_mins"],
        "PROCESSOR_020_VARIANTS": tables["processor_020_variants"],
        "LOOKUP_UPPER": dict(sorted(lookup_upper.items())),
        "LOOKUP_CANONICAL": dict(sorted(lookup_canonical.items())),
        "LOOKUP_NUMERIC_CC_PREFIXES": dict(sorted(numeric_cc_prefixes.items())),
        "LOOKUP_CC_FAMILIES": lookup_cc_families,
        "LOOKUP_ASM_MNEMONIC_INDEX": meta["_asm_mnemonic_index"],
    }


def _build_m68k_compute_runtime(runtime_payload: RuntimeM68kPayload) -> M68kComputeRuntimePayload:
    tables = runtime_payload["tables"]
    return {
        "OPERATION_TYPES": tables["operation_types"],
        "COMPUTE_FORMULAS": tables["compute_formulas"],
        "IMPLICIT_OPERANDS": tables["implicit_operands"],
        "SP_EFFECTS": tables["sp_effects"],
        "PRIMARY_DATA_SIZES": tables["primary_data_sizes"],
    }


def _build_m68k_executor_runtime(runtime_payload: RuntimeM68kPayload) -> M68kExecutorRuntimePayload:
    tables = runtime_payload["tables"]
    shift_fields = tables["shift_fields"]
    dr_values = shift_fields["dr_values"]
    max_dr_value = max(dr_values) if dr_values else -1
    return {
        "FIELD_MAPS": tables["field_maps"],
        "RAW_FIELDS": tables["raw_fields"],
        "OPERAND_MODE_TABLES": tables["operand_mode_tables"],
        "REGISTER_FIELDS": tables["register_fields"],
        "RM_FIELD": tables["rm_field"],
        "IMPLICIT_OPERANDS": tables["implicit_operands"],
        "OPMODE_TABLES_BY_VALUE": tables["opmode_tables_by_value"],
        "MOVEM_FIELDS": tables["movem_fields"],
        "IMMEDIATE_RANGES": tables["immediate_ranges"],
        "DEST_REG_FIELD": tables["dest_reg_field"],
        "OPERATION_TYPES": tables["operation_types"],
        "OPERATION_CLASSES": tables["operation_classes"],
        "SOURCE_SIGN_EXTEND": tables["source_sign_extend"],
        "BOUNDS_CHECKS": tables["bounds_checks"],
        "BIT_MODULI": tables["bit_moduli"],
        "SHIFT_COUNT_MODULI": tables["shift_count_moduli"],
        "ROTATE_EXTRA_BITS": tables["rotate_extra_bits"],
        "DIRECTION_VARIANTS": tables["direction_variants"],
        "SHIFT_FIELDS": (
            shift_fields["dr_field"],
            tuple(dr_values.get(idx) for idx in range(max_dr_value + 1)),
            shift_fields["zero_means"],
        ),
        "SHIFT_VARIANT_BEHAVIORS": tables["shift_variant_behaviors"],
        "PRIMARY_DATA_SIZES": tables["primary_data_sizes"],
        "SIGNED_RESULTS": tables["signed_results"],
        "BRANCH_INLINE_DISPLACEMENTS": tables["branch_inline_displacements"],
        "BRANCH_EXTENSION_DISPLACEMENTS": tables["branch_extension_displacements"],
    }


def _build_passthrough(name: str) -> JsonObject:
    return _load_json(name)


def _build_hunk_runtime() -> HunkRuntimePayload:
    canonical = _load_hunk_format_payload()
    return {
        "META": canonical["_meta"],
        "HUNK_TYPES": canonical["hunk_types"],
        "EXT_TYPES": canonical["ext_types"],
        "MEMORY_FLAGS": canonical["memory_flags"],
        "MEMORY_TYPE_CODES": canonical["memory_type_codes"],
        "EXT_TYPE_CATEGORIES": canonical["ext_type_categories"],
        "COMPATIBILITY_NOTES": canonical["compatibility_notes"],
        "RELOC_FORMATS": canonical["reloc_formats"],
        "RELOCATION_SEMANTICS": {
            name: (entry["bytes"], entry["mode"])
            for name, entry in canonical["relocation_semantics"].items()
        },
        "HUNK_CONTENT_FORMATS": canonical["hunk_content_formats"],
    }


def _build_naming_runtime() -> NamingRuntimePayload:
    canonical = _load_naming_rules_payload()
    return {
        "META": canonical["_meta"],
        "PATTERNS": canonical["patterns"],
        "TRIVIAL_FUNCTIONS": canonical["trivial_functions"],
        "GENERIC_PREFIX": canonical["generic_prefix"],
    }


def _build_hardware_runtime() -> HardwareRuntimePayload:
    canonical = _load_hardware_symbols_payload()
    registers: dict[int, HardwareRuntimeRegisterDef] = {}
    for entry in canonical["registers"]:
        cpu_address = int(entry["cpu_address"], 16)
        symbols = tuple(entry["symbols"])
        if not symbols:
            raise ValueError(f"Hardware entry missing symbols for ${cpu_address:08X}")
        preferred = symbols[0]
        if cpu_address in registers and registers[cpu_address]["symbol"] != preferred:
            raise ValueError(
                f"Conflicting hardware register name for ${cpu_address:08X}: "
                f"{registers[cpu_address]['symbol']!r} vs {preferred!r}"
            )
        registers[cpu_address] = {
            "symbol": preferred,
            "aliases": symbols[1:],
            "family": entry["family"],
            "include": entry["include"],
            "base_symbol": entry["base_symbol"],
            "offset": int(entry["offset"], 16),
        }
    return {
        "META": canonical["_meta"],
        "REGISTER_DEFS": registers,
    }


def build_runtime_artifacts() -> list[Path]:
    RUNTIME_PY_DIR.mkdir(exist_ok=True)
    init_py = RUNTIME_PY_DIR / "__init__.py"
    if not init_py.exists():
        init_py.write_text(
            '"""Generated Python runtime KB modules. Do not edit directly."""\n',
            encoding="utf-8",
        )
    outputs = []
    m68k_runtime = _build_m68k_runtime()
    outputs.append(RUNTIME_PY_DIR / "runtime_m68k.py")
    _write_m68k_runtime_python(outputs[-1], m68k_runtime,
                               header="Generated runtime M68K knowledge artifact. Do not edit directly.")
    outputs.append(RUNTIME_PY_DIR / "runtime_m68k_decode.py")
    _write_m68k_decode_runtime_python(
        outputs[-1],
        _build_m68k_decode_runtime(m68k_runtime),
        header="Generated runtime M68K decode knowledge artifact. Do not edit directly.",
    )
    outputs.append(RUNTIME_PY_DIR / "runtime_m68k_disasm.py")
    _write_m68k_disasm_runtime_python(
        outputs[-1],
        _build_m68k_disasm_runtime(m68k_runtime),
        header="Generated runtime M68K disassembly knowledge artifact. Do not edit directly.",
    )
    outputs.append(RUNTIME_PY_DIR / "runtime_m68k_asm.py")
    _write_m68k_asm_runtime_python(
        outputs[-1],
        _build_m68k_asm_runtime(m68k_runtime),
        header="Generated runtime M68K assembler knowledge artifact. Do not edit directly.",
    )
    outputs.append(RUNTIME_PY_DIR / "runtime_m68k_analysis.py")
    _write_m68k_analysis_runtime_python(
        outputs[-1],
        _build_m68k_analysis_runtime(m68k_runtime),
        header="Generated runtime M68K analysis knowledge artifact. Do not edit directly.",
    )
    outputs.append(RUNTIME_PY_DIR / "runtime_m68k_compute.py")
    _write_runtime_constants_python(
        outputs[-1],
        _build_m68k_compute_runtime(m68k_runtime),
        header="Generated runtime M68K compute knowledge artifact. Do not edit directly.",
    )
    outputs.append(RUNTIME_PY_DIR / "runtime_m68k_executor.py")
    _write_runtime_constants_python(
        outputs[-1],
        _build_m68k_executor_runtime(m68k_runtime),
        header="Generated runtime M68K executor knowledge artifact. Do not edit directly.",
    )
    outputs.append(RUNTIME_PY_DIR / "runtime_os.py")
    _write_os_runtime_python(outputs[-1], _build_os_runtime(),
                             header="Generated runtime Amiga OS knowledge artifact. Do not edit directly.")
    outputs.append(RUNTIME_PY_DIR / "runtime_hunk.py")
    _write_hunk_runtime_python(outputs[-1], _build_hunk_runtime(),
                               header="Generated runtime hunk knowledge artifact. Do not edit directly.")
    outputs.append(RUNTIME_PY_DIR / "runtime_naming.py")
    _write_runtime_constants_python(outputs[-1], _build_naming_runtime(),
                                    header="Generated runtime naming knowledge artifact. Do not edit directly.")
    outputs.append(RUNTIME_PY_DIR / "runtime_hardware.py")
    _write_runtime_constants_python(
        outputs[-1],
        _build_hardware_runtime(),
        header="Generated runtime Amiga hardware artifact. Do not edit directly.",
    )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build runtime knowledge artifacts from canonical JSON")
    parser.parse_args()
    outputs = build_runtime_artifacts()
    for output in outputs:
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
