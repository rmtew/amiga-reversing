/* Correlated projections of one closed source-record read. This extends the
 * existing value packets and CFG must joins, not a second transfer engine.
 * Original bytes are usable only before the existing absolute-write barrier.
 * No source discriminator invariant is inferred for abstract writable inputs. */
static size_t typed_read_hash(const M68kRenderScalarReadRelation *read, size_t capacity) {
  const unsigned char *bytes = (const unsigned char *)read;
  uint32_t hash = UINT32_C(2166136261);
  for (size_t i = 0U; i < sizeof(*read); ++i) hash = (hash ^ bytes[i]) * UINT32_C(16777619);
  return hash & (capacity - 1U);
}

static uint16_t typed_read_intern(M68kRenderLookup *lookup, const M68kRenderScalarReadRelation *read) {
  size_t at;
  if (lookup->scalar_read_index_capacity) {
    at = typed_read_hash(read, lookup->scalar_read_index_capacity);
    while (lookup->scalar_read_index[at]) {
      size_t id = lookup->scalar_read_index[at];
      if (!memcmp(&lookup->scalar_read_relations[id - 1U], read, sizeof(*read))) return (uint16_t)(id * 2U);
      at = (at + 1U) & (lookup->scalar_read_index_capacity - 1U);
    }
  }
  /* Two projection tags share a uint16_t handle. Exhaustion drops precision. */
  if (lookup->scalar_read_relation_count >= UINT16_MAX / 2U) return 0U;
  if (lookup->scalar_read_relation_count >= lookup->scalar_read_index_capacity / 2U) {
    size_t capacity = lookup->scalar_read_index_capacity ? lookup->scalar_read_index_capacity * 2U : 32U;
    size_t *index = arena_calloc(lookup->arena, capacity, sizeof(*index));
    if (!index) return 0U;
    for (size_t i = 0U; i < lookup->scalar_read_relation_count; ++i) {
      at = typed_read_hash(&lookup->scalar_read_relations[i], capacity);
      while (index[at]) at = (at + 1U) & (capacity - 1U);
      index[at] = i + 1U;
    }
    lookup->scalar_read_index = index; lookup->scalar_read_index_capacity = capacity;
  }
  if (lookup->scalar_read_relation_count == lookup->scalar_read_relation_capacity) {
    size_t capacity = lookup->scalar_read_relation_capacity ? lookup->scalar_read_relation_capacity * 2U : 16U;
    M68kRenderScalarReadRelation *grown = render_lookup_grow_array(lookup, lookup->scalar_read_relations,
      lookup->scalar_read_relation_count, sizeof(*grown), capacity);
    if (!grown) return 0U;
    lookup->scalar_read_relations = grown; lookup->scalar_read_relation_capacity = capacity;
  }
  at = typed_read_hash(read, lookup->scalar_read_index_capacity);
  while (lookup->scalar_read_index[at]) at = (at + 1U) & (lookup->scalar_read_index_capacity - 1U);
  lookup->scalar_read_relations[lookup->scalar_read_relation_count] = *read;
  lookup->scalar_read_index[at] = ++lookup->scalar_read_relation_count;
  return (uint16_t)(lookup->scalar_read_relation_count * 2U);
}

#define TYPED_READ_VISIT_VALUES(state, operation) do { \
  for (size_t r = 0U; r < 8U; ++r) { operation(&(state)->data_regs[r]); operation(&(state)->addr_regs[r]); } \
  for (size_t r = 0U; r < (state)->stack_slot_count; ++r) operation(&(state)->stack_slots[r].value); \
  for (size_t r = 0U; r < (state)->base_slot_count; ++r) operation(&(state)->base_slots[r].value); \
  for (size_t r = 0U; r < (state)->field_slot_count; ++r) operation(&(state)->field_slots[r].value); \
} while (0)

/* A captured predicate depends on the scalar field that was read, not on every
 * byte of its enclosing allocation. Ownership/type membership was established
 * at capture; a disjoint data write neither moves that allocation nor changes
 * the captured discriminator. This does not permit fresh source-byte reads
 * after mutation or grant a writable-format invariant. */
static int typed_read_overlaps_write(const M68kRenderLookup *lookup,
    const M68kRenderScalarReadRelation *read, uint32_t address, uint8_t span) {
  uint64_t end = (uint64_t)address + span;
  if (read->source_domain_id) {
    const M68kRenderSourceDomain *domain = &lookup->source_domains[read->source_domain_id - 1U];
    if ((uint64_t)address >= domain->address_end || end <= domain->address_min) return 0;
    for (size_t i = 0U; i < domain->member_count; ++i) {
      uint64_t field = (uint64_t)domain->members[i].address + read->field_cursor;
      if ((uint64_t)address < field + 2U && field < end) return 1;
    }
  } else for (uint8_t i = 0U; i < read->count; ++i) {
    uint64_t field = (uint64_t)read->roots[i] + read->field_cursor;
    if ((uint64_t)address < field + 2U && field < end) return 1;
  }
  return 0;
}

