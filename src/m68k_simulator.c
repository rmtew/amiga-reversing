#include "m68k_simulator.h"

#include "m68k_instruction_spec.h"
#include "platform_common.h"

#include <stdio.h>
#include <string.h>

static const M68kSimValue g_m68k_sim_unknown_value = {
  M68K_SIM_VALUE_UNKNOWN, 0U, M68K_SIM_PROV_NONE, 0U, 0U, 0U, 0U, 0U, {0U, {0U}}
};

static void sim_diag_error(M68kDiagSink diagnostics, const char *message) {
  if (message == NULL || message[0] == '\0') return;
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SIMULATION_FAILED, message);
}

#include "generated/m68k_simulator_tables.h"

static int sim_add_access(M68kSimStepResult *result, uint8_t kind, uint8_t width,
    size_t section_index, uint32_t offset);
static int sim_add_memory_write(M68kSimStepResult *result, uint8_t width, size_t section_index, uint32_t offset,
    const M68kSimValue *value);
static int sim_compute_ea_address(const M68kSection *section, const M68kInstructionIR *instruction, uint32_t offset,
    const M68kOperandIR *operand, uint8_t ea_formula, uint8_t ea_shape, uint8_t ea_base_kind,
    uint8_t displacement_source, uint8_t uses_displacement, uint8_t uses_index, uint8_t pc_base_bias_bytes,
    uint8_t address_literal_width_bytes, uint8_t index_extension_format, uint8_t index_register_class,
    uint8_t index_value_width_source, uint8_t index_scale_source, uint8_t index_sign_source,
    const M68kSimCpuState *state, size_t section_index, M68kSimValue *out_value);
static void sim_merge_target_set(M68kSimTargetSet *dst, const M68kSimTargetSet *src);
static int sim_read_same_section_memory_value(const M68kObject *object, size_t section_index, const M68kSection *section,
    const M68kSimMemoryState *memory_state, uint32_t address, M68kSimValue *out_value);
static int sim_read_same_section_memory_value_sized(const M68kObject *object, size_t section_index, const M68kSection *section,
    const M68kSimMemoryState *memory_state, uint32_t address, uint8_t width, M68kSimValue *out_value);
static int sim_memory_state_store(M68kSimMemoryState *state, uint8_t width, size_t section_index, uint32_t offset,
    const M68kSimValue *value);
static void sim_sync_extend_with_carry(uint16_t *sr);
static uint8_t sim_infer_ea_shape(const M68kOperandIR *operand);
static uint8_t sim_effective_ea_shape(uint8_t ea_shape, const M68kOperandIR *operand);
static int sim_operand_is_immediate_ea(const M68kOperandIR *operand);
static int sim_operand_is_absolute_long_ea(const M68kOperandIR *operand);
static int sim_operand_is_immediate_value(const M68kOperandIR *operand, uint32_t *out_value);
static int sim_ea_address_register(uint8_t ea_shape, const M68kOperandIR *operand, uint8_t *out_reg);
static uint8_t sim_bit_width_for_metadata_operand(const M68kSimFormMetadata *metadata, uint8_t operand_index,
    const M68kOperandIR *operand);
static int sim_bit_index_from_value(const M68kSimValue *value, uint8_t width, uint32_t *out_bit);
static int sim_concrete_apply_predecrement_operand(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, uint8_t operand_index, const M68kOperandIR *operand,
    M68kSimConcreteState *state, uint32_t *out_address);
static int sim_known_control_register_index(uint8_t control_register_id, uint8_t *out_index);
static int sim_exception_frame_kind_for(uint8_t target_cpu, uint8_t vector, uint8_t *out_frame_kind);
static int sim_exception_frame_def_for_kind(uint8_t frame_kind, const M68kSimExceptionFrameDef **out_def);
static int sim_exception_frame_def_for_format_code(uint8_t format_code, const M68kSimExceptionFrameDef **out_def);
static int sim_concrete_enter_exception(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    const uint16_t *saved_sr_override, uint8_t target_cpu, uint8_t *memory, size_t memory_size,
    M68kSimConcreteState *io_state, M68kDiagSink diagnostics);
static int sim_concrete_return_from_metadata(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t target_cpu, uint8_t *memory, size_t memory_size, M68kSimConcreteState *io_state,
    M68kDiagSink diagnostics);

void m68k_sim_target_set_init(M68kSimTargetSet *set) {
  if (set == NULL) return;
  memset(set, 0, sizeof(*set));
}

int m68k_sim_target_set_add(M68kSimTargetSet *set, uint32_t target) {
  size_t index;
  if (set == NULL) return 0;
  for (index = 0; index < set->count; ++index) {
    if (set->targets[index] == target) return 1;
  }
  if (set->count >= M68K_SIM_TARGET_LIMIT) return 0;
  set->targets[set->count++] = target;
  return 1;
}

void m68k_sim_value_init_unknown(M68kSimValue *value) {
  if (value == NULL) return;
  *value = g_m68k_sim_unknown_value;
}

void m68k_sim_cpu_state_init_unknown(M68kSimCpuState *state) {
  size_t index;
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
  for (index = 0; index < 8U; ++index) {
    state->d[index] = g_m68k_sim_unknown_value;
    state->a[index] = g_m68k_sim_unknown_value;
  }
  for (index = 0; index < M68K_SIM_CONTROL_REGISTER_LIMIT; ++index) {
    state->c[index] = g_m68k_sim_unknown_value;
  }
  state->sr_known = 0U;
}

void m68k_sim_memory_state_init(M68kSimMemoryState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static int sim_value_equal(const M68kSimValue *lhs, const M68kSimValue *rhs) {
  size_t index;
  if (lhs->kind != rhs->kind || lhs->section_index != rhs->section_index ||
      lhs->provenance != rhs->provenance || lhs->value != rhs->value) {
    return 0;
  }
  if (lhs->kind == M68K_SIM_VALUE_TABLE_REGION) {
    return lhs->table_start == rhs->table_start &&
      lhs->table_end == rhs->table_end &&
      lhs->table_stride == rhs->table_stride;
  }
  if (lhs->kind != M68K_SIM_VALUE_TARGET_SET) return 1;
  if (lhs->target_set.count != rhs->target_set.count) return 0;
  for (index = 0; index < lhs->target_set.count; ++index) {
    if (lhs->target_set.targets[index] != rhs->target_set.targets[index]) return 0;
  }
  return 1;
}

static int sim_expand_value_targets(const M68kSimMemoryState *memory_state, const M68kSimValue *value,
    M68kSimTargetSet *out_targets) {
  uint32_t cursor, end, stride;
  size_t cell_index;
  if (value == NULL || out_targets == NULL) return 0;
  m68k_sim_target_set_init(out_targets);
  if (value->kind == M68K_SIM_VALUE_SECTION_PTR) return m68k_sim_target_set_add(out_targets, value->value);
  if (value->kind == M68K_SIM_VALUE_TARGET_SET) {
    *out_targets = value->target_set;
    return 1;
  }
  if (value->kind != M68K_SIM_VALUE_TABLE_REGION || memory_state == NULL) return 0;
  cursor = value->table_start;
  end = value->table_end;
  stride = value->table_stride;
  if (stride == 0U) return 0;
  for (; cursor < end; cursor += stride) {
    for (cell_index = 0; cell_index < memory_state->cell_count; ++cell_index) {
      const M68kSimMemoryCell *cell = &memory_state->cells[cell_index];
      if (cell->section_index != value->section_index || cell->offset != cursor || cell->width != 4U) continue;
      if (cell->value.kind == M68K_SIM_VALUE_SECTION_PTR) {
        m68k_sim_target_set_add(out_targets, cell->value.value);
      } else if (cell->value.kind == M68K_SIM_VALUE_TABLE_REGION) {
        sim_expand_value_targets(memory_state, &cell->value, out_targets);
      } else if (cell->value.kind == M68K_SIM_VALUE_TARGET_SET) {
        sim_merge_target_set(out_targets, &cell->value.target_set);
      }
      break;
    }
  }
  return out_targets->count != 0U;
}

static M68kSimValue sim_value_constant(uint32_t value, uint8_t provenance) {
  M68kSimValue result = g_m68k_sim_unknown_value;
  result.kind = M68K_SIM_VALUE_CONSTANT;
  result.value = value;
  result.provenance = provenance;
  return result;
}

static M68kSimValue sim_value_section_ptr(size_t section_index, uint32_t value, uint8_t provenance) {
  M68kSimValue result = g_m68k_sim_unknown_value;
  result.kind = M68K_SIM_VALUE_SECTION_PTR;
  result.section_index = (uint8_t)section_index;
  result.value = value;
  result.provenance = provenance;
  return result;
}

static M68kSimValue sim_value_target_set(const M68kSimTargetSet *targets, size_t section_index, uint8_t provenance) {
  M68kSimValue result = g_m68k_sim_unknown_value;
  result.kind = M68K_SIM_VALUE_TARGET_SET;
  result.section_index = (uint8_t)section_index;
  result.provenance = provenance;
  if (targets != NULL) result.target_set = *targets;
  return result;
}

static M68kSimValue sim_value_table_region(size_t section_index, uint32_t start, uint32_t end, uint32_t stride,
    uint8_t provenance) {
  M68kSimValue result = g_m68k_sim_unknown_value;
  result.kind = M68K_SIM_VALUE_TABLE_REGION;
  result.section_index = (uint8_t)section_index;
  result.provenance = provenance;
  result.value = start;
  result.table_start = start;
  result.table_end = end;
  result.table_stride = stride;
  return result;
}

static int sim_table_region_contains(const M68kSimValue *region, const M68kSimValue *value) {
  uint32_t start, end, stride;
  uint32_t offset;
  if (region == NULL || value == NULL || region->kind != M68K_SIM_VALUE_TABLE_REGION ||
      region->section_index != value->section_index) {
    return 0;
  }
  start = region->table_start;
  end = region->table_end;
  stride = region->table_stride;
  if (stride == 0U || value->kind != M68K_SIM_VALUE_SECTION_PTR) return 0;
  if (value->value < start || value->value >= end) return 0;
  offset = value->value - start;
  return (offset % stride) == 0U;
}

static int sim_target_set_to_table_region(size_t section_index, const M68kSimTargetSet *set, M68kSimValue *out_value) {
  uint32_t stride;
  uint32_t min_target;
  uint32_t max_target;
  size_t index;
  if (set == NULL || out_value == NULL || set->count < 2U) return 0;
  min_target = set->targets[0];
  max_target = set->targets[0];
  for (index = 1; index < set->count; ++index) {
    if (set->targets[index] < min_target) min_target = set->targets[index];
    if (set->targets[index] > max_target) max_target = set->targets[index];
  }
  stride = set->targets[0] > set->targets[1] ? set->targets[0] - set->targets[1] : set->targets[1] - set->targets[0];
  if (stride == 0U) return 0;
  for (index = 0; index < set->count; ++index) {
    uint32_t offset = set->targets[index] - min_target;
    if ((offset % stride) != 0U) return 0;
  }
  if (((max_target - min_target) / stride) + 1U != set->count) return 0;
  *out_value = sim_value_table_region(section_index, min_target, max_target + stride, stride, M68K_SIM_PROV_TABLE_SCAN);
  return 1;
}

static M68kSimValue sim_value_from_target_set(size_t section_index, const M68kSimTargetSet *set, uint8_t provenance) {
  M68kSimValue region;
  if (set == NULL || set->count == 0U) return g_m68k_sim_unknown_value;
  if (set->count == 1U) return sim_value_section_ptr(section_index, set->targets[0], provenance);
  if (sim_target_set_to_table_region(section_index, set, &region)) {
    region.provenance = provenance;
    return region;
  }
  return sim_value_target_set(set, section_index, provenance);
}

static void sim_canonicalize_value(M68kSimValue *value) {
  if (value == NULL) return;
  if (value->kind == M68K_SIM_VALUE_TARGET_SET) {
    *value = sim_value_from_target_set(value->section_index, &value->target_set, value->provenance);
  }
}

static void sim_append_value_targets(M68kSimTargetSet *dst, const M68kSimValue *value) {
  size_t index;
  uint32_t cursor;
  if (dst == NULL || value == NULL) return;
  if (value->kind == M68K_SIM_VALUE_SECTION_PTR) {
    m68k_sim_target_set_add(dst, value->value);
    return;
  }
  if (value->kind == M68K_SIM_VALUE_TABLE_REGION) {
    uint32_t stride = value->table_stride == 0U ? 4U : value->table_stride;
    for (cursor = value->table_start; stride != 0U && cursor < value->table_end; cursor += stride)
      m68k_sim_target_set_add(dst, cursor);
    return;
  }
  if (value->kind != M68K_SIM_VALUE_TARGET_SET) return;
  for (index = 0; index < value->target_set.count; ++index) {
    m68k_sim_target_set_add(dst, value->target_set.targets[index]);
  }
}

static uint8_t sim_result_provenance(uint8_t lhs, uint8_t rhs, uint8_t fallback) {
  if (lhs == M68K_SIM_PROV_TABLE_SCAN || rhs == M68K_SIM_PROV_TABLE_SCAN) return M68K_SIM_PROV_TABLE_SCAN;
  if (lhs == M68K_SIM_PROV_MEMORY_LOAD || rhs == M68K_SIM_PROV_MEMORY_LOAD) return M68K_SIM_PROV_MEMORY_LOAD;
  if (lhs == M68K_SIM_PROV_PC_REL || rhs == M68K_SIM_PROV_PC_REL) return M68K_SIM_PROV_PC_REL;
  if (lhs == M68K_SIM_PROV_ADDRESS_ARITH || rhs == M68K_SIM_PROV_ADDRESS_ARITH) return M68K_SIM_PROV_ADDRESS_ARITH;
  if (lhs == M68K_SIM_PROV_REGISTER_COPY || rhs == M68K_SIM_PROV_REGISTER_COPY) return M68K_SIM_PROV_REGISTER_COPY;
  if (lhs == M68K_SIM_PROV_IMMEDIATE && rhs == M68K_SIM_PROV_IMMEDIATE) return M68K_SIM_PROV_IMMEDIATE;
  return fallback;
}

static int sim_value_is_path_stable_for_flags(const M68kSimValue *value) {
  if (value == NULL || value->kind != M68K_SIM_VALUE_CONSTANT) return 0;
  return value->provenance != M68K_SIM_PROV_MEMORY_LOAD &&
    value->provenance != M68K_SIM_PROV_TABLE_SCAN &&
    value->provenance != M68K_SIM_PROV_PC_REL;
}

static M68kSimValue sim_value_join(const M68kSimValue *lhs, const M68kSimValue *rhs) {
  if (lhs == NULL) return rhs != NULL ? *rhs : g_m68k_sim_unknown_value;
  if (rhs == NULL) return *lhs;
  if (lhs->kind == M68K_SIM_VALUE_UNKNOWN || rhs->kind == M68K_SIM_VALUE_UNKNOWN)
    return g_m68k_sim_unknown_value;
  if (sim_value_equal(lhs, rhs)) return *lhs;
  if (lhs->kind == M68K_SIM_VALUE_TABLE_REGION && rhs->kind == M68K_SIM_VALUE_TABLE_REGION &&
      lhs->section_index == rhs->section_index) {
    if (lhs->table_start == rhs->table_start &&
        lhs->table_end == rhs->table_end &&
        lhs->table_stride == rhs->table_stride) {
      return *lhs;
    }
    return g_m68k_sim_unknown_value;
  }
  if (lhs->kind == M68K_SIM_VALUE_TABLE_REGION && sim_table_region_contains(lhs, rhs)) return *lhs;
  if (rhs->kind == M68K_SIM_VALUE_TABLE_REGION && sim_table_region_contains(rhs, lhs)) return *rhs;
  if ((lhs->kind == M68K_SIM_VALUE_SECTION_PTR || lhs->kind == M68K_SIM_VALUE_TARGET_SET ||
        lhs->kind == M68K_SIM_VALUE_TABLE_REGION) &&
      (rhs->kind == M68K_SIM_VALUE_SECTION_PTR || rhs->kind == M68K_SIM_VALUE_TARGET_SET ||
        rhs->kind == M68K_SIM_VALUE_TABLE_REGION) &&
      lhs->section_index == rhs->section_index) {
    M68kSimTargetSet targets;
    m68k_sim_target_set_init(&targets);
    sim_append_value_targets(&targets, lhs);
    sim_append_value_targets(&targets, rhs);
    return sim_value_from_target_set(lhs->section_index, &targets, M68K_SIM_PROV_TABLE_SCAN);
  }
  return g_m68k_sim_unknown_value;
}

static void sim_merge_target_set(M68kSimTargetSet *dst, const M68kSimTargetSet *src) {
  size_t index;
  if (dst == NULL || src == NULL) return;
  for (index = 0; index < src->count; ++index) m68k_sim_target_set_add(dst, src->targets[index]);
}

int m68k_sim_cpu_state_equal(const M68kSimCpuState *lhs, const M68kSimCpuState *rhs) {
  size_t index;
  if (lhs == NULL || rhs == NULL) return 0;
  for (index = 0; index < 8U; ++index) {
    if (!sim_value_equal(&lhs->d[index], &rhs->d[index])) return 0;
    if (!sim_value_equal(&lhs->a[index], &rhs->a[index])) return 0;
  }
  for (index = 0; index < M68K_SIM_CONTROL_REGISTER_LIMIT; ++index) {
    if (!sim_value_equal(&lhs->c[index], &rhs->c[index])) return 0;
  }
  return lhs->pc == rhs->pc && lhs->sr == rhs->sr && lhs->sr_known == rhs->sr_known;
}

int m68k_sim_cpu_state_join(M68kSimCpuState *dst, const M68kSimCpuState *src) {
  int changed = 0;
  size_t index;
  if (dst == NULL || src == NULL) return 0;
  for (index = 0; index < 8U; ++index) {
    M68kSimValue joined = sim_value_join(&dst->d[index], &src->d[index]);
    if (!sim_value_equal(&joined, &dst->d[index])) {
      dst->d[index] = joined;
      changed = 1;
    }
    joined = sim_value_join(&dst->a[index], &src->a[index]);
    if (!sim_value_equal(&joined, &dst->a[index])) {
      dst->a[index] = joined;
      changed = 1;
    }
  }
  for (index = 0; index < M68K_SIM_CONTROL_REGISTER_LIMIT; ++index) {
    M68kSimValue joined = sim_value_join(&dst->c[index], &src->c[index]);
    if (!sim_value_equal(&joined, &dst->c[index])) {
      dst->c[index] = joined;
      changed = 1;
    }
  }
  if (dst->sr_known == 0U || src->sr_known == 0U || dst->sr != src->sr) {
    if (dst->sr_known != 0U || dst->sr != 0U) {
      dst->sr = 0U;
      dst->sr_known = 0U;
      changed = 1;
    }
  }
  return changed;
}

int m68k_sim_memory_state_equal(const M68kSimMemoryState *lhs, const M68kSimMemoryState *rhs) {
  size_t index;
  if (lhs == NULL || rhs == NULL) return 0;
  if (lhs->cell_count != rhs->cell_count) return 0;
  for (index = 0; index < lhs->cell_count; ++index) {
    if (lhs->cells[index].width != rhs->cells[index].width ||
        lhs->cells[index].section_index != rhs->cells[index].section_index ||
        lhs->cells[index].offset != rhs->cells[index].offset ||
        !sim_value_equal(&lhs->cells[index].value, &rhs->cells[index].value)) {
      return 0;
    }
  }
  return 1;
}

int m68k_sim_memory_state_join(M68kSimMemoryState *dst, const M68kSimMemoryState *src) {
  size_t index;
  int changed = 0;
  if (dst == NULL || src == NULL) return 0;
  for (index = 0; index < src->cell_count; ++index) {
    const M68kSimMemoryCell *cell = &src->cells[index];
    size_t dst_index;
    for (dst_index = 0; dst_index < dst->cell_count; ++dst_index) {
      M68kSimMemoryCell *dst_cell = &dst->cells[dst_index];
      if (dst_cell->offset != cell->offset || dst_cell->width != cell->width ||
          dst_cell->section_index != cell->section_index) continue;
      {
        M68kSimValue joined = sim_value_join(&dst_cell->value, &cell->value);
        if (!sim_value_equal(&joined, &dst_cell->value)) {
          dst_cell->value = joined;
          changed = 1;
        }
      }
      break;
    }
    if (dst_index == dst->cell_count && dst->cell_count < M68K_SIM_MEMORY_CELL_LIMIT) {
      dst->cells[dst->cell_count++] = *cell;
      changed = 1;
    }
  }
  return changed;
}

int m68k_sim_memory_state_seed_same_section_fixups(const M68kObject *object, size_t section_index,
    const M68kSection *section, M68kSimMemoryState *state) {
  size_t index;
  if (object == NULL || section == NULL || state == NULL) return 0;
  m68k_sim_memory_state_init(state);
  for (index = 0; index < object->fixup_count; ++index) {
    const M68kFixup *fixup = &object->fixups[index];
    uint32_t raw_value;
    M68kSimValue value;
    if (fixup->section_index != section_index || fixup->kind != M68K_FIXUP_ABS ||
        fixup->width != M68K_FIXUP_WIDTH_32 || !fixup->has_target_section ||
        fixup->target_section_index != section_index || fixup->offset + 4U > section->data_size) {
      continue;
    }
    raw_value = m68k_read_u32be(section->data + fixup->offset);
    if (raw_value < section->data_size) {
      value = sim_value_section_ptr(section_index, raw_value, M68K_SIM_PROV_MEMORY_LOAD);
    } else if (fixup->addend >= 0 && (uint32_t)fixup->addend < section->data_size) {
      value = sim_value_section_ptr(section_index, (uint32_t)fixup->addend, M68K_SIM_PROV_MEMORY_LOAD);
    } else {
      continue;
    }
    sim_memory_state_store(state, 4U, section_index, fixup->offset, &value);
  }
  return 1;
}

static int sim_register_is_direct(const M68kOperandIR *operand, uint8_t *is_address, uint8_t *reg);

static uint8_t sim_infer_ea_shape(const M68kOperandIR *operand) {
  if (operand == NULL) return M68K_SIM_EA_SHAPE_NONE;
  if (operand->kind == M68K_ASM_OPERAND_IND) return M68K_SIM_EA_SHAPE_INDIRECT;
  if (operand->kind == M68K_ASM_OPERAND_POSTINC) return M68K_SIM_EA_SHAPE_POSTINCREMENT;
  if (operand->kind == M68K_ASM_OPERAND_ABSL) return M68K_SIM_EA_SHAPE_ABSOLUTE_LONG;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return M68K_SIM_EA_SHAPE_NONE;
  if (operand->value.ea_mode == 2U) return M68K_SIM_EA_SHAPE_INDIRECT;
  if (operand->value.ea_mode == 3U) return M68K_SIM_EA_SHAPE_POSTINCREMENT;
  if (operand->value.ea_mode == 4U) return M68K_SIM_EA_SHAPE_PREDECREMENT;
  if (operand->value.ea_mode == 5U) return M68K_SIM_EA_SHAPE_DISPLACEMENT;
  if (operand->value.ea_mode == 6U) return M68K_SIM_EA_SHAPE_INDEX;
  if (operand->value.ea_mode == 7U && operand->value.ea_reg == 0U) return M68K_SIM_EA_SHAPE_ABSOLUTE_WORD;
  if (operand->value.ea_mode == 7U && operand->value.ea_reg == 1U) return M68K_SIM_EA_SHAPE_ABSOLUTE_LONG;
  if (operand->value.ea_mode == 7U && operand->value.ea_reg == 2U) return M68K_SIM_EA_SHAPE_PC_DISPLACEMENT;
  if (operand->value.ea_mode == 7U && operand->value.ea_reg == 3U) return M68K_SIM_EA_SHAPE_PC_INDEX;
  return M68K_SIM_EA_SHAPE_NONE;
}

static int sim_operand_is_immediate_ea(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_ABSL) &&
    operand->value.ea_mode == 7U && operand->value.ea_reg == 4U;
}

static int sim_operand_is_absolute_long_ea(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  return sim_infer_ea_shape(operand) == M68K_SIM_EA_SHAPE_ABSOLUTE_LONG;
}

static int sim_operand_matches_expected_kind(uint8_t expected_kind, const M68kOperandIR *operand) {
  uint8_t ea_shape;
  if (operand == NULL) return 0;
  ea_shape = sim_infer_ea_shape(operand);
  if (expected_kind == M68K_SIM_EXPECT_ANY) return 1;
  if (expected_kind == M68K_SIM_EXPECT_DN) return operand->kind == M68K_ASM_OPERAND_DN;
  if (expected_kind == M68K_SIM_EXPECT_AN) return operand->kind == M68K_ASM_OPERAND_AN;
  if (expected_kind == M68K_SIM_EXPECT_RN) return operand->kind == M68K_ASM_OPERAND_RN || operand->kind == M68K_ASM_OPERAND_RN_PAIR;
  if (expected_kind == M68K_SIM_EXPECT_IND) return ea_shape == M68K_SIM_EA_SHAPE_INDIRECT;
  if (expected_kind == M68K_SIM_EXPECT_POSTINC) return ea_shape == M68K_SIM_EA_SHAPE_POSTINCREMENT;
  if (expected_kind == M68K_SIM_EXPECT_PREDEC) return ea_shape == M68K_SIM_EA_SHAPE_PREDECREMENT;
  if (expected_kind == M68K_SIM_EXPECT_DISP) return ea_shape == M68K_SIM_EA_SHAPE_DISPLACEMENT;
  if (expected_kind == M68K_SIM_EXPECT_INDEX) return ea_shape == M68K_SIM_EA_SHAPE_INDEX;
  if (expected_kind == M68K_SIM_EXPECT_ABSW) return ea_shape == M68K_SIM_EA_SHAPE_ABSOLUTE_WORD;
  if (expected_kind == M68K_SIM_EXPECT_ABSL) return ea_shape == M68K_SIM_EA_SHAPE_ABSOLUTE_LONG;
  if (expected_kind == M68K_SIM_EXPECT_PCDISP) return ea_shape == M68K_SIM_EA_SHAPE_PC_DISPLACEMENT;
  if (expected_kind == M68K_SIM_EXPECT_PCINDEX) return ea_shape == M68K_SIM_EA_SHAPE_PC_INDEX;
  if (expected_kind == M68K_SIM_EXPECT_EA) {
    return operand->kind == M68K_ASM_OPERAND_DN || operand->kind == M68K_ASM_OPERAND_AN ||
           operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_IND ||
           operand->kind == M68K_ASM_OPERAND_POSTINC || operand->kind == M68K_ASM_OPERAND_ABSL ||
           operand->kind == M68K_ASM_OPERAND_BF_EA;
  }
  if (expected_kind == M68K_SIM_EXPECT_IMM) return operand->kind == M68K_ASM_OPERAND_IMM;
  if (expected_kind == M68K_SIM_EXPECT_LABEL) return operand->kind == M68K_ASM_OPERAND_LABEL;
  if (expected_kind == M68K_SIM_EXPECT_CCR) return operand->kind == M68K_ASM_OPERAND_CCR;
  if (expected_kind == M68K_SIM_EXPECT_CTRL_REG) {
    return operand->kind == M68K_ASM_OPERAND_CTRL_REG ||
      operand->kind == M68K_ASM_OPERAND_CACHE_SEL;
  }
  if (expected_kind == M68K_SIM_EXPECT_SR) return operand->kind == M68K_ASM_OPERAND_SR;
  if (expected_kind == M68K_SIM_EXPECT_USP) return operand->kind == M68K_ASM_OPERAND_USP;
  if (expected_kind == M68K_SIM_EXPECT_REGLIST) return operand->kind == M68K_ASM_OPERAND_REGLIST;
  return 0;
}

static int sim_expected_kind_prefers_register_write(uint8_t expected_kind, const M68kOperandIR *operand) {
  uint8_t is_address;
  uint8_t reg;
  if (expected_kind == M68K_SIM_EXPECT_DN || expected_kind == M68K_SIM_EXPECT_AN ||
      expected_kind == M68K_SIM_EXPECT_RN) {
    return 1;
  }
  if (expected_kind == M68K_SIM_EXPECT_EA && operand != NULL) return sim_register_is_direct(operand, &is_address, &reg);
  return 0;
}

static int sim_direct_register_slot_by_metadata(const M68kSimFormMetadata *metadata, uint8_t operand_index,
    const M68kOperandIR *operand, uint8_t *out_is_address, uint8_t *out_reg);
static int sim_ea_base_address_value(const M68kSimCpuState *state, const M68kOperandIR *operand, M68kSimValue *out_value);
static int sim_ea_index_value(const M68kSimCpuState *state, const M68kOperandIR *operand, M68kSimValue *out_value);
static int sim_ea_index_value_by_metadata(const M68kSimCpuState *state, const M68kOperandIR *operand,
    uint8_t index_extension_format, uint8_t index_register_class, uint8_t index_value_width_source,
    uint8_t index_scale_source, uint8_t index_sign_source, M68kSimValue *out_value);
static uint32_t sim_ea_index_scale(const M68kOperandIR *operand);

static size_t sim_metadata_operand_count(const M68kSimFormMetadata *metadata) {
  size_t count;
  if (metadata == NULL) return 0;
  for (count = 4U; count > 0U; --count) {
    if (metadata->operand_access_kinds[count - 1U] != M68K_SIM_ACCESS_NONE) return count;
  }
  return 0;
}

static uint8_t sim_find_operand_index_by_access(const M68kSimFormMetadata *metadata, uint8_t access_kind,
    uint8_t skip_index) {
  uint8_t operand_index;
  if (metadata == NULL) return 0xFFU;
  for (operand_index = 0U; operand_index < 4U; ++operand_index) {
    if (operand_index == skip_index) continue;
    if (metadata->operand_access_kinds[operand_index] == access_kind) return operand_index;
  }
  return 0xFFU;
}

const M68kSimFormMetadata *m68k_sim_metadata_for_instruction(const M68kInstructionIR *instruction) {
  size_t index;
  const M68kSimFormMetadata *shape_match = NULL;
  uint8_t mnemonic_id;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id == M68K_ASM_MNEMONIC_NONE) return NULL;
  for (index = 0; index < sizeof(g_m68k_sim_form_lookup) / sizeof(g_m68k_sim_form_lookup[0]); ++index) {
    const M68kSimFormLookup *entry = &g_m68k_sim_form_lookup[index];
    size_t operand_index;
    int shape_matches = 1;
    if (entry->mnemonic_id != mnemonic_id) continue;
    if (instruction->operand_count > 4U) continue;
    if (sim_metadata_operand_count(&entry->metadata) != instruction->operand_count) continue;
    for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
      if (!sim_operand_matches_expected_kind(entry->metadata.operand_expected_kinds[operand_index],
              &instruction->operands[operand_index])) {
        shape_matches = 0;
        break;
      }
    }
    if (!shape_matches) continue;
    if (entry->asm_form_index == instruction->asm_form_index)
      return &entry->metadata;
    if (shape_match != NULL) return NULL;
    shape_match = &entry->metadata;
  }
  return shape_match;
}

