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

typedef enum M68kRenderPointerCandidateMergeResult {
  M68K_RENDER_POINTER_CANDIDATE_MERGE_NONE = 0,
  M68K_RENDER_POINTER_CANDIDATE_MERGE_EXACT = 1,
  M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW = 2
} M68kRenderPointerCandidateMergeResult;

M68kRenderPointerCandidateMergeResult m68k_render_pointer_candidates_merge(
  uint8_t *dest_known, uint8_t *dest_count, uint32_t *dest_value, uint32_t dest_candidates[4],
  uint8_t source_known, uint8_t source_count, uint32_t source_value, const uint32_t source_candidates[4]);

typedef struct M68kAnalysisLabelPoint {
  size_t section_index;
  uint32_t offset;
  uint8_t confidence;
} M68kAnalysisLabelPoint;

typedef enum M68kRenderRangeStructuredItemSource {
  M68K_RENDER_RANGE_STRUCTURED_ITEM_NONE = 0,
  M68K_RENDER_RANGE_STRUCTURED_ITEM_POLICY = 1,
  M68K_RENDER_RANGE_STRUCTURED_ITEM_AUTO = 2
} M68kRenderRangeStructuredItemSource;

typedef struct M68kRenderRangeOwnershipView {
  size_t section_index;
  uint32_t start_offset;
  uint32_t end_offset;
  uint8_t kind;
  uint8_t status;
  uint8_t structured_item_source;
  uint32_t positive_evidence_flags;
  size_t structured_item_index;
  const M68kAnalysisStructuredDataItem *structured_item;
} M68kRenderRangeOwnershipView;

typedef struct M68kBaseLayoutSlot {
  int32_t displacement;
  int32_t size;
  int32_t alias_of_displacement;
  uint8_t alias;
  uint8_t has_alias_of;
  uint8_t has_source;
  uint8_t value_kind;
  uint8_t source_kind;
  uint8_t layout_kind;
  uint8_t base_kind;
  uint8_t storage_kind;
  size_t source_section_index;
  uint32_t source_offset;
  char layout_name[32];
  char base_symbol[64];
  char sizeof_symbol[64];
  char name[64];
  char owner_struct_name[64];
  char alias_of_name[64];
} M68kBaseLayoutSlot;

typedef struct M68kBaseLayoutGroup {
  size_t start_index;
  size_t end_index;
  int32_t base_offset;
  int32_t sizeof_value;
  uint8_t layout_kind;
  uint8_t uses_lib_size;
  char sizeof_symbol[64];
} M68kBaseLayoutGroup;

typedef struct M68kRenderPlatformLocalBaseSlot {
  uint8_t valid;
  uint8_t base_reg;
  uint16_t base_id;
  int16_t displacement;
  char library_name[64];
} M68kRenderPlatformLocalBaseSlot;

/* Closed low-WORD sets, capped to ensure loop convergence. Zero count is top.
 * Relative hardware sets never assert a single absolute register identity. */
#define M68K_HARDWARE_VALUE_LIMIT M68K_WORD_INDEX_VALUE_LIMIT
typedef struct M68kHardwareWordSet {
  uint16_t values[M68K_HARDWARE_VALUE_LIMIT];
  uint8_t count;
  uint8_t requires_input_contract;
} M68kHardwareWordSet;

typedef struct M68kHardwareRelativeBase {
  M68kHardwareWordSet offsets;
  uint16_t base_id;
} M68kHardwareRelativeBase;

typedef struct M68kRenderPlatformState {
  M68kHardwareWordSet word_values[8];
  M68kHardwareRelativeBase relative_hardware[8];
  uint32_t data_base_known;
  uint16_t data_base_id[8];
  char data_base_library[8][64];
  uint32_t address_base_known;
  uint16_t address_base_id[8];
  char address_base_library[8][64];
  uint32_t address_hardware_base_known;
  uint16_t address_hardware_base_id[8];
  uint32_t data_hardware_base_known;
  uint16_t data_hardware_base_id[8];
  uint32_t data_app_base_known;
  uint32_t address_app_base_known;
  uint32_t data_layout_base_known;
  char data_layout_base_symbol[8][64];
  uint32_t address_layout_base_known;
  char address_layout_base_symbol[8][64];
  uint32_t data_lvo_known;
  int16_t data_lvo[8];
  M68kRenderPlatformLocalBaseSlot local_base_slots[32];
} M68kRenderPlatformState;

typedef struct M68kRenderHardwareAddressUse {
  size_t section_index;
  M68kPlatformAddressUseIR use;
} M68kRenderHardwareAddressUse;

typedef struct M68kRenderAmigaVectorResolution {
  const AmigaOsLibraryVectorInfo *platform_vector;
  const AmigaOsLibraryVectorInfo *immediate_vector;
  const AmigaOsLibraryVectorInfo *wrapper_call_vector;
  const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
  const AmigaOsLibraryVectorInfo *helper_call_vector;
  const AmigaOsLibraryVectorInfo *chosen_vector;
  uint8_t chosen_kind;
  uint8_t chosen_note_kind;
} M68kRenderAmigaVectorResolution;

typedef struct M68kRenderGlobalBaseSlot {
  size_t section_index;
  uint32_t offset;
  size_t source_section_index;
  uint32_t source_offset;
  uint8_t has_source;
  uint8_t has_library_id;
  uint16_t library_id;
  char library_name[64];
  uint8_t conflicted;
} M68kRenderGlobalBaseSlot;

typedef struct M68kRenderGlobalBaseObservation {
  size_t section_index;
  uint32_t offset;
  uint8_t index_reg;
  int16_t lvos[32];
  size_t lvo_count;
} M68kRenderGlobalBaseObservation;

typedef struct M68kRenderBaseFieldSlot {
  char owner_name[64];
  int16_t displacement;
  size_t source_section_index;
  uint32_t source_offset;
  uint8_t has_source;
  uint8_t has_library_id;
  uint16_t library_id;
  char library_name[64];
  char symbol_name[64];
  uint8_t value_kind;
  uint8_t owner_kind;
  uint8_t observed_access_size;
  uint8_t conflicted;
} M68kRenderBaseFieldSlot;

/* A CFG-proved use of an existing canonical RSSET field. This is render
 * projection, not a new owner, policy input, or address-value domain. */
