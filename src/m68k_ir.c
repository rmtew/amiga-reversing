#include "m68k_ir.h"

#include "generated/amiga_os_runtime.h"
#include "generated/atari_st_os_runtime.h"
#include "m68k_assembler.h"
#include "m68k_fact_ir.h"
#include "platform_common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M68K_IR_SOURCE_FILE_ARENA_SIZE 16384U
#define M68K_IR_SOURCE_ANALYSIS_ARENA_SIZE 16384U
#define M68K_IR_RENDER_EVIDENCE_ARENA_SIZE 4096U

const M68kInstructionIR g_m68k_ir_instruction_none = {
  M68K_ASM_FORM_NONE,
  M68K_FORM_ID_NONE,
  M68K_ASM_MNEMONIC_NONE,
  M68K_ASM_CPU_ANY,
  0U,
  0U,
  '\0',
  0U,
  { { 0 } },
  0U
};

static void *arena_grow_array(Arena *arena, void *items, size_t count, size_t *capacity, size_t initial_capacity,
    size_t item_size) {
  size_t next_capacity;
  void *grown;
  if (count < *capacity) return items;
  next_capacity = (*capacity == 0U) ? initial_capacity : (*capacity * 2U);
  grown = arena_realloc_copy(arena, items, count * item_size, next_capacity * item_size);
  if (grown == NULL) return NULL;
  *capacity = next_capacity;
  return grown;
}

static int text_equal_nullable(const char *left, const char *right) {
  if (left == NULL || left[0] == '\0') left = NULL;
  if (right == NULL || right[0] == '\0') right = NULL;
  if (left == NULL || right == NULL) return left == right;
  return strcmp(left, right) == 0;
}

static int comma_token_list_contains(const char *list, const char *token) {
  size_t token_len;
  const char *cursor;
  if (list == NULL || token == NULL || token[0] == '\0') return 0;
  token_len = strlen(token);
  cursor = list;
  while (*cursor != '\0') {
    const char *end = strchr(cursor, ',');
    size_t part_len = end != NULL ? (size_t)(end - cursor) : strlen(cursor);
    if (part_len == token_len && strncmp(cursor, token, token_len) == 0) return 1;
    if (end == NULL) break;
    cursor = end + 1;
  }
  return 0;
}

static int expected_symbol_access_append_producer(M68kSectionAnalysisIR *section_analysis,
    M68kExpectedSymbolAccessIR *access, const char *producer) {
  size_t old_len;
  size_t producer_len;
  char *merged;
  if (section_analysis == NULL || access == NULL || section_analysis->arena == NULL ||
      producer == NULL || producer[0] == '\0') {
    return -1;
  }
  if (access->producer != NULL && comma_token_list_contains(access->producer, producer)) return 0;
  if ((access->producer == NULL || strcmp(access->producer, "unknown") == 0) &&
      strcmp(producer, "unknown") != 0) {
    access->producer = arena_strdup(section_analysis->arena, producer);
    return access->producer != NULL ? 0 : -1;
  }
  old_len = access->producer != NULL ? strlen(access->producer) : 0U;
  producer_len = strlen(producer);
  merged = (char *)arena_alloc(section_analysis->arena, old_len + producer_len + 2U);
  if (merged == NULL) return -1;
  if (old_len == 0U) {
    memcpy(merged, producer, producer_len + 1U);
  } else {
    memcpy(merged, access->producer, old_len);
    merged[old_len] = ',';
    memcpy(merged + old_len + 1U, producer, producer_len + 1U);
  }
  access->producer = merged;
  return 0;
}

const char *m68k_analysis_structured_data_role_name_for_flags(uint32_t semantic_role_flags) {
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_MACOS_SYMBOL_STRING) != 0U)
    return "macos_symbol_string";
  if ((semantic_role_flags &
      (M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING | M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING)) ==
      (M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING | M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING)) {
    return "length_prefixed_string";
  }
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST) != 0U) return "copper_list";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE) != 0U) return "palette";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) != 0U) return "pointer_table";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) != 0U) return "lookup_table";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) != 0U) return "bitmap";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE) != 0U) return "sound_sample";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING) != 0U) return "string";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_AUDIO_TABLE) != 0U) return "audio_table";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_DESTINATION) != 0U)
    return "blitter_destination";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_SOURCE) != 0U) return "blitter_source";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_DISK_BUFFER) != 0U) return "disk_buffer";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SPRITE) != 0U) return "sprite";
  if ((semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING_CONTROL_STREAM) != 0U)
    return "string_control_stream";
  return NULL;
}

const char *m68k_analysis_structured_data_source_pattern_name(uint8_t source_pattern_id) {
  switch (source_pattern_id) {
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_RELOCATION_POINTER_TABLE:
      return "relocation_pointer_table";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_WORD_DISPATCH:
      return "indexed_word_dispatch";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_POINTER_READ:
      return "indexed_local_pointer_read";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_SCALAR_READ:
      return "indexed_local_scalar_read";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POSTINCREMENT_READ_SEQUENCE:
      return "postincrement_read_sequence";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_READ:
      return "pc_relative_indexed_read";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_INDIRECT_DISPATCH:
      return "pc_relative_indexed_indirect_dispatch";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH:
      return "keyed_long_relative_dispatch";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MACOS_SYMBOL_RECORD:
      return "macos_symbol_record";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MULTILINE_TEXT:
      return "multiline_text";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_TERMINATED_TEXT:
      return "terminated_text";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_BOUNDED_TEXT:
      return "bounded_text";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_STRING_TABLE_SEQUENCE:
      return "string_table_sequence";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_CONTROL_STRING_STREAM:
      return "control_string_stream";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_API_STRING_POINTER:
      return "api_string_pointer";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POINTER_STRING_TABLE:
      return "pointer_string_table";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_WORD_OFFSET_STRING_TABLE:
      return "word_offset_string_table";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_API_TEXT_BUFFER:
      return "api_text_buffer";
    default:
      return NULL;
  }
}

uint8_t m68k_recovered_indirect_source_pattern_id(uint8_t shape) {
  switch (shape) {
    case M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_BRIEF:
    case M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_FULL:
    case M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_MEMIND:
      return M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_PC_INDEXED_INDIRECT;
    case M68K_RECOVERED_INDIRECT_SHAPE_INDEX_BRIEF:
    case M68K_RECOVERED_INDIRECT_SHAPE_INDEX_FULL:
    case M68K_RECOVERED_INDIRECT_SHAPE_INDEX_MEMIND:
      return M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_INDEXED_INDIRECT;
    case M68K_RECOVERED_INDIRECT_SHAPE_IND:
    case M68K_RECOVERED_INDIRECT_SHAPE_DISP:
      return M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_INDIRECT;
    default:
      return M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_UNKNOWN;
  }
}

const char *m68k_recovered_indirect_source_pattern_name(uint8_t source_pattern_id) {
  switch (source_pattern_id) {
    case M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_INDIRECT:
      return "indirect";
    case M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_INDEXED_INDIRECT:
      return "indexed_indirect";
    case M68K_RECOVERED_INDIRECT_SOURCE_PATTERN_PC_INDEXED_INDIRECT:
      return "pc_indexed_indirect";
    default:
      return NULL;
  }
}

const char *m68k_recovered_platform_transfer_source_kind_name(uint8_t source_kind) {
  switch (source_kind) {
    case M68K_RECOVERED_PLATFORM_TRANSFER_SOURCE_LOGICAL_DISK_OFFSET:
      return "logical_disk_offset";
    case M68K_RECOVERED_PLATFORM_TRANSFER_SOURCE_POST_READ_RUNTIME_COPY:
      return "post_read_runtime_copy";
    case M68K_RECOVERED_PLATFORM_TRANSFER_SOURCE_TARGET_LOADER_FILE:
      return "target_loader_file";
    default:
      return NULL;
  }
}

int m68k_asm_operand_absolute_value(uint8_t kind, const M68kAsmOperandValue *operand, uint32_t *out_value) {
  if (operand == NULL || out_value == NULL) return 0;
  if (kind == M68K_ASM_OPERAND_ABSL ||
      (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U &&
        (operand->ea_reg == 0U || operand->ea_reg == 1U))) {
    *out_value = operand->value;
    return 1;
  }
  return 0;
}

const char *m68k_analysis_table_kind_name(uint8_t table_kind_id) {
  switch (table_kind_id) {
    case M68K_ANALYSIS_TABLE_KIND_SCALAR:
      return "scalar";
    case M68K_ANALYSIS_TABLE_KIND_POINTER:
      return "pointer";
    case M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH:
      return "relative_code_dispatch";
    case M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH:
      return "absolute_code_dispatch";
    case M68K_ANALYSIS_TABLE_KIND_RELATIVE_DATA_LOOKUP:
      return "relative_data_lookup";
    default:
      return NULL;
  }
}

const char *m68k_analysis_table_base_expression_name(uint8_t base_expression_id) {
  switch (base_expression_id) {
    case M68K_ANALYSIS_TABLE_BASE_EXPRESSION_TABLE_LABEL:
      return "table_label";
    case M68K_ANALYSIS_TABLE_BASE_EXPRESSION_TARGET_LABEL:
      return "target_label";
    default:
      return NULL;
  }
}

const char *m68k_analysis_table_entry_count_proof_name(uint8_t proof_id) {
  switch (proof_id) {
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_STRUCTURED_RANGE:
      return "structured_range";
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_CONSUMER_STRUCTURAL_SCAN:
      return "consumer_structural_scan";
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_RELOCATION_RECORD:
      return "relocation_record";
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_PLATFORM_RECORD:
      return "platform_record";
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_MASK_DOMAIN:
      return "index_mask_domain";
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_COMPARE_DOMAIN:
      return "index_compare_domain";
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_LOOP_LIMIT:
      return "loop_limit";
    default:
      return NULL;
  }
}

const char *m68k_analysis_table_stop_reason_name(uint8_t stop_reason_id) {
  switch (stop_reason_id) {
    case M68K_ANALYSIS_TABLE_STOP_REASON_STRUCTURED_RANGE_END:
      return "structured_range_end";
    case M68K_ANALYSIS_TABLE_STOP_REASON_CONSUMER_STRUCTURAL_STOP:
      return "consumer_structural_stop";
    case M68K_ANALYSIS_TABLE_STOP_REASON_RELOCATION_RECORD_END:
      return "relocation_record_end";
    case M68K_ANALYSIS_TABLE_STOP_REASON_PLATFORM_RECORD_END:
      return "platform_record_end";
    case M68K_ANALYSIS_TABLE_STOP_REASON_INDEX_MASK_BOUND:
      return "index_mask_bound";
    case M68K_ANALYSIS_TABLE_STOP_REASON_INDEX_COMPARE_BRANCH_BOUND:
      return "index_compare_branch_bound";
    case M68K_ANALYSIS_TABLE_STOP_REASON_LOOP_LIMIT_BOUND:
      return "loop_limit_bound";
    default:
      return NULL;
  }
}

const char *m68k_table_entry_target_status_name(uint8_t status) {
  switch (status) {
    case M68K_TABLE_ENTRY_TARGET_STATUS_NUMERIC_EXACT:
      return "numeric_exact";
    case M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET:
      return "accepted_target";
    case M68K_TABLE_ENTRY_TARGET_STATUS_UNRESOLVED_TARGET:
      return "unresolved_target";
    case M68K_TABLE_ENTRY_TARGET_STATUS_INTERIOR_CODE_TARGET:
      return "interior_code_target";
    case M68K_TABLE_ENTRY_TARGET_STATUS_CONFLICTED_TARGET:
      return "conflicted_target";
    default:
      return NULL;
  }
}

const char *m68k_data_reference_source_kind_name(uint8_t source_kind) {
  switch (source_kind) {
    case M68K_DATA_REFERENCE_SOURCE_TABLE_ENTRY:
      return "table_entry";
    default:
      return NULL;
  }
}

const char *m68k_incomplete_analysis_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_INCOMPLETE_ANALYSIS_CAPACITY_EXHAUSTED:
      return "capacity_exhausted";
    default:
      return NULL;
  }
}

const char *m68k_incomplete_analysis_source_kind_name(uint8_t source_kind) {
  switch (source_kind) {
    case M68K_INCOMPLETE_ANALYSIS_SOURCE_TABLE_TARGET_SET:
      return "table_target_set";
    default:
      return NULL;
  }
}

const char *m68k_source_quality_diagnostic_severity_name(uint8_t severity) {
  switch (severity) {
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR:
      return "error";
    default:
      return "unknown";
  }
}

const char *m68k_source_quality_diagnostic_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_UNTERMINATED_OR_INVALID_CODE_RANGE:
      return "unterminated_or_invalid_code_range";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_PLATFORM_NAME_WITHOUT_USE_SHAPE:
      return "platform_name_without_use_shape";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_TABLE_TARGET_SET_LIMIT:
      return "table_target_set_limit";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_MISSING_ADDRESS_IDENTITY:
      return "missing_address_identity";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_MISSING_EXPECTED_SYMBOL_ACCESS:
      return "missing_expected_symbol_access";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_MANUAL_EVIDENCE_CONFLICT:
      return "manual_evidence_conflict";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_ACCEPTED_CODE_WITHOUT_EXECUTABLE_ORIGIN:
      return "accepted_code_without_executable_origin";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_UNREFERENCED_LABEL_STATEMENT:
      return "unreferenced_label_statement";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_PARTIAL_CODE_BLOCK_DECODE:
      return "partial_code_block_decode";
    default:
      return "unknown";
  }
}

const char *m68k_source_quality_diagnostic_origin_name(uint8_t origin) {
  switch (origin) {
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_AUTO_ANALYSIS:
      return "auto_analysis";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_PLATFORM_KB:
      return "platform_kb";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_MANUAL_EVIDENCE:
      return "manual_evidence";
    case M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_RENDER_EXPORT:
      return "render_export";
    default:
      return "unknown";
  }
}

const char *m68k_symbol_origin_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_SYMBOL_ORIGIN_ANALYSIS_LABEL:
      return "analysis_label";
    case M68K_SYMBOL_ORIGIN_ACCEPTED_CODE_TARGET:
      return "accepted_code_target";
    case M68K_SYMBOL_ORIGIN_DATA_REFERENCE:
      return "data_reference";
    case M68K_SYMBOL_ORIGIN_TABLE_ENTRY:
      return "table_entry";
    case M68K_SYMBOL_ORIGIN_ADDRESS_IDENTITY:
      return "address_identity";
    case M68K_SYMBOL_ORIGIN_PLATFORM_SEMANTIC_USE:
      return "platform_semantic_use";
    case M68K_SYMBOL_ORIGIN_MANUAL_LABEL:
      return "manual_label";
    case M68K_SYMBOL_ORIGIN_STRUCTURED_DATA:
      return "structured_data";
    case M68K_SYMBOL_ORIGIN_OBJECT_SYMBOL:
      return "object_symbol";
    default:
      return "unknown";
  }
}

const char *m68k_expected_symbol_access_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_EXPECTED_SYMBOL_ACCESS_LABEL_STATEMENT:
      return "label_statement";
    case M68K_EXPECTED_SYMBOL_ACCESS_BRANCH_TARGET:
      return "branch_target";
    case M68K_EXPECTED_SYMBOL_ACCESS_OPERAND:
      return "operand";
    case M68K_EXPECTED_SYMBOL_ACCESS_EQUATE:
      return "equate";
    case M68K_EXPECTED_SYMBOL_ACCESS_STORAGE_LABEL:
      return "storage_label";
    default:
      return "unknown";
  }
}

const char *m68k_rendered_symbol_access_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_RENDERED_SYMBOL_ACCESS_LABEL_STATEMENT:
      return "label_statement";
    case M68K_RENDERED_SYMBOL_ACCESS_BRANCH_TARGET:
      return "branch_target";
    case M68K_RENDERED_SYMBOL_ACCESS_OPERAND:
      return "operand";
    case M68K_RENDERED_SYMBOL_ACCESS_EQUATE:
      return "equate";
    case M68K_RENDERED_SYMBOL_ACCESS_COMMENT_ONLY:
      return "comment_only";
    case M68K_RENDERED_SYMBOL_ACCESS_STORAGE_LABEL:
      return "storage_label";
    default:
      return "unknown";
  }
}

const char *m68k_code_origin_class_name(uint8_t origin_class) {
  switch (origin_class) {
    case M68K_CODE_ORIGIN_STRONG_ENTRY:
      return "strong_entry";
    case M68K_CODE_ORIGIN_PROVEN_CONTROL_TARGET:
      return "proven_control_target";
    case M68K_CODE_ORIGIN_PROVEN_FALLTHROUGH:
      return "proven_fallthrough";
    case M68K_CODE_ORIGIN_PLATFORM_SEMANTIC_ENTRY:
      return "platform_semantic_entry";
    case M68K_CODE_ORIGIN_MANUAL_SEED:
      return "manual_seed";
    case M68K_CODE_ORIGIN_CONDITIONAL_TABLE_TARGET:
      return "conditional_table_target";
    case M68K_CODE_ORIGIN_CONDITIONAL_RUNTIME_ALIAS:
      return "conditional_runtime_alias";
    case M68K_CODE_ORIGIN_WEAK_SHAPE_ONLY:
      return "weak_shape_only";
    case M68K_CODE_ORIGIN_DATA_REFERENCE_ONLY:
      return "data_reference_only";
    default:
      return "unknown";
  }
}

const char *m68k_code_origin_evidence_kind_name(uint32_t evidence_kind) {
  switch (evidence_kind) {
    case M68K_CODE_ORIGIN_EVIDENCE_SECTION_ENTRY:
      return "section_entry";
    case M68K_CODE_ORIGIN_EVIDENCE_POLICY_ENTRY_OFFSET:
      return "policy_entry_offset";
    case M68K_CODE_ORIGIN_EVIDENCE_POLICY_ENTRY_POINT:
      return "policy_entry_point";
    case M68K_CODE_ORIGIN_EVIDENCE_FALLTHROUGH:
      return "fallthrough";
    case M68K_CODE_ORIGIN_EVIDENCE_INLINE_RESUME:
      return "inline_resume";
    case M68K_CODE_ORIGIN_EVIDENCE_RUNTIME_VIEW_ENTRY:
      return "runtime_view_entry";
    case M68K_CODE_ORIGIN_EVIDENCE_LINKAGE_API_ENTRY:
      return "linkage_api_entry";
    case M68K_CODE_ORIGIN_EVIDENCE_PLATFORM_LOADSEG_ENTRY:
      return "platform_loadseg_entry";
    case M68K_CODE_ORIGIN_EVIDENCE_STACK_CONTINUATION:
      return "stack_continuation";
    case M68K_CODE_ORIGIN_EVIDENCE_BOUNDARY_API_ENTRY:
      return "boundary_api_entry";
    case M68K_CODE_ORIGIN_EVIDENCE_RUNTIME_CONTROL_TARGET:
      return "runtime_control_target";
    case M68K_CODE_ORIGIN_EVIDENCE_DIRECT_CONTROL_TARGET:
      return "direct_control_target";
    case M68K_CODE_ORIGIN_EVIDENCE_RELOCATION_CONTROL_TARGET:
      return "relocation_control_target";
    case M68K_CODE_ORIGIN_EVIDENCE_TRACED_INDIRECT_CONTROL_TARGET:
      return "traced_indirect_control_target";
    case M68K_CODE_ORIGIN_EVIDENCE_DISPATCH_TABLE_CONTROL_TARGET:
      return "dispatch_table_control_target";
    case M68K_CODE_ORIGIN_EVIDENCE_CALLBACK_FIELD_CONTROL_TARGET:
      return "callback_field_control_target";
    case M68K_CODE_ORIGIN_EVIDENCE_VECTOR_STORE_CONTROL_TARGET:
      return "vector_store_control_target";
    case M68K_CODE_ORIGIN_EVIDENCE_RUNTIME_COPY_CONTROL_TARGET:
      return "runtime_copy_control_target";
    case M68K_CODE_ORIGIN_EVIDENCE_MANUAL_ACTION_LOG_ENTRY_POINT:
      return "manual_action_log_entry_point";
    case M68K_CODE_ORIGIN_EVIDENCE_DECISION_JOURNAL_ENTRY_POINT:
      return "decision_journal_entry_point";
    default:
      return "unknown";
  }
}

const char *m68k_accepted_code_run_end_kind_name(uint8_t end_kind) {
  switch (end_kind) {
    case M68K_ACCEPTED_CODE_RUN_END_TERMINAL:
      return "terminal";
    case M68K_ACCEPTED_CODE_RUN_END_PROVEN_TRANSFER:
      return "proven_transfer";
    case M68K_ACCEPTED_CODE_RUN_END_SECTION_BOUNDARY:
      return "section_boundary";
    case M68K_ACCEPTED_CODE_RUN_END_ACCEPTED_GAP:
      return "accepted_gap";
    case M68K_ACCEPTED_CODE_RUN_END_DATA_BOUNDARY:
      return "data_boundary";
    default:
      return "unknown";
  }
}

const char *m68k_address_observation_source_name(uint8_t source) {
  switch (source) {
    case M68K_ADDRESS_OBSERVATION_SOURCE_ABSOLUTE_OPERAND:
      return "absolute_operand";
    case M68K_ADDRESS_OBSERVATION_SOURCE_RUNTIME_ADDRESS_REF:
      return "runtime_address_ref";
    default:
      return "unknown";
  }
}

const char *m68k_address_identity_role_kind_name(uint8_t role_kind) {
  switch (role_kind) {
    case M68K_ADDRESS_IDENTITY_ROLE_STORAGE:
      return "storage";
    case M68K_ADDRESS_IDENTITY_ROLE_CODE:
      return "code";
    case M68K_ADDRESS_IDENTITY_ROLE_PLATFORM:
      return "platform";
    default:
      return "unknown";
  }
}

const char *m68k_absolute_address_range_status_name(uint8_t status) {
  switch (status) {
    case M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_OWNED:
      return "owned";
    case M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_UNOWNED_ONE_OFF:
      return "unowned_one_off";
    case M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_UNOWNED_SPARSE:
      return "unowned_sparse";
    case M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_CONFLICT:
      return "conflict";
    default:
      return "unknown";
  }
}

const char *m68k_absolute_memory_owner_kind_name(uint8_t owner_kind) {
  switch (owner_kind) {
    case M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL:
      return "execbase_literal";
    case M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR:
      return "cpu_vector";
    case M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER:
      return "hardware_register";
    case M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE:
      return "hardware_register_range";
    case M68K_ABSOLUTE_MEMORY_OWNER_RUNTIME_RANGE:
      return "runtime_range";
    case M68K_ABSOLUTE_MEMORY_OWNER_SECTION_STORAGE:
      return "section_storage";
    case M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY:
      return "absolute_memory";
    default:
      return "unknown";
  }
}

const char *m68k_analysis_conflict_state_name(uint8_t conflict_state) {
  switch (conflict_state) {
    case M68K_ANALYSIS_CONFLICT_STATE_CLEAN:
      return "clean";
    case M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP:
      return "code_overlap";
    case M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED:
      return "unresolved";
    case M68K_ANALYSIS_CONFLICT_STATE_CONFLICTED:
      return "conflicted";
    case M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED_CODE_TARGET:
      return "unresolved_code_target";
    default:
      return "unknown";
  }
}

const char *m68k_platform_address_use_shape_name(uint8_t use_shape) {
  switch (use_shape) {
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_TRUE_VECTOR_INSTALL:
      return "true_vector_install";
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_BASE:
      return "low_memory_base";
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_STORAGE:
      return "low_memory_storage";
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS:
      return "hardware_register_access";
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_EXECBASE_LITERAL:
      return "execbase_literal";
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_BASE_ADDRESS:
      return "hardware_base_address";
    default:
      return "unknown";
  }
}

const char *m68k_platform_semantic_use_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_PLATFORM_SEMANTIC_USE_COPPER_LIST:
      return "copper_list";
    case M68K_PLATFORM_SEMANTIC_USE_BITMAP_PLANE:
      return "bitmap_plane";
    case M68K_PLATFORM_SEMANTIC_USE_DISPLAY_SETUP:
      return "display_setup";
    case M68K_PLATFORM_SEMANTIC_USE_SOUND_SAMPLE:
      return "sound_sample";
    case M68K_PLATFORM_SEMANTIC_USE_DISK_BUFFER:
      return "disk_buffer";
    case M68K_PLATFORM_SEMANTIC_USE_BLITTER_BUFFER:
      return "blitter_buffer";
    case M68K_PLATFORM_SEMANTIC_USE_PALETTE:
      return "palette";
    case M68K_PLATFORM_SEMANTIC_USE_SPRITE:
      return "sprite";
    case M68K_PLATFORM_SEMANTIC_USE_AUDIO_TABLE:
      return "audio_table";
    case M68K_PLATFORM_SEMANTIC_USE_DISK_DMA:
      return "disk_dma";
    case M68K_PLATFORM_SEMANTIC_USE_AUDIO_REGISTER:
      return "audio_register";
    case M68K_PLATFORM_SEMANTIC_USE_HARDWARE_ACCESS:
      return "hardware_access";
    case M68K_PLATFORM_SEMANTIC_USE_HARDWARE_VALUE:
      return "hardware_value";
    case M68K_PLATFORM_SEMANTIC_USE_COPPER_ROW:
      return "copper_row";
    case M68K_PLATFORM_SEMANTIC_USE_COPPER_DISPLAY_LAYOUT:
      return "copper_display_layout";
    case M68K_PLATFORM_SEMANTIC_USE_BITMAP_MEMORY:
      return "bitmap_memory";
    case M68K_PLATFORM_SEMANTIC_USE_AUDIO_PERIOD_SOURCE:
      return "audio_period_source";
    case M68K_PLATFORM_SEMANTIC_USE_AUDIO_POINTER_SOURCE:
      return "audio_pointer_source";
    case M68K_PLATFORM_SEMANTIC_USE_PLATFORM_CALL_INPUT:
      return "platform_call_input";
    case M68K_PLATFORM_SEMANTIC_USE_PLATFORM_STACK_CLEANUP:
      return "platform_stack_cleanup";
    case M68K_PLATFORM_SEMANTIC_USE_RUNTIME_SINK_POINTER:
      return "runtime_sink_pointer";
    default:
      return "unknown";
  }
}

uint8_t m68k_analysis_structured_data_range_ownership_kind(const M68kAnalysisStructuredDataItem *item) {
  uint32_t role_flags;
  if (item == NULL) return M68K_RANGE_OWNERSHIP_UNKNOWN;
  role_flags = item->semantic_role_flags;
  if (item->platform_kind_id != M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_NONE ||
      item->platform_field_id != M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_NONE) {
    return M68K_RANGE_OWNERSHIP_PLATFORM_METADATA;
  }
  if ((role_flags & (M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE)) != 0U) {
    return M68K_RANGE_OWNERSHIP_TABLE;
  }
  if ((role_flags & (M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_MACOS_SYMBOL_STRING |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING_CONTROL_STREAM)) != 0U) {
    return M68K_RANGE_OWNERSHIP_TEXT;
  }
  return M68K_RANGE_OWNERSHIP_STRUCTURED_DATA;
}

uint32_t m68k_analysis_structured_data_range_ownership_evidence_flags(
    const M68kAnalysisStructuredDataItem *item) {
  uint32_t flags = M68K_RANGE_EVIDENCE_STRUCTURED_DATA;
  if (item == NULL) return flags;
  if (item->has_target) flags |= M68K_RANGE_EVIDENCE_POINTER_TARGET;
  if (item->has_consumer) flags |= M68K_RANGE_EVIDENCE_INDEXED_TABLE_ACCESS;
  if (item->platform_kind_id != M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_NONE ||
      item->platform_field_id != M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_NONE) {
    flags |= M68K_RANGE_EVIDENCE_PLATFORM_RECORD;
  }
  switch (item->source_pattern_id) {
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_API_STRING_POINTER:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_API_TEXT_BUFFER:
      flags |= M68K_RANGE_EVIDENCE_API_ARGUMENT;
      break;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POINTER_STRING_TABLE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_WORD_OFFSET_STRING_TABLE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_WORD_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_POINTER_READ:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_READ:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_INDIRECT_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH:
      flags |= M68K_RANGE_EVIDENCE_INDEXED_TABLE_ACCESS;
      break;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MULTILINE_TEXT:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_TERMINATED_TEXT:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_BOUNDED_TEXT:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_STRING_TABLE_SEQUENCE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_CONTROL_STRING_STREAM:
      flags |= M68K_RANGE_EVIDENCE_TEXT_SHAPE;
      break;
    default:
      break;
  }
  if ((item->semantic_role_flags & (M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_MACOS_SYMBOL_STRING |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING_CONTROL_STREAM)) != 0U) {
    flags |= M68K_RANGE_EVIDENCE_TEXT_SHAPE | M68K_RANGE_EVIDENCE_TERMINATOR_SHAPE;
  }
  return flags;
}

