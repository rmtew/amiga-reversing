#include "platform_macos_resource.h"
#include "generated/platform_executable_formats.h"

#include <stdint.h>
#include <string.h>

static uint16_t read_u16be_at(const unsigned char *data, size_t offset) {
  return (uint16_t)(((uint16_t)data[offset] << 8) | (uint16_t)data[offset + 1U]);
}

static int16_t read_i16be_at(const unsigned char *data, size_t offset) {
  return (int16_t)read_u16be_at(data, offset);
}

static uint32_t read_u24be_at(const unsigned char *data, size_t offset) {
  return ((uint32_t)data[offset] << 16) | ((uint32_t)data[offset + 1U] << 8) | (uint32_t)data[offset + 2U];
}

static uint32_t read_u32be_at(const unsigned char *data, size_t offset) {
  return ((uint32_t)data[offset] << 24) | ((uint32_t)data[offset + 1U] << 16) |
    ((uint32_t)data[offset + 2U] << 8) | (uint32_t)data[offset + 3U];
}

static int range_fits(size_t offset, size_t length, size_t size) {
  return offset <= size && length <= size - offset;
}

static void copy_resource_type(char out_type[PLATFORM_MACOS_RESOURCE_TYPE_SIZE],
    const unsigned char *data, size_t offset) {
  memcpy(out_type, data + offset, 4U);
  out_type[4] = '\0';
}

static int resource_type_matches(const char type[PLATFORM_MACOS_RESOURCE_TYPE_SIZE], const char *expected) {
  return expected != NULL && expected[0] != '\0' && expected[1] != '\0' &&
    expected[2] != '\0' && expected[3] != '\0' && expected[4] == '\0' &&
    type[0] == expected[0] && type[1] == expected[1] && type[2] == expected[2] && type[3] == expected[3];
}

static int append_code_range(PlatformMacosCodeMetadata *code, uint8_t kind, uint8_t evidence,
    uint32_t start_offset, uint32_t size, uint8_t entrypoint) {
  PlatformMacosCodeRange *range;
  if (code == NULL || size == 0U) return 0;
  if (code->layout_range_count >= PLATFORM_MACOS_CODE_LAYOUT_RANGE_CAPACITY) return -1;
  range = &code->layout_ranges[code->layout_range_count++];
  memset(range, 0, sizeof(*range));
  range->kind = kind;
  range->evidence = evidence;
  range->entrypoint = entrypoint;
  range->start_offset = start_offset;
  range->size = size;
  return 0;
}

static uint32_t find_stack_entry_to_a0_pattern(const unsigned char *payload, uint32_t payload_size,
    uint32_t start_offset) {
  uint32_t offset;
  if (payload == NULL || start_offset >= payload_size) return UINT32_MAX;
  for (offset = start_offset; offset + 1U < payload_size; offset += 2U) {
    if (payload[offset] == 0x20U && payload[offset + 1U] == 0x5FU) return offset;
  }
  return UINT32_MAX;
}

