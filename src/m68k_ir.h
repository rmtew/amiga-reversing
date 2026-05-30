#ifndef M68K_IR_H
#define M68K_IR_H

#include "m68k_asm_metadata.h"
#include "m68k_object.h"
#include "util_arena.h"

#include <stddef.h>
#include <stdint.h>

typedef enum M68kIrSyntaxMode {
  M68K_IR_SYNTAX_CANONICAL = 0,
  M68K_IR_SYNTAX_GENAM = 1,
  M68K_IR_SYNTAX_VASM = 2
} M68kIrSyntaxMode;

typedef struct M68kAssemblerSyntaxPolicy {
  uint8_t syntax_mode;
} M68kAssemblerSyntaxPolicy;

typedef struct M68kPresentationPolicy {
  uint8_t prefer_generated_names;
  uint8_t prefer_strings;
  uint8_t prefer_long_data;
  char code_label_prefix[8];
  char call_label_prefix[8];
  char data_label_prefix[8];
} M68kPresentationPolicy;

typedef enum M68kOsCompatibilityKind {
  M68K_OS_COMPATIBILITY_NONE = 0,
  M68K_OS_COMPATIBILITY_AMIGA = 1,
  M68K_OS_COMPATIBILITY_ATARI_ST = 2
} M68kOsCompatibilityKind;

typedef struct M68kOsRenderPolicy {
  uint8_t compatibility_kind;
  uint16_t compatibility_level;
} M68kOsRenderPolicy;

typedef struct M68kRenderPolicy {
  M68kAssemblerSyntaxPolicy syntax;
  M68kPresentationPolicy presentation;
  M68kOsRenderPolicy os;
} M68kRenderPolicy;

#define M68K_ANALYSIS_REGISTER_SEED_LIMIT 64U
#define M68K_ANALYSIS_ENTRY_POINT_LIMIT 256U
#define M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT 256U
#define M68K_ANALYSIS_NAMED_LABEL_LIMIT 128U
#define M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT 128U
#define M68K_ANALYSIS_RSSET_USE_SITE_BINDING_LIMIT 128U
#define M68K_ANALYSIS_ENTRY_COMMENT_LIMIT 128U
#define M68K_ANALYSIS_MANUAL_REPRESENTATION_LIMIT 128U
#define M68K_ANALYSIS_TARGET_EQUATE_LIMIT 128U
#define M68K_ANALYSIS_MANUAL_RUNTIME_ADDRESS_REF_LIMIT 128U
#define M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT 64U
#define M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT 32U
#define M68K_ANALYSIS_CUSTOM_STRUCT_ID_BASE 0x8000U

typedef enum M68kAnalysisRegisterKind {
  M68K_ANALYSIS_REGISTER_NONE = 0,
  M68K_ANALYSIS_REGISTER_DATA = 1,
  M68K_ANALYSIS_REGISTER_ADDRESS = 2
} M68kAnalysisRegisterKind;

typedef enum M68kAnalysisRegisterSeedKind {
  M68K_ANALYSIS_REGISTER_SEED_NONE = 0,
  M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE = 1,
  M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR = 2
} M68kAnalysisRegisterSeedKind;

typedef struct M68kAnalysisRegisterSeed {
  uint8_t platform_kind;
  uint8_t kind;
  uint8_t reg_kind;
  uint8_t reg_index;
  uint8_t has_entry_offset;
  uint8_t has_section_index;
  uint8_t reserved[2];
  uint32_t entry_offset;
  uint32_t section_index;
  char name[64];
  char type_name[64];
  char context_name[64];
} M68kAnalysisRegisterSeed;

typedef struct M68kAnalysisEntryPoint {
  uint8_t has_section_index;
  uint8_t reserved[3];
  uint32_t section_index;
  uint32_t offset;
} M68kAnalysisEntryPoint;

typedef enum M68kAnalysisStructuredDataKind {
  M68K_ANALYSIS_STRUCTURED_DATA_BYTES = 1,
  M68K_ANALYSIS_STRUCTURED_DATA_WORDS = 2,
  M68K_ANALYSIS_STRUCTURED_DATA_LONGS = 3,
  M68K_ANALYSIS_STRUCTURED_DATA_STRING = 4
} M68kAnalysisStructuredDataKind;

typedef enum M68kAnalysisStructuredDataRoleFlag {
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST = 1U << 0,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE = 1U << 1,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE = 1U << 2,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE = 1U << 3,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING = 1U << 4,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP = 1U << 5,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE = 1U << 6,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING = 1U << 7,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_AUDIO_TABLE = 1U << 8,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_DESTINATION = 1U << 9,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_SOURCE = 1U << 10,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_DISK_BUFFER = 1U << 11,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SPRITE = 1U << 12,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING_CONTROL_STREAM = 1U << 13,
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_MACOS_SYMBOL_STRING = 1U << 14
} M68kAnalysisStructuredDataRoleFlag;

typedef enum M68kAnalysisStructuredDataSourcePattern {
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_UNKNOWN = 0,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_RELOCATION_POINTER_TABLE = 1,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_WORD_DISPATCH = 2,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_POINTER_READ = 3,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_SCALAR_READ = 4,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POSTINCREMENT_READ_SEQUENCE = 5,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_READ = 6,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH = 7,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MACOS_SYMBOL_RECORD = 8,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MULTILINE_TEXT = 9,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_TERMINATED_TEXT = 10,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_BOUNDED_TEXT = 11,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_STRING_TABLE_SEQUENCE = 12,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_CONTROL_STRING_STREAM = 13,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_API_STRING_POINTER = 14,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POINTER_STRING_TABLE = 15,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_WORD_OFFSET_STRING_TABLE = 16,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_API_TEXT_BUFFER = 17,
  M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_INDIRECT_DISPATCH = 18
} M68kAnalysisStructuredDataSourcePattern;

typedef enum M68kAnalysisTableKind {
  M68K_ANALYSIS_TABLE_KIND_UNKNOWN = 0,
  M68K_ANALYSIS_TABLE_KIND_SCALAR = 1,
  M68K_ANALYSIS_TABLE_KIND_POINTER = 2,
  M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH = 3,
  M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH = 4,
  M68K_ANALYSIS_TABLE_KIND_RELATIVE_DATA_LOOKUP = 5
} M68kAnalysisTableKind;

typedef enum M68kAnalysisTableBaseExpression {
  M68K_ANALYSIS_TABLE_BASE_EXPRESSION_UNKNOWN = 0,
  M68K_ANALYSIS_TABLE_BASE_EXPRESSION_TABLE_LABEL = 1,
  M68K_ANALYSIS_TABLE_BASE_EXPRESSION_TARGET_LABEL = 2
} M68kAnalysisTableBaseExpression;

typedef enum M68kAnalysisTableEntryCountProof {
  M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_UNKNOWN = 0,
  M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_STRUCTURED_RANGE = 1,
  M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_CONSUMER_STRUCTURAL_SCAN = 2,
  M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_RELOCATION_RECORD = 3,
  M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_PLATFORM_RECORD = 4,
  M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_MASK_DOMAIN = 5,
  M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_COMPARE_DOMAIN = 6,
  M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_LOOP_LIMIT = 7
} M68kAnalysisTableEntryCountProof;

typedef enum M68kAnalysisTableStopReason {
  M68K_ANALYSIS_TABLE_STOP_REASON_UNKNOWN = 0,
  M68K_ANALYSIS_TABLE_STOP_REASON_STRUCTURED_RANGE_END = 1,
  M68K_ANALYSIS_TABLE_STOP_REASON_CONSUMER_STRUCTURAL_STOP = 2,
  M68K_ANALYSIS_TABLE_STOP_REASON_RELOCATION_RECORD_END = 3,
  M68K_ANALYSIS_TABLE_STOP_REASON_PLATFORM_RECORD_END = 4,
  M68K_ANALYSIS_TABLE_STOP_REASON_INDEX_MASK_BOUND = 5,
  M68K_ANALYSIS_TABLE_STOP_REASON_INDEX_COMPARE_BRANCH_BOUND = 6,
  M68K_ANALYSIS_TABLE_STOP_REASON_LOOP_LIMIT_BOUND = 7
} M68kAnalysisTableStopReason;

typedef enum M68kAnalysisStructuredDataTextField {
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_LABEL = 0,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_STRUCT_NAME = 1,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_FIELD_NAME = 2,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_FIELD_TYPE = 3,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_C_TYPE = 4,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_POINTER_STRUCT = 5,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_VALUE_DOMAIN = 6,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_CONSTANT_NAME = 7,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SEMANTIC_ROLE = 8,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SOURCE_PATTERN = 9,
  M68K_ANALYSIS_STRUCTURED_DATA_TEXT_COMMENT = 10
} M68kAnalysisStructuredDataTextField;

typedef struct M68kAnalysisStructuredDataItem {
  uint8_t has_section_index;
  uint8_t kind;
  uint8_t is_pointer;
  uint8_t has_target;
  uint32_t section_index;
  uint32_t offset;
  uint32_t size;
  uint32_t target_section;
  uint32_t target_offset;
  uint8_t has_constant_value;
  uint8_t reserved[3];
  int32_t constant_value;
  uint8_t has_consumer;
  uint8_t source_pattern_id;
  uint8_t table_kind_id;
  uint8_t table_base_expression_id;
  uint8_t table_conflicted;
  uint8_t table_conflict_state;
  uint16_t platform_kind_id;
  uint16_t platform_field_id;
  uint16_t struct_id;
  uint16_t field_id;
  uint16_t pointer_struct_id;
  uint32_t consumer_section;
  uint32_t consumer_offset;
  uint8_t has_index_register;
  uint8_t index_register_kind;
  uint8_t index_register;
  uint8_t has_target_register;
  uint8_t target_register_kind;
  uint8_t target_register;
  uint8_t entry_count_proof_id;
  uint8_t table_stop_reason_id;
  uint8_t has_index_mask_domain;
  uint8_t has_index_compare_domain;
  uint8_t index_domain_branch_mnemonic_id;
  uint8_t index_domain_reserved[1];
  uint32_t index_mask_min;
  uint32_t index_mask_max;
  uint32_t index_compare_min;
  uint32_t index_compare_max;
  uint8_t has_index_loop_domain;
  uint8_t index_loop_mnemonic_id;
  uint8_t index_loop_reserved[2];
  uint32_t index_loop_min;
  uint32_t index_loop_max;
  uint32_t semantic_role_flags;
  uint16_t label_len;
  uint16_t struct_name_len;
  uint16_t field_name_len;
  uint16_t field_type_len;
  uint16_t c_type_len;
  uint16_t pointer_struct_len;
  uint16_t value_domain_len;
  uint16_t constant_name_len;
  uint16_t semantic_role_len;
  uint16_t source_pattern_len;
  uint16_t comment_len;
  uint16_t reserved_text_len;
  char label[65];
  char struct_name[65];
  char field_name[65];
  char field_type[65];
  char c_type[65];
  char pointer_struct[65];
  char value_domain[65];
  char constant_name[65];
  char semantic_role[65];
  char source_pattern[65];
  char comment[97];
} M68kAnalysisStructuredDataItem;

