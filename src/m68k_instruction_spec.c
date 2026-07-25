#include "m68k_instruction_spec.h"
#include "m68k_parse_util.h"
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
  uint16_t patch_values[M68K_INSTRUCTION_SPEC_MAX_PATCH_VALUES];
  M68kAsmInstructionSpec spec;
  const M68kAsmFormDef *form;
  uint16_t asm_form_index;
  size_t byte_count = 0;
  size_t patch_index;
  memset(&spec, 0, sizeof(spec));
  asm_form_index = instruction->asm_form_index;
  form = &g_m68k_asm_forms[asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) {
    asm_form_index = m68k_asm_form_index_for_operands_id(instruction->mnemonic_id, instruction->operands,
      instruction->operand_count, instruction->size_suffix, instruction->target_cpu);
    form = &g_m68k_asm_forms[asm_form_index];
  }
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE ||
      form->patch_count > M68K_INSTRUCTION_SPEC_MAX_PATCH_VALUES) {
    return 0;
  }
  if (instruction->patch_value_count >= form->patch_count) {
    memcpy(patch_values, instruction->patch_values, form->patch_count * sizeof(patch_values[0]));
  } else if (m68k_asm_build_patch_values(asm_form_index, instruction->size_suffix, instruction->operands,
      instruction->operand_count, patch_values, sizeof(patch_values) / sizeof(patch_values[0])) != 0) {
    return 0;
  }
  if (instruction->has_coprocessor_id != 0U) {
    for (patch_index = 0U; patch_index < form->patch_count; ++patch_index) {
      const M68kAsmFieldPatch *patch = &g_m68k_asm_patches[form->patch_start + patch_index];
      if (patch->field_kind == M68K_ASM_FIELD_ID) patch_values[patch_index] = instruction->coprocessor_id & 0x7U;
    }
  }
  spec.mnemonic_id = instruction->mnemonic_id;
  spec.size_suffix = instruction->size_suffix;
  spec.target_cpu = instruction->target_cpu;
  spec.operand_count = instruction->operand_count;
  spec.patch_values = patch_values;
  spec.patch_value_count = form->patch_count;
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
    if (operand->value.ea_mode == 2U) return M68K_SIM_EA_SHAPE_INDIRECT;
    if (operand->value.ea_mode == 3U) return M68K_SIM_EA_SHAPE_POSTINCREMENT;
    if (operand->value.ea_mode == 4U) return M68K_SIM_EA_SHAPE_PREDECREMENT;
    if (operand->value.ea_mode == 5U) return M68K_SIM_EA_SHAPE_DISPLACEMENT;
    if (operand->value.ea_mode == 6U) return M68K_SIM_EA_SHAPE_INDEX;
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
    int32_t displacement = ea_shape == M68K_SIM_EA_SHAPE_PC_DISPLACEMENT ?
      (int32_t)m68k_sign_extend32(operand->value.value, 16U) : (int32_t)operand->value.value;
    *out_target = (uint32_t)((int32_t)pc_base + displacement);
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

static int cpu_uses_external_fpu_id(uint8_t target_cpu) {
  /* The parser target CPU is a decode ceiling. FPU <cpID> still selects an external 68881/68882 ID. */
  return target_cpu == M68K_ASM_CPU_68020 || target_cpu == M68K_ASM_CPU_68030;
}

static uint8_t fpu_id_alias_mnemonic(uint8_t mnemonic_id) {
  if (mnemonic_id < M68K_ASM_MNEMONIC_COUNT)
    return g_m68k_asm_mnemonic_metadata[mnemonic_id].fpu_alias_target_mnemonic_id;
  return M68K_ASM_MNEMONIC_NONE;
}

static uint8_t fpu_id_coprocessor_mnemonic(uint8_t mnemonic_id) {
  if (mnemonic_id < M68K_ASM_MNEMONIC_COUNT)
    return g_m68k_asm_mnemonic_metadata[mnemonic_id].fpu_coprocessor_mnemonic_id;
  return M68K_ASM_MNEMONIC_NONE;
}

