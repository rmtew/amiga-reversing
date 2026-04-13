#include "platform_file_internal.h"

#define AMIGA_BASE_SLOT_TAG_CAPACITY 64U

const char *read_amiga_library_seed_name(const M68kSection *section, uint32_t target) {
  size_t end;
  if (section == NULL || target >= section->data_size) return NULL;
  end = target;
  while (end < section->data_size && end - target < 64U) {
    uint8_t ch = section->data[end];
    if (ch == 0U) break;
    if (ch < 32U || ch > 126U) return NULL;
    ++end;
  }
  if (end >= section->data_size || section->data[end] != 0U || end == target) return NULL;
  return amiga_os_find_library_base_name((const char *)(section->data + target));
}

void set_amiga_base_slot_tag(AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement, const char *base_name) {
  size_t index;
  if (slots == NULL || base_name == NULL) return;
  for (index = 0; index < slot_count; ++index) {
    if (slots[index].base_name == NULL || slots[index].displacement == displacement) {
      slots[index].displacement = displacement;
      slots[index].base_name = base_name;
      return;
    }
  }
}

const char *lookup_amiga_base_slot_tag(const AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement) {
  size_t index;
  if (slots == NULL) return NULL;
  for (index = 0; index < slot_count; ++index) {
    if (slots[index].base_name != NULL && slots[index].displacement == displacement) return slots[index].base_name;
  }
  return NULL;
}

const char *lookup_recovered_platform_base_slot(const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  size_t index;
  if (section_analysis == NULL) return NULL;
  for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
    const M68kRecoveredPlatformBaseSlotIR *slot = &section_analysis->recovered_platform_base_slots[index];
    if (slot->displacement == displacement) return slot->base_name;
  }
  return NULL;
}

const char *resolve_amiga_app_slot_base_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  (void)ctx;
  return lookup_recovered_platform_base_slot(section_analysis, displacement);
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_library_vector_entry_for_base_name(
    const M68kInstructionIR *instruction, const char *base_name) {
  const M68kOperandIR *operand = NULL;
  int16_t displacement;
  if (instruction == NULL || base_name == NULL) return NULL;
  if (!instruction_is_call_transfer(instruction)) return NULL;
  if (!instruction_target_operand_local(instruction, &operand) || operand == NULL) return NULL;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return NULL;
  if (operand->value.ea_mode != 5U) return NULL;
  displacement = (int16_t)(operand->value.value & 0xFFFFU);
  if (displacement >= 0 || (displacement & 1) != 0) return NULL;
  return amiga_os_find_library_vector(base_name, displacement);
}