uint32_t m68k_analysis_structured_data_table_entry_size(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 0U;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES) return 1U;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS) return 2U;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS) return 4U;
  return 0U;
}

int m68k_ir_operand_immediate_value(const M68kOperandIR *operand, uint32_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (operand == NULL || out_value == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_IMM) {
    *out_value = operand->value.value;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U && operand->value.ea_reg == 4U) {
    *out_value = operand->value.value;
    return 1;
  }
  return 0;
}

int m68k_ir_byte_is_quoted_string_safe(uint8_t value) {
  return value >= 0x20U && value <= 0x7eU && value != '"' && value != '\\';
}

uint8_t m68k_analysis_table_entry_count_proof_for_source_pattern(uint8_t source_pattern_id) {
  switch (source_pattern_id) {
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_RELOCATION_POINTER_TABLE:
      return M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_RELOCATION_RECORD;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_WORD_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_POINTER_READ:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_SCALAR_READ:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POSTINCREMENT_READ_SEQUENCE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_READ:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_STRING_TABLE_SEQUENCE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POINTER_STRING_TABLE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_WORD_OFFSET_STRING_TABLE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_INDIRECT_DISPATCH:
      return M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_CONSUMER_STRUCTURAL_SCAN;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MACOS_SYMBOL_RECORD:
      return M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_PLATFORM_RECORD;
    default:
      return M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_STRUCTURED_RANGE;
  }
}

uint8_t m68k_analysis_table_stop_reason_for_entry_count_proof(uint8_t proof_id) {
  switch (proof_id) {
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_STRUCTURED_RANGE:
      return M68K_ANALYSIS_TABLE_STOP_REASON_STRUCTURED_RANGE_END;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_CONSUMER_STRUCTURAL_SCAN:
      return M68K_ANALYSIS_TABLE_STOP_REASON_CONSUMER_STRUCTURAL_STOP;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_RELOCATION_RECORD:
      return M68K_ANALYSIS_TABLE_STOP_REASON_RELOCATION_RECORD_END;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_PLATFORM_RECORD:
      return M68K_ANALYSIS_TABLE_STOP_REASON_PLATFORM_RECORD_END;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_MASK_DOMAIN:
      return M68K_ANALYSIS_TABLE_STOP_REASON_INDEX_MASK_BOUND;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_COMPARE_DOMAIN:
      return M68K_ANALYSIS_TABLE_STOP_REASON_INDEX_COMPARE_BRANCH_BOUND;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_LOOP_LIMIT:
      return M68K_ANALYSIS_TABLE_STOP_REASON_LOOP_LIMIT_BOUND;
    default:
      return M68K_ANALYSIS_TABLE_STOP_REASON_UNKNOWN;
  }
}

static uint8_t structured_data_item_infer_table_kind_id(const M68kAnalysisStructuredDataItem *item) {
  uint32_t role_flags;
  if (item == NULL) return M68K_ANALYSIS_TABLE_KIND_UNKNOWN;
  role_flags = item->semantic_role_flags;
  if ((role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) != 0U)
    return M68K_ANALYSIS_TABLE_KIND_POINTER;
  if ((role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) == 0U)
    return M68K_ANALYSIS_TABLE_KIND_UNKNOWN;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && item->has_target &&
      item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_WORD_OFFSET_STRING_TABLE)
    return M68K_ANALYSIS_TABLE_KIND_RELATIVE_DATA_LOOKUP;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && item->has_target)
    return M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS && item->has_target &&
      item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH)
    return M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
      item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_INDIRECT_DISPATCH)
    return M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS && item->has_target)
    return M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH;
  return M68K_ANALYSIS_TABLE_KIND_SCALAR;
}

#define STRUCTURED_TEXT_CAPACITY(member) (sizeof(member) > 0U ? sizeof(member) - 1U : 0U)

static char *structured_data_item_text_storage(M68kAnalysisStructuredDataItem *item, uint8_t field,
    size_t *out_capacity, uint16_t **out_length) {
  if (out_capacity != NULL) *out_capacity = 0U;
  if (out_length != NULL) *out_length = NULL;
  if (item == NULL) return NULL;
  switch (field) {
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_LABEL:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->label);
    if (out_length != NULL) *out_length = &item->label_len;
    return item->label;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_STRUCT_NAME:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->struct_name);
    if (out_length != NULL) *out_length = &item->struct_name_len;
    return item->struct_name;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_FIELD_NAME:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->field_name);
    if (out_length != NULL) *out_length = &item->field_name_len;
    return item->field_name;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_FIELD_TYPE:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->field_type);
    if (out_length != NULL) *out_length = &item->field_type_len;
    return item->field_type;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_C_TYPE:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->c_type);
    if (out_length != NULL) *out_length = &item->c_type_len;
    return item->c_type;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_POINTER_STRUCT:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->pointer_struct);
    if (out_length != NULL) *out_length = &item->pointer_struct_len;
    return item->pointer_struct;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_VALUE_DOMAIN:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->value_domain);
    if (out_length != NULL) *out_length = &item->value_domain_len;
    return item->value_domain;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_CONSTANT_NAME:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->constant_name);
    if (out_length != NULL) *out_length = &item->constant_name_len;
    return item->constant_name;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SEMANTIC_ROLE:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->semantic_role);
    if (out_length != NULL) *out_length = &item->semantic_role_len;
    return item->semantic_role;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SOURCE_PATTERN:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->source_pattern);
    if (out_length != NULL) *out_length = &item->source_pattern_len;
    return item->source_pattern;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_COMMENT:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->comment);
    if (out_length != NULL) *out_length = &item->comment_len;
    return item->comment;
  default:
    return NULL;
  }
}

static const char *structured_data_item_text_storage_const(const M68kAnalysisStructuredDataItem *item,
    uint8_t field, size_t *out_capacity, const uint16_t **out_length) {
  if (out_capacity != NULL) *out_capacity = 0U;
  if (out_length != NULL) *out_length = NULL;
  if (item == NULL) return NULL;
  switch (field) {
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_LABEL:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->label);
    if (out_length != NULL) *out_length = &item->label_len;
    return item->label;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_STRUCT_NAME:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->struct_name);
    if (out_length != NULL) *out_length = &item->struct_name_len;
    return item->struct_name;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_FIELD_NAME:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->field_name);
    if (out_length != NULL) *out_length = &item->field_name_len;
    return item->field_name;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_FIELD_TYPE:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->field_type);
    if (out_length != NULL) *out_length = &item->field_type_len;
    return item->field_type;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_C_TYPE:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->c_type);
    if (out_length != NULL) *out_length = &item->c_type_len;
    return item->c_type;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_POINTER_STRUCT:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->pointer_struct);
    if (out_length != NULL) *out_length = &item->pointer_struct_len;
    return item->pointer_struct;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_VALUE_DOMAIN:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->value_domain);
    if (out_length != NULL) *out_length = &item->value_domain_len;
    return item->value_domain;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_CONSTANT_NAME:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->constant_name);
    if (out_length != NULL) *out_length = &item->constant_name_len;
    return item->constant_name;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SEMANTIC_ROLE:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->semantic_role);
    if (out_length != NULL) *out_length = &item->semantic_role_len;
    return item->semantic_role;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SOURCE_PATTERN:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->source_pattern);
    if (out_length != NULL) *out_length = &item->source_pattern_len;
    return item->source_pattern;
  case M68K_ANALYSIS_STRUCTURED_DATA_TEXT_COMMENT:
    if (out_capacity != NULL) *out_capacity = STRUCTURED_TEXT_CAPACITY(item->comment);
    if (out_length != NULL) *out_length = &item->comment_len;
    return item->comment;
  default:
    return NULL;
  }
}

static size_t bounded_text_length_local(const char *text, size_t capacity) {
  size_t length = 0U;
  if (text == NULL) return 0U;
  while (length < capacity && text[length] != '\0') ++length;
  return length;
}

int m68k_analysis_structured_data_item_set_text(M68kAnalysisStructuredDataItem *item,
    uint8_t field, const char *text, size_t length) {
  uint16_t *stored_length;
  size_t capacity;
  size_t copy_length;
  char *storage = structured_data_item_text_storage(item, field, &capacity, &stored_length);
  if (storage == NULL || stored_length == NULL || capacity == 0U) return -1;
  if (text == NULL) {
    memset(storage, 0, capacity + 1U);
    *stored_length = 0U;
    return 0;
  }
  copy_length = length < capacity ? length : capacity;
  memcpy(storage, text, copy_length);
  storage[copy_length] = '\0';
  if (copy_length < capacity) memset(storage + copy_length + 1U, 0, capacity - copy_length);
  *stored_length = (uint16_t)copy_length;
  return copy_length == length ? 0 : -1;
}

const char *m68k_analysis_structured_data_item_text(const M68kAnalysisStructuredDataItem *item,
    uint8_t field, size_t *out_length) {
  const uint16_t *stored_length;
  size_t capacity;
  size_t length;
  const char *storage = structured_data_item_text_storage_const(item, field, &capacity, &stored_length);
  if (out_length != NULL) *out_length = 0U;
  if (storage == NULL || stored_length == NULL || capacity == 0U) return NULL;
  length = *stored_length != 0U ? *stored_length : bounded_text_length_local(storage, capacity);
  if (length > capacity) length = capacity;
  if (out_length != NULL) *out_length = length;
  return length != 0U ? storage : NULL;
}

static void m68k_analysis_structured_data_item_refresh_text_lengths(M68kAnalysisStructuredDataItem *item) {
  uint8_t field;
  if (item == NULL) return;
  for (field = M68K_ANALYSIS_STRUCTURED_DATA_TEXT_LABEL; field <= M68K_ANALYSIS_STRUCTURED_DATA_TEXT_COMMENT;
       ++field) {
    uint16_t *stored_length;
    size_t capacity;
    char *storage = structured_data_item_text_storage(item, field, &capacity, &stored_length);
    if (storage == NULL || stored_length == NULL) continue;
    if (*stored_length > capacity) {
      *stored_length = (uint16_t)capacity;
    } else if (*stored_length == 0U) {
      *stored_length = (uint16_t)bounded_text_length_local(storage, capacity);
    }
    storage[capacity] = '\0';
  }
}

void m68k_analysis_structured_data_item_refresh_table_metadata(M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return;
  item->table_kind_id = structured_data_item_infer_table_kind_id(item);
  item->table_base_expression_id = item->table_kind_id != M68K_ANALYSIS_TABLE_KIND_UNKNOWN
    ? (item->has_target ? M68K_ANALYSIS_TABLE_BASE_EXPRESSION_TARGET_LABEL :
        M68K_ANALYSIS_TABLE_BASE_EXPRESSION_TABLE_LABEL)
    : M68K_ANALYSIS_TABLE_BASE_EXPRESSION_UNKNOWN;
  if (item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN) {
    item->table_conflicted = 0U;
    item->table_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
    item->entry_count_proof_id = M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_UNKNOWN;
    item->table_stop_reason_id = M68K_ANALYSIS_TABLE_STOP_REASON_UNKNOWN;
  } else if (item->entry_count_proof_id == M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_UNKNOWN) {
    item->entry_count_proof_id =
      m68k_analysis_table_entry_count_proof_for_source_pattern(item->source_pattern_id);
  }
  if (item->table_kind_id != M68K_ANALYSIS_TABLE_KIND_UNKNOWN &&
      item->table_stop_reason_id == M68K_ANALYSIS_TABLE_STOP_REASON_UNKNOWN) {
    item->table_stop_reason_id =
      m68k_analysis_table_stop_reason_for_entry_count_proof(item->entry_count_proof_id);
  }
}

void m68k_analysis_structured_data_item_set_semantic_role_flags(M68kAnalysisStructuredDataItem *item,
    uint32_t semantic_role_flags) {
  const char *semantic_role;
  if (item == NULL) return;
  item->semantic_role_flags = semantic_role_flags;
  semantic_role = m68k_analysis_structured_data_role_name_for_flags(semantic_role_flags);
  (void)m68k_analysis_structured_data_item_set_text(item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SEMANTIC_ROLE,
    semantic_role != NULL ? semantic_role : "", semantic_role != NULL ? strlen(semantic_role) : 0U);
  m68k_analysis_structured_data_item_refresh_table_metadata(item);
}

static void m68k_ir_section_init_shared(M68kSectionIR *section, Arena *arena) {
  memset(section, 0, sizeof(*section));
  section->arena = arena;
}

static void m68k_ir_section_analysis_init_shared(M68kSectionAnalysisIR *section_analysis, Arena *arena) {
  memset(section_analysis, 0, sizeof(*section_analysis));
  section_analysis->arena = arena;
}

static void m68k_ir_source_analysis_init_defaults(M68kSourceAnalysisIR *source_analysis) {
  memset(source_analysis, 0, sizeof(*source_analysis));
  m68k_analysis_policy_init_default(&source_analysis->policy);
  m68k_analysis_findings_init(&source_analysis->findings);
}

static uint16_t m68k_platform_name_id_from_text(uint8_t platform_kind, uint8_t domain_kind, const char *text) {
  if (platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK) return amiga_os_name_id(domain_kind, text);
  if (platform_kind == M68K_PLATFORM_BACKEND_ATARI_ST) return atari_st_os_name_id(domain_kind, text);
  return 0U;
}

static uint16_t m68k_platform_name_resolve_id(const M68kPlatformNameRef *ref, const char *text) {
  if (m68k_platform_name_ref_resolve_text(ref) != NULL)
    return ref->id;
  if (ref == NULL || ref->platform_kind == 0U || ref->domain_kind == 0U) return 0U;
  return m68k_platform_name_id_from_text(ref->platform_kind, ref->domain_kind, text);
}

static uint8_t m68k_platform_kind_from_domain_text(uint8_t domain_kind, const char *text) {
  uint16_t id;
  if (text == NULL || text[0] == '\0') return 0U;
  id = amiga_os_name_id(domain_kind, text);
  if (amiga_os_name(domain_kind, id) != NULL) return M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  id = atari_st_os_name_id(domain_kind, text);
  if (atari_st_os_name(domain_kind, id) != NULL) return M68K_PLATFORM_BACKEND_ATARI_ST;
  return 0U;
}

static uint8_t m68k_platform_kind_from_ref_or_text(const M68kPlatformNameRef *ref, uint8_t default_domain_kind,
    const char *text) {
  uint8_t domain_kind = default_domain_kind;
  if (ref != NULL && ref->platform_kind != 0U) return ref->platform_kind;
  if (ref != NULL && ref->domain_kind != 0U) domain_kind = ref->domain_kind;
  if (domain_kind == 0U) return 0U;
  return m68k_platform_kind_from_domain_text(domain_kind, text);
}

static int m68k_platform_name_matches(const M68kPlatformNameRef *existing_ref, const char *existing_text,
    const M68kPlatformNameRef *candidate_ref, const char *candidate_text) {
  uint16_t existing_id = m68k_platform_name_resolve_id(existing_ref, existing_text);
  uint16_t candidate_id = m68k_platform_name_resolve_id(candidate_ref, candidate_text);
  M68kPlatformNameRef existing_resolved = { 0U, 0U, 0U };
  M68kPlatformNameRef candidate_resolved = { 0U, 0U, 0U };
  int existing_has_id = 0;
  int candidate_has_id = 0;
  if (existing_ref != NULL) {
    existing_resolved.platform_kind = existing_ref->platform_kind;
    existing_resolved.domain_kind = existing_ref->domain_kind;
    existing_resolved.id = existing_id;
    existing_has_id = m68k_platform_name_ref_resolve_text(&existing_resolved) != NULL;
  }
  if (candidate_ref != NULL) {
    candidate_resolved.platform_kind = candidate_ref->platform_kind;
    candidate_resolved.domain_kind = candidate_ref->domain_kind;
    candidate_resolved.id = candidate_id;
    candidate_has_id = m68k_platform_name_ref_resolve_text(&candidate_resolved) != NULL;
  }
  if (existing_has_id || candidate_has_id) return existing_has_id && candidate_has_id &&
    existing_ref->platform_kind == candidate_ref->platform_kind &&
    existing_ref->domain_kind == candidate_ref->domain_kind &&
    existing_id == candidate_id;
  if (existing_text == NULL || candidate_text == NULL) return existing_text == candidate_text;
  return strcmp(existing_text, candidate_text) == 0;
}

static char *arena_strdup_if_unresolved_name(Arena *arena, const M68kPlatformNameRef *ref, const char *text) {
  if (text == NULL) return NULL;
  if (m68k_platform_name_ref_resolve_text(ref) != NULL) return NULL;
  return arena_strdup(arena, text);
}

int m68k_ir_section_create(M68kSectionIR *section, Arena *result_arena) {
  if (section == NULL || result_arena == NULL) return -1;
  memset(section, 0, sizeof(*section));
  section->arena = result_arena;
  return 0;
}

int m68k_ir_source_file_create(M68kSourceFileIR *source_file) {
  if (source_file == NULL) return -1;
  memset(source_file, 0, sizeof(*source_file));
  source_file->arena = arena_create(M68K_IR_SOURCE_FILE_ARENA_SIZE);
  return source_file->arena != NULL ? 0 : -1;
}

int m68k_ir_section_analysis_create(M68kSectionAnalysisIR *section_analysis, Arena *result_arena) {
  if (section_analysis == NULL || result_arena == NULL) return -1;
  memset(section_analysis, 0, sizeof(*section_analysis));
  section_analysis->arena = result_arena;
  return 0;
}

int m68k_ir_source_analysis_create(M68kSourceAnalysisIR *source_analysis) {
  if (source_analysis == NULL) return -1;
  m68k_ir_source_analysis_init_defaults(source_analysis);
  source_analysis->arena = arena_create(M68K_IR_SOURCE_ANALYSIS_ARENA_SIZE);
  return source_analysis->arena != NULL ? 0 : -1;
}

int m68k_ir_source_analysis_append_structured_data_item(M68kSourceAnalysisIR *source_analysis,
    const M68kAnalysisStructuredDataItem *item) {
  Arena *arena;
  M68kAnalysisStructuredDataItem *grown;
  M68kAnalysisStructuredDataItem copy;
  if (source_analysis == NULL || item == NULL) return -1;
  arena = source_analysis->arena;
  if (arena == NULL) return -1;
  copy = *item;
  m68k_analysis_structured_data_item_refresh_text_lengths(&copy);
  grown = (M68kAnalysisStructuredDataItem *)arena_grow_array(arena,
    source_analysis->structured_data_items, source_analysis->structured_data_item_count,
    &source_analysis->structured_data_item_capacity, 32U, sizeof(*source_analysis->structured_data_items));
  if (grown == NULL) return -1;
  source_analysis->structured_data_items = grown;
  source_analysis->structured_data_items[source_analysis->structured_data_item_count++] = copy;
  if (source_analysis->policy.structured_data_item_count < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT) {
    source_analysis->policy.structured_data_items[source_analysis->policy.structured_data_item_count++] = copy;
  }
  return 0;
}

int m68k_ir_source_analysis_append_incomplete_analysis(M68kSourceAnalysisIR *source_analysis,
    const M68kIncompleteAnalysisIR *incomplete) {
  size_t index;
  if (source_analysis == NULL || incomplete == NULL) return -1;
  if (source_analysis->arena == NULL) return -1;
  if (incomplete->kind == M68K_INCOMPLETE_ANALYSIS_UNKNOWN ||
      incomplete->source_kind == M68K_INCOMPLETE_ANALYSIS_SOURCE_UNKNOWN) {
    return 0;
  }
  for (index = 0U; index < source_analysis->incomplete_analysis_count; ++index) {
    const M68kIncompleteAnalysisIR *existing = &source_analysis->incomplete_analyses[index];
    if (existing->kind == incomplete->kind &&
        existing->source_kind == incomplete->source_kind &&
        existing->section_index == incomplete->section_index &&
        existing->offset == incomplete->offset &&
        existing->capacity == incomplete->capacity) {
      if (source_analysis->incomplete_analyses[index].hit_count < incomplete->hit_count)
        source_analysis->incomplete_analyses[index].hit_count = incomplete->hit_count;
      return 0;
    }
  }
  source_analysis->incomplete_analyses = (M68kIncompleteAnalysisIR *)arena_grow_array(source_analysis->arena,
      source_analysis->incomplete_analyses, source_analysis->incomplete_analysis_count,
      &source_analysis->incomplete_analysis_capacity, 4U, sizeof(*source_analysis->incomplete_analyses));
  if (source_analysis->incomplete_analyses == NULL) return -1;
  source_analysis->incomplete_analyses[source_analysis->incomplete_analysis_count++] = *incomplete;
  return 0;
}

static int copy_source_quality_diagnostic_local(Arena *arena, M68kSourceQualityDiagnosticIR *dest,
    const M68kSourceQualityDiagnosticIR *src) {
  if (arena == NULL || dest == NULL || src == NULL) return -1;
  *dest = *src;
  dest->severity = M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR;
  dest->blocker = 1U;
  if (src->summary != NULL) {
    dest->summary = arena_strdup(arena, src->summary);
    if (dest->summary == NULL) return -1;
  }
  if (src->evidence_source != NULL) {
    dest->evidence_source = arena_strdup(arena, src->evidence_source);
    if (dest->evidence_source == NULL) return -1;
  }
  if (src->platform_use_shape != NULL) {
    dest->platform_use_shape = arena_strdup(arena, src->platform_use_shape);
    if (dest->platform_use_shape == NULL) return -1;
  }
  if (src->owner_kind != NULL) {
    dest->owner_kind = arena_strdup(arena, src->owner_kind);
    if (dest->owner_kind == NULL) return -1;
  }
  return 0;
}

static int source_quality_diagnostic_same_location_kind_local(const M68kSourceQualityDiagnosticIR *left,
    const M68kSourceQualityDiagnosticIR *right) {
  if (left == NULL || right == NULL) return 0;
  return left->kind == right->kind &&
    left->has_section_index == right->has_section_index &&
    (!left->has_section_index || left->section_index == right->section_index) &&
    left->has_offset == right->has_offset &&
    (!left->has_offset || left->offset == right->offset);
}

int m68k_ir_source_analysis_append_source_quality_diagnostic(M68kSourceAnalysisIR *source_analysis,
    const M68kSourceQualityDiagnosticIR *diagnostic) {
  M68kSourceQualityDiagnosticIR copy;
  size_t index;
  if (source_analysis == NULL || diagnostic == NULL || source_analysis->arena == NULL) return -1;
  if (diagnostic->kind == M68K_SOURCE_QUALITY_DIAGNOSTIC_UNKNOWN) return 0;
  for (index = 0U; index < source_analysis->source_quality_diagnostic_count; ++index) {
    if (source_quality_diagnostic_same_location_kind_local(
        &source_analysis->source_quality_diagnostics[index], diagnostic)) {
      return 0;
    }
  }
  source_analysis->source_quality_diagnostics =
    (M68kSourceQualityDiagnosticIR *)arena_grow_array(source_analysis->arena,
      source_analysis->source_quality_diagnostics, source_analysis->source_quality_diagnostic_count,
      &source_analysis->source_quality_diagnostic_capacity, 8U,
      sizeof(*source_analysis->source_quality_diagnostics));
  if (source_analysis->source_quality_diagnostics == NULL) return -1;
  memset(&copy, 0, sizeof(copy));
  if (copy_source_quality_diagnostic_local(source_analysis->arena, &copy, diagnostic) != 0) return -1;
  source_analysis->source_quality_diagnostics[source_analysis->source_quality_diagnostic_count++] = copy;
  return 0;
}

int m68k_ir_source_analysis_append_address_identity(M68kSourceAnalysisIR *source_analysis,
    const M68kAddressIdentityIR *identity) {
  M68kAddressIdentityIR copy;
  size_t index;
  if (source_analysis == NULL || identity == NULL || source_analysis->arena == NULL) return -1;
  if (identity->identity_id == 0U) return 0;
  for (index = 0U; index < source_analysis->address_identity_count; ++index) {
    const M68kAddressIdentityIR *existing = &source_analysis->address_identities[index];
    if (existing->identity_id == identity->identity_id) return 0;
  }
  source_analysis->address_identities = (M68kAddressIdentityIR *)arena_grow_array(source_analysis->arena,
    source_analysis->address_identities, source_analysis->address_identity_count,
    &source_analysis->address_identity_capacity, 16U, sizeof(*source_analysis->address_identities));
  if (source_analysis->address_identities == NULL) return -1;
  copy = *identity;
  copy.symbol_name = NULL;
  if (identity->symbol_name != NULL) {
    copy.symbol_name = arena_strdup(source_analysis->arena, identity->symbol_name);
    if (copy.symbol_name == NULL) return -1;
  }
  source_analysis->address_identities[source_analysis->address_identity_count++] = copy;
  return 0;
}

int m68k_ir_source_analysis_append_absolute_address_range(M68kSourceAnalysisIR *source_analysis,
    const M68kAbsoluteAddressRangeIR *range) {
  M68kAbsoluteAddressRangeIR copy;
  size_t index;
  if (source_analysis == NULL || range == NULL || source_analysis->arena == NULL) return -1;
  if (range->status == M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_UNKNOWN) return 0;
  for (index = 0U; index < source_analysis->absolute_address_range_count; ++index) {
    const M68kAbsoluteAddressRangeIR *existing = &source_analysis->absolute_address_ranges[index];
    if (existing->start_address == range->start_address &&
        existing->range_size == range->range_size &&
        existing->owner_kind == range->owner_kind &&
        existing->status == range->status &&
        existing->source_section_index == range->source_section_index &&
        existing->source_offset == range->source_offset) {
      return 0;
    }
  }
  source_analysis->absolute_address_ranges = (M68kAbsoluteAddressRangeIR *)arena_grow_array(
    source_analysis->arena, source_analysis->absolute_address_ranges,
    source_analysis->absolute_address_range_count, &source_analysis->absolute_address_range_capacity,
    16U, sizeof(*source_analysis->absolute_address_ranges));
  if (source_analysis->absolute_address_ranges == NULL) return -1;
  copy = *range;
  copy.symbol_name = NULL;
  if (range->symbol_name != NULL) {
    copy.symbol_name = arena_strdup(source_analysis->arena, range->symbol_name);
    if (copy.symbol_name == NULL) return -1;
  }
  source_analysis->absolute_address_ranges[source_analysis->absolute_address_range_count++] = copy;
  return 0;
}

size_t m68k_ir_source_analysis_structured_data_item_count(const M68kSourceAnalysisIR *source_analysis) {
  if (source_analysis == NULL) return 0U;
  return source_analysis->structured_data_item_count != 0U ? source_analysis->structured_data_item_count :
    source_analysis->policy.structured_data_item_count;
}

const M68kAnalysisStructuredDataItem *m68k_ir_source_analysis_structured_data_item_at(
    const M68kSourceAnalysisIR *source_analysis, size_t index) {
  if (source_analysis == NULL) return NULL;
  if (source_analysis->structured_data_item_count != 0U) {
    return index < source_analysis->structured_data_item_count ? &source_analysis->structured_data_items[index] : NULL;
  }
  return index < source_analysis->policy.structured_data_item_count &&
    index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT ? &source_analysis->policy.structured_data_items[index] : NULL;
}

int m68k_ir_source_analysis_set_policy(M68kSourceAnalysisIR *source_analysis, const M68kAnalysisPolicy *policy) {
  uint16_t index;
  uint16_t structured_count;
  int copied_source_policy = 0;
  M68kAnalysisPolicy policy_copy;
  const M68kAnalysisPolicy *source_policy;
  if (source_analysis == NULL || policy == NULL) return -1;
  source_policy = policy;
  if (policy == &source_analysis->policy) {
    m68k_analysis_policy_init_default(&policy_copy);
    if (m68k_analysis_policy_copy(&policy_copy, policy) != 0) return -1;
    source_policy = &policy_copy;
    copied_source_policy = 1;
  }
  m68k_analysis_policy_destroy(&source_analysis->policy);
  source_analysis->structured_data_items = NULL;
  source_analysis->structured_data_item_count = 0U;
  source_analysis->structured_data_item_capacity = 0U;
  if (m68k_analysis_policy_copy(&source_analysis->policy, source_policy) != 0) {
    if (copied_source_policy) m68k_analysis_policy_destroy(&policy_copy);
    return -1;
  }
  structured_count = source_analysis->policy.structured_data_item_count;
  source_analysis->policy.structured_data_item_count = 0U;
  for (index = 0U; index < structured_count && index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    if (m68k_ir_source_analysis_append_structured_data_item(source_analysis,
        &source_policy->structured_data_items[index]) != 0) {
      if (copied_source_policy) m68k_analysis_policy_destroy(&policy_copy);
      return -1;
    }
  }
  if (copied_source_policy) m68k_analysis_policy_destroy(&policy_copy);
  return 0;
}

