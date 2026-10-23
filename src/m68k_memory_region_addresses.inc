/* Address identity comes from canonical materialized views and accepted
 * operand references. No renderer text or target-specific base is consumed. */
static int mr_mapped_span(const PlatformFileListingArtifact *a,const M68kMemoryRegionIR *r,
    uint32_t *section,uint32_t *offset) {
  if(!r->source_mapped) return 0;
  if(m68k_runtime_map_resolve(&a->runtime_map,r->runtime_address,r->size,section,offset,NULL)!=1 ||
      *section>=a->object.section_count || *offset>a->object.sections[*section].data_size ||
      r->size>a->object.sections[*section].data_size-*offset) return -1;
  return 1;
}
static int mr_source_address(const PlatformFileListingArtifact *a,uint32_t section,uint32_t offset,uint32_t *address) {
  int found=0;
  for(size_t si=0;si<a->source_analysis.section_count;si++) {
    const M68kSectionAnalysisIR *s=&a->source_analysis.sections[si];
    if(s->section_index!=section) continue;
    for(size_t vi=0;vi<s->runtime_view_count;vi++) {
      const M68kRuntimeViewIR *v=&s->runtime_views[vi];
      if(!v->materialized || offset<v->storage_offset || offset-v->storage_offset>=v->size) continue;
      uint32_t candidate=v->runtime_address+(offset-v->storage_offset),ts,to;
      if(platform_artifact_runtime_source_local(a,candidate,&ts,&to)!=1 || ts!=section || to!=offset) return -1;
      if(found && candidate!=*address) return -1;
      *address=candidate;found=1;
    }
  }
  return found;
}
/* 1 absolute, 2 immediate (not necessarily a pointer), 3 PC displacement,
 * 4 PC index (reference only; bounds remain unresolved). */
static int mr_operand_address(const PlatformFileListingArtifact *a,const M68kRenderPlannedInstruction *ins,
    size_t operand,uint32_t *address) {
  const M68kOperandIR *o=&ins->instruction.operands[operand];
  if(m68k_asm_operand_absolute_value(o->kind,&o->value,address)) return 1;
  if(m68k_ir_operand_immediate_value(o,address)) return 2;
  uint8_t shape=mr_shape(o);
  if(shape!=M68K_SIM_EA_SHAPE_PC_DISPLACEMENT && shape!=M68K_SIM_EA_SHAPE_PC_INDEX) return 0;
  uint32_t pc=0,section=0,offset=0;int found=0,ambiguous=0;
  for(size_t i=0;i<ins->symbol_access_count;i++) {
    const M68kRenderPlannedSymbolAccess *s=&ins->symbol_accesses[i];
    if(s->operand_index!=operand || !s->has_target || s->comment_only) continue;
    if(found && (section!=s->target_section_index || offset!=s->target_offset)) ambiguous=1;
    section=s->target_section_index;offset=s->target_offset;found=1;
  }
  if(!found && o->symbol_ref.has_section_offset) {
    section=(uint32_t)o->symbol_ref.section_index;offset=o->symbol_ref.section_offset;found=1;
  }
  if(shape==M68K_SIM_EA_SHAPE_PC_INDEX) {
    if(!ambiguous && found && mr_source_address(a,section,offset,address)==1) return 4;
    *address=UINT32_MAX;return -4;
  }
  if(mr_source_address(a,ins->source_section_index,ins->source_offset,&pc)!=1) {
    *address=UINT32_MAX;return -3;
  }
  InstructionSpec spec;m68k_instruction_ir_to_spec(&ins->instruction,&spec);
  size_t bias=m68k_asm_operand_relative_base_offset(spec.asm_form_index,spec.operands,
      spec.operand_count,spec.size_suffix,operand,0);
  int64_t encoded=(int64_t)pc+bias+(int32_t)m68k_sign_extend32(o->value.value,16U);
  if(encoded<0 || encoded>=0x1000000) { *address=UINT32_MAX;return -3; }
  *address=(uint32_t)encoded;
  uint32_t target;
  if(ambiguous || !found || mr_source_address(a,section,offset,&target)!=1 || target!=*address) return -3;
  return 3;
}
static int mr_overlaps(uint32_t address,uint32_t width,uint32_t start,uint32_t size) {
  return (uint64_t)address+(width ? width : 1U)>start && address<(uint64_t)start+size;
}
