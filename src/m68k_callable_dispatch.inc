/* Complete callable successors require a converged, non-contract WORD set,
 * canonical table entries and a dominating load-to-transfer relation. Known
 * code targets or structural table length alone never close an indirect edge. */
static int callable_dispatch_pc_base(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint8_t operand, size_t expected_section, uint32_t expected) {
  const M68kOperandIR *ea = &instruction->operands[operand];
  size_t section; uint32_t target, unit;
  return m68k_instruction_operand_decoded_ea_shape(ea) == M68K_SIM_EA_SHAPE_PC_INDEX &&
    m68k_sim_operand_word_index_value(instruction, operand, 1U, &unit) && unit == 1U &&
    candidate_data_target_for_operand(candidate, operand, &section, &target) &&
    section == expected_section && target == expected;
}

static int callable_dispatch_target_compare(const void *a, const void *b) {
  uint32_t av = *(const uint32_t *)a, bv = *(const uint32_t *)b;
  return av < bv ? -1 : av > bv;
}

static int callable_dispatch_bind_entries(M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted,
    M68kSourceAnalysisIR *analysis, const M68kRelativeDispatchFact *fact,
    const M68kHardwareWordSet *values, M68kRenderClosedDispatch *out) {
  size_t section_index = fact->table_section_index;
  if (section_index >= decode->section_count || (!values->count && !values->known_bits_mask) ||
      values->requires_input_contract) return 0;
  const M68kDecodeSectionIR *section = &decode->sections[section_index];
  uint16_t minimum, maximum;
  if (values->count) { minimum = values->values[0]; maximum = values->values[values->count - 1U]; }
  else {
    minimum = values->known_bits_value;
    maximum = (uint16_t)(minimum | (uint16_t)~values->known_bits_mask);
    if (!(values->known_bits_mask & 1U) || (minimum & 1U)) return 0;
  }
  /* Reject before using physical ownership as a loop bound: the proof must
   * itself exclude negative, odd and out-of-owner WORD reads. */
  if (maximum > INT16_MAX || maximum >= fact->table_size) return 0;
  M68kAddressValueTableOriginIR origin = {0};
  origin.table_section_index = (uint32_t)section_index; origin.table_start_offset = fact->table_offset;
  memset(out, 0, sizeof(*out)); out->relation = *fact; out->indices = *values;
  size_t capacity = values->count ? values->count : (size_t)(maximum - minimum) / 2U + 1U;
  out->targets = arena_alloc(lookup->arena, capacity * sizeof(*out->targets));
  if (!out->targets) return -1;
  for (uint32_t cursor = 0U; cursor < (values->count ? values->count : capacity); ++cursor) {
    uint32_t displacement = values->count ? values->values[cursor] : minimum + cursor * 2U;
    if (!values->count && (displacement & values->known_bits_mask) != values->known_bits_value) continue;
    if ((displacement & 1U) || displacement >= fact->table_size) return 0;
    const M68kTableEntryIR *entry = m68k_source_analysis_table_entry_for_origin(analysis, &origin, displacement / 2U);
    if (!entry || !entry->has_target || entry->entry_size != 2U || entry->raw_value_width != 2U ||
        entry->entry_offset != fact->table_offset + displacement ||
        entry->entry_offset > section->size || 2U > section->size - entry->entry_offset ||
        entry->raw_value != m68k_read_u16be(section->data + entry->entry_offset) || entry->conflict_state ||
        entry->table_kind_id != M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH ||
        entry->source_pattern_id != M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_WORD_DISPATCH ||
        entry->target_status != M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET ||
        entry->target_section_index != section_index || entry->target_offset >= section->size ||
        !accepted[section_index][entry->target_offset]) return 0;
    int64_t target = (int64_t)fact->base_offset + (int16_t)entry->raw_value;
    if (target != entry->target_offset) return 0;
    out->targets[out->count++] = entry->target_offset;
  }
  qsort(out->targets, out->count, sizeof(*out->targets), callable_dispatch_target_compare);
  size_t unique = 0U;
  for (size_t i = 0U; i < out->count; ++i)
    if (!unique || out->targets[i] != out->targets[unique - 1U]) out->targets[unique++] = out->targets[i];
  out->count = unique;
  return out->count != 0U;
}

