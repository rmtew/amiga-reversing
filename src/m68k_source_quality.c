#include "m68k_source_quality.h"

#include "m68k_fact_ir.h"
#include "m68k_simulator.h"
#include "generated/amiga_os_runtime.h"
#include "generated/m68k_cpu_runtime.h"
#include "platform_common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t code_origin_class_from_reason(uint32_t reason) {
  switch (reason) {
    case M68K_FACT_CODE_START_REASON_SECTION_ENTRY:
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET:
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT:
      return M68K_CODE_ORIGIN_STRONG_ENTRY;
    case M68K_FACT_CODE_START_REASON_LINKAGE_API_ENTRY:
    case M68K_FACT_CODE_START_REASON_PLATFORM_LOADSEG_ENTRY:
    case M68K_FACT_CODE_START_REASON_BOUNDARY_API_ENTRY:
      return M68K_CODE_ORIGIN_PLATFORM_SEMANTIC_ENTRY;
    case M68K_FACT_CODE_START_REASON_RUNTIME_VIEW_ENTRY:
      return M68K_CODE_ORIGIN_CONDITIONAL_RUNTIME_ALIAS;
    case M68K_FACT_CODE_START_REASON_FALLTHROUGH:
      return M68K_CODE_ORIGIN_PROVEN_FALLTHROUGH;
    case M68K_FACT_CODE_START_REASON_CONTROL_TARGET:
    case M68K_FACT_CODE_START_REASON_INLINE_RESUME:
    case M68K_FACT_CODE_START_REASON_STACK_CONTINUATION:
      return M68K_CODE_ORIGIN_PROVEN_CONTROL_TARGET;
    default:
      return M68K_CODE_ORIGIN_UNKNOWN;
  }
}

static uint32_t code_origin_evidence_from_ref(const M68kCodeStartRefIR *ref) {
  if (ref == NULL) return M68K_CODE_ORIGIN_EVIDENCE_UNKNOWN;
  return ref->evidence_kind;
}

static int code_origin_class_is_executable_proof(uint8_t origin_class) {
  return origin_class == M68K_CODE_ORIGIN_STRONG_ENTRY ||
    origin_class == M68K_CODE_ORIGIN_PROVEN_CONTROL_TARGET ||
    origin_class == M68K_CODE_ORIGIN_PLATFORM_SEMANTIC_ENTRY ||
    origin_class == M68K_CODE_ORIGIN_MANUAL_SEED ||
    origin_class == M68K_CODE_ORIGIN_CONDITIONAL_TABLE_TARGET ||
    origin_class == M68K_CODE_ORIGIN_CONDITIONAL_RUNTIME_ALIAS;
}

static int append_code_origins_for_section(M68kSectionAnalysisIR *section) {
  size_t index;
  if (section == NULL) return -1;
  for (index = 0U; index < section->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section->code_start_refs[index];
    M68kCodeOriginIR origin;
    memset(&origin, 0, sizeof(origin));
    origin.offset = ref->offset;
    origin.length = ref->size;
    origin.source_section_index = (uint32_t)ref->source_section_index;
    origin.source_offset = ref->source_offset;
    origin.runtime_address = ref->runtime_address;
    origin.reason = ref->reason;
    origin.evidence_kind = code_origin_evidence_from_ref(ref);
    origin.origin_class = code_origin_class_from_reason(ref->reason);
    origin.confidence = ref->confidence;
    origin.has_runtime_address = ref->has_runtime_address;
    if (m68k_ir_section_analysis_append_code_origin(section, &origin) != 0) return -1;
  }
  return 0;
}

static int append_address_observations_for_section(M68kSectionAnalysisIR *section) {
  size_t index;
  if (section == NULL) return -1;
  for (index = 0U; index < section->runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[index];
    M68kAddressObservationIR observation;
    if (!ref->has_runtime_address && !ref->has_target) continue;
    memset(&observation, 0, sizeof(observation));
    observation.offset = ref->offset;
    observation.operand_index = ref->operand_index;
    observation.access_width = ref->size;
    observation.source = M68K_ADDRESS_OBSERVATION_SOURCE_RUNTIME_ADDRESS_REF;
    observation.confidence = ref->confidence;
    if (ref->has_runtime_address) {
      observation.raw_value = ref->runtime_address;
      observation.address = ref->runtime_address;
      observation.has_address = 1U;
    }
    if (ref->has_target) {
      observation.target_section_index = ref->target_section_index > UINT32_MAX ? UINT32_MAX :
        (uint32_t)ref->target_section_index;
      observation.target_offset = ref->target_offset;
      observation.has_target = 1U;
    }
    if (m68k_ir_section_analysis_append_address_observation(section, &observation) != 0) return -1;
  }
  return 0;
}

static uint8_t platform_address_use_shape_from_observation(const M68kAddressObservationIR *observation) {
  if (observation == NULL || !observation->has_address) return M68K_PLATFORM_ADDRESS_USE_SHAPE_UNKNOWN;
  if (observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR) {
    if (observation->access_kind == M68K_SIM_ACCESS_MEMORY_WRITE)
      return M68K_PLATFORM_ADDRESS_USE_SHAPE_TRUE_VECTOR_INSTALL;
    if (observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS)
      return M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_BASE;
    return M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_STORAGE;
  }
  if (observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER ||
      observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE) {
    if (observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS &&
        amiga_os_find_hardware_base_id_by_address(observation->address) != AMIGA_OS_HARDWARE_BASE_ID_NONE) {
      return M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_BASE_ADDRESS;
    }
    return M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS;
  }
  if (observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL) {
    return M68K_PLATFORM_ADDRESS_USE_SHAPE_EXECBASE_LITERAL;
  }
  if (observation->address < 0x400U &&
      (observation->access_kind == M68K_SIM_ACCESS_MEMORY_READ ||
       observation->access_kind == M68K_SIM_ACCESS_MEMORY_WRITE ||
       observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS)) {
    return observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS ?
      M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_BASE : M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_STORAGE;
  }
  return M68K_PLATFORM_ADDRESS_USE_SHAPE_UNKNOWN;
}

static const char *platform_address_use_symbol_from_observation(const M68kAddressObservationIR *observation,
    uint8_t shape, char *symbol_buf, size_t symbol_buf_size) {
  if (symbol_buf != NULL && symbol_buf_size != 0U) symbol_buf[0] = '\0';
  if (observation == NULL || !observation->has_address) return NULL;
  switch (shape) {
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_TRUE_VECTOR_INSTALL: {
      const M68kCpuExceptionVectorInfo *vector = m68k_cpu_find_exception_vector_by_address(observation->address);
      return vector != NULL && vector->symbol_name != NULL && vector->symbol_name[0] != '\0'
        ? vector->symbol_name
        : NULL;
    }
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_BASE_ADDRESS:
      return amiga_os_find_hardware_base_symbol_by_address(observation->address);
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS: {
      const AmigaOsHardwareRegisterFieldInfo *hardware_field =
        amiga_os_find_hardware_register_field_by_cpu_address(observation->address);
      const AmigaOsHardwareRegisterInfo *hardware_register;
      const AmigaOsHardwareRegisterRangeInfo *hardware_range;
      if (hardware_field != NULL &&
          platform_amiga_format_hardware_register_field_symbol(hardware_field, 1, symbol_buf, symbol_buf_size)) {
        return symbol_buf;
      }
      hardware_register = amiga_os_find_hardware_register_by_cpu_address(observation->address);
      if (hardware_register != NULL && hardware_register->base_symbol != NULL &&
          hardware_register->base_symbol[0] != '\0' && hardware_register->symbol_name != NULL &&
          hardware_register->symbol_name[0] != '\0') {
        int written = snprintf(symbol_buf, symbol_buf_size, "%s+%s", hardware_register->base_symbol,
          hardware_register->symbol_name);
        return written > 0 && (size_t)written < symbol_buf_size ? symbol_buf : NULL;
      }
      hardware_range = amiga_os_find_hardware_register_range_by_cpu_address(observation->address);
      if (hardware_range != NULL &&
          platform_amiga_format_hardware_register_range_symbol(hardware_range,
            observation->address - hardware_range->base_address, 1, symbol_buf, symbol_buf_size)) {
        return symbol_buf;
      }
      return amiga_os_find_hardware_base_symbol_by_address(observation->address);
    }
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_EXECBASE_LITERAL:
      return "ExecBase";
    default:
      return NULL;
  }
}

static int append_platform_address_uses_for_section(M68kSectionAnalysisIR *section) {
  size_t index;
  if (section == NULL) return -1;
  for (index = 0U; index < section->address_observation_count; ++index) {
    const M68kAddressObservationIR *observation = &section->address_observations[index];
    M68kPlatformAddressUseIR use;
    char symbol_buf[96];
    uint8_t shape = platform_address_use_shape_from_observation(observation);
    if (shape == M68K_PLATFORM_ADDRESS_USE_SHAPE_UNKNOWN) continue;
    memset(&use, 0, sizeof(use));
    symbol_buf[0] = '\0';
    use.offset = observation->offset;
    use.operand_index = observation->operand_index;
    use.address = observation->address;
    use.effective_address = observation->address;
    use.access_width = observation->access_width;
    use.access_kind = observation->access_kind;
    use.use_shape = shape;
    use.confidence = observation->confidence;
    use.symbol_name = (char *)platform_address_use_symbol_from_observation(observation, shape, symbol_buf,
      sizeof(symbol_buf));
    if (m68k_ir_section_analysis_append_platform_address_use(section, &use) != 0) return -1;
  }
  return 0;
}

static int address_identity_matches_observation(const M68kAddressIdentityIR *identity,
    const M68kAddressObservationIR *observation) {
  if (identity == NULL || observation == NULL || !observation->has_address) return 0;
  return identity->has_absolute_address && identity->absolute_address == observation->address;
}

static uint8_t address_identity_role_from_owner(uint8_t owner_kind) {
  switch (owner_kind) {
    case M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL:
    case M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR:
    case M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER:
    case M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE:
      return M68K_ADDRESS_IDENTITY_ROLE_PLATFORM;
    default:
      return M68K_ADDRESS_IDENTITY_ROLE_STORAGE;
  }
}

static uint8_t absolute_range_status_from_identity(const M68kAddressIdentityIR *identity) {
  if (identity == NULL) return M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_UNKNOWN;
  if (identity->conflicted) return M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_CONFLICT;
  if (identity->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY ||
      identity->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN) {
    return identity->observation_count > 1U ? M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_UNOWNED_SPARSE :
      M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_UNOWNED_ONE_OFF;
  }
  return M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_OWNED;
}

static void absolute_range_fill_access_counts(const M68kSourceAnalysisIR *source_analysis,
    const M68kAddressIdentityIR *identity, M68kAbsoluteAddressRangeIR *range) {
  size_t section_index;
  if (source_analysis == NULL || identity == NULL || range == NULL) return;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t observation_index;
    for (observation_index = 0U; observation_index < section->address_observation_count; ++observation_index) {
      const M68kAddressObservationIR *observation = &section->address_observations[observation_index];
      if (!observation->has_identity || observation->identity_id != identity->identity_id) continue;
      if (range->access_kind == M68K_SIM_ACCESS_NONE) range->access_kind = observation->access_kind;
      else if (range->access_kind != observation->access_kind) range->access_kind = M68K_SIM_ACCESS_COMPUTE_ADDRESS;
      if (observation->access_kind == M68K_SIM_ACCESS_MEMORY_READ) ++range->read_count;
      if (observation->access_kind == M68K_SIM_ACCESS_MEMORY_WRITE) ++range->write_count;
    }
  }
}

static uint32_t absolute_range_end(const M68kAbsoluteAddressRangeIR *range) {
  if (range == NULL) return 0U;
  if (range->range_size == 0U || range->start_address > UINT32_MAX - range->range_size)
    return range->start_address;
  return range->start_address + range->range_size;
}

static int absolute_ranges_can_merge(const M68kAbsoluteAddressRangeIR *left,
    const M68kAbsoluteAddressRangeIR *right) {
  if (left == NULL || right == NULL) return 0;
  if (left->owner_kind != right->owner_kind || left->status != right->status) return 0;
  return right->start_address <= absolute_range_end(left);
}

static void absolute_range_merge(M68kAbsoluteAddressRangeIR *dest, const M68kAbsoluteAddressRangeIR *source) {
  uint32_t start;
  uint32_t end;
  if (dest == NULL || source == NULL) return;
  start = dest->start_address < source->start_address ? dest->start_address : source->start_address;
  end = absolute_range_end(dest) > absolute_range_end(source) ? absolute_range_end(dest) : absolute_range_end(source);
  dest->start_address = start;
  dest->range_size = start <= end ? end - start : 0U;
  dest->observation_count += source->observation_count;
  dest->read_count += source->read_count;
  dest->write_count += source->write_count;
  dest->access_count += source->access_count;
  if (source->source_section_index < dest->source_section_index ||
      (source->source_section_index == dest->source_section_index && source->source_offset < dest->source_offset)) {
    dest->source_section_index = source->source_section_index;
    dest->source_offset = source->source_offset;
  }
}

static void source_analysis_sort_and_coalesce_absolute_ranges(M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  size_t out_count = 0U;
  if (source_analysis == NULL || source_analysis->absolute_address_ranges == NULL ||
      source_analysis->absolute_address_range_count == 0U) {
    return;
  }
  for (index = 1U; index < source_analysis->absolute_address_range_count; ++index) {
    M68kAbsoluteAddressRangeIR current = source_analysis->absolute_address_ranges[index];
    size_t cursor = index;
    while (cursor > 0U) {
      const M68kAbsoluteAddressRangeIR *previous = &source_analysis->absolute_address_ranges[cursor - 1U];
      if (previous->start_address < current.start_address) break;
      if (previous->start_address == current.start_address && previous->owner_kind <= current.owner_kind) break;
      source_analysis->absolute_address_ranges[cursor] = *previous;
      --cursor;
    }
    source_analysis->absolute_address_ranges[cursor] = current;
  }
  for (index = 0U; index < source_analysis->absolute_address_range_count; ++index) {
    M68kAbsoluteAddressRangeIR current = source_analysis->absolute_address_ranges[index];
    if (out_count != 0U &&
        absolute_ranges_can_merge(&source_analysis->absolute_address_ranges[out_count - 1U], &current)) {
      absolute_range_merge(&source_analysis->absolute_address_ranges[out_count - 1U], &current);
      continue;
    }
    source_analysis->absolute_address_ranges[out_count++] = current;
  }
  source_analysis->absolute_address_range_count = out_count;
}