static int sim_concrete_compute_ea_address(const M68kOperandIR *operand, uint8_t ea_formula, uint8_t ea_shape,
    uint8_t ea_base_kind, uint8_t displacement_source, uint8_t uses_displacement,
    uint8_t uses_index, uint8_t pc_base_bias_bytes, uint8_t address_literal_width_bytes,
    uint8_t index_extension_format, uint8_t index_register_class, uint8_t index_value_width_source,
    uint8_t index_scale_source, uint8_t index_sign_source,
    const M68kSimConcreteState *state, uint32_t instruction_pc, uint32_t *out_address);

static int sim_register_value(const M68kSimCpuState *state, uint8_t is_address, uint8_t reg, M68kSimValue *out_value) {
  if (state == NULL || out_value == NULL || reg >= 8U) return 0;
  *out_value = is_address ? state->a[reg] : state->d[reg];
  return 1;
}

static int sim_apply_logic(uint8_t op, const M68kSimValue *lhs, const M68kSimValue *rhs, M68kSimValue *out_value) {
  uint32_t value;
  uint8_t provenance;
  if (lhs == NULL || rhs == NULL || out_value == NULL) return 0;
  if (lhs->kind != M68K_SIM_VALUE_CONSTANT || rhs->kind != M68K_SIM_VALUE_CONSTANT) return 0;
  if (op == M68K_SIM_OP_LOGIC_AND) value = lhs->value & rhs->value;
  else if (op == M68K_SIM_OP_LOGIC_OR) value = lhs->value | rhs->value;
  else if (op == M68K_SIM_OP_LOGIC_XOR) value = lhs->value ^ rhs->value;
  else return 0;
  provenance = sim_result_provenance(lhs->provenance, rhs->provenance, M68K_SIM_PROV_REGISTER_COPY);
  *out_value = sim_value_constant(value, provenance);
  return 1;
}

static uint32_t sim_mask_for_width(uint8_t width) {
  if (width >= 4U || width == 0U) return 0xFFFFFFFFU;
  if (width == 2U) return 0x0000FFFFU;
  return 0x000000FFU;
}

static uint8_t sim_operand_width_from_instruction(const M68kInstructionIR *instruction) {
  if (instruction->size_suffix == 'b' || instruction->size_suffix == 'B') return 1U;
  if (instruction->size_suffix == 'w' || instruction->size_suffix == 'W') return 2U;
  return 4U;
}

static uint8_t sim_effective_operand_width(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, uint8_t operand_index) {
  uint8_t mode;
  uint8_t width;
  if (metadata == NULL || operand_index >= 4U) return sim_operand_width_from_instruction(instruction);
  mode = metadata->operand_width_modes[operand_index];
  width = metadata->operand_widths[operand_index];
  if (mode == M68K_SIM_WIDTH_FIXED) return width;
  if (mode == M68K_SIM_WIDTH_INSTRUCTION_SIZE) return sim_operand_width_from_instruction(instruction);
  if (mode == M68K_SIM_WIDTH_FULL_REGISTER) return 4U;
  if (width == 0U) width = sim_operand_width_from_instruction(instruction);
  return width;
}

static uint32_t sim_sign_extend_value(uint32_t value, uint8_t src_bits) {
  uint32_t mask;
  uint32_t sign_bit;
  if (src_bits >= 32U || src_bits == 0U) return value;
  mask = (1U << src_bits) - 1U;
  sign_bit = 1U << (src_bits - 1U);
  value &= mask;
  if ((value & sign_bit) != 0U) value |= ~mask;
  return value;
}

static int sim_apply_unary(uint8_t op, const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    const M68kSimValue *input, M68kSimValue *out_value) {
  uint8_t width;
  uint32_t mask;
  uint32_t value;
  if (metadata == NULL || input == NULL || out_value == NULL) return 0;
  if (input->kind != M68K_SIM_VALUE_CONSTANT) return 0;
  width = sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index);
  mask = sim_mask_for_width(width);
  value = input->value & mask;
  if (op == M68K_SIM_OP_NEGATE) {
    value = (uint32_t)(0U - value) & mask;
  } else if (op == M68K_SIM_OP_NOT) {
    value = (~value) & mask;
  } else if (op == M68K_SIM_OP_SIGN_EXTEND) {
    uint8_t source_bits = metadata->unary_sign_extend_source_bits;
    if (source_bits == 0U) source_bits = width == 2U ? 8U : 16U;
    value = sim_sign_extend_value(value, source_bits);
    if (width < 4U) value &= mask;
  } else if (op == M68K_SIM_OP_SWAP_WORDS) {
    value = (input->value << 16) | (input->value >> 16);
  } else {
    return 0;
  }
  *out_value = sim_value_constant(value, input->provenance != M68K_SIM_PROV_NONE ? input->provenance
    : M68K_SIM_PROV_REGISTER_COPY);
  return 1;
}

static uint8_t sim_shift_count(const M68kSimFormMetadata *metadata, const M68kSimValue *count_value) {
  uint32_t count;
  if (metadata == NULL) return 0U;
  if (metadata->shift_count_source == M68K_SIM_SHIFT_COUNT_IMPLICIT_ONE) return 1U;
  if (metadata->shift_count_source != M68K_SIM_SHIFT_COUNT_OPERAND ||
      count_value == NULL || count_value->kind != M68K_SIM_VALUE_CONSTANT) {
    return 0U;
  }
  count = count_value->value;
  if (metadata->shift_count_modulus != 0U) count %= metadata->shift_count_modulus;
  return (uint8_t)count;
}

static int sim_apply_shift_rotate(uint8_t op, const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    const M68kSimValue *input, const M68kSimValue *count_value, uint16_t sr, M68kSimValue *out_value,
    uint16_t *out_sr) {
  uint8_t width, count;
  uint32_t mask, value, result, width_bits, sign_bit;
  uint32_t carry = 0U;
  uint32_t extend = (sr & 0x0010U) != 0U ? 1U : 0U;
  uint32_t initial_extend = extend;
  uint16_t next_sr;
  uint8_t provenance;
  if (metadata == NULL || input == NULL || out_value == NULL) return 0;
  if (input->kind != M68K_SIM_VALUE_CONSTANT) return 0;
  provenance = sim_result_provenance(input->provenance, count_value != NULL ? count_value->provenance : M68K_SIM_PROV_NONE,
    input->provenance != M68K_SIM_PROV_NONE ? input->provenance : M68K_SIM_PROV_REGISTER_COPY);
  count = sim_shift_count(metadata, count_value);
  width = sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index);
  width_bits = width == 0U ? 32U : (uint32_t)width * 8U;
  mask = sim_mask_for_width(width);
  value = input->value & mask;
  sign_bit = width_bits == 0U ? 0U : (1U << (width_bits - 1U));
  if (count == 0U) {
    *out_value = sim_value_constant(value, provenance);
    if (out_sr != NULL) *out_sr = sr;
    return 1;
  }
  if (op == M68K_SIM_OP_SHIFT) {
    result = value;
    while (count-- != 0U) {
      if (metadata->shift_direction == M68K_SIM_SHIFT_DIR_LEFT) {
        carry = (result >> (width_bits - 1U)) & 1U;
        result = (result << 1U) & mask;
        extend = carry;
      } else if (metadata->shift_direction == M68K_SIM_SHIFT_DIR_RIGHT) {
        carry = result & 1U;
        if (metadata->shift_fill_mode == M68K_SIM_SHIFT_FILL_SIGN) result = (result >> 1U) | (result & sign_bit);
        else result >>= 1U;
        extend = carry;
      } else {
        return 0;
      }
    }
  } else if (op == M68K_SIM_OP_ROTATE || op == M68K_SIM_OP_ROTATE_EXTEND) {
    uint32_t rotate_width = width_bits + (op == M68K_SIM_OP_ROTATE_EXTEND ? metadata->shift_rotate_extra_bits : 0U);
    if (rotate_width == 0U) return 0;
    count = (uint8_t)(count % rotate_width);
    if (count == 0U) {
      *out_value = sim_value_constant(value, provenance);
      if (out_sr != NULL) *out_sr = sr;
      return 1;
    }
    result = value;
    if (op == M68K_SIM_OP_ROTATE_EXTEND) {
      while (count-- != 0U) {
        if (metadata->shift_direction == M68K_SIM_SHIFT_DIR_LEFT) {
          carry = (result >> (width_bits - 1U)) & 1U;
          result = ((result << 1U) & mask) | extend;
          extend = carry;
        } else if (metadata->shift_direction == M68K_SIM_SHIFT_DIR_RIGHT) {
          carry = result & 1U;
          result = (result >> 1U) | (extend << (width_bits - 1U));
          extend = carry;
        } else {
          return 0;
        }
      }
    } else {
      while (count-- != 0U) {
        if (metadata->shift_direction == M68K_SIM_SHIFT_DIR_LEFT) {
          carry = (result >> (width_bits - 1U)) & 1U;
          result = ((result << 1U) & mask) | carry;
        } else if (metadata->shift_direction == M68K_SIM_SHIFT_DIR_RIGHT) {
          carry = result & 1U;
          result = (result >> 1U) | (carry << (width_bits - 1U));
        } else {
          return 0;
        }
      }
    }
  } else {
    return 0;
  }
  next_sr = (uint16_t)(sr & ~0x001FU);
  if ((result & mask) == 0U) next_sr |= 0x0004U;
  if (((result & mask) & sign_bit) != 0U) next_sr |= 0x0008U;
  if (op == M68K_SIM_OP_SHIFT || op == M68K_SIM_OP_ROTATE || op == M68K_SIM_OP_ROTATE_EXTEND) {
    if (carry != 0U) next_sr |= 0x0001U;
  }
  if (op == M68K_SIM_OP_SHIFT) {
    if (extend != 0U) next_sr |= 0x0010U;
  } else if (op == M68K_SIM_OP_ROTATE_EXTEND) {
    if (extend != 0U) next_sr |= 0x0010U;
    if (extend != 0U) next_sr |= 0x0001U;
  } else if (initial_extend != 0U) {
    next_sr |= 0x0010U;
  }
  *out_value = sim_value_constant(result & mask, provenance);
  if (out_sr != NULL) *out_sr = next_sr;
  return 1;
}

static int sim_usp_control_register_index(uint8_t *out_index) {
  return sim_known_control_register_index(M68K_ASM_CONTROL_REGISTER_USP, out_index);
}

static int sim_control_register_index(const M68kOperandIR *operand, uint8_t *out_index) {
  const M68kAsmControlRegisterDef *entry;
  if (operand == NULL || out_index == NULL || operand->kind != M68K_ASM_OPERAND_CTRL_REG) return 0;
  entry = m68k_asm_find_control_register_by_id(operand->value.reg);
  if (entry == NULL || entry->value != operand->value.value ||
      operand->value.reg >= M68K_SIM_CONTROL_REGISTER_LIMIT) return 0;
  *out_index = operand->value.reg;
  return 1;
}

static int sim_control_register_value(const M68kSimCpuState *state, uint8_t reg, M68kSimValue *out_value) {
  if (state == NULL || out_value == NULL || reg >= M68K_SIM_CONTROL_REGISTER_LIMIT) return 0;
  *out_value = state->c[reg];
  return 1;
}

static int sim_special_register_value(const M68kSimCpuState *state, const M68kOperandIR *operand, M68kSimValue *out_value) {
  uint8_t ctrl_reg;
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_CCR) {
    if (state->sr_known == 0U) {
      *out_value = g_m68k_sim_unknown_value;
      return 1;
    }
    *out_value = sim_value_constant((uint32_t)(state->sr & 0x00FFU), M68K_SIM_PROV_REGISTER_COPY);
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_SR) {
    if (state->sr_known == 0U) {
      *out_value = g_m68k_sim_unknown_value;
      return 1;
    }
    *out_value = sim_value_constant(state->sr, M68K_SIM_PROV_REGISTER_COPY);
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_USP && sim_usp_control_register_index(&ctrl_reg)) {
    return sim_control_register_value(state, ctrl_reg, out_value);
  }
  if (sim_control_register_index(operand, &ctrl_reg)) return sim_control_register_value(state, ctrl_reg, out_value);
  return 0;
}

static int sim_register_is_direct(const M68kOperandIR *operand, uint8_t *is_address, uint8_t *reg) {
  return m68k_instruction_operand_direct_register(operand, is_address, reg);
}

static int sim_write_special_register(M68kSimCpuState *state, const M68kOperandIR *operand,
    const M68kSimValue *value, uint8_t width) {
  uint8_t ctrl_reg;
  M68kSimValue stored;
  if (state == NULL || operand == NULL || value == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_CCR) {
    if (value->kind == M68K_SIM_VALUE_CONSTANT) {
      state->sr = (uint16_t)((state->sr & 0xFF00U) | (value->value & 0x00FFU));
      state->sr_known = 1U;
    } else {
      state->sr = 0U;
      state->sr_known = 0U;
    }
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_SR) {
    if (value->kind == M68K_SIM_VALUE_CONSTANT) {
      state->sr = (uint16_t)(value->value & 0xFFFFU);
      state->sr_known = 1U;
    } else {
      state->sr = 0U;
      state->sr_known = 0U;
    }
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_USP && sim_usp_control_register_index(&ctrl_reg)) {
    stored = *value;
    sim_canonicalize_value(&stored);
    state->c[ctrl_reg] = stored;
    return 1;
  }
  if (sim_control_register_index(operand, &ctrl_reg)) {
    stored = *value;
    sim_canonicalize_value(&stored);
    state->c[ctrl_reg] = stored;
    return 1;
  }
  (void)width;
  return 0;
}

static void sim_write_register(M68kSimCpuState *state, const M68kOperandIR *operand, const M68kSimValue *value) {
  uint8_t is_address;
  uint8_t reg;
  M68kSimValue stored;
  if (state == NULL || operand == NULL || value == NULL) return;
  if (sim_write_special_register(state, operand, value, 4U)) return;
  if (!sim_register_is_direct(operand, &is_address, &reg)) return;
  stored = *value;
  sim_canonicalize_value(&stored);
  if (is_address) state->a[reg] = stored;
  else state->d[reg] = stored;
}

static int sim_write_register_sized(M68kSimCpuState *state, const M68kOperandIR *operand,
    const M68kSimValue *value, uint8_t width) {
  uint8_t is_address;
  uint8_t reg;
  M68kSimValue merged;
  M68kSimValue stored;
  if (state == NULL || operand == NULL || value == NULL) return 0;
  if (sim_write_special_register(state, operand, value, width)) return 1;
  if (!sim_register_is_direct(operand, &is_address, &reg)) return 0;
  if (width >= 4U || is_address) {
    stored = *value;
    sim_canonicalize_value(&stored);
    if (is_address) state->a[reg] = stored;
    else state->d[reg] = stored;
    return 1;
  }
  if (value->kind == M68K_SIM_VALUE_CONSTANT) {
    const M68kSimValue *current = is_address ? &state->a[reg] : &state->d[reg];
    uint32_t mask = width == 1U ? 0xFFU : 0xFFFFU;
    if (current->kind == M68K_SIM_VALUE_CONSTANT) {
      merged = sim_value_constant((current->value & ~mask) | (value->value & mask), value->provenance);
      if (is_address) state->a[reg] = merged;
      else state->d[reg] = merged;
      return 1;
    }
  }
  if (is_address) state->a[reg] = g_m68k_sim_unknown_value;
  else state->d[reg] = g_m68k_sim_unknown_value;
  return 1;
}

static int sim_write_operand_by_metadata(const M68kSection *section, const M68kInstructionIR *instruction,
    uint32_t offset, size_t section_index, M68kSimStepResult *result, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, const M68kOperandIR *operand, M68kSimCpuState *state, const M68kSimValue *value) {
  uint8_t access_kind;
  uint8_t width;
  M68kSimValue address;
  if (section == NULL || result == NULL || metadata == NULL || operand == NULL ||
      state == NULL || value == NULL || operand_index >= 4U) return 0;
  access_kind = metadata->operand_access_kinds[operand_index];
  width = sim_effective_operand_width(instruction, metadata, operand_index);
  if (access_kind == M68K_SIM_ACCESS_REGISTER_WRITE) return sim_write_register_sized(state, operand, value, width);
  if (access_kind == M68K_SIM_ACCESS_MEMORY_WRITE) {
    if (sim_expected_kind_prefers_register_write(metadata->operand_expected_kinds[operand_index], operand)) {
      return sim_write_register_sized(state, operand, value, width);
    }
    if (!sim_compute_ea_address(section, instruction, offset, operand,
          metadata->operand_ea_address_formulas[operand_index],
          metadata->operand_ea_address_shapes[operand_index], metadata->operand_ea_base_kinds[operand_index],
          metadata->operand_ea_displacement_sources[operand_index],
          metadata->operand_ea_uses_displacement[operand_index], metadata->operand_ea_uses_index[operand_index],
          metadata->operand_ea_pc_base_bias_bytes[operand_index],
          metadata->operand_ea_address_literal_width_bytes[operand_index],
          metadata->operand_ea_index_extension_formats[operand_index],
          metadata->operand_ea_index_register_classes[operand_index],
          metadata->operand_ea_index_value_width_sources[operand_index],
          metadata->operand_ea_index_scale_sources[operand_index],
          metadata->operand_ea_index_sign_sources[operand_index],
          state, section_index, &address)) {
      return 0;
    }
    if (address.kind == M68K_SIM_VALUE_SECTION_PTR && address.value < section->data_size) {
      m68k_sim_target_set_add(&result->discovered_labels, address.value);
      sim_add_memory_write(result, width, section_index, address.value, value);
      return sim_add_access(result, M68K_SIM_ACCESS_MEMORY_WRITE, width, section_index, address.value);
    }
  }
  return 0;
}

static const M68kFixup *find_same_section_fixup(const M68kObject *object, size_t section_index, uint32_t offset) {
  size_t index;
  if (object == NULL) return NULL;
  for (index = 0; index < object->fixup_count; ++index) {
    const M68kFixup *fixup = &object->fixups[index];
    if (fixup->section_index == section_index && fixup->offset == offset &&
        fixup->kind == M68K_FIXUP_ABS && fixup->width == M68K_FIXUP_WIDTH_32 &&
        fixup->has_target_section && fixup->target_section_index == section_index) {
      return fixup;
    }
  }
  return NULL;
}

static int sim_add_access(M68kSimStepResult *result, uint8_t kind, uint8_t width,
    size_t section_index, uint32_t offset) {
  if (result == NULL || result->access_count >= 8U) return 0;
  result->accesses[result->access_count].kind = kind;
  result->accesses[result->access_count].width = width;
  result->accesses[result->access_count].section_index = (uint8_t)section_index;
  result->accesses[result->access_count].offset = offset;
  result->access_count += 1U;
  return 1;
}

static int sim_add_memory_write(M68kSimStepResult *result, uint8_t width, size_t section_index, uint32_t offset,
    const M68kSimValue *value) {
  M68kSimValue stored;
  if (result == NULL || value == NULL || result->memory_write_count >= M68K_SIM_MEMORY_WRITE_LIMIT) return 0;
  stored = *value;
  sim_canonicalize_value(&stored);
  result->memory_writes[result->memory_write_count].width = width;
  result->memory_writes[result->memory_write_count].section_index = (uint8_t)section_index;
  result->memory_writes[result->memory_write_count].offset = offset;
  result->memory_writes[result->memory_write_count].value = stored;
  result->memory_write_count += 1U;
  return 1;
}

static int sim_memory_state_store(M68kSimMemoryState *state, uint8_t width, size_t section_index, uint32_t offset,
    const M68kSimValue *value) {
  size_t index;
  M68kSimValue stored;
  if (state == NULL || value == NULL) return 0;
  stored = *value;
  sim_canonicalize_value(&stored);
  for (index = 0; index < state->cell_count; ++index) {
    M68kSimMemoryCell *cell = &state->cells[index];
    if (cell->offset == offset && cell->width == width && cell->section_index == (uint8_t)section_index) {
      cell->value = stored;
      return 1;
    }
  }
  if (state->cell_count >= M68K_SIM_MEMORY_CELL_LIMIT) return 0;
  state->cells[state->cell_count].width = width;
  state->cells[state->cell_count].section_index = (uint8_t)section_index;
  state->cells[state->cell_count].offset = offset;
  state->cells[state->cell_count].value = stored;
  state->cell_count += 1U;
  return 1;
}

static int sim_compute_ea_address(const M68kSection *section, const M68kInstructionIR *instruction, uint32_t offset,
    const M68kOperandIR *operand, uint8_t ea_formula, uint8_t ea_shape, uint8_t ea_base_kind,
    uint8_t displacement_source, uint8_t uses_displacement, uint8_t uses_index, uint8_t pc_base_bias_bytes,
    uint8_t address_literal_width_bytes, uint8_t index_extension_format, uint8_t index_register_class,
    uint8_t index_value_width_source, uint8_t index_scale_source, uint8_t index_sign_source,
    const M68kSimCpuState *state, size_t section_index, M68kSimValue *out_value) {
  M68kSimValue base;
  M68kSimValue index_value;
  (void)instruction;
  if (section == NULL || operand == NULL || state == NULL || out_value == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA &&
      operand->kind != M68K_ASM_OPERAND_IND &&
      operand->kind != M68K_ASM_OPERAND_POSTINC && operand->kind != M68K_ASM_OPERAND_ABSL) {
    return 0;
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_AN && ea_base_kind == M68K_SIM_EA_BASE_AN) {
    return sim_ea_base_address_value(state, operand, out_value);
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_AN_PLUS_DISP) {
    if (ea_base_kind == M68K_SIM_EA_BASE_AN && displacement_source == M68K_SIM_EA_DISP_OPERAND_VALUE &&
        uses_displacement) {
      if (!sim_ea_base_address_value(state, operand, &base) || base.kind != M68K_SIM_VALUE_SECTION_PTR) return 0;
      *out_value = sim_value_section_ptr(base.section_index,
        (uint32_t)((int32_t)base.value + (int32_t)operand->value.value), M68K_SIM_PROV_ADDRESS_ARITH);
      return 1;
    }
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_ABSOLUTE_LITERAL) {
    if (ea_base_kind == M68K_SIM_EA_BASE_ABSOLUTE && address_literal_width_bytes != 0U &&
        operand->value.value < section->data_size) {
      *out_value = sim_value_section_ptr(section_index, operand->value.value, M68K_SIM_PROV_IMMEDIATE);
      return 1;
    }
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_PC_PLUS_DISP) {
    uint8_t pc_bias;
    if (ea_base_kind == M68K_SIM_EA_BASE_PC && displacement_source == M68K_SIM_EA_DISP_OPERAND_VALUE &&
        uses_displacement) {
      pc_bias = pc_base_bias_bytes != 0U ? pc_base_bias_bytes : 2U;
      *out_value = sim_value_section_ptr(section_index,
        (uint32_t)((int32_t)(offset + pc_bias) + (int32_t)operand->value.value), M68K_SIM_PROV_PC_REL);
      return out_value->value < section->data_size;
    }
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_AN_PLUS_DISP_PLUS_INDEX) {
    if (ea_base_kind == M68K_SIM_EA_BASE_AN && displacement_source == M68K_SIM_EA_DISP_OPERAND_VALUE &&
        uses_displacement && uses_index) {
      if (!sim_ea_base_address_value(state, operand, &base) || base.kind != M68K_SIM_VALUE_SECTION_PTR ||
          !sim_ea_index_value_by_metadata(state, operand, index_extension_format, index_register_class,
            index_value_width_source, index_scale_source, index_sign_source, &index_value) ||
          index_value.kind != M68K_SIM_VALUE_CONSTANT) {
        return 0;
      }
      *out_value = sim_value_section_ptr(base.section_index,
        (uint32_t)((int32_t)base.value + (int32_t)operand->value.value + (int32_t)index_value.value),
        M68K_SIM_PROV_ADDRESS_ARITH);
      return 1;
    }
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_PC_PLUS_DISP_PLUS_INDEX) {
    uint8_t pc_bias;
    if (ea_base_kind == M68K_SIM_EA_BASE_PC && displacement_source == M68K_SIM_EA_DISP_OPERAND_VALUE &&
        uses_displacement && uses_index &&
        sim_ea_index_value_by_metadata(state, operand, index_extension_format, index_register_class,
          index_value_width_source, index_scale_source, index_sign_source, &index_value) &&
        index_value.kind == M68K_SIM_VALUE_CONSTANT) {
      pc_bias = pc_base_bias_bytes != 0U ? pc_base_bias_bytes : 2U;
      *out_value = sim_value_section_ptr(section_index,
        (uint32_t)((int32_t)(offset + pc_bias) + (int32_t)operand->value.value + (int32_t)index_value.value),
        M68K_SIM_PROV_PC_REL);
      return out_value->value < section->data_size;
    }
  }
  ea_shape = sim_effective_ea_shape(ea_shape, operand);
  if (ea_shape == M68K_SIM_EA_SHAPE_INDIRECT || ea_shape == M68K_SIM_EA_SHAPE_POSTINCREMENT ||
      ea_shape == M68K_SIM_EA_SHAPE_PREDECREMENT) {
    return sim_ea_base_address_value(state, operand, out_value);
  }
  if (ea_shape == M68K_SIM_EA_SHAPE_DISPLACEMENT) {
    if (!sim_ea_base_address_value(state, operand, &base) || base.kind != M68K_SIM_VALUE_SECTION_PTR) return 0;
    *out_value = sim_value_section_ptr(base.section_index,
      (uint32_t)((int32_t)base.value + (int32_t)operand->value.value), M68K_SIM_PROV_ADDRESS_ARITH);
    return 1;
  }
  if (ea_shape == M68K_SIM_EA_SHAPE_INDEX) {
    if (!sim_ea_base_address_value(state, operand, &base) || base.kind != M68K_SIM_VALUE_SECTION_PTR) return 0;
    if (!sim_ea_index_value_by_metadata(state, operand, index_extension_format, index_register_class,
          index_value_width_source, index_scale_source, index_sign_source, &index_value)) {
      if (!sim_ea_index_value(state, operand, &index_value) || index_value.kind != M68K_SIM_VALUE_CONSTANT) return 0;
      index_value.value = (uint32_t)((int32_t)index_value.value * (int32_t)sim_ea_index_scale(operand));
    }
    if (index_value.kind != M68K_SIM_VALUE_CONSTANT) return 0;
    *out_value = sim_value_section_ptr(base.section_index,
      (uint32_t)((int32_t)base.value + (int32_t)operand->value.value + (int32_t)index_value.value),
      M68K_SIM_PROV_ADDRESS_ARITH);
    return 1;
  }
  if ((ea_shape == M68K_SIM_EA_SHAPE_ABSOLUTE_WORD || ea_shape == M68K_SIM_EA_SHAPE_ABSOLUTE_LONG) &&
      operand->value.value < section->data_size) {
    *out_value = sim_value_section_ptr(section_index, operand->value.value, M68K_SIM_PROV_IMMEDIATE);
    return 1;
  }
  if (ea_shape == M68K_SIM_EA_SHAPE_PC_DISPLACEMENT) {
    uint8_t pc_bias = pc_base_bias_bytes != 0U ? pc_base_bias_bytes : 2U;
    *out_value = sim_value_section_ptr(section_index,
      (uint32_t)((int32_t)(offset + pc_bias) + (int32_t)operand->value.value), M68K_SIM_PROV_PC_REL);
    return out_value->value < section->data_size;
  }
  if (ea_shape == M68K_SIM_EA_SHAPE_PC_INDEX) {
    uint8_t pc_bias = pc_base_bias_bytes != 0U ? pc_base_bias_bytes : 2U;
    if (!sim_ea_index_value_by_metadata(state, operand, index_extension_format, index_register_class,
          index_value_width_source, index_scale_source, index_sign_source, &index_value)) {
      if (!sim_ea_index_value(state, operand, &index_value) || index_value.kind != M68K_SIM_VALUE_CONSTANT) return 0;
      index_value.value = (uint32_t)((int32_t)index_value.value * (int32_t)sim_ea_index_scale(operand));
    }
    if (index_value.kind != M68K_SIM_VALUE_CONSTANT) return 0;
    *out_value = sim_value_section_ptr(section_index,
      (uint32_t)((int32_t)(offset + pc_bias) + (int32_t)operand->value.value + (int32_t)index_value.value),
      M68K_SIM_PROV_PC_REL);
    return out_value->value < section->data_size;
  }
  return 0;
}

static int sim_collect_same_section_fixup_targets(const M68kObject *object, size_t section_index,
    const M68kSection *section, const M68kSimMemoryState *memory_state, uint32_t table_offset,
    M68kSimValue *out_value) {
  uint32_t cursor;
  uint32_t region_end;
  uint32_t alignment;
  int found_base = 0;
  if (section == NULL || memory_state == NULL || out_value == NULL) return 0;
  (void)object;
  alignment = table_offset & 3U;
  region_end = table_offset + 4U;
  for (;;) {
    size_t cell_index;
    uint32_t next_offset = UINT32_MAX;
    for (cell_index = 0; cell_index < memory_state->cell_count; ++cell_index) {
      const M68kSimMemoryCell *candidate = &memory_state->cells[cell_index];
      if (candidate->section_index != (uint8_t)section_index || candidate->width != 4U ||
          (candidate->offset & 3U) != alignment || candidate->offset < table_offset) {
        continue;
      }
      if (candidate->offset == table_offset) found_base = 1;
      if (candidate->offset >= region_end && candidate->offset <= region_end + 4U &&
          candidate->offset < next_offset) {
        next_offset = candidate->offset;
      }
    }
    if (next_offset == UINT32_MAX) break;
    region_end = next_offset + 4U;
  }
  if (!found_base) return 0;
  for (cursor = table_offset; cursor < region_end && cursor + 4U <= section->data_size; cursor += 4U) {
    size_t cell_index;
    const M68kSimMemoryCell *cell = NULL;
    for (cell_index = 0; cell_index < memory_state->cell_count; ++cell_index) {
      const M68kSimMemoryCell *candidate = &memory_state->cells[cell_index];
      if (candidate->section_index == (uint8_t)section_index && candidate->width == 4U &&
          candidate->offset == cursor) {
        cell = candidate;
        break;
      }
    }
    if (cell == NULL) continue;
    {
      if (cell->value.kind == M68K_SIM_VALUE_SECTION_PTR) {
        /* region remains explicit until a consumer expands it */
      } else if (cell->value.kind == M68K_SIM_VALUE_TARGET_SET) {
        /* nested sets are expanded later by the consumer */
      }
    }
  }
  *out_value = sim_value_table_region(section_index, table_offset, region_end, 4U, M68K_SIM_PROV_TABLE_SCAN);
  return 1;
}

