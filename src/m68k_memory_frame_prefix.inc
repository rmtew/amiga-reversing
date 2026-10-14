/* Native prefix frame interpretation. Relative offsets are not guest addresses.
 * A modeled effect never supplies an absolute SP or discharges other-base alias
 * obligations. Every admitted CALL must return through its intact native slot. */
typedef struct MRFramePrefixState {
  uint32_t pc, returns[MR_CALL_LIMIT];
  int32_t sp, return_sp[MR_CALL_LIMIT];
  uint8_t depth;
} MRFramePrefixState;
typedef struct MRFramePrefixResult {
  uint32_t entry, failure_offset, states, paths;
  int32_t delta, minimum_delta, maximum_delta;
  const char *reason;
} MRFramePrefixResult;

static int mr_full_ea(const M68kOperandIR *o) {
  return o->kind==M68K_ASM_OPERAND_BF_EA || o->value.full_ext_base_suppress ||
    o->value.full_ext_index_suppress || o->value.full_ext_base_disp_size ||
    o->value.full_ext_outer_disp_size || o->value.full_ext_iis;
}
static MRFramePrefixResult mr_frame_prefix(const PlatformFileListingArtifact *a,
    uint32_t entry,uint32_t root) {
  MRFramePrefixResult result={0};result.entry=entry;
  int32_t pc_width=mr_pc_frame_width(a);
  MRFramePrefixState *queue=calloc(MR_PROOF_LIMIT,sizeof(*queue));size_t count=1,head=0;
  if(!queue) {result.reason="frame_prefix_allocation_failed";return result;}
  if(entry==UINT32_MAX) {result.reason="unknown_frame_entry";goto done;}
  queue[0].pc=entry;
#define MRF_FAIL(message) do {result.reason=(message);result.failure_offset=state.pc;goto done;} while(0)
#define MRF_ADD(candidate) do {MRFramePrefixState value=(candidate);size_t q; \
  for(q=0;q<count;q++) if(!memcmp(&queue[q],&value,sizeof(value))) break; \
  if(q==count) {if(count==MR_PROOF_LIMIT) MRF_FAIL("frame_prefix_state_limit");queue[count++]=value;}} while(0)
  while(head<count) {
    MRFramePrefixState state=queue[head++],next=state;result.states++;
    if(state.sp < -65536 || state.sp > 65536) MRF_FAIL("frame_prefix_extent_limit");
    if(state.sp<result.minimum_delta) result.minimum_delta=state.sp;
    if(state.sp>result.maximum_delta) result.maximum_delta=state.sp;
    if(state.pc==root && !state.depth) {
      if(result.paths && result.delta!=state.sp) MRF_FAIL("ambiguous_frame_prefix_delta");
      result.delta=state.sp;result.paths++;continue;
    }
    const M68kRenderPlannedInstruction *ins=mr_instruction(a,state.pc);
    const M68kSimFormMetadata *m=ins ? m68k_sim_metadata_for_instruction(&ins->instruction) : NULL;
    if(!m || ins->instruction.target_cpu!=M68K_ASM_CPU_68000) MRF_FAIL("unsupported_frame_prefix_instruction");
    if(m->operation_type==M68K_SIM_OP_NONE && m->operation_class==M68K_SIM_CLASS_NONE &&
        (m->flow_kind==M68K_SIM_FLOW_NONE || m->flow_kind==M68K_SIM_FLOW_SEQUENTIAL)) MRF_FAIL("unsupported_frame_prefix_instruction");
    if(m->flow_kind==M68K_SIM_FLOW_TRAP || m->operation_type==M68K_SIM_OP_LINK || m->operation_type==M68K_SIM_OP_UNLK ||
        m->operation_type==M68K_SIM_OP_PUSH_EA || m->ccr_formula==M68K_SIM_CCR_FORMULA_WRITE_SR)
      MRF_FAIL("unmodeled_frame_prefix_exception_or_link");
    unsigned stack_memory_operands=0;
    for(size_t j=0;j<ins->instruction.operand_count;j++) {
      const M68kOperandIR *o=&ins->instruction.operands[j];uint8_t access=m->operand_access_kinds[j];
      M68kAsmOperandValue v;m68k_instruction_operand_to_asm_value(o,&v);uint8_t shape=mr_shape(o);
      uint8_t ar,ri;
      if(o->kind==M68K_ASM_OPERAND_USP || (shape==M68K_SIM_EA_SHAPE_INDEX && v.index_is_address && v.index_reg==7))
        MRF_FAIL("frame_prefix_address_escape");
      if(mr_full_ea(o)) MRF_FAIL("unsupported_frame_prefix_ea");
      if(mr_direct_reg(o,1,7)) {
        if(access==M68K_SIM_ACCESS_REGISTER_READ || access==M68K_SIM_ACCESS_MEMORY_READ) MRF_FAIL("frame_prefix_address_escape");
        if(access==M68K_SIM_ACCESS_REGISTER_WRITE || access==M68K_SIM_ACCESS_MEMORY_WRITE) {
          uint32_t immediate;
          if((m->operation_type==M68K_SIM_OP_ADD || m->operation_type==M68K_SIM_OP_SUB) &&
              m->source_operand_index<ins->instruction.operand_count &&
              m68k_ir_operand_immediate_value(&ins->instruction.operands[m->source_operand_index],&immediate)) {
            M68kSimCpuState cpu;M68kSimStepResult step;m68k_sim_cpu_state_init_unknown(&cpu);
            cpu.a[7].kind=M68K_SIM_VALUE_CONSTANT;cpu.a[7].value=0x900000U+(uint32_t)state.sp;
            if(m68k_simulate_step(&a->object,0,&a->object.sections[0],state.pc,&ins->instruction,&cpu,&step) ||
                step.next_state.a[7].kind!=M68K_SIM_VALUE_CONSTANT) MRF_FAIL("unresolved_frame_prefix_adjustment");
            int64_t relative=(int64_t)step.next_state.a[7].value-0x900000;
            if(relative < -65536 || relative > 65536) MRF_FAIL("frame_prefix_extent_limit");
            next.sp=(int32_t)relative;
          } else if(m->operation_class==M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS &&
              m->source_operand_index<ins->instruction.operand_count) {
            const M68kOperandIR *source=&ins->instruction.operands[m->source_operand_index];
            M68kAsmOperandValue source_value;m68k_instruction_operand_to_asm_value(source,&source_value);
            if(mr_shape(source)!=M68K_SIM_EA_SHAPE_DISPLACEMENT || source_value.ea_reg!=7 || mr_full_ea(source))
              MRF_FAIL("frame_prefix_stack_replacement");
            next.sp=state.sp+(int16_t)source_value.value;
          } else MRF_FAIL("frame_prefix_stack_replacement");
        }
      }
      if(access==M68K_SIM_ACCESS_MEMORY_WRITE && !m68k_instruction_operand_direct_register(o,&ar,&ri) &&
          !(shape>=M68K_SIM_EA_SHAPE_INDIRECT && shape<=M68K_SIM_EA_SHAPE_INDEX && v.ea_reg==7))
        MRF_FAIL("unresolved_frame_prefix_memory_alias");
      if(shape<M68K_SIM_EA_SHAPE_INDIRECT || shape>M68K_SIM_EA_SHAPE_INDEX || v.ea_reg!=7) continue;
      if(access==M68K_SIM_ACCESS_COMPUTE_ADDRESS) {
        if(m->operation_class==M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS && mr_direct_reg(&ins->instruction.operands[m->dest_operand_index],1,7)) continue;
        MRF_FAIL("frame_prefix_address_escape");
      }
      if(++stack_memory_operands>1) MRF_FAIL("unsupported_frame_prefix_multiple_stack_operands");
      if(shape==M68K_SIM_EA_SHAPE_INDEX) MRF_FAIL("unresolved_frame_prefix_stack_index");
      unsigned width=mr_access_width(&ins->instruction,m,(uint8_t)j);
      if(!width || (m->operation_type!=M68K_SIM_OP_MOVE_MULTIPLE && width==1)) MRF_FAIL("unsupported_frame_prefix_width");
      int32_t start=state.sp;
      if(shape==M68K_SIM_EA_SHAPE_DISPLACEMENT) start+=(int16_t)v.value;
      if(shape==M68K_SIM_EA_SHAPE_PREDECREMENT) start-=(int32_t)width;
      if(start % 2) MRF_FAIL("unaligned_frame_prefix_access");
      if(access==M68K_SIM_ACCESS_MEMORY_WRITE) {
        if(!pc_width) MRF_FAIL("unknown_frame_prefix_pc_width");
        if(start<pc_width && 0<start+(int32_t)width) MRF_FAIL("frame_prefix_return_slot_write");
        for(size_t k=0;k<state.depth;k++) if(start<state.return_sp[k]+pc_width && state.return_sp[k]<start+(int32_t)width)
          MRF_FAIL("frame_prefix_return_slot_write");
      }
      if(m->operation_type==M68K_SIM_OP_MOVE_MULTIPLE &&
          (ins->instruction.operands[m->reglist_operand_index].value.value & (1U<<15))) MRF_FAIL("frame_prefix_stack_register_transfer");
      if(shape==M68K_SIM_EA_SHAPE_PREDECREMENT) next.sp-=(int32_t)width;
      if(shape==M68K_SIM_EA_SHAPE_POSTINCREMENT) next.sp+=(int32_t)width;
    }
    if(next.sp < -65536 || next.sp > 65536) MRF_FAIL("frame_prefix_extent_limit");
    if(next.sp<result.minimum_delta) result.minimum_delta=next.sp;
    if(next.sp>result.maximum_delta) result.maximum_delta=next.sp;
    next.pc=state.pc+(uint32_t)ins->instruction.byte_count;
    uint32_t target=mr_target(a,ins);
    if(m->flow_kind==M68K_SIM_FLOW_CALL) {
      if(target==UINT32_MAX || state.depth==MR_CALL_LIMIT) MRF_FAIL("unresolved_frame_prefix_call");
      int32_t delta;
      if(!pc_width || !m68k_sim_fixed_sp_delta(m,&delta) || delta!=-pc_width) MRF_FAIL("unmodeled_frame_prefix_call_effect");
      int32_t pushed=next.sp+delta;
      if(pushed % 2 || (pushed<pc_width && 0<pushed+pc_width)) MRF_FAIL("frame_prefix_call_slot_overlap");
      for(size_t k=0;k<state.depth;k++) if(pushed<state.return_sp[k]+pc_width && state.return_sp[k]<pushed+pc_width)
        MRF_FAIL("frame_prefix_call_slot_overlap");
      next.sp=pushed;next.return_sp[next.depth]=next.sp;next.returns[next.depth]=next.pc;next.depth++;
      next.pc=target;MRF_ADD(next);continue;
    }
    if(m->flow_kind==M68K_SIM_FLOW_RETURN) {
      if(m->return_restore_kind!=M68K_SIM_RETURN_RESTORE_PC_ONLY || m->return_stack_adjust_operand_index<ins->instruction.operand_count)
        MRF_FAIL("unmodeled_frame_prefix_return");
      int32_t delta;
      if(!pc_width || !m68k_sim_fixed_sp_delta(m,&delta) || delta!=pc_width) MRF_FAIL("unmodeled_frame_prefix_return");
      if(!state.depth) {
        if(state.sp!=0) MRF_FAIL("frame_prefix_entry_stack_imbalance");
        continue; /* A balanced normal return cannot reach this prefix root. */
      }
      if(state.sp!=state.return_sp[state.depth-1]) MRF_FAIL("frame_prefix_callee_stack_imbalance");
      next.sp+=delta;next.depth--;next.pc=state.returns[next.depth];next.returns[next.depth]=0;next.return_sp[next.depth]=0;
      MRF_ADD(next);continue;
    }
    if(m->flow_kind==M68K_SIM_FLOW_BRANCH || m->flow_kind==M68K_SIM_FLOW_JUMP) {
      if(target==UINT32_MAX) MRF_FAIL("unresolved_frame_prefix_branch");
      if(m->flow_conditional) MRF_ADD(next);
      next.pc=target;MRF_ADD(next);continue;
    }
    MRF_ADD(next);
  }
  if(!result.paths) result.reason="frame_prefix_root_not_reached";
done:free(queue);return result;
#undef MRF_ADD
#undef MRF_FAIL
}
