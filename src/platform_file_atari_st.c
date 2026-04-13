#include "platform_file_internal.h"

static int atari_st_find_previous_instruction_ending_at(const SectionAnalysisContext *ctx, uint32_t offset,
    uint32_t *out_prev_offset, SectionDecodeResult *out_prev_decode);

static const AtariStOsCallInfo *resolve_atari_st_trap_call_after_stack_seed(const SectionAnalysisContext *ctx,
    uint32_t next_offset, uint16_t opcode) {
  SectionDecodeResult next_decode;
  const M68kInstructionIR *trap_instruction;
  if (!section_analysis_context_probe_decode(ctx, next_offset, &next_decode)) return NULL;
  trap_instruction = &next_decode.instruction;
  if (!instruction_mnemonic_is(trap_instruction, "trap")) return NULL;
  if (trap_instruction->operand_count != 1U) return NULL;
  return atari_st_os_find_call((uint8_t)(trap_instruction->operands[0].value.value & 0xFFU), opcode);
}

static int atari_st_instruction_trap_vector(const M68kInstructionIR *instruction, uint8_t *out_vector) {
  if (out_vector != NULL) *out_vector = 0U;
  if (instruction == NULL || !instruction_mnemonic_is(instruction, "trap")) return 0;
  if (instruction->operand_count != 1U) return 0;
  if (out_vector != NULL) *out_vector = (uint8_t)(instruction->operands[0].value.value & 0xFFU);
  return 1;
}

static int atari_st_instruction_stack_adjust_delta(const M68kInstructionIR *instruction, int32_t *out_delta) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  int16_t disp16;
  uint8_t base_reg;
  int32_t value;
  if (out_delta != NULL) *out_delta = 0;
  if (instruction == NULL || out_delta == NULL) return 0;
  if ((instruction_mnemonic_is(instruction, "addq") || instruction_mnemonic_is(instruction, "add") ||
       instruction_mnemonic_is(instruction, "addi") || instruction_mnemonic_is(instruction, "adda")) &&
      instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    if (!(dst->kind == M68K_ASM_OPERAND_AN && dst->value.reg == 7U) &&
        !(dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 1U && dst->value.ea_reg == 7U)) return 0;
    if (src->kind != M68K_ASM_OPERAND_IMM &&
        (src->kind != M68K_ASM_OPERAND_EA || src->value.ea_mode != 7U || src->value.ea_reg != 4U)) {
      return 0;
    }
    value = (instruction_mnemonic_is(instruction, "addq") != 0)
      ? (int32_t)m68k_sign_extend32(src->value.value, 3U)
      : (int32_t)m68k_sign_extend32(src->value.value,
          instruction->size_suffix == 'w' ? 16U : 32U);
    *out_delta = value;
    return 1;
  }
  if ((instruction_mnemonic_is(instruction, "subq") || instruction_mnemonic_is(instruction, "sub") ||
       instruction_mnemonic_is(instruction, "subi") || instruction_mnemonic_is(instruction, "suba")) &&
      instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    if (!(dst->kind == M68K_ASM_OPERAND_AN && dst->value.reg == 7U) &&
        !(dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 1U && dst->value.ea_reg == 7U)) return 0;
    if (src->kind != M68K_ASM_OPERAND_IMM &&
        (src->kind != M68K_ASM_OPERAND_EA || src->value.ea_mode != 7U || src->value.ea_reg != 4U)) {
      return 0;
    }
    value = (instruction_mnemonic_is(instruction, "subq") != 0)
      ? (int32_t)m68k_sign_extend32(src->value.value, 3U)
      : (int32_t)m68k_sign_extend32(src->value.value,
          instruction->size_suffix == 'w' ? 16U : 32U);
    *out_delta = -value;
    return 1;
  }
  if (instruction_mnemonic_is(instruction, "lea") && instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    if (!(dst->kind == M68K_ASM_OPERAND_AN && dst->value.reg == 7U) &&
        !(dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 1U && dst->value.ea_reg == 7U)) return 0;
    if (!operand_is_indirect_disp_an(src, &base_reg, &disp16)) return 0;
    if (base_reg != 7U) return 0;
    *out_delta = (int32_t)disp16;
    return 1;
  }
  return 0;
}

