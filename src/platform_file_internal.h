#ifndef PLATFORM_FILE_INTERNAL_H
#define PLATFORM_FILE_INTERNAL_H

#include "platform_file_lib.h"
#include "generated/amiga_os_runtime.h"
#include "generated/atari_st_os_runtime.h"
#include "json_builder.h"
#include "m68k_assembler.h"
#include "m68k_backend.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_object.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_render_plan.h"
#include "m68k_simulator.h"
#include "m68k_source_ir_render.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "util_arena.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct SectionDecodeCacheEntry {
  uint32_t instruction_index;
  uint32_t explicit_target;
  uint8_t state;
  uint8_t has_explicit_target;
  uint8_t is_call;
  uint8_t is_unconditional_transfer;
  uint8_t is_conditional_transfer;
  uint8_t stops_fallthrough;
} SectionDecodeCacheEntry;

typedef struct SectionDecodeCache {
  Arena *arena;
  SectionDecodeCacheEntry *entries;
  M68kInstructionIR *instructions;
  size_t entry_count;
  size_t instruction_count;
  size_t instruction_capacity;
} SectionDecodeCache;

typedef struct SectionAnalysisContext {
  const M68kObject *object;
  const M68kSection *section;
  size_t section_index;
  const M68kSectionAnalysisIR *prior_section_analyses;
  size_t prior_section_analysis_count;
  const M68kAnalysisPolicy *analysis_policy;
  Arena *arena;
  SectionDecodeCache decode_cache;
  void *platform_cache;
} SectionAnalysisContext;

typedef struct SectionDecodeResult {
  M68kInstructionIR instruction;
  uint32_t explicit_target;
  uint8_t has_explicit_target;
  uint8_t is_call;
  uint8_t is_unconditional_transfer;
  uint8_t is_conditional_transfer;
  uint8_t stops_fallthrough;
} SectionDecodeResult;
typedef struct AmigaBaseSlotTag {
  int16_t displacement;
  uint16_t base_id;
} AmigaBaseSlotTag;

typedef struct PlatformResolvedIndirectInfo {
  uint8_t kind;
  uint8_t has_symbol_name;
  uint8_t note_kind;
  uint8_t note_reg;
  uint8_t note_stack_cleanup_known;
  uint8_t note_return_kind;
  int16_t note_disp;
  int16_t note_field_disp;
  uint16_t note_stack_cleanup_bytes;
  char symbol_name[64];
  /* Generic note context: library base, owner type, or similar note subject. */
  char note_base_name[64];
  char note_symbol_name[64];
  char available_since[16];
  char fd_version[16];
} PlatformResolvedIndirectInfo;

typedef struct PlatformRegisterMatch {
  uint8_t ok;
  uint8_t reg;
} PlatformRegisterMatch;

typedef struct PlatformAddressExgInfo {
  uint8_t ok;
  uint8_t left_reg;
  uint8_t right_reg;
} PlatformAddressExgInfo;

#define PLATFORM_LOCAL_STACK_WRAPPER_ARG_MAP_CAPACITY 16U

typedef struct PlatformLocalStackWrapperArgMapEntry {
  uint8_t reg_kind;
  uint8_t reg_index;
  uint16_t caller_stack_offset;
} PlatformLocalStackWrapperArgMapEntry;

typedef struct PlatformLocalStackWrapperSignature {
  const void *call_entry;
  PlatformLocalStackWrapperArgMapEntry args[PLATFORM_LOCAL_STACK_WRAPPER_ARG_MAP_CAPACITY];
  size_t arg_count;
} PlatformLocalStackWrapperSignature;

typedef uint16_t (*PlatformStackWrapperLookupBaseSlotFn)(void *user_ctx, const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement);
typedef uint16_t (*PlatformStackWrapperLookupOperandBaseFn)(void *user_ctx, const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    uint8_t operand_index);
typedef const void *(*PlatformStackWrapperResolveCallFn)(void *user_ctx, const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    const uint16_t addr_reg_base_ids[8]);

int section_analysis_context_init(SectionAnalysisContext *ctx, const M68kObject *object, size_t section_index,
    const M68kSection *section, const M68kSectionAnalysisIR *prior_section_analyses,
    size_t prior_section_analysis_count, const M68kAnalysisPolicy *analysis_policy, Arena *arena);
