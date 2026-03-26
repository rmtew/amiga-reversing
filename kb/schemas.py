from __future__ import annotations

from typing import NotRequired, TypedDict

from m68k_kb.runtime_types import (
    CompatibilityNote,
    CpuHierarchy,
    ExtTypeCategoryDef,
    HunkContentFormatDef,
    HunkMeta,
    HunkTypeDef,
    MemoryFlagDef,
    MemoryTypeCodeDef,
    RelocFormatDef,
)


class M68kField(TypedDict):
    name: str
    bit_hi: int
    bit_lo: int
    width: int


class M68kEncoding(TypedDict):
    fields: list[M68kField]


class M68kOperandSpec(TypedDict):
    type: str
    raw: NotRequired[str]


class M68kPrimaryDataSize(TypedDict):
    type: str
    src_bits: NotRequired[int]
    dst_bits: NotRequired[int]
    result_bits: NotRequired[int]
    divisor_bits: NotRequired[int]
    dividend_bits: NotRequired[int]
    quotient_bits: NotRequired[int]


class M68kForm(TypedDict, total=False):
    syntax: str
    operands: list[M68kOperandSpec]
    processor_020: bool
    data_sizes: M68kPrimaryDataSize


class M68kCcParameterized(TypedDict):
    prefix: str


class M68kImmediateRange(TypedDict, total=False):
    field: str
    bits: int
    signed: bool
    min: int
    max: int
    zero_means: int


class M68kOperandModes(TypedDict):
    field: str
    values: dict[str, str]


class M68kOpmodeEntry(TypedDict, total=False):
    opmode: int
    size: str
    description: str
    operation: str
    ea_is_source: bool
    source: str
    destination: str
    rx_mode: str
    ry_mode: str


class M68kDirectionVariants(TypedDict):
    field: str
    base: str
    variants: list[str]
    values: dict[str, str]


class M68kControlRegister(TypedDict):
    hex: str
    abbrev: str


class M68kDisplacementEncoding(TypedDict):
    field: str
    word_signal: int
    long_signal: int
    word_bits: int
    long_bits: int


class M68kConstraints(TypedDict, total=False):
    cc_parameterized: M68kCcParameterized
    immediate_range: M68kImmediateRange
    an_sizes: list[str]
    operand_modes: M68kOperandModes
    opmode_table: list[M68kOpmodeEntry]
    direction_variants: M68kDirectionVariants
    control_registers: list[M68kControlRegister]
    displacement_encoding: M68kDisplacementEncoding


class M68kComputeFormula(TypedDict, total=False):
    op: str
    terms: list[str | int]
    range_a: list[int]
    range_b: list[int]
    source_bits_by_size: dict[str, int]
    truncation: str


class M68kBoundsCheck(TypedDict, total=False):
    register_operand: str
    lower_bound: int
    upper_bound: int
    comparison: str
    sign_extend_bounds_for_address_register: bool
    trap_on_out_of_bounds: bool


class M68kSpEffect(TypedDict, total=False):
    action: str
    bytes: int
    reg: str
    operand: str


class M68kBitModulus(TypedDict):
    register: int
    memory: bool


class M68kVariant(TypedDict, total=False):
    mnemonic: str
    direction: str
    fill: str
    arithmetic: bool
    processor_020: bool


class M68kEaModes(TypedDict, total=False):
    src: list[str]
    dst: list[str]
    ea: list[str]


class M68kDirectionFieldValues(TypedDict):
    field: str
    form_field_value: dict[str, int]


class M68kSizeEncodingValue(TypedDict):
    size: str
    bits: int


class M68kSizeEncoding(TypedDict):
    field: str
    values: list[M68kSizeEncodingValue]


class M68kPcFlow(TypedDict):
    type: str
    conditional: bool


class M68kPcEffects(TypedDict):
    flow: M68kPcFlow
    base_sizes: NotRequired[dict[str, int]]


class M68kInstruction(TypedDict, total=False):
    mnemonic: str
    encodings: list[M68kEncoding]
    constraints: M68kConstraints
    field_descriptions: dict[str, str]
    forms: list[M68kForm]
    sizes: list[str]
    operation_type: str | None
    operation_class: str | None
    source_sign_extend: bool
    shift_count_modulus: int
    compute_formula: M68kComputeFormula
    bounds_check: M68kBoundsCheck
    sp_effects: list[M68kSpEffect]
    sp_effects_complete: bool
    implicit_operand: str
    bit_modulus: M68kBitModulus
    rotate_extra_bits: int
    signed: bool
    variants: list[M68kVariant]
    ea_modes: M68kEaModes
    direction_field_values: M68kDirectionFieldValues
    uses_label: bool
    pc_effects: M68kPcEffects
    processor_min: str
    processors: str
    size_encoding: M68kSizeEncoding


