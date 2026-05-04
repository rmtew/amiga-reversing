#include "m68k_render_lookup_internal.h"

/* Shared platform/source-analysis enrichment for M68kRenderLookup. */
static const char *amiga_input_type_or_struct_name(const AmigaOsCallInputInfo *input) {
  const char *name;
  if (input == NULL) return NULL;
  if (input->struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, input->struct_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  if (input->type_id != AMIGA_OS_TYPE_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, input->type_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  return NULL;
}

static const char *amiga_output_type_or_struct_name(const AmigaOsCallOutputInfo *output) {
  const char *name;
  if (output == NULL) return NULL;
  if (output->struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, output->struct_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  if (output->type_id != AMIGA_OS_TYPE_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, output->type_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  return NULL;
}

static void typed_stored_value_platform_names(const M68kRenderTypedStoredValue *value, const char **out_symbol_name,
    const char **out_type_name, const char **out_semantic_kind, const char **out_value_domain_name) {
  const AmigaOsCallOutputInfo *output;
  if (out_symbol_name != NULL) *out_symbol_name = NULL;
  if (out_type_name != NULL) *out_type_name = NULL;
  if (out_semantic_kind != NULL) *out_semantic_kind = NULL;
  if (out_value_domain_name != NULL) *out_value_domain_name = NULL;
  if (value == NULL) return;
  output = value->output;
  if (output != NULL) {
    if (out_symbol_name != NULL) *out_symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
    if (out_type_name != NULL) *out_type_name = amiga_output_type_or_struct_name(output);
    if (out_semantic_kind != NULL)
      *out_semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
    if (out_value_domain_name != NULL)
      *out_value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
  } else if (value->struct_id != AMIGA_OS_STRUCT_ID_NONE && out_type_name != NULL) {
    *out_type_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, value->struct_id);
  }
}

static int format_amiga_call_input_note_render(uint16_t stack_offset, const AmigaOsCallInputInfo *input,
    char *buf, size_t buf_size) {
  const char *symbol_name;
  const char *type_name;
  const char *semantic_kind;
  const char *value_domain_name;
  size_t used;
  if (buf == NULL || buf_size == 0U || input == NULL || stack_offset == 0U) return 0;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id);
  type_name = amiga_input_type_or_struct_name(input);
  semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, input->semantic_kind_id);
  value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input->value_domain_id);
  snprintf(buf, buf_size, "KNOWN: arg +%u", (unsigned)stack_offset);
  used = strlen(buf);
  if (symbol_name != NULL && symbol_name[0] != '\0' && used + strlen(symbol_name) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", symbol_name);
    used = strlen(buf);
  }
  if (type_name != NULL && type_name[0] != '\0' && used + strlen(type_name) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", type_name);
    used = strlen(buf);
  }
  if (semantic_kind != NULL && semantic_kind[0] != '\0' && used + strlen(semantic_kind) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", semantic_kind);
    used = strlen(buf);
  }
  if (value_domain_name != NULL && value_domain_name[0] != '\0' &&
      used + strlen(value_domain_name) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", value_domain_name);
  }
  return 1;
}

static int operand_is_predec_a7_local(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_PREDEC) return operand->value.reg == 7U;
  return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 4U && operand->value.ea_reg == 7U;
}

static int instruction_is_long_stack_push_for_comment(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction->operand_count == 1U) return 1;
  return instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
    instruction->operand_count == 2U && operand_is_predec_a7_local(&instruction->operands[1]);
}

static uint16_t reglist_long_stack_size_local(uint32_t mask) {
  uint16_t size = 0U;
  unsigned bit;
  for (bit = 0U; bit < 16U; ++bit) {
    if ((mask & (1UL << bit)) != 0U) size = (uint16_t)(size + 4U);
  }
  return size;
}

static int operand_is_stack_displacement_local(const M68kOperandIR *operand, int16_t *out_displacement);
static int typed_storage_keys_match(const M68kRenderTypedStorageSlot *slot, uint8_t kind, size_t section_index,
    int32_t displacement, uint32_t address);
static void typed_memory_base_clear(M68kRenderTypedMemoryBaseValue *value);
static int candidate_loads_data_target_to_address_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg);
static int candidate_loads_runtime_address_ref_target_to_address_reg(const M68kRenderLookup *lookup,
    size_t section_index, const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg);
static int accepted_range_has_code_byte(const uint8_t *accepted_bytes, uint32_t section_size,
    uint32_t offset, uint32_t size);

#define M68K_RENDER_TYPED_FLOW_DEFAULT_NODE_VISIT_LIMIT 2000000U
#define M68K_RENDER_TYPED_FLOW_DEFAULT_ITERATION_LIMIT 64U

static int instruction_stack_delta_for_comment(const M68kInstructionIR *instruction, int32_t *out_delta) {
  size_t operand_index;
  if (out_delta != NULL) *out_delta = 0;
  if (instruction == NULL || out_delta == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction->operand_count == 1U) {
    *out_delta = 4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && operand_is_predec_a7_local(&instruction->operands[1])) {
    *out_delta = 4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && operand_is_postinc_a7_local(&instruction->operands[0])) {
    *out_delta = -4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U) {
    if (instruction->operands[0].kind == M68K_ASM_OPERAND_REGLIST &&
        operand_is_predec_a7_local(&instruction->operands[1])) {
      *out_delta = reglist_long_stack_size_local(instruction->operands[0].value.value);
      return 1;
    }
    if (operand_is_postinc_a7_local(&instruction->operands[0]) &&
        instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      *out_delta = -(int32_t)reglist_long_stack_size_local(instruction->operands[1].value.value);
      return 1;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      operand_is_address_register_local(&instruction->operands[1], 7U)) {
    int16_t displacement = 0;
    if (!operand_is_stack_displacement_local(&instruction->operands[0], &displacement)) return 0;
    *out_delta = -(int32_t)displacement;
    return 1;
  }
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADD ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDA ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDI ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDQ ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ) &&
      instruction->operand_count == 2U && operand_is_address_register_local(&instruction->operands[1], 7U)) {
    uint32_t value = 0U;
    if (!operand_is_immediate_value_local(&instruction->operands[0], &value) || value > INT16_MAX) return 0;
    *out_delta = (instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ)
      ? (int32_t)value
      : -(int32_t)value;
    return 1;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    if (operand_is_predec_a7_local(&instruction->operands[operand_index]) ||
        operand_is_postinc_a7_local(&instruction->operands[operand_index])) {
      return 0;
    }
  }
  if (instruction->operand_count > 0U &&
      operand_is_address_register_local(&instruction->operands[instruction->operand_count - 1U], 7U)) {
    return 0;
  }
  return 1;
}

static int operand_is_stack_displacement_local(const M68kOperandIR *operand, int16_t *out_displacement) {
  uint8_t reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (!operand_is_address_displacement_local(operand, &reg, &displacement) || reg != 7U) return 0;
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static int render_lookup_add_stack_load_input_comments(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, const M68kInstructionIR *instruction, const AmigaOsLibraryVectorInfo *vector,
    uint16_t stack_frame_depth) {
  int16_t displacement = 0;
  if (lookup == NULL || instruction == NULL || vector == NULL) return 0;
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->size_suffix == 'l' && instruction->operand_count == 2U &&
      operand_is_stack_displacement_local(&instruction->operands[0], &displacement)) {
    uint8_t reg = 0U;
    uint8_t reg_kind = 0U;
    const AmigaOsCallInputInfo *input;
    char comment[192];
    if (operand_is_data_register_local(&instruction->operands[1], &reg)) reg_kind = 1U;
    else if (instruction->operands[1].kind == M68K_ASM_OPERAND_AN) {
      reg = (uint8_t)instruction->operands[1].value.reg;
      reg_kind = 2U;
    }
    input = amiga_vector_input_by_register(vector, reg_kind, reg);
    if (input != NULL && displacement > (int16_t)stack_frame_depth &&
        format_amiga_call_input_note_render((uint16_t)(displacement - (int16_t)stack_frame_depth), input,
          comment, sizeof(comment))) {
      return render_lookup_add_instruction_comment(lookup, section_index, offset, comment) == 0;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && operand_is_stack_displacement_local(&instruction->operands[0], &displacement) &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST && displacement > (int16_t)stack_frame_depth) {
    uint32_t mask = instruction->operands[1].value.value;
    uint16_t stack_offset = (uint16_t)(displacement - (int16_t)stack_frame_depth);
    unsigned bit;
    int added = 0;
    for (bit = 0U; bit < 16U; ++bit) {
      uint8_t reg_kind;
      uint8_t reg_index;
      const AmigaOsCallInputInfo *input;
      char comment[192];
      if ((mask & (1UL << bit)) == 0U) continue;
      reg_kind = bit < 8U ? 1U : 2U;
      reg_index = (uint8_t)(bit < 8U ? bit : bit - 8U);
      input = amiga_vector_input_by_register(vector, reg_kind, reg_index);
      if (input != NULL && format_amiga_call_input_note_render(stack_offset, input, comment, sizeof(comment)) &&
          render_lookup_add_instruction_comment(lookup, section_index, offset, comment) != 0) {
        return 0;
      }
      if (input != NULL) added = 1;
      stack_offset = (uint16_t)(stack_offset + 4U);
    }
    return added;
  }
  return 0;
}

static const M68kDecodeCandidate *find_previous_accepted_candidate(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t before_offset) {
  uint32_t probe;
  if (section == NULL || accepted_start == NULL || before_offset == 0U) return NULL;
  probe = before_offset;
  while (probe > 0U) {
    --probe;
    if (accepted_start_at(section, accepted_start, probe)) return find_candidate_at_offset_local(section, probe);
  }
  return NULL;
}

static int stack_frame_depth_before_candidate(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    uint32_t before_offset, uint16_t *out_depth) {
  const M68kDecodeCandidate *candidates[32];
  size_t count = 0U;
  int32_t depth = 0;
  uint32_t cursor;
  if (out_depth != NULL) *out_depth = 0U;
  if (section == NULL || accepted_start == NULL || out_depth == NULL) return 0;
  cursor = before_offset;
  while (count < sizeof(candidates) / sizeof(candidates[0])) {
    const M68kDecodeCandidate *candidate = find_previous_accepted_candidate(section, accepted_start, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (candidate->offset + candidate->byte_count != cursor) break;
    candidates[count++] = candidate;
    cursor = candidate->offset;
  }
  while (count > 0U) {
    M68kInstructionIR instruction;
    int32_t delta = 0;
    --count;
    if (m68k_decode_candidate_to_instruction(candidates[count], &instruction) != 0) return 0;
    if (!instruction_stack_delta_for_comment(&instruction, &delta)) return 0;
    depth += delta;
    if (depth < 0 || depth > UINT16_MAX) return 0;
  }
  *out_depth = (uint16_t)depth;
  return 1;
}

static int render_lookup_add_call_setup_comments_for_vector(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t call_offset,
    const AmigaOsLibraryVectorInfo *vector, int allow_register_stack_loads) {
  uint32_t cursor;
  uint16_t push_stack_offset = 4U;
  size_t scan_count = 0U;
  if (lookup == NULL || section == NULL || accepted_start == NULL || vector == NULL) return 0;
  cursor = call_offset;
  while (scan_count < 12U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    uint16_t stack_frame_depth = 0U;
    candidate = find_previous_accepted_candidate(section, accepted_start, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    if (allow_register_stack_loads &&
        stack_frame_depth_before_candidate(section, accepted_start, candidate->offset, &stack_frame_depth) &&
        render_lookup_add_stack_load_input_comments(lookup, section->section_index, candidate->offset, &instruction,
        vector, stack_frame_depth)) {
      cursor = candidate->offset;
      ++scan_count;
      continue;
    }
    if (instruction_is_long_stack_push_for_comment(&instruction)) {
      const AmigaOsCallInputInfo *input =
        amiga_vector_input_by_stack_index(vector, (size_t)((push_stack_offset / 4U) - 1U));
      char comment[192];
      if (input == NULL ||
          !format_amiga_call_input_note_render(push_stack_offset, input, comment, sizeof(comment)) ||
          render_lookup_add_instruction_comment(lookup, section->section_index, candidate->offset, comment) != 0) {
        break;
      }
      push_stack_offset = (uint16_t)(push_stack_offset + 4U);
      cursor = candidate->offset;
      ++scan_count;
      continue;
    }
    break;
  }
  return 0;
}

static int recovered_function_arg_temp_add(M68kRenderRecoveredFunctionArg *args, size_t *arg_count,
    size_t arg_capacity, size_t section_index, uint32_t function_offset, uint16_t stack_offset,
    uint8_t reg_kind, uint8_t reg_index, const AmigaOsCallInputInfo *input) {
  size_t index;
  if (args == NULL || arg_count == NULL || input == NULL || stack_offset == 0U ||
      reg_kind == 0U || reg_index >= 8U) {
    return 0;
  }
  for (index = 0U; index < *arg_count; ++index) {
    M68kRenderRecoveredFunctionArg *arg = &args[index];
    if (arg->section_index == section_index && arg->function_offset == function_offset &&
        arg->stack_offset == stack_offset && arg->reg_kind == reg_kind && arg->reg_index == reg_index) {
      return arg->input == input ? 0 : -1;
    }
  }
  if (*arg_count >= arg_capacity) return -1;
  memset(&args[*arg_count], 0, sizeof(args[*arg_count]));
  args[*arg_count].section_index = section_index;
  args[*arg_count].function_offset = function_offset;
  args[*arg_count].stack_offset = stack_offset;
  args[*arg_count].reg_kind = reg_kind;
  args[*arg_count].reg_index = reg_index;
  args[*arg_count].input = input;
  *arg_count += 1U;
  return 0;
}

static int collect_recovered_function_args_from_stack_load_instruction(
    M68kRenderRecoveredFunctionArg *args, size_t *arg_count, size_t arg_capacity,
    size_t section_index, uint32_t function_offset, const M68kInstructionIR *instruction,
    const AmigaOsLibraryVectorInfo *vector, uint16_t stack_frame_depth) {
  int16_t displacement = 0;
  if (args == NULL || arg_count == NULL || instruction == NULL || vector == NULL) return 0;
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->size_suffix == 'l' && instruction->operand_count == 2U &&
      operand_is_stack_displacement_local(&instruction->operands[0], &displacement) &&
      displacement > (int16_t)stack_frame_depth) {
    uint8_t reg = 0U;
    uint8_t reg_kind = 0U;
    const AmigaOsCallInputInfo *input;
    if (operand_is_data_register_local(&instruction->operands[1], &reg)) reg_kind = 1U;
    else if (instruction->operands[1].kind == M68K_ASM_OPERAND_AN) {
      reg = (uint8_t)instruction->operands[1].value.reg;
      reg_kind = 2U;
    }
    input = amiga_vector_input_by_register(vector, reg_kind, reg);
    if (input != NULL) {
      return recovered_function_arg_temp_add(args, arg_count, arg_capacity, section_index, function_offset,
        (uint16_t)(displacement - (int16_t)stack_frame_depth), reg_kind, reg, input);
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U &&
      operand_is_stack_displacement_local(&instruction->operands[0], &displacement) &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST &&
      displacement > (int16_t)stack_frame_depth) {
    uint32_t mask = instruction->operands[1].value.value;
    uint16_t stack_offset = (uint16_t)(displacement - (int16_t)stack_frame_depth);
    unsigned bit;
    for (bit = 0U; bit < 16U; ++bit) {
      uint8_t reg_kind;
      uint8_t reg_index;
      const AmigaOsCallInputInfo *input;
      if ((mask & (1UL << bit)) == 0U) continue;
      reg_kind = bit < 8U ? 1U : 2U;
      reg_index = (uint8_t)(bit < 8U ? bit : bit - 8U);
      input = amiga_vector_input_by_register(vector, reg_kind, reg_index);
      if (input != NULL && recovered_function_arg_temp_add(args, arg_count, arg_capacity, section_index,
          function_offset, stack_offset, reg_kind, reg_index, input) != 0) {
        return -1;
      }
      stack_offset = (uint16_t)(stack_offset + 4U);
    }
  }
  return 0;
}

static int render_lookup_collect_recovered_function_args_from_wrapper(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t wrapper_section_index, uint32_t wrapper_offset,
    const AmigaOsLibraryVectorInfo *expected_vector) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  M68kRenderRecoveredFunctionArg args[16];
  size_t arg_count = 0U;
  uint32_t cursor;
  uint16_t stack_frame_depth = 0U;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || expected_vector == NULL ||
      wrapper_section_index >= decode->section_count) {
    return 0;
  }
  section = &decode->sections[wrapper_section_index];
  if (!accepted_start_at(section, accepted_start[wrapper_section_index], wrapper_offset)) return 0;
  memset(&state, 0, sizeof(state));
  memset(args, 0, sizeof(args));
  cursor = wrapper_offset;
  while (cursor < section->size && cursor - wrapper_offset < 256U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsLibraryVectorInfo *vector;
    int32_t delta = 0;
    if (!accepted_start_at(section, accepted_start[wrapper_section_index], cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index, cursor);
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector == NULL) {
      vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[wrapper_section_index],
        candidate, &instruction);
    }
    if (vector == NULL) {
      vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &state, section, candidate);
    }
    if (vector == expected_vector) {
      size_t index;
      for (index = 0U; index < arg_count; ++index) {
        if (render_lookup_add_recovered_function_arg(lookup, args[index].section_index, args[index].function_offset,
            args[index].stack_offset, args[index].reg_kind, args[index].reg_index, args[index].input) != 0) {
          return -1;
        }
      }
      return 0;
    }
    if (vector != NULL || candidate_has_non_call_control_target(candidate)) break;
    if (collect_recovered_function_args_from_stack_load_instruction(args, &arg_count,
        sizeof(args) / sizeof(args[0]), section->section_index, wrapper_offset, &instruction, expected_vector,
        stack_frame_depth) != 0) {
      return -1;
    }
    if (!instruction_stack_delta_for_comment(&instruction, &delta)) break;
    if (delta < 0 && (uint32_t)(-delta) > (uint32_t)stack_frame_depth) break;
    if (delta > 0 && (uint32_t)delta > UINT16_MAX - (uint32_t)stack_frame_depth) break;
    stack_frame_depth = (uint16_t)((int32_t)stack_frame_depth + delta);
    platform_state_update_d0_lvo_after_instruction(&state, &instruction);
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (!candidate_has_local_helper_summary_fallthrough(candidate)) break;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int render_lookup_infer_amiga_recovered_local_call_summaries(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  M68kRenderPlatformState platform_state;
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  memset(&platform_state, 0, sizeof(platform_state));
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const AmigaOsLibraryVectorInfo *wrapper_call_vector;
      const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
      const AmigaOsLibraryVectorInfo *helper_call_vector;
      const AmigaOsLibraryVectorInfo *vector;
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
      wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
      direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
        section->section_index, candidate);
      helper_call_vector = (wrapper_call_vector == NULL && direct_wrapper_vector == NULL)
        ? resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section->section_index, candidate)
        : NULL;
      vector = direct_wrapper_vector != NULL ? direct_wrapper_vector :
        (wrapper_call_vector != NULL ? wrapper_call_vector : helper_call_vector);
      if (vector != NULL &&
          candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
            &target_offset) &&
          render_lookup_add_recovered_local_call_summary(lookup, target_section_index, target_offset, vector) != 0) {
        return -1;
      }
      platform_state_update_d0_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    }
  }
  return 0;
}

static int render_lookup_infer_amiga_recovered_function_args(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  M68kRenderPlatformState platform_state;
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  memset(&platform_state, 0, sizeof(platform_state));
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const AmigaOsLibraryVectorInfo *wrapper_call_vector;
      const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
      const AmigaOsLibraryVectorInfo *vector;
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
      wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
      direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
        section->section_index, candidate);
      vector = direct_wrapper_vector != NULL ? direct_wrapper_vector : wrapper_call_vector;
      if (vector != NULL &&
          candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
            &target_offset) &&
          render_lookup_collect_recovered_function_args_from_wrapper(lookup, decode, accepted_start,
            target_section_index, target_offset, vector) != 0) {
        return -1;
      }
      platform_state_update_d0_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    }
  }
  return 0;
}

static int amiga_output_has_typed_info(const AmigaOsCallOutputInfo *output) {
  if (output == NULL || output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) return 0;
  return amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id) != NULL ||
    amiga_output_type_or_struct_name(output) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id) != NULL;
}

static void typed_state_clear_base_slots_for_base(M68kRenderTypedState *state, uint8_t base_reg) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return;
  index = 0U;
  while (index < state->base_slot_count) {
    if (state->base_slots[index].known == 0U || state->base_slots[index].base_reg != base_reg) {
      ++index;
      continue;
    }
    state->base_slots[index] = state->base_slots[state->base_slot_count - 1U];
    --state->base_slot_count;
  }
}

static void typed_origin_clear(M68kRenderTypedStorageOrigin *origin) {
  if (origin == NULL) return;
  memset(origin, 0, sizeof(*origin));
}

static void typed_provenance_clear(M68kRenderTypedProvenance *provenance) {
  if (provenance == NULL) return;
  memset(provenance, 0, sizeof(*provenance));
}

static void typed_reg_value_clear(M68kRenderTypedRegValue *value) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->struct_id = AMIGA_OS_STRUCT_ID_NONE;
}

static void typed_stored_value_clear(M68kRenderTypedStoredValue *value) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->struct_id = AMIGA_OS_STRUCT_ID_NONE;
}

static int typed_stored_value_has_payload(const M68kRenderTypedStoredValue *value) {
  return value != NULL && (value->struct_id != AMIGA_OS_STRUCT_ID_NONE || value->app_address_known != 0U);
}

static void typed_stored_value_update_known(M68kRenderTypedStoredValue *value) {
  if (value == NULL) return;
  value->known = typed_stored_value_has_payload(value) ? 1U : 0U;
}

static M68kRenderTypedProvenance typed_provenance_make(uint8_t kind, size_t section_index, uint32_t offset) {
  M68kRenderTypedProvenance provenance;
  memset(&provenance, 0, sizeof(provenance));
  provenance.kind = kind;
  provenance.section_index = section_index;
  provenance.offset = offset;
  return provenance;
}

static int typed_provenances_equal(const M68kRenderTypedProvenance *left,
    const M68kRenderTypedProvenance *right);

static uint8_t typed_provenance_rank(uint8_t kind) {
  switch (kind) {
  case M68K_RENDER_TYPED_PROVENANCE_API_OUTPUT:
    return 70U;
  case M68K_RENDER_TYPED_PROVENANCE_FIELD_POINTER:
  case M68K_RENDER_TYPED_PROVENANCE_FIELD_ADDRESS:
    return 60U;
  case M68K_RENDER_TYPED_PROVENANCE_LOOKUP_STORAGE:
    return 50U;
  case M68K_RENDER_TYPED_PROVENANCE_APP_SLOT:
  case M68K_RENDER_TYPED_PROVENANCE_BASE_SLOT:
  case M68K_RENDER_TYPED_PROVENANCE_STACK_SLOT:
    return 40U;
  case M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT:
    return 30U;
  case M68K_RENDER_TYPED_PROVENANCE_REGISTER_COPY:
    return 10U;
  case M68K_RENDER_TYPED_PROVENANCE_NONE:
  default:
    return 0U;
  }
}

static void typed_provenance_merge(M68kRenderTypedProvenance *dest,
    const M68kRenderTypedProvenance *source) {
  uint8_t dest_rank;
  uint8_t source_rank;
  if (dest == NULL || source == NULL) return;
  if (typed_provenances_equal(dest, source)) return;
  if (dest->kind == M68K_RENDER_TYPED_PROVENANCE_NONE) return;
  dest_rank = typed_provenance_rank(dest->kind);
  source_rank = typed_provenance_rank(source->kind);
  if (source_rank > dest_rank) {
    *dest = *source;
  } else if (source_rank == dest_rank) {
    typed_provenance_clear(dest);
  }
}

static int typed_origins_equal(const M68kRenderTypedStorageOrigin *left,
    const M68kRenderTypedStorageOrigin *right) {
  if (left == NULL || right == NULL) return 0;
  return left->kind == right->kind && left->storage_kind == right->storage_kind &&
    left->base_reg == right->base_reg && left->section_index == right->section_index &&
    left->displacement == right->displacement && left->address == right->address;
}

static int typed_provenances_equal(const M68kRenderTypedProvenance *left,
    const M68kRenderTypedProvenance *right) {
  if (left == NULL || right == NULL) return 0;
  return left->kind == right->kind && left->section_index == right->section_index &&
    left->offset == right->offset;
}

static void typed_state_clear_reg(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) {
    typed_reg_value_clear(&state->data_regs[reg_index]);
    state->data_app_addr_regs[reg_index].known = 0U;
    state->data_app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
  } else if (reg_kind == 2U) {
    typed_reg_value_clear(&state->addr_regs[reg_index]);
    state->app_addr_regs[reg_index].known = 0U;
    state->app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->memory_base_regs[reg_index]);
    typed_state_clear_base_slots_for_base(state, reg_index);
  }
}

static void typed_state_set_reg(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    const AmigaOsCallOutputInfo *output, const M68kRenderTypedProvenance *provenance) {
  if (state == NULL || output == NULL || reg_index >= 8U || !amiga_output_has_typed_info(output)) return;
  if (reg_kind == 1U) {
    state->data_regs[reg_index].known = 1U;
    state->data_regs[reg_index].output = output;
    state->data_regs[reg_index].struct_id = output->struct_id;
    typed_origin_clear(&state->data_regs[reg_index].origin);
    state->data_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->data_app_addr_regs[reg_index].known = 0U;
    state->data_app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
  } else if (reg_kind == 2U) {
    state->addr_regs[reg_index].known = 1U;
    state->addr_regs[reg_index].output = output;
    state->addr_regs[reg_index].struct_id = output->struct_id;
    typed_origin_clear(&state->addr_regs[reg_index].origin);
    state->addr_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->app_addr_regs[reg_index].known = 0U;
    state->app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->memory_base_regs[reg_index]);
  }
}

static void typed_state_set_reg_struct_id(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    uint16_t struct_id, const M68kRenderTypedProvenance *provenance) {
  if (state == NULL || reg_index >= 8U || struct_id == AMIGA_OS_STRUCT_ID_NONE) return;
  if (reg_kind == 1U) {
    state->data_regs[reg_index].known = 1U;
    state->data_regs[reg_index].output = NULL;
    state->data_regs[reg_index].struct_id = struct_id;
    typed_origin_clear(&state->data_regs[reg_index].origin);
    state->data_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->data_app_addr_regs[reg_index].known = 0U;
    state->data_app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
  } else if (reg_kind == 2U) {
    state->addr_regs[reg_index].known = 1U;
    state->addr_regs[reg_index].output = NULL;
    state->addr_regs[reg_index].struct_id = struct_id;
    typed_origin_clear(&state->addr_regs[reg_index].origin);
    state->addr_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->app_addr_regs[reg_index].known = 0U;
    state->app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->memory_base_regs[reg_index]);
  }
}

static void typed_state_clear_all(M68kRenderTypedState *state) {
  size_t index;
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
  for (index = 0U; index < 8U; ++index) {
    state->data_regs[index].struct_id = AMIGA_OS_STRUCT_ID_NONE;
    state->addr_regs[index].struct_id = AMIGA_OS_STRUCT_ID_NONE;
  }
}

static void typed_state_apply_platform_call_clobbers(M68kRenderTypedState *state) {
  uint8_t preserved_data;
  uint8_t preserved_address;
  uint8_t bit;
  if (state == NULL) return;
  preserved_data = amiga_os_calling_convention_preserved_data_mask();
  preserved_address = amiga_os_calling_convention_preserved_address_mask();
  for (bit = 0U; bit < 8U; ++bit) {
    if ((preserved_data & (uint8_t)(1U << bit)) == 0U) typed_state_clear_reg(state, 1U, bit);
    if ((preserved_address & (uint8_t)(1U << bit)) == 0U) typed_state_clear_reg(state, 2U, bit);
  }
}

static void typed_state_set_app_address(M68kRenderTypedState *state, uint8_t reg_index, int16_t displacement,
    uint16_t struct_id, const M68kRenderTypedProvenance *provenance) {
  if (state == NULL || reg_index >= 8U) return;
  state->addr_regs[reg_index].known = struct_id != AMIGA_OS_STRUCT_ID_NONE ? 1U : 0U;
  state->addr_regs[reg_index].output = NULL;
  state->addr_regs[reg_index].struct_id = struct_id;
  typed_origin_clear(&state->addr_regs[reg_index].origin);
  state->addr_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
  state->app_addr_regs[reg_index].known = 1U;
  state->app_addr_regs[reg_index].displacement = displacement;
  typed_memory_base_clear(&state->memory_base_regs[reg_index]);
}

static void typed_state_set_data_app_address(M68kRenderTypedState *state, uint8_t reg_index, int16_t displacement) {
  if (state == NULL || reg_index >= 8U) return;
  state->data_app_addr_regs[reg_index].known = 1U;
  state->data_app_addr_regs[reg_index].displacement = displacement;
  typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
}

static void typed_memory_base_clear(M68kRenderTypedMemoryBaseValue *value) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
}

static void typed_state_set_memory_base(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    size_t section_index, uint32_t offset) {
  M68kRenderTypedMemoryBaseValue *value;
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) value = &state->data_memory_base_regs[reg_index];
  else if (reg_kind == 2U) value = &state->memory_base_regs[reg_index];
  else return;
  value->known = 1U;
  value->section_index = section_index;
  value->offset = offset;
}

static int typed_state_copy_memory_base(const M68kRenderTypedState *state, const M68kOperandIR *operand,
    M68kRenderTypedMemoryBaseValue *out_value) {
  uint8_t reg = 0U;
  if (out_value != NULL) typed_memory_base_clear(out_value);
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  if (operand_is_data_register_local(operand, &reg) && reg < 8U && state->data_memory_base_regs[reg].known) {
    *out_value = state->data_memory_base_regs[reg];
    return 1;
  }
  if (operand_address_register_index_local(operand, &reg) && reg < 8U && state->memory_base_regs[reg].known) {
    *out_value = state->memory_base_regs[reg];
    return 1;
  }
  return 0;
}

static int typed_memory_base_offset_add(uint32_t base_offset, int32_t displacement, uint32_t *out_offset) {
  int64_t value = (int64_t)base_offset + (int64_t)displacement;
  if (out_offset != NULL) *out_offset = 0U;
  if (value < 0 || value > UINT32_MAX) return 0;
  if (out_offset != NULL) *out_offset = (uint32_t)value;
  return 1;
}

static int typed_state_copy_app_address(const M68kRenderTypedState *state, const M68kOperandIR *operand,
    int16_t *out_displacement) {
  uint8_t reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (state == NULL || operand == NULL || out_displacement == NULL) return 0;
  if (operand_address_register_index_local(operand, &reg) && reg < 8U && state->app_addr_regs[reg].known) {
    *out_displacement = state->app_addr_regs[reg].displacement;
    return 1;
  }
  if (operand_is_data_register_local(operand, &reg) && reg < 8U && state->data_app_addr_regs[reg].known) {
    *out_displacement = state->data_app_addr_regs[reg].displacement;
    return 1;
  }
  return 0;
}

static const AmigaOsCallOutputInfo *typed_state_output_for_operand(const M68kRenderTypedState *state,
    const M68kOperandIR *operand, uint8_t *out_reg_kind, uint8_t *out_reg_index) {
  uint8_t reg = 0U;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 1U;
    if (out_reg_index != NULL) *out_reg_index = reg;
    return state->data_regs[reg].known ? state->data_regs[reg].output : NULL;
  }
  if (operand_address_register_index_local(operand, &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 2U;
    if (out_reg_index != NULL) *out_reg_index = reg;
    return state->addr_regs[reg].known ? state->addr_regs[reg].output : NULL;
  }
  return NULL;
}

static uint16_t typed_state_struct_id_for_operand(const M68kRenderTypedState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return AMIGA_OS_STRUCT_ID_NONE;
  if (operand_is_data_register_local(operand, &reg))
    return state->data_regs[reg].known ? state->data_regs[reg].struct_id : AMIGA_OS_STRUCT_ID_NONE;
  if (operand_address_register_index_local(operand, &reg))
    return state->addr_regs[reg].known ? state->addr_regs[reg].struct_id : AMIGA_OS_STRUCT_ID_NONE;
  return AMIGA_OS_STRUCT_ID_NONE;
}

static int typed_state_origin_for_operand(const M68kRenderTypedState *state, const M68kOperandIR *operand,
    M68kRenderTypedStorageOrigin *out_origin) {
  uint8_t reg = 0U;
  if (out_origin != NULL) typed_origin_clear(out_origin);
  if (state == NULL || operand == NULL || out_origin == NULL) return 0;
  if (operand_is_data_register_local(operand, &reg)) {
    if (state->data_regs[reg].known == 0U || state->data_regs[reg].origin.kind == M68K_RENDER_TYPED_ORIGIN_NONE)
      return 0;
    *out_origin = state->data_regs[reg].origin;
    return 1;
  }
  if (operand_address_register_index_local(operand, &reg)) {
    if (state->addr_regs[reg].known == 0U || state->addr_regs[reg].origin.kind == M68K_RENDER_TYPED_ORIGIN_NONE)
      return 0;
    *out_origin = state->addr_regs[reg].origin;
    return 1;
  }
  return 0;
}

static void typed_state_set_reg_origin(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    const M68kRenderTypedStorageOrigin *origin) {
  if (state == NULL || origin == NULL || reg_index >= 8U || origin->kind == M68K_RENDER_TYPED_ORIGIN_NONE)
    return;
  if (reg_kind == 1U && state->data_regs[reg_index].known)
    state->data_regs[reg_index].origin = *origin;
  else if (reg_kind == 2U && state->addr_regs[reg_index].known)
    state->addr_regs[reg_index].origin = *origin;
}

static int typed_stored_value_has_useful_info(const M68kRenderTypedStoredValue *value) {
  return value != NULL && value->known != 0U && typed_stored_value_has_payload(value);
}

static M68kRenderTypedStoredValue typed_stored_value_for_operand(const M68kRenderTypedState *state,
    const M68kOperandIR *operand) {
  M68kRenderTypedStoredValue value;
  int16_t app_displacement = 0;
  uint8_t reg = 0U;
  typed_stored_value_clear(&value);
  value.struct_id = typed_state_struct_id_for_operand(state, operand);
  value.output = typed_state_output_for_operand(state, operand, NULL, NULL);
  if (state != NULL && operand_is_data_register_local(operand, &reg))
    value.provenance = state->data_regs[reg].provenance;
  else if (state != NULL && operand_address_register_index_local(operand, &reg))
    value.provenance = state->addr_regs[reg].provenance;
  if (typed_state_copy_app_address(state, operand, &app_displacement)) {
    value.app_address_known = 1U;
    value.app_displacement = app_displacement;
  }
  typed_stored_value_update_known(&value);
  return value;
}

static void typed_state_clear_stack_slots(M68kRenderTypedState *state) {
  if (state == NULL) return;
  state->stack_slot_count = 0U;
}

static void typed_state_clear_stack_slot(M68kRenderTypedState *state, int16_t displacement) {
  size_t index;
  if (state == NULL) return;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    if (state->stack_slots[index].known == 0U || state->stack_slots[index].displacement != displacement) continue;
    state->stack_slots[index] = state->stack_slots[state->stack_slot_count - 1U];
    --state->stack_slot_count;
    return;
  }
}

static void typed_state_set_stack_slot(M68kRenderTypedState *state, int16_t displacement,
    const M68kRenderTypedStoredValue *value) {
  size_t index;
  if (state == NULL || value == NULL || !typed_stored_value_has_useful_info(value)) return;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    if (state->stack_slots[index].known == 0U || state->stack_slots[index].displacement != displacement) continue;
    state->stack_slots[index].value = *value;
    return;
  }
  if (state->stack_slot_count >= M68K_RENDER_TYPED_STACK_SLOT_LIMIT) return;
  state->stack_slots[state->stack_slot_count].known = 1U;
  state->stack_slots[state->stack_slot_count].displacement = displacement;
  state->stack_slots[state->stack_slot_count].value = *value;
  ++state->stack_slot_count;
}

static const M68kRenderTypedStoredValue *typed_state_stack_slot_value(const M68kRenderTypedState *state,
    int16_t displacement) {
  size_t index;
  if (state == NULL) return NULL;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    const M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
    if (slot->known != 0U && slot->displacement == displacement &&
        typed_stored_value_has_useful_info(&slot->value)) {
      return &slot->value;
    }
  }
  return NULL;
}

static const M68kRenderTypedBaseSlot *typed_state_base_slot_entry(const M68kRenderTypedState *state,
    uint8_t base_reg, int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return NULL;
  for (index = 0U; index < state->base_slot_count; ++index) {
    const M68kRenderTypedBaseSlot *slot = &state->base_slots[index];
    if (slot->known != 0U && slot->base_reg == base_reg && slot->displacement == displacement)
      return slot;
  }
  return NULL;
}

static M68kRenderTypedBaseSlot *typed_state_mutable_base_slot_entry(M68kRenderTypedState *state,
    uint8_t base_reg, int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return NULL;
  for (index = 0U; index < state->base_slot_count; ++index) {
    M68kRenderTypedBaseSlot *slot = &state->base_slots[index];
    if (slot->known != 0U && slot->base_reg == base_reg && slot->displacement == displacement)
      return slot;
  }
  return NULL;
}

static void typed_state_clear_base_slot(M68kRenderTypedState *state, uint8_t base_reg, int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return;
  for (index = 0U; index < state->base_slot_count; ++index) {
    if (state->base_slots[index].known == 0U || state->base_slots[index].base_reg != base_reg ||
        state->base_slots[index].displacement != displacement) {
      continue;
    }
    state->base_slots[index] = state->base_slots[state->base_slot_count - 1U];
    --state->base_slot_count;
    return;
  }
}

