#include "platform_common.h"

#include "m68k_decode_ir.h"
#include "m68k_parse_util.h"
#include "generated/atari_st_os_runtime.h"

#include <stdio.h>
#include <string.h>

void platform_facts_v2_resolved_call_init(PlatformFactsV2ResolvedCall *info) {
  if (info == NULL) return;
  memset(info, 0, sizeof(*info));
}

static int facts_v2_accepted_start_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    uint32_t offset) {
  return section != NULL && accepted_start != NULL && offset < section->size && accepted_start[offset] != 0U;
}

static int atari_operand_is_sp_address_reg(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_AN && operand->value.reg == 7U) ||
    (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 1U && operand->value.ea_reg == 7U);
}

static int atari_operand_is_immediate(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  return operand->kind == M68K_ASM_OPERAND_IMM ||
    (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U && operand->value.ea_reg == 4U);
}

static int atari_operand_is_indirect_disp_an(const M68kOperandIR *operand, uint8_t *out_reg,
    int16_t *out_displacement) {
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_EA ||
      operand->value.ea_mode != 5U || operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = operand->value.ea_reg;
  if (out_displacement != NULL) *out_displacement = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

static int atari_mnemonic_is_stack_add_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_ADDQ:
  case M68K_ASM_MNEMONIC_ADD:
  case M68K_ASM_MNEMONIC_ADDI:
  case M68K_ASM_MNEMONIC_ADDA:
    return 1;
  default:
    return 0;
  }
}

static int atari_mnemonic_is_stack_sub_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_SUBQ:
  case M68K_ASM_MNEMONIC_SUB:
  case M68K_ASM_MNEMONIC_SUBI:
  case M68K_ASM_MNEMONIC_SUBA:
    return 1;
  default:
    return 0;
  }
}

static int atari_instruction_trap_vector(const M68kInstructionIR *instruction, uint8_t *out_vector) {
  if (out_vector != NULL) *out_vector = 0U;
  if (instruction == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_TRAP ||
      instruction->operand_count != 1U) {
    return 0;
  }
  if (out_vector != NULL) *out_vector = (uint8_t)(instruction->operands[0].value.value & 0xFFU);
  return 1;
}

static int atari_instruction_stack_adjust_delta(const M68kInstructionIR *instruction, int32_t *out_delta) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  uint8_t base_reg;
  int16_t disp16;
  int32_t value;
  if (out_delta != NULL) *out_delta = 0;
  if (instruction == NULL || out_delta == NULL) return 0;
  if ((atari_mnemonic_is_stack_add_family(instruction->mnemonic_id) ||
       atari_mnemonic_is_stack_sub_family(instruction->mnemonic_id)) &&
      instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    if (!atari_operand_is_sp_address_reg(dst) || !atari_operand_is_immediate(src)) return 0;
    value = (instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDQ ||
             instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ)
      ? (int32_t)m68k_sign_extend32(src->value.value, 3U)
      : (int32_t)m68k_sign_extend32(src->value.value, instruction->size_suffix == 'w' ? 16U : 32U);
    *out_delta = atari_mnemonic_is_stack_sub_family(instruction->mnemonic_id) ? -value : value;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    if (!atari_operand_is_sp_address_reg(dst)) return 0;
    if (!atari_operand_is_indirect_disp_an(src, &base_reg, &disp16) || base_reg != 7U) return 0;
    *out_delta = (int32_t)disp16;
    return 1;
  }
  return 0;
}