typedef struct M68kRenderLayoutFieldUse {
  size_t section_index;
  uint32_t offset;
  uint16_t region_index;
  uint8_t operand_index;
  uint8_t base_reg;
  int16_t displacement;
} M68kRenderLayoutFieldUse;

#define M68K_APP_LAYOUT_NAME "app"

#define M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE 0U
#define M68K_RENDER_BASE_FIELD_SLOT_IOREQUEST 1U
#define M68K_RENDER_BASE_FIELD_SLOT_NAMED_VALUE 2U
#define M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS 3U
#define M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE 4U

#define M68K_RENDER_BASE_FIELD_SLOT_OWNER_NAMED 0U
#define M68K_RENDER_BASE_FIELD_SLOT_OWNER_APP_BASE 1U

static inline int render_base_field_slot_owner_is_app_base(const M68kRenderBaseFieldSlot *slot) {
  return slot != NULL && slot->owner_kind == M68K_RENDER_BASE_FIELD_SLOT_OWNER_APP_BASE;
}

static inline int render_amiga_constant_value_by_symbol_id(uint16_t symbol_id, int32_t *out_value) {
  if (out_value == NULL) return 0;
  return amiga_os_find_constant_value_by_id(symbol_id, out_value);
}

typedef struct M68kRenderIndexedVectorWrapper {
  size_t section_index;
  uint32_t offset;
  uint8_t index_reg;
  uint8_t has_library_id;
  uint16_t library_id;
  char library_name[64];
} M68kRenderIndexedVectorWrapper;

typedef struct M68kRenderRecoveredFunctionArg {
  size_t section_index;
  uint32_t function_offset;
  uint16_t stack_offset;
  uint8_t reg_kind;
  uint8_t reg_index;
  uint8_t input_valid;
  PlatformFactsV2CallInput input;
} M68kRenderRecoveredFunctionArg;

/* Transient derivation evidence only.  Durable output is a common function
 * summary result in source analysis. */
typedef struct M68kRenderPlatformDerivedSummary {
  size_t section_index;
  uint32_t target_offset;
  const AmigaOsLibraryVectorInfo *vector;
} M68kRenderPlatformDerivedSummary;

/* Derived after typed-flow convergence and before source-analysis export.
 * These are callable-owned facts, not target-policy inputs. */
typedef struct M68kRenderInferredFunctionSummary {
  M68kAnalysisFunctionSummary summary;
  uint8_t terminal_reason;
  uint32_t direct_scc_anchor_section_index;
  uint32_t direct_scc_anchor_entry_offset;
  uint32_t direct_scc_size;
  uint32_t direct_scc_ordinal;
  uint8_t reserved;
} M68kRenderInferredFunctionSummary;

/* A callback-table identity observed by completed typed flow.  It is kept
 * separate from source-analysis uses because discovery runs during the CFG
 * fixed point; the post-flow collector owns durable summary/use emission. */
typedef struct M68kRenderObservedCallbackTable {
  size_t section_index;
  uint32_t table_offset;
} M68kRenderObservedCallbackTable;

typedef struct M68kRenderTypedSlotEffect {
  size_t section_index;
  uint32_t offset;
  int16_t displacement;
  /* Optional producer-owned memory type; uses existing alignment padding. */
  uint16_t struct_id;
  const AmigaOsCallOutputInfo *output;
} M68kRenderTypedSlotEffect;

typedef struct M68kRenderAppSlotRef {
  size_t section_index;
  M68kAppSlotRefIR ref;
  char symbol_name[64];
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
  uint32_t data_class_flags;
  char data_class[64];
} M68kRenderInferredRuntimeAddressRef;

typedef struct M68kRenderRuntimeAddressRange {
  const M68kFact *fact;
  uint8_t materialization_cached;
  uint8_t materialized;
  uint8_t materialization_reason;
  uint8_t reserved0;
  M68kRuntimeViewRelationshipIR relationship;
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
  uint8_t producer_operand_index;
  uint8_t transfer_count;
  uint8_t transfer_truncated;
  /* A join erased the origin. A later stack/base read must not manufacture a
   * fresh origin for this same value and restart provenance propagation. */
  uint8_t merge_conflicted;
  size_t section_index;
  uint32_t offset;
  M68kAddressValueTransferIR transfers[8];
} M68kRenderTypedProvenance;

typedef struct M68kRenderTypedRegValue {
  uint8_t known;
  uint8_t type_conflicted;
  uint8_t pointer_value_known;
  uint8_t pointer_candidate_count;
  uint8_t raw_long_value_known;
  uint8_t raw_long_candidate_count;
  uint8_t address_value_candidate_overflow;
  uint8_t pointer_target_known;
  uint32_t pointer_value;
  uint32_t pointer_candidates[4];
  uint32_t raw_long_value;
  uint32_t raw_long_candidates[4];
  const AmigaOsCallOutputInfo *output;
  uint16_t struct_id;
  uint16_t conflict_struct_id;
  uint16_t array_element_count;
  uint16_t array_element_index;
  int32_t byte_cursor;
  /* Exact unmodified runtime layout base. 0 unknown, 1 app, otherwise the
   * canonical RSSET region index + 2; artifact-local, never a guest address. */
  uint16_t layout_base_id;
  uint16_t read_relation; /* Interned read projection: even record, odd scalar; zero unknown. */
  uint32_t entry_value_id; /* Orthogonal affine entry identity; never a guest address. */
  M68kRenderTypedStorageOrigin origin;
  M68kAddressValueTableOriginIR table_origin;
  size_t pointer_target_section_index;
  uint32_t pointer_target_offset;
  M68kRenderTypedProvenance provenance;
} M68kRenderTypedRegValue;

typedef struct M68kRenderTypedMemoryBaseValue {
  uint8_t known;
  size_t section_index;
  uint32_t offset;
  /* Immutable origin plus accumulated delta are the CFG-owned affine value.
   * offset is retained as the resolved current address for existing typed-flow
   * clients; it must always equal origin + signed_addend when affine_known. */
  uint8_t affine_known;
  uint8_t reserved_affine[3];
  size_t affine_origin_section_index;
  uint32_t affine_origin_offset;
  int32_t affine_signed_addend;
  /* A homogeneous pointer table remains a useful type source when a loop
   * merges several concrete cursor positions.  Keep its declared range
   * separately from the exact address, which is intentionally cleared at
   * such a merge. */
  uint8_t pointer_table_known;
  uint16_t pointer_table_struct_id;
  size_t pointer_table_section_index;
  uint32_t pointer_table_offset;
  uint32_t pointer_table_size;
} M68kRenderTypedMemoryBaseValue;