void m68k_ir_symbol_ref_init(M68kSymbolRefIR *symbol_ref) {
  if (symbol_ref == NULL) return;

  memset(symbol_ref, 0, sizeof(*symbol_ref));
}

void m68k_render_policy_init_default(M68kRenderPolicy *policy) {
  if (policy == NULL) return;

  memset(policy, 0, sizeof(*policy));
  policy->syntax.syntax_mode = M68K_IR_SYNTAX_CANONICAL;
  policy->presentation.prefer_generated_names = 1U;
  policy->presentation.prefer_strings = 1U;
  policy->presentation.prefer_long_data = 1U;
  memcpy(policy->presentation.code_label_prefix, "loc", 4U);
  memcpy(policy->presentation.call_label_prefix, "sub", 4U);
  memcpy(policy->presentation.data_label_prefix, "dat", 4U);
}

void m68k_render_policy_init_for_syntax(M68kRenderPolicy *policy, uint8_t syntax_mode) {
  m68k_render_policy_init_default(policy);
  if (policy == NULL) return;

  policy->syntax.syntax_mode = syntax_mode;
}

int m68k_ir_parse_syntax_mode_name(const char *text, uint8_t *out_syntax_mode) {
  if (text == NULL || out_syntax_mode == NULL) return 0;
  if (_stricmp(text, "canonical") == 0) { *out_syntax_mode = M68K_IR_SYNTAX_CANONICAL; return 1; }
  if (_stricmp(text, "genam") == 0) { *out_syntax_mode = M68K_IR_SYNTAX_GENAM; return 1; }
  if (_stricmp(text, "vasm") == 0) { *out_syntax_mode = M68K_IR_SYNTAX_VASM; return 1; }
  return 0;
}

void m68k_analysis_policy_init_default(M68kAnalysisPolicy *policy) {
  if (policy == NULL) return;

  memset(policy, 0, sizeof(*policy));
  policy->max_cpu = M68K_ASM_CPU_68060;
}

void m68k_analysis_policy_destroy(M68kAnalysisPolicy *policy) {
  if (policy == NULL) return;
  if (policy->custom_struct_owner != 0U && policy->custom_structs != NULL) free(policy->custom_structs);
  policy->custom_structs = NULL;
  policy->custom_struct_count = 0U;
  policy->custom_struct_capacity = 0U;
  policy->custom_struct_owner = 0U;
}

int m68k_analysis_policy_copy(M68kAnalysisPolicy *dest, const M68kAnalysisPolicy *src) {
  uint16_t custom_struct_count;
  uint16_t index;
  M68kAnalysisCustomStruct *custom_structs = NULL;
  if (dest == NULL || src == NULL) return -1;
  custom_struct_count = src->custom_struct_count;
  if (custom_struct_count != 0U) {
    if (src->custom_structs == NULL || custom_struct_count > M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT) return -1;
    custom_structs = (M68kAnalysisCustomStruct *)calloc(custom_struct_count, sizeof(*custom_structs));
    if (custom_structs == NULL) return -1;
    memcpy(custom_structs, src->custom_structs, (size_t)custom_struct_count * sizeof(*custom_structs));
  }
  *dest = *src;
  dest->custom_structs = custom_structs;
  dest->custom_struct_capacity = custom_struct_count;
  dest->custom_struct_owner = custom_struct_count != 0U ? 1U : 0U;
  for (index = 0U; index < dest->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    m68k_analysis_structured_data_item_refresh_text_lengths(&dest->structured_data_items[index]);
  }
  return 0;
}

void m68k_analysis_findings_init(M68kAnalysisFindings *findings) {
  if (findings == NULL) return;

  memset(findings, 0, sizeof(*findings));
  findings->required_cpu = M68K_ASM_CPU_68000;
}

void m68k_platform_name_ref_init(M68kPlatformNameRef *ref) {
  if (ref == NULL) return;
  memset(ref, 0, sizeof(*ref));
}

int m68k_platform_name_ref_is_set(const M68kPlatformNameRef *ref) {
  return m68k_platform_name_ref_resolve_text(ref) != NULL;
}

const char *m68k_platform_name_ref_resolve_text(const M68kPlatformNameRef *ref) {
  if (ref == NULL || ref->platform_kind == 0U || ref->domain_kind == 0U) return NULL;
  if (ref->platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK) return amiga_os_name(ref->domain_kind, ref->id);
  if (ref->platform_kind == M68K_PLATFORM_BACKEND_ATARI_ST) return atari_st_os_name(ref->domain_kind, ref->id);
  return NULL;
}

const char *m68k_platform_name_ref_display_text(const M68kPlatformNameRef *ref, const char *stored_text) {
  const char *resolved = m68k_platform_name_ref_resolve_text(ref);
  return resolved != NULL ? resolved : stored_text;
}

const char *m68k_target_os_compatibility_status_name(uint8_t status) {
  switch (status) {
  case M68K_TARGET_OS_COMPATIBILITY_NO_OS_CALLS: return "no_os_calls";
  case M68K_TARGET_OS_COMPATIBILITY_UNKNOWN: return "unknown";
  case M68K_TARGET_OS_COMPATIBILITY_OBSERVED: return "observed";
  default: return "unknown";
  }
}

static size_t target_platform_summary_runtime_view_count(const M68kSourceAnalysisIR *source_analysis) {
  size_t count = 0U;
  size_t section_index;
  if (source_analysis == NULL) return 0U;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index)
    count += source_analysis->sections[section_index].runtime_view_count;
  return count;
}

static int target_platform_summary_version_seen(const char versions[][16], size_t count, const char *version) {
  size_t index;
  if (version == NULL || version[0] == '\0') return 1;
  for (index = 0U; index < count; ++index) {
    if (strcmp(versions[index], version) == 0) return 1;
  }
  return 0;
}

static int target_platform_summary_fd_version_rank(const char *version, uint16_t *out_rank) {
  char *end = NULL;
  unsigned long parsed;
  if (out_rank != NULL) *out_rank = 0U;
  if (version == NULL || version[0] == '\0' || out_rank == NULL) return 0;
  parsed = strtoul(version, &end, 10);
  if (end == version || end == NULL || *end != '\0' || parsed > 65535UL) return 0;
  *out_rank = (uint16_t)parsed;
  return 1;
}

static void target_platform_summary_append_version(char versions[][16], uint16_t ranks[], size_t *io_count,
    const char *version, int is_fd_version) {
  uint16_t rank = 0U;
  size_t index;
  if (versions == NULL || ranks == NULL || io_count == NULL ||
      *io_count >= M68K_TARGET_PLATFORM_SUMMARY_VERSION_CAPACITY ||
      version == NULL || version[0] == '\0' || target_platform_summary_version_seen(versions, *io_count, version)) {
    return;
  }
  if (is_fd_version) {
    if (!target_platform_summary_fd_version_rank(version, &rank)) return;
  } else if (!amiga_os_compatibility_version_rank(version, &rank)) {
    return;
  }
  index = *io_count;
  while (index > 0U && ranks[index - 1U] > rank) {
    ranks[index] = ranks[index - 1U];
    snprintf(versions[index], sizeof(versions[index]), "%s", versions[index - 1U]);
    --index;
  }
  ranks[index] = rank;
  snprintf(versions[index], sizeof(versions[index]), "%s", version);
  ++*io_count;
}

static int target_platform_summary_version_rank(const char *version, uint16_t *out_rank) {
  return amiga_os_compatibility_version_rank(version, out_rank);
}

static void target_platform_summary_append_lower_versions(M68kTargetOsCompatibilitySummary *summary) {
  uint16_t required_rank = 0U;
  size_t index;
  if (summary == NULL || summary->minimum_required[0] == '\0' ||
      !target_platform_summary_version_rank(summary->minimum_required, &required_rank)) {
    return;
  }
  for (index = 0U; index < summary->observed_available_since_count; ++index) {
    uint16_t rank = summary->observed_available_since_ranks[index];
    if (rank < required_rank) {
      target_platform_summary_append_version(summary->lower_observed_available_since,
        summary->lower_observed_available_since_ranks, &summary->lower_observed_available_since_count,
        summary->observed_available_since[index], 0);
    }
  }
}

static const char *target_platform_summary_call_display_name(const M68kRecoveredPlatformCallIR *call) {
  const char *name;
  if (call == NULL) return "unknown";
  name = m68k_platform_name_ref_display_text(&call->symbol_ref, call->symbol_name);
  if (name != NULL && name[0] != '\0') return name;
  name = m68k_platform_name_ref_display_text(&call->note_symbol_ref, call->note_symbol_name);
  return name != NULL && name[0] != '\0' ? name : "unknown";
}

static int target_platform_summary_call_is_amiga_os(const M68kRecoveredPlatformCallIR *call) {
  return call != NULL && (call->symbol_ref.platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
    call->note_symbol_ref.platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK);
}

static void target_platform_summary_fill_driver(M68kTargetOsRequirementDriver *driver,
    const M68kSectionAnalysisIR *section, const M68kRecoveredPlatformCallIR *call) {
  const char *owner;
  if (driver == NULL || section == NULL || call == NULL) {
    return;
  }
  memset(driver, 0, sizeof(*driver));
  driver->section_index = (uint32_t)section->section_index;
  driver->offset = call->offset;
  driver->call = target_platform_summary_call_display_name(call);
  owner = m68k_platform_name_ref_display_text(&call->note_base_ref, call->note_base_name);
  if (owner != NULL && owner[0] != '\0') {
    driver->has_owner = 1U;
    driver->owner = owner;
  }
  driver->available_since = call->available_since != NULL ? call->available_since : "";
  if (call->fd_version != NULL && call->fd_version[0] != '\0') {
    driver->has_fd_version = 1U;
    driver->fd_version = call->fd_version;
  }
}

static int target_platform_summary_same_requirement_group(const M68kTargetOsRequirementGroup *group,
    const M68kTargetOsRequirementDriver *driver) {
  if (group == NULL || driver == NULL) return 0;
  return strcmp(group->call, driver->call) == 0 &&
    strcmp(group->available_since, driver->available_since) == 0 &&
    group->has_owner == driver->has_owner &&
    (!group->has_owner || strcmp(group->owner, driver->owner) == 0);
}

static void target_platform_summary_group_append_location(M68kTargetOsRequirementGroup *group,
    const M68kTargetOsRequirementDriver *driver) {
  if (group == NULL || driver == NULL) return;
  ++group->count;
  if (group->has_fd_version &&
    (!driver->has_fd_version || strcmp(group->fd_version, driver->fd_version) != 0)) {
    group->has_fd_version = 0U;
    group->fd_version = NULL;
  }
}

static void target_platform_summary_record_requirement_group(M68kTargetOsCompatibilitySummary *summary,
    const M68kTargetOsRequirementDriver *driver) {
  M68kTargetOsRequirementGroup *group;
  size_t index;
  if (summary == NULL || driver == NULL) return;
  for (index = 0U; index < summary->requirement_group_count; ++index) {
    group = &summary->requirement_groups[index];
    if (target_platform_summary_same_requirement_group(group, driver)) {
      target_platform_summary_group_append_location(group, driver);
      return;
    }
  }
  if (summary->requirement_group_count >= M68K_TARGET_PLATFORM_SUMMARY_GROUP_CAPACITY) {
    summary->requirement_groups_truncated = 1U;
    return;
  }
  group = &summary->requirement_groups[summary->requirement_group_count++];
  memset(group, 0, sizeof(*group));
  group->call = driver->call;
  group->available_since = driver->available_since;
  group->has_owner = driver->has_owner;
  if (driver->has_owner) group->owner = driver->owner;
  group->has_fd_version = driver->has_fd_version;
  if (driver->has_fd_version) group->fd_version = driver->fd_version;
  target_platform_summary_group_append_location(group, driver);
}

static void target_platform_summary_record_raw_driver(M68kTargetOsCompatibilitySummary *summary,
    const M68kSectionAnalysisIR *section, const M68kRecoveredPlatformCallIR *call) {
  M68kTargetOsRequirementDriver driver;
  if (summary == NULL || section == NULL || call == NULL) return;
  target_platform_summary_fill_driver(&driver, section, call);
  if (summary->raw_requirement_driver_count >= M68K_TARGET_PLATFORM_SUMMARY_RAW_DRIVER_CAPACITY) {
    summary->raw_requirement_drivers_truncated = 1U;
  } else {
    summary->raw_requirement_drivers[summary->raw_requirement_driver_count++] = driver;
  }
  target_platform_summary_record_requirement_group(summary, &driver);
}

static void target_platform_summary_record_max_driver(M68kTargetOsCompatibilitySummary *summary,
    const M68kSectionAnalysisIR *section, const M68kRecoveredPlatformCallIR *call) {
  M68kTargetOsRequirementDriver *driver;
  if (summary == NULL || section == NULL || call == NULL) return;
  if (summary->max_requirement_driver_count >= M68K_TARGET_PLATFORM_SUMMARY_DRIVER_CAPACITY) {
    summary->max_requirement_drivers_truncated = 1U;
    return;
  }
  driver = &summary->max_requirement_drivers[summary->max_requirement_driver_count++];
  target_platform_summary_fill_driver(driver, section, call);
}

int m68k_target_platform_summary_build(const M68kSourceAnalysisIR *source_analysis, uint8_t platform_backend_kind,
    M68kTargetPlatformSummary *out_summary) {
  uint16_t max_rank = 0U;
  size_t section_index;
  if (source_analysis == NULL || out_summary == NULL) return -1;
  memset(out_summary, 0, sizeof(*out_summary));
  out_summary->runtime_view_count = (uint32_t)target_platform_summary_runtime_view_count(source_analysis);
  if (platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    out_summary->os_compatibility.status = M68K_TARGET_OS_COMPATIBILITY_NO_OS_CALLS;
    return 0;
  }
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t call_index;
    for (call_index = 0U; call_index < section->recovered_platform_call_count; ++call_index) {
      const M68kRecoveredPlatformCallIR *call = &section->recovered_platform_calls[call_index];
      uint16_t rank = 0U;
      if (!target_platform_summary_call_is_amiga_os(call)) continue;
      ++out_summary->os_compatibility.call_count;
      target_platform_summary_append_version(out_summary->os_compatibility.observed_available_since,
        out_summary->os_compatibility.observed_available_since_ranks,
        &out_summary->os_compatibility.observed_available_since_count, call->available_since, 0);
      target_platform_summary_append_version(out_summary->os_compatibility.observed_fd_versions,
        out_summary->os_compatibility.observed_fd_version_ranks,
        &out_summary->os_compatibility.observed_fd_version_count, call->fd_version, 1);
      if (amiga_os_compatibility_version_rank(call->available_since, &rank)) {
        target_platform_summary_record_raw_driver(&out_summary->os_compatibility, section, call);
      }
      if (rank != 0U && rank >= max_rank) {
        if (rank > max_rank) {
          max_rank = rank;
          out_summary->os_compatibility.max_requirement_driver_count = 0U;
          out_summary->os_compatibility.max_requirement_drivers_truncated = 0U;
        }
        target_platform_summary_record_max_driver(&out_summary->os_compatibility, section, call);
      }
    }
  }
  if (out_summary->os_compatibility.call_count == 0U) {
    out_summary->os_compatibility.status = M68K_TARGET_OS_COMPATIBILITY_NO_OS_CALLS;
  } else if (out_summary->os_compatibility.observed_available_since_count == 0U) {
    out_summary->os_compatibility.status = M68K_TARGET_OS_COMPATIBILITY_UNKNOWN;
  } else {
    out_summary->os_compatibility.status = M68K_TARGET_OS_COMPATIBILITY_OBSERVED;
    snprintf(out_summary->os_compatibility.minimum_required,
      sizeof(out_summary->os_compatibility.minimum_required), "%s",
      out_summary->os_compatibility.observed_available_since[
        out_summary->os_compatibility.observed_available_since_count - 1U]);
    target_platform_summary_append_lower_versions(&out_summary->os_compatibility);
  }
  return 0;
}

void m68k_ir_instruction_init(M68kInstructionIR *instruction) {
  memset(instruction, 0, sizeof(*instruction));
  instruction->asm_form_index = M68K_ASM_FORM_NONE;
  instruction->canonical_form_id = M68K_FORM_ID_NONE;
  instruction->mnemonic_id = M68K_ASM_MNEMONIC_NONE;
}

const char *m68k_ir_instruction_mnemonic_name(const M68kInstructionIR *instruction) {
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_NONE)
    return m68k_asm_mnemonic_name(instruction->mnemonic_id);
  return m68k_asm_mnemonic_name(M68K_ASM_MNEMONIC_NONE);
}

void m68k_ir_data_item_init(M68kDataItemIR *item) {
  if (item == NULL) return;

  memset(item, 0, sizeof(*item));
}

void m68k_ir_statement_init(M68kStatementIR *statement) {
  if (statement == NULL) return;

  memset(statement, 0, sizeof(*statement));
}

void m68k_ir_statement_free(M68kStatementIR *statement) {
  if (statement == NULL) return;

  memset(statement, 0, sizeof(*statement));
}

int m68k_ir_section_set_name(M68kSectionIR *section, const char *name) {
  if (section == NULL) return -1;
  if (name == NULL) {
    section->name = NULL;
    return 0;
  }
  if (section->arena == NULL) return -1;
  section->name = arena_strdup(section->arena, name);
  return section->name != NULL ? 0 : -1;
}

void m68k_ir_section_destroy(M68kSectionIR *section) {
  size_t index;
  if (section == NULL) return;

  for (index = 0; index < section->statement_count; ++index)
    m68k_ir_statement_free(&section->statements[index]);
  memset(section, 0, sizeof(*section));
}

int m68k_ir_section_append_statement(M68kSectionIR *section, const M68kStatementIR *statement) {
  M68kStatementIR copy;
  if (section == NULL || statement == NULL) return -1;
  if (section->arena == NULL) return -1;
  section->statements = (M68kStatementIR *)arena_grow_array(section->arena, section->statements, section->statement_count,
      &section->statement_capacity, 16U, sizeof(*section->statements));
  if (section->statements == NULL) return -1;
  m68k_ir_statement_init(&copy);
  copy = *statement;
  copy.label_name = NULL;
  copy.comment = NULL;
  if (statement->kind == M68K_STATEMENT_DATA) {
    copy.u.data.data = NULL;
    copy.u.data.expr_text = NULL;
  }
  copy.label_name = arena_strdup(section->arena, statement->label_name);
  if (statement->label_name != NULL && copy.label_name == NULL) return -1;

  copy.comment = arena_strdup(section->arena, statement->comment);
  if (statement->comment != NULL && copy.comment == NULL) return -1;

  if (statement->kind == M68K_STATEMENT_DATA && statement->u.data.size != 0U) {
    copy.u.data.data = (uint8_t *)arena_memdup(section->arena, statement->u.data.data, statement->u.data.size);
    if (copy.u.data.data == NULL) return -1;
  }

  if (statement->kind == M68K_STATEMENT_DATA) {
    copy.u.data.expr_text = arena_strdup(section->arena, statement->u.data.expr_text);
    if (statement->u.data.expr_text != NULL && copy.u.data.expr_text == NULL) return -1;
  }

  section->statements[section->statement_count++] = copy;
  return 0;
}

void m68k_ir_source_file_destroy(M68kSourceFileIR *source_file) {
  size_t index;
  if (source_file == NULL) return;

  for (index = 0; index < source_file->section_count; ++index)
    m68k_ir_section_destroy(&source_file->sections[index]);
  arena_destroy(source_file->arena);
  memset(source_file, 0, sizeof(*source_file));
}