static int format_generated_absolute_memory_symbol(uint32_t address, char *buf, size_t buf_size) {
  int written;
  if (buf == NULL || buf_size == 0U) return 0;
  written = snprintf(buf, buf_size, "absolute_slot_%08X", (unsigned)address);
  return written > 0 && (size_t)written < buf_size;
}

static int absolute_memory_observation_supports_generated_symbol(const M68kAddressObservationIR *observation) {
  if (observation == NULL ||
      observation->source != M68K_ADDRESS_OBSERVATION_SOURCE_ABSOLUTE_OPERAND ||
      observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY ||
      observation->conflicted != 0U ||
      observation->conflict_state != M68K_ANALYSIS_CONFLICT_STATE_CLEAN ||
      !observation->has_address) {
    return 0;
  }
  if (observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS) return 1;
  return (observation->access_kind == M68K_SIM_ACCESS_MEMORY_READ ||
      observation->access_kind == M68K_SIM_ACCESS_MEMORY_WRITE) &&
    observation->access_width != 0U &&
    observation->address < 0x10000U;
}

static int address_identity_supports_generated_absolute_memory_symbol(const M68kSourceAnalysisIR *source_analysis,
    const M68kAddressIdentityIR *identity) {
  size_t section_index;
  if (source_analysis == NULL || identity == NULL || identity->identity_id == 0U) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t observation_index;
    for (observation_index = 0U; observation_index < section->address_observation_count; ++observation_index) {
      const M68kAddressObservationIR *observation = &section->address_observations[observation_index];
      if (observation->has_identity &&
          observation->identity_id == identity->identity_id &&
          absolute_memory_observation_supports_generated_symbol(observation)) {
        return 1;
      }
    }
  }
  return 0;
}

static int source_analysis_assign_absolute_memory_symbols(M68kSourceAnalysisIR *source_analysis) {
  size_t identity_index;
  if (source_analysis == NULL || source_analysis->arena == NULL) return -1;
  for (identity_index = 0U; identity_index < source_analysis->address_identity_count; ++identity_index) {
    M68kAddressIdentityIR *identity = &source_analysis->address_identities[identity_index];
    char symbol[80];
    if (identity->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY ||
        !identity->has_absolute_address ||
        identity->symbol_name != NULL ||
        !address_identity_supports_generated_absolute_memory_symbol(source_analysis, identity)) {
      continue;
    }
    if (!format_generated_absolute_memory_symbol(identity->absolute_address, symbol, sizeof(symbol))) return -1;
    identity->symbol_name = arena_strdup(source_analysis->arena, symbol);
    if (identity->symbol_name == NULL) return -1;
  }
  for (identity_index = 0U; identity_index < source_analysis->address_identity_count; ++identity_index) {
    M68kAddressIdentityIR *identity = &source_analysis->address_identities[identity_index];
    size_t section_index;
    if (identity->symbol_name == NULL) continue;
    for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
      M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
      size_t observation_index;
      for (observation_index = 0U; observation_index < section->address_observation_count; ++observation_index) {
        M68kAddressObservationIR *observation = &section->address_observations[observation_index];
        if (observation->has_identity && observation->identity_id == identity->identity_id &&
            observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY) {
          observation->symbol_name = identity->symbol_name;
        }
      }
    }
  }
  for (identity_index = 0U; identity_index < source_analysis->absolute_address_range_count; ++identity_index) {
    M68kAbsoluteAddressRangeIR *range = &source_analysis->absolute_address_ranges[identity_index];
    size_t address_identity_index;
    if (range->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY || range->symbol_name != NULL) continue;
    for (address_identity_index = 0U; address_identity_index < source_analysis->address_identity_count;
         ++address_identity_index) {
      M68kAddressIdentityIR *identity = &source_analysis->address_identities[address_identity_index];
      if (identity->symbol_name != NULL &&
          identity->has_absolute_address &&
          identity->absolute_address == range->start_address) {
        range->symbol_name = identity->symbol_name;
        break;
      }
    }
  }
  return 0;
}

static void address_identity_merge_observation(M68kAddressIdentityIR *identity,
    const M68kAddressObservationIR *observation, uint32_t section_index) {
  if (identity == NULL || observation == NULL) return;
  if (identity->observation_count == 0U) {
    identity->source_section_index = section_index;
    identity->source_offset = observation->offset;
    identity->absolute_address = observation->address;
    identity->has_absolute_address = observation->has_address;
    identity->owner_kind = observation->owner_kind;
    identity->role_kind = address_identity_role_from_owner(observation->owner_kind);
    identity->conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
    if (observation->source == M68K_ADDRESS_OBSERVATION_SOURCE_RUNTIME_ADDRESS_REF ||
        observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_RUNTIME_RANGE) {
      identity->runtime_address = observation->address;
      identity->has_runtime_address = 1U;
    }
  } else if (identity->owner_kind != observation->owner_kind &&
      observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN) {
    identity->conflicted = 1U;
    identity->conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CONFLICTED;
    ++identity->conflict_count;
  }
  if (observation->source == M68K_ADDRESS_OBSERVATION_SOURCE_RUNTIME_ADDRESS_REF ||
      observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_RUNTIME_RANGE) {
    identity->runtime_address = observation->address;
    identity->has_runtime_address = 1U;
  }
  if (observation->access_width > identity->size) identity->size = observation->access_width;
  if (observation->conflicted || observation->conflict_state != M68K_ANALYSIS_CONFLICT_STATE_CLEAN) {
    identity->conflicted = 1U;
    identity->conflict_state = observation->conflict_state != M68K_ANALYSIS_CONFLICT_STATE_CLEAN ?
      observation->conflict_state : M68K_ANALYSIS_CONFLICT_STATE_CONFLICTED;
    ++identity->conflict_count;
  }
  ++identity->observation_count;
}

static int append_address_identities_and_ranges(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  if (source_analysis->address_identity_count != 0U ||
      source_analysis->absolute_address_range_count != 0U) {
    return 0;
  }
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t observation_index;
    for (observation_index = 0U; observation_index < section->address_observation_count; ++observation_index) {
      M68kAddressObservationIR *observation = &section->address_observations[observation_index];
      M68kAddressIdentityIR identity;
      size_t identity_index;
      if (!observation->has_address) continue;
      for (identity_index = 0U; identity_index < source_analysis->address_identity_count; ++identity_index) {
        if (address_identity_matches_observation(&source_analysis->address_identities[identity_index], observation))
          break;
      }
      if (identity_index == source_analysis->address_identity_count) {
        memset(&identity, 0, sizeof(identity));
        identity.identity_id = (uint32_t)(source_analysis->address_identity_count + 1U);
        if (m68k_ir_source_analysis_append_address_identity(source_analysis, &identity) != 0) return -1;
      }
      observation->identity_id = source_analysis->address_identities[identity_index].identity_id;
      observation->has_identity = 1U;
      address_identity_merge_observation(&source_analysis->address_identities[identity_index], observation,
        (uint32_t)section->section_index);
    }
  }
  for (section_index = 0U; section_index < source_analysis->address_identity_count; ++section_index) {
    const M68kAddressIdentityIR *identity = &source_analysis->address_identities[section_index];
    M68kAbsoluteAddressRangeIR range;
    if (!identity->has_absolute_address) continue;
    memset(&range, 0, sizeof(range));
    range.start_address = identity->absolute_address;
    range.range_size = identity->size;
    range.source_section_index = identity->source_section_index;
    range.source_offset = identity->source_offset;
    range.observation_count = identity->observation_count;
    range.access_count = identity->observation_count;
    range.owner_kind = identity->owner_kind;
    range.status = absolute_range_status_from_identity(identity);
    range.access_kind = M68K_SIM_ACCESS_NONE;
    absolute_range_fill_access_counts(source_analysis, identity, &range);
    if (m68k_ir_source_analysis_append_absolute_address_range(source_analysis, &range) != 0) return -1;
  }
  source_analysis_sort_and_coalesce_absolute_ranges(source_analysis);
  if (source_analysis_assign_absolute_memory_symbols(source_analysis) != 0) return -1;
  return 0;
}

static int accepted_run_has_origin(const M68kSectionAnalysisIR *section, uint32_t start, uint32_t end) {
  size_t index;
  if (section == NULL) return 0;
  for (index = 0U; index < section->code_start_ref_count; ++index) {
    uint32_t offset = section->code_start_refs[index].offset;
    if (offset >= start && offset < end) return 1;
  }
  return 0;
}

static int accepted_run_has_executable_origin(const M68kSectionAnalysisIR *section, uint32_t start, uint32_t end) {
  size_t index;
  if (section == NULL) return 0;
  for (index = 0U; index < section->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section->code_start_refs[index];
    if (ref->offset >= start && ref->offset < end &&
        code_origin_class_is_executable_proof(code_origin_class_from_reason(ref->reason))) {
      return 1;
    }
  }
  return 0;
}

static int range_ownership_is_accepted_noncode(const M68kRangeOwnershipIR *range) {
  return range != NULL &&
    range->status == M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED &&
    range->kind != M68K_RANGE_OWNERSHIP_UNKNOWN &&
    range->kind != M68K_RANGE_OWNERSHIP_CODE &&
    range->kind != M68K_RANGE_OWNERSHIP_CONFLICT;
}

static int range_ownership_overlaps(uint32_t start, uint32_t end, const M68kRangeOwnershipIR *range) {
  return range != NULL && range->start_offset < end && range->end_offset > start;
}

static int range_ownership_blocks_hard_control_proof(const M68kRangeOwnershipIR *range) {
  return range_ownership_is_accepted_noncode(range) ||
    (range != NULL && (range->status == M68K_RANGE_OWNERSHIP_STATUS_CONFLICT ||
      range->kind == M68K_RANGE_OWNERSHIP_CONFLICT));
}

static int accepted_run_overlaps_blocking_range_for_hard_control_proof(const M68kSectionAnalysisIR *section,
    const M68kAcceptedCodeRunIR *run) {
  size_t range_index;
  if (section == NULL || run == NULL) return 1;
  for (range_index = 0U; range_index < section->range_ownership_count; ++range_index) {
    const M68kRangeOwnershipIR *range = &section->range_ownerships[range_index];
    if (range_ownership_blocks_hard_control_proof(range) &&
        range_ownership_overlaps(run->start_offset, run->end_offset, range)) {
      return 1;
    }
  }
  return 0;
}

static int code_start_ref_is_direct_hard_fallthrough_proof(const M68kCodeStartRefIR *ref) {
  if (ref == NULL) return 0;
  switch (ref->reason) {
    case M68K_FACT_CODE_START_REASON_SECTION_ENTRY:
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET:
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT:
    case M68K_FACT_CODE_START_REASON_PLATFORM_LOADSEG_ENTRY:
      return 1;
    default:
      break;
  }
  switch (ref->evidence_kind) {
    case M68K_CODE_ORIGIN_EVIDENCE_SECTION_ENTRY:
    case M68K_CODE_ORIGIN_EVIDENCE_POLICY_ENTRY_OFFSET:
    case M68K_CODE_ORIGIN_EVIDENCE_POLICY_ENTRY_POINT:
    case M68K_CODE_ORIGIN_EVIDENCE_PLATFORM_LOADSEG_ENTRY:
      return 1;
    default:
      return 0;
  }
}

static int code_start_ref_is_control_target_proof(const M68kCodeStartRefIR *ref) {
  if (ref == NULL) return 0;
  if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET) return 1;
  switch (ref->evidence_kind) {
    case M68K_CODE_ORIGIN_EVIDENCE_RUNTIME_CONTROL_TARGET:
    case M68K_CODE_ORIGIN_EVIDENCE_DIRECT_CONTROL_TARGET:
    case M68K_CODE_ORIGIN_EVIDENCE_RELOCATION_CONTROL_TARGET:
    case M68K_CODE_ORIGIN_EVIDENCE_TRACED_INDIRECT_CONTROL_TARGET:
    case M68K_CODE_ORIGIN_EVIDENCE_DISPATCH_TABLE_CONTROL_TARGET:
    case M68K_CODE_ORIGIN_EVIDENCE_CALLBACK_FIELD_CONTROL_TARGET:
    case M68K_CODE_ORIGIN_EVIDENCE_VECTOR_STORE_CONTROL_TARGET:
    case M68K_CODE_ORIGIN_EVIDENCE_RUNTIME_COPY_CONTROL_TARGET:
      return 1;
    default:
      return 0;
  }
}

static int accepted_code_run_index_containing_offset(const M68kSectionAnalysisIR *section,
    uint32_t offset, size_t *out_index) {
  size_t index;
  if (section == NULL || out_index == NULL) return 0;
  for (index = 0U; index < section->accepted_code_run_count; ++index) {
    const M68kAcceptedCodeRunIR *run = &section->accepted_code_runs[index];
    if (offset >= run->start_offset && offset < run->end_offset) {
      *out_index = index;
      return 1;
    }
  }
  return 0;
}

static int accepted_run_has_hard_fallthrough_proof_depth(const M68kSectionAnalysisIR *section,
    size_t run_index, uint8_t *proof_state, unsigned depth) {
  enum { SOURCE_QUALITY_CONTROL_PROOF_DEPTH_LIMIT = 16U };
  enum {
    SOURCE_QUALITY_PROOF_UNKNOWN = 0U,
    SOURCE_QUALITY_PROOF_VISITING = 1U,
    SOURCE_QUALITY_PROOF_FALSE = 2U,
    SOURCE_QUALITY_PROOF_TRUE = 3U
  };
  const M68kAcceptedCodeRunIR *run;
  size_t index;
  if (section == NULL || proof_state == NULL || run_index >= section->accepted_code_run_count) return 0;
  if (proof_state[run_index] == SOURCE_QUALITY_PROOF_TRUE) return 1;
  if (proof_state[run_index] == SOURCE_QUALITY_PROOF_FALSE ||
      proof_state[run_index] == SOURCE_QUALITY_PROOF_VISITING) {
    return 0;
  }
  proof_state[run_index] = SOURCE_QUALITY_PROOF_VISITING;
  run = &section->accepted_code_runs[run_index];
  for (index = 0U; index < section->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section->code_start_refs[index];
    size_t source_run_index;
    const M68kAcceptedCodeRunIR *source_run;
    if (ref->offset < run->start_offset || ref->offset >= run->end_offset) continue;
    if (code_start_ref_is_direct_hard_fallthrough_proof(ref)) {
      proof_state[run_index] = SOURCE_QUALITY_PROOF_TRUE;
      return 1;
    }
    if (!code_start_ref_is_control_target_proof(ref)) continue;
    if (depth >= SOURCE_QUALITY_CONTROL_PROOF_DEPTH_LIMIT) continue;
    if (ref->source_section_index != section->section_index) continue;
    if (ref->source_offset >= run->start_offset && ref->source_offset < run->end_offset) continue;
    if (!accepted_code_run_index_containing_offset(section, ref->source_offset, &source_run_index)) continue;
    source_run = &section->accepted_code_runs[source_run_index];
    if (accepted_run_overlaps_blocking_range_for_hard_control_proof(section, source_run)) continue;
    if (accepted_run_has_hard_fallthrough_proof_depth(section, source_run_index, proof_state, depth + 1U)) {
      proof_state[run_index] = SOURCE_QUALITY_PROOF_TRUE;
      return 1;
    }
  }
  proof_state[run_index] = SOURCE_QUALITY_PROOF_FALSE;
  return 0;
}

