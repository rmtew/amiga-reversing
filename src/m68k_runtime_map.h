#ifndef M68K_RUNTIME_MAP_H
#define M68K_RUNTIME_MAP_H
#include <stddef.h>
#include <stdint.h>

/* An index of existing materialized views, not another authority for mappings.
 * Overlapping views agree only when section and affine source identity agree. */
typedef struct M68kRuntimeMapSpan {
  uint32_t address, size, section, source_offset;
} M68kRuntimeMapSpan;
typedef struct M68kRuntimeMapSegment {
  uint64_t start, end;
  int64_t source_delta;
  uint32_t section;
  int status;
} M68kRuntimeMapSegment;
typedef struct M68kRuntimeMap {
  M68kRuntimeMapSegment *segments;
  size_t count;
} M68kRuntimeMap;

/* Map must be zero-initialized or previously built. Build O(N log N), storage
 * O(N); failure leaves the old index intact. Destroy is repeatable. */
int m68k_runtime_map_build(M68kRuntimeMap *, const M68kRuntimeMapSpan *, size_t);
void m68k_runtime_map_destroy(M68kRuntimeMap *);
/* 1 unique, 0 missing, -1 conflicting. Full spans must have one affine identity.
 * Optional steps counts comparisons/visited segments, independent of byte size. */
int m68k_runtime_map_resolve(const M68kRuntimeMap *, uint32_t address, uint32_t size,
    uint32_t *section, uint32_t *source_offset, size_t *steps);
#endif