int m68k_instruction_is_fpu_id_alias_instruction(const M68kInstructionIR *instruction) {
  if (instruction == NULL || instruction->has_coprocessor_id == 0U) return 0;
  return fpu_id_alias_mnemonic(instruction->mnemonic_id) != M68K_ASM_MNEMONIC_NONE;
}

int m68k_instruction_needs_fpu_id_directive(const M68kInstructionIR *instruction) {
  if (!m68k_instruction_is_fpu_id_alias_instruction(instruction)) return 0;
  return instruction->coprocessor_id != 1U;
}

int m68k_instruction_make_fpu_id_render_instruction(const M68kInstructionIR *instruction,
    M68kInstructionIR *out_instruction) {
  M68kAsmOperandValue operands[4];
  uint8_t mnemonic_id;
  size_t operand_index;
  if (instruction == NULL || out_instruction == NULL) return 0;
  mnemonic_id = fpu_id_alias_mnemonic(instruction->mnemonic_id);
  if (mnemonic_id == M68K_ASM_MNEMONIC_NONE || instruction->has_coprocessor_id == 0U) return 0;
  *out_instruction = *instruction;
  out_instruction->mnemonic_id = mnemonic_id;
  out_instruction->target_cpu = M68K_ASM_CPU_68040;
  out_instruction->has_coprocessor_id = 0U;
  out_instruction->coprocessor_id = 0U;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index)
    m68k_instruction_operand_to_asm_value(&instruction->operands[operand_index], &operands[operand_index]);
  out_instruction->asm_form_index = m68k_asm_form_index_for_operands_id(mnemonic_id, operands,
    instruction->operand_count, instruction->size_suffix, out_instruction->target_cpu);
  out_instruction->canonical_form_id = g_m68k_asm_forms[out_instruction->asm_form_index].canonical_form_id;
  return g_m68k_asm_forms[out_instruction->asm_form_index].mnemonic_id != M68K_ASM_MNEMONIC_NONE;
}

