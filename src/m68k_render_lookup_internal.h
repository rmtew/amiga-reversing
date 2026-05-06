#ifndef M68K_RENDER_LOOKUP_INTERNAL_H
#define M68K_RENDER_LOOKUP_INTERNAL_H

#include "m68k_render_ir.h"

#include "m68k_assembler.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_simulator.h"
#include "m68k_source_pipeline.h"
#include "m68k_source_text_util.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "generated/amiga_hunk_file_runtime.h"
#include "generated/m68k_cpu_runtime.h"
#include "generated/amiga_os_runtime.h"

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef struct M68kRenderLookup M68kRenderLookup;

typedef struct M68kRenderPlatformLocalBaseSlot {
  uint8_t valid;
  uint8_t base_reg;
  int16_t displacement;
  char library_name[64];
} M68kRenderPlatformLocalBaseSlot;

typedef struct M68kRenderPlatformState {
  uint8_t data_base_known[8];
  char data_base_library[8][64];
  uint8_t address_base_known[8];
  char address_base_library[8][64];
  uint8_t address_hardware_base_known[8];
  char address_hardware_base_symbol[8][64];
  uint8_t data_app_base_known[8];
  uint8_t address_app_base_known[8];
  uint8_t d0_lvo_known;
  int16_t d0_lvo;
  M68kRenderPlatformLocalBaseSlot local_base_slots[32];
} M68kRenderPlatformState;

typedef struct M68kRenderGlobalBaseSlot {
  size_t section_index;
  uint32_t offset;
  size_t source_section_index;
  uint32_t source_offset;
  uint8_t has_source;
  char library_name[64];
} M68kRenderGlobalBaseSlot;

typedef struct M68kRenderGlobalBaseObservation {
  size_t section_index;
  uint32_t offset;
  int16_t lvos[32];
  size_t lvo_count;
} M68kRenderGlobalBaseObservation;

typedef struct M68kRenderBaseFieldSlot {
  char owner_name[64];
  int16_t displacement;
  size_t source_section_index;
  uint32_t source_offset;
  uint8_t has_source;
  char library_name[64];
  char symbol_name[64];
  uint8_t value_kind;
  uint8_t conflicted;
} M68kRenderBaseFieldSlot;

#define M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE 0U
#define M68K_RENDER_BASE_FIELD_SLOT_IOREQUEST 1U
#define M68K_RENDER_BASE_FIELD_SLOT_NAMED_VALUE 2U
#define M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS 3U
#define M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE 4U

typedef struct M68kRenderIndexedVectorWrapper {
  size_t section_index;
  uint32_t offset;
  char library_name[64];
} M68kRenderIndexedVectorWrapper;

typedef struct M68kRenderRecoveredFunctionArg {
  size_t section_index;
  uint32_t function_offset;
  uint16_t stack_offset;
  uint8_t reg_kind;
  uint8_t reg_index;
  const AmigaOsCallInputInfo *input;
} M68kRenderRecoveredFunctionArg;

typedef struct M68kRenderRecoveredLocalCallSummary {
  size_t section_index;
  uint32_t target_offset;
  const AmigaOsLibraryVectorInfo *vector;
} M68kRenderRecoveredLocalCallSummary;

typedef struct M68kRenderTypedSlotEffect {
  size_t section_index;
  uint32_t offset;
  int16_t displacement;
  const AmigaOsCallOutputInfo *output;
} M68kRenderTypedSlotEffect;

typedef struct M68kRenderAppSlotRef {
  size_t section_index;
  M68kAppSlotRefIR ref;
} M68kRenderAppSlotRef;

typedef struct M68kRenderDeviceInstance {
  int16_t iorequest_displacement;
  uint8_t conflicted;
  char device_name[64];
} M68kRenderDeviceInstance;

typedef struct M68kRenderDeviceCall {
  size_t section_index;
  uint32_t offset;
  char device_name[64];
} M68kRenderDeviceCall;

typedef struct M68kRenderRuntimeAddressRef {
  const M68kFact *fact;
} M68kRenderRuntimeAddressRef;

typedef struct M68kRenderRuntimeAddressRefIndex {
  const M68kFact *operand_refs[M68K_DECODE_IR_MAX_OPERANDS];
  const M68kFact *external_ref;
} M68kRenderRuntimeAddressRefIndex;

