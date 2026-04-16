#include "m68k_instruction_spec.h"
#include "m68k_simulator.h"

#include <stdio.h>
#include <string.h>

const char *m68k_instruction_spec_mnemonic_name(const InstructionSpec *instruction) {
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_NONE)
    return m68k_asm_mnemonic_name(instruction->mnemonic_id);
  return m68k_asm_mnemonic_name(M68K_ASM_MNEMONIC_NONE);
}

size_t m68k_instruction_spec_assemble_bytes(const InstructionSpec *instruction, unsigned char *out_bytes,
    size_t max_bytes) {
  M68kAsmInstructionSpec spec;
  size_t byte_count = 0;
  memset(&spec, 0, sizeof(spec));
  spec.mnemonic_id = instruction->mnemonic_id;
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
  if (instruction->operand_count != 2U) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEM) return 0;
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

int m68k_instruction_operand_supports_decoded_ea_target(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  return operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_IND ||
    operand->kind == M68K_ASM_OPERAND_POSTINC || operand->kind == M68K_ASM_OPERAND_ABSL ||
    operand->kind == M68K_ASM_OPERAND_BF_EA;
}

uint8_t m68k_instruction_operand_decoded_ea_shape(const M68kOperandIR *operand) {
  if (!m68k_instruction_operand_supports_decoded_ea_target(operand)) return M68K_SIM_EA_SHAPE_NONE;
  if (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) {
    if (operand->value.ea_mode == 7U && operand->value.ea_reg == 0U) return M68K_SIM_EA_SHAPE_ABSOLUTE_WORD;
    if (operand->value.ea_mode == 7U && operand->value.ea_reg == 1U) return M68K_SIM_EA_SHAPE_ABSOLUTE_LONG;
    if (operand->value.ea_mode == 7U && operand->value.ea_reg == 2U) return M68K_SIM_EA_SHAPE_PC_DISPLACEMENT;
    if (operand->value.ea_mode == 7U && operand->value.ea_reg == 3U) return M68K_SIM_EA_SHAPE_PC_INDEX;
  }
  if (operand->kind == M68K_ASM_OPERAND_ABSL) return M68K_SIM_EA_SHAPE_ABSOLUTE_LONG;
  if (operand->kind == M68K_ASM_OPERAND_IND) return M68K_SIM_EA_SHAPE_INDIRECT;
  if (operand->kind == M68K_ASM_OPERAND_POSTINC) return M68K_SIM_EA_SHAPE_POSTINCREMENT;
  return M68K_SIM_EA_SHAPE_NONE;
}

uint8_t m68k_instruction_decoded_ea_target_kind(const M68kOperandIR *operand, uint8_t ea_shape,
    int include_pc_index) {
  if (!m68k_instruction_operand_supports_decoded_ea_target(operand)) return 0U;
  if (ea_shape == M68K_SIM_EA_SHAPE_ABSOLUTE_WORD || ea_shape == M68K_SIM_EA_SHAPE_ABSOLUTE_LONG) return 1U;
  if (ea_shape == M68K_SIM_EA_SHAPE_PC_DISPLACEMENT ||
      (include_pc_index && ea_shape == M68K_SIM_EA_SHAPE_PC_INDEX)) {
    return 2U;
  }
  return 0U;
}

int m68k_instruction_decoded_ea_target(const M68kOperandIR *operand, uint8_t ea_shape, uint32_t pc_base,
    uint32_t section_size, int include_pc_index, uint32_t *out_target) {
  if (operand == NULL || out_target == NULL || !m68k_instruction_operand_supports_decoded_ea_target(operand))
    return 0;
  if (m68k_instruction_decoded_ea_target_kind(operand, ea_shape, include_pc_index) == 1U) {
    *out_target = operand->value.value;
    return *out_target < section_size;
  }
  if (m68k_instruction_decoded_ea_target_kind(operand, ea_shape, include_pc_index) == 2U) {
    *out_target = (uint32_t)((int32_t)pc_base + (int32_t)operand->value.value);
    return *out_target < section_size;
  }
  return 0;
}

