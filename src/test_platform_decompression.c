#include "m68k_c_unit_test.h"
#include "platform_file_decompression.h"

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static int test_decompression_identify_rejects_unknown_provider(void) {
  PlatformDecompressionIdentifyResult result;
  char error[128];
  error[0] = '\0';
  M68K_C_ASSERT_INT(-1, platform_decompression_identify_path_range("missing-provider", "", "missing.bin", 0U, 1U,
    &result, error, sizeof(error)));
  M68K_C_ASSERT(strstr(error, "unsupported decompression provider") != NULL);
  return 0;
}

static int test_decompression_identify_reports_unknown_payload_without_failure(void) {
  FILE *file;
  char path[256];
  char error[128];
  PlatformDecompressionIdentifyResult result;
  snprintf(path, sizeof(path), "%s\\amiga_depack_unknown_%u.bin", getenv("TEMP") != NULL ? getenv("TEMP") : ".",
    (unsigned)(uint32_t)rand());
  file = fopen(path, "wb");
  M68K_C_ASSERT(file != NULL);
  fputs("not packed", file);
  fclose(file);
  error[0] = '\0';
  M68K_C_ASSERT_INT(0, platform_decompression_identify_path_range("ancient-cli", "ext\\tools\\ancient\\Ancient.exe",
    path, 0U, 10U, &result, error, sizeof(error)));
  M68K_C_ASSERT_U32(0U, result.found);
  M68K_C_ASSERT_STR("ancient-cli", result.provider_id);
  M68K_C_ASSERT_U32(64U, (uint32_t)strlen(result.source_sha256));
  remove(path);
  return 0;
}

static int test_decompression_does_not_write_unknown_payload(void) {
  FILE *file;
  char path[256];
  char output_path[256];
  char error[128];
  PlatformDecompressionIdentifyResult result;
  snprintf(path, sizeof(path), "%s\\amiga_depack_unknown_%u.bin", getenv("TEMP") != NULL ? getenv("TEMP") : ".",
    (unsigned)(uint32_t)rand());
  snprintf(output_path, sizeof(output_path), "%s.out", path);
  remove(output_path);
  file = fopen(path, "wb");
  M68K_C_ASSERT(file != NULL);
  fputs("not packed", file);
  fclose(file);
  error[0] = '\0';
  M68K_C_ASSERT_INT(0, platform_decompression_decompress_path_range("ancient-cli",
    "ext\\tools\\ancient\\Ancient.exe", path, 0U, 10U, output_path, &result, error, sizeof(error)));
  M68K_C_ASSERT_U32(0U, result.found);
  M68K_C_ASSERT_U32(0U, result.decompressed);
  M68K_C_ASSERT(fopen(output_path, "rb") == NULL);
  remove(path);
  remove(output_path);
  return 0;
}

static int test_decompression_candidate_scan_uses_provider_header_size(void) {
  uint8_t data[40];
  PlatformDecompressionCandidate candidates[2];
  size_t count;
  memset(data, 0, sizeof(data));
  memcpy(data, "RNC\001", 4U);
  data[11] = 5U;
  count = platform_decompression_find_candidates_in_buffer("ancient-cli", data, sizeof(data), candidates,
    sizeof(candidates) / sizeof(candidates[0]));
  M68K_C_ASSERT_U32(1U, (uint32_t)count);
  M68K_C_ASSERT_U32(0U, candidates[0].offset);
  M68K_C_ASSERT_U32(23U, candidates[0].packed_size);
  M68K_C_ASSERT_STR("rnc1", candidates[0].codec_hint);
  return 0;
}

int m68k_c_platform_decompression_tests(void) {
  static const M68kCTestCase cases[] = {
    {"decompression_identify_rejects_unknown_provider", test_decompression_identify_rejects_unknown_provider},
    {"decompression_identify_reports_unknown_payload_without_failure",
      test_decompression_identify_reports_unknown_payload_without_failure},
    {"decompression_does_not_write_unknown_payload", test_decompression_does_not_write_unknown_payload},
    {"decompression_candidate_scan_uses_provider_header_size",
      test_decompression_candidate_scan_uses_provider_header_size},
  };
  return m68k_c_test_run_suite("platform_decompression", cases, sizeof(cases) / sizeof(cases[0]));
}
