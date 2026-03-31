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
    seed_origin: str
    review_status: str
    citation: str


class OsExecBaseAddress(TypedDict):
    address: int
    library: str
    note: str
    seed_origin: str
    review_status: str
    citation: str


class OsAbsoluteSymbol(TypedDict):
    address: int
    name: str
    note: str
    seed_origin: str
    review_status: str
    citation: str


class OsIncludeOwner(TypedDict):
    kind: str
    canonical_include_path: str | None
    assembler_include_path: str | None
    source_file: str


class OsValueDomain(TypedDict, total=False):
    kind: str
    members: list[str]
    zero_name: str | None
    exact_match_policy: str
    composition: str | None
    remainder_policy: str | None


class OsApiInputValueBinding(TypedDict, total=False):
    library: str
    function: str
    input: str
    domain: str
    available_since: str
    seed_origin: str
    review_status: str
    citation: str


class OsApiInputSemanticAssertion(TypedDict):
    library: str
    function: str
    input: str
    semantic_kind: str
    semantic_note: str
    seed_origin: str
    review_status: str
    citation: str


class OsApiInputTypeOverride(TypedDict, total=False):
    library: str
    function: str
    input: str
    type: str
    i_struct: str
    seed_origin: str
    review_status: str
    citation: str


class OsStructFieldValueBinding(TypedDict, total=False):
    struct: str
    field: str
    domain: str
    context_name: str
    available_since: str
    seed_origin: str
    review_status: str
    citation: str


class OsTypedDataStreamCommandByte(TypedDict):
    destination_shift: int
    destination_mask: int
    size_shift: int
    size_mask: int
    count_mask: int
    invalid_size_value: int
    destination_modes: dict[str, int]
    source_sizes: dict[str, int]


class OsTypedDataStreamConstructor(TypedDict):
    name: str
    unit_size: int
    count: int
    destination_mode: str
    opcode: int


class OsTypedDataStreamGenericConstructor(TypedDict):
    name: str
    size_param_encoding: dict[str, int]
    count_bias: int


class OsTypedDataStreamFormat(TypedDict):
    include_path: str
    available_since: str
    alignment: int
    terminator_opcode: int
    command_byte: OsTypedDataStreamCommandByte
    constructors: list[OsTypedDataStreamConstructor]
    generic_constructor: OsTypedDataStreamGenericConstructor


class OsResidentEntryRegisterSeed(TypedDict, total=False):
    register: str
    kind: str
    struct_name: str
    named_base_source: str
    named_base_name: str
    context_name: str


class OsMeta(TypedDict):
    source: str
    ndk_path: str
    include_dir: str
    calling_convention: OsCallingConvention
    exec_base_addr: OsExecBaseAddress
    absolute_symbols: list[OsAbsoluteSymbol]
    lvo_slot_size: int
    compatibility_versions: list[str]
    include_min_versions: dict[str, str]
    resident_autoinit_words: list[str]
    resident_autoinit_word_stream_formats: dict[str, str]
    resident_autoinit_supports_short_vectors: bool
    resident_vector_prefixes: dict[str, list[str]]
    resident_entry_register_seeds: dict[str, dict[str, list[OsResidentEntryRegisterSeed]]]
    named_base_structs: dict[str, str]
    value_domains: dict[str, OsValueDomain]
    api_input_value_bindings: list[OsApiInputValueBinding]
    api_input_type_overrides: list[OsApiInputTypeOverride]
    api_input_semantic_assertions: list[OsApiInputSemanticAssertion]
    struct_field_value_bindings: list[OsStructFieldValueBinding]
    typed_data_stream_formats: dict[str, OsTypedDataStreamFormat]
    parsed_include_paths: list[str]


class OsStructField(TypedDict, total=False):
    name: str
    type: str
    offset: int
    size: int
    available_since: str
    names_by_version: dict[str, str]
    size_symbol: str
    struct: str
    c_type: str
    pointer_struct: str


class OsStructDef(TypedDict, total=False):
    source: str
    base_offset: int
    base_offset_symbol: str | None
    size: int
    available_since: str
    fields: list[OsStructField]
    base_struct: str


class OsConstant(TypedDict):
    raw: str
    value: int | None
    available_since: str
    owner: OsIncludeOwner


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
    available_since: str
    fd_version: str
    private: bool


class OsLibrary(TypedDict):
    base: str
    owner: OsIncludeOwner
    functions: dict[str, OsFunction]
    lvo_index: NotRequired[dict[str, str]]


class OsCorrectionsMeta(TypedDict, total=False):
    calling_convention: OsCallingConvention
    exec_base_addr: OsExecBaseAddress
    absolute_symbols: list[OsAbsoluteSymbol]
    value_domains: dict[str, OsValueDomain]
    api_input_value_bindings: list[OsApiInputValueBinding]
    api_input_type_overrides: list[OsApiInputTypeOverride]
    api_input_semantic_assertions: list[OsApiInputSemanticAssertion]
    struct_field_value_bindings: list[OsStructFieldValueBinding]


class OsOtherParsedMeta(TypedDict, total=False):
    source: str
    ndk_path: str
    version_map: dict[str, str]
    version_fields_note: str
    available_since_default_note: str
    struct_name_map: dict[str, str]


class OsIncludesParsedPayload(TypedDict):
    _meta: OsMeta
    constants: dict[str, OsConstant]
    libraries: dict[str, OsLibrary]
    structs: dict[str, OsStructDef]


class OsOtherParsedPayload(TypedDict):
    _meta: OsOtherParsedMeta
    functions: dict[str, dict[str, OsFunction]]


class OsCorrectionsPayload(TypedDict):
    _meta: OsCorrectionsMeta


class OsMergedReferencePayload(TypedDict):
    _meta: OsMeta
    constants: dict[str, OsConstant]
    libraries: dict[str, OsLibrary]
    structs: dict[str, OsStructDef]


class OsReferencePayload(OsMergedReferencePayload):
    pass


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
    hunkexe_supported_relocation_types: list[str]


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