typedef struct M68kRenderInferredRuntimeAddressRef {
  size_t section_index;
  M68kRuntimeAddressRefIR ref;
  char data_class[64];
} M68kRenderInferredRuntimeAddressRef;

typedef struct M68kRenderRuntimeAddressRange {
  const M68kFact *fact;
} M68kRenderRuntimeAddressRange;

typedef struct M68kRenderCodeStartRef {
  const M68kFact *fact;
} M68kRenderCodeStartRef;

typedef struct M68kRenderViolationRef {
  const M68kFact *fact;
} M68kRenderViolationRef;

typedef struct M68kRenderXref {
  size_t section_index;
  uint32_t offset;
  size_t target_section_index;
  uint32_t target_offset;
} M68kRenderXref;

enum {
  M68K_RENDER_TYPED_ORIGIN_NONE = 0,
  M68K_RENDER_TYPED_ORIGIN_STACK_SLOT = 1,
  M68K_RENDER_TYPED_ORIGIN_BASE_SLOT = 2,
  M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE = 3
};

enum {
  M68K_RENDER_TYPED_PROVENANCE_NONE = 0,
  M68K_RENDER_TYPED_PROVENANCE_API_OUTPUT = 1,
  M68K_RENDER_TYPED_PROVENANCE_REGISTER_COPY = 2,
  M68K_RENDER_TYPED_PROVENANCE_STACK_SLOT = 3,
  M68K_RENDER_TYPED_PROVENANCE_BASE_SLOT = 4,
  M68K_RENDER_TYPED_PROVENANCE_LOOKUP_STORAGE = 5,
  M68K_RENDER_TYPED_PROVENANCE_APP_SLOT = 6,
  M68K_RENDER_TYPED_PROVENANCE_FIELD_POINTER = 7,
  M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT = 8,
  M68K_RENDER_TYPED_PROVENANCE_FIELD_ADDRESS = 9
};

typedef struct M68kRenderTypedStorageOrigin {
  uint8_t kind;
  uint8_t storage_kind;
  uint8_t base_reg;
  size_t section_index;
  int32_t displacement;
  uint32_t address;
} M68kRenderTypedStorageOrigin;

typedef struct M68kRenderTypedProvenance {
  uint8_t kind;
  size_t section_index;
  uint32_t offset;
} M68kRenderTypedProvenance;

typedef struct M68kRenderTypedRegValue {
  uint8_t known;
  const AmigaOsCallOutputInfo *output;
  uint16_t struct_id;
  M68kRenderTypedStorageOrigin origin;
  M68kRenderTypedProvenance provenance;
} M68kRenderTypedRegValue;

typedef struct M68kRenderTypedStoredValue {
  uint8_t known;
  const AmigaOsCallOutputInfo *output;
  uint16_t struct_id;
  uint8_t app_address_known;
  int16_t app_displacement;
  M68kRenderTypedProvenance provenance;
} M68kRenderTypedStoredValue;

typedef struct M68kRenderTypedAppAddressValue {
  uint8_t known;
  int16_t displacement;
} M68kRenderTypedAppAddressValue;

typedef struct M68kRenderTypedMemoryBaseValue {
  uint8_t known;
  size_t section_index;
  uint32_t offset;
} M68kRenderTypedMemoryBaseValue;

typedef struct M68kRenderTypedStackSlot {
  uint8_t known;
  int16_t displacement;
  M68kRenderTypedStoredValue value;
} M68kRenderTypedStackSlot;

typedef struct M68kRenderTypedBaseSlot {
  uint8_t known;
  uint8_t base_reg;
  int16_t displacement;
  M68kRenderTypedStoredValue value;
} M68kRenderTypedBaseSlot;

#define M68K_RENDER_TYPED_STACK_SLOT_LIMIT 32U
#define M68K_RENDER_TYPED_BASE_SLOT_LIMIT 32U

typedef struct M68kRenderTypedState {
  M68kRenderTypedRegValue data_regs[8];
  M68kRenderTypedRegValue addr_regs[8];
  M68kRenderTypedAppAddressValue data_app_addr_regs[8];
  M68kRenderTypedAppAddressValue app_addr_regs[8];
  M68kRenderTypedMemoryBaseValue data_memory_base_regs[8];
  M68kRenderTypedMemoryBaseValue memory_base_regs[8];
  M68kRenderTypedStackSlot stack_slots[M68K_RENDER_TYPED_STACK_SLOT_LIMIT];
  size_t stack_slot_count;
  M68kRenderTypedBaseSlot base_slots[M68K_RENDER_TYPED_BASE_SLOT_LIMIT];
  size_t base_slot_count;
} M68kRenderTypedState;

