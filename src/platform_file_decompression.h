#ifndef PLATFORM_FILE_DECOMPRESSION_H
#define PLATFORM_FILE_DECOMPRESSION_H

#include <stddef.h>
#include <stdint.h>

typedef struct PlatformDecompressionIdentifyResult {
  int found;
  char provider_id[32];
  char provider_path[512];
  char codec_id[64];
  char codec_name[160];
  char confidence[32];
  char source_sha256[65];
  char decompressed_sha256[65];
  char decompressed_path[512];
  uint32_t source_offset;
  uint32_t packed_size;
  uint32_t decompressed_size;
  int decompressed;
} PlatformDecompressionIdentifyResult;

void platform_decompression_identify_result_init(PlatformDecompressionIdentifyResult *result);
int platform_decompression_identify_path_range(const char *provider_id, const char *provider_path,
  const char *path, uint32_t offset, uint32_t size, PlatformDecompressionIdentifyResult *out_result,
  char *error, size_t error_size);
int platform_decompression_identify_path_range_json_alloc(const char *provider_id, const char *provider_path,
  const char *path, uint32_t offset, uint32_t size, char **out_text);
int platform_decompression_decompress_path_range(const char *provider_id, const char *provider_path,
  const char *path, uint32_t offset, uint32_t size, const char *output_path,
  PlatformDecompressionIdentifyResult *out_result, char *error, size_t error_size);
int platform_decompression_decompress_path_range_json_alloc(const char *provider_id, const char *provider_path,
  const char *path, uint32_t offset, uint32_t size, const char *output_path, char **out_text);
void platform_decompression_free_text(char *text);

#endif
