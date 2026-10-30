/* Counter-relative ranges are an induction over shared affine entry values.
 * A contributing root must have one fixed translation through the body;
 * unrelated lost roots cannot provide ranges. Counter and stack identities
 * remain mandatory. Retry edges join at the same PC, so unequal potentials
 * lose the identity. */
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
  uint8_t source;
  M68kRenderTypedMemoryBaseValue source_base;
  uint8_t address;
  uint8_t raw_count;
  uint32_t raw_values[4];
} M68kLoopEntryRoot;
#define M68K_LOOP_ROOT_DATA 1U
#define M68K_LOOP_ROOT_ADDRESS 2U
#define M68K_LOOP_ROOT_CELL 3U
#define M68K_LOOP_ROOT_STACK 4U
#define M68K_LOOP_ROOT_LIMIT (16U + M68K_RENDER_TYPED_BASE_SLOT_LIMIT + M68K_RENDER_TYPED_STACK_SLOT_LIMIT)

typedef struct M68kLoopRangeRow {
  size_t node, operand;
  uint8_t reg, access, width, evidence;
  int16_t first;
  int32_t stride;
  uint8_t source;
  size_t source_section;
  uint32_t source_first;
} M68kLoopRangeRow;

/* Structural field addresses and loaded pointer values are separate claims.
 * These rows retain the former only; they do not bypass the table-content
 * stability and canonical pointee binding used by source value domains. */
typedef struct M68kLoopFieldRow {
  uint32_t offset;
  uint8_t operand, reg;
  int16_t displacement, array_addend;
  uint16_t struct_size;
  int32_t base_cursor;
  M68kRenderResolvedStructField field;
  M68kRenderTypedProvenance provenance;
  M68kAddressValueTableOriginIR table_origin;
  M68kWordIndexAccessIR index;
} M68kLoopFieldRow;

static int counter_loop_field_row(const M68kRenderLookup *lookup,
    const M68kRenderTypedFlowNode *node, const M68kInstructionIR *instruction,
    size_t operand, uint8_t reg, int16_t displacement, uint8_t width,
    int64_t first_index, int64_t index_stride, uint32_t iterations,
    uint8_t counter, uint32_t header, uint32_t tail, M68kLoopFieldRow *row) {
  const M68kRenderTypedRegValue *base = &node->typed_in.addr_regs[reg];
  uint16_t size = lookup_policy_struct_size_by_id(lookup->policy, base->struct_id);
  uint16_t records = base->array_element_count ? base->array_element_count : 1U;
  uint16_t record = base->array_element_count ? base->array_element_index : 0U;
  int64_t encoded = (int64_t)record * size + base->byte_cursor + displacement;
  int64_t first = encoded + first_index;
  int64_t last = first + index_stride * (iterations - 1U);
  int64_t lo = first < last ? first : last, hi = first > last ? first : last;
  int64_t array_addend;
  if (!base->known || base->type_conflicted || !size || record >= records ||
      index_stride % size || lo < 0 || hi + width > (int64_t)records * size ||
      first % size > INT16_MAX ||
      !lookup_policy_resolve_struct_field(lookup->policy, base->struct_id, (int16_t)(first % size), width, &row->field) ||
      !row->field.field_expr[0]) return 0;
  array_addend = ((int64_t)base->byte_cursor + displacement) / size;
  if (array_addend < INT16_MIN || array_addend > INT16_MAX) return 0;
  row->offset = node->candidate->offset; row->operand = (uint8_t)operand; row->reg = reg;
  row->displacement = displacement; row->struct_size = size; row->base_cursor = base->byte_cursor;
  row->array_addend = (int16_t)array_addend; row->provenance = base->provenance;
  row->table_origin = base->table_origin;
  row->index.reg_kind = instruction->operands[operand].value.index_is_address
    ? M68K_ANALYSIS_REGISTER_ADDRESS : M68K_ANALYSIS_REGISTER_DATA;
  row->index.reg_index = instruction->operands[operand].value.index_reg;
  row->index.access_width = width; row->index.record_count = records; row->index.base_record_index = record;
  row->index.encoded_symbol_correction = (int32_t)((int64_t)base->byte_cursor + displacement -
    array_addend * size - row->field.offset);
  int64_t symbol_addend = -(int64_t)base->byte_cursor + row->index.encoded_symbol_correction;
  if (symbol_addend < INT32_MIN || symbol_addend > INT32_MAX) return 0;
  row->index.loop_index_first = (int32_t)first_index;
  row->index.loop_domain = (M68kAffineLoopDomainIR){header, tail, iterations,
    (int32_t)index_stride, width, 1U, counter, M68K_APP_SLOT_ACCESS_READ, 0U};
  return 1;
}

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
    if (entry && entry->coefficient == 1 && entry->width == 4U && entry->root <= root_count && roots[entry->root - 1U].source == 1U) {
      M68kRenderTypedMemoryBaseValue base = roots[entry->root - 1U].source_base;
      if (typed_memory_base_apply_affine_delta(&base, entry->offset)) {
        if (kind) state->memory_base_regs[reg] = base;
        else state->data_memory_base_regs[reg] = base;
      }
    }
    if (entry && entry->coefficient == 1 && entry->width == 4U && entry->root <= root_count && roots[entry->root - 1U].app == 1U) {
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
  if (root->kind == M68K_LOOP_ROOT_CELL) {
    const M68kRenderTypedBaseSlot *slot = typed_state_memory_cell(state, root->storage_id);
    return slot ? slot->value.entry_value_id : 0U;
  }
  if (root->kind == M68K_LOOP_ROOT_STACK) {
    const M68kRenderTypedStoredValue *value = typed_state_stack_slot_value(state, root->displacement);
    return value ? value->entry_value_id : 0U;
  }
  return 0U;
}