int m68k_ir_source_file_append_section(M68kSourceFileIR *source_file, const M68kSectionIR *section) {
  M68kSectionIR copy;
  size_t statement_index;
  Arena *source_arena;
  if (source_file == NULL || section == NULL) return -1;
  source_arena = source_file->arena;
  if (source_arena == NULL) return -1;
  source_file->sections = (M68kSectionIR *)arena_grow_array(source_arena, source_file->sections,
      source_file->section_count, &source_file->section_capacity, 4U, sizeof(*source_file->sections));
  if (source_file->sections == NULL) return -1;
  m68k_ir_section_init_shared(&copy, source_arena);
  copy.kind = section->kind;
  copy.platform_mem_type = section->platform_mem_type;
  copy.platform_mem_attrs = section->platform_mem_attrs;
  copy.size = section->size;
  copy.data_size = section->data_size;
  copy.name = arena_strdup(source_arena, section->name);
  if (section->name != NULL && copy.name == NULL) return -1;

  for (statement_index = 0; statement_index < section->statement_count; ++statement_index)
    if (m68k_ir_section_append_statement( &copy, &section->statements[statement_index]) != 0) {
      m68k_ir_section_destroy(&copy);
      return -1;
    }

  source_file->sections[source_file->section_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_set_name(M68kSectionAnalysisIR *section_analysis, const char *name) {
  if (section_analysis == NULL) return -1;
  if (name == NULL) {
    section_analysis->section_name = NULL;
    return 0;
  }
  if (section_analysis->arena == NULL) return -1;
  section_analysis->section_name = arena_strdup(section_analysis->arena, name);
  return section_analysis->section_name != NULL ? 0 : -1;
}

void m68k_ir_section_analysis_destroy(M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (section_analysis == NULL) return;
  for (index = 0; index < section_analysis->violation_count; ++index)
    section_analysis->violations[index].message = NULL;
  memset(section_analysis, 0, sizeof(*section_analysis));
}

int m68k_ir_section_analysis_set_code_map(M68kSectionAnalysisIR *section_analysis, const uint8_t *code_start,
    const uint8_t *code_byte, size_t size) {
  if (section_analysis == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  section_analysis->certain_code_start = NULL;
  section_analysis->certain_code_byte = NULL;
  section_analysis->certain_code_size = size;
  if (size == 0U) return 0;

  section_analysis->certain_code_start = (uint8_t *)arena_alloc(section_analysis->arena, size);
  section_analysis->certain_code_byte = (uint8_t *)arena_alloc(section_analysis->arena, size);
  if (section_analysis->certain_code_start == NULL || section_analysis->certain_code_byte == NULL) return -1;

  if (code_start != NULL) memcpy(section_analysis->certain_code_start, code_start, size);
  else                    memset(section_analysis->certain_code_start, 0, size);
  if (code_byte != NULL) memcpy(section_analysis->certain_code_byte, code_byte, size);
  else                   memset(section_analysis->certain_code_byte, 0, size);
  return 0;
}

int m68k_ir_section_analysis_set_blocked_code_map(M68kSectionAnalysisIR *section_analysis,
    const uint8_t *blocked_code_start, size_t size) {
  if (section_analysis == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  section_analysis->blocked_code_start = NULL;
  section_analysis->blocked_code_size = size;
  if (size == 0U) return 0;

  section_analysis->blocked_code_start = (uint8_t *)arena_alloc(section_analysis->arena, size);
  if (section_analysis->blocked_code_start == NULL) return -1;
  if (blocked_code_start != NULL) memcpy(section_analysis->blocked_code_start, blocked_code_start, size);
  else                            memset(section_analysis->blocked_code_start, 0, size);
  return 0;
}

int m68k_ir_section_analysis_set_generated_labels(M68kSectionAnalysisIR *section_analysis, const GeneratedLabelKind *label_kinds,
    const uint8_t *label_flags, size_t size) {
  if (section_analysis == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  section_analysis->generated_label_kinds = NULL;
  section_analysis->generated_label_flags = NULL;
  section_analysis->generated_label_size = size;
  if (size == 0U) return 0;

  section_analysis->generated_label_kinds = (GeneratedLabelKind *)arena_alloc(section_analysis->arena,
      size * sizeof(*section_analysis->generated_label_kinds));
  section_analysis->generated_label_flags = (uint8_t *)arena_alloc(section_analysis->arena, size);
  if (section_analysis->generated_label_kinds == NULL || section_analysis->generated_label_flags == NULL) return -1;

  if (label_kinds != NULL) memcpy(section_analysis->generated_label_kinds, label_kinds,
      size * sizeof(*section_analysis->generated_label_kinds));
  else                     memset(section_analysis->generated_label_kinds, 0,
      size * sizeof(*section_analysis->generated_label_kinds));
  if (label_flags != NULL) memcpy(section_analysis->generated_label_flags, label_flags, size);
  else                     memset(section_analysis->generated_label_flags, 0, size);
  return 0;
}

int m68k_ir_section_analysis_set_word_exprs(M68kSectionAnalysisIR *section_analysis, char *const *word_exprs, size_t count) {
  size_t index;
  if (section_analysis == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  section_analysis->word_exprs = NULL;
  section_analysis->word_expr_count = count;
  if (count == 0U) return 0;

  section_analysis->word_exprs = (char **)arena_calloc(section_analysis->arena, count, sizeof(*section_analysis->word_exprs));
  if (section_analysis->word_exprs == NULL) return -1;
  if (word_exprs == NULL) return 0;
  for (index = 0; index < count; ++index) {
    if (word_exprs[index] == NULL) continue;
    section_analysis->word_exprs[index] = arena_strdup(section_analysis->arena, word_exprs[index]);
    if (section_analysis->word_exprs[index] == NULL) return -1;
  }
  return 0;
}

int m68k_ir_section_analysis_set_long_exprs(M68kSectionAnalysisIR *section_analysis, char *const *long_exprs, size_t count) {
  size_t index;
  if (section_analysis == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  section_analysis->long_exprs = NULL;
  section_analysis->long_expr_count = count;
  if (count == 0U) return 0;

  section_analysis->long_exprs = (char **)arena_calloc(section_analysis->arena, count, sizeof(*section_analysis->long_exprs));
  if (section_analysis->long_exprs == NULL) return -1;
  if (long_exprs == NULL) return 0;
  for (index = 0; index < count; ++index) {
    if (long_exprs[index] == NULL) continue;
    section_analysis->long_exprs[index] = arena_strdup(section_analysis->arena, long_exprs[index]);
    if (section_analysis->long_exprs[index] == NULL) return -1;
  }
  return 0;
}

int m68k_ir_section_analysis_add_label(M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;

  for (index = 0; index < section_analysis->label_count; ++index)
    if (section_analysis->label_offsets[index] == offset) return 0;

  section_analysis->label_offsets = (uint32_t *)arena_grow_array(section_analysis->arena, section_analysis->label_offsets,
      section_analysis->label_count, &section_analysis->label_capacity, 16U, sizeof(*section_analysis->label_offsets));
  if (section_analysis->label_offsets == NULL) return -1;
  section_analysis->label_offsets[section_analysis->label_count++] = offset;
  return 0;
}

int m68k_ir_section_analysis_append_block(M68kSectionAnalysisIR *section_analysis, const M68kCfgBlockIR *block) {
  if (section_analysis == NULL || block == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  section_analysis->blocks = (M68kCfgBlockIR *)arena_grow_array(section_analysis->arena, section_analysis->blocks,
      section_analysis->block_count, &section_analysis->block_capacity, 16U, sizeof(*section_analysis->blocks));
  if (section_analysis->blocks == NULL) return -1;
  section_analysis->blocks[section_analysis->block_count++] = *block;
  return 0;
}

int m68k_ir_section_analysis_append_edge(M68kSectionAnalysisIR *section_analysis, const M68kCfgEdgeIR *edge) {
  if (section_analysis == NULL || edge == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  section_analysis->edges = (M68kCfgEdgeIR *)arena_grow_array(section_analysis->arena, section_analysis->edges,
      section_analysis->edge_count, &section_analysis->edge_capacity, 16U, sizeof(*section_analysis->edges));
  if (section_analysis->edges == NULL) return -1;
  section_analysis->edges[section_analysis->edge_count++] = *edge;
  return 0;
}

int m68k_ir_section_analysis_append_range_ownership(M68kSectionAnalysisIR *section_analysis,
    const M68kRangeOwnershipIR *range) {
  M68kRangeOwnershipIR copy;
  if (section_analysis == NULL || range == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  if (range->end_offset <= range->start_offset) return 0;
  copy = *range;
  copy.role = range->role != NULL ? arena_strdup(section_analysis->arena, range->role) : NULL;
  copy.source_pattern = range->source_pattern != NULL ? arena_strdup(section_analysis->arena,
    range->source_pattern) : NULL;
  if ((range->role != NULL && copy.role == NULL) ||
      (range->source_pattern != NULL && copy.source_pattern == NULL)) {
    return -1;
  }
  section_analysis->range_ownerships = (M68kRangeOwnershipIR *)arena_grow_array(section_analysis->arena,
      section_analysis->range_ownerships, section_analysis->range_ownership_count,
      &section_analysis->range_ownership_capacity, 16U, sizeof(*section_analysis->range_ownerships));
  if (section_analysis->range_ownerships == NULL) return -1;
  section_analysis->range_ownerships[section_analysis->range_ownership_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_append_table_descriptor(M68kSectionAnalysisIR *section_analysis,
    const M68kTableDescriptorIR *descriptor) {
  M68kTableDescriptorIR normalized;
  M68kTableConsumerIR consumer;
  if (section_analysis == NULL || descriptor == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  if (descriptor->end_offset <= descriptor->start_offset || descriptor->entry_size == 0U ||
      descriptor->entry_count == 0U || descriptor->table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN) {
    return 0;
  }
  normalized = *descriptor;
  if (normalized.table_stop_reason_id == M68K_ANALYSIS_TABLE_STOP_REASON_UNKNOWN) {
    normalized.table_stop_reason_id =
      m68k_analysis_table_stop_reason_for_entry_count_proof(normalized.entry_count_proof_id);
  }
  section_analysis->table_descriptors = (M68kTableDescriptorIR *)arena_grow_array(section_analysis->arena,
      section_analysis->table_descriptors, section_analysis->table_descriptor_count,
      &section_analysis->table_descriptor_capacity, 8U, sizeof(*section_analysis->table_descriptors));
  if (section_analysis->table_descriptors == NULL) return -1;
  section_analysis->table_descriptors[section_analysis->table_descriptor_count++] = normalized;
  if (normalized.has_consumer) {
    memset(&consumer, 0, sizeof(consumer));
    consumer.consumer_offset = normalized.consumer_offset;
    consumer.table_section_index = (uint32_t)section_analysis->section_index;
    consumer.table_start_offset = normalized.start_offset;
    consumer.table_end_offset = normalized.end_offset;
    consumer.access_width = normalized.entry_size;
    consumer.entry_count = normalized.entry_count;
    consumer.entry_count_proof_id = normalized.entry_count_proof_id;
    consumer.table_stop_reason_id = normalized.table_stop_reason_id;
    consumer.table_kind_id = normalized.table_kind_id;
    consumer.source_pattern_id = normalized.source_pattern_id;
    consumer.has_index_register = normalized.has_index_register;
    consumer.index_register_kind = normalized.index_register_kind;
    consumer.index_register = normalized.index_register;
    consumer.has_target_register = normalized.has_target_register;
    consumer.target_register_kind = normalized.target_register_kind;
    consumer.target_register = normalized.target_register;
    consumer.has_index_mask_domain = normalized.has_index_mask_domain;
    consumer.index_mask_min = normalized.index_mask_min;
    consumer.index_mask_max = normalized.index_mask_max;
    consumer.has_index_compare_domain = normalized.has_index_compare_domain;
    consumer.index_compare_min = normalized.index_compare_min;
    consumer.index_compare_max = normalized.index_compare_max;
    consumer.index_domain_branch_mnemonic_id = normalized.index_domain_branch_mnemonic_id;
    consumer.has_index_loop_domain = normalized.has_index_loop_domain;
    consumer.index_loop_min = normalized.index_loop_min;
    consumer.index_loop_max = normalized.index_loop_max;
    consumer.index_loop_mnemonic_id = normalized.index_loop_mnemonic_id;
    if (m68k_ir_section_analysis_append_table_consumer(section_analysis, &consumer) != 0) return -1;
  }
  return 0;
}

int m68k_ir_section_analysis_append_table_consumer(M68kSectionAnalysisIR *section_analysis,
    const M68kTableConsumerIR *consumer) {
  size_t index;
  if (section_analysis == NULL || consumer == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  if (consumer->table_end_offset <= consumer->table_start_offset || consumer->access_width == 0U ||
      consumer->table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN) {
    return 0;
  }
  for (index = 0U; index < section_analysis->table_consumer_count; ++index) {
    const M68kTableConsumerIR *existing = &section_analysis->table_consumers[index];
    if (existing->consumer_offset == consumer->consumer_offset &&
        existing->table_section_index == consumer->table_section_index &&
        existing->table_start_offset == consumer->table_start_offset &&
        existing->table_end_offset == consumer->table_end_offset &&
        existing->access_width == consumer->access_width &&
        existing->table_kind_id == consumer->table_kind_id &&
        existing->source_pattern_id == consumer->source_pattern_id) {
      M68kTableConsumerIR *stored = &section_analysis->table_consumers[index];
      if (stored->entry_count_proof_id == M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_UNKNOWN &&
          consumer->entry_count_proof_id != M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_UNKNOWN) {
        stored->entry_count_proof_id = consumer->entry_count_proof_id;
      }
      if (stored->table_stop_reason_id == M68K_ANALYSIS_TABLE_STOP_REASON_UNKNOWN &&
          consumer->table_stop_reason_id != M68K_ANALYSIS_TABLE_STOP_REASON_UNKNOWN) {
        stored->table_stop_reason_id = consumer->table_stop_reason_id;
      }
      if (!stored->has_index_register && consumer->has_index_register) {
        stored->has_index_register = consumer->has_index_register;
        stored->index_register_kind = consumer->index_register_kind;
        stored->index_register = consumer->index_register;
      }
      if (!stored->has_target_register && consumer->has_target_register) {
        stored->has_target_register = consumer->has_target_register;
        stored->target_register_kind = consumer->target_register_kind;
        stored->target_register = consumer->target_register;
      }
      if (!stored->has_index_mask_domain && consumer->has_index_mask_domain) {
        stored->has_index_mask_domain = consumer->has_index_mask_domain;
        stored->index_mask_min = consumer->index_mask_min;
        stored->index_mask_max = consumer->index_mask_max;
      }
      if (!stored->has_index_compare_domain && consumer->has_index_compare_domain) {
        stored->has_index_compare_domain = consumer->has_index_compare_domain;
        stored->index_compare_min = consumer->index_compare_min;
        stored->index_compare_max = consumer->index_compare_max;
        stored->index_domain_branch_mnemonic_id = consumer->index_domain_branch_mnemonic_id;
      }
      if (!stored->has_index_loop_domain && consumer->has_index_loop_domain) {
        stored->has_index_loop_domain = consumer->has_index_loop_domain;
        stored->index_loop_min = consumer->index_loop_min;
        stored->index_loop_max = consumer->index_loop_max;
        stored->index_loop_mnemonic_id = consumer->index_loop_mnemonic_id;
      }
      return 0;
    }
  }
  section_analysis->table_consumers = (M68kTableConsumerIR *)arena_grow_array(section_analysis->arena,
      section_analysis->table_consumers, section_analysis->table_consumer_count,
      &section_analysis->table_consumer_capacity, 8U, sizeof(*section_analysis->table_consumers));
  if (section_analysis->table_consumers == NULL) return -1;
  section_analysis->table_consumers[section_analysis->table_consumer_count++] = *consumer;
  return 0;
}

int m68k_ir_section_analysis_append_table_entry(M68kSectionAnalysisIR *section_analysis,
    const M68kTableEntryIR *entry) {
  size_t index;
  if (section_analysis == NULL || entry == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  if (entry->entry_size == 0U || entry->table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN ||
      entry->target_status == M68K_TABLE_ENTRY_TARGET_STATUS_UNKNOWN) {
    return 0;
  }
  for (index = 0U; index < section_analysis->table_entry_count; ++index) {
    const M68kTableEntryIR *existing = &section_analysis->table_entries[index];
    if (existing->table_start_offset == entry->table_start_offset &&
        existing->entry_index == entry->entry_index &&
        existing->entry_offset == entry->entry_offset &&
        existing->entry_size == entry->entry_size &&
        existing->table_kind_id == entry->table_kind_id) {
      return 0;
    }
  }
  section_analysis->table_entries = (M68kTableEntryIR *)arena_grow_array(section_analysis->arena,
      section_analysis->table_entries, section_analysis->table_entry_count,
      &section_analysis->table_entry_capacity, 16U, sizeof(*section_analysis->table_entries));
  if (section_analysis->table_entries == NULL) return -1;
  section_analysis->table_entries[section_analysis->table_entry_count++] = *entry;
  return 0;
}

int m68k_ir_section_analysis_append_data_reference(M68kSectionAnalysisIR *section_analysis,
    const M68kDataReferenceIR *ref) {
  size_t index;
  if (section_analysis == NULL || ref == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  if (ref->source_kind == M68K_DATA_REFERENCE_SOURCE_UNKNOWN ||
      ref->target_status == M68K_TABLE_ENTRY_TARGET_STATUS_UNKNOWN) {
    return 0;
  }
  for (index = 0U; index < section_analysis->data_reference_count; ++index) {
    M68kDataReferenceIR *existing = &section_analysis->data_references[index];
    if (existing->source_kind == ref->source_kind &&
        existing->source_offset == ref->source_offset &&
        existing->table_start_offset == ref->table_start_offset &&
        existing->table_entry_index == ref->table_entry_index &&
        existing->target_section_index == ref->target_section_index &&
        existing->target_offset == ref->target_offset) {
      existing->evidence_flags |= ref->evidence_flags;
      existing->target_role_flags |= ref->target_role_flags;
      if (existing->target_kind == 0U && ref->target_kind != 0U)
        existing->target_kind = ref->target_kind;
      if (existing->target_table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN && ref->target_table_kind_id != 0U)
        existing->target_table_kind_id = ref->target_table_kind_id;
      if (existing->target_source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_UNKNOWN &&
          ref->target_source_pattern_id != 0U) {
        existing->target_source_pattern_id = ref->target_source_pattern_id;
      }
      return 0;
    }
  }
  section_analysis->data_references = (M68kDataReferenceIR *)arena_grow_array(section_analysis->arena,
      section_analysis->data_references, section_analysis->data_reference_count,
      &section_analysis->data_reference_capacity, 16U, sizeof(*section_analysis->data_references));
  if (section_analysis->data_references == NULL) return -1;
  section_analysis->data_references[section_analysis->data_reference_count++] = *ref;
  return 0;
}

int m68k_ir_section_analysis_append_immediate_text_token(M68kSectionAnalysisIR *section_analysis,
    const M68kImmediateTextTokenIR *token) {
  size_t index;
  if (section_analysis == NULL || token == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  if (token->width == 0U || token->width > 4U || token->text_length == 0U ||
      token->text_length > 4U) {
    return 0;
  }
  for (index = 0U; index < section_analysis->immediate_text_token_count; ++index) {
    const M68kImmediateTextTokenIR *existing = &section_analysis->immediate_text_tokens[index];
    if (existing->source_offset == token->source_offset &&
        existing->operand_index == token->operand_index &&
        existing->width == token->width &&
        existing->value == token->value) {
      return 0;
    }
  }
  section_analysis->immediate_text_tokens =
    (M68kImmediateTextTokenIR *)arena_grow_array(section_analysis->arena,
      section_analysis->immediate_text_tokens, section_analysis->immediate_text_token_count,
      &section_analysis->immediate_text_token_capacity, 16U, sizeof(*section_analysis->immediate_text_tokens));
  if (section_analysis->immediate_text_tokens == NULL) return -1;
  section_analysis->immediate_text_tokens[section_analysis->immediate_text_token_count++] = *token;
  return 0;
}

int m68k_ir_section_analysis_add_violation(M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t kind,
    const char *message) {
  char *copy;
  size_t index;
  if (section_analysis == NULL || message == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;

  for (index = 0; index < section_analysis->violation_count; ++index) {
    const M68kViolationIR *violation = &section_analysis->violations[index];
    if (violation->offset == offset && violation->kind == kind && violation->message != NULL &&
        strcmp(violation->message, message) == 0)
      return 0;
  }

  section_analysis->violations = (M68kViolationIR *)arena_grow_array(section_analysis->arena, section_analysis->violations,
      section_analysis->violation_count, &section_analysis->violation_capacity, 8U, sizeof(*section_analysis->violations));
  if (section_analysis->violations == NULL) return -1;
  copy = arena_strdup(section_analysis->arena, message);
  if (copy == NULL) return -1;

  section_analysis->violations[section_analysis->violation_count].offset = offset;
  section_analysis->violations[section_analysis->violation_count].kind = kind;
  section_analysis->violations[section_analysis->violation_count].message = copy;
  section_analysis->violation_count += 1U;
  section_analysis->violation_offset_lookup = NULL;
  section_analysis->violation_offset_lookup_size = 0U;
  section_analysis->violation_next_lookup = NULL;
  section_analysis->violation_next_lookup_size = 0U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_word_dispatch(M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredWordDispatchIR *dispatch) {
  M68kRecoveredWordDispatchIR copy;
  size_t slot_bytes;
  size_t index;
  if (section_analysis == NULL || dispatch == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_word_dispatch_count; ++index) {
    const M68kRecoveredWordDispatchIR *existing = &section_analysis->recovered_word_dispatches[index];
    if (existing->pattern == dispatch->pattern &&
        existing->table_base == dispatch->table_base &&
        existing->base_target == dispatch->base_target &&
        existing->scanned_bytes == dispatch->scanned_bytes &&
        existing->slot_count == dispatch->slot_count)
      return 0;
  }
  section_analysis->recovered_word_dispatches = (M68kRecoveredWordDispatchIR *)arena_grow_array(section_analysis->arena,
    section_analysis->recovered_word_dispatches, section_analysis->recovered_word_dispatch_count,
    &section_analysis->recovered_word_dispatch_capacity, 8U, sizeof(*section_analysis->recovered_word_dispatches));
  if (section_analysis->recovered_word_dispatches == NULL) return -1;
  memset(&copy, 0, sizeof(copy));
  copy.pattern = dispatch->pattern;
  copy.relative_to_slot = dispatch->relative_to_slot;
  copy.preserve_zero_slots = dispatch->preserve_zero_slots;
  copy.table_base = dispatch->table_base;
  copy.base_target = dispatch->base_target;
  copy.scanned_bytes = dispatch->scanned_bytes;
  copy.slot_count = dispatch->slot_count;
  if (dispatch->slot_count != 0U) {
    slot_bytes = dispatch->slot_count * sizeof(*dispatch->entry_words);
    copy.entry_words = (int16_t *)arena_memdup(section_analysis->arena, dispatch->entry_words, slot_bytes);
    copy.targets = (uint32_t *)arena_memdup(section_analysis->arena, dispatch->targets,
      dispatch->slot_count * sizeof(*dispatch->targets));
    copy.target_valid = (uint8_t *)arena_memdup(section_analysis->arena, dispatch->target_valid, dispatch->slot_count);
    if (copy.entry_words == NULL || copy.targets == NULL || copy.target_valid == NULL) return -1;
  }
  section_analysis->recovered_word_dispatches[section_analysis->recovered_word_dispatch_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_inline_dispatch(M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredInlineDispatchIR *dispatch) {
  M68kRecoveredInlineDispatchIR copy;
  size_t index;
  if (section_analysis == NULL || dispatch == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_inline_dispatch_count; ++index) {
    const M68kRecoveredInlineDispatchIR *existing = &section_analysis->recovered_inline_dispatches[index];
    if (existing->table_base == dispatch->table_base &&
        existing->scanned_bytes == dispatch->scanned_bytes &&
        existing->entry_count == dispatch->entry_count)
      return 0;
  }
  section_analysis->recovered_inline_dispatches = (M68kRecoveredInlineDispatchIR *)arena_grow_array(section_analysis->arena,
    section_analysis->recovered_inline_dispatches, section_analysis->recovered_inline_dispatch_count,
    &section_analysis->recovered_inline_dispatch_capacity, 8U, sizeof(*section_analysis->recovered_inline_dispatches));
  if (section_analysis->recovered_inline_dispatches == NULL) return -1;
  memset(&copy, 0, sizeof(copy));
  copy.table_base = dispatch->table_base;
  copy.scanned_bytes = dispatch->scanned_bytes;
  copy.entry_count = dispatch->entry_count;
  if (dispatch->entry_count != 0U) {
    copy.entry_offsets = (uint32_t *)arena_memdup(section_analysis->arena, dispatch->entry_offsets,
      dispatch->entry_count * sizeof(*dispatch->entry_offsets));
    copy.targets = (uint32_t *)arena_memdup(section_analysis->arena, dispatch->targets,
      dispatch->entry_count * sizeof(*dispatch->targets));
    if (copy.entry_offsets == NULL || copy.targets == NULL) return -1;
  }
  section_analysis->recovered_inline_dispatches[section_analysis->recovered_inline_dispatch_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_string_dispatch(M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredStringDispatchIR *dispatch) {
  M68kRecoveredStringDispatchIR copy;
  size_t index;
  if (section_analysis == NULL || dispatch == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_string_dispatch_count; ++index) {
    const M68kRecoveredStringDispatchIR *existing = &section_analysis->recovered_string_dispatches[index];
    if (existing->table_base == dispatch->table_base &&
        existing->dispatch_site == dispatch->dispatch_site &&
        existing->decoder_entry == dispatch->decoder_entry &&
        existing->entry_count == dispatch->entry_count) {
      return 0;
    }
  }
  section_analysis->recovered_string_dispatches = (M68kRecoveredStringDispatchIR *)arena_grow_array(section_analysis->arena,
    section_analysis->recovered_string_dispatches, section_analysis->recovered_string_dispatch_count,
    &section_analysis->recovered_string_dispatch_capacity, 4U, sizeof(*section_analysis->recovered_string_dispatches));
  if (section_analysis->recovered_string_dispatches == NULL) return -1;
  memset(&copy, 0, sizeof(copy));
  copy.table_base = dispatch->table_base;
  copy.table_end = dispatch->table_end;
  copy.dispatch_site = dispatch->dispatch_site;
  copy.decoder_entry = dispatch->decoder_entry;
  copy.entry_count = dispatch->entry_count;
  if (dispatch->entry_count != 0U) {
    copy.entry_offsets = (uint32_t *)arena_memdup(section_analysis->arena, dispatch->entry_offsets,
      dispatch->entry_count * sizeof(*dispatch->entry_offsets));
    copy.offset_offsets = (uint32_t *)arena_memdup(section_analysis->arena, dispatch->offset_offsets,
      dispatch->entry_count * sizeof(*dispatch->offset_offsets));
    copy.targets = (uint32_t *)arena_memdup(section_analysis->arena, dispatch->targets,
      dispatch->entry_count * sizeof(*dispatch->targets));
    if (copy.entry_offsets == NULL || copy.offset_offsets == NULL || copy.targets == NULL) return -1;
  }
  section_analysis->recovered_string_dispatches[section_analysis->recovered_string_dispatch_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_string_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredStringRefIR *ref) {
  char *copy_text;
  size_t index;
  if (section_analysis == NULL || ref == NULL || ref->text == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_string_ref_count; ++index) {
    const M68kRecoveredStringRefIR *existing = &section_analysis->recovered_string_refs[index];
    if (existing->offset == ref->offset && existing->target == ref->target) return 0;
  }
  section_analysis->recovered_string_refs = (M68kRecoveredStringRefIR *)arena_grow_array(section_analysis->arena,
    section_analysis->recovered_string_refs, section_analysis->recovered_string_ref_count,
    &section_analysis->recovered_string_ref_capacity, 8U, sizeof(*section_analysis->recovered_string_refs));
  if (section_analysis->recovered_string_refs == NULL) return -1;
  copy_text = arena_strdup(section_analysis->arena, ref->text);
  if (copy_text == NULL) return -1;
  section_analysis->recovered_string_refs[section_analysis->recovered_string_ref_count] = *ref;
  section_analysis->recovered_string_refs[section_analysis->recovered_string_ref_count].text = copy_text;
  section_analysis->recovered_string_ref_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_indirect_site(M68kSectionAnalysisIR *section_analysis,
    const M68kRecoveredIndirectSiteIR *site) {
  char *copy_detail = NULL;
  size_t index;
  if (section_analysis == NULL || site == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  if (site->flow_kind == 0U || site->shape == 0U || site->status == 0U) return -1;
  if (site->detail != NULL) {
    copy_detail = arena_strdup(section_analysis->arena, site->detail);
    if (copy_detail == NULL) return -1;
  }
  for (index = 0; index < section_analysis->recovered_indirect_site_count; ++index) {
    M68kRecoveredIndirectSiteIR *existing = &section_analysis->recovered_indirect_sites[index];
    if (existing->offset != site->offset || existing->flow_kind != site->flow_kind) continue;
    existing->shape = site->shape;
    existing->status = site->status;
    existing->has_target = site->has_target;
    existing->has_target_count = site->has_target_count;
    existing->operand_index = site->operand_index;
    existing->source_size = site->source_size;
    existing->has_expression_base = site->has_expression_base;
    existing->has_table_base = site->has_table_base;
    existing->has_table_bounds = site->has_table_bounds;
    existing->table_bounds_status = site->table_bounds_status;
    existing->target = site->target;
    existing->target_count = site->target_count;
    existing->expression_base_offset = site->expression_base_offset;
    existing->table_offset = site->table_offset;
    existing->table_size = site->table_size;
    existing->table_entry_size = site->table_entry_size;
    existing->table_entry_count = site->table_entry_count;
    existing->detail = copy_detail;
    return 0;
  }
  section_analysis->recovered_indirect_sites = (M68kRecoveredIndirectSiteIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_indirect_sites,
    section_analysis->recovered_indirect_site_count, &section_analysis->recovered_indirect_site_capacity,
    8U, sizeof(*section_analysis->recovered_indirect_sites));
  if (section_analysis->recovered_indirect_sites == NULL) return -1;
  section_analysis->recovered_indirect_sites[section_analysis->recovered_indirect_site_count] = *site;
  section_analysis->recovered_indirect_sites[section_analysis->recovered_indirect_site_count].detail = copy_detail;
  section_analysis->recovered_indirect_site_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_orphan_code_signal(M68kSectionAnalysisIR *section_analysis,
    const M68kOrphanCodeSignalIR *signal) {
  M68kOrphanCodeSignalIR copy;
  size_t index;
  if (section_analysis == NULL || signal == NULL) return -1;
  if (section_analysis->arena == NULL || signal->size == 0U || signal->reason == 0U || signal->status == 0U)
    return -1;
  for (index = 0; index < section_analysis->orphan_code_signal_count; ++index) {
    const M68kOrphanCodeSignalIR *existing = &section_analysis->orphan_code_signals[index];
    if (existing->offset == signal->offset &&
        existing->size == signal->size &&
        existing->terminal_offset == signal->terminal_offset &&
        existing->reason == signal->reason &&
        existing->status == signal->status) {
      return 0;
    }
  }
  copy = *signal;
  copy.detail = NULL;
  if (signal->detail != NULL) {
    copy.detail = arena_strdup(section_analysis->arena, signal->detail);
    if (copy.detail == NULL) return -1;
  }
  section_analysis->orphan_code_signals = (M68kOrphanCodeSignalIR *)arena_grow_array(section_analysis->arena,
    section_analysis->orphan_code_signals, section_analysis->orphan_code_signal_count,
    &section_analysis->orphan_code_signal_capacity, 8U, sizeof(*section_analysis->orphan_code_signals));
  if (section_analysis->orphan_code_signals == NULL) return -1;
  section_analysis->orphan_code_signals[section_analysis->orphan_code_signal_count] = copy;
  section_analysis->orphan_code_signal_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_app_slot_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kAppSlotRefIR *ref) {
  M68kAppSlotRefIR copy;
  size_t index;
  if (section_analysis == NULL || ref == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  if (ref->access_kind == M68K_APP_SLOT_ACCESS_NONE || ref->base_reg >= 8U || ref->operand_index >= 4U)
    return -1;
  for (index = 0; index < section_analysis->app_slot_ref_count; ++index) {
    const M68kAppSlotRefIR *existing = &section_analysis->app_slot_refs[index];
    if (existing->offset == ref->offset &&
        existing->displacement == ref->displacement &&
        existing->base_reg == ref->base_reg &&
        existing->operand_index == ref->operand_index &&
        existing->access_kind == ref->access_kind) {
      return 0;
    }
  }
  section_analysis->app_slot_refs = (M68kAppSlotRefIR *)arena_grow_array(section_analysis->arena,
    section_analysis->app_slot_refs, section_analysis->app_slot_ref_count,
    &section_analysis->app_slot_ref_capacity, 8U, sizeof(*section_analysis->app_slot_refs));
  if (section_analysis->app_slot_refs == NULL) return -1;
  copy = *ref;
  copy.symbol_name = NULL;
  if (ref->symbol_name != NULL) {
    copy.symbol_name = arena_strdup(section_analysis->arena, ref->symbol_name);
    if (copy.symbol_name == NULL) return -1;
  }
  section_analysis->app_slot_refs[section_analysis->app_slot_ref_count] = copy;
  section_analysis->app_slot_ref_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_typed_access(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t offset, uint8_t operand_index, uint8_t base_reg, int16_t displacement,
    int16_t field_offset, uint16_t struct_size, uint16_t field_size, const char *root_struct_name,
    const char *owner_struct_name, const char *field_name, const char *field_expr, uint8_t inherited,
    uint8_t nested, uint8_t type_provenance_kind, size_t type_provenance_section_index,
    uint32_t type_provenance_offset) {
  size_t index;
  char *copy_root_struct_name, *copy_owner_struct_name, *copy_field_name, *copy_field_expr;
  M68kRecoveredPlatformTypedAccessIR *new_access;
  M68kPlatformNameRef root_struct_ref = {0};
  M68kPlatformNameRef owner_struct_ref = {0};
  M68kPlatformNameRef field_ref = {0};
  if (section_analysis == NULL || section_analysis->arena == NULL || field_name == NULL || field_expr == NULL)
    return -1;
  root_struct_ref.platform_kind = platform_kind;
  root_struct_ref.domain_kind = M68K_PLATFORM_NAME_STRUCT;
  root_struct_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_STRUCT, root_struct_name);
  owner_struct_ref.platform_kind = platform_kind;
  owner_struct_ref.domain_kind = M68K_PLATFORM_NAME_STRUCT;
  owner_struct_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_STRUCT, owner_struct_name);
  field_ref.platform_kind = platform_kind;
  field_ref.domain_kind = M68K_PLATFORM_NAME_FIELD;
  field_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_FIELD, field_name);
  for (index = 0; index < section_analysis->recovered_platform_typed_access_count; ++index) {
    M68kRecoveredPlatformTypedAccessIR *existing = &section_analysis->recovered_platform_typed_accesses[index];
    if (existing->offset == offset && existing->operand_index == operand_index &&
        existing->base_reg == base_reg && existing->displacement == displacement &&
        existing->field_offset == field_offset && existing->struct_size == struct_size &&
        existing->field_size == field_size && existing->inherited == (uint8_t)(inherited != 0U) &&
        existing->nested == (uint8_t)(nested != 0U) &&
        existing->type_provenance_kind == type_provenance_kind &&
        existing->type_provenance_section_index == type_provenance_section_index &&
        existing->type_provenance_offset == type_provenance_offset &&
        m68k_platform_name_matches(&existing->root_struct_ref, existing->root_struct_name, &root_struct_ref,
          root_struct_name) &&
        m68k_platform_name_matches(&existing->owner_struct_ref, existing->owner_struct_name, &owner_struct_ref,
          owner_struct_name) &&
        m68k_platform_name_matches(&existing->field_ref, existing->field_name, &field_ref, field_name) &&
        strcmp(existing->field_expr != NULL ? existing->field_expr : "", field_expr) == 0) {
      return 0;
    }
  }
  section_analysis->recovered_platform_typed_accesses =
    (M68kRecoveredPlatformTypedAccessIR *)arena_grow_array(section_analysis->arena,
      section_analysis->recovered_platform_typed_accesses,
      section_analysis->recovered_platform_typed_access_count,
      &section_analysis->recovered_platform_typed_access_capacity, 8U,
      sizeof(*section_analysis->recovered_platform_typed_accesses));
  if (section_analysis->recovered_platform_typed_accesses == NULL) return -1;
  copy_root_struct_name = arena_strdup_if_unresolved_name(section_analysis->arena, &root_struct_ref, root_struct_name);
  if (root_struct_name != NULL && !m68k_platform_name_ref_is_set(&root_struct_ref) && copy_root_struct_name == NULL)
    return -1;
  copy_owner_struct_name = arena_strdup_if_unresolved_name(section_analysis->arena, &owner_struct_ref,
    owner_struct_name);
  if (owner_struct_name != NULL && !m68k_platform_name_ref_is_set(&owner_struct_ref) &&
      copy_owner_struct_name == NULL)
    return -1;
  copy_field_name = arena_strdup_if_unresolved_name(section_analysis->arena, &field_ref, field_name);
  if (field_name != NULL && !m68k_platform_name_ref_is_set(&field_ref) && copy_field_name == NULL) return -1;
  copy_field_expr = arena_strdup(section_analysis->arena, field_expr);
  if (copy_field_expr == NULL) return -1;
  new_access = &section_analysis->recovered_platform_typed_accesses[
    section_analysis->recovered_platform_typed_access_count];
  new_access->offset = offset;
  new_access->operand_index = operand_index;
  new_access->base_reg = base_reg;
  new_access->inherited = (uint8_t)(inherited != 0U);
  new_access->nested = (uint8_t)(nested != 0U);
  new_access->displacement = displacement;
  new_access->field_offset = field_offset;
  new_access->struct_size = struct_size;
  new_access->field_size = field_size;
  new_access->type_provenance_kind = type_provenance_kind;
  new_access->type_provenance_section_index = type_provenance_section_index;
  new_access->type_provenance_offset = type_provenance_offset;
  new_access->root_struct_name = copy_root_struct_name;
  new_access->owner_struct_name = copy_owner_struct_name;
  new_access->field_name = copy_field_name;
  new_access->field_expr = copy_field_expr;
  new_access->root_struct_ref = root_struct_ref;
  new_access->owner_struct_ref = owner_struct_ref;
  new_access->field_ref = field_ref;
  section_analysis->recovered_platform_typed_access_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_unresolved_typed_access(
    M68kSectionAnalysisIR *section_analysis, uint8_t platform_kind, uint32_t offset, uint8_t operand_index,
    uint8_t base_reg, int16_t displacement, uint16_t struct_size, const char *root_struct_name,
    uint8_t classification, uint16_t container_candidate_count, const char *container_struct_name,
    const char *container_field_expr, uint8_t refinement_applied, const char *refined_struct_name,
    uint8_t type_provenance_kind, size_t type_provenance_section_index, uint32_t type_provenance_offset) {
  size_t index;
  char *copy_root_struct_name;
  char *copy_container_struct_name = NULL;
  char *copy_container_field_expr = NULL;
  char *copy_refined_struct_name = NULL;
  M68kPlatformNameRef root_struct_ref = {0};
  M68kPlatformNameRef container_struct_ref = {0};
  M68kPlatformNameRef refined_struct_ref = {0};
  const char *candidate_container_struct_name =
    container_struct_name != NULL && container_struct_name[0] != '\0' ? container_struct_name : NULL;
  const char *candidate_container_field_expr =
    container_field_expr != NULL && container_field_expr[0] != '\0' ? container_field_expr : NULL;
  const char *candidate_refined_struct_name =
    refined_struct_name != NULL && refined_struct_name[0] != '\0' ? refined_struct_name : NULL;
  if (section_analysis == NULL || section_analysis->arena == NULL ||
      root_struct_name == NULL || root_struct_name[0] == '\0' ||
      operand_index >= 4U || base_reg >= 8U) {
    return -1;
  }
  root_struct_ref.platform_kind = platform_kind;
  root_struct_ref.domain_kind = M68K_PLATFORM_NAME_STRUCT;
  root_struct_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_STRUCT, root_struct_name);
  if (candidate_container_struct_name != NULL) {
    container_struct_ref.platform_kind = platform_kind;
    container_struct_ref.domain_kind = M68K_PLATFORM_NAME_STRUCT;
    container_struct_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_STRUCT,
      candidate_container_struct_name);
  }
  if (candidate_refined_struct_name != NULL) {
    refined_struct_ref.platform_kind = platform_kind;
    refined_struct_ref.domain_kind = M68K_PLATFORM_NAME_STRUCT;
    refined_struct_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_STRUCT,
      candidate_refined_struct_name);
  }
  for (index = 0; index < section_analysis->recovered_platform_unresolved_typed_access_count; ++index) {
    M68kRecoveredPlatformUnresolvedTypedAccessIR *existing =
      &section_analysis->recovered_platform_unresolved_typed_accesses[index];
    if (existing->offset == offset && existing->operand_index == operand_index &&
        existing->base_reg == base_reg && existing->displacement == displacement &&
        existing->struct_size == struct_size && existing->classification == classification &&
        existing->container_candidate_count == container_candidate_count &&
        existing->refinement_applied == refinement_applied &&
        existing->type_provenance_kind == type_provenance_kind &&
        existing->type_provenance_section_index == type_provenance_section_index &&
        existing->type_provenance_offset == type_provenance_offset &&
        m68k_platform_name_matches(&existing->root_struct_ref, existing->root_struct_name, &root_struct_ref,
          root_struct_name) &&
        m68k_platform_name_matches(&existing->container_struct_ref, existing->container_struct_name,
          &container_struct_ref, candidate_container_struct_name) &&
        m68k_platform_name_matches(&existing->refined_struct_ref, existing->refined_struct_name,
          &refined_struct_ref, candidate_refined_struct_name) &&
        strcmp(existing->container_field_expr != NULL ? existing->container_field_expr : "",
          candidate_container_field_expr != NULL ? candidate_container_field_expr : "") == 0) {
      return 0;
    }
  }
  section_analysis->recovered_platform_unresolved_typed_accesses =
    (M68kRecoveredPlatformUnresolvedTypedAccessIR *)arena_grow_array(section_analysis->arena,
      section_analysis->recovered_platform_unresolved_typed_accesses,
      section_analysis->recovered_platform_unresolved_typed_access_count,
      &section_analysis->recovered_platform_unresolved_typed_access_capacity, 8U,
      sizeof(*section_analysis->recovered_platform_unresolved_typed_accesses));
  if (section_analysis->recovered_platform_unresolved_typed_accesses == NULL) return -1;
  copy_root_struct_name = arena_strdup_if_unresolved_name(section_analysis->arena, &root_struct_ref,
    root_struct_name);
  if (!m68k_platform_name_ref_is_set(&root_struct_ref) && copy_root_struct_name == NULL) return -1;
  if (candidate_container_struct_name != NULL) {
    copy_container_struct_name = arena_strdup_if_unresolved_name(section_analysis->arena, &container_struct_ref,
      candidate_container_struct_name);
    if (!m68k_platform_name_ref_is_set(&container_struct_ref) && copy_container_struct_name == NULL) return -1;
  }
  if (candidate_container_field_expr != NULL) {
    copy_container_field_expr = arena_strdup(section_analysis->arena, candidate_container_field_expr);
    if (copy_container_field_expr == NULL) return -1;
  }
  if (candidate_refined_struct_name != NULL) {
    copy_refined_struct_name = arena_strdup_if_unresolved_name(section_analysis->arena, &refined_struct_ref,
      candidate_refined_struct_name);
    if (!m68k_platform_name_ref_is_set(&refined_struct_ref) && copy_refined_struct_name == NULL) return -1;
  }
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].offset = offset;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].operand_index = operand_index;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].base_reg = base_reg;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].displacement = displacement;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].struct_size = struct_size;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].classification = classification;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].container_candidate_count =
      container_candidate_count;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].refinement_applied = refinement_applied;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].type_provenance_kind = type_provenance_kind;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].type_provenance_section_index =
      type_provenance_section_index;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].type_provenance_offset =
      type_provenance_offset;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].root_struct_name = copy_root_struct_name;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].container_struct_name =
      copy_container_struct_name;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].container_field_expr =
      copy_container_field_expr;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].refined_struct_name =
      copy_refined_struct_name;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].root_struct_ref = root_struct_ref;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].container_struct_ref = container_struct_ref;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].refined_struct_ref = refined_struct_ref;
  section_analysis->recovered_platform_unresolved_typed_access_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_runtime_view(M68kSectionAnalysisIR *section_analysis,
    const M68kRuntimeViewIR *runtime_view) {
  size_t index;
  if (section_analysis == NULL || runtime_view == NULL) return -1;
  if (section_analysis->arena == NULL || runtime_view->size == 0U) return -1;
  for (index = 0; index < section_analysis->runtime_view_count; ++index) {
    const M68kRuntimeViewIR *existing = &section_analysis->runtime_views[index];
    if (existing->runtime_view_id == runtime_view->runtime_view_id ||
        (existing->storage_offset == runtime_view->storage_offset &&
         existing->runtime_address == runtime_view->runtime_address &&
         existing->size == runtime_view->size)) {
      return 0;
    }
  }
  section_analysis->runtime_views = (M68kRuntimeViewIR *)arena_grow_array(section_analysis->arena,
    section_analysis->runtime_views, section_analysis->runtime_view_count,
    &section_analysis->runtime_view_capacity, 4U, sizeof(*section_analysis->runtime_views));
  if (section_analysis->runtime_views == NULL) return -1;
  section_analysis->runtime_views[section_analysis->runtime_view_count] = *runtime_view;
  section_analysis->runtime_view_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_runtime_address_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kRuntimeAddressRefIR *runtime_address_ref) {
  size_t index;
  M68kRuntimeAddressRefIR copy;
  if (section_analysis == NULL || runtime_address_ref == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *existing = &section_analysis->runtime_address_refs[index];
    if (existing->offset == runtime_address_ref->offset &&
        existing->source_size == runtime_address_ref->source_size &&
        existing->operand_index == runtime_address_ref->operand_index &&
        existing->has_target == runtime_address_ref->has_target &&
        existing->target_section_index == runtime_address_ref->target_section_index &&
        existing->target_offset == runtime_address_ref->target_offset &&
        existing->has_runtime_address == runtime_address_ref->has_runtime_address &&
        existing->runtime_address == runtime_address_ref->runtime_address &&
        existing->has_sink_address == runtime_address_ref->has_sink_address &&
        existing->sink_address == runtime_address_ref->sink_address &&
        existing->size == runtime_address_ref->size &&
        existing->data_class_flags == runtime_address_ref->data_class_flags &&
        existing->owner_element_offset == runtime_address_ref->owner_element_offset &&
        text_equal_nullable(existing->owner_kind, runtime_address_ref->owner_kind) &&
        text_equal_nullable(existing->owner_id, runtime_address_ref->owner_id) &&
        text_equal_nullable(existing->owner_layout_id, runtime_address_ref->owner_layout_id) &&
        text_equal_nullable(existing->xref_generation_mode, runtime_address_ref->xref_generation_mode)) {
      return 0;
    }
  }
  copy = *runtime_address_ref;
  copy.data_class = NULL;
  copy.owner_kind = NULL;
  copy.owner_id = NULL;
  copy.owner_layout_id = NULL;
  copy.xref_generation_mode = NULL;
  if (runtime_address_ref->data_class != NULL) {
    copy.data_class = arena_strdup(section_analysis->arena, runtime_address_ref->data_class);
    if (copy.data_class == NULL) return -1;
  }
  if (runtime_address_ref->owner_kind != NULL) {
    copy.owner_kind = arena_strdup(section_analysis->arena, runtime_address_ref->owner_kind);
    if (copy.owner_kind == NULL) return -1;
  }
  if (runtime_address_ref->owner_id != NULL) {
    copy.owner_id = arena_strdup(section_analysis->arena, runtime_address_ref->owner_id);
    if (copy.owner_id == NULL) return -1;
  }
  if (runtime_address_ref->owner_layout_id != NULL) {
    copy.owner_layout_id = arena_strdup(section_analysis->arena, runtime_address_ref->owner_layout_id);
    if (copy.owner_layout_id == NULL) return -1;
  }
  if (runtime_address_ref->xref_generation_mode != NULL) {
    copy.xref_generation_mode = arena_strdup(section_analysis->arena, runtime_address_ref->xref_generation_mode);
    if (copy.xref_generation_mode == NULL) return -1;
  }
  section_analysis->runtime_address_refs = (M68kRuntimeAddressRefIR *)arena_grow_array(section_analysis->arena,
    section_analysis->runtime_address_refs, section_analysis->runtime_address_ref_count,
    &section_analysis->runtime_address_ref_capacity, 8U, sizeof(*section_analysis->runtime_address_refs));
  if (section_analysis->runtime_address_refs == NULL) return -1;
  section_analysis->runtime_address_refs[section_analysis->runtime_address_ref_count] = copy;
  section_analysis->runtime_address_ref_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_address_observation(M68kSectionAnalysisIR *section_analysis,
    const M68kAddressObservationIR *observation) {
  M68kAddressObservationIR copy;
  size_t index;
  if (section_analysis == NULL || observation == NULL || section_analysis->arena == NULL) return -1;
  if (observation->source == M68K_ADDRESS_OBSERVATION_SOURCE_UNKNOWN) return 0;
  for (index = 0U; index < section_analysis->address_observation_count; ++index) {
    const M68kAddressObservationIR *existing = &section_analysis->address_observations[index];
    if (existing->offset == observation->offset &&
        existing->operand_index == observation->operand_index &&
        existing->source == observation->source &&
        existing->address == observation->address &&
        existing->target_section_index == observation->target_section_index &&
        existing->target_offset == observation->target_offset &&
        existing->has_address == observation->has_address &&
        existing->has_target == observation->has_target) {
      return 0;
    }
  }
  section_analysis->address_observations = (M68kAddressObservationIR *)arena_grow_array(section_analysis->arena,
    section_analysis->address_observations, section_analysis->address_observation_count,
    &section_analysis->address_observation_capacity, 8U, sizeof(*section_analysis->address_observations));
  if (section_analysis->address_observations == NULL) return -1;
  copy = *observation;
  copy.symbol_name = NULL;
  if (observation->symbol_name != NULL) {
    copy.symbol_name = arena_strdup(section_analysis->arena, observation->symbol_name);
    if (copy.symbol_name == NULL) return -1;
  }
  section_analysis->address_observations[section_analysis->address_observation_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_append_platform_address_use(M68kSectionAnalysisIR *section_analysis,
    const M68kPlatformAddressUseIR *use) {
  M68kPlatformAddressUseIR copy;
  size_t index;
  if (section_analysis == NULL || use == NULL || section_analysis->arena == NULL) return -1;
  if (use->use_shape == M68K_PLATFORM_ADDRESS_USE_SHAPE_UNKNOWN) return 0;
  for (index = 0U; index < section_analysis->platform_address_use_count; ++index) {
    const M68kPlatformAddressUseIR *existing = &section_analysis->platform_address_uses[index];
    if (existing->offset == use->offset &&
        existing->operand_index == use->operand_index &&
        existing->address == use->address &&
        existing->effective_address == use->effective_address &&
        existing->access_kind == use->access_kind &&
        existing->use_shape == use->use_shape) {
      return 0;
    }
  }
  section_analysis->platform_address_uses = (M68kPlatformAddressUseIR *)arena_grow_array(
    section_analysis->arena, section_analysis->platform_address_uses,
    section_analysis->platform_address_use_count, &section_analysis->platform_address_use_capacity,
    8U, sizeof(*section_analysis->platform_address_uses));
  if (section_analysis->platform_address_uses == NULL) return -1;
  copy = *use;
  copy.symbol_name = NULL;
  if (use->symbol_name != NULL) {
    copy.symbol_name = arena_strdup(section_analysis->arena, use->symbol_name);
    if (copy.symbol_name == NULL) return -1;
  }
  section_analysis->platform_address_uses[section_analysis->platform_address_use_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_append_platform_semantic_use(M68kSectionAnalysisIR *section_analysis,
    const M68kPlatformSemanticUseIR *use) {
  M68kPlatformSemanticUseIR copy;
  size_t index;
  if (section_analysis == NULL || use == NULL || section_analysis->arena == NULL) return -1;
  if (use->kind == M68K_PLATFORM_SEMANTIC_USE_UNKNOWN) return 0;
  for (index = 0U; index < section_analysis->platform_semantic_use_count; ++index) {
    const M68kPlatformSemanticUseIR *existing = &section_analysis->platform_semantic_uses[index];
    if (existing->offset == use->offset &&
        existing->size == use->size &&
        existing->kind == use->kind &&
        existing->source_pattern_id == use->source_pattern_id &&
        existing->has_target == use->has_target &&
        existing->target_section_index == use->target_section_index &&
        existing->target_offset == use->target_offset &&
        existing->has_secondary_target == use->has_secondary_target &&
        existing->secondary_target_section_index == use->secondary_target_section_index &&
        existing->secondary_target_offset == use->secondary_target_offset &&
        text_equal_nullable(existing->note_text, use->note_text)) {
      return 0;
    }
  }
  section_analysis->platform_semantic_uses = (M68kPlatformSemanticUseIR *)arena_grow_array(
    section_analysis->arena, section_analysis->platform_semantic_uses,
    section_analysis->platform_semantic_use_count, &section_analysis->platform_semantic_use_capacity,
    8U, sizeof(*section_analysis->platform_semantic_uses));
  if (section_analysis->platform_semantic_uses == NULL) return -1;
  copy = *use;
  copy.note_text = NULL;
  if (use->note_text != NULL) {
    copy.note_text = arena_strdup(section_analysis->arena, use->note_text);
    if (copy.note_text == NULL) return -1;
  }
  section_analysis->platform_semantic_uses[section_analysis->platform_semantic_use_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_append_code_start_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kCodeStartRefIR *code_start_ref) {
  size_t index;
  if (section_analysis == NULL || code_start_ref == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *existing = &section_analysis->code_start_refs[index];
    if (existing->offset == code_start_ref->offset &&
        existing->reason == code_start_ref->reason &&
        existing->evidence_kind == code_start_ref->evidence_kind &&
        existing->source_section_index == code_start_ref->source_section_index &&
        existing->source_offset == code_start_ref->source_offset &&
        existing->has_runtime_address == code_start_ref->has_runtime_address &&
        existing->runtime_address == code_start_ref->runtime_address) {
      return 0;
    }
  }
  section_analysis->code_start_refs = (M68kCodeStartRefIR *)arena_grow_array(section_analysis->arena,
    section_analysis->code_start_refs, section_analysis->code_start_ref_count,
    &section_analysis->code_start_ref_capacity, 8U, sizeof(*section_analysis->code_start_refs));
  if (section_analysis->code_start_refs == NULL) return -1;
  section_analysis->code_start_refs[section_analysis->code_start_ref_count] = *code_start_ref;
  section_analysis->code_start_ref_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_source_quality_diagnostic(M68kSectionAnalysisIR *section_analysis,
    const M68kSourceQualityDiagnosticIR *diagnostic) {
  M68kSourceQualityDiagnosticIR copy;
  size_t index;
  if (section_analysis == NULL || diagnostic == NULL || section_analysis->arena == NULL) return -1;
  if (diagnostic->kind == M68K_SOURCE_QUALITY_DIAGNOSTIC_UNKNOWN) return 0;
  for (index = 0U; index < section_analysis->source_quality_diagnostic_count; ++index) {
    if (source_quality_diagnostic_same_location_kind_local(
        &section_analysis->source_quality_diagnostics[index], diagnostic)) {
      return 0;
    }
  }
  section_analysis->source_quality_diagnostics =
    (M68kSourceQualityDiagnosticIR *)arena_grow_array(section_analysis->arena,
      section_analysis->source_quality_diagnostics, section_analysis->source_quality_diagnostic_count,
      &section_analysis->source_quality_diagnostic_capacity, 8U,
      sizeof(*section_analysis->source_quality_diagnostics));
  if (section_analysis->source_quality_diagnostics == NULL) return -1;
  memset(&copy, 0, sizeof(copy));
  if (copy_source_quality_diagnostic_local(section_analysis->arena, &copy, diagnostic) != 0) return -1;
  section_analysis->source_quality_diagnostics[section_analysis->source_quality_diagnostic_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_append_symbol_origin(M68kSectionAnalysisIR *section_analysis,
    const M68kSymbolOriginIR *origin) {
  M68kSymbolOriginIR copy;
  size_t index;
  if (section_analysis == NULL || origin == NULL || section_analysis->arena == NULL) return -1;
  if (origin->origin_kind == M68K_SYMBOL_ORIGIN_UNKNOWN ||
      origin->symbol_name == NULL || origin->symbol_name[0] == '\0') return 0;
  for (index = 0U; index < section_analysis->symbol_origin_count; ++index) {
    const M68kSymbolOriginIR *existing = &section_analysis->symbol_origins[index];
    if (existing->offset == origin->offset &&
        existing->source_section_index == origin->source_section_index &&
        existing->source_offset == origin->source_offset &&
        existing->origin_kind == origin->origin_kind &&
        strcmp(existing->symbol_name, origin->symbol_name) == 0) {
      return 0;
    }
  }
  section_analysis->symbol_origins = (M68kSymbolOriginIR *)arena_grow_array(section_analysis->arena,
    section_analysis->symbol_origins, section_analysis->symbol_origin_count,
    &section_analysis->symbol_origin_capacity, 8U, sizeof(*section_analysis->symbol_origins));
  if (section_analysis->symbol_origins == NULL) return -1;
  copy = *origin;
  copy.symbol_name = arena_strdup(section_analysis->arena, origin->symbol_name);
  if (copy.symbol_name == NULL) return -1;
  section_analysis->symbol_origins[section_analysis->symbol_origin_count++] = copy;
  return 0;
}

int m68k_ir_section_analysis_append_expected_symbol_access(M68kSectionAnalysisIR *section_analysis,
    const M68kExpectedSymbolAccessIR *access) {
  M68kExpectedSymbolAccessIR copy;
  size_t index;
  const char *producer;
  if (section_analysis == NULL || access == NULL || section_analysis->arena == NULL) return -1;
  if (access->access_kind == M68K_EXPECTED_SYMBOL_ACCESS_UNKNOWN ||
      access->symbol_name == NULL || access->symbol_name[0] == '\0') return 0;
  producer = access->producer != NULL && access->producer[0] != '\0' ? access->producer : "unknown";
  for (index = 0U; index < section_analysis->expected_symbol_access_count; ++index) {
    const M68kExpectedSymbolAccessIR *existing = &section_analysis->expected_symbol_accesses[index];
    if (existing->offset == access->offset &&
        existing->target_section_index == access->target_section_index &&
        existing->target_offset == access->target_offset &&
        existing->operand_index == access->operand_index &&
        existing->access_kind == access->access_kind &&
        strcmp(existing->symbol_name, access->symbol_name) == 0) {
      return expected_symbol_access_append_producer(section_analysis,
        &section_analysis->expected_symbol_accesses[index], producer);
    }
  }
  section_analysis->expected_symbol_accesses =
    (M68kExpectedSymbolAccessIR *)arena_grow_array(section_analysis->arena,
      section_analysis->expected_symbol_accesses, section_analysis->expected_symbol_access_count,
      &section_analysis->expected_symbol_access_capacity, 8U,
      sizeof(*section_analysis->expected_symbol_accesses));
  if (section_analysis->expected_symbol_accesses == NULL) return -1;
  copy = *access;
  copy.symbol_name = arena_strdup(section_analysis->arena, access->symbol_name);
  if (copy.symbol_name == NULL) return -1;
  copy.producer = arena_strdup(section_analysis->arena, producer);
  if (copy.producer == NULL) return -1;
  section_analysis->expected_symbol_accesses[section_analysis->expected_symbol_access_count++] = copy;
  return 0;
}

int m68k_ir_render_evidence_create(M68kRenderEvidenceIR *evidence) {
  if (evidence == NULL) return -1;
  memset(evidence, 0, sizeof(*evidence));
  evidence->arena = arena_create(M68K_IR_RENDER_EVIDENCE_ARENA_SIZE);
  return evidence->arena != NULL ? 0 : -1;
}

void m68k_ir_render_evidence_destroy(M68kRenderEvidenceIR *evidence) {
  if (evidence == NULL) return;
  arena_destroy(evidence->arena);
  memset(evidence, 0, sizeof(*evidence));
}

static M68kRenderEvidenceSectionIR *render_evidence_section_by_index_mutable(
    M68kRenderEvidenceIR *evidence, uint32_t section_index) {
  size_t index;
  if (evidence == NULL) return NULL;
  for (index = 0U; index < evidence->section_count; ++index) {
    if (evidence->sections[index].section_index == section_index) return &evidence->sections[index];
  }
  return NULL;
}

const M68kRenderEvidenceSectionIR *m68k_ir_render_evidence_section_by_index(
    const M68kRenderEvidenceIR *evidence, uint32_t section_index) {
  size_t index;
  if (evidence == NULL) return NULL;
  for (index = 0U; index < evidence->section_count; ++index) {
    if (evidence->sections[index].section_index == section_index) return &evidence->sections[index];
  }
  return NULL;
}

static M68kRenderEvidenceSectionIR *render_evidence_get_or_add_section(
    M68kRenderEvidenceIR *evidence, uint32_t section_index) {
  M68kRenderEvidenceSectionIR *section;
  if (evidence == NULL || evidence->arena == NULL) return NULL;
  section = render_evidence_section_by_index_mutable(evidence, section_index);
  if (section != NULL) return section;
  evidence->sections = (M68kRenderEvidenceSectionIR *)arena_grow_array(evidence->arena,
    evidence->sections, evidence->section_count, &evidence->section_capacity, 4U,
    sizeof(*evidence->sections));
  if (evidence->sections == NULL) return NULL;
  section = &evidence->sections[evidence->section_count++];
  memset(section, 0, sizeof(*section));
  section->section_index = section_index;
  return section;
}

int m68k_ir_render_evidence_append_rendered_symbol_access(M68kRenderEvidenceIR *evidence,
    uint32_t section_index, const M68kRenderedSymbolAccessIR *access) {
  M68kRenderEvidenceSectionIR *section;
  M68kRenderedSymbolAccessIR copy;
  size_t index;
  if (evidence == NULL || evidence->arena == NULL || access == NULL) return -1;
  if (access->access_kind == M68K_RENDERED_SYMBOL_ACCESS_UNKNOWN ||
      access->symbol_name == NULL || access->symbol_name[0] == '\0') return 0;
  section = render_evidence_get_or_add_section(evidence, section_index);
  if (section == NULL) return -1;
  for (index = 0U; index < section->rendered_symbol_access_count; ++index) {
    const M68kRenderedSymbolAccessIR *existing = &section->rendered_symbol_accesses[index];
    if (existing->offset == access->offset &&
        existing->target_section_index == access->target_section_index &&
        existing->target_offset == access->target_offset &&
        existing->operand_index == access->operand_index &&
        existing->access_kind == access->access_kind &&
        existing->comment_only == access->comment_only &&
        strcmp(existing->symbol_name, access->symbol_name) == 0) {
      return 0;
    }
  }
  section->rendered_symbol_accesses = (M68kRenderedSymbolAccessIR *)arena_grow_array(evidence->arena,
    section->rendered_symbol_accesses, section->rendered_symbol_access_count,
    &section->rendered_symbol_access_capacity, 8U, sizeof(*section->rendered_symbol_accesses));
  if (section->rendered_symbol_accesses == NULL) return -1;
  copy = *access;
  copy.symbol_name = arena_strdup(evidence->arena, access->symbol_name);
  if (copy.symbol_name == NULL) return -1;
  section->rendered_symbol_accesses[section->rendered_symbol_access_count++] = copy;
  return 0;
}

int m68k_ir_render_evidence_append_all(M68kRenderEvidenceIR *evidence,
    const M68kRenderEvidenceIR *source) {
  size_t section_index;
  if (evidence == NULL || evidence->arena == NULL || source == NULL) return -1;
  for (section_index = 0U; section_index < source->section_count; ++section_index) {
    const M68kRenderEvidenceSectionIR *section = &source->sections[section_index];
    size_t access_index;
    for (access_index = 0U; access_index < section->rendered_symbol_access_count; ++access_index) {
      if (m68k_ir_render_evidence_append_rendered_symbol_access(evidence, section->section_index,
          &section->rendered_symbol_accesses[access_index]) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

int m68k_ir_section_analysis_append_code_origin(M68kSectionAnalysisIR *section_analysis,
    const M68kCodeOriginIR *origin) {
  size_t index;
  if (section_analysis == NULL || origin == NULL || section_analysis->arena == NULL) return -1;
  if (origin->origin_class == M68K_CODE_ORIGIN_UNKNOWN) return 0;
  for (index = 0U; index < section_analysis->code_origin_count; ++index) {
    const M68kCodeOriginIR *existing = &section_analysis->code_origins[index];
    if (existing->offset == origin->offset &&
        existing->origin_class == origin->origin_class &&
        existing->reason == origin->reason &&
        existing->evidence_kind == origin->evidence_kind &&
        existing->source_section_index == origin->source_section_index &&
        existing->source_offset == origin->source_offset) {
      return 0;
    }
  }
  section_analysis->code_origins = (M68kCodeOriginIR *)arena_grow_array(section_analysis->arena,
    section_analysis->code_origins, section_analysis->code_origin_count,
    &section_analysis->code_origin_capacity, 8U, sizeof(*section_analysis->code_origins));
  if (section_analysis->code_origins == NULL) return -1;
  section_analysis->code_origins[section_analysis->code_origin_count++] = *origin;
  return 0;
}

int m68k_ir_section_analysis_append_accepted_code_run(M68kSectionAnalysisIR *section_analysis,
    const M68kAcceptedCodeRunIR *run) {
  size_t index;
  if (section_analysis == NULL || run == NULL || section_analysis->arena == NULL) return -1;
  if (run->end_offset <= run->start_offset) return 0;
  for (index = 0U; index < section_analysis->accepted_code_run_count; ++index) {
    const M68kAcceptedCodeRunIR *existing = &section_analysis->accepted_code_runs[index];
    if (existing->start_offset == run->start_offset && existing->end_offset == run->end_offset) return 0;
  }
  section_analysis->accepted_code_runs = (M68kAcceptedCodeRunIR *)arena_grow_array(section_analysis->arena,
    section_analysis->accepted_code_runs, section_analysis->accepted_code_run_count,
    &section_analysis->accepted_code_run_capacity, 8U, sizeof(*section_analysis->accepted_code_runs));
  if (section_analysis->accepted_code_runs == NULL) return -1;
  section_analysis->accepted_code_runs[section_analysis->accepted_code_run_count++] = *run;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_base_slot(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, int16_t displacement, const char *base_name) {
  size_t index;
  char *copy_name;
  M68kPlatformNameRef base_ref = {0};
  if (section_analysis == NULL || base_name == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  base_ref.platform_kind = platform_kind;
  base_ref.domain_kind = M68K_PLATFORM_NAME_BASE;
  base_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_BASE, base_name);
  for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
    M68kRecoveredPlatformBaseSlotIR *existing = &section_analysis->recovered_platform_base_slots[index];
    if (existing->displacement == displacement) {
      if (m68k_platform_name_matches(&existing->base_ref, existing->base_name, &base_ref, base_name)) return 0;
      return -1;
    }
  }
  section_analysis->recovered_platform_base_slots = (M68kRecoveredPlatformBaseSlotIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_platform_base_slots,
    section_analysis->recovered_platform_base_slot_count, &section_analysis->recovered_platform_base_slot_capacity,
    8U, sizeof(*section_analysis->recovered_platform_base_slots));
  if (section_analysis->recovered_platform_base_slots == NULL) return -1;
  copy_name = arena_strdup_if_unresolved_name(section_analysis->arena, &base_ref, base_name);
  if (base_name != NULL && !m68k_platform_name_ref_is_set(&base_ref) && copy_name == NULL) return -1;
  section_analysis->recovered_platform_base_slots[section_analysis->recovered_platform_base_slot_count].displacement =
    displacement;
  section_analysis->recovered_platform_base_slots[section_analysis->recovered_platform_base_slot_count].base_name =
    copy_name;
  section_analysis->recovered_platform_base_slots[section_analysis->recovered_platform_base_slot_count].base_ref =
    base_ref;
  section_analysis->recovered_platform_base_slot_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_effect(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t offset, uint8_t kind, uint8_t reg_kind, uint8_t reg_index, int16_t displacement,
    int16_t field_disp, const char *base_name, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value) {
  size_t index;
  char *copy_name, *copy_symbol_name, *copy_type_name;
  char *copy_semantic_kind, *copy_value_domain_name;
  M68kPlatformNameRef base_ref = {0};
  M68kPlatformNameRef symbol_ref = {0};
  M68kPlatformNameRef type_ref = {0};
  M68kPlatformNameRef semantic_kind_ref = {0};
  M68kPlatformNameRef value_domain_ref = {0};
  if (section_analysis == NULL || kind == M68K_PLATFORM_EFFECT_NONE) return -1;
  if (section_analysis->arena == NULL) return -1;
  base_ref.platform_kind = platform_kind;
  base_ref.domain_kind = M68K_PLATFORM_NAME_BASE;
  base_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_BASE, base_name);
  symbol_ref.platform_kind = platform_kind;
  symbol_ref.domain_kind = M68K_PLATFORM_NAME_SYMBOL;
  symbol_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_SYMBOL, symbol_name);
  type_ref.platform_kind = platform_kind;
  type_ref.domain_kind = M68K_PLATFORM_NAME_TYPE;
  type_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_TYPE, type_name);
  semantic_kind_ref.platform_kind = platform_kind;
  semantic_kind_ref.domain_kind = M68K_PLATFORM_NAME_SEMANTIC_KIND;
  semantic_kind_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_SEMANTIC_KIND, semantic_kind);
  value_domain_ref.platform_kind = platform_kind;
  value_domain_ref.domain_kind = M68K_PLATFORM_NAME_VALUE_DOMAIN;
  value_domain_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_VALUE_DOMAIN, value_domain_name);
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    M68kRecoveredPlatformEffectIR *existing = &section_analysis->recovered_platform_effects[index];
    if (existing->offset == offset && existing->kind == kind && existing->reg_kind == reg_kind &&
        existing->reg_index == reg_index && existing->displacement == displacement && existing->field_disp == field_disp) {
      const M68kPlatformNameRef *existing_base_ref = NULL;
      const M68kPlatformNameRef *existing_symbol_ref = NULL;
      const M68kPlatformNameRef *existing_type_ref = NULL;
      const M68kPlatformNameRef *existing_semantic_kind_ref = NULL;
      const M68kPlatformNameRef *existing_value_domain_ref = NULL;
      const char *existing_base_name = NULL, *existing_symbol_name = NULL;
      const char *existing_type_name = NULL, *existing_semantic_kind = NULL;
      const char *existing_value_domain_name = NULL;
      uint8_t existing_has_constant_value = 0U;
      int32_t existing_constant_value = 0;
      if (existing->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG ||
          existing->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT ||
          existing->kind == M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT) {
        existing_base_ref = &existing->payload.named_base.base_ref;
        existing_base_name = existing->payload.named_base.base_name;
      } else if (existing->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
        existing_symbol_ref = &existing->payload.code_ptr.field_symbol_ref;
        existing_type_ref = &existing->payload.code_ptr.owner_type_ref;
        existing_semantic_kind_ref = &existing->payload.code_ptr.semantic_kind_ref;
        existing_symbol_name = existing->payload.code_ptr.field_symbol_name;
        existing_type_name = existing->payload.code_ptr.owner_type_name;
        existing_semantic_kind = existing->payload.code_ptr.semantic_kind;
      } else if (existing->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ||
          existing->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
          existing->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) {
        existing_base_ref = &existing->payload.typed.context_ref;
        existing_symbol_ref = &existing->payload.typed.symbol_ref;
        existing_type_ref = &existing->payload.typed.type_ref;
        existing_semantic_kind_ref = &existing->payload.typed.semantic_kind_ref;
        existing_value_domain_ref = &existing->payload.typed.value_domain_ref;
        existing_base_name = existing->payload.typed.context_name;
        existing_symbol_name = existing->payload.typed.symbol_name;
        existing_type_name = existing->payload.typed.type_name;
        existing_semantic_kind = existing->payload.typed.semantic_kind;
        existing_value_domain_name = existing->payload.typed.value_domain_name;
        existing_has_constant_value = existing->payload.typed.has_constant_value;
        existing_constant_value = existing->payload.typed.constant_value;
      }
      if (m68k_platform_name_matches(existing_base_ref, existing_base_name, &base_ref, base_name) &&
          m68k_platform_name_matches(existing_symbol_ref, existing_symbol_name, &symbol_ref, symbol_name) &&
          m68k_platform_name_matches(existing_type_ref, existing_type_name, &type_ref, type_name) &&
          m68k_platform_name_matches(existing_semantic_kind_ref, existing_semantic_kind,
            &semantic_kind_ref, semantic_kind) &&
          m68k_platform_name_matches(existing_value_domain_ref, existing_value_domain_name,
            &value_domain_ref, value_domain_name) &&
          existing_has_constant_value == has_constant_value &&
          (!has_constant_value || existing_constant_value == constant_value)) return 0;
      return -1;
    }
  }
  section_analysis->recovered_platform_effects = (M68kRecoveredPlatformEffectIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_platform_effects,
    section_analysis->recovered_platform_effect_count, &section_analysis->recovered_platform_effect_capacity,
    8U, sizeof(*section_analysis->recovered_platform_effects));
  if (section_analysis->recovered_platform_effects == NULL) return -1;
  copy_name = arena_strdup_if_unresolved_name(section_analysis->arena, &base_ref, base_name);
  if (base_name != NULL && !m68k_platform_name_ref_is_set(&base_ref) && copy_name == NULL) return -1;
  copy_symbol_name = arena_strdup_if_unresolved_name(section_analysis->arena, &symbol_ref, symbol_name);
  if (symbol_name != NULL && !m68k_platform_name_ref_is_set(&symbol_ref) && copy_symbol_name == NULL) return -1;
  copy_type_name = arena_strdup_if_unresolved_name(section_analysis->arena, &type_ref, type_name);
  if (type_name != NULL && !m68k_platform_name_ref_is_set(&type_ref) && copy_type_name == NULL) return -1;
  copy_semantic_kind = arena_strdup_if_unresolved_name(section_analysis->arena, &semantic_kind_ref, semantic_kind);
  if (semantic_kind != NULL && !m68k_platform_name_ref_is_set(&semantic_kind_ref) && copy_semantic_kind == NULL)
    return -1;
  copy_value_domain_name = arena_strdup_if_unresolved_name(section_analysis->arena, &value_domain_ref, value_domain_name);
  if (value_domain_name != NULL && !m68k_platform_name_ref_is_set(&value_domain_ref) && copy_value_domain_name == NULL)
    return -1;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].offset = offset;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].kind = kind;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].reg_kind = reg_kind;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].reg_index = reg_index;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].displacement =
    displacement;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].field_disp =
    field_disp;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].target_section_index =
    SIZE_MAX;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].target_offset =
    UINT32_MAX;
  memset(&section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload, 0,
    sizeof(section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload));
  if (kind == M68K_PLATFORM_EFFECT_SET_BASE_REG || kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT ||
      kind == M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT) {
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.named_base.base_name =
      copy_name;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.named_base.base_ref =
      base_ref;
  } else if (kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.code_ptr.field_symbol_name =
      copy_symbol_name;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.code_ptr.owner_type_name =
      copy_type_name;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.code_ptr.semantic_kind =
      copy_semantic_kind;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.code_ptr.field_symbol_ref =
      symbol_ref;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.code_ptr.owner_type_ref =
      type_ref;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.code_ptr.semantic_kind_ref =
      semantic_kind_ref;
  } else if (kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
      kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) {
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.symbol_name =
      copy_symbol_name;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.context_name =
      copy_name;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.type_name =
      copy_type_name;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.semantic_kind =
      copy_semantic_kind;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.value_domain_name =
      copy_value_domain_name;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.symbol_ref =
      symbol_ref;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.context_ref =
      base_ref;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.type_ref =
      type_ref;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.semantic_kind_ref =
      semantic_kind_ref;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.value_domain_ref =
      value_domain_ref;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.has_constant_value =
      has_constant_value;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.constant_value =
      constant_value;
  }
  section_analysis->recovered_platform_effect_count += 1U;
  section_analysis->recovered_platform_effect_lookup = NULL;
  section_analysis->recovered_platform_effect_lookup_size = 0U;
  section_analysis->recovered_platform_effect_next_lookup = NULL;
  section_analysis->recovered_platform_effect_next_lookup_size = 0U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_global_base_slot_effect(
    M68kSectionAnalysisIR *section_analysis, uint8_t platform_kind, uint32_t offset, size_t target_section_index,
    uint32_t target_offset, const char *base_name) {
  size_t index;
  if (section_analysis == NULL || target_section_index == SIZE_MAX || target_offset == UINT32_MAX ||
      base_name == NULL || base_name[0] == '\0') {
    return -1;
  }
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    const char *existing_base_name;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT || effect->offset != offset ||
        effect->target_section_index != target_section_index || effect->target_offset != target_offset)
      continue;
    existing_base_name = m68k_platform_name_ref_display_text(&effect->payload.named_base.base_ref,
      effect->payload.named_base.base_name);
    if (existing_base_name != NULL && strcmp(existing_base_name, base_name) == 0) return 0;
    return -1;
  }
  if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, platform_kind, offset,
        M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT, 0U, 0U, INT16_MIN, INT16_MIN, base_name, NULL, NULL, NULL,
        NULL, 0U, 0) != 0)
    return -1;
  for (index = section_analysis->recovered_platform_effect_count; index > 0U; --index) {
    M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index - 1U];
    const char *existing_base_name;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT || effect->offset != offset) continue;
    existing_base_name = m68k_platform_name_ref_display_text(&effect->payload.named_base.base_ref,
      effect->payload.named_base.base_name);
    if (existing_base_name == NULL || strcmp(existing_base_name, base_name) != 0) continue;
    effect->target_section_index = target_section_index;
    effect->target_offset = target_offset;
    return 0;
  }
  return -1;
}

int m68k_ir_section_analysis_append_recovered_platform_typed_global_slot_effect(
    M68kSectionAnalysisIR *section_analysis, uint8_t platform_kind, uint32_t offset, size_t target_section_index,
    uint32_t target_offset, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name) {
  size_t index;
  if (section_analysis == NULL || target_section_index == SIZE_MAX || target_offset == UINT32_MAX ||
      (type_name == NULL && symbol_name == NULL && semantic_kind == NULL && value_domain_name == NULL)) {
    return -1;
  }
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    const char *existing_type_name, *existing_symbol_name, *existing_semantic_kind, *existing_value_domain_name;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT || effect->offset != offset ||
        effect->target_section_index != target_section_index || effect->target_offset != target_offset)
      continue;
    existing_symbol_name = m68k_platform_name_ref_display_text(&effect->payload.typed.symbol_ref,
      effect->payload.typed.symbol_name);
    existing_type_name = m68k_platform_name_ref_display_text(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    existing_semantic_kind = m68k_platform_name_ref_display_text(&effect->payload.typed.semantic_kind_ref,
      effect->payload.typed.semantic_kind);
    existing_value_domain_name = m68k_platform_name_ref_display_text(
      &effect->payload.typed.value_domain_ref, effect->payload.typed.value_domain_name);
    if (text_equal_nullable(existing_symbol_name, symbol_name) && text_equal_nullable(existing_type_name, type_name) &&
        text_equal_nullable(existing_semantic_kind, semantic_kind) &&
        text_equal_nullable(existing_value_domain_name, value_domain_name)) {
      return 0;
    }
    return -1;
  }
  if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis, platform_kind, offset,
        M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT, 0U, 0U, INT16_MIN, INT16_MIN, NULL, symbol_name, type_name,
        semantic_kind, value_domain_name, 0U, 0) != 0)
    return -1;
  for (index = section_analysis->recovered_platform_effect_count; index > 0U; --index) {
    M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index - 1U];
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT || effect->offset != offset) continue;
    effect->target_section_index = target_section_index;
    effect->target_offset = target_offset;
    return 0;
  }
  return -1;
}

