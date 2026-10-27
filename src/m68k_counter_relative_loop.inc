/* Counter-relative ranges are an induction over shared affine entry values.
 * One body traversal must translate every carried input by one fixed offset;
 * its counter and stack pointer must retain their entry identities. Retry
 * edges join at the same PC, so unequal potentials lose the identity. */
typedef struct M68kLoopEntrySnapshot {
  M68kRenderTypedState typed;
  M68kRenderPlatformState platform;
} M68kLoopEntrySnapshot;

typedef struct M68kLoopEntryEdge {
  size_t node;
  uint32_t iterations;
  M68kLoopEntrySnapshot *snapshot;
} M68kLoopEntryEdge;

typedef struct M68kCounterLoopCandidate {
  size_t header, tail;
  uint8_t counter;
  M68kLoopEntryEdge *entries;
  size_t entry_count;
} M68kCounterLoopCandidate;

typedef struct M68kLoopEntryRoot {
  uint8_t kind, reg, app, evidence;
  int16_t displacement, app_displacement;
  uint32_t storage_id;
  int32_t stride;
} M68kLoopEntryRoot;
#define M68K_LOOP_ROOT_DATA 1U
#define M68K_LOOP_ROOT_ADDRESS 2U
#define M68K_LOOP_ROOT_ABSOLUTE 3U
#define M68K_LOOP_ROOT_STACK 4U
#define M68K_LOOP_ROOT_LIMIT (16U + M68K_RENDER_TYPED_BASE_SLOT_LIMIT + M68K_RENDER_TYPED_STACK_SLOT_LIMIT)

typedef struct M68kLoopRangeRow {
  size_t node, operand;
  uint8_t reg, access, width, evidence;
  int16_t first;
  int32_t stride;
} M68kLoopRangeRow;

static int counter_loop_append_index(size_t **items, size_t *count, size_t *capacity, size_t item) {
  if (*count == *capacity) {
    size_t next = *capacity ? *capacity * 2U : 16U;
    size_t *grown;
    if (next < *capacity || next > SIZE_MAX / sizeof(*grown)) return -1;
    grown = realloc(*items, next * sizeof(*grown));
    if (!grown) return -1;
    *items = grown; *capacity = next;
  }
  (*items)[(*count)++] = item; return 0;
}

static uint32_t counter_loop_add_root(M68kAffineEntryContext *context, M68kLoopEntryRoot *roots,
    size_t *count, M68kLoopEntryRoot root, uint8_t width) {
  if (*count >= M68K_LOOP_ROOT_LIMIT) { context->failed = 1; return 0U; }
  roots[*count] = root;
  return affine_entry_intern(context, (uint32_t)++*count, 0, width);
}

static void counter_loop_project_registers(M68kRenderTypedState *state,
    const M68kAffineEntryContext *context, const M68kLoopEntryRoot *roots, size_t root_count) {
  for (uint8_t kind = 0U; kind < 2U; ++kind) for (uint8_t reg = 0U; reg < 8U; ++reg) {
    M68kRenderTypedRegValue *value = kind ? &state->addr_regs[reg] : &state->data_regs[reg];
    M68kRenderTypedAppAddressValue *app = kind ? &state->app_addr_regs[reg] : &state->data_app_addr_regs[reg];
    const M68kAffineEntryValue *entry = affine_entry_value(context, value->entry_value_id);
    memset(app, 0, sizeof(*app));
    if (entry && entry->width == 4U && entry->root <= root_count && roots[entry->root - 1U].app) {
      const M68kLoopEntryRoot *root = &roots[entry->root - 1U];
      int64_t displacement = (int64_t)root->app_displacement + entry->offset;
      if (displacement >= INT16_MIN && displacement <= INT16_MAX) {
        app->known = 1U; app->displacement = (int16_t)displacement; app->base_evidence_kind = root->evidence;
      }
    }
  }
}

