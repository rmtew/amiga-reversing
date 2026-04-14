#include "platform_file_internal.h"

#define AMIGA_BASE_SLOT_TAG_CAPACITY 64U

typedef struct AmigaTypedSlotTag {
  int16_t displacement;
  const char *type_name;
} AmigaTypedSlotTag;

typedef struct AmigaResolvedAddressRegInfo {
  int16_t slot_disp;
  int16_t field_disp;
  const char *type_name;
  const char *owner_type_name;
} AmigaResolvedAddressRegInfo;

typedef struct AmigaResolvedDataRegInfo {
  int16_t slot_disp;
  int16_t field_disp;
  const char *type_name;
  const char *owner_type_name;
} AmigaResolvedDataRegInfo;

typedef struct AmigaTypedTraceState {
  const char *addr_reg_type_names[8];
  const char *addr_reg_owner_type_names[8];
  const char *data_reg_type_names[8];
  const char *data_reg_owner_type_names[8];
  int16_t addr_reg_slot_source[8];
  int16_t data_reg_slot_source[8];
  int16_t addr_reg_field_disp[8];
  int16_t data_reg_field_disp[8];
  AmigaTypedSlotTag slot_type_names[AMIGA_BASE_SLOT_TAG_CAPACITY];
} AmigaTypedTraceState;

typedef struct AmigaCallEffectRegState {
  const char *data_reg_base_names[8];
  const char *addr_reg_base_names[8];
  const char *data_reg_type_names[8];
  const char *addr_reg_type_names[8];
} AmigaCallEffectRegState;

typedef struct AmigaLocalSuccessSummaryCacheEntry {
  uint8_t state;
  AmigaCallEffectRegState reg_state;
} AmigaLocalSuccessSummaryCacheEntry;

static void format_amiga_slot_struct_type_name(char *buf, size_t buf_size, int16_t displacement);
static void format_amiga_typed_slot_symbol_name(char *buf, size_t buf_size, const char *type_name);
static void format_amiga_typed_slot_symbol_name_for_disp(char *buf, size_t buf_size, const char *type_name,
    int16_t displacement);
static int resolve_amiga_struct_field_symbol_name(const char *type_name, int16_t displacement, char *buf, size_t buf_size);
static const char *resolve_amiga_struct_field_nested_type_name(const char *type_name, int16_t displacement);
static const char *resolve_amiga_base_type_name(const char *base_name);
static void populate_amiga_callback_field_note_symbol(PlatformResolvedIndirectInfo *out_info);
static int resolve_amiga_address_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedAddressRegInfo *out_info);
static int resolve_amiga_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedDataRegInfo *out_info);
static int resolve_preceding_move_source_data_reg(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t dest_reg, uint8_t *out_source_reg);
static int resolve_preceding_field_loaded_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t data_reg, AmigaResolvedDataRegInfo *out_info);
static int resolve_preceding_stack_reloaded_address_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedAddressRegInfo *out_info);
static uint32_t find_amiga_typed_trace_fallback_start(const SectionAnalysisContext *ctx, uint32_t offset);
static int section_analysis_has_amiga_structural_slot_use(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement);
static int load_amiga_recovered_local_success_summary_state(const M68kSectionAnalysisIR *section_analysis,
    uint32_t target_offset, AmigaCallEffectRegState *out_state);
static int resolve_amiga_pre_call_pointer_app_disp(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t call_offset, uint8_t reg_kind, uint8_t reg_index,
    int16_t *out_disp);
static int instruction_preserves_pointer_provenance_local(const M68kInstructionIR *instruction, uint8_t reg_kind,
    uint8_t reg_index);
static int operand_address_reg_index_local(const M68kOperandIR *operand, uint8_t *out_reg);
static int operand_data_reg_index_local(const M68kOperandIR *operand, uint8_t *out_reg);
static int instruction_pushes_data_reg_to_stack_local(const M68kInstructionIR *instruction, uint8_t *out_reg);
static int instruction_pops_data_reg_from_stack_local(const M68kInstructionIR *instruction, uint8_t *out_reg);

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

static void set_amiga_typed_slot_tag(AmigaTypedSlotTag *slots, size_t slot_count, int16_t displacement,
    const char *type_name) {
  size_t index;
  if (slots == NULL || type_name == NULL) return;
  for (index = 0; index < slot_count; ++index) {
    if (slots[index].type_name == NULL || slots[index].displacement == displacement) {
      slots[index].displacement = displacement;
      slots[index].type_name = type_name;
      return;
    }
  }
}

static const char *lookup_amiga_typed_slot_tag(const AmigaTypedSlotTag *slots, size_t slot_count, int16_t displacement) {
  size_t index;
  if (slots == NULL) return NULL;
  for (index = 0; index < slot_count; ++index) {
    if (slots[index].type_name != NULL && slots[index].displacement == displacement) return slots[index].type_name;
  }
  return NULL;
}

static void seed_amiga_base_slot_tags_from_effects(const M68kSectionAnalysisIR *section_analysis,
    AmigaBaseSlotTag *slots, size_t slot_count) {
  size_t index;
  if (section_analysis == NULL || slots == NULL) return;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT || effect->payload.named_base.base_name == NULL) continue;
    set_amiga_base_slot_tag(slots, slot_count, effect->displacement, effect->payload.named_base.base_name);
  }
}

static void seed_amiga_typed_slot_tags_from_effects(const M68kSectionAnalysisIR *section_analysis,
    AmigaTypedSlotTag *slots, size_t slot_count) {
  size_t index;
  if (section_analysis == NULL || slots == NULL) return;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT || effect->payload.typed.type_name == NULL) continue;
    set_amiga_typed_slot_tag(slots, slot_count, effect->displacement, effect->payload.typed.type_name);
  }
}

const char *lookup_recovered_platform_base_slot(const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  AmigaBaseSlotTag slots[AMIGA_BASE_SLOT_TAG_CAPACITY] = {{0}};
  size_t index;
  if (section_analysis == NULL) return NULL;
  seed_amiga_base_slot_tags_from_effects(section_analysis, slots, sizeof(slots) / sizeof(slots[0]));
  {
    const char *effect_name = lookup_amiga_base_slot_tag(slots, sizeof(slots) / sizeof(slots[0]), displacement);
    if (effect_name != NULL) return effect_name;
  }
  for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
    const M68kRecoveredPlatformBaseSlotIR *slot = &section_analysis->recovered_platform_base_slots[index];
    if (slot->displacement == displacement) return slot->base_name;
  }
  return NULL;
}

static const char *lookup_recovered_platform_typed_slot(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement) {
  AmigaTypedSlotTag slots[AMIGA_BASE_SLOT_TAG_CAPACITY] = {{0}};
  if (section_analysis == NULL) return NULL;
  seed_amiga_typed_slot_tags_from_effects(section_analysis, slots, sizeof(slots) / sizeof(slots[0]));
  return lookup_amiga_typed_slot_tag(slots, sizeof(slots) / sizeof(slots[0]), displacement);
}

static int resolve_recovered_platform_typed_slot_field(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement, int16_t *out_slot_disp, const char **out_type_name, const char **out_field_name) {
  size_t index;
  int16_t best_slot_disp = INT16_MIN;
  const char *best_type_name = NULL;
  const char *best_field_name = NULL;
  if (out_slot_disp != NULL) *out_slot_disp = INT16_MIN;
  if (out_type_name != NULL) *out_type_name = NULL;
  if (out_field_name != NULL) *out_field_name = NULL;
  if (section_analysis == NULL || displacement == INT16_MIN) return 0;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    const AmigaOsStructFieldInfo *field;
    int16_t field_disp;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT || effect->payload.typed.type_name == NULL) continue;
    if (effect->displacement == INT16_MIN || effect->displacement > displacement) continue;
    field_disp = (int16_t)(displacement - effect->displacement);
    field = amiga_os_find_struct_field(effect->payload.typed.type_name, field_disp);
    if (field == NULL || field->field_name == NULL || field->field_name[0] == '\0') continue;
    if (best_type_name == NULL || effect->displacement > best_slot_disp) {
      best_slot_disp = effect->displacement;
      best_type_name = effect->payload.typed.type_name;
      best_field_name = field->field_name;
    }
  }
  if (best_type_name == NULL || best_field_name == NULL) return 0;
  if (out_slot_disp != NULL) *out_slot_disp = best_slot_disp;
  if (out_type_name != NULL) *out_type_name = best_type_name;
  if (out_field_name != NULL) *out_field_name = best_field_name;
  return 1;
}

static size_t count_recovered_platform_typed_slot_type_uses(const M68kSectionAnalysisIR *section_analysis,
    const char *type_name) {
  size_t index;
  size_t count = 0U;
  if (section_analysis == NULL || type_name == NULL || type_name[0] == '\0') return 0U;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT || effect->payload.typed.type_name == NULL) continue;
    if (strcmp(effect->payload.typed.type_name, type_name) != 0) continue;
    ++count;
  }
  return count;
}

static const char *lookup_amiga_effect_or_local_typed_slot(const M68kSectionAnalysisIR *section_analysis,
    const AmigaTypedSlotTag *slot_type_names, size_t slot_type_count, int16_t displacement) {
  const char *type_name = lookup_recovered_platform_typed_slot(section_analysis, displacement);
  if (type_name != NULL) return type_name;
  return lookup_amiga_typed_slot_tag(slot_type_names, slot_type_count, displacement);
}

const char *resolve_amiga_app_slot_base_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  (void)ctx;
  return lookup_recovered_platform_base_slot(section_analysis, displacement);
}

int resolve_amiga_app_slot_symbol_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, char *buf, size_t buf_size) {
  const char *base_name;
  const char *type_name;
  int16_t slot_disp;
  const char *field_type_name;
  const char *field_name;
  char slot_symbol_name[64];
  if (buf == NULL || buf_size == 0U) return 0;
  if (resolve_recovered_platform_typed_slot_field(section_analysis, displacement, &slot_disp, &field_type_name,
        &field_name)) {
    if (count_recovered_platform_typed_slot_type_uses(section_analysis, field_type_name) > 1U) {
      format_amiga_typed_slot_symbol_name_for_disp(slot_symbol_name, sizeof(slot_symbol_name), field_type_name, slot_disp);
    } else {
      format_amiga_typed_slot_symbol_name(slot_symbol_name, sizeof(slot_symbol_name), field_type_name);
    }
    snprintf(buf, buf_size, "%s+%s", slot_symbol_name, field_name);
    return 1;
  }
  base_name = lookup_recovered_platform_base_slot(section_analysis, displacement);
  if (base_name != NULL && base_name[0] != '\0') {
    snprintf(buf, buf_size, "app_%s", base_name);
    return 1;
  }
  type_name = lookup_recovered_platform_typed_slot(section_analysis, displacement);
  if (type_name != NULL && type_name[0] != '\0') {
    if (count_recovered_platform_typed_slot_type_uses(section_analysis, type_name) > 1U) {
      format_amiga_typed_slot_symbol_name_for_disp(buf, buf_size, type_name, displacement);
    } else {
      format_amiga_typed_slot_symbol_name(buf, buf_size, type_name);
    }
    return 1;
  }
  if (ctx != NULL && section_analysis_has_amiga_structural_slot_use(section_analysis, displacement)) {
    format_amiga_slot_struct_type_name(buf, buf_size, displacement);
    return 1;
  }
  return 0;
}

int resolve_amiga_app_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, M68kSymbolRefIR *out_symbol_ref) {
  const char *base_name;
  const char *type_name;
  int16_t slot_disp;
  const char *field_type_name;
  const char *field_name;
  if (out_symbol_ref == NULL) return 0;
  m68k_ir_symbol_ref_init(out_symbol_ref);
  if (resolve_recovered_platform_typed_slot_field(section_analysis, displacement, &slot_disp, &field_type_name,
        &field_name)) {
      out_symbol_ref->has_name = 1U;
      if (count_recovered_platform_typed_slot_type_uses(section_analysis, field_type_name) > 1U) {
        format_amiga_typed_slot_symbol_name_for_disp(out_symbol_ref->name, sizeof(out_symbol_ref->name),
          field_type_name, slot_disp);
      } else {
        format_amiga_typed_slot_symbol_name(out_symbol_ref->name, sizeof(out_symbol_ref->name), field_type_name);
      }
      out_symbol_ref->has_symbolic_addend = 1U;
      out_symbol_ref->symbolic_addend_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      out_symbol_ref->symbolic_addend_value = (int32_t)(displacement - slot_disp);
      snprintf(out_symbol_ref->symbolic_addend_name, sizeof(out_symbol_ref->symbolic_addend_name), "%s", field_name);
      return 1;
  }
  base_name = lookup_recovered_platform_base_slot(section_analysis, displacement);
  if (base_name != NULL && base_name[0] != '\0') {
    out_symbol_ref->has_name = 1U;
    snprintf(out_symbol_ref->name, sizeof(out_symbol_ref->name), "app_%s", base_name);
    return 1;
  }
  type_name = lookup_recovered_platform_typed_slot(section_analysis, displacement);
  if (type_name != NULL && type_name[0] != '\0') {
    out_symbol_ref->has_name = 1U;
    if (count_recovered_platform_typed_slot_type_uses(section_analysis, type_name) > 1U) {
      format_amiga_typed_slot_symbol_name_for_disp(out_symbol_ref->name, sizeof(out_symbol_ref->name), type_name,
        displacement);
    } else {
      format_amiga_typed_slot_symbol_name(out_symbol_ref->name, sizeof(out_symbol_ref->name), type_name);
    }
    return 1;
  }
  if (ctx != NULL && section_analysis_has_amiga_structural_slot_use(section_analysis, displacement)) {
    out_symbol_ref->has_name = 1U;
    format_amiga_slot_struct_type_name(out_symbol_ref->name, sizeof(out_symbol_ref->name), displacement);
    return 1;
  }
  return 0;
}

