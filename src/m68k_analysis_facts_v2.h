#ifndef M68K_ANALYSIS_FACTS_V2_H
#define M68K_ANALYSIS_FACTS_V2_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"
#include "m68k_object.h"
#include "m68k_render_plan.h"

#include <stdint.h>

#define M68K_FACTS_V2_RELOCATION_FAILURE_NONE 0U
#define M68K_FACTS_V2_RELOCATION_FAILURE_INVALID_FIXUP 1U
#define M68K_FACTS_V2_RELOCATION_FAILURE_BAD_WIDTH 2U
#define M68K_FACTS_V2_RELOCATION_FAILURE_PAYLOAD_OUT_OF_DATA 3U
#define M68K_FACTS_V2_RELOCATION_FAILURE_UNSUPPORTED_KIND 4U
#define M68K_FACTS_V2_RELOCATION_FAILURE_TARGET_OUT_OF_RANGE 5U
#define M68K_FACTS_V2_RELOCATION_ANCHOR_NONE 0U
#define M68K_FACTS_V2_RELOCATION_ANCHOR_POSITIVE 1U
#define M68K_FACTS_V2_RELOCATION_ANCHOR_NEGATIVE 2U
#define M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_NONE 0U
#define M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_INSTRUCTION_BYTES 1U
#define M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_DATA_PAYLOAD 2U
#define M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_UNKNOWN 3U
#define M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_BASE_REGISTER 4U
#define M68K_FACTS_V2_CODE_START_REASON_UNKNOWN 0U
#define M68K_FACTS_V2_CODE_START_REASON_SECTION_ENTRY 1U
#define M68K_FACTS_V2_CODE_START_REASON_POLICY_ENTRY_OFFSET 2U
#define M68K_FACTS_V2_CODE_START_REASON_POLICY_ENTRY_POINT 3U
#define M68K_FACTS_V2_CODE_START_REASON_CONTROL_TARGET 4U
#define M68K_FACTS_V2_CODE_START_REASON_FALLTHROUGH 5U
#define M68K_FACTS_V2_CODE_START_REASON_INLINE_RESUME 6U
#define M68K_FACTS_V2_CODE_START_REASON_RUNTIME_VIEW_ENTRY 7U

typedef struct M68kFactsV2Profile {
  double decode_seconds;
  double seed_seconds;
  double fixed_point_seconds;
  double fixed_point_reachable_seconds;
  double fixed_point_reachable_decode_seconds;
  double fixed_point_reachable_validate_seconds;
  double fixed_point_reachable_accept_seconds;
  double fixed_point_reachable_target_seconds;
  double fixed_point_reachable_relocation_seconds;
  double fixed_point_reachable_fallthrough_seconds;
  double fixed_point_index_seconds;
  double fixed_point_required_label_conflict_seconds;
  double fixed_point_opcode_relocation_conflict_seconds;
  double fixed_point_rebuild_accepted_seconds;
  double fixed_point_relocation_anchor_seconds;
  double fixed_point_materialize_labels_seconds;
  double fixed_point_runtime_address_ref_seconds;
  double fixed_point_required_label_materialize_seconds;
  double fixed_point_data_span_seconds;
  double fixed_point_invariant_seconds;
  double render_ir_seconds;
  double render_ir_lookup_seconds;
  double render_ir_platform_pass_seconds;
  double render_ir_platform_base_slot_seconds;
  double render_ir_platform_call_summary_seconds;
  double render_ir_platform_typed_ref_seconds;
  double render_ir_platform_call_comment_seconds;
  double render_ir_platform_app_slot_seconds;
  double render_ir_platform_runtime_data_seconds;
  double render_ir_platform_hardware_data_seconds;
  double render_ir_platform_generic_data_seconds;
  double render_ir_header_seconds;
  double render_ir_walk_seconds;
  double render_ir_footer_seconds;
  double source_render_seconds;
  uint32_t decoded_candidates;
  uint32_t accepted_instructions;
  uint32_t data_spans;
  uint32_t labels_created;
  uint32_t labels_referenced;
  uint32_t unresolved_labels;
  uint32_t interior_conflicts;
  uint32_t interior_conflicts_resolved_by_demote;
  uint32_t interior_conflicts_unresolved;
  uint32_t relocation_failures;
  uint32_t first_relocation_failure_reason;
  uint32_t first_relocation_failure_section;
  uint32_t first_relocation_failure_offset;
  uint32_t first_relocation_failure_target_section;
  uint32_t first_relocation_failure_width;
  uint32_t first_relocation_failure_raw_value;
  int64_t first_relocation_failure_computed_target;
  uint32_t relocation_anchors;
  uint32_t first_relocation_anchor_kind;
  uint32_t first_relocation_anchor_section;
  uint32_t first_relocation_anchor_offset;
  uint32_t first_relocation_anchor_target_section;
  uint32_t first_relocation_anchor_width;
  uint32_t first_relocation_anchor_platform_record_kind;
  uint32_t first_relocation_anchor_raw_value;
  int64_t first_relocation_anchor_addend;
  uint32_t relocation_anchor_instruction_bytes;
  uint32_t relocation_anchor_data_payloads;
  uint32_t relocation_anchor_unknown_contexts;
  uint32_t unassemblable_hunk_data_relocations;
  uint32_t unassemblable_hunk_base_register_relocations;
  uint32_t first_relocation_anchor_context;
  uint32_t first_relocation_anchor_instruction_offset;
  uint32_t code_start_facts;
  uint32_t code_start_section_entries;
  uint32_t code_start_policy_entry_offsets;
  uint32_t code_start_policy_entry_points;
  uint32_t code_start_control_targets;
  uint32_t code_start_fallthroughs;
  uint32_t code_start_inline_resumes;
  uint32_t runtime_address_ranges;
  uint32_t runtime_address_range_conflicts;
  uint32_t runtime_address_view_starts;
  uint32_t required_instruction_failures;
  uint32_t unsupported_instruction_demotes;
  uint32_t first_required_instruction_failure_section;
  uint32_t first_required_instruction_failure_offset;
  uint32_t first_required_instruction_failure_reason;
  uint32_t first_required_instruction_failure_source_section;
  uint32_t first_required_instruction_failure_source_offset;
  uint32_t first_unsupported_instruction_demote_section;
  uint32_t first_unsupported_instruction_demote_offset;
  uint32_t first_unsupported_instruction_demote_reason;
  uint32_t first_unsupported_instruction_demote_source_section;
  uint32_t first_unsupported_instruction_demote_source_offset;
  uint32_t opcode_relocation_conflicts_resolved_by_demote;
  uint32_t first_opcode_relocation_conflict_section;
  uint32_t first_opcode_relocation_conflict_offset;
  uint32_t first_opcode_relocation_conflict_aux_offset;
  uint32_t queue_iterations;
  uint32_t render_ir_statements;
  uint32_t render_ir_labels;
  uint32_t render_ir_instructions;
  uint32_t render_ir_data_spans;
  uint64_t render_ir_hash;
  uint32_t preview_source_enabled;
  uint32_t preview_source_bytes;
  uint64_t preview_source_hash;
  uint32_t asm_source_enabled;
  uint32_t asm_source_refused;
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
  uint32_t asm_source_relocation_anchor_refusals;
  uint32_t asm_source_unassemblable_hunk_data_relocation_refusals;
  uint32_t asm_source_unassemblable_hunk_base_register_relocation_refusals;
  uint32_t asm_source_first_failure_kind;
  uint32_t asm_source_first_failure_section;
  uint32_t asm_source_first_failure_offset;
  uint32_t asm_source_first_failure_aux_offset;
  uint64_t asm_source_hash;
} M68kFactsV2Profile;