static void typed_state_set_base_slot(M68kRenderTypedState *state, uint8_t base_reg, int16_t displacement,
    const M68kRenderTypedStoredValue *value) {
  size_t index;
  if (state == NULL || base_reg >= 8U || value == NULL || !typed_stored_value_has_useful_info(value)) return;
  for (index = 0U; index < state->base_slot_count; ++index) {
    if (state->base_slots[index].known == 0U || state->base_slots[index].base_reg != base_reg ||
        state->base_slots[index].displacement != displacement) {
      continue;
    }
    state->base_slots[index].value = *value;
    return;
  }
  if (state->base_slot_count >= M68K_RENDER_TYPED_BASE_SLOT_LIMIT) return;
  state->base_slots[state->base_slot_count].known = 1U;
  state->base_slots[state->base_slot_count].base_reg = base_reg;
  state->base_slots[state->base_slot_count].displacement = displacement;
  state->base_slots[state->base_slot_count].value = *value;
  ++state->base_slot_count;
}

static const M68kRenderTypedStoredValue *typed_state_base_slot_value(const M68kRenderTypedState *state,
    uint8_t base_reg, int16_t displacement) {
  const M68kRenderTypedBaseSlot *slot = typed_state_base_slot_entry(state, base_reg, displacement);
  if (slot != NULL && typed_stored_value_has_useful_info(&slot->value)) return &slot->value;
  return NULL;
}

static uint16_t lookup_typed_output_slot_struct_id(const M68kRenderLookup *lookup, int16_t displacement) {
  size_t index;
  uint16_t struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (lookup == NULL) return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < lookup->typed_slot_effect_count; ++index) {
    const M68kRenderTypedSlotEffect *effect = &lookup->typed_slot_effects[index];
    uint16_t effect_struct_id;
    if (effect->displacement != displacement || effect->output == NULL) continue;
    effect_struct_id = effect->output->struct_id;
    if (effect_struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    if (struct_id != AMIGA_OS_STRUCT_ID_NONE && struct_id != effect_struct_id) return AMIGA_OS_STRUCT_ID_NONE;
    struct_id = effect_struct_id;
  }
  return struct_id;
}

static uint16_t typed_struct_id_for_base_slot_operand(const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform_state, const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (lookup == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U) {
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  if (platform_state != NULL) {
    if (platform_state->address_app_base_known[base_reg] ||
        (base_reg == 6U && !platform_state->address_base_known[6U])) {
      uint16_t output_struct_id = lookup_typed_output_slot_struct_id(lookup, displacement);
      if (output_struct_id != AMIGA_OS_STRUCT_ID_NONE) return output_struct_id;
      return lookup_app_base_field_slot_struct_id(lookup, displacement);
    }
    if (platform_state->address_base_known[base_reg]) {
      return lookup_base_field_slot_struct_id(lookup, platform_state->address_base_library[base_reg], displacement);
    }
  } else if (base_reg == 6U) {
    return lookup_app_base_field_slot_struct_id(lookup, displacement);
  }
  return AMIGA_OS_STRUCT_ID_NONE;
}

static uint16_t lookup_typed_app_slot_struct_id(const M68kRenderLookup *lookup, int16_t displacement) {
  size_t index;
  if (lookup == NULL) return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < lookup->typed_app_slot_count; ++index) {
    const M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[index];
    if (slot->displacement == displacement)
      return slot->conflicted == 0U ? slot->struct_id : AMIGA_OS_STRUCT_ID_NONE;
  }
  return AMIGA_OS_STRUCT_ID_NONE;
}

static int typed_app_address_operand_info(const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform_state, const M68kOperandIR *operand, int16_t *out_displacement,
    uint16_t *out_struct_id) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (out_struct_id != NULL) *out_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (lookup == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U) {
    return 0;
  }
  if (!render_state_operand_uses_app_base(platform_state, base_reg, displacement)) return 0;
  if (out_displacement != NULL) *out_displacement = displacement;
  if (out_struct_id != NULL) *out_struct_id = lookup_typed_app_slot_struct_id(lookup, displacement);
  return 1;
}

static int typed_storage_key_for_lookup_memory_operand(const M68kRenderLookup *lookup,
    const M68kRenderTypedState *state, const M68kRenderPlatformState *platform_state,
    size_t current_section_index, const M68kOperandIR *operand, uint8_t access_kind, uint8_t *out_kind,
    size_t *out_section_index, int32_t *out_displacement, uint32_t *out_address) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint32_t absolute_offset = 0U;
  (void)lookup;
  if (out_kind != NULL) *out_kind = 0U;
  if (out_section_index != NULL) *out_section_index = (size_t)-1;
  if (out_displacement != NULL) *out_displacement = 0;
  if (out_address != NULL) *out_address = 0U;
  if (operand == NULL ||
      (access_kind != M68K_SIM_ACCESS_MEMORY_READ && access_kind != M68K_SIM_ACCESS_MEMORY_WRITE)) {
    return 0;
  }
  if (operand_is_address_memory_local(operand, &base_reg, &displacement) && base_reg < 8U &&
      render_state_operand_uses_app_base(platform_state, base_reg, displacement)) {
    if (out_kind != NULL) *out_kind = M68K_RENDER_TYPED_STORAGE_APP_SLOT;
    if (out_displacement != NULL) *out_displacement = displacement;
    return 1;
  }
  if (state != NULL && operand_is_address_memory_local(operand, &base_reg, &displacement) &&
      base_reg < 8U && base_reg != 7U && state->memory_base_regs[base_reg].known) {
    if (out_kind != NULL) *out_kind = M68K_RENDER_TYPED_STORAGE_BASE_SLOT;
    if (out_section_index != NULL) *out_section_index = state->memory_base_regs[base_reg].section_index;
    if (out_displacement != NULL) *out_displacement = displacement;
    if (out_address != NULL) *out_address = state->memory_base_regs[base_reg].offset;
    return 1;
  }
  if (operand_absolute_offset_local(operand, &absolute_offset)) {
    if (amiga_os_find_hardware_register_by_cpu_address(absolute_offset) != NULL) return 0;
    if (out_kind != NULL) *out_kind = M68K_RENDER_TYPED_STORAGE_ABSOLUTE;
    if (out_section_index != NULL)
      *out_section_index = operand->symbol_ref.has_section ? operand->symbol_ref.section_index : current_section_index;
    if (out_address != NULL) *out_address = absolute_offset;
    return 1;
  }
  return 0;
}

static const M68kRenderTypedStorageSlot *lookup_typed_storage_slot(const M68kRenderLookup *lookup, uint8_t kind,
    size_t section_index, int32_t displacement, uint32_t address) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    const M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    if (slot->kind != kind || slot->conflicted != 0U) continue;
    if (kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
      if (slot->displacement != displacement) continue;
    } else if (kind == M68K_RENDER_TYPED_STORAGE_ABSOLUTE) {
      if (slot->section_index != section_index || slot->address != address) continue;
    } else if (kind == M68K_RENDER_TYPED_STORAGE_BASE_SLOT) {
      if (slot->section_index != section_index || slot->address != address ||
          slot->displacement != displacement) {
        continue;
      }
    } else {
      continue;
    }
    return typed_stored_value_has_useful_info(&slot->value) ? slot : NULL;
  }
  return NULL;
}

static uint16_t typed_pointer_struct_id_for_field_read(const M68kRenderTypedState *state,
    const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint16_t struct_id = AMIGA_OS_STRUCT_ID_NONE;
  AmigaOsResolvedStructFieldInfo resolved;
  const AmigaOsStructFieldInfo *field;
  if (state == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
      !state->addr_regs[base_reg].known) {
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  struct_id = state->addr_regs[base_reg].struct_id;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return AMIGA_OS_STRUCT_ID_NONE;
  if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, displacement, 0, &resolved)) return AMIGA_OS_STRUCT_ID_NONE;
  if (resolved.query_offset != resolved.offset) return AMIGA_OS_STRUCT_ID_NONE;
  field = amiga_os_find_struct_field_by_field_id(resolved.field_id);
  if (field == NULL || field->pointer_struct_id == AMIGA_OS_STRUCT_ID_NONE) return AMIGA_OS_STRUCT_ID_NONE;
  return field->pointer_struct_id;
}

static int typed_stored_value_from_field_pointer_read(M68kRenderTypedStoredValue *value,
    const M68kRenderTypedState *state, const M68kOperandIR *operand, size_t section_index, uint32_t offset) {
  uint16_t struct_id;
  if (value == NULL) return 0;
  struct_id = typed_pointer_struct_id_for_field_read(state, operand);
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
  typed_stored_value_clear(value);
  value->struct_id = struct_id;
  value->provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_FIELD_POINTER, section_index, offset);
  typed_stored_value_update_known(value);
  return 1;
}

static uint16_t typed_nested_struct_id_for_field_address(const M68kRenderTypedState *state,
    const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint16_t struct_id = AMIGA_OS_STRUCT_ID_NONE;
  AmigaOsResolvedStructFieldInfo resolved;
  const AmigaOsStructFieldInfo *field;
  if (state == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
      !state->addr_regs[base_reg].known) {
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  struct_id = state->addr_regs[base_reg].struct_id;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return AMIGA_OS_STRUCT_ID_NONE;
  if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, displacement, 0, &resolved))
    return AMIGA_OS_STRUCT_ID_NONE;
  if (resolved.query_offset != resolved.offset) return AMIGA_OS_STRUCT_ID_NONE;
  field = amiga_os_find_struct_field_by_field_id(resolved.field_id);
  if (field == NULL || field->pointer_struct_id != AMIGA_OS_STRUCT_ID_NONE || field->size == 0U)
    return AMIGA_OS_STRUCT_ID_NONE;
  return amiga_os_struct_id_from_type_id(field->nested_type_id);
}

static uint16_t amiga_struct_size_for_struct_id(uint16_t struct_id) {
  int32_t max_end = 0;
  size_t index;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE || amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) == NULL)
    return 0U;
  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {
    const AmigaOsStructFieldInfo *field = amiga_os_struct_field_at(index);
    int32_t end;
    if (field == NULL || field->struct_id != struct_id) continue;
    end = (int32_t)field->offset + (int32_t)field->size;
    if (field->size == 0U) end = field->offset;
    if (end > max_end) max_end = end;
  }
  if (max_end <= 0) return 0U;
  return max_end > UINT16_MAX ? UINT16_MAX : (uint16_t)max_end;
}

static int amiga_struct_base_chain_contains(uint16_t struct_id, uint16_t base_struct_id) {
  uint16_t current_struct_id = struct_id;
  size_t guard;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE || base_struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
  if (struct_id == base_struct_id) return 0;
  for (guard = 0U; guard < AMIGA_OS_STRUCT_BASE_COUNT + 1U; ++guard) {
    const AmigaOsStructBaseInfo *base = amiga_os_find_struct_base_by_struct_id(current_struct_id);
    if (base == NULL || base->base_struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
    if (base->base_struct_id == base_struct_id) return 1;
    current_struct_id = base->base_struct_id;
  }
  return 0;
}

static uint16_t typed_struct_id_common_merge(uint16_t left_struct_id, uint16_t right_struct_id) {
  if (left_struct_id == right_struct_id) return left_struct_id;
  if (left_struct_id == AMIGA_OS_STRUCT_ID_NONE || right_struct_id == AMIGA_OS_STRUCT_ID_NONE)
    return AMIGA_OS_STRUCT_ID_NONE;
  if (amiga_struct_base_chain_contains(left_struct_id, right_struct_id)) return right_struct_id;
  if (amiga_struct_base_chain_contains(right_struct_id, left_struct_id)) return left_struct_id;
  return AMIGA_OS_STRUCT_ID_NONE;
}

static uint16_t typed_struct_id_refined_merge(uint16_t existing_struct_id, uint16_t candidate_struct_id,
    int *out_conflict) {
  if (out_conflict != NULL) *out_conflict = 0;
  if (existing_struct_id == AMIGA_OS_STRUCT_ID_NONE) return candidate_struct_id;
  if (candidate_struct_id == AMIGA_OS_STRUCT_ID_NONE || existing_struct_id == candidate_struct_id)
    return existing_struct_id;
  if (amiga_struct_base_chain_contains(candidate_struct_id, existing_struct_id)) return candidate_struct_id;
  if (amiga_struct_base_chain_contains(existing_struct_id, candidate_struct_id)) return existing_struct_id;
  if (out_conflict != NULL) *out_conflict = 1;
  return AMIGA_OS_STRUCT_ID_NONE;
}

static uint8_t instruction_size_suffix_bytes_local(char size_suffix) {
  if (size_suffix == 'b') return 1U;
  if (size_suffix == 'w') return 2U;
  if (size_suffix == 'l') return 4U;
  return 0U;
}

static uint16_t typed_struct_id_common_nonroot_merge(uint16_t current_struct_id, uint16_t candidate_struct_id,
    uint16_t root_struct_id, uint8_t *io_conflicted) {
  uint16_t merged;
  if (io_conflicted != NULL && *io_conflicted != 0U) return AMIGA_OS_STRUCT_ID_NONE;
  if (candidate_struct_id == AMIGA_OS_STRUCT_ID_NONE || candidate_struct_id == root_struct_id)
    return AMIGA_OS_STRUCT_ID_NONE;
  if (current_struct_id == AMIGA_OS_STRUCT_ID_NONE) return candidate_struct_id;
  merged = typed_struct_id_common_merge(current_struct_id, candidate_struct_id);
  if (merged == AMIGA_OS_STRUCT_ID_NONE || merged == root_struct_id) {
    if (io_conflicted != NULL) *io_conflicted = 1U;
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  return merged;
}

static void classify_unresolved_typed_access(uint16_t root_struct_id, int16_t displacement, uint16_t struct_size,
    uint8_t access_size, uint8_t *out_classification, uint16_t *out_candidate_count, char *out_container_struct_name,
    size_t container_struct_name_size, char *out_container_field_expr, size_t container_field_expr_size,
    uint16_t *out_container_struct_id) {
  uint32_t candidate_count = 0U, exact_size_candidate_count = 0U;
  uint16_t unique_container_struct_id = AMIGA_OS_STRUCT_ID_NONE, exact_size_common_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  uint8_t exact_size_conflicted = 0U;
  int32_t displacement32 = (int32_t)displacement;
  size_t index;
  if (out_classification != NULL)
    *out_classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP;
  if (out_candidate_count != NULL) *out_candidate_count = 0U;
  if (out_container_struct_name != NULL && container_struct_name_size > 0U) out_container_struct_name[0] = '\0';
  if (out_container_field_expr != NULL && container_field_expr_size > 0U) out_container_field_expr[0] = '\0';
  if (out_container_struct_id != NULL) *out_container_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (root_struct_id == AMIGA_OS_STRUCT_ID_NONE) return;
  if (struct_size > 0U && (displacement32 < 0 || displacement32 >= (int32_t)struct_size)) {
    if (out_classification != NULL)
      *out_classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE;
  }
  if (struct_size == 0U || displacement32 < (int32_t)struct_size || displacement32 < 0) return;
  for (index = 0U; index < AMIGA_OS_STRUCT_BASE_COUNT; ++index) {
    const AmigaOsStructBaseInfo *base = amiga_os_struct_base_at(index);
    AmigaOsResolvedStructFieldInfo resolved;
    uint16_t candidate_size;
    if (base == NULL || base->struct_id == root_struct_id) continue;
    if (!amiga_struct_base_chain_contains(base->struct_id, root_struct_id)) continue;
    candidate_size = amiga_struct_size_for_struct_id(base->struct_id);
    if (candidate_size == 0U || displacement32 >= (int32_t)candidate_size) continue;
    ++candidate_count;
    unique_container_struct_id = candidate_count == 1U ? base->struct_id : AMIGA_OS_STRUCT_ID_NONE;
    if (access_size != 0U &&
        amiga_os_resolve_struct_field_by_struct_id(base->struct_id, displacement, 0, &resolved) &&
        resolved.offset == displacement && resolved.size == access_size) {
      char exact_field_expr[96];
      if (!amiga_os_resolve_struct_field_symbol_expr_by_struct_id(base->struct_id, displacement, 0,
          exact_field_expr, sizeof(exact_field_expr))) {
        continue;
      }
      ++exact_size_candidate_count;
      exact_size_common_struct_id = typed_struct_id_common_nonroot_merge(exact_size_common_struct_id,
        base->struct_id, root_struct_id, &exact_size_conflicted);
    }
  }
  if (candidate_count == 0U) return;
  if (out_classification != NULL)
    *out_classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION;
  if (out_candidate_count != NULL)
    *out_candidate_count = candidate_count > UINT16_MAX ? UINT16_MAX : (uint16_t)candidate_count;
  if (unique_container_struct_id == AMIGA_OS_STRUCT_ID_NONE && exact_size_candidate_count != 0U &&
      exact_size_conflicted == 0U)
    unique_container_struct_id = exact_size_common_struct_id;
  if (unique_container_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    const char *container_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, unique_container_struct_id);
    if (out_container_struct_id != NULL) *out_container_struct_id = unique_container_struct_id;
    if (container_name != NULL && container_name[0] != '\0' &&
        out_container_struct_name != NULL && container_struct_name_size > 0U) {
      snprintf(out_container_struct_name, container_struct_name_size, "%s", container_name);
    }
    if (out_container_field_expr != NULL && container_field_expr_size > 0U) {
      (void)amiga_os_resolve_struct_field_symbol_expr_by_struct_id(unique_container_struct_id, displacement, 0,
        out_container_field_expr, container_field_expr_size);
    }
  }
}

static int typed_value_for_memory_read_operand(const M68kRenderLookup *lookup, const M68kRenderTypedState *state,
    const M68kRenderPlatformState *platform_state, size_t current_section_index, const M68kOperandIR *operand,
    uint8_t access_kind, M68kRenderTypedStoredValue *out_value, M68kRenderTypedStorageOrigin *out_origin) {
  uint8_t base_reg = 0U, storage_kind = 0U;
  int16_t base_displacement = 0, stack_displacement = 0;
  size_t storage_section = (size_t)-1;
  int32_t storage_displacement = 0;
  uint32_t storage_address = 0U;
  const M68kRenderTypedStoredValue *value = NULL;
  const M68kRenderTypedStorageSlot *slot = NULL;
  if (out_value != NULL) typed_stored_value_clear(out_value);
  if (out_origin != NULL) typed_origin_clear(out_origin);
  if (lookup == NULL || state == NULL || operand == NULL || out_value == NULL ||
      access_kind != M68K_SIM_ACCESS_MEMORY_READ) {
    return 0;
  }
  if (operand_is_stack_displacement_local(operand, &stack_displacement)) {
    value = typed_state_stack_slot_value(state, stack_displacement);
    if (value != NULL) {
      *out_value = *value;
      if (out_value->provenance.kind == M68K_RENDER_TYPED_PROVENANCE_NONE)
        out_value->provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_STACK_SLOT, current_section_index, 0U);
      if (out_origin != NULL) {
        out_origin->kind = M68K_RENDER_TYPED_ORIGIN_STACK_SLOT;
        out_origin->displacement = stack_displacement;
      }
      return 1;
    }
  }
  if (operand_is_address_memory_local(operand, &base_reg, &base_displacement) && base_reg < 8U && base_reg != 7U &&
      !render_state_operand_uses_app_base(platform_state, base_reg, base_displacement)) {
    value = typed_state_base_slot_value(state, base_reg, base_displacement);
    if (value != NULL) {
      *out_value = *value;
      if (out_value->provenance.kind == M68K_RENDER_TYPED_PROVENANCE_NONE)
        out_value->provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_BASE_SLOT, current_section_index, 0U);
      if (out_origin != NULL) {
        out_origin->kind = M68K_RENDER_TYPED_ORIGIN_BASE_SLOT;
        out_origin->base_reg = base_reg;
        out_origin->displacement = base_displacement;
      }
      return 1;
    }
  }
  {
    if (!typed_storage_key_for_lookup_memory_operand(lookup, state, platform_state, current_section_index, operand,
        access_kind, &storage_kind, &storage_section, &storage_displacement, &storage_address)) {
      return 0;
    }
    slot = lookup_typed_storage_slot(lookup, storage_kind, storage_section, storage_displacement, storage_address);
    value = slot != NULL ? &slot->value : NULL;
  }
  if (value == NULL) return 0;
  *out_value = *value;
  if (out_value->provenance.kind == M68K_RENDER_TYPED_PROVENANCE_NONE)
    out_value->provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_LOOKUP_STORAGE,
      slot != NULL ? slot->source_section_index : current_section_index,
      slot != NULL ? slot->source_offset : 0U);
  if (out_origin != NULL) {
    out_origin->kind = M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE;
    out_origin->storage_kind = storage_kind;
    out_origin->section_index = storage_section;
    out_origin->displacement = storage_displacement;
    out_origin->address = storage_address;
  }
  return 1;
}

static int typed_stored_value_promote_struct(M68kRenderTypedStoredValue *value, uint16_t root_struct_id,
    uint16_t refined_struct_id) {
  if (value == NULL || root_struct_id == AMIGA_OS_STRUCT_ID_NONE ||
      refined_struct_id == AMIGA_OS_STRUCT_ID_NONE || value->struct_id != root_struct_id ||
      !amiga_struct_base_chain_contains(refined_struct_id, root_struct_id)) {
    return 0;
  }
  value->struct_id = refined_struct_id;
  value->output = NULL;
  typed_stored_value_update_known(value);
  return 1;
}

static int render_lookup_promote_typed_storage_slot(M68kRenderLookup *lookup, const M68kRenderTypedStorageOrigin *origin,
    uint16_t root_struct_id, uint16_t refined_struct_id, size_t source_section_index, uint32_t source_offset,
    int *out_changed) {
  size_t index;
  if (out_changed != NULL) *out_changed = 0;
  if (lookup == NULL || origin == NULL || origin->kind != M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE)
    return 0;
  if (origin->storage_kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
    return render_lookup_add_typed_app_slot(lookup, (int16_t)origin->displacement, refined_struct_id,
      source_section_index, source_offset, out_changed);
  }
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    if (slot->conflicted != 0U || !typed_storage_keys_match(slot, origin->storage_kind, origin->section_index,
        origin->displacement, origin->address)) {
      continue;
    }
    if (typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->source_section_index = source_section_index;
      slot->source_offset = source_offset;
      slot->value.provenance =
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
      if (out_changed != NULL) *out_changed = 1;
    }
    return 0;
  }
  return 0;
}

static int typed_state_promote_origin_struct(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    const M68kRenderTypedStorageOrigin *origin, uint16_t root_struct_id, uint16_t refined_struct_id,
    size_t source_section_index, uint32_t source_offset, int *out_changed) {
  size_t index;
  int changed = 0;
  if (out_changed != NULL) *out_changed = 0;
  if (state == NULL || origin == NULL || origin->kind == M68K_RENDER_TYPED_ORIGIN_NONE) return 0;
  if (origin->kind == M68K_RENDER_TYPED_ORIGIN_STACK_SLOT) {
    for (index = 0U; index < state->stack_slot_count; ++index) {
      M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
      if (slot->known != 0U && slot->displacement == origin->displacement &&
          typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
        slot->value.provenance =
          typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
        changed = 1;
        break;
      }
    }
  } else if (origin->kind == M68K_RENDER_TYPED_ORIGIN_BASE_SLOT) {
    M68kRenderTypedBaseSlot *slot = typed_state_mutable_base_slot_entry(state, origin->base_reg,
      (int16_t)origin->displacement);
    if (slot != NULL && typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->value.provenance =
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
      changed = 1;
    }
  } else if (origin->kind == M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE) {
    if (render_lookup_promote_typed_storage_slot(lookup, origin, root_struct_id, refined_struct_id,
        source_section_index, source_offset, &changed) != 0) {
      return -1;
    }
  }
  if (out_changed != NULL) *out_changed = changed;
  return 0;
}

static int typed_state_refine_address_reg_from_prefix(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    uint8_t reg_index, uint16_t root_struct_id, uint16_t refined_struct_id, size_t source_section_index,
    uint32_t source_offset, int *out_changed) {
  int origin_changed = 0;
  if (out_changed != NULL) *out_changed = 0;
  if (state == NULL || reg_index >= 8U || root_struct_id == AMIGA_OS_STRUCT_ID_NONE ||
      refined_struct_id == AMIGA_OS_STRUCT_ID_NONE || !state->addr_regs[reg_index].known ||
      state->addr_regs[reg_index].struct_id != root_struct_id ||
      !amiga_struct_base_chain_contains(refined_struct_id, root_struct_id)) {
    return 0;
  }
  if (typed_state_promote_origin_struct(lookup, state, &state->addr_regs[reg_index].origin, root_struct_id,
      refined_struct_id, source_section_index, source_offset, &origin_changed) != 0) {
    return -1;
  }
  state->addr_regs[reg_index].struct_id = refined_struct_id;
  state->addr_regs[reg_index].output = NULL;
  state->addr_regs[reg_index].provenance =
    typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
  if (out_changed != NULL) *out_changed = 1;
  (void)origin_changed;
  return 0;
}

static int typed_reg_value_same_type_source(const M68kRenderTypedRegValue *left,
    const M68kRenderTypedStoredValue *right) {
  if (left == NULL || right == NULL || left->known == 0U || !typed_stored_value_has_useful_info(right))
    return 0;
  if (left->output != NULL && left->output == right->output) return 1;
  return left->struct_id != AMIGA_OS_STRUCT_ID_NONE && left->struct_id == right->struct_id &&
    typed_provenances_equal(&left->provenance, &right->provenance);
}

static int typed_state_promote_matching_stored_values(M68kRenderTypedState *state,
    const M68kRenderTypedRegValue *source, uint16_t root_struct_id, uint16_t refined_struct_id,
    size_t source_section_index, uint32_t source_offset) {
  size_t index;
  int changed = 0;
  if (state == NULL || source == NULL || root_struct_id == AMIGA_OS_STRUCT_ID_NONE ||
      refined_struct_id == AMIGA_OS_STRUCT_ID_NONE) {
    return 0;
  }
  for (index = 0U; index < state->stack_slot_count; ++index) {
    M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
    if (slot->known != 0U && typed_reg_value_same_type_source(source, &slot->value) &&
        typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->value.provenance =
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
      changed = 1;
    }
  }
  for (index = 0U; index < state->base_slot_count; ++index) {
    M68kRenderTypedBaseSlot *slot = &state->base_slots[index];
    if (slot->known != 0U && typed_reg_value_same_type_source(source, &slot->value) &&
        typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->value.provenance =
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
      changed = 1;
    }
  }
  return changed;
}

static int instruction_stores_typed_reg_to_a6_slot(const M68kRenderTypedState *state,
    const M68kInstructionIR *instruction, int a6_is_known_library_base, int16_t *out_displacement,
    const AmigaOsCallOutputInfo **out_output) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const AmigaOsCallOutputInfo *output;
  if (out_displacement != NULL) *out_displacement = 0;
  if (out_output != NULL) *out_output = NULL;
  if (state == NULL || instruction == NULL || out_displacement == NULL || out_output == NULL) return 0;
  if (a6_is_known_library_base) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || instruction->size_suffix != 'l' ||
      instruction->operand_count != 2U) {
    return 0;
  }
  output = typed_state_output_for_operand(state, &instruction->operands[0], NULL, NULL);
  if (output == NULL) return 0;
  if (!operand_is_address_displacement_local(&instruction->operands[1], &base_reg, &displacement) ||
      base_reg != 6U) {
    return 0;
  }
  *out_displacement = displacement;
  *out_output = output;
  return 1;
}

static int render_lookup_record_typed_struct_accesses(M68kRenderLookup *lookup, size_t section_index,
    M68kRenderTypedState *state, const M68kInstructionIR *instruction, uint32_t offset, int record_accesses,
    int *io_changed) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t base_reg = 0U, classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP;
    int16_t displacement = 0;
    uint16_t struct_id, struct_size, container_struct_id = AMIGA_OS_STRUCT_ID_NONE, container_candidate_count = 0U;
    char container_struct_name[64], container_field_expr[96], field_expr[96];
    int refinement_applied = 0;
    AmigaOsResolvedStructFieldInfo field;
    container_struct_name[0] = '\0';
    container_field_expr[0] = '\0';
    /*
     * Keep zero-offset (An) field facts analysis-only. Rendering FIELD(a0) would
     * force d16(An) encoding and break exact reproduction of original (An) bytes.
     */
    if (metadata != NULL && metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_BRANCH_TARGET)
      continue;
    if (!operand_is_address_displacement_local(operand, &base_reg, &displacement) || base_reg >= 8U) continue;
    if (!state->addr_regs[base_reg].known) continue;
    struct_id = state->addr_regs[base_reg].struct_id;
    if (struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    struct_size = amiga_struct_size_for_struct_id(struct_id);
    if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, displacement, 0, &field)) {
      classify_unresolved_typed_access(struct_id, displacement, struct_size,
        instruction_size_suffix_bytes_local(instruction->size_suffix), &classification, &container_candidate_count,
        container_struct_name, sizeof(container_struct_name), container_field_expr, sizeof(container_field_expr),
        &container_struct_id);
      if (classification == M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION &&
          container_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
        if (typed_state_refine_address_reg_from_prefix(lookup, state, base_reg, struct_id, container_struct_id,
            section_index, offset, &refinement_applied) != 0) {
          return -1;
        }
        if (refinement_applied && io_changed != NULL) *io_changed = 1;
      }
      if (record_accesses) {
        if (render_lookup_add_unresolved_typed_access(lookup, section_index, offset, (uint8_t)operand_index,
            base_reg, displacement, struct_id, struct_size, (uint8_t)(refinement_applied ? 1U : 0U),
            refinement_applied ? container_struct_id : AMIGA_OS_STRUCT_ID_NONE,
            &state->addr_regs[base_reg].provenance) != 0) {
          return -1;
        }
      }
      continue;
    }
    if (!amiga_os_resolve_struct_field_symbol_expr_by_struct_id(struct_id, displacement, 0,
        field_expr, sizeof(field_expr))) {
      if (record_accesses) {
        if (render_lookup_add_unresolved_typed_access(lookup, section_index, offset, (uint8_t)operand_index,
            base_reg, displacement, struct_id, struct_size, 0U, AMIGA_OS_STRUCT_ID_NONE,
            &state->addr_regs[base_reg].provenance) != 0) {
          return -1;
        }
      }
      continue;
    }
    if (record_accesses) {
      if (render_lookup_add_typed_access(lookup, section_index, offset, (uint8_t)operand_index, base_reg,
          displacement, struct_id, &field, field_expr, &state->addr_regs[base_reg].provenance) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int typed_flow_apply_call_input_type_refs(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, M68kRenderTypedState *state, const AmigaOsLibraryVectorInfo *vector,
    int allow_lookup_storage, int *io_changed) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t index;
  if (lookup == NULL || state == NULL || vector == NULL) return 0;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL) return 0;
  for (index = 0U; index < input_count; ++index) {
    const AmigaOsCallInputInfo *input = &inputs[index];
    int added = 0;
    if (input->struct_id == AMIGA_OS_STRUCT_ID_NONE ||
        input->reg_kind != AMIGA_OS_REGISTER_ADDRESS || input->reg_index >= 8U) {
      continue;
    }
    if (allow_lookup_storage && state->app_addr_regs[input->reg_index].known) {
      if (render_lookup_add_typed_app_slot_region(lookup, state->app_addr_regs[input->reg_index].displacement,
          input->struct_id, section_index, offset, &added) != 0) {
        return -1;
      }
      if (added && io_changed != NULL) *io_changed = 1;
    }
    if (state->addr_regs[input->reg_index].known &&
        state->addr_regs[input->reg_index].struct_id != input->struct_id &&
        amiga_struct_base_chain_contains(input->struct_id, state->addr_regs[input->reg_index].struct_id)) {
      int refined = 0;
      uint16_t root_struct_id = state->addr_regs[input->reg_index].struct_id;
      M68kRenderTypedRegValue input_value = state->addr_regs[input->reg_index];
      if (typed_state_refine_address_reg_from_prefix(lookup, state, input->reg_index,
          root_struct_id, input->struct_id, section_index, offset, &refined) != 0) {
        return -1;
      }
      if (typed_state_promote_matching_stored_values(state, &input_value, root_struct_id, input->struct_id,
          section_index, offset)) {
        refined = 1;
      }
      if (refined && io_changed != NULL) *io_changed = 1;
    }
  }
  return 0;
}

int instruction_operand_writes_register_from_metadata(const M68kInstructionIR *instruction,
    size_t operand_index) {
  const M68kSimFormMetadata *metadata;
  uint8_t access_kind;
  if (instruction == NULL || operand_index >= instruction->operand_count) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return operand_index + 1U == instruction->operand_count;
  access_kind = metadata->operand_access_kinds[operand_index];
  return access_kind == M68K_SIM_ACCESS_REGISTER_WRITE ||
    access_kind == M68K_SIM_ACCESS_REGISTER_LIST_WRITE;
}

static int instruction_move_operand_indices_from_metadata(const M68kInstructionIR *instruction,
    size_t *out_source_index, size_t *out_dest_index, const M68kSimFormMetadata **out_metadata) {
  const M68kSimFormMetadata *metadata;
  if (out_source_index != NULL) *out_source_index = 0U;
  if (out_dest_index != NULL) *out_dest_index = 0U;
  if (out_metadata != NULL) *out_metadata = NULL;
  if (instruction == NULL || instruction->operand_count == 0U) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_MOVE ||
      metadata->source_operand_index >= instruction->operand_count ||
      metadata->dest_operand_index >= instruction->operand_count) {
    return 0;
  }
  if (out_source_index != NULL) *out_source_index = metadata->source_operand_index;
  if (out_dest_index != NULL) *out_dest_index = metadata->dest_operand_index;
  if (out_metadata != NULL) *out_metadata = metadata;
  return 1;
}

static int instruction_may_update_stack_pointer_from_metadata(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (instruction == NULL) return 1;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 1;
  if (metadata->sp_effect_count != 0U) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        operand_address_register_index_local(&instruction->operands[operand_index], &reg) && reg == 7U) {
      return 1;
    }
    if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_NONE &&
        (operand_is_predec_a7_local(&instruction->operands[operand_index]) ||
         operand_is_postinc_a7_local(&instruction->operands[operand_index]))) {
      return 1;
    }
  }
  return 0;
}

static int render_lookup_record_typed_storage_store(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    const M68kRenderPlatformState *platform_state, size_t section_index, const M68kInstructionIR *instruction,
    uint32_t offset, int allow_lookup_storage, int *io_changed) {
  const M68kSimFormMetadata *metadata = NULL;
  size_t source_index = 0U, dest_index = 0U;
  uint8_t base_reg = 0U;
  int16_t base_displacement = 0, stack_displacement = 0;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  if (!instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata))
    return 0;
  if (metadata == NULL || metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE) return 0;
  const M68kOperandIR *source_operand = &instruction->operands[source_index];
  const M68kOperandIR *dest_operand = &instruction->operands[dest_index];
  M68kRenderTypedStoredValue value = typed_stored_value_for_operand(state, source_operand);
  if (!typed_stored_value_has_useful_info(&value) &&
      metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ) {
    (void)typed_value_for_memory_read_operand(lookup, state, platform_state, section_index, source_operand,
      metadata->operand_access_kinds[source_index], &value, NULL);
    if (!typed_stored_value_has_useful_info(&value) && instruction->size_suffix == 'l')
      (void)typed_stored_value_from_field_pointer_read(&value, state, source_operand, section_index, offset);
  }
  if (operand_is_stack_displacement_local(dest_operand, &stack_displacement)) {
    if (typed_stored_value_has_useful_info(&value)) typed_state_set_stack_slot(state, stack_displacement, &value);
    else typed_state_clear_stack_slot(state, stack_displacement);
    return 0;
  }
  if (operand_is_address_memory_local(dest_operand, &base_reg, &base_displacement) && base_reg < 8U &&
      base_reg != 7U && !render_state_operand_uses_app_base(platform_state, base_reg, base_displacement)) {
    if (typed_stored_value_has_useful_info(&value)) typed_state_set_base_slot(state, base_reg, base_displacement,
      &value);
    else typed_state_clear_base_slot(state, base_reg, base_displacement);
    if (!allow_lookup_storage || !state->memory_base_regs[base_reg].known) return 0;
  }
  if (!allow_lookup_storage) return 0;
  {
    uint8_t storage_kind = 0U;
    size_t storage_section = (size_t)-1;
    int32_t storage_displacement = 0;
    uint32_t storage_address = 0U;
    int added = 0;
    if (!typed_storage_key_for_lookup_memory_operand(lookup, state, platform_state, section_index, dest_operand,
        metadata->operand_access_kinds[dest_index], &storage_kind, &storage_section, &storage_displacement,
        &storage_address)) {
      return 0;
    }
    if (!typed_stored_value_has_useful_info(&value)) {
      if (render_lookup_conflict_typed_storage_slot(lookup, storage_kind, storage_section, storage_displacement,
          storage_address, section_index, offset, &added) != 0) {
        return -1;
      }
      if (added && io_changed != NULL) *io_changed = 1;
      if (storage_kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
        size_t app_index;
        for (app_index = 0U; app_index < lookup->typed_app_slot_count; ++app_index) {
          M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[app_index];
          if (slot->displacement != (int16_t)storage_displacement || slot->conflicted != 0U) continue;
          slot->conflicted = 1U;
          slot->source_section_index = section_index;
          slot->source_offset = offset;
          if (io_changed != NULL) *io_changed = 1;
        }
      }
      return 0;
    }
    if (render_lookup_add_typed_storage_slot(lookup, storage_kind, storage_section, storage_displacement,
        storage_address, &value, section_index, offset, &added) != 0) {
      return -1;
    }
    if (added && io_changed != NULL) *io_changed = 1;
    if (storage_kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT && value.struct_id != AMIGA_OS_STRUCT_ID_NONE) {
      added = 0;
      if (render_lookup_add_typed_app_slot(lookup, (int16_t)storage_displacement, value.struct_id,
          section_index, offset, &added) != 0) {
        return -1;
      }
      if (added && io_changed != NULL) *io_changed = 1;
    }
  }
  return 0;
}

static void render_lookup_conflict_typed_app_slot_for_write(M68kRenderLookup *lookup, int16_t displacement,
    size_t section_index, uint32_t offset, int *io_changed) {
  size_t app_index;
  if (lookup == NULL) return;
  for (app_index = 0U; app_index < lookup->typed_app_slot_count; ++app_index) {
    M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[app_index];
    if (slot->displacement != displacement || slot->conflicted != 0U) continue;
    slot->conflicted = 1U;
    slot->source_section_index = section_index;
    slot->source_offset = offset;
    if (io_changed != NULL) *io_changed = 1;
  }
}