int inspect_object_json(const M68kBackend *backend, const M68kObject *object, char **out_json);
int object_target_metadata_json(const M68kBackend *backend, const M68kObject *object, char **out_json);
int source_analysis_to_json(const M68kSourceAnalysisIR *source_analysis, char **out_json, M68kDiagSink diagnostics);
int source_file_listing_rows_from_render_plan_to_json(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    char **out_json, M68kDiagSink diagnostics);
int source_file_listing_window_from_render_plan_to_json(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    size_t start, size_t count, char **out_json, M68kDiagSink diagnostics);
int source_file_listing_window_from_render_plan_with_total_to_json(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    size_t total_rows, size_t start, size_t count, char **out_json, M68kDiagSink diagnostics);
int source_file_listing_total_rows_from_render_plan(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    size_t *out_total_rows, M68kDiagSink diagnostics);
int source_file_listing_addr_window_from_render_plan_to_json(const M68kSourceFileIR *source_file,
  const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
  const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
  int has_addr, uint32_t addr, size_t before, size_t after, char **out_json, M68kDiagSink diagnostics);
int source_file_listing_navigation_from_render_plan_to_json(const M68kSourceFileIR *source_file,
  const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
  const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
  char **out_json, M68kDiagSink diagnostics);
int source_file_basic_listing_rows_to_json(const M68kSourceFileIR *source_file,
    const M68kAnalysisPolicy *analysis_policy, char **out_json, M68kDiagSink diagnostics);
int platform_type_catalog_to_json(const char *backend_name, char **out_json, M68kDiagSink diagnostics);
int platform_naming_catalog_to_json(const char *backend_name, char **out_json, M68kDiagSink diagnostics);
int platform_os_metadata_catalog_to_json(const char *backend_name, char **out_json, M68kDiagSink diagnostics);
int platform_api_input_struct_to_json(const char *backend_name, const char *library_name, const char *function_name,
    const char *input_name, const char *struct_name, char **out_json, M68kDiagSink diagnostics);
PlatformResolvedIndirectInfo platform_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
PlatformResolvedIndirectInfo platform_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
int platform_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction);
int platform_resolve_inferred_label(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, char *buf, size_t buf_size);
int platform_format_instruction_comment(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    char *buf, size_t buf_size);
int platform_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref);
int platform_format_global_base_slot_label(uint8_t backend_kind, size_t section_index, char width_suffix,
    const char *base_name, char *buf, size_t buf_size);
uint8_t section_analysis_context_backend_kind(const SectionAnalysisContext *ctx);
const M68kObject *section_analysis_context_object(const SectionAnalysisContext *ctx);
const M68kSection *section_analysis_context_section(const SectionAnalysisContext *ctx);
size_t section_analysis_context_section_index(const SectionAnalysisContext *ctx);
const M68kSectionAnalysisIR *section_analysis_context_prior_section_analysis(const SectionAnalysisContext *ctx,
    size_t section_index);
const M68kAnalysisPolicy *section_analysis_context_policy(const SectionAnalysisContext *ctx);
Arena *section_analysis_context_arena(const SectionAnalysisContext *ctx);
void *section_analysis_context_platform_cache(const SectionAnalysisContext *ctx);
void section_analysis_context_set_platform_cache(const SectionAnalysisContext *ctx, void *platform_cache);
int section_analysis_context_probe_decode(const SectionAnalysisContext *ctx, uint32_t offset,
    SectionDecodeResult *out_result);
size_t section_analysis_find_block_index_containing(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
const M68kRecoveredPlatformCallIR *find_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind);
const M68kRecoveredPlatformCallIR *find_any_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset);
void load_recovered_platform_call_info(const M68kRecoveredPlatformCallIR *recovered,
    PlatformResolvedIndirectInfo *out_info);
