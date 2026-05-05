#ifndef PLATFORM_FILE_DECOMPRESSION_H
#define PLATFORM_FILE_DECOMPRESSION_H

#include "json_builder.h"

#include <stddef.h>
#include <stdint.h>

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