static int render_lookup_record_untyped_memory_writes(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    const M68kRenderPlatformState *platform_state, size_t section_index, const M68kInstructionIR *instruction,
    uint32_t offset, int allow_lookup_storage, int *io_changed) {
  const M68kSimFormMetadata *metadata = NULL;
  size_t source_index = 0U, dest_index = 0U, operand_index;
  uint8_t base_reg = 0U;
  int16_t base_displacement = 0, stack_displacement = 0;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  if (instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata))
    return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t storage_kind = 0U;
    size_t storage_section = (size_t)-1;
    int32_t storage_displacement = 0;
    uint32_t storage_address = 0U;
    int added = 0;
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_MEMORY_WRITE) continue;
    if (operand_is_stack_displacement_local(operand, &stack_displacement)) {
      typed_state_clear_stack_slot(state, stack_displacement);
    }
    if (operand_is_address_memory_local(operand, &base_reg, &base_displacement) && base_reg < 8U &&
        base_reg != 7U && !render_state_operand_uses_app_base(platform_state, base_reg, base_displacement)) {
      typed_state_clear_base_slot(state, base_reg, base_displacement);
    }
    if (!allow_lookup_storage) continue;
    if (!typed_storage_key_for_lookup_memory_operand(lookup, state, platform_state, section_index, operand,
        metadata->operand_access_kinds[operand_index], &storage_kind, &storage_section, &storage_displacement,
        &storage_address)) {
      continue;
    }
    if (render_lookup_conflict_typed_storage_slot(lookup, storage_kind, storage_section, storage_displacement,
        storage_address, section_index, offset, &added) != 0) {
      return -1;
    }
    if (added && io_changed != NULL) *io_changed = 1;
    if (storage_kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
      render_lookup_conflict_typed_app_slot_for_write(lookup, (int16_t)storage_displacement, section_index, offset,
        io_changed);
    }
  }
  return 0;
}

static void typed_state_update_after_instruction(M68kRenderTypedState *state, const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform_state, size_t section_index, const M68kInstructionIR *instruction,
    const M68kDecodeCandidate *candidate, const AmigaOsLibraryVectorInfo *vector, uint32_t offset) {
  const M68kSimFormMetadata *move_metadata = NULL;
  const AmigaOsCallOutputInfo *source_output = NULL;
  uint16_t source_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  M68kRenderTypedStorageOrigin source_origin;
  M68kRenderTypedProvenance source_provenance;
  M68kRenderTypedMemoryBaseValue source_memory_base;
  size_t operand_index, source_index = 0U, dest_index = 0U;
  uint8_t dest_reg = 0U, bit;
  int16_t source_app_displacement = 0;
  int source_is_app_address = 0;
  int source_has_memory_base = 0;
  if (state == NULL || instruction == NULL) return;
  typed_origin_clear(&source_origin);
  typed_provenance_clear(&source_provenance);
  typed_memory_base_clear(&source_memory_base);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_BSR) {
    if (vector != NULL) typed_state_apply_platform_call_clobbers(state);
    else typed_state_clear_all(state);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    for (bit = 0U; bit < 8U; ++bit) {
      if ((instruction->operands[1].value.value & (1UL << bit)) != 0U) typed_state_clear_reg(state, 1U, bit);
      if ((instruction->operands[1].value.value & (1UL << (8U + bit))) != 0U) typed_state_clear_reg(state, 2U, bit);
    }
  } else if (instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
      &move_metadata)) {
    M68kRenderTypedStoredValue stored_value;
    const M68kOperandIR *source_operand = &instruction->operands[source_index];
    const M68kOperandIR *dest_operand = &instruction->operands[dest_index];
    typed_stored_value_clear(&stored_value);
    source_output = typed_state_output_for_operand(state, source_operand, NULL, NULL);
    source_struct_id = typed_state_struct_id_for_operand(state, source_operand);
    source_is_app_address = typed_state_copy_app_address(state, source_operand, &source_app_displacement);
    source_has_memory_base = typed_state_copy_memory_base(state, source_operand, &source_memory_base);
    (void)typed_state_origin_for_operand(state, source_operand, &source_origin);
    source_provenance = typed_stored_value_for_operand(state, source_operand).provenance;
    if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE && move_metadata != NULL &&
        move_metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        typed_value_for_memory_read_operand(lookup, state, platform_state, section_index, source_operand,
          move_metadata->operand_access_kinds[source_index], &stored_value, &source_origin)) {
      source_output = stored_value.output;
      source_struct_id = stored_value.struct_id;
      source_is_app_address = stored_value.app_address_known;
      source_app_displacement = stored_value.app_displacement;
      source_provenance = stored_value.provenance;
    }
    if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE && move_metadata != NULL &&
        move_metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        instruction->size_suffix == 'l') {
      if (typed_stored_value_from_field_pointer_read(&stored_value, state, source_operand, section_index, offset)) {
        source_struct_id = stored_value.struct_id;
        source_provenance = stored_value.provenance;
      }
    }
    if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE) {
      source_struct_id = typed_struct_id_for_base_slot_operand(lookup, platform_state, source_operand);
      if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE)
        source_provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_BASE_SLOT, section_index, offset);
    }
    if (operand_is_data_register_local(dest_operand, &dest_reg)) {
      typed_state_clear_reg(state, 1U, dest_reg);
      if (source_output != NULL &&
          (source_struct_id == AMIGA_OS_STRUCT_ID_NONE || source_output->struct_id != AMIGA_OS_STRUCT_ID_NONE)) {
        typed_state_set_reg(state, 1U, dest_reg, source_output, &source_provenance);
      } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
        typed_state_set_reg_struct_id(state, 1U, dest_reg, source_struct_id, &source_provenance);
      }
      if (source_is_app_address) typed_state_set_data_app_address(state, dest_reg, source_app_displacement);
      if (source_has_memory_base)
        typed_state_set_memory_base(state, 1U, dest_reg, source_memory_base.section_index, source_memory_base.offset);
      typed_state_set_reg_origin(state, 1U, dest_reg, &source_origin);
    } else if (operand_address_register_index_local(dest_operand, &dest_reg)) {
      typed_state_clear_reg(state, 2U, dest_reg);
      if (source_is_app_address) typed_state_set_app_address(state, dest_reg, source_app_displacement,
        source_struct_id, &source_provenance);
      else if (source_output != NULL &&
          (source_struct_id == AMIGA_OS_STRUCT_ID_NONE || source_output->struct_id != AMIGA_OS_STRUCT_ID_NONE)) {
        typed_state_set_reg(state, 2U, dest_reg, source_output, &source_provenance);
      } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
        typed_state_set_reg_struct_id(state, 2U, dest_reg, source_struct_id, &source_provenance);
      }
      if (source_has_memory_base)
        typed_state_set_memory_base(state, 2U, dest_reg, source_memory_base.section_index, source_memory_base.offset);
      typed_state_set_reg_origin(state, 2U, dest_reg, &source_origin);
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U) {
    if (operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
      uint8_t source_base_reg = 0U;
      int16_t source_displacement = 0;
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      typed_state_clear_reg(state, 2U, dest_reg);
      source_struct_id = AMIGA_OS_STRUCT_ID_NONE;
      if (typed_app_address_operand_info(lookup, platform_state, &instruction->operands[0],
          &source_app_displacement, &source_struct_id)) {
        M68kRenderTypedProvenance app_provenance =
          typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_APP_SLOT, section_index, offset);
        typed_state_set_app_address(state, dest_reg, source_app_displacement, source_struct_id, &app_provenance);
      } else if (operand_is_address_memory_local(&instruction->operands[0], &source_base_reg,
          &source_displacement) && source_base_reg < 8U && state->addr_regs[source_base_reg].known) {
        if (source_displacement == 0) {
          source_struct_id = state->addr_regs[source_base_reg].struct_id;
          if (state->app_addr_regs[source_base_reg].known) {
            typed_state_set_app_address(state, dest_reg, state->app_addr_regs[source_base_reg].displacement,
              source_struct_id, &state->addr_regs[source_base_reg].provenance);
          } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
            typed_state_set_reg_struct_id(state, 2U, dest_reg, source_struct_id,
              &state->addr_regs[source_base_reg].provenance);
            typed_state_set_reg_origin(state, 2U, dest_reg, &state->addr_regs[source_base_reg].origin);
          }
        } else {
          source_struct_id = typed_nested_struct_id_for_field_address(state, &instruction->operands[0]);
          if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
            M68kRenderTypedProvenance field_provenance =
              typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_FIELD_ADDRESS, section_index, offset);
            typed_state_set_reg_struct_id(state, 2U, dest_reg, source_struct_id, &field_provenance);
          }
        }
      }
      if (candidate_loads_data_target_to_address_reg(candidate, instruction, &target_section_index, &target_offset,
          &dest_reg) ||
          candidate_loads_runtime_address_ref_target_to_address_reg(lookup, section_index, candidate, instruction,
            &target_section_index, &target_offset, &dest_reg)) {
        typed_state_set_memory_base(state, 2U, dest_reg, target_section_index, target_offset);
      } else if (operand_is_address_memory_local(&instruction->operands[0], &source_base_reg,
          &source_displacement) && source_base_reg < 8U && state->memory_base_regs[source_base_reg].known) {
        uint32_t next_offset = 0U;
        if (typed_memory_base_offset_add(state->memory_base_regs[source_base_reg].offset, source_displacement,
            &next_offset)) {
          typed_state_set_memory_base(state, 2U, dest_reg, state->memory_base_regs[source_base_reg].section_index,
            next_offset);
        }
      }
    }
  } else if (instruction->operand_count != 0U) {
    for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
      const M68kOperandIR *operand = &instruction->operands[operand_index];
      if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
      if (operand_is_data_register_local(operand, &dest_reg)) {
        typed_state_clear_reg(state, 1U, dest_reg);
      } else if (operand_address_register_index_local(operand, &dest_reg)) {
        typed_state_clear_reg(state, 2U, dest_reg);
      }
    }
  }
  if (instruction_may_update_stack_pointer_from_metadata(instruction)) typed_state_clear_stack_slots(state);
  if (vector != NULL && amiga_output_has_typed_info(&vector->output)) {
    M68kRenderTypedProvenance api_provenance =
      typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_API_OUTPUT, section_index, offset);
    typed_state_set_reg(state, vector->output.reg_kind, vector->output.reg_index, &vector->output, &api_provenance);
  }
}

static int typed_reg_values_equal(const M68kRenderTypedRegValue *left,
    const M68kRenderTypedRegValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->output == right->output && left->struct_id == right->struct_id &&
    typed_origins_equal(&left->origin, &right->origin) &&
    typed_provenances_equal(&left->provenance, &right->provenance);
}

static int typed_stored_values_equal(const M68kRenderTypedStoredValue *left,
    const M68kRenderTypedStoredValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->output == right->output && left->struct_id == right->struct_id &&
    left->app_address_known == right->app_address_known && left->app_displacement == right->app_displacement &&
    typed_provenances_equal(&left->provenance, &right->provenance);
}

static int typed_app_addresses_equal(const M68kRenderTypedAppAddressValue *left,
    const M68kRenderTypedAppAddressValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->displacement == right->displacement;
}

static int typed_memory_bases_equal(const M68kRenderTypedMemoryBaseValue *left,
    const M68kRenderTypedMemoryBaseValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->section_index == right->section_index && left->offset == right->offset;
}

static int typed_stack_slots_equal(const M68kRenderTypedStackSlot *left,
    const M68kRenderTypedStackSlot *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->displacement == right->displacement &&
    typed_stored_values_equal(&left->value, &right->value);
}

static int typed_base_slots_equal(const M68kRenderTypedBaseSlot *left,
    const M68kRenderTypedBaseSlot *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->base_reg == right->base_reg &&
    left->displacement == right->displacement && typed_stored_values_equal(&left->value, &right->value);
}

static int typed_base_slot_sets_equal(const M68kRenderTypedState *left, const M68kRenderTypedState *right) {
  size_t index;
  if (left == NULL || right == NULL || left->base_slot_count != right->base_slot_count) return 0;
  for (index = 0U; index < left->base_slot_count; ++index) {
    const M68kRenderTypedBaseSlot *left_slot = &left->base_slots[index];
    const M68kRenderTypedBaseSlot *right_slot = typed_state_base_slot_entry(right, left_slot->base_reg,
      left_slot->displacement);
    if (!typed_base_slots_equal(left_slot, right_slot)) return 0;
  }
  return 1;
}

static int typed_state_equal(const M68kRenderTypedState *left, const M68kRenderTypedState *right) {
  size_t index;
  if (left == NULL || right == NULL || left->stack_slot_count != right->stack_slot_count ||
      left->base_slot_count != right->base_slot_count) {
    return 0;
  }
  for (index = 0U; index < 8U; ++index) {
    if (!typed_reg_values_equal(&left->data_regs[index], &right->data_regs[index])) return 0;
    if (!typed_reg_values_equal(&left->addr_regs[index], &right->addr_regs[index])) return 0;
    if (!typed_app_addresses_equal(&left->data_app_addr_regs[index], &right->data_app_addr_regs[index])) return 0;
    if (!typed_app_addresses_equal(&left->app_addr_regs[index], &right->app_addr_regs[index])) return 0;
    if (!typed_memory_bases_equal(&left->data_memory_base_regs[index], &right->data_memory_base_regs[index]))
      return 0;
    if (!typed_memory_bases_equal(&left->memory_base_regs[index], &right->memory_base_regs[index])) return 0;
  }
  for (index = 0U; index < left->stack_slot_count; ++index) {
    if (!typed_stack_slots_equal(&left->stack_slots[index], &right->stack_slots[index])) return 0;
  }
  if (!typed_base_slot_sets_equal(left, right)) return 0;
  return 1;
}

static int platform_states_equal(const M68kRenderPlatformState *left, const M68kRenderPlatformState *right) {
  if (left == NULL || right == NULL) return 0;
  return memcmp(left, right, sizeof(*left)) == 0;
}

static int typed_reg_merge(M68kRenderTypedRegValue *dest, const M68kRenderTypedRegValue *source) {
  M68kRenderTypedRegValue old_value;
  if (dest == NULL || source == NULL) return 0;
  old_value = *dest;
  if (dest->known == 0U || source->known == 0U) {
    typed_reg_value_clear(dest);
    return !typed_reg_values_equal(dest, &old_value);
  }
  if (dest->output == source->output && dest->struct_id == source->struct_id) {
    if (!typed_origins_equal(&dest->origin, &source->origin)) typed_origin_clear(&dest->origin);
    typed_provenance_merge(&dest->provenance, &source->provenance);
    return !typed_reg_values_equal(dest, &old_value);
  }
  {
    uint16_t common_struct_id = typed_struct_id_common_merge(dest->struct_id, source->struct_id);
    if (common_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
      dest->struct_id = common_struct_id;
      dest->output = NULL;
      if (!typed_origins_equal(&dest->origin, &source->origin)) typed_origin_clear(&dest->origin);
      typed_provenance_merge(&dest->provenance, &source->provenance);
      return !typed_reg_values_equal(dest, &old_value);
    }
  }
  if (dest->struct_id != AMIGA_OS_STRUCT_ID_NONE && dest->struct_id == source->struct_id) {
    dest->output = NULL;
    return !typed_reg_values_equal(dest, &old_value);
  }
  typed_reg_value_clear(dest);
  return !typed_reg_values_equal(dest, &old_value);
}

static int typed_stored_value_merge(M68kRenderTypedStoredValue *dest,
    const M68kRenderTypedStoredValue *source) {
  M68kRenderTypedStoredValue old_value;
  if (dest == NULL || source == NULL) return 0;
  old_value = *dest;
  if (!typed_stored_value_has_useful_info(dest) || !typed_stored_value_has_useful_info(source)) {
    typed_stored_value_clear(dest);
    return !typed_stored_values_equal(dest, &old_value);
  }
  if (dest->app_address_known != source->app_address_known ||
      dest->app_displacement != source->app_displacement) {
    dest->app_address_known = 0U;
    dest->app_displacement = 0;
  }
  if (dest->output != source->output) dest->output = NULL;
  typed_provenance_merge(&dest->provenance, &source->provenance);
  dest->struct_id = typed_struct_id_common_merge(dest->struct_id, source->struct_id);
  if (dest->output != NULL && dest->struct_id != AMIGA_OS_STRUCT_ID_NONE &&
      dest->output->struct_id != dest->struct_id) {
    dest->output = NULL;
  }
  typed_stored_value_update_known(dest);
  return !typed_stored_values_equal(dest, &old_value);
}

static int typed_state_merge_stack_slots(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  size_t dest_index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  for (dest_index = 0U; dest_index < dest->stack_slot_count;) {
    M68kRenderTypedStackSlot *dest_slot = &dest->stack_slots[dest_index];
    const M68kRenderTypedStackSlot *source_slot = NULL;
    size_t source_index;
    for (source_index = 0U; source_index < source->stack_slot_count; ++source_index) {
      if (source->stack_slots[source_index].known != 0U &&
          source->stack_slots[source_index].displacement == dest_slot->displacement) {
        source_slot = &source->stack_slots[source_index];
        break;
      }
    }
    if (source_slot == NULL || typed_stored_value_merge(&dest_slot->value, &source_slot->value) ||
        !typed_stored_value_has_useful_info(&dest_slot->value)) {
      if (source_slot == NULL || !typed_stored_value_has_useful_info(&dest_slot->value)) {
        dest->stack_slots[dest_index] = dest->stack_slots[dest->stack_slot_count - 1U];
        --dest->stack_slot_count;
        changed = 1;
        continue;
      }
      changed = 1;
    }
    ++dest_index;
  }
  return changed;
}

static int typed_state_merge_base_slots(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  size_t dest_index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  for (dest_index = 0U; dest_index < dest->base_slot_count;) {
    M68kRenderTypedBaseSlot *dest_slot = &dest->base_slots[dest_index];
    const M68kRenderTypedBaseSlot *source_slot = typed_state_base_slot_entry(source, dest_slot->base_reg,
      dest_slot->displacement);
    if (source_slot == NULL || typed_stored_value_merge(&dest_slot->value, &source_slot->value) ||
        !typed_stored_value_has_useful_info(&dest_slot->value)) {
      if (source_slot == NULL || !typed_stored_value_has_useful_info(&dest_slot->value)) {
        dest->base_slots[dest_index] = dest->base_slots[dest->base_slot_count - 1U];
        --dest->base_slot_count;
        changed = 1;
        continue;
      }
      changed = 1;
    }
    ++dest_index;
  }
  return changed;
}

static int typed_state_merge_into(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  size_t index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  for (index = 0U; index < 8U; ++index) {
    M68kRenderTypedAppAddressValue old_data_app = dest->data_app_addr_regs[index];
    M68kRenderTypedAppAddressValue old_app = dest->app_addr_regs[index];
    M68kRenderTypedMemoryBaseValue old_data_memory_base = dest->data_memory_base_regs[index];
    M68kRenderTypedMemoryBaseValue old_memory_base = dest->memory_base_regs[index];
    changed |= typed_reg_merge(&dest->data_regs[index], &source->data_regs[index]);
    changed |= typed_reg_merge(&dest->addr_regs[index], &source->addr_regs[index]);
    if (dest->data_app_addr_regs[index].known == 0U || source->data_app_addr_regs[index].known == 0U ||
        dest->data_app_addr_regs[index].displacement != source->data_app_addr_regs[index].displacement) {
      dest->data_app_addr_regs[index].known = 0U;
      dest->data_app_addr_regs[index].displacement = 0;
    }
    if (!typed_app_addresses_equal(&old_data_app, &dest->data_app_addr_regs[index])) changed = 1;
    if (dest->app_addr_regs[index].known == 0U || source->app_addr_regs[index].known == 0U ||
        dest->app_addr_regs[index].displacement != source->app_addr_regs[index].displacement) {
      dest->app_addr_regs[index].known = 0U;
      dest->app_addr_regs[index].displacement = 0;
    }
    if (!typed_app_addresses_equal(&old_app, &dest->app_addr_regs[index])) changed = 1;
    if (dest->data_memory_base_regs[index].known == 0U || source->data_memory_base_regs[index].known == 0U ||
        dest->data_memory_base_regs[index].section_index != source->data_memory_base_regs[index].section_index ||
        dest->data_memory_base_regs[index].offset != source->data_memory_base_regs[index].offset) {
      typed_memory_base_clear(&dest->data_memory_base_regs[index]);
    }
    if (!typed_memory_bases_equal(&old_data_memory_base, &dest->data_memory_base_regs[index])) changed = 1;
    if (dest->memory_base_regs[index].known == 0U || source->memory_base_regs[index].known == 0U ||
        dest->memory_base_regs[index].section_index != source->memory_base_regs[index].section_index ||
        dest->memory_base_regs[index].offset != source->memory_base_regs[index].offset) {
      typed_memory_base_clear(&dest->memory_base_regs[index]);
    }
    if (!typed_memory_bases_equal(&old_memory_base, &dest->memory_base_regs[index])) changed = 1;
  }
  if (typed_state_merge_stack_slots(dest, source)) changed = 1;
  if (typed_state_merge_base_slots(dest, source)) changed = 1;
  return changed;
}

static void platform_state_merge_register_name(uint8_t *dest_known, char *dest_name, size_t dest_name_size,
    uint8_t source_known, const char *source_name, int *io_changed) {
  if (dest_known == NULL || dest_name == NULL || source_name == NULL || io_changed == NULL) return;
  if (*dest_known == 0U || source_known == 0U || strcmp(dest_name, source_name) != 0) {
    if (*dest_known != 0U || dest_name[0] != '\0') *io_changed = 1;
    *dest_known = 0U;
    if (dest_name_size != 0U) dest_name[0] = '\0';
  }
}

static int platform_state_merge_into(M68kRenderPlatformState *dest, const M68kRenderPlatformState *source) {
  M68kRenderPlatformState old_state;
  size_t index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  old_state = *dest;
  for (index = 0U; index < 8U; ++index) {
    platform_state_merge_register_name(&dest->address_base_known[index], dest->address_base_library[index],
      sizeof(dest->address_base_library[index]), source->address_base_known[index],
      source->address_base_library[index], &changed);
    platform_state_merge_register_name(&dest->address_hardware_base_known[index],
      dest->address_hardware_base_symbol[index], sizeof(dest->address_hardware_base_symbol[index]),
      source->address_hardware_base_known[index], source->address_hardware_base_symbol[index], &changed);
    if (dest->data_app_base_known[index] != 0U && source->data_app_base_known[index] == 0U)
      dest->data_app_base_known[index] = 0U;
    if (dest->address_app_base_known[index] != 0U && source->address_app_base_known[index] == 0U)
      dest->address_app_base_known[index] = 0U;
  }
  if (dest->d0_lvo_known == 0U || source->d0_lvo_known == 0U || dest->d0_lvo != source->d0_lvo) {
    dest->d0_lvo_known = 0U;
    dest->d0_lvo = 0;
  }
  return changed || !platform_states_equal(dest, &old_state);
}

static int typed_flow_merge_input(M68kRenderTypedFlowNode *node, const M68kRenderTypedState *typed_state,
    const M68kRenderPlatformState *platform_state) {
  int changed = 0;
  if (node == NULL || typed_state == NULL || platform_state == NULL) return 0;
  if (node->has_in == 0U) {
    node->typed_in = *typed_state;
    node->platform_in = *platform_state;
    node->has_in = 1U;
    return 1;
  }
  if (typed_state_merge_into(&node->typed_in, typed_state)) changed = 1;
  if (platform_state_merge_into(&node->platform_in, platform_state)) changed = 1;
  return changed;
}

static int typed_flow_successors_for_candidate(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const size_t *node_by_offset, uint32_t node_by_offset_count, const M68kDecodeCandidate *candidate,
    size_t *out_successors, size_t successor_capacity) {
  size_t count = 0U;
  size_t target_index;
  uint32_t next_offset;
  int has_fallthrough;
  if (section == NULL || accepted_start == NULL || node_by_offset == NULL || candidate == NULL ||
      out_successors == NULL) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if ((target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_JUMP) ||
        !target->has_section || target->section_index != section->section_index ||
        target->offset >= node_by_offset_count || node_by_offset[target->offset] == SIZE_MAX) {
      continue;
    }
    if (count < successor_capacity) out_successors[count++] = node_by_offset[target->offset];
  }
  has_fallthrough = render_cfg_candidate_has_fallthrough(candidate);
  next_offset = candidate->offset + candidate->byte_count;
  if (has_fallthrough && next_offset < node_by_offset_count && accepted_start_at(section, accepted_start, next_offset) &&
      node_by_offset[next_offset] != SIZE_MAX && count < successor_capacity) {
    out_successors[count++] = node_by_offset[next_offset];
  }
  return (int)count;
}

typedef struct M68kTypedFlowCallResolution {
  const AmigaOsLibraryVectorInfo *vector;
  uint8_t output_reg_known;
  uint8_t output_reg_kind;
  uint8_t output_reg_index;
} M68kTypedFlowCallResolution;

static void typed_flow_call_resolution_init(M68kTypedFlowCallResolution *resolution) {
  if (resolution == NULL) return;
  memset(resolution, 0, sizeof(*resolution));
}

static int typed_flow_reg_matches_output(const M68kRenderTypedRegValue *value,
    const AmigaOsCallOutputInfo *output) {
  if (value == NULL || output == NULL || value->known == 0U) return 0;
  if (value->output == output) return 1;
  return output->struct_id != AMIGA_OS_STRUCT_ID_NONE && value->struct_id == output->struct_id;
}

static int typed_flow_choose_helper_output_reg(const M68kRenderTypedState *state,
    const AmigaOsCallOutputInfo *output, uint8_t *out_reg_kind, uint8_t *out_reg_index) {
  uint8_t reg;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (state == NULL || output == NULL) return 0;
  for (reg = 0U; reg < 8U; ++reg) {
    if (typed_flow_reg_matches_output(&state->addr_regs[reg], output)) {
      if (out_reg_kind != NULL) *out_reg_kind = AMIGA_OS_REGISTER_ADDRESS;
      if (out_reg_index != NULL) *out_reg_index = reg;
      return 1;
    }
  }
  for (reg = 0U; reg < 8U; ++reg) {
    if (typed_flow_reg_matches_output(&state->data_regs[reg], output)) {
      if (out_reg_kind != NULL) *out_reg_kind = AMIGA_OS_REGISTER_DATA;
      if (out_reg_index != NULL) *out_reg_index = reg;
      return 1;
    }
  }
  return 0;
}

static int typed_flow_infer_local_helper_output_reg_at(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t helper_offset,
    const AmigaOsLibraryVectorInfo *expected_vector, unsigned depth, uint8_t *out_reg_kind,
    uint8_t *out_reg_index) {
  const M68kDecodeSectionIR *section;
  M68kRenderTypedState typed_state;
  M68kRenderPlatformState platform_state;
  uint32_t cursor;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || expected_vector == NULL || depth > 4U ||
      section_index >= decode->section_count) {
    return 0;
  }
  section = &decode->sections[section_index];
  if (!accepted_start_at(section, accepted_start[section_index], helper_offset)) return 0;
  typed_state_clear_all(&typed_state);
  memset(&platform_state, 0, sizeof(platform_state));
  cursor = helper_offset;
  while (cursor < section->size && cursor - helper_offset < 256U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsLibraryVectorInfo *platform_vector;
    const AmigaOsLibraryVectorInfo *immediate_vector;
    const AmigaOsLibraryVectorInfo *wrapper_vector;
    const AmigaOsLibraryVectorInfo *direct_vector;
    const AmigaOsLibraryVectorInfo *local_helper_vector;
    const AmigaOsLibraryVectorInfo *vector;
    M68kTypedFlowCallResolution nested_resolution;
    if (!accepted_start_at(section, accepted_start[section_index], cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
      candidate->offset);
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
    if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_RTS) {
      return typed_flow_choose_helper_output_reg(&typed_state, &expected_vector->output,
        out_reg_kind, out_reg_index);
    }
    platform_vector = attach_amiga_lvo_symbol_if_known(&platform_state, &instruction);
    immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section_index],
      candidate, &instruction);
    wrapper_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
    direct_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
      section->section_index, candidate);
    local_helper_vector = (wrapper_vector == NULL && direct_vector == NULL)
      ? resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section->section_index, candidate)
      : NULL;
    vector = platform_vector != NULL ? platform_vector :
      (direct_vector != NULL ? direct_vector :
      (wrapper_vector != NULL ? wrapper_vector :
      (immediate_vector != NULL ? immediate_vector : local_helper_vector)));
    typed_flow_call_resolution_init(&nested_resolution);
    if (local_helper_vector != NULL) {
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      if (candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
          &target_offset) &&
          typed_flow_infer_local_helper_output_reg_at(lookup, decode, accepted_start, target_section_index,
            target_offset, local_helper_vector, depth + 1U, &nested_resolution.output_reg_kind,
            &nested_resolution.output_reg_index)) {
        nested_resolution.vector = local_helper_vector;
        nested_resolution.output_reg_known = 1U;
      }
    }
    typed_state_update_after_instruction(&typed_state, lookup, &platform_state, section->section_index,
      &instruction, candidate, vector, candidate->offset);
    if (nested_resolution.output_reg_known && nested_resolution.vector != NULL &&
        amiga_output_has_typed_info(&nested_resolution.vector->output)) {
      M68kRenderTypedProvenance api_provenance =
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_API_OUTPUT, section->section_index, candidate->offset);
      typed_state_set_reg(&typed_state, nested_resolution.output_reg_kind, nested_resolution.output_reg_index,
        &nested_resolution.vector->output, &api_provenance);
    }
    platform_state_update_d0_lvo_after_instruction(&platform_state, &instruction);
    platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    platform_state_note_call_result_after_instruction(&platform_state, &instruction, vector);
    if (!candidate_has_local_helper_summary_fallthrough(candidate))
      break;
    cursor += candidate->byte_count;
  }
  return 0;
}

static const AmigaOsLibraryVectorInfo *typed_flow_resolve_vector(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kRenderPlatformState *platform_state,
    M68kInstructionIR *instruction, M68kTypedFlowCallResolution *resolution) {
  const AmigaOsLibraryVectorInfo *platform_vector;
  const AmigaOsLibraryVectorInfo *immediate_vector;
  const AmigaOsLibraryVectorInfo *wrapper_call_vector;
  const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
  const AmigaOsLibraryVectorInfo *helper_call_vector = NULL;
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (resolution != NULL) typed_flow_call_resolution_init(resolution);
  if (lookup == NULL || decode == NULL || accepted_start == NULL || section == NULL || candidate == NULL ||
      platform_state == NULL || instruction == NULL) {
    return NULL;
  }
  platform_vector = attach_amiga_lvo_symbol_if_known(platform_state, instruction);
  immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section->section_index],
    candidate, instruction);
  wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, platform_state, section, candidate);
  direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
    section->section_index, candidate);
  if (platform_vector == NULL && immediate_vector == NULL && wrapper_call_vector == NULL &&
      direct_wrapper_vector == NULL) {
    helper_call_vector = resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section->section_index,
      candidate);
  }
  if (resolution != NULL) {
    resolution->vector = platform_vector != NULL ? platform_vector :
      (direct_wrapper_vector != NULL ? direct_wrapper_vector :
      (wrapper_call_vector != NULL ? wrapper_call_vector :
      (immediate_vector != NULL ? immediate_vector : helper_call_vector)));
    if (helper_call_vector != NULL &&
        candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
          &target_offset) &&
        typed_flow_infer_local_helper_output_reg_at(lookup, decode, accepted_start, target_section_index,
          target_offset, helper_call_vector, 0U, &resolution->output_reg_kind, &resolution->output_reg_index)) {
      resolution->output_reg_known = 1U;
    }
  }
  return platform_vector != NULL ? platform_vector :
    (direct_wrapper_vector != NULL ? direct_wrapper_vector :
    (wrapper_call_vector != NULL ? wrapper_call_vector :
    (immediate_vector != NULL ? immediate_vector : helper_call_vector)));
}

static int typed_flow_process_node(M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_start,
    const M68kDecodeSectionIR *section, const M68kRenderTypedFlowNode *node, int allow_lookup_storage,
    int record_typed_accesses, M68kRenderTypedState *out_typed_state, M68kRenderPlatformState *out_platform_state,
    int *io_changed) {
  M68kInstructionIR instruction;
  const AmigaOsLibraryVectorInfo *chosen_vector;
  M68kTypedFlowCallResolution call_resolution;
  const AmigaOsCallOutputInfo *stored_output = NULL;
  int16_t slot_displacement = 0;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || section == NULL || node == NULL ||
      out_typed_state == NULL || out_platform_state == NULL || node->candidate == NULL) {
    return -1;
  }
  *out_typed_state = node->typed_in;
  *out_platform_state = node->platform_in;
  platform_state_apply_policy_register_seeds(out_platform_state, lookup->policy, section->section_index,
    node->candidate->offset);
  if (m68k_decode_candidate_to_instruction(node->candidate, &instruction) != 0) return -1;
  attach_known_instruction_relocations(lookup, section->section_index, node->candidate, &instruction);
  typed_flow_call_resolution_init(&call_resolution);
  chosen_vector = typed_flow_resolve_vector(lookup, decode, accepted_start, section, node->candidate,
    out_platform_state, &instruction, &call_resolution);
  if (render_lookup_record_typed_struct_accesses(lookup, section->section_index, out_typed_state, &instruction,
      node->candidate->offset, record_typed_accesses, io_changed) != 0) {
    return -1;
  }
  if (!record_typed_accesses &&
      typed_flow_apply_call_input_type_refs(lookup, section->section_index,
      node->candidate->offset, out_typed_state, chosen_vector, allow_lookup_storage, io_changed) != 0) {
    return -1;
  }
  if (render_lookup_record_typed_storage_store(lookup, out_typed_state, out_platform_state, section->section_index,
      &instruction, node->candidate->offset, allow_lookup_storage, io_changed) != 0) {
    return -1;
  }
  if (render_lookup_record_untyped_memory_writes(lookup, out_typed_state, out_platform_state, section->section_index,
      &instruction, node->candidate->offset, allow_lookup_storage, io_changed) != 0) {
    return -1;
  }
  if (allow_lookup_storage && instruction_stores_typed_reg_to_a6_slot(out_typed_state, &instruction,
      out_platform_state->address_base_known[6U] != 0U, &slot_displacement, &stored_output) &&
      render_lookup_add_typed_slot_effect(lookup, section->section_index, node->candidate->offset,
        slot_displacement, stored_output) != 0) {
    return -1;
  }
  typed_state_update_after_instruction(out_typed_state, lookup, out_platform_state, section->section_index,
    &instruction, node->candidate, chosen_vector, node->candidate->offset);
  if (call_resolution.output_reg_known && call_resolution.vector != NULL &&
      amiga_output_has_typed_info(&call_resolution.vector->output)) {
    M68kRenderTypedProvenance api_provenance =
      typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_API_OUTPUT, section->section_index,
        node->candidate->offset);
    typed_state_set_reg(out_typed_state, call_resolution.output_reg_kind, call_resolution.output_reg_index,
      &call_resolution.vector->output, &api_provenance);
  }
  platform_state_update_d0_lvo_after_instruction(out_platform_state, &instruction);
  platform_state_update_after_instruction(out_platform_state, lookup, &instruction);
  platform_state_note_call_result_after_instruction(out_platform_state, &instruction, chosen_vector);
  if (candidate_terminates_a6_state(node->candidate)) typed_state_clear_all(out_typed_state);
  return 0;
}

static int typed_flow_build_nodes(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    M68kRenderTypedFlowNode **out_nodes, size_t *out_node_count, size_t **out_node_by_offset,
    uint32_t *out_node_by_offset_count) {
  M68kRenderTypedFlowNode *nodes = NULL;
  size_t *node_by_offset = NULL;
  size_t candidate_index;
  uint32_t render_extent;
  size_t node_count = 0U;
  if (out_nodes != NULL) *out_nodes = NULL;
  if (out_node_count != NULL) *out_node_count = 0U;
  if (out_node_by_offset != NULL) *out_node_by_offset = NULL;
  if (out_node_by_offset_count != NULL) *out_node_by_offset_count = 0U;
  if (section == NULL || accepted_start == NULL || out_nodes == NULL || out_node_count == NULL ||
      out_node_by_offset == NULL || out_node_by_offset_count == NULL) {
    return -1;
  }
  render_extent = render_section_extent(section);
  if (render_extent == 0U) return 0;
  nodes = (M68kRenderTypedFlowNode *)calloc(section->candidate_count, sizeof(*nodes));
  node_by_offset = (size_t *)malloc(((size_t)render_extent + 1U) * sizeof(*node_by_offset));
  if (nodes == NULL || node_by_offset == NULL) goto oom;
  for (candidate_index = 0U; candidate_index <= (size_t)render_extent; ++candidate_index)
    node_by_offset[candidate_index] = SIZE_MAX;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    if (!candidate_is_accepted_start(section, accepted_start, candidate) || candidate->offset >= render_extent)
      continue;
    nodes[node_count].candidate = candidate;
    node_by_offset[candidate->offset] = node_count;
    ++node_count;
  }
  *out_nodes = nodes;
  *out_node_count = node_count;
  *out_node_by_offset = node_by_offset;
  *out_node_by_offset_count = render_extent + 1U;
  return 0;

oom:
  free(nodes);
  free(node_by_offset);
  return -1;
}

static int typed_flow_initialize_roots(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    M68kRenderTypedFlowNode *nodes, size_t node_count, const size_t *node_by_offset,
    uint32_t node_by_offset_count) {
  uint16_t *incoming_counts = NULL;
  size_t node_index;
  int seeded_root = 0;
  if (node_count == 0U) return 0;
  incoming_counts = (uint16_t *)calloc(node_count, sizeof(*incoming_counts));
  if (incoming_counts == NULL) return -1;
  for (node_index = 0U; node_index < node_count; ++node_index) {
    size_t successors[5];
    int successor_count;
    int successor_index;
    successor_count = typed_flow_successors_for_candidate(section, accepted_start, node_by_offset,
      node_by_offset_count, nodes[node_index].candidate, successors, sizeof(successors) / sizeof(successors[0]));
    for (successor_index = 0; successor_index < successor_count; ++successor_index) {
      if (successors[successor_index] < node_count && incoming_counts[successors[successor_index]] < UINT16_MAX)
        ++incoming_counts[successors[successor_index]];
    }
  }
  for (node_index = 0U; node_index < node_count; ++node_index) {
    if (incoming_counts[node_index] != 0U) continue;
    typed_state_clear_all(&nodes[node_index].typed_in);
    memset(&nodes[node_index].platform_in, 0, sizeof(nodes[node_index].platform_in));
    nodes[node_index].has_in = 1U;
    seeded_root = 1;
  }
  if (!seeded_root) {
    typed_state_clear_all(&nodes[0].typed_in);
    memset(&nodes[0].platform_in, 0, sizeof(nodes[0].platform_in));
    nodes[0].has_in = 1U;
  }
  free(incoming_counts);
  return 0;
}

