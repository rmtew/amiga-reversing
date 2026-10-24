typedef struct MRAllocationFixup {
  uint32_t source_offset,region_offset,staged_value,instruction_offset;
  uint16_t opcode;
  uint8_t width,operand_index,instruction_field;
  const char *symbol;
} MRAllocationFixup;
static int mr_allocation_fixup_order(const void *aa,const void *bb) {
  const MRAllocationFixup *a=aa,*b=bb;
  return a->source_offset<b->source_offset ? -1 : a->source_offset>b->source_offset ? 1 : 0;
}
/* Only an explicit frozen runtime symbol may admit an operand. A coincident
 * source/local-offset symbol or numeric rendered operand is not ownership. */
static const char *mr_allocation_operand_symbol(const PlatformFileListingArtifact *a,
    const M68kRenderPlannedInstruction *ins,size_t operand,uint32_t address) {
  for(size_t si=0;si<ins->symbol_access_count;si++) {
    const M68kRenderPlannedSymbolAccess *s=&ins->symbol_accesses[si];
    if(s->operand_index!=operand || s->comment_only || s->has_target ||
        s->access_kind!=M68K_RENDERED_SYMBOL_ACCESS_EQUATE || !s->symbol_name[0]) continue;
    for(size_t qi=0;qi<a->policy.target_equate_count;qi++) {
      const M68kAnalysisTargetEquate *q=&a->policy.target_equates[qi];
      if(q->address_domain && !strcmp(q->name,s->symbol_name) &&
          address>=(uint32_t)q->value &&
          (q->extent_bytes ? address-(uint32_t)q->value<q->extent_bytes : address==(uint32_t)q->value))
        return s->symbol_name;
    }
    for(size_t ri=0;ri<a->policy.memory_region_count;ri++) {
      const M68kMemoryRegionIR *r=&a->policy.memory_regions[ri];
      if(!r->source_mapped && !strcmp(r->name,s->symbol_name) &&
          address>=r->runtime_address && address-r->runtime_address<r->size) return s->symbol_name;
    }
  }
  return NULL;
}
static int mr_allocation_descends_from(const M68kAnalysisPolicy *p,size_t child,size_t owner) {
  for(size_t depth=0;depth<p->memory_region_count;depth++) {
    if(child==owner) return 1;
    const char *parent=p->memory_regions[child].parent_region_id;
    if(!parent[0]) return 0;
    size_t i=0;for(;i<p->memory_region_count;i++) if(!strcmp(parent,p->memory_regions[i].region_id)) break;
    if(i==p->memory_region_count) return 0;
    child=i;
  }
  return 0;
}
/* Coordinates come from generated form/extension metadata. Verify them against
 * the full encoder twice; never scan for address-looking words in instructions. */
