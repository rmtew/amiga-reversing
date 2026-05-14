#include "platform_file_internal.h"
#include "m68k_bitset.h"

const char *const AMIGA_APP_BASE_TAG = "__amiga_app_base__";

#include <ctype.h>
#include <stdlib.h>
#include <time.h>

#define AMIGA_BASE_SLOT_TAG_CAPACITY 64U
#define AMIGA_TYPED_STACK_CAPACITY 64U
#define AMIGA_TYPED_LOCAL_SLOT_CAPACITY 64U
#define AMIGA_TYPED_TRACE_CACHE_CAPACITY 32U
#define AMIGA_LOCAL_WRAPPER_SIGNATURE_CACHE_CAPACITY 4096U
#define AMIGA_APP_SLOT_SYMBOL_CACHE_CAPACITY 4096U
#define AMIGA_SECTION_DIRECT_CALL_CACHE_CAPACITY 4096U
#define AMIGA_BASE_SLOT_ID_CACHE_CAPACITY 8192U
#define AMIGA_LOCAL_BASE_ID_APP UINT16_MAX

typedef struct AmigaValueProvenance {
  uint16_t type_id;
  uint16_t struct_id;
  uint16_t owner_type_id;
  uint16_t owner_struct_id;
  uint16_t symbol_id;
  uint16_t context_base_id;
  uint16_t semantic_kind_id;
  uint16_t value_domain_id;
  uint8_t has_constant_value;
  int32_t constant_value;
  uint32_t source_offset;
  uint8_t source_reg_kind;
  uint8_t source_reg_index;
  int16_t slot_disp;
  int16_t field_disp;
  uint16_t field_symbol_id;
} AmigaValueProvenance;

typedef struct AmigaTypedSlotTag {
  int16_t displacement;
  AmigaValueProvenance value;
} AmigaTypedSlotTag;

typedef struct AmigaAbsoluteBaseSlotTag {
  size_t section_index;
  uint32_t target_offset;
  uint16_t base_id;
} AmigaAbsoluteBaseSlotTag;

typedef struct AmigaAbsoluteTypedSlotTag {
  size_t section_index;
  uint32_t target_offset;
  AmigaValueProvenance value;
} AmigaAbsoluteTypedSlotTag;

typedef struct AmigaTypedStackEntry {
  AmigaValueProvenance value;
} AmigaTypedStackEntry;

typedef struct AmigaTypedLocalSlotEntry {
  uint16_t base_id;
  int16_t displacement;
  AmigaValueProvenance value;
} AmigaTypedLocalSlotEntry;

typedef struct AmigaResolvedTarget {
  uint32_t target;
  uint8_t valid;
} AmigaResolvedTarget;

typedef struct AmigaTargetStackEntry {
  AmigaResolvedTarget value;
} AmigaTargetStackEntry;

typedef struct AmigaTargetLocalSlotEntry {
  uint16_t base_id;
  int16_t displacement;
  AmigaResolvedTarget value;
} AmigaTargetLocalSlotEntry;

typedef AmigaValueProvenance AmigaResolvedAddressRegInfo;
typedef AmigaValueProvenance AmigaResolvedDataRegInfo;

typedef struct AmigaTypedTraceState {
  AmigaValueProvenance addr_reg_values[8];
  AmigaValueProvenance data_reg_values[8];
  AmigaTypedSlotTag slot_type_names[AMIGA_BASE_SLOT_TAG_CAPACITY];
  AmigaAbsoluteTypedSlotTag absolute_typed_slots[AMIGA_BASE_SLOT_TAG_CAPACITY];
  AmigaTypedStackEntry saved_stack[AMIGA_TYPED_STACK_CAPACITY];
  AmigaTypedLocalSlotEntry local_slots[AMIGA_TYPED_LOCAL_SLOT_CAPACITY];
  uint16_t local_base_ids[8];
  size_t saved_stack_count;
  uint16_t next_local_base_id;
} AmigaTypedTraceState;

typedef struct AmigaTypedTraceCache {
  const M68kSectionAnalysisIR *section_analysis;
  int include_section_slots;
  uint32_t origin;
  uint32_t cursor;
  uint8_t valid;
  AmigaTypedTraceState state;
} AmigaTypedTraceCache;

typedef struct AmigaLocalWrapperSignatureCacheEntry {
  uint8_t valid;
  size_t target_section_index;
  uint32_t target_offset;
  int result;
  PlatformLocalStackWrapperSignature signature;
} AmigaLocalWrapperSignatureCacheEntry;

typedef struct AmigaAppSlotSymbolCacheEntry {
  uint8_t valid;
  const M68kSectionAnalysisIR *section_analysis;
  int16_t displacement;
  uint8_t treat_as_value;
  int result;
  M68kSymbolRefIR symbol_ref;
} AmigaAppSlotSymbolCacheEntry;

typedef struct AmigaSectionDirectCallCacheEntry {
  uint8_t valid;
  size_t source_section_index;
  size_t target_section_index;
  int result;
} AmigaSectionDirectCallCacheEntry;

typedef struct AmigaBaseSlotIdCacheEntry {
  uint8_t valid;
  const M68kSectionAnalysisIR *section_analysis;
  int16_t displacement;
  uint16_t base_id;
} AmigaBaseSlotIdCacheEntry;

typedef struct AmigaCallEffectRegState AmigaCallEffectRegState;

typedef struct AmigaLocalSuccessSummaryWorkspace {
  const M68kSectionAnalysisIR *section_analysis;
  size_t block_count;
  AmigaCallEffectRegState *entry_states;
  uint8_t (*entry_const_known)[8];
  int32_t (*entry_const_values)[8];
  uint8_t *entry_known;
  size_t *pending;
  size_t pending_capacity;
  uint8_t in_use;
} AmigaLocalSuccessSummaryWorkspace;

typedef struct AmigaPlatformCache {
  AmigaTypedTraceCache typed_traces[AMIGA_TYPED_TRACE_CACHE_CAPACITY];
  AmigaLocalWrapperSignatureCacheEntry local_wrapper_signatures[AMIGA_LOCAL_WRAPPER_SIGNATURE_CACHE_CAPACITY];
  AmigaAppSlotSymbolCacheEntry app_slot_symbols[AMIGA_APP_SLOT_SYMBOL_CACHE_CAPACITY];
  AmigaSectionDirectCallCacheEntry section_direct_calls[AMIGA_SECTION_DIRECT_CALL_CACHE_CAPACITY];
  AmigaBaseSlotIdCacheEntry base_slot_ids[AMIGA_BASE_SLOT_ID_CACHE_CAPACITY];
  AmigaLocalSuccessSummaryWorkspace local_success_workspace;
} AmigaPlatformCache;

typedef struct AmigaSymbolProfileCounters {
  size_t app_slot_lookup_calls;
  size_t app_slot_lookup_hits;
  double app_slot_lookup_seconds;
  size_t operand_addr_resolve_calls;
  size_t operand_addr_resolve_hits;
  double operand_addr_resolve_seconds;
  size_t typed_effect_lookup_calls;
  size_t typed_effect_lookup_hits;
  double typed_effect_lookup_seconds;
  size_t next_call_input_calls;
  size_t next_call_input_hits;
  double next_call_input_seconds;
  size_t stack_push_input_calls;
  size_t stack_push_input_hits;
  double stack_push_input_seconds;
  size_t unnamed_reg_resolve_calls;
  size_t unnamed_reg_resolve_hits;
  double unnamed_reg_resolve_seconds;
  size_t app_base_symbol_calls;
  size_t app_base_symbol_hits;
  double app_base_symbol_seconds;
  size_t indirect_control_calls;
  size_t indirect_control_hits;
  double indirect_control_seconds;
  size_t indirect_library_calls;
  size_t indirect_library_hits;
  double indirect_library_seconds;
  size_t indirect_indexed_calls;
  size_t indirect_indexed_hits;
  double indirect_indexed_seconds;
  size_t indirect_callback_calls;
  size_t indirect_callback_hits;
  double indirect_callback_seconds;
} AmigaSymbolProfileCounters;

static AmigaSymbolProfileCounters g_amiga_symbol_profile_counters;
static int g_amiga_symbol_profile_registered = 0;

static int amiga_profile_enabled(void) {
  static int initialized = 0;
  static int enabled = 0;
  if (!initialized) {
    const char *value = getenv("M68K_PROFILE_AMIGA_FACTS");
    enabled = (value != NULL && value[0] != '\0' && strcmp(value, "0") != 0);
    initialized = 1;
  }
  return enabled;
}

static double amiga_profile_elapsed_seconds(clock_t start_ticks, clock_t end_ticks) {
  return ((double)(end_ticks - start_ticks)) / (double)CLOCKS_PER_SEC;
}

static void amiga_profile_log_symbol_counters(void) {
  const AmigaSymbolProfileCounters *counters = &g_amiga_symbol_profile_counters;
  if (!amiga_profile_enabled()) return;
  fprintf(stderr,
    "[amiga-profile] symbol_counts app_slot=%zu/%zu %.3fs operand_addr=%zu/%zu %.3fs "
    "typed_effect=%zu/%zu %.3fs next_call_input=%zu/%zu %.3fs stack_push=%zu/%zu %.3fs "
    "unnamed_reg=%zu/%zu %.3fs app_base_symbol=%zu/%zu %.3fs indirect=%zu/%zu %.3fs "
    "indirect_library=%zu/%zu %.3fs indirect_indexed=%zu/%zu %.3fs indirect_callback=%zu/%zu %.3fs\n",
    counters->app_slot_lookup_hits,
    counters->app_slot_lookup_calls,
    counters->app_slot_lookup_seconds,
    counters->operand_addr_resolve_hits,
    counters->operand_addr_resolve_calls,
    counters->operand_addr_resolve_seconds,
    counters->typed_effect_lookup_hits,
    counters->typed_effect_lookup_calls,
    counters->typed_effect_lookup_seconds,
    counters->next_call_input_hits,
    counters->next_call_input_calls,
    counters->next_call_input_seconds,
    counters->stack_push_input_hits,
    counters->stack_push_input_calls,
    counters->stack_push_input_seconds,
    counters->unnamed_reg_resolve_hits,
    counters->unnamed_reg_resolve_calls,
    counters->unnamed_reg_resolve_seconds,
    counters->app_base_symbol_hits,
    counters->app_base_symbol_calls,
    counters->app_base_symbol_seconds,
    counters->indirect_control_hits,
    counters->indirect_control_calls,
    counters->indirect_control_seconds,
    counters->indirect_library_hits,
    counters->indirect_library_calls,
    counters->indirect_library_seconds,
    counters->indirect_indexed_hits,
    counters->indirect_indexed_calls,
    counters->indirect_indexed_seconds,
    counters->indirect_callback_hits,
    counters->indirect_callback_calls,
    counters->indirect_callback_seconds);
}

static AmigaSymbolProfileCounters *amiga_symbol_profile_counters(void) {
  if (!amiga_profile_enabled()) return NULL;
  if (!g_amiga_symbol_profile_registered) {
    atexit(amiga_profile_log_symbol_counters);
    g_amiga_symbol_profile_registered = 1;
  }
  return &g_amiga_symbol_profile_counters;
}

static int recovered_platform_slot_displacement_lookup_has(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement) {
  uint16_t key;
  if (section_analysis == NULL || section_analysis->recovered_platform_slot_displacement_lookup == NULL ||
      section_analysis->recovered_platform_slot_displacement_lookup_size == 0U)
    return 0;
  key = (uint16_t)displacement;
  if ((size_t)(key >> 3) >= section_analysis->recovered_platform_slot_displacement_lookup_size) return 0;
  return (section_analysis->recovered_platform_slot_displacement_lookup[key >> 3] & (uint8_t)(1U << (key & 7U))) != 0U;
}

static const M68kRecoveredPlatformEffectIR *first_recovered_platform_effect_at_offset(
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  if (section_analysis == NULL || section_analysis->recovered_platform_effect_lookup == NULL ||
      offset >= section_analysis->recovered_platform_effect_lookup_size)
    return NULL;
  return section_analysis->recovered_platform_effect_lookup[offset];
}

static const M68kRecoveredPlatformEffectIR *next_recovered_platform_effect_at_same_offset(
    const M68kSectionAnalysisIR *section_analysis, const M68kRecoveredPlatformEffectIR *effect) {
  size_t index;
  uint32_t next_index;
  if (section_analysis == NULL || effect == NULL || section_analysis->recovered_platform_effects == NULL ||
      section_analysis->recovered_platform_effect_next_lookup == NULL)
    return NULL;
  index = (size_t)(effect - section_analysis->recovered_platform_effects);
  if (index >= section_analysis->recovered_platform_effect_count ||
      index >= section_analysis->recovered_platform_effect_next_lookup_size)
    return NULL;
  next_index = section_analysis->recovered_platform_effect_next_lookup[index];
  if (next_index == UINT32_MAX || next_index >= section_analysis->recovered_platform_effect_count) return NULL;
  return &section_analysis->recovered_platform_effects[next_index];
}

struct AmigaCallEffectRegState {
  uint16_t data_reg_base_ids[8];
  uint16_t addr_reg_base_ids[8];
  AmigaValueProvenance data_reg_values[8];
  AmigaValueProvenance addr_reg_values[8];
};

typedef struct AmigaLocalSuccessSummaryCacheEntry {
  uint8_t state;
  AmigaCallEffectRegState reg_state;
} AmigaLocalSuccessSummaryCacheEntry;

static void format_amiga_slot_struct_type_name(char *buf, size_t buf_size, int16_t displacement);
static void format_amiga_typed_slot_symbol_name(char *buf, size_t buf_size, const char *type_name);
static void format_amiga_typed_slot_symbol_name_for_disp(char *buf, size_t buf_size, const char *type_name,
    int16_t displacement);
static int format_amiga_named_typed_slot_symbol_name(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement, char *buf, size_t buf_size);
static int resolve_amiga_struct_field_symbol_name(const char *type_name, int16_t displacement, char *buf, size_t buf_size);
static const char *resolve_amiga_struct_field_nested_type_name(const char *type_name, int16_t displacement);
static void populate_amiga_callback_field_note_symbol(PlatformResolvedIndirectInfo *out_info);
static int resolve_amiga_address_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedAddressRegInfo *out_info);
static int resolve_amiga_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedDataRegInfo *out_info);
static int resolve_preceding_move_source_data_reg(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t dest_reg, uint8_t *out_source_reg);
static int resolve_preceding_field_loaded_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t data_reg, AmigaResolvedDataRegInfo *out_info);
static int resolve_preceding_stack_reloaded_address_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedAddressRegInfo *out_info);
static uint32_t find_amiga_typed_trace_fallback_start(const SectionAnalysisContext *ctx, uint32_t offset);
static int section_analysis_has_amiga_structural_slot_use(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement);
static int load_amiga_recovered_local_success_summary_state(const M68kSectionAnalysisIR *section_analysis,
    uint32_t target_offset, AmigaCallEffectRegState *out_state);
static int summarize_amiga_direct_local_success_outputs_at(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index, uint32_t target_offset,
    AmigaLocalSuccessSummaryCacheEntry *same_section_cache, size_t same_section_cache_count,
    AmigaCallEffectRegState *out_summary);
static int resolve_amiga_local_wrapper_signature(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index, uint32_t target_offset,
    PlatformLocalStackWrapperSignature *out_signature);
static int resolve_amiga_stack_push_wrapper_input(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    size_t *out_operand_index, const AmigaOsCallInputInfo **out_input_info, uint16_t *out_stack_offset);
static int instruction_preserves_pointer_provenance_local(const M68kInstructionIR *instruction, uint8_t reg_kind,
    uint8_t reg_index);
static int operand_address_reg_index_local(const M68kOperandIR *operand, uint8_t *out_reg);
static int operand_data_reg_index_local(const M68kOperandIR *operand, uint8_t *out_reg);
static int operand_is_immediate_source_local(const M68kOperandIR *operand);
static int instruction_pushes_data_reg_to_stack_local(const M68kInstructionIR *instruction, uint8_t *out_reg);
static int instruction_pops_data_reg_from_stack_local(const M68kInstructionIR *instruction, uint8_t *out_reg);
static int instruction_pushes_movem_to_stack_local(const M68kInstructionIR *instruction, uint16_t *out_mask);
static int instruction_pops_movem_from_stack_local(const M68kInstructionIR *instruction, uint16_t *out_mask);
static void init_amiga_typed_stack_entry(AmigaTypedStackEntry *entry);
static void clear_amiga_typed_local_slot_entry(AmigaTypedLocalSlotEntry *entry);
static int operand_is_amiga_local_frame_slot(const M68kOperandIR *operand, const uint16_t *local_base_ids,
    uint8_t *out_base_reg, uint16_t *out_base_id, int16_t *out_displacement);
static int instruction_is_register_to_local_frame_slot_store(const M68kInstructionIR *instruction,
    const uint16_t *local_base_ids, uint8_t *out_source_kind, uint8_t *out_source_reg, uint16_t *out_base_id,
    int16_t *out_displacement);
static int instruction_is_register_to_resolved_app_slot_store(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    uint8_t *out_source_kind, uint8_t *out_source_reg, int16_t *out_displacement);
static void init_amiga_resolved_target(AmigaResolvedTarget *value);
static void clear_amiga_target_local_slot_entry(AmigaTargetLocalSlotEntry *entry);
static void clear_amiga_target_local_slots_for_base(AmigaTargetLocalSlotEntry *slots, size_t slot_count, uint16_t base_id);
static void set_amiga_target_local_slot_entry(AmigaTargetLocalSlotEntry *slots, size_t slot_count, uint16_t base_id,
    int16_t displacement, const AmigaResolvedTarget *value);
static int lookup_amiga_target_local_slot_entry(const AmigaTargetLocalSlotEntry *slots, size_t slot_count, uint16_t base_id,
    int16_t displacement, AmigaResolvedTarget *out_value);
static int resolve_amiga_absolute_target_from_operand(const SectionAnalysisContext *ctx, uint32_t offset,
    const M68kInstructionIR *instruction, const M68kOperandIR *operand, size_t operand_index, uint32_t *out_target);
static int resolve_amiga_pre_call_absolute_target(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t call_offset, uint8_t reg_kind, uint8_t reg_index,
    uint32_t *out_target);
static int has_recovered_amiga_app_slot_displacement(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement);
static int format_amiga_value_domain_symbolic_value(const char *domain_name, int32_t value, char *buf, size_t buf_size);
static AmigaPlatformCache *amiga_platform_cache_for_ctx(const SectionAnalysisContext *ctx);
static AmigaSectionDirectCallCacheEntry *amiga_section_direct_call_cache_find(AmigaPlatformCache *cache,
    size_t source_section_index, size_t target_section_index, int *out_found);
static uint16_t lookup_recovered_platform_base_slot_id_cached(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement);
static uint32_t next_amiga_platform_fact_code_offset(const M68kSectionAnalysisIR *section_analysis,
    uint32_t start_offset, uint32_t section_size);
typedef int (*AmigaDirectCallVisitFn)(const SectionAnalysisContext *source_ctx,
    const M68kSectionAnalysisIR *source_analysis, uint32_t source_offset, uint32_t target_offset,
    void *user_data);
static int scan_amiga_source_section_direct_calls_to_target(const SectionAnalysisContext *ctx,
    size_t source_section_index, size_t target_section_index, int stop_after_first,
    AmigaDirectCallVisitFn visit, void *user_data, int *out_found);
static int acquire_amiga_local_success_summary_workspace(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, AmigaLocalSuccessSummaryWorkspace *temp_workspace,
    AmigaLocalSuccessSummaryWorkspace **out_workspace, int *out_is_temp);
static void release_amiga_local_success_summary_workspace(AmigaPlatformCache *cache,
    AmigaLocalSuccessSummaryWorkspace *workspace, int is_temp);
static const AmigaOsLibraryVectorInfo *resolve_amiga_library_vector_entry(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
static const char *resolve_preceding_stack_reloaded_base_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg);
static void init_amiga_value_provenance(AmigaValueProvenance *value);
static int amiga_value_provenance_has_any_info(const AmigaValueProvenance *value);
static void init_amiga_base_slot_tag_array(AmigaBaseSlotTag *slots, size_t slot_count);
static void init_amiga_absolute_base_slot_tag_array(AmigaAbsoluteBaseSlotTag *slots, size_t slot_count);
static void init_amiga_base_id_array(uint16_t *ids, size_t count);
static void init_amiga_typed_slot_tag_array(AmigaTypedSlotTag *slots, size_t slot_count);
static void init_amiga_absolute_typed_slot_tag_array(AmigaAbsoluteTypedSlotTag *slots, size_t slot_count);
static uint16_t amiga_base_id_from_name_local(const char *base_name);
static const char *amiga_base_name_from_id_local(uint16_t base_id);
static int amiga_base_id_is_app_local(uint16_t base_id);
static const char *resolve_amiga_base_type_name_from_id_local(uint16_t base_id);
static const char *amiga_type_or_struct_name_local(uint16_t type_id, uint16_t struct_id);
static const char *amiga_value_provenance_type_name_local(const AmigaValueProvenance *value);
static const char *amiga_value_provenance_owner_type_name_local(const AmigaValueProvenance *value);
static const char *amiga_value_provenance_semantic_kind_local(const AmigaValueProvenance *value);
static const char *amiga_value_provenance_value_domain_name_local(const AmigaValueProvenance *value);
static const char *amiga_value_provenance_field_symbol_name_local(const AmigaValueProvenance *value);
static void amiga_value_provenance_set_type_name(AmigaValueProvenance *value, const char *type_name);
static void amiga_value_provenance_set_type_id(AmigaValueProvenance *value, uint16_t type_id);
static void amiga_value_provenance_set_struct_id(AmigaValueProvenance *value, uint16_t struct_id);
static void amiga_value_provenance_set_owner_type_name(AmigaValueProvenance *value, const char *type_name);
static void amiga_value_provenance_set_owner_type_id(AmigaValueProvenance *value, uint16_t type_id);
static void amiga_value_provenance_set_owner_struct_id(AmigaValueProvenance *value, uint16_t struct_id);
static void amiga_value_provenance_copy_owner_from_type(AmigaValueProvenance *dst, const AmigaValueProvenance *src);
static void amiga_value_provenance_set_symbol_name(AmigaValueProvenance *value, const char *symbol_name);
static void amiga_value_provenance_set_symbol_id(AmigaValueProvenance *value, uint16_t symbol_id);
static void amiga_value_provenance_set_context_base_id(AmigaValueProvenance *value, uint16_t base_id);
static void amiga_value_provenance_set_semantic_kind_name(AmigaValueProvenance *value, const char *semantic_kind);
static void amiga_value_provenance_set_semantic_kind_id(AmigaValueProvenance *value, uint16_t semantic_kind_id);
static void amiga_value_provenance_set_value_domain_name(AmigaValueProvenance *value, const char *value_domain_name);
static void amiga_value_provenance_set_value_domain_id(AmigaValueProvenance *value, uint16_t value_domain_id);
static void amiga_value_provenance_set_field_symbol_name(AmigaValueProvenance *value, const char *field_symbol_name);
static void amiga_value_provenance_set_field_symbol_id(AmigaValueProvenance *value, uint16_t field_symbol_id);
static uint32_t amiga_type_ref_key_local(uint16_t type_id, uint16_t struct_id);
static uint16_t amiga_named_base_payload_id_local(const M68kPlatformNamedBaseEffectPayloadIR *payload);
static uint16_t amiga_typed_payload_type_id_local(const M68kPlatformTypedEffectPayloadIR *payload);
static uint16_t amiga_typed_payload_semantic_kind_id_local(const M68kPlatformTypedEffectPayloadIR *payload);
static uint16_t amiga_typed_payload_value_domain_id_local(const M68kPlatformTypedEffectPayloadIR *payload);
static int amiga_typed_payload_has_any_info_local(const M68kPlatformTypedEffectPayloadIR *payload);
static void amiga_typed_payload_apply_to_value_local(AmigaValueProvenance *value,
    const M68kPlatformTypedEffectPayloadIR *payload);
static void amiga_call_effect_reg_state_set_base_id(AmigaCallEffectRegState *state, uint8_t reg_kind, uint8_t reg_index,
    uint16_t base_id);
static void amiga_call_effect_reg_state_clear_base(AmigaCallEffectRegState *state, uint8_t reg_kind, uint8_t reg_index);
static int amiga_call_effect_reg_state_has_any_info(const AmigaCallEffectRegState *state);
static uint16_t lookup_amiga_base_slot_id_local(const AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement);
static void set_amiga_base_slot_id_local(AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement, uint16_t base_id);
static uint16_t lookup_amiga_absolute_base_slot_id_local(const AmigaAbsoluteBaseSlotTag *slots, size_t slot_count,
    size_t section_index, uint32_t target_offset);
static void set_amiga_absolute_base_slot_id_local(AmigaAbsoluteBaseSlotTag *slots, size_t slot_count,
    size_t section_index, uint32_t target_offset, uint16_t base_id);
static uint16_t lookup_amiga_global_base_slot_id_local(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index, uint32_t target_offset);
static int lookup_amiga_global_typed_slot_value_local(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index, uint32_t target_offset,
    AmigaValueProvenance *out_value);
static void seed_amiga_absolute_base_slots_before_offset(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t before_offset, AmigaAbsoluteBaseSlotTag *absolute_base_slots,
    size_t absolute_base_slot_count);
static uint16_t lookup_recovered_platform_base_slot_id_local(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement);
static uint16_t lookup_amiga_app_slot_base_id_for_operand(const M68kSectionAnalysisIR *section_analysis,
    const AmigaBaseSlotTag *slot_base_names, size_t slot_base_count, const M68kOperandIR *operand,
    uint16_t current_a6_base_id, int16_t *out_displacement);

static const char *amiga_struct_field_name(const AmigaOsStructFieldInfo *field) {
  return field != NULL ? amiga_os_name(M68K_PLATFORM_NAME_FIELD, field->field_id) : NULL;
}

static const char *amiga_struct_field_nested_type_name(const AmigaOsStructFieldInfo *field) {
  return field != NULL ? amiga_os_name(M68K_PLATFORM_NAME_TYPE, field->nested_type_id) : NULL;
}

static const char *amiga_value_domain_member_name(const AmigaOsValueDomainMemberInfo *member) {
  return member != NULL ? amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, member->name_id) : NULL;
}

static const char *amiga_value_domain_zero_name(const AmigaOsValueDomainInfo *domain) {
  return domain != NULL ? amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, domain->zero_name_id) : NULL;
}

static uint16_t amiga_base_id_from_name_local(const char *base_name) {
  if (base_name == NULL || base_name[0] == '\0') return AMIGA_OS_BASE_ID_NONE;
  if (strcmp(base_name, AMIGA_APP_BASE_TAG) == 0) return AMIGA_LOCAL_BASE_ID_APP;
  return amiga_os_name_id(M68K_PLATFORM_NAME_BASE, base_name);
}

static const char *amiga_base_name_from_id_local(uint16_t base_id) {
  if (base_id == AMIGA_LOCAL_BASE_ID_APP) return AMIGA_APP_BASE_TAG;
  return amiga_os_name(M68K_PLATFORM_NAME_BASE, base_id);
}

static int amiga_base_id_is_app_local(uint16_t base_id) {
  return base_id == AMIGA_LOCAL_BASE_ID_APP;
}

static int amiga_base_id_is_none_local(uint16_t base_id) {
  return base_id != AMIGA_LOCAL_BASE_ID_APP && amiga_os_name(M68K_PLATFORM_NAME_BASE, base_id) == NULL;
}

static const char *resolve_amiga_base_type_name_from_id_local(uint16_t base_id) {
  return (amiga_base_id_is_none_local(base_id) || amiga_base_id_is_app_local(base_id)) ? NULL : "LIB";
}

static const char *amiga_type_or_struct_name_local(uint16_t type_id, uint16_t struct_id) {
  const char *name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, type_id);
  if (name != NULL) return name;
  return amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id);
}

static const char *amiga_value_provenance_type_name_local(const AmigaValueProvenance *value) {
  if (value == NULL) return NULL;
  return amiga_type_or_struct_name_local(value->type_id, value->struct_id);
}

static const char *amiga_value_provenance_owner_type_name_local(const AmigaValueProvenance *value) {
  if (value == NULL) return NULL;
  return amiga_type_or_struct_name_local(value->owner_type_id, value->owner_struct_id);
}

static const char *amiga_value_provenance_semantic_kind_local(const AmigaValueProvenance *value) {
  if (value == NULL) return NULL;
  return amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, value->semantic_kind_id);
}

static const char *amiga_value_provenance_value_domain_name_local(const AmigaValueProvenance *value) {
  if (value == NULL) return NULL;
  return amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, value->value_domain_id);
}

static const char *amiga_value_provenance_field_symbol_name_local(const AmigaValueProvenance *value) {
  if (value == NULL) return NULL;
  return amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, value->field_symbol_id);
}

static void amiga_value_provenance_set_type_name(AmigaValueProvenance *value, const char *type_name) {
  if (value == NULL) return;
  value->type_id = amiga_os_name_id(M68K_PLATFORM_NAME_TYPE, type_name);
  value->struct_id = AMIGA_OS_STRUCT_ID_NONE;
}

static void amiga_value_provenance_set_type_id(AmigaValueProvenance *value, uint16_t type_id) {
  if (value == NULL) return;
  value->type_id = type_id;
  value->struct_id = AMIGA_OS_STRUCT_ID_NONE;
}

static void amiga_value_provenance_set_struct_id(AmigaValueProvenance *value, uint16_t struct_id) {
  const char *struct_name;
  if (value == NULL) return;
  struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id);
  value->struct_id = struct_id;
  value->type_id = amiga_os_name_id(M68K_PLATFORM_NAME_TYPE, struct_name);
}

static void amiga_value_provenance_set_owner_type_name(AmigaValueProvenance *value, const char *type_name) {
  if (value == NULL) return;
  value->owner_type_id = amiga_os_name_id(M68K_PLATFORM_NAME_TYPE, type_name);
  value->owner_struct_id = AMIGA_OS_STRUCT_ID_NONE;
}

static void amiga_value_provenance_set_owner_type_id(AmigaValueProvenance *value, uint16_t type_id) {
  if (value == NULL) return;
  value->owner_type_id = type_id;
  value->owner_struct_id = AMIGA_OS_STRUCT_ID_NONE;
}

static void amiga_value_provenance_set_owner_struct_id(AmigaValueProvenance *value, uint16_t struct_id) {
  const char *struct_name;
  if (value == NULL) return;
  struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id);
  value->owner_struct_id = struct_id;
  value->owner_type_id = amiga_os_name_id(M68K_PLATFORM_NAME_TYPE, struct_name);
}

static void amiga_value_provenance_copy_owner_from_type(AmigaValueProvenance *dst, const AmigaValueProvenance *src) {
  if (dst == NULL || src == NULL) return;
  if (amiga_os_name(M68K_PLATFORM_NAME_TYPE, src->type_id) != NULL)
    amiga_value_provenance_set_owner_type_id(dst, src->type_id);
  else if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, src->struct_id) != NULL)
    amiga_value_provenance_set_owner_struct_id(dst, src->struct_id);
  else amiga_value_provenance_set_owner_type_name(dst, amiga_value_provenance_type_name_local(src));
}

static void amiga_value_provenance_set_symbol_name(AmigaValueProvenance *value, const char *symbol_name) {
  if (value == NULL) return;
  value->symbol_id = amiga_os_name_id(M68K_PLATFORM_NAME_SYMBOL, symbol_name);
}

static void amiga_value_provenance_set_symbol_id(AmigaValueProvenance *value, uint16_t symbol_id) {
  if (value == NULL) return;
  value->symbol_id = symbol_id;
}

static void amiga_value_provenance_set_context_base_id(AmigaValueProvenance *value, uint16_t base_id) {
  if (value == NULL) return;
  value->context_base_id = base_id;
}

static void amiga_value_provenance_set_semantic_kind_name(AmigaValueProvenance *value, const char *semantic_kind) {
  if (value == NULL) return;
  value->semantic_kind_id = amiga_os_name_id(M68K_PLATFORM_NAME_SEMANTIC_KIND, semantic_kind);
}

static void amiga_value_provenance_set_semantic_kind_id(AmigaValueProvenance *value, uint16_t semantic_kind_id) {
  if (value == NULL) return;
  value->semantic_kind_id = semantic_kind_id;
}

static void amiga_value_provenance_set_value_domain_name(AmigaValueProvenance *value, const char *value_domain_name) {
  if (value == NULL) return;
  value->value_domain_id = amiga_os_name_id(M68K_PLATFORM_NAME_VALUE_DOMAIN, value_domain_name);
}

static void amiga_value_provenance_set_value_domain_id(AmigaValueProvenance *value, uint16_t value_domain_id) {
  if (value == NULL) return;
  value->value_domain_id = value_domain_id;
}

static void amiga_value_provenance_set_field_symbol_name(AmigaValueProvenance *value, const char *field_symbol_name) {
  if (value == NULL) return;
  value->field_symbol_id = amiga_os_name_id(M68K_PLATFORM_NAME_SYMBOL, field_symbol_name);
}

static void amiga_value_provenance_set_field_symbol_id(AmigaValueProvenance *value, uint16_t field_symbol_id) {
  if (value == NULL) return;
  value->field_symbol_id = field_symbol_id;
}

static uint32_t amiga_type_ref_key_local(uint16_t type_id, uint16_t struct_id) {
  if (amiga_os_name(M68K_PLATFORM_NAME_TYPE, type_id) != NULL)
    return ((uint32_t)M68K_PLATFORM_NAME_TYPE << 16) | (uint32_t)type_id;
  if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) != NULL)
    return ((uint32_t)M68K_PLATFORM_NAME_STRUCT << 16) | (uint32_t)struct_id;
  return 0U;
}

static uint16_t amiga_named_base_payload_id_local(const M68kPlatformNamedBaseEffectPayloadIR *payload) {
  if (payload == NULL) return AMIGA_OS_BASE_ID_NONE;
  if (m68k_platform_name_ref_is_set(&payload->base_ref)) return payload->base_ref.id;
  return amiga_base_id_from_name_local(payload->base_name);
}

static uint16_t amiga_typed_payload_type_id_local(const M68kPlatformTypedEffectPayloadIR *payload) {
  if (payload == NULL) return AMIGA_OS_TYPE_ID_NONE;
  if (m68k_platform_name_ref_is_set(&payload->type_ref)) return payload->type_ref.id;
  return amiga_os_name_id(M68K_PLATFORM_NAME_TYPE, payload->type_name);
}

static uint16_t amiga_typed_payload_semantic_kind_id_local(const M68kPlatformTypedEffectPayloadIR *payload) {
  if (payload == NULL) return AMIGA_OS_SEMANTIC_KIND_ID_NONE;
  if (m68k_platform_name_ref_is_set(&payload->semantic_kind_ref)) return payload->semantic_kind_ref.id;
  return amiga_os_name_id(M68K_PLATFORM_NAME_SEMANTIC_KIND, payload->semantic_kind);
}

static uint16_t amiga_typed_payload_value_domain_id_local(const M68kPlatformTypedEffectPayloadIR *payload) {
  if (payload == NULL) return AMIGA_OS_VALUE_DOMAIN_ID_NONE;
  if (m68k_platform_name_ref_is_set(&payload->value_domain_ref)) return payload->value_domain_ref.id;
  return amiga_os_name_id(M68K_PLATFORM_NAME_VALUE_DOMAIN, payload->value_domain_name);
}

static uint16_t amiga_typed_payload_symbol_id_local(const M68kPlatformTypedEffectPayloadIR *payload) {
  if (payload == NULL) return AMIGA_OS_SYMBOL_ID_NONE;
  if (m68k_platform_name_ref_is_set(&payload->symbol_ref)) return payload->symbol_ref.id;
  return amiga_os_name_id(M68K_PLATFORM_NAME_SYMBOL, payload->symbol_name);
}

static uint16_t amiga_typed_payload_context_base_id_local(const M68kPlatformTypedEffectPayloadIR *payload) {
  if (payload == NULL) return AMIGA_OS_BASE_ID_NONE;
  if (m68k_platform_name_ref_is_set(&payload->context_ref)) return payload->context_ref.id;
  return amiga_base_id_from_name_local(payload->context_name);
}

static int amiga_typed_payload_has_any_info_local(const M68kPlatformTypedEffectPayloadIR *payload) {
  if (payload == NULL) return 0;
  return amiga_os_name(M68K_PLATFORM_NAME_TYPE, amiga_typed_payload_type_id_local(payload)) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, amiga_typed_payload_symbol_id_local(payload)) != NULL ||
    !amiga_base_id_is_none_local(amiga_typed_payload_context_base_id_local(payload)) ||
    amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, amiga_typed_payload_semantic_kind_id_local(payload)) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, amiga_typed_payload_value_domain_id_local(payload)) != NULL ||
    payload->has_constant_value;
}

static void amiga_typed_payload_apply_to_value_local(AmigaValueProvenance *value,
    const M68kPlatformTypedEffectPayloadIR *payload) {
  uint16_t type_id;
  uint16_t symbol_id;
  uint16_t context_base_id;
  uint16_t semantic_kind_id;
  uint16_t value_domain_id;
  if (value == NULL || payload == NULL) return;
  type_id = amiga_typed_payload_type_id_local(payload);
  symbol_id = amiga_typed_payload_symbol_id_local(payload);
  context_base_id = amiga_typed_payload_context_base_id_local(payload);
  semantic_kind_id = amiga_typed_payload_semantic_kind_id_local(payload);
  value_domain_id = amiga_typed_payload_value_domain_id_local(payload);
  if (amiga_os_name(M68K_PLATFORM_NAME_TYPE, type_id) != NULL) {
    amiga_value_provenance_set_type_id(value, type_id);
    amiga_value_provenance_set_owner_type_id(value, type_id);
  }
  if (amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, symbol_id) != NULL)
    amiga_value_provenance_set_symbol_id(value, symbol_id);
  if (!amiga_base_id_is_none_local(context_base_id))
    amiga_value_provenance_set_context_base_id(value, context_base_id);
  if (amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, semantic_kind_id) != NULL)
    amiga_value_provenance_set_semantic_kind_id(value, semantic_kind_id);
  if (amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, value_domain_id) != NULL)
    amiga_value_provenance_set_value_domain_id(value, value_domain_id);
  value->has_constant_value = payload->has_constant_value;
  value->constant_value = payload->constant_value;
}

static void amiga_call_effect_reg_state_set_base_id(AmigaCallEffectRegState *state, uint8_t reg_kind, uint8_t reg_index,
    uint16_t base_id) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) {
    state->data_reg_base_ids[reg_index] = base_id;
  } else if (reg_kind == 2U) {
    state->addr_reg_base_ids[reg_index] = base_id;
  }
}

static void amiga_call_effect_reg_state_clear_base(AmigaCallEffectRegState *state, uint8_t reg_kind, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) {
    state->data_reg_base_ids[reg_index] = AMIGA_OS_BASE_ID_NONE;
  } else if (reg_kind == 2U) {
    state->addr_reg_base_ids[reg_index] = AMIGA_OS_BASE_ID_NONE;
  }
}

const char *read_amiga_library_seed_name(const M68kSection *section, uint32_t target) {
  size_t end;
  if (section == NULL || target >= section->data_size) return NULL;
  end = target;
  while (end < section->data_size && end - target < 64U) {
    uint8_t ch = section->data[end];
    if (ch == 0U) break;
    if (ch < 32U || ch > 126U) return NULL;
    ++end;
  }
  if (end >= section->data_size || section->data[end] != 0U || end == target) return NULL;
  return amiga_os_find_library_base_name((const char *)(section->data + target));
}

static const char *read_amiga_library_seed_name_near(const M68kSection *section, uint32_t target) {
  static const int deltas[] = {0, -2, 2, -4, 4};
  size_t index;
  if (section == NULL) return NULL;
  for (index = 0U; index < sizeof(deltas) / sizeof(deltas[0]); ++index) {
    int32_t candidate = (int32_t)target + deltas[index];
    const char *name;
    if (candidate < 0 || (uint32_t)candidate >= section->data_size) continue;
    name = read_amiga_library_seed_name(section, (uint32_t)candidate);
    if (name != NULL) return name;
  }
  return NULL;
}

void set_amiga_base_slot_tag(AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement, const char *base_name) {
  set_amiga_base_slot_id_local(slots, slot_count, displacement, amiga_base_id_from_name_local(base_name));
}

const char *lookup_amiga_base_slot_tag(const AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement) {
  return amiga_base_name_from_id_local(lookup_amiga_base_slot_id_local(slots, slot_count, displacement));
}

static uint16_t lookup_amiga_base_slot_id_local(const AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement) {
  size_t index;
  if (slots == NULL) return AMIGA_OS_BASE_ID_NONE;
  for (index = 0; index < slot_count; ++index) {
    if (!amiga_base_id_is_none_local(slots[index].base_id) && slots[index].displacement == displacement)
      return slots[index].base_id;
  }
  return AMIGA_OS_BASE_ID_NONE;
}

static void set_amiga_base_slot_id_local(AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement, uint16_t base_id) {
  size_t index;
  if (slots == NULL || amiga_base_id_is_none_local(base_id) || amiga_base_id_is_app_local(base_id)) return;
  for (index = 0; index < slot_count; ++index) {
    if (amiga_base_id_is_none_local(slots[index].base_id) || slots[index].displacement == displacement) {
      slots[index].displacement = displacement;
      slots[index].base_id = base_id;
      return;
    }
  }
}

static void init_amiga_absolute_base_slot_tag_array(AmigaAbsoluteBaseSlotTag *slots, size_t slot_count) {
  size_t index;
  if (slots == NULL) return;
  for (index = 0U; index < slot_count; ++index) {
    slots[index].section_index = SIZE_MAX;
    slots[index].target_offset = UINT32_MAX;
    slots[index].base_id = AMIGA_OS_BASE_ID_NONE;
  }
}

static uint16_t lookup_amiga_absolute_base_slot_id_local(const AmigaAbsoluteBaseSlotTag *slots, size_t slot_count,
    size_t section_index, uint32_t target_offset) {
  size_t index;
  if (slots == NULL || section_index == SIZE_MAX || target_offset == UINT32_MAX) return AMIGA_OS_BASE_ID_NONE;
  for (index = 0U; index < slot_count; ++index) {
    if (!amiga_base_id_is_none_local(slots[index].base_id) && slots[index].section_index == section_index &&
        slots[index].target_offset == target_offset)
      return slots[index].base_id;
  }
  return AMIGA_OS_BASE_ID_NONE;
}

static void set_amiga_absolute_base_slot_id_local(AmigaAbsoluteBaseSlotTag *slots, size_t slot_count,
    size_t section_index, uint32_t target_offset, uint16_t base_id) {
  size_t index;
  if (slots == NULL || section_index == SIZE_MAX || target_offset == UINT32_MAX ||
      amiga_base_id_is_none_local(base_id) || amiga_base_id_is_app_local(base_id)) return;
  for (index = 0U; index < slot_count; ++index) {
    if (amiga_base_id_is_none_local(slots[index].base_id) ||
        (slots[index].section_index == section_index && slots[index].target_offset == target_offset)) {
      slots[index].section_index = section_index;
      slots[index].target_offset = target_offset;
      slots[index].base_id = base_id;
      return;
    }
  }
}

static void init_amiga_absolute_typed_slot_tag_array(AmigaAbsoluteTypedSlotTag *slots, size_t slot_count) {
  size_t index;
  if (slots == NULL) return;
  for (index = 0U; index < slot_count; ++index) {
    slots[index].section_index = SIZE_MAX;
    slots[index].target_offset = UINT32_MAX;
    init_amiga_value_provenance(&slots[index].value);
  }
}

static int lookup_amiga_absolute_typed_slot_value_local(const AmigaAbsoluteTypedSlotTag *slots, size_t slot_count,
    size_t section_index, uint32_t target_offset, AmigaValueProvenance *out_value) {
  size_t index;
  if (out_value != NULL) init_amiga_value_provenance(out_value);
  if (slots == NULL || section_index == SIZE_MAX || target_offset == UINT32_MAX || out_value == NULL) return 0;
  for (index = 0U; index < slot_count; ++index) {
    if (slots[index].section_index == section_index && slots[index].target_offset == target_offset &&
        amiga_value_provenance_has_any_info(&slots[index].value)) {
      *out_value = slots[index].value;
      return 1;
    }
  }
  return 0;
}

static void set_amiga_absolute_typed_slot_value_local(AmigaAbsoluteTypedSlotTag *slots, size_t slot_count,
    size_t section_index, uint32_t target_offset, const AmigaValueProvenance *value) {
  size_t index;
  if (slots == NULL || section_index == SIZE_MAX || target_offset == UINT32_MAX || value == NULL ||
      !amiga_value_provenance_has_any_info(value)) return;
  for (index = 0U; index < slot_count; ++index) {
    if (!amiga_value_provenance_has_any_info(&slots[index].value) ||
        (slots[index].section_index == section_index && slots[index].target_offset == target_offset)) {
      slots[index].section_index = section_index;
      slots[index].target_offset = target_offset;
      slots[index].value = *value;
      return;
    }
  }
}

static uint16_t lookup_amiga_global_base_slot_effect_id_local(const M68kSectionAnalysisIR *section_analysis,
    size_t target_section_index, uint32_t target_offset) {
  size_t index;
  if (section_analysis == NULL || target_section_index == SIZE_MAX || target_offset == UINT32_MAX)
    return AMIGA_OS_BASE_ID_NONE;
  for (index = 0U; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT ||
        effect->target_section_index != target_section_index || effect->target_offset != target_offset)
      continue;
    if (!amiga_base_id_is_none_local(effect->payload.named_base.base_ref.id))
      return effect->payload.named_base.base_ref.id;
    return amiga_base_id_from_name_local(effect->payload.named_base.base_name);
  }
  return AMIGA_OS_BASE_ID_NONE;
}

static uint16_t lookup_amiga_global_base_slot_id_local(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index, uint32_t target_offset) {
  size_t current_section_index = section_analysis_context_section_index(ctx);
  uint16_t base_id;
  const M68kSectionAnalysisIR *prior;
  if (ctx == NULL || target_section_index == SIZE_MAX || target_offset == UINT32_MAX) return AMIGA_OS_BASE_ID_NONE;
  if (target_section_index == current_section_index) {
    base_id = lookup_amiga_global_base_slot_effect_id_local(section_analysis, target_section_index, target_offset);
    if (!amiga_base_id_is_none_local(base_id)) return base_id;
  }
  prior = section_analysis_context_prior_section_analysis(ctx, target_section_index);
  return lookup_amiga_global_base_slot_effect_id_local(prior, target_section_index, target_offset);
}

static int lookup_amiga_global_typed_slot_effect_value_local(const M68kSectionAnalysisIR *section_analysis,
    size_t target_section_index, uint32_t target_offset, AmigaValueProvenance *out_value) {
  size_t index;
  if (out_value != NULL) init_amiga_value_provenance(out_value);
  if (section_analysis == NULL || target_section_index == SIZE_MAX || target_offset == UINT32_MAX ||
      out_value == NULL) {
    return 0;
  }
  for (index = 0U; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT ||
        effect->target_section_index != target_section_index || effect->target_offset != target_offset ||
        !amiga_typed_payload_has_any_info_local(&effect->payload.typed)) {
      continue;
    }
    amiga_typed_payload_apply_to_value_local(out_value, &effect->payload.typed);
    out_value->source_offset = effect->offset;
    out_value->field_disp = effect->field_disp;
    return amiga_value_provenance_has_any_info(out_value);
  }
  return 0;
}

static int lookup_amiga_global_typed_slot_value_local(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index, uint32_t target_offset,
    AmigaValueProvenance *out_value) {
  size_t current_section_index;
  const M68kSectionAnalysisIR *prior;
  if (out_value != NULL) init_amiga_value_provenance(out_value);
  if (ctx == NULL || section_analysis == NULL || target_section_index == SIZE_MAX ||
      target_offset == UINT32_MAX || out_value == NULL) {
    return 0;
  }
  current_section_index = section_analysis_context_section_index(ctx);
  if (target_section_index == current_section_index) return 0;
  prior = section_analysis_context_prior_section_analysis(ctx, target_section_index);
  return lookup_amiga_global_typed_slot_effect_value_local(prior, target_section_index, target_offset, out_value);
}

static uint16_t resolve_amiga_absolute_base_operand_id_local(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, const AmigaAbsoluteBaseSlotTag *absolute_base_slots,
    size_t absolute_base_slot_count, const M68kInstructionIR *instruction, size_t operand_index,
    uint32_t instruction_offset, int include_library_seed) {
  const M68kObject *object = section_analysis_context_object(ctx);
  size_t target_section_index = SIZE_MAX;
  uint32_t target_offset = UINT32_MAX;
  uint16_t base_id;
  if (!instruction_operand_absolute_target_ref(ctx, instruction, operand_index, instruction_offset,
        &target_section_index, &target_offset))
    return AMIGA_OS_BASE_ID_NONE;
  base_id = lookup_amiga_absolute_base_slot_id_local(absolute_base_slots, absolute_base_slot_count,
    target_section_index, target_offset);
  if (!amiga_base_id_is_none_local(base_id)) return base_id;
  base_id = lookup_amiga_global_base_slot_id_local(ctx, section_analysis, target_section_index, target_offset);
  if (!amiga_base_id_is_none_local(base_id)) return base_id;
  if (include_library_seed && object != NULL && target_section_index < object->section_count) {
    return amiga_base_id_from_name_local(read_amiga_library_seed_name_near(&object->sections[target_section_index],
      target_offset));
  }
  return AMIGA_OS_BASE_ID_NONE;
}

static void set_amiga_typed_slot_tag(AmigaTypedSlotTag *slots, size_t slot_count, int16_t displacement,
    const AmigaValueProvenance *value) {
  size_t index;
  if (slots == NULL || value == NULL ||
      (amiga_value_provenance_type_name_local(value) == NULL &&
       amiga_value_provenance_semantic_kind_local(value) == NULL &&
       amiga_value_provenance_value_domain_name_local(value) == NULL &&
       !value->has_constant_value)) return;
  for (index = 0; index < slot_count; ++index) {
    if (!amiga_value_provenance_has_any_info(&slots[index].value) || slots[index].displacement == displacement) {
      slots[index].displacement = displacement;
      slots[index].value = *value;
      return;
    }
  }
}

static const AmigaValueProvenance *lookup_amiga_typed_slot_tag(const AmigaTypedSlotTag *slots, size_t slot_count,
    int16_t displacement) {
  size_t index;
  if (slots == NULL) return NULL;
  for (index = 0; index < slot_count; ++index) {
    if (amiga_value_provenance_has_any_info(&slots[index].value) && slots[index].displacement == displacement)
      return &slots[index].value;
  }
  return NULL;
}

static void seed_amiga_base_slot_tags_from_effects(const M68kSectionAnalysisIR *section_analysis,
    AmigaBaseSlotTag *slots, size_t slot_count) {
  size_t index;
  if (section_analysis == NULL || slots == NULL) return;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    uint16_t base_id;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) continue;
    base_id = !amiga_base_id_is_none_local(effect->payload.named_base.base_ref.id)
      ? effect->payload.named_base.base_ref.id
      : amiga_base_id_from_name_local(effect->payload.named_base.base_name);
    if (amiga_base_id_is_none_local(base_id)) continue;
    set_amiga_base_slot_id_local(slots, slot_count, effect->displacement, base_id);
  }
}

static uint16_t lookup_recovered_platform_base_slot_id_local(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement) {
  AmigaBaseSlotTag slots[AMIGA_BASE_SLOT_TAG_CAPACITY];
  size_t index;
  uint16_t base_id;
  if (section_analysis == NULL) return AMIGA_OS_BASE_ID_NONE;
  init_amiga_base_slot_tag_array(slots, sizeof(slots) / sizeof(slots[0]));
  seed_amiga_base_slot_tags_from_effects(section_analysis, slots, sizeof(slots) / sizeof(slots[0]));
  base_id = lookup_amiga_base_slot_id_local(slots, sizeof(slots) / sizeof(slots[0]), displacement);
  if (!amiga_base_id_is_none_local(base_id)) return base_id;
  for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
    const M68kRecoveredPlatformBaseSlotIR *slot = &section_analysis->recovered_platform_base_slots[index];
    if (slot->displacement != displacement) continue;
    base_id = !amiga_base_id_is_none_local(slot->base_ref.id) ? slot->base_ref.id : amiga_base_id_from_name_local(slot->base_name);
    if (!amiga_base_id_is_none_local(base_id)) return base_id;
  }
  return AMIGA_OS_BASE_ID_NONE;
}

static uint16_t lookup_amiga_app_slot_base_id_for_operand(const M68kSectionAnalysisIR *section_analysis,
    const AmigaBaseSlotTag *slot_base_names, size_t slot_base_count, const M68kOperandIR *operand,
    uint16_t current_a6_base_id, int16_t *out_displacement) {
  int16_t displacement;
  if (out_displacement != NULL) *out_displacement = INT16_MIN;
  if (!operand_is_app_base_disp_ea(operand, 6U, &displacement)) return AMIGA_OS_BASE_ID_NONE;
  if (!amiga_base_id_is_app_local(current_a6_base_id) &&
      !has_recovered_amiga_app_slot_displacement(section_analysis, displacement))
    return AMIGA_OS_BASE_ID_NONE;
  if (out_displacement != NULL) *out_displacement = displacement;
  return lookup_amiga_base_slot_id_local(slot_base_names, slot_base_count, displacement);
}

static void seed_amiga_typed_slot_tags_from_effects(const M68kSectionAnalysisIR *section_analysis,
    AmigaTypedSlotTag *slots, size_t slot_count) {
  size_t index;
  if (section_analysis == NULL || slots == NULL) return;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    AmigaValueProvenance value;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) continue;
    init_amiga_value_provenance(&value);
    if (!amiga_typed_payload_has_any_info_local(&effect->payload.typed)) continue;
    amiga_typed_payload_apply_to_value_local(&value, &effect->payload.typed);
    value.source_offset = effect->offset;
    value.slot_disp = effect->displacement;
    value.field_disp = effect->field_disp;
    set_amiga_typed_slot_tag(slots, slot_count, effect->displacement, &value);
  }
}

static void apply_amiga_typed_global_slot_effect_to_slots(const M68kRecoveredPlatformEffectIR *effect,
    AmigaAbsoluteTypedSlotTag *slots, size_t slot_count) {
  AmigaValueProvenance value;
  if (effect == NULL || slots == NULL || effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT ||
      effect->target_section_index == SIZE_MAX || effect->target_offset == UINT32_MAX ||
      !amiga_typed_payload_has_any_info_local(&effect->payload.typed)) {
    return;
  }
  init_amiga_value_provenance(&value);
  amiga_typed_payload_apply_to_value_local(&value, &effect->payload.typed);
  value.source_offset = effect->offset;
  value.field_disp = effect->field_disp;
  set_amiga_absolute_typed_slot_value_local(slots, slot_count, effect->target_section_index,
    effect->target_offset, &value);
}

static void seed_amiga_absolute_typed_slots_before_offset(const M68kSectionAnalysisIR *section_analysis,
    uint32_t before_offset, AmigaAbsoluteTypedSlotTag *slots, size_t slot_count) {
  size_t index;
  if (section_analysis == NULL || slots == NULL) return;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->offset >= before_offset) continue;
    apply_amiga_typed_global_slot_effect_to_slots(effect, slots, slot_count);
  }
}

static void apply_recovered_amiga_typed_global_slot_effects_at_offset(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, AmigaAbsoluteTypedSlotTag *slots, size_t slot_count) {
  size_t index;
  const M68kRecoveredPlatformEffectIR *effect;
  if (section_analysis == NULL || slots == NULL) return;
  if (section_analysis->recovered_platform_effect_lookup != NULL) {
    for (effect = first_recovered_platform_effect_at_offset(section_analysis, offset); effect != NULL;
         effect = next_recovered_platform_effect_at_same_offset(section_analysis, effect)) {
      apply_amiga_typed_global_slot_effect_to_slots(effect, slots, slot_count);
    }
    return;
  }
  for (index = 0U; index < section_analysis->recovered_platform_effect_count; ++index) {
    effect = &section_analysis->recovered_platform_effects[index];
    if (effect->offset == offset) apply_amiga_typed_global_slot_effect_to_slots(effect, slots, slot_count);
  }
}

const char *lookup_recovered_platform_base_slot(const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  return amiga_base_name_from_id_local(lookup_recovered_platform_base_slot_id_local(section_analysis, displacement));
}

static uint32_t next_amiga_platform_fact_code_offset(const M68kSectionAnalysisIR *section_analysis,
    uint32_t start_offset, uint32_t section_size) {
  uint32_t offset;
  if (start_offset >= section_size) return UINT32_MAX;
  if (section_analysis == NULL || section_analysis->certain_code_start == NULL ||
      section_analysis->certain_code_size == 0U)
    return UINT32_MAX;
  for (offset = start_offset; offset < section_size && offset < section_analysis->certain_code_size; ++offset) {
    if (section_analysis->certain_code_start[offset] != 0U) return offset;
  }
  return UINT32_MAX;
}

static int amiga_section_has_direct_call_to_section(const SectionAnalysisContext *ctx, size_t source_section_index,
    size_t target_section_index) {
  const M68kObject *object = section_analysis_context_object(ctx);
  AmigaPlatformCache *cache;
  AmigaSectionDirectCallCacheEntry *cache_entry;
  int cache_found = 0;
  int result = 0;
  if (ctx == NULL || object == NULL || source_section_index >= object->section_count ||
      target_section_index >= object->section_count || source_section_index == target_section_index)
    return 0;
  cache = amiga_platform_cache_for_ctx(ctx);
  cache_entry = amiga_section_direct_call_cache_find(cache, source_section_index, target_section_index, &cache_found);
  if (cache_found && cache_entry != NULL) return cache_entry->result;
  if (scan_amiga_source_section_direct_calls_to_target(ctx, source_section_index, target_section_index, 1,
        NULL, NULL, &result) != 0)
    result = 0;
  if (cache_entry != NULL) {
    cache_entry->valid = 1U;
    cache_entry->source_section_index = source_section_index;
    cache_entry->target_section_index = target_section_index;
    cache_entry->result = result;
  }
  return result;
}

static uint16_t lookup_amiga_call_scoped_base_slot_id(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  const M68kObject *object;
  size_t current_section_index;
  size_t source_section_index;
  uint16_t found_base_id = AMIGA_OS_BASE_ID_NONE;
  if (ctx == NULL || section_analysis == NULL) return AMIGA_OS_BASE_ID_NONE;
  object = section_analysis_context_object(ctx);
  if (object == NULL || ctx->prior_section_analyses == NULL ||
      ctx->prior_section_analysis_count < object->section_count)
    return AMIGA_OS_BASE_ID_NONE;
  current_section_index = section_analysis_context_section_index(ctx);
  for (source_section_index = 0U; source_section_index < object->section_count; ++source_section_index) {
    const M68kSectionAnalysisIR *source_analysis;
    uint16_t source_base_id;
    if (source_section_index == current_section_index) continue;
    source_analysis = section_analysis_context_prior_section_analysis(ctx, source_section_index);
    if (source_analysis == NULL) continue;
    source_base_id = lookup_recovered_platform_base_slot_id_cached(ctx, source_analysis, displacement);
    if (amiga_base_id_is_none_local(source_base_id)) continue;
    if (!amiga_section_has_direct_call_to_section(ctx, source_section_index, current_section_index)) continue;
    if (!amiga_base_id_is_none_local(found_base_id) && found_base_id != source_base_id)
      return AMIGA_OS_BASE_ID_NONE;
    found_base_id = source_base_id;
  }
  return found_base_id;
}

static int lookup_recovered_platform_typed_slot_value(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement, AmigaValueProvenance *out_value) {
  AmigaTypedSlotTag slots[AMIGA_BASE_SLOT_TAG_CAPACITY];
  const AmigaValueProvenance *value;
  if (out_value != NULL) init_amiga_value_provenance(out_value);
  if (section_analysis == NULL || out_value == NULL) return 0;
  init_amiga_typed_slot_tag_array(slots, sizeof(slots) / sizeof(slots[0]));
  seed_amiga_typed_slot_tags_from_effects(section_analysis, slots, sizeof(slots) / sizeof(slots[0]));
  value = lookup_amiga_typed_slot_tag(slots, sizeof(slots) / sizeof(slots[0]), displacement);
  if (value == NULL) return 0;
  *out_value = *value;
  return 1;
}

static const char *lookup_recovered_platform_typed_slot(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement) {
  AmigaValueProvenance value;
  if (!lookup_recovered_platform_typed_slot_value(section_analysis, displacement, &value)) return NULL;
  return amiga_value_provenance_type_name_local(&value);
}

static int resolve_recovered_platform_typed_slot_field(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement, int16_t *out_slot_disp, const char **out_type_name, const char **out_field_name) {
  size_t index;
  int16_t best_slot_disp = INT16_MIN;
  const char *best_type_name = NULL;
  const char *best_field_name = NULL;
  if (out_slot_disp != NULL) *out_slot_disp = INT16_MIN;
  if (out_type_name != NULL) *out_type_name = NULL;
  if (out_field_name != NULL) *out_field_name = NULL;
  if (section_analysis == NULL || displacement == INT16_MIN) return 0;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    const AmigaOsStructFieldInfo *field;
    const char *field_name;
    const char *type_name;
    int16_t field_disp;
    uint16_t type_id;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) continue;
    if (effect->displacement == INT16_MIN || effect->displacement > displacement) continue;
    type_id = amiga_typed_payload_type_id_local(&effect->payload.typed);
    if (amiga_os_name(M68K_PLATFORM_NAME_TYPE, type_id) == NULL) continue;
    type_name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, type_id);
    if (type_name == NULL) continue;
    field_disp = (int16_t)(displacement - effect->displacement);
    field = amiga_os_find_struct_field(type_name, field_disp);
    field_name = amiga_struct_field_name(field);
    if (field_name == NULL || field_name[0] == '\0') continue;
    if (best_type_name == NULL || effect->displacement > best_slot_disp) {
      best_slot_disp = effect->displacement;
      best_type_name = type_name;
      best_field_name = field_name;
    }
  }
  if (best_type_name == NULL || best_field_name == NULL) return 0;
  if (out_slot_disp != NULL) *out_slot_disp = best_slot_disp;
  if (out_type_name != NULL) *out_type_name = best_type_name;
  if (out_field_name != NULL) *out_field_name = best_field_name;
  return 1;
}

static size_t count_recovered_platform_typed_slot_type_uses(const M68kSectionAnalysisIR *section_analysis,
    const char *type_name) {
  size_t index;
  size_t count = 0U;
  uint16_t type_id = amiga_os_name_id(M68K_PLATFORM_NAME_TYPE, type_name);
  if (section_analysis == NULL || type_name == NULL || type_name[0] == '\0') return 0U;
  if (amiga_os_name(M68K_PLATFORM_NAME_TYPE, type_id) == NULL) return 0U;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    uint16_t effect_type_id;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) continue;
    effect_type_id = amiga_typed_payload_type_id_local(&effect->payload.typed);
    if (effect_type_id != type_id) continue;
    ++count;
  }
  return count;
}

static int lookup_amiga_effect_or_local_typed_slot_value(const M68kSectionAnalysisIR *section_analysis,
    const AmigaTypedSlotTag *slot_type_names, size_t slot_type_count, int16_t displacement,
    AmigaValueProvenance *out_value) {
  const AmigaValueProvenance *value;
  if (lookup_recovered_platform_typed_slot_value(section_analysis, displacement, out_value)) return 1;
  if (out_value != NULL) init_amiga_value_provenance(out_value);
  value = lookup_amiga_typed_slot_tag(slot_type_names, slot_type_count, displacement);
  if (value == NULL || out_value == NULL) return 0;
  *out_value = *value;
  return 1;
}

const char *resolve_amiga_app_slot_base_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  const char *base_name = amiga_base_name_from_id_local(lookup_recovered_platform_base_slot_id_local(section_analysis,
    displacement));
  uint16_t scoped_base_id;
  if (base_name != NULL) return base_name;
  scoped_base_id = lookup_amiga_call_scoped_base_slot_id(ctx, section_analysis, displacement);
  if (!amiga_base_id_is_none_local(scoped_base_id)) return amiga_base_name_from_id_local(scoped_base_id);
  return NULL;
}

static uint16_t resolve_amiga_app_slot_base_id(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  uint16_t base_id = lookup_recovered_platform_base_slot_id_local(section_analysis, displacement);
  if (!amiga_base_id_is_none_local(base_id)) return base_id;
  base_id = lookup_amiga_call_scoped_base_slot_id(ctx, section_analysis, displacement);
  if (!amiga_base_id_is_none_local(base_id)) return base_id;
  return AMIGA_OS_BASE_ID_NONE;
}

int resolve_amiga_app_slot_symbol_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, char *buf, size_t buf_size) {
  const char *base_name;
  const char *type_name;
  int16_t slot_disp;
  const char *field_type_name;
  const char *field_name;
  char slot_symbol_name[64];
  if (buf == NULL || buf_size == 0U) return 0;
  if (resolve_recovered_platform_typed_slot_field(section_analysis, displacement, &slot_disp, &field_type_name,
        &field_name)) {
    if (!format_amiga_named_typed_slot_symbol_name(section_analysis, slot_disp, slot_symbol_name,
        sizeof(slot_symbol_name))) {
      if (count_recovered_platform_typed_slot_type_uses(section_analysis, field_type_name) > 1U) {
        format_amiga_typed_slot_symbol_name_for_disp(slot_symbol_name, sizeof(slot_symbol_name), field_type_name, slot_disp);
      } else {
        format_amiga_typed_slot_symbol_name(slot_symbol_name, sizeof(slot_symbol_name), field_type_name);
      }
    }
    snprintf(buf, buf_size, "%s+%s", slot_symbol_name, field_name);
    return 1;
  }
  base_name = resolve_amiga_app_slot_base_name(ctx, section_analysis, displacement);
  if (base_name != NULL && base_name[0] != '\0') {
    (void)platform_amiga_format_app_base_slot_name(base_name, buf, buf_size);
    return 1;
  }
  type_name = lookup_recovered_platform_typed_slot(section_analysis, displacement);
  if (type_name != NULL && type_name[0] != '\0') {
    if (!format_amiga_named_typed_slot_symbol_name(section_analysis, displacement, buf, buf_size)) {
      if (count_recovered_platform_typed_slot_type_uses(section_analysis, type_name) > 1U) {
        format_amiga_typed_slot_symbol_name_for_disp(buf, buf_size, type_name, displacement);
      } else {
        format_amiga_typed_slot_symbol_name(buf, buf_size, type_name);
      }
    }
    return 1;
  }
  if (ctx != NULL && (has_recovered_amiga_app_slot_displacement(section_analysis, displacement) ||
      section_analysis_has_amiga_structural_slot_use(section_analysis, displacement))) {
    format_amiga_slot_struct_type_name(buf, buf_size, displacement);
    return 1;
  }
  return 0;
}

int resolve_amiga_app_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, M68kSymbolRefIR *out_symbol_ref) {
  const char *base_name;
  const char *type_name;
  int16_t slot_disp;
  const char *field_type_name;
  const char *field_name;
  if (out_symbol_ref == NULL) return 0;
  m68k_ir_symbol_ref_init(out_symbol_ref);
  if (resolve_recovered_platform_typed_slot_field(section_analysis, displacement, &slot_disp, &field_type_name,
        &field_name)) {
      out_symbol_ref->has_name = 1U;
      if (!format_amiga_named_typed_slot_symbol_name(section_analysis, slot_disp, out_symbol_ref->name,
          sizeof(out_symbol_ref->name))) {
        if (count_recovered_platform_typed_slot_type_uses(section_analysis, field_type_name) > 1U) {
          format_amiga_typed_slot_symbol_name_for_disp(out_symbol_ref->name, sizeof(out_symbol_ref->name),
            field_type_name, slot_disp);
        } else {
          format_amiga_typed_slot_symbol_name(out_symbol_ref->name, sizeof(out_symbol_ref->name), field_type_name);
        }
      }
      out_symbol_ref->has_symbolic_addend = 1U;
      out_symbol_ref->symbolic_addend_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      out_symbol_ref->symbolic_addend_value = (int32_t)(displacement - slot_disp);
      snprintf(out_symbol_ref->symbolic_addend_name, sizeof(out_symbol_ref->symbolic_addend_name), "%s", field_name);
      return 1;
  }
  base_name = resolve_amiga_app_slot_base_name(ctx, section_analysis, displacement);
  if (base_name != NULL && base_name[0] != '\0') {
    out_symbol_ref->has_name = 1U;
    (void)platform_amiga_format_app_base_slot_name(base_name, out_symbol_ref->name,
      sizeof(out_symbol_ref->name));
    return 1;
  }
  type_name = lookup_recovered_platform_typed_slot(section_analysis, displacement);
  if (type_name != NULL && type_name[0] != '\0') {
    out_symbol_ref->has_name = 1U;
    if (!format_amiga_named_typed_slot_symbol_name(section_analysis, displacement, out_symbol_ref->name,
        sizeof(out_symbol_ref->name))) {
      if (count_recovered_platform_typed_slot_type_uses(section_analysis, type_name) > 1U) {
        format_amiga_typed_slot_symbol_name_for_disp(out_symbol_ref->name, sizeof(out_symbol_ref->name), type_name,
          displacement);
      } else {
        format_amiga_typed_slot_symbol_name(out_symbol_ref->name, sizeof(out_symbol_ref->name), type_name);
      }
    }
    return 1;
  }
  if (ctx != NULL && (has_recovered_amiga_app_slot_displacement(section_analysis, displacement) ||
      section_analysis_has_amiga_structural_slot_use(section_analysis, displacement))) {
    out_symbol_ref->has_name = 1U;
    format_amiga_slot_struct_type_name(out_symbol_ref->name, sizeof(out_symbol_ref->name), displacement);
    return 1;
  }
  return 0;
}

int resolve_amiga_app_slot_value_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, M68kSymbolRefIR *out_symbol_ref) {
  const char *type_name;
  const AmigaOsStructFieldInfo *field;
  if (out_symbol_ref == NULL) return 0;
  if (!resolve_amiga_app_slot_symbol_ref(ctx, section_analysis, displacement, out_symbol_ref)) return 0;
  type_name = lookup_recovered_platform_typed_slot(section_analysis, displacement);
  if (type_name == NULL || type_name[0] == '\0') return 1;
  field = amiga_os_find_struct_field(type_name, 0);
  if (field == NULL || amiga_struct_field_name(field) == NULL || amiga_struct_field_name(field)[0] == '\0') return 1;
  out_symbol_ref->has_symbolic_addend = 1U;
  out_symbol_ref->symbolic_addend_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  out_symbol_ref->symbolic_addend_value = 0;
  snprintf(out_symbol_ref->symbolic_addend_name, sizeof(out_symbol_ref->symbolic_addend_name), "%s",
    amiga_struct_field_name(field));
  return 1;
}

static void apply_recovered_amiga_platform_effect(const M68kRecoveredPlatformEffectIR *effect, uint32_t offset,
    uint16_t *data_reg_base_ids, uint16_t *addr_reg_base_ids, AmigaValueProvenance *data_reg_values,
    AmigaValueProvenance *addr_reg_values, AmigaBaseSlotTag *slot_base_names, size_t slot_base_count,
    AmigaTypedSlotTag *slot_type_names, size_t slot_type_count) {
  if (effect == NULL || effect->offset != offset) return;
  if (effect->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG) {
    uint16_t base_id = amiga_named_base_payload_id_local(&effect->payload.named_base);
    const char *base_type_name = resolve_amiga_base_type_name_from_id_local(base_id);
    if (amiga_base_id_is_none_local(base_id)) return;
    if (effect->reg_kind == 1U && data_reg_base_ids != NULL && effect->reg_index < 8U) {
      data_reg_base_ids[effect->reg_index] = base_id;
      if (data_reg_values != NULL &&
          amiga_value_provenance_type_name_local(&data_reg_values[effect->reg_index]) == NULL) {
        amiga_value_provenance_set_type_name(&data_reg_values[effect->reg_index], base_type_name);
        amiga_value_provenance_set_owner_type_name(&data_reg_values[effect->reg_index], base_type_name);
      }
    } else if (effect->reg_kind == 2U && addr_reg_base_ids != NULL && effect->reg_index < 8U) {
      addr_reg_base_ids[effect->reg_index] = base_id;
      if (addr_reg_values != NULL &&
          amiga_value_provenance_type_name_local(&addr_reg_values[effect->reg_index]) == NULL) {
        amiga_value_provenance_set_type_name(&addr_reg_values[effect->reg_index], base_type_name);
        amiga_value_provenance_set_owner_type_name(&addr_reg_values[effect->reg_index], base_type_name);
      }
    }
  } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
    if (effect->reg_kind == 1U && data_reg_values != NULL && effect->reg_index < 8U) {
      amiga_typed_payload_apply_to_value_local(&data_reg_values[effect->reg_index], &effect->payload.typed);
      data_reg_values[effect->reg_index].source_offset = offset;
      data_reg_values[effect->reg_index].source_reg_kind = effect->reg_kind;
      data_reg_values[effect->reg_index].source_reg_index = effect->reg_index;
    } else if (effect->reg_kind == 2U && addr_reg_values != NULL && effect->reg_index < 8U) {
      amiga_typed_payload_apply_to_value_local(&addr_reg_values[effect->reg_index], &effect->payload.typed);
      addr_reg_values[effect->reg_index].source_offset = offset;
      addr_reg_values[effect->reg_index].source_reg_kind = effect->reg_kind;
      addr_reg_values[effect->reg_index].source_reg_index = effect->reg_index;
    }
  } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
    AmigaValueProvenance *target = NULL;
    if (effect->reg_kind == 1U && data_reg_values != NULL && effect->reg_index < 8U)
      target = &data_reg_values[effect->reg_index];
    else if (effect->reg_kind == 2U && addr_reg_values != NULL && effect->reg_index < 8U)
      target = &addr_reg_values[effect->reg_index];
    if (target == NULL) return;
    if (amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, effect->payload.code_ptr.semantic_kind_ref.id) != NULL)
      amiga_value_provenance_set_semantic_kind_id(target, effect->payload.code_ptr.semantic_kind_ref.id);
    else
      amiga_value_provenance_set_semantic_kind_name(target,
        effect->payload.code_ptr.semantic_kind != NULL ? effect->payload.code_ptr.semantic_kind : "code_ptr");
    if (amiga_os_name(M68K_PLATFORM_NAME_TYPE, effect->payload.code_ptr.owner_type_ref.id) != NULL)
      amiga_value_provenance_set_owner_type_id(target, effect->payload.code_ptr.owner_type_ref.id);
    else
      amiga_value_provenance_set_owner_type_name(target, effect->payload.code_ptr.owner_type_name);
    target->field_disp = effect->field_disp;
    if (amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, effect->payload.code_ptr.field_symbol_ref.id) != NULL)
      amiga_value_provenance_set_field_symbol_id(target, effect->payload.code_ptr.field_symbol_ref.id);
    else
      amiga_value_provenance_set_field_symbol_name(target, effect->payload.code_ptr.field_symbol_name);
    target->source_offset = offset;
    target->source_reg_kind = effect->reg_kind;
    target->source_reg_index = effect->reg_index;
    if (target->slot_disp == INT16_MIN) target->slot_disp = effect->displacement;
  } else if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) {
    uint16_t base_id;
    if (slot_base_names == NULL) return;
    base_id = amiga_named_base_payload_id_local(&effect->payload.named_base);
    if (amiga_base_id_is_none_local(base_id)) return;
    set_amiga_base_slot_id_local(slot_base_names, slot_base_count, effect->displacement, base_id);
  } else if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) {
    AmigaValueProvenance value;
    if (slot_type_names == NULL) return;
    init_amiga_value_provenance(&value);
    amiga_typed_payload_apply_to_value_local(&value, &effect->payload.typed);
    value.source_offset = offset;
    value.slot_disp = effect->displacement;
    value.field_disp = effect->field_disp;
    if (amiga_value_provenance_has_any_info(&value))
      set_amiga_typed_slot_tag(slot_type_names, slot_type_count, effect->displacement, &value);
  }
}

static void apply_recovered_amiga_platform_effects(const M68kSectionAnalysisIR *section_analysis, uint32_t offset,
    uint16_t *data_reg_base_ids, uint16_t *addr_reg_base_ids, AmigaValueProvenance *data_reg_values,
    AmigaValueProvenance *addr_reg_values, AmigaBaseSlotTag *slot_base_names, size_t slot_base_count,
    AmigaTypedSlotTag *slot_type_names, size_t slot_type_count) {
  size_t index;
  const M68kRecoveredPlatformEffectIR *effect;
  if (section_analysis == NULL) return;
  if (section_analysis->recovered_platform_effect_lookup != NULL) {
    for (effect = first_recovered_platform_effect_at_offset(section_analysis, offset); effect != NULL;
         effect = next_recovered_platform_effect_at_same_offset(section_analysis, effect)) {
      apply_recovered_amiga_platform_effect(effect, offset, data_reg_base_ids, addr_reg_base_ids, data_reg_values,
        addr_reg_values, slot_base_names, slot_base_count, slot_type_names, slot_type_count);
    }
    return;
  }
  for (index = 0U; index < section_analysis->recovered_platform_effect_count; ++index) {
    effect = &section_analysis->recovered_platform_effects[index];
    apply_recovered_amiga_platform_effect(effect, offset, data_reg_base_ids, addr_reg_base_ids, data_reg_values,
      addr_reg_values, slot_base_names, slot_base_count, slot_type_names, slot_type_count);
  }
}

static int has_recovered_amiga_app_slot_displacement(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement) {
  size_t index;
  if (section_analysis == NULL || displacement == INT16_MIN) return 0;
  if (section_analysis->recovered_platform_slot_displacement_lookup != NULL)
    return recovered_platform_slot_displacement_lookup_has(section_analysis, displacement);
  for (index = 0U; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if ((effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT ||
         effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) &&
        effect->displacement == displacement) {
      return 1;
    }
  }
  for (index = 0U; index < section_analysis->recovered_platform_base_slot_count; ++index) {
    if (section_analysis->recovered_platform_base_slots[index].displacement == displacement) return 1;
  }
  return 0;
}

static void seed_amiga_effect_state_from_preceding_fallthrough(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t start, uint16_t *data_reg_base_ids,
    uint16_t *addr_reg_base_ids, AmigaValueProvenance *data_reg_values, AmigaValueProvenance *addr_reg_values,
    AmigaBaseSlotTag *slot_base_names, size_t slot_base_count, AmigaTypedSlotTag *slot_type_names,
    size_t slot_type_count) {
  uint32_t low;
  uint32_t candidate_start;
  uint32_t best_prev_offset = UINT32_MAX;
  M68kInstructionIR best_prev_instruction;
  int have_best = 0;
  if (ctx == NULL || section_analysis == NULL || start == 0U) return;
  low = start > 32U ? (start - 32U) : 0U;
  for (candidate_start = low; candidate_start < start; ++candidate_start) {
    uint32_t cursor = candidate_start;
    uint32_t prev_offset = UINT32_MAX;
    M68kInstructionIR prev_instruction;
    int have_prev = 0;
    while (cursor < start) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U) break;
      if (cursor + (uint32_t)decode.instruction.byte_count > start) break;
      prev_offset = cursor;
      prev_instruction = decode.instruction;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (cursor != start || !have_prev || instruction_stops_fallthrough(&prev_instruction)) continue;
    if (!have_best || prev_offset > best_prev_offset) {
      best_prev_offset = prev_offset;
      best_prev_instruction = prev_instruction;
      have_best = 1;
    }
  }
  if (!have_best) return;
  apply_recovered_amiga_platform_effects(section_analysis, best_prev_offset,
    data_reg_base_ids, addr_reg_base_ids, data_reg_values, addr_reg_values,
    slot_base_names, slot_base_count, slot_type_names, slot_type_count);
}

static void format_amiga_slot_struct_type_name(char *buf, size_t buf_size, int16_t displacement) {
  if (buf == NULL || buf_size == 0U) return;
  if (displacement == INT16_MIN) {
    buf[0] = '\0';
    return;
  }
  snprintf(buf, buf_size, "app_%04X", (unsigned)(uint16_t)displacement);
}

static void format_amiga_typed_slot_symbol_name(char *buf, size_t buf_size, const char *type_name) {
  if (buf == NULL || buf_size == 0U) return;
  if (type_name == NULL || type_name[0] == '\0') {
    buf[0] = '\0';
    return;
  }
  snprintf(buf, buf_size, "app_%s", type_name);
}

static void format_amiga_typed_slot_symbol_name_for_disp(char *buf, size_t buf_size, const char *type_name,
    int16_t displacement) {
  if (buf == NULL || buf_size == 0U) return;
  if (type_name == NULL || type_name[0] == '\0') {
    buf[0] = '\0';
    return;
  }
  snprintf(buf, buf_size, "app_%s_%04X", type_name, (unsigned)(uint16_t)displacement);
}

static int append_amiga_normalized_symbol_part(char *buf, size_t buf_size, size_t *out_index_ptr, const char *text) {
  size_t out_index;
  size_t in_index;
  if (buf == NULL || buf_size == 0U || out_index_ptr == NULL || text == NULL || text[0] == '\0') return 0;
  out_index = *out_index_ptr;
  for (in_index = 0U; text[in_index] != '\0' && out_index + 1U < buf_size; ++in_index) {
    unsigned char ch = (unsigned char)text[in_index];
    if (isalnum(ch)) {
      buf[out_index++] = (char)tolower(ch);
    } else if (out_index > 0U && buf[out_index - 1U] != '_') {
      buf[out_index++] = '_';
    }
  }
  while (out_index > 0U && buf[out_index - 1U] == '_') --out_index;
  buf[out_index] = '\0';
  *out_index_ptr = out_index;
  return 1;
}

static const M68kRecoveredPlatformEffectIR *find_recovered_platform_typed_slot_effect(
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  size_t index;
  if (section_analysis == NULL || displacement == INT16_MIN) return NULL;
  for (index = 0U; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT && effect->displacement == displacement) return effect;
  }
  return NULL;
}

static size_t count_recovered_platform_typed_slot_name_uses(const M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredPlatformEffectIR *target_effect) {
  const char *target_symbol_name;
  const char *target_context_name;
  size_t index;
  size_t count = 0U;
  if (section_analysis == NULL || target_effect == NULL) return 0U;
  target_symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&target_effect->payload.typed.symbol_ref,
    target_effect->payload.typed.symbol_name);
  target_context_name = m68k_platform_name_ref_resolve_text_or_fallback(&target_effect->payload.typed.context_ref,
    target_effect->payload.typed.context_name);
  if (target_symbol_name == NULL || target_symbol_name[0] == '\0') return 0U;
  for (index = 0U; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    const char *symbol_name;
    const char *context_name;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) continue;
    symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.symbol_ref,
      effect->payload.typed.symbol_name);
    context_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.context_ref,
      effect->payload.typed.context_name);
    if (symbol_name == NULL || strcmp(symbol_name, target_symbol_name) != 0) continue;
    if ((context_name == NULL) != (target_context_name == NULL)) continue;
    if (context_name != NULL && strcmp(context_name, target_context_name) != 0) continue;
    ++count;
  }
  return count;
}

static int format_amiga_named_typed_slot_symbol_name(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement, char *buf, size_t buf_size) {
  const M68kRecoveredPlatformEffectIR *effect;
  const char *symbol_name;
  const char *context_name;
  size_t out_index;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  effect = find_recovered_platform_typed_slot_effect(section_analysis, displacement);
  if (effect == NULL) return 0;
  symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.symbol_ref,
    effect->payload.typed.symbol_name);
  if (symbol_name == NULL || symbol_name[0] == '\0') return 0;
  context_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.context_ref,
    effect->payload.typed.context_name);
  if (context_name != NULL && context_name[0] != '\0') {
    const char *library_name = amiga_os_find_library_name_by_base_name(context_name);
    if (library_name != NULL && library_name[0] != '\0') context_name = library_name;
  }
  if ((context_name == NULL || context_name[0] == '\0') &&
      (strcmp(symbol_name, "SegList") == 0 || strcmp(symbol_name, "seglist") == 0)) {
    snprintf(buf, buf_size, "app_SegList");
    return 1;
  }
  out_index = (size_t)snprintf(buf, buf_size, "app_");
  if (out_index >= buf_size) return 0;
  if (context_name != NULL && context_name[0] != '\0') {
    if (!append_amiga_normalized_symbol_part(buf, buf_size, &out_index, context_name)) return 0;
    if (out_index + 1U >= buf_size) return 0;
    buf[out_index++] = '_';
    buf[out_index] = '\0';
  }
  if (!append_amiga_normalized_symbol_part(buf, buf_size, &out_index, symbol_name)) return 0;
  if (count_recovered_platform_typed_slot_name_uses(section_analysis, effect) > 1U) {
    snprintf(buf + out_index, buf_size - out_index, "_%04X", (unsigned)(uint16_t)displacement);
  }
  return 1;
}

static int resolve_amiga_struct_field_symbol_name(const char *type_name, int16_t displacement, char *buf,
    size_t buf_size) {
  const AmigaOsStructFieldInfo *field;
  uint16_t struct_id;
  if (type_name == NULL || buf == NULL || buf_size == 0U) return 0;
  field = amiga_os_find_struct_field(type_name, displacement);
  struct_id = amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, type_name);
  if (field == NULL && struct_id == AMIGA_OS_STRUCT_ID_LIB) {
    field = amiga_os_find_struct_field(amiga_os_name(M68K_PLATFORM_NAME_STRUCT, AMIGA_OS_STRUCT_ID_LN),
      displacement);
  }
  if (field != NULL && amiga_struct_field_name(field) != NULL && amiga_struct_field_name(field)[0] != '\0') {
    snprintf(buf, buf_size, "%s", amiga_struct_field_name(field));
    return 1;
  }
  return 0;
}

static const char *resolve_amiga_struct_field_nested_type_name(const char *type_name, int16_t displacement) {
  const AmigaOsStructFieldInfo *field;
  uint16_t struct_id;
  if (type_name == NULL) return NULL;
  field = amiga_os_find_struct_field(type_name, displacement);
  struct_id = amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, type_name);
  if (field == NULL && struct_id == AMIGA_OS_STRUCT_ID_LIB) {
    field = amiga_os_find_struct_field(amiga_os_name(M68K_PLATFORM_NAME_STRUCT, AMIGA_OS_STRUCT_ID_LN),
      displacement);
  }
  if (field == NULL || amiga_struct_field_nested_type_name(field) == NULL ||
      amiga_struct_field_nested_type_name(field)[0] == '\0') {
    return NULL;
  }
  return amiga_struct_field_nested_type_name(field);
}

static void populate_amiga_callback_field_note_symbol(PlatformResolvedIndirectInfo *out_info) {
  char field_name[64];
  if (out_info == NULL) return;
  if (out_info->note_kind != M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD) return;
  if (out_info->note_base_name[0] == '\0' || out_info->note_field_disp == INT16_MIN) return;
  if (!resolve_amiga_struct_field_symbol_name(out_info->note_base_name, out_info->note_field_disp,
      field_name, sizeof(field_name))) {
    return;
  }
  snprintf(out_info->note_symbol_name, sizeof(out_info->note_symbol_name), "%s", field_name);
}

static void populate_amiga_call_version_info(const AmigaOsLibraryVectorInfo *entry,
    PlatformResolvedIndirectInfo *out_info) {
  const char *available_since_name;
  if (entry == NULL || out_info == NULL) return;
  available_since_name = amiga_os_compatibility_version_name((AmigaOsCompatVersion)entry->available_since_version);
  if (available_since_name != NULL && available_since_name[0] != '\0')
    snprintf(out_info->available_since, sizeof(out_info->available_since), "%s", available_since_name);
  if (entry->fd_version != NULL && entry->fd_version[0] != '\0') {
    snprintf(out_info->fd_version, sizeof(out_info->fd_version), "%s", entry->fd_version);
  }
}

static int operand_address_reg_index_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || out_reg == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) {
    *out_reg = operand->value.reg;
    return 1;
  }
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 1U) {
    *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static int operand_data_reg_index_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || out_reg == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) {
    *out_reg = operand->value.reg;
    return 1;
  }
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 0U) {
    *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static int instruction_pushes_data_reg_to_stack_local(const M68kInstructionIR *instruction, uint8_t *out_reg) {
  uint8_t reg_index;
  if (out_reg != NULL) *out_reg = 0U;
  if (instruction->operand_count != 2U) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE) return 0;
  if (!operand_data_reg_index_local(&instruction->operands[0], &reg_index)) return 0;
  if (instruction->operands[1].kind != M68K_ASM_OPERAND_PREDEC) return 0;
  if (instruction->operands[1].value.ea_reg != 7U) return 0;
  if (out_reg != NULL) *out_reg = reg_index;
  return 1;
}

static int instruction_pops_data_reg_from_stack_local(const M68kInstructionIR *instruction, uint8_t *out_reg) {
  const M68kOperandIR *source = NULL;
  if (out_reg != NULL) *out_reg = 0U;
  if (instruction->operand_count != 2U) return 0;
  if (!instruction_is_data_move(instruction, out_reg, &source) || source == NULL) return 0;
  if (source->kind != M68K_ASM_OPERAND_POSTINC) return 0;
  return source->value.ea_reg == 7U;
}

static int instruction_pushes_movem_to_stack_local(const M68kInstructionIR *instruction, uint16_t *out_mask) {
  if (out_mask != NULL) *out_mask = 0U;
  if (instruction->operand_count != 2U) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEM) return 0;
  if (instruction->operands[0].kind != M68K_ASM_OPERAND_REGLIST) return 0;
  if (instruction->operands[1].kind == M68K_ASM_OPERAND_PREDEC) {
    if (instruction->operands[1].value.ea_reg != 7U) return 0;
  } else if ((instruction->operands[1].kind == M68K_ASM_OPERAND_EA ||
      instruction->operands[1].kind == M68K_ASM_OPERAND_BF_EA) &&
      instruction->operands[1].value.ea_mode == 4U) {
    if (instruction->operands[1].value.ea_reg != 7U) return 0;
  } else {
    return 0;
  }
  if (out_mask != NULL) *out_mask = (uint16_t)instruction->operands[0].value.value;
  return 1;
}

static int instruction_pops_movem_from_stack_local(const M68kInstructionIR *instruction, uint16_t *out_mask) {
  if (out_mask != NULL) *out_mask = 0U;
  if (instruction->operand_count != 2U) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEM) return 0;
  if (instruction->operands[0].kind == M68K_ASM_OPERAND_POSTINC) {
    if (instruction->operands[0].value.ea_reg != 7U) return 0;
  } else if ((instruction->operands[0].kind == M68K_ASM_OPERAND_EA ||
      instruction->operands[0].kind == M68K_ASM_OPERAND_BF_EA) &&
      instruction->operands[0].value.ea_mode == 3U) {
    if (instruction->operands[0].value.ea_reg != 7U) return 0;
  } else {
    return 0;
  }
  if (instruction->operands[1].kind != M68K_ASM_OPERAND_REGLIST) return 0;
  if (out_mask != NULL) *out_mask = (uint16_t)instruction->operands[1].value.value;
  return 1;
}

static void decode_movem_reg_bit_local(unsigned bit, uint8_t *out_reg_kind, uint8_t *out_reg_index) {
  if (out_reg_kind != NULL) *out_reg_kind = bit < 8U ? 1U : 2U;
  if (out_reg_index != NULL) *out_reg_index = bit < 8U ? (uint8_t)bit : (uint8_t)(bit - 8U);
}

static int resolve_movem_stack_pair_source_local(uint16_t push_mask, uint16_t pop_mask, uint8_t target_reg_kind,
    uint8_t target_reg_index, uint8_t *out_source_reg_kind, uint8_t *out_source_reg_index) {
  uint8_t stack_reg_kind[16];
  uint8_t stack_reg_index[16];
  size_t stack_count = 0U;
  int bit;
  if (out_source_reg_kind != NULL) *out_source_reg_kind = 0U;
  if (out_source_reg_index != NULL) *out_source_reg_index = 0U;
  for (bit = 15; bit >= 0; --bit) {
    if ((push_mask & (uint16_t)(1U << bit)) == 0U) continue;
    decode_movem_reg_bit_local((unsigned)bit, &stack_reg_kind[stack_count], &stack_reg_index[stack_count]);
    ++stack_count;
  }
  for (bit = 0; bit < 16; ++bit) {
    uint8_t dest_reg_kind;
    uint8_t dest_reg_index;
    if ((pop_mask & (uint16_t)(1U << bit)) == 0U || stack_count == 0U) continue;
    decode_movem_reg_bit_local((unsigned)bit, &dest_reg_kind, &dest_reg_index);
    --stack_count;
    if (dest_reg_kind != target_reg_kind || dest_reg_index != target_reg_index) continue;
    if (out_source_reg_kind != NULL) *out_source_reg_kind = stack_reg_kind[stack_count];
    if (out_source_reg_index != NULL) *out_source_reg_index = stack_reg_index[stack_count];
    return 1;
  }
  return 0;
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_library_vector_entry_for_base_name(
    const M68kInstructionIR *instruction, const char *base_name) {
  const M68kOperandIR *operand = NULL;
  int16_t displacement;
  if (base_name == NULL) return NULL;
  if (!instruction_is_call_transfer(instruction)) return NULL;
  if (!instruction_target_operand_local(instruction, &operand) || operand == NULL) return NULL;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return NULL;
  if (operand->value.ea_mode != 5U) return NULL;
  displacement = (int16_t)(operand->value.value & 0xFFFFU);
  if (displacement >= 0 || (displacement & 1) != 0) return NULL;
  return amiga_os_find_library_vector(base_name, displacement);
}

static int amiga_context_section_index_local(const SectionAnalysisContext *ctx, uint32_t *out_section_index) {
  const M68kObject *object = section_analysis_context_object(ctx);
  const M68kSection *section = section_analysis_context_section(ctx);
  size_t index;
  if (out_section_index == NULL) return 0;
  if (object == NULL || section == NULL) return 0;
  for (index = 0U; index < object->section_count; ++index) {
    if (&object->sections[index] == section) {
      *out_section_index = (uint32_t)index;
      return 1;
    }
  }
  return 0;
}

static int amiga_register_seed_applies_at_or_before(const SectionAnalysisContext *ctx,
    const M68kAnalysisRegisterSeed *seed, uint32_t trace_start) {
  if (seed == NULL) return 0;
  if (seed->platform_kind != 0U && seed->platform_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (seed->has_section_index) {
    uint32_t section_index;
    if (!amiga_context_section_index_local(ctx, &section_index) || seed->section_index != section_index) return 0;
  }
  return !seed->has_entry_offset || seed->entry_offset <= trace_start;
}

static int amiga_register_seed_is_better_for_trace(const M68kAnalysisRegisterSeed *seed,
    const M68kAnalysisRegisterSeed *best_seed) {
  if (seed == NULL) return 0;
  if (best_seed == NULL) return 1;
  if (seed->has_entry_offset && !best_seed->has_entry_offset) return 1;
  if (!seed->has_entry_offset && best_seed->has_entry_offset) return 0;
  if (seed->has_entry_offset && best_seed->has_entry_offset && seed->entry_offset > best_seed->entry_offset) return 1;
  return 0;
}

static const char *amiga_register_seed_struct_type_name(const M68kAnalysisRegisterSeed *seed) {
  const char *type_name;
  if (seed == NULL) return NULL;
  type_name = seed->type_name[0] != '\0' ? seed->type_name : seed->name;
  if (seed->kind == M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE) {
    const char *base_struct_name = seed->type_name[0] != '\0'
      ? seed->type_name
      : amiga_os_find_library_base_struct_name(seed->name);
    if (base_struct_name != NULL && base_struct_name[0] != '\0') return base_struct_name;
    return "LIB";
  }
  return type_name;
}

static int resolve_amiga_policy_seed_struct_field_symbol_name(const SectionAnalysisContext *ctx, uint32_t offset,
    uint8_t reg_kind, uint8_t reg_index, int16_t displacement, char *buf, size_t buf_size, const char **out_type_name) {
  const M68kAnalysisPolicy *policy = section_analysis_context_policy(ctx);
  const M68kAnalysisRegisterSeed *best_seed = NULL;
  uint32_t best_offset = 0U;
  uint32_t section_index = 0U;
  uint16_t index;
  const char *type_name;
  if (out_type_name != NULL) *out_type_name = NULL;
  if (policy == NULL || buf == NULL || buf_size == 0U || reg_index >= 8U) return 0;
  if (!amiga_context_section_index_local(ctx, &section_index)) return 0;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if ((seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR &&
         seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE) ||
        seed->reg_kind != reg_kind ||
        seed->reg_index != reg_index ||
        (seed->platform_kind != 0U && seed->platform_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) ||
        (seed->has_section_index && seed->section_index != section_index)) {
      continue;
    }
    if (seed->has_entry_offset) {
      if (seed->entry_offset > offset) continue;
      if (best_seed != NULL && best_seed->has_entry_offset && seed->entry_offset < best_offset) continue;
      best_offset = seed->entry_offset;
    } else if (best_seed != NULL && best_seed->has_entry_offset) {
      continue;
    }
    best_seed = seed;
  }
  type_name = amiga_register_seed_struct_type_name(best_seed);
  if (type_name == NULL || type_name[0] == '\0') return 0;
  if (!resolve_amiga_struct_field_symbol_name(type_name, displacement, buf, buf_size)) return 0;
  if (out_type_name != NULL) *out_type_name = type_name;
  return 1;
}

static void seed_amiga_base_regs_from_policy(const SectionAnalysisContext *ctx, uint32_t trace_start,
    uint16_t *addr_reg_base_ids, uint16_t *addr_reg_seed_base_ids, uint16_t *data_reg_base_ids) {
  const M68kAnalysisPolicy *policy = section_analysis_context_policy(ctx);
  const M68kAnalysisRegisterSeed *best_addr_seeds[8] = {0};
  const M68kAnalysisRegisterSeed *best_data_seeds[8] = {0};
  uint16_t index;
  uint8_t reg;
  if (policy == NULL) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if (seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE ||
        seed->reg_index >= 8U ||
        !amiga_register_seed_applies_at_or_before(ctx, seed, trace_start)) continue;
    if (seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS) {
      if (amiga_register_seed_is_better_for_trace(seed, best_addr_seeds[seed->reg_index]))
        best_addr_seeds[seed->reg_index] = seed;
    } else if (seed->reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
      if (amiga_register_seed_is_better_for_trace(seed, best_data_seeds[seed->reg_index]))
        best_data_seeds[seed->reg_index] = seed;
    }
  }
  for (reg = 0U; reg < 8U; ++reg) {
    uint16_t base_id;
    const M68kAnalysisRegisterSeed *seed = best_addr_seeds[reg];
    if (seed != NULL && addr_reg_base_ids != NULL) {
      base_id = amiga_base_id_from_name_local(seed->name);
      if (amiga_base_id_is_none_local(base_id))
        base_id = amiga_base_id_from_name_local(amiga_os_find_library_base_name(seed->name));
      if (!amiga_base_id_is_none_local(base_id)) {
        addr_reg_base_ids[reg] = base_id;
        if (addr_reg_seed_base_ids != NULL) addr_reg_seed_base_ids[reg] = base_id;
      }
    }
    seed = best_data_seeds[reg];
    if (seed != NULL && data_reg_base_ids != NULL) {
      base_id = amiga_base_id_from_name_local(seed->name);
      if (amiga_base_id_is_none_local(base_id))
        base_id = amiga_base_id_from_name_local(amiga_os_find_library_base_name(seed->name));
      if (!amiga_base_id_is_none_local(base_id)) data_reg_base_ids[reg] = base_id;
    }
  }
}

static void apply_amiga_typed_register_seed(const M68kAnalysisRegisterSeed *seed, uint32_t trace_start,
    uint8_t reg_kind, uint8_t reg_index, AmigaValueProvenance *target) {
  const char *type_name;
  uint16_t struct_id;
  if (seed == NULL || target == NULL) return;
  type_name = amiga_register_seed_struct_type_name(seed);
  if (type_name == NULL || type_name[0] == '\0') return;
  struct_id = amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, type_name);
  if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) != NULL) {
    amiga_value_provenance_set_struct_id(target, struct_id);
    amiga_value_provenance_set_owner_struct_id(target, struct_id);
  } else {
    amiga_value_provenance_set_type_name(target, type_name);
    amiga_value_provenance_copy_owner_from_type(target, target);
  }
  amiga_value_provenance_set_symbol_name(target, seed->name);
  target->source_offset = trace_start;
  target->source_reg_kind = reg_kind;
  target->source_reg_index = reg_index;
}

static void seed_amiga_typed_regs_from_policy(const SectionAnalysisContext *ctx, uint32_t trace_start,
    AmigaValueProvenance *data_reg_values, AmigaValueProvenance *addr_reg_values) {
  const M68kAnalysisPolicy *policy = section_analysis_context_policy(ctx);
  const M68kAnalysisRegisterSeed *best_addr_seeds[8] = {0};
  const M68kAnalysisRegisterSeed *best_data_seeds[8] = {0};
  uint16_t index;
  uint8_t reg;
  if (policy == NULL) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if ((seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR &&
         seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE) ||
        seed->reg_index >= 8U ||
        !amiga_register_seed_applies_at_or_before(ctx, seed, trace_start)) continue;
    if (seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS) {
      if (amiga_register_seed_is_better_for_trace(seed, best_addr_seeds[seed->reg_index]))
        best_addr_seeds[seed->reg_index] = seed;
    } else if (seed->reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
      if (amiga_register_seed_is_better_for_trace(seed, best_data_seeds[seed->reg_index]))
        best_data_seeds[seed->reg_index] = seed;
    }
  }
  for (reg = 0U; reg < 8U; ++reg) {
    if (addr_reg_values != NULL) apply_amiga_typed_register_seed(best_addr_seeds[reg], trace_start,
      M68K_ANALYSIS_REGISTER_ADDRESS, reg, &addr_reg_values[reg]);
    if (data_reg_values != NULL) apply_amiga_typed_register_seed(best_data_seeds[reg], trace_start,
      M68K_ANALYSIS_REGISTER_DATA, reg, &data_reg_values[reg]);
  }
}

static void trace_amiga_call_setup(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    uint32_t call_offset, const char **out_a0_seed_base_name, int16_t *out_a1_app_disp,
    const char **out_a1_seed_base_name) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t cursor;
  uint32_t start;
  uint16_t addr_reg_seed_base_ids[8];
  uint16_t addr_reg_base_ids[8];
  uint16_t saved_stack_base_ids[8];
  int16_t addr_reg_app_disp[8];
  size_t saved_stack_base_count = 0U;
  uint8_t reg_index;
  if (out_a0_seed_base_name != NULL) *out_a0_seed_base_name = NULL;
  if (out_a1_app_disp != NULL) *out_a1_app_disp = 0;
  if (out_a1_seed_base_name != NULL) *out_a1_seed_base_name = NULL;
  if (section == NULL || section_analysis == NULL) return;
  init_amiga_base_id_array(addr_reg_seed_base_ids, sizeof(addr_reg_seed_base_ids) / sizeof(addr_reg_seed_base_ids[0]));
  init_amiga_base_id_array(addr_reg_base_ids, sizeof(addr_reg_base_ids) / sizeof(addr_reg_base_ids[0]));
  init_amiga_base_id_array(saved_stack_base_ids, sizeof(saved_stack_base_ids) / sizeof(saved_stack_base_ids[0]));
  for (reg_index = 0U; reg_index < 8U; ++reg_index) addr_reg_app_disp[reg_index] = INT16_MIN;
  addr_reg_base_ids[6] = AMIGA_LOCAL_BASE_ID_APP;
  start = resolve_analysis_trace_start(ctx, section_analysis, call_offset);
  if (start == UINT32_MAX) return;
  seed_amiga_base_regs_from_policy(ctx, start, addr_reg_base_ids, addr_reg_seed_base_ids, NULL);
  cursor = start;
  while (cursor < call_offset && cursor < section->data_size) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    uint8_t dest_reg;
    const M68kOperandIR *source = NULL;
    uint8_t written_reg;
    uint32_t source_target;
    int16_t slot_disp;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    metadata = instruction_sim_metadata(&instruction);
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > call_offset) break;
    {
      PlatformAddressExgInfo exg = instruction_address_exg(&instruction);
      if (exg.ok) {
        uint16_t tmp_base = addr_reg_base_ids[exg.left_reg];
        uint16_t tmp_seed = addr_reg_seed_base_ids[exg.left_reg];
        int16_t tmp_disp = addr_reg_app_disp[exg.left_reg];
        addr_reg_base_ids[exg.left_reg] = addr_reg_base_ids[exg.right_reg];
        addr_reg_base_ids[exg.right_reg] = tmp_base;
        addr_reg_seed_base_ids[exg.left_reg] = addr_reg_seed_base_ids[exg.right_reg];
        addr_reg_seed_base_ids[exg.right_reg] = tmp_seed;
        addr_reg_app_disp[exg.left_reg] = addr_reg_app_disp[exg.right_reg];
        addr_reg_app_disp[exg.right_reg] = tmp_disp;
        cursor += (uint32_t)instruction.byte_count;
        continue;
      }
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_address_reg_approx(&instruction, written_reg)) {
        addr_reg_base_ids[written_reg] = AMIGA_OS_BASE_ID_NONE;
        addr_reg_seed_base_ids[written_reg] = AMIGA_OS_BASE_ID_NONE;
        addr_reg_app_disp[written_reg] = INT16_MIN;
      }
    }
    if (instruction_is_address_move(&instruction, &dest_reg, &source)) {
      if (operand_is_absolute_value(source, 4U)) {
        addr_reg_base_ids[dest_reg] = AMIGA_OS_BASE_ID_SYSBASE;
      } else if (source != NULL && source->kind == M68K_ASM_OPERAND_AN && source->value.reg < 8U) {
        addr_reg_base_ids[dest_reg] = addr_reg_base_ids[source->value.reg];
        addr_reg_seed_base_ids[dest_reg] = addr_reg_seed_base_ids[source->value.reg];
        addr_reg_app_disp[dest_reg] = addr_reg_app_disp[source->value.reg];
      } else if (source != NULL && operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        addr_reg_base_ids[dest_reg] = AMIGA_LOCAL_BASE_ID_APP;
        addr_reg_app_disp[dest_reg] = slot_disp;
      } else if (metadata != NULL &&
          metadata->source_operand_index < instruction.operand_count &&
          instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
            (uint32_t)section->data_size, &source_target)) {
        addr_reg_seed_base_ids[dest_reg] = amiga_base_id_from_name_local(read_amiga_library_seed_name_near(section, source_target));
      }
    } else if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[1], &dest_reg)) {
      source = &instruction.operands[0];
      if (operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        addr_reg_base_ids[dest_reg] = AMIGA_LOCAL_BASE_ID_APP;
        addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        addr_reg_app_disp[dest_reg] = slot_disp;
      } else if ((source->kind == M68K_ASM_OPERAND_EA || source->kind == M68K_ASM_OPERAND_BF_EA) &&
          source->value.ea_mode == 7U && source->value.ea_reg == 2U) {
        source_target = (uint32_t)((int32_t)cursor + 2 + (int32_t)source->value.value);
        addr_reg_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        addr_reg_seed_base_ids[dest_reg] = amiga_base_id_from_name_local(read_amiga_library_seed_name_near(section, source_target));
        addr_reg_app_disp[dest_reg] = INT16_MIN;
      } else if (metadata != NULL &&
          instruction_render_operand_target(&instruction, metadata, 0U, cursor,
            (uint32_t)section->data_size, &source_target)) {
        addr_reg_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        addr_reg_seed_base_ids[dest_reg] = amiga_base_id_from_name_local(read_amiga_library_seed_name_near(section, source_target));
        addr_reg_app_disp[dest_reg] = INT16_MIN;
      }
    }
    {
      PlatformRegisterMatch pushed = instruction_push_address_reg_to_stack(&instruction);
      if (pushed.ok && pushed.reg < 8U &&
          saved_stack_base_count < (sizeof(saved_stack_base_ids) / sizeof(saved_stack_base_ids[0]))) {
        saved_stack_base_ids[saved_stack_base_count++] = addr_reg_base_ids[pushed.reg];
      }
    }
    {
      PlatformRegisterMatch popped = instruction_pop_address_reg_from_stack(&instruction);
      if (popped.ok && saved_stack_base_count != 0U) {
        addr_reg_base_ids[popped.reg] = saved_stack_base_ids[--saved_stack_base_count];
        addr_reg_seed_base_ids[popped.reg] = AMIGA_OS_BASE_ID_NONE;
        addr_reg_app_disp[popped.reg] = INT16_MIN;
      }
    }
    cursor += (uint32_t)instruction.byte_count;
  }
  if (out_a0_seed_base_name != NULL) *out_a0_seed_base_name = amiga_base_name_from_id_local(addr_reg_seed_base_ids[0]);
  if (out_a1_app_disp != NULL) *out_a1_app_disp = addr_reg_app_disp[1];
  if (out_a1_seed_base_name != NULL) *out_a1_seed_base_name = amiga_base_name_from_id_local(addr_reg_seed_base_ids[1]);
  if (section != NULL) {
    uint32_t target;
    if (out_a0_seed_base_name != NULL && *out_a0_seed_base_name == NULL &&
        resolve_amiga_pre_call_absolute_target(ctx, section_analysis, call_offset, 2U, 0U, &target)) {
      const char *seed_name = read_amiga_library_seed_name_near(section, target);
      *out_a0_seed_base_name = amiga_base_name_from_id_local(amiga_base_id_from_name_local(seed_name));
    }
    if (out_a1_seed_base_name != NULL && *out_a1_seed_base_name == NULL &&
        resolve_amiga_pre_call_absolute_target(ctx, section_analysis, call_offset, 2U, 1U, &target)) {
      const char *seed_name = read_amiga_library_seed_name_near(section, target);
      *out_a1_seed_base_name = amiga_base_name_from_id_local(amiga_base_id_from_name_local(seed_name));
    }
  }
}

static int resolve_amiga_pre_call_absolute_target(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t call_offset, uint8_t reg_kind, uint8_t reg_index,
    uint32_t *out_target) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t start;
  uint32_t cursor;
  AmigaResolvedTarget addr_reg_targets[8];
  AmigaResolvedTarget data_reg_targets[8];
  AmigaResolvedTarget prev_addr_reg_targets[8];
  AmigaResolvedTarget prev_data_reg_targets[8];
  AmigaTargetStackEntry saved_stack[AMIGA_TYPED_STACK_CAPACITY];
  size_t saved_stack_count = 0U;
  AmigaTargetLocalSlotEntry local_slots[AMIGA_TYPED_LOCAL_SLOT_CAPACITY];
  uint16_t local_base_ids[8] = {0};
  uint16_t prev_local_base_ids[8];
  uint16_t next_local_base_id = 1U;
  uint8_t written_reg;
  if (out_target != NULL) *out_target = 0U;
  if (ctx == NULL || section == NULL || section_analysis == NULL || reg_index >= 8U) return 0;
  for (written_reg = 0U; written_reg < 8U; ++written_reg) {
    init_amiga_resolved_target(&addr_reg_targets[written_reg]);
    init_amiga_resolved_target(&data_reg_targets[written_reg]);
    prev_local_base_ids[written_reg] = 0U;
    clear_amiga_target_local_slot_entry(&local_slots[written_reg]);
  }
  for (; written_reg < AMIGA_TYPED_LOCAL_SLOT_CAPACITY; ++written_reg) {
    clear_amiga_target_local_slot_entry(&local_slots[written_reg]);
  }
  start = resolve_analysis_trace_start(ctx, section_analysis, call_offset);
  if (start == UINT32_MAX || start > call_offset) return 0;
  {
    uint32_t fallback_start = find_amiga_typed_trace_fallback_start(ctx, call_offset);
    if (fallback_start != UINT32_MAX && fallback_start < start) start = fallback_start;
  }
  for (cursor = start; cursor < call_offset && cursor < section->data_size; ) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    uint8_t mnemonic_id;
    const M68kOperandIR *source = NULL;
    uint8_t dest_reg;
    uint8_t source_reg;
    int16_t slot_disp;
    uint16_t movem_mask;
    uint8_t pushed_reg;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    mnemonic_id = instruction.mnemonic_id;
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > call_offset) break;
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      prev_addr_reg_targets[written_reg] = addr_reg_targets[written_reg];
      prev_data_reg_targets[written_reg] = data_reg_targets[written_reg];
      prev_local_base_ids[written_reg] = local_base_ids[written_reg];
      if (instruction_writes_data_reg_approx(&instruction, written_reg)) {
        init_amiga_resolved_target(&data_reg_targets[written_reg]);
      }
      if (instruction_writes_address_reg_approx(&instruction, written_reg)) {
        clear_amiga_target_local_slots_for_base(local_slots,
          sizeof(local_slots) / sizeof(local_slots[0]), local_base_ids[written_reg]);
        local_base_ids[written_reg] = 0U;
        init_amiga_resolved_target(&addr_reg_targets[written_reg]);
      }
    }
    if (instruction_is_data_move(&instruction, &dest_reg, &source) && source != NULL) {
      uint32_t source_target;
      uint16_t local_base_id;
      int16_t local_slot_disp;
      if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
        data_reg_targets[dest_reg] = prev_data_reg_targets[source_reg];
      } else if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
        data_reg_targets[dest_reg] = prev_addr_reg_targets[source_reg];
      } else if (operand_is_amiga_local_frame_slot(source, prev_local_base_ids, NULL, &local_base_id, &local_slot_disp) &&
          lookup_amiga_target_local_slot_entry(local_slots, sizeof(local_slots) / sizeof(local_slots[0]),
            local_base_id, local_slot_disp, &data_reg_targets[dest_reg])) {
      } else if (operand_is_immediate_source_local(source) && source->value.value < section->data_size) {
        data_reg_targets[dest_reg].target = source->value.value;
        data_reg_targets[dest_reg].valid = 1U;
      } else if (resolve_amiga_absolute_target_from_operand(ctx, cursor, &instruction, source, 0U, &source_target)) {
        data_reg_targets[dest_reg].target = source_target;
        data_reg_targets[dest_reg].valid = 1U;
      }
    } else if (instruction_is_address_move(&instruction, &dest_reg, &source) && source != NULL) {
      uint32_t source_target;
      uint16_t local_base_id;
      int16_t local_slot_disp;
      if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
        addr_reg_targets[dest_reg] = prev_addr_reg_targets[source_reg];
      } else if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
        addr_reg_targets[dest_reg] = prev_data_reg_targets[source_reg];
      } else if (operand_is_amiga_local_frame_slot(source, prev_local_base_ids, NULL, &local_base_id, &local_slot_disp) &&
          lookup_amiga_target_local_slot_entry(local_slots, sizeof(local_slots) / sizeof(local_slots[0]),
            local_base_id, local_slot_disp, &addr_reg_targets[dest_reg])) {
      } else if (operand_is_immediate_source_local(source) && source->value.value < section->data_size) {
        addr_reg_targets[dest_reg].target = source->value.value;
        addr_reg_targets[dest_reg].valid = 1U;
      } else if (resolve_amiga_absolute_target_from_operand(ctx, cursor, &instruction, source, 0U, &source_target)) {
        addr_reg_targets[dest_reg].target = source_target;
        addr_reg_targets[dest_reg].valid = 1U;
      }
    } else if (mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[1], &dest_reg)) {
      uint32_t source_target;
      if (resolve_amiga_absolute_target_from_operand(ctx, cursor, &instruction, &instruction.operands[0], 0U, &source_target)) {
        addr_reg_targets[dest_reg].target = source_target;
        addr_reg_targets[dest_reg].valid = 1U;
      }
    }
    {
      uint16_t local_store_base_id;
      int16_t local_slot_disp;
      uint8_t local_store_source_kind;
      uint8_t local_store_source_reg;
      const M68kOperandIR *source_operand;
      const M68kOperandIR *dest_operand;
      if (instruction_is_register_to_local_frame_slot_store(&instruction, prev_local_base_ids, &local_store_source_kind,
            &local_store_source_reg, &local_store_base_id, &local_slot_disp)) {
        if (local_store_source_kind == 1U && local_store_source_reg < 8U) {
          set_amiga_target_local_slot_entry(local_slots, sizeof(local_slots) / sizeof(local_slots[0]), local_store_base_id,
            local_slot_disp, &prev_data_reg_targets[local_store_source_reg]);
        } else if (local_store_source_kind == 2U && local_store_source_reg < 8U) {
          set_amiga_target_local_slot_entry(local_slots, sizeof(local_slots) / sizeof(local_slots[0]), local_store_base_id,
            local_slot_disp, &prev_addr_reg_targets[local_store_source_reg]);
        }
      } else if (mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction.operand_count == 2U &&
          (source_operand = &instruction.operands[0]) != NULL &&
          (dest_operand = &instruction.operands[1]) != NULL &&
          operand_is_amiga_local_frame_slot(dest_operand, prev_local_base_ids, NULL, &local_store_base_id,
            &local_slot_disp)) {
        if (operand_data_reg_index_local(source_operand, &source_reg) && source_reg < 8U) {
          set_amiga_target_local_slot_entry(local_slots, sizeof(local_slots) / sizeof(local_slots[0]), local_store_base_id,
            local_slot_disp, &prev_data_reg_targets[source_reg]);
        } else if (operand_address_reg_index_local(source_operand, &source_reg) && source_reg < 8U) {
          set_amiga_target_local_slot_entry(local_slots, sizeof(local_slots) / sizeof(local_slots[0]), local_store_base_id,
            local_slot_disp, &prev_addr_reg_targets[source_reg]);
        }
      }
    }
    if (instruction_pushes_data_reg_to_stack_local(&instruction, &pushed_reg) && pushed_reg < 8U) {
      if (saved_stack_count < (sizeof(saved_stack) / sizeof(saved_stack[0]))) {
        saved_stack[saved_stack_count++].value = prev_data_reg_targets[pushed_reg];
      }
    } else {
      PlatformRegisterMatch pushed_addr = instruction_push_address_reg_to_stack(&instruction);
      if (pushed_addr.ok && pushed_addr.reg < 8U) {
        if (saved_stack_count < (sizeof(saved_stack) / sizeof(saved_stack[0]))) {
          saved_stack[saved_stack_count++].value = prev_addr_reg_targets[pushed_addr.reg];
        }
      } else if (instruction_pushes_movem_to_stack_local(&instruction, &movem_mask)) {
        int bit;
        for (bit = 15; bit >= 0; --bit) {
          uint8_t source_reg_kind;
          uint8_t source_reg_index;
          if ((movem_mask & (uint16_t)(1U << bit)) == 0U) continue;
          decode_movem_reg_bit_local((unsigned)bit, &source_reg_kind, &source_reg_index);
          if (saved_stack_count >= (sizeof(saved_stack) / sizeof(saved_stack[0]))) break;
          init_amiga_resolved_target(&saved_stack[saved_stack_count].value);
          if (source_reg_kind == 1U && source_reg_index < 8U) {
            saved_stack[saved_stack_count].value = prev_data_reg_targets[source_reg_index];
          } else if (source_reg_kind == 2U && source_reg_index < 8U) {
            saved_stack[saved_stack_count].value = prev_addr_reg_targets[source_reg_index];
          }
          ++saved_stack_count;
        }
      }
    }
    if (instruction_pops_data_reg_from_stack_local(&instruction, &dest_reg) && dest_reg < 8U) {
      if (saved_stack_count != 0U) data_reg_targets[dest_reg] = saved_stack[--saved_stack_count].value;
    } else {
      PlatformRegisterMatch popped_addr = instruction_pop_address_reg_from_stack(&instruction);
      if (popped_addr.ok && popped_addr.reg < 8U) {
        if (saved_stack_count != 0U) addr_reg_targets[popped_addr.reg] = saved_stack[--saved_stack_count].value;
      } else if (instruction_pops_movem_from_stack_local(&instruction, &movem_mask)) {
        unsigned bit;
        for (bit = 0U; bit < 16U; ++bit) {
          uint8_t dest_reg_kind;
          uint8_t dest_reg_index;
          if ((movem_mask & (uint16_t)(1U << bit)) == 0U || saved_stack_count == 0U) continue;
          decode_movem_reg_bit_local(bit, &dest_reg_kind, &dest_reg_index);
          if (dest_reg_kind == 1U && dest_reg_index < 8U) {
            data_reg_targets[dest_reg_index] = saved_stack[--saved_stack_count].value;
          } else if (dest_reg_kind == 2U && dest_reg_index < 8U) {
            addr_reg_targets[dest_reg_index] = saved_stack[--saved_stack_count].value;
          } else {
            --saved_stack_count;
          }
        }
      }
    }
    if (mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[1], &dest_reg)) {
      source = &instruction.operands[0];
      if (source != NULL && operand_address_reg_index_local(source, &source_reg) && source_reg < 8U &&
          prev_local_base_ids[source_reg] != 0U) {
        local_base_ids[dest_reg] = prev_local_base_ids[source_reg];
      } else if (source != NULL && operand_address_reg_index_local(source, &source_reg) && source_reg == 7U) {
        local_base_ids[dest_reg] = next_local_base_id++;
      }
    } else if (mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[1], &dest_reg) &&
        operand_is_indirect_or_disp_an(&instruction.operands[0], &pushed_reg, &slot_disp)) {
      if (pushed_reg == 7U) {
        local_base_ids[dest_reg] = next_local_base_id++;
      } else if (pushed_reg < 8U && prev_local_base_ids[pushed_reg] != 0U && slot_disp == 0) {
        local_base_ids[dest_reg] = prev_local_base_ids[pushed_reg];
      } else if (pushed_reg < 8U && prev_local_base_ids[pushed_reg] != 0U) {
        local_base_ids[dest_reg] = next_local_base_id++;
      }
    } else if (mnemonic_id == M68K_ASM_MNEMONIC_LINK &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[0], &dest_reg)) {
      local_base_ids[dest_reg] = next_local_base_id++;
    }
    if (decode.is_call) {
      for (written_reg = 0U; written_reg < 8U; ++written_reg) {
        init_amiga_resolved_target(&data_reg_targets[written_reg]);
        init_amiga_resolved_target(&addr_reg_targets[written_reg]);
      }
    }
    cursor += (uint32_t)instruction.byte_count;
  }
  if (reg_kind == 1U && data_reg_targets[reg_index].valid != 0U) {
    if (out_target != NULL) *out_target = data_reg_targets[reg_index].target;
    return 1;
  }
  if (reg_kind == 2U && addr_reg_targets[reg_index].valid != 0U) {
    if (out_target != NULL) *out_target = addr_reg_targets[reg_index].target;
    return 1;
  }
  return 0;
}

static int instruction_preserves_pointer_provenance_local(const M68kInstructionIR *instruction, uint8_t reg_kind,
    uint8_t reg_index) {
  uint8_t mnemonic_id;
  const M68kOperandIR *dest;
  if (instruction->operand_count == 0U) return 0;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0;
  dest = &instruction->operands[instruction->operand_count - 1U];
  if (reg_kind == 1U) {
    if (!operand_is_data_reg_direct(dest, reg_index)) return 0;
  } else if (reg_kind == 2U) {
    {
      uint8_t dest_reg;
      if (!operand_address_reg_index_local(dest, &dest_reg) || dest_reg != reg_index) return 0;
    }
  } else {
    return 0;
  }
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_ADD:
  case M68K_ASM_MNEMONIC_ADDI:
  case M68K_ASM_MNEMONIC_ADDQ:
  case M68K_ASM_MNEMONIC_SUB:
  case M68K_ASM_MNEMONIC_SUBI:
  case M68K_ASM_MNEMONIC_SUBQ:
  case M68K_ASM_MNEMONIC_AND:
  case M68K_ASM_MNEMONIC_ANDI:
  case M68K_ASM_MNEMONIC_OR:
  case M68K_ASM_MNEMONIC_ORI:
  case M68K_ASM_MNEMONIC_EOR:
  case M68K_ASM_MNEMONIC_EORI:
    return 1;
  default:
    return 0;
  }
}

static int operand_is_immediate_source_local(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  return operand->kind == M68K_ASM_OPERAND_IMM ||
    ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 7U && operand->value.ea_reg == 4U);
}

static int instruction_has_unnamed_immediate_operand_local(const M68kInstructionIR *instruction) {
  size_t operand_index;
  if (instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!operand->symbol_ref.has_name && operand_is_immediate_source_local(operand)) return 1;
  }
  return 0;
}

static void init_amiga_resolved_target(AmigaResolvedTarget *value) {
  if (value == NULL) return;
  value->target = 0U;
  value->valid = 0U;
}

static void clear_amiga_target_local_slot_entry(AmigaTargetLocalSlotEntry *entry) {
  if (entry == NULL) return;
  entry->base_id = 0U;
  entry->displacement = 0;
  init_amiga_resolved_target(&entry->value);
}

static void clear_amiga_target_local_slots_for_base(AmigaTargetLocalSlotEntry *slots, size_t slot_count, uint16_t base_id) {
  size_t index;
  if (slots == NULL || base_id == 0U) return;
  for (index = 0U; index < slot_count; ++index) {
    if (slots[index].base_id == base_id) clear_amiga_target_local_slot_entry(&slots[index]);
  }
}

static void set_amiga_target_local_slot_entry(AmigaTargetLocalSlotEntry *slots, size_t slot_count, uint16_t base_id,
    int16_t displacement, const AmigaResolvedTarget *value) {
  size_t index;
  if (slots == NULL || base_id == 0U || value == NULL || value->valid == 0U) return;
  for (index = 0U; index < slot_count; ++index) {
    if (slots[index].base_id == base_id && slots[index].displacement == displacement) {
      slots[index].value = *value;
      return;
    }
  }
  for (index = 0U; index < slot_count; ++index) {
    if (slots[index].base_id == 0U) {
      slots[index].base_id = base_id;
      slots[index].displacement = displacement;
      slots[index].value = *value;
      return;
    }
  }
}

static int lookup_amiga_target_local_slot_entry(const AmigaTargetLocalSlotEntry *slots, size_t slot_count, uint16_t base_id,
    int16_t displacement, AmigaResolvedTarget *out_value) {
  size_t index;
  if (out_value != NULL) init_amiga_resolved_target(out_value);
  if (slots == NULL || base_id == 0U) return 0;
  for (index = 0U; index < slot_count; ++index) {
    if (slots[index].base_id != base_id || slots[index].displacement != displacement || slots[index].value.valid == 0U)
      continue;
    if (out_value != NULL) *out_value = slots[index].value;
    return 1;
  }
  return 0;
}

static int resolve_amiga_absolute_target_from_operand(const SectionAnalysisContext *ctx, uint32_t offset,
    const M68kInstructionIR *instruction, const M68kOperandIR *operand, size_t operand_index, uint32_t *out_target) {
  size_t target_section_index = SIZE_MAX;
  uint32_t target_offset = UINT32_MAX;
  if (out_target != NULL) *out_target = 0U;
  if (operand == NULL ||
      !instruction_operand_absolute_target_ref(ctx, instruction, operand_index, offset, &target_section_index,
        &target_offset) ||
      target_section_index != section_analysis_context_section_index(ctx))
    return 0;
  if (out_target != NULL) *out_target = target_offset;
  return 1;
}

static int lookup_amiga_absolute_typed_slot_operand_value(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, const AmigaTypedTraceState *state, uint32_t offset,
    const M68kInstructionIR *instruction, size_t operand_index, AmigaValueProvenance *out_value) {
  size_t target_section_index = SIZE_MAX;
  uint32_t target_offset = UINT32_MAX;
  if (out_value != NULL) init_amiga_value_provenance(out_value);
  if (ctx == NULL || section_analysis == NULL || state == NULL || instruction == NULL || out_value == NULL ||
      !instruction_operand_absolute_target_ref(ctx, instruction, operand_index, offset, &target_section_index,
        &target_offset)) {
    return 0;
  }
  if (lookup_amiga_absolute_typed_slot_value_local(state->absolute_typed_slots,
      sizeof(state->absolute_typed_slots) / sizeof(state->absolute_typed_slots[0]),
      target_section_index, target_offset, out_value)) {
    return 1;
  }
  return lookup_amiga_global_typed_slot_value_local(ctx, section_analysis, target_section_index, target_offset,
    out_value);
}

static void seed_amiga_absolute_base_slots_before_offset(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t before_offset, AmigaAbsoluteBaseSlotTag *absolute_base_slots,
    size_t absolute_base_slot_count) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint16_t addr_reg_base_ids[8];
  uint16_t data_reg_base_ids[8];
  AmigaBaseSlotTag slot_base_names[AMIGA_BASE_SLOT_TAG_CAPACITY];
  AmigaTypedSlotTag slot_type_names[AMIGA_BASE_SLOT_TAG_CAPACITY];
  uint32_t cursor = 0U;
  size_t section_index = section_analysis_context_section_index(ctx);
  size_t slot_base_count = sizeof(slot_base_names) / sizeof(slot_base_names[0]);
  if (ctx == NULL || section == NULL || section_analysis == NULL || absolute_base_slots == NULL) return;
  init_amiga_base_id_array(addr_reg_base_ids, sizeof(addr_reg_base_ids) / sizeof(addr_reg_base_ids[0]));
  init_amiga_base_id_array(data_reg_base_ids, sizeof(data_reg_base_ids) / sizeof(data_reg_base_ids[0]));
  init_amiga_base_slot_tag_array(slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]));
  init_amiga_typed_slot_tag_array(slot_type_names, sizeof(slot_type_names) / sizeof(slot_type_names[0]));
  seed_amiga_base_slot_tags_from_effects(section_analysis, slot_base_names, slot_base_count);
  {
    size_t index;
    for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
      const M68kRecoveredPlatformBaseSlotIR *slot = &section_analysis->recovered_platform_base_slots[index];
      set_amiga_base_slot_id_local(slot_base_names, slot_base_count, slot->displacement,
        !amiga_base_id_is_none_local(slot->base_ref.id) ? slot->base_ref.id : amiga_base_id_from_name_local(slot->base_name));
    }
  }
  addr_reg_base_ids[6] = AMIGA_LOCAL_BASE_ID_APP;
  seed_amiga_base_regs_from_policy(ctx, 0U, addr_reg_base_ids, NULL, data_reg_base_ids);
  while (cursor < before_offset && cursor < section->data_size) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    uint16_t prev_addr_reg_base_ids[8];
    uint16_t prev_data_reg_base_ids[8];
    uint8_t reg;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) {
      ++cursor;
      continue;
    }
    instruction = decode.instruction;
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > before_offset) break;
    for (reg = 0U; reg < 8U; ++reg) {
      prev_addr_reg_base_ids[reg] = addr_reg_base_ids[reg];
      prev_data_reg_base_ids[reg] = data_reg_base_ids[reg];
    }
    for (reg = 0U; reg < 8U; ++reg) {
      if (instruction_writes_address_reg_approx(&instruction, reg)) addr_reg_base_ids[reg] = AMIGA_OS_BASE_ID_NONE;
      if (instruction_writes_data_reg_approx(&instruction, reg)) data_reg_base_ids[reg] = AMIGA_OS_BASE_ID_NONE;
    }
    {
      uint8_t dest_reg;
      uint8_t source_reg;
      int16_t slot_disp;
      uint32_t source_target;
      uint16_t slot_base_id;
      const M68kOperandIR *source = NULL;
      if (instruction_is_data_move(&instruction, &dest_reg, &source) && source != NULL) {
        if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
          data_reg_base_ids[dest_reg] = prev_data_reg_base_ids[source_reg];
        } else if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
          data_reg_base_ids[dest_reg] = prev_addr_reg_base_ids[source_reg];
        } else if (resolve_amiga_absolute_target_from_operand(ctx, cursor, &instruction, source, 0U, &source_target)) {
          data_reg_base_ids[dest_reg] = lookup_amiga_absolute_base_slot_id_local(absolute_base_slots,
            absolute_base_slot_count, section_index, source_target);
        }
      } else if (instruction_is_address_move(&instruction, &dest_reg, &source) && source != NULL) {
        if (operand_is_absolute_value(source, 4U)) {
          addr_reg_base_ids[dest_reg] = AMIGA_OS_BASE_ID_SYSBASE;
        } else if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
          addr_reg_base_ids[dest_reg] = prev_addr_reg_base_ids[source_reg];
        } else if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
          addr_reg_base_ids[dest_reg] = prev_data_reg_base_ids[source_reg];
        } else if (!amiga_base_id_is_none_local((slot_base_id = lookup_amiga_app_slot_base_id_for_operand(
            section_analysis, slot_base_names, slot_base_count, source, prev_addr_reg_base_ids[6], &slot_disp)))) {
          addr_reg_base_ids[dest_reg] = slot_base_id;
        } else if (resolve_amiga_absolute_target_from_operand(ctx, cursor, &instruction, source, 0U, &source_target)) {
          addr_reg_base_ids[dest_reg] = lookup_amiga_absolute_base_slot_id_local(absolute_base_slots,
            absolute_base_slot_count, section_index, source_target);
        }
      }
    }
    if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction.operand_count == 2U &&
        instruction.size_suffix == 'l') {
      const M68kOperandIR *src = &instruction.operands[0];
      const M68kOperandIR *dst = &instruction.operands[1];
      uint32_t target_offset = UINT32_MAX;
      uint16_t stored_base_id = AMIGA_OS_BASE_ID_NONE;
      uint8_t source_reg;
      int16_t slot_disp;
      if ((dst->kind == M68K_ASM_OPERAND_EA || dst->kind == M68K_ASM_OPERAND_BF_EA) &&
          dst->value.ea_mode == 7U && (dst->value.ea_reg == 0U || dst->value.ea_reg == 1U) &&
          dst->value.value < section->data_size) {
        target_offset = dst->value.value;
      }
      if (target_offset != UINT32_MAX) {
        if (operand_data_reg_index_local(src, &source_reg) && source_reg < 8U)
          stored_base_id = prev_data_reg_base_ids[source_reg];
        else if (operand_address_reg_index_local(src, &source_reg) && source_reg < 8U)
          stored_base_id = prev_addr_reg_base_ids[source_reg];
        else
          stored_base_id = lookup_amiga_app_slot_base_id_for_operand(section_analysis, slot_base_names,
            slot_base_count, src, prev_addr_reg_base_ids[6], &slot_disp);
        set_amiga_absolute_base_slot_id_local(absolute_base_slots, absolute_base_slot_count, section_index, target_offset,
          stored_base_id);
      }
    }
    apply_recovered_amiga_platform_effects(section_analysis, cursor, data_reg_base_ids, addr_reg_base_ids,
      NULL, NULL, slot_base_names, slot_base_count, slot_type_names, sizeof(slot_type_names) / sizeof(slot_type_names[0]));
    cursor += (uint32_t)instruction.byte_count;
  }
}

static void amiga_call_effect_reg_state_clear(AmigaCallEffectRegState *state) {
  size_t reg_index;
  if (state == NULL) return;
  for (reg_index = 0U; reg_index < 8U; ++reg_index) {
    state->data_reg_base_ids[reg_index] = AMIGA_OS_BASE_ID_NONE;
    state->addr_reg_base_ids[reg_index] = AMIGA_OS_BASE_ID_NONE;
    init_amiga_value_provenance(&state->data_reg_values[reg_index]);
    init_amiga_value_provenance(&state->addr_reg_values[reg_index]);
  }
}

static void amiga_call_effect_reg_state_copy(AmigaCallEffectRegState *dst, const AmigaCallEffectRegState *src) {
  if (dst == NULL || src == NULL) return;
  *dst = *src;
}

static int join_consistent_amiga_type_ref_local(uint16_t existing_type_id, uint16_t existing_struct_id,
    uint16_t candidate_type_id, uint16_t candidate_struct_id, uint16_t *out_type_id, uint16_t *out_struct_id) {
  uint32_t existing_key = amiga_type_ref_key_local(existing_type_id, existing_struct_id);
  uint32_t candidate_key = amiga_type_ref_key_local(candidate_type_id, candidate_struct_id);
  if (out_type_id != NULL) *out_type_id = AMIGA_OS_TYPE_ID_NONE;
  if (out_struct_id != NULL) *out_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (existing_key == 0U && candidate_key == 0U) return 1;
  if (existing_key == 0U || candidate_key == 0U || existing_key != candidate_key) return 0;
  if (out_type_id != NULL) {
    *out_type_id = amiga_os_name(M68K_PLATFORM_NAME_TYPE, existing_type_id) != NULL
      ? existing_type_id
      : candidate_type_id;
  }
  if (out_struct_id != NULL) {
    *out_struct_id = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, existing_struct_id) != NULL
      ? existing_struct_id
      : candidate_struct_id;
  }
  return 1;
}

static uint16_t join_consistent_amiga_os_name_id(uint8_t domain_kind, uint16_t existing_id, uint16_t candidate_id) {
  if (amiga_os_name(domain_kind, existing_id) != NULL && existing_id == candidate_id) return existing_id;
  if (domain_kind == M68K_PLATFORM_NAME_STRUCT) return AMIGA_OS_STRUCT_ID_NONE;
  if (domain_kind == M68K_PLATFORM_NAME_SEMANTIC_KIND) return AMIGA_OS_SEMANTIC_KIND_ID_NONE;
  if (domain_kind == M68K_PLATFORM_NAME_VALUE_DOMAIN) return AMIGA_OS_VALUE_DOMAIN_ID_NONE;
  if (domain_kind == M68K_PLATFORM_NAME_SYMBOL) return AMIGA_OS_SYMBOL_ID_NONE;
  if (domain_kind == M68K_PLATFORM_NAME_BASE) return AMIGA_OS_BASE_ID_NONE;
  return AMIGA_OS_TYPE_ID_NONE;
}

static void clear_amiga_call_effect_value(AmigaValueProvenance *value) {
  init_amiga_value_provenance(value);
}

static int join_amiga_call_effect_value(AmigaValueProvenance *dst, const AmigaValueProvenance *src) {
  int changed = 0;
  uint16_t joined_id;
  uint16_t joined_struct_id;
  int16_t joined_disp;
  if (dst == NULL || src == NULL) return 0;
  joined_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (!join_consistent_amiga_type_ref_local(dst->type_id, dst->struct_id, src->type_id, src->struct_id,
        &joined_id, &joined_struct_id)) {
    joined_id = AMIGA_OS_TYPE_ID_NONE;
    joined_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  }
  if (joined_id != dst->type_id || joined_struct_id != dst->struct_id) {
    dst->type_id = joined_id;
    dst->struct_id = joined_struct_id;
    changed = 1;
  }
  joined_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (!join_consistent_amiga_type_ref_local(dst->owner_type_id, dst->owner_struct_id,
        src->owner_type_id, src->owner_struct_id, &joined_id, &joined_struct_id)) {
    joined_id = AMIGA_OS_TYPE_ID_NONE;
    joined_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  }
  if (joined_id != dst->owner_type_id || joined_struct_id != dst->owner_struct_id) {
    dst->owner_type_id = joined_id;
    dst->owner_struct_id = joined_struct_id;
    changed = 1;
  }
  joined_id = join_consistent_amiga_os_name_id(M68K_PLATFORM_NAME_SYMBOL, dst->symbol_id, src->symbol_id);
  if (joined_id != dst->symbol_id) {
    dst->symbol_id = joined_id;
    changed = 1;
  }
  joined_id = join_consistent_amiga_os_name_id(M68K_PLATFORM_NAME_BASE, dst->context_base_id, src->context_base_id);
  if (joined_id != dst->context_base_id) {
    dst->context_base_id = joined_id;
    changed = 1;
  }
  joined_id = join_consistent_amiga_os_name_id(M68K_PLATFORM_NAME_SEMANTIC_KIND, dst->semantic_kind_id, src->semantic_kind_id);
  if (joined_id != dst->semantic_kind_id) {
    dst->semantic_kind_id = joined_id;
    changed = 1;
  }
  joined_id = join_consistent_amiga_os_name_id(M68K_PLATFORM_NAME_VALUE_DOMAIN, dst->value_domain_id, src->value_domain_id);
  if (joined_id != dst->value_domain_id) {
    dst->value_domain_id = joined_id;
    changed = 1;
  }
  joined_id = join_consistent_amiga_os_name_id(M68K_PLATFORM_NAME_SYMBOL, dst->field_symbol_id, src->field_symbol_id);
  if (joined_id != dst->field_symbol_id) {
    dst->field_symbol_id = joined_id;
    changed = 1;
  }
  if (dst->has_constant_value != src->has_constant_value ||
      (dst->has_constant_value && dst->constant_value != src->constant_value)) {
    dst->has_constant_value = 0U;
    dst->constant_value = 0;
    dst->source_offset = UINT32_MAX;
    dst->source_reg_kind = 0U;
    dst->source_reg_index = 0U;
    changed = 1;
  } else if (dst->has_constant_value &&
      (dst->source_offset != src->source_offset ||
       dst->source_reg_kind != src->source_reg_kind ||
       dst->source_reg_index != src->source_reg_index)) {
    dst->source_offset = UINT32_MAX;
    dst->source_reg_kind = 0U;
    dst->source_reg_index = 0U;
    changed = 1;
  }
  joined_disp = (dst->slot_disp == src->slot_disp) ? dst->slot_disp : INT16_MIN;
  if (joined_disp != dst->slot_disp) {
    dst->slot_disp = joined_disp;
    changed = 1;
  }
  joined_disp = (dst->field_disp == src->field_disp) ? dst->field_disp : INT16_MIN;
  if (joined_disp != dst->field_disp) {
    dst->field_disp = joined_disp;
    changed = 1;
  }
  return changed;
}

static int amiga_call_effect_reg_state_join(AmigaCallEffectRegState *dst, const AmigaCallEffectRegState *src) {
  int changed = 0;
  uint8_t reg;
  if (dst == NULL || src == NULL) return 0;
  for (reg = 0U; reg < 8U; ++reg) {
    uint16_t joined_id;
    joined_id = join_consistent_amiga_os_name_id(M68K_PLATFORM_NAME_BASE, dst->data_reg_base_ids[reg], src->data_reg_base_ids[reg]);
    if (joined_id != dst->data_reg_base_ids[reg]) {
      dst->data_reg_base_ids[reg] = joined_id;
      changed = 1;
    }
    joined_id = join_consistent_amiga_os_name_id(M68K_PLATFORM_NAME_BASE, dst->addr_reg_base_ids[reg], src->addr_reg_base_ids[reg]);
    if (joined_id != dst->addr_reg_base_ids[reg]) {
      dst->addr_reg_base_ids[reg] = joined_id;
      changed = 1;
    }
    changed |= join_amiga_call_effect_value(&dst->data_reg_values[reg], &src->data_reg_values[reg]);
    changed |= join_amiga_call_effect_value(&dst->addr_reg_values[reg], &src->addr_reg_values[reg]);
  }
  return changed;
}

static void clear_all_amiga_call_effect_regs(AmigaCallEffectRegState *state) {
  uint8_t reg;
  if (state == NULL) return;
  for (reg = 0U; reg < 8U; ++reg) {
    state->data_reg_base_ids[reg] = AMIGA_OS_BASE_ID_NONE;
    state->addr_reg_base_ids[reg] = AMIGA_OS_BASE_ID_NONE;
    clear_amiga_call_effect_value(&state->data_reg_values[reg]);
    clear_amiga_call_effect_value(&state->addr_reg_values[reg]);
  }
}

static void apply_recovered_amiga_platform_effect_to_call_state(const M68kRecoveredPlatformEffectIR *effect,
    uint32_t offset, AmigaCallEffectRegState *state) {
  if (effect == NULL || effect->offset != offset || state == NULL) return;
  if (effect->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG) {
    uint16_t base_id = amiga_named_base_payload_id_local(&effect->payload.named_base);
    const char *base_type_name = resolve_amiga_base_type_name_from_id_local(base_id);
    if (amiga_base_id_is_none_local(base_id)) return;
    if (effect->reg_kind == 1U && effect->reg_index < 8U) {
      amiga_call_effect_reg_state_set_base_id(state, 1U, effect->reg_index, base_id);
      if (amiga_value_provenance_type_name_local(&state->data_reg_values[effect->reg_index]) == NULL) {
        amiga_value_provenance_set_type_name(&state->data_reg_values[effect->reg_index], base_type_name);
        amiga_value_provenance_set_owner_type_name(&state->data_reg_values[effect->reg_index], base_type_name);
      }
    } else if (effect->reg_kind == 2U && effect->reg_index < 8U) {
      amiga_call_effect_reg_state_set_base_id(state, 2U, effect->reg_index, base_id);
      if (amiga_value_provenance_type_name_local(&state->addr_reg_values[effect->reg_index]) == NULL) {
        amiga_value_provenance_set_type_name(&state->addr_reg_values[effect->reg_index], base_type_name);
        amiga_value_provenance_set_owner_type_name(&state->addr_reg_values[effect->reg_index], base_type_name);
      }
    }
  } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
    if (effect->reg_kind == 1U && effect->reg_index < 8U) {
      amiga_typed_payload_apply_to_value_local(&state->data_reg_values[effect->reg_index], &effect->payload.typed);
      state->data_reg_values[effect->reg_index].source_offset = offset;
      state->data_reg_values[effect->reg_index].source_reg_kind = effect->reg_kind;
      state->data_reg_values[effect->reg_index].source_reg_index = effect->reg_index;
    } else if (effect->reg_kind == 2U && effect->reg_index < 8U) {
      amiga_typed_payload_apply_to_value_local(&state->addr_reg_values[effect->reg_index], &effect->payload.typed);
      state->addr_reg_values[effect->reg_index].source_offset = offset;
      state->addr_reg_values[effect->reg_index].source_reg_kind = effect->reg_kind;
      state->addr_reg_values[effect->reg_index].source_reg_index = effect->reg_index;
    }
  }
}

static void apply_recovered_amiga_platform_effects_to_call_state(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, AmigaCallEffectRegState *state) {
  size_t index;
  const M68kRecoveredPlatformEffectIR *effect;
  if (section_analysis == NULL || state == NULL) return;
  if (section_analysis->recovered_platform_effect_lookup != NULL) {
    for (effect = first_recovered_platform_effect_at_offset(section_analysis, offset); effect != NULL;
         effect = next_recovered_platform_effect_at_same_offset(section_analysis, effect)) {
      apply_recovered_amiga_platform_effect_to_call_state(effect, offset, state);
    }
    return;
  }
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    apply_recovered_amiga_platform_effect_to_call_state(&section_analysis->recovered_platform_effects[index], offset,
      state);
  }
}

static void update_amiga_call_effect_reg_state_for_instruction(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, const M68kInstructionIR *instruction, uint32_t offset,
    const AmigaCallEffectRegState *prev_state, AmigaCallEffectRegState *state) {
  uint8_t reg_index;
  uint8_t dest_reg;
  uint8_t source_reg;
  const M68kOperandIR *source = NULL;
  if (prev_state == NULL || state == NULL) return;
  amiga_call_effect_reg_state_copy(state, prev_state);
  for (reg_index = 0U; reg_index < 8U; ++reg_index) {
    if (instruction_writes_data_reg_approx(instruction, reg_index)) {
      amiga_call_effect_reg_state_clear_base(state, 1U, reg_index);
      clear_amiga_call_effect_value(&state->data_reg_values[reg_index]);
    }
    if (instruction_writes_address_reg_approx(instruction, reg_index)) {
      amiga_call_effect_reg_state_clear_base(state, 2U, reg_index);
      clear_amiga_call_effect_value(&state->addr_reg_values[reg_index]);
    }
  }
  if (instruction_is_data_move(instruction, &dest_reg, &source) && source != NULL) {
    if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
      state->data_reg_base_ids[dest_reg] = prev_state->data_reg_base_ids[source_reg];
      state->data_reg_values[dest_reg] = prev_state->data_reg_values[source_reg];
    } else if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
      state->data_reg_base_ids[dest_reg] = prev_state->addr_reg_base_ids[source_reg];
      state->data_reg_values[dest_reg] = prev_state->addr_reg_values[source_reg];
    } else {
      int16_t field_disp = 0;
      if (operand_is_indirect_or_disp_an(source, &source_reg, &field_disp) && source_reg < 8U &&
          (amiga_value_provenance_type_name_local(&prev_state->addr_reg_values[source_reg]) != NULL ||
           amiga_value_provenance_owner_type_name_local(&prev_state->addr_reg_values[source_reg]) != NULL ||
           prev_state->addr_reg_values[source_reg].slot_disp != INT16_MIN)) {
        const char *container_type = amiga_value_provenance_type_name_local(&prev_state->addr_reg_values[source_reg]) != NULL
          ? amiga_value_provenance_type_name_local(&prev_state->addr_reg_values[source_reg])
          : amiga_value_provenance_owner_type_name_local(&prev_state->addr_reg_values[source_reg]);
        char field_symbol_name[64];
        amiga_value_provenance_set_type_name(&state->data_reg_values[dest_reg],
          resolve_amiga_struct_field_nested_type_name(container_type, field_disp));
        amiga_value_provenance_set_owner_type_name(&state->data_reg_values[dest_reg], container_type);
        state->data_reg_values[dest_reg].slot_disp = prev_state->addr_reg_values[source_reg].slot_disp;
        state->data_reg_values[dest_reg].field_disp = field_disp;
        state->data_reg_values[dest_reg].source_offset = offset;
        state->data_reg_values[dest_reg].source_reg_kind = 1U;
        state->data_reg_values[dest_reg].source_reg_index = dest_reg;
        if (resolve_amiga_struct_field_symbol_name(container_type, field_disp, field_symbol_name,
              sizeof(field_symbol_name))) {
          amiga_value_provenance_set_field_symbol_name(&state->data_reg_values[dest_reg], field_symbol_name);
          amiga_value_provenance_set_value_domain_name(&state->data_reg_values[dest_reg],
            amiga_os_find_struct_field_value_domain(container_type, field_symbol_name, NULL));
        }
      }
    }
  }
  if (instruction_is_address_move(instruction, &dest_reg, &source) && source != NULL) {
    if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
      state->addr_reg_base_ids[dest_reg] = prev_state->addr_reg_base_ids[source_reg];
      state->addr_reg_values[dest_reg] = prev_state->addr_reg_values[source_reg];
    } else if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
      state->addr_reg_base_ids[dest_reg] = prev_state->data_reg_base_ids[source_reg];
      state->addr_reg_values[dest_reg] = prev_state->data_reg_values[source_reg];
    } else {
      int16_t slot_disp;
      if (operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        AmigaValueProvenance loaded_value;
        uint16_t loaded_base_id = resolve_amiga_app_slot_base_id(ctx, section_analysis, slot_disp);
        if (lookup_recovered_platform_typed_slot_value(section_analysis, slot_disp, &loaded_value)) {
          state->addr_reg_values[dest_reg] = loaded_value;
        }
        if (amiga_value_provenance_type_name_local(&state->addr_reg_values[dest_reg]) == NULL) {
          amiga_value_provenance_set_type_name(&state->addr_reg_values[dest_reg],
            resolve_amiga_base_type_name_from_id_local(loaded_base_id));
        }
        if (amiga_value_provenance_owner_type_name_local(&state->addr_reg_values[dest_reg]) == NULL) {
          amiga_value_provenance_copy_owner_from_type(&state->addr_reg_values[dest_reg],
            &state->addr_reg_values[dest_reg]);
        }
        state->addr_reg_values[dest_reg].slot_disp = slot_disp;
        state->addr_reg_values[dest_reg].source_offset = offset;
        state->addr_reg_values[dest_reg].source_reg_kind = 2U;
        state->addr_reg_values[dest_reg].source_reg_index = dest_reg;
      } else if (operand_is_indirect_or_disp_an(source, &source_reg, &slot_disp) && source_reg < 8U &&
          (amiga_value_provenance_type_name_local(&prev_state->addr_reg_values[source_reg]) != NULL ||
           amiga_value_provenance_owner_type_name_local(&prev_state->addr_reg_values[source_reg]) != NULL ||
           prev_state->addr_reg_values[source_reg].slot_disp != INT16_MIN)) {
        const char *container_type = amiga_value_provenance_type_name_local(&prev_state->addr_reg_values[source_reg]) != NULL
          ? amiga_value_provenance_type_name_local(&prev_state->addr_reg_values[source_reg])
          : amiga_value_provenance_owner_type_name_local(&prev_state->addr_reg_values[source_reg]);
        char field_symbol_name[64];
        amiga_value_provenance_set_type_name(&state->addr_reg_values[dest_reg],
          resolve_amiga_struct_field_nested_type_name(container_type, slot_disp));
        amiga_value_provenance_set_owner_type_name(&state->addr_reg_values[dest_reg], container_type);
        state->addr_reg_values[dest_reg].slot_disp = prev_state->addr_reg_values[source_reg].slot_disp;
        state->addr_reg_values[dest_reg].field_disp = slot_disp;
        state->addr_reg_values[dest_reg].source_offset = offset;
        state->addr_reg_values[dest_reg].source_reg_kind = 2U;
        state->addr_reg_values[dest_reg].source_reg_index = dest_reg;
        if (resolve_amiga_struct_field_symbol_name(container_type, slot_disp, field_symbol_name,
              sizeof(field_symbol_name))) {
          amiga_value_provenance_set_field_symbol_name(&state->addr_reg_values[dest_reg], field_symbol_name);
          amiga_value_provenance_set_value_domain_name(&state->addr_reg_values[dest_reg],
            amiga_os_find_struct_field_value_domain(container_type, field_symbol_name, NULL));
        }
      }
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      operand_address_reg_index_local(&instruction->operands[1], &dest_reg)) {
    int16_t slot_disp;
    if (operand_is_app_base_disp_ea(&instruction->operands[0], 6U, &slot_disp)) {
      AmigaValueProvenance loaded_value;
      uint16_t loaded_base_id = resolve_amiga_app_slot_base_id(ctx, section_analysis, slot_disp);
      if (lookup_recovered_platform_typed_slot_value(section_analysis, slot_disp, &loaded_value)) {
        state->addr_reg_values[dest_reg] = loaded_value;
      }
      if (amiga_value_provenance_type_name_local(&state->addr_reg_values[dest_reg]) == NULL) {
        amiga_value_provenance_set_type_name(&state->addr_reg_values[dest_reg],
          resolve_amiga_base_type_name_from_id_local(loaded_base_id));
      }
      if (amiga_value_provenance_owner_type_name_local(&state->addr_reg_values[dest_reg]) == NULL) {
        amiga_value_provenance_copy_owner_from_type(&state->addr_reg_values[dest_reg],
          &state->addr_reg_values[dest_reg]);
      }
      state->addr_reg_values[dest_reg].slot_disp = slot_disp;
      state->addr_reg_values[dest_reg].source_offset = offset;
      state->addr_reg_values[dest_reg].source_reg_kind = 2U;
      state->addr_reg_values[dest_reg].source_reg_index = dest_reg;
    }
  }
}

static int seed_amiga_call_effect_reg_state_from_call_entry(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const AmigaOsLibraryVectorInfo *call_entry,
    AmigaCallEffectRegState *out_state) {
  const char *returned_base_name = NULL;
  uint16_t returned_base_id = 0U;
  const AmigaOsCallOutputInfo *output_info;
  uint8_t effect_reg_kind;
  uint8_t effect_reg_index;
  int changed = 0;
  if (out_state != NULL) amiga_call_effect_reg_state_clear(out_state);
  if (ctx == NULL || section_analysis == NULL || call_entry == NULL || out_state == NULL) return 0;
  if (call_entry->returns_base_reg_kind != 0U && call_entry->returns_base_name_reg_kind == AMIGA_OS_REGISTER_ADDRESS) {
    effect_reg_kind = call_entry->returns_base_reg_kind;
    effect_reg_index = call_entry->returns_base_reg_index;
    if (call_entry->returns_base_name_reg_index == 0U) {
      trace_amiga_call_setup(ctx, section_analysis, offset, &returned_base_name, NULL, NULL);
    } else if (call_entry->returns_base_name_reg_index == 1U) {
      trace_amiga_call_setup(ctx, section_analysis, offset, NULL, NULL, &returned_base_name);
    }
    returned_base_id = amiga_base_id_from_name_local(returned_base_name);
    if (amiga_base_id_is_none_local(returned_base_id)) {
      returned_base_name = amiga_os_find_library_base_name(returned_base_name);
      returned_base_id = amiga_base_id_from_name_local(returned_base_name);
    }
    if (!amiga_base_id_is_none_local(returned_base_id)) {
      if (effect_reg_kind == 1U && effect_reg_index < 8U) {
        const char *base_type_name = resolve_amiga_base_type_name_from_id_local(returned_base_id);
        amiga_call_effect_reg_state_set_base_id(out_state, 1U, effect_reg_index, returned_base_id);
        amiga_value_provenance_set_type_name(&out_state->data_reg_values[effect_reg_index], base_type_name);
        amiga_value_provenance_set_owner_type_name(&out_state->data_reg_values[effect_reg_index], base_type_name);
      } else if (effect_reg_kind == 2U && effect_reg_index < 8U) {
        const char *base_type_name = resolve_amiga_base_type_name_from_id_local(returned_base_id);
        amiga_call_effect_reg_state_set_base_id(out_state, 2U, effect_reg_index, returned_base_id);
        amiga_value_provenance_set_type_name(&out_state->addr_reg_values[effect_reg_index], base_type_name);
        amiga_value_provenance_set_owner_type_name(&out_state->addr_reg_values[effect_reg_index], base_type_name);
      }
      changed = 1;
    }
  }
  output_info = &call_entry->output;
  if (output_info->reg_kind != 0U &&
      (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, output_info->struct_id) != NULL ||
       amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output_info->semantic_kind_id) != NULL ||
       amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output_info->value_domain_id) != NULL)) {
    effect_reg_kind = output_info->reg_kind;
    effect_reg_index = output_info->reg_index;
    if (effect_reg_kind == 1U && effect_reg_index < 8U) {
      amiga_value_provenance_set_struct_id(&out_state->data_reg_values[effect_reg_index], output_info->struct_id);
      amiga_value_provenance_set_owner_struct_id(&out_state->data_reg_values[effect_reg_index], output_info->struct_id);
      amiga_value_provenance_set_symbol_id(&out_state->data_reg_values[effect_reg_index], output_info->output_id);
      amiga_value_provenance_set_semantic_kind_id(&out_state->data_reg_values[effect_reg_index],
        output_info->semantic_kind_id);
      amiga_value_provenance_set_value_domain_id(&out_state->data_reg_values[effect_reg_index],
        output_info->value_domain_id);
      changed = 1;
    } else if (effect_reg_kind == 2U && effect_reg_index < 8U) {
      amiga_value_provenance_set_struct_id(&out_state->addr_reg_values[effect_reg_index], output_info->struct_id);
      amiga_value_provenance_set_owner_struct_id(&out_state->addr_reg_values[effect_reg_index], output_info->struct_id);
      amiga_value_provenance_set_symbol_id(&out_state->addr_reg_values[effect_reg_index], output_info->output_id);
      amiga_value_provenance_set_semantic_kind_id(&out_state->addr_reg_values[effect_reg_index],
        output_info->semantic_kind_id);
      amiga_value_provenance_set_value_domain_id(&out_state->addr_reg_values[effect_reg_index],
        output_info->value_domain_id);
      changed = 1;
    }
  }
  return changed;
}

static int resolve_local_data_reg_immediate_seed(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int32_t *out_value) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t cursor;
  uint32_t start;
  int have_value = 0;
  int32_t value = 0;
  if (out_value != NULL) *out_value = 0;
  if (section == NULL || section_analysis == NULL || reg >= 8U) return 0;
  start = resolve_analysis_trace_start(ctx, section_analysis, offset);
  if (start == UINT32_MAX || start > offset) return 0;
  {
    uint32_t fallback_start = find_amiga_typed_trace_fallback_start(ctx, offset);
    if (fallback_start != UINT32_MAX && fallback_start < start) start = fallback_start;
  }
  for (cursor = start; cursor < offset && cursor < section->data_size; ) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    uint8_t mnemonic_id;
    uint8_t dest_reg;
    const M68kOperandIR *source = NULL;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    mnemonic_id = instruction.mnemonic_id;
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > offset) break;
    if (instruction_writes_data_reg_approx(&instruction, reg)) {
      if (mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
          instruction.operand_count == 2U &&
          operand_is_data_reg_direct(&instruction.operands[1], reg) &&
          operand_is_immediate_source_local(&instruction.operands[0])) {
        value = (int32_t)m68k_sign_extend32(instruction.operands[0].value.value, 8U);
        have_value = 1;
      } else if (instruction_is_data_move(&instruction, &dest_reg, &source) &&
          dest_reg == reg && operand_is_immediate_source_local(source)) {
        uint32_t raw_value = source->value.value;
        if (mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) raw_value = m68k_sign_extend32(raw_value, 8U);
        value = (int32_t)raw_value;
        have_value = 1;
      } else if (mnemonic_id == M68K_ASM_MNEMONIC_CLR &&
          instruction.operand_count != 0U &&
          operand_is_data_reg_direct(&instruction.operands[instruction.operand_count - 1U], reg)) {
        value = 0;
        have_value = 1;
      } else {
        have_value = 0;
      }
    }
    cursor += (uint32_t)instruction.byte_count;
  }
  if (have_value && out_value != NULL) *out_value = value;
  return have_value;
}

static int instruction_is_immediate_seed_to_reg_local(const M68kInstructionIR *instruction, uint8_t *out_reg_kind,
    uint8_t *out_reg_index, int32_t *out_value) {
  uint8_t dest_reg;
  uint8_t mnemonic_id;
  const M68kOperandIR *source = NULL;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (out_value != NULL) *out_value = 0;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      instruction->operand_count == 2U &&
      operand_is_immediate_source_local(&instruction->operands[0]) &&
      operand_data_reg_index_local(&instruction->operands[1], &dest_reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 1U;
    if (out_reg_index != NULL) *out_reg_index = dest_reg;
    if (out_value != NULL) *out_value = (int32_t)m68k_sign_extend32(instruction->operands[0].value.value, 8U);
    return 1;
  }
  if (instruction_is_data_move(instruction, &dest_reg, &source) && operand_is_immediate_source_local(source)) {
    if (out_reg_kind != NULL) *out_reg_kind = 1U;
    if (out_reg_index != NULL) *out_reg_index = dest_reg;
    if (out_value != NULL) *out_value = (int32_t)source->value.value;
    return 1;
  }
  if (instruction_is_address_move(instruction, &dest_reg, &source) && operand_is_immediate_source_local(source)) {
    if (out_reg_kind != NULL) *out_reg_kind = 2U;
    if (out_reg_index != NULL) *out_reg_index = dest_reg;
    if (out_value != NULL) *out_value = (int32_t)source->value.value;
    return 1;
  }
  return 0;
}

static const AmigaOsCallInputInfo *find_amiga_call_input_for_reg(const AmigaOsLibraryVectorInfo *entry, uint8_t reg_kind,
    uint8_t reg_index) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count;
  size_t index;
  uint8_t input_reg_kind;
  uint8_t input_reg_index;
  if (entry == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(entry, &input_count);
  for (index = 0U; index < input_count; ++index) {
    if (inputs[index].reg_kind == 0U) continue;
    input_reg_kind = inputs[index].reg_kind;
    input_reg_index = inputs[index].reg_index;
    if (input_reg_kind == reg_kind && input_reg_index == reg_index) return &inputs[index];
  }
  return NULL;
}

static int resolve_next_amiga_call_input_for_reg(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    uint8_t reg_kind, uint8_t reg_index, const AmigaOsLibraryVectorInfo **out_call_entry,
    const AmigaOsCallInputInfo **out_input_info) {
  const M68kSection *section;
  uint32_t cursor;
  if (out_call_entry != NULL) *out_call_entry = NULL;
  if (out_input_info != NULL) *out_input_info = NULL;
  if (ctx == NULL || section_analysis == NULL || instruction == NULL || reg_index >= 8U) return 0;
  section = section_analysis_context_section(ctx);
  if (section == NULL) return 0;
  cursor = offset + (uint32_t)instruction->byte_count;
  while (cursor < section->data_size) {
    SectionDecodeResult decode;
    PlatformResolvedIndirectInfo info;
    const AmigaOsLibraryVectorInfo *call_entry = NULL;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    if (decode.instruction.byte_count == 0U) break;
    if (decode.is_call) {
      info = resolve_amiga_library_vector_info(ctx, section_analysis, cursor, &decode.instruction);
      if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE) {
        call_entry = resolve_amiga_library_vector_entry(ctx, section_analysis, cursor, &decode.instruction);
      } else {
        info = resolve_amiga_library_vector_info(ctx, section_analysis, cursor, &decode.instruction);
        if (info.kind == PLATFORM_RESOLVED_INDIRECT_NONE)
          info = resolve_amiga_local_wrapper_dispatch_info(ctx, section_analysis, cursor, &decode.instruction);
        if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE && info.note_symbol_name[0] != '\0')
          call_entry = amiga_os_find_library_vector_by_symbol_name(info.note_symbol_name);
      }
      if (call_entry == NULL) return 0;
      if (out_call_entry != NULL) *out_call_entry = call_entry;
      if (out_input_info != NULL) *out_input_info = find_amiga_call_input_for_reg(call_entry, reg_kind, reg_index);
      return out_input_info == NULL || *out_input_info != NULL;
    }
    if ((reg_kind == 1U && instruction_writes_data_reg_approx(&decode.instruction, reg_index)) ||
        (reg_kind == 2U && instruction_writes_address_reg_approx(&decode.instruction, reg_index))) {
      return 0;
    }
    if (instruction_stops_fallthrough(&decode.instruction)) return 0;
    cursor += (uint32_t)decode.instruction.byte_count;
  }
  return 0;
}

typedef struct AmigaStackWrapperLookupContext {
  const M68kSectionAnalysisIR *caller_section_analysis;
} AmigaStackWrapperLookupContext;

static uint16_t amiga_stack_wrapper_lookup_base_slot(void *user_ctx, const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  const AmigaStackWrapperLookupContext *lookup_ctx = (const AmigaStackWrapperLookupContext *)user_ctx;
  uint16_t base_id;
  base_id = lookup_recovered_platform_base_slot_id_cached(ctx, section_analysis, displacement);
  if (!amiga_base_id_is_none_local(base_id)) return base_id;
  if (lookup_ctx != NULL && lookup_ctx->caller_section_analysis != NULL &&
      lookup_ctx->caller_section_analysis != section_analysis) {
    return lookup_recovered_platform_base_slot_id_cached(ctx, lookup_ctx->caller_section_analysis, displacement);
  }
  return AMIGA_OS_BASE_ID_NONE;
}

static uint16_t amiga_stack_wrapper_lookup_operand_base(void *user_ctx, const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    uint8_t operand_index) {
  (void)user_ctx;
  if (ctx == NULL || section_analysis == NULL || instruction == NULL) return AMIGA_OS_BASE_ID_NONE;
  return resolve_amiga_absolute_base_operand_id_local(ctx, section_analysis, NULL, 0U, instruction, operand_index,
    offset, 1);
}

static const void *amiga_stack_wrapper_resolve_call(void *user_ctx, const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    const uint16_t addr_reg_base_ids[8]) {
  const AmigaOsLibraryVectorInfo *call_entry;
  (void)user_ctx;
  call_entry = resolve_amiga_library_vector_entry(ctx, section_analysis, offset, instruction);
  if (call_entry == NULL) {
    const M68kOperandIR *target_operand = NULL;
    if (addr_reg_base_ids != NULL && instruction_target_operand_local(instruction, &target_operand) && target_operand != NULL &&
        (target_operand->kind == M68K_ASM_OPERAND_EA || target_operand->kind == M68K_ASM_OPERAND_BF_EA) &&
        target_operand->value.ea_mode == 5U && target_operand->value.ea_reg < 8U) {
      const char *base_name = amiga_base_name_from_id_local(addr_reg_base_ids[target_operand->value.ea_reg]);
      call_entry = resolve_amiga_library_vector_entry_for_base_name(instruction, base_name);
    }
  }
  if (call_entry == NULL) {
    PlatformResolvedIndirectInfo info = resolve_amiga_indexed_library_dispatch_info(ctx, section_analysis, offset, instruction);
    if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE && info.note_symbol_name[0] != '\0')
      call_entry = amiga_os_find_library_vector_by_symbol_name(info.note_symbol_name);
  }
  return call_entry;
}

static size_t amiga_local_wrapper_signature_cache_hash(size_t target_section_index, uint32_t target_offset) {
  return ((target_section_index * 1315423911U) ^ ((size_t)target_offset >> 1U)) &
    (AMIGA_LOCAL_WRAPPER_SIGNATURE_CACHE_CAPACITY - 1U);
}

static AmigaLocalWrapperSignatureCacheEntry *amiga_local_wrapper_signature_cache_find(
    AmigaPlatformCache *cache, size_t target_section_index, uint32_t target_offset, int *out_found) {
  size_t start;
  size_t probe;
  AmigaLocalWrapperSignatureCacheEntry *fallback;
  if (out_found != NULL) *out_found = 0;
  if (cache == NULL) return NULL;
  start = amiga_local_wrapper_signature_cache_hash(target_section_index, target_offset);
  fallback = &cache->local_wrapper_signatures[start];
  for (probe = 0U; probe < 8U; ++probe) {
    AmigaLocalWrapperSignatureCacheEntry *entry =
      &cache->local_wrapper_signatures[(start + probe) & (AMIGA_LOCAL_WRAPPER_SIGNATURE_CACHE_CAPACITY - 1U)];
    if (entry->valid &&
        entry->target_section_index == target_section_index &&
        entry->target_offset == target_offset) {
      if (out_found != NULL) *out_found = 1;
      return entry;
    }
    if (!entry->valid) return entry;
  }
  return fallback;
}

static int resolve_amiga_local_wrapper_signature_uncached(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index, uint32_t target_offset,
    PlatformLocalStackWrapperSignature *out_signature) {
  size_t current_section_index;
  AmigaStackWrapperLookupContext lookup_ctx;
  if (ctx == NULL || section_analysis == NULL || out_signature == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) {
    return 0;
  }
  lookup_ctx.caller_section_analysis = section_analysis;
  current_section_index = section_analysis_context_section_index(ctx);
  if (target_section_index != current_section_index) {
    return platform_analyze_local_stack_wrapper_signature_at(ctx, target_section_index, target_offset,
      AMIGA_LOCAL_BASE_ID_APP, amiga_stack_wrapper_lookup_base_slot, amiga_stack_wrapper_lookup_operand_base,
      amiga_stack_wrapper_resolve_call, &lookup_ctx, out_signature);
  }
  return platform_analyze_local_stack_wrapper_signature(ctx, section_analysis, target_offset, AMIGA_LOCAL_BASE_ID_APP,
    amiga_stack_wrapper_lookup_base_slot, amiga_stack_wrapper_lookup_operand_base, amiga_stack_wrapper_resolve_call,
    &lookup_ctx, out_signature);
}

static int resolve_amiga_local_wrapper_signature(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index, uint32_t target_offset,
    PlatformLocalStackWrapperSignature *out_signature) {
  AmigaPlatformCache *cache;
  AmigaLocalWrapperSignatureCacheEntry *entry;
  int found = 0;
  int result;
  if (out_signature != NULL) memset(out_signature, 0, sizeof(*out_signature));
  if (ctx == NULL || section_analysis == NULL || out_signature == NULL) return 0;
  cache = amiga_platform_cache_for_ctx(ctx);
  entry = amiga_local_wrapper_signature_cache_find(cache, target_section_index, target_offset, &found);
  if (found && entry != NULL) {
    if (entry->result) *out_signature = entry->signature;
    return entry->result;
  }
  result = resolve_amiga_local_wrapper_signature_uncached(ctx, section_analysis, target_section_index,
    target_offset, out_signature);
  if (entry != NULL) {
    memset(entry, 0, sizeof(*entry));
    entry->valid = 1U;
    entry->target_section_index = target_section_index;
    entry->target_offset = target_offset;
    entry->result = result;
    if (result) entry->signature = *out_signature;
  }
  return result;
}

static void append_amiga_identifier_tail(char *buf, size_t buf_size, const char *text, int strip_lvo_prefix,
    int strip_base_suffix) {
  const char *cursor = text;
  size_t used;
  size_t len;
  if (buf == NULL || buf_size == 0U || text == NULL) return;
  if (strip_lvo_prefix && strncmp(cursor, "_LVO", 4U) == 0) cursor += 4;
  len = strlen(cursor);
  if (strip_base_suffix && len > 4U && strcmp(cursor + len - 4U, "Base") == 0) len -= 4U;
  used = strlen(buf);
  while (len != 0U && used + 1U < buf_size) {
    unsigned char ch = (unsigned char)*cursor++;
    --len;
    if (isalnum(ch) || ch == '_') {
      buf[used++] = (char)ch;
    }
  }
  buf[used] = '\0';
}

static int format_amiga_local_wrapper_label(size_t section_index, const AmigaOsLibraryVectorInfo *entry,
    char *buf, size_t buf_size) {
  const char *base_name;
  const char *symbol_name;
  int written;
  if (buf == NULL || buf_size == 0U || entry == NULL) return 0;
  base_name = amiga_os_name(M68K_PLATFORM_NAME_BASE, entry->base_id);
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, entry->lvo_symbol_id);
  if (base_name == NULL || base_name[0] == '\0' || symbol_name == NULL || symbol_name[0] == '\0') return 0;
  written = snprintf(buf, buf_size, "h%u_", (unsigned)section_index);
  if (written < 0 || (size_t)written >= buf_size) return 0;
  if (entry->base_id == AMIGA_OS_BASE_ID_SYSBASE) {
    append_amiga_identifier_tail(buf, buf_size, "Exec", 0, 0);
  } else {
    append_amiga_identifier_tail(buf, buf_size, base_name, 0, 1);
  }
  append_amiga_identifier_tail(buf, buf_size, symbol_name, 1, 0);
  return buf[0] != '\0';
}

static int amiga_wrapper_scan_sees_caller_stack_arg_push_before_call(const SectionAnalysisContext *ctx,
    uint32_t offset) {
  const M68kSection *section;
  uint32_t cursor;
  if (ctx == NULL) return 0;
  section = section_analysis_context_section(ctx);
  if (section == NULL) return 0;
  cursor = offset;
  while (cursor < section->data_size && cursor - offset < 128U) {
    SectionDecodeResult decode;
    const M68kOperandIR *push_operand = NULL;
    uint8_t pushed_data_reg;
    uint8_t address_reg;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    if (decode.instruction.byte_count == 0U) break;
    if (decode.is_call) return 0;
    if (instruction_pushes_data_reg_to_stack_local(&decode.instruction, &pushed_data_reg)) return 1;
    if (instruction_pushes_long_stack_arg_local(&decode.instruction, &push_operand) &&
        (decode.instruction.mnemonic_id == M68K_ASM_MNEMONIC_PEA ||
         !operand_address_reg_index_local(push_operand, &address_reg))) {
      return 1;
    }
    if (instruction_stops_fallthrough(&decode.instruction)) return 0;
    cursor += (uint32_t)decode.instruction.byte_count;
  }
  return 0;
}

static int amiga_has_other_same_inferred_wrapper_label(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const AmigaOsLibraryVectorInfo *entry) {
  uint32_t cursor;
  size_t block_index;
  if (ctx == NULL || section_analysis == NULL || entry == NULL) return 0;
  for (cursor = 0U; cursor < section_analysis->certain_code_size; ++cursor) {
    PlatformLocalStackWrapperSignature prior_signature;
    const AmigaOsLibraryVectorInfo *prior_entry;
    int is_block_start = 0;
    if (cursor == offset) continue;
    if (section_analysis->certain_code_start == NULL || section_analysis->certain_code_start[cursor] == 0U) continue;
    for (block_index = 0U; block_index < section_analysis->block_count; ++block_index) {
      if (section_analysis->blocks[block_index].start_offset == cursor) {
        is_block_start = 1;
        break;
      }
    }
    if (!is_block_start) continue;
    if (amiga_wrapper_scan_sees_caller_stack_arg_push_before_call(ctx, cursor)) continue;
    if (!resolve_amiga_local_wrapper_signature(ctx, section_analysis, section_analysis_context_section_index(ctx),
        cursor, &prior_signature) ||
        prior_signature.call_entry == NULL) {
      continue;
    }
    prior_entry = (const AmigaOsLibraryVectorInfo *)prior_signature.call_entry;
    if (prior_entry->base_id == entry->base_id && prior_entry->lvo_symbol_id == entry->lvo_symbol_id) return 1;
  }
  return 0;
}

int platform_amiga_resolve_inferred_label(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, char *buf, size_t buf_size) {
  PlatformLocalStackWrapperSignature signature;
  const AmigaOsLibraryVectorInfo *entry;
  size_t block_index;
  int is_block_start = 0;
  if (buf != NULL && buf_size != 0U) buf[0] = '\0';
  if (ctx == NULL || section_analysis == NULL || buf == NULL || buf_size == 0U) return 0;
  for (block_index = 0U; block_index < section_analysis->block_count; ++block_index) {
    if (section_analysis->blocks[block_index].start_offset == offset) {
      is_block_start = 1;
      break;
    }
  }
  if (!is_block_start) return 0;
  if (amiga_wrapper_scan_sees_caller_stack_arg_push_before_call(ctx, offset)) return 0;
  if (!resolve_amiga_local_wrapper_signature(ctx, section_analysis, section_analysis_context_section_index(ctx),
      offset, &signature) ||
      signature.call_entry == NULL) {
    return 0;
  }
  entry = (const AmigaOsLibraryVectorInfo *)signature.call_entry;
  if (!format_amiga_local_wrapper_label(section_analysis_context_section_index(ctx), entry, buf, buf_size)) return 0;
  if (amiga_has_other_same_inferred_wrapper_label(ctx, section_analysis, offset, entry)) {
    size_t used = strlen(buf);
    if (used + 6U < buf_size) snprintf(buf + used, buf_size - used, "_%04X", (unsigned)offset);
  }
  return 1;
}

static int resolve_amiga_stack_push_wrapper_input(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    size_t *out_operand_index, const AmigaOsCallInputInfo **out_input_info, uint16_t *out_stack_offset) {
  const M68kSection *section;
  const M68kOperandIR *push_operand = NULL;
  uint32_t cursor;
  uint16_t later_push_bytes = 0U;
  if (out_operand_index != NULL) *out_operand_index = SIZE_MAX;
  if (out_input_info != NULL) *out_input_info = NULL;
  if (out_stack_offset != NULL) *out_stack_offset = 0U;
  if (ctx == NULL || section_analysis == NULL || instruction == NULL) return 0;
  section = section_analysis_context_section(ctx);
  if (section == NULL) return 0;
  if (!instruction_pushes_long_stack_arg_local(instruction, &push_operand)) return 0;
  cursor = offset + (uint32_t)instruction->byte_count;
  while (cursor < section->data_size) {
    SectionDecodeResult decode;
    const M68kOperandIR *ignored_operand = NULL;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    if (decode.instruction.byte_count == 0U) break;
    if (decode.is_call) {
      size_t target_section_index;
      uint32_t target_offset;
      PlatformLocalStackWrapperSignature signature;
      size_t index;
      uint16_t caller_stack_offset = (uint16_t)(4U + later_push_bytes);
      uint16_t min_signature_stack_offset = UINT16_MAX;
      if (!platform_resolve_direct_target_with_fixup(ctx, &decode.instruction, cursor, &target_section_index,
          &target_offset))
        return 0;
      if (!resolve_amiga_local_wrapper_signature(ctx, section_analysis, target_section_index, target_offset, &signature) ||
          signature.call_entry == NULL) {
        return 0;
      }
      for (index = 0U; index < signature.arg_count; ++index) {
        if (signature.args[index].caller_stack_offset != 0U &&
            signature.args[index].caller_stack_offset < min_signature_stack_offset)
          min_signature_stack_offset = signature.args[index].caller_stack_offset;
      }
      for (index = 0U; index < signature.arg_count; ++index) {
        const AmigaOsCallInputInfo *input_info;
        if (signature.args[index].caller_stack_offset != caller_stack_offset) {
          if (min_signature_stack_offset == UINT16_MAX ||
              signature.args[index].caller_stack_offset < min_signature_stack_offset ||
              signature.args[index].caller_stack_offset - min_signature_stack_offset != later_push_bytes) {
            continue;
          }
        }
        input_info = find_amiga_call_input_for_reg((const AmigaOsLibraryVectorInfo *)signature.call_entry, signature.args[index].reg_kind,
          signature.args[index].reg_index);
        if (input_info == NULL) continue;
        if (out_operand_index != NULL) {
          size_t operand_index;
          *out_operand_index = SIZE_MAX;
          for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
            if (&instruction->operands[operand_index] == push_operand) {
              *out_operand_index = operand_index;
              break;
            }
          }
          if (*out_operand_index == SIZE_MAX) return 0;
        }
        if (out_input_info != NULL) *out_input_info = input_info;
        if (out_stack_offset != NULL) *out_stack_offset = caller_stack_offset;
        return 1;
      }
      return 0;
    }
    if (instruction_pushes_long_stack_arg_local(&decode.instruction, &ignored_operand)) {
      later_push_bytes = (uint16_t)(later_push_bytes + 4U);
    } else if (instruction_stops_fallthrough(&decode.instruction)) {
      return 0;
    }
    cursor += (uint32_t)decode.instruction.byte_count;
  }
  return 0;
}

static int format_amiga_value_domain_symbolic_value(const char *domain_name, int32_t value, char *buf, size_t buf_size) {
  const AmigaOsValueDomainInfo *domain;
  const AmigaOsValueDomainMemberInfo *members;
  size_t member_count;
  size_t index;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (domain_name == NULL || domain_name[0] == '\0') return 0;
  domain = amiga_os_find_value_domain(domain_name);
  if (domain == NULL) return 0;
  members = amiga_os_value_domain_members(domain, &member_count);
  if (members == NULL) return 0;
  for (index = 0U; index < member_count; ++index) {
    const char *member_name;
    if (members[index].value_known == 0U) continue;
    if (members[index].value == value) {
      member_name = amiga_value_domain_member_name(&members[index]);
      if (member_name == NULL || member_name[0] == '\0') continue;
      snprintf(buf, buf_size, "%s", member_name);
      return 1;
    }
  }
  if (value == 0 && amiga_value_domain_zero_name(domain) != NULL && amiga_value_domain_zero_name(domain)[0] != '\0') {
    snprintf(buf, buf_size, "%s", amiga_value_domain_zero_name(domain));
    return 1;
  }
  if ((domain->composition == AMIGA_OS_VALUE_DOMAIN_COMPOSITION_OR ||
       domain->composition == AMIGA_OS_VALUE_DOMAIN_COMPOSITION_BIT_OR) &&
      value >= 0) {
    uint32_t remaining = (uint32_t)value;
    int wrote = 0;
    for (;;) {
      int32_t best_value = 0;
      const char *best_name = NULL;
      for (index = 0U; index < member_count; ++index) {
        uint32_t member_value;
        if (members[index].value_known == 0U || members[index].value <= 0) continue;
        if (amiga_value_domain_member_name(&members[index]) == NULL) continue;
        member_value = (uint32_t)members[index].value;
        if ((remaining & member_value) != member_value) continue;
        if (best_name == NULL || member_value > (uint32_t)best_value) {
          best_value = members[index].value;
          best_name = amiga_value_domain_member_name(&members[index]);
        }
      }
      if (best_name == NULL) break;
      if (wrote) {
        size_t used = strlen(buf);
        if (used + 1U >= buf_size) return 0;
        buf[used++] = '|';
        buf[used] = '\0';
      }
      if (strlen(buf) + strlen(best_name) + 1U > buf_size) return 0;
      strcat_s(buf, buf_size, best_name);
      remaining &= ~(uint32_t)best_value;
      wrote = 1;
      if (remaining == 0U) return 1;
    }
  }
  return 0;
}

static void clear_local_data_const_state(uint8_t *known, int32_t *values) {
  size_t index;
  if (known == NULL || values == NULL) return;
  for (index = 0U; index < 8U; ++index) {
    known[index] = 0U;
    values[index] = 0;
  }
}

static void copy_local_data_const_state(uint8_t *dst_known, int32_t *dst_values,
    const uint8_t *src_known, const int32_t *src_values) {
  if (dst_known == NULL || dst_values == NULL || src_known == NULL || src_values == NULL) return;
  memcpy(dst_known, src_known, 8U * sizeof(*dst_known));
  memcpy(dst_values, src_values, 8U * sizeof(*dst_values));
}

static int join_local_data_const_state(uint8_t *dst_known, int32_t *dst_values,
    const uint8_t *src_known, const int32_t *src_values) {
  int changed = 0;
  uint8_t reg;
  if (dst_known == NULL || dst_values == NULL || src_known == NULL || src_values == NULL) return 0;
  for (reg = 0U; reg < 8U; ++reg) {
    if (!dst_known[reg]) continue;
    if (!src_known[reg] || dst_values[reg] != src_values[reg]) {
      dst_known[reg] = 0U;
      dst_values[reg] = 0;
      changed = 1;
    }
  }
  return changed;
}

static void update_local_data_const_state_for_instruction(const M68kInstructionIR *instruction,
    const uint8_t *prev_known, const int32_t *prev_values, uint8_t *known, int32_t *values) {
  uint8_t reg;
  uint8_t dest_reg;
  uint8_t source_reg;
  uint8_t mnemonic_id;
  const M68kOperandIR *source = NULL;
  if (prev_known == NULL || prev_values == NULL || known == NULL || values == NULL) return;
  copy_local_data_const_state(known, values, prev_known, prev_values);
  for (reg = 0U; reg < 8U; ++reg) {
    if (instruction_writes_data_reg_approx(instruction, reg)) {
      known[reg] = 0U;
      values[reg] = 0;
    }
  }
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      instruction->operand_count == 2U &&
      operand_is_immediate_source_local(&instruction->operands[0]) &&
      operand_data_reg_index_local(&instruction->operands[1], &dest_reg) &&
      dest_reg < 8U) {
    known[dest_reg] = 1U;
    values[dest_reg] = (int32_t)m68k_sign_extend32(instruction->operands[0].value.value, 8U);
    return;
  }
  if (instruction_is_data_move(instruction, &dest_reg, &source) && source != NULL && dest_reg < 8U) {
    if (operand_is_immediate_source_local(source)) {
      known[dest_reg] = 1U;
      values[dest_reg] = (int32_t)source->value.value;
    } else if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U && prev_known[source_reg]) {
      known[dest_reg] = 1U;
      values[dest_reg] = prev_values[source_reg];
    }
  } else if (mnemonic_id == M68K_ASM_MNEMONIC_CLR &&
      instruction->operand_count != 0U &&
      operand_data_reg_index_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg) &&
      dest_reg < 8U) {
    known[dest_reg] = 1U;
    values[dest_reg] = 0;
  }
}

static int summarize_amiga_direct_local_success_outputs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t target_offset,
    AmigaLocalSuccessSummaryCacheEntry *cache, size_t cache_count, AmigaCallEffectRegState *out_summary) {
  const M68kSection *section = section_analysis_context_section(ctx);
  AmigaPlatformCache *platform_cache;
  AmigaLocalSuccessSummaryWorkspace temp_workspace;
  AmigaLocalSuccessSummaryWorkspace *workspace = NULL;
  int workspace_is_temp = 0;
  size_t entry_block_index;
  AmigaCallEffectRegState *entry_states = NULL;
  uint8_t (*entry_const_known)[8] = NULL;
  int32_t (*entry_const_values)[8] = NULL;
  uint8_t *entry_known = NULL;
  size_t *pending = NULL;
  size_t pending_count = 0U;
  size_t pending_capacity = 0U;
  int have_summary = 0;
  int result = 0;
  if (out_summary != NULL) amiga_call_effect_reg_state_clear(out_summary);
  if (ctx == NULL || section_analysis == NULL || section == NULL || out_summary == NULL ||
      cache == NULL || cache_count == 0U) {
    return 0;
  }
  memset(&temp_workspace, 0, sizeof(temp_workspace));
  entry_block_index = section_analysis_find_block_index_containing(section_analysis, target_offset);
  if (entry_block_index == SIZE_MAX || entry_block_index >= section_analysis->block_count || entry_block_index >= cache_count)
    return 0;
  if (cache[entry_block_index].state == 2U) {
    amiga_call_effect_reg_state_copy(out_summary, &cache[entry_block_index].reg_state);
    return amiga_call_effect_reg_state_has_any_info(&cache[entry_block_index].reg_state);
  }
  if (cache[entry_block_index].state == 1U) return 0;
  cache[entry_block_index].state = 1U;
  platform_cache = amiga_platform_cache_for_ctx(ctx);
  if (acquire_amiga_local_success_summary_workspace(ctx, section_analysis, &temp_workspace, &workspace,
        &workspace_is_temp) != 0 || workspace == NULL) {
    goto cleanup;
  }
  entry_states = workspace->entry_states;
  entry_const_known = workspace->entry_const_known;
  entry_const_values = workspace->entry_const_values;
  entry_known = workspace->entry_known;
  pending = workspace->pending;
  pending_capacity = workspace->pending_capacity;
  if (entry_states == NULL || entry_const_known == NULL || entry_const_values == NULL ||
      entry_known == NULL || pending == NULL) {
    goto cleanup;
  }
  memset(entry_known, 0, section_analysis->block_count * sizeof(*entry_known));
  amiga_call_effect_reg_state_clear(&entry_states[entry_block_index]);
  clear_local_data_const_state(entry_const_known[entry_block_index], entry_const_values[entry_block_index]);
  entry_known[entry_block_index] = 1U;
  pending[pending_count++] = entry_block_index;
  while (pending_count != 0U) {
    size_t block_index = pending[--pending_count];
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    AmigaCallEffectRegState state;
    uint8_t const_known[8];
    int32_t const_values[8];
    uint32_t cursor = block->start_offset < target_offset ? target_offset : block->start_offset;
    size_t edge_index;
    amiga_call_effect_reg_state_copy(&state, &entry_states[block_index]);
    copy_local_data_const_state(const_known, const_values, entry_const_known[block_index], entry_const_values[block_index]);
    while (cursor < block->end_offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      AmigaCallEffectRegState prev_state;
      uint8_t prev_const_known[8];
      int32_t prev_const_values[8];
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U) break;
      amiga_call_effect_reg_state_copy(&prev_state, &state);
      copy_local_data_const_state(prev_const_known, prev_const_values, const_known, const_values);
      if (decode.is_call) {
        size_t nested_target_section_index = SIZE_MAX;
        uint32_t nested_target_offset;
        AmigaCallEffectRegState nested_summary;
        AmigaCallEffectRegState call_effect_state;
        PlatformResolvedIndirectInfo info;
        const AmigaOsLibraryVectorInfo *call_entry = NULL;
        int loaded_success_summary = 0;
        clear_all_amiga_call_effect_regs(&state);
        clear_local_data_const_state(const_known, const_values);
        amiga_call_effect_reg_state_clear(&nested_summary);
        amiga_call_effect_reg_state_clear(&call_effect_state);
        if (platform_resolve_direct_target_with_fixup(ctx, &decode.instruction, cursor, &nested_target_section_index,
              &nested_target_offset) &&
            summarize_amiga_direct_local_success_outputs_at(ctx, section_analysis, nested_target_section_index,
              nested_target_offset, cache, cache_count, &nested_summary)) {
          amiga_call_effect_reg_state_copy(&state, &nested_summary);
          const_known[0] = 1U;
          const_values[0] = 0;
          loaded_success_summary = 1;
        }
        if (!loaded_success_summary) {
          info = resolve_amiga_library_vector_info(ctx, section_analysis, cursor, &decode.instruction);
          if (info.kind == PLATFORM_RESOLVED_INDIRECT_NONE)
            info = resolve_amiga_local_wrapper_dispatch_info(ctx, section_analysis, cursor, &decode.instruction);
          if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE &&
              info.note_symbol_name[0] != '\0') {
            call_entry = amiga_os_find_library_vector_by_symbol_name(info.note_symbol_name);
          }
          if (call_entry != NULL &&
              seed_amiga_call_effect_reg_state_from_call_entry(ctx, section_analysis, cursor, call_entry,
                &call_effect_state)) {
            amiga_call_effect_reg_state_copy(&state, &call_effect_state);
          }
        }
        apply_recovered_amiga_platform_effects_to_call_state(section_analysis, cursor, &state);
      } else {
        update_amiga_call_effect_reg_state_for_instruction(ctx, section_analysis, &decode.instruction, cursor,
          &prev_state, &state);
        update_local_data_const_state_for_instruction(&decode.instruction, prev_const_known, prev_const_values,
          const_known, const_values);
      }
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    for (edge_index = block->edge_start; edge_index < block->edge_start + block->edge_count; ++edge_index) {
      const M68kCfgEdgeIR *edge = &section_analysis->edges[edge_index];
      if (edge->kind == M68K_CFG_EDGE_RETURN) {
        if (!const_known[0] || const_values[0] != 0) continue;
        if (!have_summary) {
          amiga_call_effect_reg_state_copy(out_summary, &state);
          have_summary = 1;
        } else {
          amiga_call_effect_reg_state_join(out_summary, &state);
        }
        continue;
      }
      if (edge->kind == M68K_CFG_EDGE_CALL || edge->target_block_index == SIZE_MAX ||
          edge->target_block_index >= section_analysis->block_count) {
        continue;
      }
      if (!entry_known[edge->target_block_index]) {
        amiga_call_effect_reg_state_copy(&entry_states[edge->target_block_index], &state);
        copy_local_data_const_state(entry_const_known[edge->target_block_index],
          entry_const_values[edge->target_block_index], const_known, const_values);
        entry_known[edge->target_block_index] = 1U;
        if (pending_count < pending_capacity) pending[pending_count++] = edge->target_block_index;
      } else {
        int changed = 0;
        changed |= amiga_call_effect_reg_state_join(&entry_states[edge->target_block_index], &state);
        changed |= join_local_data_const_state(entry_const_known[edge->target_block_index],
          entry_const_values[edge->target_block_index], const_known, const_values);
        if (changed && pending_count < pending_capacity) pending[pending_count++] = edge->target_block_index;
      }
    }
  }
  result = have_summary;
cleanup:
  cache[entry_block_index].state = 2U;
  if (result) {
    amiga_call_effect_reg_state_copy(&cache[entry_block_index].reg_state, out_summary);
  } else {
    amiga_call_effect_reg_state_clear(&cache[entry_block_index].reg_state);
  }
  release_amiga_local_success_summary_workspace(platform_cache, workspace, workspace_is_temp);
  return result;
}

static const M68kSectionAnalysisIR *resolve_amiga_target_section_analysis(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index) {
  if (ctx == NULL || section_analysis == NULL || target_section_index == SIZE_MAX) return NULL;
  if (target_section_index == section_analysis_context_section_index(ctx)) return section_analysis;
  return section_analysis_context_prior_section_analysis(ctx, target_section_index);
}

static int summarize_amiga_direct_local_success_outputs_at(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, size_t target_section_index, uint32_t target_offset,
    AmigaLocalSuccessSummaryCacheEntry *same_section_cache, size_t same_section_cache_count,
    AmigaCallEffectRegState *out_summary) {
  const M68kObject *object;
  const M68kSectionAnalysisIR *target_analysis;
  const M68kSection *target_section;
  size_t current_section_index;
  if (out_summary != NULL) amiga_call_effect_reg_state_clear(out_summary);
  if (ctx == NULL || section_analysis == NULL || out_summary == NULL) return 0;
  current_section_index = section_analysis_context_section_index(ctx);
  if (target_section_index == current_section_index) {
    return summarize_amiga_direct_local_success_outputs(ctx, section_analysis, target_offset,
      same_section_cache, same_section_cache_count, out_summary);
  }
  object = section_analysis_context_object(ctx);
  if (object == NULL || target_section_index >= object->section_count) return 0;
  target_analysis = section_analysis_context_prior_section_analysis(ctx, target_section_index);
  if (target_analysis == NULL || target_analysis->block_count == 0U) return 0;
  target_section = &object->sections[target_section_index];
  {
    Arena *arena = arena_create(4096U);
    SectionAnalysisContext target_ctx;
    AmigaLocalSuccessSummaryCacheEntry *target_cache;
    int result = 0;
    if (arena == NULL) return 0;
    target_cache = (AmigaLocalSuccessSummaryCacheEntry *)calloc(target_analysis->block_count, sizeof(*target_cache));
    if (target_cache != NULL &&
        section_analysis_context_init(&target_ctx, object, target_section_index, target_section,
          ctx->prior_section_analyses, ctx->prior_section_analysis_count, section_analysis_context_policy(ctx),
          arena) == 0) {
      result = summarize_amiga_direct_local_success_outputs(&target_ctx, target_analysis, target_offset,
        target_cache, target_analysis->block_count, out_summary);
    }
    free(target_cache);
    arena_destroy(arena);
    return result;
  }
}

static int load_amiga_recovered_local_success_summary_state(const M68kSectionAnalysisIR *section_analysis,
    uint32_t target_offset, AmigaCallEffectRegState *out_state) {
  size_t index;
  int found = 0;
  if (out_state != NULL) amiga_call_effect_reg_state_clear(out_state);
  if (section_analysis == NULL || out_state == NULL) return 0;
  for (index = 0U; index < section_analysis->recovered_local_call_summary_count; ++index) {
    const M68kRecoveredLocalCallSummaryIR *summary = &section_analysis->recovered_local_call_summaries[index];
    uint16_t base_id;
    if (summary->target_offset != target_offset) continue;
    if (summary->success_value_known &&
        (summary->success_reg_kind != 1U || summary->success_reg_index != 0U || summary->success_reg_value != 0)) {
      continue;
    }
    if (summary->reg_index >= 8U) continue;
    if (summary->effect_kind == M68K_PLATFORM_EFFECT_SET_BASE_REG) {
      base_id = amiga_named_base_payload_id_local(&summary->payload.named_base);
      if (amiga_base_id_is_none_local(base_id)) continue;
      if (summary->reg_kind == 1U) {
        amiga_call_effect_reg_state_set_base_id(out_state, 1U, summary->reg_index, base_id);
        found = 1;
      } else if (summary->reg_kind == 2U) {
        amiga_call_effect_reg_state_set_base_id(out_state, 2U, summary->reg_index, base_id);
        found = 1;
      }
    } else if (summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
      if (summary->reg_kind == 1U) {
        amiga_typed_payload_apply_to_value_local(&out_state->data_reg_values[summary->reg_index], &summary->payload.typed);
        found = 1;
      } else if (summary->reg_kind == 2U) {
        amiga_typed_payload_apply_to_value_local(&out_state->addr_reg_values[summary->reg_index], &summary->payload.typed);
        found = 1;
      }
    }
  }
  return found;
}

static int scan_amiga_source_section_direct_calls_to_target(const SectionAnalysisContext *ctx,
    size_t source_section_index, size_t target_section_index, int stop_after_first,
    AmigaDirectCallVisitFn visit, void *user_data, int *out_found) {
  const M68kObject *object = section_analysis_context_object(ctx);
  const M68kSection *source_section;
  const M68kSectionAnalysisIR *source_analysis;
  Arena *arena;
  SectionAnalysisContext source_ctx;
  size_t call_index;
  int have_source_ctx = 0;
  int found = 0;
  if (out_found != NULL) *out_found = 0;
  if (ctx == NULL || object == NULL || source_section_index >= object->section_count ||
      target_section_index >= object->section_count || source_section_index == target_section_index) {
    return 0;
  }
  source_section = &object->sections[source_section_index];
  source_analysis = section_analysis_context_prior_section_analysis(ctx, source_section_index);
  if (source_section == NULL || source_analysis == NULL || source_section->kind != M68K_SECTION_CODE) return 0;
  arena = NULL;
  if (source_analysis->recovered_direct_section_calls_indexed) {
    for (call_index = 0U; call_index < source_analysis->recovered_direct_section_call_count; ++call_index) {
      const M68kRecoveredDirectSectionCallIR *call = &source_analysis->recovered_direct_section_calls[call_index];
      if (call->target_section_index != target_section_index) continue;
      if (visit != NULL && !have_source_ctx) {
        arena = arena_create(4096U);
        if (arena == NULL) return -1;
        if (section_analysis_context_init(&source_ctx, object, source_section_index, source_section,
              ctx->prior_section_analyses, ctx->prior_section_analysis_count, section_analysis_context_policy(ctx),
              arena) != 0) {
          arena_destroy(arena);
          return 0;
        }
        have_source_ctx = 1;
      }
      found = 1;
      if (visit != NULL && visit(&source_ctx, source_analysis, call->offset, call->target_offset, user_data) != 0) {
        if (arena != NULL) arena_destroy(arena);
        return -1;
      }
      if (stop_after_first) break;
    }
  } else {
    size_t fixup_index;
    if (visit != NULL) {
      arena = arena_create(4096U);
      if (arena == NULL) return -1;
      if (section_analysis_context_init(&source_ctx, object, source_section_index, source_section,
            ctx->prior_section_analyses, ctx->prior_section_analysis_count, section_analysis_context_policy(ctx), arena) != 0) {
        arena_destroy(arena);
        return 0;
      }
      have_source_ctx = 1;
    }
    for (fixup_index = 0U; fixup_index < object->fixup_count; ++fixup_index) {
      const M68kFixup *fixup = &object->fixups[fixup_index];
      uint32_t low;
      uint32_t candidate;
      if (fixup->section_index != source_section_index || !fixup->has_target_section ||
          fixup->target_section_index != target_section_index || fixup->offset >= source_section->data_size) {
        continue;
      }
      low = fixup->offset > 10U ? (fixup->offset - 10U) : 0U;
      for (candidate = next_amiga_platform_fact_code_offset(source_analysis, low, source_section->data_size);
           candidate != UINT32_MAX && candidate <= fixup->offset;
           candidate = next_amiga_platform_fact_code_offset(source_analysis, candidate + 1U, source_section->data_size)) {
        SectionDecodeResult decode;
        size_t call_target_section = SIZE_MAX;
        uint32_t call_target_offset = UINT32_MAX;
        if (!have_source_ctx && visit == NULL) {
          arena = arena_create(4096U);
          if (arena == NULL) return -1;
          if (section_analysis_context_init(&source_ctx, object, source_section_index, source_section,
                ctx->prior_section_analyses, ctx->prior_section_analysis_count, section_analysis_context_policy(ctx),
                arena) != 0) {
            arena_destroy(arena);
            return 0;
          }
          have_source_ctx = 1;
        }
        if (!section_analysis_context_probe_decode(&source_ctx, candidate, &decode)) continue;
        if (!decode.is_call || decode.instruction.byte_count == 0U) continue;
        if (candidate + (uint32_t)decode.instruction.byte_count <= fixup->offset) continue;
        if (!platform_resolve_direct_target_with_fixup(&source_ctx, &decode.instruction, candidate,
              &call_target_section, &call_target_offset)) {
          continue;
        }
        if (call_target_section != target_section_index) continue;
        found = 1;
        if (visit != NULL && visit(&source_ctx, source_analysis, candidate, call_target_offset, user_data) != 0) {
          if (arena != NULL) arena_destroy(arena);
          return -1;
        }
        if (stop_after_first) {
          if (arena != NULL) arena_destroy(arena);
          if (out_found != NULL) *out_found = 1;
          return 0;
        }
        break;
      }
    }
  }
  if (arena != NULL) arena_destroy(arena);
  if (out_found != NULL) *out_found = found;
  return 0;
}

static int acquire_amiga_local_success_summary_workspace(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, AmigaLocalSuccessSummaryWorkspace *temp_workspace,
    AmigaLocalSuccessSummaryWorkspace **out_workspace, int *out_is_temp) {
  AmigaPlatformCache *cache;
  AmigaLocalSuccessSummaryWorkspace *workspace;
  Arena *arena;
  size_t block_count;
  if (out_workspace != NULL) *out_workspace = NULL;
  if (out_is_temp != NULL) *out_is_temp = 0;
  if (ctx == NULL || section_analysis == NULL || out_workspace == NULL || temp_workspace == NULL) return -1;
  block_count = section_analysis->block_count != 0U ? section_analysis->block_count : 1U;
  cache = amiga_platform_cache_for_ctx(ctx);
  arena = section_analysis_context_arena(ctx);
  if (cache == NULL || arena == NULL) return -1;
  workspace = &cache->local_success_workspace;
  if (!workspace->in_use) {
    if (workspace->entry_states == NULL || workspace->block_count < block_count ||
        workspace->section_analysis != section_analysis) {
      workspace->entry_states = (AmigaCallEffectRegState *)arena_alloc(arena,
        block_count * sizeof(*workspace->entry_states));
      workspace->entry_const_known = (uint8_t (*)[8])arena_alloc(arena,
        block_count * sizeof(*workspace->entry_const_known));
      workspace->entry_const_values = (int32_t (*)[8])arena_alloc(arena,
        block_count * sizeof(*workspace->entry_const_values));
      workspace->entry_known = (uint8_t *)arena_alloc(arena, block_count * sizeof(*workspace->entry_known));
      workspace->pending = (size_t *)arena_alloc(arena, block_count * sizeof(*workspace->pending));
      if (workspace->entry_states == NULL || workspace->entry_const_known == NULL ||
          workspace->entry_const_values == NULL || workspace->entry_known == NULL || workspace->pending == NULL) {
        return -1;
      }
      workspace->block_count = block_count;
      workspace->pending_capacity = block_count;
    }
    workspace->section_analysis = section_analysis;
    workspace->in_use = 1U;
    *out_workspace = workspace;
    return 0;
  }
  memset(temp_workspace, 0, sizeof(*temp_workspace));
  temp_workspace->entry_states = (AmigaCallEffectRegState *)malloc(block_count * sizeof(*temp_workspace->entry_states));
  temp_workspace->entry_const_known = (uint8_t (*)[8])malloc(block_count * sizeof(*temp_workspace->entry_const_known));
  temp_workspace->entry_const_values = (int32_t (*)[8])malloc(block_count * sizeof(*temp_workspace->entry_const_values));
  temp_workspace->entry_known = (uint8_t *)malloc(block_count * sizeof(*temp_workspace->entry_known));
  temp_workspace->pending = (size_t *)malloc(block_count * sizeof(*temp_workspace->pending));
  if (temp_workspace->entry_states == NULL || temp_workspace->entry_const_known == NULL ||
      temp_workspace->entry_const_values == NULL || temp_workspace->entry_known == NULL ||
      temp_workspace->pending == NULL) {
    free(temp_workspace->entry_states);
    free(temp_workspace->entry_const_known);
    free(temp_workspace->entry_const_values);
    free(temp_workspace->entry_known);
    free(temp_workspace->pending);
    memset(temp_workspace, 0, sizeof(*temp_workspace));
    return -1;
  }
  temp_workspace->section_analysis = section_analysis;
  temp_workspace->block_count = block_count;
  temp_workspace->pending_capacity = block_count;
  *out_workspace = temp_workspace;
  if (out_is_temp != NULL) *out_is_temp = 1;
  return 0;
}

static void release_amiga_local_success_summary_workspace(AmigaPlatformCache *cache,
    AmigaLocalSuccessSummaryWorkspace *workspace, int is_temp) {
  if (workspace == NULL) return;
  if (is_temp) {
    free(workspace->entry_states);
    free(workspace->entry_const_known);
    free(workspace->entry_const_values);
    free(workspace->entry_known);
    free(workspace->pending);
    memset(workspace, 0, sizeof(*workspace));
    return;
  }
  if (cache != NULL && workspace == &cache->local_success_workspace) {
    cache->local_success_workspace.in_use = 0U;
  }
}

static int resolve_amiga_data_reg_info_from_success_local_calls(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, AmigaResolvedDataRegInfo *out_info) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t start;
  uint32_t cursor;
  AmigaCallEffectRegState state;
  if (out_info != NULL) init_amiga_value_provenance(out_info);
  if (ctx == NULL || section == NULL || section_analysis == NULL || reg >= 8U || out_info == NULL) return 0;
  amiga_call_effect_reg_state_clear(&state);
  start = resolve_analysis_trace_start(ctx, section_analysis, offset);
  if (start == UINT32_MAX || start > offset) return 0;
  {
    uint32_t fallback_start = find_amiga_typed_trace_fallback_start(ctx, offset);
    if (fallback_start != UINT32_MAX && fallback_start < start) start = fallback_start;
  }
  for (cursor = start; cursor < offset && cursor < section->data_size; ) {
    SectionDecodeResult decode;
    AmigaCallEffectRegState prev_state;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
    amiga_call_effect_reg_state_copy(&prev_state, &state);
    if (decode.is_call) {
      size_t target_section_index = SIZE_MAX;
      uint32_t target_offset;
      AmigaCallEffectRegState call_effect_state;
      const M68kSectionAnalysisIR *target_analysis;
      PlatformResolvedIndirectInfo info;
      const AmigaOsLibraryVectorInfo *call_entry = NULL;
      int loaded_success_summary = 0;
      clear_all_amiga_call_effect_regs(&state);
      amiga_call_effect_reg_state_clear(&call_effect_state);
      if (platform_resolve_direct_target_with_fixup(ctx, &decode.instruction, cursor, &target_section_index,
          &target_offset)) {
        target_analysis = resolve_amiga_target_section_analysis(ctx, section_analysis, target_section_index);
        loaded_success_summary = load_amiga_recovered_local_success_summary_state(target_analysis, target_offset, &state);
        if (!loaded_success_summary) {
          loaded_success_summary = summarize_amiga_direct_local_success_outputs_at(ctx, section_analysis,
            target_section_index, target_offset, NULL, 0U, &state);
        }
      }
      if (!loaded_success_summary) {
        info = resolve_amiga_library_vector_info(ctx, section_analysis, cursor, &decode.instruction);
        if (info.kind == PLATFORM_RESOLVED_INDIRECT_NONE)
          info = resolve_amiga_local_wrapper_dispatch_info(ctx, section_analysis, cursor, &decode.instruction);
        if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE &&
            info.note_symbol_name[0] != '\0') {
          call_entry = amiga_os_find_library_vector_by_symbol_name(info.note_symbol_name);
        }
        if (call_entry != NULL &&
            seed_amiga_call_effect_reg_state_from_call_entry(ctx, section_analysis, cursor, call_entry,
              &call_effect_state)) {
          amiga_call_effect_reg_state_copy(&state, &call_effect_state);
        }
      }
      apply_recovered_amiga_platform_effects_to_call_state(section_analysis, cursor, &state);
    } else {
      update_amiga_call_effect_reg_state_for_instruction(ctx, section_analysis, &decode.instruction, cursor,
        &prev_state, &state);
    }
    cursor += (uint32_t)decode.instruction.byte_count;
  }
  if (amiga_value_provenance_type_name_local(&state.data_reg_values[reg]) == NULL) return 0;
  *out_info = state.data_reg_values[reg];
  out_info->slot_disp = INT16_MIN;
  out_info->field_disp = INT16_MIN;
  if (amiga_value_provenance_owner_type_name_local(out_info) == NULL) {
    amiga_value_provenance_copy_owner_from_type(out_info, out_info);
  }
  return 1;
}

static int resolve_preceding_success_local_call_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, AmigaResolvedDataRegInfo *out_info) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  if (out_info != NULL) init_amiga_value_provenance(out_info);
  if (ctx == NULL || section == NULL || section_analysis == NULL || reg >= 8U || out_info == NULL) return 0;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    uint32_t prev_offset = UINT32_MAX;
    SectionDecodeResult prev_decode = {0};
    int have_prev = 0;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      prev_offset = cursor;
      prev_decode = decode;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (!have_prev || cursor != offset || prev_offset == UINT32_MAX || !prev_decode.is_call) continue;
    {
      size_t target_section_index = SIZE_MAX;
      uint32_t target_offset;
      AmigaCallEffectRegState summary;
      const M68kSectionAnalysisIR *target_analysis;
      if (!platform_resolve_direct_target_with_fixup(ctx, &prev_decode.instruction, prev_offset, &target_section_index,
          &target_offset)) continue;
      amiga_call_effect_reg_state_clear(&summary);
      target_analysis = resolve_amiga_target_section_analysis(ctx, section_analysis, target_section_index);
      if (!load_amiga_recovered_local_success_summary_state(target_analysis, target_offset, &summary) &&
          !summarize_amiga_direct_local_success_outputs_at(ctx, section_analysis, target_section_index,
            target_offset, NULL, 0U, &summary)) continue;
      if (amiga_value_provenance_type_name_local(&summary.data_reg_values[reg]) == NULL) continue;
      *out_info = summary.data_reg_values[reg];
      out_info->slot_disp = INT16_MIN;
      out_info->field_disp = INT16_MIN;
      if (amiga_value_provenance_owner_type_name_local(out_info) == NULL) {
        amiga_value_provenance_copy_owner_from_type(out_info, out_info);
      }
      amiga_value_provenance_set_field_symbol_name(out_info, NULL);
      return 1;
    }
  }
  return 0;
}

static int resolve_amiga_data_reg_info_from_success_local_calls_uncached(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, AmigaResolvedDataRegInfo *out_info) {
  if (out_info != NULL) init_amiga_value_provenance(out_info);
  if (ctx == NULL || section_analysis == NULL || out_info == NULL) return 0;
  return resolve_preceding_success_local_call_data_reg_info(ctx, section_analysis, offset, reg, out_info) ||
    resolve_amiga_data_reg_info_from_success_local_calls(ctx, section_analysis, offset, reg, out_info);
}

static const char *resolve_amiga_register_base_name_raw(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t target_reg_kind, uint8_t reg,
    int include_section_slots) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint16_t addr_reg_base_ids[8];
  uint16_t addr_reg_seed_base_ids[8];
  uint16_t data_reg_base_ids[8];
  AmigaBaseSlotTag slot_base_names[AMIGA_BASE_SLOT_TAG_CAPACITY];
  AmigaAbsoluteBaseSlotTag absolute_base_slots[AMIGA_BASE_SLOT_TAG_CAPACITY];
  AmigaTypedSlotTag slot_type_names[AMIGA_BASE_SLOT_TAG_CAPACITY];
  uint16_t saved_stack_base_ids[8];
  size_t saved_stack_base_count = 0U;
  size_t slot_base_count = sizeof(slot_base_names) / sizeof(slot_base_names[0]);
  uint32_t cursor;
  if (section == NULL || section_analysis == NULL || reg >= 8U) return NULL;
  init_amiga_base_id_array(addr_reg_base_ids, sizeof(addr_reg_base_ids) / sizeof(addr_reg_base_ids[0]));
  init_amiga_base_id_array(addr_reg_seed_base_ids, sizeof(addr_reg_seed_base_ids) / sizeof(addr_reg_seed_base_ids[0]));
  init_amiga_base_id_array(data_reg_base_ids, sizeof(data_reg_base_ids) / sizeof(data_reg_base_ids[0]));
  init_amiga_base_id_array(saved_stack_base_ids, sizeof(saved_stack_base_ids) / sizeof(saved_stack_base_ids[0]));
  init_amiga_base_slot_tag_array(slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]));
  init_amiga_absolute_base_slot_tag_array(absolute_base_slots, sizeof(absolute_base_slots) / sizeof(absolute_base_slots[0]));
  addr_reg_base_ids[6] = AMIGA_LOCAL_BASE_ID_APP;
  init_amiga_typed_slot_tag_array(slot_type_names, sizeof(slot_type_names) / sizeof(slot_type_names[0]));
  if (include_section_slots) {
    size_t index;
    seed_amiga_base_slot_tags_from_effects(section_analysis, slot_base_names,
      sizeof(slot_base_names) / sizeof(slot_base_names[0]));
    for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
      const M68kRecoveredPlatformBaseSlotIR *slot = &section_analysis->recovered_platform_base_slots[index];
      set_amiga_base_slot_id_local(slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]),
        slot->displacement,
        !amiga_base_id_is_none_local(slot->base_ref.id) ? slot->base_ref.id : amiga_base_id_from_name_local(slot->base_name));
    }
  }
  cursor = resolve_analysis_trace_start(ctx, section_analysis, offset);
  if (cursor == UINT32_MAX || cursor > offset) return NULL;
  seed_amiga_absolute_base_slots_before_offset(ctx, section_analysis, cursor, absolute_base_slots,
    sizeof(absolute_base_slots) / sizeof(absolute_base_slots[0]));
  seed_amiga_base_regs_from_policy(ctx, cursor, addr_reg_base_ids, addr_reg_seed_base_ids, data_reg_base_ids);
  seed_amiga_effect_state_from_preceding_fallthrough(ctx, section_analysis, cursor,
    data_reg_base_ids, addr_reg_base_ids, NULL, NULL,
    slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]),
    slot_type_names, sizeof(slot_type_names) / sizeof(slot_type_names[0]));
  while (cursor < offset && cursor < section->data_size) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    uint8_t mnemonic_id;
    const M68kSimFormMetadata *metadata;
    uint16_t prev_addr_reg_base_ids[8];
    uint16_t prev_addr_reg_seed_base_ids[8];
    uint16_t prev_data_reg_base_ids[8];
    uint8_t written_reg;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    mnemonic_id = instruction.mnemonic_id;
    metadata = instruction_sim_metadata(&instruction);
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > offset) break;
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      prev_addr_reg_base_ids[written_reg] = addr_reg_base_ids[written_reg];
      prev_addr_reg_seed_base_ids[written_reg] = addr_reg_seed_base_ids[written_reg];
      prev_data_reg_base_ids[written_reg] = data_reg_base_ids[written_reg];
    }
    {
      PlatformAddressExgInfo exg = instruction_address_exg(&instruction);
      if (exg.ok) {
        uint16_t tmp = addr_reg_base_ids[exg.left_reg];
        uint16_t tmp_seed = addr_reg_seed_base_ids[exg.left_reg];
        addr_reg_base_ids[exg.left_reg] = addr_reg_base_ids[exg.right_reg];
        addr_reg_base_ids[exg.right_reg] = tmp;
        addr_reg_seed_base_ids[exg.left_reg] = addr_reg_seed_base_ids[exg.right_reg];
        addr_reg_seed_base_ids[exg.right_reg] = tmp_seed;
        cursor += (uint32_t)instruction.byte_count;
        continue;
      }
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_address_reg_approx(&instruction, written_reg)) {
        addr_reg_base_ids[written_reg] = AMIGA_OS_BASE_ID_NONE;
        addr_reg_seed_base_ids[written_reg] = AMIGA_OS_BASE_ID_NONE;
      }
    }
    {
      uint8_t dest_reg;
      const M68kOperandIR *source = NULL;
      uint32_t source_target;
      if (instruction_is_data_move(&instruction, &dest_reg, &source)) {
        if (source != NULL && source->kind == M68K_ASM_OPERAND_DN && source->value.reg < 8U) {
          data_reg_base_ids[dest_reg] = prev_data_reg_base_ids[source->value.reg];
        } else if (source != NULL && source->kind == M68K_ASM_OPERAND_AN && source->value.reg < 8U) {
          data_reg_base_ids[dest_reg] = prev_addr_reg_base_ids[source->value.reg];
        } else if (!amiga_base_id_is_none_local((data_reg_base_ids[dest_reg] =
            resolve_amiga_absolute_base_operand_id_local(ctx, section_analysis, absolute_base_slots,
              sizeof(absolute_base_slots) / sizeof(absolute_base_slots[0]), &instruction, 0U, cursor, 1)))) {
        } else if (metadata != NULL &&
            instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
              (uint32_t)section->data_size, &source_target)) {
          uint16_t absolute_base_id = lookup_amiga_absolute_base_slot_id_local(absolute_base_slots,
            sizeof(absolute_base_slots) / sizeof(absolute_base_slots[0]), section_analysis_context_section_index(ctx),
            source_target);
          data_reg_base_ids[dest_reg] = !amiga_base_id_is_none_local(absolute_base_id) ? absolute_base_id :
            amiga_base_id_from_name_local(read_amiga_library_seed_name_near(section, source_target));
        } else {
          data_reg_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        }
      }
    }
    {
      uint8_t dest_reg;
      const M68kOperandIR *source = NULL;
      uint8_t source_reg;
      int16_t slot_disp;
      uint32_t source_target;
      uint16_t slot_base_id;
      if (instruction_is_address_move(&instruction, &dest_reg, &source)) {
        PlatformRegisterMatch popped = instruction_pop_address_reg_from_stack(&instruction);
        if (operand_is_absolute_value(source, 4U)) {
          addr_reg_base_ids[dest_reg] = AMIGA_OS_BASE_ID_SYSBASE;
          addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        } else if (popped.ok && popped.reg == 6U) {
          if (saved_stack_base_count != 0U) {
            addr_reg_base_ids[popped.reg] = saved_stack_base_ids[--saved_stack_base_count];
            addr_reg_seed_base_ids[popped.reg] = AMIGA_OS_BASE_ID_NONE;
          } else {
            addr_reg_base_ids[popped.reg] = amiga_base_id_from_name_local(resolve_preceding_stack_reloaded_base_name(
              ctx, section_analysis, cursor, popped.reg));
            addr_reg_seed_base_ids[popped.reg] = AMIGA_OS_BASE_ID_NONE;
          }
        } else if (source != NULL && source->kind == M68K_ASM_OPERAND_AN && source->value.reg < 8U) {
          addr_reg_base_ids[dest_reg] = prev_addr_reg_base_ids[source->value.reg];
          addr_reg_seed_base_ids[dest_reg] = prev_addr_reg_seed_base_ids[source->value.reg];
        } else if (source != NULL && operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
          addr_reg_base_ids[dest_reg] = prev_data_reg_base_ids[source_reg];
          addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        } else if (!amiga_base_id_is_none_local((slot_base_id = lookup_amiga_app_slot_base_id_for_operand(
            section_analysis, slot_base_names, slot_base_count, source, prev_addr_reg_base_ids[6], &slot_disp)))) {
          addr_reg_base_ids[dest_reg] = slot_base_id;
          addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        } else if (amiga_base_id_is_app_local(prev_addr_reg_base_ids[6]) &&
            operand_is_app_base_disp_ea(source, 6U, &slot_disp) &&
            !amiga_base_id_is_none_local((slot_base_id = resolve_amiga_app_slot_base_id(ctx, section_analysis, slot_disp)))) {
          addr_reg_base_ids[dest_reg] = slot_base_id;
          addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        } else if (!amiga_base_id_is_none_local((addr_reg_base_ids[dest_reg] =
            resolve_amiga_absolute_base_operand_id_local(ctx, section_analysis, absolute_base_slots,
              sizeof(absolute_base_slots) / sizeof(absolute_base_slots[0]), &instruction, 0U, cursor, 1)))) {
          addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        } else if (metadata != NULL &&
            instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
              (uint32_t)section->data_size, &source_target)) {
          uint16_t absolute_base_id = lookup_amiga_absolute_base_slot_id_local(absolute_base_slots,
            sizeof(absolute_base_slots) / sizeof(absolute_base_slots[0]), section_analysis_context_section_index(ctx),
            source_target);
          addr_reg_base_ids[dest_reg] = absolute_base_id;
          addr_reg_seed_base_ids[dest_reg] = amiga_base_id_is_none_local(absolute_base_id)
            ? amiga_base_id_from_name_local(read_amiga_library_seed_name_near(section, source_target))
            : AMIGA_OS_BASE_ID_NONE;
        } else {
          addr_reg_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
          addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        }
      } else if (mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
          instruction.operand_count == 2U &&
          operand_address_reg_index_local(&instruction.operands[1], &dest_reg)) {
        source = &instruction.operands[0];
        if (!amiga_base_id_is_none_local((slot_base_id = lookup_amiga_app_slot_base_id_for_operand(
            section_analysis, slot_base_names, slot_base_count, source, prev_addr_reg_base_ids[6], &slot_disp)))) {
          addr_reg_base_ids[dest_reg] = slot_base_id;
          addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        } else if (amiga_base_id_is_app_local(prev_addr_reg_base_ids[6]) &&
            operand_is_app_base_disp_ea(source, 6U, &slot_disp) &&
            !amiga_base_id_is_none_local((slot_base_id = resolve_amiga_app_slot_base_id(ctx, section_analysis, slot_disp)))) {
          addr_reg_base_ids[dest_reg] = slot_base_id;
          addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        } else if (metadata != NULL &&
            instruction_render_operand_target(&instruction, metadata, metadata->source_operand_index, cursor,
              (uint32_t)section->data_size, &source_target)) {
          uint16_t absolute_base_id = lookup_amiga_absolute_base_slot_id_local(absolute_base_slots,
            sizeof(absolute_base_slots) / sizeof(absolute_base_slots[0]), section_analysis_context_section_index(ctx),
            source_target);
          addr_reg_base_ids[dest_reg] = absolute_base_id;
          addr_reg_seed_base_ids[dest_reg] = amiga_base_id_is_none_local(absolute_base_id)
            ? amiga_base_id_from_name_local(read_amiga_library_seed_name_near(section, source_target))
            : AMIGA_OS_BASE_ID_NONE;
        } else {
          addr_reg_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
          addr_reg_seed_base_ids[dest_reg] = AMIGA_OS_BASE_ID_NONE;
        }
      }
    }
    if (mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction.operand_count == 1U &&
        instruction.operands[0].kind == M68K_ASM_OPERAND_EA &&
        instruction.operands[0].value.ea_mode == 2U && instruction.operands[0].value.ea_reg == 6U &&
        saved_stack_base_count < (sizeof(saved_stack_base_ids) / sizeof(saved_stack_base_ids[0]))) {
      saved_stack_base_ids[saved_stack_base_count++] = prev_addr_reg_base_ids[6];
    }
    {
      PlatformRegisterMatch pushed = instruction_push_address_reg_to_stack(&instruction);
      if (pushed.ok && pushed.reg < 8U &&
          saved_stack_base_count < (sizeof(saved_stack_base_ids) / sizeof(saved_stack_base_ids[0]))) {
        saved_stack_base_ids[saved_stack_base_count++] = prev_addr_reg_base_ids[pushed.reg];
      }
    }
    if (decode.is_call) {
      size_t target_section_index = SIZE_MAX;
      uint32_t target_offset;
      AmigaCallEffectRegState summary_state;
      const M68kSectionAnalysisIR *target_analysis;
      amiga_call_effect_reg_state_clear(&summary_state);
      if (platform_resolve_direct_target_with_fixup(ctx, &instruction, cursor, &target_section_index, &target_offset) &&
          ((target_analysis = resolve_amiga_target_section_analysis(ctx, section_analysis, target_section_index)) != NULL) &&
          (load_amiga_recovered_local_success_summary_state(target_analysis, target_offset, &summary_state) ||
           summarize_amiga_direct_local_success_outputs_at(ctx, section_analysis, target_section_index,
             target_offset, NULL, 0U, &summary_state))) {
        for (written_reg = 0U; written_reg < 8U; ++written_reg) {
          if (!amiga_base_id_is_none_local(summary_state.data_reg_base_ids[written_reg])) {
            data_reg_base_ids[written_reg] = summary_state.data_reg_base_ids[written_reg];
          }
          if (!amiga_base_id_is_none_local(summary_state.addr_reg_base_ids[written_reg])) {
            addr_reg_base_ids[written_reg] = summary_state.addr_reg_base_ids[written_reg];
            addr_reg_seed_base_ids[written_reg] = AMIGA_OS_BASE_ID_NONE;
          }
        }
      }
    }
    {
      uint8_t reg_kind;
      uint8_t reg_index;
      int16_t slot_disp;
      if ((instruction_is_register_to_app_slot_store(&instruction, &reg_kind, &reg_index, &slot_disp) &&
            amiga_base_id_is_app_local(addr_reg_base_ids[6])) ||
          instruction_is_register_to_resolved_app_slot_store(ctx, section_analysis, cursor, &instruction, &reg_kind,
            &reg_index, &slot_disp)) {
        uint16_t stored_base_id = AMIGA_OS_BASE_ID_NONE;
        if (reg_kind == 1U && reg_index < 8U) stored_base_id = prev_data_reg_base_ids[reg_index];
        else if (reg_kind == 2U && reg_index < 8U) stored_base_id = prev_addr_reg_base_ids[reg_index];
        if (!amiga_base_id_is_none_local(stored_base_id) && !amiga_base_id_is_app_local(stored_base_id))
          set_amiga_base_slot_id_local(slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]), slot_disp,
            stored_base_id);
      }
    }
    if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction.operand_count == 2U &&
        instruction.size_suffix == 'l') {
      const M68kOperandIR *src = &instruction.operands[0];
      const M68kOperandIR *dst = &instruction.operands[1];
      uint32_t target_offset = UINT32_MAX;
      uint16_t stored_base_id = AMIGA_OS_BASE_ID_NONE;
      uint8_t source_reg;
      int16_t slot_disp;
      uint16_t source_slot_base_id;
      if ((dst->kind == M68K_ASM_OPERAND_EA || dst->kind == M68K_ASM_OPERAND_BF_EA) &&
          dst->value.ea_mode == 7U && (dst->value.ea_reg == 0U || dst->value.ea_reg == 1U) &&
          dst->value.value < section->data_size) {
        target_offset = dst->value.value;
      }
      if (target_offset != UINT32_MAX) {
        if (operand_data_reg_index_local(src, &source_reg) && source_reg < 8U) {
          stored_base_id = prev_data_reg_base_ids[source_reg];
        } else if (operand_address_reg_index_local(src, &source_reg) && source_reg < 8U) {
          stored_base_id = prev_addr_reg_base_ids[source_reg];
        } else if (!amiga_base_id_is_none_local((source_slot_base_id = lookup_amiga_app_slot_base_id_for_operand(
            section_analysis, slot_base_names, slot_base_count, src, prev_addr_reg_base_ids[6], &slot_disp)))) {
          stored_base_id = source_slot_base_id;
        } else {
          stored_base_id = resolve_amiga_absolute_base_operand_id_local(ctx, section_analysis, absolute_base_slots,
            sizeof(absolute_base_slots) / sizeof(absolute_base_slots[0]), &instruction, 0U, cursor, 0);
        }
        set_amiga_absolute_base_slot_id_local(absolute_base_slots,
          sizeof(absolute_base_slots) / sizeof(absolute_base_slots[0]), section_analysis_context_section_index(ctx),
          dst->value.value, stored_base_id);
      }
    }
    {
      uint8_t reg_kind;
      uint8_t reg_index;
      int16_t slot_disp;
      if (instruction_is_app_slot_load(&instruction, &reg_kind, &reg_index, &slot_disp)) {
        uint16_t loaded_base_id = lookup_amiga_app_slot_base_id_for_operand(section_analysis, slot_base_names,
          sizeof(slot_base_names) / sizeof(slot_base_names[0]), &instruction.operands[0], addr_reg_base_ids[6],
          &slot_disp);
        if (!amiga_base_id_is_none_local(loaded_base_id)) {
          if (reg_kind == 1U && reg_index < 8U) data_reg_base_ids[reg_index] = loaded_base_id;
          else if (reg_kind == 2U && reg_index < 8U) {
            addr_reg_base_ids[reg_index] = loaded_base_id;
            addr_reg_seed_base_ids[reg_index] = AMIGA_OS_BASE_ID_NONE;
          }
        }
      }
    }
    apply_recovered_amiga_platform_effects(section_analysis, cursor, data_reg_base_ids, addr_reg_base_ids,
      NULL, NULL, slot_base_names, sizeof(slot_base_names) / sizeof(slot_base_names[0]),
      slot_type_names, sizeof(slot_type_names) / sizeof(slot_type_names[0]));
    cursor += (uint32_t)instruction.byte_count;
  }
  if (target_reg_kind == 1U) return amiga_base_name_from_id_local(data_reg_base_ids[reg]);
  return amiga_base_name_from_id_local(addr_reg_base_ids[reg]);
}

static const char *resolve_amiga_library_base_name_raw(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots) {
  return resolve_amiga_register_base_name_raw(ctx, section_analysis, offset, 2U, reg, include_section_slots);
}

static const char *resolve_preceding_stack_reloaded_base_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  if (ctx == NULL || section == NULL || section_analysis == NULL || reg >= 8U) return NULL;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    uint32_t prev_offset = UINT32_MAX;
    uint32_t second_prev_offset = UINT32_MAX;
    SectionDecodeResult prev_decode = {0};
    SectionDecodeResult second_prev_decode = {0};
    int have_prev = 0;
    int have_second_prev = 0;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      second_prev_offset = prev_offset;
      second_prev_decode = prev_decode;
      have_second_prev = have_prev;
      prev_offset = cursor;
      prev_decode = decode;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (!have_prev || !have_second_prev || cursor != offset) continue;
    {
      PlatformRegisterMatch popped;
      PlatformRegisterMatch pushed;
      uint8_t source_reg_kind, source_reg_index;
      uint16_t push_movem_mask, pop_movem_mask;
      if (instruction_pops_movem_from_stack_local(&prev_decode.instruction, &pop_movem_mask) &&
          instruction_pushes_movem_to_stack_local(&second_prev_decode.instruction, &push_movem_mask) &&
          resolve_movem_stack_pair_source_local(push_movem_mask, pop_movem_mask, 2U, reg, &source_reg_kind,
            &source_reg_index) &&
          source_reg_kind == 2U) {
        if (source_reg_index == 6U) return AMIGA_APP_BASE_TAG;
        return resolve_amiga_library_base_name_raw(ctx, section_analysis, second_prev_offset, source_reg_index, 1);
      }
      popped = instruction_pop_address_reg_from_stack(&prev_decode.instruction);
      if (!popped.ok || popped.reg != reg) continue;
      pushed = instruction_push_address_reg_to_stack(&second_prev_decode.instruction);
      if (!pushed.ok) continue;
      if (pushed.reg == 6U) return AMIGA_APP_BASE_TAG;
      return resolve_amiga_library_base_name_raw(ctx, section_analysis, second_prev_offset, pushed.reg, 1);
    }
  }
  return NULL;
}

static void init_amiga_value_provenance(AmigaValueProvenance *value) {
  if (value == NULL) return;
  value->type_id = AMIGA_OS_TYPE_ID_NONE;
  value->struct_id = AMIGA_OS_STRUCT_ID_NONE;
  value->owner_type_id = AMIGA_OS_TYPE_ID_NONE;
  value->owner_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  value->symbol_id = AMIGA_OS_SYMBOL_ID_NONE;
  value->context_base_id = AMIGA_OS_BASE_ID_NONE;
  value->semantic_kind_id = AMIGA_OS_SEMANTIC_KIND_ID_NONE;
  value->value_domain_id = AMIGA_OS_VALUE_DOMAIN_ID_NONE;
  value->has_constant_value = 0U;
  value->constant_value = 0;
  value->source_offset = UINT32_MAX;
  value->source_reg_kind = 0U;
  value->source_reg_index = 0U;
  value->slot_disp = INT16_MIN;
  value->field_disp = INT16_MIN;
  value->field_symbol_id = AMIGA_OS_SYMBOL_ID_NONE;
}

static void init_amiga_base_slot_tag_array(AmigaBaseSlotTag *slots, size_t slot_count) {
  size_t index;
  if (slots == NULL) return;
  for (index = 0U; index < slot_count; ++index) {
    slots[index].displacement = INT16_MIN;
    slots[index].base_id = AMIGA_OS_BASE_ID_NONE;
  }
}

static void init_amiga_base_id_array(uint16_t *ids, size_t count) {
  size_t index;
  if (ids == NULL) return;
  for (index = 0U; index < count; ++index) ids[index] = AMIGA_OS_BASE_ID_NONE;
}

static void init_amiga_typed_slot_tag_array(AmigaTypedSlotTag *slots, size_t slot_count) {
  size_t index;
  if (slots == NULL) return;
  for (index = 0U; index < slot_count; ++index) {
    slots[index].displacement = INT16_MIN;
    init_amiga_value_provenance(&slots[index].value);
  }
}

static int amiga_value_provenance_has_any_info(const AmigaValueProvenance *value) {
  if (value == NULL) return 0;
  return amiga_os_name(M68K_PLATFORM_NAME_TYPE, value->type_id) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_STRUCT, value->struct_id) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_TYPE, value->owner_type_id) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_STRUCT, value->owner_struct_id) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, value->symbol_id) != NULL ||
    !amiga_base_id_is_none_local(value->context_base_id) ||
    amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, value->semantic_kind_id) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, value->value_domain_id) != NULL ||
    value->has_constant_value ||
    value->slot_disp != INT16_MIN ||
    value->field_disp != INT16_MIN ||
    amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, value->field_symbol_id) != NULL;
}

static int amiga_call_effect_reg_state_has_any_info(const AmigaCallEffectRegState *state) {
  uint8_t reg_index;
  if (state == NULL) return 0;
  for (reg_index = 0U; reg_index < 8U; ++reg_index) {
    if (!amiga_base_id_is_none_local(state->data_reg_base_ids[reg_index]) ||
        !amiga_base_id_is_none_local(state->addr_reg_base_ids[reg_index]) ||
        amiga_value_provenance_has_any_info(&state->data_reg_values[reg_index]) ||
        amiga_value_provenance_has_any_info(&state->addr_reg_values[reg_index])) {
      return 1;
    }
  }
  return 0;
}

static void init_amiga_typed_trace_state(AmigaTypedTraceState *state, const M68kSectionAnalysisIR *section_analysis,
    int include_section_slots) {
  size_t index;
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
  for (index = 0U; index < 8U; ++index) {
    init_amiga_value_provenance(&state->addr_reg_values[index]);
    init_amiga_value_provenance(&state->data_reg_values[index]);
    state->local_base_ids[index] = 0U;
  }
  for (index = 0U; index < (sizeof(state->saved_stack) / sizeof(state->saved_stack[0])); ++index)
    init_amiga_typed_stack_entry(&state->saved_stack[index]);
  for (index = 0U; index < (sizeof(state->local_slots) / sizeof(state->local_slots[0])); ++index)
    clear_amiga_typed_local_slot_entry(&state->local_slots[index]);
  state->saved_stack_count = 0U;
  state->next_local_base_id = 1U;
  init_amiga_typed_slot_tag_array(state->slot_type_names, sizeof(state->slot_type_names) / sizeof(state->slot_type_names[0]));
  init_amiga_absolute_typed_slot_tag_array(state->absolute_typed_slots,
    sizeof(state->absolute_typed_slots) / sizeof(state->absolute_typed_slots[0]));
  if (include_section_slots) {
    seed_amiga_typed_slot_tags_from_effects(section_analysis, state->slot_type_names,
      sizeof(state->slot_type_names) / sizeof(state->slot_type_names[0]));
  }
}

static AmigaPlatformCache *amiga_platform_cache_for_ctx(const SectionAnalysisContext *ctx) {
  Arena *arena;
  AmigaPlatformCache *cache = (AmigaPlatformCache *)section_analysis_context_platform_cache(ctx);
  if (cache != NULL) return cache;
  arena = section_analysis_context_arena(ctx);
  if (arena == NULL) return NULL;
  cache = (AmigaPlatformCache *)arena_calloc(arena, 1U, sizeof(*cache));
  if (cache == NULL) return NULL;
  section_analysis_context_set_platform_cache(ctx, cache);
  return cache;
}

static AmigaTypedTraceCache *amiga_typed_trace_cache_find(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int include_section_slots, uint32_t origin,
    uint32_t target_offset, int *out_found) {
  AmigaPlatformCache *cache = amiga_platform_cache_for_ctx(ctx);
  AmigaTypedTraceCache *empty = NULL;
  AmigaTypedTraceCache *best = NULL;
  size_t index;
  if (out_found != NULL) *out_found = 0;
  if (cache == NULL) return NULL;
  for (index = 0U; index < AMIGA_TYPED_TRACE_CACHE_CAPACITY; ++index) {
    AmigaTypedTraceCache *entry = &cache->typed_traces[index];
    if (!entry->valid) {
      if (empty == NULL) empty = entry;
      continue;
    }
    if (entry->section_analysis != section_analysis ||
        entry->include_section_slots != include_section_slots ||
        entry->origin != origin ||
        entry->cursor > target_offset) {
      continue;
    }
    if (best == NULL || entry->cursor > best->cursor) best = entry;
  }
  if (best != NULL) {
    if (out_found != NULL) *out_found = 1;
    return best;
  }
  if (empty != NULL) return empty;
  return &cache->typed_traces[(origin >> 1U) & (AMIGA_TYPED_TRACE_CACHE_CAPACITY - 1U)];
}

static size_t amiga_app_slot_symbol_cache_hash(const M68kSectionAnalysisIR *section_analysis, int16_t displacement,
    int treat_as_value) {
  return ((((size_t)(uintptr_t)section_analysis) >> 4U) ^ ((size_t)(uint16_t)displacement * 2654435761U) ^
    (treat_as_value != 0 ? 0x9E37U : 0U)) & (AMIGA_APP_SLOT_SYMBOL_CACHE_CAPACITY - 1U);
}

static AmigaAppSlotSymbolCacheEntry *amiga_app_slot_symbol_cache_find(AmigaPlatformCache *cache,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value, int *out_found) {
  size_t start;
  size_t probe;
  AmigaAppSlotSymbolCacheEntry *fallback;
  if (out_found != NULL) *out_found = 0;
  if (cache == NULL) return NULL;
  start = amiga_app_slot_symbol_cache_hash(section_analysis, displacement, treat_as_value);
  fallback = &cache->app_slot_symbols[start];
  for (probe = 0U; probe < 8U; ++probe) {
    AmigaAppSlotSymbolCacheEntry *entry =
      &cache->app_slot_symbols[(start + probe) & (AMIGA_APP_SLOT_SYMBOL_CACHE_CAPACITY - 1U)];
    if (entry->valid &&
        entry->section_analysis == section_analysis &&
        entry->displacement == displacement &&
        entry->treat_as_value == (uint8_t)(treat_as_value != 0)) {
      if (out_found != NULL) *out_found = 1;
      return entry;
    }
    if (!entry->valid) return entry;
  }
  return fallback;
}

static size_t amiga_section_direct_call_cache_hash(size_t source_section_index, size_t target_section_index) {
  return ((source_section_index * 1315423911U) ^ (target_section_index * 2654435761U)) &
    (AMIGA_SECTION_DIRECT_CALL_CACHE_CAPACITY - 1U);
}

static AmigaSectionDirectCallCacheEntry *amiga_section_direct_call_cache_find(AmigaPlatformCache *cache,
    size_t source_section_index, size_t target_section_index, int *out_found) {
  size_t start;
  size_t probe;
  AmigaSectionDirectCallCacheEntry *fallback;
  if (out_found != NULL) *out_found = 0;
  if (cache == NULL) return NULL;
  start = amiga_section_direct_call_cache_hash(source_section_index, target_section_index);
  fallback = &cache->section_direct_calls[start];
  for (probe = 0U; probe < 8U; ++probe) {
    AmigaSectionDirectCallCacheEntry *entry =
      &cache->section_direct_calls[(start + probe) & (AMIGA_SECTION_DIRECT_CALL_CACHE_CAPACITY - 1U)];
    if (entry->valid &&
        entry->source_section_index == source_section_index &&
        entry->target_section_index == target_section_index) {
      if (out_found != NULL) *out_found = 1;
      return entry;
    }
    if (!entry->valid) return entry;
  }
  return fallback;
}

static size_t amiga_base_slot_id_cache_hash(const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  return ((((size_t)(uintptr_t)section_analysis) >> 4U) ^ ((size_t)(uint16_t)displacement * 2246822519U)) &
    (AMIGA_BASE_SLOT_ID_CACHE_CAPACITY - 1U);
}

static AmigaBaseSlotIdCacheEntry *amiga_base_slot_id_cache_find(AmigaPlatformCache *cache,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int *out_found) {
  size_t start;
  size_t probe;
  AmigaBaseSlotIdCacheEntry *fallback;
  if (out_found != NULL) *out_found = 0;
  if (cache == NULL) return NULL;
  start = amiga_base_slot_id_cache_hash(section_analysis, displacement);
  fallback = &cache->base_slot_ids[start];
  for (probe = 0U; probe < 8U; ++probe) {
    AmigaBaseSlotIdCacheEntry *entry =
      &cache->base_slot_ids[(start + probe) & (AMIGA_BASE_SLOT_ID_CACHE_CAPACITY - 1U)];
    if (entry->valid && entry->section_analysis == section_analysis && entry->displacement == displacement) {
      if (out_found != NULL) *out_found = 1;
      return entry;
    }
    if (!entry->valid) return entry;
  }
  return fallback;
}

static uint16_t lookup_recovered_platform_base_slot_id_cached(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement) {
  AmigaPlatformCache *cache;
  AmigaBaseSlotIdCacheEntry *entry;
  int found = 0;
  uint16_t base_id;
  if (ctx == NULL) return lookup_recovered_platform_base_slot_id_local(section_analysis, displacement);
  cache = amiga_platform_cache_for_ctx(ctx);
  entry = amiga_base_slot_id_cache_find(cache, section_analysis, displacement, &found);
  if (found && entry != NULL) return entry->base_id;
  base_id = lookup_recovered_platform_base_slot_id_local(section_analysis, displacement);
  if (entry != NULL) {
    entry->valid = 1U;
    entry->section_analysis = section_analysis;
    entry->displacement = displacement;
    entry->base_id = base_id;
  }
  return base_id;
}

static void init_amiga_typed_stack_entry(AmigaTypedStackEntry *entry) {
  if (entry == NULL) return;
  init_amiga_value_provenance(&entry->value);
}

static void push_amiga_typed_stack_entry(AmigaTypedStackEntry *stack, size_t stack_capacity, size_t *stack_count,
    const AmigaValueProvenance *value) {
  if (stack == NULL || stack_count == NULL || *stack_count >= stack_capacity) return;
  if (value != NULL) stack[*stack_count].value = *value;
  else init_amiga_value_provenance(&stack[*stack_count].value);
  ++(*stack_count);
}

static int pop_amiga_typed_stack_entry(AmigaTypedStackEntry *stack, size_t *stack_count,
    AmigaTypedStackEntry *out_entry) {
  if (stack == NULL || stack_count == NULL || *stack_count == 0U || out_entry == NULL) return 0;
  --(*stack_count);
  *out_entry = stack[*stack_count];
  return 1;
}

static void clear_amiga_typed_local_slot_entry(AmigaTypedLocalSlotEntry *entry) {
  if (entry == NULL) return;
  entry->base_id = 0U;
  entry->displacement = INT16_MIN;
  init_amiga_value_provenance(&entry->value);
}

static void clear_amiga_typed_local_slots_for_base(AmigaTypedLocalSlotEntry *slots, size_t slot_count,
    uint16_t base_id) {
  size_t index;
  if (slots == NULL || base_id == 0U) return;
  for (index = 0; index < slot_count; ++index) {
    if (slots[index].base_id != base_id) continue;
    clear_amiga_typed_local_slot_entry(&slots[index]);
  }
}

static void set_amiga_typed_local_slot_entry(AmigaTypedLocalSlotEntry *slots, size_t slot_count, uint16_t base_id,
    int16_t displacement, const AmigaValueProvenance *value) {
  size_t index;
  size_t empty_index = slot_count;
  if (slots == NULL || slot_count == 0U || base_id == 0U) return;
  for (index = 0; index < slot_count; ++index) {
    if (slots[index].base_id == base_id && slots[index].displacement == displacement) {
      if (value != NULL) slots[index].value = *value;
      else init_amiga_value_provenance(&slots[index].value);
      return;
    }
    if (empty_index == slot_count && slots[index].base_id == 0U) empty_index = index;
  }
  if (empty_index == slot_count) return;
  slots[empty_index].base_id = base_id;
  slots[empty_index].displacement = displacement;
  if (value != NULL) slots[empty_index].value = *value;
  else init_amiga_value_provenance(&slots[empty_index].value);
}

static int lookup_amiga_typed_local_slot_entry(const AmigaTypedLocalSlotEntry *slots, size_t slot_count,
    uint16_t base_id, int16_t displacement, AmigaTypedStackEntry *out_entry) {
  size_t index;
  if (out_entry != NULL) init_amiga_typed_stack_entry(out_entry);
  if (slots == NULL || base_id == 0U || out_entry == NULL) return 0;
  for (index = 0; index < slot_count; ++index) {
    if (slots[index].base_id != base_id || slots[index].displacement != displacement) continue;
    out_entry->value = slots[index].value;
    return 1;
  }
  return 0;
}

static int operand_is_amiga_local_frame_slot(const M68kOperandIR *operand, const uint16_t *local_base_ids,
    uint8_t *out_base_reg, uint16_t *out_base_id, int16_t *out_displacement) {
  uint8_t base_reg;
  int16_t displacement;
  if (out_base_reg != NULL) *out_base_reg = 0U;
  if (out_base_id != NULL) *out_base_id = 0U;
  if (out_displacement != NULL) *out_displacement = INT16_MIN;
  if (operand == NULL || local_base_ids == NULL) return 0;
  if (!operand_is_indirect_or_disp_an(operand, &base_reg, &displacement)) return 0;
  if (base_reg >= 8U || base_reg == 6U || local_base_ids[base_reg] == 0U) return 0;
  if (out_base_reg != NULL) *out_base_reg = base_reg;
  if (out_base_id != NULL) *out_base_id = local_base_ids[base_reg];
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static int instruction_is_register_to_local_frame_slot_store(const M68kInstructionIR *instruction,
    const uint16_t *local_base_ids, uint8_t *out_source_kind, uint8_t *out_source_reg, uint16_t *out_base_id,
    int16_t *out_displacement) {
  uint8_t source_reg;
  uint8_t base_reg;
  const M68kOperandIR *source;
  const M68kOperandIR *target;
  uint16_t base_id;
  int16_t displacement;
  if (out_source_kind != NULL) *out_source_kind = 0U;
  if (out_source_reg != NULL) *out_source_reg = 0U;
  if (out_base_id != NULL) *out_base_id = 0U;
  if (out_displacement != NULL) *out_displacement = INT16_MIN;
  if (instruction->operand_count != 2U ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE) {
    return 0;
  }
  source = &instruction->operands[0];
  target = &instruction->operands[1];
  if (!operand_is_amiga_local_frame_slot(target, local_base_ids, &base_reg, &base_id, &displacement)) return 0;
  (void)base_reg;
  if (operand_data_reg_index_local(source, &source_reg)) {
    if (out_source_kind != NULL) *out_source_kind = 1U;
  } else if (operand_address_reg_index_local(source, &source_reg)) {
    if (out_source_kind != NULL) *out_source_kind = 2U;
  } else {
    return 0;
  }
  if (out_source_reg != NULL) *out_source_reg = source_reg;
  if (out_base_id != NULL) *out_base_id = base_id;
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static int instruction_is_register_to_resolved_app_slot_store(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    uint8_t *out_source_kind, uint8_t *out_source_reg, int16_t *out_displacement) {
  const M68kOperandIR *source;
  const M68kOperandIR *target;
  const char *base_name;
  uint8_t source_reg;
  uint8_t base_reg;
  int16_t displacement;
  if (out_source_kind != NULL) *out_source_kind = 0U;
  if (out_source_reg != NULL) *out_source_reg = 0U;
  if (out_displacement != NULL) *out_displacement = INT16_MIN;
  if (instruction == NULL || instruction->operand_count != 2U ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE) return 0;
  source = &instruction->operands[0];
  target = &instruction->operands[1];
  if (!operand_is_indirect_or_disp_an(target, &base_reg, &displacement) || base_reg >= 8U) return 0;
  if (base_reg == 6U) return instruction_is_register_to_app_slot_store(instruction, out_source_kind, out_source_reg,
    out_displacement);
  base_name = resolve_amiga_library_base_name_raw(ctx, section_analysis, offset, base_reg, 1);
  if (base_name == NULL || base_name[0] == '\0') return 0;
  if (operand_data_reg_index_local(source, &source_reg)) {
    if (out_source_kind != NULL) *out_source_kind = 1U;
  } else if (operand_address_reg_index_local(source, &source_reg)) {
    if (out_source_kind != NULL) *out_source_kind = 2U;
  } else {
    return 0;
  }
  if (out_source_reg != NULL) *out_source_reg = source_reg;
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static uint32_t find_amiga_typed_trace_fallback_start(const SectionAnalysisContext *ctx, uint32_t offset) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  uint32_t best = UINT32_MAX;
  if (ctx == NULL || section == NULL || offset == 0U) return UINT32_MAX;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    int decoded_any = 0;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      decoded_any = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (decoded_any && cursor == offset) {
      best = candidate;
      break;
    }
  }
  return best;
}

static int section_analysis_has_amiga_structural_slot_use(const M68kSectionAnalysisIR *section_analysis,
    int16_t displacement) {
  size_t index;
  if (section_analysis == NULL || displacement == INT16_MIN) return 0;
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
    if (call->kind == PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL && call->note_disp == displacement) return 1;
  }
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG && effect->displacement == displacement) return 1;
  }
  return 0;
}

static int trace_amiga_typed_state(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, int include_section_slots, AmigaTypedTraceState *out_state) {
  const M68kSection *section = section_analysis_context_section(ctx);
  AmigaTypedTraceCache *cache;
  AmigaTypedStackEntry *saved_stack;
  AmigaTypedLocalSlotEntry *local_slots;
  uint16_t *local_base_ids;
  uint16_t prev_local_base_ids[8];
  uint32_t origin;
  uint32_t cursor;
  int cache_found = 0;
  if (section == NULL || section_analysis == NULL || out_state == NULL) return 0;
  cursor = resolve_analysis_trace_start(ctx, section_analysis, offset);
  if (cursor == UINT32_MAX || cursor > offset) return 0;
  {
    uint32_t fallback_cursor = find_amiga_typed_trace_fallback_start(ctx, offset);
    if (fallback_cursor != UINT32_MAX && fallback_cursor < cursor) cursor = fallback_cursor;
  }
  origin = cursor;
  cache = amiga_typed_trace_cache_find(ctx, section_analysis, include_section_slots, origin, offset, &cache_found);
  if (cache_found && cache != NULL) {
    *out_state = cache->state;
    cursor = cache->cursor;
  } else {
    init_amiga_typed_trace_state(out_state, section_analysis, include_section_slots);
    if (include_section_slots) {
      seed_amiga_absolute_typed_slots_before_offset(section_analysis, cursor, out_state->absolute_typed_slots,
        sizeof(out_state->absolute_typed_slots) / sizeof(out_state->absolute_typed_slots[0]));
    }
    seed_amiga_typed_regs_from_policy(ctx, cursor, out_state->data_reg_values, out_state->addr_reg_values);
    seed_amiga_effect_state_from_preceding_fallthrough(ctx, section_analysis, cursor,
      NULL, NULL, out_state->data_reg_values, out_state->addr_reg_values, NULL, 0U,
      out_state->slot_type_names, sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]));
  }
  saved_stack = out_state->saved_stack;
  local_slots = out_state->local_slots;
  local_base_ids = out_state->local_base_ids;
  while (cursor < offset && cursor < section->data_size) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    uint8_t mnemonic_id;
    AmigaValueProvenance prev_addr_reg_values[8];
    AmigaValueProvenance prev_data_reg_values[8];
    uint8_t dest_reg;
    uint8_t pushed_reg;
    uint8_t written_reg;
    const M68kOperandIR *source = NULL;
    int16_t slot_disp;
    uint16_t movem_mask;
    if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
    instruction = decode.instruction;
    mnemonic_id = instruction.mnemonic_id;
    if (instruction.byte_count == 0U || cursor + instruction.byte_count > offset) break;
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      prev_addr_reg_values[written_reg] = out_state->addr_reg_values[written_reg];
      prev_data_reg_values[written_reg] = out_state->data_reg_values[written_reg];
      prev_local_base_ids[written_reg] = local_base_ids[written_reg];
      if (instruction_writes_data_reg_approx(&instruction, written_reg)) {
        init_amiga_value_provenance(&out_state->data_reg_values[written_reg]);
      }
      if (instruction_writes_address_reg_approx(&instruction, written_reg)) {
        clear_amiga_typed_local_slots_for_base(local_slots,
          AMIGA_TYPED_LOCAL_SLOT_CAPACITY, local_base_ids[written_reg]);
        local_base_ids[written_reg] = 0U;
        init_amiga_value_provenance(&out_state->addr_reg_values[written_reg]);
      }
    }
    if (instruction_is_data_move(&instruction, &dest_reg, &source) && source != NULL) {
      uint8_t source_reg;
      const M68kSimFormMetadata *metadata = instruction_sim_metadata(&instruction);
      size_t source_operand_index = metadata != NULL && metadata->source_operand_index < instruction.operand_count
        ? metadata->source_operand_index
        : 0U;
      if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
        out_state->data_reg_values[dest_reg] = prev_data_reg_values[source_reg];
      } else if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
        out_state->data_reg_values[dest_reg] = prev_addr_reg_values[source_reg];
      } else if (operand_is_immediate_source_local(source)) {
        init_amiga_value_provenance(&out_state->data_reg_values[dest_reg]);
        out_state->data_reg_values[dest_reg].has_constant_value = 1U;
        out_state->data_reg_values[dest_reg].constant_value = (int32_t)source->value.value;
        out_state->data_reg_values[dest_reg].source_offset = cursor;
        out_state->data_reg_values[dest_reg].source_reg_kind = 1U;
        out_state->data_reg_values[dest_reg].source_reg_index = dest_reg;
      } else if (operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        uint16_t loaded_base_id = resolve_amiga_app_slot_base_id(ctx, section_analysis, slot_disp);
        AmigaValueProvenance loaded_value;
        init_amiga_value_provenance(&out_state->data_reg_values[dest_reg]);
        if (lookup_amiga_effect_or_local_typed_slot_value(section_analysis, out_state->slot_type_names,
              sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]), slot_disp,
              &loaded_value)) {
          out_state->data_reg_values[dest_reg] = loaded_value;
        }
        if (amiga_value_provenance_type_name_local(&out_state->data_reg_values[dest_reg]) == NULL)
          amiga_value_provenance_set_type_name(&out_state->data_reg_values[dest_reg],
            resolve_amiga_base_type_name_from_id_local(loaded_base_id));
        if (amiga_value_provenance_owner_type_name_local(&out_state->data_reg_values[dest_reg]) == NULL)
          amiga_value_provenance_set_owner_type_name(&out_state->data_reg_values[dest_reg],
            amiga_value_provenance_type_name_local(&out_state->data_reg_values[dest_reg]));
        out_state->data_reg_values[dest_reg].slot_disp = slot_disp;
      } else {
        AmigaTypedStackEntry entry;
        AmigaValueProvenance loaded_value;
        uint16_t local_base_id;
        int16_t local_slot_disp;
        if (operand_is_amiga_local_frame_slot(source, prev_local_base_ids, NULL, &local_base_id, &local_slot_disp) &&
            lookup_amiga_typed_local_slot_entry(local_slots, AMIGA_TYPED_LOCAL_SLOT_CAPACITY,
              local_base_id, local_slot_disp, &entry)) {
          out_state->data_reg_values[dest_reg] = entry.value;
        } else if (lookup_amiga_absolute_typed_slot_operand_value(ctx, section_analysis, out_state, cursor,
            &instruction, source_operand_index, &loaded_value)) {
          out_state->data_reg_values[dest_reg] = loaded_value;
          if (amiga_value_provenance_owner_type_name_local(&out_state->data_reg_values[dest_reg]) == NULL) {
            amiga_value_provenance_copy_owner_from_type(&out_state->data_reg_values[dest_reg],
              &out_state->data_reg_values[dest_reg]);
          }
        } else if (operand_is_indirect_or_disp_an(source, &source_reg, &slot_disp) &&
            source_reg < 8U &&
            (amiga_value_provenance_type_name_local(&prev_addr_reg_values[source_reg]) != NULL ||
             amiga_value_provenance_owner_type_name_local(&prev_addr_reg_values[source_reg]) != NULL ||
             prev_addr_reg_values[source_reg].slot_disp != INT16_MIN)) {
          const char *container_type_name = amiga_value_provenance_type_name_local(&prev_addr_reg_values[source_reg]) != NULL
            ? amiga_value_provenance_type_name_local(&prev_addr_reg_values[source_reg])
            : amiga_value_provenance_owner_type_name_local(&prev_addr_reg_values[source_reg]);
          char field_symbol_name[64];
          init_amiga_value_provenance(&out_state->data_reg_values[dest_reg]);
          amiga_value_provenance_set_type_name(&out_state->data_reg_values[dest_reg],
            resolve_amiga_struct_field_nested_type_name(container_type_name, slot_disp));
          amiga_value_provenance_set_owner_type_name(&out_state->data_reg_values[dest_reg], container_type_name);
          out_state->data_reg_values[dest_reg].slot_disp = prev_addr_reg_values[source_reg].slot_disp;
          out_state->data_reg_values[dest_reg].field_disp = slot_disp;
          if (resolve_amiga_struct_field_symbol_name(container_type_name, slot_disp, field_symbol_name,
                sizeof(field_symbol_name))) {
            amiga_value_provenance_set_field_symbol_name(&out_state->data_reg_values[dest_reg],
              arena_strdup(section_analysis->arena, field_symbol_name));
            amiga_value_provenance_set_value_domain_name(&out_state->data_reg_values[dest_reg],
              amiga_os_find_struct_field_value_domain(container_type_name, field_symbol_name, NULL));
          }
        }
      }
    }
    if (instruction_is_address_move(&instruction, &dest_reg, &source) && source != NULL) {
      uint8_t source_reg;
      int16_t field_disp;
      const M68kSimFormMetadata *metadata = instruction_sim_metadata(&instruction);
      size_t source_operand_index = metadata != NULL && metadata->source_operand_index < instruction.operand_count
        ? metadata->source_operand_index
        : 0U;
      if (operand_is_app_base_disp_ea(source, 6U, &slot_disp)) {
        uint16_t loaded_base_id = resolve_amiga_app_slot_base_id(ctx, section_analysis, slot_disp);
        AmigaValueProvenance loaded_value;
        init_amiga_value_provenance(&out_state->addr_reg_values[dest_reg]);
        out_state->addr_reg_values[dest_reg].slot_disp = slot_disp;
        if (lookup_amiga_effect_or_local_typed_slot_value(section_analysis, out_state->slot_type_names,
              sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]), slot_disp,
              &loaded_value)) {
          out_state->addr_reg_values[dest_reg] = loaded_value;
        }
        if (amiga_value_provenance_type_name_local(&out_state->addr_reg_values[dest_reg]) == NULL)
          amiga_value_provenance_set_type_name(&out_state->addr_reg_values[dest_reg],
            resolve_amiga_base_type_name_from_id_local(loaded_base_id));
        if (amiga_value_provenance_owner_type_name_local(&out_state->addr_reg_values[dest_reg]) == NULL)
          amiga_value_provenance_set_owner_type_name(&out_state->addr_reg_values[dest_reg],
            amiga_value_provenance_type_name_local(&out_state->addr_reg_values[dest_reg]));
        out_state->addr_reg_values[dest_reg].slot_disp = slot_disp;
      } else {
        AmigaTypedStackEntry entry;
        AmigaValueProvenance loaded_value;
        uint16_t local_base_id;
        int16_t local_slot_disp;
        if (operand_is_amiga_local_frame_slot(source, prev_local_base_ids, NULL, &local_base_id, &local_slot_disp) &&
            lookup_amiga_typed_local_slot_entry(local_slots, AMIGA_TYPED_LOCAL_SLOT_CAPACITY,
              local_base_id, local_slot_disp, &entry)) {
          out_state->addr_reg_values[dest_reg] = entry.value;
        } else if (lookup_amiga_absolute_typed_slot_operand_value(ctx, section_analysis, out_state, cursor,
            &instruction, source_operand_index, &loaded_value)) {
          out_state->addr_reg_values[dest_reg] = loaded_value;
          if (amiga_value_provenance_owner_type_name_local(&out_state->addr_reg_values[dest_reg]) == NULL) {
            amiga_value_provenance_copy_owner_from_type(&out_state->addr_reg_values[dest_reg],
              &out_state->addr_reg_values[dest_reg]);
          }
        } else if (operand_address_reg_index_local(source, &source_reg) && source_reg < 8U) {
          out_state->addr_reg_values[dest_reg] = prev_addr_reg_values[source_reg];
        } else if (operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
          out_state->addr_reg_values[dest_reg] = prev_data_reg_values[source_reg];
        } else if (operand_is_immediate_source_local(source)) {
          init_amiga_value_provenance(&out_state->addr_reg_values[dest_reg]);
          out_state->addr_reg_values[dest_reg].has_constant_value = 1U;
          out_state->addr_reg_values[dest_reg].constant_value = (int32_t)source->value.value;
          out_state->addr_reg_values[dest_reg].source_offset = cursor;
          out_state->addr_reg_values[dest_reg].source_reg_kind = 2U;
          out_state->addr_reg_values[dest_reg].source_reg_index = dest_reg;
        } else if (operand_is_indirect_or_disp_an(source, &source_reg, &field_disp) &&
            source_reg < 8U &&
            (amiga_value_provenance_type_name_local(&prev_addr_reg_values[source_reg]) != NULL ||
             amiga_value_provenance_owner_type_name_local(&prev_addr_reg_values[source_reg]) != NULL ||
             prev_addr_reg_values[source_reg].slot_disp != INT16_MIN)) {
          const char *container_type_name = amiga_value_provenance_type_name_local(&prev_addr_reg_values[source_reg]) != NULL
            ? amiga_value_provenance_type_name_local(&prev_addr_reg_values[source_reg])
            : amiga_value_provenance_owner_type_name_local(&prev_addr_reg_values[source_reg]);
          const char *nested_type_name =
            resolve_amiga_struct_field_nested_type_name(container_type_name, field_disp);
          char field_symbol_name[64];
          init_amiga_value_provenance(&out_state->addr_reg_values[dest_reg]);
          out_state->addr_reg_values[dest_reg].slot_disp = prev_addr_reg_values[source_reg].slot_disp;
          out_state->addr_reg_values[dest_reg].field_disp = field_disp;
          amiga_value_provenance_set_type_name(&out_state->addr_reg_values[dest_reg], nested_type_name);
          amiga_value_provenance_set_owner_type_name(&out_state->addr_reg_values[dest_reg], container_type_name);
          if (resolve_amiga_struct_field_symbol_name(container_type_name, field_disp, field_symbol_name,
                sizeof(field_symbol_name))) {
            amiga_value_provenance_set_field_symbol_name(&out_state->addr_reg_values[dest_reg],
              arena_strdup(section_analysis->arena, field_symbol_name));
            amiga_value_provenance_set_value_domain_name(&out_state->addr_reg_values[dest_reg],
              amiga_os_find_struct_field_value_domain(container_type_name, field_symbol_name, NULL));
          }
          if (nested_type_name != NULL) amiga_value_provenance_set_semantic_kind_name(&out_state->addr_reg_values[dest_reg], NULL);
        }
      }
      if (source != NULL && operand_address_reg_index_local(source, &source_reg) && source_reg < 8U &&
          prev_local_base_ids[source_reg] != 0U) {
        local_base_ids[dest_reg] = prev_local_base_ids[source_reg];
      } else if (source != NULL && operand_data_reg_index_local(source, &source_reg) && source_reg < 8U) {
        local_base_ids[dest_reg] = 0U;
      } else if (source != NULL && operand_address_reg_index_local(source, &source_reg) && source_reg == 7U) {
      local_base_ids[dest_reg] = out_state->next_local_base_id++;
      }
    } else if (mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[1], &dest_reg) &&
        operand_is_app_base_disp_ea(&instruction.operands[0], 6U, &slot_disp)) {
      uint16_t loaded_base_id = resolve_amiga_app_slot_base_id(ctx, section_analysis, slot_disp);
      AmigaValueProvenance loaded_value;
      init_amiga_value_provenance(&out_state->addr_reg_values[dest_reg]);
      out_state->addr_reg_values[dest_reg].slot_disp = slot_disp;
      if (lookup_amiga_effect_or_local_typed_slot_value(section_analysis, out_state->slot_type_names,
            sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]), slot_disp,
            &loaded_value)) {
        out_state->addr_reg_values[dest_reg] = loaded_value;
      }
      if (amiga_value_provenance_type_name_local(&out_state->addr_reg_values[dest_reg]) == NULL) {
        amiga_value_provenance_set_type_name(&out_state->addr_reg_values[dest_reg],
          resolve_amiga_base_type_name_from_id_local(loaded_base_id));
      }
      if (amiga_value_provenance_owner_type_name_local(&out_state->addr_reg_values[dest_reg]) == NULL) {
        amiga_value_provenance_copy_owner_from_type(&out_state->addr_reg_values[dest_reg],
          &out_state->addr_reg_values[dest_reg]);
      }
    } else if (mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[1], &dest_reg)) {
      const M68kSimFormMetadata *metadata = instruction_sim_metadata(&instruction);
      uint32_t target;
      if (instruction_render_operand_target(&instruction, metadata, 0U, cursor, section->data_size, &target)) {
        init_amiga_value_provenance(&out_state->addr_reg_values[dest_reg]);
        out_state->addr_reg_values[dest_reg].has_constant_value = 1U;
        out_state->addr_reg_values[dest_reg].constant_value = (int32_t)target;
        out_state->addr_reg_values[dest_reg].source_offset = cursor;
        out_state->addr_reg_values[dest_reg].source_reg_kind = 2U;
        out_state->addr_reg_values[dest_reg].source_reg_index = dest_reg;
      }
    } else if (mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[1], &dest_reg) &&
        operand_is_indirect_or_disp_an(&instruction.operands[0], &pushed_reg, &slot_disp)) {
      if (pushed_reg == 7U) {
        local_base_ids[dest_reg] = out_state->next_local_base_id++;
      } else if (pushed_reg < 8U && prev_local_base_ids[pushed_reg] != 0U && slot_disp == 0) {
        local_base_ids[dest_reg] = prev_local_base_ids[pushed_reg];
      } else if (pushed_reg < 8U && prev_local_base_ids[pushed_reg] != 0U) {
        local_base_ids[dest_reg] = out_state->next_local_base_id++;
      }
    } else if (mnemonic_id == M68K_ASM_MNEMONIC_LINK &&
        instruction.operand_count == 2U &&
        operand_address_reg_index_local(&instruction.operands[0], &dest_reg)) {
        local_base_ids[dest_reg] = out_state->next_local_base_id++;
    }
    {
      uint8_t local_store_source_kind;
      uint8_t local_store_source_reg;
      uint16_t local_store_base_id;
      int16_t local_slot_disp;
      if (instruction_is_register_to_local_frame_slot_store(&instruction, prev_local_base_ids, &local_store_source_kind,
            &local_store_source_reg, &local_store_base_id, &local_slot_disp)) {
        if (local_store_source_kind == 1U && local_store_source_reg < 8U) {
          set_amiga_typed_local_slot_entry(local_slots, AMIGA_TYPED_LOCAL_SLOT_CAPACITY, local_store_base_id,
            local_slot_disp, &prev_data_reg_values[local_store_source_reg]);
        } else if (local_store_source_kind == 2U && local_store_source_reg < 8U) {
          set_amiga_typed_local_slot_entry(local_slots, AMIGA_TYPED_LOCAL_SLOT_CAPACITY, local_store_base_id,
            local_slot_disp, &prev_addr_reg_values[local_store_source_reg]);
        }
      } else {
        const M68kOperandIR *dest_operand = NULL;
        if (instruction_target_operand_local(&instruction, &dest_operand) &&
            dest_operand != NULL &&
            operand_is_amiga_local_frame_slot(dest_operand, prev_local_base_ids, NULL, &local_store_base_id,
              &local_slot_disp)) {
          set_amiga_typed_local_slot_entry(local_slots, AMIGA_TYPED_LOCAL_SLOT_CAPACITY, local_store_base_id,
            local_slot_disp, NULL);
        }
      }
    }
    if (instruction_pushes_data_reg_to_stack_local(&instruction, &pushed_reg) &&
        pushed_reg < 8U) {
      push_amiga_typed_stack_entry(saved_stack, AMIGA_TYPED_STACK_CAPACITY, &out_state->saved_stack_count,
        &prev_data_reg_values[pushed_reg]);
    } else {
      PlatformRegisterMatch pushed_addr = instruction_push_address_reg_to_stack(&instruction);
      if (pushed_addr.ok && pushed_addr.reg < 8U) {
        push_amiga_typed_stack_entry(saved_stack, AMIGA_TYPED_STACK_CAPACITY, &out_state->saved_stack_count,
          &prev_addr_reg_values[pushed_addr.reg]);
      } else if (instruction_pushes_movem_to_stack_local(&instruction, &movem_mask)) {
      int bit;
      for (bit = 15; bit >= 0; --bit) {
        if ((movem_mask & (uint16_t)(1U << bit)) == 0U) continue;
        if (bit < 8) {
          push_amiga_typed_stack_entry(saved_stack, AMIGA_TYPED_STACK_CAPACITY, &out_state->saved_stack_count,
            &prev_data_reg_values[bit]);
        } else {
          uint8_t addr_reg = (uint8_t)(bit - 8);
          push_amiga_typed_stack_entry(saved_stack, AMIGA_TYPED_STACK_CAPACITY, &out_state->saved_stack_count,
            &prev_addr_reg_values[addr_reg]);
        }
      }
      }
    }
    if (instruction_pops_data_reg_from_stack_local(&instruction, &dest_reg) &&
        dest_reg < 8U) {
      AmigaTypedStackEntry entry;
      if (pop_amiga_typed_stack_entry(saved_stack, &out_state->saved_stack_count, &entry)) {
        out_state->data_reg_values[dest_reg] = entry.value;
      }
    } else {
      PlatformRegisterMatch popped_addr = instruction_pop_address_reg_from_stack(&instruction);
      if (popped_addr.ok && popped_addr.reg < 8U) {
        AmigaTypedStackEntry entry;
        if (pop_amiga_typed_stack_entry(saved_stack, &out_state->saved_stack_count, &entry)) {
          out_state->addr_reg_values[popped_addr.reg] = entry.value;
        }
      } else if (instruction_pops_movem_from_stack_local(&instruction, &movem_mask)) {
      unsigned bit;
      for (bit = 0U; bit < 16U; ++bit) {
        AmigaTypedStackEntry entry;
        if ((movem_mask & (uint16_t)(1U << bit)) == 0U) continue;
        if (!pop_amiga_typed_stack_entry(saved_stack, &out_state->saved_stack_count, &entry)) break;
        if (bit < 8U) {
          out_state->data_reg_values[bit] = entry.value;
        } else {
          uint8_t addr_reg = (uint8_t)(bit - 8U);
          out_state->addr_reg_values[addr_reg] = entry.value;
        }
      }
      }
    }
    for (written_reg = 0U; written_reg < 8U; ++written_reg) {
      if (instruction_writes_data_reg_approx(&instruction, written_reg) &&
          !amiga_value_provenance_has_any_info(&out_state->data_reg_values[written_reg]) &&
          instruction_preserves_pointer_provenance_local(&instruction, 1U, written_reg)) {
        out_state->data_reg_values[written_reg] = prev_data_reg_values[written_reg];
      }
      if (instruction_writes_address_reg_approx(&instruction, written_reg) &&
          !amiga_value_provenance_has_any_info(&out_state->addr_reg_values[written_reg]) &&
          instruction_preserves_pointer_provenance_local(&instruction, 2U, written_reg)) {
        out_state->addr_reg_values[written_reg] = prev_addr_reg_values[written_reg];
      }
    }
    {
      PlatformAddressExgInfo exg = instruction_address_exg(&instruction);
      if (exg.ok) {
        uint16_t tmp = local_base_ids[exg.left_reg];
        local_base_ids[exg.left_reg] = local_base_ids[exg.right_reg];
        local_base_ids[exg.right_reg] = tmp;
      }
    }
    apply_recovered_amiga_platform_effects(section_analysis, cursor, NULL, NULL,
      out_state->data_reg_values, out_state->addr_reg_values, NULL, 0U,
      out_state->slot_type_names, sizeof(out_state->slot_type_names) / sizeof(out_state->slot_type_names[0]));
    if (include_section_slots) {
      apply_recovered_amiga_typed_global_slot_effects_at_offset(section_analysis, cursor,
        out_state->absolute_typed_slots,
        sizeof(out_state->absolute_typed_slots) / sizeof(out_state->absolute_typed_slots[0]));
    }
    cursor += (uint32_t)instruction.byte_count;
  }
  if (cache != NULL) {
    cache->section_analysis = section_analysis;
    cache->include_section_slots = include_section_slots;
    cache->origin = origin;
    cache->cursor = cursor;
    cache->state = *out_state;
    cache->valid = 1U;
  }
  return 1;
}

static int resolve_amiga_address_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedAddressRegInfo *out_info) {
  AmigaTypedTraceState state;
  if (out_info != NULL) init_amiga_value_provenance(out_info);
  if (section_analysis == NULL || reg >= 8U || out_info == NULL) return 0;
  if (!trace_amiga_typed_state(ctx, section_analysis, offset, include_section_slots, &state) ||
      !amiga_value_provenance_has_any_info(&state.addr_reg_values[reg])) {
    uint8_t source_data_reg;
    AmigaResolvedDataRegInfo data_info;
    if (resolve_preceding_move_source_data_reg(ctx, section_analysis, offset, reg, &source_data_reg) &&
        (resolve_preceding_field_loaded_data_reg_info(ctx, section_analysis, offset, source_data_reg, &data_info) ||
         resolve_amiga_data_reg_info(ctx, section_analysis, offset, source_data_reg, include_section_slots, &data_info) ||
         resolve_amiga_data_reg_info_from_success_local_calls_uncached(ctx, section_analysis, offset, source_data_reg,
           &data_info))) {
      *out_info = data_info;
      return 1;
    }
    return resolve_preceding_stack_reloaded_address_reg_info(ctx, section_analysis, offset, reg,
      include_section_slots, out_info);
  }
  *out_info = state.addr_reg_values[reg];
  return 1;
}

static int resolve_amiga_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedDataRegInfo *out_info) {
  AmigaTypedTraceState state;
  if (out_info != NULL) init_amiga_value_provenance(out_info);
  if (section_analysis == NULL || reg >= 8U || out_info == NULL) return 0;
  if (!trace_amiga_typed_state(ctx, section_analysis, offset, include_section_slots, &state)) return 0;
  if (!amiga_value_provenance_has_any_info(&state.data_reg_values[reg])) return 0;
  *out_info = state.data_reg_values[reg];
  return 1;
}

static int resolve_preceding_move_source_data_reg(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t dest_reg, uint8_t *out_source_reg) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  if (ctx == NULL || section == NULL || section_analysis == NULL || out_source_reg == NULL) return 0;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    uint32_t prev_offset = UINT32_MAX;
    M68kInstructionIR prev_instruction;
    int have_prev = 0;
    uint8_t moved_dest_reg;
    const M68kOperandIR *source = NULL;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      prev_instruction = decode.instruction;
      prev_offset = cursor;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (!have_prev || prev_offset == UINT32_MAX || cursor != offset) continue;
    if (!instruction_is_address_move(&prev_instruction, &moved_dest_reg, &source) || moved_dest_reg != dest_reg) continue;
    if (!operand_data_reg_index_local(source, out_source_reg) || *out_source_reg >= 8U) continue;
    return 1;
  }
  return 0;
}

static int resolve_preceding_field_loaded_data_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t data_reg, AmigaResolvedDataRegInfo *out_info) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  if (out_info != NULL) init_amiga_value_provenance(out_info);
  if (ctx == NULL || section == NULL || section_analysis == NULL || out_info == NULL) return 0;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    uint32_t prev_offset = UINT32_MAX;
    M68kInstructionIR prev_instruction;
    int have_prev = 0;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      prev_offset = cursor;
      prev_instruction = decode.instruction;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (!have_prev || cursor != offset || prev_offset == UINT32_MAX) continue;
    {
      uint8_t dest_reg;
      const M68kOperandIR *source = NULL;
      AmigaResolvedAddressRegInfo owner_info;
      int16_t field_disp;
      uint8_t owner_reg;
      if (!instruction_is_data_move(&prev_instruction, &dest_reg, &source) || dest_reg != data_reg || source == NULL) continue;
      if (!operand_is_indirect_or_disp_an(source, &owner_reg, &field_disp)) continue;
      if (!resolve_amiga_address_reg_info(ctx, section_analysis, offset, owner_reg, 1, &owner_info)) continue;
      init_amiga_value_provenance(out_info);
      out_info->slot_disp = owner_info.slot_disp;
      out_info->field_disp = field_disp;
      amiga_value_provenance_set_type_name(out_info,
        resolve_amiga_struct_field_nested_type_name(amiga_value_provenance_type_name_local(&owner_info), field_disp));
      amiga_value_provenance_copy_owner_from_type(out_info, &owner_info);
      if (amiga_value_provenance_owner_type_name_local(out_info) != NULL) {
        char field_symbol_name[64];
        if (resolve_amiga_struct_field_symbol_name(amiga_value_provenance_owner_type_name_local(out_info), field_disp, field_symbol_name,
              sizeof(field_symbol_name))) {
          amiga_value_provenance_set_field_symbol_name(out_info,
            arena_strdup(section_analysis->arena, field_symbol_name));
        }
      }
      if (amiga_value_provenance_type_name_local(out_info) != NULL ||
          amiga_value_provenance_owner_type_name_local(out_info) != NULL) return 1;
    }
  }
  return 0;
}

static int resolve_preceding_stack_reloaded_address_reg_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedAddressRegInfo *out_info) {
  const M68kSection *section = section_analysis_context_section(ctx);
  uint32_t low;
  uint32_t candidate;
  if (out_info != NULL) init_amiga_value_provenance(out_info);
  if (ctx == NULL || section == NULL || section_analysis == NULL || out_info == NULL || reg >= 8U) return 0;
  low = offset > 24U ? (offset - 24U) : 0U;
  for (candidate = low; candidate < offset; ++candidate) {
    uint32_t cursor = candidate;
    uint32_t prev_offset = UINT32_MAX;
    uint32_t second_prev_offset = UINT32_MAX;
    SectionDecodeResult prev_decode = {0};
    SectionDecodeResult second_prev_decode = {0};
    int have_prev = 0;
    int have_second_prev = 0;
    while (cursor < offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U || cursor + decode.instruction.byte_count > offset) break;
      second_prev_offset = prev_offset;
      second_prev_decode = prev_decode;
      have_second_prev = have_prev;
      prev_offset = cursor;
      prev_decode = decode;
      have_prev = 1;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (!have_prev || !have_second_prev || cursor != offset) continue;
    {
      PlatformRegisterMatch popped;
      PlatformRegisterMatch pushed_addr;
      uint8_t pushed_reg;
      uint8_t source_reg_kind, source_reg_index;
      uint16_t push_movem_mask, pop_movem_mask;
      AmigaResolvedDataRegInfo data_info;
      AmigaResolvedAddressRegInfo addr_info;
      if (instruction_pops_movem_from_stack_local(&prev_decode.instruction, &pop_movem_mask) &&
          instruction_pushes_movem_to_stack_local(&second_prev_decode.instruction, &push_movem_mask) &&
          resolve_movem_stack_pair_source_local(push_movem_mask, pop_movem_mask, 2U, reg, &source_reg_kind,
            &source_reg_index)) {
        if (source_reg_kind == 1U &&
            resolve_amiga_data_reg_info(ctx, section_analysis, second_prev_offset, source_reg_index,
              include_section_slots, &data_info)) {
          *out_info = data_info;
          return amiga_value_provenance_has_any_info(out_info);
        }
        if (source_reg_kind == 2U &&
            resolve_amiga_address_reg_info(ctx, section_analysis, second_prev_offset, source_reg_index,
              include_section_slots, &addr_info)) {
          *out_info = addr_info;
          return 1;
        }
      }
      popped = instruction_pop_address_reg_from_stack(&prev_decode.instruction);
      if (!popped.ok || popped.reg != reg) continue;
      if (instruction_pushes_data_reg_to_stack_local(&second_prev_decode.instruction, &pushed_reg) &&
          resolve_amiga_data_reg_info(ctx, section_analysis, second_prev_offset, pushed_reg, include_section_slots, &data_info)) {
        *out_info = data_info;
        return amiga_value_provenance_has_any_info(out_info);
      }
      pushed_addr = instruction_push_address_reg_to_stack(&second_prev_decode.instruction);
      if (pushed_addr.ok &&
          resolve_amiga_address_reg_info(ctx, section_analysis, second_prev_offset, pushed_addr.reg,
            include_section_slots, &addr_info)) {
        *out_info = addr_info;
        return 1;
      }
    }
  }
  return 0;
}

static const char *resolve_amiga_library_base_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg) {
  return resolve_amiga_library_base_name_raw(ctx, section_analysis, offset, reg, 1);
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_library_vector_entry(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  const char *base_name;
  if (ctx == NULL || section_analysis_context_object(ctx) == NULL) return NULL;
  if (section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return NULL;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return NULL;
  {
    const M68kOperandIR *operand = NULL;
    if (!instruction_target_operand_local(instruction, &operand) || operand == NULL) return NULL;
    if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return NULL;
    if (operand->value.ea_mode != 5U || operand->value.ea_reg >= 8U) return NULL;
    base_name = resolve_amiga_library_base_name(ctx, section_analysis, offset, operand->value.ea_reg);
  }
  if (base_name == NULL) return NULL;
  return resolve_amiga_library_vector_entry_for_base_name(instruction, base_name);
}

PlatformResolvedIndirectInfo resolve_amiga_library_vector_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  PlatformResolvedIndirectInfo info;
  const M68kRecoveredPlatformCallIR *recovered;
  const AmigaOsLibraryVectorInfo *entry;
  info = platform_resolved_indirect_info_none();
  recovered = find_recovered_platform_call(section_analysis, offset, PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL);
  if (recovered != NULL) {
    load_recovered_platform_call_info(recovered, &info);
    return info;
  }
  entry = resolve_amiga_library_vector_entry(ctx, section_analysis, offset, instruction);
  if (entry == NULL) return info;
  {
    const char *symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, entry->lvo_symbol_id);
    info.kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL;
    info.has_symbol_name = 1U;
    snprintf(info.symbol_name, sizeof(info.symbol_name), "%s", symbol_name != NULL ? symbol_name : "");
    populate_amiga_call_version_info(entry, &info);
  }
  return info;
}

static const M68kRecoveredPlatformEffectIR *find_recovered_typed_reg_effect_for_reg(
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg_kind, uint8_t reg_index) {
  size_t index;
  const M68kRecoveredPlatformEffectIR *effect;
  if (section_analysis == NULL) return NULL;
  effect = first_recovered_platform_effect_at_offset(section_analysis, offset);
  if (section_analysis->recovered_platform_effect_lookup != NULL) {
    for (; effect != NULL; effect = next_recovered_platform_effect_at_same_offset(section_analysis, effect)) {
      if (effect->kind != M68K_PLATFORM_EFFECT_SET_TYPED_REG) continue;
      if (effect->reg_kind != reg_kind || effect->reg_index != reg_index) continue;
      return effect;
    }
    return NULL;
  }
  for (index = 0U; index < section_analysis->recovered_platform_effect_count; ++index) {
    effect = &section_analysis->recovered_platform_effects[index];
    if (effect->offset != offset || effect->kind != M68K_PLATFORM_EFFECT_SET_TYPED_REG) continue;
    if (effect->reg_kind != reg_kind || effect->reg_index != reg_index) continue;
    return effect;
  }
  return NULL;
}

PlatformResolvedIndirectInfo resolve_amiga_indexed_library_dispatch_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  PlatformResolvedIndirectInfo info;
  const M68kRecoveredPlatformCallIR *recovered;
  const M68kOperandIR *operand = NULL;
  const char *base_name;
  uint8_t base_reg;
  uint8_t index_is_address;
  uint8_t index_reg;
  int32_t disp;
  info = platform_resolved_indirect_info_none();
  recovered = find_recovered_platform_call(section_analysis, offset, PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH);
  if (recovered != NULL) {
    load_recovered_platform_call_info(recovered, &info);
    return info;
  }
  if (ctx == NULL || section_analysis_context_object(ctx) == NULL) return info;
  if (section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return info;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return info;
  if (!instruction_is_call_transfer(instruction)) return info;
  if (!instruction_target_operand_local(instruction, &operand) || operand == NULL) return info;
  if (!operand_is_brief_indexed_an(operand, &base_reg, &index_is_address, &index_reg, &disp)) return info;
  if (base_reg != 6U || index_is_address != 0U || disp != 0) return info;
  base_name = resolve_amiga_library_base_name(ctx, section_analysis, offset, base_reg);
  if (base_name == NULL) return info;
  if (amiga_os_name_id(M68K_PLATFORM_NAME_BASE, base_name) != AMIGA_OS_BASE_ID_DOSBASE) return info;
  info.kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH;
  info.note_kind = M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR;
  info.note_reg = index_reg;
  snprintf(info.note_base_name, sizeof(info.note_base_name), "%s", base_name);
  return info;
}

PlatformResolvedIndirectInfo resolve_amiga_callback_field_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  PlatformResolvedIndirectInfo out_info;
  const M68kRecoveredPlatformCallIR *recovered;
  const M68kOperandIR *target_operand = NULL;
  uint8_t target_reg;
  AmigaResolvedAddressRegInfo info;
  AmigaResolvedDataRegInfo data_info;
  out_info = platform_resolved_indirect_info_none();
  recovered = find_recovered_platform_call(section_analysis, offset, PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL);
  if (recovered != NULL) {
    load_recovered_platform_call_info(recovered, &out_info);
    return out_info;
  }
  if (ctx == NULL) return out_info;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return out_info;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return out_info;
  if (!instruction_is_call_transfer(instruction)) return out_info;
  if (!instruction_target_operand_local(instruction, &target_operand) || target_operand == NULL) return out_info;
  if (!operand_is_indirect_an(target_operand, &target_reg)) return out_info;
  {
    size_t effect_index;
    const M68kRecoveredPlatformEffectIR *effect = first_recovered_platform_effect_at_offset(section_analysis, offset);
    if (section_analysis->recovered_platform_effect_lookup != NULL) {
      effect_index = 0U;
    } else {
      effect = section_analysis->recovered_platform_effect_count != 0U ? &section_analysis->recovered_platform_effects[0] : NULL;
      effect_index = 0U;
    }
    while (effect != NULL) {
      const char *owner_type_name;
      const char *field_symbol_name;
      if (effect->offset == offset &&
          effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG &&
          effect->reg_kind == 2U &&
          effect->reg_index == target_reg &&
          (effect->payload.code_ptr.owner_type_name != NULL ||
           effect->payload.code_ptr.owner_type_ref.id != 0U)) {
        owner_type_name = effect->payload.code_ptr.owner_type_name != NULL
          ? effect->payload.code_ptr.owner_type_name
          : amiga_os_name(M68K_PLATFORM_NAME_TYPE, effect->payload.code_ptr.owner_type_ref.id);
        field_symbol_name = effect->payload.code_ptr.field_symbol_name != NULL
          ? effect->payload.code_ptr.field_symbol_name
          : amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, effect->payload.code_ptr.field_symbol_ref.id);
        out_info.kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL;
        out_info.note_kind = M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD;
        out_info.note_disp = effect->displacement;
        out_info.note_field_disp = effect->field_disp;
        snprintf(out_info.note_base_name, sizeof(out_info.note_base_name), "%s", owner_type_name != NULL ? owner_type_name : "");
        if (field_symbol_name != NULL && field_symbol_name[0] != '\0') {
          snprintf(out_info.note_symbol_name, sizeof(out_info.note_symbol_name), "%s", field_symbol_name);
        } else {
          populate_amiga_callback_field_note_symbol(&out_info);
        }
        return out_info;
      }
      if (section_analysis->recovered_platform_effect_lookup != NULL) {
        effect = next_recovered_platform_effect_at_same_offset(section_analysis, effect);
      } else {
        ++effect_index;
        effect = effect_index < section_analysis->recovered_platform_effect_count
          ? &section_analysis->recovered_platform_effects[effect_index]
          : NULL;
      }
    }
  }
  if (!resolve_amiga_address_reg_info(ctx, section_analysis, offset, target_reg, 1, &info)) {
    uint8_t source_data_reg;
    if (!resolve_preceding_move_source_data_reg(ctx, section_analysis, offset, target_reg, &source_data_reg))
      return out_info;
    if (!resolve_preceding_field_loaded_data_reg_info(ctx, section_analysis, offset, source_data_reg, &data_info) &&
        !resolve_amiga_data_reg_info(ctx, section_analysis, offset, source_data_reg, 1, &data_info)) {
      return out_info;
    }
    info = data_info;
    info.slot_disp = INT16_MIN;
  }
  {
    const char *owner_type_name = amiga_value_provenance_owner_type_name_local(&info) != NULL
      ? amiga_value_provenance_owner_type_name_local(&info)
      : amiga_value_provenance_type_name_local(&info);
    const char *field_symbol_name = amiga_value_provenance_field_symbol_name_local(&info);
    char slot_name[64];
    out_info.kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL;
    out_info.note_kind = M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD;
    out_info.note_disp = info.slot_disp;
    out_info.note_field_disp = info.field_disp != INT16_MIN ? info.field_disp : 4;
    if (owner_type_name != NULL) {
      snprintf(out_info.note_base_name, sizeof(out_info.note_base_name), "%s", owner_type_name);
    } else if (info.slot_disp != INT16_MIN) {
      format_amiga_slot_struct_type_name(slot_name, sizeof(slot_name), info.slot_disp);
      snprintf(out_info.note_base_name, sizeof(out_info.note_base_name), "%s", slot_name);
    } else return platform_resolved_indirect_info_none();
    if (field_symbol_name != NULL && field_symbol_name[0] != '\0') {
      snprintf(out_info.note_symbol_name, sizeof(out_info.note_symbol_name), "%s", field_symbol_name);
    } else {
      populate_amiga_callback_field_note_symbol(&out_info);
    }
  }
  return out_info;
}

PlatformResolvedIndirectInfo resolve_amiga_local_wrapper_dispatch_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  PlatformResolvedIndirectInfo info;
  const M68kRecoveredPlatformCallIR *recovered;
  const M68kSection *section = section_analysis_context_section(ctx);
  size_t entry_block_index;
  size_t pending[32];
  size_t visited[32];
  size_t pending_count = 0U;
  size_t visit_count = 0U;
  size_t target_section_index;
  uint32_t target_offset;
  int32_t lvo;
  const AmigaOsLibraryVectorInfo *entry;
  info = platform_resolved_indirect_info_none();
  recovered = find_recovered_platform_call(section_analysis, offset,
    PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH);
  if (recovered != NULL && recovered->note_kind == M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL) {
    load_recovered_platform_call_info(recovered, &info);
    return info;
  }
  if (ctx == NULL || section_analysis_context_object(ctx) == NULL || section_analysis == NULL)
    return info;
  if (section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return info;
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return info;
  if (section == NULL) return info;
  if (!instruction_is_call_transfer(instruction)) return info;
  if (!platform_resolve_direct_target_with_fixup(ctx, instruction, offset, &target_section_index, &target_offset))
    return info;
  {
    PlatformLocalStackWrapperSignature signature;
    if (resolve_amiga_local_wrapper_signature(ctx, section_analysis, target_section_index, target_offset, &signature) &&
        signature.call_entry != NULL) {
      const AmigaOsLibraryVectorInfo *signature_entry = (const AmigaOsLibraryVectorInfo *)signature.call_entry;
      const char *base_name = amiga_os_name(M68K_PLATFORM_NAME_BASE, signature_entry->base_id);
      const char *symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, signature_entry->lvo_symbol_id);
      info.kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH;
      info.note_kind = M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL;
      snprintf(info.note_base_name, sizeof(info.note_base_name), "%s", base_name != NULL ? base_name : "");
      snprintf(info.note_symbol_name, sizeof(info.note_symbol_name), "%s", symbol_name != NULL ? symbol_name : "");
      populate_amiga_call_version_info(signature_entry, &info);
      return info;
    }
  }
  if (target_section_index != section_analysis_context_section_index(ctx)) return info;
  entry_block_index = section_analysis_find_block_index_containing(section_analysis, target_offset);
  if (entry_block_index == SIZE_MAX) return info;
  pending[pending_count++] = entry_block_index;
  while (pending_count != 0U && visit_count < (sizeof(visited) / sizeof(visited[0]))) {
    size_t block_index = pending[--pending_count];
    const M68kCfgBlockIR *block;
    uint32_t cursor;
    size_t seen_index;
    int seen = 0;
    size_t edge_index;
    for (seen_index = 0U; seen_index < visit_count; ++seen_index) {
      if (visited[seen_index] == block_index) {
        seen = 1;
        break;
      }
    }
    if (seen || block_index >= section_analysis->block_count) continue;
    visited[visit_count++] = block_index;
    block = &section_analysis->blocks[block_index];
    cursor = block->start_offset < target_offset ? target_offset : block->start_offset;
    while (cursor < block->end_offset && cursor < section->data_size) {
      SectionDecodeResult decode;
      if (!section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U) break;
      if (resolve_amiga_indexed_library_dispatch_info(ctx, section_analysis, cursor, &decode.instruction).kind !=
          PLATFORM_RESOLVED_INDIRECT_NONE)
        goto found_wrapper_dispatch;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    for (edge_index = block->edge_start;
         edge_index < block->edge_start + block->edge_count && pending_count < (sizeof(pending) / sizeof(pending[0]));
         ++edge_index) {
      const M68kCfgEdgeIR *edge = &section_analysis->edges[edge_index];
      if (edge->kind == M68K_CFG_EDGE_CALL || edge->kind == M68K_CFG_EDGE_RETURN) continue;
      if (edge->target_block_index == SIZE_MAX) continue;
      pending[pending_count++] = edge->target_block_index;
    }
  }
  return info;
found_wrapper_dispatch:
  if (!resolve_local_data_reg_immediate_seed(ctx, section_analysis, offset, 0U, &lvo)) return info;
  entry = amiga_os_find_library_vector("DOSBase", (int16_t)lvo);
  if (entry == NULL) return info;
  {
    const char *symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, entry->lvo_symbol_id);
    info.kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH;
    info.note_kind = M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL;
    snprintf(info.note_base_name, sizeof(info.note_base_name), "%s", "DOSBase");
    snprintf(info.note_symbol_name, sizeof(info.note_symbol_name), "%s", symbol_name != NULL ? symbol_name : "");
    populate_amiga_call_version_info(entry, &info);
  }
  return info;
}PlatformResolvedIndirectInfo platform_amiga_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  PlatformResolvedIndirectInfo info;
  AmigaSymbolProfileCounters *symbol_profile = amiga_symbol_profile_counters();
  clock_t total_start = 0;
  if (symbol_profile != NULL) {
    total_start = clock();
    ++symbol_profile->indirect_control_calls;
  }
  if (symbol_profile != NULL) {
    clock_t profile_start = clock();
    info = resolve_amiga_library_vector_info(ctx, section_analysis, offset, instruction);
    symbol_profile->indirect_library_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
    ++symbol_profile->indirect_library_calls;
    if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE) ++symbol_profile->indirect_library_hits;
  } else {
  info = resolve_amiga_library_vector_info(ctx, section_analysis, offset, instruction);
  }
  if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE) goto done;
  if (symbol_profile != NULL) {
    clock_t profile_start = clock();
    info = resolve_amiga_indexed_library_dispatch_info(ctx, section_analysis, offset, instruction);
    symbol_profile->indirect_indexed_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
    ++symbol_profile->indirect_indexed_calls;
    if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE) ++symbol_profile->indirect_indexed_hits;
  } else {
  info = resolve_amiga_indexed_library_dispatch_info(ctx, section_analysis, offset, instruction);
  }
  if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE) goto done;
  if (symbol_profile != NULL) {
    clock_t profile_start = clock();
    info = resolve_amiga_callback_field_info(ctx, section_analysis, offset, instruction);
    symbol_profile->indirect_callback_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
    ++symbol_profile->indirect_callback_calls;
    if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE) ++symbol_profile->indirect_callback_hits;
  } else {
  info = resolve_amiga_callback_field_info(ctx, section_analysis, offset, instruction);
  }
done:
  if (symbol_profile != NULL) {
    symbol_profile->indirect_control_seconds += amiga_profile_elapsed_seconds(total_start, clock());
    if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE) ++symbol_profile->indirect_control_hits;
  }
  if (info.kind != PLATFORM_RESOLVED_INDIRECT_NONE) return info;
  return platform_resolved_indirect_info_none();
}PlatformResolvedIndirectInfo platform_amiga_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction) {
  return resolve_amiga_local_wrapper_dispatch_info(ctx, section_analysis, offset, instruction);
}

static int format_amiga_call_input_note(uint16_t stack_offset, const AmigaOsCallInputInfo *input_info,
    char *buf, size_t buf_size) {
  const char *symbol_name;
  const char *type_name;
  const char *semantic_kind;
  const char *value_domain_name;
  size_t used;
  if (buf == NULL || buf_size == 0U || input_info == NULL || stack_offset == 0U) return 0;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input_info->input_id);
  type_name = amiga_type_or_struct_name_local(input_info->type_id, input_info->struct_id);
  semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, input_info->semantic_kind_id);
  value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input_info->value_domain_id);
  snprintf(buf, buf_size, "KNOWN: arg +%u", (unsigned)stack_offset);
  used = strlen(buf);
  if (symbol_name != NULL && symbol_name[0] != '\0' && used + strlen(symbol_name) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", symbol_name);
    used = strlen(buf);
  }
  if (type_name != NULL && type_name[0] != '\0' && used + strlen(type_name) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", type_name);
    used = strlen(buf);
  }
  if (semantic_kind != NULL && semantic_kind[0] != '\0' && used + strlen(semantic_kind) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", semantic_kind);
    used = strlen(buf);
  }
  if (value_domain_name != NULL && value_domain_name[0] != '\0' && used + strlen(value_domain_name) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", value_domain_name);
  }
  return 1;
}

int platform_amiga_format_instruction_comment(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    char *buf, size_t buf_size) {
  size_t push_operand_index = SIZE_MAX;
  const AmigaOsCallInputInfo *input_info = NULL;
  uint16_t stack_offset = 0U;
  if (buf != NULL && buf_size != 0U) buf[0] = '\0';
  if (buf == NULL || buf_size == 0U) return 0;
  if (!resolve_amiga_stack_push_wrapper_input(ctx, section_analysis, offset, instruction, &push_operand_index,
      &input_info, &stack_offset) ||
      push_operand_index >= instruction->operand_count || input_info == NULL) {
    return 0;
  }
  return format_amiga_call_input_note(stack_offset, input_info, buf, buf_size);
}

static int resolve_amiga_address_reg_info_cached_local(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedAddressRegInfo *cached_values, uint32_t *cache_known, uint32_t *cache_resolved,
    AmigaResolvedAddressRegInfo *out_info) {
  if (out_info != NULL) init_amiga_value_provenance(out_info);
  if (cached_values == NULL || cache_known == NULL || cache_resolved == NULL || out_info == NULL || reg >= 8U)
    return 0;
  if (!m68k_bitset_u32_has(*cache_known, reg)) {
    if (resolve_amiga_address_reg_info(ctx, section_analysis, offset, reg, include_section_slots,
        &cached_values[reg]) != 0) {
      m68k_bitset_u32_set(cache_resolved, reg);
    }
    m68k_bitset_u32_set(cache_known, reg);
  }
  if (!m68k_bitset_u32_has(*cache_resolved, reg)) return 0;
  *out_info = cached_values[reg];
  return 1;
}

static int resolve_amiga_data_reg_info_cached_local(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t reg, int include_section_slots,
    AmigaResolvedDataRegInfo *cached_values, uint32_t *cache_known, uint32_t *cache_resolved,
    AmigaResolvedDataRegInfo *out_info) {
  if (out_info != NULL) init_amiga_value_provenance(out_info);
  if (cached_values == NULL || cache_known == NULL || cache_resolved == NULL || out_info == NULL || reg >= 8U)
    return 0;
  if (!m68k_bitset_u32_has(*cache_known, reg)) {
    if (resolve_amiga_data_reg_info(ctx, section_analysis, offset, reg, include_section_slots,
        &cached_values[reg]) != 0) {
      m68k_bitset_u32_set(cache_resolved, reg);
    }
    m68k_bitset_u32_set(cache_known, reg);
  }
  if (!m68k_bitset_u32_has(*cache_resolved, reg)) return 0;
  *out_info = cached_values[reg];
  return 1;
}

int platform_amiga_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction) {
  const M68kRecoveredPlatformCallIR *recovered;
  const M68kRecoveredPlatformEffectIR *typed_reg_effect;
  M68kOperandIR *imm_operand;
  size_t operand_index;
  const char *field_domain_name = NULL;
  int has_unnamed_immediate;
  int annotated = 0;
  AmigaResolvedAddressRegInfo cached_addr_reg_info[8];
  uint32_t cached_addr_reg_known = 0U;
  uint32_t cached_addr_reg_resolved = 0U;
  AmigaResolvedDataRegInfo cached_data_reg_info[8];
  uint32_t cached_data_reg_known = 0U;
  uint32_t cached_data_reg_resolved = 0U;
  AmigaSymbolProfileCounters *symbol_profile = NULL;
  if (ctx == NULL || section_analysis == NULL) return 0;
  if (section_analysis_context_object(ctx) == NULL ||
      section_analysis_context_object(ctx)->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  if (section_analysis_context_object(ctx)->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) return 0;
  symbol_profile = amiga_symbol_profile_counters();
  has_unnamed_immediate = instruction_has_unnamed_immediate_operand_local(instruction);
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    uint8_t base_reg;
    int16_t displacement;
    AmigaResolvedAddressRegInfo info;
    char field_symbol_name[64];
    M68kOperandIR *operand = &instruction->operands[operand_index];
    const char *container_type;
    if (!operand_is_indirect_or_disp_an(operand, &base_reg, &displacement)) continue;
    if (operand->symbol_ref.has_name != 0U && operand->symbol_ref.name_is_generated == 0U) continue;
    container_type = NULL;
    if (base_reg != 6U) {
      uint8_t dest_reg;
      const M68kOperandIR *source = NULL;
      int treat_as_value = 1;
      int has_app_slot;
      if (symbol_profile != NULL) {
        clock_t profile_start = clock();
        has_app_slot = has_recovered_amiga_app_slot_displacement(section_analysis, displacement);
        symbol_profile->app_slot_lookup_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
        ++symbol_profile->app_slot_lookup_calls;
        if (has_app_slot) ++symbol_profile->app_slot_lookup_hits;
      } else {
        has_app_slot = has_recovered_amiga_app_slot_displacement(section_analysis, displacement);
      }
      if (!has_app_slot) {
        goto try_struct_field;
      }
      if (operand_index == 0U && instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA) {
        treat_as_value = 0;
      } else if (operand_index == 0U && instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA) {
        treat_as_value = 0;
      } else if (instruction_is_address_move(instruction, &dest_reg, &source) && source == operand) {
        treat_as_value = 0;
      }
      if ((treat_as_value
            ? resolve_amiga_app_slot_value_symbol_ref(ctx, section_analysis, displacement, &operand->symbol_ref)
            : resolve_amiga_app_slot_symbol_ref(ctx, section_analysis, displacement, &operand->symbol_ref))) {
        operand->symbol_ref.name_is_generated = 0U;
        operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
        operand->symbol_ref.addend = 0;
        annotated = 1;
        continue;
      }
    }
try_struct_field:
    container_type = NULL;
    {
      int resolved;
      if (symbol_profile != NULL) {
        clock_t profile_start = clock();
        resolved = resolve_amiga_address_reg_info_cached_local(ctx, section_analysis, offset, base_reg, 1,
          cached_addr_reg_info, &cached_addr_reg_known, &cached_addr_reg_resolved, &info);
        symbol_profile->operand_addr_resolve_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
        ++symbol_profile->operand_addr_resolve_calls;
        if (resolved) ++symbol_profile->operand_addr_resolve_hits;
      } else {
        resolved = resolve_amiga_address_reg_info_cached_local(ctx, section_analysis, offset, base_reg, 1,
          cached_addr_reg_info, &cached_addr_reg_known, &cached_addr_reg_resolved, &info);
      }
      if (resolved) {
      container_type = amiga_value_provenance_type_name_local(&info) != NULL
        ? amiga_value_provenance_type_name_local(&info)
        : amiga_value_provenance_owner_type_name_local(&info);
      if (!resolve_amiga_struct_field_symbol_name(container_type, displacement, field_symbol_name, sizeof(field_symbol_name)))
        container_type = NULL;
      }
    }
    if (container_type == NULL &&
        !resolve_amiga_policy_seed_struct_field_symbol_name(ctx, offset, M68K_ANALYSIS_REGISTER_ADDRESS, base_reg,
          displacement, field_symbol_name, sizeof(field_symbol_name), &container_type)) {
      continue;
    }
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    operand->symbol_ref.addend = 0;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", field_symbol_name);
    annotated = 1;
    if (field_domain_name == NULL) {
      field_domain_name = amiga_os_find_struct_field_value_domain(container_type, field_symbol_name, NULL);
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      instruction->operand_count == 2U &&
      instruction->operands[0].kind == M68K_ASM_OPERAND_IMM &&
      operand_is_data_reg_direct(&instruction->operands[1], 0U)) {
    const char *note_symbol_name;
    recovered = find_any_recovered_platform_call(section_analysis, offset);
    note_symbol_name = recovered != NULL
      ? m68k_platform_name_ref_resolve_text_or_fallback(&recovered->note_symbol_ref, recovered->note_symbol_name)
      : NULL;
    if (recovered != NULL && recovered->kind == 0U &&
        recovered->note_kind == M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL &&
        note_symbol_name != NULL && note_symbol_name[0] != '\0') {
      imm_operand = &instruction->operands[0];
      imm_operand->symbol_ref.has_name = 1U;
      imm_operand->symbol_ref.name_is_generated = 0U;
      imm_operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      imm_operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
      imm_operand->symbol_ref.addend = 0;
      snprintf(imm_operand->symbol_ref.name, sizeof(imm_operand->symbol_ref.name), "%s", note_symbol_name);
      return 1;
    }
  }
  if (field_domain_name != NULL) {
    char domain_symbol[128];
    for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
      int32_t value;
      M68kOperandIR *operand = &instruction->operands[operand_index];
      if (operand->symbol_ref.has_name || !operand_is_immediate_source_local(operand)) continue;
      value = (int32_t)operand->value.value;
      if (!format_amiga_value_domain_symbolic_value(field_domain_name, value, domain_symbol, sizeof(domain_symbol)))
        continue;
      operand->symbol_ref.has_name = 1U;
      operand->symbol_ref.name_is_generated = 0U;
      operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
      operand->symbol_ref.addend = 0;
      snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", domain_symbol);
      annotated = 1;
    }
  }
  {
    const AmigaOsCallInputInfo *input_info = NULL;
    uint8_t reg_kind;
    uint8_t reg_index;
    int32_t value;
    char domain_symbol[128];
    if (instruction_is_immediate_seed_to_reg_local(instruction, &reg_kind, &reg_index, &value)) {
      const char *typed_reg_domain_name = NULL;
      imm_operand = &instruction->operands[0];
      if (symbol_profile != NULL) {
        clock_t profile_start = clock();
        typed_reg_effect = find_recovered_typed_reg_effect_for_reg(section_analysis, offset, reg_kind, reg_index);
        symbol_profile->typed_effect_lookup_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
        ++symbol_profile->typed_effect_lookup_calls;
        if (typed_reg_effect != NULL) ++symbol_profile->typed_effect_lookup_hits;
      } else {
        typed_reg_effect = find_recovered_typed_reg_effect_for_reg(section_analysis, offset, reg_kind, reg_index);
      }
      if (typed_reg_effect != NULL) {
        typed_reg_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN,
          amiga_typed_payload_value_domain_id_local(&typed_reg_effect->payload.typed));
      }
      if (typed_reg_effect != NULL &&
          typed_reg_domain_name != NULL &&
          typed_reg_effect->payload.typed.has_constant_value &&
          typed_reg_effect->payload.typed.constant_value == value &&
          format_amiga_value_domain_symbolic_value(typed_reg_domain_name, value,
            domain_symbol, sizeof(domain_symbol))) {
        if (!imm_operand->symbol_ref.has_name) {
          imm_operand->symbol_ref.has_name = 1U;
          imm_operand->symbol_ref.name_is_generated = 0U;
          imm_operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
          imm_operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
          imm_operand->symbol_ref.addend = 0;
          snprintf(imm_operand->symbol_ref.name, sizeof(imm_operand->symbol_ref.name), "%s", domain_symbol);
          annotated = 1;
        }
      } else {
        int next_call_resolved;
        if (symbol_profile != NULL) {
          clock_t profile_start = clock();
          next_call_resolved = resolve_next_amiga_call_input_for_reg(ctx, section_analysis, offset, instruction,
            reg_kind, reg_index, NULL, &input_info);
          symbol_profile->next_call_input_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
          ++symbol_profile->next_call_input_calls;
          if (next_call_resolved) ++symbol_profile->next_call_input_hits;
        } else {
          next_call_resolved = resolve_next_amiga_call_input_for_reg(ctx, section_analysis, offset, instruction,
            reg_kind, reg_index, NULL, &input_info);
        }
        if (next_call_resolved &&
          input_info != NULL &&
          amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input_info->value_domain_id) != NULL &&
          format_amiga_value_domain_symbolic_value(
            amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input_info->value_domain_id), value, domain_symbol,
            sizeof(domain_symbol))) {
        if (!imm_operand->symbol_ref.has_name) {
          imm_operand->symbol_ref.has_name = 1U;
          imm_operand->symbol_ref.name_is_generated = 0U;
          imm_operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
          imm_operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
          imm_operand->symbol_ref.addend = 0;
          snprintf(imm_operand->symbol_ref.name, sizeof(imm_operand->symbol_ref.name), "%s", domain_symbol);
          annotated = 1;
        }
      }
      }
    }
  }
  {
    size_t push_operand_index = SIZE_MAX;
    const AmigaOsCallInputInfo *input_info = NULL;
    const char *value_domain_name;
    int32_t value;
    char domain_symbol[128];
    int stack_resolved;
    if (symbol_profile != NULL) {
      clock_t profile_start = clock();
      stack_resolved = resolve_amiga_stack_push_wrapper_input(ctx, section_analysis, offset, instruction,
        &push_operand_index, &input_info, NULL);
      symbol_profile->stack_push_input_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
      ++symbol_profile->stack_push_input_calls;
      if (stack_resolved) ++symbol_profile->stack_push_input_hits;
    } else {
      stack_resolved = resolve_amiga_stack_push_wrapper_input(ctx, section_analysis, offset, instruction,
        &push_operand_index, &input_info, NULL);
    }
    if (stack_resolved &&
        push_operand_index < instruction->operand_count && input_info != NULL &&
        (value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input_info->value_domain_id)) != NULL &&
        operand_raw_constant_value_local(&instruction->operands[push_operand_index], &value) &&
        format_amiga_value_domain_symbolic_value(value_domain_name, value, domain_symbol, sizeof(domain_symbol))) {
      M68kOperandIR *mutable_operand = &instruction->operands[push_operand_index];
      if (!mutable_operand->symbol_ref.has_name) {
        mutable_operand->symbol_ref.has_name = 1U;
        mutable_operand->symbol_ref.name_is_generated = 0U;
        mutable_operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
        mutable_operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
        mutable_operand->symbol_ref.addend = 0;
        snprintf(mutable_operand->symbol_ref.name, sizeof(mutable_operand->symbol_ref.name), "%s", domain_symbol);
        annotated = 1;
      }
    }
  }
  if (field_domain_name == NULL && has_unnamed_immediate) {
    for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
      uint8_t reg_index;
      AmigaResolvedDataRegInfo data_info;
      AmigaResolvedAddressRegInfo addr_info;
      const M68kOperandIR *operand = &instruction->operands[operand_index];
      if (operand_data_reg_index_local(operand, &reg_index)) {
        int resolved;
        if (symbol_profile != NULL) {
          clock_t profile_start = clock();
          resolved = resolve_amiga_data_reg_info_cached_local(ctx, section_analysis, offset, reg_index, 1,
            cached_data_reg_info, &cached_data_reg_known, &cached_data_reg_resolved, &data_info);
          symbol_profile->unnamed_reg_resolve_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
          ++symbol_profile->unnamed_reg_resolve_calls;
          if (resolved) ++symbol_profile->unnamed_reg_resolve_hits;
        } else {
          resolved = resolve_amiga_data_reg_info_cached_local(ctx, section_analysis, offset, reg_index, 1,
            cached_data_reg_info, &cached_data_reg_known, &cached_data_reg_resolved, &data_info);
        }
        if (resolved && amiga_value_provenance_value_domain_name_local(&data_info) != NULL) {
          field_domain_name = amiga_value_provenance_value_domain_name_local(&data_info);
          break;
        }
      }
      if (operand_address_reg_index_local(operand, &reg_index)) {
        int resolved;
        if (symbol_profile != NULL) {
          clock_t profile_start = clock();
          resolved = resolve_amiga_address_reg_info_cached_local(ctx, section_analysis, offset, reg_index, 1,
            cached_addr_reg_info, &cached_addr_reg_known, &cached_addr_reg_resolved, &addr_info);
          symbol_profile->unnamed_reg_resolve_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
          ++symbol_profile->unnamed_reg_resolve_calls;
          if (resolved) ++symbol_profile->unnamed_reg_resolve_hits;
        } else {
          resolved = resolve_amiga_address_reg_info_cached_local(ctx, section_analysis, offset, reg_index, 1,
            cached_addr_reg_info, &cached_addr_reg_known, &cached_addr_reg_resolved, &addr_info);
        }
        if (resolved && amiga_value_provenance_value_domain_name_local(&addr_info) != NULL) {
          field_domain_name = amiga_value_provenance_value_domain_name_local(&addr_info);
          break;
        }
      }
    }
    if (field_domain_name != NULL) {
      char domain_symbol[128];
      for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
        int32_t value;
        M68kOperandIR *operand = &instruction->operands[operand_index];
        if (operand->symbol_ref.has_name || !operand_is_immediate_source_local(operand)) continue;
        value = (int32_t)operand->value.value;
        if (!format_amiga_value_domain_symbolic_value(field_domain_name, value, domain_symbol, sizeof(domain_symbol)))
          continue;
        operand->symbol_ref.has_name = 1U;
        operand->symbol_ref.name_is_generated = 0U;
        operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
        operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
        operand->symbol_ref.addend = 0;
        snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", domain_symbol);
        annotated = 1;
      }
    }
  }
  return annotated;
}

int platform_amiga_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref) {
  AmigaPlatformCache *cache;
  AmigaAppSlotSymbolCacheEntry *entry;
  AmigaSymbolProfileCounters *symbol_profile = amiga_symbol_profile_counters();
  clock_t profile_start = 0;
  int found = 0;
  int result;
  if (symbol_profile != NULL) {
    profile_start = clock();
    ++symbol_profile->app_base_symbol_calls;
  }
  if (out_symbol_ref != NULL) m68k_ir_symbol_ref_init(out_symbol_ref);
  cache = amiga_platform_cache_for_ctx(ctx);
  entry = amiga_app_slot_symbol_cache_find(cache, section_analysis, displacement, treat_as_value, &found);
  if (found && entry != NULL) {
    if (out_symbol_ref != NULL) *out_symbol_ref = entry->symbol_ref;
    if (symbol_profile != NULL) {
      symbol_profile->app_base_symbol_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
      if (entry->result) ++symbol_profile->app_base_symbol_hits;
    }
    return entry->result;
  }
  if (treat_as_value) result = resolve_amiga_app_slot_value_symbol_ref(ctx, section_analysis, displacement, out_symbol_ref);
  else result = resolve_amiga_app_slot_symbol_ref(ctx, section_analysis, displacement, out_symbol_ref);
  if (entry != NULL) {
    entry->valid = 1U;
    entry->section_analysis = section_analysis;
    entry->displacement = displacement;
    entry->treat_as_value = (uint8_t)(treat_as_value != 0);
    entry->result = result;
    if (out_symbol_ref != NULL) entry->symbol_ref = *out_symbol_ref;
    else m68k_ir_symbol_ref_init(&entry->symbol_ref);
  }
  if (symbol_profile != NULL) {
    symbol_profile->app_base_symbol_seconds += amiga_profile_elapsed_seconds(profile_start, clock());
    if (result) ++symbol_profile->app_base_symbol_hits;
  }
  return result;
}