static int sim_read_same_section_memory_value(const M68kObject *object, size_t section_index, const M68kSection *section,
    const M68kSimMemoryState *memory_state, uint32_t address, M68kSimValue *out_value) {
  const M68kFixup *fixup;
  uint32_t raw_value;
  size_t index;
  if (section == NULL || out_value == NULL || address >= section->data_size) return 0;
  if (memory_state != NULL) {
    for (index = 0; index < memory_state->cell_count; ++index) {
      const M68kSimMemoryCell *cell = &memory_state->cells[index];
      if (cell->section_index == (uint8_t)section_index && cell->offset == address && cell->width == 4U) {
        *out_value = cell->value;
        return 1;
      }
    }
  }
  if (address + 4U <= section->data_size) {
    fixup = find_same_section_fixup(object, section_index, address);
    raw_value = m68k_read_u32be(section->data + address);
    if (fixup != NULL && raw_value < section->data_size) {
      *out_value = sim_value_section_ptr(section_index, raw_value, M68K_SIM_PROV_MEMORY_LOAD);
      return 1;
    }
    if (fixup != NULL && fixup->addend >= 0 && (uint32_t)fixup->addend < section->data_size) {
      *out_value = sim_value_section_ptr(section_index, (uint32_t)fixup->addend, M68K_SIM_PROV_MEMORY_LOAD);
      return 1;
    }
    if (raw_value < section->data_size) {
      *out_value = sim_value_section_ptr(section_index, raw_value, M68K_SIM_PROV_MEMORY_LOAD);
      return 1;
    }
    *out_value = sim_value_constant(raw_value, M68K_SIM_PROV_MEMORY_LOAD);
    return 1;
  }
  if (address + 2U <= section->data_size) {
    *out_value = sim_value_constant((uint32_t)m68k_read_u16be(section->data + address), M68K_SIM_PROV_MEMORY_LOAD);
    return 1;
  }
  return 0;
}

static int sim_read_memory_value(const M68kObject *object, size_t section_index, const M68kSection *section,
    const M68kInstructionIR *instruction, uint32_t offset, const M68kOperandIR *operand,
    const M68kSimCpuState *state, const M68kSimMemoryState *memory_state, M68kSimStepResult *result,
    uint8_t width, M68kSimValue *out_value) {
  M68kSimValue address;
  M68kSimValue base;
  if (section == NULL || operand == NULL || state == NULL || out_value == NULL) return 0;
  if (sim_operand_is_immediate_ea(operand)) {
    *out_value = sim_value_constant(operand->value.value, M68K_SIM_PROV_IMMEDIATE);
    return 1;
  }
  if (sim_operand_is_absolute_long_ea(operand)) {
    if (operand->value.value < section->data_size) {
      *out_value = sim_value_section_ptr(section_index, operand->value.value, M68K_SIM_PROV_IMMEDIATE);
    } else {
      *out_value = sim_value_constant(operand->value.value, M68K_SIM_PROV_IMMEDIATE);
    }
    return 1;
  }
  if (!sim_compute_ea_address(section, instruction, offset, operand, M68K_SIM_EA_FORMULA_NONE,
        M68K_SIM_EA_SHAPE_NONE, M68K_SIM_EA_BASE_NONE, M68K_SIM_EA_DISP_NONE, 0U, 0U, 0U, 0U,
        0U, 0U, 0U, 0U, 0U,
        state, section_index, &address)) {
    if (sim_effective_ea_shape(M68K_SIM_EA_SHAPE_NONE, operand) == M68K_SIM_EA_SHAPE_INDEX &&
        sim_ea_base_address_value(state, operand, &base) &&
        base.kind == M68K_SIM_VALUE_SECTION_PTR &&
        sim_collect_same_section_fixup_targets(object, section_index, section, memory_state,
          (uint32_t)((int32_t)base.value + (int32_t)operand->value.value), out_value)) {
      return 1;
    }
    return 0;
  }
  if (address.kind != M68K_SIM_VALUE_SECTION_PTR || address.value >= section->data_size) return 0;
  sim_add_access(result, 1U, width, section_index, address.value);
  return sim_read_same_section_memory_value_sized(object, section_index, section, memory_state, address.value, width,
    out_value);
}

static int sim_eval_operand_by_metadata(const M68kObject *object, size_t section_index, const M68kSection *section,
    const M68kInstructionIR *instruction, uint32_t offset, const M68kSimFormMetadata *metadata, uint8_t operand_index,
    const M68kOperandIR *operand, const M68kSimCpuState *state, const M68kSimMemoryState *memory_state,
    M68kSimStepResult *result, M68kSimValue *out_value) {
  uint8_t access_kind;
  uint8_t is_address;
  uint8_t reg;
  if (metadata == NULL || operand == NULL || out_value == NULL || operand_index >= 4U) return 0;
  access_kind = metadata->operand_access_kinds[operand_index];
  m68k_sim_value_init_unknown(out_value);
  if (access_kind == M68K_SIM_ACCESS_IMMEDIATE) return sim_operand_is_immediate_value(operand, &out_value->value) ?
      (*out_value = sim_value_constant(out_value->value, M68K_SIM_PROV_IMMEDIATE), 1) : 0;
  if (access_kind == M68K_SIM_ACCESS_REGISTER_READ || access_kind == M68K_SIM_ACCESS_REGISTER_WRITE) {
    if (sim_special_register_value(state, operand, out_value)) return 1;
    if (!sim_direct_register_slot_by_metadata(metadata, operand_index, operand, &is_address, &reg)) return 0;
    return sim_register_value(state, is_address, reg, out_value);
  }
  if (access_kind == M68K_SIM_ACCESS_BRANCH_TARGET && operand->kind == M68K_ASM_OPERAND_LABEL) {
    *out_value = sim_value_section_ptr((uint8_t)section_index,
      offset + 2U + (uint32_t)((int32_t)operand->value.value), M68K_SIM_PROV_PC_REL);
    return 1;
  }
  if (access_kind == M68K_SIM_ACCESS_MEMORY_READ || access_kind == M68K_SIM_ACCESS_MEMORY_WRITE) {
    if (sim_direct_register_slot_by_metadata(metadata, operand_index, operand, &is_address, &reg)) {
      return sim_register_value(state, is_address, reg, out_value);
    }
    return sim_read_memory_value(object, section_index, section, instruction, offset, operand, state, memory_state, result,
      sim_effective_operand_width(instruction, metadata, operand_index), out_value);
  }
  if (access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS || access_kind == M68K_SIM_ACCESS_BRANCH_TARGET) {
    return sim_compute_ea_address(section, instruction, offset, operand,
      metadata->operand_ea_address_formulas[operand_index],
      metadata->operand_ea_address_shapes[operand_index], metadata->operand_ea_base_kinds[operand_index],
      metadata->operand_ea_displacement_sources[operand_index],
      metadata->operand_ea_uses_displacement[operand_index], metadata->operand_ea_uses_index[operand_index],
      metadata->operand_ea_pc_base_bias_bytes[operand_index],
      metadata->operand_ea_address_literal_width_bytes[operand_index],
      metadata->operand_ea_index_extension_formats[operand_index],
      metadata->operand_ea_index_register_classes[operand_index],
      metadata->operand_ea_index_value_width_sources[operand_index],
      metadata->operand_ea_index_scale_sources[operand_index],
      metadata->operand_ea_index_sign_sources[operand_index],
      state, section_index, out_value);
  }
  return 0;
}

static int sim_apply_add_sub(uint8_t is_sub, const M68kSimValue *lhs, const M68kSimValue *rhs,
    M68kSimValue *out_value) {
  uint8_t provenance;
  if (lhs == NULL || rhs == NULL || out_value == NULL) return 0;
  if (lhs->kind == M68K_SIM_VALUE_SECTION_PTR && rhs->kind == M68K_SIM_VALUE_CONSTANT) {
    *out_value = sim_value_section_ptr(lhs->section_index,
      is_sub ? (uint32_t)((int32_t)lhs->value - (int32_t)rhs->value)
             : (uint32_t)((int32_t)lhs->value + (int32_t)rhs->value),
      M68K_SIM_PROV_ADDRESS_ARITH);
    return 1;
  }
  if (lhs->kind == M68K_SIM_VALUE_CONSTANT && rhs->kind == M68K_SIM_VALUE_CONSTANT) {
    provenance = sim_result_provenance(lhs->provenance, rhs->provenance, M68K_SIM_PROV_ADDRESS_ARITH);
    *out_value = sim_value_constant(is_sub ? lhs->value - rhs->value : lhs->value + rhs->value, provenance);
    return 1;
  }
  return 0;
}

static void sim_clobber_operand_by_metadata(const M68kSection *section, const M68kInstructionIR *instruction,
    uint32_t offset, size_t section_index, M68kSimStepResult *result, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, const M68kOperandIR *operand, M68kSimCpuState *state) {
  if (section == NULL || result == NULL || metadata == NULL || operand == NULL || state == NULL)
    return;
  sim_write_operand_by_metadata(section, instruction, offset, section_index, result, metadata, operand_index, operand, state,
    &g_m68k_sim_unknown_value);
}

static int sim_adjust_value_by_constant(const M68kSimValue *base, int32_t delta, M68kSimValue *out_value) {
  M68kSimValue amount;
  if (out_value == NULL) return 0;
  amount = sim_value_constant((uint32_t)(delta < 0 ? -delta : delta), M68K_SIM_PROV_ADDRESS_ARITH);
  return sim_apply_add_sub(delta < 0, base, &amount, out_value);
}

static uint32_t sim_pack_value(uint32_t source_value, uint16_t adjustment) {
  uint32_t adjusted = (uint32_t)(uint16_t)((source_value & 0xFFFFU) + adjustment);
  return (((adjusted >> 8) & 0x0FU) << 4) | (adjusted & 0x0FU);
}

static uint32_t sim_unpack_value(uint32_t source_value, uint16_t adjustment) {
  uint32_t unpacked = (((source_value >> 4) & 0x0FU) << 8) | (source_value & 0x0FU);
  return (uint32_t)(uint16_t)(unpacked + adjustment);
}

static int sim_bitfield_is_direct_data_register(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || out_reg == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_BF_EA) return 0;
  if (operand->value.ea_mode != 0U || operand->value.ea_reg >= 8U) return 0;
  *out_reg = operand->value.ea_reg;
  return 1;
}

static int sim_bitfield_resolve_spec_abstract(const M68kAsmOperandValue *operand_value, const M68kSimCpuState *state,
    uint32_t *out_offset, uint32_t *out_width) {
  M68kSimValue reg_value;
  uint32_t offset;
  uint32_t width;
  if (operand_value == NULL || state == NULL || out_offset == NULL || out_width == NULL) return 0;
  if (operand_value->bf_offset_is_register) {
    if (operand_value->bf_offset >= 8U ||
        !sim_register_value(state, 0U, operand_value->bf_offset, &reg_value) ||
        reg_value.kind != M68K_SIM_VALUE_CONSTANT) return 0;
    offset = reg_value.value & 31U;
  } else {
    offset = operand_value->bf_offset & 31U;
  }
  if (operand_value->bf_width_is_register) {
    if (operand_value->bf_width >= 8U ||
        !sim_register_value(state, 0U, operand_value->bf_width, &reg_value) ||
        reg_value.kind != M68K_SIM_VALUE_CONSTANT) return 0;
    width = reg_value.value & 31U;
  } else {
    width = operand_value->bf_width & 31U;
  }
  if (width == 0U) width = 32U;
  *out_offset = offset;
  *out_width = width;
  return 1;
}

static int sim_bitfield_resolve_spec_concrete(const M68kAsmOperandValue *operand_value,
    const M68kSimConcreteState *state, uint32_t *out_offset, uint32_t *out_width) {
  uint32_t offset;
  uint32_t width;
  if (operand_value == NULL || state == NULL || out_offset == NULL || out_width == NULL) return 0;
  offset = operand_value->bf_offset_is_register && operand_value->bf_offset < 8U
    ? (state->d[operand_value->bf_offset] & 31U)
    : (operand_value->bf_offset & 31U);
  width = operand_value->bf_width_is_register && operand_value->bf_width < 8U
    ? (state->d[operand_value->bf_width] & 31U)
    : (operand_value->bf_width & 31U);
  if (width == 0U) width = 32U;
  *out_offset = offset;
  *out_width = width;
  return 1;
}

static uint32_t sim_bitfield_extract_from_register(uint32_t source, uint32_t offset, uint32_t width) {
  uint32_t index;
  uint32_t result = 0U;
  for (index = 0U; index < width; ++index) {
    uint32_t bit_index = (offset + index) % 32U;
    uint32_t bit = (source >> (31U - bit_index)) & 1U;
    result = (result << 1U) | bit;
  }
  return result;
}

static uint32_t sim_bitfield_insert_into_register(uint32_t original, uint32_t offset, uint32_t width,
    uint32_t field_value) {
  uint32_t index;
  uint32_t result = original;
  for (index = 0U; index < width; ++index) {
    uint32_t bit_index = (offset + index) % 32U;
    uint32_t bit = (field_value >> (width - 1U - index)) & 1U;
    uint32_t mask = 1U << (31U - bit_index);
    if (bit != 0U) result |= mask;
    else result &= ~mask;
  }
  return result;
}

static uint32_t sim_bitfield_find_first_one(uint32_t field_value, uint32_t width) {
  uint32_t index;
  for (index = 0U; index < width; ++index) {
    if (((field_value >> (width - 1U - index)) & 1U) != 0U) return index;
  }
  return width;
}

static uint32_t sim_bitfield_mask(uint32_t width) {
  return width >= 32U ? 0xFFFFFFFFU : ((1U << width) - 1U);
}

static uint8_t sim_bitfield_memory_byte_count(uint32_t offset, uint32_t width) {
  return (uint8_t)((((offset & 7U) + width) + 7U) / 8U);
}

static int sim_update_sr_nzvc(uint16_t sr, uint8_t n, uint8_t z, uint8_t v, uint8_t c, uint16_t *out_sr) {
  uint16_t next_sr;
  if (out_sr == NULL) return 0;
  next_sr = (uint16_t)(sr & ~((1U << g_m68k_sim_ccr_bit_n) | (1U << g_m68k_sim_ccr_bit_z) |
      (1U << g_m68k_sim_ccr_bit_v) | (1U << g_m68k_sim_ccr_bit_c)));
  if (n) next_sr = (uint16_t)(next_sr | (1U << g_m68k_sim_ccr_bit_n));
  if (z) next_sr = (uint16_t)(next_sr | (1U << g_m68k_sim_ccr_bit_z));
  if (v) next_sr = (uint16_t)(next_sr | (1U << g_m68k_sim_ccr_bit_v));
  if (c) next_sr = (uint16_t)(next_sr | (1U << g_m68k_sim_ccr_bit_c));
  *out_sr = next_sr;
  return 1;
}

static void sim_apply_abstract_bitfield_flags(M68kSimStepResult *result, uint16_t sr, uint32_t field_value,
    uint32_t width) {
  uint8_t n = 0U;
  uint8_t z;
  uint16_t next_sr;
  if (result == NULL || width == 0U) return;
  z = (field_value & sim_bitfield_mask(width)) == 0U ? 1U : 0U;
  if (((field_value >> (width - 1U)) & 1U) != 0U) n = 1U;
  sim_update_sr_nzvc(sr, n, z, 0U, 0U, &next_sr);
  result->next_state.sr = next_sr;
}

static int sim_apply_bitfield_nz_flags(uint16_t sr, uint32_t field_value, uint32_t width, uint16_t *out_sr) {
  uint8_t n = 0U;
  uint8_t z;
  if (out_sr == NULL || width == 0U) return 0;
  z = (field_value & sim_bitfield_mask(width)) == 0U ? 1U : 0U;
  if (((field_value >> (width - 1U)) & 1U) != 0U) n = 1U;
  return sim_update_sr_nzvc(sr, n, z, 0U, 0U, out_sr);
}

static int sim_apply_abstract_compare_test_flags(uint16_t sr, uint32_t lhs, uint32_t rhs, uint8_t width,
    uint8_t is_compare, uint16_t *out_sr) {
  uint32_t mask, result, lhs_masked, rhs_masked, sign_bit;
  uint8_t n, z;
  uint8_t v = 0U;
  uint8_t c = 0U;
  if (out_sr == NULL || width == 0U) return 0;
  mask = sim_mask_for_width(width);
  lhs_masked = lhs & mask;
  rhs_masked = rhs & mask;
  sign_bit = (uint32_t)1U << ((uint32_t)width * 8U - 1U);
  if (is_compare) {
    result = (rhs_masked - lhs_masked) & mask;
    c = rhs_masked < lhs_masked ? 1U : 0U;
    v = (((rhs_masked ^ lhs_masked) & (rhs_masked ^ result) & sign_bit) != 0U) ? 1U : 0U;
  } else {
    result = lhs_masked;
  }
  n = (result & sign_bit) != 0U ? 1U : 0U;
  z = result == 0U ? 1U : 0U;
  return sim_update_sr_nzvc(sr, n, z, v, c, out_sr);
}

static int sim_apply_abstract_add_sub_flags(uint16_t sr, uint32_t lhs, uint32_t rhs, uint8_t width, uint8_t is_sub,
    uint16_t *out_sr) {
  uint32_t mask, result, lhs_masked, rhs_masked, sign_bit;
  uint8_t n, z, v, c;
  if (out_sr == NULL || width == 0U) return 0;
  mask = sim_mask_for_width(width);
  lhs_masked = lhs & mask;
  rhs_masked = rhs & mask;
  result = is_sub ? (lhs_masked - rhs_masked) & mask : (lhs_masked + rhs_masked) & mask;
  sign_bit = (uint32_t)1U << ((uint32_t)width * 8U - 1U);
  n = (result & sign_bit) != 0U ? 1U : 0U;
  z = result == 0U ? 1U : 0U;
  if (is_sub) {
    c = lhs_masked < rhs_masked ? 1U : 0U;
    v = (((lhs_masked ^ rhs_masked) & (lhs_masked ^ result) & sign_bit) != 0U) ? 1U : 0U;
  } else {
    c = result < lhs_masked ? 1U : 0U;
    v = ((~(lhs_masked ^ rhs_masked) & (lhs_masked ^ result) & sign_bit) != 0U) ? 1U : 0U;
  }
  if (!sim_update_sr_nzvc(sr, n, z, v, c, out_sr)) return 0;
  sim_sync_extend_with_carry(out_sr);
  return 1;
}

static int sim_apply_abstract_nz_flags(uint16_t sr, uint32_t value, uint8_t width, uint16_t *out_sr) {
  uint32_t masked_value;
  uint32_t sign_bit;
  uint8_t n;
  uint8_t z;
  if (out_sr == NULL || width == 0U) return 0;
  masked_value = value & sim_mask_for_width(width);
  sign_bit = (uint32_t)1U << ((uint32_t)width * 8U - 1U);
  n = (masked_value & sign_bit) != 0U ? 1U : 0U;
  z = masked_value == 0U ? 1U : 0U;
  return sim_update_sr_nzvc(sr, n, z, 0U, 0U, out_sr);
}

static void sim_mark_condition_codes_defined(M68kSimStepResult *result) {
  if (result == NULL) return;
  result->defines_condition_codes = 1;
  result->next_state.sr_known = 1U;
}

static int sim_move_updates_condition_codes(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata) {
  uint8_t is_address = 0U;
  uint8_t reg = 0U;
  if (metadata == NULL || metadata->dest_operand_index >= instruction->operand_count) return 0;
  if (sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index,
        &instruction->operands[metadata->dest_operand_index], &is_address, &reg) && is_address) {
    return 0;
  }
  return 1;
}

static int sim_operation_may_define_condition_codes(const M68kSimFormMetadata *metadata) {
  if (metadata == NULL) return 0;
  switch (metadata->operation_type) {
    case M68K_SIM_OP_MOVE:
    case M68K_SIM_OP_ADD:
    case M68K_SIM_OP_SUB:
    case M68K_SIM_OP_LOGIC_AND:
    case M68K_SIM_OP_LOGIC_OR:
    case M68K_SIM_OP_LOGIC_XOR:
    case M68K_SIM_OP_NEGATE:
    case M68K_SIM_OP_NOT:
    case M68K_SIM_OP_SIGN_EXTEND:
    case M68K_SIM_OP_SWAP_WORDS:
    case M68K_SIM_OP_SHIFT:
    case M68K_SIM_OP_ROTATE:
    case M68K_SIM_OP_ROTATE_EXTEND:
    case M68K_SIM_OP_COMPARE:
    case M68K_SIM_OP_TEST:
    case M68K_SIM_OP_MULTIPLY:
    case M68K_SIM_OP_DIVIDE:
    case M68K_SIM_OP_BOUNDS_CHECK:
    case M68K_SIM_OP_COMPARE_SWAP:
    case M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED:
    case M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED:
    case M68K_SIM_OP_BITFIELD_TEST:
    case M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE:
    case M68K_SIM_OP_BITFIELD_CHANGE:
    case M68K_SIM_OP_BITFIELD_CLEAR:
    case M68K_SIM_OP_BITFIELD_INSERT:
    case M68K_SIM_OP_BITFIELD_SET:
    case M68K_SIM_OP_TEST_AND_SET:
    case M68K_SIM_OP_BIT_TEST:
    case M68K_SIM_OP_BIT_SET:
    case M68K_SIM_OP_BIT_CLEAR:
    case M68K_SIM_OP_BIT_CHANGE:
    case M68K_SIM_OP_CLEAR:
      return 1;
    default:
      return 0;
  }
}

static void sim_invalidate_defined_condition_codes(M68kSimStepResult *result) {
  if (result == NULL) return;
  result->defines_condition_codes = 1;
  result->next_state.sr_known = 0U;
  result->next_state.sr = 0U;
}

static void sim_invalidate_call_condition_codes(M68kSimStepResult *result) {
  if (result == NULL) return;
  result->next_state.sr_known = 0U;
  result->next_state.sr = 0U;
}

static void sim_sync_extend_with_carry(uint16_t *sr) {
  if (sr == NULL) return;
  if ((*sr & (1U << g_m68k_sim_ccr_bit_c)) != 0U) *sr = (uint16_t)(*sr | 0x0010U);
  else *sr = (uint16_t)(*sr & ~0x0010U);
}

static int sim_apply_abstract_bit_test_flags(uint16_t sr, const M68kSimFormMetadata *metadata, uint8_t dest_operand_index,
    const M68kOperandIR *dest_operand, const M68kSimValue *source, const M68kSimValue *dest_value, uint16_t *out_sr) {
  uint32_t bit_index;
  uint32_t width;
  uint32_t bit_is_set;
  uint16_t next_sr;
  if (metadata == NULL || dest_operand == NULL || source == NULL || dest_value == NULL || out_sr == NULL) return 0;
  if (dest_value->kind != M68K_SIM_VALUE_CONSTANT) return 0;
  width = sim_bit_width_for_metadata_operand(metadata, dest_operand_index, dest_operand);
  if (!sim_bit_index_from_value(source, (uint8_t)width, &bit_index)) return 0;
  bit_is_set = (dest_value->value >> bit_index) & 1U;
  next_sr = (uint16_t)(sr & ~(1U << g_m68k_sim_ccr_bit_z));
  if (bit_is_set == 0U) next_sr = (uint16_t)(next_sr | (1U << g_m68k_sim_ccr_bit_z));
  *out_sr = next_sr;
  return 1;
}

static int sim_abstract_read_memory_bitfield(const M68kObject *object, size_t section_index, const M68kSection *section,
    const M68kSimMemoryState *memory_state, uint32_t base_address, uint32_t offset_bits, uint32_t width,
    M68kSimStepResult *result, uint32_t *out_value) {
  uint8_t byte_count;
  uint8_t byte_index;
  uint32_t start_address;
  uint32_t aggregate = 0U;
  uint32_t shift;
  M68kSimValue byte_value;
  if (section == NULL || out_value == NULL || width == 0U) return 0;
  start_address = base_address + (offset_bits / 8U);
  byte_count = sim_bitfield_memory_byte_count(offset_bits, width);
  if (start_address + byte_count > section->data_size) return 0;
  for (byte_index = 0U; byte_index < byte_count; ++byte_index) {
    if (!sim_read_same_section_memory_value_sized(object, section_index, section, memory_state,
          start_address + byte_index, 1U, &byte_value) || byte_value.kind != M68K_SIM_VALUE_CONSTANT) return 0;
    aggregate = (aggregate << 8U) | (byte_value.value & 0xFFU);
    if (result != NULL) sim_add_access(result, M68K_SIM_ACCESS_MEMORY_READ, 1U, section_index, start_address + byte_index);
  }
  shift = (uint32_t)byte_count * 8U - ((offset_bits & 7U) + width);
  *out_value = (aggregate >> shift) & sim_bitfield_mask(width);
  return 1;
}

static int sim_abstract_write_memory_bitfield(const M68kObject *object, size_t section_index, const M68kSection *section,
    const M68kSimMemoryState *memory_state, uint32_t base_address, uint32_t offset_bits, uint32_t width,
    uint32_t field_value, M68kSimStepResult *result) {
  uint8_t byte_count, byte_index;
  uint32_t start_address, shift;
  uint64_t aggregate = 0U;
  uint64_t mask;
  if (section == NULL || result == NULL || width == 0U) return 0;
  start_address = base_address + (offset_bits / 8U);
  byte_count = sim_bitfield_memory_byte_count(offset_bits, width);
  if (start_address + byte_count > section->data_size) return 0;
  for (byte_index = 0U; byte_index < byte_count; ++byte_index) {
    M68kSimValue byte_value;
    if (!sim_read_same_section_memory_value_sized(object, section_index, section, memory_state,
          start_address + byte_index, 1U, &byte_value) || byte_value.kind != M68K_SIM_VALUE_CONSTANT) return 0;
    aggregate = (aggregate << 8U) | (byte_value.value & 0xFFU);
  }
  shift = (uint32_t)byte_count * 8U - ((offset_bits & 7U) + width);
  mask = ((uint64_t)sim_bitfield_mask(width)) << shift;
  aggregate = (aggregate & ~mask) | ((((uint64_t)field_value) & sim_bitfield_mask(width)) << shift);
  for (byte_index = 0U; byte_index < byte_count; ++byte_index) {
    M68kSimValue byte_value;
    uint32_t bit_shift = 8U * (uint32_t)(byte_count - 1U - byte_index);
    byte_value = sim_value_constant((uint32_t)((aggregate >> bit_shift) & 0xFFU), M68K_SIM_PROV_MEMORY_LOAD);
    sim_add_memory_write(result, 1U, section_index, start_address + byte_index, &byte_value);
    sim_add_access(result, M68K_SIM_ACCESS_MEMORY_WRITE, 1U, section_index, start_address + byte_index);
    m68k_sim_target_set_add(&result->discovered_labels, start_address + byte_index);
  }
  return 1;
}

static int sim_concrete_read_memory_bitfield(const uint8_t *memory, size_t memory_size, uint32_t base_address,
    uint32_t offset_bits, uint32_t width, uint32_t *out_value) {
  uint8_t byte_count;
  uint8_t byte_index;
  uint32_t start_address;
  uint64_t aggregate = 0U;
  uint32_t shift;
  if (memory == NULL || out_value == NULL || width == 0U) return 0;
  start_address = base_address + (offset_bits / 8U);
  byte_count = sim_bitfield_memory_byte_count(offset_bits, width);
  if (start_address + byte_count > memory_size) return 0;
  for (byte_index = 0U; byte_index < byte_count; ++byte_index) {
    aggregate = (aggregate << 8U) | memory[start_address + byte_index];
  }
  shift = (uint32_t)byte_count * 8U - ((offset_bits & 7U) + width);
  *out_value = (uint32_t)((aggregate >> shift) & sim_bitfield_mask(width));
  return 1;
}

static int sim_concrete_write_memory_bitfield(uint8_t *memory, size_t memory_size, uint32_t base_address,
    uint32_t offset_bits, uint32_t width, uint32_t field_value) {
  uint8_t byte_count, byte_index;
  uint32_t start_address, shift;
  uint64_t aggregate = 0U;
  uint64_t mask;
  if (memory == NULL || width == 0U) return 0;
  start_address = base_address + (offset_bits / 8U);
  byte_count = sim_bitfield_memory_byte_count(offset_bits, width);
  if (start_address + byte_count > memory_size) return 0;
  for (byte_index = 0U; byte_index < byte_count; ++byte_index) {
    aggregate = (aggregate << 8U) | memory[start_address + byte_index];
  }
  shift = (uint32_t)byte_count * 8U - ((offset_bits & 7U) + width);
  mask = ((uint64_t)sim_bitfield_mask(width)) << shift;
  aggregate = (aggregate & ~mask) | ((((uint64_t)field_value) & sim_bitfield_mask(width)) << shift);
  for (byte_index = 0U; byte_index < byte_count; ++byte_index) {
    uint32_t byte_shift = 8U * (uint32_t)(byte_count - 1U - byte_index);
    memory[start_address + byte_index] = (uint8_t)((aggregate >> byte_shift) & 0xFFU);
  }
  return 1;
}

static int sim_apply_signed_multiply(uint32_t lhs, uint32_t rhs, uint32_t *out_value) {
  if (out_value == NULL) return 0;
  *out_value = (uint32_t)((int32_t)(int16_t)(lhs & 0xFFFFU) * (int32_t)(int16_t)(rhs & 0xFFFFU));
  return 1;
}

static int sim_apply_unsigned_multiply(uint32_t lhs, uint32_t rhs, uint32_t *out_value) {
  if (out_value == NULL) return 0;
  *out_value = (uint32_t)((lhs & 0xFFFFU) * (rhs & 0xFFFFU));
  return 1;
}

static int sim_apply_signed_divide_status(uint32_t dividend_raw, uint32_t divisor_raw, uint32_t *out_value,
    uint8_t *out_overflow) {
  int32_t dividend;
  int32_t divisor;
  int32_t quotient;
  int32_t remainder;
  if (out_value == NULL || out_overflow == NULL) return 0;
  *out_overflow = 0U;
  divisor = (int32_t)(int16_t)(divisor_raw & 0xFFFFU);
  if (divisor == 0) return 0;
  dividend = (int32_t)dividend_raw;
  quotient = dividend / divisor;
  if (quotient < -32768 || quotient > 32767) {
    *out_overflow = 1U;
    return 1;
  }
  remainder = dividend % divisor;
  *out_value = (((uint32_t)remainder & 0xFFFFU) << 16) | ((uint32_t)quotient & 0xFFFFU);
  return 1;
}

static int sim_apply_unsigned_divide_status(uint32_t dividend, uint32_t divisor_raw, uint32_t *out_value,
    uint8_t *out_overflow) {
  uint32_t divisor;
  uint32_t quotient;
  uint32_t remainder;
  if (out_value == NULL || out_overflow == NULL) return 0;
  *out_overflow = 0U;
  divisor = divisor_raw & 0xFFFFU;
  if (divisor == 0U) return 0;
  quotient = dividend / divisor;
  if (quotient > 0xFFFFU) {
    *out_overflow = 1U;
    return 1;
  }
  remainder = dividend % divisor;
  *out_value = ((remainder & 0xFFFFU) << 16) | (quotient & 0xFFFFU);
  return 1;
}

