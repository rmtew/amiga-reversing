#ifndef PLATFORM_FILE_DECOMPRESSION_H
#define PLATFORM_FILE_DECOMPRESSION_H

#include "json_builder.h"

#include <stddef.h>
#include <stdint.h>

typedef enum PlatformDecompressionEventKind {
  PLATFORM_DECOMPRESSION_EVENT_KIND_UNKNOWN = 0,
  PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION = 1
} PlatformDecompressionEventKind;

typedef enum PlatformDerivedTargetSuggestionKind {
  PLATFORM_DERIVED_TARGET_SUGGESTION_UNKNOWN = 0,
  PLATFORM_DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD = 1
} PlatformDerivedTargetSuggestionKind;

typedef enum PlatformDecompressionSourceKind {
  PLATFORM_DECOMPRESSION_SOURCE_UNKNOWN = 0,
  PLATFORM_DECOMPRESSION_SOURCE_SECTION_RANGE = 1,
  PLATFORM_DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER = 2,
  PLATFORM_DECOMPRESSION_SOURCE_SELF_DECRUNCHER = 3,
  PLATFORM_DECOMPRESSION_SOURCE_TARGET_LOADER_FILE = 4
} PlatformDecompressionSourceKind;

typedef enum PlatformDecompressionStatus {
  PLATFORM_DECOMPRESSION_STATUS_UNKNOWN = 0,
  PLATFORM_DECOMPRESSION_STATUS_IDENTIFIED = 1,
  PLATFORM_DECOMPRESSION_STATUS_MATERIALIZABLE = 2,
  PLATFORM_DECOMPRESSION_STATUS_NEEDS_RUNTIME_METADATA = 3,
  PLATFORM_DECOMPRESSION_STATUS_NEEDS_SIMULATED_DECRUNCH = 4,
  PLATFORM_DECOMPRESSION_STATUS_SIMULATED_OUTPUT_OBSERVED = 5,
  PLATFORM_DECOMPRESSION_STATUS_NEEDS_REVIEW_BLOCKER = 6
} PlatformDecompressionStatus;

typedef enum PlatformDecompressionReason {
  PLATFORM_DECOMPRESSION_REASON_UNKNOWN = 0,
  PLATFORM_DECOMPRESSION_REASON_INVALID_RECORD = 1,
  PLATFORM_DECOMPRESSION_REASON_INITIAL_CONTROL_TARGET_VALIDATED_PROVIDER_WRAPPER = 2,
  PLATFORM_DECOMPRESSION_REASON_INITIAL_CONTROL_TARGET_VALIDATED_RUNTIME_COPY = 3,
  PLATFORM_DECOMPRESSION_REASON_MISSING_RUNTIME_COPY_EVIDENCE = 4,
  PLATFORM_DECOMPRESSION_REASON_RUNTIME_COPY_CONFLICTING = 5,
  PLATFORM_DECOMPRESSION_REASON_RUNTIME_COPY_SHORT = 6,
  PLATFORM_DECOMPRESSION_REASON_RUNTIME_COPY_OVERSIZE = 7,
  PLATFORM_DECOMPRESSION_REASON_MISSING_DECOMPRESSED_LOAD_ENTRY = 8,
  PLATFORM_DECOMPRESSION_REASON_NATIVE_TETRAGON_UNPACK_VALIDATED = 9,
  PLATFORM_DECOMPRESSION_REASON_RECOGNIZED_UNPACKER_SIGNATURE = 10,
  PLATFORM_DECOMPRESSION_REASON_UNIDENTIFIED_SELF_DECRUNCHER = 11,
  PLATFORM_DECOMPRESSION_REASON_SIMULATED_PC_RANGE_STOP = 12,
  PLATFORM_DECOMPRESSION_REASON_SIMULATED_PC_OUT_OF_RANGE = 13,
  PLATFORM_DECOMPRESSION_REASON_SIMULATED_INSTRUCTION_LIMIT = 14,
  PLATFORM_DECOMPRESSION_REASON_SIMULATED_DECODE_ERROR = 15,
  PLATFORM_DECOMPRESSION_REASON_SIMULATED_ERROR = 16,
  PLATFORM_DECOMPRESSION_REASON_SIMULATED_BAD_ARGUMENT = 17,
  PLATFORM_DECOMPRESSION_REASON_SIMULATED_NO_OUTPUT_RANGE = 18,
  PLATFORM_DECOMPRESSION_REASON_SIMULATED_UNKNOWN_STOP = 19,
  PLATFORM_DECOMPRESSION_REASON_INVALID_DECOMPRESSED_ENTRYPOINT = 20,
  PLATFORM_DECOMPRESSION_REASON_TARGET_LOADER_ACCEPTANCE_MATCHED = 21
} PlatformDecompressionReason;

