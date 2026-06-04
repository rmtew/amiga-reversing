#include "m68k_source_quality.h"

#include "m68k_fact_ir.h"
#include "m68k_bitset.h"
#include "m68k_instruction_spec.h"
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

static int code_origin_evidence_is_manual_seed(uint32_t evidence_kind) {
  return evidence_kind == M68K_CODE_ORIGIN_EVIDENCE_MANUAL_ACTION_LOG_ENTRY_POINT ||
    evidence_kind == M68K_CODE_ORIGIN_EVIDENCE_DECISION_JOURNAL_ENTRY_POINT;
}

static uint8_t code_origin_class_from_ref(const M68kCodeStartRefIR *ref) {
  if (ref == NULL) return M68K_CODE_ORIGIN_UNKNOWN;
  if (code_origin_evidence_is_manual_seed(ref->evidence_kind)) return M68K_CODE_ORIGIN_MANUAL_SEED;
  return code_origin_class_from_reason(ref->reason);
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
    origin.origin_class = code_origin_class_from_ref(ref);
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

static const char *platform_address_use_symbol_from_hardware_base_offset(uint16_t base_id, uint32_t offset,
    char *symbol_buf, size_t symbol_buf_size) {
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  if (symbol_buf != NULL && symbol_buf_size != 0U) symbol_buf[0] = '\0';
  if (base_id == AMIGA_OS_HARDWARE_BASE_ID_NONE) return NULL;
  hardware_field = amiga_os_find_hardware_register_field_by_base_id_offset(base_id, offset);
  if (hardware_field != NULL &&
      platform_amiga_format_hardware_register_field_symbol(hardware_field, 0, symbol_buf, symbol_buf_size)) {
    return symbol_buf;
  }
  hardware_register = amiga_os_find_hardware_register_by_base_id_offset(base_id, offset);
  if (hardware_register != NULL && hardware_register->symbol_name != NULL &&
      hardware_register->symbol_name[0] != '\0') {
    return hardware_register->symbol_name;
  }
  hardware_range = amiga_os_find_hardware_register_range_by_base_id_offset(base_id, offset);
  if (hardware_range != NULL &&
      platform_amiga_format_hardware_register_range_symbol(hardware_range, offset, 0, symbol_buf,
        symbol_buf_size)) {
    return symbol_buf;
  }
  return NULL;
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

static uint8_t address_identity_owner_from_observation(const M68kAddressObservationIR *observation) {
  if (observation == NULL) return M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN;
  if (observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR &&
      platform_address_use_shape_from_observation(observation) != M68K_PLATFORM_ADDRESS_USE_SHAPE_TRUE_VECTOR_INSTALL) {
    return M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY;
  }
  return observation->owner_kind;
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
    uint8_t owner_kind = address_identity_owner_from_observation(observation);
    identity->source_section_index = section_index;
    identity->source_offset = observation->offset;
    identity->absolute_address = observation->address;
    identity->has_absolute_address = observation->has_address;
    identity->owner_kind = owner_kind;
    identity->role_kind = address_identity_role_from_owner(owner_kind);
    identity->conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
    if (observation->source == M68K_ADDRESS_OBSERVATION_SOURCE_RUNTIME_ADDRESS_REF ||
        observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_RUNTIME_RANGE) {
      identity->runtime_address = observation->address;
      identity->has_runtime_address = 1U;
    }
  } else {
    uint8_t owner_kind = address_identity_owner_from_observation(observation);
    if (identity->owner_kind != owner_kind && owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN) {
      identity->conflicted = 1U;
      identity->conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CONFLICTED;
      ++identity->conflict_count;
    }
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
        code_origin_class_is_executable_proof(code_origin_class_from_ref(ref))) {
      return 1;
    }
  }
  return 0;
}

static int accepted_run_has_manual_origin(const M68kSectionAnalysisIR *section, uint32_t start, uint32_t end) {
  size_t index;
  if (section == NULL) return 0;
  for (index = 0U; index < section->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section->code_start_refs[index];
    if (ref->offset >= start && ref->offset < end && code_origin_evidence_is_manual_seed(ref->evidence_kind)) {
      return 1;
    }
  }
  return 0;
}

static uint8_t source_quality_kind_for_manual_run_conflict(const M68kSectionAnalysisIR *section,
    const M68kAcceptedCodeRunIR *run, uint8_t fallback_kind) {
  if (section != NULL && run != NULL &&
      accepted_run_has_manual_origin(section, run->start_offset, run->end_offset)) {
    return M68K_SOURCE_QUALITY_DIAGNOSTIC_MANUAL_EVIDENCE_CONFLICT;
  }
  return fallback_kind;
}