static uint32_t counter_loop_root_at_tail(const M68kRenderTypedState *state, const M68kLoopEntryRoot *root) {
  if (root->kind == M68K_LOOP_ROOT_DATA) return state->data_regs[root->reg].entry_value_id;
  if (root->kind == M68K_LOOP_ROOT_ADDRESS) return state->addr_regs[root->reg].entry_value_id;
  if (root->kind == M68K_LOOP_ROOT_ABSOLUTE) {
    const M68kRenderTypedBaseSlot *slot = typed_state_absolute_cell(state, root->storage_id);
    return slot ? slot->value.entry_value_id : 0U;
  }
  if (root->kind == M68K_LOOP_ROOT_STACK) {
    const M68kRenderTypedStoredValue *value = typed_state_stack_slot_value(state, root->displacement);
    return value ? value->entry_value_id : 0U;
  }
  return 0U;
}

static int counter_loop_prove(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, size_t section_index, M68kRenderTypedFlowGraph *graph,
    const M68kCounterLoopCandidate *candidate, size_t snapshot_bytes) {
  const M68kDecodeSectionIR *section = &decode->sections[section_index];
  M68kAffineEntryContext context = {0};
  M68kLoopEntryRoot roots[M68K_LOOP_ROOT_LIMIT];
  M68kLoopEntrySnapshot entry;
  M68kLoopRangeRow *rows = NULL;
  size_t row_count = 0U, row_capacity = 0U;
  size_t *body = NULL, body_count = 0U, body_capacity = 0U, *queue = NULL;
  size_t queue_head = 0U, queue_count = 0U, peak_queue = 0U, transfers = 0U, root_count = 0U;
  size_t counter_root = 0U, stack_root = 0U, lost_root = 0U;
  uint32_t iterations = 0U;
  const char *reason = "unknown_entry";
  int result = 0, found_entry = 0;
  const char *step_trace = getenv("AMIGA_REVERSING_ENTRY_STEP_PC");
  size_t traced_steps = 0U;
  if (counter_loop_append_index(&body, &body_count, &body_capacity, candidate->header) != 0) goto allocation;
  graph->nodes[candidate->header].has_out = 1U;
  for (size_t i = 0U; i < body_count; ++i) {
    size_t node_index = body[i];
    M68kRenderTypedFlowNode *node = &graph->nodes[node_index];
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    if (node_index == candidate->tail) continue;
    if ((graph->call_inputs_enabled && graph->call_predecessor_offsets &&
         graph->call_predecessor_offsets[node_index] != graph->call_predecessor_offsets[node_index + 1U]) ||
        (node->is_root && node_index != candidate->header) ||
        m68k_decode_candidate_to_instruction(node->candidate, &instruction) != 0 ||
        !(metadata = m68k_sim_metadata_for_instruction(&instruction))) { reason = "extra_or_invalid_entry"; goto cleanup; }
    if (!node->successor_count || metadata->flow_kind == M68K_SIM_FLOW_RETURN ||
        metadata->flow_kind == M68K_SIM_FLOW_TRAP || instruction.mnemonic_id == M68K_ASM_MNEMONIC_DBF) {
      reason = "unresolved_or_nested_exit"; goto cleanup;
    }
    if (metadata->flow_kind == M68K_SIM_FLOW_BRANCH || metadata->flow_kind == M68K_SIM_FLOW_JUMP) {
      uint32_t target;
      if (!typed_flow_first_local_control_target(lookup, section, node->candidate, &target)) {
        reason = "unresolved_control_target"; goto cleanup;
      }
    }
    for (uint8_t j = 0U; j < node->successor_count; ++j) {
      size_t next = node->successors[j];
      if (next >= graph->node_count) { reason = "unresolved_successor"; goto cleanup; }
      if (!graph->nodes[next].has_out) {
        if (counter_loop_append_index(&body, &body_count, &body_capacity, next) != 0) goto allocation;
        graph->nodes[next].has_out = 1U;
      }
    }
  }
  if (!graph->nodes[candidate->tail].has_out) { reason = "tail_unreachable"; goto cleanup; }
  for (size_t i = 0U; i < body_count; ++i) {
    size_t node = body[i];
    if (node == candidate->header) continue;
    for (size_t p = graph->predecessor_offsets[node]; p < graph->predecessor_offsets[node + 1U]; ++p)
      if (!graph->nodes[graph->predecessors[p]].has_out) { reason = "interior_external_entry"; goto cleanup; }
  }
  for (size_t i = 0U; i < candidate->entry_count; ++i) {
    const M68kLoopEntryEdge *edge = &candidate->entries[i];
    if (graph->nodes[edge->node].has_out) continue;
    if (!edge->snapshot || !edge->iterations) { reason = "unknown_entry_counter"; goto cleanup; }
    if (!found_entry) { entry = *edge->snapshot; iterations = edge->iterations; found_entry = 1; }
    else {
      if (iterations != edge->iterations) { reason = "different_entry_counts"; goto cleanup; }
      (void)typed_state_merge_into(&entry.typed, &edge->snapshot->typed, lookup->policy);
      (void)platform_state_merge_into(&entry.platform, &edge->snapshot->platform);
    }
  }
  if (!found_entry) goto cleanup;
  for (size_t i = 0U; i < body_count; ++i) {
    M68kRenderTypedFlowNode *node = &graph->nodes[body[i]];
    typed_state_clear_all(&node->typed_in); typed_state_clear_all(&node->typed_out);
    memset(&node->platform_in, 0, sizeof(node->platform_in)); memset(&node->platform_out, 0, sizeof(node->platform_out));
    node->has_in = 0U;
  }
  lookup->affine_entry_context = &context;
  /* Each entry register/cell is a distinct symbolic input. Equal numeric
   * offsets never equate an iteration's mutable cursor with a fixed base. */
  for (uint8_t reg = 0U; reg < 7U; ++reg) {
    M68kRenderTypedAppAddressValue app = entry.typed.app_addr_regs[reg];
    if (!app.known && reg == 6U) {
      app.base_evidence_kind = render_app_base_evidence_kind(lookup, &entry.platform, reg, 0, 1U);
      app.known = app.base_evidence_kind != M68K_APP_SLOT_BASE_UNSPECIFIED;
      app.displacement = 0;
    }
    if (app.known) {
      M68kLoopEntryRoot root = {0}; root.kind = M68K_LOOP_ROOT_ADDRESS; root.reg = reg;
      root.app = 1U; root.evidence = app.base_evidence_kind; root.app_displacement = app.displacement;
      entry.typed.addr_regs[reg].entry_value_id = counter_loop_add_root(&context, roots, &root_count, root, 4U);
    }
  }
  for (uint8_t reg = 0U; reg < 8U; ++reg) if (reg != candidate->counter && entry.typed.data_app_addr_regs[reg].known) {
    M68kRenderTypedAppAddressValue app = entry.typed.data_app_addr_regs[reg];
    M68kLoopEntryRoot root = {0}; root.kind = M68K_LOOP_ROOT_DATA; root.reg = reg;
    root.app = 1U; root.evidence = app.base_evidence_kind; root.app_displacement = app.displacement;
    entry.typed.data_regs[reg].entry_value_id = counter_loop_add_root(&context, roots, &root_count, root, 4U);
  }
  for (size_t i = 0U; i < entry.typed.base_slot_count; ++i) {
    M68kRenderTypedBaseSlot *slot = &entry.typed.base_slots[i];
    if (slot->known && slot->storage_id && slot->value.app_address_known) {
      M68kLoopEntryRoot root = {0}; root.kind = M68K_LOOP_ROOT_ABSOLUTE; root.storage_id = slot->storage_id;
      root.app = 1U; root.evidence = slot->value.app_base_evidence_kind; root.app_displacement = slot->value.app_displacement;
      slot->value.entry_value_id = counter_loop_add_root(&context, roots, &root_count, root, 4U);
    }
  }
  for (size_t i = 0U; i < entry.typed.stack_slot_count; ++i) {
    M68kRenderTypedStackSlot *slot = &entry.typed.stack_slots[i];
    if (slot->known && slot->value.app_address_known) {
      M68kLoopEntryRoot root = {0}; root.kind = M68K_LOOP_ROOT_STACK; root.displacement = slot->displacement;
      root.app = 1U; root.evidence = slot->value.app_base_evidence_kind; root.app_displacement = slot->value.app_displacement;
      slot->value.entry_value_id = counter_loop_add_root(&context, roots, &root_count, root, 4U);
    }
  }
  {
    M68kLoopEntryRoot root = {0}; root.kind = M68K_LOOP_ROOT_DATA; root.reg = candidate->counter;
    entry.typed.data_regs[root.reg].entry_value_id = counter_loop_add_root(&context, roots, &root_count, root, 2U);
    counter_root = root_count;
    root.kind = M68K_LOOP_ROOT_ADDRESS; root.reg = 7U;
    entry.typed.addr_regs[7].entry_value_id = counter_loop_add_root(&context, roots, &root_count, root, 4U);
    stack_root = root_count;
  }
  if (context.failed) goto allocation;
  queue = malloc(body_count * sizeof(*queue)); if (!queue) goto allocation;
  graph->nodes[candidate->header].typed_in = entry.typed;
  graph->nodes[candidate->header].platform_in = entry.platform;
  graph->nodes[candidate->header].has_in = 2U; queue[queue_count++] = candidate->header;
  while (queue_count) {
    size_t index = queue[queue_head];
    M68kRenderTypedFlowNode *node = &graph->nodes[index];
    queue_head = (queue_head + 1U) % body_count; --queue_count; node->has_in = 1U;
    if (index == candidate->tail) continue;
    counter_loop_project_registers(&node->typed_in, &context, roots, root_count);
    if (typed_flow_process_node(lookup, decode, accepted_start, section, node, 0, 0,
        &node->typed_out, &node->platform_out, NULL) != 0) goto allocation;
    ++transfers;
    if (step_trace && strtoul(step_trace, NULL, 0) == node->candidate->offset && traced_steps++ < 16U) {
      fprintf(stderr, "entry-step pc=%X", node->candidate->offset);
      for (size_t r = 0U; r < root_count; ++r)
        fprintf(stderr, " root%zu=%u/%u", r + 1U, counter_loop_root_at_tail(&node->typed_in, &roots[r]),
          counter_loop_root_at_tail(&node->typed_out, &roots[r]));
      fprintf(stderr, " stack_in=%zu stack_out=%zu", node->typed_in.stack_slot_count, node->typed_out.stack_slot_count);
      for (size_t k = 0U; k < node->typed_out.stack_slot_count; ++k)
        fprintf(stderr, " slot%d=%u:%u", node->typed_out.stack_slots[k].displacement,
          node->typed_out.stack_slots[k].value.entry_value_id, node->typed_out.stack_slots[k].caller_save_temporary);
      fputc('\n', stderr);
    }
    if (context.failed) goto allocation;
    for (uint8_t i = 0U; i < node->successor_count; ++i) {
      M68kRenderTypedFlowNode *next = &graph->nodes[node->successors[i]];
      int changed = !next->has_in;
      if (!next->has_in) { next->typed_in = node->typed_out; next->platform_in = node->platform_out; }
      else {
        changed |= typed_state_merge_into(&next->typed_in, &node->typed_out, lookup->policy);
        changed |= platform_state_merge_into(&next->platform_in, &node->platform_out);
      }
      if (changed && next->has_in != 2U) {
        queue[(queue_head + queue_count) % body_count] = node->successors[i]; ++queue_count; next->has_in = 2U;
        if (queue_count > peak_queue) peak_queue = queue_count;
      }
    }
  }
  if (!graph->nodes[candidate->tail].has_in) { reason = "tail_has_no_input"; goto cleanup; }
  for (size_t i = 0U; i < root_count; ++i) {
    const M68kAffineEntryValue *value = affine_entry_value(&context,
      counter_loop_root_at_tail(&graph->nodes[candidate->tail].typed_in, &roots[i]));
    if (!value || value->root != i + 1U) { lost_root = i + 1U; reason = "carried_value_lost_or_reassigned"; goto cleanup; }
    if ((i + 1U == counter_root || i + 1U == stack_root) && value->offset != 0) {
      reason = "counter_or_stack_changed"; goto cleanup;
    }
    roots[i].stride = value->offset;
  }
  /* No facts are promoted before the full invariant and every envelope pass. */
  for (size_t i = 0U; i < body_count; ++i) {
    size_t index = body[i]; M68kRenderTypedFlowNode *node = &graph->nodes[index];
    M68kInstructionIR instruction;
    if (index == candidate->tail || !node->has_in) continue;
    counter_loop_project_registers(&node->typed_in, &context, roots, root_count);
    if (m68k_decode_candidate_to_instruction(node->candidate, &instruction) != 0) goto allocation;
    for (size_t operand = 0U; operand < instruction.operand_count; ++operand) {
      uint8_t reg, access, width, element, count; int16_t displacement;
      const M68kAffineEntryValue *value;
      int64_t first, last, lo, hi;
      if (!typed_app_memory_span(lookup, &node->typed_in, &instruction, operand, &reg, &displacement,
          &access, &width, &element, &count) || access == M68K_APP_SLOT_ACCESS_ADDRESS) continue;
      value = affine_entry_value(&context, node->typed_in.addr_regs[reg].entry_value_id);
      if (!value || value->root > root_count || !roots[value->root - 1U].app) continue;
      const M68kLoopEntryRoot *root = &roots[value->root - 1U];
      first = (int64_t)root->app_displacement + value->offset + displacement;
      last = first + (int64_t)root->stride * (iterations - 1U);
      lo = first < last ? first : last; hi = (first > last ? first : last) + width;
      if (lo < 0 || hi > INT16_MAX + 1LL || hi - lo > UINT32_MAX ||
          !policy_declared_app_extent_covers(lookup->policy, (int16_t)lo, (uint32_t)(hi - lo))) {
        reason = "range_outside_declared_owner"; goto cleanup;
      }
      if (row_count == row_capacity) {
        size_t capacity = row_capacity ? row_capacity * 2U : 16U;
        M68kLoopRangeRow *grown;
        if (capacity < row_capacity || capacity > SIZE_MAX / sizeof(*grown)) goto allocation;
        grown = realloc(rows, capacity * sizeof(*grown)); if (!grown) goto allocation;
        rows = grown; row_capacity = capacity;
      }
      rows[row_count++] = (M68kLoopRangeRow){index, operand, reg, access, width, root->evidence, (int16_t)first, root->stride};
    }
  }
  for (size_t i = 0U; i < row_count; ++i) {
    const M68kLoopRangeRow *row = &rows[i];
    M68kRenderTypedFlowNode *node = &graph->nodes[row->node];
    M68kInstructionIR instruction;
    if (m68k_decode_candidate_to_instruction(node->candidate, &instruction) != 0 ||
        render_lookup_record_derived_app_operand(lookup, section->section_index, &node->typed_in,
          &instruction, node->candidate->offset, row->operand) != 0) goto allocation;
    for (size_t j = 0U; j < lookup->app_slot_ref_count; ++j) {
      M68kRenderAppSlotRef *ref = &lookup->app_slot_refs[j];
      if (ref->section_index == section->section_index && ref->ref.offset == node->candidate->offset &&
          ref->ref.operand_index == row->operand && ref->ref.base_reg == row->reg &&
          ref->ref.displacement == row->first && ref->ref.access_kind == row->access) {
        ref->ref.loop_iteration_count = iterations; ref->ref.loop_iteration_stride = row->stride;
        ref->ref.loop_header_offset = graph->nodes[candidate->header].candidate->offset;
        ref->ref.loop_tail_offset = graph->nodes[candidate->tail].candidate->offset;
        ref->ref.loop_counter_register = candidate->counter; break;
      }
    }
  }
  result = 1; reason = "proved"; goto cleanup;
allocation:
  result = -1; reason = "allocation_or_transfer_failure";
cleanup:
  {
    const char *trace = getenv("AMIGA_REVERSING_COUNTER_RELATIVE_TRACE");
    uint32_t header = graph->nodes[candidate->header].candidate->offset;
    if (trace && (!strcmp(trace, "*") || strtoul(trace, NULL, 0) == header))
      fprintf(stderr, "counter-relative section=%zu header=%X result=%d reason=%s nodes=%zu transfers=%zu roots=%zu rows=%zu peak_queue=%zu expression_bytes=%zu snapshot_bytes=%zu lost_root=%zu\n",
        section_index, header, result, reason, body_count, transfers, root_count, row_count, peak_queue,
        context.capacity * sizeof(*context.values) + context.index_capacity * sizeof(*context.index), snapshot_bytes, lost_root);
  }
  lookup->affine_entry_context = NULL;
  for (size_t i = 0U; i < body_count; ++i) graph->nodes[body[i]].has_in = graph->nodes[body[i]].has_out = 0U;
  affine_entry_destroy(&context); free(body); free(queue); free(rows); return result;
}