int resolve_amiga_app_slot_value_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, M68kSymbolRefIR *out_symbol_ref) {
  const char *type_name;
  const AmigaOsStructFieldInfo *field;
  if (out_symbol_ref == NULL) return 0;
  if (!resolve_amiga_app_slot_symbol_ref(ctx, section_analysis, displacement, out_symbol_ref)) return 0;
  type_name = lookup_recovered_platform_typed_slot(section_analysis, displacement);
  if (type_name == NULL || type_name[0] == '\0') return 1;
  field = amiga_os_find_struct_field(type_name, 0);
  if (field == NULL || field->field_name == NULL || field->field_name[0] == '\0') return 1;
  out_symbol_ref->has_symbolic_addend = 1U;
  out_symbol_ref->symbolic_addend_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  out_symbol_ref->symbolic_addend_value = 0;
  snprintf(out_symbol_ref->symbolic_addend_name, sizeof(out_symbol_ref->symbolic_addend_name), "%s",
    field->field_name);
  return 1;
}

static void apply_recovered_amiga_platform_effects(const M68kSectionAnalysisIR *section_analysis, uint32_t offset,
    const char **data_reg_base_names, const char **addr_reg_base_names, const char **data_reg_type_names,
    const char **addr_reg_type_names, AmigaBaseSlotTag *slot_base_names, size_t slot_base_count,
    AmigaTypedSlotTag *slot_type_names, size_t slot_type_count) {
  const M68kRecoveredPlatformEffectIR *effect;
  if (section_analysis == NULL) return;
  for (effect = find_recovered_platform_effect(section_analysis, offset, M68K_PLATFORM_EFFECT_SET_BASE_REG);
       effect != NULL;
       effect = NULL) {
    const char *base_type_name;
    if (effect->payload.named_base.base_name == NULL) break;
    base_type_name = resolve_amiga_base_type_name(effect->payload.named_base.base_name);
    if (effect->reg_kind == 1U && data_reg_base_names != NULL && effect->reg_index < 8U) {
      data_reg_base_names[effect->reg_index] = effect->payload.named_base.base_name;
      if (data_reg_type_names != NULL && data_reg_type_names[effect->reg_index] == NULL) {
        data_reg_type_names[effect->reg_index] = base_type_name;
      }
    } else if (effect->reg_kind == 2U && addr_reg_base_names != NULL && effect->reg_index < 8U) {
      addr_reg_base_names[effect->reg_index] = effect->payload.named_base.base_name;
      if (addr_reg_type_names != NULL && addr_reg_type_names[effect->reg_index] == NULL) {
        addr_reg_type_names[effect->reg_index] = base_type_name;
      }
    }
  }
  for (effect = find_recovered_platform_effect(section_analysis, offset, M68K_PLATFORM_EFFECT_SET_TYPED_REG);
       effect != NULL;
       effect = NULL) {
    if (effect->payload.typed.type_name == NULL) break;
    if (effect->reg_kind == 1U && data_reg_type_names != NULL && effect->reg_index < 8U) {
      data_reg_type_names[effect->reg_index] = effect->payload.typed.type_name;
    } else if (effect->reg_kind == 2U && addr_reg_type_names != NULL && effect->reg_index < 8U) {
      addr_reg_type_names[effect->reg_index] = effect->payload.typed.type_name;
    }
  }
  for (effect = find_recovered_platform_effect(section_analysis, offset, M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT);
       effect != NULL;
       effect = NULL) {
    if (effect->payload.named_base.base_name == NULL || slot_base_names == NULL) break;
    set_amiga_base_slot_tag(slot_base_names, slot_base_count, effect->displacement, effect->payload.named_base.base_name);
  }
  for (effect = find_recovered_platform_effect(section_analysis, offset, M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT);
       effect != NULL;
       effect = NULL) {
    if (effect->payload.typed.type_name == NULL || slot_type_names == NULL) break;
    set_amiga_typed_slot_tag(slot_type_names, slot_type_count, effect->displacement, effect->payload.typed.type_name);
  }
}

static void seed_amiga_effect_state_from_preceding_fallthrough(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t start, const char **data_reg_base_names,
    const char **addr_reg_base_names, const char **data_reg_type_names, const char **addr_reg_type_names,
    AmigaBaseSlotTag *slot_base_names, size_t slot_base_count, AmigaTypedSlotTag *slot_type_names,
    size_t slot_type_count) {
  uint32_t low;
  uint32_t candidate_start;
  uint32_t best_prev_offset = UINT32_MAX;
  M68kInstructionIR best_prev_instruction;
  int have_best = 0;
  if (ctx == NULL || section_analysis == NULL || start == 0U) return;
  low = start > 32U ? (start - 32U) : 0U;
  for (candidate_start = low; candidate_start < start; ++candidate_start) {
    uint32_t cursor = candidate_start;
    uint32_t prev_offset = UINT32_MAX;
    M68kInstructionIR prev_instruction;
    int have_prev = 0;
    while (cursor < start) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U) break;
      if (cursor + (uint32_t)decode.instruction.byte_count > start) break;
      prev_offset = cursor;
      prev_instruction = decode.instruction;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (cursor != start || !have_prev || instruction_stops_fallthrough(&prev_instruction)) continue;
    if (!have_best || prev_offset > best_prev_offset) {
      best_prev_offset = prev_offset;
      best_prev_instruction = prev_instruction;
      have_best = 1;
    }
  }
  if (!have_best) return;
  apply_recovered_amiga_platform_effects(section_analysis, best_prev_offset,
    data_reg_base_names, addr_reg_base_names, data_reg_type_names, addr_reg_type_names,
    slot_base_names, slot_base_count, slot_type_names, slot_type_count);
}

static int parse_amiga_register_name(const char *name, uint8_t *out_reg_kind, uint8_t *out_reg_index) {
  if (name == NULL || out_reg_kind == NULL || out_reg_index == NULL) return 0;
  if ((name[0] == 'D' || name[0] == 'd') && name[1] >= '0' && name[1] <= '7' && name[2] == '\0') {
    *out_reg_kind = 1U;
    *out_reg_index = (uint8_t)(name[1] - '0');
    return 1;
  }
  if ((name[0] == 'A' || name[0] == 'a') && name[1] >= '0' && name[1] <= '7' && name[2] == '\0') {
    *out_reg_kind = 2U;
    *out_reg_index = (uint8_t)(name[1] - '0');
    return 1;
  }
  return 0;
}

static void format_amiga_slot_struct_type_name(char *buf, size_t buf_size, int16_t displacement) {
  if (buf == NULL || buf_size == 0U) return;
  if (displacement == INT16_MIN) {
    buf[0] = '\0';
    return;
  }
  snprintf(buf, buf_size, "app_slot_%04X", (unsigned)(uint16_t)displacement);
}

static void format_amiga_typed_slot_symbol_name(char *buf, size_t buf_size, const char *type_name) {
  if (buf == NULL || buf_size == 0U) return;
  if (type_name == NULL || type_name[0] == '\0') {
    buf[0] = '\0';
    return;
  }
  snprintf(buf, buf_size, "app_%s", type_name);
}

static void format_amiga_typed_slot_symbol_name_for_disp(char *buf, size_t buf_size, const char *type_name,
    int16_t displacement) {
  if (buf == NULL || buf_size == 0U) return;
  if (type_name == NULL || type_name[0] == '\0') {
    buf[0] = '\0';
    return;
  }
  snprintf(buf, buf_size, "app_%s_%04X", type_name, (unsigned)(uint16_t)displacement);
}

static int resolve_amiga_struct_field_symbol_name(const char *type_name, int16_t displacement, char *buf,
    size_t buf_size) {
  const AmigaOsStructFieldInfo *field;
  if (type_name == NULL || buf == NULL || buf_size == 0U) return 0;
  field = amiga_os_find_struct_field(type_name, displacement);
  if (field != NULL && field->field_name != NULL && field->field_name[0] != '\0') {
    snprintf(buf, buf_size, "%s", field->field_name);
    return 1;
  }
  return 0;
}

static const char *resolve_amiga_struct_field_nested_type_name(const char *type_name, int16_t displacement) {
  const AmigaOsStructFieldInfo *field;
  if (type_name == NULL) return NULL;
  field = amiga_os_find_struct_field(type_name, displacement);
  if (field == NULL || field->nested_type_name == NULL || field->nested_type_name[0] == '\0') return NULL;
  return field->nested_type_name;
}

static const char *resolve_amiga_base_type_name(const char *base_name) {
  if (base_name == NULL || base_name[0] == '\0') return NULL;
  if (strcmp(base_name, AMIGA_APP_BASE_TAG) == 0) return NULL;
  return "LIB";
}

static void populate_amiga_callback_field_note_symbol(PlatformResolvedIndirectInfo *out_info) {
  char field_name[64];
  if (out_info == NULL) return;
  if (out_info->note_kind != M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD) return;
  if (out_info->note_base_name[0] == '\0' || out_info->note_field_disp == INT16_MIN) return;
  if (!resolve_amiga_struct_field_symbol_name(out_info->note_base_name, out_info->note_field_disp,
      field_name, sizeof(field_name))) {
    return;
  }
  snprintf(out_info->note_symbol_name, sizeof(out_info->note_symbol_name), "%s", field_name);
}

static int operand_address_reg_index_local(const M68kOperandIR *operand, uint8_t *out_reg) {
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

static int operand_data_reg_index_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || out_reg == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) {
    *out_reg = operand->value.reg;
    return 1;
  }
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 0U) {
    *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static int instruction_pushes_data_reg_to_stack_local(const M68kInstructionIR *instruction, uint8_t *out_reg) {
  uint8_t reg_index;
  if (out_reg != NULL) *out_reg = 0U;
  if (instruction == NULL || instruction->operand_count != 2U) return 0;
  if (!instruction_mnemonic_is(instruction, "move")) return 0;
  if (!operand_data_reg_index_local(&instruction->operands[0], &reg_index)) return 0;
  if (instruction->operands[1].kind != M68K_ASM_OPERAND_PREDEC) return 0;
  if (instruction->operands[1].value.ea_reg != 7U) return 0;
  if (out_reg != NULL) *out_reg = reg_index;
  return 1;
}

static int instruction_pops_data_reg_from_stack_local(const M68kInstructionIR *instruction, uint8_t *out_reg) {
  const M68kOperandIR *source = NULL;
  if (out_reg != NULL) *out_reg = 0U;
  if (instruction == NULL || instruction->operand_count != 2U) return 0;
  if (!instruction_is_data_move(instruction, out_reg, &source) || source == NULL) return 0;
  if (source->kind != M68K_ASM_OPERAND_POSTINC) return 0;
  return source->value.ea_reg == 7U;
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
      } else if ((source->kind == M68K_ASM_OPERAND_EA || source->kind == M68K_ASM_OPERAND_BF_EA) &&
          source->value.ea_mode == 7U && source->value.ea_reg == 2U) {
        source_target = (uint32_t)((int32_t)cursor + 2 + (int32_t)source->value.value);
        addr_reg_base_names[dest_reg] = NULL;
        addr_reg_seed_base_names[dest_reg] = read_amiga_library_seed_name(section, source_target);
        addr_reg_app_disp[dest_reg] = INT16_MIN;
      } else if (metadata != NULL &&
          instruction_render_operand_target(&instruction, metadata, 0U, cursor,
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

static int resolve_amiga_pre_call_pointer_app_disp(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t call_offset, uint8_t reg_kind, uint8_t reg_index,
    int16_t *out_disp) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t cursor;
  uint32_t start;
  int16_t addr_reg_app_disp[8];
  int16_t data_reg_app_disp[8];
  int16_t prev_addr_reg_app_disp[8];
  int16_t prev_data_reg_app_disp[8];
  uint8_t written_reg;
  if (out_disp != NULL) *out_disp = INT16_MIN;
  if (ctx == NULL || section == NULL || section_analysis == NULL || reg_index >= 8U) return 0;
  for (written_reg = 0U; written_reg < 8U; ++written_reg) {
    addr_reg_app_disp[written_reg] = INT16_MIN;
    data_reg_app_disp[written_reg] = INT16_MIN;
  }
  start = resolve_analysis_trace_start(ctx, section_analysis, call_offset);
  if (start == UINT32_MAX) return 0;
  {
    uint32_t fallback_start = find_amiga_typed_trace_fallback_start(ctx, call_offset);
    if (fallback_start != UINT32_MAX && fallback_start < start) start = fallback_start;
  }
  cursor = start;
  while (cursor < call_offset && cursor < section->data_size) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    const M68kOperandIR *source = NULL;
    uint8_t dest_reg;
    uint8_t source_reg;
    int16_t slot_disp;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > call_offset) break;
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      prev_addr_reg_app_disp[written_reg] = addr_reg_app_disp[written_reg];
      prev_data_reg_app_disp[written_reg] = data_reg_app_disp[written_reg];
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_address_reg_approx(&instruction, written_reg)) addr_reg_app_disp[written_reg] = INT16_MIN;
      if (instruction_writes_data_reg_approx(&instruction, written_reg)) data_reg_app_disp[written_reg] = INT16_MIN;
    }
    if (instruction_is_address_move(&instruction, &dest_reg, &source)) {
      if (source != NULL && operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
        addr_reg_app_disp[dest_reg] = addr_reg_app_disp[source_reg];
      } else if (source != NULL && operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
        addr_reg_app_disp[dest_reg] = data_reg_app_disp[source_reg];
      } else if (source != NULL && operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        addr_reg_app_disp[dest_reg] = slot_disp;
      }
    } else if (instruction_is_data_move(&instruction, &dest_reg, &source)) {
      if (source != NULL && operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
        data_reg_app_disp[dest_reg] = addr_reg_app_disp[source_reg];
      } else if (source != NULL && operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
        data_reg_app_disp[dest_reg] = data_reg_app_disp[source_reg];
      } else if (source != NULL && operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        data_reg_app_disp[dest_reg] = slot_disp;
      }
    } else if (instruction_mnemonic_is(&instruction, "lea") &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[1], &dest_reg) &&
        operand_is_app_base_disp_ea(&instruction.operands[0], 6U, &slot_disp)) {
      addr_reg_app_disp[dest_reg] = slot_disp;
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_address_reg_approx(&instruction, written_reg) &&
          addr_reg_app_disp[written_reg] == INT16_MIN &&
          instruction_preserves_pointer_provenance_local(&instruction, 2U, written_reg)) {
        addr_reg_app_disp[written_reg] = prev_addr_reg_app_disp[written_reg];
      }
      if (instruction_writes_data_reg_approx(&instruction, written_reg) &&
          data_reg_app_disp[written_reg] == INT16_MIN &&
          instruction_preserves_pointer_provenance_local(&instruction, 1U, written_reg)) {
        data_reg_app_disp[written_reg] = prev_data_reg_app_disp[written_reg];
      }
    }
    cursor += (uint32_t)instruction.byte_count;
  }
  if (reg_kind == 1U) {
    AmigaResolvedDataRegInfo info;
    if (resolve_amiga_data_reg_info(ctx, section_analysis, call_offset, reg_index, 1, &info) &&
        info.slot_disp != INT16_MIN) {
      if (out_disp != NULL) *out_disp = info.slot_disp;
      return 1;
    }
    if (out_disp != NULL) *out_disp = data_reg_app_disp[reg_index];
    return data_reg_app_disp[reg_index] != INT16_MIN;
  }
  if (reg_kind == 2U) {
    AmigaResolvedAddressRegInfo info;
    if (resolve_amiga_address_reg_info(ctx, section_analysis, call_offset, reg_index, 1, &info) &&
        info.slot_disp != INT16_MIN) {
      if (out_disp != NULL) *out_disp = info.slot_disp;
      return 1;
    }
    if (out_disp != NULL) *out_disp = addr_reg_app_disp[reg_index];
    return addr_reg_app_disp[reg_index] != INT16_MIN;
  }
  return 0;
}

