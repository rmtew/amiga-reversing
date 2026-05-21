#ifndef PLATFORM_MACOS_RESOURCE_H
#define PLATFORM_MACOS_RESOURCE_H

#include <stddef.h>
#include <stdint.h>

#define PLATFORM_MACOS_RESOURCE_TYPE_SIZE 5U

typedef enum PlatformMacosCodeResourceKind {
  PLATFORM_MACOS_CODE_RESOURCE_NONE = 0,
  PLATFORM_MACOS_CODE_RESOURCE_JUMP_TABLE_SEGMENT = 1,
  PLATFORM_MACOS_CODE_RESOURCE_CODE_SEGMENT = 2
} PlatformMacosCodeResourceKind;

typedef struct PlatformMacosResourceForkHeader {
  uint32_t resource_data_offset;
  uint32_t resource_map_offset;
  uint32_t resource_data_length;
  uint32_t resource_map_length;
} PlatformMacosResourceForkHeader;

typedef struct PlatformMacosCodeMetadata {
  uint8_t kind;
  uint32_t above_a5_size;
  uint32_t below_a5_size;
  uint32_t jump_table_length;
  uint32_t jump_table_offset_from_a5;
  uint16_t first_jump_table_entry_offset;
  uint16_t jump_table_entry_count;
} PlatformMacosCodeMetadata;

typedef struct PlatformMacosResourceTypeInfo {
  char type[PLATFORM_MACOS_RESOURCE_TYPE_SIZE];
  uint16_t count;
} PlatformMacosResourceTypeInfo;

typedef struct PlatformMacosResourceInfo {
  char type[PLATFORM_MACOS_RESOURCE_TYPE_SIZE];
  int16_t resource_id;
  int16_t name_offset;
  uint8_t attributes;
  uint32_t data_offset;
  uint32_t payload_offset;
  uint32_t payload_size;
  PlatformMacosCodeMetadata code;
} PlatformMacosResourceInfo;

typedef struct PlatformMacosResourceFork {
  PlatformMacosResourceForkHeader header;
  uint32_t type_list_offset;
  uint32_t name_list_offset;
  size_t type_count;
  size_t resource_count;
} PlatformMacosResourceFork;

int platform_macos_resource_fork_parse(const unsigned char *data, size_t size,
  PlatformMacosResourceFork *out_fork, PlatformMacosResourceTypeInfo *types,
  size_t type_capacity, PlatformMacosResourceInfo *resources,
  size_t resource_capacity);
int platform_macos_resource_fork_find_payload(const unsigned char *data,
  size_t size, const char *resource_type, int16_t resource_id,
  uint32_t *out_payload_offset, uint32_t *out_payload_size);

#endif
