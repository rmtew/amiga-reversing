/* Direct-call inputs use existing shared transfer/joins. CALL dependencies are
 * separate from ordinary CFG successors: no guessed return edges or caller
 * stack frame is introduced into the callee. Facts remain scoped to the known
 * original control-flow graph, not arbitrary replacement entry paths. */
static void typed_flow_call_entry_input(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kRenderTypedFlowNode *caller,
    M68kRenderTypedState *typed, M68kRenderPlatformState *platform) {
  typed_flow_instruction_input(lookup, section, caller, typed, platform);
  memset(typed->stack_slots, 0, sizeof(typed->stack_slots)); typed->stack_slot_count = 0U;
  memset(typed->base_slots, 0, sizeof(typed->base_slots)); typed->base_slot_count = 0U;
  memset(typed->field_slots, 0, sizeof(typed->field_slots)); typed->field_slot_count = 0U;
  memset(typed->io_request_setups, 0, sizeof(typed->io_request_setups));
  typed->absolute_memory_written = 1U;
  for (uint8_t i = 0U; i < 8U; ++i) {
    if (typed->data_regs[i].origin.kind == M68K_RENDER_TYPED_ORIGIN_STACK_SLOT)
      typed_origin_clear(&typed->data_regs[i].origin);
    if (typed->addr_regs[i].origin.kind == M68K_RENDER_TYPED_ORIGIN_STACK_SLOT)
      typed_origin_clear(&typed->addr_regs[i].origin);
  }
  typed_state_clear_reg(typed, M68K_ANALYSIS_REGISTER_ADDRESS, 7U);
  memset(platform->local_base_slots, 0, sizeof(platform->local_base_slots));
  m68k_bitset_u32_clear(&platform->address_base_known, 7U);
  platform->address_base_id[7] = 0U; platform->address_base_library[7][0] = '\0';
  m68k_bitset_u32_clear(&platform->address_hardware_base_known, 7U);
  platform->address_hardware_base_id[7] = 0U;
  m68k_bitset_u32_clear(&platform->address_app_base_known, 7U);
  m68k_bitset_u32_clear(&platform->address_layout_base_known, 7U);
  platform->address_layout_base_symbol[7][0] = '\0';
  memset(&platform->relative_hardware[7], 0, sizeof(platform->relative_hardware[7]));
}

static int typed_flow_hardware_root(const M68kRenderTypedFlowGraph *graph, size_t node) {
  return graph->nodes[node].is_root || (graph->call_inputs_enabled &&
    graph->call_predecessor_offsets &&
    graph->call_predecessor_offsets[node] != graph->call_predecessor_offsets[node + 1U]);
}

static int typed_flow_exposed_entry(const M68kRenderLookup *lookup, size_t section, uint32_t offset) {
  const M68kAnalysisPolicy *policy = lookup->policy;
  if (typed_flow_offset_is_policy_entry_point(policy, section, offset) ||
      (lookup->storage_label_target_refs && lookup->storage_label_target_ref_extents &&
       section < lookup->section_count && lookup->storage_label_target_refs[section] &&
       offset <= lookup->storage_label_target_ref_extents[section] &&
       lookup->storage_label_target_refs[section][offset])) return 1;
  if (!policy) return 0;
  /* A register seed constrains the value/type at an instruction. It is not
   * evidence of an additional incoming control-flow edge. Explicit code
   * entries, callback/address exposures and function contracts below carry
   * that independent-entry meaning; ordinary annotation sites do not. */
  for (size_t i = 0U; i < policy->function_summary_count; ++i) {
    const M68kAnalysisFunctionSummary *summary = &policy->function_summaries[i];
    if (summary->has_section_index && summary->section_index == section &&
        summary->callable_kind == M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT &&
        summary->entry_offset == offset) return 1;
  }
  for (size_t i = 0U; i < policy->runtime_entry_point_count; ++i) {
    size_t mapped_section; uint32_t mapped_offset;
    if (render_lookup_pointer_value_to_object_source_location(lookup,
          policy->runtime_entry_points[i].runtime_address, &mapped_section, &mapped_offset) &&
        mapped_section == section && mapped_offset == offset) return 1;
  }
  return 0;
}

/* Entry exposures grow monotonically across converged call-input epochs.
 * Each node can become independent once; a later widened value cannot revoke
 * an already established possible callback. No arbitrary epoch cap is used. */