static int instruction_preserves_pointer_provenance_local(const M68kInstructionIR *instruction, uint8_t reg_kind,
    uint8_t reg_index) {
  const char *mnemonic;
  const M68kOperandIR *dest;
  if (instruction == NULL || instruction->operand_count == 0U) return 0;
  mnemonic = instruction->mnemonic;
  if (mnemonic == NULL) return 0;
  dest = &instruction->operands[instruction->operand_count - 1U];
  if (reg_kind == 1U) {
    if (!operand_is_data_reg_direct(dest, reg_index)) return 0;
  } else if (reg_kind == 2U) {
    {
      uint8_t dest_reg;
      if (!operand_address_reg_index_local(dest, &dest_reg) || dest_reg != reg_index) return 0;
    }
  } else {
    return 0;
  }
  return instruction_mnemonic_is(instruction, "add") ||
    instruction_mnemonic_is(instruction, "addi") ||
    instruction_mnemonic_is(instruction, "addq") ||
    instruction_mnemonic_is(instruction, "sub") ||
    instruction_mnemonic_is(instruction, "subi") ||
    instruction_mnemonic_is(instruction, "subq") ||
    instruction_mnemonic_is(instruction, "and") ||
    instruction_mnemonic_is(instruction, "andi") ||
    instruction_mnemonic_is(instruction, "or") ||
    instruction_mnemonic_is(instruction, "ori") ||
    instruction_mnemonic_is(instruction, "eor") ||
    instruction_mnemonic_is(instruction, "eori");
}

static int operand_is_immediate_source_local(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  return operand->kind == M68K_ASM_OPERAND_IMM ||
    ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 7U && operand->value.ea_reg == 4U);
}

static void amiga_call_effect_reg_state_clear(AmigaCallEffectRegState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void amiga_call_effect_reg_state_copy(AmigaCallEffectRegState *dst, const AmigaCallEffectRegState *src) {
  if (dst == NULL || src == NULL) return;
  *dst = *src;
}

static const char *join_consistent_name_local(const char *existing, const char *candidate) {
  if (existing == NULL && candidate == NULL) return NULL;
  if (existing == NULL || candidate == NULL) return NULL;
  if (existing == candidate || strcmp(existing, candidate) == 0) return existing;
  return NULL;
}

static int amiga_call_effect_reg_state_join(AmigaCallEffectRegState *dst, const AmigaCallEffectRegState *src) {
  int changed = 0;
  uint8_t reg;
  if (dst == NULL || src == NULL) return 0;
  for (reg = 0U; reg < 8U; ++reg) {
    const char *joined;
    joined = join_consistent_name_local(dst->data_reg_base_names[reg], src->data_reg_base_names[reg]);
    if (joined != dst->data_reg_base_names[reg]) {
      dst->data_reg_base_names[reg] = joined;
      changed = 1;
    }
    joined = join_consistent_name_local(dst->addr_reg_base_names[reg], src->addr_reg_base_names[reg]);
    if (joined != dst->addr_reg_base_names[reg]) {
      dst->addr_reg_base_names[reg] = joined;
      changed = 1;
    }
    joined = join_consistent_name_local(dst->data_reg_type_names[reg], src->data_reg_type_names[reg]);
    if (joined != dst->data_reg_type_names[reg]) {
      dst->data_reg_type_names[reg] = joined;
      changed = 1;
    }
    joined = join_consistent_name_local(dst->addr_reg_type_names[reg], src->addr_reg_type_names[reg]);
    if (joined != dst->addr_reg_type_names[reg]) {
      dst->addr_reg_type_names[reg] = joined;
      changed = 1;
    }
  }
  return changed;
}

static void clear_all_amiga_call_effect_regs(AmigaCallEffectRegState *state) {
  uint8_t reg;
  if (state == NULL) return;
  for (reg = 0U; reg < 8U; ++reg) {
    state->data_reg_base_names[reg] = NULL;
    state->addr_reg_base_names[reg] = NULL;
    state->data_reg_type_names[reg] = NULL;
    state->addr_reg_type_names[reg] = NULL;
  }
}

static void apply_recovered_amiga_platform_effects_to_call_state(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, AmigaCallEffectRegState *state) {
  size_t index;
  if (section_analysis == NULL || state == NULL) return;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->offset != offset) continue;
    if (effect->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG && effect->payload.named_base.base_name != NULL) {
      if (effect->reg_kind == 1U && effect->reg_index < 8U) {
        state->data_reg_base_names[effect->reg_index] = effect->payload.named_base.base_name;
        if (state->data_reg_type_names[effect->reg_index] == NULL)
          state->data_reg_type_names[effect->reg_index] = resolve_amiga_base_type_name(effect->payload.named_base.base_name);
      } else if (effect->reg_kind == 2U && effect->reg_index < 8U) {
        state->addr_reg_base_names[effect->reg_index] = effect->payload.named_base.base_name;
        if (state->addr_reg_type_names[effect->reg_index] == NULL)
          state->addr_reg_type_names[effect->reg_index] = resolve_amiga_base_type_name(effect->payload.named_base.base_name);
      }
    } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG && effect->payload.typed.type_name != NULL) {
      if (effect->reg_kind == 1U && effect->reg_index < 8U) {
        state->data_reg_type_names[effect->reg_index] = effect->payload.typed.type_name;
      } else if (effect->reg_kind == 2U && effect->reg_index < 8U) {
        state->addr_reg_type_names[effect->reg_index] = effect->payload.typed.type_name;
      }
    }
  }
}

static void update_amiga_call_effect_reg_state_for_instruction(const M68kInstructionIR *instruction,
    const AmigaCallEffectRegState *prev_state, AmigaCallEffectRegState *state) {
  uint8_t reg_index;
  uint8_t dest_reg;
  uint8_t source_reg;
  const M68kOperandIR *source = NULL;
  if (instruction == NULL || prev_state == NULL || state == NULL) return;
  amiga_call_effect_reg_state_copy(state, prev_state);
  for (reg_index = 0U; reg_index < 8U; ++reg_index) {
    if (instruction_writes_data_reg_approx(instruction, reg_index)) {
      state->data_reg_base_names[reg_index] = NULL;
      state->data_reg_type_names[reg_index] = NULL;
    }
    if (instruction_writes_address_reg_approx(instruction, reg_index)) {
      state->addr_reg_base_names[reg_index] = NULL;
      state->addr_reg_type_names[reg_index] = NULL;
    }
  }
  if (instruction_is_data_move(instruction, &dest_reg, &source) && source != NULL) {
    if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
      state->data_reg_base_names[dest_reg] = prev_state->data_reg_base_names[source_reg];
      state->data_reg_type_names[dest_reg] = prev_state->data_reg_type_names[source_reg];
    } else if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
      state->data_reg_base_names[dest_reg] = prev_state->addr_reg_base_names[source_reg];
      state->data_reg_type_names[dest_reg] = prev_state->addr_reg_type_names[source_reg];
    }
  }
  if (instruction_is_address_move(instruction, &dest_reg, &source) && source != NULL) {
    if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
      state->addr_reg_base_names[dest_reg] = prev_state->addr_reg_base_names[source_reg];
      state->addr_reg_type_names[dest_reg] = prev_state->addr_reg_type_names[source_reg];
    } else if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
      state->addr_reg_base_names[dest_reg] = prev_state->data_reg_base_names[source_reg];
      state->addr_reg_type_names[dest_reg] = prev_state->data_reg_type_names[source_reg];
    }
  }
}

static int seed_amiga_call_effect_reg_state_from_call_entry(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const AmigaOsLibraryVectorInfo *call_entry,
    AmigaCallEffectRegState *out_state) {
  const char *returned_base_name = NULL;
  uint8_t effect_reg_kind;
  uint8_t effect_reg_index;
  int changed = 0;
  if (out_state != NULL) amiga_call_effect_reg_state_clear(out_state);
  if (ctx == NULL || section_analysis == NULL || call_entry == NULL || out_state == NULL) return 0;
  if (call_entry->returns_base_reg_name != NULL && call_entry->returns_base_name_reg_name != NULL &&
      parse_amiga_register_name(call_entry->returns_base_reg_name, &effect_reg_kind, &effect_reg_index)) {
    if (_stricmp(call_entry->returns_base_name_reg_name, "A0") == 0) {
      trace_amiga_call_setup(ctx, section_analysis, offset, &returned_base_name, NULL, NULL);
    } else if (_stricmp(call_entry->returns_base_name_reg_name, "A1") == 0) {
      trace_amiga_call_setup(ctx, section_analysis, offset, NULL, NULL, &returned_base_name);
    }
    if (returned_base_name != NULL) {
      if (effect_reg_kind == 1U && effect_reg_index < 8U) {
        out_state->data_reg_base_names[effect_reg_index] = returned_base_name;
        out_state->data_reg_type_names[effect_reg_index] = resolve_amiga_base_type_name(returned_base_name);
      } else if (effect_reg_kind == 2U && effect_reg_index < 8U) {
        out_state->addr_reg_base_names[effect_reg_index] = returned_base_name;
        out_state->addr_reg_type_names[effect_reg_index] = resolve_amiga_base_type_name(returned_base_name);
      }
      changed = 1;
    }
  }
  if (call_entry->output_reg_name != NULL && call_entry->output_struct_name != NULL &&
      parse_amiga_register_name(call_entry->output_reg_name, &effect_reg_kind, &effect_reg_index)) {
    if (effect_reg_kind == 1U && effect_reg_index < 8U) {
      out_state->data_reg_type_names[effect_reg_index] = call_entry->output_struct_name;
      changed = 1;
    } else if (effect_reg_kind == 2U && effect_reg_index < 8U) {
      out_state->addr_reg_type_names[effect_reg_index] = call_entry->output_struct_name;
      changed = 1;
    }
  }
  return changed;
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
  {
    uint32_t fallback_start = find_amiga_typed_trace_fallback_start(ctx, offset);
    if (fallback_start != UINT32_MAX && fallback_start < start) start = fallback_start;
  }
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
          operand_is_immediate_source_local(&instruction.operands[0])) {
        value = (int32_t)m68k_sign_extend32(instruction.operands[0].value.value, 8U);
        have_value = 1;
      } else if (instruction_is_data_move(&instruction, &dest_reg, &source) &&
          dest_reg == reg && operand_is_immediate_source_local(source)) {
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

static int append_amiga_post_call_slot_effects(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint32_t instruction_size, const AmigaCallEffectRegState *seed_state) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t cursor;
  AmigaCallEffectRegState state;
  if (ctx == NULL || section_analysis == NULL || section == NULL || seed_state == NULL) return 0;
  amiga_call_effect_reg_state_copy(&state, seed_state);
  cursor = offset + instruction_size;
  while (cursor < section->data_size) {
    SectionDecodeResult next_decode;
    M68kInstructionIR next_instruction;
    uint8_t next_source_kind;
    uint8_t next_source_reg;
    uint8_t dest_reg;
    uint8_t source_reg;
    const M68kOperandIR *source = NULL;
    int16_t next_slot_disp;
    uint8_t reg_index;
    AmigaCallEffectRegState prev_state;
    if (!section_analysis_context_probe_decode(ctx, cursor, &next_decode)) break;
    next_instruction = next_decode.instruction;
    if (next_instruction.byte_count == 0U) break;
    if (next_decode.is_call) break;
    if (instruction_is_register_to_app_slot_store(&next_instruction, &next_source_kind, &next_source_reg,
          &next_slot_disp)) {
      const char *stored_base_name = NULL;
      const char *stored_type_name = NULL;
      if (next_source_kind == 1U && next_source_reg < 8U) {
        stored_base_name = state.data_reg_base_names[next_source_reg];
        stored_type_name = state.data_reg_type_names[next_source_reg];
      } else if (next_source_kind == 2U && next_source_reg < 8U) {
        stored_base_name = state.addr_reg_base_names[next_source_reg];
        stored_type_name = state.addr_reg_type_names[next_source_reg];
      }
      if (stored_base_name != NULL &&
          m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, cursor,
            M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT, 0U, 0U, next_slot_disp, INT16_MIN,
            stored_base_name, NULL, NULL) != 0) {
        return -1;
      }
      if (stored_type_name != NULL &&
          m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, cursor,
            M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT, 0U, 0U, next_slot_disp, INT16_MIN,
            NULL, NULL, stored_type_name) != 0) {
        return -1;
      }
    }
    amiga_call_effect_reg_state_copy(&prev_state, &state);
    (void)dest_reg;
    (void)source_reg;
    (void)source;
    (void)reg_index;
    update_amiga_call_effect_reg_state_for_instruction(&next_instruction, &prev_state, &state);
    if (instruction_stops_fallthrough(&next_instruction)) break;
    cursor += (uint32_t)next_instruction.byte_count;
  }
  return 0;
}

static void clear_local_data_const_state(uint8_t *known, int32_t *values) {
  size_t index;
  if (known == NULL || values == NULL) return;
  for (index = 0U; index < 8U; ++index) {
    known[index] = 0U;
    values[index] = 0;
  }
}

