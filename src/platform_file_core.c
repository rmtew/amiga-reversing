/* Internal section analysis implementation for platform_file_lib. */
#include "platform_file_internal.h"
#include "generated/m68k_simulator_tables.h"

static int section_decode_cache_init(SectionDecodeCache *cache, Arena *arena, size_t section_size);
int section_analysis_context_probe_decode(const SectionAnalysisContext *ctx, uint32_t offset,
    SectionDecodeResult *out_result);
uint8_t section_analysis_context_backend_kind(const SectionAnalysisContext *ctx);
const M68kObject *section_analysis_context_object(const SectionAnalysisContext *ctx);
const M68kSection *section_analysis_context_section(const SectionAnalysisContext *ctx);
size_t section_analysis_context_section_index(const SectionAnalysisContext *ctx);
const M68kSectionAnalysisIR *section_analysis_context_prior_section_analysis(const SectionAnalysisContext *ctx,
    size_t section_index);
const M68kAnalysisPolicy *section_analysis_context_policy(const SectionAnalysisContext *ctx);
size_t section_analysis_find_block_index_containing(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
int instruction_writes_address_reg_approx(const M68kInstructionIR *instruction, uint8_t reg);
int instruction_writes_data_reg_approx(const M68kInstructionIR *instruction, uint8_t reg);
int operand_raw_constant_value_local(const M68kOperandIR *operand, int32_t *out_value);
static int instruction_known_stack_delta_from_metadata(const M68kInstructionIR *instruction, int32_t *inout_stack_delta);
static int sim_operand_direct_register_local(const M68kOperandIR *operand, uint8_t *is_address, uint8_t *reg);

static uint8_t effective_analysis_max_cpu(const M68kAnalysisPolicy *policy) {
  if (policy == NULL) return M68K_ASM_CPU_68060;
  if (policy->max_cpu > M68K_ASM_CPU_68060) return M68K_ASM_CPU_68060;
  return policy->max_cpu;
}

static uint8_t instruction_required_cpu(const M68kInstructionIR *instruction) {
  const M68kAsmFormDef *form;
  uint8_t cpu;
  if (instruction->target_cpu <= M68K_ASM_CPU_68060) return instruction->target_cpu;
  form = &g_m68k_asm_forms[instruction->asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return instruction->target_cpu;
  for (cpu = M68K_ASM_CPU_68000; cpu <= M68K_ASM_CPU_68060; ++cpu) {
    if ((form->cpu_mask & (1u << cpu)) != 0u) return cpu;
  }
  return instruction->target_cpu;
}

static void update_required_cpu(M68kAnalysisFindings *findings, uint8_t required_cpu) {
  if (findings == NULL) return;
  if (required_cpu > findings->required_cpu) findings->required_cpu = required_cpu;
}

static int decode_instruction_with_policy(const uint8_t *data, size_t size, uint32_t offset,
    const M68kAnalysisPolicy *policy, M68kAnalysisFindings *findings, M68kInstructionIR *out_instruction,
    M68kDiagSink diagnostics) {
  uint8_t max_cpu = effective_analysis_max_cpu(policy);
  uint8_t cpu;
  (void)offset;
  for (cpu = M68K_ASM_CPU_68000; cpu <= M68K_ASM_CPU_68060; ++cpu) {
    M68kDiagList decode_diagnostics;
    m68k_diag_list_reset(&decode_diagnostics);
    *out_instruction = m68k_ir_decode_one(data, size, cpu, m68k_diag_sink(&decode_diagnostics));
    if (!m68k_diag_has_errors(&decode_diagnostics) && out_instruction->byte_count != 0U) {
      uint8_t required_cpu = instruction_required_cpu(out_instruction);
      update_required_cpu(findings, required_cpu);
      if (required_cpu > max_cpu)
        if (findings != NULL) findings->cpu_violation_count += 1U;
      return 1;
    }
    if (cpu == M68K_ASM_CPU_68060) break;
  }
  (void)diagnostics;
  return 0;
}

static uint16_t instruction_assembler_form_index_local(const M68kInstructionIR *instruction,
    M68kInstructionIR *out_layout_instruction) {
  const M68kAsmFormDef *form;
  M68kAsmOperandValue operands[4];
  uint16_t asm_form_index;
  uint8_t mnemonic_id;
  size_t operand_index;
  if (out_layout_instruction != NULL) *out_layout_instruction = *instruction;
  mnemonic_id = instruction->mnemonic_id;
  form = &g_m68k_asm_forms[instruction->asm_form_index];
  if (form->mnemonic_id != M68K_ASM_MNEMONIC_NONE && form->mnemonic_id == mnemonic_id &&
      form->operand_count == instruction->operand_count) {
    for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
      if (!m68k_instruction_operand_matches_form_kind(&instruction->operands[operand_index],
          form->operand_kinds[operand_index])) break;
    }
    if (operand_index == instruction->operand_count) return instruction->asm_form_index;
  }
  for (operand_index = 0; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    m68k_instruction_operand_to_asm_value(&instruction->operands[operand_index], &operands[operand_index]);
  }
  asm_form_index = m68k_asm_form_index_for_operands_id(mnemonic_id, operands, instruction->operand_count,
    instruction->size_suffix, instruction->target_cpu);
  form = &g_m68k_asm_forms[asm_form_index];
  if (out_layout_instruction != NULL) {
    out_layout_instruction->asm_form_index = asm_form_index;
    out_layout_instruction->mnemonic_id = form->mnemonic_id;
    for (operand_index = 0; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
      out_layout_instruction->operands[operand_index].value = operands[operand_index];
      out_layout_instruction->operands[operand_index].kind = operands[operand_index].kind;
    }
  }
  return asm_form_index;
}

static char instruction_effective_size_suffix_local(const M68kInstructionIR *instruction, const M68kAsmFormDef *form) {
  M68kAsmOperandValue operands[4];
  size_t operand_index;
  char size_suffix;
  for (operand_index = 0; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index)
    operands[operand_index] = instruction->operands[operand_index].value;
  size_suffix = m68k_asm_choose_size_suffix(form, operands, instruction->operand_count, instruction->size_suffix);
  if (size_suffix != '\0') return size_suffix;
  return instruction->size_suffix;
}

static int operand_uses_single_word_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    (operand->ea_mode == 5 || (operand->ea_mode == 7 && operand->ea_reg == 0) ||
      (operand->ea_mode == 7 && operand->ea_reg == 2));
}

static int operand_uses_long_address_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->ea_mode == 7 && operand->ea_reg == 1;
}

static int operand_uses_immediate_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->ea_mode == 7 && operand->ea_reg == 4) || operand->kind == M68K_ASM_OPERAND_IMM;
}

static const M68kFixup *find_instruction_operand_abs32_fixup(const M68kObject *object, size_t section_index,
    const M68kInstructionIR *instruction, size_t operand_index, uint32_t instruction_offset);
static const M68kFixup *find_instruction_target_fixup(const M68kObject *object, size_t section_index,
    const M68kInstructionIR *instruction, size_t operand_index, uint32_t instruction_offset,
    const M68kAnalysisPolicy *analysis_policy);
static uint32_t find_enclosing_code_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
static int platform_resolve_same_section_direct_target_with_fixup(const SectionAnalysisContext *ctx,
    const M68kInstructionIR *instruction, uint32_t instruction_offset, uint32_t *out_target);

static int fixup_source_operand_is_direct_control_transfer(const M68kObject *object, const M68kFixup *fixup,
    const M68kAnalysisPolicy *analysis_policy);

static uint32_t fixup_width_byte_count(const M68kFixup *fixup) {
  if (fixup == NULL) return 0U;
  switch (fixup->width) {
    case M68K_FIXUP_WIDTH_8: return 1U;
    case M68K_FIXUP_WIDTH_16: return 2U;
    case M68K_FIXUP_WIDTH_32: return 4U;
    default: return 0U;
  }
}

static int fixup_payload_fits_section_data(const M68kSection *section, const M68kFixup *fixup) {
  uint32_t width = fixup_width_byte_count(fixup);
  if (section == NULL || fixup == NULL || width == 0U) return 0;
  if (fixup->offset > section->data_size) return 0;
  return width <= section->data_size - fixup->offset;
}

static int fixup_target_offset_local(const M68kObject *object, const M68kFixup *fixup, uint32_t *out_offset) {
  const M68kSection *source_section;
  const M68kSection *target_section;
  uint32_t target_extent, width, target;
  uint32_t raw_value = 0U;
  int32_t signed_value = 0;
  int64_t computed_target = -1;
  if (object == NULL || fixup == NULL || out_offset == NULL || !fixup->has_target_section ||
      fixup->section_index >= object->section_count || fixup->target_section_index >= object->section_count) {
    return 0;
  }
  source_section = &object->sections[fixup->section_index];
  target_section = &object->sections[fixup->target_section_index];
  target_extent = target_section->size != 0U ? target_section->size : target_section->data_size;
  width = fixup_width_byte_count(fixup);
  if (width == 0U || !fixup_payload_fits_section_data(source_section, fixup)) return 0;
  if (width == 1U) {
    raw_value = source_section->data[fixup->offset];
    signed_value = (int8_t)raw_value;
  } else if (width == 2U) {
    raw_value = m68k_read_u16be(source_section->data + fixup->offset);
    signed_value = (int16_t)raw_value;
  } else {
    raw_value = m68k_read_u32be(source_section->data + fixup->offset);
    signed_value = (int32_t)raw_value;
  }
  if (fixup->kind == M68K_FIXUP_PC_REL) {
    computed_target = (int64_t)fixup->offset + (int64_t)signed_value;
  } else if (fixup->kind == M68K_FIXUP_ABS || fixup->kind == M68K_FIXUP_SECTION_REL) {
    computed_target = (int64_t)raw_value;
  }
  if (computed_target >= 0 && computed_target <= UINT32_MAX) target = (uint32_t)computed_target;
  else target = UINT32_MAX;
  if (target > target_extent) {
    if (fixup->addend < 0 || (uint32_t)fixup->addend >= target_extent) return 0;
    target = (uint32_t)fixup->addend;
  }
  *out_offset = target;
  return 1;
}

