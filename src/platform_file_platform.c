#include "platform_file_internal.h"

PlatformResolvedIndirectInfo platform_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  switch (section_analysis_context_backend_kind(ctx)) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_resolve_indirect_control(ctx, section_analysis, offset, instruction);
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return platform_atari_st_resolve_indirect_control(ctx, section_analysis, offset, instruction);
  default:
    return platform_resolved_indirect_info_none();
  }
}

PlatformResolvedIndirectInfo platform_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  switch (section_analysis_context_backend_kind(ctx)) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_resolve_additional_indirect_note(ctx, section_analysis, offset, instruction);
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return platform_atari_st_resolve_additional_indirect_note(ctx, section_analysis, offset, instruction);
  default:
    return platform_resolved_indirect_info_none();
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

int platform_resolve_inferred_label(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, char *buf, size_t buf_size) {
  if (buf != NULL && buf_size != 0U) buf[0] = '\0';
  switch (section_analysis_context_backend_kind(ctx)) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_resolve_inferred_label(ctx, section_analysis, offset, buf, buf_size);
  default:
    return 0;
  }
}

int platform_format_instruction_comment(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    char *buf, size_t buf_size) {
  if (buf != NULL && buf_size != 0U) buf[0] = '\0';
  switch (section_analysis_context_backend_kind(ctx)) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_format_instruction_comment(ctx, section_analysis, offset, instruction, buf, buf_size);
  default:
    return 0;
  }
}

int platform_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref) {
  switch (section_analysis_context_backend_kind(ctx)) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_resolve_app_base_slot_symbol_ref(ctx, section_analysis, displacement, treat_as_value,
      out_symbol_ref);
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return platform_atari_st_resolve_app_base_slot_symbol_ref(ctx, section_analysis, displacement, treat_as_value,
      out_symbol_ref);
  default:
    if (out_symbol_ref != NULL) m68k_ir_symbol_ref_init(out_symbol_ref);
    return 0;
  }
}

int platform_format_global_base_slot_label(uint8_t backend_kind, size_t section_index, char width_suffix,
    const char *base_name, char *buf, size_t buf_size) {
  if (buf != NULL && buf_size != 0U) buf[0] = '\0';
  switch (backend_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return platform_amiga_format_global_base_slot_label(section_index, width_suffix, base_name, buf, buf_size);
  default:
    return 0;
  }
}