typedef enum PlatformDecompressionPayloadRole {
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN = 0,
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_RUNTIME_PAYLOAD = 1,
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM = 2,
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_ASSET_DATA = 3,
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_DATA = 4
} PlatformDecompressionPayloadRole;

typedef enum PlatformDecompressionPayloadRoleConfidence {
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_UNKNOWN = 0,
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_TOOL_INFERRED = 1,
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NATIVE_UNPACK_ENTRY_VALIDATED = 2,
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_SIGNATURE_ONLY = 3,
  PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_OBSERVED_OUTPUT_ONLY = 4
} PlatformDecompressionPayloadRoleConfidence;

typedef enum PlatformDecompressionParentRemainsActive {
  PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_UNKNOWN = 0,
  PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE = 1,
  PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_TRUE = 2
} PlatformDecompressionParentRemainsActive;

typedef enum PlatformDecompressionCodecSupport {
  PLATFORM_DECOMPRESSION_CODEC_SUPPORT_UNKNOWN = 0,
  PLATFORM_DECOMPRESSION_CODEC_SUPPORT_EXTERNAL_PROVIDER = 1,
  PLATFORM_DECOMPRESSION_CODEC_SUPPORT_NATIVE_DECOMPRESSOR = 2,
  PLATFORM_DECOMPRESSION_CODEC_SUPPORT_SIMULATOR_REQUIRED = 3
} PlatformDecompressionCodecSupport;

typedef struct PlatformDecompressionIdentifyResult {
  int found;
  char provider_id[32];
  char provider_path[512];
  char provider_sha256[65];
  char codec_id[64];
  char codec_name[160];
  char confidence[32];
  char source_sha256[65];
  char decompressed_sha256[65];
  char decompressed_path[512];
  uint32_t source_offset;
  uint32_t source_section_index;
  uint32_t source_section_offset;
  uint32_t packed_size;
  uint32_t decompressed_size;
  uint32_t decompressed_load_address;
  uint32_t decompressed_entrypoint;
  uint32_t decompressed_initial_control_target;
  uint8_t has_source_section;
  uint8_t has_decompressed_load_entry;
  uint8_t has_decompressed_load_entry_from_wrapper;
  uint8_t parent_remains_active_known;
  uint8_t parent_remains_active;
  int decompressed;
} PlatformDecompressionIdentifyResult;

typedef struct PlatformDecompressionCandidate {
  uint32_t offset;
  uint32_t packed_size;
  uint32_t decompressed_size;
  char codec_hint[32];
} PlatformDecompressionCandidate;

void platform_decompression_identify_result_init(PlatformDecompressionIdentifyResult *result);
int platform_decompression_identify_path_range(const char *provider_id, const char *provider_path,
  const char *path, uint32_t offset, uint32_t size, PlatformDecompressionIdentifyResult *out_result,
  char *error, size_t error_size);
int platform_decompression_identify_path_range_json_alloc(const char *provider_id, const char *provider_path,
  const char *path, uint32_t offset, uint32_t size, char **out_text);
int platform_decompression_identify_buffer_range(const char *provider_id, const char *provider_path,
  const uint8_t *data, uint32_t data_size, uint32_t offset, uint32_t size,
  PlatformDecompressionIdentifyResult *out_result, char *error, size_t error_size);
int platform_decompression_decompress_path_range(const char *provider_id, const char *provider_path,
  const char *path, uint32_t offset, uint32_t size, const char *output_path,
  PlatformDecompressionIdentifyResult *out_result, char *error, size_t error_size);
int platform_decompression_decompress_buffer_range(const char *provider_id, const char *provider_path,
  const uint8_t *data, uint32_t data_size, uint32_t offset, uint32_t size, const char *output_path,
  PlatformDecompressionIdentifyResult *out_result, char *error, size_t error_size);
int platform_decompression_decompress_path_range_json_alloc(const char *provider_id, const char *provider_path,
  const char *path, uint32_t offset, uint32_t size, const char *output_path, char **out_text);
size_t platform_decompression_find_candidates_in_buffer(const char *provider_id, const uint8_t *data,
  uint32_t data_size, PlatformDecompressionCandidate *out_candidates, size_t candidate_capacity);
int platform_decompression_append_result_json(JsonBuilder *builder,
  const PlatformDecompressionIdentifyResult *result);
void platform_decompression_free_text(char *text);

#endif