PlatformResolvedIndirectInfo platform_resolved_indirect_info_none(void);
uint32_t resolve_analysis_trace_start(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
const M68kSimFormMetadata *instruction_sim_metadata(const M68kInstructionIR *instruction);
int instruction_render_operand_target(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, uint32_t offset, uint32_t section_size, uint32_t *out_target);
int instruction_operand_absolute_target_ref(const SectionAnalysisContext *ctx, const M68kInstructionIR *instruction,
    size_t operand_index, uint32_t instruction_offset, size_t *out_section_index, uint32_t *out_target_offset);
int instruction_is_call_transfer(const M68kInstructionIR *instruction);
int instruction_stops_fallthrough(const M68kInstructionIR *instruction);
int instruction_target_operand_local(const M68kInstructionIR *instruction, const M68kOperandIR **out_operand);
int platform_resolve_direct_target_with_fixup(const SectionAnalysisContext *ctx,
    const M68kInstructionIR *instruction, uint32_t offset, size_t *out_section_index, uint32_t *out_target);
int operand_is_absolute_value(const M68kOperandIR *operand, uint32_t value);
int operand_raw_constant_value_local(const M68kOperandIR *operand, int32_t *out_value);
int operand_is_app_base_disp_ea(const M68kOperandIR *operand, uint8_t reg, int16_t *out_displacement);
int operand_is_data_reg_direct(const M68kOperandIR *operand, uint8_t reg);
int operand_is_indirect_an(const M68kOperandIR *operand, uint8_t *out_reg);
int operand_is_indirect_or_disp_an(const M68kOperandIR *operand, uint8_t *out_reg, int16_t *out_disp);
int operand_is_brief_indexed_an(const M68kOperandIR *operand, uint8_t *out_base_reg,
    uint8_t *out_index_is_address, uint8_t *out_index_reg, int32_t *out_disp);
int instruction_is_address_move(const M68kInstructionIR *instruction, uint8_t *out_dest_reg,
    const M68kOperandIR **out_source);
int instruction_is_data_move(const M68kInstructionIR *instruction, uint8_t *out_dest_reg,
    const M68kOperandIR **out_source);
int instruction_is_register_to_app_slot_store(const M68kInstructionIR *instruction, uint8_t *out_source_kind,
    uint8_t *out_source_reg, int16_t *out_displacement);
int instruction_is_app_slot_load(const M68kInstructionIR *instruction, uint8_t *out_dest_kind,
    uint8_t *out_dest_reg, int16_t *out_displacement);
PlatformRegisterMatch instruction_push_address_reg_to_stack(const M68kInstructionIR *instruction);
PlatformRegisterMatch instruction_pop_address_reg_from_stack(const M68kInstructionIR *instruction);
PlatformAddressExgInfo instruction_address_exg(const M68kInstructionIR *instruction);
int instruction_pushes_long_stack_arg_local(const M68kInstructionIR *instruction, const M68kOperandIR **out_operand);
int platform_analyze_local_stack_wrapper_signature(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t target_offset, uint16_t initial_a6_base_id,
    PlatformStackWrapperLookupBaseSlotFn lookup_base_slot, PlatformStackWrapperLookupOperandBaseFn lookup_operand_base,
    PlatformStackWrapperResolveCallFn resolve_call, void *user_ctx,
    PlatformLocalStackWrapperSignature *out_signature);
int platform_analyze_local_stack_wrapper_signature_at(const SectionAnalysisContext *ctx,
    size_t target_section_index, uint32_t target_offset, uint16_t initial_a6_base_id,
    PlatformStackWrapperLookupBaseSlotFn lookup_base_slot, PlatformStackWrapperLookupOperandBaseFn lookup_operand_base,
    PlatformStackWrapperResolveCallFn resolve_call, void *user_ctx,
    PlatformLocalStackWrapperSignature *out_signature);
int instruction_writes_address_reg_approx(const M68kInstructionIR *instruction, uint8_t reg);
int instruction_writes_data_reg_approx(const M68kInstructionIR *instruction, uint8_t reg);
extern const char *const AMIGA_APP_BASE_TAG;

PlatformResolvedIndirectInfo resolve_amiga_library_vector_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
PlatformResolvedIndirectInfo resolve_amiga_indexed_library_dispatch_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
PlatformResolvedIndirectInfo resolve_amiga_callback_field_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
PlatformResolvedIndirectInfo resolve_amiga_local_wrapper_dispatch_info(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
PlatformResolvedIndirectInfo platform_amiga_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
PlatformResolvedIndirectInfo platform_amiga_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
int platform_amiga_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction);
int platform_amiga_resolve_inferred_label(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, char *buf, size_t buf_size);
int platform_amiga_format_instruction_comment(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction,
    char *buf, size_t buf_size);
int platform_amiga_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref);
int platform_amiga_format_global_base_slot_label(size_t section_index, char width_suffix, const char *base_name,
    char *buf, size_t buf_size);
const char *read_amiga_library_seed_name(const M68kSection *section, uint32_t target);
void set_amiga_base_slot_tag(AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement, const char *base_name);
const char *lookup_amiga_base_slot_tag(const AmigaBaseSlotTag *slots, size_t slot_count, int16_t displacement);
const char *lookup_recovered_platform_base_slot(const M68kSectionAnalysisIR *section_analysis, int16_t displacement);
const char *resolve_amiga_app_slot_base_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement);
int resolve_amiga_app_slot_symbol_name(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, char *buf, size_t buf_size);
int resolve_amiga_app_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, M68kSymbolRefIR *out_symbol_ref);
int resolve_amiga_app_slot_value_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, M68kSymbolRefIR *out_symbol_ref);
PlatformResolvedIndirectInfo platform_atari_st_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
PlatformResolvedIndirectInfo platform_atari_st_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
int platform_atari_st_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction);
int platform_atari_st_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref);

#endif