static void trace_amiga_call_setup(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    uint32_t call_offset, const char **out_a0_seed_base_name, int16_t *out_a1_app_disp,
    const char **out_a1_seed_base_name) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t cursor;
  uint32_t start;
  const char *addr_reg_seed_base_names[8] = {0};
  const char *addr_reg_base_names[8] = {0};
  const char *saved_stack_base_names[8] = {0};
  int16_t addr_reg_app_disp[8];
  size_t saved_stack_base_count = 0U;
  uint8_t reg_index;
  if (out_a0_seed_base_name != NULL) *out_a0_seed_base_name = NULL;
  if (out_a1_app_disp != NULL) *out_a1_app_disp = 0;
  if (out_a1_seed_base_name != NULL) *out_a1_seed_base_name = NULL;
  if (section == NULL || section_analysis == NULL) return;
  for (reg_index = 0U; reg_index < 8U; ++reg_index) addr_reg_app_disp[reg_index] = INT16_MIN;
  addr_reg_base_names[6] = AMIGA_APP_BASE_TAG;
  start = resolve_analysis_trace_start(ctx, section_analysis, call_offset);
  if (start == UINT32_MAX) return;
  cursor = start;
  while (cursor < call_offset && cursor < section->data_size) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    uint8_t exg_left;
    uint8_t exg_right;
    uint8_t dest_reg;
    uint8_t pushed_reg;
    const M68kOperandIR *source = NULL;
    uint8_t written_reg;
    uint32_t source_target;
    int16_t slot_disp;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    metadata = instruction_sim_metadata(&instruction);
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > call_offset) break;
    if (instruction_is_address_exg(&instruction, &exg_left, &exg_right)) {
      const char *tmp_base = addr_reg_base_names[exg_left];
      const char *tmp_seed = addr_reg_seed_base_names[exg_left];
      int16_t tmp_disp = addr_reg_app_disp[exg_left];
      addr_reg_base_names[exg_left] = addr_reg_base_names[exg_right];
      addr_reg_base_names[exg_right] = tmp_base;
      addr_reg_seed_base_names[exg_left] = addr_reg_seed_base_names[exg_right];
      addr_reg_seed_base_names[exg_right] = tmp_seed;
      addr_reg_app_disp[exg_left] = addr_reg_app_disp[exg_right];
      addr_reg_app_disp[exg_right] = tmp_disp;
      cursor += (uint32_t)instruction.byte_count;
      continue;
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_address_reg_approx(&instruction, written_reg)) {
        addr_reg_base_names[written_reg] = NULL;
        addr_reg_seed_base_names[written_reg] = NULL;
        addr_reg_app_disp[written_reg] = INT16_MIN;
      }
    }
    if (instruction_is_address_move(&instruction, &dest_reg, &source)) {
      if (operand_is_absolute_short_value(source, 4U)) {
        addr_reg_base_names[dest_reg] = "SysBase";
      } else if (source != NULL && source->kind == M68K_ASM_OPERAND_AN && source->value.reg < 8U) {
        addr_reg_base_names[dest_reg] = addr_reg_base_names[source->value.reg];
        addr_reg_seed_base_names[dest_reg] = addr_reg_seed_base_names[source->value.reg];
        addr_reg_app_disp[dest_reg] = addr_reg_app_disp[source->value.reg];
      } else if (source != NULL && operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        addr_reg_base_names[dest_reg] = AMIGA_APP_BASE_TAG;
        addr_reg_app_disp[dest_reg] = slot_disp;
      } else if (metadata != NULL &&
          metadata->source_operand_index < instruction.operand_count &&
          instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
            (uint32_t)section->data_size, &source_target)) {
        addr_reg_seed_base_names[dest_reg] = read_amiga_library_seed_name(section, source_target);
      }
    } else if (instruction_mnemonic_is(&instruction, "lea") &&
        instruction.operand_count == 2U &&
        instruction.operands[1].kind == M68K_ASM_OPERAND_AN) {
      dest_reg = instruction.operands[1].value.reg;
      source = &instruction.operands[0];
      if (operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        addr_reg_base_names[dest_reg] = AMIGA_APP_BASE_TAG;
        addr_reg_seed_base_names[dest_reg] = NULL;
        addr_reg_app_disp[dest_reg] = slot_disp;
      } else if (metadata != NULL &&
          metadata->source_operand_index < instruction.operand_count &&
          instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
            (uint32_t)section->data_size, &source_target)) {
        addr_reg_base_names[dest_reg] = NULL;
        addr_reg_seed_base_names[dest_reg] = read_amiga_library_seed_name(section, source_target);
        addr_reg_app_disp[dest_reg] = INT16_MIN;
      }
    }
    if (instruction_pushes_address_reg_to_stack(&instruction, &pushed_reg) &&
        pushed_reg < 8U && saved_stack_base_count < (sizeof(saved_stack_base_names) / sizeof(saved_stack_base_names[0]))) {
      saved_stack_base_names[saved_stack_base_count++] = addr_reg_base_names[pushed_reg];
    }
    if (instruction_pops_address_reg_from_stack(&instruction, &dest_reg) && saved_stack_base_count != 0U) {
      addr_reg_base_names[dest_reg] = saved_stack_base_names[--saved_stack_base_count];
      addr_reg_seed_base_names[dest_reg] = NULL;
      addr_reg_app_disp[dest_reg] = INT16_MIN;
    }
    cursor += (uint32_t)instruction.byte_count;
  }
  if (out_a0_seed_base_name != NULL) *out_a0_seed_base_name = addr_reg_seed_base_names[0];
  if (out_a1_app_disp != NULL) *out_a1_app_disp = addr_reg_app_disp[1];
  if (out_a1_seed_base_name != NULL) *out_a1_seed_base_name = addr_reg_seed_base_names[1];
}

static int resolve_local_data_reg_immediate_seed(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int32_t *out_value) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t cursor;
  uint32_t start;
  int have_value = 0;
  int32_t value = 0;
  if (out_value != NULL) *out_value = 0;
  if (section == NULL || section_analysis == NULL || reg >= 8U) return 0;
  start = resolve_analysis_trace_start(ctx, section_analysis, offset);
  if (start == UINT32_MAX || start > offset) return 0;
  for (cursor = start; cursor < offset && cursor < section->data_size; ) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    uint8_t dest_reg;
    const M68kOperandIR *source = NULL;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > offset) break;
    if (instruction_writes_data_reg_approx(&instruction, reg)) {
      if (instruction_mnemonic_is(&instruction, "moveq") &&
          instruction.operand_count == 2U &&
          operand_is_data_reg_direct(&instruction.operands[1], reg) &&
          instruction.operands[0].kind == M68K_ASM_OPERAND_IMM) {
        value = (int32_t)m68k_sign_extend32(instruction.operands[0].value.value, 8U);
        have_value = 1;
      } else if (instruction_is_data_move(&instruction, &dest_reg, &source) &&
          dest_reg == reg && source != NULL && source->kind == M68K_ASM_OPERAND_IMM) {
        uint32_t raw_value = source->value.value;
        if (instruction_mnemonic_is(&instruction, "moveq")) raw_value = m68k_sign_extend32(raw_value, 8U);
        value = (int32_t)raw_value;
        have_value = 1;
      } else if (instruction_mnemonic_is(&instruction, "clr") &&
          instruction.operand_count != 0U &&
          operand_is_data_reg_direct(&instruction.operands[instruction.operand_count - 1U], reg)) {
        value = 0;
        have_value = 1;
      } else {
        have_value = 0;
      }
    }
    cursor += (uint32_t)instruction.byte_count;
  }
  if (have_value && out_value != NULL) *out_value = value;
  return have_value;
}

