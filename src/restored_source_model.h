/* Shared restored-source model for executable source display. */
#ifndef RESTORED_SOURCE_MODEL_H
#define RESTORED_SOURCE_MODEL_H

#include "platform_executable_summary.h"

#include <stddef.h>
#include <stdint.h>

typedef enum RestoredSourceOwnershipRole {
  RESTORED_SOURCE_OWNERSHIP_CODE = 1,
  RESTORED_SOURCE_OWNERSHIP_DATA = 2,
  RESTORED_SOURCE_OWNERSHIP_BSS = 3,
  RESTORED_SOURCE_OWNERSHIP_METADATA = 4,
  RESTORED_SOURCE_OWNERSHIP_RELOCATION_FIXUP = 5,
  RESTORED_SOURCE_OWNERSHIP_PADDING = 6,
  RESTORED_SOURCE_OWNERSHIP_PLACEHOLDER = 7,
  RESTORED_SOURCE_OWNERSHIP_UNKNOWN = 8,
  RESTORED_SOURCE_OWNERSHIP_CANDIDATE_CODE = 9
} RestoredSourceOwnershipRole;

typedef struct RestoredSourceOwnershipRange {
  RestoredSourceOwnershipRole role;
  const char *byte_space;
  const char *platform;
  const char *source_kind;
  uint32_t section_index;
  uint32_t start;
  uint32_t size;
  uint32_t stored_offset;
  uint8_t has_stored_offset;
  uint32_t stored_size;
  PlatformExecutableFactRef fact;
  const char *provenance;
  const char *reason;
} RestoredSourceOwnershipRange;

#define RESTORED_SOURCE_MODEL_MAX_OWNERSHIP_RANGES PLATFORM_EXECUTABLE_SUMMARY_MAX_RANGES

typedef struct RestoredSourceModel {
  const char *model;
  const char *platform;
  const char *source_kind;
  uint8_t round_trip_required;
  RestoredSourceOwnershipRange ownership_ranges[RESTORED_SOURCE_MODEL_MAX_OWNERSHIP_RANGES];
  size_t ownership_range_count;
} RestoredSourceModel;

typedef struct RestoredSourceCoverageVerifier {
  uint8_t ok;
  uint32_t gap_count;
  uint32_t overlap_count;
  uint32_t invalid_instruction_ownership_count;
  uint32_t explicit_unknown_missing_detail_count;
} RestoredSourceCoverageVerifier;

#endif
