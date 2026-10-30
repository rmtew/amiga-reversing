/* Complete callable successors require a converged, non-contract WORD set,
 * canonical table entries and a dominating load-to-transfer relation. Known
 * code targets or structural table length alone never close an indirect edge. */
static int callable_dispatch_pc_base(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint8_t operand, size_t expected_section, uint32_t expected) {
  const M68kOperandIR *ea = &instruction->operands[operand];
  size_t section; uint32_t target, unit;
  return m68k_instruction_operand_decoded_ea_shape(ea) == M68K_SIM_EA_SHAPE_PC_INDEX &&
    m68k_sim_operand_word_index_value(instruction, operand, 1U, &unit) && unit == 1U &&
    !ea->value.index_is_address &&
    candidate_data_target_for_operand(candidate, operand, &section, &target) &&
    section == expected_section && target == expected;
}

static int callable_dispatch_bind_entries(const M68kDecodeIR *decode, uint8_t **accepted,
    M68kSourceAnalysisIR *analysis, const M68kRelativeDispatchFact *fact,
    const M68kHardwareWordSet *values, M68kRenderClosedDispatch *out) {
  size_t section_index = fact->table_section_index;
  if (section_index >= decode->section_count || !values->count || values->requires_input_contract) return 0;
  const M68kDecodeSectionIR *section = &decode->sections[section_index];
  M68kAddressValueTableOriginIR origin = {0};
  origin.table_section_index = (uint32_t)section_index; origin.table_start_offset = fact->table_offset;
  memset(out, 0, sizeof(*out)); out->relation = *fact; out->indices = *values;
  for (uint8_t i = 0U; i < values->count; ++i) {
    int32_t displacement = (int16_t)values->values[i];
    if (displacement < 0 || (displacement & 1) || (uint32_t)displacement >= fact->table_size) return 0;
    const M68kTableEntryIR *entry = m68k_source_analysis_table_entry_for_origin(analysis, &origin,
      (uint32_t)displacement / 2U);
    if (!entry || !entry->has_target || entry->entry_size != 2U || entry->raw_value_width != 2U ||
        entry->entry_offset != fact->table_offset + (uint32_t)displacement ||
        entry->entry_offset > section->size || 2U > section->size - entry->entry_offset ||
        entry->raw_value != m68k_read_u16be(section->data + entry->entry_offset) || entry->conflict_state ||
        entry->table_kind_id != M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH ||
        entry->source_pattern_id != M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_WORD_DISPATCH ||
        entry->target_status != M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET ||
        entry->target_section_index != section_index || entry->target_offset >= section->size ||
        !accepted[section_index][entry->target_offset]) return 0;
    int64_t target = (int64_t)fact->base_offset + (int16_t)entry->raw_value;
    if (target != entry->target_offset) return 0;
    uint8_t j = 0U;
    while (j < out->count && out->targets[j] != entry->target_offset) ++j;
    if (j == out->count) out->targets[out->count++] = entry->target_offset;
  }
  return out->count != 0U;
}

