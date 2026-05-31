#include "platform_file_internal.h"

static const AtariStOsCallInfo *resolve_atari_st_trap_call_after_stack_seed(const SectionAnalysisContext *ctx,
    uint32_t next_offset, uint16_t opcode) {
  SectionDecodeResult next_decode;
  const M68kInstructionIR *trap_instruction;
  if (!section_analysis_context_probe_decode(ctx, next_offset, &next_decode)) return NULL;
  trap_instruction = &next_decode.instruction;
  if (trap_instruction->mnemonic_id != M68K_ASM_MNEMONIC_TRAP) return NULL;
  if (trap_instruction->operand_count != 1U) return NULL;
  return atari_st_os_find_call((uint8_t)(trap_instruction->operands[0].value.value & 0xFFU), opcode);
}

static const AtariStOsCallInfo *resolve_atari_st_trap_seed_call(const SectionAnalysisContext *ctx, uint32_t offset,
    const M68kInstructionIR *instruction, uint32_t *out_trap_offset) {
  const M68kSection *section = section_analysis_context_section(ctx);
  const M68kOperandIR *opcode_operand;
  const M68kOperandIR *dst_operand;
  uint32_t next_offset;
  uint16_t opcode;
  if (ctx == NULL || section == NULL) return NULL;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE) return NULL;
  if (instruction->operand_count != 2U) return NULL;
  opcode_operand = &instruction->operands[0];
  dst_operand = &instruction->operands[1];
  if (opcode_operand->kind != M68K_ASM_OPERAND_IMM &&
      (opcode_operand->kind != M68K_ASM_OPERAND_EA ||
       opcode_operand->value.ea_mode != 7U || opcode_operand->value.ea_reg != 4U)) {
    return NULL;
  }
  if (!((dst_operand->kind == M68K_ASM_OPERAND_PREDEC && dst_operand->value.reg == 7U) ||
        (dst_operand->kind == M68K_ASM_OPERAND_IND && dst_operand->value.reg == 7U) ||
        (dst_operand->kind == M68K_ASM_OPERAND_EA && dst_operand->value.ea_mode == 4U && dst_operand->value.ea_reg == 7U) ||
        (dst_operand->kind == M68K_ASM_OPERAND_EA && dst_operand->value.ea_mode == 2U && dst_operand->value.ea_reg == 7U))) {
    return NULL;
  }
  opcode = (uint16_t)(opcode_operand->value.value & 0xFFFFU);
  next_offset = offset + (uint32_t)instruction->byte_count;
  if (next_offset >= section->data_size) return NULL;
  if (out_trap_offset != NULL) *out_trap_offset = next_offset;
  return resolve_atari_st_trap_call_after_stack_seed(ctx, next_offset, opcode);
}

PlatformResolvedIndirectInfo platform_atari_st_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  (void)ctx;
  (void)section_analysis;
  (void)offset;
  (void)instruction;
  return platform_resolved_indirect_info_none();
}

PlatformResolvedIndirectInfo platform_atari_st_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  PlatformResolvedIndirectInfo info;
  const M68kRecoveredPlatformCallIR *recovered;
  SectionDecodeResult prev_decode;
  uint32_t prev_offset = UINT32_MAX;
  info = platform_resolved_indirect_info_none();
  if (ctx == NULL || section_analysis == NULL) return info;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_ATARI_ST) {
    return info;
  }
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return info;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_TRAP) {
    recovered = find_any_recovered_platform_call(section_analysis, offset);
    if (recovered == NULL || recovered->kind != 0U ||
        recovered->note_kind != M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL) {
      return info;
    }
    load_recovered_platform_call_info(recovered, &info);
    return info;
  }
  (void)prev_decode;
  (void)prev_offset;
  (void)recovered;
  return info;
}

int platform_atari_st_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction) {
  const M68kRecoveredPlatformCallIR *recovered;
  uint32_t trap_offset = UINT32_MAX;
  const AtariStOsCallInfo *call_info;
  if (ctx == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_ATARI_ST) {
    return 0;
  }
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  call_info = resolve_atari_st_trap_seed_call(ctx, offset, instruction, &trap_offset);
  if (call_info == NULL) return 0;
  recovered = find_any_recovered_platform_call(section_analysis, trap_offset);
  {
    const char *note_symbol_name = recovered != NULL
      ? m68k_platform_name_ref_display_text(&recovered->note_symbol_ref, recovered->note_symbol_name)
      : NULL;
    if (recovered == NULL || recovered->note_kind != M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL ||
        note_symbol_name == NULL || note_symbol_name[0] == '\0') {
      return 0;
    }
    instruction->operands[0].symbol_ref.has_name = 1U;
    instruction->operands[0].symbol_ref.name_is_generated = 0U;
    instruction->operands[0].symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_ATARI_ST;
    instruction->operands[0].symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    instruction->operands[0].symbol_ref.addend = 0;
    snprintf(instruction->operands[0].symbol_ref.name, sizeof(instruction->operands[0].symbol_ref.name), "%s",
      note_symbol_name);
    return 1;
  }
}

int platform_atari_st_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref) {
  (void)ctx;
  (void)section_analysis;
  (void)displacement;
  (void)treat_as_value;
  if (out_symbol_ref != NULL) m68k_ir_symbol_ref_init(out_symbol_ref);
  return 0;
}