int m68k_ir_section_analysis_append_recovered_local_call_summary(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t target_offset, uint8_t effect_kind, uint8_t reg_kind, uint8_t reg_index,
    uint8_t success_reg_kind, uint8_t success_reg_index, uint8_t success_value_known, int32_t success_reg_value,
    const char *base_name, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value) {
  size_t index;
  char *copy_base_name, *copy_symbol_name, *copy_type_name, *copy_semantic_kind, *copy_value_domain_name;
  M68kPlatformNameRef base_ref = {0}, symbol_ref = {0}, type_ref = {0};
  M68kPlatformNameRef semantic_kind_ref = {0}, value_domain_ref = {0};
  if (section_analysis == NULL || effect_kind == M68K_PLATFORM_EFFECT_NONE) return -1;
  if (section_analysis->arena == NULL) return -1;
  base_ref.platform_kind = platform_kind;
  base_ref.domain_kind = M68K_PLATFORM_NAME_BASE;
  base_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_BASE, base_name);
  symbol_ref.platform_kind = platform_kind;
  symbol_ref.domain_kind = M68K_PLATFORM_NAME_SYMBOL;
  symbol_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_SYMBOL, symbol_name);
  type_ref.platform_kind = platform_kind;
  type_ref.domain_kind = M68K_PLATFORM_NAME_TYPE;
  type_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_TYPE, type_name);
  semantic_kind_ref.platform_kind = platform_kind;
  semantic_kind_ref.domain_kind = M68K_PLATFORM_NAME_SEMANTIC_KIND;
  semantic_kind_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_SEMANTIC_KIND, semantic_kind);
  value_domain_ref.platform_kind = platform_kind;
  value_domain_ref.domain_kind = M68K_PLATFORM_NAME_VALUE_DOMAIN;
  value_domain_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_VALUE_DOMAIN, value_domain_name);
  for (index = 0; index < section_analysis->recovered_local_call_summary_count; ++index) {
    M68kRecoveredLocalCallSummaryIR *existing = &section_analysis->recovered_local_call_summaries[index];
    const char *existing_base_name = NULL, *existing_symbol_name = NULL, *existing_type_name = NULL;
    const char *existing_semantic_kind = NULL, *existing_value_domain_name = NULL;
    const M68kPlatformNameRef *existing_base_ref = &existing->payload.named_base.base_ref;
    const M68kPlatformNameRef *existing_symbol_ref = &existing->payload.typed.symbol_ref;
    uint8_t existing_has_constant_value = 0U;
    int32_t existing_constant_value = 0;
    if (existing->target_offset != target_offset || existing->effect_kind != effect_kind ||
        existing->reg_kind != reg_kind || existing->reg_index != reg_index ||
        existing->success_reg_kind != success_reg_kind || existing->success_reg_index != success_reg_index ||
        existing->success_value_known != success_value_known || existing->success_reg_value != success_reg_value) {
      continue;
    }
    if (existing->effect_kind == M68K_PLATFORM_EFFECT_SET_BASE_REG) {
      existing_base_name = existing->payload.named_base.base_name;
    } else if (existing->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
      existing_base_name = existing->payload.typed.context_name;
      existing_symbol_name = existing->payload.typed.symbol_name;
      existing_base_ref = &existing->payload.typed.context_ref;
      existing_type_name = existing->payload.typed.type_name;
      existing_semantic_kind = existing->payload.typed.semantic_kind;
      existing_value_domain_name = existing->payload.typed.value_domain_name;
      existing_has_constant_value = existing->payload.typed.has_constant_value;
      existing_constant_value = existing->payload.typed.constant_value;
    }
    if (m68k_platform_name_matches(existing_base_ref, existing_base_name, &base_ref, base_name) &&
        m68k_platform_name_matches(existing_symbol_ref, existing_symbol_name, &symbol_ref, symbol_name) &&
        m68k_platform_name_matches(&existing->payload.typed.type_ref, existing_type_name, &type_ref, type_name) &&
        m68k_platform_name_matches(&existing->payload.typed.semantic_kind_ref, existing_semantic_kind,
          &semantic_kind_ref, semantic_kind) &&
        m68k_platform_name_matches(&existing->payload.typed.value_domain_ref, existing_value_domain_name,
          &value_domain_ref, value_domain_name) &&
        existing_has_constant_value == has_constant_value &&
        (!has_constant_value || existing_constant_value == constant_value)) {
      return 0;
    }
    return -1;
  }
  section_analysis->recovered_local_call_summaries = (M68kRecoveredLocalCallSummaryIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_local_call_summaries,
    section_analysis->recovered_local_call_summary_count, &section_analysis->recovered_local_call_summary_capacity,
    8U, sizeof(*section_analysis->recovered_local_call_summaries));
  if (section_analysis->recovered_local_call_summaries == NULL) return -1;
  copy_base_name = arena_strdup_if_unresolved_name(section_analysis->arena, &base_ref, base_name);
  if (base_name != NULL && !m68k_platform_name_ref_is_set(&base_ref) && copy_base_name == NULL) return -1;
  copy_symbol_name = arena_strdup_if_unresolved_name(section_analysis->arena, &symbol_ref, symbol_name);
  if (symbol_name != NULL && !m68k_platform_name_ref_is_set(&symbol_ref) && copy_symbol_name == NULL) return -1;
  copy_type_name = arena_strdup_if_unresolved_name(section_analysis->arena, &type_ref, type_name);
  if (type_name != NULL && !m68k_platform_name_ref_is_set(&type_ref) && copy_type_name == NULL) return -1;
  copy_semantic_kind = arena_strdup_if_unresolved_name(section_analysis->arena, &semantic_kind_ref, semantic_kind);
  if (semantic_kind != NULL && !m68k_platform_name_ref_is_set(&semantic_kind_ref) && copy_semantic_kind == NULL)
    return -1;
  copy_value_domain_name = arena_strdup_if_unresolved_name(section_analysis->arena, &value_domain_ref, value_domain_name);
  if (value_domain_name != NULL && !m68k_platform_name_ref_is_set(&value_domain_ref) && copy_value_domain_name == NULL)
    return -1;
  section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].target_offset =
    target_offset;
  section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].effect_kind =
    effect_kind;
  section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].reg_kind =
    reg_kind;
  section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].reg_index =
    reg_index;
  section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].success_reg_kind =
    success_reg_kind;
  section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].success_reg_index =
    success_reg_index;
  section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].success_value_known =
    success_value_known;
  section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].success_reg_value =
    success_reg_value;
  memset(&section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].payload,
    0, sizeof(section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count].payload));
  if (effect_kind == M68K_PLATFORM_EFFECT_SET_BASE_REG) {
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.named_base.base_name = copy_base_name;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.named_base.base_ref = base_ref;
  } else if (effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.context_name = copy_base_name;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.symbol_name = copy_symbol_name;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.type_name = copy_type_name;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.semantic_kind = copy_semantic_kind;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.value_domain_name = copy_value_domain_name;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.context_ref = base_ref;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.symbol_ref = symbol_ref;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.type_ref = type_ref;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.semantic_kind_ref = semantic_kind_ref;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.value_domain_ref = value_domain_ref;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.has_constant_value = has_constant_value;
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.constant_value = constant_value;
  }
  section_analysis->recovered_local_call_summary_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_function_arg(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t function_offset, uint16_t stack_offset, uint8_t reg_kind, uint8_t reg_index,
    const char *context_name, const char *symbol_name, const char *type_name, const char *semantic_kind,
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value, uint8_t has_source_operand,
    uint32_t source_offset, uint8_t source_reg_kind, uint8_t source_reg_index, int16_t source_displacement) {
  size_t index;
  char *copy_context_name, *copy_symbol_name, *copy_type_name, *copy_semantic_kind, *copy_value_domain_name;
  M68kPlatformNameRef context_ref = {0}, symbol_ref = {0}, type_ref = {0};
  M68kPlatformNameRef semantic_kind_ref = {0}, value_domain_ref = {0};
  if (section_analysis == NULL || stack_offset == 0U || reg_index >= 8U || source_reg_index >= 8U) return -1;
  if (section_analysis->arena == NULL) return -1;
  context_ref.platform_kind = platform_kind;
  context_ref.domain_kind = M68K_PLATFORM_NAME_BASE;
  context_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_BASE, context_name);
  symbol_ref.platform_kind = platform_kind;
  symbol_ref.domain_kind = M68K_PLATFORM_NAME_SYMBOL;
  symbol_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_SYMBOL, symbol_name);
  type_ref.platform_kind = platform_kind;
  type_ref.domain_kind = M68K_PLATFORM_NAME_TYPE;
  type_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_TYPE, type_name);
  semantic_kind_ref.platform_kind = platform_kind;
  semantic_kind_ref.domain_kind = M68K_PLATFORM_NAME_SEMANTIC_KIND;
  semantic_kind_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_SEMANTIC_KIND, semantic_kind);
  value_domain_ref.platform_kind = platform_kind;
  value_domain_ref.domain_kind = M68K_PLATFORM_NAME_VALUE_DOMAIN;
  value_domain_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_VALUE_DOMAIN, value_domain_name);
  for (index = 0; index < section_analysis->recovered_function_arg_count; ++index) {
    M68kRecoveredFunctionArgIR *existing = &section_analysis->recovered_function_args[index];
    const char *existing_context_name = m68k_platform_name_ref_display_text(&existing->typed.context_ref,
      existing->typed.context_name);
    const char *existing_symbol_name = m68k_platform_name_ref_display_text(&existing->typed.symbol_ref,
      existing->typed.symbol_name);
    const char *existing_type_name = m68k_platform_name_ref_display_text(&existing->typed.type_ref,
      existing->typed.type_name);
    const char *existing_semantic_kind = m68k_platform_name_ref_display_text(
      &existing->typed.semantic_kind_ref, existing->typed.semantic_kind);
    const char *existing_value_domain_name = m68k_platform_name_ref_display_text(
      &existing->typed.value_domain_ref, existing->typed.value_domain_name);
    if (existing->function_offset != function_offset || existing->stack_offset != stack_offset ||
        existing->reg_kind != reg_kind || existing->reg_index != reg_index)
      continue;
    if (m68k_platform_name_matches(&existing->typed.context_ref, existing_context_name, &context_ref, context_name) &&
        m68k_platform_name_matches(&existing->typed.symbol_ref, existing_symbol_name, &symbol_ref, symbol_name) &&
        m68k_platform_name_matches(&existing->typed.type_ref, existing_type_name, &type_ref, type_name) &&
        m68k_platform_name_matches(&existing->typed.semantic_kind_ref, existing_semantic_kind,
          &semantic_kind_ref, semantic_kind) &&
        m68k_platform_name_matches(&existing->typed.value_domain_ref, existing_value_domain_name,
          &value_domain_ref, value_domain_name) &&
        existing->typed.has_constant_value == has_constant_value &&
        (!has_constant_value || existing->typed.constant_value == constant_value) &&
        existing->has_source_operand == has_source_operand &&
        (!has_source_operand || (existing->source_offset == source_offset &&
          existing->source_reg_kind == source_reg_kind && existing->source_reg_index == source_reg_index &&
          existing->source_displacement == source_displacement))) {
      return 0;
    }
    return -1;
  }
  section_analysis->recovered_function_args = (M68kRecoveredFunctionArgIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_function_args,
    section_analysis->recovered_function_arg_count, &section_analysis->recovered_function_arg_capacity,
    8U, sizeof(*section_analysis->recovered_function_args));
  if (section_analysis->recovered_function_args == NULL) return -1;
  copy_context_name = arena_strdup_if_unresolved_name(section_analysis->arena, &context_ref, context_name);
  if (context_name != NULL && !m68k_platform_name_ref_is_set(&context_ref) && copy_context_name == NULL) return -1;
  copy_symbol_name = arena_strdup_if_unresolved_name(section_analysis->arena, &symbol_ref, symbol_name);
  if (symbol_name != NULL && !m68k_platform_name_ref_is_set(&symbol_ref) && copy_symbol_name == NULL) return -1;
  copy_type_name = arena_strdup_if_unresolved_name(section_analysis->arena, &type_ref, type_name);
  if (type_name != NULL && !m68k_platform_name_ref_is_set(&type_ref) && copy_type_name == NULL) return -1;
  copy_semantic_kind = arena_strdup_if_unresolved_name(section_analysis->arena, &semantic_kind_ref, semantic_kind);
  if (semantic_kind != NULL && !m68k_platform_name_ref_is_set(&semantic_kind_ref) && copy_semantic_kind == NULL)
    return -1;
  copy_value_domain_name = arena_strdup_if_unresolved_name(section_analysis->arena, &value_domain_ref, value_domain_name);
  if (value_domain_name != NULL && !m68k_platform_name_ref_is_set(&value_domain_ref) && copy_value_domain_name == NULL)
    return -1;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].function_offset =
    function_offset;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].stack_offset = stack_offset;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].reg_kind = reg_kind;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].reg_index = reg_index;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].has_source_operand =
    has_source_operand;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].source_offset =
    source_offset;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].source_reg_kind =
    source_reg_kind;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].source_reg_index =
    source_reg_index;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].source_displacement =
    source_displacement;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.context_name =
    copy_context_name;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.symbol_name =
    copy_symbol_name;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.type_name =
    copy_type_name;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.semantic_kind =
    copy_semantic_kind;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.value_domain_name =
    copy_value_domain_name;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.context_ref =
    context_ref;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.symbol_ref =
    symbol_ref;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.type_ref = type_ref;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.semantic_kind_ref =
    semantic_kind_ref;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.value_domain_ref =
    value_domain_ref;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.has_constant_value =
    has_constant_value;
  section_analysis->recovered_function_args[section_analysis->recovered_function_arg_count].typed.constant_value =
    constant_value;
  section_analysis->recovered_function_arg_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_call(M68kSectionAnalysisIR *section_analysis,
    uint8_t platform_kind, uint32_t offset, uint8_t kind, const char *symbol_name, uint8_t note_kind, const char *note_base_name,
    const char *note_symbol_name, uint8_t note_reg, int16_t note_disp, int16_t note_field_disp,
    uint8_t note_stack_cleanup_known, uint16_t note_stack_cleanup_bytes, uint8_t note_return_kind,
    const char *available_since, const char *fd_version) {
  size_t index;
  char *copy_name, *copy_base_name, *copy_note_symbol_name;
  char *copy_available_since, *copy_fd_version;
  M68kPlatformNameRef symbol_ref = {0}, note_base_ref = {0}, note_symbol_ref = {0};
  uint16_t available_since_version = 0U;
  if (section_analysis == NULL) return -1;
  if (symbol_name == NULL && note_kind == M68K_PLATFORM_CALL_NOTE_NONE) return -1;
  if (section_analysis->arena == NULL) return -1;
  symbol_ref.platform_kind = platform_kind;
  symbol_ref.domain_kind = M68K_PLATFORM_NAME_SYMBOL;
  symbol_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_SYMBOL, symbol_name);
  note_base_ref.platform_kind = platform_kind;
  if (platform_kind == M68K_PLATFORM_BACKEND_ATARI_ST) {
    note_base_ref.domain_kind = M68K_PLATFORM_NAME_FAMILY;
  } else if (note_kind == M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD) {
    note_base_ref.domain_kind = M68K_PLATFORM_NAME_TYPE;
  } else {
    note_base_ref.domain_kind = M68K_PLATFORM_NAME_BASE;
  }
  note_base_ref.id = m68k_platform_name_id_from_text(platform_kind, note_base_ref.domain_kind, note_base_name);
  note_symbol_ref.platform_kind = platform_kind;
  note_symbol_ref.domain_kind = M68K_PLATFORM_NAME_SYMBOL;
  note_symbol_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_SYMBOL, note_symbol_name);
  if (platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK && available_since != NULL && available_since[0] != '\0') {
    available_since_version = (uint16_t)amiga_os_normalize_compatibility_version_enum(available_since);
  }
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    M68kRecoveredPlatformCallIR *existing = &section_analysis->recovered_platform_calls[index];
    if (existing->offset == offset && existing->kind == kind) {
      if (m68k_platform_name_matches(&existing->symbol_ref, existing->symbol_name, &symbol_ref, symbol_name) &&
            existing->note_kind == note_kind &&
            existing->note_reg == note_reg &&
            existing->note_stack_cleanup_known == note_stack_cleanup_known &&
            existing->note_return_kind == note_return_kind &&
            existing->note_disp == note_disp &&
            existing->note_field_disp == note_field_disp &&
            existing->note_stack_cleanup_bytes == note_stack_cleanup_bytes &&
            m68k_platform_name_matches(&existing->note_base_ref, existing->note_base_name, &note_base_ref, note_base_name) &&
            m68k_platform_name_matches(&existing->note_symbol_ref, existing->note_symbol_name,
              &note_symbol_ref, note_symbol_name) &&
            (existing->available_since_version == available_since_version ||
                ((existing->available_since == NULL && available_since == NULL) ||
                (existing->available_since != NULL && available_since != NULL &&
                 strcmp(existing->available_since, available_since) == 0))) &&
            ((existing->fd_version == NULL && fd_version == NULL) ||
                (existing->fd_version != NULL && fd_version != NULL &&
                 strcmp(existing->fd_version, fd_version) == 0))) return 0;
      return -1;
    }
  }
  section_analysis->recovered_platform_calls = (M68kRecoveredPlatformCallIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_platform_calls,
    section_analysis->recovered_platform_call_count, &section_analysis->recovered_platform_call_capacity,
    8U, sizeof(*section_analysis->recovered_platform_calls));
  if (section_analysis->recovered_platform_calls == NULL) return -1;
  copy_name = arena_strdup_if_unresolved_name(section_analysis->arena, &symbol_ref, symbol_name);
  if (symbol_name != NULL && !m68k_platform_name_ref_is_set(&symbol_ref) && copy_name == NULL) return -1;
  copy_base_name = arena_strdup_if_unresolved_name(section_analysis->arena, &note_base_ref, note_base_name);
  if (note_base_name != NULL && !m68k_platform_name_ref_is_set(&note_base_ref) && copy_base_name == NULL) return -1;
  copy_note_symbol_name = arena_strdup_if_unresolved_name(section_analysis->arena, &note_symbol_ref, note_symbol_name);
  if (note_symbol_name != NULL && !m68k_platform_name_ref_is_set(&note_symbol_ref) && copy_note_symbol_name == NULL)
    return -1;
  copy_available_since = available_since != NULL ? arena_strdup(section_analysis->arena, available_since) : NULL;
  if (available_since != NULL && copy_available_since == NULL) return -1;
  copy_fd_version = fd_version != NULL ? arena_strdup(section_analysis->arena, fd_version) : NULL;
  if (fd_version != NULL && copy_fd_version == NULL) return -1;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].offset = offset;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].kind = kind;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_kind = note_kind;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_reg = note_reg;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_stack_cleanup_known =
      note_stack_cleanup_known;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_return_kind =
      note_return_kind;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_disp = note_disp;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_field_disp =
      note_field_disp;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_stack_cleanup_bytes =
      note_stack_cleanup_bytes;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].symbol_name = copy_name;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].symbol_ref = symbol_ref;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_base_name =
    copy_base_name;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_base_ref =
    note_base_ref;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_symbol_name =
    copy_note_symbol_name;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_symbol_ref =
    note_symbol_ref;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].available_since =
    copy_available_since;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].available_since_version =
    available_since_version;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].fd_version =
    copy_fd_version;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].device_name = NULL;
  section_analysis->recovered_platform_call_count += 1U;
  section_analysis->recovered_platform_call_lookup = NULL;
  section_analysis->recovered_platform_call_lookup_size = 0U;
  section_analysis->recovered_platform_call_next_lookup = NULL;
  section_analysis->recovered_platform_call_next_lookup_size = 0U;
  return 0;
}

