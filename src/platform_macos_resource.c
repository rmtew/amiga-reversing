#include "platform_macos_resource.h"

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

static void parse_code_metadata(PlatformMacosResourceInfo *resource, const unsigned char *data) {
  if (resource->type[0] != 'C' || resource->type[1] != 'O' ||
      resource->type[2] != 'D' || resource->type[3] != 'E') {
    return;
  }
  if (resource->resource_id == 0 && resource->payload_size >= 16U) {
    resource->code.kind = PLATFORM_MACOS_CODE_RESOURCE_JUMP_TABLE_SEGMENT;
    resource->code.above_a5_size = read_u32be_at(data, resource->payload_offset);
    resource->code.below_a5_size = read_u32be_at(data, resource->payload_offset + 4U);
    resource->code.jump_table_length = read_u32be_at(data, resource->payload_offset + 8U);
    resource->code.jump_table_offset_from_a5 = read_u32be_at(data, resource->payload_offset + 12U);
    return;
  }
  resource->code.kind = PLATFORM_MACOS_CODE_RESOURCE_CODE_SEGMENT;
  if (resource->payload_size >= 4U) {
    resource->code.first_jump_table_entry_offset = read_u16be_at(data, resource->payload_offset);
    resource->code.jump_table_entry_count = read_u16be_at(data, resource->payload_offset + 2U);
  }
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
