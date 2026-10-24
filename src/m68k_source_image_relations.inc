/* Numeric record indices deliberately omit render-expression endpoints.
 * Validate their canonical source relations too, in one linear pass, instead
 * of treating presentation's omission as proof that no address edge exists. */
static const char *mr_image_relative_data_guard(const M68kSourceAnalysisIR *analysis,const M68kObject *object,const M68kRenderPlan *plan,
    const M68kMemoryRegionIR *r,unsigned char *checked,const M68kRenderPlannedExpression **refused) {
  for(size_t si=0;si<analysis->section_count;si++) {
    const M68kSectionAnalysisIR *section=&analysis->sections[si];
    for(size_t i=0;i<section->data_reference_count;i++) {
      const M68kDataReferenceIR *ref=&section->data_references[i];
      if(ref->reference_kind!=M68K_DATA_REFERENCE_KIND_BASE_DISPLACEMENT &&
          ref->reference_kind!=M68K_DATA_REFERENCE_KIND_BASE_DISPLACEMENT_RANGE) continue;
      int storage=!section->section_index && ref->source_offset<r->size;
      int base=ref->has_base && !ref->base_section_index && ref->base_offset<r->size;
      int target=!ref->target_section_index && ref->target_offset<r->size;
      if(!storage && !base && !target) continue;
      *refused=m68k_render_plan_find_expression(plan,section->section_index,ref->source_offset,
          UINT32_MAX,M68K_RENDER_PLANNED_EXPRESSION_RELATIVE);
      if(!storage || !base || !target) return "cross_owner_relative_image_reference";
      uint32_t scale=ref->reference_kind==M68K_DATA_REFERENCE_KIND_BASE_DISPLACEMENT ? 1:ref->value_scale;
      int64_t value=ref->raw_value_signed ? (int16_t)ref->raw_value:(int64_t)ref->raw_value;
      if(ref->raw_value_width!=2 || r->size<2 || ref->source_offset>r->size-2 || ref->raw_value>UINT16_MAX || !scale ||
          m68k_read_u16be(object->sections[0].data+ref->source_offset)!=ref->raw_value ||
          (int64_t)ref->base_offset+value*scale!=ref->target_offset)
        return "invalid_relative_image_source_relation";
      checked[ref->source_offset]=1;
    }
  }
  *refused=NULL;return NULL;
}
