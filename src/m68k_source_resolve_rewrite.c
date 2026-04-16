#include "m68k_source_resolve_rewrite.h"

#include "m68k_plain_parse.h"

#include <stdio.h>
#include <string.h>


#define M68K_SOURCE_RESOLVE_MAX_CASE_BYTES 64
static int encode_instruction_with_form_local(const InstructionSpec *instruction, uint16_t asm_form_index,
    char requested_size_suffix, unsigned char *out_bytes, size_t max_bytes, size_t *out_byte_count,
    M68kDiagSink diagnostics) {
  InstructionSpec working = *instruction;
  const M68kAsmFormDef *form = &g_m68k_asm_forms[asm_form_index];
  M68kAsmInstructionSpec spec;
  memset(&spec, 0, sizeof(spec));
  if (working.size_suffix == '\0') working.size_suffix = requested_size_suffix;
  if (form->bound_word_count != 0U && working.patch_value_count < (size_t)form->bound_word_count) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
      "missing patch values for form");
    return 0;
  }
  if (m68k_instruction_spec_uses_movem_predecrement_mask(&working))
    working.operands[0].value = m68k_reverse_reglist_mask((uint16_t)working.operands[0].value);
  spec.mnemonic_id = form->mnemonic_id;
  spec.size_suffix = working.size_suffix;
  spec.target_cpu = working.target_cpu;
  spec.operand_count = working.operand_count;
  spec.patch_values = working.patch_values;
  spec.patch_value_count = working.patch_value_count;
  spec.operands = working.operands;
  if (m68k_asm_assemble_instruction(&spec, out_bytes, max_bytes, out_byte_count) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
      "assemble instruction failed");
    return 0;
  }
  return 1;
}

int m68k_try_rewrite_local_call_to_branch(const M68kSourceResolveRewriteContext *context,
    size_t stmt_section_index, char requested_size_suffix, InstructionSpec *instruction,
    uint16_t *io_asm_form_index, uint32_t instruction_offset, M68kDiagSink diagnostics) {
  const char *branch_mnemonic = NULL;
  const char *label_name = NULL;
  M68kSourceLookupResult symbol;
  int32_t displacement = 0;
  char branch_text[64];
  InstructionSpec candidate;
  uint16_t candidate_form_index;
  unsigned char bytes[M68K_SOURCE_RESOLVE_MAX_CASE_BYTES];
  size_t byte_count = 0;
  if (instruction->operand_count != 1U) return 0;
  switch (instruction->mnemonic_id) {
    case M68K_ASM_MNEMONIC_JSR:
      branch_mnemonic = "bsr";
      break;
    case M68K_ASM_MNEMONIC_JMP:
      branch_mnemonic = "bra";
      break;
    default:
      return 0;
  }
  label_name = instruction->operand_label_names[0];
  if (label_name[0] == '\0') return 0;
  symbol = context->lookup_symbol(label_name, context->user_data);
  if (!symbol.ok || !symbol.defined || symbol.section_index != stmt_section_index) return 0;
  displacement = (int32_t)symbol.value - (int32_t)(instruction_offset + 2U);
  if (displacement < -32768 || displacement > 32767) return 0;
  snprintf(branch_text, sizeof(branch_text), "%s %d", branch_mnemonic, (int)displacement);
  if (!m68k_plain_parse_instruction_to_spec(branch_text, instruction->target_cpu, &candidate)) return 0;
  candidate_form_index = m68k_asm_form_index_for_operands_id(candidate.mnemonic_id, candidate.operands,
    candidate.operand_count, requested_size_suffix, candidate.target_cpu);
  if (g_m68k_asm_forms[candidate_form_index].mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0;
  if (!encode_instruction_with_form_local(&candidate, candidate_form_index, requested_size_suffix,
      bytes, sizeof(bytes), &byte_count, diagnostics)) {
    return 0;
  }
  *instruction = candidate;
  *io_asm_form_index = candidate_form_index;
  return 1;
}

void m68k_try_rewrite_local_ea_symbols_to_pc_relative(const M68kSourceResolveRewriteContext *context,
  size_t stmt_section_index, char requested_size_suffix, InstructionSpec *instruction,
  uint16_t *io_asm_form_index, uint32_t instruction_offset, M68kDiagSink diagnostics) {
  size_t operand_index;
  unsigned char current_bytes[M68K_SOURCE_RESOLVE_MAX_CASE_BYTES];
  size_t current_size = 0;
  if (!encode_instruction_with_form_local(instruction, *io_asm_form_index, requested_size_suffix,
      current_bytes, sizeof(current_bytes), &current_size, diagnostics)) {
    return;
  }
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    const char *label_name = instruction->operand_label_names[operand_index];
    M68kSourceLookupResult symbol;
    InstructionSpec candidate;
    uint16_t candidate_form_index;
    unsigned char candidate_bytes[M68K_SOURCE_RESOLVE_MAX_CASE_BYTES];
    size_t candidate_size = 0;
    int32_t displacement = 0;
    if (label_name[0] == '\0') continue;
    if (instruction->operands[operand_index].kind != M68K_ASM_OPERAND_EA) continue;
    symbol = context->lookup_symbol(label_name, context->user_data);
    if (!symbol.ok || !symbol.defined || symbol.section_index != stmt_section_index) continue;
    candidate = *instruction;
    candidate.operands[operand_index].ea_mode = 7;
    candidate.operands[operand_index].ea_reg = 2;
    candidate.operands[operand_index].value = 0U;
    candidate_form_index = m68k_asm_form_index_for_operands_id(candidate.mnemonic_id, candidate.operands,
      candidate.operand_count, requested_size_suffix, candidate.target_cpu);
    if (g_m68k_asm_forms[candidate_form_index].mnemonic_id == M68K_ASM_MNEMONIC_NONE) continue;
    displacement = (int32_t)symbol.value
      - (int32_t)(instruction_offset +
        m68k_asm_operand_relative_base_offset(candidate_form_index, candidate.operands,
          candidate.operand_count, candidate.size_suffix, operand_index, 0));
    if (displacement < -32768 || displacement > 32767) continue;
    candidate.operands[operand_index].value = (uint32_t)displacement;
    if (!encode_instruction_with_form_local(&candidate, candidate_form_index, requested_size_suffix,
        candidate_bytes, sizeof(candidate_bytes), &candidate_size, diagnostics)) {
      continue;
    }
    if (candidate_size >= current_size) continue;
    *instruction = candidate;
    *io_asm_form_index = candidate_form_index;
    current_size = candidate_size;
  }
}
