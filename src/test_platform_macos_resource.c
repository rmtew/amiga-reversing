#include "m68k_c_unit_test.h"
#include "platform_macos_resource.h"

#include <string.h>

static void put_u16(unsigned char *data, size_t offset, uint16_t value) {
  data[offset] = (unsigned char)(value >> 8);
  data[offset + 1U] = (unsigned char)value;
}

static void put_i16(unsigned char *data, size_t offset, int16_t value) {
  put_u16(data, offset, (uint16_t)value);
}

static void put_u24(unsigned char *data, size_t offset, uint32_t value) {
  data[offset] = (unsigned char)(value >> 16);
  data[offset + 1U] = (unsigned char)(value >> 8);
  data[offset + 2U] = (unsigned char)value;
}

static void put_u32(unsigned char *data, size_t offset, uint32_t value) {
  data[offset] = (unsigned char)(value >> 24);
  data[offset + 1U] = (unsigned char)(value >> 16);
  data[offset + 2U] = (unsigned char)(value >> 8);
  data[offset + 3U] = (unsigned char)value;
}

static void put_resource_header(unsigned char *data, uint32_t data_offset, uint32_t map_offset,
    uint32_t data_length, uint32_t map_length) {
  put_u32(data, 0U, data_offset);
  put_u32(data, 4U, map_offset);
  put_u32(data, 8U, data_length);
  put_u32(data, 12U, map_length);
  put_u32(data, map_offset, data_offset);
  put_u32(data, map_offset + 4U, map_offset);
  put_u32(data, map_offset + 8U, data_length);
  put_u32(data, map_offset + 12U, map_length);
}

static size_t make_two_code_resource_fork(unsigned char *data, size_t data_size) {
  const uint32_t data_offset = 0x100U;
  const uint32_t map_offset = 0x140U;
  const uint32_t map_length = 0x60U;
  size_t code0_payload = data_offset + 4U;
  size_t code1_record = data_offset + 20U;
  size_t code1_payload = code1_record + 4U;
  size_t type_list = map_offset + 28U;
  size_t ref_list = type_list + 10U;
  if (data_size < map_offset + map_length) return 0U;
  memset(data, 0, data_size);
  put_resource_header(data, data_offset, map_offset, 38U, map_length);
  put_u32(data, data_offset, 16U);
  put_u32(data, code0_payload, 32U);
  put_u32(data, code0_payload + 4U, 64U);
  put_u32(data, code0_payload + 8U, 8U);
  put_u32(data, code0_payload + 12U, 32U);
  put_u32(data, code1_record, 14U);
  put_u16(data, code1_payload, 4U);
  put_u16(data, code1_payload + 2U, 2U);
  put_u32(data, code1_payload + 4U, 0x00000010U);
  put_u16(data, code1_payload + 8U, 0U);
  data[code1_payload + 10U] = 0x20;
  data[code1_payload + 11U] = 0x5F;
  data[code1_payload + 12U] = 0x4E;
  data[code1_payload + 13U] = 0x75;

  put_u16(data, map_offset + 24U, 28U);
  put_u16(data, map_offset + 26U, 58U);
  put_u16(data, type_list, 0U);
  memcpy(data + type_list + 2U, "CODE", 4U);
  put_u16(data, type_list + 6U, 1U);
  put_u16(data, type_list + 8U, 10U);
  put_i16(data, ref_list, 0);
  put_i16(data, ref_list + 2U, -1);
  data[ref_list + 4U] = 0x20;
  put_u24(data, ref_list + 5U, 0U);
  put_i16(data, ref_list + 12U, 1);
  put_i16(data, ref_list + 14U, -1);
  put_u24(data, ref_list + 17U, 20U);
  return map_offset + map_length;
}