static uint32_t sim_normalize_numeric_value(uint32_t value, uint8_t width, uint8_t is_signed) {
  if (!is_signed) return value & sim_mask_for_width(width);
  if (width == 1U) return (uint32_t)(int32_t)(int8_t)(value & 0xFFU);
  if (width == 2U) return (uint32_t)(int32_t)(int16_t)(value & 0xFFFFU);
  return value;
}

static int sim_value_in_bounds(uint32_t candidate, uint32_t low, uint32_t high, uint8_t width, uint8_t is_signed) {
  if (is_signed) {
    int32_t signed_candidate = (int32_t)sim_normalize_numeric_value(candidate, width, 1U);
    int32_t signed_low = (int32_t)sim_normalize_numeric_value(low, width, 1U);
    int32_t signed_high = (int32_t)sim_normalize_numeric_value(high, width, 1U);
    return signed_candidate >= signed_low && signed_candidate <= signed_high;
  }
  uint32_t mask = sim_mask_for_width(width);
  candidate &= mask;
  low &= mask;
  high &= mask;
  return candidate >= low && candidate <= high;
}

static int sim_apply_predecrement_operand(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, const M68kOperandIR *operand, M68kSimCpuState *state, M68kSimValue *out_address) {
  uint8_t address_reg;
  uint8_t ea_shape;
  uint8_t width;
  M68kSimValue delta;
  if (metadata == NULL || operand == NULL || state == NULL || out_address == NULL ||
      operand_index >= 4U) return 0;
  if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_PREDECREMENT) return 0;
  ea_shape = sim_effective_ea_shape(metadata->operand_ea_address_shapes[operand_index], operand);
  if (!sim_ea_address_register(ea_shape, operand, &address_reg)) return 0;
  width = sim_effective_operand_width(instruction, metadata, operand_index);
  delta = sim_value_constant(width == 0U ? 0U : width, M68K_SIM_PROV_ADDRESS_ARITH);
  if (!sim_apply_add_sub(1U, &state->a[address_reg], &delta, out_address)) return 0;
  state->a[address_reg] = *out_address;
  return 1;
}

static int sim_concrete_apply_predecrement_operand(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, uint8_t operand_index, const M68kOperandIR *operand,
    M68kSimConcreteState *state, uint32_t *out_address) {
  uint8_t address_reg;
  uint8_t ea_shape;
  uint8_t width;
  uint32_t delta;
  if (metadata == NULL || operand == NULL || state == NULL || out_address == NULL ||
      operand_index >= 4U) return 0;
  if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_PREDECREMENT) return 0;
  ea_shape = sim_effective_ea_shape(metadata->operand_ea_address_shapes[operand_index], operand);
  if (!sim_ea_address_register(ea_shape, operand, &address_reg)) return 0;
  width = sim_effective_operand_width(instruction, metadata, operand_index);
  delta = width == 0U ? 0U : width;
  state->a[address_reg] -= delta;
  *out_address = state->a[address_reg];
  return 1;
}

static int sim_operand_is_immediate_value(const M68kOperandIR *operand, uint32_t *out_value) {
  if (operand == NULL || out_value == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_IMM) {
    *out_value = operand->value.value;
    return 1;
  }
  if (sim_operand_is_immediate_ea(operand)) {
    *out_value = operand->value.value;
    return 1;
  }
  return 0;
}

static int sim_link_displacement(const M68kInstructionIR *instruction, const M68kSimValue *value, int32_t *out_delta) {
  if (value == NULL || out_delta == NULL || value->kind != M68K_SIM_VALUE_CONSTANT) return 0;
  if (instruction->byte_count <= 4U) *out_delta = (int32_t)(int16_t)(value->value & 0xFFFFU);
  else *out_delta = (int32_t)value->value;
  return 1;
}

static int sim_link_displacement_concrete(const M68kInstructionIR *instruction, uint32_t raw_value, int32_t *out_delta) {
  if (out_delta == NULL) return 0;
  if (instruction->byte_count <= 4U) *out_delta = (int32_t)(int16_t)(raw_value & 0xFFFFU);
  else *out_delta = (int32_t)raw_value;
  return 1;
}

static uint8_t sim_bit_width_for_metadata_operand(const M68kSimFormMetadata *metadata, uint8_t operand_index,
    const M68kOperandIR *operand) {
  uint8_t is_address;
  uint8_t reg;
  if (metadata == NULL || operand == NULL || operand_index >= 4U) return 1U;
  if (metadata->operand_expected_kinds[operand_index] == M68K_SIM_EXPECT_DN ||
      metadata->operand_expected_kinds[operand_index] == M68K_SIM_EXPECT_AN ||
      metadata->operand_expected_kinds[operand_index] == M68K_SIM_EXPECT_RN) {
    return 4U;
  }
  if (sim_direct_register_slot_by_metadata(metadata, operand_index, operand, &is_address, &reg)) return 4U;
  return 1U;
}

static int sim_bit_index_from_value(const M68kSimValue *value, uint8_t width, uint32_t *out_bit) {
  uint32_t modulus;
  if (value == NULL || out_bit == NULL || value->kind != M68K_SIM_VALUE_CONSTANT) return 0;
  modulus = width >= 4U ? 32U : 8U;
  *out_bit = value->value % modulus;
  return 1;
}

static int sim_apply_bit_op(uint8_t operation_type, const M68kSimFormMetadata *metadata, uint8_t dest_operand_index,
    const M68kSimValue *source, const M68kOperandIR *dest_operand, const M68kSimValue *dest_value,
    M68kSimValue *out_value) {
  uint32_t bit_index;
  uint32_t width;
  uint32_t mask;
  if (metadata == NULL || source == NULL || dest_operand == NULL || dest_value == NULL || out_value == NULL) return 0;
  if (dest_value->kind != M68K_SIM_VALUE_CONSTANT) return 0;
  width = sim_bit_width_for_metadata_operand(metadata, dest_operand_index, dest_operand);
  if (!sim_bit_index_from_value(source, (uint8_t)width, &bit_index)) return 0;
  mask = 1U << bit_index;
  *out_value = *dest_value;
  if (operation_type == M68K_SIM_OP_BIT_TEST) return 1;
  if (operation_type == M68K_SIM_OP_BIT_SET) {
    out_value->value = dest_value->value | mask;
    return 1;
  }
  if (operation_type == M68K_SIM_OP_BIT_CLEAR) {
    out_value->value = dest_value->value & ~mask;
    return 1;
  }
  if (operation_type == M68K_SIM_OP_BIT_CHANGE) {
    out_value->value = dest_value->value ^ mask;
    return 1;
  }
  return 0;
}

static int sim_reglist_slot(uint8_t slot, uint8_t *is_address, uint8_t *reg) {
  if (is_address == NULL || reg == NULL || slot >= 16U) return 0;
  *is_address = slot >= 8U;
  *reg = *is_address ? (uint8_t)(slot - 8U) : slot;
  return 1;
}

static void sim_write_register_slot(M68kSimCpuState *state, uint8_t is_address, uint8_t reg,
    const M68kSimValue *value) {
  if (state == NULL || value == NULL || reg >= 8U) return;
  if (is_address) state->a[reg] = *value;
  else state->d[reg] = *value;
}

static uint8_t sim_reglist_count(uint16_t mask) {
  uint8_t count = 0U;
  while (mask != 0U) {
    count = (uint8_t)(count + (uint8_t)(mask & 1U));
    mask >>= 1U;
  }
  return count;
}

static uint8_t sim_effective_ea_shape(uint8_t ea_shape, const M68kOperandIR *operand) {
  if (ea_shape != M68K_SIM_EA_SHAPE_NONE) return ea_shape;
  return sim_infer_ea_shape(operand);
}

static int sim_multi_transfer_uses_predecrement(uint8_t address_update, uint8_t register_update,
    uint8_t ea_shape) {
  if (register_update == M68K_SIM_EA_UPDATE_PREDECREMENT) return 1;
  if (address_update != M68K_SIM_MULTI_UPDATE_PREDECREMENT_IF_PREDEC) return 0;
  return ea_shape == M68K_SIM_EA_SHAPE_PREDECREMENT;
}

static int sim_multi_transfer_uses_postincrement(uint8_t address_update, uint8_t register_update,
    uint8_t ea_shape) {
  if (register_update == M68K_SIM_EA_UPDATE_POSTINCREMENT) return 1;
  if (address_update != M68K_SIM_MULTI_UPDATE_POSTINCREMENT_IF_POSTINC) return 0;
  return ea_shape == M68K_SIM_EA_SHAPE_POSTINCREMENT;
}

static int sim_apply_concrete_ea_register_update(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, uint8_t operand_index, const M68kOperandIR *operand,
    M68kSimConcreteState *state) {
  uint8_t address_reg;
  uint8_t ea_shape;
  uint8_t width;
  uint32_t delta;
  if (metadata == NULL || operand == NULL || state == NULL || operand_index >= 4U) return 0;
  if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_POSTINCREMENT) return 1;
  ea_shape = sim_effective_ea_shape(metadata->operand_ea_address_shapes[operand_index], operand);
  if (!sim_ea_address_register(ea_shape, operand, &address_reg)) return 0;
  width = sim_effective_operand_width(instruction, metadata, operand_index);
  delta = width == 0U ? 0U : width;
  if (delta == 1U && address_reg == 7U) delta = 2U;
  state->a[address_reg] += delta;
  return 1;
}

static int sim_multi_transfer_includes_slot(uint8_t reg_iteration, uint16_t mask, uint8_t slot) {
  if (slot >= 16U) return 0;
  if (reg_iteration == M68K_SIM_MULTI_REG_ITERATION_ASCENDING_MASK_BITS) return (mask & (1u << slot)) != 0u;
  return 0;
}

static int sim_ea_address_register(uint8_t ea_shape, const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || out_reg == NULL) return 0;
  ea_shape = sim_effective_ea_shape(ea_shape, operand);
  if (ea_shape == M68K_SIM_EA_SHAPE_INDIRECT || ea_shape == M68K_SIM_EA_SHAPE_POSTINCREMENT ||
      ea_shape == M68K_SIM_EA_SHAPE_PREDECREMENT || ea_shape == M68K_SIM_EA_SHAPE_DISPLACEMENT ||
      ea_shape == M68K_SIM_EA_SHAPE_INDEX) {
    if (operand->kind == M68K_ASM_OPERAND_POSTINC) {
      *out_reg = operand->value.reg;
      return 1;
    }
    *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static int sim_ea_base_address_value(const M68kSimCpuState *state, const M68kOperandIR *operand, M68kSimValue *out_value) {
  uint8_t reg;
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  if (!sim_ea_address_register(M68K_SIM_EA_SHAPE_NONE, operand, &reg)) return 0;
  return sim_register_value(state, 1U, reg, out_value);
}

static int sim_ea_index_value(const M68kSimCpuState *state, const M68kOperandIR *operand, M68kSimValue *out_value) {
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  return sim_register_value(state, operand->value.index_is_address, operand->value.index_reg, out_value);
}

static int sim_ea_index_value_by_metadata(const M68kSimCpuState *state, const M68kOperandIR *operand,
    uint8_t index_extension_format, uint8_t index_register_class, uint8_t index_value_width_source,
    uint8_t index_scale_source, uint8_t index_sign_source, M68kSimValue *out_value) {
  M68kSimValue raw_value;
  uint32_t normalized;
  uint32_t scale;
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  if (index_extension_format != M68K_SIM_EA_INDEX_EXT_BRIEF ||
      index_register_class != M68K_SIM_EA_INDEX_REG_DATA_OR_ADDRESS) {
    return sim_ea_index_value(state, operand, out_value);
  }
  if (!sim_ea_index_value(state, operand, &raw_value) || raw_value.kind != M68K_SIM_VALUE_CONSTANT) return 0;
  normalized = raw_value.value;
  if (index_value_width_source == M68K_SIM_EA_INDEX_WIDTH_EXTENSION_WORD) normalized &= 0xFFFFU;
  if (index_sign_source == M68K_SIM_EA_INDEX_SIGN_EXTENSION_WORD) normalized = sim_sign_extend_value(normalized, 16U);
  if (index_scale_source == M68K_SIM_EA_INDEX_SCALE_EXTENSION_WORD) {
    scale = operand->value.scale == 0U ? 1U : operand->value.scale;
    normalized = (uint32_t)((int32_t)normalized * (int32_t)scale);
  }
  *out_value = sim_value_constant(normalized, raw_value.provenance);
  return 1;
}

static uint32_t sim_ea_index_scale(const M68kOperandIR *operand) {
  if (operand == NULL || operand->value.scale == 0U) return 1U;
  return operand->value.scale;
}

static int sim_direct_register_slot_by_metadata(const M68kSimFormMetadata *metadata, uint8_t operand_index,
    const M68kOperandIR *operand, uint8_t *out_is_address, uint8_t *out_reg) {
  uint8_t expected_kind;
  if (metadata == NULL || operand == NULL || out_is_address == NULL || out_reg == NULL || operand_index >= 4U) return 0;
  expected_kind = metadata->operand_expected_kinds[operand_index];
  if (expected_kind == M68K_SIM_EXPECT_DN) return sim_register_is_direct(operand, out_is_address, out_reg) && !*out_is_address;
  if (expected_kind == M68K_SIM_EXPECT_AN) return sim_register_is_direct(operand, out_is_address, out_reg) && *out_is_address;
  if (expected_kind == M68K_SIM_EXPECT_RN || expected_kind == M68K_SIM_EXPECT_EA) {
    return sim_register_is_direct(operand, out_is_address, out_reg);
  }
  return 0;
}

static int sim_concrete_ea_base_address_value(const M68kSimConcreteState *state, const M68kOperandIR *operand,
    uint32_t *out_value) {
  uint8_t reg;
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  if (!sim_ea_address_register(M68K_SIM_EA_SHAPE_NONE, operand, &reg)) return 0;
  *out_value = state->a[reg];
  return 1;
}

static int sim_concrete_ea_index_value(const M68kSimConcreteState *state, const M68kOperandIR *operand,
    uint32_t *out_value) {
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  *out_value = operand->value.index_is_address ? state->a[operand->value.index_reg] : state->d[operand->value.index_reg];
  return 1;
}

static int sim_concrete_ea_index_value_by_metadata(const M68kSimConcreteState *state, const M68kOperandIR *operand,
    uint8_t index_extension_format, uint8_t index_register_class, uint8_t index_value_width_source,
    uint8_t index_scale_source, uint8_t index_sign_source, uint32_t *out_value) {
  uint32_t normalized;
  uint32_t scale;
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  if (index_extension_format != M68K_SIM_EA_INDEX_EXT_BRIEF ||
      index_register_class != M68K_SIM_EA_INDEX_REG_DATA_OR_ADDRESS) {
    return sim_concrete_ea_index_value(state, operand, out_value);
  }
  if (!sim_concrete_ea_index_value(state, operand, &normalized)) return 0;
  if (index_value_width_source == M68K_SIM_EA_INDEX_WIDTH_EXTENSION_WORD) normalized &= 0xFFFFU;
  if (index_sign_source == M68K_SIM_EA_INDEX_SIGN_EXTENSION_WORD) normalized = sim_sign_extend_value(normalized, 16U);
  if (index_scale_source == M68K_SIM_EA_INDEX_SCALE_EXTENSION_WORD) {
    scale = operand->value.scale == 0U ? 1U : operand->value.scale;
    normalized = (uint32_t)((int32_t)normalized * (int32_t)scale);
  }
  *out_value = normalized;
  return 1;
}

static const M68kSimConcreteState *sim_multi_transfer_source_state(uint8_t source_snapshot,
    const M68kSimConcreteState *live_state, const M68kSimConcreteState *snapshot_state) {
  if (source_snapshot == M68K_SIM_MULTI_SNAPSHOT_BEFORE_WRITE && snapshot_state != NULL) return snapshot_state;
  return live_state;
}

static uint32_t sim_striped_transfer_byte_address(uint32_t base, uint8_t stride, uint8_t byte_index) {
  return base + (uint32_t)stride * (uint32_t)byte_index;
}

static int sim_read_same_section_memory_value_sized(const M68kObject *object, size_t section_index, const M68kSection *section,
    const M68kSimMemoryState *memory_state, uint32_t address, uint8_t width, M68kSimValue *out_value) {
  size_t index;
  if (section == NULL || out_value == NULL || width == 0U || address + width > section->data_size) return 0;
  if (memory_state != NULL) {
    for (index = 0; index < memory_state->cell_count; ++index) {
      const M68kSimMemoryCell *cell = &memory_state->cells[index];
      if (cell->section_index == (uint8_t)section_index && cell->offset == address && cell->width == width) {
        *out_value = cell->value;
        return 1;
      }
    }
  }
  if (width == 4U) return sim_read_same_section_memory_value(object, section_index, section, memory_state, address, out_value);
  if (width == 2U) {
    *out_value = sim_value_constant((uint32_t)m68k_read_u16be(section->data + address), M68K_SIM_PROV_MEMORY_LOAD);
    return 1;
  }
  *out_value = sim_value_constant((uint32_t)section->data[address], M68K_SIM_PROV_MEMORY_LOAD);
  return 1;
}

static int sim_condition_true(uint8_t condition_code, uint16_t sr) {
  uint8_t state;
  if (condition_code >= 16U) return 1;
  state = (uint8_t)((((sr >> g_m68k_sim_ccr_bit_n) & 1U) << 3) |
                    (((sr >> g_m68k_sim_ccr_bit_z) & 1U) << 2) |
                    (((sr >> g_m68k_sim_ccr_bit_v) & 1U) << 1) |
                    ((sr >> g_m68k_sim_ccr_bit_c) & 1U));
  return ((g_m68k_sim_condition_masks[condition_code] >> state) & 1U) != 0U;
}

static int sim_concrete_read_register(const M68kSimConcreteState *state, uint8_t is_address, uint8_t reg,
    uint32_t *out_value) {
  if (state == NULL || out_value == NULL || reg >= 8U) return 0;
  *out_value = is_address ? state->a[reg] : state->d[reg];
  return 1;
}

static void sim_concrete_write_register_slot(M68kSimConcreteState *state, uint8_t is_address, uint8_t reg,
    uint32_t value) {
  if (state == NULL || reg >= 8U) return;
  if (is_address) state->a[reg] = value;
  else state->d[reg] = value;
}

static int sim_concrete_read_control_register(const M68kSimConcreteState *state, uint8_t reg, uint32_t *out_value) {
  if (state == NULL || out_value == NULL || reg >= M68K_SIM_CONTROL_REGISTER_LIMIT) return 0;
  *out_value = state->c[reg];
  return 1;
}

static int sim_concrete_read_special_register(const M68kSimConcreteState *state, const M68kOperandIR *operand,
    uint32_t *out_value) {
  uint8_t ctrl_reg;
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_CCR) {
    *out_value = state->sr & 0x00FFU;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_SR) {
    *out_value = state->sr;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_USP && sim_usp_control_register_index(&ctrl_reg)) {
    return sim_concrete_read_control_register(state, ctrl_reg, out_value);
  }
  if (sim_control_register_index(operand, &ctrl_reg)) return sim_concrete_read_control_register(state, ctrl_reg, out_value);
  return 0;
}

static int sim_concrete_write_register(M68kSimConcreteState *state, const M68kOperandIR *operand, uint32_t value) {
  uint8_t is_address;
  uint8_t reg;
  uint8_t ctrl_reg;
  if (state == NULL || operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_CCR) {
    state->sr = (uint16_t)((state->sr & 0xFF00U) | (value & 0x00FFU));
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_SR) {
    state->sr = (uint16_t)(value & 0xFFFFU);
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_USP && sim_usp_control_register_index(&ctrl_reg)) {
    state->c[ctrl_reg] = value;
    return 1;
  }
  if (sim_control_register_index(operand, &ctrl_reg)) {
    state->c[ctrl_reg] = value;
    return 1;
  }
  if (!sim_register_is_direct(operand, &is_address, &reg)) return 0;
  if (is_address) state->a[reg] = value;
  else state->d[reg] = value;
  return 1;
}

static int sim_concrete_write_register_sized(M68kSimConcreteState *state, const M68kOperandIR *operand,
    uint32_t value, uint8_t width) {
  uint8_t is_address;
  uint8_t reg;
  uint8_t ctrl_reg;
  uint32_t *slot;
  uint32_t mask;
  if (state == NULL || operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_CCR) {
    state->sr = (uint16_t)((state->sr & 0xFF00U) | (value & 0x00FFU));
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_SR) {
    state->sr = (uint16_t)(value & 0xFFFFU);
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_USP && sim_usp_control_register_index(&ctrl_reg)) {
    state->c[ctrl_reg] = value;
    return 1;
  }
  if (sim_control_register_index(operand, &ctrl_reg)) {
    state->c[ctrl_reg] = value;
    return 1;
  }
  if (!sim_register_is_direct(operand, &is_address, &reg)) return 0;
  slot = is_address ? &state->a[reg] : &state->d[reg];
  if (width >= 4U || is_address) {
    *slot = value;
    return 1;
  }
  mask = width == 1U ? 0xFFU : 0xFFFFU;
  *slot = (*slot & ~mask) | (value & mask);
  return 1;
}

static int sim_concrete_write_memory_sized(uint8_t *memory, size_t memory_size, uint32_t address,
    uint32_t value, uint8_t width) {
  if (memory == NULL || width == 0U || address + width > memory_size) return 0;
  if (width == 1U) {
    memory[address] = (uint8_t)(value & 0xFFU);
    return 1;
  }
  if (width == 2U) {
    memory[address] = (uint8_t)((value >> 8) & 0xFFU);
    memory[address + 1U] = (uint8_t)(value & 0xFFU);
    return 1;
  }
  if (width == 4U) {
    memory[address] = (uint8_t)((value >> 24) & 0xFFU);
    memory[address + 1U] = (uint8_t)((value >> 16) & 0xFFU);
    memory[address + 2U] = (uint8_t)((value >> 8) & 0xFFU);
    memory[address + 3U] = (uint8_t)(value & 0xFFU);
    return 1;
  }
  return 0;
}

static int sim_concrete_write_operand_by_metadata(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, uint8_t operand_index, const M68kOperandIR *operand,
    M68kSimConcreteState *state, uint8_t *memory, size_t memory_size, uint32_t instruction_pc, uint32_t value) {
  uint8_t access_kind;
  uint8_t width;
  uint32_t address;
  if (metadata == NULL || operand == NULL || state == NULL || operand_index >= 4U) return 0;
  access_kind = metadata->operand_access_kinds[operand_index];
  width = sim_effective_operand_width(instruction, metadata, operand_index);
  if (access_kind == M68K_SIM_ACCESS_REGISTER_WRITE) return sim_concrete_write_register_sized(state, operand, value, width);
  if (access_kind == M68K_SIM_ACCESS_MEMORY_WRITE) {
    if (sim_expected_kind_prefers_register_write(metadata->operand_expected_kinds[operand_index], operand)) {
      return sim_concrete_write_register_sized(state, operand, value, width);
    }
    if (sim_concrete_compute_ea_address(operand, metadata->operand_ea_address_formulas[operand_index],
          metadata->operand_ea_address_shapes[operand_index], metadata->operand_ea_base_kinds[operand_index],
          metadata->operand_ea_displacement_sources[operand_index],
          metadata->operand_ea_uses_displacement[operand_index], metadata->operand_ea_uses_index[operand_index],
          metadata->operand_ea_pc_base_bias_bytes[operand_index],
          metadata->operand_ea_address_literal_width_bytes[operand_index],
          metadata->operand_ea_index_extension_formats[operand_index],
          metadata->operand_ea_index_register_classes[operand_index],
          metadata->operand_ea_index_value_width_sources[operand_index],
          metadata->operand_ea_index_scale_sources[operand_index],
          metadata->operand_ea_index_sign_sources[operand_index],
          state, instruction_pc, &address)) {
      return sim_concrete_write_memory_sized(memory, memory_size, address, value, width);
    }
  }
  return 0;
}

static int sim_concrete_compute_ea_address(const M68kOperandIR *operand, uint8_t ea_formula, uint8_t ea_shape,
    uint8_t ea_base_kind, uint8_t displacement_source, uint8_t uses_displacement,
    uint8_t uses_index, uint8_t pc_base_bias_bytes, uint8_t address_literal_width_bytes,
    uint8_t index_extension_format, uint8_t index_register_class, uint8_t index_value_width_source,
    uint8_t index_scale_source, uint8_t index_sign_source,
    const M68kSimConcreteState *state, uint32_t instruction_pc, uint32_t *out_address) {
  uint32_t base;
  uint32_t index_value;
  if (operand == NULL || state == NULL || out_address == NULL) return 0;
  (void)uses_index;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA &&
      operand->kind != M68K_ASM_OPERAND_IND &&
      operand->kind != M68K_ASM_OPERAND_POSTINC && operand->kind != M68K_ASM_OPERAND_ABSL) {
    return 0;
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_AN && ea_base_kind == M68K_SIM_EA_BASE_AN) {
    return sim_concrete_ea_base_address_value(state, operand, out_address);
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_AN_PLUS_DISP) {
    if (ea_base_kind == M68K_SIM_EA_BASE_AN && displacement_source == M68K_SIM_EA_DISP_OPERAND_VALUE &&
        uses_displacement) {
      if (!sim_concrete_ea_base_address_value(state, operand, &base)) return 0;
      *out_address = (uint32_t)((int32_t)base + (int32_t)operand->value.value);
      return 1;
    }
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_ABSOLUTE_LITERAL) {
    if (ea_base_kind == M68K_SIM_EA_BASE_ABSOLUTE && address_literal_width_bytes != 0U) {
      *out_address = operand->value.value;
      return 1;
    }
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_PC_PLUS_DISP) {
    uint8_t pc_bias;
    if (ea_base_kind == M68K_SIM_EA_BASE_PC && displacement_source == M68K_SIM_EA_DISP_OPERAND_VALUE &&
        uses_displacement) {
      pc_bias = pc_base_bias_bytes != 0U ? pc_base_bias_bytes : 2U;
      *out_address = (uint32_t)((int32_t)instruction_pc + (int32_t)pc_bias + (int32_t)operand->value.value);
      return 1;
    }
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_AN_PLUS_DISP_PLUS_INDEX) {
    if (ea_base_kind == M68K_SIM_EA_BASE_AN && displacement_source == M68K_SIM_EA_DISP_OPERAND_VALUE &&
        uses_displacement && uses_index &&
        sim_concrete_ea_base_address_value(state, operand, &base) &&
        sim_concrete_ea_index_value_by_metadata(state, operand, index_extension_format, index_register_class,
          index_value_width_source, index_scale_source, index_sign_source, &index_value)) {
      *out_address = (uint32_t)((int32_t)base + (int32_t)operand->value.value + (int32_t)index_value);
      return 1;
    }
  }
  if (ea_formula == M68K_SIM_EA_FORMULA_PC_PLUS_DISP_PLUS_INDEX) {
    uint8_t pc_bias;
    if (ea_base_kind == M68K_SIM_EA_BASE_PC && displacement_source == M68K_SIM_EA_DISP_OPERAND_VALUE &&
        uses_displacement && uses_index &&
        sim_concrete_ea_index_value_by_metadata(state, operand, index_extension_format, index_register_class,
          index_value_width_source, index_scale_source, index_sign_source, &index_value)) {
      pc_bias = pc_base_bias_bytes != 0U ? pc_base_bias_bytes : 2U;
      *out_address = (uint32_t)((int32_t)instruction_pc + (int32_t)pc_bias +
        (int32_t)operand->value.value + (int32_t)index_value);
      return 1;
    }
  }
  ea_shape = sim_effective_ea_shape(ea_shape, operand);
  if (ea_shape == M68K_SIM_EA_SHAPE_INDIRECT || ea_shape == M68K_SIM_EA_SHAPE_POSTINCREMENT ||
      ea_shape == M68K_SIM_EA_SHAPE_PREDECREMENT) {
    return sim_concrete_ea_base_address_value(state, operand, out_address);
  }
  if (ea_shape == M68K_SIM_EA_SHAPE_DISPLACEMENT) {
    if (!sim_concrete_ea_base_address_value(state, operand, &base)) return 0;
    *out_address = (uint32_t)((int32_t)base + (int32_t)operand->value.value);
    return 1;
  }
  if (ea_shape == M68K_SIM_EA_SHAPE_INDEX) {
    if (!sim_concrete_ea_base_address_value(state, operand, &base)) return 0;
    if (!sim_concrete_ea_index_value_by_metadata(state, operand, index_extension_format, index_register_class,
          index_value_width_source, index_scale_source, index_sign_source, &index_value)) {
      if (!sim_concrete_ea_index_value(state, operand, &index_value)) return 0;
      index_value = (uint32_t)((int32_t)index_value * (int32_t)sim_ea_index_scale(operand));
    }
    *out_address = (uint32_t)((int32_t)base + (int32_t)operand->value.value + (int32_t)index_value);
    return 1;
  }
  if (ea_shape == M68K_SIM_EA_SHAPE_ABSOLUTE_WORD || ea_shape == M68K_SIM_EA_SHAPE_ABSOLUTE_LONG) {
    *out_address = operand->value.value;
    return 1;
  }
  if (ea_shape == M68K_SIM_EA_SHAPE_PC_DISPLACEMENT) {
    uint8_t pc_bias = pc_base_bias_bytes != 0U ? pc_base_bias_bytes : 2U;
    *out_address = (uint32_t)((int32_t)instruction_pc + (int32_t)pc_bias + (int32_t)operand->value.value);
    return 1;
  }
  if (ea_shape == M68K_SIM_EA_SHAPE_PC_INDEX) {
    uint8_t pc_bias = pc_base_bias_bytes != 0U ? pc_base_bias_bytes : 2U;
    if (!sim_concrete_ea_index_value_by_metadata(state, operand, index_extension_format, index_register_class,
          index_value_width_source, index_scale_source, index_sign_source, &index_value)) {
      if (!sim_concrete_ea_index_value(state, operand, &index_value)) return 0;
      index_value = (uint32_t)((int32_t)index_value * (int32_t)sim_ea_index_scale(operand));
    }
    *out_address = (uint32_t)((int32_t)instruction_pc + (int32_t)pc_bias +
      (int32_t)operand->value.value + (int32_t)index_value);
    return 1;
  }
  return 0;
}

static int sim_concrete_read_memory_u32(const uint8_t *memory, size_t memory_size, uint32_t address,
    uint32_t *out_value) {
  if (memory == NULL || out_value == NULL || address + 4U > memory_size) return 0;
  *out_value = m68k_read_u32be(memory + address);
  return 1;
}

static int sim_concrete_read_memory_sized(const uint8_t *memory, size_t memory_size, uint32_t address,
    uint8_t width, uint32_t *out_value) {
  if (memory == NULL || out_value == NULL || width == 0U || address + width > memory_size) return 0;
  if (width == 1U) {
    *out_value = memory[address];
    return 1;
  }
  if (width == 2U) {
    *out_value = m68k_read_u16be(memory + address);
    return 1;
  }
  if (width == 4U) {
    *out_value = m68k_read_u32be(memory + address);
    return 1;
  }
  return 0;
}