static int typed_flow_record_app_loop_ranges(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, M68kRenderTypedFlowWorkflow *workflow) {
  if (lookup->typed_flow_incomplete_count) return 0;
  for (size_t section_index = 0U; section_index < workflow->section_count; ++section_index) {
    M68kRenderTypedFlowGraph *graph = &workflow->graphs[section_index];
    M68kCounterLoopCandidate *candidates = NULL; size_t count = 0U, capacity = 0U, snapshot_bytes = 0U;
    int result = 0;
    /* Snapshot only potential external entry contexts before loaning the
     * existing CFG state storage. No second per-PC value/slot array exists. */
    for (size_t tail = 0U; tail < graph->node_count; ++tail) {
      M68kRenderTypedFlowNode *end = &graph->nodes[tail];
      M68kInstructionIR instruction; uint8_t counter; size_t header = SIZE_MAX;
      if (end->candidate->mnemonic_id != M68K_ASM_MNEMONIC_DBF || end->successor_count != 2U ||
          m68k_decode_candidate_to_instruction(end->candidate, &instruction) != 0 ||
          !operand_is_data_register_local(&instruction.operands[0], &counter)) continue;
      for (uint8_t i = 0U; i < end->successor_count; ++i)
        if (graph->nodes[end->successors[i]].candidate->offset < end->candidate->offset) header = end->successors[i];
      if (header == SIZE_MAX || graph->nodes[header].is_root) continue;
      size_t edges = graph->predecessor_offsets[header + 1U] - graph->predecessor_offsets[header];
      if (edges < 2U) continue;
      if (count == capacity) {
        size_t next = capacity ? capacity * 2U : 16U;
        M68kCounterLoopCandidate *grown;
        if (next < capacity || next > SIZE_MAX / sizeof(*grown)) { result = -1; goto done; }
        grown = realloc(candidates, next * sizeof(*grown)); if (!grown) { result = -1; goto done; }
        candidates = grown; capacity = next;
      }
      M68kCounterLoopCandidate *candidate = &candidates[count++];
      memset(candidate, 0, sizeof(*candidate)); candidate->header = header; candidate->tail = tail; candidate->counter = counter;
      candidate->entries = calloc(edges, sizeof(*candidate->entries));
      if (!candidate->entries) { result = -1; goto done; }
      for (size_t p = graph->predecessor_offsets[header]; p < graph->predecessor_offsets[header + 1U]; ++p) {
        size_t pred = graph->predecessors[p]; if (pred == tail) continue;
        M68kLoopEntryEdge *edge = &candidate->entries[candidate->entry_count++]; edge->node = pred;
        const M68kRenderTypedFlowNode *node = &graph->nodes[pred];
        const M68kHardwareWordSet *word = &node->platform_out.word_values[counter];
        if (node->has_out && word->count == 1U && !word->requires_input_contract) {
          edge->iterations = (uint32_t)word->values[0] + 1U;
          edge->snapshot = malloc(sizeof(*edge->snapshot));
          if (!edge->snapshot) { result = -1; goto done; }
          edge->snapshot->typed = node->typed_out; edge->snapshot->platform = node->platform_out;
          snapshot_bytes += sizeof(*edge->snapshot);
        }
      }
    }
    for (size_t i = 0U; i < graph->node_count; ++i) graph->nodes[i].has_in = graph->nodes[i].has_out = 0U;
    for (size_t i = 0U; i < count; ++i)
      if (counter_loop_prove(lookup, decode, accepted_start, section_index, graph, &candidates[i], snapshot_bytes) < 0) {
        result = -1; break;
      }
done:
    for (size_t i = 0U; i < count; ++i) {
      for (size_t j = 0U; j < candidates[i].entry_count; ++j) free(candidates[i].entries[j].snapshot);
      free(candidates[i].entries);
    }
    free(candidates); if (result) return result;
  }
  return 0;
}
