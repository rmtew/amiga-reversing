#ifndef PLATFORM_COMMON_H
#define PLATFORM_COMMON_H

#include <stdint.h>
#include <stddef.h>

#include "generated/amiga_os_runtime.h"

struct M68kDecodeSectionIR;
struct M68kInstructionIR;
struct M68kAddressObservationIR;

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
int platform_amiga_format_hardware_register_field_symbol(const AmigaOsHardwareRegisterFieldInfo *hardware_field,
  int include_hardware_base, char *buf, size_t buf_size);
int platform_amiga_format_hardware_register_range_symbol(const AmigaOsHardwareRegisterRangeInfo *hardware_range,
  uint32_t offset, int include_hardware_base, char *buf, size_t buf_size);
int amiga_value_domain_symbolic_expr(const char *domain_name, uint32_t value, char *expr, size_t expr_size);
int platform_amiga_hardware_register_custom_immediate_expr(
  const AmigaOsHardwareRegisterInfo *hardware_register, uint32_t value, int use_bit_domain,
  char *expr, size_t expr_size);
int platform_instruction_has_normal_fallthrough(const struct M68kInstructionIR *instruction);
int platform_instruction_has_terminal_state_flow(const struct M68kInstructionIR *instruction);
void platform_format_runtime_address_symbol_name(const char *role, uint32_t address, const char *suffix,
  char *buf, size_t buf_size);

typedef enum PlatformResolvedIndirectKind {
  PLATFORM_RESOLVED_INDIRECT_NONE = 0,
  PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL = 1,
  PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH = 2,
  PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL = 3
} PlatformResolvedIndirectKind;

typedef enum PlatformFactsV2RelocationAnchorKind {
  PLATFORM_FACTS_V2_RELOCATION_ANCHOR_NONE = 0,
  PLATFORM_FACTS_V2_RELOCATION_ANCHOR_POSITIVE = 1,
  PLATFORM_FACTS_V2_RELOCATION_ANCHOR_NEGATIVE = 2
} PlatformFactsV2RelocationAnchorKind;

typedef enum PlatformFactsV2ImageOffsetTargetKind {
  PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_NONE = 0,
  PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_CODE = 1,
  PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_DATA = 2,
  PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_BSS = 3
} PlatformFactsV2ImageOffsetTargetKind;

typedef enum PlatformFactsV2DisplaySetupRegisterKind {
  PLATFORM_FACTS_V2_DISPLAY_SETUP_REGISTER_NONE = 0,
  PLATFORM_FACTS_V2_DISPLAY_SETUP_REGISTER_BPLCON0 = 1,
  PLATFORM_FACTS_V2_DISPLAY_SETUP_REGISTER_DIWSTRT = 2,
  PLATFORM_FACTS_V2_DISPLAY_SETUP_REGISTER_DIWSTOP = 3,
  PLATFORM_FACTS_V2_DISPLAY_SETUP_REGISTER_DDFSTRT = 4,
  PLATFORM_FACTS_V2_DISPLAY_SETUP_REGISTER_DDFSTOP = 5,
  PLATFORM_FACTS_V2_DISPLAY_SETUP_REGISTER_BPL1MOD = 6,
  PLATFORM_FACTS_V2_DISPLAY_SETUP_REGISTER_BPL2MOD = 7
} PlatformFactsV2DisplaySetupRegisterKind;

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
int platform_facts_v2_resolve_opcode_call(uint8_t platform_kind, uint16_t opcode,
  PlatformFactsV2ResolvedCall *out_info);
int platform_facts_v2_resolve_stack_cleanup_call(uint8_t platform_kind,
  const struct M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t block_start,
  uint32_t cleanup_offset, const struct M68kInstructionIR *cleanup_instruction,
  PlatformFactsV2ResolvedCall *out_info);
int platform_facts_v2_is_callback_vector_slot(uint8_t platform_kind, uint32_t address);
int platform_facts_v2_is_runtime_address_sink(uint8_t platform_kind, uint32_t address);
uint16_t platform_facts_v2_runtime_address_sink_kind(uint8_t platform_kind, uint32_t address);
const char *platform_facts_v2_runtime_address_sink_data_class(uint8_t platform_kind, uint32_t address);
uint32_t platform_facts_v2_runtime_address_sink_data_class_flags(uint8_t platform_kind, uint32_t address);
uint16_t platform_facts_v2_hardware_base_offset_runtime_address_sink_kind(uint8_t platform_kind,
  uint16_t base_id, uint32_t offset);
int platform_facts_v2_hardware_base_offset_runtime_address_sink_anchor_offset(uint8_t platform_kind,
  uint16_t base_id, uint32_t offset, uint32_t *out_anchor_offset);
const char *platform_facts_v2_hardware_base_offset_runtime_address_sink_data_class(uint8_t platform_kind,
  uint16_t base_id, uint32_t offset);
uint32_t platform_facts_v2_hardware_base_offset_runtime_address_sink_data_class_flags(uint8_t platform_kind,
  uint16_t base_id, uint32_t offset);
int platform_facts_v2_runtime_sound_sample_length_register_matches_sink_address(uint8_t platform_kind,
  uint32_t sink_address, uint32_t length_register_address);
int platform_facts_v2_is_audio_length_register(uint8_t platform_kind, uint32_t address);
int platform_facts_v2_is_audio_period_register(uint8_t platform_kind, uint32_t address);
uint16_t platform_facts_v2_runtime_address_storage_sink_kind(uint8_t platform_kind,
  const uint8_t *data, uint32_t size, uint32_t value_offset);