static int typed_flow_retain_new_call_exposures(const M68kRenderLookup *lookup,
    M68kRenderTypedFlowWorkflow *workflow) {
  int changed = 0;
  for (size_t i = 0U; i < lookup->address_value_consumer_count; ++i) {
    const M68kRenderTypedStoredValue *value = &lookup->address_value_consumers[i].value;
    if (!value->pointer_value_known || value->address_value_candidate_overflow ||
        value->pointer_candidate_count > 4U) continue;
    size_t count = value->pointer_candidate_count ? value->pointer_candidate_count : 1U;
    for (size_t j = 0U; j < count; ++j) {
      uint32_t raw = count == 1U ? value->pointer_value : value->pointer_candidates[j];
      size_t section; uint32_t offset;
      if (!render_lookup_pointer_value_to_object_source_location(lookup, raw, &section, &offset) ||
          section >= workflow->section_count) continue;
      M68kRenderTypedFlowGraph *g = &workflow->graphs[section];
      if (offset >= g->node_by_offset_count || g->node_by_offset[offset] == SIZE_MAX) continue;
      size_t node = g->node_by_offset[offset];
      if (!g->call_independent_entries[node]) {
        g->call_independent_entries[node] = 1U;
        g->nodes[node].is_root = 1U;
        g->call_inputs_enabled = 1U;
        changed = 1;
      }
    }
  }
  return changed;
}