static void copy_local_data_const_state(uint8_t *dst_known, int32_t *dst_values,
    const uint8_t *src_known, const int32_t *src_values) {
  if (dst_known == NULL || dst_values == NULL || src_known == NULL || src_values == NULL) return;
  memcpy(dst_known, src_known, 8U * sizeof(*dst_known));
  memcpy(dst_values, src_values, 8U * sizeof(*dst_values));
}

static int join_local_data_const_state(uint8_t *dst_known, int32_t *dst_values,
    const uint8_t *src_known, const int32_t *src_values) {
  int changed = 0;
  uint8_t reg;
  if (dst_known == NULL || dst_values == NULL || src_known == NULL || src_values == NULL) return 0;
  for (reg = 0U; reg < 8U; ++reg) {
    if (!dst_known[reg]) continue;
    if (!src_known[reg] || dst_values[reg] != src_values[reg]) {
      dst_known[reg] = 0U;
      dst_values[reg] = 0;
      changed = 1;
    }
  }
  return changed;
}

static void update_local_data_const_state_for_instruction(const M68kInstructionIR *instruction,
    const uint8_t *prev_known, const int32_t *prev_values, uint8_t *known, int32_t *values) {
  uint8_t reg;
  uint8_t dest_reg;
  uint8_t source_reg;
  const M68kOperandIR *source = NULL;
  if (instruction == NULL || prev_known == NULL || prev_values == NULL || known == NULL || values == NULL) return;
  copy_local_data_const_state(known, values, prev_known, prev_values);
  for (reg = 0U; reg < 8U; ++reg) {
    if (instruction_writes_data_reg_approx(instruction, reg)) {
      known[reg] = 0U;
      values[reg] = 0;
    }
  }
  if (instruction_mnemonic_is(instruction, "moveq") &&
      instruction->operand_count == 2U &&
      operand_is_immediate_source_local(&instruction->operands[0]) &&
      operand_data_reg_index_local(&instruction->operands[1], &dest_reg) &&
      dest_reg < 8U) {
    known[dest_reg] = 1U;
    values[dest_reg] = (int32_t)m68k_sign_extend32(instruction->operands[0].value.value, 8U);
    return;
  }
  if (instruction_is_data_move(instruction, &dest_reg, &source) && source != NULL && dest_reg < 8U) {
    if (operand_is_immediate_source_local(source)) {
      known[dest_reg] = 1U;
      values[dest_reg] = (int32_t)source->value.value;
    } else if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U && prev_known[source_reg]) {
      known[dest_reg] = 1U;
      values[dest_reg] = prev_values[source_reg];
    }
  } else if (instruction_mnemonic_is(instruction, "clr") &&
      instruction->operand_count != 0U &&
      operand_data_reg_index_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg) &&
      dest_reg < 8U) {
    known[dest_reg] = 1U;
    values[dest_reg] = 0;
  }
}

static int summarize_amiga_direct_local_success_outputs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t target_offset,
    AmigaLocalSuccessSummaryCacheEntry *cache, size_t cache_count, AmigaCallEffectRegState *out_summary) {
  const M68kSection *section = section_analysis_context_section(ctx);
  size_t entry_block_index;
  AmigaCallEffectRegState *entry_states = NULL;
  uint8_t (*entry_const_known)[8] = NULL;
  int32_t (*entry_const_values)[8] = NULL;
  uint8_t *entry_known = NULL;
  size_t *pending = NULL;
  size_t pending_count = 0U;
  size_t pending_capacity = 0U;
  int have_summary = 0;
  int result = 0;
  if (out_summary != NULL) amiga_call_effect_reg_state_clear(out_summary);
  if (ctx == NULL || section_analysis == NULL || section == NULL || out_summary == NULL ||
      cache == NULL || cache_count == 0U) {
    return 0;
  }
  entry_block_index = section_analysis_find_block_index_containing(section_analysis, target_offset);
  if (entry_block_index == SIZE_MAX || entry_block_index >= section_analysis->block_count || entry_block_index >= cache_count)
    return 0;
  if (cache[entry_block_index].state == 2U) {
    amiga_call_effect_reg_state_copy(out_summary, &cache[entry_block_index].reg_state);
    return cache[entry_block_index].reg_state.data_reg_base_names[0] != NULL ||
      cache[entry_block_index].reg_state.addr_reg_base_names[0] != NULL ||
      cache[entry_block_index].reg_state.data_reg_type_names[0] != NULL ||
      cache[entry_block_index].reg_state.addr_reg_type_names[0] != NULL ||
      cache[entry_block_index].reg_state.data_reg_base_names[1] != NULL ||
      cache[entry_block_index].reg_state.data_reg_type_names[1] != NULL ||
      cache[entry_block_index].reg_state.data_reg_base_names[2] != NULL ||
      cache[entry_block_index].reg_state.data_reg_type_names[2] != NULL ||
      cache[entry_block_index].reg_state.addr_reg_base_names[1] != NULL ||
      cache[entry_block_index].reg_state.addr_reg_type_names[1] != NULL;
  }
  if (cache[entry_block_index].state == 1U) return 0;
  cache[entry_block_index].state = 1U;
  entry_states = (AmigaCallEffectRegState *)calloc(section_analysis->block_count, sizeof(*entry_states));
  entry_const_known = (uint8_t (*)[8])calloc(section_analysis->block_count, sizeof(*entry_const_known));
  entry_const_values = (int32_t (*)[8])calloc(section_analysis->block_count, sizeof(*entry_const_values));
  entry_known = (uint8_t *)calloc(section_analysis->block_count, sizeof(*entry_known));
  pending_capacity = section_analysis->block_count != 0U ? section_analysis->block_count : 1U;
  pending = (size_t *)malloc(sizeof(*pending) * pending_capacity);
  if (entry_states == NULL || entry_const_known == NULL || entry_const_values == NULL ||
      entry_known == NULL || pending == NULL) {
    goto cleanup;
  }
  amiga_call_effect_reg_state_clear(&entry_states[entry_block_index]);
  clear_local_data_const_state(entry_const_known[entry_block_index], entry_const_values[entry_block_index]);
  entry_known[entry_block_index] = 1U;
  pending[pending_count++] = entry_block_index;
  while (pending_count != 0U) {
    size_t block_index = pending[--pending_count];
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    AmigaCallEffectRegState state;
    uint8_t const_known[8];
    int32_t const_values[8];
    uint32_t cursor = block->start_offset < target_offset ? target_offset : block->start_offset;
    size_t edge_index;
    amiga_call_effect_reg_state_copy(&state, &entry_states[block_index]);
    copy_local_data_const_state(const_known, const_values, entry_const_known[block_index], entry_const_values[block_index]);
    while (cursor < block->end_offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      AmigaCallEffectRegState prev_state;
      uint8_t prev_const_known[8];
      int32_t prev_const_values[8];
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U) break;
      amiga_call_effect_reg_state_copy(&prev_state, &state);
      copy_local_data_const_state(prev_const_known, prev_const_values, const_known, const_values);
      if (decode.is_call) {
        uint32_t nested_target_offset;
        AmigaCallEffectRegState nested_summary;
        AmigaCallEffectRegState call_effect_state;
        PlatformResolvedIndirectInfo info;
        const AmigaOsLibraryVectorInfo *call_entry = NULL;
        clear_all_amiga_call_effect_regs(&state);
        clear_local_data_const_state(const_known, const_values);
        amiga_call_effect_reg_state_clear(&nested_summary);
        amiga_call_effect_reg_state_clear(&call_effect_state);
        if (instruction_direct_target_local(ctx, &decode.instruction, cursor, &nested_target_offset) &&
            summarize_amiga_direct_local_success_outputs(ctx, section_analysis, nested_target_offset,
              cache, cache_count, &nested_summary)) {
          amiga_call_effect_reg_state_copy(&state, &nested_summary);
          const_known[0] = 1U;
          const_values[0] = 0;
        }
        platform_resolved_indirect_info_init(&info);
        if (resolve_amiga_local_wrapper_dispatch_info(ctx, section_analysis, cursor, &decode.instruction, &info) &&
            info.note_symbol_name[0] != '\0') {
          call_entry = amiga_os_find_library_vector_by_symbol_name(info.note_symbol_name);
        }
        if (call_entry != NULL &&
            seed_amiga_call_effect_reg_state_from_call_entry(ctx, section_analysis, cursor, call_entry,
              &call_effect_state)) {
          amiga_call_effect_reg_state_copy(&state, &call_effect_state);
        }
        apply_recovered_amiga_platform_effects_to_call_state(section_analysis, cursor, &state);
      } else {
        update_amiga_call_effect_reg_state_for_instruction(&decode.instruction, &prev_state, &state);
        update_local_data_const_state_for_instruction(&decode.instruction, prev_const_known, prev_const_values,
          const_known, const_values);
      }
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    for (edge_index = block->edge_start; edge_index < block->edge_start + block->edge_count; ++edge_index) {
      const M68kCfgEdgeIR *edge = &section_analysis->edges[edge_index];
      if (edge->kind == M68K_CFG_EDGE_RETURN) {
        if (!const_known[0] || const_values[0] != 0) continue;
        if (!have_summary) {
          amiga_call_effect_reg_state_copy(out_summary, &state);
          have_summary = 1;
        } else {
          amiga_call_effect_reg_state_join(out_summary, &state);
        }
        continue;
      }
      if (edge->kind == M68K_CFG_EDGE_CALL || edge->target_block_index == SIZE_MAX ||
          edge->target_block_index >= section_analysis->block_count) {
        continue;
      }
      if (!entry_known[edge->target_block_index]) {
        amiga_call_effect_reg_state_copy(&entry_states[edge->target_block_index], &state);
        copy_local_data_const_state(entry_const_known[edge->target_block_index],
          entry_const_values[edge->target_block_index], const_known, const_values);
        entry_known[edge->target_block_index] = 1U;
        if (pending_count < pending_capacity) pending[pending_count++] = edge->target_block_index;
      } else {
        int changed = 0;
        changed |= amiga_call_effect_reg_state_join(&entry_states[edge->target_block_index], &state);
        changed |= join_local_data_const_state(entry_const_known[edge->target_block_index],
          entry_const_values[edge->target_block_index], const_known, const_values);
        if (changed && pending_count < pending_capacity) pending[pending_count++] = edge->target_block_index;
      }
    }
  }
  result = have_summary;
cleanup:
  cache[entry_block_index].state = 2U;
  if (result) {
    amiga_call_effect_reg_state_copy(&cache[entry_block_index].reg_state, out_summary);
  } else {
    amiga_call_effect_reg_state_clear(&cache[entry_block_index].reg_state);
  }
  free(entry_states);
  free(entry_const_known);
  free(entry_const_values);
  free(entry_known);
  free(pending);
  return result;
}

static int load_amiga_recovered_local_success_summary_state(const M68kSectionAnalysisIR *section_analysis,
    uint32_t target_offset, AmigaCallEffectRegState *out_state) {
  size_t index;
  int found = 0;
  if (out_state != NULL) amiga_call_effect_reg_state_clear(out_state);
  if (section_analysis == NULL || out_state == NULL) return 0;
  for (index = 0U; index < section_analysis->recovered_local_call_summary_count; ++index) {
    const M68kRecoveredLocalCallSummaryIR *summary = &section_analysis->recovered_local_call_summaries[index];
    if (summary->target_offset != target_offset) continue;
    if (summary->success_reg_kind != 1U || summary->success_reg_index != 0U ||
        !summary->success_value_known || summary->success_reg_value != 0) {
      continue;
    }
    if (summary->reg_index >= 8U) continue;
    if (summary->effect_kind == M68K_PLATFORM_EFFECT_SET_BASE_REG) {
      if (summary->reg_kind == 1U) {
        out_state->data_reg_base_names[summary->reg_index] = summary->payload.named_base.base_name;
        found = 1;
      } else if (summary->reg_kind == 2U) {
        out_state->addr_reg_base_names[summary->reg_index] = summary->payload.named_base.base_name;
        found = 1;
      }
    } else if (summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
      if (summary->reg_kind == 1U) {
        out_state->data_reg_type_names[summary->reg_index] = summary->payload.typed.type_name;
        found = 1;
      } else if (summary->reg_kind == 2U) {
        out_state->addr_reg_type_names[summary->reg_index] = summary->payload.typed.type_name;
        found = 1;
      }
    }
  }
  return found;
}