static int atari_extract_stack_word_write(const M68kInstructionIR *instruction, uint8_t *out_has_value,
    uint16_t *out_value, uint32_t *out_write_disp, uint32_t *out_write_size, uint8_t *out_consumes_depth) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  if (out_has_value != NULL) *out_has_value = 0U;
  if (out_value != NULL) *out_value = 0U;
  if (out_write_disp != NULL) *out_write_disp = 0U;
  if (out_write_size != NULL) *out_write_size = 0U;
  if (out_consumes_depth != NULL) *out_consumes_depth = 0U;
  if (instruction == NULL || instruction->operand_count != 2U || instruction->size_suffix != 'w')
    return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_CLR) {
    return 0;
  }
  src = &instruction->operands[0];
  dst = &instruction->operands[1];
  if ((dst->kind == M68K_ASM_OPERAND_PREDEC && dst->value.reg == 7U) ||
      (dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 4U && dst->value.ea_reg == 7U)) {
    if (out_write_size != NULL) *out_write_size = 2U;
    if (out_consumes_depth != NULL) *out_consumes_depth = 1U;
  } else if ((dst->kind == M68K_ASM_OPERAND_IND && dst->value.reg == 7U) ||
      (dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 2U && dst->value.ea_reg == 7U)) {
    if (out_write_size != NULL) *out_write_size = 2U;
  } else {
    return 0;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_CLR) {
    if (out_has_value != NULL) *out_has_value = 1U;
    return 1;
  }
  if (atari_operand_is_immediate(src)) {
    if (out_has_value != NULL) *out_has_value = 1U;
    if (out_value != NULL) *out_value = (uint16_t)(src->value.value & 0xFFFFU);
  }
  return 1;
}

static int atari_find_previous_accepted_instruction_ending_at(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t offset, uint32_t *out_prev_offset,
    M68kInstructionIR *out_instruction) {
  uint32_t start = offset > 12U ? offset - 12U : 0U;
  uint32_t probe;
  if (out_prev_offset != NULL) *out_prev_offset = 0U;
  if (out_instruction != NULL) memset(out_instruction, 0, sizeof(*out_instruction));
  if (section == NULL || accepted_start == NULL || out_prev_offset == NULL || out_instruction == NULL)
    return 0;
  for (probe = start; probe < offset; ++probe) {
    const M68kDecodeCandidate *candidate;
    if (!facts_v2_accepted_start_at(section, accepted_start, probe)) continue;
    candidate = m68k_decode_ir_find_candidate_at_offset(section, probe);
    if (candidate == NULL || candidate->byte_count == 0U || probe + candidate->byte_count != offset) continue;
    if (m68k_decode_candidate_to_instruction(candidate, out_instruction) != 0) continue;
    *out_prev_offset = probe;
    return 1;
  }
  return 0;
}

static int atari_instruction_is_stack_cleanup_candidate(const M68kInstructionIR *instruction,
    uint16_t cleanup_bytes) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  uint8_t base_reg;
  int16_t disp16;
  if (instruction == NULL || cleanup_bytes == 0U) return 0;
  if (atari_mnemonic_is_stack_add_family(instruction->mnemonic_id) && instruction->operand_count == 2U) {
    dst = &instruction->operands[1];
    return atari_operand_is_sp_address_reg(dst) ||
      (dst->kind == M68K_ASM_OPERAND_POSTINC && dst->value.reg == 7U);
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    if (!atari_operand_is_sp_address_reg(dst)) return 0;
    if (!atari_operand_is_indirect_disp_an(src, &base_reg, &disp16) || base_reg != 7U) return 0;
    return (uint16_t)(disp16 & 0xFFFF) == cleanup_bytes;
  }
  return 0;
}

static void atari_populate_resolved_call(const AtariStOsCallInfo *call_info, uint8_t kind, uint8_t note_kind,
    PlatformFactsV2ResolvedCall *out_info) {
  const char *family_name;
  const char *symbol_name;
  if (out_info == NULL) return;
  platform_facts_v2_resolved_call_init(out_info);
  if (call_info == NULL) return;
  family_name = atari_st_os_name(M68K_PLATFORM_NAME_FAMILY, call_info->family_id);
  symbol_name = atari_st_os_name(M68K_PLATFORM_NAME_SYMBOL, call_info->symbol_id);
  out_info->platform_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  out_info->kind = kind;
  out_info->note_kind = note_kind;
  out_info->note_stack_cleanup_known = call_info->stack_cleanup_known;
  out_info->note_stack_cleanup_bytes = call_info->stack_cleanup_bytes;
  out_info->note_return_kind = call_info->return_kind;
  if (family_name != NULL)
    snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", family_name);
  if (symbol_name != NULL)
    snprintf(out_info->note_symbol_name, sizeof(out_info->note_symbol_name), "%s", symbol_name);
}