static const char *mr_allocation_absolute_fixup(const PlatformFileListingArtifact *a,
    const M68kMemoryRegionIR *r,const M68kBootstrapContractIR *boot,
    const M68kRenderPlannedInstruction *ins,size_t operand,uint32_t address,
    uint32_t staged,MRAllocationFixup *out) {
  InstructionSpec spec;unsigned char before[32],after[32];
  const char *symbol=mr_allocation_operand_symbol(a,ins,operand,address);
  if(!symbol) return "numeric_or_unbound_absolute_operand";
  m68k_instruction_ir_to_spec(&ins->instruction,&spec);
  size_t count=m68k_asm_operand_extension_word_count(spec.asm_form_index,&spec.operands[operand],spec.size_suffix);
  size_t offset=m68k_asm_operand_relative_base_offset(spec.asm_form_index,spec.operands,
      spec.operand_count,spec.size_suffix,operand,0);
  size_t width=count*2,n=m68k_instruction_spec_assemble_bytes(&spec,before,sizeof(before));
  if((width!=2 && width!=4) || !n || n!=ins->instruction.byte_count || offset<2 || offset+width>n ||
      ins->source_section_index!=0 || ins->source_offset>boot->copied_source_end || n>boot->copied_source_end-ins->source_offset ||
      ins->source_offset>a->object.sections[0].data_size || n>a->object.sections[0].data_size-ins->source_offset ||
      memcmp(before,a->object.sections[0].data+ins->source_offset,n)) return "unsupported_or_stale_absolute_operand_encoding";
  uint32_t encoded=width==2 ? m68k_read_u16be(before+offset) : m68k_read_u32be(before+offset);
  if(encoded!=(width==2 ? address&0xffffU : address)) return "absolute_operand_extension_identity_mismatch";
  if(width==2 && staged>0x7fffU) return "staged_absolute_word_encoding_overflow";
  M68kInstructionIR changed=ins->instruction;
  changed.operands[operand].value.value=staged;
  memset(&changed.operands[operand].symbol_ref,0,sizeof(changed.operands[operand].symbol_ref));
  m68k_instruction_ir_to_spec(&changed,&spec);
  if(m68k_instruction_spec_assemble_bytes(&spec,after,sizeof(after))!=n) return "absolute_operand_instruction_extent_changed";
  for(size_t i=0;i<n;i++) if((i<offset || i>=offset+width) && before[i]!=after[i])
    return "absolute_operand_patch_escapes_extension";
  encoded=width==2 ? m68k_read_u16be(after+offset) : m68k_read_u32be(after+offset);
  if(encoded!=staged) return "staged_absolute_operand_encoding_mismatch";
  *out=(MRAllocationFixup){.source_offset=ins->source_offset+(uint32_t)offset,
    .region_offset=address-r->runtime_address,.staged_value=staged,.instruction_offset=ins->source_offset,
    .opcode=m68k_read_u16be(before),.width=(uint8_t)width,.operand_index=(uint8_t)operand,
    .instruction_field=1,.symbol=symbol};
  return NULL;
}

typedef struct MRAllocationRange {uint32_t start,size;} MRAllocationRange;
static int mr_allocation_range_order(const void *aa,const void *bb) {
  const MRAllocationRange *a=aa,*b=bb;
  return a->start<b->start ? -1 : a->start>b->start ? 1 : 0;
}
/* Bounded runtime-only LONG-data or reviewed absolute-operand allocation.
 * CPU operands retain encoder-derived extension coordinates and signed-W reach.
 * This is not the legacy relocation
 * proof adapter and never promotes its numeric immediate candidates to fixups.
 * Returned bases are admitted by the same canonical fixed-layout geometry. */