/* Ordinary writes kill correlations unless a canonical source-mapped footprint
 * proves disjointness from every contributing predicate field. Unknown SP is not a
 * non-alias promise. Shared stack normalization owns predecrement width/order. */
static void typed_read_note_writes(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *meta = m68k_sim_metadata_for_instruction(instruction);
  M68kStackRegisterTransfer normalized_stack;
  int opaque = !meta || instruction_has_call_flow_local(instruction) ||
    (meta->sp_effect_count && meta->flow_kind != M68K_SIM_FLOW_RETURN &&
      !platform_instruction_stack_register_transfer(instruction, &normalized_stack)) ||
    meta->flow_kind == M68K_SIM_FLOW_TRAP;
  if (opaque) state->memory_write_barriers |= M68K_CELL_WRITTEN_ABSOLUTE;
  for (size_t op = 0U; opaque || (meta && op < instruction->operand_count && op < 4U); ++op) {
    uint32_t address = 0U; uint8_t span = 0U, reg; int16_t displacement;
    int known = 0;
    if (!opaque) {
      const M68kOperandIR *operand = &instruction->operands[op];
      M68kRenderTypedMemoryBaseValue location;
      M68kStackRegisterTransfer stack;
      if (meta->operand_access_kinds[op] != M68K_SIM_ACCESS_MEMORY_WRITE ||
          m68k_instruction_operand_decoded_ea_shape(operand) == M68K_SIM_EA_SHAPE_NONE) continue;
      if (platform_operand_memory_span(instruction, op, NULL, NULL, &span)) {
        if (operand_is_address_memory_local(operand, &reg, &displacement) &&
            typed_memory_base_with_displacement(&state->memory_base_regs[reg], displacement, &location))
          known = lookup_source_unique_runtime_span(lookup, location.section_index, location.offset, span, &address);
        else if (m68k_instruction_operand_decoded_ea_shape(operand) == M68K_SIM_EA_SHAPE_PREDECREMENT &&
            platform_instruction_stack_register_transfer(instruction, &stack) &&
            stack.direction == M68K_STACK_TRANSFER_PUSH &&
            typed_memory_base_with_displacement(&state->memory_base_regs[7], -(int32_t)span, &location))
          known = lookup_source_unique_runtime_span(lookup, location.section_index, location.offset, span, &address);
      }
    }
#define INVALIDATE_READ(value) do { \
  uint16_t id = (value)->read_relation / 2U; \
  if (id && id <= lookup->scalar_read_relation_count) { \
    const M68kRenderScalarReadRelation *read = &lookup->scalar_read_relations[id - 1U]; \
    int kill = !known || typed_read_overlaps_write(lookup, read, address, span); \
    if (kill) { \
      if (state->zero_read_relation / 2U == id) state->zero_read_relation = 0U; \
      (value)->read_relation = 0U; \
    } \
  } \
} while (0)
    TYPED_READ_VISIT_VALUES(state, INVALIDATE_READ);
#undef INVALIDATE_READ
    if (opaque) break;
  }
}

static uint32_t typed_read_source_domain(const M68kRenderLookup *lookup,
    const M68kRenderTypedRegValue *base) {
  if (!base->table_origin.has_origin || base->provenance.kind != M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA ||
      base->provenance.merge_conflicted) return 0U;
  for (size_t i = 0U; i < lookup->source_domain_count; ++i) {
    const M68kRenderSourceDomain *domain = &lookup->source_domains[i];
    if (domain->struct_id == base->struct_id &&
        domain->producer.section_index == base->provenance.section_index &&
        domain->producer.offset == base->provenance.offset &&
        domain->producer.producer_operand_index == base->provenance.producer_operand_index &&
        domain->origin.table_section_index == base->table_origin.table_section_index &&
        domain->origin.table_start_offset == base->table_origin.table_start_offset) return (uint32_t)i + 1U;
  }
  return 0U;
}