static int append_amiga_recovered_local_success_summaries(const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *section_analysis, uint32_t target_offset, AmigaLocalSuccessSummaryCacheEntry *cache,
    size_t cache_count) {
  AmigaCallEffectRegState summary;
  uint8_t reg_index;
  amiga_call_effect_reg_state_clear(&summary);
  if (!summarize_amiga_direct_local_success_outputs(ctx, section_analysis, target_offset, cache, cache_count, &summary)) return 0;
  for (reg_index = 0U; reg_index < 8U; ++reg_index) {
    if (summary.data_reg_base_names[reg_index] != NULL &&
        m68k_ir_section_analysis_append_recovered_local_call_summary(section_analysis, target_offset,
          M68K_PLATFORM_EFFECT_SET_BASE_REG, 1U, reg_index, 1U, 0U, 1U, 0,
          summary.data_reg_base_names[reg_index], NULL) != 0) {
      return -1;
    }
    if (summary.addr_reg_base_names[reg_index] != NULL &&
        m68k_ir_section_analysis_append_recovered_local_call_summary(section_analysis, target_offset,
          M68K_PLATFORM_EFFECT_SET_BASE_REG, 2U, reg_index, 1U, 0U, 1U, 0,
          summary.addr_reg_base_names[reg_index], NULL) != 0) {
      return -1;
    }
    if (summary.data_reg_type_names[reg_index] != NULL &&
        m68k_ir_section_analysis_append_recovered_local_call_summary(section_analysis, target_offset,
          M68K_PLATFORM_EFFECT_SET_TYPED_REG, 1U, reg_index, 1U, 0U, 1U, 0,
          NULL, summary.data_reg_type_names[reg_index]) != 0) {
      return -1;
    }
    if (summary.addr_reg_type_names[reg_index] != NULL &&
        m68k_ir_section_analysis_append_recovered_local_call_summary(section_analysis, target_offset,
          M68K_PLATFORM_EFFECT_SET_TYPED_REG, 2U, reg_index, 1U, 0U, 1U, 0,
          NULL, summary.addr_reg_type_names[reg_index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static int resolve_amiga_data_reg_info_from_success_local_calls(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, AmigaResolvedDataRegInfo *out_info) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t start;
  uint32_t cursor;
  AmigaCallEffectRegState state;
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  if (ctx == NULL || section == NULL || section_analysis == NULL || reg >= 8U || out_info == NULL) return 0;
  amiga_call_effect_reg_state_clear(&state);
  start = resolve_analysis_trace_start(ctx, section_analysis, offset);
  if (start == UINT32_MAX || start > offset) return 0;
  {
    uint32_t fallback_start = find_amiga_typed_trace_fallback_start(ctx, offset);
    if (fallback_start != UINT32_MAX && fallback_start < start) start = fallback_start;
  }
  for (cursor = start; cursor < offset && cursor < section->data_size; ) {
    SectionDecodeResult decode;
    AmigaCallEffectRegState prev_state;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
    amiga_call_effect_reg_state_copy(&prev_state, &state);
    if (decode.is_call) {
      uint32_t target_offset;
      AmigaCallEffectRegState call_effect_state;
      PlatformResolvedIndirectInfo info;
      const AmigaOsLibraryVectorInfo *call_entry = NULL;
      clear_all_amiga_call_effect_regs(&state);
      amiga_call_effect_reg_state_clear(&call_effect_state);
      if (instruction_direct_target_local(ctx, &decode.instruction, cursor, &target_offset)) {
        load_amiga_recovered_local_success_summary_state(section_analysis, target_offset, &state);
      }
      platform_resolved_indirect_info_init(&info);
      if (resolve_amiga_local_wrapper_dispatch_info(ctx, section_analysis, cursor, &decode.instruction, &info) &&
          info.note_symbol_name[0] != '\0') {
        call_entry = amiga_os_find_library_vector_by_symbol_name(info.note_symbol_name);
      }
      if (call_entry != NULL &&
          seed_amiga_call_effect_reg_state_from_call_entry(ctx, section_analysis, cursor, call_entry,
            &call_effect_state)) {
        amiga_call_effect_reg_state_copy(&state, &call_effect_state);
      }
      apply_recovered_amiga_platform_effects_to_call_state(section_analysis, cursor, &state);
    } else {
      update_amiga_call_effect_reg_state_for_instruction(&decode.instruction, &prev_state, &state);
    }
    cursor += (uint32_t)decode.instruction.byte_count;
  }
  if (state.data_reg_type_names[reg] == NULL) return 0;
  out_info->slot_disp = INT16_MIN;
  out_info->field_disp = INT16_MIN;
  out_info->type_name = state.data_reg_type_names[reg];
  out_info->owner_type_name = state.data_reg_type_names[reg];
  return 1;
}

static int resolve_preceding_success_local_call_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, AmigaResolvedDataRegInfo *out_info) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  if (ctx == NULL || section == NULL || section_analysis == NULL || reg >= 8U || out_info == NULL) return 0;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    uint32_t prev_offset = UINT32_MAX;
    SectionDecodeResult prev_decode = {0};
    int have_prev = 0;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      prev_offset = cursor;
      prev_decode = decode;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (!have_prev || cursor != offset || prev_offset == UINT32_MAX || !prev_decode.is_call) continue;
    {
      uint32_t target_offset;
      AmigaCallEffectRegState summary;
      if (!instruction_direct_target_local(ctx, &prev_decode.instruction, prev_offset, &target_offset)) continue;
      amiga_call_effect_reg_state_clear(&summary);
      if (!load_amiga_recovered_local_success_summary_state(section_analysis, target_offset, &summary)) continue;
      if (summary.data_reg_type_names[reg] == NULL) continue;
      out_info->slot_disp = INT16_MIN;
      out_info->field_disp = INT16_MIN;
      out_info->type_name = summary.data_reg_type_names[reg];
      out_info->owner_type_name = summary.data_reg_type_names[reg];
      return 1;
    }
  }
  return 0;
}

static int resolve_amiga_data_reg_info_from_success_local_calls_uncached(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, AmigaResolvedDataRegInfo *out_info) {
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  if (ctx == NULL || section_analysis == NULL || out_info == NULL) return 0;
  return resolve_preceding_success_local_call_data_reg_info(ctx, section_analysis, offset, reg, out_info) ||
    resolve_amiga_data_reg_info_from_success_local_calls(ctx, section_analysis, offset, reg, out_info);
}

static const char *resolve_amiga_library_base_name_raw(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots) {
  const M68kSection *section = section_analysis_context_section(ctx);
  const char *addr_reg_base_names[8] = {0};
  const char *addr_reg_seed_base_names[8] = {0};
  const char *data_reg_base_names[8] = {0};
  const char *addr_reg_type_names[8] = {0};
  const char *data_reg_type_names[8] = {0};
  AmigaBaseSlotTag slot_base_names[AMIGA_BASE_SLOT_TAG_CAPACITY] = {{0}};
  AmigaTypedSlotTag slot_type_names[AMIGA_BASE_SLOT_TAG_CAPACITY] = {{0}};
  const char *saved_stack_base_names[8] = {0};
  size_t saved_stack_base_count = 0U;
  size_t slot_base_count = sizeof(slot_base_names) / sizeof(slot_base_names[0]);
  uint32_t cursor;
  if (section == NULL || section_analysis == NULL || reg >= 8U) return NULL;
  addr_reg_base_names[6] = AMIGA_APP_BASE_TAG;
  if (include_section_slots) {
    size_t index;
    seed_amiga_base_slot_tags_from_effects(section_analysis, slot_base_names,
      sizeof(slot_base_names) / sizeof(slot_base_names[0]));
    for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
      const M68kRecoveredPlatformBaseSlotIR *slot = &section_analysis->recovered_platform_base_slots[index];
      set_amiga_base_slot_tag(slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]),
        slot->displacement, slot->base_name);
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
    uint8_t written_reg;
    uint8_t pushed_reg;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    metadata = instruction_sim_metadata(&instruction);
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > offset) break;
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      prev_addr_reg_base_names[written_reg] = addr_reg_base_names[written_reg];
      prev_addr_reg_seed_base_names[written_reg] = addr_reg_seed_base_names[written_reg];
      prev_data_reg_base_names[written_reg] = data_reg_base_names[written_reg];
    }
    {
      uint8_t exg_left;
      uint8_t exg_right;
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
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_address_reg_approx(&instruction, written_reg)) {
        addr_reg_base_names[written_reg] = NULL;
        addr_reg_seed_base_names[written_reg] = NULL;
        addr_reg_type_names[written_reg] = NULL;
      }
    }
    {
      uint8_t dest_reg;
      const M68kOperandIR *source = NULL;
      uint32_t source_target;
      if (instruction_is_data_move(&instruction, &dest_reg, &source)) {
      if (source != NULL && source->kind == M68K_ASM_OPERAND_DN && source->value.reg < 8U) {
        data_reg_base_names[dest_reg] = prev_data_reg_base_names[source->value.reg];
        data_reg_type_names[dest_reg] = data_reg_type_names[source->value.reg];
      } else if (source != NULL && source->kind == M68K_ASM_OPERAND_AN && source->value.reg < 8U) {
        data_reg_base_names[dest_reg] = prev_addr_reg_base_names[source->value.reg];
        data_reg_type_names[dest_reg] = addr_reg_type_names[source->value.reg];
      } else if (metadata != NULL &&
          instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
            (uint32_t)section->data_size, &source_target)) {
        data_reg_base_names[dest_reg] = read_amiga_library_seed_name(section, source_target);
        data_reg_type_names[dest_reg] = NULL;
      } else {
        data_reg_base_names[dest_reg] = NULL;
        data_reg_type_names[dest_reg] = NULL;
      }
      }
    }
    {
      uint8_t dest_reg;
      const M68kOperandIR *source = NULL;
      uint8_t source_reg;
      int16_t slot_disp;
      uint32_t source_target;
      if (instruction_is_address_move(&instruction, &dest_reg, &source)) {
      if (operand_is_absolute_short_value(source, 4U)) {
        addr_reg_base_names[dest_reg] = "SysBase";
        addr_reg_seed_base_names[dest_reg] = NULL;
        addr_reg_type_names[dest_reg] = NULL;
      } else if (instruction_pops_address_reg_from_stack(&instruction, &dest_reg) &&
          dest_reg == 6U && saved_stack_base_count != 0U) {
        addr_reg_base_names[dest_reg] = saved_stack_base_names[--saved_stack_base_count];
        addr_reg_seed_base_names[dest_reg] = NULL;
        addr_reg_type_names[dest_reg] = NULL;
      } else if (source != NULL && source->kind == M68K_ASM_OPERAND_AN && source->value.reg < 8U) {
        addr_reg_base_names[dest_reg] = prev_addr_reg_base_names[source->value.reg];
        addr_reg_seed_base_names[dest_reg] = prev_addr_reg_seed_base_names[source->value.reg];
        addr_reg_type_names[dest_reg] = addr_reg_type_names[source->value.reg];
      } else if (source != NULL && operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
        addr_reg_base_names[dest_reg] = prev_data_reg_base_names[source_reg];
        addr_reg_seed_base_names[dest_reg] = NULL;
        addr_reg_type_names[dest_reg] = data_reg_type_names[source_reg];
      } else if (source != NULL && operand_is_app_base_disp_ea(source, 6U, &slot_disp) &&
          prev_addr_reg_base_names[6] == AMIGA_APP_BASE_TAG) {
        addr_reg_base_names[dest_reg] = lookup_amiga_base_slot_tag(slot_base_names, slot_base_count, slot_disp);
        addr_reg_seed_base_names[dest_reg] = NULL;
        addr_reg_type_names[dest_reg] = lookup_amiga_effect_or_local_typed_slot(section_analysis,
          slot_type_names, sizeof(slot_type_names) / sizeof(slot_type_names[0]), slot_disp);
      } else if (metadata != NULL &&
          instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
            (uint32_t)section->data_size, &source_target)) {
        addr_reg_base_names[dest_reg] = NULL;
        addr_reg_seed_base_names[dest_reg] = read_amiga_library_seed_name(section, source_target);
        addr_reg_type_names[dest_reg] = NULL;
      } else {
        addr_reg_base_names[dest_reg] = NULL;
        addr_reg_seed_base_names[dest_reg] = NULL;
        addr_reg_type_names[dest_reg] = NULL;
      }
      } else if (instruction_mnemonic_is(&instruction, "lea") &&
          instruction.operand_count == 2U &&
          operand_address_reg_index_local(&instruction.operands[1], &dest_reg)) {
        source = &instruction.operands[0];
        if (source != NULL && operand_is_app_base_disp_ea(source, 6U, &slot_disp) &&
            prev_addr_reg_base_names[6] == AMIGA_APP_BASE_TAG) {
          addr_reg_base_names[dest_reg] = lookup_amiga_base_slot_tag(slot_base_names, slot_base_count, slot_disp);
          addr_reg_seed_base_names[dest_reg] = NULL;
          addr_reg_type_names[dest_reg] = lookup_amiga_effect_or_local_typed_slot(section_analysis,
            slot_type_names, sizeof(slot_type_names) / sizeof(slot_type_names[0]), slot_disp);
        } else if (metadata != NULL &&
            instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
              (uint32_t)section->data_size, &source_target)) {
          addr_reg_base_names[dest_reg] = NULL;
          addr_reg_seed_base_names[dest_reg] = read_amiga_library_seed_name(section, source_target);
          addr_reg_type_names[dest_reg] = NULL;
        } else {
          addr_reg_base_names[dest_reg] = NULL;
          addr_reg_seed_base_names[dest_reg] = NULL;
          addr_reg_type_names[dest_reg] = NULL;
        }
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
    if (decode.is_call) {
      uint32_t target_offset;
      AmigaCallEffectRegState summary_state;
      amiga_call_effect_reg_state_clear(&summary_state);
      if (instruction_direct_target_local(ctx, &instruction, cursor, &target_offset) &&
          load_amiga_recovered_local_success_summary_state(section_analysis, target_offset, &summary_state)) {
        for (written_reg = 0U; written_reg < 8U; ++written_reg) {
          if (summary_state.data_reg_base_names[written_reg] != NULL) {
            data_reg_base_names[written_reg] = summary_state.data_reg_base_names[written_reg];
            data_reg_type_names[written_reg] = summary_state.data_reg_type_names[written_reg];
          }
          if (summary_state.addr_reg_base_names[written_reg] != NULL) {
            addr_reg_base_names[written_reg] = summary_state.addr_reg_base_names[written_reg];
            addr_reg_seed_base_names[written_reg] = NULL;
            addr_reg_type_names[written_reg] = summary_state.addr_reg_type_names[written_reg];
          }
        }
      }
    }
    {
      uint8_t reg_kind;
      uint8_t reg_index;
      int16_t slot_disp;
      if (instruction_is_register_to_app_slot_store(&instruction, &reg_kind, &reg_index, &slot_disp) &&
          addr_reg_base_names[6] == AMIGA_APP_BASE_TAG) {
        const char *stored_base = NULL;
        if (reg_kind == 1U && reg_index < 8U) stored_base = prev_data_reg_base_names[reg_index];
        else if (reg_kind == 2U && reg_index < 8U) stored_base = prev_addr_reg_base_names[reg_index];
        if (stored_base != NULL && stored_base != AMIGA_APP_BASE_TAG)
          set_amiga_base_slot_tag(slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]), slot_disp,
            stored_base);
      }
    }
    {
      uint8_t reg_kind;
      uint8_t reg_index;
      int16_t slot_disp;
      if (instruction_is_app_slot_load(&instruction, &reg_kind, &reg_index, &slot_disp) &&
          addr_reg_base_names[6] == AMIGA_APP_BASE_TAG) {
        const char *loaded_base = lookup_amiga_base_slot_tag(slot_base_names, slot_base_count, slot_disp);
        const char *loaded_type = lookup_amiga_effect_or_local_typed_slot(section_analysis,
          slot_type_names, sizeof(slot_type_names) / sizeof(slot_type_names[0]), slot_disp);
        if (loaded_type == NULL) loaded_type = resolve_amiga_base_type_name(loaded_base);
        if (reg_kind == 1U && reg_index < 8U) data_reg_base_names[reg_index] = loaded_base;
        if (reg_kind == 1U && reg_index < 8U) data_reg_type_names[reg_index] = loaded_type;
        else if (reg_kind == 2U && reg_index < 8U) {
          addr_reg_base_names[reg_index] = loaded_base;
          addr_reg_seed_base_names[reg_index] = NULL;
          addr_reg_type_names[reg_index] = loaded_type;
        }
      }
    }
    apply_recovered_amiga_platform_effects(section_analysis, cursor, data_reg_base_names, addr_reg_base_names,
      data_reg_type_names, addr_reg_type_names, slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]),
      slot_type_names, sizeof(slot_type_names) / sizeof(slot_type_names[0]));
    cursor += (uint32_t)instruction.byte_count;
  }
  return addr_reg_base_names[reg] != AMIGA_APP_BASE_TAG ? addr_reg_base_names[reg] : NULL;
}

