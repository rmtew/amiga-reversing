#ifndef M68K_IR_H
#define M68K_IR_H

#include "m68k_asm_tables.h"
#include "m68k_object.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_IR_INVALID_FORM_INDEX ((uint16_t)0xFFFFu)

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

typedef struct M68kRenderPolicy {
  M68kAssemblerSyntaxPolicy syntax;
  M68kPresentationPolicy presentation;
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

typedef struct M68kSymbolRefIR {
  uint8_t kind;
  uint8_t has_name;
  uint8_t name_is_generated;
  size_t symbol_index;
  size_t section_index;
  int has_symbol;
  int has_section;
  int32_t addend;
  char name[64];
} M68kSymbolRefIR;

typedef struct M68kOperandIR {
  uint8_t kind;
  M68kAsmOperandValue value;
  M68kSymbolRefIR symbol_ref;
} M68kOperandIR;

typedef struct M68kInstructionIR {
  uint16_t form_index;
  uint8_t mnemonic_id;
  uint8_t target_cpu;
  char mnemonic[32];
  char size_suffix;
  size_t operand_count;
  M68kOperandIR operands[4];
  size_t byte_count;
} M68kInstructionIR;

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
} M68kSectionIR;

typedef struct M68kSourceFileIR {
  M68kPlatformFileKind file_kind;
  uint8_t has_atari_st_program_flags;
  uint32_t atari_st_program_flags;
  M68kSectionIR *sections;
  size_t section_count;
  size_t section_capacity;
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
  M68K_VIOLATION_INVALID_INTERIOR_REFERENCE = 3
} M68kViolationKind;

typedef struct M68kViolationIR {
  uint32_t offset;
  uint8_t kind;
  char *message;
} M68kViolationIR;

typedef struct M68kSectionAnalysisIR {
  size_t section_index;
  char *section_name;
  M68kSectionKind section_kind;
  uint32_t section_size;
  uint8_t *certain_code_start;
  uint8_t *certain_code_byte;
  size_t certain_code_size;
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
} M68kSectionAnalysisIR;

typedef struct M68kSourceAnalysisIR {
  M68kPlatformFileKind file_kind;
  M68kAnalysisPolicy policy;
  M68kAnalysisFindings findings;
  M68kSectionAnalysisIR *sections;
  size_t section_count;
  size_t section_capacity;
} M68kSourceAnalysisIR;

void m68k_ir_symbol_ref_init(M68kSymbolRefIR *symbol_ref);
void m68k_render_policy_init_default(M68kRenderPolicy *policy);
void m68k_render_policy_init_for_syntax(M68kRenderPolicy *policy, uint8_t syntax_mode);
int m68k_ir_parse_syntax_mode_name(const char *text, uint8_t *out_syntax_mode);
void m68k_analysis_policy_init_default(M68kAnalysisPolicy *policy);
void m68k_analysis_findings_init(M68kAnalysisFindings *findings);
void m68k_ir_instruction_init(M68kInstructionIR *instruction);
void m68k_ir_data_item_init(M68kDataItemIR *item);
void m68k_ir_statement_init(M68kStatementIR *statement);
void m68k_ir_statement_free(M68kStatementIR *statement);
void m68k_ir_section_init(M68kSectionIR *section);
void m68k_ir_section_free(M68kSectionIR *section);
int m68k_ir_section_append_statement(M68kSectionIR *section, const M68kStatementIR *statement);
void m68k_ir_source_file_init(M68kSourceFileIR *source_file);
void m68k_ir_source_file_free(M68kSourceFileIR *source_file);
int m68k_ir_source_file_append_section(M68kSourceFileIR *source_file, const M68kSectionIR *section);
void m68k_ir_section_analysis_init(M68kSectionAnalysisIR *section_analysis);
void m68k_ir_section_analysis_free(M68kSectionAnalysisIR *section_analysis);
int m68k_ir_section_analysis_set_code_map(M68kSectionAnalysisIR *section_analysis, const uint8_t *code_start,
  const uint8_t *code_byte, size_t size);
int m68k_ir_section_analysis_add_label(M68kSectionAnalysisIR *section_analysis, uint32_t offset);
int m68k_ir_section_analysis_append_block(M68kSectionAnalysisIR *section_analysis, const M68kCfgBlockIR *block);
int m68k_ir_section_analysis_append_edge(M68kSectionAnalysisIR *section_analysis, const M68kCfgEdgeIR *edge);
int m68k_ir_section_analysis_add_violation(M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t kind, const char *message);
void m68k_ir_source_analysis_init(M68kSourceAnalysisIR *source_analysis);
void m68k_ir_source_analysis_free(M68kSourceAnalysisIR *source_analysis);
int m68k_ir_source_analysis_append_section(M68kSourceAnalysisIR *source_analysis, const M68kSectionAnalysisIR *section_analysis);

#endif
