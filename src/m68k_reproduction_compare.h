#ifndef M68K_REPRODUCTION_COMPARE_H
#define M68K_REPRODUCTION_COMPARE_H

#include "m68k_assembler_policy.h"
#include "m68k_object.h"
#include "util_arena.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_REPRO_COMPARE_RANGE_CAPACITY 8U
#define M68K_REPRO_COMPARE_SOURCE_HINT_CAPACITY 8U
#define M68K_REPRO_COMPARE_LAYOUT_CAPACITY 64U
#define M68K_REPRO_COMPARE_DIAGNOSTIC_CAPACITY 8U

typedef enum M68kReproductionCompareStatusId {
  M68K_REPRO_COMPARE_STATUS_NOT_COMPARED = 0,
  M68K_REPRO_COMPARE_STATUS_FULL_FILE_EXACT = 1,
  M68K_REPRO_COMPARE_STATUS_CONTENT_EXACT = 2,
  M68K_REPRO_COMPARE_STATUS_MISMATCH = 3,
  M68K_REPRO_COMPARE_STATUS_INVALID_ARGUMENT = 4
} M68kReproductionCompareStatusId;

typedef enum M68kReproductionCompareExactnessId {
  M68K_REPRO_COMPARE_EXACTNESS_NONE = 0,
  M68K_REPRO_COMPARE_EXACTNESS_FULL_FILE = 1,
  M68K_REPRO_COMPARE_EXACTNESS_CONTENT = 2,
  M68K_REPRO_COMPARE_EXACTNESS_MISMATCH = 3
} M68kReproductionCompareExactnessId;

typedef enum M68kReproductionCompareDiagnosticId {
  M68K_REPRO_COMPARE_DIAG_NONE = 0,
  M68K_REPRO_COMPARE_DIAG_INVALID_ARGUMENT = 1
} M68kReproductionCompareDiagnosticId;

enum {
  M68K_REPRO_COMPARE_ISSUE_CONTENT_DIFF = 1U << 0,
  M68K_REPRO_COMPARE_ISSUE_RELOCATION_DIFF = 1U << 1,
  M68K_REPRO_COMPARE_ISSUE_CONTAINER_SHAPE_DIFF = 1U << 2,
  M68K_REPRO_COMPARE_ISSUE_SIZE_DIFF = 1U << 3,
  M68K_REPRO_COMPARE_ISSUE_RANGE_OVERFLOW = 1U << 4,
  M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_ORDER_DIFF = 1U << 5,
  M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_GROUP_DIFF = 1U << 6,
  M68K_REPRO_COMPARE_ISSUE_HUNK_RELOCATION_ENCODING_DIFF = 1U << 7,
  M68K_REPRO_COMPARE_ISSUE_POLICY_DIVERGENCE = 1U << 8,
  M68K_REPRO_COMPARE_ISSUE_UNSUPPORTED_CONTAINER_SHAPE = 1U << 9
};

typedef struct M68kReproductionCompareRange {
  uint32_t original_offset;
  uint32_t rebuilt_offset;
  uint32_t original_size;
  uint32_t rebuilt_size;
} M68kReproductionCompareRange;

typedef struct M68kReproductionCompareSourceHint {
  uint32_t issue_group_flags;
  uint32_t section_index;
  uint32_t offset;
} M68kReproductionCompareSourceHint;

typedef struct M68kReproductionCompareLayoutRange {
  uint32_t kind_id;
  uint32_t file_start;
  uint32_t file_end;
  uint32_t section_index;
  uint32_t section_offset_start;
  uint8_t has_section_index;
} M68kReproductionCompareLayoutRange;

typedef struct M68kReproductionCompareDiagnostic {
  uint32_t kind_id;
  uint32_t field_id;
  uint32_t original_value;
  uint32_t rebuilt_value;
} M68kReproductionCompareDiagnostic;

typedef struct M68kReproductionCompareResult {
  uint32_t status_id;
  uint32_t exactness_id;
  uint32_t diagnostic_id;
  uint32_t issue_group_flags;
  uint32_t first_diff_offset;
  uint8_t first_diff_original_byte;
  uint8_t first_diff_rebuilt_byte;
  uint8_t has_first_diff;
  uint8_t range_count;
  uint8_t range_overflow;
  uint8_t source_hint_count;
  uint8_t source_hint_overflow;
  uint8_t layout_count;
  uint8_t layout_overflow;
  uint8_t diagnostic_count;
  uint8_t diagnostic_overflow;
  M68kReproductionCompareRange ranges[M68K_REPRO_COMPARE_RANGE_CAPACITY];
  M68kReproductionCompareSourceHint source_hints[M68K_REPRO_COMPARE_SOURCE_HINT_CAPACITY];
  M68kReproductionCompareLayoutRange layout[M68K_REPRO_COMPARE_LAYOUT_CAPACITY];
  M68kReproductionCompareDiagnostic diagnostics[M68K_REPRO_COMPARE_DIAGNOSTIC_CAPACITY];
} M68kReproductionCompareResult;

typedef struct M68kReproductionCompareContext {
  const unsigned char *original_bytes;
  size_t original_size;
  const unsigned char *rebuilt_bytes;
  size_t rebuilt_size;
  M68kPlatformBackendKind backend_kind;
  const M68kAssemblerPolicy *assembler_policy;
  const M68kObject *original_object;
  const M68kObject *rebuilt_object;
  Arena *workflow_arena;
} M68kReproductionCompareContext;

void m68k_reproduction_compare_init_result(M68kReproductionCompareResult *result);
int m68k_reproduction_compare(const M68kReproductionCompareContext *context,
  M68kReproductionCompareResult *result);

#endif