int m68k_ir_section_analysis_set_recovered_platform_call_device_name(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind, const char *device_name) {
  size_t index;
  char *copy_name;
  if (section_analysis == NULL || device_name == NULL || device_name[0] == '\0') return 0;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
    if (call->offset != offset || call->kind != kind) continue;
    if (call->device_name != NULL) return strcmp(call->device_name, device_name) == 0 ? 0 : -1;
    copy_name = arena_strdup(section_analysis->arena, device_name);
    if (copy_name == NULL) return -1;
    call->device_name = copy_name;
    return 0;
  }
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_disk_read(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint32_t command_value, const char *command_name, uint32_t disk_offset,
    uint32_t byte_length, uint32_t destination_addr, uint8_t source_kind) {
  size_t index;
  char *copy_command_name;
  if (section_analysis == NULL || command_name == NULL || command_name[0] == '\0' ||
      m68k_recovered_platform_transfer_source_kind_name(source_kind) == NULL) {
    return -1;
  }
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_platform_disk_read_count; ++index) {
    const M68kRecoveredPlatformDiskReadIR *existing = &section_analysis->recovered_platform_disk_reads[index];
    if (existing->offset == offset &&
        existing->command_value == command_value &&
        existing->disk_offset == disk_offset &&
        existing->byte_length == byte_length &&
        existing->destination_addr == destination_addr &&
        existing->command_name != NULL && strcmp(existing->command_name, command_name) == 0 &&
        existing->source_kind == source_kind) {
      return 0;
    }
  }
  section_analysis->recovered_platform_disk_reads =
    (M68kRecoveredPlatformDiskReadIR *)arena_grow_array(section_analysis->arena,
      section_analysis->recovered_platform_disk_reads,
      section_analysis->recovered_platform_disk_read_count,
      &section_analysis->recovered_platform_disk_read_capacity,
      4U, sizeof(*section_analysis->recovered_platform_disk_reads));
  if (section_analysis->recovered_platform_disk_reads == NULL) return -1;
  copy_command_name = arena_strdup(section_analysis->arena, command_name);
  if (copy_command_name == NULL) return -1;
  section_analysis->recovered_platform_disk_reads[section_analysis->recovered_platform_disk_read_count].offset = offset;
  section_analysis->recovered_platform_disk_reads[section_analysis->recovered_platform_disk_read_count].command_value =
    command_value;
  section_analysis->recovered_platform_disk_reads[section_analysis->recovered_platform_disk_read_count].disk_offset =
    disk_offset;
  section_analysis->recovered_platform_disk_reads[section_analysis->recovered_platform_disk_read_count].byte_length =
    byte_length;
  section_analysis->recovered_platform_disk_reads[section_analysis->recovered_platform_disk_read_count].destination_addr =
    destination_addr;
  section_analysis->recovered_platform_disk_reads[section_analysis->recovered_platform_disk_read_count].command_name =
    copy_command_name;
  section_analysis->recovered_platform_disk_reads[section_analysis->recovered_platform_disk_read_count].source_kind =
    source_kind;
  section_analysis->recovered_platform_disk_read_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_runtime_copy(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint32_t source_addr, uint32_t destination_addr, uint32_t byte_length,
    uint32_t handoff_addr, uint8_t source_kind) {
  size_t index;
  if (section_analysis == NULL || m68k_recovered_platform_transfer_source_kind_name(source_kind) == NULL ||
      byte_length == 0U) {
    return -1;
  }
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_platform_runtime_copy_count; ++index) {
    const M68kRecoveredPlatformRuntimeCopyIR *existing = &section_analysis->recovered_platform_runtime_copies[index];
    if (existing->offset == offset &&
        existing->source_addr == source_addr &&
        existing->destination_addr == destination_addr &&
        existing->byte_length == byte_length &&
        existing->handoff_addr == handoff_addr &&
        existing->source_kind == source_kind) {
      return 0;
    }
  }
  section_analysis->recovered_platform_runtime_copies =
    (M68kRecoveredPlatformRuntimeCopyIR *)arena_grow_array(section_analysis->arena,
      section_analysis->recovered_platform_runtime_copies,
      section_analysis->recovered_platform_runtime_copy_count,
      &section_analysis->recovered_platform_runtime_copy_capacity,
      4U, sizeof(*section_analysis->recovered_platform_runtime_copies));
  if (section_analysis->recovered_platform_runtime_copies == NULL) return -1;
  section_analysis->recovered_platform_runtime_copies[section_analysis->recovered_platform_runtime_copy_count].offset =
    offset;
  section_analysis->recovered_platform_runtime_copies[section_analysis->recovered_platform_runtime_copy_count]
    .source_addr = source_addr;
  section_analysis->recovered_platform_runtime_copies[section_analysis->recovered_platform_runtime_copy_count]
    .destination_addr = destination_addr;
  section_analysis->recovered_platform_runtime_copies[section_analysis->recovered_platform_runtime_copy_count]
    .byte_length = byte_length;
  section_analysis->recovered_platform_runtime_copies[section_analysis->recovered_platform_runtime_copy_count]
    .handoff_addr = handoff_addr;
  section_analysis->recovered_platform_runtime_copies[section_analysis->recovered_platform_runtime_copy_count]
    .source_kind = source_kind;
  section_analysis->recovered_platform_runtime_copy_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_media_transfer(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, size_t path_section_index, uint32_t path_offset, uint32_t destination_addr,
    uint32_t source_size, const char *path, const char *source_sha256, uint8_t source_kind) {
  size_t index;
  char *copy_path;
  char *copy_sha256 = NULL;
  if (section_analysis == NULL || path == NULL || path[0] == '\0' ||
      m68k_recovered_platform_transfer_source_kind_name(source_kind) == NULL) {
    return -1;
  }
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_platform_media_transfer_count; ++index) {
    const M68kRecoveredPlatformMediaTransferIR *existing =
      &section_analysis->recovered_platform_media_transfers[index];
    if (existing->offset == offset &&
        existing->path_section_index == path_section_index &&
        existing->path_offset == path_offset &&
        existing->destination_addr == destination_addr &&
        existing->source_size == source_size &&
        existing->path != NULL && strcmp(existing->path, path) == 0 &&
        ((existing->source_sha256 == NULL && (source_sha256 == NULL || source_sha256[0] == '\0')) ||
         (existing->source_sha256 != NULL && source_sha256 != NULL &&
          strcmp(existing->source_sha256, source_sha256) == 0)) &&
        existing->source_kind == source_kind) {
      return 0;
    }
  }
  section_analysis->recovered_platform_media_transfers =
    (M68kRecoveredPlatformMediaTransferIR *)arena_grow_array(section_analysis->arena,
      section_analysis->recovered_platform_media_transfers,
      section_analysis->recovered_platform_media_transfer_count,
      &section_analysis->recovered_platform_media_transfer_capacity,
      4U, sizeof(*section_analysis->recovered_platform_media_transfers));
  if (section_analysis->recovered_platform_media_transfers == NULL) return -1;
  copy_path = arena_strdup(section_analysis->arena, path);
  if (copy_path == NULL) return -1;
  if (source_sha256 != NULL && source_sha256[0] != '\0') {
    copy_sha256 = arena_strdup(section_analysis->arena, source_sha256);
    if (copy_sha256 == NULL) return -1;
  }
  section_analysis->recovered_platform_media_transfers[section_analysis->recovered_platform_media_transfer_count]
    .offset = offset;
  section_analysis->recovered_platform_media_transfers[section_analysis->recovered_platform_media_transfer_count]
    .path_section_index = path_section_index;
  section_analysis->recovered_platform_media_transfers[section_analysis->recovered_platform_media_transfer_count]
    .path_offset =
    path_offset;
  section_analysis->recovered_platform_media_transfers[section_analysis->recovered_platform_media_transfer_count]
    .destination_addr = destination_addr;
  section_analysis->recovered_platform_media_transfers[section_analysis->recovered_platform_media_transfer_count]
    .source_size = source_size;
  section_analysis->recovered_platform_media_transfers[section_analysis->recovered_platform_media_transfer_count]
    .path = copy_path;
  section_analysis->recovered_platform_media_transfers[section_analysis->recovered_platform_media_transfer_count]
    .source_sha256 = copy_sha256;
  section_analysis->recovered_platform_media_transfers[section_analysis->recovered_platform_media_transfer_count]
    .source_kind =
    source_kind;
  section_analysis->recovered_platform_media_transfer_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_direct_section_call(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, size_t target_section_index, uint32_t target_offset) {
  size_t index;
  if (section_analysis == NULL || section_analysis->arena == NULL) return -1;
  for (index = 0U; index < section_analysis->recovered_direct_section_call_count; ++index) {
    M68kRecoveredDirectSectionCallIR *existing = &section_analysis->recovered_direct_section_calls[index];
    if (existing->offset == offset &&
        existing->target_section_index == target_section_index &&
        existing->target_offset == target_offset) {
      return 0;
    }
  }
  section_analysis->recovered_direct_section_calls = (M68kRecoveredDirectSectionCallIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_direct_section_calls,
    section_analysis->recovered_direct_section_call_count, &section_analysis->recovered_direct_section_call_capacity,
    8U, sizeof(*section_analysis->recovered_direct_section_calls));
  if (section_analysis->recovered_direct_section_calls == NULL) return -1;
  section_analysis->recovered_direct_section_calls[section_analysis->recovered_direct_section_call_count].offset = offset;
  section_analysis->recovered_direct_section_calls[section_analysis->recovered_direct_section_call_count].target_section_index =
    target_section_index;
  section_analysis->recovered_direct_section_calls[section_analysis->recovered_direct_section_call_count].target_offset =
    target_offset;
  section_analysis->recovered_direct_section_call_count += 1U;
  return 0;
}