typedef struct M68kRenderAffineAddressUse {
  size_t section_index;
  uint32_t offset;
  size_t origin_section_index;
  uint32_t origin_offset;
  size_t target_section_index;
  uint32_t target_offset;
  int32_t signed_addend;
  uint8_t operand_index;
  uint8_t base_register;
  M68kAffineLoopDomainIR loop_domain;
} M68kRenderAffineAddressUse;

typedef struct M68kRenderTypedStoredValue {
  uint8_t known;
  uint8_t pointer_value_known;
  uint8_t pointer_candidate_count;
  uint8_t raw_long_value_known;
  uint8_t raw_long_candidate_count;
  uint8_t address_value_candidate_overflow;
  uint8_t pointer_target_known;
  uint8_t app_base_evidence_kind;
  uint32_t pointer_value;
  uint32_t pointer_candidates[4];
  uint32_t raw_long_value;
  uint32_t raw_long_candidates[4];
  const AmigaOsCallOutputInfo *output;
  uint16_t struct_id;
  uint16_t array_element_count;
  uint16_t array_element_index;
  uint16_t layout_base_id;
  int32_t byte_cursor;
  uint32_t entry_value_id;
  uint8_t app_address_known;
  int16_t app_displacement;
  uint16_t read_relation;
  M68kAddressValueTableOriginIR table_origin;
  size_t pointer_target_section_index;
  uint32_t pointer_target_offset;
  M68kRenderTypedProvenance provenance;
} M68kRenderTypedStoredValue;

typedef struct M68kRenderTypedAppAddressValue {
  uint8_t known;
  uint8_t base_evidence_kind;
  int16_t displacement;
} M68kRenderTypedAppAddressValue;

typedef struct M68kRenderIoRequestSetupValue {
  uint8_t known;
  uint32_t value;
  uint32_t source_offset;
} M68kRenderIoRequestSetupValue;

typedef struct M68kRenderIoRequestSetup {
  M68kRenderIoRequestSetupValue command;
  M68kRenderIoRequestSetupValue disk_offset;
  M68kRenderIoRequestSetupValue byte_length;
  M68kRenderIoRequestSetupValue destination;
} M68kRenderIoRequestSetup;

typedef struct M68kRenderTypedStackSlot {
  uint8_t known;
  /* A value explicitly pushed by the caller is restored relative to the
   * caller's stack pointer after a call returns. Fixed stack-frame slots are
   * not given that ABI guarantee. */
  uint8_t caller_save_temporary;
  /* The ABI role of a non-temporary slot.  Keeping this distinct from its
   * displacement prevents a caller argument from satisfying a result or
   * cleanup contract at the same stack offset. */
  uint8_t abi_stack_convention;
  int16_t displacement;
  M68kRenderTypedStoredValue value;
  M68kRenderTypedMemoryBaseValue memory_base;
} M68kRenderTypedStackSlot;

typedef struct M68kRenderTypedBaseSlot {
  uint8_t known;
  uint8_t base_reg;
  int16_t displacement;
  /* 0 for register-relative cells; otherwise canonical storage index + 1.
   * Uses existing alignment padding. Canonical app/absolute cells use base_reg=UINT8_MAX. */
  uint32_t storage_id;
  M68kRenderTypedStoredValue value;
} M68kRenderTypedBaseSlot;

/* A field slot is local control-flow state, not a global alias claim.  Its
 * base register remains the object-identity contract; clearing or merging that
 * register drops the value rather than conflating equal-typed objects. */
typedef struct M68kRenderTypedFieldSlot {
  uint8_t known;
  uint8_t base_reg;
  uint16_t struct_id;
  int32_t displacement;
  M68kRenderTypedStoredValue value;
} M68kRenderTypedFieldSlot;

#define M68K_RENDER_TYPED_STACK_SLOT_LIMIT 32U
#define M68K_RENDER_TYPED_BASE_SLOT_LIMIT 32U
#define M68K_RENDER_TYPED_FIELD_SLOT_LIMIT 32U

typedef struct M68kRenderTypedState {
  M68kRenderTypedRegValue data_regs[8];
  M68kRenderTypedRegValue addr_regs[8];
  M68kRenderTypedAppAddressValue data_app_addr_regs[8];
  M68kRenderTypedAppAddressValue app_addr_regs[8];
  M68kRenderTypedMemoryBaseValue data_memory_base_regs[8];
  M68kRenderTypedMemoryBaseValue memory_base_regs[8];
  M68kRenderIoRequestSetup io_request_setups[8];
  /* Must-equal full Dn/An values: packed four-bit least-member representatives. */
  uint32_t register_alias_known;
  uint8_t register_alias_sources[8];
  /* A local write/call prevents resurrecting a global writer-summary value.
   * Exact local reaching stores may still supply their own value. */
  uint8_t memory_write_barriers;
  uint8_t source_snapshot_entry; /* Configured image-entry context, before separately guarded effects. */
  uint16_t zero_read_relation; /* CCR.Z describes the scalar projection of this read. */
  M68kRenderTypedStackSlot stack_slots[M68K_RENDER_TYPED_STACK_SLOT_LIMIT];
  size_t stack_slot_count;
  M68kRenderTypedBaseSlot base_slots[M68K_RENDER_TYPED_BASE_SLOT_LIMIT];
  size_t base_slot_count;
  M68kRenderTypedFieldSlot field_slots[M68K_RENDER_TYPED_FIELD_SLOT_LIMIT];
  size_t field_slot_count;
} M68kRenderTypedState;

typedef struct M68kRenderTypedFlowNode {
  const M68kDecodeCandidate *candidate;
  M68kRenderTypedState typed_in;
  M68kRenderTypedState typed_out;
  M68kRenderPlatformState platform_in;
  M68kRenderPlatformState platform_out;
  size_t *successors; /* One compact graph-owned edge pool, not a fixed fanout. */
  size_t call_target; /* Sparse CALL edge; SIZE_MAX when absent. */
  size_t successor_count;
  uint8_t is_root;
  uint8_t has_in;
  uint8_t has_out;
  uint8_t word_proof_ready; /* Converged scalar inputs/outputs occupy existing platform packets. */
  uint8_t source_snapshot_root; /* Canonical image entry, not an arbitrary code seed. */
} M68kRenderTypedFlowNode;

