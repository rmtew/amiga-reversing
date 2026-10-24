/* Explicit allocator returns over one canonical layout. No placement search,
 * policy mutation, intermediate mixed-layout admission or numeric fixups. */
int platform_file_facts_v2_listing_artifact_runtime_allocation_batch_json_alloc(
    PlatformFileListingArtifact *a,const char *layout_id,const char *bindings_json,char **out_text) {
  JsonBuilder b={0};PlatformFileListingArtifact *view=NULL;
  M68kMemoryLayoutIR bindings={0},final={0};M68kResolvedMemoryLayout resolved;
  const char *reason=NULL;char *members[M68K_ANALYSIS_MEMORY_REGION_LIMIT]={0},*layouts=NULL;
  int owners[M68K_ANALYSIS_MEMORY_REGION_LIMIT];size_t count=0,li=0,site_count=0;
  size_t site_capacity=0;
  MRAllocationFixup *sites=NULL;char status[64]={0};
  MRAllocationRange fixed[M68K_ANALYSIS_MEMORY_REGION_LIMIT+2];size_t fixed_count=0;
  if(!a || !layout_id || !bindings_json || !out_text) return -1;
  *out_text=NULL;
  for(;li<a->policy.memory_layout_count;li++) if(!strcmp(layout_id,a->policy.memory_layouts[li].layout_id)) break;
  if(li==a->policy.memory_layout_count) {reason="unknown_layout";goto result;}
  view=malloc(sizeof(*view));if(!view) goto failed;
  *view=*a;view->policy.memory_layout_count=0;
  const char *end=bindings_json+strlen(bindings_json),*object_end=NULL;
  const char *start=json_skip_ws_local(bindings_json,end);
  const char *object=json_next_object_local(start,end,&object_end);
  static const char *const keys[]={"schema_version","layout_id","chip_bytes","placements"};
  if(!object || object!=start || json_skip_ws_local(object_end,end)!=end ||
      !json_object_has_only_keys_local(object,object_end,keys,4) ||
      !append_metadata_memory_layout_local(object,object_end,&view->policy)) {
    reason="invalid_actual_layout_bindings";goto result;
  }
  bindings=view->policy.memory_layouts[0];final=a->policy.memory_layouts[li];
  if(strcmp(bindings.layout_id,layout_id) || bindings.chip_bytes!=final.chip_bytes || !bindings.placement_count) {
    reason="actual_layout_profile_or_owner_set_refused";goto result;
  }
  /* Canonical region order makes caller ordering irrelevant to the receipt. */
  for(size_t ri=0;ri<a->policy.memory_region_count;ri++) {
    for(size_t bi=0;bi<bindings.placement_count;bi++) {
      M68kMemoryPlacementIR *p=&bindings.placements[bi];
      if(strcmp(p->region_id,a->policy.memory_regions[ri].region_id)) continue;
      const M68kMemoryRegionIR *r=&a->policy.memory_regions[ri];
      const M68kBootstrapContractIR *owner_boot=NULL;
      for(size_t b=0;b<a->policy.bootstrap_contract_count;b++)
        if(!strcmp(final.bootstrap_contract_id,a->policy.bootstrap_contracts[b].contract_id)) owner_boot=&a->policy.bootstrap_contracts[b];
      if((!mr_allocation_source_image(a,r,owner_boot) &&
          (r->source_mapped || r->parent_region_id[0] || r->has_loader_seed || r->region_kind>2 ||
           r->alignment>8 || r->size>0x10000)) || !p->runtime_address) {
        reason="unsupported_or_NULL_actual_allocation_owner";goto result;
      }
      size_t pi=0;for(;pi<final.placement_count;pi++) if(!strcmp(final.placements[pi].region_id,p->region_id)) break;
      if(pi==final.placement_count) {
        if(pi>=M68K_ANALYSIS_MEMORY_REGION_LIMIT) {reason="placement_capacity_exceeded";goto result;}
        final.placement_count++;
      }
      final.placements[pi]=*p;owners[count++]=(int)ri;
    }
  }
  if(count!=bindings.placement_count) {reason="unknown_actual_allocation_owner";goto result;}
  if(m68k_memory_layout_resolve(&a->policy,&final,&resolved)) {reason=resolved.reason;goto result;}
  /* Exec leases are eight-byte backing, independent of semantic field extents.
   * Keep children inside their parent's claim; do not round each child. */
  for(size_t i=0;i<count;i++) {
    size_t ri=(size_t)owners[i];uint32_t address=resolved.addresses[ri];
    uint32_t size=(a->policy.memory_regions[ri].size+7U)&~7U;
    if(address%8) {reason="actual_Exec_lease_alignment_refused";goto result;}
    for(size_t j=0;j<a->policy.memory_region_count;j++) {
      const M68kMemoryRegionIR *other=&a->policy.memory_regions[j];
      if(j==ri || other->parent_region_id[0]) continue;
      uint32_t start=resolved.addresses[j]&~7U;
      uint32_t end=(resolved.addresses[j]+other->size+7U)&~7U;
      if(m68k_memory_layout_overlaps(address,size,start,end-start)) {
        reason="actual_lease_overlaps_other_root_backing";goto result;
      }
    }
  }
  site_capacity=mr_allocation_site_capacity(a);
  if(!site_capacity) goto failed;
  sites=calloc(site_capacity,sizeof(*sites));if(!sites) goto failed;
  for(size_t i=0;i<count;i++) {
    size_t admitted=0;int ri=owners[i];
    if(mr_runtime_allocation_context_json_alloc(a,a->policy.memory_regions[ri].region_id,layout_id,
        1,resolved.addresses[ri],&resolved,&final,sites+site_count,site_capacity-site_count,&admitted,&members[i])) goto failed;
    if(!json_optional_string_field_local(members[i],members[i]+strlen(members[i]),"status",status,sizeof(status)) ||
        strcmp(status,"actual_placement_valid")) {reason="member_actual_placement_refused";goto result;}
    site_count+=admitted;
  }
  qsort(sites,site_count,sizeof(*sites),mr_allocation_fixup_order);
  for(size_t i=1;i<site_count;i++) if(sites[i].source_offset<sites[i-1].source_offset+sites[i-1].width) {
    reason="cross_owner_fixup_fields_overlap";goto result;
  }
  /* No owner may patch any part of another admitted frame transformation.
   * These exact eight-byte sites were checked by the existing member planner. */
  for(size_t i=0;i<count;i++) {
    const M68kMemoryRegionIR *r=&a->policy.memory_regions[owners[i]];
    for(size_t gi=0;gi<r->address_frame_site_count;gi++) for(size_t fi=0;fi<site_count;fi++)
      if(m68k_memory_layout_overlaps(sites[fi].source_offset,sites[fi].width,
          r->address_frame_sites[gi].source_offset,8)) {reason="batch_fixup_overlaps_frame_contract";goto result;}
  }
  const M68kBootstrapContractIR *boot=NULL;
  for(size_t i=0;i<a->policy.bootstrap_contract_count;i++)
    if(!strcmp(final.bootstrap_contract_id,a->policy.bootstrap_contracts[i].contract_id)) boot=&a->policy.bootstrap_contracts[i];
  if(boot && boot->has_exit_dispatch) {
    size_t image=0;for(;image<a->policy.memory_region_count;image++) if(!strcmp(boot->image_region_id,a->policy.memory_regions[image].region_id)) break;
    M68kBootstrapExitImport import;
    if(image==a->policy.memory_region_count || !m68k_render_plan_exit_dispatch_import(&a->source_plan,boot,
        a->policy.memory_regions[image].runtime_address,resolved.addresses[image],&import)) {reason="exit_dispatch_import_not_admitted";goto result;}
    for(size_t fi=0;fi<site_count;fi++) if(m68k_memory_layout_overlaps(sites[fi].source_offset,sites[fi].width,import.field_source_offset,import.width)) {
      reason="allocation_fixup_overlaps_exit_dispatch_import";goto result;
    }
  }
  /* Fixed acquisition intent comes from the same roots and retained input,
   * not a second host-side placement model. It is not an AllocAbs success. */
  if(boot) {
    fixed[fixed_count++]=(MRAllocationRange){boot->load_address,boot->file_size};
    fixed[fixed_count++]=(MRAllocationRange){final.bootstrap_source_helper ?
      boot->load_address+boot->helper_source_start : boot->helper_runtime_address,
      boot->helper_source_end-boot->helper_source_start};
  }
  for(size_t ri=0;ri<a->policy.memory_region_count;ri++) {
    const M68kMemoryRegionIR *r=&a->policy.memory_regions[ri];int dynamic=0;
    if(r->parent_region_id[0]) continue;
    for(size_t i=0;i<count;i++) if((size_t)owners[i]==ri) dynamic=1;
    if(!dynamic) fixed[fixed_count++]=(MRAllocationRange){resolved.addresses[ri],r->size};
  }
  for(size_t i=0;i<fixed_count;i++) {
    uint32_t end=(fixed[i].start+fixed[i].size+7U)&~7U;
    fixed[i].start&=~7U;fixed[i].size=end-fixed[i].start;
  }
  qsort(fixed,fixed_count,sizeof(*fixed),mr_allocation_range_order);
  size_t merged=0;
  for(size_t i=0;i<fixed_count;i++) {
    if(merged && fixed[i].start<=fixed[merged-1].start+fixed[merged-1].size) {
      uint32_t end=fixed[i].start+fixed[i].size;
      if(end>fixed[merged-1].start+fixed[merged-1].size) fixed[merged-1].size=end-fixed[merged-1].start;
    } else fixed[merged++]=fixed[i];
  }
  fixed_count=merged;
  *view=*a;view->policy.memory_layout_count=1;view->policy.memory_layouts[0]=final;
  if(platform_file_facts_v2_listing_artifact_memory_layouts_json_alloc(view,&layouts)) goto failed;
result:
  if(json_builder_create(&b) || json_builder_append(&b,"{\"status\":") ||
      json_builder_append_json_string(&b,reason ? "refused" : "actual_placements_valid") ||
      json_builder_append(&b,",\"reason\":") ||
      (reason ? json_builder_append_json_string(&b,reason) : json_builder_append(&b,"null")) ||
      json_builder_append(&b,",\"members\":[")) goto failed;
  for(size_t i=0;i<count;i++) if(members[i]) {
    if((i && json_builder_append(&b,",")) || json_builder_append(&b,members[i])) goto failed;
  }
  if(json_builder_append(&b,"]")) goto failed;
  if(!reason && (json_builder_appendf(&b,",\"owner_count\":%zu,\"fixup_count\":%zu,\"layout\":",count,site_count) ||
      json_builder_append(&b,layouts) || json_builder_append(&b,",\"scope\":\"atomic_explicit_runtime_owner_returns_not_all_path_alias_proof\""))) goto failed;
  if(!reason) {
    if(json_builder_append(&b,",\"leases\":[")) goto failed;
    for(size_t i=0;i<count;i++) {
      const M68kMemoryRegionIR *r=&a->policy.memory_regions[owners[i]];
      if((i && json_builder_append(&b,",")) || json_builder_append(&b,"{\"region_id\":") ||
          json_builder_append_json_string(&b,r->region_id) || json_builder_appendf(&b,
            ",\"address\":%u,\"size\":%u,\"semantic_size\":%u,\"alignment\":8}",
            resolved.addresses[owners[i]],(r->size+7U)&~7U,r->size)) goto failed;
    }
    if(json_builder_append(&b,"],\"fixed_leases_requiring_OS_acquisition\":[")) goto failed;
    for(size_t i=0;i<fixed_count;i++) if((i && json_builder_append(&b,",")) ||
        json_builder_appendf(&b,"{\"address\":%u,\"size\":%u}",fixed[i].start,fixed[i].size)) goto failed;
    if(json_builder_append(&b,"],\"uncovered_runtime_extents\":[")) goto failed;
    size_t uncovered=0;
    for(size_t qi=0;qi<a->policy.target_equate_count;qi++) {
      const M68kAnalysisTargetEquate *q=&a->policy.target_equates[qi];uint32_t address=(uint32_t)q->value;char expression[128];int covered=0;
      if(!q->address_domain || !q->extent_bytes) continue;
      int rc=m68k_memory_layout_reference(&a->policy,&resolved,address,q->extent_bytes,expression,sizeof(expression),&address);
      if(rc<0) goto failed;
      for(size_t i=0;i<fixed_count;i++) if(address>=fixed[i].start && (uint64_t)address+q->extent_bytes<=(uint64_t)fixed[i].start+fixed[i].size) covered=1;
      for(size_t i=0;i<count;i++) {
        size_t ri=(size_t)owners[i];uint32_t base=resolved.addresses[ri],size=(a->policy.memory_regions[ri].size+7U)&~7U;
        if(address>=base && (uint64_t)address+q->extent_bytes<=(uint64_t)base+size) covered=1;
      }
      if(!covered) {
        if((uncovered++ && json_builder_append(&b,",")) || json_builder_append(&b,"{\"symbol\":") ||
            json_builder_append_json_string(&b,q->name) || json_builder_appendf(&b,",\"address\":%u,\"size\":%u}",address,q->extent_bytes)) goto failed;
      }
    }
    if(json_builder_append(&b,"]")) goto failed;
  }
  if(json_builder_append(&b,"}")) goto failed;
  *out_text=json_builder_build(&b);json_builder_destroy(&b);
  for(size_t i=0;i<count;i++) platform_file_free_text(members[i]);
  free(layouts);free(view);free(sites);return *out_text ? 0 : -1;
failed:
  json_builder_destroy(&b);for(size_t i=0;i<count;i++) platform_file_free_text(members[i]);
  free(layouts);free(view);free(sites);return -1;
}