static const char *resolve_amiga_address_reg_type_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots) {
  AmigaResolvedAddressRegInfo info;
  if (!resolve_amiga_address_reg_info(ctx, section_analysis, offset, reg, include_section_slots, &info)) return NULL;
  return info.type_name;
}

static void init_amiga_typed_trace_state(AmigaTypedTraceState *state, const M68kSectionAnalysisIR *section_analysis,
    int include_section_slots) {
  size_t reg_index;
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
  for (reg_index = 0U; reg_index < 8U; ++reg_index) {
    state->addr_reg_slot_source[reg_index] = INT16_MIN;
    state->data_reg_slot_source[reg_index] = INT16_MIN;
    state->addr_reg_field_disp[reg_index] = INT16_MIN;
    state->data_reg_field_disp[reg_index] = INT16_MIN;
  }
  if (include_section_slots) {
    seed_amiga_typed_slot_tags_from_effects(section_analysis, state->slot_type_names,
      sizeof(state->slot_type_names) / sizeof(state->slot_type_names[0]));
  }
}

static uint32_t find_amiga_typed_trace_fallback_start(const SectionAnalysisContext *ctx, uint32_t offset) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  uint32_t best = UINT32_MAX;
  if (ctx == NULL || section == NULL || offset == 0U) return UINT32_MAX;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    int decoded_any = 0;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      decoded_any = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (decoded_any && cursor == offset) {
      best = candidate;
      break;
    }
  }
  return best;
}

static int section_analysis_has_amiga_structural_slot_use(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement) {
  size_t index;
  if (section_analysis == NULL || displacement == INT16_MIN) return 0;
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
    if (call->kind == PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL && call->note_disp == displacement) return 1;
  }
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG && effect->displacement == displacement) return 1;
  }
  return 0;
}

static int trace_amiga_typed_state(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, int include_section_slots, AmigaTypedTraceState *out_state) {
  const M68kSection *section = section_analysis_context_section(ctx);
  const char *saved_stack_data_type_names[8] = {0};
  const char *saved_stack_data_owner_type_names[8] = {0};
  const char *saved_stack_addr_type_names[8] = {0};
  const char *saved_stack_addr_owner_type_names[8] = {0};
  int16_t saved_stack_data_slot_source[8];
  int16_t saved_stack_data_field_disp[8];
  int16_t saved_stack_addr_slot_source[8];
  int16_t saved_stack_addr_field_disp[8];
  size_t saved_stack_count = 0U;
  uint32_t cursor;
  size_t reg_index;
  if (section == NULL || section_analysis == NULL || out_state == NULL) return 0;
  init_amiga_typed_trace_state(out_state, section_analysis, include_section_slots);
  for (reg_index = 0U; reg_index < 8U; ++reg_index) {
    saved_stack_data_slot_source[reg_index] = INT16_MIN;
    saved_stack_data_field_disp[reg_index] = INT16_MIN;
    saved_stack_addr_slot_source[reg_index] = INT16_MIN;
    saved_stack_addr_field_disp[reg_index] = INT16_MIN;
  }
  cursor = resolve_analysis_trace_start(ctx, section_analysis, offset);
  if (cursor == UINT32_MAX || cursor > offset) return 0;
  {
    uint32_t fallback_cursor = find_amiga_typed_trace_fallback_start(ctx, offset);
    if (fallback_cursor != UINT32_MAX && fallback_cursor < cursor) cursor = fallback_cursor;
  }
  seed_amiga_effect_state_from_preceding_fallthrough(ctx, section_analysis, cursor,
    NULL, NULL, out_state->data_reg_type_names, out_state->addr_reg_type_names, NULL, 0U,
    out_state->slot_type_names, sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]));
  for (reg_index = 0U; reg_index < 8U; ++reg_index) {
    out_state->addr_reg_owner_type_names[reg_index] = out_state->addr_reg_type_names[reg_index];
  }
  while (cursor < offset && cursor < section->data_size) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    const char *prev_addr_reg_type_names[8];
    const char *prev_addr_reg_owner_type_names[8];
    const char *prev_data_reg_type_names[8];
    const char *prev_data_reg_owner_type_names[8];
    int16_t prev_addr_reg_slot_source[8];
    int16_t prev_data_reg_slot_source[8];
    int16_t prev_addr_reg_field_disp[8];
    int16_t prev_data_reg_field_disp[8];
    uint8_t dest_reg;
    uint8_t pushed_reg;
    uint8_t written_reg;
    const M68kOperandIR *source = NULL;
    int16_t slot_disp;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > offset) break;
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      prev_addr_reg_type_names[written_reg] = out_state->addr_reg_type_names[written_reg];
      prev_addr_reg_owner_type_names[written_reg] = out_state->addr_reg_owner_type_names[written_reg];
      prev_data_reg_type_names[written_reg] = out_state->data_reg_type_names[written_reg];
      prev_data_reg_owner_type_names[written_reg] = out_state->data_reg_owner_type_names[written_reg];
      prev_addr_reg_slot_source[written_reg] = out_state->addr_reg_slot_source[written_reg];
      prev_data_reg_slot_source[written_reg] = out_state->data_reg_slot_source[written_reg];
      prev_addr_reg_field_disp[written_reg] = out_state->addr_reg_field_disp[written_reg];
      prev_data_reg_field_disp[written_reg] = out_state->data_reg_field_disp[written_reg];
      if (instruction_writes_data_reg_approx(&instruction, written_reg)) {
        out_state->data_reg_type_names[written_reg] = NULL;
        out_state->data_reg_owner_type_names[written_reg] = NULL;
        out_state->data_reg_slot_source[written_reg] = INT16_MIN;
        out_state->data_reg_field_disp[written_reg] = INT16_MIN;
      }
      if (instruction_writes_address_reg_approx(&instruction, written_reg)) {
        out_state->addr_reg_type_names[written_reg] = NULL;
        out_state->addr_reg_owner_type_names[written_reg] = NULL;
        out_state->addr_reg_slot_source[written_reg] = INT16_MIN;
        out_state->addr_reg_field_disp[written_reg] = INT16_MIN;
      }
    }
    if (instruction_is_data_move(&instruction, &dest_reg, &source) && source != NULL) {
      uint8_t source_reg;
      if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
        out_state->data_reg_type_names[dest_reg] = prev_data_reg_type_names[source_reg];
        out_state->data_reg_owner_type_names[dest_reg] = prev_data_reg_owner_type_names[source_reg];
        out_state->data_reg_slot_source[dest_reg] = prev_data_reg_slot_source[source_reg];
        out_state->data_reg_field_disp[dest_reg] = prev_data_reg_field_disp[source_reg];
      } else if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
        out_state->data_reg_type_names[dest_reg] = prev_addr_reg_type_names[source_reg];
        out_state->data_reg_owner_type_names[dest_reg] = prev_addr_reg_owner_type_names[source_reg];
        out_state->data_reg_slot_source[dest_reg] = prev_addr_reg_slot_source[source_reg];
        out_state->data_reg_field_disp[dest_reg] = prev_addr_reg_field_disp[source_reg];
      } else if (operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        const char *loaded_base = lookup_recovered_platform_base_slot(section_analysis, slot_disp);
        out_state->data_reg_type_names[dest_reg] = lookup_amiga_effect_or_local_typed_slot(section_analysis,
          out_state->slot_type_names, sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]), slot_disp);
        if (out_state->data_reg_type_names[dest_reg] == NULL) {
          out_state->data_reg_type_names[dest_reg] = resolve_amiga_base_type_name(loaded_base);
        }
        out_state->data_reg_owner_type_names[dest_reg] = out_state->data_reg_type_names[dest_reg];
        out_state->data_reg_slot_source[dest_reg] = slot_disp;
        out_state->data_reg_field_disp[dest_reg] = INT16_MIN;
      } else if (operand_is_indirect_or_disp_an(source, &source_reg, &slot_disp) &&
          source_reg < 8U &&
          (prev_addr_reg_type_names[source_reg] != NULL ||
           prev_addr_reg_owner_type_names[source_reg] != NULL ||
           prev_addr_reg_slot_source[source_reg] != INT16_MIN)) {
        const char *container_type_name =
          prev_addr_reg_type_names[source_reg] != NULL
            ? prev_addr_reg_type_names[source_reg]
            : prev_addr_reg_owner_type_names[source_reg];
        out_state->data_reg_type_names[dest_reg] =
          resolve_amiga_struct_field_nested_type_name(container_type_name, slot_disp);
        out_state->data_reg_owner_type_names[dest_reg] =
          prev_addr_reg_type_names[source_reg] != NULL
            ? prev_addr_reg_type_names[source_reg]
            : prev_addr_reg_owner_type_names[source_reg];
        out_state->data_reg_slot_source[dest_reg] = prev_addr_reg_slot_source[source_reg];
        out_state->data_reg_field_disp[dest_reg] = slot_disp;
      }
    }
    if (instruction_is_address_move(&instruction, &dest_reg, &source) && source != NULL) {
      uint8_t source_reg;
      int16_t field_disp;
      if (operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        const char *loaded_base = lookup_recovered_platform_base_slot(section_analysis, slot_disp);
        out_state->addr_reg_slot_source[dest_reg] = slot_disp;
        out_state->addr_reg_field_disp[dest_reg] = INT16_MIN;
        out_state->addr_reg_type_names[dest_reg] = lookup_amiga_effect_or_local_typed_slot(section_analysis,
          out_state->slot_type_names, sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]), slot_disp);
        if (out_state->addr_reg_type_names[dest_reg] == NULL) {
          out_state->addr_reg_type_names[dest_reg] = resolve_amiga_base_type_name(loaded_base);
        }
        out_state->addr_reg_owner_type_names[dest_reg] = out_state->addr_reg_type_names[dest_reg];
      } else if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
        out_state->addr_reg_slot_source[dest_reg] = prev_addr_reg_slot_source[source_reg];
        out_state->addr_reg_field_disp[dest_reg] = prev_addr_reg_field_disp[source_reg];
        out_state->addr_reg_type_names[dest_reg] = prev_addr_reg_type_names[source_reg];
        out_state->addr_reg_owner_type_names[dest_reg] = prev_addr_reg_owner_type_names[source_reg];
      } else if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
        out_state->addr_reg_slot_source[dest_reg] = prev_data_reg_slot_source[source_reg];
        out_state->addr_reg_field_disp[dest_reg] = prev_data_reg_field_disp[source_reg];
        out_state->addr_reg_type_names[dest_reg] = prev_data_reg_type_names[source_reg];
        out_state->addr_reg_owner_type_names[dest_reg] = prev_data_reg_owner_type_names[source_reg];
      } else if (operand_is_indirect_or_disp_an(source, &source_reg, &field_disp) &&
          source_reg < 8U &&
          (prev_addr_reg_type_names[source_reg] != NULL ||
           prev_addr_reg_owner_type_names[source_reg] != NULL ||
           prev_addr_reg_slot_source[source_reg] != INT16_MIN)) {
        const char *container_type_name =
          prev_addr_reg_type_names[source_reg] != NULL
            ? prev_addr_reg_type_names[source_reg]
            : prev_addr_reg_owner_type_names[source_reg];
        const char *nested_type_name =
          resolve_amiga_struct_field_nested_type_name(container_type_name, field_disp);
        out_state->addr_reg_slot_source[dest_reg] = prev_addr_reg_slot_source[source_reg];
        out_state->addr_reg_field_disp[dest_reg] = nested_type_name != NULL ? INT16_MIN : field_disp;
        out_state->addr_reg_type_names[dest_reg] = nested_type_name;
        out_state->addr_reg_owner_type_names[dest_reg] =
          prev_addr_reg_type_names[source_reg] != NULL
            ? prev_addr_reg_type_names[source_reg]
            : prev_addr_reg_owner_type_names[source_reg];
      }
    } else if (instruction_mnemonic_is(&instruction, "lea") &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[1], &dest_reg) &&
        operand_is_app_base_disp_ea(&instruction.operands[0], 6U, &slot_disp)) {
      const char *loaded_base = lookup_recovered_platform_base_slot(section_analysis, slot_disp);
      out_state->addr_reg_slot_source[dest_reg] = slot_disp;
      out_state->addr_reg_field_disp[dest_reg] = INT16_MIN;
      out_state->addr_reg_type_names[dest_reg] = lookup_amiga_effect_or_local_typed_slot(section_analysis,
        out_state->slot_type_names, sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]), slot_disp);
      if (out_state->addr_reg_type_names[dest_reg] == NULL) {
        out_state->addr_reg_type_names[dest_reg] = resolve_amiga_base_type_name(loaded_base);
      }
      out_state->addr_reg_owner_type_names[dest_reg] = out_state->addr_reg_type_names[dest_reg];
    }
    if (instruction_pushes_data_reg_to_stack_local(&instruction, &pushed_reg) &&
        pushed_reg < 8U && saved_stack_count < (sizeof(saved_stack_data_type_names) / sizeof(saved_stack_data_type_names[0]))) {
      saved_stack_data_type_names[saved_stack_count] = prev_data_reg_type_names[pushed_reg];
      saved_stack_data_owner_type_names[saved_stack_count] = prev_data_reg_owner_type_names[pushed_reg];
      saved_stack_data_slot_source[saved_stack_count] = prev_data_reg_slot_source[pushed_reg];
      saved_stack_data_field_disp[saved_stack_count] = prev_data_reg_field_disp[pushed_reg];
      saved_stack_addr_type_names[saved_stack_count] = NULL;
      saved_stack_addr_owner_type_names[saved_stack_count] = NULL;
      saved_stack_addr_slot_source[saved_stack_count] = INT16_MIN;
      saved_stack_addr_field_disp[saved_stack_count] = INT16_MIN;
      ++saved_stack_count;
    } else if (instruction_pushes_address_reg_to_stack(&instruction, &pushed_reg) &&
        pushed_reg < 8U && saved_stack_count < (sizeof(saved_stack_addr_type_names) / sizeof(saved_stack_addr_type_names[0]))) {
      saved_stack_data_type_names[saved_stack_count] = NULL;
      saved_stack_data_owner_type_names[saved_stack_count] = NULL;
      saved_stack_data_slot_source[saved_stack_count] = INT16_MIN;
      saved_stack_data_field_disp[saved_stack_count] = INT16_MIN;
      saved_stack_addr_type_names[saved_stack_count] = prev_addr_reg_type_names[pushed_reg];
      saved_stack_addr_owner_type_names[saved_stack_count] = prev_addr_reg_owner_type_names[pushed_reg];
      saved_stack_addr_slot_source[saved_stack_count] = prev_addr_reg_slot_source[pushed_reg];
      saved_stack_addr_field_disp[saved_stack_count] = prev_addr_reg_field_disp[pushed_reg];
      ++saved_stack_count;
    }
    if (instruction_pops_data_reg_from_stack_local(&instruction, &dest_reg) &&
        dest_reg < 8U && saved_stack_count != 0U) {
      --saved_stack_count;
      out_state->data_reg_type_names[dest_reg] = saved_stack_data_type_names[saved_stack_count] != NULL
        ? saved_stack_data_type_names[saved_stack_count]
        : saved_stack_addr_type_names[saved_stack_count];
      out_state->data_reg_owner_type_names[dest_reg] = saved_stack_data_owner_type_names[saved_stack_count] != NULL
        ? saved_stack_data_owner_type_names[saved_stack_count]
        : saved_stack_addr_owner_type_names[saved_stack_count];
      out_state->data_reg_slot_source[dest_reg] = saved_stack_data_slot_source[saved_stack_count] != INT16_MIN
        ? saved_stack_data_slot_source[saved_stack_count]
        : saved_stack_addr_slot_source[saved_stack_count];
      out_state->data_reg_field_disp[dest_reg] = saved_stack_data_field_disp[saved_stack_count] != INT16_MIN
        ? saved_stack_data_field_disp[saved_stack_count]
        : saved_stack_addr_field_disp[saved_stack_count];
    } else if (instruction_pops_address_reg_from_stack(&instruction, &dest_reg) &&
        dest_reg < 8U && saved_stack_count != 0U) {
      --saved_stack_count;
      out_state->addr_reg_type_names[dest_reg] = saved_stack_addr_type_names[saved_stack_count] != NULL
        ? saved_stack_addr_type_names[saved_stack_count]
        : saved_stack_data_type_names[saved_stack_count];
      out_state->addr_reg_owner_type_names[dest_reg] = saved_stack_addr_owner_type_names[saved_stack_count] != NULL
        ? saved_stack_addr_owner_type_names[saved_stack_count]
        : saved_stack_data_owner_type_names[saved_stack_count];
      out_state->addr_reg_slot_source[dest_reg] = saved_stack_addr_slot_source[saved_stack_count] != INT16_MIN
        ? saved_stack_addr_slot_source[saved_stack_count]
        : saved_stack_data_slot_source[saved_stack_count];
      out_state->addr_reg_field_disp[dest_reg] = saved_stack_addr_field_disp[saved_stack_count] != INT16_MIN
        ? saved_stack_addr_field_disp[saved_stack_count]
        : saved_stack_data_field_disp[saved_stack_count];
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_data_reg_approx(&instruction, written_reg) &&
          out_state->data_reg_type_names[written_reg] == NULL &&
          instruction_preserves_pointer_provenance_local(&instruction, 1U, written_reg)) {
        out_state->data_reg_type_names[written_reg] = prev_data_reg_type_names[written_reg];
        out_state->data_reg_owner_type_names[written_reg] = prev_data_reg_owner_type_names[written_reg];
        out_state->data_reg_slot_source[written_reg] = prev_data_reg_slot_source[written_reg];
        out_state->data_reg_field_disp[written_reg] = prev_data_reg_field_disp[written_reg];
      }
      if (instruction_writes_address_reg_approx(&instruction, written_reg) &&
          out_state->addr_reg_type_names[written_reg] == NULL &&
          instruction_preserves_pointer_provenance_local(&instruction, 2U, written_reg)) {
        out_state->addr_reg_type_names[written_reg] = prev_addr_reg_type_names[written_reg];
        out_state->addr_reg_owner_type_names[written_reg] = prev_addr_reg_owner_type_names[written_reg];
        out_state->addr_reg_slot_source[written_reg] = prev_addr_reg_slot_source[written_reg];
        out_state->addr_reg_field_disp[written_reg] = prev_addr_reg_field_disp[written_reg];
      }
    }
    apply_recovered_amiga_platform_effects(section_analysis, cursor, NULL, NULL,
      out_state->data_reg_type_names, out_state->addr_reg_type_names, NULL, 0U,
      out_state->slot_type_names, sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]));
    for (reg_index = 0U; reg_index < 8U; ++reg_index) {
      if (out_state->addr_reg_type_names[reg_index] != NULL) {
        out_state->addr_reg_owner_type_names[reg_index] = out_state->addr_reg_type_names[reg_index];
      }
    }
    cursor += (uint32_t)instruction.byte_count;
  }
  return 1;
}