typedef struct M68kRenderTypedAccess {
  M68kWordIndexAccessIR word_index;
  size_t section_index;
  uint32_t offset;
  uint8_t operand_index;
  uint8_t base_reg;
  int16_t displacement;
  int16_t field_offset;
  uint16_t struct_size;
  uint16_t field_size;
  uint16_t field_byte_offset;
  int16_t array_element_addend;
  int32_t base_cursor;
  uint8_t inherited;
  uint8_t nested;
  M68kRenderTypedProvenance provenance;
  M68kAddressValueTableOriginIR table_origin;
  char root_struct_name[64];
  char owner_struct_name[64];
  char field_name[64];
  char field_expr[M68K_IR_SYMBOL_NAME_SIZE];
} M68kRenderTypedAccess;

typedef struct M68kRenderUnresolvedTypedAccess {
  size_t section_index;
  uint32_t offset;
  uint8_t operand_index;
  uint8_t base_reg;
  int32_t displacement;
  uint16_t struct_size;
  uint8_t access_size;
  uint8_t classification;
  uint8_t source_zero_write;
  uint8_t access_kind; /* Generated operand role; NONE means unavailable. */
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

typedef struct M68kRenderBootblockDiskRead {
  size_t section_index;
  uint32_t offset;
  uint32_t command_value;
  uint32_t disk_offset;
  uint32_t byte_length;
  uint32_t destination_addr;
  char command_name[32];
  uint8_t source_kind;
} M68kRenderBootblockDiskRead;

typedef struct M68kRenderBootblockRuntimeCopy {
  size_t section_index;
  uint32_t offset;
  uint32_t source_addr;
  uint32_t destination_addr;
  uint32_t byte_length;
  uint32_t handoff_addr;
  uint8_t source_kind;
} M68kRenderBootblockRuntimeCopy;

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

/* Pre-render observation of a typed address consumer. The public consumer
 * record carries the contract; the optional storage record carries only the
 * destination-specific detail. The transient value is resolved once through
 * the common source-address machinery before canonical analysis facts exist. */
typedef struct M68kRenderTypedAddressConsumer {
  M68kAddressValueConsumerIR fact;
  M68kPointerStoreIR storage;
  M68kRenderTypedStoredValue value;
  M68kRenderTypedProvenance provenance;
  size_t section_index;
  size_t target_section_index;
  size_t candidate_target_section_indices[4];
  uint32_t source_value;
  uint32_t target_offset;
  uint32_t candidate_source_values[4];
  uint32_t candidate_target_offsets[4];
  uint8_t resolution;
  uint8_t has_target;
  uint8_t candidate_target_count;
  uint8_t has_storage;
} M68kRenderTypedAddressConsumer;

void m68k_render_typed_address_consumer_mark_candidate_overflow(
  M68kRenderTypedAddressConsumer *consumer);

typedef struct M68kRenderDataPointerValue {
  uint8_t known;
  uint8_t exact;
  uint8_t dynamic_offset_known;
  size_t section_index;
  uint32_t offset;
  size_t dynamic_offset_section_index;
  uint32_t dynamic_offset_offset;
} M68kRenderDataPointerValue;

typedef struct M68kRenderDataScalarValue {
  uint8_t known;
  uint32_t value;
} M68kRenderDataScalarValue;

typedef struct M68kRenderDataPointerState {
  M68kRenderDataPointerValue data_regs[8];
  M68kRenderDataPointerValue addr_regs[8];
  M68kRenderDataScalarValue data_scalars[8];
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
  uint16_t base_id;
  char name[64];
} M68kRenderTraceRegName;

typedef struct M68kRenderTraceTarget {
  uint8_t known;
  size_t section_index;
  uint32_t offset;
} M68kRenderTraceTarget;

typedef struct M68kRenderTraceLocalSlot {
  uint8_t valid;
  uint8_t base_reg;
  uint16_t base_id;
  int16_t displacement;
  char library_name[64];
} M68kRenderTraceLocalSlot;

typedef struct M68kRenderTraceAppAddress {
  uint8_t known;
  int16_t displacement;
} M68kRenderTraceAppAddress;

typedef struct M68kRenderTraceStackValue {
  uint8_t has_library_name;
  char library_name[64];
} M68kRenderTraceStackValue;

typedef struct M68kRenderBaseTraceState {
  M68kRenderTraceRegName data_regs[8];
  M68kRenderTraceRegName addr_regs[8];
  M68kRenderTraceTarget addr_targets[8];
  M68kRenderTraceAppAddress app_addresses[8];
  M68kRenderTraceLocalSlot local_slots[32];
  M68kRenderTraceStackValue stack_values[16];
  size_t stack_value_count;
} M68kRenderBaseTraceState;

typedef enum M68kRenderBoundaryFlag {
  M68K_RENDER_BOUNDARY_NONE = 0,
  M68K_RENDER_BOUNDARY_LABEL = 1U << 0,
  M68K_RENDER_BOUNDARY_RELOCATION = 1U << 1,
  M68K_RENDER_BOUNDARY_ANCHOR = 1U << 2,
  M68K_RENDER_BOUNDARY_BLOCK_START = 1U << 3,
  M68K_RENDER_BOUNDARY_COMMENT = 1U << 4,
  M68K_RENDER_BOUNDARY_STRUCTURED_DATA = 1U << 5,
  M68K_RENDER_BOUNDARY_STRING_SPAN = 1U << 6,
  M68K_RENDER_BOUNDARY_LONG_TABLE_TARGET = 1U << 7
} M68kRenderBoundaryFlag;

/* A validated view of existing scalar leaf declarations under one canonical
 * source owner. Values keep using the shared array/cursor state below. */
typedef struct M68kRenderStaticRecordArray {
  size_t section_index;
  uint32_t offset;
  uint32_t size;
  uint16_t struct_id;
  uint16_t element_count;
} M68kRenderStaticRecordArray;

/* Sparse immutable descriptors. Handles travel in the existing value packets;
 * a repeated dynamic read kills earlier projections of the same descriptor. */
typedef struct M68kRenderScalarReadRelation {
  size_t section_index;
  uint32_t offset;
  int32_t field_cursor;
  uint32_t source_domain_id;
  uint16_t zero_type, nonzero_type;
  uint32_t roots[4], values[4];
  uint16_t types[4];
  uint8_t count;
} M68kRenderScalarReadRelation;

/* Transient projections of the canonical binder's accepted source domain.
 * They preserve source coordinates/types; no numeric candidate cap is expanded. */
typedef struct M68kRenderSourceDomainMember {
  size_t section_index;
  uint32_t offset, address, size;
  uint16_t struct_id;
} M68kRenderSourceDomainMember;

typedef struct M68kRenderSourceDomain {
  M68kRenderTypedProvenance producer;
  M68kAddressValueTableOriginIR origin;
  uint16_t struct_id;
  M68kRenderSourceDomainMember *members;
  size_t member_count;
  uint32_t address_min;
  uint64_t address_end;
} M68kRenderSourceDomain;

typedef struct M68kRenderSourceReadRequest {
  M68kRenderTypedProvenance producer;
  M68kAddressValueTableOriginIR origin;
  uint16_t struct_id;
  int32_t field_cursor;
} M68kRenderSourceReadRequest;

struct M68kRenderLookup {
  struct M68kRenderTypedFlowWorkflow *pending_source_flow;
  M68kRenderSourceReadRequest *source_read_requests;
  size_t source_read_request_count, source_read_request_capacity;
  M68kRenderSourceDomain *source_domains;
  size_t source_domain_count, source_domain_capacity;
  uint8_t source_domain_pass_done, source_domain_error;
  M68kRenderScalarReadRelation *scalar_read_relations;
  size_t scalar_read_relation_count, scalar_read_relation_capacity;
  size_t *scalar_read_index;
  size_t scalar_read_index_capacity;
  M68kRenderStaticRecordArray *static_record_arrays;
  size_t static_record_array_count;
  Arena *arena;
  struct M68kAffineEntryContext *affine_entry_context;
  uint8_t suppress_address_value_observations; /* Intermediate CFG states are non-admitting. */
  M68kIncompleteAnalysisIR *typed_flow_incomplete;
  size_t typed_flow_incomplete_count;
  size_t typed_flow_incomplete_capacity;
  /* Rendering-only bootstrap replacement. Original analysis views stay intact;
   * helper bytes are emitted in their containing image/storage view. */
  const M68kBootstrapContractIR *render_in_place_helper_contract;
  uint8_t **labels;
  uint8_t **label_target_refs;
  uint8_t **label_statement_refs;
  uint8_t **storage_label_target_refs;
  const char ***object_symbol_labels;
  const M68kFact ***relocations;
  const M68kFact ***anchors;
  uint8_t **block_starts;
  uint32_t **block_start_before_or_at;
  uint16_t **render_boundary_flags;
  uint32_t *label_extents;
  uint32_t *label_target_ref_extents;
  uint32_t *label_statement_ref_extents;
  uint32_t *storage_label_target_ref_extents;
  uint32_t *object_symbol_label_extents;
  uint32_t *relocation_extents;
  uint32_t *anchor_extents;
  uint32_t *block_start_extents;
  uint32_t *block_start_before_or_at_extents;
  uint32_t *render_boundary_extents;
  size_t section_count;
  const M68kObject *object;
  const M68kAnalysisPolicy *policy;
  uint8_t build_complete;
  uint8_t reserved0[7];
  M68kRenderGlobalBaseSlot *global_base_slots;
  size_t global_base_slot_count;
  size_t global_base_slot_capacity;
  M68kRenderBaseFieldSlot *base_field_slots;
  size_t base_field_slot_count;
  size_t base_field_slot_capacity;
  M68kRenderAppSlotRef *app_slot_refs;
  size_t app_slot_ref_count;
  size_t app_slot_ref_capacity;
  /* Frozen, source-ordered view of converged access facts; canonical order is unchanged. */
  const M68kRenderAppSlotRef **app_slot_ref_index;
  M68kRenderLayoutFieldUse *layout_field_uses;
  size_t layout_field_use_count;
  size_t layout_field_use_capacity;
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
  M68kRenderPlatformDerivedSummary *platform_derived_summaries;
  size_t platform_derived_summary_count;
  size_t platform_derived_summary_capacity;
  M68kRenderInferredFunctionSummary *inferred_function_summaries;
  size_t inferred_function_summary_count;
  size_t inferred_function_summary_capacity;
  uint8_t inferred_function_summaries_ready;
  M68kRenderObservedCallbackTable *observed_callback_tables;
  size_t observed_callback_table_count;
  size_t observed_callback_table_capacity;
  M68kRenderTypedSlotEffect *typed_slot_effects;
  size_t typed_slot_effect_count;
  size_t typed_slot_effect_capacity;
  M68kRenderTypedAccess *typed_accesses;
  size_t typed_access_count;
  size_t typed_access_capacity;
  M68kRenderHardwareAddressUse *hardware_address_uses;
  size_t hardware_address_use_count;
  size_t hardware_address_use_capacity;
  M68kRenderAffineAddressUse *affine_address_uses;
  size_t affine_address_use_count;
  size_t affine_address_use_capacity;
  M68kRenderUnresolvedTypedAccess *unresolved_typed_accesses;
  size_t unresolved_typed_access_count;
  size_t unresolved_typed_access_capacity;
  M68kRenderTypedAddressConsumer *address_value_consumers;
  size_t address_value_consumer_count;
  size_t address_value_consumer_capacity;
  M68kFunctionSummaryUseIR *function_summary_uses;
  size_t function_summary_use_count;
  size_t function_summary_use_capacity;
  M68kPlatformCallThunkIR *platform_call_thunks;
  size_t platform_call_thunk_count;
  size_t platform_call_thunk_capacity;
  M68kRenderBootblockDiskRead *bootblock_disk_reads;
  size_t bootblock_disk_read_count;
  size_t bootblock_disk_read_capacity;
  M68kRenderBootblockRuntimeCopy *bootblock_runtime_copies;
  size_t bootblock_runtime_copy_count;
  size_t bootblock_runtime_copy_capacity;
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
  M68kRenderRangeOwnershipView *range_ownerships;
  size_t range_ownership_count;
  size_t range_ownership_capacity;
  M68kAnalysisStructuredDataItem *auto_structured_data_items;
  size_t auto_structured_data_item_count;
  size_t auto_structured_data_item_capacity;
  size_t **instruction_comment_indices;
  uint32_t *instruction_comment_extents;
  size_t **auto_structured_data_item_indices;
  uint32_t *auto_structured_data_item_index_extents;
  size_t **string_span_indices;
  uint32_t *string_span_index_extents;
};

Arena *render_lookup_arena(M68kRenderLookup *lookup);
void *render_lookup_calloc(M68kRenderLookup *lookup, size_t count, size_t size);
void *render_lookup_grow_array(M68kRenderLookup *lookup, const void *old_items, size_t old_count,
  size_t item_size, size_t new_capacity);
void render_lookup_mark_boundary_flag(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  uint16_t flag);
uint16_t render_lookup_boundary_flags(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
void render_lookup_mark_label_target_ref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
void render_lookup_mark_label_statement_ref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
void render_lookup_mark_storage_label_target_ref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset);

void format_numeric_value(char *buffer, size_t buffer_size, uint32_t size, uint32_t value);
uint8_t format_lookup_asm_label_with_generation(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset);
const M68kAnalysisStructuredDataItem *lookup_structured_data_item_at_offset(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset);
const M68kAnalysisStructuredDataItem *lookup_structured_data_item_covering_offset(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset);
int lookup_range_ownership_at_offset(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    M68kRenderRangeOwnershipView *out_range);
int lookup_range_ownership_covering_offset(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    M68kRenderRangeOwnershipView *out_range);
int lookup_range_ownership_at_index(const M68kRenderLookup *lookup, size_t index,
    M68kRenderRangeOwnershipView *out_range);
int render_lookup_add_range_ownership_for_structured_item(M68kRenderLookup *lookup, size_t section_index,
    uint8_t structured_item_source, size_t structured_item_index, const M68kAnalysisStructuredDataItem *item);
int structured_data_item_comment(const M68kAnalysisStructuredDataItem *item, char *comment,
    size_t comment_size);
int structured_data_item_render_comment(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *comment, size_t comment_size);
int structured_data_item_symbolic_operand_expr(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *expr, size_t expr_size);
void record_source_export_failure(M68kRenderIRPreview *preview, M68kSourceExportFailureKind kind, size_t section_index,
    uint32_t offset, uint32_t aux_offset);
void record_numeric_runtime_ref(M68kRenderIRPreview *preview, const M68kFact *fact);
int lookup_offset_is_inside_relocation_payload(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset);
int lookup_has_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
int lookup_has_renderable_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
int lookup_structured_long_table_targets_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset);
int lookup_label_has_explicit_name(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
int lookup_structured_field_has_explicit_label(const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, size_t section_index, uint32_t offset);
int lookup_label_statement_ref_is_semantic_runtime_data(const M68kRenderLookup *lookup,
  size_t section_index, uint32_t offset);
int lookup_label_has_statement_ref(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
int lookup_should_emit_label_statement(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, size_t section_index, uint32_t offset);
uint32_t lookup_code_block_start_before_or_at(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset);
int lookup_source_runtime_address(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t source_offset, uint32_t *out_runtime_address);
int lookup_source_unique_runtime_span(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t source_offset, uint32_t width, uint32_t *out_runtime_address);
int lookup_runtime_range_materialization(const M68kRenderLookup *lookup, const M68kFact *range,
  uint8_t *out_materialized, uint8_t *out_reason, M68kRuntimeViewRelationshipIR *out_relationship);
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
void render_asm_base_layout_rs(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode);
size_t base_layout_slot_capacity_for_lookup(const M68kRenderLookup *lookup);
int base_layout_collect_slots(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, M68kBaseLayoutSlot *slots, size_t slot_capacity, size_t *out_slot_count,
  int *out_has_resident_context, int *out_has_app_sizeof_value, int32_t *out_base_offset,
  int32_t *out_app_sizeof_value);
size_t base_layout_prepare_groups(M68kBaseLayoutSlot *slots, size_t slot_count,
  M68kBaseLayoutGroup *layouts, size_t layout_capacity, int32_t app_base_offset,
  int has_resident_context, int has_app_sizeof_value, int32_t app_sizeof_value);
void render_asm_org(M68kRenderIRPreview *preview, uint32_t logical_address);
void render_asm_sync_logical_pc(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
  size_t section_index, uint32_t source_offset, uint32_t *io_logical_pc);
void platform_state_clear_data_lvo(M68kRenderPlatformState *state, uint8_t reg_index);
int platform_state_name_is_app_base(const char *name);
int platform_state_set_named_base_value(M68kRenderPlatformState *state, const M68kAnalysisPolicy *policy,
    uint8_t register_kind, uint8_t register_index, const char *base_symbol);
void platform_state_set_register_library(M68kRenderPlatformState *state, uint8_t reg_index,
  const char *library_name);
int operand_is_address_displacement_local(const M68kOperandIR *operand, uint8_t *out_reg,
  int16_t *out_displacement);
int operand_is_address_memory_local(const M68kOperandIR *operand, uint8_t *out_reg,
  int16_t *out_displacement);
int operand_is_address_register_local(const M68kOperandIR *operand, uint8_t reg_index);
int operand_is_absolute_address_local(const M68kOperandIR *operand, uint32_t address);
int operand_absolute_offset_local(const M68kOperandIR *operand, uint32_t *out_offset);
int operand_is_postinc_a7_local(const M68kOperandIR *operand);
int operand_is_data_register_local(const M68kOperandIR *operand, uint8_t *out_reg);
int operand_address_register_index_local(const M68kOperandIR *operand, uint8_t *out_reg);
uint8_t app_slot_access_kind_from_instruction(const M68kInstructionIR *instruction, size_t operand_index);
uint8_t app_slot_access_size_from_instruction(const M68kInstructionIR *instruction, size_t operand_index, uint8_t access_kind);
uint8_t render_app_base_evidence_kind(const M68kRenderLookup *lookup,
  const M68kRenderPlatformState *state, uint8_t base_reg, int16_t displacement, uint8_t access_size);
void hardware_relative_transfer_linear(M68kRenderPlatformState *state, const M68kRenderPlatformState *before,
  const M68kInstructionIR *instruction);
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
  uint8_t index_reg, const char *library_name);
int render_lookup_add_runtime_address_ref(M68kRenderLookup *lookup, const M68kFact *fact);
int render_lookup_add_runtime_address_range(M68kRenderLookup *lookup, const M68kFact *fact);
int render_lookup_add_code_start_ref(M68kRenderLookup *lookup, const M68kFact *fact);
int render_lookup_add_violation_ref(M68kRenderLookup *lookup, const M68kFact *fact);
int render_lookup_add_storage_xref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  size_t target_section_index, uint32_t target_offset);
int render_lookup_add_pc_relative_xrefs(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
  uint8_t **accepted_start);