static int test_resource_fork_parses_code_metadata(void) {
  unsigned char data[512];
  PlatformMacosResourceFork fork;
  PlatformMacosResourceTypeInfo types[1];
  PlatformMacosResourceInfo resources[2];
  size_t size = make_two_code_resource_fork(data, sizeof(data));
  M68K_C_ASSERT(size != 0U);
  M68K_C_ASSERT_INT(0, platform_macos_resource_fork_parse(data, size, &fork, types, 1U, resources, 2U));
  M68K_C_ASSERT_U32(0x100U, fork.header.resource_data_offset);
  M68K_C_ASSERT_U32(0x140U, fork.header.resource_map_offset);
  M68K_C_ASSERT_U32(1U, fork.type_count);
  M68K_C_ASSERT_U32(2U, fork.resource_count);
  M68K_C_ASSERT_STR("CODE", types[0].type);
  M68K_C_ASSERT_U32(2U, types[0].count);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_RESOURCE_JUMP_TABLE_SEGMENT, resources[0].code.kind);
  M68K_C_ASSERT_U32(32U, resources[0].code.above_a5_size);
  M68K_C_ASSERT_U32(64U, resources[0].code.below_a5_size);
  M68K_C_ASSERT_U32(8U, resources[0].code.jump_table_length);
  M68K_C_ASSERT_U32(32U, resources[0].code.jump_table_offset_from_a5);
  M68K_C_ASSERT_U32(1U, resources[0].code.layout_range_count);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_RANGE_METADATA, resources[0].code.layout_ranges[0].kind);
  M68K_C_ASSERT_U32(0U, resources[0].code.layout_ranges[0].start_offset);
  M68K_C_ASSERT_U32(16U, resources[0].code.layout_ranges[0].size);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_RESOURCE_CODE_SEGMENT, resources[1].code.kind);
  M68K_C_ASSERT_U32(4U, resources[1].code.first_jump_table_entry_offset);
  M68K_C_ASSERT_U32(2U, resources[1].code.jump_table_entry_count);
  M68K_C_ASSERT_U32(3U, resources[1].code.layout_range_count);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_RANGE_METADATA, resources[1].code.layout_ranges[0].kind);
  M68K_C_ASSERT_U32(0U, resources[1].code.layout_ranges[0].start_offset);
  M68K_C_ASSERT_U32(4U, resources[1].code.layout_ranges[0].size);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_RANGE_DATA, resources[1].code.layout_ranges[1].kind);
  M68K_C_ASSERT_U32(4U, resources[1].code.layout_ranges[1].start_offset);
  M68K_C_ASSERT_U32(6U, resources[1].code.layout_ranges[1].size);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_RANGE_CANDIDATE_CODE, resources[1].code.layout_ranges[2].kind);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_EVIDENCE_M68K_STACK_ENTRY_TO_A0, resources[1].code.layout_ranges[2].evidence);
  M68K_C_ASSERT_U32(10U, resources[1].code.layout_ranges[2].start_offset);
  M68K_C_ASSERT_U32(4U, resources[1].code.layout_ranges[2].size);
  M68K_C_ASSERT_U32(1U, resources[1].code.layout_ranges[2].entrypoint);
  return 0;
}

static int test_resource_fork_finds_selected_payload_bounds(void) {
  unsigned char data[512];
  uint32_t payload_offset = 0U;
  uint32_t payload_size = 0U;
  size_t size = make_two_code_resource_fork(data, sizeof(data));
  M68K_C_ASSERT(size != 0U);
  M68K_C_ASSERT_INT(0, platform_macos_resource_fork_find_payload(data, size, "CODE", 1, &payload_offset,
    &payload_size));
  M68K_C_ASSERT_U32(0x118U, payload_offset);
  M68K_C_ASSERT_U32(14U, payload_size);
  M68K_C_ASSERT_U32(0x00, data[payload_offset]);
  M68K_C_ASSERT_U32(0x04, data[payload_offset + 1U]);
  M68K_C_ASSERT_U32(0x20, data[payload_offset + 10U]);
  M68K_C_ASSERT_U32(0x5F, data[payload_offset + 11U]);
  M68K_C_ASSERT_INT(1, platform_macos_resource_fork_find_payload(data, size, "CODE", 2, &payload_offset,
    &payload_size));
  return 0;
}

static int test_code_layout_defers_nonzero_payload_without_entry(void) {
  unsigned char data[512];
  PlatformMacosResourceFork fork;
  PlatformMacosResourceInfo resources[2];
  size_t size = make_two_code_resource_fork(data, sizeof(data));
  M68K_C_ASSERT(size != 0U);
  data[0x118U + 10U] = 0x4E;
  data[0x118U + 11U] = 0x75;
  M68K_C_ASSERT_INT(0, platform_macos_resource_fork_parse(data, size, &fork, NULL, 0U, resources, 2U));
  M68K_C_ASSERT_U32(2U, resources[1].code.layout_range_count);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_RANGE_METADATA, resources[1].code.layout_ranges[0].kind);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_RANGE_DEFERRED, resources[1].code.layout_ranges[1].kind);
  M68K_C_ASSERT_U32(PLATFORM_MACOS_CODE_EVIDENCE_MISSING_STACK_ENTRY, resources[1].code.layout_ranges[1].evidence);
  M68K_C_ASSERT_U32(4U, resources[1].code.layout_ranges[1].start_offset);
  M68K_C_ASSERT_U32(10U, resources[1].code.layout_ranges[1].size);
  return 0;
}

static int test_resource_fork_rejects_payload_past_end(void) {
  unsigned char data[512];
  PlatformMacosResourceFork fork;
  size_t size = make_two_code_resource_fork(data, sizeof(data));
  M68K_C_ASSERT(size != 0U);
  put_u32(data, 0x114U, 0x1000U);
  M68K_C_ASSERT_INT(-1, platform_macos_resource_fork_parse(data, size, &fork, NULL, 0U, NULL, 0U));
  return 0;
}