int m68k_instruction_apply_fpu_directive_alias(M68kInstructionIR *instruction, uint8_t current_fpu_id,
    uint8_t current_fpu_directive_active, uint8_t target_cpu) {
  M68kAsmOperandValue operands[4];
  uint8_t candidate_cpus[8];
  size_t candidate_cpu_count = 0U, operand_index;
  uint8_t mnemonic_id, form_cpu = 0U, cpu;
  uint16_t form_index = 0U;
  if (instruction == NULL) return 1;
  mnemonic_id = fpu_id_coprocessor_mnemonic(instruction->mnemonic_id);
  if (mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 1;
  if (current_fpu_directive_active == 0U) return 1;
  if (current_fpu_id == 0U) return 0;
  if (current_fpu_id == 1U && !cpu_uses_external_fpu_id(target_cpu)) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index)
    m68k_instruction_operand_to_asm_value(&instruction->operands[operand_index], &operands[operand_index]);
  candidate_cpus[candidate_cpu_count++] = target_cpu;
  if (instruction->target_cpu != target_cpu) candidate_cpus[candidate_cpu_count++] = instruction->target_cpu;
  for (cpu = M68K_ASM_CPU_68000; cpu <= M68K_ASM_CPU_68060; ++cpu) {
    size_t index;
    int seen = 0;
    for (index = 0U; index < candidate_cpu_count; ++index) {
      if (candidate_cpus[index] == cpu) {
        seen = 1;
        break;
      }
    }
    if (!seen) candidate_cpus[candidate_cpu_count++] = cpu;
  }
  for (operand_index = 0U; operand_index < candidate_cpu_count; ++operand_index) {
    form_cpu = candidate_cpus[operand_index];
    form_index = m68k_asm_form_index_for_operands_id(mnemonic_id, operands,
      instruction->operand_count, instruction->size_suffix, form_cpu);
    if (g_m68k_asm_forms[form_index].mnemonic_id != M68K_ASM_MNEMONIC_NONE) break;
  }
  if (g_m68k_asm_forms[form_index].mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0;
  instruction->asm_form_index = form_index;
  instruction->canonical_form_id = g_m68k_asm_forms[form_index].canonical_form_id;
  instruction->mnemonic_id = mnemonic_id;
  instruction->target_cpu = form_cpu;
  instruction->has_coprocessor_id = 1U;
  instruction->coprocessor_id = current_fpu_id & 0x7U;
  return 1;
}

void m68k_instruction_spec_to_ir(const InstructionSpec *spec, M68kInstructionIR *out_instruction) {
  const M68kAsmFormDef *form;
  unsigned char bytes[64];
  size_t operand_index;
  m68k_ir_instruction_init(out_instruction);
  out_instruction->mnemonic_id = spec->mnemonic_id;
  out_instruction->size_suffix = spec->size_suffix;
  out_instruction->target_cpu = spec->target_cpu;
  out_instruction->has_coprocessor_id = spec->has_coprocessor_id;
  out_instruction->coprocessor_id = spec->coprocessor_id;
  out_instruction->operand_count = spec->operand_count;
  form = &g_m68k_asm_forms[spec->asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) {
    uint16_t asm_form_index = m68k_asm_form_index_for_operands_id(out_instruction->mnemonic_id, spec->operands,
      spec->operand_count, spec->size_suffix, spec->target_cpu);
    form = &g_m68k_asm_forms[asm_form_index];
  }
  if (form->mnemonic_id != M68K_ASM_MNEMONIC_NONE) {
    out_instruction->asm_form_index = form->asm_form_index;
    out_instruction->canonical_form_id = form->canonical_form_id;
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
  out_spec->has_coprocessor_id = instruction->has_coprocessor_id;
  out_spec->coprocessor_id = instruction->coprocessor_id;
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
  {
    M68kAsmOperandValue form_operands[M68K_INSTRUCTION_SPEC_MAX_OPERANDS];
    const M68kAsmFormDef *form;
    uint16_t asm_form_index = out_spec->asm_form_index;
    size_t patch_index;
    for (operand_index = 0; operand_index < out_spec->operand_count &&
        operand_index < M68K_INSTRUCTION_SPEC_MAX_OPERANDS; ++operand_index) {
      form_operands[operand_index] = out_spec->operands[operand_index];
    }
    if (m68k_instruction_spec_uses_movem_predecrement_mask(out_spec))
      form_operands[0].value = m68k_reverse_reglist_mask((uint16_t)form_operands[0].value);
    form = &g_m68k_asm_forms[asm_form_index];
    if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) {
      asm_form_index = m68k_asm_form_index_for_operands_id(out_spec->mnemonic_id, form_operands,
        out_spec->operand_count, out_spec->size_suffix, out_spec->target_cpu);
      form = &g_m68k_asm_forms[asm_form_index];
    }
    if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE ||
        form->patch_count > M68K_INSTRUCTION_SPEC_MAX_PATCH_VALUES) {
      return;
    }
    if (m68k_asm_build_patch_values(asm_form_index, out_spec->size_suffix, form_operands,
        out_spec->operand_count, out_spec->patch_values,
        sizeof(out_spec->patch_values) / sizeof(out_spec->patch_values[0])) != 0) {
      return;
    }
    out_spec->patch_value_count = form->patch_count;
    if (out_spec->has_coprocessor_id != 0U) {
      for (patch_index = 0U; patch_index < form->patch_count; ++patch_index) {
        const M68kAsmFieldPatch *patch = &g_m68k_asm_patches[form->patch_start + patch_index];
        if (patch->field_kind == M68K_ASM_FIELD_ID) out_spec->patch_values[patch_index] =
          out_spec->coprocessor_id & 0x7U;
      }
    }
  }
}