typedef struct M68kRenderTypedFlowNode {
  const M68kDecodeCandidate *candidate;
  M68kRenderTypedState typed_in;
  M68kRenderTypedState typed_out;
  M68kRenderPlatformState platform_in;
  M68kRenderPlatformState platform_out;
  size_t successors[5];
  uint8_t successor_count;
  uint8_t is_root;
  uint8_t has_in;
} M68kRenderTypedFlowNode;

typedef struct M68kRenderTypedAccess {
  size_t section_index;
  uint32_t offset;
  uint8_t operand_index;
  uint8_t base_reg;
  int16_t displacement;
  int16_t field_offset;
  uint8_t inherited;
  uint8_t nested;
  M68kRenderTypedProvenance provenance;
  char root_struct_name[64];
  char owner_struct_name[64];
  char field_name[64];
  char field_expr[96];
} M68kRenderTypedAccess;

typedef struct M68kRenderUnresolvedTypedAccess {
  size_t section_index;
  uint32_t offset;
  uint8_t operand_index;
  uint8_t base_reg;
  int16_t displacement;
  uint16_t struct_size;
  uint8_t classification;
  uint16_t container_candidate_count;
  uint8_t refinement_applied;
  M68kRenderTypedProvenance provenance;
  char root_struct_name[64];
  char container_struct_name[64];
  char container_field_expr[96];
  char refined_struct_name[64];
} M68kRenderUnresolvedTypedAccess;

typedef struct M68kRenderTypedAppSlot {
  int16_t displacement;
  uint16_t struct_id;
  uint8_t conflicted;
  uint8_t inline_region;
  size_t source_section_index;
  uint32_t source_offset;
} M68kRenderTypedAppSlot;

enum {
  M68K_RENDER_TYPED_STORAGE_APP_SLOT = 1,
  M68K_RENDER_TYPED_STORAGE_ABSOLUTE = 2,
  M68K_RENDER_TYPED_STORAGE_BASE_SLOT = 3
};

typedef struct M68kRenderTypedStorageSlot {
  uint8_t kind;
  uint8_t conflicted;
  size_t section_index;
  int32_t displacement;
  uint32_t address;
  size_t source_section_index;
  uint32_t source_offset;
  M68kRenderTypedStoredValue value;
} M68kRenderTypedStorageSlot;

typedef struct M68kRenderDataPointerValue {
  uint8_t known;
  uint8_t exact;
  uint8_t dynamic_offset_known;
  size_t section_index;
  uint32_t offset;
  size_t dynamic_offset_section_index;
  uint32_t dynamic_offset_offset;
} M68kRenderDataPointerValue;

typedef struct M68kRenderDataPointerState {
  M68kRenderDataPointerValue data_regs[8];
  M68kRenderDataPointerValue addr_regs[8];
} M68kRenderDataPointerState;

typedef struct M68kRenderStringSpan {
  size_t section_index;
  uint32_t offset;
  uint32_t size;
} M68kRenderStringSpan;

typedef struct M68kRenderInstructionComment {
  size_t section_index;
  uint32_t offset;
  char comment[384];
} M68kRenderInstructionComment;

typedef struct M68kRenderTraceRegName {
  uint8_t known;
  char name[64];
} M68kRenderTraceRegName;

typedef struct M68kRenderTraceLocalSlot {
  uint8_t valid;
  uint8_t base_reg;
  int16_t displacement;
  char library_name[64];
} M68kRenderTraceLocalSlot;

typedef struct M68kRenderTraceAppAddress {
  uint8_t known;
  int16_t displacement;
} M68kRenderTraceAppAddress;

typedef struct M68kRenderBaseTraceState {
  M68kRenderTraceRegName data_regs[8];
  M68kRenderTraceRegName addr_regs[8];
  M68kRenderTraceAppAddress app_addresses[8];
  M68kRenderTraceLocalSlot local_slots[32];
} M68kRenderBaseTraceState;