static int typed_read_domain_partition(const M68kRenderLookup *lookup, const M68kRenderSourceDomain *domain,
    int32_t cursor, uint16_t *zero_type, uint16_t *nonzero_type) {
  int have_zero = 0, have_nonzero = 0;
  *zero_type = *nonzero_type = AMIGA_OS_STRUCT_ID_NONE;
  for (size_t i = 0U; i < domain->member_count; ++i) {
    const M68kRenderSourceDomainMember *member = &domain->members[i];
    const M68kSection *source = &lookup->object->sections[member->section_index];
    if (cursor < 0 || (uint64_t)cursor + 2U > member->size || !source->data ||
        member->offset > source->size || (uint64_t)cursor + 2U > source->size - member->offset) return 0;
    const uint8_t *bytes = source->data + member->offset + cursor;
    if (!bytes[0] && !bytes[1]) {
      *zero_type = have_zero ? typed_struct_id_common_merge(lookup->policy, *zero_type, member->struct_id) : member->struct_id;
      have_zero = 1;
    } else {
      *nonzero_type = have_nonzero ? typed_struct_id_common_merge(lookup->policy, *nonzero_type, member->struct_id) : member->struct_id;
      have_nonzero = 1;
    }
  }
  return (!have_zero || *zero_type != AMIGA_OS_STRUCT_ID_NONE) &&
    (!have_nonzero || *nonzero_type != AMIGA_OS_STRUCT_ID_NONE);
}

static void typed_read_defer_source_domain(M68kRenderLookup *lookup, const M68kRenderTypedRegValue *base,
    int32_t cursor) {
  if (lookup->source_domain_pass_done || lookup->suppress_address_value_observations ||
      !base->table_origin.has_origin || base->provenance.kind != M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA ||
      base->provenance.merge_conflicted) return;
  /* Only the converged recording epoch appends requests; it visits each read
   * once. Reset requests with that epoch, rather than quadratic dedup scans. */
  if (lookup->source_read_request_count == lookup->source_read_request_capacity) {
    size_t capacity = lookup->source_read_request_capacity ? lookup->source_read_request_capacity * 2U : 16U;
    M68kRenderSourceReadRequest *grown = render_lookup_grow_array(lookup, lookup->source_read_requests,
      lookup->source_read_request_count, sizeof(*grown), capacity);
    if (!grown) { lookup->source_domain_error = 1U; return; }
    lookup->source_read_requests = grown; lookup->source_read_request_capacity = capacity;
  }
  M68kRenderSourceReadRequest *request = &lookup->source_read_requests[lookup->source_read_request_count++];
  memset(request, 0, sizeof(*request)); request->producer = base->provenance;
  request->origin = base->table_origin; request->struct_id = base->struct_id; request->field_cursor = cursor;
}