typedef enum M68kAnalysisStructuredDataPlatformKind {
  M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_NONE = 0U,
  M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_AMIGA_RESIDENT_AUTOINIT = 1U
} M68kAnalysisStructuredDataPlatformKind;

typedef enum M68kAnalysisStructuredDataPlatformField {
  M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_NONE = 0U,
  M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_BASE_SIZE = 1U,
  M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_VECTORS = 2U,
  M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_INIT_STRUCT = 3U,
  M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_INIT_FUNCTION = 4U
} M68kAnalysisStructuredDataPlatformField;

typedef enum M68kAnalysisLabelDomain {
  M68K_ANALYSIS_LABEL_DOMAIN_SOURCE = 0U,
  M68K_ANALYSIS_LABEL_DOMAIN_RUNTIME = 1U
} M68kAnalysisLabelDomain;

typedef struct M68kAnalysisNamedLabel {
  uint8_t has_section_index;
  uint8_t domain;
  uint8_t reserved[2];
  uint32_t section_index;
  uint32_t offset;
  char name[64];
} M68kAnalysisNamedLabel;

typedef struct M68kAnalysisEntryComment {
  uint8_t has_section_index;
  uint8_t reserved[3];
  uint32_t section_index;
  uint32_t offset;
  char comment[192];
} M68kAnalysisEntryComment;

typedef struct M68kAnalysisRssetLayoutRegion {
  uint32_t offset;
  uint8_t size;
  uint8_t flags;
  uint8_t storage_kind_id;
  uint8_t reserved[1];
  char layout_name[32];
  char base_symbol[64];
  char sizeof_symbol[64];
  char symbol[64];
  char struct_name[64];
  char pointer_struct[64];
  char storage_kind[32];
  char semantic_type[64];
} M68kAnalysisRssetLayoutRegion;

typedef enum M68kAnalysisRssetLayoutRegionFlag {
  M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_LAYOUT = 1U,
  M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_BASE = 2U
} M68kAnalysisRssetLayoutRegionFlag;

typedef enum M68kAnalysisRssetLayoutStorageKind {
  M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_UNKNOWN = 0U,
  M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_INSTANCE = 1U,
  M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER = 2U,
  M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER = 3U,
  M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_SCALAR = 4U,
  M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_BYTE_ARRAY = 5U
} M68kAnalysisRssetLayoutStorageKind;

typedef struct M68kAnalysisRssetUseSiteBinding {
  uint32_t section_index;
  uint32_t offset;
  uint32_t displacement;
  uint8_t operand_index;
  uint8_t base_reg;
  uint8_t reserved[2];
  char layout_name[32];
  char base_symbol[64];
  char base_evidence_id[96];
  char binding_id[256];
  char owner_action_id[96];
} M68kAnalysisRssetUseSiteBinding;

#define M68K_ANALYSIS_RUNTIME_RANGE_LIMIT 64U
#define M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT 64U

typedef struct M68kAnalysisRuntimeRange {
  uint8_t has_section_index;
  uint8_t reserved[3];
  uint32_t section_index;
  uint32_t offset;
  uint32_t size;
  uint32_t runtime_address;
  char name[64];
} M68kAnalysisRuntimeRange;

typedef struct M68kAnalysisRuntimeEntryPoint {
  uint8_t has_section_index;
  uint8_t reserved[3];
  uint32_t section_index;
  uint32_t runtime_address;
} M68kAnalysisRuntimeEntryPoint;

typedef enum M68kAnalysisRepresentationStyle {
  M68K_ANALYSIS_REPRESENTATION_STYLE_NONE = 0,
  M68K_ANALYSIS_REPRESENTATION_STYLE_HEX = 1,
  M68K_ANALYSIS_REPRESENTATION_STYLE_BINARY = 2,
  M68K_ANALYSIS_REPRESENTATION_STYLE_CHARACTER = 3,
  M68K_ANALYSIS_REPRESENTATION_STYLE_STRING = 4,
  M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL = 5,
  M68K_ANALYSIS_REPRESENTATION_STYLE_DECIMAL = 6
} M68kAnalysisRepresentationStyle;

typedef struct M68kAnalysisManualRepresentation {
  uint8_t has_section_index;
  uint8_t style_id;
  uint8_t has_operand_index;
  uint8_t operand_index;
  uint16_t symbol_id;
  uint16_t target_equate_index;
  uint32_t section_index;
  uint32_t offset;
  uint32_t size;
} M68kAnalysisManualRepresentation;

typedef struct M68kAnalysisTargetEquate {
  char name[64];
  int32_t value;
  uint8_t value_style_id;
  uint8_t reserved[3];
  char value_expr[64];
} M68kAnalysisTargetEquate;

typedef struct M68kAnalysisCustomStructField {
  char name[64];
  char type_name[64];
  uint32_t offset;
  uint32_t size;
  char struct_name[64];
  char pointer_struct[64];
  char named_base[64];
} M68kAnalysisCustomStructField;

typedef struct M68kAnalysisCustomStruct {
  char name[64];
  uint32_t size;
  uint16_t field_count;
  uint16_t reserved;
  M68kAnalysisCustomStructField fields[M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT];
} M68kAnalysisCustomStruct;

typedef struct M68kAnalysisManualRuntimeAddressRef {
  uint8_t has_section_index;
  uint8_t has_target;
  uint8_t has_runtime_address;
  uint8_t confidence;
  uint32_t section_index;
  uint32_t offset;
  uint32_t size;
  uint32_t target_section_index;
  uint32_t target_offset;
  uint32_t runtime_address;
  uint32_t owner_element_offset;
  char owner_kind[32];
  char owner_id[96];
  char owner_layout_id[64];
  char xref_generation_mode[32];
} M68kAnalysisManualRuntimeAddressRef;

typedef struct M68kAnalysisPolicy {
  uint8_t max_cpu;
  uint8_t has_entry_offset;
  uint8_t disable_implicit_entry_points;
  uint8_t reserved0[1];
  uint16_t register_seed_count;
  uint16_t entry_point_count;
  uint16_t structured_data_item_count;
  uint16_t named_label_count;
  uint16_t entry_comment_count;
  uint16_t runtime_range_count;
  uint16_t runtime_entry_point_count;
  uint16_t rsset_layout_region_count;
  uint16_t rsset_use_site_binding_count;
  uint16_t manual_representation_count;
  uint16_t target_equate_count;
  uint16_t manual_runtime_address_ref_count;
  uint16_t custom_struct_count;
  uint16_t custom_struct_capacity;
  uint8_t custom_struct_owner;
  uint8_t reserved1[1];
  uint32_t entry_offset;
  M68kAnalysisRegisterSeed register_seeds[M68K_ANALYSIS_REGISTER_SEED_LIMIT];
  M68kAnalysisEntryPoint entry_points[M68K_ANALYSIS_ENTRY_POINT_LIMIT];
  M68kAnalysisStructuredDataItem structured_data_items[M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT];
  M68kAnalysisNamedLabel named_labels[M68K_ANALYSIS_NAMED_LABEL_LIMIT];
  M68kAnalysisEntryComment entry_comments[M68K_ANALYSIS_ENTRY_COMMENT_LIMIT];
  M68kAnalysisRuntimeRange runtime_ranges[M68K_ANALYSIS_RUNTIME_RANGE_LIMIT];
  M68kAnalysisRuntimeEntryPoint runtime_entry_points[M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT];
  M68kAnalysisRssetLayoutRegion rsset_layout_regions[M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT];
  M68kAnalysisRssetUseSiteBinding rsset_use_site_bindings[M68K_ANALYSIS_RSSET_USE_SITE_BINDING_LIMIT];
  M68kAnalysisManualRepresentation manual_representations[M68K_ANALYSIS_MANUAL_REPRESENTATION_LIMIT];
  M68kAnalysisTargetEquate target_equates[M68K_ANALYSIS_TARGET_EQUATE_LIMIT];
  M68kAnalysisManualRuntimeAddressRef manual_runtime_address_refs[M68K_ANALYSIS_MANUAL_RUNTIME_ADDRESS_REF_LIMIT];
  M68kAnalysisCustomStruct *custom_structs;
} M68kAnalysisPolicy;

typedef struct M68kAnalysisFindings {
  uint8_t required_cpu;
  uint32_t cpu_violation_count;
} M68kAnalysisFindings;

typedef enum M68kIrSymbolRefKind {
  M68K_IR_SYMBOL_REF_NONE = 0,
  M68K_IR_SYMBOL_REF_ABS = 1,
  M68K_IR_SYMBOL_REF_PC_REL = 2,
  M68K_IR_SYMBOL_REF_SECTION_REL = 3
} M68kIrSymbolRefKind;

typedef enum M68kIrSymbolProvenance {
  M68K_IR_SYMBOL_PROVENANCE_NONE = 0,
  M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA = 1,
  M68K_IR_SYMBOL_PROVENANCE_PLATFORM_ATARI_ST = 2
} M68kIrSymbolProvenance;

#define M68K_IR_SYMBOL_NAME_SIZE 256U

typedef enum M68kPlatformNameDomainKind {
  M68K_PLATFORM_NAME_NONE = 0,
  M68K_PLATFORM_NAME_LIBRARY = 1,
  M68K_PLATFORM_NAME_BASE = 2,
  M68K_PLATFORM_NAME_FUNCTION = 3,
  M68K_PLATFORM_NAME_SYMBOL = 4,
  M68K_PLATFORM_NAME_INCLUDE = 5,
  M68K_PLATFORM_NAME_TYPE = 6,
  M68K_PLATFORM_NAME_STRUCT = 7,
  M68K_PLATFORM_NAME_FIELD = 8,
  M68K_PLATFORM_NAME_SEMANTIC_KIND = 9,
  M68K_PLATFORM_NAME_VALUE_DOMAIN = 10,
  M68K_PLATFORM_NAME_FAMILY = 11,
  M68K_PLATFORM_NAME_HEADER = 12
} M68kPlatformNameDomainKind;

typedef struct M68kPlatformNameRef {
  uint8_t platform_kind;
  uint8_t domain_kind;
  uint16_t id;
} M68kPlatformNameRef;

typedef struct M68kSymbolRefIR {
  uint8_t kind;
  uint8_t has_name;
  uint8_t name_is_generated;
  uint8_t has_symbolic_addend;
  uint8_t name_provenance;
  uint8_t symbolic_addend_provenance;
  uint8_t render_pc_relative_displacement_expr;
  uint32_t pc_relative_displacement_base_offset;
  size_t symbol_index;
  size_t section_index;
  int has_symbol;
  int has_section;
  int32_t addend;
  int32_t symbolic_addend_value;
  char name[M68K_IR_SYMBOL_NAME_SIZE];
  char symbolic_addend_name[64];
} M68kSymbolRefIR;