static int code_start_ref_is_mid_instruction_manual_seed(const M68kSectionAnalysisIR *section,
    const M68kCodeStartRefIR *ref) {
  if (section == NULL || ref == NULL || !code_origin_evidence_is_manual_seed(ref->evidence_kind)) return 0;
  if (section->certain_code_byte == NULL || section->certain_code_start == NULL) return 0;
  if (ref->offset >= section->certain_code_size) return 0;
  return section->certain_code_byte[ref->offset] != 0U && section->certain_code_start[ref->offset] == 0U;
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

static int range_ownership_is_manual_code_seed_conflict(const M68kRangeOwnershipIR *range) {
  if (range == NULL ||
      range->kind == M68K_RANGE_OWNERSHIP_UNKNOWN ||
      range->kind == M68K_RANGE_OWNERSHIP_CODE) {
    return 0;
  }
  if (range->status == M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED ||
      range->status == M68K_RANGE_OWNERSHIP_STATUS_CONFLICT ||
      range->kind == M68K_RANGE_OWNERSHIP_CONFLICT) {
    return 1;
  }
  return (range->negative_evidence_flags &
    (M68K_RANGE_NEGATIVE_STRUCTURED_DATA_OVERLAP | M68K_RANGE_NEGATIVE_CODE_OVERLAP)) != 0U;
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

static int source_quality_recovered_platform_call_covers_opword(const M68kSectionAnalysisIR *section,
    uint32_t offset, uint32_t run_end);

static int classify_run_end_from_decode(const M68kSectionAnalysisIR *section, const M68kDecodeSectionIR *decode_section,
    uint32_t start, uint32_t end, M68kAcceptedCodeRunIR *run) {
  uint32_t offset;
  if (decode_section == NULL || run == NULL || end <= start) return 0;
  offset = start;
  while (offset < end) {
    const M68kDecodeCandidate *candidate = m68k_decode_ir_find_candidate_at_offset(decode_section, offset);
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    uint32_t next_offset;
    if (candidate == NULL && source_quality_recovered_platform_call_covers_opword(section, offset, end)) {
      offset += 2U;
      continue;
    }
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

static int source_quality_candidate_stops_linear_flow(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  return !platform_instruction_has_normal_fallthrough(&instruction);
}

static int source_quality_recovered_platform_call_covers_opword(const M68kSectionAnalysisIR *section,
    uint32_t offset, uint32_t run_end) {
  size_t index;
  if (section == NULL || offset > UINT32_MAX - 2U || offset + 2U > run_end) return 0;
  for (index = 0U; index < section->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section->recovered_platform_calls[index];
    if (call->offset == offset &&
        (call->symbol_ref.platform_kind != M68K_PLATFORM_BACKEND_UNKNOWN ||
         call->note_symbol_ref.platform_kind != M68K_PLATFORM_BACKEND_UNKNOWN ||
         call->note_base_ref.platform_kind != M68K_PLATFORM_BACKEND_UNKNOWN)) {
      return 1;
    }
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
    if (candidate == NULL && source_quality_recovered_platform_call_covers_opword(section, offset, run->end_offset)) {
      expected_offset = offset + 2U;
      continue;
    }
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
  diagnostic.origin = kind == M68K_SOURCE_QUALITY_DIAGNOSTIC_MANUAL_EVIDENCE_CONFLICT
    ? M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_MANUAL_EVIDENCE
    : M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_AUTO_ANALYSIS;
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
  diagnostic.origin = kind == M68K_SOURCE_QUALITY_DIAGNOSTIC_MANUAL_EVIDENCE_CONFLICT
    ? M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_MANUAL_EVIDENCE
    : M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_AUTO_ANALYSIS;
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

static int append_manual_code_start_diagnostic(M68kSectionAnalysisIR *section, const M68kCodeStartRefIR *ref,
    const char *summary, const char *evidence_source) {
  M68kSourceQualityDiagnosticIR diagnostic;
  uint32_t end_offset;
  if (section == NULL || ref == NULL) return -1;
  if (ref->size != 0U && ref->offset <= UINT32_MAX - ref->size) {
    end_offset = ref->offset + ref->size;
  } else {
    end_offset = ref->offset < UINT32_MAX ? ref->offset + 1U : ref->offset;
  }
  memset(&diagnostic, 0, sizeof(diagnostic));
  diagnostic.kind = M68K_SOURCE_QUALITY_DIAGNOSTIC_MANUAL_EVIDENCE_CONFLICT;
  diagnostic.severity = M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR;
  diagnostic.blocker = 1U;
  diagnostic.origin = M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_MANUAL_EVIDENCE;
  diagnostic.has_section_index = 1U;
  diagnostic.section_index = (uint32_t)section->section_index;
  diagnostic.has_offset = 1U;
  diagnostic.offset = ref->offset;
  diagnostic.has_related_range = 1U;
  diagnostic.related_start = ref->offset;
  diagnostic.related_end = end_offset;
  diagnostic.summary = (char *)summary;
  diagnostic.evidence_source = (char *)evidence_source;
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

static int source_quality_symbol_token_char(char ch, int first) {
  if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || ch == '_') return 1;
  return !first && ch >= '0' && ch <= '9';
}

static int source_quality_symbol_expr_contains_token(const char *expr, const char *token) {
  size_t token_len;
  size_t index;
  if (expr == NULL || token == NULL || token[0] == '\0') return 0;
  token_len = strlen(token);
  for (index = 0U; expr[index] != '\0'; ++index) {
    if ((index == 0U || !source_quality_symbol_token_char(expr[index - 1U], 0)) &&
        strncmp(&expr[index], token, token_len) == 0 &&
        !source_quality_symbol_token_char(expr[index + token_len], 0)) {
      return 1;
    }
  }
  return 0;
}

static int rendered_symbol_access_matches_expected(const M68kRenderedSymbolAccessIR *rendered,
    const M68kExpectedSymbolAccessIR *expected, uint8_t rendered_kind) {
  if (rendered == NULL || expected == NULL || rendered_kind == M68K_RENDERED_SYMBOL_ACCESS_UNKNOWN) return 0;
  if (rendered->comment_only) return 0;
  if (rendered->access_kind != rendered_kind) {
    const int expected_symbolic_operand =
      expected->access_kind == M68K_EXPECTED_SYMBOL_ACCESS_EQUATE ||
      expected->access_kind == M68K_EXPECTED_SYMBOL_ACCESS_OPERAND;
    const int rendered_symbolic_operand =
      rendered->access_kind == M68K_RENDERED_SYMBOL_ACCESS_EQUATE ||
      rendered->access_kind == M68K_RENDERED_SYMBOL_ACCESS_OPERAND;
    if (!expected_symbolic_operand || !rendered_symbolic_operand ||
        !source_quality_symbol_expr_contains_token(rendered->symbol_name, expected->symbol_name)) {
      return 0;
    }
  }
  if (rendered->offset != expected->offset) return 0;
  if (rendered->symbol_name == NULL || rendered->symbol_name[0] == '\0') return 0;
  if (!expected->has_target &&
      (expected->symbol_name == NULL || (
        strcmp(rendered->symbol_name, expected->symbol_name) != 0 &&
        !source_quality_symbol_expr_contains_token(rendered->symbol_name, expected->symbol_name) &&
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

typedef struct M68kRenderedSymbolAccessOffsetIndex {
  const M68kRenderedSymbolAccessIR **items;
  size_t count;
} M68kRenderedSymbolAccessOffsetIndex;

static int compare_rendered_symbol_access_offset_ptrs(const void *left, const void *right) {
  const M68kRenderedSymbolAccessIR *left_access = *(const M68kRenderedSymbolAccessIR *const *)left;
  const M68kRenderedSymbolAccessIR *right_access = *(const M68kRenderedSymbolAccessIR *const *)right;
  if (left_access->offset < right_access->offset) return -1;
  if (left_access->offset > right_access->offset) return 1;
  if (left_access->access_kind < right_access->access_kind) return -1;
  if (left_access->access_kind > right_access->access_kind) return 1;
  return 0;
}

static int rendered_symbol_access_offset_index_build(const M68kRenderEvidenceSectionIR *render_evidence_section,
    M68kRenderedSymbolAccessOffsetIndex *index) {
  size_t access_index;
  if (index == NULL) return -1;
  index->items = NULL;
  index->count = 0U;
  if (render_evidence_section == NULL || render_evidence_section->rendered_symbol_access_count == 0U) return 0;
  index->items = (const M68kRenderedSymbolAccessIR **)calloc(
    render_evidence_section->rendered_symbol_access_count, sizeof(*index->items));
  if (index->items == NULL) return -1;
  for (access_index = 0U; access_index < render_evidence_section->rendered_symbol_access_count; ++access_index) {
    index->items[index->count++] = &render_evidence_section->rendered_symbol_accesses[access_index];
  }
  qsort(index->items, index->count, sizeof(*index->items), compare_rendered_symbol_access_offset_ptrs);
  return 0;
}

static void rendered_symbol_access_offset_index_destroy(M68kRenderedSymbolAccessOffsetIndex *index) {
  if (index == NULL) return;
  free(index->items);
  memset(index, 0, sizeof(*index));
}

static size_t rendered_symbol_access_offset_index_lower_bound(const M68kRenderedSymbolAccessOffsetIndex *index,
    uint32_t offset) {
  size_t low = 0U;
  size_t high = index != NULL ? index->count : 0U;
  while (low < high) {
    size_t mid = low + ((high - low) / 2U);
    if (index->items[mid]->offset < offset) low = mid + 1U;
    else high = mid;
  }
  return low;
}

static int section_has_rendered_symbol_access(const M68kRenderedSymbolAccessOffsetIndex *rendered_index,
    const M68kExpectedSymbolAccessIR *expected) {
  uint8_t rendered_kind;
  size_t index;
  if (rendered_index == NULL || expected == NULL) return 0;
  rendered_kind = rendered_symbol_access_kind_for_expected(expected->access_kind);
  if (rendered_kind == M68K_RENDERED_SYMBOL_ACCESS_UNKNOWN) return 1;
  for (index = rendered_symbol_access_offset_index_lower_bound(rendered_index, expected->offset);
      index < rendered_index->count && rendered_index->items[index]->offset == expected->offset; ++index) {
    if (rendered_symbol_access_matches_expected(rendered_index->items[index], expected, rendered_kind)) {
      return 1;
    }
  }
  return 0;
}

static int append_missing_expected_symbol_access_diagnostic(M68kSectionAnalysisIR *section,
    const M68kExpectedSymbolAccessIR *access) {
  M68kSourceQualityDiagnosticIR diagnostic;
  char evidence_source[256];
  const char *producer;
  const char *symbol_name;
  if (section == NULL || access == NULL) return -1;
  producer = access->producer != NULL && access->producer[0] != '\0' ? access->producer : "unknown";
  symbol_name = access->symbol_name != NULL && access->symbol_name[0] != '\0' ? access->symbol_name : "unknown";
  if (access->has_target) {
    snprintf(evidence_source, sizeof(evidence_source),
      "expected_symbol_access:producer=%s access=%s symbol=%s operand=%u target=%u:%u",
      producer, m68k_expected_symbol_access_kind_name(access->access_kind), symbol_name,
      (unsigned)access->operand_index, (unsigned)access->target_section_index,
      (unsigned)access->target_offset);
  } else {
    snprintf(evidence_source, sizeof(evidence_source),
      "expected_symbol_access:producer=%s access=%s symbol=%s operand=%u",
      producer, m68k_expected_symbol_access_kind_name(access->access_kind), symbol_name,
      (unsigned)access->operand_index);
  }
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

static int expected_symbol_access_has_precise_producer(const M68kExpectedSymbolAccessIR *access) {
  return access != NULL && access->producer != NULL && access->producer[0] != '\0' &&
    strcmp(access->producer, "unknown") != 0;
}

static int append_expected_symbol_access_without_producer_diagnostic(M68kSectionAnalysisIR *section,
    const M68kExpectedSymbolAccessIR *access) {
  M68kSourceQualityDiagnosticIR diagnostic;
  char evidence_source[256];
  const char *symbol_name;
  if (section == NULL || access == NULL) return -1;
  symbol_name = access->symbol_name != NULL && access->symbol_name[0] != '\0' ? access->symbol_name : "unknown";
  if (access->has_target) {
    snprintf(evidence_source, sizeof(evidence_source),
      "expected_symbol_access:producer=unknown access=%s symbol=%s operand=%u target=%u:%u",
      m68k_expected_symbol_access_kind_name(access->access_kind), symbol_name,
      (unsigned)access->operand_index, (unsigned)access->target_section_index,
      (unsigned)access->target_offset);
  } else {
    snprintf(evidence_source, sizeof(evidence_source),
      "expected_symbol_access:producer=unknown access=%s symbol=%s operand=%u",
      m68k_expected_symbol_access_kind_name(access->access_kind), symbol_name,
      (unsigned)access->operand_index);
  }
  memset(&diagnostic, 0, sizeof(diagnostic));
  diagnostic.kind = M68K_SOURCE_QUALITY_DIAGNOSTIC_EXPECTED_SYMBOL_ACCESS_WITHOUT_PRODUCER;
  diagnostic.severity = M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR;
  diagnostic.blocker = 1U;
  diagnostic.origin = M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_AUTO_ANALYSIS;
  diagnostic.has_section_index = 1U;
  diagnostic.section_index = (uint32_t)section->section_index;
  diagnostic.has_offset = 1U;
  diagnostic.offset = access->offset;
  diagnostic.summary = "expected symbol access has no precise producer";
  diagnostic.evidence_source = evidence_source;
  return m68k_ir_section_analysis_append_source_quality_diagnostic(section, &diagnostic);
}

static int section_has_expected_symbol_access_for_platform_operand_expr_token(
    const M68kSectionAnalysisIR *section, const M68kPlatformSemanticUseIR *use, const char *token) {
  size_t index;
  if (section == NULL || use == NULL || token == NULL || token[0] == '\0') return 0;
  for (index = 0U; index < section->expected_symbol_access_count; ++index) {
    const M68kExpectedSymbolAccessIR *access = &section->expected_symbol_accesses[index];
    if (access->offset != use->offset) continue;
    if (access->operand_index != use->operand_index) continue;
    if (access->symbol_name == NULL || strcmp(access->symbol_name, token) != 0) continue;
    return 1;
  }
  return 0;
}

static int append_platform_operand_expr_without_expected_access_diagnostic(M68kSectionAnalysisIR *section,
    const M68kPlatformSemanticUseIR *use, const char *token) {
  M68kSourceQualityDiagnosticIR diagnostic;
  char evidence_source[256];
  if (section == NULL || use == NULL || token == NULL || token[0] == '\0') return -1;
  snprintf(evidence_source, sizeof(evidence_source),
    "platform_semantic_use:kind=%s operand_expr=%s missing_symbol=%s operand=%u",
    m68k_platform_semantic_use_kind_name(use->kind),
    use->operand_expr != NULL && use->operand_expr[0] != '\0' ? use->operand_expr : "unknown",
    token, (unsigned)use->operand_index);
  memset(&diagnostic, 0, sizeof(diagnostic));
  diagnostic.kind = M68K_SOURCE_QUALITY_DIAGNOSTIC_PLATFORM_OPERAND_EXPR_WITHOUT_EXPECTED_ACCESS;
  diagnostic.severity = M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR;
  diagnostic.blocker = 1U;
  diagnostic.origin = M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_AUTO_ANALYSIS;
  diagnostic.has_section_index = 1U;
  diagnostic.section_index = (uint32_t)section->section_index;
  diagnostic.has_offset = 1U;
  diagnostic.offset = use->offset;
  diagnostic.summary = "platform operand expression has no expected symbol access";
  diagnostic.evidence_source = evidence_source;
  return m68k_ir_section_analysis_append_source_quality_diagnostic(section, &diagnostic);
}

static int append_platform_operand_expr_without_expected_access_diagnostics_for_use(
    M68kSectionAnalysisIR *section, const M68kPlatformSemanticUseIR *use) {
  size_t index = 0U;
  if (section == NULL || use == NULL || !use->has_operand_expr ||
      use->operand_expr == NULL || use->operand_expr[0] == '\0' ||
      use->operand_index == UINT32_MAX) {
    return 0;
  }
  while (use->operand_expr[index] != '\0') {
    char token[M68K_IR_SYMBOL_NAME_SIZE];
    size_t token_start;
    size_t token_len = 0U;
    while (use->operand_expr[index] != '\0' && !source_quality_symbol_token_char(use->operand_expr[index], 1))
      ++index;
    token_start = index;
    while (use->operand_expr[index] != '\0' &&
        source_quality_symbol_token_char(use->operand_expr[index], token_len == 0U)) {
      if (token_len + 1U < sizeof(token)) token[token_len++] = use->operand_expr[index];
      ++index;
    }
    if (token_len == 0U || token_len >= sizeof(token)) continue;
    if (token_start > 0U && use->operand_expr[token_start - 1U] >= '0' &&
        use->operand_expr[token_start - 1U] <= '9') {
      continue;
    }
    token[token_len] = '\0';
    if (!section_has_expected_symbol_access_for_platform_operand_expr_token(section, use, token)) {
      if (append_platform_operand_expr_without_expected_access_diagnostic(section, use, token) != 0) return -1;
    }
  }
  return 0;
}

static int append_platform_operand_expr_without_expected_access_diagnostics_for_section(
    M68kSectionAnalysisIR *section) {
  size_t index;
  if (section == NULL) return -1;
  for (index = 0U; index < section->platform_semantic_use_count; ++index) {
    if (append_platform_operand_expr_without_expected_access_diagnostics_for_use(
        section, &section->platform_semantic_uses[index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_missing_expected_symbol_access_diagnostics_for_section(M68kSectionAnalysisIR *section,
    const M68kRenderEvidenceSectionIR *render_evidence_section) {
  size_t index;
  M68kRenderedSymbolAccessOffsetIndex rendered_index;
  int result = -1;
  if (section == NULL) return -1;
  memset(&rendered_index, 0, sizeof(rendered_index));
  if (append_platform_operand_expr_without_expected_access_diagnostics_for_section(section) != 0) return -1;
  if (rendered_symbol_access_offset_index_build(render_evidence_section, &rendered_index) != 0) return -1;
  for (index = 0U; index < section->expected_symbol_access_count; ++index) {
    const M68kExpectedSymbolAccessIR *access = &section->expected_symbol_accesses[index];
    if (!expected_symbol_access_has_precise_producer(access)) {
      if (append_expected_symbol_access_without_producer_diagnostic(section, access) != 0) goto done;
      continue;
    }
    if (!section_has_rendered_symbol_access(&rendered_index, access)) {
      if (append_missing_expected_symbol_access_diagnostic(section, access) != 0) goto done;
    }
  }
  result = 0;

done:
  rendered_symbol_access_offset_index_destroy(&rendered_index);
  return result;
}

typedef struct M68kRenderedReferenceIndex {
  const M68kRenderedSymbolAccessIR **by_target;
  size_t by_target_count;
  const M68kRenderedSymbolAccessIR **by_name;
  size_t by_name_count;
} M68kRenderedReferenceIndex;

static void rendered_reference_index_destroy(M68kRenderedReferenceIndex *index);

static int rendered_symbol_access_is_label_reference_candidate(const M68kRenderedSymbolAccessIR *access) {
  return access != NULL && !access->comment_only &&
    access->access_kind != M68K_RENDERED_SYMBOL_ACCESS_LABEL_STATEMENT &&
    access->access_kind != M68K_RENDERED_SYMBOL_ACCESS_UNKNOWN;
}

static int compare_rendered_symbol_access_target_ptrs(const void *left, const void *right) {
  const M68kRenderedSymbolAccessIR *left_access = *(const M68kRenderedSymbolAccessIR *const *)left;
  const M68kRenderedSymbolAccessIR *right_access = *(const M68kRenderedSymbolAccessIR *const *)right;
  if (left_access->target_section_index < right_access->target_section_index) return -1;
  if (left_access->target_section_index > right_access->target_section_index) return 1;
  if (left_access->target_offset < right_access->target_offset) return -1;
  if (left_access->target_offset > right_access->target_offset) return 1;
  return 0;
}

static int compare_rendered_symbol_access_name_ptrs(const void *left, const void *right) {
  const M68kRenderedSymbolAccessIR *left_access = *(const M68kRenderedSymbolAccessIR *const *)left;
  const M68kRenderedSymbolAccessIR *right_access = *(const M68kRenderedSymbolAccessIR *const *)right;
  const char *left_name = left_access->symbol_name != NULL ? left_access->symbol_name : "";
  const char *right_name = right_access->symbol_name != NULL ? right_access->symbol_name : "";
  return strcmp(left_name, right_name);
}

static int rendered_reference_index_build(const M68kRenderEvidenceIR *render_evidence,
    M68kRenderedReferenceIndex *index) {
  size_t section_index;
  size_t target_capacity = 0U;
  size_t name_capacity = 0U;
  if (index == NULL) return -1;
  memset(index, 0, sizeof(*index));
  if (render_evidence == NULL) return 0;
  for (section_index = 0U; section_index < render_evidence->section_count; ++section_index) {
    const M68kRenderEvidenceSectionIR *section = &render_evidence->sections[section_index];
    size_t access_index;
    for (access_index = 0U; access_index < section->rendered_symbol_access_count; ++access_index) {
      const M68kRenderedSymbolAccessIR *access = &section->rendered_symbol_accesses[access_index];
      if (!rendered_symbol_access_is_label_reference_candidate(access)) continue;
      if (access->has_target) ++target_capacity;
      if (access->symbol_name != NULL && access->symbol_name[0] != '\0') ++name_capacity;
    }
  }
  if (target_capacity != 0U) {
    index->by_target = (const M68kRenderedSymbolAccessIR **)calloc(target_capacity, sizeof(*index->by_target));
    if (index->by_target == NULL) return -1;
  }
  if (name_capacity != 0U) {
    index->by_name = (const M68kRenderedSymbolAccessIR **)calloc(name_capacity, sizeof(*index->by_name));
    if (index->by_name == NULL) {
      rendered_reference_index_destroy(index);
      return -1;
    }
  }
  for (section_index = 0U; section_index < render_evidence->section_count; ++section_index) {
    const M68kRenderEvidenceSectionIR *section = &render_evidence->sections[section_index];
    size_t access_index;
    for (access_index = 0U; access_index < section->rendered_symbol_access_count; ++access_index) {
      const M68kRenderedSymbolAccessIR *access = &section->rendered_symbol_accesses[access_index];
      if (!rendered_symbol_access_is_label_reference_candidate(access)) continue;
      if (access->has_target) index->by_target[index->by_target_count++] = access;
      if (access->symbol_name != NULL && access->symbol_name[0] != '\0') index->by_name[index->by_name_count++] = access;
    }
  }
  if (index->by_target_count != 0U)
    qsort(index->by_target, index->by_target_count, sizeof(*index->by_target),
      compare_rendered_symbol_access_target_ptrs);
  if (index->by_name_count != 0U)
    qsort(index->by_name, index->by_name_count, sizeof(*index->by_name),
      compare_rendered_symbol_access_name_ptrs);
  return 0;
}

static void rendered_reference_index_destroy(M68kRenderedReferenceIndex *index) {
  if (index == NULL) return;
  free(index->by_target);
  free(index->by_name);
  memset(index, 0, sizeof(*index));
}

static int rendered_reference_index_has_target(const M68kRenderedReferenceIndex *index,
    uint32_t target_section_index, uint32_t target_offset) {
  size_t low = 0U;
  size_t high = index != NULL ? index->by_target_count : 0U;
  while (low < high) {
    size_t mid = low + ((high - low) / 2U);
    const M68kRenderedSymbolAccessIR *access = index->by_target[mid];
    if (access->target_section_index < target_section_index ||
        (access->target_section_index == target_section_index && access->target_offset < target_offset)) {
      low = mid + 1U;
    } else {
      high = mid;
    }
  }
  while (low < (index != NULL ? index->by_target_count : 0U)) {
    const M68kRenderedSymbolAccessIR *access = index->by_target[low];
    if (access->target_section_index != target_section_index || access->target_offset != target_offset) break;
    return 1;
  }
  return 0;
}

static int rendered_reference_index_has_name(const M68kRenderedReferenceIndex *index, const char *symbol_name) {
  size_t low = 0U;
  size_t high = index != NULL ? index->by_name_count : 0U;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 0;
  while (low < high) {
    size_t mid = low + ((high - low) / 2U);
    int cmp = strcmp(index->by_name[mid]->symbol_name, symbol_name);
    if (cmp < 0) low = mid + 1U;
    else high = mid;
  }
  return low < (index != NULL ? index->by_name_count : 0U) &&
    strcmp(index->by_name[low]->symbol_name, symbol_name) == 0;
}

static int rendered_reference_index_references_label(const M68kRenderedReferenceIndex *index,
    const M68kRenderedSymbolAccessIR *label) {
  if (index == NULL || label == NULL) return 0;
  if (label->has_target &&
      rendered_reference_index_has_target(index, label->target_section_index, label->target_offset)) {
    return 1;
  }
  return rendered_reference_index_has_name(index, label->symbol_name);
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
    M68kSectionAnalysisIR *section, const M68kRenderEvidenceIR *render_evidence,
    const M68kRenderedReferenceIndex *reference_index) {
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
    if (!rendered_reference_index_references_label(reference_index, access)) {
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

static int append_manual_mid_instruction_diagnostics_for_section(M68kSectionAnalysisIR *section) {
  size_t index;
  if (section == NULL) return -1;
  for (index = 0U; index < section->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section->code_start_refs[index];
    if (!code_start_ref_is_mid_instruction_manual_seed(section, ref)) continue;
    if (append_manual_code_start_diagnostic(section, ref,
        "manual code seed lands inside an accepted instruction",
        "manual_code_start_ref") != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_manual_mid_instruction_diagnostics(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    if (append_manual_mid_instruction_diagnostics_for_section(&source_analysis->sections[section_index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_manual_noncode_overlap_diagnostics_for_section(M68kSectionAnalysisIR *section) {
  size_t run_index;
  if (section == NULL) return -1;
  for (run_index = 0U; run_index < section->accepted_code_run_count; ++run_index) {
    const M68kAcceptedCodeRunIR *run = &section->accepted_code_runs[run_index];
    size_t range_index;
    if (!accepted_run_has_manual_origin(section, run->start_offset, run->end_offset)) continue;
    for (range_index = 0U; range_index < section->range_ownership_count; ++range_index) {
      const M68kRangeOwnershipIR *range = &section->range_ownerships[range_index];
      if (!range_ownership_is_manual_code_seed_conflict(range) ||
          !range_ownership_overlaps(run->start_offset, run->end_offset, range)) {
        continue;
      }
      if (append_run_diagnostic(section, run,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_MANUAL_EVIDENCE_CONFLICT,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR, 1U,
          "manual code seed overlaps non-code range") != 0) {
        return -1;
      }
      break;
    }
  }
  return 0;
}

static int append_manual_noncode_overlap_diagnostics(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    if (append_manual_noncode_overlap_diagnostics_for_section(&source_analysis->sections[section_index]) != 0) {
      return -1;
    }
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
          source_quality_kind_for_manual_run_conflict(section, run,
            M68K_SOURCE_QUALITY_DIAGNOSTIC_UNTERMINATED_OR_INVALID_CODE_RANGE),
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

static int accepted_gap_run_has_noncontrol_operand_access(const M68kSectionAnalysisIR *section,
    const M68kAcceptedCodeRunIR *run) {
  size_t access_index;
  if (section == NULL || run == NULL) return 0;
  for (access_index = 0U; access_index < section->expected_symbol_access_count; ++access_index) {
    const M68kExpectedSymbolAccessIR *access = &section->expected_symbol_accesses[access_index];
    if (access->access_kind == M68K_EXPECTED_SYMBOL_ACCESS_BRANCH_TARGET ||
        access->access_kind == M68K_EXPECTED_SYMBOL_ACCESS_LABEL_STATEMENT ||
        access->access_kind == M68K_EXPECTED_SYMBOL_ACCESS_EQUATE ||
        !access->has_target || access->target_section_index != section->section_index) {
      continue;
    }
    if (access->offset >= run->start_offset && access->offset < run->end_offset) continue;
    if (access->target_offset >= run->start_offset && access->target_offset < run->end_offset) return 1;
  }
  return 0;
}

static int accepted_gap_run_has_negative_range_evidence(const M68kSectionAnalysisIR *section,
    const M68kAcceptedCodeRunIR *run) {
  size_t range_index;
  if (section == NULL || run == NULL) return 0;
  for (range_index = 0U; range_index < section->range_ownership_count; ++range_index) {
    const M68kRangeOwnershipIR *range = &section->range_ownerships[range_index];
    if (!range_ownership_overlaps(run->start_offset, run->end_offset, range)) continue;
    if (range->kind == M68K_RANGE_OWNERSHIP_CODE &&
        range->status == M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED &&
        range->negative_evidence_flags == 0U) {
      continue;
    }
    if (range->negative_evidence_flags != 0U || range_ownership_blocks_hard_control_proof(range)) return 1;
  }
  return 0;
}

static int append_unterminated_accepted_gap_diagnostics_for_section(M68kSectionAnalysisIR *section) {
  size_t run_index;
  if (section == NULL) return -1;
  for (run_index = 0U; run_index < section->accepted_code_run_count; ++run_index) {
    const M68kAcceptedCodeRunIR *run = &section->accepted_code_runs[run_index];
    if (run->end_kind != M68K_ACCEPTED_CODE_RUN_END_ACCEPTED_GAP) continue;
    if (!accepted_run_has_executable_origin(section, run->start_offset, run->end_offset)) continue;
    if (!accepted_gap_run_has_noncontrol_operand_access(section, run) &&
        !accepted_gap_run_has_negative_range_evidence(section, run)) {
      continue;
    }
    if (append_run_diagnostic(section, run,
        source_quality_kind_for_manual_run_conflict(section, run,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_UNTERMINATED_OR_INVALID_CODE_RANGE),
        M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR, 1U,
        "accepted code run ends without terminal flow or structural continuation proof") != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_unterminated_accepted_gap_diagnostics(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    if (append_unterminated_accepted_gap_diagnostics_for_section(
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

static int append_palette_upload_platform_semantic_use(M68kSourceAnalysisIR *source_analysis,
    const M68kAnalysisStructuredDataItem *item) {
  M68kSectionAnalysisIR *section;
  M68kPlatformSemanticUseIR use;
  char note[64];
  if (source_analysis == NULL || item == NULL ||
      (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE) == 0U ||
      !item->has_consumer || item->consumer_section >= source_analysis->section_count ||
      item->size < 4U || (item->size & 1U) != 0U) {
    return 0;
  }
  memset(&use, 0, sizeof(use));
  snprintf(note, sizeof(note), "palette upload %u colors", (unsigned)(item->size / 2U));
  use.kind = M68K_PLATFORM_SEMANTIC_USE_PALETTE;
  use.offset = item->consumer_offset;
  use.size = 0U;
  use.role_flags = M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE;
  use.source_pattern_id = item->source_pattern_id;
  use.confidence = 255U;
  use.has_target = item->has_section_index;
  use.target_section_index = item->section_index;
  use.target_offset = item->offset;
  use.note_text = note;
  section = &source_analysis->sections[item->consumer_section];
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
    if (append_palette_upload_platform_semantic_use(source_analysis, item) != 0) return -1;
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

static int append_bitmap_memory_platform_semantic_uses(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t ref_index;
    for (ref_index = 0U; ref_index < section->runtime_address_ref_count; ++ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[ref_index];
      size_t base_index;
      uint8_t plane_index = 0U;
      uint32_t base_address = 0U;
      uint32_t delta = 0U;
      int matched = 0;
      char note[128];
      M68kPlatformSemanticUseIR use;
      if ((ref->data_class_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) == 0U ||
          !ref->has_runtime_address || ref->size != 0U) {
        continue;
      }
      for (base_index = 0U; base_index < section->runtime_address_ref_count; ++base_index) {
        const M68kRuntimeAddressRefIR *base_ref = &section->runtime_address_refs[base_index];
        if ((base_ref->data_class_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) == 0U ||
            !base_ref->has_runtime_address || base_ref->size == 0U) {
          continue;
        }
        if (ref->runtime_address >= base_ref->runtime_address &&
            ref->runtime_address - base_ref->runtime_address < base_ref->size) {
          base_address = base_ref->runtime_address;
          delta = ref->runtime_address - base_ref->runtime_address;
          matched = 1;
          break;
        }
        if (plane_index != UINT8_MAX) ++plane_index;
      }
      if (!matched) continue;
      if (delta == 0U) {
        snprintf(note, sizeof(note), "bitmap memory plane %u base $%08X",
          (unsigned)plane_index, (unsigned)base_address);
      } else {
        snprintf(note, sizeof(note), "bitmap memory plane %u +$%X ($%08X)",
          (unsigned)plane_index, (unsigned)delta, (unsigned)(base_address + delta));
      }
      memset(&use, 0, sizeof(use));
      use.kind = M68K_PLATFORM_SEMANTIC_USE_BITMAP_MEMORY;
      use.offset = ref->offset;
      use.size = ref->source_size;
      use.confidence = ref->confidence;
      use.note_text = note;
      if (m68k_ir_section_analysis_append_platform_semantic_use(section, &use) != 0) return -1;
    }
  }
  return 0;
}

static const M68kDecodeSectionIR *source_quality_decode_section_by_index(const M68kDecodeIR *decode,
    uint32_t section_index, size_t *out_decode_index);
static int source_quality_candidate_is_accepted_start(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate);
static int source_quality_reglist_contains_register(const M68kOperandIR *operand, uint8_t reg_kind,
    uint8_t reg_index);
static int source_quality_operand_is_predec_a7(const M68kOperandIR *operand);
static int source_quality_operand_is_postinc_a7(const M68kOperandIR *operand);
static int source_quality_operand_absolute_offset(const M68kOperandIR *operand, uint32_t *out_offset);
static int source_quality_operand_address_register_index(const M68kOperandIR *operand, uint8_t *out_reg);
static int source_quality_operand_data_register_index(const M68kOperandIR *operand, uint8_t *out_reg);
static int source_quality_accepted_range_has_code_byte(const uint8_t *accepted_bytes, uint32_t section_size,
    uint32_t offset, uint32_t size);
static int source_quality_section_has_label_at(const M68kSectionAnalysisIR *section, uint32_t offset);
static const M68kDecodeCandidate *source_quality_previous_accepted_candidate(
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t cursor);
static uint32_t source_quality_immediate_domain_value_for_instruction_size(const M68kInstructionIR *instruction,
    uint32_t value);

static int format_source_quality_amiga_disk_dma_note(const AmigaOsHardwareRegisterInfo *hardware_register,
    uint32_t value, char *buf, size_t buf_size) {
  uint32_t word = value & 0xFFFFU;
  uint32_t byte_length;
  const char *direction;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_register == NULL ||
      (hardware_register->symbol_id != AMIGA_OS_SYMBOL_ID_DSKLEN &&
       hardware_register->symbol_id != AMIGA_OS_SYMBOL_ID_DSKSYNC)) {
    return 0;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_DSKSYNC) {
    snprintf(buf, buf_size, "disk sync word $%04X", (unsigned)word);
    return strlen(buf) + 1U < buf_size;
  }
  if ((word & AMIGA_OS_DSKLEN_DMA_ENABLE_MASK) == 0U) return 0;
  byte_length = (word & AMIGA_OS_DSKLEN_LENGTH_MASK) * AMIGA_OS_DSKLEN_LENGTH_UNIT_BYTES;
  if (byte_length == 0U) return 0;
  direction = (word & AMIGA_OS_DSKLEN_WRITE_MASK) != 0U ? "write" : "read";
  snprintf(buf, buf_size, "disk DMA %s %u bytes", direction, (unsigned)byte_length);
  return strlen(buf) + 1U < buf_size;
}

static int format_source_quality_amiga_hardware_value_note(const AmigaOsHardwareRegisterInfo *hardware_register,
    uint32_t value, char *buf, size_t buf_size) {
  uint32_t word = value & 0xFFFFU;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_register == NULL) return 0;
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_BPLCON0) {
    uint32_t plane_count = (word >> 12) & 7U;
    const char *resolution = (word & 0x8000U) != 0U ? "hires" : "lores";
    const char *color = (word & 0x0200U) != 0U ? " color" : "";
    if (plane_count == 0U) return 0;
    snprintf(buf, buf_size, "display %u bitplanes %s%s", (unsigned)plane_count, resolution, color);
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_BPLCON1) {
    snprintf(buf, buf_size, "display scroll pf1=%u pf2=%u",
      (unsigned)(word & 0xFU), (unsigned)((word >> 4) & 0xFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_DIWSTRT) {
    snprintf(buf, buf_size, "display window start v=$%02X h=$%02X",
      (unsigned)((word >> 8) & 0xFFU), (unsigned)(word & 0xFFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_DIWSTOP) {
    snprintf(buf, buf_size, "display window stop v=$%02X h=$%02X",
      (unsigned)((word >> 8) & 0xFFU), (unsigned)(word & 0xFFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_DDFSTRT) {
    snprintf(buf, buf_size, "display fetch start $%02X", (unsigned)(word & 0xFFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_DDFSTOP) {
    snprintf(buf, buf_size, "display fetch stop $%02X", (unsigned)(word & 0xFFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_BPL1MOD ||
      hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_BPL2MOD) {
    int16_t modulo = (int16_t)word;
    snprintf(buf, buf_size, "bitplane modulo %d bytes", (int)modulo);
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_BLTSIZE) {
    uint32_t height = (word >> 6) & 0x3FFU;
    uint32_t width_words = word & 0x3FU;
    if (height == 0U) height = 1024U;
    if (width_words == 0U) width_words = 64U;
    snprintf(buf, buf_size, "blitter size %u rows x %u words (%u bytes/row)",
      (unsigned)height, (unsigned)width_words, (unsigned)(width_words * 2U));
    return strlen(buf) + 1U < buf_size;
  }
  return 0;
}

static int format_source_quality_copper_wait_note(uint16_t first, uint16_t second, char *buf, size_t buf_size) {
  uint32_t wait_word = (uint32_t)(first & 0xFFFEU);
  if (buf == NULL || buf_size == 0U || (first & 1U) == 0U || (second & 1U) != 0U) return 0;
  buf[0] = '\0';
  snprintf(buf, buf_size, "copper wait v=$%02X h=$%02X mask $%04X",
    (unsigned)((wait_word >> 8) & 0xFFU), (unsigned)(wait_word & 0xFEU), (unsigned)second);
  return strlen(buf) + 1U < buf_size;
}

static int format_source_quality_copper_display_row_note(uint16_t first, uint16_t second, char *buf,
    size_t buf_size) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  uint32_t register_offset = (uint32_t)(first & 0x01FEU);
  if (buf == NULL || buf_size == 0U || (first & 1U) != 0U) return 0;
  buf[0] = '\0';
  hardware_register = amiga_os_find_hardware_register_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM,
    register_offset);
  return format_source_quality_amiga_hardware_value_note(hardware_register, (uint32_t)second, buf, buf_size);
}

static const AmigaOsHardwareRegisterInfo *source_quality_copper_runtime_pointer_register(uint16_t register_word) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  uint32_t register_offset = (uint32_t)(register_word & 0x01FEU);
  if ((register_word & 1U) != 0U) return NULL;
  hardware_register = amiga_os_find_hardware_register_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM,
    register_offset);
  if (hardware_register == NULL) {
    hardware_range = amiga_os_find_hardware_register_range_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM,
      register_offset);
    if (hardware_range != NULL) {
      hardware_register =
        amiga_os_find_hardware_register_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM, hardware_range->offset);
    }
  }
  if (hardware_register == NULL ||
      (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U ||
      hardware_register->runtime_target_kind == AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_NONE) {
    return NULL;
  }
  return hardware_register;
}

static int format_source_quality_copper_runtime_pointer_note(const uint8_t *data, uint32_t offset, uint32_t cursor,
    uint32_t size, uint16_t first, uint16_t second, char *buf, size_t buf_size) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  uint32_t register_offset = (uint32_t)(first & 0x01FEU);
  uint32_t pointer_index;
  uint16_t next_first;
  uint16_t next_second;
  uint32_t pointer_address;
  if (data == NULL || buf == NULL || buf_size == 0U || cursor + 8U > size) return 0;
  buf[0] = '\0';
  hardware_register = source_quality_copper_runtime_pointer_register(first);
  if (hardware_register == NULL) return 0;
  if (register_offset < hardware_register->offset ||
      ((register_offset - hardware_register->offset) & 3U) != 0U) {
    return 0;
  }
  next_first = m68k_read_u16be(data + offset + cursor + 4U);
  next_second = m68k_read_u16be(data + offset + cursor + 6U);
  if ((next_first & 1U) != 0U || (uint32_t)(next_first & 0x01FEU) != register_offset + 2U) return 0;
  pointer_index = (register_offset - hardware_register->offset) / 4U;
  pointer_address = ((uint32_t)second << 16) | next_second;
  if (pointer_address == 0U) {
    snprintf(buf, buf_size, "%s pointer %u disabled", hardware_register->runtime_target_role,
      (unsigned)pointer_index);
  } else {
    snprintf(buf, buf_size, "%s pointer $%08X", hardware_register->runtime_target_role,
      (unsigned)pointer_address);
  }
  return strlen(buf) + 1U < buf_size;
}

static int source_quality_copper_bitmap_pointer_at(const uint8_t *data, uint32_t offset, uint32_t cursor,
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
  hardware_register = source_quality_copper_runtime_pointer_register(first);
  if (hardware_register == NULL ||
      hardware_register->runtime_target_kind != AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BITMAP) {
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

static uint32_t source_quality_runtime_target_kind_role_flags(uint16_t kind) {
  switch (kind) {
    case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_COPPER_LIST:
      return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST;
    case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_DISK_BUFFER:
      return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_DISK_BUFFER;
    case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BLITTER_SOURCE:
      return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_SOURCE;
    case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BLITTER_DESTINATION:
      return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_DESTINATION;
    case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BITMAP:
      return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP;
    case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_SPRITE:
      return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SPRITE;
    case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_SOUND_SAMPLE:
      return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE;
    default:
      return 0U;
  }
}

static int source_quality_copper_runtime_pointer_details_at(const uint8_t *data, uint32_t offset, uint32_t cursor,
    uint32_t size, uint32_t *out_pointer, uint32_t *out_role_flags, const char **out_role) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  uint16_t first;
  uint16_t second;
  uint16_t next_first;
  uint16_t next_second;
  uint32_t register_offset;
  if (out_pointer != NULL) *out_pointer = 0U;
  if (out_role_flags != NULL) *out_role_flags = 0U;
  if (out_role != NULL) *out_role = NULL;
  if (data == NULL || cursor + 8U > size) return 0;
  first = m68k_read_u16be(data + offset + cursor);
  second = m68k_read_u16be(data + offset + cursor + 2U);
  next_first = m68k_read_u16be(data + offset + cursor + 4U);
  next_second = m68k_read_u16be(data + offset + cursor + 6U);
  if ((first & 1U) != 0U || (next_first & 1U) != 0U) return 0;
  register_offset = (uint32_t)(first & 0x01FEU);
  hardware_register = source_quality_copper_runtime_pointer_register(first);
  if (hardware_register == NULL || hardware_register->runtime_target_role == NULL ||
      hardware_register->runtime_target_role[0] == '\0') {
    return 0;
  }
  if (register_offset < hardware_register->offset ||
      ((register_offset - hardware_register->offset) & 3U) != 0U ||
      (uint32_t)(next_first & 0x01FEU) != register_offset + 2U) {
    return 0;
  }
  if (out_pointer != NULL) *out_pointer = ((uint32_t)second << 16) | next_second;
  if (out_role_flags != NULL)
    *out_role_flags = source_quality_runtime_target_kind_role_flags(hardware_register->runtime_target_kind);
  if (out_role != NULL) *out_role = hardware_register->runtime_target_role;
  return out_pointer == NULL || *out_pointer != 0U;
}

static uint8_t source_quality_collect_copper_bitmap_pointers(const uint8_t *data, uint32_t offset, uint32_t size,
    uint32_t *pointers, uint8_t pointer_limit) {
  uint32_t cursor;
  uint8_t pointer_count = 0U;
  if (data == NULL || pointers == NULL || pointer_limit == 0U || size == 0U) return 0U;
  for (cursor = 0U; cursor + 8U <= size && pointer_count < pointer_limit; cursor += 4U) {
    uint32_t pointer = 0U;
    if (!source_quality_copper_bitmap_pointer_at(data, offset, cursor, size, &pointer)) continue;
    pointers[pointer_count++] = pointer;
  }
  return pointer_count;
}

static uint32_t source_quality_copper_bitmap_pointer_even_step(const uint32_t *pointers, uint8_t pointer_count) {
  uint32_t step = 0U;
  uint8_t index;
  if (pointers == NULL || pointer_count < 2U || pointers[1] <= pointers[0]) return 0U;
  step = pointers[1] - pointers[0];
  if (step == 0U) return 0U;
  for (index = 2U; index < pointer_count; ++index) {
    if (pointers[index] <= pointers[index - 1U] || pointers[index] - pointers[index - 1U] != step) {
      return 0U;
    }
  }
  return step;
}

static int format_source_quality_copper_display_layout_note(const uint8_t *data, uint32_t offset, uint32_t size,
    char *buf, size_t buf_size) {
  uint32_t pointers[8];
  uint8_t pointer_count;
  uint32_t step;
  if (buf != NULL && buf_size != 0U) buf[0] = '\0';
  if (data == NULL || buf == NULL || buf_size == 0U || size == 0U) return 0;
  pointer_count = source_quality_collect_copper_bitmap_pointers(data, offset, size, pointers,
    (uint8_t)(sizeof(pointers) / sizeof(pointers[0])));
  if (pointer_count == 0U) return 0;
  step = source_quality_copper_bitmap_pointer_even_step(pointers, pointer_count);
  if (step != 0U) {
    snprintf(buf, buf_size, "display layout %u bitmap planes $%08X..$%08X step $%X",
      (unsigned)pointer_count, (unsigned)pointers[0], (unsigned)pointers[pointer_count - 1U],
      (unsigned)step);
  } else if (pointer_count == 1U) {
    snprintf(buf, buf_size, "display layout 1 bitmap plane $%08X", (unsigned)pointers[0]);
  } else {
    snprintf(buf, buf_size, "display layout %u bitmap plane bases from $%08X",
      (unsigned)pointer_count, (unsigned)pointers[0]);
  }
  return strlen(buf) + 1U < buf_size;
}

typedef struct M68kSourceQualityDisplaySetup {
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
} M68kSourceQualityDisplaySetup;

static int source_quality_instruction_move_operand_indices_from_metadata(const M68kInstructionIR *instruction,
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

static int source_quality_candidate_operand_absolute_value(const M68kDecodeCandidate *candidate,
    size_t operand_index, uint32_t *out_value) {
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

static int source_quality_display_setup_record_register_write(M68kSourceQualityDisplaySetup *setup,
    const AmigaOsHardwareRegisterInfo *hardware_register, uint32_t value) {
  uint16_t word = (uint16_t)value;
  if (setup == NULL || hardware_register == NULL) return 0;
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_BPLCON0) {
    setup->has_bplcon0 = 1U;
    setup->bplcon0 = word;
    return 1;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_DIWSTRT) {
    setup->has_diwstrt = 1U;
    setup->diwstrt = word;
    return 1;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_DIWSTOP) {
    setup->has_diwstop = 1U;
    setup->diwstop = word;
    return 1;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_DDFSTRT) {
    setup->has_ddfstrt = 1U;
    setup->ddfstrt = word;
    return 1;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_DDFSTOP) {
    setup->has_ddfstop = 1U;
    setup->ddfstop = word;
    return 1;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_BPL1MOD) {
    setup->has_bpl1mod = 1U;
    setup->bpl1mod = (int16_t)word;
    return 1;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_BPL2MOD) {
    setup->has_bpl2mod = 1U;
    setup->bpl2mod = (int16_t)word;
    return 1;
  }
  return 0;
}

static int source_quality_display_setup_collect_immediate_write(M68kSourceQualityDisplaySetup *setup,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  size_t source_index = 0U, dest_index = 0U;
  uint32_t value = 0U;
  uint32_t dest_address = 0U;
  if (setup == NULL || candidate == NULL || instruction == NULL || instruction->size_suffix != 'w' ||
      !source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
        &metadata) ||
      metadata == NULL || metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
      !m68k_ir_operand_immediate_value(&instruction->operands[source_index], &value) ||
      !source_quality_candidate_operand_absolute_value(candidate, dest_index, &dest_address)) {
    return 0;
  }
  hardware_register = amiga_os_find_hardware_register_by_cpu_address(dest_address);
  return source_quality_display_setup_record_register_write(setup, hardware_register, value);
}

static int source_quality_collect_display_setup_before_offset(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t end_offset, M68kSourceQualityDisplaySetup *setup) {
  size_t candidate_index;
  if (setup != NULL) memset(setup, 0, sizeof(*setup));
  if (section == NULL || accepted_start == NULL || setup == NULL) return 0;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    if (candidate->offset >= end_offset) break;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    (void)source_quality_display_setup_collect_immediate_write(setup, candidate, &instruction);
  }
  return setup->has_bplcon0 || setup->has_diwstrt || setup->has_diwstop ||
    setup->has_ddfstrt || setup->has_ddfstop || setup->has_bpl1mod || setup->has_bpl2mod;
}

static int format_source_quality_display_setup_note(const M68kSourceQualityDisplaySetup *setup, char *buf,
    size_t buf_size) {
  uint32_t plane_count;
  uint32_t fetch_bytes_per_row = 0U;
  uint32_t visible_rows = 0U;
  const char *resolution;
  const char *color;
  int written;
  if (buf != NULL && buf_size != 0U) buf[0] = '\0';
  if (setup == NULL || buf == NULL || buf_size == 0U || !setup->has_bplcon0) return 0;
  plane_count = ((uint32_t)setup->bplcon0 >> 12) & 7U;
  if (plane_count == 0U) return 0;
  resolution = (setup->bplcon0 & 0x8000U) != 0U ? "hires" : "lores";
  color = (setup->bplcon0 & 0x0200U) != 0U ? " color" : "";
  written = snprintf(buf, buf_size, "display setup %u bitplanes %s%s",
    (unsigned)plane_count, resolution, color);
  if (written <= 0 || (size_t)written >= buf_size) return 0;
  if (setup->has_diwstrt && setup->has_diwstop) {
    uint32_t start_v = ((uint32_t)setup->diwstrt >> 8) & 0xFFU;
    uint32_t stop_v = ((uint32_t)setup->diwstop >> 8) & 0xFFU;
    written = snprintf(buf + strlen(buf), buf_size - strlen(buf),
      " window v=$%02X..$%02X h=$%02X..$%02X",
      (unsigned)start_v, (unsigned)stop_v,
      (unsigned)(setup->diwstrt & 0xFFU), (unsigned)(setup->diwstop & 0xFFU));
    if (written <= 0 || (size_t)written >= buf_size - strlen(buf)) return 0;
    if (stop_v > start_v) {
      visible_rows = stop_v - start_v;
      written = snprintf(buf + strlen(buf), buf_size - strlen(buf), " rows %u", (unsigned)visible_rows);
      if (written <= 0 || (size_t)written >= buf_size - strlen(buf)) return 0;
    }
  }
  if (setup->has_ddfstrt && setup->has_ddfstop) {
    uint32_t start_fetch = (uint32_t)setup->ddfstrt & 0xFFU;
    uint32_t stop_fetch = (uint32_t)setup->ddfstop & 0xFFU;
    written = snprintf(buf + strlen(buf), buf_size - strlen(buf),
      " fetch $%02X..$%02X", (unsigned)start_fetch, (unsigned)stop_fetch);
    if (written <= 0 || (size_t)written >= buf_size - strlen(buf)) return 0;
    if (stop_fetch >= start_fetch) {
      fetch_bytes_per_row = (((stop_fetch - start_fetch) >> 3) + 1U) * 2U;
      written = snprintf(buf + strlen(buf), buf_size - strlen(buf),
        " row %u bytes/plane", (unsigned)fetch_bytes_per_row);
      if (written <= 0 || (size_t)written >= buf_size - strlen(buf)) return 0;
    }
  }
  if (setup->has_bpl1mod && setup->has_bpl2mod) {
    written = snprintf(buf + strlen(buf), buf_size - strlen(buf),
      " mod %d/%d", (int)setup->bpl1mod, (int)setup->bpl2mod);
    if (written <= 0 || (size_t)written >= buf_size - strlen(buf)) return 0;
  }
  if (fetch_bytes_per_row != 0U && visible_rows != 0U) {
    written = snprintf(buf + strlen(buf), buf_size - strlen(buf),
      " span $%X/plane", (unsigned)(fetch_bytes_per_row * visible_rows));
    if (written <= 0 || (size_t)written >= buf_size - strlen(buf)) return 0;
  }
  return 1;
}

static int format_source_quality_amiga_audio_register_note(const AmigaOsHardwareRegisterFieldInfo *hardware_field,
    uint32_t value, int has_immediate, char *buf, size_t buf_size) {
  uint32_t word = value & 0xFFFFU;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_field == NULL) return 0;
  if (has_immediate) {
    if (hardware_field->field_symbol_id == AMIGA_OS_SYMBOL_ID_AC_LEN) {
      snprintf(buf, buf_size, "sound sample length %u bytes", (unsigned)(word * 2U));
      return strlen(buf) + 1U < buf_size;
    }
    if (hardware_field->field_symbol_id == AMIGA_OS_SYMBOL_ID_AC_PER) {
      snprintf(buf, buf_size, "audio period %u", (unsigned)word);
      return strlen(buf) + 1U < buf_size;
    }
    if (hardware_field->field_symbol_id == AMIGA_OS_SYMBOL_ID_AC_VOL) {
      snprintf(buf, buf_size, "audio volume %u", (unsigned)word);
      return strlen(buf) + 1U < buf_size;
    }
    return 0;
  }
  if (hardware_field->field_symbol_id == AMIGA_OS_SYMBOL_ID_AC_PER) {
    snprintf(buf, buf_size, "audio period");
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_field->field_symbol_id == AMIGA_OS_SYMBOL_ID_AC_DAT) {
    snprintf(buf, buf_size, "audio data word");
    return strlen(buf) + 1U < buf_size;
  }
  return 0;
}

static uint32_t source_quality_byte_width_for_instruction_size(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0U;
  if (instruction->size_suffix == 'b') return 1U;
  if (instruction->size_suffix == 'w') return 2U;
  if (instruction->size_suffix == 'l') return 4U;
  return 0U;
}

static int format_source_quality_amiga_hardware_register_access_note(
    const AmigaOsHardwareRegisterInfo *hardware_register, uint8_t access_kind, char *buf, size_t buf_size) {
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_register == NULL || access_kind != M68K_SIM_ACCESS_MEMORY_READ) return 0;
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_JOY0DAT) {
    snprintf(buf, buf_size, "joystick/mouse port 0 data");
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_JOY1DAT) {
    snprintf(buf, buf_size, "joystick/mouse port 1 data");
    return strlen(buf) + 1U < buf_size;
  }
  if (hardware_register->symbol_id == AMIGA_OS_SYMBOL_ID_INTREQR) {
    snprintf(buf, buf_size, "interrupt request state");
    return strlen(buf) + 1U < buf_size;
  }
  return 0;
}

static int format_source_quality_amiga_hardware_range_access_note(
    const AmigaOsHardwareRegisterRangeInfo *hardware_range, uint32_t offset, uint8_t access_kind,
    uint32_t byte_width, char *buf, size_t buf_size) {
  uint32_t index;
  uint32_t color_count;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_range == NULL || hardware_range->symbol_id != AMIGA_OS_SYMBOL_ID_COLOR ||
      access_kind != M68K_SIM_ACCESS_MEMORY_WRITE || offset < hardware_range->offset) {
    return 0;
  }
  index = (offset - hardware_range->offset) / 2U;
  color_count = byte_width > 2U ? byte_width / 2U : 1U;
  if (color_count > 1U) {
    snprintf(buf, buf_size, "palette colors %u-%u", (unsigned)index, (unsigned)(index + color_count - 1U));
  } else {
    snprintf(buf, buf_size, "palette color %u", (unsigned)index);
  }
  return strlen(buf) + 1U < buf_size;
}

static int append_hardware_note_platform_semantic_uses_for_section(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start) {
  size_t observation_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  for (observation_index = 0U; observation_index < section_analysis->address_observation_count; ++observation_index) {
    const M68kAddressObservationIR *observation = &section_analysis->address_observations[observation_index];
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsHardwareRegisterInfo *hardware_register;
    const AmigaOsHardwareRegisterFieldInfo *hardware_field;
    const AmigaOsHardwareRegisterRangeInfo *hardware_range;
    M68kPlatformSemanticUseIR use;
    uint32_t value = 0U;
    uint8_t source_index;
    int has_immediate_source = 0;
    char note[160];
    if ((observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER &&
         observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE) ||
        observation->operand_index == UINT32_MAX) {
      continue;
    }
    candidate = m68k_decode_ir_find_candidate_at_offset(section, observation->offset);
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    if (observation->operand_index >= instruction.operand_count) continue;
    hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(observation->address);
    hardware_register = amiga_os_find_hardware_register_by_cpu_address(observation->address);
    hardware_range = amiga_os_find_hardware_register_range_by_cpu_address(observation->address);
    if (hardware_register == NULL && hardware_field == NULL && hardware_range == NULL) continue;
    for (source_index = 0U; source_index < instruction.operand_count; ++source_index) {
      if (source_index == observation->operand_index) continue;
      if (m68k_ir_operand_immediate_value(&instruction.operands[source_index], &value)) {
        has_immediate_source = 1;
        break;
      }
    }
    if (has_immediate_source) {
      value = source_quality_immediate_domain_value_for_instruction_size(&instruction, value);
      if (observation->access_kind != M68K_SIM_ACCESS_MEMORY_WRITE) continue;
      if (format_source_quality_amiga_hardware_value_note(hardware_register, value, note, sizeof(note))) {
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_HARDWARE_VALUE;
      } else if (format_source_quality_amiga_disk_dma_note(hardware_register, value, note, sizeof(note))) {
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_DISK_DMA;
      } else if (format_source_quality_amiga_audio_register_note(hardware_field, value, 1, note, sizeof(note))) {
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_AUDIO_REGISTER;
      } else {
        continue;
      }
    } else {
      if (observation->access_kind != M68K_SIM_ACCESS_MEMORY_WRITE &&
          observation->access_kind != M68K_SIM_ACCESS_MEMORY_READ) {
        continue;
      }
      memset(&use, 0, sizeof(use));
      if (format_source_quality_amiga_audio_register_note(hardware_field, 0U, 0, note, sizeof(note))) {
        use.kind = M68K_PLATFORM_SEMANTIC_USE_AUDIO_REGISTER;
      } else if (format_source_quality_amiga_hardware_register_access_note(hardware_register, observation->access_kind,
          note, sizeof(note)) ||
          format_source_quality_amiga_hardware_range_access_note(hardware_range, observation->owner_offset,
            observation->access_kind, source_quality_byte_width_for_instruction_size(&instruction), note,
            sizeof(note))) {
        use.kind = M68K_PLATFORM_SEMANTIC_USE_HARDWARE_ACCESS;
      } else {
        continue;
      }
    }
    use.offset = candidate->offset;
    use.size = candidate->byte_count;
    use.confidence = observation->confidence;
    use.note_text = note;
    if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
  }
  return 0;
}

static int append_hardware_note_platform_semantic_uses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, NULL);
    if (section == NULL || section->section_index >= decode->section_count) continue;
    if (append_hardware_note_platform_semantic_uses_for_section(section_analysis, section,
        accepted_start[section->section_index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static int source_quality_section_has_label_at(const M68kSectionAnalysisIR *section, uint32_t offset);
static int source_quality_copper_list_item_renders_word_row_at(const M68kSourceAnalysisIR *source_analysis,
    const M68kSectionAnalysisIR *section_analysis, size_t section_index, uint32_t offset);

static int append_copper_runtime_pointer_word_symbol_access_and_use(M68kSectionAnalysisIR *section,
    uint32_t offset, const char *symbol_name, uint32_t runtime_address, uint32_t role_flags, uint8_t confidence) {
  M68kExpectedSymbolAccessIR access;
  M68kPlatformSemanticUseIR use;
  if (section == NULL || symbol_name == NULL || symbol_name[0] == '\0' || runtime_address == 0U ||
      role_flags == 0U) {
    return 0;
  }
  memset(&access, 0, sizeof(access));
  access.symbol_name = (char *)symbol_name;
  access.producer = "copper_runtime_pointer_word_symbol";
  access.offset = offset;
  access.operand_index = UINT32_MAX;
  access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_EQUATE;
  access.confidence = confidence;
  if (m68k_ir_section_analysis_append_expected_symbol_access(section, &access) != 0) return -1;
  memset(&use, 0, sizeof(use));
  use.kind = M68K_PLATFORM_SEMANTIC_USE_COPPER_ROW;
  use.offset = offset;
  use.size = 4U;
  use.role_flags = role_flags;
  use.confidence = confidence;
  use.has_operand_expr = 1U;
  use.operand_expr = (char *)symbol_name;
  use.operand_index = UINT32_MAX;
  use.has_runtime_address = 1U;
  use.runtime_address = runtime_address;
  return m68k_ir_section_analysis_append_platform_semantic_use(section, &use);
}

static int append_structured_copper_row_platform_semantic_uses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode) {
  size_t item_index;
  if (source_analysis == NULL || decode == NULL) return 0;
  for (item_index = 0U; item_index < source_analysis->structured_data_item_count; ++item_index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[item_index];
    M68kSectionAnalysisIR *section_analysis;
    const M68kDecodeSectionIR *section;
    uint32_t cursor = 0U;
    int raw_word_mode = 0;
    if (!item->has_section_index || item->size < 4U ||
        (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST) == 0U) {
      continue;
    }
    section_analysis = source_analysis_section_by_index(source_analysis, item->section_index);
    section = source_quality_decode_section_by_index(decode, item->section_index, NULL);
    if (section_analysis == NULL || section == NULL || section->data == NULL ||
        item->offset > section->size || item->size > section->size - item->offset) {
      continue;
    }
    {
      char note[160];
      M68kPlatformSemanticUseIR use;
      if (format_source_quality_copper_display_layout_note(section->data, item->offset, item->size,
          note, sizeof(note))) {
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_COPPER_DISPLAY_LAYOUT;
        use.offset = item->offset;
        use.size = item->size;
        use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
        use.note_text = note;
        if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
      }
    }
    while (cursor + 4U <= item->size) {
      uint32_t row_offset = item->offset + cursor;
      uint16_t first;
      uint16_t second;
      char note[160];
      M68kPlatformSemanticUseIR use;
      if (raw_word_mode) {
        cursor += 2U;
        continue;
      }
      if (cursor + 2U < item->size && source_quality_section_has_label_at(section_analysis, row_offset + 2U)) {
        cursor += 2U;
        raw_word_mode = 1;
        continue;
      }
      first = m68k_read_u16be(section->data + row_offset);
      second = m68k_read_u16be(section->data + row_offset + 2U);
      if (first == 0xFFFFU && second == 0xFFFEU) {
        cursor += 4U;
        continue;
      }
      if (format_source_quality_copper_wait_note(first, second, note, sizeof(note)) ||
          format_source_quality_copper_display_row_note(first, second, note, sizeof(note)) ||
          format_source_quality_copper_runtime_pointer_note(section->data, item->offset, cursor, item->size,
            first, second, note, sizeof(note))) {
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_COPPER_ROW;
        use.offset = row_offset;
        use.size = 4U;
        use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
        use.note_text = note;
        if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
      }
      {
        uint32_t pointer_address = 0U;
        uint32_t role_flags = 0U;
        const char *role = NULL;
        char high_symbol[80];
        char low_symbol[80];
        if (source_quality_copper_runtime_pointer_details_at(section->data, item->offset, cursor, item->size,
            &pointer_address, &role_flags, &role) &&
            source_quality_copper_list_item_renders_word_row_at(source_analysis, section_analysis,
              item->section_index, row_offset) &&
            source_quality_copper_list_item_renders_word_row_at(source_analysis, section_analysis,
              item->section_index, row_offset + 4U)) {
          platform_format_runtime_address_symbol_name(role, pointer_address, "_hi", high_symbol,
            sizeof(high_symbol));
          platform_format_runtime_address_symbol_name(role, pointer_address, "_lo", low_symbol,
            sizeof(low_symbol));
          if (append_copper_runtime_pointer_word_symbol_access_and_use(section_analysis, row_offset, high_symbol,
              pointer_address, role_flags, M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
            return -1;
          }
          if (append_copper_runtime_pointer_word_symbol_access_and_use(section_analysis, row_offset + 4U,
              low_symbol, pointer_address, role_flags, M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
            return -1;
          }
        }
      }
      cursor += 4U;
    }
  }
  return 0;
}

static int source_quality_has_copper_list_item_at(const M68kSourceAnalysisIR *source_analysis,
    size_t section_index, uint32_t offset) {
  size_t item_index;
  if (source_analysis == NULL) return 0;
  for (item_index = 0U; item_index < source_analysis->structured_data_item_count; ++item_index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[item_index];
    if (item->has_section_index && item->section_index == section_index && item->offset == offset &&
        (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST) != 0U) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_copper_list_item_renders_word_row_at(const M68kSourceAnalysisIR *source_analysis,
    const M68kSectionAnalysisIR *section_analysis, size_t section_index, uint32_t offset) {
  size_t item_index;
  const M68kAnalysisStructuredDataItem *selected_item = NULL;
  if (source_analysis == NULL || section_analysis == NULL || section_index > UINT32_MAX) return 0;
  for (item_index = 0U; item_index < source_analysis->structured_data_item_count; ++item_index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[item_index];
    if (!item->has_section_index || item->section_index != section_index || item->size == 0U ||
        item->kind != M68K_ANALYSIS_STRUCTURED_DATA_WORDS ||
        (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST) == 0U ||
        item->offset > UINT32_MAX - item->size ||
        offset < item->offset || offset >= item->offset + item->size) {
      continue;
    }
    if (selected_item == NULL || item->offset > selected_item->offset) {
      selected_item = item;
    }
  }
  if (selected_item == NULL) return 0;
  for (item_index = 0U; item_index < source_analysis->structured_data_item_count; ++item_index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[item_index];
    if (item == selected_item || !item->has_section_index || item->section_index != section_index) continue;
    if (item->offset > selected_item->offset && item->offset < selected_item->offset + selected_item->size) {
      return 0;
    }
  }
  {
    uint32_t cursor = 0U;
    int raw_word_mode = 0;
    while (cursor + 4U <= selected_item->size) {
      uint32_t row_offset = selected_item->offset + cursor;
      if (raw_word_mode) {
        if (row_offset == offset) return 0;
        cursor += 2U;
        continue;
      }
      if (cursor + 2U < selected_item->size &&
          source_quality_section_has_label_at(section_analysis, row_offset + 2U)) {
        if (row_offset == offset) return 0;
        cursor += 2U;
        raw_word_mode = 1;
        continue;
      }
      if (row_offset == offset) return 1;
      cursor += 4U;
    }
  }
  return 0;
}

static int append_copper_display_setup_platform_semantic_uses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, NULL);
    size_t ref_index;
    if (section == NULL || section->section_index >= decode->section_count) continue;
    for (ref_index = 0U; ref_index < section_analysis->runtime_address_ref_count; ++ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section_analysis->runtime_address_refs[ref_index];
      M68kSectionAnalysisIR *target_section;
      M68kSourceQualityDisplaySetup setup;
      M68kPlatformSemanticUseIR use;
      char note[192];
      if ((ref->data_class_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST) == 0U ||
          !ref->has_target || ref->target_section_index > UINT32_MAX ||
          !source_quality_has_copper_list_item_at(source_analysis, ref->target_section_index, ref->target_offset)) {
        continue;
      }
      target_section = source_analysis_section_by_index(source_analysis, (uint32_t)ref->target_section_index);
      if (target_section == NULL) continue;
      if (!source_quality_collect_display_setup_before_offset(section, accepted_start[section->section_index],
          ref->offset, &setup) ||
          !format_source_quality_display_setup_note(&setup, note, sizeof(note))) {
        continue;
      }
      memset(&use, 0, sizeof(use));
      use.kind = M68K_PLATFORM_SEMANTIC_USE_DISPLAY_SETUP;
      use.offset = ref->target_offset;
      use.size = ref->size;
      use.confidence = ref->confidence;
      use.has_target = 1U;
      use.target_section_index = (uint32_t)ref->target_section_index;
      use.target_offset = ref->target_offset;
      use.note_text = note;
      if (m68k_ir_section_analysis_append_platform_semantic_use(target_section, &use) != 0) return -1;
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
    accepted_start != NULL && candidate->offset < section->size && accepted_start[candidate->offset] != 0U &&
    m68k_decode_ir_find_candidate_at_offset(section, candidate->offset) == candidate;
}

static const AmigaOsHardwareRegisterInfo *source_quality_runtime_sink_register_for_cpu_address(uint32_t address) {
  const AmigaOsHardwareRegisterInfo *hardware_register = amiga_os_find_hardware_register_by_cpu_address(address);
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  if (hardware_register == NULL) {
    hardware_range = amiga_os_find_hardware_register_range_by_cpu_address(address);
    if (hardware_range != NULL) {
      hardware_register =
        amiga_os_find_hardware_register_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM, hardware_range->offset);
    }
  }
  if (hardware_register == NULL ||
      (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U ||
      hardware_register->runtime_target_kind == AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_NONE ||
      hardware_register->runtime_target_role == NULL ||
      hardware_register->runtime_target_role[0] == '\0') {
    return NULL;
  }
  return hardware_register;
}

static const AmigaOsHardwareRegisterInfo *source_quality_runtime_sink_register_for_base_id_offset(
    uint16_t base_id, uint32_t offset) {
  const AmigaOsHardwareRegisterInfo *hardware_register =
    amiga_os_find_hardware_register_by_base_id_offset(base_id, offset);
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  if (hardware_register == NULL) {
    hardware_range = amiga_os_find_hardware_register_range_by_base_id_offset(base_id, offset);
    if (hardware_range != NULL) {
      hardware_register = amiga_os_find_hardware_register_by_base_id_offset(base_id, hardware_range->offset);
    }
  }
  if (hardware_register == NULL ||
      (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U ||
      hardware_register->runtime_target_kind == AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_NONE ||
      hardware_register->runtime_target_role == NULL ||
      hardware_register->runtime_target_role[0] == '\0') {
    return NULL;
  }
  return hardware_register;
}

static const M68kRuntimeAddressRefIR *source_quality_runtime_sink_ref_for_offset(
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint32_t sink_address) {
  size_t index;
  if (section_analysis == NULL) return NULL;
  for (index = 0U; index < section_analysis->runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *ref = &section_analysis->runtime_address_refs[index];
    if (ref->offset != offset || !ref->has_runtime_address || ref->runtime_address == 0U) continue;
    if (ref->has_sink_address && ref->sink_address != sink_address) continue;
    return ref;
  }
  return NULL;
}

static int source_quality_runtime_sink_has_dynamic_source_use(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return 0;
  for (index = 0U; index < section_analysis->platform_semantic_use_count; ++index) {
    const M68kPlatformSemanticUseIR *use = &section_analysis->platform_semantic_uses[index];
    if (use->offset != offset) continue;
    if (use->kind == M68K_PLATFORM_SEMANTIC_USE_AUDIO_POINTER_SOURCE &&
        (use->has_secondary_target ||
         (use->note_text != NULL && strcmp(use->note_text, "dynamic_offset") == 0))) {
      return 1;
    }
  }
  return 0;
}

static int append_expected_runtime_sink_operand_symbol_access_at(M68kSectionAnalysisIR *section,
    uint32_t offset, uint32_t operand_index, uint8_t confidence, const char *symbol);

static int source_quality_runtime_address_maps_to_materialized_source(const M68kSectionAnalysisIR *section,
    uint32_t runtime_address);

static int source_quality_runtime_address_to_materialized_source(const M68kSourceAnalysisIR *source_analysis,
    uint32_t runtime_address, uint32_t *out_section_index, uint32_t *out_offset);

static int source_quality_runtime_address_maps_to_any_materialized_source(const M68kSourceAnalysisIR *source_analysis,
    uint32_t runtime_address);

static const M68kAddressObservationIR *source_quality_address_observation_for_candidate_operand(
    const M68kSectionAnalysisIR *section, const M68kDecodeCandidate *candidate, size_t operand_index);

static int source_quality_candidate_data_target_for_operand(const M68kDecodeCandidate *candidate,
    uint32_t operand_index, uint32_t *out_section_index, uint32_t *out_offset);

static const M68kFact *source_quality_unique_relocation_ref_for_operand(const M68kFactIR *facts,
    size_t section_index, const M68kDecodeCandidate *candidate, size_t operand_index);

static int source_quality_unique_symbol_origin_at_storage_offset(const M68kSourceAnalysisIR *source_analysis,
    uint32_t storage_offset, uint32_t *out_section_index, uint32_t *out_offset) {
  size_t section_index;
  uint32_t match_section_index = 0U;
  uint32_t match_offset = 0U;
  uint32_t match_count = 0U;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (source_analysis == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    if (storage_offset >= section->section_size) continue;
    if (source_quality_symbol_origin_at(section, storage_offset) == NULL) continue;
    match_section_index = (uint32_t)section->section_index;
    match_offset = storage_offset;
    ++match_count;
  }
  if (match_count != 1U) return 0;
  if (out_section_index != NULL) *out_section_index = match_section_index;
  if (out_offset != NULL) *out_offset = match_offset;
  return 1;
}

static void source_quality_runtime_sink_note_text(const M68kSectionAnalysisIR *section_analysis,
    const AmigaOsHardwareRegisterInfo *hardware_register, const M68kRuntimeAddressRefIR *runtime_ref,
    uint32_t offset, char *note, size_t note_size) {
  if (note == NULL || note_size == 0U || hardware_register == NULL) return;
  if (runtime_ref != NULL && !runtime_ref->has_target &&
      !source_quality_runtime_sink_has_dynamic_source_use(section_analysis, offset)) {
    snprintf(note, note_size, "%s pointer $%08X", hardware_register->runtime_target_role,
      (unsigned)runtime_ref->runtime_address);
  } else {
    snprintf(note, note_size, "%s pointer", hardware_register->runtime_target_role);
  }
}

static void source_quality_runtime_sink_set_operand_fact(M68kPlatformSemanticUseIR *use,
    const M68kSourceAnalysisIR *source_analysis, const M68kSectionAnalysisIR *section_analysis,
    const AmigaOsHardwareRegisterInfo *hardware_register, const M68kRuntimeAddressRefIR *runtime_ref,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    char *operand_expr, size_t operand_expr_size) {
  uint32_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  uint32_t value = 0U;
  if (use == NULL || runtime_ref == NULL || instruction == NULL ||
      runtime_ref->operand_index >= instruction->operand_count ||
      !m68k_ir_operand_immediate_value(&instruction->operands[runtime_ref->operand_index], &value) ||
      !runtime_ref->has_runtime_address || value != runtime_ref->runtime_address) {
    return;
  }
  use->operand_index = runtime_ref->operand_index;
  if (source_quality_candidate_data_target_for_operand(candidate, runtime_ref->operand_index,
      &target_section_index, &target_offset)) {
    use->has_target = 1U;
    use->target_section_index = target_section_index;
    use->target_offset = target_offset;
    return;
  }
  if (runtime_ref->has_target && runtime_ref->target_section_index <= UINT32_MAX) {
    use->has_target = 1U;
    use->target_section_index = (uint32_t)runtime_ref->target_section_index;
    use->target_offset = runtime_ref->target_offset;
    return;
  }
  if (source_quality_unique_symbol_origin_at_storage_offset(source_analysis, runtime_ref->runtime_address,
      &target_section_index, &target_offset)) {
    use->has_target = 1U;
    use->target_section_index = target_section_index;
    use->target_offset = target_offset;
    return;
  }
  if (source_quality_runtime_address_maps_to_any_materialized_source(source_analysis, runtime_ref->runtime_address) ||
      source_quality_runtime_address_maps_to_materialized_source(section_analysis, runtime_ref->runtime_address)) {
    return;
  }
  if (hardware_register == NULL || hardware_register->runtime_target_role == NULL ||
      hardware_register->runtime_target_role[0] == '\0' || operand_expr == NULL || operand_expr_size == 0U) {
    return;
  }
  platform_format_runtime_address_symbol_name(hardware_register->runtime_target_role, runtime_ref->runtime_address, "",
    operand_expr, operand_expr_size);
  if (operand_expr[0] == '\0') return;
  use->operand_expr = operand_expr;
  use->has_operand_expr = 1U;
  use->runtime_address = runtime_ref->runtime_address;
  use->has_runtime_address = 1U;
}

static int append_runtime_sink_pointer_semantic_uses_for_section(M68kSectionAnalysisIR *section_analysis,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start) {
  size_t observation_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  for (observation_index = 0U; observation_index < section_analysis->address_observation_count; ++observation_index) {
    const M68kAddressObservationIR *observation = &section_analysis->address_observations[observation_index];
    const AmigaOsHardwareRegisterInfo *hardware_register;
    const M68kDecodeCandidate *candidate;
    const M68kRuntimeAddressRefIR *runtime_ref;
    M68kInstructionIR instruction;
    M68kPlatformSemanticUseIR use;
    char note[160];
    char operand_expr[M68K_IR_SYMBOL_NAME_SIZE];
    if (!observation->has_address ||
        observation->access_kind != M68K_SIM_ACCESS_MEMORY_WRITE ||
        (observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER &&
         observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE)) {
      continue;
    }
    hardware_register = source_quality_runtime_sink_register_for_cpu_address(observation->address);
    if (hardware_register == NULL) continue;
    candidate = m68k_decode_ir_find_candidate_at_offset(section, observation->offset);
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    runtime_ref = source_quality_runtime_sink_ref_for_offset(section_analysis, observation->offset,
      observation->address);
    source_quality_runtime_sink_note_text(section_analysis, hardware_register, runtime_ref, observation->offset, note,
      sizeof(note));
    memset(&use, 0, sizeof(use));
    use.kind = M68K_PLATFORM_SEMANTIC_USE_RUNTIME_SINK_POINTER;
    use.offset = candidate->offset;
    use.size = candidate->byte_count;
    use.role_flags = platform_facts_v2_runtime_address_sink_data_class_flags(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
      observation->address);
    use.confidence = runtime_ref != NULL ? runtime_ref->confidence : M68K_FACT_CONFIDENCE_TOOL_INFERRED;
    use.note_text = note;
    source_quality_runtime_sink_set_operand_fact(&use, source_analysis, section_analysis, hardware_register, runtime_ref,
      candidate, &instruction, operand_expr, sizeof(operand_expr));
    if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
    if (use.has_operand_expr &&
        append_expected_runtime_sink_operand_symbol_access_at(section_analysis, candidate->offset,
          use.operand_index, use.confidence, use.operand_expr) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_runtime_sink_pointer_semantic_uses(M68kSourceAnalysisIR *source_analysis,
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
    if (append_runtime_sink_pointer_semantic_uses_for_section(section_analysis, source_analysis, section,
        accepted_start[decode_index]) != 0) {
      return -1;
    }
  }
  return 0;
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

static const M68kFact *source_quality_unique_relocation_ref_for_span(const M68kFactIR *facts,
    size_t section_index, uint32_t span_start, uint32_t span_size) {
  const M68kFact *match = NULL;
  size_t fact_index;
  if (facts == NULL || span_size == 0U) return NULL;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    if (!source_quality_relocation_exactly_covers_span(fact, section_index, span_start, span_size)) continue;
    if (match != NULL) return NULL;
    match = fact;
  }
  return match;
}

static int source_quality_has_structured_data_item(const M68kSourceAnalysisIR *source_analysis,
    uint32_t section_index, uint32_t offset, uint32_t size, uint8_t kind, uint8_t source_pattern_id) {
  size_t index;
  if (source_analysis == NULL) return 0;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    if (item->has_section_index && item->section_index == section_index && item->offset == offset &&
        item->size == size && item->kind == kind && item->source_pattern_id == source_pattern_id) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_has_structured_data_item_with_role(const M68kSourceAnalysisIR *source_analysis,
    uint32_t section_index, uint32_t offset, uint32_t size, uint8_t kind, uint32_t role_flags) {
  size_t index;
  if (source_analysis == NULL || role_flags == 0U) return 0;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    if (item->has_section_index && item->section_index == section_index && item->offset == offset &&
        item->size == size && item->kind == kind && item->semantic_role_flags == role_flags) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_has_structured_data_role_at_offset(const M68kSourceAnalysisIR *source_analysis,
    uint32_t section_index, uint32_t offset, uint32_t role_flags) {
  size_t index;
  if (source_analysis == NULL || role_flags == 0U) return 0;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    if (!item->has_section_index || item->section_index != section_index || item->offset != offset) continue;
    if ((item->semantic_role_flags & role_flags) != 0U) return 1;
  }
  return 0;
}

static uint32_t source_quality_copper_list_size_at(const M68kDecodeSectionIR *section, uint32_t offset) {
  uint32_t cursor;
  if (section == NULL || section->data == NULL || offset >= section->size || section->size - offset < 4U)
    return 0U;
  for (cursor = offset; cursor + 4U <= section->size; cursor += 4U) {
    uint16_t first = m68k_read_u16be(section->data + cursor);
    uint16_t second = m68k_read_u16be(section->data + cursor + 2U);
    if (first == 0xFFFFU && second == 0xFFFEU) return cursor + 4U - offset;
  }
  return 0U;
}

static uint8_t source_quality_collect_copper_bitmap_pointer_rows(const uint8_t *data, uint32_t offset,
    uint32_t size, uint32_t *row_offsets, uint32_t *pointers, uint8_t pointer_limit) {
  uint32_t cursor;
  uint8_t pointer_count = 0U;
  if (data == NULL || pointers == NULL || pointer_limit == 0U || size == 0U) return 0U;
  for (cursor = 0U; cursor + 8U <= size && pointer_count < pointer_limit; cursor += 4U) {
    uint32_t pointer = 0U;
    if (!source_quality_copper_bitmap_pointer_at(data, offset, cursor, size, &pointer)) continue;
    if (row_offsets != NULL) row_offsets[pointer_count] = offset + cursor;
    pointers[pointer_count++] = pointer;
  }
  return pointer_count;
}

static int append_source_quality_runtime_address_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kRuntimeAddressRefIR *ref) {
  if (section_analysis == NULL || ref == NULL) return -1;
  return m68k_ir_section_analysis_append_runtime_address_ref(section_analysis, ref);
}

static int append_source_quality_inferred_bitmap_runtime_refs_for_copper_list(
    M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section, uint32_t offset, uint32_t size) {
  uint32_t row_offsets[8];
  uint32_t pointers[8];
  uint32_t step;
  uint8_t index;
  uint8_t pointer_count;
  const char *role_name;
  if (section_analysis == NULL || section == NULL || section->data == NULL) return 0;
  pointer_count = source_quality_collect_copper_bitmap_pointer_rows(section->data, offset, size, row_offsets,
    pointers, (uint8_t)(sizeof(pointers) / sizeof(pointers[0])));
  if (pointer_count == 0U) return 0;
  step = source_quality_copper_bitmap_pointer_even_step(pointers, pointer_count);
  role_name = m68k_analysis_structured_data_role_name_for_flags(M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP);
  if (role_name == NULL) return 0;
  for (index = 0U; index < pointer_count; ++index) {
    M68kRuntimeAddressRefIR ref;
    memset(&ref, 0, sizeof(ref));
    ref.offset = row_offsets[index];
    ref.source_size = 4U;
    ref.operand_index = UINT32_MAX;
    ref.size = step;
    ref.has_runtime_address = 1U;
    ref.runtime_address = pointers[index];
    ref.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
    ref.data_class_flags = M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP;
    ref.data_class = (char *)role_name;
    if (append_source_quality_runtime_address_ref(section_analysis, &ref) != 0) return -1;
  }
  return 0;
}

static int source_quality_runtime_ref_sink_address(const M68kDecodeSectionIR *section,
    const M68kRuntimeAddressRefIR *ref, uint32_t *out_sink_address) {
  const M68kDecodeCandidate *candidate;
  M68kInstructionIR instruction;
  if (out_sink_address != NULL) *out_sink_address = 0U;
  if (section == NULL || ref == NULL || out_sink_address == NULL) return 0;
  if (ref->has_sink_address) {
    *out_sink_address = ref->sink_address;
    return 1;
  }
  candidate = m68k_decode_ir_find_candidate_at_offset(section, ref->offset);
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      !((ref->operand_index == 0U || ref->operand_index == UINT32_MAX) &&
        instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction.size_suffix == 'l' &&
        instruction.operand_count == 2U)) {
    return 0;
  }
  return source_quality_candidate_operand_absolute_value(candidate, 1U, out_sink_address);
}

static int source_quality_candidate_immediate_audio_length_bytes(const M68kDecodeCandidate *candidate,
    uint32_t audio_register_offset, uint32_t *out_size) {
  M68kInstructionIR instruction;
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  uint32_t immediate = 0U;
  uint32_t dest_address = 0U;
  if (out_size != NULL) *out_size = 0U;
  if (candidate == NULL || out_size == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
      candidate->size_suffix != 'w' || candidate->operand_count != 2U) {
    return 0;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      !m68k_ir_operand_immediate_value(&instruction.operands[0], &immediate) ||
      !source_quality_candidate_operand_absolute_value(candidate, 1U, &dest_address)) {
    return 0;
  }
  hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(dest_address);
  if (hardware_field == NULL ||
      hardware_field->register_offset != audio_register_offset ||
      hardware_field->field_symbol_id != AMIGA_OS_SYMBOL_ID_AC_LEN) {
    return 0;
  }
  *out_size = (immediate & 0xFFFFU) * 2U;
  return *out_size != 0U;
}

static uint32_t source_quality_sound_sample_size_from_nearby_audio_length_write(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kRuntimeAddressRefIR *ref, uint32_t sink_address) {
  const M68kDecodeCandidate *pointer_candidate;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  uint32_t cursor;
  uint8_t step;
  if (section == NULL || accepted_start == NULL || ref == NULL) return 0U;
  hardware_register = amiga_os_find_hardware_register_by_cpu_address(sink_address);
  if (hardware_register == NULL ||
      hardware_register->runtime_target_kind != AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_SOUND_SAMPLE) {
    return 0U;
  }
  pointer_candidate = m68k_decode_ir_find_candidate_at_offset(section, ref->offset);
  if (pointer_candidate == NULL || pointer_candidate->byte_count == 0U) return 0U;
  cursor = pointer_candidate->offset + pointer_candidate->byte_count;
  for (step = 0U; step < 4U && cursor < section->size && accepted_start[cursor] != 0U; ++step) {
    const M68kDecodeCandidate *candidate = m68k_decode_ir_find_candidate_at_offset(section, cursor);
    uint32_t size = 0U;
    if (candidate == NULL || candidate->byte_count == 0U) return 0U;
    if (source_quality_candidate_immediate_audio_length_bytes(candidate, hardware_register->offset, &size))
      return size;
    cursor += candidate->byte_count;
  }
  return 0U;
}

static int append_platform_runtime_structured_data_item(M68kSourceAnalysisIR *source_analysis,
    uint32_t section_index, uint32_t offset, uint32_t size, uint8_t kind, uint32_t role_flags) {
  M68kAnalysisStructuredDataItem item;
  if (source_analysis == NULL || size == 0U || role_flags == 0U ||
      m68k_analysis_structured_data_role_name_for_flags(role_flags) == NULL ||
      source_quality_has_structured_data_role_at_offset(source_analysis, section_index, offset, role_flags) ||
      source_quality_has_structured_data_item_with_role(source_analysis, section_index, offset, size, kind,
        role_flags)) {
    return 0;
  }
  memset(&item, 0, sizeof(item));
  item.has_section_index = 1U;
  item.section_index = section_index;
  item.offset = offset;
  item.size = size;
  item.kind = kind;
  item.entry_count_proof_id = M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_STRUCTURED_RANGE;
  m68k_analysis_structured_data_item_set_semantic_role_flags(&item, role_flags);
  return m68k_ir_source_analysis_append_structured_data_item(source_analysis, &item);
}

static int append_platform_runtime_structured_data_items(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    size_t ref_index;
    if (section == NULL) continue;
    for (ref_index = 0U; ref_index < section_analysis->runtime_address_ref_count; ++ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section_analysis->runtime_address_refs[ref_index];
      uint32_t size = 0U;
      uint8_t kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
      uint32_t role_flags = 0U;
      if (!ref->has_target || ref->target_section_index > UINT32_MAX ||
          ref->target_section_index >= decode->section_count) {
        continue;
      }
      if ((ref->data_class_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST) != 0U) {
        const M68kDecodeSectionIR *target_section = source_quality_decode_section_by_index(decode,
          (uint32_t)ref->target_section_index, NULL);
        M68kSectionAnalysisIR *target_analysis;
        size = source_quality_copper_list_size_at(target_section, ref->target_offset);
        role_flags = M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST;
        kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
        if (size == 0U) continue;
        if (append_platform_runtime_structured_data_item(source_analysis, (uint32_t)ref->target_section_index,
            ref->target_offset, size, kind, role_flags) != 0) {
          return -1;
        }
        target_analysis = source_analysis_section_by_index(source_analysis, (uint32_t)ref->target_section_index);
        if (target_analysis != NULL &&
            append_source_quality_inferred_bitmap_runtime_refs_for_copper_list(target_analysis, target_section,
              ref->target_offset, size) != 0) {
          return -1;
        }
        continue;
      } else if ((ref->data_class_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE) != 0U &&
          accepted_start != NULL) {
        uint32_t sink_address = 0U;
        if (!source_quality_runtime_ref_sink_address(section, ref, &sink_address)) continue;
        size = source_quality_sound_sample_size_from_nearby_audio_length_write(section, accepted_start[decode_index],
          ref, sink_address);
        role_flags = M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE;
        kind = M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
        if (size != 0U) {
          if (append_platform_runtime_structured_data_item(source_analysis, (uint32_t)ref->target_section_index,
              ref->target_offset, size, kind, role_flags) != 0) {
            return -1;
          }
        }
      }
    }
  }
  return 0;
}

typedef struct M68kSourceQualityBitmapRuntimeAddress {
  uint8_t matched;
  uint8_t plane_index;
  uint32_t base;
  uint32_t size;
  uint32_t delta;
} M68kSourceQualityBitmapRuntimeAddress;

typedef struct M68kSourceQualityBitmapBaseState {
  M68kSourceQualityBitmapRuntimeAddress address_regs[8];
} M68kSourceQualityBitmapBaseState;

static int source_quality_operand_address_memory(const M68kOperandIR *operand, uint8_t *out_reg,
    int16_t *out_displacement) {
  if (out_reg != NULL) *out_reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (operand == NULL ||
      (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
      operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (operand->value.ea_mode == 2U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  if (operand->value.ea_mode == 5U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    if (out_displacement != NULL) *out_displacement = (int16_t)(operand->value.value & 0xFFFFU);
    return 1;
  }
  return 0;
}

static int source_quality_bitmap_runtime_address_for_value(const M68kSectionAnalysisIR *section,
    uint32_t value, M68kSourceQualityBitmapRuntimeAddress *out_address) {
  size_t index;
  uint8_t plane_index = 0U;
  if (out_address != NULL) memset(out_address, 0, sizeof(*out_address));
  if (section == NULL || out_address == NULL) return 0;
  for (index = 0U; index < section->runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[index];
    uint32_t base;
    uint32_t size;
    if ((ref->data_class_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) == 0U ||
        !ref->has_runtime_address || ref->size == 0U) {
      continue;
    }
    base = ref->runtime_address;
    size = ref->size;
    if (value >= base && value - base < size) {
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

static int append_source_quality_bitmap_memory_runtime_ref(M68kSectionAnalysisIR *section,
    uint32_t offset, const M68kSourceQualityBitmapRuntimeAddress *address) {
  M68kRuntimeAddressRefIR ref;
  const char *role_name;
  if (section == NULL || address == NULL || !address->matched) return 0;
  role_name = m68k_analysis_structured_data_role_name_for_flags(M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP);
  if (role_name == NULL) return 0;
  memset(&ref, 0, sizeof(ref));
  ref.offset = offset;
  ref.operand_index = UINT32_MAX;
  ref.has_runtime_address = 1U;
  ref.runtime_address = address->base + address->delta;
  ref.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  ref.data_class_flags = M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP;
  ref.data_class = (char *)role_name;
  return append_source_quality_runtime_address_ref(section, &ref);
}

static int source_quality_operand_runtime_address_from_bitmap_base(
    const M68kSourceQualityBitmapBaseState *state, const M68kOperandIR *operand,
    M68kSourceQualityBitmapRuntimeAddress *out_address) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  int64_t value;
  const M68kSourceQualityBitmapRuntimeAddress *base;
  if (out_address != NULL) memset(out_address, 0, sizeof(*out_address));
  if (state == NULL || operand == NULL || out_address == NULL ||
      !source_quality_operand_address_memory(operand, &base_reg, &displacement) || base_reg >= 8U ||
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

static int source_quality_instruction_immediate_address_register_load(const M68kInstructionIR *instruction,
    uint32_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (instruction == NULL || out_value == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA ||
      instruction->operand_count != 2U ||
      !source_quality_operand_address_register_index(&instruction->operands[1], NULL)) {
    return 0;
  }
  return m68k_ir_operand_immediate_value(&instruction->operands[0], out_value);
}

static int append_bitmap_memory_runtime_refs_for_instruction(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    const M68kSourceQualityBitmapBaseState *state) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint32_t immediate_address = 0U;
  if (section_analysis == NULL || candidate == NULL || instruction == NULL) return 0;
  if (source_quality_instruction_immediate_address_register_load(instruction, &immediate_address)) {
    M68kSourceQualityBitmapRuntimeAddress address;
    if (source_quality_bitmap_runtime_address_for_value(section_analysis, immediate_address, &address) &&
        append_source_quality_bitmap_memory_runtime_ref(section_analysis, candidate->offset, &address) != 0) {
      return -1;
    }
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    M68kSourceQualityBitmapRuntimeAddress address;
    uint32_t absolute = 0U;
    uint8_t access = metadata != NULL && operand_index < 4U ?
      metadata->operand_access_kinds[operand_index] : M68K_SIM_ACCESS_NONE;
    if (source_quality_operand_absolute_offset(operand, &absolute) &&
        source_quality_bitmap_runtime_address_for_value(section_analysis, absolute, &address)) {
      if (append_source_quality_bitmap_memory_runtime_ref(section_analysis, candidate->offset, &address) != 0)
        return -1;
      continue;
    }
    if ((access == M68K_SIM_ACCESS_MEMORY_READ || access == M68K_SIM_ACCESS_MEMORY_WRITE) &&
        source_quality_operand_runtime_address_from_bitmap_base(state, operand, &address)) {
      if (append_source_quality_bitmap_memory_runtime_ref(section_analysis, candidate->offset, &address) != 0)
        return -1;
    }
  }
  return 0;
}

static void source_quality_bitmap_base_state_update_after_instruction(
    M68kSourceQualityBitmapBaseState *state, const M68kSectionAnalysisIR *section_analysis,
    const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  M68kSourceQualityBitmapRuntimeAddress absolute_address;
  uint8_t has_absolute_address = 0U;
  uint32_t immediate_address = 0U;
  size_t operand_index;
  if (state == NULL || section_analysis == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return;
  memset(&absolute_address, 0, sizeof(absolute_address));
  if (source_quality_instruction_immediate_address_register_load(instruction, &immediate_address) &&
      source_quality_bitmap_runtime_address_for_value(section_analysis, immediate_address, &absolute_address)) {
    has_absolute_address = 1U;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    uint32_t absolute = 0U;
    if (has_absolute_address) break;
    if (source_quality_operand_absolute_offset(&instruction->operands[operand_index], &absolute) &&
        source_quality_bitmap_runtime_address_for_value(section_analysis, absolute, &absolute_address)) {
      has_absolute_address = 1U;
      break;
    }
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        source_quality_operand_address_register_index(&instruction->operands[operand_index], &reg) && reg < 8U) {
      if (has_absolute_address) state->address_regs[reg] = absolute_address;
      else memset(&state->address_regs[reg], 0, sizeof(state->address_regs[reg]));
    } else if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_LIST_WRITE) {
      uint8_t bit;
      for (bit = 0U; bit < 8U; ++bit) {
        if (source_quality_reglist_contains_register(&instruction->operands[operand_index], 2U, bit))
          memset(&state->address_regs[bit], 0, sizeof(state->address_regs[bit]));
      }
    }
    if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_NONE &&
        source_quality_operand_address_memory(&instruction->operands[operand_index], &reg, NULL) && reg < 8U) {
      memset(&state->address_regs[reg], 0, sizeof(state->address_regs[reg]));
    }
  }
}

static int append_bitmap_memory_runtime_refs(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    M68kSourceQualityBitmapBaseState state;
    size_t candidate_index;
    if (section == NULL) continue;
    memset(&state, 0, sizeof(state));
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      if (!source_quality_candidate_is_accepted_start(section, accepted_start[decode_index], candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      if (append_bitmap_memory_runtime_refs_for_instruction(section_analysis, candidate, &instruction,
          &state) != 0) {
        return -1;
      }
      source_quality_bitmap_base_state_update_after_instruction(&state, section_analysis, &instruction);
    }
  }
  return 0;
}

typedef struct SourceQualityRelocationRefIndex {
  const M68kFact **items;
  size_t count;
} SourceQualityRelocationRefIndex;

static int compare_source_quality_relocation_ref_offsets(const void *left, const void *right) {
  const M68kFact *left_fact = *(const M68kFact *const *)left;
  const M68kFact *right_fact = *(const M68kFact *const *)right;
  if (left_fact->offset < right_fact->offset) return -1;
  if (left_fact->offset > right_fact->offset) return 1;
  return 0;
}

static int source_quality_build_relocation_pointer_ref_index(const M68kFactIR *facts,
    const M68kDecodeIR *decode, uint32_t section_index, SourceQualityRelocationRefIndex *index) {
  size_t fact_index;
  size_t capacity = 0U;
  if (index == NULL) return -1;
  memset(index, 0, sizeof(*index));
  if (facts == NULL || decode == NULL) return 0;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    if (fact->kind == M68K_FACT_RELOCATION_REF && fact->section_index == section_index &&
        fact->size == 4U && fact->target_section_index < decode->section_count) {
      ++capacity;
    }
  }
  if (capacity == 0U) return 0;
  index->items = (const M68kFact **)calloc(capacity, sizeof(*index->items));
  if (index->items == NULL) return -1;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    if (fact->kind == M68K_FACT_RELOCATION_REF && fact->section_index == section_index &&
        fact->size == 4U && fact->target_section_index < decode->section_count) {
      index->items[index->count++] = fact;
    }
  }
  qsort(index->items, index->count, sizeof(*index->items), compare_source_quality_relocation_ref_offsets);
  return 0;
}

static void source_quality_relocation_ref_index_destroy(SourceQualityRelocationRefIndex *index) {
  if (index == NULL) return;
  free(index->items);
  memset(index, 0, sizeof(*index));
}

static int source_quality_relocation_ref_at_index_is_unique_offset(
    const SourceQualityRelocationRefIndex *index, size_t item_index) {
  uint32_t offset;
  if (index == NULL || item_index >= index->count) return 0;
  offset = index->items[item_index]->offset;
  if (item_index != 0U && index->items[item_index - 1U]->offset == offset) return 0;
  if (item_index + 1U < index->count && index->items[item_index + 1U]->offset == offset) return 0;
  return 1;
}

static int source_quality_relocation_ref_at_index_is_data_pointer_long(
    const SourceQualityRelocationRefIndex *index, size_t item_index, const uint8_t *accepted_bytes,
    uint32_t section_size) {
  const M68kFact *relocation;
  uint32_t cursor;
  if (index == NULL || accepted_bytes == NULL || item_index >= index->count) return 0;
  relocation = index->items[item_index];
  if (!source_quality_relocation_ref_at_index_is_unique_offset(index, item_index) ||
      relocation->offset > section_size || 4U > section_size - relocation->offset) {
    return 0;
  }
  for (cursor = 0U; cursor < 4U; ++cursor) {
    if (accepted_bytes[relocation->offset + cursor] != 0U) return 0;
  }
  return 1;
}

static int append_relocation_pointer_table_item(M68kSourceAnalysisIR *source_analysis,
    uint32_t section_index, uint32_t offset, uint32_t size) {
  M68kAnalysisStructuredDataItem item;
  if (source_analysis == NULL || size < 8U ||
      source_quality_has_structured_data_item(source_analysis, section_index, offset, size,
        M68K_ANALYSIS_STRUCTURED_DATA_LONGS,
        M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_RELOCATION_POINTER_TABLE)) {
    return 0;
  }
  memset(&item, 0, sizeof(item));
  item.has_section_index = 1U;
  item.section_index = section_index;
  item.offset = offset;
  item.size = size;
  item.kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  item.source_pattern_id = M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_RELOCATION_POINTER_TABLE;
  m68k_analysis_structured_data_item_set_semantic_role_flags(&item,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE);
  return m68k_ir_source_analysis_append_structured_data_item(source_analysis, &item);
}

static int append_relocation_pointer_table_items(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_bytes) {
  size_t decode_index;
  if (source_analysis == NULL || decode == NULL || facts == NULL || accepted_bytes == NULL) return 0;
  for (decode_index = 0U; decode_index < decode->section_count; ++decode_index) {
    const M68kDecodeSectionIR *section = &decode->sections[decode_index];
    uint32_t section_index = 0U;
    M68kSectionAnalysisIR *analysis_section;
    SourceQualityRelocationRefIndex relocation_index;
    size_t relocation_item_index = 0U;
    int result = 0;
    if (section->section_index > UINT32_MAX) continue;
    section_index = (uint32_t)section->section_index;
    analysis_section = source_analysis_section_by_index(source_analysis, section_index);
    if (analysis_section == NULL) continue;
    if (source_quality_build_relocation_pointer_ref_index(facts, decode, section_index, &relocation_index) != 0)
      return -1;
    while (relocation_item_index < relocation_index.count) {
      uint32_t start;
      uint32_t cursor;
      if (!source_quality_relocation_ref_at_index_is_data_pointer_long(&relocation_index,
          relocation_item_index, accepted_bytes[decode_index], section->size)) {
        ++relocation_item_index;
        continue;
      }
      start = relocation_index.items[relocation_item_index]->offset;
      cursor = start;
      while (relocation_item_index < relocation_index.count &&
          source_quality_relocation_ref_at_index_is_data_pointer_long(&relocation_index,
            relocation_item_index, accepted_bytes[decode_index], section->size) &&
          relocation_index.items[relocation_item_index]->offset == cursor) {
        cursor += 4U;
        ++relocation_item_index;
      }
      if (cursor - start >= 8U) {
        if (append_relocation_pointer_table_item(source_analysis, section_index, start, cursor - start) != 0) {
          result = -1;
          break;
        }
      }
    }
    source_quality_relocation_ref_index_destroy(&relocation_index);
    if (result != 0) return result;
  }
  return 0;
}

typedef struct M68kSourceQualityTableIndexDomainEvidence {
  uint8_t has_mask;
  uint32_t mask_min;
  uint32_t mask_max;
  uint8_t has_compare;
  uint32_t compare_min;
  uint32_t compare_max;
  uint8_t branch_mnemonic_id;
  uint8_t has_loop;
  uint32_t loop_min;
  uint32_t loop_max;
  uint8_t loop_mnemonic_id;
} M68kSourceQualityTableIndexDomainEvidence;

#define M68K_SOURCE_QUALITY_WORD_DISPATCH_LOCAL_LIMIT 0x2000
#define M68K_SOURCE_QUALITY_WORD_DISPATCH_FAR_BOUNDARY_MIN 0x1000

static int source_quality_structured_data_kind_for_candidate_size(const M68kDecodeCandidate *candidate,
    uint32_t *out_size, uint8_t *out_kind) {
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

static int source_quality_section_has_interior_label(const M68kSectionAnalysisIR *section,
    uint32_t offset, uint32_t size) {
  uint32_t cursor;
  if (section == NULL || size == 0U) return 0;
  for (cursor = offset + 1U; cursor < offset + size; ++cursor) {
    if (source_quality_section_has_label_at(section, cursor)) return 1;
  }
  return 0;
}

static int source_quality_existing_structured_data_overlaps(const M68kSourceAnalysisIR *source_analysis,
    uint32_t section_index, uint32_t offset, uint32_t size) {
  size_t index;
  uint32_t end;
  if (source_analysis == NULL || size == 0U || offset > UINT32_MAX - size) return 0;
  end = offset + size;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    uint32_t item_end;
    if (!item->has_section_index || item->section_index != section_index || item->size == 0U ||
        item->offset > UINT32_MAX - item->size) {
      continue;
    }
    item_end = item->offset + item->size;
    if (item->offset < end && item_end > offset) return 1;
  }
  return 0;
}

static int source_quality_range_ownership_covers_noncode_or_conflict(const M68kSectionAnalysisIR *section,
    uint32_t offset) {
  size_t index;
  if (section == NULL) return 0;
  for (index = 0U; index < section->range_ownership_count; ++index) {
    const M68kRangeOwnershipIR *range = &section->range_ownerships[index];
    if (offset < range->start_offset || offset >= range->end_offset) continue;
    if (range->kind != M68K_RANGE_OWNERSHIP_CODE) return 1;
  }
  return 0;
}

static uint32_t source_quality_pc_relative_lookup_table_span(const M68kSourceAnalysisIR *source_analysis,
    const M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_bytes, uint32_t offset, uint32_t item_size) {
  uint32_t cursor;
  if (source_analysis == NULL || section_analysis == NULL || section == NULL || accepted_bytes == NULL ||
      item_size == 0U || offset > section->size || item_size > section->size - offset) {
    return 0U;
  }
  cursor = offset + item_size;
  while (cursor + item_size <= section->size &&
      !source_quality_section_has_label_at(section_analysis, cursor) &&
      !source_quality_section_has_interior_label(section_analysis, cursor, item_size) &&
      !source_quality_accepted_range_has_code_byte(accepted_bytes, section->size, cursor, item_size) &&
      !source_quality_existing_structured_data_overlaps(source_analysis, (uint32_t)section_analysis->section_index,
        cursor, item_size) &&
      !source_quality_range_ownership_covers_noncode_or_conflict(section_analysis, cursor)) {
    cursor += item_size;
  }
  return cursor - offset;
}

static int source_quality_operand_pc_indexed_data_register(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (out_reg != NULL) *out_reg = 0U;
  if (operand == NULL ||
      (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
      operand->value.ea_mode != 7U || operand->value.ea_reg != 3U ||
      operand->value.index_is_address || operand->value.index_reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = operand->value.index_reg;
  return 1;
}

static const M68kDecodeCandidate *source_quality_next_accepted_candidate(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate) {
  uint32_t next_offset;
  if (section == NULL || accepted_start == NULL || candidate == NULL ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return NULL;
  }
  next_offset = candidate->offset + candidate->byte_count;
  if (next_offset >= section->size || !accepted_start[next_offset]) return NULL;
  return m68k_decode_ir_find_candidate_at_offset(section, next_offset);
}

static int source_quality_instruction_sets_data_register_immediate(const M68kInstructionIR *instruction,
    uint8_t reg, uint32_t *out_value) {
  size_t source_index = 0U;
  size_t dest_index = 0U;
  const M68kSimFormMetadata *metadata = NULL;
  uint8_t dest_reg = 0U;
  uint32_t value = 0U;
  if (instruction == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ && instruction->operand_count >= 2U) {
    source_index = 0U;
    dest_index = 1U;
  } else if (!source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index,
      &dest_index, &metadata)) {
    return 0;
  }
  if (!source_quality_operand_data_register_index(&instruction->operands[dest_index], &dest_reg) ||
      dest_reg != reg ||
      !m68k_ir_operand_immediate_value(&instruction->operands[source_index], &value)) {
    return 0;
  }
  if (out_value != NULL) *out_value = value;
  return 1;
}

static int source_quality_instruction_writes_data_register(const M68kInstructionIR *instruction, uint8_t reg) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t operand_reg = 0U;
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE) continue;
    if (source_quality_operand_data_register_index(&instruction->operands[operand_index], &operand_reg) &&
        operand_reg == reg) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_instruction_is_dbf_to_loop(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint8_t count_reg, uint32_t loop_offset) {
  M68kInstructionIR instruction;
  size_t target_index;
  uint8_t dbf_reg = 0U;
  if (section == NULL || candidate == NULL ||
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_DBF ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      instruction.operand_count < 2U ||
      !source_quality_operand_data_register_index(&instruction.operands[0], &dbf_reg) ||
      dbf_reg != count_reg) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section && target->section_index == section->section_index &&
        target->offset == loop_offset) {
      return 1;
    }
  }
  return 0;
}

static void source_quality_derive_loop_domain_around_table_access(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *table_candidate, uint8_t index_register,
    M68kSourceQualityTableIndexDomainEvidence *out_domain) {
  const M68kDecodeCandidate *init_candidate;
  const M68kDecodeCandidate *cursor;
  M68kInstructionIR init_instruction;
  uint32_t initial_value = 0U;
  size_t scan_count = 0U;
  if (out_domain != NULL) memset(out_domain, 0, sizeof(*out_domain));
  if (section == NULL || accepted_start == NULL || table_candidate == NULL || out_domain == NULL ||
      index_register >= 8U) {
    return;
  }
  init_candidate = source_quality_previous_accepted_candidate(section, accepted_start, table_candidate->offset);
  if (init_candidate == NULL || init_candidate->byte_count == 0U ||
      init_candidate->offset + init_candidate->byte_count != table_candidate->offset ||
      m68k_decode_candidate_to_instruction(init_candidate, &init_instruction) != 0 ||
      !source_quality_instruction_sets_data_register_immediate(&init_instruction, index_register,
        &initial_value) ||
      initial_value > 0xFFFFU) {
    return;
  }
  cursor = source_quality_next_accepted_candidate(section, accepted_start, table_candidate);
  while (cursor != NULL && scan_count < 8U) {
    M68kInstructionIR instruction;
    if (m68k_decode_candidate_to_instruction(cursor, &instruction) != 0) return;
    if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_DBF) {
      if (source_quality_instruction_is_dbf_to_loop(section, cursor, index_register, table_candidate->offset)) {
        out_domain->has_loop = 1U;
        out_domain->loop_min = 0U;
        out_domain->loop_max = initial_value;
        out_domain->loop_mnemonic_id = M68K_ASM_MNEMONIC_DBF;
      }
      return;
    }
    if (source_quality_instruction_writes_data_register(&instruction, index_register)) return;
    cursor = source_quality_next_accepted_candidate(section, accepted_start, cursor);
    ++scan_count;
  }
}

static uint32_t source_quality_structured_item_entry_count(const M68kAnalysisStructuredDataItem *item) {
  uint32_t entry_size = 0U;
  if (item == NULL || item->size == 0U) return 0U;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES) entry_size = 1U;
  else if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS) entry_size = 2U;
  else if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS) entry_size = 4U;
  if (entry_size == 0U || item->size % entry_size != 0U) return 0U;
  return item->size / entry_size;
}

static uint8_t source_quality_table_entry_count_proof_rank(uint8_t proof_id) {
  switch (proof_id) {
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_UNKNOWN:
      return 0U;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_STRUCTURED_RANGE:
      return 1U;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_CONSUMER_STRUCTURAL_SCAN:
      return 2U;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_MASK_DOMAIN:
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_COMPARE_DOMAIN:
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_LOOP_LIMIT:
      return 3U;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_RELOCATION_RECORD:
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_PLATFORM_RECORD:
      return 4U;
    default:
      return 0U;
  }
}

static void source_quality_set_entry_count_proof_if_stronger(M68kAnalysisStructuredDataItem *item, uint8_t proof_id) {
  if (item == NULL) return;
  if (source_quality_table_entry_count_proof_rank(proof_id) >
      source_quality_table_entry_count_proof_rank(item->entry_count_proof_id)) {
    item->entry_count_proof_id = proof_id;
    item->table_stop_reason_id = m68k_analysis_table_stop_reason_for_entry_count_proof(item->entry_count_proof_id);
  }
}

static void source_quality_promote_entry_count_proof_from_index_domain(M68kAnalysisStructuredDataItem *item) {
  uint32_t entry_count = source_quality_structured_item_entry_count(item);
  if (item == NULL || entry_count == 0U) return;
  if (item->has_index_compare_domain && item->index_compare_min == 0U &&
      item->index_compare_max < UINT32_MAX && entry_count == item->index_compare_max + 1U) {
    source_quality_set_entry_count_proof_if_stronger(item,
      M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_COMPARE_DOMAIN);
  } else if (item->has_index_loop_domain && item->index_loop_min == 0U &&
      item->index_loop_max < UINT32_MAX && entry_count == item->index_loop_max + 1U) {
    source_quality_set_entry_count_proof_if_stronger(item, M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_LOOP_LIMIT);
  } else if (item->has_index_mask_domain && item->index_mask_min == 0U &&
      item->index_mask_max < UINT32_MAX && entry_count == item->index_mask_max + 1U) {
    source_quality_set_entry_count_proof_if_stronger(item,
      M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_MASK_DOMAIN);
  }
}

static int source_quality_candidate_next_is_indirect_control_through_addr_reg(
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
    uint8_t reg) {
  const M68kDecodeCandidate *next_candidate;
  M68kInstructionIR next_instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index = 0U;
  uint32_t next_offset;
  const M68kOperandIR *operand;
  if (section == NULL || accepted_start == NULL || candidate == NULL || reg >= 8U ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  next_offset = candidate->offset + candidate->byte_count;
  if (next_offset >= section->size || !accepted_start[next_offset]) return 0;
  next_candidate = m68k_decode_ir_find_candidate_at_offset(section, next_offset);
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
  operand = &next_instruction.operands[operand_index];
  return operand->kind == M68K_ASM_OPERAND_EA &&
    operand->value.ea_mode == 2U &&
    operand->value.ea_reg == reg;
}

static int source_quality_candidate_later_is_indirect_control_through_addr_reg(
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
    uint8_t reg) {
  const uint32_t max_gap_instructions = 4U;
  uint32_t cursor;
  uint32_t gap_count;
  if (section == NULL || accepted_start == NULL || candidate == NULL || reg >= 8U ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  if (source_quality_candidate_next_is_indirect_control_through_addr_reg(section, accepted_start, candidate, reg))
    return 1;
  cursor = candidate->offset + candidate->byte_count;
  for (gap_count = 0U; gap_count < max_gap_instructions && cursor < section->size; ++gap_count) {
    const M68kDecodeCandidate *gap_candidate;
    M68kInstructionIR instruction;
    if (!accepted_start[cursor]) return 0;
    gap_candidate = m68k_decode_ir_find_candidate_at_offset(section, cursor);
    if (gap_candidate == NULL || m68k_decode_candidate_to_instruction(gap_candidate, &instruction) != 0)
      return 0;
    if (source_quality_candidate_next_is_indirect_control_through_addr_reg(section, accepted_start, gap_candidate,
        reg)) {
      return !source_quality_instruction_writes_data_register(&instruction, reg);
    }
    if (source_quality_instruction_writes_data_register(&instruction, reg)) return 0;
    if (gap_candidate->offset > UINT32_MAX - gap_candidate->byte_count) return 0;
    cursor = gap_candidate->offset + gap_candidate->byte_count;
  }
  return 0;
}

static int source_quality_candidate_next_is_indexed_control_through_data_reg(
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
    uint8_t reg, uint32_t table_section_index, uint32_t table_offset) {
  const M68kDecodeCandidate *next_candidate;
  M68kInstructionIR next_instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index = 0U;
  uint32_t next_offset;
  uint8_t index_reg = 0U;
  uint32_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (section == NULL || accepted_start == NULL || candidate == NULL || reg >= 8U ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  next_offset = candidate->offset + candidate->byte_count;
  if (next_offset >= section->size || !accepted_start[next_offset]) return 0;
  next_candidate = m68k_decode_ir_find_candidate_at_offset(section, next_offset);
  if (next_candidate == NULL || m68k_decode_candidate_to_instruction(next_candidate, &next_instruction) != 0)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(&next_instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_JUMP && metadata->flow_kind != M68K_SIM_FLOW_CALL)) {
    return 0;
  }
  if (metadata->target_operand_index < next_instruction.operand_count)
    operand_index = metadata->target_operand_index;
  return operand_index < next_instruction.operand_count &&
    source_quality_operand_pc_indexed_data_register(&next_instruction.operands[operand_index], &index_reg) &&
    index_reg == reg &&
    source_quality_candidate_data_target_for_operand(next_candidate, (uint32_t)operand_index,
      &target_section_index, &target_offset) &&
    target_section_index == table_section_index &&
    target_offset == table_offset;
}

static int source_quality_candidate_dest_data_register(const M68kInstructionIR *instruction, uint8_t *out_reg) {
  const M68kSimFormMetadata *metadata = NULL;
  size_t source_index = 0U;
  size_t dest_index = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (instruction == NULL || out_reg == NULL ||
      !source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
        &metadata) ||
      dest_index >= instruction->operand_count) {
    return 0;
  }
  (void)source_index;
  return source_quality_operand_data_register_index(&instruction->operands[dest_index], out_reg);
}

static void source_quality_structured_item_apply_index_domain(M68kAnalysisStructuredDataItem *item,
    const M68kSourceQualityTableIndexDomainEvidence *index_domain) {
  if (item == NULL || index_domain == NULL) return;
  if (index_domain->has_mask) {
    item->has_index_mask_domain = 1U;
    item->index_mask_min = index_domain->mask_min;
    item->index_mask_max = index_domain->mask_max;
  }
  if (index_domain->has_compare) {
    item->has_index_compare_domain = 1U;
    item->index_compare_min = index_domain->compare_min;
    item->index_compare_max = index_domain->compare_max;
    item->index_domain_branch_mnemonic_id = index_domain->branch_mnemonic_id;
  }
  if (index_domain->has_loop) {
    item->has_index_loop_domain = 1U;
    item->index_loop_min = index_domain->loop_min;
    item->index_loop_max = index_domain->loop_max;
    item->index_loop_mnemonic_id = index_domain->loop_mnemonic_id;
  }
}

static int source_quality_structured_data_item_same_range_role(const M68kAnalysisStructuredDataItem *left,
    const M68kAnalysisStructuredDataItem *right) {
  if (left == NULL || right == NULL) return 0;
  return left->has_section_index == right->has_section_index &&
    left->section_index == right->section_index &&
    left->offset == right->offset &&
    left->kind == right->kind &&
    left->semantic_role_flags == right->semantic_role_flags &&
    (left->size == right->size ||
     (left->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) != 0U);
}

static uint8_t source_quality_structured_data_source_pattern_rank(uint8_t source_pattern_id) {
  switch (source_pattern_id) {
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_UNKNOWN:
      return 0U;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_READ:
      return 1U;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_POINTER_READ:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_SCALAR_READ:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POSTINCREMENT_READ_SEQUENCE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_STRING_TABLE_SEQUENCE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POINTER_STRING_TABLE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_WORD_OFFSET_STRING_TABLE:
      return 3U;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_WORD_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_INDIRECT_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_RELOCATION_POINTER_TABLE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MACOS_SYMBOL_RECORD:
      return 4U;
    default:
      return 2U;
  }
}

static void source_quality_update_structured_data_item_if_not_downgrade(M68kAnalysisStructuredDataItem *existing,
    const M68kAnalysisStructuredDataItem *item, int *updated) {
  uint8_t existing_rank;
  uint8_t item_rank;
  if (existing == NULL || item == NULL) return;
  existing_rank = source_quality_structured_data_source_pattern_rank(existing->source_pattern_id);
  item_rank = source_quality_structured_data_source_pattern_rank(item->source_pattern_id);
  if (existing_rank > item_rank || (existing_rank == item_rank && existing->size > item->size)) {
    if (updated != NULL) *updated = 1;
    return;
  }
  *existing = *item;
  if (updated != NULL) *updated = 1;
}

static int source_quality_update_matching_structured_data_item(M68kSourceAnalysisIR *source_analysis,
    const M68kAnalysisStructuredDataItem *item) {
  size_t index;
  uint16_t policy_index;
  int updated = 0;
  if (source_analysis == NULL || item == NULL) return 0;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    if (source_quality_structured_data_item_same_range_role(&source_analysis->structured_data_items[index], item)) {
      source_quality_update_structured_data_item_if_not_downgrade(
        &source_analysis->structured_data_items[index], item, &updated);
      break;
    }
  }
  for (policy_index = 0U; policy_index < source_analysis->policy.structured_data_item_count; ++policy_index) {
    if (source_quality_structured_data_item_same_range_role(
        &source_analysis->policy.structured_data_items[policy_index], item)) {
      source_quality_update_structured_data_item_if_not_downgrade(
        &source_analysis->policy.structured_data_items[policy_index], item, &updated);
      break;
    }
  }
  return updated;
}

static int append_pc_relative_lookup_table_item(M68kSourceAnalysisIR *source_analysis,
    uint32_t table_section_index, uint32_t table_offset, uint32_t size, uint8_t kind,
    uint8_t source_pattern_id, uint32_t consumer_section, uint32_t consumer_offset,
    uint8_t has_index_register, uint8_t index_register_kind, uint8_t index_register,
    uint8_t has_target_register, uint8_t target_register_kind, uint8_t target_register,
    const M68kSourceQualityTableIndexDomainEvidence *index_domain, uint8_t has_target,
    uint32_t target_section, uint32_t target_offset) {
  M68kAnalysisStructuredDataItem item;
  const char *source_pattern;
  if (source_analysis == NULL || size == 0U ||
      source_quality_has_structured_data_item(source_analysis, table_section_index, table_offset, size, kind,
        source_pattern_id)) {
    return 0;
  }
  memset(&item, 0, sizeof(item));
  item.has_section_index = 1U;
  item.section_index = table_section_index;
  item.offset = table_offset;
  item.size = size;
  item.kind = kind;
  item.has_consumer = 1U;
  item.consumer_section = consumer_section;
  item.consumer_offset = consumer_offset;
  item.source_pattern_id = source_pattern_id;
  item.entry_count_proof_id = m68k_analysis_table_entry_count_proof_for_source_pattern(source_pattern_id);
  item.table_stop_reason_id = m68k_analysis_table_stop_reason_for_entry_count_proof(item.entry_count_proof_id);
  if (has_index_register) {
    item.has_index_register = 1U;
    item.index_register_kind = index_register_kind;
    item.index_register = index_register;
  }
  if (has_target_register) {
    item.has_target_register = 1U;
    item.target_register_kind = target_register_kind;
    item.target_register = target_register;
  }
  source_quality_structured_item_apply_index_domain(&item, index_domain);
  if (has_target) {
    item.has_target = 1U;
    item.target_section = target_section;
    item.target_offset = target_offset;
  }
  source_pattern = m68k_analysis_structured_data_source_pattern_name(source_pattern_id);
  if (source_pattern != NULL) {
    (void)m68k_analysis_structured_data_item_set_text(&item,
      M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SOURCE_PATTERN, source_pattern, strlen(source_pattern));
  }
  m68k_analysis_structured_data_item_set_semantic_role_flags(&item,
    M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE);
  source_quality_promote_entry_count_proof_from_index_domain(&item);
  m68k_analysis_structured_data_item_refresh_table_metadata(&item);
  if (source_quality_update_matching_structured_data_item(source_analysis, &item)) return 0;
  return m68k_ir_source_analysis_append_structured_data_item(source_analysis, &item);
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

static int append_expected_storage_label_statement_symbol_accesses_for_section(
    M68kSectionAnalysisIR *section_analysis) {
  size_t view_index;
  if (section_analysis == NULL) return -1;
  for (view_index = 0U; view_index < section_analysis->runtime_view_count; ++view_index) {
    const M68kRuntimeViewIR *view = &section_analysis->runtime_views[view_index];
    const M68kSymbolOriginIR *origin;
    M68kExpectedSymbolAccessIR access;
    if (view->materialized == 0U || view->runtime_address == view->storage_offset ||
        view->storage_offset >= section_analysis->section_size) {
      continue;
    }
    origin = source_quality_symbol_origin_at(section_analysis, view->storage_offset);
    if (origin == NULL) continue;
    memset(&access, 0, sizeof(access));
    access.symbol_name = origin->symbol_name;
    access.producer = "storage_label_statement";
    access.offset = view->storage_offset;
    access.target_section_index = (uint32_t)section_analysis->section_index;
    access.target_offset = view->storage_offset;
    access.operand_index = UINT32_MAX;
    access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_STORAGE_LABEL;
    access.confidence = origin->confidence;
    access.has_target = 1U;
    if (m68k_ir_section_analysis_append_expected_symbol_access(section_analysis, &access) != 0) return -1;
  }
  return 0;
}

static int append_expected_storage_label_statement_symbol_accesses(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    if (append_expected_storage_label_statement_symbol_accesses_for_section(
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

static int source_quality_operand_address_displacement(const M68kOperandIR *operand, uint8_t *out_reg,
    int16_t *out_displacement) {
  if (out_reg != NULL) *out_reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (operand == NULL ||
      (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
      operand->value.ea_mode != 5U ||
      operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = operand->value.ea_reg;
  if (out_displacement != NULL) *out_displacement = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

static int source_quality_operand_data_register_index(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (out_reg != NULL) *out_reg = 0U;
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

typedef struct M68kSourceQualityAudioLengthSource {
  uint8_t known;
  uint8_t base_reg;
  int16_t displacement;
  uint8_t transformed;
} M68kSourceQualityAudioLengthSource;

typedef struct M68kSourceQualityAudioPeriodSource {
  uint8_t known;
  uint8_t transformed;
  uint32_t target_section_index;
  uint32_t target_offset;
} M68kSourceQualityAudioPeriodSource;

typedef struct M68kSourceQualityAudioPointerSource {
  uint8_t known;
  uint8_t exact;
  uint8_t dynamic_offset_known;
  uint32_t target_section_index;
  uint32_t target_offset;
  uint32_t dynamic_offset_section_index;
  uint32_t dynamic_offset_offset;
} M68kSourceQualityAudioPointerSource;

typedef struct M68kSourceQualityAudioPointerState {
  M68kSourceQualityAudioPointerSource data_regs[8];
  M68kSourceQualityAudioPointerSource addr_regs[8];
} M68kSourceQualityAudioPointerState;

typedef struct M68kSourceQualityPaletteHardwareRangePointer {
  uint8_t known;
  const AmigaOsHardwareRegisterRangeInfo *range;
  uint32_t offset;
} M68kSourceQualityPaletteHardwareRangePointer;

typedef struct M68kSourceQualityPaletteHardwareRangeState {
  M68kSourceQualityPaletteHardwareRangePointer addr_regs[8];
} M68kSourceQualityPaletteHardwareRangeState;

typedef struct M68kSourceQualityPalettePointerSave {
  uint8_t valid;
  uint32_t mask;
  M68kSourceQualityAudioPointerSource data_regs[8];
  M68kSourceQualityAudioPointerSource addr_regs[8];
  M68kSourceQualityPaletteHardwareRangePointer hardware_addr_regs[8];
} M68kSourceQualityPalettePointerSave;

#define M68K_SOURCE_QUALITY_AMIGA_COLOR_REGISTER_BYTES 64U

static void source_quality_audio_length_sources_clear(M68kSourceQualityAudioLengthSource sources[8]) {
  memset(sources, 0, 8U * sizeof(sources[0]));
}

static void source_quality_audio_period_sources_clear(M68kSourceQualityAudioPeriodSource sources[8]) {
  memset(sources, 0, 8U * sizeof(sources[0]));
}

static void source_quality_audio_pointer_state_clear_all(M68kSourceQualityAudioPointerState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void source_quality_audio_pointer_state_clear_reg(M68kSourceQualityAudioPointerState *state,
    uint8_t reg_kind, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) state->data_regs[reg_index].known = 0U;
  else if (reg_kind == 2U) state->addr_regs[reg_index].known = 0U;
}

static void source_quality_audio_pointer_state_set_reg(M68kSourceQualityAudioPointerState *state,
    uint8_t reg_kind, uint8_t reg_index, uint32_t section_index, uint32_t offset) {
  M68kSourceQualityAudioPointerSource *value;
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) value = &state->data_regs[reg_index];
  else if (reg_kind == 2U) value = &state->addr_regs[reg_index];
  else return;
  memset(value, 0, sizeof(*value));
  value->known = 1U;
  value->exact = 1U;
  value->target_section_index = section_index;
  value->target_offset = offset;
}

static void source_quality_audio_pointer_state_copy_reg(M68kSourceQualityAudioPointerState *state,
    uint8_t reg_kind, uint8_t reg_index, const M68kSourceQualityAudioPointerSource *source) {
  if (state == NULL || source == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) state->data_regs[reg_index] = *source;
  else if (reg_kind == 2U) state->addr_regs[reg_index] = *source;
}

static int source_quality_candidate_data_target_for_operand(const M68kDecodeCandidate *candidate,
    uint32_t operand_index, uint32_t *out_section_index, uint32_t *out_offset) {
  size_t target_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (candidate == NULL || out_section_index == NULL || out_offset == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_DATA || target->has_section == 0U ||
        target->has_operand == 0U || target->operand_index != operand_index ||
        target->section_index > UINT32_MAX) {
      continue;
    }
    *out_section_index = (uint32_t)target->section_index;
    *out_offset = target->offset;
    return 1;
  }
  return 0;
}

static int source_quality_candidate_data_target_for_operand_with_analysis(
    const M68kSectionAnalysisIR *section_analysis, const M68kDecodeCandidate *candidate,
    uint32_t operand_index, uint32_t *out_section_index, uint32_t *out_offset) {
  size_t observation_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (section_analysis != NULL && candidate != NULL) {
    for (observation_index = 0U; observation_index < section_analysis->address_observation_count;
         ++observation_index) {
      const M68kAddressObservationIR *observation =
        &section_analysis->address_observations[observation_index];
      if (observation->offset == candidate->offset && observation->operand_index == operand_index &&
          observation->has_target != 0U && observation->conflicted == 0U &&
          observation->target_section_index <= UINT32_MAX) {
        if (out_section_index != NULL) *out_section_index = observation->target_section_index;
        if (out_offset != NULL) *out_offset = observation->target_offset;
        return 1;
      }
    }
  }
  return source_quality_candidate_data_target_for_operand(candidate, operand_index, out_section_index, out_offset);
}

static int source_quality_accepted_range_has_code_byte(const uint8_t *accepted_bytes, uint32_t section_size,
    uint32_t offset, uint32_t size) {
  uint32_t cursor;
  if (accepted_bytes == NULL || size == 0U || offset >= section_size || size > section_size - offset) return 0;
  for (cursor = 0U; cursor < size; ++cursor) {
    if (accepted_bytes[offset + cursor] != 0U) return 1;
  }
  return 0;
}

static const M68kSourceQualityAudioPointerSource *source_quality_audio_pointer_state_value_for_operand(
    const M68kSourceQualityAudioPointerState *state, const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (source_quality_operand_data_register_index(operand, &reg))
    return state->data_regs[reg].known ? &state->data_regs[reg] : NULL;
  if (source_quality_operand_address_register_index(operand, &reg))
    return state->addr_regs[reg].known ? &state->addr_regs[reg] : NULL;
  return NULL;
}

static int source_quality_audio_length_write_source_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint8_t *out_reg) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  size_t source_index = 0U, dest_index = 0U;
  uint32_t dest_address = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_reg == NULL ||
      instruction->size_suffix != 'w' ||
      !source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
        &metadata) ||
      metadata == NULL || metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
      !source_quality_operand_data_register_index(&instruction->operands[source_index], out_reg) ||
      !source_quality_candidate_operand_absolute_value(candidate, dest_index, &dest_address)) {
    return 0;
  }
  hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(dest_address);
  return hardware_field != NULL && hardware_field->field_symbol_id == AMIGA_OS_SYMBOL_ID_AC_LEN;
}

static int source_quality_audio_period_write_source_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint8_t *out_reg) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  size_t source_index = 0U, dest_index = 0U;
  uint32_t dest_address = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_reg == NULL ||
      instruction->size_suffix != 'w' ||
      !source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
        &metadata) ||
      metadata == NULL || metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
      !source_quality_operand_data_register_index(&instruction->operands[source_index], out_reg) ||
      !source_quality_candidate_operand_absolute_value(candidate, dest_index, &dest_address)) {
    return 0;
  }
  hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(dest_address);
  return hardware_field != NULL && hardware_field->field_symbol_id == AMIGA_OS_SYMBOL_ID_AC_PER;
}

static int source_quality_audio_pointer_write_source_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint8_t *out_reg) {
  const M68kSimFormMetadata *metadata;
  size_t source_index = 0U, dest_index = 0U;
  uint32_t dest_address = 0U;
  uint16_t sink_kind;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_reg == NULL ||
      instruction->size_suffix != 'l' ||
      !source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
        &metadata) ||
      metadata == NULL || metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
      !source_quality_operand_address_register_index(&instruction->operands[source_index], out_reg) ||
      !source_quality_candidate_operand_absolute_value(candidate, dest_index, &dest_address)) {
    return 0;
  }
  sink_kind = platform_facts_v2_runtime_address_sink_kind(M68K_PLATFORM_BACKEND_AMIGA_HUNK, dest_address);
  return sink_kind == AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_SOUND_SAMPLE;
}

static int format_source_quality_audio_length_source_note(const M68kSourceQualityAudioLengthSource *source,
    char *buf, size_t buf_size) {
  char disp[32];
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (source == NULL || !source->known) return 0;
  if (source->displacement < 0) snprintf(disp, sizeof(disp), "-$%04X",
    (unsigned)(uint16_t)(-source->displacement));
  else if (source->displacement > 0) snprintf(disp, sizeof(disp), "$%04X",
    (unsigned)(uint16_t)source->displacement);
  else disp[0] = '\0';
  snprintf(buf, buf_size, "audio sample length %s%s(a%u) header word",
    source->transformed ? "derived from " : "from ", disp, (unsigned)source->base_reg);
  return strlen(buf) + 1U < buf_size;
}

static void source_quality_audio_length_sources_update_after_instruction(
    M68kSourceQualityAudioLengthSource sources[8], const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  size_t source_index = 0U, dest_index = 0U, operand_index;
  uint8_t dest_reg = 0U;
  uint8_t source_base_reg = 0U;
  int16_t source_displacement = 0;
  if (sources == NULL || instruction == NULL) return;
  if (source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
        &metadata) &&
      metadata != NULL && metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
      instruction->size_suffix == 'w' &&
      source_quality_operand_data_register_index(&instruction->operands[dest_index], &dest_reg) &&
      source_quality_operand_address_displacement(&instruction->operands[source_index], &source_base_reg,
        &source_displacement)) {
    sources[dest_reg].known = 1U;
    sources[dest_reg].base_reg = source_base_reg;
    sources[dest_reg].displacement = source_displacement;
    sources[dest_reg].transformed = 0U;
    return;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) {
    source_quality_audio_length_sources_clear(sources);
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE ||
        !source_quality_operand_data_register_index(&instruction->operands[operand_index], &reg)) {
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

static void source_quality_audio_period_sources_update_after_instruction(
    M68kSourceQualityAudioPeriodSource sources[8], const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  size_t source_index = 0U, dest_index = 0U, operand_index;
  uint32_t table_section_index = 0U;
  uint32_t table_offset = 0U;
  uint8_t dest_reg = 0U;
  if (sources == NULL || instruction == NULL) return;
  if (source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
        &metadata) &&
      metadata != NULL && metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
      instruction->size_suffix == 'w' &&
      source_quality_operand_data_register_index(&instruction->operands[dest_index], &dest_reg) &&
      source_quality_candidate_data_target_for_operand(candidate, (uint32_t)source_index,
        &table_section_index, &table_offset)) {
    sources[dest_reg].known = 1U;
    sources[dest_reg].transformed = 0U;
    sources[dest_reg].target_section_index = table_section_index;
    sources[dest_reg].target_offset = table_offset;
    return;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) {
    source_quality_audio_period_sources_clear(sources);
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE ||
        !source_quality_operand_data_register_index(&instruction->operands[operand_index], &reg)) {
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

static void source_quality_audio_pointer_state_mark_dynamic(M68kSourceQualityAudioPointerState *state,
    uint8_t reg_index, const M68kDecodeCandidate *candidate) {
  uint32_t table_section_index = 0U;
  uint32_t table_offset = 0U;
  if (state == NULL || reg_index >= 8U || !state->addr_regs[reg_index].known) return;
  state->addr_regs[reg_index].exact = 0U;
  if (source_quality_candidate_data_target_for_operand(candidate, 0U, &table_section_index, &table_offset)) {
    state->addr_regs[reg_index].dynamic_offset_known = 1U;
    state->addr_regs[reg_index].dynamic_offset_section_index = table_section_index;
    state->addr_regs[reg_index].dynamic_offset_offset = table_offset;
  }
}

static void source_quality_audio_pointer_state_update_after_instruction(
    M68kSourceQualityAudioPointerState *state, const M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  const M68kSourceQualityAudioPointerSource *source_value = NULL;
  uint32_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  uint32_t absolute_offset = 0U;
  uint8_t dest_reg = 0U;
  uint8_t source_reg = 0U;
  int16_t displacement = 0;
  size_t operand_index;
  if (state == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_CALL) {
    source_quality_audio_pointer_state_clear_all(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      source_quality_operand_address_register_index(&instruction->operands[1], &dest_reg)) {
    if (source_quality_candidate_data_target_for_operand_with_analysis(section_analysis, candidate, 0U,
        &target_section_index, &target_offset)) {
      source_quality_audio_pointer_state_set_reg(state, 2U, dest_reg, target_section_index, target_offset);
      return;
    }
    if (section != NULL && source_quality_operand_absolute_offset(&instruction->operands[0], &absolute_offset) &&
        absolute_offset < section->size && section->section_index <= UINT32_MAX) {
      source_quality_audio_pointer_state_set_reg(state, 2U, dest_reg, (uint32_t)section->section_index,
        absolute_offset);
      return;
    }
    if (section != NULL &&
        source_quality_operand_address_displacement(&instruction->operands[0], &source_reg, &displacement) &&
        source_reg < 8U && state->addr_regs[source_reg].known &&
        state->addr_regs[source_reg].target_section_index == section->section_index) {
      int64_t adjusted_offset = (int64_t)(uint64_t)state->addr_regs[source_reg].target_offset +
        (int64_t)displacement;
      if (adjusted_offset >= 0 && (uint64_t)adjusted_offset < (uint64_t)section->size) {
        M68kSourceQualityAudioPointerSource adjusted = state->addr_regs[source_reg];
        adjusted.target_offset = (uint32_t)adjusted_offset;
        source_quality_audio_pointer_state_copy_reg(state, 2U, dest_reg, &adjusted);
        return;
      }
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U &&
      source_quality_operand_data_register_index(&instruction->operands[1], &dest_reg) &&
      source_quality_candidate_data_target_for_operand_with_analysis(section_analysis, candidate, 0U,
        &target_section_index, &target_offset)) {
    source_quality_audio_pointer_state_set_reg(state, 1U, dest_reg, target_section_index, target_offset);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDA && instruction->operand_count == 2U &&
      source_quality_operand_address_register_index(&instruction->operands[1], &dest_reg)) {
    source_quality_audio_pointer_state_mark_dynamic(state, dest_reg, candidate);
    return;
  }
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->operand_count == 2U) {
    source_value = source_quality_audio_pointer_state_value_for_operand(state, &instruction->operands[0]);
    if (source_quality_operand_data_register_index(&instruction->operands[1], &dest_reg)) {
      source_quality_audio_pointer_state_clear_reg(state, 1U, dest_reg);
      if (source_value != NULL) source_quality_audio_pointer_state_copy_reg(state, 1U, dest_reg, source_value);
      return;
    }
    if (source_quality_operand_address_register_index(&instruction->operands[1], &dest_reg)) {
      source_quality_audio_pointer_state_clear_reg(state, 2U, dest_reg);
      if (source_value != NULL) source_quality_audio_pointer_state_copy_reg(state, 2U, dest_reg, source_value);
      return;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
      if (source_quality_reglist_contains_register(&instruction->operands[1], 1U, dest_reg))
        source_quality_audio_pointer_state_clear_reg(state, 1U, dest_reg);
      if (source_quality_reglist_contains_register(&instruction->operands[1], 2U, dest_reg))
        source_quality_audio_pointer_state_clear_reg(state, 2U, dest_reg);
    }
    return;
  }
  if (metadata == NULL) return;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE) continue;
    if (source_quality_operand_data_register_index(operand, &dest_reg))
      source_quality_audio_pointer_state_clear_reg(state, 1U, dest_reg);
    else if (source_quality_operand_address_register_index(operand, &dest_reg))
      source_quality_audio_pointer_state_clear_reg(state, 2U, dest_reg);
  }
}

static int append_pc_relative_lookup_table_items(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, uint8_t *const *accepted_bytes) {
  size_t decode_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL) return 0;
  for (decode_index = 0U; decode_index < decode->section_count; ++decode_index) {
    const M68kDecodeSectionIR *section = &decode->sections[decode_index];
    M68kSectionAnalysisIR *consumer_analysis;
    M68kSourceQualityAudioPointerState state;
    size_t candidate_index;
    if (section->section_index > UINT32_MAX || accepted_start[decode_index] == NULL ||
        accepted_bytes[decode_index] == NULL) {
      return -1;
    }
    consumer_analysis = source_analysis_section_by_index(source_analysis, (uint32_t)section->section_index);
    if (consumer_analysis == NULL) continue;
    source_quality_audio_pointer_state_clear_all(&state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const M68kSimFormMetadata *metadata;
      uint32_t item_size = 0U;
      uint8_t item_kind = 0U;
      size_t target_index;
      if (!source_quality_candidate_is_accepted_start(section, accepted_start[decode_index], candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      metadata = m68k_sim_metadata_for_instruction(&instruction);
      if (metadata != NULL &&
          source_quality_structured_data_kind_for_candidate_size(candidate, &item_size, &item_kind)) {
        for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
          const M68kDecodeTarget *target = &candidate->targets[target_index];
          const M68kOperandIR *operand;
          uint8_t shape;
          uint8_t dest_reg = 0U;
          uint8_t dest_data_reg = 0U;
          uint8_t table_index_reg = 0U;
          uint32_t span;
          uint8_t source_pattern_id = M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_READ;
          M68kSourceQualityTableIndexDomainEvidence index_domain;
          M68kSectionAnalysisIR *table_analysis;
          uint8_t has_target = 0U;
          uint32_t table_target_section = 0U;
          uint32_t table_target_offset = 0U;
          if (target->kind != M68K_DECODE_TARGET_DATA || !target->has_section || !target->has_operand ||
              target->section_index >= decode->section_count || target->section_index > UINT32_MAX ||
              target->operand_index >= instruction.operand_count || target->operand_index >= 4U) {
            continue;
          }
          operand = &instruction.operands[target->operand_index];
          shape = m68k_instruction_operand_decoded_ea_shape(operand);
          if (m68k_instruction_decoded_ea_target_kind(operand, shape, 1) != 2U) continue;
          if (metadata->operand_access_kinds[target->operand_index] != M68K_SIM_ACCESS_MEMORY_READ) continue;
          if (item_kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
              source_quality_candidate_dest_data_register(&instruction, &dest_data_reg) &&
              source_quality_candidate_next_is_indexed_control_through_data_reg(section,
                accepted_start[decode_index], candidate, dest_data_reg, (uint32_t)target->section_index,
                target->offset)) {
            continue;
          }
          if (source_quality_accepted_range_has_code_byte(accepted_bytes[target->section_index],
              decode->sections[target->section_index].size, target->offset, item_size)) {
            continue;
          }
          table_analysis = source_analysis_section_by_index(source_analysis, (uint32_t)target->section_index);
          if (table_analysis == NULL) continue;
          span = source_quality_pc_relative_lookup_table_span(source_analysis, table_analysis,
            &decode->sections[target->section_index], accepted_bytes[target->section_index], target->offset,
            item_size);
          if (span == 0U) continue;
          memset(&index_domain, 0, sizeof(index_domain));
          if (item_kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
              instruction.operand_count >= 2U &&
              source_quality_operand_address_register_index(&instruction.operands[instruction.operand_count - 1U],
                &dest_reg) &&
              dest_reg < 8U &&
              source_quality_candidate_later_is_indirect_control_through_addr_reg(section,
                accepted_start[decode_index], candidate, dest_reg)) {
            source_pattern_id = M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_INDIRECT_DISPATCH;
          }
          if (source_quality_operand_pc_indexed_data_register(operand, &table_index_reg)) {
            source_quality_derive_loop_domain_around_table_access(section, accepted_start[decode_index],
              candidate, table_index_reg, &index_domain);
          }
          if (item_kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
              instruction.operand_count >= 2U &&
              source_quality_operand_address_register_index(&instruction.operands[instruction.operand_count - 1U],
                &dest_reg) &&
              dest_reg < 8U && state.addr_regs[dest_reg].known &&
              source_quality_candidate_later_is_indirect_control_through_addr_reg(section,
                accepted_start[decode_index], candidate, dest_reg)) {
            has_target = 1U;
            table_target_section = state.addr_regs[dest_reg].target_section_index;
            table_target_offset = state.addr_regs[dest_reg].target_offset;
          }
          if (append_pc_relative_lookup_table_item(source_analysis, (uint32_t)target->section_index,
              target->offset, span, item_kind, source_pattern_id, (uint32_t)section->section_index,
              candidate->offset, index_domain.has_loop, M68K_ANALYSIS_REGISTER_DATA, table_index_reg, 0U,
              M68K_ANALYSIS_REGISTER_NONE, 0U, &index_domain, has_target, table_target_section,
              table_target_offset) != 0) {
            return -1;
          }
        }
      }
      source_quality_audio_pointer_state_update_after_instruction(&state, consumer_analysis, section, candidate,
        &instruction);
    }
  }
  return 0;
}

static int source_quality_operand_is_address_postincrement(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (out_reg != NULL) *out_reg = 0U;
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_POSTINC && operand->value.reg < 8U) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 3U && operand->value.ea_reg < 8U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static int source_quality_candidate_local_call_target(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t *out_target_offset);
static int source_quality_instruction_writes_address_register_mask(const M68kInstructionIR *instruction,
    uint8_t mask);
static int source_quality_local_callee_preserves_address_register_mask_with_depth(
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t target_offset,
    uint8_t mask, uint8_t depth);

static void source_quality_dispatch_pointer_state_update_after_instruction(M68kSourceQualityAudioPointerState *state,
    const M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  if (state == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata != NULL &&
      (metadata->flow_kind == M68K_SIM_FLOW_CALL || metadata->flow_kind == M68K_SIM_FLOW_JUMP)) {
    source_quality_audio_pointer_state_clear_all(state);
    return;
  }
  source_quality_audio_pointer_state_update_after_instruction(state, section_analysis, section, candidate,
    instruction);
}

static int source_quality_data_pointer_value_with_signed_displacement(
    const M68kSourceQualityAudioPointerSource *value, int32_t displacement,
    uint32_t *out_section_index, uint32_t *out_offset) {
  int64_t adjusted;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (value == NULL || !value->known || out_section_index == NULL || out_offset == NULL) return 0;
  adjusted = (int64_t)(uint64_t)value->target_offset + (int64_t)displacement;
  if (adjusted < 0 || adjusted > UINT32_MAX) return 0;
  *out_section_index = value->target_section_index;
  *out_offset = (uint32_t)adjusted;
  return 1;
}

static int source_quality_ea_shape_is_indexed_or_pc_indexed(uint8_t shape) {
  return shape == M68K_SIM_EA_SHAPE_INDEX || shape == M68K_SIM_EA_SHAPE_PC_INDEX;
}

static int source_quality_indexed_control_operand_target(const M68kDecodeCandidate *candidate,
    uint32_t operand_index, const M68kOperandIR *operand, const M68kSourceQualityAudioPointerState *state,
    uint32_t *out_section_index, uint32_t *out_offset) {
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (candidate == NULL || operand == NULL || out_section_index == NULL || out_offset == NULL) return 0;
  if (source_quality_candidate_data_target_for_operand(candidate, operand_index, out_section_index, out_offset))
    return 1;
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_reg >= 8U || state == NULL) return 0;
  return source_quality_data_pointer_value_with_signed_displacement(&state->addr_regs[operand->value.ea_reg],
    (int32_t)operand->value.value, out_section_index, out_offset);
}

static int source_quality_candidate_next_is_indexed_control_through_reg(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
    const M68kSourceQualityAudioPointerState *state, uint8_t reg, uint8_t index_is_address,
    uint32_t table_section_index, uint32_t table_offset, uint32_t *out_next_offset,
    uint32_t *out_target_base_offset) {
  const M68kDecodeCandidate *next_candidate;
  M68kInstructionIR next_instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index = 0U;
  uint32_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  uint32_t next_offset;
  const M68kOperandIR *operand;
  if (out_next_offset != NULL) *out_next_offset = 0U;
  if (out_target_base_offset != NULL) *out_target_base_offset = 0U;
  if (section == NULL || accepted_start == NULL || candidate == NULL || reg >= 8U ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  next_offset = candidate->offset + candidate->byte_count;
  if (next_offset >= section->size || !accepted_start[next_offset]) return 0;
  next_candidate = m68k_decode_ir_find_candidate_at_offset(section, next_offset);
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
  operand = &next_instruction.operands[operand_index];
  if (operand->kind != M68K_ASM_OPERAND_EA ||
      !source_quality_ea_shape_is_indexed_or_pc_indexed(m68k_instruction_operand_decoded_ea_shape(operand)) ||
      operand->value.index_is_address != index_is_address || operand->value.index_reg != reg) {
    return 0;
  }
  if (!source_quality_indexed_control_operand_target(next_candidate, (uint32_t)operand_index, operand, state,
      &target_section_index, &target_offset)) {
    return 0;
  }
  if (target_section_index != table_section_index || target_offset < table_offset ||
      ((target_offset - table_offset) & 1U) != 0U) {
    return 0;
  }
  if (out_next_offset != NULL) *out_next_offset = next_offset;
  if (out_target_base_offset != NULL) *out_target_base_offset = target_offset;
  return 1;
}

static int source_quality_candidate_preserves_address_reg_before_dispatch(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate, uint8_t reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint32_t target_offset = 0U;
  if (candidate == NULL || reg >= 8U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return 0;
  if (metadata->flow_kind == M68K_SIM_FLOW_CALL) {
    return source_quality_candidate_local_call_target(section, candidate, &target_offset) &&
      source_quality_local_callee_preserves_address_register_mask_with_depth(section, accepted_start, target_offset,
        (uint8_t)(1U << reg), 0U);
  }
  if (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
      metadata->flow_kind == M68K_SIM_FLOW_RETURN || metadata->flow_kind == M68K_SIM_FLOW_TRAP ||
      (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U)) {
    return 0;
  }
  return !source_quality_instruction_writes_address_register_mask(&instruction, (uint8_t)(1U << reg));
}

static int source_quality_candidate_later_is_indirect_dispatch_through_addr_reg(
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
    uint8_t reg) {
  const uint32_t max_gap_instructions = 4U;
  uint32_t cursor;
  uint32_t gap_count;
  if (section == NULL || accepted_start == NULL || candidate == NULL || reg >= 8U ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  if (source_quality_candidate_next_is_indirect_control_through_addr_reg(section, accepted_start, candidate, reg))
    return 1;
  cursor = candidate->offset + candidate->byte_count;
  for (gap_count = 0U; gap_count < max_gap_instructions && cursor < section->size; ++gap_count) {
    const M68kDecodeCandidate *gap_candidate;
    if (!accepted_start[cursor]) return 0;
    gap_candidate = m68k_decode_ir_find_candidate_at_offset(section, cursor);
    if (gap_candidate == NULL) return 0;
    if (source_quality_candidate_next_is_indirect_control_through_addr_reg(section, accepted_start, gap_candidate,
        reg)) {
      return source_quality_candidate_preserves_address_reg_before_dispatch(section, accepted_start, gap_candidate,
        reg);
    }
    if (!source_quality_candidate_preserves_address_reg_before_dispatch(section, accepted_start, gap_candidate, reg))
      return 0;
    if (gap_candidate->offset > UINT32_MAX - gap_candidate->byte_count) return 0;
    cursor = gap_candidate->offset + gap_candidate->byte_count;
  }
  return 0;
}

static uint32_t source_quality_scan_indexed_word_dispatch_table_span(
    M68kSourceAnalysisIR *source_analysis, const M68kDecodeIR *decode, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes, uint32_t table_section_index, uint32_t table_offset,
    uint32_t base_section_index, uint32_t base_offset) {
  const M68kDecodeSectionIR *table_section;
  const M68kDecodeSectionIR *base_section;
  const M68kSectionAnalysisIR *table_analysis;
  uint32_t cursor;
  uint32_t target_count = 0U;
  uint32_t first_forward_target = UINT32_MAX;
  uint8_t saw_unaccepted_target = 0U, stopped_at_boundary = 0U, saw_far_displacement = 0U;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      table_section_index >= decode->section_count || base_section_index >= decode->section_count) {
    return 0U;
  }
  table_section = &decode->sections[table_section_index];
  base_section = &decode->sections[base_section_index];
  table_analysis = source_analysis_section_by_index(source_analysis, table_section_index);
  if (table_section->data == NULL || table_offset >= table_section->size ||
      base_offset >= base_section->size || accepted_start[base_section_index] == NULL ||
      accepted_bytes[table_section_index] == NULL || table_analysis == NULL) {
    return 0U;
  }
  for (cursor = table_offset; cursor + 2U <= table_section->size; cursor += 2U) {
    int32_t displacement;
    int64_t target64;
    if (cursor != table_offset && source_quality_section_has_label_at(table_analysis, cursor)) {
      stopped_at_boundary = 1U;
      break;
    }
    if (source_quality_accepted_range_has_code_byte(accepted_bytes[table_section_index], table_section->size,
        cursor, 2U)) {
      break;
    }
    displacement = (int32_t)(int16_t)m68k_read_u16be(table_section->data + cursor);
    target64 = (int64_t)(uint64_t)base_offset + (int64_t)displacement;
    if (saw_far_displacement && target_count >= 2U && cursor != table_offset && displacement == 0 &&
        cursor + 4U <= table_section->size && m68k_read_u16be(table_section->data + cursor + 2U) == 0U) {
      stopped_at_boundary = 1U;
      break;
    }
    if (displacement < -M68K_SOURCE_QUALITY_WORD_DISPATCH_LOCAL_LIMIT ||
        displacement > M68K_SOURCE_QUALITY_WORD_DISPATCH_LOCAL_LIMIT) break;
    if (displacement < -M68K_SOURCE_QUALITY_WORD_DISPATCH_FAR_BOUNDARY_MIN ||
        displacement > M68K_SOURCE_QUALITY_WORD_DISPATCH_FAR_BOUNDARY_MIN) {
      saw_far_displacement = 1U;
    }
    if (target64 < 0 || target64 >= (int64_t)(uint64_t)base_section->size ||
        ((uint32_t)target64 & 1U) != 0U) {
      break;
    }
    if (source_quality_accepted_range_has_code_byte(accepted_bytes[base_section_index], base_section->size,
        (uint32_t)target64, 1U) && !accepted_start[base_section_index][(uint32_t)target64]) {
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
  }
  if (target_count < 2U) return 0U;
  if (!saw_unaccepted_target || stopped_at_boundary) return target_count * 2U;
  return 0U;
}

static uint32_t source_quality_skip_leading_zero_word_dispatch_entries(const M68kDecodeIR *decode,
    uint32_t section_index, uint32_t table_offset, uint32_t base_offset) {
  const M68kDecodeSectionIR *section;
  if (decode == NULL || section_index >= decode->section_count || table_offset >= base_offset) return table_offset;
  section = &decode->sections[section_index];
  if (section->data == NULL) return table_offset;
  while (table_offset < base_offset && table_offset + 2U <= section->size &&
      m68k_read_u16be(section->data + table_offset) == 0U) {
    table_offset += 2U;
  }
  return table_offset;
}

static uint32_t source_quality_scan_keyed_long_relative_dispatch_table_span(
    M68kSourceAnalysisIR *source_analysis, const M68kDecodeIR *decode, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes, uint32_t table_section_index, uint32_t table_offset,
    uint32_t base_section_index, uint32_t base_offset) {
  const M68kDecodeSectionIR *table_section;
  const M68kDecodeSectionIR *base_section;
  const M68kSectionAnalysisIR *table_analysis;
  const M68kSectionAnalysisIR *base_analysis;
  uint32_t cursor;
  uint32_t target_count = 0U;
  uint32_t first_forward_target = UINT32_MAX;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      table_section_index >= decode->section_count || base_section_index >= decode->section_count) {
    return 0U;
  }
  table_section = &decode->sections[table_section_index];
  base_section = &decode->sections[base_section_index];
  table_analysis = source_analysis_section_by_index(source_analysis, table_section_index);
  base_analysis = source_analysis_section_by_index(source_analysis, base_section_index);
  if (table_section->data == NULL || table_offset >= table_section->size ||
      base_offset >= base_section->size || accepted_start[base_section_index] == NULL ||
      accepted_bytes[table_section_index] == NULL || table_analysis == NULL || base_analysis == NULL) {
    return 0U;
  }
  for (cursor = table_offset; cursor + 4U <= table_section->size; cursor += 4U) {
    uint32_t entry;
    int32_t displacement;
    int64_t target64;
    if (cursor != table_offset && source_quality_section_has_label_at(table_analysis, cursor)) break;
    if (source_quality_accepted_range_has_code_byte(accepted_bytes[table_section_index], table_section->size,
        cursor, 4U)) {
      break;
    }
    entry = m68k_read_u32be(table_section->data + cursor);
    if (entry == 0U) break;
    displacement = (int32_t)(int16_t)((entry >> 16U) & 0xFFFFU);
    if (displacement < -M68K_SOURCE_QUALITY_WORD_DISPATCH_LOCAL_LIMIT ||
        displacement > M68K_SOURCE_QUALITY_WORD_DISPATCH_LOCAL_LIMIT) {
      break;
    }
    target64 = (int64_t)(uint64_t)base_offset + (int64_t)displacement;
    if (target64 < 0 || target64 >= (int64_t)(uint64_t)base_section->size ||
        ((uint32_t)target64 & 1U) != 0U) {
      break;
    }
    if (source_quality_accepted_range_has_code_byte(accepted_bytes[base_section_index], base_section->size,
        (uint32_t)target64, 1U) && !accepted_start[base_section_index][(uint32_t)target64]) {
      break;
    }
    if (!accepted_start[base_section_index][(uint32_t)target64] ||
        !source_quality_section_has_label_at(base_analysis, (uint32_t)target64)) {
      break;
    }
    ++target_count;
    if (table_section_index == base_section_index && (uint32_t)target64 > table_offset &&
        (uint32_t)target64 < first_forward_target) {
      first_forward_target = (uint32_t)target64;
    }
    if (target_count >= 2U && first_forward_target != UINT32_MAX && cursor + 4U >= first_forward_target) break;
  }
  return target_count >= 2U ? target_count * 4U : 0U;
}

static int source_quality_candidate_loads_postincrement_long_table_to_data_reg(
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    const M68kSourceQualityAudioPointerState *state, uint32_t *out_table_section_index,
    uint32_t *out_table_offset, uint8_t *out_dest_reg) {
  const M68kSimFormMetadata *metadata = NULL;
  size_t source_index = 0U;
  size_t dest_index = 0U;
  uint8_t source_reg = 0U;
  uint8_t dest_reg = 0U;
  if (out_table_section_index != NULL) *out_table_section_index = 0U;
  if (out_table_offset != NULL) *out_table_offset = 0U;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (candidate == NULL || instruction == NULL || state == NULL || out_table_section_index == NULL ||
      out_table_offset == NULL || out_dest_reg == NULL || instruction->size_suffix != 'l' ||
      !source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
        &metadata) ||
      metadata == NULL || source_index >= instruction->operand_count || dest_index >= instruction->operand_count ||
      source_index >= 4U) {
    return 0;
  }
  if (metadata->operand_access_kinds[source_index] != M68K_SIM_ACCESS_MEMORY_READ ||
      !source_quality_operand_is_address_postincrement(&instruction->operands[source_index], &source_reg) ||
      !source_quality_operand_data_register_index(&instruction->operands[dest_index], &dest_reg) ||
      source_reg >= 8U || !state->addr_regs[source_reg].known) {
    return 0;
  }
  *out_table_section_index = state->addr_regs[source_reg].target_section_index;
  *out_table_offset = state->addr_regs[source_reg].target_offset;
  *out_dest_reg = dest_reg;
  return 1;
}

static int source_quality_candidate_is_swap_data_reg(const M68kDecodeCandidate *candidate, uint8_t reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t operand_reg = 0U;
  if (candidate == NULL || reg >= 8U || candidate->operand_count != 1U ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  return metadata != NULL && metadata->operation_type == M68K_SIM_OP_SWAP_WORDS &&
    source_quality_operand_data_register_index(&instruction.operands[0], &operand_reg) && operand_reg == reg;
}

static int source_quality_candidate_is_indexed_control_through_data_reg_base(
    const M68kDecodeCandidate *candidate, const M68kSourceQualityAudioPointerState *state, uint8_t reg,
    uint32_t table_section_index, uint32_t table_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index = 0U;
  uint32_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  const M68kOperandIR *operand;
  if (candidate == NULL || reg >= 8U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_JUMP && metadata->flow_kind != M68K_SIM_FLOW_CALL)) {
    return 0;
  }
  if (metadata->target_operand_index < instruction.operand_count)
    operand_index = metadata->target_operand_index;
  if (operand_index >= instruction.operand_count) return 0;
  operand = &instruction.operands[operand_index];
  if (operand->kind != M68K_ASM_OPERAND_EA ||
      !source_quality_ea_shape_is_indexed_or_pc_indexed(m68k_instruction_operand_decoded_ea_shape(operand)) ||
      operand->value.index_is_address || operand->value.index_reg != reg) {
    return 0;
  }
  if (!source_quality_indexed_control_operand_target(candidate, (uint32_t)operand_index, operand, state,
      &target_section_index, &target_offset)) {
    return 0;
  }
  return target_section_index == table_section_index && target_offset == table_offset;
}

typedef struct M68kSourceQualityKeyedLongDispatchValue {
  uint8_t known;
  uint8_t swapped;
  uint32_t table_section_index;
  uint32_t table_offset;
} M68kSourceQualityKeyedLongDispatchValue;

typedef struct M68kSourceQualityKeyedLongDispatchState {
  M68kSourceQualityKeyedLongDispatchValue data_regs[8];
} M68kSourceQualityKeyedLongDispatchState;

static void source_quality_keyed_long_dispatch_state_clear(M68kSourceQualityKeyedLongDispatchState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void source_quality_keyed_long_dispatch_state_clear_reg(M68kSourceQualityKeyedLongDispatchState *state,
    uint8_t reg) {
  if (state == NULL || reg >= 8U) return;
  memset(&state->data_regs[reg], 0, sizeof(state->data_regs[reg]));
}

static void source_quality_keyed_long_dispatch_state_set_loaded(M68kSourceQualityKeyedLongDispatchState *state,
    uint8_t reg, uint32_t table_section_index, uint32_t table_offset) {
  M68kSourceQualityKeyedLongDispatchValue *value;
  if (state == NULL || reg >= 8U) return;
  value = &state->data_regs[reg];
  memset(value, 0, sizeof(*value));
  value->known = 1U;
  value->table_section_index = table_section_index;
  value->table_offset = table_offset;
}

static void source_quality_keyed_long_dispatch_state_mark_swapped(M68kSourceQualityKeyedLongDispatchState *state,
    uint8_t reg) {
  if (state == NULL || reg >= 8U || !state->data_regs[reg].known) return;
  state->data_regs[reg].swapped = 1U;
}

static void source_quality_keyed_long_dispatch_state_kill_data_writes(
    M68kSourceQualityKeyedLongDispatchState *state, const M68kInstructionIR *instruction, uint8_t preserve_reg) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (state == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) {
    source_quality_keyed_long_dispatch_state_clear(state);
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_LIST_WRITE &&
        operand->kind == M68K_ASM_OPERAND_REGLIST) {
      uint8_t bit;
      for (bit = 0U; bit < 8U; ++bit) {
        if ((operand->value.value & (1UL << bit)) != 0U && bit != preserve_reg)
          source_quality_keyed_long_dispatch_state_clear_reg(state, bit);
      }
      continue;
    }
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE) continue;
    if (source_quality_operand_data_register_index(operand, &reg) && reg < 8U && reg != preserve_reg)
      source_quality_keyed_long_dispatch_state_clear_reg(state, reg);
  }
}

static void source_quality_keyed_long_dispatch_state_update_after_instruction(
    M68kSourceQualityKeyedLongDispatchState *state, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, const M68kSourceQualityAudioPointerState *pointer_state) {
  const M68kSimFormMetadata *metadata;
  uint32_t table_section_index = 0U;
  uint32_t table_offset = 0U;
  uint8_t reg = 0U;
  uint8_t preserve_reg = UINT8_MAX;
  int loaded = 0;
  int swapped = 0;
  if (state == NULL || candidate == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) {
    source_quality_keyed_long_dispatch_state_clear(state);
    return;
  }
  if (source_quality_candidate_loads_postincrement_long_table_to_data_reg(candidate, instruction, pointer_state,
      &table_section_index, &table_offset, &reg)) {
    preserve_reg = reg;
    loaded = 1;
  } else {
    uint8_t scan_reg;
    for (scan_reg = 0U; scan_reg < 8U; ++scan_reg) {
      if (state->data_regs[scan_reg].known && source_quality_candidate_is_swap_data_reg(candidate, scan_reg)) {
        preserve_reg = scan_reg;
        reg = scan_reg;
        swapped = 1;
        break;
      }
    }
  }
  source_quality_keyed_long_dispatch_state_kill_data_writes(state, instruction, preserve_reg);
  if (loaded) source_quality_keyed_long_dispatch_state_set_loaded(state, reg, table_section_index, table_offset);
  else if (swapped) source_quality_keyed_long_dispatch_state_mark_swapped(state, reg);
  if (metadata->flow_kind == M68K_SIM_FLOW_CALL || metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
      metadata->flow_kind == M68K_SIM_FLOW_RETURN || metadata->flow_kind == M68K_SIM_FLOW_TRAP) {
    source_quality_keyed_long_dispatch_state_clear(state);
  }
}

static int source_quality_maybe_add_keyed_long_dispatch_table(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, uint8_t *const *accepted_bytes,
    const M68kSourceQualityKeyedLongDispatchState *state,
    const M68kSourceQualityAudioPointerState *pointer_state, uint32_t section_index,
    const M68kDecodeCandidate *candidate) {
  uint8_t reg;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      state == NULL || candidate == NULL) {
    return 0;
  }
  for (reg = 0U; reg < 8U; ++reg) {
    const M68kSourceQualityKeyedLongDispatchValue *value = &state->data_regs[reg];
    uint32_t span;
    if (!value->known || !value->swapped) continue;
    if (!source_quality_candidate_is_indexed_control_through_data_reg_base(candidate, pointer_state, reg,
        value->table_section_index, value->table_offset)) {
      continue;
    }
    span = source_quality_scan_keyed_long_relative_dispatch_table_span(source_analysis, decode, accepted_start,
      accepted_bytes, value->table_section_index, value->table_offset, value->table_section_index,
      value->table_offset);
    if (span == 0U) continue;
    if (append_pc_relative_lookup_table_item(source_analysis, value->table_section_index, value->table_offset,
        span, M68K_ANALYSIS_STRUCTURED_DATA_LONGS,
        M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH, section_index,
        candidate->offset, 0U, M68K_ANALYSIS_REGISTER_NONE, 0U, 0U, M68K_ANALYSIS_REGISTER_NONE, 0U, NULL, 1U,
        value->table_section_index, value->table_offset) != 0) {
      return -1;
    }
  }
  return 0;
}

static int source_quality_candidate_adds_indexed_word_table_to_address_reg(
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    const M68kSourceQualityAudioPointerState *state, uint32_t *out_table_section_index,
    uint32_t *out_table_offset, uint32_t *out_base_section_index, uint32_t *out_base_offset,
    uint8_t *out_dest_reg, uint8_t *out_index_register_kind, uint8_t *out_index_register) {
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
  if (out_index_register_kind != NULL) *out_index_register_kind = M68K_ANALYSIS_REGISTER_NONE;
  if (out_index_register != NULL) *out_index_register = 0U;
  if (candidate == NULL || instruction == NULL || state == NULL || out_table_section_index == NULL ||
      out_table_offset == NULL || out_base_section_index == NULL || out_base_offset == NULL ||
      out_dest_reg == NULL || candidate->size_suffix != 'w' ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_ADDA) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_ADD) return 0;
  if (metadata->source_operand_index < candidate->operand_count) source_index = metadata->source_operand_index;
  if (metadata->dest_operand_index < candidate->operand_count) dest_index = metadata->dest_operand_index;
  if (source_index < candidate->operand_count && source_index < instruction->operand_count && source_index < 4U &&
      !((metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
         metadata->operand_ea_uses_index[source_index]) ||
        source_quality_ea_shape_is_indexed_or_pc_indexed(metadata->operand_ea_address_shapes[source_index]) ||
        source_quality_ea_shape_is_indexed_or_pc_indexed(
          m68k_instruction_operand_decoded_ea_shape(&instruction->operands[source_index])))) {
    source_index = (size_t)-1;
  }
  if (dest_index < instruction->operand_count &&
      !source_quality_operand_address_register_index(&instruction->operands[dest_index], NULL)) {
    dest_index = (size_t)-1;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    if (source_index == (size_t)-1 &&
        ((metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_READ &&
          metadata->operand_ea_uses_index[operand_index]) ||
         source_quality_ea_shape_is_indexed_or_pc_indexed(metadata->operand_ea_address_shapes[operand_index]) ||
         (operand_index < instruction->operand_count &&
          source_quality_ea_shape_is_indexed_or_pc_indexed(
            m68k_instruction_operand_decoded_ea_shape(&instruction->operands[operand_index]))))) {
      source_index = operand_index;
    }
    if (dest_index == (size_t)-1 &&
        metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        source_quality_operand_address_register_index(&instruction->operands[operand_index], &dest_reg)) {
      dest_index = operand_index;
    }
  }
  if (source_index >= candidate->operand_count || dest_index >= instruction->operand_count ||
      source_index >= instruction->operand_count || source_index >= 4U) {
    return 0;
  }
  if (!source_quality_operand_address_register_index(&instruction->operands[dest_index], &dest_reg) ||
      dest_reg >= 8U || !state->addr_regs[dest_reg].known) {
    return 0;
  }
  if (!source_quality_ea_shape_is_indexed_or_pc_indexed(
        m68k_instruction_operand_decoded_ea_shape(&instruction->operands[source_index])) ||
      instruction->operands[source_index].value.index_reg >= 8U) {
    return 0;
  }
  if (!source_quality_indexed_control_operand_target(candidate, (uint32_t)source_index,
      &instruction->operands[source_index], state, out_table_section_index, out_table_offset)) {
    return 0;
  }
  *out_base_section_index = state->addr_regs[dest_reg].target_section_index;
  *out_base_offset = state->addr_regs[dest_reg].target_offset;
  *out_dest_reg = dest_reg;
  if (out_index_register_kind != NULL) {
    *out_index_register_kind = instruction->operands[source_index].value.index_is_address ?
      M68K_ANALYSIS_REGISTER_ADDRESS : M68K_ANALYSIS_REGISTER_DATA;
  }
  if (out_index_register != NULL) *out_index_register = instruction->operands[source_index].value.index_reg;
  return 1;
}

static int source_quality_candidate_loads_indexed_word_table_to_reg(
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    const M68kSourceQualityAudioPointerState *state, uint8_t dest_is_address,
    uint32_t *out_table_section_index, uint32_t *out_table_offset, uint8_t *out_dest_reg,
    uint8_t *out_index_register_kind, uint8_t *out_index_register) {
  const M68kSimFormMetadata *metadata = NULL;
  size_t source_index = 0U;
  size_t dest_index = 0U;
  uint8_t dest_reg = 0U;
  if (out_table_section_index != NULL) *out_table_section_index = 0U;
  if (out_table_offset != NULL) *out_table_offset = 0U;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_index_register_kind != NULL) *out_index_register_kind = M68K_ANALYSIS_REGISTER_NONE;
  if (out_index_register != NULL) *out_index_register = 0U;
  if (candidate == NULL || instruction == NULL || out_table_section_index == NULL ||
      out_table_offset == NULL || out_dest_reg == NULL || instruction->size_suffix != 'w' ||
      !source_quality_instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
        &metadata) ||
      metadata == NULL || source_index >= instruction->operand_count || dest_index >= instruction->operand_count ||
      source_index >= candidate->operand_count || source_index >= 4U) {
    return 0;
  }
  if (!((metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        metadata->operand_ea_uses_index[source_index]) ||
       source_quality_ea_shape_is_indexed_or_pc_indexed(metadata->operand_ea_address_shapes[source_index]) ||
       source_quality_ea_shape_is_indexed_or_pc_indexed(
         m68k_instruction_operand_decoded_ea_shape(&instruction->operands[source_index])))) {
    return 0;
  }
  if (dest_is_address) {
    if (!source_quality_operand_address_register_index(&instruction->operands[dest_index], &dest_reg)) return 0;
  } else if (!source_quality_operand_data_register_index(&instruction->operands[dest_index], &dest_reg)) {
    return 0;
  }
  if (!source_quality_indexed_control_operand_target(candidate, (uint32_t)source_index,
      &instruction->operands[source_index], state, out_table_section_index, out_table_offset)) {
    return 0;
  }
  if (instruction->operands[source_index].value.index_reg >= 8U) return 0;
  *out_dest_reg = dest_reg;
  if (out_index_register_kind != NULL) {
    *out_index_register_kind = instruction->operands[source_index].value.index_is_address ?
      M68K_ANALYSIS_REGISTER_ADDRESS : M68K_ANALYSIS_REGISTER_DATA;
  }
  if (out_index_register != NULL) *out_index_register = instruction->operands[source_index].value.index_reg;
  return 1;
}

static int source_quality_instruction_scales_word_index_register(const M68kInstructionIR *instruction,
    uint8_t index_reg) {
  uint8_t left_reg = 0U;
  uint8_t right_reg = 0U;
  return instruction != NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADD &&
    instruction->size_suffix == 'w' && instruction->operand_count == 2U &&
    source_quality_operand_data_register_index(&instruction->operands[0], &left_reg) &&
    source_quality_operand_data_register_index(&instruction->operands[1], &right_reg) &&
    left_reg == index_reg && right_reg == index_reg;
}

static int source_quality_instruction_masks_index_register(const M68kInstructionIR *instruction,
    uint8_t index_reg, uint32_t *out_mask) {
  uint8_t dest_reg = 0U;
  uint32_t value = 0U;
  if (out_mask != NULL) *out_mask = 0U;
  if (instruction == NULL || instruction->size_suffix != 'w' || instruction->operand_count != 2U ||
      (instruction->mnemonic_id != M68K_ASM_MNEMONIC_ANDI &&
       instruction->mnemonic_id != M68K_ASM_MNEMONIC_AND) ||
      !m68k_ir_operand_immediate_value(&instruction->operands[0], &value) ||
      !source_quality_operand_data_register_index(&instruction->operands[1], &dest_reg) ||
      dest_reg != index_reg) {
    return 0;
  }
  if (out_mask != NULL) *out_mask = value & 0xFFFFU;
  return 1;
}

static int source_quality_instruction_compares_index_register_immediate(const M68kInstructionIR *instruction,
    uint8_t index_reg, uint32_t *out_limit) {
  uint8_t dest_reg = 0U;
  uint32_t value = 0U;
  if (out_limit != NULL) *out_limit = 0U;
  if (instruction == NULL || instruction->size_suffix != 'w' || instruction->operand_count != 2U ||
      (instruction->mnemonic_id != M68K_ASM_MNEMONIC_CMPI &&
       instruction->mnemonic_id != M68K_ASM_MNEMONIC_CMP) ||
      !m68k_ir_operand_immediate_value(&instruction->operands[0], &value) ||
      !source_quality_operand_data_register_index(&instruction->operands[1], &dest_reg) ||
      dest_reg != index_reg) {
    return 0;
  }
  if (out_limit != NULL) *out_limit = value & 0xFFFFU;
  return 1;
}

static int source_quality_branch_mnemonic_exits_above_compare(uint8_t mnemonic_id) {
  return mnemonic_id == M68K_ASM_MNEMONIC_BHI || mnemonic_id == M68K_ASM_MNEMONIC_BGT;
}

static void source_quality_derive_index_domain_before_table_access(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t table_access_offset, uint8_t index_register_kind,
    uint8_t index_register, M68kSourceQualityTableIndexDomainEvidence *out_domain) {
  const M68kDecodeCandidate *candidates[8];
  M68kInstructionIR instructions[8];
  size_t count = 0U;
  size_t index;
  size_t scale_index = SIZE_MAX;
  uint32_t cursor;
  if (out_domain == NULL) return;
  memset(out_domain, 0, sizeof(*out_domain));
  if (section == NULL || accepted_start == NULL || index_register_kind != M68K_ANALYSIS_REGISTER_DATA ||
      index_register >= 8U) {
    return;
  }
  cursor = table_access_offset;
  while (count < sizeof(candidates) / sizeof(candidates[0])) {
    const M68kDecodeCandidate *previous = source_quality_previous_accepted_candidate(section, accepted_start, cursor);
    if (previous == NULL || previous->byte_count == 0U || previous->offset + previous->byte_count != cursor) break;
    candidates[count++] = previous;
    cursor = previous->offset;
  }
  for (index = 0U; index < count; ++index) {
    const M68kDecodeCandidate *previous = candidates[count - 1U - index];
    if (m68k_decode_candidate_to_instruction(previous, &instructions[index]) != 0) return;
    if (source_quality_instruction_scales_word_index_register(&instructions[index], index_register))
      scale_index = index;
  }
  if (scale_index == SIZE_MAX) return;
  for (index = scale_index + 1U; index < count; ++index) {
    if (instructions[index].mnemonic_id != M68K_ASM_MNEMONIC_LEA &&
        instructions[index].mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) {
      return;
    }
  }
  for (index = 0U; index < scale_index; ++index) {
    uint32_t mask = 0U;
    if (source_quality_instruction_masks_index_register(&instructions[index], index_register, &mask)) {
      out_domain->has_mask = 1U;
      out_domain->mask_min = 0U;
      out_domain->mask_max = mask;
    }
  }
  for (index = 0U; index + 1U < scale_index; ++index) {
    uint32_t limit = 0U;
    if (source_quality_instruction_compares_index_register_immediate(&instructions[index], index_register,
        &limit) &&
        source_quality_branch_mnemonic_exits_above_compare(instructions[index + 1U].mnemonic_id)) {
      out_domain->has_compare = 1U;
      out_domain->compare_min = 0U;
      out_domain->compare_max = limit;
      out_domain->branch_mnemonic_id = instructions[index + 1U].mnemonic_id;
    }
  }
}

static int source_quality_append_dispatch_table_item(M68kSourceAnalysisIR *source_analysis,
    uint32_t table_section_index, uint32_t table_offset, uint32_t size, uint8_t kind,
    uint32_t consumer_section, uint32_t consumer_offset, uint8_t index_register_kind, uint8_t index_register,
    uint8_t target_register_kind, uint8_t target_register,
    const M68kSourceQualityTableIndexDomainEvidence *index_domain, uint32_t target_section,
    uint32_t target_offset) {
  return append_pc_relative_lookup_table_item(source_analysis, table_section_index, table_offset, size, kind,
    M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_WORD_DISPATCH, consumer_section, consumer_offset, 1U,
    index_register_kind, index_register, 1U, target_register_kind, target_register, index_domain, 1U,
    target_section, target_offset);
}

static int append_indexed_word_dispatch_table_items(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, uint8_t *const *accepted_bytes) {
  size_t decode_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL) return 0;
  for (decode_index = 0U; decode_index < decode->section_count; ++decode_index) {
    const M68kDecodeSectionIR *section = &decode->sections[decode_index];
    M68kSourceQualityAudioPointerState state;
    M68kSourceQualityKeyedLongDispatchState keyed_state;
    M68kSectionAnalysisIR *section_analysis;
    size_t candidate_index;
    uint32_t section_index;
    if (section->section_index > UINT32_MAX || accepted_start[decode_index] == NULL ||
        accepted_bytes[decode_index] == NULL) {
      return -1;
    }
    section_index = (uint32_t)section->section_index;
    section_analysis = source_analysis_section_by_index(source_analysis, section_index);
    if (section_analysis == NULL) continue;
    source_quality_audio_pointer_state_clear_all(&state);
    source_quality_keyed_long_dispatch_state_clear(&keyed_state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      if (!source_quality_candidate_is_accepted_start(section, accepted_start[decode_index], candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      if (source_quality_maybe_add_keyed_long_dispatch_table(source_analysis, decode, accepted_start,
          accepted_bytes, &keyed_state, &state, section_index, candidate) != 0) {
        return -1;
      }
      {
        uint32_t load_table_section = 0U;
        uint32_t load_table_offset = 0U;
        uint32_t addr_load_table_section = 0U;
        uint32_t addr_load_table_offset = 0U;
        uint32_t add_sections[2] = {0U, 0U};
        uint32_t add_offsets[2] = {0U, 0U};
        uint32_t table_size = 0U;
        uint32_t consumer_offset = 0U;
        uint32_t target_base_offset = 0U;
        uint8_t dest_reg = 0U;
        uint8_t addr_dest_reg = 0U;
        uint8_t load_index_register_kind = M68K_ANALYSIS_REGISTER_NONE;
        uint8_t load_index_register = 0U;
        uint8_t addr_load_index_register_kind = M68K_ANALYSIS_REGISTER_NONE;
        uint8_t addr_load_index_register = 0U;
        uint8_t add_index_register_kind = M68K_ANALYSIS_REGISTER_NONE;
        uint8_t add_index_register = 0U;
        int loads_dispatch;
        int loads_address_dispatch;
        int next_indexed_dispatch;
        int next_address_indexed_dispatch;
        int adds_dispatch;
        int next_dispatch;
        loads_dispatch = source_quality_candidate_loads_indexed_word_table_to_reg(candidate, &instruction, &state,
          0U, &load_table_section, &load_table_offset, &dest_reg, &load_index_register_kind,
          &load_index_register);
        next_indexed_dispatch = loads_dispatch ?
          source_quality_candidate_next_is_indexed_control_through_reg(section, accepted_start[decode_index],
            candidate, &state, dest_reg, 0U, load_table_section, load_table_offset, &consumer_offset,
            &target_base_offset) : 0;
        loads_address_dispatch = source_quality_candidate_loads_indexed_word_table_to_reg(candidate, &instruction,
          &state, 1U, &addr_load_table_section, &addr_load_table_offset, &addr_dest_reg,
          &addr_load_index_register_kind, &addr_load_index_register);
        next_address_indexed_dispatch = loads_address_dispatch ?
          source_quality_candidate_next_is_indexed_control_through_reg(section, accepted_start[decode_index],
            candidate, &state, addr_dest_reg, 1U, addr_load_table_section, addr_load_table_offset,
            &consumer_offset, &target_base_offset) : 0;
        adds_dispatch = source_quality_candidate_adds_indexed_word_table_to_address_reg(candidate, &instruction,
          &state, &add_sections[0], &add_offsets[0], &add_sections[1], &add_offsets[1], &dest_reg,
          &add_index_register_kind, &add_index_register);
        next_dispatch = adds_dispatch ?
          source_quality_candidate_later_is_indirect_dispatch_through_addr_reg(section, accepted_start[decode_index],
            candidate, dest_reg) : 0;
        if ((loads_dispatch && next_indexed_dispatch) ||
            (loads_address_dispatch && next_address_indexed_dispatch)) {
          uint32_t dispatch_table_section = loads_dispatch ? load_table_section : addr_load_table_section;
          uint32_t dispatch_table_offset_raw = loads_dispatch ? load_table_offset : addr_load_table_offset;
          uint8_t table_index_register_kind = loads_dispatch ? load_index_register_kind :
            addr_load_index_register_kind;
          uint8_t table_index_register = loads_dispatch ? load_index_register : addr_load_index_register;
          uint8_t table_target_register_kind = loads_dispatch ? M68K_ANALYSIS_REGISTER_DATA :
            M68K_ANALYSIS_REGISTER_ADDRESS;
          uint8_t table_target_register = loads_dispatch ? dest_reg : addr_dest_reg;
          M68kSourceQualityTableIndexDomainEvidence index_domain;
          uint32_t dispatch_table_offset = source_quality_skip_leading_zero_word_dispatch_entries(decode,
            dispatch_table_section, dispatch_table_offset_raw, target_base_offset);
          source_quality_derive_index_domain_before_table_access(section, accepted_start[decode_index],
            candidate->offset, table_index_register_kind, table_index_register, &index_domain);
          if (dispatch_table_section < decode->section_count && dispatch_table_offset < target_base_offset &&
              !source_quality_accepted_range_has_code_byte(accepted_bytes[dispatch_table_section],
                decode->sections[dispatch_table_section].size, dispatch_table_offset,
                target_base_offset - dispatch_table_offset)) {
            M68kSectionAnalysisIR *dispatch_table_analysis =
              source_analysis_section_by_index(source_analysis, dispatch_table_section);
            uint32_t leading_size = target_base_offset - dispatch_table_offset;
            if (!source_quality_section_has_interior_label(dispatch_table_analysis, dispatch_table_offset,
                leading_size)) {
              if (source_quality_append_dispatch_table_item(source_analysis, dispatch_table_section,
                  dispatch_table_offset, leading_size, M68K_ANALYSIS_STRUCTURED_DATA_WORDS, section_index,
                  consumer_offset, table_index_register_kind, table_index_register, table_target_register_kind,
                  table_target_register, &index_domain, dispatch_table_section, target_base_offset) != 0) {
                return -1;
              }
            }
          }
          table_size = source_quality_scan_indexed_word_dispatch_table_span(source_analysis, decode, accepted_start,
            accepted_bytes, dispatch_table_section, target_base_offset, dispatch_table_section, target_base_offset);
          if (table_size != 0U &&
              source_quality_append_dispatch_table_item(source_analysis, dispatch_table_section, target_base_offset,
                table_size, M68K_ANALYSIS_STRUCTURED_DATA_WORDS, section_index, consumer_offset,
                table_index_register_kind, table_index_register, table_target_register_kind,
                table_target_register, &index_domain, dispatch_table_section, target_base_offset) != 0) {
            return -1;
          }
        }
        if (adds_dispatch && next_dispatch) {
          M68kSourceQualityTableIndexDomainEvidence index_domain;
          source_quality_derive_index_domain_before_table_access(section, accepted_start[decode_index],
            candidate->offset, add_index_register_kind, add_index_register, &index_domain);
          table_size = source_quality_scan_indexed_word_dispatch_table_span(source_analysis, decode, accepted_start,
            accepted_bytes, add_sections[0], add_offsets[0], add_sections[1], add_offsets[1]);
          if (table_size != 0U &&
              source_quality_append_dispatch_table_item(source_analysis, add_sections[0], add_offsets[0],
                table_size, M68K_ANALYSIS_STRUCTURED_DATA_WORDS, section_index, candidate->offset,
                add_index_register_kind, add_index_register, M68K_ANALYSIS_REGISTER_ADDRESS, dest_reg,
                &index_domain, add_sections[1], add_offsets[1]) != 0) {
            return -1;
          }
        }
      }
      source_quality_keyed_long_dispatch_state_update_after_instruction(&keyed_state, candidate, &instruction,
        &state);
      source_quality_dispatch_pointer_state_update_after_instruction(&state, section_analysis, section, candidate,
        &instruction);
    }
  }
  return 0;
}

static void source_quality_palette_hardware_range_state_clear_all(
    M68kSourceQualityPaletteHardwareRangeState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void source_quality_palette_hardware_range_state_clear_reg(
    M68kSourceQualityPaletteHardwareRangeState *state, uint8_t reg) {
  if (state == NULL || reg >= 8U) return;
  memset(&state->addr_regs[reg], 0, sizeof(state->addr_regs[reg]));
}

static int source_quality_instruction_loads_hardware_range_to_address_reg(const M68kDecodeCandidate *candidate,
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
      !source_quality_operand_address_register_index(&instruction->operands[1], &dest_reg) ||
      !source_quality_candidate_operand_absolute_value(candidate, 0U, &absolute)) {
    return 0;
  }
  range = amiga_os_find_hardware_register_range_by_cpu_address(absolute);
  if (range == NULL) return 0;
  *out_range = range;
  *out_range_offset = absolute - range->base_address - range->offset;
  *out_reg = dest_reg;
  return 1;
}

static void source_quality_palette_hardware_range_state_update_after_instruction(
    M68kSourceQualityPaletteHardwareRangeState *state, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction) {
  const AmigaOsHardwareRegisterRangeInfo *range = NULL;
  uint32_t range_offset = 0U;
  uint8_t dest_reg = 0U;
  size_t operand_index;
  const M68kSimFormMetadata *metadata;
  if (state == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_CALL) {
    source_quality_palette_hardware_range_state_clear_all(state);
    return;
  }
  if (source_quality_instruction_loads_hardware_range_to_address_reg(candidate, instruction, &range,
      &range_offset, &dest_reg)) {
    state->addr_regs[dest_reg].known = 1U;
    state->addr_regs[dest_reg].range = range;
    state->addr_regs[dest_reg].offset = range_offset;
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    uint8_t bit;
    for (bit = 0U; bit < 8U; ++bit) {
      if (source_quality_reglist_contains_register(&instruction->operands[1], 2U, bit))
        source_quality_palette_hardware_range_state_clear_reg(state, bit);
    }
    return;
  }
  if (metadata == NULL) return;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE) continue;
    if (source_quality_operand_address_register_index(operand, &dest_reg))
      source_quality_palette_hardware_range_state_clear_reg(state, dest_reg);
  }
}

static int source_quality_palette_data_target_for_operand(const M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t operand_index, uint32_t *out_section_index,
    uint32_t *out_offset) {
  const M68kFact *relocation;
  M68kInstructionIR instruction;
  uint32_t absolute_offset = 0U;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (source_quality_candidate_data_target_for_operand(candidate, operand_index, out_section_index, out_offset))
    return 1;
  relocation = source_quality_unique_relocation_ref_for_operand(facts,
    section != NULL ? section->section_index : 0U, candidate, operand_index);
  if (relocation != NULL && decode != NULL && relocation->target_section_index < decode->section_count &&
      relocation->target_offset <= UINT32_MAX) {
    if (out_section_index != NULL) *out_section_index = (uint32_t)relocation->target_section_index;
    if (out_offset != NULL) *out_offset = (uint32_t)relocation->target_offset;
    return 1;
  }
  if (candidate != NULL && m68k_decode_candidate_to_instruction(candidate, &instruction) == 0 &&
      operand_index < instruction.operand_count &&
      source_quality_operand_absolute_offset(&instruction.operands[operand_index], &absolute_offset)) {
    if (source_quality_runtime_address_to_materialized_source(source_analysis, absolute_offset, out_section_index,
        out_offset)) {
      return 1;
    }
    if (section != NULL && absolute_offset < section->size && section->section_index <= UINT32_MAX) {
      if (out_section_index != NULL) *out_section_index = (uint32_t)section->section_index;
      if (out_offset != NULL) *out_offset = absolute_offset;
      return 1;
    }
  }
  return 0;
}

static void source_quality_palette_data_pointer_state_update_after_instruction(
    M68kSourceQualityAudioPointerState *state, const M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  const M68kSourceQualityAudioPointerSource *source_value = NULL;
  uint32_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  uint8_t dest_reg = 0U;
  uint8_t source_reg = 0U;
  int16_t displacement = 0;
  size_t operand_index;
  if (state == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_CALL) {
    source_quality_audio_pointer_state_clear_all(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      source_quality_operand_address_register_index(&instruction->operands[1], &dest_reg)) {
    if (source_quality_palette_data_target_for_operand(source_analysis, decode, facts, section, candidate, 0U,
        &target_section_index, &target_offset)) {
      source_quality_audio_pointer_state_set_reg(state, 2U, dest_reg, target_section_index, target_offset);
      return;
    }
    if (section != NULL &&
        source_quality_operand_address_displacement(&instruction->operands[0], &source_reg, &displacement) &&
        source_reg < 8U && state->addr_regs[source_reg].known &&
        state->addr_regs[source_reg].target_section_index == section->section_index) {
      int64_t adjusted_offset = (int64_t)(uint64_t)state->addr_regs[source_reg].target_offset +
        (int64_t)displacement;
      if (adjusted_offset >= 0 && (uint64_t)adjusted_offset < (uint64_t)section->size) {
        M68kSourceQualityAudioPointerSource adjusted = state->addr_regs[source_reg];
        adjusted.target_offset = (uint32_t)adjusted_offset;
        source_quality_audio_pointer_state_copy_reg(state, 2U, dest_reg, &adjusted);
        return;
      }
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U &&
      source_quality_operand_data_register_index(&instruction->operands[1], &dest_reg) &&
      source_quality_palette_data_target_for_operand(source_analysis, decode, facts, section, candidate, 0U,
        &target_section_index, &target_offset)) {
    source_quality_audio_pointer_state_set_reg(state, 1U, dest_reg, target_section_index, target_offset);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDA && instruction->operand_count == 2U &&
      source_quality_operand_address_register_index(&instruction->operands[1], &dest_reg)) {
    source_quality_audio_pointer_state_mark_dynamic(state, dest_reg, candidate);
    return;
  }
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->operand_count == 2U) {
    source_value = source_quality_audio_pointer_state_value_for_operand(state, &instruction->operands[0]);
    if (source_quality_operand_data_register_index(&instruction->operands[1], &dest_reg)) {
      source_quality_audio_pointer_state_clear_reg(state, 1U, dest_reg);
      if (source_value != NULL) source_quality_audio_pointer_state_copy_reg(state, 1U, dest_reg, source_value);
      return;
    }
    if (source_quality_operand_address_register_index(&instruction->operands[1], &dest_reg)) {
      source_quality_audio_pointer_state_clear_reg(state, 2U, dest_reg);
      if (source_value != NULL) source_quality_audio_pointer_state_copy_reg(state, 2U, dest_reg, source_value);
      return;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
      if (source_quality_reglist_contains_register(&instruction->operands[1], 1U, dest_reg))
        source_quality_audio_pointer_state_clear_reg(state, 1U, dest_reg);
      if (source_quality_reglist_contains_register(&instruction->operands[1], 2U, dest_reg))
        source_quality_audio_pointer_state_clear_reg(state, 2U, dest_reg);
    }
    return;
  }
  if (metadata == NULL) return;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE) continue;
    if (source_quality_operand_data_register_index(operand, &dest_reg))
      source_quality_audio_pointer_state_clear_reg(state, 1U, dest_reg);
    else if (source_quality_operand_address_register_index(operand, &dest_reg))
      source_quality_audio_pointer_state_clear_reg(state, 2U, dest_reg);
  }
}

static int source_quality_instruction_is_movem_reglist_predec_a7(const M68kInstructionIR *instruction,
    uint32_t *out_mask) {
  if (out_mask != NULL) *out_mask = 0U;
  if (instruction == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEM ||
      instruction->size_suffix != 'l' || instruction->operand_count != 2U ||
      instruction->operands[0].kind != M68K_ASM_OPERAND_REGLIST ||
      !source_quality_operand_is_predec_a7(&instruction->operands[1])) {
    return 0;
  }
  if (out_mask != NULL) *out_mask = instruction->operands[0].value.value;
  return 1;
}

static int source_quality_instruction_is_movem_postinc_a7_reglist(const M68kInstructionIR *instruction,
    uint32_t *out_mask) {
  if (out_mask != NULL) *out_mask = 0U;
  if (instruction == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEM ||
      instruction->size_suffix != 'l' || instruction->operand_count != 2U ||
      !source_quality_operand_is_postinc_a7(&instruction->operands[0]) ||
      instruction->operands[1].kind != M68K_ASM_OPERAND_REGLIST) {
    return 0;
  }
  if (out_mask != NULL) *out_mask = instruction->operands[1].value.value;
  return 1;
}

static void source_quality_palette_pointer_save_before_instruction(M68kSourceQualityPalettePointerSave *save,
    const M68kSourceQualityAudioPointerState *data_state,
    const M68kSourceQualityPaletteHardwareRangeState *hardware_state, const M68kInstructionIR *instruction) {
  uint32_t mask = 0U;
  if (save == NULL || data_state == NULL || hardware_state == NULL || instruction == NULL) return;
  if (source_quality_instruction_is_movem_reglist_predec_a7(instruction, &mask)) {
    save->valid = 1U;
    save->mask = mask;
    memcpy(save->data_regs, data_state->data_regs, sizeof(save->data_regs));
    memcpy(save->addr_regs, data_state->addr_regs, sizeof(save->addr_regs));
    memcpy(save->hardware_addr_regs, hardware_state->addr_regs, sizeof(save->hardware_addr_regs));
  } else if ((instruction->operand_count > 0U && source_quality_operand_is_predec_a7(&instruction->operands[0])) ||
      (instruction->operand_count > 1U && source_quality_operand_is_predec_a7(&instruction->operands[1]))) {
    save->valid = 0U;
  }
}

static void source_quality_palette_pointer_save_after_instruction(M68kSourceQualityPalettePointerSave *save,
    M68kSourceQualityAudioPointerState *data_state, M68kSourceQualityPaletteHardwareRangeState *hardware_state,
    const M68kInstructionIR *instruction) {
  uint32_t mask = 0U;
  uint8_t bit;
  const M68kSimFormMetadata *metadata;
  if (save == NULL || data_state == NULL || hardware_state == NULL || instruction == NULL) return;
  if (!source_quality_instruction_is_movem_postinc_a7_reglist(instruction, &mask)) {
    metadata = m68k_sim_metadata_for_instruction(instruction);
    if ((metadata == NULL || metadata->flow_kind != M68K_SIM_FLOW_CALL) &&
        ((instruction->operand_count > 0U && source_quality_operand_is_postinc_a7(&instruction->operands[0])) ||
         (instruction->operand_count > 1U && source_quality_operand_is_postinc_a7(&instruction->operands[1])))) {
      save->valid = 0U;
    }
    return;
  }
  if (!save->valid) return;
  for (bit = 0U; bit < 8U; ++bit) {
    if ((mask & save->mask & (1UL << bit)) != 0U) data_state->data_regs[bit] = save->data_regs[bit];
    if ((mask & save->mask & (1UL << (8U + bit))) != 0U) {
      data_state->addr_regs[bit] = save->addr_regs[bit];
      hardware_state->addr_regs[bit] = save->hardware_addr_regs[bit];
    }
  }
  save->valid = 0U;
}

static int source_quality_candidate_local_call_target(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t *out_target_offset) {
  size_t target_index;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (section == NULL || candidate == NULL || out_target_offset == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_CALL && target->has_section &&
        target->section_index == section->section_index && target->offset < section->size) {
      *out_target_offset = target->offset;
      return 1;
    }
  }
  return 0;
}

static int source_quality_candidate_first_local_control_target(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t *out_target_offset) {
  size_t target_index;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (section == NULL || candidate == NULL || out_target_offset == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if ((target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_JUMP) &&
        target->has_section && target->section_index == section->section_index && target->offset < section->size) {
      *out_target_offset = target->offset;
      return 1;
    }
  }
  return 0;
}

static int source_quality_instruction_writes_address_register_mask(const M68kInstructionIR *instruction,
    uint8_t mask) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint8_t operand_reg = 0U;
  if (instruction == NULL || mask == 0U) return 1;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        source_quality_operand_address_register_index(&instruction->operands[operand_index], &operand_reg) &&
        operand_reg < 8U && (mask & (uint8_t)(1U << operand_reg)) != 0U) {
      return 1;
    }
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_LIST_WRITE) {
      uint8_t reg;
      for (reg = 0U; reg < 8U; ++reg) {
        if ((mask & (uint8_t)(1U << reg)) != 0U &&
            source_quality_reglist_contains_register(&instruction->operands[operand_index], 2U, reg)) {
          return 1;
        }
      }
    }
    if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_NONE &&
        source_quality_operand_is_address_postincrement(&instruction->operands[operand_index], &operand_reg) &&
        operand_reg < 8U && (mask & (uint8_t)(1U << operand_reg)) != 0U) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_local_callee_preserves_address_register_mask_with_depth(
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t target_offset,
    uint8_t mask, uint8_t depth) {
  uint32_t worklist[64];
  uint32_t visited[64];
  uint8_t work_count = 0U;
  uint8_t visited_count = 0U;
  uint8_t visited_any = 0U;
  if (section == NULL || accepted_start == NULL || target_offset >= section->size || mask == 0U || depth > 4U)
    return 0;
  worklist[work_count++] = target_offset;
  while (work_count != 0U) {
    uint32_t cursor = worklist[--work_count];
    uint8_t step;
    for (step = 0U; step < 32U && cursor < section->size && accepted_start[cursor] != 0U; ++step) {
      const M68kDecodeCandidate *candidate;
      M68kInstructionIR instruction;
      const M68kSimFormMetadata *metadata;
      uint32_t target = 0U;
      uint8_t seen = 0U;
      uint8_t index;
      for (index = 0U; index < visited_count; ++index) {
        if (visited[index] == cursor) {
          seen = 1U;
          break;
        }
      }
      if (seen) break;
      if (visited_count >= (uint8_t)(sizeof(visited) / sizeof(visited[0]))) return 0;
      visited[visited_count++] = cursor;
      visited_any = 1U;
      candidate = m68k_decode_ir_find_candidate_at_offset(section, cursor);
      if (candidate == NULL || candidate->byte_count == 0U ||
          m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
        return 0;
      }
      metadata = m68k_sim_metadata_for_instruction(&instruction);
      if (metadata == NULL || source_quality_instruction_writes_address_register_mask(&instruction, mask)) return 0;
      if (metadata->flow_kind == M68K_SIM_FLOW_CALL) {
        if (!source_quality_candidate_local_call_target(section, candidate, &target) ||
            !source_quality_local_callee_preserves_address_register_mask_with_depth(section, accepted_start, target,
              mask, (uint8_t)(depth + 1U))) {
          return 0;
        }
      } else if (source_quality_candidate_first_local_control_target(section, candidate, &target)) {
        if (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
            (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U)) {
          cursor = target;
          continue;
        }
        if (work_count >= (uint8_t)(sizeof(worklist) / sizeof(worklist[0]))) return 0;
        worklist[work_count++] = target;
      }
      if (metadata->flow_kind == M68K_SIM_FLOW_RETURN) break;
      if (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
          (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U) ||
          metadata->flow_kind == M68K_SIM_FLOW_TRAP) {
        break;
      }
      if (candidate->byte_count > section->size - cursor) break;
      cursor += candidate->byte_count;
    }
  }
  return visited_any != 0U;
}

static int source_quality_palette_call_preserves_address_registers(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  uint32_t target_offset = 0U;
  if (section == NULL || accepted_start == NULL || candidate == NULL || instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || metadata->flow_kind != M68K_SIM_FLOW_CALL) return 0;
  return source_quality_candidate_local_call_target(section, candidate, &target_offset) &&
    source_quality_local_callee_preserves_address_register_mask_with_depth(section, accepted_start, target_offset,
      0xFFU, 0U);
}

static int source_quality_has_structured_data_covering_offset(const M68kSourceAnalysisIR *source_analysis,
    uint32_t section_index, uint32_t offset) {
  size_t index;
  if (source_analysis == NULL) return 0;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis->structured_data_items[index];
    if (!item->has_section_index || item->section_index != section_index || item->size == 0U ||
        item->offset > offset) {
      continue;
    }
    if (offset - item->offset < item->size) return 1;
  }
  return 0;
}

static uint32_t source_quality_palette_source_span(const M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset, uint32_t max_size) {
  uint32_t cursor;
  if (source_analysis == NULL || section == NULL || accepted_bytes == NULL || offset >= section->size ||
      max_size < 2U || section->section_index > UINT32_MAX) {
    return 0U;
  }
  cursor = offset;
  while (cursor + 2U <= section->size && cursor - offset < max_size) {
    if (cursor != offset &&
        source_quality_has_structured_data_covering_offset(source_analysis, (uint32_t)section->section_index,
          cursor)) {
      break;
    }
    if (source_quality_accepted_range_has_code_byte(accepted_bytes, section->size, cursor, 2U)) break;
    cursor += 2U;
  }
  return cursor - offset;
}

static int append_palette_upload_structured_data_item(M68kSourceAnalysisIR *source_analysis,
    uint32_t source_section_index, uint32_t source_offset, uint32_t size, uint32_t consumer_section_index,
    uint32_t consumer_offset) {
  M68kAnalysisStructuredDataItem item;
  if (source_analysis == NULL || size < 4U ||
      source_quality_has_structured_data_item(source_analysis, source_section_index, source_offset, size,
        M68K_ANALYSIS_STRUCTURED_DATA_WORDS, M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_UNKNOWN)) {
    return 0;
  }
  memset(&item, 0, sizeof(item));
  item.has_section_index = 1U;
  item.section_index = source_section_index;
  item.offset = source_offset;
  item.size = size;
  item.kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  item.has_consumer = 1U;
  item.consumer_section = consumer_section_index;
  item.consumer_offset = consumer_offset;
  m68k_analysis_structured_data_item_set_semantic_role_flags(&item, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE);
  return m68k_ir_source_analysis_append_structured_data_item(source_analysis, &item);
}

static int source_quality_maybe_classify_palette_upload(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kDecodeSectionIR *section, uint8_t *const *accepted_bytes,
    const M68kSourceQualityAudioPointerState *data_state,
    const M68kSourceQualityPaletteHardwareRangeState *hardware_state, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  const M68kSourceQualityAudioPointerSource *source_value;
  const M68kSourceQualityPaletteHardwareRangePointer *dest_value;
  uint8_t source_reg = 0U;
  uint8_t dest_reg = 0U;
  uint32_t available_register_bytes;
  uint32_t size;
  if (source_analysis == NULL || decode == NULL || section == NULL || accepted_bytes == NULL ||
      data_state == NULL || hardware_state == NULL || candidate == NULL || instruction == NULL ||
      instruction->size_suffix != 'w' || instruction->operand_count != 2U ||
      !source_quality_operand_is_address_postincrement(&instruction->operands[0], &source_reg) ||
      !source_quality_operand_is_address_postincrement(&instruction->operands[1], &dest_reg)) {
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
      dest_value->range->symbol_id != AMIGA_OS_SYMBOL_ID_COLOR ||
      source_value->target_section_index >= decode->section_count ||
      accepted_bytes[source_value->target_section_index] == NULL ||
      source_value->target_offset >= decode->sections[source_value->target_section_index].size ||
      dest_value->offset >= M68K_SOURCE_QUALITY_AMIGA_COLOR_REGISTER_BYTES ||
      section->section_index > UINT32_MAX) {
    return 0;
  }
  available_register_bytes = M68K_SOURCE_QUALITY_AMIGA_COLOR_REGISTER_BYTES - dest_value->offset;
  size = source_quality_palette_source_span(source_analysis, &decode->sections[source_value->target_section_index],
    accepted_bytes[source_value->target_section_index], source_value->target_offset, available_register_bytes);
  if (size < 4U || size != available_register_bytes) return 0;
  return append_palette_upload_structured_data_item(source_analysis, source_value->target_section_index,
    source_value->target_offset, size, (uint32_t)section->section_index, candidate->offset);
}

static int append_palette_upload_structured_data_items_for_section(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint8_t *const *accepted_bytes) {
  M68kSourceQualityAudioPointerState data_state;
  M68kSourceQualityPaletteHardwareRangeState hardware_state;
  M68kSourceQualityPalettePointerSave pointer_save;
  size_t candidate_index;
  if (source_analysis == NULL || decode == NULL || section == NULL || accepted_start == NULL ||
      accepted_bytes == NULL) {
    return 0;
  }
  source_quality_audio_pointer_state_clear_all(&data_state);
  source_quality_palette_hardware_range_state_clear_all(&hardware_state);
  memset(&pointer_save, 0, sizeof(pointer_save));
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    source_quality_palette_pointer_save_before_instruction(&pointer_save, &data_state, &hardware_state,
      &instruction);
    if (source_quality_maybe_classify_palette_upload(source_analysis, decode, section, accepted_bytes,
        &data_state, &hardware_state, candidate, &instruction) != 0) {
      return -1;
    }
    if (!source_quality_palette_call_preserves_address_registers(section, accepted_start, candidate,
        &instruction)) {
      source_quality_palette_data_pointer_state_update_after_instruction(&data_state, source_analysis, decode, facts,
        section, candidate, &instruction);
      source_quality_palette_hardware_range_state_update_after_instruction(&hardware_state, candidate, &instruction);
    }
    source_quality_palette_pointer_save_after_instruction(&pointer_save, &data_state, &hardware_state,
      &instruction);
  }
  return 0;
}

static int append_palette_upload_structured_data_items(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    if (section == NULL) continue;
    if (append_palette_upload_structured_data_items_for_section(source_analysis, decode, facts, section,
        accepted_start[decode_index], accepted_bytes) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_audio_source_platform_semantic_uses_for_section(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeIR *decode, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    uint8_t *const *accepted_bytes) {
  M68kSourceQualityAudioLengthSource length_sources[8];
  M68kSourceQualityAudioPeriodSource period_sources[8];
  M68kSourceQualityAudioPointerState pointer_state;
  size_t candidate_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  source_quality_audio_length_sources_clear(length_sources);
  source_quality_audio_period_sources_clear(period_sources);
  source_quality_audio_pointer_state_clear_all(&pointer_state);
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    uint8_t source_reg = 0U;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    if (source_quality_audio_length_write_source_reg(candidate, &instruction, &source_reg) &&
        source_reg < 8U && length_sources[source_reg].known) {
      M68kPlatformSemanticUseIR use;
      char note[128];
      if (!format_source_quality_audio_length_source_note(&length_sources[source_reg], note, sizeof(note))) return -1;
      memset(&use, 0, sizeof(use));
      use.kind = M68K_PLATFORM_SEMANTIC_USE_AUDIO_REGISTER;
      use.offset = candidate->offset;
      use.size = candidate->byte_count;
      use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
      use.note_text = note;
      if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
    }
    if (source_quality_audio_period_write_source_reg(candidate, &instruction, &source_reg) &&
        source_reg < 8U && period_sources[source_reg].known) {
      M68kPlatformSemanticUseIR use;
      memset(&use, 0, sizeof(use));
      use.kind = M68K_PLATFORM_SEMANTIC_USE_AUDIO_PERIOD_SOURCE;
      use.offset = candidate->offset;
      use.size = candidate->byte_count;
      use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
      use.has_target = 1U;
      use.target_section_index = period_sources[source_reg].target_section_index;
      use.target_offset = period_sources[source_reg].target_offset;
      use.note_text = period_sources[source_reg].transformed ? "transformed" : NULL;
      if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
    }
    if (source_quality_audio_pointer_write_source_reg(candidate, &instruction, &source_reg) &&
        source_reg < 8U && pointer_state.addr_regs[source_reg].known && decode != NULL && accepted_bytes != NULL) {
      const M68kSourceQualityAudioPointerSource *source = &pointer_state.addr_regs[source_reg];
      if (source->target_section_index < decode->section_count &&
          source->target_offset < decode->sections[source->target_section_index].size &&
          !source_quality_accepted_range_has_code_byte(accepted_bytes[source->target_section_index],
            decode->sections[source->target_section_index].size, source->target_offset, 1U)) {
        M68kPlatformSemanticUseIR use;
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_AUDIO_POINTER_SOURCE;
        use.offset = candidate->offset;
        use.size = candidate->byte_count;
        use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
        use.has_target = 1U;
        use.target_section_index = source->target_section_index;
        use.target_offset = source->target_offset;
        if (source->dynamic_offset_known && source->dynamic_offset_section_index < decode->section_count &&
            source->dynamic_offset_offset < decode->sections[source->dynamic_offset_section_index].size &&
            !source_quality_accepted_range_has_code_byte(accepted_bytes[source->dynamic_offset_section_index],
              decode->sections[source->dynamic_offset_section_index].size, source->dynamic_offset_offset, 2U)) {
          use.has_secondary_target = 1U;
          use.secondary_target_section_index = source->dynamic_offset_section_index;
          use.secondary_target_offset = source->dynamic_offset_offset;
        }
        use.note_text = source->exact ? NULL : "dynamic_offset";
        if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
      }
    }
    source_quality_audio_length_sources_update_after_instruction(length_sources, &instruction);
    source_quality_audio_period_sources_update_after_instruction(period_sources, candidate, &instruction);
    source_quality_audio_pointer_state_update_after_instruction(&pointer_state, section_analysis, section, candidate,
      &instruction);
  }
  return 0;
}

static int append_audio_source_platform_semantic_uses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, uint8_t *const *accepted_bytes) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    if (section == NULL) continue;
    if (append_audio_source_platform_semantic_uses_for_section(section_analysis, decode, section,
        accepted_start[decode_index], accepted_bytes) != 0) {
      return -1;
    }
  }
  return 0;
}

typedef struct SourceQualityHardwareBaseState {
  uint32_t address_base_known;
  uint16_t address_base_id[8];
} SourceQualityHardwareBaseState;

static void source_quality_hardware_base_state_set(SourceQualityHardwareBaseState *state, uint8_t reg_index,
    uint16_t base_id) {
  if (state == NULL || reg_index >= 8U || base_id == AMIGA_OS_HARDWARE_BASE_ID_NONE) return;
  m68k_bitset_u32_set(&state->address_base_known, reg_index);
  state->address_base_id[reg_index] = base_id;
}

static void source_quality_hardware_base_state_clear(SourceQualityHardwareBaseState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->address_base_known, reg_index);
  state->address_base_id[reg_index] = AMIGA_OS_HARDWARE_BASE_ID_NONE;
}

static void source_quality_hardware_base_state_clear_all(SourceQualityHardwareBaseState *state) {
  if (state == NULL) return;
  state->address_base_known = 0U;
  memset(state->address_base_id, 0, sizeof(state->address_base_id));
}

static void source_quality_hardware_base_state_apply_policy_register_seeds(SourceQualityHardwareBaseState *state,
    const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  uint16_t index;
  if (state == NULL || policy == NULL || section_index > UINT32_MAX) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    uint16_t base_id;
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if ((seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE &&
         seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR) ||
        seed->reg_kind != M68K_ANALYSIS_REGISTER_ADDRESS || seed->reg_index >= 8U) {
      continue;
    }
    base_id = amiga_os_hardware_base_id(seed->name);
    if (base_id == AMIGA_OS_HARDWARE_BASE_ID_NONE) continue;
    source_quality_hardware_base_state_set(state, seed->reg_index, base_id);
  }
}

static void source_quality_hardware_base_state_apply_inferred_register_seeds(SourceQualityHardwareBaseState *state,
    const M68kSourceQualityHardwareBaseSeed *seeds, size_t seed_count, size_t section_index, uint32_t offset) {
  size_t index;
  if (state == NULL || seeds == NULL || section_index > UINT32_MAX) return;
  for (index = 0U; index < seed_count; ++index) {
    const M68kSourceQualityHardwareBaseSeed *seed = &seeds[index];
    if (seed->conflicted != 0U || seed->section_index != section_index || seed->offset != offset ||
        seed->reg_index >= 8U || seed->hardware_base_id == AMIGA_OS_HARDWARE_BASE_ID_NONE) {
      continue;
    }
    source_quality_hardware_base_state_set(state, seed->reg_index, seed->hardware_base_id);
  }
}

static int source_quality_operand_hardware_base_id(const SourceQualityHardwareBaseState *state,
    const M68kOperandIR *operand, uint16_t *out_base_id) {
  uint8_t reg = 0U;
  uint32_t value = 0U;
  uint16_t base_id = AMIGA_OS_HARDWARE_BASE_ID_NONE;
  if (out_base_id != NULL) *out_base_id = AMIGA_OS_HARDWARE_BASE_ID_NONE;
  if (operand == NULL) return 0;
  if (source_quality_operand_address_register_index(operand, &reg) &&
      state != NULL && reg < 8U && m68k_bitset_u32_has(state->address_base_known, reg)) {
    if (out_base_id != NULL) *out_base_id = state->address_base_id[reg];
    return state->address_base_id[reg] != AMIGA_OS_HARDWARE_BASE_ID_NONE;
  }
  if (m68k_ir_operand_immediate_value(operand, &value) ||
      source_quality_operand_absolute_offset(operand, &value)) {
    base_id = amiga_os_find_hardware_base_id_by_address(value);
    if (base_id == AMIGA_OS_HARDWARE_BASE_ID_NONE) return 0;
    if (out_base_id != NULL) *out_base_id = base_id;
    return 1;
  }
  return 0;
}

static void source_quality_hardware_base_state_update_after_instruction(SourceQualityHardwareBaseState *state,
    const M68kInstructionIR *instruction) {
  uint8_t dest_reg = 0U;
  uint16_t source_base_id = AMIGA_OS_HARDWARE_BASE_ID_NONE;
  if (state == NULL || instruction == NULL) return;
  if (platform_instruction_has_terminal_state_flow(instruction)) {
    source_quality_hardware_base_state_clear_all(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U && instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
        if (source_quality_reglist_contains_register(&instruction->operands[1], 2U, dest_reg))
          source_quality_hardware_base_state_clear(state, dest_reg);
      }
    }
    return;
  }
  if (instruction->operand_count < 2U) return;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA) {
    return;
  }
  if (!source_quality_operand_address_register_index(&instruction->operands[instruction->operand_count - 1U],
      &dest_reg)) {
    return;
  }
  if (source_quality_operand_hardware_base_id(state, &instruction->operands[0], &source_base_id))
    source_quality_hardware_base_state_set(state, dest_reg, source_base_id);
  else
    source_quality_hardware_base_state_clear(state, dest_reg);
}

static int append_hardware_base_platform_address_uses_for_section(
    M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kAnalysisPolicy *policy, const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds,
    size_t hardware_base_seed_count) {
  SourceQualityHardwareBaseState state;
  size_t candidate_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  memset(&state, 0, sizeof(state));
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    uint8_t operand_index;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    source_quality_hardware_base_state_apply_policy_register_seeds(&state, policy, section->section_index,
      candidate->offset);
    source_quality_hardware_base_state_apply_inferred_register_seeds(&state, hardware_base_seeds,
      hardware_base_seed_count, section->section_index, candidate->offset);
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) {
      source_quality_hardware_base_state_update_after_instruction(&state, &instruction);
      continue;
    }
    for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
      uint8_t access_kind = metadata->operand_access_kinds[operand_index];
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      uint16_t base_id;
      uint32_t base_address = 0U;
      const char *base_symbol;
      const char *symbol_name;
      char symbol_buf[96];
      M68kPlatformAddressUseIR use;
      if (access_kind != M68K_SIM_ACCESS_MEMORY_WRITE &&
          access_kind != M68K_SIM_ACCESS_MEMORY_READ &&
          access_kind != M68K_SIM_ACCESS_COMPUTE_ADDRESS) {
        continue;
      }
      if (!source_quality_operand_address_displacement(&instruction.operands[operand_index], &base_reg,
          &displacement) ||
          base_reg >= 8U || displacement < 0 ||
          !m68k_bitset_u32_has(state.address_base_known, base_reg)) {
        continue;
      }
      base_id = state.address_base_id[base_reg];
      base_symbol = amiga_os_hardware_base_symbol(base_id);
      if (base_symbol == NULL ||
          !amiga_os_find_hardware_base_address(base_symbol, &base_address)) {
        continue;
      }
      symbol_name = platform_address_use_symbol_from_hardware_base_offset(base_id,
        (uint32_t)(uint16_t)displacement, symbol_buf, sizeof(symbol_buf));
      if (symbol_name == NULL || symbol_name[0] == '\0') continue;
      memset(&use, 0, sizeof(use));
      use.symbol_name = (char *)symbol_name;
      use.offset = candidate->offset;
      use.operand_index = operand_index;
      use.address = base_address + (uint32_t)(uint16_t)displacement;
      use.effective_address = use.address;
      use.access_width = source_quality_byte_width_for_instruction_size(&instruction);
      use.access_kind = access_kind;
      use.use_shape = M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS;
      use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
      if (m68k_ir_section_analysis_append_platform_address_use(section_analysis, &use) != 0) return -1;
    }
    source_quality_hardware_base_state_update_after_instruction(&state, &instruction);
  }
  return 0;
}

static int append_hardware_base_platform_address_uses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, const M68kAnalysisPolicy *policy,
    const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds, size_t hardware_base_seed_count) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    if (section == NULL || section->section_index >= decode->section_count) continue;
    if (append_hardware_base_platform_address_uses_for_section(section_analysis, section,
        accepted_start[decode_index], policy, hardware_base_seeds, hardware_base_seed_count) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_hardware_base_note_platform_semantic_uses_for_section(
    M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kAnalysisPolicy *policy, const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds,
    size_t hardware_base_seed_count) {
  SourceQualityHardwareBaseState state;
  size_t candidate_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  memset(&state, 0, sizeof(state));
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    uint8_t operand_index;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    source_quality_hardware_base_state_apply_policy_register_seeds(&state, policy, section->section_index,
      candidate->offset);
    source_quality_hardware_base_state_apply_inferred_register_seeds(&state, hardware_base_seeds,
      hardware_base_seed_count, section->section_index, candidate->offset);
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) {
      source_quality_hardware_base_state_update_after_instruction(&state, &instruction);
      continue;
    }
    for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
      uint8_t access_kind = metadata->operand_access_kinds[operand_index];
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      const AmigaOsHardwareRegisterInfo *hardware_register;
      const AmigaOsHardwareRegisterFieldInfo *hardware_field;
      const AmigaOsHardwareRegisterRangeInfo *hardware_range;
      M68kPlatformSemanticUseIR use;
      uint32_t value = 0U;
      uint8_t source_index;
      int has_immediate_source = 0;
      char note[160];
      if (access_kind != M68K_SIM_ACCESS_MEMORY_WRITE && access_kind != M68K_SIM_ACCESS_MEMORY_READ) continue;
      if (!source_quality_operand_address_displacement(&instruction.operands[operand_index], &base_reg,
          &displacement) ||
          base_reg >= 8U || displacement < 0 ||
          !m68k_bitset_u32_has(state.address_base_known, base_reg)) {
        continue;
      }
      hardware_field = amiga_os_find_hardware_register_field_by_base_id_offset(state.address_base_id[base_reg],
        (uint32_t)(uint16_t)displacement);
      hardware_register = amiga_os_find_hardware_register_by_base_id_offset(state.address_base_id[base_reg],
        (uint32_t)(uint16_t)displacement);
      hardware_range = amiga_os_find_hardware_register_range_by_base_id_offset(state.address_base_id[base_reg],
        (uint32_t)(uint16_t)displacement);
      if (hardware_field == NULL && hardware_register == NULL && hardware_range == NULL) continue;
      for (source_index = 0U; source_index < instruction.operand_count; ++source_index) {
        if (source_index == operand_index) continue;
        if (m68k_ir_operand_immediate_value(&instruction.operands[source_index], &value)) {
          has_immediate_source = 1;
          break;
        }
      }
      if (has_immediate_source) {
        if (access_kind != M68K_SIM_ACCESS_MEMORY_WRITE) continue;
        value = source_quality_immediate_domain_value_for_instruction_size(&instruction, value);
      }
      if (has_immediate_source &&
          format_source_quality_amiga_hardware_value_note(hardware_register, value, note, sizeof(note))) {
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_HARDWARE_VALUE;
      } else if (has_immediate_source &&
          format_source_quality_amiga_disk_dma_note(hardware_register, value, note, sizeof(note))) {
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_DISK_DMA;
      } else if (format_source_quality_amiga_audio_register_note(hardware_field, value, has_immediate_source, note,
          sizeof(note))) {
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_AUDIO_REGISTER;
      } else if (!has_immediate_source &&
          (format_source_quality_amiga_hardware_register_access_note(hardware_register, access_kind, note,
             sizeof(note)) ||
           format_source_quality_amiga_hardware_range_access_note(hardware_range, (uint32_t)(uint16_t)displacement,
             access_kind, source_quality_byte_width_for_instruction_size(&instruction), note, sizeof(note)))) {
        memset(&use, 0, sizeof(use));
        use.kind = M68K_PLATFORM_SEMANTIC_USE_HARDWARE_ACCESS;
      } else {
        continue;
      }
      use.offset = candidate->offset;
      use.size = candidate->byte_count;
      use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
      use.note_text = note;
      if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
    }
    source_quality_hardware_base_state_update_after_instruction(&state, &instruction);
  }
  return 0;
}