static int instruction_mnemonic_is_generated_branch_family(const M68kInstructionIR *instruction) {
  if (instruction == NULL || instruction->mnemonic_id >= M68K_ASM_MNEMONIC_COUNT) return 0;
  return g_m68k_asm_mnemonic_metadata[instruction->mnemonic_id].family == M68K_ASM_MNEMONIC_FAMILY_BRANCH;
}

const M68kSimFormMetadata *instruction_sim_metadata(const M68kInstructionIR *instruction) {
  return m68k_sim_metadata_for_instruction(instruction);
}

static int instruction_branch_target(const M68kInstructionIR *instruction, uint32_t offset, uint32_t *out_target) {
  size_t operand_index;
  uint32_t base_offset;
  if (out_target == NULL) return 0;
  base_offset = offset + 2U;
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->kind == M68K_ASM_OPERAND_LABEL) {
      *out_target = base_offset + (uint32_t)((int32_t)operand->value.value);
      return 1;
    }
  }
  return 0;
}

static int instruction_branch_target_from_bytes(const M68kInstructionIR *instruction, const uint8_t *data, size_t size,
    uint32_t offset, uint32_t *out_target) {
  if (instruction == NULL || data == NULL || out_target == NULL) return 0;
  if (instruction->byte_count == 2U && size >= 2U && instruction_mnemonic_is_generated_branch_family(instruction)) {
    *out_target = offset + 2U + (uint32_t)((int32_t)(int8_t)data[1]);
    return 1;
  }
  if (instruction_branch_target(instruction, offset, out_target)) return 1;
  return 0;
}

static uint8_t instruction_effective_ea_shape(const M68kSimFormMetadata *metadata, const M68kInstructionIR *instruction,
    uint8_t operand_index) {
  const M68kOperandIR *operand;
  if (metadata == NULL || operand_index >= instruction->operand_count) return M68K_SIM_EA_SHAPE_NONE;
  if (metadata->operand_ea_address_shapes[operand_index] != M68K_SIM_EA_SHAPE_NONE)
    return metadata->operand_ea_address_shapes[operand_index];
  if (metadata->operand_ea_address_formulas[operand_index] != M68K_SIM_EA_FORMULA_DECODED_EA) return M68K_SIM_EA_SHAPE_NONE;
  operand = &instruction->operands[operand_index];
  return m68k_instruction_operand_decoded_ea_shape(operand);
}

static int instruction_metadata_operand_target(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  const M68kOperandIR *operand;
  uint8_t pc_bias;
  if (metadata == NULL || out_target == NULL || operand_index >= instruction->operand_count) return 0;
  operand = &instruction->operands[operand_index];
  if (operand->kind == M68K_ASM_OPERAND_LABEL) {
    return instruction_branch_target(instruction, offset, out_target) && *out_target < section_size;
  }
  if (metadata->operand_ea_address_formulas[operand_index] == M68K_SIM_EA_FORMULA_ABSOLUTE_LITERAL &&
      metadata->operand_ea_address_literal_width_bytes[operand_index] != 0U) {
    *out_target = operand->value.value;
    return *out_target < section_size;
  }
  if (metadata->operand_ea_address_formulas[operand_index] == M68K_SIM_EA_FORMULA_PC_PLUS_DISP &&
      metadata->operand_ea_displacement_sources[operand_index] == M68K_SIM_EA_DISP_OPERAND_VALUE &&
      metadata->operand_ea_uses_displacement[operand_index] &&
      !metadata->operand_ea_uses_index[operand_index]) {
    pc_bias = metadata->operand_ea_pc_base_bias_bytes[operand_index] != 0U
      ? metadata->operand_ea_pc_base_bias_bytes[operand_index]
      : 2U;
    *out_target = (uint32_t)((int32_t)offset + (int32_t)pc_bias + (int32_t)operand->value.value);
    return *out_target < section_size;
  }
  if (metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_ADDRESS &&
      metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_IMMEDIATE) {
    *out_target = operand->value.value;
    return *out_target < section_size;
  }
  return 0;
}

int instruction_render_operand_target(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  const M68kOperandIR *operand;
  uint8_t formula;
  uint8_t pc_bias;
  if (metadata == NULL || out_target == NULL || operand_index >= instruction->operand_count) return 0;
  operand = &instruction->operands[operand_index];
  formula = metadata->operand_ea_address_formulas[operand_index];
  if (formula == M68K_SIM_EA_FORMULA_PC_PLUS_DISP &&
      metadata->operand_ea_displacement_sources[operand_index] == M68K_SIM_EA_DISP_OPERAND_VALUE &&
      metadata->operand_ea_uses_displacement[operand_index] &&
      !metadata->operand_ea_uses_index[operand_index]) {
    pc_bias = metadata->operand_ea_pc_base_bias_bytes[operand_index] != 0U
      ? metadata->operand_ea_pc_base_bias_bytes[operand_index]
      : 2U;
    *out_target = (uint32_t)((int32_t)offset + (int32_t)pc_bias + (int32_t)operand->value.value);
    return *out_target < section_size;
  }
  if (formula == M68K_SIM_EA_FORMULA_DECODED_EA &&
      metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_COMPUTE_ADDRESS &&
      metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_ADDRESS) {
    pc_bias = metadata->operand_ea_pc_base_bias_bytes[operand_index] != 0U
      ? metadata->operand_ea_pc_base_bias_bytes[operand_index]
      : 2U;
    return m68k_instruction_decoded_ea_target(operand,
      instruction_effective_ea_shape(metadata, instruction, operand_index),
      offset + (uint32_t)pc_bias, section_size, 1, out_target);
  }
  if (instruction_metadata_operand_target(instruction, metadata, operand_index, offset, section_size, out_target)) return 1;
  return 0;
}

static int operand_is_absolute_long_ea(const M68kOperandIR *operand) {
  return operand != NULL && operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U &&
    operand->value.ea_reg == 1U;
}

static int object_requires_abs32_fixup_for_absolute_label(const M68kObject *object) {
  if (object == NULL) return 0;
  if (object->platform_file_kind == M68K_PLATFORM_FILE_OBJECT) return 1;
  if (object->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  return object->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
    object->platform_backend_kind == M68K_PLATFORM_BACKEND_ATARI_ST;
}

static int absolute_long_operand_missing_required_fixup(const M68kObject *object, size_t section_index,
    const M68kInstructionIR *instruction, size_t operand_index, uint32_t instruction_offset) {
  const M68kOperandIR *operand;
  if (!object_requires_abs32_fixup_for_absolute_label(object)) return 0;
  if (instruction == NULL || operand_index >= instruction->operand_count) return 0;
  operand = &instruction->operands[operand_index];
  return operand_is_absolute_long_ea(operand) &&
    find_instruction_operand_abs32_fixup(object, section_index, instruction, operand_index, instruction_offset) == NULL;
}

static int absolute_long_operand_should_stay_numeric(const M68kObject *object, size_t section_index,
    const M68kInstructionIR *instruction, size_t operand_index, uint32_t instruction_offset) {
  return absolute_long_operand_missing_required_fixup(object, section_index, instruction, operand_index,
    instruction_offset);
}

static int instruction_has_unrelocated_absolute_long_operand(const M68kObject *object, size_t section_index,
    const M68kInstructionIR *instruction, uint32_t instruction_offset) {
  size_t operand_index;
  if (instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    if (absolute_long_operand_should_stay_numeric(object, section_index, instruction, operand_index,
        instruction_offset)) {
      return 1;
    }
  }
  return 0;
}

static int instruction_is_unconditional_transfer(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL) return 0;
  return (metadata->flow_kind == M68K_SIM_FLOW_JUMP) ||
    (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U);
}

int instruction_is_call_transfer(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL) return 0;
  return metadata->flow_kind == M68K_SIM_FLOW_CALL;
}

int instruction_stops_fallthrough(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL) return 0;
  return metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
    metadata->flow_kind == M68K_SIM_FLOW_RETURN ||
    (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U);
}

static int is_conditional_transfer(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL) return 0;
  return metadata->flow_conditional != 0U &&
    (metadata->flow_kind == M68K_SIM_FLOW_BRANCH || metadata->flow_kind == M68K_SIM_FLOW_JUMP);
}

int instruction_target_operand_local(const M68kInstructionIR *instruction, const M68kOperandIR **out_operand) {
  const M68kSimFormMetadata *metadata;
  uint8_t operand_index;
  if (out_operand != NULL) *out_operand = NULL;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL) return 0;
  operand_index = metadata->target_operand_index;
  if (operand_index == 0xFFU || operand_index >= instruction->operand_count) return 0;
  if (out_operand != NULL) *out_operand = &instruction->operands[operand_index];
  return 1;
}

static void platform_resolved_indirect_info_init(PlatformResolvedIndirectInfo *info) {
  if (info == NULL) return;
  memset(info, 0, sizeof(*info));
  info->note_disp = INT16_MIN;
  info->note_field_disp = INT16_MIN;
}

PlatformResolvedIndirectInfo platform_resolved_indirect_info_none(void) {
  PlatformResolvedIndirectInfo info;
  platform_resolved_indirect_info_init(&info);
  return info;
}