static const char *resolve_amiga_library_base_name_raw(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots) {
  const M68kSection *section = section_analysis_context_section(ctx);
  const char *addr_reg_base_names[8] = {0};
  const char *addr_reg_seed_base_names[8] = {0};
  const char *data_reg_base_names[8] = {0};
  AmigaBaseSlotTag slot_base_names[AMIGA_BASE_SLOT_TAG_CAPACITY] = {{0}};
  const char *saved_stack_base_names[8] = {0};
  size_t saved_stack_base_count = 0U;
  size_t slot_base_count = sizeof(slot_base_names) / sizeof(slot_base_names[0]);
  uint32_t cursor;
  if (section == NULL || section_analysis == NULL || reg >= 8U) return NULL;
  addr_reg_base_names[6] = AMIGA_APP_BASE_TAG;
  if (include_section_slots) {
    size_t index;
    slot_base_count = section_analysis->recovered_platform_base_slot_count;
    if (slot_base_count > (sizeof(slot_base_names) / sizeof(slot_base_names[0])))
      slot_base_count = sizeof(slot_base_names) / sizeof(slot_base_names[0]);
    for (index = 0; index < slot_base_count; ++index) {
      slot_base_names[index].displacement = section_analysis->recovered_platform_base_slots[index].displacement;
      slot_base_names[index].base_name = section_analysis->recovered_platform_base_slots[index].base_name;
    }
  }
  cursor = resolve_analysis_trace_start(ctx, section_analysis, offset);
  if (cursor == UINT32_MAX || cursor > offset) return NULL;
  while (cursor < offset && cursor < section->data_size) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    const char *prev_addr_reg_base_names[8];
    const char *prev_addr_reg_seed_base_names[8];
    const char *prev_data_reg_base_names[8];
    uint8_t exg_left;
    uint8_t exg_right;
    uint8_t dest_reg;
    uint8_t reg_kind;
    uint8_t reg_index;
    const M68kOperandIR *source = NULL;
    uint8_t written_reg;
    uint8_t pushed_reg;
    int16_t slot_disp;
    uint32_t source_target;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    metadata = instruction_sim_metadata(&instruction);
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > offset) break;
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      prev_addr_reg_base_names[written_reg] = addr_reg_base_names[written_reg];
      prev_addr_reg_seed_base_names[written_reg] = addr_reg_seed_base_names[written_reg];
      prev_data_reg_base_names[written_reg] = data_reg_base_names[written_reg];
    }
    if (instruction_is_address_exg(&instruction, &exg_left, &exg_right)) {
      const char *tmp = addr_reg_base_names[exg_left];
      const char *tmp_seed = addr_reg_seed_base_names[exg_left];
      addr_reg_base_names[exg_left] = addr_reg_base_names[exg_right];
      addr_reg_base_names[exg_right] = tmp;
      addr_reg_seed_base_names[exg_left] = addr_reg_seed_base_names[exg_right];
      addr_reg_seed_base_names[exg_right] = tmp_seed;
      cursor += (uint32_t)instruction.byte_count;
      continue;
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_address_reg_approx(&instruction, written_reg)) {
        addr_reg_base_names[written_reg] = NULL;
        addr_reg_seed_base_names[written_reg] = NULL;
      }
    }
    if (instruction_is_data_move(&instruction, &dest_reg, &source)) {
      if (source != NULL && source->kind == M68K_ASM_OPERAND_DN && source->value.reg < 8U) {
        data_reg_base_names[dest_reg] = prev_data_reg_base_names[source->value.reg];
      } else if (source != NULL && source->kind == M68K_ASM_OPERAND_AN && source->value.reg < 8U) {
        data_reg_base_names[dest_reg] = prev_addr_reg_base_names[source->value.reg];
      } else if (metadata != NULL &&
          instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
            (uint32_t)section->data_size, &source_target)) {
        data_reg_base_names[dest_reg] = read_amiga_library_seed_name(section, source_target);
      } else {
        data_reg_base_names[dest_reg] = NULL;
      }
    }
    if (instruction_is_address_move(&instruction, &dest_reg, &source)) {
      if (operand_is_absolute_short_value(source, 4U)) {
        addr_reg_base_names[dest_reg] = "SysBase";
        addr_reg_seed_base_names[dest_reg] = NULL;
      } else if (instruction_pops_address_reg_from_stack(&instruction, &dest_reg) &&
          dest_reg == 6U && saved_stack_base_count != 0U) {
        addr_reg_base_names[dest_reg] = saved_stack_base_names[--saved_stack_base_count];
        addr_reg_seed_base_names[dest_reg] = NULL;
      } else if (source != NULL && source->kind == M68K_ASM_OPERAND_AN && source->value.reg < 8U) {
        addr_reg_base_names[dest_reg] = prev_addr_reg_base_names[source->value.reg];
        addr_reg_seed_base_names[dest_reg] = prev_addr_reg_seed_base_names[source->value.reg];
      } else if (source != NULL && source->kind == M68K_ASM_OPERAND_DN && source->value.reg < 8U) {
        addr_reg_base_names[dest_reg] = prev_data_reg_base_names[source->value.reg];
        addr_reg_seed_base_names[dest_reg] = NULL;
      } else if (source != NULL && operand_is_app_base_disp_ea(source, 6U, &slot_disp) &&
          prev_addr_reg_base_names[6] == AMIGA_APP_BASE_TAG) {
        addr_reg_base_names[dest_reg] = lookup_amiga_base_slot_tag(slot_base_names, slot_base_count, slot_disp);
        addr_reg_seed_base_names[dest_reg] = NULL;
      } else if (metadata != NULL &&
          instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
            (uint32_t)section->data_size, &source_target)) {
        addr_reg_base_names[dest_reg] = NULL;
        addr_reg_seed_base_names[dest_reg] = read_amiga_library_seed_name(section, source_target);
      } else {
        addr_reg_base_names[dest_reg] = NULL;
        addr_reg_seed_base_names[dest_reg] = NULL;
      }
    }
    if (instruction_mnemonic_is(&instruction, "pea") && instruction.operand_count == 1U &&
        instruction.operands[0].kind == M68K_ASM_OPERAND_EA &&
        instruction.operands[0].value.ea_mode == 2U && instruction.operands[0].value.ea_reg == 6U &&
        saved_stack_base_count < (sizeof(saved_stack_base_names) / sizeof(saved_stack_base_names[0]))) {
      saved_stack_base_names[saved_stack_base_count++] = prev_addr_reg_base_names[6];
    }
    if (instruction_pushes_address_reg_to_stack(&instruction, &pushed_reg) &&
        pushed_reg < 8U && saved_stack_base_count < (sizeof(saved_stack_base_names) / sizeof(saved_stack_base_names[0]))) {
      saved_stack_base_names[saved_stack_base_count++] = prev_addr_reg_base_names[pushed_reg];
    }
    if (instruction_is_register_to_app_slot_store(&instruction, &reg_kind, &reg_index, &slot_disp) &&
        addr_reg_base_names[6] == AMIGA_APP_BASE_TAG) {
      const char *stored_base = NULL;
      if (reg_kind == 1U && reg_index < 8U) stored_base = prev_data_reg_base_names[reg_index];
      else if (reg_kind == 2U && reg_index < 8U) stored_base = prev_addr_reg_base_names[reg_index];
      if (stored_base != NULL && stored_base != AMIGA_APP_BASE_TAG)
        set_amiga_base_slot_tag(slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]), slot_disp,
          stored_base);
    }
    if (instruction_is_app_slot_load(&instruction, &reg_kind, &reg_index, &slot_disp) &&
        addr_reg_base_names[6] == AMIGA_APP_BASE_TAG) {
      const char *loaded_base = lookup_amiga_base_slot_tag(slot_base_names, slot_base_count, slot_disp);
      if (reg_kind == 1U && reg_index < 8U) data_reg_base_names[reg_index] = loaded_base;
      else if (reg_kind == 2U && reg_index < 8U) {
        addr_reg_base_names[reg_index] = loaded_base;
        addr_reg_seed_base_names[reg_index] = NULL;
      }
    }
    {
      const M68kOperandIR *call_operand = NULL;
      const char *call_base_name = NULL;
      const AmigaOsLibraryVectorInfo *call_entry = NULL;
      if (instruction_target_operand_local(&instruction, &call_operand) && call_operand != NULL &&
          call_operand->kind == M68K_ASM_OPERAND_EA && call_operand->value.ea_mode == 5U &&
          call_operand->value.ea_reg < 8U) {
        call_base_name = addr_reg_base_names[call_operand->value.ea_reg];
      }
      if (call_base_name != NULL && call_base_name != AMIGA_APP_BASE_TAG) {
        call_entry = resolve_amiga_library_vector_entry_for_base_name(&instruction, call_base_name);
      }
      if (call_entry != NULL && call_entry->returns_base_reg_name != NULL &&
          call_entry->returns_base_name_reg_name != NULL &&
          _stricmp(call_entry->returns_base_reg_name, "D0") == 0 &&
          _stricmp(call_entry->returns_base_name_reg_name, "A1") == 0) {
        data_reg_base_names[0] = addr_reg_seed_base_names[1];
      }
    }
    cursor += (uint32_t)instruction.byte_count;
  }
  return addr_reg_base_names[reg] != AMIGA_APP_BASE_TAG ? addr_reg_base_names[reg] : NULL;
}

