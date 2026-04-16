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
#include "m68k_simulator.h"
#include "m68k_source_ir_render.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "util_arena.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct SectionAnalysisContext SectionAnalysisContext;
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

typedef enum PlatformResolvedIndirectKind {
  PLATFORM_RESOLVED_INDIRECT_NONE = 0,
  PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL = 1,
  PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH = 2,
  PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL = 3
} PlatformResolvedIndirectKind;

typedef struct PlatformRegisterMatch {
  uint8_t ok;
  uint8_t reg;
} PlatformRegisterMatch;

typedef struct PlatformAddressExgInfo {
  uint8_t ok;
  uint8_t left_reg;
  uint8_t right_reg;
} PlatformAddressExgInfo;

int build_section_analysis(const M68kObject *object, size_t section_index, const M68kSection *section,
    Arena *scratch_arena,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings, M68kSectionAnalysisIR *out_analysis,
    M68kDiagSink diagnostics);
int build_section_ir(const M68kObject *object, const M68kSection *section, M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings, const M68kRenderPolicy *policy,
    M68kSectionIR *out_section_ir, M68kDiagSink diagnostics);
int finalize_section_analysis(const M68kSection *section, const M68kAnalysisPolicy *analysis_policy,
    M68kSectionAnalysisIR *section_analysis, M68kAnalysisFindings *out_findings);

int inspect_object_json(const M68kBackend *backend, const M68kObject *object, char **out_json);
int source_analysis_to_json(const M68kSourceAnalysisIR *source_analysis, char **out_json, M68kDiagSink diagnostics);
int populate_source_ir_from_object(const M68kBackend *backend, const M68kObject *object,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
    M68kDiagSink diagnostics);
int populate_source_ir_from_object_with_metrics(const M68kBackend *backend, const M68kObject *object,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
    PlatformFileRunMetrics *out_metrics, M68kDiagSink diagnostics);
int populate_source_analysis_from_object(const M68kObject *object, const M68kAnalysisPolicy *analysis_policy,
    M68kSourceAnalysisIR *out_source_analysis, M68kDiagSink diagnostics);

PlatformResolvedIndirectInfo platform_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
int platform_collect_recovered_platform_facts(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis);
PlatformResolvedIndirectInfo platform_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
int platform_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction);
int platform_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref);
uint8_t section_analysis_context_backend_kind(const SectionAnalysisContext *ctx);
const M68kObject *section_analysis_context_object(const SectionAnalysisContext *ctx);
const M68kSection *section_analysis_context_section(const SectionAnalysisContext *ctx);
int section_analysis_context_probe_decode(const SectionAnalysisContext *ctx, uint32_t offset,
    SectionDecodeResult *out_result);
size_t section_analysis_find_block_index_containing(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
const M68kRecoveredPlatformCallIR *find_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind);
const M68kRecoveredPlatformCallIR *find_any_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset);
const M68kRecoveredPlatformEffectIR *find_recovered_platform_effect(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind);
void load_recovered_platform_call_info(const M68kRecoveredPlatformCallIR *recovered,
    PlatformResolvedIndirectInfo *out_info);
void platform_resolved_indirect_info_init(PlatformResolvedIndirectInfo *info);
PlatformResolvedIndirectInfo platform_resolved_indirect_info_none(void);
uint32_t resolve_analysis_trace_start(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
const M68kSimFormMetadata *instruction_sim_metadata(const M68kInstructionIR *instruction);
int instruction_branch_target(const M68kInstructionIR *instruction, uint32_t offset, uint32_t *out_target);
int instruction_render_operand_target(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, uint32_t offset, uint32_t section_size, uint32_t *out_target);
int instruction_is_call_transfer(const M68kInstructionIR *instruction);
int instruction_stops_fallthrough(const M68kInstructionIR *instruction);
int instruction_target_operand_local(const M68kInstructionIR *instruction, const M68kOperandIR **out_operand);
int instruction_direct_target_local(const SectionAnalysisContext *ctx, const M68kInstructionIR *instruction,
    uint32_t offset, uint32_t *out_target);
int operand_is_absolute_short_value(const M68kOperandIR *operand, uint16_t value);
int operand_is_app_base_disp_ea(const M68kOperandIR *operand, uint8_t reg, int16_t *out_displacement);
int operand_is_data_reg_direct(const M68kOperandIR *operand, uint8_t reg);
int operand_is_indirect_an(const M68kOperandIR *operand, uint8_t *out_reg);
int operand_is_indirect_disp_an(const M68kOperandIR *operand, uint8_t *out_reg, int16_t *out_disp);
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
int collect_recovered_amiga_platform_facts(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis);
PlatformResolvedIndirectInfo platform_amiga_resolve_indirect_control(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
int platform_amiga_collect_recovered_platform_facts(const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *section_analysis);
PlatformResolvedIndirectInfo platform_amiga_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
int platform_amiga_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction);
int platform_amiga_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref);
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
int platform_atari_st_collect_recovered_platform_facts(const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *section_analysis);
PlatformResolvedIndirectInfo platform_atari_st_resolve_additional_indirect_note(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, const M68kInstructionIR *instruction);
int platform_atari_st_annotate_instruction_symbol_refs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset, M68kInstructionIR *instruction);
int platform_atari_st_resolve_app_base_slot_symbol_ref(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, int16_t displacement, int treat_as_value,
    M68kSymbolRefIR *out_symbol_ref);

#endif