void m68k_facts_v2_profile_init(M68kFactsV2Profile *profile);
int m68k_facts_v2_collect_profile(const M68kObject *object, const M68kAnalysisPolicy *policy,
  M68kFactsV2Profile *out_profile, M68kDiagSink diagnostics);
int m68k_facts_v2_collect_direct_rebuild_profile(const M68kObject *object, const M68kAnalysisPolicy *policy,
  M68kFactsV2Profile *out_profile, M68kDiagSink diagnostics);
int m68k_facts_v2_collect_asm_source_profile(const M68kObject *object, const M68kAnalysisPolicy *policy,
  M68kFactsV2Profile *out_profile, M68kDiagSink diagnostics);
int m68k_facts_v2_render_asm_source_alloc(const M68kObject *object, const M68kAnalysisPolicy *policy,
  char **out_source, M68kFactsV2Profile *out_profile, M68kDiagSink diagnostics);
int m68k_facts_v2_render_asm_source_profile_alloc(const M68kObject *object, const M68kAnalysisPolicy *policy,
  char **out_source, M68kFactsV2Profile *out_profile, uint8_t fail_on_refused, M68kDiagSink diagnostics);
int m68k_facts_v2_render_asm_source_analysis_profile_alloc(const M68kObject *object,
    const M68kAnalysisPolicy *policy, char **out_source, M68kFactsV2Profile *out_profile,
    M68kSourceAnalysisIR *out_source_analysis, uint8_t fail_on_refused, M68kDiagSink diagnostics);
int m68k_facts_v2_render_asm_source_plan_analysis_profile_alloc(const M68kObject *object,
    const M68kAnalysisPolicy *policy, char **out_source, M68kRenderPlan *out_source_plan,
    M68kFactsV2Profile *out_profile, M68kSourceAnalysisIR *out_source_analysis, uint8_t fail_on_refused,
    M68kDiagSink diagnostics);
int m68k_facts_v2_collect_source_analysis_profile(const M68kObject *object,
  const M68kAnalysisPolicy *policy, M68kFactsV2Profile *out_profile,
  M68kSourceAnalysisIR *out_source_analysis, M68kDiagSink diagnostics);
void m68k_facts_v2_free_text(char *text);

#endif