void m68k_ir_source_analysis_destroy(M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  if (source_analysis == NULL)
    return;
  for (index = 0; index < source_analysis->section_count; ++index) {
    m68k_ir_section_analysis_destroy(&source_analysis->sections[index]);
  }
  m68k_analysis_policy_destroy(&source_analysis->policy);
  arena_destroy(source_analysis->arena);
  memset(source_analysis, 0, sizeof(*source_analysis));
}

int m68k_ir_source_analysis_append_platform_storage_layout(M68kSourceAnalysisIR *source_analysis,
    const M68kPlatformStorageLayoutIR *layout) {
  size_t index;
  Arena *arena;
  if (source_analysis == NULL || layout == NULL || layout->layout_kind == M68K_PLATFORM_STORAGE_LAYOUT_NONE ||
      layout->region_kind == M68K_PLATFORM_STORAGE_REGION_NONE || layout->size == 0U || layout->base_reg >= 8U) {
    return -1;
  }
  arena = source_analysis->arena;
  if (arena == NULL) return -1;
  for (index = 0U; index < source_analysis->platform_storage_layout_count; ++index) {
    const M68kPlatformStorageLayoutIR *existing = &source_analysis->platform_storage_layouts[index];
    if (existing->platform_kind == layout->platform_kind &&
        existing->layout_kind == layout->layout_kind &&
        existing->region_kind == layout->region_kind &&
        existing->base_reg == layout->base_reg &&
        existing->start == layout->start &&
        existing->size == layout->size &&
        existing->owner_resource_id == layout->owner_resource_id) {
      return 0;
    }
  }
  source_analysis->platform_storage_layouts = (M68kPlatformStorageLayoutIR *)arena_grow_array(arena,
    source_analysis->platform_storage_layouts, source_analysis->platform_storage_layout_count,
    &source_analysis->platform_storage_layout_capacity, 4U, sizeof(*source_analysis->platform_storage_layouts));
  if (source_analysis->platform_storage_layouts == NULL) return -1;
  source_analysis->platform_storage_layouts[source_analysis->platform_storage_layout_count] = *layout;
  source_analysis->platform_storage_layout_count += 1U;
  return 0;
}

static int source_analysis_structured_item_range_overlaps_accepted_code(const M68kSourceAnalysisIR *source_analysis,
    const M68kAnalysisStructuredDataItem *item) {
  const M68kSectionAnalysisIR *section;
  uint32_t cursor;
  if (source_analysis == NULL || item == NULL || !item->has_section_index ||
      item->section_index >= source_analysis->section_count || item->size == 0U) {
    return 0;
  }
  section = &source_analysis->sections[item->section_index];
  if (section->certain_code_byte == NULL || item->offset >= section->certain_code_size) return 0;
  for (cursor = 0U; cursor < item->size && cursor < section->certain_code_size - item->offset; ++cursor) {
    if (section->certain_code_byte[item->offset + cursor] != 0U) return 1;
  }
  return 0;
}

static int source_analysis_table_kind_is_code_dispatch(uint8_t table_kind_id) {
  return table_kind_id == M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH ||
    table_kind_id == M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH;
}

static uint32_t source_analysis_table_item_section_index(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 0U;
  return item->has_section_index ? item->section_index : 0U;
}

static int source_analysis_code_start_is_accepted(const M68kSourceAnalysisIR *source_analysis,
    size_t section_index, uint32_t offset) {
  const M68kSectionAnalysisIR *section;
  if (source_analysis == NULL || section_index >= source_analysis->section_count) return 0;
  section = &source_analysis->sections[section_index];
  return section->certain_code_start != NULL && offset < section->certain_code_size &&
    section->certain_code_start[offset] != 0U;
}

static int source_analysis_code_ref_originates_from_table_item(const M68kCodeStartRefIR *ref,
    uint32_t item_section_index, const M68kAnalysisStructuredDataItem *item) {
  uint32_t item_end;
  if (ref == NULL || item == NULL || ref->source_section_index != item_section_index) return 0;
  if (item->offset <= UINT32_MAX - item->size) {
    item_end = item->offset + item->size;
    if (ref->source_offset >= item->offset && ref->source_offset < item_end) return 1;
  }
  return item->has_consumer && ref->source_section_index == item->consumer_section &&
    ref->source_offset == item->consumer_offset;
}

static int source_analysis_table_has_unaccepted_code_target_refs(
    const M68kSourceAnalysisIR *source_analysis, const M68kAnalysisStructuredDataItem *item) {
  size_t section_index;
  uint32_t item_section_index;
  if (source_analysis == NULL || item == NULL || !source_analysis_table_kind_is_code_dispatch(item->table_kind_id))
    return 0;
  item_section_index = source_analysis_table_item_section_index(item);
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t ref_index;
    for (ref_index = 0U; ref_index < section->code_start_ref_count; ++ref_index) {
      const M68kCodeStartRefIR *ref = &section->code_start_refs[ref_index];
      if (ref->reason != M68K_FACT_CODE_START_REASON_CONTROL_TARGET) continue;
      if (!source_analysis_code_ref_originates_from_table_item(ref, item_section_index, item)) continue;
      if (!source_analysis_code_start_is_accepted(source_analysis, section_index, ref->offset)) return 1;
    }
  }
  return 0;
}

static uint32_t table_conflict_negative_evidence_flags(uint8_t conflict_state) {
  if (conflict_state == M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP) return M68K_RANGE_NEGATIVE_CODE_OVERLAP;
  if (conflict_state == M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED_CODE_TARGET)
    return M68K_RANGE_NEGATIVE_UNRESOLVED_CODE_TARGET;
  return 0U;
}

static void source_analysis_update_materialized_table_conflict(M68kSourceAnalysisIR *source_analysis,
    const M68kAnalysisStructuredDataItem *item) {
  size_t section_index;
  uint32_t item_section_index;
  uint32_t item_end;
  if (source_analysis == NULL || item == NULL || item->size == 0U || item->offset > UINT32_MAX - item->size) {
    return;
  }
  item_section_index = source_analysis_table_item_section_index(item);
  item_end = item->offset + item->size;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t descriptor_index;
    size_t range_index;
    if (section->section_index != item_section_index) continue;
    for (descriptor_index = 0U; descriptor_index < section->table_descriptor_count; ++descriptor_index) {
      M68kTableDescriptorIR *descriptor = &section->table_descriptors[descriptor_index];
      if (descriptor->start_offset == item->offset && descriptor->end_offset == item_end &&
          descriptor->table_kind_id == item->table_kind_id &&
          descriptor->source_pattern_id == item->source_pattern_id) {
        descriptor->status = item->table_conflicted ? M68K_RANGE_OWNERSHIP_STATUS_CONFLICT :
          M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED;
        descriptor->conflict_state = item->table_conflict_state;
      }
    }
    for (range_index = 0U; range_index < section->range_ownership_count; ++range_index) {
      M68kRangeOwnershipIR *range = &section->range_ownerships[range_index];
      if (range->start_offset == item->offset && range->end_offset == item_end &&
          range->table_kind_id == item->table_kind_id &&
          range->source_pattern_id == item->source_pattern_id) {
        range->status = item->table_conflicted ? M68K_RANGE_OWNERSHIP_STATUS_CONFLICT :
          M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED;
        range->conflict_state = item->table_conflict_state;
        range->negative_evidence_flags = table_conflict_negative_evidence_flags(item->table_conflict_state);
      }
    }
  }
}

void m68k_ir_source_analysis_finalize_table_conflicts(M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  size_t item_count;
  int has_dynamic_items;
  if (source_analysis == NULL) return;
  has_dynamic_items = source_analysis->structured_data_item_count != 0U;
  item_count = has_dynamic_items ? source_analysis->structured_data_item_count :
    source_analysis->policy.structured_data_item_count;
  if (!has_dynamic_items && item_count > M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT)
    item_count = M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT;
  for (index = 0U; index < item_count; ++index) {
    M68kAnalysisStructuredDataItem *item = has_dynamic_items ? &source_analysis->structured_data_items[index] :
      &source_analysis->policy.structured_data_items[index];
    if (item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN) continue;
    if (source_analysis_structured_item_range_overlaps_accepted_code(source_analysis, item)) {
      item->table_conflicted = 1U;
      item->table_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP;
    } else if (source_analysis_table_has_unaccepted_code_target_refs(source_analysis, item)) {
      item->table_conflicted = 1U;
      item->table_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED_CODE_TARGET;
    } else {
      item->table_conflicted = 0U;
      item->table_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
    }
    source_analysis_update_materialized_table_conflict(source_analysis, item);
  }
  if (!has_dynamic_items) return;
  for (index = 0U; index < source_analysis->policy.structured_data_item_count; ++index) {
    if (index >= item_count) break;
    source_analysis->policy.structured_data_items[index] = source_analysis->structured_data_items[index];
  }
}

static int m68k_base_layout_field_same_layout(const M68kBaseLayoutFieldIR *left,
    const M68kBaseLayoutFieldIR *right) {
  if (left == NULL || right == NULL) return 0;
  return left->layout_kind == right->layout_kind &&
    left->base_kind == right->base_kind &&
    text_equal_nullable(left->layout_name, right->layout_name) &&
    text_equal_nullable(left->base_symbol, right->base_symbol) &&
    text_equal_nullable(left->sizeof_symbol, right->sizeof_symbol);
}

static int m68k_base_layout_field_same_base(const M68kBaseLayoutFieldIR *left,
    const M68kBaseLayoutFieldIR *right) {
  if (left == NULL || right == NULL) return 0;
  if (left->base_kind != M68K_BASE_LAYOUT_BASE_KIND_UNKNOWN ||
      right->base_kind != M68K_BASE_LAYOUT_BASE_KIND_UNKNOWN) {
    return left->base_kind != M68K_BASE_LAYOUT_BASE_KIND_UNKNOWN &&
      left->base_kind == right->base_kind;
  }
  return text_equal_nullable(left->base_symbol, right->base_symbol);
}

static int m68k_base_layout_fields_overlap(const M68kBaseLayoutFieldIR *left,
    const M68kBaseLayoutFieldIR *right) {
  uint32_t left_end;
  uint32_t right_end;
  if (left == NULL || right == NULL || left->size == 0U || right->size == 0U) return 0;
  if (UINT32_MAX - left->offset < left->size || UINT32_MAX - right->offset < right->size) return 0;
  left_end = left->offset + left->size;
  right_end = right->offset + right->size;
  return left->offset < right_end && right->offset < left_end;
}

static int m68k_layout_ranges_overlap(int64_t left_start, uint32_t left_size, uint32_t right_start,
    uint32_t right_size) {
  int64_t left_end;
  uint64_t right_end;
  if (left_size == 0U || right_size == 0U || left_start < 0) return 0;
  left_end = left_start + (int64_t)left_size;
  right_end = (uint64_t)right_start + (uint64_t)right_size;
  if (right_end > (uint64_t)INT64_MAX) return 0;
  return left_start < (int64_t)right_end && (int64_t)right_start < left_end;
}

static int m68k_platform_typed_access_owner_range(const M68kRecoveredPlatformTypedAccessIR *access,
    int64_t *out_start, uint32_t *out_size) {
  int64_t owner_range_start;
  uint32_t owner_range_size;
  if (out_start != NULL) *out_start = 0;
  if (out_size != NULL) *out_size = 0U;
  if (access == NULL) return 0;
  owner_range_start = (int64_t)access->displacement;
  owner_range_size = access->field_size;
  if (access->struct_size != 0U && access->field_offset >= 0 && access->displacement >= access->field_offset) {
    owner_range_start = (int64_t)access->displacement - (int64_t)access->field_offset;
    owner_range_size = access->struct_size;
  }
  if (owner_range_size == 0U) return 0;
  if (out_start != NULL) *out_start = owner_range_start;
  if (out_size != NULL) *out_size = owner_range_size;
  return 1;
}

static int m68k_base_layout_field_conflicts_with_other_layout(const M68kSourceAnalysisIR *source_analysis,
    const M68kBaseLayoutFieldIR *field) {
  size_t index;
  if (source_analysis == NULL || field == NULL) return 0;
  for (index = 0U; index < source_analysis->base_layout_field_count; ++index) {
    const M68kBaseLayoutFieldIR *other = &source_analysis->base_layout_fields[index];
    if (m68k_base_layout_field_same_layout(field, other)) continue;
    if (!m68k_base_layout_field_same_base(field, other)) continue;
    if (m68k_base_layout_fields_overlap(field, other)) return 1;
  }
  return 0;
}