int m68k_instruction_operand_direct_register(const M68kOperandIR *operand, uint8_t *is_address, uint8_t *reg) {
  if (operand == NULL || is_address == NULL || reg == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) {
    *is_address = 0U;
    *reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_AN) {
    *is_address = 1U;
    *reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN) {
    *is_address = operand->value.reg_is_address;
    *reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode <= 1U) {
    *is_address = operand->value.ea_mode == 1U;
    *reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

int m68k_instruction_operand_matches_form_kind(const M68kOperandIR *operand, uint8_t form_kind) {
  if (operand == NULL) return 0;
  switch (form_kind) {
  case M68K_ASM_OPERAND_IND:
    return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 2U;
  case M68K_ASM_OPERAND_POSTINC:
    return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 3U;
  case M68K_ASM_OPERAND_PREDEC:
    return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 4U;
  case M68K_ASM_OPERAND_ABSL:
    return operand->kind == M68K_ASM_OPERAND_EA &&
      operand->value.ea_mode == 7U && operand->value.ea_reg == 1U;
  case M68K_ASM_OPERAND_EA:
    return operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_IND ||
      operand->kind == M68K_ASM_OPERAND_POSTINC || operand->kind == M68K_ASM_OPERAND_PREDEC ||
      operand->kind == M68K_ASM_OPERAND_ABSL;
  default:
    return operand->kind == form_kind;
  }
}

void m68k_instruction_operand_to_asm_value(const M68kOperandIR *operand, M68kAsmOperandValue *out_value) {
  if (out_value == NULL) return;
  memset(out_value, 0, sizeof(*out_value));
  if (operand == NULL) return;
  *out_value = operand->value;
  out_value->kind = operand->kind;
  switch (operand->kind) {
  case M68K_ASM_OPERAND_IND:
    out_value->kind = M68K_ASM_OPERAND_EA;
    out_value->ea_mode = 2U;
    break;
  case M68K_ASM_OPERAND_POSTINC:
    out_value->kind = M68K_ASM_OPERAND_EA;
    out_value->ea_mode = 3U;
    break;
  case M68K_ASM_OPERAND_PREDEC:
    out_value->kind = M68K_ASM_OPERAND_EA;
    out_value->ea_mode = 4U;
    out_value->ea_reg = operand->value.reg;
    break;
  case M68K_ASM_OPERAND_ABSL:
    out_value->kind = M68K_ASM_OPERAND_EA;
    out_value->ea_mode = 7U;
    out_value->ea_reg = 1U;
    break;
  default:
    break;
  }
}

void m68k_instruction_spec_to_ir(const InstructionSpec *spec, M68kInstructionIR *out_instruction) {
  const M68kAsmFormDef *form;
  unsigned char bytes[64];
  size_t operand_index;
  m68k_ir_instruction_init(out_instruction);
  out_instruction->mnemonic_id = spec->mnemonic_id;
  out_instruction->size_suffix = spec->size_suffix;
  out_instruction->target_cpu = spec->target_cpu;
  out_instruction->operand_count = spec->operand_count;
  form = &g_m68k_asm_forms[spec->asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) {
    uint16_t asm_form_index = m68k_asm_form_index_for_operands_id(out_instruction->mnemonic_id, spec->operands,
      spec->operand_count, spec->size_suffix, spec->target_cpu);
    form = &g_m68k_asm_forms[asm_form_index];
  }
  if (form->mnemonic_id != M68K_ASM_MNEMONIC_NONE) {
    out_instruction->asm_form_index = form->asm_form_index;
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
  out_spec->mnemonic_id = instruction->mnemonic_id;
  out_spec->size_suffix = instruction->size_suffix;
  out_spec->target_cpu = instruction->target_cpu;
  out_spec->asm_form_index = instruction->asm_form_index;
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