static int typed_flow_enable_call_inputs(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted, M68kRenderTypedFlowWorkflow *workflow) {
  if (!workflow->graphs) return 0;
  uint8_t **independent = arena_calloc(workflow->arena, workflow->section_count, sizeof(*independent));
  if (!independent) return -1;
  for (size_t section = 0U; section < workflow->section_count; ++section) {
    M68kRenderTypedFlowGraph *g = &workflow->graphs[section];
    if (!g->node_count) continue;
    g->call_predecessor_offsets = arena_calloc(workflow->arena, g->node_count + 1U, sizeof(size_t));
    independent[section] = arena_calloc(workflow->arena, g->node_count, 1U);
    g->call_independent_entries = independent[section];
    if (!g->call_predecessor_offsets || !independent[section]) return -1;
    for (size_t n = 0U; n < g->node_count; ++n) {
      g->nodes[n].call_target = SIZE_MAX;
      independent[section][n] = typed_flow_exposed_entry(lookup, section, g->nodes[n].candidate->offset);
    }
  }
  /* One decode scan builds all section indexes. Known data-address exposures
   * and cross-section calls retain unknown independent entries. */
  for (size_t from_section = 0U; from_section < decode->section_count; ++from_section) {
    const M68kDecodeSectionIR *s = &decode->sections[from_section];
    for (size_t i = 0U; i < s->candidate_count; ++i) {
      const M68kDecodeCandidate *c = &s->candidates[i];
      M68kInstructionIR instruction;
      size_t target_section; uint32_t offset;
      if (!candidate_is_accepted_start(s, accepted[from_section], c)) continue;
      for (size_t t = 0U; t < c->target_count; ++t) {
        const M68kDecodeTarget *target = &c->targets[t];
        if (target->kind != M68K_DECODE_TARGET_DATA || !target->has_section ||
            target->section_index >= workflow->section_count) continue;
        M68kRenderTypedFlowGraph *g = &workflow->graphs[target->section_index];
        if (target->offset < g->node_by_offset_count && g->node_by_offset[target->offset] != SIZE_MAX)
          independent[target->section_index][g->node_by_offset[target->offset]] = 1U;
      }
      if (m68k_decode_candidate_to_instruction(c, &instruction) != 0 ||
          !instruction_has_call_flow_local(&instruction) ||
          !typed_flow_local_call_target(lookup, c, &target_section, &offset) ||
          target_section >= workflow->section_count) continue;
      M68kRenderTypedFlowGraph *g = &workflow->graphs[target_section];
      if (offset >= g->node_by_offset_count || g->node_by_offset[offset] == SIZE_MAX) continue;
      size_t target = g->node_by_offset[offset];
      if (from_section != target_section) { independent[target_section][target] = 1U; continue; }
      if (c->offset >= g->node_by_offset_count || g->node_by_offset[c->offset] == SIZE_MAX) continue;
      size_t caller = g->node_by_offset[c->offset];
      g->nodes[caller].call_target = target;
      ++g->call_predecessor_offsets[target + 1U];
    }
  }
  for (size_t r = 0U; r < lookup->runtime_address_ref_count; ++r) {
    const M68kFact *ref = lookup->runtime_address_refs[r].fact;
    if (!ref || ref->target_section_index >= workflow->section_count) continue;
    M68kRenderTypedFlowGraph *g = &workflow->graphs[ref->target_section_index];
    if (ref->target_offset >= g->node_by_offset_count || g->node_by_offset[ref->target_offset] == SIZE_MAX) continue;
    int control = 0;
    if (ref->section_index < workflow->section_count) {
      const M68kRenderTypedFlowGraph *source = &workflow->graphs[ref->section_index];
      if (ref->offset < source->node_by_offset_count && source->node_by_offset[ref->offset] != SIZE_MAX) {
        M68kInstructionIR instruction;
        if (m68k_decode_candidate_to_instruction(source->nodes[source->node_by_offset[ref->offset]].candidate,
              &instruction) == 0) {
          const M68kSimFormMetadata *metadata = m68k_sim_metadata_for_instruction(&instruction);
          control = metadata && (metadata->flow_kind == M68K_SIM_FLOW_CALL ||
            metadata->flow_kind == M68K_SIM_FLOW_JUMP || metadata->flow_kind == M68K_SIM_FLOW_BRANCH);
        }
      }
    }
    if (!control) independent[ref->target_section_index][g->node_by_offset[ref->target_offset]] = 1U;
  }
  /* Declared/inferred callback summaries own their LONG table domain even
   * when no ordinary pointer-table rendering descriptor exists. */
  size_t declared_count = lookup->policy ? lookup->policy->function_summary_count : 0U;
  for (size_t i = 0U; i < declared_count + lookup->inferred_function_summary_count; ++i) {
    const M68kAnalysisFunctionSummary *summary = i < declared_count ?
      &lookup->policy->function_summaries[i] : &lookup->inferred_function_summaries[i - declared_count].summary;
    if (summary->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_CALLBACK_TABLE ||
        !summary->has_section_index || !lookup->object ||
        summary->section_index >= lookup->object->section_count) continue;
    const M68kSection *table = &lookup->object->sections[summary->section_index];
    if (!table->data || summary->table_offset > table->size ||
        summary->entry_count > (table->size - summary->table_offset) / 4U) continue;
    for (size_t j = 0U; j < summary->entry_count; ++j) {
      size_t section; uint32_t offset;
      uint32_t raw = m68k_read_u32be(table->data + summary->table_offset + j * 4U);
      if (!render_lookup_pointer_value_to_object_source_location(lookup, raw, &section, &offset) ||
          section >= workflow->section_count) continue;
      const M68kRenderTypedFlowGraph *g = &workflow->graphs[section];
      if (offset < g->node_by_offset_count && g->node_by_offset[offset] != SIZE_MAX)
        independent[section][g->node_by_offset[offset]] = 1U;
    }
  }
  (void)typed_flow_retain_new_call_exposures(lookup, workflow);
  for (size_t section = 0U; section < workflow->section_count; ++section) {
    M68kRenderTypedFlowGraph *g = &workflow->graphs[section];
    if (!g->node_count) continue;
    size_t *cursor = arena_calloc(workflow->arena, g->node_count, sizeof(size_t));
    uint8_t *reachable = arena_calloc(workflow->arena, g->node_count, 1U);
    size_t *queue = arena_alloc(workflow->arena, g->node_count * sizeof(size_t));
    size_t head = 0U, count = 0U;
    if (!cursor || !reachable || !queue) return -1;
    for (size_t n = 0U; n < g->node_count; ++n)
      g->call_predecessor_offsets[n + 1U] += g->call_predecessor_offsets[n];
    size_t calls = g->call_predecessor_offsets[g->node_count];
    g->call_predecessors = arena_alloc(workflow->arena, (calls ? calls : 1U) * sizeof(size_t));
    if (!g->call_predecessors) return -1;
    memcpy(cursor, g->call_predecessor_offsets, g->node_count * sizeof(size_t));
    for (size_t n = 0U; n < g->node_count; ++n) if (g->nodes[n].call_target < g->node_count)
      g->call_predecessors[cursor[g->nodes[n].call_target]++] = n;
    for (size_t n = 0U; n < g->node_count; ++n) {
      if (independent[section][n] || (g->nodes[n].is_root &&
          g->call_predecessor_offsets[n] == g->call_predecessor_offsets[n + 1U])) {
        reachable[n] = 1U; queue[count++] = n;
      }
    }
    while (head < count) {
      size_t n = queue[head++];
      for (size_t e = 0U; e <= g->nodes[n].successor_count; ++e) {
        size_t target = e == g->nodes[n].successor_count ? g->nodes[n].call_target : g->nodes[n].successors[e];
        if (target < g->node_count && !reachable[target]) { reachable[target] = 1U; queue[count++] = target; }
      }
    }
    size_t changed_roots = 0U, contextual_entries = 0U;
    for (size_t n = 0U; n < g->node_count; ++n) {
      uint8_t before = g->nodes[n].is_root;
      if (!independent[section][n] && g->call_predecessor_offsets[n] != g->call_predecessor_offsets[n + 1U])
        ++contextual_entries;
      if (independent[section][n]) g->nodes[n].is_root = 1U;
      else if (reachable[n] && g->call_predecessor_offsets[n] != g->call_predecessor_offsets[n + 1U])
        g->nodes[n].is_root = 0U;
      /* Unreachable recursive/disconnected components retain their unknown
       * original roots; absence of a known entry never becomes a proof. */
      changed_roots += before != g->nodes[n].is_root;
    }
    g->call_inputs_enabled = g->call_inputs_enabled || contextual_entries != 0U || changed_roots != 0U;
    const char *trace = getenv("AMIGA_REVERSING_PROFILE_CALL_INPUTS");
    if (trace && !strcmp(trace, "1")) fprintf(stderr,
      "call_inputs section=%zu nodes=%zu edges=%zu contextual_entries=%zu changed_roots=%zu node_bytes=%zu index_bytes=%zu\n",
      section, g->node_count, calls, contextual_entries, changed_roots, sizeof(M68kRenderTypedFlowNode),
      (g->node_count + 1U + calls) * sizeof(size_t));
  }
  return 0;
}