static const char *resolve_amiga_library_base_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg) {
  return resolve_amiga_library_base_name_raw(ctx, section_analysis, offset, reg, 1);
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_library_vector_entry(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  const char *base_name;
  if (ctx == NULL || section_analysis_context_object(ctx) == NULL || instruction == NULL) return NULL;
  if (section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return NULL;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return NULL;
  {
    const M68kOperandIR *operand = NULL;
    if (!instruction_target_operand_local(instruction, &operand) || operand == NULL) return NULL;
    if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return NULL;
    if (operand->value.ea_mode != 5U || operand->value.ea_reg != 6U) return NULL;
    base_name = resolve_amiga_library_base_name(ctx, section_analysis, offset, operand->value.ea_reg);
  }
  if (base_name == NULL) return NULL;
  return resolve_amiga_library_vector_entry_for_base_name(instruction, base_name);
}

static void collect_section_amiga_base_slot_tags(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, AmigaBaseSlotTag *slots, size_t slot_count) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t offset;
  if (section == NULL || section_analysis == NULL || slots == NULL) return;
  for (offset = 0U; offset < section->data_size; ++offset) {
    SectionDecodeResult call_decode;
    M68kInstructionIR call_instruction;
    uint32_t cursor;
    const char *seed_base_name = NULL;
    uint32_t success_offset = UINT32_MAX;
    const AmigaOsLibraryVectorInfo *call_entry;
    const M68kOperandIR *call_operand = NULL;
    const char *base_name;
    int16_t displacement;
    if (!section_analysis_context_probe_decode(ctx, offset, &call_decode)) continue;
    call_instruction = call_decode.instruction;
    if (!instruction_target_operand_local(&call_instruction, &call_operand) || call_operand == NULL) continue;
    if (!operand_is_app_base_disp_ea(call_operand, 6U, &displacement)) continue;
    if (displacement >= 0 || (displacement & 1) != 0) continue;
    base_name = resolve_amiga_library_base_name_raw(ctx, section_analysis, offset, call_operand->value.ea_reg, 0);
    if (base_name == NULL) continue;
    call_entry = amiga_os_find_library_vector(base_name, displacement);
    if (call_entry == NULL) continue;
    if (call_entry->returns_base_reg_name != NULL && call_entry->returns_base_name_reg_name != NULL) {
      trace_amiga_call_setup(ctx, section_analysis, offset, NULL, NULL, &seed_base_name);
      if (seed_base_name == NULL) continue;
    } else if (strcmp(call_entry->function_name, "OpenDevice") == 0 &&
        call_entry->input_a1_struct_name != NULL &&
        strcmp(call_entry->input_a1_struct_name, "IO") == 0) {
      int16_t io_disp = INT16_MIN;
      trace_amiga_call_setup(ctx, section_analysis, offset, &seed_base_name, &io_disp, NULL);
      if (seed_base_name == NULL || io_disp == INT16_MIN) continue;
      set_amiga_base_slot_tag(slots, slot_count,
        (int16_t)(io_disp + AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET), seed_base_name);
      continue;
    } else {
      continue;
    }
    cursor = offset + (uint32_t)call_instruction.byte_count;
    if (cursor >= section->data_size) continue;
    {
      SectionDecodeResult decode;
      M68kInstructionIR instruction;
      uint32_t branch_target;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) continue;
      instruction = decode.instruction;
      if (instruction_pops_address_reg_from_stack(&instruction, NULL)) {
        cursor += (uint32_t)instruction.byte_count;
      }
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) continue;
      instruction = decode.instruction;
      if (!instruction_mnemonic_is(&instruction, "tst") || instruction.operand_count != 1U ||
          !operand_is_data_reg_direct(&instruction.operands[0], 0U)) {
        continue;
      }
      cursor += (uint32_t)instruction.byte_count;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) continue;
      instruction = decode.instruction;
      if (instruction_mnemonic_is(&instruction, "bne") &&
          instruction_branch_target(&instruction, cursor, &branch_target)) {
        success_offset = branch_target;
      } else if (instruction_mnemonic_is(&instruction, "beq")) {
        success_offset = cursor + (uint32_t)instruction.byte_count;
      } else {
        continue;
      }
    }
    if (success_offset == UINT32_MAX || success_offset >= section->data_size) continue;
    for (cursor = success_offset; cursor < section->data_size; ) {
      SectionDecodeResult decode;
      M68kInstructionIR instruction;
      uint8_t source_kind;
      uint8_t source_reg;
      int16_t slot_disp;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      instruction = decode.instruction;
      if (instruction.byte_count == 0U) break;
      if (instruction_is_register_to_app_slot_store(&instruction, &source_kind, &source_reg, &slot_disp) &&
          source_kind == 1U && source_reg == 0U) {
        set_amiga_base_slot_tag(slots, slot_count, slot_disp, seed_base_name);
        break;
      }
      if (instruction_stops_fallthrough(&instruction)) break;
      cursor += (uint32_t)instruction.byte_count;
    }
  }
}