static size_t typed_flow_limit_from_env(const char *name, size_t default_value) {
  const char *text = getenv(name);
  const char *cursor;
  size_t value = 0U;
  if (text == NULL || text[0] == '\0') return default_value;
  for (cursor = text; *cursor != '\0'; ++cursor) {
    size_t digit;
    if (*cursor < '0' || *cursor > '9') return default_value;
    digit = (size_t)(*cursor - '0');
    if (value > (SIZE_MAX - digit) / 10U) return default_value;
    value = value * 10U + digit;
  }
  return value != 0U ? value : default_value;
}

static int render_lookup_analyze_amiga_typed_refs_for_section(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, const M68kDecodeSectionIR *section, int final_pass, int *io_changed) {
  M68kRenderTypedFlowNode *nodes = NULL;
  size_t *node_by_offset = NULL;
  uint32_t node_by_offset_count = 0U;
  size_t node_count = 0U;
  size_t iteration = 0U;
  size_t node_visit_count = 0U;
  size_t iteration_limit = typed_flow_limit_from_env("AMIGA_REVERSING_TYPED_FLOW_MAX_ITERATIONS",
    M68K_RENDER_TYPED_FLOW_DEFAULT_ITERATION_LIMIT);
  size_t node_visit_limit = typed_flow_limit_from_env("AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS",
    M68K_RENDER_TYPED_FLOW_DEFAULT_NODE_VISIT_LIMIT);
  int state_changed = 1;
  int result = -1;
  if (typed_flow_build_nodes(section, accepted_start[section->section_index], &nodes, &node_count, &node_by_offset,
      &node_by_offset_count) != 0) {
    return -1;
  }
  if (typed_flow_initialize_roots(section, accepted_start[section->section_index], nodes, node_count, node_by_offset,
      node_by_offset_count) != 0) {
    goto cleanup;
  }
  while (state_changed && iteration < node_count + 8U && iteration < iteration_limit &&
      node_visit_count < node_visit_limit) {
    size_t node_index;
    state_changed = 0;
    ++iteration;
    for (node_index = 0U; node_index < node_count; ++node_index) {
      M68kRenderTypedState next_typed_state;
      M68kRenderPlatformState next_platform_state;
      size_t successors[5];
      int successor_count, successor_index;
      if (nodes[node_index].has_in == 0U) continue;
      if (++node_visit_count > node_visit_limit) break;
      if (typed_flow_process_node(lookup, decode, accepted_start, section, &nodes[node_index], !final_pass,
          0, &next_typed_state, &next_platform_state, io_changed) != 0) {
        goto cleanup;
      }
      if (!typed_state_equal(&nodes[node_index].typed_out, &next_typed_state) ||
          !platform_states_equal(&nodes[node_index].platform_out, &next_platform_state)) {
        nodes[node_index].typed_out = next_typed_state;
        nodes[node_index].platform_out = next_platform_state;
        state_changed = 1;
      }
      successor_count = typed_flow_successors_for_candidate(section, accepted_start[section->section_index],
        node_by_offset, node_by_offset_count, nodes[node_index].candidate, successors,
        sizeof(successors) / sizeof(successors[0]));
      for (successor_index = 0; successor_index < successor_count; ++successor_index) {
        if (successors[successor_index] >= node_count) continue;
        if (typed_flow_merge_input(&nodes[successors[successor_index]], &next_typed_state, &next_platform_state))
          state_changed = 1;
      }
    }
  }
  if (final_pass) {
    size_t node_index;
    for (node_index = 0U; node_index < node_count; ++node_index) {
      M68kRenderTypedState ignored_typed_state;
      M68kRenderPlatformState ignored_platform_state;
      if (nodes[node_index].has_in == 0U) continue;
      if (typed_flow_process_node(lookup, decode, accepted_start, section, &nodes[node_index], 0,
          1, &ignored_typed_state, &ignored_platform_state, NULL) != 0) {
        goto cleanup;
      }
    }
  }
  result = 0;

cleanup:
  free(nodes);
  free(node_by_offset);
  return result;
}

static int render_lookup_analyze_amiga_typed_refs(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  int pass;
  int changed = 0;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (pass = 0; pass < 5; ++pass) {
    int final_pass = pass == 4;
    size_t section_index;
    changed = 0;
    if (final_pass) lookup->typed_access_count = 0U;
    for (section_index = 0U; section_index < decode->section_count; ++section_index) {
      if (render_lookup_analyze_amiga_typed_refs_for_section(lookup, decode, accepted_start,
          &decode->sections[section_index], final_pass, final_pass ? NULL : &changed) != 0) {
        return -1;
      }
    }
    if (!final_pass && !changed) pass = 3;
  }
  return 0;
}

static void data_pointer_state_clear_all(M68kRenderDataPointerState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void data_pointer_state_clear_reg(M68kRenderDataPointerState *state, uint8_t reg_kind, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) state->data_regs[reg_index].known = 0U;
  else if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) state->addr_regs[reg_index].known = 0U;
}

static void data_pointer_state_set_reg_with_exact(M68kRenderDataPointerState *state, uint8_t reg_kind,
    uint8_t reg_index, size_t section_index, uint32_t offset, uint8_t exact) {
  M68kRenderDataPointerValue *value;
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) value = &state->data_regs[reg_index];
  else if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) value = &state->addr_regs[reg_index];
  else return;
  value->known = 1U;
  value->exact = exact != 0U;
  value->dynamic_offset_known = 0U;
  value->section_index = section_index;
  value->offset = offset;
  value->dynamic_offset_section_index = 0U;
  value->dynamic_offset_offset = 0U;
}

static void data_pointer_state_set_reg(M68kRenderDataPointerState *state, uint8_t reg_kind, uint8_t reg_index,
    size_t section_index, uint32_t offset) {
  data_pointer_state_set_reg_with_exact(state, reg_kind, reg_index, section_index, offset, 1U);
}

static void data_pointer_state_copy_reg(M68kRenderDataPointerState *state, uint8_t reg_kind, uint8_t reg_index,
    const M68kRenderDataPointerValue *source) {
  M68kRenderDataPointerValue *dest;
  if (state == NULL || source == NULL || reg_index >= 8U) return;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) dest = &state->data_regs[reg_index];
  else if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) dest = &state->addr_regs[reg_index];
  else return;
  *dest = *source;
}

static int candidate_data_target_for_operand(const M68kDecodeCandidate *candidate, uint32_t operand_index,
    size_t *out_section_index, uint32_t *out_offset) {
  size_t target_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (candidate == NULL || out_section_index == NULL || out_offset == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_DATA || target->has_section == 0U ||
        target->has_operand == 0U || target->operand_index != operand_index) {
      continue;
    }
    *out_section_index = target->section_index;
    *out_offset = target->offset;
    return 1;
  }
  return 0;
}

static void data_pointer_state_mark_address_reg_dynamic(M68kRenderDataPointerState *state, uint8_t reg_index,
    const M68kDecodeCandidate *candidate) {
  size_t table_section_index = 0U;
  uint32_t table_offset = 0U;
  if (state == NULL || reg_index >= 8U || !state->addr_regs[reg_index].known) return;
  state->addr_regs[reg_index].exact = 0U;
  if (candidate_data_target_for_operand(candidate, 0U, &table_section_index, &table_offset)) {
    state->addr_regs[reg_index].dynamic_offset_known = 1U;
    state->addr_regs[reg_index].dynamic_offset_section_index = table_section_index;
    state->addr_regs[reg_index].dynamic_offset_offset = table_offset;
  }
}

static const M68kRenderDataPointerValue *data_pointer_state_value_for_operand(
    const M68kRenderDataPointerState *state, const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg)) return state->data_regs[reg].known ? &state->data_regs[reg] : NULL;
  if (operand_address_register_index_local(operand, &reg)) return state->addr_regs[reg].known ? &state->addr_regs[reg] : NULL;
  return NULL;
}

static int candidate_loads_data_target_to_address_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  uint8_t dest_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_section_index == NULL || out_offset == NULL ||
      out_reg == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  if (candidate_data_target_for_operand(candidate, 0U, out_section_index, out_offset)) {
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int candidate_loads_relocated_data_target_to_address_reg(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  uint8_t dest_reg = 0U;
  uint32_t relocation_offset;
  uint32_t relocation_end;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (lookup == NULL || section == NULL || candidate == NULL || instruction == NULL ||
      out_section_index == NULL || out_offset == NULL || out_reg == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg) ||
      candidate->byte_count > section->size || candidate->offset > section->size - candidate->byte_count) {
    return 0;
  }
  relocation_end = candidate->offset + candidate->byte_count;
  for (relocation_offset = candidate->offset + 2U; relocation_offset < relocation_end; ++relocation_offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, relocation_offset);
    if (relocation == NULL || relocation->size != 4U ||
        relocation->target_section_index >= lookup->section_count) {
      continue;
    }
    *out_section_index = relocation->target_section_index;
    *out_offset = relocation->target_offset;
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int candidate_loads_runtime_address_ref_target_to_address_reg(const M68kRenderLookup *lookup,
    size_t section_index, const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  size_t runtime_ref_index;
  uint8_t dest_reg = 0U;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (lookup == NULL || candidate == NULL || instruction == NULL ||
      out_section_index == NULL || out_offset == NULL || out_reg == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  for (runtime_ref_index = lookup->runtime_address_ref_count; runtime_ref_index > 0U; --runtime_ref_index) {
    const M68kFact *fact = lookup->runtime_address_refs[runtime_ref_index - 1U].fact;
    if (fact == NULL || fact->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
        fact->section_index != section_index || fact->offset != candidate->offset ||
        fact->reason != 0U || !fact->has_runtime_address ||
        fact->target_section_index >= lookup->section_count) {
      continue;
    }
    *out_section_index = fact->target_section_index;
    *out_offset = fact->target_offset;
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static void data_pointer_state_update_after_instruction_ex(M68kRenderDataPointerState *state,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction, uint8_t prefer_local_absolute) {
  const M68kRenderDataPointerValue *source_value = NULL;
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U, absolute_offset = 0U;
  uint8_t dest_reg = 0U, source_reg = 0U;
  int16_t displacement = 0;
  size_t operand_index;
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_BSR) {
    data_pointer_state_clear_all(state);
    return;
  }
  if (candidate_loads_data_target_to_address_reg(candidate, instruction, &target_section_index, &target_offset,
      &dest_reg)) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, target_section_index, target_offset);
    return;
  }
  if (prefer_local_absolute && section != NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest_reg) &&
      operand_absolute_offset_local(&instruction->operands[0], &absolute_offset) &&
      absolute_offset < section->size) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, section->section_index,
      absolute_offset);
    return;
  }
  if (candidate_loads_runtime_address_ref_target_to_address_reg(lookup, section != NULL ? section->section_index : 0U,
      candidate, instruction, &target_section_index, &target_offset, &dest_reg) ||
      candidate_loads_relocated_data_target_to_address_reg(lookup, section, candidate, instruction,
        &target_section_index, &target_offset, &dest_reg)) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, target_section_index, target_offset);
    return;
  }
  if (!prefer_local_absolute && section != NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest_reg) &&
      operand_absolute_offset_local(&instruction->operands[0], &absolute_offset) &&
      absolute_offset < section->size) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, section->section_index,
      absolute_offset);
    return;
  }
  if (section != NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest_reg) &&
      operand_is_address_displacement_local(&instruction->operands[0], &source_reg, &displacement) &&
      source_reg < 8U && state->addr_regs[source_reg].known &&
      state->addr_regs[source_reg].section_index == section->section_index) {
    int64_t adjusted_offset = (int64_t)state->addr_regs[source_reg].offset + (int64_t)displacement;
    if (adjusted_offset >= 0 && (uint64_t)adjusted_offset < (uint64_t)section->size) {
      M68kRenderDataPointerValue adjusted = state->addr_regs[source_reg];
      adjusted.offset = (uint32_t)adjusted_offset;
      data_pointer_state_copy_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, &adjusted);
      return;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDA && instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    data_pointer_state_mark_address_reg_dynamic(state, dest_reg, candidate);
    return;
  }
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->operand_count == 2U) {
    source_value = data_pointer_state_value_for_operand(state, &instruction->operands[0]);
    if (operand_is_data_register_local(&instruction->operands[1], &dest_reg)) {
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg);
      if (source_value != NULL)
        data_pointer_state_copy_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg, source_value);
      return;
    }
    if (operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg);
      if (source_value != NULL)
        data_pointer_state_copy_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, source_value);
      return;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    uint8_t bit;
    for (bit = 0U; bit < 8U; ++bit) {
      if ((instruction->operands[1].value.value & (1UL << bit)) != 0U)
        data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, bit);
      if ((instruction->operands[1].value.value & (1UL << (8U + bit))) != 0U)
        data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, bit);
    }
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
    if (operand_is_data_register_local(operand, &dest_reg))
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg);
    else if (operand_address_register_index_local(operand, &dest_reg))
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg);
  }
}

static int render_find_c_string_span(const M68kDecodeSectionIR *section, uint32_t offset, uint32_t *out_size) {
  uint32_t cursor;
  uint32_t text_size = 0U;
  if (out_size != NULL) *out_size = 0U;
  if (section == NULL || section->data == NULL || offset >= section->size || out_size == NULL) return 0;
  cursor = offset;
  while (cursor < section->size && section->data[cursor] != 0U) {
    if (!byte_is_quoted_string_safe(section->data[cursor])) return 0;
    ++cursor;
    ++text_size;
  }
  if (cursor >= section->size || section->data[cursor] != 0U || text_size < 2U) return 0;
  *out_size = text_size + 1U;
  return 1;
}

static int render_lookup_add_string_spans_for_vector_inputs(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    const AmigaOsLibraryVectorInfo *vector, const M68kRenderDataPointerState *state) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t index;
  if (lookup == NULL || decode == NULL || vector == NULL || state == NULL) return 0;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL) return 0;
  for (index = 0U; index < input_count; ++index) {
    const AmigaOsCallInputInfo *input = &inputs[index];
    const M68kRenderDataPointerValue *value = NULL;
    const M68kDecodeSectionIR *section;
    uint32_t string_size = 0U;
    if (input->semantic_kind_id != AMIGA_OS_SEMANTIC_KIND_ID_STRING_PTR || input->reg_index >= 8U) continue;
    if (input->reg_kind == AMIGA_OS_REGISTER_DATA) value = state->data_regs[input->reg_index].known ?
      &state->data_regs[input->reg_index] : NULL;
    else if (input->reg_kind == AMIGA_OS_REGISTER_ADDRESS) value = state->addr_regs[input->reg_index].known ?
      &state->addr_regs[input->reg_index] : NULL;
    if (value == NULL || !value->exact || value->section_index >= decode->section_count) continue;
    section = &decode->sections[value->section_index];
    if (!render_find_c_string_span(section, value->offset, &string_size)) continue;
    if (render_lookup_add_string_span(lookup, value->section_index, value->offset, string_size) != 0) return -1;
  }
  return 0;
}

static int append_render_lookup_recovered_local_call_summaries_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->recovered_local_call_summary_count; ++index) {
    const M68kRenderRecoveredLocalCallSummary *summary = &lookup->recovered_local_call_summaries[index];
    const AmigaOsCallOutputInfo *output;
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (summary->section_index != section_analysis->section_index || summary->vector == NULL) continue;
    output = &summary->vector->output;
    if (output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) continue;
    symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
    type_name = amiga_output_type_or_struct_name(output);
    semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
    value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
    if ((symbol_name == NULL || symbol_name[0] == '\0') &&
        (type_name == NULL || type_name[0] == '\0') &&
        (semantic_kind == NULL || semantic_kind[0] == '\0') &&
        (value_domain_name == NULL || value_domain_name[0] == '\0')) {
      continue;
    }
    if (m68k_ir_section_analysis_append_recovered_local_call_summary(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, summary->target_offset, M68K_PLATFORM_EFFECT_SET_TYPED_REG,
        output->reg_kind, output->reg_index, 0U, 0U, 0U, 0, NULL, symbol_name, type_name, semantic_kind,
        value_domain_name, 0U, 0) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_render_lookup_recovered_function_args_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->recovered_function_arg_count; ++index) {
    const M68kRenderRecoveredFunctionArg *arg = &lookup->recovered_function_args[index];
    const AmigaOsCallInputInfo *input = arg->input;
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (arg->section_index != section_analysis->section_index || input == NULL) continue;
    symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id);
    type_name = amiga_input_type_or_struct_name(input);
    semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, input->semantic_kind_id);
    value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input->value_domain_id);
    if (m68k_ir_section_analysis_append_recovered_function_arg(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, arg->function_offset, arg->stack_offset, arg->reg_kind, arg->reg_index,
        NULL, symbol_name, type_name, semantic_kind, value_domain_name, 0U, 0) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_render_lookup_typed_accesses_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_access_count; ++index) {
    const M68kRenderTypedAccess *access = &lookup->typed_accesses[index];
    if (access->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_typed_access(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, access->offset, access->operand_index, access->base_reg,
        access->displacement, access->field_offset, access->root_struct_name, access->owner_struct_name,
        access->field_name, access->field_expr, access->inherited, access->nested, access->provenance.kind,
        access->provenance.section_index, access->provenance.offset) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_render_lookup_unresolved_typed_accesses_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->unresolved_typed_access_count; ++index) {
    const M68kRenderUnresolvedTypedAccess *access = &lookup->unresolved_typed_accesses[index];
    if (access->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_unresolved_typed_access(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, access->offset, access->operand_index, access->base_reg,
        access->displacement, access->struct_size, access->root_struct_name, access->classification,
        access->container_candidate_count, access->container_struct_name, access->container_field_expr,
        access->refinement_applied, access->refined_struct_name, access->provenance.kind,
        access->provenance.section_index, access->provenance.offset) != 0) {
      return -1;
    }
  }
  return 0;
}

static int global_base_observation_add(M68kRenderGlobalBaseObservation **observations, size_t *count,
    size_t *capacity, size_t section_index, uint32_t offset, int16_t lvo) {
  size_t index;
  if (observations == NULL || count == NULL || capacity == NULL) return -1;
  for (index = 0U; index < *count; ++index) {
    M68kRenderGlobalBaseObservation *observation = &(*observations)[index];
    size_t lvo_index;
    if (observation->section_index != section_index || observation->offset != offset) continue;
    for (lvo_index = 0U; lvo_index < observation->lvo_count; ++lvo_index)
      if (observation->lvos[lvo_index] == lvo) return 0;
    if (observation->lvo_count < sizeof(observation->lvos) / sizeof(observation->lvos[0]))
      observation->lvos[observation->lvo_count++] = lvo;
    return 0;
  }
  if (*count == *capacity) {
    size_t next_capacity = *capacity == 0U ? 16U : *capacity * 2U;
    M68kRenderGlobalBaseObservation *grown =
      (M68kRenderGlobalBaseObservation *)realloc(*observations, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    *observations = grown;
    *capacity = next_capacity;
  }
  memset(&(*observations)[*count], 0, sizeof((*observations)[*count]));
  (*observations)[*count].section_index = section_index;
  (*observations)[*count].offset = offset;
  (*observations)[*count].lvos[0] = lvo;
  (*observations)[*count].lvo_count = 1U;
  ++(*count);
  return 0;
}

static int library_has_all_observed_lvos(const char *base_name, const M68kRenderGlobalBaseObservation *observation) {
  size_t index;
  if (base_name == NULL || observation == NULL || observation->lvo_count == 0U) return 0;
  for (index = 0U; index < observation->lvo_count; ++index) {
    if (amiga_os_find_library_vector(base_name, observation->lvos[index]) == NULL) return 0;
  }
  return 1;
}

static int library_id_seen_local(const uint16_t *ids, size_t count, uint16_t id) {
  size_t index;
  for (index = 0U; index < count; ++index)
    if (ids[index] == id) return 1;
  return 0;
}

static const char *unique_library_for_observed_lvos(const M68kRenderGlobalBaseObservation *observation) {
  uint16_t seen_ids[AMIGA_OS_LIBRARY_VECTOR_COUNT];
  size_t seen_count = 0U;
  const char *matched_library = NULL;
  size_t index;
  if (observation == NULL || observation->lvo_count == 0U) return NULL;
  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {
    const AmigaOsLibraryVectorInfo *vector = amiga_os_library_vector_at(index);
    const char *library_name;
    const char *base_name;
    if (vector == NULL) continue;
    if (library_id_seen_local(seen_ids, seen_count, vector->library_id)) continue;
    if (seen_count < sizeof(seen_ids) / sizeof(seen_ids[0])) seen_ids[seen_count++] = vector->library_id;
    library_name = amiga_os_name(M68K_PLATFORM_NAME_LIBRARY, vector->library_id);
    base_name = amiga_os_find_library_base_name(library_name);
    if (library_name == NULL || base_name == NULL) continue;
    if (!library_has_all_observed_lvos(base_name, observation)) continue;
    if (matched_library != NULL && strcmp(matched_library, library_name) != 0) return NULL;
    matched_library = library_name;
  }
  return matched_library;
}

static int render_lookup_add_global_base_slot(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *library_name, size_t source_section_index, uint32_t source_offset) {
  size_t index;
  M68kRenderGlobalBaseSlot *grown;
  size_t next_capacity;
  uint8_t has_source = source_section_index != SIZE_MAX && source_offset != UINT32_MAX;
  if (lookup == NULL || library_name == NULL || library_name[0] == '\0') return 0;
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    M68kRenderGlobalBaseSlot *slot = &lookup->global_base_slots[index];
    if (slot->section_index == section_index && slot->offset == offset) {
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
      if (has_source && slot->has_source == 0U) {
        slot->source_section_index = source_section_index;
        slot->source_offset = source_offset;
        slot->has_source = 1U;
      }
      return 0;
    }
  }
  if (lookup->global_base_slot_count == lookup->global_base_slot_capacity) {
    next_capacity = lookup->global_base_slot_capacity == 0U ? 8U : lookup->global_base_slot_capacity * 2U;
    grown = (M68kRenderGlobalBaseSlot *)realloc(lookup->global_base_slots, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->global_base_slots = grown;
    lookup->global_base_slot_capacity = next_capacity;
  }
  memset(&lookup->global_base_slots[lookup->global_base_slot_count], 0,
    sizeof(lookup->global_base_slots[lookup->global_base_slot_count]));
  lookup->global_base_slots[lookup->global_base_slot_count].section_index = section_index;
  lookup->global_base_slots[lookup->global_base_slot_count].offset = offset;
  lookup->global_base_slots[lookup->global_base_slot_count].source_section_index = source_section_index;
  lookup->global_base_slots[lookup->global_base_slot_count].source_offset = source_offset;
  lookup->global_base_slots[lookup->global_base_slot_count].has_source = has_source;
  snprintf(lookup->global_base_slots[lookup->global_base_slot_count].library_name,
    sizeof(lookup->global_base_slots[lookup->global_base_slot_count].library_name), "%s", library_name);
  ++lookup->global_base_slot_count;
  return 0;
}

static int render_lookup_add_base_field_slot_with_symbol(M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, const char *library_name, const char *symbol_name, uint8_t value_kind,
    size_t source_section_index, uint32_t source_offset) {
  size_t index;
  M68kRenderBaseFieldSlot *grown;
  size_t next_capacity;
  uint8_t has_source = source_section_index != SIZE_MAX && source_offset != UINT32_MAX;
  const char *slot_library_name = library_name != NULL ? library_name : "";
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0') return 0;
  if (value_kind == M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE ||
      value_kind == M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE) {
    if (slot_library_name[0] == '\0' || amiga_os_find_library_base_name(slot_library_name) == NULL) return 0;
  } else if (value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
    if (strcmp(owner_name, "__amiga_app_base__") != 0) return 0;
  } else if (symbol_name == NULL || symbol_name[0] == '\0') {
    return 0;
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    if (strcmp(slot->owner_name, owner_name) != 0 || slot->displacement != displacement) continue;
    if (slot->conflicted) return 0;
    if (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS && value_kind != M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
      slot->value_kind = value_kind;
      if (slot_library_name[0] != '\0') {
        snprintf(slot->library_name, sizeof(slot->library_name), "%s", slot_library_name);
      }
      if (symbol_name != NULL && symbol_name[0] != '\0') {
        snprintf(slot->symbol_name, sizeof(slot->symbol_name), "%s", symbol_name);
      }
    } else if (value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
      /* The generic app-state access confirms the slot exists but must not erase a better name. */
    } else if (slot->value_kind != value_kind ||
        (slot->library_name[0] != '\0' && strcmp(slot->library_name, slot_library_name) != 0) ||
        (slot->symbol_name[0] != '\0' && (symbol_name == NULL || strcmp(slot->symbol_name, symbol_name) != 0)) ||
        (slot->symbol_name[0] == '\0' && symbol_name != NULL && symbol_name[0] != '\0')) {
      slot->library_name[0] = '\0';
      slot->symbol_name[0] = '\0';
      slot->conflicted = 1U;
    } else if (slot->library_name[0] == '\0' && slot_library_name[0] != '\0') {
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", slot_library_name);
    }
    if (has_source && slot->has_source == 0U) {
      slot->source_section_index = source_section_index;
      slot->source_offset = source_offset;
      slot->has_source = 1U;
    }
    return 0;
  }
  if (lookup->base_field_slot_count == lookup->base_field_slot_capacity) {
    next_capacity = lookup->base_field_slot_capacity == 0U ? 8U : lookup->base_field_slot_capacity * 2U;
    grown = (M68kRenderBaseFieldSlot *)realloc(lookup->base_field_slots, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->base_field_slots = grown;
    lookup->base_field_slot_capacity = next_capacity;
  }
  memset(&lookup->base_field_slots[lookup->base_field_slot_count], 0,
    sizeof(lookup->base_field_slots[lookup->base_field_slot_count]));
  snprintf(lookup->base_field_slots[lookup->base_field_slot_count].owner_name,
    sizeof(lookup->base_field_slots[lookup->base_field_slot_count].owner_name), "%s", owner_name);
  lookup->base_field_slots[lookup->base_field_slot_count].displacement = displacement;
  lookup->base_field_slots[lookup->base_field_slot_count].source_section_index = source_section_index;
  lookup->base_field_slots[lookup->base_field_slot_count].source_offset = source_offset;
  lookup->base_field_slots[lookup->base_field_slot_count].has_source = has_source;
  if (slot_library_name[0] != '\0') {
    snprintf(lookup->base_field_slots[lookup->base_field_slot_count].library_name,
      sizeof(lookup->base_field_slots[lookup->base_field_slot_count].library_name), "%s", slot_library_name);
  }
  if (symbol_name != NULL && symbol_name[0] != '\0') {
    snprintf(lookup->base_field_slots[lookup->base_field_slot_count].symbol_name,
      sizeof(lookup->base_field_slots[lookup->base_field_slot_count].symbol_name), "%s", symbol_name);
  }
  lookup->base_field_slots[lookup->base_field_slot_count].value_kind = value_kind;
  ++lookup->base_field_slot_count;
  return 0;
}

static int render_lookup_add_base_field_slot(M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, const char *library_name, size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, owner_name, displacement, library_name, NULL,
    M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE, source_section_index, source_offset);
}

static int render_lookup_add_device_base_field_slot(M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, const char *library_name, size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, owner_name, displacement, library_name, NULL,
    M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE, source_section_index, source_offset);
}

static int render_lookup_add_named_app_field_slot(M68kRenderLookup *lookup, int16_t displacement,
    const char *symbol_name, size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, "__amiga_app_base__", displacement, "", symbol_name,
    M68K_RENDER_BASE_FIELD_SLOT_NAMED_VALUE, source_section_index, source_offset);
}

static int render_lookup_add_app_access_slot(M68kRenderLookup *lookup, int16_t displacement,
    size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, "__amiga_app_base__", displacement, "", NULL,
    M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS, source_section_index, source_offset);
}

static int render_lookup_seed_policy_app_slot_regions(M68kRenderLookup *lookup) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (lookup == NULL || policy == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < policy->app_slot_region_count && index < M68K_ANALYSIS_APP_SLOT_REGION_LIMIT; ++index) {
    const M68kAnalysisAppSlotRegion *slot = &policy->app_slot_regions[index];
    if (slot->symbol[0] == '\0' || slot->offset > 0x7FFFU) continue;
    if (render_lookup_add_named_app_field_slot(lookup, (int16_t)slot->offset, slot->symbol, SIZE_MAX,
        UINT32_MAX) != 0) {
      return -1;
    }
  }
  return 0;
}

static int render_lookup_add_device_instance(M68kRenderLookup *lookup, int16_t iorequest_displacement,
    const char *device_name) {
  size_t index;
  M68kRenderDeviceInstance *grown;
  size_t next_capacity;
  if (lookup == NULL || device_name == NULL || device_name[0] == '\0') return 0;
  for (index = 0U; index < lookup->device_instance_count; ++index) {
    M68kRenderDeviceInstance *instance = &lookup->device_instances[index];
    if (instance->iorequest_displacement != iorequest_displacement) continue;
    if (strcmp(instance->device_name, device_name) != 0) {
      instance->device_name[0] = '\0';
      instance->conflicted = 1U;
    }
    return 0;
  }
  if (lookup->device_instance_count == lookup->device_instance_capacity) {
    next_capacity = lookup->device_instance_capacity == 0U ? 8U : lookup->device_instance_capacity * 2U;
    grown = (M68kRenderDeviceInstance *)realloc(lookup->device_instances, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->device_instances = grown;
    lookup->device_instance_capacity = next_capacity;
  }
  memset(&lookup->device_instances[lookup->device_instance_count], 0,
    sizeof(lookup->device_instances[lookup->device_instance_count]));
  lookup->device_instances[lookup->device_instance_count].iorequest_displacement = iorequest_displacement;
  snprintf(lookup->device_instances[lookup->device_instance_count].device_name,
    sizeof(lookup->device_instances[lookup->device_instance_count].device_name), "%s", device_name);
  ++lookup->device_instance_count;
  return 0;
}

static const char *render_lookup_device_name_for_iorequest(const M68kRenderLookup *lookup,
    int16_t iorequest_displacement) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->device_instance_count; ++index) {
    const M68kRenderDeviceInstance *instance = &lookup->device_instances[index];
    if (instance->iorequest_displacement == iorequest_displacement && instance->conflicted == 0U &&
        instance->device_name[0] != '\0') {
      return instance->device_name;
    }
  }
  return NULL;
}

static int render_lookup_add_device_call(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *device_name) {
  size_t index;
  M68kRenderDeviceCall *grown;
  size_t next_capacity;
  if (lookup == NULL || device_name == NULL || device_name[0] == '\0') return 0;
  for (index = 0U; index < lookup->device_call_count; ++index) {
    M68kRenderDeviceCall *call = &lookup->device_calls[index];
    if (call->section_index != section_index || call->offset != offset) continue;
    return strcmp(call->device_name, device_name) == 0 ? 0 : -1;
  }
  if (lookup->device_call_count == lookup->device_call_capacity) {
    next_capacity = lookup->device_call_capacity == 0U ? 8U : lookup->device_call_capacity * 2U;
    grown = (M68kRenderDeviceCall *)realloc(lookup->device_calls, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->device_calls = grown;
    lookup->device_call_capacity = next_capacity;
  }
  memset(&lookup->device_calls[lookup->device_call_count], 0, sizeof(lookup->device_calls[lookup->device_call_count]));
  lookup->device_calls[lookup->device_call_count].section_index = section_index;
  lookup->device_calls[lookup->device_call_count].offset = offset;
  snprintf(lookup->device_calls[lookup->device_call_count].device_name,
    sizeof(lookup->device_calls[lookup->device_call_count].device_name), "%s", device_name);
  ++lookup->device_call_count;
  return 0;
}

const char *render_lookup_device_name_for_call(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->device_call_count; ++index) {
    const M68kRenderDeviceCall *call = &lookup->device_calls[index];
    if (call->section_index == section_index && call->offset == offset && call->device_name[0] != '\0')
      return call->device_name;
  }
  return NULL;
}

static int render_lookup_add_app_access_ref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t base_reg, int16_t displacement, uint8_t operand_index, uint8_t access_kind) {
  size_t index;
  M68kRenderAppSlotRef *grown;
  size_t next_capacity;
  if (lookup == NULL || base_reg >= 8U || operand_index >= 4U ||
      access_kind == M68K_APP_SLOT_ACCESS_NONE) {
    return 0;
  }
  if (render_lookup_add_app_access_slot(lookup, displacement, section_index, offset) != 0) return -1;
  for (index = 0U; index < lookup->app_slot_ref_count; ++index) {
    const M68kRenderAppSlotRef *existing = &lookup->app_slot_refs[index];
    if (existing->section_index == section_index && existing->ref.offset == offset &&
        existing->ref.displacement == displacement && existing->ref.base_reg == base_reg &&
        existing->ref.operand_index == operand_index && existing->ref.access_kind == access_kind) {
      return 0;
    }
  }
  if (lookup->app_slot_ref_count == lookup->app_slot_ref_capacity) {
    next_capacity = lookup->app_slot_ref_capacity == 0U ? 32U : lookup->app_slot_ref_capacity * 2U;
    grown = (M68kRenderAppSlotRef *)realloc(lookup->app_slot_refs, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->app_slot_refs = grown;
    lookup->app_slot_ref_capacity = next_capacity;
  }
  memset(&lookup->app_slot_refs[lookup->app_slot_ref_count], 0,
    sizeof(lookup->app_slot_refs[lookup->app_slot_ref_count]));
  lookup->app_slot_refs[lookup->app_slot_ref_count].section_index = section_index;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.offset = offset;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.displacement = displacement;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.base_reg = base_reg;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.operand_index = operand_index;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.access_kind = access_kind;
  ++lookup->app_slot_ref_count;
  return 0;
}

int render_lookup_add_runtime_address_ref(M68kRenderLookup *lookup, const M68kFact *fact) {
  M68kRenderRuntimeAddressRef *grown;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || fact == NULL || fact->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
      !fact->has_runtime_address) {
    return 0;
  }
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    const M68kFact *existing = lookup->runtime_address_refs[index].fact;
    if (existing == NULL) continue;
    if (existing->section_index == fact->section_index && existing->offset == fact->offset &&
        existing->reason == fact->reason && existing->target_section_index == fact->target_section_index &&
        existing->target_offset == fact->target_offset && existing->has_runtime_address &&
        existing->runtime_address == fact->runtime_address) {
      return 0;
    }
  }
  if (lookup->runtime_address_ref_count == lookup->runtime_address_ref_capacity) {
    next_capacity = lookup->runtime_address_ref_capacity == 0U ? 32U :
      lookup->runtime_address_ref_capacity * 2U;
    grown = (M68kRenderRuntimeAddressRef *)realloc(lookup->runtime_address_refs,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->runtime_address_refs = grown;
    lookup->runtime_address_ref_capacity = next_capacity;
  }
  lookup->runtime_address_refs[lookup->runtime_address_ref_count].fact = fact;
  ++lookup->runtime_address_ref_count;
  return 0;
}

static int render_lookup_add_inferred_runtime_address_ref(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint32_t runtime_address, uint32_t size, const char *data_class) {
  M68kRenderInferredRuntimeAddressRef *grown;
  M68kRenderInferredRuntimeAddressRef *entry;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || data_class == NULL || data_class[0] == '\0') return 0;
  for (index = 0U; index < lookup->inferred_runtime_address_ref_count; ++index) {
    const M68kRenderInferredRuntimeAddressRef *existing = &lookup->inferred_runtime_address_refs[index];
    if (existing->section_index == section_index && existing->ref.offset == offset &&
        existing->ref.has_runtime_address && existing->ref.runtime_address == runtime_address &&
        existing->ref.size == size && strcmp(existing->data_class, data_class) == 0) {
      return 0;
    }
  }
  if (lookup->inferred_runtime_address_ref_count == lookup->inferred_runtime_address_ref_capacity) {
    next_capacity = lookup->inferred_runtime_address_ref_capacity == 0U ? 16U :
      lookup->inferred_runtime_address_ref_capacity * 2U;
    grown = (M68kRenderInferredRuntimeAddressRef *)realloc(lookup->inferred_runtime_address_refs,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->inferred_runtime_address_refs = grown;
    lookup->inferred_runtime_address_ref_capacity = next_capacity;
  }
  entry = &lookup->inferred_runtime_address_refs[lookup->inferred_runtime_address_ref_count];
  memset(entry, 0, sizeof(*entry));
  entry->section_index = section_index;
  entry->ref.offset = offset;
  entry->ref.operand_index = UINT32_MAX;
  entry->ref.size = size;
  entry->ref.has_target = 0U;
  entry->ref.has_runtime_address = 1U;
  entry->ref.runtime_address = runtime_address;
  entry->ref.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  snprintf(entry->data_class, sizeof(entry->data_class), "%s", data_class);
  entry->ref.data_class = entry->data_class;
  ++lookup->inferred_runtime_address_ref_count;
  return 0;
}

int render_lookup_add_runtime_address_range(M68kRenderLookup *lookup, const M68kFact *fact) {
  M68kRenderRuntimeAddressRange *grown;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || fact == NULL || fact->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      !fact->has_runtime_address || fact->size == 0U) {
    return 0;
  }
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *existing = lookup->runtime_address_ranges[index].fact;
    if (existing == NULL) continue;
    if (existing->section_index == fact->section_index && existing->offset == fact->offset &&
        existing->runtime_address == fact->runtime_address && existing->size == fact->size) {
      return 0;
    }
  }
  if (lookup->runtime_address_range_count == lookup->runtime_address_range_capacity) {
    next_capacity = lookup->runtime_address_range_capacity == 0U ? 16U :
      lookup->runtime_address_range_capacity * 2U;
    grown = (M68kRenderRuntimeAddressRange *)realloc(lookup->runtime_address_ranges,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->runtime_address_ranges = grown;
    lookup->runtime_address_range_capacity = next_capacity;
  }
  lookup->runtime_address_ranges[lookup->runtime_address_range_count].fact = fact;
  ++lookup->runtime_address_range_count;
  return 0;
}