/* Conservative for 24-bit 68000 bus aliases, including sign-extended
 * absolute.W addresses. Wrapped envelopes are refused, never split/guessed. */
static int counter_loop_bus_span(int64_t first, int64_t last, uint32_t width,
    uint32_t *out_lo, uint32_t *out_hi) {
  int64_t lo = first < last ? first : last, hi = (first > last ? first : last) + width;
  if (!width || lo < 0 || hi > (int64_t)UINT32_MAX + 1 ||
      ((uint64_t)lo >> 24) != ((uint64_t)(hi - 1) >> 24)) return 0;
  *out_lo = (uint32_t)lo & 0xFFFFFFU;
  *out_hi = *out_lo + (uint32_t)(hi - lo);
  return 1;
}

static void counter_loop_capture_raw(M68kLoopEntryRoot *root, const M68kRenderTypedRegValue *value) {
  if (value->address_value_candidate_overflow) return;
  if (value->raw_long_value_known && value->raw_long_candidate_count <= 4U) {
    root->raw_count = value->raw_long_candidate_count ? value->raw_long_candidate_count : 1U;
    for (uint8_t i = 0U; i < root->raw_count; ++i)
      root->raw_values[i] = value->raw_long_candidate_count ? value->raw_long_candidates[i] : value->raw_long_value;
  } else if (value->pointer_value_known && value->pointer_candidate_count <= 4U) {
    root->raw_count = value->pointer_candidate_count ? value->pointer_candidate_count : 1U;
    for (uint8_t i = 0U; i < root->raw_count; ++i)
      root->raw_values[i] = value->pointer_candidate_count ? value->pointer_candidates[i] : value->pointer_value;
  }
}