static int classify_run_end_from_cfg(const M68kSectionAnalysisIR *section, uint32_t start, uint32_t end,
    M68kAcceptedCodeRunIR *run) {
  size_t block_index;
  if (section == NULL || run == NULL) return 0;
  for (block_index = 0U; block_index < section->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section->blocks[block_index];
    size_t edge_index;
    if (block->start_offset > start || block->end_offset != end) continue;
    for (edge_index = 0U; edge_index < block->edge_count; ++edge_index) {
      const M68kCfgEdgeIR *edge;
      size_t absolute_edge_index = block->edge_start + edge_index;
      if (absolute_edge_index >= section->edge_count) return -1;
      edge = &section->edges[absolute_edge_index];
      if (edge->source_offset < start || edge->source_offset >= end) continue;
      if (edge->kind == M68K_CFG_EDGE_RETURN) {
        run->end_kind = M68K_ACCEPTED_CODE_RUN_END_TERMINAL;
        run->terminal_offset = edge->source_offset;
        run->has_terminal_offset = 1U;
        return 1;
      }
      if (edge->kind == M68K_CFG_EDGE_JUMP) {
        run->end_kind = M68K_ACCEPTED_CODE_RUN_END_PROVEN_TRANSFER;
        run->terminal_offset = edge->source_offset;
        run->has_terminal_offset = 1U;
        return 1;
      }
    }
  }
  return 0;
}

static int classify_run_end_from_decode(const M68kDecodeSectionIR *decode_section, uint32_t start, uint32_t end,
    M68kAcceptedCodeRunIR *run) {
  uint32_t offset;
  if (decode_section == NULL || run == NULL || end <= start) return 0;
  offset = start;
  while (offset < end) {
    const M68kDecodeCandidate *candidate = m68k_decode_ir_find_candidate_at_offset(decode_section, offset);
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    uint32_t next_offset;
    if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > end - offset) break;
    next_offset = offset + candidate->byte_count;
    if (next_offset != end) {
      offset = next_offset;
      continue;
    }
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) return 0;
    if (metadata->flow_kind == M68K_SIM_FLOW_RETURN ||
        (metadata->flow_kind == M68K_SIM_FLOW_TRAP &&
         metadata->exception_trigger == M68K_SIM_EXCEPTION_TRIGGER_ALWAYS &&
         metadata->exception_pc_source == M68K_SIM_EXCEPTION_PC_CURRENT)) {
      run->end_kind = M68K_ACCEPTED_CODE_RUN_END_TERMINAL;
      run->terminal_offset = candidate->offset;
      run->has_terminal_offset = 1U;
      return 1;
    }
    if (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
        (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U)) {
      run->end_kind = M68K_ACCEPTED_CODE_RUN_END_PROVEN_TRANSFER;
      run->terminal_offset = candidate->offset;
      run->has_terminal_offset = 1U;
      return 1;
    }
    return 0;
  }
  return 0;
}

static int accepted_run_decode_coverage_gap(const M68kSectionAnalysisIR *section,
    const M68kDecodeSectionIR *decode_section, const M68kAcceptedCodeRunIR *run, uint32_t *out_offset) {
  uint32_t offset;
  uint32_t expected_offset;
  uint8_t saw_start = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (section == NULL || decode_section == NULL || run == NULL || section->certain_code_start == NULL ||
      section->certain_code_byte == NULL || run->end_offset <= run->start_offset) {
    return 0;
  }
  expected_offset = run->start_offset;
  for (offset = run->start_offset; offset < run->end_offset && (size_t)offset < section->certain_code_size;
       ++offset) {
    const M68kDecodeCandidate *candidate;
    uint32_t next_offset;
    if (section->certain_code_start[offset] == 0U) continue;
    saw_start = 1U;
    if (offset < expected_offset) continue;
    if (offset > expected_offset) {
      if (out_offset != NULL) *out_offset = expected_offset;
      return 1;
    }
    candidate = m68k_decode_ir_find_candidate_at_offset(decode_section, offset);
    if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > run->end_offset - offset) {
      if (out_offset != NULL) *out_offset = offset;
      return 1;
    }
    next_offset = offset + candidate->byte_count;
    if (next_offset <= expected_offset) {
      if (out_offset != NULL) *out_offset = offset;
      return 1;
    }
    expected_offset = next_offset;
  }
  if (!saw_start || expected_offset < run->end_offset) {
    if (out_offset != NULL) *out_offset = saw_start ? expected_offset : run->start_offset;
    return 1;
  }
  return 0;
}

static int append_run_offset_diagnostic(M68kSectionAnalysisIR *section, const M68kAcceptedCodeRunIR *run,
    uint32_t offset, uint8_t kind, uint8_t severity, uint8_t blocker, const char *summary,
    const char *evidence_source) {
  M68kSourceQualityDiagnosticIR diagnostic;
  if (section == NULL || run == NULL) return -1;
  memset(&diagnostic, 0, sizeof(diagnostic));
  diagnostic.kind = kind;
  diagnostic.severity = severity;
  diagnostic.blocker = blocker;
  diagnostic.origin = M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_AUTO_ANALYSIS;
  diagnostic.has_section_index = 1U;
  diagnostic.section_index = (uint32_t)section->section_index;
  diagnostic.has_offset = 1U;
  diagnostic.offset = offset;
  diagnostic.has_related_range = 1U;
  diagnostic.related_start = run->start_offset;
  diagnostic.related_end = run->end_offset;
  diagnostic.summary = (char *)summary;
  diagnostic.evidence_source = (char *)evidence_source;
  return m68k_ir_section_analysis_append_source_quality_diagnostic(section, &diagnostic);
}

static int append_run_diagnostic(M68kSectionAnalysisIR *section, const M68kAcceptedCodeRunIR *run, uint8_t kind,
    uint8_t severity, uint8_t blocker, const char *summary) {
  M68kSourceQualityDiagnosticIR diagnostic;
  if (section == NULL || run == NULL) return -1;
  memset(&diagnostic, 0, sizeof(diagnostic));
  diagnostic.kind = kind;
  diagnostic.severity = severity;
  diagnostic.blocker = blocker;
  diagnostic.origin = M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_AUTO_ANALYSIS;
  diagnostic.has_section_index = 1U;
  diagnostic.section_index = (uint32_t)section->section_index;
  diagnostic.has_offset = 1U;
  diagnostic.offset = run->start_offset;
  diagnostic.has_related_range = 1U;
  diagnostic.related_start = run->start_offset;
  diagnostic.related_end = run->end_offset;
  diagnostic.summary = (char *)summary;
  diagnostic.evidence_source = "accepted_code_run";
  return m68k_ir_section_analysis_append_source_quality_diagnostic(section, &diagnostic);
}

static uint8_t rendered_symbol_access_kind_for_expected(uint8_t expected_kind) {
  switch (expected_kind) {
    case M68K_EXPECTED_SYMBOL_ACCESS_LABEL_STATEMENT:
      return M68K_RENDERED_SYMBOL_ACCESS_LABEL_STATEMENT;
    case M68K_EXPECTED_SYMBOL_ACCESS_BRANCH_TARGET:
      return M68K_RENDERED_SYMBOL_ACCESS_BRANCH_TARGET;
    case M68K_EXPECTED_SYMBOL_ACCESS_OPERAND:
      return M68K_RENDERED_SYMBOL_ACCESS_OPERAND;
    case M68K_EXPECTED_SYMBOL_ACCESS_EQUATE:
      return M68K_RENDERED_SYMBOL_ACCESS_EQUATE;
    case M68K_EXPECTED_SYMBOL_ACCESS_STORAGE_LABEL:
      return M68K_RENDERED_SYMBOL_ACCESS_STORAGE_LABEL;
    default:
      return M68K_RENDERED_SYMBOL_ACCESS_UNKNOWN;
  }
}

static int source_quality_hex_digit_value(char value, uint32_t *out_digit) {
  if (out_digit != NULL) *out_digit = 0U;
  if (value >= '0' && value <= '9') {
    if (out_digit != NULL) *out_digit = (uint32_t)(value - '0');
    return 1;
  }
  if (value >= 'A' && value <= 'F') {
    if (out_digit != NULL) *out_digit = 10U + (uint32_t)(value - 'A');
    return 1;
  }
  if (value >= 'a' && value <= 'f') {
    if (out_digit != NULL) *out_digit = 10U + (uint32_t)(value - 'a');
    return 1;
  }
  return 0;
}

static int source_quality_symbol_suffix_u32(const char *symbol_name, const char *prefix, uint32_t *out_value) {
  size_t prefix_len;
  size_t index;
  uint32_t value = 0U;
  if (out_value != NULL) *out_value = 0U;
  if (symbol_name == NULL || prefix == NULL) return 0;
  prefix_len = strlen(prefix);
  if (strncmp(symbol_name, prefix, prefix_len) != 0) return 0;
  for (index = 0U; index < 8U; ++index) {
    uint32_t digit = 0U;
    if (!source_quality_hex_digit_value(symbol_name[prefix_len + index], &digit)) return 0;
    value = (value << 4) | digit;
  }
  if (symbol_name[prefix_len + 8U] != '\0') return 0;
  if (out_value != NULL) *out_value = value;
  return 1;
}

static int rendered_symbol_access_is_runtime_alias_for_expected_absolute_slot(
    const M68kRenderedSymbolAccessIR *rendered, const M68kExpectedSymbolAccessIR *expected) {
  uint32_t rendered_value = 0U;
  uint32_t expected_value = 0U;
  if (rendered == NULL || expected == NULL) return 0;
  if (!source_quality_symbol_suffix_u32(expected->symbol_name, "absolute_slot_", &expected_value)) return 0;
  if (!source_quality_symbol_suffix_u32(rendered->symbol_name, "runtime_address_", &rendered_value)) return 0;
  return rendered_value == expected_value;
}

static int rendered_symbol_access_matches_expected(const M68kRenderedSymbolAccessIR *rendered,
    const M68kExpectedSymbolAccessIR *expected, uint8_t rendered_kind) {
  if (rendered == NULL || expected == NULL || rendered_kind == M68K_RENDERED_SYMBOL_ACCESS_UNKNOWN) return 0;
  if (rendered->comment_only) return 0;
  if (rendered->access_kind != rendered_kind) return 0;
  if (rendered->offset != expected->offset) return 0;
  if (rendered->symbol_name == NULL || rendered->symbol_name[0] == '\0') return 0;
  if (!expected->has_target &&
      (expected->symbol_name == NULL || (
        strcmp(rendered->symbol_name, expected->symbol_name) != 0 &&
        !rendered_symbol_access_is_runtime_alias_for_expected_absolute_slot(rendered, expected)))) {
    return 0;
  }
  if (expected->has_target) {
    if (!rendered->has_target ||
        rendered->target_section_index != expected->target_section_index ||
        rendered->target_offset != expected->target_offset) {
      return 0;
    }
  }
  if (expected->operand_index != UINT32_MAX && rendered->operand_index != expected->operand_index) return 0;
  return 1;
}

static int section_has_rendered_symbol_access(const M68kRenderEvidenceSectionIR *render_evidence_section,
    const M68kExpectedSymbolAccessIR *expected) {
  uint8_t rendered_kind;
  size_t index;
  if (render_evidence_section == NULL || expected == NULL) return 0;
  rendered_kind = rendered_symbol_access_kind_for_expected(expected->access_kind);
  if (rendered_kind == M68K_RENDERED_SYMBOL_ACCESS_UNKNOWN) return 1;
  for (index = 0U; index < render_evidence_section->rendered_symbol_access_count; ++index) {
    if (rendered_symbol_access_matches_expected(&render_evidence_section->rendered_symbol_accesses[index], expected,
        rendered_kind)) {
      return 1;
    }
  }
  return 0;
}

static int append_missing_expected_symbol_access_diagnostic(M68kSectionAnalysisIR *section,
    const M68kExpectedSymbolAccessIR *access) {
  M68kSourceQualityDiagnosticIR diagnostic;
  char evidence_source[160];
  const char *producer;
  if (section == NULL || access == NULL) return -1;
  producer = access->producer != NULL && access->producer[0] != '\0' ? access->producer : "unknown";
  snprintf(evidence_source, sizeof(evidence_source), "expected_symbol_access:%s", producer);
  memset(&diagnostic, 0, sizeof(diagnostic));
  diagnostic.kind = M68K_SOURCE_QUALITY_DIAGNOSTIC_MISSING_EXPECTED_SYMBOL_ACCESS;
  diagnostic.severity = M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR;
  diagnostic.blocker = 1U;
  diagnostic.origin = M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_RENDER_EXPORT;
  diagnostic.has_section_index = 1U;
  diagnostic.section_index = (uint32_t)section->section_index;
  diagnostic.has_offset = 1U;
  diagnostic.offset = access->offset;
  diagnostic.summary = "expected symbol access was not rendered";
  diagnostic.evidence_source = evidence_source;
  return m68k_ir_section_analysis_append_source_quality_diagnostic(section, &diagnostic);
}