int render_lookup_add_code_start_ref(M68kRenderLookup *lookup, const M68kFact *fact) {
  M68kRenderCodeStartRef *grown;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || fact == NULL || fact->kind != M68K_FACT_CODE_ACCEPTED ||
      fact->reason == M68K_FACT_CODE_START_REASON_FALLTHROUGH) {
    return 0;
  }
  for (index = 0U; index < lookup->code_start_ref_count; ++index) {
    const M68kFact *existing = lookup->code_start_refs[index].fact;
    if (existing == NULL) continue;
    if (existing->section_index == fact->section_index && existing->offset == fact->offset &&
        existing->reason == fact->reason && existing->source_section_index == fact->source_section_index &&
        existing->source_offset == fact->source_offset && existing->has_runtime_address == fact->has_runtime_address &&
        existing->runtime_address == fact->runtime_address) {
      return 0;
    }
  }
  if (lookup->code_start_ref_count == lookup->code_start_ref_capacity) {
    next_capacity = lookup->code_start_ref_capacity == 0U ? 32U : lookup->code_start_ref_capacity * 2U;
    grown = (M68kRenderCodeStartRef *)realloc(lookup->code_start_refs, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->code_start_refs = grown;
    lookup->code_start_ref_capacity = next_capacity;
  }
  lookup->code_start_refs[lookup->code_start_ref_count].fact = fact;
  ++lookup->code_start_ref_count;
  return 0;
}

int render_lookup_add_violation_ref(M68kRenderLookup *lookup, const M68kFact *fact) {
  M68kRenderViolationRef *grown;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || fact == NULL || fact->kind != M68K_FACT_VIOLATION) return 0;
  for (index = 0U; index < lookup->violation_ref_count; ++index) {
    const M68kFact *existing = lookup->violation_refs[index].fact;
    if (existing == NULL) continue;
    if (existing->section_index == fact->section_index && existing->offset == fact->offset &&
        existing->target_section_index == fact->target_section_index &&
        existing->target_offset == fact->target_offset && existing->reason == fact->reason) {
      return 0;
    }
  }
  if (lookup->violation_ref_count == lookup->violation_ref_capacity) {
    next_capacity = lookup->violation_ref_capacity == 0U ? 16U : lookup->violation_ref_capacity * 2U;
    grown = (M68kRenderViolationRef *)realloc(lookup->violation_refs, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->violation_refs = grown;
    lookup->violation_ref_capacity = next_capacity;
  }
  lookup->violation_refs[lookup->violation_ref_count].fact = fact;
  ++lookup->violation_ref_count;
  return 0;
}

static int render_lookup_add_auto_structured_data_item(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint32_t size, const char *semantic_role, uint8_t kind) {
  M68kAnalysisStructuredDataItem *grown;
  M68kAnalysisStructuredDataItem *item;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || semantic_role == NULL || semantic_role[0] == '\0' || size == 0U) return 0;
  if (lookup_structured_data_item_at_offset(lookup, section_index, offset) != NULL) return 0;
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *existing = &lookup->auto_structured_data_items[index];
    if (existing->section_index == (uint32_t)section_index && existing->offset == offset &&
        existing->size == size && strcmp(existing->semantic_role, semantic_role) == 0) {
      return 0;
    }
  }
  if (lookup->auto_structured_data_item_count == lookup->auto_structured_data_item_capacity) {
    next_capacity = lookup->auto_structured_data_item_capacity == 0U ? 16U :
      lookup->auto_structured_data_item_capacity * 2U;
    grown = (M68kAnalysisStructuredDataItem *)realloc(lookup->auto_structured_data_items,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->auto_structured_data_items = grown;
    lookup->auto_structured_data_item_capacity = next_capacity;
  }
  item = &lookup->auto_structured_data_items[lookup->auto_structured_data_item_count];
  memset(item, 0, sizeof(*item));
  item->has_section_index = 1U;
  item->section_index = (uint32_t)section_index;
  item->offset = offset;
  item->size = size;
  item->kind = kind;
  snprintf(item->semantic_role, sizeof(item->semantic_role), "%s", semantic_role);
  ++lookup->auto_structured_data_item_count;
  return 0;
}

int render_lookup_add_storage_xref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    size_t target_section_index, uint32_t target_offset) {
  M68kRenderXref *grown;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL) return 0;
  for (index = 0U; index < lookup->xref_count; ++index) {
    const M68kRenderXref *xref = &lookup->xrefs[index];
    if (xref->section_index == section_index && xref->offset == offset &&
        xref->target_section_index == target_section_index && xref->target_offset == target_offset) {
      return 0;
    }
  }
  if (lookup->xref_count == lookup->xref_capacity) {
    next_capacity = lookup->xref_capacity == 0U ? 64U : lookup->xref_capacity * 2U;
    grown = (M68kRenderXref *)realloc(lookup->xrefs, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->xrefs = grown;
    lookup->xref_capacity = next_capacity;
  }
  lookup->xrefs[lookup->xref_count].section_index = section_index;
  lookup->xrefs[lookup->xref_count].offset = offset;
  lookup->xrefs[lookup->xref_count].target_section_index = target_section_index;
  lookup->xrefs[lookup->xref_count].target_offset = target_offset;
  ++lookup->xref_count;
  return 0;
}

int render_lookup_add_pc_relative_xrefs(M68kRenderLookup *lookup, const M68kDecodeIR *decode) {
  size_t section_index;
  if (lookup == NULL || decode == NULL) return 0;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      size_t target_index;
      int decoded = 0;
      memset(&instruction, 0, sizeof(instruction));
      for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
        const M68kDecodeTarget *target = &candidate->targets[target_index];
        if (!target->has_section || !target->has_operand || target->section_index >= decode->section_count)
          continue;
        if (!decoded) {
          if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
          decoded = 1;
        }
        if (target->operand_index >= instruction.operand_count) continue;
        if (symbol_ref_kind_for_operand(&instruction.operands[target->operand_index]) != M68K_IR_SYMBOL_REF_PC_REL)
          continue;
        if (render_lookup_add_storage_xref(lookup, section->section_index, candidate->offset,
            target->section_index, target->offset) != 0)
          return -1;
      }
    }
  }
  return 0;
}

int render_lookup_add_indexed_vector_wrapper(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *library_name) {
  size_t index;
  M68kRenderIndexedVectorWrapper *grown;
  size_t next_capacity;
  if (lookup == NULL || library_name == NULL || library_name[0] == '\0') return 0;
  if (amiga_os_find_library_base_name(library_name) == NULL) return 0;
  for (index = 0U; index < lookup->indexed_vector_wrapper_count; ++index) {
    M68kRenderIndexedVectorWrapper *wrapper = &lookup->indexed_vector_wrappers[index];
    if (wrapper->section_index != section_index || wrapper->offset != offset) continue;
    if (strcmp(wrapper->library_name, library_name) != 0) wrapper->library_name[0] = '\0';
    return 0;
  }
  if (lookup->indexed_vector_wrapper_count == lookup->indexed_vector_wrapper_capacity) {
    next_capacity = lookup->indexed_vector_wrapper_capacity == 0U ? 8U :
      lookup->indexed_vector_wrapper_capacity * 2U;
    grown = (M68kRenderIndexedVectorWrapper *)realloc(lookup->indexed_vector_wrappers,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->indexed_vector_wrappers = grown;
    lookup->indexed_vector_wrapper_capacity = next_capacity;
  }
  memset(&lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count], 0,
    sizeof(lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count]));
  lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].section_index = section_index;
  lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].offset = offset;
  snprintf(lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].library_name,
    sizeof(lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].library_name), "%s", library_name);
  ++lookup->indexed_vector_wrapper_count;
  return 0;
}

static int comment_contains_part(const char *comment, const char *part) {
  if (comment == NULL || part == NULL || part[0] == '\0') return 1;
  return strstr(comment, part) != NULL;
}

int append_comment_part_local(char *comment, size_t comment_size, const char *part) {
  size_t used;
  size_t needed;
  if (comment == NULL || comment_size == 0U || part == NULL || part[0] == '\0') return 1;
  if (comment_contains_part(comment, part)) return 1;
  used = strlen(comment);
  needed = strlen(part) + (used != 0U ? 3U : 0U) + 1U;
  if (needed > comment_size - used) return 0;
  if (used != 0U) strcat(comment, " | ");
  strcat(comment, part);
  return 1;
}

static size_t *lookup_instruction_comment_index_slot(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->instruction_comment_indices == NULL ||
      lookup->instruction_comment_extents == NULL || offset >= lookup->instruction_comment_extents[section_index] ||
      lookup->instruction_comment_indices[section_index] == NULL) {
    return NULL;
  }
  return &lookup->instruction_comment_indices[section_index][offset];
}

static const size_t *lookup_instruction_comment_index_slot_const(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->instruction_comment_indices == NULL ||
      lookup->instruction_comment_extents == NULL || offset >= lookup->instruction_comment_extents[section_index] ||
      lookup->instruction_comment_indices[section_index] == NULL) {
    return NULL;
  }
  return &lookup->instruction_comment_indices[section_index][offset];
}

int render_lookup_add_instruction_comment(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *comment) {
  size_t index;
  size_t *index_slot;
  M68kRenderInstructionComment *grown;
  size_t next_capacity;
  if (lookup == NULL || comment == NULL || comment[0] == '\0') return 0;
  index_slot = lookup_instruction_comment_index_slot(lookup, section_index, offset);
  if (index_slot != NULL && *index_slot != 0U && *index_slot <= lookup->instruction_comment_count) {
    M68kRenderInstructionComment *entry = &lookup->instruction_comments[*index_slot - 1U];
    if (entry->section_index == section_index && entry->offset == offset) {
      (void)append_comment_part_local(entry->comment, sizeof(entry->comment), comment);
      return 0;
    }
    *index_slot = 0U;
  }
  for (index = 0U; index < lookup->instruction_comment_count; ++index) {
    M68kRenderInstructionComment *entry = &lookup->instruction_comments[index];
    if (entry->section_index != section_index || entry->offset != offset) continue;
    if (index_slot != NULL) *index_slot = index + 1U;
    (void)append_comment_part_local(entry->comment, sizeof(entry->comment), comment);
    return 0;
  }
  if (lookup->instruction_comment_count == lookup->instruction_comment_capacity) {
    next_capacity = lookup->instruction_comment_capacity == 0U ? 32U : lookup->instruction_comment_capacity * 2U;
    grown = (M68kRenderInstructionComment *)realloc(lookup->instruction_comments, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->instruction_comments = grown;
    lookup->instruction_comment_capacity = next_capacity;
  }
  memset(&lookup->instruction_comments[lookup->instruction_comment_count], 0,
    sizeof(lookup->instruction_comments[lookup->instruction_comment_count]));
  lookup->instruction_comments[lookup->instruction_comment_count].section_index = section_index;
  lookup->instruction_comments[lookup->instruction_comment_count].offset = offset;
  snprintf(lookup->instruction_comments[lookup->instruction_comment_count].comment,
    sizeof(lookup->instruction_comments[lookup->instruction_comment_count].comment), "%s", comment);
  if (index_slot != NULL) *index_slot = lookup->instruction_comment_count + 1U;
  ++lookup->instruction_comment_count;
  return 0;
}

int render_lookup_add_recovered_function_arg(M68kRenderLookup *lookup, size_t section_index,
    uint32_t function_offset, uint16_t stack_offset, uint8_t reg_kind, uint8_t reg_index,
    const AmigaOsCallInputInfo *input) {
  size_t index;
  M68kRenderRecoveredFunctionArg *grown;
  size_t next_capacity;
  if (lookup == NULL || input == NULL || stack_offset == 0U || reg_kind == 0U || reg_index >= 8U) return 0;
  for (index = 0U; index < lookup->recovered_function_arg_count; ++index) {
    M68kRenderRecoveredFunctionArg *entry = &lookup->recovered_function_args[index];
    if (entry->section_index == section_index && entry->function_offset == function_offset &&
        entry->stack_offset == stack_offset && entry->reg_kind == reg_kind && entry->reg_index == reg_index) {
      if (entry->input != input) entry->input = NULL;
      return 0;
    }
  }
  if (lookup->recovered_function_arg_count == lookup->recovered_function_arg_capacity) {
    next_capacity = lookup->recovered_function_arg_capacity == 0U ? 16U :
      lookup->recovered_function_arg_capacity * 2U;
    grown = (M68kRenderRecoveredFunctionArg *)realloc(lookup->recovered_function_args,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->recovered_function_args = grown;
    lookup->recovered_function_arg_capacity = next_capacity;
  }
  memset(&lookup->recovered_function_args[lookup->recovered_function_arg_count], 0,
    sizeof(lookup->recovered_function_args[lookup->recovered_function_arg_count]));
  lookup->recovered_function_args[lookup->recovered_function_arg_count].section_index = section_index;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].function_offset = function_offset;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].stack_offset = stack_offset;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].reg_kind = reg_kind;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].reg_index = reg_index;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].input = input;
  ++lookup->recovered_function_arg_count;
  return 0;
}

int render_lookup_add_recovered_local_call_summary(M68kRenderLookup *lookup, size_t section_index,
    uint32_t target_offset, const AmigaOsLibraryVectorInfo *vector) {
  size_t index;
  M68kRenderRecoveredLocalCallSummary *grown;
  size_t next_capacity;
  if (lookup == NULL || vector == NULL) return 0;
  for (index = 0U; index < lookup->recovered_local_call_summary_count; ++index) {
    M68kRenderRecoveredLocalCallSummary *entry = &lookup->recovered_local_call_summaries[index];
    if (entry->section_index == section_index && entry->target_offset == target_offset) {
      if (entry->vector != vector) entry->vector = NULL;
      return 0;
    }
  }
  if (lookup->recovered_local_call_summary_count == lookup->recovered_local_call_summary_capacity) {
    next_capacity = lookup->recovered_local_call_summary_capacity == 0U ? 16U :
      lookup->recovered_local_call_summary_capacity * 2U;
    grown = (M68kRenderRecoveredLocalCallSummary *)realloc(lookup->recovered_local_call_summaries,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->recovered_local_call_summaries = grown;
    lookup->recovered_local_call_summary_capacity = next_capacity;
  }
  memset(&lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count], 0,
    sizeof(lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count]));
  lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count].section_index = section_index;
  lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count].target_offset = target_offset;
  lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count].vector = vector;
  ++lookup->recovered_local_call_summary_count;
  return 0;
}

int render_lookup_add_typed_slot_effect(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    int16_t displacement, const AmigaOsCallOutputInfo *output) {
  size_t index;
  M68kRenderTypedSlotEffect *grown;
  size_t next_capacity;
  if (lookup == NULL || output == NULL || output->reg_kind == AMIGA_OS_REGISTER_NONE ||
      output->reg_index >= 8U) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_slot_effect_count; ++index) {
    M68kRenderTypedSlotEffect *entry = &lookup->typed_slot_effects[index];
    if (entry->section_index == section_index && entry->offset == offset &&
        entry->displacement == displacement) {
      if (entry->output != output) entry->output = NULL;
      return 0;
    }
  }
  if (lookup->typed_slot_effect_count == lookup->typed_slot_effect_capacity) {
    next_capacity = lookup->typed_slot_effect_capacity == 0U ? 16U : lookup->typed_slot_effect_capacity * 2U;
    grown = (M68kRenderTypedSlotEffect *)realloc(lookup->typed_slot_effects, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->typed_slot_effects = grown;
    lookup->typed_slot_effect_capacity = next_capacity;
  }
  memset(&lookup->typed_slot_effects[lookup->typed_slot_effect_count], 0,
    sizeof(lookup->typed_slot_effects[lookup->typed_slot_effect_count]));
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].section_index = section_index;
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].offset = offset;
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].displacement = displacement;
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].output = output;
  ++lookup->typed_slot_effect_count;
  return 0;
}

static int typed_storage_keys_match(const M68kRenderTypedStorageSlot *slot, uint8_t kind, size_t section_index,
    int32_t displacement, uint32_t address) {
  if (slot == NULL || slot->kind != kind) return 0;
  if (kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) return slot->displacement == displacement;
  if (kind == M68K_RENDER_TYPED_STORAGE_ABSOLUTE)
    return slot->section_index == section_index && slot->address == address;
  if (kind == M68K_RENDER_TYPED_STORAGE_BASE_SLOT)
    return slot->section_index == section_index && slot->address == address && slot->displacement == displacement;
  return 0;
}

static int typed_storage_merge_value(M68kRenderTypedStorageSlot *slot,
    const M68kRenderTypedStoredValue *value) {
  int changed = 0;
  if (slot == NULL || value == NULL || slot->conflicted != 0U || !typed_stored_value_has_useful_info(value))
    return 0;
  {
    int conflict = 0;
    uint16_t merged_struct_id = typed_struct_id_refined_merge(slot->value.struct_id, value->struct_id, &conflict);
    if (conflict) {
      slot->conflicted = 1U;
      slot->value.known = 0U;
      slot->value.output = NULL;
      changed = 1;
    } else if (slot->value.struct_id != merged_struct_id) {
      slot->value.struct_id = merged_struct_id;
      slot->value.output = NULL;
      changed = 1;
    }
  }
  if (slot->conflicted != 0U) {
    slot->conflicted = 1U;
    slot->value.known = 0U;
    slot->value.output = NULL;
    changed = 1;
  } else {
    if (slot->value.output == NULL && value->output != NULL &&
        (slot->value.struct_id == AMIGA_OS_STRUCT_ID_NONE ||
          value->output->struct_id == AMIGA_OS_STRUCT_ID_NONE ||
          value->output->struct_id == slot->value.struct_id)) {
      slot->value.output = value->output;
      changed = 1;
    } else if (slot->value.output != NULL && value->output != NULL && slot->value.output != value->output) {
      slot->value.output = NULL;
      changed = 1;
    }
    if (value->app_address_known) {
      if (!slot->value.app_address_known) {
        slot->value.app_address_known = 1U;
        slot->value.app_displacement = value->app_displacement;
        changed = 1;
      } else if (slot->value.app_displacement != value->app_displacement) {
        slot->conflicted = 1U;
        slot->value.known = 0U;
        slot->value.output = NULL;
        changed = 1;
      }
    }
    if (slot->value.output != NULL && slot->value.struct_id != AMIGA_OS_STRUCT_ID_NONE &&
        slot->value.output->struct_id != AMIGA_OS_STRUCT_ID_NONE &&
        slot->value.output->struct_id != slot->value.struct_id) {
      slot->value.output = NULL;
      changed = 1;
    }
    {
      M68kRenderTypedProvenance old_provenance = slot->value.provenance;
      typed_provenance_merge(&slot->value.provenance, &value->provenance);
      if (!typed_provenances_equal(&slot->value.provenance, &old_provenance)) changed = 1;
    }
    if (slot->conflicted == 0U && typed_stored_value_has_payload(&slot->value)) slot->value.known = 1U;
  }
  return changed;
}

int render_lookup_add_typed_storage_slot(M68kRenderLookup *lookup, uint8_t kind, size_t section_index,
    int32_t displacement, uint32_t address, const M68kRenderTypedStoredValue *value,
    size_t source_section_index, uint32_t source_offset, int *out_added) {
  size_t index;
  M68kRenderTypedStorageSlot *grown;
  size_t next_capacity;
  if (out_added != NULL) *out_added = 0;
  if (lookup == NULL || !typed_stored_value_has_useful_info(value)) return 0;
  if (kind != M68K_RENDER_TYPED_STORAGE_APP_SLOT && kind != M68K_RENDER_TYPED_STORAGE_ABSOLUTE &&
      kind != M68K_RENDER_TYPED_STORAGE_BASE_SLOT) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    int changed;
    if (!typed_storage_keys_match(slot, kind, section_index, displacement, address)) continue;
    changed = typed_storage_merge_value(slot, value);
    if (changed) {
      slot->source_section_index = source_section_index;
      slot->source_offset = source_offset;
      if (out_added != NULL) *out_added = 1;
    }
    return 0;
  }
  if (lookup->typed_storage_slot_count == lookup->typed_storage_slot_capacity) {
    next_capacity = lookup->typed_storage_slot_capacity == 0U ? 16U : lookup->typed_storage_slot_capacity * 2U;
    grown = (M68kRenderTypedStorageSlot *)realloc(lookup->typed_storage_slots, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->typed_storage_slots = grown;
    lookup->typed_storage_slot_capacity = next_capacity;
  }
  memset(&lookup->typed_storage_slots[lookup->typed_storage_slot_count], 0,
    sizeof(lookup->typed_storage_slots[lookup->typed_storage_slot_count]));
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].kind = kind;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].section_index = section_index;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].displacement = displacement;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].address = address;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].source_section_index = source_section_index;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].source_offset = source_offset;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].value = *value;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].value.known = 1U;
  ++lookup->typed_storage_slot_count;
  if (out_added != NULL) *out_added = 1;
  return 0;
}

int render_lookup_conflict_typed_storage_slot(M68kRenderLookup *lookup, uint8_t kind, size_t section_index,
    int32_t displacement, uint32_t address, size_t source_section_index, uint32_t source_offset, int *out_added) {
  size_t index;
  if (out_added != NULL) *out_added = 0;
  if (lookup == NULL) return 0;
  if (kind != M68K_RENDER_TYPED_STORAGE_APP_SLOT && kind != M68K_RENDER_TYPED_STORAGE_ABSOLUTE &&
      kind != M68K_RENDER_TYPED_STORAGE_BASE_SLOT) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    if (!typed_storage_keys_match(slot, kind, section_index, displacement, address)) continue;
    if (slot->conflicted == 0U) {
      slot->conflicted = 1U;
      slot->value.known = 0U;
      slot->value.output = NULL;
      if (out_added != NULL) *out_added = 1;
    }
    return 0;
  }
  (void)source_section_index;
  (void)source_offset;
  return 0;
}

static int render_lookup_add_typed_app_slot_internal(M68kRenderLookup *lookup, int16_t displacement,
    uint16_t struct_id, uint8_t inline_region, size_t source_section_index, uint32_t source_offset,
    int *out_added) {
  size_t index;
  M68kRenderTypedAppSlot *grown;
  size_t next_capacity;
  M68kRenderTypedStoredValue value;
  int storage_added = 0;
  if (out_added != NULL) *out_added = 0;
  if (lookup == NULL || struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
  typed_stored_value_clear(&value);
  value.known = 1U;
  value.struct_id = struct_id;
  if (render_lookup_add_typed_storage_slot(lookup, M68K_RENDER_TYPED_STORAGE_APP_SLOT, (size_t)-1, displacement,
      0U, &value, source_section_index, source_offset, &storage_added) != 0) {
    return -1;
  }
  if (storage_added && out_added != NULL) *out_added = 1;
  for (index = 0U; index < lookup->typed_app_slot_count; ++index) {
    M68kRenderTypedAppSlot *entry = &lookup->typed_app_slots[index];
    if (entry->displacement != displacement) continue;
    if (entry->struct_id != struct_id && entry->conflicted == 0U) {
      int conflict = 0;
      uint16_t merged_struct_id = typed_struct_id_refined_merge(entry->struct_id, struct_id, &conflict);
      if (conflict) {
        entry->conflicted = 1U;
        if (out_added != NULL) *out_added = 1;
      } else if (merged_struct_id != entry->struct_id) {
        entry->struct_id = merged_struct_id;
        entry->source_section_index = source_section_index;
        entry->source_offset = source_offset;
        if (out_added != NULL) *out_added = 1;
      }
    }
    if (inline_region != 0U && entry->inline_region == 0U && entry->conflicted == 0U) {
      entry->inline_region = 1U;
      entry->source_section_index = source_section_index;
      entry->source_offset = source_offset;
      if (out_added != NULL) *out_added = 1;
    }
    return 0;
  }
  if (lookup->typed_app_slot_count == lookup->typed_app_slot_capacity) {
    next_capacity = lookup->typed_app_slot_capacity == 0U ? 16U : lookup->typed_app_slot_capacity * 2U;
    grown = (M68kRenderTypedAppSlot *)realloc(lookup->typed_app_slots, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->typed_app_slots = grown;
    lookup->typed_app_slot_capacity = next_capacity;
  }
  lookup->typed_app_slots[lookup->typed_app_slot_count].displacement = displacement;
  lookup->typed_app_slots[lookup->typed_app_slot_count].struct_id = struct_id;
  lookup->typed_app_slots[lookup->typed_app_slot_count].conflicted = 0U;
  lookup->typed_app_slots[lookup->typed_app_slot_count].inline_region = inline_region != 0U ? 1U : 0U;
  lookup->typed_app_slots[lookup->typed_app_slot_count].source_section_index = source_section_index;
  lookup->typed_app_slots[lookup->typed_app_slot_count].source_offset = source_offset;
  ++lookup->typed_app_slot_count;
  if (out_added != NULL) *out_added = 1;
  return 0;
}

int render_lookup_add_typed_app_slot(M68kRenderLookup *lookup, int16_t displacement, uint16_t struct_id,
    size_t source_section_index, uint32_t source_offset, int *out_added) {
  return render_lookup_add_typed_app_slot_internal(lookup, displacement, struct_id, 0U,
    source_section_index, source_offset, out_added);
}

int render_lookup_add_typed_app_slot_region(M68kRenderLookup *lookup, int16_t displacement, uint16_t struct_id,
    size_t source_section_index, uint32_t source_offset, int *out_added) {
  return render_lookup_add_typed_app_slot_internal(lookup, displacement, struct_id, 1U,
    source_section_index, source_offset, out_added);
}

int render_lookup_add_typed_access(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t root_struct_id,
    const AmigaOsResolvedStructFieldInfo *field, const char *field_expr,
    const M68kRenderTypedProvenance *provenance) {
  const char *root_struct_name;
  const char *owner_struct_name;
  const char *field_name;
  size_t index;
  M68kRenderTypedAccess *grown;
  size_t next_capacity;
  if (lookup == NULL || field == NULL || field_expr == NULL || field_expr[0] == '\0' ||
      root_struct_id == AMIGA_OS_STRUCT_ID_NONE || operand_index >= 4U || base_reg >= 8U) {
    return 0;
  }
  root_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, root_struct_id);
  owner_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, field->owner_struct_id);
  field_name = amiga_os_name(M68K_PLATFORM_NAME_FIELD, field->field_id);
  if (root_struct_name == NULL || owner_struct_name == NULL || field_name == NULL) return 0;
  for (index = 0U; index < lookup->typed_access_count; ++index) {
    const M68kRenderTypedAccess *entry = &lookup->typed_accesses[index];
    if (entry->section_index == section_index && entry->offset == offset &&
        entry->operand_index == operand_index) {
      return 0;
    }
  }
  if (lookup->typed_access_count == lookup->typed_access_capacity) {
    next_capacity = lookup->typed_access_capacity == 0U ? 32U : lookup->typed_access_capacity * 2U;
    grown = (M68kRenderTypedAccess *)realloc(lookup->typed_accesses, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->typed_accesses = grown;
    lookup->typed_access_capacity = next_capacity;
  }
  memset(&lookup->typed_accesses[lookup->typed_access_count], 0,
    sizeof(lookup->typed_accesses[lookup->typed_access_count]));
  lookup->typed_accesses[lookup->typed_access_count].section_index = section_index;
  lookup->typed_accesses[lookup->typed_access_count].offset = offset;
  lookup->typed_accesses[lookup->typed_access_count].operand_index = operand_index;
  lookup->typed_accesses[lookup->typed_access_count].base_reg = base_reg;
  lookup->typed_accesses[lookup->typed_access_count].displacement = displacement;
  lookup->typed_accesses[lookup->typed_access_count].field_offset = field->offset;
  lookup->typed_accesses[lookup->typed_access_count].inherited = field->inherited;
  lookup->typed_accesses[lookup->typed_access_count].nested = field->nested;
  if (provenance != NULL) {
    lookup->typed_accesses[lookup->typed_access_count].provenance = *provenance;
  }
  snprintf(lookup->typed_accesses[lookup->typed_access_count].root_struct_name,
    sizeof(lookup->typed_accesses[lookup->typed_access_count].root_struct_name), "%s", root_struct_name);
  snprintf(lookup->typed_accesses[lookup->typed_access_count].owner_struct_name,
    sizeof(lookup->typed_accesses[lookup->typed_access_count].owner_struct_name), "%s", owner_struct_name);
  snprintf(lookup->typed_accesses[lookup->typed_access_count].field_name,
    sizeof(lookup->typed_accesses[lookup->typed_access_count].field_name), "%s", field_name);
  snprintf(lookup->typed_accesses[lookup->typed_access_count].field_expr,
    sizeof(lookup->typed_accesses[lookup->typed_access_count].field_expr), "%s", field_expr);
  ++lookup->typed_access_count;
  return 0;
}

int render_lookup_add_unresolved_typed_access(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t root_struct_id,
    uint16_t struct_size, uint8_t refinement_applied, uint16_t refined_struct_id,
    const M68kRenderTypedProvenance *provenance) {
  const char *root_struct_name;
  const char *refined_struct_name = NULL;
  size_t index;
  M68kRenderUnresolvedTypedAccess *grown;
  size_t next_capacity;
  if (lookup == NULL || root_struct_id == AMIGA_OS_STRUCT_ID_NONE || operand_index >= 4U || base_reg >= 8U)
    return 0;
  root_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, root_struct_id);
  if (root_struct_name == NULL || root_struct_name[0] == '\0') return 0;
  if (refinement_applied != 0U && refined_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    refined_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, refined_struct_id);
    if (refined_struct_name == NULL || refined_struct_name[0] == '\0') {
      refinement_applied = 0U;
      refined_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    }
  }
  for (index = 0U; index < lookup->unresolved_typed_access_count; ++index) {
    const M68kRenderUnresolvedTypedAccess *entry = &lookup->unresolved_typed_accesses[index];
    if (entry->section_index == section_index && entry->offset == offset &&
        entry->operand_index == operand_index) {
      return 0;
    }
  }
  if (lookup->unresolved_typed_access_count == lookup->unresolved_typed_access_capacity) {
    next_capacity = lookup->unresolved_typed_access_capacity == 0U
      ? 16U
      : lookup->unresolved_typed_access_capacity * 2U;
    grown = (M68kRenderUnresolvedTypedAccess *)realloc(lookup->unresolved_typed_accesses,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->unresolved_typed_accesses = grown;
    lookup->unresolved_typed_access_capacity = next_capacity;
  }
  memset(&lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count], 0,
    sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count]));
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].section_index = section_index;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].offset = offset;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].operand_index = operand_index;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].base_reg = base_reg;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].displacement = displacement;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].struct_size = struct_size;
  classify_unresolved_typed_access(root_struct_id, displacement, struct_size, 0U,
    &lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].classification,
    &lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_candidate_count,
    lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_struct_name,
    sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_struct_name),
    lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_field_expr,
    sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_field_expr),
    NULL);
  if (refinement_applied != 0U && refined_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].classification =
      M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION;
    snprintf(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_struct_name,
      sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_struct_name),
      "%s", refined_struct_name);
    (void)amiga_os_resolve_struct_field_symbol_expr_by_struct_id(refined_struct_id, displacement, 0,
      lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_field_expr,
      sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_field_expr));
  }
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].refinement_applied =
    refinement_applied != 0U ? 1U : 0U;
  if (provenance != NULL)
    lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].provenance = *provenance;
  snprintf(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].root_struct_name,
    sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].root_struct_name),
    "%s", root_struct_name);
  if (refinement_applied != 0U && refined_struct_name != NULL) {
    snprintf(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].refined_struct_name,
      sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].refined_struct_name),
      "%s", refined_struct_name);
  }
  ++lookup->unresolved_typed_access_count;
  return 0;
}

int render_lookup_add_string_span(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint32_t size) {
  size_t index;
  M68kRenderStringSpan *grown;
  size_t next_capacity;
  if (lookup == NULL || size == 0U) return 0;
  for (index = 0U; index < lookup->string_span_count; ++index) {
    M68kRenderStringSpan *entry = &lookup->string_spans[index];
    if (entry->section_index == section_index && entry->offset == offset) {
      if (entry->size != size) entry->size = 0U;
      return 0;
    }
  }
  if (lookup->string_span_count == lookup->string_span_capacity) {
    next_capacity = lookup->string_span_capacity == 0U ? 16U : lookup->string_span_capacity * 2U;
    grown = (M68kRenderStringSpan *)realloc(lookup->string_spans, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->string_spans = grown;
    lookup->string_span_capacity = next_capacity;
  }
  lookup->string_spans[lookup->string_span_count].section_index = section_index;
  lookup->string_spans[lookup->string_span_count].offset = offset;
  lookup->string_spans[lookup->string_span_count].size = size;
  ++lookup->string_span_count;
  return 0;
}

const char *lookup_instruction_comment(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  size_t index;
  const size_t *index_slot;
  if (lookup == NULL) return NULL;
  index_slot = lookup_instruction_comment_index_slot_const(lookup, section_index, offset);
  if (index_slot != NULL && *index_slot != 0U && *index_slot <= lookup->instruction_comment_count) {
    const M68kRenderInstructionComment *entry = &lookup->instruction_comments[*index_slot - 1U];
    if (entry->section_index == section_index && entry->offset == offset && entry->comment[0] != '\0')
      return entry->comment;
  }
  for (index = 0U; index < lookup->instruction_comment_count; ++index) {
    const M68kRenderInstructionComment *entry = &lookup->instruction_comments[index];
    if (entry->section_index == section_index && entry->offset == offset && entry->comment[0] != '\0')
      return entry->comment;
  }
  return NULL;
}

const M68kRenderStringSpan *lookup_string_span_at_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->string_span_count; ++index) {
    const M68kRenderStringSpan *entry = &lookup->string_spans[index];
    if (entry->section_index == section_index && entry->offset == offset && entry->size != 0U) return entry;
  }
  return NULL;
}

static const char *amiga_library_base_name_for_render_effect(const char *library_name) {
  const char *base_name;
  if (library_name == NULL || library_name[0] == '\0') return NULL;
  base_name = amiga_os_find_library_base_name(library_name);
  return base_name != NULL && base_name[0] != '\0' ? base_name : NULL;
}

static int append_render_lookup_platform_effects_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    const M68kRenderGlobalBaseSlot *slot = &lookup->global_base_slots[index];
    const char *base_name = amiga_library_base_name_for_render_effect(slot->library_name);
    if (slot->has_source == 0U || slot->source_section_index != section_analysis->section_index ||
        base_name == NULL) {
      continue;
    }
    if (m68k_ir_section_analysis_append_recovered_platform_global_base_slot_effect(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, slot->section_index, slot->offset,
        base_name) != 0) {
      return -1;
    }
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    const char *base_name = amiga_library_base_name_for_render_effect(slot->library_name);
    if (slot->has_source == 0U || slot->source_section_index != section_analysis->section_index ||
        slot->conflicted != 0U || !base_field_slot_is_base_pointer(slot) ||
        base_name == NULL) {
      continue;
    }
    if (strcmp(slot->owner_name, "__amiga_app_base__") != 0) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_base_slot(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->displacement, base_name) != 0 ||
        m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT,
        0U, 0U, slot->displacement, INT16_MIN, base_name, NULL, NULL, NULL, NULL, 0U, 0) != 0) {
      return -1;
    }
  }
  for (index = 0U; index < lookup->typed_slot_effect_count; ++index) {
    const M68kRenderTypedSlotEffect *effect = &lookup->typed_slot_effects[index];
    const AmigaOsCallOutputInfo *output = effect->output;
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (effect->section_index != section_analysis->section_index || output == NULL) continue;
    symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
    type_name = amiga_output_type_or_struct_name(output);
    semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
    value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
    if ((symbol_name == NULL || symbol_name[0] == '\0') &&
        (type_name == NULL || type_name[0] == '\0') &&
        (semantic_kind == NULL || semantic_kind[0] == '\0') &&
        (value_domain_name == NULL || value_domain_name[0] == '\0')) {
      continue;
    }
    if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, effect->offset, M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT,
        0U, 0U, effect->displacement, INT16_MIN, NULL, symbol_name, type_name, semantic_kind,
        value_domain_name, 0U, 0) != 0) {
      return -1;
    }
  }
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    const M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (slot->conflicted != 0U || slot->source_section_index != section_analysis->section_index ||
        !typed_stored_value_has_useful_info(&slot->value)) {
      continue;
    }
    typed_stored_value_platform_names(&slot->value, &symbol_name, &type_name, &semantic_kind,
      &value_domain_name);
    if ((symbol_name == NULL || symbol_name[0] == '\0') &&
        (type_name == NULL || type_name[0] == '\0') &&
        (semantic_kind == NULL || semantic_kind[0] == '\0') &&
        (value_domain_name == NULL || value_domain_name[0] == '\0')) {
      continue;
    }
    if (slot->kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
      int has_direct_slot_effect = 0;
      size_t effect_index;
      if (slot->displacement < INT16_MIN || slot->displacement > INT16_MAX) continue;
      for (effect_index = 0U; effect_index < lookup->typed_slot_effect_count; ++effect_index) {
        const M68kRenderTypedSlotEffect *effect = &lookup->typed_slot_effects[effect_index];
        if (effect->section_index == slot->source_section_index && effect->offset == slot->source_offset &&
            effect->displacement == (int16_t)slot->displacement) {
          has_direct_slot_effect = 1;
          break;
        }
      }
      if (has_direct_slot_effect) continue;
      if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
          M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT,
          0U, 0U, (int16_t)slot->displacement, INT16_MIN, NULL, symbol_name, type_name, semantic_kind,
          value_domain_name, 0U, 0) != 0) {
        return -1;
      }
    } else if (slot->kind == M68K_RENDER_TYPED_STORAGE_ABSOLUTE) {
      if (m68k_ir_section_analysis_append_recovered_platform_typed_global_slot_effect(section_analysis,
          M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, slot->section_index, slot->address,
          symbol_name, type_name, semantic_kind, value_domain_name) != 0) {
        return -1;
      }
    } else if (slot->kind == M68K_RENDER_TYPED_STORAGE_BASE_SLOT) {
      uint32_t target_offset = 0U;
      if (!typed_memory_base_offset_add(slot->address, slot->displacement, &target_offset)) continue;
      if (m68k_ir_section_analysis_append_recovered_platform_typed_global_slot_effect(section_analysis,
          M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, slot->section_index, target_offset,
          symbol_name, type_name, semantic_kind, value_domain_name) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int append_render_lookup_app_slot_refs_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->app_slot_ref_count; ++index) {
    const M68kRenderAppSlotRef *ref = &lookup->app_slot_refs[index];
    if (ref->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_app_slot_ref(section_analysis, &ref->ref) != 0) return -1;
  }
  return 0;
}