struct M68kRenderLookup {
  Arena *arena;
  uint8_t **labels;
  const char ***object_symbol_labels;
  const M68kFact ***relocations;
  const M68kFact ***anchors;
  uint8_t **block_starts;
  uint32_t *label_extents;
  uint32_t *object_symbol_label_extents;
  uint32_t *relocation_extents;
  uint32_t *anchor_extents;
  uint32_t *block_start_extents;
  size_t section_count;
  const M68kObject *object;
  const M68kAnalysisPolicy *policy;
  M68kRenderGlobalBaseSlot *global_base_slots;
  size_t global_base_slot_count;
  size_t global_base_slot_capacity;
  M68kRenderBaseFieldSlot *base_field_slots;
  size_t base_field_slot_count;
  size_t base_field_slot_capacity;
  M68kRenderAppSlotRef *app_slot_refs;
  size_t app_slot_ref_count;
  size_t app_slot_ref_capacity;
  M68kRenderDeviceInstance *device_instances;
  size_t device_instance_count;
  size_t device_instance_capacity;
  M68kRenderDeviceCall *device_calls;
  size_t device_call_count;
  size_t device_call_capacity;
  M68kRenderRuntimeAddressRef *runtime_address_refs;
  size_t runtime_address_ref_count;
  size_t runtime_address_ref_capacity;
  M68kRenderRuntimeAddressRefIndex **runtime_address_ref_indices;
  uint32_t *runtime_address_ref_index_extents;
  M68kRenderInferredRuntimeAddressRef *inferred_runtime_address_refs;
  size_t inferred_runtime_address_ref_count;
  size_t inferred_runtime_address_ref_capacity;
  M68kRenderRuntimeAddressRange *runtime_address_ranges;
  size_t runtime_address_range_count;
  size_t runtime_address_range_capacity;
  M68kRenderCodeStartRef *code_start_refs;
  size_t code_start_ref_count;
  size_t code_start_ref_capacity;
  M68kRenderViolationRef *violation_refs;
  size_t violation_ref_count;
  size_t violation_ref_capacity;
  M68kRenderXref *xrefs;
  size_t xref_count;
  size_t xref_capacity;
  M68kRenderIndexedVectorWrapper *indexed_vector_wrappers;
  size_t indexed_vector_wrapper_count;
  size_t indexed_vector_wrapper_capacity;
  M68kRenderRecoveredFunctionArg *recovered_function_args;
  size_t recovered_function_arg_count;
  size_t recovered_function_arg_capacity;
  M68kRenderRecoveredLocalCallSummary *recovered_local_call_summaries;
  size_t recovered_local_call_summary_count;
  size_t recovered_local_call_summary_capacity;
  M68kRenderTypedSlotEffect *typed_slot_effects;
  size_t typed_slot_effect_count;
  size_t typed_slot_effect_capacity;
  M68kRenderTypedAccess *typed_accesses;
  size_t typed_access_count;
  size_t typed_access_capacity;
  M68kRenderUnresolvedTypedAccess *unresolved_typed_accesses;
  size_t unresolved_typed_access_count;
  size_t unresolved_typed_access_capacity;
  M68kRenderTypedAppSlot *typed_app_slots;
  size_t typed_app_slot_count;
  size_t typed_app_slot_capacity;
  M68kRenderTypedStorageSlot *typed_storage_slots;
  size_t typed_storage_slot_count;
  size_t typed_storage_slot_capacity;
  M68kRenderInstructionComment *instruction_comments;
  size_t instruction_comment_count;
  size_t instruction_comment_capacity;
  M68kRenderStringSpan *string_spans;
  size_t string_span_count;
  size_t string_span_capacity;
  M68kAnalysisStructuredDataItem *auto_structured_data_items;
  size_t auto_structured_data_item_count;
  size_t auto_structured_data_item_capacity;
  size_t **instruction_comment_indices;
  uint32_t *instruction_comment_extents;
};

Arena *render_lookup_arena(M68kRenderLookup *lookup);
void *render_lookup_calloc(M68kRenderLookup *lookup, size_t count, size_t size);
void *render_lookup_grow_array(M68kRenderLookup *lookup, const void *old_items, size_t old_count,
  size_t item_size, size_t new_capacity);

void format_numeric_value(char *buffer, size_t buffer_size, uint32_t size, uint32_t value);
uint8_t format_lookup_asm_label_with_generation(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset);
const M68kAnalysisStructuredDataItem *lookup_structured_data_item_at_offset(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset);
const M68kAnalysisStructuredDataItem *lookup_structured_data_item_covering_offset(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset);
int structured_data_item_comment(const M68kAnalysisStructuredDataItem *item, char *comment,
    size_t comment_size);
