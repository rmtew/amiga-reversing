/* Bounded future-use audit, deliberately separate from relocation closure.
 * This projects accepted ordinary control flow; it cannot certify private
 * frames, asynchronous observers, exceptions or instruction timing. */
#define MR_LIVENESS_EVENT_LIMIT 32U
typedef struct MRLivenessState {
  uint32_t pc, owner, returns[MR_CALL_LIMIT], owners[MR_CALL_LIMIT];
  uint16_t aliases;
  uint8_t depth;
} MRLivenessState;
typedef struct MRLivenessEvent { uint32_t pc; const char *kind; } MRLivenessEvent;
typedef struct MRLivenessResult {
  uint32_t states, leaf, start;
  unsigned event_count, deaths, uses, barriers;
  MRLivenessEvent events[MR_LIVENESS_EVENT_LIMIT];
  int applicable, truncated;
} MRLivenessResult;

static uint16_t mr_liveness_register(const M68kOperandIR *o) {
  uint8_t address, reg;
  return m68k_instruction_operand_direct_register(o,&address,&reg) ?
    (uint16_t)(1U<<(reg+(address ? 8U : 0U))) : 0;
}
static void mr_liveness_event(MRLivenessResult *r,uint32_t pc,const char *kind,int category) {
  for(unsigned i=0;i<r->event_count;i++)
    if(r->events[i].pc==pc && !strcmp(r->events[i].kind,kind)) return;
  if(r->event_count==MR_LIVENESS_EVENT_LIMIT) {r->truncated=1;return;}
  r->events[r->event_count++]=(MRLivenessEvent){pc,kind};
  if(category==0) r->deaths++; else if(category==1) r->uses++; else r->barriers++;
}