int platform_macos_code_metadata_parse(const unsigned char *payload, uint32_t payload_size,
    int16_t resource_id, PlatformMacosCodeMetadata *out_code) {
  uint32_t entry_offset;
  if (out_code == NULL) return -1;
  memset(out_code, 0, sizeof(*out_code));
  if (resource_id == 0) {
    out_code->kind = PLATFORM_MACOS_CODE_RESOURCE_JUMP_TABLE_SEGMENT;
    if (payload_size >= 16U && payload != NULL) {
      out_code->above_a5_size = read_u32be_at(payload, 0U);
      out_code->below_a5_size = read_u32be_at(payload, 4U);
      out_code->jump_table_length = read_u32be_at(payload, 8U);
      out_code->jump_table_offset_from_a5 = read_u32be_at(payload, 12U);
    }
    return append_code_range(out_code, PLATFORM_MACOS_CODE_RANGE_METADATA,
      PLATFORM_MACOS_CODE_EVIDENCE_CODE0_JUMP_TABLE_METADATA, 0U, payload_size, 0U);
  }
  out_code->kind = PLATFORM_MACOS_CODE_RESOURCE_CODE_SEGMENT;
  if (payload_size >= 4U && payload != NULL) {
    out_code->first_jump_table_entry_offset = read_u16be_at(payload, 0U);
    out_code->jump_table_entry_count = read_u16be_at(payload, 2U);
    if (append_code_range(out_code, PLATFORM_MACOS_CODE_RANGE_METADATA,
        PLATFORM_MACOS_CODE_EVIDENCE_NONZERO_SEGMENT_HEADER, 0U, 4U, 0U) != 0) {
      return -1;
    }
  }
  if (payload_size <= 4U || payload == NULL) return 0;
  entry_offset = find_stack_entry_to_a0_pattern(payload, payload_size, 4U);
  if (entry_offset == UINT32_MAX) {
    return append_code_range(out_code, PLATFORM_MACOS_CODE_RANGE_DEFERRED,
      PLATFORM_MACOS_CODE_EVIDENCE_MISSING_STACK_ENTRY, 4U, payload_size - 4U, 0U);
  }
  if (entry_offset > 4U &&
      append_code_range(out_code, PLATFORM_MACOS_CODE_RANGE_DATA,
        PLATFORM_MACOS_CODE_EVIDENCE_PREFIX_BEFORE_STACK_ENTRY, 4U, entry_offset - 4U, 0U) != 0) {
    return -1;
  }
  return append_code_range(out_code, PLATFORM_MACOS_CODE_RANGE_CANDIDATE_CODE,
    PLATFORM_MACOS_CODE_EVIDENCE_M68K_STACK_ENTRY_TO_A0, entry_offset, payload_size - entry_offset, 1U);
}

int platform_macos_code_metadata_executable_range(const PlatformMacosCodeMetadata *code,
    uint32_t *out_start_offset, uint32_t *out_size) {
  size_t index;
  if (out_start_offset != NULL) *out_start_offset = 0U;
  if (out_size != NULL) *out_size = 0U;
  if (code == NULL) return -1;
  for (index = 0U; index < code->layout_range_count; ++index) {
    const PlatformMacosCodeRange *range = &code->layout_ranges[index];
    if ((range->kind == PLATFORM_MACOS_CODE_RANGE_CONFIRMED_CODE ||
         range->kind == PLATFORM_MACOS_CODE_RANGE_CANDIDATE_CODE) && range->entrypoint) {
      if (out_start_offset != NULL) *out_start_offset = range->start_offset;
      if (out_size != NULL) *out_size = range->size;
      return 0;
    }
  }
  return 1;
}

const char *platform_macos_code_range_kind_name(uint8_t kind) {
  switch (kind) {
    case PLATFORM_MACOS_CODE_RANGE_METADATA: return "metadata";
    case PLATFORM_MACOS_CODE_RANGE_DATA: return "data";
    case PLATFORM_MACOS_CODE_RANGE_CANDIDATE_CODE: return "candidate_code";
    case PLATFORM_MACOS_CODE_RANGE_CONFIRMED_CODE: return "confirmed_code";
    case PLATFORM_MACOS_CODE_RANGE_DEFERRED: return "deferred";
    default: return "none";
  }
}

const char *platform_macos_code_range_evidence_name(uint8_t evidence) {
  switch (evidence) {
    case PLATFORM_MACOS_CODE_EVIDENCE_CODE0_JUMP_TABLE_METADATA: return "code0_jump_table_metadata";
    case PLATFORM_MACOS_CODE_EVIDENCE_NONZERO_SEGMENT_HEADER: return "nonzero_code_segment_header";
    case PLATFORM_MACOS_CODE_EVIDENCE_PREFIX_BEFORE_STACK_ENTRY: return "prefix_before_stack_entry";
    case PLATFORM_MACOS_CODE_EVIDENCE_M68K_STACK_ENTRY_TO_A0: return "m68k_movea_l_stack_to_a0_entry";
    case PLATFORM_MACOS_CODE_EVIDENCE_MISSING_STACK_ENTRY: return "missing_m68k_movea_l_stack_to_a0_entry";
    default: return "none";
  }
}