uint8_t symbol_ref_kind_for_operand(const M68kOperandIR *operand);
int render_lookup_add_instruction_comment(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  const char *comment);
int render_lookup_add_recovered_function_arg(M68kRenderLookup *lookup, size_t section_index,
  uint32_t function_offset, uint16_t stack_offset, uint8_t reg_kind, uint8_t reg_index,
  const PlatformFactsV2CallInput *input);
int render_lookup_add_platform_derived_summary(M68kRenderLookup *lookup, size_t section_index,
    uint32_t target_offset, const AmigaOsLibraryVectorInfo *vector);
int render_lookup_add_function_summary_use(M68kRenderLookup *lookup, const M68kFunctionSummaryUseIR *use);
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
/* Shared read-only inline-object projection; never a pointer-cell insertion. */
size_t render_lookup_inline_app_region_count(const M68kRenderLookup *lookup);
int render_lookup_inline_app_region_at(const M68kRenderLookup *lookup, size_t index,
    int16_t *displacement, uint16_t *struct_id, const char **symbol);
uint16_t render_lookup_struct_id(const M68kRenderLookup *lookup, const char *name);
uint16_t render_lookup_struct_size(const M68kRenderLookup *lookup, uint16_t struct_id);
const char *render_lookup_struct_name(const M68kRenderLookup *lookup, uint16_t struct_id);
int render_lookup_struct_field_expression(const M68kRenderLookup *lookup, uint16_t struct_id,
    int16_t displacement, char *expression, size_t expression_size);