static int resolve_amiga_address_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedAddressRegInfo *out_info) {
  AmigaTypedTraceState state;
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  if (section_analysis == NULL || reg >= 8U || out_info == NULL) return 0;
  if (!trace_amiga_typed_state(ctx, section_analysis, offset, include_section_slots, &state) ||
      (state.addr_reg_type_names[reg] == NULL && state.addr_reg_owner_type_names[reg] == NULL &&
       state.addr_reg_slot_source[reg] == INT16_MIN && state.addr_reg_field_disp[reg] == INT16_MIN)) {
    uint8_t source_data_reg;
    AmigaResolvedDataRegInfo data_info;
    if (resolve_preceding_move_source_data_reg(ctx, section_analysis, offset, reg, &source_data_reg) &&
        (resolve_preceding_field_loaded_data_reg_info(ctx, section_analysis, offset, source_data_reg, &data_info) ||
         resolve_amiga_data_reg_info(ctx, section_analysis, offset, source_data_reg, include_section_slots, &data_info) ||
         resolve_amiga_data_reg_info_from_success_local_calls_uncached(ctx, section_analysis, offset, source_data_reg,
           &data_info))) {
      out_info->slot_disp = data_info.slot_disp;
      out_info->field_disp = data_info.field_disp;
      out_info->type_name = data_info.type_name;
      out_info->owner_type_name = data_info.owner_type_name;
      return 1;
    }
    return resolve_preceding_stack_reloaded_address_reg_info(ctx, section_analysis, offset, reg,
      include_section_slots, out_info);
  }
  out_info->slot_disp = state.addr_reg_slot_source[reg];
  out_info->field_disp = state.addr_reg_field_disp[reg];
  out_info->type_name = state.addr_reg_type_names[reg];
  out_info->owner_type_name = state.addr_reg_owner_type_names[reg];
  return 1;
}

static int resolve_amiga_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedDataRegInfo *out_info) {
  AmigaTypedTraceState state;
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  if (section_analysis == NULL || reg >= 8U || out_info == NULL) return 0;
  if (!trace_amiga_typed_state(ctx, section_analysis, offset, include_section_slots, &state)) return 0;
  if (state.data_reg_type_names[reg] == NULL && state.data_reg_owner_type_names[reg] == NULL &&
      state.data_reg_slot_source[reg] == INT16_MIN && state.data_reg_field_disp[reg] == INT16_MIN) return 0;
  out_info->slot_disp = state.data_reg_slot_source[reg];
  out_info->field_disp = state.data_reg_field_disp[reg];
  out_info->type_name = state.data_reg_type_names[reg];
  out_info->owner_type_name = state.data_reg_owner_type_names[reg];
  return 1;
}

static int resolve_preceding_move_source_data_reg(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t dest_reg, uint8_t *out_source_reg) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  if (ctx == NULL || section == NULL || section_analysis == NULL || out_source_reg == NULL) return 0;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    uint32_t prev_offset = UINT32_MAX;
    M68kInstructionIR prev_instruction;
    int have_prev = 0;
    uint8_t moved_dest_reg;
    const M68kOperandIR *source = NULL;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      prev_instruction = decode.instruction;
      prev_offset = cursor;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (!have_prev || prev_offset == UINT32_MAX || cursor != offset) continue;
    if (!instruction_is_address_move(&prev_instruction, &moved_dest_reg, &source) || moved_dest_reg != dest_reg) continue;
    if (!operand_data_reg_index_local(source, out_source_reg) || *out_source_reg >= 8U) continue;
    return 1;
  }
  return 0;
}

static int resolve_preceding_field_loaded_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t data_reg, AmigaResolvedDataRegInfo *out_info) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  if (ctx == NULL || section == NULL || section_analysis == NULL || out_info == NULL) return 0;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    uint32_t prev_offset = UINT32_MAX;
    M68kInstructionIR prev_instruction;
    int have_prev = 0;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      prev_offset = cursor;
      prev_instruction = decode.instruction;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (!have_prev || cursor != offset || prev_offset == UINT32_MAX) continue;
    {
      uint8_t dest_reg;
      const M68kOperandIR *source = NULL;
      AmigaResolvedAddressRegInfo owner_info;
      int16_t field_disp;
      uint8_t owner_reg;
      if (!instruction_is_data_move(&prev_instruction, &dest_reg, &source) || dest_reg != data_reg || source == NULL) continue;
      if (!operand_is_indirect_or_disp_an(source, &owner_reg, &field_disp)) continue;
      if (!resolve_amiga_address_reg_info(ctx, section_analysis, offset, owner_reg, 1, &owner_info)) continue;
      out_info->field_disp = field_disp;
      out_info->type_name = resolve_amiga_struct_field_nested_type_name(owner_info.type_name, field_disp);
      out_info->owner_type_name = owner_info.type_name != NULL ? owner_info.type_name : owner_info.owner_type_name;
      if (out_info->type_name != NULL || out_info->owner_type_name != NULL) return 1;
    }
  }
  return 0;
}

static int resolve_preceding_stack_reloaded_address_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedAddressRegInfo *out_info) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  if (out_info != NULL) memset(out_info, 0, sizeof(*out_info));
  if (ctx == NULL || section == NULL || section_analysis == NULL || out_info == NULL || reg >= 8U) return 0;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    uint32_t prev_offset = UINT32_MAX;
    uint32_t second_prev_offset = UINT32_MAX;
    SectionDecodeResult prev_decode = {0};
    SectionDecodeResult second_prev_decode = {0};
    int have_prev = 0;
    int have_second_prev = 0;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      second_prev_offset = prev_offset;
      second_prev_decode = prev_decode;
      have_second_prev = have_prev;
      prev_offset = cursor;
      prev_decode = decode;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (!have_prev || !have_second_prev || cursor != offset) continue;
    {
      uint8_t popped_reg;
      uint8_t pushed_reg;
      AmigaResolvedDataRegInfo data_info;
      AmigaResolvedAddressRegInfo addr_info;
      if (!instruction_pops_address_reg_from_stack(&prev_decode.instruction, &popped_reg) || popped_reg != reg) continue;
      if (instruction_pushes_data_reg_to_stack_local(&second_prev_decode.instruction, &pushed_reg) &&
          resolve_amiga_data_reg_info(ctx, section_analysis, second_prev_offset, pushed_reg, include_section_slots, &data_info)) {
        out_info->slot_disp = data_info.slot_disp;
        out_info->field_disp = data_info.field_disp;
        out_info->type_name = data_info.type_name;
        out_info->owner_type_name = data_info.owner_type_name;
        return out_info->type_name != NULL || out_info->owner_type_name != NULL || out_info->slot_disp != INT16_MIN;
      }
      if (instruction_pushes_address_reg_to_stack(&second_prev_decode.instruction, &pushed_reg) &&
          resolve_amiga_address_reg_info(ctx, section_analysis, second_prev_offset, pushed_reg, include_section_slots, &addr_info)) {
        *out_info = addr_info;
        return 1;
      }
    }
  }
  return 0;
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

static int collect_section_amiga_base_slot_tags(const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *section_analysis, AmigaBaseSlotTag *slots, size_t slot_count) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t offset;
  if (section == NULL || section_analysis == NULL || slots == NULL) return 0;
  for (offset = 0U; offset < section->data_size; ++offset) {
    SectionDecodeResult call_decode;
    M68kInstructionIR call_instruction;
    uint32_t cursor;
    const char *seed_base_name = NULL;
    int16_t input_struct_disp = INT16_MIN;
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
      if (_stricmp(call_entry->returns_base_reg_name, "D0") == 0 &&
          m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, offset,
            M68K_PLATFORM_EFFECT_SET_BASE_REG, 1U, 0U, INT16_MIN, INT16_MIN, seed_base_name, NULL, NULL) != 0) {
        return -1;
      }
    } else if (call_entry->input_struct_reg_name != NULL && call_entry->input_struct_name != NULL) {
      uint8_t input_reg_kind;
      uint8_t input_reg_index;
      if (!parse_amiga_register_name(call_entry->input_struct_reg_name, &input_reg_kind, &input_reg_index)) continue;
      if (!resolve_amiga_pre_call_pointer_app_disp(ctx, section_analysis, offset, input_reg_kind, input_reg_index,
            &input_struct_disp)) {
        continue;
      }
      if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, offset,
            M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT, 0U, 0U, input_struct_disp, INT16_MIN, NULL, NULL,
            call_entry->input_struct_name) != 0) {
        return -1;
      }
      if (strcmp(call_entry->function_name, "OpenDevice") == 0 &&
          strcmp(call_entry->input_struct_name, "IO") == 0) {
        int16_t io_disp = INT16_MIN;
        io_disp = input_struct_disp;
        trace_amiga_call_setup(ctx, section_analysis, offset, &seed_base_name, &io_disp, NULL);
        if (seed_base_name == NULL || io_disp == INT16_MIN) continue;
        set_amiga_base_slot_tag(slots, slot_count,
          (int16_t)(io_disp + AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET), seed_base_name);
        if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, offset,
              M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT, 0U, 0U,
              (int16_t)(io_disp + AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET), INT16_MIN, seed_base_name, NULL, NULL) != 0) {
          return -1;
        }
      }
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
        if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, cursor,
              M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT, 0U, 0U, slot_disp, INT16_MIN, seed_base_name, NULL, NULL) != 0) {
          return -1;
        }
        break;
      }
      if (instruction_stops_fallthrough(&instruction)) break;
      cursor += (uint32_t)instruction.byte_count;
    }
  }
  return 0;
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