static int append_render_lookup_runtime_views_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    M68kRuntimeViewIR view;
    if (fact == NULL || fact->section_index != section_analysis->section_index ||
        fact->size == 0U || !fact->has_runtime_address) {
      continue;
    }
    memset(&view, 0, sizeof(view));
    view.runtime_view_id = (uint32_t)index;
    view.storage_offset = fact->offset;
    view.size = fact->size;
    view.runtime_address = fact->runtime_address;
    view.kind = fact->runtime_kind;
    view.confidence = fact->confidence;
    if (m68k_ir_section_analysis_append_runtime_view(section_analysis, &view) != 0) return -1;
  }
  return 0;
}

static const char *runtime_address_ref_data_class(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    const M68kFact *fact);

static int append_render_lookup_runtime_address_refs_for_section(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_refs[index].fact;
    M68kRuntimeAddressRefIR ref;
    if (fact == NULL || fact->section_index != section_analysis->section_index) continue;
    memset(&ref, 0, sizeof(ref));
    ref.offset = fact->offset;
    ref.operand_index = fact->reason;
    ref.has_target = fact->target_section_index < lookup->section_count;
    ref.target_section_index = fact->target_section_index;
    ref.target_offset = fact->target_offset;
    ref.has_runtime_address = fact->has_runtime_address;
    ref.runtime_address = fact->runtime_address;
    ref.confidence = fact->confidence;
    ref.data_class = (char *)runtime_address_ref_data_class(lookup, decode, fact);
    if (m68k_ir_section_analysis_append_runtime_address_ref(section_analysis, &ref) != 0) return -1;
  }
  for (index = 0U; index < lookup->inferred_runtime_address_ref_count; ++index) {
    const M68kRenderInferredRuntimeAddressRef *entry = &lookup->inferred_runtime_address_refs[index];
    if (entry->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_runtime_address_ref(section_analysis, &entry->ref) != 0) return -1;
  }
  return 0;
}

static int append_render_lookup_code_start_refs_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->code_start_ref_count; ++index) {
    const M68kFact *fact = lookup->code_start_refs[index].fact;
    M68kCodeStartRefIR ref;
    if (fact == NULL || fact->section_index != section_analysis->section_index) continue;
    memset(&ref, 0, sizeof(ref));
    ref.offset = fact->offset;
    ref.reason = fact->reason;
    ref.confidence = fact->confidence;
    ref.has_runtime_address = fact->has_runtime_address;
    ref.source_section_index = fact->source_section_index;
    ref.source_offset = fact->source_offset;
    ref.runtime_address = fact->runtime_address;
    ref.size = fact->size;
    if (m68k_ir_section_analysis_append_code_start_ref(section_analysis, &ref) != 0) return -1;
  }
  return 0;
}

static const char *render_lookup_code_start_reason_name(uint32_t reason) {
  switch (reason) {
  case M68K_FACT_CODE_START_REASON_SECTION_ENTRY:
    return "section_entry";
  case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET:
    return "policy_entry_offset";
  case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT:
    return "policy_entry_point";
  case M68K_FACT_CODE_START_REASON_CONTROL_TARGET:
    return "control_target";
  case M68K_FACT_CODE_START_REASON_FALLTHROUGH:
    return "fallthrough";
  case M68K_FACT_CODE_START_REASON_INLINE_RESUME:
    return "inline_resume";
  default:
    return "unknown";
  }
}

static void data_pointer_state_update_after_instruction(M68kRenderDataPointerState *state,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  data_pointer_state_update_after_instruction_ex(state, lookup, section, candidate, instruction, 0U);
}

static int append_render_lookup_violations_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->violation_ref_count; ++index) {
    const M68kFact *fact = lookup->violation_refs[index].fact;
    uint8_t kind;
    char message[192];
    if (fact == NULL || fact->section_index != section_analysis->section_index) continue;
    if (fact->target_section_index == fact->section_index && fact->target_offset == fact->offset) {
      kind = M68K_VIOLATION_DECODE_FAILED_REACHABLE;
      snprintf(message, sizeof(message),
        "%s code candidate at $%04X rejected after source $%04X; emitted as data",
        render_lookup_code_start_reason_name(fact->reason), (unsigned)fact->offset,
        (unsigned)fact->source_offset);
    } else {
      kind = M68K_VIOLATION_INVALID_INTERIOR_REFERENCE;
      snprintf(message, sizeof(message),
        "code/data boundary conflict at $%04X references $%04X; emitted as data",
        (unsigned)fact->offset, (unsigned)fact->target_offset);
    }
    if (m68k_ir_section_analysis_add_violation(section_analysis, fact->offset, kind, message) != 0) return -1;
  }
  return 0;
}

static int asm_candidate_operand_absolute_value(const M68kDecodeCandidate *candidate, size_t operand_index,
    uint32_t *out_value) {
  const M68kAsmOperandValue *operand;
  uint8_t kind;
  if (out_value != NULL) *out_value = 0U;
  if (candidate == NULL || operand_index >= candidate->operand_count || out_value == NULL) return 0;
  operand = &candidate->operands[operand_index];
  kind = candidate->operand_kinds[operand_index];
  if (kind == M68K_ASM_OPERAND_ABSL ||
      (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U &&
        (operand->ea_reg == 0U || operand->ea_reg == 1U))) {
    *out_value = operand->value;
    return 1;
  }
  return 0;
}

static const char *runtime_address_ref_data_class(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    const M68kFact *fact) {
  const M68kDecodeSectionIR *section;
  const M68kDecodeCandidate *candidate;
  uint32_t sink_address = 0U;
  if (lookup == NULL || lookup->object == NULL || decode == NULL || fact == NULL ||
      fact->kind != M68K_FACT_RUNTIME_ADDRESS_REF || fact->section_index >= decode->section_count) {
    return NULL;
  }
  section = &decode->sections[fact->section_index];
  candidate = find_candidate_at_offset_local(section, fact->offset);
  if (candidate == NULL ||
      (fact->reason != UINT32_MAX && fact->reason >= candidate->operand_count)) {
    return NULL;
  }
  if (!((fact->reason == 0U || fact->reason == UINT32_MAX) &&
        candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
        candidate->size_suffix == 'l' && candidate->operand_count == 2U)) {
    return NULL;
  }
  if (!asm_candidate_operand_absolute_value(candidate, 1U, &sink_address)) return NULL;
  return platform_facts_v2_runtime_address_sink_data_class(lookup->object->platform_backend_kind, sink_address);
}

static int runtime_address_ref_sink_address(const M68kDecodeIR *decode, const M68kFact *fact,
    uint32_t *out_sink_address) {
  const M68kDecodeSectionIR *section;
  const M68kDecodeCandidate *candidate;
  if (out_sink_address != NULL) *out_sink_address = 0U;
  if (decode == NULL || fact == NULL || out_sink_address == NULL ||
      fact->kind != M68K_FACT_RUNTIME_ADDRESS_REF || fact->section_index >= decode->section_count) {
    return 0;
  }
  section = &decode->sections[fact->section_index];
  candidate = find_candidate_at_offset_local(section, fact->offset);
  if (candidate == NULL ||
      !((fact->reason == 0U || fact->reason == UINT32_MAX) &&
        candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
        candidate->size_suffix == 'l' && candidate->operand_count == 2U)) {
    return 0;
  }
  return asm_candidate_operand_absolute_value(candidate, 1U, out_sink_address);
}

static uint32_t copper_list_size_at(const M68kDecodeSectionIR *section, uint32_t offset) {
  uint32_t cursor;
  if (section == NULL || section->data == NULL || offset >= section->size || ((section->size - offset) < 4U))
    return 0U;
  for (cursor = offset; cursor + 4U <= section->size; cursor += 4U) {
    uint16_t first = m68k_read_u16be(section->data + cursor);
    uint16_t second = m68k_read_u16be(section->data + cursor + 2U);
    if (first == 0xFFFFU && second == 0xFFFEU) return cursor + 4U - offset;
  }
  return 0U;
}

static const AmigaOsHardwareRegisterInfo *copper_runtime_pointer_register_local(uint16_t copper_register_word) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  uint32_t offset = (uint32_t)(copper_register_word & 0x01FEU);
  if ((copper_register_word & 1U) != 0U) return NULL;
  hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", offset);
  if (hardware_register == NULL) {
    hardware_range = amiga_os_find_hardware_register_range_by_base_offset("_custom", offset);
    if (hardware_range != NULL)
      hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", hardware_range->offset);
  }
  if (hardware_register == NULL ||
      (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U ||
      hardware_register->runtime_target_role == NULL || hardware_register->runtime_target_role[0] == '\0') {
    return NULL;
  }
  return hardware_register;
}

static int copper_list_bitmap_pointer_at(const uint8_t *data, uint32_t offset, uint32_t cursor,
    uint32_t size, uint32_t *out_pointer) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  uint16_t first;
  uint16_t second;
  uint16_t next_first;
  uint16_t next_second;
  uint32_t register_offset;
  if (out_pointer != NULL) *out_pointer = 0U;
  if (data == NULL || out_pointer == NULL || cursor + 8U > size) return 0;
  first = m68k_read_u16be(data + offset + cursor);
  second = m68k_read_u16be(data + offset + cursor + 2U);
  next_first = m68k_read_u16be(data + offset + cursor + 4U);
  next_second = m68k_read_u16be(data + offset + cursor + 6U);
  if ((first & 1U) != 0U || (next_first & 1U) != 0U) return 0;
  register_offset = (uint32_t)(first & 0x01FEU);
  hardware_register = copper_runtime_pointer_register_local(first);
  if (hardware_register == NULL || hardware_register->runtime_target_role == NULL ||
      strcmp(hardware_register->runtime_target_role, "bitmap") != 0) {
    return 0;
  }
  if (register_offset < hardware_register->offset ||
      ((register_offset - hardware_register->offset) & 3U) != 0U) {
    return 0;
  }
  if ((uint32_t)(next_first & 0x01FEU) != register_offset + 2U) return 0;
  *out_pointer = ((uint32_t)second << 16) | next_second;
  return *out_pointer != 0U;
}

static uint8_t collect_copper_bitmap_pointers(const M68kDecodeSectionIR *section, uint32_t offset, uint32_t size,
    uint32_t *row_offsets, uint32_t *pointers, uint8_t pointer_limit) {
  uint32_t cursor;
  uint8_t pointer_count = 0U;
  if (section == NULL || section->data == NULL || pointers == NULL || pointer_limit == 0U || size == 0U)
    return 0U;
  for (cursor = 0U; cursor + 8U <= size && pointer_count < pointer_limit; cursor += 4U) {
    uint32_t pointer = 0U;
    if (!copper_list_bitmap_pointer_at(section->data, offset, cursor, size, &pointer)) continue;
    if (row_offsets != NULL) row_offsets[pointer_count] = offset + cursor;
    pointers[pointer_count++] = pointer;
  }
  return pointer_count;
}

static uint32_t copper_bitmap_pointer_even_step(const uint32_t *pointers, uint8_t pointer_count) {
  uint32_t step = 0U;
  uint8_t index;
  if (pointers == NULL || pointer_count < 2U || pointers[1] <= pointers[0]) return 0U;
  step = pointers[1] - pointers[0];
  if (step == 0U) return 0U;
  for (index = 2U; index < pointer_count; ++index) {
    if (pointers[index] <= pointers[index - 1U] || pointers[index] - pointers[index - 1U] != step)
      return 0U;
  }
  return step;
}

static int format_copper_display_layout_comment(const M68kDecodeSectionIR *section, uint32_t offset,
    uint32_t size, char *comment, size_t comment_size) {
  uint32_t pointers[8];
  uint8_t pointer_count = 0U;
  uint32_t step = 0U;
  if (comment != NULL && comment_size != 0U) comment[0] = '\0';
  if (section == NULL || section->data == NULL || comment == NULL || comment_size == 0U || size == 0U)
    return 0;
  pointer_count = collect_copper_bitmap_pointers(section, offset, size, NULL, pointers,
    (uint8_t)(sizeof(pointers) / sizeof(pointers[0])));
  if (pointer_count == 0U) return 0;
  step = copper_bitmap_pointer_even_step(pointers, pointer_count);
  if (step != 0U) {
    snprintf(comment, comment_size, "display layout %u bitmap planes $%08X..$%08X step $%X",
      (unsigned)pointer_count, (unsigned)pointers[0], (unsigned)pointers[pointer_count - 1U],
      (unsigned)step);
  } else if (pointer_count == 1U) {
    snprintf(comment, comment_size, "display layout 1 bitmap plane $%08X", (unsigned)pointers[0]);
  } else {
    snprintf(comment, comment_size, "display layout %u bitmap plane bases from $%08X",
      (unsigned)pointer_count, (unsigned)pointers[0]);
  }
  return strlen(comment) + 1U < comment_size;
}

static int render_lookup_add_copper_bitmap_runtime_refs(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset, uint32_t size) {
  uint32_t row_offsets[8];
  uint32_t pointers[8];
  uint32_t step;
  uint8_t index;
  uint8_t pointer_count;
  if (lookup == NULL || section == NULL) return 0;
  pointer_count = collect_copper_bitmap_pointers(section, offset, size, row_offsets, pointers,
    (uint8_t)(sizeof(pointers) / sizeof(pointers[0])));
  if (pointer_count == 0U) return 0;
  step = copper_bitmap_pointer_even_step(pointers, pointer_count);
  for (index = 0U; index < pointer_count; ++index) {
    if (render_lookup_add_inferred_runtime_address_ref(lookup, section->section_index, row_offsets[index],
        pointers[index], step, "bitmap") != 0) {
      return -1;
    }
  }
  return 0;
}

typedef struct M68kRenderBitmapRuntimeAddress {
  uint8_t matched;
  uint8_t plane_index;
  uint32_t base;
  uint32_t size;
  uint32_t delta;
} M68kRenderBitmapRuntimeAddress;

typedef struct M68kRenderBitmapBaseState {
  M68kRenderBitmapRuntimeAddress address_regs[8];
} M68kRenderBitmapBaseState;

static int bitmap_runtime_address_for_value(const M68kRenderLookup *lookup, uint32_t value,
    M68kRenderBitmapRuntimeAddress *out_address) {
  size_t index;
  uint8_t plane_index = 0U;
  if (out_address != NULL) memset(out_address, 0, sizeof(*out_address));
  if (lookup == NULL || out_address == NULL) return 0;
  for (index = 0U; index < lookup->inferred_runtime_address_ref_count; ++index) {
    const M68kRenderInferredRuntimeAddressRef *entry = &lookup->inferred_runtime_address_refs[index];
    uint32_t base;
    uint32_t size;
    if (entry->ref.data_class == NULL || strcmp(entry->ref.data_class, "bitmap") != 0 ||
        !entry->ref.has_runtime_address) {
      continue;
    }
    base = entry->ref.runtime_address;
    size = entry->ref.size;
    if ((size == 0U && value == base) ||
        (size != 0U && value >= base && value - base < size)) {
      out_address->matched = 1U;
      out_address->plane_index = plane_index;
      out_address->base = base;
      out_address->size = size;
      out_address->delta = value - base;
      return 1;
    }
    if (plane_index != UINT8_MAX) ++plane_index;
  }
  return 0;
}

static int format_bitmap_memory_comment(const M68kRenderBitmapRuntimeAddress *address,
    char *comment, size_t comment_size) {
  int written;
  if (comment != NULL && comment_size != 0U) comment[0] = '\0';
  if (address == NULL || !address->matched || comment == NULL || comment_size == 0U) return 0;
  if (address->delta == 0U) {
    written = snprintf(comment, comment_size, "bitmap memory plane %u base $%08X",
      (unsigned)address->plane_index, (unsigned)address->base);
  } else {
    written = snprintf(comment, comment_size, "bitmap memory plane %u +$%X ($%08X)",
      (unsigned)address->plane_index, (unsigned)address->delta,
      (unsigned)(address->base + address->delta));
  }
  return written > 0 && (size_t)written < comment_size;
}

static int render_lookup_add_bitmap_memory_comment(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, const M68kRenderBitmapRuntimeAddress *address) {
  char comment[96];
  int result;
  if (!format_bitmap_memory_comment(address, comment, sizeof(comment))) return 0;
  result = render_lookup_add_instruction_comment(lookup, section_index, offset, comment);
  if (result != 0) return result;
  return render_lookup_add_inferred_runtime_address_ref(lookup, section_index, offset,
    address->base + address->delta, 0U, "bitmap");
}

static int operand_runtime_address_from_bitmap_base(const M68kRenderBitmapBaseState *state,
    const M68kOperandIR *operand, M68kRenderBitmapRuntimeAddress *out_address) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  int64_t value;
  const M68kRenderBitmapRuntimeAddress *base;
  if (out_address != NULL) memset(out_address, 0, sizeof(*out_address));
  if (state == NULL || operand == NULL || out_address == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
      !state->address_regs[base_reg].matched) {
    return 0;
  }
  base = &state->address_regs[base_reg];
  value = (int64_t)base->base + (int64_t)base->delta + (int64_t)displacement;
  if (value < 0 || value > UINT32_MAX) return 0;
  *out_address = *base;
  if ((uint32_t)value < out_address->base) return 0;
  out_address->delta = (uint32_t)value - out_address->base;
  if (out_address->size != 0U && out_address->delta >= out_address->size) return 0;
  return 1;
}

static int render_lookup_comment_bitmap_memory_uses_for_instruction(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, const M68kRenderBitmapBaseState *state) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (lookup == NULL || section == NULL || candidate == NULL || instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    M68kRenderBitmapRuntimeAddress address;
    uint32_t absolute = 0U;
    uint8_t access = metadata != NULL && operand_index < 4U ?
      metadata->operand_access_kinds[operand_index] : M68K_SIM_ACCESS_NONE;
    if (operand_absolute_offset_local(operand, &absolute) &&
        bitmap_runtime_address_for_value(lookup, absolute, &address)) {
      if (render_lookup_add_bitmap_memory_comment(lookup, section->section_index, candidate->offset,
          &address) != 0) {
        return -1;
      }
      continue;
    }
    if ((access == M68K_SIM_ACCESS_MEMORY_READ || access == M68K_SIM_ACCESS_MEMORY_WRITE) &&
        operand_runtime_address_from_bitmap_base(state, operand, &address)) {
      if (render_lookup_add_bitmap_memory_comment(lookup, section->section_index, candidate->offset,
          &address) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static void bitmap_base_state_update_after_instruction(M68kRenderBitmapBaseState *state,
    const M68kRenderLookup *lookup, const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  M68kRenderBitmapRuntimeAddress absolute_address;
  uint8_t has_absolute_address = 0U;
  size_t operand_index;
  if (state == NULL || lookup == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return;
  memset(&absolute_address, 0, sizeof(absolute_address));
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    uint32_t absolute = 0U;
    if (operand_absolute_offset_local(&instruction->operands[operand_index], &absolute) &&
        bitmap_runtime_address_for_value(lookup, absolute, &absolute_address)) {
      has_absolute_address = 1U;
      break;
    }
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        operand_address_register_index_local(&instruction->operands[operand_index], &reg) && reg < 8U) {
      if (has_absolute_address) state->address_regs[reg] = absolute_address;
      else memset(&state->address_regs[reg], 0, sizeof(state->address_regs[reg]));
    } else if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_LIST_WRITE) {
      uint8_t bit;
      for (bit = 0U; bit < 8U; ++bit) {
        if (reglist_contains_address_register_local(&instruction->operands[operand_index], bit))
          memset(&state->address_regs[bit], 0, sizeof(state->address_regs[bit]));
      }
    }
    if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_NONE &&
        operand_is_address_memory_local(&instruction->operands[operand_index], &reg, NULL) && reg < 8U) {
      memset(&state->address_regs[reg], 0, sizeof(state->address_regs[reg]));
    }
  }
}

static int render_lookup_infer_amiga_bitmap_memory_uses(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL ||
      lookup->inferred_runtime_address_ref_count == 0U) {
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderBitmapBaseState state;
    size_t candidate_index;
    memset(&state, 0, sizeof(state));
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      if (render_lookup_comment_bitmap_memory_uses_for_instruction(lookup, section, candidate,
          &instruction, &state) != 0) {
        return -1;
      }
      bitmap_base_state_update_after_instruction(&state, lookup, &instruction);
    }
  }
  return 0;
}

typedef struct M68kRenderDisplaySetup {
  uint8_t has_bplcon0;
  uint8_t has_diwstrt;
  uint8_t has_diwstop;
  uint8_t has_ddfstrt;
  uint8_t has_ddfstop;
  uint8_t has_bpl1mod;
  uint8_t has_bpl2mod;
  uint16_t bplcon0;
  uint16_t diwstrt;
  uint16_t diwstop;
  uint16_t ddfstrt;
  uint16_t ddfstop;
  int16_t bpl1mod;
  int16_t bpl2mod;
} M68kRenderDisplaySetup;

static int display_setup_record_register_write(M68kRenderDisplaySetup *setup,
    const AmigaOsHardwareRegisterInfo *hardware_register, uint32_t value) {
  uint16_t word = (uint16_t)value;
  if (setup == NULL || hardware_register == NULL || hardware_register->symbol_name == NULL) return 0;
  if (strcmp(hardware_register->symbol_name, "bplcon0") == 0) {
    setup->has_bplcon0 = 1U;
    setup->bplcon0 = word;
    return 1;
  }
  if (strcmp(hardware_register->symbol_name, "diwstrt") == 0) {
    setup->has_diwstrt = 1U;
    setup->diwstrt = word;
    return 1;
  }
  if (strcmp(hardware_register->symbol_name, "diwstop") == 0) {
    setup->has_diwstop = 1U;
    setup->diwstop = word;
    return 1;
  }
  if (strcmp(hardware_register->symbol_name, "ddfstrt") == 0) {
    setup->has_ddfstrt = 1U;
    setup->ddfstrt = word;
    return 1;
  }
  if (strcmp(hardware_register->symbol_name, "ddfstop") == 0) {
    setup->has_ddfstop = 1U;
    setup->ddfstop = word;
    return 1;
  }
  if (strcmp(hardware_register->symbol_name, "bpl1mod") == 0) {
    setup->has_bpl1mod = 1U;
    setup->bpl1mod = (int16_t)word;
    return 1;
  }
  if (strcmp(hardware_register->symbol_name, "bpl2mod") == 0) {
    setup->has_bpl2mod = 1U;
    setup->bpl2mod = (int16_t)word;
    return 1;
  }
  return 0;
}

static int display_setup_collect_immediate_write(M68kRenderDisplaySetup *setup,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  size_t source_index = 0U, dest_index = 0U;
  uint32_t value = 0U;
  uint32_t dest_address = 0U;
  if (setup == NULL || candidate == NULL || instruction == NULL || instruction->size_suffix != 'w' ||
      !instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata) ||
      metadata == NULL || metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
      !operand_is_immediate_value_local(&instruction->operands[source_index], &value) ||
      !asm_candidate_operand_absolute_value(candidate, dest_index, &dest_address)) {
    return 0;
  }
  hardware_register = amiga_os_find_hardware_register_by_cpu_address(dest_address);
  return display_setup_record_register_write(setup, hardware_register, value);
}

static int collect_display_setup_before_offset(const M68kDecodeSectionIR *section, uint8_t *accepted_start,
    uint32_t end_offset, M68kRenderDisplaySetup *setup) {
  size_t candidate_index;
  if (setup != NULL) memset(setup, 0, sizeof(*setup));
  if (section == NULL || accepted_start == NULL || setup == NULL) return 0;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    if (candidate->offset >= end_offset) break;
    if (!candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    (void)display_setup_collect_immediate_write(setup, candidate, &instruction);
  }
  return setup->has_bplcon0 || setup->has_diwstrt || setup->has_diwstop ||
    setup->has_ddfstrt || setup->has_ddfstop || setup->has_bpl1mod || setup->has_bpl2mod;
}

static int format_display_setup_comment(const M68kRenderDisplaySetup *setup, char *comment,
    size_t comment_size) {
  uint32_t plane_count;
  const char *resolution;
  const char *color;
  int written;
  if (comment != NULL && comment_size != 0U) comment[0] = '\0';
  if (setup == NULL || comment == NULL || comment_size == 0U || !setup->has_bplcon0) return 0;
  plane_count = ((uint32_t)setup->bplcon0 >> 12) & 7U;
  if (plane_count == 0U) return 0;
  resolution = (setup->bplcon0 & 0x8000U) != 0U ? "hires" : "lores";
  color = (setup->bplcon0 & 0x0200U) != 0U ? " color" : "";
  written = snprintf(comment, comment_size, "display setup %u bitplanes %s%s",
    (unsigned)plane_count, resolution, color);
  if (written <= 0 || (size_t)written >= comment_size) return 0;
  if (setup->has_diwstrt && setup->has_diwstop) {
    written = snprintf(comment + strlen(comment), comment_size - strlen(comment),
      " window v=$%02X..$%02X h=$%02X..$%02X",
      (unsigned)((setup->diwstrt >> 8) & 0xFFU), (unsigned)((setup->diwstop >> 8) & 0xFFU),
      (unsigned)(setup->diwstrt & 0xFFU), (unsigned)(setup->diwstop & 0xFFU));
    if (written <= 0 || (size_t)written >= comment_size - strlen(comment)) return 0;
  }
  if (setup->has_ddfstrt && setup->has_ddfstop) {
    written = snprintf(comment + strlen(comment), comment_size - strlen(comment),
      " fetch $%02X..$%02X", (unsigned)(setup->ddfstrt & 0xFFU), (unsigned)(setup->ddfstop & 0xFFU));
    if (written <= 0 || (size_t)written >= comment_size - strlen(comment)) return 0;
  }
  if (setup->has_bpl1mod && setup->has_bpl2mod) {
    written = snprintf(comment + strlen(comment), comment_size - strlen(comment),
      " mod %d/%d", (int)setup->bpl1mod, (int)setup->bpl2mod);
    if (written <= 0 || (size_t)written >= comment_size - strlen(comment)) return 0;
  }
  return 1;
}

typedef struct M68kRenderAudioLengthSource {
  uint8_t known;
  uint8_t base_reg;
  int16_t displacement;
  uint8_t transformed;
} M68kRenderAudioLengthSource;

typedef struct M68kRenderAudioPeriodSource {
  uint8_t known;
  uint8_t transformed;
  size_t section_index;
  uint32_t offset;
} M68kRenderAudioPeriodSource;

typedef struct M68kRenderHardwareRangePointer {
  uint8_t known;
  const AmigaOsHardwareRegisterRangeInfo *range;
  uint32_t offset;
} M68kRenderHardwareRangePointer;

typedef struct M68kRenderHardwareRangePointerState {
  M68kRenderHardwareRangePointer addr_regs[8];
} M68kRenderHardwareRangePointerState;

static void audio_length_sources_clear(M68kRenderAudioLengthSource sources[8]) {
  memset(sources, 0, 8U * sizeof(sources[0]));
}

static void audio_period_sources_clear(M68kRenderAudioPeriodSource sources[8]) {
  memset(sources, 0, 8U * sizeof(sources[0]));
}

static int audio_length_write_source_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint8_t *out_reg) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  size_t source_index = 0U, dest_index = 0U;
  uint32_t dest_address = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_reg == NULL ||
      instruction->size_suffix != 'w' ||
      !instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata) ||
      metadata == NULL || metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
      !operand_is_data_register_local(&instruction->operands[source_index], out_reg) ||
      !asm_candidate_operand_absolute_value(candidate, dest_index, &dest_address)) {
    return 0;
  }
  hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(dest_address);
  return hardware_field != NULL && hardware_field->field_symbol != NULL &&
    strcmp(hardware_field->field_symbol, "ac_len") == 0;
}

static int audio_period_write_source_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint8_t *out_reg) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  size_t source_index = 0U, dest_index = 0U;
  uint32_t dest_address = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_reg == NULL ||
      instruction->size_suffix != 'w' ||
      !instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata) ||
      metadata == NULL || metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
      !operand_is_data_register_local(&instruction->operands[source_index], out_reg) ||
      !asm_candidate_operand_absolute_value(candidate, dest_index, &dest_address)) {
    return 0;
  }
  hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(dest_address);
  return hardware_field != NULL && hardware_field->field_symbol != NULL &&
    strcmp(hardware_field->field_symbol, "ac_per") == 0;
}

static int render_lookup_add_audio_length_source_comment(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, const M68kRenderAudioLengthSource *source) {
  char comment[128];
  char disp[32];
  if (lookup == NULL || source == NULL || !source->known) return 0;
  if (source->displacement < 0) snprintf(disp, sizeof(disp), "-$%04X", (unsigned)(uint16_t)(-source->displacement));
  else if (source->displacement > 0) snprintf(disp, sizeof(disp), "$%04X", (unsigned)(uint16_t)source->displacement);
  else disp[0] = '\0';
  snprintf(comment, sizeof(comment), "audio sample length %s%s(a%u) header word",
    source->transformed ? "derived from " : "from ", disp, (unsigned)source->base_reg);
  return render_lookup_add_instruction_comment(lookup, section_index, offset, comment);
}

static void format_pointer_source_label(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset);

static int render_lookup_add_audio_period_source_comment(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, const M68kRenderAudioPeriodSource *source) {
  char label[64];
  char comment[128];
  if (lookup == NULL || source == NULL || !source->known) return 0;
  format_pointer_source_label(lookup, label, sizeof(label), source->section_index, source->offset);
  snprintf(comment, sizeof(comment), "period from %s%s", label, source->transformed ? " transformed" : "");
  return render_lookup_add_instruction_comment(lookup, section_index, offset, comment);
}

static void format_pointer_source_label(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset) {
  uint32_t runtime_address = 0U;
  if (buf == NULL || buf_size == 0U) return;
  if (lookup_source_should_render_runtime_label(lookup, section_index, offset, &runtime_address)) {
    snprintf(buf, buf_size, "loc_%u_%08X", (unsigned)section_index, (unsigned)runtime_address);
    return;
  }
  (void)format_lookup_asm_label_with_generation(lookup, buf, buf_size, section_index, offset);
}

static int render_lookup_add_audio_pointer_source_comment(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_bytes, size_t section_index, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, const M68kRenderDataPointerState *state) {
  const M68kSimFormMetadata *metadata;
  const M68kRenderDataPointerValue *value;
  const char *data_class;
  size_t source_index = 0U, dest_index = 0U;
  uint8_t source_reg = 0U;
  uint8_t platform_kind;
  uint32_t dest_address = 0U;
  char label[64];
  char table_label[64];
  char comment[192];
  if (lookup == NULL || decode == NULL || accepted_bytes == NULL || candidate == NULL ||
      instruction == NULL || state == NULL ||
      !instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata) ||
      metadata == NULL || instruction->size_suffix != 'l' ||
      metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
      !operand_address_register_index_local(&instruction->operands[source_index], &source_reg) ||
      !asm_candidate_operand_absolute_value(candidate, dest_index, &dest_address)) {
    return 0;
  }
  platform_kind = (uint8_t)(lookup->object != NULL ?
    lookup->object->platform_backend_kind : M68K_PLATFORM_BACKEND_UNKNOWN);
  data_class = platform_facts_v2_runtime_address_sink_data_class(platform_kind, dest_address);
  if (data_class == NULL || strcmp(data_class, "sound_sample") != 0 ||
      source_reg >= 8U || !state->addr_regs[source_reg].known) {
    return 0;
  }
  value = &state->addr_regs[source_reg];
  if (value->section_index >= decode->section_count || value->offset >= decode->sections[value->section_index].size ||
      accepted_range_has_code_byte(accepted_bytes[value->section_index], decode->sections[value->section_index].size,
        value->offset, 1U)) {
    return 0;
  }
  (void)format_lookup_asm_label_with_generation(lookup, label, sizeof(label), value->section_index, value->offset);
  if (value->dynamic_offset_known && value->dynamic_offset_section_index < decode->section_count &&
      value->dynamic_offset_offset < decode->sections[value->dynamic_offset_section_index].size &&
      !accepted_range_has_code_byte(accepted_bytes[value->dynamic_offset_section_index],
        decode->sections[value->dynamic_offset_section_index].size, value->dynamic_offset_offset, 2U)) {
    format_pointer_source_label(lookup, table_label, sizeof(table_label), value->dynamic_offset_section_index,
      value->dynamic_offset_offset);
    snprintf(comment, sizeof(comment), "source %s + dynamic offset from %s", label, table_label);
  } else {
    snprintf(comment, sizeof(comment), "source %s%s", label, value->exact ? "" : " + dynamic offset");
  }
  return render_lookup_add_instruction_comment(lookup, section_index, candidate->offset, comment);
}

static void audio_length_sources_update_after_instruction(M68kRenderAudioLengthSource sources[8],
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  size_t source_index = 0U, dest_index = 0U, operand_index;
  uint8_t dest_reg = 0U;
  uint8_t source_base_reg = 0U;
  int16_t source_displacement = 0;
  if (sources == NULL || instruction == NULL) return;
  if (instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata) &&
      metadata != NULL && metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
      instruction->size_suffix == 'w' &&
      operand_is_data_register_local(&instruction->operands[dest_index], &dest_reg) &&
      operand_is_address_displacement_local(&instruction->operands[source_index], &source_base_reg,
        &source_displacement)) {
    sources[dest_reg].known = 1U;
    sources[dest_reg].base_reg = source_base_reg;
    sources[dest_reg].displacement = source_displacement;
    sources[dest_reg].transformed = 0U;
    return;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) {
    audio_length_sources_clear(sources);
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE ||
        !operand_is_data_register_local(&instruction->operands[operand_index], &reg)) {
      continue;
    }
    if (sources[reg].known && instruction->operand_count > 1U &&
        metadata->operand_access_kinds[0] == M68K_SIM_ACCESS_IMMEDIATE) {
      sources[reg].transformed = 1U;
    } else {
      memset(&sources[reg], 0, sizeof(sources[reg]));
    }
  }
  (void)candidate;
}

static void audio_period_sources_update_after_instruction(M68kRenderAudioPeriodSource sources[8],
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  size_t source_index = 0U, dest_index = 0U, operand_index;
  size_t table_section_index = 0U;
  uint32_t table_offset = 0U;
  uint8_t dest_reg = 0U;
  if (sources == NULL || instruction == NULL) return;
  if (instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata) &&
      metadata != NULL && metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
      instruction->size_suffix == 'w' && operand_is_data_register_local(&instruction->operands[dest_index],
        &dest_reg) && candidate_data_target_for_operand(candidate, (uint32_t)source_index,
        &table_section_index, &table_offset)) {
    sources[dest_reg].known = 1U;
    sources[dest_reg].transformed = 0U;
    sources[dest_reg].section_index = table_section_index;
    sources[dest_reg].offset = table_offset;
    return;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) {
    audio_period_sources_clear(sources);
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE ||
        !operand_is_data_register_local(&instruction->operands[operand_index], &reg)) {
      continue;
    }
    if (sources[reg].known && instruction->operand_count > 1U &&
        metadata->operand_access_kinds[0] == M68K_SIM_ACCESS_IMMEDIATE) {
      sources[reg].transformed = 1U;
    } else {
      memset(&sources[reg], 0, sizeof(sources[reg]));
    }
  }
}

static int render_lookup_infer_amiga_audio_length_sources(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, uint8_t **accepted_bytes) {
  M68kRenderAudioLengthSource sources[8];
  M68kRenderAudioPeriodSource period_sources[8];
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderDataPointerState data_state;
    size_t candidate_index;
    audio_length_sources_clear(sources);
    audio_period_sources_clear(period_sources);
    data_pointer_state_clear_all(&data_state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      uint8_t source_reg = 0U;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      if (audio_length_write_source_reg(candidate, &instruction, &source_reg) && source_reg < 8U &&
          sources[source_reg].known &&
          render_lookup_add_audio_length_source_comment(lookup, section_index, candidate->offset,
            &sources[source_reg]) != 0) {
        return -1;
      }
      if (audio_period_write_source_reg(candidate, &instruction, &source_reg) && source_reg < 8U &&
          period_sources[source_reg].known &&
          render_lookup_add_audio_period_source_comment(lookup, section_index, candidate->offset,
            &period_sources[source_reg]) != 0) {
        return -1;
      }
      if (render_lookup_add_audio_pointer_source_comment(lookup, decode, accepted_bytes, section_index,
          candidate, &instruction, &data_state) != 0) {
        return -1;
      }
      audio_length_sources_update_after_instruction(sources, candidate, &instruction);
      audio_period_sources_update_after_instruction(period_sources, candidate, &instruction);
      data_pointer_state_update_after_instruction_ex(&data_state, lookup, section, candidate, &instruction, 1U);
    }
  }
  return 0;
}

static int candidate_immediate_audio_length_bytes(const M68kDecodeCandidate *candidate,
    const char *audio_register_symbol, uint32_t *out_size) {
  M68kInstructionIR instruction;
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  uint32_t immediate = 0U;
  uint32_t dest_address = 0U;
  if (out_size != NULL) *out_size = 0U;
  if (candidate == NULL || audio_register_symbol == NULL || out_size == NULL ||
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'w' ||
      candidate->operand_count != 2U) {
    return 0;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      !operand_is_immediate_value_local(&instruction.operands[0], &immediate) ||
      !asm_candidate_operand_absolute_value(candidate, 1U, &dest_address)) {
    return 0;
  }
  hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(dest_address);
  if (hardware_field == NULL || hardware_field->register_symbol == NULL || hardware_field->field_symbol == NULL ||
      strcmp(hardware_field->register_symbol, audio_register_symbol) != 0 ||
      strcmp(hardware_field->field_symbol, "ac_len") != 0) {
    return 0;
  }
  *out_size = (immediate & 0xFFFFU) * 2U;
  return *out_size != 0U;
}

