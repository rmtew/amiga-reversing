#include "platform_file_internal.h"

PlatformResolvedIndirectKind platform_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  switch (section_analysis_context_backend_kind(ctx)) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_resolve_indirect_control(ctx, section_analysis, offset, instruction, out_info);
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return platform_atari_st_resolve_indirect_control(ctx, section_analysis, offset, instruction, out_info);
  default:
    return PLATFORM_RESOLVED_INDIRECT_NONE;
  }
}

int platform_collect_recovered_platform_facts(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis) {
  switch (section_analysis_context_backend_kind(ctx)) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_collect_recovered_platform_facts(ctx, section_analysis);
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return platform_atari_st_collect_recovered_platform_facts(ctx, section_analysis);
  default:
    return 0;
  }
}

int platform_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  switch (section_analysis_context_backend_kind(ctx)) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_resolve_additional_indirect_note(ctx, section_analysis, offset, instruction, out_info);
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return platform_atari_st_resolve_additional_indirect_note(ctx, section_analysis, offset, instruction, out_info);
  default:
    return 0;
  }
}

int platform_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction) {
  switch (section_analysis_context_backend_kind(ctx)) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_annotate_instruction_symbol_refs(ctx, section_analysis, offset, instruction);
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return platform_atari_st_annotate_instruction_symbol_refs(ctx, section_analysis, offset, instruction);
  default:
    return 0;
  }
}
