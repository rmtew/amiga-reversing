/* Call-local normalization of a side-effect-free entry prefix. This does not
 * change the callable's context-free contract or interpret a return edge.
 * The established suffix proof remains responsible for every path/effect. */
typedef struct M68kPrefixScalar { uint32_t value, mask; } M68kPrefixScalar;

static M68kRenderTypedStorageSlot *typed_storage_reserve_identity(M68kRenderLookup *,
    uint8_t, size_t, int32_t, uint32_t, int *);

static void guarded_prefix_reserve(M68kRenderLookup *lookup,const M68kInstructionIR *instruction,
    uint8_t operand,size_t section,int *changed) {
  uint32_t address; int added=0;
  if (operand >= instruction->operand_count ||
      platform_operand_memory_access(instruction,operand) != M68K_SIM_ACCESS_MEMORY_READ ||
      !operand_absolute_offset_local(&instruction->operands[operand],&address) ||
      platform_facts_v2_address_has_hardware_owner(lookup->object->platform_backend_kind,address)) return;
  uint8_t width=m68k_sim_operand_width_bytes(instruction,operand);
  if (width != 1U && width != 2U && width != 4U) return;
  if (!typed_storage_reserve_identity(lookup,M68K_RENDER_TYPED_STORAGE_ABSOLUTE,section,0,address,&added))
    lookup->source_domain_error=1U;
  if (added && changed) *changed=1;
}

static void guarded_prefix_words(const M68kRenderTypedState *typed,
    const M68kRenderPlatformState *platform,M68kPrefixScalar words[8]) {
  memset(words,0,8U*sizeof(*words));
  for(uint8_t r=0U;r<8U;++r) {
    const M68kRenderTypedRegValue *value=&typed->data_regs[r];
    if(value->raw_long_value_known && value->raw_long_candidate_count<=1U && !value->address_value_candidate_overflow)
      words[r]=(M68kPrefixScalar){value->raw_long_value,UINT32_MAX};
    else if(platform->word_values[r].count==1U && !platform->word_values[r].requires_input_contract)
      words[r]=(M68kPrefixScalar){platform->word_values[r].values[0],UINT16_MAX};
  }
}

static M68kPrefixScalar guarded_prefix_value(const M68kRenderLookup *lookup,
    const M68kRenderTypedState *state,const M68kInstructionIR *instruction,uint8_t operand,
    const M68kPrefixScalar words[8],size_t section) {
  M68kPrefixScalar result={0};uint32_t raw;uint8_t reg;
  if(operand>=instruction->operand_count) return result;
  const M68kOperandIR *source=&instruction->operands[operand];
  if(m68k_ir_operand_immediate_value(source,&raw)) result=(M68kPrefixScalar){raw,UINT32_MAX};
  else if(operand_is_data_register_local(source,&reg) && reg<8U) result=words[reg];
  else if(platform_operand_memory_access(instruction,operand)==M68K_SIM_ACCESS_MEMORY_READ &&
      operand_absolute_offset_local(source,&raw)) {
    uint8_t width=m68k_sim_operand_width_bytes(instruction,operand);
    uint32_t read_lo,read_hi;
    if((width!=1U && width!=2U && width!=4U) ||
        !typed_runtime_bus_span(raw,raw,width,&read_lo,&read_hi)) return result;
    for(size_t i=0U;i<state->base_slot_count;++i) {
      const M68kRenderTypedBaseSlot *cell=&state->base_slots[i];
      uint32_t lo,hi;
      if(!cell->known || !cell->storage_id || cell->storage_id>lookup->typed_storage_slot_count) continue;
      const M68kRenderTypedStorageSlot *owner=&lookup->typed_storage_slots[cell->storage_id-1U];
      if(owner->kind!=M68K_RENDER_TYPED_STORAGE_ABSOLUTE || !cell->value.raw_long_value_known ||
          cell->value.address_value_candidate_overflow || cell->value.raw_long_candidate_count>1U ||
          !typed_runtime_bus_span(owner->address,owner->address,4U,&lo,&hi) || read_lo<lo || read_hi>hi) continue;
      uint32_t mask=width==4U ? UINT32_MAX : width==2U ? UINT16_MAX : UINT8_MAX;
      uint32_t value=(cell->value.raw_long_value >> ((hi-read_hi)*8U)) & mask;
      if(result.mask && result.value!=value) return (M68kPrefixScalar){0};
      result=(M68kPrefixScalar){value,mask};
    }
  }
  return result;
}