const char *platform_macos_code_range_fact_id(uint8_t evidence) {
  switch (evidence) {
    case PLATFORM_MACOS_CODE_EVIDENCE_CODE0_JUMP_TABLE_METADATA:
      return PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_CODE_RESOURCE_0_JUMP_TABLE_METADATA;
    case PLATFORM_MACOS_CODE_EVIDENCE_NONZERO_SEGMENT_HEADER:
      return PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_CODE_RESOURCE_NONZERO_SEGMENT_HEADER;
    case PLATFORM_MACOS_CODE_EVIDENCE_PREFIX_BEFORE_STACK_ENTRY:
    case PLATFORM_MACOS_CODE_EVIDENCE_M68K_STACK_ENTRY_TO_A0:
      return PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_CODE_RESOURCE_MOVEA_STACK_A0_BOUNDARY_CANDIDATE;
    case PLATFORM_MACOS_CODE_EVIDENCE_MISSING_STACK_ENTRY:
      return PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_CODE_RESOURCE_BYTE_ENTRY_RULE_UNKNOWN;
    default:
      return "";
  }
}

const char *platform_macos_code_range_fact_status(uint8_t evidence) {
  switch (evidence) {
    case PLATFORM_MACOS_CODE_EVIDENCE_CODE0_JUMP_TABLE_METADATA:
    case PLATFORM_MACOS_CODE_EVIDENCE_NONZERO_SEGMENT_HEADER:
      return "validated";
    case PLATFORM_MACOS_CODE_EVIDENCE_PREFIX_BEFORE_STACK_ENTRY:
    case PLATFORM_MACOS_CODE_EVIDENCE_M68K_STACK_ENTRY_TO_A0:
      return "candidate";
    case PLATFORM_MACOS_CODE_EVIDENCE_MISSING_STACK_ENTRY:
      return "deferred";
    default:
      return "unsupported";
  }
}

const char *platform_macos_code_range_parser_use(uint8_t evidence) {
  switch (evidence) {
    case PLATFORM_MACOS_CODE_EVIDENCE_CODE0_JUMP_TABLE_METADATA:
    case PLATFORM_MACOS_CODE_EVIDENCE_NONZERO_SEGMENT_HEADER:
      return "accepted_parser_output";
    case PLATFORM_MACOS_CODE_EVIDENCE_PREFIX_BEFORE_STACK_ENTRY:
    case PLATFORM_MACOS_CODE_EVIDENCE_M68K_STACK_ENTRY_TO_A0:
      return "candidate_only";
    case PLATFORM_MACOS_CODE_EVIDENCE_MISSING_STACK_ENTRY:
      return "deferred_only";
    default:
      return "unsupported_only";
  }
}

static void parse_code_metadata(PlatformMacosResourceInfo *resource, const unsigned char *data) {
  if (resource->type[0] != 'C' || resource->type[1] != 'O' ||
      resource->type[2] != 'D' || resource->type[3] != 'E') {
    return;
  }
  (void)platform_macos_code_metadata_parse(data + resource->payload_offset, resource->payload_size,
    resource->resource_id, &resource->code);
}