static int callable_dispatch_candidate(const M68kDecodeIR *decode,
    const M68kRenderTypedFlowWorkflow *flow, const M68kRelativeDispatchFact *fact,
    M68kRenderClosedDispatch *out) {
  if (!flow || !flow->graphs ||
      fact->consumer_section_index >= flow->section_count || !fact->has_producer || fact->entry_size != 2U ||
      fact->producer_section_index != fact->consumer_section_index ||
      fact->table_section_index != fact->consumer_section_index ||
      fact->base_section_index != fact->consumer_section_index ||
      fact->consumer_section_index >= decode->section_count ||
      fact->producer_offset >= fact->consumer_offset) return 0;
  size_t section_index = fact->consumer_section_index;
  const M68kDecodeSectionIR *section = &decode->sections[section_index];
  M68kRenderTypedFlowGraph *graph = &flow->graphs[section_index];
  if (fact->producer_offset >= graph->node_by_offset_count ||
      graph->node_by_offset[fact->producer_offset] == SIZE_MAX) return 0;
  const M68kRenderTypedFlowNode *load = &graph->nodes[graph->node_by_offset[fact->producer_offset]];
  const M68kDecodeCandidate *jump = m68k_decode_ir_find_candidate_at_offset(section, fact->consumer_offset);
  M68kInstructionIR li, ji; uint8_t loaded;
  if (!load->word_proof_ready || !jump ||
      m68k_decode_candidate_to_instruction(load->candidate, &li) ||
      m68k_decode_candidate_to_instruction(jump, &ji) || li.mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
      li.size_suffix != 'w' || li.operand_count != 2U || fact->producer_operand_index != 0U ||
      !operand_is_data_register_local(&li.operands[1], &loaded) ||
      ji.mnemonic_id != M68K_ASM_MNEMONIC_JMP || ji.operand_count != 1U ||
      !callable_dispatch_pc_base(load->candidate, &li, 0U, section_index, fact->table_offset) ||
      !callable_dispatch_pc_base(jump, &ji, 0U, section_index, fact->base_offset) ||
      ji.operands[0].value.index_reg != loaded) return 0;
  uint8_t index = li.operands[0].value.index_reg;
  if (index >= 8U) return 0;
  const M68kHardwareWordSet *values = &load->platform_in.word_values[index];
  if (!values->count || values->requires_input_contract) return 0;
  /* No alternate incoming edge, call or mutation of the loaded displacement
   * may occur before the transfer. This validates dominance rather than
   * promoting a single trace witness into a universal control relation. */
  uint32_t previous = load->candidate->offset, cursor = previous + load->candidate->byte_count;
  while (cursor <= jump->offset) {
    if (cursor >= graph->node_by_offset_count || graph->node_by_offset[cursor] == SIZE_MAX) return 0;
    size_t n = graph->node_by_offset[cursor], begin = graph->predecessor_offsets[n];
    const M68kRenderTypedFlowNode *node = &graph->nodes[n];
    if (node->is_root || graph->predecessor_offsets[n + 1U] != begin + 1U ||
        graph->nodes[graph->predecessors[begin]].candidate->offset != previous) return 0;
    if (cursor == jump->offset) break;
    M68kInstructionIR instruction;
    if (m68k_decode_candidate_to_instruction(node->candidate, &instruction)) return 0;
    const M68kSimFormMetadata *meta = m68k_sim_metadata_for_instruction(&instruction);
    if (!meta || meta->flow_kind != M68K_SIM_FLOW_SEQUENTIAL) return 0;
    for (size_t i = 0U; i < instruction.operand_count; ++i)
      if (platform_operand_register_write_mask(&instruction, i) & ((uint16_t)1U << loaded)) return 0;
    previous = cursor; cursor += node->candidate->byte_count;
  }
  memset(out, 0, sizeof(*out)); out->relation = *fact; out->indices = *values;
  return 1;
}

/* Copy only a validated relation and finite index proof while the shared
 * graph still contains converged packets. Loop/range projection later loans
 * those packets; no late source pass may interpret their temporary contents. */
static int callable_dispatch_capture(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    const M68kRenderTypedFlowWorkflow *flow) {
  lookup->dispatch_request_count = 0U;
  if (!lookup->control_facts || !flow || !flow->graphs) return 0;
  const M68kFactIR *facts = lookup->control_facts;
  for (size_t i = 0U; i < facts->relative_dispatch_count; ++i) {
    M68kRenderClosedDispatch request;
    const M68kRelativeDispatchFact *fact = &facts->relative_dispatches[i];
    if (!callable_dispatch_candidate(decode, flow, fact, &request)) continue;
    int ambiguous = 0;
    for (size_t j = 0U; j < facts->relative_dispatch_count; ++j)
      if (j != i && facts->relative_dispatches[j].consumer_section_index == fact->consumer_section_index &&
          facts->relative_dispatches[j].consumer_offset == fact->consumer_offset) ambiguous = 1;
    if (ambiguous) continue;
    if (lookup->dispatch_request_count == lookup->dispatch_request_capacity) {
      size_t capacity = lookup->dispatch_request_capacity ? lookup->dispatch_request_capacity * 2U : 8U;
      M68kRenderClosedDispatch *grown = render_lookup_grow_array(lookup, lookup->dispatch_requests,
        lookup->dispatch_request_count, sizeof(*grown), capacity);
      if (!grown) return -1;
      lookup->dispatch_requests = grown; lookup->dispatch_request_capacity = capacity;
    }
    lookup->dispatch_requests[lookup->dispatch_request_count++] = request;
  }
  return 0;
}