static int typed_flow_guarded_call_prefix(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted, size_t section_index, uint32_t entry,
    M68kRenderTypedState *typed, M68kRenderPlatformState *platform,
    M68kAnalysisFunctionSummary *summary, int discover, int *changed) {
  M68kRenderTypedState next = *typed; M68kRenderPlatformState bases = *platform;
  M68kPrefixScalar words[8] = {{0}}, predicate = {0};
  M68kInstructionIR producer = {0}; M68kLocalCalleeInputs visited = {0};
  int have_predicate = 0, guarded = 0, result = 0; uint32_t offset = entry;
  if (section_index >= decode->section_count) return 0;
  const M68kDecodeSectionIR *section = &decode->sections[section_index];
  guarded_prefix_words(typed,platform,words);
  for (;;) {
    M68kTypedLocalCalleeState visit = {0}; visit.offset = offset;
    if (local_callee_input_visit(&visited,&visit) != 1) break; /* Cyclic prefixes refuse. */
    const M68kDecodeCandidate *candidate = m68k_decode_ir_find_candidate_at_offset(section,offset);
    M68kInstructionIR instruction; uint8_t limit = 0U, reg;
    if (!candidate || offset >= section->size || !accepted[section_index][offset] ||
        m68k_decode_candidate_to_instruction(candidate,&instruction)) break;
    const M68kSimFormMetadata *metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (!metadata) break;
    if (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional &&
        metadata->operation_type != M68K_SIM_OP_DBCC) {
      uint32_t target; int taken;
      if (!have_predicate || !m68k_sim_known_value_branch(&producer,&instruction,predicate.value,predicate.mask,&taken) ||
          !typed_flow_first_local_control_target(lookup,section,candidate,&target)) break;
      guarded = 1; have_predicate = 0;
      offset = taken ? target : offset + candidate->byte_count; continue;
    }
    int simple_move = metadata->operation_type == M68K_SIM_OP_MOVE && instruction.operand_count == 2U &&
      m68k_instruction_operand_direct_register(&instruction.operands[1],&limit,&reg) && (!limit || reg < 7U);
    int test = metadata->operation_type == M68K_SIM_OP_TEST || metadata->operation_type == M68K_SIM_OP_BIT_TEST;
    /* The call has pushed a return PC. Do not normalize a prefix that can
     * observe/update its stack through the caller's pre-CALL A7 packet. */
    for (uint8_t i = 0U; i < instruction.operand_count; ++i) {
      const M68kOperandIR *operand = &instruction.operands[i]; uint8_t address, r;
      uint32_t absolute, immediate;
      if (m68k_instruction_operand_direct_register(operand,&address,&r)) {
        if (address && r == 7U) simple_move = test = 0;
      } else if (i == metadata->source_operand_index || i == metadata->dest_operand_index) {
        if (!m68k_ir_operand_immediate_value(operand,&immediate) && !operand_absolute_offset_local(operand,&absolute))
          simple_move = test = 0; /* Non-absolute memory stays in the suffix proof. */
      }
    }
    if (metadata->flow_kind != M68K_SIM_FLOW_NONE && metadata->flow_kind != M68K_SIM_FLOW_SEQUENTIAL) simple_move = test = 0;
    if (!simple_move && !test) {
      if (guarded && typed_flow_local_callee_effect_summary(lookup,decode,accepted,section_index,offset,summary,&limit)) {
        *typed = next; *platform = bases; result = 1;
      }
      break;
    }
    uint8_t source = test && metadata->operation_type == M68K_SIM_OP_BIT_TEST ?
      metadata->dest_operand_index : metadata->source_operand_index;
    if(discover) guarded_prefix_reserve(lookup,&instruction,source,section_index,changed);
    M68kPrefixScalar value = guarded_prefix_value(lookup,&next,&instruction,source,words,section_index);
    if (source < instruction.operand_count &&
        platform_operand_memory_access(&instruction,source) == M68K_SIM_ACCESS_MEMORY_READ && !value.mask) break;
    producer = instruction; predicate = value;
    have_predicate = metadata->ccr_formula != M68K_SIM_CCR_FORMULA_NONE && value.mask != 0U;
    if (simple_move && !limit) {
      uint8_t width = m68k_sim_operand_width_bytes(&instruction,1U);
      uint32_t mask = width == 4U ? UINT32_MAX : width == 2U ? UINT16_MAX : width == 1U ? UINT8_MAX : 0U;
      words[reg].value = (words[reg].value & ~mask) | (value.value & mask);
      words[reg].mask = (words[reg].mask & ~mask) | (value.mask & mask);
    }
    typed_state_update_after_instruction(&next,lookup,&bases,section_index,&instruction,candidate,NULL,offset,0);
    platform_state_update_after_instruction(&bases,lookup,&instruction);
    typed_state_project_layout_roots(&next,lookup,&bases);
    typed_state_import_layout_roots(&next,lookup,&bases,section_index,offset);
    if (candidate->byte_count > section->size-offset) break;
    offset += candidate->byte_count;
  }
  const char *trace = getenv("AMIGA_REVERSING_GUARDED_CALL_TRACE");
  if (trace && (!strcmp(trace,"*") || strtoul(trace,NULL,0) == entry))
    fprintf(stderr,"guarded-call section=%zu entry=%X stop=%X guarded=%d result=%d pcs=%zu cells=%zu\n",
      section_index,entry,offset,guarded,result,visited.count,next.base_slot_count);
  free(visited.states);free(visited.index);
  return result;
}