static uint16_t typed_read_capture(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    const M68kInstructionIR *instruction, uint8_t operand_index, size_t section_index, uint32_t offset) {
  M68kRenderScalarReadRelation read;
  memset(&read, 0, sizeof(read));
  M68kRenderResolvedStructField field;
  uint8_t base_reg; int16_t displacement; int64_t field_cursor;
  M68kRenderTypedRegValue *base;
  uint16_t handle;
  if (!lookup || !state || !state->source_snapshot_entry ||
      state->memory_write_barriers & M68K_CELL_WRITTEN_ABSOLUTE || lookup->affine_entry_context ||
      operand_index >= instruction->operand_count || m68k_sim_operand_width_bytes(instruction, operand_index) != 2U ||
      operand_index >= 4U) return 0U;
  if (!operand_is_address_memory_local(&instruction->operands[operand_index], &base_reg, &displacement)) {
    uint8_t update_width;
    if (m68k_instruction_operand_decoded_ea_shape(&instruction->operands[operand_index]) !=
          M68K_SIM_EA_SHAPE_POSTINCREMENT ||
        !typed_single_auto_update_cursor(lookup, state, instruction, operand_index, &base_reg, &update_width))
      return 0U;
    displacement = 0;
  }
  if (base_reg >= 7U) return 0U;
  base = &state->addr_regs[base_reg];
  if (!base->known || base->type_conflicted || base->address_value_candidate_overflow) return 0U;
  field_cursor = (int64_t)base->byte_cursor + displacement;
  if (field_cursor < 0 || field_cursor > INT16_MAX ||
      !lookup_policy_resolve_struct_field(lookup->policy, base->struct_id, (int16_t)field_cursor, 2U, &field) ||
      field.offset != field_cursor || field.size != 2U) return 0U;
  read.section_index = section_index; read.offset = offset; read.field_cursor = (int32_t)field_cursor;
  if (!base->pointer_value_known || !base->pointer_candidate_count) {
    read.source_domain_id = typed_read_source_domain(lookup, base);
    if (!read.source_domain_id) { typed_read_defer_source_domain(lookup, base, (int32_t)field_cursor); return 0U; }
    if (!typed_read_domain_partition(lookup, &lookup->source_domains[read.source_domain_id - 1U],
        (int32_t)field_cursor, &read.zero_type, &read.nonzero_type)) return 0U;
  } else {
    if (base->pointer_candidate_count > 4U) return 0U;
    read.count = base->pointer_candidate_count;
  }
  for (uint8_t i = 0U; i < read.count; ++i) {
    uint32_t root = base->pointer_candidates[i], mapped = 0U;
    size_t source_section = SIZE_MAX; uint32_t source_offset = 0U;
    uint16_t type, conflict = AMIGA_OS_STRUCT_ID_NONE; int32_t cursor;
    for (size_t si = 0U; si < lookup->section_count; ++si) {
      uint32_t candidate;
      if (analysis_lookup_materialized_runtime_address_source_offset(lookup, si, root, &candidate)) {
        if (source_section != SIZE_MAX) return 0U;
        source_section = si; source_offset = candidate;
      }
    }
    if (source_section == SIZE_MAX ||
        !lookup_source_unique_runtime_span(lookup, source_section, source_offset, (uint32_t)field_cursor + 2U, &mapped) ||
        mapped != root) return 0U;
    type = lookup_policy_struct_id_for_static_data_target(lookup, source_section, source_offset,
      NULL, NULL, &cursor, &conflict);
    if (type == AMIGA_OS_STRUCT_ID_NONE || conflict != AMIGA_OS_STRUCT_ID_NONE || cursor ||
        typed_struct_id_common_merge(lookup->policy, type, base->struct_id) != base->struct_id ||
        field_cursor + 2U > lookup_policy_struct_size_by_id(lookup->policy, type)) return 0U;
    const M68kSection *source = &lookup->object->sections[source_section];
    if (!source->data || source_offset > source->size || field_cursor + 2U > source->size - source_offset) return 0U;
    read.roots[i] = root; read.types[i] = type;
    const uint8_t *bytes = source->data + source_offset + (uint32_t)field_cursor;
    read.values[i] = ((uint16_t)bytes[0] << 8U) | bytes[1];
  }
  handle = typed_read_intern(lookup, &read);
  if (!handle) return 0U;
  /* A descriptor denotes this read occurrence, not a value from an earlier
   * loop iteration. Kill both old projections before binding the new pair. */
#define KILL_READ(value) do { if (((value)->read_relation & ~1U) == handle) (value)->read_relation = 0U; } while (0)
  TYPED_READ_VISIT_VALUES(state, KILL_READ);
#undef KILL_READ
  if ((state->zero_read_relation & ~1U) == handle) state->zero_read_relation = 0U;
  uint8_t root_alias = typed_register_alias_root(state, (uint8_t)(base_reg + 8U));
  for (uint8_t r = 0U; r < 8U; ++r) {
    if (typed_register_alias_root(state, r) == root_alias) state->data_regs[r].read_relation = handle;
    if (typed_register_alias_root(state, (uint8_t)(r + 8U)) == root_alias) state->addr_regs[r].read_relation = handle;
  }
  return (uint16_t)(handle | 1U);
}