static int atari_st_extract_stack_word_write(const M68kInstructionIR *instruction, uint8_t *out_has_value,
    uint16_t *out_value, uint32_t *out_write_disp, uint32_t *out_write_size, uint8_t *out_consumes_depth) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  if (out_has_value != NULL) *out_has_value = 0U;
  if (out_value != NULL) *out_value = 0U;
  if (out_write_disp != NULL) *out_write_disp = 0U;
  if (out_write_size != NULL) *out_write_size = 0U;
  if (out_consumes_depth != NULL) *out_consumes_depth = 0U;
  if (instruction == NULL) return 0;
  if (instruction->operand_count != 2U) return 0;
  src = &instruction->operands[0];
  dst = &instruction->operands[1];
  if ((instruction_mnemonic_is(instruction, "move") || instruction_mnemonic_is(instruction, "clr")) &&
      instruction->size_suffix == 'w') {
    if ((dst->kind == M68K_ASM_OPERAND_PREDEC && dst->value.reg == 7U) ||
        (dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 4U && dst->value.ea_reg == 7U)) {
      if (out_write_disp != NULL) *out_write_disp = 0U;
      if (out_write_size != NULL) *out_write_size = 2U;
      if (out_consumes_depth != NULL) *out_consumes_depth = 1U;
      if (instruction_mnemonic_is(instruction, "clr")) {
        if (out_has_value != NULL) *out_has_value = 1U;
        if (out_value != NULL) *out_value = 0U;
        return 1;
      }
      if (src->kind == M68K_ASM_OPERAND_IMM ||
          (src->kind == M68K_ASM_OPERAND_EA && src->value.ea_mode == 7U && src->value.ea_reg == 4U)) {
        if (out_has_value != NULL) *out_has_value = 1U;
        if (out_value != NULL) *out_value = (uint16_t)(src->value.value & 0xFFFFU);
      }
      return 1;
    }
    if ((dst->kind == M68K_ASM_OPERAND_IND && dst->value.reg == 7U) ||
        (dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 2U && dst->value.ea_reg == 7U)) {
      if (out_write_disp != NULL) *out_write_disp = 0U;
      if (out_write_size != NULL) *out_write_size = 2U;
      if (out_consumes_depth != NULL) *out_consumes_depth = 0U;
      if (instruction_mnemonic_is(instruction, "clr")) {
        if (out_has_value != NULL) *out_has_value = 1U;
        if (out_value != NULL) *out_value = 0U;
        return 1;
      }
      if (src->kind == M68K_ASM_OPERAND_IMM ||
          (src->kind == M68K_ASM_OPERAND_EA && src->value.ea_mode == 7U && src->value.ea_reg == 4U)) {
        if (out_has_value != NULL) *out_has_value = 1U;
        if (out_value != NULL) *out_value = (uint16_t)(src->value.value & 0xFFFFU);
      }
      return 1;
    }
  }
  return 0;
}