/* Only a closed adjacent flag producer can choose an ordinary CFG edge.
 * The value comes from that producer's reaching packet, never original bytes
 * read out of context. No extra per-node scalar state is introduced. */
static const M68kRenderTypedFlowNode *guarded_branch_producer(
    const M68kRenderTypedFlowGraph *graph,size_t index,M68kInstructionIR *producer,M68kInstructionIR *branch) {
  const M68kRenderTypedFlowNode *node=&graph->nodes[index];
  size_t begin=graph->predecessor_offsets[index];
  if(node->is_root || node->successor_count!=2U ||
      (graph->call_inputs_enabled && graph->call_predecessor_offsets &&
       graph->call_predecessor_offsets[index]!=graph->call_predecessor_offsets[index+1U]) ||
      graph->predecessor_offsets[index+1U]!=begin+1U ||
      m68k_decode_candidate_to_instruction(node->candidate,branch)) return NULL;
  const M68kSimFormMetadata *b=m68k_sim_metadata_for_instruction(branch);
  if(!b || b->flow_kind!=M68K_SIM_FLOW_BRANCH || !b->flow_conditional || b->operation_type==M68K_SIM_OP_DBCC) return NULL;
  const M68kRenderTypedFlowNode *prior=&graph->nodes[graph->predecessors[begin]];
  if(prior->candidate->offset+prior->candidate->byte_count!=node->candidate->offset ||
      m68k_decode_candidate_to_instruction(prior->candidate,producer)) return NULL;
  const M68kSimFormMetadata *p=m68k_sim_metadata_for_instruction(producer);
  if(!p || (p->ccr_formula!=M68K_SIM_CCR_FORMULA_MOVE_FLAGS &&
      p->ccr_formula!=M68K_SIM_CCR_FORMULA_TEST_FLAGS && p->operation_type!=M68K_SIM_OP_BIT_TEST)) return NULL;
  return prior;
}

static void guarded_branch_reserve_cells(M68kRenderLookup *lookup,M68kRenderTypedFlowGraph *graph,size_t section) {
  for(size_t i=0U;i<graph->node_count;++i) {
    M68kInstructionIR producer,branch;
    if(!guarded_branch_producer(graph,i,&producer,&branch)) continue;
    const M68kSimFormMetadata *p=m68k_sim_metadata_for_instruction(&producer);
    uint8_t source=p->operation_type==M68K_SIM_OP_BIT_TEST ? p->dest_operand_index : p->source_operand_index;
    guarded_prefix_reserve(lookup,&producer,source,section,NULL);
  }
}

static int guarded_branch_allows_edge(const M68kRenderLookup *lookup,
    const M68kRenderTypedFlowGraph *graph,size_t from,size_t to,size_t section) {
  M68kInstructionIR producer,branch;M68kPrefixScalar words[8];int taken;
  const M68kRenderTypedFlowNode *prior=guarded_branch_producer(graph,from,&producer,&branch);
  /* A current initializer value is not an all-caller reachability proof for
   * later gameplay/interrupt phases. Ordinary pruning stops at that boundary;
   * the separate call-local proof still uses its own reaching packet. */
  if(!prior || !prior->has_in ||
      !(prior->typed_in.source_snapshot_entry & M68K_TYPED_SOURCE_CONTEXT_INITIAL_PREFIX)) return 1;
  const M68kSimFormMetadata *p=m68k_sim_metadata_for_instruction(&producer);
  uint8_t source=p->operation_type==M68K_SIM_OP_BIT_TEST ? p->dest_operand_index : p->source_operand_index;
  guarded_prefix_words(&prior->typed_in,&prior->platform_in,words);
  M68kPrefixScalar value=guarded_prefix_value(lookup,&prior->typed_in,&producer,source,words,section);
  if(!m68k_sim_known_value_branch(&producer,&branch,value.value,value.mask,&taken)) return 1;
  int target=graph->nodes[to].candidate->offset != graph->nodes[from].candidate->offset+graph->nodes[from].candidate->byte_count;
  return taken==target;
}