/* Backward must-reaching definition over the shared CFG. Only one two-byte
 * visited mask per instruction; queue entries are sparse (instruction,register)
 * pairs. Every incoming path must reach the producer without losing identity. */
static int callable_dispatch_reaches(const M68kRenderTypedFlowGraph *graph,
    size_t producer, uint8_t produced, size_t consumer, uint8_t consumed, uint8_t width) {
  uint16_t *seen = calloc(graph->node_count, sizeof(*seen));
  size_t *queue = NULL, count = 0U, capacity = 0U, head = 0U;
  int result = -1, found = 0;
  if (!seen) return -1;
  capacity = 32U; queue = malloc(capacity * sizeof(*queue));
  if (!queue) goto done;
  queue[count++] = consumer * 16U + consumed;
  seen[consumer] |= (uint16_t)(1U << consumed);
  while (head < count) {
    size_t item = queue[head++], n = item / 16U;
    uint8_t reg = (uint8_t)(item % 16U);
    if (typed_flow_hardware_root(graph, n) ||
        graph->predecessor_offsets[n] == graph->predecessor_offsets[n + 1U]) { result = 0; goto done; }
    for (size_t p = graph->predecessor_offsets[n]; p < graph->predecessor_offsets[n + 1U]; ++p) {
      size_t prev = graph->predecessors[p]; uint8_t prior_reg = reg;
      if (prev == producer && reg == produced) { found = 1; continue; }
      M68kInstructionIR instruction;
      if (m68k_decode_candidate_to_instruction(graph->nodes[prev].candidate, &instruction)) { result = 0; goto done; }
      const M68kSimFormMetadata *meta = m68k_sim_metadata_for_instruction(&instruction);
      /* Calls need a separate validated transport contract, not an assumption
       * that absence of an explicit destination preserves registers. */
      if (!meta || meta->flow_kind == M68K_SIM_FLOW_CALL || meta->flow_kind == M68K_SIM_FLOW_RETURN) {
        result = 0; goto done;
      }
      uint16_t writes = 0U;
      for (size_t i = 0U; i < instruction.operand_count; ++i)
        writes |= platform_operand_register_write_mask(&instruction, i);
      if (writes & (1U << reg)) {
        uint8_t source, dest;
        if (!instruction_register_identity_copy(&instruction, width, &source, &dest) || dest != reg) {
          result = 0; goto done;
        }
        prior_reg = source;
      }
      if (seen[prev] & (1U << prior_reg)) continue;
      seen[prev] |= (uint16_t)(1U << prior_reg);
      if (count == capacity) {
        size_t next = capacity * 2U;
        if (next < capacity || next > SIZE_MAX / sizeof(*queue)) goto done;
        size_t *grown = realloc(queue, next * sizeof(*queue));
        if (!grown) goto done;
        queue = grown; capacity = next;
      }
      queue[count++] = prev * 16U + prior_reg;
    }
  }
  result = found;
done:
  free(queue); free(seen); return result;
}

