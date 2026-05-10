#ifndef PLATFORM_COMMON_H
#define PLATFORM_COMMON_H

#include <stdint.h>
#include <stddef.h>

struct M68kDecodeSectionIR;
struct M68kInstructionIR;

static inline uint16_t m68k_read_u16be(const uint8_t *data) {
  return (uint16_t)(((uint16_t)data[0] << 8) | (uint16_t)data[1]);
}

static inline uint32_t m68k_read_u32be(const uint8_t *data) {
  return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

char *m68k_platform_dup_string(const char *text);
int m68k_platform_join_path(const char *base, const char *name, char **out_path);
int m68k_platform_sha256_hex(const unsigned char *data, size_t size, char out_hex[65]);
int platform_amiga_format_global_base_slot_label(size_t section_index, char width_suffix, const char *base_name,
  char *buf, size_t buf_size);
int platform_amiga_format_app_base_slot_name(const char *base_name, char *buf, size_t buf_size);

typedef enum PlatformResolvedIndirectKind {
  PLATFORM_RESOLVED_INDIRECT_NONE = 0,
  PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL = 1,
  PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH = 2,
  PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL = 3
} PlatformResolvedIndirectKind;

typedef struct PlatformFactsV2ResolvedCall {
  uint8_t platform_kind;
  uint8_t kind;
  uint8_t note_kind;
  uint8_t note_stack_cleanup_known;
  uint8_t note_return_kind;
  uint16_t note_stack_cleanup_bytes;
  char note_base_name[64];
  char note_symbol_name[64];
} PlatformFactsV2ResolvedCall;

void platform_facts_v2_resolved_call_init(PlatformFactsV2ResolvedCall *info);
int platform_facts_v2_resolve_trap_call(uint8_t platform_kind,
  const struct M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t block_start,
  uint32_t trap_offset, PlatformFactsV2ResolvedCall *out_info);
int platform_facts_v2_resolve_stack_cleanup_call(uint8_t platform_kind,
  const struct M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t block_start,
  uint32_t cleanup_offset, const struct M68kInstructionIR *cleanup_instruction,
  PlatformFactsV2ResolvedCall *out_info);
int platform_facts_v2_is_callback_vector_slot(uint8_t platform_kind, uint32_t address);
int platform_facts_v2_is_runtime_address_sink(uint8_t platform_kind, uint32_t address);
uint16_t platform_facts_v2_runtime_address_sink_kind(uint8_t platform_kind, uint32_t address);
const char *platform_facts_v2_runtime_address_sink_data_class(uint8_t platform_kind, uint32_t address);
uint32_t platform_facts_v2_runtime_address_sink_data_class_flags(uint8_t platform_kind, uint32_t address);
uint16_t platform_facts_v2_runtime_address_storage_sink_kind(uint8_t platform_kind,
  const uint8_t *data, uint32_t size, uint32_t value_offset);
const char *platform_facts_v2_runtime_address_storage_sink_data_class(uint8_t platform_kind,
  const uint8_t *data, uint32_t size, uint32_t value_offset);
uint32_t platform_facts_v2_runtime_address_storage_sink_data_class_flags(uint8_t platform_kind,
  const uint8_t *data, uint32_t size, uint32_t value_offset);
int platform_facts_v2_pc_relative_section_anchor_for_target(uint8_t platform_kind, int64_t target,
  uint32_t *out_base_offset, int32_t *out_addend);
int platform_facts_v2_supports_loadseg_segment_chain(uint8_t platform_kind);
int platform_facts_v2_loadseg_segment_body_for_hops(uint8_t platform_kind, size_t section_count,
  size_t anchor_section_index, uint32_t link_hops, size_t *out_section_index);

#endif