static int append_hardware_base_note_platform_semantic_uses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, const M68kAnalysisPolicy *policy,
    const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds, size_t hardware_base_seed_count) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, NULL);
    if (section == NULL || section->section_index >= decode->section_count) continue;
    if (append_hardware_base_note_platform_semantic_uses_for_section(section_analysis, section,
        accepted_start[section->section_index], policy, hardware_base_seeds, hardware_base_seed_count) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_runtime_sink_pointer_hardware_base_semantic_uses_for_section(
    M68kSectionAnalysisIR *section_analysis, const M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kAnalysisPolicy *policy,
    const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds, size_t hardware_base_seed_count) {
  SourceQualityHardwareBaseState state;
  size_t candidate_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  memset(&state, 0, sizeof(state));
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    uint8_t operand_index;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    source_quality_hardware_base_state_apply_policy_register_seeds(&state, policy, section->section_index,
      candidate->offset);
    source_quality_hardware_base_state_apply_inferred_register_seeds(&state, hardware_base_seeds,
      hardware_base_seed_count, section->section_index, candidate->offset);
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) {
      source_quality_hardware_base_state_update_after_instruction(&state, &instruction);
      continue;
    }
    for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      uint32_t sink_address;
      const AmigaOsHardwareRegisterInfo *hardware_register;
      const M68kRuntimeAddressRefIR *runtime_ref;
      M68kPlatformSemanticUseIR use;
      char note[160];
      char operand_expr[M68K_IR_SYMBOL_NAME_SIZE];
      if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_MEMORY_WRITE) continue;
      if (instruction.size_suffix != 'l') continue;
      if (!source_quality_operand_address_displacement(&instruction.operands[operand_index], &base_reg,
          &displacement) ||
          base_reg >= 8U ||
          !m68k_bitset_u32_has(state.address_base_known, base_reg) ||
          displacement < 0) {
        continue;
      }
      hardware_register = source_quality_runtime_sink_register_for_base_id_offset(state.address_base_id[base_reg],
        (uint32_t)(uint16_t)displacement);
      if (hardware_register == NULL) continue;
      sink_address = hardware_register->base_address + (uint32_t)(uint16_t)displacement;
      runtime_ref = source_quality_runtime_sink_ref_for_offset(section_analysis, candidate->offset, sink_address);
      source_quality_runtime_sink_note_text(section_analysis, hardware_register, runtime_ref, candidate->offset, note,
        sizeof(note));
      memset(&use, 0, sizeof(use));
      use.kind = M68K_PLATFORM_SEMANTIC_USE_RUNTIME_SINK_POINTER;
      use.offset = candidate->offset;
      use.size = candidate->byte_count;
      use.role_flags = platform_facts_v2_runtime_address_sink_data_class_flags(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
        sink_address);
      use.confidence = runtime_ref != NULL ? runtime_ref->confidence : M68K_FACT_CONFIDENCE_TOOL_INFERRED;
      use.note_text = note;
      source_quality_runtime_sink_set_operand_fact(&use, source_analysis, section_analysis, hardware_register,
        runtime_ref, candidate, &instruction, operand_expr, sizeof(operand_expr));
      if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
      if (use.has_operand_expr &&
          append_expected_runtime_sink_operand_symbol_access_at(section_analysis, candidate->offset,
            use.operand_index, use.confidence, use.operand_expr) != 0) {
        return -1;
      }
    }
    source_quality_hardware_base_state_update_after_instruction(&state, &instruction);
  }
  return 0;
}