static int append_missing_expected_symbol_access_diagnostics_for_section(M68kSectionAnalysisIR *section,
    const M68kRenderEvidenceSectionIR *render_evidence_section) {
  size_t index;
  if (section == NULL) return -1;
  for (index = 0U; index < section->expected_symbol_access_count; ++index) {
    const M68kExpectedSymbolAccessIR *access = &section->expected_symbol_accesses[index];
    if (!section_has_rendered_symbol_access(render_evidence_section, access)) {
      if (append_missing_expected_symbol_access_diagnostic(section, access) != 0) return -1;
    }
  }
  return 0;
}

static int rendered_symbol_access_references_label(const M68kRenderedSymbolAccessIR *label,
    const M68kRenderedSymbolAccessIR *access) {
  if (label == NULL || access == NULL || access->comment_only ||
      access->access_kind == M68K_RENDERED_SYMBOL_ACCESS_LABEL_STATEMENT ||
      access->access_kind == M68K_RENDERED_SYMBOL_ACCESS_UNKNOWN) {
    return 0;
  }
  if (label->has_target && access->has_target) {
    return label->target_section_index == access->target_section_index &&
      label->target_offset == access->target_offset;
  }
  return label->symbol_name != NULL && access->symbol_name != NULL &&
    strcmp(label->symbol_name, access->symbol_name) == 0;
}

static int render_evidence_has_rendered_reference_to_label(const M68kRenderEvidenceIR *render_evidence,
    const M68kRenderedSymbolAccessIR *label) {
  size_t section_index;
  size_t index;
  if (render_evidence == NULL || label == NULL) return 0;
  for (section_index = 0U; section_index < render_evidence->section_count; ++section_index) {
    const M68kRenderEvidenceSectionIR *section = &render_evidence->sections[section_index];
    for (index = 0U; index < section->rendered_symbol_access_count; ++index) {
      if (rendered_symbol_access_references_label(label, &section->rendered_symbol_accesses[index])) return 1;
    }
  }
  return 0;
}

static int section_label_has_durable_unreferenced_origin(const M68kSectionAnalysisIR *section,
    const M68kRenderedSymbolAccessIR *label) {
  size_t index;
  if (section == NULL || label == NULL) return 0;
  for (index = 0U; index < section->symbol_origin_count; ++index) {
    const M68kSymbolOriginIR *origin = &section->symbol_origins[index];
    if (origin->origin_kind != M68K_SYMBOL_ORIGIN_STRUCTURED_DATA &&
        origin->origin_kind != M68K_SYMBOL_ORIGIN_OBJECT_SYMBOL) continue;
    if (label->has_target) {
      if (label->target_section_index == section->section_index && label->target_offset == origin->offset)
        return 1;
    } else if (label->symbol_name != NULL && origin->symbol_name != NULL &&
        strcmp(label->symbol_name, origin->symbol_name) == 0) {
      return 1;
    }
  }
  return 0;
}

static int code_origin_class_justifies_unreferenced_label(uint8_t origin_class) {
  return origin_class == M68K_CODE_ORIGIN_STRONG_ENTRY ||
    origin_class == M68K_CODE_ORIGIN_PROVEN_CONTROL_TARGET ||
    origin_class == M68K_CODE_ORIGIN_PLATFORM_SEMANTIC_ENTRY ||
    origin_class == M68K_CODE_ORIGIN_MANUAL_SEED ||
    origin_class == M68K_CODE_ORIGIN_CONDITIONAL_TABLE_TARGET ||
    origin_class == M68K_CODE_ORIGIN_CONDITIONAL_RUNTIME_ALIAS;
}

static int section_label_has_code_origin(const M68kSectionAnalysisIR *section,
    const M68kRenderedSymbolAccessIR *label) {
  size_t index;
  if (section == NULL || label == NULL) return 0;
  for (index = 0U; index < section->code_origin_count; ++index) {
    const M68kCodeOriginIR *origin = &section->code_origins[index];
    if (!code_origin_class_justifies_unreferenced_label(origin->origin_class)) continue;
    if (label->has_target) {
      if (label->target_section_index == section->section_index && label->target_offset == origin->offset)
        return 1;
    } else if (label->offset == origin->offset) {
      return 1;
    }
  }
  return 0;
}

static int source_analysis_label_has_structured_data_item_origin(const M68kSourceAnalysisIR *source_analysis,
    const M68kSectionAnalysisIR *section, const M68kRenderedSymbolAccessIR *label) {
  size_t index;
  uint32_t target_section_index;
  uint32_t target_offset;
  if (source_analysis == NULL || section == NULL || label == NULL) return 0;
  target_section_index = (uint32_t)section->section_index;
  target_offset = label->offset;
  if (label->has_target) {
    target_section_index = label->target_section_index;
    target_offset = label->target_offset;
  }
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    if (!item->has_section_index || item->section_index != target_section_index) continue;
    if (item->size == 0U || item->offset > UINT32_MAX - item->size) continue;
    if (target_offset >= item->offset && target_offset < item->offset + item->size) return 1;
  }
  return 0;
}

static int section_label_has_noncode_range_origin(const M68kSourceAnalysisIR *source_analysis,
    const M68kSectionAnalysisIR *section, const M68kRenderedSymbolAccessIR *label) {
  size_t index;
  if (section == NULL || label == NULL) return 0;
  for (index = 0U; index < section->range_ownership_count; ++index) {
    const M68kRangeOwnershipIR *range = &section->range_ownerships[index];
    if (range->kind == M68K_RANGE_OWNERSHIP_UNKNOWN ||
        range->kind == M68K_RANGE_OWNERSHIP_CODE ||
        range->kind == M68K_RANGE_OWNERSHIP_CONFLICT ||
        range->status != M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED) {
      continue;
    }
    if (label->has_target) {
      if (label->target_section_index == section->section_index &&
          label->target_offset >= range->start_offset && label->target_offset < range->end_offset)
        return 1;
    } else if (label->offset >= range->start_offset && label->offset < range->end_offset) {
      return 1;
    }
  }
  if (source_analysis_label_has_structured_data_item_origin(source_analysis, section, label)) return 1;
  return 0;
}

static int section_label_is_accepted_code_start(const M68kSectionAnalysisIR *section,
    const M68kRenderedSymbolAccessIR *label) {
  uint32_t offset;
  if (section == NULL || label == NULL || section->certain_code_start == NULL ||
      section->certain_code_size == 0U) {
    return 0;
  }
  if (label->has_target) {
    if (label->target_section_index != section->section_index) return 0;
    offset = label->target_offset;
  } else {
    offset = label->offset;
  }
  return (size_t)offset < section->certain_code_size && section->certain_code_start[offset] != 0U;
}

static int append_unreferenced_label_statement_diagnostic(M68kSectionAnalysisIR *section,
    const M68kRenderedSymbolAccessIR *label) {
  M68kSourceQualityDiagnosticIR diagnostic;
  if (section == NULL || label == NULL) return -1;
  memset(&diagnostic, 0, sizeof(diagnostic));
  diagnostic.kind = M68K_SOURCE_QUALITY_DIAGNOSTIC_UNREFERENCED_LABEL_STATEMENT;
  diagnostic.severity = M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR;
  diagnostic.blocker = 1U;
  diagnostic.origin = M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_RENDER_EXPORT;
  diagnostic.has_section_index = 1U;
  diagnostic.section_index = (uint32_t)section->section_index;
  diagnostic.has_offset = 1U;
  diagnostic.offset = label->offset;
  diagnostic.summary = "label statement has no rendered symbol reference";
  diagnostic.evidence_source = "rendered_symbol_access";
  return m68k_ir_section_analysis_append_source_quality_diagnostic(section, &diagnostic);
}

static int append_unreferenced_label_statement_diagnostics_for_section(M68kSourceAnalysisIR *source_analysis,
    M68kSectionAnalysisIR *section, const M68kRenderEvidenceIR *render_evidence) {
  size_t index;
  const M68kRenderEvidenceSectionIR *render_evidence_section;
  if (section == NULL || render_evidence == NULL) return -1;
  render_evidence_section = m68k_ir_render_evidence_section_by_index(render_evidence,
    (uint32_t)section->section_index);
  if (render_evidence_section == NULL) return 0;
  for (index = 0U; index < render_evidence_section->rendered_symbol_access_count; ++index) {
    const M68kRenderedSymbolAccessIR *access = &render_evidence_section->rendered_symbol_accesses[index];
    if (access->access_kind != M68K_RENDERED_SYMBOL_ACCESS_LABEL_STATEMENT || access->comment_only) continue;
    if (section_label_has_durable_unreferenced_origin(section, access)) continue;
    if (section_label_has_code_origin(section, access)) continue;
    if (section_label_has_noncode_range_origin(source_analysis, section, access)) continue;
    if (section_label_is_accepted_code_start(section, access)) continue;
    if (!render_evidence_has_rendered_reference_to_label(render_evidence, access)) {
      if (append_unreferenced_label_statement_diagnostic(section, access) != 0) return -1;
    }
  }
  return 0;
}

static int append_accepted_code_range_ownerships_for_section(M68kSectionAnalysisIR *section) {
  uint32_t cursor;
  if (section == NULL || section->certain_code_byte == NULL || section->certain_code_size == 0U) return 0;
  cursor = 0U;
  while ((size_t)cursor < section->certain_code_size) {
    M68kRangeOwnershipIR range;
    uint32_t start;
    if (section->certain_code_byte[cursor] == 0U) {
      ++cursor;
      continue;
    }
    start = cursor;
    while ((size_t)cursor < section->certain_code_size && section->certain_code_byte[cursor] != 0U) ++cursor;
    memset(&range, 0, sizeof(range));
    range.start_offset = start;
    range.end_offset = cursor;
    range.kind = M68K_RANGE_OWNERSHIP_CODE;
    range.status = M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED;
    range.positive_evidence_flags = M68K_RANGE_EVIDENCE_ACCEPTED_CODE;
    if (m68k_ir_section_analysis_append_range_ownership(section, &range) != 0) return -1;
  }
  return 0;
}

static uint32_t structured_data_range_negative_evidence_flags(uint8_t conflict_state) {
  if (conflict_state == M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP) return M68K_RANGE_NEGATIVE_CODE_OVERLAP;
  if (conflict_state == M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED_CODE_TARGET)
    return M68K_RANGE_NEGATIVE_UNRESOLVED_CODE_TARGET;
  return 0U;
}

static int section_has_certain_code_overlap(const M68kSectionAnalysisIR *section, uint32_t start, uint32_t end) {
  uint32_t cursor;
  if (section == NULL || section->certain_code_byte == NULL || section->certain_code_size == 0U || start >= end)
    return 0;
  if (start >= section->certain_code_size) return 0;
  if (end > section->certain_code_size) end = (uint32_t)section->certain_code_size;
  for (cursor = start; cursor < end; ++cursor) {
    if (section->certain_code_byte[cursor] != 0U) return 1;
  }
  return 0;
}

static M68kSectionAnalysisIR *source_analysis_section_by_index(M68kSourceAnalysisIR *source_analysis,
    uint32_t section_index) {
  size_t index;
  if (source_analysis == NULL) return NULL;
  for (index = 0U; index < source_analysis->section_count; ++index) {
    if (source_analysis->sections[index].section_index == section_index) return &source_analysis->sections[index];
  }
  return NULL;
}

static const M68kSymbolOriginIR *source_quality_symbol_origin_at(const M68kSectionAnalysisIR *section,
    uint32_t offset) {
  size_t index;
  if (section == NULL) return NULL;
  for (index = 0U; index < section->symbol_origin_count; ++index) {
    const M68kSymbolOriginIR *origin = &section->symbol_origins[index];
    if (origin->offset == offset && origin->symbol_name != NULL && origin->symbol_name[0] != '\0')
      return origin;
  }
  return NULL;
}

static int append_structured_data_range_ownerships(M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  if (source_analysis == NULL) return -1;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    M68kSectionAnalysisIR *section;
    M68kRangeOwnershipIR range;
    uint8_t conflict_state;
    uint8_t conflicted;
    if (!item->has_section_index || item->size == 0U || item->offset > UINT32_MAX - item->size) continue;
    section = source_analysis_section_by_index(source_analysis, item->section_index);
    if (section == NULL) continue;
    conflict_state = item->table_conflict_state;
    conflicted = item->table_conflicted;
    if (section_has_certain_code_overlap(section, item->offset, item->offset + item->size)) {
      conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP;
      conflicted = 1U;
    }
    memset(&range, 0, sizeof(range));
    range.start_offset = item->offset;
    range.end_offset = item->offset + item->size;
    range.kind = m68k_analysis_structured_data_range_ownership_kind(item);
    range.status = conflicted ? M68K_RANGE_OWNERSHIP_STATUS_CONFLICT :
      M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED;
    range.data_kind = item->kind;
    range.conflict_state = conflict_state;
    range.positive_evidence_flags = m68k_analysis_structured_data_range_ownership_evidence_flags(item);
    range.negative_evidence_flags = conflicted ? structured_data_range_negative_evidence_flags(conflict_state) : 0U;
    range.has_source = item->has_consumer;
    range.source_offset = item->consumer_offset;
    range.table_kind_id = item->table_kind_id;
    range.source_pattern_id = item->source_pattern_id;
    range.role = item->semantic_role[0] != '\0' ? (char *)item->semantic_role : NULL;
    range.source_pattern = item->source_pattern[0] != '\0' ? (char *)item->source_pattern : NULL;
    if (m68k_ir_section_analysis_append_range_ownership(section, &range) != 0) return -1;
  }
  return 0;
}

static int accepted_run_overlaps_accepted_noncode(const M68kSectionAnalysisIR *section,
    const M68kAcceptedCodeRunIR *run) {
  size_t range_index;
  if (section == NULL || run == NULL) return 0;
  for (range_index = 0U; range_index < section->range_ownership_count; ++range_index) {
    const M68kRangeOwnershipIR *range = &section->range_ownerships[range_index];
    if (range_ownership_is_accepted_noncode(range) &&
        range_ownership_overlaps(run->start_offset, run->end_offset, range)) {
      return 1;
    }
  }
  return 0;
}

