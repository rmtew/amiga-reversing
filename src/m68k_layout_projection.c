#include "m68k_layout_projection.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

void m68k_layout_projection_destroy(M68kLayoutProjection *p) {
  if(!p) return;
  free(p->owned_rows);free(p->owned_declarations);memset(p,0,sizeof(*p));
}
static int stop(M68kLayoutProjection *p,int result,const char *reason) {
  p->reason=reason;return result;
}
int m68k_layout_projection_build(M68kLayoutProjection *out,const M68kRenderPlan *base,
    const M68kAnalysisPolicy *policy,const M68kMemoryLayoutIR *baseline,
    const M68kMemoryLayoutIR *selected,const M68kSourceAnalysisIR *analysis) {
  M68kResolvedMemoryLayout before;
  uint8_t declarations[M68K_ANALYSIS_MEMORY_REGION_LIMIT]={0};
  uint8_t rows[M68K_ANALYSIS_MEMORY_REGION_LIMIT]={0};
  if(!out) return -1;
  memset(out,0,sizeof(*out));
  if(!base || !policy || !baseline || !selected || !analysis || !base->finalized)
    return stop(out,1,"frozen_selected_layout_required");
  if(m68k_memory_layout_resolve(policy,selected,&out->resolved) ||
      m68k_memory_layout_validate_source(policy,&out->resolved,analysis))
    return stop(out,-1,out->resolved.reason ? out->resolved.reason : "layout_resolution_failed");
  if(m68k_memory_layout_resolve(policy,baseline,&before))
    return stop(out,-1,"invalid_frozen_layout");
  if(!baseline->bootstrap_contract_id[0] || baseline->chip_bytes!=selected->chip_bytes ||
      strcmp(baseline->bootstrap_contract_id,selected->bootstrap_contract_id) ||
      baseline->bootstrap_forward_disjoint!=selected->bootstrap_forward_disjoint)
    return stop(out,1,"bootstrap_or_profile_change_requires_new_plan");
  for(size_t i=0;i<policy->memory_region_count;i++)
    if(policy->memory_regions[i].source_mapped && before.addresses[i]!=out->resolved.addresses[i])
      return stop(out,1,"mapped_storage_move_requires_new_plan");
  for(size_t s=0;s<analysis->section_count;s++) {
    const M68kSectionAnalysisIR *section=&analysis->sections[s];
    for(size_t v=0;v<section->runtime_view_count;v++) {
      const M68kRuntimeViewIR *view=&section->runtime_views[v];
      uint32_t a=0,b=0;char expression[128];
      if(!view->materialized) continue;
      int ra=m68k_memory_layout_reference(policy,&before,view->runtime_address,view->size,expression,sizeof(expression),&a);
      int rb=m68k_memory_layout_reference(policy,&out->resolved,view->runtime_address,view->size,expression,sizeof(expression),&b);
      if(ra!=rb || a!=b) return stop(out,1,"materialized_view_move_requires_new_plan");
    }
  }
  if(base->row_count>SIZE_MAX/sizeof(*out->owned_rows) ||
      base->declaration_count>SIZE_MAX/sizeof(*out->owned_declarations)) return stop(out,-1,"projection_size_overflow");
  out->owned_rows=malloc(base->row_count*sizeof(*out->owned_rows));
  out->owned_declarations=malloc(base->declaration_count*sizeof(*out->owned_declarations));
  if((base->row_count && !out->owned_rows) || (base->declaration_count && !out->owned_declarations))
    return stop(out,-1,"projection_allocation_failed");
  if(base->row_count) memcpy(out->owned_rows,base->rows,base->row_count*sizeof(*out->owned_rows));
  if(base->declaration_count) memcpy(out->owned_declarations,base->declarations,base->declaration_count*sizeof(*out->owned_declarations));
  out->plan=*base;out->plan.rows=out->owned_rows;out->plan.declarations=out->owned_declarations;
  out->owned_bytes=base->row_count*sizeof(*out->owned_rows)+base->declaration_count*sizeof(*out->owned_declarations)+sizeof(out->root_text);
  for(size_t d=0;d<base->declaration_count;d++) {
    M68kRenderPlannedDeclaration *decl=&out->owned_declarations[d];
    ++out->declarations_visited;
    if(!decl->layout_region_index_plus_one) continue;
    size_t i=decl->layout_region_index_plus_one-1U;
    if(i>=policy->memory_region_count || declarations[i]++ ||
        strcmp(decl->name,policy->memory_regions[i].name)) return stop(out,-1,"invalid_frozen_layout_declaration");
    if(out->resolved.parents[i]<0)
      snprintf(decl->expression,sizeof(decl->expression),"$%X",out->resolved.addresses[i]);
  }
  size_t byte=0;uint32_t line=0;
  for(size_t r=0;r<base->row_count;r++) {
    M68kRenderPlanRow *row=&out->owned_rows[r];++out->rows_visited;
    if(row->layout_region_index_plus_one) {
      size_t i=row->layout_region_index_plus_one-1U;
      if(i>=policy->memory_region_count || rows[i]++ || row->kind!=M68K_RENDER_PLAN_ROW_EQUATE)
        return stop(out,-1,"invalid_frozen_layout_row");
      if(out->resolved.parents[i]<0 && before.addresses[i]!=out->resolved.addresses[i]) {
        int n=snprintf(out->root_text[i],sizeof(out->root_text[i]),"%s\tEQU\t$%X\n",policy->memory_regions[i].name,out->resolved.addresses[i]);
        if(n<0 || (size_t)n>=sizeof(out->root_text[i])) return stop(out,-1,"layout_root_text_overflow");
        row->text=out->root_text[i];++out->rewritten_roots;
      }
    }
    row->start_byte=byte;row->start_line=line;
    row->byte_count=strlen(row->text);byte+=row->byte_count;line+=row->line_count;
  }
  for(size_t i=0;i<policy->memory_region_count;i++)
    if(declarations[i]!=1 || rows[i]!=1) return stop(out,1,"layout_declarations_require_new_plan");
  out->plan.total_bytes=byte;out->plan.total_lines=line;
  return 0;
}