static int append_runtime_sink_pointer_hardware_base_semantic_uses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, const M68kAnalysisPolicy *policy,
    const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds, size_t hardware_base_seed_count) {
  size_t section_index;
  if (source_analysis == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, NULL);
    if (section == NULL || section->section_index >= decode->section_count) continue;
    if (append_runtime_sink_pointer_hardware_base_semantic_uses_for_section(section_analysis, source_analysis, section,
        accepted_start[section->section_index], policy, hardware_base_seeds, hardware_base_seed_count) != 0) {
      return -1;
    }
  }
  return 0;
}

static int source_quality_reglist_contains_register(const M68kOperandIR *operand, uint8_t reg_kind,
    uint8_t reg_index) {
  uint32_t mask;
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_REGLIST || reg_index >= 8U) return 0;
  mask = operand->value.value;
  if (reg_kind == 1U) return (mask & (1UL << reg_index)) != 0U;
  if (reg_kind == 2U) return (mask & (1UL << (8U + reg_index))) != 0U;
  return 0;
}

static int source_quality_instruction_loads_immediate_to_register(const M68kInstructionIR *instruction,
    uint8_t *out_reg_kind, uint8_t *out_reg_index, uint32_t *out_value) {
  uint32_t value = 0U;
  uint8_t reg = 0U;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (out_value != NULL) *out_value = 0U;
  if (instruction == NULL || instruction->operand_count != 2U ||
      !m68k_ir_operand_immediate_value(&instruction->operands[0], &value)) {
    return 0;
  }
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEQ) {
    return 0;
  }
  if (source_quality_operand_data_register_index(&instruction->operands[1], &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 1U;
  } else if (source_quality_operand_address_register_index(&instruction->operands[1], &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 2U;
  } else {
    return 0;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) value = (uint32_t)(int32_t)(int8_t)(value & 0xFFU);
  else if (instruction->size_suffix == 'b') value = (uint32_t)(int32_t)(int8_t)(value & 0xFFU);
  else if (instruction->size_suffix == 'w') value = (uint32_t)(int32_t)(int16_t)(value & 0xFFFFU);
  if (out_reg_index != NULL) *out_reg_index = reg;
  if (out_value != NULL) *out_value = value;
  return 1;
}

static uint32_t source_quality_immediate_domain_value_for_instruction_size(const M68kInstructionIR *instruction,
    uint32_t value) {
  if (instruction == NULL) return value;
  if (instruction->size_suffix == 'b') return value & 0xFFU;
  if (instruction->size_suffix == 'w') return value & 0xFFFFU;
  return value;
}

static int source_quality_symbol_name_is_plain_local(const char *name) {
  size_t index;
  if (name == NULL || name[0] == '\0') return 0;
  for (index = 0U; name[index] != '\0'; ++index) {
    const char ch = name[index];
    if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || ch == '_') continue;
    if (index != 0U && ch >= '0' && ch <= '9') continue;
    return 0;
  }
  return 1;
}

