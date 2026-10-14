/* Conservative root-to-use proof over canonical accepted instructions and
 * generated CPU semantics. Limits and unsupported escapes are refusals. */
#define MR_PROOF_LIMIT 8192U
#define MR_CALL_LIMIT 16U
typedef struct MRProofState {
  uint32_t pc, function_entry, offset, d[8], zero[8], returns[MR_CALL_LIMIT], functions[MR_CALL_LIMIT];
  int32_t sp, saved_sp[MR_CALL_LIMIT], return_sp[MR_CALL_LIMIT];
  uint32_t saved_offset[MR_CALL_LIMIT];
  uint8_t known[8], reg, depth, live, saved_count;
} MRProofState;
typedef struct MRProofResult {
  uint32_t source_offset, access_count, minimum_offset, maximum_end, states;
  const char *reason;
} MRProofResult;

static const M68kRenderPlannedInstruction *mr_instruction(const PlatformFileListingArtifact *a,uint32_t pc) {
  return m68k_render_plan_find_instruction(&a->source_plan,0,pc);
}
static uint32_t mr_target(const PlatformFileListingArtifact *a,const M68kRenderPlannedInstruction *ins) {
  size_t i;uint32_t target=UINT32_MAX; const M68kSectionAnalysisIR *s=&a->source_analysis.sections[0];
  for(i=0;i<s->edge_count;i++) if(s->edges[i].source_offset==ins->source_offset &&
      (s->edges[i].kind==M68K_CFG_EDGE_CALL || s->edges[i].kind==M68K_CFG_EDGE_BRANCH || s->edges[i].kind==M68K_CFG_EDGE_JUMP)) {
    if(!mr_instruction(a,s->edges[i].target_offset) || (target!=UINT32_MAX && target!=s->edges[i].target_offset)) return UINT32_MAX;
    target=s->edges[i].target_offset;
  }
  return target;
}
static uint32_t mr_address_target(const M68kRenderPlannedInstruction *ins,size_t operand) {
  size_t i;
  for(i=0;i<ins->symbol_access_count;i++) if(ins->symbol_accesses[i].operand_index==operand && ins->symbol_accesses[i].has_target)
    return ins->symbol_accesses[i].target_offset;
  if(ins->instruction.operands[operand].symbol_ref.has_section_offset)
    return ins->instruction.operands[operand].symbol_ref.section_offset;
  return UINT32_MAX;
}
/* Resolve a unique entry through the canonical CFG, stopping at callable
 * entry candidates. Layout order alone never establishes a return context. */
static uint32_t mr_owner(const PlatformFileListingArtifact *a,uint32_t pc) {
  const M68kSectionAnalysisIR *section=&a->source_analysis.sections[0];
  size_t n=section->block_count,i,j,head=0,count=0;
  uint8_t *entry=calloc(n,1),*seen=calloc(n,1);size_t *queue=calloc(n,sizeof(*queue));
  uint32_t owner=UINT32_MAX;int found=0,ambiguous=0;
  if(!entry || !seen || !queue) goto done;
  for(i=0;i<section->edge_count;i++) if(section->edges[i].kind==M68K_CFG_EDGE_CALL && section->edges[i].target_block_index<n)
    entry[section->edges[i].target_block_index]=1;
  for(i=0;i<a->source_plan.instruction_count;i++) {
    const M68kRenderPlannedInstruction *ins=&a->source_plan.instructions[i];
    const M68kSimFormMetadata *m=m68k_sim_metadata_for_instruction(&ins->instruction);
    const M68kRenderPlannedInstruction *next=mr_instruction(a,ins->source_offset+(uint32_t)ins->instruction.byte_count);
    const M68kSimFormMetadata *nm=next ? m68k_sim_metadata_for_instruction(&next->instruction) : NULL;
    if(!m || !nm || m->operation_class!=M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS || nm->operation_type!=M68K_SIM_OP_MOVE ||
        nm->operand_access_kinds[nm->dest_operand_index]!=M68K_SIM_ACCESS_MEMORY_WRITE) continue;
    uint32_t target=mr_address_target(ins,m->source_operand_index);
    for(j=0;j<n;j++) if(section->blocks[j].start_offset==target) entry[j]=1;
  }
  for(i=0;i<n;i++) if(section->blocks[i].start_offset<=pc && pc<section->blocks[i].end_offset) {
    queue[count++]=i;seen[i]=1;break;
  }
  if(!count) goto done;
  while(head<count) {
    size_t block=queue[head++];
    if(entry[block]) {
      uint32_t candidate=section->blocks[block].start_offset;
      if(found && owner!=candidate) ambiguous=1;
      owner=candidate;found=1;continue;
    }
    int predecessor=0;
    for(i=0;i<section->edge_count;i++) {
      const M68kCfgEdgeIR *edge=&section->edges[i];
      if(edge->target_block_index!=block || edge->kind==M68K_CFG_EDGE_CALL || edge->source_block_index>=n) continue;
      predecessor=1;
      if(!seen[edge->source_block_index]) {seen[edge->source_block_index]=1;queue[count++]=edge->source_block_index;}
    }
    if(!predecessor) ambiguous=1;
  }
done:free(entry);free(seen);free(queue);return found && !ambiguous ? owner : UINT32_MAX;
}
static uint8_t mr_shape(const M68kOperandIR *o) {
  M68kOperandIR normalized=*o;
  m68k_instruction_operand_to_asm_value(o,&normalized.value);
  normalized.kind=normalized.value.kind;
  return m68k_instruction_operand_decoded_ea_shape(&normalized);
}
static int mr_direct_reg(const M68kOperandIR *o,uint8_t address,uint8_t reg) {
  uint8_t is_address,index;
  return m68k_instruction_operand_direct_register(o,&is_address,&index) && is_address==address && index==reg;
}
/* A MOVEM operand covers every selected register, not one element. */
static unsigned mr_access_width(const M68kInstructionIR *ins,const M68kSimFormMetadata *m,uint8_t operand) {
  unsigned width=m68k_sim_operand_width_bytes(ins,operand);
  if(m->operation_type==M68K_SIM_OP_MOVE_MULTIPLE && operand==m->address_operand_index) {
    uint32_t mask=ins->operands[m->reglist_operand_index].value.value;unsigned count=0;
    for(unsigned bit=0;bit<16;bit++) if(mask & (1U<<bit)) count++;
    width*=count;
  }
  return width;
}
/* Check all reverse-CFG paths from a callback slot load back to the actual
 * entry save. Only instructions that preserve that frame are admitted. */