static int counter_loop_source_write_disjoint(const M68kRenderLookup *lookup,
    const M68kRenderTypedFlowNode *node, const M68kInstructionIR *instruction, size_t operand,
    const M68kAffineEntryContext *context, const M68kLoopEntryRoot *roots, size_t root_count,
    uint32_t iterations, uint32_t protected_lo, uint32_t protected_hi) {
  uint8_t reg, access, width, element, count;
  int16_t displacement;
  uint32_t lo, hi, address;
  if (operand_absolute_offset_local(&instruction->operands[operand], &address)) {
    if (!platform_operand_memory_span(instruction, operand, &element, &count, &width) ||
        !counter_loop_bus_span(address, address, width, &lo, &hi)) return 0;
    return hi <= protected_lo || lo >= protected_hi;
  }
  if (!typed_register_memory_span(instruction, operand, &reg, &displacement, &access, &width, &element, &count))
    return 0;
  const M68kAffineEntryValue *value = affine_entry_value(context, node->typed_in.addr_regs[reg].entry_value_id);
  if (!value || value->coefficient != 1 || !value->root || value->root > root_count) return 0;
  const M68kLoopEntryRoot *root = &roots[value->root - 1U];
  int64_t relative = (int64_t)value->offset + displacement;
  int64_t final_relative = relative + (int64_t)root->stride * (iterations - 1U);
  if (root->source == 1U) {
    int64_t first = (int64_t)root->source_base.offset + relative;
    int64_t last = (int64_t)root->source_base.offset + final_relative;
    int64_t begin = first < last ? first : last, end = (first > last ? first : last) + width;
    if (begin < 0 || end > (int64_t)UINT32_MAX + 1 || end - begin > UINT32_MAX ||
        !lookup_source_unique_runtime_span(lookup, root->source_base.section_index, (uint32_t)begin,
          (uint32_t)(end - begin), &address) ||
        !counter_loop_bus_span(address, address, (uint32_t)(end - begin), &lo, &hi)) return 0;
    if (getenv("AMIGA_REVERSING_TRACE_SOURCE_CURSOR_DOMAINS"))
      fprintf(stderr, "source_write pc=%X reg=A%u root=%u source=%zu first=%lld last=%lld width=%u runtime=%X..%X protected=%X..%X\n",
        node->candidate->offset, reg, value->root, root->source_base.section_index,
        (long long)first, (long long)last, width, lo, hi, protected_lo, protected_hi);
    return hi <= protected_lo || lo >= protected_hi;
  }
  /* Raw addresses are used only with a carried app root proved invariant by
   * this pass. A first-iteration constant with no entry relation is not enough. */
  if ((root->app != 1U && root->address != 1U) || !root->raw_count) return 0;
  for (uint8_t i = 0U; i < root->raw_count; ++i) {
    if (!counter_loop_bus_span((int64_t)root->raw_values[i] + relative,
          (int64_t)root->raw_values[i] + final_relative, width, &lo, &hi) ||
        (hi > protected_lo && lo < protected_hi)) return 0;
  }
  return 1;
}

static int counter_loop_source_range_stable(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kRenderTypedFlowGraph *graph,
    const size_t *body, size_t body_count, const M68kCounterLoopCandidate *candidate,
    const M68kAffineEntryContext *context, const M68kLoopEntryRoot *roots, size_t root_count,
    const M68kLoopRangeRow *row, uint32_t iterations) {
  uint32_t address, table_lo, table_hi;
  int64_t last = (int64_t)row->source_first + (int64_t)row->stride * (iterations - 1U);
  int64_t first = row->source_first < last ? row->source_first : last;
  uint64_t width = (row->source_first > last ? row->source_first : last) + row->width - first;
  if (first < 0 || width > UINT32_MAX ||
      !lookup_source_unique_runtime_span(lookup, row->source_section, (uint32_t)first, (uint32_t)width, &address) ||
      !counter_loop_bus_span(address, address, (uint32_t)width, &table_lo, &table_hi)) return 0;
  for (size_t b = 0U; b < body_count; ++b) {
    const M68kRenderTypedFlowNode *node = &graph->nodes[body[b]];
    M68kInstructionIR instruction;
    if (body[b] == candidate->tail) continue;
    if (m68k_decode_candidate_to_instruction(node->candidate, &instruction)) return 0;
    if (instruction_has_call_flow_local(&instruction)) return 0;
    for (size_t operand = 0U; operand < instruction.operand_count; ++operand) {
      if (platform_operand_memory_access(&instruction, operand) != M68K_SIM_ACCESS_MEMORY_WRITE) continue;
      if (!counter_loop_source_write_disjoint(lookup, node, &instruction, operand, context, roots, root_count,
            iterations, table_lo, table_hi)) return 0;
      /* Writes must also preserve the very instructions used by this proof. */
      for (size_t c = 0U; c < body_count; ++c) {
        const M68kDecodeCandidate *code = graph->nodes[body[c]].candidate;
        uint32_t code_lo, code_hi;
        if (!lookup_source_unique_runtime_span(lookup, section->section_index, code->offset, code->byte_count, &address) ||
            !counter_loop_bus_span(address, address, code->byte_count, &code_lo, &code_hi) ||
            !counter_loop_source_write_disjoint(lookup, node, &instruction, operand, context, roots, root_count,
              iterations, code_lo, code_hi)) return 0;
      }
    }
  }
  return 1;
}

