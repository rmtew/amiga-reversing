#ifndef M68K_MEMORY_LAYOUT_H
#define M68K_MEMORY_LAYOUT_H
#include "m68k_ir.h"
/* Shared finite geometry. Callers own memory-class, lease, alias and proof
 * policy; these routines neither allocate nor infer a domain. Bounds are
 * half-open and arithmetic is widened before validation. */
int m68k_memory_layout_extent_fits(uint32_t address,uint32_t size,uint32_t alignment,
    uint32_t domain_start,uint64_t domain_end);
int m68k_memory_layout_overlaps(uint32_t address,uint32_t width,uint32_t start,uint32_t size);
int m68k_memory_layout_translate_reference(uint32_t original,uint32_t placed,uint32_t size,
    uint32_t address,uint32_t width,uint32_t *result);
typedef struct M68kLayoutPoint {
  uint64_t address, prefix_max_moved_end;
  uint32_t containing_regions;
} M68kLayoutPoint;
typedef struct M68kResolvedMemoryLayout {
  uint32_t addresses[M68K_ANALYSIS_MEMORY_REGION_LIMIT];
  int16_t parents[M68K_ANALYSIS_MEMORY_REGION_LIMIT];
  uint16_t region_count;
  uint32_t ancestor_bits[M68K_ANALYSIS_MEMORY_REGION_LIMIT];
  M68kLayoutPoint points[2*M68K_ANALYSIS_MEMORY_REGION_LIMIT];
  size_t point_count;
  int failed_region;
  const char *reason;
} M68kResolvedMemoryLayout;
/* Placement validation only: no reference closure, initialization, encoding or
 * execution claim. These are canonical region facts, never inferred extents. */
int m68k_memory_layout_resolve(const M68kAnalysisPolicy *,const M68kMemoryLayoutIR *,M68kResolvedMemoryLayout *);
/* Resolve only an already typed runtime reference; callers must never pass
 * arbitrary scalar values here. Returns 1 mapped, 0 unaffected, -1 ambiguous
 * or partially intersecting a moved region (never a stale numeric fallback). */
int m68k_memory_layout_reference(const M68kAnalysisPolicy *,const M68kResolvedMemoryLayout *,
    uint32_t address,uint32_t width,char *expression,size_t capacity,uint32_t *placed_address);
/* Same answer, with comparison/candidate counts for deterministic scaling tests.
 * Build O(R log R), query O(log R + K), storage O(R), R <= native region limit. */
int m68k_memory_layout_reference_profiled(const M68kAnalysisPolicy *,const M68kResolvedMemoryLayout *,
    uint32_t address,uint32_t width,char *expression,size_t capacity,uint32_t *placed_address,size_t *steps);
/* Shared source-view and typed-extent admission for clean rendering and reuse. */
int m68k_memory_layout_validate_source(const M68kAnalysisPolicy *,M68kResolvedMemoryLayout *,
    const M68kSourceAnalysisIR *);
#endif