static int append_amiga_typed_call_effects(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint32_t instruction_size, const AmigaOsLibraryVectorInfo *call_entry) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint8_t effect_reg_kind;
  uint8_t effect_reg_index;
  int16_t input_struct_disp = INT16_MIN;
  const char *returned_base_name = NULL;
  AmigaCallEffectRegState seed_state;
  amiga_call_effect_reg_state_clear(&seed_state);
  if (ctx == NULL || section_analysis == NULL || section == NULL || call_entry == NULL) return 0;
  if (call_entry->input_struct_reg_name != NULL && call_entry->input_struct_name != NULL &&
      parse_amiga_register_name(call_entry->input_struct_reg_name, &effect_reg_kind, &effect_reg_index) &&
      resolve_amiga_pre_call_pointer_app_disp(ctx, section_analysis, offset, effect_reg_kind, effect_reg_index,
        &input_struct_disp)) {
    if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, offset,
          M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT, 0U, 0U, input_struct_disp, INT16_MIN, NULL, NULL,
          call_entry->input_struct_name) != 0) {
      return -1;
    }
  }
  if (call_entry->returns_base_reg_name != NULL && call_entry->returns_base_name_reg_name != NULL &&
      parse_amiga_register_name(call_entry->returns_base_reg_name, &effect_reg_kind, &effect_reg_index)) {
    if (_stricmp(call_entry->returns_base_name_reg_name, "A0") == 0) {
      trace_amiga_call_setup(ctx, section_analysis, offset, &returned_base_name, NULL, NULL);
    } else if (_stricmp(call_entry->returns_base_name_reg_name, "A1") == 0) {
      trace_amiga_call_setup(ctx, section_analysis, offset, NULL, NULL, &returned_base_name);
    }
  }
  if (returned_base_name != NULL && call_entry->returns_base_reg_name != NULL &&
      parse_amiga_register_name(call_entry->returns_base_reg_name, &effect_reg_kind, &effect_reg_index)) {
    if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, offset,
          M68K_PLATFORM_EFFECT_SET_BASE_REG, effect_reg_kind, effect_reg_index, INT16_MIN, INT16_MIN,
          returned_base_name, NULL, NULL) != 0) {
      return -1;
    }
    if (effect_reg_kind == 1U && effect_reg_index < 8U) {
      seed_state.data_reg_base_names[effect_reg_index] = returned_base_name;
    } else if (effect_reg_kind == 2U && effect_reg_index < 8U) {
      seed_state.addr_reg_base_names[effect_reg_index] = returned_base_name;
    }
  }
  if (call_entry->output_reg_name != NULL && call_entry->output_struct_name != NULL &&
      parse_amiga_register_name(call_entry->output_reg_name, &effect_reg_kind, &effect_reg_index)) {
    if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, offset,
          M68K_PLATFORM_EFFECT_SET_TYPED_REG, effect_reg_kind, effect_reg_index, INT16_MIN, INT16_MIN,
          NULL, NULL, call_entry->output_struct_name) != 0) {
      return -1;
    }
    if (effect_reg_kind == 1U && effect_reg_index < 8U) {
      seed_state.data_reg_type_names[effect_reg_index] = call_entry->output_struct_name;
    } else if (effect_reg_kind == 2U && effect_reg_index < 8U) {
      seed_state.addr_reg_type_names[effect_reg_index] = call_entry->output_struct_name;
    }
  }
  if (returned_base_name == NULL && call_entry->output_struct_name == NULL) return 0;
  return append_amiga_post_call_slot_effects(ctx, section_analysis, offset, instruction_size, &seed_state);
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
  const M68kRecoveredPlatformEffectIR *effect;
  const M68kOperandIR *target_operand = NULL;
  uint8_t target_reg;
  AmigaResolvedAddressRegInfo info;
  AmigaResolvedDataRegInfo data_info;
  recovered = find_recovered_platform_call(section_analysis, offset, PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL);
  if (recovered != NULL) {
    load_recovered_platform_call_info(recovered, out_info);
    return 1;
  }
  if (ctx == NULL || instruction == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  if (!instruction_is_call_transfer(instruction)) return 0;
  if (!instruction_target_operand_local(instruction, &target_operand) || target_operand == NULL) return 0;
  if (!operand_is_indirect_an(target_operand, &target_reg)) return 0;
  effect = find_recovered_platform_effect(section_analysis, offset, M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG);
  if (effect != NULL && effect->reg_kind == 2U && effect->reg_index == target_reg &&
      effect->payload.code_ptr.owner_type_name != NULL) {
    if (out_info != NULL) {
      out_info->kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL;
      out_info->note_kind = M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD;
      out_info->note_disp = effect->displacement;
      out_info->note_field_disp = effect->field_disp;
      snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", effect->payload.code_ptr.owner_type_name);
      if (effect->payload.code_ptr.field_symbol_name != NULL && effect->payload.code_ptr.field_symbol_name[0] != '\0') {
        snprintf(out_info->note_symbol_name, sizeof(out_info->note_symbol_name), "%s",
          effect->payload.code_ptr.field_symbol_name);
      } else {
        populate_amiga_callback_field_note_symbol(out_info);
      }
    }
    return 1;
  }
  if (!resolve_amiga_address_reg_info(ctx, section_analysis, offset, target_reg, 1, &info)) {
    uint8_t source_data_reg;
    if (!resolve_preceding_move_source_data_reg(ctx, section_analysis, offset, target_reg, &source_data_reg)) return 0;
    if (!resolve_preceding_field_loaded_data_reg_info(ctx, section_analysis, offset, source_data_reg, &data_info) &&
        !resolve_amiga_data_reg_info(ctx, section_analysis, offset, source_data_reg, 1, &data_info)) {
      return 0;
    }
    info.slot_disp = INT16_MIN;
    info.field_disp = data_info.field_disp;
    info.type_name = data_info.type_name;
    info.owner_type_name = data_info.owner_type_name;
  }
  if (out_info != NULL) {
    const char *owner_type_name = info.owner_type_name != NULL ? info.owner_type_name : info.type_name;
    char slot_name[64];
    out_info->kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL;
    out_info->note_kind = M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD;
    out_info->note_disp = info.slot_disp;
    out_info->note_field_disp = info.field_disp != INT16_MIN ? info.field_disp : 4;
    if (owner_type_name != NULL) {
      snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", owner_type_name);
    } else if (info.slot_disp != INT16_MIN) {
      format_amiga_slot_struct_type_name(slot_name, sizeof(slot_name), info.slot_disp);
      snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", slot_name);
    } else {
      return 0;
    }
    populate_amiga_callback_field_note_symbol(out_info);
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
  AmigaLocalSuccessSummaryCacheEntry *success_cache = NULL;
  size_t success_cache_count = 0U;
  uint32_t offset;
  if (ctx == NULL || section == NULL || section_analysis == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  success_cache_count = section_analysis->block_count != 0U ? section_analysis->block_count : 1U;
  success_cache = (AmigaLocalSuccessSummaryCacheEntry *)calloc(success_cache_count, sizeof(*success_cache));
  if (success_cache == NULL) return -1;
  if (collect_section_amiga_base_slot_tags(ctx, section_analysis, slots, sizeof(slots) / sizeof(slots[0])) != 0) {
    free(success_cache);
    return -1;
  }
  for (offset = 0U; offset < section->data_size; ++offset) {
    SectionDecodeResult decode;
    PlatformResolvedIndirectInfo info;
    const AmigaOsLibraryVectorInfo *call_entry = NULL;
    if (!section_analysis_context_probe_decode(ctx, offset, &decode)) continue;
    {
      uint8_t move_dest_reg;
      const M68kOperandIR *move_source = NULL;
      int direct_d0_imm_seed = 0;
      if (instruction_mnemonic_is(&decode.instruction, "moveq") &&
          decode.instruction.operand_count == 2U &&
          operand_is_immediate_source_local(&decode.instruction.operands[0]) &&
          operand_is_data_reg_direct(&decode.instruction.operands[1], 0U)) {
        direct_d0_imm_seed = 1;
      } else if (instruction_is_data_move(&decode.instruction, &move_dest_reg, &move_source) &&
          move_dest_reg == 0U && operand_is_immediate_source_local(move_source)) {
        direct_d0_imm_seed = 1;
      }
      if (direct_d0_imm_seed) {
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
          free(success_cache);
          return -1;
        }
      }
    }
    }
    if (!decode.is_call) continue;
    platform_resolved_indirect_info_init(&info);
    if (platform_resolve_indirect_control(ctx, section_analysis, offset, &decode.instruction, &info) ==
        PLATFORM_RESOLVED_INDIRECT_NONE) {
      if (!resolve_amiga_local_wrapper_dispatch_info(ctx, section_analysis, offset, &decode.instruction, &info)) continue;
    }
    if (info.kind == PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL) {
      call_entry = resolve_amiga_library_vector_entry(ctx, section_analysis, offset, &decode.instruction);
    } else if (info.kind == PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH &&
        info.note_symbol_name[0] != '\0') {
      call_entry = amiga_os_find_library_vector_by_symbol_name(info.note_symbol_name);
    }
    if (call_entry != NULL &&
        append_amiga_typed_call_effects(ctx, section_analysis, offset, (uint32_t)decode.instruction.byte_count,
          call_entry) != 0) {
      free(success_cache);
      return -1;
    }
    if (info.kind == PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL) {
      const M68kOperandIR *target_operand = NULL;
      uint8_t target_reg;
        if (instruction_target_operand_local(&decode.instruction, &target_operand) && target_operand != NULL &&
            operand_is_indirect_an(target_operand, &target_reg)) {
          {
            const char *field_symbol_name = info.note_symbol_name[0] != '\0' ? info.note_symbol_name : NULL;
          if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, offset,
              M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG, 2U, target_reg, info.note_disp, info.note_field_disp,
              NULL, field_symbol_name, info.note_base_name[0] != '\0' ? info.note_base_name : NULL) != 0) {
            free(success_cache);
            return -1;
          }
          }
        }
      }
    if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis,
          offset, info.kind, info.has_symbol_name ? info.symbol_name : NULL, info.note_kind,
          info.note_base_name[0] != '\0' ? info.note_base_name : NULL,
          info.note_symbol_name[0] != '\0' ? info.note_symbol_name : NULL,
          info.note_reg, info.note_disp, info.note_field_disp,
          info.note_stack_cleanup_known, info.note_stack_cleanup_bytes, info.note_return_kind) != 0) {
      free(success_cache);
      return -1;
    }
  }
  for (offset = 0U; offset < section->data_size; ++offset) {
    SectionDecodeResult decode;
    uint32_t target_offset;
    if (!section_analysis_context_probe_decode(ctx, offset, &decode)) continue;
    if (!decode.is_call) continue;
    if (!instruction_direct_target_local(ctx, &decode.instruction, offset, &target_offset)) continue;
    if (append_amiga_recovered_local_success_summaries(ctx, section_analysis, target_offset,
          success_cache, success_cache_count) != 0) {
      free(success_cache);
      return -1;
    }
  }
  for (offset = 0U; offset < section->data_size; ++offset) {
    SectionDecodeResult decode;
    uint8_t source_kind;
    uint8_t source_reg;
    int16_t slot_disp;
    const char *stored_type_name = NULL;
    if (!section_analysis_context_probe_decode(ctx, offset, &decode)) continue;
    if (!instruction_is_register_to_app_slot_store(&decode.instruction, &source_kind, &source_reg, &slot_disp)) continue;
    if (source_kind == 1U) {
      AmigaResolvedDataRegInfo data_info;
      if (resolve_preceding_field_loaded_data_reg_info(ctx, section_analysis, offset, source_reg, &data_info) ||
          resolve_preceding_success_local_call_data_reg_info(ctx, section_analysis, offset, source_reg, &data_info) ||
          resolve_amiga_data_reg_info(ctx, section_analysis, offset, source_reg, 1, &data_info) ||
          resolve_amiga_data_reg_info_from_success_local_calls(ctx, section_analysis, offset, source_reg, &data_info)) {
        stored_type_name = data_info.type_name;
      }
    } else if (source_kind == 2U) {
      AmigaResolvedAddressRegInfo addr_info;
      if (resolve_amiga_address_reg_info(ctx, section_analysis, offset, source_reg, 1, &addr_info)) {
        stored_type_name = addr_info.type_name;
      }
    }
    if (stored_type_name != NULL &&
        m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, offset,
          M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT, 0U, 0U, slot_disp, INT16_MIN, NULL, NULL,
          stored_type_name) != 0) {
      free(success_cache);
      return -1;
    }
  }
  free(success_cache);
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
  size_t operand_index;
  if (ctx == NULL || section_analysis == NULL || instruction == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    uint8_t base_reg;
    int16_t displacement;
    const char *type_name;
    char field_symbol_name[64];
    M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!operand_is_indirect_or_disp_an(operand, &base_reg, &displacement)) continue;
    type_name = resolve_amiga_address_reg_type_name(ctx, section_analysis, offset, base_reg, 1);
    if (!resolve_amiga_struct_field_symbol_name(type_name, displacement, field_symbol_name, sizeof(field_symbol_name)))
      continue;
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    operand->symbol_ref.addend = 0;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", field_symbol_name);
  }
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
  imm_operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  imm_operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  imm_operand->symbol_ref.addend = 0;
  snprintf(imm_operand->symbol_ref.name, sizeof(imm_operand->symbol_ref.name), "%s", recovered->note_symbol_name);
  return 1;
}

int platform_amiga_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref) {
  if (treat_as_value) return resolve_amiga_app_slot_value_symbol_ref(ctx, section_analysis, displacement, out_symbol_ref);
  return resolve_amiga_app_slot_symbol_ref(ctx, section_analysis, displacement, out_symbol_ref);
}
