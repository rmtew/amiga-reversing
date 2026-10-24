#ifndef M68K_LAYOUT_PROJECTION_H
#define M68K_LAYOUT_PROJECTION_H
#include "m68k_memory_layout.h"
#include "m68k_render_plan.h"

/* Scoped view over one immutable semantic plan. Only rows/declarations below
 * are owned; all other arrays/text borrow the caller's live base plan. */
typedef struct M68kLayoutProjection {
  M68kRenderPlan plan;
  M68kResolvedMemoryLayout resolved;
  M68kRenderPlanRow *owned_rows;
  M68kRenderPlannedDeclaration *owned_declarations;
  char root_text[M68K_ANALYSIS_MEMORY_REGION_LIMIT][224];
  size_t rows_visited, declarations_visited, rewritten_roots, owned_bytes;
  const char *reason;
} M68kLayoutProjection;

/* 0 view ready; 1 requires a new semantic plan; -1 refused. Does not change
 * image/bootstrap placement or re-run discovery/rendering from target bytes. */
int m68k_layout_projection_build(M68kLayoutProjection *,const M68kRenderPlan *,
    const M68kAnalysisPolicy *,const M68kMemoryLayoutIR *baseline,
    const M68kMemoryLayoutIR *selected,const M68kSourceAnalysisIR *);
void m68k_layout_projection_destroy(M68kLayoutProjection *);
#endif
