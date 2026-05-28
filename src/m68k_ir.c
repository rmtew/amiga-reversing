#include "m68k_ir.h"

#include "generated/amiga_os_runtime.h"
#include "generated/atari_st_os_runtime.h"
#include "m68k_assembler.h"
#include "platform_common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M68K_IR_SOURCE_FILE_ARENA_SIZE 16384U
#define M68K_IR_SOURCE_ANALYSIS_ARENA_SIZE 16384U

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
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH:
      return "keyed_long_relative_dispatch";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MACOS_SYMBOL_RECORD:
      return "macos_symbol_record";
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MULTILINE_TEXT:
      return "multiline_text";
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

static uint8_t structured_data_item_infer_table_kind_id(const M68kAnalysisStructuredDataItem *item) {
  uint32_t role_flags;
  if (item == NULL) return M68K_ANALYSIS_TABLE_KIND_UNKNOWN;
  role_flags = item->semantic_role_flags;
  if ((role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) != 0U)
    return M68K_ANALYSIS_TABLE_KIND_POINTER;
  if ((role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) == 0U)
    return M68K_ANALYSIS_TABLE_KIND_UNKNOWN;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && item->has_target)
    return M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS && item->has_target &&
      item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH)
    return M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS && item->has_target)
    return M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH;
  return M68K_ANALYSIS_TABLE_KIND_SCALAR;
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
  }
}