int resolve_amiga_library_vector_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  const M68kRecoveredPlatformCallIR *recovered;
  const AmigaOsLibraryVectorInfo *entry;
  recovered = find_recovered_platform_call(section_analysis, offset, PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL);
  if (recovered != NULL) {
    load_recovered_platform_call_info(recovered, out_info);
    return 1;
  }
  entry = resolve_amiga_library_vector_entry(ctx, section_analysis, offset, instruction);
  if (entry == NULL) return 0;
  if (out_info != NULL) {
    out_info->kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL;
    out_info->has_symbol_name = 1U;
    snprintf(out_info->symbol_name, sizeof(out_info->symbol_name), "%s", entry->lvo_symbol_name);
  }
  return 1;
}

int resolve_amiga_indexed_library_dispatch_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  const M68kRecoveredPlatformCallIR *recovered;
  const M68kOperandIR *operand = NULL;
  const char *base_name;
  uint8_t base_reg;
  uint8_t index_is_address;
  uint8_t index_reg;
  int32_t disp;
  recovered = find_recovered_platform_call(section_analysis, offset, PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH);
  if (recovered != NULL) {
    load_recovered_platform_call_info(recovered, out_info);
    return 1;
  }
  if (ctx == NULL || section_analysis_context_object(ctx) == NULL || instruction == NULL) return 0;
  if (section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  if (!instruction_is_call_transfer(instruction)) return 0;
  if (!instruction_target_operand_local(instruction, &operand) || operand == NULL) return 0;
  if (!operand_is_brief_indexed_an(operand, &base_reg, &index_is_address, &index_reg, &disp)) return 0;
  if (base_reg != 6U || index_is_address != 0U || disp != 0) return 0;
  base_name = resolve_amiga_library_base_name(ctx, section_analysis, offset, base_reg);
  if (base_name == NULL) return 0;
  if (strcmp(base_name, "DOSBase") != 0) return 0;
  if (out_info != NULL) {
    out_info->kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH;
    out_info->note_kind = M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR;
    out_info->note_reg = index_reg;
    snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", base_name);
  }
  return 1;
}