int platform_macos_resource_fork_parse(const unsigned char *data, size_t size,
    PlatformMacosResourceFork *out_fork, PlatformMacosResourceTypeInfo *types,
    size_t type_capacity, PlatformMacosResourceInfo *resources,
    size_t resource_capacity) {
  PlatformMacosResourceFork fork;
  size_t type_index;
  size_t type_entry;
  if (data == NULL || out_fork == NULL || size < 16U) return -1;
  memset(&fork, 0, sizeof(fork));
  fork.header.resource_data_offset = read_u32be_at(data, 0U);
  fork.header.resource_map_offset = read_u32be_at(data, 4U);
  fork.header.resource_data_length = read_u32be_at(data, 8U);
  fork.header.resource_map_length = read_u32be_at(data, 12U);
  if (!range_fits(fork.header.resource_data_offset, fork.header.resource_data_length, size) ||
      !range_fits(fork.header.resource_map_offset, fork.header.resource_map_length, size) ||
      !range_fits(fork.header.resource_map_offset, 28U, size)) {
    return -1;
  }
  fork.type_list_offset = fork.header.resource_map_offset + read_u16be_at(data, fork.header.resource_map_offset + 24U);
  fork.name_list_offset = fork.header.resource_map_offset + read_u16be_at(data, fork.header.resource_map_offset + 26U);
  if (!range_fits(fork.type_list_offset, 2U, size)) return -1;
  fork.type_count = (size_t)read_u16be_at(data, fork.type_list_offset) + 1U;
  type_entry = fork.type_list_offset + 2U;
  for (type_index = 0U; type_index < fork.type_count; ++type_index) {
    char resource_type[PLATFORM_MACOS_RESOURCE_TYPE_SIZE];
    uint16_t resource_count;
    size_t ref_entry;
    uint16_t ref_list_delta;
    uint16_t resource_index;
    if (!range_fits(type_entry, 8U, size)) return -1;
    copy_resource_type(resource_type, data, type_entry);
    resource_count = (uint16_t)(read_u16be_at(data, type_entry + 4U) + 1U);
    ref_list_delta = read_u16be_at(data, type_entry + 6U);
    ref_entry = fork.type_list_offset + ref_list_delta;
    if (types != NULL && type_index < type_capacity) {
      memcpy(types[type_index].type, resource_type, sizeof(types[type_index].type));
      types[type_index].count = resource_count;
    }
    for (resource_index = 0U; resource_index < resource_count; ++resource_index) {
      uint32_t relative_payload_offset;
      size_t payload_header_offset;
      uint32_t payload_size;
      size_t payload_offset;
      PlatformMacosResourceInfo resource;
      if (!range_fits(ref_entry, 12U, size)) return -1;
      memset(&resource, 0, sizeof(resource));
      memcpy(resource.type, resource_type, sizeof(resource.type));
      resource.resource_id = read_i16be_at(data, ref_entry);
      resource.name_offset = read_i16be_at(data, ref_entry + 2U);
      resource.attributes = data[ref_entry + 4U];
      resource.data_offset = read_u24be_at(data, ref_entry + 5U);
      relative_payload_offset = resource.data_offset;
      payload_header_offset = (size_t)fork.header.resource_data_offset + (size_t)relative_payload_offset;
      if (!range_fits(payload_header_offset, 4U, size)) return -1;
      payload_size = read_u32be_at(data, payload_header_offset);
      payload_offset = payload_header_offset + 4U;
      if (!range_fits(payload_offset, payload_size, size) || payload_offset > UINT32_MAX) return -1;
      resource.payload_offset = (uint32_t)payload_offset;
      resource.payload_size = payload_size;
      parse_code_metadata(&resource, data);
      if (resources != NULL && fork.resource_count < resource_capacity) {
        resources[fork.resource_count] = resource;
      }
      ++fork.resource_count;
      ref_entry += 12U;
    }
    type_entry += 8U;
  }
  *out_fork = fork;
  return 0;
}