static int callable_dispatch_collect(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted, M68kSourceAnalysisIR *analysis) {
  int added = 0;
  for (size_t i = 0U; i < lookup->closed_dispatch_count; ++i) {
    const M68kRenderClosedDispatch *existing = &lookup->closed_dispatches[i];
    int found = 0;
    for (size_t j = 0U; j < lookup->dispatch_request_count; ++j)
      if (lookup->dispatch_requests[j].relation.consumer_section_index == existing->relation.consumer_section_index &&
          lookup->dispatch_requests[j].relation.consumer_offset == existing->relation.consumer_offset) found = 1;
    if (!found) return -1;
  }
  for (size_t i = 0U; i < lookup->dispatch_request_count; ++i) {
    const M68kRenderClosedDispatch *request = &lookup->dispatch_requests[i];
    const M68kRelativeDispatchFact *fact = &request->relation;
    const M68kRenderClosedDispatch *existing = lookup_closed_dispatch(lookup,
      fact->consumer_section_index, fact->consumer_offset);
    M68kRenderClosedDispatch candidate;
    int valid = callable_dispatch_bind_entries(decode, accepted, analysis, fact, &request->indices, &candidate);
    if (existing) {
      if (!valid) return -1;
      for (uint8_t j = 0U; j < candidate.count; ++j) {
        uint8_t k = 0U; while (k < existing->count && existing->targets[k] != candidate.targets[j]) ++k;
        if (k == existing->count) return -1;
      }
      continue;
    }
    if (!valid || lookup->source_domain_pass_done) continue;
    if (lookup->closed_dispatch_count == lookup->closed_dispatch_capacity) {
      size_t capacity = lookup->closed_dispatch_capacity ? lookup->closed_dispatch_capacity * 2U : 8U;
      M68kRenderClosedDispatch *grown = render_lookup_grow_array(lookup, lookup->closed_dispatches,
        lookup->closed_dispatch_count, sizeof(*grown), capacity);
      if (!grown) return -1;
      lookup->closed_dispatches = grown; lookup->closed_dispatch_capacity = capacity;
    }
    lookup->closed_dispatches[lookup->closed_dispatch_count++] = candidate; added = 1;
  }
  return added;
}

static int callable_dispatch_reprove(M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted) {
  /* Previously refused bodies must be retried in the same condensation order;
   * recursive components retain the existing independent refusal. */
  for (size_t i = 0U; i < lookup->inferred_function_summary_count; ++i) {
    M68kRenderInferredFunctionSummary *record = &lookup->inferred_function_summaries[i];
    if (record->summary.callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT) continue;
    M68kAnalysisFunctionSummary old = record->summary;
    memset(&record->summary, 0, sizeof(record->summary));
    record->summary.callable_kind = old.callable_kind; record->summary.has_section_index = old.has_section_index;
    record->summary.section_index = old.section_index; record->summary.entry_offset = old.entry_offset;
    memcpy(record->summary.function_summary_id, old.function_summary_id, sizeof(old.function_summary_id));
    function_summary_set_register_partition(&record->summary, 0U, 0U);
    record->summary.memory_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_UNKNOWN;
    record->summary.escape_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_UNKNOWN;
    record->terminal_reason = M68K_FUNCTION_SUMMARY_TERMINAL_NONE;
  }
  return render_lookup_solve_inferred_direct_function_summaries(lookup, decode, accepted);
}
