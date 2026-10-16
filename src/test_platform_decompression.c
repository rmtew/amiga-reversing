#include "m68k_c_unit_test.h"
#include "platform_file_decompression.h"
#include "platform_common.h"

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static void test_decompression_temp_path(char *path, size_t capacity, const char *stem) {
#ifdef _WIN32
  const char *directory = getenv("TEMP");
  const char separator = '\\';
#else
  const char *directory = getenv("TMPDIR");
  const char separator = '/';
#endif
  if (directory == NULL || directory[0] == '\0') directory = ".";
  snprintf(path, capacity, "%s%camiga_%s_%u.bin", directory, separator, stem, (unsigned)(uint32_t)rand());
}

static int test_native_file_sha256_vectors_and_errors(void) {
  FILE *file;
  char path[256], digest[65], expected[65];
  uint32_t size;
  uint8_t bytes[17003];
  size_t index;
  test_decompression_temp_path(path, sizeof(path), "sha256");
  file = fopen(path, "wb");
  M68K_C_ASSERT(file != NULL);
  fclose(file);
  M68K_C_ASSERT_INT(0, m68k_platform_file_sha256_hex(path, &size, digest));
  M68K_C_ASSERT_U32(0U, size);
  M68K_C_ASSERT_STR("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", digest);
  file = fopen(path, "wb");
  M68K_C_ASSERT(file != NULL);
  fputs("abc", file);
  fclose(file);
  M68K_C_ASSERT_INT(0, m68k_platform_file_sha256_hex(path, &size, digest));
  M68K_C_ASSERT_U32(3U, size);
  M68K_C_ASSERT_STR("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", digest);
  for (index = 0U; index < sizeof(bytes); ++index) bytes[index] = (uint8_t)(index & 0xffU);
  file = fopen(path, "wb");
  M68K_C_ASSERT(file != NULL);
  M68K_C_ASSERT_U32(sizeof(bytes), fwrite(bytes, 1U, sizeof(bytes), file));
  fclose(file);
  M68K_C_ASSERT_INT(0, m68k_platform_sha256_hex(bytes, sizeof(bytes), expected));
  M68K_C_ASSERT_INT(0, m68k_platform_file_sha256_hex(path, &size, digest));
  M68K_C_ASSERT_U32(sizeof(bytes), size);
  M68K_C_ASSERT_STR(expected, digest);
  remove(path);
  M68K_C_ASSERT_INT(-1, m68k_platform_file_sha256_hex(path, &size, digest));
  M68K_C_ASSERT_U32(0U, size);
  M68K_C_ASSERT_STR("", digest);
  return 0;
}

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
#ifdef _WIN32
  const char *provider = "ext\\tools\\ancient\\Ancient.exe";
#else
  /* This metadata/unknown-input test needs a readable executable, not Ancient. */
  const char *provider = "/bin/false";
#endif
  test_decompression_temp_path(path, sizeof(path), "depack_unknown");
  file = fopen(path, "wb");
  M68K_C_ASSERT(file != NULL);
  fputs("not packed", file);
  fclose(file);
  error[0] = '\0';
  M68K_C_ASSERT_INT(0, platform_decompression_identify_path_range("ancient-cli", provider,
    path, 0U, 10U, &result, error, sizeof(error)));
  M68K_C_ASSERT_U32(0U, result.found);
  M68K_C_ASSERT_STR("ancient-cli", result.provider_id);
  M68K_C_ASSERT_U32(64U, (uint32_t)strlen(result.provider_sha256));
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
  test_decompression_temp_path(path, sizeof(path), "depack_unknown");
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

static int test_decompression_candidate_scan_rejects_header_guess(void) {
  uint8_t data[40];
  PlatformDecompressionCandidate candidates[2];
  size_t count;
  memset(data, 0, sizeof(data));
  memcpy(data, "RNC\001", 4U);
  data[11] = 5U;
  count = platform_decompression_find_candidates_in_buffer("ancient-cli", data, sizeof(data), candidates,
    sizeof(candidates) / sizeof(candidates[0]));
  M68K_C_ASSERT_U32(0U, (uint32_t)count);
  return 0;
}

static int test_decompression_candidate_scan_requires_provider_validation(void) {
  uint8_t data[96];
  PlatformDecompressionCandidate candidates[4];
  size_t count;
  memset(data, 0, sizeof(data));
  memcpy(data + 4U, "RNC\002", 4U);
  data[15] = 7U;
  memcpy(data + 48U, "...\001", 4U);
  data[59] = 9U;
  count = platform_decompression_find_candidates_in_buffer("ancient-cli", data, sizeof(data), candidates,
    sizeof(candidates) / sizeof(candidates[0]));
  M68K_C_ASSERT_U32(0U, (uint32_t)count);
  return 0;
}

static int test_decompression_result_json_exports_codec_support_id(void) {
  PlatformDecompressionIdentifyResult result;
  JsonBuilder builder = {0};
  char *json;
  platform_decompression_identify_result_init(&result);
  result.found = 1;
  snprintf(result.provider_id, sizeof(result.provider_id), "ancient-cli");
  snprintf(result.codec_id, sizeof(result.codec_id), "rnc1-old");
  snprintf(result.codec_name, sizeof(result.codec_name), "RNC1");
  snprintf(result.confidence, sizeof(result.confidence), "tool");
  M68K_C_ASSERT_INT(0, json_builder_create(&builder));
  M68K_C_ASSERT_INT(0, platform_decompression_append_result_json(&builder, &result));
  json = json_builder_build(&builder);
  M68K_C_ASSERT(json != NULL);
  M68K_C_ASSERT(strstr(json, "\"codec_support_id\":1,\"codec_support\":\"external_provider\"") != NULL);
  free(json);
  return 0;
}

int m68k_c_platform_decompression_tests(void) {
  static const M68kCTestCase cases[] = {
    {"native_file_sha256_vectors_and_errors", test_native_file_sha256_vectors_and_errors},
    {"decompression_identify_rejects_unknown_provider", test_decompression_identify_rejects_unknown_provider},
    {"decompression_identify_reports_unknown_payload_without_failure",
      test_decompression_identify_reports_unknown_payload_without_failure},
    {"decompression_does_not_write_unknown_payload", test_decompression_does_not_write_unknown_payload},
    {"decompression_candidate_scan_rejects_header_guess",
      test_decompression_candidate_scan_rejects_header_guess},
    {"decompression_candidate_scan_requires_provider_validation",
      test_decompression_candidate_scan_requires_provider_validation},
    {"decompression_result_json_exports_codec_support_id",
      test_decompression_result_json_exports_codec_support_id},
  };
  return m68k_c_test_run_suite("platform_decompression", cases, sizeof(cases) / sizeof(cases[0]));
}
