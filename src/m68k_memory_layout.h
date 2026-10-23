#ifndef M68K_MEMORY_LAYOUT_H
#define M68K_MEMORY_LAYOUT_H
#include "m68k_ir.h"
typedef struct M68kResolvedMemoryLayout {
  uint32_t addresses[M68K_ANALYSIS_MEMORY_REGION_LIMIT];
  int16_t parents[M68K_ANALYSIS_MEMORY_REGION_LIMIT];
  uint16_t region_count;
  int failed_region;
  const char *reason;
} M68kResolvedMemoryLayout;
/* Placement validation only: no reference closure, initialization, encoding or
 * execution claim. These are canonical region facts, never inferred extents. */
int m68k_memory_layout_resolve(const M68kAnalysisPolicy *,const M68kMemoryLayoutIR *,M68kResolvedMemoryLayout *);
#endif