int operand_is_absolute_value(const M68kOperandIR *operand, uint32_t value) {
  if (operand == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return 0;
  if (operand->value.ea_mode != 7U) return 0;
  if (operand->value.ea_reg == 0U) return (operand->value.value & 0xFFFFU) == (value & 0xFFFFU);
  if (operand->value.ea_reg == 1U) return operand->value.value == value;
  return 0;
}

int operand_is_app_base_disp_ea(const M68kOperandIR *operand, uint8_t reg, int16_t *out_displacement) {
  if (out_displacement != NULL) *out_displacement = 0;
  if (operand == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return 0;
  if (operand->value.ea_mode != 5U || operand->value.ea_reg != reg) return 0;
  if (out_displacement != NULL) *out_displacement = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

int operand_is_data_reg_direct(const M68kOperandIR *operand, uint8_t reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) return operand->value.reg == reg;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->value.ea_mode == 0U && operand->value.ea_reg == reg;
}

static int operand_is_address_reg_direct(const M68kOperandIR *operand, uint8_t reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) return operand->value.reg == reg;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->value.ea_mode == 1U && operand->value.ea_reg == reg;
}

static int instruction_is_compare_or_test_like_local(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_CMP:
  case M68K_ASM_MNEMONIC_CMPI:
  case M68K_ASM_MNEMONIC_CMPA:
  case M68K_ASM_MNEMONIC_CMPM:
  case M68K_ASM_MNEMONIC_TST:
  case M68K_ASM_MNEMONIC_BTST:
  case M68K_ASM_MNEMONIC_BCHG:
  case M68K_ASM_MNEMONIC_BCLR:
  case M68K_ASM_MNEMONIC_BSET:
    return 1;
  default:
    return 0;
  }
}

static int instruction_is_compare_like_address_write_local(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_CMP:
  case M68K_ASM_MNEMONIC_CMPI:
  case M68K_ASM_MNEMONIC_CMPA:
  case M68K_ASM_MNEMONIC_CMPM:
  case M68K_ASM_MNEMONIC_TST:
    return 1;
  default:
    return 0;
  }
}

int instruction_is_address_move(const M68kInstructionIR *instruction, uint8_t *out_dest_reg,
    const M68kOperandIR **out_source) {
  uint8_t dest_reg;
  uint8_t mnemonic_id;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_source != NULL) *out_source = NULL;
  if (instruction->operand_count != 2U) return 0;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id != M68K_ASM_MNEMONIC_MOVEA && mnemonic_id != M68K_ASM_MNEMONIC_MOVE) return 0;
  for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
    if (operand_is_address_reg_direct(&instruction->operands[1], dest_reg)) {
      if (out_dest_reg != NULL) *out_dest_reg = dest_reg;
      if (out_source != NULL) *out_source = &instruction->operands[0];
      return 1;
    }
  }
  return 0;
}

int instruction_is_data_move(const M68kInstructionIR *instruction, uint8_t *out_dest_reg,
    const M68kOperandIR **out_source) {
  uint8_t dest_reg;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_source != NULL) *out_source = NULL;
  if (instruction->operand_count != 2U) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE) return 0;
  for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
    if (operand_is_data_reg_direct(&instruction->operands[1], dest_reg)) {
      if (out_dest_reg != NULL) *out_dest_reg = dest_reg;
      if (out_source != NULL) *out_source = &instruction->operands[0];
      return 1;
    }
  }
  return 0;
}

int instruction_is_register_to_app_slot_store(const M68kInstructionIR *instruction, uint8_t *out_source_kind,
    uint8_t *out_source_reg, int16_t *out_displacement) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  uint8_t mnemonic_id;
  if (out_source_kind != NULL) *out_source_kind = 0U;
  if (out_source_reg != NULL) *out_source_reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (instruction->operand_count != 2U) return 0;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id != M68K_ASM_MNEMONIC_MOVE && mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) return 0;
  src = &instruction->operands[0];
  dst = &instruction->operands[1];
  if (!operand_is_app_base_disp_ea(dst, 6U, out_displacement)) return 0;
  if (operand_is_data_reg_direct(src, src->kind == M68K_ASM_OPERAND_DN ? src->value.reg : src->value.ea_reg)) {
    if (out_source_kind != NULL) *out_source_kind = 1U;
    if (out_source_reg != NULL) *out_source_reg =
      (src->kind == M68K_ASM_OPERAND_DN) ? src->value.reg : src->value.ea_reg;
    return 1;
  }
  if (operand_is_address_reg_direct(src, src->kind == M68K_ASM_OPERAND_AN ? src->value.reg : src->value.ea_reg)) {
    if (out_source_kind != NULL) *out_source_kind = 2U;
    if (out_source_reg != NULL) *out_source_reg =
      (src->kind == M68K_ASM_OPERAND_AN) ? src->value.reg : src->value.ea_reg;
    return 1;
  }
  return 0;
}

int instruction_is_app_slot_load(const M68kInstructionIR *instruction, uint8_t *out_dest_kind,
    uint8_t *out_dest_reg, int16_t *out_displacement) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  uint8_t mnemonic_id;
  if (out_dest_kind != NULL) *out_dest_kind = 0U;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (instruction->operand_count != 2U) return 0;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id != M68K_ASM_MNEMONIC_MOVE && mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) return 0;
  src = &instruction->operands[0];
  dst = &instruction->operands[1];
  if (!operand_is_app_base_disp_ea(src, 6U, out_displacement)) return 0;
  if (operand_is_data_reg_direct(dst, dst->kind == M68K_ASM_OPERAND_DN ? dst->value.reg : dst->value.ea_reg)) {
    if (out_dest_kind != NULL) *out_dest_kind = 1U;
    if (out_dest_reg != NULL) *out_dest_reg =
      (dst->kind == M68K_ASM_OPERAND_DN) ? dst->value.reg : dst->value.ea_reg;
    return 1;
  }
  if (operand_is_address_reg_direct(dst, dst->kind == M68K_ASM_OPERAND_AN ? dst->value.reg : dst->value.ea_reg)) {
    if (out_dest_kind != NULL) *out_dest_kind = 2U;
    if (out_dest_reg != NULL) *out_dest_reg =
      (dst->kind == M68K_ASM_OPERAND_AN) ? dst->value.reg : dst->value.ea_reg;
    return 1;
  }
  return 0;
}

PlatformRegisterMatch instruction_push_address_reg_to_stack(const M68kInstructionIR *instruction) {
  PlatformRegisterMatch result = {0};
  uint8_t is_address = 0U;
  uint8_t reg = 0U;
  if (instruction->operand_count != 2U) return result;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE) return result;
  if (!sim_operand_direct_register_local(&instruction->operands[0], &is_address, &reg) || is_address == 0U)
    return result;
  if (instruction->operands[1].kind == M68K_ASM_OPERAND_PREDEC) {
    if (instruction->operands[1].value.ea_reg != 7U) return result;
  } else if ((instruction->operands[1].kind == M68K_ASM_OPERAND_EA ||
      instruction->operands[1].kind == M68K_ASM_OPERAND_BF_EA) &&
      instruction->operands[1].value.ea_mode == 4U) {
    if (instruction->operands[1].value.ea_reg != 7U) return result;
  } else return result;
  result.ok = 1U;
  result.reg = reg;
  return result;
}

PlatformRegisterMatch instruction_pop_address_reg_from_stack(const M68kInstructionIR *instruction) {
  PlatformRegisterMatch result = {0};
  const M68kOperandIR *source;
  uint8_t dest_reg;
  if (instruction->operand_count != 2U) return result;
  if (!instruction_is_address_move(instruction, &dest_reg, &source) || source == NULL) return result;
  if (source->kind == M68K_ASM_OPERAND_POSTINC && source->value.ea_reg == 7U) {
    result.ok = 1U;
    result.reg = dest_reg;
    return result;
  }
  if ((source->kind == M68K_ASM_OPERAND_EA || source->kind == M68K_ASM_OPERAND_BF_EA) &&
      source->value.ea_mode == 3U && source->value.ea_reg == 7U) {
    result.ok = 1U;
    result.reg = dest_reg;
    return result;
  }
  return result;
}

PlatformAddressExgInfo instruction_address_exg(const M68kInstructionIR *instruction) {
  PlatformAddressExgInfo result = {0};
  if (instruction->operand_count != 2U) return result;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_EXG) return result;
  if (instruction->operands[0].kind != M68K_ASM_OPERAND_AN || instruction->operands[1].kind != M68K_ASM_OPERAND_AN)
    return result;
  result.ok = 1U;
  result.left_reg = instruction->operands[0].value.reg;
  result.right_reg = instruction->operands[1].value.reg;
  return result;
}

static const M68kRecoveredPlatformCallIR *next_recovered_platform_call_at_same_offset(
    const M68kSectionAnalysisIR *section_analysis, const M68kRecoveredPlatformCallIR *call) {
  size_t index;
  uint32_t next_index;
  if (section_analysis == NULL || call == NULL || section_analysis->recovered_platform_calls == NULL)
    return NULL;
  index = (size_t)(call - section_analysis->recovered_platform_calls);
  if (index >= section_analysis->recovered_platform_call_count) return NULL;
  if (section_analysis->recovered_platform_call_next_lookup != NULL &&
      index < section_analysis->recovered_platform_call_next_lookup_size) {
    next_index = section_analysis->recovered_platform_call_next_lookup[index];
    if (next_index == UINT32_MAX || next_index >= section_analysis->recovered_platform_call_count) return NULL;
    return &section_analysis->recovered_platform_calls[next_index];
  }
  for (index += 1U; index < section_analysis->recovered_platform_call_count; ++index) {
    if (section_analysis->recovered_platform_calls[index].offset == call->offset)
      return &section_analysis->recovered_platform_calls[index];
  }
  return NULL;
}

const M68kRecoveredPlatformCallIR *find_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind) {
  size_t index;
  if (section_analysis == NULL) return NULL;
  if (offset < section_analysis->recovered_platform_call_lookup_size &&
      section_analysis->recovered_platform_call_lookup != NULL) {
    const M68kRecoveredPlatformCallIR *call = section_analysis->recovered_platform_call_lookup[offset];
    for (; call != NULL; call = next_recovered_platform_call_at_same_offset(section_analysis, call)) {
      if (call->kind == kind) return call;
    }
    return NULL;
  }
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
    if (call->offset == offset && call->kind == kind) return call;
  }
  return NULL;
}