static int callable_dispatch_candidate(const M68kDecodeIR *decode,
    const M68kRenderTypedFlowWorkflow *flow, const M68kRelativeDispatchFact *fact,
    M68kRenderClosedDispatch *out) {
  if (!flow || !flow->graphs ||
      fact->consumer_section_index >= flow->section_count || !fact->has_producer || fact->entry_size != 2U ||
      fact->producer_section_index != fact->consumer_section_index ||
      fact->table_section_index != fact->consumer_section_index ||
      fact->base_section_index != fact->consumer_section_index ||
      fact->consumer_section_index >= decode->section_count) return 0;
  size_t section_index = fact->consumer_section_index;
  M68kRenderTypedFlowGraph *graph = &flow->graphs[section_index];
  if (fact->producer_offset >= graph->node_by_offset_count || fact->consumer_offset >= graph->node_by_offset_count)
    return 0;
  size_t producer = graph->node_by_offset[fact->producer_offset], consumer = graph->node_by_offset[fact->consumer_offset];
  if (producer == SIZE_MAX || consumer == SIZE_MAX) return 0;
  const M68kRenderTypedFlowNode *load = &graph->nodes[producer], *jump = &graph->nodes[consumer];
  M68kInstructionIR li, ji; uint8_t kind, loaded;
  if (!load->word_proof_ready ||
      m68k_decode_candidate_to_instruction(load->candidate, &li) ||
      m68k_decode_candidate_to_instruction(jump->candidate, &ji) ||
      (li.mnemonic_id != M68K_ASM_MNEMONIC_MOVE && li.mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) ||
      li.size_suffix != 'w' || li.operand_count != 2U || fact->producer_operand_index != 0U ||
      !m68k_instruction_operand_direct_register(&li.operands[1], &kind, &loaded) || loaded >= 8U ||
      ji.mnemonic_id != M68K_ASM_MNEMONIC_JMP || ji.operand_count != 1U ||
      !callable_dispatch_pc_base(load->candidate, &li, 0U, section_index, fact->table_offset) ||
      li.operands[0].value.index_is_address) return 0;
  loaded += kind ? 8U : 0U;
  uint8_t index = li.operands[0].value.index_reg;
  if (index >= 8U) return 0;
  const M68kHardwareWordSet *values = &load->platform_in.word_values[index];
  if ((!values->count && !values->known_bits_mask) || values->requires_input_contract) return 0;
  int reaches = 0;
  if (callable_dispatch_pc_base(jump->candidate, &ji, 0U, section_index, fact->base_offset)) {
    uint8_t target_reg = ji.operands[0].value.index_reg + (ji.operands[0].value.index_is_address ? 8U : 0U);
    reaches = callable_dispatch_reaches(graph, producer, loaded, consumer, target_reg, 2U);
  } else if (m68k_instruction_operand_decoded_ea_shape(&ji.operands[0]) == M68K_SIM_EA_SHAPE_INDIRECT) {
    uint8_t target_reg = ji.operands[0].value.ea_reg;
    if (target_reg >= 8U) return 0;
    /* Find the canonical PC-base construction, then prove both halves of the
     * transport. A numerically plausible An value is never enough. */
    for (size_t n = 0U; n < graph->node_count; ++n) {
      M68kInstructionIR lea; uint8_t dest;
      if (m68k_decode_candidate_to_instruction(graph->nodes[n].candidate, &lea) ||
          lea.mnemonic_id != M68K_ASM_MNEMONIC_LEA || lea.operand_count != 2U ||
          !operand_address_register_index_local(&lea.operands[1], &dest) ||
          !callable_dispatch_pc_base(graph->nodes[n].candidate, &lea, 0U, section_index, fact->base_offset)) continue;
      uint8_t offset_reg = lea.operands[0].value.index_reg + (lea.operands[0].value.index_is_address ? 8U : 0U);
      int a = callable_dispatch_reaches(graph, producer, loaded, n, offset_reg, 2U);
      if (a < 0) return -1;
      if (!a) continue;
      int b = callable_dispatch_reaches(graph, n, dest + 8U, consumer, target_reg + 8U, 4U);
      if (b < 0) return -1;
      if (b) { reaches = 1; break; }
    }
  }
  if (reaches <= 0) return reaches;
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
    int candidate = callable_dispatch_candidate(decode, flow, fact, &request);
    if (candidate < 0) return -1;
    if (!candidate) continue;
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
    int valid = callable_dispatch_bind_entries(lookup, decode, accepted, analysis, fact, &request->indices, &candidate);
    if (valid < 0) return -1;
    if (existing) {
      if (!valid) return -1;
      for (size_t j = 0U; j < candidate.count; ++j) {
        size_t k = 0U; while (k < existing->count && existing->targets[k] != candidate.targets[j]) ++k;
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