int render_lookup_add_typed_access(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t root_struct_id,
    const AmigaOsResolvedStructFieldInfo *field, const char *field_expr,
    const M68kRenderTypedProvenance *provenance);
int render_lookup_add_unresolved_typed_access(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  uint8_t operand_index, uint8_t base_reg, int32_t displacement, uint16_t root_struct_id, uint16_t struct_size,
  uint8_t access_size, uint8_t refinement_applied, uint16_t refined_struct_id,
  const M68kRenderTypedProvenance *provenance);
const char *render_lookup_device_name_for_call(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset);
int render_lookup_add_string_span(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  uint32_t size);
const char *lookup_instruction_comment(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
const M68kAnalysisManualRepresentation *lookup_manual_operand_representation(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, size_t operand_index);
const M68kRenderStringSpan *lookup_string_span_at_offset(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset);
int append_comment_part_local(char *comment, size_t comment_size, const char *part);
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
int amiga_unknown_base_register_owner_name(uint8_t base_reg, char *buf, size_t buf_size);
int amiga_vector_call_input_by_register(const AmigaOsLibraryVectorInfo *vector,
  uint8_t reg_kind, uint8_t reg_index, PlatformFactsV2CallInput *out_input);
const AmigaOsLibraryVectorInfo *attach_amiga_lvo_symbol_if_known(const M68kRenderPlatformState *state,
  M68kInstructionIR *instruction);
const AmigaOsLibraryVectorInfo *attach_amiga_lvo_immediate_if_known(const M68kRenderLookup *lookup,
  const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
  M68kInstructionIR *instruction);
int base_field_slot_is_base_pointer(const M68kRenderBaseFieldSlot *slot);
int candidate_calls_a6_lvo(const M68kDecodeCandidate *candidate, int16_t *out_lvo);
int candidate_calls_a6_data_indexed_vector(const M68kDecodeCandidate *candidate, uint8_t *out_index_reg);
int candidate_has_local_helper_summary_fallthrough(const M68kDecodeCandidate *candidate);
int candidate_has_non_call_control_target(const M68kDecodeCandidate *candidate);
int candidate_is_accepted_start(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
  const M68kDecodeCandidate *candidate);
int candidate_loads_data_lvo_immediate(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
  int16_t *out_lvo);
int candidate_loads_relocated_global_slot_to_a6(const M68kRenderLookup *lookup, size_t section_index,
  const M68kDecodeCandidate *candidate, size_t *out_target_section, uint32_t *out_target_offset);
int candidate_writes_a6_unknown(const M68kDecodeCandidate *candidate);
const M68kDecodeCandidate *find_candidate_at_offset_local(const M68kDecodeSectionIR *section, uint32_t offset);
int find_unique_relocation_operand(const M68kDecodeCandidate *candidate, const M68kFact *relocation,
  size_t *out_operand_index);
int instruction_is_local_wrapper_cleanup(const M68kInstructionIR *instruction);
uint16_t render_base_field_slot_pointer_struct_id(const M68kRenderBaseFieldSlot *slot);
uint16_t lookup_app_base_field_slot_struct_id(const M68kRenderLookup *lookup, int16_t displacement);
uint16_t lookup_base_field_slot_struct_id(const M68kRenderLookup *lookup, const char *owner_name,
  int16_t displacement);
int lookup_has_amiga_resident_library_context(const M68kRenderLookup *lookup);
const M68kFact *lookup_relocation_at(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
void platform_state_apply_policy_register_seeds(M68kRenderPlatformState *state, const M68kAnalysisPolicy *policy,
  size_t section_index, uint32_t offset);
void platform_state_update_data_lvo_after_instruction(M68kRenderPlatformState *state,
  const M68kInstructionIR *instruction);
void platform_state_update_after_instruction(M68kRenderPlatformState *state, const M68kRenderLookup *lookup,
  const M68kInstructionIR *instruction);
void platform_state_note_call_result_after_instruction(M68kRenderPlatformState *state,
  const M68kInstructionIR *instruction, const AmigaOsLibraryVectorInfo *vector);
uint32_t render_section_extent(const M68kDecodeSectionIR *section);
int render_cfg_candidate_has_fallthrough(const M68kDecodeCandidate *candidate);
int render_lookup_add_indexed_vector_wrapper_branch_aliases(M68kRenderLookup *lookup,
  const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t indexed_entry,
  uint8_t index_reg, const char *library_name);
const AmigaOsLibraryVectorInfo *resolve_amiga_indexed_wrapper_call_vector(const M68kRenderLookup *lookup,
  const M68kRenderPlatformState *state, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate);
void attach_operand_label_symbol(const M68kRenderLookup *lookup, M68kInstructionIR *instruction,
  size_t operand_index, size_t source_section_index, uint32_t source_offset, size_t target_section_index,
  uint32_t target_offset);
typedef struct M68kSourceAnalysisBuildStats {
  uint32_t platform_base_slot_count;
  uint32_t platform_call_count;
  uint32_t platform_effect_count;
} M68kSourceAnalysisBuildStats;

typedef struct M68kPlatformAnalysisPassStats {
  double pass_seconds;
  double base_slot_seconds;
  double call_summary_seconds;
  double typed_ref_seconds;
  double typed_summary_seconds;
  double typed_graph_seconds;
  double typed_flow_seconds;
  double typed_callback_seconds;
  double call_comment_seconds;
  double app_slot_seconds;
  double runtime_data_seconds;
  double hardware_data_seconds;
  double generic_data_seconds;
} M68kPlatformAnalysisPassStats;

int m68k_analysis_render_lookup_run_platform_passes(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
  uint8_t **accepted_start, uint8_t **accepted_bytes, M68kPlatformAnalysisPassStats *stats);
int m68k_render_lookup_build(M68kRenderLookup *lookup, const M68kObject *object, const M68kDecodeIR *decode,
  const M68kFactIR *facts, const M68kAnalysisPolicy *policy, uint8_t **accepted_start,
  const M68kAnalysisLabelPoint *analysis_labels, size_t analysis_label_count);
void m68k_analysis_render_lookup_release_source_flow(M68kRenderLookup *lookup);
/* 1: canonical domains changed typed input; 0: no eligible input; -1: failure. */
int m68k_analysis_render_lookup_refine_source_domains(M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, M68kSourceAnalysisIR *source_analysis);
void m68k_render_lookup_destroy(M68kRenderLookup *lookup);
void m68k_render_lookup_materialize_relocation_target_labels(M68kRenderLookup *lookup);
int m68k_analysis_render_lookup_import_source_analysis_structured_data(M68kRenderLookup *lookup,
  const M68kSourceAnalysisIR *source_analysis);
int m68k_analysis_render_lookup_materialize_typed_address_targets(M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, uint8_t **accepted_bytes);
int m68k_analysis_render_lookup_append_base_layout_fields(Arena *scratch_arena,
  const M68kRenderLookup *lookup, const M68kDecodeIR *decode, M68kSourceAnalysisIR *source_analysis);
int m68k_analysis_render_lookup_build_source_analysis(M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, const M68kAnalysisPolicy *policy, uint8_t **accepted_start,
  uint8_t **accepted_bytes, M68kSourceAnalysisIR *source_analysis, M68kSourceAnalysisBuildStats *out_stats);
/* The renderer may tentatively propagate a pointee type before the canonical
 * source-analysis table-entry binder has validated the selection.  Remove
 * only table-derived renderer facts whose final durable address value is not
 * a unique symbolic contract. */
/* Shared source-record view used by transfer and final canonical binding.
 * Packed arrays, source-field interiors and conflicting declarations retain
 * the same semantics in both consumers. No values are read from raw bytes. */
uint16_t m68k_policy_source_struct_at(const M68kAnalysisPolicy *policy, size_t section_index,
    uint32_t offset, uint16_t *out_array_count, uint16_t *out_array_index,
    int32_t *out_cursor, uint16_t *out_conflict_struct_id);
void m68k_analysis_render_lookup_reconcile_typed_table_contracts(M68kRenderLookup *lookup,
  M68kSourceAnalysisIR *source_analysis);
void m68k_analysis_render_lookup_resolve_amiga_instruction_platform_vectors(const M68kRenderLookup *lookup,
  const M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode, uint8_t **accepted_start_all,
  const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
  M68kInstructionIR *instruction, M68kRenderAmigaVectorResolution *resolution);
int m68k_analysis_render_lookup_append_platform_call_facts_for_section(M68kSourceAnalysisBuildStats *stats,
  M68kRenderLookup *lookup, M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode,
  const M68kAnalysisPolicy *policy, uint8_t **accepted_start_all, size_t section_array_index,
  const M68kDecodeSectionIR *section, M68kSectionAnalysisIR *section_analysis);
int m68k_render_ir_preview_emit_prepared(const M68kObject *object, const M68kDecodeIR *decode,
  M68kRenderLookup *prepared_lookup, const M68kAnalysisPolicy *policy, uint8_t **accepted_start,
  uint8_t **accepted_bytes, int render_text_preview, int render_asm_source, int collect_asm_source_text,
  int emit_asm_source_text, M68kRenderIRPreview *out_preview, const M68kSourceAnalysisIR *source_analysis);
int m68k_analysis_render_lookup_append_cfg_for_section(const M68kRenderLookup *lookup,
  const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const uint8_t *accepted_bytes,
  Arena *scratch_arena, M68kSectionAnalysisIR *section_analysis);
int m68k_analysis_render_lookup_append_labels_for_section(const M68kRenderLookup *lookup,
  const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
  M68kSectionAnalysisIR *section_analysis);
int m68k_analysis_render_lookup_append_orphan_code_signals_for_section(const M68kRenderLookup *lookup,
  const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const uint8_t *accepted_bytes,
  M68kSectionAnalysisIR *section_analysis);
int m68k_analysis_render_lookup_append_section(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
  M68kSectionAnalysisIR *section_analysis);
int instruction_operand_writes_register_from_metadata(const M68kInstructionIR *instruction,
  size_t operand_index);
/* Rebuild only after the platform collectors have completed. */
int render_lookup_index_app_accesses(M68kRenderLookup *lookup);

#endif