void m68k_analysis_structured_data_item_set_semantic_role_flags(M68kAnalysisStructuredDataItem *item,
    uint32_t semantic_role_flags) {
  const char *semantic_role;
  if (item == NULL) return;
  item->semantic_role_flags = semantic_role_flags;
  semantic_role = m68k_analysis_structured_data_role_name_for_flags(semantic_role_flags);
  snprintf(item->semantic_role, sizeof(item->semantic_role), "%s", semantic_role != NULL ? semantic_role : "");
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

static uint8_t m68k_platform_kind_from_ref_or_text(const M68kPlatformNameRef *ref, uint8_t fallback_domain_kind,
    const char *text) {
  uint8_t domain_kind = fallback_domain_kind;
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

const char *m68k_platform_name_ref_resolve_text_or_fallback(const M68kPlatformNameRef *ref, const char *text) {
  const char *resolved = m68k_platform_name_ref_resolve_text(ref);
  return resolved != NULL ? resolved : text;
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

static const char *target_platform_summary_call_display_name(const M68kRecoveredPlatformCallIR *call) {
  const char *name;
  if (call == NULL) return "unknown";
  name = m68k_platform_name_ref_resolve_text_or_fallback(&call->symbol_ref, call->symbol_name);
  if (name != NULL && name[0] != '\0') return name;
  name = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_symbol_ref, call->note_symbol_name);
  return name != NULL && name[0] != '\0' ? name : "unknown";
}

static int target_platform_summary_call_is_amiga_os(const M68kRecoveredPlatformCallIR *call) {
  return call != NULL && (call->symbol_ref.platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
    call->note_symbol_ref.platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK);
}

static void target_platform_summary_record_driver(M68kTargetOsCompatibilitySummary *summary,
    const M68kSectionAnalysisIR *section, const M68kRecoveredPlatformCallIR *call) {
  M68kTargetOsRequirementDriver *driver;
  const char *owner;
  if (summary == NULL || section == NULL || call == NULL ||
      summary->max_requirement_driver_count >= M68K_TARGET_PLATFORM_SUMMARY_DRIVER_CAPACITY) {
    return;
  }
  driver = &summary->max_requirement_drivers[summary->max_requirement_driver_count++];
  memset(driver, 0, sizeof(*driver));
  driver->section_index = (uint32_t)section->section_index;
  driver->offset = call->offset;
  snprintf(driver->call, sizeof(driver->call), "%s", target_platform_summary_call_display_name(call));
  owner = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_base_ref, call->note_base_name);
  if (owner != NULL && owner[0] != '\0') {
    driver->has_owner = 1U;
    snprintf(driver->owner, sizeof(driver->owner), "%s", owner);
  }
  snprintf(driver->available_since, sizeof(driver->available_since), "%s",
    call->available_since != NULL ? call->available_since : "");
  if (call->fd_version != NULL && call->fd_version[0] != '\0') {
    driver->has_fd_version = 1U;
    snprintf(driver->fd_version, sizeof(driver->fd_version), "%s", call->fd_version);
  }
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
      if (amiga_os_compatibility_version_rank(call->available_since, &rank) && rank >= max_rank) {
        if (rank > max_rank) {
          max_rank = rank;
          out_summary->os_compatibility.max_requirement_driver_count = 0U;
        }
        target_platform_summary_record_driver(&out_summary->os_compatibility, section, call);
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
  section_analysis->app_slot_refs[section_analysis->app_slot_ref_count] = *ref;
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

int m68k_ir_section_analysis_append_absolute_memory_ref(M68kSectionAnalysisIR *section_analysis,
    const M68kAbsoluteMemoryRefIR *absolute_memory_ref) {
  size_t index;
  if (section_analysis == NULL || absolute_memory_ref == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->absolute_memory_ref_count; ++index) {
    const M68kAbsoluteMemoryRefIR *existing = &section_analysis->absolute_memory_refs[index];
    if (existing->offset == absolute_memory_ref->offset &&
        existing->operand_index == absolute_memory_ref->operand_index &&
        existing->address == absolute_memory_ref->address &&
        existing->access_kind == absolute_memory_ref->access_kind &&
        existing->owner_kind == absolute_memory_ref->owner_kind &&
        existing->conflict_state == absolute_memory_ref->conflict_state) {
      return 0;
    }
  }
  section_analysis->absolute_memory_refs = (M68kAbsoluteMemoryRefIR *)arena_grow_array(section_analysis->arena,
    section_analysis->absolute_memory_refs, section_analysis->absolute_memory_ref_count,
    &section_analysis->absolute_memory_ref_capacity, 8U, sizeof(*section_analysis->absolute_memory_refs));
  if (section_analysis->absolute_memory_refs == NULL) return -1;
  section_analysis->absolute_memory_refs[section_analysis->absolute_memory_ref_count] = *absolute_memory_ref;
  section_analysis->absolute_memory_ref_count += 1U;
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
    existing_base_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.named_base.base_ref,
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
    existing_base_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.named_base.base_ref,
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
    existing_symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.symbol_ref,
      effect->payload.typed.symbol_name);
    existing_type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    existing_semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.semantic_kind_ref,
      effect->payload.typed.semantic_kind);
    existing_value_domain_name = m68k_platform_name_ref_resolve_text_or_fallback(
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
    const char *existing_context_name = m68k_platform_name_ref_resolve_text_or_fallback(&existing->typed.context_ref,
      existing->typed.context_name);
    const char *existing_symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&existing->typed.symbol_ref,
      existing->typed.symbol_name);
    const char *existing_type_name = m68k_platform_name_ref_resolve_text_or_fallback(&existing->typed.type_ref,
      existing->typed.type_name);
    const char *existing_semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(
      &existing->typed.semantic_kind_ref, existing->typed.semantic_kind);
    const char *existing_value_domain_name = m68k_platform_name_ref_resolve_text_or_fallback(
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

void m68k_ir_source_analysis_finalize_table_conflicts(M68kSourceAnalysisIR *source_analysis) {
  uint16_t index;
  if (source_analysis == NULL) return;
  for (index = 0U; index < source_analysis->policy.structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    M68kAnalysisStructuredDataItem *item = &source_analysis->policy.structured_data_items[index];
    if (item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN) continue;
    if (source_analysis_structured_item_range_overlaps_accepted_code(source_analysis, item)) {
      item->table_conflicted = 1U;
      item->table_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP;
    } else {
      item->table_conflicted = 0U;
      item->table_conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
    }
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
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    const char *owner_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->owner_struct_ref,
      access->owner_struct_name);
    const char *field_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->field_ref,
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
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    const char *container_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(
      &access->container_struct_ref, access->container_struct_name);
    const char *refined_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(
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
  for (index = 0; index < section_analysis->absolute_memory_ref_count; ++index) {
    if (m68k_ir_section_analysis_append_absolute_memory_ref(&copy,
          &section_analysis->absolute_memory_refs[index]) != 0) {
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
  for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
    const M68kRecoveredPlatformBaseSlotIR *slot = &section_analysis->recovered_platform_base_slots[index];
    const char *base_name = m68k_platform_name_ref_resolve_text_or_fallback(&slot->base_ref, slot->base_name);
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
    const char *base_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.named_base.base_ref,
      effect->payload.named_base.base_name);
    const char *symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.code_ptr.field_symbol_ref,
      effect->payload.code_ptr.field_symbol_name);
    const char *code_ptr_type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.code_ptr.owner_type_ref,
      effect->payload.code_ptr.owner_type_name);
    const char *code_ptr_semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.code_ptr.semantic_kind_ref,
      effect->payload.code_ptr.semantic_kind);
    const char *typed_type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    const char *typed_symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.symbol_ref,
      effect->payload.typed.symbol_name);
    const char *typed_context_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.context_ref,
      effect->payload.typed.context_name);
    const char *typed_semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.semantic_kind_ref,
      effect->payload.typed.semantic_kind);
    const char *typed_value_domain_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.value_domain_ref,
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
    const char *base_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.named_base.base_ref,
      summary->payload.named_base.base_name);
    const char *typed_context_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.context_ref,
      summary->payload.typed.context_name);
    const char *typed_symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.symbol_ref,
      summary->payload.typed.symbol_name);
    const char *type_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.type_ref,
      summary->payload.typed.type_name);
    const char *semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.semantic_kind_ref,
      summary->payload.typed.semantic_kind);
    const char *value_domain_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.value_domain_ref,
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
    const char *context_name = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.context_ref,
      arg->typed.context_name);
    const char *symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.symbol_ref,
      arg->typed.symbol_name);
    const char *type_name = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.type_ref,
      arg->typed.type_name);
    const char *semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.semantic_kind_ref,
      arg->typed.semantic_kind);
    const char *value_domain_name = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.value_domain_ref,
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
      const char *symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->symbol_ref, call->symbol_name);
      const char *note_base_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_base_ref, call->note_base_name);
      const char *note_symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_symbol_ref, call->note_symbol_name);
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