typedef struct M68kOperandIR {
  uint8_t kind;
  uint8_t has_exact_render_value;
  uint8_t manual_representation_style_id;
  uint8_t reserved0;
  M68kAsmOperandValue value;
  uint32_t exact_render_value;
  M68kSymbolRefIR symbol_ref;
} M68kOperandIR;

typedef struct M68kInstructionIR {
  uint16_t asm_form_index;
  M68kFormId canonical_form_id;
  uint8_t mnemonic_id;
  uint8_t target_cpu;
  uint8_t has_coprocessor_id;
  uint8_t coprocessor_id;
  char size_suffix;
  size_t operand_count;
  M68kOperandIR operands[4];
  size_t byte_count;
} M68kInstructionIR;

extern const M68kInstructionIR g_m68k_ir_instruction_none;

typedef enum M68kDataItemKind {
  M68K_DATA_ITEM_BYTES = 1,
  M68K_DATA_ITEM_WORDS = 2,
  M68K_DATA_ITEM_LONGS = 3,
  M68K_DATA_ITEM_STRING = 4
} M68kDataItemKind;

typedef struct M68kDataItemIR {
  uint8_t kind;
  uint8_t *data;
  size_t size;
  char *expr_text;
} M68kDataItemIR;

typedef enum M68kStatementKind {
  M68K_STATEMENT_LABEL = 1,
  M68K_STATEMENT_INSTRUCTION = 2,
  M68K_STATEMENT_DATA = 3,
  M68K_STATEMENT_ALIGN = 4,
  M68K_STATEMENT_RESERVE = 5
} M68kStatementKind;

typedef enum M68kStatementCommentKind {
  M68K_STATEMENT_COMMENT_NONE = 0,
  M68K_STATEMENT_COMMENT_VIOLATION = 1,
  M68K_STATEMENT_COMMENT_METADATA = 2,
  M68K_STATEMENT_COMMENT_FIELD = 3,
  M68K_STATEMENT_COMMENT_STRUCT_LABEL = 4
} M68kStatementCommentKind;

#define M68K_STATEMENT_SOURCE_BYTES_MAX 16U

typedef struct M68kStatementIR {
  uint8_t kind;
  uint8_t comment_kind;
  uint32_t offset;
  char *label_name;
  char *comment;
  uint8_t label_is_generated;
  uint8_t source_byte_count;
  uint8_t source_bytes[M68K_STATEMENT_SOURCE_BYTES_MAX];
  union {
    M68kInstructionIR instruction;
    M68kDataItemIR data;
    uint32_t alignment;
    uint32_t reserve_size;
  } u;
} M68kStatementIR;

typedef struct M68kSectionIR {
  char *name;
  M68kSectionKind kind;
  uint8_t platform_mem_type;
  uint32_t platform_mem_attrs;
  uint32_t size;
  uint32_t data_size;
  M68kStatementIR *statements;
  size_t statement_count;
  size_t statement_capacity;
  Arena *arena;
} M68kSectionIR;

typedef struct M68kSourceFileIR {
  M68kPlatformFileKind file_kind;
  uint8_t platform_backend_kind;
  uint8_t has_atari_st_program_flags;
  uint32_t atari_st_program_flags;
  M68kSectionIR *sections;
  size_t section_count;
  size_t section_capacity;
  Arena *arena;
} M68kSourceFileIR;

typedef enum M68kCodeCertainty {
  M68K_CODE_CERTAIN = 1,
  M68K_CODE_PROBABLE = 2,
  M68K_CODE_UNKNOWN = 3
} M68kCodeCertainty;

typedef enum M68kCfgEdgeKind {
  M68K_CFG_EDGE_FALLTHROUGH = 1,
  M68K_CFG_EDGE_BRANCH = 2,
  M68K_CFG_EDGE_CALL = 3,
  M68K_CFG_EDGE_JUMP = 4,
  M68K_CFG_EDGE_RETURN = 5
} M68kCfgEdgeKind;

typedef struct M68kCfgBlockIR {
  uint32_t start_offset;
  uint32_t end_offset;
  uint8_t certainty;
  size_t edge_start;
  size_t edge_count;
} M68kCfgBlockIR;

typedef struct M68kCfgEdgeIR {
  size_t source_block_index;
  size_t target_block_index;
  uint32_t source_offset;
  uint32_t target_offset;
  uint8_t kind;
} M68kCfgEdgeIR;

typedef enum M68kViolationKind {
  M68K_VIOLATION_CPU_POLICY = 1,
  M68K_VIOLATION_DECODE_FAILED_REACHABLE = 2,
  M68K_VIOLATION_INVALID_INTERIOR_REFERENCE = 3,
  M68K_VIOLATION_UNRESOLVED_INDIRECT = 4,
  M68K_VIOLATION_ORPHANED_CODE = 5
} M68kViolationKind;

typedef enum GeneratedLabelKind {
  GENERATED_LABEL_LOC = 0,
  GENERATED_LABEL_SUB = 1,
  GENERATED_LABEL_DAT = 2
} GeneratedLabelKind;

typedef struct M68kViolationIR {
  uint32_t offset;
  uint8_t kind;
  char *message;
} M68kViolationIR;

typedef struct M68kRecoveredWordDispatchIR {
  uint8_t pattern;
  uint8_t relative_to_slot;
  uint8_t preserve_zero_slots;
  uint32_t table_base;
  uint32_t base_target;
  uint32_t scanned_bytes;
  size_t slot_count;
  int16_t *entry_words;
  uint32_t *targets;
  uint8_t *target_valid;
} M68kRecoveredWordDispatchIR;

typedef struct M68kRecoveredInlineDispatchIR {
  uint32_t table_base;
  uint32_t scanned_bytes;
  size_t entry_count;
  uint32_t *entry_offsets;
  uint32_t *targets;
} M68kRecoveredInlineDispatchIR;

typedef struct M68kRecoveredStringDispatchIR {
  uint32_t table_base;
  uint32_t table_end;
  uint32_t dispatch_site;
  uint32_t decoder_entry;
  size_t entry_count;
  uint32_t *entry_offsets;
  uint32_t *offset_offsets;
  uint32_t *targets;
} M68kRecoveredStringDispatchIR;

typedef struct M68kRecoveredStringRefIR {
  uint32_t offset;
  uint32_t target;
  char *text;
} M68kRecoveredStringRefIR;

typedef enum M68kRecoveredIndirectFlowKind {
  M68K_RECOVERED_INDIRECT_FLOW_CALL = 1,
  M68K_RECOVERED_INDIRECT_FLOW_JUMP = 2
} M68kRecoveredIndirectFlowKind;

typedef enum M68kRecoveredIndirectShape {
  M68K_RECOVERED_INDIRECT_SHAPE_IND = 1,
  M68K_RECOVERED_INDIRECT_SHAPE_DISP = 2,
  M68K_RECOVERED_INDIRECT_SHAPE_INDEX_BRIEF = 3,
  M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_BRIEF = 4,
  M68K_RECOVERED_INDIRECT_SHAPE_INDEX_FULL = 5,
  M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_FULL = 6,
  M68K_RECOVERED_INDIRECT_SHAPE_INDEX_MEMIND = 7,
  M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_MEMIND = 8
} M68kRecoveredIndirectShape;

typedef enum M68kRecoveredIndirectSourcePattern {
  M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_UNKNOWN = 0,
  M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_INDIRECT = 1,
  M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_INDEXED_INDIRECT = 2,
  M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_PC_INDEXED_INDIRECT = 3
} M68kRecoveredIndirectSourcePattern;

typedef enum M68kRecoveredIndirectStatus {
  M68K_RECOVERED_INDIRECT_STATUS_UNRESOLVED = 1,
  M68K_RECOVERED_INDIRECT_STATUS_RESOLVED_RUNTIME = 2,
  M68K_RECOVERED_INDIRECT_STATUS_RUNTIME = 3,
  M68K_RECOVERED_INDIRECT_STATUS_PER_CALLER = 4,
  M68K_RECOVERED_INDIRECT_STATUS_BACKWARD_SLICE = 5,
  M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE = 6,
  M68K_RECOVERED_INDIRECT_STATUS_EXTERNAL = 7
} M68kRecoveredIndirectStatus;

typedef enum M68kRecoveredIndirectTableBoundsStatus {
  M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_NONE = 0,
  M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_INSUFFICIENT_ENTRIES = 1,
  M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_CODE_OVERLAP = 2,
  M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_UNDECODED_ENTRY = 3,
  M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_UNSUPPORTED_ENTRY_SHAPE = 4
} M68kRecoveredIndirectTableBoundsStatus;

typedef struct M68kRecoveredIndirectSiteIR {
  uint32_t offset;
  uint8_t flow_kind;
  uint8_t shape;
  uint8_t status;
  uint8_t has_target;
  uint8_t has_target_count;
  uint8_t operand_index;
  uint8_t source_size;
  uint8_t has_expression_base;
  uint8_t has_table_base;
  uint8_t has_table_bounds;
  uint8_t table_bounds_status;
  uint8_t is_table_candidate;
  uint8_t source_pattern_id;
  uint8_t conflict_state;
  uint8_t reserved0;
  uint32_t target;
  uint32_t target_count;
  uint32_t expression_base_offset;
  uint32_t table_offset;
  uint32_t table_size;
  uint32_t table_entry_size;
  uint32_t table_entry_count;
  char *detail;
} M68kRecoveredIndirectSiteIR;

typedef enum M68kOrphanCodeSignalReason {
  M68K_ORPHAN_CODE_SIGNAL_TERMINAL_DECODE = 1,
  M68K_ORPHAN_CODE_SIGNAL_CALLBACK_SLOT = 2
} M68kOrphanCodeSignalReason;

typedef enum M68kOrphanCodeSignalStatus {
  M68K_ORPHAN_CODE_SIGNAL_UNRESOLVED = 1,
  M68K_ORPHAN_CODE_SIGNAL_REJECTED = 2,
  M68K_ORPHAN_CODE_SIGNAL_SUPPRESSED = 3,
  M68K_ORPHAN_CODE_SIGNAL_LINKED = 4,
  M68K_ORPHAN_CODE_SIGNAL_PROMOTED = 5
} M68kOrphanCodeSignalStatus;

typedef enum M68kOrphanCodeSignalContext {
  M68K_ORPHAN_CODE_SIGNAL_CONTEXT_ACCEPTED_CODE_BOUNDARY = 1,
  M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RENDERABLE_LABEL = 2,
  M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RUNTIME_VIEW = 3
} M68kOrphanCodeSignalContext;