int structured_data_item_render_comment(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *comment, size_t comment_size);
int structured_data_item_symbolic_operand_expr(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *expr, size_t expr_size);
int amiga_value_domain_symbolic_expr(const char *domain_name, uint32_t value, char *expr,
    size_t expr_size);
int amiga_hardware_register_custom_immediate_expr(const AmigaOsHardwareRegisterInfo *hardware_register,
  uint32_t value, int use_bit_domain, char *expr, size_t expr_size);
int format_amiga_hardware_register_field_symbol(const AmigaOsHardwareRegisterFieldInfo *hardware_field,
  int include_hardware_base, char *buf, size_t buf_size);
int format_amiga_hardware_register_range_symbol(const AmigaOsHardwareRegisterRangeInfo *hardware_range,
  uint32_t offset, int include_hardware_base, char *buf, size_t buf_size);
void record_asm_source_failure(M68kRenderIRPreview *preview, uint32_t kind, size_t section_index,
    uint32_t offset, uint32_t aux_offset);
void record_numeric_runtime_ref(M68kRenderIRPreview *preview, const M68kFact *fact);
int lookup_offset_is_inside_relocation_payload(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset);
int lookup_has_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
int lookup_has_renderable_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
int lookup_source_runtime_address(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t source_offset, uint32_t *out_runtime_address);
int lookup_source_has_materialized_runtime_address(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t source_offset, uint32_t runtime_address);
int lookup_source_should_render_runtime_label(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t source_offset, uint32_t *out_runtime_address);
int lookup_source_offset_is_materialized_runtime_range_start(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t source_offset);
int lookup_source_logical_address(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t source_offset, uint32_t *out_logical_address);
const char *lookup_global_base_slot_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset);
const char *lookup_base_field_slot_library(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement);
const char *lookup_app_base_field_slot_library(const M68kRenderLookup *lookup, int16_t displacement);
int library_base_can_use_app_extension_slot(const char *owner_name, int16_t displacement);
int lookup_base_field_slot_symbol_name(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, char *symbol_name, size_t symbol_name_size);
int lookup_app_base_field_slot_symbol_name(const M68kRenderLookup *lookup, int16_t displacement,
    char *symbol_name, size_t symbol_name_size);
const char *lookup_indexed_vector_wrapper_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset);
void render_asm_app_extension_rs(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode);
void render_asm_org(M68kRenderIRPreview *preview, uint32_t logical_address);
void render_asm_sync_logical_pc(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
  size_t section_index, uint32_t source_offset, uint32_t *io_logical_pc);
int render_asm_runtime_alias_labels(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
  size_t section_index, uint32_t offset, uint8_t has_primary_runtime, uint32_t primary_runtime_address);
void platform_state_clear_d0_lvo(M68kRenderPlatformState *state);
int platform_state_name_is_app_base(const char *name);
int operand_is_address_displacement_local(const M68kOperandIR *operand, uint8_t *out_reg,
  int16_t *out_displacement);
int operand_is_address_memory_local(const M68kOperandIR *operand, uint8_t *out_reg,
  int16_t *out_displacement);
int operand_is_immediate_value_local(const M68kOperandIR *operand, uint32_t *out_value);
int operand_is_address_register_local(const M68kOperandIR *operand, uint8_t reg_index);
int operand_is_absolute_address_local(const M68kOperandIR *operand, uint32_t address);
int operand_absolute_offset_local(const M68kOperandIR *operand, uint32_t *out_offset);
int operand_is_postinc_a7_local(const M68kOperandIR *operand);
int operand_is_data_register_local(const M68kOperandIR *operand, uint8_t *out_reg);
int operand_address_register_index_local(const M68kOperandIR *operand, uint8_t *out_reg);
uint8_t app_slot_access_kind_from_instruction(const M68kInstructionIR *instruction, size_t operand_index);
int render_state_operand_uses_app_base(const M68kRenderPlatformState *state, uint8_t base_reg,
  int16_t displacement);
int candidate_lea_known_amiga_name_to_address_reg(const M68kRenderLookup *lookup,
  const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate, uint8_t *out_reg, char *out_name,
  size_t out_size);
int reglist_contains_data_register_local(const M68kOperandIR *operand, uint8_t reg_index);
int reglist_contains_address_register_local(const M68kOperandIR *operand, uint8_t reg_index);
int accepted_start_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t offset);
int candidate_direct_target(const M68kDecodeCandidate *candidate, size_t *out_section_index,
  uint32_t *out_target);