static uint8_t source_quality_platform_symbol_expr_expected_access_kind(const char *symbol_expr) {
  int32_t value = 0;
  if (source_quality_symbol_name_is_plain_local(symbol_expr) &&
      amiga_os_find_symbol_include(symbol_expr) == NULL &&
      amiga_os_find_constant_value(symbol_expr, &value)) {
    return M68K_EXPECTED_SYMBOL_ACCESS_EQUATE;
  }
  return M68K_EXPECTED_SYMBOL_ACCESS_OPERAND;
}

static int append_expected_platform_symbol_expr_accesses(M68kSectionAnalysisIR *section_analysis,
    const char *symbol_expr, const char *producer, uint32_t offset, uint32_t operand_index, uint8_t confidence) {
  size_t index = 0U;
  if (section_analysis == NULL || symbol_expr == NULL || symbol_expr[0] == '\0') return 0;
  while (symbol_expr[index] != '\0') {
    char token[M68K_IR_SYMBOL_NAME_SIZE];
    size_t token_len = 0U;
    int32_t constant_value = 0;
    while (symbol_expr[index] != '\0' && !source_quality_symbol_token_char(symbol_expr[index], 1)) ++index;
    while (symbol_expr[index] != '\0' && source_quality_symbol_token_char(symbol_expr[index], token_len == 0U)) {
      if (token_len + 1U < sizeof(token)) token[token_len++] = symbol_expr[index];
      ++index;
    }
    if (token_len == 0U || token_len >= sizeof(token)) continue;
    token[token_len] = '\0';
    if (amiga_os_find_symbol_include(token) == NULL &&
        !amiga_os_find_constant_value(token, &constant_value)) {
      continue;
    }
    {
      M68kExpectedSymbolAccessIR access;
      memset(&access, 0, sizeof(access));
      access.symbol_name = token;
      access.producer = (char *)producer;
      access.offset = offset;
      access.operand_index = operand_index;
      access.access_kind = source_quality_platform_symbol_expr_expected_access_kind(token);
      access.confidence = confidence;
      if (m68k_ir_section_analysis_append_expected_symbol_access(section_analysis, &access) != 0) return -1;
    }
  }
  return 0;
}

