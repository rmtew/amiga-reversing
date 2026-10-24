/* Source-backed allocation uses frozen target identities, never raw numeric
 * containment as evidence that a scalar is a pointer. Shares the existing
 * actual-layout/collision/field-overlap machinery with runtime owners. */
static int mr_allocation_source_image(const PlatformFileListingArtifact *a,
    const M68kMemoryRegionIR *r,const M68kBootstrapContractIR *boot) {
  uint32_t section=0,offset=0;
  return boot && r->source_mapped && r->region_kind==1 && !r->parent_region_id[0] &&
    !r->has_loader_seed && r->alignment<=8 && !strcmp(r->region_id,boot->image_region_id) &&
    mr_mapped_span(a,r,&section,&offset)==1 && section==0 && offset==0 &&
    r->size==boot->copied_source_end && a->object.section_count==1;
}
static const char *mr_image_interpreted_target(const PlatformFileListingArtifact *a,
    const M68kRenderPlannedExpression *e,uint32_t *target,int *found) {
  *found=0;
  for(size_t i=0;i<a->policy.manual_runtime_address_ref_count;i++) {
    const M68kAnalysisManualRuntimeAddressRef *ref=&a->policy.manual_runtime_address_refs[i];
    if(!ref->has_section_index || ref->section_index!=e->source_section_index || ref->offset!=e->source_offset ||
        strcmp(ref->owner_kind,"data_block_interpreted_ref")) continue;
    if(!ref->has_target || !ref->has_runtime_address || ref->size!=4 ||
        ref->target_section_index!=0 || ref->runtime_address!=e->logical_address)
      return "unsupported_interpreted_image_pointer";
    uint32_t address=0;
    if(mr_source_address(a,ref->target_section_index,ref->target_offset,&address)!=1 || address!=ref->runtime_address)
      return "interpreted_image_pointer_mapping_mismatch";
    if(*found && *target!=ref->target_offset) return "conflicting_interpreted_image_pointer";
    *target=ref->target_offset;*found=1;
  }
  return NULL;
}
static const char *mr_image_instruction_fixup(const PlatformFileListingArtifact *a,
    const M68kMemoryRegionIR *r,const M68kBootstrapContractIR *boot,
    const M68kRenderPlannedExpression *e,uint32_t staged,MRAllocationFixup *out,int *emitted) {
  *emitted=0;
  const M68kRenderPlannedInstruction *ins=m68k_render_plan_find_instruction(&a->source_plan,e->source_section_index,e->source_offset);
  if(!ins || e->operand_index>=ins->instruction.operand_count) return "missing_image_instruction_identity";
  size_t operand=e->operand_index;
  const M68kOperandIR *o=&ins->instruction.operands[operand];
  uint32_t address=0;int immediate=m68k_ir_operand_immediate_value(o,&address);
  int absolute=m68k_asm_operand_absolute_value(o->kind,&o->value,&address);
  const M68kSimFormMetadata *m=m68k_sim_metadata_for_instruction(&ins->instruction);
  if(!absolute && !immediate) {
    uint8_t shape=mr_shape(o);
    /* Encoded relative values remain invariant only when both storage and
     * target move with this source owner. Labels embedded in branch opwords
     * require generated control-flow identity rather than an address scan. */
    if(e->source_section_index || e->source_offset>=r->size ||
        (shape!=M68K_SIM_EA_SHAPE_PC_DISPLACEMENT && shape!=M68K_SIM_EA_SHAPE_PC_INDEX &&
         !(m && m->target_operand_index==operand && m->flow_kind!=M68K_SIM_FLOW_SEQUENTIAL)))
      return "unsupported_image_operand_encoding";
    return NULL;
  }
  if(absolute) {
    if(!m) return "unsupported_image_operand_semantics";
    if(m->operand_access_kinds[operand]==M68K_SIM_ACCESS_MEMORY_READ ||
        m->operand_access_kinds[operand]==M68K_SIM_ACCESS_MEMORY_WRITE) {
      uint32_t width=mr_access_width(&ins->instruction,m,(uint8_t)operand);
      if(!width || width>r->size-e->target_offset) return "partial_image_operand_access";
    }
  }
  if(boot->has_exit_dispatch && e->source_offset==boot->exit_dispatch_call_source_offset) {
    M68kBootstrapExitImport import;
    if(!m68k_render_plan_exit_dispatch_import(&a->source_plan,boot,r->runtime_address,staged-e->target_offset,&import))
      return "image_exit_import_not_admitted";
    return NULL; /* Owned host import, deliberately excluded from image fields. */
  }
  InstructionSpec spec;unsigned char before[32],after[32];size_t offset=0,width=0;
  m68k_instruction_ir_to_spec(&ins->instruction,&spec);
  if(m68k_asm_operand_extension_span(spec.asm_form_index,spec.operands,spec.operand_count,spec.size_suffix,
      operand,&offset,&width) || width!=4 || offset<2) return "image_pointer_requires_contiguous_LONG_extension";
  size_t n=m68k_instruction_spec_assemble_bytes(&spec,before,sizeof(before));
  if(!n || n!=ins->instruction.byte_count || offset+width>n || e->source_section_index ||
      e->source_offset>r->size || n>r->size-e->source_offset ||
      memcmp(before,a->object.sections[0].data+e->source_offset,n) ||
      m68k_read_u32be(before+offset)!=r->runtime_address+e->target_offset)
    return "stale_or_nonabsolute_image_operand_encoding";
  M68kInstructionIR changed=ins->instruction;
  changed.operands[operand].value.value=staged;
  memset(&changed.operands[operand].symbol_ref,0,sizeof(changed.operands[operand].symbol_ref));
  m68k_instruction_ir_to_spec(&changed,&spec);
  if(m68k_instruction_spec_assemble_bytes(&spec,after,sizeof(after))!=n || m68k_read_u32be(after+offset)!=staged)
    return "image_operand_reencoding_mismatch";
  for(size_t i=0;i<n;i++) if((i<offset || i>=offset+width) && before[i]!=after[i])
    return "image_operand_patch_escapes_extension";
  *out=(MRAllocationFixup){.source_offset=e->source_offset+(uint32_t)offset,
    .region_offset=e->target_offset,.staged_value=staged,.instruction_offset=e->source_offset,
    .opcode=m68k_read_u16be(before),.width=4,.operand_index=(uint8_t)operand,
    .instruction_field=immediate ? 2:1,.symbol=e->target_symbol,.has_source_target=1,
    .target_offset=e->target_offset};
  *emitted=1;return NULL;
}
static const char *mr_allocation_image_fixups(const PlatformFileListingArtifact *a,
    const M68kMemoryRegionIR *r,const M68kBootstrapContractIR *boot,uint32_t staged,
    MRAllocationFixup *sites,size_t capacity,size_t *count,const M68kRenderPlannedExpression **refused) {
  for(size_t i=0;i<a->source_plan.expression_count;i++) {
    const M68kRenderPlannedExpression *e=&a->source_plan.expressions[i];
    *refused=e;
    uint32_t target=0;int found=0;
    int pointer=e->kind==M68K_RENDER_PLANNED_EXPRESSION_DATA_POINTER || e->kind==M68K_RENDER_PLANNED_EXPRESSION_TABLE_ENTRY;
    if(e->has_target) {
      if(e->target_section_index || e->target_offset>=r->size) {
        if(e->kind==M68K_RENDER_PLANNED_EXPRESSION_INSTRUCTION_OPERAND &&
            !e->source_section_index && e->source_offset<r->size) {
          const M68kRenderPlannedInstruction *ins=m68k_render_plan_find_instruction(&a->source_plan,0,e->source_offset);
          if(!ins || e->operand_index>=ins->instruction.operand_count) return "missing_image_instruction_identity";
          const M68kOperandIR *o=&ins->instruction.operands[e->operand_index];
          const M68kSimFormMetadata *m=m68k_sim_metadata_for_instruction(&ins->instruction);
          if(mr_shape(o)==M68K_SIM_EA_SHAPE_PC_DISPLACEMENT || mr_shape(o)==M68K_SIM_EA_SHAPE_PC_INDEX ||
              (m && m->target_operand_index==e->operand_index && m->flow_kind!=M68K_SIM_FLOW_SEQUENTIAL &&
               o->kind==M68K_ASM_OPERAND_LABEL)) return "cross_owner_relative_image_reference";
        }
        continue;
      }
      if(e->outcome!=M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) return "unresolved_image_source_identity";
      target=e->target_offset;found=1;
    } else if(pointer && e->pointer_width==4 && e->pointer_address_domain==M68K_ANALYSIS_POINTER_DOMAIN_RUNTIME_ONLY) {
      uint32_t address=0;
      const char *reason=mr_image_interpreted_target(a,e,&target,&found);if(reason) return reason;
      if(found && target>=r->size) continue;
      if(!found && mr_pointer_runtime_address(a,e,&address) && address>=r->runtime_address && address-r->runtime_address<r->size) {
        target=address-r->runtime_address;found=1;
      }
      if(!found && e->logical_address>=r->runtime_address && e->logical_address-r->runtime_address<r->size)
        return "unresolved_runtime_image_pointer";
    }
    if(!found) continue;
    if(e->kind==M68K_RENDER_PLANNED_EXPRESSION_RELATIVE) {
      if(!e->has_base_target || e->base_section_index || e->base_offset>=r->size ||
          e->source_section_index || e->source_offset>=r->size) return "cross_owner_relative_image_reference";
      continue;
    }
    if(*count>=capacity) return "fixup_capacity_exceeded";
    if(e->kind==M68K_RENDER_PLANNED_EXPRESSION_INSTRUCTION_OPERAND) {
      if(e->outcome!=M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) return "unresolved_image_instruction_reference";
      int emitted=0;const char *reason=mr_image_instruction_fixup(a,r,boot,e,staged+target,&sites[*count],&emitted);
      if(reason) return reason;
      *count+=(size_t)emitted;continue;
    }
    if(!pointer) continue;
    if(e->pointer_width!=4 || e->source_section_index || e->source_offset>r->size || r->size-e->source_offset<4 ||
        m68k_read_u32be(a->object.sections[0].data+e->source_offset)!=r->runtime_address+target)
      return "unsupported_or_stale_image_data_pointer";
    sites[(*count)++]=(MRAllocationFixup){.source_offset=e->source_offset,.region_offset=target,
      .staged_value=staged+target,.width=4,.symbol=e->target_symbol,.has_source_target=1,.target_offset=target,
      .pointer_domain_plus_one=(uint8_t)(e->pointer_address_domain+1)};
  }
  *refused=NULL;return NULL;
}