static int mr_callback_prefix(const PlatformFileListingArtifact *a,uint32_t handler,uint32_t load) {
  const M68kSectionAnalysisIR *s=&a->source_analysis.sections[0];
  uint32_t *queue=calloc(MR_PROOF_LIMIT,sizeof(*queue));size_t count=1,head=0;int reached=0,ok=0;
  if(!queue) return 0;
  queue[0]=load;
  while(head<count) {
    uint32_t pc=queue[head++];int predecessors=0;
    for(size_t i=0;i<a->source_plan.instruction_count;i++) {
      const M68kRenderPlannedInstruction *pre=&a->source_plan.instructions[i];
      const M68kSimFormMetadata *m=m68k_sim_metadata_for_instruction(&pre->instruction);
      if(!m) continue;
      int connects=pre->source_offset+(uint32_t)pre->instruction.byte_count==pc &&
        (m->flow_kind==M68K_SIM_FLOW_NONE || m->flow_kind==M68K_SIM_FLOW_SEQUENTIAL ||
          (m->flow_kind==M68K_SIM_FLOW_BRANCH && m->flow_conditional));
      for(size_t e=0;e<s->edge_count;e++) if(s->edges[e].source_offset==pre->source_offset && s->edges[e].target_offset==pc &&
          (s->edges[e].kind==M68K_CFG_EDGE_BRANCH || s->edges[e].kind==M68K_CFG_EDGE_JUMP)) connects=1;
      if(!connects) continue;
      if(pre->instruction.target_cpu!=M68K_ASM_CPU_68000) goto done;
      predecessors++;
      if(pre->source_offset==handler) {reached=1;continue;}
      if(m->flow_kind==M68K_SIM_FLOW_CALL || m->flow_kind==M68K_SIM_FLOW_RETURN || m->flow_kind==M68K_SIM_FLOW_TRAP ||
          m->operation_type==M68K_SIM_OP_MOVE_MULTIPLE) goto done;
      for(size_t j=0;j<pre->instruction.operand_count;j++) {
        const M68kOperandIR *o=&pre->instruction.operands[j];M68kAsmOperandValue v;
        m68k_instruction_operand_to_asm_value(o,&v);uint8_t shape=mr_shape(o);
        if(mr_direct_reg(o,1,7) || (shape>=M68K_SIM_EA_SHAPE_INDIRECT && shape<=M68K_SIM_EA_SHAPE_INDEX && v.ea_reg==7)) goto done;
        /* An unknown write might reach the saved frame through another base. */
        uint8_t ar,reg;
        if(m->operand_access_kinds[j]==M68K_SIM_ACCESS_MEMORY_WRITE && !m68k_instruction_operand_direct_register(o,&ar,&reg)) goto done;
      }
      size_t q;for(q=0;q<count;q++) if(queue[q]==pre->source_offset) break;
      if(q==count) {if(count==MR_PROOF_LIMIT) goto done;queue[count++]=pre->source_offset;}
    }
    if(!predecessors) goto done;
  }
  ok=reached;
done:free(queue);return ok;
}
/* Prefix-frame check over reverse canonical control flow. Calls and writes
 * through other registers remain outside this bounded contract. */
static int mr_root_prefix_frame(const PlatformFileListingArtifact *a,uint32_t entry,uint32_t root) {
  if(entry==root) return 1;
  /* Reuse the strict path check by making the entry its stopping boundary.
   * It normally checks predecessors; inspect the entry instruction too. */
  const M68kRenderPlannedInstruction *first=mr_instruction(a,entry);
  const M68kSimFormMetadata *m=first ? m68k_sim_metadata_for_instruction(&first->instruction) : NULL;
  if(!m || first->instruction.target_cpu!=M68K_ASM_CPU_68000 || m->flow_kind==M68K_SIM_FLOW_CALL || m->flow_kind==M68K_SIM_FLOW_RETURN || m->flow_kind==M68K_SIM_FLOW_TRAP) return 0;
  for(size_t j=0;j<first->instruction.operand_count;j++) {
    const M68kOperandIR *o=&first->instruction.operands[j];M68kAsmOperandValue v;
    m68k_instruction_operand_to_asm_value(o,&v);uint8_t shape=mr_shape(o);
    uint8_t ar,ri;
    if(m->operand_access_kinds[j]==M68K_SIM_ACCESS_MEMORY_WRITE && !m68k_instruction_operand_direct_register(o,&ar,&ri)) return 0;
    if(mr_direct_reg(o,1,7) || (shape>=M68K_SIM_EA_SHAPE_INDIRECT && shape<=M68K_SIM_EA_SHAPE_INDEX && v.ea_reg==7)) return 0;
  }
  return mr_callback_prefix(a,entry,root);
}
/* A callback return is discharged only by actual slot-load/call/restore
 * consumers. Unknown consumers or a mismatched register save remain open. */