static int append_accepted_run_noncode_fallthrough_diagnostics_for_section(M68kSectionAnalysisIR *section) {
  size_t run_index;
  uint8_t *proof_state;
  if (section == NULL) return -1;
  if (section->accepted_code_run_count == 0U) return 0;
  proof_state = (uint8_t *)calloc(section->accepted_code_run_count, sizeof(*proof_state));
  if (proof_state == NULL) return -1;
  for (run_index = 0U; run_index < section->accepted_code_run_count; ++run_index) {
    const M68kAcceptedCodeRunIR *run = &section->accepted_code_runs[run_index];
    size_t range_index;
    if (run->end_kind != M68K_ACCEPTED_CODE_RUN_END_ACCEPTED_GAP) continue;
    if (!accepted_run_has_hard_fallthrough_proof_depth(section, run_index, proof_state, 0U)) continue;
    if (accepted_run_overlaps_accepted_noncode(section, run)) continue;
    for (range_index = 0U; range_index < section->range_ownership_count; ++range_index) {
      const M68kRangeOwnershipIR *range = &section->range_ownerships[range_index];
      if (range->start_offset != run->end_offset || !range_ownership_is_accepted_noncode(range)) continue;
      if (append_run_diagnostic(section, run,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_UNTERMINATED_OR_INVALID_CODE_RANGE,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR, 1U,
          "accepted code run falls through into accepted non-code range") != 0) {
        free(proof_state);
        return -1;
      }
      break;
    }
  }
  free(proof_state);
  return 0;
}

static int append_accepted_run_noncode_fallthrough_diagnostics(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    if (append_accepted_run_noncode_fallthrough_diagnostics_for_section(
        &source_analysis->sections[section_index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static uint8_t platform_semantic_use_kind_from_role_flag(uint32_t role_flag) {
  switch (role_flag) {
    case M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST:
      return M68K_PLATFORM_SEMANTIC_USE_COPPER_LIST;
    case M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP:
      return M68K_PLATFORM_SEMANTIC_USE_BITMAP_PLANE;
    case M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE:
      return M68K_PLATFORM_SEMANTIC_USE_SOUND_SAMPLE;
    case M68K_ANALYSIS_STRUCTURED_DATA_ROLE_DISK_BUFFER:
      return M68K_PLATFORM_SEMANTIC_USE_DISK_BUFFER;
    case M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_DESTINATION:
    case M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_SOURCE:
      return M68K_PLATFORM_SEMANTIC_USE_BLITTER_BUFFER;
    case M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE:
      return M68K_PLATFORM_SEMANTIC_USE_PALETTE;
    case M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SPRITE:
      return M68K_PLATFORM_SEMANTIC_USE_SPRITE;
    case M68K_ANALYSIS_STRUCTURED_DATA_ROLE_AUDIO_TABLE:
      return M68K_PLATFORM_SEMANTIC_USE_AUDIO_TABLE;
    default:
      return M68K_PLATFORM_SEMANTIC_USE_UNKNOWN;
  }
}

static int append_structured_data_platform_semantic_use(M68kSourceAnalysisIR *source_analysis,
    const M68kAnalysisStructuredDataItem *item, uint32_t role_flag) {
  M68kSectionAnalysisIR *section;
  M68kPlatformSemanticUseIR use;
  if (source_analysis == NULL || item == NULL || !item->has_section_index ||
      item->section_index >= source_analysis->section_count) {
    return 0;
  }
  memset(&use, 0, sizeof(use));
  use.kind = platform_semantic_use_kind_from_role_flag(role_flag);
  if (use.kind == M68K_PLATFORM_SEMANTIC_USE_UNKNOWN) return 0;
  use.offset = item->offset;
  use.size = item->size;
  use.role_flags = role_flag;
  use.source_pattern_id = item->source_pattern_id;
  use.confidence = 255U;
  use.has_target = item->has_target;
  use.target_section_index = item->target_section;
  use.target_offset = item->target_offset;
  section = &source_analysis->sections[item->section_index];
  return m68k_ir_section_analysis_append_platform_semantic_use(section, &use);
}

static int append_structured_data_platform_semantic_uses(M68kSourceAnalysisIR *source_analysis) {
  static const uint32_t platform_role_flags[] = {
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_DISK_BUFFER,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_DESTINATION,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_SOURCE,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SPRITE,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_AUDIO_TABLE
  };
  size_t item_index, role_index;
  if (source_analysis == NULL) return -1;
  for (item_index = 0U; item_index < source_analysis->structured_data_item_count; ++item_index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[item_index];
    for (role_index = 0U; role_index < sizeof(platform_role_flags) / sizeof(platform_role_flags[0]); ++role_index) {
      uint32_t role_flag = platform_role_flags[role_index];
      if ((item->semantic_role_flags & role_flag) == 0U) continue;
      if (append_structured_data_platform_semantic_use(source_analysis, item, role_flag) != 0) return -1;
    }
  }
  return 0;
}

static int append_runtime_ref_platform_semantic_use(M68kSectionAnalysisIR *section,
    const M68kRuntimeAddressRefIR *ref, uint32_t role_flag) {
  M68kPlatformSemanticUseIR use;
  if (section == NULL || ref == NULL) return -1;
  memset(&use, 0, sizeof(use));
  use.kind = platform_semantic_use_kind_from_role_flag(role_flag);
  if (use.kind == M68K_PLATFORM_SEMANTIC_USE_UNKNOWN) return 0;
  use.offset = ref->offset;
  use.size = ref->size != 0U ? ref->size : ref->source_size;
  use.role_flags = role_flag;
  use.confidence = ref->confidence;
  use.has_target = ref->has_target;
  use.target_section_index = (uint32_t)ref->target_section_index;
  use.target_offset = ref->target_offset;
  return m68k_ir_section_analysis_append_platform_semantic_use(section, &use);
}

static int append_runtime_ref_platform_semantic_uses(M68kSourceAnalysisIR *source_analysis) {
  static const uint32_t platform_role_flags[] = {
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_DISK_BUFFER,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_DESTINATION,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_SOURCE,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SPRITE,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_AUDIO_TABLE
  };
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t ref_index;
    for (ref_index = 0U; ref_index < section->runtime_address_ref_count; ++ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[ref_index];
      size_t role_index;
      for (role_index = 0U; role_index < sizeof(platform_role_flags) / sizeof(platform_role_flags[0]);
           ++role_index) {
        uint32_t role_flag = platform_role_flags[role_index];
        if ((ref->data_class_flags & role_flag) == 0U) continue;
        if (append_runtime_ref_platform_semantic_use(section, ref, role_flag) != 0) return -1;
      }
    }
  }
  return 0;
}

static int append_structured_data_table_descriptors(M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  if (source_analysis == NULL) return -1;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    M68kSectionAnalysisIR *section;
    M68kTableDescriptorIR descriptor;
    uint32_t entry_size;
    if (!item->has_section_index || item->size == 0U ||
        item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN ||
        item->offset > UINT32_MAX - item->size) {
      continue;
    }
    entry_size = m68k_analysis_structured_data_table_entry_size(item);
    if (entry_size == 0U || item->size < entry_size) continue;
    section = source_analysis_section_by_index(source_analysis, item->section_index);
    if (section == NULL) continue;
    memset(&descriptor, 0, sizeof(descriptor));
    descriptor.start_offset = item->offset;
    descriptor.end_offset = item->offset + item->size;
    descriptor.entry_size = entry_size;
    descriptor.entry_count = item->size / entry_size;
    descriptor.entry_count_proof_id = item->entry_count_proof_id;
    descriptor.table_stop_reason_id = item->table_stop_reason_id;
    descriptor.table_kind_id = item->table_kind_id;
    descriptor.base_expression_id = item->table_base_expression_id;
    descriptor.source_pattern_id = item->source_pattern_id;
    descriptor.status = item->table_conflicted ? M68K_RANGE_OWNERSHIP_STATUS_CONFLICT :
      M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED;
    descriptor.role_flags = item->semantic_role_flags;
    descriptor.has_target = item->has_target;
    descriptor.target_section_index = item->target_section;
    descriptor.target_offset = item->target_offset;
    descriptor.has_consumer = item->has_consumer;
    descriptor.consumer_section_index = item->consumer_section;
    descriptor.consumer_offset = item->consumer_offset;
    descriptor.has_index_register = item->has_index_register;
    descriptor.index_register_kind = item->index_register_kind;
    descriptor.index_register = item->index_register;
    descriptor.has_target_register = item->has_target_register;
    descriptor.target_register_kind = item->target_register_kind;
    descriptor.target_register = item->target_register;
    descriptor.has_index_mask_domain = item->has_index_mask_domain;
    descriptor.index_mask_min = item->index_mask_min;
    descriptor.index_mask_max = item->index_mask_max;
    descriptor.has_index_compare_domain = item->has_index_compare_domain;
    descriptor.index_compare_min = item->index_compare_min;
    descriptor.index_compare_max = item->index_compare_max;
    descriptor.index_domain_branch_mnemonic_id = item->index_domain_branch_mnemonic_id;
    descriptor.has_index_loop_domain = item->has_index_loop_domain;
    descriptor.index_loop_min = item->index_loop_min;
    descriptor.index_loop_max = item->index_loop_max;
    descriptor.index_loop_mnemonic_id = item->index_loop_mnemonic_id;
    descriptor.conflict_state = item->table_conflict_state;
    if (m68k_ir_section_analysis_append_table_descriptor(section, &descriptor) != 0) return -1;
  }
  return 0;
}

static int source_quality_structured_data_item_is_pointer_table(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
    (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) != 0U;
}

static int source_quality_structured_data_item_is_keyed_long_relative_lookup_table(
    const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS && item->has_target &&
    item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH &&
    (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) != 0U;
}

static int source_quality_structured_data_item_is_absolute_long_lookup_table(
    const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
    item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH &&
    (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) != 0U;
}

static const M68kDecodeSectionIR *source_quality_decode_section_by_index(const M68kDecodeIR *decode,
    uint32_t section_index, size_t *out_decode_index) {
  size_t index;
  if (out_decode_index != NULL) *out_decode_index = 0U;
  if (decode == NULL) return NULL;
  for (index = 0U; index < decode->section_count; ++index) {
    if (decode->sections[index].section_index == section_index) {
      if (out_decode_index != NULL) *out_decode_index = index;
      return &decode->sections[index];
    }
  }
  return NULL;
}

static int source_quality_candidate_is_accepted_start(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate) {
  return section != NULL && candidate != NULL && candidate->byte_count != 0U &&
    accepted_start != NULL && candidate->offset < section->size && accepted_start[candidate->offset] != 0U;
}

static int source_quality_target_is_control_symbol_access(const M68kDecodeTarget *target) {
  return target != NULL &&
    (target->kind == M68K_DECODE_TARGET_BRANCH ||
     target->kind == M68K_DECODE_TARGET_CALL ||
     target->kind == M68K_DECODE_TARGET_JUMP);
}

static int source_quality_operand_has_intrinsic_control_label(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) return 1;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->value.ea_mode == 7U && (operand->value.ea_reg == 2U || operand->value.ea_reg == 3U);
}

static int source_quality_relocation_exactly_covers_span(const M68kFact *fact,
    size_t section_index, uint32_t span_start, uint32_t span_size) {
  uint32_t span_end;
  uint32_t fact_end;
  if (fact == NULL || fact->kind != M68K_FACT_RELOCATION_REF ||
      fact->section_index != section_index || fact->size == 0U || span_size == 0U) {
    return 0;
  }
  if (span_start > UINT32_MAX - span_size || fact->offset > UINT32_MAX - fact->size) return 0;
  span_end = span_start + span_size;
  fact_end = fact->offset + fact->size;
  return fact->offset == span_start && fact_end == span_end;
}

static int source_quality_operand_has_relocation_ref(const M68kFactIR *facts,
    size_t section_index, const M68kDecodeCandidate *candidate, size_t operand_index) {
  uint32_t span_start = 0U;
  uint32_t span_size = 0U;
  size_t fact_index;
  if (facts == NULL || candidate == NULL) return 0;
  if (!m68k_decode_candidate_operand_storage_span(candidate, operand_index, &span_start, &span_size)) return 0;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    if (source_quality_relocation_exactly_covers_span(&facts->facts[fact_index], section_index,
        span_start, span_size)) {
      return 1;
    }
  }
  return 0;
}

static const M68kFact *source_quality_unique_relocation_ref_for_operand(const M68kFactIR *facts,
    size_t section_index, const M68kDecodeCandidate *candidate, size_t operand_index) {
  const M68kFact *match = NULL;
  uint32_t span_start = 0U;
  uint32_t span_size = 0U;
  size_t fact_index;
  if (facts == NULL || candidate == NULL) return NULL;
  if (!m68k_decode_candidate_operand_storage_span(candidate, operand_index, &span_start, &span_size)) return NULL;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    if (!source_quality_relocation_exactly_covers_span(fact, section_index, span_start, span_size)) continue;
    if (match != NULL) return NULL;
    match = fact;
  }
  return match;
}

static const M68kDecodeTarget *source_quality_control_target_for_operand(const M68kDecodeCandidate *candidate,
    size_t operand_index) {
  size_t target_index;
  const M68kDecodeTarget *unique_unindexed_target = NULL;
  size_t unique_unindexed_count = 0U;
  if (candidate == NULL) return NULL;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (!source_quality_target_is_control_symbol_access(target)) continue;
    if (target->has_operand) {
      if (target->operand_index == operand_index) return target;
      continue;
    }
    unique_unindexed_target = target;
    ++unique_unindexed_count;
  }
  return unique_unindexed_count == 1U ? unique_unindexed_target : NULL;
}

static int source_quality_append_expected_branch_symbol_access(M68kSectionAnalysisIR *source_section_analysis,
    const M68kSymbolOriginIR *origin, const M68kDecodeCandidate *candidate, uint32_t target_section_index,
    uint32_t target_offset, uint32_t operand_index) {
  M68kExpectedSymbolAccessIR access;
  if (source_section_analysis == NULL || origin == NULL || candidate == NULL) {
    return -1;
  }
  memset(&access, 0, sizeof(access));
  access.symbol_name = origin->symbol_name;
  access.producer = "relocated_branch";
  access.offset = candidate->offset;
  access.target_section_index = target_section_index;
  access.target_offset = target_offset;
  access.operand_index = operand_index;
  access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_BRANCH_TARGET;
  access.confidence = origin->confidence;
  access.has_target = 1U;
  return m68k_ir_section_analysis_append_expected_symbol_access(source_section_analysis, &access);
}