typedef enum M68kOrphanCodeSignalInboundEvidence {
  M68K_ORPHAN_CODE_SIGNAL_INBOUND_UNKNOWN = 1,
  M68K_ORPHAN_CODE_SIGNAL_INBOUND_JUMP_TABLE = 2,
  M68K_ORPHAN_CODE_SIGNAL_INBOUND_CALLBACK = 3,
  M68K_ORPHAN_CODE_SIGNAL_INBOUND_VECTOR = 4,
  M68K_ORPHAN_CODE_SIGNAL_INBOUND_RUNTIME_COPY = 5,
  M68K_ORPHAN_CODE_SIGNAL_INBOUND_API = 6,
  M68K_ORPHAN_CODE_SIGNAL_INBOUND_METADATA = 7,
  M68K_ORPHAN_CODE_SIGNAL_INBOUND_POLICY_SEED = 8
} M68kOrphanCodeSignalInboundEvidence;

typedef enum M68kOrphanCodeSignalNearbyDataRelation {
  M68K_ORPHAN_CODE_SIGNAL_NEARBY_DATA_NONE = 0,
  M68K_ORPHAN_CODE_SIGNAL_NEARBY_DATA_OVERLAP = 1,
  M68K_ORPHAN_CODE_SIGNAL_NEARBY_DATA_AFTER = 2,
  M68K_ORPHAN_CODE_SIGNAL_NEARBY_DATA_BEFORE = 3
} M68kOrphanCodeSignalNearbyDataRelation;

typedef enum M68kOrphanCodeSignalArbitrationFlag {
  M68K_ORPHAN_CODE_SIGNAL_ARBITRATION_REPORT_ONLY_CODE_SHAPE = 1U << 0,
  M68K_ORPHAN_CODE_SIGNAL_ARBITRATION_SUPPRESSED_BY_STRUCTURED_DATA = 1U << 1,
  M68K_ORPHAN_CODE_SIGNAL_ARBITRATION_NEGATIVE_WEAK_TEXT_EVIDENCE = 1U << 2
} M68kOrphanCodeSignalArbitrationFlag;

typedef struct M68kOrphanCodeSignalIR {
  uint32_t offset;
  uint32_t size;
  uint32_t terminal_offset;
  uint8_t terminal_flow_kind;
  uint8_t reason;
  uint8_t status;
  uint8_t confidence;
  uint8_t required_cpu;
  uint8_t instruction_count;
  uint8_t decode_conflict_count;
  uint8_t context;
  uint8_t missing_inbound;
  uint8_t nearby_data_relation;
  uint8_t nearby_data_table_kind_id;
  uint32_t nearby_data_flags;
  uint32_t arbitration_flags;
  uint32_t nearby_data_offset;
  uint32_t nearby_data_distance;
  char *detail;
} M68kOrphanCodeSignalIR;

typedef struct M68kRecoveredPlatformBaseSlotIR {
  int16_t displacement;
  char *base_name;
  M68kPlatformNameRef base_ref;
} M68kRecoveredPlatformBaseSlotIR;

typedef enum M68kAppSlotAccessKind {
  M68K_APP_SLOT_ACCESS_NONE = 0,
  M68K_APP_SLOT_ACCESS_READ = 1,
  M68K_APP_SLOT_ACCESS_WRITE = 2,
  M68K_APP_SLOT_ACCESS_READ_WRITE = 3,
  M68K_APP_SLOT_ACCESS_ADDRESS = 4
} M68kAppSlotAccessKind;

typedef struct M68kAppSlotRefIR {
  uint32_t offset;
  int16_t displacement;
  uint8_t base_reg;
  uint8_t operand_index;
  uint8_t access_kind;
} M68kAppSlotRefIR;

typedef struct M68kRecoveredPlatformTypedAccessIR {
  uint32_t offset;
  uint8_t operand_index;
  uint8_t base_reg;
  uint8_t inherited;
  uint8_t nested;
  int16_t displacement;
  int16_t field_offset;
  uint16_t struct_size;
  uint16_t field_size;
  uint8_t type_provenance_kind;
  size_t type_provenance_section_index;
  uint32_t type_provenance_offset;
  char *root_struct_name;
  char *owner_struct_name;
  char *field_name;
  char *field_expr;
  M68kPlatformNameRef root_struct_ref;
  M68kPlatformNameRef owner_struct_ref;
  M68kPlatformNameRef field_ref;
} M68kRecoveredPlatformTypedAccessIR;

typedef enum M68kPlatformUnresolvedTypedAccessClassification {
  M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP = 0,
  M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION = 1,
  M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE = 2
} M68kPlatformUnresolvedTypedAccessClassification;

typedef enum M68kPlatformTypeProvenanceKind {
  M68K_PLATFORM_TYPE_PROVENANCE_NONE = 0,
  M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT = 1,
  M68K_PLATFORM_TYPE_PROVENANCE_REGISTER_COPY = 2,
  M68K_PLATFORM_TYPE_PROVENANCE_STACK_SLOT = 3,
  M68K_PLATFORM_TYPE_PROVENANCE_BASE_SLOT = 4,
  M68K_PLATFORM_TYPE_PROVENANCE_LOOKUP_STORAGE = 5,
  M68K_PLATFORM_TYPE_PROVENANCE_APP_SLOT = 6,
  M68K_PLATFORM_TYPE_PROVENANCE_FIELD_POINTER = 7,
  M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT = 8,
  M68K_PLATFORM_TYPE_PROVENANCE_FIELD_ADDRESS = 9,
  M68K_PLATFORM_TYPE_PROVENANCE_API_INPUT = 10,
  M68K_PLATFORM_TYPE_PROVENANCE_POLICY_SEED = 11
} M68kPlatformTypeProvenanceKind;

typedef struct M68kRecoveredPlatformUnresolvedTypedAccessIR {
  uint32_t offset;
  uint8_t operand_index;
  uint8_t base_reg;
  int16_t displacement;
  uint16_t struct_size;
  uint8_t classification;
  uint16_t container_candidate_count;
  uint8_t refinement_applied;
  uint8_t type_provenance_kind;
  size_t type_provenance_section_index;
  uint32_t type_provenance_offset;
  char *root_struct_name;
  char *container_struct_name;
  char *container_field_expr;
  char *refined_struct_name;
  M68kPlatformNameRef root_struct_ref;
  M68kPlatformNameRef container_struct_ref;
  M68kPlatformNameRef refined_struct_ref;
} M68kRecoveredPlatformUnresolvedTypedAccessIR;

typedef enum M68kPlatformEffectKind {
  M68K_PLATFORM_EFFECT_NONE = 0,
  M68K_PLATFORM_EFFECT_SET_BASE_REG = 1,
  M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT = 2,
  M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG = 3,
  M68K_PLATFORM_EFFECT_SET_TYPED_REG = 4,
  M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT = 5,
  M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT = 6,
  M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT = 7
} M68kPlatformEffectKind;

typedef struct M68kPlatformNamedBaseEffectPayloadIR {
  char *base_name;
  M68kPlatformNameRef base_ref;
} M68kPlatformNamedBaseEffectPayloadIR;

typedef struct M68kPlatformTypedEffectPayloadIR {
  char *symbol_name;
  char *context_name;
  char *type_name;
  char *semantic_kind;
  char *value_domain_name;
  M68kPlatformNameRef symbol_ref;
  M68kPlatformNameRef context_ref;
  M68kPlatformNameRef type_ref;
  M68kPlatformNameRef semantic_kind_ref;
  M68kPlatformNameRef value_domain_ref;
  uint8_t has_constant_value;
  int32_t constant_value;
} M68kPlatformTypedEffectPayloadIR;

typedef struct M68kPlatformCodePtrEffectPayloadIR {
  char *field_symbol_name;
  char *owner_type_name;
  char *semantic_kind;
  M68kPlatformNameRef field_symbol_ref;
  M68kPlatformNameRef owner_type_ref;
  M68kPlatformNameRef semantic_kind_ref;
} M68kPlatformCodePtrEffectPayloadIR;

typedef struct M68kRecoveredPlatformEffectIR {
  uint32_t offset;
  uint8_t kind;
  uint8_t reg_kind;
  uint8_t reg_index;
  int16_t displacement;
  int16_t field_disp;
  size_t target_section_index;
  uint32_t target_offset;
  union {
    M68kPlatformNamedBaseEffectPayloadIR named_base;
    M68kPlatformTypedEffectPayloadIR typed;
    M68kPlatformCodePtrEffectPayloadIR code_ptr;
  } payload;
} M68kRecoveredPlatformEffectIR;

typedef struct M68kRecoveredLocalCallSummaryIR {
  uint32_t target_offset;
  uint8_t effect_kind;
  uint8_t reg_kind;
  uint8_t reg_index;
  uint8_t success_reg_kind;
  uint8_t success_reg_index;
  uint8_t success_value_known;
  int32_t success_reg_value;
  union {
    M68kPlatformNamedBaseEffectPayloadIR named_base;
    M68kPlatformTypedEffectPayloadIR typed;
  } payload;
} M68kRecoveredLocalCallSummaryIR;

typedef struct M68kRecoveredFunctionArgIR {
  uint32_t function_offset;
  uint16_t stack_offset;
  uint8_t reg_kind;
  uint8_t reg_index;
  uint32_t source_offset;
  int16_t source_displacement;
  uint8_t has_source_operand;
  uint8_t source_reg_kind;
  uint8_t source_reg_index;
  uint8_t reserved[3];
  M68kPlatformTypedEffectPayloadIR typed;
} M68kRecoveredFunctionArgIR;

typedef enum M68kPlatformCallNoteKind {
  M68K_PLATFORM_CALL_NOTE_NONE = 0,
  M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR = 1,
  M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD = 2,
  M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL = 3,
  M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL = 4,
  M68K_PLATFORM_CALL_NOTE_STACK_CLEANUP = 5
} M68kPlatformCallNoteKind;

typedef struct M68kRecoveredPlatformCallIR {
  uint32_t offset;
  uint8_t kind;
  uint8_t note_kind;
  uint8_t note_reg;
  uint8_t note_stack_cleanup_known;
  uint8_t note_return_kind;
  int16_t note_disp;
  int16_t note_field_disp;
  uint16_t note_stack_cleanup_bytes;
  char *symbol_name;
  M68kPlatformNameRef symbol_ref;
  /* Generic note context: library base, owner type, or similar note subject. */
  char *note_base_name;
  M68kPlatformNameRef note_base_ref;
  char *note_symbol_name;
  M68kPlatformNameRef note_symbol_ref;
  char *available_since;
  uint16_t available_since_version;
  char *fd_version;
  char *device_name;
} M68kRecoveredPlatformCallIR;

#define M68K_TARGET_PLATFORM_SUMMARY_VERSION_CAPACITY 16U
#define M68K_TARGET_PLATFORM_SUMMARY_RAW_DRIVER_CAPACITY 512U
#define M68K_TARGET_PLATFORM_SUMMARY_DRIVER_CAPACITY 64U
#define M68K_TARGET_PLATFORM_SUMMARY_GROUP_CAPACITY 128U

typedef enum M68kTargetOsCompatibilityStatus {
  M68K_TARGET_OS_COMPATIBILITY_NO_OS_CALLS = 0,
  M68K_TARGET_OS_COMPATIBILITY_UNKNOWN = 1,
  M68K_TARGET_OS_COMPATIBILITY_OBSERVED = 2
} M68kTargetOsCompatibilityStatus;