static int counter_loop_prove(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, size_t section_index, M68kRenderTypedFlowGraph *graph,
    const M68kCounterLoopCandidate *candidate, size_t snapshot_bytes) {
  const M68kDecodeSectionIR *section = &decode->sections[section_index];
  M68kAffineEntryContext context = {0};
  M68kLoopEntryRoot roots[M68K_LOOP_ROOT_LIMIT];
  M68kLoopEntrySnapshot entry;
  M68kLoopRangeRow *rows = NULL;
  M68kLoopFieldRow *fields = NULL;
  size_t field_count = 0U, field_capacity = 0U;
  size_t row_count = 0U, row_capacity = 0U;
  size_t *body = NULL, body_count = 0U, body_capacity = 0U, *queue = NULL;
  size_t queue_head = 0U, queue_count = 0U, peak_queue = 0U, transfers = 0U, root_count = 0U;
  size_t counter_root = 0U, stack_root = 0U, lost_root = 0U;
  uint32_t iterations = 0U;
  const char *reason = "unknown_entry";
  int result = 0, found_entry = 0, source_call = 0;
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
        metadata->flow_kind == M68K_SIM_FLOW_TRAP) {
      reason = "unresolved_or_nested_exit"; goto cleanup;
    }
    if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_DBF) {
      uint8_t inner_counter;
      if (!operand_is_data_register_local(&instruction.operands[0], &inner_counter) || inner_counter == candidate->counter) {
        reason = "nested_counter_overlap"; goto cleanup;
      }
    }
    if (instruction_has_call_flow_local(&instruction)) source_call = 1;
    if (metadata->flow_kind == M68K_SIM_FLOW_BRANCH || metadata->flow_kind == M68K_SIM_FLOW_JUMP) {
      uint32_t target;
      if (!typed_flow_first_local_control_target(lookup, section, node->candidate, &target)) {
        reason = "unresolved_control_target"; goto cleanup;
      }
    }
    for (size_t j = 0U; j < node->successor_count; ++j) {
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
      counter_loop_capture_raw(&root, &entry.typed.addr_regs[reg]);
      entry.typed.addr_regs[reg].entry_value_id = counter_loop_add_root(&context, roots, &root_count, root, 4U);
    }
  }
  for (uint8_t reg = 0U; reg < 8U; ++reg) if (reg != candidate->counter && entry.typed.data_app_addr_regs[reg].known) {
    M68kRenderTypedAppAddressValue app = entry.typed.data_app_addr_regs[reg];
    M68kLoopEntryRoot root = {0}; root.kind = M68K_LOOP_ROOT_DATA; root.reg = reg;
    root.app = 1U; root.evidence = app.base_evidence_kind; root.app_displacement = app.displacement;
    entry.typed.data_regs[reg].entry_value_id = counter_loop_add_root(&context, roots, &root_count, root, 4U);
  }
  /* Source identities share the same affine entry algebra as app cursors.
   * Numeric equality never joins roots from distinct entry registers. */
  for (uint8_t kind = 0U; kind < 2U; ++kind) for (uint8_t reg = 0U; reg < (kind ? 7U : 8U); ++reg) {
    M68kRenderTypedRegValue *value = kind ? &entry.typed.addr_regs[reg] : &entry.typed.data_regs[reg];
    const M68kRenderTypedMemoryBaseValue *base = kind ? &entry.typed.memory_base_regs[reg] :
      &entry.typed.data_memory_base_regs[reg];
    if (value->entry_value_id || (!kind && reg == candidate->counter)) continue;
    M68kLoopEntryRoot root = {0}; root.kind = kind ? M68K_LOOP_ROOT_ADDRESS : M68K_LOOP_ROOT_DATA;
    root.reg = reg;
    if (base->known && base->affine_known) { root.source = 1U; root.source_base = *base; }
    else if (kind) {
      counter_loop_capture_raw(&root, value);
      if (!root.raw_count) continue;
      root.address = 1U;
    } else continue;
    value->entry_value_id = counter_loop_add_root(&context, roots, &root_count, root, 4U);
  }
  for (size_t i = 0U; i < entry.typed.base_slot_count; ++i) {
    M68kRenderTypedBaseSlot *slot = &entry.typed.base_slots[i];
    if (slot->known && slot->storage_id && slot->value.app_address_known) {
      M68kLoopEntryRoot root = {0}; root.kind = M68K_LOOP_ROOT_CELL; root.storage_id = slot->storage_id;
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
    for (size_t i = 0U; i < node->successor_count; ++i) {
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
    if (!value || value->coefficient != 1 || value->root != i + 1U) {
      if (roots[i].source || roots[i].address || roots[i].app) {
        if (roots[i].source) roots[i].source = 2U;
        if (roots[i].address) roots[i].address = 2U;
        if (roots[i].app) roots[i].app = 2U;
        continue;
      }
      lost_root = i + 1U; reason = "carried_value_lost_or_reassigned"; goto cleanup;
    }
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
      int64_t first, last, lo, hi, index_first = 0, index_stride = 0;
      int indexed = 0;
      if (!typed_register_memory_span(&instruction, operand, &reg, &displacement,
          &access, &width, &element, &count)) {
        const M68kOperandIR *ea = &instruction.operands[operand];
        const M68kAffineEntryValue *index;
        uint32_t contribution;
        int32_t encoded = (int32_t)ea->value.value;
        if (m68k_instruction_operand_decoded_ea_shape(ea) != M68K_SIM_EA_SHAPE_INDEX ||
            !m68k_sim_operand_word_index_value(&instruction, operand, 0U, &contribution) ||
            ea->value.ea_reg >= 7U || encoded < INT16_MIN || encoded > INT16_MAX ||
            !platform_operand_memory_span(&instruction, operand, &width, &count, NULL) ||
            width != 4U || count != 1U) continue;
        access = app_slot_access_kind_from_instruction(&instruction, operand);
        if (access != M68K_APP_SLOT_ACCESS_READ) continue;
        index = affine_entry_value(&context, ea->value.index_is_address
          ? node->typed_in.addr_regs[ea->value.index_reg].entry_value_id
          : node->typed_in.data_regs[ea->value.index_reg].entry_value_id);
        if (!index || index->root != counter_root || index->width != 2U) continue;
        /* The body leaves the WORD counter unchanged; DBF decrements it at
         * the boundary. Keep the signed WORD contribution linear only when
         * the entire proven sequence avoids sign/wrap discontinuities. */
        index_first = (int64_t)index->coefficient * (iterations - 1U) + index->offset;
        if (index_first < INT16_MIN || index_first > INT16_MAX ||
            !m68k_sim_operand_word_index_value(&instruction, operand, (uint32_t)index_first, &contribution) ||
            (int32_t)contribution != index_first ||
            !m68k_sim_operand_word_index_value(&instruction, operand, (uint32_t)index->offset, &contribution) ||
            (int32_t)contribution != index->offset) continue;
        index_stride = -(int64_t)index->coefficient;
        reg = ea->value.ea_reg; displacement = (int16_t)encoded; indexed = 1;
      }
      if (access == M68K_APP_SLOT_ACCESS_ADDRESS) continue;
      value = affine_entry_value(&context, node->typed_in.addr_regs[reg].entry_value_id);
      if (!value || value->coefficient != 1 || value->root > root_count) continue;
      const M68kLoopEntryRoot *root = &roots[value->root - 1U];
      if (indexed && root->source == 1U && root->stride == 0) {
        M68kLoopFieldRow field = {0};
        if (counter_loop_field_row(lookup, node, &instruction, operand, reg, displacement, width,
            index_first, index_stride, iterations, candidate->counter,
            graph->nodes[candidate->header].candidate->offset,
            graph->nodes[candidate->tail].candidate->offset, &field)) {
          if (field_count == field_capacity) {
            size_t capacity = field_capacity ? field_capacity * 2U : 16U;
            M68kLoopFieldRow *grown;
            if (capacity < field_capacity || capacity > SIZE_MAX / sizeof(*grown)) goto allocation;
            grown = realloc(fields, capacity * sizeof(*grown)); if (!grown) goto allocation;
            fields = grown; field_capacity = capacity;
          }
          fields[field_count++] = field;
        }
      }
      if (root->source == 1U) {
        const M68kAnalysisStructuredDataItem *table;
        if (source_call || access != M68K_APP_SLOT_ACCESS_READ || width != 4U || count != 1U ||
            !typed_pointer_read_operand_supported(&instruction, operand)) continue;
        table = lookup_pointer_table_item_for_contract(lookup, root->source_base.pointer_table_section_index,
          root->source_base.pointer_table_offset, root->source_base.pointer_table_size);
        if (!root->source_base.pointer_table_known || !table) continue;
        int64_t stride = (int64_t)root->stride + index_stride;
        if (stride < INT32_MIN || stride > INT32_MAX) continue;
        first = (int64_t)root->source_base.offset + value->offset + displacement + index_first;
        last = first + stride * (iterations - 1U);
        lo = first < last ? first : last; hi = (first > last ? first : last) + width;
        if (lo < table->offset || hi > (int64_t)table->offset + table->size ||
            ((first - table->offset) % 4) || stride % 4) continue;
        if (row_count == row_capacity) {
          size_t capacity = row_capacity ? row_capacity * 2U : 16U;
          M68kLoopRangeRow *grown;
          if (capacity < row_capacity || capacity > SIZE_MAX / sizeof(*grown)) goto allocation;
          grown = realloc(rows, capacity * sizeof(*grown)); if (!grown) goto allocation;
          rows = grown; row_capacity = capacity;
        }
        M68kLoopRangeRow row = {0}; row.node = index; row.operand = operand; row.reg = reg;
        row.access = access; row.width = width; row.stride = (int32_t)stride; row.source = 1U;
        row.source_section = root->source_base.section_index; row.source_first = (uint32_t)first;
        rows[row_count++] = row;
        continue;
      }
      if (indexed) continue; /* No new app-owner/index inference in this slice. */
      if (root->app != 1U || !typed_app_memory_span(lookup, &node->typed_in, &instruction, operand, &reg,
          &displacement, &access, &width, &element, &count)) continue;
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
  for (size_t i = 0U; i < field_count; ++i) {
    const M68kLoopFieldRow *field = &fields[i];
    if (render_lookup_add_typed_access_by_names(lookup, section->section_index, field->offset,
        field->operand, field->reg, field->displacement, field->struct_size, field->array_addend,
        field->base_cursor, 0U, &field->field, &field->provenance, &field->table_origin,
        &field->index) != 0) goto allocation;
  }
  for (size_t i = 0U; i < row_count; ++i) {
    const M68kLoopRangeRow *row = &rows[i];
    M68kRenderTypedFlowNode *node = &graph->nodes[row->node];
    M68kInstructionIR instruction;
    if (row->source) {
      if (!counter_loop_source_range_stable(lookup, section, graph, body, body_count, candidate,
          &context, roots, root_count, row, iterations)) continue;
      M68kRenderTypedMemoryBaseValue base = node->typed_in.memory_base_regs[row->reg];
      int32_t displacement = (int32_t)((int64_t)row->source_first - base.offset);
      if (render_lookup_add_affine_address_use(lookup, section->section_index, node->candidate->offset,
          (uint8_t)row->operand, row->reg, &base, displacement)) goto allocation;
      for (size_t j = 0U; j < lookup->affine_address_use_count; ++j) {
        M68kRenderAffineAddressUse *use = &lookup->affine_address_uses[j];
        if (use->section_index != section->section_index || use->offset != node->candidate->offset ||
            use->operand_index != row->operand || use->target_section_index != row->source_section ||
            use->target_offset != row->source_first) continue;
        M68kAffineLoopDomainIR domain = {0}; domain.state = 1U;
        domain.header_offset = graph->nodes[candidate->header].candidate->offset;
        domain.tail_offset = graph->nodes[candidate->tail].candidate->offset;
        domain.iteration_count = iterations; domain.iteration_stride = row->stride;
        domain.access_width = row->width; domain.counter_register = candidate->counter;
        domain.access_kind = row->access;
        if (use->loop_domain.state && memcmp(&use->loop_domain, &domain, sizeof(domain)))
          use->loop_domain.state = 2U;
        else use->loop_domain = domain;
      }
      continue;
    }
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
  affine_entry_destroy(&context); free(body); free(queue); free(rows); free(fields); return result;
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
      for (size_t i = 0U; i < end->successor_count; ++i)
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