static int atari_resolve_trap_call(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    uint32_t block_start, uint32_t trap_offset, PlatformFactsV2ResolvedCall *out_info) {
  const M68kDecodeCandidate *trap_candidate;
  M68kInstructionIR trap_instruction;
  uint8_t trap_vector = 0U;
  uint32_t cursor = trap_offset;
  int32_t target_disp = 0;
  if (out_info != NULL) platform_facts_v2_resolved_call_init(out_info);
  if (section == NULL || accepted_start == NULL ||
      !facts_v2_accepted_start_at(section, accepted_start, trap_offset)) {
    return 0;
  }
  trap_candidate = m68k_decode_ir_find_candidate_at_offset(section, trap_offset);
  if (trap_candidate == NULL || m68k_decode_candidate_to_instruction(trap_candidate, &trap_instruction) != 0)
    return 0;
  if (!atari_instruction_trap_vector(&trap_instruction, &trap_vector)) return 0;
  while (cursor > block_start) {
    M68kInstructionIR prev_instruction;
    uint32_t prev_offset;
    uint32_t write_disp, write_size;
    int32_t stack_delta;
    uint8_t has_value, consumes_depth;
    uint16_t value;
    if (!atari_find_previous_accepted_instruction_ending_at(section, accepted_start, cursor, &prev_offset,
        &prev_instruction)) {
      break;
    }
    if (atari_instruction_stack_adjust_delta(&prev_instruction, &stack_delta)) {
      target_disp += stack_delta;
      if (target_disp < 0) return 0;
      cursor = prev_offset;
      continue;
    }
    if (atari_extract_stack_word_write(&prev_instruction, &has_value, &value, &write_disp, &write_size,
        &consumes_depth)) {
      if (target_disp >= (int32_t)write_disp && target_disp < (int32_t)(write_disp + write_size)) {
        const AtariStOsCallInfo *call_info = has_value ? atari_st_os_find_call(trap_vector, value) : NULL;
        if (call_info == NULL) return 0;
        atari_populate_resolved_call(call_info, 0U, M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL, out_info);
        return 1;
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
  return 0;
}

static int atari_resolve_stack_cleanup_call(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    uint32_t block_start, uint32_t cleanup_offset, const M68kInstructionIR *cleanup_instruction,
    PlatformFactsV2ResolvedCall *out_info) {
  M68kInstructionIR prev_instruction;
  uint32_t prev_offset;
  PlatformFactsV2ResolvedCall trap_info;
  if (out_info != NULL) platform_facts_v2_resolved_call_init(out_info);
  if (section == NULL || accepted_start == NULL || cleanup_instruction == NULL) return 0;
  if (!atari_find_previous_accepted_instruction_ending_at(section, accepted_start, cleanup_offset,
      &prev_offset, &prev_instruction)) {
    return 0;
  }
  if (!atari_instruction_trap_vector(&prev_instruction, NULL)) return 0;
  if (!atari_resolve_trap_call(section, accepted_start, block_start, prev_offset, &trap_info)) return 0;
  if (!trap_info.note_stack_cleanup_known ||
      !atari_instruction_is_stack_cleanup_candidate(cleanup_instruction,
        trap_info.note_stack_cleanup_bytes)) {
    return 0;
  }
  if (out_info != NULL) {
    *out_info = trap_info;
    out_info->kind = 1U;
    out_info->note_kind = M68K_PLATFORM_CALL_NOTE_STACK_CLEANUP;
  }
  return 1;
}

int platform_facts_v2_resolve_trap_call(uint8_t platform_kind,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t block_start,
    uint32_t trap_offset, PlatformFactsV2ResolvedCall *out_info) {
  if (out_info != NULL) platform_facts_v2_resolved_call_init(out_info);
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return atari_resolve_trap_call(section, accepted_start, block_start, trap_offset, out_info);
  default:
    return 0;
  }
}

int platform_facts_v2_resolve_stack_cleanup_call(uint8_t platform_kind,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t block_start,
    uint32_t cleanup_offset, const M68kInstructionIR *cleanup_instruction,
    PlatformFactsV2ResolvedCall *out_info) {
  if (out_info != NULL) platform_facts_v2_resolved_call_init(out_info);
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return atari_resolve_stack_cleanup_call(section, accepted_start, block_start, cleanup_offset,
      cleanup_instruction, out_info);
  default:
    return 0;
  }
}