int resolve_amiga_callback_field_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  const M68kRecoveredPlatformCallIR *recovered;
  const M68kSection *section = section_analysis_context_section(ctx);
  const M68kOperandIR *target_operand = NULL;
  uint8_t target_reg;
  uint32_t cursor;
  uint32_t start;
  int16_t addr_reg_slot_source[8];
  int16_t prev_addr_reg_slot_source[8];
  size_t reg_index;
  recovered = find_recovered_platform_call(section_analysis, offset, PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL);
  if (recovered != NULL) {
    load_recovered_platform_call_info(recovered, out_info);
    return 1;
  }
  if (ctx == NULL || section == NULL || instruction == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  if (!instruction_is_call_transfer(instruction)) return 0;
  if (!instruction_target_operand_local(instruction, &target_operand) || target_operand == NULL) return 0;
  if (!operand_is_indirect_an(target_operand, &target_reg)) return 0;
  for (reg_index = 0U; reg_index < 8U; ++reg_index) addr_reg_slot_source[reg_index] = INT16_MIN;
  start = resolve_analysis_trace_start(ctx, section_analysis, offset);
  if (start == UINT32_MAX || start > offset) return 0;
  for (cursor = start; cursor < offset && cursor < section->data_size; ) {
    SectionDecodeResult decode;
    M68kInstructionIR step;
    const M68kOperandIR *source = NULL;
    uint8_t dest_reg;
    uint8_t written_reg;
    int16_t slot_disp;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    step = decode.instruction;
    if (step.byte_count == 0U || cursor + step.byte_count > offset) break;
    for (reg_index = 0U; reg_index < 8U; ++reg_index) {
      prev_addr_reg_slot_source[reg_index] = addr_reg_slot_source[reg_index];
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_address_reg_approx(&step, written_reg)) {
        addr_reg_slot_source[written_reg] = INT16_MIN;
      }
    }
    if (instruction_is_address_move(&step, &dest_reg, &source) && source != NULL) {
      uint8_t source_reg;
      int16_t field_disp;
      if (operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        addr_reg_slot_source[dest_reg] = slot_disp;
      } else if (source->kind == M68K_ASM_OPERAND_AN && source->value.reg < 8U) {
        addr_reg_slot_source[dest_reg] = prev_addr_reg_slot_source[source->value.reg];
      } else if (operand_is_indirect_disp_an(source, &source_reg, &field_disp) &&
          source_reg < 8U && field_disp == 4 && prev_addr_reg_slot_source[source_reg] == 0x01A2) {
        addr_reg_slot_source[dest_reg] = 0x01A2;
      }
    }
    cursor += (uint32_t)step.byte_count;
  }
  if (addr_reg_slot_source[target_reg] != 0x01A2) return 0;
  if (out_info != NULL) {
    out_info->kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL;
    out_info->note_kind = M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD;
    out_info->note_disp = 0x01A2;
    out_info->note_field_disp = 4;
  }
  return 1;
}