static void typed_read_predicate_after(M68kRenderTypedState *state, const M68kInstructionIR *instruction,
    uint16_t direct_test_relation) {
  const M68kSimFormMetadata *meta = m68k_sim_metadata_for_instruction(instruction);
  uint8_t reg = 0U; uint16_t relation = 0U;
  if (!meta || meta->flow_kind == M68K_SIM_FLOW_CALL) { state->zero_read_relation = 0U; return; }
  if (meta->operation_type == M68K_SIM_OP_TEST && meta->source_operand_index < instruction->operand_count &&
      m68k_sim_operand_width_bytes(instruction, meta->source_operand_index) == 2U) {
    relation = direct_test_relation;
    if (operand_is_data_register_local(&instruction->operands[meta->source_operand_index], &reg))
      relation = state->data_regs[reg].read_relation;
  } else if (meta->operation_type == M68K_SIM_OP_MOVE && meta->ccr_formula == M68K_SIM_CCR_FORMULA_MOVE_FLAGS &&
      meta->dest_operand_index < instruction->operand_count &&
      m68k_sim_operand_width_bytes(instruction, meta->dest_operand_index) == 2U) {
    if (operand_is_data_register_local(&instruction->operands[meta->dest_operand_index], &reg))
      relation = state->data_regs[reg].read_relation;
    else if (meta->source_operand_index < instruction->operand_count) {
      /* MOVE to memory sets Z from the transferred WORD too. The shared write
       * footprint has already invalidated aliases; do not invent a relation
       * for an unknown memory source or a partial-width transfer. */
      const M68kOperandIR *source = &instruction->operands[meta->source_operand_index];
      if (operand_is_data_register_local(source, &reg)) relation = state->data_regs[reg].read_relation;
      else if (operand_address_register_index_local(source, &reg)) relation = state->addr_regs[reg].read_relation;
    }
  } else if (meta->operation_type == M68K_SIM_OP_COMPARE && meta->source_operand_index < instruction->operand_count &&
      meta->dest_operand_index < instruction->operand_count &&
      m68k_sim_operand_width_bytes(instruction, meta->dest_operand_index) == 2U) {
    uint32_t value;
    if (m68k_ir_operand_immediate_value(&instruction->operands[meta->source_operand_index], &value) && !value &&
        operand_is_data_register_local(&instruction->operands[meta->dest_operand_index], &reg))
      relation = state->data_regs[reg].read_relation;
  } else if (meta->ccr_formula == M68K_SIM_CCR_FORMULA_NONE &&
      (meta->operation_type == M68K_SIM_OP_NOP || meta->operation_type == M68K_SIM_OP_MOVE_MULTIPLE ||
       meta->operation_class == M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS || meta->flow_kind == M68K_SIM_FLOW_BRANCH ||
       meta->flow_kind == M68K_SIM_FLOW_JUMP ||
       (meta->operation_type == M68K_SIM_OP_MOVE && meta->dest_operand_index < instruction->operand_count &&
        operand_address_register_index_local(&instruction->operands[meta->dest_operand_index], &reg)))) return;
  state->zero_read_relation = (relation & 1U) ? relation : 0U;
}

static void typed_read_refine_edge(const M68kRenderLookup *lookup, const M68kRenderTypedFlowNode *predecessor,
    const M68kRenderTypedFlowNode *successor, M68kRenderTypedState *state) {
  M68kInstructionIR branch; int zero, taken;
  uint16_t handle = (uint16_t)(state->zero_read_relation & ~1U);
  uint32_t roots[4] = {0}; uint16_t type = AMIGA_OS_STRUCT_ID_NONE; uint8_t count = 0U;
  if (!handle || handle / 2U > lookup->scalar_read_relation_count ||
      m68k_decode_candidate_to_instruction(predecessor->candidate, &branch)) return;
  taken = successor->candidate->offset != predecessor->candidate->offset + predecessor->candidate->byte_count;
  if (!m68k_sim_branch_zero_requirement(&branch, taken, &zero)) return;
  const M68kRenderScalarReadRelation *read = &lookup->scalar_read_relations[handle / 2U - 1U];
  for (uint8_t i = 0U; i < read->count; ++i) if ((read->values[i] == 0U) == zero) {
    roots[count++] = read->roots[i];
    type = count == 1U ? read->types[i] : typed_struct_id_common_merge(lookup->policy, type, read->types[i]);
  }
  if (read->source_domain_id) type = zero ? read->zero_type : read->nonzero_type;
  /* Impossible edges remain conservatively unrefined; no reachability claim. */
  if ((!read->source_domain_id && (!count || count == read->count)) || type == AMIGA_OS_STRUCT_ID_NONE) return;
#define REFINE_READ(value) do { \
  if ((value)->read_relation == handle && !(value)->address_value_candidate_overflow) { \
    if ((value)->pointer_value_known) { \
      uint32_t intersection[4] = {0}; uint8_t used = 0U; \
      for (uint8_t j = 0U; j < (value)->pointer_candidate_count; ++j) \
        for (uint8_t i = 0U; i < count; ++i) if ((value)->pointer_candidates[j] == roots[i]) \
          intersection[used++] = roots[i]; \
      if (!used) break; \
      (value)->pointer_candidate_count = used; (value)->pointer_value = intersection[0]; \
      memcpy((value)->pointer_candidates, intersection, sizeof(intersection)); \
    } \
    (value)->struct_id = type; (value)->output = NULL; (value)->known = 1U; \
    (value)->pointer_target_known = 0U; (value)->array_element_count = 1U; (value)->array_element_index = 0U; \
    if (!(value)->table_origin.has_origin) \
      (value)->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT, \
        read->section_index, predecessor->candidate->offset); \
  } \
} while (0)
  TYPED_READ_VISIT_VALUES(state, REFINE_READ);
#undef REFINE_READ
}
#undef TYPED_READ_VISIT_VALUES