const M68kRecoveredPlatformCallIR *find_any_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return NULL;
  if (offset < section_analysis->recovered_platform_call_lookup_size &&
      section_analysis->recovered_platform_call_lookup != NULL &&
      section_analysis->recovered_platform_call_lookup[offset] != NULL) {
    return section_analysis->recovered_platform_call_lookup[offset];
  }
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
    if (call->offset == offset) return call;
  }
  return NULL;
}

void load_recovered_platform_call_info(const M68kRecoveredPlatformCallIR *recovered,
    PlatformResolvedIndirectInfo *out_info) {
  const char *symbol_name;
  const char *note_base_name;
  const char *note_symbol_name;
  if (recovered == NULL || out_info == NULL) return;
  platform_resolved_indirect_info_init(out_info);
  symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&recovered->symbol_ref, recovered->symbol_name);
  note_base_name = m68k_platform_name_ref_resolve_text_or_fallback(&recovered->note_base_ref, recovered->note_base_name);
  note_symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&recovered->note_symbol_ref, recovered->note_symbol_name);
  out_info->kind = recovered->kind;
  out_info->has_symbol_name = symbol_name != NULL ? 1U : 0U;
  out_info->note_kind = recovered->note_kind;
  out_info->note_reg = recovered->note_reg;
  out_info->note_stack_cleanup_known = recovered->note_stack_cleanup_known;
  out_info->note_return_kind = recovered->note_return_kind;
  out_info->note_disp = recovered->note_disp;
  out_info->note_field_disp = recovered->note_field_disp;
  out_info->note_stack_cleanup_bytes = recovered->note_stack_cleanup_bytes;
  if (symbol_name != NULL)
    snprintf(out_info->symbol_name, sizeof(out_info->symbol_name), "%s", symbol_name);
  if (note_base_name != NULL)
    snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", note_base_name);
  if (note_symbol_name != NULL)
    snprintf(out_info->note_symbol_name, sizeof(out_info->note_symbol_name), "%s", note_symbol_name);
  if (recovered->available_since != NULL)
    snprintf(out_info->available_since, sizeof(out_info->available_since), "%s", recovered->available_since);
  if (recovered->fd_version != NULL)
    snprintf(out_info->fd_version, sizeof(out_info->fd_version), "%s", recovered->fd_version);
}

uint32_t resolve_analysis_trace_start(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t block_index;
  uint32_t start;
  uint32_t candidate_start;
  if (section_analysis == NULL) return UINT32_MAX;
  block_index = section_analysis_find_block_index_containing(section_analysis, offset);
  if (block_index != SIZE_MAX && block_index < section_analysis->block_count) {
    start = section_analysis->blocks[block_index].start_offset;
    if (ctx != NULL && start < offset) {
      SectionDecodeResult decode;
      if (section_analysis_context_probe_decode(ctx, start, &decode) &&
          instruction_pop_address_reg_from_stack(&decode.instruction).ok) {
        uint32_t low = start > 32U ? (start - 32U) : 0U;
        for (candidate_start = low; candidate_start < start; ++candidate_start) {
          uint32_t cursor = candidate_start;
          while (cursor < start) {
            SectionDecodeResult prior_decode;
            if (!section_analysis_context_probe_decode(ctx, cursor, &prior_decode)) break;
            if (prior_decode.instruction.byte_count == 0U) break;
            if (cursor + (uint32_t)prior_decode.instruction.byte_count > start) break;
            cursor += (uint32_t)prior_decode.instruction.byte_count;
          }
          if (cursor == start) return candidate_start;
        }
      }
    }
    if (start < offset) return start;
  }
  start = find_enclosing_code_start(section_analysis, offset);
  if (start != UINT32_MAX && start < offset) return start;
  candidate_start = offset;
  while (candidate_start-- > ((offset > 32U) ? (offset - 32U) : 0U)) {
    uint32_t cursor = candidate_start;
    while (cursor < offset) {
      SectionDecodeResult decode;
      if (ctx == NULL || !section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U) break;
      if (cursor + (uint32_t)decode.instruction.byte_count > offset) break;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (cursor == offset) return candidate_start;
  }
  return UINT32_MAX;
}

static int operand_is_direct_control_target(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_EA) return 0;
  switch (operand->value.ea_mode) {
    case 7U:
      return operand->value.ea_reg == 0U || operand->value.ea_reg == 1U || operand->value.ea_reg == 2U;
    default:
      return 0;
  }
}

static int fixup_source_operand_is_direct_control_transfer(const M68kObject *object, const M68kFixup *fixup,
    const M68kAnalysisPolicy *analysis_policy) {
  const M68kSection *source_section;
  uint32_t width;
  uint32_t fixup_end;
  uint32_t first_candidate;
  uint32_t candidate;
  if (object == NULL || fixup == NULL || fixup->section_index >= object->section_count) return 0;
  width = fixup_width_byte_count(fixup);
  if (width == 0U) return 0;
  source_section = &object->sections[fixup->section_index];
  if (source_section->kind != M68K_SECTION_CODE || !fixup_payload_fits_section_data(source_section, fixup)) return 0;
  fixup_end = fixup->offset + width;
  first_candidate = fixup->offset > 16U ? fixup->offset - 16U : 0U;
  for (candidate = first_candidate; candidate <= fixup->offset && candidate < source_section->data_size; ++candidate) {
    M68kInstructionIR instruction;
    size_t operand_index;
    if (!decode_instruction_with_policy(source_section->data + candidate, source_section->data_size - candidate,
          candidate, analysis_policy, NULL, &instruction, m68k_diag_sink(NULL)) ||
        instruction.byte_count == 0U ||
        candidate + instruction.byte_count <= fixup->offset) {
      continue;
    }
    for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
      if (fixup->kind == M68K_FIXUP_ABS && fixup->width == M68K_FIXUP_WIDTH_32 &&
          find_instruction_operand_abs32_fixup(object, fixup->section_index, &instruction, operand_index, candidate) ==
            fixup) {
        return instruction_is_call_transfer(&instruction) ||
          instruction_is_unconditional_transfer(&instruction) ||
          is_conditional_transfer(&instruction);
      }
    }
    if ((instruction_is_call_transfer(&instruction) ||
         instruction_is_unconditional_transfer(&instruction) ||
         is_conditional_transfer(&instruction)) &&
        candidate < fixup->offset &&
        fixup_end <= candidate + instruction.byte_count) {
      return 1;
    }
  }
  return 0;
}

static int instruction_control_transfer_target( const M68kInstructionIR *instruction, const uint8_t *data, size_t size,
    uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  const M68kSimFormMetadata *metadata;
  uint8_t operand_index;
  if (!instruction_is_call_transfer(instruction) && !instruction_is_unconditional_transfer(instruction) &&
      !is_conditional_transfer(instruction)) {
    return 0;
  }
  if (instruction_branch_target_from_bytes(instruction, data, size, offset, out_target)) {
    if (*out_target < section_size && (*out_target & 1U) == 0U) return 1;
    return 0;
  }
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index >= instruction->operand_count) return 0;
  operand_index = metadata->target_operand_index;
  if (!operand_is_direct_control_target(&instruction->operands[operand_index])) return 0;
  if (!instruction_metadata_operand_target(instruction, metadata, operand_index, offset, section_size, out_target))
    return 0;
  return (*out_target & 1U) == 0U;
}

static int section_decode_cache_init(SectionDecodeCache *cache, Arena *arena, size_t section_size) {
  size_t entry_count;
  if (cache == NULL || arena == NULL) return -1;
  memset(cache, 0, sizeof(*cache));
  entry_count = section_size != 0U ? section_size : 1U;
  cache->arena = arena;
  cache->entries = (SectionDecodeCacheEntry *)arena_calloc(arena, entry_count, sizeof(*cache->entries));
  if (cache->entries == NULL) return -1;
  cache->entry_count = section_size;
  return 0;
}

static int section_decode_cache_reserve_instructions(SectionDecodeCache *cache, size_t min_capacity) {
  M68kInstructionIR *instructions;
  size_t new_capacity;
  size_t max_capacity;
  if (cache == NULL || cache->arena == NULL) return 0;
  if (min_capacity <= cache->instruction_capacity) return 1;
  max_capacity = cache->entry_count != 0U ? cache->entry_count : 1U;
  if (min_capacity > max_capacity) return 0;
  new_capacity = cache->instruction_capacity != 0U ? cache->instruction_capacity : 64U;
  if (new_capacity > max_capacity) new_capacity = max_capacity;
  while (new_capacity < min_capacity) {
    if (new_capacity >= max_capacity / 2U) {
      new_capacity = max_capacity;
      break;
    }
    new_capacity *= 2U;
  }
  instructions = (M68kInstructionIR *)arena_realloc_copy(cache->arena, cache->instructions,
    cache->instruction_capacity * sizeof(*cache->instructions), new_capacity * sizeof(*cache->instructions));
  if (instructions == NULL) return 0;
  cache->instructions = instructions;
  cache->instruction_capacity = new_capacity;
  return 1;
}

static int section_decode_cache_store_instruction(SectionDecodeCache *cache, const M68kInstructionIR *instruction,
    uint32_t *out_index) {
  uint32_t index;
  if (cache == NULL || instruction == NULL ||
      cache->instruction_count > (size_t)UINT32_MAX) {
    return 0;
  }
  if (!section_decode_cache_reserve_instructions(cache, cache->instruction_count + 1U)) return 0;
  index = (uint32_t)cache->instruction_count++;
  cache->instructions[index] = *instruction;
  if (out_index != NULL) *out_index = index;
  return 1;
}