int resolve_amiga_local_wrapper_dispatch_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  const M68kSection *section = section_analysis_context_section(ctx);
  size_t entry_block_index;
  size_t pending[32];
  size_t visited[32];
  size_t pending_count = 0U;
  size_t visit_count = 0U;
  uint32_t target_offset;
  int32_t lvo;
  const AmigaOsLibraryVectorInfo *entry;
  if (ctx == NULL || section_analysis_context_object(ctx) == NULL || section_analysis == NULL || instruction == NULL) return 0;
  if (section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  if (section == NULL) return 0;
  if (!instruction_is_call_transfer(instruction)) return 0;
  if (!instruction_direct_target_local(ctx, instruction, offset, &target_offset)) return 0;
  entry_block_index = section_analysis_find_block_index_containing(section_analysis, target_offset);
  if (entry_block_index == SIZE_MAX) return 0;
  pending[pending_count++] = entry_block_index;
  while (pending_count != 0U && visit_count < (sizeof(visited) / sizeof(visited[0]))) {
    size_t block_index = pending[--pending_count];
    const M68kCfgBlockIR *block;
    uint32_t cursor;
    size_t seen_index;
    int seen = 0;
    size_t edge_index;
    for (seen_index = 0U; seen_index < visit_count; ++seen_index) {
      if (visited[seen_index] == block_index) {
        seen = 1;
        break;
      }
    }
    if (seen || block_index >= section_analysis->block_count) continue;
    visited[visit_count++] = block_index;
    block = &section_analysis->blocks[block_index];
    cursor = block->start_offset < target_offset ? target_offset : block->start_offset;
    while (cursor < block->end_offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U) break;
      if (resolve_amiga_indexed_library_dispatch_info(ctx, section_analysis, cursor, &decode.instruction, NULL))
        goto found_wrapper_dispatch;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    for (edge_index = block->edge_start;
         edge_index < block->edge_start + block->edge_count && pending_count < (sizeof(pending) / sizeof(pending[0]));
         ++edge_index) {
      const M68kCfgEdgeIR *edge = &section_analysis->edges[edge_index];
      if (edge->kind == M68K_CFG_EDGE_CALL || edge->kind == M68K_CFG_EDGE_RETURN) continue;
      if (edge->target_block_index == SIZE_MAX) continue;
      pending[pending_count++] = edge->target_block_index;
    }
  }
  return 0;
found_wrapper_dispatch:
  if (!resolve_local_data_reg_immediate_seed(ctx, section_analysis, offset, 0U, &lvo)) return 0;
  entry = amiga_os_find_library_vector("DOSBase", (int16_t)lvo);
  if (entry == NULL) return 0;
  if (out_info != NULL) {
    out_info->kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH;
    out_info->note_kind = M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL;
    snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", "DOSBase");
    snprintf(out_info->note_symbol_name, sizeof(out_info->note_symbol_name), "%s", entry->lvo_symbol_name);
  }
  return 1;
}