static int test_restored_source_verifier_accepts_complete_candidate_coverage(void) {
  PlatformMacosRestoredSourceCoverageVerifier verifier;
  const PlatformMacosRestoredSourceRangeView ranges[] = {
    {"metadata", 0U, 4U, 4U, "validated", "header", "test", 1U, 0U},
    {"candidate_code", 4U, 4U, 8U, "candidate", "entry", "test", 1U, 1U},
  };
  M68K_C_ASSERT_INT(0, platform_macos_restored_source_verify_ranges(ranges, 2U, 8U, &verifier));
  M68K_C_ASSERT_U32(1U, verifier.ok);
  M68K_C_ASSERT_U32(0U, verifier.gap_count);
  M68K_C_ASSERT_U32(0U, verifier.overlap_count);
  M68K_C_ASSERT_U32(0U, verifier.invalid_instruction_ownership_count);
  M68K_C_ASSERT_U32(0U, verifier.explicit_unknown_missing_detail_count);
  return 0;
}

static int test_restored_source_verifier_rejects_gaps(void) {
  PlatformMacosRestoredSourceCoverageVerifier verifier;
  const PlatformMacosRestoredSourceRangeView ranges[] = {
    {"metadata", 0U, 2U, 2U, "validated", "header", "test", 1U, 0U},
    {"candidate_code", 4U, 2U, 6U, "candidate", "entry", "test", 1U, 1U},
  };
  M68K_C_ASSERT_INT(0, platform_macos_restored_source_verify_ranges(ranges, 2U, 6U, &verifier));
  M68K_C_ASSERT_U32(0U, verifier.ok);
  M68K_C_ASSERT_U32(1U, verifier.gap_count);
  return 0;
}

static int test_restored_source_verifier_rejects_overlaps(void) {
  PlatformMacosRestoredSourceCoverageVerifier verifier;
  const PlatformMacosRestoredSourceRangeView ranges[] = {
    {"metadata", 0U, 4U, 4U, "validated", "header", "test", 1U, 0U},
    {"candidate_code", 2U, 4U, 6U, "candidate", "entry", "test", 1U, 1U},
  };
  M68K_C_ASSERT_INT(0, platform_macos_restored_source_verify_ranges(ranges, 2U, 6U, &verifier));
  M68K_C_ASSERT_U32(0U, verifier.ok);
  M68K_C_ASSERT_U32(1U, verifier.overlap_count);
  return 0;
}

static int test_restored_source_verifier_rejects_malformed_unknown_ranges(void) {
  PlatformMacosRestoredSourceCoverageVerifier verifier;
  const PlatformMacosRestoredSourceRangeView ranges[] = {
    {"unknown", 0U, 4U, 4U, "deferred", "", "test", 1U, 0U},
    {"unknown", 4U, 4U, 8U, "deferred", "missing provenance", "", 1U, 0U},
    {"unknown", 8U, 4U, 12U, "deferred", "hidden unknown", "test", 0U, 0U},
  };
  M68K_C_ASSERT_INT(0, platform_macos_restored_source_verify_ranges(ranges, 3U, 12U, &verifier));
  M68K_C_ASSERT_U32(0U, verifier.ok);
  M68K_C_ASSERT_U32(3U, verifier.explicit_unknown_missing_detail_count);
  return 0;
}

static int test_restored_source_verifier_rejects_unsafe_instruction_ownership(void) {
  PlatformMacosRestoredSourceCoverageVerifier verifier;
  const PlatformMacosRestoredSourceRangeView ranges[] = {
    {"data", 0U, 2U, 2U, "candidate", "instruction claimed as data", "test", 1U, 1U},
    {"candidate_code", 2U, 2U, 4U, "validated", "candidate role with accepted status", "test", 1U, 1U},
  };
  M68K_C_ASSERT_INT(0, platform_macos_restored_source_verify_ranges(ranges, 2U, 4U, &verifier));
  M68K_C_ASSERT_U32(0U, verifier.ok);
  M68K_C_ASSERT_U32(2U, verifier.invalid_instruction_ownership_count);
  return 0;
}

int m68k_c_platform_macos_resource_tests(void) {
  static const M68kCTestCase cases[] = {
    {"resource_fork_parses_code_metadata", test_resource_fork_parses_code_metadata},
    {"resource_fork_finds_selected_payload_bounds", test_resource_fork_finds_selected_payload_bounds},
    {"code_layout_defers_nonzero_payload_without_entry", test_code_layout_defers_nonzero_payload_without_entry},
    {"resource_fork_rejects_payload_past_end", test_resource_fork_rejects_payload_past_end},
    {"restored_source_verifier_accepts_complete_candidate_coverage",
      test_restored_source_verifier_accepts_complete_candidate_coverage},
    {"restored_source_verifier_rejects_gaps", test_restored_source_verifier_rejects_gaps},
    {"restored_source_verifier_rejects_overlaps", test_restored_source_verifier_rejects_overlaps},
    {"restored_source_verifier_rejects_malformed_unknown_ranges",
      test_restored_source_verifier_rejects_malformed_unknown_ranges},
    {"restored_source_verifier_rejects_unsafe_instruction_ownership",
      test_restored_source_verifier_rejects_unsafe_instruction_ownership},
  };
  return m68k_c_test_run_suite("platform_macos_resource", cases, sizeof(cases) / sizeof(cases[0]));
}