int section_analysis_context_init(SectionAnalysisContext *ctx, const M68kObject *object, size_t section_index,
    const M68kSection *section, const M68kSectionAnalysisIR *prior_section_analyses,
    size_t prior_section_analysis_count, const M68kAnalysisPolicy *analysis_policy, Arena *arena) {
  if (ctx == NULL || section == NULL || analysis_policy == NULL || arena == NULL) return -1;
  memset(ctx, 0, sizeof(*ctx));
  ctx->object = object;
  ctx->section = section;
  ctx->section_index = section_index;
  ctx->prior_section_analyses = prior_section_analyses;
  ctx->prior_section_analysis_count = prior_section_analysis_count;
  ctx->analysis_policy = analysis_policy;
  ctx->arena = arena;
  return section_decode_cache_init(&ctx->decode_cache, arena, section->data_size);
}

static void update_findings_for_cached_instruction(const M68kInstructionIR *instruction,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings) {
  uint8_t required_cpu;
  uint8_t max_cpu;
  if (findings == NULL) return;
  required_cpu = instruction_required_cpu(instruction);
  update_required_cpu(findings, required_cpu);
  max_cpu = effective_analysis_max_cpu(analysis_policy);
  if (required_cpu > max_cpu) findings->cpu_violation_count += 1U;
}

static int section_analysis_context_decode(const SectionAnalysisContext *ctx, uint32_t offset,
    M68kAnalysisFindings *findings, SectionDecodeResult *out_result) {
  SectionDecodeCacheEntry *entry;
  int decode_result;
  if (out_result != NULL) memset(out_result, 0, sizeof(*out_result));
  if (ctx == NULL || ctx->section == NULL || ctx->analysis_policy == NULL || ctx->decode_cache.entries == NULL ||
      offset >= ctx->section->data_size || offset >= ctx->decode_cache.entry_count) {
    return 0;
  }
  entry = &ctx->decode_cache.entries[offset];
  if (entry->state == 0U) {
    M68kInstructionIR instruction;
    uint32_t instruction_index = UINT32_MAX;
    decode_result = decode_instruction_with_policy(ctx->section->data + offset, ctx->section->data_size - offset,
      offset, ctx->analysis_policy, NULL, &instruction, m68k_diag_sink(NULL));
    if (decode_result <= 0 || instruction.byte_count == 0U ||
        offset + instruction.byte_count > ctx->section->data_size) {
      entry->state = 1U;
      return 0;
    }
    if (!section_decode_cache_store_instruction(&((SectionAnalysisContext *)ctx)->decode_cache, &instruction,
          &instruction_index)) {
      entry->state = 1U;
      return 0;
    }
    entry->instruction_index = instruction_index;
    entry->state = 2U;
    if (platform_resolve_same_section_direct_target_with_fixup(ctx, &instruction, offset, &entry->explicit_target)) {
      entry->has_explicit_target = 1U;
    }
    entry->is_call = (uint8_t)instruction_is_call_transfer(&instruction);
    entry->is_unconditional_transfer = (uint8_t)instruction_is_unconditional_transfer(&instruction);
    entry->is_conditional_transfer = (uint8_t)is_conditional_transfer(&instruction);
    entry->stops_fallthrough = (uint8_t)instruction_stops_fallthrough(&instruction);
  }
  if (entry->state != 2U) return 0;
  if (entry->instruction_index >= ctx->decode_cache.instruction_count) return 0;
  update_findings_for_cached_instruction(&ctx->decode_cache.instructions[entry->instruction_index], ctx->analysis_policy,
    findings);
  if (out_result != NULL) {
    out_result->instruction = ctx->decode_cache.instructions[entry->instruction_index];
    out_result->has_explicit_target = entry->has_explicit_target;
    out_result->explicit_target = entry->explicit_target;
    out_result->is_call = entry->is_call;
    out_result->is_unconditional_transfer = entry->is_unconditional_transfer;
    out_result->is_conditional_transfer = entry->is_conditional_transfer;
    out_result->stops_fallthrough = entry->stops_fallthrough;
  }
  return 1;
}

int section_analysis_context_probe_decode(const SectionAnalysisContext *ctx, uint32_t offset,
    SectionDecodeResult *out_result) {
  M68kInstructionIR instruction;
  int decode_result;
  uint32_t explicit_target = 0U;
  uint8_t has_explicit_target = 0U;
  if (ctx != NULL && ctx->analysis_policy != NULL && ctx->decode_cache.entries != NULL &&
      offset < ctx->decode_cache.entry_count) {
    return section_analysis_context_decode(ctx, offset, NULL, out_result);
  }
  if (ctx == NULL || ctx->section == NULL || offset >= ctx->section->data_size) return 0;
  decode_result = decode_instruction_with_policy(ctx->section->data + offset, ctx->section->data_size - offset, offset,
    ctx->analysis_policy, NULL, &instruction, m68k_diag_sink(NULL));
  if (decode_result <= 0 || instruction.byte_count == 0U || offset + instruction.byte_count > ctx->section->data_size)
    return 0;
  if (platform_resolve_same_section_direct_target_with_fixup(ctx, &instruction, offset, &explicit_target)) {
    has_explicit_target = 1U;
  }
  if (out_result != NULL) {
    out_result->instruction = instruction;
    out_result->explicit_target = explicit_target;
    out_result->has_explicit_target = has_explicit_target;
    out_result->is_call = (uint8_t)instruction_is_call_transfer(&instruction);
    out_result->is_unconditional_transfer = (uint8_t)instruction_is_unconditional_transfer(&instruction);
    out_result->is_conditional_transfer = (uint8_t)is_conditional_transfer(&instruction);
    out_result->stops_fallthrough = (uint8_t)instruction_stops_fallthrough(&instruction);
  }
  return 1;
}

uint8_t section_analysis_context_backend_kind(const SectionAnalysisContext *ctx) {
  if (ctx == NULL || ctx->object == NULL) return M68K_PLATFORM_BACKEND_UNKNOWN;
  return ctx->object->platform_backend_kind;
}

const M68kObject *section_analysis_context_object(const SectionAnalysisContext *ctx) {
  return ctx != NULL ? ctx->object : NULL;
}

const M68kSection *section_analysis_context_section(const SectionAnalysisContext *ctx) {
  return ctx != NULL ? ctx->section : NULL;
}

size_t section_analysis_context_section_index(const SectionAnalysisContext *ctx) {
  return ctx != NULL ? ctx->section_index : SIZE_MAX;
}

const M68kSectionAnalysisIR *section_analysis_context_prior_section_analysis(const SectionAnalysisContext *ctx,
    size_t section_index) {
  if (ctx == NULL || ctx->prior_section_analyses == NULL || section_index >= ctx->prior_section_analysis_count)
    return NULL;
  return &ctx->prior_section_analyses[section_index];
}

const M68kAnalysisPolicy *section_analysis_context_policy(const SectionAnalysisContext *ctx) {
  return ctx != NULL ? ctx->analysis_policy : NULL;
}

Arena *section_analysis_context_arena(const SectionAnalysisContext *ctx) {
  return ctx != NULL ? ctx->arena : NULL;
}

void *section_analysis_context_platform_cache(const SectionAnalysisContext *ctx) {
  return ctx != NULL ? ctx->platform_cache : NULL;
}

void section_analysis_context_set_platform_cache(const SectionAnalysisContext *ctx, void *platform_cache) {
  if (ctx == NULL) return;
  ((SectionAnalysisContext *)ctx)->platform_cache = platform_cache;
}

static int sim_operand_direct_register_local(const M68kOperandIR *operand, uint8_t *is_address, uint8_t *reg) {
  return m68k_instruction_operand_direct_register(operand, is_address, reg);
}

int operand_is_brief_indexed_an(const M68kOperandIR *operand, uint8_t *out_base_reg,
    uint8_t *out_index_is_address, uint8_t *out_index_reg, int32_t *out_disp) {
  if (operand == NULL || out_base_reg == NULL || out_index_is_address == NULL || out_index_reg == NULL ||
      out_disp == NULL) {
    return 0;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 6U) return 0;
  *out_base_reg = operand->value.ea_reg;
  *out_index_is_address = operand->value.index_is_address;
  *out_index_reg = operand->value.index_reg;
  *out_disp = (int32_t)m68k_sign_extend32(operand->value.value, 8U);
  return 1;
}

int operand_is_indirect_an(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || out_reg == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_IND && operand->kind != M68K_ASM_OPERAND_EA) return 0;
  if (operand->value.ea_mode != 2U) return 0;
  *out_reg = operand->value.ea_reg;
  return 1;
}