static int m68k_base_layout_field_conflicts_with_platform_typed_range(
    const M68kSourceAnalysisIR *source_analysis, const M68kBaseLayoutFieldIR *field) {
  size_t section_index;
  if (source_analysis == NULL || field == NULL || field->size == 0U ||
      field->layout_kind == M68K_BASE_LAYOUT_KIND_APP ||
      field->base_kind != M68K_BASE_LAYOUT_BASE_KIND_APP) {
    return 0;
  }
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t access_index;
    for (access_index = 0U; access_index < section->recovered_platform_typed_access_count; ++access_index) {
      const M68kRecoveredPlatformTypedAccessIR *access = &section->recovered_platform_typed_accesses[access_index];
      int64_t owner_range_start;
      uint32_t owner_range_size;
      if (access->type_provenance_kind != M68K_PLATFORM_TYPE_PROVENANCE_APP_SLOT) continue;
      if (!m68k_platform_typed_access_owner_range(access, &owner_range_start, &owner_range_size)) continue;
      if (owner_range_start < 0 || owner_range_start > (int64_t)UINT32_MAX) continue;
      if (m68k_layout_ranges_overlap((int64_t)field->offset, field->size,
          (uint32_t)owner_range_start, owner_range_size)) {
        return 1;
      }
    }
    for (access_index = 0U; access_index < section->recovered_platform_unresolved_typed_access_count;
        ++access_index) {
      const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
        &section->recovered_platform_unresolved_typed_accesses[access_index];
      if (access->type_provenance_kind != M68K_PLATFORM_TYPE_PROVENANCE_APP_SLOT) continue;
      if (access->displacement < 0) continue;
      if (m68k_layout_ranges_overlap((int64_t)field->offset, field->size,
          (uint32_t)access->displacement, access->struct_size)) {
        return 1;
      }
    }
  }
  return 0;
}

void m68k_ir_source_analysis_finalize_base_layout_conflicts(M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  if (source_analysis == NULL) return;
  for (index = 0U; index < source_analysis->base_layout_field_count; ++index) {
    M68kBaseLayoutFieldIR *field = &source_analysis->base_layout_fields[index];
    if (field->conflicted) continue;
    if (m68k_base_layout_field_conflicts_with_other_layout(source_analysis, field) ||
        m68k_base_layout_field_conflicts_with_platform_typed_range(source_analysis, field)) {
      field->conflicted = 1U;
    }
  }
}

static int m68k_base_layout_field_matches(const M68kBaseLayoutFieldIR *left,
    const M68kBaseLayoutFieldIR *right) {
  if (left == NULL || right == NULL) return 0;
  return text_equal_nullable(left->layout_name, right->layout_name) &&
    text_equal_nullable(left->base_symbol, right->base_symbol) &&
    text_equal_nullable(left->sizeof_symbol, right->sizeof_symbol) &&
    text_equal_nullable(left->symbol, right->symbol) &&
    m68k_platform_name_matches(&left->owner_struct_ref, left->owner_struct_name, &right->owner_struct_ref,
      right->owner_struct_name) &&
    left->offset == right->offset &&
    left->size == right->size &&
    left->alias == right->alias &&
    left->has_alias_of == right->has_alias_of &&
    text_equal_nullable(left->alias_of_symbol, right->alias_of_symbol) &&
    text_equal_nullable(left->conflict_reason, right->conflict_reason) &&
    left->alias_of_offset == right->alias_of_offset &&
    left->source_kind == right->source_kind &&
    left->value_kind == right->value_kind &&
    left->confidence == right->confidence &&
    left->conflicted == right->conflicted &&
    left->layout_kind == right->layout_kind &&
    left->base_kind == right->base_kind &&
    left->has_source == right->has_source &&
    left->source_section_index == right->source_section_index &&
    left->source_offset == right->source_offset;
}

int m68k_ir_source_analysis_append_base_layout_field(M68kSourceAnalysisIR *source_analysis,
    const M68kBaseLayoutFieldIR *field) {
  M68kBaseLayoutFieldIR copy;
  size_t index;
  Arena *arena;
  if (source_analysis == NULL || field == NULL) return -1;
  arena = source_analysis->arena;
  if (arena == NULL || field->symbol == NULL || field->symbol[0] == '\0' || field->size == 0U) return -1;
  for (index = 0U; index < source_analysis->base_layout_field_count; ++index) {
    if (m68k_base_layout_field_matches(&source_analysis->base_layout_fields[index], field)) return 0;
  }
  source_analysis->base_layout_fields = (M68kBaseLayoutFieldIR *)arena_grow_array(arena,
      source_analysis->base_layout_fields, source_analysis->base_layout_field_count,
      &source_analysis->base_layout_field_capacity, 16U, sizeof(*source_analysis->base_layout_fields));
  if (source_analysis->base_layout_fields == NULL) return -1;
  memset(&copy, 0, sizeof(copy));
  copy.layout_name = arena_strdup(arena, field->layout_name != NULL ? field->layout_name : "");
  copy.base_symbol = arena_strdup(arena, field->base_symbol != NULL ? field->base_symbol : "");
  copy.sizeof_symbol = arena_strdup(arena, field->sizeof_symbol != NULL ? field->sizeof_symbol : "");
  copy.symbol = arena_strdup(arena, field->symbol);
  copy.owner_struct_name = arena_strdup_if_unresolved_name(arena, &field->owner_struct_ref,
    field->owner_struct_name);
  copy.alias_of_symbol = field->alias_of_symbol != NULL ? arena_strdup(arena, field->alias_of_symbol) : NULL;
  copy.conflict_reason = field->conflict_reason != NULL ? arena_strdup(arena, field->conflict_reason) : NULL;
  if (copy.layout_name == NULL || copy.base_symbol == NULL || copy.sizeof_symbol == NULL ||
      copy.symbol == NULL ||
      (field->owner_struct_name != NULL && !m68k_platform_name_ref_is_set(&field->owner_struct_ref) &&
        copy.owner_struct_name == NULL) ||
      (field->alias_of_symbol != NULL && copy.alias_of_symbol == NULL) ||
      (field->conflict_reason != NULL && copy.conflict_reason == NULL)) {
    return -1;
  }
  copy.owner_struct_ref = field->owner_struct_ref;
  copy.offset = field->offset;
  copy.size = field->size;
  copy.alias = field->alias;
  copy.has_alias_of = field->has_alias_of;
  copy.source_kind = field->source_kind;
  copy.value_kind = field->value_kind;
  copy.confidence = field->confidence;
  copy.conflicted = field->conflicted;
  copy.layout_kind = field->layout_kind;
  copy.base_kind = field->base_kind;
  copy.alias_of_offset = field->alias_of_offset;
  copy.has_source = field->has_source;
  copy.source_section_index = field->source_section_index;
  copy.source_offset = field->source_offset;
  source_analysis->base_layout_fields[source_analysis->base_layout_field_count] = copy;
  source_analysis->base_layout_field_count += 1U;
  return 0;
}

int m68k_ir_source_analysis_append_section(M68kSourceAnalysisIR *source_analysis,
                                           const M68kSectionAnalysisIR *section_analysis) {
  M68kSectionAnalysisIR copy;
  size_t index;
  Arena *source_arena;
  if (source_analysis == NULL || section_analysis == NULL)
    return -1;
  source_arena = source_analysis->arena;
  if (source_arena == NULL) return -1;
  source_analysis->sections = (M68kSectionAnalysisIR *)arena_grow_array(source_arena, source_analysis->sections,
      source_analysis->section_count, &source_analysis->section_capacity, 4U, sizeof(*source_analysis->sections));
  if (source_analysis->sections == NULL) return -1;
  m68k_ir_section_analysis_init_shared(&copy, source_arena);
  copy.section_index = section_analysis->section_index;
  copy.section_name = arena_strdup(source_arena, section_analysis->section_name);
  if (section_analysis->section_name != NULL && copy.section_name == NULL) return -1;
  copy.section_kind = section_analysis->section_kind;
  copy.section_size = section_analysis->section_size;
  if (m68k_ir_section_analysis_set_code_map( &copy, section_analysis->certain_code_start,
          section_analysis->certain_code_byte,
          section_analysis->certain_code_size) != 0) {
    m68k_ir_section_analysis_destroy(&copy);
    return -1;
  }
  if (m68k_ir_section_analysis_set_blocked_code_map(&copy, section_analysis->blocked_code_start,
          section_analysis->blocked_code_size) != 0) {
    m68k_ir_section_analysis_destroy(&copy);
    return -1;
  }
  if (m68k_ir_section_analysis_set_generated_labels(&copy, section_analysis->generated_label_kinds,
          section_analysis->generated_label_flags, section_analysis->generated_label_size) != 0) {
    m68k_ir_section_analysis_destroy(&copy);
    return -1;
  }
  if (m68k_ir_section_analysis_set_word_exprs(&copy, section_analysis->word_exprs,
          section_analysis->word_expr_count) != 0) {
    m68k_ir_section_analysis_destroy(&copy);
    return -1;
  }
  if (m68k_ir_section_analysis_set_long_exprs(&copy, section_analysis->long_exprs,
          section_analysis->long_expr_count) != 0) {
    m68k_ir_section_analysis_destroy(&copy);
    return -1;
  }
  for (index = 0; index < section_analysis->recovered_word_dispatch_count; ++index) {
    if (m68k_ir_section_analysis_append_recovered_word_dispatch(&copy,
          &section_analysis->recovered_word_dispatches[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_inline_dispatch_count; ++index) {
    if (m68k_ir_section_analysis_append_recovered_inline_dispatch(&copy,
          &section_analysis->recovered_inline_dispatches[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_string_dispatch_count; ++index) {
    if (m68k_ir_section_analysis_append_recovered_string_dispatch(&copy,
          &section_analysis->recovered_string_dispatches[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_string_ref_count; ++index) {
    if (m68k_ir_section_analysis_append_recovered_string_ref(&copy,
          &section_analysis->recovered_string_refs[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_indirect_site_count; ++index) {
    if (m68k_ir_section_analysis_append_recovered_indirect_site(&copy,
          &section_analysis->recovered_indirect_sites[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->orphan_code_signal_count; ++index) {
    if (m68k_ir_section_analysis_append_orphan_code_signal(&copy,
          &section_analysis->orphan_code_signals[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->app_slot_ref_count; ++index) {
    if (m68k_ir_section_analysis_append_app_slot_ref(&copy,
          &section_analysis->app_slot_refs[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access =
      &section_analysis->recovered_platform_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_display_text(&access->root_struct_ref,
      access->root_struct_name);
    const char *owner_struct_name = m68k_platform_name_ref_display_text(&access->owner_struct_ref,
      access->owner_struct_name);
    const char *field_name = m68k_platform_name_ref_display_text(&access->field_ref,
      access->field_name);
    uint8_t platform_kind = m68k_platform_kind_from_ref_or_text(&access->root_struct_ref,
      M68K_PLATFORM_NAME_STRUCT, root_struct_name);
    if (platform_kind == 0U) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&access->owner_struct_ref,
        M68K_PLATFORM_NAME_STRUCT, owner_struct_name);
    }
    if (platform_kind == 0U) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&access->field_ref,
        M68K_PLATFORM_NAME_FIELD, field_name);
    }
    if (m68k_ir_section_analysis_append_recovered_platform_typed_access(&copy, platform_kind,
          access->offset, access->operand_index, access->base_reg, access->displacement,
          access->field_offset, access->struct_size, access->field_size, root_struct_name, owner_struct_name,
          field_name, access->field_expr, access->inherited, access->nested, access->type_provenance_kind,
          access->type_provenance_section_index, access->type_provenance_offset) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &section_analysis->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_display_text(&access->root_struct_ref,
      access->root_struct_name);
    const char *container_struct_name = m68k_platform_name_ref_display_text(
      &access->container_struct_ref, access->container_struct_name);
    const char *refined_struct_name = m68k_platform_name_ref_display_text(
      &access->refined_struct_ref, access->refined_struct_name);
    uint8_t platform_kind = m68k_platform_kind_from_ref_or_text(&access->root_struct_ref,
      M68K_PLATFORM_NAME_STRUCT, root_struct_name);
    if (m68k_ir_section_analysis_append_recovered_platform_unresolved_typed_access(&copy, platform_kind,
          access->offset, access->operand_index, access->base_reg, access->displacement,
          access->struct_size, root_struct_name, access->classification, access->container_candidate_count,
          container_struct_name, access->container_field_expr, access->refinement_applied,
          refined_struct_name, access->type_provenance_kind, access->type_provenance_section_index,
          access->type_provenance_offset) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->runtime_view_count; ++index) {
    if (m68k_ir_section_analysis_append_runtime_view(&copy, &section_analysis->runtime_views[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->runtime_address_ref_count; ++index) {
    if (m68k_ir_section_analysis_append_runtime_address_ref(&copy,
          &section_analysis->runtime_address_refs[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->address_observation_count; ++index) {
    if (m68k_ir_section_analysis_append_address_observation(&copy,
          &section_analysis->address_observations[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->platform_address_use_count; ++index) {
    if (m68k_ir_section_analysis_append_platform_address_use(&copy,
          &section_analysis->platform_address_uses[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->platform_semantic_use_count; ++index) {
    if (m68k_ir_section_analysis_append_platform_semantic_use(&copy,
          &section_analysis->platform_semantic_uses[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->code_start_ref_count; ++index) {
    if (m68k_ir_section_analysis_append_code_start_ref(&copy,
          &section_analysis->code_start_refs[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->source_quality_diagnostic_count; ++index) {
    if (m68k_ir_section_analysis_append_source_quality_diagnostic(&copy,
          &section_analysis->source_quality_diagnostics[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->symbol_origin_count; ++index) {
    if (m68k_ir_section_analysis_append_symbol_origin(&copy,
          &section_analysis->symbol_origins[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->expected_symbol_access_count; ++index) {
    if (m68k_ir_section_analysis_append_expected_symbol_access(&copy,
          &section_analysis->expected_symbol_accesses[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->code_origin_count; ++index) {
    if (m68k_ir_section_analysis_append_code_origin(&copy,
          &section_analysis->code_origins[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->accepted_code_run_count; ++index) {
    if (m68k_ir_section_analysis_append_accepted_code_run(&copy,
          &section_analysis->accepted_code_runs[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
    const M68kRecoveredPlatformBaseSlotIR *slot = &section_analysis->recovered_platform_base_slots[index];
    const char *base_name = m68k_platform_name_ref_display_text(&slot->base_ref, slot->base_name);
    uint8_t platform_kind = m68k_platform_kind_from_ref_or_text(&slot->base_ref, M68K_PLATFORM_NAME_BASE,
      base_name);
    if (m68k_ir_section_analysis_append_recovered_platform_base_slot(&copy, platform_kind,
          slot->displacement, base_name) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    const char *base_name = m68k_platform_name_ref_display_text(&effect->payload.named_base.base_ref,
      effect->payload.named_base.base_name);
    const char *symbol_name = m68k_platform_name_ref_display_text(&effect->payload.code_ptr.field_symbol_ref,
      effect->payload.code_ptr.field_symbol_name);
    const char *code_ptr_type_name = m68k_platform_name_ref_display_text(&effect->payload.code_ptr.owner_type_ref,
      effect->payload.code_ptr.owner_type_name);
    const char *code_ptr_semantic_kind = m68k_platform_name_ref_display_text(&effect->payload.code_ptr.semantic_kind_ref,
      effect->payload.code_ptr.semantic_kind);
    const char *typed_type_name = m68k_platform_name_ref_display_text(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    const char *typed_symbol_name = m68k_platform_name_ref_display_text(&effect->payload.typed.symbol_ref,
      effect->payload.typed.symbol_name);
    const char *typed_context_name = m68k_platform_name_ref_display_text(&effect->payload.typed.context_ref,
      effect->payload.typed.context_name);
    const char *typed_semantic_kind = m68k_platform_name_ref_display_text(&effect->payload.typed.semantic_kind_ref,
      effect->payload.typed.semantic_kind);
    const char *typed_value_domain_name = m68k_platform_name_ref_display_text(&effect->payload.typed.value_domain_ref,
      effect->payload.typed.value_domain_name);
    uint8_t platform_kind = 0U;
    if (effect->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT ||
        effect->kind == M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&effect->payload.named_base.base_ref,
        M68K_PLATFORM_NAME_BASE, base_name);
    } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&effect->payload.code_ptr.field_symbol_ref,
        M68K_PLATFORM_NAME_SYMBOL, symbol_name);
      if (platform_kind == 0U) {
        platform_kind = m68k_platform_kind_from_ref_or_text(&effect->payload.code_ptr.owner_type_ref,
          M68K_PLATFORM_NAME_TYPE, code_ptr_type_name);
      }
      if (platform_kind == 0U) {
        platform_kind = m68k_platform_kind_from_ref_or_text(&effect->payload.code_ptr.semantic_kind_ref,
          M68K_PLATFORM_NAME_SEMANTIC_KIND, code_ptr_semantic_kind);
      }
    } else {
      platform_kind = m68k_platform_kind_from_ref_or_text(&effect->payload.typed.symbol_ref,
        M68K_PLATFORM_NAME_SYMBOL, typed_symbol_name);
      if (platform_kind == 0U) {
        platform_kind = m68k_platform_kind_from_ref_or_text(&effect->payload.typed.context_ref,
          M68K_PLATFORM_NAME_BASE, typed_context_name);
      }
      if (platform_kind == 0U) {
        platform_kind = m68k_platform_kind_from_ref_or_text(&effect->payload.typed.type_ref,
        M68K_PLATFORM_NAME_TYPE, typed_type_name);
      }
      if (platform_kind == 0U) {
        platform_kind = m68k_platform_kind_from_ref_or_text(&effect->payload.typed.semantic_kind_ref,
          M68K_PLATFORM_NAME_SEMANTIC_KIND, typed_semantic_kind);
      }
      if (platform_kind == 0U) {
        platform_kind = m68k_platform_kind_from_ref_or_text(&effect->payload.typed.value_domain_ref,
          M68K_PLATFORM_NAME_VALUE_DOMAIN, typed_value_domain_name);
      }
    }
    if (m68k_ir_section_analysis_append_recovered_platform_effect(&copy,
        platform_kind,
        effect->offset, effect->kind,
        effect->reg_kind, effect->reg_index, effect->displacement, effect->field_disp,
        (effect->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT ||
          effect->kind == M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT)
            ? base_name :
            ((effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
              effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT)
              ? typed_context_name : NULL),
          effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG ? symbol_name :
              ((effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
                effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT)
                ? typed_symbol_name : NULL),
          (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) ? code_ptr_type_name :
              ((effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
                effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT)
                ? typed_type_name : NULL),
          (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) ? code_ptr_semantic_kind :
              ((effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
                effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT)
                ? typed_semantic_kind : NULL),
          (effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
            effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) ? typed_value_domain_name : NULL,
          (effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
            effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) ? effect->payload.typed.has_constant_value : 0U,
          (effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
            effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) ? effect->payload.typed.constant_value : 0) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
    if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT ||
        effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) {
      copy.recovered_platform_effects[copy.recovered_platform_effect_count - 1U].target_section_index =
        effect->target_section_index;
      copy.recovered_platform_effects[copy.recovered_platform_effect_count - 1U].target_offset =
        effect->target_offset;
    }
  }
  for (index = 0; index < section_analysis->recovered_local_call_summary_count; ++index) {
    const M68kRecoveredLocalCallSummaryIR *summary = &section_analysis->recovered_local_call_summaries[index];
    const char *base_name = m68k_platform_name_ref_display_text(&summary->payload.named_base.base_ref,
      summary->payload.named_base.base_name);
    const char *typed_context_name = m68k_platform_name_ref_display_text(&summary->payload.typed.context_ref,
      summary->payload.typed.context_name);
    const char *typed_symbol_name = m68k_platform_name_ref_display_text(&summary->payload.typed.symbol_ref,
      summary->payload.typed.symbol_name);
    const char *type_name = m68k_platform_name_ref_display_text(&summary->payload.typed.type_ref,
      summary->payload.typed.type_name);
    const char *semantic_kind = m68k_platform_name_ref_display_text(&summary->payload.typed.semantic_kind_ref,
      summary->payload.typed.semantic_kind);
    const char *value_domain_name = m68k_platform_name_ref_display_text(&summary->payload.typed.value_domain_ref,
      summary->payload.typed.value_domain_name);
    uint8_t platform_kind = summary->effect_kind == M68K_PLATFORM_EFFECT_SET_BASE_REG
      ? m68k_platform_kind_from_ref_or_text(&summary->payload.named_base.base_ref, M68K_PLATFORM_NAME_BASE,
          base_name)
      : m68k_platform_kind_from_ref_or_text(&summary->payload.typed.context_ref, M68K_PLATFORM_NAME_BASE,
          typed_context_name);
    if (platform_kind == 0U && summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&summary->payload.typed.symbol_ref,
        M68K_PLATFORM_NAME_SYMBOL, typed_symbol_name);
    }
    if (platform_kind == 0U && summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&summary->payload.typed.type_ref,
        M68K_PLATFORM_NAME_TYPE, type_name);
    }
    if (platform_kind == 0U && summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&summary->payload.typed.semantic_kind_ref,
        M68K_PLATFORM_NAME_SEMANTIC_KIND, semantic_kind);
    }
    if (platform_kind == 0U && summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&summary->payload.typed.value_domain_ref,
        M68K_PLATFORM_NAME_VALUE_DOMAIN, value_domain_name);
    }
    if (m68k_ir_section_analysis_append_recovered_local_call_summary(&copy,
          platform_kind,
          summary->target_offset, summary->effect_kind,
          summary->reg_kind, summary->reg_index, summary->success_reg_kind, summary->success_reg_index,
          summary->success_value_known, summary->success_reg_value,
          summary->effect_kind == M68K_PLATFORM_EFFECT_SET_BASE_REG ? base_name :
            (summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ? typed_context_name : NULL),
          summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ? typed_symbol_name : NULL,
          summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ? type_name : NULL,
          summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ? semantic_kind : NULL,
          summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ? value_domain_name : NULL,
          summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ? summary->payload.typed.has_constant_value : 0U,
          summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ? summary->payload.typed.constant_value : 0) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_function_arg_count; ++index) {
    const M68kRecoveredFunctionArgIR *arg = &section_analysis->recovered_function_args[index];
    const char *context_name = m68k_platform_name_ref_display_text(&arg->typed.context_ref,
      arg->typed.context_name);
    const char *symbol_name = m68k_platform_name_ref_display_text(&arg->typed.symbol_ref,
      arg->typed.symbol_name);
    const char *type_name = m68k_platform_name_ref_display_text(&arg->typed.type_ref,
      arg->typed.type_name);
    const char *semantic_kind = m68k_platform_name_ref_display_text(&arg->typed.semantic_kind_ref,
      arg->typed.semantic_kind);
    const char *value_domain_name = m68k_platform_name_ref_display_text(&arg->typed.value_domain_ref,
      arg->typed.value_domain_name);
    uint8_t platform_kind = m68k_platform_kind_from_ref_or_text(&arg->typed.context_ref, M68K_PLATFORM_NAME_BASE,
      context_name);
    if (platform_kind == 0U) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&arg->typed.symbol_ref, M68K_PLATFORM_NAME_SYMBOL,
        symbol_name);
    }
    if (platform_kind == 0U) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&arg->typed.type_ref, M68K_PLATFORM_NAME_TYPE,
        type_name);
    }
    if (platform_kind == 0U) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&arg->typed.semantic_kind_ref,
        M68K_PLATFORM_NAME_SEMANTIC_KIND, semantic_kind);
    }
    if (platform_kind == 0U) {
      platform_kind = m68k_platform_kind_from_ref_or_text(&arg->typed.value_domain_ref,
        M68K_PLATFORM_NAME_VALUE_DOMAIN, value_domain_name);
    }
    if (m68k_ir_section_analysis_append_recovered_function_arg(&copy, platform_kind, arg->function_offset,
          arg->stack_offset, arg->reg_kind, arg->reg_index, context_name, symbol_name, type_name, semantic_kind,
          value_domain_name, arg->typed.has_constant_value, arg->typed.constant_value, arg->has_source_operand,
          arg->source_offset, arg->source_reg_kind, arg->source_reg_index, arg->source_displacement) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
      const char *symbol_name = m68k_platform_name_ref_display_text(&call->symbol_ref, call->symbol_name);
      const char *note_base_name = m68k_platform_name_ref_display_text(&call->note_base_ref, call->note_base_name);
      const char *note_symbol_name = m68k_platform_name_ref_display_text(&call->note_symbol_ref, call->note_symbol_name);
      uint8_t platform_kind = m68k_platform_kind_from_ref_or_text(&call->symbol_ref, M68K_PLATFORM_NAME_SYMBOL,
        symbol_name);
      if (platform_kind == 0U) {
        if (call->note_kind == M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD) {
          platform_kind = m68k_platform_kind_from_ref_or_text(&call->note_base_ref, M68K_PLATFORM_NAME_TYPE,
            note_base_name);
        } else {
          platform_kind = m68k_platform_kind_from_ref_or_text(&call->note_base_ref, M68K_PLATFORM_NAME_BASE,
            note_base_name);
          if (platform_kind == 0U) {
            platform_kind = m68k_platform_kind_from_ref_or_text(&call->note_base_ref, M68K_PLATFORM_NAME_FAMILY,
              note_base_name);
          }
        }
      }
      if (platform_kind == 0U) {
        platform_kind = m68k_platform_kind_from_ref_or_text(&call->note_symbol_ref, M68K_PLATFORM_NAME_SYMBOL,
          note_symbol_name);
      }
      if (m68k_ir_section_analysis_append_recovered_platform_call(&copy,
          platform_kind,
          call->offset, call->kind, symbol_name, call->note_kind, note_base_name,
          note_symbol_name, call->note_reg, call->note_disp, call->note_field_disp,
          call->note_stack_cleanup_known, call->note_stack_cleanup_bytes, call->note_return_kind,
          call->available_since, call->fd_version) != 0) {
          m68k_ir_section_analysis_destroy(&copy);
          return -1;
        }
      if (m68k_ir_section_analysis_set_recovered_platform_call_device_name(&copy, call->offset, call->kind,
          call->device_name) != 0) {
          m68k_ir_section_analysis_destroy(&copy);
          return -1;
        }
  }
  for (index = 0; index < section_analysis->recovered_platform_disk_read_count; ++index) {
    const M68kRecoveredPlatformDiskReadIR *read = &section_analysis->recovered_platform_disk_reads[index];
    if (m68k_ir_section_analysis_append_recovered_platform_disk_read(&copy, read->offset, read->command_value,
        read->command_name, read->disk_offset, read->byte_length, read->destination_addr,
        read->source_kind) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_runtime_copy_count; ++index) {
    const M68kRecoveredPlatformRuntimeCopyIR *runtime_copy =
      &section_analysis->recovered_platform_runtime_copies[index];
    if (m68k_ir_section_analysis_append_recovered_platform_runtime_copy(&copy, runtime_copy->offset,
        runtime_copy->source_addr, runtime_copy->destination_addr, runtime_copy->byte_length,
        runtime_copy->handoff_addr, runtime_copy->source_kind) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_media_transfer_count; ++index) {
    const M68kRecoveredPlatformMediaTransferIR *media_transfer =
      &section_analysis->recovered_platform_media_transfers[index];
    if (m68k_ir_section_analysis_append_recovered_platform_media_transfer(&copy, media_transfer->offset,
        media_transfer->path_section_index, media_transfer->path_offset,
        media_transfer->destination_addr, media_transfer->source_size, media_transfer->path,
        media_transfer->source_sha256, media_transfer->source_kind) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_direct_section_call_count; ++index) {
    const M68kRecoveredDirectSectionCallIR *call = &section_analysis->recovered_direct_section_calls[index];
    if (m68k_ir_section_analysis_append_recovered_direct_section_call(&copy, call->offset,
          call->target_section_index, call->target_offset) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  copy.recovered_direct_section_calls_indexed = section_analysis->recovered_direct_section_calls_indexed;
  for (index = 0; index < section_analysis->label_count; ++index) {
    if (m68k_ir_section_analysis_add_label( &copy, section_analysis->label_offsets[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->block_count; ++index) {
    if (m68k_ir_section_analysis_append_block( &copy, &section_analysis->blocks[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->range_ownership_count; ++index) {
    if (m68k_ir_section_analysis_append_range_ownership(&copy, &section_analysis->range_ownerships[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->table_descriptor_count; ++index) {
    if (m68k_ir_section_analysis_append_table_descriptor(&copy,
          &section_analysis->table_descriptors[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->table_entry_count; ++index) {
    if (m68k_ir_section_analysis_append_table_entry(&copy,
          &section_analysis->table_entries[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->data_reference_count; ++index) {
    if (m68k_ir_section_analysis_append_data_reference(&copy,
          &section_analysis->data_references[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->immediate_text_token_count; ++index) {
    if (m68k_ir_section_analysis_append_immediate_text_token(&copy,
          &section_analysis->immediate_text_tokens[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->edge_count; ++index) {
    if (m68k_ir_section_analysis_append_edge( &copy, &section_analysis->edges[index]) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->violation_count; ++index) {
    const M68kViolationIR *violation = &section_analysis->violations[index];
    if (m68k_ir_section_analysis_add_violation(&copy, violation->offset,
                                               violation->kind,
                                               violation->message) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  source_analysis->sections[source_analysis->section_count++] = copy;
  return 0;
}