static int source_quality_instruction_writes_register(const M68kInstructionIR *instruction, uint8_t reg_kind,
    uint8_t reg_index) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint8_t reg = 0U;
  if (instruction == NULL || reg_kind == 0U || reg_index >= 8U) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t access_kind = metadata->operand_access_kinds[operand_index];
    if (access_kind == M68K_SIM_ACCESS_REGISTER_LIST_WRITE &&
        source_quality_reglist_contains_register(operand, reg_kind, reg_index)) {
      return 1;
    }
    if (access_kind != M68K_SIM_ACCESS_REGISTER_WRITE) continue;
    if (reg_kind == 1U && source_quality_operand_data_register_index(operand, &reg) && reg == reg_index) return 1;
    if (reg_kind == 2U && source_quality_operand_address_register_index(operand, &reg) && reg == reg_index)
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

static int source_quality_runtime_operand_expr_use_exists_at(const M68kSectionAnalysisIR *section,
  uint32_t offset, uint32_t operand_index, uint32_t runtime_address);

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
      if (observation != NULL && observation->has_address &&
          source_quality_runtime_operand_expr_use_exists_at(section_analysis, observation->offset,
            observation->operand_index, observation->address)) {
        continue;
      }
      memset(&access, 0, sizeof(access));
      access.symbol_name = section_storage_origin != NULL ? section_storage_origin->symbol_name :
        observation->symbol_name;
      access.producer = section_storage_origin != NULL ? "section_storage_address_observation" :
        "absolute_address_observation";
      access.offset = observation->offset;
      access.operand_index = observation->operand_index;
      access.access_kind = section_storage_origin != NULL ? M68K_EXPECTED_SYMBOL_ACCESS_OPERAND :
        M68K_EXPECTED_SYMBOL_ACCESS_EQUATE;
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

