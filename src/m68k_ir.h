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
#define M68K_ANALYSIS_ENTRY_POINT_LIMIT 64U
#define M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT 256U
#define M68K_ANALYSIS_NAMED_LABEL_LIMIT 128U
#define M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT 128U
#define M68K_ANALYSIS_ENTRY_COMMENT_LIMIT 128U

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
  M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING = 1U << 7
} M68kAnalysisStructuredDataRoleFlag;

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
  uint8_t reserved2[3];
  uint32_t consumer_section;
  uint32_t consumer_offset;
  uint32_t semantic_role_flags;
  char label[64];
  char struct_name[64];
  char field_name[64];
  char field_type[64];
  char c_type[64];
  char pointer_struct[64];
  char value_domain[64];
  char constant_name[64];
  char semantic_role[64];
  char source_pattern[64];
  char comment[64];
} M68kAnalysisStructuredDataItem;

typedef struct M68kAnalysisNamedLabel {
  uint8_t has_section_index;
  uint8_t reserved[3];
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
  uint8_t reserved[2];
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
  M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_LAYOUT = 1U
} M68kAnalysisRssetLayoutRegionFlag;

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
  uint32_t entry_offset;
  M68kAnalysisRegisterSeed register_seeds[M68K_ANALYSIS_REGISTER_SEED_LIMIT];
  M68kAnalysisEntryPoint entry_points[M68K_ANALYSIS_ENTRY_POINT_LIMIT];
  M68kAnalysisStructuredDataItem structured_data_items[M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT];
  M68kAnalysisNamedLabel named_labels[M68K_ANALYSIS_NAMED_LABEL_LIMIT];
  M68kAnalysisEntryComment entry_comments[M68K_ANALYSIS_ENTRY_COMMENT_LIMIT];
  M68kAnalysisRuntimeRange runtime_ranges[M68K_ANALYSIS_RUNTIME_RANGE_LIMIT];
  M68kAnalysisRuntimeEntryPoint runtime_entry_points[M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT];
  M68kAnalysisRssetLayoutRegion rsset_layout_regions[M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT];
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
  M68kAsmOperandValue value;
  uint32_t exact_render_value;
  M68kSymbolRefIR symbol_ref;
} M68kOperandIR;

typedef struct M68kInstructionIR {
  uint16_t asm_form_index;
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

#define M68K_STATEMENT_SOURCE_BYTES_MAX 16U

typedef struct M68kStatementIR {
  uint8_t kind;
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
  uint8_t owns_arena;
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
  M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_INSUFFICIENT_ENTRIES = 1
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
  uint8_t has_table_bounds;
  uint8_t table_bounds_status;
  uint8_t reserved[2];
  uint32_t target;
  uint32_t target_count;
  uint32_t table_offset;
  uint32_t table_size;
  uint32_t table_entry_size;
  uint32_t table_entry_count;
  char *detail;
} M68kRecoveredIndirectSiteIR;

typedef enum M68kOrphanCodeSignalReason {
  M68K_ORPHAN_CODE_SIGNAL_TERMINAL_DECODE = 1
} M68kOrphanCodeSignalReason;

typedef enum M68kOrphanCodeSignalStatus {
  M68K_ORPHAN_CODE_SIGNAL_UNRESOLVED = 1
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
  uint8_t reserved[1];
  uint32_t nearby_data_flags;
  char *nearby_data_class;
  char *nearby_data_relation;
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
  M68K_PLATFORM_TYPE_PROVENANCE_FIELD_ADDRESS = 9
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
  M68K_RUNTIME_VIEW_SUPPRESSED_OVERLAID_BY_RUNTIME_COPY = 107
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
  char *data_class;
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
  uint8_t reserved0[2];
  char *alias_of_symbol;
  char *conflict_reason;
  uint32_t alias_of_offset;
  uint8_t has_source;
  uint8_t reserved[3];
  size_t source_section_index;
  uint32_t source_offset;
} M68kBaseLayoutFieldIR;

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
  uint8_t owns_arena;
} M68kSectionAnalysisIR;

typedef struct M68kSourceAnalysisIR {
  M68kPlatformFileKind file_kind;
  M68kAnalysisPolicy policy;
  M68kAnalysisFindings findings;
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
uint32_t m68k_analysis_structured_data_role_flags_for_text(const char *semantic_role);
void m68k_analysis_structured_data_item_set_semantic_role(M68kAnalysisStructuredDataItem *item,
  const char *semantic_role);
void m68k_analysis_findings_init(M68kAnalysisFindings *findings);
void m68k_platform_name_ref_init(M68kPlatformNameRef *ref);
int m68k_platform_name_ref_is_set(const M68kPlatformNameRef *ref);
const char *m68k_platform_name_ref_resolve_text(const M68kPlatformNameRef *ref);
const char *m68k_platform_name_ref_resolve_text_or_fallback(const M68kPlatformNameRef *ref, const char *text);
void m68k_ir_instruction_init(M68kInstructionIR *instruction);
const char *m68k_ir_instruction_mnemonic_name(const M68kInstructionIR *instruction);
void m68k_ir_data_item_init(M68kDataItemIR *item);
void m68k_ir_statement_init(M68kStatementIR *statement);
void m68k_ir_statement_free(M68kStatementIR *statement);
int m68k_ir_section_create(M68kSectionIR *section);
/* Arena-backed setters never reclaim replaced storage until m68k_ir_section_destroy(). */
int m68k_ir_section_set_name(M68kSectionIR *section, const char *name);
void m68k_ir_section_destroy(M68kSectionIR *section);
int m68k_ir_section_append_statement(M68kSectionIR *section, const M68kStatementIR *statement);
int m68k_ir_source_file_create(M68kSourceFileIR *source_file);
void m68k_ir_source_file_destroy(M68kSourceFileIR *source_file);
int m68k_ir_source_file_append_section(M68kSourceFileIR *source_file, const M68kSectionIR *section);
int m68k_ir_section_analysis_create(M68kSectionAnalysisIR *section_analysis);
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
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value);
int m68k_ir_section_analysis_append_recovered_platform_call(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t offset, uint8_t kind, const char *symbol_name, uint8_t note_kind, const char *note_base_name,
    const char *note_symbol_name, uint8_t note_reg, int16_t note_disp, int16_t note_field_disp,
    uint8_t note_stack_cleanup_known, uint16_t note_stack_cleanup_bytes, uint8_t note_return_kind,
    const char *available_since, const char *fd_version);
int m68k_ir_section_analysis_set_recovered_platform_call_device_name(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind, const char *device_name);
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
int m68k_ir_source_analysis_append_base_layout_field(M68kSourceAnalysisIR *source_analysis,
  const M68kBaseLayoutFieldIR *field);
int m68k_ir_source_analysis_append_section(M68kSourceAnalysisIR *source_analysis, const M68kSectionAnalysisIR *section_analysis);

#endif