class M68kConditionFamilyEntry(TypedDict):
    prefix: str
    canonical: str
    codes: list[str]
    match_numeric_suffix: bool
    exclude_from_family: list[str]


class M68kCcTestDefinition(TypedDict):
    encoding: int
    test: str


class M68kMeta(TypedDict):
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
    nop_opword: int
    opword_bytes: int
    pmmu_condition_codes: list[str]
    register_aliases: dict[str, str]
    size_byte_count: dict[str, int]


class M68kInstructionsPayload(TypedDict):
    _meta: M68kMeta
    instructions: list[M68kInstruction]


class OsCallingConvention(TypedDict):
    scratch_regs: list[str]
    preserved_regs: list[str]
    base_reg: str
    return_reg: str
    note: str


class OsExecBaseAddress(TypedDict):
    address: int
    library: str
    note: str


class OsAbsoluteSymbol(TypedDict):
    address: int
    name: str
    note: str


class OsIncludeOwner(TypedDict):
    kind: str
    include_path: str | None
    comment_include_path: str | None
    source_file: str


class OsMeta(TypedDict):
    calling_convention: OsCallingConvention
    exec_base_addr: OsExecBaseAddress
    absolute_symbols: list[OsAbsoluteSymbol]
    lvo_slot_size: int
    named_base_structs: dict[str, str]
    input_constant_domains: dict[str, dict[str, list[str]]]
    value_domains: dict[str, list[str]]
    field_value_domains: dict[str, str]
    field_context_value_domains: dict[str, dict[str, str]]
    library_lvo_owners: dict[str, OsIncludeOwner]


class OsStructField(TypedDict, total=False):
    name: str
    type: str
    offset: int
    size: int
    size_symbol: str
    struct: str
    c_type: str
    pointer_struct: str


class OsStructDef(TypedDict, total=False):
    source: str
    base_offset: int
    base_offset_symbol: str | None
    size: int
    fields: list[OsStructField]
    base_struct: str


class OsConstant(TypedDict):
    raw: str
    value: int | None


class OsInput(TypedDict, total=False):
    name: str
    regs: list[str]
    type: str
    i_struct: str
    semantic_kind: str
    semantic_note: str


class OsOutput(TypedDict, total=False):
    name: str
    reg: str | None
    type: str
    i_struct: str


class OsReturnsBase(TypedDict):
    name_reg: str
    base_reg: str


class OsReturnsMemory(TypedDict, total=False):
    result_reg: str
    size_reg: str | None


class OsFunction(TypedDict, total=False):
    lvo: int | None
    returns_base: OsReturnsBase
    returns_memory: OsReturnsMemory
    output: OsOutput
    no_return: bool
    inputs: list[OsInput]
    os_since: str
    fd_version: str
    private: bool


class OsLibrary(TypedDict):
    base: str
    functions: dict[str, OsFunction]
    lvo_index: dict[str, str]


class OsReferencePayload(TypedDict):
    _meta: OsMeta
    constants: dict[str, OsConstant]
    libraries: dict[str, OsLibrary]
    structs: dict[str, OsStructDef]


class HunkRelocationSemantic(TypedDict):
    bytes: int
    citation: str
    description: str
    mode: str


class HunkFormatPayload(TypedDict):
    _meta: HunkMeta
    hunk_types: dict[str, HunkTypeDef]
    ext_types: dict[str, HunkTypeDef]
    memory_flags: dict[str, MemoryFlagDef]
    memory_type_codes: dict[str, MemoryTypeCodeDef]
    ext_type_categories: ExtTypeCategoryDef
    compatibility_notes: list[CompatibilityNote]
    reloc_formats: dict[str, RelocFormatDef]
    relocation_semantics: dict[str, HunkRelocationSemantic]
    hunk_content_formats: dict[str, HunkContentFormatDef]


class HardwareRegister(TypedDict):
    base_symbol: str
    cpu_address: str
    family: str
    include: str
    offset: str
    symbols: list[str]


class HardwareSymbolsPayload(TypedDict):
    _meta: dict[str, object]
    registers: list[HardwareRegister]


class NamingPattern(TypedDict):
    name: str
    functions: list[str]


class NamingRulesMeta(TypedDict):
    description: str
    source: str


class NamingRulesPayload(TypedDict):
    _meta: NamingRulesMeta
    generic_prefix: str
    patterns: list[NamingPattern]
    trivial_functions: list[str]