typedef struct M68kTargetOsRequirementDriver {
  uint32_t section_index;
  uint32_t offset;
  const char *call;
  const char *owner;
  const char *available_since;
  const char *fd_version;
  uint8_t has_owner;
  uint8_t has_fd_version;
} M68kTargetOsRequirementDriver;

typedef struct M68kTargetOsRequirementGroup {
  const char *call;
  const char *owner;
  const char *available_since;
  const char *fd_version;
  uint32_t count;
  uint8_t has_owner;
  uint8_t has_fd_version;
} M68kTargetOsRequirementGroup;

typedef struct M68kTargetOsCompatibilitySummary {
  uint8_t status;
  uint32_t call_count;
  char observed_available_since[M68K_TARGET_PLATFORM_SUMMARY_VERSION_CAPACITY][16];
  uint16_t observed_available_since_ranks[M68K_TARGET_PLATFORM_SUMMARY_VERSION_CAPACITY];
  size_t observed_available_since_count;
  char lower_observed_available_since[M68K_TARGET_PLATFORM_SUMMARY_VERSION_CAPACITY][16];
  uint16_t lower_observed_available_since_ranks[M68K_TARGET_PLATFORM_SUMMARY_VERSION_CAPACITY];
  size_t lower_observed_available_since_count;
  char observed_fd_versions[M68K_TARGET_PLATFORM_SUMMARY_VERSION_CAPACITY][16];
  uint16_t observed_fd_version_ranks[M68K_TARGET_PLATFORM_SUMMARY_VERSION_CAPACITY];
  size_t observed_fd_version_count;
  char minimum_required[16];
  M68kTargetOsRequirementDriver raw_requirement_drivers[M68K_TARGET_PLATFORM_SUMMARY_RAW_DRIVER_CAPACITY];
  size_t raw_requirement_driver_count;
  M68kTargetOsRequirementDriver max_requirement_drivers[M68K_TARGET_PLATFORM_SUMMARY_DRIVER_CAPACITY];
  size_t max_requirement_driver_count;
  M68kTargetOsRequirementGroup requirement_groups[M68K_TARGET_PLATFORM_SUMMARY_GROUP_CAPACITY];
  size_t requirement_group_count;
  uint8_t raw_requirement_drivers_truncated;
  uint8_t max_requirement_drivers_truncated;
  uint8_t requirement_groups_truncated;
} M68kTargetOsCompatibilitySummary;

typedef struct M68kTargetPlatformSummary {
  uint32_t runtime_view_count;
  M68kTargetOsCompatibilitySummary os_compatibility;
} M68kTargetPlatformSummary;

typedef enum M68kRecoveredPlatformTransferSourceKind {
  M68K_RECOVERED_PLATFORM_TRANSFER_SOURCE_NONE = 0,
  M68K_RECOVERED_PLATFORM_TRANSFER_SOURCE_LOGICAL_DISK_OFFSET = 1,
  M68K_RECOVERED_PLATFORM_TRANSFER_SOURCE_POST_READ_RUNTIME_COPY = 2
} M68kRecoveredPlatformTransferSourceKind;

typedef struct M68kRecoveredPlatformDiskReadIR {
  uint32_t offset;
  uint32_t command_value;
  uint32_t disk_offset;
  uint32_t byte_length;
  uint32_t destination_addr;
  char *command_name;
  uint8_t source_kind;
} M68kRecoveredPlatformDiskReadIR;

typedef struct M68kRecoveredPlatformRuntimeCopyIR {
  uint32_t offset;
  uint32_t source_addr;
  uint32_t destination_addr;
  uint32_t byte_length;
  uint32_t handoff_addr;
  uint8_t source_kind;
} M68kRecoveredPlatformRuntimeCopyIR;

typedef struct M68kRecoveredDirectSectionCallIR {
  uint32_t offset;
  size_t target_section_index;
  uint32_t target_offset;
} M68kRecoveredDirectSectionCallIR;

typedef enum M68kRuntimeViewMaterializationReason {
  M68K_RUNTIME_VIEW_MATERIALIZATION_REASON_NONE = 0,
  M68K_RUNTIME_VIEW_MATERIALIZED_FULL_SOURCE_POLICY_LOAD_VIEW = 1,
  M68K_RUNTIME_VIEW_MATERIALIZED_POLICY_ENTRY_POINT = 2,
  M68K_RUNTIME_VIEW_MATERIALIZED_RUNTIME_REF_TARGET = 3,
  M68K_RUNTIME_VIEW_MATERIALIZED_DISCOVERED_COPY_ENTRY = 4,
  M68K_RUNTIME_VIEW_SUPPRESSED_CONFLICTING_DISCOVERED_COPY = 101,
  M68K_RUNTIME_VIEW_SUPPRESSED_CROSSED_BY_STORAGE_XREF = 102,
  M68K_RUNTIME_VIEW_SUPPRESSED_EXIT_TO_LARGER_RUNTIME_RANGE = 103,
  M68K_RUNTIME_VIEW_SUPPRESSED_REDUNDANT_CONTAINED_VIEW = 104,
  M68K_RUNTIME_VIEW_SUPPRESSED_STORAGE_CONTINUATION = 105,
  M68K_RUNTIME_VIEW_SUPPRESSED_NO_MATERIALIZING_EVIDENCE = 106,
  M68K_RUNTIME_VIEW_SUPPRESSED_OVERLAID_BY_RUNTIME_COPY = 107,
  M68K_RUNTIME_VIEW_SUPPRESSED_INCOMPLETE_SOURCE_RANGE = 108,
  M68K_RUNTIME_VIEW_SUPPRESSED_CONTAINS_NESTED_RUNTIME_RANGE = 109
} M68kRuntimeViewMaterializationReason;

typedef enum M68kRuntimeViewRelationshipKind {
  M68K_RUNTIME_VIEW_RELATIONSHIP_NONE = 0,
  M68K_RUNTIME_VIEW_RELATIONSHIP_EXITS_TO_LARGER_RUNTIME_RANGE = 1,
  M68K_RUNTIME_VIEW_RELATIONSHIP_CONTAINED_BY_RUNTIME_RANGE = 2,
  M68K_RUNTIME_VIEW_RELATIONSHIP_OVERLAID_BY_RUNTIME_COPY = 3
} M68kRuntimeViewRelationshipKind;

typedef struct M68kRuntimeViewRelationshipIR {
  uint8_t kind;
  uint8_t reserved0;
  uint16_t reserved1;
  uint32_t runtime_view_id;
  uint32_t storage_offset;
  uint32_t runtime_address;
  uint32_t size;
} M68kRuntimeViewRelationshipIR;

typedef struct M68kRuntimeViewIR {
  uint32_t runtime_view_id;
  uint32_t storage_offset;
  uint32_t size;
  uint32_t runtime_address;
  uint8_t kind;
  uint8_t confidence;
  uint8_t materialized;
  uint8_t materialization_reason;
  uint8_t has_entry_point;
  uint8_t entry_confidence;
  uint16_t entry_point_count;
  uint32_t entry_source_offset;
  uint32_t entry_runtime_address;
  uint32_t entry_reason;
  M68kRuntimeViewRelationshipIR relationship;
} M68kRuntimeViewIR;

typedef struct M68kRuntimeAddressRefIR {
  uint32_t offset;
  uint32_t operand_index;
  uint32_t size;
  uint8_t has_target;
  uint8_t has_runtime_address;
  uint8_t has_sink_address;
  uint8_t confidence;
  size_t target_section_index;
  uint32_t target_offset;
  uint32_t runtime_address;
  uint32_t sink_address;
  uint32_t data_class_flags;
  char *data_class;
  char *owner_kind;
  char *owner_id;
  char *owner_layout_id;
  char *xref_generation_mode;
  uint32_t owner_element_offset;
} M68kRuntimeAddressRefIR;

typedef enum M68kAbsoluteMemoryOwnerKind {
  M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN = 0,
  M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL = 1,
  M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR = 2,
  M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER = 3,
  M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE = 4,
  M68K_ABSOLUTE_MEMORY_OWNER_RUNTIME_RANGE = 5,
  M68K_ABSOLUTE_MEMORY_OWNER_SECTION_STORAGE = 6,
  M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY = 7
} M68kAbsoluteMemoryOwnerKind;

typedef enum M68kAnalysisConflictState {
  M68K_ANALYSIS_CONFLICT_STATE_CLEAN = 0,
  M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP = 1,
  M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED = 2,
  M68K_ANALYSIS_CONFLICT_STATE_CONFLICTED = 3,
  M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED_CODE_TARGET = 4
} M68kAnalysisConflictState;

typedef enum M68kMemoryLayoutRecordKind {
  M68K_MEMORY_LAYOUT_RECORD_BASE_LAYOUT = 1,
  M68K_MEMORY_LAYOUT_RECORD_BASE_LAYOUT_FIELD = 2,
  M68K_MEMORY_LAYOUT_RECORD_PLATFORM_STORAGE_EFFECT = 3,
  M68K_MEMORY_LAYOUT_RECORD_PLATFORM_TYPED_ACCESS = 4,
  M68K_MEMORY_LAYOUT_RECORD_PLATFORM_UNRESOLVED_TYPED_ACCESS = 5,
  M68K_MEMORY_LAYOUT_RECORD_RUNTIME_VIEW = 6,
  M68K_MEMORY_LAYOUT_RECORD_RUNTIME_ADDRESS_REF = 7,
  M68K_MEMORY_LAYOUT_RECORD_ABSOLUTE_MEMORY_REF = 8,
  M68K_MEMORY_LAYOUT_RECORD_PLATFORM_STORAGE_LAYOUT = 9
} M68kMemoryLayoutRecordKind;

typedef struct M68kAbsoluteMemoryRefIR {
  uint32_t offset;
  uint32_t operand_index;
  uint32_t source_size;
  uint32_t access_width;
  uint32_t address;
  uint32_t owner_offset;
  uint8_t access_kind;
  uint8_t owner_kind;
  uint8_t confidence;
  uint8_t conflicted;
  uint8_t conflict_state;
  uint8_t reserved[3];
} M68kAbsoluteMemoryRefIR;

typedef struct M68kCodeStartRefIR {
  uint32_t offset;
  uint32_t reason;
  uint8_t confidence;
  uint8_t has_runtime_address;
  uint8_t reserved[2];
  size_t source_section_index;
  uint32_t source_offset;
  uint32_t runtime_address;
  uint32_t size;
} M68kCodeStartRefIR;

typedef enum M68kBaseLayoutFieldSourceKind {
  M68K_BASE_LAYOUT_FIELD_SOURCE_NONE = 0,
  M68K_BASE_LAYOUT_FIELD_SOURCE_APP_SLOT_ACCESS = 1,
  M68K_BASE_LAYOUT_FIELD_SOURCE_POLICY_RSSET_REGION = 2
} M68kBaseLayoutFieldSourceKind;