int collect_recovered_amiga_platform_facts(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis) {
    const M68kSection *section = section_analysis_context_section(ctx);
  AmigaBaseSlotTag slots[AMIGA_BASE_SLOT_TAG_CAPACITY] = {{0}};
  uint32_t offset;
  size_t index;
  if (ctx == NULL || section == NULL || section_analysis == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  collect_section_amiga_base_slot_tags(ctx, section_analysis, slots, sizeof(slots) / sizeof(slots[0]));
  for (index = 0U; index < (sizeof(slots) / sizeof(slots[0])); ++index) {
    if (slots[index].base_name == NULL) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_base_slot(section_analysis,
          slots[index].displacement, slots[index].base_name) != 0) {
      return -1;
    }
  }
    for (offset = 0U; offset < section->data_size; ++offset) {
      SectionDecodeResult decode;
      PlatformResolvedIndirectInfo info;
      if (!section_analysis_context_probe_decode(ctx, offset, &decode)) continue;
      if (instruction_mnemonic_is(&decode.instruction, "moveq") &&
          decode.instruction.operand_count == 2U &&
          decode.instruction.operands[0].kind == M68K_ASM_OPERAND_IMM &&
          operand_is_data_reg_direct(&decode.instruction.operands[1], 0U)) {
        uint32_t next_offset = offset + (uint32_t)decode.instruction.byte_count;
        SectionDecodeResult next_decode;
        platform_resolved_indirect_info_init(&info);
        if (next_offset < section->data_size &&
            section_analysis_context_probe_decode(ctx, next_offset, &next_decode) &&
            resolve_amiga_local_wrapper_dispatch_info(ctx, section_analysis, next_offset, &next_decode.instruction, &info) &&
            info.note_symbol_name[0] != '\0') {
          if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis,
                offset, 0U, NULL, M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL,
                info.note_base_name[0] != '\0' ? info.note_base_name : NULL,
                info.note_symbol_name, 0U, INT16_MIN, INT16_MIN, 0U, 0U, 0U) != 0) {
            return -1;
          }
        }
      }
      if (!decode.is_call) continue;
      platform_resolved_indirect_info_init(&info);
      if (platform_resolve_indirect_control(ctx, section_analysis, offset, &decode.instruction, &info) ==
          PLATFORM_RESOLVED_INDIRECT_NONE) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis,
          offset, info.kind, info.has_symbol_name ? info.symbol_name : NULL, info.note_kind,
          info.note_base_name[0] != '\0' ? info.note_base_name : NULL,
          info.note_symbol_name[0] != '\0' ? info.note_symbol_name : NULL,
          info.note_reg, info.note_disp, info.note_field_disp,
          info.note_stack_cleanup_known, info.note_stack_cleanup_bytes, info.note_return_kind) != 0) {
      return -1;
    }
  }
  return 0;
}

PlatformResolvedIndirectKind platform_amiga_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  if (resolve_amiga_library_vector_info(ctx, section_analysis, offset, instruction, out_info))
    return PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL;
  if (resolve_amiga_indexed_library_dispatch_info(ctx, section_analysis, offset, instruction, out_info))
    return PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH;
  if (resolve_amiga_callback_field_info(ctx, section_analysis, offset, instruction, out_info))
    return PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL;
  return PLATFORM_RESOLVED_INDIRECT_NONE;
}

int platform_amiga_collect_recovered_platform_facts(const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *section_analysis) {
  return collect_recovered_amiga_platform_facts(ctx, section_analysis);
}

int platform_amiga_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    PlatformResolvedIndirectInfo *out_info) {
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  return resolve_amiga_local_wrapper_dispatch_info(ctx, section_analysis, offset, instruction, out_info);
}

int platform_amiga_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction) {
  const M68kRecoveredPlatformCallIR *recovered;
  M68kOperandIR *imm_operand;
  if (ctx == NULL || section_analysis == NULL || instruction == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  if (!instruction_mnemonic_is(instruction, "moveq")) return 0;
  if (instruction->operand_count != 2U) return 0;
  if (instruction->operands[0].kind != M68K_ASM_OPERAND_IMM) return 0;
  if (!operand_is_data_reg_direct(&instruction->operands[1], 0U)) return 0;
  recovered = find_any_recovered_platform_call(section_analysis, offset);
  if (recovered == NULL || recovered->kind != 0U ||
      recovered->note_kind != M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL ||
      recovered->note_symbol_name == NULL || recovered->note_symbol_name[0] == '\0') {
    return 0;
  }
  imm_operand = &instruction->operands[0];
  imm_operand->symbol_ref.has_name = 1U;
  imm_operand->symbol_ref.name_is_generated = 0U;
  imm_operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  imm_operand->symbol_ref.addend = 0;
  snprintf(imm_operand->symbol_ref.name, sizeof(imm_operand->symbol_ref.name), "%s", recovered->note_symbol_name);
  return 1;
}
