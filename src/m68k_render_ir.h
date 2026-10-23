/* Ordered render-preview IR for facts_v2 analysis. */
#ifndef M68K_RENDER_IR_H
#define M68K_RENDER_IR_H

#include "m68k_decode_ir.h"
#include "m68k_fact_ir.h"
#include "m68k_render_plan.h"
#include "m68k_source_export.h"
#include "m68k_memory_layout.h"

#include <stddef.h>
#include <stdint.h>

typedef struct Arena Arena;
typedef struct M68kAnalysisPolicy M68kAnalysisPolicy;
typedef struct M68kRenderEvidenceIR M68kRenderEvidenceIR;
typedef struct M68kSourceAnalysisIR M68kSourceAnalysisIR;
typedef struct M68kRenderIRPreview M68kRenderIRPreview;

typedef int (*M68kRenderIRPreparedSink)(M68kRenderIRPreview *preview, void *user);

struct M68kRenderIRPreview {
  uint32_t statement_count;
  uint32_t label_statement_count;
  uint32_t instruction_statement_count;
  uint32_t data_statement_count;
  double lookup_seconds;
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
  uint32_t asm_source_lossy_numeric_hunk_relocations;
  uint32_t asm_source_instruction_render_failures;
  uint32_t asm_source_instruction_byte_mismatches;
  uint32_t asm_source_instruction_relocation_failures;
  M68kSourceExportFailureKind asm_source_first_failure_kind;
  uint32_t asm_source_first_failure_section;
  uint32_t asm_source_first_failure_offset;
  uint32_t asm_source_first_failure_aux_offset;
  char *asm_source_text;
  size_t asm_source_text_capacity;
  /* Immutable rendering decisions, separate from temporary emitted rows. */
  M68kRenderPlan asm_source_plan;
  M68kRenderPlan asm_source_rows;
  M68kRenderPlanRowBuilder asm_source_row_builder;
  M68kRenderPlanRow transient_row;
  M68kRenderEvidenceIR *render_evidence;
  Arena *scratch_arena;
  uint32_t asm_source_body_start_byte;
  uint8_t platform_backend_kind;
  const M68kAnalysisPolicy *analysis_policy;
  uint8_t memory_layout_enabled;
  M68kResolvedMemoryLayout memory_layout;
  M68kRenderTransientRowSink transient_row_sink;
  void *transient_row_sink_user;
  M68kRenderIRPreparedSink prepared_sink;
  void *prepared_sink_user;
  uint8_t transient_row_live;
  uint8_t precomputing_planned_evidence;
  uint8_t planned_evidence_precomputed;
  uint8_t collect_asm_source_text;
  uint8_t collect_asm_source_hash;
  uint8_t asm_source_allocation_failed;
  uint32_t planned_evidence_next_order;
};

void m68k_render_ir_preview_init(M68kRenderIRPreview *preview);
void m68k_render_ir_preview_destroy(M68kRenderIRPreview *preview);
void m68k_render_ir_preview_set_transient_row_sink(M68kRenderIRPreview *preview,
  M68kRenderTransientRowSink sink, void *user);
void m68k_render_ir_preview_set_prepared_sink(M68kRenderIRPreview *preview,
  M68kRenderIRPreparedSink sink, void *user);
int candidate_calls_a6_lvo(const M68kDecodeCandidate *candidate, int16_t *out_lvo);

#endif