typedef enum M68kBaseLayoutKind {
  M68K_BASE_LAYOUT_KIND_UNKNOWN = 0,
  M68K_BASE_LAYOUT_KIND_APP = 1,
  M68K_BASE_LAYOUT_KIND_NAMED = 2
} M68kBaseLayoutKind;

typedef enum M68kBaseLayoutBaseKind {
  M68K_BASE_LAYOUT_BASE_KIND_UNKNOWN = 0,
  M68K_BASE_LAYOUT_BASE_KIND_APP = 1
} M68kBaseLayoutBaseKind;

typedef struct M68kBaseLayoutFieldIR {
  char *layout_name;
  char *base_symbol;
  char *sizeof_symbol;
  char *symbol;
  char *owner_struct_name;
  M68kPlatformNameRef owner_struct_ref;
  uint32_t offset;
  uint32_t size;
  uint8_t alias;
  uint8_t has_alias_of;
  uint8_t source_kind;
  uint8_t value_kind;
  uint8_t confidence;
  uint8_t conflicted;
  uint8_t layout_kind;
  uint8_t base_kind;
  char *alias_of_symbol;
  char *conflict_reason;
  uint32_t alias_of_offset;
  uint8_t has_source;
  uint8_t reserved[3];
  size_t source_section_index;
  uint32_t source_offset;
} M68kBaseLayoutFieldIR;

typedef enum M68kRangeOwnershipKind {
  M68K_RANGE_OWNERSHIP_UNKNOWN = 0,
  M68K_RANGE_OWNERSHIP_CODE = 1,
  M68K_RANGE_OWNERSHIP_TEXT = 2,
  M68K_RANGE_OWNERSHIP_TABLE = 3,
  M68K_RANGE_OWNERSHIP_STRUCTURED_DATA = 4,
  M68K_RANGE_OWNERSHIP_PLATFORM_METADATA = 5,
  M68K_RANGE_OWNERSHIP_RESIDUAL = 6,
  M68K_RANGE_OWNERSHIP_CONFLICT = 7
} M68kRangeOwnershipKind;

typedef enum M68kRangeOwnershipStatus {
  M68K_RANGE_OWNERSHIP_STATUS_UNKNOWN = 0,
  M68K_RANGE_OWNERSHIP_STATUS_CANDIDATE = 1,
  M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED = 2,
  M68K_RANGE_OWNERSHIP_STATUS_CONFLICT = 3,
  M68K_RANGE_OWNERSHIP_STATUS_BLOCKED = 4,
  M68K_RANGE_OWNERSHIP_STATUS_DEFERRED = 5
} M68kRangeOwnershipStatus;

typedef enum M68kRangeOwnershipEvidenceFlag {
  M68K_RANGE_EVIDENCE_ACCEPTED_CODE = 1U << 0,
  M68K_RANGE_EVIDENCE_BRANCH_TARGET = 1U << 1,
  M68K_RANGE_EVIDENCE_POINTER_TARGET = 1U << 2,
  M68K_RANGE_EVIDENCE_INDEXED_TABLE_ACCESS = 1U << 3,
  M68K_RANGE_EVIDENCE_API_ARGUMENT = 1U << 4,
  M68K_RANGE_EVIDENCE_PLATFORM_RECORD = 1U << 5,
  M68K_RANGE_EVIDENCE_TEXT_SHAPE = 1U << 6,
  M68K_RANGE_EVIDENCE_TERMINATOR_SHAPE = 1U << 7,
  M68K_RANGE_EVIDENCE_CODE_SHAPE = 1U << 8,
  M68K_RANGE_EVIDENCE_STRUCTURED_DATA = 1U << 9
} M68kRangeOwnershipEvidenceFlag;

typedef enum M68kRangeOwnershipNegativeEvidenceFlag {
  M68K_RANGE_NEGATIVE_MISSING_INBOUND = 1U << 0,
  M68K_RANGE_NEGATIVE_STRUCTURED_DATA_OVERLAP = 1U << 1,
  M68K_RANGE_NEGATIVE_CODE_OVERLAP = 1U << 2,
  M68K_RANGE_NEGATIVE_UNRESOLVED_CODE_TARGET = 1U << 3
} M68kRangeOwnershipNegativeEvidenceFlag;

typedef struct M68kRangeOwnershipIR {
  uint32_t start_offset;
  uint32_t end_offset;
  uint8_t kind;
  uint8_t status;
  uint8_t data_kind;
  uint8_t conflict_state;
  uint32_t positive_evidence_flags;
  uint32_t negative_evidence_flags;
  uint32_t source_offset;
  uint8_t has_source;
  uint8_t table_kind_id;
  uint8_t source_pattern_id;
  uint8_t reserved[1];
  char *role;
  char *source_pattern;
} M68kRangeOwnershipIR;

typedef struct M68kTableDescriptorIR {
  uint32_t start_offset;
  uint32_t end_offset;
  uint32_t entry_size;
  uint32_t entry_count;
  uint8_t entry_count_proof_id;
  uint8_t table_kind_id;
  uint8_t base_expression_id;
  uint8_t source_pattern_id;
  uint8_t status;
  uint32_t role_flags;
  uint8_t has_target;
  uint8_t has_consumer;
  uint8_t conflict_state;
  uint8_t table_stop_reason_id;
  uint32_t target_section_index;
  uint32_t target_offset;
  uint32_t consumer_section_index;
  uint32_t consumer_offset;
  uint8_t has_index_register;
  uint8_t index_register_kind;
  uint8_t index_register;
  uint8_t has_target_register;
  uint8_t target_register_kind;
  uint8_t target_register;
  uint8_t has_index_mask_domain;
  uint8_t has_index_compare_domain;
  uint8_t index_domain_branch_mnemonic_id;
  uint8_t reserved_registers[3];
  uint32_t index_mask_min;
  uint32_t index_mask_max;
  uint32_t index_compare_min;
  uint32_t index_compare_max;
  uint8_t has_index_loop_domain;
  uint8_t index_loop_mnemonic_id;
  uint8_t index_loop_reserved[2];
  uint32_t index_loop_min;
  uint32_t index_loop_max;
} M68kTableDescriptorIR;

typedef struct M68kTableConsumerIR {
  uint32_t consumer_offset;
  uint32_t table_section_index;
  uint32_t table_start_offset;
  uint32_t table_end_offset;
  uint32_t access_width;
  uint32_t entry_count;
  uint8_t table_kind_id;
  uint8_t source_pattern_id;
  uint8_t has_index_register;
  uint8_t index_register_kind;
  uint8_t index_register;
  uint8_t has_target_register;
  uint8_t target_register_kind;
  uint8_t target_register;
  uint8_t entry_count_proof_id;
  uint8_t table_stop_reason_id;
  uint8_t has_index_mask_domain;
  uint8_t has_index_compare_domain;
  uint8_t index_domain_branch_mnemonic_id;
  uint8_t reserved[3];
  uint32_t index_mask_min;
  uint32_t index_mask_max;
  uint32_t index_compare_min;
  uint32_t index_compare_max;
  uint8_t has_index_loop_domain;
  uint8_t index_loop_mnemonic_id;
  uint8_t index_loop_reserved[2];
  uint32_t index_loop_min;
  uint32_t index_loop_max;
} M68kTableConsumerIR;

typedef enum M68kTableEntryTargetStatus {
  M68K_TABLE_ENTRY_TARGET_STATUS_UNKNOWN = 0,
  M68K_TABLE_ENTRY_TARGET_STATUS_NUMERIC_EXACT = 1,
  M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET = 2,
  M68K_TABLE_ENTRY_TARGET_STATUS_UNRESOLVED_TARGET = 3,
  M68K_TABLE_ENTRY_TARGET_STATUS_INTERIOR_CODE_TARGET = 4,
  M68K_TABLE_ENTRY_TARGET_STATUS_CONFLICTED_TARGET = 5
} M68kTableEntryTargetStatus;

typedef struct M68kTableEntryIR {
  uint32_t table_start_offset;
  uint32_t entry_index;
  uint32_t entry_offset;
  uint32_t entry_size;
  uint32_t raw_value;
  uint8_t raw_value_width;
  uint8_t table_kind_id;
  uint8_t source_pattern_id;
  uint8_t target_status;
  uint8_t conflict_state;
  uint8_t has_target;
  uint8_t reserved[2];
  uint32_t target_section_index;
  uint32_t target_offset;
} M68kTableEntryIR;

typedef enum M68kDataReferenceSourceKind {
  M68K_DATA_REFERENCE_SOURCE_UNKNOWN = 0,
  M68K_DATA_REFERENCE_SOURCE_TABLE_ENTRY = 1
} M68kDataReferenceSourceKind;

typedef enum M68kDataReferenceEvidenceFlag {
  M68K_DATA_REFERENCE_EVIDENCE_TABLE_ENTRY = 1U << 0,
  M68K_DATA_REFERENCE_EVIDENCE_POINTER_TABLE = 1U << 1,
  M68K_DATA_REFERENCE_EVIDENCE_RELATIVE_DATA_LOOKUP = 1U << 2,
  M68K_DATA_REFERENCE_EVIDENCE_ACCEPTED_TARGET = 1U << 3,
  M68K_DATA_REFERENCE_EVIDENCE_STRUCTURED_TARGET = 1U << 4,
  M68K_DATA_REFERENCE_EVIDENCE_TEXT_TARGET = 1U << 5,
  M68K_DATA_REFERENCE_EVIDENCE_STRING_TARGET = 1U << 6
} M68kDataReferenceEvidenceFlag;

typedef struct M68kDataReferenceIR {
  uint32_t source_offset;
  uint8_t source_kind;
  uint8_t table_kind_id;
  uint8_t source_pattern_id;
  uint8_t target_status;
  uint8_t conflict_state;
  uint8_t target_kind;
  uint8_t target_table_kind_id;
  uint8_t target_source_pattern_id;
  uint32_t evidence_flags;
  uint32_t target_role_flags;
  uint32_t table_start_offset;
  uint32_t table_entry_index;
  uint32_t table_entry_offset;
  uint32_t table_entry_size;
  uint32_t raw_value;
  uint32_t target_section_index;
  uint32_t target_offset;
} M68kDataReferenceIR;

typedef enum M68kImmediateTextTokenEvidenceFlag {
  M68K_IMMEDIATE_TEXT_TOKEN_EVIDENCE_ACCEPTED_INSTRUCTION = 1U << 0,
  M68K_IMMEDIATE_TEXT_TOKEN_EVIDENCE_PRINTABLE_BYTES = 1U << 1
} M68kImmediateTextTokenEvidenceFlag;

typedef struct M68kImmediateTextTokenIR {
  uint32_t source_offset;
  uint32_t value;
  uint32_t evidence_flags;
  uint8_t operand_index;
  uint8_t width;
  uint8_t text_length;
  uint8_t reserved0;
  char text[5];
} M68kImmediateTextTokenIR;

