/* Additional source-backed encodings already owned by canonical interpretation
 * and Copper semantics. No byte scan or expression-string parser is used. */
static int mr_image_data_extent(const PlatformFileListingArtifact *a,uint32_t offset,uint32_t width) {
  const M68kRenderPlanRow *row=m68k_render_plan_find_row_for_source_offset(&a->source_plan,0,offset);
  return row && row->kind==M68K_RENDER_PLAN_ROW_DATA && row->has_source_range &&
    offset>=row->source_offset && offset-row->source_offset<=row->source_size &&
    width<=row->source_size-(offset-row->source_offset);
}
static const char *mr_image_interpreted_fields(const PlatformFileListingArtifact *a,
    const M68kMemoryRegionIR *r,uint32_t staged,MRAllocationFixup *sites,size_t capacity,size_t *count,
    uint32_t *failure_offset) {
  for(size_t i=0;i<a->policy.manual_runtime_address_ref_count;i++) {
    const M68kAnalysisManualRuntimeAddressRef *ref=&a->policy.manual_runtime_address_refs[i];
    if(strcmp(ref->owner_kind,"data_block_interpreted_ref") || !ref->has_target ||
        ref->target_section_index || ref->target_offset>=r->size) continue;
#define INTERPRETED_REFUSE(reason) do {*failure_offset=ref->offset;return reason;} while(0)
    if(!ref->has_section_index || ref->section_index || !ref->has_runtime_address || ref->size!=4 ||
        ref->offset%2 || ref->offset>r->size || r->size-ref->offset<4 ||
        m68k_read_u32be(a->object.sections[0].data+ref->offset)!=ref->runtime_address)
      INTERPRETED_REFUSE("unsupported_or_stale_interpreted_image_field");
    int covered=0;
    for(size_t f=0;f<*count;f++) if(sites[f].source_offset==ref->offset) {
      /* An independently admitted winning native encoding remains authoritative.
       * Do not reinterpret an unused legacy local-offset target tuple as a new
       * source identity. Require the original encoded runtime value to agree. */
      if(sites[f].width!=4 || r->runtime_address+sites[f].region_offset!=ref->runtime_address)
        INTERPRETED_REFUSE("conflicting_interpreted_image_field");
      covered=1;break;
    }
    if(covered) continue;
    uint32_t address=0;
    if(mr_source_address(a,ref->target_section_index,ref->target_offset,&address)!=1 ||
        address!=ref->runtime_address || address!=r->runtime_address+ref->target_offset)
      INTERPRETED_REFUSE("interpreted_image_pointer_mapping_mismatch");
    if(!mr_image_data_extent(a,ref->offset,4)) INTERPRETED_REFUSE("interpreted_image_field_not_rendered_data");
    if(*count>=capacity) INTERPRETED_REFUSE("fixup_capacity_exceeded");
    sites[(*count)++]=(MRAllocationFixup){.source_offset=ref->offset,.region_offset=ref->target_offset,
      .staged_value=staged+ref->target_offset,.width=4,.has_source_target=1,.target_offset=ref->target_offset,
      .pointer_domain_plus_one=3,.interpreted_owner=ref->owner_id};
#undef INTERPRETED_REFUSE
  }
  return NULL;
}
static const char *mr_image_copper_fields(const PlatformFileListingArtifact *a,
    const M68kMemoryRegionIR *r,uint32_t staged,MRAllocationFixup *sites,size_t capacity,size_t *count,
    const M68kRenderPlannedExpression **refused) {
  for(size_t i=0;i<a->source_plan.expression_count;i++) {
    const M68kRenderPlannedExpression *e=&a->source_plan.expressions[i];
    if(e->kind!=M68K_RENDER_PLANNED_EXPRESSION_EQUATE || !e->pointer_value_part ||
        e->logical_address<r->runtime_address || e->logical_address-r->runtime_address>=r->size) continue;
    *refused=e;
    if(e->source_section_index || e->source_offset%2 || e->pointer_width!=2 ||
        e->pointer_address_domain!=M68K_ANALYSIS_POINTER_DOMAIN_RUNTIME_ONLY ||
        e->outcome!=M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC ||
        (e->pointer_value_part!=M68K_RUNTIME_ADDRESS_PART_HIGH16 && e->pointer_value_part!=M68K_RUNTIME_ADDRESS_PART_LOW16))
      return "unsupported_typed_Copper_address_word";
    if(e->pointer_value_part==M68K_RUNTIME_ADDRESS_PART_LOW16 && e->source_offset<4)
      return "unpaired_Copper_address_words";
    uint32_t high=e->pointer_value_part==M68K_RUNTIME_ADDRESS_PART_HIGH16 ? e->source_offset:e->source_offset-4;
    const M68kRenderPlannedExpression *hi=m68k_render_plan_find_expression(&a->source_plan,0,high,UINT32_MAX,M68K_RENDER_PLANNED_EXPRESSION_EQUATE);
    const M68kRenderPlannedExpression *lo=m68k_render_plan_find_expression(&a->source_plan,0,high+4,UINT32_MAX,M68K_RENDER_PLANNED_EXPRESSION_EQUATE);
    if(!hi || !lo || hi->pointer_value_part!=M68K_RUNTIME_ADDRESS_PART_HIGH16 ||
        lo->pointer_value_part!=M68K_RUNTIME_ADDRESS_PART_LOW16 || hi->logical_address!=lo->logical_address ||
        hi->logical_address!=e->logical_address || high>r->size || r->size-high<8 ||
        !mr_image_data_extent(a,high+2,2) || !mr_image_data_extent(a,high+6,2) ||
        (((uint32_t)m68k_read_u16be(a->object.sections[0].data+high+2)<<16) |
            m68k_read_u16be(a->object.sections[0].data+high+6))!=e->logical_address)
      return "unpaired_or_stale_Copper_address_words";
    if(e->pointer_value_part==M68K_RUNTIME_ADDRESS_PART_LOW16) continue;
    if(*count>capacity || capacity-*count<2) return "fixup_capacity_exceeded";
    uint32_t offset=e->logical_address-r->runtime_address,value=staged+offset;
    for(uint8_t part=M68K_RUNTIME_ADDRESS_PART_HIGH16;part<=M68K_RUNTIME_ADDRESS_PART_LOW16;part++)
      sites[(*count)++]=(MRAllocationFixup){.source_offset=high+(part==M68K_RUNTIME_ADDRESS_PART_HIGH16 ? 2:6),
        .region_offset=offset,.staged_value=part==M68K_RUNTIME_ADDRESS_PART_HIGH16 ? value>>16:value&0xffffU,
        .width=2,.has_source_target=1,.target_offset=offset,.pointer_domain_plus_one=3,
        .value_part=part,.pair_source_offset=high};
  }
  *refused=NULL;return NULL;
}
