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

typedef struct M68kAnalysisPolicy {
  uint8_t max_cpu;
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
  char name[64];
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
  M68K_STATEMENT_ALIGN = 4
} M68kStatementKind;

typedef struct M68kStatementIR {
  uint8_t kind;
  uint32_t offset;
  char *label_name;
  char *comment;
  uint8_t label_is_generated;
  union {
    M68kInstructionIR instruction;
    M68kDataItemIR data;
    uint32_t alignment;
  } u;
} M68kStatementIR;

typedef struct M68kSectionIR {
  char *name;
  M68kSectionKind kind;
  uint32_t size;
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
  M68K_VIOLATION_UNRESOLVED_INDIRECT = 4
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

typedef struct M68kRecoveredPlatformBaseSlotIR {
  int16_t displacement;
  char *base_name;
  M68kPlatformNameRef base_ref;
} M68kRecoveredPlatformBaseSlotIR;

typedef enum M68kPlatformEffectKind {
  M68K_PLATFORM_EFFECT_NONE = 0,
  M68K_PLATFORM_EFFECT_SET_BASE_REG = 1,
  M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT = 2,
  M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG = 3,
  M68K_PLATFORM_EFFECT_SET_TYPED_REG = 4,
  M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT = 5
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
} M68kRecoveredPlatformCallIR;

typedef struct M68kSectionAnalysisIR {
  size_t section_index;
  char *section_name;
  M68kSectionKind section_kind;
  uint32_t section_size;
  uint8_t *certain_code_start;
  uint8_t *certain_code_byte;
  size_t certain_code_size;
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
  M68kRecoveredPlatformBaseSlotIR *recovered_platform_base_slots;
  size_t recovered_platform_base_slot_count;
  size_t recovered_platform_base_slot_capacity;
  M68kRecoveredPlatformEffectIR *recovered_platform_effects;
  size_t recovered_platform_effect_count;
  size_t recovered_platform_effect_capacity;
  M68kRecoveredLocalCallSummaryIR *recovered_local_call_summaries;
  size_t recovered_local_call_summary_count;
  size_t recovered_local_call_summary_capacity;
  M68kRecoveredPlatformCallIR *recovered_platform_calls;
  size_t recovered_platform_call_count;
  size_t recovered_platform_call_capacity;
  Arena *arena;
  uint8_t owns_arena;
} M68kSectionAnalysisIR;

typedef struct M68kSourceAnalysisIR {
  M68kPlatformFileKind file_kind;
  M68kAnalysisPolicy policy;
  M68kAnalysisFindings findings;
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
int m68k_ir_section_analysis_append_recovered_platform_base_slot(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, int16_t displacement, const char *base_name);
int m68k_ir_section_analysis_append_recovered_platform_effect(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t offset, uint8_t kind, uint8_t reg_kind, uint8_t reg_index, int16_t displacement,
    int16_t field_disp, const char *base_name, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value);
int m68k_ir_section_analysis_append_recovered_local_call_summary(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t target_offset, uint8_t effect_kind, uint8_t reg_kind, uint8_t reg_index,
    uint8_t success_reg_kind, uint8_t success_reg_index, uint8_t success_value_known, int32_t success_reg_value,
    const char *base_name, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value);
int m68k_ir_section_analysis_append_recovered_platform_call(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t offset, uint8_t kind, const char *symbol_name, uint8_t note_kind, const char *note_base_name,
    const char *note_symbol_name, uint8_t note_reg, int16_t note_disp, int16_t note_field_disp,
    uint8_t note_stack_cleanup_known, uint16_t note_stack_cleanup_bytes, uint8_t note_return_kind,
    const char *available_since, const char *fd_version);
int m68k_ir_source_analysis_create(M68kSourceAnalysisIR *source_analysis);
void m68k_ir_source_analysis_destroy(M68kSourceAnalysisIR *source_analysis);
int m68k_ir_source_analysis_append_section(M68kSourceAnalysisIR *source_analysis, const M68kSectionAnalysisIR *section_analysis);

#endif