static int source_quality_append_expected_operand_symbol_access(M68kSectionAnalysisIR *source_section_analysis,
    const M68kSymbolOriginIR *origin, const M68kDecodeCandidate *candidate, uint32_t target_section_index,
    uint32_t target_offset, uint32_t operand_index) {
  M68kExpectedSymbolAccessIR access;
  if (source_section_analysis == NULL || origin == NULL || candidate == NULL) {
    return -1;
  }
  memset(&access, 0, sizeof(access));
  access.symbol_name = origin->symbol_name;
  access.producer = "data_operand";
  access.offset = candidate->offset;
  access.target_section_index = target_section_index;
  access.target_offset = target_offset;
  access.operand_index = operand_index;
  access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_OPERAND;
  access.confidence = origin->confidence;
  access.has_target = 1U;
  return m68k_ir_section_analysis_append_expected_symbol_access(source_section_analysis, &access);
}

static int source_quality_append_expected_equate_symbol_access(M68kSectionAnalysisIR *source_section_analysis,
    const char *symbol_name, uint32_t offset, uint32_t operand_index) {
  M68kExpectedSymbolAccessIR access;
  if (source_section_analysis == NULL || symbol_name == NULL || symbol_name[0] == '\0') return -1;
  memset(&access, 0, sizeof(access));
  access.symbol_name = (char *)symbol_name;
  access.producer = "manual_equate";
  access.offset = offset;
  access.operand_index = operand_index;
  access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_EQUATE;
  access.confidence = M68K_FACT_CONFIDENCE_REQUIRED;
  return m68k_ir_section_analysis_append_expected_symbol_access(source_section_analysis, &access);
}

