/* Canonical selection shapes normalize to a byte-index envelope. A singleton
 * stays exact; finite/ambiguous selections are not widened into loop domains. */
static int typed_source_domain_span(M68kSourceAnalysisIR *analysis, const M68kAddressValueIR *value,
    uint32_t *minimum, uint32_t *maximum) {
  if (!value || value->pointer_width != 4U) return 0;
  if (value->resolution == M68K_ADDRESS_VALUE_RESOLUTION_TYPE_DOMAIN &&
      value->table_origin.selection_kind == M68K_ADDRESS_VALUE_TABLE_SELECTION_BOUNDED_SOURCE_CURSOR)
    return m68k_ir_source_analysis_pointer_loop_domain(analysis, value, minimum, maximum) &&
      *minimum == value->table_origin.index_min && *maximum == value->table_origin.index_max;
  if (value->resolution == M68K_ADDRESS_VALUE_RESOLUTION_RESOLVED && value->has_target &&
      value->candidate_target_count == 1U &&
      value->table_origin.selection_kind == M68K_ADDRESS_VALUE_TABLE_SELECTION_SINGLETON &&
      value->table_origin.entry_index <= UINT32_MAX / 4U) {
    *minimum = *maximum = value->table_origin.entry_index * 4U;
    return 1;
  }
  return 0;
}

/* Producer validation precedes conditional refinement. The canonical source
 * binder owns membership/ownership; this is its typed-value input projection. */
static int typed_source_domain_matches(const M68kRenderSourceDomain *domain,
    const M68kRenderSourceReadRequest *request) {
  return domain->struct_id == request->struct_id &&
    domain->producer.section_index == request->producer.section_index &&
    domain->producer.offset == request->producer.offset &&
    domain->producer.producer_operand_index == request->producer.producer_operand_index &&
    domain->origin.table_section_index == request->origin.table_section_index &&
    domain->origin.table_start_offset == request->origin.table_start_offset;
}

static int typed_source_domain_add(M68kRenderLookup *lookup, M68kSourceAnalysisIR *analysis,
    const M68kRenderSourceReadRequest *request, const M68kAddressValueIR *value) {
  M68kRenderSourceDomain domain;
  uint32_t minimum, maximum;
  const char *prefix = lookup_policy_struct_name_by_id(lookup->policy, request->struct_id);
  memset(&domain, 0, sizeof(domain));
  if (!prefix || strcmp(prefix, value->pointee_struct_name) ||
      !typed_source_domain_span(analysis, value, &minimum, &maximum) ||
      (minimum & 3U) || (maximum & 3U) || maximum < minimum) return 0;
  domain.producer = request->producer; domain.origin = value->table_origin;
  domain.struct_id = request->struct_id; domain.member_count = (maximum - minimum) / 4U + 1U;
  if (domain.member_count > SIZE_MAX / sizeof(*domain.members)) return -1;
  domain.members = arena_calloc(lookup->arena, domain.member_count, sizeof(*domain.members));
  if (!domain.members) return -1;
  domain.address_min = UINT32_MAX;
  for (size_t i = 0U; i < domain.member_count; ++i) {
    const M68kTableEntryIR *entry = m68k_source_analysis_table_entry_for_origin(analysis,
      &value->table_origin, minimum / 4U + (uint32_t)i);
    const char *reason = NULL; uint16_t type;
    if (!entry || !entry->has_target || entry->conflict_state || !entry->raw_value ||
        entry->target_status != M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET ||
        !m68k_source_analysis_entry_pointee_contract(analysis, entry, prefix, &type, &reason)) return 0;
    const char *name = lookup_policy_struct_name_by_id(lookup->policy, type);
    const char *canonical = lookup_policy_struct_name_by_id(&analysis->policy, type);
    if (!name || !canonical || strcmp(name, canonical)) return 0;
    M68kRenderSourceDomainMember *member = &domain.members[i];
    member->section_index = entry->target_section_index; member->offset = entry->target_offset;
    member->struct_id = type; member->size = lookup_policy_struct_size_by_id(lookup->policy, type);
    if (!member->size || !lookup_source_unique_runtime_span(lookup, member->section_index,
        member->offset, member->size, &member->address)) return 0;
    if (member->address < domain.address_min) domain.address_min = member->address;
    uint64_t end = (uint64_t)member->address + member->size;
    if (end > domain.address_end) domain.address_end = end;
  }
  uint16_t zero, nonzero;
  if (!typed_read_domain_partition(lookup, &domain, request->field_cursor, &zero, &nonzero) ||
      ((zero == AMIGA_OS_STRUCT_ID_NONE || zero == request->struct_id) &&
       (nonzero == AMIGA_OS_STRUCT_ID_NONE || nonzero == request->struct_id))) return 0;
  if (lookup->source_domain_count >= UINT32_MAX) return -1;
  if (lookup->source_domain_count == lookup->source_domain_capacity) {
    size_t capacity = lookup->source_domain_capacity ? lookup->source_domain_capacity * 2U : 8U;
    M68kRenderSourceDomain *grown = render_lookup_grow_array(lookup, lookup->source_domains,
      lookup->source_domain_count, sizeof(*grown), capacity);
    if (!grown) return -1;
    lookup->source_domains = grown; lookup->source_domain_capacity = capacity;
  }
  lookup->source_domains[lookup->source_domain_count++] = domain;
  return 1;
}

