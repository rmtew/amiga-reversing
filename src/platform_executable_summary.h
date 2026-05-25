/* Shared executable summary/range model for platform import pipeline. */
#ifndef PLATFORM_EXECUTABLE_SUMMARY_H
#define PLATFORM_EXECUTABLE_SUMMARY_H

#include <stddef.h>
#include <stdint.h>

typedef enum PlatformExecutableRangeRole {
  PLATFORM_EXECUTABLE_RANGE_ROLE_CODE = 1,
  PLATFORM_EXECUTABLE_RANGE_ROLE_DATA = 2,
  PLATFORM_EXECUTABLE_RANGE_ROLE_BSS = 3,
  PLATFORM_EXECUTABLE_RANGE_ROLE_METADATA = 4,
  PLATFORM_EXECUTABLE_RANGE_ROLE_CANDIDATE_CODE = 5
} PlatformExecutableRangeRole;

typedef enum PlatformExecutableLimitKind {
  PLATFORM_EXECUTABLE_LIMIT_RUNTIME_ENTRY = 1,
  PLATFORM_EXECUTABLE_LIMIT_RELOCATION_BREADTH = 2,
  PLATFORM_EXECUTABLE_LIMIT_UNSUPPORTED_PAYLOAD = 3
} PlatformExecutableLimitKind;

typedef struct PlatformExecutableFactRef {
  const char *fact_id;
  const char *fact_status;
  const char *parser_use;
} PlatformExecutableFactRef;

typedef struct PlatformExecutableRange {
  PlatformExecutableRangeRole role;
  uint32_t load_offset;
  uint32_t stored_offset;
  uint8_t has_stored_offset;
  uint32_t size;
  uint32_t stored_size;
  PlatformExecutableFactRef fact;
} PlatformExecutableRange;

typedef struct PlatformExecutableLimit {
  PlatformExecutableLimitKind kind;
  PlatformExecutableFactRef fact;
} PlatformExecutableLimit;

#define PLATFORM_EXECUTABLE_SUMMARY_MAX_RANGES 4096U
#define PLATFORM_EXECUTABLE_SUMMARY_MAX_LIMITS 16U

typedef struct PlatformExecutableSummary {
  const char *record_id;
  PlatformExecutableRange ranges[PLATFORM_EXECUTABLE_SUMMARY_MAX_RANGES];
  size_t range_count;
  PlatformExecutableLimit limits[PLATFORM_EXECUTABLE_SUMMARY_MAX_LIMITS];
  size_t limit_count;
} PlatformExecutableSummary;

#endif