static MRLivenessResult mr_after_leaf_liveness(const PlatformFileListingArtifact *a,
    const M68kMemoryRegionIR *region,const M68kRenderPlannedInstruction *root,uint8_t operand) {
  MRLivenessResult result={0};uint8_t address,reg;
  const M68kSimFormMetadata *rm=m68k_sim_metadata_for_instruction(&root->instruction);
  if(!rm || rm->operation_class!=M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS ||
      !m68k_instruction_operand_direct_register(&root->instruction.operands[rm->dest_operand_index],&address,&reg) ||
      !address || reg==7) return result;
  const M68kRenderPlannedInstruction *leaf=mr_instruction(a,root->source_offset+(uint32_t)root->instruction.byte_count);
  const M68kSimFormMetadata *lm=leaf ? m68k_sim_metadata_for_instruction(&leaf->instruction) : NULL;
  if(!lm || leaf->instruction.target_cpu!=M68K_ASM_CPU_68000 ||
      lm->exception_trigger || lm->bounds_trap_on_fail || lm->ccr_formula==M68K_SIM_CCR_FORMULA_WRITE_SR ||
      (lm->flow_kind!=M68K_SIM_FLOW_NONE && lm->flow_kind!=M68K_SIM_FLOW_SEQUENTIAL)) return result;
  unsigned reads=0;
  for(size_t j=0;j<leaf->instruction.operand_count;j++) {
    const M68kOperandIR *o=&leaf->instruction.operands[j];uint8_t access=lm->operand_access_kinds[j],shape=mr_shape(o);
    M68kAsmOperandValue v;m68k_instruction_operand_to_asm_value(o,&v);
    if(access==M68K_SIM_ACCESS_MEMORY_WRITE || (mr_liveness_register(o)&(1U<<(8U+reg)))) return result;
    if(access==M68K_SIM_ACCESS_REGISTER_LIST_WRITE && (v.value&(1U<<(8U+reg)))) return result;
    if(shape>=M68K_SIM_EA_SHAPE_INDIRECT && shape<=M68K_SIM_EA_SHAPE_INDEX && v.ea_reg==reg) {
      if(access!=M68K_SIM_ACCESS_MEMORY_READ ||
          (shape!=M68K_SIM_EA_SHAPE_INDIRECT && shape!=M68K_SIM_EA_SHAPE_DISPLACEMENT)) return result;
      int64_t offset=(int64_t)root->instruction.operands[operand].value.value-region->runtime_address;
      if(shape==M68K_SIM_EA_SHAPE_DISPLACEMENT) offset+=(int16_t)v.value;
      unsigned width=mr_access_width(&leaf->instruction,lm,(uint8_t)j);
      if(!width || offset<0 || offset+width>region->size) return result;
      reads++;
    }
  }
  if(reads!=1) return result;
  result.applicable=1;result.leaf=leaf->source_offset;
  result.start=leaf->source_offset+(uint32_t)leaf->instruction.byte_count;
  MRLivenessState *queue=calloc(MR_PROOF_LIMIT,sizeof(*queue));size_t head=0,count=1;
  if(!queue) {mr_liveness_event(&result,result.start,"allocation_limit",2);return result;}
  queue[0].pc=result.start;queue[0].owner=mr_owner(a,root->source_offset);queue[0].aliases=(uint16_t)(1U<<(8U+reg));
#define ML_EVENT(kind,category) do {mr_liveness_event(&result,state.pc,kind,category);goto next_state;} while(0)
#define ML_ADD(value) do {MRLivenessState candidate=(value);size_t qi; \
  for(qi=0;qi<count;qi++) if(!memcmp(&queue[qi],&candidate,sizeof(candidate))) break; \
  if(qi==count) {if(count==MR_PROOF_LIMIT) {result.truncated=1;mr_liveness_event(&result,state.pc,"state_limit",2);goto next_state;}queue[count++]=candidate;}} while(0)
  while(head<count) {
    MRLivenessState state=queue[head++],next=state;result.states++;
    const M68kRenderPlannedInstruction *ins=mr_instruction(a,state.pc);
    const M68kSimFormMetadata *m=ins ? m68k_sim_metadata_for_instruction(&ins->instruction) : NULL;
    if(!m || ins->instruction.target_cpu!=M68K_ASM_CPU_68000 ||
        (m->operation_type==M68K_SIM_OP_NONE && m->operation_class==M68K_SIM_CLASS_NONE &&
          (m->flow_kind==M68K_SIM_FLOW_NONE || m->flow_kind==M68K_SIM_FLOW_SEQUENTIAL))) ML_EVENT("unsupported_instruction",2);
    if(m->flow_kind==M68K_SIM_FLOW_TRAP || m->exception_trigger || m->bounds_trap_on_fail ||
        m->ccr_formula==M68K_SIM_CCR_FORMULA_WRITE_SR ||
        m->operation_type==M68K_SIM_OP_PUSH_EA || m->operation_type==M68K_SIM_OP_LINK ||
        m->operation_type==M68K_SIM_OP_UNLK) ML_EVENT("exception_or_implicit_frame_observer",2);
    uint16_t copy=0,destination=0,computed=0;
    if(m->operation_type==M68K_SIM_OP_MOVE && m->source_operand_index<ins->instruction.operand_count &&
        m->dest_operand_index<ins->instruction.operand_count) {
      copy=mr_liveness_register(&ins->instruction.operands[m->source_operand_index])&state.aliases;
      destination=mr_liveness_register(&ins->instruction.operands[m->dest_operand_index]);
      if(copy && (!destination || m68k_sim_operand_width_bytes(&ins->instruction,m->source_operand_index)!=4))
        ML_EVENT("pointer_value_escape",1);
    }
    for(size_t j=0;j<ins->instruction.operand_count;j++) {
      const M68kOperandIR *o=&ins->instruction.operands[j];uint8_t access=m->operand_access_kinds[j],shape=mr_shape(o);
      if(o->kind==M68K_ASM_OPERAND_USP) ML_EVENT("exception_or_implicit_frame_observer",2);
      if(o->value.full_ext_base_suppress || o->value.full_ext_index_suppress || o->value.full_ext_base_disp_size ||
          o->value.full_ext_outer_disp_size || o->value.full_ext_iis || o->kind==M68K_ASM_OPERAND_BF_EA)
        ML_EVENT("unsupported_effective_address",2);
      uint16_t direct=mr_liveness_register(o);
      if(direct&state.aliases) {
        if(access==M68K_SIM_ACCESS_REGISTER_READ || access==M68K_SIM_ACCESS_MEMORY_READ) {
          if(!copy || j!=m->source_operand_index) ML_EVENT("pointer_value_observed",1);
        }
        if(access==M68K_SIM_ACCESS_REGISTER_WRITE || access==M68K_SIM_ACCESS_MEMORY_WRITE) {
          if(m->operation_type!=M68K_SIM_OP_MOVE && m->operation_class!=M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS)
            ML_EVENT("dependent_register_update",2);
          if(!(direct&0xff00U) && m68k_sim_operand_width_bytes(&ins->instruction,(uint8_t)j)!=4)
            ML_EVENT("partial_alias_overwrite",2);
          next.aliases&=(uint16_t)~direct;
        }
      }
      M68kAsmOperandValue v;m68k_instruction_operand_to_asm_value(o,&v);
      uint16_t bases=0;
      if(shape>=M68K_SIM_EA_SHAPE_INDIRECT && shape<=M68K_SIM_EA_SHAPE_INDEX) bases=(uint16_t)(1U<<(8U+v.ea_reg));
      if(shape==M68K_SIM_EA_SHAPE_INDEX || shape==M68K_SIM_EA_SHAPE_PC_INDEX)
        bases|=(uint16_t)(1U<<(v.index_reg+(v.index_is_address ? 8U : 0U)));
      if(bases&state.aliases) {
        if(access==M68K_SIM_ACCESS_COMPUTE_ADDRESS && m->operation_class==M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS &&
            m->dest_operand_index<ins->instruction.operand_count) {
          uint16_t dest=mr_liveness_register(&ins->instruction.operands[m->dest_operand_index]);
          if(!dest || (dest&(1U<<15))) ML_EVENT("pointer_value_escape",1);
          computed|=dest;
        } else ML_EVENT(access==M68K_SIM_ACCESS_BRANCH_TARGET ? "pointer_control_escape" : "later_pointer_memory_access",1);
      }
      if((access==M68K_SIM_ACCESS_REGISTER_LIST_READ || access==M68K_SIM_ACCESS_REGISTER_LIST_WRITE) &&
          (v.value&state.aliases)) ML_EVENT("saved_or_restored_pointer_observer",2);
    }
    next.aliases|=computed;
    if(copy) next.aliases|=destination;
    if(next.aliases&(1U<<15)) ML_EVENT("pointer_stack_escape",1);
    if(!next.aliases) ML_EVENT("independent_overwrite",0);
    next.pc=state.pc+(uint32_t)ins->instruction.byte_count;uint32_t target=mr_target(a,ins);
    if(m->flow_kind==M68K_SIM_FLOW_CALL) {
      if(target==UINT32_MAX || state.depth==MR_CALL_LIMIT) ML_EVENT("unresolved_call",2);
      next.returns[next.depth]=next.pc;next.owners[next.depth]=state.owner;next.depth++;
      next.owner=target;next.pc=target;ML_ADD(next);continue;
    }
    if(m->flow_kind==M68K_SIM_FLOW_RETURN) {
      if(m->return_restore_kind!=M68K_SIM_RETURN_RESTORE_PC_ONLY || m->return_stack_adjust_operand_index<ins->instruction.operand_count)
        ML_EVENT("exception_return_observer",2);
      if(state.depth) {
        next.depth--;next.pc=next.returns[next.depth];next.owner=next.owners[next.depth];
        next.returns[next.depth]=next.owners[next.depth]=0;ML_ADD(next);continue;
      }
      if(state.owner==UINT32_MAX) ML_EVENT("unresolved_return_context",2);
      const M68kSectionAnalysisIR *section=&a->source_analysis.sections[0];unsigned callers=0;
      for(size_t e=0;e<section->edge_count;e++) {
        const M68kCfgEdgeIR *edge=&section->edges[e];
        if(edge->target_offset==state.owner && edge->kind!=M68K_CFG_EDGE_CALL &&
            mr_owner(a,edge->source_offset)!=state.owner)
          mr_liveness_event(&result,state.pc,"unmodeled_tail_return_context",2);
      }
      for(size_t e=0;e<section->edge_count;e++) {
        const M68kCfgEdgeIR *edge=&section->edges[e];
        if(edge->kind!=M68K_CFG_EDGE_CALL || edge->target_offset!=state.owner) continue;
        const M68kRenderPlannedInstruction *call=mr_instruction(a,edge->source_offset);
        if(!call) ML_EVENT("unaccepted_caller",2);
        next.pc=call->source_offset+(uint32_t)call->instruction.byte_count;next.owner=mr_owner(a,call->source_offset);
        ML_ADD(next);callers++;
      }
      if(!callers) ML_EVENT("unresolved_return_context",2);
      continue;
    }
    if(m->flow_kind==M68K_SIM_FLOW_BRANCH || m->flow_kind==M68K_SIM_FLOW_JUMP) {
      if(target==UINT32_MAX) ML_EVENT("unresolved_branch",2);
      if(m->flow_conditional) ML_ADD(next);
      next.pc=target;ML_ADD(next);continue;
    }
    ML_ADD(next);
next_state:;
  }
  free(queue);return result;
#undef ML_EVENT
#undef ML_ADD
}
