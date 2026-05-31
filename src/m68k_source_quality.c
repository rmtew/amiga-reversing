#include "m68k_source_quality.h"

#include "m68k_fact_ir.h"
#include "m68k_simulator.h"
#include "platform_common.h"

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

static int append_platform_address_uses_for_section(M68kSectionAnalysisIR *section) {
  size_t index;
  if (section == NULL) return -1;
  for (index = 0U; index < section->address_observation_count; ++index) {
    const M68kAddressObservationIR *observation = &section->address_observations[index];
    M68kPlatformAddressUseIR use;
    uint8_t shape = platform_address_use_shape_from_observation(observation);
    if (shape == M68K_PLATFORM_ADDRESS_USE_SHAPE_UNKNOWN) continue;
    memset(&use, 0, sizeof(use));
    use.offset = observation->offset;
    use.operand_index = observation->operand_index;
    use.address = observation->address;
    use.effective_address = observation->address;
    use.access_width = observation->access_width;
    use.access_kind = observation->access_kind;
    use.use_shape = shape;
    use.confidence = observation->confidence;
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

static int classify_run_end_from_cfg(const M68kSectionAnalysisIR *section, uint32_t start, uint32_t end,
    M68kAcceptedCodeRunIR *run) {
  size_t block_index;
  if (section == NULL || run == NULL) return 0;
  for (block_index = 0U; block_index < section->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section->blocks[block_index];
    size_t edge_index;
    if (block->start_offset < start || block->end_offset != end) continue;
    for (edge_index = 0U; edge_index < block->edge_count; ++edge_index) {
      const M68kCfgEdgeIR *edge;
      size_t absolute_edge_index = block->edge_start + edge_index;
      if (absolute_edge_index >= section->edge_count) return -1;
      edge = &section->edges[absolute_edge_index];
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

static M68kSectionAnalysisIR *source_analysis_section_by_index(M68kSourceAnalysisIR *source_analysis,
    uint32_t section_index) {
  size_t index;
  if (source_analysis == NULL) return NULL;
  for (index = 0U; index < source_analysis->section_count; ++index) {
    if (source_analysis->sections[index].section_index == section_index) return &source_analysis->sections[index];
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
    if (!item->has_section_index || item->size == 0U || item->offset > UINT32_MAX - item->size) continue;
    section = source_analysis_section_by_index(source_analysis, item->section_index);
    if (section == NULL) continue;
    memset(&range, 0, sizeof(range));
    range.start_offset = item->offset;
    range.end_offset = item->offset + item->size;
    range.kind = m68k_analysis_structured_data_range_ownership_kind(item);
    range.status = item->table_conflicted ? M68K_RANGE_OWNERSHIP_STATUS_CONFLICT :
      M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED;
    range.data_kind = item->kind;
    range.conflict_state = item->table_conflict_state;
    range.positive_evidence_flags = m68k_analysis_structured_data_range_ownership_evidence_flags(item);
    range.negative_evidence_flags = item->table_conflicted ?
      structured_data_range_negative_evidence_flags(item->table_conflict_state) : 0U;
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

static int append_accepted_runs_for_section(M68kSectionAnalysisIR *section) {
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
    if (classify_run_end_from_cfg(section, start, cursor, &run) < 0) return -1;
    if (section->certain_code_start != NULL) {
      uint32_t offset;
      for (offset = start; offset < cursor && (size_t)offset < section->certain_code_size; ++offset) {
        if (section->certain_code_start[offset] != 0U) ++run.instruction_count;
      }
    }
    if (m68k_ir_section_analysis_append_accepted_code_run(section, &run) != 0) return -1;
    if (!accepted_run_has_executable_origin(section, start, cursor)) {
      if (append_run_diagnostic(section, &run,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_ACCEPTED_CODE_WITHOUT_EXECUTABLE_ORIGIN,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR, 1U,
          "accepted code run lacks non-fallthrough executable origin") != 0) {
        return -1;
      }
    } else if (run.end_kind == M68K_ACCEPTED_CODE_RUN_END_ACCEPTED_GAP) {
      if (append_run_diagnostic(section, &run,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_UNTERMINATED_OR_INVALID_CODE_RANGE,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_WARNING, 0U,
          "accepted code run ends before section boundary without terminal or proven transfer edge") != 0) {
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
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, uint8_t *const *accepted_bytes) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    if (append_code_origins_for_section(section) != 0) return -1;
    if (append_address_observations_for_section(section) != 0) return -1;
    if (append_platform_address_uses_for_section(section) != 0) return -1;
    if (append_accepted_runs_for_section(section) != 0) return -1;
    if (append_accepted_code_range_ownerships_for_section(section) != 0) return -1;
    if (append_orphan_conflict_ranges_for_section(section) != 0) return -1;
  }
  if (append_structured_data_range_ownerships(source_analysis) != 0) return -1;
  if (append_structured_data_table_descriptors(source_analysis) != 0) return -1;
  if (append_structured_data_table_entries(source_analysis, decode, accepted_start, accepted_bytes) != 0) return -1;
  if (append_immediate_text_tokens(source_analysis, decode, accepted_start) != 0) return -1;
  if (append_address_identities_and_ranges(source_analysis) != 0) return -1;
  return 0;
}