static int mr_callback_restore(const PlatformFileListingArtifact *a,uint32_t entry,uint8_t reg) {
  size_t i,j;uint32_t slot=UINT32_MAX;uint8_t base=0;int consumers=0;
  for(i=0;i<a->source_plan.instruction_count;i++) {
    const M68kRenderPlannedInstruction *ins=&a->source_plan.instructions[i];
    const M68kSimFormMetadata *m=m68k_sim_metadata_for_instruction(&ins->instruction);
    const M68kRenderPlannedInstruction *next=mr_instruction(a,ins->source_offset+(uint32_t)ins->instruction.byte_count);
    const M68kSimFormMetadata *n=next ? m68k_sim_metadata_for_instruction(&next->instruction) : NULL;
    uint8_t ar,ri;
    if(!m || !n || m->operation_class!=M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS || mr_address_target(ins,m->source_operand_index)!=entry ||
        !m68k_instruction_operand_direct_register(&ins->instruction.operands[m->dest_operand_index],&ar,&ri) || !ar ||
        n->operation_type!=M68K_SIM_OP_MOVE || !mr_direct_reg(&next->instruction.operands[n->source_operand_index],1,ri)) continue;
    const M68kOperandIR *dest=&next->instruction.operands[n->dest_operand_index];
    if(mr_shape(dest)!=M68K_SIM_EA_SHAPE_DISPLACEMENT) return 0;
    if(slot!=UINT32_MAX && (slot!=dest->value.value || base!=dest->value.ea_reg)) return 0;
    slot=dest->value.value;base=dest->value.ea_reg;
  }
  if(slot==UINT32_MAX) return 0;
  for(i=0;i<a->source_plan.instruction_count;i++) {
    const M68kRenderPlannedInstruction *ins=&a->source_plan.instructions[i];
    const M68kSimFormMetadata *m=m68k_sim_metadata_for_instruction(&ins->instruction);
    if(!m) continue;
    for(j=0;j<ins->instruction.operand_count;j++) {
      const M68kOperandIR *o=&ins->instruction.operands[j];
      if(mr_shape(o)!=M68K_SIM_EA_SHAPE_DISPLACEMENT || o->value.ea_reg!=base || o->value.value!=slot ||
          m->operand_access_kinds[j]!=M68K_SIM_ACCESS_MEMORY_READ) continue;
      uint8_t ar,ri;
      if(m->operation_type!=M68K_SIM_OP_MOVE || !m68k_instruction_operand_direct_register(&ins->instruction.operands[m->dest_operand_index],&ar,&ri) || !ar) return 0;
      const M68kRenderPlannedInstruction *call=mr_instruction(a,ins->source_offset+(uint32_t)ins->instruction.byte_count);
      const M68kSimFormMetadata *cm=call ? m68k_sim_metadata_for_instruction(&call->instruction) : NULL;
      if(!cm || cm->flow_kind!=M68K_SIM_FLOW_CALL || mr_shape(&call->instruction.operands[cm->target_operand_index])!=M68K_SIM_EA_SHAPE_INDIRECT ||
          call->instruction.operands[cm->target_operand_index].value.ea_reg!=ri) return 0;
      uint32_t pc=call->source_offset+(uint32_t)call->instruction.byte_count,mask=0;int restored=0,saved=0;
      for(size_t k=0;k<8;k++) {
        const M68kRenderPlannedInstruction *post=mr_instruction(a,pc);
        const M68kSimFormMetadata *pm=post ? m68k_sim_metadata_for_instruction(&post->instruction) : NULL;
        if(!pm) break;
        if(pm->operation_type==M68K_SIM_OP_MOVE_MULTIPLE && pm->multi_transfer_direction==M68K_SIM_MULTI_MEMORY_TO_REGISTER) {
          mask=post->instruction.operands[pm->reglist_operand_index].value.value;
          const M68kOperandIR *restore=&post->instruction.operands[pm->address_operand_index];
          if((mask & (1U<<(8U+reg))) && m68k_sim_operand_width_bytes(&post->instruction,pm->address_operand_index)==4 &&
              mr_shape(restore)==M68K_SIM_EA_SHAPE_POSTINCREMENT && restore->value.ea_reg==7) restored=1;
          break;
        }
        for(size_t op=0;op<post->instruction.operand_count;op++) {
          const M68kOperandIR *o=&post->instruction.operands[op];
          M68kAsmOperandValue normalized;m68k_instruction_operand_to_asm_value(o,&normalized);
          uint8_t shape=mr_shape(o);
          uint8_t direct_ar,direct_reg;
          if(pm->operand_access_kinds[op]==M68K_SIM_ACCESS_MEMORY_WRITE &&
              !m68k_instruction_operand_direct_register(o,&direct_ar,&direct_reg)) return 0;
          if(mr_direct_reg(o,1,7) || mr_direct_reg(o,1,reg) || (shape>=M68K_SIM_EA_SHAPE_INDIRECT && shape<=M68K_SIM_EA_SHAPE_INDEX && normalized.ea_reg==reg)) return 0;
          if(shape>=M68K_SIM_EA_SHAPE_INDIRECT && shape<=M68K_SIM_EA_SHAPE_INDEX && normalized.ea_reg==7) return 0;
        }
        if(pm->flow_kind!=M68K_SIM_FLOW_SEQUENTIAL && pm->flow_kind!=M68K_SIM_FLOW_NONE) break;
        pc+=(uint32_t)post->instruction.byte_count;
      }
      if(!restored) return 0;
      uint32_t handler=mr_owner(a,ins->source_offset);
      const M68kRenderPlannedInstruction *pre=handler!=UINT32_MAX ? mr_instruction(a,handler) : NULL;
      const M68kSimFormMetadata *pm=pre ? m68k_sim_metadata_for_instruction(&pre->instruction) : NULL;
      if(pm && pm->operation_type==M68K_SIM_OP_MOVE_MULTIPLE && pm->multi_transfer_direction==M68K_SIM_MULTI_REGISTER_TO_MEMORY &&
          pre->instruction.operands[pm->reglist_operand_index].value.value==mask &&
          m68k_sim_operand_width_bytes(&pre->instruction,pm->address_operand_index)==4 &&
          mr_shape(&pre->instruction.operands[pm->address_operand_index])==M68K_SIM_EA_SHAPE_PREDECREMENT &&
          pre->instruction.operands[pm->address_operand_index].value.ea_reg==7) saved=1;
      if(!saved || !mr_callback_prefix(a,handler,ins->source_offset)) return 0;
      consumers++;
    }
  }
  return consumers>0;
}

