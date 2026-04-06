#include "m68k_instruction_spec.h"

#include <stdio.h>
#include <string.h>

size_t m68k_instruction_spec_assemble_bytes(const InstructionSpec *instruction, unsigned char *out_bytes,
    size_t max_bytes) {
  M68kAsmInstructionSpec spec;
  size_t byte_count = 0;
  spec.mnemonic = instruction->mnemonic;
  spec.size_suffix = instruction->size_suffix;
  spec.target_cpu = instruction->target_cpu;
  spec.operand_count = instruction->operand_count;
  spec.patch_values = instruction->patch_values;
  spec.patch_value_count = instruction->patch_value_count;
  spec.operands = instruction->operands;
  if (m68k_asm_assemble_instruction(&spec, out_bytes, max_bytes, &byte_count) != 0) return 0;
  return byte_count;
}

int m68k_instruction_spec_uses_movem_predecrement_mask(const InstructionSpec *instruction) {
  if (instruction == NULL || instruction->operand_count != 2U) return 0;
  if (_stricmp(instruction->mnemonic, "movem") != 0) return 0;
  if (instruction->operands[0].kind != M68K_ASM_OPERAND_REGLIST) return 0;
  if (instruction->operands[1].kind != M68K_ASM_OPERAND_EA) return 0;
  return instruction->operands[1].ea_mode == 4U;
}

uint16_t m68k_reverse_reglist_mask(uint16_t mask) {
  uint16_t reversed = 0U;
  unsigned bit;
  for (bit = 0; bit < 16U; ++bit) {
    if ((mask & (uint16_t)(1U << bit)) == 0U) continue;
    reversed |= (uint16_t)(1U << (15U - bit));
  }
  return reversed;
}

void m68k_instruction_spec_to_ir(const InstructionSpec *spec, M68kInstructionIR *out_instruction) {
  const M68kAsmFormDef *form;
  unsigned char bytes[64];
  size_t operand_index;
  m68k_ir_instruction_init(out_instruction);
  snprintf(out_instruction->mnemonic, sizeof(out_instruction->mnemonic), "%s", spec->mnemonic);
  out_instruction->size_suffix = spec->size_suffix;
  out_instruction->target_cpu = spec->target_cpu;
  out_instruction->operand_count = spec->operand_count;
  form = NULL;
  if (spec->form_index != M68K_IR_INVALID_FORM_INDEX && (size_t)spec->form_index < m68k_asm_form_count())
    form = &g_m68k_asm_forms[spec->form_index];
  if (form == NULL)
    form = m68k_asm_find_form_for_operands(spec->mnemonic, spec->operands, spec->operand_count, spec->size_suffix,
      spec->target_cpu);
  if (form != NULL) {
    out_instruction->form_index = (uint16_t)(form - g_m68k_asm_forms);
    out_instruction->mnemonic_id = form->mnemonic_id;
  }
  out_instruction->byte_count = m68k_instruction_spec_assemble_bytes(spec, bytes, sizeof(bytes));
  for (operand_index = 0; operand_index < spec->operand_count && operand_index < M68K_INSTRUCTION_SPEC_MAX_OPERANDS;
      ++operand_index) {
    M68kOperandIR *operand = &out_instruction->operands[operand_index];
    operand->kind = spec->operands[operand_index].kind;
    operand->value = spec->operands[operand_index];
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    if (spec->operand_label_names[operand_index][0] != '\0') {
      operand->symbol_ref.has_name = 1;
      operand->symbol_ref.name_is_generated = 0U;
      operand->symbol_ref.addend = spec->operand_label_addends[operand_index];
      snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s",
        spec->operand_label_names[operand_index]);
      if (operand->kind == M68K_ASM_OPERAND_LABEL) {
        operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_PC_REL;
      } else if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7 &&
          (operand->value.ea_reg == 2 || operand->value.ea_reg == 3)) {
        operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_PC_REL;
      } else {
        operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_ABS;
      }
    }
  }
}

void m68k_instruction_ir_to_spec(const M68kInstructionIR *instruction, InstructionSpec *out_spec) {
  size_t operand_index;
  memset(out_spec, 0, sizeof(*out_spec));
  snprintf(out_spec->mnemonic, sizeof(out_spec->mnemonic), "%s", instruction->mnemonic);
  out_spec->size_suffix = instruction->size_suffix;
  out_spec->target_cpu = instruction->target_cpu;
  out_spec->form_index = instruction->form_index;
  out_spec->operand_count = instruction->operand_count;
  for (operand_index = 0; operand_index < instruction->operand_count &&
      operand_index < M68K_INSTRUCTION_SPEC_MAX_OPERANDS; ++operand_index) {
    out_spec->operands[operand_index] = instruction->operands[operand_index].value;
    if (instruction->operands[operand_index].symbol_ref.has_name) {
      snprintf(out_spec->operand_label_names[operand_index], sizeof(out_spec->operand_label_names[operand_index]), "%s",
        instruction->operands[operand_index].symbol_ref.name);
      out_spec->operand_label_addends[operand_index] = instruction->operands[operand_index].symbol_ref.addend;
    }
  }
}