static int typed_source_domains_still_valid(M68kRenderLookup *lookup, M68kSourceAnalysisIR *analysis) {
  for (size_t i = 0U; i < lookup->source_domain_count; ++i) {
    const M68kRenderSourceDomain *domain = &lookup->source_domains[i];
    M68kAddressValueTableOriginIR origin = domain->origin;
    const M68kAddressValueIR *value = NULL;
    uint32_t minimum, maximum;
    if (source_analysis_table_contract_state(analysis, &domain->producer, &origin, &value) !=
          M68K_RENDER_TABLE_CONTRACT_VALID || !typed_source_domain_span(analysis, value, &minimum, &maximum) ||
        value->table_origin.selection_kind != domain->origin.selection_kind ||
        (domain->origin.selection_kind == M68K_ADDRESS_VALUE_TABLE_SELECTION_SINGLETON ?
          value->table_origin.entry_index != domain->origin.entry_index :
          (minimum != domain->origin.index_min || maximum != domain->origin.index_max))) return 0;
    for (size_t j = 0U; j < domain->member_count; ++j) {
      const M68kTableEntryIR *entry = m68k_source_analysis_table_entry_for_origin(analysis,
        &value->table_origin, minimum / 4U + (uint32_t)j);
      uint16_t type;
      const char *prefix = lookup_policy_struct_name_by_id(lookup->policy, domain->struct_id);
      if (!entry || !entry->has_target || entry->conflict_state || !entry->raw_value ||
          entry->target_status != M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET ||
          entry->target_section_index != domain->members[j].section_index ||
          entry->target_offset != domain->members[j].offset ||
          !m68k_source_analysis_entry_pointee_contract(analysis, entry, prefix, &type, NULL) ||
          type != domain->members[j].struct_id) return 0;
    }
  }
  return 1;
}

int m68k_analysis_render_lookup_refine_source_domains(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, M68kSourceAnalysisIR *analysis) {
  if (!lookup || !decode || !accepted_start || !analysis) return -1;
  int closed = callable_dispatch_collect(lookup, decode, accepted_start, analysis);
  if (closed < 0) return -1;
  if (lookup->source_domain_pass_done)
    return typed_source_domains_still_valid(lookup, analysis) ? 0 : -1;
  if (closed && callable_dispatch_reprove(lookup, decode, accepted_start)) return -1;
  lookup->source_domain_pass_done = 1U;
  if (!lookup->pending_source_flow) return 0;
  for (size_t i = 0U; i < lookup->source_read_request_count; ++i) {
    const M68kRenderSourceReadRequest *request = &lookup->source_read_requests[i];
    M68kAddressValueTableOriginIR origin = request->origin;
    const M68kAddressValueIR *value = NULL;
    int found = 0;
    for (size_t j = 0U; j < lookup->source_domain_count; ++j)
      found |= typed_source_domain_matches(&lookup->source_domains[j], request);
    if (found) continue;
    uint32_t minimum, maximum;
    if (source_analysis_table_contract_state(analysis, &request->producer, &origin, &value) !=
          M68K_RENDER_TABLE_CONTRACT_VALID || !typed_source_domain_span(analysis, value, &minimum, &maximum)) continue;
    if (typed_source_domain_add(lookup, analysis, request, value) < 0) return -1;
  }
  if (!lookup->source_domain_count && !closed) { m68k_analysis_render_lookup_release_source_flow(lookup); return 0; }
  /* The loop proof borrows node packets. The ordinary solver recomputes its
   * scalar proof and all input states; graph/index/CFG storage is reused. */
  M68kRenderTypedFlowWorkflow *flow = lookup->pending_source_flow;
  lookup->unresolved_typed_access_count = 0U;
  if (render_lookup_analyze_amiga_typed_refs(lookup, decode, accepted_start, flow, 1) ||
      typed_flow_solve_call_inputs(lookup, decode, accepted_start, flow, 0) ||
      render_lookup_record_typed_app_slot_pointer_accesses(lookup, decode, accepted_start)) return -1;
  typed_flow_filter_nonapp_fallbacks(lookup, decode, flow);
  if (callable_dispatch_capture(lookup, decode, flow) ||
      callable_dispatch_collect(lookup, decode, accepted_start, analysis) < 0) return -1;
  if (typed_flow_record_app_loop_ranges(lookup, decode, accepted_start, flow, 0) ||
      typed_prune_resolved_indexed_diagnostics(lookup)) return -1;
  m68k_analysis_render_lookup_release_source_flow(lookup);
  return 1;
}