static const AtariStOsCallInfo *resolve_atari_st_trap_call_from_stack(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t trap_offset) {
  size_t block_index;
  uint32_t cursor = trap_offset;
  uint32_t block_start = 0U;
  uint8_t trap_vector;
  int32_t target_disp = 0;
  SectionDecodeResult trap_decode;
  if (ctx == NULL || section_analysis == NULL) return NULL;
  if (!section_analysis_context_probe_decode(ctx, trap_offset, &trap_decode)) return NULL;
  if (!atari_st_instruction_trap_vector(&trap_decode.instruction, &trap_vector)) return NULL;
  block_index = section_analysis_find_block_index_containing(section_analysis, trap_offset);
  if (block_index < section_analysis->block_count) {
    block_start = section_analysis->blocks[block_index].start_offset;
  } else {
    block_start = trap_offset > 32U ? trap_offset - 32U : 0U;
  }
  while (cursor > block_start) {
    SectionDecodeResult prev_decode;
    uint32_t prev_offset, write_disp, write_size;
    int32_t stack_delta;
    uint8_t has_value, consumes_depth;
    uint16_t value;
    if (!atari_st_find_previous_instruction_ending_at(ctx, cursor, &prev_offset, &prev_decode)) break;
    if (atari_st_instruction_stack_adjust_delta(&prev_decode.instruction, &stack_delta)) {
      target_disp += stack_delta;
      if (target_disp < 0) return NULL;
      cursor = prev_offset;
      continue;
    }
    if (atari_st_extract_stack_word_write(&prev_decode.instruction, &has_value, &value, &write_disp, &write_size,
          &consumes_depth)) {
      if (target_disp >= (int32_t)write_disp && target_disp < (int32_t)(write_disp + write_size)) {
        const AtariStOsCallInfo *call_info;
        if (!has_value) return NULL;
        call_info = atari_st_os_find_call(trap_vector, value);
        return call_info;
      }
      if (consumes_depth != 0U) {
        target_disp -= (int32_t)write_size;
        if (target_disp < 0) target_disp = 0;
      }
      cursor = prev_offset;
      continue;
    }
    cursor = prev_offset;
  }
  return NULL;
}

static const AtariStOsCallInfo *resolve_atari_st_trap_seed_call(const SectionAnalysisContext *ctx, uint32_t offset,
    const M68kInstructionIR *instruction, uint32_t *out_trap_offset) {
  const M68kSection *section = section_analysis_context_section(ctx);
  const M68kOperandIR *opcode_operand;
  const M68kOperandIR *dst_operand;
  uint32_t next_offset;
  uint16_t opcode;
  if (ctx == NULL || instruction == NULL || section == NULL) return NULL;
  if (!instruction_mnemonic_is(instruction, "move")) return NULL;
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

static int atari_st_find_previous_instruction_ending_at(const SectionAnalysisContext *ctx, uint32_t offset,
    uint32_t *out_prev_offset, SectionDecodeResult *out_prev_decode) {
  uint32_t start = offset > 12U ? (offset - 12U) : 0U;
  uint32_t candidate;
  if (ctx == NULL || out_prev_offset == NULL || out_prev_decode == NULL) return 0;
  for (candidate = start; candidate < offset; ++candidate) {
    SectionDecodeResult decode;
    if (!section_analysis_context_probe_decode(ctx, candidate, &decode)) continue;
    if (candidate + (uint32_t)decode.instruction.byte_count != offset) continue;
    *out_prev_offset = candidate;
    *out_prev_decode = decode;
    return 1;
  }
  return 0;
}

static int atari_st_instruction_is_stack_cleanup_candidate(const M68kInstructionIR *instruction, uint16_t cleanup_bytes) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  int32_t disp;
  if (instruction == NULL) return 0;
  if (cleanup_bytes == 0U) return 0;
  if ((instruction_mnemonic_is(instruction, "addq") || instruction_mnemonic_is(instruction, "add") ||
       instruction_mnemonic_is(instruction, "addi") || instruction_mnemonic_is(instruction, "adda")) &&
      instruction->operand_count == 2U) {
    dst = &instruction->operands[1];
    return (dst->kind == M68K_ASM_OPERAND_AN && dst->value.reg == 7U) ||
      (dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 1U && dst->value.ea_reg == 7U) ||
      (dst->kind == M68K_ASM_OPERAND_POSTINC && dst->value.reg == 7U);
  }
  if (instruction_mnemonic_is(instruction, "lea") && instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    {
      uint8_t base_reg;
      int16_t disp16;
    if (dst->kind != M68K_ASM_OPERAND_AN || dst->value.reg != 7U) return 0;
      if (!operand_is_indirect_disp_an(src, &base_reg, &disp16)) return 0;
      if (base_reg != 7U) return 0;
      disp = disp16;
      return (uint16_t)(disp & 0xFFFF) == cleanup_bytes;
    }
  }
  return 0;
}