int platform_file_facts_v2_listing_artifact_runtime_allocation_json_alloc(
    PlatformFileListingArtifact *a,const char *region_id,const char *layout_id,
    int has_actual,uint32_t actual,char **out_text) {
  JsonBuilder b={0};PlatformFileListingArtifact *view=NULL;char *layouts=NULL;
  const char *reason=NULL;int ri=-1;size_t li=0,fixups=0,numeric=0;
  MRAllocationRange *ranges=NULL;size_t range_count=0,range_capacity=0;
  M68kResolvedMemoryLayout initial,resolved;
  MRAllocationFixup sites[32];int cpu_scope=0;uint32_t maximum_base=0xffffffU;
  const M68kRenderPlannedInstruction *frame_guards[M68K_ADDRESS_FRAME_SITE_LIMIT];size_t frame_guard_count=0;
  const M68kRenderPlannedInstruction *refusal_instruction=NULL;size_t refusal_operand=0;
  const M68kMemoryRegionIR *r=NULL;const M68kBootstrapContractIR *boot=NULL;
  if(!a || !region_id || !layout_id || !out_text) return -1;
  *out_text=NULL;
  for(size_t i=0;i<a->policy.memory_region_count;i++)
    if(!strcmp(region_id,a->policy.memory_regions[i].region_id)) ri=(int)i;
  for(;li<a->policy.memory_layout_count;li++)
    if(!strcmp(layout_id,a->policy.memory_layouts[li].layout_id)) break;
  if(ri<0 || li==a->policy.memory_layout_count) {reason="unknown_region_or_layout";goto result;}
  r=&a->policy.memory_regions[ri];cpu_scope=!r->dma_access;
  if(r->source_mapped || r->parent_region_id[0] || r->has_loader_seed ||
      r->region_kind>2 || r->alignment>8 || r->size>0x10000) {
    reason="unsupported_runtime_allocation_owner";goto result;
  }
  for(size_t i=0;i<a->policy.memory_region_count;i++) {
    if(i==(size_t)ri || !mr_allocation_descends_from(&a->policy,i,(size_t)ri)) continue;
    const M68kMemoryRegionIR *child=&a->policy.memory_regions[i];
    if(!cpu_scope) {reason="allocation_subregions_unsupported";goto result;}
    if(child->source_mapped || child->has_loader_seed || child->dma_access) {
      reason="allocation_subregion_materialization_unsupported";goto result;
    }
  }
  for(size_t i=0;i<a->policy.bootstrap_contract_count;i++)
    if(!strcmp(a->policy.bootstrap_contracts[i].contract_id,a->policy.memory_layouts[li].bootstrap_contract_id))
      boot=&a->policy.bootstrap_contracts[i];
  if(!boot) {reason="retained_input_contract_required";goto result;}
  if(m68k_memory_layout_resolve(&a->policy,&a->policy.memory_layouts[li],&initial)) {
    reason=initial.reason;goto result;
  }
  for(size_t i=0;i<a->source_plan.instruction_count;i++) {
    const M68kRenderPlannedInstruction *ins=&a->source_plan.instructions[i];
    const M68kSimFormMetadata *m=m68k_sim_metadata_for_instruction(&ins->instruction);
    for(size_t j=0;j<ins->instruction.operand_count;j++) {
      uint32_t address=0;int kind=mr_operand_address(a,ins,j,&address);
      if(kind==2) {
        if(address>=r->runtime_address && address-r->runtime_address<r->size) {
          if(cpu_scope && mr_allocation_operand_symbol(a,ins,j,address)) {
            reason="immediate_pointer_reference_unsupported";refusal_instruction=ins;refusal_operand=j;goto result;
          }
          numeric++;
        }
        continue;
      }
      uint32_t width=m ? mr_access_width(&ins->instruction,m,(uint8_t)j) : 1;
      if(m && m->operand_access_kinds[j]==M68K_SIM_ACCESS_COMPUTE_ADDRESS) width=1;
      if(!mr_overlaps(address,width ? width : 1,r->runtime_address,r->size)) continue;
      if(!kind) continue;
      if(cpu_scope && kind==1 && ins->address_frame_active &&
          ins->address_frame_region_index_plus_one==(size_t)ri+1 && j==ins->address_frame_operand_index) {
        const M68kOperandIR *operand=&ins->render_instruction.operands[j];
        if(frame_guard_count>=M68K_ADDRESS_FRAME_SITE_LIMIT ||
            m68k_instruction_operand_decoded_ea_shape(operand)!=M68K_SIM_EA_SHAPE_DISPLACEMENT ||
            operand->value.ea_reg!=r->address_frame_register ||
            operand->value.value!=address-r->runtime_address ||
            ins->address_frame_displacement!=address-r->runtime_address) {
          reason="address_frame_allocation_guard_refused";refusal_instruction=ins;refusal_operand=j;goto result;
        }
        frame_guards[frame_guard_count++]=ins;continue;
      }
      if(!cpu_scope) {reason="non_data_pointer_reference_unsupported";goto result;}
      if(kind!=1 || !m || m->flow_kind!=M68K_SIM_FLOW_SEQUENTIAL ||
          (m->operand_access_kinds[j]!=M68K_SIM_ACCESS_COMPUTE_ADDRESS &&
           m->operand_access_kinds[j]!=M68K_SIM_ACCESS_MEMORY_READ &&
           m->operand_access_kinds[j]!=M68K_SIM_ACCESS_MEMORY_WRITE)) {
        reason="unsupported_CPU_operand_reference";refusal_instruction=ins;refusal_operand=j;goto result;
      }
      if(address<r->runtime_address || !width || width>r->size-(address-r->runtime_address)) {
        reason="partial_absolute_operand_access";refusal_instruction=ins;refusal_operand=j;goto result;
      }
      if(fixups>=32) {reason="fixup_capacity_exceeded";goto result;}
      reason=mr_allocation_absolute_fixup(a,r,boot,ins,j,address,
          initial.addresses[ri]+address-r->runtime_address,&sites[fixups]);
      if(reason) {refusal_instruction=ins;refusal_operand=j;goto result;}
      if(sites[fixups].width==2) {
        uint32_t bound=0x7fffU-sites[fixups].region_offset;
        if(bound<maximum_base) maximum_base=bound;
      }
      fixups++;
    }
  }
  for(size_t i=0;i<a->source_plan.expression_count;i++) {
    const M68kRenderPlannedExpression *e=&a->source_plan.expressions[i];uint32_t address=0;
    /* An explicit runtime-only value outside this owner is not a body alias.
     * Unresolved values inside it still refuse; source offsets never enter this
     * numeric branch and require canonical target mapping above. */
    if(e->pointer_address_domain==M68K_ANALYSIS_POINTER_DOMAIN_RUNTIME_ONLY &&
        e->logical_address>=r->runtime_address && e->logical_address-r->runtime_address<r->size &&
        !mr_pointer_runtime_address(a,e,&address)) {
      reason="unresolved_runtime_pointer_site";goto result;
    }
    if(!mr_pointer_runtime_address(a,e,&address) || address<r->runtime_address || address-r->runtime_address>=r->size) continue;
    if(e->pointer_address_domain!=M68K_ANALYSIS_POINTER_DOMAIN_RUNTIME_ONLY || e->has_target ||
        e->source_section_index!=0 || e->source_section_index>=a->object.section_count ||
        e->source_offset>boot->copied_source_end || boot->copied_source_end-e->source_offset<4 ||
        e->source_offset>a->object.sections[0].data_size || a->object.sections[0].data_size-e->source_offset<4 ||
        m68k_read_u32be(a->object.sections[0].data+e->source_offset)!=e->logical_address) {
      reason="unsupported_or_stale_typed_pointer_encoding";goto result;
    }
    if(fixups>=32) {reason="fixup_capacity_exceeded";goto result;}
    sites[fixups++]=(MRAllocationFixup){.source_offset=e->source_offset,
      .region_offset=address-r->runtime_address,.staged_value=initial.addresses[ri]+address-r->runtime_address,
      .width=4,.symbol=e->target_symbol};
  }
  if(!fixups) {reason=cpu_scope ? "no_admitted_CPU_fixups" : "no_explicit_runtime_LONG_data_fixups";goto result;}
  qsort(sites,fixups,sizeof(*sites),mr_allocation_fixup_order);
  for(size_t i=1;i<fixups;i++) if(sites[i].source_offset<sites[i-1].source_offset+sites[i-1].width) {
    reason="overlapping_runtime_fixups";goto result;
  }
  range_capacity=a->policy.memory_region_count+a->policy.target_equate_count;
  ranges=calloc(range_capacity ? range_capacity : 1,sizeof(*ranges));if(!ranges) goto failed;
  for(size_t i=0;i<a->policy.memory_region_count;i++) {
    const M68kMemoryRegionIR *other=&a->policy.memory_regions[i];
    if((int)i==ri || other->parent_region_id[0]) continue;
    ranges[range_count++]=(MRAllocationRange){initial.addresses[i],other->size};
  }
  for(size_t qi=0;qi<a->policy.target_equate_count;qi++) {
    const M68kAnalysisTargetEquate *q=&a->policy.target_equates[qi];
    uint32_t address=(uint32_t)q->value;char expression[128];int owned=0;
    if(!q->address_domain || !q->extent_bytes) continue;
    if(cpu_scope && address>=r->runtime_address &&
        address-r->runtime_address<r->size && q->extent_bytes<=r->size-(address-r->runtime_address)) owned=1;
    if(address==r->runtime_address && q->extent_bytes==r->size)
      for(size_t fi=0;fi<fixups;fi++) if(sites[fi].symbol && !strcmp(sites[fi].symbol,q->name)) {owned=1;break;}
    if(owned) continue;
    if(m68k_memory_layout_reference(&a->policy,&initial,address,q->extent_bytes,
        expression,sizeof(expression),&address)<0) {reason="ambiguous_protected_runtime_extent";goto result;}
    if(m68k_memory_layout_overlaps((uint32_t)q->value,q->extent_bytes,r->runtime_address,r->size)) {
      reason="unbound_runtime_alias_of_allocation_owner";goto result;
    }
    ranges[range_count++]=(MRAllocationRange){address,q->extent_bytes};
  }
  qsort(ranges,range_count,sizeof(*ranges),mr_allocation_range_order);
  size_t merged=0;
  for(size_t i=0;i<range_count;i++) {
    uint64_t end=(uint64_t)ranges[i].start+ranges[i].size;
    if(end>0x1000000) {reason="invalid_protected_runtime_extent";goto result;}
    if(merged && ranges[i].start<=(uint64_t)ranges[merged-1].start+ranges[merged-1].size) {
      uint64_t prior=(uint64_t)ranges[merged-1].start+ranges[merged-1].size;
      if(end>prior) ranges[merged-1].size=(uint32_t)(end-ranges[merged-1].start);
    } else ranges[merged++]=ranges[i];
  }
  range_count=merged;
  if(has_actual && !actual) {reason="allocator_returned_NULL";goto result;}
  if(has_actual && m68k_memory_layout_overlaps(actual,r->size,boot->load_address,boot->file_size)) {
    reason="allocator_result_overlaps_live_input";goto result;
  }
  view=malloc(sizeof(*view));if(!view) goto failed;
  *view=*a;view->policy.memory_layout_count=1;
  view->policy.memory_layouts[0]=a->policy.memory_layouts[li];
  M68kMemoryLayoutIR *layout=&view->policy.memory_layouts[0];
  if(has_actual) {
    size_t pi=0;for(;pi<layout->placement_count;pi++) if(!strcmp(layout->placements[pi].region_id,region_id)) break;
    if(pi==layout->placement_count) {
      if(pi>=M68K_ANALYSIS_MEMORY_REGION_LIMIT) {reason="placement_capacity_exceeded";goto result;}
      layout->placement_count++;
      snprintf(layout->placements[pi].region_id,sizeof(layout->placements[pi].region_id),"%s",region_id);
    }
    layout->placements[pi].runtime_address=actual;
  }
  if(m68k_memory_layout_resolve(&view->policy,layout,&resolved)) {reason=resolved.reason;goto result;}
  if(has_actual) for(size_t i=0;i<range_count;i++)
    if(m68k_memory_layout_overlaps(actual,r->size,ranges[i].start,ranges[i].size)) {
      reason="allocator_result_overlaps_protected_runtime_extent";goto result;
    }
  if(cpu_scope && has_actual && actual>maximum_base) {reason="absolute_word_encoding_overflow";goto result;}
  if(platform_file_facts_v2_listing_artifact_memory_layouts_json_alloc(view,&layouts)) goto failed;
result:
  if(json_builder_create(&b) || json_builder_append(&b,"{\"status\":") ||
      json_builder_append_json_string(&b,reason ? "refused" : has_actual ? "actual_placement_valid" : "bounded_allocation_candidate") ||
      json_builder_append(&b,",\"reason\":") ||
      (reason ? json_builder_append_json_string(&b,reason) : json_builder_append(&b,"null"))) goto failed;
  if(refusal_instruction && json_builder_appendf(&b,
      ",\"refusal_site\":{\"source_section_index\":%u,\"source_offset\":%u,\"operand_index\":%zu}",
      refusal_instruction->source_section_index,refusal_instruction->source_offset,refusal_operand)) goto failed;
  if(!reason) {
    if(json_builder_append(&b,",\"region_id\":") || json_builder_append_json_string(&b,region_id) ||
        json_builder_appendf(&b,",\"size\":%u,\"alignment\":%u,\"memory_requirement\":\"chip\","
          "\"original_address\":%u,\"staged_address\":%u,\"numeric_immediate_candidates_not_fixups\":%zu,\"fixups\":[",
          r->size,r->alignment,r->runtime_address,initial.addresses[ri],numeric)) goto failed;
    for(size_t fi=0;fi<fixups;fi++) {
      const MRAllocationFixup *f=&sites[fi];
      const char *encoding=f->instruction_field ? (f->width==2 ? "absolute_word_operand" : "absolute_long_operand") : "absolute_long_data";
      if((fi && json_builder_append(&b,",")) || json_builder_appendf(&b,
          "{\"source_section_index\":0,\"source_offset\":%u,\"width\":%u,\"encoding\":",
          f->source_offset,f->width) || json_builder_append_json_string(&b,encoding) ||
          json_builder_appendf(&b,",\"address_domain\":\"runtime_only\",\"region_offset\":%u,\"staged_value\":%u",
          f->region_offset,f->staged_value)) goto failed;
      if(f->instruction_field && (json_builder_appendf(&b,
          ",\"instruction_source_offset\":%u,\"operand_index\":%u,\"opcode\":%u,\"symbol\":",
          f->instruction_offset,f->operand_index,f->opcode) || json_builder_append_json_string(&b,f->symbol))) goto failed;
      if(json_builder_append(&b,"}")) goto failed;
    }
    if(json_builder_append(&b,"]")) goto failed;
    if(cpu_scope && frame_guard_count) {
      if(json_builder_append(&b,",\"address_frame_contract_sha256\":") ||
          json_builder_append_json_string(&b,r->address_frame_contract_sha256) ||
          json_builder_append(&b,",\"address_frame_guards\":[")) goto failed;
      for(size_t gi=0;gi<frame_guard_count;gi++) {
        const M68kRenderPlannedInstruction *ins=frame_guards[gi];InstructionSpec spec;unsigned char bytes[32];
        m68k_instruction_ir_to_spec(&ins->render_instruction,&spec);
        size_t offset=m68k_asm_operand_relative_base_offset(spec.asm_form_index,spec.operands,
            spec.operand_count,spec.size_suffix,ins->address_frame_operand_index,0);
        if(m68k_instruction_spec_assemble_bytes(&spec,bytes,sizeof(bytes))!=8 || offset+2!=8) goto failed;
        if((gi && json_builder_append(&b,",")) || json_builder_appendf(&b,
            "{\"instruction_source_offset\":%u,\"opcode\":%u,\"displacement_source_offset\":%u,"
            "\"displacement\":%u,\"base_register\":%u,\"instruction_size\":8}",ins->source_offset,
            m68k_read_u16be(bytes),ins->source_offset+(uint32_t)offset,
            ins->address_frame_displacement,r->address_frame_register)) goto failed;
      }
      if(json_builder_append(&b,"]")) goto failed;
    }
    if(json_builder_append(&b,",\"protected_ranges\":[")) goto failed;
    for(size_t pi=0;pi<range_count;pi++)
      if((pi && json_builder_append(&b,",")) || json_builder_appendf(&b,
          "{\"address\":%u,\"size\":%u}",ranges[pi].start,ranges[pi].size)) goto failed;
    if(json_builder_append(&b,"],\"layout\":") || json_builder_append(&b,layouts) ||
        (cpu_scope && json_builder_appendf(&b,",\"maximum_actual_base\":%u",maximum_base)) ||
        json_builder_append(&b,",\"scope\":") || json_builder_append_json_string(&b,
          cpu_scope ? "reviewed_symbolic_absolute_operands_and_LONG_data_not_all_path_alias_proof" :
          "reviewed_typed_LONG_data_only_not_all_path_alias_proof") ||
        json_builder_append(&b,",\"lifetime\":\"retain_until_DMA_quiescent_exit\",\"unresolved\":["
          "\"Numeric immediates, unclassified bytes and synthesized aliases are not certified by this candidate.\","
          "\"Normal-input execution, initialization, DMA lifetime and output qualification remain required.\","
          "\"Fixed game RAM outside explicit leases is not certified as OS-owned.\"]")) goto failed;
  }
  if(json_builder_append(&b,"}")) goto failed;
  *out_text=json_builder_build(&b);json_builder_destroy(&b);free(view);free(ranges);platform_file_free_text(layouts);
  return *out_text ? 0 : -1;
failed:
  json_builder_destroy(&b);free(view);free(ranges);platform_file_free_text(layouts);return -1;
}