typedef enum M68kIncompleteAnalysisKind {
  M68K_INCOMPLETE_ANALYSIS_UNKNOWN = 0,
  M68K_INCOMPLETE_ANALYSIS_CAPACITY_EXHAUSTED = 1
} M68kIncompleteAnalysisKind;

typedef enum M68kIncompleteAnalysisSourceKind {
  M68K_INCOMPLETE_ANALYSIS_SOURCE_UNKNOWN = 0,
  M68K_INCOMPLETE_ANALYSIS_SOURCE_TABLE_TARGET_SET = 1
} M68kIncompleteAnalysisSourceKind;

typedef struct M68kIncompleteAnalysisIR {
  uint8_t kind;
  uint8_t source_kind;
  uint8_t reserved[2];
  uint32_t section_index;
  uint32_t offset;
  uint32_t capacity;
  uint32_t hit_count;
} M68kIncompleteAnalysisIR;

typedef struct M68kSectionAnalysisIR {
  size_t section_index;
  char *section_name;
  M68kSectionKind section_kind;
  uint32_t section_size;
  uint8_t *certain_code_start;
  uint8_t *certain_code_byte;
  size_t certain_code_size;
  uint8_t *blocked_code_start;
  size_t blocked_code_size;
  GeneratedLabelKind *generated_label_kinds;
  uint8_t *generated_label_flags;
  size_t generated_label_size;
  char **word_exprs;
  size_t word_expr_count;
  char **long_exprs;
  size_t long_expr_count;
  uint32_t *label_offsets;
  size_t label_count;
  size_t label_capacity;
  uint8_t *label_offset_lookup;
  size_t label_offset_lookup_size;
  uint8_t *block_start_lookup;
  size_t block_start_lookup_size;
  uint8_t *string_dispatch_target_lookup;
  size_t string_dispatch_target_lookup_size;
  uint32_t *nearest_static_label_lookup;
  size_t nearest_static_label_lookup_size;
  M68kViolationIR **violation_offset_lookup;
  size_t violation_offset_lookup_size;
  uint32_t *violation_next_lookup;
  size_t violation_next_lookup_size;
  M68kRangeOwnershipIR *range_ownerships;
  size_t range_ownership_count;
  size_t range_ownership_capacity;
  M68kTableDescriptorIR *table_descriptors;
  size_t table_descriptor_count;
  size_t table_descriptor_capacity;
  M68kTableConsumerIR *table_consumers;
  size_t table_consumer_count;
  size_t table_consumer_capacity;
  M68kTableEntryIR *table_entries;
  size_t table_entry_count;
  size_t table_entry_capacity;
  M68kDataReferenceIR *data_references;
  size_t data_reference_count;
  size_t data_reference_capacity;
  M68kImmediateTextTokenIR *immediate_text_tokens;
  size_t immediate_text_token_count;
  size_t immediate_text_token_capacity;
  M68kRecoveredPlatformCallIR **recovered_platform_call_lookup;
  size_t recovered_platform_call_lookup_size;
  uint32_t *recovered_platform_call_next_lookup;
  size_t recovered_platform_call_next_lookup_size;
  M68kRecoveredPlatformEffectIR **recovered_platform_effect_lookup;
  size_t recovered_platform_effect_lookup_size;
  uint32_t *recovered_platform_effect_next_lookup;
  size_t recovered_platform_effect_next_lookup_size;
  uint8_t *recovered_platform_slot_displacement_lookup;
  size_t recovered_platform_slot_displacement_lookup_size;
  M68kCfgBlockIR *blocks;
  size_t block_count;
  size_t block_capacity;
  M68kCfgEdgeIR *edges;
  size_t edge_count;
  size_t edge_capacity;
  M68kViolationIR *violations;
  size_t violation_count;
  size_t violation_capacity;
  M68kRecoveredWordDispatchIR *recovered_word_dispatches;
  size_t recovered_word_dispatch_count;
  size_t recovered_word_dispatch_capacity;
  M68kRecoveredInlineDispatchIR *recovered_inline_dispatches;
  size_t recovered_inline_dispatch_count;
  size_t recovered_inline_dispatch_capacity;
  M68kRecoveredStringDispatchIR *recovered_string_dispatches;
  size_t recovered_string_dispatch_count;
  size_t recovered_string_dispatch_capacity;
  M68kRecoveredStringRefIR *recovered_string_refs;
  size_t recovered_string_ref_count;
  size_t recovered_string_ref_capacity;
  M68kRecoveredIndirectSiteIR *recovered_indirect_sites;
  size_t recovered_indirect_site_count;
  size_t recovered_indirect_site_capacity;
  M68kOrphanCodeSignalIR *orphan_code_signals;
  size_t orphan_code_signal_count;
  size_t orphan_code_signal_capacity;
  M68kAppSlotRefIR *app_slot_refs;
  size_t app_slot_ref_count;
  size_t app_slot_ref_capacity;
  M68kRecoveredPlatformTypedAccessIR *recovered_platform_typed_accesses;
  size_t recovered_platform_typed_access_count;
  size_t recovered_platform_typed_access_capacity;
  M68kRecoveredPlatformUnresolvedTypedAccessIR *recovered_platform_unresolved_typed_accesses;
  size_t recovered_platform_unresolved_typed_access_count;
  size_t recovered_platform_unresolved_typed_access_capacity;
  M68kRecoveredPlatformBaseSlotIR *recovered_platform_base_slots;
  size_t recovered_platform_base_slot_count;
  size_t recovered_platform_base_slot_capacity;
  M68kRecoveredPlatformEffectIR *recovered_platform_effects;
  size_t recovered_platform_effect_count;
  size_t recovered_platform_effect_capacity;
  M68kRecoveredLocalCallSummaryIR *recovered_local_call_summaries;
  size_t recovered_local_call_summary_count;
  size_t recovered_local_call_summary_capacity;
  M68kRecoveredFunctionArgIR *recovered_function_args;
  size_t recovered_function_arg_count;
  size_t recovered_function_arg_capacity;
  M68kRecoveredPlatformCallIR *recovered_platform_calls;
  size_t recovered_platform_call_count;
  size_t recovered_platform_call_capacity;
  M68kRecoveredPlatformDiskReadIR *recovered_platform_disk_reads;
  size_t recovered_platform_disk_read_count;
  size_t recovered_platform_disk_read_capacity;
  M68kRecoveredPlatformRuntimeCopyIR *recovered_platform_runtime_copies;
  size_t recovered_platform_runtime_copy_count;
  size_t recovered_platform_runtime_copy_capacity;
  M68kRecoveredDirectSectionCallIR *recovered_direct_section_calls;
  size_t recovered_direct_section_call_count;
  size_t recovered_direct_section_call_capacity;
  M68kRuntimeViewIR *runtime_views;
  size_t runtime_view_count;
  size_t runtime_view_capacity;
  M68kRuntimeAddressRefIR *runtime_address_refs;
  size_t runtime_address_ref_count;
  size_t runtime_address_ref_capacity;
  M68kAbsoluteMemoryRefIR *absolute_memory_refs;
  size_t absolute_memory_ref_count;
  size_t absolute_memory_ref_capacity;
  M68kCodeStartRefIR *code_start_refs;
  size_t code_start_ref_count;
  size_t code_start_ref_capacity;
  uint8_t recovered_direct_section_calls_indexed;
  Arena *arena;
} M68kSectionAnalysisIR;

typedef struct M68kSourceAnalysisIR {
  M68kPlatformFileKind file_kind;
  M68kAnalysisPolicy policy;
  M68kAnalysisFindings findings;
  M68kAnalysisStructuredDataItem *structured_data_items;
  size_t structured_data_item_count;
  size_t structured_data_item_capacity;
  M68kIncompleteAnalysisIR *incomplete_analyses;
  size_t incomplete_analysis_count;
  size_t incomplete_analysis_capacity;
  M68kPlatformStorageLayoutIR *platform_storage_layouts;
  size_t platform_storage_layout_count;
  size_t platform_storage_layout_capacity;
  M68kBaseLayoutFieldIR *base_layout_fields;
  size_t base_layout_field_count;
  size_t base_layout_field_capacity;
  M68kSectionAnalysisIR *sections;
  size_t section_count;
  size_t section_capacity;
  Arena *arena;
} M68kSourceAnalysisIR;

void m68k_ir_symbol_ref_init(M68kSymbolRefIR *symbol_ref);
void m68k_render_policy_init_default(M68kRenderPolicy *policy);
void m68k_render_policy_init_for_syntax(M68kRenderPolicy *policy, uint8_t syntax_mode);
int m68k_ir_parse_syntax_mode_name(const char *text, uint8_t *out_syntax_mode);
void m68k_analysis_policy_init_default(M68kAnalysisPolicy *policy);
void m68k_analysis_policy_destroy(M68kAnalysisPolicy *policy);
int m68k_analysis_policy_copy(M68kAnalysisPolicy *dest, const M68kAnalysisPolicy *src);
int m68k_ir_source_analysis_set_policy(M68kSourceAnalysisIR *source_analysis, const M68kAnalysisPolicy *policy);
int m68k_ir_source_analysis_append_structured_data_item(M68kSourceAnalysisIR *source_analysis,
  const M68kAnalysisStructuredDataItem *item);
int m68k_ir_source_analysis_append_incomplete_analysis(M68kSourceAnalysisIR *source_analysis,
  const M68kIncompleteAnalysisIR *incomplete);
size_t m68k_ir_source_analysis_structured_data_item_count(const M68kSourceAnalysisIR *source_analysis);
const M68kAnalysisStructuredDataItem *m68k_ir_source_analysis_structured_data_item_at(
  const M68kSourceAnalysisIR *source_analysis, size_t index);
const char *m68k_analysis_structured_data_role_name_for_flags(uint32_t semantic_role_flags);
const char *m68k_analysis_structured_data_source_pattern_name(uint8_t source_pattern_id);
const char *m68k_analysis_table_kind_name(uint8_t table_kind_id);
const char *m68k_analysis_table_base_expression_name(uint8_t base_expression_id);
const char *m68k_analysis_table_entry_count_proof_name(uint8_t proof_id);
const char *m68k_analysis_table_stop_reason_name(uint8_t stop_reason_id);
const char *m68k_table_entry_target_status_name(uint8_t status);
const char *m68k_data_reference_source_kind_name(uint8_t source_kind);
const char *m68k_incomplete_analysis_kind_name(uint8_t kind);
const char *m68k_incomplete_analysis_source_kind_name(uint8_t source_kind);
uint8_t m68k_analysis_table_entry_count_proof_for_source_pattern(uint8_t source_pattern_id);
uint8_t m68k_analysis_table_stop_reason_for_entry_count_proof(uint8_t proof_id);
uint8_t m68k_recovered_indirect_source_pattern_id(uint8_t shape);
const char *m68k_recovered_indirect_source_pattern_name(uint8_t source_pattern_id);
const char *m68k_recovered_platform_transfer_source_kind_name(uint8_t source_kind);
int m68k_asm_operand_absolute_value(uint8_t kind, const M68kAsmOperandValue *operand, uint32_t *out_value);
void m68k_analysis_structured_data_item_set_semantic_role_flags(M68kAnalysisStructuredDataItem *item,
  uint32_t semantic_role_flags);