int platform_atari_st_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  (void)ctx;
  (void)section_analysis;
  (void)offset;
  (void)instruction;
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  return PLATFORM_RESOLVED_INDIRECT_NONE;
}

int platform_atari_st_collect_recovered_platform_facts(const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *section_analysis) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t offset;
  if (ctx == NULL || section == NULL || section_analysis == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_ATARI_ST) {
    return 0;
  }
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  for (offset = 0U; offset < section->data_size; ++offset) {
    SectionDecodeResult decode;
    SectionDecodeResult cleanup_decode;
    const AtariStOsCallInfo *call_info;
    uint32_t cleanup_offset = UINT32_MAX;
    if (!section_analysis_context_probe_decode(ctx, offset, &decode)) continue;
    if (!instruction_mnemonic_is(&decode.instruction, "trap")) continue;
    call_info = resolve_atari_st_trap_call_from_stack(ctx, section_analysis, offset);
    if (call_info == NULL) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis,
          offset, 0U, NULL, M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL,
          call_info->family_name, call_info->symbol_name, 0U, INT16_MIN, INT16_MIN,
          call_info->stack_cleanup_known, call_info->stack_cleanup_bytes, call_info->return_kind) != 0) {
      return -1;
    }
    if (!call_info->stack_cleanup_known) continue;
    cleanup_offset = offset + (uint32_t)decode.instruction.byte_count;
    if (cleanup_offset >= section->data_size) continue;
    if (!section_analysis_context_probe_decode(ctx, cleanup_offset, &cleanup_decode)) continue;
    if (!atari_st_instruction_is_stack_cleanup_candidate(&cleanup_decode.instruction,
          call_info->stack_cleanup_bytes)) {
      continue;
    }
    if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis,
          cleanup_offset, 1U, NULL, M68K_PLATFORM_CALL_NOTE_STACK_CLEANUP,
          call_info->family_name, call_info->symbol_name, 0U, INT16_MIN, INT16_MIN,
          call_info->stack_cleanup_known, call_info->stack_cleanup_bytes, call_info->return_kind) != 0) {
      return -1;
    }
  }
  return 0;
}

int platform_atari_st_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  const M68kRecoveredPlatformCallIR *recovered;
  SectionDecodeResult prev_decode;
  uint32_t prev_offset = UINT32_MAX;
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  if (ctx == NULL || section_analysis == NULL || instruction == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_ATARI_ST) {
    return 0;
  }
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  if (instruction_mnemonic_is(instruction, "trap")) {
    recovered = find_any_recovered_platform_call(section_analysis, offset);
    if (recovered == NULL || recovered->kind != 0U ||
        recovered->note_kind != M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL) {
      return 0;
    }
    load_recovered_platform_call_info(recovered, out_info);
    return 1;
  }
  (void)prev_decode;
  (void)prev_offset;
  (void)recovered;
  return 0;
}

int platform_atari_st_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction) {
  const M68kRecoveredPlatformCallIR *recovered;
  uint32_t trap_offset = UINT32_MAX;
  const AtariStOsCallInfo *call_info;
  if (ctx == NULL || instruction == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_ATARI_ST) {
    return 0;
  }
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  call_info = resolve_atari_st_trap_seed_call(ctx, offset, instruction, &trap_offset);
  if (call_info == NULL) return 0;
  recovered = find_any_recovered_platform_call(section_analysis, trap_offset);
  if (recovered == NULL || recovered->note_kind != M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL ||
      recovered->note_symbol_name == NULL || recovered->note_symbol_name[0] == '\0') {
    return 0;
  }
  instruction->operands[0].symbol_ref.has_name = 1U;
  instruction->operands[0].symbol_ref.name_is_generated = 0U;
  instruction->operands[0].symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  instruction->operands[0].symbol_ref.addend = 0;
  snprintf(instruction->operands[0].symbol_ref.name, sizeof(instruction->operands[0].symbol_ref.name), "%s",
      recovered->note_symbol_name);
  return 1;
}