static MRProofResult mr_prove_root(const PlatformFileListingArtifact *a,const M68kMemoryRegionIR *region,
    const M68kRenderPlannedInstruction *root,uint8_t operand) {
  MRProofResult result={0}; MRProofState *queue=calloc(MR_PROOF_LIMIT,sizeof(*queue));size_t count=1,head=0;
  const M68kSimFormMetadata *rm=m68k_sim_metadata_for_instruction(&root->instruction);uint8_t ar,reg;
  result.minimum_offset=UINT32_MAX;
  if(!queue || !rm || rm->operation_class!=M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS ||
      !m68k_instruction_operand_direct_register(&root->instruction.operands[rm->dest_operand_index],&ar,&reg) || !ar || reg==7) {
    result.reason="unsupported_pointer_producer";goto done;
  }
  queue[0].pc=root->source_offset+(uint32_t)root->instruction.byte_count;queue[0].reg=reg;queue[0].live=1;
  queue[0].offset=root->instruction.operands[operand].value.value-region->runtime_address;
  queue[0].function_entry=mr_owner(a,root->source_offset);
  /* Seed only immediate full-register definitions in the same basic block. */
  const M68kSectionAnalysisIR *section=&a->source_analysis.sections[0];uint32_t block_start=root->source_offset;
  for(size_t i=0;i<section->block_count;i++) if(section->blocks[i].start_offset<=root->source_offset && root->source_offset<section->blocks[i].end_offset) block_start=section->blocks[i].start_offset;
  for(size_t i=0;i<a->source_plan.instruction_count;i++) {
    const M68kRenderPlannedInstruction *pre=&a->source_plan.instructions[i];
    if(pre->source_offset<block_start || pre->source_offset>=root->source_offset) continue;
    const M68kSimFormMetadata *pm=m68k_sim_metadata_for_instruction(&pre->instruction);uint32_t v;uint8_t pa,pr;
    if(!pm) {memset(queue[0].known,0,sizeof(queue[0].known));memset(queue[0].zero,0,sizeof(queue[0].zero));continue;}
    for(size_t op=0;op<pre->instruction.operand_count;op++) {
      uint8_t aa,rr;
      if(m68k_instruction_operand_direct_register(&pre->instruction.operands[op],&aa,&rr) && !aa &&
          (pm->operand_access_kinds[op]==M68K_SIM_ACCESS_REGISTER_WRITE || pm->operand_access_kinds[op]==M68K_SIM_ACCESS_MEMORY_WRITE)) {
        queue[0].known[rr]=0;queue[0].d[rr]=0;queue[0].zero[rr]=0;
      }
    }
    if(pm->operation_type==M68K_SIM_OP_MOVE_MULTIPLE && pm->multi_transfer_direction==M68K_SIM_MULTI_MEMORY_TO_REGISTER)
      for(size_t rr=0;rr<8;rr++) if(pre->instruction.operands[pm->reglist_operand_index].value.value & (1U<<rr))
        queue[0].known[rr]=0,queue[0].d[rr]=0,queue[0].zero[rr]=0;
    if(pm && pm->operation_type==M68K_SIM_OP_MOVE && pre->instruction.size_suffix=='l' &&
        m68k_ir_operand_immediate_value(&pre->instruction.operands[pm->source_operand_index],&v) &&
        m68k_instruction_operand_direct_register(&pre->instruction.operands[pm->dest_operand_index],&pa,&pr) && !pa) {
      queue[0].known[pr]=1;queue[0].d[pr]=v;queue[0].zero[pr]=~v;
    }
  }
#define MR_FAIL(reason_text) do {result.reason=reason_text;result.source_offset=state.pc;goto done;} while(0)
/* Join scalars at an identical pointer/stack/control context. Counter values
 * unrelated to a pointer cannot cause an unbounded concrete path enumeration.
 * Losing a bound becomes unknown and is refused at a subsequent indexed use. */
#define MR_ADD(value) do {MRProofState candidate=(value),key=candidate;size_t qi; \
  memset(key.d,0,sizeof(key.d));memset(key.zero,0,sizeof(key.zero));memset(key.known,0,sizeof(key.known)); \
  for(qi=0;qi<count;qi++) {MRProofState oldkey=queue[qi];memset(oldkey.d,0,sizeof(oldkey.d));memset(oldkey.zero,0,sizeof(oldkey.zero));memset(oldkey.known,0,sizeof(oldkey.known)); \
    if(memcmp(&oldkey,&key,sizeof(key))) continue; \
    for(size_t md=0;md<8;md++) {candidate.zero[md]&=queue[qi].zero[md];if(!candidate.known[md] || !queue[qi].known[md] || candidate.d[md]!=queue[qi].d[md]) candidate.known[md]=0,candidate.d[md]=0;} \
    if(!memcmp(&queue[qi],&candidate,sizeof(candidate))) break; \
    queue[qi]=candidate;if(qi<head) {if(count==MR_PROOF_LIMIT) MR_FAIL("pointer_proof_state_limit");queue[count++]=candidate;}break; \
  } \
  if(qi==count) {if(count==MR_PROOF_LIMIT) MR_FAIL("pointer_proof_state_limit");queue[count++]=candidate;}} while(0)
  while(head<count) {
    MRProofState state=queue[head++],next=state;result.states++;
    const M68kRenderPlannedInstruction *ins=mr_instruction(a,state.pc);
    const M68kSimFormMetadata *m=ins ? m68k_sim_metadata_for_instruction(&ins->instruction) : NULL;
    if(!m) MR_FAIL("unaccepted_or_unsupported_pointer_path");
    if(ins->instruction.target_cpu!=M68K_ASM_CPU_68000) MR_FAIL("unsupported_pointer_cpu_scope");
    if(m->flow_kind==M68K_SIM_FLOW_TRAP) MR_FAIL("unmodeled_pointer_exception");
    if((state.saved_count || state.depth) && (m->operation_type==M68K_SIM_OP_LINK || m->operation_type==M68K_SIM_OP_UNLK)) MR_FAIL("saved_pointer_frame_address_escape");
    M68kSimCpuState cpu;M68kSimStepResult step;m68k_sim_cpu_state_init_unknown(&cpu);
    if(state.live) {cpu.a[state.reg].kind=M68K_SIM_VALUE_CONSTANT;cpu.a[state.reg].value=region->runtime_address+state.offset;}
    cpu.a[7].kind=M68K_SIM_VALUE_CONSTANT;cpu.a[7].value=(uint32_t)(0x900000+state.sp);
    for(size_t d=0;d<8;d++) if(state.known[d]) {cpu.d[d].kind=M68K_SIM_VALUE_CONSTANT;cpu.d[d].value=state.d[d];}
    int dependent_write=0,independent_kill=0;int32_t cursor_update=0;uint32_t computed_offset=0;
    int stack_push=0,stack_restore=-1;
    if(m->operation_type==M68K_SIM_OP_MOVE && m->source_operand_index<ins->instruction.operand_count && m->dest_operand_index<ins->instruction.operand_count) {
      const M68kOperandIR *source=&ins->instruction.operands[m->source_operand_index], *dest=&ins->instruction.operands[m->dest_operand_index];
      M68kAsmOperandValue source_address,dest_address;
      m68k_instruction_operand_to_asm_value(source,&source_address);m68k_instruction_operand_to_asm_value(dest,&dest_address);
      if(state.live && mr_direct_reg(source,1,state.reg) && mr_shape(dest)==M68K_SIM_EA_SHAPE_PREDECREMENT && dest_address.ea_reg==7 &&
          m68k_sim_operand_width_bytes(&ins->instruction,m->dest_operand_index)==4) stack_push=1;
      if(mr_shape(source)==M68K_SIM_EA_SHAPE_POSTINCREMENT && source_address.ea_reg==7 && mr_direct_reg(dest,1,state.reg) &&
          m68k_sim_operand_width_bytes(&ins->instruction,m->source_operand_index)==4) {
        for(size_t slot=0;slot<state.saved_count;slot++) if(state.saved_sp[slot]==state.sp) stack_restore=(int)slot;
      }
    }

    for(size_t j=0;j<ins->instruction.operand_count;j++) {
      const M68kOperandIR *o=&ins->instruction.operands[j];uint8_t access=m->operand_access_kinds[j];
      if(state.live && mr_direct_reg(o,1,state.reg)) {
        if((access==M68K_SIM_ACCESS_REGISTER_READ || access==M68K_SIM_ACCESS_MEMORY_READ) && m->flow_kind!=M68K_SIM_FLOW_RETURN && !stack_push) MR_FAIL("pointer_value_escape_or_comparison");
        if(access==M68K_SIM_ACCESS_REGISTER_WRITE || access==M68K_SIM_ACCESS_MEMORY_WRITE) {
          if(m->operation_type==M68K_SIM_OP_MOVE || m->operation_class==M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS) independent_kill=1;
          else MR_FAIL("unsupported_pointer_arithmetic");
        }
      }
      if(mr_direct_reg(o,1,7) && (access==M68K_SIM_ACCESS_REGISTER_WRITE || access==M68K_SIM_ACCESS_MEMORY_WRITE))
        MR_FAIL("unsupported_pointer_stack_replacement");
      if((state.saved_count || state.depth) && mr_direct_reg(o,1,7) &&
          (access==M68K_SIM_ACCESS_REGISTER_READ || access==M68K_SIM_ACCESS_MEMORY_READ)) MR_FAIL("saved_pointer_frame_address_escape");
      if(o->value.full_ext_base_suppress || o->value.full_ext_index_suppress || o->value.full_ext_base_disp_size ||
          o->value.full_ext_outer_disp_size || o->value.full_ext_iis || o->kind==M68K_ASM_OPERAND_BF_EA) MR_FAIL("unsupported_pointer_ea_scope");
      uint8_t shape=mr_shape(o);
      M68kAsmOperandValue normalized;
      m68k_instruction_operand_to_asm_value(o,&normalized);
      if(shape>=M68K_SIM_EA_SHAPE_INDIRECT && shape<=M68K_SIM_EA_SHAPE_INDEX && normalized.ea_reg==7 && m->operation_type!=M68K_SIM_OP_MOVE_MULTIPLE) {
        unsigned stack_width=m68k_sim_operand_width_bytes(&ins->instruction,(uint8_t)j);
        int64_t stack_start=state.sp;
        if(shape==M68K_SIM_EA_SHAPE_DISPLACEMENT) stack_start+=(int16_t)o->value.value;
        if(shape==M68K_SIM_EA_SHAPE_INDEX && (state.saved_count || state.depth)) MR_FAIL("unresolved_saved_pointer_stack_index");
        if(shape==M68K_SIM_EA_SHAPE_PREDECREMENT) stack_start-=stack_width;
        if((state.saved_count || state.depth) && access==M68K_SIM_ACCESS_COMPUTE_ADDRESS) MR_FAIL("saved_pointer_frame_address_escape");
        for(size_t slot=0;slot<state.saved_count;slot++) if(stack_start < state.saved_sp[slot]+4 && state.saved_sp[slot] < stack_start+stack_width && (int)slot!=stack_restore)
          MR_FAIL("saved_pointer_stack_alias_access");
        for(size_t slot=0;slot<state.depth;slot++) if(stack_start<state.return_sp[slot]+4 && state.return_sp[slot]<stack_start+stack_width)
          MR_FAIL("pointer_return_slot_access");
        if(shape==M68K_SIM_EA_SHAPE_POSTINCREMENT) next.sp+=stack_width;
        if(shape==M68K_SIM_EA_SHAPE_PREDECREMENT) next.sp-=stack_width;
      }
      if((state.live || state.saved_count || state.depth) &&
          (access==M68K_SIM_ACCESS_MEMORY_WRITE || (state.saved_count && access==M68K_SIM_ACCESS_MEMORY_READ)) &&
          shape>=M68K_SIM_EA_SHAPE_INDIRECT && shape<=M68K_SIM_EA_SHAPE_INDEX && normalized.ea_reg!=7 &&
          (!state.live || normalized.ea_reg!=state.reg)) MR_FAIL("unresolved_pointer_frame_alias");
      if(!state.live || shape<M68K_SIM_EA_SHAPE_INDIRECT || shape>M68K_SIM_EA_SHAPE_INDEX || normalized.ea_reg!=state.reg) continue;
      int64_t low=state.offset,high=low;
      if(shape==M68K_SIM_EA_SHAPE_DISPLACEMENT || shape==M68K_SIM_EA_SHAPE_INDEX) low=high=low+(int16_t)o->value.value;
      if(shape==M68K_SIM_EA_SHAPE_INDEX) {
        if(o->value.index_is_address) MR_FAIL("unbounded_address_index");
        uint32_t maximum=state.known[o->value.index_reg] ? state.d[o->value.index_reg] : ~state.zero[o->value.index_reg];
        if((o->value.index_long && maximum>INT32_MAX) || (!o->value.index_long && maximum>INT16_MAX)) MR_FAIL("unbounded_signed_index");
        high+=(int64_t)maximum*(1U<<o->value.scale);
      }
      unsigned width=mr_access_width(&ins->instruction,m,(uint8_t)j);
      if(shape==M68K_SIM_EA_SHAPE_PREDECREMENT) low-=width,high-=width;
      if(access==M68K_SIM_ACCESS_MEMORY_READ || access==M68K_SIM_ACCESS_MEMORY_WRITE) {
        if(!width || low<0 || high+(int64_t)width>region->size) MR_FAIL("pointer_access_outside_region");
        if((uint32_t)low<result.minimum_offset) result.minimum_offset=(uint32_t)low;
        if((uint32_t)(high+width)>result.maximum_end) result.maximum_end=(uint32_t)(high+width);
        result.access_count++;
      } else if(access==M68K_SIM_ACCESS_COMPUTE_ADDRESS) {
        if(m->operation_class!=M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS || m->dest_operand_index>=ins->instruction.operand_count ||
            !mr_direct_reg(&ins->instruction.operands[m->dest_operand_index],1,state.reg)) MR_FAIL("pointer_value_escape_or_comparison");
        if(low!=high || low<0 || low>region->size) MR_FAIL("unresolved_pointer_arithmetic");
        dependent_write=1;computed_offset=(uint32_t)low;
      }
      else if(access==M68K_SIM_ACCESS_BRANCH_TARGET) MR_FAIL("region_pointer_control_transfer");
      if(shape==M68K_SIM_EA_SHAPE_POSTINCREMENT || shape==M68K_SIM_EA_SHAPE_PREDECREMENT) {
        if(!width || cursor_update) MR_FAIL("unsupported_cursor_update");
        cursor_update=shape==M68K_SIM_EA_SHAPE_POSTINCREMENT ? (int32_t)width : -(int32_t)width;
      }
    }
    if(stack_push) {
      if(next.saved_count==MR_CALL_LIMIT) MR_FAIL("pointer_stack_alias_limit");
      next.saved_sp[next.saved_count]=next.sp;next.saved_offset[next.saved_count]=state.offset;next.saved_count++;
    }
    if(stack_restore>=0) {
      next.offset=state.saved_offset[stack_restore];next.live=1;
      for(size_t slot=(size_t)stack_restore+1;slot<state.saved_count;slot++) {
        next.saved_sp[slot-1]=state.saved_sp[slot];next.saved_offset[slot-1]=state.saved_offset[slot];
      }
      next.saved_count--;next.saved_sp[next.saved_count]=0;next.saved_offset[next.saved_count]=0;
    }
    if(independent_kill && !dependent_write && stack_restore<0) {
      if(!next.saved_count) continue;
      next.live=0;
    }
    if(m->operation_type==M68K_SIM_OP_MOVE_MULTIPLE) {
      uint32_t mask=ins->instruction.operands[m->reglist_operand_index].value.value;
      uint8_t width=m68k_sim_operand_width_bytes(&ins->instruction,m->address_operand_index);
      unsigned registers=0,preceding=0;
      for(unsigned bit=0;bit<16;bit++) if(mask & (1U<<bit)) {registers++;if(bit<8U+state.reg) preceding++;}
      M68kAsmOperandValue address; m68k_instruction_operand_to_asm_value(&ins->instruction.operands[m->address_operand_index],&address);
      uint8_t shape=mr_shape(&ins->instruction.operands[m->address_operand_index]);
      if(state.saved_count || state.depth || (state.live && (mask & (1U<<(8U+state.reg))))) {
        if(address.ea_reg!=7 || width!=4 ||
           (m->multi_transfer_direction==M68K_SIM_MULTI_REGISTER_TO_MEMORY && shape!=M68K_SIM_EA_SHAPE_PREDECREMENT) ||
           (m->multi_transfer_direction==M68K_SIM_MULTI_MEMORY_TO_REGISTER && shape!=M68K_SIM_EA_SHAPE_POSTINCREMENT)) MR_FAIL("unsupported_pointer_stack_transfer");
      }
      if(address.ea_reg==7 && width==4) {
        int32_t start=shape==M68K_SIM_EA_SHAPE_PREDECREMENT ? state.sp-4*(int32_t)registers : state.sp;
        for(size_t slot=0;slot<state.depth;slot++) if(start<state.return_sp[slot]+4 && state.return_sp[slot]<start+4*(int32_t)registers)
          MR_FAIL("pointer_return_slot_access");
        if(m->multi_transfer_direction==M68K_SIM_MULTI_REGISTER_TO_MEMORY && shape==M68K_SIM_EA_SHAPE_PREDECREMENT) {
          next.sp-=4*(int32_t)registers;
          if(state.live && (mask & (1U<<(8U+state.reg)))) {
            if(next.saved_count==MR_CALL_LIMIT) MR_FAIL("pointer_stack_alias_limit");
            next.saved_sp[next.saved_count]=next.sp+4*(int32_t)preceding;
            next.saved_offset[next.saved_count]=state.offset;next.saved_count++;
          }
        } else if(m->multi_transfer_direction==M68K_SIM_MULTI_MEMORY_TO_REGISTER && shape==M68K_SIM_EA_SHAPE_POSTINCREMENT) {
          int found=-1;
          for(size_t slot=0;slot<state.saved_count;slot++) if(state.saved_sp[slot]>=state.sp && state.saved_sp[slot]<state.sp+4*(int32_t)registers) {
            if(!(mask & (1U<<(8U+state.reg))) || state.saved_sp[slot]!=state.sp+4*(int32_t)preceding || found>=0) MR_FAIL("saved_pointer_restored_to_other_register");
            found=(int)slot;
          }
          if(found>=0) {
            next.offset=state.saved_offset[found];next.live=1;
            for(size_t slot=(size_t)found+1;slot<state.saved_count;slot++) {
              next.saved_sp[slot-1]=state.saved_sp[slot];next.saved_offset[slot-1]=state.saved_offset[slot];
            }
            next.saved_count--;next.saved_sp[next.saved_count]=0;next.saved_offset[next.saved_count]=0;
          } else if(mask & (1U<<(8U+state.reg))) next.live=0;
          next.sp+=4*(int32_t)registers;
        }
      }
      if(!next.live && !next.saved_count) continue;
    }
    if(m68k_simulate_step(&a->object,0,&a->object.sections[0],state.pc,&ins->instruction,&cpu,&step)) MR_FAIL("pointer_transfer_simulation_failed");
    uint8_t dirty[8]={0};
    for(size_t j=0;j<ins->instruction.operand_count;j++) {
      uint8_t address,index;
      if(m68k_instruction_operand_direct_register(&ins->instruction.operands[j],&address,&index) && !address &&
          (m->operand_access_kinds[j]==M68K_SIM_ACCESS_REGISTER_WRITE || m->operand_access_kinds[j]==M68K_SIM_ACCESS_MEMORY_WRITE)) dirty[index]=1;
    }
    if(m->operation_type==M68K_SIM_OP_MOVE_MULTIPLE && m->multi_transfer_direction==M68K_SIM_MULTI_MEMORY_TO_REGISTER)
      for(size_t d=0;d<8;d++) if(ins->instruction.operands[m->reglist_operand_index].value.value & (1U<<d)) dirty[d]=1;
    int memory_derived=0;
    for(size_t j=0;j<ins->instruction.operand_count;j++) {
      uint8_t ar,ri;uint32_t immediate_value;
      if(m->operand_access_kinds[j]==M68K_SIM_ACCESS_MEMORY_READ &&
          !m68k_ir_operand_immediate_value(&ins->instruction.operands[j],&immediate_value) &&
          !m68k_instruction_operand_direct_register(&ins->instruction.operands[j],&ar,&ri)) memory_derived=1;
    }
    for(size_t d=0;d<8;d++) {
      next.known[d]=step.next_state.d[d].kind==M68K_SIM_VALUE_CONSTANT;
      next.d[d]=next.known[d] ? step.next_state.d[d].value : 0;
      if(next.known[d]) next.zero[d]=~next.d[d];
      else if(dirty[d]) next.zero[d]=0;
      /* The CPU simulator can resolve bytes from the original section. Those
       * bytes are not an immutability contract for running game memory. */
      if(memory_derived && dirty[d]) next.known[d]=0,next.d[d]=0,next.zero[d]=0;
    }
    /* Generated operand widths preserve upper bits on byte/word loads. */
    uint8_t di=m->dest_operand_index,dr=0,da=0;uint32_t immediate=0;
    if(di<ins->instruction.operand_count && m68k_instruction_operand_direct_register(&ins->instruction.operands[di],&da,&dr) && !da) {
      uint8_t width=m68k_sim_operand_width_bytes(&ins->instruction,di);
      if(!next.known[dr]) {
        if(m->operation_type==M68K_SIM_OP_MOVE && width) next.zero[dr]=state.zero[dr] & (width==1 ? 0xffffff00U : width==2 ? 0xffff0000U : 0U);
        else if(m->operation_type==M68K_SIM_OP_BIT_CLEAR && m68k_ir_operand_immediate_value(&ins->instruction.operands[m->source_operand_index],&immediate)) next.zero[dr]=state.zero[dr] | (1U<<(immediate%32U));
        else if(width==1) next.zero[dr]=state.zero[dr] & 0xffffff00U;
        else next.zero[dr]=0;
      }
    }
    for(size_t j=0;j<ins->instruction.operand_count;j++) if(mr_direct_reg(&ins->instruction.operands[j],1,7) &&
        (m->operand_access_kinds[j]==M68K_SIM_ACCESS_REGISTER_WRITE || m->operand_access_kinds[j]==M68K_SIM_ACCESS_MEMORY_WRITE)) {
      if(step.next_state.a[7].kind!=M68K_SIM_VALUE_CONSTANT && (state.saved_count || state.depth)) MR_FAIL("unresolved_saved_pointer_stack_adjustment");
      if(step.next_state.a[7].kind==M68K_SIM_VALUE_CONSTANT) next.sp=(int32_t)step.next_state.a[7].value-0x900000;
    }
    if(cursor_update) next.offset=(uint32_t)((int64_t)state.offset+cursor_update);
    if(dependent_write) {
      next.offset=computed_offset;
    }
    next.pc=state.pc+(uint32_t)ins->instruction.byte_count;
    uint32_t target=mr_target(a,ins);
    if(m->flow_kind==M68K_SIM_FLOW_CALL) {
      if(target==UINT32_MAX || state.depth==MR_CALL_LIMIT) MR_FAIL("unresolved_pointer_call");
      next.sp-=4;
      next.return_sp[next.depth]=next.sp;next.returns[next.depth]=next.pc;next.functions[next.depth]=state.function_entry;next.depth++;
      next.function_entry=target;next.pc=target;MR_ADD(next);continue;
    }
    if(m->flow_kind==M68K_SIM_FLOW_RETURN) {
      if(m->return_restore_kind!=M68K_SIM_RETURN_RESTORE_PC_ONLY || m->return_stack_adjust_operand_index<ins->instruction.operand_count)
        MR_FAIL("unmodeled_pointer_return");
      if(state.depth && state.sp!=state.return_sp[state.depth-1]) MR_FAIL("pointer_return_stack_imbalance");
      if(!state.depth && state.sp!=0) MR_FAIL("pointer_return_stack_imbalance");
      if(state.depth) {next.sp+=4;next.depth--;next.pc=state.returns[next.depth];next.function_entry=state.functions[next.depth];next.returns[next.depth]=next.functions[next.depth]=0;next.return_sp[next.depth]=0;MR_ADD(next);continue;}
      if(state.saved_count) MR_FAIL("saved_pointer_return_escape");
      if(state.function_entry==UINT32_MAX) MR_FAIL("unresolved_pointer_return_context");
      /* The root may start mid-function; its prefix must preserve the entry
       * return frame. A root killed before RETURN does not require this. */
      if(!mr_root_prefix_frame(a,queue[0].function_entry,root->source_offset)) MR_FAIL("unmodeled_pointer_prefix_frame");
      for(size_t e=0;e<section->edge_count;e++) if(section->edges[e].target_offset==state.function_entry && section->edges[e].kind!=M68K_CFG_EDGE_CALL &&
          mr_owner(a,section->edges[e].source_offset)!=state.function_entry) MR_FAIL("unmodeled_pointer_tail_context");
      int callers=0;
      for(size_t e=0;e<section->edge_count;e++) if(section->edges[e].kind==M68K_CFG_EDGE_CALL && section->edges[e].target_offset==state.function_entry) {
        const M68kRenderPlannedInstruction *call=mr_instruction(a,section->edges[e].source_offset);
        if(!call) MR_FAIL("unaccepted_pointer_caller");
        next.pc=call->source_offset+(uint32_t)call->instruction.byte_count;next.function_entry=mr_owner(a,call->source_offset);
        if(!mr_root_prefix_frame(a,next.function_entry,call->source_offset)) MR_FAIL("unmodeled_pointer_caller_frame");
        MR_ADD(next);callers++;
      }
      if(!callers && !mr_callback_restore(a,state.function_entry,state.reg)) MR_FAIL("unresolved_pointer_return_context");
      continue;
    }
    if(m->flow_kind==M68K_SIM_FLOW_BRANCH || m->flow_kind==M68K_SIM_FLOW_JUMP) {
      if(target==UINT32_MAX) MR_FAIL("unresolved_pointer_branch");
      int take=1,fall=m->flow_conditional;
      if(m->operation_type==M68K_SIM_OP_DBCC && m->condition_code==1 && ins->instruction.operand_count &&
          m68k_instruction_operand_direct_register(&ins->instruction.operands[0],&da,&dr) && !da && next.known[dr]) {
        take=(next.d[dr]&0xffffU)!=0xffffU;fall=!take;
      }
      if(fall) MR_ADD(next);
      if(take) {next.pc=target;MR_ADD(next);}continue;
    }
    MR_ADD(next);
  }
done:free(queue);return result;
#undef MR_FAIL
#undef MR_ADD
}