static int operand_is_indirect_disp_an(const M68kOperandIR *operand, uint8_t *out_reg, int16_t *out_disp) {
  if (operand == NULL || out_reg == NULL || out_disp == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return 0;
  if (operand->value.ea_mode != 5U) return 0;
  *out_reg = operand->value.ea_reg;
  *out_disp = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

int operand_is_indirect_or_disp_an(const M68kOperandIR *operand, uint8_t *out_reg, int16_t *out_disp) {
  if (operand == NULL || out_reg == NULL || out_disp == NULL) return 0;
  if (operand_is_indirect_an(operand, out_reg)) {
    *out_disp = 0;
    return 1;
  }
  return operand_is_indirect_disp_an(operand, out_reg, out_disp);
}

int instruction_writes_data_reg_approx(const M68kInstructionIR *instruction, uint8_t reg) {
  uint8_t dest_is_address;
  uint8_t dest_reg;
  uint8_t mnemonic_id;
  if (instruction->operand_count == 0U) return 0;
  if (!sim_operand_direct_register_local(&instruction->operands[instruction->operand_count - 1U], &dest_is_address, &dest_reg) ||
      dest_is_address != 0U || dest_reg != reg) {
    return 0;
  }
  mnemonic_id = instruction->mnemonic_id;
  if (instruction_is_compare_or_test_like_local(mnemonic_id)) return 0;
  return 1;
}

int instruction_writes_address_reg_approx(const M68kInstructionIR *instruction, uint8_t reg) {
  uint8_t dest_is_address;
  uint8_t dest_reg;
  uint8_t mnemonic_id;
  if (instruction->operand_count == 0U) return 0;
  if (!sim_operand_direct_register_local(&instruction->operands[instruction->operand_count - 1U], &dest_is_address, &dest_reg) ||
      dest_is_address == 0U || dest_reg != reg) {
    return 0;
  }
  mnemonic_id = instruction->mnemonic_id;
  if (instruction_is_compare_like_address_write_local(mnemonic_id)) return 0;
  return 1;
}

size_t section_analysis_find_block_index_containing(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t low = 0U;
  size_t high;
  if (section_analysis == NULL) return SIZE_MAX;
  high = section_analysis->block_count;
  while (low < high) {
    size_t mid = low + ((high - low) / 2U);
    const M68kCfgBlockIR *block = &section_analysis->blocks[mid];
    if (offset < block->start_offset) {
      high = mid;
    } else if (offset >= block->end_offset) {
      low = mid + 1U;
    } else {
      return mid;
    }
  }
  return SIZE_MAX;
}

static int instruction_direct_target_local(const SectionAnalysisContext *ctx, const M68kInstructionIR *instruction,
    uint32_t instruction_offset, uint32_t *out_target) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  if (section == NULL || out_target == NULL || instruction_offset >= section->data_size) return 0;
  return instruction_control_transfer_target(instruction, section->data + instruction_offset,
    section->data_size - instruction_offset, instruction_offset, (uint32_t)section->data_size, out_target);
}

int platform_resolve_direct_target_with_fixup(const SectionAnalysisContext *ctx,
    const M68kInstructionIR *instruction, uint32_t instruction_offset, size_t *out_section_index,
    uint32_t *out_target) {
  const M68kObject *object;
  const M68kSection *section;
  const M68kSimFormMetadata *metadata;
  size_t section_index;
  size_t fixup_index;
  uint32_t target;
  if (out_section_index != NULL) *out_section_index = SIZE_MAX;
  if (out_target != NULL) *out_target = 0U;
  if (ctx == NULL || instruction == NULL || out_section_index == NULL || out_target == NULL) return 0;
  object = section_analysis_context_object(ctx);
  section = section_analysis_context_section(ctx);
  section_index = section_analysis_context_section_index(ctx);
  if (section == NULL || section_index == SIZE_MAX) return 0;
  metadata = instruction_sim_metadata(instruction);
  if (object != NULL && section_index < object->section_count) {
    if (metadata != NULL && metadata->target_operand_index != 0xFFU &&
        metadata->target_operand_index < instruction->operand_count) {
      const M68kFixup *target_fixup = find_instruction_target_fixup(object, section_index, instruction,
        metadata->target_operand_index, instruction_offset, section_analysis_context_policy(ctx));
      if (target_fixup != NULL && target_fixup->has_target_section &&
          target_fixup->target_section_index < object->section_count &&
          fixup_target_offset_local(object, target_fixup, &target)) {
        const M68kSection *target_section = &object->sections[target_fixup->target_section_index];
        if (target < target_section->data_size) {
          *out_section_index = target_fixup->target_section_index;
          *out_target = target;
          return 1;
        }
      }
    }
    for (fixup_index = 0U; fixup_index < object->fixup_count; ++fixup_index) {
      const M68kFixup *fixup = &object->fixups[fixup_index];
      const M68kSection *target_section;
      uint32_t width = fixup_width_byte_count(fixup);
      uint32_t fixup_end;
      if (fixup->section_index != section_index || !fixup->has_target_section ||
          fixup->target_section_index >= object->section_count || width == 0U ||
          !fixup_source_operand_is_direct_control_transfer(object, fixup, section_analysis_context_policy(ctx))) {
        continue;
      }
      if (!fixup_payload_fits_section_data(section, fixup)) continue;
      fixup_end = fixup->offset + width;
      if (fixup->offset < instruction_offset || fixup_end > instruction_offset + instruction->byte_count) continue;
      target_section = &object->sections[fixup->target_section_index];
      if (!fixup_target_offset_local(object, fixup, &target)) continue;
      if (target >= target_section->data_size) continue;
      *out_section_index = fixup->target_section_index;
      *out_target = target;
      return 1;
    }
  }
  if (metadata != NULL && metadata->target_operand_index != 0xFFU &&
      metadata->target_operand_index < instruction->operand_count &&
      absolute_long_operand_should_stay_numeric(object, section_index, instruction, metadata->target_operand_index,
        instruction_offset)) {
    return 0;
  }
  if (instruction_has_unrelocated_absolute_long_operand(object, section_index, instruction, instruction_offset)) return 0;
  if (instruction_direct_target_local(ctx, instruction, instruction_offset, &target) && target < section->data_size) {
    *out_section_index = section_index;
    *out_target = target;
    return 1;
  }
  return 0;
}

static int platform_resolve_same_section_direct_target_with_fixup(const SectionAnalysisContext *ctx,
    const M68kInstructionIR *instruction, uint32_t instruction_offset, uint32_t *out_target) {
  size_t section_index;
  size_t target_section_index;
  uint32_t target;
  if (out_target != NULL) *out_target = 0U;
  if (ctx == NULL || instruction == NULL || out_target == NULL) return 0;
  section_index = section_analysis_context_section_index(ctx);
  if (!platform_resolve_direct_target_with_fixup(ctx, instruction, instruction_offset, &target_section_index, &target))
    return 0;
  if (target_section_index != section_index) return 0;
  *out_target = target;
  return 1;
}

int operand_raw_constant_value_local(const M68kOperandIR *operand, int32_t *out_value) {
  if (out_value != NULL) *out_value = 0;
  if (operand == NULL || out_value == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_IMM ||
      ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
       operand->value.ea_mode == 7U && operand->value.ea_reg == 4U)) {
    *out_value = (int32_t)operand->value.value;
    return 1;
  }
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 7U && (operand->value.ea_reg == 0U || operand->value.ea_reg == 1U)) {
    *out_value = (int32_t)operand->value.value;
    return 1;
  }
  return 0;
}

static int operand_address_reg_index_local_core(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || out_reg == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) {
    *out_reg = operand->value.reg;
    return 1;
  }
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 1U) {
    *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static void platform_decode_movem_reg_bit(unsigned bit, uint8_t *out_reg_kind, uint8_t *out_reg_index) {
  if (out_reg_kind != NULL) *out_reg_kind = bit < 8U ? 1U : 2U;
  if (out_reg_index != NULL) *out_reg_index = bit < 8U ? (uint8_t)bit : (uint8_t)(bit - 8U);
}

static size_t platform_popcount16(uint16_t value) {
  size_t count = 0U;
  while (value != 0U) {
    count += (size_t)(value & 1U);
    value = (uint16_t)(value >> 1);
  }
  return count;
}

static uint8_t instruction_size_suffix_width_local(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0U;
  if (instruction->size_suffix == 'b') return 1U;
  if (instruction->size_suffix == 'w') return 2U;
  if (instruction->size_suffix == 'l') return 4U;
  return 0U;
}

static uint8_t instruction_operand_ea_shape_from_metadata(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, uint8_t operand_index) {
  const M68kOperandIR *operand;
  uint8_t shape;
  if (instruction == NULL || metadata == NULL || operand_index >= instruction->operand_count || operand_index >= 4U)
    return M68K_SIM_EA_SHAPE_NONE;
  shape = metadata->operand_ea_address_shapes[operand_index];
  if (shape != M68K_SIM_EA_SHAPE_NONE) return shape;
  operand = &instruction->operands[operand_index];
  if (operand->kind == M68K_ASM_OPERAND_PREDEC) return M68K_SIM_EA_SHAPE_PREDECREMENT;
  if (operand->kind == M68K_ASM_OPERAND_POSTINC) return M68K_SIM_EA_SHAPE_POSTINCREMENT;
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA)) {
    switch (operand->value.ea_mode) {
      case 2: return M68K_SIM_EA_SHAPE_INDIRECT;
      case 3: return M68K_SIM_EA_SHAPE_POSTINCREMENT;
      case 4: return M68K_SIM_EA_SHAPE_PREDECREMENT;
      case 5: return M68K_SIM_EA_SHAPE_DISPLACEMENT;
      case 6: return M68K_SIM_EA_SHAPE_INDEX;
      default: break;
    }
  }
  return M68K_SIM_EA_SHAPE_NONE;
}

int instruction_pushes_long_stack_arg_local(const M68kInstructionIR *instruction, const M68kOperandIR **out_operand) {
  if (out_operand != NULL) *out_operand = NULL;
  if (instruction == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction->operand_count == 1U) {
    if (out_operand != NULL) *out_operand = &instruction->operands[0];
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U &&
      ((instruction->operands[1].kind == M68K_ASM_OPERAND_PREDEC && instruction->operands[1].value.ea_reg == 7U) ||
       ((instruction->operands[1].kind == M68K_ASM_OPERAND_EA ||
         instruction->operands[1].kind == M68K_ASM_OPERAND_BF_EA) &&
        instruction->operands[1].value.ea_mode == 4U && instruction->operands[1].value.ea_reg == 7U))) {
    if (out_operand != NULL) *out_operand = &instruction->operands[0];
    return 1;
  }
  return 0;
}