int candidate_direct_control_target(const M68kRenderLookup *lookup, size_t source_section_index,
  const M68kDecodeCandidate *candidate, size_t *out_section_index, uint32_t *out_target);
int candidate_direct_same_section_target(const M68kDecodeCandidate *candidate, size_t section_index,
  uint32_t *out_target);
int candidate_terminates_a6_state(const M68kDecodeCandidate *candidate);
int render_lookup_add_indexed_vector_wrapper(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  const char *library_name);
int render_lookup_add_runtime_address_ref(M68kRenderLookup *lookup, const M68kFact *fact);
int render_lookup_add_runtime_address_range(M68kRenderLookup *lookup, const M68kFact *fact);
int render_lookup_add_code_start_ref(M68kRenderLookup *lookup, const M68kFact *fact);
int render_lookup_add_violation_ref(M68kRenderLookup *lookup, const M68kFact *fact);
int render_lookup_add_storage_xref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  size_t target_section_index, uint32_t target_offset);
int render_lookup_add_pc_relative_xrefs(M68kRenderLookup *lookup, const M68kDecodeIR *decode);
uint8_t symbol_ref_kind_for_operand(const M68kOperandIR *operand);
int render_lookup_add_instruction_comment(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  const char *comment);
int render_lookup_add_recovered_function_arg(M68kRenderLookup *lookup, size_t section_index,
  uint32_t function_offset, uint16_t stack_offset, uint8_t reg_kind, uint8_t reg_index,
  const AmigaOsCallInputInfo *input);
int render_lookup_add_recovered_local_call_summary(M68kRenderLookup *lookup, size_t section_index,
  uint32_t target_offset, const AmigaOsLibraryVectorInfo *vector);
int render_lookup_add_typed_slot_effect(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  int16_t displacement, const AmigaOsCallOutputInfo *output);
int render_lookup_add_typed_app_slot(M68kRenderLookup *lookup, int16_t displacement, uint16_t struct_id,
    size_t source_section_index, uint32_t source_offset, int *out_added);
int render_lookup_add_typed_app_slot_region(M68kRenderLookup *lookup, int16_t displacement, uint16_t struct_id,
    size_t source_section_index, uint32_t source_offset, int *out_added);
int render_lookup_add_typed_storage_slot(M68kRenderLookup *lookup, uint8_t kind, size_t section_index,
  int32_t displacement, uint32_t address, const M68kRenderTypedStoredValue *value,
  size_t source_section_index, uint32_t source_offset, int *out_added);
int render_lookup_conflict_typed_storage_slot(M68kRenderLookup *lookup, uint8_t kind, size_t section_index,
  int32_t displacement, uint32_t address, size_t source_section_index, uint32_t source_offset, int *out_added);
int render_lookup_add_typed_access(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t root_struct_id,
    const AmigaOsResolvedStructFieldInfo *field, const char *field_expr,
    const M68kRenderTypedProvenance *provenance);
int render_lookup_add_unresolved_typed_access(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t root_struct_id, uint16_t struct_size,
  uint8_t refinement_applied, uint16_t refined_struct_id, const M68kRenderTypedProvenance *provenance);
const char *render_lookup_device_name_for_call(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset);
int render_lookup_add_string_span(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  uint32_t size);
const char *lookup_instruction_comment(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
const M68kRenderStringSpan *lookup_string_span_at_offset(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset);
int append_comment_part_local(char *comment, size_t comment_size, const char *part);
int render_lookup_infer_amiga_call_input_comments(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
  uint8_t **accepted_start);
const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_vector_at(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t wrapper_offset,
  unsigned depth);
const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector_depth(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
  const M68kDecodeCandidate *candidate, unsigned depth);
const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
  const M68kDecodeCandidate *candidate);
const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector_depth(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
  const M68kDecodeCandidate *candidate, unsigned depth);
const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
  const M68kDecodeCandidate *candidate);
void attach_known_instruction_relocations(const M68kRenderLookup *lookup, size_t section_index,
  const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction);

char ascii_lower_local(char c);
int ascii_char_is_symbol_local(char c, int first);
int asm_symbol_name_is_safe_local(const char *name);
int ascii_contains_case_local(const char *text, const char *needle);
const char *amiga_library_name_from_base_symbol_name(const char *symbol_name);
int amiga_unknown_base_register_owner_name(uint8_t base_reg, char *buf, size_t buf_size);
const AmigaOsCallInputInfo *amiga_vector_input_by_register(const AmigaOsLibraryVectorInfo *vector,
  uint8_t reg_kind, uint8_t reg_index);