int platform_macos_resource_fork_find_payload(const unsigned char *data,
    size_t size, const char *resource_type, int16_t resource_id,
    uint32_t *out_payload_offset, uint32_t *out_payload_size) {
  PlatformMacosResourceFork fork;
  size_t type_index;
  size_t type_entry;
  if (out_payload_offset != NULL) *out_payload_offset = 0U;
  if (out_payload_size != NULL) *out_payload_size = 0U;
  if (platform_macos_resource_fork_parse(data, size, &fork, NULL, 0U, NULL, 0U) != 0) {
    return -1;
  }
  type_entry = fork.type_list_offset + 2U;
  for (type_index = 0U; type_index < fork.type_count; ++type_index) {
    char current_type[PLATFORM_MACOS_RESOURCE_TYPE_SIZE];
    uint16_t resource_count;
    uint16_t resource_index;
    size_t ref_entry;
    if (!range_fits(type_entry, 8U, size)) return -1;
    copy_resource_type(current_type, data, type_entry);
    resource_count = (uint16_t)(read_u16be_at(data, type_entry + 4U) + 1U);
    ref_entry = fork.type_list_offset + read_u16be_at(data, type_entry + 6U);
    for (resource_index = 0U; resource_index < resource_count; ++resource_index) {
      int16_t current_id;
      size_t payload_header_offset;
      uint32_t payload_size;
      size_t payload_offset;
      if (!range_fits(ref_entry, 12U, size)) return -1;
      current_id = read_i16be_at(data, ref_entry);
      payload_header_offset = (size_t)fork.header.resource_data_offset + (size_t)read_u24be_at(data, ref_entry + 5U);
      if (!range_fits(payload_header_offset, 4U, size)) return -1;
      payload_size = read_u32be_at(data, payload_header_offset);
      payload_offset = payload_header_offset + 4U;
      if (!range_fits(payload_offset, payload_size, size) || payload_offset > UINT32_MAX) return -1;
      if (current_id == resource_id && resource_type_matches(current_type, resource_type)) {
        if (out_payload_offset != NULL) *out_payload_offset = (uint32_t)payload_offset;
        if (out_payload_size != NULL) *out_payload_size = payload_size;
        return 0;
      }
      ref_entry += 12U;
    }
    type_entry += 8U;
  }
  return 1;
}

static int string_empty(const char *value) {
  return value == NULL || value[0] == '\0';
}

static int restored_source_role_allows_instruction(const char *role, const char *status) {
  if (role == NULL || status == NULL) return 0;
  if (strcmp(role, "code") == 0) return strcmp(status, "validated") == 0 || strcmp(status, "parser_asserted") == 0;
  if (strcmp(role, "candidate_code") == 0) return strcmp(status, "candidate") == 0;
  return 0;
}

int platform_macos_restored_source_verify_ranges(const PlatformMacosRestoredSourceRangeView *ranges,
    size_t range_count, uint32_t payload_size, PlatformMacosRestoredSourceCoverageVerifier *out_verifier) {
  size_t index;
  uint32_t cursor = 0U;
  PlatformMacosRestoredSourceCoverageVerifier verifier;
  if (out_verifier == NULL) return -1;
  memset(&verifier, 0, sizeof(verifier));
  if (ranges == NULL && range_count != 0U) return -1;
  for (index = 0U; index < range_count; ++index) {
    const PlatformMacosRestoredSourceRangeView *range = &ranges[index];
    uint32_t end = range->end;
    if (range->size != 0U && end == 0U) end = range->start + range->size;
    if (range->start > cursor) ++verifier.gap_count;
    if (range->start < cursor) ++verifier.overlap_count;
    if (range->role != NULL && strcmp(range->role, "unknown") == 0 &&
        (string_empty(range->reason) || string_empty(range->provenance) || range->source_visible != 1U)) {
      ++verifier.explicit_unknown_missing_detail_count;
    }
    if (range->contains_instruction && !restored_source_role_allows_instruction(range->role, range->status)) {
      ++verifier.invalid_instruction_ownership_count;
    }
    if (end > cursor) cursor = end;
  }
  if (payload_size > cursor) ++verifier.gap_count;
  verifier.ok = verifier.gap_count == 0U && verifier.overlap_count == 0U &&
    verifier.invalid_instruction_ownership_count == 0U &&
    verifier.explicit_unknown_missing_detail_count == 0U;
  *out_verifier = verifier;
  return 0;
}