static int platform_local_stack_wrapper_signature_add_arg(PlatformLocalStackWrapperSignature *signature,
    uint8_t reg_kind, uint8_t reg_index, int32_t caller_stack_offset) {
  size_t index;
  if (signature == NULL || reg_kind == 0U || reg_index >= 8U || caller_stack_offset <= 0 ||
      caller_stack_offset > UINT16_MAX) {
    return 0;
  }
  for (index = 0U; index < signature->arg_count; ++index) {
    if (signature->args[index].reg_kind == reg_kind && signature->args[index].reg_index == reg_index) {
      signature->args[index].caller_stack_offset = (uint16_t)caller_stack_offset;
      return 1;
    }
  }
  if (signature->arg_count >= PLATFORM_LOCAL_STACK_WRAPPER_ARG_MAP_CAPACITY) return 0;
  signature->args[signature->arg_count].reg_kind = reg_kind;
  signature->args[signature->arg_count].reg_index = reg_index;
  signature->args[signature->arg_count].caller_stack_offset = (uint16_t)caller_stack_offset;
  ++signature->arg_count;
  return 1;
}

int platform_analyze_local_stack_wrapper_signature(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t target_offset, uint16_t initial_a6_base_id,
    PlatformStackWrapperLookupBaseSlotFn lookup_base_slot, PlatformStackWrapperLookupOperandBaseFn lookup_operand_base,
    PlatformStackWrapperResolveCallFn resolve_call, void *user_ctx,
    PlatformLocalStackWrapperSignature *out_signature) {
  const M68kSection *section;
  int32_t stack_delta = 0;
  uint32_t cursor;
  uint16_t addr_reg_base_ids[8];
  if (out_signature != NULL) memset(out_signature, 0, sizeof(*out_signature));
  if (ctx == NULL || section_analysis == NULL || out_signature == NULL || resolve_call == NULL)
    return 0;
  section = section_analysis_context_section(ctx);
  if (section == NULL) return 0;
  memset(addr_reg_base_ids, 0, sizeof(addr_reg_base_ids));
  addr_reg_base_ids[6] = initial_a6_base_id;
  cursor = target_offset;
  while (cursor < section->data_size && cursor - target_offset < 128U) {
    SectionDecodeResult decode;
    M68kInstructionIR *instruction;
    uint8_t reg;
    uint8_t base_reg;
    const M68kOperandIR *source = NULL;
    int16_t displacement;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = &decode.instruction;
    if (instruction->byte_count == 0U) break;
    if (decode.is_call) {
      out_signature->call_entry = resolve_call(user_ctx, ctx, section_analysis, cursor, instruction, addr_reg_base_ids);
      return out_signature->call_entry != NULL;
    }
    if (!instruction_known_stack_delta_from_metadata(instruction, &stack_delta)) return 0;
    if (instruction_is_data_move(instruction, &reg, &source) && source != NULL &&
        operand_is_indirect_or_disp_an(source, &base_reg, &displacement) &&
        (source->kind == M68K_ASM_OPERAND_EA || source->kind == M68K_ASM_OPERAND_BF_EA) &&
        base_reg == 7U) {
      platform_local_stack_wrapper_signature_add_arg(out_signature, 1U, reg, (int32_t)displacement - stack_delta);
    } else if (instruction_is_address_move(instruction, &reg, &source) && source != NULL &&
        operand_is_indirect_or_disp_an(source, &base_reg, &displacement) &&
        (source->kind == M68K_ASM_OPERAND_EA || source->kind == M68K_ASM_OPERAND_BF_EA) &&
        base_reg == 7U) {
      platform_local_stack_wrapper_signature_add_arg(out_signature, 2U, reg, (int32_t)displacement - stack_delta);
    } else if (instruction_is_address_move(instruction, &reg, &source) && source != NULL && reg < 8U) {
      uint8_t source_reg;
      int16_t slot_disp;
      size_t source_index = (size_t)(source - instruction->operands);
      if (operand_address_reg_index_local_core(source, &source_reg) && source_reg < 8U) {
        addr_reg_base_ids[reg] = addr_reg_base_ids[source_reg];
      } else if (operand_is_app_base_disp_ea(source, 6U, &slot_disp) && lookup_base_slot != NULL) {
        addr_reg_base_ids[reg] = lookup_base_slot(user_ctx, ctx, section_analysis, slot_disp);
      } else if (lookup_operand_base != NULL && source_index < instruction->operand_count) {
        addr_reg_base_ids[reg] = lookup_operand_base(user_ctx, ctx, section_analysis, cursor, instruction,
          (uint8_t)source_index);
      } else {
        addr_reg_base_ids[reg] = 0U;
      }
    } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
        instruction->operand_count == 2U &&
        (instruction->operands[0].kind == M68K_ASM_OPERAND_EA ||
         instruction->operands[0].kind == M68K_ASM_OPERAND_BF_EA) &&
        instruction->operands[0].value.ea_mode == 5U && instruction->operands[0].value.ea_reg == 7U &&
        instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      unsigned bit;
      int32_t load_disp = (int16_t)(instruction->operands[0].value.value & 0xFFFFU);
      int32_t loaded_bytes = 0;
      for (bit = 0U; bit < 16U; ++bit) {
        uint8_t reg_kind;
        uint8_t reg_index;
        if ((instruction->operands[1].value.value & (uint32_t)(1U << bit)) == 0U) continue;
        platform_decode_movem_reg_bit(bit, &reg_kind, &reg_index);
        platform_local_stack_wrapper_signature_add_arg(out_signature, reg_kind, reg_index,
          load_disp - stack_delta + loaded_bytes);
        loaded_bytes += 4;
      }
    }
    if (instruction_stops_fallthrough(instruction)) return 0;
    cursor += (uint32_t)instruction->byte_count;
  }
  return 0;
}

int platform_analyze_local_stack_wrapper_signature_at(const SectionAnalysisContext *ctx,
    size_t target_section_index, uint32_t target_offset, uint16_t initial_a6_base_id,
    PlatformStackWrapperLookupBaseSlotFn lookup_base_slot, PlatformStackWrapperLookupOperandBaseFn lookup_operand_base,
    PlatformStackWrapperResolveCallFn resolve_call, void *user_ctx,
    PlatformLocalStackWrapperSignature *out_signature) {
  const M68kObject *object;
  const M68kSection *target_section;
  const M68kSectionAnalysisIR *target_analysis;
  size_t current_section_index;
  if (out_signature != NULL) memset(out_signature, 0, sizeof(*out_signature));
  if (ctx == NULL || out_signature == NULL) return 0;
  object = section_analysis_context_object(ctx);
  current_section_index = section_analysis_context_section_index(ctx);
  if (object == NULL || target_section_index >= object->section_count) return 0;
  target_section = &object->sections[target_section_index];
  if (target_section_index == current_section_index) {
    target_analysis = section_analysis_context_prior_section_analysis(ctx, target_section_index);
    if (target_analysis == NULL) return 0;
    return platform_analyze_local_stack_wrapper_signature(ctx, target_analysis, target_offset, initial_a6_base_id,
      lookup_base_slot, lookup_operand_base, resolve_call, user_ctx, out_signature);
  }
  target_analysis = section_analysis_context_prior_section_analysis(ctx, target_section_index);
  if (target_analysis == NULL) return 0;
  {
    Arena *arena = arena_create(4096U);
    SectionAnalysisContext target_ctx;
    int result = 0;
    if (arena == NULL) return 0;
    if (section_analysis_context_init(&target_ctx, object, target_section_index, target_section,
        ctx->prior_section_analyses, ctx->prior_section_analysis_count, section_analysis_context_policy(ctx), arena) == 0) {
      result = platform_analyze_local_stack_wrapper_signature(&target_ctx, target_analysis, target_offset,
        initial_a6_base_id, lookup_base_slot, lookup_operand_base, resolve_call, user_ctx, out_signature);
    }
    arena_destroy(arena);
    return result;
  }
}

static uint32_t find_enclosing_code_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  uint32_t cursor;
  if (section_analysis == NULL || section_analysis->certain_code_start == NULL || section_analysis->certain_code_byte == NULL ||
      offset >= section_analysis->certain_code_size || section_analysis->certain_code_byte[offset] == 0U)
    return UINT32_MAX;
  cursor = offset;
  while (cursor > 0U && section_analysis->certain_code_start[cursor] == 0U &&
      section_analysis->certain_code_byte[cursor - 1U] != 0U)
    --cursor;
  return section_analysis->certain_code_start[cursor] != 0U ? cursor : UINT32_MAX;
}

static const M68kFixup *find_section_fixup_at_offset(const M68kObject *object, size_t section_index, uint32_t offset,
    M68kFixupWidth width) {
  size_t fixup_index;
  if (object == NULL) return NULL;
  for (fixup_index = 0; fixup_index < object->fixup_count; ++fixup_index) {
    const M68kFixup *fixup = &object->fixups[fixup_index];
    if (fixup->section_index == section_index && fixup->offset == offset && fixup->kind == M68K_FIXUP_ABS &&
        fixup->width == width && fixup->has_target_section) {
      return fixup;
    }
  }
  return NULL;
}

