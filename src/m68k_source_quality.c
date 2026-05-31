#include "m68k_source_quality.h"

#include "m68k_fact_ir.h"
#include "m68k_simulator.h"

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
    origin.evidence_kind = ref->reason;
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
  for (index = 0U; index < section->absolute_memory_ref_count; ++index) {
    const M68kAbsoluteMemoryRefIR *ref = &section->absolute_memory_refs[index];
    M68kAddressObservationIR observation;
    memset(&observation, 0, sizeof(observation));
    observation.offset = ref->offset;
    observation.operand_index = ref->operand_index;
    observation.raw_value = ref->address;
    observation.address = ref->address;
    observation.access_width = ref->access_width;
    observation.access_kind = ref->access_kind;
    observation.source = M68K_ADDRESS_OBSERVATION_SOURCE_ABSOLUTE_MEMORY_REF;
    observation.owner_kind = ref->owner_kind;
    observation.owner_offset = ref->owner_offset;
    observation.conflict_state = ref->conflict_state;
    observation.conflicted = ref->conflicted;
    observation.has_address = 1U;
    observation.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
    if (m68k_ir_section_analysis_append_address_observation(section, &observation) != 0) return -1;
  }
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

int m68k_source_quality_analyze(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    if (append_code_origins_for_section(section) != 0) return -1;
    if (append_address_observations_for_section(section) != 0) return -1;
    if (append_platform_address_uses_for_section(section) != 0) return -1;
    if (append_accepted_runs_for_section(section) != 0) return -1;
    if (append_accepted_code_range_ownerships_for_section(section) != 0) return -1;
  }
  if (append_structured_data_range_ownerships(source_analysis) != 0) return -1;
  if (append_structured_data_table_descriptors(source_analysis) != 0) return -1;
  if (append_address_identities_and_ranges(source_analysis) != 0) return -1;
  return 0;
}
