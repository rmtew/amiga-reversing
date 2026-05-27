#include "m68k_analysis_facts_v2.h"

#include "m68k_decode_ir.h"
#include "m68k_assembler.h"
#include "m68k_bitset.h"
#include "m68k_fact_ir.h"
#include "m68k_ir_codec.h"
#include "m68k_instruction_spec.h"
#include "m68k_parse_util.h"
#include "m68k_render_ir.h"
#include "m68k_simulator.h"
#include "platform_common.h"
#include "generated/amiga_os_runtime.h"
#include "generated/m68k_cpu_runtime.h"
#include "util_arena.h"

#include <stdlib.h>
#include <string.h>
#include <time.h>

#define M68K_FACTS_V2_TRACE_UNKNOWN 0U
#define M68K_FACTS_V2_TRACE_CONSTANT 1U
#define M68K_FACTS_V2_TRACE_SOURCE_OFFSET 2U
#define M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS 3U
#define M68K_FACTS_V2_TRACE_TARGET_SET 4U
#define M68K_FACTS_V2_TRACE_WORD_RELATIVE_TABLE 5U
#define M68K_FACTS_V2_TRACE_KEYED_LONG_RELATIVE_TABLE 6U
#define M68K_FACT_RUNTIME_ADDRESS_REF_NO_OPERAND UINT32_MAX
#define M68K_FACTS_V2_TRACE_ABSOLUTE_SLOT_LIMIT 16U
#define M68K_FACTS_V2_TRACE_STACK_SLOT_LIMIT 8U
#define M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT 64U
#define M68K_FACTS_V2_TRACE_STATE_VARIANT_LIMIT 2U
#define M68K_FACTS_V2_TRACE_INDIRECT_STATE_VARIANT_LIMIT 8U
/* Word-relative dispatches may fan out across a large routine cluster; each
   entry is still required to map to an even in-section control target. */
#define M68K_FACTS_V2_WORD_DISPATCH_LOCAL_LIMIT 0x2000
#define M68K_FACTS_V2_WORD_DISPATCH_FAR_BOUNDARY_MIN 0x1000
#define M68K_FACTS_V2_EXTERNAL_RUNTIME_ADDRESS_MIN 0x1000U

typedef struct M68kFactsV2TraceValue {
  uint8_t kind;
  uint8_t has_origin;
  uint16_t origin_operand_index;
  size_t section_index;
  uint32_t value;
  size_t origin_section_index;
  uint32_t origin_offset;
  uint32_t code_start_reason;
  uint32_t target_count;
  uint32_t targets[M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT];
} M68kFactsV2TraceValue;

typedef struct M68kFactsV2AbsoluteSlot {
  uint8_t used;
  uint8_t reserved[3];
  uint32_t address;
  M68kFactsV2TraceValue value;
} M68kFactsV2AbsoluteSlot;

typedef struct M68kFactsV2StackSlot {
  uint8_t used;
  uint8_t reserved[3];
  uint32_t displacement;
  M68kFactsV2TraceValue value;
} M68kFactsV2StackSlot;

typedef struct M68kFactsV2CallbackFieldTarget {
  size_t section_index;
  uint32_t store_offset;
  uint8_t base_reg;
  uint8_t reserved[3];
  int32_t displacement;
  M68kFactsV2TraceValue target;
} M68kFactsV2CallbackFieldTarget;

typedef struct M68kFactsV2CallbackFieldTargets {
  M68kFactsV2CallbackFieldTarget *items;
  size_t count;
  size_t capacity;
} M68kFactsV2CallbackFieldTargets;

typedef struct M68kFactsV2TraceState {
  M68kFactsV2TraceValue d[8];
  M68kFactsV2TraceValue a[8];
  uint32_t d_low16_known;
  uint32_t d_low16_has_origin;
  uint16_t d_low16[8];
  uint32_t d_low16_origin_offset[8];
  M68kFactsV2AbsoluteSlot absolute_slots[M68K_FACTS_V2_TRACE_ABSOLUTE_SLOT_LIMIT];
  M68kFactsV2StackSlot stack_slots[M68K_FACTS_V2_TRACE_STACK_SLOT_LIMIT];
  uint8_t reglist_copy_valid;
  uint8_t reglist_copy_width;
  uint16_t reglist_copy_mask;
  size_t reglist_copy_section_index;
  uint32_t reglist_copy_offset;
  uint32_t reglist_copy_size;
  uint8_t copied_entry_valid;
  uint8_t copied_entry_dest_reg;
  size_t copied_entry_section_index;
  uint32_t copied_entry_source_offset;
  uint32_t copied_entry_size;
} M68kFactsV2TraceState;

typedef struct M68kFactsV2WorkItem {
  size_t section_index;
  uint32_t offset;
  uint32_t reason;
  size_t source_section_index;
  uint32_t source_offset;
  uint8_t confidence;
  uint8_t has_runtime_address;
  uint8_t allow_trace_variant;
  uint8_t reserved[1];
  uint32_t runtime_address;
  M68kFactsV2TraceState trace_state;
} M68kFactsV2WorkItem;

typedef struct M68kFactsV2WorkQueue {
  Arena *arena;
  M68kFactsV2WorkItem *items;
  size_t *stateful_next;
  size_t count;
  size_t capacity;
  size_t stateful_next_capacity;
  size_t cursor;
  size_t section_count;
  uint8_t **queued_confidence;
  size_t **stateful_heads;
  uint32_t *extents;
} M68kFactsV2WorkQueue;

typedef struct M68kFactsV2RelocationFailure {
  uint32_t reason;
  uint32_t anchor_kind;
  uint32_t section;
  uint32_t offset;
  uint32_t target_section;
  uint32_t width;
  uint32_t platform_record_kind;
  uint32_t raw_value;
  int64_t computed_target;
} M68kFactsV2RelocationFailure;

typedef struct M68kFactsV2TableBaseRef {
  uint8_t valid;
  uint8_t has_origin;
  size_t origin_section_index;
  uint32_t origin_offset;
  size_t origin_operand_index;
  uint32_t table_offset;
  uint32_t base_runtime_address;
} M68kFactsV2TableBaseRef;

typedef struct M68kFactsV2RelocationLookup {
  size_t section_count;
  size_t **indices;
  uint32_t *extents;
} M68kFactsV2RelocationLookup;

typedef struct M68kFactsV2LabelLookup {
  size_t section_count;
  uint8_t **labels;
  uint32_t *extents;
} M68kFactsV2LabelLookup;

typedef struct M68kAcceptedSectionIndex {
  const M68kDecodeCandidate **candidates;
  size_t count;
} M68kAcceptedSectionIndex;

typedef struct M68kAcceptedCandidateIndex {
  Arena *arena;
  ArenaMark mark;
  uint8_t has_mark;
  uint8_t reserved[7];
  M68kAcceptedSectionIndex *sections;
  size_t section_count;
} M68kAcceptedCandidateIndex;

typedef struct M68kRuntimeAddressRange {
  size_t section_index;
  uint32_t source_offset;
  uint32_t runtime_address;
  uint32_t size;
  uint8_t kind;
  uint8_t confidence;
  uint8_t reserved[2];
} M68kRuntimeAddressRange;

typedef struct M68kRuntimeAddressSpace {
  Arena *arena;
  M68kRuntimeAddressRange *ranges;
  size_t count;
  size_t capacity;
} M68kRuntimeAddressSpace;

typedef struct M68kFactsV2Workflow {
  Arena *arena;
  M68kRenderIRPreview *render_preview;
} M68kFactsV2Workflow;

static int append_violation_fact(M68kFactIR *facts, size_t section_index, uint32_t source_offset,
  uint32_t target_offset);
static int append_violation_fact_with_reason(M68kFactIR *facts, size_t section_index, uint32_t source_offset,
  uint32_t target_offset, uint32_t reason, size_t reason_source_section_index, uint32_t reason_source_offset);
static int append_runtime_address_ref_fact(M68kFactIR *facts, size_t section_index, uint32_t source_offset,
  size_t operand_index, uint32_t target_offset, uint32_t runtime_address, uint8_t confidence);
static int append_runtime_address_ref_fact_with_sink(M68kFactIR *facts, size_t section_index,
  uint32_t source_offset, size_t operand_index, uint32_t target_offset, uint32_t runtime_address,
  uint32_t sink_address, uint8_t confidence);
static int append_external_runtime_address_ref_fact(M68kFactIR *facts, size_t section_index,
  uint32_t source_offset, size_t operand_index, uint32_t runtime_address, uint32_t sink_address,
  size_t sink_source_section_index, uint32_t sink_source_offset, uint8_t confidence);
static int append_relocation_anchor_fact(M68kFactIR *facts, const M68kFixup *fixup,
  const M68kFactsV2RelocationFailure *anchor);
static void trace_value_set_unknown(M68kFactsV2TraceValue *value);
static void trace_value_set_constant(M68kFactsV2TraceValue *value, uint32_t constant);
static void trace_value_set_constant_with_origin(M68kFactsV2TraceValue *value, uint32_t constant,
  size_t section_index, uint32_t offset, size_t operand_index);
static void trace_value_set_source_offset_with_reason(M68kFactsV2TraceValue *value, size_t section_index,
  uint32_t offset, uint32_t code_start_reason);
static int trace_value_from_candidate_source(size_t section_index, const M68kDecodeSectionIR *section,
  const M68kDecodeCandidate *candidate, size_t operand_index, const M68kFactsV2TraceState *state,
  M68kFactsV2TraceValue *out_value);
static int trace_value_to_table_storage_offset(const M68kFactsV2TraceValue *value,
  const M68kRuntimeAddressSpace *runtime_addresses, size_t section_index, uint32_t section_size,
  uint32_t *out_offset);
static int trace_state_operand_storage_offset(const M68kRuntimeAddressSpace *runtime_addresses,
  size_t section_index, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
  const M68kFactsV2TraceState *state, size_t operand_index, uint32_t *out_offset);
static int candidate_operand_data_target_offset(const M68kDecodeCandidate *candidate, size_t operand_index,
  size_t section_index, uint32_t *out_offset);
static int scan_interleaved_indexed_key_stub_table(M68kDecodeIR *decode, uint8_t max_cpu, size_t section_index,
  const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate, uint8_t **accepted_start,
  uint8_t **accepted_bytes, uint32_t *out_entries, uint32_t entry_limit, uint32_t *out_entry_count,
  uint32_t *out_stub_table_offset, uint32_t *out_stride);
static int indexed_control_operand_base_is_inside_instruction(const M68kDecodeCandidate *candidate,
  uint32_t operand_base_offset);
static int indexed_control_post_instruction_table_start(const M68kDecodeSectionIR *section,
  const M68kDecodeCandidate *candidate, uint32_t operand_base_offset, uint32_t *out_table_offset);
static int scan_indexed_direct_variable_stub_entries(M68kDecodeIR *decode, uint8_t max_cpu,
  size_t section_index, const M68kDecodeSectionIR *section, uint32_t table_offset, uint8_t **accepted_start,
  uint8_t **accepted_bytes, uint32_t *out_entries, uint32_t entry_limit, uint32_t *out_entry_count);
static int enqueue_code_start_runtime(M68kFactIR *facts, M68kFactsV2WorkQueue *queue,
  M68kFactsV2Profile *profile, size_t section_index, uint32_t offset, uint8_t confidence,
  uint32_t reason, size_t source_section_index, uint32_t source_offset, uint8_t has_runtime_address,
  uint32_t runtime_address, const M68kFactsV2TraceState *trace_state);
static int candidate_is_long_immediate_to_data_register(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
  uint32_t *out_value);
static int candidate_lea_pc_relative_data_target(const M68kDecodeCandidate *candidate, size_t section_index,
  uint32_t section_size, uint8_t *out_reg, uint32_t *out_offset);
static int candidate_lea_platform_section_anchor(const M68kDecodeCandidate *candidate, uint8_t platform_kind,
  uint8_t *out_reg, uint32_t *out_base_offset, int32_t *out_addend);
static int candidate_lea_absolute_address(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
  uint32_t *out_address);
static int candidate_lea_relocated_address(const M68kFactsV2RelocationLookup *relocation_lookup,
  const M68kFactIR *facts, size_t section_index, const M68kDecodeCandidate *candidate, uint8_t *out_reg,
  size_t *out_target_section, uint32_t *out_target_offset);
static int candidate_moves_relocated_address_to_address_register(
  const M68kFactsV2RelocationLookup *relocation_lookup, const M68kFactIR *facts, size_t section_index,
  const M68kDecodeCandidate *candidate, uint8_t *out_reg, size_t *out_target_section,
  uint32_t *out_target_offset);
static int runtime_address_space_add(M68kRuntimeAddressSpace *space, size_t section_index,
  uint32_t source_offset, uint32_t runtime_address, uint32_t size, uint8_t kind, uint8_t confidence,
  M68kFactIR *facts, M68kFactsV2Profile *profile);
static int runtime_address_space_translate(const M68kRuntimeAddressSpace *space, size_t section_index,
  uint32_t runtime_address, uint32_t section_size, uint32_t *out_source_offset);
static int runtime_address_space_section_has_range(const M68kRuntimeAddressSpace *space, size_t section_index);
static int runtime_address_space_source_to_runtime_near(const M68kRuntimeAddressSpace *space, size_t section_index,
  uint32_t source_offset, uint8_t has_current_runtime, uint32_t current_runtime,
  uint32_t *out_runtime_address);
static int resolve_runtime_or_section_target(const M68kRuntimeAddressSpace *space, size_t section_index,
  uint32_t runtime_address, uint32_t section_size, uint32_t *out_source_offset);
static int append_xref_fact(M68kFactIR *facts, size_t section_index, uint32_t source_offset,
  uint32_t target_offset, uint8_t confidence);
static int append_indirect_table_base_runtime_ref(M68kFactIR *facts, size_t section_index,
  const M68kFactsV2TableBaseRef *base_ref);

static int policy_structured_item_matches_section(const M68kAnalysisStructuredDataItem *item,
    size_t section_index) {
  if (item == NULL) return 0;
  if (item->has_section_index) return item->section_index == (uint32_t)section_index;
  return section_index == 0U;
}

static int policy_structured_data_overlaps_range(const M68kAnalysisPolicy *policy, size_t section_index,
    uint32_t start, uint32_t size, uint32_t *out_structured_offset) {
  uint16_t index;
  uint32_t end;
  if (out_structured_offset != NULL) *out_structured_offset = 0U;
  if (policy == NULL || size == 0U || UINT32_MAX - start < size) return 0;
  end = start + size;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    uint32_t item_end;
    if (item->size == 0U || !policy_structured_item_matches_section(item, section_index)) continue;
    if (UINT32_MAX - item->offset < item->size) continue;
    item_end = item->offset + item->size;
    if (start < item_end && end > item->offset) {
      if (out_structured_offset != NULL) *out_structured_offset = item->offset;
      return 1;
    }
  }
  return 0;
}

static double elapsed_seconds_local(clock_t start, clock_t end) {
  return ((double)(end - start)) / (double)CLOCKS_PER_SEC;
}

static void add_elapsed_seconds_local(double *total, clock_t start, clock_t end) {
  if (total != NULL) *total += elapsed_seconds_local(start, end);
}

static clock_t profile_phase_start_local(int enabled) {
  return enabled ? clock() : (clock_t)0;
}

static void profile_phase_add_local(int enabled, double *total, clock_t start) {
  if (enabled) add_elapsed_seconds_local(total, start, clock());
}

static int preview_source_enabled_local(void) {
  const char *value = getenv("AMIGA_REVERSING_FACTS_V2_PREVIEW_SOURCE");
  return value != NULL && strcmp(value, "1") == 0;
}

static int asm_source_enabled_local(void) {
  const char *value = getenv("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE");
  return value != NULL && strcmp(value, "1") == 0;
}

static int reachable_profile_enabled_local(void) {
  const char *value = getenv("AMIGA_REVERSING_FACTS_V2_REACHABLE_PROFILE");
  return value != NULL && strcmp(value, "1") == 0;
}

static int facts_v2_workflow_create(M68kFactsV2Workflow *workflow) {
  if (workflow == NULL) return -1;
  memset(workflow, 0, sizeof(*workflow));
  workflow->arena = arena_create(4096U);
  if (workflow->arena == NULL) return -1;
  workflow->render_preview = (M68kRenderIRPreview *)arena_calloc(workflow->arena, 1U,
    sizeof(*workflow->render_preview));
  if (workflow->render_preview == NULL) return -1;
  m68k_render_ir_preview_init(workflow->render_preview);
  return 0;
}

static void facts_v2_workflow_destroy(M68kFactsV2Workflow *workflow) {
  if (workflow == NULL) return;
  if (workflow->render_preview != NULL) m68k_render_ir_preview_destroy(workflow->render_preview);
  arena_destroy(workflow->arena);
  memset(workflow, 0, sizeof(*workflow));
}

static void work_queue_destroy(M68kFactsV2WorkQueue *queue) {
  if (queue == NULL) return;
  memset(queue, 0, sizeof(*queue));
}

static int work_queue_init_for_decode(M68kFactsV2WorkQueue *queue, const M68kDecodeIR *decode, Arena *arena) {
  size_t section_index;
  if (queue == NULL || decode == NULL || arena == NULL) return -1;
  memset(queue, 0, sizeof(*queue));
  queue->arena = arena;
  queue->section_count = decode->section_count;
  queue->queued_confidence = (uint8_t **)arena_calloc(arena, decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*queue->queued_confidence));
  queue->stateful_heads = (size_t **)arena_calloc(arena, decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*queue->stateful_heads));
  queue->extents = (uint32_t *)arena_calloc(arena, decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*queue->extents));
  if (queue->queued_confidence == NULL || queue->stateful_heads == NULL || queue->extents == NULL) goto fail;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    uint32_t extent = decode->sections[section_index].size;
    queue->extents[section_index] = extent;
    if (extent == 0U) continue;
    queue->queued_confidence[section_index] = (uint8_t *)arena_calloc(arena, extent,
      sizeof(*queue->queued_confidence[section_index]));
    if (queue->queued_confidence[section_index] == NULL) goto fail;
  }
  return 0;
fail:
  work_queue_destroy(queue);
  return -1;
}

static void trace_state_init_unknown(M68kFactsV2TraceState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static int trace_reglist_mask_contains_register(uint16_t mask, uint8_t is_address, uint8_t reg) {
  uint8_t slot;
  if (reg >= 8U) return 0;
  slot = is_address ? (uint8_t)(8U + reg) : reg;
  return (mask & (uint16_t)(1U << slot)) != 0U;
}

static void trace_state_clear_data_register(M68kFactsV2TraceState *state, uint8_t reg) {
  if (state == NULL || reg >= 8U) return;
  trace_value_set_unknown(&state->d[reg]);
  m68k_bitset_u32_clear(&state->d_low16_known, reg);
  m68k_bitset_u32_clear(&state->d_low16_has_origin, reg);
}

static void trace_state_set_data_register_constant(M68kFactsV2TraceState *state, uint8_t reg,
    uint32_t value) {
  if (state == NULL || reg >= 8U) return;
  trace_value_set_constant(&state->d[reg], value);
  m68k_bitset_u32_set(&state->d_low16_known, reg);
  m68k_bitset_u32_clear(&state->d_low16_has_origin, reg);
  state->d_low16[reg] = (uint16_t)(value & 0xFFFFU);
}

static void trace_state_set_data_register_constant_with_origin(M68kFactsV2TraceState *state, uint8_t reg,
    uint32_t value, size_t section_index, uint32_t offset, size_t operand_index) {
  if (state == NULL || reg >= 8U) return;
  trace_value_set_constant_with_origin(&state->d[reg], value, section_index, offset, operand_index);
  m68k_bitset_u32_set(&state->d_low16_known, reg);
  m68k_bitset_u32_set(&state->d_low16_has_origin, reg);
  state->d_low16[reg] = (uint16_t)(value & 0xFFFFU);
  state->d_low16_origin_offset[reg] = offset;
}

static void trace_state_set_data_register_low16(M68kFactsV2TraceState *state, uint8_t reg,
    uint16_t value, uint32_t origin_offset) {
  if (state == NULL || reg >= 8U) return;
  trace_value_set_unknown(&state->d[reg]);
  m68k_bitset_u32_set(&state->d_low16_known, reg);
  m68k_bitset_u32_set(&state->d_low16_has_origin, reg);
  state->d_low16[reg] = value;
  state->d_low16_origin_offset[reg] = origin_offset;
}

static int trace_state_matches_queued(const M68kFactsV2TraceState *queued,
    const M68kFactsV2TraceState *incoming) {
  M68kFactsV2TraceState unknown;
  if (queued == NULL) return incoming == NULL;
  if (incoming != NULL) return memcmp(queued, incoming, sizeof(*queued)) == 0;
  trace_state_init_unknown(&unknown);
  return memcmp(queued, &unknown, sizeof(*queued)) == 0;
}

static size_t *work_queue_stateful_head_slot(M68kFactsV2WorkQueue *queue, size_t section_index,
    uint32_t offset) {
  if (queue == NULL || section_index >= queue->section_count || queue->stateful_heads == NULL ||
      queue->extents == NULL || offset >= queue->extents[section_index]) {
    return NULL;
  }
  if (queue->stateful_heads[section_index] == NULL) {
    uint32_t extent = queue->extents[section_index];
    queue->stateful_heads[section_index] = (size_t *)arena_calloc(queue->arena, extent != 0U ? extent : 1U,
      sizeof(*queue->stateful_heads[section_index]));
  }
  if (queue->stateful_heads[section_index] == NULL) return NULL;
  return &queue->stateful_heads[section_index][offset];
}

static int work_queue_grow_items(M68kFactsV2WorkQueue *queue, size_t next_capacity) {
  M68kFactsV2WorkItem *grown_items;
  size_t *grown_next;
  size_t old_capacity;
  if (queue == NULL || next_capacity <= queue->capacity) return 0;
  old_capacity = queue->capacity;
  grown_items = (M68kFactsV2WorkItem *)arena_realloc_copy(queue->arena, queue->items,
    old_capacity * sizeof(*queue->items), next_capacity * sizeof(*grown_items));
  if (grown_items == NULL) return -1;
  queue->items = grown_items;
  grown_next = (size_t *)arena_realloc_copy(queue->arena, queue->stateful_next,
    old_capacity * sizeof(*queue->stateful_next), next_capacity * sizeof(*grown_next));
  if (grown_next == NULL) return -1;
  queue->stateful_next = grown_next;
  memset(queue->stateful_next + old_capacity, 0, (next_capacity - old_capacity) * sizeof(*queue->stateful_next));
  queue->capacity = next_capacity;
  queue->stateful_next_capacity = next_capacity;
  return 0;
}

static int work_queue_existing_stateful_item_matches(const M68kFactsV2WorkItem *item, size_t section_index,
    uint32_t offset, uint8_t confidence, uint8_t has_runtime_address, uint32_t runtime_address) {
  if (item == NULL || item->section_index != section_index || item->offset != offset ||
      item->has_runtime_address != has_runtime_address || item->confidence < confidence) {
    return 0;
  }
  return has_runtime_address == 0U || item->runtime_address == runtime_address;
}

static int trace_value_is_target_set(const M68kFactsV2TraceValue *value) {
  return value != NULL && value->kind == M68K_FACTS_V2_TRACE_TARGET_SET && value->target_count != 0U;
}

static int trace_value_can_drive_indirect_control(const M68kFactsV2TraceValue *value) {
  if (value == NULL) return 0;
  return value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET ||
    value->kind == M68K_FACTS_V2_TRACE_TARGET_SET ||
    value->kind == M68K_FACTS_V2_TRACE_WORD_RELATIVE_TABLE ||
    value->kind == M68K_FACTS_V2_TRACE_KEYED_LONG_RELATIVE_TABLE;
}

static int trace_state_can_drive_indirect_control(const M68kFactsV2TraceState *state) {
  uint8_t reg;
  if (state == NULL) return 0;
  if (state->copied_entry_valid) return 1;
  for (reg = 0U; reg < 8U; ++reg) {
    if (trace_value_can_drive_indirect_control(&state->a[reg])) return 1;
    if (trace_value_is_target_set(&state->d[reg]) ||
        state->d[reg].kind == M68K_FACTS_V2_TRACE_WORD_RELATIVE_TABLE ||
        state->d[reg].kind == M68K_FACTS_V2_TRACE_KEYED_LONG_RELATIVE_TABLE) {
      return 1;
    }
  }
  return 0;
}

static int trace_value_can_drive_runtime_sink(uint8_t platform_kind, const M68kFactsV2TraceValue *value) {
  uint32_t displacement;
  if (value == NULL ||
      (value->kind != M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS && value->kind != M68K_FACTS_V2_TRACE_CONSTANT)) {
    return 0;
  }
  for (displacement = 0U; displacement <= 0x1FEU; displacement += 2U) {
    if (value->value <= UINT32_MAX - displacement &&
        platform_facts_v2_is_runtime_address_sink(platform_kind, value->value + displacement)) {
      return 1;
    }
  }
  return 0;
}

static int trace_state_can_drive_runtime_sink(uint8_t platform_kind, const M68kFactsV2TraceState *state) {
  uint8_t reg;
  if (state == NULL) return 0;
  for (reg = 0U; reg < 8U; ++reg) {
    if (trace_value_can_drive_runtime_sink(platform_kind, &state->a[reg])) return 1;
  }
  return 0;
}

static int work_queue_push(M68kFactsV2WorkQueue *queue, size_t section_index, uint32_t offset,
    uint8_t confidence, uint32_t reason, size_t source_section_index, uint32_t source_offset,
    uint8_t has_runtime_address, uint32_t runtime_address, const M68kFactsV2TraceState *trace_state,
    uint8_t allow_trace_variant) {
  size_t item_index;
  size_t state_variant_count = 0U;
  size_t state_variant_limit;
  uint8_t saw_branch_merge_variant_anchor = 0U;
  size_t *stateful_head_slot = NULL;
  int is_stateful;
  int carries_indirect_control_state;
  if (queue == NULL) return -1;
  carries_indirect_control_state = trace_state_can_drive_indirect_control(trace_state);
  is_stateful = has_runtime_address != 0U || allow_trace_variant;
  state_variant_limit = allow_trace_variant && carries_indirect_control_state
    ? M68K_FACTS_V2_TRACE_INDIRECT_STATE_VARIANT_LIMIT
    : M68K_FACTS_V2_TRACE_STATE_VARIANT_LIMIT;
  if (!is_stateful && section_index < queue->section_count && queue->queued_confidence != NULL &&
      queue->extents != NULL && queue->queued_confidence[section_index] != NULL &&
      offset < queue->extents[section_index]) {
    if (queue->queued_confidence[section_index][offset] >= confidence) return 0;
    queue->queued_confidence[section_index][offset] = confidence;
  }
  if (is_stateful) {
    stateful_head_slot = work_queue_stateful_head_slot(queue, section_index, offset);
    if (stateful_head_slot == NULL) return -1;
    for (item_index = *stateful_head_slot; item_index != 0U; item_index = queue->stateful_next[item_index - 1U]) {
      const M68kFactsV2WorkItem *item = &queue->items[item_index - 1U];
      if (!work_queue_existing_stateful_item_matches(item, section_index, offset, confidence,
          has_runtime_address, runtime_address)) continue;
      ++state_variant_count;
      if (trace_state_matches_queued(&item->trace_state, trace_state)) return 0;
      if ((reason == M68K_FACT_CODE_START_REASON_FALLTHROUGH &&
           item->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET) ||
          (reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET &&
           item->reason == M68K_FACT_CODE_START_REASON_FALLTHROUGH)) {
        uint32_t source_delta = source_offset > item->source_offset
          ? source_offset - item->source_offset
          : item->source_offset - source_offset;
        if (source_section_index == item->source_section_index && source_delta <= 32U)
          saw_branch_merge_variant_anchor = 1U;
      }
    }
    if (state_variant_count != 0U && !saw_branch_merge_variant_anchor &&
        !(allow_trace_variant && carries_indirect_control_state))
      return 0;
    if (state_variant_count >= state_variant_limit) return 0;
  }
  if (queue->count == queue->capacity) {
    size_t next_capacity = queue->capacity == 0U ? 64U : queue->capacity * 2U;
    if (work_queue_grow_items(queue, next_capacity) != 0) return -1;
  }
  queue->items[queue->count].section_index = section_index;
  queue->items[queue->count].offset = offset;
  queue->items[queue->count].reason = reason;
  queue->items[queue->count].source_section_index = source_section_index;
  queue->items[queue->count].source_offset = source_offset;
  queue->items[queue->count].confidence = confidence;
  queue->items[queue->count].has_runtime_address = has_runtime_address;
  queue->items[queue->count].allow_trace_variant = allow_trace_variant;
  queue->items[queue->count].runtime_address = runtime_address;
  if (trace_state != NULL) queue->items[queue->count].trace_state = *trace_state;
  else trace_state_init_unknown(&queue->items[queue->count].trace_state);
  if (is_stateful) {
    if (stateful_head_slot == NULL) return -1;
    queue->stateful_next[queue->count] = *stateful_head_slot;
    *stateful_head_slot = queue->count + 1U;
  } else if (queue->stateful_next != NULL && queue->count < queue->stateful_next_capacity) {
    queue->stateful_next[queue->count] = 0U;
  }
  ++queue->count;
  return 0;
}

static int work_queue_pop(M68kFactsV2WorkQueue *queue, M68kFactsV2WorkItem *out_item) {
  if (queue == NULL || out_item == NULL || queue->cursor >= queue->count) return 0;
  *out_item = queue->items[queue->cursor++];
  return 1;
}

static void relocation_lookup_destroy(M68kFactsV2RelocationLookup *lookup) {
  if (lookup == NULL) return;
  memset(lookup, 0, sizeof(*lookup));
}

static int relocation_lookup_build(M68kFactsV2RelocationLookup *lookup, const M68kDecodeIR *decode,
    const M68kFactIR *facts, Arena *arena) {
  size_t section_index;
  size_t fact_index;
  if (lookup == NULL || decode == NULL || facts == NULL || arena == NULL) return -1;
  memset(lookup, 0, sizeof(*lookup));
  lookup->section_count = decode->section_count;
  lookup->indices = (size_t **)arena_calloc(arena, decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*lookup->indices));
  lookup->extents = (uint32_t *)arena_calloc(arena, decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*lookup->extents));
  if (lookup->indices == NULL || lookup->extents == NULL) goto fail;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    uint32_t extent = section->size;
    uint32_t offset;
    lookup->extents[section_index] = extent;
    if (extent == 0U) continue;
    lookup->indices[section_index] = (size_t *)arena_alloc(arena,
      (size_t)extent * sizeof(*lookup->indices[section_index]));
    if (lookup->indices[section_index] == NULL) goto fail;
    for (offset = 0U; offset < extent; ++offset) lookup->indices[section_index][offset] = SIZE_MAX;
  }
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    if (fact->kind != M68K_FACT_RELOCATION_REF || fact->section_index >= decode->section_count) continue;
    if (fact->offset >= lookup->extents[fact->section_index] ||
        lookup->indices[fact->section_index] == NULL) continue;
    if (lookup->indices[fact->section_index][fact->offset] == SIZE_MAX)
      lookup->indices[fact->section_index][fact->offset] = fact_index;
  }
  return 0;
fail:
  relocation_lookup_destroy(lookup);
  return -1;
}

static const M68kFact *relocation_lookup_ref_at(const M68kFactsV2RelocationLookup *lookup,
    const M68kFactIR *facts, size_t section_index, uint32_t offset) {
  size_t fact_index;
  if (lookup == NULL || facts == NULL || section_index >= lookup->section_count ||
      lookup->indices == NULL || lookup->extents == NULL || offset >= lookup->extents[section_index] ||
      lookup->indices[section_index] == NULL) {
    return NULL;
  }
  fact_index = lookup->indices[section_index][offset];
  if (fact_index == SIZE_MAX || fact_index >= facts->fact_count) return NULL;
  return &facts->facts[fact_index];
}

static uint32_t decode_section_extent_local(const M68kDecodeSectionIR *section) {
  if (section == NULL) return 0U;
  return section->allocation_size > section->size ? section->allocation_size : section->size;
}

static void label_lookup_destroy(M68kFactsV2LabelLookup *lookup) {
  if (lookup == NULL) return;
  memset(lookup, 0, sizeof(*lookup));
}

static int label_lookup_build(M68kFactsV2LabelLookup *lookup, const M68kDecodeIR *decode, Arena *arena) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || arena == NULL) return -1;
  memset(lookup, 0, sizeof(*lookup));
  lookup->section_count = decode->section_count;
  lookup->labels = (uint8_t **)arena_calloc(arena, decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*lookup->labels));
  lookup->extents = (uint32_t *)arena_calloc(arena, decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*lookup->extents));
  if (lookup->labels == NULL || lookup->extents == NULL) goto fail;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    uint32_t extent = decode_section_extent_local(&decode->sections[section_index]);
    lookup->extents[section_index] = extent;
    lookup->labels[section_index] = (uint8_t *)arena_calloc(arena, (size_t)extent + 1U,
      sizeof(*lookup->labels[section_index]));
    if (lookup->labels[section_index] == NULL) goto fail;
  }
  return 0;
fail:
  label_lookup_destroy(lookup);
  return -1;
}

static int label_lookup_has_label(const M68kFactsV2LabelLookup *lookup, const M68kFactIR *facts,
    size_t section_index, uint32_t offset) {
  if (lookup != NULL && section_index < lookup->section_count && lookup->labels != NULL &&
      lookup->extents != NULL && lookup->labels[section_index] != NULL &&
      offset <= lookup->extents[section_index]) {
    return lookup->labels[section_index][offset] != 0U;
  }
  return m68k_fact_ir_has_label(facts, section_index, offset);
}

static int label_lookup_create_label(M68kFactsV2LabelLookup *lookup, M68kFactIR *facts,
    size_t section_index, uint32_t offset, uint8_t confidence) {
  M68kFact fact;
  if (facts == NULL) return -1;
  if (label_lookup_has_label(lookup, facts, section_index, offset)) return 0;
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_LABEL_CREATED;
  fact.confidence = confidence;
  fact.section_index = section_index;
  fact.offset = offset;
  if (m68k_fact_ir_append(facts, &fact) != 0) return -1;
  if (lookup != NULL && section_index < lookup->section_count && lookup->labels != NULL &&
      lookup->extents != NULL && lookup->labels[section_index] != NULL &&
      offset <= lookup->extents[section_index]) {
    lookup->labels[section_index][offset] = 1U;
  }
  return 0;
}

static const M68kDecodeCandidate *ensure_candidate_at_offset(M68kDecodeIR *decode,
    const M68kDecodeSectionIR *section, uint32_t offset, uint8_t max_cpu) {
  const M68kDecodeCandidate *candidate = NULL;
  if (decode == NULL || section == NULL) return NULL;
  if (m68k_decode_ir_ensure_candidate_at(decode, section->section_index, offset, max_cpu, &candidate,
      m68k_diag_sink(NULL)) != 0) {
    return NULL;
  }
  return candidate;
}

static int accepted_offset_is_interior(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const uint8_t *accepted_bytes, uint32_t offset) {
  if (section == NULL || accepted_start == NULL || accepted_bytes == NULL || offset >= section->size)
    return 0;
  return accepted_bytes[offset] != 0U && accepted_start[offset] == 0U;
}

static int accepted_range_has_code_byte_local(const uint8_t *accepted_bytes, uint32_t section_size,
    uint32_t offset, uint32_t size) {
  uint32_t cursor;
  if (accepted_bytes == NULL || size == 0U || offset > section_size || size > section_size - offset) return 1;
  for (cursor = 0U; cursor < size; ++cursor) {
    if (accepted_bytes[offset + cursor] != 0U) return 1;
  }
  return 0;
}

static void accepted_candidate_index_destroy(M68kAcceptedCandidateIndex *index) {
  if (index == NULL) return;
  if (index->has_mark && index->arena != NULL) arena_rewind(index->arena, index->mark);
  memset(index, 0, sizeof(*index));
}

static int accepted_candidate_index_build(M68kAcceptedCandidateIndex *index, const M68kDecodeIR *decode,
    uint8_t **accepted_start, Arena *arena) {
  size_t section_index;
  if (index == NULL || decode == NULL || accepted_start == NULL || arena == NULL) return -1;
  accepted_candidate_index_destroy(index);
  index->arena = arena;
  index->mark = arena_mark(arena);
  index->has_mark = 1U;
  index->section_count = decode->section_count;
  index->sections = (M68kAcceptedSectionIndex *)arena_calloc(arena,
    decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*index->sections));
  if (index->sections == NULL) goto fail;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kAcceptedSectionIndex *section_indexed = &index->sections[section_index];
    size_t candidate_index;
    size_t accepted_count = 0U;
    if (accepted_start[section_index] == NULL) continue;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      if (candidate->offset < section->size && accepted_start[section_index][candidate->offset])
        ++accepted_count;
    }
    if (accepted_count == 0U) continue;
    section_indexed->candidates = (const M68kDecodeCandidate **)arena_alloc(arena,
      accepted_count * sizeof(*section_indexed->candidates));
    if (section_indexed->candidates == NULL) goto fail;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      if (candidate->offset < section->size && accepted_start[section_index][candidate->offset])
        section_indexed->candidates[section_indexed->count++] = candidate;
    }
  }
  return 0;
fail:
  accepted_candidate_index_destroy(index);
  return -1;
}

static const M68kDecodeCandidate *accepted_candidate_index_covering(const M68kAcceptedCandidateIndex *index,
    const uint8_t *accepted_start,
    size_t section_index, uint32_t offset, int interior_only) {
  const M68kAcceptedSectionIndex *section_indexed;
  const M68kDecodeCandidate *candidate;
  size_t lo = 0U;
  size_t hi;
  uint32_t candidate_end;
  if (index == NULL || accepted_start == NULL || section_index >= index->section_count ||
      index->sections == NULL) {
    return NULL;
  }
  section_indexed = &index->sections[section_index];
  if (section_indexed->candidates == NULL || section_indexed->count == 0U) return NULL;
  hi = section_indexed->count;
  while (lo < hi) {
    size_t mid = lo + ((hi - lo) / 2U);
    if (section_indexed->candidates[mid]->offset <= offset) lo = mid + 1U;
    else hi = mid;
  }
  if (lo == 0U) return NULL;
  candidate = section_indexed->candidates[lo - 1U];
  if (candidate == NULL || !accepted_start[candidate->offset]) return NULL;
  if (candidate->byte_count == 0U || candidate->offset > UINT32_MAX - candidate->byte_count) return NULL;
  candidate_end = candidate->offset + candidate->byte_count;
  if (offset < candidate->offset || offset >= candidate_end) return NULL;
  if (interior_only && offset <= candidate->offset) return NULL;
  return candidate;
}

static void profile_record_code_start(M68kFactsV2Profile *profile, uint32_t reason) {
  if (profile == NULL) return;
  ++profile->code_start_facts;
  switch (reason) {
    case M68K_FACT_CODE_START_REASON_SECTION_ENTRY:
      ++profile->code_start_section_entries;
      break;
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET:
      ++profile->code_start_policy_entry_offsets;
      break;
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT:
      ++profile->code_start_policy_entry_points;
      break;
    case M68K_FACT_CODE_START_REASON_CONTROL_TARGET:
      ++profile->code_start_control_targets;
      break;
    case M68K_FACT_CODE_START_REASON_FALLTHROUGH:
      ++profile->code_start_fallthroughs;
      break;
    case M68K_FACT_CODE_START_REASON_INLINE_RESUME:
      ++profile->code_start_inline_resumes;
      break;
    case M68K_FACT_CODE_START_REASON_LINKAGE_API_ENTRY:
      ++profile->code_start_linkage_api_entries;
      break;
    case M68K_FACT_CODE_START_REASON_PLATFORM_LOADSEG_ENTRY:
      ++profile->code_start_platform_loadseg_entries;
      break;
    case M68K_FACT_CODE_START_REASON_STACK_CONTINUATION:
      ++profile->code_start_stack_continuations;
      break;
    case M68K_FACT_CODE_START_REASON_BOUNDARY_API_ENTRY:
      ++profile->code_start_boundary_api_entries;
      break;
    default:
      break;
  }
}

static void profile_record_platform_loadseg_segment_link_access(M68kFactsV2Profile *profile,
    size_t section_index, uint32_t offset, uint8_t resolved_target, size_t target_section_index) {
  if (profile == NULL) return;
  if (profile->platform_loadseg_segment_link_accesses == 0U) {
    profile->first_platform_loadseg_segment_link_section = (uint32_t)section_index;
    profile->first_platform_loadseg_segment_link_offset = offset;
    profile->first_platform_loadseg_segment_link_target_section = resolved_target
      ? (uint32_t)target_section_index
      : UINT32_MAX;
  }
  ++profile->platform_loadseg_segment_link_accesses;
  ++profile->platform_loadseg_segment_link_bptr_loads;
  if (resolved_target) ++profile->platform_loadseg_segment_link_resolved_targets;
}

static int append_code_start_fact(M68kFactIR *facts, size_t section_index, uint32_t offset, uint8_t confidence,
    uint32_t reason, size_t source_section_index, uint32_t source_offset, uint8_t has_runtime_address,
    uint32_t runtime_address) {
  M68kFact fact;
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_CODE_START;
  fact.confidence = confidence;
  fact.section_index = section_index;
  fact.offset = offset;
  fact.reason = reason;
  fact.has_runtime_address = has_runtime_address;
  fact.runtime_address = runtime_address;
  fact.source_section_index = source_section_index;
  fact.source_offset = source_offset;
  return m68k_fact_ir_append(facts, &fact);
}

static int enqueue_code_start(M68kFactIR *facts, M68kFactsV2WorkQueue *queue, M68kFactsV2Profile *profile,
    size_t section_index, uint32_t offset, uint8_t confidence, uint32_t reason,
    size_t source_section_index, uint32_t source_offset) {
  return enqueue_code_start_runtime(facts, queue, profile, section_index, offset, confidence, reason,
    source_section_index, source_offset, 0U, 0U, NULL);
}

static int enqueue_code_start_runtime_ex(M68kFactIR *facts, M68kFactsV2WorkQueue *queue,
    M68kFactsV2Profile *profile, size_t section_index, uint32_t offset, uint8_t confidence,
    uint32_t reason, size_t source_section_index, uint32_t source_offset, uint8_t has_runtime_address,
    uint32_t runtime_address, const M68kFactsV2TraceState *trace_state, uint8_t allow_trace_variant) {
  if (append_code_start_fact(facts, section_index, offset, confidence, reason, source_section_index,
      source_offset, has_runtime_address, runtime_address) != 0) {
    return -1;
  }
  profile_record_code_start(profile, reason);
  if (profile != NULL && has_runtime_address) ++profile->runtime_address_view_starts;
  return work_queue_push(queue, section_index, offset, confidence, reason, source_section_index,
    source_offset, has_runtime_address, runtime_address, trace_state, allow_trace_variant);
}

static int enqueue_code_start_runtime(M68kFactIR *facts, M68kFactsV2WorkQueue *queue,
    M68kFactsV2Profile *profile, size_t section_index, uint32_t offset, uint8_t confidence,
    uint32_t reason, size_t source_section_index, uint32_t source_offset, uint8_t has_runtime_address,
    uint32_t runtime_address, const M68kFactsV2TraceState *trace_state) {
  return enqueue_code_start_runtime_ex(facts, queue, profile, section_index, offset, confidence, reason,
    source_section_index, source_offset, has_runtime_address, runtime_address, trace_state, 0U);
}

static uint32_t fixup_width_bytes_local(const M68kFixup *fixup) {
  if (fixup == NULL) return 0U;
  switch (fixup->width) {
    case M68K_FIXUP_WIDTH_8: return 1U;
    case M68K_FIXUP_WIDTH_16: return 2U;
    case M68K_FIXUP_WIDTH_32: return 4U;
    default: return 0U;
  }
}

static int fixup_payload_fits_section_data_local(const M68kSection *section, const M68kFixup *fixup) {
  uint32_t width = fixup_width_bytes_local(fixup);
  if (section == NULL || fixup == NULL || width == 0U) return 0;
  if (fixup->offset > section->data_size) return 0;
  return width <= section->data_size - fixup->offset;
}

static int read_fixup_payload_raw_local(const M68kSection *section, const M68kFixup *fixup,
    uint32_t *out_raw_value) {
  uint32_t width;
  if (out_raw_value != NULL) *out_raw_value = 0U;
  if (section == NULL || fixup == NULL || out_raw_value == NULL) return 0;
  width = fixup_width_bytes_local(fixup);
  if (width == 0U || !fixup_payload_fits_section_data_local(section, fixup)) return 0;
  if (width == 1U) *out_raw_value = section->data[fixup->offset];
  else if (width == 2U) *out_raw_value = m68k_read_u16be(section->data + fixup->offset);
  else *out_raw_value = m68k_read_u32be(section->data + fixup->offset);
  return 1;
}

static void relocation_failure_init(M68kFactsV2RelocationFailure *failure, const M68kFixup *fixup) {
  if (failure == NULL) return;
  memset(failure, 0, sizeof(*failure));
  failure->computed_target = -1;
  if (fixup == NULL) return;
  failure->section = (uint32_t)fixup->section_index;
  failure->offset = fixup->offset;
  failure->target_section = (uint32_t)fixup->target_section_index;
  failure->width = fixup_width_bytes_local(fixup);
  failure->platform_record_kind = fixup->platform_relocation_record_kind;
}

static void relocation_failure_set(M68kFactsV2RelocationFailure *failure, uint32_t reason,
    uint32_t raw_value, int64_t computed_target) {
  if (failure == NULL) return;
  failure->reason = reason;
  failure->raw_value = raw_value;
  failure->computed_target = computed_target;
}

static void profile_record_relocation_failure(M68kFactsV2Profile *profile,
    const M68kFactsV2RelocationFailure *failure) {
  if (profile == NULL) return;
  if (profile->relocation_failures == 0U && failure != NULL) {
    profile->first_relocation_failure_reason = failure->reason;
    profile->first_relocation_failure_section = failure->section;
    profile->first_relocation_failure_offset = failure->offset;
    profile->first_relocation_failure_target_section = failure->target_section;
    profile->first_relocation_failure_width = failure->width;
    profile->first_relocation_failure_raw_value = failure->raw_value;
    profile->first_relocation_failure_computed_target = failure->computed_target;
  }
  ++profile->relocation_failures;
}

static void profile_record_relocation_anchor(M68kFactsV2Profile *profile,
    const M68kFactsV2RelocationFailure *anchor) {
  if (profile == NULL) return;
  if (profile->relocation_anchors == 0U && anchor != NULL) {
    profile->first_relocation_anchor_kind = anchor->anchor_kind;
    profile->first_relocation_anchor_section = anchor->section;
    profile->first_relocation_anchor_offset = anchor->offset;
    profile->first_relocation_anchor_target_section = anchor->target_section;
    profile->first_relocation_anchor_width = anchor->width;
    profile->first_relocation_anchor_platform_record_kind = anchor->platform_record_kind;
    profile->first_relocation_anchor_raw_value = anchor->raw_value;
    profile->first_relocation_anchor_addend = anchor->computed_target;
  }
  ++profile->relocation_anchors;
}

static uint32_t classify_out_of_range_relocation_anchor(const M68kObject *object,
    const M68kFixup *fixup, uint32_t width, uint32_t raw_value) {
  uint32_t platform_anchor;
  if (object == NULL || fixup == NULL) return M68K_FACTS_V2_RELOCATION_ANCHOR_NONE;
  platform_anchor = platform_facts_v2_relocation_anchor_kind(object->platform_backend_kind,
    object->platform_file_kind, fixup->kind, width, raw_value);
  switch (platform_anchor) {
  case PLATFORM_FACTS_V2_RELOCATION_ANCHOR_NEGATIVE:
    return M68K_FACTS_V2_RELOCATION_ANCHOR_NEGATIVE;
  case PLATFORM_FACTS_V2_RELOCATION_ANCHOR_POSITIVE:
    return M68K_FACTS_V2_RELOCATION_ANCHOR_POSITIVE;
  default:
    return M68K_FACTS_V2_RELOCATION_ANCHOR_NONE;
  }
}

static int facts_v2_fixup_addend_is_platform_normalized_target(const M68kObject *object,
    const M68kFixup *fixup, uint32_t width, uint32_t target_extent, uint32_t *out_offset) {
  if (object == NULL || fixup == NULL || out_offset == NULL) return 0;
  return platform_facts_v2_fixup_addend_is_normalized_target(object->platform_backend_kind,
    object->platform_file_kind, fixup->kind, fixup->has_target_section != 0, fixup->addend, width, target_extent,
    out_offset);
}

static int facts_v2_first_section_of_kind(const M68kObject *object, M68kSectionKind kind,
    size_t *out_index, const M68kSection **out_section) {
  size_t index;
  if (object == NULL) return 0;
  for (index = 0U; index < object->section_count; ++index) {
    if (object->sections[index].kind != kind) continue;
    if (out_index != NULL) *out_index = index;
    if (out_section != NULL) *out_section = &object->sections[index];
    return 1;
  }
  return 0;
}

static int facts_v2_platform_image_offset_target(const M68kObject *object, const M68kFixup *fixup,
    uint32_t raw_value, size_t *out_section_index, uint32_t *out_offset) {
  size_t text_index = 0U;
  size_t data_index = 0U;
  size_t bss_index = 0U;
  const M68kSection *text_section = NULL;
  const M68kSection *data_section = NULL;
  const M68kSection *bss_section = NULL;
  uint8_t target_kind = PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_NONE;
  uint32_t target_offset = 0U;
  if (object == NULL || fixup == NULL || out_section_index == NULL || out_offset == NULL) return 0;
  if (!facts_v2_first_section_of_kind(object, M68K_SECTION_CODE, &text_index, &text_section) ||
      !facts_v2_first_section_of_kind(object, M68K_SECTION_DATA, &data_index, &data_section)) {
    return 0;
  }
  (void)facts_v2_first_section_of_kind(object, M68K_SECTION_BSS, &bss_index, &bss_section);
  if (!platform_facts_v2_image_offset_target(object->platform_backend_kind, object->platform_file_kind,
      fixup->kind, fixup_width_bytes_local(fixup), raw_value, text_section->size, data_section->size,
      bss_section != NULL, bss_section != NULL ? bss_section->size : 0U, &target_kind, &target_offset)) {
    return 0;
  }
  switch (target_kind) {
  case PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_CODE:
    *out_section_index = text_index;
    *out_offset = target_offset;
    return 1;
  case PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_DATA:
    *out_section_index = data_index;
    *out_offset = target_offset;
    return 1;
  case PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_BSS:
    if (bss_section == NULL) return 0;
    *out_section_index = bss_index;
    *out_offset = target_offset;
    return 1;
  default:
    return 0;
  }
}

static int seed_runtime_address_space_from_policy(const M68kObject *object, const M68kAnalysisPolicy *policy,
    M68kRuntimeAddressSpace *runtime_addresses, M68kFactIR *facts, M68kFactsV2Profile *profile) {
  uint16_t range_index;
  if (object == NULL || policy == NULL || runtime_addresses == NULL) return -1;
  for (range_index = 0U; range_index < policy->runtime_range_count &&
       range_index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++range_index) {
    const M68kAnalysisRuntimeRange *range = &policy->runtime_ranges[range_index];
    size_t section_index = range->has_section_index ? range->section_index : 0U;
    const M68kSection *section;
    uint32_t extent;
    uint32_t size;
    if (section_index >= object->section_count) continue;
    section = &object->sections[section_index];
    extent = section->size != 0U ? section->size : section->data_size;
    if (range->offset >= extent) continue;
    size = range->size != 0U && range->size <= extent - range->offset ? range->size : extent - range->offset;
    if (runtime_address_space_add(runtime_addresses, section_index, range->offset, range->runtime_address,
        size, M68K_FACT_RUNTIME_RANGE_KIND_POLICY, M68K_FACT_CONFIDENCE_REQUIRED, facts, profile) != 0) {
      return -1;
    }
  }
  return 0;
}

static int facts_v2_fixup_target_offset(const M68kObject *object, const M68kFixup *fixup,
    uint32_t *out_offset, M68kFactsV2RelocationFailure *out_failure) {
  const M68kSection *source_section;
  const M68kSection *target_section;
  uint32_t target_extent, width, target;
  uint32_t raw_value = 0U;
  int32_t signed_value = 0;
  int64_t computed_target = -1;
  relocation_failure_init(out_failure, fixup);
  if (object == NULL || fixup == NULL || out_offset == NULL || !fixup->has_target_section ||
      fixup->section_index >= object->section_count || fixup->target_section_index >= object->section_count) {
    relocation_failure_set(out_failure, M68K_FACTS_V2_RELOCATION_FAILURE_INVALID_FIXUP, 0U, -1);
    return 0;
  }
  source_section = &object->sections[fixup->section_index];
  target_section = &object->sections[fixup->target_section_index];
  target_extent = target_section->size != 0U ? target_section->size : target_section->data_size;
  width = fixup_width_bytes_local(fixup);
  if (width == 0U) {
    relocation_failure_set(out_failure, M68K_FACTS_V2_RELOCATION_FAILURE_BAD_WIDTH, 0U, -1);
    return 0;
  }
  if (!fixup_payload_fits_section_data_local(source_section, fixup)) {
    relocation_failure_set(out_failure, M68K_FACTS_V2_RELOCATION_FAILURE_PAYLOAD_OUT_OF_DATA, 0U, -1);
    return 0;
  }
  if (width == 1U) {
    raw_value = source_section->data[fixup->offset];
    signed_value = (int8_t)raw_value;
  } else if (width == 2U) {
    raw_value = m68k_read_u16be(source_section->data + fixup->offset);
    signed_value = (int16_t)raw_value;
  } else {
    raw_value = m68k_read_u32be(source_section->data + fixup->offset);
    signed_value = (int32_t)raw_value;
  }
  if (fixup->kind == M68K_FIXUP_PC_REL) computed_target = (int64_t)fixup->offset + (int64_t)signed_value;
  else if (fixup->kind == M68K_FIXUP_ABS || fixup->kind == M68K_FIXUP_SECTION_REL) computed_target = raw_value;
  else {
    relocation_failure_set(out_failure, M68K_FACTS_V2_RELOCATION_FAILURE_UNSUPPORTED_KIND, raw_value, -1);
    return 0;
  }
  if (computed_target >= 0 && computed_target <= UINT32_MAX) target = (uint32_t)computed_target;
  else target = UINT32_MAX;
  if (target > target_extent) {
    if (facts_v2_fixup_addend_is_platform_normalized_target(object, fixup, width, target_extent, &target)) {
      *out_offset = target;
      return 1;
    }
    uint32_t anchor_kind = classify_out_of_range_relocation_anchor(object, fixup, width, raw_value);
    if (out_failure != NULL) out_failure->anchor_kind = anchor_kind;
    if (anchor_kind != M68K_FACTS_V2_RELOCATION_ANCHOR_NONE) {
      int64_t addend = anchor_kind == M68K_FACTS_V2_RELOCATION_ANCHOR_NEGATIVE
        ? (int64_t)(int32_t)raw_value
        : computed_target;
      relocation_failure_set(out_failure, M68K_FACTS_V2_RELOCATION_FAILURE_NONE, raw_value, addend);
    } else {
      relocation_failure_set(out_failure, M68K_FACTS_V2_RELOCATION_FAILURE_TARGET_OUT_OF_RANGE, raw_value,
        computed_target);
    }
    return 0;
  }
  *out_offset = target;
  return 1;
}

static int seed_facts_from_object(const M68kObject *object, const M68kAnalysisPolicy *policy,
    M68kFactIR *facts, M68kFactsV2LabelLookup *label_lookup, M68kFactsV2WorkQueue *queue,
    M68kRuntimeAddressSpace *runtime_addresses, M68kFactsV2Profile *profile) {
  size_t section_index, fixup_index, entry_index, label_index, symbol_index;
  size_t implicit_entry_section = (size_t)-1;
  if (object == NULL || policy == NULL || facts == NULL || label_lookup == NULL ||
      queue == NULL || runtime_addresses == NULL || profile == NULL)
    return -1;
  if (seed_runtime_address_space_from_policy(object, policy, runtime_addresses, facts, profile) != 0) return -1;
  /* A normal implicit executable entry belongs to the first section only. Later
     code sections need explicit policy, metadata, or analysis-discovered flow. */
  if (!policy->disable_implicit_entry_points && !policy->has_entry_offset &&
      object->section_count != 0U) {
    const M68kSection *entry_section = &object->sections[0];
    if (entry_section->kind == M68K_SECTION_CODE && entry_section->data_size != 0U)
      implicit_entry_section = 0U;
  }
  for (section_index = 0U; section_index < object->section_count; ++section_index) {
    const M68kSection *section = &object->sections[section_index];
    M68kFact fact;
    memset(&fact, 0, sizeof(fact));
    if (section->kind == M68K_SECTION_CODE && section->data_size != 0U &&
        section_index == implicit_entry_section) {
      if (enqueue_code_start(facts, queue, profile, section_index, 0U, M68K_FACT_CONFIDENCE_REQUIRED,
          M68K_FACT_CODE_START_REASON_SECTION_ENTRY, section_index, 0U) != 0) return -1;
      if (label_lookup_create_label(label_lookup, facts, section_index, 0U,
          M68K_FACT_CONFIDENCE_REQUIRED) != 0) return -1;
    } else if (section->data_size != 0U || section->size != 0U) {
      fact.kind = M68K_FACT_DATA_SPAN;
      fact.confidence = M68K_FACT_CONFIDENCE_REQUIRED;
      fact.section_index = section_index;
      fact.size = section->data_size != 0U ? section->data_size : section->size;
      if (m68k_fact_ir_append(facts, &fact) != 0) return -1;
    }
  }
  if (policy->has_entry_offset && object->section_count != 0U) {
    const M68kSection *section = &object->sections[0];
    uint32_t extent = section->size != 0U ? section->size : section->data_size;
    if (policy->entry_offset <= extent) {
      if (enqueue_code_start(facts, queue, profile, 0U, policy->entry_offset, M68K_FACT_CONFIDENCE_REQUIRED,
          M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET, 0U, policy->entry_offset) != 0) return -1;
      if (label_lookup_create_label(label_lookup, facts, 0U, policy->entry_offset,
          M68K_FACT_CONFIDENCE_REQUIRED) != 0)
        return -1;
    }
  }
  for (entry_index = 0U; entry_index < policy->entry_point_count; ++entry_index) {
    const M68kAnalysisEntryPoint *entry = &policy->entry_points[entry_index];
    size_t target_section = entry->has_section_index ? entry->section_index : 0U;
    if (target_section >= object->section_count) continue;
    if (enqueue_code_start(facts, queue, profile, target_section, entry->offset, M68K_FACT_CONFIDENCE_REQUIRED,
        M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT, target_section, entry->offset) != 0) return -1;
    if (label_lookup_create_label(label_lookup, facts, target_section, entry->offset,
        M68K_FACT_CONFIDENCE_REQUIRED) != 0) return -1;
  }
  for (entry_index = 0U; entry_index < policy->runtime_entry_point_count &&
       entry_index < M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT; ++entry_index) {
    const M68kAnalysisRuntimeEntryPoint *entry = &policy->runtime_entry_points[entry_index];
    size_t target_section = entry->has_section_index ? entry->section_index : 0U;
    const M68kSection *section;
    M68kFactsV2TraceState trace_state;
    uint32_t target_offset = 0U;
    if (target_section >= object->section_count) continue;
    section = &object->sections[target_section];
    if (!resolve_runtime_or_section_target(runtime_addresses, target_section, entry->runtime_address,
        section->size != 0U ? section->size : section->data_size, &target_offset)) {
      continue;
    }
    trace_state_init_unknown(&trace_state);
    if (enqueue_code_start_runtime(facts, queue, profile, target_section, target_offset,
        M68K_FACT_CONFIDENCE_REQUIRED, M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT,
        target_section, target_offset, 1U, entry->runtime_address, &trace_state) != 0) return -1;
    if (label_lookup_create_label(label_lookup, facts, target_section, target_offset,
        M68K_FACT_CONFIDENCE_REQUIRED) != 0) return -1;
  }
  for (label_index = 0U; label_index < policy->named_label_count; ++label_index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[label_index];
    size_t target_section = label->has_section_index ? label->section_index : 0U;
    if (label->domain == M68K_ANALYSIS_LABEL_DOMAIN_RUNTIME) continue;
    if (target_section >= object->section_count) continue;
    if (label_lookup_create_label(label_lookup, facts, target_section, label->offset,
        M68K_FACT_CONFIDENCE_REQUIRED) != 0)
      return -1;
  }
  for (symbol_index = 0U; symbol_index < object->symbol_count; ++symbol_index) {
    const M68kSymbol *symbol = &object->symbols[symbol_index];
    const M68kSection *section;
    uint32_t extent;
    if (!symbol->defined || symbol->section_index >= object->section_count) continue;
    section = &object->sections[symbol->section_index];
    extent = section->size != 0U ? section->size : section->data_size;
    if (symbol->value > extent) continue;
    if (label_lookup_create_label(label_lookup, facts, symbol->section_index, symbol->value,
        M68K_FACT_CONFIDENCE_REQUIRED) != 0) return -1;
  }
  for (fixup_index = 0U; fixup_index < object->fixup_count; ++fixup_index) {
    const M68kFixup *fixup = &object->fixups[fixup_index];
    M68kFactsV2RelocationFailure failure;
    M68kFact fact;
    uint32_t target_offset = 0U;
    uint32_t raw_value = 0U;
    int has_raw_value = 0;
    int has_target_section = fixup->has_target_section;
    size_t target_section_index = fixup->target_section_index;
    memset(&fact, 0, sizeof(fact));
    memset(&failure, 0, sizeof(failure));
    if (fixup->section_index < object->section_count)
      has_raw_value = read_fixup_payload_raw_local(&object->sections[fixup->section_index], fixup, &raw_value);
    if (fixup->has_target_section && !facts_v2_fixup_target_offset(object, fixup, &target_offset, &failure)) {
      if (failure.anchor_kind != M68K_FACTS_V2_RELOCATION_ANCHOR_NONE) {
        if (append_relocation_anchor_fact(facts, fixup, &failure) != 0) return -1;
        profile_record_relocation_anchor(profile, &failure);
        continue;
      }
      if (append_violation_fact(facts, fixup->section_index, fixup->offset, 0U) != 0) return -1;
      profile_record_relocation_failure(profile, &failure);
      continue;
    }
    if (!has_target_section && has_raw_value &&
        facts_v2_platform_image_offset_target(object, fixup, raw_value, &target_section_index, &target_offset)) {
      has_target_section = 1;
    }
    if (!has_target_section) {
      relocation_failure_init(&failure, fixup);
      relocation_failure_set(&failure, M68K_FACTS_V2_RELOCATION_FAILURE_TARGET_OUT_OF_RANGE, raw_value,
        (int64_t)raw_value);
      if (append_violation_fact(facts, fixup->section_index, fixup->offset, raw_value) != 0) return -1;
      profile_record_relocation_failure(profile, &failure);
      continue;
    }
    fact.kind = M68K_FACT_RELOCATION_REF;
    fact.confidence = M68K_FACT_CONFIDENCE_REQUIRED;
    fact.section_index = fixup->section_index;
    fact.offset = fixup->offset;
    fact.target_section_index = target_section_index;
    fact.target_offset = target_offset;
    if (has_raw_value && (fixup->kind == M68K_FIXUP_ABS || fixup->kind == M68K_FIXUP_SECTION_REL))
      fact.target_addend = raw_value;
    fact.size = fixup_width_bytes_local(fixup);
    fact.platform_record_kind = fixup->platform_relocation_record_kind;
    if (m68k_fact_ir_append(facts, &fact) != 0) return -1;
    if (has_target_section) {
      if (m68k_fact_ir_require_label(facts, target_section_index, fact.target_offset,
          M68K_FACT_CONFIDENCE_REQUIRED) != 0) return -1;
      if (label_lookup_create_label(label_lookup, facts, target_section_index, fact.target_offset,
          M68K_FACT_CONFIDENCE_REQUIRED) != 0) return -1;
    }
  }
  return 0;
}

static int candidate_has_generated_conditional_branch_flow(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  return metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional != 0U;
}

static int candidate_has_normal_fallthrough(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (candidate == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 1;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return 1;
  if (metadata->flow_kind == M68K_SIM_FLOW_RETURN || metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
      (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U)) {
    return 0;
  }
  return !(metadata->flow_kind == M68K_SIM_FLOW_TRAP &&
    metadata->exception_trigger == M68K_SIM_EXCEPTION_TRIGGER_ALWAYS &&
    metadata->exception_pc_source == M68K_SIM_EXCEPTION_PC_CURRENT);
}

static int is_code_target_invalid_for_section(const M68kDecodeSectionIR *section,
    const M68kDecodeTarget *target) {
  if (section == NULL || target == NULL || !target->has_section) return 0;
  if (target->section_index != section->section_index) return 0;
  return target->offset >= section->size || (target->offset & 1U) != 0U;
}

static int candidate_has_invalid_code_target(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t *out_target_offset) {
  size_t target_index;
  if (section == NULL || candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_CALL &&
        target->kind != M68K_DECODE_TARGET_JUMP) {
      continue;
    }
    if (!is_code_target_invalid_for_section(section, target)) continue;
    if (out_target_offset != NULL) *out_target_offset = target->offset;
    return 1;
  }
  return 0;
}

static int operand_is_address_register_direct(const M68kAsmOperandValue *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) {
    if (out_reg != NULL) *out_reg = operand->reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && operand->reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 1U) {
    if (out_reg != NULL) *out_reg = operand->ea_reg;
    return 1;
  }
  return 0;
}

static int operand_is_data_register_direct(const M68kAsmOperandValue *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) {
    if (out_reg != NULL) *out_reg = operand->reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && !operand->reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 0U) {
    if (out_reg != NULL) *out_reg = operand->ea_reg;
    return 1;
  }
  return 0;
}

static int operand_is_stack_predecrement(const M68kAsmOperandValue *operand) {
  return operand != NULL && operand->kind == M68K_ASM_OPERAND_EA &&
    operand->ea_mode == 4U && operand->ea_reg == 7U;
}

static int operand_is_stack_postincrement(const M68kAsmOperandValue *operand) {
  return operand != NULL && operand->kind == M68K_ASM_OPERAND_EA &&
    operand->ea_mode == 3U && operand->ea_reg == 7U;
}

static int operand_is_stack_displacement(const M68kAsmOperandValue *operand, uint32_t displacement) {
  return operand != NULL && operand->kind == M68K_ASM_OPERAND_EA &&
    operand->ea_mode == 5U && operand->ea_reg == 7U && operand->value == displacement;
}

static int operand_stack_displacement_value(const M68kAsmOperandValue *operand, uint32_t *out_displacement) {
  if (out_displacement != NULL) *out_displacement = 0U;
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_EA ||
      operand->ea_mode != 5U || operand->ea_reg != 7U) {
    return 0;
  }
  if (out_displacement != NULL) *out_displacement = operand->value;
  return 1;
}

static int operand_is_postincrement_address_register(uint8_t kind, const M68kAsmOperandValue *operand,
    uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (kind == M68K_ASM_OPERAND_POSTINC) {
    if (out_reg != NULL) *out_reg = operand->reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 3U) {
    if (out_reg != NULL) *out_reg = operand->ea_reg;
    return 1;
  }
  return 0;
}

static int operand_is_plain_address_register_indirect(uint8_t kind, const M68kAsmOperandValue *operand,
    uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (kind == M68K_ASM_OPERAND_IND) {
    if (out_reg != NULL) *out_reg = operand->reg;
    return operand->reg < 8U;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 2U && operand->ea_reg < 8U) {
    if (out_reg != NULL) *out_reg = operand->ea_reg;
    return 1;
  }
  return 0;
}

static int operand_is_control_address_register_indirect(uint8_t kind, const M68kAsmOperandValue *operand,
    uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (kind == M68K_ASM_OPERAND_IND || kind == M68K_ASM_OPERAND_POSTINC ||
      kind == M68K_ASM_OPERAND_PREDEC) {
    if (operand->reg >= 8U) return 0;
    if (out_reg != NULL) *out_reg = operand->reg;
    return 1;
  }
  return operand_is_plain_address_register_indirect(kind, operand, out_reg);
}

static int operand_immediate_value(uint8_t kind, const M68kAsmOperandValue *operand, uint32_t *out_value) {
  if (operand == NULL || out_value == NULL) return 0;
  if (kind == M68K_ASM_OPERAND_IMM || operand->kind == M68K_ASM_OPERAND_IMM ||
      (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U && operand->ea_reg == 4U)) {
    *out_value = operand->value;
    return 1;
  }
  return 0;
}

static int candidate_operand_runtime_address_value(const M68kDecodeCandidate *candidate, size_t operand_index,
    uint8_t platform_kind, uint32_t *out_value) {
  uint32_t value = 0U;
  if (candidate == NULL || operand_index >= candidate->operand_count || out_value == NULL) return 0;
  if (m68k_asm_operand_absolute_value(candidate->operand_kinds[operand_index], &candidate->operands[operand_index],
      &value)) {
    *out_value = value;
    return 1;
  }
  if (!operand_immediate_value(candidate->operand_kinds[operand_index], &candidate->operands[operand_index],
      &value)) {
    return 0;
  }
  if (operand_index == 0U && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
      candidate->operand_count == 2U) {
    uint8_t dest_reg = 0U;
    if (operand_is_address_register_direct(&candidate->operands[1], &dest_reg)) {
      *out_value = value;
      return 1;
    }
  }
  if (operand_index == 0U && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
      candidate->size_suffix == 'l' && candidate->operand_count == 2U) {
    uint32_t dest_address = 0U;
    if (m68k_asm_operand_absolute_value(candidate->operand_kinds[1], &candidate->operands[1], &dest_address) &&
        (platform_facts_v2_is_callback_vector_slot(platform_kind, dest_address) ||
         platform_facts_v2_is_runtime_address_sink(platform_kind, dest_address))) {
      *out_value = value;
      return 1;
    }
  }
  *out_value = value;
  return 0;
}

static int candidate_immediate_operand_is_address_domain(const M68kDecodeCandidate *candidate, size_t operand_index) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t other_index;
  if (candidate == NULL || operand_index >= candidate->operand_count ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || operand_index >= instruction.operand_count || operand_index >= 4U) return 0;
  if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_BRANCH_TARGET ||
      metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_COMPUTE_ADDRESS ||
      metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_ADDRESS ||
      metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_CONTROL_TARGET) {
    return 1;
  }
  if (metadata->operation_type != M68K_SIM_OP_COMPARE ||
      metadata->source_operand_index != operand_index) {
    return 0;
  }
  for (other_index = 0U; other_index < candidate->operand_count && other_index < 4U &&
       other_index < instruction.operand_count; ++other_index) {
    uint8_t reg = 0U;
    if (other_index == operand_index) continue;
    if (metadata->operand_access_kinds[other_index] != M68K_SIM_ACCESS_REGISTER_READ) continue;
    if (operand_is_address_register_direct(&candidate->operands[other_index], &reg)) return 1;
  }
  return 0;
}

static int candidate_operand_feeds_runtime_address_sink(const M68kDecodeCandidate *candidate,
    size_t operand_index, uint8_t platform_kind) {
  uint32_t dest_address = 0U;
  if (candidate == NULL || operand_index >= candidate->operand_count) return 0;
  if (operand_index == 0U && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
      candidate->size_suffix == 'l' && candidate->operand_count == 2U &&
      m68k_asm_operand_absolute_value(candidate->operand_kinds[1], &candidate->operands[1], &dest_address)) {
    return platform_facts_v2_is_runtime_address_sink(platform_kind, dest_address);
  }
  return 0;
}

static int candidate_operand_is_control_runtime_ref(const M68kDecodeCandidate *candidate, size_t operand_index) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (candidate == NULL || operand_index >= candidate->operand_count) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || operand_index >= instruction.operand_count) return 0;
  return metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_BRANCH_TARGET &&
    metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_CONTROL_TARGET;
}

static int operand_uses_address_register_as_address(uint8_t kind, const M68kAsmOperandValue *operand, uint8_t reg) {
  if (operand == NULL || reg >= 8U) return 0;
  if ((kind == M68K_ASM_OPERAND_IND || kind == M68K_ASM_OPERAND_POSTINC ||
       kind == M68K_ASM_OPERAND_PREDEC) &&
      operand->reg == reg) {
    return 1;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA) return 0;
  if (operand->ea_mode >= 2U && operand->ea_mode <= 6U && operand->ea_reg == reg) return 1;
  return 0;
}

static int candidate_uses_address_register_as_pointer(const M68kDecodeCandidate *candidate, uint8_t reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (candidate == NULL || reg >= 8U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t access = metadata->operand_access_kinds[operand_index];
    if (access != M68K_SIM_ACCESS_MEMORY_READ && access != M68K_SIM_ACCESS_MEMORY_WRITE &&
        access != M68K_SIM_ACCESS_COMPUTE_ADDRESS && access != M68K_SIM_ACCESS_BRANCH_TARGET) {
      continue;
    }
    if (operand_uses_address_register_as_address(candidate->operand_kinds[operand_index],
        &candidate->operands[operand_index], reg)) {
      return 1;
    }
  }
  return 0;
}

static int candidate_pointer_arithmetic_updates_address_register(const M68kDecodeCandidate *candidate, uint8_t reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t dest_index;
  uint8_t dest_reg = 0U;
  if (candidate == NULL || reg >= 8U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->operation_type != M68K_SIM_OP_ADD && metadata->operation_type != M68K_SIM_OP_SUB) ||
      metadata->dest_operand_index >= candidate->operand_count) {
    return 0;
  }
  dest_index = metadata->dest_operand_index;
  return operand_is_address_register_direct(&candidate->operands[dest_index], &dest_reg) && dest_reg == reg;
}

static int candidate_clobbers_address_register(const M68kDecodeCandidate *candidate, uint8_t reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (candidate == NULL || reg >= 8U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0)
    return 1;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return 1;
  if (candidate_pointer_arithmetic_updates_address_register(candidate, reg)) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t written_reg = 0U;
    uint8_t access = metadata->operand_access_kinds[operand_index];
    if (access != M68K_SIM_ACCESS_REGISTER_WRITE && access != M68K_SIM_ACCESS_REGISTER_LIST_WRITE) continue;
    if (operand_is_address_register_direct(&candidate->operands[operand_index], &written_reg) && written_reg == reg)
      return 1;
  }
  return 0;
}

static const M68kDecodeCandidate *section_candidate_at_offset(const M68kDecodeSectionIR *section, uint32_t offset) {
  size_t index;
  if (section == NULL) return NULL;
  for (index = 0U; index < section->candidate_count; ++index) {
    if (section->candidates[index].offset == offset) return &section->candidates[index];
  }
  return NULL;
}

static int following_pointer_use_proves_runtime_address_label(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const uint8_t *accepted_start, uint8_t reg) {
  uint32_t cursor;
  uint32_t step;
  if (section == NULL || candidate == NULL || accepted_start == NULL || reg >= 8U ||
      candidate->byte_count == 0U || candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  for (step = 0U; step < 16U && cursor < section->size && cursor - candidate->offset <= 96U; ++step) {
    const M68kDecodeCandidate *next = section_candidate_at_offset(section, cursor);
    if (next == NULL || !accepted_start[cursor] || next->byte_count == 0U) return 0;
    if (candidate_uses_address_register_as_pointer(next, reg)) return 1;
    if (candidate_clobbers_address_register(next, reg)) return 0;
    if (!candidate_has_normal_fallthrough(next)) return 0;
    if (next->offset > UINT32_MAX - next->byte_count) return 0;
    cursor = next->offset + next->byte_count;
  }
  return 0;
}

static int runtime_address_space_target_is_discovered_copy(const M68kRuntimeAddressSpace *space,
    size_t section_index, uint32_t runtime_address, uint32_t target_offset) {
  size_t index;
  if (space == NULL) return 0;
  for (index = space->count; index > 0U; --index) {
    const M68kRuntimeAddressRange *map = &space->ranges[index - 1U];
    uint32_t delta;
    if (map->kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
        map->section_index != section_index || runtime_address < map->runtime_address) {
      continue;
    }
    delta = runtime_address - map->runtime_address;
    if (delta < map->size && map->source_offset <= UINT32_MAX - delta &&
        map->source_offset + delta == target_offset) {
      return 1;
    }
  }
  return 0;
}

static int runtime_address_ref_needs_target_label(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, size_t operand_index, uint8_t platform_kind,
    const M68kRuntimeAddressSpace *runtime_addresses, const uint8_t *accepted_start, uint32_t target_offset,
    uint32_t runtime_address) {
  uint8_t dest_reg = 0U;
  if (runtime_address == target_offset) return 1;
  if (candidate_operand_is_control_runtime_ref(candidate, operand_index)) return 1;
  if (candidate_operand_feeds_runtime_address_sink(candidate, operand_index, platform_kind)) return 1;
  if (candidate != NULL && operand_index == 0U && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
      candidate->operand_count == 2U &&
      operand_is_address_register_direct(&candidate->operands[1], &dest_reg)) {
    if (section != NULL && accepted_start != NULL && target_offset < section->size &&
        accepted_start[target_offset] != 0U) {
      return 1;
    }
    return runtime_address_space_target_is_discovered_copy(runtime_addresses,
        section != NULL ? section->section_index : 0U, runtime_address, target_offset) &&
      following_pointer_use_proves_runtime_address_label(section, candidate, accepted_start, dest_reg);
  }
  return 1;
}

static int ir_operand_direct_data_register(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && !operand->value.reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 0U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static int ir_operand_direct_address_register(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && operand->value.reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 1U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static void trace_value_set_unknown(M68kFactsV2TraceValue *value) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
}

static void trace_value_set_constant(M68kFactsV2TraceValue *value, uint32_t constant) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->kind = M68K_FACTS_V2_TRACE_CONSTANT;
  value->value = constant;
}

static void trace_value_set_constant_with_origin(M68kFactsV2TraceValue *value, uint32_t constant,
    size_t section_index, uint32_t offset, size_t operand_index) {
  trace_value_set_constant(value, constant);
  if (value == NULL || operand_index > UINT16_MAX) return;
  value->has_origin = 1U;
  value->origin_section_index = section_index;
  value->origin_offset = offset;
  value->origin_operand_index = (uint16_t)operand_index;
}

static void trace_value_set_source_offset(M68kFactsV2TraceValue *value, size_t section_index, uint32_t offset) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->kind = M68K_FACTS_V2_TRACE_SOURCE_OFFSET;
  value->section_index = section_index;
  value->value = offset;
}

static void trace_value_set_source_offset_with_origin(M68kFactsV2TraceValue *value, size_t section_index,
    uint32_t offset, size_t origin_section_index, uint32_t origin_offset, size_t operand_index) {
  trace_value_set_source_offset(value, section_index, offset);
  if (value == NULL || operand_index > UINT16_MAX) return;
  value->has_origin = 1U;
  value->origin_section_index = origin_section_index;
  value->origin_offset = origin_offset;
  value->origin_operand_index = (uint16_t)operand_index;
}

static void trace_value_set_source_offset_with_reason(M68kFactsV2TraceValue *value, size_t section_index,
    uint32_t offset, uint32_t code_start_reason) {
  trace_value_set_source_offset(value, section_index, offset);
  if (value != NULL) value->code_start_reason = code_start_reason;
}

static void trace_value_set_runtime_address(M68kFactsV2TraceValue *value, uint32_t address) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->kind = M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS;
  value->value = address;
}

static void trace_value_set_runtime_address_with_origin(M68kFactsV2TraceValue *value, uint32_t address,
    size_t section_index, uint32_t offset, size_t operand_index) {
  trace_value_set_runtime_address(value, address);
  if (value == NULL || operand_index > UINT16_MAX) return;
  value->has_origin = 1U;
  value->origin_section_index = section_index;
  value->origin_offset = offset;
  value->origin_operand_index = (uint16_t)operand_index;
}

static void trace_value_set_target_set(M68kFactsV2TraceValue *value, size_t section_index,
    const uint32_t *targets, uint32_t target_count) {
  uint32_t index;
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->kind = M68K_FACTS_V2_TRACE_TARGET_SET;
  value->section_index = section_index;
  if (targets == NULL) return;
  if (target_count > M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT)
    target_count = M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT;
  value->target_count = target_count;
  for (index = 0U; index < target_count; ++index) value->targets[index] = targets[index];
}

static void trace_value_set_word_relative_table(M68kFactsV2TraceValue *value, size_t section_index,
    uint32_t table_offset) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->kind = M68K_FACTS_V2_TRACE_WORD_RELATIVE_TABLE;
  value->section_index = section_index;
  value->value = table_offset;
}

static void trace_value_set_keyed_long_relative_table(M68kFactsV2TraceValue *value, size_t section_index,
    uint32_t table_offset) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->kind = M68K_FACTS_V2_TRACE_KEYED_LONG_RELATIVE_TABLE;
  value->section_index = section_index;
  value->value = table_offset;
}

static int trace_value_advance(M68kFactsV2TraceValue *value, uint32_t delta) {
  if (value == NULL || value->kind == M68K_FACTS_V2_TRACE_UNKNOWN) return 0;
  if (value->kind == M68K_FACTS_V2_TRACE_TARGET_SET ||
      value->kind == M68K_FACTS_V2_TRACE_WORD_RELATIVE_TABLE ||
      value->kind == M68K_FACTS_V2_TRACE_KEYED_LONG_RELATIVE_TABLE) {
    trace_value_set_unknown(value);
    return 0;
  }
  if (value->value > UINT32_MAX - delta) {
    trace_value_set_unknown(value);
    return 0;
  }
  value->value += delta;
  return 1;
}

static M68kFactsV2AbsoluteSlot *trace_state_find_absolute_slot(M68kFactsV2TraceState *state,
    uint32_t address) {
  size_t index;
  if (state == NULL) return NULL;
  for (index = 0U; index < M68K_FACTS_V2_TRACE_ABSOLUTE_SLOT_LIMIT; ++index) {
    if (state->absolute_slots[index].used && state->absolute_slots[index].address == address)
      return &state->absolute_slots[index];
  }
  return NULL;
}

static const M68kFactsV2AbsoluteSlot *trace_state_find_absolute_slot_const(const M68kFactsV2TraceState *state,
    uint32_t address) {
  size_t index;
  if (state == NULL) return NULL;
  for (index = 0U; index < M68K_FACTS_V2_TRACE_ABSOLUTE_SLOT_LIMIT; ++index) {
    if (state->absolute_slots[index].used && state->absolute_slots[index].address == address)
      return &state->absolute_slots[index];
  }
  return NULL;
}

static void trace_state_clear_absolute_slot(M68kFactsV2TraceState *state, uint32_t address) {
  M68kFactsV2AbsoluteSlot *slot = trace_state_find_absolute_slot(state, address);
  if (slot != NULL) memset(slot, 0, sizeof(*slot));
}

static void trace_state_set_absolute_slot(M68kFactsV2TraceState *state, uint32_t address,
    const M68kFactsV2TraceValue *value) {
  M68kFactsV2AbsoluteSlot *slot;
  size_t index;
  if (state == NULL || value == NULL) return;
  slot = trace_state_find_absolute_slot(state, address);
  if (slot == NULL) {
    for (index = 0U; index < M68K_FACTS_V2_TRACE_ABSOLUTE_SLOT_LIMIT; ++index) {
      if (!state->absolute_slots[index].used) {
        slot = &state->absolute_slots[index];
        break;
      }
    }
  }
  if (slot == NULL) return;
  memset(slot, 0, sizeof(*slot));
  slot->used = 1U;
  slot->address = address;
  slot->value = *value;
}

static M68kFactsV2StackSlot *trace_state_find_stack_slot(M68kFactsV2TraceState *state,
    uint32_t displacement) {
  size_t index;
  if (state == NULL) return NULL;
  for (index = 0U; index < M68K_FACTS_V2_TRACE_STACK_SLOT_LIMIT; ++index) {
    if (state->stack_slots[index].used && state->stack_slots[index].displacement == displacement)
      return &state->stack_slots[index];
  }
  return NULL;
}

static const M68kFactsV2StackSlot *trace_state_find_stack_slot_const(const M68kFactsV2TraceState *state,
    uint32_t displacement) {
  size_t index;
  if (state == NULL) return NULL;
  for (index = 0U; index < M68K_FACTS_V2_TRACE_STACK_SLOT_LIMIT; ++index) {
    if (state->stack_slots[index].used && state->stack_slots[index].displacement == displacement)
      return &state->stack_slots[index];
  }
  return NULL;
}

static void trace_state_set_stack_slot(M68kFactsV2TraceState *state, uint32_t displacement,
    const M68kFactsV2TraceValue *value) {
  M68kFactsV2StackSlot *slot;
  size_t index;
  if (state == NULL || value == NULL) return;
  slot = trace_state_find_stack_slot(state, displacement);
  if (slot == NULL) {
    for (index = 0U; index < M68K_FACTS_V2_TRACE_STACK_SLOT_LIMIT; ++index) {
      if (!state->stack_slots[index].used) {
        slot = &state->stack_slots[index];
        break;
      }
    }
  }
  if (slot == NULL) return;
  memset(slot, 0, sizeof(*slot));
  slot->used = 1U;
  slot->displacement = displacement;
  slot->value = *value;
}

static void trace_state_clear_stack_slots(M68kFactsV2TraceState *state) {
  if (state == NULL) return;
  memset(state->stack_slots, 0, sizeof(state->stack_slots));
}

static void trace_state_shift_stack_slots(M68kFactsV2TraceState *state, int32_t sp_delta) {
  size_t index;
  if (state == NULL) return;
  for (index = 0U; index < M68K_FACTS_V2_TRACE_STACK_SLOT_LIMIT; ++index) {
    M68kFactsV2StackSlot *slot = &state->stack_slots[index];
    int64_t displacement;
    if (!slot->used) continue;
    displacement = (int64_t)slot->displacement - (int64_t)sp_delta;
    if (displacement < 0 || displacement > 0xFFFF) {
      memset(slot, 0, sizeof(*slot));
      continue;
    }
    slot->displacement = (uint32_t)displacement;
  }
}

static void trace_state_push_stack_value(M68kFactsV2TraceState *state, const M68kFactsV2TraceValue *value) {
  if (state == NULL || value == NULL) return;
  trace_state_shift_stack_slots(state, -4);
  trace_state_set_stack_slot(state, 0U, value);
}

static void trace_state_pop_stack_long(M68kFactsV2TraceState *state) {
  M68kFactsV2StackSlot *slot;
  if (state == NULL) return;
  slot = trace_state_find_stack_slot(state, 0U);
  if (slot != NULL) memset(slot, 0, sizeof(*slot));
  trace_state_shift_stack_slots(state, 4);
}

static void trace_state_kill_register_writes(const M68kDecodeCandidate *candidate,
    M68kFactsV2TraceState *state) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (candidate == NULL || state == NULL) return;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return;
  for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
    uint8_t access = metadata->operand_access_kinds[operand_index];
    uint8_t reg = 0U;
    if (access != M68K_SIM_ACCESS_REGISTER_WRITE && access != M68K_SIM_ACCESS_REGISTER_LIST_WRITE)
      continue;
    if (ir_operand_direct_data_register(&instruction.operands[operand_index], &reg)) {
      if (state->reglist_copy_valid &&
          trace_reglist_mask_contains_register(state->reglist_copy_mask, 0U, reg)) {
        state->reglist_copy_valid = 0U;
      }
      trace_state_clear_data_register(state, reg);
    } else if (ir_operand_direct_address_register(&instruction.operands[operand_index], &reg)) {
      if (state->reglist_copy_valid &&
          trace_reglist_mask_contains_register(state->reglist_copy_mask, 1U, reg)) {
        state->reglist_copy_valid = 0U;
      }
      if (state->copied_entry_valid && state->copied_entry_dest_reg == reg)
        state->copied_entry_valid = 0U;
      trace_value_set_unknown(&state->a[reg]);
    } else {
      state->reglist_copy_valid = 0U;
      state->copied_entry_valid = 0U;
    }
  }
}

static uint8_t trace_candidate_transfer_width(const M68kDecodeCandidate *candidate) {
  if (candidate == NULL) return 0U;
  if (candidate->size_suffix == 'b') return 1U;
  if (candidate->size_suffix == 'w') return 2U;
  if (candidate->size_suffix == 'l') return 4U;
  return 0U;
}

static int trace_candidate_reglist_operand(const M68kDecodeCandidate *candidate,
    const M68kSimFormMetadata *metadata, size_t *out_operand_index, uint16_t *out_mask) {
  size_t operand_index;
  if (out_operand_index != NULL) *out_operand_index = 0U;
  if (out_mask != NULL) *out_mask = 0U;
  if (candidate == NULL || metadata == NULL || out_operand_index == NULL || out_mask == NULL) return 0;
  if (metadata->reglist_operand_index < candidate->operand_count &&
      candidate->operand_kinds[metadata->reglist_operand_index] == M68K_ASM_OPERAND_REGLIST) {
    *out_operand_index = metadata->reglist_operand_index;
    *out_mask = (uint16_t)candidate->operands[metadata->reglist_operand_index].value;
    return *out_mask != 0U;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t access = metadata->operand_access_kinds[operand_index];
    if (access != M68K_SIM_ACCESS_REGISTER_LIST_READ && access != M68K_SIM_ACCESS_REGISTER_LIST_WRITE) continue;
    if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_REGLIST) continue;
    *out_operand_index = operand_index;
    *out_mask = (uint16_t)candidate->operands[operand_index].value;
    return *out_mask != 0U;
  }
  return 0;
}

static int operand_is_predecrement_address_register(uint8_t kind, const M68kAsmOperandValue *operand,
    uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (kind == M68K_ASM_OPERAND_PREDEC) {
    if (out_reg != NULL) *out_reg = operand->reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 4U) {
    if (out_reg != NULL) *out_reg = operand->ea_reg;
    return 1;
  }
  return 0;
}

static int trace_candidate_memory_operand_index(const M68kDecodeCandidate *candidate,
    const M68kSimFormMetadata *metadata, uint8_t access_kind, size_t *out_operand_index) {
  size_t operand_index;
  if (out_operand_index != NULL) *out_operand_index = 0U;
  if (candidate == NULL || metadata == NULL || out_operand_index == NULL) return 0;
  if (metadata->address_operand_index < candidate->operand_count &&
      metadata->operand_access_kinds[metadata->address_operand_index] == access_kind) {
    *out_operand_index = metadata->address_operand_index;
    return 1;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    if (metadata->operand_access_kinds[operand_index] == access_kind) {
      *out_operand_index = operand_index;
      return 1;
    }
  }
  return 0;
}

static int trace_state_operand_runtime_address(const M68kFactsV2TraceState *state,
    const M68kDecodeCandidate *candidate, size_t operand_index, uint32_t *out_address) {
  const M68kAsmOperandValue *operand;
  uint32_t absolute = 0U;
  uint8_t reg = 0U;
  int64_t address;
  int32_t displacement = 0;
  if (out_address != NULL) *out_address = 0U;
  if (state == NULL || candidate == NULL || out_address == NULL || operand_index >= candidate->operand_count)
    return 0;
  if (m68k_asm_operand_absolute_value(candidate->operand_kinds[operand_index], &candidate->operands[operand_index],
      &absolute)) {
    *out_address = absolute;
    return 1;
  }
  operand = &candidate->operands[operand_index];
  if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA || operand->ea_reg >= 8U)
    return 0;
  if (operand->ea_mode != 2U && operand->ea_mode != 5U) return 0;
  reg = operand->ea_reg;
  if (state->a[reg].kind != M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS &&
      state->a[reg].kind != M68K_FACTS_V2_TRACE_CONSTANT) {
    return 0;
  }
  if (operand->ea_mode == 5U) displacement = (int32_t)(int16_t)(operand->value & 0xFFFFU);
  address = (int64_t)(uint64_t)state->a[reg].value + (int64_t)displacement;
  if (address < 0 || address > (int64_t)(uint64_t)UINT32_MAX) return 0;
  *out_address = (uint32_t)address;
  return 1;
}

static int candidate_operand_base_field_slot(const M68kDecodeCandidate *candidate, size_t operand_index,
    uint8_t *out_base_reg, int32_t *out_displacement) {
  const M68kAsmOperandValue *operand;
  if (out_base_reg != NULL) *out_base_reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (candidate == NULL || out_base_reg == NULL || out_displacement == NULL ||
      operand_index >= candidate->operand_count) {
    return 0;
  }
  operand = &candidate->operands[operand_index];
  if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA || operand->ea_reg >= 7U)
    return 0;
  if (operand->ea_mode == 2U) {
    *out_base_reg = operand->ea_reg;
    *out_displacement = 0;
    return 1;
  }
  if (operand->ea_mode == 5U) {
    *out_base_reg = operand->ea_reg;
    *out_displacement = (int32_t)(int16_t)(operand->value & 0xFFFFU);
    return 1;
  }
  return 0;
}

static void trace_state_apply_reglist_memory_read(size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kRuntimeAddressSpace *runtime_addresses,
    M68kFactsV2TraceState *state) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t reglist_operand = 0U, memory_operand = 0U;
  uint16_t mask = 0U;
  uint8_t width;
  uint32_t source_offset = 0U, size;
  if (section == NULL || candidate == NULL || runtime_addresses == NULL || state == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_MOVE_MULTIPLE ||
      metadata->multi_transfer_direction != M68K_SIM_MULTI_MEMORY_TO_REGISTER) {
    return;
  }
  width = trace_candidate_transfer_width(candidate);
  if (width == 0U ||
      !trace_candidate_reglist_operand(candidate, metadata, &reglist_operand, &mask) ||
      !trace_candidate_memory_operand_index(candidate, metadata, M68K_SIM_ACCESS_MEMORY_READ,
        &memory_operand) ||
      !trace_state_operand_storage_offset(runtime_addresses, section_index, section, candidate, state,
        memory_operand, &source_offset)) {
    return;
  }
  size = (uint32_t)m68k_popcount16(mask) * (uint32_t)width;
  if (size == 0U || source_offset > section->size || size > section->size - source_offset) return;
  (void)reglist_operand;
  state->reglist_copy_valid = 1U;
  state->reglist_copy_width = width;
  state->reglist_copy_mask = mask;
  state->reglist_copy_section_index = section_index;
  state->reglist_copy_offset = source_offset;
  state->reglist_copy_size = size;
}

static int trace_state_record_reglist_runtime_copy(M68kRuntimeAddressSpace *space, M68kFactIR *facts,
    M68kFactsV2Profile *profile, size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *state) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t reglist_operand = 0U;
  size_t memory_operand = 0U;
  uint16_t mask = 0U;
  uint8_t width;
  uint32_t runtime_address = 0U;
  (void)section_index;
  if (space == NULL || section == NULL || candidate == NULL || state == NULL || !state->reglist_copy_valid ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_MOVE_MULTIPLE ||
      metadata->multi_transfer_direction != M68K_SIM_MULTI_REGISTER_TO_MEMORY) {
    return 0;
  }
  width = trace_candidate_transfer_width(candidate);
  if (width == 0U || width != state->reglist_copy_width ||
      !trace_candidate_reglist_operand(candidate, metadata, &reglist_operand, &mask) ||
      mask != state->reglist_copy_mask ||
      !trace_candidate_memory_operand_index(candidate, metadata, M68K_SIM_ACCESS_MEMORY_WRITE,
        &memory_operand) ||
      !trace_state_operand_runtime_address(state, candidate, memory_operand, &runtime_address)) {
    return 0;
  }
  (void)reglist_operand;
  return runtime_address_space_add(space, state->reglist_copy_section_index,
    state->reglist_copy_offset, runtime_address, state->reglist_copy_size,
    M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY, M68K_FACT_CONFIDENCE_TOOL_INFERRED,
    facts, profile);
}

static void trace_state_apply_predecrement_copy_entry(size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *before,
    M68kFactsV2TraceState *after) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t source_reg = 0U, dest_reg = 0U, width;
  uint32_t count, size, source_start;
  if (section == NULL || candidate == NULL || before == NULL || after == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_MOVE || candidate->operand_count != 2U)
    return;
  width = trace_candidate_transfer_width(candidate);
  if (width == 0U ||
      !operand_is_predecrement_address_register(candidate->operand_kinds[0], &candidate->operands[0],
        &source_reg) ||
      !operand_is_predecrement_address_register(candidate->operand_kinds[1], &candidate->operands[1],
        &dest_reg) ||
      before->a[source_reg].kind != M68K_FACTS_V2_TRACE_SOURCE_OFFSET ||
      before->a[source_reg].section_index != section_index ||
      before->a[source_reg].value > section->size ||
      !m68k_bitset_u32_has(before->d_low16_known, 0U)) {
    return;
  }
  count = (uint32_t)before->d_low16[0] + 1U;
  if (count == 0U || count > UINT32_MAX / (uint32_t)width) return;
  size = count * (uint32_t)width;
  if (size == 0U || size > before->a[source_reg].value) return;
  source_start = before->a[source_reg].value - size;
  if (source_start >= section->size || size > section->size - source_start) return;
  after->copied_entry_valid = 1U;
  after->copied_entry_dest_reg = dest_reg;
  after->copied_entry_section_index = section_index;
  after->copied_entry_source_offset = source_start;
  after->copied_entry_size = size;
}

static int trace_state_move_copy_source_is_tracked_value(const M68kDecodeCandidate *candidate,
    size_t operand_index, const M68kFactsV2TraceState *state) {
  uint8_t reg = 0U;
  uint32_t value = 0U;
  if (candidate == NULL || state == NULL || operand_index >= candidate->operand_count) return 0;
  if (operand_is_data_register_direct(&candidate->operands[operand_index], &reg) ||
      operand_is_address_register_direct(&candidate->operands[operand_index], &reg) ||
      operand_is_stack_postincrement(&candidate->operands[operand_index])) {
    return 1;
  }
  if (operand_immediate_value(candidate->operand_kinds[operand_index], &candidate->operands[operand_index],
      &value)) {
    return 1;
  }
  return m68k_asm_operand_absolute_value(candidate->operand_kinds[operand_index], &candidate->operands[operand_index],
      &value) && trace_state_find_absolute_slot_const(state, value) != NULL;
}

static void trace_state_apply_move_value_copy(size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *before,
    M68kFactsV2TraceState *after) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  M68kFactsV2TraceValue value;
  uint8_t reg = 0U;
  if (section == NULL || candidate == NULL || before == NULL || after == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_MOVE ||
      metadata->source_operand_index >= candidate->operand_count ||
      metadata->dest_operand_index >= candidate->operand_count) {
    return;
  }
  if (!trace_state_move_copy_source_is_tracked_value(candidate, metadata->source_operand_index, before)) return;
  if (!trace_value_from_candidate_source(section_index, section, candidate, metadata->source_operand_index,
      before, &value)) {
    return;
  }
  if (operand_is_data_register_direct(&candidate->operands[metadata->dest_operand_index], &reg)) {
    after->d[reg] = value;
    if (value.kind == M68K_FACTS_V2_TRACE_CONSTANT) {
      m68k_bitset_u32_set(&after->d_low16_known, reg);
      m68k_bitset_u32_set(&after->d_low16_has_origin, reg);
      after->d_low16[reg] = (uint16_t)(value.value & 0xFFFFU);
      after->d_low16_origin_offset[reg] = candidate->offset;
    } else {
      uint8_t source_reg = 0U;
      if (operand_is_data_register_direct(&candidate->operands[metadata->source_operand_index], &source_reg) &&
          m68k_bitset_u32_has(before->d_low16_known, source_reg)) {
        m68k_bitset_u32_set(&after->d_low16_known, reg);
        m68k_bitset_u32_set(&after->d_low16_has_origin, reg);
        after->d_low16[reg] = before->d_low16[source_reg];
        after->d_low16_origin_offset[reg] = candidate->offset;
      } else {
        m68k_bitset_u32_clear(&after->d_low16_known, reg);
        m68k_bitset_u32_clear(&after->d_low16_has_origin, reg);
      }
    }
  } else if (operand_is_address_register_direct(&candidate->operands[metadata->dest_operand_index], &reg) &&
             reg != 7U) {
    after->a[reg] = value;
  }
}

static int candidate_dbcc_counter_register_for_loop(const M68kDecodeCandidate *candidate,
    size_t section_index, uint32_t loop_member_offset, uint8_t *out_reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t target_index;
  uint8_t reg = 0U;
  if (candidate == NULL || out_reg == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_DBCC ||
      metadata->source_operand_index >= candidate->operand_count ||
      !operand_is_data_register_direct(&candidate->operands[metadata->source_operand_index], &reg)) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH && target->has_section &&
        target->section_index == section_index && target->offset <= loop_member_offset) {
      *out_reg = reg;
      return 1;
    }
  }
  return 0;
}

static int following_dbcc_loop_counter_register(M68kDecodeIR *decode, size_t section_index,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate, uint8_t max_cpu,
    uint8_t *out_reg) {
  uint32_t cursor;
  uint32_t step;
  if (decode == NULL || section == NULL || candidate == NULL || out_reg == NULL ||
      candidate->byte_count == 0U || candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  for (step = 0U; step < 6U && cursor < section->size && cursor - candidate->offset <= 24U; ++step) {
    const M68kDecodeCandidate *next = NULL;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &next,
        m68k_diag_sink(NULL)) != 0 || next == NULL || next->byte_count == 0U) {
      return 0;
    }
    if (candidate_dbcc_counter_register_for_loop(next, section_index, candidate->offset, out_reg)) return 1;
    if (!candidate_has_normal_fallthrough(next) || next->offset > UINT32_MAX - next->byte_count) return 0;
    cursor = next->offset + next->byte_count;
  }
  return 0;
}

static int candidate_branches_back_to_loop_member(const M68kDecodeCandidate *candidate,
    size_t section_index, uint32_t loop_member_offset) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH && target->has_section &&
        target->section_index == section_index && target->offset <= loop_member_offset) {
      return 1;
    }
  }
  return 0;
}

static int candidate_decrements_data_register_by_one(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
    uint32_t *out_width) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t reg = 0U;
  uint32_t value = 0U;
  if (out_width != NULL) *out_width = 0U;
  if (candidate == NULL || out_reg == NULL || out_width == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_SUB ||
      metadata->source_operand_index >= candidate->operand_count ||
      metadata->dest_operand_index >= candidate->operand_count ||
      !operand_immediate_value(candidate->operand_kinds[metadata->source_operand_index],
        &candidate->operands[metadata->source_operand_index], &value) ||
      value != 1U ||
      !operand_is_data_register_direct(&candidate->operands[metadata->dest_operand_index], &reg)) {
    return 0;
  }
  *out_reg = reg;
  if (candidate->size_suffix == 'b') *out_width = 1U;
  else if (candidate->size_suffix == 'w') *out_width = 2U;
  else if (candidate->size_suffix == 'l') *out_width = 4U;
  else return 0;
  return 1;
}

static int following_decrement_branch_loop_counter_register(M68kDecodeIR *decode, size_t section_index,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate, uint8_t max_cpu,
    uint8_t *out_reg, uint8_t *out_use_full_counter) {
  uint32_t cursor;
  uint32_t step;
  uint8_t reg = 0U;
  uint32_t counter_width = 0U;
  int saw_decrement = 0;
  if (out_use_full_counter != NULL) *out_use_full_counter = 0U;
  if (decode == NULL || section == NULL || candidate == NULL || out_reg == NULL ||
      out_use_full_counter == NULL || candidate->byte_count == 0U ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  for (step = 0U; step < 6U && cursor < section->size && cursor - candidate->offset <= 24U; ++step) {
    const M68kDecodeCandidate *next = NULL;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &next,
        m68k_diag_sink(NULL)) != 0 || next == NULL || next->byte_count == 0U) {
      return 0;
    }
    if (!saw_decrement) {
      if (candidate_decrements_data_register_by_one(next, &reg, &counter_width)) {
        saw_decrement = 1;
      } else if (!candidate_has_normal_fallthrough(next)) {
        return 0;
      }
    } else if (candidate_branches_back_to_loop_member(next, section_index, candidate->offset)) {
      *out_reg = reg;
      *out_use_full_counter = counter_width == 4U ? 1U : 0U;
      return 1;
    } else if (!candidate_has_normal_fallthrough(next)) {
      return 0;
    }
    if (next->offset > UINT32_MAX - next->byte_count) return 0;
    cursor = next->offset + next->byte_count;
  }
  return 0;
}

static uint32_t trace_copy_size_from_counter_register(const M68kFactsV2TraceState *state, uint8_t reg,
    uint32_t width, uint32_t fallback_size, uint8_t inclusive_counter, uint8_t use_full_counter) {
  uint32_t count;
  uint32_t size;
  if (state == NULL || reg >= 8U || width == 0U ||
      !m68k_bitset_u32_has(state->d_low16_known, reg)) return fallback_size;
  if (use_full_counter && state->d[reg].kind == M68K_FACTS_V2_TRACE_CONSTANT) {
    count = state->d[reg].value;
  } else {
    count = (uint32_t)state->d_low16[reg] + (inclusive_counter ? 1U : 0U);
  }
  if (count != 0U && count <= UINT32_MAX / width) {
    size = count * width;
    if (size != 0U && size < fallback_size) return size;
  }
  return fallback_size;
}

static uint32_t trace_copy_size_from_state(const M68kFactsV2TraceState *state, uint32_t width,
    uint32_t candidate_offset, uint8_t has_loop_counter_reg, uint8_t loop_counter_reg,
    uint8_t loop_counter_is_inclusive, uint8_t loop_counter_uses_full_value, uint32_t fallback_size) {
  uint32_t count;
  uint32_t size;
  if (state == NULL || width == 0U) return fallback_size;
  if (has_loop_counter_reg) {
    return trace_copy_size_from_counter_register(state, loop_counter_reg, width, fallback_size,
      loop_counter_is_inclusive, loop_counter_uses_full_value);
  }
  if (m68k_bitset_u32_has(state->d_low16_known, 0U) &&
      m68k_bitset_u32_has(state->d_low16_has_origin, 0U) &&
      state->d_low16_origin_offset[0] < candidate_offset &&
      candidate_offset - state->d_low16_origin_offset[0] <= 8U) {
    count = (uint32_t)state->d_low16[0] + 1U;
    if (count != 0U && count <= UINT32_MAX / width) {
      size = count * width;
      if (size != 0U && size < fallback_size) return size;
    }
  }
  if (state->d[0].kind != M68K_FACTS_V2_TRACE_CONSTANT || state->d[0].value == UINT32_MAX) return fallback_size;
  count = state->d[0].value + 1U;
  if (count != 0U && count <= UINT32_MAX / width) {
    size = count * width;
    if (size != 0U && size < fallback_size) return size;
  }
  return fallback_size;
}

static int trace_state_record_runtime_copy(M68kDecodeIR *decode, M68kRuntimeAddressSpace *space, M68kFactIR *facts,
    M68kFactsV2Profile *profile, size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *state, uint8_t max_cpu) {
  uint8_t source_reg = 0U, dest_reg = 0U, loop_counter_reg = 0U, has_loop_counter_reg = 0U;
  uint8_t loop_counter_is_inclusive = 0U;
  uint8_t loop_counter_uses_full_value = 0U;
  uint32_t width = 0U, fallback_size, copy_size;
  if (space == NULL || section == NULL || candidate == NULL || state == NULL) return 0;
  if (trace_state_record_reglist_runtime_copy(space, facts, profile, section_index, section, candidate,
      state) != 0) {
    return -1;
  }
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->operand_count != 2U)
    return 0;
  if (candidate->size_suffix == 'b') width = 1U;
  else if (candidate->size_suffix == 'w') width = 2U;
  else if (candidate->size_suffix == 'l') width = 4U;
  if (width == 0U) return 0;
  if (!operand_is_postincrement_address_register(candidate->operand_kinds[0], &candidate->operands[0],
      &source_reg) ||
      !operand_is_postincrement_address_register(candidate->operand_kinds[1], &candidate->operands[1],
      &dest_reg)) {
    return 0;
  }
  if (state->a[source_reg].kind != M68K_FACTS_V2_TRACE_SOURCE_OFFSET ||
      state->a[dest_reg].kind != M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS ||
      state->a[source_reg].section_index != section_index ||
      state->a[source_reg].value >= section->size) {
    return 0;
  }
  fallback_size = section->size - state->a[source_reg].value;
  if (following_dbcc_loop_counter_register(decode, section_index, section, candidate, max_cpu, &loop_counter_reg)) {
    has_loop_counter_reg = 1U;
    loop_counter_is_inclusive = 1U;
  } else if (following_decrement_branch_loop_counter_register(decode, section_index, section, candidate, max_cpu,
      &loop_counter_reg, &loop_counter_uses_full_value)) {
    has_loop_counter_reg = 1U;
    loop_counter_is_inclusive = 0U;
  }
  copy_size = trace_copy_size_from_state(state, width, candidate->offset, has_loop_counter_reg, loop_counter_reg,
    loop_counter_is_inclusive, loop_counter_uses_full_value, fallback_size);
  if (copy_size > fallback_size) copy_size = fallback_size;
  return runtime_address_space_add(space, section_index, state->a[source_reg].value,
    state->a[dest_reg].value, copy_size, M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY,
    M68K_FACT_CONFIDENCE_TOOL_INFERRED, facts, profile);
}

static int trace_value_resolve_runtime_ref_target(const M68kRuntimeAddressSpace *runtime_addresses,
    size_t section_index, const M68kDecodeSectionIR *section, const M68kFactsV2TraceValue *value,
    uint32_t *out_target_offset, uint32_t *out_runtime_address) {
  uint32_t target_offset = 0U;
  uint32_t runtime_address = 0U;
  if (runtime_addresses == NULL || section == NULL || value == NULL || out_target_offset == NULL ||
      out_runtime_address == NULL) {
    return 0;
  }
  if (value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
    if (value->section_index != section_index || value->value >= section->size) return 0;
    target_offset = value->value;
    if (!runtime_address_space_source_to_runtime_near(runtime_addresses, section_index, target_offset,
        0U, 0U, &runtime_address)) {
      runtime_address = target_offset;
    }
  } else if (value->kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS ||
             value->kind == M68K_FACTS_V2_TRACE_CONSTANT) {
    runtime_address = value->value;
    if (!runtime_address_space_translate(runtime_addresses, section_index, runtime_address, section->size,
        &target_offset)) {
      return 0;
    }
  } else {
    return 0;
  }
  *out_target_offset = target_offset;
  *out_runtime_address = runtime_address;
  return 1;
}

static int trace_state_record_runtime_sink_ref(const M68kRuntimeAddressSpace *runtime_addresses,
    M68kFactIR *facts, uint8_t platform_kind, size_t section_index, const M68kDecodeSectionIR *section,
    uint8_t *accepted_start, uint8_t *accepted_bytes, const M68kDecodeCandidate *candidate,
    const M68kFactsV2TraceState *state) {
  uint32_t sink_address = 0U;
  uint32_t target_offset = 0U;
  uint32_t runtime_address = 0U;
  uint8_t reg = 0U;
  const M68kFactsV2TraceValue *value = NULL;
  int ref_result;
  if (runtime_addresses == NULL || facts == NULL || section == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || candidate == NULL || state == NULL) {
    return 0;
  }
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) {
    return 0;
  }
  if (!trace_state_operand_runtime_address(state, candidate, 1U, &sink_address) ||
      !platform_facts_v2_is_runtime_address_sink(platform_kind, sink_address)) {
    return 0;
  }
  if (operand_is_data_register_direct(&candidate->operands[0], &reg)) {
    value = &state->d[reg];
  } else if (operand_is_address_register_direct(&candidate->operands[0], &reg)) {
    value = &state->a[reg];
  } else {
    return 0;
  }
  if (!trace_value_resolve_runtime_ref_target(runtime_addresses, section_index, section, value,
      &target_offset, &runtime_address)) {
    if (value->kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS ||
        value->kind == M68K_FACTS_V2_TRACE_CONSTANT) {
      ref_result = append_external_runtime_address_ref_fact(facts, section_index, candidate->offset,
        M68K_FACT_RUNTIME_ADDRESS_REF_NO_OPERAND, value->value, sink_address,
        (size_t)-1, 0U, M68K_FACT_CONFIDENCE_TOOL_INFERRED);
      if (ref_result < 0) return -1;
      if (value->has_origin) {
        ref_result = append_external_runtime_address_ref_fact(facts, value->origin_section_index,
          value->origin_offset, value->origin_operand_index, value->value, sink_address,
          (size_t)-1, 0U, M68K_FACT_CONFIDENCE_TOOL_INFERRED);
        if (ref_result < 0) return -1;
      }
    }
    return 0;
  }
  if (accepted_offset_is_interior(section, accepted_start, accepted_bytes, target_offset)) return 0;
  ref_result = append_runtime_address_ref_fact_with_sink(facts, section_index, candidate->offset,
    M68K_FACT_RUNTIME_ADDRESS_REF_NO_OPERAND, target_offset, runtime_address, sink_address,
    M68K_FACT_CONFIDENCE_TOOL_INFERRED);
  if (ref_result < 0) return -1;
  if (value->has_origin && value->origin_section_index == section_index) {
    const M68kDecodeCandidate *origin_candidate = m68k_decode_ir_find_candidate_at_offset(section,
      value->origin_offset);
    if (origin_candidate != NULL && origin_candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
      int origin_ref_result = append_runtime_address_ref_fact_with_sink(facts, value->origin_section_index,
        value->origin_offset, value->origin_operand_index, target_offset, runtime_address, sink_address,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED);
      if (origin_ref_result < 0) return -1;
    }
  }
  if (ref_result == 0) return 0;
  if (append_xref_fact(facts, section_index, candidate->offset, target_offset,
      M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
    return -1;
  }
  return m68k_fact_ir_require_label(facts, section_index, target_offset,
    M68K_FACT_CONFIDENCE_TOOL_INFERRED);
}

static int trace_state_operand_storage_offset(const M68kRuntimeAddressSpace *runtime_addresses,
    size_t section_index, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kFactsV2TraceState *state, size_t operand_index, uint32_t *out_offset) {
  const M68kAsmOperandValue *operand;
  uint32_t base = 0U;
  int32_t displacement = 0;
  int64_t target;
  if (out_offset != NULL) *out_offset = 0U;
  if (runtime_addresses == NULL || section == NULL || candidate == NULL || state == NULL ||
      out_offset == NULL || operand_index >= candidate->operand_count) {
    return 0;
  }
  if (candidate_operand_data_target_offset(candidate, operand_index, section_index, out_offset)) return 1;
  operand = &candidate->operands[operand_index];
  if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA || operand->ea_reg >= 8U) return 0;
  if (operand->ea_mode != 2U && operand->ea_mode != 5U) return 0;
  if (!trace_value_to_table_storage_offset(&state->a[operand->ea_reg], runtime_addresses, section_index,
      section->size, &base)) {
    return 0;
  }
  if (operand->ea_mode == 5U) displacement = (int32_t)(int16_t)(operand->value & 0xFFFFU);
  target = (int64_t)(uint64_t)base + (int64_t)displacement;
  if (target < 0 || target >= (int64_t)(uint64_t)section->size) return 0;
  *out_offset = (uint32_t)target;
  return 1;
}

static int trace_state_record_runtime_storage_sink_ref(const M68kRuntimeAddressSpace *runtime_addresses,
    M68kFactIR *facts, uint8_t platform_kind, size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *state) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  M68kFactsV2TraceValue value;
  uint32_t sink_offset = 0U;
  uint8_t source_index;
  uint8_t dest_index;
  int ref_result;
  if (runtime_addresses == NULL || facts == NULL || section == NULL || candidate == NULL || state == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return 0;
  source_index = metadata->source_operand_index;
  dest_index = metadata->dest_operand_index;
  if (source_index >= candidate->operand_count || dest_index >= candidate->operand_count) return 0;
  if (metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE) return 0;
  if (!trace_state_operand_storage_offset(runtime_addresses, section_index, section, candidate, state,
      dest_index, &sink_offset)) {
    return 0;
  }
  if (platform_facts_v2_runtime_address_storage_sink_data_class_flags(platform_kind, section->data, section->size,
      sink_offset) == 0U) {
    return 0;
  }
  if (!trace_value_from_candidate_source(section_index, section, candidate, source_index, state, &value)) return 0;
  if ((value.kind != M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS && value.kind != M68K_FACTS_V2_TRACE_CONSTANT) ||
      !value.has_origin) {
    return 0;
  }
  if (value.value < M68K_FACTS_V2_EXTERNAL_RUNTIME_ADDRESS_MIN) return 0;
  ref_result = append_external_runtime_address_ref_fact(facts, value.origin_section_index, value.origin_offset,
    value.origin_operand_index, value.value, 0U, section_index, sink_offset, M68K_FACT_CONFIDENCE_TOOL_INFERRED);
  return ref_result < 0 ? -1 : 0;
}

static int trace_value_from_candidate_source(size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, size_t operand_index, const M68kFactsV2TraceState *state,
    M68kFactsV2TraceValue *out_value) {
  uint8_t reg = 0U;
  uint32_t value = 0U;
  const M68kFactsV2AbsoluteSlot *slot;
  const M68kFactsV2StackSlot *stack_slot;
  if (out_value != NULL) trace_value_set_unknown(out_value);
  if (section == NULL || candidate == NULL || state == NULL || out_value == NULL ||
      operand_index >= candidate->operand_count) {
    return 0;
  }
  if (operand_is_data_register_direct(&candidate->operands[operand_index], &reg)) {
    *out_value = state->d[reg];
    return out_value->kind != M68K_FACTS_V2_TRACE_UNKNOWN;
  }
  if (operand_is_address_register_direct(&candidate->operands[operand_index], &reg)) {
    *out_value = state->a[reg];
    return out_value->kind != M68K_FACTS_V2_TRACE_UNKNOWN;
  }
  if (m68k_asm_operand_absolute_value(candidate->operand_kinds[operand_index], &candidate->operands[operand_index],
      &value)) {
    slot = trace_state_find_absolute_slot_const(state, value);
    if (slot != NULL) {
      *out_value = slot->value;
      return out_value->kind != M68K_FACTS_V2_TRACE_UNKNOWN;
    }
    if (value < section->size) {
      trace_value_set_source_offset(out_value, section_index, value);
      return 1;
    }
  }
  if (operand_is_stack_postincrement(&candidate->operands[operand_index])) {
    stack_slot = trace_state_find_stack_slot_const(state, 0U);
    if (stack_slot != NULL) {
      *out_value = stack_slot->value;
      return out_value->kind != M68K_FACTS_V2_TRACE_UNKNOWN;
    }
  }
  if (operand_immediate_value(candidate->operand_kinds[operand_index], &candidate->operands[operand_index],
      &value)) {
    if (candidate->size_suffix != 'l') return 0;
    trace_value_set_runtime_address_with_origin(out_value, value, section_index, candidate->offset, operand_index);
    return 1;
  }
  return 0;
}

static int trace_value_from_candidate_address_operand(size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, size_t operand_index, M68kFactsV2TraceValue *out_value) {
  uint32_t value = 0U;
  if (out_value != NULL) trace_value_set_unknown(out_value);
  if (section == NULL || candidate == NULL || out_value == NULL || operand_index >= candidate->operand_count)
    return 0;
  if (candidate_operand_data_target_offset(candidate, operand_index, section_index, &value)) {
    trace_value_set_source_offset_with_origin(out_value, section_index, value, section_index, candidate->offset,
      operand_index);
    return 1;
  }
  if (m68k_asm_operand_absolute_value(candidate->operand_kinds[operand_index], &candidate->operands[operand_index],
      &value)) {
    trace_value_set_runtime_address_with_origin(out_value, value, section_index, candidate->offset, operand_index);
    return 1;
  }
  return 0;
}

static int control_address_to_section_offset(const M68kRuntimeAddressSpace *runtime_addresses,
    size_t section_index, uint32_t section_size, uint32_t address, uint32_t *out_offset) {
  uint32_t mapped_offset = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (out_offset == NULL) return 0;
  if (runtime_address_space_translate(runtime_addresses, section_index, address, section_size,
      &mapped_offset)) {
    *out_offset = mapped_offset;
    return 1;
  }
  if (address < section_size) {
    *out_offset = address;
    return 1;
  }
  return 0;
}

static int trace_value_to_table_storage_offset(const M68kFactsV2TraceValue *value,
    const M68kRuntimeAddressSpace *runtime_addresses, size_t section_index, uint32_t section_size,
    uint32_t *out_offset) {
  uint32_t mapped_offset = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (value == NULL || out_offset == NULL) return 0;
  if (value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
    if (value->section_index != section_index || value->value >= section_size) return 0;
    *out_offset = value->value;
    return 1;
  }
  if (value->kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS ||
      value->kind == M68K_FACTS_V2_TRACE_CONSTANT) {
    if (!control_address_to_section_offset(runtime_addresses, section_index, section_size,
        value->value, &mapped_offset)) {
      return 0;
    }
    *out_offset = mapped_offset;
    return 1;
  }
  return 0;
}

static int trace_value_to_table_base_address(const M68kFactsV2TraceValue *value, size_t section_index,
    uint32_t section_size, uint32_t *out_address) {
  if (out_address != NULL) *out_address = 0U;
  if (value == NULL || out_address == NULL) return 0;
  if (value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
    if (value->section_index != section_index || value->value >= section_size) return 0;
    *out_address = value->value;
    return 1;
  }
  if (value->kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS ||
      value->kind == M68K_FACTS_V2_TRACE_CONSTANT) {
    *out_address = value->value;
    return 1;
  }
  return 0;
}

static int candidate_operand_data_target_offset(const M68kDecodeCandidate *candidate, size_t operand_index,
    size_t section_index, uint32_t *out_offset) {
  size_t target_index;
  if (out_offset != NULL) *out_offset = 0U;
  if (candidate == NULL || out_offset == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_DATA && target->has_operand &&
        target->operand_index == operand_index && target->has_section &&
        target->section_index == section_index) {
      *out_offset = target->offset;
      return 1;
    }
  }
  return 0;
}

static int trace_state_indexed_table_base_offset(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, size_t operand_index, const M68kFactsV2TraceState *state,
    const M68kRuntimeAddressSpace *runtime_addresses, uint32_t *out_offset) {
  const M68kAsmOperandValue *operand;
  uint32_t base = 0U;
  int32_t displacement = 0;
  int64_t target;
  if (out_offset != NULL) *out_offset = 0U;
  if (section == NULL || candidate == NULL || state == NULL || out_offset == NULL ||
      operand_index >= candidate->operand_count) {
    return 0;
  }
  if (candidate_operand_data_target_offset(candidate, operand_index, section->section_index, out_offset))
    return 1;
  operand = &candidate->operands[operand_index];
  if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA || operand->ea_reg >= 8U) return 0;
  if (!trace_value_to_table_storage_offset(&state->a[operand->ea_reg], runtime_addresses,
      section->section_index, section->size, &base))
    return 0;
  displacement = (int32_t)operand->value;
  target = (int64_t)(uint64_t)base + (int64_t)displacement;
  if (target < 0 || target >= (int64_t)(uint64_t)section->size) return 0;
  *out_offset = (uint32_t)target;
  return 1;
}

static int facts_v2_ea_shape_is_indexed_or_pc_indexed(uint8_t shape) {
  return shape == M68K_SIM_EA_SHAPE_INDEX || shape == M68K_SIM_EA_SHAPE_PC_INDEX;
}

static int facts_v2_instruction_operand_is_indexed_or_pc_indexed(const M68kInstructionIR *instruction,
    size_t operand_index) {
  if (instruction == NULL || operand_index >= instruction->operand_count) return 0;
  return facts_v2_ea_shape_is_indexed_or_pc_indexed(
    m68k_instruction_operand_decoded_ea_shape(&instruction->operands[operand_index]));
}

static int facts_v2_asm_operand_is_indexed_or_pc_indexed(const M68kAsmOperandValue *operand) {
  M68kOperandIR ir_operand;
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_EA) return 0;
  memset(&ir_operand, 0, sizeof(ir_operand));
  ir_operand.kind = M68K_ASM_OPERAND_EA;
  ir_operand.value = *operand;
  return facts_v2_ea_shape_is_indexed_or_pc_indexed(
    m68k_instruction_operand_decoded_ea_shape(&ir_operand));
}

static int control_target_starts_in_zero_padding(const M68kDecodeSectionIR *section, uint32_t target_offset) {
  enum { ZERO_PADDING_TARGET_MIN = 16U };
  uint32_t index;
  if (section == NULL || section->data == NULL || target_offset > section->size ||
      section->size - target_offset < ZERO_PADDING_TARGET_MIN) {
    return 0;
  }
  for (index = 0U; index < ZERO_PADDING_TARGET_MIN; ++index) {
    if (section->data[target_offset + index] != 0U) return 0;
  }
  return 1;
}

static int control_target_address_starts_in_zero_padding(const M68kDecodeSectionIR *section,
    const M68kRuntimeAddressSpace *runtime_addresses, size_t section_index, uint32_t target_address) {
  uint32_t target_offset = 0U;
  if (section == NULL) return 0;
  if (runtime_address_space_translate(runtime_addresses, section_index, target_address, section->size,
      &target_offset)) {
    return control_target_starts_in_zero_padding(section, target_offset);
  }
  if (target_address < section->size) return control_target_starts_in_zero_padding(section, target_address);
  return 0;
}

static uint32_t scan_long_control_target_table(const M68kDecodeSectionIR *section,
    const M68kRuntimeAddressSpace *runtime_addresses, const uint8_t *accepted_bytes, uint32_t table_offset,
    uint32_t *targets, uint32_t target_limit) {
  uint32_t cursor;
  uint32_t target_count = 0U;
  if (section == NULL || section->data == NULL || targets == NULL || target_limit == 0U ||
      table_offset >= section->size) {
    return 0U;
  }
  for (cursor = table_offset; cursor + 4U <= section->size && target_count < target_limit; cursor += 4U) {
    uint32_t target = m68k_read_u32be(section->data + cursor);
    uint32_t target_offset = 0U;
    if (accepted_range_has_code_byte_local(accepted_bytes, section->size, cursor, 4U)) break;
    if (target == 0U) continue;
    if ((target & 1U) != 0U || !control_address_to_section_offset(runtime_addresses,
        section->section_index, section->size, target, &target_offset)) {
      break;
    }
    if (control_target_starts_in_zero_padding(section, target_offset)) break;
    targets[target_count++] = target;
  }
  return target_count >= 2U ? target_count : 0U;
}

static uint32_t scan_word_relative_control_target_table(const M68kDecodeSectionIR *section,
    const M68kRuntimeAddressSpace *runtime_addresses, const uint8_t *accepted_start,
    const uint8_t *accepted_bytes, uint32_t table_offset, uint32_t base_address, uint32_t *targets,
    uint32_t target_limit) {
  uint32_t cursor;
  uint32_t target_count = 0U;
  uint32_t first_forward_target = UINT32_MAX;
  uint32_t base_source_offset = 0U;
  uint8_t saw_far_displacement = 0U;
  if (section == NULL || section->data == NULL || targets == NULL || target_limit == 0U ||
      table_offset >= section->size || !control_address_to_section_offset(runtime_addresses,
        section->section_index, section->size, base_address, &base_source_offset)) {
    return 0U;
  }
  for (cursor = table_offset; cursor + 2U <= section->size && target_count < target_limit; cursor += 2U) {
    int32_t displacement = (int32_t)(int16_t)m68k_read_u16be(section->data + cursor);
    int64_t target64 = (int64_t)(uint64_t)base_address + (int64_t)displacement;
    uint32_t target_address;
    uint32_t target_offset = 0U;
    if (accepted_range_has_code_byte_local(accepted_bytes, section->size, cursor, 2U)) break;
    if (target_count >= 2U && cursor == base_source_offset && displacement == 0) break;
    if (saw_far_displacement && target_count >= 2U && cursor != table_offset && displacement == 0 &&
        cursor + 4U <= section->size && m68k_read_u16be(section->data + cursor + 2U) == 0U) {
      break;
    }
    if (displacement < -M68K_FACTS_V2_WORD_DISPATCH_LOCAL_LIMIT ||
        displacement > M68K_FACTS_V2_WORD_DISPATCH_LOCAL_LIMIT) break;
    if (displacement < -M68K_FACTS_V2_WORD_DISPATCH_FAR_BOUNDARY_MIN ||
        displacement > M68K_FACTS_V2_WORD_DISPATCH_FAR_BOUNDARY_MIN) {
      saw_far_displacement = 1U;
    }
    if (target64 < 0 || target64 > (int64_t)(uint64_t)UINT32_MAX) break;
    target_address = (uint32_t)target64;
    if ((target_address & 1U) != 0U || !control_address_to_section_offset(runtime_addresses,
        section->section_index, section->size, target_address, &target_offset)) {
      break;
    }
    if (control_target_starts_in_zero_padding(section, target_offset)) break;
    if (accepted_offset_is_interior(section, accepted_start, accepted_bytes, target_offset)) break;
    targets[target_count++] = target_address;
    if (target_offset > table_offset && target_offset < first_forward_target)
      first_forward_target = target_offset;
    if (target_count >= 2U && first_forward_target != UINT32_MAX && cursor + 2U >= first_forward_target) break;
  }
  return target_count >= 2U ? target_count : 0U;
}

static uint32_t scan_keyed_long_relative_control_target_table(const M68kDecodeSectionIR *section,
    const M68kRuntimeAddressSpace *runtime_addresses, const uint8_t *accepted_start,
    const uint8_t *accepted_bytes, uint32_t table_offset, uint32_t base_address, uint32_t *targets,
    uint32_t target_limit) {
  uint32_t cursor;
  uint32_t target_count = 0U;
  uint32_t first_forward_target = UINT32_MAX;
  if (section == NULL || section->data == NULL || runtime_addresses == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || targets == NULL || target_limit == 0U || table_offset >= section->size) {
    return 0U;
  }
  for (cursor = table_offset; cursor + 4U <= section->size && target_count < target_limit; cursor += 4U) {
    uint32_t entry = m68k_read_u32be(section->data + cursor);
    int32_t displacement;
    int64_t target64;
    uint32_t target_address;
    uint32_t target_offset = 0U;
    if (accepted_range_has_code_byte_local(accepted_bytes, section->size, cursor, 4U)) break;
    if (entry == 0U) break;
    displacement = (int32_t)(int16_t)((entry >> 16U) & 0xFFFFU);
    if (displacement < -M68K_FACTS_V2_WORD_DISPATCH_LOCAL_LIMIT ||
        displacement > M68K_FACTS_V2_WORD_DISPATCH_LOCAL_LIMIT) break;
    target64 = (int64_t)(uint64_t)base_address + (int64_t)displacement;
    if (target64 < 0 || target64 > (int64_t)(uint64_t)UINT32_MAX) break;
    target_address = (uint32_t)target64;
    if ((target_address & 1U) != 0U || !control_address_to_section_offset(runtime_addresses,
        section->section_index, section->size, target_address, &target_offset)) {
      break;
    }
    if (control_target_starts_in_zero_padding(section, target_offset)) break;
    if (accepted_offset_is_interior(section, accepted_start, accepted_bytes, target_offset)) break;
    targets[target_count++] = target_address;
    if (target_offset > table_offset && target_offset < first_forward_target)
      first_forward_target = target_offset;
    if (target_count >= 2U && first_forward_target != UINT32_MAX && cursor + 4U >= first_forward_target)
      break;
  }
  return target_count >= 2U ? target_count : 0U;
}

static int trace_state_candidate_loads_long_target_table(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *before,
    const M68kRuntimeAddressSpace *runtime_addresses, const uint8_t *accepted_bytes, uint8_t *out_dest_reg,
    M68kFactsV2TraceValue *out_value, M68kFactsV2TableBaseRef *out_base_ref) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t dest_reg = 0U;
  uint8_t base_reg = 0U;
  uint32_t table_offset = 0U;
  uint32_t scan_offset = 0U;
  uint32_t targets[M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT];
  uint32_t target_count;
  size_t source_index = (size_t)-1;
  size_t dest_index = (size_t)-1;
  size_t operand_index;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_value != NULL) trace_value_set_unknown(out_value);
  if (out_base_ref != NULL) memset(out_base_ref, 0, sizeof(*out_base_ref));
  if (section == NULL || candidate == NULL || before == NULL || out_dest_reg == NULL || out_value == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return 0;
  if (metadata->source_operand_index < candidate->operand_count)
    source_index = metadata->source_operand_index;
  if (metadata->dest_operand_index < candidate->operand_count)
    dest_index = metadata->dest_operand_index;
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    if (source_index == (size_t)-1 &&
        metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        metadata->operand_ea_uses_index[operand_index]) {
      source_index = operand_index;
    }
    if (dest_index == (size_t)-1 &&
        metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        operand_is_address_register_direct(&candidate->operands[operand_index], &dest_reg)) {
      dest_index = operand_index;
    }
  }
  if ((source_index == (size_t)-1 || dest_index == (size_t)-1) && candidate->operand_count == 2U &&
      operand_is_address_register_direct(&candidate->operands[1], &dest_reg) &&
      candidate->operand_kinds[0] == M68K_ASM_OPERAND_EA &&
      facts_v2_instruction_operand_is_indexed_or_pc_indexed(&instruction, 0U)) {
    source_index = 0U;
    dest_index = 1U;
  }
  if (source_index >= candidate->operand_count || dest_index >= candidate->operand_count ||
      source_index >= instruction.operand_count || dest_index >= instruction.operand_count) {
    return 0;
  }
  if (!operand_is_address_register_direct(&candidate->operands[dest_index], &dest_reg)) return 0;
  if (!(metadata->operand_ea_uses_index[source_index] ||
        facts_v2_instruction_operand_is_indexed_or_pc_indexed(&instruction, source_index))) {
    return 0;
  }
  if (candidate->operand_kinds[source_index] == M68K_ASM_OPERAND_EA &&
      candidate->operands[source_index].ea_reg < 8U) {
    base_reg = candidate->operands[source_index].ea_reg;
  }
  if (!trace_state_indexed_table_base_offset(section, candidate, source_index, before,
      runtime_addresses, &table_offset))
    return 0;
  scan_offset = table_offset;
  target_count = scan_long_control_target_table(section, runtime_addresses, accepted_bytes, table_offset, targets,
    M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT);
  if (target_count == 0U && table_offset <= UINT32_MAX - 4U &&
      accepted_range_has_code_byte_local(accepted_bytes, section->size, table_offset, 4U)) {
    scan_offset = table_offset + 4U;
    target_count = scan_long_control_target_table(section, runtime_addresses, accepted_bytes, scan_offset,
      targets, M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT);
  }
  if (target_count == 0U) return 0;
  if (out_base_ref != NULL && base_reg < 8U && before->a[base_reg].kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS) {
    out_base_ref->valid = 1U;
    out_base_ref->has_origin = before->a[base_reg].has_origin;
    out_base_ref->origin_section_index = before->a[base_reg].origin_section_index;
    out_base_ref->origin_offset = before->a[base_reg].origin_offset;
    out_base_ref->origin_operand_index = before->a[base_reg].origin_operand_index;
    out_base_ref->table_offset = scan_offset;
    out_base_ref->base_runtime_address = before->a[base_reg].value;
  }
  *out_dest_reg = dest_reg;
  trace_value_set_target_set(out_value, section->section_index, targets, target_count);
  return 1;
}

static int trace_state_candidate_adds_word_target_table(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *before,
    const M68kRuntimeAddressSpace *runtime_addresses, const uint8_t *accepted_start,
    const uint8_t *accepted_bytes, uint8_t *out_dest_reg, M68kFactsV2TraceValue *out_value) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t dest_reg = 0U;
  uint32_t table_offset = 0U;
  uint32_t base_address = 0U;
  uint32_t targets[M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT];
  uint32_t target_count;
  size_t source_index = (size_t)-1;
  size_t dest_index = (size_t)-1;
  size_t operand_index;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_value != NULL) trace_value_set_unknown(out_value);
  if (section == NULL || candidate == NULL || before == NULL || out_dest_reg == NULL || out_value == NULL ||
      accepted_start == NULL || accepted_bytes == NULL ||
      candidate->size_suffix != 'w' || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_ADD) return 0;
  if (metadata->source_operand_index < candidate->operand_count)
    source_index = metadata->source_operand_index;
  if (metadata->dest_operand_index < candidate->operand_count)
    dest_index = metadata->dest_operand_index;
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    if (source_index == (size_t)-1 &&
        metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        metadata->operand_ea_uses_index[operand_index]) {
      source_index = operand_index;
    }
    if (dest_index == (size_t)-1 &&
        metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        operand_is_address_register_direct(&candidate->operands[operand_index], &dest_reg)) {
      dest_index = operand_index;
    }
  }
  if (source_index >= candidate->operand_count || dest_index >= candidate->operand_count ||
      source_index >= instruction.operand_count || dest_index >= instruction.operand_count) {
    return 0;
  }
  if (!operand_is_address_register_direct(&candidate->operands[dest_index], &dest_reg)) return 0;
  if (!(metadata->operand_ea_uses_index[source_index] ||
        facts_v2_instruction_operand_is_indexed_or_pc_indexed(&instruction, source_index))) {
    return 0;
  }
  if (!trace_value_to_table_base_address(&before->a[dest_reg], section->section_index, section->size,
      &base_address))
    return 0;
  if (!trace_state_indexed_table_base_offset(section, candidate, source_index, before,
      runtime_addresses, &table_offset))
    return 0;
  target_count = scan_word_relative_control_target_table(section, runtime_addresses, accepted_start, accepted_bytes,
    table_offset, base_address, targets, M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT);
  if (target_count == 0U) return 0;
  *out_dest_reg = dest_reg;
  trace_value_set_target_set(out_value, section->section_index, targets, target_count);
  return 1;
}

static int trace_state_candidate_loads_word_relative_target_table(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *before,
    const M68kRuntimeAddressSpace *runtime_addresses, const uint8_t *accepted_start,
    const uint8_t *accepted_bytes, uint8_t *out_dest_reg, uint8_t *out_dest_is_address,
    M68kFactsV2TraceValue *out_value) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t dest_reg = 0U;
  uint32_t table_offset = 0U;
  size_t source_index = (size_t)-1;
  size_t dest_index = (size_t)-1;
  size_t operand_index;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_dest_is_address != NULL) *out_dest_is_address = 0U;
  if (out_value != NULL) trace_value_set_unknown(out_value);
  (void)accepted_start;
  (void)accepted_bytes;
  if (section == NULL || candidate == NULL || before == NULL || out_dest_reg == NULL ||
      out_dest_is_address == NULL || out_value == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      candidate->size_suffix != 'w' || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return 0;
  if (metadata->source_operand_index < candidate->operand_count)
    source_index = metadata->source_operand_index;
  if (metadata->dest_operand_index < candidate->operand_count)
    dest_index = metadata->dest_operand_index;
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    if (source_index == (size_t)-1 &&
        metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        metadata->operand_ea_uses_index[operand_index]) {
      source_index = operand_index;
    }
    if (dest_index == (size_t)-1 &&
        metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        (operand_is_data_register_direct(&candidate->operands[operand_index], &dest_reg) ||
         operand_is_address_register_direct(&candidate->operands[operand_index], &dest_reg))) {
      dest_index = operand_index;
    }
  }
  if (source_index >= candidate->operand_count || dest_index >= candidate->operand_count ||
      source_index >= instruction.operand_count || dest_index >= instruction.operand_count) {
    return 0;
  }
  if (operand_is_address_register_direct(&candidate->operands[dest_index], &dest_reg)) {
    *out_dest_is_address = 1U;
  } else if (!operand_is_data_register_direct(&candidate->operands[dest_index], &dest_reg)) {
    return 0;
  }
  if (!(metadata->operand_ea_uses_index[source_index] ||
        facts_v2_instruction_operand_is_indexed_or_pc_indexed(&instruction, source_index))) {
    return 0;
  }
  if (!trace_state_indexed_table_base_offset(section, candidate, source_index, before,
      runtime_addresses, &table_offset))
    return 0;
  *out_dest_reg = dest_reg;
  trace_value_set_word_relative_table(out_value, section->section_index, table_offset);
  return 1;
}

static int trace_state_candidate_loads_keyed_long_relative_table_entry(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *before,
    const M68kRuntimeAddressSpace *runtime_addresses, uint8_t *out_dest_reg,
    M68kFactsV2TraceValue *out_value) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t source_reg = 0U;
  uint8_t dest_reg = 0U;
  uint32_t table_offset = 0U;
  size_t source_index = (size_t)-1;
  size_t dest_index = (size_t)-1;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_value != NULL) trace_value_set_unknown(out_value);
  if (section == NULL || candidate == NULL || before == NULL || runtime_addresses == NULL ||
      out_dest_reg == NULL || out_value == NULL || candidate->size_suffix != 'l' ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_MOVE) return 0;
  if (metadata->source_operand_index < candidate->operand_count)
    source_index = metadata->source_operand_index;
  if (metadata->dest_operand_index < candidate->operand_count)
    dest_index = metadata->dest_operand_index;
  if (source_index >= candidate->operand_count || dest_index >= candidate->operand_count ||
      source_index >= instruction.operand_count || dest_index >= instruction.operand_count) {
    return 0;
  }
  if (!operand_is_postincrement_address_register(candidate->operand_kinds[source_index],
      &candidate->operands[source_index], &source_reg) ||
      !operand_is_data_register_direct(&candidate->operands[dest_index], &dest_reg) ||
      !trace_value_to_table_storage_offset(&before->a[source_reg], runtime_addresses,
        section->section_index, section->size, &table_offset)) {
    return 0;
  }
  *out_dest_reg = dest_reg;
  trace_value_set_keyed_long_relative_table(out_value, section->section_index, table_offset);
  return 1;
}

static int trace_state_candidate_swaps_keyed_long_relative_table_entry(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *before,
    const M68kRuntimeAddressSpace *runtime_addresses, const uint8_t *accepted_start,
    const uint8_t *accepted_bytes, uint8_t *out_dest_reg, M68kFactsV2TraceValue *out_value) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t reg = 0U;
  uint32_t table_offset = 0U;
  uint32_t base_address = 0U;
  uint32_t targets[M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT];
  uint32_t target_count;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_value != NULL) trace_value_set_unknown(out_value);
  if (section == NULL || candidate == NULL || before == NULL || runtime_addresses == NULL ||
      accepted_start == NULL || accepted_bytes == NULL || out_dest_reg == NULL || out_value == NULL ||
      candidate->operand_count != 1U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_SWAP_WORDS ||
      !operand_is_data_register_direct(&candidate->operands[0], &reg) ||
      before->d[reg].kind != M68K_FACTS_V2_TRACE_KEYED_LONG_RELATIVE_TABLE ||
      before->d[reg].section_index != section->section_index) {
    return 0;
  }
  table_offset = before->d[reg].value;
  base_address = table_offset;
  (void)runtime_address_space_source_to_runtime_near(runtime_addresses, section->section_index, table_offset,
    0U, 0U, &base_address);
  target_count = scan_keyed_long_relative_control_target_table(section, runtime_addresses, accepted_start,
    accepted_bytes, table_offset, base_address, targets, M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT);
  if (target_count == 0U) return 0;
  *out_dest_reg = reg;
  trace_value_set_target_set(out_value, section->section_index, targets, target_count);
  return 1;
}

static void trace_state_apply_known_effects(size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2RelocationLookup *relocation_lookup,
    const M68kFactIR *facts, M68kFactsV2TraceState *state) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata = NULL;
  uint8_t reg = 0U;
  uint32_t value = 0U;
  size_t target_section = 0U;
  uint32_t target_offset = 0U;
  int handled_stack_update = 0;
  int handled_relocated_address = 0;
  if (candidate == NULL || state == NULL) return;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) == 0)
    metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata != NULL && metadata->operation_type == M68K_SIM_OP_PUSH_EA &&
      metadata->source_operand_index < candidate->operand_count) {
    M68kFactsV2TraceValue pushed_value;
    if (trace_value_from_candidate_address_operand(section_index, section, candidate,
        metadata->source_operand_index, &pushed_value)) {
      trace_state_push_stack_value(state, &pushed_value);
      handled_stack_update = 1;
    }
  }
  if (candidate_is_long_immediate_to_data_register(candidate, &reg, &value)) {
    if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) {
      value = m68k_sign_extend32(value, 8U);
      trace_state_set_data_register_constant(state, reg, value);
    } else {
      trace_state_set_data_register_constant_with_origin(state, reg, value, section_index, candidate->offset, 0U);
    }
  } else if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && candidate->size_suffix == 'w' &&
      candidate->operand_count == 2U &&
      operand_immediate_value(candidate->operand_kinds[0], &candidate->operands[0], &value) &&
      operand_is_data_register_direct(&candidate->operands[1], &reg)) {
    trace_state_set_data_register_low16(state, reg, (uint16_t)(value & 0xFFFFU), candidate->offset);
  }
  if (candidate_lea_pc_relative_data_target(candidate, section_index,
      section != NULL && section->size <= UINT32_MAX ? (uint32_t)section->size : 0U, &reg, &value)) {
    trace_value_set_source_offset(&state->a[reg], section_index, value);
  } else if (candidate_lea_relocated_address(relocation_lookup, facts, section_index, candidate, &reg,
      &target_section, &target_offset)) {
    trace_value_set_source_offset(&state->a[reg], target_section, target_offset);
    handled_relocated_address = 1;
  } else if (candidate_moves_relocated_address_to_address_register(relocation_lookup, facts, section_index,
      candidate, &reg, &target_section, &target_offset)) {
    trace_value_set_source_offset(&state->a[reg], target_section, target_offset);
    handled_relocated_address = 1;
  } else if (candidate_lea_absolute_address(candidate, &reg, &value)) {
    trace_value_set_runtime_address_with_origin(&state->a[reg], value, section_index, candidate->offset, 0U);
  }
  if (!handled_relocated_address && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
      candidate->operand_count == 2U &&
      operand_immediate_value(candidate->operand_kinds[0], &candidate->operands[0], &value) &&
      operand_is_address_register_direct(&candidate->operands[1], &reg)) {
    trace_value_set_runtime_address_with_origin(&state->a[reg], value, section_index, candidate->offset, 0U);
  } else if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && candidate->size_suffix == 'l' &&
      candidate->operand_count == 2U &&
      m68k_asm_operand_absolute_value(candidate->operand_kinds[0], &candidate->operands[0], &value) &&
      operand_is_address_register_direct(&candidate->operands[1], &reg)) {
    const M68kFactsV2AbsoluteSlot *slot = trace_state_find_absolute_slot_const(state, value);
    if (slot != NULL) state->a[reg] = slot->value;
  }
  if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && candidate->operand_count == 2U) {
    uint8_t source_reg = 0U;
    uint8_t dest_reg = 0U;
    uint32_t width = 0U;
    uint32_t dest_address = 0U;
    if (candidate->size_suffix == 'b') width = 1U;
    else if (candidate->size_suffix == 'w') width = 2U;
    else if (candidate->size_suffix == 'l') width = 4U;
    if (width != 0U &&
        operand_is_postincrement_address_register(candidate->operand_kinds[0], &candidate->operands[0],
          &source_reg) &&
        operand_is_postincrement_address_register(candidate->operand_kinds[1], &candidate->operands[1],
          &dest_reg)) {
      trace_value_advance(&state->a[source_reg], width);
      trace_value_advance(&state->a[dest_reg], width);
    }
    if (m68k_asm_operand_absolute_value(candidate->operand_kinds[1], &candidate->operands[1], &dest_address)) {
      M68kFactsV2TraceValue stored_value;
      if (width == 4U && trace_value_from_candidate_source(section_index, section, candidate, 0U, state,
          &stored_value)) {
        trace_state_set_absolute_slot(state, dest_address, &stored_value);
      } else {
        trace_state_clear_absolute_slot(state, dest_address);
      }
    }
    if (width == 4U && operand_is_stack_predecrement(&candidate->operands[1])) {
      M68kFactsV2TraceValue pushed_value;
      if (trace_value_from_candidate_source(section_index, section, candidate, 0U, state, &pushed_value))
        trace_state_push_stack_value(state, &pushed_value);
      else trace_state_clear_stack_slots(state);
      handled_stack_update = 1;
    } else if (width == 4U && operand_is_stack_postincrement(&candidate->operands[0])) {
      trace_state_pop_stack_long(state);
      handled_stack_update = 1;
    }
  }
  if (!handled_stack_update && metadata != NULL) {
    size_t operand_index;
    if (metadata->sp_effect_count != 0U) {
      trace_state_clear_stack_slots(state);
      return;
    }
    for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
      if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
          operand_is_address_register_direct(&candidate->operands[operand_index], &reg) && reg == 7U) {
        trace_state_clear_stack_slots(state);
        return;
      }
      if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_NONE &&
          candidate->operands[operand_index].kind == M68K_ASM_OPERAND_EA &&
          candidate->operands[operand_index].ea_reg == 7U) {
        trace_state_clear_stack_slots(state);
        return;
      }
    }
  }
}

static void trace_state_after_candidate(size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *before,
    const M68kFactsV2RelocationLookup *relocation_lookup, const M68kFactIR *facts,
    const M68kRuntimeAddressSpace *runtime_addresses, const uint8_t *accepted_start, const uint8_t *accepted_bytes,
    M68kFactsV2TraceState *after) {
  uint8_t table_dest_reg = 0U;
  uint8_t table_targets_are_data = 0U;
  uint8_t table_targets_are_address = 0U;
  M68kFactsV2TraceValue table_targets;
  uint8_t keyed_table_dest_reg = 0U;
  M68kFactsV2TraceValue keyed_table_value;
  int has_table_targets = 0;
  int has_keyed_table_value = 0;
  if (after == NULL) return;
  trace_value_set_unknown(&table_targets);
  trace_value_set_unknown(&keyed_table_value);
  has_table_targets = trace_state_candidate_loads_long_target_table(section, candidate, before, runtime_addresses,
    accepted_bytes, &table_dest_reg, &table_targets, NULL);
  if (!has_table_targets) {
    has_table_targets = trace_state_candidate_adds_word_target_table(section, candidate, before,
      runtime_addresses, accepted_start, accepted_bytes, &table_dest_reg, &table_targets);
  }
  if (!has_table_targets) {
    has_table_targets = trace_state_candidate_loads_word_relative_target_table(section, candidate, before,
      runtime_addresses, accepted_start, accepted_bytes, &table_dest_reg, &table_targets_are_address,
      &table_targets);
    table_targets_are_data = has_table_targets && !table_targets_are_address ? 1U : 0U;
  }
  if (!has_table_targets) {
    has_table_targets = trace_state_candidate_swaps_keyed_long_relative_table_entry(section, candidate, before,
      runtime_addresses, accepted_start, accepted_bytes, &table_dest_reg, &table_targets);
    table_targets_are_data = has_table_targets ? 1U : table_targets_are_data;
  }
  has_keyed_table_value = trace_state_candidate_loads_keyed_long_relative_table_entry(section, candidate, before,
    runtime_addresses, &keyed_table_dest_reg, &keyed_table_value);
  if (before != NULL) *after = *before;
  else trace_state_init_unknown(after);
  trace_state_kill_register_writes(candidate, after);
  trace_state_apply_move_value_copy(section_index, section, candidate, before, after);
  trace_state_apply_known_effects(section_index, section, candidate, relocation_lookup, facts, after);
  trace_state_apply_reglist_memory_read(section_index, section, candidate, runtime_addresses, after);
  trace_state_apply_predecrement_copy_entry(section_index, section, candidate, before, after);
  if (has_table_targets && table_dest_reg < 8U) {
    if (table_targets_are_data) after->d[table_dest_reg] = table_targets;
    else after->a[table_dest_reg] = table_targets;
  }
  if (has_keyed_table_value && keyed_table_dest_reg < 8U) {
    after->d[keyed_table_dest_reg] = keyed_table_value;
  }
}

static int candidate_moves_word_data_reg_to_data_reg(const M68kDecodeCandidate *candidate,
    uint8_t *out_source_reg, uint8_t *out_dest_reg) {
  uint8_t source_reg = 0U;
  uint8_t dest_reg = 0U;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
      candidate->size_suffix != 'w' || candidate->operand_count != 2U) {
    return 0;
  }
  if (!operand_is_data_register_direct(&candidate->operands[0], &source_reg) ||
      !operand_is_data_register_direct(&candidate->operands[1], &dest_reg)) {
    return 0;
  }
  if (out_source_reg != NULL) *out_source_reg = source_reg;
  if (out_dest_reg != NULL) *out_dest_reg = dest_reg;
  return 1;
}

static int candidate_moves_long_indirect_address_reg_to_same_reg(const M68kDecodeCandidate *candidate,
    uint8_t reg) {
  uint8_t source_reg = 0U;
  uint8_t dest_reg = 0U;
  return candidate != NULL && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
    candidate->size_suffix == 'l' && candidate->operand_count == 2U &&
    operand_is_plain_address_register_indirect(candidate->operand_kinds[0], &candidate->operands[0],
      &source_reg) &&
    operand_is_address_register_direct(&candidate->operands[1], &dest_reg) &&
    source_reg == reg && dest_reg == reg;
}

static int candidate_moves_long_address_reg_slot_to_same_reg(const M68kDecodeCandidate *candidate,
    uint8_t reg, int32_t displacement) {
  uint8_t source_reg = 0U;
  uint8_t dest_reg = 0U;
  int32_t slot_displacement = 0;
  return candidate != NULL && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
    candidate->size_suffix == 'l' && candidate->operand_count == 2U &&
    candidate_operand_base_field_slot(candidate, 0U, &source_reg, &slot_displacement) &&
    operand_is_address_register_direct(&candidate->operands[1], &dest_reg) &&
    source_reg == reg && dest_reg == reg && slot_displacement == displacement;
}

static int candidate_adds_address_reg_to_same_reg(const M68kDecodeCandidate *candidate, uint8_t reg) {
  uint8_t source_reg = 0U;
  uint8_t dest_reg = 0U;
  return candidate != NULL && candidate->mnemonic_id == M68K_ASM_MNEMONIC_ADDA &&
    candidate->size_suffix == 'l' && candidate->operand_count == 2U &&
    operand_is_address_register_direct(&candidate->operands[0], &source_reg) &&
    operand_is_address_register_direct(&candidate->operands[1], &dest_reg) &&
    source_reg == reg && dest_reg == reg;
}

static int candidate_dbcc_branches_to_offset_with_reg(const M68kDecodeCandidate *candidate, uint8_t reg,
    uint32_t target_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t target_index;
  uint8_t db_reg = 0U;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_DBCC ||
      metadata->source_operand_index >= candidate->operand_count ||
      !operand_is_data_register_direct(&candidate->operands[metadata->source_operand_index], &db_reg) ||
      db_reg != reg) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH && target->has_section &&
        target->offset == target_offset) {
      return 1;
    }
  }
  return 0;
}

static int candidate_addq_long_to_address_reg(const M68kDecodeCandidate *candidate, uint8_t reg,
    uint32_t expected_value) {
  uint8_t dest_reg = 0U;
  uint32_t value = 0U;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_ADDQ ||
      candidate->size_suffix != 'l' || candidate->operand_count != 2U) {
    return 0;
  }
  if (!operand_immediate_value(candidate->operand_kinds[0], &candidate->operands[0], &value) ||
      value != expected_value ||
      !operand_is_address_register_direct(&candidate->operands[1], &dest_reg) || dest_reg != reg) {
    return 0;
  }
  return 1;
}

static int candidate_is_rts(const M68kDecodeCandidate *candidate) {
  return candidate != NULL && candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTS;
}

static int resolve_platform_loadseg_helper_summary(M68kDecodeIR *decode, uint8_t platform_kind,
    size_t section_index, const M68kDecodeSectionIR *section, uint32_t target_offset, uint8_t max_cpu,
    uint8_t *out_count_reg, uint8_t *out_result_reg, size_t *out_anchor_section_index) {
  const M68kDecodeCandidate *candidate;
  uint32_t cursor;
  uint32_t loop_offset;
  uint8_t count_reg = 0U;
  uint8_t loop_reg = 0U;
  uint8_t result_reg = 0U;
  uint32_t base_offset = 0U;
  int32_t addend = 0;
  if (out_count_reg != NULL) *out_count_reg = 0U;
  if (out_result_reg != NULL) *out_result_reg = 0U;
  if (out_anchor_section_index != NULL) *out_anchor_section_index = 0U;
  if (decode == NULL || section == NULL || out_count_reg == NULL || out_result_reg == NULL ||
      out_anchor_section_index == NULL || target_offset >= section->size) {
    return 0;
  }
  candidate = ensure_candidate_at_offset(decode, section, target_offset, max_cpu);
  if (!candidate_moves_word_data_reg_to_data_reg(candidate, &count_reg, &loop_reg) ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  candidate = ensure_candidate_at_offset(decode, section, cursor, max_cpu);
  if (candidate == NULL || candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  if (candidate_lea_platform_section_anchor(candidate, platform_kind, &result_reg, &base_offset, &addend)) {
    if (base_offset != 0U || addend != -4) return 0;
  } else if (candidate_lea_pc_relative_data_target(candidate, section_index, section->size, &result_reg,
      &base_offset)) {
    if (base_offset != 0U) return 0;
    addend = 0;
  } else {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  loop_offset = cursor;
  candidate = ensure_candidate_at_offset(decode, section, cursor, max_cpu);
  if (!((addend == -4 && candidate_moves_long_indirect_address_reg_to_same_reg(candidate, result_reg)) ||
        (addend == 0 && candidate_moves_long_address_reg_slot_to_same_reg(candidate, result_reg, -4))) ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  candidate = ensure_candidate_at_offset(decode, section, cursor, max_cpu);
  if (!candidate_adds_address_reg_to_same_reg(candidate, result_reg) ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  candidate = ensure_candidate_at_offset(decode, section, cursor, max_cpu);
  if (!candidate_adds_address_reg_to_same_reg(candidate, result_reg) ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  candidate = ensure_candidate_at_offset(decode, section, cursor, max_cpu);
  if (!candidate_dbcc_branches_to_offset_with_reg(candidate, loop_reg, loop_offset) ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  candidate = ensure_candidate_at_offset(decode, section, cursor, max_cpu);
  if (!candidate_addq_long_to_address_reg(candidate, result_reg, 4U) ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  cursor = candidate->offset + candidate->byte_count;
  candidate = ensure_candidate_at_offset(decode, section, cursor, max_cpu);
  if (!candidate_is_rts(candidate)) return 0;
  *out_count_reg = count_reg;
  *out_result_reg = result_reg;
  *out_anchor_section_index = section_index;
  return 1;
}

static int trace_state_apply_platform_loadseg_helper_call(M68kDecodeIR *decode, uint8_t platform_kind,
    size_t section_index, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kFactsV2TraceState *before, uint8_t max_cpu, M68kFactsV2TraceState *after) {
  size_t target_index;
  if (decode == NULL || section == NULL || candidate == NULL || before == NULL || after == NULL ||
      (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR && candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR)) {
    return 0;
  }
  if (!platform_facts_v2_supports_loadseg_segment_chain(platform_kind)) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    uint8_t count_reg = 0U;
    uint8_t result_reg = 0U;
    size_t anchor_section_index = 0U;
    uint32_t link_hops = 0U;
    size_t body_section_index = 0U;
    if (target->kind != M68K_DECODE_TARGET_CALL || !target->has_section ||
        target->section_index != section_index) {
      continue;
    }
    if (!resolve_platform_loadseg_helper_summary(decode, platform_kind, section_index, section, target->offset,
        max_cpu, &count_reg, &result_reg, &anchor_section_index)) {
      continue;
    }
    if (!m68k_bitset_u32_has(before->d_low16_known, count_reg)) continue;
    link_hops = (uint32_t)before->d_low16[count_reg] + 1U;
    if (!platform_facts_v2_loadseg_segment_body_for_hops(platform_kind, decode->section_count,
        anchor_section_index, link_hops, &body_section_index) ||
        body_section_index >= decode->section_count ||
        decode->sections[body_section_index].kind != M68K_SECTION_CODE ||
        decode->sections[body_section_index].size == 0U) {
      continue;
    }
    trace_value_set_source_offset_with_reason(&after->a[result_reg], body_section_index, 0U,
      M68K_FACT_CODE_START_REASON_PLATFORM_LOADSEG_ENTRY);
    return 1;
  }
  return 0;
}

static int trace_state_candidate_loads_platform_loadseg_segment_link(M68kDecodeIR *decode, uint8_t platform_kind,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *before,
    size_t *out_target_section_index) {
  uint8_t reg;
  size_t target_section_index = 0U;
  const M68kFactsV2TraceValue *base;
  if (out_target_section_index != NULL) *out_target_section_index = (size_t)-1;
  if (decode == NULL || candidate == NULL || before == NULL ||
      !platform_facts_v2_supports_loadseg_segment_chain(platform_kind)) {
    return 0;
  }
  for (reg = 0U; reg < 8U; ++reg) {
    if (!candidate_moves_long_address_reg_slot_to_same_reg(candidate, reg, -4)) continue;
    base = &before->a[reg];
    if (base->kind != M68K_FACTS_V2_TRACE_SOURCE_OFFSET || base->value != 0U) continue;
    if (platform_facts_v2_loadseg_segment_body_for_hops(platform_kind, decode->section_count,
        base->section_index, 1U, &target_section_index) &&
        target_section_index < decode->section_count) {
      if (out_target_section_index != NULL) *out_target_section_index = target_section_index;
    }
    return 1;
  }
  return 0;
}

static int candidate_pushes_address_reg_to_stack(const M68kDecodeCandidate *candidate, uint8_t *out_reg) {
  uint8_t reg = 0U;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
      candidate->size_suffix != 'l' || candidate->operand_count != 2U) {
    return 0;
  }
  if (!operand_is_address_register_direct(&candidate->operands[0], &reg)) return 0;
  if (!operand_is_stack_predecrement(&candidate->operands[1])) return 0;
  if (out_reg != NULL) *out_reg = reg;
  return 1;
}

static int candidate_loads_return_slot_to_address_reg(const M68kDecodeCandidate *candidate, uint8_t reg) {
  uint8_t dest_reg = 0U;
  return candidate != NULL && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
    candidate->size_suffix == 'l' && candidate->operand_count == 2U &&
    operand_is_stack_displacement(&candidate->operands[0], 4U) &&
    operand_is_address_register_direct(&candidate->operands[1], &dest_reg) && dest_reg == reg;
}

static int candidate_stores_address_reg_to_return_slot(const M68kDecodeCandidate *candidate, uint8_t reg) {
  uint8_t source_reg = 0U;
  return candidate != NULL && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
    candidate->size_suffix == 'l' && candidate->operand_count == 2U &&
    operand_is_address_register_direct(&candidate->operands[0], &source_reg) && source_reg == reg &&
    operand_is_stack_displacement(&candidate->operands[1], 4U);
}

static int candidate_loads_stack_slot_to_address_reg(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
    uint32_t *out_displacement) {
  uint8_t dest_reg = 0U;
  uint32_t displacement = 0U;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA ||
      candidate->size_suffix != 'l' || candidate->operand_count != 2U ||
      !operand_stack_displacement_value(&candidate->operands[0], &displacement) ||
      !operand_is_address_register_direct(&candidate->operands[1], &dest_reg)) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = dest_reg;
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static int candidate_reads_inline_word_from_address_reg(const M68kDecodeCandidate *candidate, uint8_t reg) {
  uint8_t source_reg = 0U;
  return candidate != NULL && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
    candidate->size_suffix == 'w' && candidate->operand_count >= 1U &&
    operand_is_postincrement_address_register(candidate->operand_kinds[0], &candidate->operands[0],
      &source_reg) && source_reg == reg;
}

static int candidate_stores_address_reg_to_stack_slot(const M68kDecodeCandidate *candidate, uint8_t reg,
    uint32_t displacement) {
  uint8_t source_reg = 0U;
  return candidate != NULL && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
    candidate->size_suffix == 'l' && candidate->operand_count == 2U &&
    operand_is_address_register_direct(&candidate->operands[0], &source_reg) && source_reg == reg &&
    operand_is_stack_displacement(&candidate->operands[1], displacement);
}

static int candidate_pops_address_reg_from_stack(const M68kDecodeCandidate *candidate, uint8_t reg) {
  uint8_t dest_reg = 0U;
  return candidate != NULL && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
    candidate->size_suffix == 'l' && candidate->operand_count == 2U &&
    operand_is_stack_postincrement(&candidate->operands[0]) &&
    operand_is_address_register_direct(&candidate->operands[1], &dest_reg) && dest_reg == reg;
}

static int callee_rewrites_return_address_from_string_cursor(M68kDecodeIR *decode,
    const M68kDecodeSectionIR *section, uint32_t target_offset, uint8_t max_cpu) {
  const M68kDecodeCandidate *candidate;
  uint8_t reg = 0U;
  uint32_t offset;
  uint32_t scan_end;
  int saw_store = 0;
  int saw_pop = 0;
  if (section == NULL || target_offset >= section->size || (target_offset & 1U) != 0U) return 0;
  candidate = ensure_candidate_at_offset(decode, section, target_offset, max_cpu);
  if (!candidate_pushes_address_reg_to_stack(candidate, &reg)) return 0;
  offset = candidate->offset + candidate->byte_count;
  candidate = ensure_candidate_at_offset(decode, section, offset, max_cpu);
  if (!candidate_loads_return_slot_to_address_reg(candidate, reg)) return 0;
  offset = candidate->offset + candidate->byte_count;
  scan_end = target_offset + 160U;
  if (scan_end < target_offset || scan_end > section->size) scan_end = section->size;
  while (offset < scan_end) {
    candidate = ensure_candidate_at_offset(decode, section, offset, max_cpu);
    if (candidate == NULL || candidate->byte_count == 0U) return 0;
    if (candidate_stores_address_reg_to_return_slot(candidate, reg)) saw_store = 1;
    else if (candidate_pops_address_reg_from_stack(candidate, reg)) saw_pop = 1;
    else if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTS) return saw_store && saw_pop;
    offset = candidate->offset + candidate->byte_count;
  }
  return 0;
}

static int callee_rewrites_return_address_after_inline_word(M68kDecodeIR *decode,
    const M68kDecodeSectionIR *section, uint32_t target_offset, uint8_t max_cpu) {
  const M68kDecodeCandidate *candidate;
  uint8_t reg = 0U;
  uint32_t displacement = 0U;
  uint32_t offset;
  uint32_t scan_end;
  int saw_load = 0;
  int saw_read = 0;
  if (section == NULL || target_offset >= section->size || (target_offset & 1U) != 0U) return 0;
  offset = target_offset;
  scan_end = target_offset + 96U;
  if (scan_end < target_offset || scan_end > section->size) scan_end = section->size;
  while (offset < scan_end) {
    candidate = ensure_candidate_at_offset(decode, section, offset, max_cpu);
    if (candidate == NULL || candidate->byte_count == 0U) return 0;
    if (!saw_load) {
      if (candidate_loads_stack_slot_to_address_reg(candidate, &reg, &displacement)) saw_load = 1;
    } else if (!saw_read) {
      if (candidate_reads_inline_word_from_address_reg(candidate, reg)) {
        saw_read = 1;
      } else if (candidate_clobbers_address_register(candidate, reg)) {
        return 0;
      }
    } else if (candidate_stores_address_reg_to_stack_slot(candidate, reg, displacement)) {
      return 1;
    } else if (candidate_clobbers_address_register(candidate, reg)) {
      return 0;
    }
    if (candidate_is_rts(candidate)) return 0;
    if (candidate->offset > UINT32_MAX - candidate->byte_count) return 0;
    offset = candidate->offset + candidate->byte_count;
  }
  return 0;
}

static int is_inline_string_byte(uint8_t value) {
  return (value >= 0x20U && value <= 0x7EU) || value == '\r' || value == '\n' || value == '\t';
}

static int find_inline_string_payload_end(const M68kDecodeSectionIR *section, uint32_t offset,
    uint32_t *out_end) {
  uint32_t cursor;
  uint32_t scan_end;
  uint32_t string_bytes = 0U;
  if (section == NULL || section->data == NULL || out_end == NULL || offset >= section->size) return 0;
  cursor = offset;
  scan_end = offset + 2048U;
  if (scan_end < offset || scan_end > section->size) scan_end = section->size;
  while (cursor < scan_end) {
    uint8_t value = section->data[cursor++];
    if (value == 0U) {
      uint32_t end = cursor;
      if (string_bytes < 3U) return 0;
      if ((end & 1U) != 0U) ++end;
      if (end > section->size) return 0;
      *out_end = end;
      return 1;
    }
    if (!is_inline_string_byte(value)) return 0;
    ++string_bytes;
  }
  return 0;
}

static int call_consumes_inline_string_payload(M68kDecodeIR *decode, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t fallthrough, uint32_t *out_resume_offset, uint8_t max_cpu) {
  size_t target_index;
  if (section == NULL || candidate == NULL || out_resume_offset == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR && candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_CALL || !target->has_section ||
        target->section_index != section->section_index) {
      continue;
    }
    if (!callee_rewrites_return_address_from_string_cursor(decode, section, target->offset, max_cpu)) continue;
    if (find_inline_string_payload_end(section, fallthrough, out_resume_offset)) return 1;
  }
  return 0;
}

static int call_consumes_inline_word_payload(M68kDecodeIR *decode, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t fallthrough, uint32_t *out_resume_offset, uint8_t max_cpu) {
  size_t target_index;
  if (section == NULL || candidate == NULL || out_resume_offset == NULL ||
      fallthrough > section->size || section->size - fallthrough < 2U) {
    return 0;
  }
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR && candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_CALL || !target->has_section ||
        target->section_index != section->section_index) {
      continue;
    }
    if (!callee_rewrites_return_address_after_inline_word(decode, section, target->offset, max_cpu)) continue;
    *out_resume_offset = fallthrough + 2U;
    return 1;
  }
  return 0;
}

static int append_xref_fact(M68kFactIR *facts, size_t section_index, uint32_t source_offset,
    uint32_t target_offset, uint8_t confidence) {
  M68kFact fact;
  size_t fact_index;
  if (facts == NULL) return -1;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *existing = &facts->facts[fact_index];
    if (existing->kind == M68K_FACT_XREF && existing->section_index == section_index &&
        existing->offset == source_offset && existing->target_section_index == section_index &&
        existing->target_offset == target_offset) {
      return 0;
    }
  }
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_XREF;
  fact.confidence = confidence;
  fact.section_index = section_index;
  fact.offset = source_offset;
  fact.target_section_index = section_index;
  fact.target_offset = target_offset;
  return m68k_fact_ir_append(facts, &fact);
}

static int append_runtime_address_ref_fact(M68kFactIR *facts, size_t section_index, uint32_t source_offset,
    size_t operand_index, uint32_t target_offset, uint32_t runtime_address, uint8_t confidence) {
  return append_runtime_address_ref_fact_with_sink(facts, section_index, source_offset, operand_index,
    target_offset, runtime_address, 0U, confidence);
}

static int append_runtime_address_ref_fact_with_sink(M68kFactIR *facts, size_t section_index,
    uint32_t source_offset, size_t operand_index, uint32_t target_offset, uint32_t runtime_address,
    uint32_t sink_address, uint8_t confidence) {
  M68kFact fact;
  size_t fact_index;
  if (facts == NULL || operand_index > UINT32_MAX) return -1;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *existing = &facts->facts[fact_index];
    if (existing->kind == M68K_FACT_RUNTIME_ADDRESS_REF && existing->section_index == section_index &&
        existing->offset == source_offset && existing->reason == (uint32_t)operand_index &&
        existing->target_section_index == section_index && existing->target_offset == target_offset &&
        existing->has_runtime_address && existing->runtime_address == runtime_address &&
        existing->has_sink_address == (sink_address != 0U ? 1U : 0U) &&
        existing->sink_address == sink_address) {
      return 0;
    }
  }
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_REF;
  fact.confidence = confidence;
  fact.section_index = section_index;
  fact.offset = source_offset;
  fact.reason = (uint32_t)operand_index;
  fact.has_runtime_address = 1U;
  fact.runtime_address = runtime_address;
  if (sink_address != 0U) {
    fact.has_sink_address = 1U;
    fact.sink_address = sink_address;
  }
  fact.target_section_index = section_index;
  fact.target_offset = target_offset;
  return m68k_fact_ir_append(facts, &fact) == 0 ? 1 : -1;
}

static int append_external_runtime_address_ref_fact(M68kFactIR *facts, size_t section_index,
    uint32_t source_offset, size_t operand_index, uint32_t runtime_address, uint32_t sink_address,
    size_t sink_source_section_index, uint32_t sink_source_offset, uint8_t confidence) {
  M68kFact fact;
  size_t fact_index;
  if (facts == NULL || operand_index > UINT32_MAX) return -1;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *existing = &facts->facts[fact_index];
    if (existing->kind == M68K_FACT_RUNTIME_ADDRESS_REF && existing->section_index == section_index &&
        existing->offset == source_offset && existing->reason == (uint32_t)operand_index &&
        existing->target_section_index == (size_t)-1 && existing->has_runtime_address &&
        existing->runtime_address == runtime_address && existing->target_offset == sink_address &&
        existing->has_sink_address && existing->sink_address == sink_address &&
        existing->source_section_index == sink_source_section_index &&
        existing->source_offset == sink_source_offset) {
      return 0;
    }
  }
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_REF;
  fact.confidence = confidence;
  fact.section_index = section_index;
  fact.offset = source_offset;
  fact.reason = (uint32_t)operand_index;
  fact.has_runtime_address = 1U;
  fact.runtime_address = runtime_address;
  fact.has_sink_address = 1U;
  fact.sink_address = sink_address;
  fact.target_section_index = (size_t)-1;
  fact.target_offset = sink_address;
  fact.source_section_index = sink_source_section_index;
  fact.source_offset = sink_source_offset;
  return m68k_fact_ir_append(facts, &fact) == 0 ? 1 : -1;
}

static int append_runtime_address_range_fact(M68kFactIR *facts, size_t section_index, uint32_t source_offset,
    uint32_t runtime_address, uint32_t size, uint8_t kind, uint8_t confidence) {
  M68kFact fact;
  size_t fact_index;
  if (facts == NULL || size == 0U) return -1;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *existing = &facts->facts[fact_index];
    if (existing->kind == M68K_FACT_RUNTIME_ADDRESS_RANGE &&
        existing->section_index == section_index &&
        existing->offset == source_offset &&
        existing->runtime_address == runtime_address &&
        existing->size == size &&
        existing->runtime_kind == kind) {
      return 0;
    }
  }
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_RANGE;
  fact.confidence = confidence;
  fact.section_index = section_index;
  fact.offset = source_offset;
  fact.has_runtime_address = 1U;
  fact.runtime_kind = kind;
  fact.runtime_address = runtime_address;
  fact.source_section_index = section_index;
  fact.source_offset = source_offset;
  fact.size = size;
  return m68k_fact_ir_append(facts, &fact);
}

static int append_cross_section_xref_fact(M68kFactIR *facts, size_t source_section_index, uint32_t source_offset,
    size_t target_section_index, uint32_t target_offset, uint8_t confidence) {
  M68kFact fact;
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_XREF;
  fact.confidence = confidence;
  fact.section_index = source_section_index;
  fact.offset = source_offset;
  fact.target_section_index = target_section_index;
  fact.target_offset = target_offset;
  return m68k_fact_ir_append(facts, &fact);
}

static int append_violation_fact(M68kFactIR *facts, size_t section_index, uint32_t source_offset,
    uint32_t target_offset) {
  return append_violation_fact_with_reason(facts, section_index, source_offset, target_offset,
    M68K_FACT_CODE_START_REASON_UNKNOWN, section_index, source_offset);
}

static int append_violation_fact_with_reason(M68kFactIR *facts, size_t section_index, uint32_t source_offset,
    uint32_t target_offset, uint32_t reason, size_t reason_source_section_index, uint32_t reason_source_offset) {
  M68kFact fact;
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_VIOLATION;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = section_index;
  fact.offset = source_offset;
  fact.reason = reason;
  fact.source_section_index = reason_source_section_index;
  fact.source_offset = reason_source_offset;
  fact.target_section_index = section_index;
  fact.target_offset = target_offset;
  return m68k_fact_ir_append(facts, &fact);
}

static int candidate_is_absolute_control_transfer(const M68kDecodeCandidate *candidate) {
  M68kAsmOperandValue operand;
  if (candidate == NULL || candidate->operand_count != 1U) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR && candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP)
    return 0;
  operand = candidate->operands[0];
  operand.kind = candidate->operand_kinds[0];
  if (operand.kind == M68K_ASM_OPERAND_ABSL) return 1;
  return operand.kind == M68K_ASM_OPERAND_EA && operand.ea_mode == 7U &&
    (operand.ea_reg == 0U || operand.ea_reg == 1U);
}

static int candidate_absolute_control_address(const M68kDecodeCandidate *candidate, uint32_t *out_address) {
  if (candidate == NULL || (candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR) || candidate->operand_count != 1U ||
      out_address == NULL)
    return 0;
  return m68k_asm_operand_absolute_value(candidate->operand_kinds[0], &candidate->operands[0], out_address);
}

static void runtime_address_space_destroy(M68kRuntimeAddressSpace *space) {
  if (space == NULL) return;
  memset(space, 0, sizeof(*space));
}

static void runtime_address_space_init(M68kRuntimeAddressSpace *space, Arena *arena) {
  if (space == NULL) return;
  memset(space, 0, sizeof(*space));
  space->arena = arena;
}

static int runtime_address_conflict_is_temporal_overlay(const M68kRuntimeAddressRange *existing,
    size_t section_index, uint32_t source_offset, uint32_t runtime_address, uint32_t size, uint8_t kind) {
  uint64_t existing_start, existing_end, new_start, new_end;
  if (existing == NULL || kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
      existing->kind != M68K_FACT_RUNTIME_RANGE_KIND_POLICY ||
      existing->section_index != section_index || source_offset != 0U ||
      existing->source_offset != 0U || runtime_address >= existing->runtime_address || size == 0U) {
    return 0;
  }
  existing_start = existing->runtime_address;
  existing_end = existing_start + existing->size;
  new_start = runtime_address;
  new_end = new_start + size;
  return existing_start < new_end && new_start < existing_end;
}

static int runtime_address_space_add(M68kRuntimeAddressSpace *space, size_t section_index, uint32_t source_offset,
    uint32_t runtime_address, uint32_t size, uint8_t kind, uint8_t confidence, M68kFactIR *facts,
    M68kFactsV2Profile *profile) {
  size_t index;
  M68kRuntimeAddressRange *grown;
  size_t next_capacity;
  if (space == NULL || facts == NULL || size == 0U) return 0;
  for (index = 0U; index < space->count; ++index) {
    M68kRuntimeAddressRange *existing = &space->ranges[index];
    uint64_t existing_start = existing->runtime_address;
    uint64_t existing_end = existing_start + existing->size;
    uint64_t new_start = runtime_address;
    uint64_t new_end = new_start + size;
    if (existing->section_index == section_index && existing->source_offset == source_offset &&
        existing->runtime_address == runtime_address) {
      if (size > existing->size) {
        existing->size = size;
        if (append_runtime_address_range_fact(facts, section_index, source_offset, runtime_address, size, kind,
            confidence) != 0) {
          return -1;
        }
      }
      if (confidence > existing->confidence) existing->confidence = confidence;
      return 0;
    }
    if (existing->section_index == section_index && existing_start < new_end && new_start < existing_end) {
      uint64_t overlap_start = existing_start > new_start ? existing_start : new_start;
      uint64_t existing_source = (uint64_t)existing->source_offset + (overlap_start - existing_start);
      uint64_t new_source = (uint64_t)source_offset + (overlap_start - new_start);
      if (existing_source != new_source) {
        if (runtime_address_conflict_is_temporal_overlay(existing, section_index, source_offset, runtime_address,
            size, kind)) {
          continue;
        }
        if (profile != NULL) ++profile->runtime_address_range_conflicts;
        if (existing->confidence < M68K_FACT_CONFIDENCE_REQUIRED ||
            confidence < M68K_FACT_CONFIDENCE_REQUIRED) {
          if (kind == M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY &&
              confidence < M68K_FACT_CONFIDENCE_REQUIRED &&
              append_runtime_address_range_fact(facts, section_index, source_offset, runtime_address, size,
                M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY, confidence) != 0) {
            return -1;
          }
          return 0;
        }
        return -1;
      }
    }
  }
  if (space->count == space->capacity) {
    next_capacity = space->capacity == 0U ? 16U : space->capacity * 2U;
    grown = (M68kRuntimeAddressRange *)arena_realloc_copy(space->arena, space->ranges,
      space->capacity * sizeof(*space->ranges), next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    space->ranges = grown;
    space->capacity = next_capacity;
  }
  memset(&space->ranges[space->count], 0, sizeof(space->ranges[space->count]));
  space->ranges[space->count].section_index = section_index;
  space->ranges[space->count].source_offset = source_offset;
  space->ranges[space->count].runtime_address = runtime_address;
  space->ranges[space->count].size = size;
  space->ranges[space->count].kind = kind;
  space->ranges[space->count].confidence = confidence;
  ++space->count;
  if (profile != NULL) ++profile->runtime_address_ranges;
  return append_runtime_address_range_fact(facts, section_index, source_offset, runtime_address, size, kind,
    confidence);
}

static int runtime_address_space_translate(const M68kRuntimeAddressSpace *space, size_t section_index,
    uint32_t runtime_address, uint32_t section_size, uint32_t *out_source_offset) {
  size_t index;
  if (space == NULL || out_source_offset == NULL) return 0;
  for (index = space->count; index > 0U; --index) {
    const M68kRuntimeAddressRange *map = &space->ranges[index - 1U];
    uint32_t delta;
    if (map->section_index != section_index) continue;
    if (runtime_address < map->runtime_address) continue;
    delta = runtime_address - map->runtime_address;
    if (delta >= map->size) continue;
    if (map->source_offset > UINT32_MAX - delta) continue;
    if (map->source_offset + delta >= section_size) continue;
    *out_source_offset = map->source_offset + delta;
    return 1;
  }
  return 0;
}

static int runtime_address_space_section_has_range(const M68kRuntimeAddressSpace *space, size_t section_index) {
  size_t index;
  if (space == NULL) return 0;
  for (index = 0U; index < space->count; ++index) {
    if (space->ranges[index].section_index == section_index && space->ranges[index].size != 0U) return 1;
  }
  return 0;
}

static int runtime_address_space_source_to_runtime_near(const M68kRuntimeAddressSpace *space, size_t section_index,
    uint32_t source_offset, uint8_t has_current_runtime, uint32_t current_runtime, uint32_t *out_runtime_address) {
  size_t index;
  if (space == NULL || out_runtime_address == NULL) return 0;
  if (has_current_runtime) {
    for (index = space->count; index > 0U; --index) {
      const M68kRuntimeAddressRange *map = &space->ranges[index - 1U];
      uint32_t current_delta;
      uint32_t target_delta;
      if (map->section_index != section_index) continue;
      if (current_runtime < map->runtime_address) continue;
      current_delta = current_runtime - map->runtime_address;
      if (current_delta >= map->size) continue;
      if (source_offset < map->source_offset) continue;
      target_delta = source_offset - map->source_offset;
      if (target_delta >= map->size || map->runtime_address > UINT32_MAX - target_delta) continue;
      *out_runtime_address = map->runtime_address + target_delta;
      return 1;
    }
  }
  for (index = space->count; index > 0U; --index) {
    const M68kRuntimeAddressRange *map = &space->ranges[index - 1U];
    uint32_t target_delta;
    if (map->section_index != section_index || source_offset < map->source_offset) continue;
    target_delta = source_offset - map->source_offset;
    if (target_delta >= map->size || map->runtime_address > UINT32_MAX - target_delta) continue;
    *out_runtime_address = map->runtime_address + target_delta;
    return 1;
  }
  return 0;
}

static int resolve_runtime_or_section_target(const M68kRuntimeAddressSpace *space, size_t section_index,
    uint32_t runtime_address, uint32_t section_size, uint32_t *out_source_offset) {
  if (out_source_offset == NULL) return 0;
  if (runtime_address_space_translate(space, section_index, runtime_address, section_size, out_source_offset))
    return 1;
  if (runtime_address < section_size) {
    *out_source_offset = runtime_address;
    return 1;
  }
  return 0;
}

static int append_runtime_address_refs_for_accepted(const M68kDecodeIR *decode, uint8_t platform_kind,
    const M68kRuntimeAddressSpace *runtime_addresses, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactIR *facts) {
  size_t section_index;
  if (decode == NULL || runtime_addresses == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      facts == NULL) {
    return -1;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    if (accepted_start[section_index] == NULL || accepted_bytes[section_index] == NULL) return -1;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      size_t operand_index;
      if (!accepted_start[section_index][candidate->offset]) continue;
      for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
        uint32_t runtime_address = 0U;
        uint32_t target_offset = 0U;
        int ref_result;
        if (!candidate_operand_runtime_address_value(candidate, operand_index, platform_kind, &runtime_address))
          continue;
        if (!runtime_address_space_translate(runtime_addresses, section_index, runtime_address, section->size,
            &target_offset)) {
          if (candidate_operand_feeds_runtime_address_sink(candidate, operand_index, platform_kind)) {
            uint32_t sink_address = 0U;
            (void)m68k_asm_operand_absolute_value(candidate->operand_kinds[1], &candidate->operands[1], &sink_address);
            ref_result = append_external_runtime_address_ref_fact(facts, section_index, candidate->offset,
              operand_index, runtime_address, sink_address, (size_t)-1, 0U,
              M68K_FACT_CONFIDENCE_TOOL_INFERRED);
            if (ref_result < 0) return -1;
          }
          continue;
        }
        if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index],
            target_offset)) {
          continue;
        }
        if (!runtime_address_ref_needs_target_label(section, candidate, operand_index, platform_kind,
            runtime_addresses, accepted_start[section_index], target_offset, runtime_address)) {
          continue;
        }
        {
          uint32_t sink_address = 0U;
          if (candidate_operand_feeds_runtime_address_sink(candidate, operand_index, platform_kind)) {
            (void)m68k_asm_operand_absolute_value(candidate->operand_kinds[1], &candidate->operands[1], &sink_address);
          }
          ref_result = append_runtime_address_ref_fact_with_sink(facts, section_index, candidate->offset,
            operand_index, target_offset, runtime_address, sink_address, M68K_FACT_CONFIDENCE_TOOL_INFERRED);
        }
        if (ref_result < 0) return -1;
        if (ref_result == 0) continue;
        if (append_xref_fact(facts, section_index, candidate->offset, target_offset,
            M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
          return -1;
        }
        if (m68k_fact_ir_require_label(facts, section_index, target_offset,
              M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
          return -1;
        }
      }
    }
  }
  return 0;
}

static int facts_v2_absolute_ref_access_kind(uint8_t access_kind) {
  return access_kind == M68K_SIM_ACCESS_MEMORY_READ ||
    access_kind == M68K_SIM_ACCESS_MEMORY_WRITE ||
    access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS ||
    access_kind == M68K_SIM_ACCESS_BRANCH_TARGET;
}

static const M68kFact *facts_v2_operand_relocation_ref(const M68kFactsV2RelocationLookup *relocation_lookup,
    const M68kFactIR *facts, size_t section_index, const M68kDecodeCandidate *candidate,
    size_t operand_index) {
  M68kAsmOperandValue operands[M68K_DECODE_IR_MAX_OPERANDS];
  size_t index;
  size_t begin;
  size_t end;
  uint32_t cursor;
  if (relocation_lookup == NULL || facts == NULL || candidate == NULL ||
      operand_index >= candidate->operand_count || candidate->operand_count > M68K_DECODE_IR_MAX_OPERANDS) {
    return NULL;
  }
  for (index = 0U; index < candidate->operand_count; ++index) {
    operands[index] = candidate->operands[index];
    operands[index].kind = candidate->operand_kinds[index];
  }
  begin = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, operands, candidate->operand_count,
    candidate->size_suffix, operand_index, 0);
  end = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, operands, candidate->operand_count,
    candidate->size_suffix, operand_index, 1);
  if (begin > end || begin > UINT32_MAX - candidate->offset || end > UINT32_MAX - candidate->offset) return NULL;
  for (cursor = candidate->offset + (uint32_t)begin; cursor < candidate->offset + (uint32_t)end; ++cursor) {
    const M68kFact *relocation = relocation_lookup_ref_at(relocation_lookup, facts, section_index, cursor);
    if (relocation != NULL) return relocation;
  }
  return NULL;
}

static uint32_t facts_v2_instruction_access_width(const M68kInstructionIR *instruction, uint8_t access_kind) {
  if (instruction == NULL || access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS ||
      access_kind == M68K_SIM_ACCESS_BRANCH_TARGET) {
    return 0U;
  }
  if (instruction->size_suffix == 'b') return 1U;
  if (instruction->size_suffix == 'w') return 2U;
  if (instruction->size_suffix == 'l') return 4U;
  return 0U;
}

static int facts_v2_access_overlaps_accepted_code(const uint8_t *accepted_bytes, uint32_t section_size,
    uint32_t offset, uint32_t width, uint8_t access_kind) {
  uint32_t cursor;
  uint32_t end;
  if (accepted_bytes == NULL || offset >= section_size ||
      (access_kind != M68K_SIM_ACCESS_MEMORY_READ && access_kind != M68K_SIM_ACCESS_MEMORY_WRITE)) {
    return 0;
  }
  if (width == 0U) width = 1U;
  end = section_size - offset < width ? section_size : offset + width;
  for (cursor = offset; cursor < end; ++cursor) {
    if (accepted_bytes[cursor] != 0U) return 1;
  }
  return 0;
}

static void facts_v2_classify_absolute_memory_ref(uint8_t platform_kind,
    const M68kRuntimeAddressSpace *runtime_addresses, size_t section_index, uint32_t section_size,
    uint32_t address, M68kAbsoluteMemoryRefIR *ref) {
  const M68kCpuExceptionVectorInfo *vector = m68k_cpu_find_exception_vector_by_address(address);
  uint8_t platform_owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN;
  uint32_t platform_owner_offset = 0U;
  if (ref == NULL) return;
  ref->owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY;
  ref->owner_offset = address;
  if (platform_facts_v2_absolute_memory_owner(platform_kind, address, &platform_owner_kind,
      &platform_owner_offset)) {
    ref->owner_kind = platform_owner_kind;
    ref->owner_offset = platform_owner_offset;
    return;
  }
  if (vector != NULL) {
    ref->owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR;
    ref->owner_offset = 0U;
    return;
  }
  if (runtime_address_space_translate(runtime_addresses, section_index, address, section_size,
      &ref->owner_offset)) {
    ref->owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_RUNTIME_RANGE;
    return;
  }
  if (!runtime_address_space_section_has_range(runtime_addresses, section_index) && address < section_size) {
    ref->owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_SECTION_STORAGE;
    ref->owner_offset = address;
  }
}

static int append_absolute_memory_refs_for_accepted(const M68kDecodeIR *decode, const M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, uint8_t platform_kind,
    const M68kRuntimeAddressSpace *runtime_addresses, uint8_t **accepted_start,
    uint8_t **accepted_bytes, M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (decode == NULL || runtime_addresses == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      source_analysis == NULL || source_analysis->section_count < decode->section_count) {
    return -1;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    size_t candidate_index;
    if (accepted_start[section_index] == NULL || accepted_bytes[section_index] == NULL) return -1;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const M68kSimFormMetadata *metadata;
      size_t operand_index;
      if (!accepted_start[section_index][candidate->offset]) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      metadata = m68k_sim_metadata_for_instruction(&instruction);
      if (metadata == NULL) continue;
      for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U &&
           operand_index < instruction.operand_count; ++operand_index) {
        uint32_t address = 0U;
        uint8_t access_kind = metadata->operand_access_kinds[operand_index];
        int has_absolute_operand;
        int has_address_immediate;
        const M68kFact *relocation;
        size_t owner_section_index = section_index;
        M68kAbsoluteMemoryRefIR ref;
        has_absolute_operand = m68k_asm_operand_absolute_value(candidate->operand_kinds[operand_index],
          &candidate->operands[operand_index], &address);
        has_address_immediate = !has_absolute_operand &&
          candidate_immediate_operand_is_address_domain(candidate, operand_index) &&
          operand_immediate_value(candidate->operand_kinds[operand_index], &candidate->operands[operand_index],
            &address);
        if ((!has_absolute_operand || !facts_v2_absolute_ref_access_kind(access_kind)) &&
            !has_address_immediate) {
          continue;
        }
        memset(&ref, 0, sizeof(ref));
        ref.offset = candidate->offset;
        ref.operand_index = (uint32_t)operand_index;
        ref.source_size = candidate->byte_count;
        ref.access_width = has_absolute_operand && facts_v2_absolute_ref_access_kind(access_kind)
          ? facts_v2_instruction_access_width(&instruction, access_kind)
          : 0U;
        ref.address = address;
        ref.access_kind = access_kind;
        ref.confidence = (uint8_t)M68K_FACT_CONFIDENCE_TOOL_INFERRED;
        relocation = facts_v2_operand_relocation_ref(relocation_lookup, facts, section_index, candidate,
          operand_index);
        if (relocation != NULL && relocation->target_section_index < decode->section_count) {
          owner_section_index = relocation->target_section_index;
          ref.owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_SECTION_STORAGE;
          ref.owner_offset = relocation->target_offset;
        } else {
          facts_v2_classify_absolute_memory_ref(platform_kind, runtime_addresses, section_index, section->size,
            address, &ref);
        }
        ref.conflicted = owner_section_index < decode->section_count ?
          (uint8_t)facts_v2_access_overlaps_accepted_code(accepted_bytes[owner_section_index],
            decode->sections[owner_section_index].size, ref.owner_offset, ref.access_width, access_kind) : 0U;
        ref.conflict_state = ref.conflicted ? M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP :
          M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
        if (m68k_ir_section_analysis_append_absolute_memory_ref(section_analysis, &ref) != 0) return -1;
      }
    }
  }
  return 0;
}

static int append_platform_storage_layouts_from_object(const M68kObject *object,
    M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  if (object == NULL || source_analysis == NULL) return -1;
  for (index = 0U; index < object->platform_storage_layout_count; ++index)
    if (m68k_ir_source_analysis_append_platform_storage_layout(source_analysis,
        &object->platform_storage_layouts[index]) != 0)
      return -1;
  return 0;
}

static int candidate_lea_absolute_address(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
    uint32_t *out_address) {
  uint8_t dest_reg = 0U;
  uint32_t address = 0U;
  M68kAsmOperandValue dest_operand;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA ||
      candidate->operand_count != 2U)
    return 0;
  if (!m68k_asm_operand_absolute_value(candidate->operand_kinds[0], &candidate->operands[0], &address)) return 0;
  dest_operand = candidate->operands[1];
  dest_operand.kind = candidate->operand_kinds[1];
  if (!operand_is_address_register_direct(&dest_operand, &dest_reg)) return 0;
  if (out_reg != NULL) *out_reg = dest_reg;
  if (out_address != NULL) *out_address = address;
  return 1;
}

static int candidate_lea_relocated_address(const M68kFactsV2RelocationLookup *relocation_lookup,
    const M68kFactIR *facts, size_t section_index, const M68kDecodeCandidate *candidate, uint8_t *out_reg,
    size_t *out_target_section, uint32_t *out_target_offset) {
  uint8_t dest_reg = 0U;
  uint32_t ignored_address = 0U;
  uint32_t cursor;
  uint32_t end;
  M68kAsmOperandValue dest_operand;
  if (out_reg != NULL) *out_reg = 0U;
  if (out_target_section != NULL) *out_target_section = 0U;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (relocation_lookup == NULL || facts == NULL || candidate == NULL || out_reg == NULL ||
      out_target_section == NULL || out_target_offset == NULL ||
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA || candidate->operand_count != 2U ||
      !m68k_asm_operand_absolute_value(candidate->operand_kinds[0], &candidate->operands[0], &ignored_address) ||
      candidate->byte_count > UINT32_MAX - candidate->offset) {
    return 0;
  }
  dest_operand = candidate->operands[1];
  dest_operand.kind = candidate->operand_kinds[1];
  if (!operand_is_address_register_direct(&dest_operand, &dest_reg)) return 0;
  end = candidate->offset + candidate->byte_count;
  for (cursor = candidate->offset + 2U; cursor < end; ++cursor) {
    const M68kFact *relocation = relocation_lookup_ref_at(relocation_lookup, facts, section_index, cursor);
    if (relocation == NULL || relocation->size != 4U) continue;
    *out_reg = dest_reg;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    return 1;
  }
  return 0;
}

static int candidate_moves_relocated_address_to_address_register(
    const M68kFactsV2RelocationLookup *relocation_lookup, const M68kFactIR *facts, size_t section_index,
    const M68kDecodeCandidate *candidate, uint8_t *out_reg, size_t *out_target_section,
    uint32_t *out_target_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t dest_reg = 0U;
  uint32_t ignored_value = 0U;
  uint32_t cursor;
  uint32_t end;
  M68kAsmOperandValue dest_operand;
  if (out_reg != NULL) *out_reg = 0U;
  if (out_target_section != NULL) *out_target_section = 0U;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (relocation_lookup == NULL || facts == NULL || candidate == NULL || out_reg == NULL ||
      out_target_section == NULL || out_target_offset == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      candidate->byte_count > UINT32_MAX - candidate->offset) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_MOVE ||
      metadata->source_operand_index >= candidate->operand_count ||
      metadata->dest_operand_index >= candidate->operand_count ||
      !operand_immediate_value(candidate->operand_kinds[metadata->source_operand_index],
        &candidate->operands[metadata->source_operand_index], &ignored_value)) {
    return 0;
  }
  dest_operand = candidate->operands[metadata->dest_operand_index];
  dest_operand.kind = candidate->operand_kinds[metadata->dest_operand_index];
  if (!operand_is_address_register_direct(&dest_operand, &dest_reg) || dest_reg == 7U) return 0;
  end = candidate->offset + candidate->byte_count;
  for (cursor = candidate->offset + 2U; cursor < end; ++cursor) {
    const M68kFact *relocation = relocation_lookup_ref_at(relocation_lookup, facts, section_index, cursor);
    if (relocation == NULL || relocation->size != 4U) continue;
    *out_reg = dest_reg;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    return 1;
  }
  return 0;
}

static int candidate_lea_pc_relative_data_target(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t section_size, uint8_t *out_reg, uint32_t *out_offset) {
  size_t target_index;
  uint8_t dest_reg = 0U;
  M68kInstructionIR instruction;
  M68kAsmOperandValue layout_operands[M68K_DECODE_IR_MAX_OPERANDS];
  uint8_t shape;
  size_t relative_base;
  uint32_t pc_base;
  uint32_t target_offset;
  uint32_t target_limit;
  M68kAsmOperandValue dest_operand;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA ||
      candidate->operand_count != 2U)
    return 0;
  dest_operand = candidate->operands[1];
  dest_operand.kind = candidate->operand_kinds[1];
  if (!operand_is_address_register_direct(&dest_operand, &dest_reg)) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_DATA || !target->has_operand || target->operand_index != 0U ||
        !target->has_section || target->section_index != section_index)
      continue;
    if (out_reg != NULL) *out_reg = dest_reg;
    if (out_offset != NULL) *out_offset = target->offset;
    return 1;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) == 0 && instruction.operand_count >= 1U) {
    size_t operand_index;
    for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
      layout_operands[operand_index] = candidate->operands[operand_index];
      layout_operands[operand_index].kind = candidate->operand_kinds[operand_index];
    }
    shape = m68k_instruction_operand_decoded_ea_shape(&instruction.operands[0]);
    relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, layout_operands,
      candidate->operand_count, candidate->size_suffix, 0U, 0);
    if (relative_base <= UINT32_MAX - candidate->offset) {
      pc_base = candidate->offset + (uint32_t)relative_base;
      target_limit = section_size < UINT32_MAX ? section_size + 1U : section_size;
      if (m68k_instruction_decoded_ea_target_kind(&instruction.operands[0], shape, 1) == 2U &&
          m68k_instruction_decoded_ea_target(&instruction.operands[0], shape, pc_base, target_limit, 1,
            &target_offset)) {
        if (out_reg != NULL) *out_reg = dest_reg;
        if (out_offset != NULL) *out_offset = target_offset;
        return 1;
      }
    }
  }
  return 0;
}

static int candidate_lea_platform_section_anchor(const M68kDecodeCandidate *candidate, uint8_t platform_kind,
    uint8_t *out_reg, uint32_t *out_base_offset, int32_t *out_addend) {
  M68kInstructionIR instruction;
  M68kAsmOperandValue asm_operands[M68K_DECODE_IR_MAX_OPERANDS];
  M68kAsmOperandValue dest_operand;
  uint8_t dest_reg = 0U;
  size_t operand_index;
  size_t relative_base;
  int64_t target;
  uint32_t base_offset = 0U;
  int32_t addend = 0;
  if (out_reg != NULL) *out_reg = 0U;
  if (out_base_offset != NULL) *out_base_offset = 0U;
  if (out_addend != NULL) *out_addend = 0;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA ||
      candidate->operand_count != 2U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      instruction.operand_count < 1U) {
    return 0;
  }
  dest_operand = candidate->operands[1];
  dest_operand.kind = candidate->operand_kinds[1];
  if (!operand_is_address_register_direct(&dest_operand, &dest_reg)) return 0;
  if (candidate->operand_kinds[0] != M68K_ASM_OPERAND_EA ||
      candidate->operands[0].ea_mode != 7U || candidate->operands[0].ea_reg != 2U) {
    return 0;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
    asm_operands[operand_index] = candidate->operands[operand_index];
    asm_operands[operand_index].kind = candidate->operand_kinds[operand_index];
  }
  relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, asm_operands,
    candidate->operand_count, candidate->size_suffix, 0U, 0);
  target = (int64_t)candidate->offset + (int64_t)relative_base +
    (int64_t)(int32_t)m68k_sign_extend32(candidate->operands[0].value, 16U);
  if (!platform_facts_v2_pc_relative_section_anchor_for_target(platform_kind, target, &base_offset, &addend, NULL))
    return 0;
  if (out_reg != NULL) *out_reg = dest_reg;
  if (out_base_offset != NULL) *out_base_offset = base_offset;
  if (out_addend != NULL) *out_addend = addend;
  return 1;
}

static int candidate_is_long_immediate_to_data_register(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
    uint32_t *out_value) {
  uint8_t dest_reg = 0U;
  uint32_t value = 0U;
  if (candidate == NULL || candidate->operand_count != 2U) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE && candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEQ)
    return 0;
  if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && candidate->size_suffix != 'l') return 0;
  if (!operand_immediate_value(candidate->operand_kinds[0], &candidate->operands[0], &value)) return 0;
  if (!operand_is_data_register_direct(&candidate->operands[1], &dest_reg)) return 0;
  if (out_reg != NULL) *out_reg = dest_reg;
  if (out_value != NULL) *out_value = value;
  return 1;
}

static int candidate_is_long_data_register_postincrement_store(const M68kDecodeCandidate *candidate,
    uint8_t *out_source_reg, uint8_t *out_dest_reg) {
  uint8_t source_reg = 0U;
  uint8_t dest_reg = 0U;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
      candidate->size_suffix != 'l' || candidate->operand_count != 2U)
    return 0;
  if (!operand_is_data_register_direct(&candidate->operands[0], &source_reg)) return 0;
  if (!operand_is_postincrement_address_register(candidate->operand_kinds[1], &candidate->operands[1],
      &dest_reg))
    return 0;
  if (out_source_reg != NULL) *out_source_reg = source_reg;
  if (out_dest_reg != NULL) *out_dest_reg = dest_reg;
  return 1;
}

static int candidate_stores_immediate_to_interrupt_vector(const M68kDecodeCandidate *candidate,
    uint8_t platform_kind, uint32_t *out_target_address) {
  uint32_t vector_address = 0U;
  uint32_t target_address = 0U;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
      candidate->size_suffix != 'l' || candidate->operand_count != 2U || out_target_address == NULL)
    return 0;
  if (!operand_immediate_value(candidate->operand_kinds[0], &candidate->operands[0], &target_address)) return 0;
  if (!m68k_asm_operand_absolute_value(candidate->operand_kinds[1], &candidate->operands[1], &vector_address)) return 0;
  if (!platform_facts_v2_is_callback_vector_slot(platform_kind, vector_address)) return 0;
  *out_target_address = target_address;
  return 1;
}

static int trace_value_is_same_section_control_address(const M68kFactsV2TraceValue *value, size_t section_index) {
  if (value == NULL) return 0;
  if (value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) return value->section_index == section_index;
  return value->kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS || value->kind == M68K_FACTS_V2_TRACE_CONSTANT;
}

static int candidate_stores_trace_to_callback_vector(size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *store_candidate, uint8_t platform_kind, const M68kFactsV2TraceState *trace_state,
    M68kFactsV2TraceValue *out_target_value) {
  M68kFactsV2TraceValue source_value;
  uint8_t data_reg = 0U;
  uint8_t address_reg = 0U;
  if (out_target_value != NULL) trace_value_set_unknown(out_target_value);
  if (store_candidate == NULL || trace_state == NULL || out_target_value == NULL)
    return 0;
  if (store_candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && store_candidate->size_suffix == 'l' &&
      store_candidate->operand_count == 2U) {
    uint32_t vector_address = 0U;
    if (m68k_asm_operand_absolute_value(store_candidate->operand_kinds[1], &store_candidate->operands[1],
        &vector_address)) {
      int is_vector = platform_facts_v2_is_callback_vector_slot(platform_kind, vector_address);
      int has_source = trace_value_from_candidate_source(section_index, section, store_candidate, 0U, trace_state,
        &source_value);
      if (is_vector && has_source && trace_value_is_same_section_control_address(&source_value, section_index)) {
        *out_target_value = source_value;
        return 1;
      }
    }
  }
  if (!candidate_is_long_data_register_postincrement_store(store_candidate, &data_reg, &address_reg)) return 0;
  if (!trace_value_is_same_section_control_address(&trace_state->d[data_reg], section_index) ||
      trace_state->a[address_reg].kind != M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS) {
    return 0;
  }
  if (!platform_facts_v2_is_callback_vector_slot(platform_kind, trace_state->a[address_reg].value)) return 0;
  *out_target_value = trace_state->d[data_reg];
  return 1;
}

static int enqueue_same_section_control_resolved_target_from_offset(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    uint32_t source_offset, uint32_t target_offset, uint8_t target_has_runtime_address,
    uint32_t runtime_address, uint8_t confidence, uint32_t code_start_reason,
    const M68kFactsV2TraceState *trace_state) {
  const M68kDecodeSectionIR *section;
  const M68kDecodeCandidate *target_candidate = NULL;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || section_index >= decode->section_count)
    return 0;
  section = &decode->sections[section_index];
  if (target_offset >= section->size) return 0;
  if ((target_offset & 1U) != 0U) return 0;
  if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index],
      target_offset)) {
    if (append_violation_fact(facts, section_index, source_offset, target_offset) != 0) return -1;
    return 0;
  }
  if (m68k_decode_ir_ensure_candidate_at(decode, section_index, target_offset, max_cpu, &target_candidate,
      m68k_diag_sink(NULL)) != 0)
    return -1;
  if (target_candidate == NULL) return 0;
  if (append_xref_fact(facts, section_index, source_offset, target_offset, confidence) != 0)
    return -1;
  if (m68k_fact_ir_require_label(facts, section_index, target_offset, confidence) != 0)
    return -1;
  if (accepted_start[section_index][target_offset] && trace_state == NULL && !target_has_runtime_address) return 0;
  return enqueue_code_start_runtime(facts, queue, profile, section_index, target_offset,
    confidence, code_start_reason != 0U ? code_start_reason : M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
    section_index, source_offset, target_has_runtime_address, runtime_address, trace_state);
}

static int enqueue_same_section_control_resolved_target(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeCandidate *candidate, uint32_t target_offset, uint8_t target_has_runtime_address,
    uint32_t runtime_address, uint8_t confidence, const M68kFactsV2TraceState *trace_state) {
  if (candidate == NULL) return 0;
  return enqueue_same_section_control_resolved_target_from_offset(decode, facts, queue, accepted_start,
    accepted_bytes, profile, max_cpu, section_index, candidate->offset, target_offset,
    target_has_runtime_address, runtime_address, confidence, M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
    trace_state);
}

static int enqueue_same_section_control_target_from_offset(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    uint32_t source_offset, uint32_t target_address, uint8_t confidence,
    const M68kRuntimeAddressSpace *runtime_addresses, const M68kFactsV2TraceState *trace_state) {
  const M68kDecodeSectionIR *section;
  uint32_t target_offset = 0U;
  uint8_t target_has_runtime_address = 0U;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || section_index >= decode->section_count)
    return 0;
  section = &decode->sections[section_index];
  if (runtime_address_space_translate(runtime_addresses, section_index, target_address, section->size,
      &target_offset)) {
    target_has_runtime_address = 1U;
  } else if (target_address < section->size) {
    target_offset = target_address;
  } else {
    return 0;
  }
  return enqueue_same_section_control_resolved_target_from_offset(decode, facts, queue, accepted_start, accepted_bytes,
    profile, max_cpu, section_index, source_offset, target_offset, target_has_runtime_address, target_address,
    confidence, M68K_FACT_CODE_START_REASON_CONTROL_TARGET, trace_state);
}

static int enqueue_same_section_control_target(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeCandidate *candidate, uint32_t target_address, uint8_t confidence,
    const M68kRuntimeAddressSpace *runtime_addresses, const M68kFactsV2TraceState *trace_state) {
  if (candidate == NULL) return 0;
  return enqueue_same_section_control_target_from_offset(decode, facts, queue, accepted_start, accepted_bytes,
    profile, max_cpu, section_index, candidate->offset, target_address, confidence, runtime_addresses,
    trace_state);
}

static int enqueue_cross_section_control_resolved_target_from_offset(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t source_section_index, uint32_t source_offset,
    size_t target_section_index, uint32_t target_offset, uint8_t confidence, uint32_t code_start_reason) {
  const M68kDecodeSectionIR *target_section;
  const M68kDecodeCandidate *target_candidate = NULL;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || source_section_index >= decode->section_count ||
      target_section_index >= decode->section_count || accepted_start[target_section_index] == NULL ||
      accepted_bytes[target_section_index] == NULL) {
    return 0;
  }
  target_section = &decode->sections[target_section_index];
  if (target_section->kind != M68K_SECTION_CODE || target_offset >= target_section->size ||
      (target_offset & 1U) != 0U) {
    return 0;
  }
  if (accepted_offset_is_interior(target_section, accepted_start[target_section_index],
      accepted_bytes[target_section_index], target_offset)) {
    if (append_violation_fact_with_reason(facts, target_section_index, target_offset, target_offset,
        M68K_FACT_CODE_START_REASON_CONTROL_TARGET, source_section_index, source_offset) != 0) {
      return -1;
    }
    return 0;
  }
  if (m68k_decode_ir_ensure_candidate_at(decode, target_section_index, target_offset, max_cpu,
      &target_candidate, m68k_diag_sink(NULL)) != 0) {
    return -1;
  }
  if (target_candidate == NULL) return 0;
  if (append_cross_section_xref_fact(facts, source_section_index, source_offset, target_section_index,
      target_offset, confidence) != 0) {
    return -1;
  }
  if (m68k_fact_ir_require_label(facts, target_section_index, target_offset, confidence) != 0) return -1;
  if (accepted_start[target_section_index][target_offset]) return 0;
  return enqueue_code_start(facts, queue, profile, target_section_index, target_offset, confidence,
    code_start_reason != 0U ? code_start_reason : M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
    source_section_index, source_offset);
}

static int enqueue_same_section_control_trace_target(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceValue *target_value, uint8_t confidence,
    const M68kRuntimeAddressSpace *runtime_addresses, const M68kFactsV2TraceState *trace_state) {
  const M68kDecodeSectionIR *section;
  if (decode == NULL || target_value == NULL || section_index >= decode->section_count) return 0;
  section = &decode->sections[section_index];
  if (target_value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
    if (target_value->section_index != section_index) {
      if (candidate == NULL) return 0;
      return enqueue_cross_section_control_resolved_target_from_offset(decode, facts, queue, accepted_start,
        accepted_bytes, profile, max_cpu, section_index, candidate->offset, target_value->section_index,
        target_value->value, confidence, target_value->code_start_reason);
    }
    if (target_value->value >= section->size) return 0;
    return enqueue_same_section_control_resolved_target(decode, facts, queue, accepted_start, accepted_bytes,
      profile, max_cpu, section_index, candidate, target_value->value, 0U, 0U, confidence, trace_state);
  }
  if (target_value->kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS ||
      target_value->kind == M68K_FACTS_V2_TRACE_CONSTANT) {
    return enqueue_same_section_control_target(decode, facts, queue, accepted_start, accepted_bytes,
      profile, max_cpu, section_index, candidate, target_value->value, confidence, runtime_addresses, trace_state);
  }
  return 0;
}

static int append_trace_origin_runtime_control_ref(M68kDecodeIR *decode, M68kFactIR *facts,
    uint8_t **accepted_start, uint8_t **accepted_bytes, uint8_t max_cpu, size_t section_index,
    const M68kFactsV2TraceValue *target_value, const M68kRuntimeAddressSpace *runtime_addresses,
    uint8_t confidence) {
  const M68kDecodeSectionIR *section;
  const M68kDecodeCandidate *target_candidate = NULL;
  uint32_t target_offset = 0U;
  uint32_t runtime_address = 0U;
  int ref_result;
  if (decode == NULL || facts == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      target_value == NULL || !target_value->has_origin || section_index >= decode->section_count ||
      target_value->origin_section_index != section_index) {
    return 0;
  }
  section = &decode->sections[section_index];
  if (target_value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
    if (target_value->section_index != section_index) return 0;
    target_offset = target_value->value;
    runtime_address = target_offset;
    (void)runtime_address_space_source_to_runtime_near(runtime_addresses, section_index, target_offset, 0U, 0U,
      &runtime_address);
  } else if (target_value->kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS ||
      target_value->kind == M68K_FACTS_V2_TRACE_CONSTANT) {
    runtime_address = target_value->value;
    if (!runtime_address_space_translate(runtime_addresses, section_index, runtime_address, section->size,
        &target_offset)) {
      if (runtime_address >= section->size) return 0;
      target_offset = runtime_address;
    }
  } else {
    return 0;
  }
  if (target_offset >= section->size || (target_offset & 1U) != 0U ||
      accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index],
        target_offset)) {
    return 0;
  }
  if (m68k_decode_ir_ensure_candidate_at(decode, section_index, target_offset, max_cpu, &target_candidate,
      m68k_diag_sink(NULL)) != 0) {
    return -1;
  }
  if (target_candidate == NULL) return 0;
  ref_result = append_runtime_address_ref_fact(facts, section_index, target_value->origin_offset,
    target_value->origin_operand_index, target_offset, runtime_address, confidence);
  if (ref_result < 0) return -1;
  if (append_xref_fact(facts, section_index, target_value->origin_offset, target_offset, confidence) != 0)
    return -1;
  return m68k_fact_ir_require_label(facts, section_index, target_offset, confidence);
}

static int enqueue_interrupt_vector_store_target(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, uint8_t platform_kind, size_t section_index,
    const M68kDecodeCandidate *candidate, const M68kRuntimeAddressSpace *runtime_addresses,
    const M68kFactsV2TraceState *trace_state) {
  const M68kDecodeSectionIR *section;
  uint32_t target_address = 0U;
  M68kFactsV2TraceValue target_value;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || candidate == NULL || section_index >= decode->section_count)
    return 0;
  section = &decode->sections[section_index];
  if (candidate_stores_immediate_to_interrupt_vector(candidate, platform_kind, &target_address)) {
    return enqueue_same_section_control_target(decode, facts, queue, accepted_start, accepted_bytes,
      profile, max_cpu, section_index, candidate, target_address, M68K_FACT_CONFIDENCE_REQUIRED,
      runtime_addresses, trace_state);
  }
  if (candidate_stores_trace_to_callback_vector(section_index, section, candidate, platform_kind, trace_state,
      &target_value)) {
    if (append_trace_origin_runtime_control_ref(decode, facts, accepted_start, accepted_bytes, max_cpu,
        section_index, &target_value, runtime_addresses, M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0)
      return -1;
    return enqueue_same_section_control_trace_target(decode, facts, queue, accepted_start, accepted_bytes,
      profile, max_cpu, section_index, candidate, &target_value, M68K_FACT_CONFIDENCE_TOOL_INFERRED,
      runtime_addresses, trace_state);
  }
  return 0;
}

static int facts_runtime_ref_source_inside_discovered_copy_range(const M68kFactIR *facts, const M68kFact *ref,
    const M68kRuntimeAddressRange *target_range) {
  size_t fact_index;
  if (facts == NULL || ref == NULL) return 1;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *range = &facts->facts[fact_index];
    uint64_t range_end;
    if (range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
        range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
        range->section_index != ref->section_index || range->size == 0U) {
      continue;
    }
    if (target_range != NULL && range->section_index == target_range->section_index &&
        range->offset == target_range->source_offset && range->runtime_address == target_range->runtime_address) {
      continue;
    }
    range_end = (uint64_t)range->offset + range->size;
    if (ref->offset >= range->offset && (uint64_t)ref->offset < range_end) return 1;
  }
  return 0;
}

static int facts_runtime_range_has_internal_control_entry(const M68kFactIR *facts,
    const M68kRuntimeAddressRange *range) {
  size_t fact_index;
  uint64_t range_start, range_end;
  if (facts == NULL || range == NULL || range->size == 0U) return 0;
  range_start = range->runtime_address;
  range_end = range_start + range->size;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    if (fact->kind != M68K_FACT_CODE_START ||
        fact->reason != M68K_FACT_CODE_START_REASON_CONTROL_TARGET ||
        fact->section_index != range->section_index || !fact->has_runtime_address ||
        fact->runtime_address < range_start || (uint64_t)fact->runtime_address >= range_end) {
      continue;
    }
    if (fact->offset != range->source_offset || fact->runtime_address != range->runtime_address) return 1;
  }
  return 0;
}

static int facts_runtime_ref_targets_range_start(const M68kDecodeIR *decode, const M68kFactIR *facts,
    const M68kRuntimeAddressRange *range, size_t *out_source_section_index, uint32_t *out_source_offset) {
  size_t fact_index;
  if (decode == NULL || facts == NULL || range == NULL) return 0;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    const M68kDecodeSectionIR *source_section;
    const M68kDecodeCandidate *source_candidate;
    M68kInstructionIR source_instruction;
    const M68kSimFormMetadata *source_metadata;
    size_t operand_index;
    int is_control_target = 0;
    if (fact->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
        fact->confidence < M68K_FACT_CONFIDENCE_TOOL_INFERRED ||
        fact->target_section_index != range->section_index ||
        fact->target_offset != range->source_offset ||
        !fact->has_runtime_address ||
        fact->runtime_address != range->runtime_address) {
      continue;
    }
    if (fact->section_index >= decode->section_count || fact->reason == M68K_FACT_RUNTIME_ADDRESS_REF_NO_OPERAND)
      continue;
    source_section = &decode->sections[fact->section_index];
    source_candidate = m68k_decode_ir_find_candidate_at_offset(source_section, fact->offset);
    operand_index = (size_t)fact->reason;
    if (source_candidate == NULL || operand_index >= source_candidate->operand_count) {
      continue;
    }
    if (m68k_decode_candidate_to_instruction(source_candidate, &source_instruction) == 0 &&
        operand_index < source_instruction.operand_count) {
      source_metadata = m68k_sim_metadata_for_instruction(&source_instruction);
      is_control_target = source_metadata != NULL &&
        source_metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_BRANCH_TARGET &&
        source_metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_CONTROL_TARGET;
    }
    if (!is_control_target &&
        (facts_runtime_ref_source_inside_discovered_copy_range(facts, fact, range) ||
         facts_runtime_range_has_internal_control_entry(facts, range))) {
      continue;
    }
    if (out_source_section_index != NULL) *out_source_section_index = fact->section_index;
    if (out_source_offset != NULL) *out_source_offset = fact->offset;
    return 1;
  }
  return 0;
}

static int seed_runtime_ref_target_discovered_copy_entries(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, const M68kRuntimeAddressSpace *runtime_addresses,
    uint8_t **accepted_start, uint8_t **accepted_bytes, M68kFactsV2Profile *profile,
    uint8_t max_cpu, uint32_t *out_seed_count) {
  size_t range_index;
  uint32_t seed_count = 0U;
  if (out_seed_count != NULL) *out_seed_count = 0U;
  if (decode == NULL || facts == NULL || queue == NULL || runtime_addresses == NULL ||
      accepted_start == NULL || accepted_bytes == NULL || profile == NULL) {
    return -1;
  }
  for (range_index = 0U; range_index < runtime_addresses->count; ++range_index) {
    const M68kRuntimeAddressRange *range = &runtime_addresses->ranges[range_index];
    const M68kDecodeSectionIR *section;
    const M68kDecodeCandidate *candidate = NULL;
    M68kFactsV2TraceState trace_state;
    size_t source_section_index = range->section_index;
    uint32_t source_offset = range->source_offset;
    if (range->kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
        range->confidence < M68K_FACT_CONFIDENCE_TOOL_INFERRED ||
        range->section_index >= decode->section_count || (range->source_offset & 1U) != 0U) {
      continue;
    }
    section = &decode->sections[range->section_index];
    if (range->source_offset >= section->size ||
        accepted_start[range->section_index][range->source_offset] ||
        accepted_offset_is_interior(section, accepted_start[range->section_index],
          accepted_bytes[range->section_index], range->source_offset) ||
        !facts_runtime_ref_targets_range_start(decode, facts, range, &source_section_index, &source_offset)) {
      continue;
    }
    if (m68k_decode_ir_ensure_candidate_at(decode, range->section_index, range->source_offset, max_cpu,
        &candidate, m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (candidate == NULL) continue;
    trace_state_init_unknown(&trace_state);
    if (m68k_fact_ir_require_label(facts, range->section_index, range->source_offset,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
      return -1;
    }
    if (enqueue_code_start_runtime(facts, queue, profile, range->section_index, range->source_offset,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_RUNTIME_VIEW_ENTRY,
        source_section_index, source_offset, 1U, range->runtime_address, &trace_state) != 0) {
      return -1;
    }
    ++seed_count;
  }
  if (out_seed_count != NULL) *out_seed_count = seed_count;
  return 0;
}

static int enqueue_runtime_alias_absolute_control_target(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeCandidate *candidate, const M68kRuntimeAddressSpace *runtime_addresses,
    const M68kFactsV2TraceState *trace_state) {
  const M68kDecodeSectionIR *section;
  uint32_t runtime_address = 0U;
  uint32_t source_offset = 0U;
  if (decode == NULL || section_index >= decode->section_count || runtime_addresses == NULL) return 0;
  section = &decode->sections[section_index];
  if (!candidate_absolute_control_address(candidate, &runtime_address)) return 0;
  if (!runtime_address_space_translate(runtime_addresses, section_index, runtime_address, section->size,
      &source_offset))
    return 0;
  (void)source_offset;
  return enqueue_same_section_control_target(decode, facts, queue, accepted_start, accepted_bytes,
    profile, max_cpu, section_index, candidate, runtime_address, M68K_FACT_CONFIDENCE_TOOL_INFERRED,
    runtime_addresses, trace_state);
}

static int trace_value_as_control_target_address(const M68kFactsV2TraceValue *value,
    size_t section_index, uint32_t *out_address) {
  if (out_address != NULL) *out_address = 0U;
  if (value == NULL || out_address == NULL) return 0;
  if (value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
    if (value->section_index != section_index) return 0;
    *out_address = value->value;
    return 1;
  }
  if (value->kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS ||
      value->kind == M68K_FACTS_V2_TRACE_CONSTANT) {
    *out_address = value->value;
    return 1;
  }
  return 0;
}

static int trace_state_control_target_operand_address(const M68kDecodeCandidate *candidate,
    size_t operand_index, size_t section_index, const M68kFactsV2TraceState *trace_state,
    uint32_t *out_address) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  const M68kAsmOperandValue *operand;
  M68kFactsV2TraceValue value;
  uint8_t reg = 0U;
  if (out_address != NULL) *out_address = 0U;
  if (candidate == NULL || trace_state == NULL || out_address == NULL ||
      operand_index >= candidate->operand_count ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || operand_index >= instruction.operand_count ||
      metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
      metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) {
    return 0;
  }
  operand = &candidate->operands[operand_index];
  if (candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_EA && operand->ea_reg < 8U &&
      (operand->ea_mode == 2U || operand->ea_mode == 5U) &&
      trace_state_operand_runtime_address(trace_state, candidate, operand_index, out_address)) {
    return 1;
  }
  if (!operand_is_control_address_register_indirect(candidate->operand_kinds[operand_index], operand, &reg)) return 0;
  if (operand->kind == M68K_ASM_OPERAND_EA &&
      (metadata->operand_ea_uses_index[operand_index] || metadata->operand_ea_uses_displacement[operand_index])) {
    return 0;
  }
  value = trace_state->a[reg];
  return trace_value_as_control_target_address(&value, section_index, out_address);
}

static int indexed_control_operand_index_reg(const M68kDecodeCandidate *candidate, size_t operand_index,
    uint8_t want_address_index, uint8_t *out_reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  const M68kAsmOperandValue *operand;
  int decoded_index_form;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || out_reg == NULL || operand_index >= candidate->operand_count ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || operand_index >= instruction.operand_count ||
      metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
      metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) {
    return 0;
  }
  operand = &candidate->operands[operand_index];
  decoded_index_form = candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_EA &&
    facts_v2_instruction_operand_is_indexed_or_pc_indexed(&instruction, operand_index);
  if (!metadata->operand_ea_uses_index[operand_index] && !decoded_index_form) return 0;
  if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA ||
      operand->index_is_address != want_address_index || operand->index_reg >= 8U) {
    return 0;
  }
  *out_reg = operand->index_reg;
  return 1;
}

static int indexed_control_operand_data_index_reg(const M68kDecodeCandidate *candidate, size_t operand_index,
    uint8_t *out_reg) {
  return indexed_control_operand_index_reg(candidate, operand_index, 0U, out_reg);
}

static int indexed_control_operand_address_index_reg(const M68kDecodeCandidate *candidate, size_t operand_index,
    uint8_t *out_reg) {
  return indexed_control_operand_index_reg(candidate, operand_index, 1U, out_reg);
}

static int indexed_control_operand_base_ref(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, size_t operand_index, const M68kRuntimeAddressSpace *runtime_addresses,
    const M68kFactsV2TraceState *trace_state, uint32_t *out_offset, uint32_t *out_address) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  const M68kAsmOperandValue *operand;
  uint32_t base_offset = 0U;
  uint32_t base_address = 0U;
  int32_t displacement = 0;
  int64_t target_address64;
  if (out_offset != NULL) *out_offset = 0U;
  if (out_address != NULL) *out_address = 0U;
  if (section == NULL || candidate == NULL || runtime_addresses == NULL || trace_state == NULL ||
      out_offset == NULL || out_address == NULL || operand_index >= candidate->operand_count ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  if (candidate_operand_data_target_offset(candidate, operand_index, section->section_index, &base_offset)) {
    base_address = base_offset;
    (void)runtime_address_space_source_to_runtime_near(runtime_addresses, section->section_index,
      base_offset, 0U, 0U, &base_address);
    *out_offset = base_offset;
    *out_address = base_address;
    return 1;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || operand_index >= instruction.operand_count ||
      metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
      metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET ||
      !facts_v2_instruction_operand_is_indexed_or_pc_indexed(&instruction, operand_index)) {
    return 0;
  }
  operand = &candidate->operands[operand_index];
  if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA || operand->ea_reg >= 8U)
    return 0;
  if (!trace_value_to_table_storage_offset(&trace_state->a[operand->ea_reg], runtime_addresses,
      section->section_index, section->size, &base_offset) ||
      !trace_value_to_table_base_address(&trace_state->a[operand->ea_reg], section->section_index,
        section->size, &base_address)) {
    return 0;
  }
  displacement = (int32_t)operand->value;
  target_address64 = (int64_t)(uint64_t)base_address + (int64_t)displacement;
  if (target_address64 < 0 || target_address64 > (int64_t)(uint64_t)UINT32_MAX) return 0;
  if (displacement < 0 && (uint32_t)(-displacement) > base_offset) return 0;
  if (displacement > 0 && base_offset > UINT32_MAX - (uint32_t)displacement) return 0;
  base_offset = (uint32_t)((int64_t)(uint64_t)base_offset + (int64_t)displacement);
  if (base_offset >= section->size) return 0;
  *out_offset = base_offset;
  *out_address = (uint32_t)target_address64;
  return 1;
}

static int scan_biased_word_relative_control_targets_for_indexed_operand(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, size_t operand_index, const M68kRuntimeAddressSpace *runtime_addresses,
    const uint8_t *accepted_start, const uint8_t *accepted_bytes, const M68kFactsV2TraceValue *table_value,
    const M68kFactsV2TraceState *trace_state, M68kFactsV2TraceValue *out_targets) {
  uint32_t target_base_offset = 0U;
  uint32_t target_base_address = 0U;
  uint32_t table_offset;
  uint32_t targets[M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT];
  uint32_t target_count;
  if (out_targets != NULL) trace_value_set_unknown(out_targets);
  if (section == NULL || candidate == NULL || runtime_addresses == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || table_value == NULL || out_targets == NULL ||
      table_value->kind != M68K_FACTS_V2_TRACE_WORD_RELATIVE_TABLE ||
      table_value->section_index != section->section_index ||
      !indexed_control_operand_base_ref(section, candidate, operand_index, runtime_addresses, trace_state,
        &target_base_offset, &target_base_address) ||
      target_base_offset < table_value->value || ((target_base_offset - table_value->value) & 1U) != 0U) {
    return 0;
  }
  table_offset = table_value->value;
  while (table_offset < target_base_offset && table_offset + 2U <= section->size &&
      m68k_read_u16be(section->data + table_offset) == 0U) {
    table_offset += 2U;
  }
  target_count = scan_word_relative_control_target_table(section, runtime_addresses, accepted_start,
    accepted_bytes, table_offset, target_base_address, targets, M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT);
  if (target_count == 0U && table_offset < target_base_offset) {
    target_count = scan_word_relative_control_target_table(section, runtime_addresses, accepted_start,
      accepted_bytes, target_base_offset, target_base_address, targets, M68K_FACTS_V2_TRACE_TARGET_SET_LIMIT);
  }
  if (target_count == 0U) return 0;
  trace_value_set_target_set(out_targets, section->section_index, targets, target_count);
  return 1;
}

static int enqueue_trace_target_set_control_targets(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeCandidate *candidate, const M68kRuntimeAddressSpace *runtime_addresses,
    const M68kFactsV2TraceState *trace_state, const M68kFactsV2TraceValue *value, int *out_enqueued) {
  uint32_t target_index;
  if (out_enqueued != NULL) *out_enqueued = 0;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || candidate == NULL || value == NULL ||
      value->kind != M68K_FACTS_V2_TRACE_TARGET_SET || value->section_index != section_index) {
    return 0;
  }
  for (target_index = 0U; target_index < value->target_count; ++target_index) {
    if (control_target_address_starts_in_zero_padding(&decode->sections[section_index], runtime_addresses,
        section_index, value->targets[target_index])) {
      continue;
    }
    if (enqueue_same_section_control_target(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, section_index, candidate, value->targets[target_index],
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, runtime_addresses, trace_state) != 0) {
      return -1;
    }
    if (out_enqueued != NULL) *out_enqueued = 1;
  }
  return 0;
}

static int candidate_has_decoded_direct_control_target(const M68kDecodeCandidate *candidate) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
        target->kind == M68K_DECODE_TARGET_JUMP) {
      return 1;
    }
  }
  return 0;
}

static int trace_value_origin_is_direct_stack_address_push(M68kDecodeIR *decode,
    const M68kFactsV2TraceValue *value, uint8_t max_cpu) {
  const M68kDecodeSectionIR *origin_section;
  const M68kDecodeCandidate *origin_candidate;
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (decode == NULL || value == NULL || !value->has_origin ||
      value->origin_section_index >= decode->section_count) {
    return 0;
  }
  origin_section = &decode->sections[value->origin_section_index];
  origin_candidate = ensure_candidate_at_offset(decode, origin_section, value->origin_offset, max_cpu);
  if (origin_candidate == NULL || value->origin_operand_index >= origin_candidate->operand_count) return 0;
  if (m68k_decode_candidate_to_instruction(origin_candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata != NULL && metadata->operation_type == M68K_SIM_OP_PUSH_EA &&
      metadata->source_operand_index == value->origin_operand_index) {
    return 1;
  }
  return origin_candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && origin_candidate->size_suffix == 'l' &&
    origin_candidate->operand_count == 2U && value->origin_operand_index == 0U &&
    operand_is_stack_predecrement(&origin_candidate->operands[1]);
}

static int enqueue_stack_continuation_for_terminal_indirect_jump(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeCandidate *candidate, const M68kSimFormMetadata *metadata,
    const M68kRuntimeAddressSpace *runtime_addresses, const M68kFactsV2TraceState *trace_state,
    int resolved_indirect_target) {
  const M68kDecodeSectionIR *section;
  const M68kFactsV2StackSlot *slot;
  const M68kFactsV2TraceValue *value;
  uint32_t target_offset = 0U;
  uint32_t runtime_address = 0U;
  uint8_t has_runtime_address = 0U;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || candidate == NULL || metadata == NULL || trace_state == NULL ||
      section_index >= decode->section_count || !resolved_indirect_target ||
      metadata->flow_kind != M68K_SIM_FLOW_JUMP ||
      candidate_has_normal_fallthrough(candidate) || candidate_has_decoded_direct_control_target(candidate)) {
    return 0;
  }
  section = &decode->sections[section_index];
  slot = trace_state_find_stack_slot_const(trace_state, 0U);
  if (slot == NULL) return 0;
  value = &slot->value;
  if (!trace_value_origin_is_direct_stack_address_push(decode, value, max_cpu)) return 0;
  if (value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
    if (value->section_index != section_index) return 0;
    target_offset = value->value;
  } else if (value->kind == M68K_FACTS_V2_TRACE_RUNTIME_ADDRESS ||
      value->kind == M68K_FACTS_V2_TRACE_CONSTANT) {
    runtime_address = value->value;
    if (runtime_address_space_translate(runtime_addresses, section_index, runtime_address, section->size,
        &target_offset)) {
      has_runtime_address = 1U;
    } else if (runtime_address < section->size) {
      target_offset = runtime_address;
    } else {
      return 0;
    }
  } else {
    return 0;
  }
  if (target_offset <= candidate->offset) return 0;
  return enqueue_same_section_control_resolved_target_from_offset(decode, facts, queue, accepted_start,
    accepted_bytes, profile, max_cpu, section_index, candidate->offset, target_offset, has_runtime_address,
    runtime_address, M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_STACK_CONTINUATION,
    trace_state);
}

static int enqueue_traced_indirect_control_target(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeCandidate *candidate, const M68kRuntimeAddressSpace *runtime_addresses,
    const M68kFactsV2TraceState *trace_state) {
  M68kDecodeCandidate candidate_copy;
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint32_t target_address = 0U;
  size_t operand_index;
  int enqueued = 0;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || candidate == NULL || trace_state == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  candidate_copy = *candidate;
  candidate = &candidate_copy;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (operand_index >= instruction.operand_count ||
        metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
        metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) {
      continue;
    }
    if (!trace_state_control_target_operand_address(candidate, operand_index, section_index, trace_state,
        &target_address)) {
      const M68kAsmOperandValue *operand = &candidate->operands[operand_index];
      const M68kFactsV2TraceValue *value = NULL;
      if (indexed_control_operand_data_index_reg(candidate, operand_index, &reg)) {
        value = &trace_state->d[reg];
        if (value->kind == M68K_FACTS_V2_TRACE_WORD_RELATIVE_TABLE) {
          M68kFactsV2TraceValue biased_targets;
          int target_set_enqueued = 0;
          if (!scan_biased_word_relative_control_targets_for_indexed_operand(&decode->sections[section_index],
              candidate, operand_index, runtime_addresses, accepted_start[section_index],
              accepted_bytes[section_index], value, trace_state, &biased_targets)) {
            continue;
          }
          if (enqueue_trace_target_set_control_targets(decode, facts, queue, accepted_start, accepted_bytes,
              profile, max_cpu, section_index, candidate, runtime_addresses, trace_state, &biased_targets,
              &target_set_enqueued) != 0)
            return -1;
          if (target_set_enqueued) enqueued = 1;
          continue;
        }
      } else if (indexed_control_operand_address_index_reg(candidate, operand_index, &reg)) {
        value = &trace_state->a[reg];
        if (value->kind == M68K_FACTS_V2_TRACE_WORD_RELATIVE_TABLE) {
          M68kFactsV2TraceValue biased_targets;
          int target_set_enqueued = 0;
          if (!scan_biased_word_relative_control_targets_for_indexed_operand(&decode->sections[section_index],
              candidate, operand_index, runtime_addresses, accepted_start[section_index],
              accepted_bytes[section_index], value, trace_state, &biased_targets)) {
            continue;
          }
          if (enqueue_trace_target_set_control_targets(decode, facts, queue, accepted_start, accepted_bytes,
              profile, max_cpu, section_index, candidate, runtime_addresses, trace_state, &biased_targets,
              &target_set_enqueued) != 0)
            return -1;
          if (target_set_enqueued) enqueued = 1;
          continue;
        }
      } else {
        if (!operand_is_control_address_register_indirect(candidate->operand_kinds[operand_index], operand, &reg))
          continue;
        value = &trace_state->a[reg];
      }
      if (value != NULL && value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
        if (enqueue_same_section_control_trace_target(decode, facts, queue, accepted_start, accepted_bytes,
            profile, max_cpu, section_index, candidate, value, M68K_FACT_CONFIDENCE_TOOL_INFERRED,
            runtime_addresses, trace_state) != 0) {
          return -1;
        }
        enqueued = 1;
        continue;
      }
      {
        int target_set_enqueued = 0;
        if (enqueue_trace_target_set_control_targets(decode, facts, queue, accepted_start, accepted_bytes,
            profile, max_cpu, section_index, candidate, runtime_addresses, trace_state, value,
            &target_set_enqueued) != 0)
          return -1;
        if (target_set_enqueued) enqueued = 1;
      }
      continue;
    }
    if (control_target_address_starts_in_zero_padding(&decode->sections[section_index], runtime_addresses,
        section_index, target_address)) {
      continue;
    }
    if (enqueue_same_section_control_target(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, section_index, candidate, target_address, M68K_FACT_CONFIDENCE_TOOL_INFERRED,
        runtime_addresses, trace_state) != 0) {
      return -1;
    }
    enqueued = 1;
  }
  (void)enqueued;
  if (enqueue_stack_continuation_for_terminal_indirect_jump(decode, facts, queue, accepted_start, accepted_bytes,
      profile, max_cpu, section_index, candidate, metadata, runtime_addresses, trace_state, enqueued) != 0) {
    return -1;
  }
  return 0;
}

static int enqueue_traced_copied_entry_control_target(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeCandidate *candidate, const M68kFactsV2TraceState *trace_state) {
  M68kDecodeCandidate candidate_copy;
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || candidate == NULL || trace_state == NULL || !trace_state->copied_entry_valid ||
      trace_state->copied_entry_section_index != section_index ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  candidate_copy = *candidate;
  candidate = &candidate_copy;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
    const M68kAsmOperandValue *operand;
    uint8_t reg = 0U;
    if (operand_index >= instruction.operand_count ||
        metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
        metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) {
      continue;
    }
    operand = &candidate->operands[operand_index];
    if (!operand_is_control_address_register_indirect(candidate->operand_kinds[operand_index], operand, &reg)) continue;
    if (reg != trace_state->copied_entry_dest_reg) continue;
    return enqueue_same_section_control_resolved_target(decode, facts, queue, accepted_start, accepted_bytes,
      profile, max_cpu, section_index, candidate, trace_state->copied_entry_source_offset, 0U, 0U,
      M68K_FACT_CONFIDENCE_TOOL_INFERRED, trace_state);
  }
  return 0;
}

static uint8_t recovered_indirect_flow_kind_from_metadata(const M68kSimFormMetadata *metadata) {
  if (metadata == NULL) return 0U;
  if (metadata->flow_kind == M68K_SIM_FLOW_CALL) return M68K_RECOVERED_INDIRECT_FLOW_CALL;
  if (metadata->flow_kind == M68K_SIM_FLOW_JUMP) return M68K_RECOVERED_INDIRECT_FLOW_JUMP;
  return 0U;
}

static int decode_target_is_indexed_control_operand_base(const M68kDecodeCandidate *candidate,
    const M68kDecodeTarget *target) {
  if (candidate == NULL || target == NULL || !target->has_operand ||
      target->operand_index >= candidate->operand_count ||
      (target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_CALL &&
       target->kind != M68K_DECODE_TARGET_JUMP)) {
    return 0;
  }
  return facts_v2_asm_operand_is_indexed_or_pc_indexed(&candidate->operands[target->operand_index]);
}

static uint8_t recovered_indirect_shape_for_operand(const M68kDecodeCandidate *candidate,
    const M68kSimFormMetadata *metadata, size_t operand_index) {
  const M68kAsmOperandValue *operand;
  int uses_index;
  int uses_displacement;
  int decoded_index_form;
  if (candidate == NULL || metadata == NULL || operand_index >= candidate->operand_count ||
      operand_index >= 4U) {
    return 0U;
  }
  operand = &candidate->operands[operand_index];
  if (candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_IND ||
      candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_POSTINC ||
      candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_PREDEC) {
    return M68K_RECOVERED_INDIRECT_SHAPE_IND;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->ea_reg >= 8U) return 0U;
  if (operand->ea_mode == 7U && (operand->ea_reg == 0U || operand->ea_reg == 1U)) return 0U;
  decoded_index_form = facts_v2_asm_operand_is_indexed_or_pc_indexed(operand);
  uses_index = metadata->operand_ea_uses_index[operand_index] != 0U || decoded_index_form;
  uses_displacement = metadata->operand_ea_uses_displacement[operand_index] != 0U || decoded_index_form;
  if (!uses_index && !uses_displacement) return M68K_RECOVERED_INDIRECT_SHAPE_IND;
  if (!uses_index && uses_displacement) return M68K_RECOVERED_INDIRECT_SHAPE_DISP;
  if (operand->full_ext_iis != 0U) return M68K_RECOVERED_INDIRECT_SHAPE_INDEX_MEMIND;
  if (operand->full_ext_base_disp_size != M68K_ASM_FULL_EXT_BD_RESERVED ||
      operand->full_ext_outer_disp_size != 0U || operand->full_ext_base_suppress != 0U ||
      operand->full_ext_index_suppress != 0U) {
    return M68K_RECOVERED_INDIRECT_SHAPE_INDEX_FULL;
  }
  return M68K_RECOVERED_INDIRECT_SHAPE_INDEX_BRIEF;
}

static int candidate_single_direct_nonfallthrough_control_target(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint8_t *out_target_kind, uint32_t *out_target_offset);

static int candidate_is_nonfallthrough_stub_entry(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint8_t *out_target_kind, uint32_t *out_target_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t target_kind = 0U;
  uint32_t target_offset = 0U;
  if (out_target_kind != NULL) *out_target_kind = 0U;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (candidate == NULL) return 0;
  if (candidate_single_direct_nonfallthrough_control_target(section, candidate, &target_kind, &target_offset) &&
      (target_kind == M68K_DECODE_TARGET_BRANCH || target_kind == M68K_DECODE_TARGET_JUMP)) {
    if (out_target_kind != NULL) *out_target_kind = target_kind;
    if (out_target_offset != NULL) *out_target_offset = target_offset;
    return 1;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || candidate_has_normal_fallthrough(candidate)) return 0;
  return metadata->flow_kind == M68K_SIM_FLOW_RETURN || metadata->flow_kind == M68K_SIM_FLOW_TRAP;
}

static void recovered_indirect_site_set_table_base_status(M68kRecoveredIndirectSiteIR *site,
    uint32_t table_offset, uint8_t status) {
  if (site == NULL) return;
  site->has_table_base = 1U;
  site->table_offset = table_offset;
  site->table_bounds_status = status;
}

static void recovered_indirect_site_apply_expression_base(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, M68kRecoveredIndirectSiteIR *site) {
  uint32_t expression_base_offset = 0U;
  if (section == NULL || candidate == NULL || site == NULL ||
      site->operand_index >= candidate->operand_count ||
      !candidate_operand_data_target_offset(candidate, site->operand_index, section->section_index,
        &expression_base_offset)) {
    return;
  }
  site->has_expression_base = 1U;
  site->expression_base_offset = expression_base_offset;
}

static void recovered_indirect_site_apply_direct_stub_table_bounds(M68kDecodeIR *decode,
    size_t section_index, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate,
    uint8_t max_cpu, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kRecoveredIndirectSiteIR *site) {
  const uint32_t scan_limit = 64U;
  uint32_t table_offset = 0U;
  uint32_t cursor;
  uint32_t stride = 0U;
  uint32_t entry_count = 0U;
  uint32_t first_forward_target = UINT32_MAX;
  if (decode == NULL || section == NULL || site_candidate == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || site == NULL || section_index >= decode->section_count ||
      site->operand_index >= site_candidate->operand_count ||
      !candidate_operand_data_target_offset(site_candidate, site->operand_index, section->section_index,
        &table_offset)) {
    return;
  }
  if (table_offset < site_candidate->offset ||
      table_offset - site_candidate->offset < site_candidate->byte_count) {
    return;
  }
  recovered_indirect_site_set_table_base_status(site, table_offset,
    M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_NONE);
  cursor = table_offset;
  while (cursor < section->size && entry_count < scan_limit) {
    const M68kDecodeCandidate *candidate = NULL;
    uint8_t target_kind = 0U;
    uint32_t target_offset = 0U;
    if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index], cursor))
      break;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0) {
      break;
    }
    if (candidate == NULL) {
      if (entry_count == 0U) {
        site->has_table_bounds = 1U;
        site->table_bounds_status = M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_UNDECODED_ENTRY;
        site->table_entry_size = 0U;
        site->table_entry_count = 0U;
        site->table_size = 0U;
      }
      break;
    }
    if (!candidate_is_nonfallthrough_stub_entry(section, candidate, &target_kind, &target_offset)) {
      if (entry_count == 0U) {
        site->has_table_bounds = 1U;
        site->table_bounds_status = M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_UNSUPPORTED_ENTRY_SHAPE;
        site->table_entry_size = candidate->byte_count;
        site->table_entry_count = 1U;
        site->table_size = candidate->byte_count;
      }
      break;
    }
    if (accepted_range_has_code_byte_local(accepted_bytes[section_index], section->size, cursor,
        candidate->byte_count)) {
      site->has_table_base = 1U;
      site->has_table_bounds = 1U;
      site->table_bounds_status = M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_CODE_OVERLAP;
      site->table_offset = table_offset;
      site->table_entry_size = candidate->byte_count;
      site->table_entry_count = 1U;
      site->table_size = candidate->byte_count;
      return;
    }
    if (stride == 0U) {
      stride = candidate->byte_count;
      if (stride == 0U) break;
    } else if (candidate->byte_count != stride) {
      break;
    }
    if (target_offset > table_offset && target_offset < first_forward_target)
      first_forward_target = target_offset;
    ++entry_count;
    if (cursor > UINT32_MAX - stride) break;
    cursor += stride;
    if (entry_count >= 2U && first_forward_target != UINT32_MAX && cursor >= first_forward_target)
      break;
  }
  if (entry_count == 0U || entry_count >= 2U || stride == 0U) return;
  {
    uint32_t entries[64];
    uint32_t interleaved_count = 0U;
    uint32_t interleaved_table = 0U;
    uint32_t interleaved_stride = 0U;
    if (scan_interleaved_indexed_key_stub_table(decode, max_cpu, section_index, section, site_candidate,
        accepted_start, accepted_bytes, entries, 64U, &interleaved_count, &interleaved_table,
        &interleaved_stride)) {
      site->has_table_base = 1U;
      site->has_table_bounds = 1U;
      site->table_bounds_status = M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_NONE;
      site->table_offset = interleaved_table;
      site->table_entry_size = interleaved_stride;
      site->table_entry_count = interleaved_count;
      site->table_size = interleaved_stride * interleaved_count;
      return;
    }
  }
  site->has_table_base = 1U;
  site->has_table_bounds = 1U;
  site->table_bounds_status = M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_INSUFFICIENT_ENTRIES;
  site->table_offset = table_offset;
  site->table_entry_size = stride;
  site->table_entry_count = entry_count;
  site->table_size = stride * entry_count;
}

static void recovered_indirect_site_apply_code_start_refs(M68kRecoveredIndirectSiteIR *site,
    const M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  uint32_t count = 0U;
  uint32_t first_target = 0U;
  if (site == NULL || section_analysis == NULL) return;
  for (index = 0U; index < section_analysis->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section_analysis->code_start_refs[index];
    if (ref->source_section_index != section_analysis->section_index ||
        ref->source_offset != site->offset ||
        ref->reason != M68K_FACT_CODE_START_REASON_CONTROL_TARGET) {
      continue;
    }
    if (count == 0U) first_target = ref->offset;
    if (count != UINT32_MAX) ++count;
  }
  if (count == 0U) return;
  site->has_target = 1U;
  site->target = first_target;
  site->has_target_count = 1U;
  site->target_count = count;
  site->status = count > 1U ? M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE :
    M68K_RECOVERED_INDIRECT_STATUS_BACKWARD_SLICE;
  site->detail = count > 1U ? "accepted indirect jump table targets" :
    "accepted traced indirect control target";
}

static void recovered_indirect_site_finalize_table_candidate(M68kRecoveredIndirectSiteIR *site) {
  if (site == NULL) return;
  site->source_pattern_id = m68k_recovered_indirect_source_pattern_id(site->shape);
  site->conflict_state = M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED;
  if (site->status == M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE ||
      site->status == M68K_RECOVERED_INDIRECT_STATUS_RESOLVED_RUNTIME ||
      site->status == M68K_RECOVERED_INDIRECT_STATUS_RUNTIME ||
      site->status == M68K_RECOVERED_INDIRECT_STATUS_EXTERNAL) {
    site->is_table_candidate = 0U;
    return;
  }
  site->is_table_candidate = (uint8_t)(site->has_table_base != 0U || site->has_table_bounds != 0U ||
    site->has_expression_base != 0U || site->table_bounds_status != M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_NONE);
}

static int candidate_indexed_control_table_offset(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t *out_table_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (out_table_offset != NULL) *out_table_offset = 0U;
  if (candidate == NULL || out_table_offset == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U &&
       operand_index < instruction.operand_count; ++operand_index) {
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
        metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET ||
        !facts_v2_instruction_operand_is_indexed_or_pc_indexed(&instruction, operand_index)) {
      continue;
    }
    if (candidate_operand_data_target_offset(candidate, operand_index, section_index, out_table_offset))
      return 1;
  }
  return 0;
}

static int candidate_indexed_control_table_offset_and_index_reg(const M68kDecodeCandidate *candidate,
    size_t section_index, uint32_t *out_table_offset, uint8_t *out_index_reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (out_table_offset != NULL) *out_table_offset = 0U;
  if (out_index_reg != NULL) *out_index_reg = 0U;
  if (candidate == NULL || out_table_offset == NULL || out_index_reg == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U &&
       operand_index < instruction.operand_count; ++operand_index) {
    const M68kAsmOperandValue *operand = &candidate->operands[operand_index];
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
        metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET ||
        !facts_v2_instruction_operand_is_indexed_or_pc_indexed(&instruction, operand_index) ||
        candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA ||
        operand->index_is_address || operand->index_reg >= 8U) {
      continue;
    }
    if (candidate_operand_data_target_offset(candidate, operand_index, section_index, out_table_offset)) {
      *out_index_reg = operand->index_reg;
      return 1;
    }
  }
  return 0;
}

static int candidate_indexed_data_read_table_offset_and_width(const M68kDecodeCandidate *candidate,
    size_t section_index, uint8_t index_reg, uint32_t *out_table_offset, uint32_t *out_width) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (out_table_offset != NULL) *out_table_offset = 0U;
  if (out_width != NULL) *out_width = 0U;
  if (candidate == NULL || out_table_offset == NULL || out_width == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U &&
       operand_index < instruction.operand_count; ++operand_index) {
    const M68kAsmOperandValue *operand = &candidate->operands[operand_index];
    uint32_t table_offset = 0U;
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_MEMORY_READ ||
        !facts_v2_instruction_operand_is_indexed_or_pc_indexed(&instruction, operand_index) ||
        candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA ||
        operand->index_is_address || operand->index_reg != index_reg) {
      continue;
    }
    if (!candidate_operand_data_target_offset(candidate, operand_index, section_index, &table_offset))
      continue;
    *out_table_offset = table_offset;
    *out_width = facts_v2_instruction_access_width(&instruction, M68K_SIM_ACCESS_MEMORY_READ);
    return *out_width != 0U;
  }
  return 0;
}

static int find_nearby_indexed_key_table_for_control(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *site_candidate, const uint8_t *accepted_start, uint8_t index_reg,
    uint32_t stub_table_offset, uint32_t *out_key_table_offset, uint32_t *out_key_width) {
  const uint32_t lookback_limit = 12U;
  size_t candidate_index;
  uint32_t best_offset = 0U;
  uint32_t best_table_offset = 0U;
  uint32_t best_width = 0U;
  if (out_key_table_offset != NULL) *out_key_table_offset = 0U;
  if (out_key_width != NULL) *out_key_width = 0U;
  if (section == NULL || site_candidate == NULL || accepted_start == NULL ||
      out_key_table_offset == NULL || out_key_width == NULL) {
    return 0;
  }
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    uint32_t key_table_offset = 0U;
    uint32_t key_width = 0U;
    if (candidate->offset >= site_candidate->offset || accepted_start[candidate->offset] == 0U ||
        candidate->byte_count > site_candidate->offset - candidate->offset ||
        site_candidate->offset - (candidate->offset + candidate->byte_count) > lookback_limit) {
      continue;
    }
    if (!candidate_indexed_data_read_table_offset_and_width(candidate, section->section_index, index_reg,
        &key_table_offset, &key_width)) {
      continue;
    }
    if (key_width == 0U || key_table_offset > UINT32_MAX - key_width ||
        key_table_offset + key_width != stub_table_offset) {
      continue;
    }
    if (best_width == 0U || candidate->offset > best_offset) {
      best_offset = candidate->offset;
      best_table_offset = key_table_offset;
      best_width = key_width;
    }
  }
  if (best_width == 0U) return 0;
  *out_key_table_offset = best_table_offset;
  *out_key_width = best_width;
  return 1;
}

static int scan_interleaved_indexed_key_stub_table(M68kDecodeIR *decode, uint8_t max_cpu, size_t section_index,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate, uint8_t **accepted_start,
    uint8_t **accepted_bytes, uint32_t *out_entries, uint32_t entry_limit, uint32_t *out_entry_count,
    uint32_t *out_stub_table_offset, uint32_t *out_stride) {
  uint32_t stub_table_offset = 0U;
  uint32_t key_table_offset = 0U;
  uint32_t key_width = 0U;
  uint32_t cursor;
  uint32_t stride = 0U;
  uint32_t entry_count = 0U;
  uint32_t stub_width = 0U;
  uint32_t first_forward_target = UINT32_MAX;
  uint8_t index_reg = 0U;
  if (out_entry_count != NULL) *out_entry_count = 0U;
  if (out_stub_table_offset != NULL) *out_stub_table_offset = 0U;
  if (out_stride != NULL) *out_stride = 0U;
  if (decode == NULL || section == NULL || site_candidate == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || out_entries == NULL || out_entry_count == NULL ||
      out_stub_table_offset == NULL || out_stride == NULL || entry_limit == 0U ||
      section_index >= decode->section_count ||
      !candidate_indexed_control_table_offset_and_index_reg(site_candidate, section->section_index,
        &stub_table_offset, &index_reg) ||
      !find_nearby_indexed_key_table_for_control(section, site_candidate, accepted_start[section_index],
        index_reg, stub_table_offset, &key_table_offset, &key_width)) {
    return 0;
  }
  cursor = stub_table_offset;
  while (cursor < section->size && entry_count < entry_limit) {
    const M68kDecodeCandidate *candidate = NULL;
    uint8_t target_kind = 0U;
    uint32_t target_offset = 0U;
    uint32_t key_offset = key_table_offset;
    if (entry_count != 0U) {
      uint32_t key_delta;
      if (stride == 0U || entry_count > UINT32_MAX / stride) break;
      key_delta = entry_count * stride;
      if (key_table_offset > UINT32_MAX - key_delta) break;
      key_offset = key_table_offset + key_delta;
    }
    if (key_offset > UINT32_MAX - key_width) break;
    if (accepted_range_has_code_byte_local(accepted_bytes[section_index], section->size, key_offset, key_width))
      break;
    if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index], cursor))
      break;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (candidate == NULL || !candidate_single_direct_nonfallthrough_control_target(section, candidate,
        &target_kind, &target_offset) || target_kind != M68K_DECODE_TARGET_BRANCH) {
      break;
    }
    if (stub_width == 0U) {
      stub_width = candidate->byte_count;
      if (stub_width == 0U || key_width > UINT32_MAX - stub_width) break;
      stride = key_width + stub_width;
    } else if (candidate->byte_count != stub_width) {
      break;
    }
    if (target_offset > stub_table_offset && target_offset < first_forward_target)
      first_forward_target = target_offset;
    out_entries[entry_count++] = cursor;
    if (cursor > UINT32_MAX - stride) break;
    cursor += stride;
    if (entry_count >= 2U && first_forward_target != UINT32_MAX && cursor >= first_forward_target)
      break;
  }
  if (entry_count < 2U || stride == 0U) return 0;
  *out_entry_count = entry_count;
  *out_stub_table_offset = stub_table_offset;
  *out_stride = stride;
  return 1;
}

static int enqueue_direct_indexed_stub_entries(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate,
    const M68kRuntimeAddressSpace *runtime_addresses) {
  enum { STUB_ENTRY_LIMIT = 64 };
  uint32_t entries[STUB_ENTRY_LIMIT];
  uint32_t table_offset = 0U;
  uint32_t cursor;
  uint32_t stride = 0U;
  uint32_t entry_count = 0U;
  uint32_t index;
  M68kFactsV2TraceState unknown_state;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || section == NULL || site_candidate == NULL || runtime_addresses == NULL ||
      section_index >= decode->section_count ||
      !candidate_indexed_control_table_offset(site_candidate, section->section_index, &table_offset)) {
    return 0;
  }
  if (indexed_control_operand_base_is_inside_instruction(site_candidate, table_offset) &&
      !indexed_control_post_instruction_table_start(section, site_candidate, table_offset, &table_offset)) {
    return 0;
  }
  cursor = table_offset;
  while (cursor < section->size && entry_count < STUB_ENTRY_LIMIT) {
    const M68kDecodeCandidate *candidate = NULL;
    if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index], cursor))
      break;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0)
      return -1;
    if (candidate == NULL || !candidate_is_nonfallthrough_stub_entry(section, candidate, NULL, NULL))
      break;
    if (stride == 0U) {
      stride = candidate->byte_count;
      if (stride == 0U) break;
    } else if (candidate->byte_count != stride) {
      break;
    }
    entries[entry_count++] = cursor;
    if (cursor > UINT32_MAX - stride) break;
    cursor += stride;
  }
  if (entry_count < 2U) {
    int scan_result = 0;
    uint32_t operand_base_offset = 0U;
    uint32_t post_instruction_table_offset = 0U;
    if (candidate_indexed_control_table_offset(site_candidate, section->section_index, &operand_base_offset) &&
        indexed_control_post_instruction_table_start(section, site_candidate, operand_base_offset,
          &post_instruction_table_offset)) {
      scan_result = scan_indexed_direct_variable_stub_entries(decode, max_cpu, section_index, section,
        post_instruction_table_offset, accepted_start, accepted_bytes, entries, STUB_ENTRY_LIMIT, &entry_count);
      if (scan_result < 0) return -1;
    }
    if (scan_result == 0 &&
        !scan_interleaved_indexed_key_stub_table(decode, max_cpu, section_index, section, site_candidate,
          accepted_start, accepted_bytes, entries, STUB_ENTRY_LIMIT, &entry_count, &table_offset, &stride)) {
      return 0;
    }
  }
  trace_state_init_unknown(&unknown_state);
  for (index = 0U; index < entry_count; ++index) {
    if (enqueue_same_section_control_target_from_offset(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, section_index, site_candidate->offset, entries[index],
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, runtime_addresses, &unknown_state) != 0) {
      return -1;
    }
  }
  return 0;
}

static int section_analysis_has_platform_call_at_offset(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return 0;
  for (index = 0U; index < section_analysis->recovered_platform_call_count; ++index) {
    if (section_analysis->recovered_platform_calls[index].offset == offset) return 1;
  }
  return 0;
}

static int append_recovered_indirect_sites_for_accepted(M68kDecodeIR *decode,
    uint8_t **accepted_start, uint8_t **accepted_bytes, M68kSourceAnalysisIR *source_analysis, uint8_t max_cpu) {
  size_t section_index;
  if (decode == NULL || accepted_start == NULL || accepted_bytes == NULL || source_analysis == NULL ||
      source_analysis->section_count < decode->section_count) {
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const M68kSimFormMetadata *metadata;
      uint8_t flow_kind;
      size_t operand_index;
      if (candidate->offset >= section->size || accepted_start[section_index][candidate->offset] == 0U)
        continue;
      if (candidate_has_decoded_direct_control_target(candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      metadata = m68k_sim_metadata_for_instruction(&instruction);
      flow_kind = recovered_indirect_flow_kind_from_metadata(metadata);
      if (flow_kind == 0U) continue;
      for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U &&
           operand_index < instruction.operand_count; ++operand_index) {
        M68kRecoveredIndirectSiteIR site;
        uint8_t shape;
        if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
            metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) {
          continue;
        }
        if (section_analysis_has_platform_call_at_offset(&source_analysis->sections[section_index],
            candidate->offset)) {
          continue;
        }
        shape = recovered_indirect_shape_for_operand(candidate, metadata, operand_index);
        if (shape == 0U) continue;
        memset(&site, 0, sizeof(site));
        site.offset = candidate->offset;
        site.flow_kind = flow_kind;
        site.shape = shape;
        site.status = M68K_RECOVERED_INDIRECT_STATUS_UNRESOLVED;
        site.operand_index = (uint8_t)operand_index;
        site.source_size = candidate->byte_count;
        site.detail = "accepted indirect control target";
        recovered_indirect_site_apply_expression_base(section, candidate, &site);
        recovered_indirect_site_apply_code_start_refs(&site, &source_analysis->sections[section_index]);
        if (site.status == M68K_RECOVERED_INDIRECT_STATUS_UNRESOLVED) {
          recovered_indirect_site_apply_direct_stub_table_bounds(decode, section_index, section, candidate,
            max_cpu, accepted_start, accepted_bytes, &site);
        }
        recovered_indirect_site_finalize_table_candidate(&site);
        if (m68k_ir_section_analysis_append_recovered_indirect_site(&source_analysis->sections[section_index],
            &site) != 0) {
          return -1;
        }
      }
    }
  }
  return 0;
}

static int candidate_indirect_control_uses_address_reg(const M68kDecodeCandidate *candidate, uint8_t reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (candidate == NULL || reg >= 8U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U &&
       operand_index < instruction.operand_count; ++operand_index) {
    const M68kAsmOperandValue *operand = &candidate->operands[operand_index];
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
        metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) {
      continue;
    }
    if ((candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_IND ||
         candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_POSTINC ||
         candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_PREDEC) &&
        operand->reg == reg) {
      return 1;
    }
    {
      uint8_t indirect_reg = 0U;
      if (operand_is_plain_address_register_indirect(candidate->operand_kinds[operand_index],
          operand, &indirect_reg) && indirect_reg == reg) {
        return 1;
      }
    }
  }
  return 0;
}

static int enqueue_immediate_indirect_target_set(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kRuntimeAddressSpace *runtime_addresses, const M68kFactsV2TraceState *trace_state) {
  uint32_t next_offset;
  const M68kDecodeCandidate *next_candidate = NULL;
  M68kDecodeCandidate next_candidate_copy;
  uint8_t reg;
  if (decode == NULL || facts == NULL || queue == NULL || section == NULL || candidate == NULL ||
      trace_state == NULL || !candidate_has_normal_fallthrough(candidate) ||
      candidate->byte_count > UINT32_MAX - candidate->offset) {
    return 0;
  }
  next_offset = candidate->offset + candidate->byte_count;
  if (next_offset >= section->size) return 0;
  if (m68k_decode_ir_ensure_candidate_at(decode, section_index, next_offset, max_cpu, &next_candidate,
      m68k_diag_sink(NULL)) != 0)
    return -1;
  if (next_candidate == NULL) return 0;
  next_candidate_copy = *next_candidate;
  next_candidate = &next_candidate_copy;
  for (reg = 0U; reg < 8U; ++reg) {
    uint32_t target_index;
    const M68kFactsV2TraceValue *value = &trace_state->a[reg];
    if (!candidate_indirect_control_uses_address_reg(next_candidate, reg)) {
      continue;
    }
    if (value->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
      if (enqueue_same_section_control_trace_target(decode, facts, queue, accepted_start, accepted_bytes,
          profile, max_cpu, section_index, next_candidate, value, M68K_FACT_CONFIDENCE_TOOL_INFERRED,
          runtime_addresses, trace_state) != 0) {
        return -1;
      }
      continue;
    }
    if (!trace_value_is_target_set(value) || value->section_index != section_index) continue;
    for (target_index = 0U; target_index < value->target_count; ++target_index) {
      if (enqueue_same_section_control_target_from_offset(decode, facts, queue, accepted_start, accepted_bytes,
          profile, max_cpu, section_index, next_candidate->offset, value->targets[target_index],
          M68K_FACT_CONFIDENCE_TOOL_INFERRED, runtime_addresses, NULL) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static const M68kDecodeCandidate *find_accepted_candidate_ending_at(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t end_offset) {
  size_t candidate_index;
  if (section == NULL || accepted_start == NULL) return NULL;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    if (candidate->offset > end_offset || candidate->byte_count > end_offset - candidate->offset) continue;
    if (candidate->offset + candidate->byte_count == end_offset && accepted_start[candidate->offset])
      return candidate;
  }
  return NULL;
}

static int candidate_indirect_control_address_register(const M68kDecodeCandidate *candidate, uint8_t *out_reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || out_reg == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U &&
       operand_index < instruction.operand_count; ++operand_index) {
    const M68kAsmOperandValue *operand = &candidate->operands[operand_index];
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
        metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) {
      continue;
    }
    if (operand_is_control_address_register_indirect(candidate->operand_kinds[operand_index], operand, out_reg))
      return 1;
  }
  return 0;
}

static int candidate_indirect_control_base_register(const M68kDecodeCandidate *candidate, uint8_t *out_reg) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || out_reg == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U &&
       operand_index < instruction.operand_count; ++operand_index) {
    uint8_t base_reg = 0U;
    int32_t displacement = 0;
    const M68kAsmOperandValue *operand = &candidate->operands[operand_index];
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
        metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) {
      continue;
    }
    if (operand_is_control_address_register_indirect(candidate->operand_kinds[operand_index], operand, out_reg))
      return 1;
    if (candidate_operand_base_field_slot(candidate, operand_index, &base_reg, &displacement) &&
        displacement == 0) {
      *out_reg = base_reg;
      return 1;
    }
  }
  return 0;
}

static int enqueue_target_set_for_indirect_site(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index,
    const M68kDecodeCandidate *site_candidate, const M68kFactsV2TraceValue *targets,
    const M68kRuntimeAddressSpace *runtime_addresses, const M68kDecodeSectionIR *section) {
  M68kFactsV2TraceState unknown_state;
  uint32_t index;
  uint32_t source_offset;
  if (site_candidate == NULL || !trace_value_is_target_set(targets)) return 0;
  source_offset = site_candidate->offset;
  trace_state_init_unknown(&unknown_state);
  for (index = 0U; index < targets->target_count; ++index) {
    if (control_target_address_starts_in_zero_padding(section, runtime_addresses, section_index,
        targets->targets[index])) {
      continue;
    }
    if (enqueue_same_section_control_target_from_offset(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, section_index, source_offset, targets->targets[index],
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, runtime_addresses, &unknown_state) != 0) {
      return -1;
    }
  }
  return 0;
}

static int callback_field_targets_append(Arena *arena, M68kFactsV2CallbackFieldTargets *targets,
    const M68kFactsV2CallbackFieldTarget *target) {
  size_t index;
  if (arena == NULL || targets == NULL || target == NULL) return -1;
  for (index = 0U; index < targets->count; ++index) {
    const M68kFactsV2CallbackFieldTarget *existing = &targets->items[index];
    if (existing->section_index == target->section_index && existing->base_reg == target->base_reg &&
        existing->displacement == target->displacement && existing->target.kind == target->target.kind &&
        existing->target.section_index == target->target.section_index &&
        existing->target.value == target->target.value) {
      return 0;
    }
  }
  if (targets->count == targets->capacity) {
    size_t next_capacity = targets->capacity != 0U ? targets->capacity * 2U : 16U;
    size_t old_size = targets->capacity * sizeof(*targets->items);
    size_t new_size = next_capacity * sizeof(*targets->items);
    M68kFactsV2CallbackFieldTarget *grown =
      (M68kFactsV2CallbackFieldTarget *)arena_realloc_copy(arena, targets->items, old_size, new_size);
    if (grown == NULL) return -1;
    targets->items = grown;
    targets->capacity = next_capacity;
  }
  targets->items[targets->count++] = *target;
  return 0;
}

static int callback_field_target_resolves_to_decode(M68kDecodeIR *decode,
    const M68kRuntimeAddressSpace *runtime_addresses, uint8_t **accepted_start, uint8_t **accepted_bytes,
    uint8_t max_cpu, size_t section_index, const M68kDecodeSectionIR *section,
    const M68kFactsV2TraceValue *target) {
  uint32_t target_offset = 0U;
  const M68kDecodeCandidate *target_candidate = NULL;
  if (decode == NULL || runtime_addresses == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      section == NULL || target == NULL || section_index >= decode->section_count) {
    return 0;
  }
  if (!trace_value_is_same_section_control_address(target, section_index)) return 0;
  if (target->kind == M68K_FACTS_V2_TRACE_SOURCE_OFFSET) {
    if (target->section_index != section_index || target->value >= section->size) return 0;
    target_offset = target->value;
  } else {
    if (control_target_address_starts_in_zero_padding(section, runtime_addresses, section_index,
        target->value)) {
      return 0;
    }
    if (!control_address_to_section_offset(runtime_addresses, section_index, section->size,
        target->value, &target_offset)) {
      return 0;
    }
  }
  if ((target_offset & 1U) != 0U || target_offset >= section->size) return 0;
  if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index],
      target_offset)) {
    return 0;
  }
  if (m68k_decode_ir_ensure_candidate_at(decode, section_index, target_offset, max_cpu, &target_candidate,
      m68k_diag_sink(NULL)) != 0) {
    return -1;
  }
  return target_candidate != NULL;
}

static int collect_callback_field_target_from_store(M68kDecodeIR *decode,
    const M68kFactsV2RelocationLookup *relocation_lookup, const M68kRuntimeAddressSpace *runtime_addresses,
    Arena *arena, M68kFactsV2CallbackFieldTargets *targets, uint8_t **accepted_start,
    uint8_t **accepted_bytes, uint8_t max_cpu, size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *store_candidate) {
  enum { BACKWARD_SLICE_LIMIT = 6 };
  const M68kDecodeCandidate *previous[BACKWARD_SLICE_LIMIT];
  const M68kDecodeCandidate *cursor_candidate;
  M68kFactsV2TraceState state;
  M68kFactsV2TraceValue stored_value;
  M68kFactsV2CallbackFieldTarget target;
  uint32_t cursor;
  uint8_t base_reg = 0U;
  int32_t displacement = 0;
  size_t count = 0U;
  size_t index;
  int resolve_result;
  if (decode == NULL || relocation_lookup == NULL || runtime_addresses == NULL || arena == NULL ||
      targets == NULL || accepted_start == NULL || accepted_bytes == NULL || section == NULL ||
      store_candidate == NULL || store_candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
      store_candidate->size_suffix != 'l' || store_candidate->operand_count != 2U ||
      !candidate_operand_base_field_slot(store_candidate, 1U, &base_reg, &displacement)) {
    return 0;
  }
  cursor = store_candidate->offset;
  while (count < BACKWARD_SLICE_LIMIT) {
    cursor_candidate = find_accepted_candidate_ending_at(section, accepted_start[section_index], cursor);
    if (cursor_candidate == NULL) break;
    previous[count++] = cursor_candidate;
    cursor = cursor_candidate->offset;
    if (cursor == 0U) break;
  }
  trace_state_init_unknown(&state);
  for (index = count; index > 0U; --index) {
    const M68kDecodeCandidate *candidate = previous[index - 1U];
    M68kFactsV2TraceState next_state;
    trace_state_after_candidate(section_index, section, candidate, &state, relocation_lookup, NULL,
      runtime_addresses, accepted_start[section_index], accepted_bytes[section_index], &next_state);
    state = next_state;
  }
  if (!trace_value_from_candidate_source(section_index, section, store_candidate, 0U, &state, &stored_value))
    return 0;
  resolve_result = callback_field_target_resolves_to_decode(decode, runtime_addresses, accepted_start,
    accepted_bytes, max_cpu, section_index, section, &stored_value);
  if (resolve_result < 0) return -1;
  if (resolve_result == 0) {
    return 0;
  }
  memset(&target, 0, sizeof(target));
  target.section_index = section_index;
  target.store_offset = store_candidate->offset;
  target.base_reg = base_reg;
  target.displacement = displacement;
  target.target = stored_value;
  return callback_field_targets_append(arena, targets, &target);
}

static int collect_callback_field_targets_for_accepted(M68kDecodeIR *decode,
    const M68kFactsV2RelocationLookup *relocation_lookup, const M68kRuntimeAddressSpace *runtime_addresses,
    Arena *arena, uint8_t **accepted_start, uint8_t **accepted_bytes, uint8_t max_cpu,
    M68kFactsV2CallbackFieldTargets *out_targets) {
  size_t section_index;
  if (decode == NULL || relocation_lookup == NULL || runtime_addresses == NULL || arena == NULL ||
      accepted_start == NULL || accepted_bytes == NULL || out_targets == NULL) {
    return -1;
  }
  memset(out_targets, 0, sizeof(*out_targets));
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    if (accepted_start[section_index] == NULL || accepted_bytes[section_index] == NULL) return -1;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      if (candidate->offset >= section->size || !accepted_start[section_index][candidate->offset]) continue;
      if (collect_callback_field_target_from_store(decode, relocation_lookup, runtime_addresses, arena,
          out_targets, accepted_start, accepted_bytes, max_cpu, section_index, section, candidate) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int candidate_loads_callback_field_to_control_register(const M68kDecodeCandidate *candidate,
    uint8_t control_reg, uint8_t *out_base_reg, int32_t *out_displacement) {
  uint8_t dest_reg = 0U;
  if (out_base_reg != NULL) *out_base_reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA ||
      candidate->size_suffix != 'l' || candidate->operand_count != 2U ||
      !operand_is_address_register_direct(&candidate->operands[1], &dest_reg) || dest_reg != control_reg) {
    return 0;
  }
  return candidate_operand_base_field_slot(candidate, 0U, out_base_reg, out_displacement);
}

static int trace_callback_site_linear_state(const M68kFactsV2RelocationLookup *relocation_lookup,
    const M68kRuntimeAddressSpace *runtime_addresses, uint8_t **accepted_start, uint8_t **accepted_bytes,
    size_t section_index, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate,
    M68kFactsV2TraceState *out_state) {
  enum { BACKWARD_SLICE_LIMIT = 48 };
  const M68kDecodeCandidate *previous[BACKWARD_SLICE_LIMIT];
  const M68kDecodeCandidate *cursor_candidate;
  uint32_t cursor;
  size_t count = 0U;
  size_t index;
  if (out_state != NULL) trace_state_init_unknown(out_state);
  if (relocation_lookup == NULL || runtime_addresses == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || section == NULL || site_candidate == NULL || out_state == NULL ||
      accepted_start[section_index] == NULL || accepted_bytes[section_index] == NULL) {
    return 0;
  }
  cursor = site_candidate->offset;
  while (count < BACKWARD_SLICE_LIMIT) {
    cursor_candidate = find_accepted_candidate_ending_at(section, accepted_start[section_index], cursor);
    if (cursor_candidate == NULL) break;
    previous[count++] = cursor_candidate;
    if (cursor_candidate->offset == 0U || !candidate_has_normal_fallthrough(cursor_candidate) ||
        candidate_has_decoded_direct_control_target(cursor_candidate)) {
      break;
    }
    cursor = cursor_candidate->offset;
  }
  trace_state_init_unknown(out_state);
  for (index = count; index > 0U; --index) {
    const M68kDecodeCandidate *candidate = previous[index - 1U];
    M68kFactsV2TraceState next_state;
    trace_state_after_candidate(section_index, section, candidate, out_state, relocation_lookup, NULL,
      runtime_addresses, accepted_start[section_index], accepted_bytes[section_index], &next_state);
    *out_state = next_state;
  }
  return count != 0U;
}

static int enqueue_callback_field_indirect_targets(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, const M68kRuntimeAddressSpace *runtime_addresses,
    const M68kFactsV2RelocationLookup *relocation_lookup,
    const M68kFactsV2CallbackFieldTargets *targets, size_t section_index,
    const M68kDecodeCandidate *site_candidate) {
  const M68kDecodeSectionIR *section;
  const M68kDecodeCandidate *load_candidate;
  M68kFactsV2TraceState site_state;
  uint8_t control_reg = 0U;
  uint8_t base_reg = 0U;
  int32_t displacement = 0;
  size_t index;
  size_t matched_count = 0U;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || runtime_addresses == NULL || relocation_lookup == NULL || targets == NULL ||
      site_candidate == NULL || section_index >= decode->section_count ||
      !candidate_indirect_control_base_register(site_candidate, &control_reg)) {
    return 0;
  }
  section = &decode->sections[section_index];
  load_candidate = find_accepted_candidate_ending_at(section, accepted_start[section_index],
    site_candidate->offset);
  if (!candidate_loads_callback_field_to_control_register(load_candidate, control_reg, &base_reg,
      &displacement)) {
    return 0;
  }
  for (index = 0U; index < targets->count; ++index) {
    const M68kFactsV2CallbackFieldTarget *target = &targets->items[index];
    if (target->section_index == section_index && target->base_reg == base_reg &&
        target->displacement == displacement) {
      ++matched_count;
    }
  }
  if (matched_count < 2U) return 0;
  (void)trace_callback_site_linear_state(relocation_lookup, runtime_addresses, accepted_start, accepted_bytes,
    section_index, section, site_candidate, &site_state);
  for (index = 0U; index < targets->count; ++index) {
    const M68kFactsV2CallbackFieldTarget *target = &targets->items[index];
    if (target->section_index != section_index || target->base_reg != base_reg ||
        target->displacement != displacement) {
      continue;
    }
    if (enqueue_same_section_control_trace_target(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, section_index, site_candidate, &target->target,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, runtime_addresses, &site_state) != 0) {
      return -1;
    }
  }
  return 0;
}

static int seed_callback_field_indirect_targets(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kFactsV2WorkQueue *queue,
    const M68kRuntimeAddressSpace *runtime_addresses, Arena *scratch_arena,
    uint8_t **accepted_start, uint8_t **accepted_bytes, M68kFactsV2Profile *profile,
    uint8_t max_cpu, uint32_t *out_seeded_count) {
  ArenaMark mark;
  M68kFactsV2CallbackFieldTargets targets;
  size_t section_index;
  size_t before_queue_cursor;
  if (out_seeded_count != NULL) *out_seeded_count = 0U;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || queue == NULL ||
      runtime_addresses == NULL || scratch_arena == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || profile == NULL) {
    return -1;
  }
  before_queue_cursor = (uint32_t)queue->count;
  mark = arena_mark(scratch_arena);
  if (collect_callback_field_targets_for_accepted(decode, relocation_lookup, runtime_addresses,
      scratch_arena, accepted_start, accepted_bytes, max_cpu, &targets) != 0) {
    arena_rewind(scratch_arena, mark);
    return -1;
  }
  if (targets.count == 0U) {
    arena_rewind(scratch_arena, mark);
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      if (candidate->offset >= section->size || !accepted_start[section_index][candidate->offset]) continue;
      if (candidate_has_decoded_direct_control_target(candidate)) continue;
      if (enqueue_callback_field_indirect_targets(decode, facts, queue, accepted_start, accepted_bytes,
          profile, max_cpu, runtime_addresses, relocation_lookup, &targets, section_index, candidate) != 0) {
        arena_rewind(scratch_arena, mark);
        return -1;
      }
    }
  }
  if (out_seeded_count != NULL && queue->count > before_queue_cursor)
    *out_seeded_count = (uint32_t)(queue->count - before_queue_cursor);
  arena_rewind(scratch_arena, mark);
  return 0;
}

static int enqueue_backward_sliced_indirect_table_targets(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kFactsV2WorkQueue *queue,
    uint8_t **accepted_start, uint8_t **accepted_bytes, M68kFactsV2Profile *profile,
    uint8_t max_cpu, size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *site_candidate, const M68kRuntimeAddressSpace *runtime_addresses) {
  enum { BACKWARD_SLICE_LIMIT = 6 };
  const M68kDecodeCandidate *previous[BACKWARD_SLICE_LIMIT];
  const M68kDecodeCandidate *cursor_candidate;
  M68kFactsV2TraceState state;
  M68kFactsV2TraceValue targets;
  M68kFactsV2TableBaseRef base_ref;
  uint32_t cursor;
  uint8_t control_reg = 0U;
  size_t count = 0U;
  size_t candidate_index;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || section == NULL || site_candidate == NULL || runtime_addresses == NULL ||
      !candidate_indirect_control_address_register(site_candidate, &control_reg)) {
    return 0;
  }
  cursor = site_candidate->offset;
  while (count < BACKWARD_SLICE_LIMIT) {
    cursor_candidate = find_accepted_candidate_ending_at(section, accepted_start[section_index], cursor);
    if (cursor_candidate == NULL) break;
    previous[count++] = cursor_candidate;
    cursor = cursor_candidate->offset;
    if (cursor == 0U) break;
  }
  if (count == 0U) return 0;
  for (candidate_index = 0U; candidate_index < count; ++candidate_index) {
    size_t replay_index;
    size_t gap_index;
    uint8_t dest_reg = 0U;
    uint8_t gap_preserves_control_reg = 1U;
    for (gap_index = 0U; gap_index < candidate_index; ++gap_index) {
      const M68kDecodeCandidate *gap_candidate = previous[gap_index];
      if (!candidate_has_normal_fallthrough(gap_candidate) ||
          candidate_clobbers_address_register(gap_candidate, control_reg)) {
        gap_preserves_control_reg = 0U;
        break;
      }
    }
    if (!gap_preserves_control_reg) break;
    trace_state_init_unknown(&state);
    for (replay_index = count; replay_index > candidate_index + 1U; --replay_index) {
      const M68kDecodeCandidate *candidate = previous[replay_index - 1U];
      M68kFactsV2TraceState next_state;
      trace_state_after_candidate(section_index, section, candidate, &state, relocation_lookup, facts,
        runtime_addresses, accepted_start[section_index], accepted_bytes[section_index], &next_state);
      state = next_state;
    }
    trace_value_set_unknown(&targets);
    memset(&base_ref, 0, sizeof(base_ref));
    cursor_candidate = previous[candidate_index];
    if (trace_state_candidate_loads_long_target_table(section, cursor_candidate, &state, runtime_addresses,
        accepted_bytes[section_index], &dest_reg, &targets, &base_ref) && dest_reg == control_reg) {
      if (append_indirect_table_base_runtime_ref(facts, section_index, &base_ref) != 0) return -1;
      return enqueue_target_set_for_indirect_site(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, section_index, site_candidate, &targets, runtime_addresses, section);
    }
    if (trace_state_candidate_adds_word_target_table(section, cursor_candidate, &state, runtime_addresses,
        accepted_start[section_index], accepted_bytes[section_index], &dest_reg, &targets) &&
        dest_reg == control_reg) {
      return enqueue_target_set_for_indirect_site(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, section_index, site_candidate, &targets, runtime_addresses, section);
    }
  }
  return 0;
}

static int append_indirect_table_base_runtime_ref(M68kFactIR *facts, size_t section_index,
    const M68kFactsV2TableBaseRef *base_ref) {
  int ref_result;
  if (facts == NULL || base_ref == NULL || !base_ref->valid || !base_ref->has_origin ||
      base_ref->origin_section_index != section_index) {
    return 0;
  }
  ref_result = append_runtime_address_ref_fact(facts, section_index, base_ref->origin_offset,
    base_ref->origin_operand_index, base_ref->table_offset, base_ref->base_runtime_address,
    M68K_FACT_CONFIDENCE_TOOL_INFERRED);
  if (ref_result < 0) return -1;
  if (ref_result == 0) return 0;
  if (append_xref_fact(facts, section_index, base_ref->origin_offset, base_ref->table_offset,
      M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
    return -1;
  }
  if (m68k_fact_ir_require_label(facts, section_index, base_ref->table_offset,
      M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
    return -1;
  }
  return 0;
}

static int append_backward_sliced_indirect_table_targets_for_accepted(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kFactsV2WorkQueue *queue,
    uint8_t **accepted_start, uint8_t **accepted_bytes, M68kFactsV2Profile *profile,
    uint8_t max_cpu, const M68kRuntimeAddressSpace *runtime_addresses) {
  size_t section_index;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || queue == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || profile == NULL || runtime_addresses == NULL) {
    return -1;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      if (candidate->offset >= section->size || accepted_start[section_index][candidate->offset] == 0U)
        continue;
      if (candidate_has_decoded_direct_control_target(candidate)) continue;
      if (enqueue_backward_sliced_indirect_table_targets(decode, facts, relocation_lookup, queue, accepted_start,
          accepted_bytes, profile, max_cpu, section_index, section, candidate, runtime_addresses) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int enqueue_relocated_control_target(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kFactsV2WorkQueue *queue,
    uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t source_section_index,
    const M68kDecodeCandidate *candidate) {
  uint32_t offset;
  uint32_t end;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || candidate == NULL || !candidate_is_absolute_control_transfer(candidate)) {
    return 0;
  }
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset + 2U; offset < end; ++offset) {
    const M68kFact *relocation = relocation_lookup_ref_at(relocation_lookup, facts, source_section_index, offset);
    const M68kDecodeSectionIR *target_section;
    const M68kDecodeCandidate *target_candidate = NULL;
    if (relocation == NULL) continue;
    if (relocation->target_section_index >= decode->section_count) continue;
    target_section = &decode->sections[relocation->target_section_index];
    if (target_section->kind != M68K_SECTION_CODE) continue;
    if (relocation->target_offset >= target_section->size || (relocation->target_offset & 1U) != 0U) continue;
    if (accepted_start[relocation->target_section_index][relocation->target_offset]) continue;
    if (accepted_offset_is_interior(target_section, accepted_start[relocation->target_section_index],
        accepted_bytes[relocation->target_section_index], relocation->target_offset)) {
      if (append_violation_fact(facts, source_section_index, candidate->offset, relocation->target_offset) != 0)
        return -1;
      continue;
    }
    if (m68k_decode_ir_ensure_candidate_at(decode, relocation->target_section_index, relocation->target_offset,
        max_cpu, &target_candidate, m68k_diag_sink(NULL)) != 0) return -1;
    if (target_candidate == NULL) continue;
    if (append_cross_section_xref_fact(facts, source_section_index, candidate->offset,
        relocation->target_section_index, relocation->target_offset, M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0)
      return -1;
    if (enqueue_code_start(facts, queue, profile, relocation->target_section_index, relocation->target_offset,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
        source_section_index, candidate->offset) != 0) return -1;
  }
  return 0;
}

static int candidate_is_nonfallthrough_jump_template(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  return metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_JUMP && metadata->flow_conditional == 0U;
}

static int candidate_relocated_jump_template_target(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, uint8_t **accepted_start, uint8_t **accepted_bytes,
    uint8_t max_cpu, size_t section_index, const M68kDecodeCandidate *candidate,
    size_t *out_target_section_index, uint32_t *out_target_offset) {
  uint32_t cursor;
  uint32_t end;
  if (out_target_section_index != NULL) *out_target_section_index = 0U;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || candidate == NULL ||
      out_target_section_index == NULL || out_target_offset == NULL || section_index >= decode->section_count ||
      candidate->byte_count > UINT32_MAX - candidate->offset || !candidate_is_nonfallthrough_jump_template(candidate)) {
    return 0;
  }
  end = candidate->offset + candidate->byte_count;
  for (cursor = candidate->offset; cursor < end; ++cursor) {
    const M68kFact *relocation = relocation_lookup_ref_at(relocation_lookup, facts, section_index, cursor);
    const M68kDecodeSectionIR *target_section;
    const M68kDecodeCandidate *target_candidate = NULL;
    if (relocation == NULL || relocation->size != 4U || relocation->target_section_index >= decode->section_count)
      continue;
    target_section = &decode->sections[relocation->target_section_index];
    if (target_section->kind != M68K_SECTION_CODE ||
        relocation->target_offset >= target_section->size || (relocation->target_offset & 1U) != 0U) {
      continue;
    }
    if (accepted_start != NULL && accepted_bytes != NULL &&
        accepted_start[relocation->target_section_index] != NULL &&
        accepted_bytes[relocation->target_section_index] != NULL &&
        accepted_offset_is_interior(target_section, accepted_start[relocation->target_section_index],
          accepted_bytes[relocation->target_section_index], relocation->target_offset)) {
      continue;
    }
    if (m68k_decode_ir_ensure_candidate_at(decode, relocation->target_section_index, relocation->target_offset,
        max_cpu, &target_candidate, m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (target_candidate == NULL) continue;
    *out_target_section_index = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    return 1;
  }
  return 0;
}

static int relocation_ref_is_valid_jump_template(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, uint8_t **accepted_start, uint8_t **accepted_bytes,
    uint8_t max_cpu, const M68kFact *relocation, const M68kDecodeCandidate **out_candidate,
    size_t *out_target_section_index, uint32_t *out_target_offset) {
  const M68kDecodeSectionIR *section;
  uint32_t lower;
  uint32_t start;
  uint32_t fixup_end;
  if (out_candidate != NULL) *out_candidate = NULL;
  if (out_target_section_index != NULL) *out_target_section_index = 0U;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || relocation == NULL || out_candidate == NULL ||
      relocation->kind != M68K_FACT_RELOCATION_REF || relocation->section_index >= decode->section_count ||
      relocation->size == 0U || relocation->offset > UINT32_MAX - relocation->size) {
    return 0;
  }
  section = &decode->sections[relocation->section_index];
  fixup_end = relocation->offset + relocation->size;
  if (relocation->offset >= section->size || fixup_end > section->size ||
      accepted_start[relocation->section_index] == NULL || accepted_bytes[relocation->section_index] == NULL) {
    return 0;
  }
  lower = relocation->offset > M68K_STATEMENT_SOURCE_BYTES_MAX
    ? relocation->offset - M68K_STATEMENT_SOURCE_BYTES_MAX
    : 0U;
  for (start = lower; start <= relocation->offset; ++start) {
    const M68kDecodeCandidate *candidate = NULL;
    size_t target_section_index = 0U;
    uint32_t target_offset = 0U;
    int target_result;
    if (m68k_decode_ir_ensure_candidate_at(decode, relocation->section_index, start, max_cpu,
        &candidate, m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (candidate == NULL || candidate->offset > relocation->offset ||
        candidate->byte_count < relocation->size || candidate->offset > UINT32_MAX - candidate->byte_count ||
        candidate->offset + candidate->byte_count < fixup_end ||
        accepted_range_has_code_byte_local(accepted_bytes[relocation->section_index], section->size,
          candidate->offset, candidate->byte_count) ||
        accepted_offset_is_interior(section, accepted_start[relocation->section_index],
          accepted_bytes[relocation->section_index], candidate->offset)) {
      continue;
    }
    target_result = candidate_relocated_jump_template_target(decode, facts, relocation_lookup, accepted_start,
      accepted_bytes, max_cpu, relocation->section_index, candidate, &target_section_index, &target_offset);
    if (target_result < 0) return -1;
    if (target_result == 0) continue;
    *out_candidate = candidate;
    if (out_target_section_index != NULL) *out_target_section_index = target_section_index;
    if (out_target_offset != NULL) *out_target_offset = target_offset;
    return 1;
  }
  return 0;
}

static int candidate_has_nearby_relocated_jump_template(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, uint8_t **accepted_start, uint8_t **accepted_bytes,
    uint8_t max_cpu, size_t section_index, const M68kDecodeCandidate *candidate) {
  const uint32_t scan_window = 128U;
  size_t fact_index;
  uint32_t lower;
  uint32_t upper;
  if (facts == NULL || candidate == NULL) return 0;
  lower = candidate->offset > scan_window ? candidate->offset - scan_window : 0U;
  upper = candidate->offset <= UINT32_MAX - scan_window ? candidate->offset + scan_window : UINT32_MAX;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *relocation = &facts->facts[fact_index];
    const M68kDecodeCandidate *other = NULL;
    int valid;
    if (relocation->kind != M68K_FACT_RELOCATION_REF || relocation->section_index != section_index ||
        relocation->offset < lower || relocation->offset > upper) {
      continue;
    }
    valid = relocation_ref_is_valid_jump_template(decode, facts, relocation_lookup, accepted_start,
      accepted_bytes, max_cpu, relocation, &other, NULL, NULL);
    if (valid < 0) return -1;
    if (valid == 0 || other == NULL || other->offset == candidate->offset) continue;
    return 1;
  }
  return 0;
}

static int seed_relocation_backed_jump_template_tables(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kFactsV2WorkQueue *queue,
    uint8_t **accepted_start, uint8_t **accepted_bytes, M68kFactsV2Profile *profile, uint8_t max_cpu) {
  size_t fact_index;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || queue == NULL ||
      accepted_start == NULL || accepted_bytes == NULL || profile == NULL) {
    return -1;
  }
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *relocation = &facts->facts[fact_index];
    const M68kDecodeCandidate *candidate = NULL;
    size_t target_section_index = 0U;
    uint32_t target_offset = 0U;
    int valid;
    valid = relocation_ref_is_valid_jump_template(decode, facts, relocation_lookup, accepted_start,
      accepted_bytes, max_cpu, relocation, &candidate, &target_section_index, &target_offset);
    if (valid < 0) return -1;
    if (valid == 0 || candidate == NULL) continue;
    if (accepted_start[relocation->section_index][candidate->offset]) continue;
    valid = candidate_has_nearby_relocated_jump_template(decode, facts, relocation_lookup, accepted_start,
      accepted_bytes, max_cpu, relocation->section_index, candidate);
    if (valid < 0) return -1;
    if (valid == 0) continue;
    if (enqueue_code_start(facts, queue, profile, relocation->section_index, candidate->offset,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
        relocation->section_index, candidate->offset) != 0) {
      return -1;
    }
    if (target_section_index < decode->section_count && target_offset < decode->sections[target_section_index].size &&
        accepted_start[target_section_index] != NULL && !accepted_start[target_section_index][target_offset] &&
        !accepted_offset_is_interior(&decode->sections[target_section_index], accepted_start[target_section_index],
          accepted_bytes[target_section_index], target_offset) &&
        enqueue_code_start(facts, queue, profile, target_section_index, target_offset,
          M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
          relocation->section_index, candidate->offset) != 0) {
      return -1;
    }
  }
  return 0;
}

static int relocation_ref_is_code_pointer_table_entry(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, uint8_t **accepted_start, uint8_t **accepted_bytes,
    uint8_t max_cpu, size_t section_index, uint32_t offset, const M68kFact **out_relocation) {
  const M68kFact *relocation;
  const M68kDecodeSectionIR *target_section;
  const M68kDecodeCandidate *target_candidate = NULL;
  if (out_relocation != NULL) *out_relocation = NULL;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || section_index >= decode->section_count || offset > UINT32_MAX - 4U ||
      accepted_bytes[section_index] == NULL ||
      accepted_range_has_code_byte_local(accepted_bytes[section_index], decode->sections[section_index].size,
        offset, 4U)) {
    return 0;
  }
  relocation = relocation_lookup_ref_at(relocation_lookup, facts, section_index, offset);
  if (relocation == NULL || relocation->kind != M68K_FACT_RELOCATION_REF || relocation->size != 4U ||
      relocation->target_section_index >= decode->section_count) {
    return 0;
  }
  target_section = &decode->sections[relocation->target_section_index];
  if (target_section->kind != M68K_SECTION_CODE || relocation->target_offset >= target_section->size ||
      (relocation->target_offset & 1U) != 0U || accepted_start[relocation->target_section_index] == NULL ||
      accepted_bytes[relocation->target_section_index] == NULL ||
      accepted_offset_is_interior(target_section, accepted_start[relocation->target_section_index],
        accepted_bytes[relocation->target_section_index], relocation->target_offset)) {
    return 0;
  }
  if (m68k_decode_ir_ensure_candidate_at(decode, relocation->target_section_index, relocation->target_offset,
      max_cpu, &target_candidate, m68k_diag_sink(NULL)) != 0) {
    return -1;
  }
  if (target_candidate == NULL) return 0;
  if (out_relocation != NULL) *out_relocation = relocation;
  return 1;
}

static int seed_relocation_backed_function_pointer_tables(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kFactsV2WorkQueue *queue,
    uint8_t **accepted_start, uint8_t **accepted_bytes, M68kFactsV2Profile *profile, uint8_t max_cpu,
    uint32_t *out_promoted_count) {
  size_t section_index;
  uint32_t promoted_count = 0U;
  if (out_promoted_count != NULL) *out_promoted_count = 0U;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || queue == NULL ||
      accepted_start == NULL || accepted_bytes == NULL || profile == NULL) {
    return -1;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    uint32_t offset = 0U;
    while (offset + 8U <= section->size) {
      const M68kFact *entries[64];
      uint32_t entry_count = 0U;
      uint32_t cursor = offset;
      while (entry_count < (uint32_t)(sizeof(entries) / sizeof(entries[0])) && cursor + 4U <= section->size) {
        const M68kFact *relocation = NULL;
        int valid = relocation_ref_is_code_pointer_table_entry(decode, facts, relocation_lookup, accepted_start,
          accepted_bytes, max_cpu, section_index, cursor, &relocation);
        if (valid < 0) return -1;
        if (valid == 0 || relocation == NULL) break;
        entries[entry_count++] = relocation;
        cursor += 4U;
      }
      if (entry_count >= 2U) {
        uint32_t entry_index;
        for (entry_index = 0U; entry_index < entry_count; ++entry_index) {
          const M68kFact *relocation = entries[entry_index];
          uint32_t prior_index;
          uint8_t target_already_seen = 0U;
          if (append_cross_section_xref_fact(facts, section_index, relocation->offset,
              relocation->target_section_index, relocation->target_offset,
              M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
            return -1;
          }
          if (accepted_start[relocation->target_section_index][relocation->target_offset]) continue;
          for (prior_index = 0U; prior_index < entry_index; ++prior_index) {
            const M68kFact *prior = entries[prior_index];
            if (prior->target_section_index == relocation->target_section_index &&
                prior->target_offset == relocation->target_offset) {
              target_already_seen = 1U;
              break;
            }
          }
          if (target_already_seen) continue;
          if (enqueue_code_start(facts, queue, profile, relocation->target_section_index,
              relocation->target_offset, M68K_FACT_CONFIDENCE_TOOL_INFERRED,
              M68K_FACT_CODE_START_REASON_CONTROL_TARGET, section_index, relocation->offset) != 0) {
            return -1;
          }
          ++promoted_count;
        }
        offset = cursor;
      } else {
        offset += 2U;
      }
    }
  }
  if (out_promoted_count != NULL) *out_promoted_count = promoted_count;
  return 0;
}

static int append_relocation_anchor_fact(M68kFactIR *facts, const M68kFixup *fixup,
    const M68kFactsV2RelocationFailure *anchor) {
  M68kFact fact;
  if (facts == NULL || fixup == NULL || anchor == NULL) return -1;
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RELOCATION_ANCHOR;
  fact.confidence = M68K_FACT_CONFIDENCE_REQUIRED;
  fact.section_index = fixup->section_index;
  fact.offset = fixup->offset;
  fact.target_section_index = fixup->target_section_index;
  fact.target_offset = anchor->raw_value;
  fact.target_addend = anchor->computed_target;
  fact.size = fixup_width_bytes_local(fixup);
  fact.platform_record_kind = anchor->platform_record_kind;
  fact.anchor_kind = anchor->anchor_kind;
  return m68k_fact_ir_append(facts, &fact);
}

static int mark_accepted_bytes(uint8_t *accepted_bytes, const M68kDecodeCandidate *candidate,
    uint32_t section_size) {
  uint32_t index;
  if (accepted_bytes == NULL || candidate == NULL || candidate->offset + candidate->byte_count > section_size)
    return -1;
  for (index = 0U; index < candidate->byte_count; ++index) accepted_bytes[candidate->offset + index] = 1U;
  return 0;
}

static int candidate_overlaps_accepted_bytes(const uint8_t *accepted_bytes,
    const M68kDecodeCandidate *candidate, uint32_t section_size) {
  uint32_t index;
  if (accepted_bytes == NULL || candidate == NULL || candidate->offset + candidate->byte_count > section_size)
    return 1;
  for (index = 0U; index < candidate->byte_count; ++index) {
    if (accepted_bytes[candidate->offset + index] != 0U) return 1;
  }
  return 0;
}

static const M68kFact *find_accepted_code_fact(const M68kFactIR *facts, size_t section_index,
    uint32_t offset) {
  size_t fact_index;
  if (facts == NULL) return NULL;
  for (fact_index = facts->fact_count; fact_index > 0U; --fact_index) {
    const M68kFact *fact = &facts->facts[fact_index - 1U];
    if (fact->kind == M68K_FACT_CODE_ACCEPTED && fact->section_index == section_index &&
        fact->offset == offset) {
      return fact;
    }
  }
  return NULL;
}

static void clear_accepted_candidate(uint8_t *accepted_start, uint8_t *accepted_bytes,
    const M68kDecodeCandidate *candidate, uint32_t *accepted_count) {
  uint32_t byte_index;
  if (accepted_start == NULL || accepted_bytes == NULL || candidate == NULL) return;
  if (!accepted_start[candidate->offset]) return;
  accepted_start[candidate->offset] = 0U;
  for (byte_index = 0U; byte_index < candidate->byte_count; ++byte_index)
    accepted_bytes[candidate->offset + byte_index] = 0U;
  if (accepted_count != NULL && *accepted_count != 0U) --*accepted_count;
}

static int fallthrough_candidate_should_replace_overlap(const M68kFactIR *facts,
    const M68kFactsV2WorkItem *item, const M68kDecodeCandidate *candidate,
    const M68kDecodeCandidate *existing) {
  const M68kFact *existing_fact;
  if (facts == NULL || item == NULL || candidate == NULL || existing == NULL) return 0;
  if (item->reason != M68K_FACT_CODE_START_REASON_FALLTHROUGH) return 0;
  if (candidate->offset >= existing->offset) return 0;
  if (candidate->target_cpu > existing->target_cpu) return 0;
  existing_fact = find_accepted_code_fact(facts, item->section_index, existing->offset);
  if (existing_fact == NULL) return 0;
  if (existing_fact->confidence >= M68K_FACT_CONFIDENCE_REQUIRED) return 0;
  return existing_fact->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET;
}

static int replace_overlapping_inferred_targets_if_preferred(M68kFactIR *facts,
    const M68kFactsV2WorkItem *item, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint8_t **accepted_start, uint8_t **accepted_bytes,
    uint32_t *accepted_count) {
  uint32_t offset;
  uint32_t end;
  int replaced = 0;
  if (facts == NULL || item == NULL || section == NULL || candidate == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || accepted_count == NULL) {
    return 0;
  }
  if (candidate->offset > section->size || candidate->byte_count > section->size - candidate->offset)
    return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset; offset < end; ++offset) {
    const M68kDecodeCandidate *existing;
    if (accepted_start[item->section_index][offset] == 0U) continue;
    existing = m68k_decode_ir_find_candidate_at_offset(section, offset);
    if (existing == NULL) return 0;
    if (!fallthrough_candidate_should_replace_overlap(facts, item, candidate, existing)) return 0;
  }
  for (offset = candidate->offset; offset < end; ++offset) {
    const M68kDecodeCandidate *existing;
    if (accepted_start[item->section_index][offset] == 0U) continue;
    existing = m68k_decode_ir_find_candidate_at_offset(section, offset);
    if (existing == NULL) return -1;
    clear_accepted_candidate(accepted_start[item->section_index], accepted_bytes[item->section_index],
      existing, accepted_count);
    replaced = 1;
  }
  return replaced;
}

static int rebuild_accepted_bytes_from_starts(const M68kDecodeIR *decode, uint8_t **accepted_start,
    uint8_t **accepted_bytes, uint32_t *out_accepted_count) {
  size_t section_index;
  uint32_t accepted_count = 0U;
  if (decode == NULL || accepted_start == NULL || accepted_bytes == NULL || out_accepted_count == NULL)
    return -1;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    if (accepted_bytes[section_index] == NULL || accepted_start[section_index] == NULL) return -1;
    memset(accepted_bytes[section_index], 0, section->size);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      if (!accepted_start[section_index][candidate->offset]) continue;
      if (candidate_overlaps_accepted_bytes(accepted_bytes[section_index], candidate, section->size)) return -1;
      if (mark_accepted_bytes(accepted_bytes[section_index], candidate, section->size) != 0) return -1;
      ++accepted_count;
    }
  }
  *out_accepted_count = accepted_count;
  return 0;
}

static int candidate_reencodes_exactly(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  M68kIrEncodeResult encoded;
  uint8_t encoded_bytes[32];
  if (section == NULL || candidate == NULL || candidate->byte_count > sizeof(encoded_bytes)) return 0;
  if (candidate->offset > section->size || candidate->byte_count > section->size - candidate->offset) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  encoded = m68k_ir_encode_one(&instruction, encoded_bytes, sizeof(encoded_bytes), m68k_diag_sink(NULL));
  return encoded.byte_count == candidate->byte_count &&
    memcmp(encoded_bytes, section->data + candidate->offset, candidate->byte_count) == 0;
}

static int operand_has_reserved_full_extension(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  if (operand->full_ext_base_disp_size != M68K_ASM_FULL_EXT_BD_RESERVED) return 0;
  if (operand->full_ext_base_suppress == 0U && operand->full_ext_index_suppress == 0U &&
      operand->full_ext_outer_disp_size == 0U && operand->full_ext_iis == 0U) {
    return 0;
  }
  return facts_v2_asm_operand_is_indexed_or_pc_indexed(operand);
}

static int candidate_has_reserved_full_extension(const M68kDecodeCandidate *candidate) {
  size_t operand_index;
  if (candidate == NULL) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
    if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA &&
        candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_BF_EA) {
      continue;
    }
    if (operand_has_reserved_full_extension(&candidate->operands[operand_index])) return 1;
  }
  return 0;
}

static void facts_v2_record_required_instruction_failure(M68kFactsV2Profile *profile,
    const M68kFactsV2WorkItem *item) {
  if (profile == NULL || item == NULL) return;
  if (profile->required_instruction_failures == 0U) {
    profile->first_required_instruction_failure_section = (uint32_t)item->section_index;
    profile->first_required_instruction_failure_offset = item->offset;
    profile->first_required_instruction_failure_reason = item->reason;
    profile->first_required_instruction_failure_source_section = (uint32_t)item->source_section_index;
    profile->first_required_instruction_failure_source_offset = item->source_offset;
  }
  ++profile->required_instruction_failures;
}

static int reject_or_demote_unsafe_candidate(M68kFactIR *facts, const M68kFactsV2WorkItem *item,
    M68kFactsV2Profile *profile) {
  if (facts == NULL || item == NULL || profile == NULL) return -1;
  if (append_violation_fact_with_reason(facts, item->section_index, item->offset, item->offset,
      item->reason, item->source_section_index, item->source_offset) != 0) return -1;
  if (item->confidence >= M68K_FACT_CONFIDENCE_REQUIRED) {
    facts_v2_record_required_instruction_failure(profile, item);
    return 0;
  }
  if (profile->unsupported_instruction_demotes == 0U) {
    profile->first_unsupported_instruction_demote_section = (uint32_t)item->section_index;
    profile->first_unsupported_instruction_demote_offset = item->offset;
    profile->first_unsupported_instruction_demote_reason = item->reason;
    profile->first_unsupported_instruction_demote_source_section = (uint32_t)item->source_section_index;
    profile->first_unsupported_instruction_demote_source_offset = item->source_offset;
  }
  ++profile->unsupported_instruction_demotes;
  return 1;
}

static int validate_reachable_candidate_for_acceptance(const M68kAnalysisPolicy *policy, M68kFactIR *facts,
    const M68kFactsV2WorkItem *item, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint8_t **accepted_start, uint8_t **accepted_bytes,
    uint32_t *accepted_count, M68kFactsV2Profile *profile) {
  uint32_t structured_offset = 0U;
  uint32_t invalid_target_offset = 0U;
  int reject_result;
  if (policy_structured_data_overlaps_range(policy, item->section_index, candidate->offset,
      candidate->byte_count, &structured_offset)) {
    if (append_violation_fact(facts, item->section_index, item->offset, structured_offset) != 0) return -1;
    return 1;
  }
  if (candidate_has_invalid_code_target(section, candidate, &invalid_target_offset)) {
    if (append_violation_fact(facts, item->section_index, item->offset, invalid_target_offset) != 0) return -1;
    reject_result = reject_or_demote_unsafe_candidate(facts, item, profile);
    if (reject_result < 0) return -1;
    if (reject_result > 0) return 1;
  }
  if (candidate_has_reserved_full_extension(candidate) || !candidate_reencodes_exactly(section, candidate)) {
    reject_result = reject_or_demote_unsafe_candidate(facts, item, profile);
    if (reject_result < 0) return -1;
    if (reject_result > 0) return 1;
  }
  if (candidate_overlaps_accepted_bytes(accepted_bytes[item->section_index], candidate, section->size)) {
    int replace_result = replace_overlapping_inferred_targets_if_preferred(facts, item, section, candidate,
      accepted_start, accepted_bytes, accepted_count);
    if (replace_result < 0) return -1;
    if (replace_result > 0) return 0;
    reject_result = reject_or_demote_unsafe_candidate(facts, item, profile);
    if (reject_result < 0) return -1;
    if (reject_result > 0) return 1;
  }
  return 0;
}

static uint32_t count_data_spans_and_append_facts(const M68kDecodeIR *decode, uint8_t **accepted_bytes,
    M68kFactIR *facts) {
  size_t section_index;
  uint32_t span_count = 0U;
  if (decode == NULL || accepted_bytes == NULL || facts == NULL) return 0U;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    uint32_t offset = 0U;
    while (offset < section->size) {
      uint32_t start;
      while (offset < section->size && accepted_bytes[section_index][offset]) ++offset;
      if (offset >= section->size) break;
      start = offset;
      while (offset < section->size && !accepted_bytes[section_index][offset]) ++offset;
      {
        M68kFact fact;
        memset(&fact, 0, sizeof(fact));
        fact.kind = M68K_FACT_DATA_SPAN;
        fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
        fact.section_index = section->section_index;
        fact.offset = start;
        fact.size = offset - start;
        if (m68k_fact_ir_append(facts, &fact) != 0) return span_count;
      }
      ++span_count;
    }
  }
  return span_count;
}

static int demote_required_label_conflicts(const M68kDecodeIR *decode,
    const M68kAcceptedCandidateIndex *accepted_index, uint8_t **accepted_start,
    uint8_t **accepted_bytes, M68kFactIR *facts, M68kFactsV2LabelLookup *label_lookup,
    uint32_t *accepted_count, uint32_t *out_interior_conflicts) {
  size_t fact_index;
  uint32_t interior = 0U;
  if (decode == NULL || accepted_index == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      facts == NULL || accepted_count == NULL || out_interior_conflicts == NULL) {
    return -1;
  }
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    const M68kDecodeSectionIR *section;
    const M68kDecodeCandidate *candidate;
    if (fact->kind != M68K_FACT_LABEL_REQUIRED || fact->confidence < M68K_FACT_CONFIDENCE_REQUIRED ||
        fact->section_index >= decode->section_count)
      continue;
    section = &decode->sections[fact->section_index];
    if (!accepted_offset_is_interior(section, accepted_start[fact->section_index],
        accepted_bytes[fact->section_index], fact->offset)) {
      continue;
    }
    candidate = accepted_candidate_index_covering(accepted_index, accepted_start[fact->section_index],
      fact->section_index, fact->offset, 1);
    if (candidate == NULL) continue;
    clear_accepted_candidate(accepted_start[fact->section_index], accepted_bytes[fact->section_index],
      candidate, accepted_count);
    if (label_lookup_create_label(label_lookup, facts, fact->section_index, fact->offset,
        fact->confidence) != 0) return -1;
    if (append_violation_fact(facts, fact->section_index, candidate->offset, fact->offset) != 0) return -1;
    ++interior;
  }
  *out_interior_conflicts = interior;
  return 0;
}

static int demote_opcode_relocation_conflicts(const M68kDecodeIR *decode,
    const M68kAcceptedCandidateIndex *accepted_index, uint8_t **accepted_start,
    uint8_t **accepted_bytes, M68kFactIR *facts, uint32_t *accepted_count, M68kFactsV2Profile *profile) {
  size_t fact_index;
  if (decode == NULL || accepted_index == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      facts == NULL || accepted_count == NULL || profile == NULL) {
    return -1;
  }
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    const M68kDecodeSectionIR *section;
    const M68kDecodeCandidate *candidate;
    uint32_t relocation_end;
    uint32_t offset;
    if (fact->kind != M68K_FACT_RELOCATION_REF || fact->section_index >= decode->section_count) continue;
    if (fact->size == 0U || fact->offset > UINT32_MAX - fact->size) continue;
    section = &decode->sections[fact->section_index];
    relocation_end = fact->offset + fact->size;
    for (offset = fact->offset; offset < relocation_end && offset < section->size; ++offset) {
      uint32_t candidate_end;
      candidate = accepted_candidate_index_covering(accepted_index, accepted_start[fact->section_index],
        fact->section_index, offset, 0);
      if (candidate == NULL || !accepted_start[fact->section_index][candidate->offset]) continue;
      if (candidate->offset < fact->offset && candidate->byte_count <= UINT32_MAX - candidate->offset) {
        candidate_end = candidate->offset + candidate->byte_count;
        if (candidate_end >= relocation_end) continue;
      }
      clear_accepted_candidate(accepted_start[fact->section_index], accepted_bytes[fact->section_index],
        candidate, accepted_count);
      if (append_violation_fact(facts, fact->section_index, candidate->offset, fact->offset) != 0) return -1;
      if (profile->opcode_relocation_conflicts_resolved_by_demote == 0U) {
        profile->first_opcode_relocation_conflict_section = (uint32_t)fact->section_index;
        profile->first_opcode_relocation_conflict_offset = candidate->offset;
        profile->first_opcode_relocation_conflict_aux_offset = fact->offset;
      }
      ++profile->opcode_relocation_conflicts_resolved_by_demote;
    }
  }
  return 0;
}

static int candidate_is_hunk_base_register_anchor(const M68kDecodeCandidate *candidate,
    const M68kFact *fact) {
  uint8_t dest_reg = 0U;
  const M68kAsmOperandValue *source;
  if (candidate == NULL || fact == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) {
    return 0;
  }
  if (fact->size != 4U || fact->offset != candidate->offset + 2U) return 0;
  source = &candidate->operands[0];
  if (source->kind != M68K_ASM_OPERAND_EA || source->ea_mode != 7U || source->ea_reg != 1U)
    return 0;
  if (source->value != fact->target_offset) return 0;
  return operand_is_address_register_direct(&candidate->operands[1], &dest_reg);
}

static uint32_t classify_relocation_anchor_context(const M68kDecodeIR *decode,
    const M68kAcceptedCandidateIndex *accepted_index, uint8_t **accepted_start, uint8_t **accepted_bytes,
    const M68kFact *fact, uint32_t *out_instruction_offset) {
  const M68kDecodeSectionIR *section;
  const M68kDecodeCandidate *candidate;
  if (out_instruction_offset != NULL) *out_instruction_offset = 0U;
  if (decode == NULL || accepted_index == NULL || accepted_start == NULL || accepted_bytes == NULL || fact == NULL ||
      fact->section_index >= decode->section_count) {
    return M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_UNKNOWN;
  }
  section = &decode->sections[fact->section_index];
  candidate = accepted_candidate_index_covering(accepted_index, accepted_start[fact->section_index],
    fact->section_index, fact->offset, 0);
  if (candidate != NULL) {
    if (out_instruction_offset != NULL) *out_instruction_offset = candidate->offset;
    if (candidate_is_hunk_base_register_anchor(candidate, fact))
      return M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_BASE_REGISTER;
    return M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_INSTRUCTION_BYTES;
  }
  if (fact->offset < section->size && accepted_bytes[fact->section_index] != NULL &&
      accepted_bytes[fact->section_index][fact->offset] == 0U) {
    return M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_DATA_PAYLOAD;
  }
  return M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_UNKNOWN;
}

static int classify_relocation_anchor_contexts(const M68kDecodeIR *decode,
    const M68kAcceptedCandidateIndex *accepted_index, uint8_t **accepted_start,
    uint8_t **accepted_bytes, const M68kFactIR *facts, M68kFactsV2Profile *profile) {
  size_t fact_index;
  uint32_t anchor_index = 0U;
  if (decode == NULL || accepted_index == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      facts == NULL || profile == NULL)
    return -1;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    uint32_t instruction_offset = 0U;
    uint32_t context;
    if (fact->kind != M68K_FACT_RELOCATION_ANCHOR) continue;
    context = classify_relocation_anchor_context(decode, accepted_index, accepted_start, accepted_bytes, fact,
      &instruction_offset);
    if (anchor_index == 0U) {
      profile->first_relocation_anchor_context = context;
      profile->first_relocation_anchor_instruction_offset = instruction_offset;
    }
    switch (context) {
      case M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_INSTRUCTION_BYTES:
        ++profile->relocation_anchor_instruction_bytes;
        break;
      case M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_DATA_PAYLOAD:
        ++profile->relocation_anchor_data_payloads;
        ++profile->unassemblable_hunk_data_relocations;
        break;
      case M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_BASE_REGISTER:
        ++profile->unassemblable_hunk_base_register_relocations;
        break;
      default:
        ++profile->relocation_anchor_unknown_contexts;
        break;
    }
    ++anchor_index;
  }
  return 0;
}

static int materialize_safe_required_labels(const M68kDecodeIR *decode, uint8_t **accepted_start,
    uint8_t **accepted_bytes, M68kFactIR *facts, M68kFactsV2LabelLookup *label_lookup) {
  size_t fact_index;
  if (decode == NULL || accepted_start == NULL || accepted_bytes == NULL || facts == NULL) return -1;
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    const M68kDecodeSectionIR *section;
    uint32_t extent;
    if (fact->kind != M68K_FACT_LABEL_REQUIRED || fact->section_index >= decode->section_count) continue;
    section = &decode->sections[fact->section_index];
    extent = decode_section_extent_local(section);
    if (fact->offset > extent) continue;
    if (accepted_offset_is_interior(section, accepted_start[fact->section_index],
        accepted_bytes[fact->section_index], fact->offset)) {
      continue;
    }
    if (label_lookup_create_label(label_lookup, facts, fact->section_index, fact->offset,
        fact->confidence) != 0) return -1;
  }
  return 0;
}

static int materialize_pc_relative_interior_data_anchors(const M68kDecodeIR *decode,
    const M68kAcceptedCandidateIndex *accepted_index, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactIR *facts, M68kFactsV2LabelLookup *label_lookup) {
  size_t section_index;
  if (decode == NULL || accepted_index == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      facts == NULL || label_lookup == NULL) {
    return -1;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    if (accepted_start[section_index] == NULL || accepted_bytes[section_index] == NULL) return -1;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      size_t target_index;
      if (candidate->offset >= section->size || !accepted_start[section_index][candidate->offset]) continue;
      for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
        const M68kDecodeTarget *target = &candidate->targets[target_index];
        const M68kDecodeCandidate *anchor;
        if (target->kind != M68K_DECODE_TARGET_DATA || !target->has_section ||
            target->section_index != section_index || !target->has_operand ||
            target->operand_index >= candidate->operand_count ||
            (candidate->operand_kinds[target->operand_index] != M68K_ASM_OPERAND_EA &&
              candidate->operand_kinds[target->operand_index] != M68K_ASM_OPERAND_BF_EA) ||
            candidate->operands[target->operand_index].ea_mode != 7U ||
            candidate->operands[target->operand_index].ea_reg != 2U ||
            !accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index],
              target->offset)) {
          continue;
        }
        anchor = accepted_candidate_index_covering(accepted_index, accepted_start[section_index],
          section_index, target->offset, 1);
        if (anchor == NULL || anchor->offset >= target->offset) continue;
        if (label_lookup_create_label(label_lookup, facts, section_index, anchor->offset,
            M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
          return -1;
        }
      }
    }
  }
  return 0;
}

static int labelled_entry_decodes_terminal_api_wrapper(M68kDecodeIR *decode, const M68kDecodeSectionIR *section,
    uint8_t platform_kind, uint8_t **accepted_bytes, uint32_t offset, uint8_t max_cpu) {
  uint32_t cursor = offset;
  uint32_t instruction_count = 0U;
  int has_api_call = 0;
  if (decode == NULL || section == NULL || accepted_bytes == NULL || section->section_index >= decode->section_count ||
      offset >= section->size) {
    return 0;
  }
  while (cursor < section->size && instruction_count < 8U) {
    const M68kDecodeCandidate *candidate = ensure_candidate_at_offset(decode, section, cursor, max_cpu);
    int16_t lvo = 0;
    if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > section->size - cursor)
      return 0;
    if (accepted_range_has_code_byte_local(accepted_bytes[section->section_index], section->size, cursor,
        candidate->byte_count)) {
      return 0;
    }
    ++instruction_count;
    if (candidate_calls_a6_lvo(candidate, &lvo) && platform_facts_v2_lvo_is_api(platform_kind, lvo))
      has_api_call = 1;
    if (!candidate_has_normal_fallthrough(candidate))
      return has_api_call && instruction_count >= 3U;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int candidate_contains_relocation_ref(const M68kFactsV2RelocationLookup *relocation_lookup,
    const M68kFactIR *facts, size_t section_index, const M68kDecodeCandidate *candidate) {
  uint32_t cursor;
  uint32_t end;
  if (relocation_lookup == NULL || facts == NULL || candidate == NULL || candidate->byte_count == 0U ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  end = candidate->offset + candidate->byte_count;
  for (cursor = candidate->offset; cursor < end; ++cursor) {
    const M68kFact *relocation = relocation_lookup_ref_at(relocation_lookup, facts, section_index, cursor);
    if (relocation != NULL && relocation->kind == M68K_FACT_RELOCATION_REF &&
        relocation->offset >= candidate->offset && relocation->size <= end - relocation->offset) {
      return 1;
    }
  }
  return 0;
}

static int boundary_entry_decodes_relocation_backed_terminal_api_wrapper(M68kDecodeIR *decode,
    const M68kDecodeSectionIR *section, const M68kFactsV2RelocationLookup *relocation_lookup,
    const M68kFactIR *facts, uint8_t platform_kind, uint8_t **accepted_bytes, uint32_t offset,
    uint8_t max_cpu) {
  uint32_t cursor = offset;
  uint32_t instruction_count = 0U;
  int has_api_call = 0;
  int has_relocation_ref = 0;
  if (decode == NULL || section == NULL || relocation_lookup == NULL || facts == NULL || accepted_bytes == NULL ||
      section->section_index >= decode->section_count || offset >= section->size) {
    return 0;
  }
  while (cursor < section->size && instruction_count < 8U) {
    const M68kDecodeCandidate *candidate = ensure_candidate_at_offset(decode, section, cursor, max_cpu);
    int16_t lvo = 0;
    if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > section->size - cursor)
      return 0;
    if (accepted_range_has_code_byte_local(accepted_bytes[section->section_index], section->size, cursor,
        candidate->byte_count)) {
      return 0;
    }
    ++instruction_count;
    if (candidate_contains_relocation_ref(relocation_lookup, facts, section->section_index, candidate))
      has_relocation_ref = 1;
    if (candidate_calls_a6_lvo(candidate, &lvo) && platform_facts_v2_lvo_is_api(platform_kind, lvo))
      has_api_call = 1;
    if (!candidate_has_normal_fallthrough(candidate))
      return has_relocation_ref && has_api_call && instruction_count >= 3U;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int seed_linkage_api_entry_labels(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2LabelLookup *label_lookup, M68kFactsV2WorkQueue *queue,
    uint8_t platform_kind, uint8_t **accepted_start, uint8_t **accepted_bytes, M68kFactsV2Profile *profile,
    uint8_t max_cpu, uint32_t *out_seeded) {
  size_t fact_index;
  uint32_t seeded = 0U;
  if (decode == NULL || facts == NULL || label_lookup == NULL || queue == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || out_seeded == NULL) {
    return -1;
  }
  if (!platform_facts_v2_supports_linkage_api_entry_labels(platform_kind)) {
    *out_seeded = 0U;
    return 0;
  }
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    const M68kDecodeSectionIR *section;
    if (fact->kind != M68K_FACT_LABEL_REQUIRED || fact->confidence < M68K_FACT_CONFIDENCE_REQUIRED ||
        fact->section_index >= decode->section_count) {
      continue;
    }
    section = &decode->sections[fact->section_index];
    if (section->kind != M68K_SECTION_CODE || fact->offset >= section->size ||
        accepted_start[fact->section_index][fact->offset] || accepted_bytes[fact->section_index][fact->offset] ||
        !label_lookup_has_label(label_lookup, facts, fact->section_index, fact->offset) ||
        !labelled_entry_decodes_terminal_api_wrapper(decode, section, platform_kind, accepted_bytes, fact->offset,
          max_cpu)) {
      continue;
    }
    if (enqueue_code_start_runtime(facts, queue, profile, fact->section_index, fact->offset,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED,
        M68K_FACT_CODE_START_REASON_LINKAGE_API_ENTRY, fact->section_index, fact->offset, 0U, 0U, NULL) != 0) {
      return -1;
    }
    ++seeded;
  }
  *out_seeded = seeded;
  return 0;
}

static int seed_boundary_api_entries(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kFactsV2WorkQueue *queue,
    uint8_t platform_kind, uint8_t **accepted_start, uint8_t **accepted_bytes, M68kFactsV2Profile *profile,
    uint8_t max_cpu, uint32_t *out_seeded) {
  size_t section_index;
  uint32_t seeded = 0U;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || queue == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || out_seeded == NULL) {
    return -1;
  }
  *out_seeded = 0U;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    uint32_t offset;
    if (section->kind != M68K_SECTION_CODE || accepted_start[section_index] == NULL ||
        accepted_bytes[section_index] == NULL) {
      continue;
    }
    for (offset = 2U; offset < section->size; offset += 2U) {
      if (!accepted_bytes[section_index][offset - 1U] || accepted_start[section_index][offset] ||
          accepted_bytes[section_index][offset] ||
          accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index],
            offset) ||
          !boundary_entry_decodes_relocation_backed_terminal_api_wrapper(decode, section, relocation_lookup, facts,
            platform_kind, accepted_bytes, offset, max_cpu)) {
        continue;
      }
      if (enqueue_code_start(facts, queue, profile, section_index, offset,
          M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_BOUNDARY_API_ENTRY,
          section_index, offset) != 0) {
        return -1;
      }
      ++seeded;
    }
  }
  *out_seeded = seeded;
  return 0;
}

static size_t platform_api_entry_seed_pass_limit(const M68kDecodeIR *decode) {
  size_t section_index;
  size_t limit = 1U;
  if (decode == NULL) return limit;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t section_limit;
    if (section->kind != M68K_SECTION_CODE) continue;
    section_limit = ((size_t)section->size / 2U) + 1U;
    if (section_limit > ((size_t)-1) - limit) return (size_t)-1;
    limit += section_limit;
  }
  return limit;
}

static uint32_t resolve_required_label_invariants(const M68kDecodeIR *decode, uint8_t **accepted_start,
    uint8_t **accepted_bytes, const M68kFactIR *facts, M68kFactIR *out_facts,
    const M68kFactsV2LabelLookup *label_lookup, uint32_t *out_interior_conflicts) {
  size_t fact_index;
  uint32_t unresolved = 0U;
  uint32_t interior = 0U;
  if (decode == NULL || accepted_start == NULL || accepted_bytes == NULL || facts == NULL || out_facts == NULL ||
      out_interior_conflicts == NULL) {
    return 0U;
  }
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    const M68kDecodeSectionIR *section;
    if (fact->kind != M68K_FACT_LABEL_REQUIRED || fact->confidence < M68K_FACT_CONFIDENCE_REQUIRED ||
        fact->section_index >= decode->section_count)
      continue;
    section = &decode->sections[fact->section_index];
    if (label_lookup_has_label(label_lookup, facts, fact->section_index, fact->offset)) continue;
    ++unresolved;
    if (accepted_offset_is_interior(section, accepted_start[fact->section_index],
        accepted_bytes[fact->section_index], fact->offset)) {
      if (append_violation_fact(out_facts, fact->section_index, fact->offset, fact->offset) == 0) ++interior;
    }
  }
  *out_interior_conflicts = interior;
  return unresolved;
}

static int candidate_has_control_target_local(const M68kDecodeCandidate *candidate) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
        target->kind == M68K_DECODE_TARGET_JUMP) {
      return 1;
    }
  }
  return 0;
}

static int candidate_single_direct_nonfallthrough_control_target(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint8_t *out_kind, uint32_t *out_target_offset) {
  size_t target_index;
  const M68kDecodeTarget *direct_target = NULL;
  if (out_kind != NULL) *out_kind = 0U;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (section == NULL || candidate == NULL || candidate->byte_count == 0U ||
      candidate_has_normal_fallthrough(candidate)) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_CALL &&
        target->kind != M68K_DECODE_TARGET_JUMP) {
      continue;
    }
    if (!target->has_section || target->section_index != section->section_index ||
        target->offset >= section->size || (target->offset & 1U) != 0U) {
      return 0;
    }
    if (direct_target != NULL) return 0;
    direct_target = target;
  }
  if (direct_target == NULL) return 0;
  if (out_kind != NULL) *out_kind = direct_target->kind;
  if (out_target_offset != NULL) *out_target_offset = direct_target->offset;
  return 1;
}

static int candidate_matches_direct_control_stub_table_entry(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *anchor, const M68kDecodeCandidate *candidate, uint8_t anchor_target_kind) {
  uint8_t target_kind = 0U;
  if (section == NULL || anchor == NULL || candidate == NULL || candidate->byte_count != anchor->byte_count)
    return 0;
  if (!candidate_single_direct_nonfallthrough_control_target(section, candidate, &target_kind, NULL)) return 0;
  return target_kind == anchor_target_kind;
}

static int candidate_has_relocated_absolute_control_target(const M68kDecodeIR *decode, const M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, uint8_t **accepted_start) {
  uint32_t cursor;
  uint32_t end;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || candidate == NULL ||
      section_index >= decode->section_count || !candidate_is_absolute_control_transfer(candidate) ||
      candidate->byte_count > UINT32_MAX - candidate->offset) {
    return 0;
  }
  end = candidate->offset + candidate->byte_count;
  for (cursor = candidate->offset + 2U; cursor < end; ++cursor) {
    const M68kFact *relocation = relocation_lookup_ref_at(relocation_lookup, facts, section_index, cursor);
    const M68kDecodeSectionIR *target_section;
    if (relocation == NULL || relocation->size != 4U ||
        relocation->target_section_index >= decode->section_count) {
      continue;
    }
    target_section = &decode->sections[relocation->target_section_index];
    if (target_section->kind != M68K_SECTION_CODE ||
        relocation->target_offset >= target_section->size || (relocation->target_offset & 1U) != 0U) {
      continue;
    }
    if (relocation->target_section_index == section_index &&
        (accepted_start == NULL || accepted_start[relocation->target_section_index] == NULL ||
          !accepted_start[relocation->target_section_index][relocation->target_offset])) {
      continue;
    }
    return 1;
  }
  return 0;
}

static int enqueue_adjacent_direct_control_stub_table_entries(M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kFactsV2WorkQueue *queue,
    uint8_t **accepted_start, uint8_t **accepted_bytes, M68kFactsV2Profile *profile, uint8_t max_cpu,
    size_t section_index, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *anchor,
    const M68kRuntimeAddressSpace *runtime_addresses) {
  uint8_t anchor_target_kind = 0U, require_relocated_absolute_target = 0U;
  uint32_t anchor_target_offset = 0U;
  uint32_t stride, direction;
  if (decode == NULL || facts == NULL || relocation_lookup == NULL || queue == NULL ||
      accepted_start == NULL || accepted_bytes == NULL || profile == NULL || section == NULL ||
      anchor == NULL || runtime_addresses == NULL || section_index >= decode->section_count) {
    return -1;
  }
  if (!candidate_single_direct_nonfallthrough_control_target(section, anchor, &anchor_target_kind,
      &anchor_target_offset)) {
    return 0;
  }
  (void)anchor_target_offset;
  if (anchor_target_kind != M68K_DECODE_TARGET_BRANCH) {
    if (anchor_target_kind != M68K_DECODE_TARGET_CALL && anchor_target_kind != M68K_DECODE_TARGET_JUMP) return 0;
    if (!candidate_has_relocated_absolute_control_target(decode, facts, relocation_lookup, section_index,
        anchor, accepted_start)) {
      return 0;
    }
    require_relocated_absolute_target = 1U;
  }
  stride = anchor->byte_count;
  if (stride == 0U) return 0;
  for (direction = 0U; direction < 2U; ++direction) {
    const uint32_t scan_limit = 16U;
    uint32_t cursor = anchor->offset;
    uint32_t scanned;
    for (scanned = 0U; scanned < scan_limit; ++scanned) {
      const M68kDecodeCandidate *candidate = NULL;
      uint32_t entry_runtime = 0U;
      uint8_t has_entry_runtime = 0U;
      if (direction == 0U) {
        if (cursor < stride) break;
        cursor -= stride;
      } else {
        if (cursor > UINT32_MAX - stride) break;
        cursor += stride;
        if (cursor >= section->size) break;
      }
      if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index],
          cursor)) {
        break;
      }
      if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
          m68k_diag_sink(NULL)) != 0) {
        return -1;
      }
      if (candidate == NULL ||
          !candidate_matches_direct_control_stub_table_entry(section, anchor, candidate, anchor_target_kind)) {
        break;
      }
      if (require_relocated_absolute_target &&
          !candidate_has_relocated_absolute_control_target(decode, facts, relocation_lookup, section_index,
            candidate, accepted_start)) {
        break;
      }
      if (accepted_start[section_index][cursor]) continue;
      if (runtime_address_space_source_to_runtime_near(runtime_addresses, section_index, cursor, 0U, 0U,
          &entry_runtime)) {
        has_entry_runtime = 1U;
      }
      if (m68k_fact_ir_require_label(facts, section_index, cursor,
          M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
        return -1;
      }
      if (enqueue_code_start_runtime(facts, queue, profile, section_index, cursor,
          M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
          section_index, anchor->offset, has_entry_runtime, entry_runtime, NULL) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int candidate_indexed_control_table_base_offset(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t *out_table_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (out_table_offset != NULL) *out_table_offset = 0U;
  if (section == NULL || candidate == NULL || out_table_offset == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < instruction.operand_count &&
       operand_index < 4U; ++operand_index) {
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
        metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) {
      continue;
    }
    if (candidate_operand_data_target_offset(candidate, operand_index, section->section_index, out_table_offset))
      return 1;
  }
  return 0;
}

static int indexed_control_operand_base_is_inside_instruction(const M68kDecodeCandidate *candidate,
    uint32_t operand_base_offset) {
  if (candidate == NULL || candidate->byte_count == 0U ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  return operand_base_offset >= candidate->offset &&
    operand_base_offset < candidate->offset + candidate->byte_count;
}

static int indexed_control_post_instruction_table_start(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t operand_base_offset, uint32_t *out_table_offset) {
  uint32_t table_offset;
  if (out_table_offset != NULL) *out_table_offset = 0U;
  if (section == NULL || candidate == NULL || out_table_offset == NULL ||
      !indexed_control_operand_base_is_inside_instruction(candidate, operand_base_offset) ||
      candidate->offset > UINT32_MAX - candidate->byte_count) {
    return 0;
  }
  table_offset = candidate->offset + candidate->byte_count;
  if (table_offset >= section->size) return 0;
  *out_table_offset = table_offset;
  return 1;
}

static int scan_indexed_backward_inline_tail_entries(M68kDecodeIR *decode, uint8_t max_cpu, size_t section_index,
  const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate, uint8_t **accepted_start,
  uint8_t **accepted_bytes, uint32_t *out_entries, uint32_t entry_limit, uint32_t *out_entry_count);
static int scan_indexed_forward_inline_tail_entries(M68kDecodeIR *decode, uint8_t max_cpu, size_t section_index,
  const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate, uint8_t **accepted_start,
  uint8_t **accepted_bytes, uint32_t *out_entries, uint32_t entry_limit, uint32_t *out_entry_count);
static int scan_indexed_forward_branch_terminated_stub_entries(M68kDecodeIR *decode, uint8_t max_cpu,
  size_t section_index, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate,
  uint8_t **accepted_start, uint8_t **accepted_bytes, uint32_t *out_entries, uint32_t entry_limit,
  uint32_t *out_entry_count);

static int enqueue_indexed_direct_control_stub_table_entries(M68kDecodeIR *decode, M68kFactIR *facts,
    M68kFactsV2WorkQueue *queue, uint8_t **accepted_start, uint8_t **accepted_bytes,
    M68kFactsV2Profile *profile, uint8_t max_cpu, size_t section_index, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *site_candidate, const M68kRuntimeAddressSpace *runtime_addresses) {
  const uint32_t scan_limit = 64U;
  uint32_t entries[64];
  uint32_t table_offset = 0U, cursor, stride = 0U;
  uint32_t entry_count = 0U, first_forward_target = UINT32_MAX, entry_index;
  if (decode == NULL || facts == NULL || queue == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      profile == NULL || section == NULL || site_candidate == NULL || runtime_addresses == NULL ||
      section_index >= decode->section_count ||
      !candidate_indexed_control_table_base_offset(section, site_candidate, &table_offset)) {
    return 0;
  }
  if (indexed_control_operand_base_is_inside_instruction(site_candidate, table_offset) &&
      !indexed_control_post_instruction_table_start(section, site_candidate, table_offset, &table_offset)) {
    return 0;
  }
  cursor = table_offset;
  while (cursor < section->size && entry_count < scan_limit) {
    const M68kDecodeCandidate *candidate = NULL;
    uint8_t target_kind = 0U;
    uint32_t target_offset = 0U;
    if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index], cursor))
      break;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (candidate == NULL || !candidate_single_direct_nonfallthrough_control_target(section, candidate,
        &target_kind, &target_offset) || target_kind != M68K_DECODE_TARGET_BRANCH) {
      break;
    }
    if (stride == 0U) {
      stride = candidate->byte_count;
      if (stride == 0U) break;
    } else if (candidate->byte_count != stride) {
      break;
    }
    if (target_offset > table_offset && target_offset < first_forward_target)
      first_forward_target = target_offset;
    entries[entry_count] = cursor;
    ++entry_count;
    if (cursor > UINT32_MAX - stride) break;
    cursor += stride;
    if (entry_count >= 2U && first_forward_target != UINT32_MAX && cursor >= first_forward_target)
      break;
  }
  if (entry_count < 2U || stride == 0U) {
    int scan_result = scan_indexed_backward_inline_tail_entries(decode, max_cpu, section_index, section,
      site_candidate, accepted_start, accepted_bytes, entries, scan_limit, &entry_count);
    if (scan_result < 0) return -1;
    if (scan_result == 0) {
      scan_result = scan_indexed_forward_inline_tail_entries(decode, max_cpu, section_index, section,
        site_candidate, accepted_start, accepted_bytes, entries, scan_limit, &entry_count);
      if (scan_result < 0) return -1;
    }
    if (scan_result == 0) {
      uint32_t post_instruction_table_offset = 0U;
      uint32_t operand_base_offset = 0U;
      if (candidate_indexed_control_table_base_offset(section, site_candidate, &operand_base_offset) &&
          indexed_control_post_instruction_table_start(section, site_candidate, operand_base_offset,
            &post_instruction_table_offset)) {
        scan_result = scan_indexed_direct_variable_stub_entries(decode, max_cpu, section_index, section,
          post_instruction_table_offset, accepted_start, accepted_bytes, entries, scan_limit, &entry_count);
        if (scan_result < 0) return -1;
      }
    }
    if (scan_result == 0) {
      scan_result = scan_indexed_forward_branch_terminated_stub_entries(decode, max_cpu, section_index,
        section, site_candidate, accepted_start, accepted_bytes, entries, scan_limit, &entry_count);
      if (scan_result < 0) return -1;
    }
    if (scan_result == 0) {
      return 0;
    }
  }
  for (entry_index = 0U; entry_index < entry_count; ++entry_index) {
    uint32_t entry_runtime = 0U;
    uint8_t has_entry_runtime = 0U;
    cursor = entries[entry_index];
    if (accepted_start[section_index][cursor]) continue;
    if (runtime_address_space_source_to_runtime_near(runtime_addresses, section_index, cursor, 0U, 0U,
        &entry_runtime)) {
      has_entry_runtime = 1U;
    }
    if (append_xref_fact(facts, section_index, site_candidate->offset, cursor,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) {
      return -1;
    }
    if (m68k_fact_ir_require_label(facts, section_index, cursor, M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0)
      return -1;
    if (enqueue_code_start_runtime(facts, queue, profile, section_index, cursor,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
        section_index, site_candidate->offset, has_entry_runtime, entry_runtime, NULL) != 0) {
      return -1;
    }
  }
  return 0;
}

static int candidate_has_branch_target_in_range(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t start, uint32_t end) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH && target->has_section &&
        target->section_index == section_index &&
        target->offset >= start && target->offset < end) {
      return 1;
    }
  }
  return 0;
}

static int scan_indexed_direct_variable_stub_entries(M68kDecodeIR *decode, uint8_t max_cpu, size_t section_index,
    const M68kDecodeSectionIR *section, uint32_t table_offset, uint8_t **accepted_start, uint8_t **accepted_bytes,
    uint32_t *out_entries, uint32_t entry_limit, uint32_t *out_entry_count) {
  uint32_t cursor;
  uint32_t first_forward_target = UINT32_MAX;
  if (out_entry_count != NULL) *out_entry_count = 0U;
  if (decode == NULL || section == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      out_entries == NULL || out_entry_count == NULL || entry_limit == 0U ||
      section_index >= decode->section_count || table_offset >= section->size) {
    return 0;
  }
  cursor = table_offset;
  while (cursor < section->size && *out_entry_count < entry_limit) {
    const M68kDecodeCandidate *candidate = NULL;
    uint8_t target_kind = 0U;
    uint32_t target_offset = 0U;
    if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index], cursor))
      break;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (candidate == NULL || !candidate_single_direct_nonfallthrough_control_target(section, candidate,
        &target_kind, &target_offset) || target_kind != M68K_DECODE_TARGET_BRANCH ||
        candidate->byte_count == 0U) {
      break;
    }
    if (target_offset > table_offset && target_offset < first_forward_target)
      first_forward_target = target_offset;
    out_entries[(*out_entry_count)++] = cursor;
    if (cursor > UINT32_MAX - candidate->byte_count) break;
    cursor += candidate->byte_count;
    if (*out_entry_count >= 2U && first_forward_target != UINT32_MAX && cursor >= first_forward_target)
      break;
  }
  return *out_entry_count >= 2U;
}

static int scan_indexed_backward_inline_tail_entries(M68kDecodeIR *decode, uint8_t max_cpu, size_t section_index,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate, uint8_t **accepted_start,
    uint8_t **accepted_bytes, uint32_t *out_entries, uint32_t entry_limit, uint32_t *out_entry_count) {
  const uint32_t scan_limit = 64U;
  uint32_t table_offset = 0U;
  uint32_t run_start;
  uint32_t cursor;
  uint32_t stride = 0U;
  uint32_t run_count = 0U;
  const M68kDecodeCandidate *first = NULL;
  const M68kDecodeCandidate *base = NULL;
  if (out_entry_count != NULL) *out_entry_count = 0U;
  if (decode == NULL || section == NULL || site_candidate == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || out_entries == NULL || out_entry_count == NULL || entry_limit == 0U ||
      section_index >= decode->section_count || site_candidate->byte_count == 0U ||
      site_candidate->offset > UINT32_MAX - site_candidate->byte_count ||
      !candidate_indexed_control_table_base_offset(section, site_candidate, &table_offset)) {
    return 0;
  }
  run_start = site_candidate->offset + site_candidate->byte_count;
  if (table_offset <= run_start || table_offset - run_start > scan_limit) return 0;
  if (m68k_decode_ir_ensure_candidate_at(decode, section_index, table_offset, max_cpu, &base,
      m68k_diag_sink(NULL)) != 0) {
    return -1;
  }
  if (base == NULL || !candidate_has_branch_target_in_range(base, section->section_index, run_start,
      table_offset)) {
    return 0;
  }
  if (accepted_range_has_code_byte_local(accepted_bytes[section_index], section->size, table_offset,
      base->byte_count)) {
    return 0;
  }
  cursor = run_start;
  while (cursor < table_offset && run_count < entry_limit) {
    const M68kDecodeCandidate *candidate = NULL;
    if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index], cursor))
      return 0;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (candidate == NULL || candidate->byte_count == 0U || cursor > UINT32_MAX - candidate->byte_count)
      return 0;
    if (accepted_range_has_code_byte_local(accepted_bytes[section_index], section->size, cursor,
        candidate->byte_count)) {
      return 0;
    }
    if (first == NULL) {
      first = candidate;
      stride = candidate->byte_count;
    } else if (candidate->byte_count != stride || candidate->asm_form_index != first->asm_form_index ||
        candidate->disasm_form_index != first->disasm_form_index) {
      return 0;
    }
    ++run_count;
    cursor += candidate->byte_count;
  }
  if (cursor != table_offset || run_count < 2U || stride == 0U || run_count > entry_limit) return 0;
  cursor = run_start + stride;
  *out_entry_count = 0U;
  while (cursor <= table_offset && *out_entry_count < entry_limit) {
    out_entries[(*out_entry_count)++] = cursor;
    if (cursor > UINT32_MAX - stride) break;
    cursor += stride;
  }
  return *out_entry_count >= 2U;
}

static int scan_indexed_forward_inline_tail_entries(M68kDecodeIR *decode, uint8_t max_cpu, size_t section_index,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate, uint8_t **accepted_start,
    uint8_t **accepted_bytes, uint32_t *out_entries, uint32_t entry_limit, uint32_t *out_entry_count) {
  const uint32_t scan_limit = 64U;
  uint32_t table_offset = 0U;
  uint32_t cursor;
  uint32_t stride = 0U;
  uint32_t run_count = 0U;
  const M68kDecodeCandidate *first = NULL;
  if (out_entry_count != NULL) *out_entry_count = 0U;
  if (decode == NULL || section == NULL || site_candidate == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || out_entries == NULL || out_entry_count == NULL || entry_limit == 0U ||
      section_index >= decode->section_count || site_candidate->byte_count == 0U ||
      site_candidate->offset > UINT32_MAX - site_candidate->byte_count ||
      !candidate_indexed_control_table_base_offset(section, site_candidate, &table_offset)) {
    return 0;
  }
  if (table_offset != site_candidate->offset + site_candidate->byte_count || table_offset >= section->size)
    return 0;
  cursor = table_offset;
  *out_entry_count = 0U;
  while (cursor < section->size && cursor - table_offset <= scan_limit && *out_entry_count < entry_limit) {
    const M68kDecodeCandidate *candidate = NULL;
    if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index], cursor))
      return 0;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (candidate == NULL || candidate->byte_count == 0U || cursor > UINT32_MAX - candidate->byte_count)
      return 0;
    if (accepted_range_has_code_byte_local(accepted_bytes[section_index], section->size, cursor,
        candidate->byte_count)) {
      return 0;
    }
    if (candidate_has_branch_target_in_range(candidate, section->section_index, table_offset, cursor)) {
      out_entries[(*out_entry_count)++] = cursor;
      return run_count >= 2U && *out_entry_count >= 2U;
    }
    if (first == NULL) {
      first = candidate;
      stride = candidate->byte_count;
    } else if (candidate->byte_count != stride || candidate->asm_form_index != first->asm_form_index ||
        candidate->disasm_form_index != first->disasm_form_index) {
      return 0;
    }
    if (run_count != 0U) {
      out_entries[(*out_entry_count)++] = cursor;
    }
    ++run_count;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int scan_forward_branch_terminated_stub_entry(M68kDecodeIR *decode, uint8_t max_cpu,
    size_t section_index, const M68kDecodeSectionIR *section, uint8_t **accepted_start,
    uint8_t **accepted_bytes, uint32_t entry_start, uint32_t entry_limit, uint32_t *out_entry_end,
    uint32_t *out_branch_relative_offset, uint32_t *out_target_offset) {
  uint32_t cursor;
  if (out_entry_end != NULL) *out_entry_end = 0U;
  if (out_branch_relative_offset != NULL) *out_branch_relative_offset = 0U;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (decode == NULL || section == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      out_entry_end == NULL || out_branch_relative_offset == NULL || out_target_offset == NULL ||
      section_index >= decode->section_count || entry_start >= section->size || entry_limit == 0U) {
    return 0;
  }
  cursor = entry_start;
  while (cursor < section->size && cursor - entry_start <= entry_limit) {
    const M68kDecodeCandidate *candidate = NULL;
    uint8_t target_kind = 0U;
    uint32_t target_offset = 0U;
    if (accepted_offset_is_interior(section, accepted_start[section_index], accepted_bytes[section_index], cursor))
      return 0;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (candidate == NULL || candidate->byte_count == 0U || cursor > UINT32_MAX - candidate->byte_count)
      return 0;
    if (accepted_range_has_code_byte_local(accepted_bytes[section_index], section->size, cursor,
        candidate->byte_count)) {
      return 0;
    }
    if (candidate_single_direct_nonfallthrough_control_target(section, candidate, &target_kind,
        &target_offset)) {
      if (target_kind != M68K_DECODE_TARGET_BRANCH || target_offset <= cursor + candidate->byte_count)
        return 0;
      *out_entry_end = cursor + candidate->byte_count;
      *out_branch_relative_offset = cursor - entry_start;
      *out_target_offset = target_offset;
      return 1;
    }
    if (candidate_has_decoded_direct_control_target(candidate) || !candidate_has_normal_fallthrough(candidate))
      return 0;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int scan_indexed_forward_branch_terminated_stub_entries(M68kDecodeIR *decode, uint8_t max_cpu,
    size_t section_index, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *site_candidate,
    uint8_t **accepted_start, uint8_t **accepted_bytes, uint32_t *out_entries, uint32_t entry_limit,
    uint32_t *out_entry_count) {
  const uint32_t max_entry_size = 32U;
  uint32_t table_offset = 0U;
  uint32_t first_end = 0U;
  uint32_t branch_relative_offset = 0U;
  uint32_t common_target = 0U;
  uint32_t stride;
  uint32_t cursor;
  if (out_entry_count != NULL) *out_entry_count = 0U;
  if (decode == NULL || section == NULL || site_candidate == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || out_entries == NULL || out_entry_count == NULL || entry_limit == 0U ||
      section_index >= decode->section_count || site_candidate->byte_count == 0U ||
      site_candidate->offset > UINT32_MAX - site_candidate->byte_count ||
      !candidate_indexed_control_table_base_offset(section, site_candidate, &table_offset)) {
    return 0;
  }
  if (table_offset != site_candidate->offset + site_candidate->byte_count || table_offset >= section->size)
    return 0;
  if (scan_forward_branch_terminated_stub_entry(decode, max_cpu, section_index, section, accepted_start,
      accepted_bytes, table_offset, max_entry_size, &first_end, &branch_relative_offset, &common_target) < 1) {
    return 0;
  }
  if (first_end <= table_offset || first_end > common_target) return 0;
  stride = first_end - table_offset;
  if (stride == 0U || stride > max_entry_size) return 0;
  cursor = table_offset;
  *out_entry_count = 0U;
  while (cursor < common_target && *out_entry_count < entry_limit) {
    uint32_t entry_end = 0U;
    uint32_t entry_branch_relative_offset = 0U;
    uint32_t target_offset = 0U;
    int scan_result = scan_forward_branch_terminated_stub_entry(decode, max_cpu, section_index, section,
      accepted_start, accepted_bytes, cursor, max_entry_size, &entry_end, &entry_branch_relative_offset,
      &target_offset);
    if (scan_result < 0) return -1;
    if (scan_result == 0 || entry_end != cursor + stride ||
        entry_branch_relative_offset != branch_relative_offset || target_offset != common_target) {
      break;
    }
    out_entries[(*out_entry_count)++] = cursor;
    if (cursor > UINT32_MAX - stride) break;
    cursor += stride;
  }
  return *out_entry_count >= 2U;
}

static int replay_runtime_sink_provenance_fallthrough(const M68kObject *object, M68kDecodeIR *decode,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kRuntimeAddressSpace *runtime_addresses,
    M68kFactIR *facts, M68kFactsV2WorkQueue *queue, M68kFactsV2Profile *profile, size_t section_index,
    uint32_t offset, const M68kFactsV2TraceState *initial_state, uint8_t **accepted_start,
    uint8_t **accepted_bytes, uint8_t max_cpu) {
  const uint32_t replay_limit = 8U;
  const M68kDecodeSectionIR *section;
  M68kFactsV2TraceState state;
  uint32_t cursor = offset;
  uint32_t step;
  if (object == NULL || decode == NULL || runtime_addresses == NULL || facts == NULL || profile == NULL ||
      initial_state == NULL || accepted_start == NULL || accepted_bytes == NULL ||
      section_index >= decode->section_count) {
    return -1;
  }
  section = &decode->sections[section_index];
  state = *initial_state;
  for (step = 0U; step < replay_limit && cursor < section->size; ++step) {
    const M68kDecodeCandidate *candidate = NULL;
    M68kDecodeCandidate candidate_copy;
    M68kFactsV2TraceState next_state;
    uint32_t next_cursor;
    if (!accepted_start[section_index][cursor]) return 0;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0) {
      return -1;
    }
    if (candidate == NULL) return 0;
    candidate_copy = *candidate;
    candidate = &candidate_copy;
    if (trace_state_record_runtime_copy(decode, runtime_addresses, facts, profile, section_index, section, candidate,
        &state, max_cpu) != 0) {
      return -1;
    }
    if (trace_state_record_runtime_sink_ref(runtime_addresses, facts, object->platform_backend_kind,
        section_index, section, accepted_start[section_index], accepted_bytes[section_index],
        candidate, &state) != 0) {
      return -1;
    }
    if (trace_state_record_runtime_storage_sink_ref(runtime_addresses, facts, object->platform_backend_kind,
        section_index, section, candidate, &state) != 0) {
      return -1;
    }
    trace_state_after_candidate(section_index, section, candidate, &state, relocation_lookup, facts,
      runtime_addresses, accepted_start[section_index], accepted_bytes[section_index], &next_state);
    if (queue != NULL && trace_state_can_drive_indirect_control(&state)) {
      if (enqueue_immediate_indirect_target_set(decode, facts, queue, accepted_start, accepted_bytes, profile,
          max_cpu, section_index, section, candidate, runtime_addresses, &next_state) != 0)
        return -1;
      if (enqueue_traced_indirect_control_target(decode, facts, queue, accepted_start, accepted_bytes,
          profile, max_cpu, section_index, candidate, runtime_addresses, &state) != 0)
        return -1;
      if (enqueue_traced_copied_entry_control_target(decode, facts, queue, accepted_start, accepted_bytes,
          profile, max_cpu, section_index, candidate, &state) != 0)
        return -1;
    }
    if (!candidate_has_normal_fallthrough(candidate) || candidate_has_control_target_local(candidate))
      return 0;
    if (candidate->byte_count > UINT32_MAX - cursor) return 0;
    next_cursor = cursor + candidate->byte_count;
    if (next_cursor <= cursor) return 0;
    if (next_cursor >= section->size) return 0;
    if (!accepted_start[section_index][next_cursor]) {
      uint32_t fallthrough_runtime = 0U;
      uint8_t fallthrough_has_runtime = (uint8_t)runtime_address_space_source_to_runtime_near(runtime_addresses,
        section_index, next_cursor, 0U, 0U, &fallthrough_runtime);
      uint8_t fallthrough_confidence = candidate_has_generated_conditional_branch_flow(candidate)
        ? M68K_FACT_CONFIDENCE_TOOL_INFERRED : M68K_FACT_CONFIDENCE_SPECULATIVE;
      if (queue != NULL && trace_state_can_drive_indirect_control(&next_state)) {
        if (enqueue_code_start_runtime_ex(facts, queue, profile, section_index, next_cursor,
            fallthrough_confidence, M68K_FACT_CODE_START_REASON_FALLTHROUGH, section_index, cursor,
            fallthrough_has_runtime, fallthrough_runtime, &next_state, 1U) != 0)
          return -1;
      }
      return 0;
    }
    cursor = next_cursor;
    state = next_state;
  }
  return 0;
}

static int candidate_preserves_trace_state_across_jump(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->flow_kind != M68K_SIM_FLOW_JUMP ||
      metadata->sp_effect_count != 0U) {
    return 0;
  }
  for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
    uint8_t access = metadata->operand_access_kinds[operand_index];
    if (access == M68K_SIM_ACCESS_REGISTER_WRITE || access == M68K_SIM_ACCESS_REGISTER_LIST_WRITE) return 0;
  }
  return 1;
}

static int target_prefix_uses_trace_indirect_control(M68kDecodeIR *decode, size_t section_index,
    uint32_t target_offset, const M68kFactsV2TraceState *trace_state, uint8_t max_cpu) {
  const uint32_t scan_limit = 8U;
  const M68kDecodeSectionIR *section;
  uint32_t cursor = target_offset;
  uint32_t step;
  if (decode == NULL || trace_state == NULL || section_index >= decode->section_count ||
      !trace_state_can_drive_indirect_control(trace_state)) {
    return 0;
  }
  section = &decode->sections[section_index];
  for (step = 0U; step < scan_limit && cursor < section->size; ++step) {
    const M68kDecodeCandidate *candidate = NULL;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    size_t operand_index;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0 || candidate == NULL) {
      return 0;
    }
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata != NULL &&
        (metadata->flow_kind == M68K_SIM_FLOW_CALL || metadata->flow_kind == M68K_SIM_FLOW_JUMP)) {
      for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
        uint8_t reg = 0U;
        if (operand_index >= instruction.operand_count ||
            metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET ||
            metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET ||
            !operand_is_control_address_register_indirect(candidate->operand_kinds[operand_index],
              &candidate->operands[operand_index], &reg)) {
          continue;
        }
        if (reg < 8U && trace_value_can_drive_indirect_control(&trace_state->a[reg])) return 1;
      }
    }
    if (!candidate_has_normal_fallthrough(candidate) || candidate_has_control_target_local(candidate)) return 0;
    if (candidate->byte_count == 0U || candidate->byte_count > UINT32_MAX - cursor) return 0;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int target_prefix_uses_trace_runtime_sink(M68kDecodeIR *decode, const M68kFactsV2RelocationLookup *relocation_lookup,
    const M68kRuntimeAddressSpace *runtime_addresses, M68kFactIR *facts, uint8_t platform_kind,
    uint8_t **accepted_start, uint8_t **accepted_bytes, size_t section_index, uint32_t target_offset,
    const M68kFactsV2TraceState *trace_state, uint8_t max_cpu) {
  const uint32_t scan_limit = 8U;
  const M68kDecodeSectionIR *section;
  M68kFactsV2TraceState state;
  uint32_t cursor = target_offset;
  uint32_t step;
  if (decode == NULL || relocation_lookup == NULL || runtime_addresses == NULL || facts == NULL ||
      accepted_start == NULL || accepted_bytes == NULL || trace_state == NULL ||
      section_index >= decode->section_count || !trace_state_can_drive_runtime_sink(platform_kind, trace_state)) {
    return 0;
  }
  section = &decode->sections[section_index];
  state = *trace_state;
  for (step = 0U; step < scan_limit && cursor < section->size; ++step) {
    const M68kDecodeCandidate *candidate = NULL;
    M68kFactsV2TraceState next_state;
    uint32_t sink_address = 0U;
    if (m68k_decode_ir_ensure_candidate_at(decode, section_index, cursor, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0 || candidate == NULL) {
      return 0;
    }
    if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && candidate->size_suffix == 'l' &&
        candidate->operand_count == 2U &&
        (operand_is_data_register_direct(&candidate->operands[0], NULL) ||
         operand_is_address_register_direct(&candidate->operands[0], NULL)) &&
        trace_state_operand_runtime_address(&state, candidate, 1U, &sink_address) &&
        platform_facts_v2_is_runtime_address_sink(platform_kind, sink_address)) {
      return 1;
    }
    trace_state_after_candidate(section_index, section, candidate, &state, relocation_lookup, facts,
      runtime_addresses, accepted_start[section_index], accepted_bytes[section_index], &next_state);
    state = next_state;
    if (!candidate_has_normal_fallthrough(candidate) || candidate_has_control_target_local(candidate)) return 0;
    if (candidate->byte_count == 0U || candidate->byte_count > UINT32_MAX - cursor) return 0;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int accept_platform_opcode_call(const M68kObject *object, const M68kDecodeSectionIR *section,
    M68kFactIR *facts, M68kFactsV2WorkQueue *queue, M68kFactsV2Profile *profile,
    const M68kFactsV2WorkItem *item, uint8_t **accepted_start, uint8_t **accepted_bytes) {
  PlatformFactsV2ResolvedCall call_info;
  M68kFact fact;
  uint32_t fallthrough;
  uint16_t opcode;
  if (object == NULL || section == NULL || facts == NULL || queue == NULL || item == NULL ||
      accepted_start == NULL || accepted_bytes == NULL || section->data == NULL ||
      item->offset + 2U > section->size) {
    return 0;
  }
  opcode = m68k_read_u16be(section->data + item->offset);
  if (!platform_facts_v2_resolve_opcode_call(object->platform_backend_kind, opcode, &call_info)) return 0;
  accepted_start[item->section_index][item->offset] = 1U;
  accepted_bytes[item->section_index][item->offset] = 1U;
  accepted_bytes[item->section_index][item->offset + 1U] = 1U;
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_CODE_ACCEPTED;
  fact.confidence = item->confidence;
  fact.section_index = item->section_index;
  fact.offset = item->offset;
  fact.reason = item->reason;
  fact.has_runtime_address = item->has_runtime_address;
  fact.runtime_address = item->runtime_address;
  fact.source_section_index = item->source_section_index;
  fact.source_offset = item->source_offset;
  fact.size = 2U;
  fact.platform_record_kind = opcode;
  if (m68k_fact_ir_append(facts, &fact) != 0) return -1;
  if (profile != NULL) ++profile->platform_call_count;
  fallthrough = item->offset + 2U;
  if (fallthrough < section->size) {
    uint8_t has_runtime = item->has_runtime_address;
    uint32_t runtime = item->runtime_address;
    if (has_runtime && runtime <= UINT32_MAX - 2U) runtime += 2U;
    if (enqueue_code_start_runtime(facts, queue, profile, item->section_index, fallthrough,
        M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_LINKAGE_API_ENTRY,
        item->section_index, item->offset, has_runtime, runtime, &item->trace_state) != 0) {
      return -1;
    }
  }
  return 1;
}

static int run_reachable_fixed_point(const M68kObject *object, M68kDecodeIR *decode, M68kFactIR *facts,
    const M68kAnalysisPolicy *policy,
    const M68kFactsV2RelocationLookup *relocation_lookup, M68kFactsV2WorkQueue *queue,
    M68kRuntimeAddressSpace *runtime_addresses,
    uint8_t **accepted_start, uint8_t **accepted_bytes,
    uint32_t *out_accepted_count, M68kFactsV2Profile *profile, uint8_t max_cpu,
    M68kDiagSink diagnostics) {
  M68kFactsV2WorkItem item;
  uint32_t accepted_count = 0U;
  int profile_reachable_phases = reachable_profile_enabled_local();
  if (object == NULL || decode == NULL || facts == NULL || queue == NULL || runtime_addresses == NULL ||
      accepted_start == NULL || accepted_bytes == NULL || out_accepted_count == NULL || profile == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
      "reachable fixed point received invalid arguments");
    return -1;
  }
  while (work_queue_pop(queue, &item)) {
    const M68kDecodeSectionIR *section;
    const M68kDecodeCandidate *candidate;
    M68kDecodeCandidate candidate_copy;
    M68kFactsV2TraceState next_trace_state;
    size_t target_index;
    clock_t phase_start;
    int validation_result;
    int already_accepted;
    if (item.section_index >= decode->section_count) continue;
    section = &decode->sections[item.section_index];
    if (item.offset >= section->size) continue;
    already_accepted = accepted_start[item.section_index][item.offset] != 0U;
    phase_start = profile_phase_start_local(profile_reachable_phases);
    if (m68k_decode_ir_ensure_candidate_at(decode, item.section_index, item.offset, max_cpu, &candidate,
        m68k_diag_sink(NULL)) != 0) {
      profile_phase_add_local(profile_reachable_phases, &profile->fixed_point_reachable_decode_seconds,
        phase_start);
      m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_DECODE_FAILED,
        "reachable fixed point decode failed at %u:%08X", (unsigned)item.section_index, (unsigned)item.offset);
      return -1;
    }
    profile_phase_add_local(profile_reachable_phases, &profile->fixed_point_reachable_decode_seconds,
      phase_start);
    if (candidate == NULL) {
      int platform_opcode_result = accept_platform_opcode_call(object, section, facts, queue, profile, &item,
        accepted_start, accepted_bytes);
      if (platform_opcode_result < 0) return -1;
      if (platform_opcode_result > 0) continue;
      int appended_violation = 0;
      if (accepted_offset_is_interior(section, accepted_start[item.section_index],
          accepted_bytes[item.section_index], item.offset)) {
        if (append_violation_fact(facts, item.section_index, item.offset, item.offset) != 0) return -1;
        appended_violation = 1;
      }
      if (item.confidence >= M68K_FACT_CONFIDENCE_REQUIRED) {
        if (!appended_violation &&
            append_violation_fact(facts, item.section_index, item.offset, item.offset) != 0) return -1;
        facts_v2_record_required_instruction_failure(profile, &item);
      }
      continue;
    }
    candidate_copy = *candidate;
    candidate = &candidate_copy;
    if (already_accepted) {
      if (item.has_runtime_address || item.allow_trace_variant) {
        if (replay_runtime_sink_provenance_fallthrough(object, decode, relocation_lookup, runtime_addresses, facts,
            queue, profile, item.section_index, item.offset, &item.trace_state, accepted_start, accepted_bytes,
            max_cpu) != 0) {
          return -1;
        }
      }
      if (enqueue_backward_sliced_indirect_table_targets(decode, facts, relocation_lookup, queue, accepted_start,
          accepted_bytes, profile, max_cpu, item.section_index, section, candidate, runtime_addresses) != 0) {
        return -1;
      }
      continue;
    }
    phase_start = profile_phase_start_local(profile_reachable_phases);
    validation_result = validate_reachable_candidate_for_acceptance(policy, facts, &item, section, candidate,
      accepted_start, accepted_bytes, &accepted_count, profile);
    profile_phase_add_local(profile_reachable_phases, &profile->fixed_point_reachable_validate_seconds,
      phase_start);
    if (validation_result < 0) {
      m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
        "reachable fixed point validation failed at %u:%08X", (unsigned)item.section_index,
        (unsigned)item.offset);
      return -1;
    }
    if (validation_result > 0) continue;
    phase_start = profile_phase_start_local(profile_reachable_phases);
    if (mark_accepted_bytes(accepted_bytes[item.section_index], candidate, section->size) != 0) {
      m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
        "reachable fixed point accepted-byte marking failed at %u:%08X", (unsigned)item.section_index,
        (unsigned)item.offset);
      return -1;
    }
    accepted_start[item.section_index][item.offset] = 1U;
    {
      M68kFact fact;
      memset(&fact, 0, sizeof(fact));
      fact.kind = M68K_FACT_CODE_ACCEPTED;
      fact.confidence = item.confidence;
      fact.section_index = item.section_index;
      fact.offset = item.offset;
      fact.reason = item.reason;
      fact.has_runtime_address = item.has_runtime_address;
      fact.runtime_address = item.runtime_address;
      fact.source_section_index = item.source_section_index;
      fact.source_offset = item.source_offset;
      fact.size = candidate->byte_count;
      if (m68k_fact_ir_append(facts, &fact) != 0) {
        m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
          "reachable fixed point code fact append failed at %u:%08X", (unsigned)item.section_index,
          (unsigned)item.offset);
        return -1;
      }
    }
    ++accepted_count;
    profile_phase_add_local(profile_reachable_phases, &profile->fixed_point_reachable_accept_seconds,
      phase_start);
    if (trace_state_record_runtime_copy(decode, runtime_addresses, facts, profile, item.section_index, section,
        candidate, &item.trace_state, max_cpu) != 0)
    {
      m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
        "reachable fixed point runtime-copy recording failed at %u:%08X", (unsigned)item.section_index,
        (unsigned)item.offset);
      return -1;
    }
    if (trace_state_record_runtime_sink_ref(runtime_addresses, facts, object->platform_backend_kind,
        item.section_index, section, accepted_start[item.section_index], accepted_bytes[item.section_index],
        candidate, &item.trace_state) != 0) {
      return -1;
    }
    if (trace_state_record_runtime_storage_sink_ref(runtime_addresses, facts, object->platform_backend_kind,
        item.section_index, section, candidate, &item.trace_state) != 0) {
      return -1;
    }
    {
      size_t segment_link_target_section = (size_t)-1;
      if (trace_state_candidate_loads_platform_loadseg_segment_link(decode, object->platform_backend_kind,
          candidate, &item.trace_state, &segment_link_target_section)) {
        profile_record_platform_loadseg_segment_link_access(profile, item.section_index, item.offset,
          segment_link_target_section < decode->section_count ? 1U : 0U, segment_link_target_section);
      }
    }
    trace_state_after_candidate(item.section_index, section, candidate, &item.trace_state, relocation_lookup, facts,
      runtime_addresses, accepted_start[item.section_index], accepted_bytes[item.section_index], &next_trace_state);
    (void)trace_state_apply_platform_loadseg_helper_call(decode, object->platform_backend_kind,
      item.section_index, section, candidate, &item.trace_state, max_cpu, &next_trace_state);
    if (enqueue_immediate_indirect_target_set(decode, facts, queue, accepted_start, accepted_bytes, profile,
        max_cpu, item.section_index, section, candidate, runtime_addresses, &next_trace_state) != 0)
      return -1;
    if (enqueue_indexed_direct_control_stub_table_entries(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, item.section_index, section, candidate, runtime_addresses) != 0)
      return -1;
    phase_start = profile_phase_start_local(profile_reachable_phases);
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      uint32_t target_offset = target->offset;
      uint8_t target_has_runtime = 0U;
      uint32_t target_runtime = 0U;
      if (!target->has_section) continue;
      if (target->kind != M68K_DECODE_TARGET_DATA) {
        uint32_t runtime_address = 0U;
        uint32_t mapped_offset = 0U;
        if (candidate_absolute_control_address(candidate, &runtime_address)) {
          if (!runtime_address_space_translate(runtime_addresses, item.section_index, runtime_address,
              section->size, &mapped_offset)) {
            continue;
          }
          target_offset = mapped_offset;
          target_has_runtime = 1U;
          target_runtime = runtime_address;
        } else if (runtime_address_space_source_to_runtime_near(runtime_addresses, item.section_index,
            target_offset, item.has_runtime_address, item.runtime_address, &target_runtime)) {
          target_has_runtime = 1U;
        }
      }
      if (target_offset >= section->size) continue;
      if (append_xref_fact(facts, item.section_index, item.offset, target_offset,
          M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) return -1;
      if (accepted_offset_is_interior(section, accepted_start[item.section_index],
          accepted_bytes[item.section_index], target_offset)) {
        if (append_violation_fact(facts, item.section_index, item.offset, target_offset) != 0) return -1;
        continue;
      }
      if (m68k_fact_ir_require_label(facts, item.section_index, target_offset,
          M68K_FACT_CONFIDENCE_TOOL_INFERRED) != 0) return -1;
      if (target->kind == M68K_DECODE_TARGET_DATA ||
          decode_target_is_indexed_control_operand_base(candidate, target)) {
        continue;
      }
      {
        const M68kDecodeCandidate *target_candidate = NULL;
        const M68kFactsV2TraceState *target_trace_state = &next_trace_state;
        uint8_t allow_trace_variant = 0U;
        if (candidate_preserves_trace_state_across_jump(candidate)) {
          target_trace_state = &item.trace_state;
        }
        if (m68k_decode_ir_ensure_candidate_at(decode, item.section_index, target_offset, max_cpu,
            &target_candidate, m68k_diag_sink(NULL)) != 0) return -1;
        if (target_candidate == NULL) continue;
        if (target_prefix_uses_trace_indirect_control(decode, item.section_index, target_offset,
            target_trace_state, max_cpu)) {
          allow_trace_variant = 1U;
        }
        if (target_prefix_uses_trace_runtime_sink(decode, relocation_lookup, runtime_addresses, facts,
            object->platform_backend_kind, accepted_start, accepted_bytes, item.section_index, target_offset,
            target_trace_state, max_cpu)) {
          allow_trace_variant = 1U;
        }
        if (target_has_runtime) {
          if (enqueue_code_start_runtime(facts, queue, profile, item.section_index, target_offset,
              M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
              item.section_index, item.offset, 1U, target_runtime, target_trace_state) != 0) return -1;
        } else {
          if (enqueue_code_start_runtime_ex(facts, queue, profile, item.section_index, target_offset,
              M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_CONTROL_TARGET,
              item.section_index, item.offset, 0U, 0U, target_trace_state, allow_trace_variant) != 0) return -1;
        }
      }
    }
    profile_phase_add_local(profile_reachable_phases, &profile->fixed_point_reachable_target_seconds,
      phase_start);
    if (item.reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET &&
        enqueue_adjacent_direct_control_stub_table_entries(decode, facts, relocation_lookup, queue,
          accepted_start, accepted_bytes, profile, max_cpu, item.section_index, section, candidate,
          runtime_addresses) != 0) {
      return -1;
    }
    phase_start = profile_phase_start_local(profile_reachable_phases);
    if (enqueue_relocated_control_target(decode, facts, relocation_lookup, queue, accepted_start, accepted_bytes,
        profile, max_cpu, item.section_index, candidate) != 0) return -1;
    if (enqueue_runtime_alias_absolute_control_target(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, item.section_index, candidate, runtime_addresses, &next_trace_state) != 0) return -1;
    if (enqueue_traced_indirect_control_target(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, item.section_index, candidate, runtime_addresses, &item.trace_state) != 0) return -1;
    if (enqueue_traced_copied_entry_control_target(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, item.section_index, candidate, &item.trace_state) != 0) return -1;
    if (enqueue_direct_indexed_stub_entries(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, item.section_index, section, candidate, runtime_addresses) != 0) {
      return -1;
    }
    if (enqueue_backward_sliced_indirect_table_targets(decode, facts, relocation_lookup, queue, accepted_start,
        accepted_bytes, profile, max_cpu, item.section_index, section, candidate, runtime_addresses) != 0) {
      return -1;
    }
    if (enqueue_interrupt_vector_store_target(decode, facts, queue, accepted_start, accepted_bytes,
        profile, max_cpu, object->platform_backend_kind, item.section_index, candidate, runtime_addresses,
        &item.trace_state) != 0) return -1;
    profile_phase_add_local(profile_reachable_phases, &profile->fixed_point_reachable_relocation_seconds,
      phase_start);
    phase_start = profile_phase_start_local(profile_reachable_phases);
    if (candidate_has_normal_fallthrough(candidate)) {
      uint32_t fallthrough = candidate->offset + candidate->byte_count;
      if (fallthrough < section->size) {
        uint32_t inline_resume = 0U;
        uint8_t fallthrough_has_runtime = 0U;
        uint32_t fallthrough_runtime = 0U;
        uint8_t fallthrough_allow_trace_variant = item.allow_trace_variant &&
          (trace_state_can_drive_indirect_control(&next_trace_state) ||
           trace_state_can_drive_runtime_sink(object->platform_backend_kind, &next_trace_state));
        uint8_t fallthrough_confidence = candidate_has_generated_conditional_branch_flow(candidate)
          ? M68K_FACT_CONFIDENCE_TOOL_INFERRED : M68K_FACT_CONFIDENCE_SPECULATIVE;
        if (item.has_runtime_address && item.runtime_address <= UINT32_MAX - candidate->byte_count) {
          fallthrough_has_runtime = 1U;
          fallthrough_runtime = item.runtime_address + candidate->byte_count;
        } else if (runtime_address_space_source_to_runtime_near(runtime_addresses, item.section_index, fallthrough,
            item.has_runtime_address, item.runtime_address, &fallthrough_runtime)) {
          fallthrough_has_runtime = 1U;
        }
        if (call_consumes_inline_string_payload(decode, section, candidate, fallthrough, &inline_resume, max_cpu)) {
          if (inline_resume < section->size) {
            if (fallthrough_has_runtime) {
              uint32_t inline_runtime = fallthrough_runtime;
              if (inline_resume >= fallthrough && inline_runtime <= UINT32_MAX - (inline_resume - fallthrough))
                inline_runtime += inline_resume - fallthrough;
              if (enqueue_code_start_runtime(facts, queue, profile, item.section_index, inline_resume,
                  M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_INLINE_RESUME,
                  item.section_index, item.offset, 1U, inline_runtime, &next_trace_state) != 0) return -1;
            } else {
              if (enqueue_code_start_runtime_ex(facts, queue, profile, item.section_index, inline_resume,
                  M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_INLINE_RESUME,
                  item.section_index, item.offset, 0U, 0U, &next_trace_state,
                  fallthrough_allow_trace_variant) != 0) return -1;
            }
          }
          profile_phase_add_local(profile_reachable_phases, &profile->fixed_point_reachable_fallthrough_seconds,
            phase_start);
          continue;
        }
        if (call_consumes_inline_word_payload(decode, section, candidate, fallthrough, &inline_resume, max_cpu)) {
          if (inline_resume < section->size) {
            if (fallthrough_has_runtime) {
              uint32_t inline_runtime = fallthrough_runtime;
              if (inline_resume >= fallthrough && inline_runtime <= UINT32_MAX - (inline_resume - fallthrough))
                inline_runtime += inline_resume - fallthrough;
              if (enqueue_code_start_runtime(facts, queue, profile, item.section_index, inline_resume,
                  M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_INLINE_RESUME,
                  item.section_index, item.offset, 1U, inline_runtime, &next_trace_state) != 0) return -1;
            } else {
              if (enqueue_code_start_runtime_ex(facts, queue, profile, item.section_index, inline_resume,
                  M68K_FACT_CONFIDENCE_TOOL_INFERRED, M68K_FACT_CODE_START_REASON_INLINE_RESUME,
                  item.section_index, item.offset, 0U, 0U, &next_trace_state,
                  fallthrough_allow_trace_variant) != 0) return -1;
            }
          }
          profile_phase_add_local(profile_reachable_phases, &profile->fixed_point_reachable_fallthrough_seconds,
            phase_start);
          continue;
        }
        if (fallthrough_has_runtime) {
          if (enqueue_code_start_runtime(facts, queue, profile, item.section_index, fallthrough,
              fallthrough_confidence, M68K_FACT_CODE_START_REASON_FALLTHROUGH,
              item.section_index, item.offset, 1U, fallthrough_runtime, &next_trace_state) != 0) return -1;
        } else {
          if (enqueue_code_start_runtime_ex(facts, queue, profile, item.section_index, fallthrough,
              fallthrough_confidence, M68K_FACT_CODE_START_REASON_FALLTHROUGH,
              item.section_index, item.offset, 0U, 0U, &next_trace_state,
              fallthrough_allow_trace_variant) != 0) return -1;
        }
      }
    }
    profile_phase_add_local(profile_reachable_phases, &profile->fixed_point_reachable_fallthrough_seconds,
      phase_start);
  }
  *out_accepted_count = accepted_count;
  return 0;
}

static int allocate_section_maps(const M68kDecodeIR *decode, Arena *arena, uint8_t ***out_start,
    uint8_t ***out_bytes) {
  uint8_t **starts;
  uint8_t **bytes;
  size_t section_index;
  if (decode == NULL || arena == NULL || out_start == NULL || out_bytes == NULL) return -1;
  starts = (uint8_t **)arena_calloc(arena, decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*starts));
  bytes = (uint8_t **)arena_calloc(arena, decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*bytes));
  if (starts == NULL || bytes == NULL) return -1;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    uint32_t size = decode->sections[section_index].size;
    starts[section_index] = (uint8_t *)arena_calloc(arena, size != 0U ? size : 1U, 1U);
    bytes[section_index] = (uint8_t *)arena_calloc(arena, size != 0U ? size : 1U, 1U);
    if (starts[section_index] == NULL || bytes[section_index] == NULL) return -1;
  }
  *out_start = starts;
  *out_bytes = bytes;
  return 0;
}

static void free_section_maps(const M68kDecodeIR *decode, uint8_t **starts, uint8_t **bytes) {
  (void)decode;
  (void)starts;
  (void)bytes;
}

void m68k_facts_v2_profile_init(M68kFactsV2Profile *profile) {
  if (profile == NULL) return;
  memset(profile, 0, sizeof(*profile));
}

static int facts_v2_has_hard_failures(const M68kFactsV2Profile *profile) {
  return profile != NULL && (profile->unresolved_labels != 0U ||
    profile->interior_conflicts_unresolved != 0U || profile->relocation_failures != 0U ||
    profile->relocation_anchor_instruction_bytes != 0U ||
    profile->relocation_anchor_unknown_contexts != 0U ||
    profile->required_instruction_failures != 0U);
}

static int facts_v2_has_source_blockers(const M68kFactsV2Profile *profile) {
  return facts_v2_has_hard_failures(profile);
}

static void facts_v2_record_source_blocker_first_failure(M68kFactsV2Profile *profile) {
  uint32_t kind = M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE;
  uint32_t section = 0U;
  uint32_t offset = 0U;
  uint32_t aux_offset = 0U;
  if (profile == NULL ||
      profile->asm_source_first_failure_kind != M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE)
    return;
  if (profile->unresolved_labels != 0U) {
    kind = M68K_RENDER_IR_ASM_SOURCE_FAILURE_UNRESOLVED_LABEL;
  } else if (profile->interior_conflicts_unresolved != 0U) {
    kind = M68K_RENDER_IR_ASM_SOURCE_FAILURE_INTERIOR_CONFLICT;
  } else if (profile->relocation_failures != 0U) {
    kind = M68K_RENDER_IR_ASM_SOURCE_FAILURE_RELOCATION;
    section = profile->first_relocation_failure_section;
    offset = profile->first_relocation_failure_offset;
    aux_offset = profile->first_relocation_failure_target_section;
  } else if (profile->relocation_anchor_instruction_bytes != 0U ||
      profile->relocation_anchor_unknown_contexts != 0U) {
    section = profile->first_relocation_anchor_section;
    offset = profile->first_relocation_anchor_offset;
    aux_offset = profile->first_relocation_anchor_target_section;
    kind = M68K_RENDER_IR_ASM_SOURCE_FAILURE_RELOCATION_ANCHOR;
  } else if (profile->required_instruction_failures != 0U) {
    kind = M68K_RENDER_IR_ASM_SOURCE_FAILURE_REQUIRED_INSTRUCTION;
    section = profile->first_required_instruction_failure_section;
    offset = profile->first_required_instruction_failure_offset;
  }
  profile->asm_source_first_failure_kind = kind;
  profile->asm_source_first_failure_section = section;
  profile->asm_source_first_failure_offset = offset;
  profile->asm_source_first_failure_aux_offset = aux_offset;
}

static int facts_v2_has_asm_source_failures(const M68kFactsV2Profile *profile) {
  return profile != NULL && (profile->asm_source_instruction_render_failures != 0U ||
    profile->asm_source_instruction_byte_mismatches != 0U ||
    profile->asm_source_instruction_relocation_failures != 0U);
}

static int facts_v2_collect_profile_internal(const M68kObject *object, const M68kAnalysisPolicy *policy,
    M68kFactsV2Profile *out_profile, int force_asm_source, int collect_asm_source_text,
    int allow_env_asm_source, int fail_on_asm_refused, int mark_source_blockers, char **out_asm_source,
    M68kSourceAnalysisIR *out_source_analysis, M68kRenderPlan *out_asm_source_plan, M68kDiagSink diagnostics) {
  M68kDecodeIR decode;
  M68kFactIR facts;
  M68kFactsV2WorkQueue queue;
  M68kFactsV2RelocationLookup relocation_lookup;
  M68kFactsV2LabelLookup label_lookup;
  M68kAcceptedCandidateIndex accepted_index;
  M68kRuntimeAddressSpace runtime_addresses;
  M68kFactsV2Workflow workflow;
  M68kRenderIRPreview *render_preview = NULL;
  int render_text_preview;
  int render_asm_source;
  uint8_t **accepted_start = NULL;
  uint8_t **accepted_bytes = NULL;
  clock_t start, end;
  uint8_t max_cpu;
  const char *fail_stage = "initialization";
  if (object == NULL || policy == NULL || out_profile == NULL) return -1;
  if (out_asm_source != NULL) *out_asm_source = NULL;
  if (out_source_analysis != NULL) memset(out_source_analysis, 0, sizeof(*out_source_analysis));
  if (out_asm_source_plan != NULL) m68k_render_plan_init(out_asm_source_plan);
  m68k_facts_v2_profile_init(out_profile);
  m68k_decode_ir_init(&decode);
  m68k_fact_ir_init(&facts);
  memset(&workflow, 0, sizeof(workflow));
  if (facts_v2_workflow_create(&workflow) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    goto fail;
  }
  render_preview = workflow.render_preview;
  memset(&queue, 0, sizeof(queue));
  memset(&relocation_lookup, 0, sizeof(relocation_lookup));
  memset(&label_lookup, 0, sizeof(label_lookup));
  memset(&accepted_index, 0, sizeof(accepted_index));
  runtime_address_space_init(&runtime_addresses, workflow.arena);
  render_text_preview = preview_source_enabled_local();
  render_asm_source = force_asm_source || (allow_env_asm_source && asm_source_enabled_local());
  max_cpu = policy->max_cpu != 0U ? policy->max_cpu : M68K_ASM_CPU_68060;
  start = clock();
  fail_stage = "decode";
  if (m68k_decode_ir_build_object_sections(&decode, object, diagnostics) != 0) goto fail;
  end = clock();
  out_profile->decode_seconds = elapsed_seconds_local(start, end);
  fail_stage = "work queue initialization";
  if (work_queue_init_for_decode(&queue, &decode, workflow.arena) != 0) goto fail;
  fail_stage = "accepted map allocation";
  if (allocate_section_maps(&decode, workflow.arena, &accepted_start, &accepted_bytes) != 0) goto fail;
  start = clock();
  fail_stage = "label lookup build";
  if (label_lookup_build(&label_lookup, &decode, workflow.arena) != 0) goto fail;
  fail_stage = "fact seeding";
  if (seed_facts_from_object(object, policy, &facts, &label_lookup, &queue, &runtime_addresses,
      out_profile) != 0) goto fail;
  fail_stage = "relocation lookup build";
  if (relocation_lookup_build(&relocation_lookup, &decode, &facts, workflow.arena) != 0) goto fail;
  fail_stage = "relocation-backed jump template seeding";
  if (seed_relocation_backed_jump_template_tables(&decode, &facts, &relocation_lookup, &queue,
      accepted_start, accepted_bytes, out_profile, max_cpu) != 0) goto fail;
  end = clock();
  out_profile->seed_seconds = elapsed_seconds_local(start, end);
  start = clock();
  fail_stage = "reachable fixed point";
  if (run_reachable_fixed_point(object, &decode, &facts, policy, &relocation_lookup, &queue, &runtime_addresses,
      accepted_start, accepted_bytes, &out_profile->accepted_instructions, out_profile, max_cpu,
      diagnostics) != 0) goto fail;
  {
    uint32_t promoted_function_pointer_targets = 0U;
    fail_stage = "relocation-backed function pointer table seeding";
    if (seed_relocation_backed_function_pointer_tables(&decode, &facts, &relocation_lookup, &queue,
        accepted_start, accepted_bytes, out_profile, max_cpu, &promoted_function_pointer_targets) != 0) goto fail;
    if (promoted_function_pointer_targets != 0U) {
      fail_stage = "function pointer target reachable fixed point";
      if (run_reachable_fixed_point(object, &decode, &facts, policy, &relocation_lookup, &queue, &runtime_addresses,
          accepted_start, accepted_bytes, &out_profile->accepted_instructions, out_profile, max_cpu,
          diagnostics) != 0) goto fail;
    }
  }
  end = clock();
  add_elapsed_seconds_local(&out_profile->fixed_point_reachable_seconds, start, end);
  out_profile->decoded_candidates = decode.decoded_candidate_count;
  start = clock();
  fail_stage = "accepted index build";
  if (accepted_candidate_index_build(&accepted_index, &decode, accepted_start, workflow.arena) != 0) goto fail;
  end = clock();
  add_elapsed_seconds_local(&out_profile->fixed_point_index_seconds, start, end);
  {
    uint32_t demoted_interior_conflicts = 0U;
    start = clock();
    fail_stage = "required label conflict demotion";
    if (demote_required_label_conflicts(&decode, &accepted_index, accepted_start, accepted_bytes, &facts,
        &label_lookup, &out_profile->accepted_instructions, &demoted_interior_conflicts) != 0) goto fail;
    end = clock();
    add_elapsed_seconds_local(&out_profile->fixed_point_required_label_conflict_seconds, start, end);
    out_profile->interior_conflicts_resolved_by_demote = demoted_interior_conflicts;
  }
  {
    start = clock();
    fail_stage = "opcode relocation conflict demotion";
    if (demote_opcode_relocation_conflicts(&decode, &accepted_index, accepted_start, accepted_bytes, &facts,
        &out_profile->accepted_instructions, out_profile) != 0) goto fail;
    end = clock();
    add_elapsed_seconds_local(&out_profile->fixed_point_opcode_relocation_conflict_seconds, start, end);
  }
  accepted_candidate_index_destroy(&accepted_index);
  start = clock();
  fail_stage = "accepted byte rebuild";
  if (rebuild_accepted_bytes_from_starts(&decode, accepted_start, accepted_bytes,
      &out_profile->accepted_instructions) != 0) goto fail;
  end = clock();
  add_elapsed_seconds_local(&out_profile->fixed_point_rebuild_accepted_seconds, start, end);
  start = clock();
  fail_stage = "accepted index rebuild";
  if (accepted_candidate_index_build(&accepted_index, &decode, accepted_start, workflow.arena) != 0) goto fail;
  end = clock();
  add_elapsed_seconds_local(&out_profile->fixed_point_index_seconds, start, end);
  start = clock();
  fail_stage = "relocation anchor classification";
  if (classify_relocation_anchor_contexts(&decode, &accepted_index, accepted_start, accepted_bytes, &facts,
      out_profile) != 0) goto fail;
  end = clock();
  add_elapsed_seconds_local(&out_profile->fixed_point_relocation_anchor_seconds, start, end);
  accepted_candidate_index_destroy(&accepted_index);
  start = clock();
  fail_stage = "runtime address reference append";
  if (append_runtime_address_refs_for_accepted(&decode, object->platform_backend_kind, &runtime_addresses,
      accepted_start, accepted_bytes, &facts) != 0) {
    goto fail;
  }
  {
    uint32_t runtime_view_entry_seeds = 0U;
    uint32_t runtime_view_accepted = 0U;
    fail_stage = "runtime view entry seeding";
    if (seed_runtime_ref_target_discovered_copy_entries(&decode, &facts, &queue, &runtime_addresses,
        accepted_start, accepted_bytes, out_profile, max_cpu, &runtime_view_entry_seeds) != 0) {
      goto fail;
    }
    if (runtime_view_entry_seeds != 0U) {
      fail_stage = "runtime view entry reachable fixed point";
      if (run_reachable_fixed_point(object, &decode, &facts, policy, &relocation_lookup, &queue,
          &runtime_addresses, accepted_start, accepted_bytes, &runtime_view_accepted, out_profile, max_cpu,
          diagnostics) != 0) {
        goto fail;
      }
      out_profile->accepted_instructions += runtime_view_accepted;
      fail_stage = "runtime view entry accepted byte rebuild";
      if (rebuild_accepted_bytes_from_starts(&decode, accepted_start, accepted_bytes,
          &out_profile->accepted_instructions) != 0) {
        goto fail;
      }
      fail_stage = "runtime view entry runtime address reference append";
      if (append_runtime_address_refs_for_accepted(&decode, object->platform_backend_kind, &runtime_addresses,
          accepted_start, accepted_bytes, &facts) != 0) {
        goto fail;
      }
    }
  }
  end = clock();
  add_elapsed_seconds_local(&out_profile->fixed_point_runtime_address_ref_seconds, start, end);
  {
    size_t backward_table_queue_count = queue.count;
    uint32_t backward_table_accepted = 0U;
    fail_stage = "backward sliced indirect table append";
    if (append_backward_sliced_indirect_table_targets_for_accepted(&decode, &facts, &relocation_lookup, &queue,
        accepted_start, accepted_bytes, out_profile, max_cpu, &runtime_addresses) != 0) {
      goto fail;
    }
    if (queue.count > backward_table_queue_count) {
      fail_stage = "backward sliced indirect table reachable fixed point";
      if (run_reachable_fixed_point(object, &decode, &facts, policy, &relocation_lookup, &queue,
          &runtime_addresses, accepted_start, accepted_bytes, &backward_table_accepted, out_profile, max_cpu,
          diagnostics) != 0) {
        goto fail;
      }
      out_profile->accepted_instructions += backward_table_accepted;
      fail_stage = "backward sliced indirect table accepted byte rebuild";
      if (rebuild_accepted_bytes_from_starts(&decode, accepted_start, accepted_bytes,
          &out_profile->accepted_instructions) != 0) {
        goto fail;
      }
    }
  }
  {
    uint32_t callback_field_entry_seeds = 0U;
    uint32_t callback_field_accepted = 0U;
    fail_stage = "callback field indirect target seeding";
    if (seed_callback_field_indirect_targets(&decode, &facts, &relocation_lookup, &queue, &runtime_addresses,
        workflow.arena, accepted_start, accepted_bytes, out_profile, max_cpu, &callback_field_entry_seeds) != 0) {
      goto fail;
    }
    if (callback_field_entry_seeds != 0U) {
      fail_stage = "callback field indirect target reachable fixed point";
      if (run_reachable_fixed_point(object, &decode, &facts, policy, &relocation_lookup, &queue,
          &runtime_addresses, accepted_start, accepted_bytes, &callback_field_accepted, out_profile, max_cpu,
          diagnostics) != 0) {
        goto fail;
      }
      out_profile->accepted_instructions += callback_field_accepted;
      fail_stage = "callback field accepted byte rebuild";
      if (rebuild_accepted_bytes_from_starts(&decode, accepted_start, accepted_bytes,
          &out_profile->accepted_instructions) != 0) {
        goto fail;
      }
      fail_stage = "callback field runtime address reference append";
      if (append_runtime_address_refs_for_accepted(&decode, object->platform_backend_kind, &runtime_addresses,
          accepted_start, accepted_bytes, &facts) != 0) {
        goto fail;
      }
    }
  }
  start = clock();
  fail_stage = "required label materialization";
  if (accepted_candidate_index_build(&accepted_index, &decode, accepted_start, workflow.arena) != 0) goto fail;
  if (materialize_pc_relative_interior_data_anchors(&decode, &accepted_index, accepted_start, accepted_bytes,
      &facts, &label_lookup) != 0) {
    goto fail;
  }
  accepted_candidate_index_destroy(&accepted_index);
  if (materialize_safe_required_labels(&decode, accepted_start, accepted_bytes, &facts, &label_lookup) != 0)
    goto fail;
  {
    size_t api_entry_seed_pass;
    size_t api_entry_seed_pass_limit = platform_api_entry_seed_pass_limit(&decode);
    for (api_entry_seed_pass = 0U; api_entry_seed_pass < api_entry_seed_pass_limit; ++api_entry_seed_pass) {
      uint32_t linkage_api_entry_seeds = 0U;
      uint32_t boundary_api_entry_seeds = 0U;
      uint32_t api_entry_accepted = 0U;
      fail_stage = "platform API entry seeding";
      if (seed_linkage_api_entry_labels(&decode, &facts, &label_lookup, &queue, object->platform_backend_kind,
          accepted_start, accepted_bytes, out_profile, max_cpu, &linkage_api_entry_seeds) != 0) {
        goto fail;
      }
      if (seed_boundary_api_entries(&decode, &facts, &relocation_lookup, &queue, object->platform_backend_kind,
          accepted_start, accepted_bytes, out_profile, max_cpu, &boundary_api_entry_seeds) != 0) {
        goto fail;
      }
      if (linkage_api_entry_seeds == 0U && boundary_api_entry_seeds == 0U) break;
      fail_stage = "platform API entry reachable fixed point";
      if (run_reachable_fixed_point(object, &decode, &facts, policy, &relocation_lookup, &queue,
          &runtime_addresses, accepted_start, accepted_bytes, &api_entry_accepted, out_profile, max_cpu,
          diagnostics) != 0) {
        goto fail;
      }
      out_profile->accepted_instructions += api_entry_accepted;
      fail_stage = "platform API entry accepted byte rebuild";
      if (rebuild_accepted_bytes_from_starts(&decode, accepted_start, accepted_bytes,
          &out_profile->accepted_instructions) != 0) {
        goto fail;
      }
      fail_stage = "platform API entry runtime address reference append";
      if (append_runtime_address_refs_for_accepted(&decode, object->platform_backend_kind, &runtime_addresses,
          accepted_start, accepted_bytes, &facts) != 0) {
        goto fail;
      }
      if (api_entry_accepted == 0U) break;
    }
  }
  end = clock();
  add_elapsed_seconds_local(&out_profile->fixed_point_required_label_materialize_seconds, start, end);
  out_profile->fixed_point_materialize_labels_seconds =
    out_profile->fixed_point_runtime_address_ref_seconds +
    out_profile->fixed_point_required_label_materialize_seconds;
  start = clock();
  fail_stage = "data span classification";
  out_profile->data_spans = count_data_spans_and_append_facts(&decode, accepted_bytes, &facts);
  end = clock();
  add_elapsed_seconds_local(&out_profile->fixed_point_data_span_seconds, start, end);
  out_profile->fixed_point_seconds =
    out_profile->fixed_point_reachable_seconds +
    out_profile->fixed_point_index_seconds +
    out_profile->fixed_point_required_label_conflict_seconds +
    out_profile->fixed_point_opcode_relocation_conflict_seconds +
    out_profile->fixed_point_rebuild_accepted_seconds +
    out_profile->fixed_point_relocation_anchor_seconds +
    out_profile->fixed_point_materialize_labels_seconds +
    out_profile->fixed_point_data_span_seconds;
  {
    uint32_t invariant_interior_conflicts = 0U;
    start = clock();
    fail_stage = "required label invariant resolution";
    out_profile->unresolved_labels = resolve_required_label_invariants(&decode, accepted_start, accepted_bytes,
      &facts, &facts, &label_lookup, &invariant_interior_conflicts);
    end = clock();
    add_elapsed_seconds_local(&out_profile->fixed_point_invariant_seconds, start, end);
    out_profile->interior_conflicts_unresolved = invariant_interior_conflicts;
    out_profile->interior_conflicts = out_profile->interior_conflicts_resolved_by_demote +
      out_profile->interior_conflicts_unresolved;
  }
  if ((render_asm_source || mark_source_blockers) && facts_v2_has_source_blockers(out_profile)) {
    out_profile->asm_source_enabled = render_asm_source ? 1U : 0U;
    out_profile->asm_source_refused = 1U;
    out_profile->asm_source_relocation_anchor_refusals =
      out_profile->relocation_anchor_instruction_bytes + out_profile->relocation_anchor_unknown_contexts;
    out_profile->asm_source_unassemblable_hunk_data_relocation_refusals =
      out_profile->unassemblable_hunk_data_relocations;
    out_profile->asm_source_unassemblable_hunk_base_register_relocation_refusals =
      out_profile->unassemblable_hunk_base_register_relocations;
    facts_v2_record_source_blocker_first_failure(out_profile);
    render_asm_source = 0;
    if (fail_on_asm_refused && force_asm_source) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
        "facts_v2 asm source refused because structural invariants failed");
      goto fail;
    }
  }
  out_profile->labels_created = facts.label_created_count;
  out_profile->labels_referenced = facts.label_required_count;
  out_profile->queue_iterations = (uint32_t)queue.cursor;
  start = clock();
  fail_stage = "render preview build";
  if (m68k_render_ir_preview_build(object, &decode, &facts, policy, accepted_start, accepted_bytes,
      render_text_preview, render_asm_source, collect_asm_source_text, out_asm_source != NULL, render_preview,
      out_source_analysis) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
      "facts_v2 render preview build failed");
    goto fail;
  }
  if (out_source_analysis != NULL &&
      append_recovered_indirect_sites_for_accepted(&decode, accepted_start, accepted_bytes, out_source_analysis,
        max_cpu) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
      "facts_v2 accepted indirect site append failed");
    goto fail;
  }
  if (out_source_analysis != NULL &&
      append_absolute_memory_refs_for_accepted(&decode, &facts, &relocation_lookup, object->platform_backend_kind,
        &runtime_addresses, accepted_start, accepted_bytes, out_source_analysis) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
      "facts_v2 absolute memory ref append failed");
    goto fail;
  }
  if (out_source_analysis != NULL && append_platform_storage_layouts_from_object(object, out_source_analysis) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
      "facts_v2 platform storage layout append failed");
    goto fail;
  }
  if (out_source_analysis != NULL) {
    m68k_ir_source_analysis_finalize_table_conflicts(out_source_analysis);
    m68k_ir_source_analysis_finalize_base_layout_conflicts(out_source_analysis);
  }
  end = clock();
  out_profile->render_ir_seconds = elapsed_seconds_local(start, end);
  out_profile->render_ir_lookup_seconds = render_preview->lookup_seconds;
  out_profile->render_ir_platform_pass_seconds = render_preview->platform_pass_seconds;
  out_profile->render_ir_platform_base_slot_seconds = render_preview->platform_pass_base_slot_seconds;
  out_profile->render_ir_platform_call_summary_seconds = render_preview->platform_pass_call_summary_seconds;
  out_profile->render_ir_platform_typed_ref_seconds = render_preview->platform_pass_typed_ref_seconds;
  out_profile->render_ir_platform_call_comment_seconds = render_preview->platform_pass_call_comment_seconds;
  out_profile->render_ir_platform_app_slot_seconds = render_preview->platform_pass_app_slot_seconds;
  out_profile->render_ir_platform_runtime_data_seconds = render_preview->platform_pass_runtime_data_seconds;
  out_profile->render_ir_platform_hardware_data_seconds = render_preview->platform_pass_hardware_data_seconds;
  out_profile->render_ir_platform_generic_data_seconds = render_preview->platform_pass_generic_data_seconds;
  out_profile->render_ir_header_seconds = render_preview->header_seconds;
  out_profile->render_ir_walk_seconds = render_preview->walk_seconds;
  out_profile->render_ir_footer_seconds = render_preview->footer_seconds;
  out_profile->render_ir_statements = render_preview->statement_count;
  out_profile->render_ir_labels = render_preview->label_statement_count;
  out_profile->render_ir_instructions = render_preview->instruction_statement_count;
  out_profile->render_ir_data_spans = render_preview->data_statement_count;
  out_profile->render_ir_hash = render_preview->structural_hash;
  out_profile->preview_source_enabled = render_text_preview ? 1U : 0U;
  out_profile->preview_source_bytes = render_preview->text_bytes;
  out_profile->preview_source_hash = render_preview->text_hash;
  if (out_profile->asm_source_refused == 0U) out_profile->asm_source_enabled = render_asm_source ? 1U : 0U;
  out_profile->asm_source_bytes = render_preview->asm_source_bytes;
  out_profile->asm_source_lines = render_preview->asm_source_lines;
  out_profile->asm_source_plan_rows = render_preview->asm_source_plan_rows;
  out_profile->asm_source_plan_lines = render_preview->asm_source_plan_lines;
  out_profile->asm_source_plan_bytes = render_preview->asm_source_plan_bytes;
  out_profile->asm_source_relocation_exprs = render_preview->asm_source_relocation_exprs;
  out_profile->asm_source_symbolic_instructions = render_preview->asm_source_symbolic_instructions;
  out_profile->asm_source_numeric_runtime_refs = render_preview->asm_source_numeric_runtime_refs;
  out_profile->asm_source_first_numeric_runtime_ref_section =
    render_preview->asm_source_first_numeric_runtime_ref_section;
  out_profile->asm_source_first_numeric_runtime_ref_offset =
    render_preview->asm_source_first_numeric_runtime_ref_offset;
  out_profile->asm_source_first_numeric_runtime_ref_target_section =
    render_preview->asm_source_first_numeric_runtime_ref_target_section;
  out_profile->asm_source_first_numeric_runtime_ref_target_offset =
    render_preview->asm_source_first_numeric_runtime_ref_target_offset;
  out_profile->asm_source_first_numeric_runtime_ref_runtime_address =
    render_preview->asm_source_first_numeric_runtime_ref_runtime_address;
  out_profile->platform_base_slot_count = render_preview->platform_base_slot_count;
  out_profile->platform_call_count = render_preview->platform_call_count;
  out_profile->platform_effect_count = render_preview->platform_effect_count;
  out_profile->asm_source_lossy_numeric_hunk_relocations =
    render_preview->asm_source_lossy_numeric_hunk_relocations;
  out_profile->asm_source_instruction_render_failures = render_preview->asm_source_instruction_render_failures;
  out_profile->asm_source_instruction_byte_mismatches = render_preview->asm_source_instruction_byte_mismatches;
  out_profile->asm_source_instruction_relocation_failures =
    render_preview->asm_source_instruction_relocation_failures;
  if (out_profile->asm_source_first_failure_kind == M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE) {
    out_profile->asm_source_first_failure_kind = render_preview->asm_source_first_failure_kind;
    out_profile->asm_source_first_failure_section = render_preview->asm_source_first_failure_section;
    out_profile->asm_source_first_failure_offset = render_preview->asm_source_first_failure_offset;
    out_profile->asm_source_first_failure_aux_offset = render_preview->asm_source_first_failure_aux_offset;
  }
  out_profile->asm_source_hash = render_preview->asm_source_hash;
  if (render_asm_source && (out_profile->relocation_anchor_instruction_bytes != 0U ||
      out_profile->relocation_anchor_unknown_contexts != 0U)) {
    out_profile->asm_source_enabled = 1U;
    out_profile->asm_source_refused = 1U;
    out_profile->asm_source_relocation_anchor_refusals =
      out_profile->relocation_anchor_instruction_bytes + out_profile->relocation_anchor_unknown_contexts;
    facts_v2_record_source_blocker_first_failure(out_profile);
  }
  if (render_asm_source && facts_v2_has_asm_source_failures(out_profile)) {
    out_profile->asm_source_enabled = 1U;
    out_profile->asm_source_refused = 1U;
    if (fail_on_asm_refused) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
        "facts_v2 asm source refused because source rendering invariants failed");
      goto fail;
    }
  }
  if (out_asm_source != NULL && !facts_v2_has_asm_source_failures(out_profile) &&
      render_preview->asm_source_text != NULL) {
    *out_asm_source = render_preview->asm_source_text;
    render_preview->asm_source_text = NULL;
  }
  if (out_asm_source_plan != NULL && !facts_v2_has_asm_source_failures(out_profile)) {
    m68k_render_plan_move(out_asm_source_plan, &render_preview->asm_source_plan);
  }
  {
    ArenaStats workflow_stats = arena_stats(workflow.arena);
    out_profile->workflow_arena_peak_used =
      workflow_stats.peak_used > UINT32_MAX ? UINT32_MAX : (uint32_t)workflow_stats.peak_used;
    out_profile->workflow_arena_total_blocks =
      workflow_stats.total_block_count > UINT32_MAX ? UINT32_MAX : (uint32_t)workflow_stats.total_block_count;
  }
  accepted_candidate_index_destroy(&accepted_index);
  free_section_maps(&decode, accepted_start, accepted_bytes);
  label_lookup_destroy(&label_lookup);
  relocation_lookup_destroy(&relocation_lookup);
  runtime_address_space_destroy(&runtime_addresses);
  work_queue_destroy(&queue);
  facts_v2_workflow_destroy(&workflow);
  m68k_fact_ir_destroy(&facts);
  m68k_decode_ir_destroy(&decode);
  return 0;
fail:
  if (!m68k_diag_has_errors(diagnostics.list)) {
    m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
      "facts_v2 failed during %s", fail_stage);
  }
  if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
  accepted_candidate_index_destroy(&accepted_index);
  free_section_maps(&decode, accepted_start, accepted_bytes);
  label_lookup_destroy(&label_lookup);
  relocation_lookup_destroy(&relocation_lookup);
  runtime_address_space_destroy(&runtime_addresses);
  work_queue_destroy(&queue);
  facts_v2_workflow_destroy(&workflow);
  m68k_fact_ir_destroy(&facts);
  m68k_decode_ir_destroy(&decode);
  return -1;
}

int m68k_facts_v2_collect_profile(const M68kObject *object, const M68kAnalysisPolicy *policy,
    M68kFactsV2Profile *out_profile, M68kDiagSink diagnostics) {
  return facts_v2_collect_profile_internal(object, policy, out_profile, 0, 0, 1, 0, 0, NULL, NULL, NULL,
    diagnostics);
}

int m68k_facts_v2_collect_direct_rebuild_profile(const M68kObject *object, const M68kAnalysisPolicy *policy,
    M68kFactsV2Profile *out_profile, M68kDiagSink diagnostics) {
  return facts_v2_collect_profile_internal(object, policy, out_profile, 0, 0, 1, 0, 1, NULL, NULL, NULL,
    diagnostics);
}

int m68k_facts_v2_collect_asm_source_profile(const M68kObject *object, const M68kAnalysisPolicy *policy,
    M68kFactsV2Profile *out_profile, M68kDiagSink diagnostics) {
  return facts_v2_collect_profile_internal(object, policy, out_profile, 1, 0, 1, 0, 0, NULL, NULL, NULL,
    diagnostics);
}

int m68k_facts_v2_render_asm_source_alloc(const M68kObject *object, const M68kAnalysisPolicy *policy,
    char **out_source, M68kFactsV2Profile *out_profile, M68kDiagSink diagnostics) {
  return m68k_facts_v2_render_asm_source_profile_alloc(object, policy, out_source, out_profile, 1U, diagnostics);
}

int m68k_facts_v2_render_asm_source_profile_alloc(const M68kObject *object, const M68kAnalysisPolicy *policy,
    char **out_source, M68kFactsV2Profile *out_profile, uint8_t fail_on_refused, M68kDiagSink diagnostics) {
  M68kFactsV2Profile local_profile;
  M68kFactsV2Profile *profile = out_profile != NULL ? out_profile : &local_profile;
  if (out_source == NULL) return -1;
  *out_source = NULL;
  return facts_v2_collect_profile_internal(object, policy, profile, 1, 1, 1, fail_on_refused != 0U, 0,
    out_source, NULL, NULL, diagnostics);
}

int m68k_facts_v2_render_asm_source_analysis_profile_alloc(const M68kObject *object,
    const M68kAnalysisPolicy *policy, char **out_source, M68kFactsV2Profile *out_profile,
    M68kSourceAnalysisIR *out_source_analysis, uint8_t fail_on_refused, M68kDiagSink diagnostics) {
  M68kFactsV2Profile local_profile;
  M68kFactsV2Profile *profile = out_profile != NULL ? out_profile : &local_profile;
  if (out_source == NULL || out_source_analysis == NULL) return -1;
  *out_source = NULL;
  memset(out_source_analysis, 0, sizeof(*out_source_analysis));
  return facts_v2_collect_profile_internal(object, policy, profile, 1, 1, 1, fail_on_refused != 0U, 0,
    out_source, out_source_analysis, NULL, diagnostics);
}

int m68k_facts_v2_render_asm_source_plan_analysis_profile_alloc(const M68kObject *object,
    const M68kAnalysisPolicy *policy, char **out_source, M68kRenderPlan *out_source_plan,
    M68kFactsV2Profile *out_profile, M68kSourceAnalysisIR *out_source_analysis, uint8_t fail_on_refused,
    M68kDiagSink diagnostics) {
  M68kFactsV2Profile local_profile;
  M68kFactsV2Profile *profile = out_profile != NULL ? out_profile : &local_profile;
  if (out_source_plan == NULL || out_source_analysis == NULL) return -1;
  if (out_source != NULL) *out_source = NULL;
  memset(out_source_analysis, 0, sizeof(*out_source_analysis));
  m68k_render_plan_init(out_source_plan);
  return facts_v2_collect_profile_internal(object, policy, profile, 1, 1, 1, fail_on_refused != 0U, 0,
    out_source, out_source_analysis, out_source_plan, diagnostics);
}

int m68k_facts_v2_collect_source_analysis_profile(const M68kObject *object,
    const M68kAnalysisPolicy *policy, M68kFactsV2Profile *out_profile,
    M68kSourceAnalysisIR *out_source_analysis, M68kDiagSink diagnostics) {
  M68kFactsV2Profile local_profile;
  M68kFactsV2Profile *profile = out_profile != NULL ? out_profile : &local_profile;
  if (out_source_analysis == NULL) return -1;
  memset(out_source_analysis, 0, sizeof(*out_source_analysis));
  return facts_v2_collect_profile_internal(object, policy, profile, 0, 0, 0, 0, 0, NULL,
    out_source_analysis, NULL, diagnostics);
}

void m68k_facts_v2_free_text(char *text) {
  free(text);
}