static const M68kFixup *find_instruction_operand_abs32_fixup(const M68kObject *object, size_t section_index,
    const M68kInstructionIR *instruction, size_t operand_index, uint32_t instruction_offset) {
  M68kInstructionIR layout_instruction_storage;
  uint16_t asm_form_index;
  const M68kInstructionIR *layout_instruction;
  const M68kAsmFormDef *form;
  char size_suffix;
  size_t word_index;
  size_t extension_index;
  if (object == NULL || instruction == NULL || section_index >= object->section_count ||
      operand_index >= instruction->operand_count) {
    return NULL;
  }
  asm_form_index = instruction_assembler_form_index_local(instruction, &layout_instruction_storage);
  layout_instruction = &layout_instruction_storage;
  form = &g_m68k_asm_forms[asm_form_index];
  if (form->mnemonic_id != M68K_ASM_MNEMONIC_NONE) {
    size_suffix = instruction_effective_size_suffix_local(layout_instruction, form);
    word_index = 1U + form->bound_word_count;
    for (extension_index = 0; extension_index < form->extension_count; ++extension_index) {
      const M68kAsmExtensionDef *extension = &g_m68k_asm_extensions[form->extension_start + extension_index];
      const M68kAsmOperandValue *operand = &layout_instruction->operands[extension->operand_index].value;
      switch (extension->kind) {
      case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
        if (operand_uses_single_word_extension_local(operand)) word_index += 1U;
        break;
      case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
        if (operand_uses_long_address_extension_local(operand)) {
          if (extension->operand_index == operand_index) {
            const M68kFixup *fixup = find_section_fixup_at_offset(object, section_index,
              instruction_offset + (uint32_t)(word_index * 2U), M68K_FIXUP_WIDTH_32);
            if (fixup != NULL) return fixup;
          }
          word_index += 2U;
        }
        break;
      case M68K_ASM_EXTENSION_EA_IMMEDIATE:
        if (operand_uses_immediate_extension_local(operand)) {
          size_t extension_words = m68k_asm_operand_extension_word_count(asm_form_index, operand, size_suffix);
          if (extension->operand_index == operand_index && extension_words >= 2U) {
            const M68kFixup *fixup = find_section_fixup_at_offset(object, section_index,
              instruction_offset + (uint32_t)(word_index * 2U), M68K_FIXUP_WIDTH_32);
            if (fixup != NULL) return fixup;
          }
          word_index += extension_words;
        }
        break;
      case M68K_ASM_EXTENSION_EA_INDEX:
        word_index += m68k_asm_operand_extension_word_count(asm_form_index, operand, size_suffix);
        break;
      case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
      case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
      case M68K_ASM_EXTENSION_DISP16_ALWAYS:
        word_index += 1U;
        break;
      default:
        break;
      }
    }
  }
  {
    const M68kOperandIR *ir_operand = &instruction->operands[operand_index];
    uint32_t scan_offset;
    if (ir_operand->kind == M68K_ASM_OPERAND_EA && ir_operand->value.ea_mode == 7U &&
        ir_operand->value.ea_reg == 1U && instruction->byte_count >= 6U) {
      for (scan_offset = instruction_offset + 2U; scan_offset + 4U <= instruction_offset + instruction->byte_count;
           scan_offset += 2U) {
        const M68kFixup *fixup = find_section_fixup_at_offset(object, section_index, scan_offset, M68K_FIXUP_WIDTH_32);
        if (fixup != NULL) return fixup;
      }
    }
  }
  return NULL;
}

static const M68kFixup *find_instruction_target_fixup(const M68kObject *object, size_t section_index,
    const M68kInstructionIR *instruction, size_t operand_index, uint32_t instruction_offset,
    const M68kAnalysisPolicy *analysis_policy) {
  const M68kFixup *fixup;
  const M68kSimFormMetadata *metadata;
  size_t fixup_index;
  if (object == NULL || instruction == NULL || section_index >= object->section_count ||
      operand_index >= instruction->operand_count)
    return NULL;
  fixup = find_instruction_operand_abs32_fixup(object, section_index, instruction, operand_index, instruction_offset);
  if (fixup != NULL) return fixup;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index != operand_index) return NULL;
  if (!instruction_is_call_transfer(instruction) && !instruction_is_unconditional_transfer(instruction) &&
      !is_conditional_transfer(instruction))
    return NULL;
  for (fixup_index = 0U; fixup_index < object->fixup_count; ++fixup_index) {
    uint32_t width;
    uint32_t fixup_end;
    fixup = &object->fixups[fixup_index];
    width = fixup_width_byte_count(fixup);
    if (fixup->section_index != section_index || width == 0U ||
        !fixup_payload_fits_section_data(&object->sections[section_index], fixup))
      continue;
    fixup_end = fixup->offset + width;
    if (fixup->offset < instruction_offset || fixup_end > instruction_offset + instruction->byte_count) continue;
    if (fixup_source_operand_is_direct_control_transfer(object, fixup, analysis_policy)) return fixup;
  }
  return NULL;
}

int instruction_operand_absolute_target_ref(const SectionAnalysisContext *ctx, const M68kInstructionIR *instruction,
    size_t operand_index, uint32_t instruction_offset, size_t *out_section_index, uint32_t *out_target_offset) {
  const M68kObject *object = section_analysis_context_object(ctx);
  const M68kSection *section = section_analysis_context_section(ctx);
  size_t section_index = section_analysis_context_section_index(ctx);
  const M68kOperandIR *operand;
  const M68kSimFormMetadata *metadata;
  const M68kFixup *fixup;
  uint32_t target;
  if (out_section_index != NULL) *out_section_index = SIZE_MAX;
  if (out_target_offset != NULL) *out_target_offset = UINT32_MAX;
  if (ctx == NULL || instruction == NULL || section == NULL || operand_index >= instruction->operand_count ||
      section_index == SIZE_MAX) {
    return 0;
  }
  operand = &instruction->operands[operand_index];
  fixup = find_instruction_operand_abs32_fixup(object, section_index, instruction, operand_index, instruction_offset);
  if (fixup != NULL && fixup->has_target_section && fixup_target_offset_local(object, fixup, &target)) {
    if (out_section_index != NULL) *out_section_index = fixup->target_section_index;
    if (out_target_offset != NULL) *out_target_offset = target;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_IMM && operand->value.value < section->data_size) {
    if (out_section_index != NULL) *out_section_index = section_index;
    if (out_target_offset != NULL) *out_target_offset = operand->value.value;
    return 1;
  }
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 7U) {
    if ((operand->value.ea_reg == 0U || operand->value.ea_reg == 1U) &&
        operand->value.value < section->data_size) {
      if (out_section_index != NULL) *out_section_index = section_index;
      if (out_target_offset != NULL) *out_target_offset = operand->value.value;
      return 1;
    }
    if (operand->value.ea_reg == 2U) {
      target = (uint32_t)((int32_t)instruction_offset + 2 + (int32_t)operand->value.value);
      if (target < section->data_size) {
        if (out_section_index != NULL) *out_section_index = section_index;
        if (out_target_offset != NULL) *out_target_offset = target;
        return 1;
      }
    }
  }
  metadata = instruction_sim_metadata(instruction);
  if (metadata != NULL && operand_index <= UINT8_MAX &&
      instruction_render_operand_target(instruction, metadata, (uint8_t)operand_index, instruction_offset,
        (uint32_t)section->data_size, &target)) {
    if (out_section_index != NULL) *out_section_index = section_index;
    if (out_target_offset != NULL) *out_target_offset = target;
    return 1;
  }
  return 0;
}

static int instruction_known_stack_delta_from_metadata(const M68kInstructionIR *instruction, int32_t *inout_stack_delta) {
  const M68kSimFormMetadata *metadata;
  uint8_t effect_index;
  if (instruction == NULL || inout_stack_delta == NULL) return 0;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL) return !instruction_writes_address_reg_approx(instruction, 7U);
  if (metadata->multi_transfer_direction != M68K_SIM_MULTI_NONE) {
    uint8_t address_index = metadata->address_operand_index;
    uint8_t reglist_index = metadata->reglist_operand_index;
    uint8_t address_shape;
    uint32_t bytes;
    if (address_index >= instruction->operand_count || reglist_index >= instruction->operand_count ||
        instruction->operands[reglist_index].kind != M68K_ASM_OPERAND_REGLIST) {
      return 0;
    }
    address_shape = instruction_operand_ea_shape_from_metadata(instruction, metadata, address_index);
    bytes = (uint32_t)platform_popcount16((uint16_t)instruction->operands[reglist_index].value.value) *
      (uint32_t)instruction_size_suffix_width_local(instruction);
    if (bytes == 0U) return 0;
    if (metadata->multi_transfer_direction == M68K_SIM_MULTI_REGISTER_TO_MEMORY &&
        metadata->multi_transfer_address_update == M68K_SIM_MULTI_UPDATE_PREDECREMENT_IF_PREDEC &&
        address_shape == M68K_SIM_EA_SHAPE_PREDECREMENT &&
        instruction->operands[address_index].value.ea_reg == 7U) {
      *inout_stack_delta += (int32_t)bytes;
      return 1;
    }
    if (metadata->multi_transfer_direction == M68K_SIM_MULTI_MEMORY_TO_REGISTER &&
        metadata->multi_transfer_address_update == M68K_SIM_MULTI_UPDATE_POSTINCREMENT_IF_POSTINC &&
        address_shape == M68K_SIM_EA_SHAPE_POSTINCREMENT &&
        instruction->operands[address_index].value.ea_reg == 7U) {
      *inout_stack_delta -= (int32_t)bytes;
      return 1;
    }
  }
  if (metadata->sp_effect_count == 0U && instruction_writes_address_reg_approx(instruction, 7U)) return 0;
  for (effect_index = 0U; effect_index < metadata->sp_effect_count; ++effect_index) {
    const M68kSimSpEffectDef *effect = &g_m68k_sim_sp_effects[metadata->sp_effect_start + effect_index];
    switch (effect->action) {
      case M68K_SIM_SP_DECREMENT:
      case M68K_SIM_SP_STORE_REG_TO_STACK:
        if (effect->bytes <= 0) return 0;
        *inout_stack_delta += effect->bytes;
        break;
      case M68K_SIM_SP_INCREMENT:
      case M68K_SIM_SP_LOAD_FROM_STACK_TO_REG:
        if (effect->bytes <= 0) return 0;
        *inout_stack_delta -= effect->bytes;
        break;
      case M68K_SIM_SP_ADJUST:
      case M68K_SIM_SP_SAVE_TO_REG:
      case M68K_SIM_SP_LOAD_FROM_REG:
        return 0;
      default:
        return 0;
    }
  }
  return 1;
}