const char *platform_facts_v2_runtime_address_storage_sink_data_class(uint8_t platform_kind,
  const uint8_t *data, uint32_t size, uint32_t value_offset);
uint32_t platform_facts_v2_runtime_address_storage_sink_data_class_flags(uint8_t platform_kind,
  const uint8_t *data, uint32_t size, uint32_t value_offset);
int platform_facts_v2_absolute_memory_owner(uint8_t platform_kind, uint32_t address,
  uint8_t *out_owner_kind, uint32_t *out_owner_offset);
int platform_facts_v2_absolute_memory_owner_stays_literal(uint8_t platform_kind, uint32_t address);
int platform_facts_v2_address_has_hardware_owner(uint8_t platform_kind, uint32_t address);
int platform_facts_v2_address_has_symbolic_owner(uint8_t platform_kind, uint32_t address);
uint8_t platform_facts_v2_address_use_shape_from_observation(uint8_t platform_kind,
  const struct M68kAddressObservationIR *observation);
const char *platform_facts_v2_address_use_symbol_from_observation(uint8_t platform_kind,
  const struct M68kAddressObservationIR *observation, uint8_t shape, char *symbol_buf, size_t symbol_buf_size);
int platform_facts_v2_hardware_base_offset_known(uint8_t platform_kind, uint16_t base_id, uint32_t offset);
const char *platform_facts_v2_hardware_base_offset_symbol(uint8_t platform_kind, uint16_t base_id,
  uint32_t offset, char *symbol_buf, size_t symbol_buf_size);
int platform_facts_v2_hardware_base_offset_immediate_expr(uint8_t platform_kind, uint16_t base_id,
  uint32_t offset, uint32_t value, int use_bit_domain, char *expr, size_t expr_size);
int platform_facts_v2_hardware_base_offset_value_expr(uint8_t platform_kind, uint16_t base_id,
  uint32_t offset, uint32_t value, char *expr, size_t expr_size);
int platform_facts_v2_value_domain_symbolic_expr(uint8_t platform_kind, const char *domain_name,
  uint32_t value, char *expr, size_t expr_size);
const char *platform_facts_v2_hardware_base_symbol(uint8_t platform_kind, uint16_t base_id);
const char *platform_facts_v2_hardware_base_symbol_for_address(uint8_t platform_kind, uint32_t address);
int platform_facts_v2_hardware_base_address(uint8_t platform_kind, uint16_t base_id, uint32_t *out_address);
int platform_facts_v2_hardware_base_id_for_symbol(uint8_t platform_kind, const char *symbol_name,
  uint16_t *out_base_id);
int platform_facts_v2_hardware_base_id_for_address(uint8_t platform_kind, uint32_t address, uint16_t *out_base_id);
int platform_facts_v2_hardware_base_offset_for_address(uint8_t platform_kind, uint32_t address,
  uint16_t *out_base_id, uint32_t *out_offset);
int platform_facts_v2_palette_color_register_range_offset_for_address(uint8_t platform_kind, uint32_t address,
  uint32_t *out_range_offset);
int platform_facts_v2_hardware_access_note_for_address(uint8_t platform_kind, uint32_t address,
  uint8_t access_kind, uint32_t byte_width, uint8_t has_immediate_value, uint32_t value,
  uint8_t *out_semantic_use_kind, char *buf, size_t buf_size);
int platform_facts_v2_hardware_base_offset_access_note(uint8_t platform_kind, uint16_t base_id, uint32_t offset,
  uint8_t access_kind, uint32_t byte_width, uint8_t has_immediate_value, uint32_t value,
  uint8_t *out_semantic_use_kind, char *buf, size_t buf_size);
int platform_facts_v2_display_setup_register_for_address(uint8_t platform_kind, uint32_t address,
  uint8_t *out_register_kind);
uint32_t platform_facts_v2_relocation_anchor_kind(uint8_t platform_kind, uint8_t platform_file_kind,
  uint8_t fixup_kind, uint32_t width, uint32_t raw_value);
int platform_facts_v2_fixup_addend_is_normalized_target(uint8_t platform_kind, uint8_t platform_file_kind,
  uint8_t fixup_kind, uint8_t has_target_section, int64_t addend, uint32_t width, uint32_t target_extent,
  uint32_t *out_offset);
int platform_facts_v2_image_offset_target(uint8_t platform_kind, uint8_t platform_file_kind, uint8_t fixup_kind,
  uint32_t width, uint32_t raw_value, uint32_t code_size, uint32_t data_size, uint8_t has_bss, uint32_t bss_size,
  uint8_t *out_target_kind, uint32_t *out_offset);
int platform_facts_v2_supports_linkage_api_entry_labels(uint8_t platform_kind);
int platform_facts_v2_lvo_is_api(uint8_t platform_kind, int16_t lvo);
int platform_facts_v2_pc_relative_section_anchor_for_target(uint8_t platform_kind, int64_t target,
  uint32_t *out_base_offset, int32_t *out_addend, uint8_t *out_symbol_provenance);
int platform_facts_v2_supports_loadseg_segment_chain(uint8_t platform_kind);
int platform_facts_v2_loadseg_segment_body_for_hops(uint8_t platform_kind, size_t section_count,
  size_t anchor_section_index, uint32_t link_hops, size_t *out_section_index);

#endif