static int sim_concrete_eval_value_operand(const M68kOperandIR *operand, const M68kSimConcreteState *state,
    const uint8_t *memory, size_t memory_size, uint32_t instruction_pc, uint32_t *out_value) {
  uint8_t is_address;
  uint8_t reg;
  uint32_t address;
  if (operand == NULL || state == NULL || out_value == NULL) return 0;
  if (sim_operand_is_immediate_value(operand, out_value)) return 1;
  if (sim_register_is_direct(operand, &is_address, &reg)) return sim_concrete_read_register(state, is_address, reg, out_value);
  if (!sim_concrete_compute_ea_address(operand, M68K_SIM_EA_FORMULA_NONE, M68K_SIM_EA_SHAPE_NONE,
        M68K_SIM_EA_BASE_NONE, M68K_SIM_EA_DISP_NONE, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U,
        state, instruction_pc, &address)) return 0;
  return sim_concrete_read_memory_u32(memory, memory_size, address, out_value);
}

static int sim_concrete_eval_value_operand_by_metadata(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, uint8_t operand_index,
    const M68kOperandIR *operand,
    const M68kSimConcreteState *state, const uint8_t *memory, size_t memory_size, uint32_t instruction_pc,
    uint32_t *out_value) {
  uint8_t access_kind;
  uint8_t width;
  if (metadata == NULL || operand == NULL || state == NULL || out_value == NULL || operand_index >= 4U) return 0;
  access_kind = metadata->operand_access_kinds[operand_index];
  width = sim_effective_operand_width(instruction, metadata, operand_index);
  if (access_kind == M68K_SIM_ACCESS_IMMEDIATE) return sim_operand_is_immediate_value(operand, out_value);
  if (access_kind == M68K_SIM_ACCESS_REGISTER_READ || access_kind == M68K_SIM_ACCESS_REGISTER_WRITE) {
    uint8_t is_address;
    uint8_t reg;
    if (sim_concrete_read_special_register(state, operand, out_value)) return 1;
    if (!sim_direct_register_slot_by_metadata(metadata, operand_index, operand, &is_address, &reg)) return 0;
    return sim_concrete_read_register(state, is_address, reg, out_value);
  }
  if (access_kind == M68K_SIM_ACCESS_BRANCH_TARGET && operand->kind == M68K_ASM_OPERAND_LABEL) {
    *out_value = instruction_pc + 2U + (uint32_t)((int32_t)operand->value.value);
    return 1;
  }
  if (access_kind == M68K_SIM_ACCESS_MEMORY_READ || access_kind == M68K_SIM_ACCESS_MEMORY_WRITE) {
    uint8_t is_address;
    uint8_t reg;
    uint32_t address;
    if (sim_direct_register_slot_by_metadata(metadata, operand_index, operand, &is_address, &reg)) {
      return sim_concrete_read_register(state, is_address, reg, out_value);
    }
    if (!sim_concrete_compute_ea_address(operand, metadata->operand_ea_address_formulas[operand_index],
          metadata->operand_ea_address_shapes[operand_index], metadata->operand_ea_base_kinds[operand_index],
          metadata->operand_ea_displacement_sources[operand_index],
          metadata->operand_ea_uses_displacement[operand_index], metadata->operand_ea_uses_index[operand_index],
          metadata->operand_ea_pc_base_bias_bytes[operand_index],
          metadata->operand_ea_address_literal_width_bytes[operand_index],
          metadata->operand_ea_index_extension_formats[operand_index],
          metadata->operand_ea_index_register_classes[operand_index],
          metadata->operand_ea_index_value_width_sources[operand_index],
          metadata->operand_ea_index_scale_sources[operand_index],
          metadata->operand_ea_index_sign_sources[operand_index],
          state, instruction_pc, &address)) {
      return sim_concrete_eval_value_operand(operand, state, memory, memory_size, instruction_pc, out_value);
    }
    return sim_concrete_read_memory_sized(memory, memory_size, address, width, out_value);
  }
  if (access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS || access_kind == M68K_SIM_ACCESS_BRANCH_TARGET) {
    return sim_concrete_compute_ea_address(operand, metadata->operand_ea_address_formulas[operand_index],
      metadata->operand_ea_address_shapes[operand_index], metadata->operand_ea_base_kinds[operand_index],
      metadata->operand_ea_displacement_sources[operand_index],
      metadata->operand_ea_uses_displacement[operand_index], metadata->operand_ea_uses_index[operand_index],
      metadata->operand_ea_pc_base_bias_bytes[operand_index],
      metadata->operand_ea_address_literal_width_bytes[operand_index],
      metadata->operand_ea_index_extension_formats[operand_index],
      metadata->operand_ea_index_register_classes[operand_index],
      metadata->operand_ea_index_value_width_sources[operand_index],
      metadata->operand_ea_index_scale_sources[operand_index],
      metadata->operand_ea_index_sign_sources[operand_index],
      state, instruction_pc, out_value);
  }
  return 0;
}

static int sim_concrete_eval_operand_by_metadata(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, uint8_t operand_index,
    const M68kOperandIR *operand,
    const M68kSimConcreteState *state, const uint8_t *memory, size_t memory_size, uint32_t instruction_pc,
    uint32_t *out_value) {
  if (metadata == NULL || operand == NULL || out_value == NULL || operand_index >= 4U) return 0;
  return sim_concrete_eval_value_operand_by_metadata(instruction, metadata, operand_index, operand, state, memory, memory_size,
    instruction_pc, out_value);
}

static int sim_metadata_has_accesses(const M68kSimFormMetadata *metadata) {
  uint8_t operand_index;
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < 4U; ++operand_index) {
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_NONE) return 1;
  }
  return 0;
}

static int sim_known_control_register_index(uint8_t control_register_id, uint8_t *out_index) {
  if (out_index == NULL || control_register_id >= M68K_SIM_CONTROL_REGISTER_LIMIT) return 0;
  if (m68k_asm_find_control_register_by_id(control_register_id) == NULL) return 0;
  *out_index = control_register_id;
  return 1;
}

static int sim_is_explicit_concrete_noop(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata) {
  if (metadata == NULL) return 0;
  return metadata->operation_type == M68K_SIM_OP_NONE &&
    metadata->flow_kind == M68K_SIM_FLOW_SEQUENTIAL &&
    !sim_metadata_has_accesses(metadata) &&
    instruction->mnemonic_id == M68K_ASM_MNEMONIC_NOP;
}

static void sim_set_unsupported_concrete_exception_error(M68kDiagSink diagnostics) {
  sim_diag_error(diagnostics, "unsupported concrete exception/trap");
}

static int sim_exception_frame_kind_for(uint8_t target_cpu, uint8_t vector, uint8_t *out_frame_kind) {
  size_t index;
  uint32_t cpu_mask;
  if (out_frame_kind == NULL || target_cpu > 31U) return 0;
  cpu_mask = 1u << target_cpu;
  for (index = 0; index < sizeof(g_m68k_sim_exception_frame_rules) / sizeof(g_m68k_sim_exception_frame_rules[0]); ++index) {
    const M68kSimExceptionFrameRule *rule = &g_m68k_sim_exception_frame_rules[index];
    if ((rule->cpu_mask & cpu_mask) == 0U) continue;
    if (vector < rule->vector_start || vector > rule->vector_end) continue;
    *out_frame_kind = rule->frame_kind;
    return 1;
  }
  return 0;
}

static int sim_exception_frame_def_for_kind(uint8_t frame_kind, const M68kSimExceptionFrameDef **out_def) {
  size_t index;
  if (out_def == NULL) return 0;
  for (index = 0; index < sizeof(g_m68k_sim_exception_frames) / sizeof(g_m68k_sim_exception_frames[0]); ++index) {
    if (g_m68k_sim_exception_frames[index].frame_kind == frame_kind) {
      *out_def = &g_m68k_sim_exception_frames[index];
      return 1;
    }
  }
  return 0;
}

static int sim_exception_frame_def_for_format_code(uint8_t format_code, const M68kSimExceptionFrameDef **out_def) {
  size_t index;
  if (out_def == NULL) return 0;
  for (index = 0; index < sizeof(g_m68k_sim_exception_frames) / sizeof(g_m68k_sim_exception_frames[0]); ++index) {
    if (g_m68k_sim_exception_frames[index].format_code == format_code) {
      *out_def = &g_m68k_sim_exception_frames[index];
      return 1;
    }
  }
  return 0;
}

static int sim_concrete_push_frame_word(uint8_t *memory, size_t memory_size, uint32_t *io_sp, uint16_t value) {
  if (memory == NULL || io_sp == NULL || *io_sp < 2U) return 0;
  *io_sp -= 2U;
  if (*io_sp + 2U > memory_size) return 0;
  memory[*io_sp] = (uint8_t)((value >> 8) & 0xFFU);
  memory[*io_sp + 1U] = (uint8_t)(value & 0xFFU);
  return 1;
}

static int sim_concrete_push_frame_long(uint8_t *memory, size_t memory_size, uint32_t *io_sp, uint32_t value) {
  if (memory == NULL || io_sp == NULL || *io_sp < 4U) return 0;
  *io_sp -= 4U;
  if (*io_sp + 4U > memory_size) return 0;
  memory[*io_sp] = (uint8_t)((value >> 24) & 0xFFU);
  memory[*io_sp + 1U] = (uint8_t)((value >> 16) & 0xFFU);
  memory[*io_sp + 2U] = (uint8_t)((value >> 8) & 0xFFU);
  memory[*io_sp + 3U] = (uint8_t)(value & 0xFFU);
  return 1;
}

static int sim_concrete_return_from_metadata(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t target_cpu, uint8_t *memory, size_t memory_size, M68kSimConcreteState *io_state,
    M68kDiagSink diagnostics) {
  uint8_t usp_reg, isp_reg;
  uint16_t restored_sr, frame_word = 0U;
  uint32_t stack_pointer, restored_pc, next_sp;
  int restore_user_mode;
  const M68kSimExceptionFrameDef *frame_def = NULL;
  if (metadata == NULL || memory == NULL || io_state == NULL) {
    sim_diag_error(diagnostics, "bad arguments");
    return -1;
  }
  if (metadata->exception_trigger == M68K_SIM_EXCEPTION_TRIGGER_IF_USER_MODE &&
      (io_state->sr & 0x2000U) == 0U) {
    return sim_concrete_enter_exception(instruction, metadata, NULL, target_cpu, memory, memory_size, io_state,
      diagnostics) ? 0 : -1;
  }
  stack_pointer = io_state->a[7];
  if (metadata->return_restore_kind == M68K_SIM_RETURN_RESTORE_PC_ONLY) {
    if (stack_pointer + 4U > memory_size) {
      sim_diag_error(diagnostics, "stack out of range");
      return -1;
    }
    restored_pc = m68k_read_u32be(memory + stack_pointer);
    next_sp = stack_pointer + 4U;
    if (metadata->return_stack_adjust_operand_index < instruction->operand_count) {
      uint32_t raw_adjust;
      int32_t signed_adjust;
      if (!sim_operand_is_immediate_value(&instruction->operands[metadata->return_stack_adjust_operand_index], &raw_adjust)) {
        sim_diag_error(diagnostics, "unsupported concrete return adjustment");
        return -1;
      }
      signed_adjust = (int32_t)(int16_t)(raw_adjust & 0xFFFFU);
      next_sp = (uint32_t)(next_sp + signed_adjust);
    }
    io_state->pc = restored_pc;
    io_state->a[7] = next_sp;
    return 0;
  }
  if (metadata->return_restore_kind == M68K_SIM_RETURN_RESTORE_CCR_THEN_PC) {
    if (stack_pointer + 6U > memory_size) {
      sim_diag_error(diagnostics, "stack out of range");
      return -1;
    }
    restored_sr = (uint16_t)((io_state->sr & 0xFF00U) | m68k_read_u16be(memory + stack_pointer));
    restored_pc = m68k_read_u32be(memory + stack_pointer + 2U);
    io_state->sr = restored_sr;
    io_state->pc = restored_pc;
    io_state->a[7] = stack_pointer + 6U;
    return 0;
  }
  if (metadata->return_restore_kind != M68K_SIM_RETURN_RESTORE_EXCEPTION_FRAME) {
    sim_diag_error(diagnostics, "unsupported concrete return restore");
    return -1;
  }
  if (target_cpu == M68K_ASM_CPU_68000) {
    if (!sim_exception_frame_def_for_kind(M68K_SIM_EXCEPTION_FRAME_MC68000_GROUP_1_2, &frame_def)) {
      sim_diag_error(diagnostics, "unsupported concrete exception/trap: frame format");
      return -1;
    }
  } else {
    if (stack_pointer + 8U > memory_size) {
      sim_diag_error(diagnostics, "stack out of range");
      return -1;
    }
    frame_word = m68k_read_u16be(memory + stack_pointer + 6U);
    if (((frame_word >> 12) & 0x0FU) == 0U) {
      if (!sim_exception_frame_def_for_kind(M68K_SIM_EXCEPTION_FRAME_FORMAT_0, &frame_def)) {
        sim_diag_error(diagnostics, "unsupported concrete exception/trap: frame format");
        return -1;
      }
    } else if (!sim_exception_frame_def_for_format_code((uint8_t)((frame_word >> 12) & 0x0FU), &frame_def)) {
      sim_diag_error(diagnostics, "unsupported concrete exception/trap: frame format");
      return -1;
    }
  }
  if (frame_def == NULL || stack_pointer + frame_def->frame_size_bytes > memory_size) {
    sim_diag_error(diagnostics, "stack out of range");
    return -1;
  }
  restored_sr = m68k_read_u16be(memory + stack_pointer);
  restored_pc = m68k_read_u32be(memory + stack_pointer + 2U);
  next_sp = stack_pointer + frame_def->frame_size_bytes;
  restore_user_mode = (restored_sr & 0x2000U) == 0U;
  if (restore_user_mode) {
    if (sim_known_control_register_index(M68K_ASM_CONTROL_REGISTER_ISP, &isp_reg)) io_state->c[isp_reg] = next_sp;
    if (sim_usp_control_register_index(&usp_reg)) io_state->a[7] = io_state->c[usp_reg];
    else io_state->a[7] = next_sp;
  } else {
    io_state->a[7] = next_sp;
    if (sim_known_control_register_index(M68K_ASM_CONTROL_REGISTER_ISP, &isp_reg)) io_state->c[isp_reg] = next_sp;
  }
  io_state->sr = restored_sr;
  io_state->pc = restored_pc;
  return 0;
}

static int sim_concrete_enter_exception(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    const uint16_t *saved_sr_override, uint8_t target_cpu, uint8_t *memory, size_t memory_size,
    M68kSimConcreteState *io_state,
    M68kDiagSink diagnostics) {
  uint8_t vector, frame_kind, usp_reg, isp_reg, vbr_reg;
  uint32_t current_pc, saved_pc, vector_base = 0U, vector_address, handler_pc, stack_pointer;
  uint16_t saved_sr, next_sr;
  int user_mode;
  if (metadata == NULL || memory == NULL || io_state == NULL) {
    sim_diag_error(diagnostics, "bad arguments");
    return 0;
  }
  if (metadata->exception_vector_source == M68K_SIM_EXCEPTION_VECTOR_FIXED) {
    vector = metadata->exception_vector;
  } else if (metadata->exception_vector_source == M68K_SIM_EXCEPTION_VECTOR_TRAP_IMMEDIATE) {
    if (instruction->operand_count == 0U ||
        !sim_operand_is_immediate_value(&instruction->operands[0], &handler_pc)) {
      sim_diag_error(diagnostics, "unsupported concrete exception/trap: trap vector");
      return 0;
    }
    vector = (uint8_t)(32U + (handler_pc & 0x0FU));
  } else {
    sim_diag_error(diagnostics, "unsupported concrete exception/trap: vector source");
    return 0;
  }
  if (!sim_exception_frame_kind_for(target_cpu, vector, &frame_kind)) {
    sim_diag_error(diagnostics, "unsupported concrete exception/trap: frame kind");
    return 0;
  }
  if (target_cpu >= M68K_ASM_CPU_68020 && (io_state->sr & 0x1000U) != 0U) {
    sim_diag_error(diagnostics, "unsupported concrete exception/trap: trace mode");
    return 0;
  }
  current_pc = io_state->pc;
  saved_pc = metadata->exception_pc_source == M68K_SIM_EXCEPTION_PC_NEXT
    ? current_pc + (uint32_t)instruction->byte_count
    : current_pc;
  saved_sr = saved_sr_override != NULL ? *saved_sr_override : io_state->sr;
  user_mode = (saved_sr & 0x2000U) == 0U;
  stack_pointer = io_state->a[7];
  if (user_mode) {
    if (sim_usp_control_register_index(&usp_reg)) io_state->c[usp_reg] = io_state->a[7];
    if (sim_known_control_register_index(M68K_ASM_CONTROL_REGISTER_ISP, &isp_reg)) stack_pointer = io_state->c[isp_reg];
  } else if (target_cpu >= M68K_ASM_CPU_68010 &&
      sim_known_control_register_index(M68K_ASM_CONTROL_REGISTER_ISP, &isp_reg)) {
    stack_pointer = io_state->c[isp_reg];
  }
  if (target_cpu >= M68K_ASM_CPU_68010 &&
      sim_known_control_register_index(M68K_ASM_CONTROL_REGISTER_VBR, &vbr_reg)) {
    vector_base = io_state->c[vbr_reg];
  }
  if (frame_kind == M68K_SIM_EXCEPTION_FRAME_MC68000_GROUP_1_2) {
    if (!sim_concrete_push_frame_long(memory, memory_size, &stack_pointer, saved_pc) ||
        !sim_concrete_push_frame_word(memory, memory_size, &stack_pointer, saved_sr)) {
      sim_diag_error(diagnostics, "stack out of range");
      return 0;
    }
  } else if (frame_kind == M68K_SIM_EXCEPTION_FRAME_FORMAT_0) {
    uint16_t format_vector = (uint16_t)(vector << 2);
    if (!sim_concrete_push_frame_word(memory, memory_size, &stack_pointer, format_vector) ||
        !sim_concrete_push_frame_long(memory, memory_size, &stack_pointer, saved_pc) ||
        !sim_concrete_push_frame_word(memory, memory_size, &stack_pointer, saved_sr)) {
      sim_diag_error(diagnostics, "stack out of range");
      return 0;
    }
  } else if (frame_kind == M68K_SIM_EXCEPTION_FRAME_FORMAT_2) {
    uint16_t format_vector = (uint16_t)(0x2000U | (vector << 2));
    uint32_t address_value = metadata->exception_address_source == M68K_SIM_EXCEPTION_ADDRESS_CURRENT_PC ? current_pc : 0U;
    if (!sim_concrete_push_frame_long(memory, memory_size, &stack_pointer, address_value) ||
        !sim_concrete_push_frame_word(memory, memory_size, &stack_pointer, format_vector) ||
        !sim_concrete_push_frame_long(memory, memory_size, &stack_pointer, saved_pc) ||
        !sim_concrete_push_frame_word(memory, memory_size, &stack_pointer, saved_sr)) {
      sim_diag_error(diagnostics, "stack out of range");
      return 0;
    }
  } else {
    sim_diag_error(diagnostics, "unsupported concrete exception/trap: frame format");
    return 0;
  }
  io_state->a[7] = stack_pointer;
  if (sim_known_control_register_index(M68K_ASM_CONTROL_REGISTER_ISP, &isp_reg)) io_state->c[isp_reg] = stack_pointer;
  vector_address = vector_base + ((uint32_t)vector * 4U);
  if (vector_address + 4U > memory_size) {
    sim_diag_error(diagnostics, "vector out of range");
    return 0;
  }
  handler_pc = m68k_read_u32be(memory + vector_address);
  next_sr = (uint16_t)((saved_sr & 0x0700U) | 0x2000U);
  io_state->sr = next_sr;
  io_state->pc = handler_pc;
  return 1;
}

static int sim_set_unsupported_concrete_operation_error(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, M68kDiagSink diagnostics) {
  if (metadata == NULL) return 0;
  if (metadata->flow_kind == M68K_SIM_FLOW_TRAP) {
    sim_set_unsupported_concrete_exception_error(diagnostics);
    return 1;
  }
  if (metadata->operation_type == M68K_SIM_OP_NONE &&
      metadata->flow_kind == M68K_SIM_FLOW_CALL) {
    sim_diag_error(diagnostics, "unsupported concrete admin instruction");
    return 1;
  }
  if (metadata->operation_type == M68K_SIM_OP_NONE &&
      metadata->flow_kind == M68K_SIM_FLOW_SEQUENTIAL &&
      !sim_is_explicit_concrete_noop(instruction, metadata)) {
    sim_diag_error(diagnostics, "unsupported concrete admin instruction");
    return 1;
  }
  return 0;
}

