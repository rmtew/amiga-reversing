#ifndef PLATFORM_MACOS_RESOURCE_H
#define PLATFORM_MACOS_RESOURCE_H

#include <stddef.h>
#include <stdint.h>

#define PLATFORM_MACOS_RESOURCE_TYPE_SIZE 5U
#define PLATFORM_MACOS_CODE_LAYOUT_RANGE_CAPACITY 8U

typedef enum PlatformMacosCodeResourceKind {
  PLATFORM_MACOS_CODE_RESOURCE_NONE = 0,
  PLATFORM_MACOS_CODE_RESOURCE_JUMP_TABLE_SEGMENT = 1,
  PLATFORM_MACOS_CODE_RESOURCE_CODE_SEGMENT = 2
} PlatformMacosCodeResourceKind;

typedef enum PlatformMacosCodeRangeKind {
  PLATFORM_MACOS_CODE_RANGE_NONE = 0,
  PLATFORM_MACOS_CODE_RANGE_METADATA = 1,
  PLATFORM_MACOS_CODE_RANGE_DATA = 2,
  PLATFORM_MACOS_CODE_RANGE_CANDIDATE_CODE = 3,
  PLATFORM_MACOS_CODE_RANGE_CONFIRMED_CODE = 4,
  PLATFORM_MACOS_CODE_RANGE_DEFERRED = 5,
  PLATFORM_MACOS_CODE_RANGE_CANDIDATE_UNRESOLVED_PREFIX = 6
} PlatformMacosCodeRangeKind;

typedef enum PlatformMacosCodeRangeEvidence {
  PLATFORM_MACOS_CODE_EVIDENCE_NONE = 0,
  PLATFORM_MACOS_CODE_EVIDENCE_CODE0_JUMP_TABLE_METADATA = 1,
  PLATFORM_MACOS_CODE_EVIDENCE_NONZERO_SEGMENT_HEADER = 2,
  PLATFORM_MACOS_CODE_EVIDENCE_PREFIX_BEFORE_STACK_ENTRY = 3,
  PLATFORM_MACOS_CODE_EVIDENCE_FAR_MODEL_SEGMENT_HEADER = 4,
  PLATFORM_MACOS_CODE_EVIDENCE_M68K_STACK_ENTRY_TO_A0 = 5,
  PLATFORM_MACOS_CODE_EVIDENCE_MISSING_STACK_ENTRY = 6
} PlatformMacosCodeRangeEvidence;

typedef struct PlatformMacosCodeRange {
  uint8_t kind;
  uint8_t evidence;
  uint8_t entrypoint;
  uint32_t start_offset;
  uint32_t size;
} PlatformMacosCodeRange;

typedef struct PlatformMacosRestoredSourceRangeView {
  const char *role;
  uint32_t start;
  uint32_t size;
  uint32_t end;
  const char *status;
  const char *reason;
  const char *provenance;
  uint8_t source_visible;
  uint8_t contains_instruction;
} PlatformMacosRestoredSourceRangeView;

typedef struct PlatformMacosRestoredSourceCoverageVerifier {
  uint8_t ok;
  uint32_t gap_count;
  uint32_t overlap_count;
  uint32_t invalid_instruction_ownership_count;
  uint32_t explicit_unknown_missing_detail_count;
} PlatformMacosRestoredSourceCoverageVerifier;

typedef enum PlatformMacosSegmentLoaderFixupInventoryStatus {
  PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_ABSENT = 0,
  PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_PARSEABLE = 1,
  PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_UNSUPPORTED = 2,
  PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_CUSTOM_UNKNOWN = 3,
  PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_MALFORMED = 4
} PlatformMacosSegmentLoaderFixupInventoryStatus;

typedef struct PlatformMacosSegmentLoaderFixupInventory {
  uint8_t status;
  uint8_t source_visible;
  uint8_t encoding_byte_provenance_known;
  uint32_t source_offset;
  uint32_t size;
  uint32_t end;
  const char *reason;
  const char *provenance;
} PlatformMacosSegmentLoaderFixupInventory;

typedef enum PlatformMacosSegmentLoaderFixupInventoryAggregateStatus {
  PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_AGGREGATE_BLOCKED = 0,
  PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_AGGREGATE_PARSEABLE = 1,
  PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_AGGREGATE_MALFORMED = 2
} PlatformMacosSegmentLoaderFixupInventoryAggregateStatus;

typedef struct PlatformMacosSegmentLoaderFixupInventoryAggregate {
  uint8_t status;
  uint32_t absent_count;
  uint32_t parseable_count;
  uint32_t unsupported_count;
  uint32_t custom_unknown_count;
  uint32_t malformed_count;
  const char *summary;
} PlatformMacosSegmentLoaderFixupInventoryAggregate;

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
  uint8_t far_model;
  uint32_t near_entry_start_a5_offset;
  uint32_t near_entry_count;
  uint32_t far_entry_start_a5_offset;
  uint32_t far_entry_count;
  uint32_t a5_relocation_info_offset;
  uint32_t current_a5_value;
  uint32_t segment_relocation_info_offset;
  uint32_t segment_load_address;
  size_t layout_range_count;
  PlatformMacosCodeRange layout_ranges[PLATFORM_MACOS_CODE_LAYOUT_RANGE_CAPACITY];
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
int platform_macos_code_metadata_parse(const unsigned char *payload, uint32_t payload_size,
  int16_t resource_id, PlatformMacosCodeMetadata *out_code);
int platform_macos_code_metadata_executable_range(const PlatformMacosCodeMetadata *code,
  uint32_t *out_start_offset, uint32_t *out_size);
int platform_macos_segment_loader_fixup_inventory_from_code_metadata(const PlatformMacosCodeMetadata *code,
  int16_t resource_id, uint32_t payload_size, PlatformMacosSegmentLoaderFixupInventory *out_inventory);
const char *platform_macos_segment_loader_fixup_inventory_status_name(uint8_t status);
int platform_macos_segment_loader_fixup_inventory_aggregate_counts(const uint32_t *counts, size_t count_capacity,
  PlatformMacosSegmentLoaderFixupInventoryAggregate *out_aggregate);
const char *platform_macos_segment_loader_fixup_inventory_aggregate_status_name(uint8_t status);
const char *platform_macos_code_range_kind_name(uint8_t kind);
const char *platform_macos_code_range_evidence_name(uint8_t evidence);
const char *platform_macos_code_range_fact_id(uint8_t evidence);
const char *platform_macos_code_range_fact_status(uint8_t evidence);
const char *platform_macos_code_range_parser_use(uint8_t evidence);
int platform_macos_restored_source_verify_ranges(const PlatformMacosRestoredSourceRangeView *ranges,
  size_t range_count, uint32_t payload_size, PlatformMacosRestoredSourceCoverageVerifier *out_verifier);

#endif
