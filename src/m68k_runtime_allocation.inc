typedef struct MRAllocationRange {uint32_t start,size;} MRAllocationRange;
static int mr_allocation_range_order(const void *aa,const void *bb) {
  const MRAllocationRange *a=aa,*b=bb;
  return a->start<b->start ? -1 : a->start>b->start ? 1 : 0;
}
/* Bounded runtime-only LONG-data allocation. This is not the legacy relocation
 * proof adapter and never promotes its numeric immediate candidates to fixups.
 * Returned bases are admitted by the same canonical fixed-layout geometry. */
int platform_file_facts_v2_listing_artifact_runtime_allocation_json_alloc(
    PlatformFileListingArtifact *a,const char *region_id,const char *layout_id,
    int has_actual,uint32_t actual,char **out_text) {
  JsonBuilder b={0};PlatformFileListingArtifact *view=NULL;char *layouts=NULL;
  const char *reason=NULL;int ri=-1;size_t li=0,fixups=0,numeric=0;
  MRAllocationRange *ranges=NULL;size_t range_count=0,range_capacity=0;
  M68kResolvedMemoryLayout initial,resolved;
  const char *owner_symbols[32];
  const M68kMemoryRegionIR *r=NULL;const M68kBootstrapContractIR *boot=NULL;
  if(!a || !region_id || !layout_id || !out_text) return -1;
  *out_text=NULL;
  for(size_t i=0;i<a->policy.memory_region_count;i++)
    if(!strcmp(region_id,a->policy.memory_regions[i].region_id)) ri=(int)i;
  for(;li<a->policy.memory_layout_count;li++)
    if(!strcmp(layout_id,a->policy.memory_layouts[li].layout_id)) break;
  if(ri<0 || li==a->policy.memory_layout_count) {reason="unknown_region_or_layout";goto result;}
  r=&a->policy.memory_regions[ri];
  if(r->source_mapped || r->parent_region_id[0] || r->has_loader_seed || !r->dma_access ||
      r->region_kind>2 || r->alignment>8 || r->size>0x10000) {
    reason="unsupported_runtime_allocation_owner";goto result;
  }
  for(size_t i=0;i<a->policy.memory_region_count;i++)
    if(!strcmp(a->policy.memory_regions[i].parent_region_id,r->region_id)) {
      reason="allocation_subregions_unsupported";goto result;
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
    for(size_t j=0;j<ins->instruction.operand_count;j++) {
      uint32_t address=0;int kind=mr_operand_address(a,ins,j,&address);
      if(address<r->runtime_address || address-r->runtime_address>=r->size) continue;
      if(kind==2) numeric++;
      else if(kind) {reason="non_data_pointer_reference_unsupported";goto result;}
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
    owner_symbols[fixups++]=e->target_symbol;
  }
  if(!fixups) {reason="no_explicit_runtime_LONG_data_fixups";goto result;}
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
    if(address==r->runtime_address && q->extent_bytes==r->size)
      for(size_t fi=0;fi<fixups;fi++) if(!strcmp(owner_symbols[fi],q->name)) {owned=1;break;}
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
  if(platform_file_facts_v2_listing_artifact_memory_layouts_json_alloc(view,&layouts)) goto failed;
result:
  if(json_builder_create(&b) || json_builder_append(&b,"{\"status\":") ||
      json_builder_append_json_string(&b,reason ? "refused" : has_actual ? "actual_placement_valid" : "bounded_allocation_candidate") ||
      json_builder_append(&b,",\"reason\":") ||
      (reason ? json_builder_append_json_string(&b,reason) : json_builder_append(&b,"null"))) goto failed;
  if(!reason) {
    if(json_builder_append(&b,",\"region_id\":") || json_builder_append_json_string(&b,region_id) ||
        json_builder_appendf(&b,",\"size\":%u,\"alignment\":%u,\"memory_requirement\":\"chip\","
          "\"original_address\":%u,\"staged_address\":%u,\"numeric_immediate_candidates_not_fixups\":%zu,\"fixups\":[",
          r->size,r->alignment,r->runtime_address,initial.addresses[ri],numeric)) goto failed;
    size_t fi=0;
    for(size_t i=0;i<a->source_plan.expression_count;i++) {
      const M68kRenderPlannedExpression *e=&a->source_plan.expressions[i];uint32_t address=0;
      if(!mr_pointer_runtime_address(a,e,&address) || address<r->runtime_address || address-r->runtime_address>=r->size) continue;
      if((fi++ && json_builder_append(&b,",")) || json_builder_appendf(&b,
          "{\"source_section_index\":%u,\"source_offset\":%u,\"width\":4,\"encoding\":\"absolute_long_data\","
          "\"address_domain\":\"runtime_only\",\"region_offset\":%u,\"staged_value\":%u}",
          e->source_section_index,e->source_offset,address-r->runtime_address,
          initial.addresses[ri]+address-r->runtime_address)) goto failed;
    }
    if(json_builder_append(&b,"],\"protected_ranges\":[")) goto failed;
    for(size_t pi=0;pi<range_count;pi++)
      if((pi && json_builder_append(&b,",")) || json_builder_appendf(&b,
          "{\"address\":%u,\"size\":%u}",ranges[pi].start,ranges[pi].size)) goto failed;
    if(json_builder_append(&b,"],\"layout\":") || json_builder_append(&b,layouts) ||
        json_builder_append(&b,",\"scope\":\"reviewed_typed_LONG_data_only_not_all_path_alias_proof\","
          "\"lifetime\":\"retain_until_DMA_quiescent_exit\",\"unresolved\":["
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