int m68k_simulate_step_with_memory(const M68kObject *object, size_t section_index, const M68kSection *section, uint32_t offset,
    const M68kInstructionIR *instruction, const M68kSimCpuState *state, const M68kSimMemoryState *memory_state,
    M68kSimStepResult *out_result) {
  const M68kSimFormMetadata *metadata;
  M68kSimValue src;
  M68kSimValue dst;
  M68kSimValue value;
  uint8_t lhs_is_address;
  uint8_t lhs_reg;
  uint8_t rhs_is_address;
  uint8_t rhs_reg;
  uint8_t aux_operand_index;
  if (state == NULL || out_result == NULL) return -1;
  memset(out_result, 0, sizeof(*out_result));
  out_result->next_state = *state;
  out_result->next_state.pc = offset + (uint32_t)instruction->byte_count;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 0;
  if (metadata->flow_kind == M68K_SIM_FLOW_CALL) {
    sim_invalidate_call_condition_codes(out_result);
  }
  if (metadata->operation_class == M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count &&
      sim_compute_ea_address(section, instruction, offset, &instruction->operands[metadata->source_operand_index],
        metadata->operand_ea_address_formulas[metadata->source_operand_index],
        metadata->operand_ea_address_shapes[metadata->source_operand_index],
        metadata->operand_ea_base_kinds[metadata->source_operand_index],
        metadata->operand_ea_displacement_sources[metadata->source_operand_index],
        metadata->operand_ea_uses_displacement[metadata->source_operand_index],
        metadata->operand_ea_uses_index[metadata->source_operand_index],
        metadata->operand_ea_pc_base_bias_bytes[metadata->source_operand_index],
        metadata->operand_ea_address_literal_width_bytes[metadata->source_operand_index],
        metadata->operand_ea_index_extension_formats[metadata->source_operand_index],
        metadata->operand_ea_index_register_classes[metadata->source_operand_index],
        metadata->operand_ea_index_value_width_sources[metadata->source_operand_index],
        metadata->operand_ea_index_scale_sources[metadata->source_operand_index],
        metadata->operand_ea_index_sign_sources[metadata->source_operand_index],
        state, section_index, &value)) {
    sim_write_register(&out_result->next_state, &instruction->operands[metadata->dest_operand_index], &value);
    if (value.kind == M68K_SIM_VALUE_SECTION_PTR) m68k_sim_target_set_add(&out_result->discovered_labels, value.value);
  } else if (metadata->operation_type == M68K_SIM_OP_MOVE &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], state, memory_state, out_result, &src)) {
    if (sim_move_updates_condition_codes(instruction, metadata)) {
      if (sim_value_is_path_stable_for_flags(&src)) {
        sim_apply_abstract_nz_flags(state->sr, src.value,
          sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), &out_result->next_state.sr);
        sim_mark_condition_codes_defined(out_result);
      } else {
        sim_invalidate_defined_condition_codes(out_result);
      }
    }
    sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
      metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state, &src);
    if (src.kind == M68K_SIM_VALUE_SECTION_PTR) {
      m68k_sim_target_set_add(&out_result->discovered_labels, src.value);
    } else {
      sim_expand_value_targets(memory_state, &src, &out_result->discovered_labels);
    }
  } else if (metadata->operation_type == M68K_SIM_OP_MOVE &&
      metadata->dest_operand_index < instruction->operand_count) {
    if (sim_move_updates_condition_codes(instruction, metadata)) {
      sim_invalidate_defined_condition_codes(out_result);
    }
    sim_clobber_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
      metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state);
  } else if (metadata->operation_type == M68K_SIM_OP_MOVE_PERIPHERAL && instruction->operand_count >= 2U) {
    uint8_t reg_index = metadata->striped_reg_operand_index;
    uint8_t address_index = metadata->striped_address_operand_index;
    uint8_t width = sim_operand_width_from_instruction(instruction);
    M68kSimValue address;
    if (reg_index >= instruction->operand_count || address_index >= instruction->operand_count) return 0;
    if (!sim_compute_ea_address(section, instruction, offset, &instruction->operands[address_index],
          metadata->operand_ea_address_formulas[address_index],
          metadata->operand_ea_address_shapes[address_index], metadata->operand_ea_base_kinds[address_index],
          metadata->operand_ea_displacement_sources[address_index],
          metadata->operand_ea_uses_displacement[address_index], metadata->operand_ea_uses_index[address_index],
          metadata->operand_ea_pc_base_bias_bytes[address_index],
          metadata->operand_ea_address_literal_width_bytes[address_index],
          metadata->operand_ea_index_extension_formats[address_index],
          metadata->operand_ea_index_register_classes[address_index],
          metadata->operand_ea_index_value_width_sources[address_index],
          metadata->operand_ea_index_scale_sources[address_index],
          metadata->operand_ea_index_sign_sources[address_index],
          state, section_index, &address) ||
        address.kind != M68K_SIM_VALUE_SECTION_PTR) {
      return 0;
    }
    if (metadata->striped_direction == M68K_SIM_STRIPED_REGISTER_TO_MEMORY) {
      if (!sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata, reg_index,
          &instruction->operands[reg_index],
          state, memory_state, out_result, &src)) return 0;
      if (src.kind != M68K_SIM_VALUE_CONSTANT) src = g_m68k_sim_unknown_value;
      {
        uint8_t byte_index;
        for (byte_index = 0U; byte_index < width; ++byte_index) {
          uint32_t byte_address = sim_striped_transfer_byte_address(address.value, metadata->striped_stride, byte_index);
          M68kSimValue byte_value = g_m68k_sim_unknown_value;
          if (byte_address >= section->data_size) continue;
          if (src.kind == M68K_SIM_VALUE_CONSTANT) {
            uint8_t shift = (uint8_t)(8U * (width - 1U - byte_index));
            byte_value = sim_value_constant((src.value >> shift) & 0xFFU, M68K_SIM_PROV_REGISTER_COPY);
          }
          sim_add_memory_write(out_result, 1U, section_index, byte_address, &byte_value);
          sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_WRITE, 1U, section_index, byte_address);
          m68k_sim_target_set_add(&out_result->discovered_labels, byte_address);
        }
      }
    } else if (metadata->striped_direction == M68K_SIM_STRIPED_MEMORY_TO_REGISTER) {
      uint32_t combined = 0U;
      int known = 1;
      uint8_t byte_index;
      for (byte_index = 0U; byte_index < width; ++byte_index) {
        M68kSimValue byte_value;
        uint32_t byte_address = sim_striped_transfer_byte_address(address.value, metadata->striped_stride, byte_index);
        if (byte_address >= section->data_size ||
            !sim_read_same_section_memory_value_sized(object, section_index, section, memory_state, byte_address, 1U, &byte_value) ||
            byte_value.kind != M68K_SIM_VALUE_CONSTANT) {
          known = 0;
          break;
        }
        combined = (combined << 8) | (byte_value.value & 0xFFU);
        sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_READ, 1U, section_index, byte_address);
      }
      if (known) {
        if (width == 2U) combined = (uint32_t)(int32_t)(int16_t)(combined & 0xFFFFU);
        value = sim_value_constant(combined, M68K_SIM_PROV_MEMORY_LOAD);
      } else {
        value = g_m68k_sim_unknown_value;
      }
      sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
        reg_index, &instruction->operands[reg_index], &out_result->next_state, &value);
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_ADD || metadata->operation_type == M68K_SIM_OP_SUB) &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], state, memory_state, out_result, &src) &&
      sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index,
        &instruction->operands[metadata->dest_operand_index], &lhs_is_address, &lhs_reg) &&
      sim_register_value(state, lhs_is_address, lhs_reg, &dst) &&
      sim_apply_add_sub(metadata->operation_type == M68K_SIM_OP_SUB, &dst, &src, &value)) {
    if (!lhs_is_address) {
      if (src.kind == M68K_SIM_VALUE_CONSTANT && dst.kind == M68K_SIM_VALUE_CONSTANT &&
          sim_value_is_path_stable_for_flags(&src) && sim_value_is_path_stable_for_flags(&dst) &&
          sim_apply_abstract_add_sub_flags(state->sr, dst.value, src.value,
            sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index),
            metadata->operation_type == M68K_SIM_OP_SUB, &out_result->next_state.sr)) {
        sim_mark_condition_codes_defined(out_result);
      } else {
        sim_invalidate_defined_condition_codes(out_result);
      }
    }
    sim_write_register(&out_result->next_state, &instruction->operands[metadata->dest_operand_index], &value);
    if (value.kind == M68K_SIM_VALUE_SECTION_PTR) m68k_sim_target_set_add(&out_result->discovered_labels, value.value);
  } else if ((metadata->operation_type == M68K_SIM_OP_ADD || metadata->operation_type == M68K_SIM_OP_SUB) &&
      metadata->dest_operand_index < instruction->operand_count) {
    sim_clobber_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
      metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state);
  } else if ((metadata->operation_type == M68K_SIM_OP_LOGIC_AND || metadata->operation_type == M68K_SIM_OP_LOGIC_OR ||
          metadata->operation_type == M68K_SIM_OP_LOGIC_XOR) &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], state, memory_state, out_result, &src) &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->dest_operand_index,
        &instruction->operands[metadata->dest_operand_index], state, memory_state, out_result, &dst) &&
      sim_apply_logic(metadata->operation_type, &dst, &src, &value)) {
    if (sim_value_is_path_stable_for_flags(&value)) {
      sim_apply_abstract_nz_flags(state->sr, value.value,
        sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), &out_result->next_state.sr);
      sim_mark_condition_codes_defined(out_result);
    } else {
      sim_invalidate_defined_condition_codes(out_result);
    }
    sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
      metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state, &value);
  } else if ((metadata->operation_type == M68K_SIM_OP_NEGATE || metadata->operation_type == M68K_SIM_OP_NOT ||
          metadata->operation_type == M68K_SIM_OP_SIGN_EXTEND || metadata->operation_type == M68K_SIM_OP_SWAP_WORDS) &&
      metadata->dest_operand_index < instruction->operand_count &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->dest_operand_index,
        &instruction->operands[metadata->dest_operand_index], state, memory_state, out_result, &dst) &&
      sim_apply_unary(metadata->operation_type, instruction, metadata, &dst, &value)) {
    if (sim_value_is_path_stable_for_flags(&value)) {
      uint8_t width = sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index);
      if (metadata->operation_type == M68K_SIM_OP_NEGATE && dst.kind == M68K_SIM_VALUE_CONSTANT) {
        sim_apply_abstract_compare_test_flags(state->sr, dst.value, 0U, width, 1U, &out_result->next_state.sr);
        sim_sync_extend_with_carry(&out_result->next_state.sr);
      } else {
        sim_apply_abstract_nz_flags(state->sr, value.value, width, &out_result->next_state.sr);
      }
      sim_mark_condition_codes_defined(out_result);
    } else {
      sim_invalidate_defined_condition_codes(out_result);
    }
    sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
      metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state, &value);
  } else if ((metadata->operation_type == M68K_SIM_OP_SHIFT || metadata->operation_type == M68K_SIM_OP_ROTATE ||
          metadata->operation_type == M68K_SIM_OP_ROTATE_EXTEND) &&
      metadata->dest_operand_index < instruction->operand_count &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->dest_operand_index,
        &instruction->operands[metadata->dest_operand_index], state, memory_state, out_result, &dst) &&
      (metadata->shift_count_source != M68K_SIM_SHIFT_COUNT_OPERAND ||
        (metadata->source_operand_index < instruction->operand_count &&
         sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
           metadata->source_operand_index,
           &instruction->operands[metadata->source_operand_index], state, memory_state, out_result, &src))) &&
      sim_apply_shift_rotate(metadata->operation_type, instruction, metadata, &dst,
        metadata->shift_count_source == M68K_SIM_SHIFT_COUNT_OPERAND ? &src : NULL,
        state->sr, &value, &out_result->next_state.sr)) {
    if (sim_value_is_path_stable_for_flags(&value)) sim_mark_condition_codes_defined(out_result);
    else sim_invalidate_defined_condition_codes(out_result);
    sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
      metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state, &value);
  } else if ((metadata->operation_type == M68K_SIM_OP_COMPARE || metadata->operation_type == M68K_SIM_OP_TEST) &&
      metadata->source_operand_index < instruction->operand_count &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], state, memory_state, out_result, &src)) {
      dst = g_m68k_sim_unknown_value;
      if (metadata->operation_type == M68K_SIM_OP_COMPARE &&
          metadata->dest_operand_index < instruction->operand_count) {
        sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
          metadata->dest_operand_index,
          &instruction->operands[metadata->dest_operand_index], state, memory_state, out_result, &dst);
      }
      if (src.kind == M68K_SIM_VALUE_CONSTANT) {
        uint8_t width = sim_effective_operand_width(instruction, metadata, metadata->source_operand_index);
        if (metadata->operation_type == M68K_SIM_OP_COMPARE && dst.kind == M68K_SIM_VALUE_CONSTANT &&
            sim_value_is_path_stable_for_flags(&src) && sim_value_is_path_stable_for_flags(&dst)) {
          sim_apply_abstract_compare_test_flags(state->sr, src.value, dst.value, width, 1U,
            &out_result->next_state.sr);
          sim_mark_condition_codes_defined(out_result);
        } else if (metadata->operation_type == M68K_SIM_OP_TEST && sim_value_is_path_stable_for_flags(&src)) {
          sim_apply_abstract_compare_test_flags(state->sr, src.value, 0U, width, 0U,
            &out_result->next_state.sr);
          sim_mark_condition_codes_defined(out_result);
        } else {
          sim_invalidate_defined_condition_codes(out_result);
        }
      } else {
        sim_invalidate_defined_condition_codes(out_result);
      }
  } else if ((metadata->operation_type == M68K_SIM_OP_MULTIPLY ||
          metadata->operation_type == M68K_SIM_OP_DIVIDE) &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->source_operand_index, &instruction->operands[metadata->source_operand_index],
        state, memory_state, out_result, &src) &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index],
        state, memory_state, out_result, &dst)) {
    value = g_m68k_sim_unknown_value;
    if (src.kind == M68K_SIM_VALUE_CONSTANT && dst.kind == M68K_SIM_VALUE_CONSTANT) {
      uint32_t result_value;
      int ok = 0;
      uint8_t overflow = 0U;
      if (metadata->operation_type == M68K_SIM_OP_MULTIPLY) {
        ok = metadata->numeric_is_signed
          ? sim_apply_signed_multiply(dst.value, src.value, &result_value)
          : sim_apply_unsigned_multiply(dst.value, src.value, &result_value);
        if (ok) {
          value = sim_value_constant(result_value, M68K_SIM_PROV_ADDRESS_ARITH);
          if (sim_apply_abstract_nz_flags(state->sr, result_value,
                sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index),
                &out_result->next_state.sr)) {
            sim_mark_condition_codes_defined(out_result);
          }
        }
      } else {
        ok = metadata->numeric_is_signed
          ? sim_apply_signed_divide_status(dst.value, src.value, &result_value, &overflow)
          : sim_apply_unsigned_divide_status(dst.value, src.value, &result_value, &overflow);
        if (ok && overflow) value = dst;
        else if (ok) value = sim_value_constant(result_value, M68K_SIM_PROV_ADDRESS_ARITH);
        if (ok) {
          uint32_t quotient = overflow ? dst.value : result_value;
          uint16_t next_sr;
          uint8_t q_low = (uint8_t)(quotient & 0xFFFFU);
          sim_update_sr_nzvc(state->sr,
            metadata->numeric_is_signed && !overflow && (quotient & 0x8000U) != 0U,
            !overflow && (q_low == 0U) && ((quotient & 0xFFFFU) == 0U),
            overflow, 0U, &next_sr);
          out_result->next_state.sr = next_sr;
          sim_mark_condition_codes_defined(out_result);
        }
      }
    } else {
      sim_invalidate_defined_condition_codes(out_result);
    }
    if (sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index,
          &instruction->operands[metadata->dest_operand_index], &lhs_is_address, &lhs_reg) &&
        !lhs_is_address) {
      sim_write_register_slot(&out_result->next_state, 0U, lhs_reg, &value);
    } else {
      sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
        metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state,
        &value);
    }
  } else if (metadata->operation_type == M68K_SIM_OP_BOUNDS_CHECK &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count) {
    uint8_t bounds_width = sim_effective_operand_width(instruction, metadata, metadata->source_operand_index);
    uint16_t next_sr;
    M68kSimValue bounds_address = g_m68k_sim_unknown_value;
    sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
      metadata->source_operand_index, &instruction->operands[metadata->source_operand_index],
      state, memory_state, out_result, &src);
    sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
      metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index],
      state, memory_state, out_result, &dst);
    if (metadata->bounds_mode == M68K_SIM_BOUNDS_UPPER_ONLY &&
        src.kind == M68K_SIM_VALUE_CONSTANT && dst.kind == M68K_SIM_VALUE_CONSTANT && bounds_width != 0U) {
      int in_range = sim_value_in_bounds(dst.value, 0U, src.value, bounds_width, metadata->numeric_is_signed);
      sim_update_sr_nzvc(state->sr, 0U, 0U, 0U, in_range ? 0U : 1U, &next_sr);
      out_result->next_state.sr = next_sr;
      sim_mark_condition_codes_defined(out_result);
      if (!in_range && metadata->bounds_trap_on_fail) out_result->stops_fallthrough = 1;
    } else if (metadata->bounds_mode == M68K_SIM_BOUNDS_LOWER_UPPER_PAIR &&
        sim_compute_ea_address(section, instruction, offset, &instruction->operands[metadata->source_operand_index],
          metadata->operand_ea_address_formulas[metadata->source_operand_index],
          sim_effective_ea_shape(metadata->operand_ea_address_shapes[metadata->source_operand_index],
            &instruction->operands[metadata->source_operand_index]),
          metadata->operand_ea_base_kinds[metadata->source_operand_index],
          metadata->operand_ea_displacement_sources[metadata->source_operand_index],
          metadata->operand_ea_uses_displacement[metadata->source_operand_index],
          metadata->operand_ea_uses_index[metadata->source_operand_index],
          metadata->operand_ea_pc_base_bias_bytes[metadata->source_operand_index],
          metadata->operand_ea_address_literal_width_bytes[metadata->source_operand_index],
          metadata->operand_ea_index_extension_formats[metadata->source_operand_index],
          metadata->operand_ea_index_register_classes[metadata->source_operand_index],
          metadata->operand_ea_index_value_width_sources[metadata->source_operand_index],
          metadata->operand_ea_index_scale_sources[metadata->source_operand_index],
          metadata->operand_ea_index_sign_sources[metadata->source_operand_index],
          state, section_index, &bounds_address) &&
        bounds_address.kind == M68K_SIM_VALUE_SECTION_PTR &&
        dst.kind == M68K_SIM_VALUE_CONSTANT && bounds_width != 0U &&
        bounds_address.value + (uint32_t)(2U * bounds_width) <= section->data_size) {
      M68kSimValue low_value;
      M68kSimValue high_value;
      if (sim_read_same_section_memory_value_sized(object, section_index, section, memory_state,
            bounds_address.value, bounds_width, &low_value) &&
          sim_read_same_section_memory_value_sized(object, section_index, section, memory_state,
            bounds_address.value + bounds_width, bounds_width, &high_value) &&
          low_value.kind == M68K_SIM_VALUE_CONSTANT && high_value.kind == M68K_SIM_VALUE_CONSTANT) {
        int in_range = sim_value_in_bounds(dst.value, low_value.value, high_value.value, bounds_width, metadata->numeric_is_signed);
        sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_READ, bounds_width, section_index, bounds_address.value);
        sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_READ, bounds_width, section_index, bounds_address.value + bounds_width);
        sim_update_sr_nzvc(state->sr, 0U, 0U, 0U, in_range ? 0U : 1U, &next_sr);
        out_result->next_state.sr = next_sr;
        sim_mark_condition_codes_defined(out_result);
        if (!in_range && metadata->bounds_trap_on_fail) out_result->stops_fallthrough = 1;
      }
    }
  } else if (metadata->operation_type == M68K_SIM_OP_COMPARE_SWAP &&
      instruction->operand_count >= 3U &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata, 0U,
        &instruction->operands[0], state, memory_state, out_result, &src) &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata, 1U,
        &instruction->operands[1], state, memory_state, out_result, &dst)) {
    uint32_t mask = sim_mask_for_width(sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index));
    uint8_t width = sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index);
    if (instruction->operands[0].kind == M68K_ASM_OPERAND_DN_PAIR &&
        instruction->operands[1].kind == M68K_ASM_OPERAND_DN_PAIR &&
        instruction->operands[metadata->dest_operand_index].kind == M68K_ASM_OPERAND_RN_PAIR) {
      const M68kAsmOperandValue *compare_pair = &instruction->operands[0].value;
      const M68kAsmOperandValue *update_pair = &instruction->operands[1].value;
      const M68kAsmOperandValue *dest_pair = &instruction->operands[metadata->dest_operand_index].value;
      M68kSimValue current1;
      M68kSimValue current2;
      if (compare_pair->reg < 8U && compare_pair->pair_reg < 8U &&
          update_pair->reg < 8U && update_pair->pair_reg < 8U &&
          dest_pair->reg_is_address && dest_pair->pair_reg_is_address &&
          dest_pair->reg < 8U && dest_pair->pair_reg < 8U &&
          state->a[dest_pair->reg].kind == M68K_SIM_VALUE_SECTION_PTR &&
          state->a[dest_pair->pair_reg].kind == M68K_SIM_VALUE_SECTION_PTR &&
          sim_read_same_section_memory_value_sized(object, section_index, section, memory_state,
            state->a[dest_pair->reg].value, width, &current1) &&
          sim_read_same_section_memory_value_sized(object, section_index, section, memory_state,
            state->a[dest_pair->pair_reg].value, width, &current2) &&
          current1.kind == M68K_SIM_VALUE_CONSTANT && current2.kind == M68K_SIM_VALUE_CONSTANT &&
          state->d[compare_pair->reg].kind == M68K_SIM_VALUE_CONSTANT &&
          state->d[compare_pair->pair_reg].kind == M68K_SIM_VALUE_CONSTANT) {
        uint8_t success = (current1.value & mask) == (state->d[compare_pair->reg].value & mask) &&
          (current2.value & mask) == (state->d[compare_pair->pair_reg].value & mask);
        if (sim_apply_abstract_compare_test_flags(state->sr, state->d[compare_pair->reg].value,
              current1.value, width, 1U, &out_result->next_state.sr)) {
          if (success) {
            out_result->next_state.sr = (uint16_t)(out_result->next_state.sr | (1U << g_m68k_sim_ccr_bit_z));
          } else {
            out_result->next_state.sr = (uint16_t)(out_result->next_state.sr & ~(1U << g_m68k_sim_ccr_bit_z));
          }
          sim_mark_condition_codes_defined(out_result);
        }
        if (success) {
          sim_add_memory_write(out_result, width, section_index, state->a[dest_pair->reg].value, &state->d[update_pair->reg]);
          sim_add_memory_write(out_result, width, section_index, state->a[dest_pair->pair_reg].value, &state->d[update_pair->pair_reg]);
          sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_WRITE, width, section_index, state->a[dest_pair->reg].value);
          sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_WRITE, width, section_index, state->a[dest_pair->pair_reg].value);
        } else {
          sim_write_register_slot(&out_result->next_state, 0U, compare_pair->reg, &current1);
          sim_write_register_slot(&out_result->next_state, 0U, compare_pair->pair_reg, &current2);
        }
      }
    } else if (sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
          metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index],
          state, memory_state, out_result, &value) &&
        src.kind == M68K_SIM_VALUE_CONSTANT && value.kind == M68K_SIM_VALUE_CONSTANT) {
      if (sim_apply_abstract_compare_test_flags(state->sr, src.value, value.value, width, 1U,
            &out_result->next_state.sr)) {
        if ((src.value & mask) == (value.value & mask)) {
          out_result->next_state.sr = (uint16_t)(out_result->next_state.sr | (1U << g_m68k_sim_ccr_bit_z));
        } else {
          out_result->next_state.sr = (uint16_t)(out_result->next_state.sr & ~(1U << g_m68k_sim_ccr_bit_z));
        }
        sim_mark_condition_codes_defined(out_result);
      }
      if ((src.value & mask) == (value.value & mask)) {
        sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
          metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state,
          &dst);
      } else {
        sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
          0U, &instruction->operands[0], &out_result->next_state, &value);
      }
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_BITFIELD_CHANGE ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_CLEAR ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_SET ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_TEST) &&
      metadata->source_operand_index < instruction->operand_count) {
    uint8_t bf_reg;
    uint32_t bf_offset;
    uint32_t bf_width;
    uint32_t field_value;
    const M68kOperandIR *bf_operand = &instruction->operands[metadata->source_operand_index];
    if (metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT &&
        metadata->dest_operand_index < instruction->operand_count) {
      bf_operand = &instruction->operands[metadata->dest_operand_index];
    }
    if (sim_bitfield_is_direct_data_register(bf_operand, &bf_reg) &&
        sim_bitfield_resolve_spec_abstract(&bf_operand->value, state, &bf_offset, &bf_width) &&
        state->d[bf_reg].kind == M68K_SIM_VALUE_CONSTANT) {
      field_value = sim_bitfield_extract_from_register(state->d[bf_reg].value, bf_offset, bf_width);
      sim_apply_abstract_bitfield_flags(out_result, state->sr, field_value, bf_width);
      sim_mark_condition_codes_defined(out_result);
      if (metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE) {
        uint32_t written = field_value;
        if (metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED && bf_width < 32U) {
          written = sim_sign_extend_value(field_value, (uint8_t)bf_width);
        } else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE) {
          written = bf_offset + sim_bitfield_find_first_one(field_value, bf_width);
        }
        value = sim_value_constant(written, M68K_SIM_PROV_REGISTER_COPY);
        sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
          metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state,
          &value);
      } else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CHANGE ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_CLEAR ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_SET) {
        uint32_t updated_bits = field_value;
        if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CHANGE) updated_bits ^= sim_mask_for_width(4U) >> (32U - bf_width);
        else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CLEAR) updated_bits = 0U;
        else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_SET) updated_bits = sim_mask_for_width(4U) >> (32U - bf_width);
        else if (metadata->source_operand_index < instruction->operand_count &&
            sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
              metadata->source_operand_index, &instruction->operands[metadata->source_operand_index],
              state, memory_state, out_result, &src) &&
            src.kind == M68K_SIM_VALUE_CONSTANT) {
          updated_bits = src.value & (sim_mask_for_width(4U) >> (32U - bf_width));
        } else {
          updated_bits = 0U;
        }
        value = sim_value_constant(sim_bitfield_insert_into_register(
            state->d[bf_reg].value, bf_offset, bf_width, updated_bits), M68K_SIM_PROV_REGISTER_COPY);
        out_result->next_state.d[bf_reg] = value;
      }
    } else if (sim_bitfield_resolve_spec_abstract(&bf_operand->value, state, &bf_offset, &bf_width)) {
      M68kSimValue address;
      M68kOperandIR ea_operand = *bf_operand;
      ea_operand.kind = M68K_ASM_OPERAND_EA;
      if (sim_compute_ea_address(section, instruction, offset, &ea_operand,
            metadata->operand_ea_address_formulas[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_address_shapes[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_base_kinds[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_displacement_sources[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_uses_displacement[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_uses_index[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_pc_base_bias_bytes[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_address_literal_width_bytes[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_index_extension_formats[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_index_register_classes[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_index_value_width_sources[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_index_scale_sources[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            metadata->operand_ea_index_sign_sources[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
              ? metadata->dest_operand_index : metadata->source_operand_index],
            state, section_index, &address) &&
          address.kind == M68K_SIM_VALUE_SECTION_PTR &&
          sim_abstract_read_memory_bitfield(object, section_index, section, memory_state, address.value,
            bf_offset, bf_width, out_result, &field_value)) {
        sim_apply_abstract_bitfield_flags(out_result, state->sr, field_value, bf_width);
        sim_mark_condition_codes_defined(out_result);
        if (metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED ||
            metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED ||
            metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE) {
          uint32_t written = field_value;
          if (metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED && bf_width < 32U) {
            written = sim_sign_extend_value(field_value, (uint8_t)bf_width);
          } else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE) {
            written = bf_offset + sim_bitfield_find_first_one(field_value, bf_width);
          }
          value = sim_value_constant(written, M68K_SIM_PROV_MEMORY_LOAD);
          sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
            metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state,
            &value);
        } else {
          uint32_t updated_bits = field_value;
          if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CHANGE) updated_bits ^= sim_bitfield_mask(bf_width);
          else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CLEAR) updated_bits = 0U;
          else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_SET) updated_bits = sim_bitfield_mask(bf_width);
          else if (metadata->source_operand_index < instruction->operand_count &&
              sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
                metadata->source_operand_index, &instruction->operands[metadata->source_operand_index],
                state, memory_state, out_result, &src) && src.kind == M68K_SIM_VALUE_CONSTANT) {
            updated_bits = src.value & sim_bitfield_mask(bf_width);
          } else {
            updated_bits = 0U;
          }
          sim_abstract_write_memory_bitfield(object, section_index, section, memory_state, address.value,
            bf_offset, bf_width, updated_bits, out_result);
        }
      }
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_PACK || metadata->operation_type == M68K_SIM_OP_UNPACK) &&
      instruction->operand_count >= 3U) {
    const M68kOperandIR *pack_source = &instruction->operands[metadata->source_operand_index];
    const M68kOperandIR *pack_dest = &instruction->operands[metadata->dest_operand_index];
    const M68kOperandIR *pack_adjust = &instruction->operands[2];
    M68kSimValue adjust_value;
    M68kSimValue source_address;
    M68kSimValue dest_address;
    M68kSimValue packed_value;
    if (!sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata, 2U,
          pack_adjust, state, memory_state, out_result, &adjust_value)) {
      return 0;
    }
    if (metadata->operand_ea_register_updates[metadata->source_operand_index] == M68K_SIM_EA_UPDATE_PREDECREMENT) {
      if (!sim_apply_predecrement_operand(instruction, metadata, metadata->source_operand_index, pack_source,
            &out_result->next_state, &source_address)) {
        return 0;
      }
      if (source_address.kind == M68K_SIM_VALUE_SECTION_PTR && source_address.value < section->data_size &&
          sim_read_same_section_memory_value_sized(object, section_index, section, memory_state, source_address.value,
            sim_effective_operand_width(instruction, metadata, metadata->source_operand_index), &src)) {
        sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_READ,
          sim_effective_operand_width(instruction, metadata, metadata->source_operand_index), section_index,
          source_address.value);
      } else {
        src = g_m68k_sim_unknown_value;
      }
    } else if (!sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
          metadata->source_operand_index, pack_source, &out_result->next_state, memory_state, out_result, &src)) {
      return 0;
    }
    if (src.kind == M68K_SIM_VALUE_CONSTANT && adjust_value.kind == M68K_SIM_VALUE_CONSTANT) {
      packed_value = sim_value_constant(metadata->operation_type == M68K_SIM_OP_PACK
          ? sim_pack_value(src.value, (uint16_t)adjust_value.value)
          : sim_unpack_value(src.value, (uint16_t)adjust_value.value),
        M68K_SIM_PROV_ADDRESS_ARITH);
    } else {
      packed_value = g_m68k_sim_unknown_value;
    }
    if (metadata->operand_ea_register_updates[metadata->dest_operand_index] == M68K_SIM_EA_UPDATE_PREDECREMENT) {
      if (!sim_apply_predecrement_operand(instruction, metadata, metadata->dest_operand_index, pack_dest,
            &out_result->next_state, &dest_address)) {
        return 0;
      }
      if (dest_address.kind == M68K_SIM_VALUE_SECTION_PTR && dest_address.value < section->data_size) {
        sim_add_memory_write(out_result,
          sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), section_index,
          dest_address.value, &packed_value);
        sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_WRITE,
          sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), section_index,
          dest_address.value);
        m68k_sim_target_set_add(&out_result->discovered_labels, dest_address.value);
      }
    } else {
      sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
        metadata->dest_operand_index, pack_dest, &out_result->next_state, &packed_value);
    }
  } else if (metadata->operation_type == M68K_SIM_OP_TEST_AND_SET &&
      metadata->source_operand_index < instruction->operand_count &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], state, memory_state, out_result, &src)) {
    if (src.kind == M68K_SIM_VALUE_CONSTANT) {
      sim_apply_abstract_nz_flags(state->sr, src.value, 1U, &out_result->next_state.sr);
      sim_mark_condition_codes_defined(out_result);
    }
    if (src.kind == M68K_SIM_VALUE_CONSTANT) {
      value = sim_value_constant(src.value | 0x80U, M68K_SIM_PROV_IMMEDIATE);
    } else {
      value = g_m68k_sim_unknown_value;
    }
    sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
      metadata->source_operand_index, &instruction->operands[metadata->source_operand_index], &out_result->next_state, &value);
  } else if (metadata->operation_type == M68K_SIM_OP_MOVE_PERIPHERAL && instruction->operand_count >= 2U) {
    uint8_t reg_index = metadata->striped_reg_operand_index;
    uint8_t address_index = metadata->striped_address_operand_index;
    uint8_t width = sim_operand_width_from_instruction(instruction);
    M68kSimValue address;
    if (reg_index >= instruction->operand_count || address_index >= instruction->operand_count) return 0;
    if (!sim_compute_ea_address(section, instruction, offset, &instruction->operands[address_index],
          metadata->operand_ea_address_formulas[address_index],
          metadata->operand_ea_address_shapes[address_index], metadata->operand_ea_base_kinds[address_index],
          metadata->operand_ea_displacement_sources[address_index],
          metadata->operand_ea_uses_displacement[address_index], metadata->operand_ea_uses_index[address_index],
          metadata->operand_ea_pc_base_bias_bytes[address_index],
          metadata->operand_ea_address_literal_width_bytes[address_index],
          metadata->operand_ea_index_extension_formats[address_index],
          metadata->operand_ea_index_register_classes[address_index],
          metadata->operand_ea_index_value_width_sources[address_index],
          metadata->operand_ea_index_scale_sources[address_index],
          metadata->operand_ea_index_sign_sources[address_index],
          state, section_index, &address) ||
        address.kind != M68K_SIM_VALUE_SECTION_PTR) return 0;
    if (metadata->striped_direction == M68K_SIM_STRIPED_REGISTER_TO_MEMORY) {
      uint8_t byte_index;
      if (!sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata, reg_index,
          &instruction->operands[reg_index],
          state, memory_state, out_result, &src)) return 0;
      if (src.kind != M68K_SIM_VALUE_CONSTANT) src = g_m68k_sim_unknown_value;
      for (byte_index = 0U; byte_index < width; ++byte_index) {
        uint32_t byte_address = sim_striped_transfer_byte_address(address.value, metadata->striped_stride, byte_index);
        M68kSimValue byte_value = g_m68k_sim_unknown_value;
        if (byte_address >= section->data_size) continue;
        if (src.kind == M68K_SIM_VALUE_CONSTANT) {
          uint8_t shift = (uint8_t)(8U * (width - 1U - byte_index));
          byte_value = sim_value_constant((src.value >> shift) & 0xFFU, M68K_SIM_PROV_REGISTER_COPY);
        }
        sim_add_memory_write(out_result, 1U, section_index, byte_address, &byte_value);
        sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_WRITE, 1U, section_index, byte_address);
        m68k_sim_target_set_add(&out_result->discovered_labels, byte_address);
      }
    } else if (metadata->striped_direction == M68K_SIM_STRIPED_MEMORY_TO_REGISTER) {
      uint32_t combined = 0U;
      int known = 1;
      uint8_t byte_index;
      for (byte_index = 0U; byte_index < width; ++byte_index) {
        M68kSimValue byte_value;
        uint32_t byte_address = sim_striped_transfer_byte_address(address.value, metadata->striped_stride, byte_index);
        if (byte_address >= section->data_size ||
            !sim_read_same_section_memory_value_sized(object, section_index, section, memory_state, byte_address, 1U, &byte_value) ||
            byte_value.kind != M68K_SIM_VALUE_CONSTANT) {
          known = 0;
          break;
        }
        combined = (combined << 8) | (byte_value.value & 0xFFU);
        sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_READ, 1U, section_index, byte_address);
      }
      value = known ? sim_value_constant(combined, M68K_SIM_PROV_MEMORY_LOAD) : g_m68k_sim_unknown_value;
      sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
        reg_index, &instruction->operands[reg_index], &out_result->next_state, &value);
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_BIT_TEST || metadata->operation_type == M68K_SIM_OP_BIT_SET ||
          metadata->operation_type == M68K_SIM_OP_BIT_CLEAR || metadata->operation_type == M68K_SIM_OP_BIT_CHANGE) &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], state, memory_state, out_result, &src) &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata,
        metadata->dest_operand_index,
        &instruction->operands[metadata->dest_operand_index], state, memory_state, out_result, &dst) &&
      sim_apply_bit_op(metadata->operation_type, metadata, metadata->dest_operand_index, &src,
        &instruction->operands[metadata->dest_operand_index], &dst, &value)) {
    sim_apply_abstract_bit_test_flags(state->sr, metadata, metadata->dest_operand_index,
      &instruction->operands[metadata->dest_operand_index], &src, &dst, &out_result->next_state.sr);
    if (src.kind == M68K_SIM_VALUE_CONSTANT && dst.kind == M68K_SIM_VALUE_CONSTANT) {
      sim_mark_condition_codes_defined(out_result);
    } else {
      sim_invalidate_defined_condition_codes(out_result);
    }
    if (metadata->operation_type != M68K_SIM_OP_BIT_TEST) {
      sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
        metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state, &value);
    }
  } else if (metadata->operation_type == M68K_SIM_OP_MOVE_MULTIPLE && instruction->operand_count >= 2U) {
    uint8_t width = sim_operand_width_from_instruction(instruction);
    uint8_t reglist_index = metadata->reglist_operand_index;
    uint8_t address_index = metadata->address_operand_index;
    const M68kOperandIR *address_operand;
    if (reglist_index >= instruction->operand_count || address_index >= instruction->operand_count) return 0;
    address_operand = &instruction->operands[address_index];
    if (metadata->multi_transfer_direction == M68K_SIM_MULTI_REGISTER_TO_MEMORY) {
        M68kSimValue address;
        uint32_t cursor;
        uint16_t mask = (uint16_t)instruction->operands[reglist_index].value.value;
        uint8_t address_reg;
        uint8_t address_shape = sim_effective_ea_shape(metadata->operand_ea_address_shapes[address_index], address_operand);
        int is_predecrement = sim_multi_transfer_uses_predecrement(metadata->multi_transfer_address_update,
          metadata->operand_ea_register_updates[address_index], address_shape);
        if (!sim_ea_address_register(address_shape, address_operand, &address_reg)) return 0;
        if (sim_compute_ea_address(section, instruction, offset, address_operand,
              metadata->operand_ea_address_formulas[address_index],
              metadata->operand_ea_address_shapes[address_index], metadata->operand_ea_base_kinds[address_index],
            metadata->operand_ea_displacement_sources[address_index],
            metadata->operand_ea_uses_displacement[address_index], metadata->operand_ea_uses_index[address_index],
            metadata->operand_ea_pc_base_bias_bytes[address_index],
            metadata->operand_ea_address_literal_width_bytes[address_index],
            metadata->operand_ea_index_extension_formats[address_index],
            metadata->operand_ea_index_register_classes[address_index],
            metadata->operand_ea_index_value_width_sources[address_index],
            metadata->operand_ea_index_scale_sources[address_index],
            metadata->operand_ea_index_sign_sources[address_index],
            state, section_index, &address) &&
          address.kind == M68K_SIM_VALUE_SECTION_PTR) {
        cursor = address.value;
        if (is_predecrement) {
          uint8_t count = sim_reglist_count(mask);
          cursor -= (uint32_t)width * (uint32_t)count;
          out_result->next_state.a[address_reg] = sim_value_section_ptr(address.section_index, cursor,
            M68K_SIM_PROV_ADDRESS_ARITH);
        }
        for (lhs_reg = 0U; lhs_reg < 16U; ++lhs_reg) {
          uint8_t reg_is_address;
          uint8_t reg_index;
          if (!sim_multi_transfer_includes_slot(metadata->multi_transfer_reg_iteration, mask, lhs_reg)) continue;
          if (!sim_reglist_slot(lhs_reg, &reg_is_address, &reg_index)) continue;
          src = reg_is_address ? state->a[reg_index] : state->d[reg_index];
          if (cursor + width <= section->data_size) {
            sim_add_memory_write(out_result, width, section_index, cursor, &src);
            sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_WRITE, width, section_index, cursor);
            m68k_sim_target_set_add(&out_result->discovered_labels, cursor);
          }
          cursor += width;
        }
      }
    } else if (metadata->multi_transfer_direction == M68K_SIM_MULTI_MEMORY_TO_REGISTER) {
        M68kSimValue address;
        uint32_t cursor;
        uint16_t mask = (uint16_t)instruction->operands[reglist_index].value.value;
        uint8_t address_reg;
        uint8_t address_shape = sim_effective_ea_shape(metadata->operand_ea_address_shapes[address_index], address_operand);
        int is_postincrement = sim_multi_transfer_uses_postincrement(metadata->multi_transfer_address_update,
          metadata->operand_ea_register_updates[address_index], address_shape);
        if (!sim_ea_address_register(address_shape, address_operand, &address_reg)) return 0;
        if (sim_compute_ea_address(section, instruction, offset, address_operand,
              metadata->operand_ea_address_formulas[address_index],
              metadata->operand_ea_address_shapes[address_index], metadata->operand_ea_base_kinds[address_index],
            metadata->operand_ea_displacement_sources[address_index],
            metadata->operand_ea_uses_displacement[address_index], metadata->operand_ea_uses_index[address_index],
            metadata->operand_ea_pc_base_bias_bytes[address_index],
            metadata->operand_ea_address_literal_width_bytes[address_index],
            metadata->operand_ea_index_extension_formats[address_index],
            metadata->operand_ea_index_register_classes[address_index],
            metadata->operand_ea_index_value_width_sources[address_index],
            metadata->operand_ea_index_scale_sources[address_index],
            metadata->operand_ea_index_sign_sources[address_index],
            state, section_index, &address) &&
          address.kind == M68K_SIM_VALUE_SECTION_PTR) {
        cursor = address.value;
        for (lhs_reg = 0U; lhs_reg < 16U; ++lhs_reg) {
          uint8_t reg_is_address;
          uint8_t reg_index;
          if (!sim_multi_transfer_includes_slot(metadata->multi_transfer_reg_iteration, mask, lhs_reg)) continue;
          if (!sim_reglist_slot(lhs_reg, &reg_is_address, &reg_index)) continue;
          if (cursor + width <= section->data_size &&
              sim_read_same_section_memory_value_sized(object, section_index, section, memory_state, cursor, width, &src)) {
            if (width == 2U && src.kind == M68K_SIM_VALUE_CONSTANT) {
              src.value = (uint32_t)(int32_t)(int16_t)(src.value & 0xFFFFU);
            }
            sim_write_register_slot(&out_result->next_state, reg_is_address, reg_index, &src);
            sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_READ, width, section_index, cursor);
            if (src.kind == M68K_SIM_VALUE_SECTION_PTR) m68k_sim_target_set_add(&out_result->discovered_labels, src.value);
          } else {
            sim_write_register_slot(&out_result->next_state, reg_is_address, reg_index, &g_m68k_sim_unknown_value);
          }
          cursor += width;
        }
        if (is_postincrement) {
          out_result->next_state.a[address_reg] = sim_value_section_ptr(address.section_index, cursor,
            M68K_SIM_PROV_ADDRESS_ARITH);
        }
      }
    }
  } else if (metadata->operation_type == M68K_SIM_OP_PUSH_EA &&
      metadata->source_operand_index < instruction->operand_count &&
      sim_compute_ea_address(section, instruction, offset, &instruction->operands[metadata->source_operand_index],
        metadata->operand_ea_address_formulas[metadata->source_operand_index],
        metadata->operand_ea_address_shapes[metadata->source_operand_index],
        metadata->operand_ea_base_kinds[metadata->source_operand_index],
        metadata->operand_ea_displacement_sources[metadata->source_operand_index],
        metadata->operand_ea_uses_displacement[metadata->source_operand_index],
        metadata->operand_ea_uses_index[metadata->source_operand_index],
        metadata->operand_ea_pc_base_bias_bytes[metadata->source_operand_index],
        metadata->operand_ea_address_literal_width_bytes[metadata->source_operand_index],
        metadata->operand_ea_index_extension_formats[metadata->source_operand_index],
        metadata->operand_ea_index_register_classes[metadata->source_operand_index],
        metadata->operand_ea_index_value_width_sources[metadata->source_operand_index],
        metadata->operand_ea_index_scale_sources[metadata->source_operand_index],
        metadata->operand_ea_index_sign_sources[metadata->source_operand_index],
        state, section_index, &src)) {
    dst = state->a[7];
    if (sim_adjust_value_by_constant(&dst, -4, &value)) {
      out_result->next_state.a[7] = value;
      if (value.kind == M68K_SIM_VALUE_SECTION_PTR && value.value < section->data_size) {
        sim_add_memory_write(out_result, 4U, section_index, value.value, &src);
        sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_WRITE, 4U, section_index, value.value);
        m68k_sim_target_set_add(&out_result->discovered_labels, value.value);
      }
    } else {
      out_result->next_state.a[7] = g_m68k_sim_unknown_value;
    }
    if (src.kind == M68K_SIM_VALUE_SECTION_PTR) m68k_sim_target_set_add(&out_result->discovered_labels, src.value);
  } else if (metadata->operation_type == M68K_SIM_OP_LINK &&
      instruction->operand_count >= 2U &&
      metadata->source_operand_index < instruction->operand_count &&
      (aux_operand_index = sim_find_operand_index_by_access(
        metadata, M68K_SIM_ACCESS_IMMEDIATE, metadata->source_operand_index)) < instruction->operand_count &&
      sim_direct_register_slot_by_metadata(metadata, metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], &lhs_is_address, &lhs_reg) &&
      lhs_is_address &&
      sim_eval_operand_by_metadata(object, section_index, section, instruction, offset, metadata, aux_operand_index,
        &instruction->operands[aux_operand_index],
        state, memory_state, out_result, &src)) {
    int32_t link_delta = 0;
    dst = state->a[7];
    if (sim_adjust_value_by_constant(&dst, -4, &value)) {
      out_result->next_state.a[lhs_reg] = value;
      if (value.kind == M68K_SIM_VALUE_SECTION_PTR && value.value < section->data_size) {
        sim_add_memory_write(out_result, 4U, section_index, value.value, &state->a[lhs_reg]);
        sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_WRITE, 4U, section_index, value.value);
        m68k_sim_target_set_add(&out_result->discovered_labels, value.value);
      }
      if (sim_link_displacement(instruction, &src, &link_delta) &&
          sim_adjust_value_by_constant(&value, link_delta, &dst)) {
        out_result->next_state.a[7] = dst;
      } else {
        out_result->next_state.a[7] = g_m68k_sim_unknown_value;
      }
    } else {
      out_result->next_state.a[lhs_reg] = g_m68k_sim_unknown_value;
      out_result->next_state.a[7] = g_m68k_sim_unknown_value;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_UNLK &&
      metadata->source_operand_index < instruction->operand_count &&
      sim_direct_register_slot_by_metadata(metadata, metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], &lhs_is_address, &lhs_reg) &&
      lhs_is_address) {
    src = state->a[lhs_reg];
    out_result->next_state.a[7] = src;
    if (src.kind == M68K_SIM_VALUE_SECTION_PTR && src.value < section->data_size &&
        sim_read_same_section_memory_value(object, section_index, section, memory_state, src.value, &dst)) {
      out_result->next_state.a[lhs_reg] = dst;
      sim_add_access(out_result, M68K_SIM_ACCESS_MEMORY_READ, 4U, section_index, src.value);
      if (dst.kind == M68K_SIM_VALUE_SECTION_PTR) m68k_sim_target_set_add(&out_result->discovered_labels, dst.value);
    } else {
      out_result->next_state.a[lhs_reg] = g_m68k_sim_unknown_value;
    }
    if (sim_adjust_value_by_constant(&src, 4, &value)) out_result->next_state.a[7] = value;
    else out_result->next_state.a[7] = g_m68k_sim_unknown_value;
  } else if (metadata->operation_type == M68K_SIM_OP_CLEAR && instruction->operand_count != 0U) {
    value = sim_value_constant(0U, M68K_SIM_PROV_IMMEDIATE);
    sim_apply_abstract_nz_flags(state->sr, 0U,
      sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), &out_result->next_state.sr);
    sim_mark_condition_codes_defined(out_result);
    sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
      metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state, &value);
  } else if (metadata->operation_type == M68K_SIM_OP_SET_COND && instruction->operand_count != 0U) {
    value = sim_value_constant(sim_condition_true(metadata->condition_code, state->sr) ? 0xFFU : 0U,
      M68K_SIM_PROV_IMMEDIATE);
    sim_write_operand_by_metadata(section, instruction, offset, section_index, out_result, metadata,
      metadata->dest_operand_index, &instruction->operands[metadata->dest_operand_index], &out_result->next_state, &value);
  } else if (metadata->operation_type == M68K_SIM_OP_DBCC && instruction->operand_count >= 1U &&
      metadata->source_operand_index < instruction->operand_count &&
      sim_direct_register_slot_by_metadata(metadata, metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], &lhs_is_address, &lhs_reg) &&
      !lhs_is_address) {
    dst = state->d[lhs_reg];
    if (!sim_condition_true(metadata->condition_code, state->sr)) {
      if (dst.kind == M68K_SIM_VALUE_CONSTANT) {
        value = sim_value_constant((dst.value & 0xFFFF0000U) | (uint32_t)(((dst.value & 0xFFFFU) - 1U) & 0xFFFFU),
          M68K_SIM_PROV_ADDRESS_ARITH);
      } else {
        value = g_m68k_sim_unknown_value;
      }
      out_result->next_state.d[lhs_reg] = value;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_SWAP &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count &&
      sim_direct_register_slot_by_metadata(metadata, metadata->source_operand_index,
        &instruction->operands[metadata->source_operand_index], &lhs_is_address, &lhs_reg) &&
      sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index,
        &instruction->operands[metadata->dest_operand_index], &rhs_is_address, &rhs_reg)) {
    src = lhs_is_address ? state->a[lhs_reg] : state->d[lhs_reg];
    dst = rhs_is_address ? state->a[rhs_reg] : state->d[rhs_reg];
    if (lhs_is_address) out_result->next_state.a[lhs_reg] = dst; else out_result->next_state.d[lhs_reg] = dst;
    if (rhs_is_address) out_result->next_state.a[rhs_reg] = src; else out_result->next_state.d[rhs_reg] = src;
  }
  if (out_result->defines_condition_codes == 0 && sim_operation_may_define_condition_codes(metadata)) {
    sim_invalidate_defined_condition_codes(out_result);
  }
  if (metadata->target_operand_index != 0xFFU && metadata->target_operand_index < instruction->operand_count) {
    const M68kOperandIR *target_operand = &instruction->operands[metadata->target_operand_index];
    int target_taken = 1;
    if (metadata->flow_conditional && metadata->operation_type != M68K_SIM_OP_DBCC) {
      target_taken = state->sr_known != 0U && sim_condition_true(metadata->condition_code, state->sr);
    }
    if (target_taken && sim_compute_ea_address(section, instruction, offset, target_operand,
          metadata->operand_ea_address_formulas[metadata->target_operand_index],
          metadata->operand_ea_address_shapes[metadata->target_operand_index],
          metadata->operand_ea_base_kinds[metadata->target_operand_index],
          metadata->operand_ea_displacement_sources[metadata->target_operand_index],
          metadata->operand_ea_uses_displacement[metadata->target_operand_index],
          metadata->operand_ea_uses_index[metadata->target_operand_index],
          metadata->operand_ea_pc_base_bias_bytes[metadata->target_operand_index],
          metadata->operand_ea_address_literal_width_bytes[metadata->target_operand_index],
          metadata->operand_ea_index_extension_formats[metadata->target_operand_index],
          metadata->operand_ea_index_register_classes[metadata->target_operand_index],
          metadata->operand_ea_index_value_width_sources[metadata->target_operand_index],
          metadata->operand_ea_index_scale_sources[metadata->target_operand_index],
          metadata->operand_ea_index_sign_sources[metadata->target_operand_index],
          &out_result->next_state, section_index, &value)) {
      if (value.kind == M68K_SIM_VALUE_SECTION_PTR) {
        m68k_sim_target_set_add(&out_result->control_targets, value.value);
      } else {
        sim_expand_value_targets(memory_state, &value, &out_result->control_targets);
      }
    }
    if (target_taken && out_result->control_targets.count == 0U && target_operand->kind == M68K_ASM_OPERAND_LABEL) {
      m68k_sim_target_set_add(&out_result->control_targets,
        offset + 2U + (uint32_t)((int32_t)target_operand->value.value));
    }
  }
  if (metadata->operation_type == M68K_SIM_OP_TRAPV) {
    out_result->stops_fallthrough = state->sr_known != 0U && (state->sr & 0x0002U) != 0U;
  } else if (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional &&
      metadata->operation_type != M68K_SIM_OP_DBCC && state->sr_known != 0U &&
      sim_condition_true(metadata->condition_code, state->sr)) {
    out_result->stops_fallthrough = 1;
  } else if (!out_result->stops_fallthrough) {
    out_result->stops_fallthrough = metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
      metadata->flow_kind == M68K_SIM_FLOW_RETURN;
  }
  return 0;
}