const AmigaOsCallInputInfo *amiga_vector_input_by_stack_index(const AmigaOsLibraryVectorInfo *vector,
  size_t stack_index);
const AmigaOsLibraryVectorInfo *attach_amiga_lvo_symbol_if_known(const M68kRenderPlatformState *state,
  M68kInstructionIR *instruction);
const AmigaOsLibraryVectorInfo *attach_amiga_lvo_immediate_if_known(const M68kRenderLookup *lookup,
  const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
  M68kInstructionIR *instruction);
int base_field_slot_is_base_pointer(const M68kRenderBaseFieldSlot *slot);
int byte_is_quoted_string_safe(uint8_t value);
int candidate_calls_a6_lvo(const M68kDecodeCandidate *candidate, int16_t *out_lvo);
int candidate_calls_a6_d0_indexed_vector(const M68kDecodeCandidate *candidate);
int candidate_has_local_helper_summary_fallthrough(const M68kDecodeCandidate *candidate);
int candidate_has_non_call_control_target(const M68kDecodeCandidate *candidate);
int candidate_is_accepted_start(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
  const M68kDecodeCandidate *candidate);
int candidate_loads_d0_lvo_immediate(const M68kDecodeCandidate *candidate, int16_t *out_lvo);
int candidate_loads_relocated_global_slot_to_a6(const M68kRenderLookup *lookup, size_t section_index,
  const M68kDecodeCandidate *candidate, size_t *out_target_section, uint32_t *out_target_offset);
int candidate_writes_a6_unknown(const M68kDecodeCandidate *candidate);
const M68kDecodeCandidate *find_candidate_at_offset_local(const M68kDecodeSectionIR *section, uint32_t offset);
int find_unique_relocation_operand(const M68kDecodeCandidate *candidate, const M68kFact *relocation,
  size_t *out_operand_index);
int instruction_is_local_wrapper_cleanup(const M68kInstructionIR *instruction);
uint16_t lookup_app_base_field_slot_struct_id(const M68kRenderLookup *lookup, int16_t displacement);
uint16_t lookup_base_field_slot_struct_id(const M68kRenderLookup *lookup, const char *owner_name,
  int16_t displacement);
int lookup_has_amiga_resident_library_context(const M68kRenderLookup *lookup);
const M68kFact *lookup_relocation_at(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
void platform_state_apply_policy_register_seeds(M68kRenderPlatformState *state, const M68kAnalysisPolicy *policy,
  size_t section_index, uint32_t offset);
void platform_state_update_d0_lvo_after_instruction(M68kRenderPlatformState *state,
  const M68kInstructionIR *instruction);
void platform_state_update_after_instruction(M68kRenderPlatformState *state, const M68kRenderLookup *lookup,
  const M68kInstructionIR *instruction);
void platform_state_note_call_result_after_instruction(M68kRenderPlatformState *state,
  const M68kInstructionIR *instruction, const AmigaOsLibraryVectorInfo *vector);
uint32_t render_section_extent(const M68kDecodeSectionIR *section);
int render_cfg_candidate_has_fallthrough(const M68kDecodeCandidate *candidate);
int render_lookup_add_indexed_vector_wrapper_branch_aliases(M68kRenderLookup *lookup,
  const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t indexed_entry,
  const char *library_name);
const AmigaOsLibraryVectorInfo *resolve_amiga_indexed_wrapper_call_vector(const M68kRenderLookup *lookup,
  const M68kRenderPlatformState *state, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate);
void attach_operand_label_symbol(const M68kRenderLookup *lookup, M68kInstructionIR *instruction,
  size_t operand_index, size_t source_section_index, uint32_t source_offset, size_t target_section_index,
  uint32_t target_offset);
int m68k_analysis_render_lookup_run_platform_passes(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
  uint8_t **accepted_start, uint8_t **accepted_bytes, M68kRenderIRPreview *preview);
int m68k_analysis_render_lookup_append_auto_policy(M68kSourceAnalysisIR *source_analysis,
  M68kRenderLookup *lookup);
int m68k_analysis_render_lookup_append_section(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
  M68kSectionAnalysisIR *section_analysis);
int instruction_operand_writes_register_from_metadata(const M68kInstructionIR *instruction,
  size_t operand_index);
#endif