static uint32_t sound_sample_size_from_nearby_audio_length_write(const M68kDecodeIR *decode,
    uint8_t **accepted_start, const M68kFact *fact, uint32_t sink_address) {
  const M68kDecodeSectionIR *section;
  const M68kDecodeCandidate *pointer_candidate;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  uint32_t cursor;
  uint8_t step;
  if (decode == NULL || accepted_start == NULL || fact == NULL || fact->section_index >= decode->section_count)
    return 0U;
  hardware_register = amiga_os_find_hardware_register_by_cpu_address(sink_address);
  if (hardware_register == NULL || hardware_register->symbol_name == NULL ||
      hardware_register->runtime_target_role == NULL ||
      strcmp(hardware_register->runtime_target_role, "sound_sample") != 0) {
    return 0U;
  }
  section = &decode->sections[fact->section_index];
  pointer_candidate = find_candidate_at_offset_local(section, fact->offset);
  if (pointer_candidate == NULL || pointer_candidate->byte_count == 0U) return 0U;
  cursor = pointer_candidate->offset + pointer_candidate->byte_count;
  for (step = 0U; step < 4U && cursor < section->size &&
       accepted_start_at(section, accepted_start[fact->section_index], cursor); ++step) {
    const M68kDecodeCandidate *candidate = find_candidate_at_offset_local(section, cursor);
    uint32_t size = 0U;
    if (candidate == NULL || candidate->byte_count == 0U) return 0U;
    if (candidate_immediate_audio_length_bytes(candidate, hardware_register->symbol_name, &size)) return size;
    cursor += candidate->byte_count;
  }
  return 0U;
}

static int render_lookup_infer_platform_runtime_structured_data(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  size_t index;
  if (lookup == NULL || decode == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_refs[index].fact;
    const char *data_class = runtime_address_ref_data_class(lookup, decode, fact);
    uint32_t sink_address = 0U;
    uint32_t size = 0U;
    uint8_t kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
    if (fact == NULL || data_class == NULL || fact->target_section_index >= decode->section_count) continue;
    if (strcmp(data_class, "copper_list") == 0) {
      size = copper_list_size_at(&decode->sections[fact->target_section_index], fact->target_offset);
      if (size != 0U) {
        char layout_comment[128];
        char setup_comment[192];
        M68kRenderDisplaySetup display_setup;
        if (format_copper_display_layout_comment(&decode->sections[fact->target_section_index],
            fact->target_offset, size, layout_comment, sizeof(layout_comment)) &&
            render_lookup_add_instruction_comment(lookup, fact->target_section_index, fact->target_offset,
              layout_comment) != 0) {
          return -1;
        }
        if (accepted_start != NULL && fact->section_index < decode->section_count &&
            collect_display_setup_before_offset(&decode->sections[fact->section_index],
              accepted_start[fact->section_index], fact->offset, &display_setup) &&
            format_display_setup_comment(&display_setup, setup_comment, sizeof(setup_comment)) &&
            render_lookup_add_instruction_comment(lookup, fact->target_section_index, fact->target_offset,
              setup_comment) != 0) {
          return -1;
        }
        if (render_lookup_add_copper_bitmap_runtime_refs(lookup, &decode->sections[fact->target_section_index],
            fact->target_offset, size) != 0) {
          return -1;
        }
      }
    } else if (accepted_start != NULL && strcmp(data_class, "sound_sample") == 0 &&
        runtime_address_ref_sink_address(decode, fact, &sink_address)) {
      size = sound_sample_size_from_nearby_audio_length_write(decode, accepted_start, fact, sink_address);
      kind = M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
    }
    if (size == 0U) continue;
    if (render_lookup_add_auto_structured_data_item(lookup, fact->target_section_index, fact->target_offset,
        size, data_class, kind) != 0) {
      return -1;
    }
  }
  return 0;
}

#define M68K_RENDER_LOOKUP_AMIGA_COLOR_REGISTER_BYTES 64U

static int operand_is_address_postincrement_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_EA ||
      operand->value.ea_mode != 3U || operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = operand->value.ea_reg;
  return 1;
}

static void hardware_range_pointer_state_clear_all(M68kRenderHardwareRangePointerState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void hardware_range_pointer_state_clear_reg(M68kRenderHardwareRangePointerState *state, uint8_t reg) {
  if (state == NULL || reg >= 8U) return;
  memset(&state->addr_regs[reg], 0, sizeof(state->addr_regs[reg]));
}

static int instruction_loads_hardware_range_to_address_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, const AmigaOsHardwareRegisterRangeInfo **out_range,
    uint32_t *out_range_offset, uint8_t *out_reg) {
  const AmigaOsHardwareRegisterRangeInfo *range;
  uint32_t absolute = 0U;
  uint8_t dest_reg = 0U;
  if (out_range != NULL) *out_range = NULL;
  if (out_range_offset != NULL) *out_range_offset = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_range == NULL || out_range_offset == NULL ||
      out_reg == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg) ||
      !asm_candidate_operand_absolute_value(candidate, 0U, &absolute)) {
    return 0;
  }
  range = amiga_os_find_hardware_register_range_by_cpu_address(absolute);
  if (range == NULL) return 0;
  *out_range = range;
  *out_range_offset = absolute - range->base_address - range->offset;
  *out_reg = dest_reg;
  return 1;
}

static void hardware_range_pointer_state_update_after_instruction(M68kRenderHardwareRangePointerState *state,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  const AmigaOsHardwareRegisterRangeInfo *range = NULL;
  uint32_t range_offset = 0U;
  uint8_t dest_reg = 0U;
  size_t operand_index;
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_BSR) {
    hardware_range_pointer_state_clear_all(state);
    return;
  }
  if (instruction_loads_hardware_range_to_address_reg(candidate, instruction, &range, &range_offset, &dest_reg)) {
    state->addr_regs[dest_reg].known = 1U;
    state->addr_regs[dest_reg].range = range;
    state->addr_regs[dest_reg].offset = range_offset;
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    uint8_t bit;
    for (bit = 0U; bit < 8U; ++bit) {
      if ((instruction->operands[1].value.value & (1UL << (8U + bit))) != 0U)
        hardware_range_pointer_state_clear_reg(state, bit);
    }
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
    if (operand_address_register_index_local(operand, &dest_reg))
      hardware_range_pointer_state_clear_reg(state, dest_reg);
  }
}

static uint32_t palette_source_span(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_bytes, uint32_t offset, uint32_t max_size) {
  uint32_t cursor;
  if (lookup == NULL || section == NULL || accepted_bytes == NULL ||
      offset >= section->size || max_size < 2U) {
    return 0U;
  }
  cursor = offset;
  while (cursor + 2U <= section->size && cursor - offset < max_size) {
    if (cursor != offset && (lookup_has_label(lookup, section->section_index, cursor) ||
        lookup_structured_data_item_covering_offset(lookup, section->section_index, cursor) != NULL)) {
      break;
    }
    if (accepted_range_has_code_byte(accepted_bytes, section->size, cursor, 2U)) break;
    cursor += 2U;
  }
  return cursor - offset;
}

static int render_lookup_maybe_classify_palette_upload(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    const M68kDecodeSectionIR *section, uint8_t **accepted_bytes, const M68kRenderDataPointerState *data_state,
    const M68kRenderHardwareRangePointerState *hardware_state, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  const M68kRenderDataPointerValue *source_value;
  const M68kRenderHardwareRangePointer *dest_value;
  uint8_t source_reg = 0U;
  uint8_t dest_reg = 0U;
  uint32_t available_register_bytes;
  uint32_t size;
  char comment[96];
  if (lookup == NULL || decode == NULL || section == NULL || accepted_bytes == NULL || data_state == NULL ||
      hardware_state == NULL || candidate == NULL || instruction == NULL ||
      instruction->size_suffix != 'w' || instruction->operand_count != 2U ||
      !operand_is_address_postincrement_local(&instruction->operands[0], &source_reg) ||
      !operand_is_address_postincrement_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL ||
      metadata->operand_access_kinds[0] != M68K_SIM_ACCESS_MEMORY_READ ||
      metadata->operand_access_kinds[1] != M68K_SIM_ACCESS_MEMORY_WRITE) {
    return 0;
  }
  source_value = &data_state->addr_regs[source_reg];
  dest_value = &hardware_state->addr_regs[dest_reg];
  if (!source_value->known || !source_value->exact || !dest_value->known || dest_value->range == NULL ||
      dest_value->range->symbol_name == NULL || strcmp(dest_value->range->symbol_name, "color") != 0 ||
      source_value->section_index >= decode->section_count ||
      accepted_bytes[source_value->section_index] == NULL ||
      source_value->offset >= decode->sections[source_value->section_index].size ||
      dest_value->offset >= M68K_RENDER_LOOKUP_AMIGA_COLOR_REGISTER_BYTES) {
    return 0;
  }
  available_register_bytes = M68K_RENDER_LOOKUP_AMIGA_COLOR_REGISTER_BYTES - dest_value->offset;
  size = palette_source_span(lookup, &decode->sections[source_value->section_index],
    accepted_bytes[source_value->section_index], source_value->offset, available_register_bytes);
  if (size < 4U || size != available_register_bytes) return 0;
  if (render_lookup_add_auto_structured_data_item(lookup, source_value->section_index, source_value->offset,
      size, "palette", M68K_ANALYSIS_STRUCTURED_DATA_WORDS) != 0) {
    return -1;
  }
  snprintf(comment, sizeof(comment), "palette upload %u colors", (unsigned)(size / 2U));
  return render_lookup_add_instruction_comment(lookup, section->section_index, candidate->offset, comment);
}

static int render_lookup_infer_amiga_palette_uploads(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, uint8_t **accepted_bytes) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderDataPointerState data_state;
    M68kRenderHardwareRangePointerState hardware_state;
    size_t candidate_index;
    data_pointer_state_clear_all(&data_state);
    hardware_range_pointer_state_clear_all(&hardware_state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      if (render_lookup_maybe_classify_palette_upload(lookup, decode, section, accepted_bytes,
          &data_state, &hardware_state, candidate, &instruction) != 0) {
        return -1;
      }
      data_pointer_state_update_after_instruction(&data_state, lookup, section, candidate, &instruction);
      hardware_range_pointer_state_update_after_instruction(&hardware_state, candidate, &instruction);
    }
  }
  return 0;
}

static int accepted_range_has_code_byte(const uint8_t *accepted_bytes, uint32_t section_size,
    uint32_t offset, uint32_t size) {
  uint32_t cursor;
  if (accepted_bytes == NULL || offset > section_size || size > section_size - offset) return 1;
  for (cursor = 0U; cursor < size; ++cursor) {
    if (accepted_bytes[offset + cursor] != 0U) return 1;
  }
  return 0;
}

static int relocation_is_data_pointer_long(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_bytes, size_t section_index, uint32_t offset) {
  const M68kFact *relocation;
  if (lookup == NULL || decode == NULL || accepted_bytes == NULL || section_index >= decode->section_count)
    return 0;
  if (accepted_range_has_code_byte(accepted_bytes[section_index], decode->sections[section_index].size, offset, 4U))
    return 0;
  relocation = lookup_relocation_at(lookup, section_index, offset);
  return relocation != NULL && relocation->size == 4U && relocation->target_section_index < decode->section_count;
}

static int render_lookup_infer_relocation_pointer_tables(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_bytes) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_bytes == NULL) return 0;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    uint32_t offset = 0U;
    while (offset + 8U <= section->size) {
      uint32_t start = offset;
      uint32_t cursor = offset;
      while (cursor + 4U <= section->size &&
          relocation_is_data_pointer_long(lookup, decode, accepted_bytes, section_index, cursor)) {
        cursor += 4U;
      }
      if (cursor - start >= 8U) {
        if (render_lookup_add_auto_structured_data_item(lookup, section_index, start, cursor - start,
            "pointer_table", M68K_ANALYSIS_STRUCTURED_DATA_LONGS) != 0) {
          return -1;
        }
        offset = cursor;
      } else {
        offset += 2U;
      }
    }
  }
  return 0;
}

static int structured_data_kind_for_candidate_size(const M68kDecodeCandidate *candidate, uint32_t *out_size,
    uint8_t *out_kind) {
  if (out_size != NULL) *out_size = 0U;
  if (out_kind != NULL) *out_kind = 0U;
  if (candidate == NULL || out_size == NULL || out_kind == NULL) return 0;
  if (candidate->size_suffix == 'b') {
    *out_size = 1U;
    *out_kind = M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
    return 1;
  }
  if (candidate->size_suffix == 'w') {
    *out_size = 2U;
    *out_kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
    return 1;
  }
  if (candidate->size_suffix == 'l') {
    *out_size = 4U;
    *out_kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
    return 1;
  }
  return 0;
}

#define M68K_RENDER_LOOKUP_PC_INDEX_TABLE_MAX_SPAN 64U
#define M68K_RENDER_LOOKUP_WORD_DISPATCH_LOCAL_LIMIT 0x1000
#define M68K_RENDER_LOOKUP_WORD_DISPATCH_SLOT_LIMIT 32U

static uint32_t pc_relative_lookup_table_span(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset,
    uint32_t item_size) {
  uint32_t cursor;
  if (lookup == NULL || section == NULL || accepted_bytes == NULL || item_size == 0U ||
      offset > section->size || item_size > section->size - offset) {
    return 0U;
  }
  cursor = offset + item_size;
  while (cursor + item_size <= section->size &&
      cursor - offset < M68K_RENDER_LOOKUP_PC_INDEX_TABLE_MAX_SPAN &&
      !lookup_has_label(lookup, section->section_index, cursor) &&
      lookup_structured_data_item_covering_offset(lookup, section->section_index, cursor) == NULL &&
      !accepted_range_has_code_byte(accepted_bytes, section->size, cursor, item_size)) {
    cursor += item_size;
  }
  return cursor - offset;
}

static int dispatch_pointer_loads_local_address(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  size_t target_index;
  uint8_t dest_reg = 0U;
  uint32_t absolute_offset = 0U;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (section == NULL || candidate == NULL || instruction == NULL || out_section_index == NULL ||
      out_offset == NULL || out_reg == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA ||
      instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_DATA || target->has_section == 0U ||
        target->has_operand == 0U || target->operand_index != 0U) {
      continue;
    }
    *out_section_index = target->section_index;
    *out_offset = target->offset;
    *out_reg = dest_reg;
    return 1;
  }
  if (lookup != NULL) {
    size_t runtime_ref_index;
    for (runtime_ref_index = lookup->runtime_address_ref_count; runtime_ref_index > 0U; --runtime_ref_index) {
      const M68kFact *fact = lookup->runtime_address_refs[runtime_ref_index - 1U].fact;
      if (fact == NULL || fact->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
          fact->section_index != section->section_index || fact->offset != candidate->offset ||
          fact->reason != 0U || !fact->has_runtime_address ||
          fact->target_section_index >= lookup->section_count) {
        continue;
      }
      *out_section_index = fact->target_section_index;
      *out_offset = fact->target_offset;
      *out_reg = dest_reg;
      return 1;
    }
  }
  if (lookup != NULL && candidate->byte_count <= section->size &&
      candidate->offset <= section->size - candidate->byte_count) {
    uint32_t relocation_offset;
    uint32_t relocation_end;
    relocation_end = candidate->offset + candidate->byte_count;
    for (relocation_offset = candidate->offset + 2U; relocation_offset < relocation_end; ++relocation_offset) {
      const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, relocation_offset);
      if (relocation == NULL || relocation->size != 4U) continue;
      *out_section_index = relocation->target_section_index;
      *out_offset = relocation->target_offset;
      *out_reg = dest_reg;
      return 1;
    }
  }
  if (operand_absolute_offset_local(&instruction->operands[0], &absolute_offset) &&
      absolute_offset < section->size) {
    *out_section_index = section->section_index;
    *out_offset = absolute_offset;
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static void dispatch_pointer_state_update_after_instruction(M68kRenderDataPointerState *state,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction) {
  const M68kRenderDataPointerValue *source_value = NULL;
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  uint8_t dest_reg = 0U;
  size_t operand_index;
  const M68kSimFormMetadata *metadata;
  if (state == NULL || section == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata != NULL &&
      (metadata->flow_kind == M68K_SIM_FLOW_CALL || metadata->flow_kind == M68K_SIM_FLOW_JUMP)) {
    data_pointer_state_clear_all(state);
    return;
  }
  if (dispatch_pointer_loads_local_address(lookup, section, candidate, instruction, &target_section_index,
      &target_offset, &dest_reg)) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, target_section_index, target_offset);
    return;
  }
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->operand_count == 2U) {
    source_value = data_pointer_state_value_for_operand(state, &instruction->operands[0]);
    if (operand_is_data_register_local(&instruction->operands[1], &dest_reg)) {
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg);
      if (source_value != NULL)
        data_pointer_state_copy_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg, source_value);
      return;
    }
    if (operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg);
      if (source_value != NULL)
        data_pointer_state_copy_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, source_value);
      return;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    uint8_t bit;
    for (bit = 0U; bit < 8U; ++bit) {
      if ((instruction->operands[1].value.value & (1UL << bit)) != 0U)
        data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, bit);
      if ((instruction->operands[1].value.value & (1UL << (8U + bit))) != 0U)
        data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, bit);
    }
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
    if (operand_is_data_register_local(operand, &dest_reg))
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg);
    else if (operand_address_register_index_local(operand, &dest_reg))
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg);
  }
}

static int candidate_next_is_indirect_control_through_addr_reg(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate, uint8_t reg) {
  const M68kDecodeCandidate *next_candidate;
  M68kInstructionIR next_instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index = 0U;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint32_t next_offset;
  if (section == NULL || accepted_start == NULL || candidate == NULL || reg >= 8U ||
      candidate->byte_count > section->size || candidate->offset > section->size - candidate->byte_count) {
    return 0;
  }
  next_offset = candidate->offset + candidate->byte_count;
  if (next_offset >= section->size || !accepted_start[next_offset]) return 0;
  next_candidate = find_candidate_at_offset_local(section, next_offset);
  if (next_candidate == NULL || m68k_decode_candidate_to_instruction(next_candidate, &next_instruction) != 0)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(&next_instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_JUMP && metadata->flow_kind != M68K_SIM_FLOW_CALL)) {
    return 0;
  }
  if (metadata->target_operand_index < next_instruction.operand_count)
    operand_index = metadata->target_operand_index;
  if (operand_index >= next_instruction.operand_count) return 0;
  return operand_is_address_memory_local(&next_instruction.operands[operand_index], &base_reg,
    &displacement) && base_reg == reg && displacement == 0;
}

static uint32_t scan_indexed_word_dispatch_table_span(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, uint8_t **accepted_bytes,
    size_t table_section_index, uint32_t table_offset, size_t base_section_index, uint32_t base_offset) {
  const M68kDecodeSectionIR *table_section;
  const M68kDecodeSectionIR *base_section;
  uint32_t cursor;
  uint32_t target_count = 0U;
  uint32_t first_forward_target = UINT32_MAX;
  uint8_t saw_unaccepted_target = 0U;
  uint8_t stopped_at_boundary = 0U;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      table_section_index >= decode->section_count || base_section_index >= decode->section_count) {
    return 0U;
  }
  table_section = &decode->sections[table_section_index];
  base_section = &decode->sections[base_section_index];
  if (table_section->data == NULL || table_offset >= table_section->size ||
      base_offset >= base_section->size || accepted_start[base_section_index] == NULL ||
      accepted_bytes[table_section_index] == NULL) {
    return 0U;
  }
  for (cursor = table_offset; cursor + 2U <= table_section->size; cursor += 2U) {
    int32_t displacement;
    int64_t target64;
    if (cursor != table_offset && lookup_has_label(lookup, table_section_index, cursor)) {
      stopped_at_boundary = 1U;
      break;
    }
    if (accepted_range_has_code_byte(accepted_bytes[table_section_index], table_section->size, cursor, 2U))
      break;
    displacement = (int32_t)(int16_t)m68k_read_u16be(table_section->data + cursor);
    target64 = (int64_t)(uint64_t)base_offset + (int64_t)displacement;
    if (displacement < -M68K_RENDER_LOOKUP_WORD_DISPATCH_LOCAL_LIMIT ||
        displacement > M68K_RENDER_LOOKUP_WORD_DISPATCH_LOCAL_LIMIT) break;
    if (target64 < 0 || target64 >= (int64_t)(uint64_t)base_section->size ||
        ((uint32_t)target64 & 1U) != 0U) {
      break;
    }
    if (!accepted_start[base_section_index][(uint32_t)target64]) saw_unaccepted_target = 1U;
    ++target_count;
    if (table_section_index == base_section_index && (uint32_t)target64 > table_offset &&
        (uint32_t)target64 < first_forward_target) {
      first_forward_target = (uint32_t)target64;
    }
    if (target_count >= 2U && first_forward_target != UINT32_MAX && cursor + 2U >= first_forward_target) {
      stopped_at_boundary = 1U;
      break;
    }
    if (target_count >= M68K_RENDER_LOOKUP_WORD_DISPATCH_SLOT_LIMIT) break;
  }
  if (target_count < 2U) return 0U;
  if (!saw_unaccepted_target || stopped_at_boundary) return target_count * 2U;
  return 0U;
}

static int candidate_adds_indexed_word_table_to_address_reg(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    const M68kRenderDataPointerState *state, size_t *out_table_section_index, uint32_t *out_table_offset,
    size_t *out_base_section_index, uint32_t *out_base_offset, uint8_t *out_dest_reg) {
  const M68kSimFormMetadata *metadata;
  size_t source_index = (size_t)-1;
  size_t dest_index = (size_t)-1;
  size_t operand_index;
  uint8_t dest_reg = 0U;
  if (out_table_section_index != NULL) *out_table_section_index = 0U;
  if (out_table_offset != NULL) *out_table_offset = 0U;
  if (out_base_section_index != NULL) *out_base_section_index = 0U;
  if (out_base_offset != NULL) *out_base_offset = 0U;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (section == NULL || candidate == NULL || instruction == NULL || state == NULL ||
      out_table_section_index == NULL || out_table_offset == NULL || out_base_section_index == NULL ||
      out_base_offset == NULL || out_dest_reg == NULL || candidate->size_suffix != 'w') {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_ADD) return 0;
  if (metadata->source_operand_index < candidate->operand_count) source_index = metadata->source_operand_index;
  if (metadata->dest_operand_index < candidate->operand_count) dest_index = metadata->dest_operand_index;
  if (source_index < candidate->operand_count && source_index < instruction->operand_count && source_index < 4U &&
      !((metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
         metadata->operand_ea_uses_index[source_index]) ||
        metadata->operand_ea_address_shapes[source_index] == M68K_SIM_EA_SHAPE_INDEX ||
        m68k_instruction_operand_decoded_ea_shape(&instruction->operands[source_index]) ==
          M68K_SIM_EA_SHAPE_INDEX)) {
    source_index = (size_t)-1;
  }
  if (dest_index < instruction->operand_count &&
      !operand_address_register_index_local(&instruction->operands[dest_index], NULL)) {
    dest_index = (size_t)-1;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    if (source_index == (size_t)-1 &&
        ((metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_READ &&
          metadata->operand_ea_uses_index[operand_index]) ||
         metadata->operand_ea_address_shapes[operand_index] == M68K_SIM_EA_SHAPE_INDEX ||
         (operand_index < instruction->operand_count &&
          m68k_instruction_operand_decoded_ea_shape(&instruction->operands[operand_index]) ==
            M68K_SIM_EA_SHAPE_INDEX))) {
      source_index = operand_index;
    }
    if (dest_index == (size_t)-1 &&
        metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        operand_address_register_index_local(&instruction->operands[operand_index], &dest_reg)) {
      dest_index = operand_index;
    }
  }
  if (source_index >= candidate->operand_count || dest_index >= instruction->operand_count ||
      source_index >= instruction->operand_count || source_index >= 4U) {
    return 0;
  }
  if (!operand_address_register_index_local(&instruction->operands[dest_index], &dest_reg) || dest_reg >= 8U)
    return 0;
  if (!((metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        metadata->operand_ea_uses_index[source_index]) ||
       metadata->operand_ea_address_shapes[source_index] == M68K_SIM_EA_SHAPE_INDEX ||
       m68k_instruction_operand_decoded_ea_shape(&instruction->operands[source_index]) ==
         M68K_SIM_EA_SHAPE_INDEX)) {
    return 0;
  }
  {
    const M68kOperandIR *source_operand = &instruction->operands[source_index];
    const M68kRenderDataPointerValue *table_base;
    const M68kRenderDataPointerValue *target_base = &state->addr_regs[dest_reg];
    uint8_t source_reg;
    uint32_t displacement;
    if (source_operand->kind != M68K_ASM_OPERAND_EA || source_operand->value.ea_reg >= 8U) return 0;
    source_reg = source_operand->value.ea_reg;
    table_base = &state->addr_regs[source_reg];
    if (!table_base->known || !target_base->known) return 0;
    displacement = source_operand->value.value;
    if (table_base->offset > UINT32_MAX - displacement) return 0;
    *out_table_section_index = table_base->section_index;
    *out_table_offset = table_base->offset + displacement;
    *out_base_section_index = target_base->section_index;
    *out_base_offset = target_base->offset;
  }
  *out_dest_reg = dest_reg;
  return 1;
}

static int render_lookup_infer_indexed_word_dispatch_tables(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, uint8_t **accepted_bytes) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL) return 0;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderDataPointerState state;
    size_t candidate_index;
    data_pointer_state_clear_all(&state);
    if (accepted_start[section_index] == NULL) return -1;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      {
        size_t sections[2] = {0U, 0U};
        uint32_t offsets[2] = {0U, 0U};
        uint32_t table_size = 0U;
        uint8_t dest_reg = 0U;
        int adds_dispatch = candidate_adds_indexed_word_table_to_address_reg(section, candidate, &instruction, &state,
          &sections[0], &offsets[0], &sections[1], &offsets[1], &dest_reg);
        int next_dispatch = adds_dispatch ? candidate_next_is_indirect_control_through_addr_reg(section,
          accepted_start[section_index], candidate, dest_reg) : 0;
        if (adds_dispatch && next_dispatch) {
          table_size = scan_indexed_word_dispatch_table_span(lookup, decode, accepted_start, accepted_bytes,
            sections[0], offsets[0], sections[1], offsets[1]);
          if (table_size != 0U &&
              render_lookup_add_auto_structured_data_item(lookup, sections[0], offsets[0], table_size,
                "lookup_table", M68K_ANALYSIS_STRUCTURED_DATA_WORDS) != 0) {
            return -1;
          }
        }
      }
      dispatch_pointer_state_update_after_instruction(&state, lookup, section, candidate, &instruction);
    }
  }
  return 0;
}

static int render_lookup_infer_pc_relative_lookup_scalars(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, uint8_t **accepted_bytes) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL) return 0;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    if (accepted_start[section_index] == NULL || accepted_bytes[section_index] == NULL) return -1;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const M68kSimFormMetadata *metadata;
      size_t target_index;
      uint32_t item_size = 0U;
      uint8_t item_kind = 0U;
      if (!accepted_start[section_index][candidate->offset]) continue;
      if (!structured_data_kind_for_candidate_size(candidate, &item_size, &item_kind)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      metadata = m68k_sim_metadata_for_instruction(&instruction);
      if (metadata == NULL) continue;
      for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
        const M68kDecodeTarget *target = &candidate->targets[target_index];
        const M68kOperandIR *operand;
        uint8_t shape;
        if (target->kind != M68K_DECODE_TARGET_DATA || !target->has_section || !target->has_operand ||
            target->section_index >= decode->section_count || target->operand_index >= instruction.operand_count ||
            target->operand_index >= 4U) {
          continue;
        }
        operand = &instruction.operands[target->operand_index];
        shape = m68k_instruction_operand_decoded_ea_shape(operand);
        if (m68k_instruction_decoded_ea_target_kind(operand, shape, 1) != 2U) continue;
        if (metadata->operand_access_kinds[target->operand_index] != M68K_SIM_ACCESS_MEMORY_READ) continue;
        if (accepted_range_has_code_byte(accepted_bytes[target->section_index],
            decode->sections[target->section_index].size, target->offset, item_size)) {
          continue;
        }
        if (render_lookup_add_auto_structured_data_item(lookup, target->section_index, target->offset,
            pc_relative_lookup_table_span(lookup, &decode->sections[target->section_index],
              accepted_bytes[target->section_index], target->offset, item_size),
            "lookup_table", item_kind) != 0) {
          return -1;
        }
      }
    }
  }
  return 0;
}

static int source_analysis_append_auto_structured_data_policy(M68kSourceAnalysisIR *source_analysis,
    const M68kRenderLookup *lookup) {
  size_t index;
  if (source_analysis == NULL || lookup == NULL) return 0;
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    M68kAnalysisPolicy *policy = &source_analysis->policy;
    if (policy->structured_data_item_count >= M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT) return -1;
    policy->structured_data_items[policy->structured_data_item_count++] =
      lookup->auto_structured_data_items[index];
  }
  return 0;
}

static void trace_reg_set(M68kRenderTraceRegName *reg, const char *name) {
  if (reg == NULL || name == NULL || name[0] == '\0') return;
  reg->known = 1U;
  snprintf(reg->name, sizeof(reg->name), "%s", name);
}

static void trace_reg_clear(M68kRenderTraceRegName *reg) {
  if (reg == NULL) return;
  reg->known = 0U;
  reg->name[0] = '\0';
}

static void trace_addr_reg_set_name(M68kRenderBaseTraceState *state, uint8_t reg, const char *name) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_set(&state->addr_regs[reg], name);
  state->app_addresses[reg].known = 0U;
  state->app_addresses[reg].displacement = 0;
}

static void trace_addr_reg_clear(M68kRenderBaseTraceState *state, uint8_t reg) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_clear(&state->addr_regs[reg]);
  state->app_addresses[reg].known = 0U;
  state->app_addresses[reg].displacement = 0;
}

static void trace_addr_reg_set_app_address(M68kRenderBaseTraceState *state, uint8_t reg, int16_t displacement) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_clear(&state->addr_regs[reg]);
  state->app_addresses[reg].known = 1U;
  state->app_addresses[reg].displacement = displacement;
}

static void trace_state_reset(M68kRenderBaseTraceState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void trace_state_apply_policy_register_seeds(M68kRenderBaseTraceState *state,
    const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  uint16_t index;
  if (state == NULL || policy == NULL) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if ((seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE &&
         seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR) ||
        seed->reg_index >= 8U || seed->name[0] == '\0')
      continue;
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if (seed->reg_kind == M68K_ANALYSIS_REGISTER_DATA) trace_reg_set(&state->data_regs[seed->reg_index], seed->name);
    else if (seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS)
      trace_addr_reg_set_name(state, seed->reg_index, seed->name);
  }
}

int operand_is_data_register_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && !operand->value.reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 0U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

int operand_address_register_index_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && operand->value.reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 1U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

int operand_is_address_displacement_local(const M68kOperandIR *operand, uint8_t *out_reg,
    int16_t *out_displacement) {
  if (operand == NULL ||
      (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
      operand->value.ea_mode != 5U || operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = operand->value.ea_reg;
  if (out_displacement != NULL) *out_displacement = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

int operand_is_address_memory_local(const M68kOperandIR *operand, uint8_t *out_reg,
    int16_t *out_displacement) {
  if (operand == NULL ||
      (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
      operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (operand->value.ea_mode == 2U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    if (out_displacement != NULL) *out_displacement = 0;
    return 1;
  }
  return operand_is_address_displacement_local(operand, out_reg, out_displacement);
}

static const char *trace_name_from_operand(const M68kRenderBaseTraceState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg) && state->data_regs[reg].known) return state->data_regs[reg].name;
  if (operand_address_register_index_local(operand, &reg) && state->addr_regs[reg].known)
    return state->addr_regs[reg].name;
  return NULL;
}

static const char *trace_library_from_operand(const M68kRenderBaseTraceState *state,
    const M68kOperandIR *operand) {
  const char *name = trace_name_from_operand(state, operand);
  const char *library_name;
  if (name == NULL || name[0] == '\0') return NULL;
  if (amiga_os_find_library_base_name(name) != NULL) return name;
  library_name = amiga_library_name_from_base_symbol_name(name);
  return library_name != NULL && amiga_os_find_library_base_name(library_name) != NULL ? library_name : NULL;
}

static const char *trace_local_slot_library(const M68kRenderBaseTraceState *state, uint8_t base_reg,
    int16_t displacement);

static const char *trace_known_library_from_operand(const M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *library_name = trace_library_from_operand(state, operand);
  if (library_name != NULL) return library_name;
  if (lookup == NULL || operand == NULL) return NULL;
  if (operand_is_address_displacement_local(operand, &base_reg, &displacement)) {
    library_name = trace_local_slot_library(state, base_reg, displacement);
    if (library_name != NULL && amiga_os_find_library_base_name(library_name) != NULL) return library_name;
    if (state != NULL && state->addr_regs[base_reg].known) {
      library_name = lookup_base_field_slot_library(lookup, state->addr_regs[base_reg].name, displacement);
      if (library_name != NULL) return library_name;
    }
    if (state == NULL || !state->addr_regs[base_reg].known) {
      char owner_name[32];
      if (amiga_unknown_base_register_owner_name(base_reg, owner_name, sizeof(owner_name))) {
        library_name = lookup_base_field_slot_library(lookup, owner_name, displacement);
        if (library_name != NULL) return library_name;
      }
    }
    if (base_reg == 6U && (state == NULL || !state->addr_regs[6].known))
      return lookup_app_base_field_slot_library(lookup, displacement);
  }
  return NULL;
}

static void trace_state_update_register_names_after_candidate(M68kRenderBaseTraceState *state,
    const M68kRenderLookup *lookup, const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const char *source_name;
  const char *source_library;
  uint8_t dest_reg = 0U;
  if (state == NULL || candidate == NULL) return;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) {
    return;
  }
  if (candidate->operand_count != 2U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return;
  source_name = trace_name_from_operand(state, &instruction.operands[0]);
  source_library = trace_known_library_from_operand(lookup, state, &instruction.operands[0]);
  if (operand_is_data_register_local(&instruction.operands[1], &dest_reg)) {
    if (source_name != NULL) trace_reg_set(&state->data_regs[dest_reg], source_name);
    else trace_reg_clear(&state->data_regs[dest_reg]);
  } else if (operand_address_register_index_local(&instruction.operands[1], &dest_reg)) {
    if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && source_library != NULL) {
      trace_addr_reg_set_name(state, dest_reg, source_library);
    } else if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
        operand_is_absolute_address_local(&instruction.operands[0], 4U)) {
      trace_addr_reg_set_name(state, dest_reg, amiga_os_exec_base_library_name());
    } else if (source_name != NULL) trace_addr_reg_set_name(state, dest_reg, source_name);
    else trace_addr_reg_clear(state, dest_reg);
  }
}

static void trace_local_slot_set(M68kRenderBaseTraceState *state, uint8_t base_reg, int16_t displacement,
    const char *library_name) {
  size_t index;
  if (state == NULL || base_reg >= 8U || library_name == NULL || library_name[0] == '\0') return;
  for (index = 0U; index < sizeof(state->local_slots) / sizeof(state->local_slots[0]); ++index) {
    M68kRenderTraceLocalSlot *slot = &state->local_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement) {
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
      return;
    }
  }
  for (index = 0U; index < sizeof(state->local_slots) / sizeof(state->local_slots[0]); ++index) {
    M68kRenderTraceLocalSlot *slot = &state->local_slots[index];
    if (slot->valid) continue;
    slot->valid = 1U;
    slot->base_reg = base_reg;
    slot->displacement = displacement;
    snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
    return;
  }
}

static const char *trace_local_slot_library(const M68kRenderBaseTraceState *state, uint8_t base_reg,
    int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return NULL;
  for (index = 0U; index < sizeof(state->local_slots) / sizeof(state->local_slots[0]); ++index) {
    const M68kRenderTraceLocalSlot *slot = &state->local_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement)
      return slot->library_name;
  }
  return NULL;
}

static int read_library_name_string_at(const M68kDecodeSectionIR *section, uint32_t offset, char *out_name,
    size_t out_size) {
  size_t index = 0U;
  if (section == NULL || section->data == NULL || out_name == NULL || out_size == 0U || offset >= section->size)
    return 0;
  while (offset + index < section->size && index + 1U < out_size) {
    uint8_t value = section->data[offset + index];
    if (value == 0U) {
      out_name[index] = '\0';
      return index != 0U && amiga_os_find_library_base_name(out_name) != NULL;
    }
    if (value < 0x20U || value > 0x7EU) return 0;
    out_name[index++] = (char)value;
  }
  return 0;
}