int m68k_simulate_step(const M68kObject *object, size_t section_index, const M68kSection *section, uint32_t offset,
    const M68kInstructionIR *instruction, const M68kSimCpuState *state, M68kSimStepResult *out_result) {
  return m68k_simulate_step_with_memory(object, section_index, section, offset, instruction, state, NULL, out_result);
}

int m68k_simulate_step_concrete(const M68kInstructionIR *instruction, uint8_t target_cpu,
    const uint8_t *code, size_t code_size, uint8_t *memory, size_t memory_size, M68kSimConcreteState *io_state,
    M68kDiagSink diagnostics) {
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *source, *dest, *target;
  uint32_t immediate_value = 0U, resolved_value = 0U, resolved_address = 0U, current_address = 0U;
  uint8_t is_address, lhs_is_address, lhs_reg, rhs_is_address, rhs_reg;
  uint8_t aux_operand_index;
  if (io_state == NULL) {
    sim_diag_error(diagnostics, "bad arguments");
    return -1;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) {
    m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SIMULATION_FAILED, "missing simulator metadata for %s",
      m68k_ir_instruction_mnemonic_name(instruction));
    return -1;
  }
  source = metadata->source_operand_index != 0xFFU && metadata->source_operand_index < instruction->operand_count
    ? &instruction->operands[metadata->source_operand_index] : NULL;
  dest = metadata->dest_operand_index != 0xFFU && metadata->dest_operand_index < instruction->operand_count
    ? &instruction->operands[metadata->dest_operand_index] : NULL;
  target = metadata->target_operand_index != 0xFFU && metadata->target_operand_index < instruction->operand_count
    ? &instruction->operands[metadata->target_operand_index] : NULL;
  if (metadata->exception_trigger == M68K_SIM_EXCEPTION_TRIGGER_ALWAYS) {
    return sim_concrete_enter_exception(instruction, metadata, NULL, target_cpu, memory, memory_size, io_state,
      diagnostics) ? 0 : -1;
  }
  if (metadata->exception_trigger == M68K_SIM_EXCEPTION_TRIGGER_IF_USER_MODE &&
      (io_state->sr & 0x2000U) == 0U) {
    return sim_concrete_enter_exception(instruction, metadata, NULL, target_cpu, memory, memory_size, io_state,
      diagnostics) ? 0 : -1;
  }
  if (metadata->operation_type == M68K_SIM_OP_MOVE && instruction->operand_count == 2U &&
      source != NULL && dest != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
        memory, memory_size, io_state->pc, &immediate_value) &&
      sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index, dest, &is_address, &lhs_reg) && !is_address) {
    io_state->d[lhs_reg] = immediate_value;
  } else if (metadata->operation_class == M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS &&
      source != NULL && dest != NULL &&
      sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index, dest, &is_address, &lhs_reg) && is_address) {
    if (!sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
          memory, memory_size, io_state->pc, &resolved_address)) {
      sim_diag_error(diagnostics, "unsupported concrete effective address");
      return -1;
    }
    io_state->a[lhs_reg] = resolved_address;
  } else if ((metadata->operation_type == M68K_SIM_OP_ADD || metadata->operation_type == M68K_SIM_OP_SUB) &&
      source != NULL && dest != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
        memory, memory_size, io_state->pc, &immediate_value) &&
      sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index, dest, &is_address, &lhs_reg)) {
    uint32_t delta = immediate_value == 0U ? 8U : immediate_value;
    if (metadata->operation_type == M68K_SIM_OP_SUB) delta = (uint32_t)(0U - delta);
    if (is_address) io_state->a[lhs_reg] += delta; else io_state->d[lhs_reg] += delta;
  } else if ((metadata->operation_type == M68K_SIM_OP_LOGIC_AND || metadata->operation_type == M68K_SIM_OP_LOGIC_OR ||
          metadata->operation_type == M68K_SIM_OP_LOGIC_XOR) &&
      source != NULL && dest != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
        memory, memory_size, io_state->pc, &immediate_value) &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest, io_state,
        memory, memory_size, io_state->pc, &resolved_value)) {
    uint32_t written_value;
    if (metadata->operation_type == M68K_SIM_OP_LOGIC_AND) written_value = resolved_value & immediate_value;
    else if (metadata->operation_type == M68K_SIM_OP_LOGIC_OR) written_value = resolved_value | immediate_value;
    else written_value = resolved_value ^ immediate_value;
    sim_apply_abstract_nz_flags(io_state->sr, written_value,
      sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), &io_state->sr);
    if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest,
          io_state, memory, memory_size, io_state->pc, written_value)) {
      sim_diag_error(diagnostics, "unsupported concrete logic destination");
      return -1;
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_NEGATE || metadata->operation_type == M68K_SIM_OP_NOT ||
          metadata->operation_type == M68K_SIM_OP_SIGN_EXTEND || metadata->operation_type == M68K_SIM_OP_SWAP_WORDS) &&
      dest != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest, io_state,
        memory, memory_size, io_state->pc, &resolved_value)) {
    M68kSimValue input_value;
    M68kSimValue output_value;
    uint8_t write_width = sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index);
    input_value = sim_value_constant(resolved_value, M68K_SIM_PROV_REGISTER_COPY);
    if (!sim_apply_unary(metadata->operation_type, instruction, metadata, &input_value, &output_value)) {
      sim_diag_error(diagnostics, "unsupported concrete unary destination");
      return -1;
    }
    if (metadata->operation_type == M68K_SIM_OP_NEGATE) {
      sim_apply_abstract_compare_test_flags(io_state->sr, resolved_value, 0U,
        sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), 1U, &io_state->sr);
      sim_sync_extend_with_carry(&io_state->sr);
    } else {
      sim_apply_abstract_nz_flags(io_state->sr, output_value.value,
        sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), &io_state->sr);
    }
    if (sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index, dest, &is_address, &lhs_reg)) {
      uint32_t merged_value = output_value.value;
      if (write_width == 1U) merged_value = (resolved_value & 0xFFFFFF00U) | (output_value.value & 0xFFU);
      else if (write_width == 2U && !is_address) merged_value = (resolved_value & 0xFFFF0000U) | (output_value.value & 0xFFFFU);
      if (!sim_concrete_write_register(io_state, dest, merged_value)) {
        sim_diag_error(diagnostics, "unsupported concrete unary destination");
        return -1;
      }
    } else if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest,
          io_state, memory, memory_size, io_state->pc, output_value.value)) {
      sim_diag_error(diagnostics, "unsupported concrete unary destination");
      return -1;
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_SHIFT || metadata->operation_type == M68K_SIM_OP_ROTATE ||
          metadata->operation_type == M68K_SIM_OP_ROTATE_EXTEND) &&
      dest != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest, io_state,
        memory, memory_size, io_state->pc, &resolved_value) &&
      (metadata->shift_count_source != M68K_SIM_SHIFT_COUNT_OPERAND ||
        (source != NULL && sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
          memory, memory_size, io_state->pc, &immediate_value)))) {
    M68kSimValue input_value;
    M68kSimValue count_input;
    M68kSimValue output_value;
    uint8_t write_width = sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index);
    input_value = sim_value_constant(resolved_value, M68K_SIM_PROV_REGISTER_COPY);
    count_input = sim_value_constant(immediate_value, M68K_SIM_PROV_IMMEDIATE);
    if (!sim_apply_shift_rotate(metadata->operation_type, instruction, metadata, &input_value,
          metadata->shift_count_source == M68K_SIM_SHIFT_COUNT_OPERAND ? &count_input : NULL,
          io_state->sr, &output_value, &io_state->sr)) {
      sim_diag_error(diagnostics, "unsupported concrete shift/rotate");
      return -1;
    }
    if (sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index, dest, &is_address, &lhs_reg)) {
      uint32_t merged_value = output_value.value;
      if (write_width == 1U) merged_value = (resolved_value & 0xFFFFFF00U) | (output_value.value & 0xFFU);
      else if (write_width == 2U && !is_address) merged_value = (resolved_value & 0xFFFF0000U) | (output_value.value & 0xFFFFU);
      if (!sim_concrete_write_register(io_state, dest, merged_value)) {
        sim_diag_error(diagnostics, "unsupported concrete shift/rotate");
        return -1;
      }
    } else if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest,
          io_state, memory, memory_size, io_state->pc, output_value.value)) {
      sim_diag_error(diagnostics, "unsupported concrete shift/rotate");
      return -1;
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_COMPARE || metadata->operation_type == M68K_SIM_OP_TEST) &&
      source != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
        memory, memory_size, io_state->pc, &resolved_value)) {
    if (metadata->operation_type == M68K_SIM_OP_COMPARE && dest != NULL &&
        !sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest, io_state,
          memory, memory_size, io_state->pc, &resolved_address)) {
      sim_diag_error(diagnostics, "unsupported concrete compare destination");
      return -1;
    }
    if (!sim_apply_concrete_ea_register_update(instruction, metadata, metadata->source_operand_index, source, io_state)) {
      sim_diag_error(diagnostics, "unsupported concrete compare source update");
      return -1;
    }
    if (metadata->operation_type == M68K_SIM_OP_COMPARE && dest != NULL &&
        !sim_apply_concrete_ea_register_update(instruction, metadata, metadata->dest_operand_index, dest, io_state)) {
      sim_diag_error(diagnostics, "unsupported concrete compare destination update");
      return -1;
    }
    if (metadata->operation_type == M68K_SIM_OP_COMPARE && dest != NULL) {
      sim_apply_abstract_compare_test_flags(io_state->sr, resolved_value, resolved_address,
        sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), 1U, &io_state->sr);
    } else {
      sim_apply_abstract_compare_test_flags(io_state->sr, resolved_value, 0U,
        sim_effective_operand_width(instruction, metadata, metadata->source_operand_index), 0U, &io_state->sr);
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_MULTIPLY || metadata->operation_type == M68K_SIM_OP_DIVIDE) &&
      source != NULL && dest != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
        memory, memory_size, io_state->pc, &resolved_value) &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest, io_state,
        memory, memory_size, io_state->pc, &resolved_address)) {
    uint32_t result_value;
    int ok;
    uint8_t overflow = 0U;
    ok = metadata->operation_type == M68K_SIM_OP_MULTIPLY
      ? (metadata->numeric_is_signed
          ? sim_apply_signed_multiply(resolved_address, resolved_value, &result_value)
          : sim_apply_unsigned_multiply(resolved_address, resolved_value, &result_value))
      : (metadata->numeric_is_signed
          ? sim_apply_signed_divide_status(resolved_address, resolved_value, &result_value, &overflow)
          : sim_apply_unsigned_divide_status(resolved_address, resolved_value, &result_value, &overflow));
    if (!ok) {
      sim_diag_error(diagnostics, "unsupported concrete multiply/divide");
      return -1;
    }
    if (metadata->operation_type == M68K_SIM_OP_DIVIDE) {
      uint16_t next_sr;
      uint16_t quotient = overflow ? (uint16_t)(resolved_address & 0xFFFFU) : (uint16_t)(result_value & 0xFFFFU);
      sim_update_sr_nzvc(io_state->sr,
        metadata->numeric_is_signed && !overflow && (quotient & 0x8000U) != 0U,
        !overflow && quotient == 0U, overflow, 0U, &next_sr);
      io_state->sr = next_sr;
    } else {
      sim_apply_abstract_nz_flags(io_state->sr, result_value,
        sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), &io_state->sr);
    }
    if (!overflow) {
      if (sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index, dest, &is_address, &lhs_reg) &&
          !is_address) {
        io_state->d[lhs_reg] = result_value;
      } else if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest,
            io_state, memory, memory_size, io_state->pc, result_value)) {
        sim_diag_error(diagnostics, "unsupported concrete multiply/divide");
        return -1;
      }
    }
  } else if (metadata->operation_type == M68K_SIM_OP_BOUNDS_CHECK &&
      source != NULL && dest != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
        memory, memory_size, io_state->pc, &resolved_value) &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest, io_state,
        memory, memory_size, io_state->pc, &resolved_address)) {
    uint8_t bounds_width = sim_effective_operand_width(instruction, metadata, metadata->source_operand_index);
    uint32_t low = 0U;
    uint32_t high = resolved_value;
    uint16_t prior_sr = io_state->sr;
    int in_range = 1;
    if (metadata->bounds_mode == M68K_SIM_BOUNDS_LOWER_UPPER_PAIR) {
      if (!sim_concrete_compute_ea_address(source,
            metadata->operand_ea_address_formulas[metadata->source_operand_index],
            metadata->operand_ea_address_shapes[metadata->source_operand_index],
            metadata->operand_ea_base_kinds[metadata->source_operand_index],
            metadata->operand_ea_displacement_sources[metadata->source_operand_index],
            metadata->operand_ea_uses_displacement[metadata->source_operand_index],
            metadata->operand_ea_uses_index[metadata->source_operand_index],
            metadata->operand_ea_pc_base_bias_bytes[metadata->source_operand_index],
            metadata->operand_ea_address_literal_width_bytes[metadata->source_operand_index],
            metadata->operand_ea_index_extension_formats[metadata->source_operand_index],
            metadata->operand_ea_index_register_classes[metadata->source_operand_index],
            metadata->operand_ea_index_value_width_sources[metadata->source_operand_index],
            metadata->operand_ea_index_scale_sources[metadata->source_operand_index],
            metadata->operand_ea_index_sign_sources[metadata->source_operand_index],
            io_state, io_state->pc, &current_address) ||
          !sim_concrete_read_memory_sized(memory, memory_size, current_address, bounds_width, &low) ||
          !sim_concrete_read_memory_sized(memory, memory_size, current_address + bounds_width, bounds_width, &high)) {
        sim_diag_error(diagnostics, "unsupported concrete bounds source");
        return -1;
      }
      in_range = sim_value_in_bounds(resolved_address, low, high, bounds_width, metadata->numeric_is_signed);
      sim_update_sr_nzvc(io_state->sr, 0U, 0U, 0U, in_range ? 0U : 1U, &io_state->sr);
    } else {
      in_range = sim_value_in_bounds(resolved_address, 0U, high, bounds_width, metadata->numeric_is_signed);
      sim_update_sr_nzvc(io_state->sr, 0U, 0U, 0U, in_range ? 0U : 1U, &io_state->sr);
    }
    if (metadata->bounds_trap_on_fail && !in_range) {
      const uint16_t *saved_sr_override =
        metadata->exception_stacked_sr_source == M68K_SIM_EXCEPTION_STACKED_SR_UPDATED_FLAGS ? NULL : &prior_sr;
      return sim_concrete_enter_exception(instruction, metadata, saved_sr_override, target_cpu, memory, memory_size, io_state,
        diagnostics) ? 0 : -1;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_COMPARE_SWAP && instruction->operand_count >= 3U) {
    uint32_t compare_value, update_value, current_value, mask;
    uint8_t width;
    if (instruction->operands[0].kind == M68K_ASM_OPERAND_DN_PAIR &&
        instruction->operands[1].kind == M68K_ASM_OPERAND_DN_PAIR &&
        instruction->operands[metadata->dest_operand_index].kind == M68K_ASM_OPERAND_RN_PAIR) {
      const M68kAsmOperandValue *compare_pair = &instruction->operands[0].value;
      const M68kAsmOperandValue *update_pair = &instruction->operands[1].value;
      const M68kAsmOperandValue *dest_pair = &instruction->operands[metadata->dest_operand_index].value;
      uint32_t compare1, compare2, update1, update2;
      uint32_t current1, current2, addr1, addr2;
      width = sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index);
      mask = sim_mask_for_width(width);
      if (compare_pair->reg >= 8U || compare_pair->pair_reg >= 8U ||
          update_pair->reg >= 8U || update_pair->pair_reg >= 8U ||
          !dest_pair->reg_is_address || !dest_pair->pair_reg_is_address ||
          dest_pair->reg >= 8U || dest_pair->pair_reg >= 8U) {
        sim_diag_error(diagnostics, "unsupported concrete compare-swap");
        return -1;
      }
      compare1 = io_state->d[compare_pair->reg] & mask;
      compare2 = io_state->d[compare_pair->pair_reg] & mask;
      update1 = io_state->d[update_pair->reg];
      update2 = io_state->d[update_pair->pair_reg];
      addr1 = io_state->a[dest_pair->reg];
      addr2 = io_state->a[dest_pair->pair_reg];
      if (!sim_concrete_read_memory_sized(memory, memory_size, addr1, width, &current1) ||
          !sim_concrete_read_memory_sized(memory, memory_size, addr2, width, &current2)) {
        sim_diag_error(diagnostics, "unsupported concrete compare-swap");
        return -1;
      }
      if (sim_apply_abstract_compare_test_flags(io_state->sr, compare1, current1, width, 1U, &io_state->sr)) {
        if ((current1 & mask) == compare1 && (current2 & mask) == compare2) {
          io_state->sr = (uint16_t)(io_state->sr | (1U << g_m68k_sim_ccr_bit_z));
        } else {
          io_state->sr = (uint16_t)(io_state->sr & ~(1U << g_m68k_sim_ccr_bit_z));
        }
      }
      if ((current1 & mask) == compare1 && (current2 & mask) == compare2) {
        if (!sim_concrete_write_memory_sized(memory, memory_size, addr1, update1, width) ||
            !sim_concrete_write_memory_sized(memory, memory_size, addr2, update2, width)) {
          sim_diag_error(diagnostics, "unsupported concrete compare-swap destination");
          return -1;
        }
      } else {
        if (width == 1U) {
          io_state->d[compare_pair->reg] = (io_state->d[compare_pair->reg] & 0xFFFFFF00U) | (current1 & 0xFFU);
          io_state->d[compare_pair->pair_reg] = (io_state->d[compare_pair->pair_reg] & 0xFFFFFF00U) | (current2 & 0xFFU);
        } else if (width == 2U) {
          io_state->d[compare_pair->reg] = (io_state->d[compare_pair->reg] & 0xFFFF0000U) | (current1 & 0xFFFFU);
          io_state->d[compare_pair->pair_reg] = (io_state->d[compare_pair->pair_reg] & 0xFFFF0000U) | (current2 & 0xFFFFU);
        } else {
          io_state->d[compare_pair->reg] = current1;
          io_state->d[compare_pair->pair_reg] = current2;
        }
      }
    } else {
      if (source == NULL || instruction->operand_count < 3U ||
          !sim_concrete_eval_operand_by_metadata(instruction, metadata, 0U, &instruction->operands[0], io_state,
            memory, memory_size, io_state->pc, &compare_value) ||
          !sim_concrete_eval_operand_by_metadata(instruction, metadata, 1U, &instruction->operands[1], io_state,
            memory, memory_size, io_state->pc, &update_value)) {
        sim_diag_error(diagnostics, "unsupported concrete compare-swap");
        return -1;
      }
      width = sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index);
      if (sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index,
          &instruction->operands[metadata->dest_operand_index], &is_address, &lhs_reg)) {
        if (!sim_concrete_read_register(io_state, is_address, lhs_reg, &current_value)) {
          sim_diag_error(diagnostics, "unsupported concrete compare-swap");
          return -1;
        }
      } else if (!sim_concrete_compute_ea_address(&instruction->operands[metadata->dest_operand_index],
          metadata->operand_ea_address_formulas[metadata->dest_operand_index],
          metadata->operand_ea_address_shapes[metadata->dest_operand_index],
          metadata->operand_ea_base_kinds[metadata->dest_operand_index],
          metadata->operand_ea_displacement_sources[metadata->dest_operand_index],
          metadata->operand_ea_uses_displacement[metadata->dest_operand_index],
          metadata->operand_ea_uses_index[metadata->dest_operand_index],
          metadata->operand_ea_pc_base_bias_bytes[metadata->dest_operand_index],
          metadata->operand_ea_address_literal_width_bytes[metadata->dest_operand_index],
          metadata->operand_ea_index_extension_formats[metadata->dest_operand_index],
          metadata->operand_ea_index_register_classes[metadata->dest_operand_index],
          metadata->operand_ea_index_value_width_sources[metadata->dest_operand_index],
          metadata->operand_ea_index_scale_sources[metadata->dest_operand_index],
          metadata->operand_ea_index_sign_sources[metadata->dest_operand_index],
          io_state, io_state->pc, &current_address) ||
          !sim_concrete_read_memory_sized(memory, memory_size, current_address, width, &current_value)) {
        sim_diag_error(diagnostics, "unsupported concrete compare-swap");
        return -1;
      }
      mask = sim_mask_for_width(sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index));
      if (sim_apply_abstract_compare_test_flags(io_state->sr, compare_value, current_value, width, 1U, &io_state->sr)) {
        if ((current_value & mask) == (compare_value & mask)) {
          io_state->sr = (uint16_t)(io_state->sr | (1U << g_m68k_sim_ccr_bit_z));
        } else {
          io_state->sr = (uint16_t)(io_state->sr & ~(1U << g_m68k_sim_ccr_bit_z));
        }
      }
      if ((current_value & mask) == (compare_value & mask)) {
        if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index,
              &instruction->operands[metadata->dest_operand_index], io_state, memory, memory_size, io_state->pc,
              update_value)) {
          sim_diag_error(diagnostics, "unsupported concrete compare-swap destination");
          return -1;
        }
      } else if (!sim_concrete_write_operand_by_metadata(instruction, metadata, 0U, &instruction->operands[0],
            io_state, memory, memory_size, io_state->pc, current_value)) {
        sim_diag_error(diagnostics, "unsupported concrete compare-swap compare register");
        return -1;
      }
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_BITFIELD_CHANGE ||
      metadata->operation_type == M68K_SIM_OP_BITFIELD_CLEAR ||
      metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED ||
      metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED ||
      metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE ||
      metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT ||
      metadata->operation_type == M68K_SIM_OP_BITFIELD_SET ||
      metadata->operation_type == M68K_SIM_OP_BITFIELD_TEST) &&
      metadata->source_operand_index < instruction->operand_count) {
    const M68kOperandIR *bf_operand = &instruction->operands[metadata->source_operand_index];
    uint8_t bf_reg;
    uint32_t bf_offset, bf_width, field_value, updated_bits, field_mask;
    if (metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT &&
        metadata->dest_operand_index < instruction->operand_count) {
      bf_operand = &instruction->operands[metadata->dest_operand_index];
    }
    if (!sim_bitfield_resolve_spec_concrete(&bf_operand->value, io_state, &bf_offset, &bf_width)) {
      sim_diag_error(diagnostics, "unsupported concrete bitfield");
      return -1;
    }
    field_mask = sim_bitfield_mask(bf_width);
    if (sim_bitfield_is_direct_data_register(bf_operand, &bf_reg)) {
      field_value = sim_bitfield_extract_from_register(io_state->d[bf_reg], bf_offset, bf_width);
      sim_apply_bitfield_nz_flags(io_state->sr, field_value, bf_width, &io_state->sr);
      if (metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE) {
        uint32_t written = field_value;
        if (metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED && bf_width < 32U) {
          written = sim_sign_extend_value(field_value, (uint8_t)bf_width);
        } else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE) {
          written = bf_offset + sim_bitfield_find_first_one(field_value, bf_width);
        }
        if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index,
              &instruction->operands[metadata->dest_operand_index], io_state, memory, memory_size, io_state->pc,
              written)) {
          sim_diag_error(diagnostics, "unsupported concrete bitfield destination");
          return -1;
        }
      } else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CHANGE ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_CLEAR ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT ||
          metadata->operation_type == M68K_SIM_OP_BITFIELD_SET) {
        if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CHANGE) updated_bits = field_value ^ field_mask;
        else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CLEAR) updated_bits = 0U;
        else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_SET) updated_bits = field_mask;
        else if (!sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index,
              &instruction->operands[metadata->source_operand_index], io_state, memory, memory_size, io_state->pc,
              &updated_bits)) {
          sim_diag_error(diagnostics, "unsupported concrete bitfield source");
          return -1;
        } else {
          updated_bits &= field_mask;
        }
        io_state->d[bf_reg] = sim_bitfield_insert_into_register(io_state->d[bf_reg], bf_offset, bf_width, updated_bits);
      }
    } else {
      M68kOperandIR ea_operand = *bf_operand;
      ea_operand.kind = M68K_ASM_OPERAND_EA;
      if (!sim_concrete_compute_ea_address(&ea_operand,
          metadata->operand_ea_address_formulas[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_address_shapes[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_base_kinds[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_displacement_sources[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_uses_displacement[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_uses_index[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_pc_base_bias_bytes[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_address_literal_width_bytes[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_index_extension_formats[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_index_register_classes[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_index_value_width_sources[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_index_scale_sources[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          metadata->operand_ea_index_sign_sources[metadata->operation_type == M68K_SIM_OP_BITFIELD_INSERT
            ? metadata->dest_operand_index : metadata->source_operand_index],
          io_state, io_state->pc, &resolved_address) ||
          !sim_concrete_read_memory_bitfield(memory, memory_size, resolved_address, bf_offset, bf_width, &field_value)) {
        sim_diag_error(diagnostics, "unsupported concrete bitfield");
        return -1;
      }
    sim_apply_bitfield_nz_flags(io_state->sr, field_value, bf_width, &io_state->sr);
    if (metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED ||
        metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED ||
        metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE) {
      uint32_t written = field_value;
      if (metadata->operation_type == M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED && bf_width < 32U) {
        written = sim_sign_extend_value(field_value, (uint8_t)bf_width);
      } else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE) {
        written = bf_offset + sim_bitfield_find_first_one(field_value, bf_width);
      }
      if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index,
            &instruction->operands[metadata->dest_operand_index], io_state, memory, memory_size, io_state->pc,
            written)) {
        sim_diag_error(diagnostics, "unsupported concrete bitfield destination");
        return -1;
      }
    } else {
      if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CHANGE) updated_bits = field_value ^ field_mask;
      else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_CLEAR) updated_bits = 0U;
      else if (metadata->operation_type == M68K_SIM_OP_BITFIELD_SET) updated_bits = field_mask;
      else if (!sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index,
            &instruction->operands[metadata->source_operand_index], io_state, memory, memory_size, io_state->pc,
            &updated_bits)) {
        sim_diag_error(diagnostics, "unsupported concrete bitfield source");
        return -1;
      } else {
        updated_bits &= field_mask;
      }
      if (!sim_concrete_write_memory_bitfield(memory, memory_size, resolved_address, bf_offset, bf_width, updated_bits)) {
        sim_diag_error(diagnostics, "unsupported concrete bitfield destination");
        return -1;
      }
    }
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_PACK || metadata->operation_type == M68K_SIM_OP_UNPACK) &&
      source != NULL && dest != NULL && instruction->operand_count >= 3U) {
    uint32_t source_value;
    uint32_t dest_value;
    uint16_t adjustment;
    const M68kOperandIR *adjust_operand = &instruction->operands[2];
    if (!sim_concrete_eval_operand_by_metadata(instruction, metadata, 2U, adjust_operand, io_state,
          memory, memory_size, io_state->pc, &immediate_value)) {
      sim_diag_error(diagnostics, "unsupported concrete pack adjustment");
      return -1;
    }
    adjustment = (uint16_t)immediate_value;
    if (metadata->operand_ea_register_updates[metadata->source_operand_index] == M68K_SIM_EA_UPDATE_PREDECREMENT) {
      if (!sim_concrete_apply_predecrement_operand(instruction, metadata, metadata->source_operand_index, source,
            io_state, &resolved_address) ||
          !sim_concrete_read_memory_sized(memory, memory_size, resolved_address,
            sim_effective_operand_width(instruction, metadata, metadata->source_operand_index), &source_value)) {
        sim_diag_error(diagnostics, "unsupported concrete pack source");
        return -1;
      }
    } else if (!sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
          memory, memory_size, io_state->pc, &source_value)) {
      sim_diag_error(diagnostics, "unsupported concrete pack source");
      return -1;
    }
    dest_value = metadata->operation_type == M68K_SIM_OP_PACK
      ? sim_pack_value(source_value, adjustment)
      : sim_unpack_value(source_value, adjustment);
    if (metadata->operand_ea_register_updates[metadata->dest_operand_index] == M68K_SIM_EA_UPDATE_PREDECREMENT) {
      if (!sim_concrete_apply_predecrement_operand(instruction, metadata, metadata->dest_operand_index, dest,
            io_state, &resolved_address) ||
          !sim_concrete_write_memory_sized(memory, memory_size, resolved_address, dest_value,
            sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index))) {
        sim_diag_error(diagnostics, "unsupported concrete pack destination");
        return -1;
      }
    } else if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest,
          io_state, memory, memory_size, io_state->pc, dest_value)) {
      sim_diag_error(diagnostics, "unsupported concrete pack destination");
      return -1;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_TEST_AND_SET && source != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
        memory, memory_size, io_state->pc, &resolved_value)) {
    sim_apply_abstract_nz_flags(io_state->sr, resolved_value, 1U, &io_state->sr);
    uint32_t written_value = resolved_value | 0x80U;
    if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source,
          io_state, memory, memory_size, io_state->pc, written_value)) {
      sim_diag_error(diagnostics, "unsupported concrete tas destination");
      return -1;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_MOVE_PERIPHERAL && instruction->operand_count >= 2U) {
    uint8_t reg_index = metadata->striped_reg_operand_index;
    uint8_t address_index = metadata->striped_address_operand_index;
    uint8_t width = sim_operand_width_from_instruction(instruction);
    const M68kOperandIR *reg_operand;
    const M68kOperandIR *address_operand;
    if (reg_index >= instruction->operand_count || address_index >= instruction->operand_count) {
      sim_diag_error(diagnostics, "unsupported concrete movep metadata");
      return -1;
    }
    reg_operand = &instruction->operands[reg_index];
    address_operand = &instruction->operands[address_index];
    if (!sim_concrete_compute_ea_address(address_operand, metadata->operand_ea_address_formulas[address_index],
          metadata->operand_ea_address_shapes[address_index], metadata->operand_ea_base_kinds[address_index],
          metadata->operand_ea_displacement_sources[address_index],
          metadata->operand_ea_uses_displacement[address_index], metadata->operand_ea_uses_index[address_index],
          metadata->operand_ea_pc_base_bias_bytes[address_index],
          metadata->operand_ea_address_literal_width_bytes[address_index],
          metadata->operand_ea_index_extension_formats[address_index],
          metadata->operand_ea_index_register_classes[address_index],
          metadata->operand_ea_index_value_width_sources[address_index],
          metadata->operand_ea_index_scale_sources[address_index],
          metadata->operand_ea_index_sign_sources[address_index],
          io_state, io_state->pc, &resolved_address)) {
      sim_diag_error(diagnostics, "unsupported concrete movep address");
      return -1;
    }
    if (metadata->striped_direction == M68K_SIM_STRIPED_REGISTER_TO_MEMORY) {
      uint8_t byte_index;
      if (!sim_concrete_eval_operand_by_metadata(instruction, metadata, reg_index, reg_operand, io_state,
            memory, memory_size, io_state->pc, &resolved_value)) {
        sim_diag_error(diagnostics, "unsupported concrete movep register");
        return -1;
      }
      for (byte_index = 0U; byte_index < width; ++byte_index) {
        uint32_t byte_address = sim_striped_transfer_byte_address(resolved_address, metadata->striped_stride, byte_index);
        uint8_t shift = (uint8_t)(8U * (width - 1U - byte_index));
        if (!sim_concrete_write_memory_sized(memory, memory_size, byte_address, (resolved_value >> shift) & 0xFFU, 1U)) {
          sim_diag_error(diagnostics, "movep write out of range");
          return -1;
        }
      }
    } else if (metadata->striped_direction == M68K_SIM_STRIPED_MEMORY_TO_REGISTER) {
      uint32_t combined = 0U;
      uint8_t byte_index;
      for (byte_index = 0U; byte_index < width; ++byte_index) {
        uint32_t byte_address = sim_striped_transfer_byte_address(resolved_address, metadata->striped_stride, byte_index);
        if (memory == NULL || byte_address >= memory_size) {
          sim_diag_error(diagnostics, "movep read out of range");
          return -1;
        }
        combined = (combined << 8) | memory[byte_address];
      }
      if (!sim_concrete_write_operand_by_metadata(instruction, metadata, reg_index, reg_operand,
            io_state, memory, memory_size, io_state->pc, combined)) {
        sim_diag_error(diagnostics, "unsupported concrete movep destination");
        return -1;
      }
    } else {
      sim_diag_error(diagnostics, "unsupported concrete movep direction");
      return -1;
    }
  } else if ((metadata->operation_type == M68K_SIM_OP_BIT_TEST || metadata->operation_type == M68K_SIM_OP_BIT_SET ||
          metadata->operation_type == M68K_SIM_OP_BIT_CLEAR || metadata->operation_type == M68K_SIM_OP_BIT_CHANGE) &&
      source != NULL && dest != NULL &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
        memory, memory_size, io_state->pc, &resolved_value) &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest, io_state,
        memory, memory_size, io_state->pc, &resolved_address)) {
    uint8_t width = sim_bit_width_for_metadata_operand(metadata, metadata->dest_operand_index, dest);
    uint32_t modulus = width >= 4U ? 32U : 8U;
    uint32_t mask = 1U << (resolved_value % modulus);
    uint32_t written_value = resolved_address;
    uint16_t next_sr = (uint16_t)(io_state->sr & ~(1U << g_m68k_sim_ccr_bit_z));
    if ((resolved_address & mask) == 0U) next_sr = (uint16_t)(next_sr | (1U << g_m68k_sim_ccr_bit_z));
    io_state->sr = next_sr;
    if (metadata->operation_type == M68K_SIM_OP_BIT_SET) written_value = resolved_address | mask;
    else if (metadata->operation_type == M68K_SIM_OP_BIT_CLEAR) written_value = resolved_address & ~mask;
    else if (metadata->operation_type == M68K_SIM_OP_BIT_CHANGE) written_value = resolved_address ^ mask;
    if (metadata->operation_type != M68K_SIM_OP_BIT_TEST &&
        !sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest,
          io_state, memory, memory_size, io_state->pc, written_value)) {
      sim_diag_error(diagnostics, "unsupported concrete bit destination");
      return -1;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_MOVE_MULTIPLE && instruction->operand_count >= 2U) {
    uint8_t width = sim_operand_width_from_instruction(instruction);
    uint8_t reglist_index = metadata->reglist_operand_index;
    uint8_t address_index = metadata->address_operand_index;
    const M68kOperandIR *address_operand;
    if (reglist_index >= instruction->operand_count || address_index >= instruction->operand_count) {
      sim_diag_error(diagnostics, "unsupported concrete movem metadata");
      return -1;
    }
    address_operand = &instruction->operands[address_index];
    if (metadata->multi_transfer_direction == M68K_SIM_MULTI_REGISTER_TO_MEMORY) {
      uint32_t address;
        uint32_t cursor;
        uint16_t mask = (uint16_t)instruction->operands[reglist_index].value.value;
        uint8_t address_reg;
        uint8_t address_shape = sim_effective_ea_shape(metadata->operand_ea_address_shapes[address_index], address_operand);
        int is_predecrement = sim_multi_transfer_uses_predecrement(metadata->multi_transfer_address_update,
          metadata->operand_ea_register_updates[address_index], address_shape);
        M68kSimConcreteState source_state = *io_state;
        const M68kSimConcreteState *read_state = sim_multi_transfer_source_state(
          metadata->multi_transfer_source_snapshot, io_state, &source_state);
        if (!sim_ea_address_register(address_shape, address_operand, &address_reg)) {
          sim_diag_error(diagnostics, "unsupported concrete movem address register");
          return -1;
        }
        if (
            !sim_concrete_compute_ea_address(address_operand, metadata->operand_ea_address_formulas[address_index],
              metadata->operand_ea_address_shapes[address_index], metadata->operand_ea_base_kinds[address_index],
            metadata->operand_ea_displacement_sources[address_index],
            metadata->operand_ea_uses_displacement[address_index], metadata->operand_ea_uses_index[address_index],
            metadata->operand_ea_pc_base_bias_bytes[address_index],
            metadata->operand_ea_address_literal_width_bytes[address_index],
            metadata->operand_ea_index_extension_formats[address_index],
            metadata->operand_ea_index_register_classes[address_index],
            metadata->operand_ea_index_value_width_sources[address_index],
            metadata->operand_ea_index_scale_sources[address_index],
            metadata->operand_ea_index_sign_sources[address_index],
            io_state, io_state->pc, &address)) {
        sim_diag_error(diagnostics, "unsupported concrete movem destination");
        return -1;
      }
      cursor = address;
      if (is_predecrement) {
        cursor -= (uint32_t)width * (uint32_t)sim_reglist_count(mask);
        io_state->a[address_reg] = cursor;
      }
      for (lhs_reg = 0U; lhs_reg < 16U; ++lhs_reg) {
        uint8_t reg_is_address;
        uint8_t reg_index;
        uint32_t reg_value;
        if (!sim_multi_transfer_includes_slot(metadata->multi_transfer_reg_iteration, mask, lhs_reg)) continue;
        if (!sim_reglist_slot(lhs_reg, &reg_is_address, &reg_index) ||
            !sim_concrete_read_register(read_state, reg_is_address, reg_index, &reg_value) ||
            !sim_concrete_write_memory_sized(memory, memory_size, cursor, reg_value, width)) {
          sim_diag_error(diagnostics, "unsupported concrete movem store");
          return -1;
        }
        cursor += width;
      }
    } else if (metadata->multi_transfer_direction == M68K_SIM_MULTI_MEMORY_TO_REGISTER) {
        uint32_t address;
        uint32_t cursor;
        uint16_t mask = (uint16_t)instruction->operands[reglist_index].value.value;
        uint8_t address_reg;
        uint8_t address_shape = sim_effective_ea_shape(metadata->operand_ea_address_shapes[address_index], address_operand);
        int is_postincrement = sim_multi_transfer_uses_postincrement(metadata->multi_transfer_address_update,
          metadata->operand_ea_register_updates[address_index], address_shape);
        if (!sim_ea_address_register(address_shape, address_operand, &address_reg)) {
          sim_diag_error(diagnostics, "unsupported concrete movem address register");
          return -1;
        }
        if (
            !sim_concrete_compute_ea_address(address_operand, metadata->operand_ea_address_formulas[address_index],
              metadata->operand_ea_address_shapes[address_index], metadata->operand_ea_base_kinds[address_index],
            metadata->operand_ea_displacement_sources[address_index],
            metadata->operand_ea_uses_displacement[address_index], metadata->operand_ea_uses_index[address_index],
            metadata->operand_ea_pc_base_bias_bytes[address_index],
            metadata->operand_ea_address_literal_width_bytes[address_index],
            metadata->operand_ea_index_extension_formats[address_index],
            metadata->operand_ea_index_register_classes[address_index],
            metadata->operand_ea_index_value_width_sources[address_index],
            metadata->operand_ea_index_scale_sources[address_index],
            metadata->operand_ea_index_sign_sources[address_index],
            io_state, io_state->pc, &address)) {
        sim_diag_error(diagnostics, "unsupported concrete movem source");
        return -1;
      }
      cursor = address;
      for (lhs_reg = 0U; lhs_reg < 16U; ++lhs_reg) {
        uint8_t reg_is_address;
        uint8_t reg_index;
        uint32_t reg_value;
        if (!sim_multi_transfer_includes_slot(metadata->multi_transfer_reg_iteration, mask, lhs_reg)) continue;
        if (!sim_reglist_slot(lhs_reg, &reg_is_address, &reg_index)) {
          sim_diag_error(diagnostics, "unsupported concrete movem reglist");
          return -1;
        }
        if (width == 2U) {
          uint16_t word_value;
          if (memory == NULL || cursor + 2U > memory_size) {
            sim_diag_error(diagnostics, "movem read out of range");
            return -1;
          }
          word_value = m68k_read_u16be(memory + cursor);
          reg_value = (uint32_t)(int32_t)(int16_t)word_value;
        } else {
          if (!sim_concrete_read_memory_u32(memory, memory_size, cursor, &reg_value)) {
            sim_diag_error(diagnostics, "movem read out of range");
            return -1;
          }
        }
        sim_concrete_write_register_slot(io_state, reg_is_address, reg_index, reg_value);
        cursor += width;
      }
      if (is_postincrement) io_state->a[address_reg] = cursor;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_PUSH_EA && source != NULL) {
    if (!sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
          memory, memory_size, io_state->pc, &resolved_address)) {
      sim_diag_error(diagnostics, "unsupported concrete pea source");
      return -1;
    }
    if (memory == NULL || io_state->a[7] < 4U || io_state->a[7] > memory_size) {
      sim_diag_error(diagnostics, "stack out of range");
      return -1;
    }
    io_state->a[7] -= 4U;
    if (!sim_concrete_write_memory_sized(memory, memory_size, io_state->a[7], resolved_address, 4U)) {
      sim_diag_error(diagnostics, "stack out of range");
      return -1;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_LINK && source != NULL && instruction->operand_count >= 2U &&
      sim_direct_register_slot_by_metadata(metadata, metadata->source_operand_index, source, &is_address, &lhs_reg) && is_address &&
      (aux_operand_index = sim_find_operand_index_by_access(
        metadata, M68K_SIM_ACCESS_IMMEDIATE, metadata->source_operand_index)) < instruction->operand_count &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, aux_operand_index, &instruction->operands[aux_operand_index], io_state,
        memory, memory_size, io_state->pc, &resolved_value)) {
    int32_t link_delta = 0;
    if (memory == NULL || io_state->a[7] < 4U || io_state->a[7] > memory_size) {
      sim_diag_error(diagnostics, "stack out of range");
      return -1;
    }
    if (!sim_link_displacement_concrete(instruction, resolved_value, &link_delta)) {
      sim_diag_error(diagnostics, "unsupported concrete link displacement");
      return -1;
    }
    io_state->a[7] -= 4U;
    if (!sim_concrete_write_memory_sized(memory, memory_size, io_state->a[7], io_state->a[lhs_reg], 4U)) {
      sim_diag_error(diagnostics, "stack out of range");
      return -1;
    }
    io_state->a[lhs_reg] = io_state->a[7];
    io_state->a[7] = (uint32_t)((int32_t)io_state->a[7] + link_delta);
  } else if (metadata->operation_type == M68K_SIM_OP_UNLK && source != NULL &&
      sim_direct_register_slot_by_metadata(metadata, metadata->source_operand_index, source, &is_address, &lhs_reg) && is_address) {
    io_state->a[7] = io_state->a[lhs_reg];
    if (memory == NULL || io_state->a[7] + 4U > memory_size) {
      sim_diag_error(diagnostics, "stack out of range");
      return -1;
    }
    io_state->a[lhs_reg] = m68k_read_u32be(memory + io_state->a[7]);
    io_state->a[7] += 4U;
  } else if (metadata->operation_type == M68K_SIM_OP_MOVE && source != NULL && dest != NULL) {
    if (!sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->source_operand_index, source, io_state,
          memory, memory_size, io_state->pc, &resolved_value)) {
      sim_diag_error(diagnostics, "unsupported concrete move source");
      return -1;
    }
    if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest,
          io_state, memory, memory_size, io_state->pc, resolved_value)) {
      sim_diag_error(diagnostics, "unsupported concrete move destination");
      return -1;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_CLEAR && dest != NULL) {
    sim_apply_abstract_nz_flags(io_state->sr, 0U,
      sim_effective_operand_width(instruction, metadata, metadata->dest_operand_index), &io_state->sr);
    if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest,
          io_state, memory, memory_size, io_state->pc, 0U)) {
      sim_diag_error(diagnostics, "unsupported concrete clear destination");
      return -1;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_SET_COND && dest != NULL) {
    uint32_t value = sim_condition_true(metadata->condition_code, io_state->sr) ? 0xFFU : 0x00U;
    if (!sim_concrete_write_operand_by_metadata(instruction, metadata, metadata->dest_operand_index, dest,
          io_state, memory, memory_size, io_state->pc, value)) {
      sim_diag_error(diagnostics, "unsupported concrete condition destination");
      return -1;
    }
  } else if (metadata->operation_type == M68K_SIM_OP_DBCC && source != NULL && target != NULL &&
      sim_direct_register_slot_by_metadata(metadata, metadata->source_operand_index, source, &is_address, &lhs_reg) && !is_address &&
      sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->target_operand_index, target, io_state,
        memory, memory_size, io_state->pc, &resolved_address)) {
    uint16_t counter;
    if (sim_condition_true(metadata->condition_code, io_state->sr)) {
      io_state->pc += (uint32_t)instruction->byte_count;
      return 0;
    }
    counter = (uint16_t)((io_state->d[lhs_reg] - 1U) & 0xFFFFU);
    io_state->d[lhs_reg] = (io_state->d[lhs_reg] & 0xFFFF0000U) | (uint32_t)counter;
    if (counter != 0xFFFFU) io_state->pc = resolved_address;
    else io_state->pc += (uint32_t)instruction->byte_count;
    return 0;
  } else if (metadata->operation_type == M68K_SIM_OP_TRAPV) {
    if ((io_state->sr & 0x0002U) == 0U) {
      io_state->pc += (uint32_t)instruction->byte_count;
      return 0;
    }
    return sim_concrete_enter_exception(instruction, metadata, NULL, target_cpu, memory, memory_size, io_state,
      diagnostics) ? 0 : -1;
  } else if (metadata->operation_type == M68K_SIM_OP_SWAP && source != NULL && dest != NULL &&
      sim_direct_register_slot_by_metadata(metadata, metadata->source_operand_index, source, &lhs_is_address, &lhs_reg) &&
      sim_direct_register_slot_by_metadata(metadata, metadata->dest_operand_index, dest, &rhs_is_address, &rhs_reg)) {
    uint32_t lhs_value;
    uint32_t rhs_value;
    if (!sim_concrete_read_register(io_state, lhs_is_address, lhs_reg, &lhs_value) ||
        !sim_concrete_read_register(io_state, rhs_is_address, rhs_reg, &rhs_value) ||
        !sim_concrete_write_register(io_state, source, rhs_value) ||
        !sim_concrete_write_register(io_state, dest, lhs_value)) {
      sim_diag_error(diagnostics, "unsupported concrete register swap");
      return -1;
    }
  } else if (metadata->operation_type != M68K_SIM_OP_NONE &&
      (metadata->flow_kind == M68K_SIM_FLOW_JUMP || metadata->flow_kind == M68K_SIM_FLOW_CALL ||
          metadata->flow_kind == M68K_SIM_FLOW_BRANCH) &&
      target != NULL) {
    if (sim_concrete_eval_operand_by_metadata(instruction, metadata, metadata->target_operand_index, target, io_state,
          memory, memory_size, io_state->pc, &resolved_address)) {
      if (metadata->flow_conditional && !sim_condition_true(metadata->condition_code, io_state->sr)) {
        io_state->pc += (uint32_t)instruction->byte_count;
        return 0;
      }
      if (metadata->flow_kind == M68K_SIM_FLOW_CALL) {
        if (memory == NULL || io_state->a[7] < 4U || io_state->a[7] > memory_size) {
          sim_diag_error(diagnostics, "stack out of range");
          return -1;
        }
        io_state->a[7] -= 4U;
        if (io_state->a[7] + 4U > memory_size) {
          sim_diag_error(diagnostics, "stack out of range");
          return -1;
        }
        memory[io_state->a[7]] = (uint8_t)(((io_state->pc + (uint32_t)instruction->byte_count) >> 24) & 0xFFU);
        memory[io_state->a[7] + 1U] = (uint8_t)(((io_state->pc + (uint32_t)instruction->byte_count) >> 16) & 0xFFU);
        memory[io_state->a[7] + 2U] = (uint8_t)(((io_state->pc + (uint32_t)instruction->byte_count) >> 8) & 0xFFU);
        memory[io_state->a[7] + 3U] = (uint8_t)((io_state->pc + (uint32_t)instruction->byte_count) & 0xFFU);
      }
      io_state->pc = resolved_address;
      return 0;
    }
    sim_diag_error(diagnostics, "unsupported concrete control transfer");
    return -1;
  } else if (metadata->flow_kind == M68K_SIM_FLOW_RETURN) {
    return sim_concrete_return_from_metadata(instruction, metadata, target_cpu, memory, memory_size, io_state,
      diagnostics);
  } else if (sim_set_unsupported_concrete_operation_error(instruction, metadata, diagnostics)) {
    return -1;
  } else {
    (void)code;
    (void)code_size;
    m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SIMULATION_FAILED,
      "unsupported concrete instruction %s op=%u class=%u flow=%u operands=%u/%u",
      m68k_ir_instruction_mnemonic_name(instruction), (unsigned)metadata->operation_type,
      (unsigned)metadata->operation_class, (unsigned)metadata->flow_kind,
      instruction->operand_count != 0U ? (unsigned)instruction->operands[0].kind : 0U,
      instruction->operand_count > 1U ? (unsigned)instruction->operands[1].kind : 0U);
    return -1;
  }
  io_state->pc += (uint32_t)instruction->byte_count;
  return 0;
}