void m68k_analysis_structured_data_item_refresh_table_metadata(M68kAnalysisStructuredDataItem *item);
int m68k_analysis_structured_data_item_set_text(M68kAnalysisStructuredDataItem *item,
  uint8_t field, const char *text, size_t length);
const char *m68k_analysis_structured_data_item_text(const M68kAnalysisStructuredDataItem *item,
  uint8_t field, size_t *out_length);
void m68k_analysis_findings_init(M68kAnalysisFindings *findings);
void m68k_platform_name_ref_init(M68kPlatformNameRef *ref);
int m68k_platform_name_ref_is_set(const M68kPlatformNameRef *ref);
const char *m68k_platform_name_ref_resolve_text(const M68kPlatformNameRef *ref);
const char *m68k_platform_name_ref_resolve_text_or_fallback(const M68kPlatformNameRef *ref, const char *text);
const char *m68k_target_os_compatibility_status_name(uint8_t status);
int m68k_target_platform_summary_build(const M68kSourceAnalysisIR *source_analysis, uint8_t platform_backend_kind,
  M68kTargetPlatformSummary *out_summary);
void m68k_ir_instruction_init(M68kInstructionIR *instruction);
const char *m68k_ir_instruction_mnemonic_name(const M68kInstructionIR *instruction);
void m68k_ir_data_item_init(M68kDataItemIR *item);
void m68k_ir_statement_init(M68kStatementIR *statement);
void m68k_ir_statement_free(M68kStatementIR *statement);
int m68k_ir_section_create(M68kSectionIR *section, Arena *result_arena);
/* Arena-backed setters never reclaim replaced storage until m68k_ir_section_destroy(). */
int m68k_ir_section_set_name(M68kSectionIR *section, const char *name);
void m68k_ir_section_destroy(M68kSectionIR *section);
int m68k_ir_section_append_statement(M68kSectionIR *section, const M68kStatementIR *statement);
int m68k_ir_source_file_create(M68kSourceFileIR *source_file);
void m68k_ir_source_file_destroy(M68kSourceFileIR *source_file);
int m68k_ir_source_file_append_section(M68kSourceFileIR *source_file, const M68kSectionIR *section);
int m68k_ir_section_analysis_create(M68kSectionAnalysisIR *section_analysis, Arena *result_arena);
/* Arena-backed setters never reclaim replaced storage until m68k_ir_section_analysis_destroy(). */
int m68k_ir_section_analysis_set_name(M68kSectionAnalysisIR *section_analysis, const char *name);
void m68k_ir_section_analysis_destroy(M68kSectionAnalysisIR *section_analysis);
int m68k_ir_section_analysis_set_code_map(M68kSectionAnalysisIR *section_analysis, const uint8_t *code_start,
  const uint8_t *code_byte, size_t size);
int m68k_ir_section_analysis_set_blocked_code_map(M68kSectionAnalysisIR *section_analysis,
  const uint8_t *blocked_code_start, size_t size);
int m68k_ir_section_analysis_set_generated_labels(M68kSectionAnalysisIR *section_analysis, const GeneratedLabelKind *label_kinds,
  const uint8_t *label_flags, size_t size);
int m68k_ir_section_analysis_set_word_exprs(M68kSectionAnalysisIR *section_analysis, char *const *word_exprs, size_t count);
int m68k_ir_section_analysis_set_long_exprs(M68kSectionAnalysisIR *section_analysis, char *const *long_exprs, size_t count);
int m68k_ir_section_analysis_add_label(M68kSectionAnalysisIR *section_analysis, uint32_t offset);
int m68k_ir_section_analysis_append_block(M68kSectionAnalysisIR *section_analysis, const M68kCfgBlockIR *block);
int m68k_ir_section_analysis_append_edge(M68kSectionAnalysisIR *section_analysis, const M68kCfgEdgeIR *edge);
int m68k_ir_section_analysis_append_range_ownership(M68kSectionAnalysisIR *section_analysis,
    const M68kRangeOwnershipIR *range);
int m68k_ir_section_analysis_append_table_descriptor(M68kSectionAnalysisIR *section_analysis,
    const M68kTableDescriptorIR *descriptor);
int m68k_ir_section_analysis_append_table_consumer(M68kSectionAnalysisIR *section_analysis,
    const M68kTableConsumerIR *consumer);
int m68k_ir_section_analysis_append_table_entry(M68kSectionAnalysisIR *section_analysis,
    const M68kTableEntryIR *entry);
int m68k_ir_section_analysis_append_data_reference(M68kSectionAnalysisIR *section_analysis,
    const M68kDataReferenceIR *ref);
int m68k_ir_section_analysis_append_immediate_text_token(M68kSectionAnalysisIR *section_analysis,
    const M68kImmediateTextTokenIR *token);
int m68k_ir_section_analysis_add_violation(M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t kind, const char *message);
int m68k_ir_section_analysis_append_recovered_word_dispatch(M68kSectionAnalysisIR *section_analysis,
  const M68kRecoveredWordDispatchIR *dispatch);
int m68k_ir_section_analysis_append_recovered_inline_dispatch(M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredInlineDispatchIR *dispatch);
int m68k_ir_section_analysis_append_recovered_string_dispatch(M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredStringDispatchIR *dispatch);
int m68k_ir_section_analysis_append_recovered_string_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredStringRefIR *ref);
int m68k_ir_section_analysis_append_recovered_indirect_site(M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredIndirectSiteIR *site);
int m68k_ir_section_analysis_append_orphan_code_signal(M68kSectionAnalysisIR *section_analysis,
    const M68kOrphanCodeSignalIR *signal);
int m68k_ir_section_analysis_append_app_slot_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kAppSlotRefIR *ref);
int m68k_ir_section_analysis_append_recovered_platform_typed_access(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t offset, uint8_t operand_index, uint8_t base_reg, int16_t displacement,
    int16_t field_offset, uint16_t struct_size, uint16_t field_size, const char *root_struct_name,
    const char *owner_struct_name, const char *field_name, const char *field_expr, uint8_t inherited,
    uint8_t nested, uint8_t type_provenance_kind, size_t type_provenance_section_index,
    uint32_t type_provenance_offset);
int m68k_ir_section_analysis_append_recovered_platform_unresolved_typed_access(
    M68kSectionAnalysisIR *section_analysis, uint8_t platform_kind, uint32_t offset, uint8_t operand_index,
    uint8_t base_reg, int16_t displacement, uint16_t struct_size, const char *root_struct_name,
    uint8_t classification, uint16_t container_candidate_count, const char *container_struct_name,
    const char *container_field_expr, uint8_t refinement_applied, const char *refined_struct_name,
    uint8_t type_provenance_kind, size_t type_provenance_section_index, uint32_t type_provenance_offset);
int m68k_ir_section_analysis_append_recovered_platform_base_slot(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, int16_t displacement, const char *base_name);
int m68k_ir_section_analysis_append_recovered_platform_effect(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t offset, uint8_t kind, uint8_t reg_kind, uint8_t reg_index, int16_t displacement,
    int16_t field_disp, const char *base_name, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value);
int m68k_ir_section_analysis_append_recovered_platform_global_base_slot_effect(
    M68kSectionAnalysisIR *section_analysis, uint8_t platform_kind, uint32_t offset, size_t target_section_index,
    uint32_t target_offset, const char *base_name);
int m68k_ir_section_analysis_append_recovered_platform_typed_global_slot_effect(
    M68kSectionAnalysisIR *section_analysis, uint8_t platform_kind, uint32_t offset, size_t target_section_index,
    uint32_t target_offset, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name);
int m68k_ir_section_analysis_append_recovered_local_call_summary(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t target_offset, uint8_t effect_kind, uint8_t reg_kind, uint8_t reg_index,
    uint8_t success_reg_kind, uint8_t success_reg_index, uint8_t success_value_known, int32_t success_reg_value,
    const char *base_name, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value);
int m68k_ir_section_analysis_append_recovered_function_arg(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t function_offset, uint16_t stack_offset, uint8_t reg_kind, uint8_t reg_index,
    const char *context_name, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value, uint8_t has_source_operand,
    uint32_t source_offset, uint8_t source_reg_kind, uint8_t source_reg_index, int16_t source_displacement);
int m68k_ir_section_analysis_append_recovered_platform_call(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t offset, uint8_t kind, const char *symbol_name, uint8_t note_kind, const char *note_base_name,
    const char *note_symbol_name, uint8_t note_reg, int16_t note_disp, int16_t note_field_disp,
    uint8_t note_stack_cleanup_known, uint16_t note_stack_cleanup_bytes, uint8_t note_return_kind,
    const char *available_since, const char *fd_version);
int m68k_ir_section_analysis_set_recovered_platform_call_device_name(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind, const char *device_name);
int m68k_ir_section_analysis_append_recovered_platform_disk_read(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint32_t command_value, const char *command_name, uint32_t disk_offset,
    uint32_t byte_length, uint32_t destination_addr, uint8_t source_kind);
int m68k_ir_section_analysis_append_recovered_platform_runtime_copy(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint32_t source_addr, uint32_t destination_addr, uint32_t byte_length,
    uint32_t handoff_addr, uint8_t source_kind);
int m68k_ir_section_analysis_append_recovered_direct_section_call(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, size_t target_section_index, uint32_t target_offset);
int m68k_ir_section_analysis_append_runtime_view(M68kSectionAnalysisIR *section_analysis,
    const M68kRuntimeViewIR *runtime_view);
int m68k_ir_section_analysis_append_runtime_address_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kRuntimeAddressRefIR *runtime_address_ref);
int m68k_ir_section_analysis_append_absolute_memory_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kAbsoluteMemoryRefIR *absolute_memory_ref);
int m68k_ir_section_analysis_append_code_start_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kCodeStartRefIR *code_start_ref);
int m68k_ir_source_analysis_create(M68kSourceAnalysisIR *source_analysis);
void m68k_ir_source_analysis_destroy(M68kSourceAnalysisIR *source_analysis);
int m68k_ir_source_analysis_append_platform_storage_layout(M68kSourceAnalysisIR *source_analysis,
  const M68kPlatformStorageLayoutIR *layout);
int m68k_ir_source_analysis_append_base_layout_field(M68kSourceAnalysisIR *source_analysis,
  const M68kBaseLayoutFieldIR *field);
int m68k_ir_source_analysis_append_section(M68kSourceAnalysisIR *source_analysis, const M68kSectionAnalysisIR *section_analysis);
void m68k_ir_source_analysis_finalize_table_conflicts(M68kSourceAnalysisIR *source_analysis);
void m68k_ir_source_analysis_finalize_base_layout_conflicts(M68kSourceAnalysisIR *source_analysis);

#endif