static const M68kAddressObservationIR *platform_address_use_matching_observation(
    const M68kSectionAnalysisIR *section_analysis, const M68kPlatformAddressUseIR *use) {
  size_t index;
  if (section_analysis == NULL || use == NULL) return NULL;
  for (index = 0U; index < section_analysis->address_observation_count; ++index) {
    const M68kAddressObservationIR *observation = &section_analysis->address_observations[index];
    if (observation->offset != use->offset ||
        observation->operand_index != use->operand_index ||
        !observation->has_address ||
        observation->address != use->address) {
      continue;
    }
    return observation;
  }
  return NULL;
}

static int platform_address_use_operand_matches_accepted_instruction(const M68kPlatformAddressUseIR *use,
    const M68kInstructionIR *instruction) {
  uint32_t value = 0U;
  if (use == NULL || instruction == NULL || use->operand_index >= instruction->operand_count) return 0;
  if (source_quality_operand_absolute_offset(&instruction->operands[use->operand_index], &value)) {
    return value == use->address;
  }
  if (use->use_shape == M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS) {
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    const AmigaOsHardwareRegisterFieldInfo *hardware_field;
    const AmigaOsHardwareRegisterInfo *hardware_register;
    const AmigaOsHardwareRegisterRangeInfo *hardware_range;
    uint16_t base_id = AMIGA_OS_HARDWARE_BASE_ID_NONE;
    uint32_t register_offset = 0U;
    char symbol_buf[96];
    const char *symbol_name;
    if (!source_quality_operand_address_displacement(&instruction->operands[use->operand_index], &base_reg,
        &displacement) ||
        displacement < 0) {
      return 0;
    }
    hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(use->address);
    if (hardware_field != NULL) {
      base_id = hardware_field->base_id;
      register_offset = hardware_field->register_offset + hardware_field->field_offset;
    } else {
      hardware_register = amiga_os_find_hardware_register_by_cpu_address(use->address);
      if (hardware_register != NULL) {
        base_id = hardware_register->base_id;
        register_offset = hardware_register->offset;
      } else {
        hardware_range = amiga_os_find_hardware_register_range_by_cpu_address(use->address);
        if (hardware_range == NULL) return 0;
        base_id = hardware_range->base_id;
        register_offset = use->address - hardware_range->base_address;
      }
    }
    if ((uint32_t)(uint16_t)displacement != register_offset) return 0;
    symbol_name = platform_address_use_symbol_from_hardware_base_offset(base_id, register_offset, symbol_buf,
      sizeof(symbol_buf));
    return symbol_name != NULL && use->symbol_name != NULL && strcmp(symbol_name, use->symbol_name) == 0;
  }
  return 0;
}

static int append_expected_platform_symbol_operand_accesses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  if (decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    size_t use_index;
    if (section == NULL) continue;
    for (use_index = 0U; use_index < section_analysis->platform_address_use_count; ++use_index) {
      const M68kPlatformAddressUseIR *use = &section_analysis->platform_address_uses[use_index];
      const M68kDecodeCandidate *candidate;
      const M68kAddressObservationIR *observation;
      M68kInstructionIR instruction;
      M68kExpectedSymbolAccessIR access;
      if (use->use_shape != M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS ||
          use->symbol_name == NULL || use->symbol_name[0] == '\0' || use->operand_index == UINT32_MAX) {
        continue;
      }
      candidate = m68k_decode_ir_find_candidate_at_offset(section, use->offset);
      if (candidate == NULL ||
          !source_quality_candidate_is_accepted_start(section, accepted_start[decode_index], candidate) ||
          use->operand_index >= candidate->operand_count) {
        continue;
      }
      observation = platform_address_use_matching_observation(section_analysis, use);
      if (observation != NULL &&
          (observation->conflicted != 0U ||
           observation->conflict_state != M68K_ANALYSIS_CONFLICT_STATE_CLEAN)) {
        continue;
      }
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
          !platform_address_use_operand_matches_accepted_instruction(use, &instruction)) {
        continue;
      }
      memset(&access, 0, sizeof(access));
      access.symbol_name = use->symbol_name;
      access.producer = "platform_address_use";
      access.offset = use->offset;
      access.operand_index = use->operand_index;
      access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_OPERAND;
      access.confidence = use->confidence;
      if (m68k_ir_section_analysis_append_expected_symbol_access(section_analysis, &access) != 0) return -1;
    }
  }
  return 0;
}

static int source_quality_pc_relative_operand_crosses_runtime_org(
    const M68kSectionAnalysisIR *section_analysis, uint32_t source_offset, uint32_t target_offset) {
  size_t view_index;
  uint32_t low;
  uint32_t high;
  if (section_analysis == NULL || source_offset == target_offset) return 0;
  if (source_offset < target_offset) {
    low = source_offset;
    high = target_offset;
  } else {
    low = target_offset;
    high = source_offset;
  }
  for (view_index = 0U; view_index < section_analysis->runtime_view_count; ++view_index) {
    const M68kRuntimeViewIR *view = &section_analysis->runtime_views[view_index];
    if (view->materialized == 0U || view->runtime_address == view->storage_offset) continue;
    if (view->storage_offset > low && view->storage_offset <= high) return 1;
  }
  return 0;
}

static int source_quality_source_offset_has_distinct_runtime_address(
    const M68kSectionAnalysisIR *section_analysis, uint32_t source_offset, uint32_t *out_runtime_address) {
  size_t view_index;
  if (out_runtime_address != NULL) *out_runtime_address = 0U;
  if (section_analysis == NULL) return 0;
  for (view_index = 0U; view_index < section_analysis->runtime_view_count; ++view_index) {
    const M68kRuntimeViewIR *view = &section_analysis->runtime_views[view_index];
    uint32_t delta;
    uint32_t runtime_address;
    if (view->materialized == 0U || source_offset < view->storage_offset) continue;
    delta = source_offset - view->storage_offset;
    if (delta >= view->size || view->runtime_address > UINT32_MAX - delta) continue;
    runtime_address = view->runtime_address + delta;
    if (runtime_address == source_offset) continue;
    if (out_runtime_address != NULL) *out_runtime_address = runtime_address;
    return 1;
  }
  return 0;
}

static int source_quality_candidate_operand_is_pc_relative_storage_operand(
    const M68kDecodeCandidate *candidate, size_t operand_index) {
  if (candidate == NULL || operand_index >= candidate->operand_count) return 0;
  if (candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_LABEL) return 1;
  return candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_EA &&
    candidate->operands[operand_index].ea_mode == 7U &&
    candidate->operands[operand_index].ea_reg == 2U;
}

static int append_expected_pc_relative_storage_symbol_accesses_for_section(
    M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start) {
  size_t candidate_index;
  if (section_analysis == NULL || section == NULL) return -1;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    size_t target_index;
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      const M68kSymbolOriginIR *origin;
      M68kExpectedSymbolAccessIR access;
      if ((target->kind != M68K_DECODE_TARGET_DATA && !source_quality_target_is_control_symbol_access(target)) ||
          !target->has_section || !target->has_operand ||
          target->section_index != section->section_index ||
          target->section_index != section_analysis->section_index ||
          !source_quality_candidate_operand_is_pc_relative_storage_operand(candidate, target->operand_index) ||
          !source_quality_source_offset_has_distinct_runtime_address(section_analysis, target->offset, NULL) ||
          !source_quality_pc_relative_operand_crosses_runtime_org(section_analysis, candidate->offset,
            target->offset)) {
        continue;
      }
      origin = source_quality_symbol_origin_at(section_analysis, target->offset);
      if (origin == NULL) continue;
      memset(&access, 0, sizeof(access));
      access.symbol_name = origin->symbol_name;
      access.producer = "pc_relative_storage_operand";
      access.offset = candidate->offset;
      access.target_section_index = (uint32_t)section_analysis->section_index;
      access.target_offset = target->offset;
      access.operand_index = (uint32_t)target->operand_index;
      access.access_kind = source_quality_target_is_control_symbol_access(target) ?
        M68K_EXPECTED_SYMBOL_ACCESS_BRANCH_TARGET : M68K_EXPECTED_SYMBOL_ACCESS_OPERAND;
      access.confidence = origin->confidence;
      access.has_target = 1U;
      if (m68k_ir_section_analysis_append_expected_symbol_access(section_analysis, &access) != 0) return -1;
      memset(&access, 0, sizeof(access));
      access.symbol_name = origin->symbol_name;
      access.producer = "pc_relative_storage_label_statement";
      access.offset = target->offset;
      access.target_section_index = (uint32_t)section_analysis->section_index;
      access.target_offset = target->offset;
      access.operand_index = UINT32_MAX;
      access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_STORAGE_LABEL;
      access.confidence = origin->confidence;
      access.has_target = 1U;
      if (m68k_ir_section_analysis_append_expected_symbol_access(section_analysis, &access) != 0) return -1;
    }
  }
  return 0;
}

static int append_expected_pc_relative_storage_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
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
    if (append_expected_pc_relative_storage_symbol_accesses_for_section(section_analysis, section,
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

static int source_quality_runtime_ref_operand_contains_value(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kRuntimeAddressRefIR *ref) {
  const M68kDecodeCandidate *candidate;
  M68kInstructionIR instruction;
  uint32_t value = 0U;
  if (section == NULL || accepted_start == NULL || ref == NULL ||
      ref->operand_index == UINT32_MAX || ref->offset >= section->size || !accepted_start[ref->offset]) {
    return 0;
  }
  candidate = m68k_decode_ir_find_candidate_at_offset(section, ref->offset);
  if (candidate == NULL || ref->operand_index >= candidate->operand_count ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      ref->operand_index >= instruction.operand_count) {
    return 0;
  }
  if (!m68k_ir_operand_immediate_value(&instruction.operands[ref->operand_index], &value) &&
      !source_quality_operand_absolute_offset(&instruction.operands[ref->operand_index], &value)) {
    return 0;
  }
  return value == ref->runtime_address;
}

static int append_expected_runtime_ref_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  if (decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *decode_section = source_quality_decode_section_by_index(decode,
      (uint32_t)section->section_index, &decode_index);
    size_t ref_index;
    if (decode_section == NULL) continue;
    for (ref_index = 0U; ref_index < section->runtime_address_ref_count; ++ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[ref_index];
      M68kExpectedSymbolAccessIR access;
      char symbol[80];
      if (!ref->has_runtime_address || ref->has_target || ref->has_sink_address || ref->runtime_address == 0U ||
          ref->operand_index == UINT32_MAX || ref->data_class_flags != 0U ||
          (ref->data_class != NULL && ref->data_class[0] != '\0') ||
          !source_quality_runtime_ref_operand_contains_value(decode_section, accepted_start[decode_index], ref)) {
        continue;
      }
      platform_format_runtime_address_symbol_name("runtime_address", ref->runtime_address, "",
        symbol, sizeof(symbol));
      if (symbol[0] == '\0') continue;
      memset(&access, 0, sizeof(access));
      access.symbol_name = symbol;
      access.producer = "runtime_address_ref";
      access.offset = ref->offset;
      access.operand_index = ref->operand_index;
      access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_EQUATE;
      access.confidence = ref->confidence;
      if (m68k_ir_section_analysis_append_expected_symbol_access(section, &access) != 0) return -1;
    }
  }
  return 0;
}

static int source_quality_runtime_operand_expr_use_exists_at(const M68kSectionAnalysisIR *section,
    uint32_t offset, uint32_t operand_index, uint32_t runtime_address) {
  size_t index;
  if (section == NULL || operand_index == UINT32_MAX) return 0;
  for (index = 0U; index < section->platform_semantic_use_count; ++index) {
    const M68kPlatformSemanticUseIR *use = &section->platform_semantic_uses[index];
    if (use->offset == offset &&
        use->operand_index == operand_index &&
        use->has_operand_expr &&
        use->has_runtime_address &&
        use->runtime_address == runtime_address) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_runtime_ref_operand_expr_use_exists(const M68kSectionAnalysisIR *section,
    const M68kRuntimeAddressRefIR *ref) {
  if (ref == NULL) return 0;
  return source_quality_runtime_operand_expr_use_exists_at(section, ref->offset, ref->operand_index,
    ref->runtime_address);
}

static int append_expected_runtime_sink_operand_symbol_access_at(M68kSectionAnalysisIR *section,
    uint32_t offset, uint32_t operand_index, uint8_t confidence, const char *symbol) {
  M68kExpectedSymbolAccessIR access;
  if (section == NULL || symbol == NULL || symbol[0] == '\0' || operand_index == UINT32_MAX) return 0;
  memset(&access, 0, sizeof(access));
  access.symbol_name = (char *)symbol;
  access.producer = (char *)"runtime_sink_pointer_operand";
  access.offset = offset;
  access.operand_index = operand_index;
  access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_EQUATE;
  access.confidence = confidence;
  return m68k_ir_section_analysis_append_expected_symbol_access(section, &access);
}

static int source_quality_runtime_address_maps_to_materialized_source(const M68kSectionAnalysisIR *section,
    uint32_t runtime_address) {
  size_t view_index;
  if (section == NULL) return 0;
  for (view_index = 0U; view_index < section->runtime_view_count; ++view_index) {
    const M68kRuntimeViewIR *view = &section->runtime_views[view_index];
    uint32_t delta;
    if (!view->materialized || runtime_address < view->runtime_address) continue;
    delta = runtime_address - view->runtime_address;
    if (delta < view->size && view->storage_offset <= section->section_size &&
        delta < section->section_size - view->storage_offset) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_runtime_address_to_materialized_source(const M68kSourceAnalysisIR *source_analysis,
    uint32_t runtime_address, uint32_t *out_section_index, uint32_t *out_offset) {
  size_t section_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (source_analysis == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t view_index;
    if (section->section_index > UINT32_MAX) continue;
    for (view_index = 0U; view_index < section->runtime_view_count; ++view_index) {
      const M68kRuntimeViewIR *view = &section->runtime_views[view_index];
      uint32_t delta;
      if (!view->materialized || runtime_address < view->runtime_address) continue;
      delta = runtime_address - view->runtime_address;
      if (delta < view->size && view->storage_offset <= section->section_size &&
          delta < section->section_size - view->storage_offset) {
        if (out_section_index != NULL) *out_section_index = (uint32_t)section->section_index;
        if (out_offset != NULL) *out_offset = view->storage_offset + delta;
        return 1;
      }
    }
  }
  return 0;
}

static int source_quality_runtime_address_maps_to_any_materialized_source(const M68kSourceAnalysisIR *source_analysis,
    uint32_t runtime_address) {
  size_t section_index;
  if (source_analysis == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    if (source_quality_runtime_address_maps_to_materialized_source(&source_analysis->sections[section_index],
        runtime_address)) {
      return 1;
    }
  }
  return 0;
}

static int source_quality_operand_has_materialized_storage_observation(const M68kSectionAnalysisIR *section,
    uint32_t offset, uint32_t operand_index, uint32_t runtime_address) {
  size_t index;
  if (section == NULL || operand_index == UINT32_MAX || runtime_address == 0U) return 0;
  for (index = 0U; index < section->address_observation_count; ++index) {
    const M68kAddressObservationIR *observation = &section->address_observations[index];
    if (observation->offset == offset &&
        observation->operand_index == operand_index &&
        observation->has_address &&
        observation->address == runtime_address &&
        (observation->has_target ||
          observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_SECTION_STORAGE)) {
      return 1;
    }
  }
  return 0;
}

static const M68kRuntimeAddressRefIR *source_quality_runtime_ref_for_candidate_operand(
    const M68kSectionAnalysisIR *section, const M68kDecodeCandidate *candidate, size_t operand_index) {
  size_t ref_index;
  if (section == NULL || candidate == NULL) return NULL;
  for (ref_index = 0U; ref_index < section->runtime_address_ref_count; ++ref_index) {
    const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[ref_index];
    if (ref->offset == candidate->offset && ref->operand_index == operand_index) return ref;
  }
  return NULL;
}

static int source_quality_candidate_has_local_runtime_storage_ref(const M68kSectionAnalysisIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  size_t operand_index;
  if (section == NULL || candidate == NULL || instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kRuntimeAddressRefIR *ref = source_quality_runtime_ref_for_candidate_operand(section, candidate,
      operand_index);
    uint32_t runtime_address = 0U;
    if (ref != NULL && ref->has_target) return 1;
    if (source_quality_operand_absolute_offset(&instruction->operands[operand_index], &runtime_address) &&
        source_quality_runtime_address_maps_to_materialized_source(section, runtime_address)) {
      return 1;
    }
  }
  return 0;
}

static uint32_t source_quality_runtime_sink_role_flags_for_value(const M68kSectionAnalysisIR *section,
    const M68kDecodeSectionIR *decode_section, const uint8_t *accepted_start, uint32_t runtime_address,
    uint8_t *out_confidence) {
  size_t ref_index;
  if (out_confidence != NULL) *out_confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  if (section == NULL || decode_section == NULL || accepted_start == NULL || runtime_address == 0U) return 0U;
  for (ref_index = 0U; ref_index < section->runtime_address_ref_count; ++ref_index) {
    const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[ref_index];
    if (!ref->has_runtime_address || ref->runtime_address != runtime_address || ref->data_class_flags == 0U ||
        !source_quality_runtime_ref_operand_contains_value(decode_section, accepted_start, ref)) {
      continue;
    }
    if (out_confidence != NULL) *out_confidence = ref->confidence;
    return ref->data_class_flags;
  }
  return 0U;
}

static int append_runtime_sink_operand_expr_semantic_use_at(M68kSectionAnalysisIR *section,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeCandidate *candidate, uint32_t operand_index,
    uint32_t runtime_address, uint32_t role_flags, uint8_t confidence) {
  const char *role;
  M68kPlatformSemanticUseIR use;
  char symbol[M68K_IR_SYMBOL_NAME_SIZE];
  if (section == NULL || candidate == NULL || role_flags == 0U || operand_index == UINT32_MAX ||
      runtime_address == 0U ||
      source_quality_unique_symbol_origin_at_storage_offset(source_analysis, runtime_address, NULL, NULL) ||
      source_quality_runtime_address_maps_to_any_materialized_source(source_analysis, runtime_address) ||
      source_quality_runtime_address_maps_to_materialized_source(section, runtime_address) ||
      source_quality_operand_has_materialized_storage_observation(section, candidate->offset, operand_index,
        runtime_address) ||
      source_quality_runtime_operand_expr_use_exists_at(section, candidate->offset, operand_index,
        runtime_address)) {
    return 0;
  }
  role = m68k_analysis_structured_data_role_name_for_flags(role_flags);
  if (role == NULL || role[0] == '\0') return 0;
  platform_format_runtime_address_symbol_name(role, runtime_address, "", symbol, sizeof(symbol));
  if (symbol[0] == '\0') return 0;
  memset(&use, 0, sizeof(use));
  use.kind = M68K_PLATFORM_SEMANTIC_USE_RUNTIME_SINK_POINTER;
  use.offset = candidate->offset;
  use.size = candidate->byte_count;
  use.role_flags = role_flags;
  use.confidence = confidence;
  use.operand_index = operand_index;
  use.operand_expr = symbol;
  use.has_operand_expr = 1U;
  use.runtime_address = runtime_address;
  use.has_runtime_address = 1U;
  if (m68k_ir_section_analysis_append_platform_semantic_use(section, &use) != 0) return -1;
  if (append_expected_runtime_sink_operand_symbol_access_at(section, candidate->offset, operand_index, confidence,
      symbol) != 0)
    return -1;
  return 0;
}

static int append_runtime_sink_operand_expr_semantic_uses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  if (decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    const M68kDecodeSectionIR *decode_section;
    size_t decode_index = 0U;
    size_t ref_index;
    size_t candidate_index;
    decode_section = source_quality_decode_section_by_index(decode, (uint32_t)section->section_index, &decode_index);
    if (decode_section == NULL) continue;
    for (ref_index = 0U; ref_index < section->runtime_address_ref_count; ++ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[ref_index];
      const M68kDecodeCandidate *candidate;
      if (!ref->has_runtime_address || ref->runtime_address == 0U || ref->has_target ||
          ref->operand_index == UINT32_MAX || ref->data_class_flags == 0U ||
          source_quality_runtime_ref_operand_expr_use_exists(section, ref) ||
          !source_quality_runtime_ref_operand_contains_value(decode_section, accepted_start[decode_index], ref)) {
        continue;
      }
      candidate = m68k_decode_ir_find_candidate_at_offset(decode_section, ref->offset);
      if (!source_quality_candidate_is_accepted_start(decode_section, accepted_start[decode_index], candidate))
        continue;
      if (append_runtime_sink_operand_expr_semantic_use_at(section, source_analysis, candidate, ref->operand_index,
          ref->runtime_address, ref->data_class_flags, ref->confidence) != 0)
        return -1;
    }
    for (candidate_index = 0U; candidate_index < decode_section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &decode_section->candidates[candidate_index];
      M68kInstructionIR instruction;
      size_t operand_index;
      if (!source_quality_candidate_is_accepted_start(decode_section, accepted_start[decode_index], candidate))
        continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      if (!source_quality_candidate_has_local_runtime_storage_ref(section, candidate, &instruction)) continue;
      for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
        const M68kRuntimeAddressRefIR *operand_ref = source_quality_runtime_ref_for_candidate_operand(section,
          candidate, operand_index);
        uint32_t runtime_address = 0U;
        uint8_t confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
        uint32_t role_flags;
        if (operand_ref != NULL && operand_ref->has_target) continue;
        if (!m68k_ir_operand_immediate_value(&instruction.operands[operand_index], &runtime_address)) continue;
        role_flags = source_quality_runtime_sink_role_flags_for_value(section, decode_section,
          accepted_start[decode_index], runtime_address, &confidence);
        if (role_flags == 0U) continue;
        if (append_runtime_sink_operand_expr_semantic_use_at(section, source_analysis, candidate,
            (uint32_t)operand_index, runtime_address, role_flags, confidence) != 0)
          return -1;
      }
    }
  }
  return 0;
}

static int append_expected_copper_runtime_pointer_word_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  if (decode == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    const M68kDecodeSectionIR *decode_section = source_quality_decode_section_by_index(decode,
      (uint32_t)section->section_index, NULL);
    size_t ref_index;
    if (decode_section == NULL || decode_section->data == NULL) continue;
    for (ref_index = 0U; ref_index < section->runtime_address_ref_count; ++ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[ref_index];
      const AmigaOsHardwareRegisterInfo *hardware_register;
      uint32_t pointer_address = 0U;
      uint16_t first;
      char high_symbol[80];
      char low_symbol[80];
      if (!ref->has_runtime_address || ref->runtime_address == 0U ||
          (ref->data_class_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) == 0U ||
          ref->offset > decode_section->size || 8U > decode_section->size - ref->offset ||
          !source_quality_copper_list_item_renders_word_row_at(source_analysis, section, section->section_index,
            ref->offset) ||
          !source_quality_copper_list_item_renders_word_row_at(source_analysis, section, section->section_index,
            ref->offset + 4U) ||
          !source_quality_copper_bitmap_pointer_at(decode_section->data, ref->offset, 0U, 8U,
            &pointer_address) ||
          pointer_address != ref->runtime_address) {
        continue;
      }
      first = m68k_read_u16be(decode_section->data + ref->offset);
      hardware_register = source_quality_copper_runtime_pointer_register(first);
      if (hardware_register == NULL || hardware_register->runtime_target_role == NULL ||
          hardware_register->runtime_target_role[0] == '\0') {
        continue;
      }
      platform_format_runtime_address_symbol_name(hardware_register->runtime_target_role, ref->runtime_address,
        "_hi", high_symbol, sizeof(high_symbol));
      platform_format_runtime_address_symbol_name(hardware_register->runtime_target_role, ref->runtime_address,
        "_lo", low_symbol, sizeof(low_symbol));
      if (high_symbol[0] == '\0' || low_symbol[0] == '\0') continue;
      if (append_copper_runtime_pointer_word_symbol_access_and_use(section, ref->offset, high_symbol,
          ref->runtime_address, ref->data_class_flags, ref->confidence) != 0) {
        return -1;
      }
      if (append_copper_runtime_pointer_word_symbol_access_and_use(section, ref->offset + 4U, low_symbol,
          ref->runtime_address, ref->data_class_flags, ref->confidence) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int source_quality_instruction_has_call_flow(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  if (instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  return metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_CALL;
}

static const M68kDecodeCandidate *source_quality_previous_accepted_candidate(
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t cursor) {
  size_t candidate_index;
  const M68kDecodeCandidate *best = NULL;
  if (section == NULL || accepted_start == NULL || cursor == 0U || cursor > section->size) return NULL;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (candidate->byte_count == 0U || candidate->byte_count > cursor) continue;
    if (candidate->offset + candidate->byte_count != cursor) continue;
    if (best == NULL || candidate->offset > best->offset) best = candidate;
  }
  return best;
}

static int source_quality_find_platform_call_input_immediate(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kRecoveredPlatformCallIR *call, const AmigaOsCallInputInfo *input,
    const M68kDecodeCandidate **out_candidate, uint32_t *out_value) {
  uint32_t cursor;
  size_t scan_count = 0U;
  if (out_candidate != NULL) *out_candidate = NULL;
  if (out_value != NULL) *out_value = 0U;
  if (section == NULL || accepted_start == NULL || call == NULL || input == NULL) return 0;
  cursor = call->offset;
  while (scan_count < 12U) {
    const M68kDecodeCandidate *candidate =
      source_quality_previous_accepted_candidate(section, accepted_start, cursor);
    M68kInstructionIR instruction;
    uint8_t reg_kind = 0U;
    uint8_t reg_index = 0U;
    uint32_t value = 0U;
    if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    if (source_quality_instruction_loads_immediate_to_register(&instruction, &reg_kind, &reg_index, &value) &&
        reg_kind == input->reg_kind && reg_index == input->reg_index) {
      if (out_candidate != NULL) *out_candidate = candidate;
      if (out_value != NULL) *out_value = value;
      return 1;
    }
    if (source_quality_instruction_writes_register(&instruction, input->reg_kind, input->reg_index)) break;
    if (source_quality_instruction_has_call_flow(&instruction)) break;
    cursor = candidate->offset;
    ++scan_count;
  }
  return 0;
}

static const char *source_quality_amiga_input_type_or_struct_name(const AmigaOsCallInputInfo *input) {
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

static int format_source_quality_amiga_call_input_note(uint16_t stack_offset,
    const AmigaOsCallInputInfo *input, char *buf, size_t buf_size) {
  const char *symbol_name;
  const char *type_name;
  const char *semantic_kind;
  const char *value_domain_name;
  size_t used;
  if (buf == NULL || buf_size == 0U || input == NULL || stack_offset == 0U) return 0;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id);
  type_name = source_quality_amiga_input_type_or_struct_name(input);
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

static const AmigaOsCallInputInfo *source_quality_amiga_vector_input_by_register(
    const AmigaOsLibraryVectorInfo *vector, uint8_t reg_kind, uint8_t reg_index) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t index;
  if (vector == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL) return NULL;
  for (index = 0U; index < input_count; ++index) {
    if (inputs[index].reg_kind == reg_kind && inputs[index].reg_index == reg_index) return &inputs[index];
  }
  return NULL;
}

static const AmigaOsCallInputInfo *source_quality_amiga_vector_input_by_stack_index(
    const AmigaOsLibraryVectorInfo *vector, size_t stack_index) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  if (vector == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL || stack_index >= input_count) return NULL;
  return &inputs[stack_index];
}

static int source_quality_operand_is_predec_a7(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_PREDEC) return operand->value.reg == 7U;
  return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 4U && operand->value.ea_reg == 7U;
}

static int source_quality_operand_is_postinc_a7(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_POSTINC) return operand->value.reg == 7U;
  return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 3U && operand->value.ea_reg == 7U;
}

static int source_quality_operand_is_stack_displacement(const M68kOperandIR *operand, int16_t *out_displacement) {
  uint8_t reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (!source_quality_operand_address_displacement(operand, &reg, &displacement) || reg != 7U) return 0;
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static int source_quality_instruction_is_long_stack_push(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction->operand_count == 1U) return 1;
  return instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
    instruction->operand_count == 2U && source_quality_operand_is_predec_a7(&instruction->operands[1]);
}

static uint16_t source_quality_reglist_long_stack_size(uint32_t mask) {
  uint16_t size = 0U;
  unsigned bit;
  for (bit = 0U; bit < 16U; ++bit) {
    if ((mask & (1UL << bit)) != 0U) size = (uint16_t)(size + 4U);
  }
  return size;
}

static int source_quality_instruction_stack_delta(const M68kInstructionIR *instruction, int32_t *out_delta) {
  size_t operand_index;
  if (out_delta != NULL) *out_delta = 0;
  if (instruction == NULL || out_delta == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction->operand_count == 1U) {
    *out_delta = 4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && source_quality_operand_is_predec_a7(&instruction->operands[1])) {
    *out_delta = 4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && source_quality_operand_is_postinc_a7(&instruction->operands[0])) {
    *out_delta = -4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U) {
    if (instruction->operands[0].kind == M68K_ASM_OPERAND_REGLIST &&
        source_quality_operand_is_predec_a7(&instruction->operands[1])) {
      *out_delta = source_quality_reglist_long_stack_size(instruction->operands[0].value.value);
      return 1;
    }
    if (source_quality_operand_is_postinc_a7(&instruction->operands[0]) &&
        instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      *out_delta = -(int32_t)source_quality_reglist_long_stack_size(instruction->operands[1].value.value);
      return 1;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      source_quality_operand_address_register_index(&instruction->operands[1], NULL)) {
    uint8_t reg = 0U;
    int16_t displacement = 0;
    if (!source_quality_operand_address_register_index(&instruction->operands[1], &reg) || reg != 7U ||
        !source_quality_operand_is_stack_displacement(&instruction->operands[0], &displacement)) {
      return 0;
    }
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
      instruction->operand_count == 2U) {
    uint8_t reg = 0U;
    uint32_t value = 0U;
    if (!source_quality_operand_address_register_index(&instruction->operands[1], &reg) || reg != 7U ||
        !m68k_ir_operand_immediate_value(&instruction->operands[0], &value) || value > INT16_MAX) {
      return 0;
    }
    *out_delta = (instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ)
      ? (int32_t)value
      : -(int32_t)value;
    return 1;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    if (source_quality_operand_is_predec_a7(&instruction->operands[operand_index]) ||
        source_quality_operand_is_postinc_a7(&instruction->operands[operand_index])) {
      return 0;
    }
  }
  if (instruction->operand_count > 0U) {
    uint8_t reg = 0U;
    if (source_quality_operand_address_register_index(&instruction->operands[instruction->operand_count - 1U],
        &reg) && reg == 7U) {
      return 0;
    }
  }
  return 1;
}

static int source_quality_stack_frame_depth_before_candidate(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t before_offset, uint16_t *out_depth) {
  const M68kDecodeCandidate *candidates[32];
  size_t count = 0U;
  int32_t depth = 0;
  uint32_t cursor;
  if (out_depth != NULL) *out_depth = 0U;
  if (section == NULL || accepted_start == NULL || out_depth == NULL) return 0;
  cursor = before_offset;
  while (count < sizeof(candidates) / sizeof(candidates[0])) {
    const M68kDecodeCandidate *candidate =
      source_quality_previous_accepted_candidate(section, accepted_start, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    candidates[count++] = candidate;
    cursor = candidate->offset;
  }
  while (count > 0U) {
    M68kInstructionIR instruction;
    int32_t delta = 0;
    --count;
    if (m68k_decode_candidate_to_instruction(candidates[count], &instruction) != 0) return 0;
    if (!source_quality_instruction_stack_delta(&instruction, &delta)) return 0;
    depth += delta;
    if (depth < 0 || depth > UINT16_MAX) return 0;
  }
  *out_depth = (uint16_t)depth;
  return 1;
}

static int append_platform_call_input_semantic_use(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeCandidate *candidate, uint16_t stack_offset, const AmigaOsCallInputInfo *input) {
  M68kPlatformSemanticUseIR use;
  char note[192];
  if (section_analysis == NULL || candidate == NULL || input == NULL || stack_offset == 0U) return 0;
  if (!format_source_quality_amiga_call_input_note(stack_offset, input, note, sizeof(note))) return 0;
  memset(&use, 0, sizeof(use));
  use.kind = M68K_PLATFORM_SEMANTIC_USE_PLATFORM_CALL_INPUT;
  use.offset = candidate->offset;
  use.size = candidate->byte_count;
  use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  use.note_text = note;
  return m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use);
}

static int append_platform_operand_expr_semantic_use(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeCandidate *candidate, uint8_t kind, uint32_t operand_index, const char *operand_expr,
    uint8_t confidence, const char *expected_producer, uint8_t expected_confidence) {
  M68kPlatformSemanticUseIR use;
  if (section_analysis == NULL || candidate == NULL || operand_expr == NULL || operand_expr[0] == '\0') return 0;
  memset(&use, 0, sizeof(use));
  use.kind = kind;
  use.offset = candidate->offset;
  use.size = candidate->byte_count;
  use.confidence = confidence;
  use.operand_index = operand_index;
  use.operand_expr = (char *)operand_expr;
  use.has_operand_expr = 1U;
  if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
  return append_expected_platform_symbol_expr_accesses(section_analysis, operand_expr, expected_producer,
    candidate->offset, operand_index, expected_confidence);
}

static int append_platform_call_input_operand_expr_semantic_uses_for_call(
    M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kRecoveredPlatformCallIR *call, const AmigaOsLibraryVectorInfo *vector) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t input_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL || call == NULL || vector == NULL) {
    return 0;
  }
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL) return 0;
  for (input_index = 0U; input_index < input_count; ++input_index) {
    const AmigaOsCallInputInfo *input = &inputs[input_index];
    const M68kDecodeCandidate *producer = NULL;
    const char *value_domain_name;
    char symbol_expr[M68K_IR_SYMBOL_NAME_SIZE];
    uint32_t value = 0U;
    if (input->value_domain_id == AMIGA_OS_VALUE_DOMAIN_ID_NONE) continue;
    if (!source_quality_find_platform_call_input_immediate(section, accepted_start, call, input, &producer, &value))
      continue;
    value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input->value_domain_id);
    if (!amiga_value_domain_symbolic_expr(value_domain_name, value, symbol_expr, sizeof(symbol_expr))) continue;
    if (append_platform_operand_expr_semantic_use(section_analysis, producer,
        M68K_PLATFORM_SEMANTIC_USE_PLATFORM_CALL_INPUT, 0U, symbol_expr,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, "platform_call_input_value_domain_operand",
        M68K_FACT_CONFIDENCE_REQUIRED) != 0) {
      return -1;
    }
  }
  return 0;
}

