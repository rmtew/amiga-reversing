/* Ordered render-preview IR for facts_v2 analysis. */
#ifndef M68K_RENDER_IR_H
#define M68K_RENDER_IR_H

#include "m68k_decode_ir.h"
#include "m68k_fact_ir.h"
#include "m68k_render_plan.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_RENDER_ASM_INCLUDE_LIMIT 64U
#define M68K_RENDER_ASM_INCLUDE_PATH_SIZE 64U
#define M68K_RENDER_ASM_DECLARATION_LIMIT 1024U
#define M68K_RENDER_ASM_SYMBOL_NAME_SIZE 64U

typedef struct Arena Arena;

typedef enum M68kRenderIRAsmSourceFailureKind {
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE = 0,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER = 1,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_BYTE_MISMATCH = 2,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_INSTRUCTION_RELOCATION = 3,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_UNRESOLVED_LABEL = 4,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_INTERIOR_CONFLICT = 5,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_RELOCATION = 6,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_RELOCATION_ANCHOR = 7,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_UNASSEMBLABLE_HUNK_DATA_RELOCATION = 8,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_UNASSEMBLABLE_HUNK_BASE_REGISTER_RELOCATION = 9,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_REQUIRED_INSTRUCTION = 10,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_TABLE_TARGET_SET_LIMIT = 11,
  M68K_RENDER_IR_ASM_SOURCE_FAILURE_SOURCE_QUALITY = 12
} M68kRenderIRAsmSourceFailureKind;

typedef struct M68kRenderIRPreview {
  uint32_t statement_count;
  uint32_t label_statement_count;
  uint32_t instruction_statement_count;
  uint32_t data_statement_count;
  double lookup_seconds;
  double platform_pass_seconds;
  double platform_pass_base_slot_seconds;
  double platform_pass_call_summary_seconds;
  double platform_pass_typed_ref_seconds;
  double platform_pass_call_comment_seconds;
  double platform_pass_app_slot_seconds;
  double platform_pass_runtime_data_seconds;
  double platform_pass_hardware_data_seconds;
  double platform_pass_generic_data_seconds;
  double header_seconds;
  double walk_seconds;
  double footer_seconds;
  uint64_t structural_hash;
  uint64_t text_hash;
  uint32_t text_bytes;
  uint64_t asm_source_hash;
  uint32_t asm_source_bytes;
  uint32_t asm_source_lines;
  uint32_t asm_source_plan_rows;
  uint32_t asm_source_plan_lines;
  uint32_t asm_source_plan_bytes;
  uint32_t asm_source_relocation_exprs;
  uint32_t asm_source_symbolic_instructions;
  uint32_t asm_source_numeric_runtime_refs;
  uint32_t asm_source_first_numeric_runtime_ref_section;
  uint32_t asm_source_first_numeric_runtime_ref_offset;
  uint32_t asm_source_first_numeric_runtime_ref_target_section;
  uint32_t asm_source_first_numeric_runtime_ref_target_offset;
  uint32_t asm_source_first_numeric_runtime_ref_runtime_address;
  uint32_t platform_base_slot_count;
  uint32_t platform_call_count;
  uint32_t platform_effect_count;
  uint32_t asm_source_lossy_numeric_hunk_relocations;
  uint32_t asm_source_instruction_render_failures;
  uint32_t asm_source_instruction_byte_mismatches;
  uint32_t asm_source_instruction_relocation_failures;
  uint32_t asm_source_first_failure_kind;
  uint32_t asm_source_first_failure_section;
  uint32_t asm_source_first_failure_offset;
  uint32_t asm_source_first_failure_aux_offset;
  char *asm_source_text;
  size_t asm_source_text_capacity;
  M68kRenderPlan asm_source_plan;
  M68kRenderPlanRowBuilder asm_source_row_builder;
  Arena *asm_source_header_arena;
  Arena *scratch_arena;
  char asm_source_includes[M68K_RENDER_ASM_INCLUDE_LIMIT][M68K_RENDER_ASM_INCLUDE_PATH_SIZE];
  char asm_source_declarations[M68K_RENDER_ASM_DECLARATION_LIMIT][M68K_RENDER_ASM_SYMBOL_NAME_SIZE];
  char *asm_source_declaration_lines[M68K_RENDER_ASM_DECLARATION_LIMIT];
  uint32_t asm_source_body_start_byte;
  uint16_t asm_source_include_count;
  uint16_t asm_source_declaration_count;
  uint8_t platform_backend_kind;
  uint8_t collect_asm_source_text;
  uint8_t collect_asm_source_hash;
  uint8_t asm_source_allocation_failed;
} M68kRenderIRPreview;

void m68k_render_ir_preview_init(M68kRenderIRPreview *preview);
void m68k_render_ir_preview_destroy(M68kRenderIRPreview *preview);
int candidate_calls_a6_lvo(const M68kDecodeCandidate *candidate, int16_t *out_lvo);
int m68k_render_ir_preview_build(const M68kObject *object, const M68kDecodeIR *decode, const M68kFactIR *facts,
  const M68kAnalysisPolicy *policy, uint8_t **accepted_start, uint8_t **accepted_bytes, int render_text_preview,
  int render_asm_source, int collect_asm_source_text, int emit_asm_source_text,
  M68kRenderIRPreview *out_preview, M68kSourceAnalysisIR *out_source_analysis);

#endif