static int format_lower_symbol_component(const char *text, char *out, size_t out_size) {
  size_t in_index;
  size_t out_index = 0U;
  int previous_sep = 0;
  if (out == NULL || out_size == 0U) return 0;
  out[0] = '\0';
  if (text == NULL || text[0] == '\0') return 0;
  for (in_index = 0U; text[in_index] != '\0'; ++in_index) {
    char ch = text[in_index];
    int is_alnum = (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9');
    if (is_alnum) {
      if (out_index + 1U >= out_size) return 0;
      out[out_index++] = ascii_lower_local(ch);
      previous_sep = 0;
    } else if (out_index != 0U && !previous_sep) {
      if (out_index + 1U >= out_size) return 0;
      out[out_index++] = '_';
      previous_sep = 1;
    }
  }
  while (out_index != 0U && out[out_index - 1U] == '_') --out_index;
  out[out_index] = '\0';
  return out_index != 0U;
}

static int format_app_named_value_slot_symbol(const char *source_name, char *symbol_name, size_t symbol_name_size) {
  char name_part[48];
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  symbol_name[0] = '\0';
  if (source_name == NULL || source_name[0] == '\0') return 0;
  if (strcmp(source_name, "SegList") == 0 || strcmp(source_name, "seglist") == 0) {
    written = snprintf(symbol_name, symbol_name_size, "app_SegList");
    return written > 0 && (size_t)written < symbol_name_size;
  }
  if (!format_lower_symbol_component(source_name, name_part, sizeof(name_part))) return 0;
  written = snprintf(symbol_name, symbol_name_size, "app_%s", name_part);
  return written > 0 && (size_t)written < symbol_name_size;
}

static const AmigaOsCallInputInfo *open_device_iorequest_input_info(void) {
  const AmigaOsLibraryVectorInfo *open_device = amiga_os_find_library_vector_by_symbol_name("_LVOOpenDevice");
  const AmigaOsCallInputInfo *inputs;
  size_t count = 0U;
  size_t index;
  if (open_device == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(open_device, &count);
  if (inputs == NULL) return NULL;
  for (index = 0U; index < count; ++index) {
    const AmigaOsCallInputInfo *input = &inputs[index];
    if (input->reg_kind == AMIGA_OS_REGISTER_ADDRESS && input->reg_index == 1U &&
        input->struct_id == AMIGA_OS_STRUCT_ID_IO) {
      return input;
    }
  }
  return NULL;
}

static int amiga_vector_iorequest_address_register(const AmigaOsLibraryVectorInfo *vector, uint8_t *out_reg) {
  const AmigaOsCallInputInfo *inputs;
  size_t count = 0U;
  size_t index;
  if (out_reg != NULL) *out_reg = 0U;
  if (vector == NULL) return 0;
  inputs = amiga_os_library_vector_inputs(vector, &count);
  if (inputs == NULL) return 0;
  for (index = 0U; index < count; ++index) {
    const AmigaOsCallInputInfo *input = &inputs[index];
    if (input->reg_kind == AMIGA_OS_REGISTER_ADDRESS && input->reg_index < 8U &&
        input->struct_id == AMIGA_OS_STRUCT_ID_IO) {
      if (out_reg != NULL) *out_reg = input->reg_index;
      return 1;
    }
  }
  return 0;
}

static int format_open_device_app_iorequest_slot_name(const char *device_name, char *symbol_name,
    size_t symbol_name_size) {
  const AmigaOsCallInputInfo *input = open_device_iorequest_input_info();
  const char *input_name = input != NULL ? amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id) : NULL;
  char device_part[48];
  char input_part[32];
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  symbol_name[0] = '\0';
  if (!format_lower_symbol_component(device_name, device_part, sizeof(device_part)) ||
      !format_lower_symbol_component(input_name, input_part, sizeof(input_part))) {
    return 0;
  }
  written = snprintf(symbol_name, symbol_name_size, "app_%s_%s", device_part, input_part);
  return written > 0 && (size_t)written < symbol_name_size;
}

int candidate_lea_known_amiga_name_to_address_reg(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint8_t *out_reg, char *out_name, size_t out_size) {
  M68kInstructionIR instruction;
  uint32_t absolute_offset = 0U;
  uint8_t dest_reg = 0U;
  int16_t displacement;
  int64_t target;
  if (section == NULL || candidate == NULL || out_name == NULL || out_size == 0U) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA || candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_address_register_index_local(&instruction.operands[1], &dest_reg)) return 0;
  if (instruction.operands[0].kind == M68K_ASM_OPERAND_EA &&
      instruction.operands[0].value.ea_mode == 7U && instruction.operands[0].value.ea_reg == 2U) {
    displacement = (int16_t)(instruction.operands[0].value.value & 0xFFFFU);
    target = (int64_t)candidate->offset + 2 + displacement;
    if (target < 0 || target > UINT32_MAX) return 0;
    if (!read_library_name_string_at(section, (uint32_t)target, out_name, out_size)) return 0;
    if (out_reg != NULL) *out_reg = dest_reg;
    return 1;
  }
  if (operand_absolute_offset_local(&instruction.operands[0], &absolute_offset)) {
    if (!read_library_name_string_at(section, absolute_offset, out_name, out_size)) return 0;
    if (out_reg != NULL) *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int candidate_lea_app_base_address_to_address_reg(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
    int16_t *out_displacement) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  uint8_t dest_reg = 0U;
  int16_t displacement = 0;
  if (candidate == NULL || out_reg == NULL || out_displacement == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA || candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[0], &base_reg, &displacement) ||
      base_reg != 6U) {
    return 0;
  }
  if (!operand_address_register_index_local(&instruction.operands[1], &dest_reg)) return 0;
  *out_reg = dest_reg;
  *out_displacement = displacement;
  return 1;
}

static int candidate_is_exec_open_library_call(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate) {
  int16_t lvo = 0;
  const AmigaOsLibraryVectorInfo *open_library;
  const AmigaOsLibraryVectorInfo *old_open_library;
  if (state == NULL || !state->addr_regs[6].known) return 0;
  if (strcmp(state->addr_regs[6].name, amiga_os_exec_base_library_name()) != 0) return 0;
  if (!candidate_calls_a6_lvo(candidate, &lvo)) return 0;
  open_library = amiga_os_find_library_vector_by_symbol_name("_LVOOpenLibrary");
  old_open_library = amiga_os_find_library_vector_by_symbol_name("_LVOOldOpenLibrary");
  return (open_library != NULL && open_library->lvo == lvo) ||
    (old_open_library != NULL && old_open_library->lvo == lvo);
}

static int amiga_vector_is_open_library(const AmigaOsLibraryVectorInfo *vector) {
  const char *symbol_name;
  if (vector == NULL) return 0;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  return symbol_name != NULL &&
    (strcmp(symbol_name, "_LVOOpenLibrary") == 0 || strcmp(symbol_name, "_LVOOldOpenLibrary") == 0);
}

static int candidate_is_exec_open_device_call(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate) {
  int16_t lvo = 0;
  const AmigaOsLibraryVectorInfo *open_device;
  if (state == NULL || !state->addr_regs[6].known) return 0;
  if (strcmp(state->addr_regs[6].name, amiga_os_exec_base_library_name()) != 0) return 0;
  if (!candidate_calls_a6_lvo(candidate, &lvo)) return 0;
  open_device = amiga_os_find_library_vector_by_symbol_name("_LVOOpenDevice");
  return open_device != NULL && open_device->lvo == lvo;
}

static int render_lookup_record_device_call_from_iorequest(M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate) {
  int16_t lvo = 0;
  const AmigaOsLibraryVectorInfo *vector;
  const char *base_name;
  uint8_t iorequest_reg = 0U;
  const char *device_name;
  if (lookup == NULL || state == NULL || section == NULL || candidate == NULL) return 0;
  if (!state->addr_regs[6].known || !candidate_calls_a6_lvo(candidate, &lvo)) return 0;
  base_name = amiga_os_find_library_base_name(state->addr_regs[6].name);
  vector = amiga_os_find_library_vector(base_name != NULL ? base_name : state->addr_regs[6].name, lvo);
  if (!amiga_vector_iorequest_address_register(vector, &iorequest_reg)) return 0;
  if (!state->app_addresses[iorequest_reg].known) return 0;
  device_name = render_lookup_device_name_for_iorequest(lookup, state->app_addresses[iorequest_reg].displacement);
  if (device_name == NULL) return 0;
  return render_lookup_add_device_call(lookup, section->section_index, candidate->offset, device_name);
}

static int candidate_stores_library_to_local_slot(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate, uint8_t *out_base_reg, int16_t *out_displacement,
    const char **out_library_name) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *library_name;
  if (state == NULL || candidate == NULL || out_base_reg == NULL || out_displacement == NULL ||
      out_library_name == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  library_name = trace_library_from_operand(state, &instruction.operands[0]);
  if (library_name == NULL || amiga_os_find_library_base_name(library_name) == NULL) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[1], &base_reg, &displacement)) return 0;
  *out_base_reg = base_reg;
  *out_displacement = displacement;
  *out_library_name = library_name;
  return 1;
}

static int candidate_stores_d0_to_a6_slot(const M68kDecodeCandidate *candidate, int16_t *out_displacement) {
  M68kInstructionIR instruction;
  uint8_t source_reg = 0U;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (candidate == NULL || out_displacement == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_data_register_local(&instruction.operands[0], &source_reg) || source_reg != 0U) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[1], &base_reg, &displacement) ||
      base_reg != 6U) return 0;
  *out_displacement = displacement;
  return 1;
}

int reglist_contains_data_register_local(const M68kOperandIR *operand, uint8_t reg_index) {
  uint32_t mask;
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_REGLIST || reg_index >= 8U) return 0;
  mask = operand->value.value;
  return (mask & (1UL << reg_index)) != 0U;
}

static int candidate_writes_d0_unknown(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  if (candidate == NULL) return 0;
  if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      candidate->mnemonic_id == M68K_ASM_MNEMONIC_BSR) return 1;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEM)
    return instruction.operand_count >= 2U && reglist_contains_data_register_local(&instruction.operands[1], 0U);
  if (instruction.operand_count >= 2U) {
    const M68kOperandIR *dest = &instruction.operands[instruction.operand_count - 1U];
    uint8_t dest_reg = 0U;
    if (operand_is_data_register_local(dest, &dest_reg) && dest_reg == 0U) return 1;
  }
  return 0;
}

static int candidate_stops_open_library_store_scan(const M68kDecodeCandidate *candidate) {
  if (candidate == NULL) return 1;
  return candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTR ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_STOP ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_ILLEGAL ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_JMP;
}

static int candidate_has_open_library_store_scan_fallthrough(const M68kDecodeCandidate *candidate) {
  if (candidate_stops_open_library_store_scan(candidate)) return 0;
  return candidate->mnemonic_id != M68K_ASM_MNEMONIC_BRA;
}

static void update_open_library_store_scan_a6_state(const M68kDecodeCandidate *candidate, int *a6_is_exec) {
  M68kInstructionIR instruction;
  if (candidate == NULL || a6_is_exec == NULL) return;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return;
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction.operand_count >= 2U && reglist_contains_address_register_local(&instruction.operands[1], 6U))
      *a6_is_exec = 0;
    return;
  }
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction.operand_count >= 2U &&
      operand_is_address_register_local(&instruction.operands[1], 6U)) {
    *a6_is_exec = operand_is_absolute_address_local(&instruction.operands[0], 4U) ? 1 : 0;
  }
}

static int open_library_store_scan_enqueue(uint32_t *queue_offsets, uint8_t *queue_a6_is_exec, size_t *queue_count,
    const uint32_t *visited_offsets, const uint8_t *visited_a6_is_exec, size_t visited_count, uint32_t offset,
    int a6_is_exec) {
  size_t index;
  if (queue_offsets == NULL || queue_a6_is_exec == NULL || queue_count == NULL ||
      visited_offsets == NULL || visited_a6_is_exec == NULL) return 0;
  for (index = 0U; index < visited_count; ++index)
    if (visited_offsets[index] == offset && visited_a6_is_exec[index] == (uint8_t)(a6_is_exec != 0)) return 0;
  for (index = 0U; index < *queue_count; ++index)
    if (queue_offsets[index] == offset && queue_a6_is_exec[index] == (uint8_t)(a6_is_exec != 0)) return 0;
  if (*queue_count >= 64U) return 0;
  queue_offsets[*queue_count] = offset;
  queue_a6_is_exec[*queue_count] = (uint8_t)(a6_is_exec != 0);
  ++(*queue_count);
  return 1;
}

static int render_lookup_add_open_library_result_app_base_slots(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t start_offset,
    const char *library_name) {
  uint32_t queue_offsets[64];
  uint32_t visited_offsets[64];
  uint8_t queue_a6_is_exec[64];
  uint8_t visited_a6_is_exec[64];
  size_t queue_head = 0U;
  size_t queue_count = 0U;
  size_t visited_count = 0U;
  int result = 0;
  if (lookup == NULL || section == NULL || accepted_start == NULL ||
      library_name == NULL || library_name[0] == '\0') return 0;
  open_library_store_scan_enqueue(queue_offsets, queue_a6_is_exec, &queue_count,
    visited_offsets, visited_a6_is_exec, visited_count, start_offset, 1);
  while (queue_head < queue_count && visited_count < sizeof(visited_offsets) / sizeof(visited_offsets[0])) {
    uint32_t offset = queue_offsets[queue_head];
    int a6_is_exec = queue_a6_is_exec[queue_head] != 0U;
    const M68kDecodeCandidate *candidate;
    int16_t displacement = 0;
    size_t target_index;
    int next_a6_is_exec;
    ++queue_head;
    visited_offsets[visited_count] = offset;
    visited_a6_is_exec[visited_count] = (uint8_t)(a6_is_exec != 0);
    ++visited_count;
    if (!accepted_start_at(section, accepted_start, offset)) continue;
    candidate = find_candidate_at_offset_local(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U) continue;
    if (!a6_is_exec && candidate_stores_d0_to_a6_slot(candidate, &displacement)) {
      if (render_lookup_add_base_field_slot(lookup, "__amiga_app_base__", displacement, library_name,
          section->section_index, candidate->offset) != 0)
        return -1;
      result = 1;
      continue;
    }
    if (candidate_writes_d0_unknown(candidate)) continue;
    next_a6_is_exec = a6_is_exec;
    update_open_library_store_scan_a6_state(candidate, &next_a6_is_exec);
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      if (target->has_section == 0U || target->section_index != section->section_index) continue;
      open_library_store_scan_enqueue(queue_offsets, queue_a6_is_exec, &queue_count,
        visited_offsets, visited_a6_is_exec, visited_count, target->offset, next_a6_is_exec);
    }
    if (candidate_has_open_library_store_scan_fallthrough(candidate)) {
      open_library_store_scan_enqueue(queue_offsets, queue_a6_is_exec, &queue_count,
        visited_offsets, visited_a6_is_exec, visited_count, candidate->offset + candidate->byte_count,
        next_a6_is_exec);
    }
  }
  return result;
}

static int candidate_copies_local_slot_to_global_slot(const M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, size_t section_index, const M68kDecodeCandidate *candidate,
    size_t *out_target_section, uint32_t *out_target_offset, const char **out_library_name) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *library_name;
  uint32_t offset;
  uint32_t end;
  if (lookup == NULL || state == NULL || candidate == NULL || out_target_section == NULL ||
      out_target_offset == NULL || out_library_name == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[0], &base_reg, &displacement)) return 0;
  library_name = trace_local_slot_library(state, base_reg, displacement);
  if (library_name == NULL || amiga_os_find_library_base_name(library_name) == NULL) return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset + 2U; offset < end; ++offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 1U) continue;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    *out_library_name = library_name;
    return 1;
  }
  return 0;
}

static int candidate_stores_library_to_global_slot(const M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, size_t section_index, const M68kDecodeCandidate *candidate,
    size_t *out_target_section, uint32_t *out_target_offset, const char **out_library_name) {
  M68kInstructionIR instruction;
  const char *library_name;
  uint32_t offset;
  uint32_t end;
  if (lookup == NULL || state == NULL || candidate == NULL || out_target_section == NULL ||
      out_target_offset == NULL || out_library_name == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  library_name = trace_library_from_operand(state, &instruction.operands[0]);
  if (library_name == NULL || amiga_os_find_library_base_name(library_name) == NULL) return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset + 2U; offset < end; ++offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 1U) continue;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    *out_library_name = library_name;
    return 1;
  }
  return 0;
}

static int candidate_stores_named_value_to_app_slot(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate, int16_t *out_displacement, char *out_symbol_name,
    size_t out_symbol_name_size) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *source_name;
  if (out_symbol_name != NULL && out_symbol_name_size != 0U) out_symbol_name[0] = '\0';
  if (state == NULL || candidate == NULL || out_displacement == NULL ||
      out_symbol_name == NULL || out_symbol_name_size == 0U) {
    return 0;
  }
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) {
    return 0;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  source_name = trace_name_from_operand(state, &instruction.operands[0]);
  if (source_name == NULL || source_name[0] == '\0' || platform_state_name_is_app_base(source_name)) return 0;
  if (amiga_os_find_library_base_name(source_name) != NULL ||
      amiga_os_find_library_name_by_base_name(source_name) != NULL) {
    return 0;
  }
  if (!operand_is_address_displacement_local(&instruction.operands[1], &base_reg, &displacement)) return 0;
  if (base_reg >= 8U || !state->addr_regs[base_reg].known ||
      !platform_state_name_is_app_base(state->addr_regs[base_reg].name)) {
    return 0;
  }
  if (!format_app_named_value_slot_symbol(source_name, out_symbol_name, out_symbol_name_size)) return 0;
  *out_displacement = displacement;
  return 1;
}

static int app_slot_access_memory_write_is_readwrite(const M68kSimFormMetadata *metadata) {
  if (metadata == NULL) return 0;
  switch (metadata->operation_type) {
  case M68K_SIM_OP_MOVE:
  case M68K_SIM_OP_CLEAR:
  case M68K_SIM_OP_SET_COND:
  case M68K_SIM_OP_MOVE_MULTIPLE:
  case M68K_SIM_OP_MOVE_PERIPHERAL:
    return 0;
  default:
    return 1;
  }
}

uint8_t app_slot_access_kind_from_instruction(const M68kInstructionIR *instruction, size_t operand_index) {
  const M68kSimFormMetadata *metadata;
  uint8_t access_kind;
  if (instruction == NULL || operand_index >= instruction->operand_count || operand_index >= 4U)
    return M68K_APP_SLOT_ACCESS_NONE;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return M68K_APP_SLOT_ACCESS_NONE;
  access_kind = metadata->operand_access_kinds[operand_index];
  if (access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS || access_kind == M68K_SIM_ACCESS_BRANCH_TARGET)
    return M68K_APP_SLOT_ACCESS_ADDRESS;
  if (access_kind == M68K_SIM_ACCESS_MEMORY_READ || access_kind == M68K_SIM_ACCESS_REGISTER_READ)
    return M68K_APP_SLOT_ACCESS_READ;
  if (access_kind == M68K_SIM_ACCESS_MEMORY_WRITE || access_kind == M68K_SIM_ACCESS_REGISTER_WRITE) {
    return app_slot_access_memory_write_is_readwrite(metadata)
      ? M68K_APP_SLOT_ACCESS_READ_WRITE
      : M68K_APP_SLOT_ACCESS_WRITE;
  }
  return M68K_APP_SLOT_ACCESS_NONE;
}

int render_state_operand_uses_app_base(const M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement) {
  if (state == NULL || base_reg >= 8U) return 0;
  if (state->address_app_base_known[base_reg]) return 1;
  if (state->address_base_known[base_reg])
    return library_base_can_use_app_extension_slot(state->address_base_library[base_reg], displacement);
  return base_reg == 6U && !state->address_base_known[6U];
}

static int render_lookup_analyze_amiga_app_state_slots(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  size_t section_index;
  int32_t min_app_displacement = 0;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  if (lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK)
    return 0;
  if (lookup_has_amiga_resident_library_context(lookup) &&
      !amiga_os_find_constant_value("LIB_SIZE", &min_app_displacement)) {
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderPlatformState state;
    size_t candidate_index;
    memset(&state, 0, sizeof(state));
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      size_t operand_index;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
        uint8_t base_reg = 0U;
        int16_t displacement = 0;
        uint8_t access_kind;
        if (!operand_is_address_displacement_local(&instruction.operands[operand_index], &base_reg,
            &displacement)) {
          continue;
        }
        if ((int32_t)displacement < min_app_displacement) continue;
        if (!render_state_operand_uses_app_base(&state, base_reg, displacement)) continue;
        access_kind = app_slot_access_kind_from_instruction(&instruction, operand_index);
        if (access_kind == M68K_APP_SLOT_ACCESS_NONE) continue;
        if (render_lookup_add_app_access_ref(lookup, section->section_index, candidate->offset, base_reg,
            displacement, (uint8_t)operand_index, access_kind) != 0) {
          return -1;
        }
      }
      platform_state_update_after_instruction(&state, lookup, &instruction);
    }
  }
  return 0;
}

static int render_lookup_infer_global_base_slots(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  M68kRenderGlobalBaseObservation *observations = NULL;
  M68kRenderGlobalBaseObservation *wrapper_observations = NULL;
  size_t observation_count = 0U;
  size_t observation_capacity = 0U;
  size_t wrapper_observation_count = 0U;
  size_t wrapper_observation_capacity = 0U;
  size_t section_index;
  int result = -1;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderBaseTraceState trace_state;
    size_t candidate_index;
    uint32_t expected_offset = 0U;
    int have_expected_offset = 0;
    int current_slot_valid = 0;
    int current_segment_valid = 0;
    uint32_t current_segment_entry = 0U;
    size_t current_slot_section = 0U;
    uint32_t current_slot_offset = 0U;
    trace_state_reset(&trace_state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      size_t slot_section = 0U;
      uint32_t slot_offset = 0U;
      const char *library_name = NULL;
      const AmigaOsLibraryVectorInfo *helper_vector = NULL;
      uint8_t local_base_reg = 0U, loaded_address_reg = 0U, app_address_reg = 0U;
      int16_t local_displacement = 0, app_address_displacement = 0, named_app_slot_displacement = 0;
      char loaded_library_name[64], named_app_slot_symbol[64];
      int16_t lvo = 0, wrapper_lvo = 0;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (have_expected_offset && candidate->offset != expected_offset) {
        current_segment_valid = 0;
      }
      if (!current_segment_valid) {
        current_segment_valid = 1;
        current_segment_entry = candidate->offset;
      }
      trace_state_apply_policy_register_seeds(&trace_state, lookup->policy, section->section_index,
        candidate->offset);
      if (candidate_lea_known_amiga_name_to_address_reg(section, candidate, &loaded_address_reg,
          loaded_library_name, sizeof(loaded_library_name))) {
        trace_addr_reg_set_name(&trace_state, loaded_address_reg, loaded_library_name);
      }
      if (candidate_lea_app_base_address_to_address_reg(candidate, &app_address_reg, &app_address_displacement)) {
        trace_addr_reg_set_app_address(&trace_state, app_address_reg, app_address_displacement);
      }
      if (candidate_is_exec_open_library_call(&trace_state, candidate) && trace_state.addr_regs[1].known) {
        trace_reg_set(&trace_state.data_regs[0], trace_state.addr_regs[1].name);
        if (render_lookup_add_open_library_result_app_base_slots(lookup, section, accepted_start[section_index],
            candidate->offset + candidate->byte_count, trace_state.addr_regs[1].name) < 0) {
          goto cleanup;
        }
      }
      helper_vector = resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section->section_index,
        candidate);
      if (amiga_vector_is_open_library(helper_vector) && trace_state.addr_regs[1].known) {
        trace_reg_set(&trace_state.data_regs[0], trace_state.addr_regs[1].name);
        if (render_lookup_add_open_library_result_app_base_slots(lookup, section, accepted_start[section_index],
            candidate->offset + candidate->byte_count, trace_state.addr_regs[1].name) < 0) {
          goto cleanup;
        }
      }
      if (candidate_is_exec_open_device_call(&trace_state, candidate) &&
          trace_state.addr_regs[0].known && trace_state.app_addresses[1].known) {
        char iorequest_slot_name[64];
        int32_t device_base_displacement = (int32_t)trace_state.app_addresses[1].displacement +
          (int32_t)AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET;
        if (render_lookup_add_device_instance(lookup, trace_state.app_addresses[1].displacement,
            trace_state.addr_regs[0].name) != 0 ||
            render_lookup_add_device_call(lookup, section->section_index, candidate->offset,
            trace_state.addr_regs[0].name) != 0) {
          goto cleanup;
        }
        if (format_open_device_app_iorequest_slot_name(trace_state.addr_regs[0].name, iorequest_slot_name,
            sizeof(iorequest_slot_name))) {
          if (render_lookup_add_base_field_slot_with_symbol(lookup, "__amiga_app_base__",
              trace_state.app_addresses[1].displacement, trace_state.addr_regs[0].name, iorequest_slot_name,
              M68K_RENDER_BASE_FIELD_SLOT_IOREQUEST, section->section_index, candidate->offset) != 0) {
            goto cleanup;
          }
        }
        if (device_base_displacement >= -32768 && device_base_displacement <= 32767) {
          if (render_lookup_add_device_base_field_slot(lookup, "__amiga_app_base__",
              (int16_t)device_base_displacement, trace_state.addr_regs[0].name, section->section_index,
              candidate->offset) != 0) {
            goto cleanup;
          }
        }
      }
      if (render_lookup_record_device_call_from_iorequest(lookup, &trace_state, section, candidate) != 0)
        goto cleanup;
      if (candidate_stores_library_to_local_slot(&trace_state, candidate, &local_base_reg, &local_displacement,
          &library_name)) {
        char unknown_owner_name[32];
        const char *owner_name = trace_state.addr_regs[local_base_reg].known
          ? trace_state.addr_regs[local_base_reg].name
          : (local_base_reg == 6U ? "__amiga_app_base__" : NULL);
        if (owner_name == NULL &&
            amiga_unknown_base_register_owner_name(local_base_reg, unknown_owner_name, sizeof(unknown_owner_name))) {
          owner_name = unknown_owner_name;
        }
        trace_local_slot_set(&trace_state, local_base_reg, local_displacement, library_name);
        if (owner_name != NULL &&
            render_lookup_add_base_field_slot(lookup, owner_name, local_displacement, library_name,
              section->section_index, candidate->offset) != 0) {
          goto cleanup;
        }
      }
      if (candidate_stores_named_value_to_app_slot(&trace_state, candidate, &named_app_slot_displacement,
          named_app_slot_symbol, sizeof(named_app_slot_symbol))) {
        if (render_lookup_add_named_app_field_slot(lookup, named_app_slot_displacement, named_app_slot_symbol,
            section->section_index, candidate->offset) != 0) {
          goto cleanup;
        }
      }
      if (candidate_copies_local_slot_to_global_slot(lookup, &trace_state, section->section_index, candidate,
          &slot_section, &slot_offset, &library_name)) {
        if (render_lookup_add_global_base_slot(lookup, slot_section, slot_offset, library_name,
            section->section_index, candidate->offset) != 0) goto cleanup;
      }
      if (candidate_stores_library_to_global_slot(lookup, &trace_state, section->section_index, candidate,
          &slot_section, &slot_offset, &library_name)) {
        if (render_lookup_add_global_base_slot(lookup, slot_section, slot_offset, library_name,
            section->section_index, candidate->offset) != 0) goto cleanup;
      }
      if (candidate_loads_relocated_global_slot_to_a6(lookup, section->section_index, candidate,
          &slot_section, &slot_offset)) {
        current_slot_valid = 1;
        current_slot_section = slot_section;
        current_slot_offset = slot_offset;
      } else if (candidate_writes_a6_unknown(candidate)) {
        current_slot_valid = 0;
      }
      if (current_slot_valid && candidate_calls_a6_lvo(candidate, &lvo)) {
        if (global_base_observation_add(&observations, &observation_count, &observation_capacity,
          current_slot_section, current_slot_offset, lvo) != 0) goto cleanup;
      }
      if (candidate_loads_d0_lvo_immediate(candidate, &wrapper_lvo)) {
        uint32_t next_offset = candidate->offset + candidate->byte_count;
        const M68kDecodeCandidate *next_candidate = NULL;
        uint32_t wrapper_offset = 0U;
        if (accepted_start_at(section, accepted_start[section_index], next_offset))
          next_candidate = find_candidate_at_offset_local(section, next_offset);
        if (candidate_direct_same_section_target(next_candidate, section->section_index, &wrapper_offset)) {
          if (global_base_observation_add(&wrapper_observations, &wrapper_observation_count,
              &wrapper_observation_capacity, section->section_index, wrapper_offset, wrapper_lvo) != 0) {
            goto cleanup;
          }
        }
      }
      if (trace_state.addr_regs[6].known && candidate_calls_a6_d0_indexed_vector(candidate)) {
        if (render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, current_segment_entry,
            trace_state.addr_regs[6].name) != 0 ||
            render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, candidate->offset,
            trace_state.addr_regs[6].name) != 0 ||
            render_lookup_add_indexed_vector_wrapper_branch_aliases(lookup, section, accepted_start[section_index],
            current_segment_entry, trace_state.addr_regs[6].name) != 0) {
          goto cleanup;
        }
      }
      if (candidate_terminates_a6_state(candidate)) {
        current_slot_valid = 0;
        current_segment_valid = 0;
        trace_state_reset(&trace_state);
      } else {
        trace_state_update_register_names_after_candidate(&trace_state, lookup, candidate);
      }
      expected_offset = candidate->offset + candidate->byte_count;
      have_expected_offset = 1;
    }
  }
  for (section_index = 0U; section_index < observation_count; ++section_index) {
    const M68kRenderGlobalBaseObservation *observation = &observations[section_index];
    const char *library_name = unique_library_for_observed_lvos(observation);
    if (library_name == NULL) continue;
    if (render_lookup_add_global_base_slot(lookup, observation->section_index, observation->offset,
        library_name, SIZE_MAX, UINT32_MAX) != 0) goto cleanup;
  }
  for (section_index = 0U; section_index < wrapper_observation_count; ++section_index) {
    const M68kRenderGlobalBaseObservation *observation = &wrapper_observations[section_index];
    const char *library_name = unique_library_for_observed_lvos(observation);
    if (library_name == NULL) continue;
    if (render_lookup_add_indexed_vector_wrapper(lookup, observation->section_index, observation->offset,
        library_name) != 0) goto cleanup;
  }
  result = 0;
cleanup:
  free(observations);
  free(wrapper_observations);
  return result;
}

const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_vector_at(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t wrapper_offset,
    unsigned depth) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  const AmigaOsLibraryVectorInfo *pending_vector = NULL;
  uint32_t cursor;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || section_index >= decode->section_count)
    return NULL;
  if (depth > 4U) return NULL;
  section = &decode->sections[section_index];
  if (!accepted_start_at(section, accepted_start[section_index], wrapper_offset)) return NULL;
  memset(&state, 0, sizeof(state));
  cursor = wrapper_offset;
  while (cursor < section->size && cursor - wrapper_offset < 128U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    uint32_t relocation_offset;
    uint32_t relocation_end;
    const AmigaOsLibraryVectorInfo *vector;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (!accepted_start_at(section, accepted_start[section_index], cursor)) break;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    relocation_end = candidate->offset + candidate->byte_count;
    for (relocation_offset = candidate->offset; relocation_offset < relocation_end; ++relocation_offset) {
      const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, relocation_offset);
      size_t operand_index = 0U;
      if (relocation == NULL) continue;
      if (!find_unique_relocation_operand(candidate, relocation, &operand_index) ||
          operand_index >= instruction.operand_count) {
        continue;
      }
      attach_operand_label_symbol(lookup, &instruction, operand_index, section->section_index, candidate->offset,
        relocation->target_section_index, relocation->target_offset);
    }
    if (pending_vector != NULL) {
      if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_RTS) return pending_vector;
      if (!instruction_is_local_wrapper_cleanup(&instruction)) return NULL;
      cursor += candidate->byte_count;
      continue;
    }
    if (candidate_has_non_call_control_target(candidate)) return NULL;
    vector = resolve_amiga_direct_wrapper_call_vector_depth(lookup, decode, accepted_start, section->section_index,
      candidate, depth + 1U);
    if (vector != NULL) {
      pending_vector = vector;
      cursor += candidate->byte_count;
      continue;
    }
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector != NULL) {
      if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_JMP) return vector;
      pending_vector = vector;
      cursor += candidate->byte_count;
      continue;
    }
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (candidate_terminates_a6_state(candidate)) break;
    cursor += candidate->byte_count;
  }
  return NULL;
}

const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector_depth(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate, unsigned depth) {
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (depth > 4U) return NULL;
  if (candidate == NULL ||
      (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
       candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR)) {
    return NULL;
  }
  if (!candidate_direct_control_target(lookup, source_section_index, candidate, &target_section_index, &target_offset))
    return NULL;
  if (target_section_index == source_section_index && target_offset == candidate->offset) return NULL;
  return resolve_amiga_direct_wrapper_vector_at(lookup, decode, accepted_start, target_section_index, target_offset,
    depth);
}

const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate) {
  return resolve_amiga_direct_wrapper_call_vector_depth(lookup, decode, accepted_start, source_section_index,
    candidate, 0U);
}

void attach_known_instruction_relocations(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  uint32_t relocation_offset;
  uint32_t relocation_end;
  if (lookup == NULL || candidate == NULL || instruction == NULL) return;
  relocation_end = candidate->offset + candidate->byte_count;
  for (relocation_offset = candidate->offset; relocation_offset < relocation_end; ++relocation_offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, relocation_offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) ||
        operand_index >= instruction->operand_count) {
      continue;
    }
    attach_operand_label_symbol(lookup, instruction, operand_index, section_index, candidate->offset,
      relocation->target_section_index, relocation->target_offset);
  }
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_primary_vector_at(
    const M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index,
    uint32_t helper_offset, unsigned depth) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  uint32_t cursor;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      section_index >= decode->section_count || depth > 4U) {
    return NULL;
  }
  section = &decode->sections[section_index];
  if (!accepted_start_at(section, accepted_start[section_index], helper_offset)) return NULL;
  memset(&state, 0, sizeof(state));
  cursor = helper_offset;
  while (cursor < section->size && cursor - helper_offset < 256U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsLibraryVectorInfo *vector;
    const AmigaOsLibraryVectorInfo *nested_vector;
    if (!accepted_start_at(section, accepted_start[section_index], cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index, cursor);
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector != NULL) return vector;
    vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section_index], candidate,
      &instruction);
    if (vector != NULL) return vector;
    vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &state, section, candidate);
    if (vector != NULL) return vector;
    vector = resolve_amiga_direct_wrapper_call_vector_depth(lookup, decode, accepted_start, section->section_index,
      candidate, depth + 1U);
    if (vector != NULL) return vector;
    nested_vector = resolve_amiga_local_helper_call_vector_depth(lookup, decode, accepted_start,
      section->section_index, candidate, depth + 1U);
    if (nested_vector != NULL) return nested_vector;
    if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_BSR ||
        candidate->mnemonic_id == M68K_ASM_MNEMONIC_JSR) {
      return NULL;
    }
    platform_state_update_d0_lvo_after_instruction(&state, &instruction);
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (!candidate_has_local_helper_summary_fallthrough(candidate)) break;
    cursor += candidate->byte_count;
  }
  return NULL;
}

const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector_depth(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate, unsigned depth) {
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (depth > 4U || candidate == NULL ||
      (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
       candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR)) {
    return NULL;
  }
  if (!candidate_direct_control_target(lookup, source_section_index, candidate, &target_section_index, &target_offset))
    return NULL;
  if (target_section_index == source_section_index && target_offset == candidate->offset) return NULL;
  return resolve_amiga_local_helper_primary_vector_at(lookup, decode, accepted_start, target_section_index,
    target_offset, depth);
}

const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate) {
  return resolve_amiga_local_helper_call_vector_depth(lookup, decode, accepted_start, source_section_index,
    candidate, 0U);
}

int render_lookup_infer_amiga_call_input_comments(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  M68kRenderPlatformState platform_state;
  M68kRenderDataPointerState data_pointer_state;
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  memset(&platform_state, 0, sizeof(platform_state));
  data_pointer_state_clear_all(&data_pointer_state);
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    data_pointer_state_clear_all(&data_pointer_state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const AmigaOsLibraryVectorInfo *platform_vector;
      const AmigaOsLibraryVectorInfo *immediate_vector;
      const AmigaOsLibraryVectorInfo *wrapper_call_vector;
      const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
      const AmigaOsLibraryVectorInfo *vector;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
      platform_vector = attach_amiga_lvo_symbol_if_known(&platform_state, &instruction);
      immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section_index],
        candidate, &instruction);
      wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
      direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
        section->section_index, candidate);
      vector = platform_vector != NULL ? platform_vector :
        (direct_wrapper_vector != NULL ? direct_wrapper_vector :
        (wrapper_call_vector != NULL ? wrapper_call_vector : immediate_vector));
      if (vector != NULL &&
          render_lookup_add_call_setup_comments_for_vector(lookup, section, accepted_start[section_index],
            candidate->offset, vector, platform_vector != NULL || immediate_vector != NULL) != 0) {
        return -1;
      }
      if (vector != NULL && render_lookup_add_string_spans_for_vector_inputs(lookup, decode, vector,
          &data_pointer_state) != 0) {
        return -1;
      }
      data_pointer_state_update_after_instruction(&data_pointer_state, lookup, section, candidate, &instruction);
      platform_state_update_d0_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    }
  }
  return 0;
}

int m68k_analysis_render_lookup_run_platform_passes(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, uint8_t **accepted_bytes) {
  if (render_lookup_seed_policy_app_slot_regions(lookup) != 0) return -1;
  if (render_lookup_infer_global_base_slots(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_infer_amiga_recovered_local_call_summaries(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_infer_amiga_recovered_function_args(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_analyze_amiga_typed_refs(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_infer_amiga_call_input_comments(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_analyze_amiga_app_state_slots(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_infer_platform_runtime_structured_data(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_infer_amiga_palette_uploads(lookup, decode, accepted_start, accepted_bytes) != 0) return -1;
  if (render_lookup_infer_amiga_bitmap_memory_uses(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_infer_amiga_audio_length_sources(lookup, decode, accepted_start, accepted_bytes) != 0) return -1;
  if (render_lookup_infer_relocation_pointer_tables(lookup, decode, accepted_bytes) != 0) return -1;
  if (render_lookup_infer_indexed_word_dispatch_tables(lookup, decode, accepted_start, accepted_bytes) != 0)
    return -1;
  if (render_lookup_infer_pc_relative_lookup_scalars(lookup, decode, accepted_start, accepted_bytes) != 0)
    return -1;
  return 0;
}

int m68k_analysis_render_lookup_append_auto_policy(M68kSourceAnalysisIR *source_analysis,
    M68kRenderLookup *lookup) {
  return source_analysis_append_auto_structured_data_policy(source_analysis, lookup);
}

int m68k_analysis_render_lookup_append_section(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    M68kSectionAnalysisIR *section_analysis) {
  if (append_render_lookup_platform_effects_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_app_slot_refs_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_runtime_views_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_runtime_address_refs_for_section(lookup, decode, section_analysis) != 0) return -1;
  if (append_render_lookup_code_start_refs_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_violations_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_recovered_local_call_summaries_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_recovered_function_args_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_typed_accesses_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_unresolved_typed_accesses_for_section(lookup, section_analysis) != 0) return -1;
  return 0;
}