static const AmigaOsLibraryVectorInfo *source_quality_recovered_call_vector(
    const M68kRecoveredPlatformCallIR *call) {
  const char *symbol_name;
  const AmigaOsLibraryVectorInfo *vector;
  if (call == NULL) return NULL;
  symbol_name = m68k_platform_name_ref_display_text(&call->symbol_ref, call->symbol_name);
  vector = amiga_os_find_library_vector_by_symbol_name(symbol_name);
  if (vector != NULL) return vector;
  symbol_name = m68k_platform_name_ref_display_text(&call->note_symbol_ref, call->note_symbol_name);
  return amiga_os_find_library_vector_by_symbol_name(symbol_name);
}

static int append_local_wrapper_call_input_semantic_uses(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kRecoveredPlatformCallIR *call) {
  const char *call_symbol;
  const AmigaOsLibraryVectorInfo *vector;
  uint32_t cursor;
  uint16_t push_stack_offset = 4U;
  size_t scan_count = 0U;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL || call == NULL ||
      call->note_kind != M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL) {
    return 0;
  }
  call_symbol = m68k_platform_name_ref_display_text(&call->symbol_ref, call->symbol_name);
  if (call_symbol == NULL || call_symbol[0] == '\0') {
    call_symbol = m68k_platform_name_ref_display_text(&call->note_symbol_ref, call->note_symbol_name);
  }
  vector = amiga_os_find_library_vector_by_symbol_name(call_symbol);
  if (vector == NULL) return 0;
  cursor = call->offset;
  while (scan_count < 12U) {
    const M68kDecodeCandidate *candidate =
      source_quality_previous_accepted_candidate(section, accepted_start, cursor);
    M68kInstructionIR instruction;
    const AmigaOsCallInputInfo *input;
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    if (!source_quality_instruction_is_long_stack_push(&instruction)) break;
    input = source_quality_amiga_vector_input_by_stack_index(vector, (size_t)((push_stack_offset / 4U) - 1U));
    if (input == NULL ||
        append_platform_call_input_semantic_use(section_analysis, candidate, push_stack_offset, input) != 0) {
      break;
    }
    push_stack_offset = (uint16_t)(push_stack_offset + 4U);
    cursor = candidate->offset;
    ++scan_count;
  }
  return 0;
}

static int append_stack_load_platform_call_input_semantic_uses(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    const AmigaOsLibraryVectorInfo *vector, uint16_t stack_frame_depth) {
  int16_t displacement = 0;
  if (section_analysis == NULL || candidate == NULL || instruction == NULL || vector == NULL) return 0;
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->size_suffix == 'l' && instruction->operand_count == 2U &&
      source_quality_operand_is_stack_displacement(&instruction->operands[0], &displacement)) {
    uint8_t reg = 0U;
    uint8_t reg_kind = 0U;
    const AmigaOsCallInputInfo *input;
    if (source_quality_operand_data_register_index(&instruction->operands[1], &reg)) reg_kind = 1U;
    else if (source_quality_operand_address_register_index(&instruction->operands[1], &reg)) reg_kind = 2U;
    input = source_quality_amiga_vector_input_by_register(vector, reg_kind, reg);
    if (input != NULL && displacement > (int16_t)stack_frame_depth) {
      if (append_platform_call_input_semantic_use(section_analysis, candidate,
          (uint16_t)(displacement - (int16_t)stack_frame_depth), input) != 0) {
        return -1;
      }
      return 1;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && source_quality_operand_is_stack_displacement(&instruction->operands[0],
        &displacement) && instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST &&
      displacement > (int16_t)stack_frame_depth) {
    uint32_t mask = instruction->operands[1].value.value;
    uint16_t stack_offset = (uint16_t)(displacement - (int16_t)stack_frame_depth);
    unsigned bit;
    int added = 0;
    for (bit = 0U; bit < 16U; ++bit) {
      uint8_t reg_kind;
      uint8_t reg_index;
      const AmigaOsCallInputInfo *input;
      if ((mask & (1UL << bit)) == 0U) continue;
      reg_kind = bit < 8U ? 1U : 2U;
      reg_index = (uint8_t)(bit < 8U ? bit : bit - 8U);
      input = source_quality_amiga_vector_input_by_register(vector, reg_kind, reg_index);
      if (input != NULL &&
          append_platform_call_input_semantic_use(section_analysis, candidate, stack_offset, input) != 0) {
        return -1;
      }
      if (input != NULL) added = 1;
      stack_offset = (uint16_t)(stack_offset + 4U);
    }
    return added;
  }
  return 0;
}

static int append_platform_call_input_semantic_uses_for_call(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kRecoveredPlatformCallIR *call,
    const AmigaOsLibraryVectorInfo *vector) {
  uint32_t cursor;
  uint16_t push_stack_offset = 4U;
  size_t scan_count = 0U;
  int allow_register_stack_loads;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL || call == NULL || vector == NULL)
    return 0;
  if (call->note_kind == M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL) return 0;
  allow_register_stack_loads = call->note_kind == M68K_PLATFORM_CALL_NOTE_NONE ||
    call->note_kind == M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL;
  cursor = call->offset;
  while (scan_count < 12U) {
    const M68kDecodeCandidate *candidate =
      source_quality_previous_accepted_candidate(section, accepted_start, cursor);
    M68kInstructionIR instruction;
    uint16_t stack_frame_depth = 0U;
    int load_result;
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    load_result = 0;
    if (allow_register_stack_loads &&
        source_quality_stack_frame_depth_before_candidate(section, accepted_start, candidate->offset,
          &stack_frame_depth)) {
      load_result = append_stack_load_platform_call_input_semantic_uses(section_analysis, candidate, &instruction,
        vector, stack_frame_depth);
      if (load_result < 0) return -1;
    }
    if (load_result > 0) {
      cursor = candidate->offset;
      ++scan_count;
      continue;
    }
    if (source_quality_instruction_is_long_stack_push(&instruction)) {
      const AmigaOsCallInputInfo *input = source_quality_amiga_vector_input_by_stack_index(vector,
        (size_t)((push_stack_offset / 4U) - 1U));
      if (input == NULL ||
          append_platform_call_input_semantic_use(section_analysis, candidate, push_stack_offset, input) != 0) {
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

static int append_platform_call_input_semantic_uses_for_section(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start) {
  size_t call_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  for (call_index = 0U; call_index < section_analysis->recovered_platform_call_count; ++call_index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[call_index];
    const char *call_symbol = m68k_platform_name_ref_display_text(&call->symbol_ref, call->symbol_name);
    const AmigaOsLibraryVectorInfo *vector;
    if (call_symbol == NULL || call_symbol[0] == '\0') {
      call_symbol = m68k_platform_name_ref_display_text(&call->note_symbol_ref, call->note_symbol_name);
    }
    if (call_symbol == NULL || call_symbol[0] == '\0') continue;
    vector = source_quality_recovered_call_vector(call);
    if (append_platform_call_input_operand_expr_semantic_uses_for_call(section_analysis, section, accepted_start,
        call, vector) != 0) {
      return -1;
    }
    if (call->note_kind == M68K_PLATFORM_CALL_NOTE_LOCAL_HELPER_SYMBOL) continue;
    if (call->note_kind == M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL) {
      if (append_local_wrapper_call_input_semantic_uses(section_analysis, section, accepted_start, call) != 0) {
        return -1;
      }
      continue;
    }
    if (append_platform_call_input_semantic_uses_for_call(section_analysis, section, accepted_start, call,
        vector) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_platform_call_input_semantic_uses(M68kSourceAnalysisIR *source_analysis,
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
    if (append_platform_call_input_semantic_uses_for_section(section_analysis, section, accepted_start[decode_index])
        != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_platform_stack_cleanup_semantic_uses_for_section(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start) {
  size_t call_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  for (call_index = 0U; call_index < section_analysis->recovered_platform_call_count; ++call_index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[call_index];
    const M68kDecodeCandidate *candidate;
    const char *note_symbol_name;
    M68kPlatformSemanticUseIR use;
    char note[160];
    if (call->note_kind != M68K_PLATFORM_CALL_NOTE_STACK_CLEANUP ||
        call->note_stack_cleanup_known == 0U) {
      continue;
    }
    note_symbol_name = m68k_platform_name_ref_display_text(&call->note_symbol_ref, call->note_symbol_name);
    if (note_symbol_name == NULL || note_symbol_name[0] == '\0') continue;
    candidate = m68k_decode_ir_find_candidate_at_offset(section, call->offset);
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    snprintf(note, sizeof(note), "KNOWN: stack cleanup for %s pop %u", note_symbol_name,
      (unsigned)call->note_stack_cleanup_bytes);
    memset(&use, 0, sizeof(use));
    use.kind = M68K_PLATFORM_SEMANTIC_USE_PLATFORM_STACK_CLEANUP;
    use.offset = candidate->offset;
    use.size = candidate->byte_count;
    use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
    use.note_text = note;
    if (m68k_ir_section_analysis_append_platform_semantic_use(section_analysis, &use) != 0) return -1;
  }
  return 0;
}

static int append_platform_stack_cleanup_semantic_uses(M68kSourceAnalysisIR *source_analysis,
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
    if (append_platform_stack_cleanup_semantic_uses_for_section(section_analysis, section,
        accepted_start[decode_index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static int source_quality_hardware_register_immediate_symbol_expr(
    const AmigaOsHardwareRegisterInfo *hardware_register, const M68kInstructionIR *instruction,
    int use_bit_domain, uint32_t value, char *symbol_expr, size_t symbol_expr_size) {
  uint16_t domain_id;
  const char *domain_name = NULL;
  if (hardware_register == NULL || instruction == NULL || symbol_expr == NULL || symbol_expr_size == 0U) return 0;
  if (!use_bit_domain) value = source_quality_immediate_domain_value_for_instruction_size(instruction, value);
  if (platform_amiga_hardware_register_custom_immediate_expr(hardware_register, value, use_bit_domain, symbol_expr,
      symbol_expr_size)) {
    return 1;
  }
  domain_id = use_bit_domain ? hardware_register->bit_domain_id : hardware_register->value_domain_id;
  if (domain_id == AMIGA_OS_VALUE_DOMAIN_ID_NONE) return 0;
  domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, domain_id);
  if (domain_name == NULL || domain_name[0] == '\0') return 0;
  return amiga_value_domain_symbolic_expr(domain_name, value, symbol_expr, symbol_expr_size);
}

static int append_expected_hardware_register_value_domain_symbol_accesses_for_section(
    M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section, const uint8_t *accepted_start) {
  size_t observation_index;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  for (observation_index = 0U; observation_index < section_analysis->address_observation_count; ++observation_index) {
    const M68kAddressObservationIR *observation = &section_analysis->address_observations[observation_index];
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    const AmigaOsHardwareRegisterInfo *hardware_register;
    int use_bit_domain;
    size_t operand_index;
    if (observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER) continue;
    if (observation->access_kind != M68K_SIM_ACCESS_MEMORY_WRITE &&
        observation->access_kind != M68K_SIM_ACCESS_MEMORY_READ &&
        observation->access_kind != M68K_SIM_ACCESS_COMPUTE_ADDRESS) {
      continue;
    }
    candidate = m68k_decode_ir_find_candidate_at_offset(section, observation->offset);
    if (!source_quality_candidate_is_accepted_start(section, accepted_start, candidate)) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) continue;
    hardware_register = amiga_os_find_hardware_register_by_cpu_address(observation->address);
    if (hardware_register == NULL) continue;
    use_bit_domain =
      metadata->operation_type == M68K_SIM_OP_BIT_TEST ||
      metadata->operation_type == M68K_SIM_OP_BIT_SET ||
      metadata->operation_type == M68K_SIM_OP_BIT_CLEAR ||
      metadata->operation_type == M68K_SIM_OP_BIT_CHANGE;
    for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
      char symbol_expr[M68K_IR_SYMBOL_NAME_SIZE];
      uint32_t value = 0U;
      if (!m68k_ir_operand_immediate_value(&instruction.operands[operand_index], &value)) continue;
      if (!source_quality_hardware_register_immediate_symbol_expr(hardware_register, &instruction, use_bit_domain,
          value, symbol_expr, sizeof(symbol_expr))) continue;
      if (append_platform_operand_expr_semantic_use(section_analysis, candidate,
          M68K_PLATFORM_SEMANTIC_USE_HARDWARE_VALUE, (uint32_t)operand_index, symbol_expr,
          observation->confidence, "platform_hardware_register_value_domain_operand",
          observation->confidence) != 0)
        return -1;
    }
  }
  return 0;
}

static int append_expected_hardware_register_value_domain_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
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
    if (append_expected_hardware_register_value_domain_symbol_accesses_for_section(section_analysis, section,
        accepted_start[decode_index]) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_expected_register_derived_hardware_value_domain_symbol_accesses_for_section(
    M68kSectionAnalysisIR *section_analysis, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kAnalysisPolicy *policy, const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds,
    size_t hardware_base_seed_count) {
  SourceQualityHardwareBaseState state;
  uint32_t offset;
  if (section_analysis == NULL || section == NULL || accepted_start == NULL) return 0;
  memset(&state, 0, sizeof(state));
  for (offset = 0U; offset < section->size; ++offset) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    size_t operand_index;
    int use_bit_domain;
    if (accepted_start[offset] == 0U) continue;
    candidate = m68k_decode_ir_find_candidate_at_offset(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U) continue;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
    source_quality_hardware_base_state_apply_policy_register_seeds(&state, policy, section->section_index,
      candidate->offset);
    source_quality_hardware_base_state_apply_inferred_register_seeds(&state, hardware_base_seeds,
      hardware_base_seed_count, section->section_index, candidate->offset);
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) {
      source_quality_hardware_base_state_update_after_instruction(&state, &instruction);
      continue;
    }
    use_bit_domain =
      metadata->operation_type == M68K_SIM_OP_BIT_TEST ||
      metadata->operation_type == M68K_SIM_OP_BIT_SET ||
      metadata->operation_type == M68K_SIM_OP_BIT_CLEAR ||
      metadata->operation_type == M68K_SIM_OP_BIT_CHANGE;
    for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
      uint8_t access_kind = metadata->operand_access_kinds[operand_index];
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      const AmigaOsHardwareRegisterInfo *hardware_register;
      size_t immediate_index;
      if (access_kind != M68K_SIM_ACCESS_MEMORY_WRITE &&
          access_kind != M68K_SIM_ACCESS_MEMORY_READ &&
          access_kind != M68K_SIM_ACCESS_COMPUTE_ADDRESS) {
        continue;
      }
      if (!source_quality_operand_address_displacement(&instruction.operands[operand_index], &base_reg,
          &displacement) ||
          base_reg >= 8U ||
          !m68k_bitset_u32_has(state.address_base_known, base_reg) ||
          displacement < 0) {
        continue;
      }
      hardware_register = amiga_os_find_hardware_register_by_base_id_offset(state.address_base_id[base_reg],
        (uint32_t)(uint16_t)displacement);
      if (hardware_register == NULL) continue;
      for (immediate_index = 0U; immediate_index < instruction.operand_count; ++immediate_index) {
        char symbol_expr[M68K_IR_SYMBOL_NAME_SIZE];
        uint32_t value = 0U;
        if (!m68k_ir_operand_immediate_value(&instruction.operands[immediate_index], &value)) continue;
        if (!source_quality_hardware_register_immediate_symbol_expr(hardware_register, &instruction, use_bit_domain,
            value, symbol_expr, sizeof(symbol_expr))) continue;
        if (append_platform_operand_expr_semantic_use(section_analysis, candidate,
            M68K_PLATFORM_SEMANTIC_USE_HARDWARE_VALUE, (uint32_t)immediate_index, symbol_expr,
            M68K_FACT_CONFIDENCE_TOOL_INFERRED, "platform_hardware_base_register_value_domain_operand",
            M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0)
          return -1;
      }
    }
    source_quality_hardware_base_state_update_after_instruction(&state, &instruction);
  }
  return 0;
}

static int append_expected_register_derived_hardware_value_domain_symbol_accesses(
    M68kSourceAnalysisIR *source_analysis, const M68kDecodeIR *decode, uint8_t *const *accepted_start,
    const M68kAnalysisPolicy *policy, const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds,
    size_t hardware_base_seed_count) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  if (decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t decode_index = 0U;
    const M68kDecodeSectionIR *section = source_quality_decode_section_by_index(decode,
      (uint32_t)section_analysis->section_index, &decode_index);
    if (section == NULL) continue;
    if (append_expected_register_derived_hardware_value_domain_symbol_accesses_for_section(section_analysis, section,
        accepted_start[decode_index], policy, hardware_base_seeds, hardware_base_seed_count) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_expected_table_entry_target_symbol_accesses(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t entry_index;
    for (entry_index = 0U; entry_index < section_analysis->table_entry_count; ++entry_index) {
      const M68kTableEntryIR *entry = &section_analysis->table_entries[entry_index];
      M68kSectionAnalysisIR *target_section;
      const M68kSymbolOriginIR *origin;
      M68kExpectedSymbolAccessIR access;
      if (!entry->has_target || entry->target_status != M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET) {
        continue;
      }
      target_section = source_analysis_section_by_index(source_analysis, entry->target_section_index);
      if (target_section == NULL) continue;
      origin = source_quality_symbol_origin_at(target_section, entry->target_offset);
      if (origin == NULL) continue;
      memset(&access, 0, sizeof(access));
      access.symbol_name = origin->symbol_name;
      access.producer = "table_entry_target";
      access.offset = entry->entry_offset;
      access.target_section_index = entry->target_section_index;
      access.target_offset = entry->target_offset;
      access.operand_index = UINT32_MAX;
      access.access_kind = M68K_EXPECTED_SYMBOL_ACCESS_OPERAND;
      access.confidence = origin->confidence;
      access.has_target = 1U;
      if (m68k_ir_section_analysis_append_expected_symbol_access(section_analysis, &access) != 0) return -1;
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

static int source_quality_relocation_target_inside_structured_item(const M68kAnalysisStructuredDataItem *item,
    const M68kFact *relocation) {
  if (item == NULL || relocation == NULL || !item->has_section_index || item->size == 0U ||
      relocation->target_section_index != item->section_index) {
    return 0;
  }
  if (item->offset > UINT32_MAX - item->size) return 0;
  return relocation->target_offset >= item->offset && relocation->target_offset < item->offset + item->size;
}

static int append_structured_data_table_entry_target(M68kSourceAnalysisIR *source_analysis,
    M68kSectionAnalysisIR *section_analysis, const M68kAnalysisStructuredDataItem *item, uint32_t entry_index,
    uint32_t entry_offset, uint32_t entry_size, uint32_t raw_value, uint8_t raw_value_width,
    uint32_t target_section_index, int64_t target_offset, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const uint8_t *accepted_bytes) {
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
  entry.target_section_index = target_section_index;
  entry.target_offset = (uint32_t)target_offset;
  if (item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH ||
      item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH) {
    if (section != NULL && target_section_index == section->section_index) {
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
    M68kSectionAnalysisIR *section_analysis, const M68kAnalysisStructuredDataItem *item,
    const M68kFactIR *facts) {
  uint32_t cursor;
  uint32_t entry_size;
  if (source_analysis == NULL || section == NULL || section_analysis == NULL || item == NULL ||
      section->data == NULL) {
    return -1;
  }
  entry_size = m68k_analysis_structured_data_table_entry_size(item);
  if (entry_size == 0U || item->size < entry_size || item->offset >= section->size) return 0;
  if (item->table_conflicted) return 0;
  for (cursor = 0U; cursor + entry_size <= item->size && item->offset + cursor + entry_size <= section->size;
      cursor += entry_size) {
    uint32_t entry_index = cursor / entry_size;
    uint32_t entry_offset = item->offset + cursor;
    if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && item->has_target) {
      uint16_t raw_word = m68k_read_u16be(section->data + entry_offset);
      int64_t target_offset = (int64_t)item->target_offset + (int32_t)(int16_t)raw_word;
      if (append_structured_data_table_entry_target(source_analysis, section_analysis, item, entry_index,
          entry_offset, entry_size, raw_word, 2U, item->target_section, target_offset, section, accepted_start,
          accepted_bytes) != 0) {
        return -1;
      }
    } else if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
        source_quality_structured_data_item_is_keyed_long_relative_lookup_table(item)) {
      uint32_t raw_long = m68k_read_u32be(section->data + entry_offset);
      int64_t target_offset = (int64_t)item->target_offset + (int32_t)(int16_t)((raw_long >> 16U) & 0xFFFFU);
      if (append_structured_data_table_entry_target(source_analysis, section_analysis, item, entry_index,
          entry_offset, entry_size, raw_long, 4U, item->target_section, target_offset, section, accepted_start,
          accepted_bytes) != 0) {
        return -1;
      }
    } else if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
        (source_quality_structured_data_item_is_pointer_table(item) ||
         source_quality_structured_data_item_is_absolute_long_lookup_table(item))) {
      uint32_t raw_long = m68k_read_u32be(section->data + entry_offset);
      uint32_t target_offset = 0U;
      uint8_t allow_source_offset = source_quality_structured_data_item_is_absolute_long_lookup_table(item) ? 1U : 0U;
      const M68kFact *relocation = item->source_pattern_id ==
          M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_RELOCATION_POINTER_TABLE ?
        source_quality_unique_relocation_ref_for_span(facts, section_analysis->section_index, entry_offset,
          entry_size) : NULL;
      if (relocation != NULL && relocation->target_section_index <= UINT32_MAX &&
          !source_quality_relocation_target_inside_structured_item(item, relocation)) {
        if (append_structured_data_table_entry_target(source_analysis, section_analysis, item, entry_index,
            entry_offset, entry_size, raw_long, 4U, (uint32_t)relocation->target_section_index,
            relocation->target_offset, section, accepted_start, accepted_bytes) != 0) {
          return -1;
        }
      } else if (raw_long != 0U &&
          source_quality_exact_pointer_value_label_offset(section_analysis, section->size, raw_long,
            allow_source_offset, &target_offset)) {
        if (append_structured_data_table_entry_target(source_analysis, section_analysis, item, entry_index,
            entry_offset, entry_size, raw_long, 4U, item->target_section, target_offset, section, accepted_start,
            accepted_bytes) != 0) {
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
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes) {
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
        section_accepted_bytes, section_analysis, item, facts) != 0) {
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
    while ((size_t)cursor < section->certain_code_size && section->certain_code_byte[cursor] != 0U) {
      const M68kDecodeCandidate *candidate = NULL;
      uint32_t next_offset = cursor + 1U;
      if (decode_section != NULL && section->certain_code_start != NULL &&
          section->certain_code_start[cursor] != 0U) {
        candidate = m68k_decode_ir_find_candidate_at_offset(decode_section, cursor);
        if (candidate != NULL && candidate->byte_count != 0U &&
            candidate->byte_count <= UINT32_MAX - cursor &&
            cursor + candidate->byte_count <= section->certain_code_size) {
          next_offset = cursor + candidate->byte_count;
        }
      }
      cursor = next_offset;
      if (candidate != NULL && source_quality_candidate_stops_linear_flow(candidate)) break;
    }
    memset(&run, 0, sizeof(run));
    run.start_offset = start;
    run.end_offset = cursor;
    run.end_kind = (size_t)cursor >= section->certain_code_size ?
      M68K_ACCEPTED_CODE_RUN_END_SECTION_BOUNDARY : M68K_ACCEPTED_CODE_RUN_END_ACCEPTED_GAP;
    run.has_origin = (uint8_t)accepted_run_has_origin(section, start, cursor);
    (void)classify_run_end_from_decode(section, decode_section, start, cursor, &run);
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
            source_quality_kind_for_manual_run_conflict(section, &run,
              M68K_SOURCE_QUALITY_DIAGNOSTIC_PARTIAL_CODE_BLOCK_DECODE),
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

int m68k_source_quality_analyze_with_policy_and_hardware_base_seeds(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes, const M68kAnalysisPolicy *policy,
    const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds, size_t hardware_base_seed_count) {
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
  if (append_expected_storage_label_statement_symbol_accesses(source_analysis) != 0) return -1;
  if (append_expected_intrinsic_branch_symbol_accesses(source_analysis, decode, facts, accepted_start) != 0)
    return -1;
  if (append_expected_data_operand_symbol_accesses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_expected_pc_relative_storage_symbol_accesses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_expected_manual_equate_symbol_accesses(source_analysis) != 0) return -1;
  if (append_expected_runtime_ref_symbol_accesses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_platform_runtime_structured_data_items(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_bitmap_memory_runtime_refs(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_expected_copper_runtime_pointer_word_symbol_accesses(source_analysis, decode) != 0) return -1;
  if (append_expected_hardware_register_value_domain_symbol_accesses(source_analysis, decode, accepted_start) != 0)
    return -1;
  if (append_expected_register_derived_hardware_value_domain_symbol_accesses(source_analysis, decode,
      accepted_start, policy, hardware_base_seeds, hardware_base_seed_count) != 0)
    return -1;
  if (append_hardware_base_platform_address_uses(source_analysis, decode, accepted_start, policy,
      hardware_base_seeds, hardware_base_seed_count) != 0)
    return -1;
  if (append_palette_upload_structured_data_items(source_analysis, decode, facts, accepted_start, accepted_bytes) != 0)
    return -1;
  if (append_relocation_pointer_table_items(source_analysis, decode, facts, accepted_bytes) != 0) return -1;
  if (append_indexed_word_dispatch_table_items(source_analysis, decode, accepted_start, accepted_bytes) != 0)
    return -1;
  if (append_pc_relative_lookup_table_items(source_analysis, decode, accepted_start, accepted_bytes) != 0) return -1;
  m68k_ir_source_analysis_finalize_table_conflicts(source_analysis);
  if (append_structured_data_range_ownerships(source_analysis) != 0) return -1;
  if (append_manual_mid_instruction_diagnostics(source_analysis) != 0) return -1;
  if (append_manual_noncode_overlap_diagnostics(source_analysis) != 0) return -1;
  if (append_accepted_run_noncode_fallthrough_diagnostics(source_analysis) != 0) return -1;
  if (append_unterminated_accepted_gap_diagnostics(source_analysis) != 0) return -1;
  if (append_structured_data_platform_semantic_uses(source_analysis) != 0) return -1;
  if (append_structured_copper_row_platform_semantic_uses(source_analysis, decode) != 0) return -1;
  if (append_copper_display_setup_platform_semantic_uses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_runtime_ref_platform_semantic_uses(source_analysis) != 0) return -1;
  if (append_bitmap_memory_platform_semantic_uses(source_analysis) != 0) return -1;
  if (append_platform_call_input_semantic_uses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_platform_stack_cleanup_semantic_uses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_audio_source_platform_semantic_uses(source_analysis, decode, accepted_start, accepted_bytes) != 0)
    return -1;
  if (append_runtime_sink_pointer_semantic_uses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_runtime_sink_pointer_hardware_base_semantic_uses(source_analysis, decode, accepted_start, policy,
      hardware_base_seeds, hardware_base_seed_count) != 0)
    return -1;
  if (append_runtime_sink_operand_expr_semantic_uses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_hardware_note_platform_semantic_uses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_hardware_base_note_platform_semantic_uses(source_analysis, decode, accepted_start, policy,
      hardware_base_seeds, hardware_base_seed_count) != 0)
    return -1;
  if (append_structured_data_table_descriptors(source_analysis) != 0) return -1;
  if (append_structured_data_table_entries(source_analysis, decode, facts, accepted_start, accepted_bytes) != 0)
    return -1;
  if (append_expected_table_entry_target_symbol_accesses(source_analysis) != 0) return -1;
  if (append_immediate_text_tokens(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_address_identities_and_ranges(source_analysis) != 0) return -1;
  if (append_expected_address_observation_symbol_accesses(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_expected_platform_symbol_operand_accesses(source_analysis, decode, accepted_start) != 0) return -1;
  return 0;
}

int m68k_source_quality_analyze_with_policy(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes, const M68kAnalysisPolicy *policy) {
  return m68k_source_quality_analyze_with_policy_and_hardware_base_seeds(source_analysis, decode, facts,
    accepted_start, accepted_bytes, policy, NULL, 0U);
}

int m68k_source_quality_analyze(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes) {
  return m68k_source_quality_analyze_with_policy(source_analysis, decode, facts, accepted_start, accepted_bytes, NULL);
}

int m68k_source_quality_analyze_rendered_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
    const M68kRenderEvidenceIR *render_evidence) {
  size_t section_index;
  M68kRenderedReferenceIndex reference_index;
  int result = -1;
  if (source_analysis == NULL || render_evidence == NULL) return -1;
  if (rendered_reference_index_build(render_evidence, &reference_index) != 0) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kRenderEvidenceSectionIR *render_evidence_section =
      m68k_ir_render_evidence_section_by_index(render_evidence,
        (uint32_t)source_analysis->sections[section_index].section_index);
    if (append_missing_expected_symbol_access_diagnostics_for_section(&source_analysis->sections[section_index],
        render_evidence_section) != 0) {
      goto done;
    }
    if (append_unreferenced_label_statement_diagnostics_for_section(source_analysis,
        &source_analysis->sections[section_index], render_evidence, &reference_index) != 0) {
      goto done;
    }
  }
  result = 0;

done:
  rendered_reference_index_destroy(&reference_index);
  return result;
}