static int append_expected_relocated_branch_symbol_accesses_for_section(M68kSourceAnalysisIR *source_analysis,
    M68kSectionAnalysisIR *section_analysis, const M68kDecodeIR *decode, const M68kDecodeSectionIR *section,
    const M68kFactIR *facts, const uint8_t *source_accepted_start, uint8_t *const *accepted_start) {
  size_t candidate_index;
  if (source_analysis == NULL || section_analysis == NULL || decode == NULL || section == NULL ||
      source_accepted_start == NULL || accepted_start == NULL) {
    return -1;
  }
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    size_t operand_index;
    if (!source_quality_candidate_is_accepted_start(section, source_accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
      const M68kFact *relocation;
      const M68kDecodeTarget *control_target;
      const M68kDecodeSectionIR *target_decode_section;
      M68kSectionAnalysisIR *target_section_analysis;
      const M68kSymbolOriginIR *origin;
      size_t target_decode_index = 0U;
      control_target = source_quality_control_target_for_operand(candidate, operand_index);
      if (control_target == NULL) continue;
      relocation = source_quality_unique_relocation_ref_for_operand(facts, section->section_index, candidate,
        operand_index);
      if (relocation == NULL || relocation->target_section_index > UINT32_MAX) continue;
      target_decode_section = source_quality_decode_section_by_index(decode,
        (uint32_t)relocation->target_section_index, &target_decode_index);
      if (target_decode_section == NULL || accepted_start[target_decode_index] == NULL ||
          relocation->target_offset >= target_decode_section->size ||
          accepted_start[target_decode_index][relocation->target_offset] == 0U) {
        continue;
      }
      target_section_analysis = source_analysis_section_by_index(source_analysis,
        (uint32_t)relocation->target_section_index);
      if (target_section_analysis == NULL) continue;
      origin = source_quality_symbol_origin_at(target_section_analysis, relocation->target_offset);
      if (origin == NULL) continue;
      if (source_quality_append_expected_branch_symbol_access(section_analysis, origin, candidate,
          (uint32_t)relocation->target_section_index, relocation->target_offset, (uint32_t)operand_index) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int append_expected_label_statement_symbol_accesses_for_section(M68kSectionAnalysisIR *section_analysis) {
  size_t label_index;
  if (section_analysis == NULL) return -1;
  for (label_index = 0U; label_index < section_analysis->label_count; ++label_index) {
    const uint32_t offset = section_analysis->label_offsets[label_index];
    const M68kSymbolOriginIR *origin = source_quality_symbol_origin_at(section_analysis, offset);
    M68kExpectedSymbolAccessIR access;
    if (origin == NULL) continue;
    memset(&access, 0, sizeof(access));
    access.symbol_name = origin->symbol_name;
    access.producer = "label_statement";
    access.offset = offset;
    access.target_section_index = (uint32_t)section_analysis->section_index;
    access.target_offset = offset;
    access.operand_index = UINT32_MAX;
    access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_LABEL_STATEMENT;
    access.confidence = origin->confidence;
    access.has_target = 1U;
    if (m68k_ir_section_analysis_append_expected_symbol_access(section_analysis, &access) != 0) return -1;
  }
  return 0;
}

static int append_expected_label_statement_symbol_accesses(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    if (append_expected_label_statement_symbol_accesses_for_section(
        &source_analysis->sections[section_index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_expected_intrinsic_branch_symbol_accesses_for_section(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeSectionIR *section, const M68kFactIR *facts, const uint8_t *accepted_start) {
  size_t candidate_index;
  if (section_analysis == NULL || section == NULL) return -1;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    size_t target_index;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      const M68kSymbolOriginIR *origin;
      M68kExpectedSymbolAccessIR access;
      if (!source_quality_target_is_control_symbol_access(target) || !target->has_section ||
          target->section_index != section->section_index || !target->has_operand ||
          target->operand_index >= instruction.operand_count ||
          target->offset >= section->size || accepted_start == NULL ||
          accepted_start[target->offset] == 0U ||
          source_quality_operand_has_relocation_ref(facts, section->section_index, candidate,
            target->operand_index) ||
          !source_quality_operand_has_intrinsic_control_label(&instruction.operands[target->operand_index])) {
        continue;
      }
      origin = source_quality_symbol_origin_at(section_analysis, target->offset);
      if (origin == NULL) continue;
      memset(&access, 0, sizeof(access));
      access.symbol_name = origin->symbol_name;
      access.producer = "intrinsic_branch";
      access.offset = candidate->offset;
      access.target_section_index = (uint32_t)target->section_index;
      access.target_offset = target->offset;
      access.operand_index = (uint32_t)target->operand_index;
      access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_BRANCH_TARGET;
      access.confidence = origin->confidence;
      access.has_target = 1U;
      if (m68k_ir_section_analysis_append_expected_symbol_access(section_analysis, &access) != 0) return -1;
    }
  }
  return 0;
}

static int append_expected_intrinsic_branch_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    if (section == NULL) continue;
    if (append_expected_intrinsic_branch_symbol_accesses_for_section(section_analysis, section, facts,
        accepted_start[decode_index]) != 0) {
      return -1;
    }
    if (append_expected_relocated_branch_symbol_accesses_for_section(source_analysis, section_analysis, decode,
        section, facts, accepted_start[decode_index], accepted_start) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_expected_data_operand_symbol_accesses_for_section(M68kSourceAnalysisIR *source_analysis,
    M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start) {
  size_t candidate_index;
  if (source_analysis == NULL || section_analysis == NULL || section == NULL) return -1;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    size_t target_index;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      M68kSectionAnalysisIR *target_section_analysis;
      const M68kSymbolOriginIR *origin;
      if (target->kind != M68K_DECODE_TARGET_DATA || !target->has_section || !target->has_operand ||
          target->operand_index >= candidate->operand_count || target->section_index > UINT32_MAX) {
        continue;
      }
      target_section_analysis = source_analysis_section_by_index(source_analysis, (uint32_t)target->section_index);
      if (target_section_analysis == NULL) continue;
      origin = source_quality_symbol_origin_at(target_section_analysis, target->offset);
      if (origin == NULL) continue;
      if (source_quality_append_expected_operand_symbol_access(section_analysis, origin, candidate,
          (uint32_t)target->section_index, target->offset, (uint32_t)target->operand_index) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int append_expected_data_operand_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    if (section == NULL) continue;
    if (append_expected_data_operand_symbol_accesses_for_section(source_analysis, section_analysis, section,
        accepted_start[decode_index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static int source_quality_operand_absolute_offset(const M68kOperandIR *operand, uint32_t *out_offset) {
  if (out_offset != NULL) *out_offset = 0U;
  if (operand == NULL) return 0;
  return m68k_asm_operand_absolute_value(operand->kind, &operand->value, out_offset);
}

static int source_quality_operand_address_register_index(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (out_reg != NULL) *out_reg = 0U;
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

static int source_quality_observation_is_stack_top_symbol_operand(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, const M68kAddressObservationIR *observation) {
  uint8_t dest_reg = 0U;
  uint32_t value = 0U;
  if (instruction == NULL || metadata == NULL || observation == NULL ||
      observation->operand_index >= instruction->operand_count ||
      metadata->source_operand_index != observation->operand_index ||
      metadata->dest_operand_index >= instruction->operand_count ||
      (metadata->operation_type != M68K_SIM_OP_MOVE &&
       metadata->operation_class != M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS) ||
      metadata->operand_access_kinds[metadata->dest_operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE ||
      !source_quality_operand_address_register_index(&instruction->operands[metadata->dest_operand_index],
        &dest_reg) ||
      dest_reg != 7U) {
    return 0;
  }
  if (!m68k_ir_operand_immediate_value(&instruction->operands[observation->operand_index], &value) &&
      !source_quality_operand_absolute_offset(&instruction->operands[observation->operand_index], &value)) {
    return 0;
  }
  return value == observation->address && value != 0U &&
    m68k_cpu_find_exception_vector_by_address(value) == NULL &&
    amiga_os_find_hardware_base_symbol_by_address(value) == NULL &&
    amiga_os_find_hardware_register_by_cpu_address(value) == NULL &&
    amiga_os_find_hardware_register_field_by_cpu_address(value) == NULL &&
    amiga_os_find_hardware_register_range_by_cpu_address(value) == NULL;
}

static int source_quality_observation_has_bitmap_runtime_comment_owner(
    const M68kSectionAnalysisIR *section, const M68kAddressObservationIR *observation) {
  size_t index;
  if (section == NULL || observation == NULL || !observation->has_address) return 0;
  for (index = 0U; index < section->runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[index];
    if (ref->offset == observation->offset &&
        ref->has_runtime_address &&
        ref->runtime_address == observation->address &&
        (ref->data_class_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) != 0U) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_observation_requires_rendered_absolute_symbol(
    const M68kSectionAnalysisIR *section, const M68kDecodeCandidate *candidate,
    const M68kAddressObservationIR *observation) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint32_t address = 0U;
  if (candidate == NULL || observation == NULL ||
      observation->symbol_name == NULL || observation->symbol_name[0] == '\0' ||
      observation->source != M68K_ADDRESS_OBSERVATION_SOURCE_ABSOLUTE_OPERAND ||
      observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY ||
      observation->conflicted != 0U ||
      observation->conflict_state != M68K_ANALYSIS_CONFLICT_STATE_CLEAN ||
      observation->operand_index == UINT32_MAX ||
      observation->offset != candidate->offset ||
      observation->operand_index >= candidate->operand_count ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      observation->operand_index >= instruction.operand_count ||
      !source_quality_operand_absolute_offset(&instruction.operands[observation->operand_index], &address) ||
      address != observation->address) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || observation->operand_index >= 4U ||
      metadata->operand_access_kinds[observation->operand_index] != observation->access_kind) {
    return 0;
  }
  if (source_quality_observation_is_stack_top_symbol_operand(&instruction, metadata, observation)) {
    return 0;
  }
  if (source_quality_observation_has_bitmap_runtime_comment_owner(section, observation)) {
    return 0;
  }
  if ((observation->access_kind == M68K_SIM_ACCESS_MEMORY_READ ||
       observation->access_kind == M68K_SIM_ACCESS_MEMORY_WRITE) &&
      observation->access_width != 0U &&
      observation->address < 0x10000U) {
    return 1;
  }
  return observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS;
}

static const M68kSymbolOriginIR *source_quality_section_storage_observation_origin(
    M68kSourceAnalysisIR *source_analysis, const M68kSectionAnalysisIR *section,
    const M68kDecodeCandidate *candidate, const M68kAddressObservationIR *observation,
    uint32_t *out_target_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  M68kSectionAnalysisIR *target_section;
  uint32_t target_offset;
  uint32_t address = 0U;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (source_analysis == NULL || candidate == NULL || observation == NULL ||
      observation->source != M68K_ADDRESS_OBSERVATION_SOURCE_ABSOLUTE_OPERAND ||
      observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_SECTION_STORAGE ||
      observation->conflicted != 0U ||
      observation->conflict_state != M68K_ANALYSIS_CONFLICT_STATE_CLEAN ||
      !observation->has_target ||
      observation->operand_index == UINT32_MAX ||
      observation->offset != candidate->offset ||
      observation->operand_index >= candidate->operand_count ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      observation->operand_index >= instruction.operand_count ||
      !source_quality_operand_absolute_offset(&instruction.operands[observation->operand_index], &address) ||
      address != observation->address) {
    return NULL;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || observation->operand_index >= 4U ||
      metadata->operand_access_kinds[observation->operand_index] != observation->access_kind) {
    return NULL;
  }
  if (observation->access_kind != M68K_SIM_ACCESS_MEMORY_READ &&
      observation->access_kind != M68K_SIM_ACCESS_MEMORY_WRITE &&
      observation->access_kind != M68K_SIM_ACCESS_COMPUTE_ADDRESS) {
    return NULL;
  }
  if (source_quality_observation_is_stack_top_symbol_operand(&instruction, metadata, observation) ||
      source_quality_observation_has_bitmap_runtime_comment_owner(section, observation)) {
    return NULL;
  }
  target_section = source_analysis_section_by_index(source_analysis, observation->target_section_index);
  target_offset = observation->target_offset;
  if (observation->address != observation->target_offset) {
    target_offset = observation->address;
  }
  if (out_target_offset != NULL) *out_target_offset = target_offset;
  return source_quality_symbol_origin_at(target_section, target_offset);
}

static const M68kAddressObservationIR *source_quality_address_observation_for_candidate_operand(
    const M68kSectionAnalysisIR *section, const M68kDecodeCandidate *candidate, size_t operand_index) {
  size_t index;
  if (section == NULL || candidate == NULL || operand_index > UINT32_MAX) return NULL;
  for (index = 0U; index < section->address_observation_count; ++index) {
    const M68kAddressObservationIR *observation = &section->address_observations[index];
    if (observation->offset == candidate->offset &&
        observation->operand_index == (uint32_t)operand_index) {
      return observation;
    }
  }
  return NULL;
}

static int append_expected_address_observation_symbol_accesses_for_section(M68kSectionAnalysisIR *section_analysis,
    M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section, const uint8_t *accepted_start) {
  size_t candidate_index;
  if (section_analysis == NULL || source_analysis == NULL || section == NULL) return -1;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    size_t operand_index;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
      const M68kAddressObservationIR *observation =
        source_quality_address_observation_for_candidate_operand(section_analysis, candidate, operand_index);
      const M68kSymbolOriginIR *section_storage_origin = NULL;
      uint32_t section_storage_target_offset = 0U;
      int requires_absolute_symbol =
        source_quality_observation_requires_rendered_absolute_symbol(section_analysis, candidate, observation);
      M68kExpectedSymbolAccessIR access;
      if (!requires_absolute_symbol) {
        section_storage_origin = source_quality_section_storage_observation_origin(source_analysis, section_analysis,
          candidate, observation, &section_storage_target_offset);
      }
      if (section_storage_origin == NULL && !requires_absolute_symbol) {
        continue;
      }
      memset(&access, 0, sizeof(access));
      access.symbol_name = section_storage_origin != NULL ? section_storage_origin->symbol_name :
        observation->symbol_name;
      access.producer = section_storage_origin != NULL ? "section_storage_address_observation" :
        "absolute_address_observation";
      access.offset = observation->offset;
      access.operand_index = observation->operand_index;
      access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_OPERAND;
      access.confidence = section_storage_origin != NULL ? section_storage_origin->confidence : observation->confidence;
      if (section_storage_origin != NULL || observation->has_target) {
        access.target_section_index = observation->target_section_index;
        access.target_offset = section_storage_origin != NULL ? section_storage_target_offset :
          observation->target_offset;
        access.has_target = 1U;
      }
      if (m68k_ir_section_analysis_append_expected_symbol_access(section_analysis, &access) != 0) return -1;
    }
  }
  return 0;
}

static int append_expected_address_observation_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  if (decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    if (section == NULL) continue;
    if (append_expected_address_observation_symbol_accesses_for_section(section_analysis, source_analysis, section,
        accepted_start[decode_index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_expected_manual_equate_symbol_accesses(M68kSourceAnalysisIR *source_analysis) {
  const M68kAnalysisPolicy *policy;
  uint16_t index;
  if (source_analysis == NULL) return -1;
  policy = &source_analysis->policy;
  for (index = 0U; index < policy->manual_representation_count &&
       index < M68K_ANALYSIS_MANUAL_REPRESENTATION_LIMIT; ++index) {
    const M68kAnalysisManualRepresentation *representation = &policy->manual_representations[index];
    const M68kAnalysisTargetEquate *equate;
    M68kSectionAnalysisIR *section_analysis;
    if (!representation->has_section_index || !representation->has_operand_index ||
        representation->style_id != M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL ||
        representation->target_equate_index == 0U ||
        representation->target_equate_index > policy->target_equate_count ||
        representation->target_equate_index > M68K_ANALYSIS_TARGET_EQUATE_LIMIT) {
      continue;
    }
    equate = &policy->target_equates[representation->target_equate_index - 1U];
    section_analysis = source_analysis_section_by_index(source_analysis, representation->section_index);
    if (section_analysis == NULL) continue;
    if (source_quality_append_expected_equate_symbol_access(section_analysis, equate->name,
        representation->offset, representation->operand_index) != 0) {
      return -1;
    }
  }
  return 0;
}

static uint8_t source_quality_immediate_text_token_width_for_candidate(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction) {
  char suffix;
  if (instruction != NULL &&
      (instruction->size_suffix == 'b' || instruction->size_suffix == 'w' ||
       instruction->size_suffix == 'l')) {
    suffix = instruction->size_suffix;
  } else {
    suffix = m68k_decode_candidate_effective_size_suffix(candidate);
  }
  if (suffix == 'b') return 1U;
  if (suffix == 'w') return 2U;
  if (suffix == 'l') return 4U;
  return 0U;
}

static int source_quality_immediate_text_token_bytes(uint32_t value, uint8_t width, char *out_text,
    uint8_t *out_text_length) {
  uint8_t index;
  int saw_non_space = 0;
  if (out_text == NULL || out_text_length == NULL || width == 0U || width > 4U) return 0;
  for (index = 0U; index < width; ++index) {
    uint8_t shift = (uint8_t)((width - 1U - index) * 8U);
    uint8_t byte = (uint8_t)((value >> shift) & 0xFFU);
    if (!m68k_ir_byte_is_quoted_string_safe(byte)) return 0;
    if (byte != ' ') saw_non_space = 1;
    out_text[index] = (char)byte;
  }
  if (!saw_non_space) return 0;
  out_text[width] = '\0';
  *out_text_length = width;
  return 1;
}

static int append_immediate_text_tokens_for_section(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    M68kSectionAnalysisIR *section_analysis) {
  size_t candidate_index;
  if (section == NULL || accepted_start == NULL || section_analysis == NULL) return 0;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    uint8_t width;
    size_t operand_index;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    width = source_quality_immediate_text_token_width_for_candidate(candidate, &instruction);
    if (width == 0U) continue;
    for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
      M68kImmediateTextTokenIR token;
      uint32_t value;
      if (!m68k_ir_operand_immediate_value(&instruction.operands[operand_index], &value)) continue;
      memset(&token, 0, sizeof(token));
      if (!source_quality_immediate_text_token_bytes(value, width, token.text, &token.text_length)) continue;
      token.source_offset = candidate->offset;
      token.operand_index = (uint8_t)operand_index;
      token.width = width;
      token.value = value;
      token.evidence_flags =
        M68K_IMMEDIATE_TEXT_TOKEN_EVIDENCE_ACCEPTED_INSTRUCTION |
        M68K_IMMEDIATE_TEXT_TOKEN_EVIDENCE_PRINTABLE_BYTES;
      if (m68k_ir_section_analysis_append_immediate_text_token(section_analysis, &token) != 0) return -1;
    }
  }
  return 0;
}

static int append_immediate_text_tokens(M68kSourceAnalysisIR *source_analysis, const M68kDecodeIR *decode,
    uint8_t *const *accepted_start) {
  size_t index;
  if (source_analysis == NULL) return -1;
  if (decode == NULL || accepted_start == NULL) return 0;
  for (index = 0U; index < source_analysis->section_count; ++index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[index];
    const M68kDecodeSectionIR *section;
    size_t decode_index = 0U;
    section = source_quality_decode_section_by_index(decode, (uint32_t)section_analysis->section_index,
      &decode_index);
    if (section == NULL) continue;
    if (append_immediate_text_tokens_for_section(section, accepted_start[decode_index], section_analysis) != 0)
      return -1;
  }
  return 0;
}

static int source_quality_runtime_view_maps_address(const M68kRuntimeViewIR *view, uint32_t runtime_address,
    uint32_t section_size, uint32_t *out_source_offset) {
  uint32_t delta;
  uint32_t source_offset;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (view == NULL || !view->materialized || runtime_address < view->runtime_address) return 0;
  delta = runtime_address - view->runtime_address;
  if (delta >= view->size || view->storage_offset > UINT32_MAX - delta) return 0;
  source_offset = view->storage_offset + delta;
  if (source_offset >= section_size) return 0;
  if (out_source_offset != NULL) *out_source_offset = source_offset;
  return 1;
}

static int source_quality_source_logical_address(const M68kSectionAnalysisIR *section, uint32_t source_offset,
    uint32_t *out_logical_address) {
  size_t index;
  if (out_logical_address == NULL) return 0;
  if (section != NULL) {
    for (index = 0U; index < section->runtime_view_count; ++index) {
      const M68kRuntimeViewIR *view = &section->runtime_views[index];
      uint32_t delta;
      if (!view->materialized || source_offset < view->storage_offset) continue;
      delta = source_offset - view->storage_offset;
      if (delta >= view->size || view->runtime_address > UINT32_MAX - delta) continue;
      *out_logical_address = view->runtime_address + delta;
      return 1;
    }
  }
  *out_logical_address = source_offset;
  return 1;
}

static int source_quality_section_has_label_at(const M68kSectionAnalysisIR *section, uint32_t offset) {
  size_t index;
  if (section == NULL) return 0;
  if (section->label_offset_lookup != NULL && offset < section->label_offset_lookup_size) {
    return section->label_offset_lookup[offset] != 0U;
  }
  for (index = 0U; index < section->label_count; ++index) {
    if (section->label_offsets[index] == offset) return 1;
  }
  return 0;
}

static int source_quality_any_runtime_address_source_offset(const M68kSectionAnalysisIR *section,
    uint32_t runtime_address, uint32_t section_size, uint32_t *out_source_offset) {
  size_t index;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (section == NULL) return 0;
  for (index = 0U; index < section->runtime_view_count; ++index) {
    if (source_quality_runtime_view_maps_address(&section->runtime_views[index], runtime_address, section_size,
        out_source_offset)) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_exact_pointer_value_label_offset(const M68kSectionAnalysisIR *section,
    uint32_t section_size, uint32_t value, uint8_t allow_in_section_source_offset, uint32_t *out_source_offset) {
  size_t index;
  uint32_t logical_address = 0U;
  int value_is_in_section_source_offset = 0;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (section == NULL) return 0;
  for (index = 0U; index < section->runtime_view_count; ++index) {
    uint32_t source_offset = 0U;
    if (!source_quality_runtime_view_maps_address(&section->runtime_views[index], value, section_size,
        &source_offset)) {
      continue;
    }
    if (!source_quality_source_logical_address(section, source_offset, &logical_address) ||
        logical_address != value) {
      continue;
    }
    if (out_source_offset != NULL) *out_source_offset = source_offset;
    return 1;
  }
  if (value < section_size && source_quality_source_logical_address(section, value, &logical_address)) {
    value_is_in_section_source_offset = 1;
    if (allow_in_section_source_offset ||
        (logical_address == value && source_quality_section_has_label_at(section, value))) {
      if (out_source_offset != NULL) *out_source_offset = value;
      return 1;
    }
  }
  if (!value_is_in_section_source_offset &&
      source_quality_any_runtime_address_source_offset(section, value, section_size, out_source_offset)) {
    return 1;
  }
  return 0;
}

static uint8_t source_quality_code_table_target_status(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const uint8_t *accepted_bytes, uint32_t target_offset,
    uint8_t *out_conflict_state) {
  if (out_conflict_state != NULL) *out_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
  if (section == NULL || target_offset >= section->size) {
    if (out_conflict_state != NULL) *out_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED_CODE_TARGET;
    return M68K_TABLE_ENTRY_TARGET_STATUS_UNRESOLVED_TARGET;
  }
  if (accepted_start != NULL && accepted_start[target_offset] != 0U) {
    return M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET;
  }
  if (accepted_bytes != NULL && accepted_bytes[target_offset] != 0U) {
    if (out_conflict_state != NULL) *out_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED_CODE_TARGET;
    return M68K_TABLE_ENTRY_TARGET_STATUS_INTERIOR_CODE_TARGET;
  }
  if (out_conflict_state != NULL) *out_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED_CODE_TARGET;
  return M68K_TABLE_ENTRY_TARGET_STATUS_UNRESOLVED_TARGET;
}

static uint32_t source_quality_data_reference_evidence_for_table_kind(uint8_t table_kind_id) {
  uint32_t flags = M68K_DATA_REFERENCE_EVIDENCE_TABLE_ENTRY;
  if (table_kind_id == M68K_ANALYSIS_TABLE_KIND_POINTER) flags |= M68K_DATA_REFERENCE_EVIDENCE_POINTER_TABLE;
  if (table_kind_id == M68K_ANALYSIS_TABLE_KIND_RELATIVE_DATA_LOOKUP)
    flags |= M68K_DATA_REFERENCE_EVIDENCE_RELATIVE_DATA_LOOKUP;
  return flags;
}

static uint32_t source_quality_target_role_flags_for_structured_item(const M68kAnalysisStructuredDataItem *item) {
  uint32_t flags = item != NULL ? item->semantic_role_flags : 0U;
  if (item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING) {
    flags |= M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING;
  }
  return flags;
}

static uint32_t source_quality_data_reference_target_evidence(uint32_t target_role_flags) {
  uint32_t flags = 0U;
  if (target_role_flags == 0U) return flags;
  flags |= M68K_DATA_REFERENCE_EVIDENCE_STRUCTURED_TARGET;
  if ((target_role_flags & (M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_MACOS_SYMBOL_STRING |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING_CONTROL_STREAM)) != 0U) {
    flags |= M68K_DATA_REFERENCE_EVIDENCE_TEXT_TARGET;
  }
  if ((target_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING) != 0U) {
    flags |= M68K_DATA_REFERENCE_EVIDENCE_STRING_TARGET;
  }
  return flags;
}

static const M68kAnalysisStructuredDataItem *source_quality_structured_data_item_covering_offset(
    const M68kSourceAnalysisIR *source_analysis, uint32_t section_index, uint32_t offset) {
  size_t index;
  if (source_analysis == NULL) return NULL;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    if (!item->has_section_index || item->section_index != section_index || item->offset > offset) continue;
    if (item->size == 0U || item->offset > UINT32_MAX - item->size) continue;
    if (offset < item->offset + item->size) return item;
  }
  return NULL;
}

static int append_structured_data_reference_for_table_entry(M68kSourceAnalysisIR *source_analysis,
    M68kSectionAnalysisIR *section_analysis, const M68kAnalysisStructuredDataItem *item,
    const M68kTableEntryIR *entry) {
  const M68kAnalysisStructuredDataItem *target_item;
  M68kDataReferenceIR ref;
  if (source_analysis == NULL || section_analysis == NULL || item == NULL || entry == NULL || !entry->has_target)
    return -1;
  if (entry->target_status != M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET) return 0;
  if (item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH ||
      item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH) {
    return 0;
  }
  memset(&ref, 0, sizeof(ref));
  ref.source_offset = item->has_consumer ? item->consumer_offset : entry->entry_offset;
  ref.source_kind = M68K_DATA_REFERENCE_SOURCE_TABLE_ENTRY;
  ref.table_kind_id = item->table_kind_id;
  ref.source_pattern_id = item->source_pattern_id;
  ref.target_status = entry->target_status;
  ref.conflict_state = entry->conflict_state;
  target_item = source_quality_structured_data_item_covering_offset(source_analysis, entry->target_section_index,
    entry->target_offset);
  if (target_item != NULL) {
    ref.target_kind = target_item->kind;
    ref.target_table_kind_id = target_item->table_kind_id;
    ref.target_source_pattern_id = target_item->source_pattern_id;
    ref.target_role_flags = source_quality_target_role_flags_for_structured_item(target_item);
  }
  ref.evidence_flags = source_quality_data_reference_evidence_for_table_kind(item->table_kind_id) |
    M68K_DATA_REFERENCE_EVIDENCE_ACCEPTED_TARGET |
    source_quality_data_reference_target_evidence(ref.target_role_flags);
  ref.table_start_offset = item->offset;
  ref.table_entry_index = entry->entry_index;
  ref.table_entry_offset = entry->entry_offset;
  ref.table_entry_size = entry->entry_size;
  ref.raw_value = entry->raw_value;
  ref.target_section_index = entry->target_section_index;
  ref.target_offset = entry->target_offset;
  return m68k_ir_section_analysis_append_data_reference(section_analysis, &ref);
}

static int append_structured_data_table_entry_target(M68kSourceAnalysisIR *source_analysis,
    M68kSectionAnalysisIR *section_analysis, const M68kAnalysisStructuredDataItem *item, uint32_t entry_index,
    uint32_t entry_offset, uint32_t entry_size, uint32_t raw_value, uint8_t raw_value_width,
    int64_t target_offset, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const uint8_t *accepted_bytes) {
  M68kTableEntryIR entry;
  uint8_t conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
  if (source_analysis == NULL || section_analysis == NULL || item == NULL || target_offset < 0 ||
      target_offset > UINT32_MAX) {
    return 0;
  }
  memset(&entry, 0, sizeof(entry));
  entry.table_start_offset = item->offset;
  entry.entry_index = entry_index;
  entry.entry_offset = entry_offset;
  entry.entry_size = entry_size;
  entry.raw_value = raw_value;
  entry.raw_value_width = raw_value_width;
  entry.table_kind_id = item->table_kind_id;
  entry.source_pattern_id = item->source_pattern_id;
  entry.has_target = 1U;
  entry.target_section_index = item->target_section;
  entry.target_offset = (uint32_t)target_offset;
  if (item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH ||
      item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH) {
    if (section != NULL && item->target_section == section->section_index) {
      entry.target_status = source_quality_code_table_target_status(section, accepted_start, accepted_bytes,
        (uint32_t)target_offset, &conflict_state);
    } else {
      entry.target_status = M68K_TABLE_ENTRY_TARGET_STATUS_UNRESOLVED_TARGET;
      conflict_state = M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED_CODE_TARGET;
    }
  } else {
    entry.target_status = M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET;
  }
  entry.conflict_state = conflict_state;
  if (m68k_ir_section_analysis_append_table_entry(section_analysis, &entry) != 0) return -1;
  return append_structured_data_reference_for_table_entry(source_analysis, section_analysis, item, &entry);
}

static int append_structured_data_table_entry_numeric(M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisStructuredDataItem *item, uint32_t entry_index, uint32_t entry_offset,
    uint32_t entry_size, uint32_t raw_value, uint8_t raw_value_width) {
  M68kTableEntryIR entry;
  if (section_analysis == NULL || item == NULL) return -1;
  memset(&entry, 0, sizeof(entry));
  entry.table_start_offset = item->offset;
  entry.entry_index = entry_index;
  entry.entry_offset = entry_offset;
  entry.entry_size = entry_size;
  entry.raw_value = raw_value;
  entry.raw_value_width = raw_value_width;
  entry.table_kind_id = item->table_kind_id;
  entry.source_pattern_id = item->source_pattern_id;
  entry.target_status = M68K_TABLE_ENTRY_TARGET_STATUS_NUMERIC_EXACT;
  return m68k_ir_section_analysis_append_table_entry(section_analysis, &entry);
}

static int append_structured_data_table_entries_for_item(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const uint8_t *accepted_bytes,
    M68kSectionAnalysisIR *section_analysis, const M68kAnalysisStructuredDataItem *item) {
  uint32_t cursor;
  uint32_t entry_size;
  if (source_analysis == NULL || section == NULL || section_analysis == NULL || item == NULL ||
      section->data == NULL) {
    return -1;
  }
  entry_size = m68k_analysis_structured_data_table_entry_size(item);
  if (entry_size == 0U || item->size < entry_size || item->offset >= section->size) return 0;
  for (cursor = 0U; cursor + entry_size <= item->size && item->offset + cursor + entry_size <= section->size;
      cursor += entry_size) {
    uint32_t entry_index = cursor / entry_size;
    uint32_t entry_offset = item->offset + cursor;
    if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && item->has_target) {
      uint16_t raw_word = m68k_read_u16be(section->data + entry_offset);
      int64_t target_offset = (int64_t)item->target_offset + (int32_t)(int16_t)raw_word;
      if (append_structured_data_table_entry_target(source_analysis, section_analysis, item, entry_index,
          entry_offset, entry_size, raw_word, 2U, target_offset, section, accepted_start, accepted_bytes) != 0) {
        return -1;
      }
    } else if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
        source_quality_structured_data_item_is_keyed_long_relative_lookup_table(item)) {
      uint32_t raw_long = m68k_read_u32be(section->data + entry_offset);
      int64_t target_offset = (int64_t)item->target_offset + (int32_t)(int16_t)((raw_long >> 16U) & 0xFFFFU);
      if (append_structured_data_table_entry_target(source_analysis, section_analysis, item, entry_index,
          entry_offset, entry_size, raw_long, 4U, target_offset, section, accepted_start, accepted_bytes) != 0) {
        return -1;
      }
    } else if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
        (source_quality_structured_data_item_is_pointer_table(item) ||
         source_quality_structured_data_item_is_absolute_long_lookup_table(item))) {
      uint32_t raw_long = m68k_read_u32be(section->data + entry_offset);
      uint32_t target_offset = 0U;
      uint8_t allow_source_offset = source_quality_structured_data_item_is_absolute_long_lookup_table(item) ? 1U : 0U;
      if (raw_long != 0U &&
          source_quality_exact_pointer_value_label_offset(section_analysis, section->size, raw_long,
            allow_source_offset, &target_offset)) {
        if (append_structured_data_table_entry_target(source_analysis, section_analysis, item, entry_index,
            entry_offset, entry_size, raw_long, 4U, target_offset, section, accepted_start, accepted_bytes) != 0) {
          return -1;
        }
      } else if (append_structured_data_table_entry_numeric(section_analysis, item, entry_index, entry_offset,
          entry_size, raw_long, 4U) != 0) {
        return -1;
      }
    } else {
      uint32_t raw_value = entry_size == 1U ? section->data[entry_offset] :
        entry_size == 2U ? m68k_read_u16be(section->data + entry_offset) :
        m68k_read_u32be(section->data + entry_offset);
      if (append_structured_data_table_entry_numeric(section_analysis, item, entry_index, entry_offset,
          entry_size, raw_value, (uint8_t)entry_size) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int append_structured_data_table_entries(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, uint8_t *const *accepted_bytes) {
  size_t index;
  if (source_analysis == NULL) return -1;
  if (decode == NULL) return 0;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    M68kSectionAnalysisIR *section_analysis;
    const M68kDecodeSectionIR *section;
    const uint8_t *section_accepted_start = NULL;
    const uint8_t *section_accepted_bytes = NULL;
    size_t decode_index = 0U;
    uint32_t entry_size;
    if (!item->has_section_index || item->size == 0U ||
        item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN ||
        item->offset > UINT32_MAX - item->size) {
      continue;
    }
    entry_size = m68k_analysis_structured_data_table_entry_size(item);
    if (entry_size == 0U || item->size < entry_size) continue;
    section_analysis = source_analysis_section_by_index(source_analysis, item->section_index);
    section = source_quality_decode_section_by_index(decode, item->section_index, &decode_index);
    if (section_analysis == NULL || section == NULL) continue;
    if (accepted_start != NULL) section_accepted_start = accepted_start[decode_index];
    if (accepted_bytes != NULL) section_accepted_bytes = accepted_bytes[decode_index];
    if (append_structured_data_table_entries_for_item(source_analysis, section, section_accepted_start,
        section_accepted_bytes, section_analysis, item) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_accepted_runs_for_section(M68kSectionAnalysisIR *section,
    const M68kDecodeSectionIR *decode_section) {
  uint32_t cursor;
  if (section == NULL || section->certain_code_byte == NULL || section->certain_code_size == 0U) return 0;
  cursor = 0U;
  while ((size_t)cursor < section->certain_code_size) {
    M68kAcceptedCodeRunIR run;
    uint32_t start;
    if (section->certain_code_byte[cursor] == 0U) {
      ++cursor;
      continue;
    }
    start = cursor;
    while ((size_t)cursor < section->certain_code_size && section->certain_code_byte[cursor] != 0U) ++cursor;
    memset(&run, 0, sizeof(run));
    run.start_offset = start;
    run.end_offset = cursor;
    run.end_kind = (size_t)cursor >= section->certain_code_size ?
      M68K_ACCEPTED_CODE_RUN_END_SECTION_BOUNDARY : M68K_ACCEPTED_CODE_RUN_END_ACCEPTED_GAP;
    run.has_origin = (uint8_t)accepted_run_has_origin(section, start, cursor);
    (void)classify_run_end_from_decode(decode_section, start, cursor, &run);
    if (classify_run_end_from_cfg(section, start, cursor, &run) < 0) return -1;
    if (section->certain_code_start != NULL) {
      uint32_t offset;
      for (offset = start; offset < cursor && (size_t)offset < section->certain_code_size; ++offset) {
        if (section->certain_code_start[offset] != 0U) ++run.instruction_count;
      }
    }
    if (m68k_ir_section_analysis_append_accepted_code_run(section, &run) != 0) return -1;
    {
      uint32_t partial_offset;
      if (accepted_run_decode_coverage_gap(section, decode_section, &run, &partial_offset)) {
        if (append_run_offset_diagnostic(section, &run, partial_offset,
            M68K_SOURCE_QUALITY_DIAGNOSTIC_PARTIAL_CODE_BLOCK_DECODE,
            M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR, 1U,
            "accepted code run contains bytes not covered by decoded instructions",
            "accepted_code_run_decode_coverage") != 0) {
          return -1;
        }
      }
    }
    if (!accepted_run_has_executable_origin(section, start, cursor)) {
      if (append_run_diagnostic(section, &run,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_ACCEPTED_CODE_WITHOUT_EXECUTABLE_ORIGIN,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR, 1U,
          "accepted code run lacks non-fallthrough executable origin") != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int append_orphan_conflict_ranges_for_section(M68kSectionAnalysisIR *section) {
  size_t index;
  if (section == NULL) return -1;
  for (index = 0U; index < section->orphan_code_signal_count; ++index) {
    const M68kOrphanCodeSignalIR *signal = &section->orphan_code_signals[index];
    M68kRangeOwnershipIR range;
    if (signal->size == 0U || signal->nearby_data_relation == M68K_ORPHAN_CODE_SIGNAL_NEARBY_DATA_NONE)
      continue;
    memset(&range, 0, sizeof(range));
    range.start_offset = signal->offset;
    if (signal->offset > UINT32_MAX - signal->size) continue;
    range.end_offset = signal->offset + signal->size;
    range.kind = M68K_RANGE_OWNERSHIP_CONFLICT;
    range.status = M68K_RANGE_OWNERSHIP_STATUS_CONFLICT;
    range.positive_evidence_flags = M68K_RANGE_EVIDENCE_CODE_SHAPE;
    range.negative_evidence_flags = M68K_RANGE_NEGATIVE_MISSING_INBOUND |
      M68K_RANGE_NEGATIVE_STRUCTURED_DATA_OVERLAP;
    range.conflict_state = M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED;
    if (m68k_ir_section_analysis_append_range_ownership(section, &range) != 0) return -1;
  }
  return 0;
}

int m68k_source_quality_analyze(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    const M68kDecodeSectionIR *decode_section = NULL;
    if (decode != NULL && section->section_index <= UINT32_MAX) {
      decode_section = source_quality_decode_section_by_index(decode, (uint32_t)section->section_index, NULL);
    }
    if (append_code_origins_for_section(section) != 0) return -1;
    if (append_address_observations_for_section(section) != 0) return -1;
    if (append_platform_address_uses_for_section(section) != 0) return -1;
    if (append_accepted_runs_for_section(section, decode_section) != 0) return -1;
    if (append_accepted_code_range_ownerships_for_section(section) != 0) return -1;
    if (append_orphan_conflict_ranges_for_section(section) != 0) return -1;
  }
  if (append_expected_label_statement_symbol_accesses(source_analysis) != 0) return -1;
  if (append_expected_intrinsic_branch_symbol_accesses(source_analysis, decode, facts, accepted_start) != 0)
    return -1;
  if (append_expected_data_operand_symbol_accesses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_expected_manual_equate_symbol_accesses(source_analysis) != 0) return -1;
  if (append_structured_data_range_ownerships(source_analysis) != 0) return -1;
  if (append_accepted_run_noncode_fallthrough_diagnostics(source_analysis) != 0) return -1;
  if (append_structured_data_platform_semantic_uses(source_analysis) != 0) return -1;
  if (append_runtime_ref_platform_semantic_uses(source_analysis) != 0) return -1;
  if (append_structured_data_table_descriptors(source_analysis) != 0) return -1;
  if (append_structured_data_table_entries(source_analysis, decode, accepted_start, accepted_bytes) != 0) return -1;
  if (append_immediate_text_tokens(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_address_identities_and_ranges(source_analysis) != 0) return -1;
  if (append_expected_address_observation_symbol_accesses(source_analysis, decode, accepted_start) != 0) return -1;
  return 0;
}

int m68k_source_quality_analyze_rendered_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
    const M68kRenderEvidenceIR *render_evidence) {
  size_t section_index;
  if (source_analysis == NULL || render_evidence == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kRenderEvidenceSectionIR *render_evidence_section =
      m68k_ir_render_evidence_section_by_index(render_evidence,
        (uint32_t)source_analysis->sections[section_index].section_index);
    if (append_missing_expected_symbol_access_diagnostics_for_section(&source_analysis->sections[section_index],
        render_evidence_section) != 0) {
      return -1;
    }
    if (append_unreferenced_label_statement_diagnostics_for_section(source_analysis,
        &source_analysis->sections[section_index], render_evidence) != 0) {
      return -1;
    }
  }
  return 0;
}
